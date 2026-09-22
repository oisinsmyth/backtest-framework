"""`data/retail_attention.py`, the two fixtures and the validation report — D621.

WHAT IS CHECKED HERE AND WHY IT IS NOT IN THE GOLDEN. The golden pins four pieces of arithmetic
against hand-worked ground truth. This file pins the things that are not arithmetic: the guards
that must RAISE, the outage that must come back as `None` and never `0`, the fixtures' own
shape, and the one claim that makes the whole measurement checkable — that
`data/retail_attention_validation.json` is a pure function of the committed fixtures and
reproduces from them byte for byte.

THE CLOSED CASES THAT MATTER MOST ARE THE TWO REFUSALS:

  * **a same-day or later observation in a z window RAISES.** R9 is the price list: a monotone
    effect spanning 465 percentage points that vanished entirely once its conditioner was lagged
    by one bar, in an analysis script whose author did not think a descriptive cut needed a
    guard. Filtering such an observation is indistinguishable from a window that never had one,
    so it is refused instead.
  * **a missing holder poll is `None`.** The Robintrack archive has two site outages, 6.4 and
    9.9 days. A zero across one of them would show USO losing 144,000 holders overnight and
    regaining them ten days later — two of the largest flows in the sample, both fictional.

No return is computed, no price bar is read, and the newest row any test here touches is dated
2020-08-13.
"""

from __future__ import annotations

import datetime as dt
import gzip
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from backtest_framework.data.attention import (
    AttentionError,
    InsufficientHistory,
    LookaheadRefused,
    ResolutionRefused,
)
from backtest_framework.data import retail_attention as RA
from backtest_framework.data.retail_attention import (
    CREATION_LAG,
    HOLDER_COLUMNS,
    HOLDERS_LAG,
    MAX_GAP_DAYS,
    OUTAGES,
    CreationSeries,
    HolderObs,
    RetailAttention,
    RetailAttentionError,
    creation_accel,
    creation_available_at,
    creation_level,
    creation_z,
    creations,
    daily_holders,
    holders_available_at,
    holders_z,
    in_outage,
    news_n_hourly,
    pearson,
    quantile_linear,
    rank_average,
    read_holder_fixture,
    robinhood_holders,
    spearman,
)

UTC = dt.timezone.utc
REPO = Path(__file__).resolve().parents[2]
RT_FIXTURE = REPO / "data" / "fixtures" / "robintrack_energy_funds.csv.gz"
RT_META = REPO / "data" / "fixtures" / "robintrack_energy_funds.meta.json"
GDELT_FIXTURE = REPO / "data" / "fixtures" / "gdelt_hourly_sample.csv.gz"
GDELT_META = REPO / "data" / "fixtures" / "gdelt_hourly_sample.meta.json"
VALIDATION = REPO / "data" / "retail_attention_validation.json"
NAV_FIXTURE = REPO / "data" / "fixtures" / "fund_nav_daily.csv.gz"


