"""Pairs study v3 - beta-hedged trading (D94).

One variable changed from v2: TRADING. Selection is v2's CointegrationSelector,
byte-identical (Gatev prefilter 50 -> Engle-Granger beta in [0.7, 1.3] -> ADF rank
-> top 5). What changes: each pair now TRADES its train-window-fitted beta —
spread = ln A − β·ln B, legs sized in the β ratio, weights normalized to constant
gross 2·leg_weight (D94) so risk stays comparable with v1/v2. The v2->v3 delta is
attributable to the hedge alone.

Run: uv run python scripts/run_pairs_study_v3.py   (offline, deterministic)
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from backtest_framework.data.cleaner import clean
from backtest_framework.data.corporate_actions import load_events_json
from backtest_framework.data.csv_fixture import load_fixture_csv_with_volumes
from backtest_framework.data.snapshot_store import SnapshotStore
from backtest_framework.data.validator import validate
from backtest_framework.registry.trial_registry import TrialRegistry
from backtest_framework.research.beta_zscore import BetaHedgedZScoreStrategy
from backtest_framework.research.cointegration import CointegrationSelector
from backtest_framework.research.pairs_study import (
    StudyConfig,
    render_study_sweep_table,
    render_study_tearsheet,
    run_pairs_study,
)

REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "data" / "fixtures" / "universe_daily_2015_2024_raw.csv.gz"
EVENTS = REPO / "data" / "fixtures" / "universe_daily_2015_2024_raw_events.json"
RESULTS = REPO / "docs" / "results" / "pairs_study_v3.md"

CONFIG = StudyConfig()  # IDENTICAL to v1/v2 - the study changes trading only
V1_RESULTS = {0.0: "+3.45%", 0.5: "-5.01%", 1.0: "-13.01%", 4.0: "-49.91%"}  # pairs_study_v1.md
V2_RESULTS = {0.0: "+19.03%", 0.5: "+5.70%", 1.0: "-6.43%", 4.0: "-56.81%"}  # pairs_study_v2.md


def beta_hedged_factory(pair, strategy_id, config, details):
    """v3's strategy_factory (D94): trade the selector's fitted beta."""
    return BetaHedgedZScoreStrategy(
        strategy_id=strategy_id,
        instrument_a=pair[0],
        instrument_b=pair[1],
        hedge_beta=details["beta"],
        lookback=config.lookback,
        entry_z=config.entry_z,
        exit_z=config.exit_z,
        leg_weight=config.leg_weight,
    )


def main() -> int:
    bars, volumes = load_fixture_csv_with_volumes(FIXTURE)
    actions = load_events_json(EVENTS)

    cleaned, cleaning_report = clean(bars, volumes)
    validation = validate(cleaned, actions, volumes)
    store = SnapshotStore(REPO / "data" / "snapshots")
    snapshot_id = store.create(cleaned, actions, cleaning_report=cleaning_report, validation=validation,
                               extra_meta={"source_fixture": FIXTURE.name})
    snapshot = store.load(snapshot_id)

    registry = TrialRegistry(REPO / "data" / "pairs_study_v3_registry.sqlite")
    selector = CointegrationSelector(gatev_prefilter=50, beta_window=(0.7, 1.3), adf_lags=1)
    result = run_pairs_study(
        bars_by_symbol=snapshot.bars_by_symbol,
        volumes_by_symbol=volumes,
        actions=snapshot.actions,
        registry=registry,
        snapshot_id=snapshot_id,
        config=CONFIG,
        trial_id_prefix="pairs-study-v3",
        selector=selector,
        strategy_factory=beta_hedged_factory,
    )

    spy = snapshot.bars_by_symbol[CONFIG.benchmark_symbol]
    spy_returns = {b.timestamp: b.bar.close / a.bar.close - 1.0 for a, b in zip(spy, spy[1:])}

    n_trials = result.n_windows * len(CONFIG.multipliers)
    doc = f"""# Pairs Study v3 — β-hedged trading

**Date produced:** {datetime.now(timezone.utc).date().isoformat()} · **Snapshot:**
`{snapshot_id}` · **Universe/windows/selection: identical to
[v2](pairs_study_v2.md)** — one variable changed (D94): each pair now TRADES its
train-window Engle-Granger β instead of the fixed 1:1 hedge. Spread = ln A − β·ln B;
legs sized in the β ratio with weights normalized to constant gross
2·leg_weight = {2 * CONFIG.leg_weight:g} (w_A = 2w/(1+β), w_B = 2wβ/(1+β)), so
gross exposure — and therefore the risk being compared — matches v1/v2 exactly.
β = 1 provably reduces to v1/v2's strategy (tested identity). **Trials logged:**
{n_trials} (`data/pairs_study_v3_registry.sqlite`).

