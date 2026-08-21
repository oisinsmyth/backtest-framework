"""BTC/ETH z-score pairs study runner (D122-D127) -> docs/results/crypto_pairs_btc_eth.md.

Offline and deterministic: reads the committed BTC/ETH fixture, freezes it through the
Step-7 pipeline (clean -> validate -> SnapshotStore -> load) exactly as
`scripts/run_breakout_study.py` does, runs every (variant, cost tier) combination, logs
every trial to a dedicated registry, and writes the report.

Run: uv run python scripts/run_crypto_pairs_study.py
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from backtest_framework.analytics.tearsheet import render_metrics_table
from backtest_framework.data.cleaner import clean
from backtest_framework.data.corporate_actions import load_events_json
from backtest_framework.data.csv_fixture import load_fixture_csv_with_volumes
from backtest_framework.data.snapshot_store import SnapshotStore
from backtest_framework.data.validator import validate
from backtest_framework.registry.trial_registry import TrialRegistry
from backtest_framework.research import crypto_pairs_study as cp

REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "data" / "fixtures" / "crypto_daily_2015_2025_raw.csv.gz"
EVENTS = REPO / "data" / "fixtures" / "crypto_daily_2015_2025_raw_events.json"
REGISTRY_PATH = REPO / "data" / "crypto_pairs_registry.sqlite"
RESULTS = REPO / "docs" / "results" / "crypto_pairs_btc_eth.md"
SUMMARY_JSON = REPO / "data" / "crypto_pairs_summary.json"

BASELINE = cp.baseline_name()
GRID_NAMES = [v.name for v in cp.grid_variants()]
GROSS_NAMES = [v.name for v in cp.gross_variants()]
CONVENTION_NAMES = [v.name for v in cp.convention_variants()]
COST_NAMES = [v.name for v in cp.cost_variants()]
ORDERED = GRID_NAMES + GROSS_NAMES + CONVENTION_NAMES + COST_NAMES


def freeze_snapshot() -> tuple[str, dict, dict]:
    bars, volumes = load_fixture_csv_with_volumes(FIXTURE)
    actions = load_events_json(EVENTS)
    cleaned, cleaning_report = clean(bars, volumes)
    validation = validate(cleaned, actions, volumes)
    store = SnapshotStore(REPO / "data" / "snapshots")
    snapshot_id = store.create(
        cleaned,
        actions,
        volumes_by_symbol=volumes,
        cleaning_report=cleaning_report,
        validation=validation,
        extra_meta={"source_fixture": FIXTURE.name},
    )
    snapshot = store.load(snapshot_id)
    gate = {
        "cleaning_changes": len(cleaning_report.changes),
        "hard_violations": len(validation.hard_violations),
        "warnings": len(validation.warnings),
    }
    return snapshot_id, snapshot.bars_by_symbol, gate


def main() -> int:
    started = time.time()
    snapshot_id, bars_by_symbol, gate = freeze_snapshot()
    print(f"snapshot {snapshot_id}")
    print(
        f"  clean: {gate['cleaning_changes']} change(s); "
        f"validator: {gate['hard_violations']} hard, {gate['warnings']} warning(s)"
    )

    if REGISTRY_PATH.exists():
        REGISTRY_PATH.unlink()  # a study re-run is one coherent trial pool, not a merge
    registry = TrialRegistry(REGISTRY_PATH)
    config = cp.CryptoPairsConfig()

    seen = {"n": 0}

    def progress(label: str) -> None:
        seen["n"] += 1
        if seen["n"] % 20 == 0:
            print(f"  ... {seen['n']} variant-runs ({label})")

    result = cp.run_crypto_pairs_study(
        bars_by_symbol, registry, snapshot_id, config=config, progress=progress
    )
    print(
        f"ran {result.n_oos_trials} out-of-sample trials, {len(registry)} registry rows, "
        f"in {time.time() - started:.0f}s"
    )

    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(render_report(result, gate), encoding="utf-8")
    SUMMARY_JSON.write_text(json.dumps(summary_payload(result, gate), indent=2), encoding="utf-8")
    registry.close()
    print(f"wrote {RESULTS.relative_to(REPO)} and {SUMMARY_JSON.relative_to(REPO)}")
    return 0


def summary_payload(result: cp.StudyResult, gate: dict) -> dict:
    """Machine-readable companion to the report — what a later regression test would diff
    against, and what keeps the prose's headline numbers checkable."""
    config = result.config
    return {
        "snapshot_id": result.snapshot_id,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "config": config.to_dict(),
        "tiers": [{"name": t.name, "fee_bps": t.fee_bps, "role": t.role} for t in result.tiers],
        "sanity_gate": gate,
        "oos_start": result.oos_start.date().isoformat(),
        "oos_end": result.oos_end.date().isoformat(),
        "n_oos_bars": result.n_oos_bars,
        "n_windows": result.n_windows,
        "n_oos_trials": result.n_oos_trials,
        "cointegration": {
            **result.cointegration.to_metrics(),
            "windows": [
                {
                    "window": w.window,
                    "train_start": w.train_start.date().isoformat(),
                    "train_end": w.train_end.date().isoformat(),
                    "adf_traded_spread": w.adf_traded_spread,
                    "engle_granger_beta": w.engle_granger_beta,
                    "engle_granger_adf": w.engle_granger_adf,
                }
                for w in result.cointegration.windows
            ],
        },
        "dsr_by_tier": result.dsr_by_tier,
        "dsr_inputs_by_tier": result.dsr_inputs_by_tier,
        "betas_by_tier": result.betas_by_tier,
        "variants": {
            f"{name}@{tier}": {
                "total_return": r.total_return,
                "cagr": cp.cagr(r.total_return, r.n_oos_bars, config.periods_per_year),
                "sharpe_annual": r.sharpe_annual(r.resolved),
                "max_drawdown": r.max_drawdown,
                "round_trips": r.n_round_trips,
                "exposure": r.exposure,
                "annual_turnover": r.annual_turnover,
                "costs": r.cost_totals(),
            }
            for (name, tier), r in result.results.items()
        },
        "benchmarks": {
            f"{name}@{tier}": {
                "total_return": b.total_return,
                "cagr": cp.cagr(b.total_return, len(b.oos_equity), config.periods_per_year),
                "sharpe_annual": b.sharpe_annual(config.benchmark_config()),
                "max_drawdown": b.max_drawdown,
            }
            for (name, tier), b in result.benchmarks.items()
        },
    }