def _script(name: str, alias: str):
    """Load a `scripts/` runner by path. `scripts/` is not a package, so `sys.path` gets the
    directory and the module is registered before execution. Both runners' module bodies define
    constants and functions and read nothing."""
    path = REPO / "scripts" / f"{name}.py"
    if str(REPO / "scripts") not in sys.path:
        sys.path.insert(0, str(REPO / "scripts"))
    spec = importlib.util.spec_from_file_location(alias, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


BUILDER = _script("build_robintrack_funds", "d621_build_robintrack_funds")
GDELT = _script("fetch_gdelt_hourly", "d621_fetch_gdelt_hourly")
REPORT = _script("retail_attention_report", "d621_retail_attention_report")


def needs_d621_fixture(path: Path) -> None:
    """Skip when one of D621's own two fixtures is absent, and say exactly why it can be.

    `.gitignore:109` excludes every `data/**/*.csv.gz` (D536's bulk-panel convention), so both
    fixtures are BUILT rather than cloned. They are not yet rows of `data/data_manifest.json`
    either: the manifest's panel count is pinned at 128 by `tests/unit/test_panels.py` and
    `tests/unit/test_running_page_figures.py`, and `data/data_manifest.json` and
    `data/panel_catalogue.py` are shared documents this record does not edit. The rows were added by the
    integrator the same day (manifest 128 -> 132), so this helper now applies D609's three-way
    `panel_status` -- a listed absence is an honest skip, an unlisted one is a bug -- and keeps
    the build command in its skip message rather than leaving a reader to guess.
    """
    from backtest_framework.data.panels import panel_status

    status = panel_status(path)
    if status == "present":
        return
    builders = {
        "robintrack_energy_funds.csv.gz": "uv run python scripts/build_robintrack_funds.py --build",
        "gdelt_hourly_sample.csv.gz": "uv run python scripts/fetch_gdelt_hourly.py --from-files",
    }
    if status == "absent_listed":
        pytest.skip(
            f"{path.name} is absent and listed in data/data_manifest.json (a gitignored bulk "
            f"panel, D536); build it with: {builders.get(path.name, '')}"
        )
    raise FileNotFoundError(f"{path} is absent AND not a manifest panel: a wrong path or an unbuilt row")


# ============================================================ the module keeps no writer (D612)
def test_the_module_exposes_no_writer():
    """D612's guarantee, carried forward: this module reads and computes and never opens a file
    for writing. A guarantee about code that does not exist can only be tested as an assertion
    about the namespace."""
    bad = [n for n in dir(RA) if not n.startswith("_") and RA.FORBIDDEN_NAME_RE.search(n)]
    assert bad == ["NO_WRITER_HERE"], bad
    assert not hasattr(RA, "write_fixture") and not hasattr(RA, "save")


def test_the_module_source_opens_nothing_for_writing():
    """The namespace check catches a NAME; this catches a call. `read_holder_fixture` opens a
    gzip stream in `"rt"` and there must be no other mode anywhere in the file."""
    source = (REPO / "src" / "backtest_framework" / "data" / "retail_attention.py").read_text(
        encoding="utf-8"
    )
    assert '"wt"' not in source and '"wb"' not in source and '"w"' not in source
    assert '"rt"' in source


# ================================================================================== creations
def test_creations_differences_against_the_previous_day_in_the_source():
    shares = {
        dt.date(2019, 11, 1): 100.0,   # Friday
        dt.date(2019, 11, 4): 110.0,   # Monday: a three-calendar-day step, ONE creation
        dt.date(2019, 11, 5): 105.0,
    }
    series = creations(shares, fund="TEST")
    assert series.deltas == ((dt.date(2019, 11, 4), 10.0), (dt.date(2019, 11, 5), -5.0))
    assert series.prev_day(dt.date(2019, 11, 4)) == dt.date(2019, 11, 1)
    assert series.skipped == ()


def test_the_first_day_of_a_series_has_no_creation():
    """Inventing one from zero would make the fund's launch its largest creation ever."""
    series = creations({dt.date(2019, 11, 1): 100.0}, fund="TEST")
    assert series.deltas == () and series.steps == ()
    with pytest.raises(RetailAttentionError):
        series.value(dt.date(2019, 11, 1))


def test_a_gap_longer_than_the_limit_is_skipped_and_named():
    series = creations(
        {dt.date(2019, 11, 1): 100.0, dt.date(2019, 12, 1): 900.0}, fund="TEST"
    )
    assert series.deltas == ()
    assert series.skipped == ((dt.date(2019, 12, 1), 30),)


def test_a_gap_exactly_at_the_limit_is_still_one_step():
    a, b = dt.date(2019, 11, 1), dt.date(2019, 11, 1) + dt.timedelta(days=MAX_GAP_DAYS)
    series = creations({a: 100.0, b: 150.0}, fund="TEST")
    assert series.deltas == ((b, 50.0),) and series.skipped == ()


def test_a_duplicated_day_raises():
    class Twice(dict):
        def items(self):
            return [(dt.date(2019, 11, 1), 1.0), (dt.date(2019, 11, 1), 2.0)]

    with pytest.raises(RetailAttentionError):
        creations(Twice(), fund="TEST")


def test_a_datetime_key_is_refused_because_it_is_not_a_day():
    with pytest.raises(RetailAttentionError):
        creations({dt.datetime(2019, 11, 1, tzinfo=UTC): 1.0}, fund="TEST")


# ================================================================================ the daily z
def test_creation_z_refuses_an_observation_dated_after_the_scored_day():
    obs = [(dt.date(2019, 10, 1) + dt.timedelta(days=k), float(k)) for k in range(10)]
    scored = dt.date(2019, 10, 6)
    with pytest.raises(LookaheadRefused):
        creation_z(obs, scored)


def test_creation_z_refuses_a_same_day_duplicate():
    """The scored day's own observation is the value being scored and must appear exactly once;
    a second one is ambiguous and is refused rather than resolved by position."""
    obs = [(dt.date(2019, 10, 1) + dt.timedelta(days=k), float(k)) for k in range(6)]
    obs.append((dt.date(2019, 10, 6), 99.0))
    with pytest.raises(RetailAttentionError):
        creation_z(obs, dt.date(2019, 10, 6))


def test_creation_z_refuses_below_the_minimum_matched_observations():
    obs = [(dt.date(2019, 10, 1) + dt.timedelta(days=k), float(k)) for k in range(4)]
    with pytest.raises(InsufficientHistory):
        creation_z(obs, dt.date(2019, 10, 4))


def test_creation_z_refuses_a_constant_window():
    obs = [(dt.date(2019, 10, 1) + dt.timedelta(days=k), 7.0) for k in range(7)]
    with pytest.raises(InsufficientHistory):
        creation_z(obs, dt.date(2019, 10, 7))


def test_an_observation_older_than_the_window_is_dropped_not_an_error():
    """Old is not a leak. The 200-day-old point is simply outside the 60-day window."""
    obs = [(dt.date(2019, 10, 1) + dt.timedelta(days=k), float(k)) for k in range(7)]
    with_old = [(dt.date(2018, 1, 1), 9999.0), *obs]
    assert creation_z(with_old, dt.date(2019, 10, 7)) == creation_z(obs, dt.date(2019, 10, 7))


def test_an_unknown_match_rule_raises():
    obs = [(dt.date(2019, 10, 1) + dt.timedelta(days=k), float(k)) for k in range(7)]
    with pytest.raises(RetailAttentionError):
        creation_z(obs, dt.date(2019, 10, 7), match="nearest")  # type: ignore[arg-type]


# ============================================================================= level and accel
def test_creation_level_is_att_level_and_refuses_an_empty_mapping():
    assert creation_level({"BOIL": 1.0, "KOLD": 3.0}) == 2.0
    with pytest.raises(InsufficientHistory):
        creation_level({})


def test_creation_level_ignores_an_absent_fund_rather_than_scoring_it_zero():
    """An absent fund is no measurement; a zero z is an exactly average creation day."""
    assert creation_level({"BOIL": 2.0}) == 2.0
    assert creation_level({"BOIL": 2.0, "KOLD": 0.0}) == 1.0


def test_creation_accel_is_exactly_zero_on_a_constant():
    days = [dt.date(2019, 11, 1) + dt.timedelta(days=k) for k in range(6)]
    assert creation_accel([(d, 2.5) for d in days], days[-1]) == 0.0


def test_creation_accel_needs_six_observations():
    days = [dt.date(2019, 11, 1) + dt.timedelta(days=k) for k in range(5)]
    with pytest.raises(InsufficientHistory):
        creation_accel([(d, 1.0) for d in days], days[-1])


def test_creation_accel_refuses_a_calendar_hole_inside_the_window():
    days = [dt.date(2019, 11, 1) + dt.timedelta(days=k) for k in range(5)]
    days.append(days[-1] + dt.timedelta(days=MAX_GAP_DAYS + 1))
    with pytest.raises(InsufficientHistory):
        creation_accel([(d, float(i)) for i, d in enumerate(days)], days[-1])


def test_creation_accel_refuses_a_day_that_is_not_in_the_series():
    days = [dt.date(2019, 11, 1) + dt.timedelta(days=k) for k in range(6)]
    with pytest.raises(InsufficientHistory):
        creation_accel([(d, 1.0) for d in days], dt.date(2020, 1, 1))


# ================================================================================ availability
def test_the_creation_lag_is_one_full_day_and_unconditional():
    assert CREATION_LAG == dt.timedelta(days=1)
    for day in (dt.date(2019, 11, 4), dt.date(2019, 12, 31), dt.date(2020, 2, 29)):
        assert creation_available_at(day) == dt.datetime.combine(
            day + dt.timedelta(days=1), dt.time(0, 0), tzinfo=UTC
        )


def test_the_holder_lag_is_one_full_poll_interval():
    assert HOLDERS_LAG == dt.timedelta(hours=1)
    when = dt.datetime(2019, 11, 4, 13, 22, 5, tzinfo=UTC)
    assert holders_available_at(when) == dt.datetime(2019, 11, 4, 14, 22, 5, tzinfo=UTC)


def test_a_naive_instant_is_refused_everywhere():
    with pytest.raises(RetailAttentionError):
        holders_available_at(dt.datetime(2019, 11, 4, 13, 0))


def test_the_bundle_refuses_a_component_that_was_not_yet_available():
    """The whole reason the bundle exists: a component quoted at an instant it could not have
    been read at is a look-ahead, and it raises rather than being reported."""
    day = dt.date(2019, 11, 4)
    with pytest.raises(LookaheadRefused):
        RetailAttention(
            tau=dt.datetime(2019, 11, 4, 23, 0, tzinfo=UTC),
            creation_day=day,
            creation_value=100.0,
        )
    ok = RetailAttention(
        tau=dt.datetime(2019, 11, 5, 0, 0, tzinfo=UTC), creation_day=day, creation_value=100.0
    )
    assert ok.available_at() == {"creations": dt.datetime(2019, 11, 5, 0, 0, tzinfo=UTC)}


def test_the_bundle_refuses_a_half_supplied_component():
    with pytest.raises(RetailAttentionError):
        RetailAttention(tau=dt.datetime(2019, 11, 5, tzinfo=UTC), creation_day=dt.date(2019, 11, 4))


# ===================================================================== holders and the outages
def _obs(*pairs: tuple[str, int]) -> list[HolderObs]:
    return [
        HolderObs(ticker="USO", ts_utc=dt.datetime.fromisoformat(s).replace(tzinfo=UTC), holders=h)
        for s, h in pairs
    ]


def test_an_hour_with_no_poll_is_none_and_never_zero():
    rows = _obs(("2019-11-04T13:10:00", 100), ("2019-11-04T15:05:00", 120))
    assert robinhood_holders(rows, "USO", dt.datetime(2019, 11, 4, 13, tzinfo=UTC)) == 100
    assert robinhood_holders(rows, "USO", dt.datetime(2019, 11, 4, 14, tzinfo=UTC)) is None
    assert robinhood_holders(rows, "USO", dt.datetime(2019, 11, 4, 15, tzinfo=UTC)) == 120


def test_an_hour_with_two_polls_returns_the_last_one():
    rows = _obs(("2019-11-04T13:10:00", 100), ("2019-11-04T13:50:00", 111))
    assert robinhood_holders(rows, "USO", dt.datetime(2019, 11, 4, 13, tzinfo=UTC)) == 111


def test_an_hour_off_the_boundary_raises():
    rows = _obs(("2019-11-04T13:10:00", 100))
    with pytest.raises(RetailAttentionError):
        robinhood_holders(rows, "USO", dt.datetime(2019, 11, 4, 13, 30, tzinfo=UTC))


def test_the_daily_cut_is_the_last_poll_of_the_utc_day():
    rows = _obs(
        ("2019-11-04T01:00:00", 10), ("2019-11-04T23:30:00", 44), ("2019-11-05T00:10:00", 45)
    )
    assert daily_holders(rows, "USO", dt.date(2019, 11, 4)) == 44
    assert daily_holders(rows, "USO", dt.date(2019, 11, 5)) == 45
    assert daily_holders(rows, "USO", dt.date(2019, 11, 6)) is None


def test_the_two_declared_outages_are_half_open_intervals():
    assert len(OUTAGES) == 2
    for start, end in OUTAGES:
        assert in_outage(start) and not in_outage(end)
        assert in_outage(start + (end - start) / 2)
        assert not in_outage(start - dt.timedelta(seconds=1))


def test_holders_z_is_d612s_zscore_matched():
    """A thin adapter and nothing else: the hourly holder series is scored by the rule the
    deposit's line 255 states, not by a second rule invented here."""
    from backtest_framework.data.attention import zscore_matched

    obs = [(dt.date(2019, 9, 30) + dt.timedelta(days=7 * k), 14, 10.0 + 2 * k) for k in range(5)]
    obs.append((dt.date(2019, 11, 4), 14, 20.0))
    assert holders_z(obs, dt.date(2019, 11, 4), 14) == zscore_matched(obs, dt.date(2019, 11, 4), 14)


# ============================================================================ the statistics
def test_rank_average_gives_ties_the_average_of_the_ranks_they_span():
    assert rank_average([1.0, 2.0, 2.0, 3.0]) == (1.0, 2.5, 2.5, 4.0)
    assert rank_average([5.0, 5.0, 5.0]) == (2.0, 2.0, 2.0)


def test_spearman_is_invariant_to_a_monotone_transform_and_pearson_is_not():
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [1.0, 4.0, 9.0, 16.0, 25.0]
    assert spearman(x, y) == 1.0
    assert pearson(x, y) != 1.0


def test_a_correlation_with_a_constant_side_raises_rather_than_returning_zero():
    with pytest.raises(InsufficientHistory):
        pearson([1.0, 1.0, 1.0, 1.0], [1.0, 2.0, 3.0, 4.0])


def test_a_correlation_of_two_points_raises():
    with pytest.raises(InsufficientHistory):
        pearson([1.0, 2.0], [3.0, 4.0])


def test_mismatched_lengths_raise():
    with pytest.raises(RetailAttentionError):
        pearson([1.0, 2.0, 3.0], [1.0, 2.0])


def test_a_non_finite_input_raises_everywhere():
    for bad in (float("nan"), float("inf")):
        with pytest.raises(RetailAttentionError):
            pearson([1.0, 2.0, bad], [1.0, 2.0, 3.0])
        with pytest.raises(RetailAttentionError):
            quantile_linear([1.0, bad], 0.5)


def test_quantile_refuses_a_p_outside_the_unit_interval():
    with pytest.raises(RetailAttentionError):
        quantile_linear([1.0, 2.0, 3.0], 1.5)


# ================================================================== the DOC API response shape
def test_the_api_shape_parser_on_the_recorded_payload():
    """`GDELT.API_SHAPE` is a payload of the DOC 2.0 DOCUMENTED response shape and is not a
    recorded live response -- the API answered 429 and then dropped the connection on
    2026-09-22, and the record says so. Its fields are the ones
    `scripts/fetch_attention.py:gdelt_doc` already reads."""
    series = news_n_hourly(GDELT.API_SHAPE, accept_hourly=True)
    assert series.resolution == "hour"
    assert series.points[0] == (dt.datetime(2019, 11, 4, 0, 0, tzinfo=UTC), 12.0)
    assert series.total == 21.0


def test_the_same_payload_is_refused_under_the_deposits_fifteen_minute_rule():
    with pytest.raises(ResolutionRefused):
        news_n_hourly(GDELT.API_SHAPE, accept_hourly=False)


def test_a_daily_bucket_is_refused_even_when_hourly_is_asked_for():
    daily = {**GDELT.API_SHAPE, "query_details": {"date_resolution": "day"}}
    with pytest.raises(ResolutionRefused):
        news_n_hourly(daily, accept_hourly=True)


def test_a_fifteen_minute_bucket_passes_both_settings_unwidened():
    fine = {**GDELT.API_SHAPE, "query_details": {"date_resolution": "15min"}}
    assert news_n_hourly(fine, accept_hourly=False).resolution == "15min"
    assert news_n_hourly(fine, accept_hourly=True).resolution == "15min"


def test_accept_hourly_must_be_a_bool_not_a_truthy_string():
    with pytest.raises(RetailAttentionError):
        news_n_hourly(GDELT.API_SHAPE, accept_hourly="yes")  # type: ignore[arg-type]


def test_a_payload_with_no_resolution_raises_rather_than_defaulting():
    with pytest.raises(RetailAttentionError):
        news_n_hourly({"timeline": GDELT.API_SHAPE["timeline"]}, accept_hourly=True)


def test_a_backwards_timeline_raises():
    backwards = {
        **GDELT.API_SHAPE,
        "timeline": [{"data": [
            {"date": "20191104T010000Z", "value": 1},
            {"date": "20191104T000000Z", "value": 2},
        ]}],
    }
    with pytest.raises(RetailAttentionError):
        news_n_hourly(backwards, accept_hourly=True)


# ===================================================================== the Robintrack fixture
@pytest.fixture(scope="module")
def holders():
    needs_d621_fixture(RT_FIXTURE)
    return read_holder_fixture(RT_FIXTURE)


def test_the_fixture_holds_the_six_tickers(holders):
    assert sorted({o.ticker for o in holders}) == sorted(BUILDER.TICKERS)


def test_the_fixture_is_monotone_within_each_ticker(holders):
    seen: dict[str, dt.datetime] = {}
    for obs in holders:
        prev = seen.get(obs.ticker)
        assert prev is None or obs.ts_utc > prev, (obs.ticker, obs.ts_utc)
        seen[obs.ticker] = obs.ts_utc


def test_every_holder_count_is_a_non_negative_integer(holders):
    for obs in holders:
        assert isinstance(obs.holders, int) and obs.holders >= 0


def test_every_ticker_carries_the_two_site_outages_and_no_others(holders):
    by_ticker: dict[str, list[HolderObs]] = {}
    for obs in holders:
        by_ticker.setdefault(obs.ticker, []).append(obs)
    for ticker, rows in by_ticker.items():
        found = BUILDER.gaps(rows)
        assert len(found) == 2, (ticker, found)
        assert [g[1][:10] for g in found] == ["2019-01-30", "2020-01-16"], (ticker, found)


def test_the_outages_read_as_none_through_the_library(holders):
    """The fixture's gaps and the module's declared `OUTAGES` are the same two holes: a day two
    days into each outage has no poll for any ticker."""
    for start, _end in OUTAGES:
        day = start.date() + dt.timedelta(days=2)
        for ticker in BUILDER.TICKERS:
            assert daily_holders(holders, ticker, day) is None, (ticker, day)


def test_boils_series_ends_early_and_the_meta_says_so(holders):
    """The one per-fund surprise: BOIL stops on 2020-04-21 where the other five run to
    2020-08-13. Pinned so a later reader does not assume a common end date."""
    last = {t: max(o.ts_utc for o in holders if o.ticker == t) for t in BUILDER.TICKERS}
    assert last["BOIL"].date() == dt.date(2020, 4, 21)
    for other in ("KOLD", "UCO", "SCO", "UNG", "USO"):
        assert last[other].date() == dt.date(2020, 8, 13)
    meta = json.loads(RT_META.read_text(encoding="utf-8"))
    assert "2020-04-21" in meta["boil_note"]


def test_the_fixture_matches_its_own_meta():
    from backtest_framework.validation.frozen import sha256_file

    needs_d621_fixture(RT_FIXTURE)
    meta = json.loads(RT_META.read_text(encoding="utf-8"))
    assert sha256_file(RT_FIXTURE, text_normalise=False) == meta["sha256"]
    assert meta["columns"] == list(HOLDER_COLUMNS)
    assert meta["rows"] == 115290


def test_the_p9_canadian_etps_are_not_in_the_archive():
    """HNU and HOU are the ledger's P9 Canadian leveraged natural-gas ETPs. They are TSX-listed
    and have no file in the 8,597-ticker Robinhood export, which is recorded so that nobody
    searches for them again."""
    export = REPO / "data" / "raw" / "robintrack" / "popularity_export"
    if not export.is_dir():
        pytest.skip("data/raw/robintrack is a gitignored cache and is not on this machine")
    for ticker in BUILDER.P9_NOT_ON_ROBINHOOD:
        assert not (export / f"{ticker}.csv").is_file()


def test_a_tampered_fixture_line_raises_on_read(tmp_path):
    """The reader is a guard, not a loader: a holder cell that is not an integer stops the read
    rather than being coerced."""
    bad = tmp_path / "bad.csv.gz"
    with gzip.open(bad, "wt", encoding="utf-8", newline="\n") as fh:
        fh.write(",".join(HOLDER_COLUMNS) + "\n")
        fh.write("USO,2019-11-04T13:00:00Z,12.5\n")
    with pytest.raises(RetailAttentionError):
        read_holder_fixture(bad)


def test_a_wrong_header_raises_on_read(tmp_path):
    bad = tmp_path / "bad.csv.gz"
    with gzip.open(bad, "wt", encoding="utf-8", newline="\n") as fh:
        fh.write("ticker,timestamp,holders\nUSO,2019-11-04T13:00:00Z,12\n")
    with pytest.raises(RetailAttentionError):
        read_holder_fixture(bad)


# ========================================================================= the GDELT fixture
def test_the_gdelt_hourly_fixture_is_hourly_and_names_its_corpus():
    needs_d621_fixture(GDELT_FIXTURE)
    meta = json.loads(GDELT_META.read_text(encoding="utf-8"))
    assert meta["rows_by_source"][GDELT.SOURCE_FILES] == meta["rows"]
    assert meta["rows_by_source"][GDELT.SOURCE_API] == 0
    with gzip.open(GDELT_FIXTURE, "rt", encoding="utf-8", newline="") as fh:
        header = tuple(fh.readline().rstrip("\n").split(","))
        assert header == GDELT.COLUMNS
        for line in fh:
            source, _qid, hour, avail, count, _tone = line.rstrip("\n").split(",")
            assert source == GDELT.SOURCE_FILES
            h = dt.datetime.strptime(hour, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
            a = dt.datetime.strptime(avail, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
            assert (h.minute, h.second) == (0, 0)
            assert a == h + dt.timedelta(hours=1)
            assert int(count) >= 0


def test_the_api_half_is_declared_deferred_and_names_the_tool():
    """A logged block names the tool. The deferral carries the URL, the two outcomes and the
    order they came in, so nobody repeats the probe to find out what happened."""
    needs_d621_fixture(GDELT_FIXTURE)
    meta = json.loads(GDELT_META.read_text(encoding="utf-8"))
    state = meta["api_state"]
    assert state["state"].startswith("DEFERRED")
    assert "urlopen" in state["tool"]
    assert state["url"].startswith("https://api.gdeltproject.org/")
    outcomes = [a["outcome"] for a in state["attempts"]]
    assert outcomes == ["HTTP 429", "NO RESPONSE - TCP connect timed out"]


# ============================================================== the validation report itself
def test_the_validation_json_reproduces_from_the_fixtures_byte_for_byte(requires_panel):
    """THE CLAIM THAT MAKES THE MEASUREMENT CHECKABLE. The report carries no build timestamp --
    it carries the sha256 of every file it read -- so recomputing it from the committed fixtures
    must give the committed bytes. A number nobody can reproduce is a number nobody can check."""
    needs_d621_fixture(RT_FIXTURE)
    needs_d621_fixture(GDELT_FIXTURE)
    requires_panel(NAV_FIXTURE)
    assert VALIDATION.is_file()
    assert REPORT.render(REPORT.compute()) == VALIDATION.read_text(encoding="utf-8")


def test_the_validation_json_says_what_it_is_not():
    payload = json.loads(VALIDATION.read_text(encoding="utf-8"))
    assert "NOT A SIGNAL TEST" in payload["what_this_is"]
    assert "no null is run" in payload["what_this_is"]
    assert payload["inputs"]["fund_nav_daily"]["reserved_from"] == "2024-01-01"


def test_every_correlation_cell_carries_both_statistics_and_its_own_n():
    """R17's shape, applied to a correlation: a rank statistic and a product-moment statistic are
    reported together or not at all, and each cell states the n it was computed on."""
    payload = json.loads(VALIDATION.read_text(encoding="utf-8"))
    for fund, cell in payload["per_fund"].items():
        for name in ("correlations", "correlations_nonzero_creation"):
            for lag, values in cell[name].items():
                if lag == "why":
                    continue
                assert set(values) >= {"n", "spearman", "pearson"}, (fund, name, lag)
                assert isinstance(values["n"], int)


def test_the_report_reads_the_panel_through_the_chokepoint_with_the_seal_on_it():
    payload = json.loads(VALIDATION.read_text(encoding="utf-8"))
    window = payload["inputs"]["fund_nav_daily"]["window_record"]
    assert window["reserved_from"] == "2024-01-01"
    assert window["reserved_rows_read"] == 0
    assert window["last_session_read"] < "2024-01-01"


def test_the_report_counts_the_effective_number_of_cells_honestly():
    """Four funds, two underlyings, one issuer. The record must not read as four confirmations
    and the artefact says so in its own conventions block."""
    payload = json.loads(VALIDATION.read_text(encoding="utf-8"))
    assert "NOT FOUR EXPERIMENTS" in payload["conventions"]["independence"]


def test_the_two_funds_with_no_share_count_say_why():
    payload = json.loads(VALIDATION.read_text(encoding="utf-8"))
    assert sorted(payload["holders_only"]) == ["UNG", "USO"]
    for cell in payload["holders_only"].values():
        assert "no free NAV" in cell["why_no_truth"]
        assert cell["d_holders"]["n"] > 100


def test_the_dropped_polls_are_counted_and_never_zero_filled():
    """BOIL's holder series stops four months early, so its steps after 2020-04-21 have no
    second end. They are DROPPED AND COUNTED, and the count is what makes that visible."""
    payload = json.loads(VALIDATION.read_text(encoding="utf-8"))
    boil = payload["per_fund"]["BOIL"]
    assert boil["n_dropped_for_missing_holder_poll"] > 0
    assert boil["n_paired"] + boil["n_dropped_for_missing_holder_poll"] == (
        boil["n_creation_steps_in_overlap"]
    )


# ============================================================ the report's own pairing helpers
def test_the_report_pairs_both_series_over_the_same_interval():
    series = CreationSeries(
        fund="T",
        deltas=((dt.date(2019, 11, 4), 10.0),),
        skipped=(),
        steps=((dt.date(2019, 11, 4), dt.date(2019, 11, 1)),),
    )
    index = {("T", dt.date(2019, 11, 1)): 50, ("T", dt.date(2019, 11, 4)): 60}
    rows = REPORT.pair(series, index, "T", dt.date(2019, 1, 1), dt.date(2020, 1, 1))
    assert rows == [(dt.date(2019, 11, 4), 10.0, 10.0)]


def test_the_report_drops_a_step_whose_either_end_has_no_poll():
    series = CreationSeries(
        fund="T",
        deltas=((dt.date(2019, 11, 4), 10.0),),
        skipped=(),
        steps=((dt.date(2019, 11, 4), dt.date(2019, 11, 1)),),
    )
    for index in (
        {("T", dt.date(2019, 11, 4)): 60},
        {("T", dt.date(2019, 11, 1)): 50},
        {},
    ):
        assert REPORT.pair(series, index, "T", dt.date(2019, 1, 1), dt.date(2020, 1, 1)) == []


def test_the_lag_convention_is_in_series_steps():
    rows = [
        (dt.date(2019, 11, 1) + dt.timedelta(days=k), float(k), float(k) * 2.0)
        for k in range(5)
    ]
    cells = REPORT.correlations(rows)
    assert cells["lag_0"]["n"] == 5
    assert cells["lag_+1"]["n"] == 4 and cells["lag_-1"]["n"] == 4
    assert cells["lag_0"]["spearman"] == 1.0


def test_the_report_describes_a_distribution_and_not_just_a_mean():
    out = REPORT.describe([1.0, 1.0, 1.0, 1.0, 100.0])
    assert out["mean"] == 20.8 and out["median"] == 1.0
    assert out["n_zero"] == 0 and out["n_positive"] == 5


# ===================================================================== the two script selftests
def test_the_builder_selftest_passes(tmp_path):
    assert BUILDER.selftest(tmp_path) == 0


def test_the_gdelt_selftest_passes():
    assert GDELT.selftest() == 0


def test_the_report_selftest_passes():
    assert REPORT.selftest() == 0


def test_the_selftests_can_actually_fail():
    """A self-test that cannot fail is worse than none. `expect_raise` is the idiom all three
    share, and it must itself raise when the guard it is pointed at does nothing."""
    for module in (BUILDER, GDELT, REPORT):
        with pytest.raises(AssertionError):
            module.expect_raise(lambda: None, AttentionError, "a function that never raises")
