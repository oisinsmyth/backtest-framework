"""D399 -- THE TWO FREE FIXES TO THE PIVOT CLASSIFIER, measured against the causal ground truth.

    uv run python scripts/d399_signed_vol_segment.py                run the grid + exact nulls
    uv run python scripts/d399_signed_vol_segment.py --selftest     audits only
    uv run python scripts/d399_signed_vol_segment.py --verify-rvol  rvol21 vs the panel's own grid

WHY. `scripts/d399_pivot_classifier_diagnostic.py` measured the incumbent segmenter's cut test --
`abs(r) > tau`, tau = 0.08 log -- on the real GME window and found two defects that need no new
construction to fix:

  FIX 1, SIGN THE RESIDUAL. For a SUPPORT line a pivot ABOVE the line is a HIGHER LOW: the trend
  holding. Below it is a violation. `abs()` cannot tell them apart, and measured, 7 of 14 support
  cuts (50%) and 6 of 14 resistance cuts (43%) fired on a CONFIRMING pivot -- the segmenter killed
  the trend at the moment it was being confirmed.

  FIX 2, NORMALISE THE THRESHOLD. tau is a fixed 8.3% in price. Against what an ordinary random
  walk would produce over the gap since the previous pivot -- `rvol21 * sqrt(gap)` -- that fixed
  number is worth a median 1.19 sigma on support (range 0.42-2.00) and 1.31 on resistance
  (0.61-2.17). The gap at a cut runs 4 to 26 bars and the test charges them the same.

HOW THEY ARE PARAMETERISED, so that the incumbent is a CELL of this grid and not a separate code
path:

  conf_mult   the threshold multiplier applied on the CONFIRMING side only.
              1.0 == the unsigned incumbent (a control, not a candidate)
              inf == cut on violation only
              2, 4 == a confirming pivot must be that much further out to cut
  mode="vol"  thr = max(tau_sigma * rvol21[pivot bar] * sqrt(bars since the previous pivot), floor)
              tau is then in SIGMA, not in log price, and means one thing at every gap.

EVERYTHING ELSE IS HELD AT THE INCUMBENT CELL -- carry = 3, min_piv = 5, delta gate on -- because
the question is what the two fixes are worth, not what a wider search is worth. R13: 52 cells, one
of which is the control, and the null below is read as a best-of-N.

AUDITS.
  [X] conf_mult = 1 and mode = "abs" must reproduce `d399_alt_segment.sliding_events` BIT-IDENTICALLY
      on both sides at three taus and three carries -- and conf_mult = 2 must DIFFER, or the
      parameter is decorative.
  [B] the control cell must re-score to the published causal 0.3175 through this file's own harness,
      or nothing below is comparable to the standing best.
  [L] the lag audit and its k=0 self-test are `d399_alt_segment`'s, called on the new builder.
  [V] rvol21 is rebuilt here from GME's own bars through `ragged_vol_scores._trail`; --verify-rvol
      asserts it is bit-identical to the panel grid the diagnostic read.

Scores nothing else. Admits nothing (R15).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

GT = REPO / "data" / "d399_live_ground_truth.json"
OUT = REPO / "data" / "d399_signed_vol_scores.json"

# the incumbent cell, frozen: slide/abs/tau=0.08/carry=3/min_piv=5/delta-gate
INC_TAU, INC_CARRY, INC_MINPIV, INC_GATE = 0.08, 3, 5, True
PUBLISHED_CAUSAL = 0.3175        # data/d399_causal_scores.json, "segmentation" (the
#                                 RECORDED value; the 0.317 in that run's printed table is 3 dp)

ABS_TAUS = [0.05, 0.08, 0.12]                 # the incumbent and one step either side
VOL_TAUS = [0.75, 1.00, 1.25, 1.50, 2.00]     # in SIGMA; the measured medians were 1.19 / 1.31
VOL_FLOORS = [0.02, 0.04]                     # log price, so a dead-vol stretch cannot cut on noise
CONF_MULTS = [1.0, 2.0, 4.0, float("inf")]    # 1.0 IS THE UNSIGNED CONTROL
N_NULLED = 8


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


SEG = _load("d399seg", "d399_alt_segment.py")
ols = SEG.ols                      # ONE least-squares implementation, not a restatement


# --------------------------------------------------------------------------
# the classifier
# --------------------------------------------------------------------------


def scale_of(cx, cy, b, a, x_new, mode):
    """THE YARDSTICK THE RESIDUAL IS MEASURED IN. One function, so the competing definitions of a
    'far' pivot differ in exactly one place and nothing else.

    The residual here is already the right kind: the new pivot is NOT in the fit when its distance
    is measured, so `r` is a PREDICTION error, not an in-sample one. What was missing is its
    proper standard error. For a prediction at x_new from an OLS fit on n points,

        Var(y_new - y_hat) = sigma^2 * (1 + 1/n + (x_new - xbar)^2 / Sxx)

    and dividing by that is what makes one threshold mean one thing everywhere. The inflation term
    is the honest version of the `rvol21 * sqrt(gap)` I hand-rolled: a pivot far past the fit's
    centre of mass IS harder to predict, and the fit's own geometry already knows by how much --
    including how wide the piece is, which a gap-since-last-pivot cannot see.

        "sd"    sigma alone -- the existing d399_alt_segment path, no inflation
        "pred"  sigma * sqrt(1 + 1/n + (x-xbar)^2/Sxx) -- the textbook prediction se
        "mad"   the same, with sigma replaced by 1.4826 * MAD of the residuals, so the pivots the
                test exists to catch cannot inflate the yardstick that is supposed to catch them
    """
    n = len(cx)
    xs = np.asarray(cx, float)
    ys = np.asarray(cy, float)
    if n >= 3:
        res = ys - (b * xs + a)
        if mode == "mad":
            med = float(np.median(res))
            sigma = 1.4826 * float(np.median(np.abs(res - med)))
        else:
            sigma = float(np.sqrt(float((res * res).sum()) / (n - 2)))
    else:
        sigma = 0.0
    if mode == "sd":
        return sigma
    xbar = float(xs.mean())
    sxx = float(((xs - xbar) ** 2).sum())
    lev = 1.0 + 1.0 / n + (((x_new - xbar) ** 2) / sxx if sxx > 0.0 else 0.0)
    return sigma * math.sqrt(lev)


POOL_MIN = 10          # below this the trailing scale is not estimated; the floor carries the test


def sliding_events_v2(pidx, ppx, k, mode, tau, floor, carry, sign, conf_mult, rvol, nwin=50):
    """Sliding segmentation with a SIGNED and (optionally) VOL-NORMALISED cut test.

    `sign` is the pivot sign: -1 for support (fitted on lows), +1 for resistance. For support a
    POSITIVE residual is above the line = confirming; for resistance a NEGATIVE one is.

    `rvol[j]` is the name's own 21-bar return sd at bar j. It is read at the PIVOT's bar, which the
    segmenter only acts on at pivot + k, so the read is three bars in the past and cannot leak.

    With mode="abs" and conf_mult=1.0 this is `d399_alt_segment.sliding_events`, statement for
    statement -- see [X]."""
    cb, sl, npv, sid, ic = [], [], [], [], []
    cx, cy, pool = [], [], []
    for p in range(len(pidx)):
        x, y = float(pidx[p]), float(ppx[p])
        if len(cx) >= 2:
            b, a = ols(cx, cy)
            if np.isfinite(b):
                r = y - (b * x + a)
                if mode == "abs":
                    thr = tau
                elif mode == "vol":
                    # FIX 2: what an ordinary random walk would do over the gap since the last pivot
                    gap = max(1.0, x - cx[-1])
                    j = int(pidx[p])
                    v = rvol[j] if (0 <= j < rvol.size and np.isfinite(rvol[j])) else 0.0
                    thr = max(tau * float(v) * math.sqrt(gap), floor)
                elif mode == "sd":
                    n = len(cx)
                    if n >= 3:
                        res = np.asarray(cy, float) - (b * np.asarray(cx, float) + a)
                        sd = float(np.sqrt(float((res * res).sum()) / (n - 2)))
                    else:
                        sd = 0.0
                    thr = max(tau * sd, floor)
                elif mode == "trail":
                    # THE YARDSTICK ESTIMATED OFF MORE THAN THE PIECE. `sd`/`pred`/`mad` all take
                    # their scale from the CURRENT piece -- 4 to 7 pivots, ~3 degrees of freedom --
                    # so the scale's own sampling error swamps the variation it exists to correct,
                    # and the test goes bimodal (never cut, or cut on everything). This pools the
                    # last `nwin` out-of-sample residuals ACROSS pieces, which is the same quantity
                    # measured on 10-20x the data. Causal: every residual in the pool was recorded
                    # at a pivot already confirmed.
                    if len(pool) >= POOL_MIN:
                        arr = np.abs(np.asarray(pool[-nwin:], float))
                        thr = max(tau * 1.4826 * float(np.median(arr)), floor)
                    else:
                        thr = max(floor, tau * 1.4826 * 0.0)
                else:
                    thr = max(tau * scale_of(cx, cy, b, a, x, mode), floor)
                pool.append(r)
                # FIX 1: a pivot on the CONFIRMING side has to travel `conf_mult` times as far
                confirming = (r > 0.0) if sign < 0 else (r < 0.0)
                thr_eff = thr * conf_mult if confirming else thr
                if abs(r) > thr_eff:                   # THE CUT
                    cx = cx[-carry:] if carry > 0 else []
                    cy = cy[-carry:] if carry > 0 else []
        cx.append(x)
        cy.append(y)
        b, aa = ols(cx, cy)
        cb.append(int(pidx[p]) + k)
        sl.append(b)
        ic.append(aa)
        npv.append(len(cx))
        sid.append(int(cx[0]))
    return (np.array(cb, int), np.array(sl, float), np.array(npv, int), np.array(sid, int),
            np.array(ic, float))


def broadcast_line(events, m, min_piv, delta_gate, delta):
    """`d399_alt_segment.broadcast`, plus THE LINE ITSELF -- the piece's fit evaluated at bar t, in
    log price. The score only ever needed the slope, so the level has never been drawn. It is what
    the chart shows, and it is the thing the principal actually looks at."""
    cb, sl, npv, sid, ic = events
    G, S = SEG.broadcast((cb, sl, npv, sid), m, min_piv, delta_gate, delta)
    L = np.full(m, np.nan)
    if cb.size:
        t = np.arange(m)
        j = np.clip(np.searchsorted(cb, t, "right") - 1, 0, cb.size - 1)
        with np.errstate(invalid="ignore"):
            lvl = sl[j] * t + ic[j]
        on = np.isfinite(G) & np.isfinite(lvl)
        L[on] = lvl[on]
    return G, L, S


def anchor_line(G, S, body_lo, body_hi, kind, lag=0):
    """THE CONSTRAINT: support must sit UNDER the candle body, resistance OVER it, at every bar.

    The OLS intercept does not respect that and cannot -- a regression puts its line through the
    middle of the pivots, so it crosses bodies by construction. This keeps the OLS GRADIENT and
    throws the OLS intercept away, replacing it with the only intercept that satisfies the
    constraint everywhere in the piece:

        support     c = min over bars s in [seg_start, t-lag] of  log(body_low[s])  - g*s
        resistance  c = max over bars s in [seg_start, t-lag] of  log(body_high[s]) - g*s

    That is the principal's own ratchet, solved in closed form instead of iterated: the line is
    pushed away from price until the trend is respected, and because the whole line shifts by a
    constant, respecting the newest bar cannot break an older one. It touches the most extreme
    body in the piece, which is what makes it a TRENDLINE rather than a regression.

    `lag=0` places the line at bar t using bar t's own body, which is what "support at the time
    step has to be under the body" says. `lag=1` is the tradeable version: the level is knowable at
    the previous close. Both are reported; neither changes the GRADIENT, so neither moves the score.
    """
    m = G.size
    L = np.full(m, np.nan)
    t_all = np.arange(m, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        lb = np.log(body_lo)
        hb = np.log(body_hi)
    for t in range(m):
        g = G[t]
        if not np.isfinite(g) or S[t] < 0:
            continue
        s0 = max(0, int(S[t]))
        end = t - lag
        if end < s0:
            end = s0
        sl = slice(s0, end + 1)
        base = (lb[sl] if kind == "support" else hb[sl]) - g * t_all[sl]
        base = base[np.isfinite(base)]
        if base.size == 0:
            continue
        c = float(base.min()) if kind == "support" else float(base.max())
        L[t] = g * t + c
    return L


def assert_respects_bodies(L, body_lo, body_hi, kind, window, tol=1e-12):
    """[R] The constraint is a PROMISE, so it is asserted, not measured. Support may not sit above
    the body low; resistance may not sit below the body high. Returns the count checked."""
    on = np.isfinite(L) & window
    if not on.any():
        return 0
    lvl = np.exp(L[on])
    ref = (body_lo if kind == "support" else body_hi)[on]
    bad = (lvl > ref * (1 + tol)) if kind == "support" else (lvl < ref * (1 - tol))
    if bad.any():
        i = int(np.flatnonzero(on)[np.flatnonzero(bad)[0]])
        raise AssertionError(
            f"[R] {kind} line breaks the body at bar {i}: line {np.exp(L[i]):.4f} vs body "
            f"{(body_lo if kind == 'support' else body_hi)[i]:.4f} ({int(bad.sum())} bars)")
    return int(on.sum())


def combined_events(idx_lo, lp_lo, idx_hi, lp_hi, k, mode, tau, floor, carry, conf_mult,
                    rvol, nwin=50, share_cuts=True, par_h=None):
    """ONE SEGMENT, TWO LINES -- support and resistance cut together.

    Until now the two sides were segmented in complete isolation: their own pivot series, their own
    buffer, their own cuts. Nothing tied a support line to the resistance line above it, even
    though 79% of the principal's own lines were drawn as PAIRS and he said in terms that the pair
    is the object -- "the pairs will always be broken".

    Here both pivot series are merged into ONE stream in bar order. A piece holds both buffers; a
    cut empties both. Three things become expressible that could not be said before:

      mode="chan"  the residual measured against the CHANNEL'S OWN WIDTH. A pivot 8% off its line
                   is a great deal inside a 10%-wide channel and nothing inside a 60%-wide one --
                   and channel width does not exist until the sides are joined.
      par_h        cut when the two edges stop being PARALLEL, |g_hi - g_lo| > par_h. A channel
                   that is opening or closing has stopped being one channel.
      share_cuts   whether a break on one side ends the other. TRUE is the point of this function;
                   FALSE is the control, and must reproduce the independent segmenter exactly.

    Emits one state per pivot (either side), carrying BOTH lines, so a bar's support and resistance
    always come from the same piece."""
    n_lo, n_hi = len(idx_lo), len(idx_hi)
    stream = ([(int(idx_lo[i]), float(lp_lo[i]), 0) for i in range(n_lo)]
              + [(int(idx_hi[i]), float(lp_hi[i]), 1) for i in range(n_hi)])
    stream.sort(key=lambda t: (t[0], t[2]))          # bar order; a tie puts the low first

    cx = [[], []]                                     # 0 = support (lows), 1 = resistance (highs)
    cy = [[], []]
    pool = [[], []]
    seg_start = None
    cb, g0, i0, n0, g1, i1, n1, sid = [], [], [], [], [], [], [], []
    src = []            # which side's pivot produced this state -- a bar can carry BOTH

    for (bar, y, side) in stream:
        x = float(bar)
        other = 1 - side
        cut = False
        if len(cx[side]) >= 2:
            b, a = ols(cx[side], cy[side])
            if np.isfinite(b):
                r = y - (b * x + a)
                if mode == "abs":
                    thr = tau
                elif mode == "chan":
                    # the width of the channel AT THIS BAR, in log price
                    bo, ao = ols(cx[other], cy[other])
                    if np.isfinite(bo):
                        w = abs((bo * x + ao) - (b * x + a))
                        thr = max(tau * w, floor)
                    else:
                        thr = max(tau * 0.0, floor)
                elif mode == "trail":
                    src = pool[side] if not share_cuts else (pool[0] + pool[1])
                    if len(src) >= POOL_MIN:
                        arr = np.abs(np.asarray(src[-nwin:], float))
                        thr = max(tau * 1.4826 * float(np.median(arr)), floor)
                    else:
                        thr = floor
                else:
                    thr = max(tau * scale_of(cx[side], cy[side], b, a, x, mode), floor)
                pool[side].append(r)
                sgn = -1 if side == 0 else +1          # support fitted on lows, resistance on highs
                confirming = (r > 0.0) if sgn < 0 else (r < 0.0)
                if abs(r) > (thr * conf_mult if confirming else thr):
                    cut = True
        # THE PARALLEL TEST: the channel has stopped being one channel
        if (not cut) and par_h is not None and len(cx[0]) >= 2 and len(cx[1]) >= 2:
            bl, _al = ols(cx[0], cy[0])
            bh, _ah = ols(cx[1], cy[1])
            if np.isfinite(bl) and np.isfinite(bh) and abs(bh - bl) > par_h:
                cut = True
        if cut:
            sides = (0, 1) if share_cuts else (side,)
            for s in sides:
                cx[s] = cx[s][-carry:] if carry > 0 else []
                cy[s] = cy[s][-carry:] if carry > 0 else []
            seg_start = None
        cx[side].append(x)
        cy[side].append(y)
        if seg_start is None:
            seg_start = int(min([v for s in (0, 1) for v in cx[s]] or [x]))
        bl, al = ols(cx[0], cy[0])
        bh, ah = ols(cx[1], cy[1])
        cb.append(bar + k)
        g0.append(bl); i0.append(al); n0.append(len(cx[0]))
        g1.append(bh); i1.append(ah); n1.append(len(cx[1]))
        sid.append(seg_start)
        src.append(side)
    return dict(cb=np.array(cb, int), sid=np.array(sid, int), src=np.array(src, int),
                support=(np.array(g0, float), np.array(i0, float), np.array(n0, int)),
                resistance=(np.array(g1, float), np.array(i1, float), np.array(n1, int)))


def broadcast_combined(ev, kind, m, min_piv, delta_gate, delta):
    """One side of a combined event stream, in the same shape `broadcast_line` returns."""
    cb, sid = ev["cb"], ev["sid"]
    sl, ic, npv = ev[kind]
    return broadcast_line((cb, sl, npv, sid, ic), m, min_piv, delta_gate, delta)


def scripted_events(pidx, ppx, k, carry, cut_at):
    """The same segmenter with the CUT TEST REPLACED BY A SCRIPT: cut at pivot p iff cut_at[p].

    This exists for the classifier null. Everything else -- the OLS, the carry, the confirm-bar
    stamping, the emitted quantities -- is the incumbent's, so a difference in score can only come
    from WHERE the cuts fall, never from how the pieces are fitted or broadcast."""
    cb, sl, npv, sid, ic = [], [], [], [], []
    cx, cy = [], []
    fired = 0
    for p in range(len(pidx)):
        x, y = float(pidx[p]), float(ppx[p])
        if len(cx) >= 2 and cut_at[p]:
            cx = cx[-carry:] if carry > 0 else []
            cy = cy[-carry:] if carry > 0 else []
            fired += 1
        cx.append(x)
        cy.append(y)
        b, aa = ols(cx, cy)
        cb.append(int(pidx[p]) + k)
        sl.append(b)
        ic.append(aa)
        npv.append(len(cx))
        sid.append(int(cx[0]))
    return (np.array(cb, int), np.array(sl, float), np.array(npv, int),
            np.array(sid, int), np.array(ic, float)), fired


def incumbent_cuts(pidx, ppx, k, tau, carry):
    """Where the incumbent cuts, and where it COULD have. Returns (cut, eligible) boolean arrays
    over pivot positions -- the two counts the classifier null has to match."""
    cut = np.zeros(len(pidx), bool)
    elig = np.zeros(len(pidx), bool)
    cx, cy = [], []
    for p in range(len(pidx)):
        x, y = float(pidx[p]), float(ppx[p])
        if len(cx) >= 2:
            b, a = ols(cx, cy)
            if np.isfinite(b):
                elig[p] = True
                if abs(y - (b * x + a)) > tau:
                    cut[p] = True
                    cx = cx[-carry:] if carry > 0 else []
                    cy = cy[-carry:] if carry > 0 else []
        cx.append(x)
        cy.append(y)
    return cut, elig


# --------------------------------------------------------------------------
# rvol21, rebuilt from the name's own bars
# --------------------------------------------------------------------------


def own_rvol21(bars, VS):
    """`ragged_vol_scores`' rvol21 for ONE symbol, off its own contiguous bars.

    Same function, same window, same MIN_FRAC -- so this is the panel grid's row, not a lookalike.
    --verify-rvol proves it."""
    c = np.array([b.bar.close for b in bars], float)
    prev = np.concatenate([[np.nan], c[:-1]])
    with np.errstate(invalid="ignore", divide="ignore"):
        r = np.log(c / prev)
    return VS._trail(r, VS.RVOL_BARS, lambda w: np.nanstd(w, axis=1))


# --------------------------------------------------------------------------
# harness
# --------------------------------------------------------------------------


class H:
    def __init__(self, k=None):
        self.DR = _load("d399draw", "d399_draw_construction.py")
        self.UO = _load("d240", "run_uptrend_onset.py")
        self.RP = _load("rp", "ragged_panel.py")
        self.SEG = SEG
        self.SC = _load("d399causal", "d399_score_causal.py")
        self.VS = _load("vs", "ragged_vol_scores.py")
        from backtest_framework.research.structure import pivots as PV
        from backtest_framework.research.structure import pivots_tie_tolerant as PVT

        self.gt = json.loads(GT.read_text())
        self.start = int(self.gt["start_bar"])
        self.n = int(self.gt["n"])
        self.seen_to = int(self.gt["seen_through"])
        self.first_seen = min(L["drawn_at"] for L in self.gt["lines"])
        self.seen = np.zeros(self.n, bool)
        self.seen[self.first_seen:self.seen_to + 1] = True
        self.g_true = {kd: np.array([np.nan if v is None else v for v in self.gt[f"g_{kd}"]], float)
                       for kd in ("support", "resistance")}
        self.delta = self.DR.DELTA
        # `k` is the pivot half-width AND the D173 confirmation lag, so varying it varies both.
        # The [B] control keeps its own: that assertion pins the PUBLISHED number, computed at
        # UO.K on the strict pivot set, and it must not move when the working k does.
        self.k = int(k) if k is not None else self.UO.K
        self.k_strict = self.UO.K

        self.panel, cleaned = self.RP.load_ragged(*self.DR.MINING, fee_bps=0.0,
                                                  dividend_bound=True)
        self.sym = self.gt["symbol"]
        self.bars = cleaned[self.sym]
        self.m = len(self.bars)
        # THE DEFAULT PIVOT SET IS NOW TIE-TOLERANT. The strict-uniqueness rule discarded 11% of
        # qualifying highs and 20% of lows on this window and accounted for five of the nine
        # pivots the principal marked that the detector missed; relaxing it moves agreement with
        # him from 81% to 91% (data/d399_pivot_ground_truth.json). `pivots` itself is untouched --
        # this is a separate function -- and the STRICT set is still built, because the `[B]`
        # control has to keep reproducing the published 0.3175, which was computed under it.
        self.sign = {"support": -1, "resistance": +1}
        self.piv, self.piv_strict = {}, {}
        for name, fn, kk, store in (("tie-tolerant", PVT, self.k, self.piv),
                                    ("strict", PV, self.k_strict, self.piv_strict)):
            ps = fn(self.bars, kk)
            for kd, sg in self.sign.items():
                idx = np.array([p.index for p in ps if p.sign == sg], dtype=int)
                lp = np.log(np.array([p.price for p in ps if p.sign == sg], float))
                assert idx.size == 0 or np.all(np.diff(idx) > 0), (
                    f"{name} pivot indices not ascending")
                store[kd] = (idx, lp)
        self.n_piv_extra = sum(self.piv[kd][0].size - self.piv_strict[kd][0].size
                               for kd in self.sign)
        # ONLY MEANINGFUL AT THE SAME WINDOW. The strict set is pinned at k_strict so the [B]
        # control cannot drift, so once the working k is overridden the two sets differ by window
        # as well as by tie rule and the count says nothing about either.
        if self.k == self.k_strict:
            assert self.n_piv_extra > 0, (
                "[P] at the same k the tie-tolerant set is no larger than the strict one -- "
                "either the new function is not doing anything or it is not being called")
        else:
            same_k = PVT(self.bars, self.k_strict)
            n_same = sum(1 for p in same_k)
            n_strict = sum(self.piv_strict[kd][0].size for kd in self.sign)
            assert n_same > n_strict, (
                "[P] the tie-tolerant function is not doing anything at k_strict either")
        self.rvol = own_rvol21(self.bars, self.VS)
        self.last_line = {}

    # ---- builders
    def events(self, kd, cfg, strict=False):
        idx, lp = (self.piv_strict if strict else self.piv)[kd]
        return sliding_events_v2(idx, lp, self.k_strict if strict else self.k,
                                 cfg["mode"], cfg["tau"], cfg["floor"],
                                 cfg["carry"], self.sign[kd], cfg["conf_mult"], self.rvol,
                                 nwin=cfg.get("nwin", 50))

    def grads(self, cfg, strict=False):
        out = {}
        for kd in ("support", "resistance"):
            ev = self.events(kd, cfg, strict=strict)
            self.SEG.audit_monotone_events(ev[:4])
            G, L, _S = broadcast_line(ev, self.m, cfg["min_piv"], cfg["gate"], self.delta)
            out[kd] = G
            self.last_line[kd] = L
        return out

    # ---- scoring, through the causal scorer's own functions
    def score(self, Gs):
        cell, sc = {}, []
        for kd in ("support", "resistance"):
            gf = Gs[kd][self.start:self.start + self.n]
            s = self.SC.score_side(gf, self.g_true[kd], self.seen, self.delta)
            cell[kd] = s
            sc.append(s["score"])
        cell["SCORE"] = round(float(np.mean(sc)), 4)
        return cell

    def null(self, Gs):
        nl = {}
        for kd in ("support", "resistance"):
            gf = Gs[kd][self.start:self.start + self.n]
            nl[kd] = self.SC.rotation_null(gf, self.g_true[kd], self.seen, self.delta,
                                           self.first_seen, self.seen_to)
        p50 = float(np.mean([nl[kd]["p50"] for kd in nl]))
        p95 = float(np.mean([nl[kd]["p95"] for kd in nl]))
        return dict(sides=nl, p50=round(p50, 4), p95=round(p95, 4))


# --------------------------------------------------------------------------
# audits
# --------------------------------------------------------------------------


def audit_control_is_identical(h):
    """[X] RIGHT-QUANTITY. The new builder at conf_mult=1 / mode=abs must be the OLD builder,
    bit-identically, over the taus and carries the incumbent lives in -- and conf_mult=2 must
    change something, or the fix is a no-op dressed as a parameter."""
    checked, moved = 0, 0
    for tau in (0.05, 0.08, 0.12):
        for carry in (1, 2, 3):
            for kd in ("support", "resistance"):
                idx, lp = h.piv[kd]
                old = h.SEG.sliding_events(idx, lp, h.k, "abs", tau, 0.0, carry)
                new = sliding_events_v2(idx, lp, h.k, "abs", tau, 0.0, carry,
                                        h.sign[kd], 1.0, h.rvol)
                assert len(new) == 5 and len(old) == 4, "[X] arity moved unexpectedly"
                for o, nw, nm in zip(old, new[:4], ("confirm_bar", "slope", "npiv", "seg_id")):
                    assert o.shape == nw.shape, f"[X] {nm} shape moved at tau={tau} carry={carry}"
                    same = (np.array_equal(o, nw, equal_nan=True) if o.dtype.kind == "f"
                            else np.array_equal(o, nw))
                    assert same, (f"[X] {nm} DIFFERS at tau={tau} carry={carry} {kd} -- the "
                                  f"control is not the incumbent")
                checked += 1
                sgn = sliding_events_v2(idx, lp, h.k, "abs", tau, 0.0, carry,
                                        h.sign[kd], 2.0, h.rvol)
                moved += int(not np.array_equal(old[1], sgn[1], equal_nan=True))
    assert moved > 0, "[X] SELF-TEST FAILED: conf_mult=2 changed nothing -- the parameter is dead"
    return checked, moved


def audit_scale_modes(h):
    """[S] The residual's YARDSTICK is the only thing that may differ between these modes.

    `sd` must still be d399_alt_segment's sd path bit-identically -- the refactor into `scale_of`
    must not have moved it. `pred` must then DIFFER from `sd` (or the leverage inflation is
    arithmetically dead), and `mad` must differ from both."""
    same_sd, diff_pred, diff_mad = 0, 0, 0
    for tau in (1.5, 2.5, 4.0):
        for kd in ("support", "resistance"):
            idx, lp = h.piv[kd]
            old = h.SEG.sliding_events(idx, lp, h.k, "sd", tau, SCALE_FLOOR, INC_CARRY)
            new = sliding_events_v2(idx, lp, h.k, "sd", tau, SCALE_FLOOR, INC_CARRY,
                                    h.sign[kd], 1.0, h.rvol)
            assert np.array_equal(old[1], new[1], equal_nan=True), (
                f"[S] the sd path MOVED at tau={tau} {kd} -- the refactor changed a published path")
            same_sd += 1
            for md, box in (("pred", "p"), ("mad", "m")):
                alt = sliding_events_v2(idx, lp, h.k, md, tau, SCALE_FLOOR, INC_CARRY,
                                        h.sign[kd], 1.0, h.rvol)
                moved = not np.array_equal(new[1], alt[1], equal_nan=True)
                if box == "p":
                    diff_pred += int(moved)
                else:
                    diff_mad += int(moved)
    assert diff_pred > 0, "[S] SELF-TEST FAILED: `pred` == `sd`, the leverage inflation does nothing"
    assert diff_mad > 0, "[S] SELF-TEST FAILED: `mad` == `sd`, the robust scale does nothing"
    return same_sd, diff_pred, diff_mad


def audit_lag(h):
    """[L] `d399_alt_segment`'s causality audit, run on the NEW builder, plus its k=0 self-test."""
    probe = list(range(h.start, h.start + h.n, 7))
    # every mode that carries state or reads an outside series -- `trail` especially, because its
    # scale is a POOL accumulated across pieces and a pool is exactly where a leak would hide
    cfgs = [dict(mode="vol", tau=1.25, floor=0.02, carry=INC_CARRY, conf_mult=4.0, nwin=50),
            dict(mode="pred", tau=2.0, floor=SCALE_FLOOR, carry=INC_CARRY, conf_mult=1.0, nwin=50),
            dict(mode="mad", tau=2.0, floor=SCALE_FLOOR, carry=INC_CARRY, conf_mult=2.0, nwin=50),
            dict(mode="trail", tau=1.5, floor=SCALE_FLOOR, carry=INC_CARRY, conf_mult=1.0,
                 nwin=100)]
    done = 0
    for cfg in cfgs:
        for kd in ("support", "resistance"):
            idx, lp = h.piv[kd]

            def B(i, p, kk, c=cfg, s=h.sign[kd]):
                # [:4] because d399_alt_segment's audit predates the intercept this file emits
                return sliding_events_v2(i, p, kk, c["mode"], c["tau"], c["floor"], c["carry"],
                                         s, c["conf_mult"], h.rvol, nwin=c["nwin"])[:4]

            ev = B(idx, lp, h.k)
            h.SEG.audit_monotone_events(ev)
            G, _S = h.SEG.broadcast(ev, h.m, 2, False, h.delta)
            h.SEG.audit_causality(idx, lp, h.k, B, h.m, probe, G)
            h.SEG.audit_causality_selftest(idx, lp, h.k, B, h.m)
            done += 1
    return len(probe), done


