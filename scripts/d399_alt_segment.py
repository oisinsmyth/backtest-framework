"""D399 -- PIECEWISE-LINEAR SEGMENTATION of the confirmed-pivot series, scored against the
principal's hand-drawn lines.

    uv run python scripts/d399_alt_segment.py                 the whole grid + the exact null
    uv run python scripts/d399_alt_segment.py --selftest      only the audits

WHAT IS DIFFERENT HERE. Every D399 branch so far grows ONE window forward and asks "has the
gradient moved by more than h?" -- the test is on the FITTED SLOPE. This file asks the
segmentation question instead: cut the pivot series into linear pieces, and the test is on the
RESIDUAL of the next pivot against the piece it would join. A slope can drift a long way without
any pivot ever sitting far off the line (a gentle bend), and a slope can be stable while a pivot
lands far off it (a break). The two tests are not the same test.

TWO SEGMENTERS, both causal:

  SLIDING (`sliding_events`)   maintain the current piece; when a newly CONFIRMED pivot's residual
                               against the piece's OLS fit exceeds the threshold, close the piece
                               and open the next one. Threshold is either an absolute log-residual
                               (`abs`) or a multiple of the piece's own residual sd (`sd`, floored,
                               because a 2-point piece has sd exactly 0 and would cut on anything).
                               `carry` is how many trailing pivots of the closed piece seed the new
                               one -- carry=1 starts at the offender alone, carry=2 lets the new
                               piece have a slope immediately.

  BOTTOM-UP (`bottomup_events`)  over a trailing buffer of the last `buf` CONFIRMED pivots: start
                               from adjacent pairs, repeatedly merge the cheapest adjacent pair
                               (cost = max |residual| of the merged piece, the same units as the
                               sliding threshold) until the cheapest merge exceeds `tau`. The
                               gradient is the LAST piece's OLS slope. It re-segments from scratch
                               at every new pivot, so it can revise history -- but only history it
                               was already allowed to see.

CAUSALITY. A pivot at index p is knowable at p + k (k = 3, D173). Both segmenters consume pivots
in ascending index and stamp each resulting state with `confirm_bar = p + k`; the state at bar t is
the last state whose confirm_bar <= t. `audit_causality` re-derives G at sampled bars from a SECOND
implementation that rebuilds the segmentation from the truncated pivot list `index <= t - k` and
never calls the broadcast path -- and `audit_causality_selftest` checks that audit RAISES on a
deliberately leaked (k = 0) build, because a self-test that cannot fail is worse than none.

THE SCORE is not restated here. `human_mask` and `score_side` are imported from
`scripts/d399_score_against_drawn.py` and called, so this file cannot drift from the definition;
`assert_matches_scorer` re-scores branch E (min_piv 3, h 4%/yr) through this harness and asserts
it reproduces the published 0.2363 before any grid runs.

NULL. The best cell is put against the EXACT time rotation of its own gradient series inside the
260-bar window -- all 259 non-zero offsets enumerated, so the p95 has SE exactly 0 (CLAUDE.md's
rule for a finite, small null group). Rotating G keeps the construction's coverage and slope
distribution and destroys only the alignment to the drawn lines.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

GT = REPO / "data" / "d399_drawn_ground_truth.json"
OUT = REPO / "temp" / "d399_alt_segment_grid.json"
PUBLISHED_BRANCH_E = 0.2363     # data/d399_vs_drawn.json, branch E / min_piv 3 / h 4%/yr


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


# --------------------------------------------------------------------------
# least squares on a piece
# --------------------------------------------------------------------------


def ols(x, y):
    """(slope, intercept) of y on x. nan when fewer than two distinct x."""
    n = len(x)
    if n < 2:
        return np.nan, np.nan
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    xm = x.mean()
    dx = x - xm
    den = float((dx * dx).sum())
    if den <= 0.0:
        return np.nan, np.nan
    ym = y.mean()
    b = float((dx * (y - ym)).sum() / den)
    return b, float(ym - b * xm)


def max_abs_resid(x, y):
    """Cost of a piece: the worst |residual| of its own OLS fit, in log price. Zero for a
    piece of one or two points, which is what makes bottom-up start from pairs."""
    if len(x) <= 2:
        return 0.0
    b, a = ols(x, y)
    if not np.isfinite(b):
        return 0.0
    return float(np.max(np.abs(np.asarray(y, float) - (b * np.asarray(x, float) + a))))


# --------------------------------------------------------------------------
# the two segmenters -- both emit one state per CONFIRMED pivot
# --------------------------------------------------------------------------


def sliding_events(pidx, ppx, k, mode, tau, floor, carry):
    """Causal sliding-window segmentation. Returns (confirm_bar, slope, npiv, seg_id) arrays.

    `seg_id` is the pivot INDEX of the piece's first pivot -- a stable name for the piece that
    both segmenters can share, so segment lengths are measured the same way for each."""
    cb, sl, npv, sid = [], [], [], []
    cx, cy = [], []
    for p in range(len(pidx)):
        x, y = float(pidx[p]), float(ppx[p])
        if len(cx) >= 2:
            b, a = ols(cx, cy)
            if np.isfinite(b):
                r = y - (b * x + a)
                if mode == "abs":
                    thr = tau
                else:
                    n = len(cx)
                    if n >= 3:
                        res = np.asarray(cy, float) - (b * np.asarray(cx, float) + a)
                        sd = float(np.sqrt(float((res * res).sum()) / (n - 2)))
                    else:
                        sd = 0.0
                    thr = max(tau * sd, floor)
                if abs(r) > thr:                       # THE CUT
                    cx = cx[-carry:] if carry > 0 else []
                    cy = cy[-carry:] if carry > 0 else []
        cx.append(x)
        cy.append(y)
        b, _a = ols(cx, cy)
        cb.append(int(pidx[p]) + k)
        sl.append(b)
        npv.append(len(cx))
        sid.append(int(cx[0]))
    return (np.array(cb, int), np.array(sl, float), np.array(npv, int), np.array(sid, int))


def _bottomup(x, y, tau):
    """Keogh bottom-up over one buffer. Returns the pieces as [start, end] index pairs."""
    n = len(x)
    if n == 0:
        return []
    segs = [[i, min(i + 1, n - 1)] for i in range(0, n, 2)]
    if len(segs) >= 2 and segs[-1][0] == segs[-2][1]:      # odd n: last point is its own piece
        segs[-1] = [segs[-1][0], segs[-1][0]]
    while len(segs) > 1:
        costs = [max_abs_resid(x[segs[i][0]:segs[i + 1][1] + 1],
                               y[segs[i][0]:segs[i + 1][1] + 1])
                 for i in range(len(segs) - 1)]
        j = int(np.argmin(costs))
        if costs[j] > tau:
            break
        segs[j] = [segs[j][0], segs[j + 1][1]]
        del segs[j + 1]
    return segs


def bottomup_events(pidx, ppx, k, tau, buf):
    """Bottom-up merge over a TRAILING BUFFER of confirmed pivots -- re-segmented from scratch at
    every new pivot, but never over a pivot the bar could not see."""
    cb, sl, npv, sid = [], [], [], []
    x_all = pidx.astype(float)
    for p in range(len(pidx)):
        lo = max(0, p - buf + 1)
        x = x_all[lo:p + 1]
        y = ppx[lo:p + 1]
        segs = _bottomup(x, y, tau)
        s, e = segs[-1]
        b, _a = ols(x[s:e + 1], y[s:e + 1])
        cb.append(int(pidx[p]) + k)
        sl.append(b)
        npv.append(e - s + 1)
        sid.append(int(x[s]))
    return (np.array(cb, int), np.array(sl, float), np.array(npv, int), np.array(sid, int))


# --------------------------------------------------------------------------
# events -> per-bar gradient
# --------------------------------------------------------------------------


def broadcast(events, m, min_piv, delta_gate, delta):
    """The state at bar t is the last event with confirm_bar <= t. No trend where the piece holds
    fewer than `min_piv` pivots, and (optionally) where |slope| <= delta -- 'in those spaces we
    just don't trend'."""
    cb, sl, npv, sid = events
    G = np.full(m, np.nan)
    S = np.full(m, -1, int)
    if cb.size == 0:
        return G, S
    t = np.arange(m)
    j = np.searchsorted(cb, t, "right") - 1
    ok = j >= 0
    jj = np.clip(j, 0, cb.size - 1)
    g = np.where(ok, sl[jj], np.nan)
    n = np.where(ok, npv[jj], 0)
    keep = ok & np.isfinite(g) & (n >= min_piv)
    if delta_gate:
        keep &= np.abs(g) > delta
    G[keep] = g[keep]
    S[keep] = sid[jj][keep]
    return G, S


def segment_lengths(S, sl_window):
    """Bars per piece, inside the scored window, counting only bars that carry a trend. The
    human's drawn segments span 10-78 bars, median 45; this is the like-for-like number."""
    s = S[sl_window]
    out, i, n = [], 0, s.size
    while i < n:
        if s[i] < 0:
            i += 1
            continue
        j = i
        while j + 1 < n and s[j + 1] == s[i]:
            j += 1
        out.append(j - i + 1)
        i = j + 1
    return out


