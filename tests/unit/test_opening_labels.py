"""`backtest_framework.opening.labels` -- the opening agent-state model's day-type labels (s.5.3, OA-A6).

Covers the deposit's required unit tests 1, 3 and 12 (`OPENING_AGENT_STATE_PREREG.md` s.15), named
`test_opening_NN_...` so the crosswalk finds them, plus ATR20's prior-sessions-only rule. Synthetic inputs only.
"""

from __future__ import annotations

import numpy as np

from backtest_framework.opening.labels import atr_prior, classify, merge_rare


def _one(d0, o, c, h, lo, ih, il, pc, atr):
    return classify(np.array([d0]), np.array([o]), np.array([c]), np.array([h]), np.array([lo]), np.array([ih]),
                    np.array([il]), np.array([pc]), np.array([atr]))[0]


def test_opening_01_labels_reproduce_each_rule_in_order() -> None:
    # CONT: up from the open, body 8 of range 10 (>= 0.6), range 10 >= 1.8 x IB 4
    assert _one(+1, 100, 108, 109, 99, 102, 98, 100, 5) == "CONT"
    # REV: the same day read against an opening direction of -1
    assert _one(-1, 100, 108, 109, 99, 102, 98, 100, 5) == "REV"
    # CONT beats FADE: a big gap filled AND a trend day with d0 is CONT (the order)
    assert _one(-1, 100, 92, 101, 91, 101, 97, 96, 4) == "CONT"
    # FADE: gap +4 >= 0.25 x ATR 8; low 96.9 <= 100 - 0.75 x 4 = 97; not a trend day (IB too wide)
    assert _one(+1, 100, 99, 101, 96.9, 101, 96.9, 96, 8) == "FADE"
    # the same day whose low stops at 97.1 does not fill 75%: RANGE
    assert _one(+1, 100, 99, 101, 97.1, 101, 97.1, 96, 8) == "RANGE"
    # a gap below 0.25 x ATR is never FADE, however far it fills
    assert _one(+1, 100, 99, 101, 90, 101, 90, 99.5, 8) == "RANGE"
    # a down gap is filled by trading UP through it
    assert _one(-1, 100, 101, 103.1, 99, 103.1, 99, 104, 8) == "FADE"


def test_opening_03_d0_zero_is_unclassified_and_untraded() -> None:
    assert _one(0, 100, 108, 109, 99, 102, 98, 100, 5) is None
    # a missing input is unclassified too, never a silent RANGE
    assert _one(+1, 100, 108, 109, 99, 102, 98, 100, np.nan) is None


def test_opening_12_a_mirror_image_day_keeps_its_label() -> None:
    rng = np.random.default_rng(12)
    n = 400
    o = 100 + rng.normal(0, 1, n)
    c = o + rng.normal(0, 3, n)
    h = np.maximum(o, c) + rng.uniform(0, 0.8, n)
    lo = np.minimum(o, c) - rng.uniform(0, 0.8, n)
    ih = np.minimum(h, o + rng.uniform(0, 1, n))  # a narrow opening hour, so trend days occur
    il = np.maximum(lo, o - rng.uniform(0, 1, n))
    pc = o + rng.normal(0, 1.5, n)
    atr = rng.uniform(1, 6, n)
    d0 = rng.choice([-1.0, 1.0], n)
    a = classify(d0, o, c, h, lo, ih, il, pc, atr)
    # mirror every price through 200: highs become lows, the day's direction and d0 flip
    m = classify(-d0, 200 - o, 200 - c, 200 - lo, 200 - h, 200 - il, 200 - ih, 200 - pc, atr)
    assert list(a) == list(m)
    assert len(set(a)) >= 3, "the synthetic days must exercise several labels"


def test_opening_atr20_uses_the_prior_twenty_sessions_only() -> None:
    n = 30
    h = np.full(n, 102.0)
    lo = np.full(n, 98.0)
    c = np.full(n, 100.0)
    a = atr_prior(h, lo, c)
    assert np.isnan(a[:21]).all() and np.allclose(a[21:], 4.0)
    h2 = h.copy()
    h2[25] = 150.0  # a huge range ON session 25 must not reach session 25's own ATR
    b = atr_prior(h2, lo, c)
    assert b[25] == a[25] and b[26] > a[26]


def test_opening_rare_classes_merge_for_both_markets() -> None:
    f = {"ES": {"CONT": 0.2, "REV": 0.1, "FADE": 0.07, "RANGE": 0.63},
         "NQ": {"CONT": 0.2, "REV": 0.12, "FADE": 0.09, "RANGE": 0.59}}
    assert merge_rare(f) == ["FADE"]