def audit_combined_reduces(h):
    """[C] THE MERGE MACHINERY IS CORRECT.

    With `share_cuts=False` the combined segmenter is the independent one wearing a different
    shape: each side still cuts only itself, so its per-side slope series must be BIT-IDENTICAL to
    `sliding_events_v2`. That isolates the interleave, the shared buffers and the emission from the
    thing actually under test, which is whether SHARING the cut helps.

    And `share_cuts=True` must then DIFFER, or the whole idea is a no-op."""
    same, moved = 0, 0
    for tau in (0.05, 0.08, 0.12):
        for cm in (1.0, 2.0):
            idx_lo, lp_lo = h.piv["support"]
            idx_hi, lp_hi = h.piv["resistance"]
            solo = combined_events(idx_lo, lp_lo, idx_hi, lp_hi, h.k, "abs", tau, 0.0,
                                   INC_CARRY, cm, h.rvol, share_cuts=False)
            shared = combined_events(idx_lo, lp_lo, idx_hi, lp_hi, h.k, "abs", tau, 0.0,
                                     INC_CARRY, cm, h.rvol, share_cuts=True)
            for si, (kind, sg) in enumerate((("support", -1), ("resistance", +1))):
                idx, lp = h.piv[kind]
                ref = sliding_events_v2(idx, lp, h.k, "abs", tau, 0.0, INC_CARRY, sg, cm, h.rvol)
                # the combined stream emits at EVERY pivot on EITHER side, so select on the
                # recorded source side -- a bar can carry a low pivot and a high pivot at once
                keep = solo["src"] == si
                assert np.array_equal(solo["cb"][keep] - h.k, idx), (
                    f"[C] the {kind} rows of the merged stream are not that side's own pivots")
                got = solo[kind][0][keep]
                want = ref[1]
                assert got.size == want.size, (
                    f"[C] {kind} emits {got.size} states, the independent path {want.size}")
                assert np.array_equal(got, want, equal_nan=True), (
                    f"[C] share_cuts=False DIFFERS from the independent segmenter at tau={tau} "
                    f"conf={cm} on {kind} -- the merge machinery is wrong, not the idea")
                same += 1
                moved += int(not np.array_equal(shared[kind][0][keep], want, equal_nan=True))
    assert moved > 0, "[C] SELF-TEST FAILED: sharing the cut changed nothing"
    return same, moved