## The sweep (D8)

{render_study_sweep_table(result)}

## v1 → v2 → v3 (one variable per step)

| | v1 (Gatev, 1:1 hedge) | v2 (coint. selection, 1:1 hedge) | v3 (coint. selection, β hedge) |
|---|---|---|---|
| 0× | {V1_RESULTS[0.0]} | {V2_RESULTS[0.0]} | {(result.curves[0.0].final_nav / CONFIG.starting_cash - 1):+.2%} |
| 0.5× | {V1_RESULTS[0.5]} | {V2_RESULTS[0.5]} | {(result.curves[0.5].final_nav / CONFIG.starting_cash - 1):+.2%} |
| 1× | {V1_RESULTS[1.0]} | {V2_RESULTS[1.0]} | {(result.curves[1.0].final_nav / CONFIG.starting_cash - 1):+.2%} |
| 4× | {V1_RESULTS[4.0]} | {V2_RESULTS[4.0]} | {(result.curves[4.0].final_nav / CONFIG.starting_cash - 1):+.2%} |

v1→v2 isolated selection; v2→v3 isolates the hedge. The measurement: whether
trading the fitted β beats trading 1:1 on the same pairs — β estimation noise is
part of that measurement, not a confound (the fit is honest train-window-only,
applied out-of-sample, D22).

**Finding: β-hedging hurt, at every cost level.** Gross falls from v2's +19.03%
to {(result.curves[0.0].final_nav / CONFIG.starting_cash - 1):+.2%}; at real costs the loss deepens from −6.43% to
{(result.curves[1.0].final_nav / CONFIG.starting_cash - 1):+.2%}. Since selection, windows, costs, and gross exposure are all held
fixed, the delta prices exactly one thing: a train-window β carried out-of-sample
is noisier than it is helpful on this universe. The pairs the selector admits
already have β ≈ 1 (the [0.7, 1.3] coherence window), so the hedge's room for
benefit was small by construction, while the estimation error it imports is not.
The 1:1 hedge is the better trade here — an estimation-error result, and a real
finding for the Phase G writeup, not a failure of the study.

## Tearsheet at 1× (real costs)

{render_study_tearsheet(result, spy_returns)}

## Deflated Sharpe Ratio (D21/D86/D90)

- Observed stitched Sharpe (daily, rf {CONFIG.rf_annual:.0%}): {result.dsr_inputs["observed_sr_daily"]:.4f}
  over T = {result.dsr_inputs["t"]:,} OOS bars; skew {result.dsr_inputs["skew"]:.2f},
  kurtosis {result.dsr_inputs["kurt"]:.2f}.
- **DSR = {result.dsr:.4f}** — N and V pulled from this study's TrialRegistry.
- **Program-level multiplicity (D90, extended):** the research program has now run
  THREE studies of {n_trials} logged trials each, every window scoring
  {result.n_pairs_tested_per_window:,} candidates. Registry-N per study understates
  both the cross-study count and the selection breadth, so any DSR here is
  optimistic: DSR < 0.95 read as "no demonstrated edge" remains the only safe
  reading; a DSR ≥ 0.95 could not be taken at face value.

## Standing caveats

Unchanged from v2 (σ/ADV full-sample calibration D66; single-source data D26;
XLF-spinoff-as-split encoding D88; fixed-lag no-constant ADF rank D93). New in v3:
β is a fitted parameter carried out-of-sample per window — its estimation error is
part of the strategy, and the v2→v3 delta prices exactly that trade-off (D94).

## Reproduction

`uv run python scripts/run_pairs_study_v3.py` — offline, deterministic. Strategy
mechanics tested in `tests/unit/test_beta_zscore.py` (incl. the β=1 → v2-strategy
identity); the factory wiring and the β=1 whole-study equivalence in
`tests/integration/test_pairs_study.py`.
"""
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(doc, encoding="utf-8")
    registry.close()

    print(f"snapshot: {snapshot_id[:16]}...")
    print(render_study_sweep_table(result))
    print(f"DSR = {result.dsr:.4f}  (T={result.dsr_inputs['t']}, "
          f"SR_daily={result.dsr_inputs['observed_sr_daily']:.4f})")
    print(f"\nwrote {RESULTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
