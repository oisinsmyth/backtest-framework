"""The Binance fetch → resample → fixture → freeze path, end to end and offline.

Gates closed here:

- The whole path runs on a synthetic archive with no network: fetch, D161 day-level drop,
  resample to 15m, write the fixture trio, freeze a snapshot.
- A UTC day the provider served short is dropped ENTIRELY rather than emitting a bucket
  of the wrong duration (D161), and the drop is counted.
- Genuinely empty bars survive to the snapshot as `zero_volume` WARNINGS, and the snapshot
  loads WITHOUT `allow_quarantined` — D192's and D143's deferrals stay unspent.
- What the volume rule would have dropped is MEASURED, because `clean()` is called twice.
- All three volume columns round-trip through fixture and snapshot still aligned.
"""

from __future__ import annotations

import hashlib
import io
import zipfile
from datetime import date, datetime

import pytest

from backtest_framework.data.binance_source import BinanceDataSource
from backtest_framework.data.cleaner import clean
from backtest_framework.data.corporate_actions import CorporateActions, load_events_json, save_events_json
from backtest_framework.data.csv_fixture import load_fixture_csv_with_extras, save_fixture_csv
from backtest_framework.data.snapshot_store import SnapshotStore
from backtest_framework.data.validator import validate
from backtest_framework.research.breakout_intraday import census_days, resample

MINUTE_MS = 60_000
DAY_START = 1619827200000  # 2021-05-01 00:00 UTC
SYMBOL = "TESTUSDT"


def _row(open_time: int, close: float, base: float, trades: int) -> str:
    quote = base * close
    return (
        f"{open_time},{close},{close + 1},{close - 1},{close},{base},"
        f"{open_time + 59_999},{quote},{trades},{base / 2},{base / 2 * close},0\n"
    )


def _month(days: int, empty_every: int = 0, short_day: int | None = None) -> str:
    """`days` complete UTC days of 1m bars. `empty_every` makes every Nth minute a
    genuine empty bar (zero volume AND zero trades). `short_day` serves one minute fewer
    on that day index, which is what forces D161's day-level drop."""
    rows = []
    for d in range(days):
        minutes = 1440 - (1 if short_day == d else 0)
        for m in range(minutes):
            t = DAY_START + (d * 1440 + m) * MINUTE_MS
            empty = empty_every and (m % empty_every == 0)
            rows.append(_row(t, 100.0 + m * 0.001, 0.0 if empty else 2.0, 0 if empty else 7))
    return "".join(rows)


class _Response:
    def __init__(self, payload: bytes):
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        return None


def _stub(text: str):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(f"{SYMBOL}-1m-2021-05.csv", text)
    payload = buffer.getvalue()
    digest = hashlib.sha256(payload).hexdigest()
    listing = (
        "<ListBucketResult><IsTruncated>false</IsTruncated><Contents>"
        f"<Key>data/spot/monthly/klines/{SYMBOL}/1m/{SYMBOL}-1m-2021-05.zip</Key>"
        "<LastModified>2024-01-01T00:00:00.000Z</LastModified><ETag>&quot;e&quot;</ETag>"
        f"<Size>{len(payload)}</Size></Contents></ListBucketResult>"
    )

    def opener(url: str, timeout: int = 0):
        if "?delimiter=" in url:
            return _Response(listing.encode())
        if url.endswith(".CHECKSUM"):
            return _Response(f"{digest}  {SYMBOL}-1m-2021-05.zip\n".encode())
        return _Response(payload)

    return opener


def _build(tmp_path, text: str):
    """fetch → day census → resample → fixture trio, returning the paths and counts."""
    source = BinanceDataSource(cache_root=tmp_path / "cache", opener=_stub(text), pause=0.0)
    bars, columns, report = source.get_volume_columns(
        SYMBOL, date(2021, 5, 1), date(2021, 5, 31), "1m"
    )
    day_census = census_days(bars, source_minutes=1)

    series = {}
    out_bars = None
    for name in ("quote_volume", "base_volume", "taker_buy_base"):
        resampled, values, rep = resample(
            bars, columns[name], 15, day_census.complete, source_minutes=1
        )
        rep.check()
        series[name] = values
        out_bars = resampled

    fixture = tmp_path / "f.csv.gz"
    events = tmp_path / "f_events.json"
    save_fixture_csv(
        fixture,
        {SYMBOL: out_bars},
        {SYMBOL: series["quote_volume"]},
        {
            "base_volume": {SYMBOL: series["base_volume"]},
            "taker_buy_base": {SYMBOL: series["taker_buy_base"]},
        },
    )
    save_events_json(
        events,
        CorporateActions(dividends_by_symbol={SYMBOL: []}, splits_by_symbol={SYMBOL: []}),
    )
    return fixture, events, day_census, report


def _freeze(tmp_path, fixture, events):
    """The freeze path from `scripts/fetch_binance_fixture.py`, mirrored."""
    bars, volumes, extras = load_fixture_csv_with_extras(fixture)
    actions = load_events_json(events)
    cleaned, price_report = clean(bars)
    for symbol in bars:
        assert len(cleaned[symbol]) == len(bars[symbol]), "price-only clean dropped a bar"
    _, full_report = clean(bars, volumes)
    validation = validate(cleaned, actions, volumes)
    store = SnapshotStore(tmp_path / "snapshots")
    snapshot_id = store.create(
        cleaned,
        actions,
        volumes_by_symbol=volumes,
        cleaning_report=price_report,
        validation=validation,
        extra_columns=extras,
    )
    return store, snapshot_id, validation, full_report


# ---------------------------------------------------------------- the happy path


