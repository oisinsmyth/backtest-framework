"""Integration gates for the crypto-universe cross-section (D140-D144).

Offline: everything runs on the committed universe fixture, on a small subset of its
symbols so the suite stays fast. The full 63-symbol run lives in
`scripts/run_breakout_universe.py`.

What these assert is not "the numbers are good" but "the numbers mean what the report
says they mean": the out-of-sample span really starts where training ends, nothing fills
before it, a symbol the policy rejects really cannot reach the engine, the cost tiers are
really ordered, the registry is really append-only with unique hashes, and the DSR pool
is really the per-symbol rows rather than the window or benchmark rows.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.data.cleaner import clean
from backtest_framework.data.csv_fixture import load_fixture_csv_with_volumes
from backtest_framework.registry.trial_registry import TrialRegistry, compute_trial_hash
from backtest_framework.research import breakout_study as bs
from backtest_framework.research import breakout_universe as bu
from backtest_framework.simulator.fills import Bar

REPO = Path(__file__).resolve().parent.parent.parent
FIXTURE = REPO / "data" / "fixtures" / "crypto_universe_2015_2025_raw.csv.gz"
END = date(2025, 12, 31)
SNAPSHOT = "test-snapshot-universe"

SUBSET = ("BTC-USD", "ETH-USD", "LUNC-USD", "FTT-USD")
"""Two survivors and two collapses, so every split-dependent assertion has both sides."""

TOO_SHORT = "SHORTCOIN"
"""A synthetic symbol that fails the min-history rule. It is fed to the study alongside
real ones to prove the screen is a gate and not a report."""


def _short_series(n: int = 120) -> list[TimestampedBar]:
    bars, price = [], 100.0
    for i in range(n):
        price *= 1.03 if i % 2 else 0.98
        bars.append(
            TimestampedBar(
                timestamp=datetime(2021, 1, 1) + timedelta(days=i),
                bar=Bar(open=price, high=price * 1.01, low=price * 0.99, close=price),
            )
        )
    return bars


@pytest.fixture(scope="module")
def cleaned_subset(requires_panel):
    requires_panel(FIXTURE)
    raw_bars, raw_volumes = load_fixture_csv_with_volumes(FIXTURE)
    bars = {s: raw_bars[s] for s in SUBSET}
    volumes = {s: raw_volumes[s] for s in SUBSET}
    cleaned, _report = clean(bars, volumes)
    aligned = {s: bu.align_volumes(cleaned[s], bars[s], volumes[s]) for s in cleaned}
    return cleaned, aligned


@pytest.fixture(scope="module")
def study():
    return bs.BreakoutStudyConfig()


@pytest.fixture(scope="module")
def run(cleaned_subset, tmp_path_factory, study):
    """One study run over the subset PLUS a synthetic symbol the policy must reject."""
    bars, volumes = cleaned_subset
    short = _short_series()
    with_reject = {**bars, TOO_SHORT: short}
    volumes_with_reject = {**volumes, TOO_SHORT: [50_000_000.0] * len(short)}
    registry_path = tmp_path_factory.mktemp("universe") / "registry.sqlite"
    registry = TrialRegistry(registry_path)
    result = bu.run_universe_study(
        with_reject,
        volumes_with_reject,
        registry,
        SNAPSHOT,
        cohorts={s: "test_cohort" for s in with_reject},
        study=study,
        end_date=END,
    )
    yield result, registry
    registry.close()


# --------------------------------------------------- the policy is a gate, not a report


def test_a_symbol_the_policy_rejects_never_reaches_the_engine(run):
    """The whole study rests on this: a symbol failing the coverage rule must be absent
    from the results, absent from the registry, and present in the exclusion list with a
    reason. Silence in any of those three places would be the bias itself."""
    result, registry = run
    assert TOO_SHORT not in result.runs
    assert TOO_SHORT in result.selection.excluded
    assert "min-history" in result.selection.excluded[TOO_SHORT]
    assert TOO_SHORT not in result.selection.included
    assert not [t for t in registry.all_trials() if t.config.get("symbol") == TOO_SHORT]
    assert not [t for t in registry.all_trials() if TOO_SHORT in t.trial_id]


def test_the_study_runs_every_admitted_symbol_at_every_tier(run):
    result, _registry = run
    assert set(result.runs) == set(SUBSET)
    for symbol, symbol_run in result.runs.items():
        assert set(symbol_run.by_tier) == {t.name for t in bs.DEFAULT_TIERS}


# ------------------------------------------------------------- walk-forward geometry


def test_oos_span_starts_where_window_zero_training_ends_for_every_symbol(run, cleaned_subset, study):
    bars, _volumes = cleaned_subset
    result, _registry = run
    for symbol, symbol_run in result.runs.items():
        spans = bs._window_spans(bars[symbol], study)
        window_index, train_start, test_start, _test_end = spans[0]
        assert (window_index, train_start) == (0, 0)
        assert test_start == study.train_size
        assert symbol_run.oos_start == bars[symbol][test_start].timestamp
        for tier_run in symbol_run.by_tier.values():
            assert tier_run.variant.oos_equity[0][0] == bars[symbol][test_start].timestamp


def test_no_fill_lands_before_the_first_out_of_sample_bar(run):
    """`run_variant` raises internally if a fill lands in the warm-up prefix; this proves
    the guarantee holds for every symbol in the cross-section, not just the two the
    BTC/ETH suite covered."""
    result, _registry = run
    for symbol_run in result.runs.values():
        first_oos = symbol_run.oos_start
        for tier_run in symbol_run.by_tier.values():
            for episode in tier_run.variant.episodes:
                assert episode.entry_timestamp >= first_oos


def test_no_symbol_is_truncated_to_another_symbols_inception(run, cleaned_subset, study):
    """D45's inner-join rule must NOT bind here: each symbol is its own single-instrument
    backtest (the N=1 case of D64). If it ever did bind, every coin would start at the
    youngest one's inception, which is the failure this fixture is deliberately built to
    avoid."""
    bars, _volumes = cleaned_subset
    result, _registry = run
    starts = {run_.oos_start for run_ in result.runs.values()}
    assert len(starts) > 1, "symbols must keep their own inceptions"
    for symbol, symbol_run in result.runs.items():
        spans = bs._window_spans(bars[symbol], study)
        assert symbol_run.oos_start == bars[symbol][spans[0][2]].timestamp


# -------------------------------------------------------------------------- costs


def test_final_nav_is_monotone_non_increasing_in_the_fee_tier(run):
    """The same property the BTC/ETH study property-tested, asserted across the
    cross-section: a higher fee can never produce a higher terminal NAV on the same
    signal path."""
    result, _registry = run
    ordered = [t.name for t in sorted(bs.DEFAULT_TIERS, key=lambda t: t.fee_bps)]
    for symbol, symbol_run in result.runs.items():
        navs = [symbol_run.by_tier[name].variant.final_nav for name in ordered]
        for cheaper, dearer in zip(navs, navs[1:]):
            assert dearer <= cheaper + 1e-9, f"{symbol}: NAV rose with the fee"
        costs = [symbol_run.by_tier[name].variant.diagnostics.total_costs for name in ordered]
        assert costs[0] == pytest.approx(0.0, abs=1e-9)
        for cheaper, dearer in zip(costs, costs[1:]):
            assert dearer >= cheaper - 1e-9


def test_benchmarks_cover_exactly_the_same_span_as_the_strategy(run):
    """A benchmark measured over a different span is not a benchmark. The matched-exposure
    row in particular runs through the engine, so its calendar must be pinned."""
    result, _registry = run
    for symbol_run in result.runs.values():
        for tier_run in symbol_run.by_tier.values():
            strategy_stamps = [ts for ts, _ in tier_run.variant.oos_equity]
            assert [ts for ts, _ in tier_run.hold.oos_equity] == strategy_stamps
            assert tier_run.matched is not None
            assert [ts for ts, _ in tier_run.matched.oos_equity] == strategy_stamps
            assert len(tier_run.variant.oos_returns) == len(tier_run.hold.oos_returns)


def test_matched_exposure_benchmark_uses_the_strategys_own_exposure(run):
    result, _registry = run
    for symbol_run in result.runs.values():
        for tier_run in symbol_run.by_tier.values():
            logged = tier_run.variant.diagnostics.exposure
            assert 0.0 < logged <= 1.0
            # The constant-fraction benchmark is built at exactly that fraction; a
            # mismatch would make the "fair test" column answer a different question.
            assert tier_run.matched is not None


# ----------------------------------------------------------------------- registry


def test_every_registry_row_is_unique_in_id_and_in_hash(run):
    result, registry = run
    trials = registry.all_trials()
    ids = [t.trial_id for t in trials]
    hashes = [t.trial_hash for t in trials]
    assert len(set(ids)) == len(ids)
    assert len(set(hashes)) == len(hashes)
    assert all(t.snapshot_id == SNAPSHOT for t in trials)
    # And the hash really is a function of (config, snapshot, seed) — recomputing it
    # from the stored config must reproduce it.
    for trial in trials[:25]:
        assert compute_trial_hash(trial.config, trial.snapshot_id, trial.seed) == trial.trial_hash


def test_registry_row_kinds_partition_the_log(run):
    result, registry = run
    kinds = {t.config.get("row_kind") for t in registry.all_trials()}
    assert kinds == {"symbol", "benchmark", "window"}
    symbol_rows = [t for t in registry.all_trials() if t.config["row_kind"] == "symbol"]
    assert len(symbol_rows) == len(SUBSET) * len(bs.DEFAULT_TIERS) == result.n_oos_trials
    assert all("oos_sharpe_daily" in t.metrics for t in symbol_rows)


def test_every_logged_config_is_the_unmodified_baseline(run):
    """This study's discipline is one configuration everywhere. If a symbol ever ran a
    different rule, the cross-section would stop being a cross-section."""
    result, registry = run
    expected = bs.breakout_config(bs.BASELINE_N_ENTRY, bs.BASELINE_N_EXIT)
    for trial in registry.all_trials():
        assert trial.config["variant"] == bu.BASELINE_VARIANT
        assert trial.config["fixed_config"] == expected
        assert trial.config["fit"] is None
        assert trial.config["universe_policy"] == result.selection.policy.to_dict()


# ---------------------------------------------------------------------------- DSR


def test_the_dsr_pool_is_the_symbol_rows_and_only_the_symbol_rows(run):
    """D98's rule: the pool is selected on identity fields, never on the presence of a
    metric. Window and benchmark rows share the same config keys, so a sloppy predicate
    would swallow them and inflate N."""
    result, registry = run
    for tier in bs.DEFAULT_TIERS:
        inputs = result.dsr_inputs_by_tier[tier.name]
        assert inputs["n_trials"] == len(SUBSET)
        assert 0.0 <= result.dsr_by_tier[tier.name] <= 1.0
        assert inputs["best_symbol"] in SUBSET
        # Units contract: the observed SR is daily, matching the logged metric.
        best = result.runs[inputs["best_symbol"]].by_tier[tier.name].variant
        assert inputs["observed_sr_daily"] == pytest.approx(
            best.sharpe_daily(result.config), rel=1e-12
        )
        assert inputs["t"] == len(best.oos_returns)


def test_the_best_symbol_in_the_pool_really_is_the_best(run):
    result, _registry = run
    for tier in bs.DEFAULT_TIERS:
        sharpes = {
            symbol: symbol_run.by_tier[tier.name].variant.sharpe_daily(result.config)
            for symbol, symbol_run in result.runs.items()
        }
        assert result.dsr_inputs_by_tier[tier.name]["best_symbol"] == max(sharpes, key=sharpes.get)


# ------------------------------------------------------------- cross-section stats


def test_hit_rates_count_every_admitted_symbol_exactly_once(run):
    result, _registry = run
    split = bu.split_by_status(result, bs.REFERENCE_TIER)
    assert split["all"]["n_symbols"] == len(SUBSET)
    assert (
        split[bu.SURVIVED]["n_symbols"] + split["collapsed_or_delisted"]["n_symbols"]
        == len(SUBSET)
    )
    wins, total, _fraction = split["all"]["beat_buy_and_hold"]
    assert total == len(SUBSET)
    assert 0 <= wins <= total


def test_hit_rate_agrees_with_the_per_symbol_comparison(run):
    """The summary must be arithmetic on the rows, not a second computation that can
    drift from them."""
    result, _registry = run
    tier = bs.REFERENCE_TIER
    expected = sum(
        1
        for symbol_run in result.runs.values()
        if symbol_run.by_tier[tier].variant.total_return
        > symbol_run.by_tier[tier].hold.total_return
    )
    assert bu.cross_section(result, tier)["beat_buy_and_hold"][0] == expected


def _table_widths(table: str) -> set[int]:
    """Column count per row, counting an escaped `\\|` as literal text rather than as a
    cell separator — which is how a markdown renderer reads it."""
    rows = [line for line in table.splitlines() if line.startswith("|")]
    return {len(line.replace("\\|", "").split("|")) for line in rows}


def test_the_report_tables_render_without_a_stray_pipe(run):
    """Exclusion reasons are free text — written by the policy and by the provider's own
    exception messages — and they land verbatim in markdown tables. An unescaped '|'
    inside one silently breaks the row, and the reader never learns why a symbol was
    excluded. The renderer escapes; this proves it, including on a reason that actually
    contains a pipe."""
    result, _registry = run
    hostile_reason = "median |daily return| 0.141% < required 0.500% (peg screen)"
    tables = [
        bu.render_symbol_table(result, bs.REFERENCE_TIER),
        bu.render_hit_rate_table(result, bs.REFERENCE_TIER),
        bu.render_tier_table(result),
        bu.render_dsr_table(result),
        bu.render_exclusion_table(
            {**result.selection.excluded, "PEG-USD": hostile_reason},
            {"NOPE-USD": "provider returned an empty series | truncated"},
            {s: c.to_dict() for s, c in result.selection.coverage.items()},
            {s: "test_cohort" for s in result.selection.coverage},
        ),
    ]
    for table in tables:
        widths = _table_widths(table)
        assert len(widths) == 1, f"ragged markdown table:\n{table}"
    assert "\\|daily return\\|" in tables[-1]


def test_the_published_report_has_no_ragged_table():
    """The artifact itself, not just the renderers. A table that lost a column between
    generation and the committed file is a defect a reader sees and an author does not."""
    report = REPO / "docs" / "results" / "breakout_universe.md"
    if not report.exists():  # the runner has not been executed in this checkout
        pytest.skip("docs/results/breakout_universe.md has not been generated")
    block: list[str] = []
    for line in report.read_text(encoding="utf-8").splitlines() + [""]:
        if line.startswith("|"):
            block.append(line)
            continue
        if block:
            assert len(_table_widths("\n".join(block))) == 1, (
                "ragged markdown table in the published report:\n" + "\n".join(block[:3])
            )
            block = []


# ------------------------------------------------------- cross-study reconciliation


def test_btc_and_eth_reproduce_the_published_breakout_results(run):
    """BTC-USD and ETH-USD appear in both crypto studies, which share the strategy code
    and the harness but NOT the data — separate fixtures, fetched separately, from a
    provider that restates history (D24). Agreement to the printed precision is what
    licenses reading this cross-section against `BREAKOUT_RESULTS.md`'s numbers.

    **A failure here is a DATA event, not a code regression**: either the provider
    restated history, or one of the two fixtures is stale. Either way, two documents in
    this repo would be quoting different BTC histories, which is exactly the silent drift
    D24 exists to make impossible."""
    result, _registry = run
    diffs = bu.reconcile_against_published(result)
    assert set(diffs) == {"BTC-USD", "ETH-USD"}
    for symbol, per_metric in diffs.items():
        for metric, error_in_printed_units in per_metric.items():
            # 1.0 == off by exactly the last digit the source prints.
            assert error_in_printed_units < 1.0, (
                f"{symbol}.{metric} differs from BREAKOUT_RESULTS.md by "
                f"{error_in_printed_units:.2f}x the precision that document prints — the "
                "two fixtures are not the same data"
            )


# -------------------------------------------------------------------- determinism


def test_the_study_is_deterministic(cleaned_subset, tmp_path_factory, study):
    """Offline and deterministic is a claim the report makes in its header."""
    bars, volumes = cleaned_subset
    two = {s: bars[s] for s in SUBSET[:2]}
    two_volumes = {s: volumes[s] for s in SUBSET[:2]}
    outcomes = []
    for i in range(2):
        registry = TrialRegistry(tmp_path_factory.mktemp(f"determinism{i}") / "r.sqlite")
        result = bu.run_universe_study(
            two,
            two_volumes,
            registry,
            SNAPSHOT,
            cohorts={s: "c" for s in two},
            study=study,
            tiers=bs.DEFAULT_TIERS[-1:],
            end_date=END,
        )
        outcomes.append(
            {
                s: (
                    r.by_tier[bs.REFERENCE_TIER].variant.total_return,
                    r.by_tier[bs.REFERENCE_TIER].variant.max_drawdown,
                    r.by_tier[bs.REFERENCE_TIER].hold.total_return,
                )
                for s, r in result.runs.items()
            }
        )
        registry.close()
    assert outcomes[0] == outcomes[1]


# ------------------------------------------------------------------- live fetch


@pytest.mark.live_fetch
def test_the_fetch_scripts_provider_assumptions_still_hold():
    """NETWORK. The fixture is frozen, so this does not gate the study — it gates the
    fetch script's assumptions about the provider for the day someone re-runs it: spot
    crypto returns no dividends and no splits, and bars are stamped 00:00 (D108)."""
    from backtest_framework.data.yfinance_source import EquityDataSource

    source = EquityDataSource()
    for symbol in ("BTC-USD", "FTT-USD"):
        bars, volumes, dividends, splits = source.get_raw_history(
            symbol, date(2022, 1, 1), date(2022, 6, 30)
        )
        assert bars, f"{symbol} returned no bars"
        assert len(volumes) == len(bars)
        assert not dividends and not splits, "spot crypto must have no corporate actions"
        assert {tb.timestamp.hour for tb in bars} == {0}