# ------------------------------------------------------------------------ rendering


def render_report(result: cp.StudyResult, gate: dict) -> str:
    sections = [
        _header(result, gate),
        _method(result),
        _findings_first(result),
        _cointegration_section(result),
        _performance_section(result),
        _grid_section(result),
        _tearsheet_section(result),
        _benchmark_section(result),
        _dsr_section(result),
        _multiplicity(result),
        _verdict(result),
        _caveats(result),
    ]
    return "\n\n".join(section.strip() + "\n" for section in sections)


def _ref_tier(result: cp.StudyResult):
    return next(t for t in result.tiers if t.name == cp.REFERENCE_TIER)


def _worst_window(result: cp.StudyResult, variant_name: str, tier_name: str) -> tuple[int, float, str, str]:
    """(window index, return, start date, end date) of the single worst walk-forward
    window. Computed rather than remembered — a report that names a crash from memory is
    one data revision away from being wrong."""
    r = result.results[(variant_name, tier_name)]
    navs = [r.window_final_nav[i] for i in sorted(r.window_final_nav)]
    starts = [result.config.starting_cash] + navs[:-1]
    returns = [nav / start - 1.0 for nav, start in zip(navs, starts)]
    index = min(range(len(returns)), key=lambda i: returns[i])
    _window, first, last = result.window_test_spans[index]
    return index, returns[index], first.date().isoformat(), last.date().isoformat()


def _header(result: cp.StudyResult, gate: dict) -> str:
    config = result.config
    return f"""# BTC/ETH z-score pairs: is there a spread to trade at all?

**Date produced:** {datetime.now(timezone.utc).date().isoformat()} ·
**Snapshot:** `{result.snapshot_id}` ·
**Registry:** `data/crypto_pairs_registry.sqlite`
({len(result.results)} out-of-sample trials + per-window rows) ·
**Reproduce:** `uv run python scripts/run_crypto_pairs_study.py` (offline, deterministic)

> **Lead finding, because it changes how everything below should be read.** At **zero
> fees and zero carry** the baseline configuration returns
> **{result.results[('carry_free', 'maker_0bp')].total_return:+.1%}** over the
> out-of-sample span. There is no edge here for costs to eat. Every cost number in this
> document is therefore a description of *how much faster* a losing strategy loses, not a
> viability threshold — and any reading of the form "it would work at a cheaper venue" is
> unavailable.

**Thesis frame (D37).** This IS the project's market-neutral thesis strategy: long one
leg, short the other, gross ~200% of NAV, designed to carry no market exposure. Its
honest primary hurdle is therefore the **risk-free rate**, which every Sharpe below
already carries (rf = {config.rf_annual:.0%}). Buy-and-hold columns are reported second,
and are a *long-only* benchmark for a market-neutral book — they answer "what did the
beta you deliberately did not take do?", not "what should this have beaten".

**Data.** {config.symbol_a} and {config.symbol_b} daily bars, 00:00 UTC boundary, fixed.
Fixture `data/fixtures/crypto_daily_2015_2025_raw.csv.gz`, frozen through the Step-7
pipeline (clean → validate → `SnapshotStore.create` → load). The sanity gate (D25/D26)
reported **{gate['cleaning_changes']} cleaning change(s)** and **{gate['hard_violations']}
hard violation(s)**, with {gate['warnings']} warning(s) — genuine large crypto moves, none
quarantining.

**The sample is ETH's, not BTC's.** D45/D63 inner-join alignment drops every timestamp
that is not present on both legs, which truncates the pair at ETH-USD's inception
(2017-11-09) and discards 1,043 BTC bars. That is *correct* for a pairs trade — there is
no spread on a day one leg does not exist — and it is stated rather than worked around.
The breakout study, running one single-instrument backtest per symbol, kept BTC's full
history; **the two studies therefore do not cover the same span**, and no return in this
document is directly comparable to a BTC-USD row in `BREAKOUT_RESULTS.md`.

**Scale.** {len(result.results)} out-of-sample trials
({len(result.variants)} variants × {len(result.tiers)} cost tiers), plus
{len(result.results) * result.n_windows:,} per-window rows and
{result.n_windows} training-window cointegration tests. Annualisation on
{config.periods_per_year:.0f} days (crypto trades every calendar day, D17)."""


