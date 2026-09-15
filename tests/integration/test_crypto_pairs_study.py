"""Integration gates for the BTC/ETH pairs study harness (D122-D127).

Offline: everything runs on the committed BTC/ETH fixture, no live fetch.

What these assert is not "the numbers are good" but "the numbers mean what the report
says they mean": the out-of-sample span really starts where training ends, nothing trades
inside the warm-up prefix, the D45 truncation to ETH's inception really happened, the
cost tiers really are ordered, the benchmarks really cover the same span, the registry
rows are unique and hash what ran, and the trial pool the DSR consumes really is the
configuration rows and not the window rows.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from backtest_framework.data.csv_fixture import load_fixture_csv_with_volumes
from backtest_framework.registry.trial_registry import TrialRegistry, compute_trial_hash
from backtest_framework.research import crypto_pairs_study as cp
from backtest_framework.research.breakout_study import DEFAULT_TIERS

REPO = Path(__file__).resolve().parent.parent.parent
FIXTURE = REPO / "data" / "fixtures" / "crypto_daily_2015_2025_raw.csv.gz"
TOLERANCE = 1e-9


@pytest.fixture(scope="module")
def bars(requires_panel):
    requires_panel(FIXTURE)
    loaded, _volumes = load_fixture_csv_with_volumes(FIXTURE)
    return loaded


@pytest.fixture(scope="module")
def config():
    return cp.CryptoPairsConfig()


@pytest.fixture(scope="module")
def series(bars, config):
    return cp.aligned_series(bars, config)


@pytest.fixture(scope="module")
def baseline():
    return cp.PairsVariant(cp.baseline_name(), "grid")


# ------------------------------------------------------------------ the D45 truncation


def test_alignment_truncates_the_pair_to_eth_inception(bars, series):
    """D45/D63's inner join, asserted rather than described. The report's "the sample is
    ETH's, not BTC's" claim — and the fact that no number in it shares a span with
    BREAKOUT_RESULTS.md's BTC rows — rests entirely on this."""
    assert len(bars["BTC-USD"]) > len(bars["ETH-USD"])
    assert len(series["BTC-USD"]) == len(series["ETH-USD"]) == len(bars["ETH-USD"])
    assert series["BTC-USD"][0].timestamp == bars["ETH-USD"][0].timestamp
    assert [tb.timestamp for tb in series["BTC-USD"]] == [
        tb.timestamp for tb in series["ETH-USD"]
    ]


# ------------------------------------------------------------- walk-forward geometry


def test_oos_span_starts_where_the_first_training_slice_ends(series, config):
    spans = cp.window_spans(series, config)
    window_index, train_start, test_start, test_end = spans[0]
    assert (window_index, train_start) == (0, 0)
    assert test_start == config.train_size
    assert test_end - test_start == config.test_size
    # Windows step by test_size and tile the OOS span with no gaps or overlaps.
    for (_, _, a_start, a_end), (_, _, b_start, _) in zip(spans, spans[1:]):
        assert b_start == a_end == a_start + config.test_size


def test_no_oos_bar_lies_inside_any_training_slice(series, config):
    spans = cp.window_spans(series, config)
    for _index, train_start, test_start, _test_end in spans:
        assert test_start - train_start == config.train_size
        assert train_start < test_start


def test_nothing_trades_before_the_first_oos_bar(series, config, baseline):
    """The warm-up prefix is exactly `lookback` bars, so the strategy's own guard keeps
    it flat throughout it and no in-sample P&L can reach the reported curve (D123).
    `run_variant` raises if a fill lands in the prefix; this proves the assertion is
    reachable by checking the curve starts flat at exactly the first OOS bar.

    The earliest possible fill is the SECOND OOS bar's open: the last prefix bar has only
    `lookback` visible bars, one short of the window the strategy needs, so it produces no
    order at all; the first OOS bar is the first decision, and under next_open it fills a
    bar later."""
    spans = cp.window_spans(series, config)
    oos_start = spans[0][2]
    for tier in (DEFAULT_TIERS[0], DEFAULT_TIERS[-1]):
        result = cp.run_variant(series, baseline, tier, config)
        assert result.oos_equity[0][0] == series["BTC-USD"][oos_start].timestamp
        assert result.oos_equity[0][1] == pytest.approx(config.starting_cash, rel=TOLERANCE)
        assert result.oos_fills, "the baseline never traded — the test proves nothing"
        first_fill = min(ts for ts, *_ in result.oos_fills)
        assert first_fill >= series["BTC-USD"][oos_start + 1].timestamp


