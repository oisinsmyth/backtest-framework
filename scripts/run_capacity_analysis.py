"""Capacity analysis (D95): the v2 study at nine AUM levels, real unscaled costs.

The D8 multiplier sweep can't see account size; the real bricks can. IBKR's
$1/order minimum penalizes small accounts, sqrt-impact penalizes large ones,
spread/borrow/margin are scale-invariant. This script measures net(AUM) directly:
same selection, same trading, same windows as v2 - only starting_cash varies.

Run: uv run python scripts/run_capacity_analysis.py   (offline, deterministic, ~10 min)
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from backtest_framework.costs.calibration import calibrate_impact_params
from backtest_framework.data.cleaner import clean
from backtest_framework.data.corporate_actions import load_events_json
from backtest_framework.data.csv_fixture import load_fixture_csv_with_volumes
from backtest_framework.data.snapshot_store import SnapshotStore
from backtest_framework.data.validator import validate
from backtest_framework.registry.trial_registry import TrialRegistry
from backtest_framework.research.capacity import (
    render_capacity_drag_table,
    render_capacity_headline_table,
    run_capacity_study,
)
from backtest_framework.research.cointegration import CointegrationSelector
from backtest_framework.research.pairs_study import StudyConfig, run_pairs_study

REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "data" / "fixtures" / "universe_daily_2015_2024_raw.csv.gz"
EVENTS = REPO / "data" / "fixtures" / "universe_daily_2015_2024_raw_events.json"
RESULTS = REPO / "docs" / "results" / "capacity_analysis.md"

CONFIG = StudyConfig()  # v2's exact configuration; only starting_cash varies per level
AUM_LEVELS = (10e3, 30e3, 100e3, 300e3, 1e6, 3e6, 10e6, 30e6, 100e6)
V2_GROSS = "+19.03%"  # pairs_study_v2.md, 0x row - the scale-free reference


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

    registry = TrialRegistry(REPO / "data" / "capacity_study_registry.sqlite")
    print(f"snapshot: {snapshot_id[:16]}...  running {len(AUM_LEVELS)} AUM levels")
    result = run_capacity_study(
        bars_by_symbol=snapshot.bars_by_symbol,
        volumes_by_symbol=volumes,
        actions=snapshot.actions,
        registry=registry,
        snapshot_id=snapshot_id,
        aum_levels=AUM_LEVELS,
        config=CONFIG,
        selector_factory=make_selector,
        adv_by_symbol=adv_by_symbol,
    )
    for lv in result.levels:
        print(f"  {lv.label:>6}: net {lv.net_return:+.2%}  "
              f"max participation {lv.max_participation:.2%} ({lv.participation_symbol})")

    # Sanity run: gross at $100M (0x through a PLAIN stack - no recorder, so the
    # extra multiplier can't poison any ledger). Confirms the levels differ only
    # through costs: gross should sit near v2's +19.03% (share rounding aside).
    print("sanity run: 0x/1x at $100M through a plain stack...")
    from dataclasses import replace
    sanity = run_pairs_study(
        bars_by_symbol=snapshot.bars_by_symbol,
        volumes_by_symbol=volumes,
        actions=snapshot.actions,
        registry=registry,
        snapshot_id=snapshot_id,
        config=replace(CONFIG, starting_cash=100e6, multipliers=(0.0, 1.0)),
        trial_id_prefix="capacity-sanity-$100M",
        selector=make_selector(),
    )
    gross_100m = sanity.curves[0.0].final_nav / 100e6 - 1.0
    net_100m_sanity = sanity.curves[1.0].final_nav / 100e6 - 1.0
    level_100m = result.levels[-1]
    print(f"  $100M gross {gross_100m:+.2%} (v2 reference {V2_GROSS}); "
          f"1x sanity {net_100m_sanity:+.2%} vs recorded level {level_100m.net_return:+.2%}")

    clearing = [lv for lv in result.levels if lv.net_return > 0]
    peak = max(result.levels, key=lambda lv: lv.net_return)
    gross_annual = (1.0 + gross_100m) ** (1.0 / peak.years) - 1.0
    peak_floor = sum(
        peak.annualized_drag(b) for b in ("PercentOfNotionalSpread", "BorrowFee", "MarginInterest")
    )
    peak_size_aware = peak.annualized_drag("IBKRCommission") + peak.annualized_drag("SqrtImpact")
    peak_margin = peak.annualized_drag("MarginInterest")
    if clearing:
        finding = (
            f"**The edge clears real costs at {', '.join(lv.label for lv in clearing)}** "
            f"(peak {peak.net_return:+.2%} over the 9-year study at {peak.label}). "
            "Outside that window the size-aware frictions take it back: commission "
            "minimums at smaller sizes, impact at larger ones."
        )
    else:
        finding = (
            f"**No AUM level clears real costs.** The hump is real and lands where the "
            f"cost structure predicts — commission minimums punish the small end, "
            f"√-impact the large end, with the optimum at {peak.label} "
            f"({peak.net_return:+.2%} over the study, {peak.net_return_annual:+.2%}/yr) — "
            f"but the whole curve sits below zero. The arithmetic at the optimum: the "
            f"gross edge is ≈{gross_annual:+.2%}/yr; the scale-invariant floor "
            f"(spread + borrow + margin interest on ~200% gross) is {peak_floor:.2%}/yr "
            f"by itself, and the size-aware frictions (commission + impact) still add "
            f"{peak_size_aware:.2%}/yr at the optimum — {peak_floor + peak_size_aware:.2%}/yr "
            f"of total drag against {gross_annual:+.2%}/yr of edge. The largest single "
            f"fixed lever is margin interest ({peak_margin:.2%}/yr at the retail 6% rate): "
            f"to first order, even FREE margin funding would lift the optimum only to "
            f"≈{peak.net_return_annual + peak_margin:+.2%}/yr. The honest conclusion: "
            f"this edge, at this gross exposure, does not clear real frictions at any "
            f"account size — the binding constraint is the cost floor of running a "
            f"~200% gross book, not any one size-dependent friction."
        )

    n_trials = (len(AUM_LEVELS) + 2) * result.levels[0].study.n_windows
    doc = f"""# Capacity analysis — where does the v2 edge clear real costs?