def classifier_null(h, draws=500, seed=20260909):
    """DOES THE CUT TEST DO ANYTHING AT ALL?

    A control that shares the treatment's nuisance rather than just its count (CLAUDE.md): keep the
    incumbent's OLS, its carry, its min_piv, its delta gate and its EXACT NUMBER OF CUTS PER SIDE,
    and randomise only WHICH eligible pivots the cuts land on. If the incumbent's score sits inside
    that distribution, the score is bought by cutting OFTEN -- by staying short and local -- and not
    by the classifier being right about which pivot broke the trend. That would make every
    refinement of the residual test, these two included, the wrong lever."""
    ctl = dict(mode="abs", tau=INC_TAU, floor=0.0, conf_mult=1.0,
               carry=INC_CARRY, min_piv=INC_MINPIV, gate=INC_GATE)
    obs = h.score(h.grads(ctl))["SCORE"]
    info, rng_ct = {}, {}
    for kd in ("support", "resistance"):
        idx, lp = h.piv[kd]
        cut, elig = incumbent_cuts(idx, lp, h.k, INC_TAU, INC_CARRY)
        info[kd] = (idx, lp, cut, elig)
        rng_ct[kd] = (int(cut.sum()), int(elig.sum()))
    out, fired = [], []
    for d in range(draws):
        Gs, tot_fired = {}, 0
        for si, kd in enumerate(("support", "resistance")):
            idx, lp, cut, elig = info[kd]
            n_cut, _ne = rng_ct[kd]
            # an explicit array seed -- never hash() on a str, which is salted per process (D392)
            rng = np.random.default_rng([seed, si, d])
            pos = np.flatnonzero(elig)
            pick = rng.choice(pos, size=min(n_cut, pos.size), replace=False)
            script = np.zeros(idx.size, bool)
            script[pick] = True
            ev, fd = scripted_events(idx, lp, h.k, INC_CARRY, script)
            tot_fired += fd
            G, _L, _S = broadcast_line(ev, h.m, INC_MINPIV, INC_GATE, h.delta)
            Gs[kd] = G
        out.append(h.score(Gs)["SCORE"])
        fired.append(tot_fired)
    a = np.asarray(out, float)
    return dict(observed=obs, draws=int(a.size),
                incumbent_cuts={kd: rng_ct[kd][0] for kd in rng_ct},
                incumbent_eligible={kd: rng_ct[kd][1] for kd in rng_ct},
                mean_random_cuts_fired=round(float(np.mean(fired)), 1),
                p50=round(float(np.median(a)), 4), p95=round(float(np.quantile(a, .95)), 4),
                max=round(float(a.max()), 4),
                pctile_of_observed=round(float((a < obs).mean()), 4),
                se_p95=round(float(np.std(a) * 1.0 / np.sqrt(a.size)), 4))


