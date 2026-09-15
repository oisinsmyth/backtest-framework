"""Unit gates for the crypto-universe selection policy (D140-D144).

The policy is the load-bearing part of this study: it decides what the cross-section
*is*, and a bug in it would silently reintroduce exactly the survivorship bias the
study exists to measure. So these tests check the screen, not the strategy — that every
rule excludes what it should, that every exclusion is reported with a reason, and that
the committed fixture round-trips bit-for-bit.

Offline: synthetic series plus the committed fixture. No network.
"""

from __future__ import annotations

import json
import math
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from backtest_framework.data.corporate_actions import load_events_json
from backtest_framework.data.csv_fixture import load_fixture_csv_with_volumes, save_fixture_csv
from backtest_framework.research import breakout_study as bs
from backtest_framework.research import breakout_universe as bu
from backtest_framework.simulator.fills import Bar
from backtest_framework.data.bars import TimestampedBar

REPO = Path(__file__).resolve().parent.parent.parent
FIXTURE = REPO / "data" / "fixtures" / "crypto_universe_2015_2025_raw.csv.gz"
EVENTS = REPO / "data" / "fixtures" / "crypto_universe_2015_2025_raw_events.json"
META = REPO / "data" / "fixtures" / "crypto_universe_2015_2025_raw.meta.json"
END = date(2025, 12, 31)


# ---------------------------------------------------------------------- synthetics


def series(
    n: int,
    start: datetime = datetime(2018, 1, 1),
    first: float = 100.0,
    growth: float = 0.001,
    wobble: float = 0.03,
) -> list[TimestampedBar]:
    """A deterministic, strictly positive series with a real day-to-day move, so it
    passes the peg screen without any randomness in the test."""
    bars = []
    price = first
    for i in range(n):
        price *= 1.0 + growth + (wobble if i % 2 == 0 else -wobble)
        bars.append(
            TimestampedBar(
                timestamp=start + timedelta(days=i),
                bar=Bar(open=price, high=price * 1.01, low=price * 0.99, close=price),
            )
        )
    return bars


def volumes(bars, level: float = 50_000_000.0) -> list[float]:
    return [level] * len(bars)


# ------------------------------------------------------------------- the screen


def test_min_history_rule_excludes_short_series_and_names_the_reason():
    short, long = series(bu.DEFAULT_POLICY.min_bars - 1), series(bu.DEFAULT_POLICY.min_bars)
    selection = bu.apply_policy(
        {"SHORT": short, "LONG": long},
        {"SHORT": volumes(short), "LONG": volumes(long)},
        end_date=END,
    )
    assert selection.included == ("LONG",)
    assert "SHORT" in selection.excluded
    assert "min-history" in selection.excluded["SHORT"]
    assert str(bu.DEFAULT_POLICY.min_bars) in selection.excluded["SHORT"]


def test_min_history_threshold_admits_exactly_four_walk_forward_windows():
    """The 520-bar floor is justified by what it buys, so pin what it buys: a symbol at
    the threshold must produce four windows and a full year out of sample. If the study
    config ever changes, this fails rather than leaving the docstring's arithmetic to
    rot."""
    study = bs.BreakoutStudyConfig()
    spans = bs._window_spans(series(bu.DEFAULT_POLICY.min_bars), study)
    assert len(spans) == 4
    assert spans[-1][3] - spans[0][2] == 4 * study.test_size == 252


def test_liquidity_floor_excludes_thin_symbols_and_reports_the_statistic():
    bars = series(1000)
    floor = bu.DEFAULT_POLICY.min_median_daily_volume_usd
    selection = bu.apply_policy(
        {"THIN": bars, "THICK": bars},
        {"THIN": volumes(bars, floor - 1.0), "THICK": volumes(bars, floor)},
        end_date=END,
    )
    assert selection.included == ("THICK",)
    assert "liquidity floor" in selection.excluded["THIN"]
    # The floor is a >= comparison, so a symbol exactly at it is admitted.
    assert selection.coverage["THICK"].median_daily_volume == floor


def test_liquidity_floor_uses_the_median_not_the_mean():
    """A token with a handful of enormous launch days and nothing since must fail. If
    the screen used the mean, those few days would carry it over the floor."""
    bars = series(1000)
    spiky = [1.0] * 990 + [10_000_000_000.0] * 10
    selection = bu.apply_policy({"SPIKY": bars}, {"SPIKY": spiky}, end_date=END)
    assert "SPIKY" in selection.excluded
    assert selection.coverage["SPIKY"].mean_daily_volume > bu.DEFAULT_POLICY.min_median_daily_volume_usd
    assert selection.coverage["SPIKY"].median_daily_volume == 1.0