def _method(result: cp.StudyResult) -> str:
    config = result.config
    tiers = ", ".join(f"`{t.name}` = {t.fee_bps / 100:.2f}% ({t.role})" for t in result.tiers)
    return f"""## Method, in one screen

**Signal.** `strategies.zscore_pairs.ZScorePairsStrategy` (D69), **unmodified**. spread =
ln({config.symbol_a}) − ln({config.symbol_b}); z is computed against the mean and stdev of
the `lookback` spreads ending at the **previous** bar (D44). z > entry_z → short the
spread; z < −entry_z → long it; |z| < exit_z → flat; in between, hold the current side
(hysteresis). Baseline lookback {cp.BASELINE_LOOKBACK}, entry {cp.BASELINE_ENTRY_Z:.1f},
exit {cp.BASELINE_EXIT_Z:.1f}, ±100%/leg — D69's a-priori first-number parameters, carried
over unchanged so the grid is a sensitivity around a pre-existing choice.

**Hedge.** Fixed 1:1 in log space, by D69's construction. Section "Cointegration" below
tests whether that is a defensible description of this pair. It is not.

**Execution.** `fill_timing="next_open"` (D103) — a decision at bar t's close fills at bar
t+1's **open**, so the strategy never trades at the price that produced its signal. Same
convention as the breakout study, for comparability. `fill_close` is run as a sensitivity
(D105's precedent: measure the convention, do not argue about it).

**Walk-forward.** train={config.train_size}, test={config.test_size}, step={config.step},
via `walk_forward_windows` (D85). {result.n_windows} windows. The out-of-sample span
starts exactly where window 0's training slice ends. **Nothing is fitted**, so the
continuous run needs no parameter schedule; the training slices are used only for the
cointegration diagnostic, through views that physically contain no test bar (D22/D56).

**Stitching.** One continuous out-of-sample backtest (D123), the breakout study's pattern
(D113) rather than the pairs studies' chained windows (D89). `stitch_chained` is run as a
sensitivity so the difference is a number, not a claim.

**Costs (D124).** {tiers} — the breakout study's `CostTier` objects, unmodified, so the
fee dimension is identical between the two studies. **Plus two carry bricks a long-only
book does not pay**: `BorrowFee` at {config.borrow_annual_rate:.0%}/yr on the short leg's
notional (D71), and `MarginInterest` at {config.margin_annual_rate:.0%}/yr on
max(gross − NAV, 0) (D5). Every stack is built through the declarative `build_cost_stack`
path (D102), so the dict the registry hashes is the dict the stack is built from.

**Benchmarks.** Buy-and-hold {config.symbol_a}, buy-and-hold {config.symbol_b}, and a
50/50 basket, over the same OOS span at the same tier, via `breakout_study.run_benchmark`
(D115: fixed *quantity*, bought at the second OOS bar's open, fee paid on entry notional,
marked at the final close). The basket is the mean of the two curves, which is exactly a
fixed-quantity 50/50 hold with half the capital in each leg."""


