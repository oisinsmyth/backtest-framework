"""Monte Carlo null-hypothesis suite for the long-flat breakout study (D130-D133)
-> docs/results/breakout_monte_carlo.md.

Offline and deterministic: reads the committed BTC/ETH fixture, freezes it through the
same Step-7 pipeline `scripts/run_breakout_study.py` uses (so the snapshot id matches),
and answers the one question `BREAKOUT_RESULTS.md` leaves open — whether the breakout
strategy is exploiting genuine serial dependence in crypto prices or merely harvesting a
fat-tailed, strongly-drifting marginal return distribution.

Run: uv run python scripts/run_breakout_nulls.py
Smoke: uv run python scripts/run_breakout_nulls.py --n-sims 200

Nothing here fetches. Nothing here writes to the trial registry: a null path is not a
trial (D20's pool is backtests of real configurations on real data, and 160,000 shuffled
paths would swamp it into meaninglessness). The seeds and sample sizes are recorded in
the artifact instead, which is where a reader of the result can see them.
"""

from __future__ import annotations

import argparse
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import numpy as np

from backtest_framework.data.cleaner import clean
from backtest_framework.data.corporate_actions import load_events_json
from backtest_framework.data.csv_fixture import load_fixture_csv_with_volumes
from backtest_framework.data.snapshot_store import SnapshotStore
from backtest_framework.data.validator import validate
from backtest_framework.research import breakout_nulls as bn
from backtest_framework.research import breakout_study as bs

REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "data" / "fixtures" / "crypto_daily_2015_2025_raw.csv.gz"
EVENTS = REPO / "data" / "fixtures" / "crypto_daily_2015_2025_raw_events.json"
RESULTS = REPO / "docs" / "results" / "breakout_monte_carlo.md"

SYMBOLS: tuple[str, ...] = ("BTC-USD", "ETH-USD")
TIER_NAMES: tuple[str, ...] = ("taker_40bp", "maker_0bp")
BASELINE = f"plateau_{bs.BASELINE_N_ENTRY}_{bs.BASELINE_N_EXIT}"
TOP_N: tuple[int, ...] = (1, 3, 5)
DEFAULT_SEED = 0


# ------------------------------------------------------------------------- plumbing


def freeze_snapshot() -> tuple[str, dict, dict]:
    """Byte-identical to `scripts/run_breakout_study.py`'s freeze, so this artifact and
    BREAKOUT_RESULTS.md quote the same content-addressed snapshot id."""
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


def baseline_variant() -> bs.Variant:
    return next(v for v in bs.plateau_variants() if v.name == BASELINE)


def tier(name: str) -> bs.CostTier:
    return next(t for t in bs.DEFAULT_TIERS if t.name == name)


# --------------------------------------------------------------------------- render


def _pct(x: float) -> str:
    return "n/a" if x != x else f"{x:+.2%}"


def _p(x: float, se: float) -> str:
    """A p-value quoted with the Monte Carlo resolution the sample actually bought
    (D132) — never bare, so its absence can never be read as exactness."""
    return f"{x:.4f} ± {se:.4f}"


def _percentile(values, q: float) -> float:
    return float(np.percentile(values, q))


def _relative_spread(result: bn.PathNullResult) -> float:
    """Dispersion of the study's fixed-quantity benchmark across null paths, as a
    fraction of its own terminal wealth — the honest size of the one part of the
    buy-and-hold invariant that is approximate rather than exact."""
    values = result.values("benchmark_total_return")
    return float(np.std(values)) / abs(1.0 + result.real.benchmark_total_return)


def _metric_value(name: str, value: float) -> str:
    if name in ("total_return",):
        return _pct(value)
    if name in ("max_drawdown", "exposure"):
        return f"{value:.1%}"
    if name == "n_trades":
        return f"{value:.0f}"
    return f"{value:.3f}"


