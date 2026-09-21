"""Invariants of hurdle P, quantified over random daily series — D590.

The unit and golden files pin chosen inputs; that is the right shape for a GATE and the
wrong shape for a GUARANTEE (`tests/property/test_macd_invariants.py`). The failures
feared here have a shape rather than a location:

  * `p5_recognised` disagreeing with `scripts/d495_agree_confluence.py` on a series
    nobody thought to write down — reproduction guard (d) of the D590 record, in its
    quantified form;
  * the dollar-native floor picking up a scale dependence it must not have: doubling
    every daily dollar and the cap must give the SAME deaths and the same lives, because
    the floor is an absolute distance and not a fraction of anything (D542);
  * a hurdle silently returning a plausible number on an input it cannot serve.

D78 fixed the convention (`derandomize=True`), and D537 withdrew the claim that it makes
the suite byte-deterministic: the seed is fixed but the constant pool hypothesis draws
from is harvested at test time, so a failure that does not reproduce when this file is
run alone is NOT thereby a flake — reproduce it with the whole suite.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from backtest_framework.validation import hurdle_p as HP

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "scripts"

# D78 / D537: the seed is fixed, the examples are not.
SETTINGS = settings(derandomize=True, max_examples=40, deadline=None)


def _d495():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    if "d495_agree_confluence" in sys.modules:
        return sys.modules["d495_agree_confluence"]
    spec = importlib.util.spec_from_file_location(
        "d495_agree_confluence", SCRIPTS / "d495_agree_confluence.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["d495_agree_confluence"] = mod
    spec.loader.exec_module(mod)
    return mod


DOLLARS = st.floats(min_value=-5_000.0, max_value=5_000.0,
                    allow_nan=False, allow_infinity=False, width=32)
SERIES = st.lists(DOLLARS, min_size=2, max_size=400)


def _same(a, b) -> bool:
    if isinstance(a, float) and math.isnan(a):
        return isinstance(b, float) and math.isnan(b)
    return bool(a == b)


# ---------------------------------------------------------------- guard (d), quantified


@SETTINGS
@given(SERIES)
def test_p5_recognised_is_d495s_on_every_series(xs):
    """Reproduction guard (d): the published haircut, function against function."""
    d495 = _d495()
    x = np.asarray(xs, dtype=float)
    mine, theirs = HP.p5_recognised(x), d495.p5_recognised(x)
    assert set(mine) == set(theirs)
    for k in mine:
        assert _same(mine[k], theirs[k]), (k, mine[k], theirs[k])


@SETTINGS
@given(SERIES)
def test_p5_recognised_never_credits_more_than_the_total(xs):
    """R11's convention is a HAIRCUT: it can only take profit away, never add it."""
    h = HP.p5_recognised(np.asarray(xs, dtype=float))
    assert h["recognised_usd"] <= h["total_usd"] + 1e-9
    assert h["haircut_usd"] >= 0.0
    if h["total_usd"] > 0:
        assert h["haircut_applies"] == (h["haircut_usd"] > 0)


# ---------------------------------------------------------------- the dollar-native floor


@SETTINGS
@given(SERIES, st.floats(min_value=1.5, max_value=50.0, allow_nan=False,
                         allow_infinity=False))
def test_the_floor_is_scale_free_in_dollars_not_in_fractions(xs, k):
    """D542. Double the dollars AND the cap and nothing about the deaths may move.

    A fraction-of-a-compounded-peak drawdown does not have this property, which is why
    `analytics/metrics.py:max_drawdown` is the wrong instrument for a prop floor.
    """
    x = np.asarray(xs, dtype=float)
    a = HP.max_drawdown_life(x, 2_000.0)
    b = HP.max_drawdown_life(x * k, 2_000.0 * k)
    assert a[0] == b[0]
    assert a[2] == b[2]
    assert _same(a[1], b[1])


@SETTINGS
@given(SERIES)
def test_a_tighter_cap_never_buys_the_account_more_life(xs):
    x = np.asarray(xs, dtype=float)
    tight = HP.max_drawdown_life(x, 500.0)
    loose = HP.max_drawdown_life(x, 2_000.0)
    assert tight[0] >= loose[0]


@SETTINGS
@given(SERIES)
def test_the_episodes_partition_the_window_and_never_overlap(xs):
    x = np.asarray(xs, dtype=float)
    _, _, eps = HP.max_drawdown_life(x, 300.0)
    prev_end = -1
    for start, end, length in eps:
        assert start == prev_end + 1
        assert end >= start
        assert length == end - start + 1
        prev_end = end
    assert prev_end < len(x)


@SETTINGS
@given(SERIES)
def test_p1_sizing_puts_the_drawdown_exactly_on_the_cap(xs):
    """The whole content of P1: scale until the trailing drawdown IS the budget."""
    x = np.asarray(xs, dtype=float)
    eq = np.cumsum(x)
    peak = np.maximum.accumulate(np.maximum(eq, 0.0))
    assume(float((peak - eq).max()) > 1e-6)
    s = HP.p1_size(x, 2_000.0)
    scaled = x * s["size_multiplier"]
    eq2 = np.cumsum(scaled)
    peak2 = np.maximum.accumulate(np.maximum(eq2, 0.0))
    assert float((peak2 - eq2).max()) == pytest.approx(2_000.0, rel=1e-9)