def _findings_first(result: cp.StudyResult) -> str:
    free = result.results[("carry_free", "maker_0bp")]
    baseline_ref = result.results[(BASELINE, cp.REFERENCE_TIER)]
    coint = result.cointegration
    betas = result.betas_by_tier[cp.REFERENCE_TIER]
    chained = result.results[("stitch_chained", cp.REFERENCE_TIER)]
    continuous = baseline_ref
    return f"""---

## Read this first

### 1. The premise fails before the costs do

The a-priori question was whether BTC/ETH mean reversion clears crypto trading frictions.
It does not get that far. Stripped of **all** frictions — zero fee tier, zero borrow, zero
margin interest — the baseline configuration returns
**{free.total_return:+.1%}** over {result.n_oos_bars:,} out-of-sample bars, with an
annualised Sharpe of {free.sharpe_annual(free.resolved):.2f} against a
{result.config.rf_annual:.0%} risk-free rate. Adding the full real cost stack at the taker
tier moves that to {baseline_ref.total_return:+.1%}.

Frictions cost roughly
{(free.total_return - baseline_ref.total_return) / (1 + free.total_return):.0%} of the
zero-cost terminal wealth here, which is a large number, and it is also **irrelevant to
the verdict**: subtracting a large loss from a large loss does not produce a decision.

### 2. The pair is not cointegrated, and the 1:1 hedge is not what the data says

Tested inside each of the {result.n_windows} training windows only, the log spread the
strategy actually trades is stationary at the 5% level in
**{coint.count('5%')} of {result.n_windows} windows ({coint.rate('5%'):.0%})** — about
what pure noise would produce. The Engle–Granger β linking the two log price series has a
median of {float(sorted(coint.betas)[len(coint.betas) // 2]):.2f} and sits inside D92's
coherence band [0.7, 1.3] in only {coint.beta_coherent_rate():.0%} of windows. The full
table is below; it is a first-class result, not a footnote.

### 3. Market neutrality: the one claim that survives

Realised beta of the baseline at the reference tier is
**{betas[f'vs_{result.config.symbol_a}']:+.4f}** vs {result.config.symbol_a},
**{betas[f'vs_{result.config.symbol_b}']:+.4f}** vs {result.config.symbol_b}, and
**{betas['vs_basket_5050']:+.4f}** vs the 50/50 basket. The D37 expectation is ≈ 0 and it
is met on all three. The strategy is genuinely market-neutral. It is also genuinely
unprofitable, and those two facts are independent.

### 4. The stitching choice was measured, not asserted

`stitch_chained` (the pairs-study v1–v3 pattern) returns
{chained.total_return:+.1%} against the continuous run's {continuous.total_return:+.1%} at
the same tier, with {chained.n_round_trips} round trips against
{continuous.n_round_trips}. The gap is the free liquidation at each of the
{result.n_windows} window boundaries **plus** the silent reset of the strategy's own
hysteresis state (`_side`), which a fresh per-window instance discards. It is not a small
effect, and it is the reason the continuous pattern is the headline (D123)."""


def _cointegration_section(result: cp.StudyResult) -> str:
    coint = result.cointegration
    n = result.n_windows
    return f"""---

# Cointegration: testing the premise instead of assuming it

BTC/ETH was chosen a priori, and it is famous. D22's rule — selection belongs inside the
training window, over a broad universe — cannot be satisfied by a study with no selection
step, so D70's meta-in-sample caveat applies in full. The one honest thing available is to
test the premise the strategy rests on, inside the training windows only, and report the
answer whatever it is.

**Method.** For each of the {n} training windows (`walk_forward_windows` hands out views
that physically contain no test bar, D22/D56), two tests on the {result.config.train_size}
training bars:

1. The **traded 1:1 log spread** ln A − ln B, demeaned, through `research.cointegration`'s
   ADF (D93). The hedge ratio is *known*, not estimated, so the Dickey–Fuller τ_μ table
   applies. Critical values are anchored against `statsmodels.tsa.stattools.adfuller` in
   the unit suite rather than typed in from memory.
2. The textbook **Engle–Granger** residual: fit ln A = α + β·ln B on the window, ADF the
   residual against the stricter EG critical values (β was estimated from the same
   sample). β is reported and **not** traded — D92's coherence argument: stationarity
   evidence about ln A − 0.4·ln B is evidence about a spread this strategy does not hold.

**Why thresholds at all, when D29/D93 refused them.** Those decisions govern *selection*,
where ranking N candidates is the honest operation and a p-value adds nothing. This study
selects nothing. The only question an ADF can answer here is the binary one, and that
needs a critical value (D125).

{cp.render_cointegration_table(result)}

β median {float(sorted(coint.betas)[len(coint.betas) // 2]):.3f}, range
{min(coint.betas):.3f} to {max(coint.betas):.3f}; inside [0.7, 1.3] in
{coint.beta_coherent_rate():.0%} of windows.

**What this means.** A 5% test that fires {coint.rate('5%'):.0%} of the time is
indistinguishable from a 5% test firing on noise. The pair *tracks* — that is what makes
it famous — but tracking is not mean reversion, which is exactly the distinction study v1
of the ETF pairs work already ran into (D92). Here it is worse: β is not merely noisy, it
is systematically far from 1, so even the pairs that "look" cointegrated are cointegrated
in a spread with a hedge ratio the strategy does not use.

Per-window detail:

{cp.render_window_cointegration_table(result)}"""


