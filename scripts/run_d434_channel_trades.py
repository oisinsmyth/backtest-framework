"""D434 -- TRADING THE FINAL CHANNEL: enter on agreement, exit on a target or a trailing stop.

    uv run python -u scripts/run_d434_channel_trades.py --proof     assertions on 3 names
    uv run python -u scripts/run_d434_channel_trades.py             the whole panel

THE RULE, as the principal declared it (2026-09-10), and it is not searched:

  ENTER  at the close of bar e, when BOTH lines are drawn at e, their gradients have the SAME
         sign, both exceed delta, and they are SIMILAR --
             |g_sup - g_res| <= tau * max(|g_sup|, |g_res|)
         long if both rise, short if both fall. `tau` is the one parameter the principal did not
         fix; {0.25, 0.50, 1.00} is declared here and 0.50 is the headline (R13: 3 x 3 = 9 cells).

  EXIT   whichever comes first, on bars e+1 onward:
             TARGET   long: high >= resistance + m*ATR   (m in {1, 2, 3}; 2 is the headline)
                      short: low  <= support    - m*ATR
             TRAIL    long: low  <= support - 1*ATR, the level RATCHETING up only
                      short: high >= resistance + 1*ATR, ratcheting down only
             GONE     neither line is drawn any more  -- "exit when there are no support or
                      resistance [lines]"; while ONE survives the trade keeps going, which is the
                      principal's "so keep going with only one"
             EOD      the name's last bar
         A stop and a target inside the same bar is scored as the STOP (the pessimistic
         assumption; the bar's path is unknown at daily resolution). A gap through a level fills
         at the open, not the level.

  "KEEP GOING WITH ONLY ONE" NEEDS THE SIDES TO BE SEPARABLE, and the frozen cell couples them
  (`pairbreak`/`pairdraw` on: either line's invalidation kills both, and a bar draws both or
  neither). So two construction variants are run and both are reported:
      INDEPENDENT  pair_break = pair_draw = OFF -- the sides live and die separately, one can
                   outlive the other, and GONE means neither. THE PRINCIPAL'S RULE. Headline.
      PAIRED       CELL_FINAL exactly. The sides die together, so GONE fires at the first break
                   and the trail/target machinery rarely gets to speak. The control.
  Nothing else in the construction is touched.

CAUSALITY. The entry reads the channel at the close of e and buys at that close -- the repo's
`score[:, t-1] -> held at t` convention exactly. Each exit level for bar u is built from the last
bar at or before u-1 on which the side was drawn, with that segment's frozen (g, c) projected to
u, and from ATR at u-1: knowable at the previous close. `[L]` re-derives every entry from inputs
truncated at e.

P&L. Price return from the OHLC actually traded, PLUS the panel's dividend component over the
held bars (`total_log_returns - log_returns`), signed by direction -- so a dividend pays a long
and costs a short (D280's inversion). Cost is the Corwin-Schultz round-trip spread of the name
HELD over its own held bars, charged once (D285: never an assumed figure).
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

OUT = REPO / "data" / "d434_channel_trades.json"

TAU_GRID = (0.25, 0.50, 1.00)      # gradient similarity, relative
TP_GRID = (1.0, 2.0, 3.0)          # target, in ATR beyond the far line
HEAD_TAU, HEAD_TP = 0.50, 2.0      # the headline cell, declared before the run
STOP_ATR = 1.0                     # the principal's trailing stop, in ATR beyond the near line
ATR_W = 20                         # trailing mean of true range, the D412 convention
SPLIT_LR = 0.40                    # a single-bar |log return| this large is an unadjusted split
MIN_TRADES = 100                   # non-vacuity, per side
N_SIMS, NULL_SEED = 300, 0
PPY, RF, BORROW = 252.0, 0.04, 0.03


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


# --------------------------------------------------------------------------
# per-name inputs
# --------------------------------------------------------------------------


def atr_of(hi, lo, cl, w=ATR_W):
    """Trailing mean of true range, CAUSAL: atr[t] reads bars t-w+1..t, so a decision for bar
    u uses atr[u-1]. Never a fixed percentage (D387) and never the whole sample (D384)."""
    n = len(cl)
    pc = np.concatenate(([np.nan], cl[:-1]))
    tr = np.maximum(hi, pc) - np.minimum(lo, pc)
    tr[0] = hi[0] - lo[0]
    out = np.full(n, np.nan)
    c = np.cumsum(np.where(np.isfinite(tr), tr, 0.0))
    k = np.cumsum(np.isfinite(tr).astype(float))
    for t in range(w - 1, n):
        a = t - w
        num = c[t] - (c[a] if a >= 0 else 0.0)
        den = k[t] - (k[a] if a >= 0 else 0.0)
        out[t] = num / den if den > 0 else np.nan
    return out


def build_lines(RC, DR, PVT, bars, cell, pair):
    """The construction on one name's whole history. Returns per-bar drawn level and gradient per
    side, plus the projection of the LAST DRAWN segment to every later bar -- which is what the
    exit rule reads once a side has stopped being drawn."""
    m = len(bars)
    op = np.array([b.bar.open for b in bars], float)
    cl = np.array([b.bar.close for b in bars], float)
    hi = np.array([b.bar.high for b in bars], float)
    lo = np.array([b.bar.low for b in bars], float)
    with np.errstate(divide="ignore"):
        body = {"support": np.log(np.minimum(op, cl)), "resistance": np.log(np.maximum(op, cl))}
        ext = {"support": np.log(lo), "resistance": np.log(hi)}
    ps = PVT(bars, cell["k"])
    piv = {}
    for kd, sg in (("support", -1), ("resistance", +1)):
        piv[kd] = (np.array([p.index for p in ps if p.sign == sg], int),
                   np.log(np.array([p.price for p in ps if p.sign == sg], float)))
    G, L, S, why = RC.recalc_pair(
        piv, cell["k"], body, m,
        carry=cell["carry"], min_piv=cell["min_piv"],
        max_dg=RC.INF if cell["dg"] is None else DR.h_of_annual(cell["dg"]),
        max_dh=math.log1p(cell["dh"] / 100), use_body=cell["use_body"],
        min_width=math.log1p(cell["min_width"] / 100), delta=DR.DELTA, ext_log=ext,
        break_pivot=cell["break_pivot"], anchor_clear=cell["anchor_clear"],
        decay_end=cell["decay_end"], extend_back=cell["extend_back"],
        back_tol=None, fit_mode=cell["fit_mode"], touch_tol=cell["touch_tol"],
        min_touch=cell["min_touch"], height_mode=cell["height_mode"],
        walk_chain=cell["walk_chain"], max_reach=cell["max_reach"], syn_ttl=cell["syn_ttl"],
        stale_w=cell["stale_w"], stale_d=math.log1p(cell["stale_d"] / 100),
        stale_stat=cell["stale_stat"], fit_tol=math.log1p(cell["fit_tol"] / 100),
        pair_break=pair, pair_draw=pair, anchor_mode=cell["anchor_mode"],
        anchor_q=cell["anchor_q"], decay_mode=cell["decay_mode"],
        break_depth=math.log1p(cell["break_depth"] / 100), break_bars=cell["break_bars"],
        max_piv=cell["max_piv"])
    # the invariants the construction promises, on the WHOLE history rather than a window
    btol = math.log1p(cell["break_depth"] / 100)
    RC.assert_respects_body(L, body, np.ones(m, bool), tol=btol)
    RC.assert_no_inversion(L, np.ones(m, bool), math.log1p(cell["min_width"] / 100))

    proj, gproj, seen = {}, {}, {}
    q = np.arange(m, dtype=float)
    for kd in ("support", "resistance"):
        on = np.isfinite(L[kd])
        c_at = np.where(on, L[kd] - G[kd] * q, np.nan)          # the segment's frozen intercept
        idx = np.where(on, np.arange(m), -1)
        last = np.maximum.accumulate(idx)                        # last bar this side was drawn
        ok = last >= 0
        g_last = np.where(ok, G[kd][np.maximum(last, 0)], np.nan)
        c_last = np.where(ok, c_at[np.maximum(last, 0)], np.nan)
        proj[kd] = g_last * q + c_last          # the line, extended past its last drawn bar
        gproj[kd] = g_last
        seen[kd] = last
    return dict(m=m, op=op, cl=cl, hi=hi, lo=lo, G=G, L=L, proj=proj, gproj=gproj, seen=seen,
                drawn={kd: np.isfinite(L[kd]) for kd in ("support", "resistance")})


def entry_mask(N, elig, delta, tau):
    """The entry condition at the close of each bar. A SECOND path re-derives this in `[L]`."""
    gs, gr = N["G"]["support"], N["G"]["resistance"]
    both = N["drawn"]["support"] & N["drawn"]["resistance"] & elig
    with np.errstate(invalid="ignore"):
        big = (np.abs(gs) > delta) & (np.abs(gr) > delta)
        sim = np.abs(gs - gr) <= tau * np.maximum(np.abs(gs), np.abs(gr))
        up = both & big & sim & (gs > 0) & (gr > 0)
        dn = both & big & sim & (gs < 0) & (gr < 0)
    return np.where(up, 1, np.where(dn, -1, 0)).astype(np.int8)


# --------------------------------------------------------------------------
# the walk
# --------------------------------------------------------------------------


def walk(N, sig, atr, tp_mult, stop_atr=STOP_ATR):
    """One pass through a name: enter on `sig`, exit on target, trail, GONE or EOD. Returns a
    list of trades. Every level read for bar u is built from data at or before u-1."""
    m = N["m"]
    op, cl, hi, lo = N["op"], N["cl"], N["hi"], N["lo"]
    ps, pr = N["proj"]["support"], N["proj"]["resistance"]
    ds, dr = N["drawn"]["support"], N["drawn"]["resistance"]
    seen_s, seen_r = N["seen"]["support"], N["seen"]["resistance"]
    # JUMP BETWEEN CANDIDATES. Entries are sparse and stepping over every flat bar in Python was
    # the whole cost of this function: 18 walks per name over 4.1M bars is 74M iterations of a
    # loop that does nothing. Same trades, same order.
    cands = np.flatnonzero(sig != 0)
    trades, ptr = [], 0
    while ptr < cands.size:
        e = int(cands[ptr])
        if e >= m - 1:
            break
        d = int(sig[e])
        if not np.isfinite(cl[e]) or cl[e] <= 0:
            ptr += 1
            continue
        entry = float(cl[e])
        stop = np.nan
        u = e + 1
        while u < m:
            a = atr[u - 1]
            # the side's last drawn bar must be at or before u-1 for its level to be knowable
            sup_ok = seen_s[u - 1] >= 0
            res_ok = seen_r[u - 1] >= 0
            sup = math.exp(ps[u]) if sup_ok and np.isfinite(ps[u]) else np.nan
            res = math.exp(pr[u]) if res_ok and np.isfinite(pr[u]) else np.nan
            # GONE: neither side is drawn any more. One alive is enough to keep going.
            if not (ds[u - 1] or dr[u - 1]):
                trades.append((e, u, d, entry, float(cl[u]), "gone"))
                break
            if np.isfinite(a) and a > 0:
                if d > 0:
                    lvl = (sup - stop_atr * a) if np.isfinite(sup) else np.nan
                    if np.isfinite(lvl):
                        stop = lvl if not np.isfinite(stop) else max(stop, lvl)   # ratchets up
                    tp = (res + tp_mult * a) if np.isfinite(res) else np.nan
                    if np.isfinite(stop) and lo[u] <= stop:                      # stop first
                        trades.append((e, u, d, entry, float(min(stop, op[u])), "stop"))
                        break
                    if np.isfinite(tp) and hi[u] >= tp:
                        trades.append((e, u, d, entry, float(max(tp, op[u])), "target"))
                        break
                else:
                    lvl = (res + stop_atr * a) if np.isfinite(res) else np.nan
                    if np.isfinite(lvl):
                        stop = lvl if not np.isfinite(stop) else min(stop, lvl)   # ratchets down
                    tp = (sup - tp_mult * a) if np.isfinite(sup) else np.nan
                    if np.isfinite(stop) and hi[u] >= stop:
                        trades.append((e, u, d, entry, float(max(stop, op[u])), "stop"))
                        break
                    if np.isfinite(tp) and lo[u] <= tp:
                        trades.append((e, u, d, entry, float(min(tp, op[u])), "target"))
                        break
            u += 1
        else:
            trades.append((e, m - 1, d, entry, float(cl[m - 1]), "eod"))
        ptr = int(np.searchsorted(cands, trades[-1][1] + 1, side="left"))
    return trades


# --------------------------------------------------------------------------
# audits
# --------------------------------------------------------------------------


def audit_lag(RC, DR, PVT, bars, cell, pair, elig, delta, tau, probes):
    """[L] Re-derive the entry decision at sampled bars from inputs TRUNCATED at e: the bars cut
    to [0, e], pivots recomputed on the cut, the construction rerun. A rule that reads the future
    disagrees here. Returns the number of bars compared."""
    N = build_lines(RC, DR, PVT, bars, cell, pair)
    sig = entry_mask(N, elig, delta, tau)
    checked = 0
    for e in probes:
        if e < 30 or e >= N["m"]:
            continue
        N2 = build_lines(RC, DR, PVT, bars[:e + 1], cell, pair)
        s2 = entry_mask(N2, elig[:e + 1], delta, tau)
        if int(s2[e]) != int(sig[e]):
            raise AssertionError(
                f"[L] entry at bar {e}: full history says {int(sig[e])}, the truncated rebuild "
                f"says {int(s2[e])} -- the rule reads the future")
        checked += 1
    assert checked >= max(1, len(probes) // 2), (
        f"[L] VACUOUS: only {checked} of {len(probes)} probes compared")
    return checked


def audit_sign(trades, ret):
    """[S] IN MONEY. Inside a LONG trade the name-bar with the largest positive total log return
    must ADD to the trade's return; inside a SHORT it must SUBTRACT. Asserted on the real trades,
    and the mirror is asserted to FAIL, so the check cannot pass vacuously."""
    best = None
    for k, tr in enumerate(trades):
        e, x, d = tr["e"], tr["x"], tr["dir"]
        seg = ret[e + 1:x + 1]
        if seg.size == 0:
            continue
        j = int(np.nanargmax(seg))
        v = float(seg[j])
        if np.isfinite(v) and (best is None or v > best[0]):
            best = (v, k, d)
    assert best is not None, "[S] no trade carried a finite bar return"
    v, k, d = best
    contrib = d * v
    assert (contrib > 0) == (d > 0), (
        f"[S] the biggest up-bar inside a {'long' if d > 0 else 'short'} trade contributes "
        f"{contrib:+.4f} -- the direction sign is inverted")
    # and the mirror must FAIL, or the check above could not have failed either
    assert not ((-d * v > 0) == (d > 0)), "[S] SELF-TEST: the inverted direction also passes"
    return v, d


# --------------------------------------------------------------------------


def summarise(rows, label, spread_bp=None):
    """Per-trade lens: gross and net, mean AND median, both-tail trim, concentration."""
    if not rows:
        return dict(label=label, n=0)
    g = np.array([r["gross"] for r in rows], float)
    net = np.array([r["net"] for r in rows], float)
    hold = np.array([r["x"] - r["e"] for r in rows], float)
    lo_, hi_ = np.percentile(g, 1), np.percentile(g, 99)
    trimmed = g[(g >= lo_) & (g <= hi_)]
    pnl = g - g.min() if g.min() < 0 else g
    share = np.sort(g)[::-1]
    top1 = share[:max(1, len(share) // 100)].sum() / share.sum() if share.sum() != 0 else np.nan
    return dict(
        label=label, n=len(rows),
        gross_bp=1e4 * float(g.mean()), gross_med_bp=1e4 * float(np.median(g)),
        net_bp=1e4 * float(net.mean()), net_med_bp=1e4 * float(np.median(net)),
        trim_bp=1e4 * float(trimmed.mean()) if trimmed.size else float("nan"),
        ex_top_bp=1e4 * float(g[g <= hi_].mean()), ex_bot_bp=1e4 * float(g[g >= lo_].mean()),
        win=float((g > 0).mean()), hold_med=float(np.median(hold)), hold_mean=float(hold.mean()),
        payoff=float(g[g > 0].mean() / -g[g < 0].mean()) if (g < 0).any() and (g > 0).any() else float("nan"),
        skew=float(((g - g.mean()) ** 3).mean() / (g.std() ** 3)) if g.std() > 0 else float("nan"),
        top1_share=float(top1), breakeven_bp=1e4 * float(g.mean()),
        spread_bp=spread_bp, se_bp=1e4 * float(g.std(ddof=1) / math.sqrt(len(g))),
        by_exit={k: int(sum(1 for r in rows if r["why"] == k))
                 for k in ("target", "stop", "gone", "eod")})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--proof", action="store_true", help="assertions on a few names, no full run")
    ap.add_argument("--names", type=int, default=0, help="first N names (0 = all)")
    a = ap.parse_args()

    t0 = time.time()
    RC = _load("d399rc", "d399_recalc_segment.py")
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
    print(f"  {NS.SETTINGS_LINE_FINAL}")

    # ---- the floor, cross-sectional and causal (D343 keep_v2), and the spread grid
    CL = np.ascontiguousarray(panel.closes.T)
    live = np.ascontiguousarray(panel.live.T)
    VOL = np.full((T, n), np.nan)
    HIg, LOg = np.full((T, n), np.nan), np.full((T, n), np.nan)
    pos = {d: i for i, d in enumerate(panel.dates)}
    sym = {s: i for i, s in enumerate(panel.symbols)}
    rowmap = {}
    for s, bars in cleaned.items():
        i = sym.get(s)
        if i is None:
            continue
        rr = np.full(len(bars), -1, int)
        for j, st in enumerate(bars):
            t = pos.get(st.timestamp[:10])
            if t is not None:
                rr[j] = t
                VOL[t, i], HIg[t, i], LOg[t, i] = st.bar.volume, st.bar.high, st.bar.low
        rowmap[s] = rr
    ev = json.loads(Path(DR.MINING[1]).read_text(encoding="utf-8"))
    RAWF = UF.raw_price_factor(panel, ev)
    DV = X.roll_mean_T(CL * VOL)
    elig_grid = live & UF.floor_mask_v2(CL * RAWF, DV, live)
    CS = SP.corwin_schultz(HIg.T, LOg.T, panel.live)      # (n, T) round-trip proportional spread
    print(f"  floor: {100 * elig_grid.mean():.1f}% of cells eligible; spread grid built "
          f"({time.time() - t0:.0f}s)")

    LR = panel.log_returns
    TLR = panel.total_log_returns
    DIV = TLR - LR                                        # the dividend component, by construction

    syms = list(panel.symbols)
    if a.proof:
        syms = [s for s in ("BA", "COST", "SNPS") if s in sym] or syms[:3]
    elif a.names:
        syms = syms[:a.names]

    variants = (("INDEPENDENT", False), ("PAIRED", True))
    cells = [(tau, tp) for tau in TAU_GRID for tp in TP_GRID]
    # only the HEADLINE cell gets a book grid: 18 of them would be 950 MB on top of a 2.4 GB
    # panel, and the null is declared on the headline only
    hkey = ("INDEPENDENT", HEAD_TAU, HEAD_TP)
    book = {hkey: np.zeros((n, T), dtype=np.float32)}
    rows = {(v, tau, tp): [] for v, _ in variants for tau, tp in cells}
    n_split = 0
    t1 = time.time()
    for c, s in enumerate(syms):
        i = sym[s]
        bars = cleaned[s]
        rr = rowmap[s]
        good = rr >= 0
        if good.sum() < 60:
            continue
        elig = np.zeros(len(bars), bool)
        elig[good] = elig_grid[rr[good], i]
        lr = np.full(len(bars), np.nan)
        lr[good] = LR[i, rr[good]]
        dv = np.zeros(len(bars))
        dv[good] = np.nan_to_num(DIV[i, rr[good]])
        cs = np.full(len(bars), np.nan)
        cs[good] = CS[i, rr[good]]
        for vname, pair in variants:
            N = build_lines(RC, DR, PVT, bars, NS.CELL_FINAL, pair)
            atr = atr_of(N["hi"], N["lo"], N["cl"])
            for tau in TAU_GRID:
                sig = entry_mask(N, elig, DR.DELTA, tau)
                for tp in TP_GRID:
                    for (e, x, d, entry, exitp, why) in walk(N, sig, atr, tp):
                        if entry <= 0 or exitp <= 0:
                            continue
                        seg = slice(e + 1, x + 1)
                        held = np.abs(lr[seg])
                        if np.isfinite(held).any() and np.nanmax(held) > SPLIT_LR:
                            n_split += 1          # an unadjusted split, not a move (D399's guard)
                            continue
                        gross = d * (math.log(exitp / entry) + float(dv[seg].sum()))
                        sp = float(np.nanmean(cs[seg])) if np.isfinite(cs[seg]).any() else np.nan
                        sp = 0.0 if not np.isfinite(sp) else sp
                        rows[(vname, tau, tp)].append(dict(
                            sym=s, e=int(e), x=int(x), dir=int(d), gross=float(gross),
                            net=float(gross - sp), spread=sp, why=why,
                            date=bars[e].timestamp[:10]))
                        if (vname, tau, tp) == hkey:
                            book[hkey][i, rr[e + 1]:rr[x] + 1] = d
        if (c + 1) % 200 == 0:
            print(f"    {c + 1}/{len(syms)} names, {time.time() - t1:.0f}s")

    # ---- the audits, on the headline cell
    key = hkey
    s0 = syms[0]
    N0 = build_lines(RC, DR, PVT, cleaned[s0], NS.CELL_FINAL, False)
    el0 = np.zeros(len(cleaned[s0]), bool)
    g0 = rowmap[s0] >= 0
    el0[g0] = elig_grid[rowmap[s0][g0], sym[s0]]
    probes = [int(v) for v in np.linspace(60, N0["m"] - 2, 7).astype(int)]
    nchk = audit_lag(RC, DR, PVT, cleaned[s0], NS.CELL_FINAL, False, el0, DR.DELTA, HEAD_TAU, probes)
    print(f"\n  [L] {nchk} entry decisions on {s0} re-derived from a truncated rebuild  OK")
    tl = rows[key]
    sm = tl[0]["sym"]
    rsm = rowmap[sm]
    tot = np.full(len(cleaned[sm]), np.nan)
    gsm = rsm >= 0
    tot[gsm] = TLR[sym[sm], rsm[gsm]]
    v, d = audit_sign([r for r in tl if r["sym"] == sm], tot)
    print(f"  [S] the largest up-bar inside a {'long' if d > 0 else 'short'} trade on {sm} "
          f"({1e4 * v:+.0f} bp) contributes with the right sign  OK")
    for side, want in ((1, "long"), (-1, "short")):
        k = sum(1 for r in tl if r["dir"] == side)
        print(f"  [N] {want} trades: {k}" + ("" if k >= MIN_TRADES or a.proof
                                             else f"  << {MIN_TRADES}, VACUOUS"))

    # ---- report
    print(f"\n  PER TRADE, gross bp -- the declared 9-cell grid, both variants (R13)")
    print(f"  {'variant':<12s} {'tau':>5s} {'tp':>4s} {'side':<6s} {'n':>6s} {'gross':>8s} "
          f"{'med':>8s} {'net':>8s} {'win%':>5s} {'hold':>5s} {'tgt/stop/gone':>15s}")
    out = {}
    for vname, _p in variants:
        for tau, tp in cells:
            rr2 = rows[(vname, tau, tp)]
            for side, nm in ((1, "long"), (-1, "short")):
                sub = [r for r in rr2 if r["dir"] == side]
                st = summarise(sub, f"{vname}/tau{tau}/tp{tp}/{nm}")
                out[f"{vname}|{tau}|{tp}|{nm}"] = st
                if st["n"]:
                    b = st["by_exit"]
                    print(f"  {vname:<12s} {tau:>5.2f} {tp:>4.1f} {nm:<6s} {st['n']:>6d} "
                          f"{st['gross_bp']:>8.1f} {st['gross_med_bp']:>8.1f} {st['net_bp']:>8.1f} "
                          f"{100 * st['win']:>5.0f} {st['hold_med']:>5.0f} "
                          f"{b['target']:>5d}/{b['stop']}/{b['gone']}")

    # ---- the null and the book, on the headline cell only
    hb = {}
    emask = np.ascontiguousarray(elig_grid.T.astype(float))
    np.save(REPO / "temp" / "d434_book_headline.npy", book[key])   # so the book can be re-scored
    try:
        FN = _load("fastnull", "fast_null.py")
        for side, nm in ((1, "long"), (-1, "short"), (0, "both")):
            p = book[key].astype(np.float64)
            if side > 0:
                p[p < 0] = 0.0
            elif side < 0:
                p[p > 0] = 0.0
            # THE MASK GOES ON THE POSITION, NOT ONLY ON THE NULL'S CONTEXT. The first version
            # passed `mask=` to the context and scored an unmasked book, and
            # `assert_matches_scorer` refused it -- which is the whole reason that assertion is
            # called once per study. Both now see the same book.
            p *= emask
            if not p.any():
                continue
            ctx = FN.NullContext(panel, mask=emask)
            sc = RP.score(panel, p, 0, ppy=PPY, rf_annual=RF, borrow_annual=BORROW)
            ctx.assert_matches_scorer(p, lambda q: RP.score(panel, q, 0, ppy=PPY, rf_annual=RF,
                                                            borrow_annual=BORROW),
                                      rf_annual=RF, borrow_annual=BORROW, ppy=PPY)
            sh, mn = FN.rotation_null(ctx, p, 0, n_sims=N_SIMS, seed=NULL_SEED, ppy=PPY,
                                      rf_annual=RF, borrow_annual=BORROW)
            p95 = float(np.percentile(mn, 95))
            bs = np.array([np.percentile(np.random.default_rng(k).choice(mn, mn.size), 95)
                           for k in range(200)])
            hb[nm] = dict(total_return=sc["total_return"], sharpe=sc["excess_sharpe"],
                          exposure=sc["exposure_gross"], maxdd=sc["max_drawdown"],
                          entries=sc["entries"], null_p50=float(np.percentile(mn, 50)),
                          null_p95=p95, null_p95_se=float(bs.std(ddof=1)))
            print(f"  [BOOK] {nm:<5s} total {100 * sc['total_return']:>7.1f}%  sharpe "
                  f"{sc['excess_sharpe']:>5.2f}  expo {sc['exposure_gross']:.3f}  null p50 "
                  f"{100 * hb[nm]['null_p50']:>7.1f}%  p95 {100 * p95:>7.1f}% "
                  f"(SE {100 * hb[nm]['null_p95_se']:.1f})")
    except Exception as exc:                       # the book lens must not lose the trade lens
        print(f"  [BOOK] not scored: {type(exc).__name__}: {exc}")
        hb = dict(error=f"{type(exc).__name__}: {exc}")

    # ---- WHAT THE WINNERS DEPEND ON (CLAUDE.md group 3), on the headline cell
    conc = {}
    for side, nm in ((1, "long"), (-1, "short")):
        sub = [r for r in tl if r["dir"] == side]
        if not sub:
            continue
        byname = {}
        for r in sub:
            byname[r["sym"]] = byname.get(r["sym"], 0.0) + r["gross"]
        vals = np.array(sorted(byname.values(), reverse=True), float)
        tot_p = vals.sum()
        half = int(np.searchsorted(np.cumsum(vals), 0.5 * tot_p) + 1) if tot_p > 0 else None
        yrs = {}
        for r in sub:
            yrs.setdefault(r["date"][:4], []).append(r["gross"])
        conc[nm] = dict(
            names=len(byname), names_to_half_pnl=half,
            top1_name_share=float(vals[0] / tot_p) if tot_p > 0 else None,
            top5_name_share=float(vals[:5].sum() / tot_p) if tot_p > 0 else None,
            top10_name_share=float(vals[:10].sum() / tot_p) if tot_p > 0 else None,
            gme_trade_share=float(sum(1 for r in sub if r["sym"] == "GME") / len(sub)),
            years_profitable=int(sum(1 for v in yrs.values() if np.mean(v) > 0)),
            years=len(yrs),
            mean_by_year={y: 1e4 * float(np.mean(v)) for y, v in sorted(yrs.items())})
        c = conc[nm]
        print(f"  [CONC] {nm:<5s} {c['names']} names, {c['names_to_half_pnl']} to half the P&L, "
              f"top-1 {100 * (c['top1_name_share'] or 0):.0f}% top-10 "
              f"{100 * (c['top10_name_share'] or 0):.0f}%, GME {100 * c['gme_trade_share']:.1f}% "
              f"of trades, {c['years_profitable']}/{c['years']} years positive")

    top = max(rows[key], key=lambda r: r["gross"]) if rows[key] else None
    if top:
        print(f"\n  TOP TRADE (headline cell): {top['sym']} {top['date']} bars {top['e']}->{top['x']} "
              f"{'long' if top['dir'] > 0 else 'short'} {1e4 * top['gross']:+.0f} bp, exit {top['why']}")
    print(f"  split-guard rejections: {n_split}")
    if not a.proof:
        OUT.write_text(json.dumps(dict(
            what="D434: the final channel traded -- enter on agreement, exit on target/trail",
            settings_line=NS.SETTINGS_LINE_FINAL, tau_grid=list(TAU_GRID), tp_grid=list(TP_GRID),
            headline=dict(tau=HEAD_TAU, tp=HEAD_TP, variant="INDEPENDENT"),
            stop_atr=STOP_ATR, atr_w=ATR_W, n_names=len(syms), per_trade=out, book=hb,
            concentration=conc, top_trade=top, split_rejected=n_split), indent=1))
        print(f"  [P] {OUT.relative_to(REPO)} written ({time.time() - t0:.0f}s total)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