# --------------------------------------------------------------------------
# audits
# --------------------------------------------------------------------------


def audit_causality(kind_pidx, kind_ppx, k, builder, m, bars_to_check, G):
    """LAG AUDIT. Re-derive the gradient at sampled bars from a SECOND path: truncate the pivot
    list to `index <= t - k`, rebuild the segmentation on that alone, and take the LAST event's
    slope. Never touches `broadcast`. Raises on any mismatch."""
    for t in bars_to_check:
        vis = kind_pidx <= t - k
        if not vis.any():
            continue
        cb, sl, npv, sid = builder(kind_pidx[vis], kind_ppx[vis], k)
        want = sl[-1] if cb.size and cb[-1] <= t else np.nan
        got_npiv = npv[-1] if cb.size else 0
        have = G[t]
        if np.isnan(have):
            continue                       # gated off by min_piv / delta -- the audit below covers it
        if not (np.isfinite(want) and abs(want - have) <= 1e-12 * max(1.0, abs(want))):
            raise AssertionError(
                f"LAG AUDIT FAILED at bar {t}: broadcast says {have!r}, the truncated rebuild "
                f"says {want!r} (piece had {got_npiv} pivots)")
    return True


def audit_causality_selftest(pidx, ppx, k, builder, m):
    """The audit must RAISE on a deliberately leaked book. Build G with lag 0 (every pivot usable
    on its own bar) and hand it to an audit that expects lag k; if that passes, the audit is
    decorative."""
    leaked = builder(pidx, ppx, 0)
    G_leak, _S = broadcast(leaked, m, 2, False, 1e-3)
    probe = [t for t in range(200, m, 97)]
    try:
        audit_causality(pidx, ppx, k, builder, m, probe, G_leak)
    except AssertionError:
        return True
    raise AssertionError("SELF-TEST FAILED: the lag audit accepted a k=0 (leaked) gradient")