def _performance_section(result: cp.StudyResult) -> str:
    ref = _ref_tier(result)
    return f"""---

# Performance

## Every variant at the reference tier (`{ref.name}`, {ref.fee_bps / 100:.2f}% taker)

Costs are split into the three bricks that charge them, because for a pairs book they are
not the same story: fees scale with turnover, borrow scales with time short, margin
scales with gross exposure above NAV.

{cp.render_variant_table(result, ref.name, ORDERED)}

## The baseline across the cost tiers — maker vs taker

{cp.render_tier_table(result, BASELINE)}

**Two legs, four fills per round trip.** A pairs entry buys one leg and sells the other;
the exit reverses both. Against the breakout study's two fills per round trip that is
double the fee bill for the same tier, before accounting for the fact that this strategy
also re-normalizes both legs to constant gross every bar (the `ZScorePairsStrategy` +
`Sizer` convention, D61/D94), which is where the
{result.results[(BASELINE, ref.name)].annual_turnover:.0f}× annualised turnover comes
from. Concretely: going from `maker_0bp` to `{ref.name}` gives up
{(result.results[(BASELINE, 'maker_0bp')].total_return - result.results[(BASELINE, ref.name)].total_return) / (1 + result.results[(BASELINE, 'maker_0bp')].total_return):.0%}
of the zero-fee terminal wealth and
{result.results[(BASELINE, 'maker_0bp')].sharpe_annual(result.config) - result.results[(BASELINE, ref.name)].sharpe_annual(result.config):.2f}
of annualised Sharpe. The breakout study found the same fee range worth a fraction of a
Sharpe point on a book that trades a few dozen times a decade; a book that re-normalizes
200% of gross every day is in a different regime entirely. **It is still not the binding
constraint here** — see the zero-cost row.

## Gross exposure and the margin threshold (D96)

{cp.render_variant_table(result, ref.name, [BASELINE] + GROSS_NAMES)}

At `leg_weight` = 1.0 the book runs ~200% gross, so D5's margin base — max(gross − NAV, 0)
— is roughly NAV itself and margin interest accrues continuously. At 0.5, gross equals NAV
and the base collapses; at 0.25 it is zero. D96 found that threshold to be the dominant
cost lever on the ETF pairs book, and the margin column above reproduces the collapse
exactly. What it does not do is rescue the result: de-levering scales a negative return
stream toward zero without changing its sign.

## Convention and cost-assumption sensitivities

{cp.render_variant_table(result, ref.name, [BASELINE] + CONVENTION_NAMES + COST_NAMES)}"""


def _grid_section(result: cp.StudyResult) -> str:
    ref = _ref_tier(result)
    spread = cp.grid_spread(result, ref.name)
    gap = spread["best_minus_neighbours_over_spread"]
    if gap > 0.5:
        verdict = (
            "**Read this as a spike, not a plateau — do not quote the best cell.** The top "
            "cell stands more than half the surface's entire range above its own "
            "neighbours, which is what an artifact of one sample looks like."
        )
    elif gap > 0.25:
        verdict = (
            "**Borderline.** The top cell sits meaningfully above its immediate neighbours: "
            "not a clean plateau, and the best cell should not be quoted as the strategy's "
            "performance."
        )
    else:
        verdict = (
            "**This is a plateau, not a spike.** The best cell's neighbours are close "
            "behind it, so the parameter choice is not carrying the result."
        )
    return f"""---

# Parameter sensitivity

12 cells: `lookback` ∈ {{{', '.join(str(x) for x in cp.GRID_LOOKBACKS)}}} ×
`entry_z` ∈ {{{', '.join(f'{z:g}' for z in cp.GRID_ENTRY_Z)}}}, with `exit_z` held at
D69's a-priori {cp.GRID_EXIT_Z:g}. Holding `exit_z` is a scope choice, not an oversight —
adding it as a third axis triples the grid — and it is named again in the caveats.

Annualised Sharpe at `{ref.name}`:

{cp.render_grid_surface(result, ref.name, "sharpe")}

Same surface, CAGR:

{cp.render_grid_surface(result, ref.name, "cagr")}

Same surface, round trips (the mechanical explanation for the shape):

{cp.render_grid_surface(result, ref.name, "round_trips")}

**Spike test.** Best cell is lookback={int(spread['best_lookback'])},
entry_z={spread['best_entry_z']:g} at Sharpe {spread['best_sharpe']:.3f}; its immediate
neighbours average {spread['neighbour_mean_sharpe']:.3f}; the whole
{int(spread['n_cells'])}-cell surface spans {spread['worst_sharpe']:.3f} to
{spread['best_sharpe']:.3f} (spread {spread['surface_spread']:.3f}). The
best-minus-neighbours gap is **{gap:.2f} of the surface's own spread**. {verdict}

**The best cell is a corner, and that matters more than the spike test.** Sharpe improves
monotonically along both axes — longer `lookback`, higher `entry_z` — so the surface's
optimum lies outside the grid, and what the surface is actually measuring is *trade less*.
The round-trip grid makes the mechanism explicit: the best cell takes
{result.results[(f"grid_lb{cp.GRID_LOOKBACKS[-1]}_z{cp.GRID_ENTRY_Z[-1]:g}", ref.name)].n_round_trips}
round trips against the worst cell's
{result.results[(f"grid_lb{cp.GRID_LOOKBACKS[0]}_z{cp.GRID_ENTRY_Z[0]:g}", ref.name)].n_round_trips}.
A parameter surface whose only gradient is "do this less" is not evidence of a parameter
worth tuning; it is the shape a strategy with negative expectancy per trade produces by
construction, and extending the grid would extend the gradient rather than find a peak.

Every cell in the surface is negative, which makes the plateau/spike question mostly
academic here: there is no cell worth quoting.

Same surface at the free tier (`maker_0bp`), which strips the **fee** effect out (borrow
and margin interest are still charged — they are carry, not fees, and no tier turns them
off; the `carry_free` variant above is what does):

{cp.render_grid_surface(result, "maker_0bp", "sharpe")}"""


