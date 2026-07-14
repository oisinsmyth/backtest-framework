"""Pairs study v1 — THE FIRST PHASE G RESULT.

Full pipeline, offline and deterministic from the committed universe fixture:
fixture -> clean -> validate -> snapshot -> walk-forward Gatev selection (top 5 of
1,596 pairs per window) -> multi-strategy OOS runs through the real cost stack ->
0-4x sweep -> tearsheet -> registry-fed DSR -> docs/results/pairs_study_v1.md.

Run: uv run python scripts/run_pairs_study.py
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
from backtest_framework.research.pairs_study import (
    StudyConfig,
    render_study_sweep_table,
    render_study_tearsheet,
    run_pairs_study,
)

REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "data" / "fixtures" / "universe_daily_2015_2024_raw.csv.gz"
EVENTS = REPO / "data" / "fixtures" / "universe_daily_2015_2024_raw_events.json"
RESULTS = REPO / "docs" / "results" / "pairs_study_v1.md"

CONFIG = StudyConfig()  # the defaults ARE the study config; changes = new study version


def main() -> int:
    bars, volumes = load_fixture_csv_with_volumes(FIXTURE)
    actions = load_events_json(EVENTS)

    cleaned, cleaning_report = clean(bars, volumes)
    validation = validate(cleaned, actions, volumes)
    store = SnapshotStore(REPO / "data" / "snapshots")
    snapshot_id = store.create(
        cleaned, actions, cleaning_report=cleaning_report, validation=validation,
        extra_meta={"source_fixture": FIXTURE.name},
    )
    snapshot = store.load(snapshot_id)

    registry = TrialRegistry(REPO / "data" / "pairs_study_v1_registry.sqlite")
    result = run_pairs_study(
        bars_by_symbol=snapshot.bars_by_symbol,
        volumes_by_symbol=volumes,  # volumes ride outside the snapshot (D72 note)
        actions=snapshot.actions,
        registry=registry,
        snapshot_id=snapshot_id,
        config=CONFIG,
    )

    # SPY provider-frame daily returns for the beta row (D37).
    spy = snapshot.bars_by_symbol[CONFIG.benchmark_symbol]
    spy_returns = {
        b.timestamp: b.bar.close / a.bar.close - 1.0 for a, b in zip(spy, spy[1:])
    }

    warnings = [v for v in snapshot.meta["validation"]["violations"] if not v["hard"]]
    curve_1x = result.curves[1.0]
    doc = f"""# Pairs Study v1 — walk-forward Gatev/z-score over a 57-ETF universe

**Date produced:** {datetime.now(timezone.utc).date().isoformat()} · **Snapshot:**
`{snapshot_id}` (content-addressed, reproducible from the committed
`{FIXTURE.name}`) · **Universe:** 57 ETFs, 2015–2024 daily · **Windows:**
{result.n_windows} (train {CONFIG.train_size}, test {CONFIG.test_size}) ·
**Selection:** Gatev top-{CONFIG.top_n} of **{result.n_pairs_tested_per_window:,}
pairs per window** · **Trials logged:** {result.n_windows * len(CONFIG.multipliers)}
(`data/pairs_study_v1_registry.sqlite`).

The first Phase G research artifact. Pipeline provenance: cleaning made
{len(snapshot.meta["cleaning_report"]["changes"])} change(s); validation passed with
{len(warnings)} warning(s); 14 splits (incl. OIH 1-for-20, USO 1-for-8) and 2,285
dividends handled as events (D75).

## Strategy (study v1)

Z-score mean reversion on each selected pair (fixed 1:1 log-hedge, lookback
{CONFIG.lookback}, entry {CONFIG.entry_z}, exit {CONFIG.exit_z}, ±{CONFIG.leg_weight:.0%}
per leg), top-{CONFIG.top_n} pairs traded simultaneously in ONE portfolio per window —
shared legs net internally (D27). Windows chain: each starts with the previous
window's ending NAV. Cointegration tests and Kalman hedge ratios are future study
versions, deliberately not v1.

## The sweep (D8)

{render_study_sweep_table(result)}

## Tearsheet at 1× (real costs)

{render_study_tearsheet(result, spy_returns)}

## Deflated Sharpe Ratio (D21/D86/D90)

- Observed stitched Sharpe (daily, rf {CONFIG.rf_annual:.0%}): {result.dsr_inputs["observed_sr_daily"]:.4f}
  over T = {result.dsr_inputs["t"]:,} OOS bars; skew {result.dsr_inputs["skew"]:.2f},
  kurtosis {result.dsr_inputs["kurt"]:.2f}.
- **DSR = {result.dsr:.4f}** — N and V[{{SRn}}] pulled from this study's TrialRegistry,
  never typed in. N = {result.dsr_inputs["n_trials"]} one-per-window 1×-cost trials
  (a window re-run at a scaled cost multiplier is a sensitivity point, not an extra
  trial — D98); V is in daily units, matching the observed SR. All
  {result.n_windows * len(CONFIG.multipliers)} logged backtests stay in the registry.
- **Multiplicity caveat (D90):** registry-N counts logged backtests, but each window
  *scored {result.n_pairs_tested_per_window:,} candidate pairs* to pick its top
  {CONFIG.top_n} — selection breadth the registry-N does not capture, so even this
  DSR is optimistic. Interpreting DSR < 0.95 as "no demonstrated edge" is therefore
  conservative in the safe direction; interpreting DSR ≥ 0.95 would NOT be.

## Standing caveats (R3)

1. σ/ADV impact params are full-sample calibrated (D66) — documented look-ahead in
   cost parameters, not signal.
2. Single-source data (yfinance); event tables trusted after internal frame checks
   (D75); second-source cross-check remains deferred (D26).
3. Study v1 signal is the simplest honest one; richer signals are future versions.
4. XLF's 2016 "split" (ratio 1.231) is yfinance's encoding of the XLRE spin-off —
   handled mechanically as a split; economically approximate.

## Reproduction

`uv run python scripts/run_pairs_study.py` — offline, deterministic; recreates the
same content-addressed snapshot and identical numbers. Study mechanics are tested in
`tests/integration/test_pairs_study.py`.
"""
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(doc, encoding="utf-8")
    registry.close()

    print(f"snapshot: {snapshot_id}")
    print(render_study_sweep_table(result))
    print(f"DSR = {result.dsr:.4f}  (T={result.dsr_inputs['t']}, "
          f"SR_daily={result.dsr_inputs['observed_sr_daily']:.4f})")
    print(f"\nwrote {RESULTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