def audit_monotone_events(events):
    """RIGHT-QUANTITY. Confirm bars must be non-decreasing (the broadcast searchsorted assumes
    it), every piece must hold >= 1 pivot, and a piece's id must be <= its confirm bar."""
    cb, sl, npv, sid = events
    assert np.all(np.diff(cb) >= 0), "confirm bars not sorted"
    assert np.all(npv >= 1), "a piece with no pivots"
    assert np.all(sid <= cb), "a piece named by a pivot it cannot have seen"
    return True


# --------------------------------------------------------------------------
# scoring harness -- the scorer's OWN functions, not a restatement
# --------------------------------------------------------------------------


class Harness:
    def __init__(self):
        self.DR = _load("d399draw", "d399_draw_construction.py")
        self.UO = _load("d240_uptrend", "run_uptrend_onset.py")
        self.RP = _load("ragged_panel", "ragged_panel.py")
        self.SC = _load("d399score", "d399_score_against_drawn.py")
        from backtest_framework.research.structure import pivots as PV

        self.gt = json.loads(GT.read_text())
        self.start = int(self.gt["start_bar"])
        self.n = int(self.gt["n"])
        self.sl = slice(self.start, self.start + self.n)
        self.delta = self.DR.DELTA
        self.k = self.UO.K

        panel, cleaned = self.RP.load_ragged(*self.DR.MINING, fee_bps=0.0, dividend_bound=True)
        bars = cleaned[self.gt["symbol"]]
        self.m = len(bars)
        self.hi = np.array([b.bar.high for b in bars], float)
        self.lo = np.array([b.bar.low for b in bars], float)
        ps = PV(bars, self.k)
        self.piv = {}
        for kind, sign in (("support", -1), ("resistance", +1)):
            idx = np.array([p.index for p in ps if p.sign == sign], dtype=int)
            lp = np.log(np.array([p.price for p in ps if p.sign == sign], float))
            assert idx.size == 0 or np.all(np.diff(idx) > 0), "pivot indices not ascending"
            self.piv[kind] = (idx, lp)
        self.px = {"support": np.log(self.lo), "resistance": np.log(self.hi)}
        self.mask = {}
        for kind in ("support", "resistance"):
            hon, hg, _lvl = self.SC.human_mask(self.gt["lines"], self.n, kind)
            self.mask[kind] = (hon, hg)

    def score_G(self, kind, G):
        """One side, through the scorer's own `score_side`."""
        hon, hg = self.mask[kind]
        Gw = G[self.sl]
        both = hon & np.isfinite(Gw)
        return self.SC.score_side(Gw, hg, both, int(hon.sum()), self.delta)

    def assert_matches_scorer(self):
        """Branch E, min_piv 3, h 4%/yr, re-scored through this harness must reproduce the
        published 0.2363 to the printed precision. If it does not, every number below is
        incomparable to the standing best and nothing else in this file may be believed."""
        h = self.DR.h_of_annual(4.0)
        parts = {}
        for kind, widen in (("support", -1), ("resistance", +1)):
            idx, lp = self.piv[kind]
            G, _L, _anc, _win = self.DR.segment_windows(
                idx, lp, self.px[kind], self.m, self.k, h, widen,
                min_piv=3, max_window=self.UO.WINDOW)
            parts[kind] = self.score_G(kind, G)
        tot = round(float(np.mean([parts[k]["score"] for k in parts])), 4)
        assert tot == PUBLISHED_BRANCH_E, (
            f"HARNESS MISMATCH: branch E rescores to {tot}, published {PUBLISHED_BRANCH_E}")
        return tot, parts


