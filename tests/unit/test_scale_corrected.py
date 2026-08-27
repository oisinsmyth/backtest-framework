"""Gates for D232's scale-corrected Impulse MACD.

The three validation checks the pre-registration names as tests rather than
hurdles live here: the synthetic downtrend, exact scale invariance, and
no look-ahead.
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.research import macd as M  # noqa: E402


def _load():
    spec = importlib.util.spec_from_file_location(
        "rsc", REPO / "scripts" / "run_scale_corrected.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["rsc"] = module
    spec.loader.exec_module(module)
    return module


R = _load()
ART = json.loads((REPO / "data" / "scale_corrected_summary.json").read_text(encoding="utf-8"))
SPREAD = 0.004


@dataclass(frozen=True)
class _Bar:
    high: float
    low: float
    close: float


@dataclass(frozen=True)
class _TS:
    bar: _Bar


def bars_from(closes):
    return [_TS(_Bar(c * (1 + SPREAD), c * (1 - SPREAD), c)) for c in closes]


def frac_long(score, start):
    a = np.asarray(score, dtype=float)[start:]
    a = a[~np.isnan(a)]
    return float((a > 0).mean())


WARM = M.impulse_warm_up_bars()


# --------------------------------------------------------------------------
# The declared validation: the synthetic downtrend
# --------------------------------------------------------------------------


def test_the_published_indicator_is_long_through_a_steady_decline():
    """The defect itself, pinned. If this ever stops failing, the premise of D232
    has changed and the record needs revisiting."""
    t = np.arange(4000)
    px = 100 * np.exp(math.log(0.80) / 252 * t)
    b = bars_from(px)
    assert frac_long(M.impulse_signal_score(M.impulse_macd_series(b)), WARM) > 0.95


@pytest.mark.parametrize("fn", ["ratio_score", "log_score"])
def test_both_corrections_stand_aside_on_a_steady_decline(fn):
    """D232's declared gate: < 60% long where the published rung is 100% long."""
    t = np.arange(4000)
    px = 100 * np.exp(math.log(0.80) / 252 * t)
    assert frac_long(getattr(R, fn)(bars_from(px)), WARM) < 0.60


@pytest.mark.parametrize("fn", ["ratio_score", "log_score"])
def test_the_corrected_histogram_is_machine_zero_on_a_steady_decline(fn):
    """The substantive claim, and much stronger than counting how often the sign is
    positive.

    A steady exponential trend is a STRAIGHT LINE in log space, so md is constant
    and its derivative is ZERO -- the correct answer for a path carrying no
    acceleration. Both corrections reach ~1e-16, thirteen orders of magnitude below
    the published construction's 1.3e-03, so whatever sign they report is the sign
    of floating-point noise and nothing else.

    D232's record predicted I1L would 'land near 50%'. It lands at 25.6%, and this
    test explains why that guess was meaningless: at 1e-16 the fraction is
    arbitrary."""
    t = np.arange(4000)
    px = 100 * np.exp(math.log(0.80) / 252 * t)
    bars = bars_from(px)

    published = np.asarray(M.impulse_signal_score(M.impulse_macd_series(bars)), dtype=float)
    corrected = np.asarray(getattr(R, fn)(bars), dtype=float)
    pub = np.abs(published[WARM:][~np.isnan(published[WARM:])]).mean()
    cor = np.abs(corrected[WARM:][~np.isnan(corrected[WARM:])]).mean()

    assert cor < 1e-12, f"{fn} left a residual of {cor:.2e}"
    assert cor < pub * 1e-9, f"{fn} only reduced {pub:.2e} to {cor:.2e}"


def test_both_corrections_still_hold_an_accelerating_uptrend():
    """A fix that stood aside from everything would pass the test above for the
    wrong reason."""
    t = np.arange(4000)
    px = 100 * np.exp(0.0002 * t + 3e-8 * t**2)
    for fn in (R.ratio_score, R.log_score):
        assert frac_long(fn(bars_from(px)), WARM) > 0.80


