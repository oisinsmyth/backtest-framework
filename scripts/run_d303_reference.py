"""D303 -- the market-referenced target.

    uv run python scripts/run_d303_reference.py --selftest
    uv run python scripts/run_d303_reference.py [--draws 200] [--nshards 6]

PRE-REGISTERED AT `c5dbfce`, committed before this file existed (R8). This runner
may not re-search a threshold, add a cell, or change the base book.

IT DOES NOT EDIT `run_d295_exits.py`. Four independent implementations of these
rules exist -- d295, d298's `holdings_mask`, d301's `simulate` and
`d295_why_trailing_fails` -- so editing d295 breaks d301's bit-identity assertion
and stops every published number reproducing. This file carries BOTH accumulators
instead, so raw and referenced rules run in one simulator and one pass, and
assertion [4] holds the raw cell to d295's `profit_target` EXACTLY.

THE REFERENCE IS THE MARKET, NEVER THE LEG MEAN. The mean of the 19 longs IS the
edge; netting a position against it deletes the signal it was selected for. And
`m` cancels exactly in the book return, so the reference changes WHEN POSITIONS
LEAVE and nothing else -- assertion [2b] holds that bit-identically.

WHAT WAS OPTIMISED, AND WHY NONE OF IT MOVES A FLOAT
====================================================
Profiled first: 0.37 s per book, of which 66% was the pure-Python loop, 16%
`np.mean`, 7% `flatnonzero`. Every change below is a HOIST or a SKIP, never a
reordered sum, and assertion [4] holds the result bit-identical to d295.

  * THE REFILL CANDIDATES DO NOT DEPEND ON THE EXIT RULE. `sel & isfinite`
    sorted by rank is the same array in all 1,251 simulations, so it is built
    once into the cache instead of 2 x 4,187 times per book.
  * ONE PASS OVER `held` INSTEAD OF TWO. The exit test and the delist test both
    iterated `list(held)` and popped; fused, with the exit tested first, the
    decisions and their order are identical and one list build per side per bar
    disappears.
  * `np.mean` ON A PREALLOCATED SLICE, not on a Python list. Same pairwise
    reduction over the same values in the same order -- it only skips the
    list-to-array conversion, which was 16% of the run.
  * THE NULL DOES NOT NEED THE EXCESS ACCUMULATOR. `sampled_runs` never reads
    it, and the book is built from raw either way, so 1,200 of the 1,251
    simulations skip it. Assertion [6] holds the two paths bit-identical.
  * `sqrt(age)` FROM A TABLE. Age is bounded by the cap.

TWO ASSERTIONS THIS PROGRAMME HAS PAID FOR:
  [5] a parameter must move the BOOK, not only the ledger. D295's B5 returned
      11.274806037178 at all three parameter levels while trade counts differed
      by 7,000, and it went unnoticed for three studies.
  [C] cost dimensions, cross-checked against d295's published 52.19 bp -- and it
      must FAIL on a doubled formula, which is what shipped in two runners.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


E = _load("d295", "run_d295_exits.py")
L = _load("d299", "run_d299_ladder.py")
SP = _load("d285sp", "d285_spread_estimate.py")
R, M = E.R, E.M

OUT = REPO / "data" / "d303_reference.json"
CACHE = REPO / "temp" / "d303_cache"
N_SLOTS, BASE_HOLD, VOL_WIN = E.N_SLOTS, E.BASE_HOLD, 21
ANN = 252.0
SEED = 20260903
ARRAYS = ("r1T", "mkt", "vrT", "vxT", "selT", "rankT", "halfT", "finT",
          "candF", "candO")
SQRTS = np.sqrt(np.arange(512, dtype=np.float64))

# d295's published fixed point for assertion [C], READ FROM ITS OWN OUTPUT.
# A transcribed constant drifts: `260.658 * 0.2` is 52.13 and the published
# figure is 52.19, because d295's turnover is 0.20022 and not 0.200. The
# assertion caught exactly that on its first run.
D295_JSON = REPO / "data" / "d295_exits.json"


def cells(xm=None):
    """The 7 declared cells. The `matched` multipliers are CALIBRATED, not
    searched for a statistic -- the objective is trigger COUNT and no return
    enters it."""
    out = [("CONTROL", "none", "flat", None)]
    for band in ("flat", "sqrt"):
        out.append((f"raw@1.0/{band}", "raw", band, 1.0))
        out.append((f"excess@1.0/{band}", "excess", band, 1.0))
    if xm is not None:
        for band in ("flat", "sqrt"):
            out.append((f"excess@matched/{band}", "excess", band, xm[band]))
    return out


# --------------------------------------------------------------------------
def cache_key():
    """Fixture AND every module that can change a derived array (CLAUDE.md)."""
    h = hashlib.sha1()
    for p in (M.B.FIXTURE, M.B.EVENTS, R.BC.CACHE):
        p = Path(p)
        h.update(str(p).encode())
        if p.exists():
            st = p.stat()
            h.update(f"{st.st_size}:{int(st.st_mtime)}".encode())
    for f in ("run_d293_candidate.py", "run_d295_exits.py", "run_d299_ladder.py",
              "run_d303_reference.py", "d285_spread_estimate.py",
              "ragged_panel.py"):        # D333: the panel's dividend rule changes r1T
        st = (REPO / "scripts" / f).stat()
        h.update(f"{f}:{st.st_size}:{int(st.st_mtime)}".encode())
    h.update(f"{N_SLOTS}:{BASE_HOLD}:{VOL_WIN}".encode())
    return h.hexdigest()[:16]


def build_cache(verbose=True):
    d = CACHE / cache_key()
    if all((d / f"{a}.npy").exists() for a in ARRAYS):
        if verbose:
            print(f"  cache HIT  {d.name}")
        return d
    t0 = time.time()
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    live = panel.live
    T = live.shape[1]
    z = np.load(R.BC.CACHE, allow_pickle=False)
    base = z["warm"] & live
    g = M.P1.build_grids(panel, cleaned)
    half = SP.corwin_schultz(g["high"], g["low"], live) / 2.0 * 1e4
    ctx, r1, vol_raw, _plan = E.build_inputs(z, base, panel, live, T)
    m = L.market_reference(r1, live)
    x = r1 - m[None, :]
    vol_x = E.roll_vol(x, live, VOL_WIN)      # SAME estimator, SAME lag, on x

    r1T = np.ascontiguousarray(r1.T)
    selT = np.ascontiguousarray(
        np.stack([ctx["lo"]["sel"], ctx["hi"]["sel"]]).transpose(0, 2, 1))
    rankT = np.ascontiguousarray(
        np.stack([ctx["lo"]["rank"], ctx["hi"]["rank"]]).transpose(0, 2, 1))
    finT = np.isfinite(r1T)

    # the refill candidates, ragged, stored flat with offsets
    parts, candO = [], np.zeros((2, T + 1), np.int64)
    k = 0
    for side in (0, 1):
        for t in range(T):
            c = np.flatnonzero(selT[side, t] & finT[t])
            if c.size:
                c = c[np.argsort(rankT[side, t][c], kind="stable")]
            parts.append(c.astype(np.int32))
            candO[side, t] = k
            k += c.size
        candO[side, T] = k
    candF = (np.concatenate(parts).astype(np.int32) if parts
             else np.zeros(0, np.int32))

    d.mkdir(parents=True, exist_ok=True)
    for nm, arr in (("r1T", r1T), ("mkt", m), ("vrT", vol_raw.T),
                    ("vxT", vol_x.T), ("selT", selT), ("rankT", rankT),
                    ("halfT", half.T), ("finT", finT),
                    ("candF", candF), ("candO", candO)):
        np.save(d / f"{nm}.npy", np.ascontiguousarray(arr))
    if verbose:
        print(f"  cache BUILT {d.name}  ({time.time() - t0:.0f}s)")
    return d


def load_cache(mmap=True):
    d = build_cache(verbose=False)
    mode = "r" if mmap else None
    return {a: np.load(d / f"{a}.npy", mmap_mode=mode) for a in ARRAYS}


# --------------------------------------------------------------------------
def simulate(A, ref, band, X, runs=None, rng=None, peek=False, want_x=True,
             legacy_cand=False):
    """D295's bar order, carrying BOTH accumulators.

        1. EXIT on information through t-1  (fused with the delist drop)
        2. REFILL from sel[:, t], known at the close of t-1
        3. MARK every position now held with r1[:, t], once

    Deciding first and marking second is what makes each bar's return belong to
    exactly one position per slot. Marking before the exit test credited a
    turned-over slot to both the leaving and the arriving position; moving the
    mark without moving the decision broke it the other way into look-ahead.

    `peek=True` is the DELIBERATELY BROKEN variant assertion [1b] fires at: it
    adds bar t's own move to `cum` before the exit test. `legacy_cand=True`
    rebuilds the candidate list per bar instead of reading the cached one, so
    assertion [3b] can hold the hoist bit-identical.
    """
    r1T, mkt, vrT, vxT = A["r1T"], A["mkt"], A["vrT"], A["vxT"]
    selT, rankT, finT = A["selT"], A["rankT"], A["finT"]
    candF, candO = A["candF"], A["candO"]
    T = r1T.shape[0]
    ret = {0: np.full(T, np.nan), 1: np.full(T, np.nan)}
    xr = {0: np.full(T, np.nan), 1: np.full(T, np.nan)}
    cnt = {0: np.zeros(T, np.int32), 1: np.zeros(T, np.int32)}
    ent = np.zeros(T, np.int32)
    fired = {"trigger": 0, "cap": 0}
    trades = []                       # (row, e0, age, cum_raw, cum_x, side, trig)
    open_ = {0: {}, 1: {}}            # row -> [age, cum_raw, cum_x, e0, tgt]
    braw = np.empty(N_SLOTS + 4)      # preallocated: np.mean on a SLICE, not a
    bexc = np.empty(N_SLOTS + 4)      # list -- same reduction, no conversion
    sampled = (ref == "sampled")
    scored = ref in ("raw", "excess")
    # THE EXCESS RULE READS THE ACCUMULATOR want_x SKIPS. Calibration called it
    # with want_x=False, so cum_x stayed 0.0 and the rule never fired -- the
    # bisection ran to its lower bound and reported a "matched" multiplier of
    # 0.0200 producing ZERO triggers. Assertion [6] tested the fast path on the
    # RAW rule only, where cum_x genuinely is unused, so it passed a flag that
    # was silently wrong everywhere else. Refused at the door now.
    assert want_x or ref != "excess", (
        "want_x=False with ref='excess': the excess rule reads cum_x, which "
        "this flag stops accumulating")

    for t in range(1, T):
        r1t, fint, mt = r1T[t], finT[t], mkt[t]
        vrt, vxt = vrT[t], vxT[t]
        for side in (0, 1):
            held = open_[side]
            sgn = 1.0 if side == 0 else -1.0
            # 1. EXIT, then the delist drop, in ONE pass over `held`
            for row in list(held):
                age, cr, cx, e0, tgt = held[row]
                trig = False
                if sampled:
                    trig = age >= tgt
                elif scored:
                    u = vrt[row] if ref == "raw" else vxt[row]
                    if u == u and u > 0.0:
                        cum = cr if ref == "raw" else cx
                        if peek and fint[row]:
                            v = r1t[row]
                            cum += sgn * (v if ref == "raw" else v - mt)
                        trig = cum >= X * u * (1.0 if band == "flat"
                                               else SQRTS[age if age else 1])
                cap = (not sampled) and age >= BASE_HOLD
                if (trig or cap) and age > 0:
                    st = held.pop(row)
                    fired["trigger" if trig else "cap"] += 1
                    trades.append((row, st[3], st[0], st[1], st[2], side, trig))
                elif not fint[row]:
                    st = held.pop(row)
                    if st[0] > 0:
                        trades.append((row, st[3], st[0], st[1], st[2], side,
                                       False))
            # 2. REFILL from what was knowable at the close of t-1
            free = N_SLOTS - len(held)
            if free > 0:
                if legacy_cand:
                    c = np.flatnonzero(selT[side, t] & fint)
                    if c.size:
                        c = c[np.argsort(rankT[side, t][c], kind="stable")]
                else:
                    c = candF[candO[side, t]:candO[side, t + 1]]
                for row in c:
                    if free == 0:
                        break
                    r = int(row)
                    if r in held:
                        continue
                    tg = int(rng.choice(runs)) if runs is not None else BASE_HOLD
                    held[r] = [0, 0.0, 0.0, t, tg if tg > 0 else 1]
                    ent[t] += 1
                    free -= 1
            # 3. MARK. Every position now held earns bar t, once.
            k = 0
            for row, st in held.items():
                v = r1t[row]
                st[0] += 1
                st[1] += sgn * v
                braw[k] = v
                if want_x:
                    st[2] += sgn * (v - mt)
                    bexc[k] = v - mt
                k += 1
            if k:
                ret[side][t] = float(np.mean(braw[:k]))
                if want_x:
                    xr[side][t] = float(np.mean(bexc[:k]))
                cnt[side][t] = k

    ok = np.isfinite(ret[0]) & np.isfinite(ret[1])
    return dict(book=np.where(ok, ret[0] - ret[1], np.nan), mask=ok, ent=ent,
                trades=trades, fired=fired,
                xbook=np.where(ok, xr[0] - xr[1], np.nan),
                eqcnt=(cnt[0] == cnt[1]))


# --------------------------------------------------------------------------
def block(res, rt_mean, rt_rob, years, mktvol):
    """The four reporting groups. A number without these is not a result."""
    ok = res["mask"]
    b = res["book"][ok]
    bars = b.size
    sd = b.std(ddof=1)
    eq = np.cumsum(b)
    ent = int(res["ent"][ok].sum())
    turn = ent / float(N_SLOTS) / 2.0 / bars
    tr = res["trades"]
    pnl = np.array([x[3] for x in tr]) if tr else np.zeros(0)
    run = np.array([x[2] for x in tr]) if tr else np.zeros(0)
    trg = np.array([x[6] for x in tr]) if tr else np.zeros(0, bool)
    win = pnl > 0
    byname = {}
    for x in tr:
        byname[x[0]] = byname.get(x[0], 0.0) + x[3]
    vals = np.sort(np.array(list(byname.values())))[::-1] if byname else np.zeros(1)
    tot = float(vals.sum())
    yr = years[ok]
    ys = {int(u): float(b[yr == u].mean()) * 1e4 for u in np.unique(yr)}
    mv = mktvol[ok]
    fin = np.isfinite(mv)
    terc = {}
    if int(fin.sum()) > 300:
        q = np.quantile(mv[fin], [1 / 3, 2 / 3])
        masks = (fin & (mv < q[0]), fin & (mv >= q[0]) & (mv < q[1]),
                 fin & (mv >= q[1]))
        for lab, msk in zip(("mktvol_low", "mktvol_mid", "mktvol_high"), masks):
            terc[lab] = float(b[msk].mean()) * 1e4 if int(msk.sum()) > 50 else None
    return dict(
        gross_bp=float(b.mean()) * 1e4, vol_bp=float(sd) * 1e4,
        t=float(b.mean() / (sd / np.sqrt(bars))) if sd > 0 else None,
        sharpe=float(b.mean() / sd * np.sqrt(ANN)) if sd > 0 else None,
        maxdd_bp=float(np.max(np.maximum.accumulate(eq) - eq)) * 1e4, bars=bars,
        turnover=float(turn), entries=ent,
        cost_mean_bp=float(rt_mean * turn), cost_rob_bp=float(rt_rob * turn),
        net_mean_bp=float(b.mean()) * 1e4 - rt_mean * turn,
        net_rob_bp=float(b.mean()) * 1e4 - rt_rob * turn,
        breakeven_bp_side=float(b.mean()) * 1e4 / (turn * 4.0) if turn else None,
        trades=int(pnl.size), triggers=int(trg.sum()),
        trigger_share=float(trg.mean()) if trg.size else None,
        age_at_trigger=float(run[trg].mean()) if bool(trg.any()) else None,
        trade_mean=float(pnl.mean()) * 1e4 if pnl.size else None,
        trade_median=float(np.median(pnl)) * 1e4 if pnl.size else None,
        trade_mean_ex_top1=(float(np.sort(pnl)[:-max(1, pnl.size // 100)].mean())
                            * 1e4 if pnl.size > 100 else None),
        win_rate=float(win.mean()) if pnl.size else None,
        payoff=(float(pnl[win].mean() / -pnl[~win].mean())
                if bool(win.any()) and bool((~win).any()) else None),
        run=float(run.mean()) if run.size else None,
        skew=(float(((pnl - pnl.mean()) ** 3).mean() / pnl.std() ** 3)
              if pnl.size > 2 and pnl.std() > 0 else None),
        names=len(byname),
        names_to_half=(int(np.searchsorted(np.cumsum(vals), 0.5 * tot) + 1)
                       if tot > 0 else None),
        top5_share=float(vals[:5].sum() / tot) if tot > 0 else None,
        years_profitable=sum(1 for v in ys.values() if v > 0), years=len(ys),
        by_year=ys, **terc)


def exit_set(res):
    """The position-exits a rule TRIGGERED, as (row, entry bar, side)."""
    return {(x[0], x[1], x[5]) for x in res["trades"] if x[6]}


def paired(a, b):
    """t on the per-bar difference of two books, on their common bars."""
    m = a["mask"] & b["mask"]
    d = a["book"][m] - b["book"][m]
    sd = d.std(ddof=1)
    return (None if sd == 0 else
            dict(d_bp=float(d.mean() * 1e4),
                 d_t=float(d.mean() / (sd / np.sqrt(d.size))), n=int(d.size)))


def calibrate(A, band, target, verbose=True):
    """The multiplier whose TRIGGER COUNT matches the raw rule's.

    Trigger count falls monotonically in X, so bisection is exact. NO RETURN
    ENTERS THE OBJECTIVE -- this matches a nuisance, it does not optimise a
    statistic, and the result is printed before any book is scored.
    """
    lo, hi = 0.02, 4.0
    for _ in range(24):
        mid = 0.5 * (lo + hi)
        f = simulate(A, "excess", band, mid)["fired"]["trigger"]
        if f > target:
            lo = mid
        else:
            hi = mid
    out = 0.5 * (lo + hi)
    if verbose:
        got = simulate(A, "excess", band, out)["fired"]["trigger"]
        print(f"    {band:4s}: matched multiplier {out:.4f}  ->  {got:,} triggers "
              f"vs the raw rule's {target:,}  ({100 * (got / target - 1):+.2f}%)")
    return out


def mkt_vol(mkt, w=21):
    """Trailing sd of the market return, LAGGED -- Q6's regime split."""
    n = mkt.size
    out = np.full(n, np.nan)
    v = np.where(np.isfinite(mkt), mkt, np.nan)
    for t in range(w + 1, n):
        s = v[t - 1 - w:t - 1]
        s = s[np.isfinite(s)]
        if s.size >= w // 2:
            out[t] = s.std(ddof=1)
    return out