# --------------------------------------------------------------------------
# the grid
# --------------------------------------------------------------------------

ABS_TAUS = [0.02, 0.03, 0.05, 0.08, 0.12, 0.20, 0.30, 0.40, 0.50, 0.75, 1.00, 1e9]
#                                                                              ^^^^
# 1e9 is the NEVER-CUT CONTROL, and it is in the grid deliberately. It is the same code path with
# the segmentation switched off: one piece that opens at the first pivot and grows forever, i.e.
# an expanding-window OLS. If the score keeps climbing to it, the score is rewarding NOT
# segmenting, and any "best threshold" below it is an artefact of where the grid stopped.
SD_TAUS = [1.5, 2.0, 2.5, 3.0, 4.0]
SD_FLOORS = [0.03, 0.06]
CARRIES = [1, 2, 3]
MIN_PIVS = [2, 3, 4, 5]
DELTA_GATES = [False, True]
BU_TAUS = [0.02, 0.05, 0.10, 0.20, 0.40, 0.75]
BU_BUFS = [12, 20, 30]
N_NULLED = 10             # top cells put against their own exact rotation null


def configs():
    out = []
    for carry in CARRIES:
        for tau in ABS_TAUS:
            out.append(dict(method="slide", mode="abs", tau=tau, floor=None, carry=carry))
        for tau in SD_TAUS:
            for fl in SD_FLOORS:
                out.append(dict(method="slide", mode="sd", tau=tau, floor=fl, carry=carry))
    for buf in BU_BUFS:
        for tau in BU_TAUS:
            out.append(dict(method="bottomup", mode="maxres", tau=tau, floor=None, buf=buf))
    return out


