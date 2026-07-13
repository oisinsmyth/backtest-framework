"""The Step 2 headline gate: config -> hash -> registry -> reload -> re-run reproduces
the original result. This is also the Phase A milestone in DEVELOPMENT_TIMETABLE.md
("the reproducibility loop closes — a trial can be logged, reloaded, and re-run
identically").
"""

from datetime import datetime

from backtest_framework.config.sim_config import build_sim_objects
from backtest_framework.registry.trial_registry import TrialRegistry, compute_trial_hash
from backtest_framework.simulator.fills import Bar

CONFIG = {
    "carry_model": {"type": "act365", "annual_rate": 0.06},
    "fill_model": {"type": "stop_gap_aware", "stop_side": "sell_stop"},
}
SNAPSHOT_ID = "snap-2026-07-13"
SEED = 42

PREV, CURR = datetime(2026, 7, 10, 16, 0), datetime(2026, 7, 13, 16, 0)
BAR = Bar(open=38, high=39, low=37, close=38)


def _run(config: dict) -> dict:
    """Stand-in for "run a backtest": build live objects from config, exercise them
    against a fixed scenario, return the results as if they were headline metrics."""
    objs = build_sim_objects(config)
    return {
        "carry_accrued": objs.carry_model.accrue(100_000, PREV, CURR),
        "stop_fill_price": objs.fill_model.fill(45, BAR),
    }


def test_full_reproducibility_loop(tmp_path):
    # 1. Run once, log the trial.
    original_metrics = _run(CONFIG)
    registry = TrialRegistry(tmp_path / "trials.sqlite")
    trial_hash = registry.add_trial(
        trial_id="trial-001",
        config=CONFIG,
        params={},
        metrics=original_metrics,
        snapshot_id=SNAPSHOT_ID,
        seed=SEED,
    )
    registry.close()

    # 2. Simulate a fresh process: reopen the registry, reload the trial.
    reopened = TrialRegistry(tmp_path / "trials.sqlite")
    record = reopened.get_trial("trial-001")

    # The hash reloaded from disk matches the one computed at write time...
    assert record.trial_hash == trial_hash
    # ...and independently recomputing it from the reloaded fields matches too.
    assert compute_trial_hash(record.config, record.snapshot_id, record.seed) == trial_hash

    # 3. Re-run from the reloaded config alone.
    rerun_metrics = _run(record.config)

    # 4. Reproduces the original result exactly, including the logged metrics.
    assert rerun_metrics == original_metrics
    assert record.metrics == original_metrics
