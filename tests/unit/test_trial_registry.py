"""Unit tests for TrialRegistry (D20), per VERIFICATION_SCHEME.md Step 1."""

import pytest

from backtest_framework.registry.trial_registry import (
    TrialAlreadyExistsError,
    TrialRegistry,
    compute_trial_hash,
)


def _sample_trial(trial_id="trial-001"):
    return dict(
        trial_id=trial_id,
        config={"cost_model": "ibkr_v1", "fill_assumption": "touch"},
        params={"lookback": 20, "entry_z": 2.0},
        metrics={"sharpe": 1.23, "max_drawdown": -0.08},
        snapshot_id="snap-2026-07-13",
        seed=42,
    )


def test_write_read_roundtrip_preserves_everything(tmp_path):
    registry = TrialRegistry(tmp_path / "trials.sqlite")
    kwargs = _sample_trial()
    trial_hash = registry.add_trial(**kwargs)

    record = registry.get_trial(kwargs["trial_id"])
    assert record.trial_id == kwargs["trial_id"]
    assert record.config == kwargs["config"]
    assert record.params == kwargs["params"]
    assert record.metrics == kwargs["metrics"]
    assert record.snapshot_id == kwargs["snapshot_id"]
    assert record.seed == kwargs["seed"]
    assert record.trial_hash == trial_hash


def test_registry_is_append_only(tmp_path):
    registry = TrialRegistry(tmp_path / "trials.sqlite")
    kwargs = _sample_trial()
    registry.add_trial(**kwargs)

    with pytest.raises(TrialAlreadyExistsError):
        registry.add_trial(**kwargs)

    # The original row must be untouched, not silently overwritten.
    assert len(registry) == 1


def test_registry_survives_process_restart(tmp_path):
    db_path = tmp_path / "trials.sqlite"

    registry = TrialRegistry(db_path)
    registry.add_trial(**_sample_trial("trial-001"))
    registry.close()  # simulate the process ending

    reopened = TrialRegistry(db_path)  # simulate a fresh process starting
    assert len(reopened) == 1
    record = reopened.get_trial("trial-001")
    assert record.config == _sample_trial("trial-001")["config"]


def test_identical_inputs_produce_identical_hash():
    kwargs = _sample_trial()
    h1 = compute_trial_hash(kwargs["config"], kwargs["snapshot_id"], kwargs["seed"])
    h2 = compute_trial_hash(kwargs["config"], kwargs["snapshot_id"], kwargs["seed"])
    assert h1 == h2


def test_identical_config_different_key_order_produces_identical_hash():
    config_a = {"cost_model": "ibkr_v1", "fill_assumption": "touch"}
    config_b = {"fill_assumption": "touch", "cost_model": "ibkr_v1"}
    h1 = compute_trial_hash(config_a, "snap-1", 42)
    h2 = compute_trial_hash(config_b, "snap-1", 42)
    assert h1 == h2


@pytest.mark.parametrize(
    "mutate",
    [
        lambda k: k.__setitem__("config", {**k["config"], "fill_assumption": "trade_through"}),
        lambda k: k.__setitem__("snapshot_id", "snap-2026-07-14"),
        lambda k: k.__setitem__("seed", 43),
    ],
    ids=["config_change", "snapshot_change", "seed_change"],
)
def test_any_semantic_change_produces_different_hash(mutate):
    kwargs = _sample_trial()
    original_hash = compute_trial_hash(kwargs["config"], kwargs["snapshot_id"], kwargs["seed"])

    mutate(kwargs)
    changed_hash = compute_trial_hash(kwargs["config"], kwargs["snapshot_id"], kwargs["seed"])

    assert changed_hash != original_hash
