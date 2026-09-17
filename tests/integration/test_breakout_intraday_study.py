"""Integration gates for the cost-frequency frontier (D160-D165).

Offline: the end-to-end gates run on a deterministic synthetic hourly series, and the
fixture gates run on the committed intraday fixture (skipped if it is absent, since it
is a one-time manual fetch).

What these assert is not "the frontier is right" but "the frontier means what the report
says it means": every frequency really did get the same number of walk-forward windows,
every cell really was logged with a distinct hash, the cost tiers really are ordered at
every frequency, the sizing brick and the metrics layer really do share one calendar, and
the resample-to-daily really does or does not reconcile with the provider's own bars.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.data.cleaner import clean
from backtest_framework.data.corporate_actions import CorporateActions
from backtest_framework.data.csv_fixture import load_fixture_csv_with_volumes, save_fixture_csv
from backtest_framework.data.snapshot_store import SnapshotStore
from backtest_framework.data.validator import validate
from backtest_framework.registry.trial_registry import TrialRegistry
from backtest_framework.research import breakout_intraday as bi
from backtest_framework.research import breakout_study as bs
from backtest_framework.simulator.fills import Bar

REPO = Path(__file__).resolve().parent.parent.parent
FIXTURES = REPO / "data" / "fixtures"
HOURLY_FIXTURE = FIXTURES / "crypto_intraday_1h_raw.csv.gz"
DAILY_FIXTURE = FIXTURES / "crypto_daily_2015_2025_raw.csv.gz"

SYMBOL = "SYN-USD"
TIERS = (bs.DEFAULT_TIERS[0], bs.DEFAULT_TIERS[2], bs.DEFAULT_TIERS[3])


def synthetic_hourly(n_days: int = 450, seed: int = 7):
    """A deterministic trending-then-reverting hourly series with real OHLC shape.

    Built from an explicit LCG rather than numpy so the series is byte-identical on any
    platform (D34's spirit: a stochastic input gets a stated, reproducible seed)."""
    state = seed
    def uniform() -> float:
        nonlocal state
        state = (1103515245 * state + 12345) % (1 << 31)
        return state / (1 << 31)

    bars, volumes = [], []
    price = 100.0
    start = datetime(2024, 1, 1)
    for i in range(n_days * 24):
        # A slow regime cycle (120-day period) so even the 1d rung's 40-bar breakout
        # sees genuine trends and reversals rather than a random walk it never trades.
        # A cell that never trades has a flat NAV, an infinite Sharpe and no place in
        # the DSR pool — `_dsr_for` refuses it loudly, which is the correct behaviour
        # and a useless test fixture.
        drift = 0.0008 * math.sin(2 * math.pi * i / (24 * 120))
        shock = (uniform() - 0.5) * 0.012
        close = price * (1.0 + drift + shock)
        high = max(price, close) * (1.0 + 0.004 * uniform())
        low = min(price, close) * (1.0 - 0.004 * uniform())
        bars.append(
            TimestampedBar(
                timestamp=start + timedelta(hours=i),
                bar=Bar(open=price, high=high, low=low, close=close),
            )
        )
        volumes.append(1000.0 + 100.0 * uniform())
        price = close
    return bars, volumes


@pytest.fixture(scope="module")
def synthetic_series():
    bars, volumes = synthetic_hourly()
    series, census, _reports = bi.frequency_series(bars, volumes)
    return series, census


@pytest.fixture(scope="module")
def frontier(synthetic_series, tmp_path_factory):
    """Design B across three rungs and three tiers — cheap enough to run in a test, and
    it exercises exactly the paths the study runs."""
    series, census = synthetic_series
    registry = TrialRegistry(tmp_path_factory.mktemp("registry") / "frontier.sqlite")
    result = bi.run_frontier(
        {SYMBOL: series},
        census,
        registry,
        snapshot_id="synthetic",
        frequencies=(bi.FREQ_1H, bi.Frequency("4h", 240), bi.Frequency("1d", 1440)),
        designs=(bi.DESIGN_B,),
        tiers=TIERS,
    )
    yield result, registry
    registry.close()


# ------------------------------------------------------- equal windows, equal calendar


def test_every_frequency_gets_the_same_number_of_walk_forward_windows(frontier):
    result, _registry = frontier
    counts = {key: row.n_windows for key, row in result.rows.items()}
    assert len(set(counts.values())) == 1, counts
    assert result.n_windows == bi.window_count(len(result.census.complete))
    assert result.n_windows >= 2


def test_every_frequency_covers_the_same_out_of_sample_calendar(frontier):
    """Equal window COUNTS are not enough — the windows must also cover the same days,
    or the ladder compares spans instead of frequencies."""
    result, _registry = frontier
    spans = {
        (row.frequency.name, row.tier.name): (
            row.result.oos_equity[0][0].date(),
            row.result.oos_equity[-1][0].date(),
        )
        for row in result.rows.values()
    }
    starts = {start for start, _end in spans.values()}
    assert len(starts) == 1, spans
    # End dates differ only by the intra-day timestamp of the final bar, never by a day.
    ends = {end for _start, end in spans.values()}
    assert len(ends) == 1, spans


def test_daily_return_series_are_the_same_length_at_every_frequency(frontier):
    """The DSR pool's units contract (D164) requires one T across a multi-frequency
    pool. That is only true if the day-collapsed curves line up."""
    result, _registry = frontier
    assert len({len(row.daily_returns) for row in result.rows.values()}) == 1


# ---------------------------------------------------------------------- cost ordering


def test_costs_are_monotone_across_tiers_at_every_frequency(frontier):
    """Final NAV is non-increasing in the fee, and total costs are non-decreasing —
    at every rung of the ladder, not just the daily one."""
    result, _registry = frontier
    ordered = sorted(TIERS, key=lambda t: t.fee_bps)
    for design in result.designs:
        for freq in result.frequencies:
            navs, costs = [], []
            for tier in ordered:
                row = result.row(SYMBOL, design.key, freq.name, tier.name)
                navs.append(row.result.final_nav)
                costs.append(row.result.diagnostics.total_costs)
            assert all(a >= b - 1e-9 for a, b in zip(navs, navs[1:])), (freq.name, navs)
            assert all(a <= b + 1e-9 for a, b in zip(costs, costs[1:])), (freq.name, costs)
            assert costs[0] == pytest.approx(0.0)  # maker_0bp charges nothing


def test_fee_drag_tracks_turnover_times_the_fee_rate(frontier):
    """`fee_drag_annual` is the sample-robust half of the frontier, so it had better be
    the arithmetic it claims to be: turnover x fee rate, to within the difference
    between average equity and the equity each individual fill was charged against."""
    result, _registry = frontier
    for row in result.rows.values():
        if row.tier.fee_bps == 0:
            assert row.fee_drag_annual == pytest.approx(0.0)
            continue
        implied = row.result.diagnostics.annual_turnover * row.tier.fee_bps / 10_000.0
        assert row.fee_drag_annual == pytest.approx(implied, rel=0.15)


def test_cost_drag_in_sharpe_units_matches_the_measured_gross_minus_net_wedge(frontier):
    """The frontier's cost curve is DERIVED (fee drag / vol); the wedge is MEASURED (run
    the same cell at 0 bp and at the tier and subtract). They must agree, or the
    conversion that lets a cost curve be compared against an outside gross edge is
    hand-waving.

    The tolerance widens with the wedge on purpose. `dSharpe ~ c/sigma` is a FIRST-ORDER
    approximation; once `c` reaches a large fraction of capital per year the two runs'
    position paths diverge outright and the linear term stops being the whole story. The
    report says so in the same words rather than quoting one tolerance for every rung."""
    result, _registry = frontier
    for design in result.designs:
        for freq in result.frequencies:
            for tier in TIERS:
                if tier.fee_bps == 0:
                    continue
                row = result.row(SYMBOL, design.key, freq.name, tier.name)
                wedge = bi.cost_wedge(result, SYMBOL, design.key, freq.name, tier.name)
                assert row.cost_drag_sharpe_units > 0
                assert abs(row.cost_drag_sharpe_units - wedge) <= max(0.15, 0.40 * abs(wedge))


# -------------------------------------------------------------------- registry hygiene


def test_every_cell_is_logged_once_with_a_distinct_hash(frontier):
    result, registry = frontier
    trials = registry.all_trials()
    assert len(trials) == len(result.rows)
    assert len({t.trial_id for t in trials}) == len(trials)
    assert len({t.trial_hash for t in trials}) == len(trials)


def test_the_logged_config_carries_both_copies_of_periods_per_year(frontier):
    """D17's rule has two homes in this study, and a trial that logged only one of them
    could not be audited for the mismatch `assert_periods_per_year_agree` prevents."""
    result, registry = frontier
    by_id = {t.trial_id: t for t in registry.all_trials()}
    for (symbol, design_key, freq_name, tier_name), row in result.rows.items():
        trial = by_id[f"breakout-intraday-v1-{symbol}-{design_key}-{freq_name}-{tier_name}"]
        assert trial.config["periods_per_year"] == row.frequency.periods_per_year
        assert (
            trial.config["strategy"]["weight_source"]["periods_per_year"]
            == row.frequency.periods_per_year
        )
        assert trial.config["row_kind"] == "variant"
        assert trial.config["bars_per_day"] == row.frequency.bars_per_day


def test_the_crossover_reads_the_ladder_from_slow_to_fast(frontier):
    result, _registry = frontier
    verdict = bi.crossover(result, SYMBOL, bi.DESIGN_B.key)
    assert [r["frequency"] for r in verdict["ladder"]] == ["1d", "4h", "1h"]
    # Turnover rises monotonically as the bar shrinks under Design B — the cost curve is
    # the half of the frontier that is measured rather than estimated.
    turnovers = [r["annual_turnover"] for r in verdict["ladder"]]
    assert all(a <= b for a, b in zip(turnovers, turnovers[1:])), turnovers
    assert set(verdict) >= {"sharpe_crossover", "cost_share_crossover", "spliced_crossover"}


# ------------------------------------------------------------------ fixture round-trip


def test_fixture_round_trip_preserves_intraday_bars_and_volumes(tmp_path):
    bars, volumes = synthetic_hourly(n_days=3)
    path = tmp_path / "round_trip.csv.gz"
    save_fixture_csv(path, {SYMBOL: bars}, {SYMBOL: volumes})
    loaded_bars, loaded_volumes = load_fixture_csv_with_volumes(path)
    assert loaded_bars[SYMBOL] == bars
    assert loaded_volumes[SYMBOL] == pytest.approx(volumes)
    # Sub-daily timestamps survive the CSV, which the daily fixtures never exercise.
    assert loaded_bars[SYMBOL][1].timestamp == bars[0].timestamp + timedelta(hours=1)


def test_snapshot_round_trip_preserves_the_resampled_ladder(tmp_path):
    """clean -> validate -> SnapshotStore -> load -> resample must give exactly what
    resampling the pre-snapshot series gives. A snapshot that quietly reordered or
    re-typed a bar would move every number in the study."""
    bars, volumes = synthetic_hourly(n_days=5)
    cleaned, report = clean({SYMBOL: bars})
    assert len(cleaned[SYMBOL]) == len(bars) and not report.changes
    validation = validate(cleaned, CorporateActions(), {SYMBOL: volumes})
    store = SnapshotStore(tmp_path / "snapshots")
    snapshot_id = store.create(
        cleaned, CorporateActions(), volumes_by_symbol={SYMBOL: volumes}, validation=validation
    )
    snapshot = store.load(snapshot_id)
    before, _c, _r = bi.frequency_series(bars, volumes)
    after, _c2, _r2 = bi.frequency_series(
        snapshot.bars_by_symbol[SYMBOL], snapshot.volumes_by_symbol[SYMBOL]
    )
    for freq in bi.STUDY_FREQUENCIES:
        assert after[freq.name][0] == before[freq.name][0]
        assert after[freq.name][1] == pytest.approx(before[freq.name][1])
    # Re-freezing identical bytes is idempotent (D72), so a re-run of the study logs the
    # same snapshot_id its report quotes.
    assert store.create(cleaned, CorporateActions(), volumes_by_symbol={SYMBOL: volumes}) == snapshot_id


# ------------------------------------------------- gates on the committed 1h fixture


@pytest.fixture(scope="module")
def committed_hourly(requires_panel):
    requires_panel(HOURLY_FIXTURE)
    return load_fixture_csv_with_volumes(HOURLY_FIXTURE)


def test_the_committed_fixture_yields_equal_window_counts_at_every_frequency(committed_hourly):
    bars, volumes = committed_hourly
    for symbol in bars:
        series, census, reports = bi.frequency_series(bars[symbol], volumes[symbol])
        expected = bi.window_count(len(census.complete))
        assert expected == 7
        for freq in bi.STUDY_FREQUENCIES:
            reports[freq.name].check()
            assert len(series[freq.name][0]) == len(census.complete) * freq.bars_per_day


def test_the_price_only_cleaner_drops_nothing_but_the_volume_rule_would_halve_it(
    committed_hourly,
):
    """The finding that decides how the study freezes its fixture, pinned so it cannot
    regress silently: yfinance reports Volume=0 on roughly half of all hourly crypto
    bars, and `clean-v1`'s `non_positive_volume` rule would delete every one of them."""
    bars, volumes = committed_hourly
    price_only, price_report = clean(bars)
    assert not price_report.changes
    assert all(len(price_only[s]) == len(bars[s]) for s in bars)

    _with_volumes, full_report = clean(bars, volumes)
    dropped = len(full_report.changes)
    total = sum(len(v) for v in bars.values())
    assert {c.rule for c in full_report.changes} == {"non_positive_volume"}
    assert 0.35 * total < dropped < 0.65 * total, f"{dropped} of {total}"


def test_the_sanity_gate_does_not_quarantine_intraday_bars_and_its_move_check_is_silent(
    committed_hourly,
):
    """Two claims the report makes about the gate, asserted rather than narrated: it
    passes (0 hard violations), and the reason the move check passes is that a 25%
    threshold is unreachable on hourly bars, not that the data is pristine."""
    bars, volumes = committed_hourly
    cleaned, _ = clean(bars)
    result = validate(cleaned, CorporateActions(), volumes)
    assert result.passed and not result.hard_violations
    assert {v.check for v in result.warnings} <= {"zero_volume", "volume_spike"}
    assert not [v for v in result.violations if v.check == "unexplained_move"]
    for series in cleaned.values():
        biggest = max(
            abs(series[i].bar.close / series[i - 1].bar.close - 1.0) for i in range(1, len(series))
        )
        assert biggest < 0.25  # the daily warning threshold is out of reach


def test_the_1h_to_1d_resample_does_not_reconcile_with_the_provider_daily_fixture(
    committed_hourly,
):
    """A negative gate, pinned because the discrepancy IS the finding (D161).

    The contract asked for floating-point agreement where the provider agrees. It does
    not agree: opens and closes are a couple of basis points apart with no sign bias,
    while the resampled high is below the provider's daily high on essentially every day
    and the resampled low above its daily low on most. Were this to start reconciling,
    the report's reconciliation section would be wrong and would need rewriting — which
    is exactly what a test is for."""
    if not DAILY_FIXTURE.exists():
        pytest.skip("daily fixture absent")
    bars, volumes = committed_hourly
    daily_bars, _ = load_fixture_csv_with_volumes(DAILY_FIXTURE)
    for symbol in bars:
        series, _census, _r = bi.frequency_series(
            bars[symbol], volumes[symbol], (bi.Frequency("1d", 1440),)
        )
        resampled = {tb.timestamp.date(): tb.bar for tb in series["1d"][0]}
        provider = {tb.timestamp.date(): tb.bar for tb in daily_bars[symbol]}
        common = sorted(set(resampled) & set(provider))
        assert len(common) > 400

        exact_closes = sum(
            1 for d in common if abs(resampled[d].close / provider[d].close - 1.0) < 1e-12
        )
        assert exact_closes < 0.2 * len(common), "provider now agrees — rewrite the report"

        highs_below = sum(1 for d in common if resampled[d].high <= provider[d].high + 1e-9)
        lows_above = sum(1 for d in common if resampled[d].low >= provider[d].low - 1e-9)
        assert highs_below > 0.95 * len(common)
        assert lows_above > 0.80 * len(common)


# ------------------------------------------------------------------ network (opt-in)


@pytest.mark.live_fetch
def test_yfinance_serves_hourly_crypto_bars_on_the_utc_hour_grid():
    """The one assumption the offline pipeline cannot check for itself: that the
    provider stamps intraday crypto bars in UTC, on the hour. If it ever stops, every
    bucket in the resampling contract is mis-anchored. Excluded from the default run
    (pyproject `addopts`); run with `pytest -m live_fetch`."""
    from datetime import date as _date

    from backtest_framework.data.yfinance_source import EquityDataSource

    end = _date.today()
    bars, volumes, dividends, splits = EquityDataSource().get_raw_history(
        "BTC-USD", end - timedelta(days=4), end, "1h"
    )
    assert bars and len(volumes) == len(bars)
    assert not dividends and not splits  # spot crypto, D108
    assert {tb.timestamp.minute for tb in bars} == {0}
    assert all(tb.timestamp.second == 0 for tb in bars)
    for a, b in zip(bars, bars[1:]):
        assert (b.timestamp - a.timestamp) % timedelta(hours=1) == timedelta(0)