def test_variant_matches_a_directly_constructed_run_over_the_same_span(series, config, baseline):
    """The harness must add nothing to what the strategy and engine do. Same bars, same
    stack, same fill timing, built by hand -> identical equity curve."""
    from backtest_framework.engine.allocator import ConstantSplitAllocator
    from backtest_framework.engine.backtest import run_backtest
    from backtest_framework.instruments.equity import Equity

    tier = DEFAULT_TIERS[-1]
    harness = cp.run_variant(series, baseline, tier, config)

    spans = cp.window_spans(series, config)
    oos_start, oos_end = spans[0][2], spans[-1][3]
    warm_up = baseline.lookback
    direct = run_backtest(
        bars_by_instrument={
            symbol: list(series[symbol][oos_start - warm_up : oos_end]) for symbol in config.symbols
        },
        instruments={
            symbol: Equity(symbol=symbol, quantity_precision=8) for symbol in config.symbols
        },
        strategies=[baseline.build_strategy(config)],
        cost_stack=cp.build_pair_cost_stack(
            cp.pair_cost_stack_config(tier, config.borrow_annual_rate, config.margin_annual_rate)
        ),
        allocator=ConstantSplitAllocator(),
        starting_cash=config.starting_cash,
        fill_timing=config.fill_timing,
    )
    for (ts_a, nav_a), (ts_b, nav_b) in zip(harness.oos_equity, direct.equity_curve[warm_up:]):
        assert ts_a == ts_b
        assert nav_a == pytest.approx(nav_b, rel=1e-12)


# ------------------------------------------------------------------------- stitching


def test_both_stitching_modes_cover_the_same_bars(series, config, baseline):
    """Whatever the seam does to the numbers, it must not change WHICH bars are being
    reported — otherwise the sensitivity row would be comparing two different samples
    and the measured difference would mean nothing (D123)."""
    chained = cp.PairsVariant("chained", "convention", stitch="chained")
    a = cp.run_variant(series, baseline, DEFAULT_TIERS[-1], config)
    b = cp.run_variant(series, chained, DEFAULT_TIERS[-1], config)
    assert [ts for ts, _ in a.oos_equity] == [ts for ts, _ in b.oos_equity]
    assert len(a.oos_returns) == len(b.oos_returns)
    assert a.n_oos_bars == b.n_oos_bars


def test_chained_stitching_starts_each_window_from_the_previous_windows_nav(series, config):
    """The chaining invariant (D89's, reproduced here so the sensitivity row is a fair
    representation of the pattern it is standing in for): window i's first OOS NAV is
    window i-1's last, because window i's starting cash IS that NAV and the strategy is
    flat through the prefix and cannot fill on the first test bar under next_open."""
    chained = cp.PairsVariant("chained", "convention", stitch="chained", lookback=60)
    result = cp.run_variant(series, chained, DEFAULT_TIERS[-1], config)
    navs = [nav for _, nav in result.oos_equity]
    for window in range(1, 5):
        boundary = window * config.test_size
        assert navs[boundary] == pytest.approx(navs[boundary - 1], rel=1e-12)


# ------------------------------------------------------------------------ cost tiers