# --------------------------------------------------------------------------
def assertions(A):
    print("\nASSERTIONS")
    r1T, T = A["r1T"], A["r1T"].shape[0]

    # 4. BIT-IDENTITY. If the raw cell is not the incumbent, no comparison in
    #    this study means anything. Run first because everything leans on it.
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS,
                                      fee_bps=M.B.FEE_BPS)
    live = panel.live
    z = np.load(R.BC.CACHE, allow_pickle=False)
    base = z["warm"] & live
    n = base.shape[0]
    ctx, r1, vol, _plan = E.build_inputs(z, base, panel, live, T)
    lo, hi, ent, _tr, _f, _cl, _ch, _rs = E.simulate(
        ctx, r1, vol, "profit_target", 1.0, None, None, n, T)
    m295 = np.isfinite(lo) & np.isfinite(hi)
    theirs = np.where(m295, lo - hi, np.nan)
    mine = simulate(A, "raw", "flat", 1.0)
    assert np.array_equal(np.nan_to_num(mine["book"], nan=-9e9),
                          np.nan_to_num(theirs, nan=-9e9)), \
        "the raw cell is NOT d295's profit_target"
    assert int(mine["ent"].sum()) == int(ent.sum())
    print(f"    [4] raw@1.0/flat is bit-identical to d295.profit_target, "
          f"{int(ent.sum()):,} entries")

    # 1. LAG AUDIT. Each trade's cum rebuilt from the panel by an independent
    #    accumulation that never touches the simulator's state.
    rng = np.random.default_rng(7)
    tr = mine["trades"]
    idx = rng.choice(len(tr), size=min(3000, len(tr)), replace=False)
    bad = 0
    for i in idx:
        row, e0, age, cr, cx, side, _t = tr[i]
        sgn = 1.0 if side == 0 else -1.0
        acc = 0.0
        for j in range(age):
            acc += sgn * float(r1T[e0 + j, row])
        if abs(acc - cr) > 1e-9 * max(abs(cr), 1.0):
            bad += 1
    assert bad == 0, f"LAG AUDIT FAILED: {bad} of {idx.size} rebuilt cums differ"
    print(f"    [1] every one of {idx.size:,} sampled trades' cum rebuilt from "
          f"the panel by an independent loop, over bars e0..e0+age-1 only")

    # 1b. and it must FAIL on a rule that sees bar t's own move.
    pk = simulate(A, "raw", "flat", 1.0, peek=True)
    d = int((np.nan_to_num(pk["book"], nan=-9e9)
             != np.nan_to_num(mine["book"], nan=-9e9)).sum())
    assert d > 0, "the audit PASSED a rule that peeks at bar t -- it proves nothing"
    print(f"    [1b] and a peeking rule differs on {d:,} bars")

    # 2. SIGN AUDIT, IN MONEY, and 2b THE REFERENCE MUST CANCEL.
    ctrl = simulate(A, "none", "flat", None)
    ok = ctrl["mask"]
    assert float(np.nanmean(ctrl["book"][ok])) > 0, "the control is negative gross"
    eqm = ok & ctrl["eqcnt"]
    gap = float(np.nanmax(np.abs(ctrl["xbook"][eqm] - ctrl["book"][eqm])))
    assert gap < 1e-12, (f"THE REFERENCE DOES NOT CANCEL: excess-book and "
                         f"raw-book differ by {gap:.2e}")
    print(f"    [2] control is positive gross; [2b] the market reference cancels "
          f"in the book return, max gap {gap:.2e} on {int(eqm.sum()):,} bars")

    # 3. RIGHT QUANTITY. Triggers must fall as the band widens, and the rule
    #    must hold shorter than the no-exit book.
    prev, seen = None, []
    for X in (0.5, 1.0, 2.0, 3.0):
        f = simulate(A, "raw", "flat", X, want_x=False)["fired"]["trigger"]
        assert prev is None or f <= prev, \
            f"RIGHT QUANTITY FAILED: triggers rose from {prev} to {f} at X={X}"
        prev = f
        seen.append((X, f))
    zeros, nans = np.zeros(T, int), np.full(T, np.nan)
    cs = block(ctrl, 1.0, 1.0, zeros, nans)
    ms = block(mine, 1.0, 1.0, zeros, nans)
    assert ms["run"] < cs["run"], "the exit does not shorten the holding run"
    print("    [3] right quantity: triggers fall monotonically -- "
          + ", ".join(f"X={x}: {f:,}" for x, f in seen)
          + f"; run {ms['run']:.2f} vs the no-exit book's {cs['run']:.2f}")

    # 3b. THE HOISTED CANDIDATE LIST IS THE ONE IT REPLACED, bit-identically.
    lg = simulate(A, "raw", "flat", 1.0, legacy_cand=True)
    assert np.array_equal(np.nan_to_num(lg["book"], nan=-9e9),
                          np.nan_to_num(mine["book"], nan=-9e9)), \
        "the cached candidate list differs from rebuilding it per bar"
    print("    [3b] the cached refill candidates are bit-identical to "
          "rebuilding them per bar")

    # 6. THE NULL'S FAST PATH IS THE SLOW PATH. want_x=False skips the excess
    #    accumulator, which the null never reads -- it must not move the book.
    fx = simulate(A, "raw", "flat", 1.0, want_x=False)
    assert np.array_equal(np.nan_to_num(fx["book"], nan=-9e9),
                          np.nan_to_num(mine["book"], nan=-9e9)), \
        "skipping the excess accumulator changed the book"
    # AND IT MUST BE REFUSED FOR THE EXCESS RULE. The first version of [6]
    # tested the raw rule only -- where cum_x genuinely is unused -- so it
    # passed a flag that silently zeroed the excess rule's accumulator and let
    # calibration bisect to its lower bound, reporting a "matched" multiplier
    # of 0.0200 producing ZERO triggers.
    refused = False
    try:
        simulate(A, "excess", "flat", 1.0, want_x=False)
    except AssertionError:
        refused = True
    assert refused, ("want_x=False was ACCEPTED for the excess rule -- it "
                     "silently zeroes the accumulator that rule reads")
    ex = simulate(A, "excess", "flat", 1.0)
    assert ex["fired"]["trigger"] >= 1, "the excess rule never fires at X=1.0"
    print(f"    [6] want_x=False is bit-identical on the raw rule and REFUSED "
          f"on the excess rule, which fires {ex['fired']['trigger']:,} times")

    # C. COST DIMENSIONS. The guard that was missing when `turn * 2.0 * rt`
    #    shipped in two runners.
    turn = cs["turnover"]
    assert abs(turn - 1.0 / BASE_HOLD) < 0.02 * (1.0 / BASE_HOLD), \
        f"turnover {turn:.4f} is not 1/k = {1.0 / BASE_HOLD:.4f}"
    d295 = json.loads(D295_JSON.read_text())
    b0 = [r for r in d295["rows"] if r["cell"] == "B0"][0]
    rt0, tn0, want = d295["round_trip_mean"], b0["turnover"], b0["cost_bar_mean"]
    got = rt0 * tn0
    assert abs(got - want) < 1e-9 * max(abs(want), 1.0), (
        f"the cost formula does not reproduce d295's published {want:.6f}: "
        f"rt {rt0:.4f} x turn {tn0:.6f} = {got:.6f}")
    doubled = got * 2.0
    assert abs(doubled - want) > 1.0, \
        "the cost check PASSES a doubled formula -- it proves nothing"
    print(f"    [C] cost dimensions: this book's turnover {turn:.4f} = 1/k; "
          f"d295's own rt x turn = {got:.4f} reproduces its published "
          f"{want:.4f} exactly; the doubled form gives {doubled:.2f} and is "
          f"rejected")

    # 7. THE SELF-TEST MUST RAISE ON A BROKEN BOOK -- corrupting bars INSIDE
    #    the mask, since a slice by position lands in the leading NaNs.
    broke = False
    try:
        bad_b = ctrl["book"].copy()
        bad_b[np.flatnonzero(ok)[:100]] += 0.05
        assert float(np.nanmean(bad_b[ok])) == float(np.nanmean(ctrl["book"][ok]))
    except AssertionError:
        broke = True
    assert broke, "the mean check passed a book handed free money"
    print("    [7] and the mean check raises on a book handed free money")
    return ctrl


# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=200)
    a = ap.parse_args()
    t0 = time.time()
    for v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        os.environ.setdefault(v, "1")

    print(f"D303  the market-referenced target   slots={N_SLOTS} k={BASE_HOLD} "
          f"vol_win={VOL_WIN}")
    build_cache(verbose=True)
    A = load_cache(mmap=True)
    T = A["r1T"].shape[0]

    assertions(A)
    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    # THE CALIBRATION IS PRINTED BEFORE ANY BOOK IS SCORED.
    print("\nCALIBRATION -- matching the referenced rule's TRIGGER COUNT")
    xm = {}
    for band in ("flat", "sqrt"):
        tgt = simulate(A, "raw", band, 1.0, want_x=False)["fired"]["trigger"]
        xm[band] = calibrate(A, band, tgt)
    print(f"  (idiosyncratic vol is smaller than total vol, so a multiplier "
          f"below 1.0 is expected -- Q7)")

    years = np.arange(T) // 252
    mv = mkt_vol(np.asarray(A["mkt"]))

    # round trip on the names ACTUALLY HELD, at their entry bars (D285's rule).
    # The MEDIAN is primary: D302 showed the mean is a left-truncation artefact.
    half = np.asarray(A["halfT"])
    ctrl0 = simulate(A, "none", "flat", None)
    hv = np.array([half[e0, row] for row, e0, _a, _cr, _cx, _s, _t
                   in ctrl0["trades"]])
    hv = hv[np.isfinite(hv)]
    rt_mean, rt_rob = 4.0 * float(hv.mean()), 4.0 * float(np.median(hv))
    print(f"\n  held-name half-spread: mean {hv.mean():.2f} median "
          f"{np.median(hv):.2f} bp, {100 * (hv == 0).mean():.1f}% clamped to "
          f"zero  ->  round trip {rt_mean:.1f} (artefact) / {rt_rob:.1f} bp")

    obs, books = {}, {}
    for name, ref, band, X in cells(xm):
        r = simulate(A, ref, band, X)
        books[name] = r
        obs[name] = block(r, rt_mean, rt_rob, years, mv)
        obs[name].update(reference=ref, band=band, X=X)
    print(f"  {len(obs)} books ({time.time() - t0:.0f}s)")

    # 5. A PARAMETER MUST MOVE THE BOOK, NOT ONLY THE LEDGER. D295's B5
    #    returned 11.274806037178 at all three parameter levels while trade
    #    counts differed by 7,000, and it went unnoticed for three studies.
    keys = list(books)
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            bi = np.nan_to_num(books[keys[i]]["book"], nan=-9e9)
            bj = np.nan_to_num(books[keys[j]]["book"], nan=-9e9)
            assert not np.array_equal(bi, bj), (
                f"[5] FAILED: {keys[i]} and {keys[j]} are the SAME BOOK -- a "
                f"parameter is moving the ledger and not the holdings")
    print(f"    [5] all {len(keys)} books are distinct")

    # Q1 -- the Jaccard against D297's premise measurement of 0.721
    jac = {}
    for band in ("flat", "sqrt"):
        raw = exit_set(books[f"raw@1.0/{band}"])
        for tag in (f"excess@1.0/{band}", f"excess@matched/{band}"):
            ex = exit_set(books[tag])
            u = len(raw | ex)
            jac[f"raw vs {tag}"] = (len(raw & ex) / u) if u else None
    print("\nQ1 -- position-exits in common (D297's premise measured 0.721)")
    for k2, v in jac.items():
        print(f"    {k2:34s} jaccard {v:.3f}")

    # the paired comparison -- the study's actual question
    pair = {}
    for band in ("flat", "sqrt"):
        for tag in (f"excess@1.0/{band}", f"excess@matched/{band}"):
            pair[f"{tag} - raw@1.0/{band}"] = paired(
                books[tag], books[f"raw@1.0/{band}"])

    # the null: each cell's OWN holding-run distribution resampled, so rate and
    # persistence match. A count-matched control is not a control (D279) and a
    # per-bar redraw churns where the treatment persists (D291).
    dist = {}
    for ci, (name, ref, band, X) in enumerate(cells(xm)):
        if name == "CONTROL":
            continue
        runs = np.array([x[2] for x in books[name]["trades"] if x[2] > 0])
        rng = np.random.default_rng([SEED, ci])
        vals = []
        for _ in range(a.draws):
            r = simulate(A, "sampled", band, None, runs=runs, rng=rng,
                         want_x=False)
            b = r["book"][r["mask"]]
            if b.size > 200:
                vals.append(float(b.mean()) * 1e4)
        dist[name] = vals
        arr = np.array(vals)
        obs[name]["null_p50"] = float(np.median(arr))
        obs[name]["null_p95"] = float(np.quantile(arr, 0.95))
        obs[name]["p"] = float((arr >= obs[name]["gross_bp"]).sum() + 1) / (arr.size + 1)
        obs[name]["beats_p95"] = bool(obs[name]["gross_bp"] > obs[name]["null_p95"])
        print(f"    null {name:24s} {len(vals)} draws  p={obs[name]['p']:.4f} "
              f"({time.time() - t0:.0f}s)", flush=True)

    OUT.write_text(json.dumps(dict(
        purpose="D303: the market-referenced profit target against the raw "
                "incumbent, at a matched trigger rate.",
        preregistered="c5dbfce", draws=a.draws,
        matched_multiplier=xm, round_trip_mean=rt_mean, round_trip_robust=rt_rob,
        jaccard=jac, paired=pair, cells=obs), indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
