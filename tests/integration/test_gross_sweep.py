"""Integration tests for the gross exposure sweep (D96) on the synthetic universe.

The mechanism under test is the margin THRESHOLD: interest accrues on
max(gross − NAV, 0), so a book at gross ≤ NAV pays none — it collapses at the
boundary instead of scaling down. Linear frictions (spread) must meanwhile scale
roughly in proportion to leg_weight.
"""

import pytest
from test_pairs_study import CONFIG, _synthetic_universe

from backtest_framework.data.corporate_actions import CorporateActions
from backtest_framework.registry.trial_registry import TrialRegistry
from backtest_framework.research.gross_sweep import (
    render_margin_drag_matrix,
    render_net_return_matrix,
    run_gross_sweep,
)


@pytest.fixture(scope="module")
def sweep(tmp_path_factory):
    bars, volumes = _synthetic_universe()
    registry = TrialRegistry(tmp_path_factory.mktemp("gross") / "trials.sqlite")
    # CONFIG has top_n=3 with each pair's legs at ±lw of its capital slice, so
    # max book gross = 2·lw·NAV: lw 0.25 is safely BELOW the margin threshold,
    # lw 0.5 sits exactly AT it (rounding/NAV-drift can nudge gross past NAV on
    # some bars), lw 1.0 is well above it.
    result = run_gross_sweep(
        bars_by_symbol=bars,
        volumes_by_symbol=volumes,
        actions=CorporateActions(),
        registry=registry,
        snapshot_id="synthetic-universe",
        leg_weights=(0.25, 0.5, 1.0),
        aum_levels=(100_000.0,),
        config=CONFIG,
        selector_factory=lambda: None,  # default Gatev selection
        adv_by_symbol={s: 5e6 for s in bars},
    )
    return result, registry


def test_margin_interest_collapses_at_the_gross_threshold(sweep):
    result, _ = sweep
    below = result.by_leg_weight[0.25].levels[0]
    at_threshold = result.by_leg_weight[0.5].levels[0]
    above = result.by_leg_weight[1.0].levels[0]

    # Strictly below the threshold the base is NEVER positive - exactly zero.
    assert below.annualized_drag("MarginInterest") == 0.0
    assert above.annualized_drag("MarginInterest") > 0.0

    # AT the threshold: whole-share rounding and NAV drift nudge gross past NAV
    # on some bars, so drag is trace-positive - but it COLLAPSES (orders of
    # magnitude below lw 1.0), it does not halve as proportional scaling would.
    assert at_threshold.annualized_drag("MarginInterest") < 0.05 * above.annualized_drag("MarginInterest")


def test_linear_frictions_scale_roughly_with_leg_weight(sweep):
    result, _ = sweep
    small = result.by_leg_weight[0.5].levels[0].annualized_drag("PercentOfNotionalSpread")
    large = result.by_leg_weight[1.0].levels[0].annualized_drag("PercentOfNotionalSpread")
    # Turnover isn't exactly linear (rounding, NAV path feedback), hence the
    # loose band — the point is proportional-ish, NOT threshold behavior.
    assert large / small == pytest.approx(2.0, rel=0.35)


def test_leg_weight_runs_share_one_registry_without_collisions(sweep):
    result, registry = sweep
    assert registry.get_trial("gross-lw0.25-$100k-1.0x-w00") is not None
    assert registry.get_trial("gross-lw0.5-$100k-1.0x-w00") is not None
    assert registry.get_trial("gross-lw1-$100k-1.0x-w00") is not None
    n_windows = result.by_leg_weight[0.5].levels[0].study.n_windows
    assert len(registry.all_trials()) == 3 * n_windows  # 3 lws x 1 AUM x windows


def test_matrices_render_with_gross_labels(sweep):
    result, _ = sweep
    net = render_net_return_matrix(result)
    assert "lw 0.25 (gross 50%)" in net and "lw 1 (gross 200%)" in net
    assert "$100k" in net
    margin = render_margin_drag_matrix(result)
    assert "0.000%" in margin  # the below-threshold cell renders as exactly zero