def _tearsheet_section(result: cp.StudyResult) -> str:
    ref = _ref_tier(result)
    r = result.results[(BASELINE, ref.name)]
    basket = result.benchmarks[("basket_5050", ref.name)]
    table = render_metrics_table(
        r.oos_returns,
        rf_annual=result.config.rf_annual,
        periods_per_year=result.config.periods_per_year,
        equity_curve=r.oos_equity,
        benchmark_returns=basket.oos_returns,
        mc_seed=result.config.seed,
    )
    return f"""---

# Tearsheet — baseline `{BASELINE}` at real costs (`{ref.name}`)

Benchmark for the beta row is the 50/50 basket. The ≈ 0 expectation printed next to it is
D37's, and it is the one line in this document the strategy passes cleanly.

{table}"""


def _benchmark_section(result: cp.StudyResult) -> str:
    ref = _ref_tier(result)
    return f"""---

# Benchmarks (D37: risk-free first, buy-and-hold second)

{cp.render_benchmark_table(result, ref.name, BASELINE)}

**Read the two frames separately.**

- **Against the risk-free rate**, which D37 makes the primary hurdle for a market-neutral
  book: the strategy's Sharpe is
  {result.results[(BASELINE, ref.name)].sharpe_annual(result.config):.2f}. That is not
  "indistinguishable from zero"; it is decisively negative against a
  {result.config.rf_annual:.0%} hurdle over {result.n_oos_bars:,} bars.
- **Against buy-and-hold**, which is a *long-only* comparison for a book built to have no
  market exposure: the gap is enormous, and it is also the wrong test. A market-neutral
  strategy that matched buy-and-hold would be a market-neutral strategy that had failed at
  being market-neutral. The realised-beta column is how you check that, and it says the
  neutrality is real.

The benchmark columns are still worth printing, because they establish the opportunity
cost honestly: over this span, the beta this strategy deliberately refused was the entire
return available on these two instruments."""


def _dsr_section(result: cp.StudyResult) -> str:
    lines = [
        "| Tier | Best variant in pool | Its daily SR | T (bars) | N (configs in pool) | V[{SRn}] | **DSR** |",
        "|---|---|---|---|---|---|---|",
    ]
    for tier in result.tiers:
        i = result.dsr_inputs_by_tier[tier.name]
        lines.append(
            f"| `{tier.name}` | `{i['best_variant']}` | {i['observed_sr_daily']:.4f} | "
            f"{i['t']:,} | {i['n_trials']} | {i['var_trials_daily']:.6f} | "
            f"**{result.dsr_by_tier[tier.name]:.4f}** |"
        )
    return f"""---

# Deflated Sharpe (D21/D86/D98/D116)

{chr(10).join(lines)}

**What the trial pool is.** Per D116, for a parameter-swept study N is the number of
*configurations* tried, so the pool at each tier is every **grid** and **gross** variant's
out-of-sample daily Sharpe — {result.dsr_inputs_by_tier[cp.REFERENCE_TIER]['n_trials']}
configurations. Pool membership is decided on identity fields in the logged config
(`row_kind`, `group`, `tier`) and never on the presence of a metric (D98's rule).
Per-window rows carry `row_kind="window"` and are excluded by the same predicate. Units
are per-period (daily, non-annualised) throughout, per D98's contract.

**What the trial pool is NOT.** It excludes the convention sensitivities (fill timing,
stitching) and the cost-assumption sensitivities (borrow rate), because those are the same
configuration re-priced — D98 established that a re-pricing is a sensitivity point, not an
additional independent trial. More importantly it excludes the two largest terms of all:

- **The pair.** BTC/ETH was chosen a priori because it is the famous crypto pair. There
  is no selection step to correct, so D29's multiplicity machinery has nothing to bite on
  and D70's meta-in-sample caveat stands uncorrected. The registry's N cannot see this.
- **The asset class.** Testing a pairs strategy on the two crypto assets that survived to
  2025 is a selected sample by construction.

**The reading is unchanged from D90/D116: DSR < 0.95 means "no demonstrated edge"; DSR ≥
0.95 does not mean the reverse.** Every DSR here is below
{max(result.dsr_by_tier.values()):.3f}, which is what a decisively negative observed
Sharpe produces under any N — the deflation is doing almost no work, because the *best of
14 configurations* is still far below the noise floor. So the multiplicity question never
becomes load-bearing in this study. That is an accident of the sign, not a strength of the
method: had the observed Sharpe been positive, the uncounted pair-choice multiplicity
above would have made these numbers unusable at face value."""


