"""D478 -- TRADING THE GROW-RIGHT LINES, IN-SAMPLE. Spec: docs/decisions/D478-trading-the-grow-right-lines-in-sample.md

    uv run python scripts/run_d478_grow_trades.py --proof        three names, audits, no file
    uv run python scripts/run_d478_grow_trades.py                the panel; ~20 min over 12 processes

THE SAME RULE AS D477 (in while a trend, out when not; minimum gradient swept), on two causal
line sources in one run: GROW (D478's construction, the principal's line below, from bar 0 of
each name) and CAUSAL (D399's CELL_FINAL, D477's causal arm, so its numbers must reproduce).
Both are causal, so both get nulls: a within-name time rotation of the trend-state series per
trade (200 draws) and D476's book rotation null on the headline books.

SPEED. The grow-right walk is pure Python at ~1 ms/bar; 5.5 M bars over 12 processes. Workers
receive only a name's four price arrays and return its runs, and load the estimator module
once in an initializer -- the panel never leaves the parent (D427's lesson: measure the worker
before the fan-out; one worker here is numpy plus one module).

EXACTNESS. The per-trade null needs a vectorised trade extractor; [V] asserts it returns the
same (entry, exit, side) list as D477's loop on every real state series, and the same gross
per trade to 1e-9 bp (the log of a ratio versus a difference of cumulative sums is not the
same float; the tolerance is stated, not hidden).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import multiprocessing as mp
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "d478_grow_trades.json"

LINE = ("split=causal grow=parallel back=9 atmax=end tol=2 mt=2 basis=wick minlen=30 maxlen=1000 "
        "mw=5.5 maxw=55 maxoff=6.5 mintd=10 tau=1 brk=-1 bbars=1 bon=close")
GMIN_PCT = (0.0, 10.0, 25.0, 50.0, 100.0, 200.0)
HEAD_GMIN = 25.0
# D482, THE LEVEL RULE: not which way the lines point but where the close sits between them.
# pos = (log close - support level) / (resistance level - support level), both lines drawn;
# long on pos <= POS_LO, short on pos >= POS_HI, held HOLD bars after the entry bar (a further
# qualifying bar inside the hold extends it). The sweep is over the hold.
HOLDS = (1, 3, 5, 10, 20)
HEAD_HOLD = 5
POS_LO, POS_HI = 0.10, 0.90


def level_state(N, elig, hold):
    """+1 / -1 / 0 at each bar's close under the level rule."""
    ls, lr = N["L"]["support"], N["L"]["resistance"]
    both = N["drawn"]["support"] & N["drawn"]["resistance"] & elig
    with np.errstate(invalid="ignore", divide="ignore"):
        width = lr - ls
        pos = np.where(both & (width > 0), (np.log(N["cl"]) - ls) / np.where(width > 0, width, 1.0), np.nan)
        raw = np.where(pos <= POS_LO, 1, np.where(pos >= POS_HI, -1, 0)).astype(np.int8)
    raw[~np.isfinite(pos)] = 0
    state = np.zeros(raw.size, np.int8)
    cur, left = 0, 0
    for t in range(raw.size):
        if raw[t] != 0:
            cur, left = int(raw[t]), int(hold)
            state[t] = cur
        elif left > 0:
            state[t] = cur
            left -= 1
    return state


def dip_state(N, elig, hold, x, n, drawn_only):
    """D483, THE DIP CONTROL: +1 on a close more than `x` (log) below the lowest low of the
    previous `n` bars, -1 on a close more than `x` above the highest high of the previous `n`
    bars, held `hold` bars -- no lines consulted, unless `drawn_only`, which restricts the
    events to bars on which the source has both lines drawn (the channel's existence without
    its level)."""
    m = N["m"]
    lcl, llo, lhi = np.log(N["cl"]), np.log(N["lo"]), np.log(N["hi"])
    raw = np.zeros(m, np.int8)
    for t in range(n, m):
        if not elig[t]:
            continue
        if drawn_only and not (N["drawn"]["support"][t] and N["drawn"]["resistance"][t]):
            continue
        lo_n, hi_n = np.nanmin(llo[t - n:t]), np.nanmax(lhi[t - n:t])
        if lcl[t] < lo_n - x:
            raw[t] = 1
        elif lcl[t] > hi_n + x:
            raw[t] = -1
    state = np.zeros(m, np.int8)
    cur, left = 0, 0
    for t in range(m):
        if raw[t] != 0:
            cur, left = int(raw[t]), int(hold)
            state[t] = cur
        elif left > 0:
            state[t] = cur
            left -= 1
    return state


