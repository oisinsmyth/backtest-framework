"""The opening agent-state model's day-type labels (OPENING_AGENT_STATE_PREREG.md s.5.3) and the readings OA-A6
fixes (ruled 2026-09-28).

Labels are TRAINING TARGETS ONLY (s.0.6): they read the whole 09:30-16:00 session and never enter a feature.

Rules, applied in this order, relative to the opening direction d0 = sign(price at t0 - RTH open):
- CONT: sign(close - open) = d0, |close - open| >= 0.6 R, and R >= 1.8 IB;
- REV:  sign(close - open) = -d0, with the same two size conditions;
- FADE: |gap| >= 0.25 ATR20, price trades through >= 75% of the gap towards the prior close by 16:00, and not
  CONT/REV;
- RANGE: everything else.
d0 = 0 leaves the day unclassified (None) and untraded (s.5.2).

OA-A6: open = the 09:30 bar's open; close = the 15:59 bar's close; prior close = the prior session's last RTH close;
gap = open - prior close; R = RTH high - low; IB = the 09:30-10:29 range; ATR20 = the mean true range of the 20
sessions BEFORE the current one, on RTH daily bars.
"""
from __future__ import annotations

import numpy as np

LABELS = ("CONT", "REV", "FADE", "RANGE")
TREND_BODY, TREND_RANGE_IB = 0.6, 1.8
FADE_GAP_ATR, FADE_THROUGH = 0.25, 0.75
ATR_N = 20


def atr_prior(high: np.ndarray, low: np.ndarray, close: np.ndarray, n: int = ATR_N) -> np.ndarray:
    """ATR over the n sessions BEFORE each session (NaN until n true ranges exist). Sessions in time order.

    True range at s = max(high[s], close[s-1]) - min(low[s], close[s-1]); the first session has no prior close and
    no true range. The value at s averages the true ranges of sessions s-n .. s-1, so it is known at s's open.
    """
    h, lo, c = (np.asarray(x, dtype=float) for x in (high, low, close))
    tr = np.full(len(h), np.nan)
    tr[1:] = np.maximum(h[1:], c[:-1]) - np.minimum(lo[1:], c[:-1])
    out = np.full(len(h), np.nan)
    for s in range(n + 1, len(h) + 1):
        if s < len(h):
            out[s] = tr[s - n:s].mean()
    return out


def classify(d0: np.ndarray, open_: np.ndarray, close: np.ndarray, rth_high: np.ndarray, rth_low: np.ndarray,
             ib_high: np.ndarray, ib_low: np.ndarray, prior_close: np.ndarray, atr20: np.ndarray) -> np.ndarray:
    """One label per day (object array; None where d0 = 0 or an input is missing)."""
    d0 = np.asarray(d0, dtype=float)
    o, c, h, lo = (np.asarray(x, dtype=float) for x in (open_, close, rth_high, rth_low))
    ih, il, pc, atr = (np.asarray(x, dtype=float) for x in (ib_high, ib_low, prior_close, atr20))
    R, IB, move, gap = h - lo, ih - il, c - o, o - pc
    trend = (np.abs(move) >= TREND_BODY * R) & (R >= TREND_RANGE_IB * IB)
    sm = np.sign(move)
    cont = trend & (sm == d0) & (sm != 0)
    rev = trend & (sm == -d0) & (sm != 0)
    big_gap = np.abs(gap) >= FADE_GAP_ATR * atr
    through = np.where(gap > 0, lo <= o - FADE_THROUGH * gap, h >= o + FADE_THROUGH * np.abs(gap))
    fade = big_gap & through & (gap != 0) & ~cont & ~rev
    out = np.where(cont, "CONT", np.where(rev, "REV", np.where(fade, "FADE", "RANGE"))).astype(object)
    bad = (d0 == 0) | ~np.isfinite(d0) | ~np.isfinite(o + c + h + lo + ih + il + pc + atr)
    out[bad] = None
    return out


def merge_rare(freq: dict[str, dict[str, float]], floor: float = 0.08) -> list[str]:
    """O-D4 read by OA-A6.7: the classes (never RANGE) below `floor` in EITHER market, to be merged into RANGE for
    both. `freq` is {market: {label: share}} over the in-sample."""
    rare = set()
    for shares in freq.values():
        for lab in ("CONT", "REV", "FADE"):
            if shares.get(lab, 0.0) < floor:
                rare.add(lab)
    return sorted(rare)
