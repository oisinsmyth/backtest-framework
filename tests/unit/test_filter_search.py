"""Gates for D228's filter search.

The load-bearing ones are the look-ahead test and the null-construction test.
Everything else pins arithmetic that would otherwise be a claim in prose.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location(
        "rfs", REPO / "scripts" / "run_filter_search.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["rfs"] = module
    spec.loader.exec_module(module)
    return module


R = _load()


# --------------------------------------------------------------------------
# Trade spans and the scatter reconstruction
# --------------------------------------------------------------------------


def test_trade_spans_finds_maximal_runs():
    pos = np.array([[0, 1, 1, 0, 0, 1, 0], [1, 1, 0, 0, 0, 0, 0]], dtype=float)
    sym, start, end = R.trade_spans(pos)
    assert list(zip(sym.tolist(), start.tolist(), end.tolist())) == [
        (0, 1, 3),
        (0, 5, 6),
        (1, 0, 2),
    ]


def test_trade_spans_handles_a_run_touching_the_last_bar():
    pos = np.array([[0, 0, 1, 1]], dtype=float)
    sym, start, end = R.trade_spans(pos)
    assert (sym.tolist(), start.tolist(), end.tolist()) == ([0], [2], [4])


def test_book_from_spans_reconstructs_the_parent_exactly():
    """Size 1.0 on every span must give the parent back. If this drifts, every
    entry-gated candidate and all 1,000 null replications are wrong together."""
    rng = np.random.default_rng(7)
    pos = (rng.random((6, 200)) > 0.6).astype(float)
    sym, start, end = R.trade_spans(pos)
    rebuilt = R.book_from_spans(pos.shape, sym, start, end, np.ones(len(sym)))
    assert np.array_equal(rebuilt, pos)


def test_book_from_spans_scales_each_trade_independently():
    pos = np.array([[0, 1, 1, 0, 1, 0]], dtype=float)
    sym, start, end = R.trade_spans(pos)
    out = R.book_from_spans(pos.shape, sym, start, end, np.array([0.25, 0.75]))
    assert out.tolist() == [[0.0, 0.25, 0.25, 0.0, 0.75, 0.0]]


# --------------------------------------------------------------------------
# The trailing statistics must be TRAILING
# --------------------------------------------------------------------------


def test_trailing_window_ends_inclusive_of_bar_t():
    """The convention, pinned: `out[t]` covers `x[t-window+1 .. t]` INCLUSIVE.

    Including bar t is correct and is not look-ahead, because every signal is
    shifted by LAG before it reaches a position -- see the test below, which is
    the invariant that actually matters."""
    rng = np.random.default_rng(11)
    x = rng.normal(size=(2, 50))
    assert R.trailing_std(x, 10)[0, 30] == pytest.approx(
        np.std(x[0, 21:31], ddof=1), rel=1e-10
    )
    assert R.trailing_mean(x, 8)[1, 25] == pytest.approx(
        np.mean(x[1, 18:26]), rel=1e-12
    )


def test_a_spike_at_bar_t_moves_nothing_strictly_before_t():
    # Perturb from bar 40 ONWARD, not a single bar: a median over ten values is
    # robust to one outlier, so a lone spike would leave it unmoved and the test
    # would pass for the wrong reason.
    x = np.ones((1, 60))
    a = R.trailing_median(x, 10)
    x[0, 40:] = 500.0
    b = R.trailing_median(x, 10)
    assert np.allclose(a[0, :40], b[0, :40], equal_nan=True)
    assert not np.allclose(a[0, 40:], b[0, 40:], equal_nan=True)

    rng = np.random.default_rng(3)
    y = rng.normal(size=(1, 80))
    c = R.trailing_std(y, 20)
    y[0, 55] += 100.0
    d = R.trailing_std(y, 20)
    assert np.allclose(c[0, :55], d[0, :55], equal_nan=True)


@pytest.mark.parametrize("fn", ["trailing_std", "trailing_mean", "trailing_median"])
def test_the_shifted_signal_at_bar_t_cannot_depend_on_bar_t(fn):
    """THE no-look-ahead invariant. Perturb the input from bar t onward and assert
    no SHIFTED value at any index <= t moves. This is what the arm actually reads,
    and the vacuous version of this test (too short a series) is what let a
    look-ahead defect through in D224."""
    f = getattr(R, fn)
    rng = np.random.default_rng(21)
    x = rng.normal(size=(3, 400)) + 5.0
    t = 300
    a = R.shift(np.nan_to_num(f(x, 20)), R.LAG)
    x[:, t:] += 50.0
    b = R.shift(np.nan_to_num(f(x, 20)), R.LAG)
    assert np.allclose(a[:, : t + 1], b[:, : t + 1])
    assert not np.allclose(a[:, t + 1 :], b[:, t + 1 :])


def test_trailing_stats_are_nan_before_the_window_fills():
    x = np.ones((1, 30))
    assert np.isnan(R.trailing_std(x, 10)[0, :10]).all()
    assert np.isnan(R.trailing_mean(x, 10)[0, :10]).all()
    assert np.isnan(R.trailing_median(x, 10)[0, :10]).all()


# --------------------------------------------------------------------------
# The lag convention
# --------------------------------------------------------------------------


def test_shift_holds_through_bar_t_what_was_decided_earlier():
    x = np.array([[1.0, 2.0, 3.0, 4.0]])
    assert R.shift(x, 1).tolist() == [[0.0, 1.0, 2.0, 3.0]]


def test_signals_are_shifted_by_the_same_lag_as_the_arm():
    """If the filter were read unshifted it would know the close that produced the
    arm's own signal -- a one-bar look-ahead that would flatter every candidate."""
    assert R.LAG == 1
    src = Path(REPO / "scripts" / "run_filter_search.py").read_text(encoding="utf-8")
    assert "return {k: shift(v, LAG) for k, v in sig.items()}" in src