def build_events(H, kind, cfg):
    idx, lp = H.piv[kind]
    if cfg["method"] == "slide":
        return sliding_events(idx, lp, H.k, cfg["mode"], cfg["tau"], cfg["floor"] or 0.0,
                              cfg["carry"])
    return bottomup_events(idx, lp, H.k, cfg["tau"], cfg["buf"])


def label(cfg, min_piv, gate):
    if cfg["method"] == "slide":
        base = (f"slide/{cfg['mode']}/tau={cfg['tau']:g}"
                + (f",fl={cfg['floor']:g}" if cfg["mode"] == "sd" else "")
                + f"/carry={cfg['carry']}")
    else:
        base = f"bottomup/buf={cfg['buf']}/tau={cfg['tau']:g}"
    return f"{base}/min_piv={min_piv}/gate={'Y' if gate else 'N'}"


def exact_rotation_null(H, Gs):
    """EXACT time rotation of the gradient series inside the scored window: all 259 non-zero
    offsets, so the p95 carries SE exactly 0. The rotation preserves coverage and the whole slope
    distribution and destroys only the alignment to the drawn lines."""
    scores = []
    for d in range(1, H.n):
        tot = []
        for kind in ("support", "resistance"):
            Gw = np.roll(Gs[kind][H.sl], d)
            full = np.full(H.m, np.nan)
            full[H.sl] = Gw
            tot.append(H.score_G(kind, full)["score"])
        scores.append(float(np.mean(tot)))
    s = np.array(scores)
    return dict(n_offsets=int(s.size), p50=round(float(np.median(s)), 4),
                p95=round(float(np.quantile(s, 0.95)), 4),
                max=round(float(s.max()), 4), se_p95=0.0, scores=s)


def null_of(H, cfg, min_piv, gate):
    Gs = {}
    for kind in ("support", "resistance"):
        ev = build_events(H, kind, cfg)
        Gs[kind], _S = broadcast(ev, H.m, min_piv, gate, H.delta)
    return exact_rotation_null(H, Gs)


def per_line_report(H, Gs):
    """LOOK AT THE OBJECT. A headline AGREEMENT of 0.76 can be one steep drawn leg carrying the
    mean while the shallow legs contribute nothing, so every drawn line is reported on its own:
    how many of its bars the construction speaks on, and what it agrees to there."""
    out = []
    for L in H.gt["lines"]:
        a, b = int(L["i0"]), int(L["i1"])
        gd = float(L["g_per_bar"])
        Gw = Gs[L["kind"]][H.sl][a:b + 1]
        on = np.isfinite(Gw)
        if on.any():
            rel = np.abs(Gw[on] - gd) / max(abs(gd), H.delta)
            agr = float(np.clip(1.0 - rel, 0.0, None).mean())
            med = float(np.median(Gw[on]))
        else:
            agr, med = 0.0, float("nan")
        out.append(dict(kind=L["kind"], i0=a, i1=b, bars=b - a + 1,
                        g_drawn=round(gd, 6), overlap=int(on.sum()),
                        median_g_fit=(round(med, 6) if np.isfinite(med) else None),
                        agreement=round(agr, 4)))
    return out