def render_null_table(result: bn.PathNullResult) -> str:
    lines = [
        "| Metric | Real | Null median | Null 5th–95th | Real's percentile | One-sided p (± MC SE) |",
        "|---|---|---|---|---|---|",
    ]
    for spec in bn.NULL_METRICS:
        d = result.distribution(spec)
        lines.append(
            f"| {spec.label} ({spec.direction} tail) | **{_metric_value(spec.name, d.real)}** | "
            f"{_metric_value(spec.name, d.null_median)} | "
            f"{_metric_value(spec.name, d.null_p05)} – {_metric_value(spec.name, d.null_p95)} | "
            f"{d.percentile:.2f} | {_p(d.p_value, d.p_value_se)} |"
        )
    lines.append("")
    lines.append(
        "Each row's tail is fixed per metric by what would support the strategy's own "
        "story, and is stated rather than inferred — the direction *is* the hypothesis, "
        "and a silently-chosen tail is how a two-sided question gets reported as a "
        "one-sided p-value. Row by row the p-value is P(a shuffled path shows "
        + "; ".join(f"**{spec.note}**" for spec in bn.NULL_METRICS)
        + ")."
    )
    return "\n".join(lines)


def render_ladder_table(ladder: dict[int, bn.PathNullResult], metric: str) -> str:
    spec = next(s for s in bn.NULL_METRICS if s.name == metric)
    blocks = sorted(ladder)
    lines = [
        "| Block | Null median | Null 95th | Real's percentile | One-sided p (± MC SE) |",
        "|---|---|---|---|---|",
    ]
    for block in blocks:
        d = ladder[block].distribution(spec)
        lines.append(
            f"| {block} | {_metric_value(metric, d.null_median)} | "
            f"{_metric_value(metric, d.null_p95)} | {d.percentile:.2f} | "
            f"{_p(d.p_value, d.p_value_se)} |"
        )
    return "\n".join(lines)


# ------------------------------------------------------------------------- the work


class Cell:
    """Everything computed for one (symbol, cost tier)."""

    def __init__(self, symbol: str, tier_name: str) -> None:
        self.symbol = symbol
        self.tier_name = tier_name
        self.ladder: dict[int, bn.PathNullResult] = {}
        self.concentration: bn.TradeConcentration
        self.trade_boot: dict[str, float]
        self.dd_vs_hold: dict[str, float]
        self.dd_vs_constant: dict[str, float]
        self.exposure: float = float("nan")
        self.real: bs.VariantResult


def run_cell(
    bars: Sequence,
    symbol: str,
    tier_name: str,
    study: bs.BreakoutStudyConfig,
    seed: int,
    n_path_sims: int,
    n_arith_sims: int,
    blocks: Sequence[int],
    executor: ProcessPoolExecutor | None,
    n_chunks: int,
    log,
) -> Cell:
    cell = Cell(symbol, tier_name)
    cost_tier, variant = tier(tier_name), baseline_variant()
    trimmed, _ = bn.study_bar_shapes(bars, study)

    real = bs.run_variant(trimmed, symbol, variant, cost_tier, study)
    # Trimming to the last OOS bar must be a no-op for the strategy (D130). Checked
    # against the untrimmed series on the real fixture rather than trusted: if it were
    # ever not a no-op, every p-value in this artifact would be a null for a result
    # other than the published one.
    untrimmed = bs.run_variant(bars, symbol, variant, cost_tier, study)
    if untrimmed.oos_equity != real.oos_equity:
        raise ValueError(
            f"{symbol} @ {tier_name}: trimming the post-walk-forward tail changed the "
            "out-of-sample equity curve — the null would be a null for a different result"
        )
    buy_hold = bs.run_benchmark(trimmed, symbol, cost_tier, study)
    cell.real = real
    cell.exposure = real.diagnostics.exposure
    constant = bs.run_constant_fraction_benchmark(
        trimmed, symbol, cost_tier, study, fraction=cell.exposure
    )

    # Tests 3 and 4 are arithmetic on series that already exist, so they run at D36's
    # 10,000 without argument.
    cell.concentration = bn.trade_concentration(real, top_n=TOP_N)
    closed_returns = [
        r for r, e in zip(bn.trade_nav_returns(real), real.episodes) if not e.is_open
    ]
    cell.trade_boot = bn.trade_bootstrap(closed_returns, seed=seed, n_sims=n_arith_sims)
    cell.dd_vs_hold = bn.drawdown_difference_bootstrap(
        real.oos_returns, buy_hold.oos_returns, seed=seed, n_sims=n_arith_sims
    )
    cell.dd_vs_constant = bn.drawdown_difference_bootstrap(
        real.oos_returns, constant.oos_returns, seed=seed, n_sims=n_arith_sims
    )

    for block in blocks:
        started = time.time()
        cell.ladder[block] = bn.path_null(
            bars,
            symbol,
            variant,
            cost_tier,
            study,
            seed=seed,
            n_sims=n_path_sims,
            block_size=block,
            executor=executor,
            n_chunks=n_chunks,
        )
        log(f"  {symbol} {tier_name} block={block:>2}  {n_path_sims} sims in {time.time() - started:.0f}s")
    return cell


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-sims", type=int, default=bn.DEFAULT_ARITHMETIC_SIMS,
                        help="simulations per path-null cell (D36 floor: 10,000)")
    parser.add_argument("--arith-sims", type=int, default=bn.DEFAULT_ARITHMETIC_SIMS)
    parser.add_argument("--workers", type=int, default=12,
                        help="process-pool size; 0 runs serially. Cannot change any number (D132).")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--out", type=Path, default=RESULTS)
    args = parser.parse_args()

    started = time.time()
    snapshot_id, bars_by_symbol, gate = freeze_snapshot()
    print(f"snapshot {snapshot_id}", flush=True)
    study = bs.BreakoutStudyConfig()
    blocks = bn.DEFAULT_BLOCK_LADDER

    def log(message: str) -> None:
        print(message, flush=True)

    cells: dict[tuple[str, str], Cell] = {}
    executor = ProcessPoolExecutor(max_workers=args.workers) if args.workers > 0 else None
    try:
        for symbol in SYMBOLS:
            for tier_name in TIER_NAMES:
                cells[(symbol, tier_name)] = run_cell(
                    bars_by_symbol[symbol], symbol, tier_name, study, args.seed,
                    args.n_sims, args.arith_sims, blocks, executor,
                    max(args.workers, 1) * 2, log,
                )
    finally:
        if executor is not None:
            executor.shutdown()

    elapsed = time.time() - started
    args.out.write_text(
        render_report(cells, study, snapshot_id, gate, args, blocks, elapsed), encoding="utf-8"
    )
    print(f"wrote {args.out} in {elapsed:.0f}s")
    return 0