def verify_rvol(h):
    """[V] the locally rebuilt rvol21 vs the panel grid `d348_prep` serves. Bit-identical or raise."""
    PREP = _load("d348p", "d348_prep.py")
    P = PREP.prep(need_grids=False, verbose=False)
    i = h.panel.symbols.index(h.sym)
    grid = np.asarray(P["score"]("rvol21"))[i]
    at = np.flatnonzero(h.panel.live[i])
    assert at.size == h.rvol.size, f"[V] {at.size} live bars vs {h.rvol.size} own bars"
    a, b = grid[at], h.rvol
    fin = np.isfinite(a)
    assert np.array_equal(fin, np.isfinite(b)), "[V] finite masks differ"
    assert np.array_equal(a[fin], b[fin]), (
        f"[V] values differ, max {np.max(np.abs(a[fin] - b[fin])):.3e}")
    return int(fin.sum())


# --------------------------------------------------------------------------
# the grid
# --------------------------------------------------------------------------


SD_TAUS = [1.5, 2.0, 2.5, 3.0, 4.0]
PRED_TAUS = [1.0, 1.5, 2.0, 2.5, 3.0]
MAD_TAUS = [1.5, 2.0, 2.5, 3.0, 4.0]
SCALE_FLOOR = 0.02          # the 0.02/0.04 sweep was bit-identical: residuals that small never cut
TRAIL_TAUS = [0.75, 1.00, 1.25, 1.50, 2.00]
TRAIL_WINS = [20, 50, 100]  # pivots pooled into the scale -- the axis this run exists to test