def test_final_nav_is_non_increasing_in_the_fee_tier(series, config, baseline):
    """The D8 sweep gate applied to this study's tiers.

    Worth stating why this is an EMPIRICAL check here and a near-theorem in the breakout
    study: this book sizes to a target weight off current NAV (D61), so a higher fee
    lowers NAV, which shrinks the next position, which changes the subsequent P&L. On a
    losing path a dearer run could in principle end higher. It does not on this fixture,
    and a future data set where it did would produce a failing test rather than a quietly
    misleading cost table."""
    navs = [cp.run_variant(series, baseline, tier, config).final_nav for tier in DEFAULT_TIERS]
    assert [t.fee_bps for t in DEFAULT_TIERS] == sorted(t.fee_bps for t in DEFAULT_TIERS)
    for cheaper, dearer in zip(navs, navs[1:]):
        assert dearer <= cheaper + 1e-6


def test_zero_fee_tier_charges_no_fees_but_still_charges_carry(series, config, baseline):
    """The distinction the report's grid section turns on: a 0 bp tier is not a
    frictionless run. Borrow and margin interest are carry, and no fee tier turns them
    off — only the `carry_free` variant does."""
    result = cp.run_variant(series, baseline, DEFAULT_TIERS[0], config)
    costs = result.cost_totals()
    assert costs["fees"] == 0.0
    assert costs["borrow"] > 0.0
    assert costs["margin"] > 0.0

    free = cp.PairsVariant("free", "cost", borrow_annual_rate=0.0, margin_annual_rate=0.0)
    frictionless = cp.run_variant(series, free, DEFAULT_TIERS[0], config)
    assert frictionless.total_costs == 0.0
    assert frictionless.final_nav > result.final_nav


def test_the_margin_base_collapses_at_the_gross_threshold(series, config):
    """D96's mechanism, reproduced on a different instrument: at leg_weight 0.5 gross
    exposure equals NAV so max(gross − NAV, 0) collapses, and at 0.25 it is exactly
    zero. Stated as a collapse rather than "exactly zero at 0.5", because at the
    threshold itself lot rounding and NAV drift leave trace margin on scattered bars —
    the same correction the gross-exposure study had to make."""
    tier = DEFAULT_TIERS[-1]
    full = cp.run_variant(series, cp.PairsVariant("lw1", "gross", leg_weight=1.0), tier, config)
    half = cp.run_variant(series, cp.PairsVariant("lw05", "gross", leg_weight=0.5), tier, config)
    quarter = cp.run_variant(series, cp.PairsVariant("lw025", "gross", leg_weight=0.25), tier, config)
    assert quarter.cost_totals()["margin"] == 0.0
    assert half.cost_totals()["margin"] < full.cost_totals()["margin"] / 10.0
    assert full.cost_totals()["margin"] > 0.0


def test_borrow_cost_is_monotone_in_the_borrow_rate(series, config):
    tier = DEFAULT_TIERS[-1]
    charged = []
    for rate in (0.0, 0.10, 0.25):
        variant = cp.PairsVariant(f"b{rate}", "cost", borrow_annual_rate=rate)
        charged.append(cp.run_variant(series, variant, tier, config).cost_totals()["borrow"])
    assert charged[0] == 0.0
    assert charged[0] < charged[1] < charged[2]


# ------------------------------------------------------------------------- benchmarks


def test_benchmarks_cover_exactly_the_strategy_oos_span(series, config, baseline):
    tier = DEFAULT_TIERS[-1]
    strategy_result = cp.run_variant(series, baseline, tier, config)
    benchmarks = cp.run_benchmarks(series, tier, config)
    assert set(benchmarks) == {"BTC-USD", "ETH-USD", "basket_5050"}
    for benchmark in benchmarks.values():
        assert [ts for ts, _ in benchmark.oos_equity] == [
            ts for ts, _ in strategy_result.oos_equity
        ]
        assert len(benchmark.oos_returns) == len(strategy_result.oos_returns)


def test_the_single_leg_benchmarks_are_the_breakout_studys_buy_and_hold(series, config):
    """Reused, not reimplemented (D115). Asserted by calling the breakout study's own
    function directly and demanding byte equality."""
    from backtest_framework.research.breakout_study import run_benchmark

    tier = DEFAULT_TIERS[-1]
    mine = cp.run_benchmarks(series, tier, config)
    for symbol in config.symbols:
        theirs = run_benchmark(list(series[symbol]), symbol, tier, config.benchmark_config())
        assert mine[symbol].oos_equity == theirs.oos_equity


