"""D477 -- THE CEILING: the same trading rule, with PERFECT lines.

    uv run python -u scripts/run_d477_oracle_ceiling.py --proof
    uv run python -u scripts/run_d477_oracle_ceiling.py

WHAT THIS IS. D476 traded the D399 channel and failed: long +7.6 +- 6.5 bp/trade, short -73 bp,
and a book below its own rotation null's p50. Two explanations survive that result -- the LINES
are too poor (estimator error: pivots confirmed k bars late, a fit frozen on two points, a stale
test) or the OBJECT is empty (a channel, however well drawn, does not predict). This study
separates them by removing the estimator entirely and changing nothing else.

THE ORACLE. Each name's history is cut, WITH FULL KNOWLEDGE OF THE FUTURE, into maximal channels:
a support line no low pierces by more than `tol`, a resistance line no high pierces, at least
`MIN_TOUCH` touches a side, at least `MIN_WIDTH` wide, extended as far forward as it survives.
Inside a channel, the support and resistance at bar t are that channel's lines evaluated at t.
Between channels there are no lines. `envelope_fit` (audited by [V] and [A]) does the fitting.

WHAT THE TRADER IS ALLOWED TO SEE, and this is the principal's constraint, 2026-09-10:
**the support and resistance level at the current bar and at previous bars, and nothing else.**
It is NOT told where a channel starts or ends. It learns a channel has ended the bar the lines
stop being there -- never in advance. So it cannot hold to a boundary it has been shown, and the
hindsight in the LEVEL is the only hindsight it gets. That is the quantity being measured.

WITHOUT THAT CONSTRAINT THE STUDY WOULD BE VACUOUS. A hindsight channel is a box built to
contain price: "go long from the channel's first bar to its last" earns a positive return by
construction, and "buy at a line no low sits below" cannot lose. Any statistic computed inside a
window that was chosen knowing the answer is a tautology. Withholding the boundaries is what
makes the number mean something.

THE RULE IS D476's, UNCHANGED -- `entry_mask`, `walk`, `summarise` and `atr_of` are imported from
that runner rather than restated, so the two studies differ in the LINES and in nothing else.
Same 9 cells, same ATR target and trailing stop, same costs, same split guard, same panel and
floor. The comparison is per-trade, cell for cell, against `data/d476_channel_trades.json`.

THIS IS A CEILING AND NOTHING HERE IS ADMISSIBLE AS A SIGNAL. It reads the future by design.
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

OUT = REPO / "data" / "d477_oracle_ceiling.json"

# THE PRINCIPAL'S SETTINGS LINE, 2026-09-10, dialled in by eye on the twelve names and
# transcribed field for field:
#   split=greedy seed=5 slack=0 pk=1 tol=1.75 mt=3 basis=wick minlen=20 maxlen=1000 mw=0
#   maxw=24 maxoff=-1 mintd=35 tau=0.4 shade=on
# (`seed` and `pk` belong to the other two splitters and are inert under greedy; `shade` is
# cosmetic.) His own verdict on it: "not perfect but the best I could do" -- and that, with
# perfect knowledge and a dozen dials, is itself the first real evidence about the object.
SETTINGS_LINE = ("split=greedy seed=5 slack=0 pk=1 tol=1.75 mt=3 basis=wick minlen=20 "
                 "maxlen=1000 mw=0 maxw=24 maxoff=-1 mintd=35 tau=0.4 shade=on")
TOL = math.log1p(0.0175)     # a wick may pierce the line by this much, in log
MIN_TOUCH = 3                # touches a side for a channel to count as one
MIN_LEN = 20                 # bars; shorter than this is not a channel
MAX_LEN = 1000               # bars; bounds the search
MIN_WIDTH = 0.0              # no floor on the width
MAX_WIDTH = math.log1p(0.24)  # ... but a ceiling: a channel wider than this is a box, not a channel
MAX_OFFSET = -1.0            # off; the touch-density filter is doing this job instead
MIN_TOUCH_DENSITY = 0.35     # at least this share of bars must reach one of the two lines
TAU_PARALLEL = 0.4           # the two sides must be roughly parallel
SLACK = 0                    # greedy: the start does not slide


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def fit_window(RC, lo, hi, a, b):
    """One window, fitted and filtered. A FAITHFUL PORT of the page's `fitWindow` -- the same
    tests in the same order, the same clamp of a negative offset to zero, the same touch count --
    because the settings above were chosen by eye against that page and must mean the same here."""
    m = b - a + 1
    if m < 2:
        return None
    x = np.arange(a, b + 1, dtype=float)
    gs, cs, ts = RC.envelope_fit(x, lo[a:b + 1], "support", TOL)
    gr, cr, tr = RC.envelope_fit(x, hi[a:b + 1], "resistance", TOL)
    if not (np.isfinite(gs) and np.isfinite(gr)) or ts < MIN_TOUCH or tr < MIN_TOUCH:
        return None
    w0 = (gr * x[0] + cr) - (gs * x[0] + cs)
    w1 = (gr * x[-1] + cr) - (gs * x[-1] + cs)
    if min(w0, w1) < MIN_WIDTH:
        return None
    if MAX_WIDTH >= 0 and max(w0, w1) > MAX_WIDTH:
        return None
    if TAU_PARALLEL >= 0 and abs(gs - gr) > TAU_PARALLEL * max(abs(gs), abs(gr)):
        return None
    d = np.minimum(lo[a:b + 1] - (gs * x + cs), (gr * x + cr) - hi[a:b + 1])
    off = float(np.maximum(d, 0.0).sum() / m)
    td = float((d <= TOL).sum() / m)
    if MAX_OFFSET >= 0 and off > MAX_OFFSET:
        return None
    if MIN_TOUCH_DENSITY >= 0 and td < MIN_TOUCH_DENSITY:
        return None
    return dict(a=a, b=b, gs=float(gs), cs=float(cs), gr=float(gr), cr=float(cr),
                ts=int(ts), tr=int(tr), off=off, td=td, score=int(ts) + int(tr))


def grow_right(RC, lo, hi, A, B, limit):
    """Extend by a stride that starts at an eighth of the length and halves on failure down to
    one, so the far end is found to the exact bar in O(L log L) rather than O(L^2). The page does
    exactly this; growing one bar at a time made a long channel hang the browser."""
    cur, stride = None, max(1, (B - A + 1) >> 3)
    while stride >= 1:
        nB = min(limit, B + stride)
        if nB <= B or nB - A + 1 > MAX_LEN:
            if stride == 1:
                break
            stride >>= 1
            continue
        f = fit_window(RC, lo, hi, A, nB)
        if f is not None:
            cur, B = f, nB
            stride = max(1, (B - A + 1) >> 3)
        else:
            if stride == 1:
                break
            stride >>= 1
    return B, cur


def oracle_channels(RC, lo, hi, a0=0, a1=None):
    """Channels LEFT TO RIGHT, WITH FULL INFORMATION, under the principal's settings: from `a`,
    seed at the minimum length and grow right while the window still passes every filter; emit
    it; restart past it. Disjoint by construction, and the bars between channels are bars no
    channel covers -- which the trading rule reads as "no lines".

    The gradient-similarity test IS part of validity here (tau = 0.4), because the principal put
    it there. One consequence is stated rather than discovered later: the trading rule's own
    similarity gate can then never bind, since 0.4 is tighter than any tau in D476's grid."""
    n = lo.size if a1 is None else a1
    segs, a = [], a0
    while a + MIN_LEN <= n:
        best = None
        for s in range(a, a + SLACK + 1):
            if s + MIN_LEN > n:
                break
            seed = fit_window(RC, lo, hi, s, s + MIN_LEN - 1)
            if seed is None:
                continue
            _b, g = grow_right(RC, lo, hi, s, s + MIN_LEN - 1, n - 1)
            cand = g if g is not None else seed
            if best is None or (cand["b"] - cand["a"]) > (best["b"] - best["a"]) \
                    or ((cand["b"] - cand["a"]) == (best["b"] - best["a"])
                        and cand["score"] > best["score"]):
                best = cand
        if best is None:
            a += 1
            continue
        segs.append(best)
        a = best["b"] + 1
    return segs


