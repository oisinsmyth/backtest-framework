"""Gross exposure study (D96): the v2 study across leg_weight x AUM.

The capacity analysis (D95) showed no account size clears real costs at 200%
gross, and named the cost floor as the binding constraint. Margin interest - the
floor's biggest term - is a THRESHOLD cost (charged on max(gross - NAV, 0)): at
gross <= NAV it collapses instead of scaling down. Whether that beats the
proportionally smaller edge is sign-unknown; this script measures it.

Run: uv run python scripts/run_gross_sweep.py   (offline, deterministic, ~20 min)
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from backtest_framework.costs.calibration import calibrate_impact_params
from backtest_framework.data.cleaner import clean
from backtest_framework.data.corporate_actions import load_events_json
from backtest_framework.data.csv_fixture import load_fixture_csv_with_volumes
from backtest_framework.data.snapshot_store import SnapshotStore
from backtest_framework.data.validator import validate
from backtest_framework.registry.trial_registry import TrialRegistry
from backtest_framework.research.cointegration import CointegrationSelector
from backtest_framework.research.gross_sweep import (
    render_margin_drag_matrix,
    render_net_return_matrix,
    render_total_drag_matrix,
    run_gross_sweep,
)
from backtest_framework.research.pairs_study import StudyConfig, run_pairs_study

REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "data" / "fixtures" / "universe_daily_2015_2024_raw.csv.gz"
EVENTS = REPO / "data" / "fixtures" / "universe_daily_2015_2024_raw_events.json"
RESULTS = REPO / "docs" / "results" / "gross_exposure_study.md"

CONFIG = StudyConfig()  # v2's configuration; leg_weight and starting_cash vary per cell
LEG_WEIGHTS = (0.25, 0.5, 0.75, 1.0)
AUM_LEVELS = (100e3, 300e3, 1e6, 3e6, 10e6)


def make_selector() -> CointegrationSelector:
    return CointegrationSelector(gatev_prefilter=50, beta_window=(0.7, 1.3), adf_lags=1)


def main() -> int:
    bars, volumes = load_fixture_csv_with_volumes(FIXTURE)
    actions = load_events_json(EVENTS)

    cleaned, cleaning_report = clean(bars, volumes)
    validation = validate(cleaned, actions, volumes)
    store = SnapshotStore(REPO / "data" / "snapshots")
    snapshot_id = store.create(cleaned, actions, cleaning_report=cleaning_report, validation=validation,
                               extra_meta={"source_fixture": FIXTURE.name})
    snapshot = store.load(snapshot_id)

    adv_by_symbol = {
        s: p.adv_shares for s, p in calibrate_impact_params(snapshot.bars_by_symbol, volumes).items()
    }

    registry = TrialRegistry(REPO / "data" / "gross_sweep_registry.sqlite")
    print(f"snapshot: {snapshot_id[:16]}...  grid: {len(LEG_WEIGHTS)} leg_weights x {len(AUM_LEVELS)} AUM levels")
    result = run_gross_sweep(
        bars_by_symbol=snapshot.bars_by_symbol,
        volumes_by_symbol=volumes,
        actions=snapshot.actions,
        registry=registry,
        snapshot_id=snapshot_id,
        leg_weights=LEG_WEIGHTS,
        aum_levels=AUM_LEVELS,
        config=CONFIG,
        selector_factory=make_selector,
        adv_by_symbol=adv_by_symbol,
    )
    for lw, cap in result.by_leg_weight.items():
        cells = "  ".join(f"{lv.label} {lv.net_return_annual:+.2%}/yr" for lv in cap.levels)
        print(f"  lw {lw:g}: {cells}")

    # Per-lw gross reference (0x through a PLAIN stack at $100M, like D95's
    # sanity run): the honest numerator for each column - compounding and
    # rounding keep the edge from scaling exactly with lw.
    print("gross reference runs (0x/1x, plain stack, $100M)...")
    gross_by_lw: dict[float, float] = {}
    for lw in LEG_WEIGHTS:
        sanity = run_pairs_study(
            bars_by_symbol=snapshot.bars_by_symbol,
            volumes_by_symbol=volumes,
            actions=snapshot.actions,
            registry=registry,
            snapshot_id=snapshot_id,
            config=replace(CONFIG, leg_weight=lw, starting_cash=100e6, multipliers=(0.0, 1.0)),
            trial_id_prefix=f"gross-sanity-lw{lw:g}",
            selector=make_selector(),
        )
        gross_by_lw[lw] = sanity.curves[0.0].final_nav / 100e6 - 1.0
        print(f"  lw {lw:g}: gross {gross_by_lw[lw]:+.2%}")

    years = result.by_leg_weight[LEG_WEIGHTS[0]].levels[0].years
    gross_annual = {lw: (1.0 + g) ** (1.0 / years) - 1.0 for lw, g in gross_by_lw.items()}
    gross_ref_lines = ["| leg_weight | Book gross | Gross return (9yr, 0×) | Gross /yr |", "|---|---|---|---|"]
    for lw in LEG_WEIGHTS:
        gross_ref_lines.append(
            f"| {lw:g} | {2 * lw:.0%} | {gross_by_lw[lw]:+.2%} | {gross_annual[lw]:+.2%} |"
        )
    gross_ref_table = "\n".join(gross_ref_lines)

    positive = [
        (lw, lv)
        for lw in LEG_WEIGHTS
        for lv in result.by_leg_weight[lw].levels
        if lv.net_return_annual > 0
    ]
    if positive:
        best_lw, best = max(positive, key=lambda t: t[1].net_return_annual)
        cells = ", ".join(f"lw {lw:g} @ {lv.label} ({lv.net_return_annual:+.2%}/yr)" for lw, lv in positive)
        best_sr = best.study.dsr_inputs["observed_sr_daily"] * (CONFIG.periods_per_year ** 0.5)
        finding = (
            f"**{len(positive)} cells clear absolute real costs: {cells}.** The margin "
            f"threshold did what the arithmetic predicted — the drag collapses below 100% "
            f"gross rather than halving (see the margin matrix) — and every positive cell "
            f"lives in the low-gross columns. The best is lw {best_lw:g} at {best.label}: "
            f"{best.net_return_annual:+.2%}/yr net against a {gross_annual[best_lw]:+.2%}/yr "
            f"gross edge.\n\n"
            f"**But clearing costs is not clearing the hurdle.** Against the study's "
            f"{CONFIG.rf_annual:.0%} risk-free rate, the best cell's stitched Sharpe is "
            f"{best_sr:.2f} — it underperforms T-bills by "
            f"≈{abs(best.net_return_annual - CONFIG.rf_annual):.2%}/yr, decisively, not "
            f"marginally. Two honest notes cut opposite ways: (1) the simulator credits no "
            f"interest on idle cash, and a gross ≤ 100% book is MOSTLY idle cash, so a real "
            f"account sweeping cash into bills would recover much of that gap — but that "
            f"return belongs to the risk-free rate, not to the strategy; (2) after five "
            f"studies of program-level multiplicity (D90), even a genuinely thin positive "
            f"edge would be statistically indistinguishable from zero. What this study "
            f"establishes: at low gross the edge can just pay for its own implementation — "
            f"it cannot pay for the capital it occupies."
        )
    else:
        best_lw, best = max(
            ((lw, lv) for lw in LEG_WEIGHTS for lv in result.by_leg_weight[lw].levels),
            key=lambda t: t[1].net_return_annual,
        )
        finding = (
            f"**No (leg_weight, AUM) cell clears real costs.** The best is lw {best_lw:g} at "
            f"{best.label}: {best.net_return_annual:+.2%}/yr. The margin threshold collapsed as "
            f"predicted (see the margin matrix), but the edge shrinks with gross at least as "
            f"fast as the remaining frictions do — the cost story closes completely: this "
            f"edge cannot pay for its own implementation at any gross exposure, at any "
            f"account size."
        )

    n_windows = result.by_leg_weight[LEG_WEIGHTS[0]].levels[0].study.n_windows
    n_trials = (len(LEG_WEIGHTS) * len(AUM_LEVELS) + 2 * len(LEG_WEIGHTS)) * n_windows
    doc = f"""# Gross exposure study — does lower gross clear the cost floor?