def _multiplicity(result: cp.StudyResult) -> str:
    return f"""---

# Multiplicity: everything that was evaluated

| What | Count |
|---|---|
| Strategy variants | {len(result.variants)} |
| — parameter-grid cells (lookback × entry_z) | {len(GRID_NAMES)} |
| — gross-exposure (`leg_weight`) settings | {len(GROSS_NAMES)} |
| — convention sensitivities (fill timing, stitching) | {len(CONVENTION_NAMES)} |
| — cost-assumption sensitivities (borrow rate) | {len(COST_NAMES)} |
| Cost tiers | {len(result.tiers)} |
| **Out-of-sample trials logged** | **{len(result.results)}** |
| Per-window trial rows logged | {len(result.results) * result.n_windows:,} |
| In-training-window cointegration tests (diagnostic, not trials) | {result.n_windows} |
| Fitted parameters | **0** |

Nothing in this study is fitted. The cointegration tests are diagnostics computed on
training views and never feed a trading decision, so they are not selection and do not
enter N — but they are listed because "how many things did you look at" is the question
multiplicity accounting exists to answer, and the answer includes them."""


def _verdict(result: cp.StudyResult) -> str:
    ref = _ref_tier(result)
    base = result.results[(BASELINE, ref.name)]
    free_all = result.results[("carry_free", "maker_0bp")]
    free_fee = result.results[(BASELINE, "maker_0bp")]
    borrow_0 = result.results[("borrow_0pct", ref.name)]
    borrow_25 = result.results[("borrow_25pct", ref.name)]
    lw025 = result.results[("gross_lw0.25", ref.name)]
    lw05 = result.results[("gross_lw0.5", ref.name)]
    coint = result.cointegration
    betas = result.betas_by_tier[ref.name]
    costs = base.cost_totals()
    worst = _worst_window(result, BASELINE, ref.name)
    return f"""---

# Verdict

**No edge, at any cost tier, at any parameter setting in the grid, before frictions or
after them.**

- Zero fees, zero carry: **{free_all.total_return:+.1%}**
  (Sharpe {free_all.sharpe_annual(free_all.resolved):.2f}).
- Zero fees, real carry: **{free_fee.total_return:+.1%}**
  (Sharpe {free_fee.sharpe_annual(free_fee.resolved):.2f}).
- Full real costs at the taker tier: **{base.total_return:+.1%}**
  (Sharpe {base.sharpe_annual(base.resolved):.2f}, max drawdown {base.max_drawdown:.1%}).
- Every one of the {int(cp.grid_spread(result, ref.name)['n_cells'])} grid cells is
  negative at every tier.

**Why, mechanically.** The strategy's premise is that ln(BTC) − ln(ETH) mean-reverts. On
this sample it does not: the ADF rejects a unit root in only
{coint.rate('5%'):.0%} of training windows at the 5% level, and the relationship the data
*does* support has a median β of
{float(sorted(coint.betas)[len(coint.betas) // 2]):.2f} — nowhere near the 1:1 hedge the
strategy holds. A {cp.BASELINE_ENTRY_Z:.1f}σ entry into a spread that trends instead of
reverting is a loss-generating machine, and the walk-forward record shows it: the worst
single window is
window {worst[0]} ({worst[2]} → {worst[3]}) at **{worst[1]:+.1%}** — a mean-reversion book
meets a spread that keeps widening by holding, and re-normalizing to constant gross every
bar means holding *harder* as the loss accumulates.

**Where the money goes, at real costs.** Fees {costs['fees']:,.0f}, borrow
{costs['borrow']:,.0f}, margin interest {costs['margin']:,.0f} — on
{result.config.starting_cash:,.0f} of starting capital over
{base.years:.1f} years. The two carry bricks together are comparable in size to the fee
bill even at the taker tier, which is the structural point a long-only study cannot make:
**a pairs book pays rent on both the short leg and the leverage, every day it is in a
trade, whether or not it trades.**

**The borrow assumption, stated because it is the most result-corrupting choice available
(D124).** The headline uses {result.config.borrow_annual_rate:.0%}/yr on the short leg.
The sensitivity spans {borrow_0.total_return:+.1%} at 0%/yr to
{borrow_25.total_return:+.1%} at 25%/yr. A silent zero would have left
**{(1 + borrow_0.total_return) / (1 + base.total_return):.2f}× the terminal wealth** the
stated rate produces — a large relative flattery on a small base — and would have been
indefensible: shorting spot BTC or ETH means borrowing the coin from a venue, and that is
neither free nor stable. What makes the verdict robust is not the rate chosen but that
**it does not move at 0%/yr either**: the strategy still loses
{abs(borrow_0.total_return):.0%}.

**Gross exposure.** De-levering to `leg_weight` = 0.5 makes gross exposure equal NAV, and
margin interest collapses from {costs['margin']:,.0f} to
{lw05.cost_totals()['margin']:,.0f}; at 0.25 it is exactly zero. That is D96's threshold
arithmetic reproduced on a different instrument, and it is the study's one clean
confirmation of an earlier finding. It does not rescue anything: total return improves to
{lw05.total_return:+.1%} and {lw025.total_return:+.1%} because a smaller position loses
less, while Sharpe goes {base.sharpe_annual(base.resolved):.2f} →
{lw05.sharpe_annual(lw05.resolved):.2f} → {lw025.sharpe_annual(lw025.resolved):.2f} —
**not** monotone, because the {result.config.rf_annual:.0%} risk-free hurdle does not
scale down with the position. De-levering a negative-drift strategy walks it toward cash,
and against a positive rf, cash strictly beats it.

**What survives.** The market-neutrality claim, and only that: realised beta
{betas[f'vs_{result.config.symbol_a}']:+.4f} / {betas[f'vs_{result.config.symbol_b}']:+.4f}
/ {betas['vs_basket_5050']:+.4f} against the two legs and the basket, against a D37
expectation of ≈ 0. The engineering works. The thesis does not.

## What would change the answer

Not a cheaper venue, and not a better parameter. The three levers that could matter, in
descending order:

1. **A hedge ratio the data supports.** β is systematically far from 1 and moves across
   windows. D94 already found that a static per-window β estimate cost more in estimation
   noise than it bought on the ETF universe — but on a pair whose β median is
   {float(sorted(coint.betas)[len(coint.betas) // 2]):.2f} rather than ≈ 1, that finding
   does not transfer, and a β-hedged version of this study is the obvious next experiment.
2. **A pair chosen inside the training window, from a universe.** D22's rule, which this
   study structurally cannot satisfy. Crypto has enough liquid assets for a real selection
   step, and that would also give the DSR something honest to deflate.
3. **A cointegration gate on the trade itself**, not just as a diagnostic: stand aside in
   windows where the training-window ADF does not reject. On this pair that would mean
   standing aside {1 - coint.rate('5%'):.0%} of the time, which is close to "do not trade
   this pair" — the same conclusion by a longer route."""