def test_peg_screen_excludes_a_stablecoin():
    """A pegged series never prints a breakout, so the strategy's Sharpe on it is
    undefined rather than bad — which would poison the DSR pool's variance."""
    pegged = [
        TimestampedBar(
            timestamp=datetime(2020, 1, 1) + timedelta(days=i),
            bar=Bar(open=1.0, high=1.0005, low=0.9995, close=1.0 + (0.0002 if i % 2 else -0.0002)),
        )
        for i in range(1000)
    ]
    selection = bu.apply_policy({"PEG": pegged}, {"PEG": volumes(pegged)}, end_date=END)
    assert "PEG" in selection.excluded
    assert "peg screen" in selection.excluded["PEG"]


def test_non_positive_prices_exclude_the_symbol():
    bars = series(1000)
    bars[500] = TimestampedBar(
        timestamp=bars[500].timestamp, bar=Bar(open=0.0, high=1.0, low=0.0, close=1.0)
    )
    selection = bu.apply_policy({"ZERO": bars}, {"ZERO": volumes(bars)}, end_date=END)
    assert "ZERO" in selection.excluded
    assert "non-positive" in selection.excluded["ZERO"]


def test_every_excluded_symbol_carries_a_reason_and_nothing_is_dropped_silently():
    """The screen must partition its input: included + excluded == everything handed in.
    A symbol that vanished from both would be an invisible exclusion, which is the exact
    failure mode this whole study is about."""
    good, short, thin = series(1000), series(100), series(1000)
    inputs = {"GOOD": good, "SHORT": short, "THIN": thin}
    selection = bu.apply_policy(
        inputs,
        {"GOOD": volumes(good), "SHORT": volumes(short), "THIN": volumes(thin, 1.0)},
        end_date=END,
    )
    assert set(selection.included) | set(selection.excluded) == set(inputs)
    assert not set(selection.included) & set(selection.excluded)
    assert all(reason for reason in selection.excluded.values())
    assert set(selection.coverage) == set(inputs)


def test_the_screen_never_looks_at_a_return_or_a_drawdown():
    """Two symbols with identical bar counts, volumes and per-bar variation but wildly
    different outcomes must be treated identically by the screen. That is the difference
    between a universe rule and a survivorship filter."""
    winner = series(1000, growth=0.004)
    loser = series(1000, growth=-0.004)
    selection = bu.apply_policy(
        {"WINNER": winner, "LOSER": loser},
        {"WINNER": volumes(winner), "LOSER": volumes(loser)},
        end_date=END,
    )
    assert set(selection.included) == {"WINNER", "LOSER"}
    assert selection.excluded == {}


# --------------------------------------------------------------- classification


def test_collapsed_label_is_terminal_drawdown_from_the_symbols_own_peak():
    # Rise, then fall to under 10% of the peak.
    rising = series(400, growth=0.01)
    peak = rising[-1].bar.close
    falling = [
        TimestampedBar(
            timestamp=rising[-1].timestamp + timedelta(days=i + 1),
            bar=Bar(
                open=peak * 0.99 ** (i + 1) * 1.001,
                high=peak * 0.99 ** (i + 1) * 1.01,
                low=peak * 0.99 ** (i + 1) * 0.98,
                close=peak * 0.99 ** (i + 1),
            ),
        )
        for i in range(400)
    ]
    bars = rising + falling
    coverage = bu.coverage_for("DEAD", bars, volumes(bars))
    assert coverage.terminal_drawdown > bu.DEFAULT_POLICY.collapse_terminal_drawdown
    # End date at the series' own last bar, so `delisted` cannot pre-empt the label
    # under test — the two rules are checked separately, below.
    assert bu.classify(coverage, bu.DEFAULT_POLICY, coverage.last_bar.date()) == bu.COLLAPSED

    alive = bu.coverage_for("ALIVE", rising, volumes(rising))
    assert bu.classify(alive, bu.DEFAULT_POLICY, alive.last_bar.date()) == bu.SURVIVED


def test_delisted_label_wins_over_collapsed_and_is_measured_from_the_end_date():
    bars = series(600)
    coverage = bu.coverage_for("GONE", bars, volumes(bars))
    # Series ends 2019-08-24-ish; an END far in the future makes it delisted.
    assert bu.classify(coverage, bu.DEFAULT_POLICY, END) == bu.DELISTED
    # An END right at the last bar makes it not delisted.
    assert bu.classify(coverage, bu.DEFAULT_POLICY, coverage.last_bar.date()) == bu.SURVIVED


def test_status_labels_are_only_assigned_to_included_symbols():
    good, short = series(1000), series(100)
    selection = bu.apply_policy(
        {"GOOD": good, "SHORT": short}, {"GOOD": volumes(good), "SHORT": volumes(short)}, end_date=END
    )
    assert set(selection.status) == set(selection.included)
    assert selection.survived + selection.collapsed == selection.included


