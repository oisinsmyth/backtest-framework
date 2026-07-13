"""Unit tests for declarative SimConfig + factories (D35), per VERIFICATION_SCHEME.md Step 2.

Covers: hash determinism across key ordering, factory-built objects behaving identically
to hand-constructed equivalents, and invalid configs failing loudly with the bad key named.
The fourth Step 2 gate (the full reproducibility loop) lives in
test_reproducibility_loop.py, since it also exercises TrialRegistry.
"""

from datetime import datetime

import pytest

from backtest_framework.config.carry_model import CARRY_MODEL_REGISTRY
from backtest_framework.config.errors import ConfigError
from backtest_framework.config.fill_model import FILL_MODEL_REGISTRY, FillModel
from backtest_framework.config.sim_config import build_sim_objects, validate_sim_config
from backtest_framework.costs.bricks import FlatRateCarry
from backtest_framework.registry.trial_registry import compute_trial_hash
from backtest_framework.simulator.fills import Bar, StopSide

VALID_CONFIG = {
    "carry_model": {"type": "act365", "annual_rate": 0.06},
    "fill_model": {"type": "stop_gap_aware", "stop_side": "sell_stop"},
}


# --- Gate 1: same config dict -> same hash, across runs and key orderings -------------


def test_same_config_same_hash_across_runs():
    h1 = compute_trial_hash(VALID_CONFIG, "snap-1", 42)
    h2 = compute_trial_hash(VALID_CONFIG, "snap-1", 42)
    assert h1 == h2


def test_same_config_same_hash_across_nested_key_reordering():
    reordered = {
        "fill_model": {"stop_side": "sell_stop", "type": "stop_gap_aware"},
        "carry_model": {"annual_rate": 0.06, "type": "act365"},
    }
    h1 = compute_trial_hash(VALID_CONFIG, "snap-1", 42)
    h2 = compute_trial_hash(reordered, "snap-1", 42)
    assert h1 == h2


def test_semantically_different_nested_config_changes_hash():
    changed = {
        "carry_model": {"type": "act365", "annual_rate": 0.05},  # different rate
        "fill_model": {"type": "stop_gap_aware", "stop_side": "sell_stop"},
    }
    assert compute_trial_hash(VALID_CONFIG, "snap-1", 42) != compute_trial_hash(changed, "snap-1", 42)


# --- Gate 2: factory-built objects behave identically to hand-constructed ones --------


def test_factory_built_carry_model_matches_hand_constructed():
    factory_built = CARRY_MODEL_REGISTRY.build({"type": "act365", "annual_rate": 0.06})
    hand_built = FlatRateCarry(annual_rate=0.06, day_count=365.0)

    prev, curr = datetime(2026, 7, 10, 16, 0), datetime(2026, 7, 13, 16, 0)
    assert factory_built.cost(100_000, prev, curr) == hand_built.cost(100_000, prev, curr)


def test_factory_built_fill_model_matches_hand_constructed():
    factory_built = FILL_MODEL_REGISTRY.build({"type": "stop_gap_aware", "stop_side": "sell_stop"})
    hand_built = FillModel(stop_side=StopSide.SELL_STOP)

    bar = Bar(open=38, high=39, low=37, close=38)
    assert factory_built.fill(45, bar) == hand_built.fill(45, bar)


def test_build_sim_objects_matches_hand_constructed_pair():
    objs = build_sim_objects(VALID_CONFIG)
    hand_carry = FlatRateCarry(annual_rate=0.06, day_count=365.0)
    hand_fill = FillModel(stop_side=StopSide.SELL_STOP)

    prev, curr = datetime(2026, 7, 10, 16, 0), datetime(2026, 7, 13, 16, 0)
    bar = Bar(open=38, high=39, low=37, close=38)
    assert objs.carry_model.cost(100_000, prev, curr) == hand_carry.cost(100_000, prev, curr)
    assert objs.fill_model.fill(45, bar) == hand_fill.fill(45, bar)


# --- Gate 3: invalid config fails loudly at factory time, naming the bad key ----------


def test_sim_config_missing_required_key_names_it():
    with pytest.raises(ConfigError, match="fill_model"):
        validate_sim_config({"carry_model": {"type": "act365", "annual_rate": 0.06}})


def test_sim_config_unknown_top_level_key_names_it():
    config = {**VALID_CONFIG, "bogus_extra_key": 123}
    with pytest.raises(ConfigError, match="bogus_extra_key"):
        validate_sim_config(config)


def test_sim_config_not_a_dict_fails_loudly():
    with pytest.raises(ConfigError, match="dict"):
        validate_sim_config(["not", "a", "dict"])  # type: ignore[arg-type]


def test_unknown_model_type_names_it_and_lists_known_types():
    with pytest.raises(ConfigError, match="bogus_type") as excinfo:
        CARRY_MODEL_REGISTRY.build({"type": "bogus_type", "annual_rate": 0.06})
    assert "act365" in str(excinfo.value)  # the known-types list is actually useful


def test_carry_model_missing_required_key_names_it():
    with pytest.raises(ConfigError, match="annual_rate"):
        CARRY_MODEL_REGISTRY.build({"type": "act365"})


def test_carry_model_wrong_type_names_the_bad_key():
    with pytest.raises(ConfigError, match="annual_rate"):
        CARRY_MODEL_REGISTRY.build({"type": "act365", "annual_rate": "six percent"})


def test_fill_model_invalid_stop_side_names_it_and_lists_allowed_values():
    with pytest.raises(ConfigError, match="stop_side") as excinfo:
        FILL_MODEL_REGISTRY.build({"type": "stop_gap_aware", "stop_side": "sideways"})
    assert "sell_stop" in str(excinfo.value) and "buy_stop" in str(excinfo.value)


def test_config_missing_type_key_names_it():
    with pytest.raises(ConfigError, match="'type'"):
        CARRY_MODEL_REGISTRY.build({"annual_rate": 0.06})