**Date produced:** {datetime.now(timezone.utc).date().isoformat()} · **Snapshot:**
`{snapshot_id}` · **Method (D96):** the byte-identical v2 study
([capacity_analysis.md](capacity_analysis.md) machinery, D95) across
**leg_weight ∈ {{{", ".join(f"{lw:g}" for lw in LEG_WEIGHTS)}}} × AUM ∈
{{{", ".join(lv.label for lv in result.by_leg_weight[LEG_WEIGHTS[0]].levels)}}}**, real
unscaled costs. One variable: leg_weight (book gross when all pairs are in trade
= 2·lw·NAV). The mechanism under test is the **margin threshold** — interest
accrues on max(gross − NAV, 0), so at gross ≤ NAV it collapses instead of
scaling down, while the edge scales ≈∝ lw, spread/borrow ∝ lw, impact ∝ lw^1.5,
and the $1/order commission minimums don't shrink at all. AUM below $100k is
omitted a fortiori: minimums already dominate there at lw 1 and lower gross
strictly worsens that end. The lw 1 column reproduces the capacity artifact's
rows (same computation — a built-in cross-check). Amounts are USD. **Trials
logged:** {n_trials} (`data/gross_sweep_registry.sqlite`).

## Net return per year (1× real costs)

{render_net_return_matrix(result)}

## The mechanism: margin drag (annualized, % of average NAV)

{render_margin_drag_matrix(result)}

At and below the 100% gross threshold (lw ≤ 0.5) margin does not halve — it
collapses. Trace amounts at lw 0.5 are real: whole-share rounding and NAV drift
nudge gross past NAV on scattered bars.

## Total drag (annualized, % of average NAV)

{render_total_drag_matrix(result)}

## Gross reference per column (0×, plain stack, $100M)

{gross_ref_table}

## The finding

{finding}

## Caveats

Inherited from the capacity analysis (D95): √-law participation boundary
(smaller books push it less — the low-lw columns are the model's comfort zone),
full-sample σ/ADV calibration (D66), retail margin/borrow rates held fixed,
whole-share rounding at small sizes. Program-level multiplicity (D90) now spans
five studies; any thin positive here is subject to it in full.

## Reproduction

`uv run python scripts/run_gross_sweep.py` — offline, deterministic. The margin
threshold collapse, ~linear spread scaling, and registry non-collision are
tested in `tests/integration/test_gross_sweep.py`.
"""
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(doc, encoding="utf-8")
    registry.close()

    print(render_net_return_matrix(result))
    print(f"\nwrote {RESULTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