def audit_no_future_state(N, elig, probes, fn):
    """[F] the state at bar e depends only on what is known at bars <= e: delete every later
    level, gradient, drawn flag and PRICE, and re-derive. `fn(N, elig)` is the state function."""
    base = fn(N, elig)
    checked = 0
    for e in probes:
        if e < 35 or e >= N["m"]:
            continue
        N2 = dict(N)
        N2["L"] = {k: v.copy() for k, v in N["L"].items()}
        N2["G"] = {k: v.copy() for k, v in N["G"].items()}
        N2["drawn"] = {k: v.copy() for k, v in N["drawn"].items()}
        for kd in ("support", "resistance"):
            N2["L"][kd][e + 1:] = np.nan
            N2["G"][kd][e + 1:] = np.nan
            N2["drawn"][kd][e + 1:] = False
        for q in ("cl", "lo", "hi"):
            if q in N:
                arr = N[q].astype(float).copy()
                arr[e + 1:] = np.nan
                N2[q] = arr
        if int(fn(N2, elig)[e]) != int(base[e]):
            raise AssertionError(f"[F] the state at bar {e} moves when the future is deleted")
        checked += 1
    assert checked >= max(1, len(probes) // 2), f"[F] VACUOUS: {checked}/{len(probes)}"
    return checked
N_SIMS_TRADE, N_SIMS_BOOK, NULL_SEED = 200, 300, 0
PPY, RF, BORROW = 252.0, 0.04, 0.03
SPLIT_LR = 0.40
MIN_TRADES = 100
WORKERS = 12
SOURCES = ("GROW", "CAUSAL")


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


# ----------------------------------------------------------------------------- the GROW worker
_W = {}


def _init(line):
    # A WORKER THAT DIES AT START IS INVISIBLE: the pool respawns it forever and the parent
    # burns half a core doing so, with nothing in the log. So every worker failure is written
    # to a file the parent can read.
    try:
        _W["RC"] = _load("d399rc", "d399_recalc_segment.py")
        _W["CG"] = _load("d451cg", "d478_causal_grow.py")
        _W["P"] = _W["CG"].parse_line(line)
    except BaseException:
        import traceback
        (REPO / "temp" / "d478_worker.err").write_text(traceback.format_exc())
        raise


def _grow(args):
    try:
        return _grow_inner(args)
    except BaseException:
        import traceback
        (REPO / "temp" / "d478_worker.err").write_text(f"{args[0]}\n" + traceback.format_exc())
        raise


def _hand_init():
    """D481: the hand cell per name in a worker. The pivot construction is GIL-bound Python at
    ~1-2 s a name; over processes the panel's 1,573 names take minutes, not the better part of
    an hour. ARRAYS ONLY cross into the worker: the pivots are detected in the parent (the
    detector needs the bar objects and the fixture modules, and a worker that imported those
    hung), and the worker loads the estimator module and the cell, nothing else."""
    _W["RC"] = _load("d399rc", "d399_recalc_segment.py")
    _W["HC"] = _load("d460hc", "d480_hand_cell.py")


def _hand(args):
    sym, op, cl, hi, lo, piv, delta, max_dg = args
    try:
        t0 = time.time()
        HC = _W["HC"]
        N = HC.lines_from_arrays(_W["RC"], op, cl, hi, lo, piv, HC.CELL_HAND, HC.MARGIN, delta, max_dg)
        return sym, N, time.time() - t0
    except BaseException:
        import traceback
        (REPO / "temp" / "d481_worker.err").write_text(f"{sym}\n" + traceback.format_exc())
        raise


def _grow_inner(args):
    sym, o, h, l, c = args
    CG, RC, P = _W["CG"], _W["RC"], _W["P"]
    with np.errstate(divide="ignore"):
        if P["basis"] == "body":
            lo, hi = np.log(np.minimum(o, c)), np.log(np.maximum(o, c))
        else:
            lo, hi = np.log(l), np.log(h)
        cl = np.log(c)
    t0 = time.time()
    runs = CG.causal_channels(RC, lo, hi, P, cl=cl)
    return sym, [dict(a=r["a"], b=r["b"], A=r["A"], As=r["As"], gs=r["gs"], cs=r["cs"],
                      gr=r["gr"], cr=r["cr"], ts=r["ts"], tr=r["tr"], off=r["off"],
                      td=r["td"], w=r["w"]) for r in runs], time.time() - t0


# ----------------------------------------------------------------------------- vectorised trades
def trades_np(state, cl, lcl, cum_dv, cum_jump):
    """Every maximal run of a non-zero state -> (e, x, d, gross, split). Same trades as
    D477's `trend_trades`: enter at the close of the run's first bar, exit at the close of the
    first bar outside it (or the last bar). `cum_dv` and `cum_jump` are cumulative sums with a
    leading zero, so a segment [e+1, x] sums to cum[x+1] - cum[e+1]."""
    m = state.size
    if m == 0:
        return np.empty(0, int), np.empty(0, int), np.empty(0, int), np.empty(0), np.empty(0, bool)
    ch = np.flatnonzero(np.diff(state) != 0) + 1
    starts = np.concatenate(([0], ch))
    ends = np.concatenate((ch, [m]))
    d = state[starts]
    keep = d != 0
    e, u, d = starts[keep], ends[keep], d[keep]
    x = np.minimum(u, m - 1)
    ok = (x > e) & np.isfinite(cl[e]) & (cl[e] > 0) & np.isfinite(cl[x]) & (cl[x] > 0)
    e, x, d = e[ok], x[ok], d[ok]
    gross = d * (np.log(cl[x] / cl[e]) + (cum_dv[x + 1] - cum_dv[e + 1]))
    split = (cum_jump[x + 1] - cum_jump[e + 1]) > 0
    return e, x, d, gross, split


def trade_null(states, cls, lcls, cum_dvs, cum_jumps, eligs, n_sims, seed):
    """WITHIN-NAME TIME ROTATION OF THE STATE SERIES. Each name's +1/-1/0 series is rolled by a
    random offset and re-masked to its eligible bars (the null lives in the tradeable universe),
    then the same extractor runs against the real closes. Trade count, duration and name are
    preserved; timing is destroyed. Returns the mean gross per trade per side, per draw."""
    rng = np.random.default_rng(seed)
    out = np.full((n_sims, 2), np.nan)
    for k in range(n_sims):
        s = np.zeros(2)
        n = np.zeros(2)
        for st, cl, lcl, cdv, cj, el in zip(states, cls, lcls, cum_dvs, cum_jumps, eligs):
            m = st.size
            off = int(rng.integers(0, m)) if m > 1 else 0
            r = np.roll(st, off)
            r[~el] = 0
            e, x, d, g, sp = trades_np(r, cl, lcl, cdv, cj)
            g = g[~sp]
            d = d[~sp]
            for j, side in enumerate((1, -1)):
                sel = d == side
                s[j] += g[sel].sum()
                n[j] += sel.size and sel.sum()
        out[k] = np.where(n > 0, s / np.maximum(n, 1), np.nan)
    return out


# ----------------------------------------------------------------------------- main
def main() -> int:
    global LINE, OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--proof", action="store_true")
    ap.add_argument("--names", type=int, default=0)
    ap.add_argument("--workers", type=int, default=WORKERS)
    ap.add_argument("--line", default=LINE, help="the GROW settings line (default: D478's)")
    ap.add_argument("--out", default=str(OUT), help="the result file (default: D478's)")
    ap.add_argument("--tag", default="D478", help="the decision the run belongs to")
    ap.add_argument("--source", default="grow", choices=("grow", "hand"),
                    help="what fills the first column: the grow-right walk, or D480's hand cell (D481)")
    ap.add_argument("--rule", default="trend", choices=("trend", "level", "dip"),
                    help="trend: in while a trend (D477); level: position in the channel, held HOLD bars (D482); "
                         "dip: a close beyond the previous N bars' range by X, no lines (D483)")
    ap.add_argument("--head", type=float, default=None, help="override the headline sweep value (null and book)")
    ap.add_argument("--dip-x", type=float, default=4.0, help="dip rule: per cent beyond the previous range")
    ap.add_argument("--dip-n", type=int, default=30, help="dip rule: bars of previous range")
    ap.add_argument("--dip-drawn", action="store_true", help="dip rule: only on bars with both lines drawn")
    a = ap.parse_args()
    LEVEL = a.rule != "trend"                      # level and dip share the hold sweep
    SWEEP = HOLDS if LEVEL else GMIN_PCT
    HEAD = a.head if a.head is not None else (HEAD_HOLD if LEVEL else HEAD_GMIN)
    if LEVEL:
        HEAD = int(HEAD)
    assert HEAD in SWEEP, f"headline {HEAD} not in the sweep {SWEEP}"
    SWNAME = "hold" if LEVEL else "gmin"
    DIPX = math.log1p(a.dip_x / 100)
    LINE, OUT = a.line, Path(a.out).resolve()      # resolved: the final print is repo-relative
    HC = _load("d460hc", "d480_hand_cell.py") if a.source == "hand" else None
    LBL = "HAND" if a.source == "hand" else "GROW"
    if HC is not None:
        LINE = HC.SETTINGS_LINE_HAND

    t0 = time.time()
    RC = _load("d399rc", "d399_recalc_segment.py")
    CG = _load("d451cg", "d478_causal_grow.py")
    D7 = _load("d450", "run_d477_oracle_ceiling.py")
    D4 = _load("d434", "run_d476_channel_trades.py")
    NS = _load("d399ns", "d399_new_sample.py")
    DR = _load("d399draw", "d399_draw_construction.py")
    RP = _load("rp", "ragged_panel.py")
    X = _load("d320", "run_d320_tilt_filters.py")
    UF = _load("d339uf", "d339_universe_floor.py")
    SP = _load("d285sp", "d285_spread_estimate.py")
    FN = _load("fastnull", "fast_null.py")
    UF.bind(X, None)
    from backtest_framework.research.structure import pivots_tie_tolerant as PVT

    P = CG.parse_line(LINE)
    panel, cleaned = RP.load_ragged(*DR.MINING, fee_bps=0.0, dividend_bound=True)
    T, n = len(panel.dates), len(panel.symbols)
    print(f"\n  panel {n} names x {T} dates in {time.time() - t0:.0f}s")
    print(f"  {LBL:<6s} {LINE}")
    print(f"  CAUSAL D399 CELL_FINAL (D477's causal arm)")
    if a.rule == "dip":
        print(f"  RULE   DIP CONTROL: long on a close more than {a.dip_x:g}% below the lowest low of the previous "
              f"{a.dip_n} bars, short on a close more than {a.dip_x:g}% above the highest high"
              f"{' -- only on bars with both lines drawn' if a.dip_drawn else ' -- NO LINES'}; "
              f"held {list(HOLDS)} bars; headline {HEAD}")
    elif LEVEL:
        print(f"  RULE   LEVEL: long on close at or below {POS_LO:.0%} of the channel, short at or above "
              f"{POS_HI:.0%}, held {list(HOLDS)} bars; headline {HEAD}")
    else:
        print(f"  RULE   in while a trend, out when not; minimum gradient swept {list(GMIN_PCT)} %/yr; "
              f"NO target, NO stop; headline {HEAD_GMIN:.0f}")

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

    syms = [s for s in panel.symbols if (rowmap[s] >= 0).sum() >= 60]
    if a.proof:
        syms = [s for s in ("BA", "COST", "SNPS") if s in sym] or syms[:3]
    elif a.names:
        syms = syms[:a.names]

    # ---- the GROW walk, over processes; longest names first so the tail is short
    grow_runs, hand_N, cpu, wall = {}, {}, 0.0, 0.0
    if a.source == "grow":
        items = sorted(syms, key=lambda s: -len(cleaned[s]))
        tot_bars = sum(len(cleaned[s]) for s in items)
        print(f"  [P] GROW walk: {tot_bars / 1e6:.2f} M bars at ~1 ms/bar over {a.workers} workers "
              f"-> projected {tot_bars * 1e-3 / a.workers / 60:.0f} min wall")
        t1 = time.time()
        args = [(s, *(np.array([getattr(b.bar, k) for b in cleaned[s]], float) for k in ("open", "high", "low", "close")))
                for s in items]
        if a.workers > 1 and len(items) > 3:
            with mp.get_context("spawn").Pool(a.workers, initializer=_init, initargs=(LINE,)) as pool:
                for k, (s, runs, dt) in enumerate(pool.imap_unordered(_grow, args, chunksize=4)):
                    grow_runs[s], cpu = runs, cpu + dt
                    if (k + 1) % 200 == 0:
                        print(f"    grow {k + 1}/{len(items)} names, {time.time() - t1:.0f}s wall")
        else:
            _init(LINE)
            for s, runs, dt in map(_grow, args):
                grow_runs[s], cpu = runs, cpu + dt
        wall = time.time() - t1
        print(f"  [SPEED] GROW walk {wall:.0f}s wall, sum(item time)/wall = {cpu / max(wall, 1e-9):.2f}x"
              + ("" if a.workers == 1 or cpu / max(wall, 1e-9) >= 0.7 * a.workers else "  << BELOW 70% EFFICIENCY"))
    else:
        hand_N = {}
        if a.workers > 1 and len(syms) > 3:
            items = sorted(syms, key=lambda s: -len(cleaned[s]))
            print(f"  [P] HAND cell (D480): the pivot construction on {len(items)} names over {a.workers} workers "
                  f"(~1.5 s a name single-threaded -> projected {1.5 * len(items) / a.workers / 60:.0f} min wall)")
            t1 = time.time()
            max_dg = RC.INF if HC.CELL_HAND["dg"] is None else DR.h_of_annual(HC.CELL_HAND["dg"])
            hand_args = []
            for s in items:                      # pivots in the parent: the detector needs the bar objects
                bb = cleaned[s]
                hand_args.append((s, *(np.array([getattr(b.bar, q) for b in bb], float) for q in ("open", "close", "high", "low")),
                                  HC.pivots_of(PVT, bb, HC.CELL_HAND["k"]), DR.DELTA, max_dg))
            print(f"    pivots detected for {len(items)} names in {time.time() - t1:.0f}s")
            with mp.get_context("spawn").Pool(a.workers, initializer=_hand_init) as pool:
                for k, (s, N, dt) in enumerate(pool.imap_unordered(_hand, hand_args, chunksize=2)):
                    hand_N[s], cpu = N, cpu + dt
                    if (k + 1) % 200 == 0:
                        print(f"    hand {k + 1}/{len(items)} names, {time.time() - t1:.0f}s wall")
            wall = time.time() - t1
            print(f"  [SPEED] HAND cell {wall:.0f}s wall, sum(item time)/wall = {cpu / max(wall, 1e-9):.2f}x"
                  + ("" if cpu / max(wall, 1e-9) >= 0.7 * a.workers else "  << BELOW 70% EFFICIENCY"))
        else:
            print(f"  [P] HAND cell (D480): the pivot construction per name in the trades loop, single process")

    # ---- trades, both sources, every gmin
    GM = {p: math.log1p(p / 100) / 252.0 for p in GMIN_PCT}

    def state_of(N_, elig_, p_):
        if a.rule == "dip":
            return dip_state(N_, elig_, p_, DIPX, a.dip_n, a.dip_drawn)
        return level_state(N_, elig_, p_) if LEVEL else D7.trend_state(N_, elig_, GM[p_])

    rows = {(sc, p): [] for sc in SOURCES for p in SWEEP}
    book = {sc: np.zeros((n, T), dtype=np.float32) for sc in SOURCES}
    cover = {sc: [0, 0] for sc in SOURCES}
    null_in = {sc: dict(states=[], cls=[], lcls=[], cum_dvs=[], cum_jumps=[], eligs=[]) for sc in SOURCES}
    n_split, run_len, win_len = 0, [], []
    tot_by_sym, sym_of = {}, {}
    n_v, worst_v = 0, 0.0
    t2 = time.time()
    N0, el0 = None, None
    for c, s in enumerate(syms):
        i = sym[s]
        bars = cleaned[s]
        rr = rowmap[s]
        good = rr >= 0
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
        jump = np.nan_to_num(np.abs(lr)) > SPLIT_LR
        cum_dv = np.concatenate(([0.0], np.cumsum(dv)))
        cum_jump = np.concatenate(([0], np.cumsum(jump.astype(int))))
        for sc in SOURCES:
            if sc == "GROW":
                if HC is not None:
                    N = hand_N[s] if s in hand_N else HC.hand_lines(RC, DR, PVT, bars, HC.CELL_HAND, HC.MARGIN)
                    for kd in ("support", "resistance"):    # drawn-run lengths, from the mask
                        dr_ = N["drawn"][kd].astype(int)
                        ch_ = np.flatnonzero(np.diff(np.concatenate(([0], dr_, [0]))))
                        run_len += list(ch_[1::2] - ch_[0::2])
                    win_len = run_len
                else:
                    N, runs = CG.causal_lines(RC, bars, P, runs=grow_runs[s])
                    run_len += [r["b"] - r["a"] + 1 for r in runs]
                    win_len += [r["b"] - r["A"] + 1 for r in runs]
                if N0 is None:
                    N0, el0 = N, elig
            else:
                N = D4.build_lines(RC, DR, PVT, bars, NS.CELL_FINAL, True)
            cover[sc][0] += int((N["drawn"]["support"] & N["drawn"]["resistance"]).sum())
            cover[sc][1] += m
            lcl = np.log(N["cl"])
            for p in SWEEP:
                state = state_of(N, elig, p)
                loop = D7.trend_trades(state, N["cl"])
                if p == HEAD:
                    # [V] the vectorised extractor against the loop, on the real series
                    e, x, d, g, spl = trades_np(state, N["cl"], lcl, cum_dv, cum_jump)
                    if [(int(a_), int(b_), int(c_)) for a_, b_, c_ in zip(e, x, d)] != [(a_, b_, c_) for a_, b_, c_ in loop]:
                        raise AssertionError(f"[V] vectorised trades differ from the loop on {s}/{sc}")
                    n_v += len(loop)
                    for (e_, x_, d_), g_ in zip(loop, g):
                        seg = slice(e_ + 1, x_ + 1)
                        gl = d_ * (math.log(N["cl"][x_] / N["cl"][e_]) + float(dv[seg].sum()))
                        worst_v = max(worst_v, abs(1e4 * (gl - g_)))
                    nl = null_in[sc]
                    nl["states"].append(state)
                    nl["cls"].append(N["cl"])
                    nl["lcls"].append(lcl)
                    nl["cum_dvs"].append(cum_dv)
                    nl["cum_jumps"].append(cum_jump)
                    nl["eligs"].append(elig)
                for (e_, x_, d_) in loop:
                    seg = slice(e_ + 1, x_ + 1)
                    held = np.abs(lr[seg])
                    if np.isfinite(held).any() and np.nanmax(held) > SPLIT_LR:
                        n_split += 1
                        continue
                    gross = d_ * (math.log(N["cl"][x_] / N["cl"][e_]) + float(dv[seg].sum()))
                    sp = float(np.nanmean(cs[seg])) if np.isfinite(cs[seg]).any() else 0.0
                    sp = 0.0 if not np.isfinite(sp) else sp
                    rows[(sc, p)].append(dict(sym=s, e=int(e_), x=int(x_), dir=int(d_),
                                              gross=float(gross), net=float(gross - sp),
                                              spread=sp, date=bars[e_].timestamp[:10]))
                    if p == HEAD and rr[e_ + 1] >= 0 and rr[x_] >= 0:
                        book[sc][i, rr[e_ + 1]:rr[x_] + 1] = d_
        if (c + 1) % 200 == 0:
            print(f"    trades {c + 1}/{len(syms)} names, {time.time() - t2:.0f}s")
    if worst_v > 1e-9:
        raise AssertionError(f"[V] gross differs by up to {worst_v:.2e} bp between extractors")
    print(f"  [V] vectorised extractor == loop on {n_v} real trades: same (e, x, d), gross within "
          f"{worst_v:.1e} bp  OK")
    # [XV] the vectorised comparison must be able to fail: a state rolled by one bar
    st = null_in["GROW"]["states"][0]
    if trades_np(np.roll(st, 1), null_in["GROW"]["cls"][0], null_in["GROW"]["lcls"][0],
                 null_in["GROW"]["cum_dvs"][0], null_in["GROW"]["cum_jumps"][0])[0].tolist() \
            == [t for t, _, _ in D7.trend_trades(st, null_in["GROW"]["cls"][0])]:
        raise AssertionError("[XV] a one-bar shift of the state was not distinguishable")
    print(f"  [XV] the extractor comparison rejects a one-bar shift  OK")

    rl, wl = np.array(run_len, float), np.array(win_len, float)
    print(f"\n  {LBL}: {len(rl):,} drawn runs | drawn length median {np.median(rl):.0f} p90 "
          f"{np.percentile(rl, 90):.0f} max {rl.max():.0f} | window median {np.median(wl):.0f} | "
          f"both lines drawn on {100 * cover['GROW'][0] / max(1, cover['GROW'][1]):.0f}% of bars "
          f"(CAUSAL {100 * cover['CAUSAL'][0] / max(1, cover['CAUSAL'][1]):.0f}%)")

    pr = [int(v) for v in np.linspace(30, N0["m"] - 2, 9).astype(int)]
    nf = (audit_no_future_state(N0, el0, pr, lambda N_, e_: state_of(N_, e_, HEAD)) if LEVEL
          else D7.audit_no_future(N0, el0, GM[HEAD], pr))
    print(f"  [F] {nf} states on {syms[0]} unchanged when every future level is deleted  OK")
    hkey = ("GROW", HEAD)
    v, d = D7.audit_sign(rows[hkey], sym_of, tot_by_sym)
    print(f"  [S] the largest up-bar inside a {'long' if d > 0 else 'short'} {LBL} trade "
          f"({1e4 * v:+.0f} bp) contributes with the right sign  OK")

    # ---- per-trade table
    print(f"\n  PER TRADE, gross bp -- {LBL} ({'D480 hand cell' if HC else 'grow-right lines'}) vs CAUSAL (D399's CELL_FINAL), SAME rule")
    print(f"  {SWNAME:>6s} {'side':<6s} {'':<2s}{'n':>7s} {'gross':>8s} {'+-SE':>6s} {'med':>8s} "
          f"{'trim':>8s} {'net':>8s} {'win%':>5s} {'hold':>5s}   |   "
          f"{'n':>7s} {'gross':>8s} {'+-SE':>6s} {'med':>8s} {'net':>8s} {'win%':>5s} {'hold':>5s}")
    out = {}
    for p in SWEEP:
        for side, nm in ((1, "long"), (-1, "short")):
            line = f"  {p:>6.0f} {nm:<6s}   "
            for sc in SOURCES:
                sub = [r for r in rows[(sc, p)] if r["dir"] == side]
                st = D7.summarise(sub, f"{sc}/g{p}/{nm}")
                out[f"{sc}|{p}|{nm}"] = st
                if not st["n"]:
                    line += f"{0:>7d}" + " " * 48
                    continue
                if sc == "GROW":
                    line += (f"{st['n']:>7d} {st['gross_bp']:>8.1f} {st['se_bp']:>6.1f} "
                             f"{st['gross_med_bp']:>8.1f} {st['trim_bp']:>8.1f} "
                             f"{st['net_bp']:>8.1f} {100 * st['win']:>5.0f} {st['hold_med']:>5.0f}   |   ")
                else:
                    line += (f"{st['n']:>7d} {st['gross_bp']:>8.1f} {st['se_bp']:>6.1f} "
                             f"{st['gross_med_bp']:>8.1f} {st['net_bp']:>8.1f} "
                             f"{100 * st['win']:>5.0f} {st['hold_med']:>5.0f}")
            print(line)

    # ---- the per-trade null, headline gmin, both sources
    tn = {}
    n_sims = 20 if a.proof else N_SIMS_TRADE
    t3 = time.time()
    for sc in SOURCES:
        nl = null_in[sc]
        sim = trade_null(nl["states"], nl["cls"], nl["lcls"], nl["cum_dvs"], nl["cum_jumps"],
                         nl["eligs"], n_sims, NULL_SEED)
        for j, nm in enumerate(("long", "short")):
            col = sim[:, j]
            col = col[np.isfinite(col)]
            sc_ = out[f"{sc}|{HEAD}|{nm}"]
            score = sc_["gross_bp"] / 1e4 if sc_["n"] else np.nan
            p95 = float(np.percentile(col, 95)) if col.size else np.nan
            bs = np.array([np.percentile(np.random.default_rng(k).choice(col, col.size), 95)
                           for k in range(200)]) if col.size else np.array([np.nan])
            pct = float((col < score).mean()) if col.size and np.isfinite(score) else np.nan
            se95 = float(bs.std(ddof=1)) if col.size > 1 else np.nan
            margin = (score - p95) / se95 if np.isfinite(se95) and se95 > 0 else np.nan
            verdict = ("ABOVE" if margin > 2 else "UNRESOLVED" if margin > -2 else "BELOW") \
                if np.isfinite(margin) else "n/a"
            if np.isfinite(score) and score <= 0:
                verdict += " (score <= 0: control comparison empty)"
            tn[f"{sc}|{nm}"] = dict(score_bp=1e4 * score, null_p50_bp=1e4 * float(np.percentile(col, 50)) if col.size else np.nan,
                                    null_p95_bp=1e4 * p95, null_p95_se_bp=1e4 * se95, percentile=pct,
                                    n_sims=int(col.size), verdict=verdict)
            r = tn[f"{sc}|{nm}"]
            print(f"  [NULL/trade] {sc:<7s} {nm:<5s} score {r['score_bp']:>7.1f} bp | rotation p50 "
                  f"{r['null_p50_bp']:>7.1f} p95 {r['null_p95_bp']:>7.1f} (SE {r['null_p95_se_bp']:.1f}) | "
                  f"score at pct {100 * pct:>5.1f} | {verdict}")
    print(f"  per-trade nulls: {n_sims} draws x 2 sources in {time.time() - t3:.0f}s")

    # ---- the books, headline gmin, with D476's rotation null
    hb = {}
    emask = np.ascontiguousarray(elig_grid.T.astype(float))
    nb = 30 if a.proof else N_SIMS_BOOK
    for sc in SOURCES:
        for side, nm in ((1, "long"), (-1, "short"), (0, "both")):
            p = book[sc].astype(np.float64)
            if side > 0:
                p[p < 0] = 0.0
            elif side < 0:
                p[p > 0] = 0.0
            p *= emask
            if not p.any():
                continue
            ctx = FN.NullContext(panel, mask=emask)
            scr = RP.score(panel, p, 0, ppy=PPY, rf_annual=RF, borrow_annual=BORROW)
            ctx.assert_matches_scorer(p, lambda q: RP.score(panel, q, 0, ppy=PPY, rf_annual=RF,
                                                            borrow_annual=BORROW),
                                      rf_annual=RF, borrow_annual=BORROW, ppy=PPY)
            sh, mn = FN.rotation_null(ctx, p, 0, n_sims=nb, seed=NULL_SEED, ppy=PPY,
                                      rf_annual=RF, borrow_annual=BORROW)
            p95 = float(np.percentile(mn, 95))
            bs = np.array([np.percentile(np.random.default_rng(k).choice(mn, mn.size), 95)
                           for k in range(200)])
            hb[f"{sc}|{nm}"] = dict(total_return=scr["total_return"], sharpe=scr["excess_sharpe"],
                                    exposure=scr["exposure_gross"], maxdd=scr["max_drawdown"],
                                    null_p50=float(np.percentile(mn, 50)), null_p95=p95,
                                    null_p95_se=float(bs.std(ddof=1)),
                                    null_sharpe_p95=float(np.percentile(sh, 95)))
            h = hb[f"{sc}|{nm}"]
            print(f"  [BOOK] {sc:<7s} {nm:<5s} total {100 * h['total_return']:>7.1f}%  sharpe "
                  f"{h['sharpe']:>5.2f}  expo {h['exposure']:.3f}  maxDD {100 * h['maxdd']:>6.1f}%  | "
                  f"null p50 {100 * h['null_p50']:>7.1f}%  p95 {100 * p95:>7.1f}% (SE "
                  f"{100 * h['null_p95_se']:.1f})  sharpe p95 {h['null_sharpe_p95']:.2f}")
    print(f"  [M] assert_matches_scorer passed on every scored book  OK")

    # ---- what the winners depend on (GROW, headline), and the top trade
    conc = {}
    for side, nm in ((1, "long"), (-1, "short")):
        sub = [r for r in rows[hkey] if r["dir"] == side]
        if not sub:
            continue
        byname = {}
        for r in sub:
            byname[r["sym"]] = byname.get(r["sym"], 0.0) + r["gross"]
        vals = np.array(sorted(byname.values(), reverse=True), float)
        tot_p = vals.sum()
        half = int(np.searchsorted(np.cumsum(vals), 0.5 * tot_p) + 1) if tot_p > 0 else -1
        years = {}
        for r in sub:
            years[r["date"][:4]] = years.get(r["date"][:4], 0.0) + r["gross"]
        conc[nm] = dict(names=len(byname), names_to_half=half,
                        top1=float(vals[:1].sum() / tot_p) if tot_p > 0 else np.nan,
                        top5=float(vals[:5].sum() / tot_p) if tot_p > 0 else np.nan,
                        top10=float(vals[:10].sum() / tot_p) if tot_p > 0 else np.nan,
                        profitable_years=sum(1 for v in years.values() if v > 0), years=len(years))
        cc = conc[nm]
        print(f"  [CONC] {LBL} {nm:<5s} {cc['names']} names, {cc['names_to_half']} to half the P&L, "
              f"top1/5/10 {100 * cc['top1']:.0f}/{100 * cc['top5']:.0f}/{100 * cc['top10']:.0f}%, "
              f"{cc['profitable_years']}/{cc['years']} years profitable")
    top = max(rows[hkey], key=lambda r: r["gross"]) if rows[hkey] else None
    if top:
        print(f"  TOP TRADE ({LBL}, {SWNAME} {HEAD:.0f}): {top['sym']} {top['date']} "
              f"{top['e']}->{top['x']} {'long' if top['dir'] > 0 else 'short'} "
              f"{1e4 * top['gross']:+.0f} bp")
    for side, nm in ((1, "long"), (-1, "short")):
        k = sum(1 for r in rows[hkey] if r["dir"] == side)
        print(f"  [N] {LBL} {nm} trades at the headline gmin: {k}"
              + ("" if k >= MIN_TRADES or a.proof else f"  << {MIN_TRADES}, VACUOUS"))
    print(f"  split-guard rejections: {n_split}")
    if not a.proof and not a.names:              # a partial panel is never the record's file
        OUT.write_text(json.dumps(dict(
            what=f"{a.tag}: trading the grow-right lines in-sample -- in while a trend, out when not",
            grow_line=LINE, rule=a.rule, sweep=list(SWEEP), sweep_name=SWNAME, headline=HEAD,
            dip=dict(x_pct=a.dip_x, n=a.dip_n, drawn_only=a.dip_drawn) if a.rule == "dip" else None,
            gmin_pct=list(GMIN_PCT), headline_gmin=HEAD_GMIN, n_names=len(syms),
            grow_runs=int(len(rl)), grow_run_len_median=float(np.median(rl)),
            grow_window_median=float(np.median(wl)),
            coverage={sc: 100 * cover[sc][0] / max(1, cover[sc][1]) for sc in SOURCES},
            per_trade=out, trade_null=tn, book=hb, concentration=conc, top_trade=top,
            split_rejected=n_split, grow_walk_wall_s=wall, grow_walk_cpu_s=cpu,
            total_s=time.time() - t0), indent=1))
        print(f"  [P] {OUT.relative_to(REPO)} written ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