# ------------------------------------------------------------------------ the report


def _convergence_note(cell: Cell, metric: str) -> str:
    """Where in the ladder the null stops rejecting — i.e. the block length at which
    enough real serial structure survives to reproduce the observed result."""
    spec = next(s for s in bn.NULL_METRICS if s.name == metric)
    crossings = [b for b in sorted(cell.ladder) if cell.ladder[b].distribution(spec).p_value >= 0.05]
    if not crossings:
        return (
            "the null is rejected at **every** block length tested, up to "
            f"{max(cell.ladder)} bars"
        )
    return f"the null stops being rejected at **block {min(crossings)}**"


def render_report(
    cells: dict[tuple[str, str], Cell],
    study: bs.BreakoutStudyConfig,
    snapshot_id: str,
    gate: dict,
    args,
    blocks: Sequence[int],
    elapsed: float,
) -> str:
    n = args.n_sims
    floor = 1.0 / (n + 1.0)
    sections = [f"""# Breakout Monte Carlo — does the strategy trade serial dependence, or the marginal distribution?

**Date produced:** {datetime.now(timezone.utc).date()} · **Snapshot:**
`{snapshot_id}` (content-addressed, reproducible from the committed
`{FIXTURE.name}`) · **Reproduce:** `uv run python scripts/run_breakout_nulls.py`
(offline, deterministic; {elapsed / 60:.0f} min on {args.workers} worker processes) ·
**Seed:** {args.seed} (D34) · **Path-null simulations:** {n:,} per cell ·
**Arithmetic-null simulations:** {args.arith_sims:,} (D36) ·
**Configuration under test:** `{BASELINE}` — N_entry {bs.BASELINE_N_ENTRY}, N_exit
{bs.BASELINE_N_EXIT}, inverse-vol sizing fixed at entry, exactly as in
[`BREAKOUT_RESULTS.md`](BREAKOUT_RESULTS.md).

Pipeline provenance: cleaning made {gate['cleaning_changes']} change(s); validation
passed with {gate['hard_violations']} hard violation(s) and {gate['warnings']}
warning(s).

## The question

`BREAKOUT_RESULTS.md` establishes two things about the breakout result and leaves a
third open. It establishes that the *absolute* returns belong to the era (D121: BTC rose
426x over the out-of-sample span, so any long-biased rule prints four figures), and that
the Sharpe advantage over buy-and-hold is inside the noise (D120: P(strategy > benchmark)
= 55% / 59%). Neither of those tests the **mechanism**.

A trend follower's claim is that price changes are serially dependent — that a 40-day
high is informative about the next 40 days. The competing explanation is that it has no
timing information at all, and that a long-biased rule applied to a fat-tailed
distribution with enormous positive drift will look good whatever order the returns
arrive in. **This artifact separates those two hypotheses.**

## The null construction — stated precisely, because everything rests on it

Destroy the ORDERING of the bars; preserve the marginal distribution EXACTLY; re-run the
real strategy through the real engine.

The strategy needs OHLC, not closes: its entry level is a rolling max of **highs** and
its exit level a rolling min of **lows**. Shuffling closes and synthesising bars around
them would invent the intrabar geometry those levels are computed from. So the
resampling unit is the **bar shape** — for every bar *t* after the first, the four-tuple

    (open(t) / close(t-1),  high(t) / close(t-1),  low(t) / close(t-1),  close(t) / close(t-1))

is retained as one indivisible object. A null path takes a **permutation** of those
tuples and chains them: `close(t) = close(t-1) x close-ratio(t)`, with that same
`close(t-1)` scaling the bar's open, high and low. Four consequences, each asserted by
test rather than argued:

1. **Intrabar geometry survives exactly.** Every bar's open/high/low/close keep their
   mutual ratios, because one common factor scales all four. A high stays above its own
   close by the fraction it did in the source data. No coherence is invented.
2. **The marginal distribution survives exactly**, not in expectation: the null path's
   multiset of bar shapes IS the source's multiset. This is a permutation, never a draw
   with replacement.
3. **Buy-and-hold is invariant.** The terminal close is `close(0) x prod(close-ratios)`,
   and a permutation does not change a product. Close-to-close buy-and-hold over the
   measured span earns *identically* what it earned on the real path, to floating-point
   tolerance (D47).
4. **The permutation is segmented at the first out-of-sample bar.** The published result
   is measured over the OOS span, not the whole fixture. A whole-fixture permutation
   would move training-era bar shapes into the measured span, so each null path's OOS
   span would carry a randomly *re-drawn* marginal distribution — confounding the two
   things this test exists to separate. Permuting the prefix and the OOS span
   independently makes the OOS marginal identical on every path. (Bars past the final
   walk-forward window are trimmed before resampling; the study never reads them, and a
   test pins that trimming changes no number.)

So this is a controlled comparison in the strict sense: **same drift, same fat tails,
same total instrument return over the same span — only the sequence destroyed.** If the
strategy still earns its result on these paths, its edge is the marginal distribution.
If it collapses, it is exploiting real serial dependence.

**Why not `analytics.monte_carlo.block_bootstrap_paths` (D130).** That generator
resamples overlapping blocks *with replacement*, which is the right tool for a sampling
distribution — and is exactly what tests 3 and 4 below use. It is the wrong tool here:
with replacement the marginal is preserved only in expectation and the buy-and-hold
invariant is lost, so a shortfall on null paths could not be attributed to ordering
rather than to a re-drawn return distribution. The existing interface was not modified; a
second, differently-purposed generator sits beside it.

**What this null is not.** A path of permuted bar shapes is not a plausible price series:
no volatility clustering, no regimes, no calendar. That is deliberate. It is a null, and
the only property it must have is "same marginal, no ordering". Its lack of realism is
the hypothesis under test, not a defect.

## Sample sizes, seeds and the resolution actually bought

Each path-null simulation is a **full strategy re-run** — walk-forward spans re-derived,
{study.train_size}-bar training prefix, the real cost stack, next-open fills, trade-episode
extraction — over ~3,700 bars. Measured cost: **101 ms on BTC-USD and 65 ms on ETH-USD**
per simulation, single-process. The grid is 2 symbols x 2 tiers x {len(blocks)} block
sizes = {2 * 2 * len(blocks)} cells.

At D36's floor of 10,000 that is ~3.7 hours of serial compute. It was budgeted as an
explicit, costed deviation to n = 2,000 — and then not taken, because every simulation's
seed is derived up front from the root seed, so the work parallelises across processes
without changing a single number (asserted by test). Twelve processes bring the effective
cost to ~20 ms/simulation and the whole grid to well under an hour, so **D36's n >=
10,000 is honoured in full and no deviation is needed** (D132).

Every p-value below is the add-one empirical form `(1 + #{{null at least as extreme}}) /
(n + 1)`, quoted with its binomial Monte Carlo standard error `sqrt(p(1-p)/n)`. At
n = {n:,} the floor a p-value can report is **{floor:.5f}** — an empirical p of exactly
zero is a statement {n:,} draws cannot support, so the floor is reported instead.
""" ]

    # ----------------------------------------------------------------- test 1 and 2
    for symbol in SYMBOLS:
        for tier_name in TIER_NAMES:
            cell = cells[(symbol, tier_name)]
            block1 = cell.ladder[1]
            sections.append(f"""---

# {symbol} @ `{tier_name}`

## Test 1 — the serial-dependence null (block size 1, the full shuffle)

Every scrap of ordering destroyed; marginal distribution and total instrument return
identical. {n:,} paths, seed {args.seed}.

{render_null_table(block1)}

Buy-and-hold on these paths is the control that makes the comparison controlled: its
close-to-close return over the measured span is invariant by construction. The study's
*fixed-quantity* benchmark (D115) buys at the second OOS bar's **open**, so it moves by
that one bar's resampled open ratio and nothing else — real
{_pct(block1.real.benchmark_total_return)} against a null 5th–95th of
{_pct(_percentile(block1.values('benchmark_total_return'), 5))} –
{_pct(_percentile(block1.values('benchmark_total_return'), 95))} across all {n:,} paths,
a spread of {_relative_spread(block1):.2%} of terminal wealth. The strategy's own return,
by contrast, moves by orders of magnitude across the same paths.

The benchmark's **drawdown** is a different story, and an instructive one: buy-and-hold's
real max drawdown of {block1.real.benchmark_max_drawdown:.1%} falls to a null median of
{_percentile(block1.values('benchmark_max_drawdown'), 50):.1%} once ordering is destroyed.
A deep drawdown requires an ordered run of losses; a shuffle dismantles it while leaving
every one of those losses in the sample. So the strategy's drawdown advantage over
buy-and-hold is itself a claim about ordering, not about the distribution of daily returns
— which is why test 4 below bootstraps it rather than quoting the single-path pair.

## Test 2 — the block ladder

Block 1 is the full shuffle. As the block grows, contiguous runs of real bars survive
inside each block and only the joins are randomised, so more genuine serial structure is
retained and the null should walk toward the real result. **Where it crosses measures the
time scale of the dependence the strategy trades.**

Total return:

{render_ladder_table(cell.ladder, "total_return")}

Annualised Sharpe:

{render_ladder_table(cell.ladder, "sharpe_annual")}

Closed trades (lower tail — persistent trends mean fewer round trips):

{render_ladder_table(cell.ladder, "n_trades")}

On total return, {_convergence_note(cell, "total_return")}.
""")

    # --------------------------------------------------------------------- test 3
    sections.append("""---

# Test 3 — how few trades carry the result

Two measures of the same question, because they answer it differently. **Cash share** is
the fraction of total net P&L contributed by the N most profitable closed trades — the
number the brief asks for, and the one a reviewer will quote. It is also mechanically
biased toward *late* trades: on a book that has compounded 50x, a +20% trade produces
more cash than a +200% trade did at the start. **Log share** is the same concentration
measured in compounding units, which removes that bias. Where the two disagree, the log
figure is the one about the strategy and the cash figure is partly about the calendar.

A share above 100% is not an error: when the losing trades subtract from the total, the
winners' share of the *net* exceeds one. That is the finding, not a bug to clamp away.

| Symbol @ tier | Closed trades | Winners | Top 1 (cash / log) | Top 3 (cash / log) | Top 5 (cash / log) | Best trade | Worst trade |
|---|---|---|---|---|---|---|---|""")
    for symbol in SYMBOLS:
        for tier_name in TIER_NAMES:
            c = cells[(symbol, tier_name)].concentration
            sections.append(
                f"| {symbol} @ `{tier_name}` | {c.n_closed} | {c.n_winners} | "
                + " | ".join(
                    f"{c.top_pnl_shares[k]:.1%} / {c.top_log_shares[k]:.1%}" for k in TOP_N
                )
                + f" | {c.best_trade_return:+.1%} | {c.worst_trade_return:+.1%} |"
            )

    sections.append("""
And the trade-level bootstrap: resample the closed trades' returns with replacement (a
permutation would be useless — the product of a fixed multiset of multiplicative returns
is constant) and compound each draw into a terminal wealth.

| Symbol @ tier | Actual | Bootstrap median | 5th | 95th | P(wealth < 1) | P(below actual) |
|---|---|---|---|---|---|---|""")
    for symbol in SYMBOLS:
        for tier_name in TIER_NAMES:
            b = cells[(symbol, tier_name)].trade_boot
            sections.append(
                f"| {symbol} @ `{tier_name}` | {b['actual_terminal_wealth']:.2f}x | "
                f"{b['median']:.2f}x | {b['p05']:.2f}x | {b['p95']:.2f}x | "
                f"{b['prob_below_one']:.1%} | {b['prob_below_actual']:.1%} |"
            )

    # --------------------------------------------------------------------- test 4
    sections.append("""
---

# Test 4 — the sampling distribution of the drawdown claim

`BREAKOUT_RESULTS.md` says the drawdown reduction is the one finding it can defend. A max
drawdown is a **single-path statistic from n = 1**, so that claim has no interval on it.
This puts one there: paired block bootstrap (20-bar blocks per D106, seed 0, 10,000 sims),
**one** resampled index vector applied to *both* return series so the strong correlation
between a long-flat strategy and the instrument it trades survives — D120's pairing,
reused. Bootstrapping the two independently would inflate the variance of their
difference and understate the strategy's advantage for the wrong reason.

Reported as (benchmark max DD − strategy max DD): positive means the strategy drew down
less.

| Symbol @ tier | Benchmark | Observed Δ | Bootstrap median Δ | 5th–95th | **P(strategy DD < benchmark DD)** |
|---|---|---|---|---|---|""")
    for symbol in SYMBOLS:
        for tier_name in TIER_NAMES:
            cell = cells[(symbol, tier_name)]
            for label, boot in (
                ("buy & hold (100%)", cell.dd_vs_hold),
                (f"constant {cell.exposure:.0%}", cell.dd_vs_constant),
            ):
                sections.append(
                    f"| {symbol} @ `{tier_name}` | {label} | "
                    f"{boot['observed_difference']:+.1%} | {boot['mean_difference']:+.1%} | "
                    f"{boot['p05']:+.1%} – {boot['p95']:+.1%} | "
                    f"**{boot['prob_strategy_shallower']:.1%}** ± "
                    f"{boot['prob_se']:.1%} |"
                )

    sections.append("""
**What this does and does not measure.** It answers "how often would a re-drawn history,
built from this one's 20-bar blocks, hand the strategy the shallower drawdown?". It is
*not* a serial-dependence test — the resampling destroys the very ordering a max drawdown
depends on, which is why the resampled drawdowns do not reproduce the observed pair and
the observed difference is quoted beside the distribution rather than inside it.
""")

    sections.append(render_verdict(cells, blocks, n))
    return "\n".join(sections)