def configs():
    out = []
    for cm in CONF_MULTS:
        for tau in ABS_TAUS:
            out.append(dict(mode="abs", tau=tau, floor=0.0, conf_mult=cm,
                            carry=INC_CARRY, min_piv=INC_MINPIV, gate=INC_GATE))
        for tau in VOL_TAUS:
            for fl in VOL_FLOORS:
                out.append(dict(mode="vol", tau=tau, floor=fl, conf_mult=cm,
                                carry=INC_CARRY, min_piv=INC_MINPIV, gate=INC_GATE))
        for md, taus in (("sd", SD_TAUS), ("pred", PRED_TAUS), ("mad", MAD_TAUS)):
            for tau in taus:
                out.append(dict(mode=md, tau=tau, floor=SCALE_FLOOR, conf_mult=cm,
                                carry=INC_CARRY, min_piv=INC_MINPIV, gate=INC_GATE))
        for nw in TRAIL_WINS:
            for tau in TRAIL_TAUS:
                out.append(dict(mode="trail", tau=tau, floor=SCALE_FLOOR, conf_mult=cm, nwin=nw,
                                carry=INC_CARRY, min_piv=INC_MINPIV, gate=INC_GATE))
    return out


def label(c):
    cm = "1(unsigned)" if c["conf_mult"] == 1.0 else (
        "inf(viol-only)" if math.isinf(c["conf_mult"]) else f"{c['conf_mult']:g}")
    if c["mode"] == "abs":
        base = f"abs/tau={c['tau']:g}"
    elif c["mode"] == "vol":
        base = f"vol/tau={c['tau']:.2f}s,fl={c['floor']:g}"
    elif c["mode"] == "trail":
        base = f"trail{c.get('nwin', 50)}/tau={c['tau']:.2f}s"
    else:
        base = f"{c['mode']}/tau={c['tau']:.2f}s"
    return f"{base}/conf={cm}"


def is_control(c):
    return (c["mode"] == "abs" and c["tau"] == INC_TAU and c["conf_mult"] == 1.0)


CHAN_TAUS = [0.10, 0.15, 0.20, 0.30, 0.45]     # tau as a FRACTION OF THE CHANNEL'S OWN WIDTH
COMB_MIN_PIVS = [3, 5]                          # the semantics changed: a shared piece needs both
PAR_ANNUAL = [None, 12.0, 25.0]                 # |g_hi - g_lo| cut, in annualised percentage points