def test_three_complete_days_resample_to_the_exact_bar_count(tmp_path):
    fixture, _, day_census, _ = _build(tmp_path, _month(days=3))
    assert len(day_census.complete) == 3 and not day_census.incomplete
    bars, _, _ = load_fixture_csv_with_extras(fixture)
    assert len(bars[SYMBOL]) == 3 * 96  # 96 fifteen-minute bars per UTC day


def test_bars_land_on_the_fifteen_minute_utc_grid(tmp_path):
    fixture, _, _, _ = _build(tmp_path, _month(days=2))
    bars, _, _ = load_fixture_csv_with_extras(fixture)
    assert bars[SYMBOL][0].timestamp == datetime(2021, 5, 1, 0, 0)
    assert all(tb.timestamp.minute % 15 == 0 for tb in bars[SYMBOL])


def test_all_three_volume_columns_survive_the_fixture_roundtrip(tmp_path):
    fixture, _, _, _ = _build(tmp_path, _month(days=2))
    bars, volumes, extras = load_fixture_csv_with_extras(fixture)
    n = len(bars[SYMBOL])
    assert len(volumes[SYMBOL]) == n
    assert len(extras["base_volume"][SYMBOL]) == n
    assert len(extras["taker_buy_base"][SYMBOL]) == n
    # 15 minutes x 2.0 base = 30.0 per bucket, and quote is base x price, never derived.
    assert extras["base_volume"][SYMBOL][0] == pytest.approx(30.0)
    assert extras["taker_buy_base"][SYMBOL][0] == pytest.approx(15.0)


# ---------------------------------------------------------------- D161 day-level drop


def test_a_short_utc_day_is_dropped_whole_and_counted(tmp_path):
    """`resample` refuses to emit a bucket of the wrong duration, so partial days go
    first — at the level of the DAY, not the bucket (D161)."""
    fixture, _, day_census, _ = _build(tmp_path, _month(days=3, short_day=1))
    assert len(day_census.complete) == 2
    assert [d.isoformat() for d, _ in day_census.incomplete] == ["2021-05-02"]
    assert day_census.incomplete[0][1] == 1439
    bars, _, _ = load_fixture_csv_with_extras(fixture)
    assert len(bars[SYMBOL]) == 2 * 96
    assert not any(tb.timestamp.date().isoformat() == "2021-05-02" for tb in bars[SYMBOL])


# ---------------------------------------------------------------- the gate


def test_empty_bars_reach_the_snapshot_as_warnings_and_it_loads_unquarantined(tmp_path):
    """The whole point of the 15m base: no cleaner edit, no override, deferrals unspent.

    Every minute of one 15m bucket is empty, so the aggregate is a genuine zero-volume
    bar — the case D192 says is TRUE rather than a defect.
    """
    text = "".join(
        _row(
            DAY_START + m * MINUTE_MS,
            100.0 + m * 0.001,
            0.0 if m < 15 else 2.0,
            0 if m < 15 else 7,
        )
        for m in range(1440)
    )
    fixture, events, _, _ = _build(tmp_path, text)
    store, snapshot_id, validation, full_report = _freeze(tmp_path, fixture, events)

    assert validation.hard_violations == ()
    assert validation.passed
    zero_volume = [v for v in validation.warnings if v.check == "zero_volume"]
    assert len(zero_volume) == 1

    snapshot = store.load(snapshot_id)  # no allow_quarantined
    assert snapshot.meta["quarantined"] is False


def test_the_volume_rule_counterfactual_is_measured_not_assumed(tmp_path):
    """`clean()` is called twice: once for real on prices, once to count what the volume
    rule would have deleted. That measurement is what makes skipping the rule honest."""
    text = "".join(
        _row(DAY_START + m * MINUTE_MS, 100.0, 0.0 if m < 15 else 2.0, 0 if m < 15 else 7)
        for m in range(1440)
    )
    fixture, events, _, _ = _build(tmp_path, text)
    _, _, _, full_report = _freeze(tmp_path, fixture, events)
    dropped = [c for c in full_report.changes if c.rule == "non_positive_volume"]
    assert len(dropped) == 1


def test_a_fully_traded_fixture_produces_no_zero_volume_warnings(tmp_path):
    fixture, events, _, _ = _build(tmp_path, _month(days=2))
    _, _, validation, full_report = _freeze(tmp_path, fixture, events)
    assert [v for v in validation.warnings if v.check == "zero_volume"] == []
    assert full_report.changes == ()


def test_the_snapshot_carries_all_three_columns(tmp_path):
    fixture, events, _, _ = _build(tmp_path, _month(days=2))
    store, snapshot_id, _, _ = _freeze(tmp_path, fixture, events)
    snapshot = store.load(snapshot_id)
    assert set(snapshot.extras) == {"base_volume", "taker_buy_base"}
    assert len(snapshot.extras["base_volume"][SYMBOL]) == len(snapshot.bars_by_symbol[SYMBOL])


def test_the_events_sidecar_is_empty_but_present(tmp_path):
    """D48/D108 — an empty sidecar must not be a lie, and here it is true by construction."""
    _, events, _, _ = _build(tmp_path, _month(days=1))
    actions = load_events_json(events)
    assert actions.dividends_by_symbol == {SYMBOL: []}
    assert actions.splits_by_symbol == {SYMBOL: []}


# ---------------------------------------------------------------- determinism


def test_the_fixture_is_byte_identical_on_a_second_build(tmp_path):
    first, _, _, _ = _build(tmp_path / "a", _month(days=2))
    second, _, _, _ = _build(tmp_path / "b", _month(days=2))
    assert first.read_bytes() == second.read_bytes()
