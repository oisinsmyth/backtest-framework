"""Integration gates for the breakout study harness (D113–D116).

Offline: everything runs on the committed BTC/ETH fixture, no live fetch.

What these assert is not "the numbers are good" but "the numbers mean what the report
says they mean": the out-of-sample span really starts where training ends, nothing
trades inside the warm-up prefix, fitted parameters really are fitted on training bars
only, the cost tiers really are ordered, and the trial pool the DSR consumes really is
the variant rows and not the window rows.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.data.csv_fixture import load_fixture_csv_with_volumes
from backtest_framework.registry.trial_registry import TrialRegistry, compute_trial_hash
from backtest_framework.research import breakout_study as bs
from backtest_framework.simulator.fills import Bar

REPO = Path(__file__).resolve().parent.parent.parent
FIXTURE = REPO / "data" / "fixtures" / "crypto_daily_2015_2025_raw.csv.gz"
TOLERANCE = 1e-9


@pytest.fixture(scope="module")
def btc(requires_panel):
    requires_panel(FIXTURE)
    bars, _volumes = load_fixture_csv_with_volumes(FIXTURE)
    return bars["BTC-USD"]


@pytest.fixture(scope="module")
def btc_volumes(requires_panel):
    """The volume series that goes with `btc`, for variants carrying the volume filter
    (D168). A filter declaring `requires_volume` refuses to run without it, which is the
    whole point of the three-state design — so any test sweeping `filter_variants()` has
    to supply it."""
    requires_panel(FIXTURE)
    _bars, volumes = load_fixture_csv_with_volumes(FIXTURE)
    return volumes["BTC-USD"]


@pytest.fixture(scope="module")
def study():
    return bs.BreakoutStudyConfig()


# ------------------------------------------------------------- walk-forward geometry


def test_oos_span_starts_where_the_first_training_slice_ends(btc, study):
    spans = bs._window_spans(btc, study)
    window_index, train_start, test_start, test_end = spans[0]
    assert (window_index, train_start) == (0, 0)
    assert test_start == study.train_size
    assert test_end - test_start == study.test_size
    # Windows step by test_size and tile the OOS span with no gaps or overlaps.
    for (_, _, a_start, a_end), (_, _, b_start, _) in zip(spans, spans[1:]):
        assert b_start == a_end == a_start + study.test_size


def test_no_oos_bar_lies_inside_any_training_slice(btc, study):
    spans = bs._window_spans(btc, study)
    for _index, train_start, test_start, _test_end in spans:
        assert train_start < test_start
        assert test_start - train_start == study.train_size


def test_nothing_trades_during_the_warm_up_prefix(btc, study):
    """The prefix is exactly the strategy's warm-up requirement, so its own guard
    keeps it flat — in-sample P&L cannot reach the reported curve. run_variant
    asserts this internally; this test proves the assertion is reachable by checking
    the first fill lands on or after the first OOS bar."""
    spans = bs._window_spans(btc, study)
    oos_start = spans[0][2]
    tier = bs.DEFAULT_TIERS[-1]
    for variant in bs.plateau_variants()[:2] + bs.filter_variants()[:1]:
        result = bs.run_variant(btc, "BTC-USD", variant, tier, study)
        assert result.oos_equity[0][0] == btc[oos_start].timestamp
        assert result.oos_equity[0][1] == pytest.approx(study.starting_cash, rel=TOLERANCE)
        for episode in result.episodes:
            assert episode.entry_timestamp >= btc[oos_start].timestamp


def test_variant_matches_a_directly_constructed_strategy_over_the_same_span(btc, study):
    """The harness must add nothing to what the strategy does. Same bars, same stack,
    same fill timing, built by hand -> identical equity curve."""
    from backtest_framework.costs.bricks import PercentOfNotionalSpread
    from backtest_framework.costs.stack import CostStack
    from backtest_framework.engine.allocator import ConstantSplitAllocator
    from backtest_framework.engine.backtest import run_backtest
    from backtest_framework.instruments.equity import Equity
    from backtest_framework.strategies.breakout import build_breakout_strategy

    tier = bs.CostTier("taker_40bp", 40.0, "taker")
    variant = bs.Variant("plateau_40_10", "plateau", fixed_config=bs.breakout_config(40, 10))
    harness = bs.run_variant(btc, "BTC-USD", variant, tier, study)

    spans = bs._window_spans(btc, study)
    oos_start, oos_end = spans[0][2], spans[-1][3]
    strategy = build_breakout_strategy(variant.fixed_config, "breakout-BTC-USD", "BTC-USD")
    warm_up = strategy.warm_up_bars()
    direct = run_backtest(
        bars_by_instrument={"BTC-USD": list(btc[oos_start - warm_up : oos_end])},
        instruments={"BTC-USD": Equity(symbol="BTC-USD", quantity_precision=8)},
        strategies=[strategy],
        cost_stack=CostStack(trade_bricks=(PercentOfNotionalSpread(bps=40.0),)),
        allocator=ConstantSplitAllocator(),
        starting_cash=study.starting_cash,
        fill_timing="next_open",
    )
    for (ts_a, nav_a), (ts_b, nav_b) in zip(harness.oos_equity, direct.equity_curve[warm_up:]):
        assert ts_a == ts_b
        assert nav_a == pytest.approx(nav_b, rel=1e-12)


# --------------------------------------------------------------------- filter wiring


def test_debounce_m1_reproduces_the_baseline_through_the_whole_study(btc, study):
    """m=1 is the identity filter. If the filter machinery is wired correctly, a
    baseline with a 1-close debounce bolted on must be indistinguishable from the
    baseline — end to end, not just at the signal level."""
    tier = bs.DEFAULT_TIERS[-1]
    base = bs.run_variant(
        btc, "BTC-USD", bs.Variant("base", "plateau", fixed_config=bs.breakout_config(40, 10)), tier, study
    )
    debounced = bs.run_variant(
        btc,
        "BTC-USD",
        bs.Variant(
            "m1", "filter",
            fixed_config=bs.breakout_config(40, 10, filters=[{"type": "consecutive_close", "m": 1}]),
        ),
        tier,
        study,
    )
    assert base.final_nav == pytest.approx(debounced.final_nav, rel=1e-12)
    assert base.diagnostics.n_closed_trades == debounced.diagnostics.n_closed_trades


def test_each_filter_only_ever_removes_entries_relative_to_the_baseline_count(
    btc, btc_volumes, study
):
    """A veto cannot increase the number of entries taken on a fixed price path. (The
    entry BARS can shift — see the unit-test note — but the count cannot rise, because
    every entry the filtered strategy takes is one the baseline's raw condition also
    flagged, and the baseline takes every flagged entry it is flat for.)"""
    tier = bs.DEFAULT_TIERS[0]  # zero fees: isolate signal effects from cost effects
    base = bs.run_variant(
        btc, "BTC-USD", bs.Variant("base", "plateau", fixed_config=bs.breakout_config(40, 10)), tier, study
    )
    for variant in bs.filter_variants():
        filtered = bs.run_variant(btc, "BTC-USD", variant, tier, study, volumes=btc_volumes)
        assert len(filtered.episodes) <= len(base.episodes), variant.name


# ------------------------------------------------------------------ in-train fitting


def test_in_train_selection_never_sees_a_test_bar(btc, study):
    """The structural check (D22/D28's rule applied here): record every bar handed to
    the fitter and assert none of them is at or after that window's first test bar."""
    spans = bs._window_spans(btc, study)
    test_starts = [test_start for _i, _t, test_start, _e in spans]
    seen: list[tuple[datetime, datetime]] = []

    def recording_fit(train_bars, tier, cfg):
        seen.append((train_bars[0].timestamp, train_bars[-1].timestamp))
        return bs.breakout_config(40, 10)

    variant = bs.Variant("recorded", "selection", fit=recording_fit, fit_description={"probe": True})
    bs.run_variant(btc, "BTC-USD", variant, bs.DEFAULT_TIERS[-1], study)

    assert len(seen) == len(spans)
    for (first, last), test_start in zip(seen, test_starts):
        assert last < btc[test_start].timestamp, "fitter was handed a test bar"
        assert first == btc[test_start - study.train_size].timestamp


def test_the_fitted_schedule_switches_at_window_boundaries(btc, study):
    """A fitter that returns a different configuration each window must produce a
    schedule whose switch points are exactly the window test-start indices."""
    spans = bs._window_spans(btc, study)
    grid = [(20, 5), (30, 10), (40, 10), (55, 20)]
    calls = {"n": 0}

    def cycling_fit(train_bars, tier, cfg):
        n_entry, n_exit = grid[calls["n"] % len(grid)]
        calls["n"] += 1
        return bs.breakout_config(n_entry, n_exit)

    variant = bs.Variant("cycling", "selection", fit=cycling_fit, fit_description={"probe": True})
    result = bs.run_variant(btc, "BTC-USD", variant, bs.DEFAULT_TIERS[-1], study)
    starts = [start for start, _config in result.schedule]
    assert starts == [test_start for _i, _t, test_start, _e in spans]


def test_scheduled_breakout_carries_its_position_across_a_parameter_swap():
    """The reason the study runs continuously (D113): a schedule switch must not
    flatten the book. Built as a unit here so the guarantee is visible without a
    10-year backtest around it."""
    from backtest_framework.engine.dataview import build_data_view

    closes = [100 + i for i in range(60)]
    bars = [Bar(open=c, high=c + 0.5, low=c - 0.5, close=c) for c in closes]
    strategy = bs.ScheduledBreakout(
        "s", "X", ((0, bs.breakout_config(20, 5, weight_source={"type": "fixed_weight", "fraction": 1.0})),
                   (40, bs.breakout_config(30, 10, weight_source={"type": "fixed_weight", "fraction": 1.0}))),
    )
    weights = [
        strategy.generate_targets({"X": build_data_view(bars, i)})[0].weight for i in range(len(bars))
    ]
    assert weights[39] > 0 and weights[40] > 0, "position dropped at the schedule switch"
    assert all(w > 0 for w in weights[30:])


def test_scheduled_breakout_warm_up_is_the_max_across_the_schedule():
    strategy = bs.ScheduledBreakout(
        "s", "X", ((0, bs.breakout_config(20, 5)), (300, bs.breakout_config(55, 20))),
    )
    assert strategy.warm_up_bars() == max(
        bs.ScheduledBreakout("s", "X", ((0, bs.breakout_config(20, 5)),)).warm_up_bars(),
        bs.ScheduledBreakout("s", "X", ((0, bs.breakout_config(55, 20)),)).warm_up_bars(),
    )


def test_schedule_must_start_at_zero_and_increase():
    with pytest.raises(ValueError, match="begin at index 0"):
        bs.ScheduledBreakout("s", "X", ((5, bs.breakout_config()),))
    with pytest.raises(ValueError, match="strictly increasing"):
        bs.ScheduledBreakout("s", "X", ((0, bs.breakout_config()), (0, bs.breakout_config(20, 5))))


# ------------------------------------------------------------------------ cost tiers


def test_final_nav_is_non_increasing_in_the_fee_tier(btc, study):
    """The D8 sweep gate applied to this study's tiers: dearer execution can never
    produce a better result on an identical strategy and path."""
    variant = bs.Variant("base", "plateau", fixed_config=bs.breakout_config(40, 10))
    navs = [bs.run_variant(btc, "BTC-USD", variant, tier, study).final_nav for tier in bs.DEFAULT_TIERS]
    assert [t.fee_bps for t in bs.DEFAULT_TIERS] == sorted(t.fee_bps for t in bs.DEFAULT_TIERS)
    for cheaper, dearer in zip(navs, navs[1:]):
        assert dearer <= cheaper + 1e-6


def test_zero_fee_tier_charges_nothing(btc, study):
    variant = bs.Variant("base", "plateau", fixed_config=bs.breakout_config(40, 10))
    result = bs.run_variant(btc, "BTC-USD", variant, bs.DEFAULT_TIERS[0], study)
    assert result.diagnostics.total_costs == 0.0
    assert result.diagnostics.cost_share_of_gross == 0.0


# ------------------------------------------------------------------------- benchmark


def test_analytic_buy_and_hold_agrees_with_the_engine_run_version(btc, study):
    """Cross-check between the reported benchmark (fixed quantity, computed directly)
    and the same thing expressed as a constant 100% target weight through the engine.
    They differ only by the close-to-open sizing gap (D115); a large divergence would
    mean one of them is not buy-and-hold."""
    for tier in bs.DEFAULT_TIERS:
        analytic = bs.run_benchmark(btc, "BTC-USD", tier, study)
        engine = bs.run_benchmark_via_engine(btc, "BTC-USD", tier, study)
        assert analytic.total_return == pytest.approx(engine.total_return, rel=2e-4)
        assert analytic.max_drawdown == pytest.approx(engine.max_drawdown, rel=1e-3)


def test_benchmark_covers_exactly_the_strategy_oos_span(btc, study):
    variant = bs.Variant("base", "plateau", fixed_config=bs.breakout_config(40, 10))
    strategy_result = bs.run_variant(btc, "BTC-USD", variant, bs.DEFAULT_TIERS[-1], study)
    benchmark = bs.run_benchmark(btc, "BTC-USD", bs.DEFAULT_TIERS[-1], study)
    assert [ts for ts, _ in benchmark.oos_equity] == [ts for ts, _ in strategy_result.oos_equity]
    assert len(benchmark.oos_returns) == len(strategy_result.oos_returns)


def test_benchmark_is_not_rebalanced(btc, study):
    """Fixed quantity: the benchmark's return between any two bars equals the
    instrument's price return exactly, from the second OOS bar onward (cash is zero
    to rounding after the single entry)."""
    tier = bs.DEFAULT_TIERS[0]
    benchmark = bs.run_benchmark(btc, "BTC-USD", tier, study)
    spans = bs._window_spans(btc, study)
    series = btc[spans[0][2] : spans[-1][3]]
    for i in range(2, len(series)):
        price_return = series[i].bar.close / series[i - 1].bar.close - 1.0
        assert benchmark.oos_returns[i - 1] == pytest.approx(price_return, rel=1e-9)


# -------------------------------------------------------------- registry and the DSR


@pytest.fixture(scope="module")
def small_study(btc, tmp_path_factory):
    """A deliberately small study — one symbol, two tiers, four variants including the
    fitted one — so the registry/DSR wiring is exercised end to end without a 90-second
    test."""
    study_config = bs.BreakoutStudyConfig()
    tiers = (bs.DEFAULT_TIERS[0], bs.DEFAULT_TIERS[-1])
    registry = TrialRegistry(tmp_path_factory.mktemp("registry") / "trials.sqlite")
    variants, selector = bs.default_variants("BTC-USD", study_config)
    keep = {"plateau_20_5", "plateau_40_10", "filter_trend_gate_200", "selected_in_train"}

    original = bs.default_variants

    def patched(symbol, cfg):
        vs, sel = original(symbol, cfg)
        return [v for v in vs if v.name in keep], sel

    bs.default_variants = patched
    try:
        result = bs.run_breakout_study(
            {"BTC-USD": btc}, registry, snapshot_id="test-snapshot", study=study_config, tiers=tiers,
            trial_id_prefix="itest",
        )
    finally:
        bs.default_variants = original
    yield result, registry
    registry.close()


def test_every_variant_and_window_is_logged_once(small_study):
    result, registry = small_study
    symbol_result = result.by_symbol["BTC-USD"]
    n_variants, n_tiers = len(result.variant_names), len(result.tiers)
    expected = n_variants * n_tiers * (1 + symbol_result.n_windows)
    assert len(registry) == expected
    kinds = [t.config["row_kind"] for t in registry.all_trials()]
    assert kinds.count("variant") == n_variants * n_tiers
    assert kinds.count("window") == n_variants * n_tiers * symbol_result.n_windows


def test_trial_hashes_distinguish_every_configuration(small_study):
    _result, registry = small_study
    variant_rows = [t for t in registry.all_trials() if t.config["row_kind"] == "variant"]
    hashes = {t.trial_hash for t in variant_rows}
    assert len(hashes) == len(variant_rows), "two different configurations hashed identically"
    for trial in variant_rows:
        assert trial.trial_hash == compute_trial_hash(trial.config, trial.snapshot_id, trial.seed)
        assert trial.snapshot_id == "test-snapshot"


def test_logged_config_rebuilds_the_strategy_that_ran(small_study):
    """D102's rule, applied here: the dict the registry hashes is the dict the
    strategy is built from, so a logged trial can be reconstructed exactly."""
    from backtest_framework.strategies.breakout import build_breakout_strategy

    _result, registry = small_study
    for trial in registry.all_trials():
        if trial.config["row_kind"] != "variant":
            continue
        for _start, strategy_config in trial.config["resolved_schedule"]:
            rebuilt = build_breakout_strategy(strategy_config, "s", trial.config["symbol"])
            assert rebuilt.config() == strategy_config


def test_dsr_pool_is_the_variant_rows_at_one_symbol_and_tier(small_study):
    result, registry = small_study
    symbol_result = result.by_symbol["BTC-USD"]
    for tier in result.tiers:
        inputs = symbol_result.dsr_inputs_by_tier[tier.name]
        assert inputs["n_trials"] == len(result.variant_names)
        assert 0.0 <= symbol_result.dsr_by_tier[tier.name] <= 1.0
        assert inputs["t"] == symbol_result.n_oos_bars - 1
        assert not math.isnan(inputs["var_trials_daily"])


def test_study_is_reproducible(btc, small_study, tmp_path):
    """Same inputs -> same numbers. Re-runs one variant and compares to the study's
    stored result to the last bit."""
    result, _registry = small_study
    stored = result.by_symbol["BTC-USD"].variants[("plateau_40_10", "taker_40bp")]
    rerun = bs.run_variant(
        btc,
        "BTC-USD",
        bs.Variant("plateau_40_10", "plateau", fixed_config=bs.breakout_config(40, 10)),
        bs.DEFAULT_TIERS[-1],
        result.config,
    )
    assert rerun.final_nav == stored.final_nav
    assert rerun.oos_returns == stored.oos_returns