# --------------------------------------------------------------- volume alignment


def test_align_volumes_reindexes_by_timestamp_and_refuses_foreign_bars():
    raw = series(20)
    raw_volumes = [float(i) for i in range(20)]
    cleaned = [tb for i, tb in enumerate(raw) if i % 3]  # simulate dropped bars
    aligned = bu.align_volumes(cleaned, raw, raw_volumes)
    assert aligned == [float(i) for i in range(20) if i % 3]

    foreign = [TimestampedBar(timestamp=datetime(1999, 1, 1), bar=raw[0].bar)]
    with pytest.raises(ValueError, match="no raw volume"):
        bu.align_volumes(foreign, raw, raw_volumes)
    with pytest.raises(ValueError, match="misaligned input"):
        bu.align_volumes(cleaned, raw, raw_volumes[:-1])


# ------------------------------------------------------------------- arithmetic


def test_distribution_reports_the_whole_shape_and_ignores_nans():
    d = bu.distribution([1.0, 2.0, 3.0, 4.0, float("nan")])
    assert d["n"] == 4
    assert d["min"] == 1.0 and d["max"] == 4.0
    assert d["median"] == 2.5
    assert d["mean"] == 2.5


def test_rate_excludes_undefined_comparisons_from_both_sides():
    wins, total, fraction = bu._rate([True, False, None, True])
    assert (wins, total) == (2, 3)
    assert fraction == pytest.approx(2 / 3)


def test_risk_free_return_compounds_at_the_studys_own_rate():
    study = bs.BreakoutStudyConfig()
    one_year = bu.risk_free_return(int(study.periods_per_year), study)
    assert one_year == pytest.approx(study.rf_annual, rel=1e-12)


# ------------------------------------------------------------- fixture round-trip


@pytest.fixture(scope="module")
def fixture_data(requires_panel):
    requires_panel(FIXTURE)
    return load_fixture_csv_with_volumes(FIXTURE)


@pytest.fixture(scope="module")
def fixture_meta():
    return json.loads(META.read_text(encoding="utf-8"))


def test_fixture_round_trips_bit_for_bit(fixture_data, tmp_path_factory):
    """save -> load -> identical bars. The fixture is the study's data of record; if a
    round trip is lossy, every number downstream is quoting a different series from the
    one committed."""
    bars, volumes_by_symbol = fixture_data
    out = tmp_path_factory.mktemp("roundtrip") / "universe.csv.gz"
    save_fixture_csv(out, bars, volumes_by_symbol)
    reloaded_bars, reloaded_volumes = load_fixture_csv_with_volumes(out)
    assert set(reloaded_bars) == set(bars)
    for symbol in bars:
        assert reloaded_bars[symbol] == bars[symbol]
        assert reloaded_volumes[symbol] == volumes_by_symbol[symbol]


def test_every_bar_in_the_fixture_is_stamped_midnight(fixture_data):
    """D108's bar-boundary rule, checked on the committed data rather than trusted from
    the fetch script that wrote it."""
    bars, _ = fixture_data
    for symbol, series_ in bars.items():
        stamps = {(tb.timestamp.hour, tb.timestamp.minute, tb.timestamp.second) for tb in series_}
        assert stamps == {(0, 0, 0)}, f"{symbol} has bars off the 00:00 UTC boundary: {stamps}"
        assert all(tb.timestamp.tzinfo is None for tb in series_)


def test_events_sidecar_is_empty_by_construction(fixture_data):
    """Spot crypto has no dividends and no splits. An events sidecar with an entry in it
    would mean the provider frame is not what this fixture assumes — and a silently
    dropped event would be the same lie in the other direction (D48/D108)."""
    bars, _ = fixture_data
    actions = load_events_json(EVENTS)
    assert set(actions.dividends_by_symbol) == set(bars)
    assert set(actions.splits_by_symbol) == set(bars)
    assert all(not v for v in actions.dividends_by_symbol.values())
    assert all(not v for v in actions.splits_by_symbol.values())


def test_fixture_timestamps_are_unique_and_ordered(fixture_data):
    bars, _ = fixture_data
    for symbol, series_ in bars.items():
        stamps = [tb.timestamp for tb in series_]
        assert stamps == sorted(stamps), f"{symbol} bars are not in order"
        assert len(set(stamps)) == len(stamps), f"{symbol} has duplicate timestamps"