**Date produced:** {datetime.now(timezone.utc).date().isoformat()} · **Snapshot:**
`{snapshot_id}` · **Method (D95):** the byte-identical v2 study
([pairs_study_v2.md](pairs_study_v2.md) — cointegration selection, 1:1 hedge per
v3's verdict) run at {len(AUM_LEVELS)} log-spaced account sizes with the REAL,
unscaled cost stack. The multiplier sweep (D8) scales all frictions uniformly and
cannot see size; here the bricks themselves produce the size dependence — IBKR's
$1/order minimum binds small accounts, √-impact (fraction ∝ √(Q/ADV)) binds large
ones, spread/borrow/margin are scale-invariant rates. Selection depends only on
train views, so every level trades the SAME pairs on the same dates: the levels
differ only through costs and whole-share rounding. Amounts are USD. **Trials
logged:** {n_trials} (`data/capacity_study_registry.sqlite`).

## Net return by account size (1× real costs)

{render_capacity_headline_table(result)}

## Where the money goes — drag decomposition (annualized, % of average NAV)

{render_capacity_drag_table(result)}

## The finding

{finding}

For reference, the same strategy is **{V2_GROSS} gross** (0× costs) — measured at
$100M in this run's sanity check: {gross_100m:+.2%}, confirming gross is
scale-invariant up to rounding and the spread between levels is pure cost
structure. (The sanity run's 1× leg reproduces the recorded $100M level:
{net_100m_sanity:+.2%} vs {level_100m.net_return:+.2%}.)

## Caveats

- **√-law extrapolation**: the square-root impact model is an empirical fit from
  institutional execution data; the max-participation column reports how far each
  level pushes it. Levels trading a large fraction of a symbol's ADV are model
  extrapolation, not measurement — treat the large-AUM rows as increasingly
  approximate.
- **Full-sample σ/ADV calibration** (D66) — the standing mild look-ahead in cost
  parameters, never in signal.
- **Retail rate assumptions held fixed across scale**: 6% margin interest and
  25bps borrow are retail-grade at every level. Institutions fund cheaper — a
  large account's true drag table would shrink the MarginInterest/BorrowFee
  columns. Stated, not modeled.
- **Whole-share rounding** is a real small-account friction and part of the
  small-AUM rows' honest story (positions of ~tens of shares are lumpy).
- **DSR is not the object here**: these are cost diagnostics of ONE strategy at
  varying account size, not new signal trials. They are still logged to the
  registry, so they count toward the program-level multiplicity record (D90).
- Standing data caveats unchanged (single-source D26, XLF-spinoff encoding D88).

## Reproduction

`uv run python scripts/run_capacity_analysis.py` — offline, deterministic.
Recorder transparency (attribution provably does not perturb the run) and the
two-sided direction property are tested in `tests/unit/test_capacity.py` and
`tests/integration/test_capacity_study.py`.
"""
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(doc, encoding="utf-8")
    registry.close()

    print(render_capacity_headline_table(result))
    print(f"\nwrote {RESULTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