# --------------------------------------------------------------------------
# Scale invariance
# --------------------------------------------------------------------------


def test_the_log_displacement_is_EXACTLY_invariant_to_scale():
    """Not merely close. smma and zlema are linear with unit DC gain, so on
    log(kP) = log k + log P every leg shifts by the same constant and mi - hi is
    unchanged. This is the property I1L is built on."""
    rng = np.random.default_rng(11)
    px = 100 * np.exp(np.cumsum(rng.normal(0.0003, 0.01, 2500)))
    a = np.asarray(R.log_score(bars_from(px)), dtype=float)
    b = np.asarray(R.log_score(bars_from(px * 137.0)), dtype=float)
    m = ~(np.isnan(a) | np.isnan(b))
    assert np.allclose(a[m], b[m], atol=1e-9)


def test_the_ratio_correction_is_invariant_too():
    rng = np.random.default_rng(12)
    px = 100 * np.exp(np.cumsum(rng.normal(0.0003, 0.01, 2500)))
    a = np.asarray(R.ratio_score(bars_from(px)), dtype=float)
    b = np.asarray(R.ratio_score(bars_from(px * 137.0)), dtype=float)
    m = ~(np.isnan(a) | np.isnan(b))
    assert np.allclose(a[m], b[m], atol=1e-9)


# --------------------------------------------------------------------------
# No look-ahead
# --------------------------------------------------------------------------


@pytest.mark.parametrize("fn", ["ratio_score", "log_score"])
def test_perturbing_from_bar_t_moves_nothing_at_or_before_t(fn):
    rng = np.random.default_rng(13)
    px = 100 * np.exp(np.cumsum(rng.normal(0.0003, 0.01, 2000)))
    t = 1500
    a = np.asarray(getattr(R, fn)(bars_from(px)), dtype=float)
    px2 = px.copy()
    px2[t:] *= 1.5
    b = np.asarray(getattr(R, fn)(bars_from(px2)), dtype=float)
    m = ~(np.isnan(a[:t]) | np.isnan(b[:t]))
    assert np.allclose(a[:t][m], b[:t][m])


# --------------------------------------------------------------------------
# The dead zone is preserved by both corrections
# --------------------------------------------------------------------------


def test_both_corrections_keep_the_dead_zone():
    """`0.0` inside the channel is a stated value, not a missing one. A fix that
    quietly changed it would be testing two things at once."""
    src = (REPO / "scripts" / "run_scale_corrected.py").read_text(encoding="utf-8")
    assert src.count("out.append(0.0)") == 1
    flat = bars_from(np.full(2500, 100.0))
    for fn in (R.ratio_score, R.log_score):
        a = np.asarray(fn(flat), dtype=float)[WARM:]
        a = a[~np.isnan(a)]
        assert np.allclose(a, 0.0)


# --------------------------------------------------------------------------
# The committed run
# --------------------------------------------------------------------------


def test_the_run_is_a_screen_and_not_a_verdict():
    assert ART["stage"] == "screen"
    assert ART["is_verdict"] is False
    assert ART["n_symbols"] == 57


def test_the_standing_delta_hurdle_was_not_lowered():
    """Lowering the bar to fit the expected effect is what pre-registration exists
    to prevent."""
    assert ART["delta_hurdle"] == 0.10
    assert R.DELTA_HURDLE == 0.10


def test_both_corrected_rungs_were_run_and_neither_was_dropped():
    for rung in ("I1r_ratio", "I1L_log"):
        assert f"{rung}|long_flat|none" in ART["cells"]
        assert f"{rung}|long_flat|none" in ART["deltas"]


def test_exposure_barely_moved_which_is_Z3():
    base = ART["cells"]["I1_signal|long_flat|none"]["exposure"]
    for rung in ("I1r_ratio", "I1L_log"):
        assert abs(ART["cells"][f"{rung}|long_flat|none"]["exposure"] - base) < 0.02