def test_cleaning_removes_every_non_positive_price_before_the_engine_sees_it(fixture_data):
    """The RAW fixture is allowed to contain provider garbage — it is the raw record
    (D6), and `AAVE-USD`'s first bar really does print open=low=0. What must be true is
    that nothing non-positive survives cleaning, because the strategy's log returns and
    inverse-vol sizing are undefined on a zero price and would raise or silently produce
    nonsense.

    This is the level the policy screens at, and this test pins that the two agree."""
    from backtest_framework.data.cleaner import clean

    bars, volumes_by_symbol = fixture_data
    raw_bad = {
        symbol
        for symbol, series_ in bars.items()
        for tb in series_
        if min(tb.bar.open, tb.bar.high, tb.bar.low, tb.bar.close) <= 0
    }
    cleaned, _report = clean(bars, volumes_by_symbol)
    for symbol, series_ in cleaned.items():
        for tb in series_:
            b = tb.bar
            assert min(b.open, b.high, b.low, b.close) > 0, f"{symbol} {tb.timestamp}"
            assert b.low <= b.high + 1e-9 * abs(b.high), f"{symbol} {tb.timestamp}"
    # And the policy agrees: no admitted symbol carries a non-positive bar after cleaning.
    for symbol in cleaned:
        coverage = bu.coverage_for(
            symbol, cleaned[symbol], bu.align_volumes(cleaned[symbol], bars[symbol], volumes_by_symbol[symbol])
        )
        assert coverage.n_nonpositive_bars == 0
    assert raw_bad, "if the raw fixture ever stops containing garbage, this test stops testing"


# -------------------------------------------------- the committed fixture obeys the policy


def test_the_committed_fixture_contains_exactly_what_the_policy_admits(fixture_data, fixture_meta):
    """The fixture and the meta must agree, and both must agree with a fresh application
    of the policy. If they ever disagree, the fixture has drifted from the rule that
    produced it."""
    bars, volumes_by_symbol = fixture_data
    from backtest_framework.data.cleaner import clean

    cleaned, _report = clean(bars, volumes_by_symbol)
    aligned = {s: bu.align_volumes(cleaned[s], bars[s], volumes_by_symbol[s]) for s in cleaned}
    selection = bu.apply_policy(cleaned, aligned, end_date=date.fromisoformat(fixture_meta["end"]))
    assert selection.excluded == {}
    assert set(selection.included) == set(bars) == set(fixture_meta["symbols_included"])
    assert selection.status == fixture_meta["status_by_symbol"]


def test_the_meta_records_every_attempted_symbol_with_an_outcome(fixture_meta):
    """A documented 'could not obtain' is evidence; a silent omission is the bias."""
    attempted = set(fixture_meta["symbols_requested"])
    accounted = (
        set(fixture_meta["symbols_included"])
        | set(fixture_meta["symbols_excluded"])
        | set(fixture_meta["fetch_failures"])
    )
    assert accounted == attempted
    assert all(reason for reason in fixture_meta["symbols_excluded"].values())
    assert all(reason for reason in fixture_meta["fetch_failures"].values())
    # Coverage statistics survive for excluded symbols too, so an exclusion can be
    # audited without re-fetching.
    for symbol in fixture_meta["symbols_excluded"]:
        assert symbol in fixture_meta["coverage"]


def test_the_universe_actually_contains_failed_assets(fixture_meta):
    """The study's entire premise. If the collapsed bucket were empty or trivial, the
    cross-section would be the same survivorship bias at greater scale, and the report's
    headline would be meaningless."""
    statuses = fixture_meta["status_by_symbol"]
    collapsed = [s for s, st in statuses.items() if st in bu.COLLAPSED_BUCKET]
    survived = [s for s, st in statuses.items() if st == bu.SURVIVED]
    assert len(collapsed) >= 20, "the universe must contain a substantial failed cohort"
    assert len(survived) >= 10, "and enough survivors to split against"
    # The named, deliberately-sought failures made it in.
    assert "LUNC-USD" in statuses and statuses["LUNC-USD"] in bu.COLLAPSED_BUCKET
    assert "FTT-USD" in statuses and statuses["FTT-USD"] in bu.COLLAPSED_BUCKET


def test_terminal_drawdown_in_the_meta_matches_the_committed_bars(fixture_data, fixture_meta):
    """The hindsight label is computed from the data, so it must be re-derivable from
    the data — not a hand-typed annotation."""
    bars, _ = fixture_data
    for symbol, recorded in fixture_meta["coverage"].items():
        if symbol not in bars:
            continue  # excluded symbols are not in the fixture, only in the meta
        closes = [tb.bar.close for tb in bars[symbol]]
        expected = 1.0 - closes[-1] / max(closes)
        assert recorded["terminal_drawdown"] == pytest.approx(expected, rel=1e-6)
        assert math.isfinite(recorded["median_abs_daily_return"])