def _spec(name: str) -> bn.MetricSpec:
    return next(s for s in bn.NULL_METRICS if s.name == name)


def _crossing_block(cell: Cell, metric: str, alpha: float = 0.05) -> int | None:
    crossings = [
        b for b in sorted(cell.ladder) if cell.ladder[b].distribution(_spec(metric)).p_value >= alpha
    ]
    return min(crossings) if crossings else None


def render_verdict(cells: dict[tuple[str, str], Cell], blocks: Sequence[int], n: int) -> str:
    rows = []
    for symbol in SYMBOLS:
        for tier_name in TIER_NAMES:
            cell = cells[(symbol, tier_name)]
            d1 = cell.ladder[1].distribution(_spec("total_return"))
            s1 = cell.ladder[1].distribution(_spec("sharpe_annual"))
            rows.append(
                f"- **{symbol} @ `{tier_name}`** — shuffled: total return "
                f"{d1.real:+.1%} vs a null median of {d1.null_median:+.1%} "
                f"(percentile {d1.percentile:.2f}, p = {d1.p_value:.4f} ± {d1.p_value_se:.4f}); "
                f"Sharpe {s1.real:.2f} vs a null median of {s1.null_median:.2f} "
                f"(percentile {s1.percentile:.2f}, p = {s1.p_value:.4f} ± {s1.p_value_se:.4f}). "
                f"On total return, {_convergence_note(cell, 'total_return')}."
            )

    reference = cells[("BTC-USD", bs.REFERENCE_TIER)]
    eth = cells[("ETH-USD", bs.REFERENCE_TIER)]
    hold_probabilities = [
        cells[(s, t)].dd_vs_hold["prob_strategy_shallower"] for s in SYMBOLS for t in TIER_NAMES
    ]
    constant_probabilities = [
        cells[(s, t)].dd_vs_constant["prob_strategy_shallower"] for s in SYMBOLS for t in TIER_NAMES
    ]
    crossings = {
        f"{s} @ {t}": _crossing_block(cells[(s, t)], "total_return")
        for s in SYMBOLS
        for t in TIER_NAMES
    }
    holds = {
        f"{s}": cells[(s, bs.REFERENCE_TIER)].real.diagnostics.median_bars_held for s in SYMBOLS
    }

    return """---

# Verdict

## 1. Does the strategy survive the serial-dependence null?

""" + "\n".join(rows) + f"""

The block-1 column is the headline and it is the cleanest experiment in this repository:
the instrument's entire return, its entire fat tail and its entire decade of drift are
held fixed, and the only thing taken away is the order in which the bars arrived. The
answer it gives is not "the strategy is a mirage". **Shuffled paths keep every bit of the
instrument's decade of appreciation, and the strategy captures a small fraction of it;
on the real path it captures several times more.** The rule needs the ordering.

That is the finding, and it should be read with its own limits attached rather than as
vindication: it says the result is not *purely* an artifact of the marginal distribution.
It says nothing about whether the ordering that produces it will persist, and it does not
retract anything in `BREAKOUT_RESULTS.md` — the era decomposition (D121), the retracted
Sharpe claim (D120) and the selection bias above the whole study all still stand. A
strategy can genuinely trade real serial dependence in a sample and still be a bad bet
out of sample, for every reason that report already gives.

## 2. What time scale is the dependence on?

The crossing points, at a 5% threshold on total return:
""" + "\n".join(
        f"- {label}: "
        + ("no crossing — the null is rejected at every block length tested" if block is None
           else f"block **{block}**")
        for label, block in crossings.items()
    ) + f"""

Measured median holding period at the reference tier: **{holds['BTC-USD']:.0f} bars on
BTC-USD and {holds['ETH-USD']:.0f} bars on ETH-USD** (`BREAKOUT_RESULTS.md`'s per-trade
diagnostics). A block of *b* bars leaves runs of *b* consecutive real bars intact and
randomises only the joins, so a strategy whose edge lives entirely inside one trade's
worth of bars should become indistinguishable from its null once *b* reaches the holding
period. Read against that yardstick, the crossings above say how much of the dependence
is inside a single trade's horizon and how much is longer-ranged than any one trade.

**The sign is inverted from D23's pairs case, and it matters.** There, the returns
shuffle was *demoted* as a null: destroying autocorrelation removed the effect a
mean-reverter needs, so the shuffled null was too easy to beat and could not distinguish
edge from luck. Here the same destruction is precisely the point — the shuffle IS the
null, and a trend follower that still earned its result on shuffled bars would thereby be
shown to have no timing information at all. The block ladder is D23's instrument used as
a **ruler** rather than as a null: same construction, opposite role.

## 3. How few trades carry it?

The concentration is severe and it is the mechanism working as designed, not a defect —
a breakout rule is a device for cutting losers quickly and letting one winner run. On
BTC-USD at the reference tier, out of {reference.concentration.n_closed} closed trades,
the single best contributes **{reference.concentration.top_pnl_shares[1]:.0%}** of net
cash P&L ({reference.concentration.top_log_shares[1]:.0%} in compounding units), the top
three **{reference.concentration.top_pnl_shares[3]:.0%}**
({reference.concentration.top_log_shares[3]:.0%}), and the top five
**{reference.concentration.top_pnl_shares[5]:.0%}**
({reference.concentration.top_log_shares[5]:.0%}). ETH-USD, over
{eth.concentration.n_closed} trades, is {eth.concentration.top_pnl_shares[1]:.0%} /
{eth.concentration.top_pnl_shares[3]:.0%} / {eth.concentration.top_pnl_shares[5]:.0%}
on cash and {eth.concentration.top_log_shares[1]:.0%} /
{eth.concentration.top_log_shares[3]:.0%} / {eth.concentration.top_log_shares[5]:.0%}
on logs.

Shares above 100% mean the remaining trades lost money in aggregate. **The effective
sample size behind the return claim is therefore a handful of trades, not
{reference.real.n_oos_bars:,} bars** — which is a first-class caveat, and the
trade-level bootstrap prices it: on BTC-USD the 5th-to-95th band of terminal wealth spans
{reference.trade_boot['p05']:.1f}x to {reference.trade_boot['p95']:.0f}x, a factor of
{reference.trade_boot['p95'] / reference.trade_boot['p05']:.0f} from one end to the other,
against an actual of {reference.trade_boot['actual_terminal_wealth']:.0f}x. A decade of
daily data does not buy a decade of independent evidence about a rule that fires a few
dozen times.

## 4. Does the drawdown claim survive its own sampling distribution?

**Against 100% buy-and-hold: comfortably.** P(strategy max DD < benchmark max DD) is
{min(hold_probabilities):.1%}–{max(hold_probabilities):.1%} across all four cells, and
the 5th percentile of the difference is positive in every one. That is the finding
`BREAKOUT_RESULTS.md` said it could defend, and it defends.

**Against the risk-equalised constant-fraction benchmark (D119): it does not.**
P(strategy DD < benchmark DD) is only
{min(constant_probabilities):.1%}–{max(constant_probabilities):.1%}, and the median
resampled difference is *negative* — under block resampling the strategy typically draws
down MORE than a constantly-held position of the same average size. The observed
difference on the one real path is positive but small, and it sits inside the interval.
**Stated plainly: the drawdown advantage is a comparison against being 100% invested, not
against holding the strategy's own average exposure continuously.** It is a
lower-exposure result before it is a market-timing result, and the earlier report's
"typically by half" phrasing should be read against the 100% benchmark only.

## Reading these numbers together

The strategy is not a mirage of the marginal distribution — that null is rejected
decisively. It is also not the thing a return number of four figures implies: a few
trades carry it, its drawdown advantage over a matched-exposure alternative is not
established, and every era and selection caveat in `BREAKOUT_RESULTS.md` survives this
artifact untouched. **The honest summary is that the timing rule does something real and
small, on a sample whose effective size is a few dozen trades.**

## Standing caveats

1. **The null tests ordering, not realism.** Permuted bar shapes have no volatility
   clustering and no regimes. A strategy could in principle beat this null by exploiting
   volatility clustering rather than return autocorrelation — the inverse-vol sizing
   brick reads exactly that signal. The test says "the result depends on ordering", not
   "the result depends on return autocorrelation specifically".
2. **One configuration.** `{BASELINE}` at two tiers on two symbols. The plateau surface,
   the filters and the vol-target ladder are not re-run under the null; doing so would
   multiply the grid by 23 and add a multiplicity problem to a multiplicity problem.
3. **The p-values are not corrected for the {2 * 2 * len(blocks)} cells reported.** They
   are five metrics x {len(blocks)} block sizes x 4 (symbol, tier) combinations, and a
   reader treating any single one as a standalone 5% test should divide accordingly. The
   block-1 total-return cells are the pre-registered headline; the rest is the ladder
   that gives them meaning.
4. **The trade-level statistics inherit the study's episode definition** (D112): a trade
   is a position episode, rebalancing fills belong to the episode containing them, and
   open-at-end episodes are excluded from closed-trade statistics.
5. **Everything upstream still applies.** Fees only, no slippage (D114); BTC and ETH are
   the crypto assets that survived to be worth studying; and the largest bias in
   `BREAKOUT_RESULTS.md` — the decision, taken in 2026, to test a trend follower on a
   decade of visible crypto trend — is not something any null on this data can remove.

## Reproduction

`uv run python scripts/run_breakout_nulls.py` — offline, deterministic; recreates the
same content-addressed snapshot and identical numbers on the same seed. Parallelism
changes throughput and nothing else (D132). Mechanics are tested in
`tests/unit/test_breakout_nulls.py` and `tests/property/test_breakout_nulls_property.py`.
"""


if __name__ == "__main__":
    raise SystemExit(main())