def combined_configs(h):
    """The combined grid. R13: every axis is declared here and the count is printed."""
    out = []
    for share in (False, True):
        for mp in COMB_MIN_PIVS:
            for cm in (1.0, 2.0):
                for pa in PAR_ANNUAL:
                    ph = None if pa is None else h.DR.h_of_annual(pa)
                    for tau in ABS_TAUS:
                        out.append(dict(mode="abs", tau=tau, floor=0.0, conf_mult=cm,
                                        share_cuts=share, min_piv=mp, par_annual=pa, par_h=ph,
                                        carry=INC_CARRY, gate=INC_GATE, nwin=50))
                    for tau in CHAN_TAUS:
                        out.append(dict(mode="chan", tau=tau, floor=SCALE_FLOOR, conf_mult=cm,
                                        share_cuts=share, min_piv=mp, par_annual=pa, par_h=ph,
                                        carry=INC_CARRY, gate=INC_GATE, nwin=50))
                    for tau in TRAIL_TAUS:
                        out.append(dict(mode="trail", tau=tau, floor=SCALE_FLOOR, conf_mult=cm,
                                        share_cuts=share, min_piv=mp, par_annual=pa, par_h=ph,
                                        carry=INC_CARRY, gate=INC_GATE, nwin=100))
    return out


def comb_label(c):
    if c["mode"] == "abs":
        base = f"abs/tau={c['tau']:g}"
    elif c["mode"] == "chan":
        base = f"chan/tau={c['tau']:g}w"
    else:
        base = f"trail{c['nwin']}/tau={c['tau']:.2f}s"
    par = "-" if c["par_annual"] is None else f"{c['par_annual']:g}%"
    tag = "SHARED" if c["share_cuts"] else "solo"
    return f"{tag:<6s}/{base}/mp={c['min_piv']}/conf={c['conf_mult']:g}/par={par}"


CHART_CELLS = [
    ("alwayson", "BASELINE -- never says 'no trend'",
     dict(mode="abs", tau=INC_TAU, floor=0.0, conf_mult=1.0, min_piv=1, gate=False)),
    ("fixed", "r vs a FIXED 8% -- the incumbent, sides fully independent",
     dict(mode="abs", tau=INC_TAU, floor=0.0, conf_mult=1.0)),
    ("chan_shared", "COMBINED SEGMENT -- one piece, a break on either side ends both",
     dict(mode="chan", tau=0.45, floor=SCALE_FLOOR, conf_mult=1.0, min_piv=5,
          combined=True, share_cuts=True)),
    ("chan_solo", "COMBINED YARDSTICK -- tau is 20% of the CHANNEL'S OWN WIDTH, cuts stay separate",
     dict(mode="chan", tau=0.20, floor=SCALE_FLOOR, conf_mult=2.0, min_piv=5,
          combined=True, share_cuts=False)),
    ("trail100", "r / (robust sd of the last 100 pivots' residuals)",
     dict(mode="trail", tau=1.50, floor=SCALE_FLOOR, conf_mult=1.0, nwin=100)),
]


def placement(level_px, ref_px):
    """WHERE THE LINE SITS relative to the bar it is drawn on, in percent of that bar's own
    high (resistance) or low (support).

    This has never been computed before: every D399 score reads the SLOPE only, so the level was
    unexamined until the construction was drawn. The principal's own lines get the identical
    statistic, and they are the benchmark -- a support line 10% under the low is what HE draws."""
    ok = np.isfinite(level_px) & np.isfinite(ref_px) & (ref_px > 0)
    if not ok.any():
        return None
    g = (level_px[ok] - ref_px[ok]) / ref_px[ok] * 100.0
    return dict(n=int(ok.sum()), median=round(float(np.median(g)), 1),
                p10=round(float(np.percentile(g, 10)), 1),
                p90=round(float(np.percentile(g, 90)), 1))


def human_placement(h, o, hip, lop):
    """The same statistic on the principal's 25 lines, over the bars he actually HELD each one."""
    out = {}
    for kd in ("support", "resistance"):
        lev, ref = [], []
        for L in h.gt["lines"]:
            if L["kind"] != kd:
                continue
            sg = L["segment"]
            a, b = int(L["drawn_at"]), max(int(L["drawn_at"]), int(L["ended_at"]))
            i = np.arange(a, b + 1)
            lev.append(np.exp(np.log(sg["p0"]) + L["g_per_bar"] * (i - sg["i0"])))
            ref.append((lop if kd == "support" else hip)[i])
        out[kd] = placement(np.concatenate(lev), np.concatenate(ref)) if lev else None
    return out