# ---------------------------------------------------------------- P3


@SETTINGS
@given(SERIES)
def test_p3a_counts_exactly_the_days_beyond_two_percent(xs):
    x = np.asarray(xs, dtype=float)
    g = HP.p3(x, 50_000.0)
    assert g["p3a_breaches"] == int((x <= -1_000.0).sum())
    assert g["p3a_breaches_per_year"] == pytest.approx(
        g["p3a_breaches"] / len(x) * 252, rel=1e-12)
    assert 0.0 <= g["p_breach_in_252"] <= 1.0


@SETTINGS
@given(SERIES)
def test_enforcing_p3_never_lengthens_the_account(xs):
    """P3 is a second way to die: it adds deaths and brings the FIRST death forward or not at all.

    The MEAN life is not monotone in it, and the first version of this test said it was. The
    harvested falsifying input (2026-09-21, found once by a parallel agent's full-suite run,
    D537) is `[-2000, 0, -1000]` on a $50,000 account: the trailing-drawdown walker dies once
    at session 1 (life 1.0); with P3 the account also dies at session 3 on the -$1,000 day,
    a SECOND episode of length 2, so the mean life rises to 1.5 and `p3b_life_cost` is -0.5.
    Every death still came no later than before -- the mean moved because a new, longer
    episode joined the average. So the invariant is on the death TIMES, not the mean, and a
    negative `p3b_life_cost` is a legitimate reported value, pinned below.
    """
    x = np.asarray(xs, dtype=float)
    g = HP.p3(x, 50_000.0)
    trail_dd = 50_000.0 * HP.DD_FRACTION
    _, _, episodes_dd = HP.max_drawdown_life(x, trail_dd)
    lives_p3 = HP._life_with_p3(x, trail_dd, g["p3_cap_usd"])
    assert g["deaths_with_p3"] >= g["deaths_dd_only"]
    if episodes_dd and lives_p3:
        # `max_drawdown_life` episodes are `(start, end, length)`; `_life_with_p3` returns lengths.
        assert lives_p3[0] <= episodes_dd[0][2], "the first death with P3 on came LATER"
    assert sum(lives_p3) <= len(x)


def test_the_harvested_p3_counterexample_is_pinned():
    """The exact input from the docstring above, so the behaviour is a fact and not a memory."""
    g = HP.p3(np.array([-2000.0, 0.0, -1000.0]), 50_000.0)
    assert (g["deaths_dd_only"], g["deaths_with_p3"]) == (1, 2)
    assert (g["life_dd_only_sessions"], g["life_with_p3_sessions"]) == (1.0, 1.5)
    assert g["p3b_life_cost"] == -0.5


@SETTINGS
@given(SERIES)
def test_p3c_is_reported_and_never_gates(xs):
    g = HP.p3(np.asarray(xs, dtype=float), 50_000.0)
    assert not any(k.startswith("p3c") and k.endswith("pass") for k in g)
    assert g["p3c_worst_day_usd"] == min(xs)


# ---------------------------------------------------------------- P2, the clock


@SETTINGS
@given(st.lists(st.tuples(st.integers(0, 23), st.integers(0, 59)), min_size=1,
                max_size=20))
def test_p2_is_exactly_the_max_exit_against_the_venue_clock(times):
    exits = [f"{h:02d}:{m:02d}" for h, m in times]
    limit = 16 * 60 + 10           # mffu_rapid_eod_50k, 16:10 ET
    want = max(h * 60 + m for h, m in times) <= limit
    assert HP.p2_flatten(exits, "mffu_rapid_eod_50k") is want


# ---------------------------------------------------------------- the boundary


@SETTINGS
@given(st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False),
       st.floats(min_value=10.0, max_value=5_000.0, allow_nan=False,
                 allow_infinity=False))
def test_the_dollar_wrapper_is_the_fraction_form_scaled(sharpe, sigma_usd):
    """The unit boundary is a conversion and nothing else; if it ever becomes more than
    that, this fires.

    Sigma is drawn from $10 to $5,000 a day, which is the range a one-contract futures
    book can occupy on a $50,000 account (the ledger's C-d bar is $500). Below about
    $1 a day D496's own `expm1(theta * D)` overflows to inf -- a property of the
    inherited closed form at absurd parameters, reproduced faithfully rather than
    patched, and `test_a_fraction_where_dollars_belong_always_raises` shows the wrapper
    refuses that whole region anyway.
    """
    account = 50_000.0
    got_p, got_l = HP.expected_profit_before_breach_usd(sharpe, sigma_usd, account,
                                                        0.04 * account)
    want_p, want_l = HP.expected_profit_before_breach(sharpe, sigma_usd / account, 0.04)
    assert got_p == want_p * account
    assert _same(got_l, want_l)


@SETTINGS
@given(st.floats(min_value=1e-12, max_value=0.4, allow_nan=False, allow_infinity=False))
def test_a_fraction_where_dollars_belong_always_raises(sigma_frac):
    """The slip that crashed D503's first run, on every fraction below the floor."""
    account = 50_000.0
    assume(sigma_frac / account < HP.MIN_SIGMA_FRAC)
    try:
        HP.expected_profit_before_breach_usd(1.0, sigma_frac, account)
    except ValueError:
        return
    raise AssertionError(f"no raise on sigma_usd={sigma_frac!r}")
