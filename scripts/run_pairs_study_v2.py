"""Pairs study v2 - cointegration-filtered selection (D92, D93).

One variable changed from v1: SELECTION. Gatev prefilter (top 50 of 1,596) ->
Engle-Granger beta with a [0.7, 1.3] coherence window (the strategy trades the 1:1
spread) -> ADF-statistic rank -> top 5. Trading, costs, windows, and every other
parameter are byte-identical to v1, so the v1->v2 delta is attributable to selection
alone.

Run: uv run python scripts/run_pairs_study_v2.py   (offline, deterministic)
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
RESULTS = REPO / "docs" / "results" / "pairs_study_v2.md"

CONFIG = StudyConfig()  # IDENTICAL to v1 - the study changes selection only
V1_RESULTS = {0.0: "+3.45%", 1.0: "-13.01%", 4.0: "-49.91%"}  # from pairs_study_v1.md


def main() -> int:
    bars, volumes = load_fixture_csv_with_volumes(FIXTURE)
    actions = load_events_json(EVENTS)

    cleaned, cleaning_report = clean(bars, volumes)
    validation = validate(cleaned, actions, volumes)
    store = SnapshotStore(REPO / "data" / "snapshots")
    snapshot_id = store.create(cleaned, actions, cleaning_report=cleaning_report, validation=validation,
                               extra_meta={"source_fixture": FIXTURE.name})
    snapshot = store.load(snapshot_id)

    registry = TrialRegistry(REPO / "data" / "pairs_study_v2_registry.sqlite")
    selector = CointegrationSelector(gatev_prefilter=50, beta_window=(0.7, 1.3), adf_lags=1)
    result = run_pairs_study(
        bars_by_symbol=snapshot.bars_by_symbol,
        volumes_by_symbol=volumes,
        actions=snapshot.actions,
        registry=registry,
        snapshot_id=snapshot_id,
        config=CONFIG,
        trial_id_prefix="pairs-study-v2",
        selector=selector,
    )

    spy = snapshot.bars_by_symbol[CONFIG.benchmark_symbol]
    spy_returns = {b.timestamp: b.bar.close / a.bar.close - 1.0 for a, b in zip(spy, spy[1:])}

    n_trials = result.n_windows * len(CONFIG.multipliers)
    doc = f"""# Pairs Study v2 — cointegration-filtered selection

**Date produced:** {datetime.now(timezone.utc).date().isoformat()} · **Snapshot:**
`{snapshot_id}` · **Universe/windows/trading: identical to
[v1](pairs_study_v1.md)** — one variable changed (D92): selection is now Gatev
prefilter (top {selector.gatev_prefilter} of {result.n_pairs_tested_per_window:,})
→ Engle-Granger β with a coherence window of {list(selector.beta_window)} (the
strategy trades the 1:1 spread, so β must be near 1) → ADF-statistic rank → top
{CONFIG.top_n}. β is logged per selected pair (informing a future β-hedged v3), not
traded. ADF statistic anchored against statsmodels (D93). **Trials logged:**
{n_trials} (`data/pairs_study_v2_registry.sqlite`).

## The sweep (D8)

{render_study_sweep_table(result)}

## v1 → v2 (selection is the only change)

| | v1 (Gatev only) | v2 (cointegration-filtered) |
|---|---|---|
| 0× | {V1_RESULTS[0.0]} | {(result.curves[0.0].final_nav / CONFIG.starting_cash - 1):+.2%} |
| 1× | {V1_RESULTS[1.0]} | {(result.curves[1.0].final_nav / CONFIG.starting_cash - 1):+.2%} |
| 4× | {V1_RESULTS[4.0]} | {(result.curves[4.0].final_nav / CONFIG.starting_cash - 1):+.2%} |

## Tearsheet at 1× (real costs)

{render_study_tearsheet(result, spy_returns)}

## Deflated Sharpe Ratio (D21/D86/D90)

- Observed stitched Sharpe (daily, rf {CONFIG.rf_annual:.0%}): {result.dsr_inputs["observed_sr_daily"]:.4f}
  over T = {result.dsr_inputs["t"]:,} OOS bars; skew {result.dsr_inputs["skew"]:.2f},
  kurtosis {result.dsr_inputs["kurt"]:.2f}.
- **DSR = {result.dsr:.4f}** — N and V pulled from this study's TrialRegistry.
- **Program-level multiplicity (D90, extended):** the research program has now run
  two studies of {n_trials} logged trials each, every window scoring
  {result.n_pairs_tested_per_window:,} candidates. Registry-N per study understates
  both the cross-study count and the selection breadth, so any DSR here is
  optimistic: DSR < 0.95 read as "no demonstrated edge" remains the only safe
  reading; a DSR ≥ 0.95 could not be taken at face value.

## Standing caveats

Unchanged from v1 (σ/ADV full-sample calibration D66; single-source data D26;
XLF-spinoff-as-split encoding D88). New in v2: ADF ranking uses a fixed lag order
({selector.adf_lags}) and the no-constant EG-residual convention — statistic-only,
no p-values, per D29's rank-don't-threshold rule (D93).

## Reproduction

`uv run python scripts/run_pairs_study_v2.py` — offline, deterministic. Selection
mechanics tested in `tests/unit/test_cointegration.py` (incl. exact statsmodels
ADF ties) and `tests/integration/test_pairs_study.py`.
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
