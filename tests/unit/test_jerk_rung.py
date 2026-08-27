"""Gates for D229's jerk rung.

The load-bearing ones are the pairing test (a bootstrap that drew separate dates
per rung would silently destroy the common variance that makes a ladder delta
worth measuring) and the tie policy, which is live at 3.10% of bars here against
a rounding-order curiosity for a level rule.
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
        "rjr", REPO / "scripts" / "run_jerk_rung.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["rjr"] = module
    spec.loader.exec_module(module)
    return module


R = _load()


class _Series:
    """Just enough of ImpulseSeries for `jerk_score`."""

    def __init__(self, histogram):
        self.histogram = tuple(histogram)


# --------------------------------------------------------------------------
# The rung
# --------------------------------------------------------------------------


def test_jerk_is_the_first_difference_of_the_histogram():
    out = R.jerk_score(_Series([1.0, 3.0, 2.0, 2.5]))
    assert math.isnan(out[0])
    assert out[1:] == (2.0, -1.0, 0.5)


def test_jerk_is_nan_wherever_the_histogram_is_nan():
    out = R.jerk_score(_Series([math.nan, math.nan, 1.0, 4.0]))
    assert math.isnan(out[0])
    assert math.isnan(out[1])
    assert math.isnan(out[2])  # 1.0 - nan
    assert out[3] == 3.0


def test_jerk_length_matches_the_input():
    for n in (2, 5, 50):
        assert len(R.jerk_score(_Series([float(i) for i in range(n)]))) == n


def test_a_flat_histogram_gives_exact_zeros_which_the_tie_policy_sends_flat():
    """`md` is EXACTLY 0.0 in the dead zone, so a run of dead-zone bars gives
    hist == 0.0 exactly and then d hist == 0.0 exactly. Measured at 3.10% of live
    bars before the record was written; the flat policy was committed in advance."""
    from backtest_framework.research import macd as M

    score = R.jerk_score(_Series([0.0] * 10))
    assert score[1:] == (0.0,) * 9
    pos = M.positions(score, start=1, long_short=False)
    assert set(pos) == {0.0}


def test_ties_are_flat_not_carried_forward():
    from backtest_framework.research import macd as M

    # up, tie, down -> long, flat, flat (long_flat)
    score = (math.nan, 1.0, 0.0, -1.0)
    assert M.positions(score, start=1, long_short=False) == (0.0, 1.0, 0.0, 0.0)


def test_jerk_at_bar_t_cannot_see_bar_t_plus_one():
    base = [float(i) for i in range(30)]
    a = R.jerk_score(_Series(base))
    base[20] = 999.0
    b = R.jerk_score(_Series(base))
    assert a[:20] == b[:20]
    assert a[20] != b[20]


# --------------------------------------------------------------------------
# The paired bootstrap -- the load-bearing construction
# --------------------------------------------------------------------------


def test_bootstrap_of_a_series_against_itself_is_exactly_zero():
    """The tightest possible pairing check: identical inputs must give a delta of
    exactly 0 in EVERY replication. If the two series were indexed separately this
    would be noise instead."""
    rng = np.random.default_rng(4)
    x = rng.normal(0.0005, 0.01, size=800)
    out = R.paired_block_bootstrap(x, x)
    assert out["p05"] == 0.0
    assert out["p95"] == 0.0
    assert out["sd"] == 0.0


def test_bootstrap_recovers_the_sign_of_a_real_difference():
    rng = np.random.default_rng(6)
    good = rng.normal(0.0010, 0.01, size=1500)
    bad = rng.normal(-0.0010, 0.01, size=1500)
    out = R.paired_block_bootstrap(good, bad)
    assert out["p50"] > 0.0
    assert out["p05"] > 0.0


def test_bootstrap_is_deterministic():
    rng = np.random.default_rng(8)
    a = rng.normal(size=600)
    b = rng.normal(size=600)
    assert R.paired_block_bootstrap(a, b) == R.paired_block_bootstrap(a, b)


def test_bootstrap_refuses_mismatched_lengths():
    with pytest.raises(AssertionError):
        R.paired_block_bootstrap(np.zeros(100), np.zeros(99))


def test_bootstrap_draws_one_index_and_applies_it_to_both_series():
    """Pinned by reading the source, because it is invisible in the output: `idx`
    is built once per replication and used for BOTH rungs."""
    src = (REPO / "scripts" / "run_jerk_rung.py").read_text(encoding="utf-8")
    body = src.split("def paired_block_bootstrap")[1].split("def build")[0]
    assert "xa, xb = a[idx], b[idx]" in body
    assert body.count("starts = rng.integers") == 1


def test_bootstrap_blocks_stay_inside_the_series():
    """An off-by-one in the block start would index past the end and either raise
    or silently wrap."""
    n, block = 100, 21
    rng = np.random.default_rng(0)
    starts = rng.integers(0, n - block + 1, size=200)
    idx = (starts[:, None] + np.arange(block)[None, :]).ravel()
    assert idx.max() < n
    assert idx.min() >= 0


# --------------------------------------------------------------------------
# Declared constants and conventions
# --------------------------------------------------------------------------


def test_the_declared_constants_are_the_pre_registered_ones():
    assert R.BLOCK == 21
    assert R.N_BOOT == 1000
    assert R.SEED == 0
    assert R.LAG == 1
    assert R.DELTA_HURDLE == 0.10
    assert R.RUNGS == ("I0_jerk", "I1_signal", "I2_band")
    assert R.FRESH_LOOKS == 4


def test_hurdle_a_requires_both_legs():
    """The point estimate alone was D218's test. D229's is stricter and this pins
    that it stayed stricter."""
    src = (REPO / "scripts" / "run_jerk_rung.py").read_text(encoding="utf-8")
    assert 'd["I0_minus_I1"] >= DELTA_HURDLE' in src
    assert 'd["boot"]["p05"] > DELTA_HURDLE' in src


def test_rf_per_bar_compounds_to_the_annual_rate():
    assert math.expm1(R.RF_PER_BAR * R.PPY) == pytest.approx(R.RF_ANNUAL, rel=1e-12)


def test_excess_sharpe_charges_rf_only_on_exposure():
    port = np.full(500, 0.0004)
    assert R.excess_sharpe(port, np.full(500, 0.5)) > R.excess_sharpe(
        port, np.full(500, 1.0)
    )


def test_the_runner_does_not_edit_d218s_committed_runner():
    """D229 duplicates four lines of dispatch rather than patching
    `run_impulse_macd.arm_positions`. Editing a committed study's code after it
    reported is how a record stops describing what was run."""
    src = (REPO / "scripts" / "run_impulse_macd.py").read_text(encoding="utf-8")
    assert "I0_jerk" not in src
    assert "jerk" not in src.lower()
