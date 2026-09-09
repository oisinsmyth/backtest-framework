"""D399 ALT -- THE CHARTIST'S TWO-PIVOT LINE, scored against the principal's hand-drawn lines.

    uv run python scripts/d399_alt_pivotpair.py            the whole grid
    uv run python scripts/d399_alt_pivotpair.py --selftest  the causality audits only

WHY THIS CONSTRUCTION. The ground truth in `data/d399_drawn_ground_truth.json` was produced by
CLICKING TWO BARS: `snap` says the endpoints are snapped to the wick, low for support and high for
resistance. The target is therefore literally a two-pivot object, and every branch scored so far
(B/C/D/E) answers it with a REGRESSION over many pivots. This file asks whether imitating the
drawing gesture directly beats fitting.

THE MECHANIC. Per side, per bar t:

    a line is a PAIR of confirmed swing pivots (p1 < p2), frozen: g = (y2-y1)/(x2-x1),
    level(t) = y2 + g*(t - x2), all in log price
    it stays LIVE until the close breaks it by more than `tol` (support: close < level - tol)
    on a break the pair is retired and a new line may only be drawn once a pivot NEWER than
    the broken line's anchor has confirmed -- otherwise the same pair would be redrawn into
    the same break every bar

VARIANTS OF THE PAIR
    a       the two most recent confirmed pivots
    b_far   the newest pivot + the EARLIEST pivot within `lookback` such that no bar between
            them pierces the line. This is the line a chartist actually draws: the longest
            unpierced line. (For support "pierces" = a LOW below the line.)
    b_near  the newest pivot + the LATEST unpierced partner -- the tightest valid line.
            b_near differs from `a` exactly where the naive most-recent pair is pierced.

    refresh=False   the pair is frozen until the line breaks
    refresh=True    the pair is re-selected whenever a NEW pivot confirms

    delta filter (variant c): declare no trend where |g| <= DELTA (1e-3).
    min_run filter: drop any segment shorter than MIN_RUN (5) bars.
    Both are reported as extra SCORE columns on every row rather than as extra rows.

CAUSALITY, which is the whole risk here. A pivot at index p is knowable only at p+k (k=K=3), so
the pivot pointer advances only while `pidx[ptr] <= t - k`. The line through (p1, p2) is therefore
first drawable at p2+k. Three audits below:

    [LAG]   a SECOND implementation -- re-run the construction on the series TRUNCATED at T and
            require the first T outputs to be bit-identical to the full-series run. This never
            calls the selection logic differently; it removes the future entirely. A leak of any
            kind, of any size, breaks it.
    [PAIR]  every bar's recorded anchor satisfies p2 + k <= t.
    [BREAK] the [LAG] audit is re-run against a deliberately leaking build (k=0) and must FAIL.

NOTHING IS ADMITTED HERE (R15). This is an ORACLE benchmark: the drawn lines had the whole window
in view, this construction is causal, and a shortfall does not refute it.
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

CACHE = REPO / "temp" / "d399_alt_pivotpair_gme.npz"
OUT = REPO / "temp" / "d399_alt_pivotpair_grid.json"
PIERCE_EPS = 1e-9


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


# --------------------------------------------------------------------------------------------
# the construction


def valid_partners(pidx, ppx, logw, sign, lookback):
    """For every pivot ordinal j, the ordinals i < j within `lookback` bars whose line to j is
    NOT pierced by any bar between them. Returned newest-first.

    Depends only on (j, lookback) and on bars at or before pidx[j], so it is computed once and
    shared across every bar that might draw from j -- and it carries no future information,
    because bar pidx[j] is itself only usable at pidx[j] + k."""
    P = pidx.size
    out = [[] for _ in range(P)]
    for j in range(P):
        x2, y2 = int(pidx[j]), float(ppx[j])
        for i in range(j - 1, -1, -1):
            x1 = int(pidx[i])
            if x2 - x1 > lookback:
                break
            y1 = float(ppx[i])
            g = (y2 - y1) / (x2 - x1)
            seg = logw[x1:x2 + 1]
            line = y1 + g * np.arange(x2 - x1 + 1)
            if sign < 0:
                ok = bool(np.all(seg >= line - PIERCE_EPS))
            else:
                ok = bool(np.all(seg <= line + PIERCE_EPS))
            if ok:
                out[j].append(i)
    return out


def draw(pidx, ppx, logw, logclose, n_bars, k, sign, variant, tol, partners):
    """One side's line, bar by bar. Returns (G, L, p1_used, p2_used).

    `sign` is -1 for support (line under the LOWS, broken by a close below) and +1 for
    resistance. `logw` is the wick series the pivots snap to. `tol` is in log price."""
    G = np.full(n_bars, np.nan)
    L = np.full(n_bars, np.nan)
    A1 = np.full(n_bars, -1, int)
    A2 = np.full(n_bars, -1, int)
    P = pidx.size
    ptr = 0                 # number of pivots CONFIRMED as of bar t
    cur = None              # (g, x2, y2, j)
    need_j = 0              # no line may anchor on an ordinal below this (a broken pair is retired)

    def select(j):
        if variant == "a":
            return j - 1 if j >= 1 else None
        cand = partners[j]
        if not cand:
            return None
        return cand[-1] if variant == "b_far" else cand[0]

    for t in range(n_bars):
        while ptr < P and pidx[ptr] <= t - k:
            ptr += 1
        newest = ptr - 1
        if cur is not None:
            lvl = cur[2] + cur[0] * (t - cur[1])
            broken = (logclose[t] < lvl - tol) if sign < 0 else (logclose[t] > lvl + tol)
            if broken:
                need_j = cur[3] + 1     # retire the pair; a NEWER pivot is required to redraw
                cur = None
        if cur is not None and REFRESH[0] and newest > cur[3] and newest >= need_j:
            cur = None                  # a new pivot has confirmed: re-select the pair
        if cur is None and newest >= max(1, need_j):
            i = select(newest)
            if i is not None:
                x1, x2 = int(pidx[i]), int(pidx[newest])
                y1, y2 = float(ppx[i]), float(ppx[newest])
                cur = ((y2 - y1) / (x2 - x1), x2, y2, newest, x1)
        if cur is not None:
            assert cur[1] + k <= t, "[PAIR] anchor pivot used before it confirmed"
            G[t] = cur[0]
            L[t] = cur[2] + cur[0] * (t - cur[1])
            A1[t], A2[t] = cur[4], cur[1]
    return G, L, A1, A2


REFRESH = [False]           # module-level so `draw` stays a single code path; set by run_cell


def run_cell(dat, variant, tol, lookback, refresh, k, partners_cache):
    REFRESH[0] = refresh
    res = {}
    for kind, sign, wick in (("support", -1, dat["loglow"]), ("resistance", +1, dat["loghigh"])):
        pidx = dat[f"pidx_{kind}"]
        ppx = dat[f"ppx_{kind}"]
        key = (kind, lookback, k)
        if key not in partners_cache:
            partners_cache[key] = valid_partners(pidx, ppx, wick, sign, lookback)
        G, L, A1, A2 = draw(pidx, ppx, wick, dat["logclose"], dat["m"], k, sign, variant, tol,
                            partners_cache[key])
        res[kind] = (G, L, A1, A2)
    return res


# --------------------------------------------------------------------------------------------
# filters and scoring


def apply_delta(G, delta):
    out = G.copy()
    out[~(np.abs(out) > delta)] = np.nan
    return out


def apply_min_run(G, min_run):
    """Drop any run of a CONSTANT gradient shorter than `min_run` bars. A two-bar flicker is not
    a trend (the project's MIN_RUN rule), applied per side rather than to a joint state."""
    out = G.copy()
    m = out.size
    i = 0
    while i < m:
        if not np.isfinite(out[i]):
            i += 1
            continue
        j = i
        while j + 1 < m and np.isfinite(out[j + 1]) and out[j + 1] == out[i]:
            j += 1
        if (j - i + 1) < min_run:
            out[i:j + 1] = np.nan
        i = j + 1
    return out


def score(cells, gt, start, n, SC, delta):
    """The published scorer, called on this construction's G. `SC.score_side` and `SC.human_mask`
    are imported, not re-implemented, so the number is comparable to the 0.236 by construction."""
    per, tot = {}, []
    for kind in ("support", "resistance"):
        G = cells[kind]
        Gw = G[start:start + n]
        hon, hg, _lvl = SC.human_mask(gt["lines"], n, kind)
        mon = np.isfinite(Gw)
        both = hon & mon
        s = SC.score_side(Gw, hg, both, int(hon.sum()), delta)
        s["machine_bars_on"] = int(mon.sum())
        s["precision"] = round(float(both.sum() / max(mon.sum(), 1)), 4)
        s["segments"] = int(np.sum(np.isfinite(Gw[1:]) & (
            ~np.isfinite(Gw[:-1]) | (Gw[1:] != Gw[:-1])))) + int(np.isfinite(Gw[0]))
        per[kind] = s
        tot.append(s["score"])
    return per, float(np.mean(tot))


# --------------------------------------------------------------------------------------------
# data


def load_data(k):
    if CACHE.exists():
        z = np.load(CACHE, allow_pickle=False)
        if int(z["k"]) == k:
            d = {kk: z[kk] for kk in z.files}
            d["m"] = int(z["m"])
            return d
    DR = _load("d399draw", "d399_draw_construction.py")
    RP = _load("ragged_panel", "ragged_panel.py")
    from backtest_framework.research.structure import pivots as PV
    _panel, cleaned = RP.load_ragged(*DR.MINING, fee_bps=0.0, dividend_bound=True)
    bars = cleaned["GME"]
    m = len(bars)
    hi = np.array([b.bar.high for b in bars], float)
    lo = np.array([b.bar.low for b in bars], float)
    cl = np.array([b.bar.close for b in bars], float)
    ps = PV(bars, k)
    d = dict(m=m, loghigh=np.log(hi), loglow=np.log(lo), logclose=np.log(cl), k=np.int64(k))
    for kind, sign in (("support", -1), ("resistance", +1)):
        idx = np.array([p.index for p in ps if p.sign == sign], dtype=int)
        assert idx.size == 0 or np.all(np.diff(idx) > 0), "pivot indices not ascending"
        d[f"pidx_{kind}"] = idx
        d[f"ppx_{kind}"] = np.log(np.array([p.price for p in ps if p.sign == sign], float))
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.savez(CACHE, **{kk: np.asarray(v) for kk, v in d.items()})
    d["m"] = m
    return d


def truncated_prefix(dat, T, variant, tol, lookback, refresh, k, true_k):
    """[LAG] SECOND IMPLEMENTATION: the same construction on a series that PHYSICALLY ENDS at T.

    It shares `draw`, but nothing after bar T-1 exists for it. The pivot set is cut to what the
    TRUNCATED BARS COULD HAVE DETECTED -- a fractal pivot at index p needs bars p+1..p+true_k, so
    only p <= T-1-true_k survives, regardless of the lag the construction claims to use. That is
    what makes this an audit rather than a restatement: a build that advances its pointer faster
    than true_k reaches for pivots the truncated series simply does not contain, and the prefixes
    diverge. The honest build never does, so its prefixes are bit-identical."""
    sub = dict(m=T, loghigh=dat["loghigh"][:T], loglow=dat["loglow"][:T],
               logclose=dat["logclose"][:T])
    pc = {}
    for kind in ("support", "resistance"):
        keep = dat[f"pidx_{kind}"] <= T - 1 - true_k
        sub[f"pidx_{kind}"] = dat[f"pidx_{kind}"][keep]
        sub[f"ppx_{kind}"] = dat[f"ppx_{kind}"][keep]
    return run_cell(sub, variant, tol, lookback, refresh, k, pc)


def selftest(dat, k, leak_k=None):
    """Returns True if the prefix audit PASSES. `leak_k` builds the deliberately broken version:
    the pivot pointer advances with a lag of `leak_k` instead of k, so bar t reads a pivot that
    has not confirmed. [BREAK] requires this to return False."""
    kk = k if leak_k is None else leak_k
    ok = True
    for variant, tol, lookback, refresh in (("a", 0.0, 252, False),
                                            ("b_far", 0.01, 126, False),
                                            ("b_near", 0.03, 63, True)):
        full = run_cell(dat, variant, tol, lookback, refresh, kk, {})
        for T in (2500, 2600, 2689):
            sub = truncated_prefix(dat, T, variant, tol, lookback, refresh, kk, k)
            for kind in ("support", "resistance"):
                a = full[kind][0][:T]
                b = sub[kind][0]
                if not np.array_equal(a, b, equal_nan=True):
                    ok = False
    return ok


# --------------------------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--sensitivity", action="store_true",
                    help="the pre-declared grid's best sits at its SHORTEST lookback (63) and the "
                         "score is monotone in it, so the grid cannot say whether 63 is a choice "
                         "or an edge. This extends the lookback axis ONLY, at the best cell's "
                         "other settings, and is reported separately as the extension it is.")
    a = ap.parse_args()

    DR = _load("d399draw", "d399_draw_construction.py")
    SC = _load("d399score", "d399_score_against_drawn.py")
    UO = _load("d240_uptrend", "run_uptrend_onset.py")
    K, DELTA, MIN_RUN = UO.K, DR.DELTA, DR.MIN_RUN

    t0 = time.time()
    dat = load_data(K)
    gt = json.loads((REPO / "data" / "d399_drawn_ground_truth.json").read_text())
    start, n = int(gt["start_bar"]), int(gt["n"])
    print(f"  GME {dat['m']} bars, {dat['pidx_support'].size} swing lows / "
          f"{dat['pidx_resistance'].size} swing highs, k={K}   ({time.time() - t0:.1f}s)")

    print("\n  AUDITS")
    good = selftest(dat, K)
    print(f"    [LAG]   truncated-prefix identity on 3 configs x 3 cut points x 2 sides: "
          f"{'PASS' if good else 'FAIL'}")
    assert good, "[LAG] the construction reads the future"
    bad = selftest(dat, K, leak_k=0)
    print(f"    [BREAK] the same audit against a k=0 (leaking) build: "
          f"{'raises as required' if not bad else 'DID NOT FIRE -- audit is worthless'}")
    assert not bad, "[BREAK] the lag audit cannot fail; it is not an audit"
    print("    [PAIR]  asserted inside `draw` on every bar a line exists")

    if a.selftest:
        return 0

    VARIANTS = ["a", "b_far", "b_near"]
    TOLS = [0.0, 0.01, 0.03]
    LOOKBACKS = [63, 126, 252]
    REFRESHES = [False, True]

    rows = []
    pc = {}
    for variant in VARIANTS:
        for refresh in REFRESHES:
            for tol in TOLS:
                for lookback in LOOKBACKS:
                    cells = run_cell(dat, variant, tol, lookback, refresh, K, pc)
                    raw = {kd: cells[kd][0] for kd in cells}
                    per_r, tot_r = score(raw, gt, start, n, SC, DELTA)
                    dfl = {kd: apply_delta(raw[kd], DELTA) for kd in raw}
                    per_d, tot_d = score(dfl, gt, start, n, SC, DELTA)
                    mrn = {kd: apply_min_run(dfl[kd], MIN_RUN) for kd in dfl}
                    per_m, tot_m = score(mrn, gt, start, n, SC, DELTA)
                    rows.append(dict(variant=variant, refresh=refresh, tol=tol, lookback=lookback,
                                     score=round(tot_r, 4), score_delta=round(tot_d, 4),
                                     score_delta_minrun=round(tot_m, 4),
                                     per_side=per_r, per_side_delta=per_d,
                                     per_side_delta_minrun=per_m))

    print(f"\n  GRID -- {len(rows)} cells. SCORE = mean over the two sides of "
          f"AGREEMENT * RECALL**0.25. Published best to beat: 0.236\n")
    print(f"  {'variant':>7s} {'refr':>5s} {'tol':>5s} {'lkbk':>5s} "
          f"{'SCORE':>7s} {'+delta':>7s} {'+minrun':>8s}   "
          f"{'sup agr':>8s} {'sup rec':>8s} {'res agr':>8s} {'res rec':>8s}")
    for r in rows:
        s, rr = r["per_side"]["support"], r["per_side"]["resistance"]
        print(f"  {r['variant']:>7s} {str(r['refresh']):>5s} {100*r['tol']:>4.0f}% "
              f"{r['lookback']:>5d} {r['score']:>7.3f} {r['score_delta']:>7.3f} "
              f"{r['score_delta_minrun']:>8.3f}   "
              f"{(s['agreement'] or 0):>8.3f} {s['recall']:>8.3f} "
              f"{(rr['agreement'] or 0):>8.3f} {rr['recall']:>8.3f}")

    flat = []
    for r in rows:
        for col, ps in (("score", "per_side"), ("score_delta", "per_side_delta"),
                        ("score_delta_minrun", "per_side_delta_minrun")):
            flat.append((r[col], col, r, r[ps]))
    flat.sort(key=lambda z: -z[0])
    best = flat[0]
    print(f"\n  BEST OF {len(flat)} scored cells (a best-of-N, and it needs the floor below "
          f"to mean anything):")
    r, ps = best[2], best[3]
    print(f"    variant={r['variant']} refresh={r['refresh']} tol={100*r['tol']:.0f}% "
          f"lookback={r['lookback']} filter={best[1]}  SCORE {best[0]:.4f}")
    for kind in ("support", "resistance"):
        c = ps[kind]
        print(f"      {kind:>10s}  agreement {c['agreement']}  recall {c['recall']}  "
              f"precision {c['precision']}  overlap {c['overlap_bars']}  "
              f"machine-on {c['machine_bars_on']}/{n}  segments {c['segments']}  "
              f"score {c['score']}")

    allv = np.array([z[0] for z in flat])
    print(f"\n  FLOOR: the grid's own distribution over {allv.size} scored cells -- "
          f"min {allv.min():.3f}  p50 {np.median(allv):.3f}  p90 {np.quantile(allv, .9):.3f}  "
          f"max {allv.max():.3f}")

    # the question the principal asked: does the non-pierced line beat the naive pair?
    print("\n  (b) NON-PIERCING vs (a) NAIVE MOST-RECENT PAIR, matched on refresh/tol/lookback:")
    by = {(r["variant"], r["refresh"], r["tol"], r["lookback"]): r for r in rows}
    for col in ("score", "score_delta", "score_delta_minrun"):
        wins_far = wins_near = ties = tot = 0
        dfar, dnear = [], []
        for (v, rf, tl, lb), r in by.items():
            if v != "a":
                continue
            for vv, acc in (("b_far", dfar), ("b_near", dnear)):
                o = by[(vv, rf, tl, lb)]
                acc.append(o[col] - r[col])
                tot += 1
                if o[col] > r[col]:
                    if vv == "b_far":
                        wins_far += 1
                    else:
                        wins_near += 1
                elif o[col] == r[col]:
                    ties += 1
        print(f"    {col:>19s}:  b_far mean delta {np.mean(dfar):+.4f} (beats a in "
              f"{wins_far}/{len(dfar)}),  b_near mean delta {np.mean(dnear):+.4f} "
              f"(beats a in {wins_near}/{len(dnear)})")

    sens = None
    if a.sensitivity:
        print("\n  SENSITIVITY (NOT part of the pre-declared grid): variant=b_far, refresh=True, "
              "tol=0%, lookback extended\n")
        sens = []
        print(f"  {'lkbk':>5s} {'SCORE':>7s} {'+delta':>7s} {'+minrun':>8s}   "
              f"{'sup agr':>8s} {'sup rec':>8s} {'res agr':>8s} {'res rec':>8s}")
        for lb in (10, 15, 21, 31, 42, 63, 84, 126, 189, 252, 504):
            cells = run_cell(dat, "b_far", 0.0, lb, True, K, pc)
            raw = {kd: cells[kd][0] for kd in cells}
            per_r, tot_r = score(raw, gt, start, n, SC, DELTA)
            dfl = {kd: apply_delta(raw[kd], DELTA) for kd in raw}
            _pd, tot_d = score(dfl, gt, start, n, SC, DELTA)
            mrn = {kd: apply_min_run(dfl[kd], MIN_RUN) for kd in dfl}
            per_m, tot_m = score(mrn, gt, start, n, SC, DELTA)
            s, rr = per_m["support"], per_m["resistance"]
            sens.append(dict(lookback=lb, score=round(tot_r, 4), score_delta=round(tot_d, 4),
                             score_delta_minrun=round(tot_m, 4), per_side_delta_minrun=per_m))
            print(f"  {lb:>5d} {tot_r:>7.3f} {tot_d:>7.3f} {tot_m:>8.3f}   "
                  f"{(s['agreement'] or 0):>8.3f} {s['recall']:>8.3f} "
                  f"{(rr['agreement'] or 0):>8.3f} {rr['recall']:>8.3f}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(dict(
        sensitivity_b_far_refresh_tol0=sens,
        what="D399 ALT -- chartist two-pivot line, scored against the hand-drawn ground truth",
        k=K, delta=DELTA, min_run=MIN_RUN, start_bar=start, n=n,
        note="DIAGNOSTIC / ORACLE benchmark. Nothing admitted (R15). Best is a best-of-N.",
        rows=rows), indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}")
    print(f"  total {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