def chart_data(h):
    """Per-bar candles and the DRAWN LINE of each cell over the ground-truth window, plus the
    principal's own 25 lines. The line, not the slope -- see `broadcast_line`."""
    s, n = h.start, h.n
    o = np.array([b.bar.open for b in h.bars], float)[s:s + n]
    hi = np.array([b.bar.high for b in h.bars], float)[s:s + n]
    lo = np.array([b.bar.low for b in h.bars], float)[s:s + n]
    c = np.array([b.bar.close for b in h.bars], float)[s:s + n]
    dates = [str(b.timestamp)[:10] for b in h.bars][s:s + n]
    op_all = np.array([b.bar.open for b in h.bars], float)
    cl_all = np.array([b.bar.close for b in h.bars], float)
    body_lo = np.minimum(op_all, cl_all)          # the principal's own break convention is the
    body_hi = np.maximum(op_all, cl_all)          # BODY, not the wick
    win = np.zeros(h.m, bool)
    win[s:s + n] = True
    cells = []
    for key, blurb, part in CHART_CELLS:
        cfg = dict(dict(carry=INC_CARRY, min_piv=INC_MINPIV, gate=INC_GATE), **part)
        comb = cfg.pop("combined", False)
        if comb:
            idx_lo, lp_lo = h.piv["support"]
            idx_hi, lp_hi = h.piv["resistance"]
            cev = combined_events(idx_lo, lp_lo, idx_hi, lp_hi, h.k, cfg["mode"], cfg["tau"],
                                  cfg["floor"], cfg["carry"], cfg["conf_mult"], h.rvol,
                                  nwin=cfg.get("nwin", 50), share_cuts=cfg["share_cuts"],
                                  par_h=cfg.get("par_h"))
            Gs = {kd: broadcast_combined(cev, kd, h.m, cfg["min_piv"], cfg["gate"], h.delta)[0]
                  for kd in ("support", "resistance")}
        else:
            Gs = h.grads(cfg)
        sc = h.score(Gs)
        lines, grads, cuts, place, reach = {}, {}, {}, {}, {}
        anchored, anchored_lag1, place_anc, n_brk, n_live = {}, {}, {}, {}, {}
        for kd in ("support", "resistance"):
            if comb:
                G, LL, S = broadcast_combined(cev, kd, h.m, cfg["min_piv"], cfg["gate"], h.delta)
            else:
                G, LL, S = broadcast_line(h.events(kd, cfg), h.m, cfg["min_piv"], cfg["gate"],
                                          h.delta)
            # HOW OFTEN THE RAW OLS LINE BREAKS THE BODY -- the thing the anchor exists to fix
            ref = body_lo if kd == "support" else body_hi
            with np.errstate(over="ignore", invalid="ignore"):
                raw = np.exp(LL)
            liv = np.isfinite(raw) & win
            brk = (raw > ref) if kd == "support" else (raw < ref)
            n_brk[kd] = int((brk & liv).sum())
            n_live[kd] = int(liv.sum())

            LA_ = anchor_line(G, S, body_lo, body_hi, kd, lag=0)
            assert_respects_bodies(LA_, body_lo, body_hi, kd, win)
            LA1 = anchor_line(G, S, body_lo, body_hi, kd, lag=1)
            with np.errstate(over="ignore"):
                anchored[kd] = [None if not np.isfinite(v) else float(v)
                                for v in np.exp(LA_[s:s + n])]
                a1 = np.exp(LA1[s:s + n])
            anchored_lag1[kd] = [None if not np.isfinite(v) else float(v) for v in a1]
            place_anc[kd] = placement(np.exp(LA_[s:s + n]), (lo if kd == "support" else hi))
            with np.errstate(over="ignore"):
                px = np.exp(LL[s:s + n])
            lines[kd] = [None if not np.isfinite(v) else float(v) for v in px]
            grads[kd] = [None if not np.isfinite(v) else float(v) for v in G[s:s + n]]
            seg = S[s:s + n]
            cuts[kd] = [int(i) for i in range(1, n) if seg[i] >= 0 and seg[i] != seg[i - 1]]
            place[kd] = placement(px, (lo if kd == "support" else hi))
            live = np.isfinite(px) & (seg >= 0)
            back = (np.arange(s, s + n) - S[s:s + n])[live]
            reach[kd] = int(np.median(back)) if back.size else None
        lab = comb_label(dict(cfg, share_cuts=cfg.get("share_cuts", False),
                              par_annual=None)) if comb else label(cfg)
        cells.append(dict(key=key, blurb=blurb, label=lab, SCORE=sc["SCORE"],
                          delta_vs_control=round(sc["SCORE"] - PUBLISHED_CAUSAL, 4),
                          support=lines["support"], resistance=lines["resistance"],
                          g_support=grads["support"], g_resistance=grads["resistance"],
                          cuts_support=cuts["support"], cuts_resistance=cuts["resistance"],
                          n_cuts=len(cuts["support"]) + len(cuts["resistance"]),
                          placement=place, reach_bars=reach,
                          anchored=anchored, anchored_lag1=anchored_lag1,
                          placement_anchored=place_anc,
                          body_breaks=n_brk, live_bars=n_live,
                          parts={kd: {kk: sc[kd][kk] for kk in
                                      ("TP", "FP", "FN", "precision", "recall", "quality", "score")}
                                 for kd in ("support", "resistance")}))
    # the principal's own lines, in the same window coordinates the candles use. `segment` carries
    # the two clicks; `drawn_at` .. `ended_at` is the stretch he actually HELD it live, and only
    # that stretch is scored -- so both are exported and the page draws them differently.
    drawn = []
    for L in h.gt["lines"]:
        sg = L["segment"]
        drawn.append(dict(id=L["id"], kind=L["kind"], i0=int(sg["i0"]), i1=int(sg["i1"]),
                          p0=float(sg["p0"]), p1=float(sg["p1"]),
                          drawn_at=int(L["drawn_at"]), ended_at=int(L["ended_at"]),
                          g_per_bar=float(L["g_per_bar"]), live_bars=int(L["live_bars"])))
    human_place = human_placement(h, o, hi, lo)
    return dict(symbol=h.sym, start_bar=s, n=n, first_seen=h.first_seen, seen_through=h.seen_to,
                human_placement=human_place,
                dates=dates, open=list(map(float, o)), high=list(map(float, hi)),
                low=list(map(float, lo)), close=list(map(float, c)),
                control_score=PUBLISHED_CAUSAL, cells=cells, drawn=drawn)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--verify-rvol", action="store_true")
    ap.add_argument("--classifier-null", action="store_true")
    ap.add_argument("--combined", action="store_true",
                    help="segment support and resistance in ONE shared piece")
    ap.add_argument("--chart", action="store_true")
    ap.add_argument("--draws", type=int, default=500)
    a = ap.parse_args()

    t0 = time.time()
    h = H()
    print(f"\n  {h.sym} {h.m} bars in {time.time() - t0:.0f}s | pivots "
          f"{h.piv['support'][0].size} low / {h.piv['resistance'][0].size} high | "
          f"rvol21 finite on {int(np.isfinite(h.rvol).sum())} bars")
    print(f"  CAUSAL ground truth: bars {h.first_seen}-{h.seen_to}, {len(h.gt['lines'])} lines, "
          f"median life {h.gt['median_live_bars']:.0f} bars\n")

    ck, mv = audit_control_is_identical(h)
    print(f"  [X] conf_mult=1/mode=abs is BIT-IDENTICAL to d399_alt_segment.sliding_events on "
          f"{ck} (tau, carry, side) combinations -- and conf_mult=2 moves {mv} of them  OK")
    ss, dp, dm = audit_scale_modes(h)
    print(f"  [S] the `sd` yardstick is unmoved by the refactor on {ss} (tau, side) pairs; `pred` "
          f"differs from it on {dp}/{ss} and `mad` on {dm}/{ss}  OK")
    np_, nb = audit_lag(h)
    print(f"  [L] lag audit passes on {np_} bars x {nb} (mode, side) builders -- vol, pred, mad and "
          f"the stateful trail pool -- and RAISES on every k=0 leaked build  OK")
    if a.verify_rvol:
        nf = verify_rvol(h)
        print(f"  [V] rvol21 rebuilt from {h.sym}'s own bars is BIT-IDENTICAL to the panel grid "
              f"on all {nf} finite bars  OK")

    ctl = dict(mode="abs", tau=INC_TAU, floor=0.0, conf_mult=1.0,
               carry=INC_CARRY, min_piv=INC_MINPIV, gate=INC_GATE)
    # the control is pinned to the STRICT pivot set, because that is what produced the
    # published number; the tie-tolerant set is the new default for everything else
    base = h.score(h.grads(ctl, strict=True))
    assert base["SCORE"] == PUBLISHED_CAUSAL, (
        f"[B] the control re-scores to {base['SCORE']}, published {PUBLISHED_CAUSAL} -- nothing "
        f"below is comparable")
    print(f"  [B] the control cell re-scores to {base['SCORE']} == the published causal "
          f"{PUBLISHED_CAUSAL}  OK")
    if a.selftest:
        return 0

    if a.combined:
        cs, cm_moved = audit_combined_reduces(h)
        print(f"  [C] share_cuts=False is BIT-IDENTICAL to the independent segmenter on {cs} "
              f"(tau, conf, side) cases, and sharing the cut moves {cm_moved} of them  OK")
        cfgs = combined_configs(h)
        print(f"\n  {len(cfgs)} combined cells | axes: share_cuts x2, mode x3, tau, "
              f"min_piv {COMB_MIN_PIVS}, conf x2, parallel {PAR_ANNUAL} (R13)")
        print(f"  the independent incumbent, for reference: {PUBLISHED_CAUSAL}\n")
        idx_lo, lp_lo = h.piv["support"]
        idx_hi, lp_hi = h.piv["resistance"]
        rows = []
        for c in cfgs:
            ev = combined_events(idx_lo, lp_lo, idx_hi, lp_hi, h.k, c["mode"], c["tau"],
                                 c["floor"], c["carry"], c["conf_mult"], h.rvol,
                                 nwin=c["nwin"], share_cuts=c["share_cuts"], par_h=c["par_h"])
            Gs = {}
            for kd in ("support", "resistance"):
                G, _L, _S = broadcast_combined(ev, kd, h.m, c["min_piv"], c["gate"], h.delta)
                Gs[kd] = G
            cell = h.score(Gs)
            rows.append(dict(label=comb_label(c), SCORE=cell["SCORE"],
                             share=bool(c["share_cuts"]), mode=c["mode"],
                             min_piv=c["min_piv"], conf=c["conf_mult"],
                             par_annual=c["par_annual"], tau=c["tau"],
                             support=cell["support"], resistance=cell["resistance"]))
        rows.sort(key=lambda r: -r["SCORE"])
        print(f"  {'cell':<48s} {'SCORE':>7s} {'qualS':>6s} {'qualR':>6s} {'precS':>6s} "
              f"{'precR':>6s} {'FP':>5s} {'FN':>5s}")
        for r in rows[:24]:
            s, q = r["support"], r["resistance"]
            print(f"  {r['label']:<48s} {r['SCORE']:>7.4f} {(s['quality'] or 0):>6.3f} "
                  f"{(q['quality'] or 0):>6.3f} {s['precision']:>6.3f} {q['precision']:>6.3f} "
                  f"{s['FP'] + q['FP']:>5d} {s['FN'] + q['FN']:>5d}")
        best_sh = max((r for r in rows if r["share"]), key=lambda r: r["SCORE"])
        best_so = max((r for r in rows if not r["share"]), key=lambda r: r["SCORE"])
        print(f"\n  DOES SHARING THE CUT HELP? -- best of each half, same axes either side")
        print(f"    solo   (each side cuts itself)  {best_so['SCORE']:>7.4f}  {best_so['label']}")
        print(f"    SHARED (a break ends both)      {best_sh['SCORE']:>7.4f}  {best_sh['label']}")
        print(f"    independent incumbent           {PUBLISHED_CAUSAL:>7.4f}")
        for md in ("abs", "chan", "trail"):
            sub = [r for r in rows if r["mode"] == md and r["share"]]
            if sub:
                b = max(sub, key=lambda r: r["SCORE"])
                print(f"    best SHARED {md:<6s}            {b['SCORE']:>7.4f}  {b['label']}")
        P = REPO / "data" / "d399_combined_scores.json"
        P.write_text(json.dumps(dict(
            what="D399: support and resistance segmented in ONE shared piece",
            reference_independent=PUBLISHED_CAUSAL, n_cells=len(rows),
            best_shared=best_sh, best_solo=best_so, grid=rows), indent=1))
        print(f"\n  [P] {P.relative_to(REPO)} written")
        print(f"  BEST-OF-{len(rows)}; the solo half is the matched control, not a second search.")
        return 0

    if a.chart:
        CH = REPO / "temp" / "d399_signed_vol_chart.json"
        cd = chart_data(h)
        CH.parent.mkdir(parents=True, exist_ok=True)
        CH.write_text(json.dumps(cd))
        print(f"\n  {'cell':<12s} {'SCORE':>7s} {'vs ctl':>8s} {'cuts':>5s}  configuration")
        for c in cd["cells"]:
            print(f"  {c['key']:<12s} {c['SCORE']:>7.4f} {c['delta_vs_control']:>+8.4f} "
                  f"{c['n_cuts']:>5d}  {c['label']}")
        print(f"\n  [P] {CH.relative_to(REPO)} written ({cd['n']} bars, {len(cd['drawn'])} drawn "
              f"lines)")
        return 0

    if a.classifier_null:
        t1 = time.time()
        cn = classifier_null(h, draws=a.draws)
        print(f"\n  CLASSIFIER NULL -- the incumbent's cuts MOVED TO RANDOM ELIGIBLE PIVOTS")
        print(f"  everything else identical: same OLS, same carry={INC_CARRY}, "
              f"min_piv={INC_MINPIV}, delta gate, and the same NUMBER of cuts per side")
        print(f"  incumbent cuts {cn['incumbent_cuts']} of eligible {cn['incumbent_eligible']}; "
              f"the random scripts fire {cn['mean_random_cuts_fired']} on average")
        print(f"\n  observed (the incumbent)      {cn['observed']:.4f}")
        print(f"  random-placement p50           {cn['p50']:.4f}")
        print(f"  random-placement p95           {cn['p95']:.4f}  (SE {cn['se_p95']:.4f}, "
              f"{cn['draws']} draws -- SAMPLED, so this p95 is biased toward the centre)")
        print(f"  random-placement max           {cn['max']:.4f}")
        print(f"  the incumbent sits at the {100 * cn['pctile_of_observed']:.1f}th percentile "
              f"of its own cut-count-matched random control")
        verdict = ("THE CUT TEST IS DOING WORK" if cn["observed"] > cn["p95"]
                   else "THE CUT TEST IS NOT SEPARABLE FROM CUTTING AT THAT RATE")
        print(f"  -> {verdict}")
        (REPO / "data" / "d399_classifier_null.json").write_text(json.dumps(cn, indent=1))
        print(f"  [P] data/d399_classifier_null.json written ({time.time() - t1:.0f}s)")
        return 0

    cfgs = configs()
    print(f"\n  {len(cfgs)} cells (carry={INC_CARRY}, min_piv={INC_MINPIV}, delta gate on -- "
          f"HELD at the incumbent, so only the two fixes vary)\n")
    print(f"  {'cell':<34s} {'SCORE':>7s} {'qualS':>6s} {'qualR':>6s} {'precS':>6s} {'recS':>6s} "
          f"{'precR':>6s} {'recR':>6s} {'FP':>5s} {'FN':>5s}")
    rows = []
    for c in cfgs:
        Gs = h.grads(c)
        cell = h.score(Gs)
        s, r = cell["support"], cell["resistance"]
        rows.append(dict(label=label(c), cfg={kk: (None if isinstance(vv, float) and math.isinf(vv)
                                                   else vv) for kk, vv in c.items()},
                         conf_mult=("inf" if math.isinf(c["conf_mult"]) else c["conf_mult"]),
                         control=is_control(c), SCORE=cell["SCORE"],
                         support=s, resistance=r))
        print(f"  {label(c):<34s} {cell['SCORE']:>7.4f} {(s['quality'] or 0):>6.3f} "
              f"{(r['quality'] or 0):>6.3f} {s['precision']:>6.3f} {s['recall']:>6.3f} "
              f"{r['precision']:>6.3f} {r['recall']:>6.3f} {s['FP'] + r['FP']:>5d} "
              f"{s['FN'] + r['FN']:>5d}"
              + ("   <- CONTROL (the incumbent)" if is_control(c) else ""))

    rows.sort(key=lambda x: -x["SCORE"])
    print(f"\n  RANKED. control {PUBLISHED_CAUSAL}; best {rows[0]['label']} {rows[0]['SCORE']:.4f} "
          f"({rows[0]['SCORE'] - PUBLISHED_CAUSAL:+.4f})")

    # ---- what each fix is worth ON ITS OWN, which is the question that was asked
    def best_where(pred):
        sub = [r for r in rows if pred(r)]
        return max(sub, key=lambda r: r["SCORE"]) if sub else None

    f1 = best_where(lambda r: r["cfg"]["mode"] == "abs" and r["conf_mult"] != 1.0)
    f2 = best_where(lambda r: r["cfg"]["mode"] == "vol" and r["conf_mult"] == 1.0)
    f12 = best_where(lambda r: r["cfg"]["mode"] == "vol" and r["conf_mult"] != 1.0)
    print(f"\n  EACH FIX ON ITS OWN (everything else at the incumbent)")
    print(f"  {'neither (the control)':<40s} {PUBLISHED_CAUSAL:>7.4f}")
    for nm, r in (("FIX 1 only  (signed, fixed tau)", f1),
                  ("FIX 2 only  (unsigned, vol-normalised)", f2),
                  ("BOTH", f12)):
        if r:
            print(f"  {nm:<40s} {r['SCORE']:>7.4f} {r['SCORE'] - PUBLISHED_CAUSAL:>+8.4f}   "
                  f"{r['label']}")

    # ---- exact rotation nulls on the top cells and on the control
    print(f"\n  EXACT TIME-ROTATION NULLS (every offset in the seen window enumerated; SE of p95 = 0)")
    print(f"  {'cell':<34s} {'SCORE':>7s} {'p50':>7s} {'p95':>7s} {'clears?':>9s}")
    nulls = []
    seen_lbl = set()
    for r in rows[:N_NULLED] + [x for x in rows if x["control"]]:
        if r["label"] in seen_lbl:
            continue
        seen_lbl.add(r["label"])
        cfg = dict(r["cfg"])
        cfg["conf_mult"] = float("inf") if cfg["conf_mult"] is None else cfg["conf_mult"]
        nu = h.null(h.grads(cfg))
        nu.update(label=r["label"], observed=r["SCORE"], clears=bool(r["SCORE"] > nu["p95"]),
                  control=r["control"])
        nulls.append(nu)
        print(f"  {r['label']:<34s} {r['SCORE']:>7.4f} {nu['p50']:>7.4f} {nu['p95']:>7.4f} "
              f"{('CLEARS' if nu['clears'] else 'inside'):>9s}"
              + ("   <- CONTROL" if r["control"] else ""))

    res = dict(what="D399: sign the residual, normalise the threshold -- vs the causal ground truth",
               ground_truth=str(GT.relative_to(REPO)), symbol=h.sym,
               held=dict(carry=INC_CARRY, min_piv=INC_MINPIV, delta_gate=INC_GATE),
               control_label=label(ctl), control_score=PUBLISHED_CAUSAL,
               n_cells=len(rows), best=rows[0], nulls=nulls, grid=rows)
    OUT.write_text(json.dumps(res, indent=1))
    print(f"\n  [P] {OUT.relative_to(REPO)} written")
    print(f"  BEST-OF-{len(rows)} over a grid whose control is one cell -- read the margin against "
          f"the null above, not on its own (R13, R14).")
    print("\nNothing is admitted (R15).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
