"""Integration tests for the capacity study (D95) on the synthetic universe.

Two properties carry the design: the recorder must be invisible to the run it
attributes (identity), and the size-aware bricks must produce the two-sided
capacity story (direction — commission minimums bind small, √-impact binds large).
"""

import pytest
from test_pairs_study import CONFIG, _synthetic_universe

from backtest_framework.data.corporate_actions import CorporateActions
from backtest_framework.registry.trial_registry import TrialRegistry
from backtest_framework.research.capacity import (
    recording_cost_stack,
    run_capacity_study,
)
from backtest_framework.research.pairs_study import build_base_cost_stack, run_pairs_study


def test_recorded_run_is_identical_to_the_default_path(tmp_path):
    # The transparency identity (D95): injecting a recording wrap of the SAME base
    # stack must reproduce the default run's equity curves exactly — attribution
    # never perturbs what it attributes. Also locks the base_stack=None contract.
    bars, volumes = _synthetic_universe()

    default_result = run_pairs_study(
        bars_by_symbol=bars,
        volumes_by_symbol=volumes,
        actions=CorporateActions(),
        registry=TrialRegistry(tmp_path / "default.sqlite"),
        snapshot_id="synthetic-universe",
        config=CONFIG,
        trial_id_prefix="cap-default",
    )

    recorded_stack, ledger = recording_cost_stack(
        build_base_cost_stack(bars, volumes, CorporateActions())
    )
    recorded_result = run_pairs_study(
        bars_by_symbol=bars,
        volumes_by_symbol=volumes,
        actions=CorporateActions(),
        registry=TrialRegistry(tmp_path / "recorded.sqlite"),
        snapshot_id="synthetic-universe",
        config=CONFIG,
        trial_id_prefix="cap-recorded",
        base_stack=recorded_stack,
    )

    for m in CONFIG.multipliers:
        assert recorded_result.curves[m].equity == default_result.curves[m].equity
    assert ledger.totals  # and the ledger actually saw the charges


def test_commission_binds_small_and_impact_binds_large(tmp_path):
    # The two-sided capacity story, measured: at $20k the $1/order minimum is a
    # visible fraction of NAV; at $10M it vanishes while sqrt-impact grows.
    bars, volumes = _synthetic_universe()
    registry = TrialRegistry(tmp_path / "capacity.sqlite")

    result = run_capacity_study(
        bars_by_symbol=bars,
        volumes_by_symbol=volumes,
        actions=CorporateActions(),
        registry=registry,
        snapshot_id="synthetic-universe",
        aum_levels=(20_000.0, 10_000_000.0),
        config=CONFIG,
        selector_factory=lambda: None,  # default Gatev selection
        adv_by_symbol={s: 5e6 for s in bars},
    )

    small, large = result.levels
    assert small.label == "$20k" and large.label == "$10M"

    # Commission drag (as % of NAV/yr) strictly higher at the small level...
    assert small.annualized_drag("IBKRCommission") > large.annualized_drag("IBKRCommission")
    # ...impact drag and participation strictly higher at the large level.
    assert large.annualized_drag("SqrtImpact") > small.annualized_drag("SqrtImpact")
    assert large.max_participation > small.max_participation

    # Trials landed in the shared registry under per-level prefixes.
    assert registry.get_trial("capacity-$20k-1.0x-w00") is not None
    assert registry.get_trial("capacity-$10M-1.0x-w00") is not None

    # Scale-invariant bricks are within the same order of magnitude across levels
    # (rounding aside) — the drag DIFFERENCE comes from the size-aware bricks.
    small_spread = small.annualized_drag("PercentOfNotionalSpread")
    large_spread = large.annualized_drag("PercentOfNotionalSpread")
    assert small_spread == pytest.approx(large_spread, rel=0.5)