def test_realised_beta_is_near_zero_on_the_real_fixture(series, config, baseline):
    """D37's expectation for a market-neutral book, checked as a gate rather than only
    printed. The bound is deliberately loose (|β| < 0.1): this asserts "the neutrality
    claim is not falsified", not a precise value the report would have to keep in sync."""
    tier = DEFAULT_TIERS[-1]
    result = cp.run_variant(series, baseline, tier, config)
    betas = cp.realised_betas(result, cp.run_benchmarks(series, tier, config))
    assert set(betas) == {"vs_BTC-USD", "vs_ETH-USD", "vs_basket_5050"}
    for name, beta in betas.items():
        assert abs(beta) < 0.1, f"{name} beta {beta:+.4f} — market-neutral claim falsified"


# ---------------------------------------------------------- cointegration on real data


def test_the_pair_is_mostly_not_cointegrated(series, config):
    """The study's first-class finding, pinned so a data revision that changed it would
    fail loudly instead of silently rewriting the verdict. Asserted as a band, not a
    point, so the test is about the conclusion and not about the fourth decimal."""
    report = cp.cointegration_report(series, config)
    assert len(report.windows) == len(cp.window_spans(series, config))
    assert report.rate("5%") < 0.25
    assert report.rate("5%", "engle_granger") < 0.25
    assert report.beta_coherent_rate() < 0.75


# ------------------------------------------------------------- registry, DSR, rebuild


@pytest.fixture(scope="module")
def small_study(bars, config, tmp_path_factory):
    """A deliberately small study — two tiers, four variants spanning three groups — so
    the registry/DSR wiring is exercised end to end without a 40-second test."""
    registry = TrialRegistry(tmp_path_factory.mktemp("registry") / "trials.sqlite")
    variants = [
        cp.PairsVariant(cp.baseline_name(), "grid"),
        cp.PairsVariant("grid_lb20_z2", "grid", lookback=20),
        cp.PairsVariant("gross_lw0.5", "gross", leg_weight=0.5),
        cp.PairsVariant("borrow_0pct", "cost", borrow_annual_rate=0.0),
    ]
    result = cp.run_crypto_pairs_study(
        bars,
        registry,
        snapshot_id="test-snapshot",
        config=config,
        tiers=(DEFAULT_TIERS[0], DEFAULT_TIERS[-1]),
        variants=variants,
        trial_id_prefix="itest",
    )
    yield result, registry
    registry.close()


def test_every_variant_and_window_is_logged_once(small_study):
    result, registry = small_study
    n_variants, n_tiers = len(result.variants), len(result.tiers)
    assert len(registry) == n_variants * n_tiers * (1 + result.n_windows)
    kinds = [t.config["row_kind"] for t in registry.all_trials()]
    assert kinds.count("variant") == n_variants * n_tiers
    assert kinds.count("window") == n_variants * n_tiers * result.n_windows


def test_trial_ids_and_hashes_distinguish_every_configuration(small_study):
    _result, registry = small_study
    trials = registry.all_trials()
    assert len({t.trial_id for t in trials}) == len(trials)
    variant_rows = [t for t in trials if t.config["row_kind"] == "variant"]
    assert len({t.trial_hash for t in variant_rows}) == len(variant_rows)
    for trial in trials:
        assert trial.trial_hash == compute_trial_hash(trial.config, trial.snapshot_id, trial.seed)
        assert trial.snapshot_id == "test-snapshot"


def test_the_logged_cost_stack_is_the_one_that_was_built(small_study):
    """D102's rule: what the registry hashes is what ran. Rebuild the stack from the
    logged dict and demand the bricks match the tier and the resolved carry rates."""
    result, registry = small_study
    for trial in registry.all_trials():
        if trial.config["row_kind"] != "variant":
            continue
        stack = cp.build_pair_cost_stack(trial.config["cost_stack"])
        assert stack.trade_bricks[0].bps == trial.config["fee_bps"]
        assert stack.carry_bricks[0].annual_rate == trial.config["borrow_annual_rate"]
        assert stack.portfolio_carry_bricks[0].annual_rate == trial.config["margin_annual_rate"]