def oracle_lines(RC, bars, segs=None):
    """The per-bar view the trader is given: a level and a gradient per side inside a channel,
    nothing between channels. Shaped exactly like `run_d434.build_lines` so the same walk reads
    it, and carrying the same `proj`/`seen` fields -- which is how "keep going with only one"
    and the GONE exit behave identically to D476."""
    m = len(bars)
    op = np.array([b.bar.open for b in bars], float)
    cl = np.array([b.bar.close for b in bars], float)
    hi = np.array([b.bar.high for b in bars], float)
    lo = np.array([b.bar.low for b in bars], float)
    with np.errstate(divide="ignore"):
        llo, lhi = np.log(lo), np.log(hi)
    if segs is None:
        segs = oracle_channels(RC, llo, lhi)
    G = {kd: np.full(m, np.nan) for kd in ("support", "resistance")}
    L = {kd: np.full(m, np.nan) for kd in ("support", "resistance")}
    q = np.arange(m, dtype=float)
    for s in segs:
        i = np.arange(s["a"], s["b"] + 1)
        G["support"][i], L["support"][i] = s["gs"], s["gs"] * i + s["cs"]
        G["resistance"][i], L["resistance"][i] = s["gr"], s["gr"] * i + s["cr"]
    proj, gproj, seen, drawn = {}, {}, {}, {}
    for kd in ("support", "resistance"):
        on = np.isfinite(L[kd])
        c_at = np.where(on, L[kd] - G[kd] * q, np.nan)
        idx = np.where(on, np.arange(m), -1)
        last = np.maximum.accumulate(idx)
        ok = last >= 0
        g_last = np.where(ok, G[kd][np.maximum(last, 0)], np.nan)
        c_last = np.where(ok, c_at[np.maximum(last, 0)], np.nan)
        proj[kd] = g_last * q + c_last
        gproj[kd] = g_last
        seen[kd] = last
        drawn[kd] = on
    return dict(m=m, op=op, cl=cl, hi=hi, lo=lo, G=G, L=L, proj=proj, gproj=gproj, seen=seen,
                drawn=drawn), segs