def branch_E_G(H, min_piv=3, h_annual=4.0):
    h = H.DR.h_of_annual(h_annual)
    Gs = {}
    for kind, widen in (("support", -1), ("resistance", +1)):
        idx, lp = H.piv[kind]
        G, _L, _a, _w = H.DR.segment_windows(idx, lp, H.px[kind], H.m, H.k, h, widen,
                                             min_piv=min_piv, max_window=H.UO.WINDOW)
        Gs[kind] = G
    return Gs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true", help="run only the audits")
    a = ap.parse_args()

    t0 = time.time()
    H = Harness()
    print(f"  loaded {H.gt['symbol']} {H.m} bars in {time.time() - t0:.0f}s; "
          f"pivots {H.piv['support'][0].size} low / {H.piv['resistance'][0].size} high\n")

    tot, parts = H.assert_matches_scorer()
    print(f"  [assert_matches_scorer] branch E rescores to {tot} == published "
          f"{PUBLISHED_BRANCH_E}  OK")

    # ---- audits, on a mid-grid configuration of each segmenter
    probe = list(range(H.start, H.start + H.n, 7))
    for name, cfg in (("slide", dict(method="slide", mode="abs", tau=0.05, floor=None, carry=2)),
                      ("bottomup", dict(method="bottomup", mode="maxres", tau=0.05, buf=20))):
        for kind in ("support", "resistance"):
            idx, lp = H.piv[kind]
            if cfg["method"] == "slide":
                def B(i, p, kk, c=cfg):
                    return sliding_events(i, p, kk, c["mode"], c["tau"], c["floor"] or 0.0,
                                          c["carry"])
            else:
                def B(i, p, kk, c=cfg):
                    return bottomup_events(i, p, kk, c["tau"], c["buf"])
            ev = B(idx, lp, H.k)
            audit_monotone_events(ev)
            G, _S = broadcast(ev, H.m, 2, False, H.delta)
            audit_causality(idx, lp, H.k, B, H.m, probe, G)
            audit_causality_selftest(idx, lp, H.k, B, H.m)
        print(f"  [audit] {name}: lag audit passes on {len(probe)} bars x2 sides, and RAISES on "
              f"the k=0 leaked build  OK")
    if a.selftest:
        return 0

    # ---- the grid
    human_lens = [int(L["i1"]) - int(L["i0"]) + 1 for L in H.gt["lines"]]
    rows = []
    cfgs = configs()
    print(f"\n  {len(cfgs)} segmentations x {len(MIN_PIVS)} min_piv x {len(DELTA_GATES)} gate "
          f"= {len(cfgs) * len(MIN_PIVS) * len(DELTA_GATES)} cells\n")
    for cfg in cfgs:
        ev = {kind: build_events(H, kind, cfg) for kind in ("support", "resistance")}
        for e in ev.values():
            audit_monotone_events(e)
        for mp in MIN_PIVS:
            for gate in DELTA_GATES:
                Gs, Ss, cells = {}, {}, {}
                for kind in ("support", "resistance"):
                    G, S = broadcast(ev[kind], H.m, mp, gate, H.delta)
                    Gs[kind], Ss[kind] = G, S
                    cells[kind] = H.score_G(kind, G)
                lens = (segment_lengths(Ss["support"], H.sl)
                        + segment_lengths(Ss["resistance"], H.sl))
                rows.append(dict(
                    label=label(cfg, mp, gate), cfg=dict(cfg), min_piv=mp, gate=bool(gate),
                    SCORE=round(float(np.mean([cells[k]["score"] for k in cells])), 4),
                    sup=cells["support"], res=cells["resistance"],
                    n_segments=len(lens),
                    median_seg_bars=(float(np.median(lens)) if lens else None),
                    mean_seg_bars=(round(float(np.mean(lens)), 1) if lens else None)))
    rows.sort(key=lambda r: -r["SCORE"])

    print(f"  {'configuration':<48s} {'SCORE':>7s} {'agrS':>6s} {'recS':>6s} {'agrR':>6s} "
          f"{'recR':>6s} {'nseg':>5s} {'medbars':>8s}")
    for r in rows:
        print(f"  {r['label']:<48s} {r['SCORE']:>7.4f} "
              f"{(r['sup']['agreement'] or 0):>6.3f} {r['sup']['recall']:>6.3f} "
              f"{(r['res']['agreement'] or 0):>6.3f} {r['res']['recall']:>6.3f} "
              f"{r['n_segments']:>5d} "
              f"{(r['median_seg_bars'] if r['median_seg_bars'] is not None else float('nan')):>8.1f}")

    best = rows[0]
    print(f"\n  human drew 7 segments, spans {sorted(human_lens)}, median "
          f"{float(np.median(human_lens)):.0f} bars")
    print(f"  BEST {best['label']}  SCORE {best['SCORE']:.4f} vs branch E {PUBLISHED_BRANCH_E}")

    # ---- what the best cell actually got, line by line
    Gbest = {}
    for kind in ("support", "resistance"):
        Gbest[kind], _S = broadcast(build_events(H, kind, best["cfg"]), H.m,
                                    best["min_piv"], best["gate"], H.delta)
    lines = per_line_report(H, Gbest)
    print(f"\n  THE BEST CELL, LINE BY LINE  ({best['label']})")
    print(f"  {'drawn line':<26s} {'bars':>5s} {'seen':>5s} {'g drawn':>10s} {'g fit':>10s} "
          f"{'agree':>7s}")
    for L in lines:
        print(f"  {L['kind'] + ' ' + str(L['i0']) + '-' + str(L['i1']):<26s} {L['bars']:>5d} "
              f"{L['overlap']:>5d} {L['g_drawn']:>10.5f} "
              f"{(L['median_g_fit'] if L['median_g_fit'] is not None else float('nan')):>10.5f} "
              f"{L['agreement']:>7.3f}")

    # ---- EXACT rotation nulls: the top N cells and branch E, on the same footing.
    # The distribution, not the percentile alone -- and the percentile of the observed inside it.
    print(f"\n  EXACT TIME-ROTATION NULLS ({H.n - 1} offsets enumerated, SE of p95 exactly 0)")
    print(f"  {'configuration':<48s} {'SCORE':>7s} {'p50':>7s} {'p95':>7s} {'max':>7s} "
          f"{'pctile':>7s} {'beats p95?':>11s}")
    nulls = []
    for r in rows[:N_NULLED]:
        nu = null_of(H, r["cfg"], r["min_piv"], r["gate"])
        s = nu.pop("scores")
        nu["observed"] = r["SCORE"]
        nu["pctile_of_observed"] = round(float((s < r["SCORE"]).mean()), 4)
        nu["beats_p95"] = bool(r["SCORE"] > nu["p95"])
        nu["label"] = r["label"]
        nulls.append(nu)
        print(f"  {r['label']:<48s} {r['SCORE']:>7.4f} {nu['p50']:>7.4f} {nu['p95']:>7.4f} "
              f"{nu['max']:>7.4f} {100 * nu['pctile_of_observed']:>6.1f}% "
              f"{'YES' if nu['beats_p95'] else 'no':>11s}")
    ge = branch_E_G(H)
    nuE = exact_rotation_null(H, ge)
    sE = nuE.pop("scores")
    obsE = round(float(np.mean([H.score_G(k, ge[k])["score"] for k in ge])), 4)
    nuE.update(observed=obsE, label="branch E/min_piv=3/h=4%",
               pctile_of_observed=round(float((sE < obsE).mean()), 4),
               beats_p95=bool(obsE > nuE["p95"]))
    nulls.append(nuE)
    print(f"  {'branch E/min_piv=3/h=4% (the standing best)':<48s} {obsE:>7.4f} {nuE['p50']:>7.4f} "
          f"{nuE['p95']:>7.4f} {nuE['max']:>7.4f} "
          f"{100 * nuE['pctile_of_observed']:>6.1f}% {'YES' if nuE['beats_p95'] else 'no':>11s}")

    res = dict(what="D399 piecewise-linear segmentation of the pivot series vs the drawn lines",
               published_branch_E=PUBLISHED_BRANCH_E,
               human_segment_bars=human_lens,
               n_cells=len(rows), best=best, best_lines=lines, nulls=nulls, grid=rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}")
    print("  ORACLE benchmark, and the reported best is a BEST-OF-N over "
          f"{len(rows)} cells -- read it against the null above, not on its own.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