def test_the_logged_config_rebuilds_and_re_runs_what_ran(small_study, series):
    """The full reproducibility loop (D35/D102): config -> registry -> reload -> rebuild
    -> re-run reproduces the logged final NAV exactly. Run on one row per group so every
    kind of override is exercised, without re-running the whole study."""
    from backtest_framework.research.breakout_study import CostTier

    result, registry = small_study
    seen_groups = set()
    for trial in registry.all_trials():
        if trial.config["row_kind"] != "variant" or trial.config["group"] in seen_groups:
            continue
        seen_groups.add(trial.config["group"])
        rebuilt_config = cp.CryptoPairsConfig.from_dict(trial.config)
        rebuilt_variant = cp.PairsVariant.from_config(trial.config)
        tier = CostTier(
            trial.config["tier"], trial.config["fee_bps"], trial.config["venue_role"]
        )
        rerun = cp.run_variant(series, rebuilt_variant, tier, rebuilt_config)
        assert rerun.final_nav == pytest.approx(trial.metrics["final_nav"], rel=1e-12)
        assert rerun.total_return == pytest.approx(trial.metrics["total_return"], rel=1e-12)
    assert seen_groups == {"grid", "gross", "cost"}


def test_the_dsr_pool_is_the_configuration_rows_only(small_study):
    """D116's pool, D98's selection rule. The `cost` group variant is a re-pricing of the
    same configuration, so it must NOT be in the pool — and the pool must be selected by
    identity fields, never by which rows happen to carry the metric."""
    result, registry = small_study
    expected = sum(1 for v in result.variants if v.group in cp.DSR_POOL_GROUPS)
    for tier in result.tiers:
        inputs = result.dsr_inputs_by_tier[tier.name]
        assert inputs["n_trials"] == expected
        assert inputs["t"] == result.n_oos_bars - 1
        assert 0.0 <= result.dsr_by_tier[tier.name] <= 1.0
        assert not math.isnan(inputs["var_trials_daily"])

    pooled = [
        t
        for t in registry.all_trials()
        if t.config["row_kind"] == "variant"
        and t.config["group"] in cp.DSR_POOL_GROUPS
        and t.config["tier"] == result.tiers[0].name
    ]
    assert {t.config["variant"] for t in pooled} == {
        v.name for v in result.variants if v.group in cp.DSR_POOL_GROUPS
    }


def test_logged_window_sharpe_is_in_daily_units(small_study):
    """D98's units contract, the audit's one red finding, re-pinned for this study: the
    metric fed to the DSR pool and the observed SR must be in the same per-period units.
    A √365 discrepancy here would force every DSR toward 0 regardless of the strategy."""
    result, _registry = small_study
    variant = result.variants[0]
    r = result.results[(variant.name, result.tiers[-1].name)]
    annual = r.sharpe_annual(r.resolved)
    assert r.sharpe_daily(r.resolved) == pytest.approx(
        annual / math.sqrt(result.config.periods_per_year), rel=1e-12
    )
    for window_sharpe in r.window_sharpes_daily.values():
        assert abs(window_sharpe) < 1.0, "a per-period Sharpe this large is annualised units"


def test_the_study_span_is_reported_consistently(small_study, series, config):
    result, _registry = small_study
    spans = cp.window_spans(series, config)
    assert result.n_windows == len(spans)
    assert result.n_oos_bars == spans[-1][3] - spans[0][2]
    assert result.oos_start == series["BTC-USD"][spans[0][2]].timestamp
    assert result.oos_end == series["BTC-USD"][spans[-1][3] - 1].timestamp
    assert len(result.window_test_spans) == len(spans)
    assert result.window_test_spans[0][1] == result.oos_start
    assert result.window_test_spans[-1][2] == result.oos_end