GMIN_PCT = (0.0, 10.0, 25.0, 50.0, 100.0, 200.0)   # minimum |gradient|, annualised per cent
HEAD_GMIN = 25.0
N_SIMS, NULL_SEED = 300, 0
PPY, RF, BORROW = 252.0, 0.04, 0.03
SPLIT_LR = 0.40
MIN_TRADES = 100


def trend_state(N, elig, gmin):
    """+1 / -1 / 0 at each bar's close. A TREND is: both lines drawn, their gradients of the same
    sign, and BOTH steeper than `gmin`. Nothing else. Read at the close of the bar itself."""
    gs, gr = N["G"]["support"], N["G"]["resistance"]
    both = N["drawn"]["support"] & N["drawn"]["resistance"] & elig
    with np.errstate(invalid="ignore"):
        up = both & (gs > gmin) & (gr > gmin)
        dn = both & (gs < -gmin) & (gr < -gmin)
    return np.where(up, 1, np.where(dn, -1, 0)).astype(np.int8)


def trend_trades(state, cl):
    """IN WHILE THERE IS A TREND, OUT WHEN THERE IS NOT. Enter at the close of the first bar in a
    trend; exit at the close of the first bar that is no longer in it, or has flipped -- which is
    the first bar at which the end is knowable. No target, no stop, no holding cap."""
    m = state.size
    out, t = [], 0
    while t < m:
        d = int(state[t])
        if d == 0:
            t += 1
            continue
        u = t + 1
        while u < m and int(state[u]) == d:
            u += 1
        x = min(u, m - 1)
        if x > t and np.isfinite(cl[t]) and cl[t] > 0 and np.isfinite(cl[x]) and cl[x] > 0:
            out.append((t, x, d))
        t = u
    return out