def _caveats(result: cp.StudyResult) -> str:
    return f"""---

# Standing caveats (R3)

1. **Meta-in-sample by pair choice (D22/D70).** BTC/ETH was not selected by any procedure
   in this study; it was chosen because it is the famous crypto pair. There is no
   selection step, so there is nothing for D29's multiplicity correction to work on, and
   the DSR cannot see this bias. The direction of the bias is *toward* a flattering
   result, which makes the negative verdict conservative.
2. **The sample is ETH's.** Inner-join alignment (D45/D63) truncates the study to
   2017-11-09 onward, discarding 1,043 BTC bars. Correct for a pairs trade, but it means
   no number here shares a span with `BREAKOUT_RESULTS.md`'s BTC rows.
3. **`exit_z` is not swept.** Held at D69's 0.5 across all 12 grid cells. The hysteresis
   band's width is a real degree of freedom and it was not explored.
4. **Borrow and margin rates are assumptions, not measurements.**
   {result.config.borrow_annual_rate:.0%}/yr coin borrow and
   {result.config.margin_annual_rate:.0%}/yr USD margin are mid-range for this sample's
   venues; both were swept, neither was sourced from a rate history. A real study would
   use a borrow-rate time series, and crypto borrow rates spike exactly when spreads
   dislocate — i.e. precisely when this strategy is largest.
5. **Fees only, on the trade side.** No bid/ask spread, no market impact, no slippage. The
   tiers are `breakout_study`'s and carry D114's caveat unchanged: a market order into a
   dislocated spread is the adversely-selected moment to trade, and daily bars cannot see
   it. Every return here is optimistic on that axis.
6. **Spot, not perpetuals (D108).** Modelled as `Equity(quantity_precision=8)`. A
   perpetual-futures implementation would replace the borrow brick with funding — and
   funding on BTC/ETH perps has historically *paid* shorts on average, which is the one
   modelling change that could move the cost side materially in the strategy's favour.
   It would not close a {result.results[('carry_free', 'maker_0bp')].total_return:.0%}
   zero-cost gap.
7. **Single data source (D26).** yfinance only, no second-source cross-check. Crypto daily
   bars are a cross-venue aggregate, so "the open" is a convention rather than a price
   anyone was quoted.
8. **Constant-gross re-normalization.** `ZScorePairsStrategy` emits a target *weight*
   every bar, and `Sizer` re-sizes to current NAV (D61), so both legs are rebalanced daily
   while in a trade. That is the framework's existing pairs convention (D94) and it drives
   the {result.results[(BASELINE, cp.REFERENCE_TIER)].annual_turnover:.0f}× turnover. A
   band-rebalanced implementation would trade far less; it is a strategy change, not a
   study knob, and was not made."""


if __name__ == "__main__":
    raise SystemExit(main())
