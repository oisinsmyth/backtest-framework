"""Unit tests for `validation/filter_oracle.py` (D690): the oracle filter and the accuracy assessment.

Each statistic is pinned on an input whose answer is known in closed form (a perfect score, a reversed one, a constant
one, hand-counted ties), and every guard the module promises is shown to raise. Nothing here reads a market fixture.
"""
from __future__ import annotations

import numpy as np
import pytest

from backtest_framework.validation.filter_oracle import (
    FilterOracleError,
    assess,
    auc,
    average_ranks,
    calibration,
    capture,
    confusion,
    normal_scores,
    oracle_take,
    oracle_take_threshold,
    partial_oracle_curve,
    partial_oracle_score,
    spearman,
    top_fraction,
)


def test_average_ranks_average_the_ties():
    assert average_ranks([10, 20, 20, 5]).tolist() == [2.0, 3.5, 3.5, 1.0]
    assert average_ranks([7, 7, 7]).tolist() == [2.0, 2.0, 2.0]


def test_spearman_is_one_for_any_monotone_map_and_minus_one_reversed():
    x = np.arange(50.0)
    assert spearman(x, np.exp(x / 10)) == pytest.approx(1.0)
    assert spearman(x, -x ** 3) == pytest.approx(-1.0)


def test_auc_perfect_reversed_and_tied():
    lab = np.array([False, False, True, True])
    assert auc([0.1, 0.2, 0.8, 0.9], lab) == pytest.approx(1.0)
    assert auc([0.9, 0.8, 0.2, 0.1], lab) == pytest.approx(0.0)
    assert auc([0.5, 0.5, 0.5, 0.5], lab) == pytest.approx(0.5)      # ties count half


def test_normal_scores_are_symmetric_and_rank_preserving():
    z = normal_scores([3.0, 1.0, 2.0])
    assert z[1] < z[2] < z[0]
    assert z[2] == pytest.approx(0.0, abs=1e-12)
    assert z[0] == pytest.approx(-z[1])


def test_the_oracle_takes_exactly_the_winners_and_captures_all_of_them():
    net = np.array([5.0, -3.0, 0.0, 2.0, -1.0])
    take = oracle_take(net)
    assert take.tolist() == [True, False, False, True, False]
    c = capture(net, take)
    assert c["capture_of_oracle"] == pytest.approx(1.0)
    assert c["oracle_net"] == 7.0 and c["take_all_net"] == 3.0
    cf = confusion(take, net > 0)
    assert cf["precision"] == 1.0 and cf["recall"] == 1.0 and cf["balanced_accuracy"] == 1.0


def test_oracle_threshold_is_the_template_bar():
    assert oracle_take_threshold([10.0, 8.84, 8.83], cost=4.42, k=2.0).tolist() == [True, True, False]
    with pytest.raises(FilterOracleError):
        oracle_take_threshold([1.0], cost=-1.0)


def test_confusion_counts_by_hand():
    take = np.array([True, True, False, False, True])
    lab = np.array([True, False, True, False, False])
    c = confusion(take, lab)
    assert (c["tp"], c["fp"], c["fn"], c["tn"]) == (1, 2, 1, 1)
    assert c["precision"] == pytest.approx(1 / 3) and c["recall"] == pytest.approx(0.5)
    assert c["balanced_accuracy"] == pytest.approx(0.5 * (0.5 + 1 / 3))


def test_top_fraction_keeps_round_q_n():
    s = np.array([5.0, 1.0, 4.0, 2.0, 3.0])
    assert top_fraction(s, 0.4).tolist() == [True, False, True, False, False]
    assert top_fraction(s, 0.01).sum() == 1
    with pytest.raises(FilterOracleError):
        top_fraction(s, 0.0)


def test_calibration_of_an_honest_projection_has_slope_one():
    rng = np.random.default_rng(0)
    p = rng.normal(0, 1, 5000)
    r = p + rng.normal(0, 0.1, 5000)
    c = calibration(p, r, n_bins=10)
    assert c["slope"] == pytest.approx(1.0, abs=0.02)
    assert c["intercept"] == pytest.approx(0.0, abs=0.01)
    assert len(c["bins"]) == 10
    with pytest.raises(FilterOracleError):
        calibration(np.ones(100), r[:100])


def test_the_partial_oracle_spans_random_to_perfect():
    rng = np.random.default_rng(1)
    t = rng.normal(0, 1, 20000)
    assert spearman(partial_oracle_score(t, 1.0, rng), t) == pytest.approx(1.0)
    assert abs(spearman(partial_oracle_score(t, 0.0, rng), t)) < 0.03
    mid = spearman(partial_oracle_score(t, 0.5, rng), t)
    assert mid == pytest.approx(6 / np.pi * np.arcsin(0.25), abs=0.02)
    with pytest.raises(FilterOracleError):
        partial_oracle_score(t, 1.2, rng)


def test_the_curve_rises_with_accuracy_and_its_zero_is_the_null():
    rng = np.random.default_rng(2)
    net = rng.normal(0, 10, 4000)
    curve = partial_oracle_curve(net, net, rhos=(0.0, 0.2, 0.6, 1.0), q=0.3, n_draw=20, rng=rng)
    means = [c["mean_net_per_trade"] for c in curve]
    assert means == sorted(means)
    assert abs(means[0]) < 1.0                                   # a random 30 % keeps the population mean (0)
    assert curve[-1]["precision_mean"] == pytest.approx(1.0)     # the oracle's top 30 % are all winners


def test_assess_fires_on_the_guards():
    s = np.arange(10.0)
    g = np.arange(10.0) - 4
    with pytest.raises(FilterOracleError):
        assess(s, np.ones(9, dtype=bool), g, g)                  # length mismatch
    with pytest.raises(FilterOracleError):
        assess(s, (s > 5).astype(int), g, g)                     # not a boolean mask
    bad = g.copy()
    bad[3] = np.nan
    with pytest.raises(FilterOracleError):
        assess(s, s > 5, bad, g)                                 # a NaN
    out = assess(s, s > 5, g, g - 1)
    assert out["auc_vs_oracle_label"] == pytest.approx(1.0)
    assert out["capture"]["trades"] == 4