# --------------------------------------------------------------------------
# rf on the exposed fraction -- D228 Part 1, fact 2
# --------------------------------------------------------------------------


def test_excess_sharpe_charges_rf_only_on_exposure():
    port = np.full(500, 0.0004)
    half = np.full(500, 0.5)
    full = np.full(500, 1.0)
    # A book exposed half the time is charged half the rf, so its excess return is
    # higher than the same book charged in full.
    assert R.excess_sharpe(port, half) > R.excess_sharpe(port, full)


def test_excess_sharpe_equals_rf_zero_when_exposure_is_zero():
    port = np.random.default_rng(5).normal(0.0003, 0.01, size=400)
    flat = np.zeros(400)
    expected = float(np.mean(port)) / float(np.std(port, ddof=1)) * math.sqrt(R.PPY)
    assert R.excess_sharpe(port, flat) == pytest.approx(expected, rel=1e-12)


def test_rf_per_bar_compounds_to_the_annual_rate():
    assert math.expm1(R.RF_PER_BAR * R.PPY) == pytest.approx(R.RF_ANNUAL, rel=1e-12)


# --------------------------------------------------------------------------
# The candidate set is the DECLARED one
# --------------------------------------------------------------------------


def test_the_candidate_list_is_closed_at_eight():
    assert R.CANDIDATES == ("G1", "G2", "S1", "S2", "S3", "S4", "S5", "R1")
    assert len(R.CANDIDATES) == R.FRESH_LOOKS == 8


def test_r1_is_excluded_from_the_null_and_only_r1():
    """R1's signal is the parent's own flat mask, so there is nothing to rotate.
    Excluding it is a disclosed limitation; excluding anything ELSE would be a
    silently shrunken search."""
    assert set(R.CANDIDATES) - set(R.NULL_CANDIDATES) == {"R1"}
    assert len(R.NULL_CANDIDATES) == 7


def test_no_volume_candidate_exists_d220_stop_is_honoured():
    """D220's stop reads 'no volume work continues on this fixture' and this IS
    that fixture. The stop is honoured rather than overridden, so no candidate may
    read volume."""
    src = Path(REPO / "scripts" / "run_filter_search.py").read_text(encoding="utf-8")
    body = src.split("def candidate_signals")[1].split("def excess_sharpe")[0]
    assert "volume" not in body.lower()
    assert ".volume" not in body


def test_gates_are_binary_and_sizers_are_not():
    rng = np.random.default_rng(2)
    sig = rng.random((4, 30))
    parent = np.ones((4, 30))
    spans = R.trade_spans(parent)
    for name in R.GATES:
        out = R.apply_candidate(name, sig, parent, spans, None)
        assert set(np.unique(out)) <= {0.0, 1.0}


# --------------------------------------------------------------------------
# The null construction -- the load-bearing detail
# --------------------------------------------------------------------------


def test_null_rotation_preserves_each_signal_s_own_distribution():
    """Rotation must be the same series pointed at the wrong bars, so every
    order statistic is unchanged."""
    rng = np.random.default_rng(9)
    sig = rng.random((5, 300))
    rotated = np.array([np.roll(sig[i], 37) for i in range(5)])
    assert np.allclose(np.sort(sig, axis=1), np.sort(rotated, axis=1))


def test_one_offset_vector_is_reused_across_all_candidates():
    """Rotating candidates independently would make them artificially independent,
    inflating the max and giving a floor that is wrong in the conservative
    direction. The offsets are drawn ONCE per replication, outside the candidate
    loop -- pinned here because it is invisible in the output."""
    src = Path(REPO / "scripts" / "run_filter_search.py").read_text(encoding="utf-8")
    body = src.split("def best_of_search_null")[1].split("def build")[0]
    draw = body.index("offsets = rng.integers")
    loop = body.index("for name in NULL_CANDIDATES")
    assert draw < loop, "offsets must be drawn before the candidate loop, not inside it"


def test_multiplicity_counts_are_the_declared_ones():
    assert R.FRESH_LOOKS == 8
    assert R.INHERITED_D218 == 62
    assert R.DISCLOSED_PRIOR == 45_803


def test_windows_are_the_declared_ones():
    assert (R.VOL_WINDOW, R.MA_WINDOW) == (63, 200)
    assert R.N_SIMS == 1000
    assert R.SEED == 0
