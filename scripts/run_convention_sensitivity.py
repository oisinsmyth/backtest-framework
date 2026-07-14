"""Convention-sensitivity study (D105): how much of the v2 result is convention?

The audit (F3/F4) flagged the two optimistic conventions every published study
inherits: same-bar-close fills (the entry always catches exactly the close that
triggered the signal) and full-sample sqrt-impact calibration (a documented
look-ahead in cost parameters, D66). Both now have honest alternatives in the
framework (D102/D103). This study re-runs the v2 configuration — cointegration
selection, 1:1 hedge, identical windows and parameters — across the 2x2 of
conventions and publishes the deltas. One registry, one snapshot, four prefixes.

Run: uv run python scripts/run_convention_sensitivity.py   (offline, deterministic)
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from backtest_framework.data.cleaner import clean
from backtest_framework.data.corporate_actions import load_events_json
from backtest_framework.data.csv_fixture import load_fixture_csv_with_volumes
from backtest_framework.data.snapshot_store import SnapshotStore
from backtest_framework.data.validator import validate
from backtest_framework.registry.trial_registry import TrialRegistry
from backtest_framework.research.cointegration import CointegrationSelector
from backtest_framework.research.pairs_study import StudyConfig, run_pairs_study

REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "data" / "fixtures" / "universe_daily_2015_2024_raw.csv.gz"
EVENTS = REPO / "data" / "fixtures" / "universe_daily_2015_2024_raw_events.json"
RESULTS = REPO / "docs" / "results" / "convention_sensitivity.md"

# v2's config with the sweep cut to the two informative levels: 0x isolates the
# gross edge (fill timing bites here), 1x is the real-cost verdict. The published
# v2 artifact's 5-level sweep is the baseline anchor; per-multiplier chaining makes
# the shared levels byte-identical.
BASE = StudyConfig(multipliers=(0.0, 1.0))

VARIANTS = (
    ("baseline", BASE),
    ("next-open", replace(BASE, fill_timing="next_open")),
    ("train-cal", replace(BASE, impact_calibration="train_window")),
    ("both", replace(BASE, fill_timing="next_open", impact_calibration="train_window")),
)

V2_PUBLISHED = {0.0: "+19.03%", 1.0: "-6.43%"}  # from pairs_study_v2.md — anchor


def main() -> int:
    bars, volumes = load_fixture_csv_with_volumes(FIXTURE)
    actions = load_events_json(EVENTS)

    cleaned, cleaning_report = clean(bars, volumes)
    validation = validate(cleaned, actions, volumes)
    store = SnapshotStore(REPO / "data" / "snapshots")
    snapshot_id = store.create(cleaned, actions, cleaning_report=cleaning_report, validation=validation,
                               extra_meta={"source_fixture": FIXTURE.name})
    snapshot = store.load(snapshot_id)

    registry = TrialRegistry(REPO / "data" / "convention_sensitivity_registry.sqlite")
    results = {}
    for name, config in VARIANTS:
        results[name] = run_pairs_study(
            bars_by_symbol=snapshot.bars_by_symbol,
            volumes_by_symbol=volumes,
            actions=snapshot.actions,
            registry=registry,
            snapshot_id=snapshot_id,
            config=config,
            trial_id_prefix=f"conv-{name}",
            selector=CointegrationSelector(gatev_prefilter=50, beta_window=(0.7, 1.3), adf_lags=1),
        )
        print(f"{name}: 0x {results[name].curves[0.0].final_nav / config.starting_cash - 1:+.2%}  "
              f"1x {results[name].curves[1.0].final_nav / config.starting_cash - 1:+.2%}  "
              f"DSR {results[name].dsr:.4f}")

    def ret(name: str, m: float) -> float:
        return results[name].curves[m].final_nav / BASE.starting_cash - 1.0

    rows = "\n".join(
        f"| {name} | {'close' if config.fill_timing == 'close' else 'next open'} | "
        f"{config.impact_calibration.replace('_', ' ')} | {ret(name, 0.0):+.2%} | {ret(name, 1.0):+.2%} | "
        f"{results[name].dsr:.4f} |"
        for name, config in VARIANTS
    )

    doc = f"""# Convention sensitivity — how much of the v2 result is convention? (D105)

**Date produced:** {datetime.now(timezone.utc).date().isoformat()} · **Snapshot:**
`{snapshot_id}` · **Configuration: identical to [v2](pairs_study_v2.md)**
(cointegration selection, 1:1 hedge, same windows/parameters) — only the two
execution/calibration conventions vary. **Trials logged:**
{sum(r.n_windows * 2 for r in results.values())}
(`data/convention_sensitivity_registry.sqlite`). Baseline anchor: the published
v2 artifact reports {V2_PUBLISHED[0.0]} at 0× and {V2_PUBLISHED[1.0]} at 1×.

## Why this study exists (audit F3/F4)

Every study through v3 fills orders at the close of the bar that generated the
signal — optimistic for mean reversion, since the entry always catches exactly
the close that triggered it — and calibrates sqrt-impact σ/ADV on the full
sample (a documented look-ahead in cost parameters, D66, never in the signal).
D103/D102 added the honest alternatives: next-bar-open fills and per-window
train-slice calibration. This study prices both conventions on the program's
strongest configuration, per the house one-variable-per-study rule.

## The 2×2

| Variant | Fill timing | Impact calibration | 0× return | 1× return | DSR |
|---|---|---|---|---|---|
{rows}

Reading: the **0× column at next-open prices the fill-timing convention alone**
(no costs, so calibration is irrelevant at 0× — the train-cal 0× row must equal
the baseline 0× row, a built-in cross-check). The **1× rows price the full
stack** under each convention pair; "both" is the fully-conservative cell.

## Interpretation rule (D90/D98)

Per-variant DSRs are computed over each variant's own 1× window trials (N =
{results["baseline"].dsr_inputs["n_trials"]} per variant, daily units). The
program-level multiplicity caveat applies unchanged: DSR < 0.95 read as "no
demonstrated edge" is the only safe reading.

## Reproduction

`uv run python scripts/run_convention_sensitivity.py` — offline, deterministic.
Engine fill-timing semantics are gate-tested (`test_backtest_loop.py`,
`test_simulator_invariants.py`, D103); per-window calibration leak-freedom is
gate-tested (`test_pairs_study.py`, D102).
"""
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(doc, encoding="utf-8")
    registry.close()
    print(f"\nwrote {RESULTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