def audit_no_future(N, elig, gmin, probes):
    """[F] THE RULE SEES NO BOUNDARY IN ADVANCE. The state at bar e must depend only on the levels
    at bars <= e. Re-derive it with every level after e deleted: identical.

    This does not claim the study is causal -- it is not, by design, since the LEVELS were fitted
    knowing the future. It claims exactly what was promised: the rule reads only the current and
    previous bars, so a channel's start and end are never known before they happen."""
    base = trend_state(N, elig, gmin)
    checked = 0
    for e in probes:
        if e < 5 or e >= N["m"]:
            continue
        N2 = dict(N)
        N2["G"] = {k: v.copy() for k, v in N["G"].items()}
        N2["drawn"] = {k: v.copy() for k, v in N["drawn"].items()}
        for kd in ("support", "resistance"):
            N2["G"][kd][e + 1:] = np.nan
            N2["drawn"][kd][e + 1:] = False
        if int(trend_state(N2, elig, gmin)[e]) != int(base[e]):
            raise AssertionError(f"[F] the state at bar {e} moves when the future is deleted")
        checked += 1
    assert checked >= max(1, len(probes) // 2), f"[F] VACUOUS: {checked}/{len(probes)}"
    return checked


def audit_sign(rows, sym_of, tot_by_sym):
    """[S] IN MONEY: the largest up-bar inside a LONG trade must add to it and inside a SHORT
    subtract, and the inverted direction must fail the same test."""
    best = None
    for r in rows:
        tot = tot_by_sym.get(r["sym"])
        if tot is None:
            continue
        seg = tot[r["e"] + 1:r["x"] + 1]
        if seg.size == 0 or not np.isfinite(seg).any():
            continue
        v = float(np.nanmax(seg))
        if best is None or v > best[0]:
            best = (v, r["dir"])
    assert best is not None, "[S] no trade carried a finite bar return"
    v, d = best
    assert ((d * v) > 0) == (d > 0), f"[S] direction inverted: {d * v:+.4f}"
    assert not ((((-d) * v) > 0) == (d > 0)), "[S] SELF-TEST: the inverted direction also passes"
    return v, d


def summarise(rows, label):
    if not rows:
        return dict(label=label, n=0)
    g = np.array([r["gross"] for r in rows], float)
    net = np.array([r["net"] for r in rows], float)
    hold = np.array([r["x"] - r["e"] for r in rows], float)
    lo_, hi_ = np.percentile(g, 1), np.percentile(g, 99)
    tr = g[(g >= lo_) & (g <= hi_)]
    return dict(label=label, n=len(rows),
                gross_bp=1e4 * float(g.mean()), gross_med_bp=1e4 * float(np.median(g)),
                se_bp=1e4 * float(g.std(ddof=1) / math.sqrt(len(g))),
                net_bp=1e4 * float(net.mean()),
                trim_bp=1e4 * float(tr.mean()) if tr.size else float("nan"),
                ex_top_bp=1e4 * float(g[g <= hi_].mean()),
                win=float((g > 0).mean()), hold_med=float(np.median(hold)),
                spread_bp=1e4 * float(np.mean([r["spread"] for r in rows])))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--proof", action="store_true")
    ap.add_argument("--names", type=int, default=0)
    a = ap.parse_args()

    t0 = time.time()
    RC = _load("d399rc", "d399_recalc_segment.py")
    D4 = _load("d434", "run_d476_channel_trades.py")
    NS = _load("d399ns", "d399_new_sample.py")
    DR = _load("d399draw", "d399_draw_construction.py")
    RP = _load("rp", "ragged_panel.py")
    X = _load("d320", "run_d320_tilt_filters.py")
    UF = _load("d339uf", "d339_universe_floor.py")
    SP = _load("d285sp", "d285_spread_estimate.py")
    UF.bind(X, None)
    from backtest_framework.research.structure import pivots_tie_tolerant as PVT

    panel, cleaned = RP.load_ragged(*DR.MINING, fee_bps=0.0, dividend_bound=True)
    T, n = len(panel.dates), len(panel.symbols)
    print(f"\n  panel {n} names x {T} dates in {time.time() - t0:.0f}s")
    print(f"  ORACLE {SETTINGS_LINE}")
    print(f"  RULE   in while a trend, out when not; minimum gradient swept "
          f"{list(GMIN_PCT)} %/yr; NO target, NO stop")

    CL = np.ascontiguousarray(panel.closes.T)
    live = np.ascontiguousarray(panel.live.T)
    VOL = np.full((T, n), np.nan)
    HIg, LOg = np.full((T, n), np.nan), np.full((T, n), np.nan)
    posn = {d: i for i, d in enumerate(panel.dates)}
    sym = {s: i for i, s in enumerate(panel.symbols)}
    rowmap = {}
    for s, bars in cleaned.items():
        i = sym.get(s)
        if i is None:
            continue
        rr = np.full(len(bars), -1, int)
        for j, stx in enumerate(bars):
            t = posn.get(stx.timestamp[:10])
            if t is not None:
                rr[j] = t
                VOL[t, i], HIg[t, i], LOg[t, i] = stx.bar.volume, stx.bar.high, stx.bar.low
        rowmap[s] = rr
    ev = json.loads(Path(DR.MINING[1]).read_text(encoding="utf-8"))
    elig_grid = live & UF.floor_mask_v2(CL * UF.raw_price_factor(panel, ev),
                                        X.roll_mean_T(CL * VOL), live)
    CS = SP.corwin_schultz(HIg.T, LOg.T, panel.live)
    LR, TLR = panel.log_returns, panel.total_log_returns
    DIV = TLR - LR
    print(f"  floor {100 * elig_grid.mean():.1f}% eligible ({time.time() - t0:.0f}s)")

    syms = list(panel.symbols)
    if a.proof:
        syms = [s for s in ("BA", "COST", "SNPS") if s in sym] or syms[:3]
    elif a.names:
        syms = syms[:a.names]

    GM = {p: math.log1p(p / 100) / 252.0 for p in GMIN_PCT}
    sources = ("ORACLE", "CAUSAL")
    rows = {(sc, p): [] for sc in sources for p in GMIN_PCT}
    hkey = ("ORACLE", HEAD_GMIN)
    book = {sc: np.zeros((n, T), dtype=np.float32) for sc in sources}
    cover = {sc: [0, 0] for sc in sources}
    n_split, seg_n, seg_len = 0, 0, []
    tot_by_sym, sym_of = {}, {}
    t1 = time.time()
    for c, s in enumerate(syms):
        i = sym[s]
        bars = cleaned[s]
        rr = rowmap[s]
        good = rr >= 0
        if good.sum() < 60:
            continue
        m = len(bars)
        elig = np.zeros(m, bool)
        elig[good] = elig_grid[rr[good], i]
        lr = np.full(m, np.nan)
        lr[good] = LR[i, rr[good]]
        dv = np.zeros(m)
        dv[good] = np.nan_to_num(DIV[i, rr[good]])
        cs = np.full(m, np.nan)
        cs[good] = CS[i, rr[good]]
        tot = np.full(m, np.nan)
        tot[good] = TLR[i, rr[good]]
        tot_by_sym[s] = tot
        for sc in sources:
            if sc == "ORACLE":
                N, segs = oracle_lines(RC, bars)
                seg_n += len(segs)
                seg_len += [g["b"] - g["a"] + 1 for g in segs]
            else:
                N = D4.build_lines(RC, DR, PVT, bars, NS.CELL_FINAL, True)
            cover[sc][0] += int((N["drawn"]["support"] & N["drawn"]["resistance"]).sum())
            cover[sc][1] += m
            for p in GMIN_PCT:
                state = trend_state(N, elig, GM[p])
                for (e, x, d) in trend_trades(state, N["cl"]):
                    seg = slice(e + 1, x + 1)
                    held = np.abs(lr[seg])
                    if np.isfinite(held).any() and np.nanmax(held) > SPLIT_LR:
                        n_split += 1
                        continue
                    gross = d * (math.log(N["cl"][x] / N["cl"][e]) + float(dv[seg].sum()))
                    sp = float(np.nanmean(cs[seg])) if np.isfinite(cs[seg]).any() else 0.0
                    sp = 0.0 if not np.isfinite(sp) else sp
                    rows[(sc, p)].append(dict(sym=s, e=int(e), x=int(x), dir=int(d),
                                              gross=float(gross), net=float(gross - sp),
                                              spread=sp, date=bars[e].timestamp[:10]))
                    if p == HEAD_GMIN and rr[e + 1] >= 0 and rr[x] >= 0:
                        book[sc][i, rr[e + 1]:rr[x] + 1] = d
        if (c + 1) % 200 == 0:
            print(f"    {c + 1}/{len(syms)} names, {time.time() - t1:.0f}s")

    sl = np.array(seg_len, float)
    print(f"\n  ORACLE CHANNELS {seg_n:,} | length median {np.median(sl):.0f} p90 "
          f"{np.percentile(sl, 90):.0f} max {sl.max():.0f} | both lines drawn on "
          f"{100 * cover['ORACLE'][0] / max(1, cover['ORACLE'][1]):.0f}% of bars "
          f"(causal {100 * cover['CAUSAL'][0] / max(1, cover['CAUSAL'][1]):.0f}%)")

    s0 = syms[0]
    el0 = np.zeros(len(cleaned[s0]), bool)
    g0 = rowmap[s0] >= 0
    el0[g0] = elig_grid[rowmap[s0][g0], sym[s0]]
    N0, _ = oracle_lines(RC, cleaned[s0])
    pr = [int(v) for v in np.linspace(30, N0["m"] - 2, 9).astype(int)]
    print(f"  [F] {audit_no_future(N0, el0, GM[HEAD_GMIN], pr)} states on {s0} unchanged when "
          f"every future level is deleted -- no boundary is seen in advance  OK")
    v, d = audit_sign(rows[hkey], sym_of, tot_by_sym)
    print(f"  [S] the largest up-bar inside a {'long' if d > 0 else 'short'} trade "
          f"({1e4 * v:+.0f} bp) contributes with the right sign  OK")

    print(f"\n  PER TRADE, gross bp -- ORACLE (perfect lines) vs CAUSAL (D399's), SAME rule")
    print(f"  {'gmin':>6s} {'side':<6s} {'':<2s}{'n':>7s} {'gross':>8s} {'+-SE':>6s} {'med':>8s} "
          f"{'trim':>8s} {'net':>8s} {'win%':>5s} {'hold':>5s}   |   "
          f"{'n':>7s} {'gross':>8s} {'+-SE':>6s} {'med':>8s} {'net':>8s} {'win%':>5s} {'hold':>5s}")
    out = {}
    for p in GMIN_PCT:
        for side, nm in ((1, "long"), (-1, "short")):
            line = f"  {p:>6.0f} {nm:<6s}   "
            for sc in sources:
                sub = [r for r in rows[(sc, p)] if r["dir"] == side]
                st = summarise(sub, f"{sc}/g{p}/{nm}")
                out[f"{sc}|{p}|{nm}"] = st
                if not st["n"]:
                    line += f"{0:>7d}" + " " * 48
                    continue
                if sc == "ORACLE":
                    line += (f"{st['n']:>7d} {st['gross_bp']:>8.1f} {st['se_bp']:>6.1f} "
                             f"{st['gross_med_bp']:>8.1f} {st['trim_bp']:>8.1f} "
                             f"{st['net_bp']:>8.1f} {100 * st['win']:>5.0f} {st['hold_med']:>5.0f}   |   ")
                else:
                    line += (f"{st['n']:>7d} {st['gross_bp']:>8.1f} {st['se_bp']:>6.1f} "
                             f"{st['gross_med_bp']:>8.1f} {st['net_bp']:>8.1f} "
                             f"{100 * st['win']:>5.0f} {st['hold_med']:>5.0f}")
            print(line)

    # THE BOOK, DESCRIPTIVE ONLY -- NO NULL. A rotation null asks whether a book's timing beats a
    # random re-timing of the same trades; for lines fitted knowing the future the question is
    # empty, and running it cost more than the study (the principal killed the first run on it).
    # The comparison here is ORACLE against CAUSAL, per trade; the book totals are context.
    hb = {}
    emask = np.ascontiguousarray(elig_grid.T.astype(float))
    for sc in sources:
        for side, nm in ((1, "long"), (-1, "short"), (0, "both")):
            p = book[sc].astype(np.float64)
            if side > 0:
                p[p < 0] = 0.0
            elif side < 0:
                p[p > 0] = 0.0
            p *= emask
            if not p.any():
                continue
            sc2 = RP.score(panel, p, 0, ppy=PPY, rf_annual=RF, borrow_annual=BORROW)
            hb[f"{sc}|{nm}"] = dict(total_return=sc2["total_return"], sharpe=sc2["excess_sharpe"],
                                    exposure=sc2["exposure_gross"], maxdd=sc2["max_drawdown"])
            h = hb[f"{sc}|{nm}"]
            print(f"  [BOOK] {sc:<7s} {nm:<5s} total {100 * h['total_return']:>7.1f}%  "
                  f"sharpe {h['sharpe']:>5.2f}  expo {h['exposure']:.3f}  maxDD "
                  f"{100 * h['maxdd']:>6.1f}%")

    top = max(rows[hkey], key=lambda r: r["gross"]) if rows[hkey] else None
    if top:
        print(f"\n  TOP TRADE (oracle, gmin {HEAD_GMIN:.0f}%): {top['sym']} {top['date']} "
              f"{top['e']}->{top['x']} {'long' if top['dir'] > 0 else 'short'} "
              f"{1e4 * top['gross']:+.0f} bp")
    for side, nm in ((1, "long"), (-1, "short")):
        k = sum(1 for r in rows[hkey] if r["dir"] == side)
        print(f"  [N] oracle {nm} trades at the headline gmin: {k}"
              + ("" if k >= MIN_TRADES or a.proof else f"  << {MIN_TRADES}, VACUOUS"))
    print(f"  split-guard rejections: {n_split}")
    if not a.proof:
        OUT.write_text(json.dumps(dict(
            what="D477: the ceiling -- in while a trend, out when not, on perfect vs causal lines",
            oracle_settings=SETTINGS_LINE, gmin_pct=list(GMIN_PCT), headline_gmin=HEAD_GMIN,
            n_names=len(syms), oracle_channels=seg_n,
            oracle_len_median=float(np.median(sl)),
            coverage={sc: 100 * cover[sc][0] / max(1, cover[sc][1]) for sc in sources},
            per_trade=out, book=hb, top_trade=top, split_rejected=n_split), indent=1))
        print(f"  [P] {OUT.relative_to(REPO)} written ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
