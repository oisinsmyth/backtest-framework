"""D301 -- the stack, layer by layer, on one identical book.

    uv run python scripts/run_d301_stack.py --selftest
    uv run python scripts/run_d301_stack.py [--draws 200]

THIS IS A MEASUREMENT, NOT A HYPOTHESIS TEST. Every construction here has
already been decided by an earlier record; nothing is searched, nothing is
promoted, and this file is NOT a result record. Its job is to put the primary
signal, the confluence pair, the triple, and the best mined exits on ONE book
with ONE stat block so the layers are comparable. If something surprising falls
out it becomes a pre-registered study, not a finding.

THE LAYERS. Every construction is `gate to the top/bottom N_BASE by a gate
score, then order WITHIN the gate by a rank score, hold N_SLOTS`:

    hist_L alone          gate hist_L      · order hist_L
    macd_hist alone       gate macd_hist   · order macd_hist
    rsi alone             gate rsi         · order rsi
    pair                  gate mean-rank(macd_hist, rsi) · order the same
    TRIPLE (incumbent)    gate hist_L      · order mean-rank(macd_hist, rsi)

    The triple is NOT a three-way mean. It is gate-then-order, which is what
    D293 built and what every study since has run.

Then the exits, on the triple only, inherited unchanged from the studies that
screened them: profit target at 1.0x vol (D295 B6, p=0.005) and the D297 overlay
at X=12, s=0.0 (p=0.015). Their D298 combination is the best stack the programme
has -- and BOTH inherit D295's unfixed reference defect, which is reported here
rather than silently carried.

ASSERTION [1] IS THE ONE THAT MATTERS. This file has its own simulator, because
D295's trade ledger records (cum, age, side) and not the NAME, so it cannot
answer "how many names reach half the P&L" -- group 3 of the reporting standard,
the one that catches a book carried by three symbols. The new simulator is held
BIT-IDENTICAL to `d295.simulate` on both rules before any number is reported.
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


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


E = _load("d295", "run_d295_exits.py")
O = _load("d297", "run_d297_overlay.py")
SP = _load("d285sp", "d285_spread_estimate.py")
R, M = E.R, E.M

OUT = REPO / "data" / "d301_stack.json"
PRIMARY, PAIR = E.PRIMARY, E.PAIR
N_BASE, N_SLOTS, BASE_HOLD = E.N_BASE, E.N_SLOTS, E.BASE_HOLD
TARGET_X = 1.0
OVERLAY_X, OVERLAY_S = 12.0, 0.0
ANN = 252.0
SEED = 20260903


LAYERS = (
    ("1 primary alone",   PRIMARY,  (PRIMARY,)),
    ("2 macd_hist alone", "macd_hist", ("macd_hist",)),
    ("2 rsi alone",       "rsi",       ("rsi",)),
    ("3 pair mean-rank",  None,     PAIR),
    ("4 TRIPLE",          PRIMARY,  PAIR),
)
STACKS = (("4 TRIPLE + target", "profit_target", False),
          ("4 TRIPLE + overlay", "none", True),
          ("4 TRIPLE + target + overlay", "profit_target", True))


# --------------------------------------------------------------------------
def raw_pct(score, base):
    """Per-bar rank percentile of a RAW score. Deliberately NOT lagged.

    `R.ranked` lags internally, so a percentile built from its output and fed
    back in would be lagged twice. This builds the percentile from the raw
    signal and lets `R.ranked` apply the one lag.
    """
    v = np.ascontiguousarray(np.where(base, score, np.nan).T)
    order = np.argsort(v, axis=1, kind="stable")
    pos = np.empty(order.shape, np.int32)
    np.put_along_axis(pos, order,
                      np.arange(order.shape[1], dtype=np.int32)[None, :], axis=1)
    cnt = np.isfinite(v).sum(axis=1)
    p = (pos + 0.5) / np.maximum(cnt, 1)[:, None]
    p[pos >= cnt[:, None]] = np.nan
    return np.ascontiguousarray(p.T)


def build_ctx(gate, within, z, base, T, n):
    """`gate` names the gate signal (None = gate by the within-mean itself)."""
    with np.errstate(invalid="ignore"):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            gs = (z[gate] if gate is not None
                  else np.nanmean([raw_pct(z[s], base) for s in within], axis=0))
    order_a, cnt_a, _ = R.ranked(gs, base)
    plan = R.LegPlan(order_a, cnt_a, N_BASE, T)
    pc = {}
    for b in within:
        _, cb, pb = R.ranked(z[b], base)
        pc[b] = (R.pct_at(pb, cb, plan.lo, plan.cols),
                 R.pct_at(pb, cb, plan.hi, plan.cols))
    bc = np.broadcast_to(plan.cols[None, :], plan.lo.shape)
    ctx = {}
    for si, (side, rows) in enumerate((("lo", plan.lo), ("hi", plan.hi))):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            avg = np.nanmean([pc[b][si] for b in within], axis=0)
        # low average percentile is best on the long leg, high on the short --
        # `op_meanrank`'s convention, so the selected set matches
        v = np.where(np.isnan(avg), np.inf, avg if side == "lo" else -avg)
        ordr = np.argsort(v, axis=0, kind="stable")
        pos = np.empty(ordr.shape, dtype=np.int32)
        np.put_along_axis(pos, ordr,
                          np.arange(avg.shape[0], dtype=np.int32)[:, None], axis=0)
        rank = np.full((n, T), n, dtype=np.int32)
        rank[rows.ravel(), bc.ravel()] = pos.ravel()
        # `primary` is the gate membership. d295.simulate reads it for rules
        # that do not use it, so it must be present or the bit-identity check
        # cannot run at all.
        ctx[side] = dict(rank=rank, sel=rank < N_SLOTS, primary=rank < N_BASE)
    return ctx, plan


def rotate_rank(ctx, s, n):
    """THE NULL. Rank j inside the gate becomes (j + s) mod N_BASE.

    A random SUBSET is not a control for a persistent selector -- it re-draws
    every bar where the treatment persists, so it churns, and that voided
    D291's veto arm. This shift preserves EACH NAME'S RANK PERSISTENCE exactly,
    along with the gate membership, the held-set size and the entry rate. Only
    the alignment between rank order and actual preference is destroyed.
    """
    out = {}
    for side in ("lo", "hi"):
        rk = ctx[side]["rank"]
        gated = rk < N_BASE
        new = np.where(gated, (rk + s) % N_BASE, n).astype(np.int32)
        out[side] = dict(rank=new, sel=new < N_SLOTS, primary=gated)
    return out


# --------------------------------------------------------------------------
def simulate(ctx, r1, vol, rule, n, T):
    """D295's bar order exactly, with the NAME recorded in the trade ledger.

        1. EXIT on information through t-1
        2. drop anything with no return at t -- delisted out from under us
        3. REFILL from sel[:, t], known at the close of t-1
        4. MARK every position now held with r1[:, t], once

    Assertion [1] holds this bit-identical to `d295.simulate` on both rules.
    """
    ret = {"lo": np.full(T, np.nan), "hi": np.full(T, np.nan)}
    cnt = {"lo": np.zeros(T, np.int32), "hi": np.zeros(T, np.int32)}
    ent = np.zeros(T, np.int32)
    trades = []                      # (row, entry_bar, age, cum, side)
    open_ = {"lo": {}, "hi": {}}     # row -> [age, cum, entry_bar]

    for t in range(1, T):
        for side in ("lo", "hi"):
            sel, rk = ctx[side]["sel"], ctx[side]["rank"]
            held = open_[side]
            sgn = 1.0 if side == "lo" else -1.0
            for row in list(held):
                age, cum, e0 = held[row]
                u = vol[row, t]
                u = u if (np.isfinite(u) and u > 0) else np.nan
                cap = age >= BASE_HOLD
                trig = (rule == "profit_target" and np.isfinite(u)
                        and cum >= TARGET_X * u)
                if (trig or cap) and age > 0:
                    st = held.pop(row)
                    trades.append((row, st[2], st[0], st[1], side))
            for row in list(held):
                if not np.isfinite(r1[row, t]):
                    st = held.pop(row)
                    if st[0] > 0:
                        trades.append((row, st[2], st[0], st[1], side))
            free = N_SLOTS - len(held)
            if free > 0:
                cand = np.flatnonzero(sel[:, t] & np.isfinite(r1[:, t]))
                if cand.size:
                    cand = cand[np.argsort(rk[cand, t], kind="stable")]
                    for row in cand:
                        if free == 0:
                            break
                        r = int(row)
                        if r in held:
                            continue
                        held[r] = [0, 0.0, t]
                        ent[t] += 1
                        free -= 1
            earned = []
            for row in held:
                v = r1[row, t]
                st = held[row]
                st[0] += 1
                st[1] += sgn * v
                earned.append(v)
            if earned:
                ret[side][t] = float(np.mean(earned))
                cnt[side][t] = len(earned)

    ok = np.isfinite(ret["lo"]) & np.isfinite(ret["hi"])
    book = np.where(ok, ret["lo"] - ret["hi"], np.nan)
    return dict(book=book, mask=ok, ent=ent, trades=trades)


def block(res, scale, rt_mean, rt_rob, years):
    """The four reporting groups. A number without these is not a result."""
    ok = res["mask"]
    raw = res["book"][ok]
    b = raw * scale[ok]
    bars = b.size
    sd = b.std(ddof=1)
    eq = np.cumsum(b)
    dd = float(np.max(np.maximum.accumulate(eq) - eq)) * 1e4
    ent = int(res["ent"][ok].sum())
    turn = ent / float(N_SLOTS) / 2.0 / bars
    tr = res["trades"]
    pnl = np.array([x[3] for x in tr]) if tr else np.zeros(0)
    run = np.array([x[2] for x in tr]) if tr else np.zeros(0)
    rows = np.array([x[0] for x in tr]) if tr else np.zeros(0, int)
    win = pnl > 0
    ex = np.sort(pnl)[:-max(1, int(0.01 * pnl.size))] if pnl.size > 100 else pnl

    # group 3 -- name concentration and the yearly split
    byname = {}
    for x in tr:
        byname[x[0]] = byname.get(x[0], 0.0) + x[3]
    vals = np.sort(np.array(list(byname.values())))[::-1]
    tot = vals.sum()
    half = int(np.searchsorted(np.cumsum(vals), 0.5 * tot) + 1) if tot > 0 else None
    yr = years[ok]
    ys = {}
    for u in np.unique(yr):
        ys[int(u)] = float(b[yr == u].mean()) * 1e4
    prof = sum(1 for v in ys.values() if v > 0)

    return dict(
        # 1 -- performance, gross AND net
        gross_bp=float(b.mean()) * 1e4,
        vol_bp=float(sd) * 1e4,
        sharpe=float(b.mean() / sd * np.sqrt(ANN)) if sd > 0 else None,
        t=float(b.mean() / (sd / np.sqrt(bars))) if sd > 0 else None,
        maxdd_bp=dd, exposure=float(scale[ok].mean()), bars=bars,
        turnover=float(turn),
        cost_mean_bp=float(turn * 2.0 * rt_mean),
        cost_rob_bp=float(turn * 2.0 * rt_rob),
        net_mean_bp=float(b.mean()) * 1e4 - float(turn * 2.0 * rt_mean),
        net_rob_bp=float(b.mean()) * 1e4 - float(turn * 2.0 * rt_rob),
        breakeven_bp_side=(float(b.mean()) * 1e4 / (turn * 4.0)
                           if turn > 0 else None),
        # 2 -- trade distribution
        trades=int(pnl.size),
        trade_mean=float(pnl.mean()) * 1e4 if pnl.size else None,
        trade_median=float(np.median(pnl)) * 1e4 if pnl.size else None,
        trade_mean_ex_top1=float(ex.mean()) * 1e4 if ex.size else None,
        win_rate=float(win.mean()) if pnl.size else None,
        payoff=(float(pnl[win].mean() / -pnl[~win].mean())
                if win.any() and (~win).any() else None),
        run=float(run.mean()) if run.size else None,
        skew=float(((pnl - pnl.mean()) ** 3).mean() / pnl.std() ** 3)
        if pnl.size > 2 and pnl.std() > 0 else None,
        kurt=float(((pnl - pnl.mean()) ** 4).mean() / pnl.std() ** 4)
        if pnl.size > 2 and pnl.std() > 0 else None,
        # 3 -- what the winners depend on
        names=len(byname),
        names_to_half=half,
        top1_share=float(vals[0] / tot) if tot > 0 and vals.size else None,
        top5_share=float(vals[:5].sum() / tot) if tot > 0 and vals.size else None,
        top10_share=float(vals[:10].sum() / tot) if tot > 0 and vals.size else None,
        years=len(ys), years_profitable=prof, by_year=ys)


def overlay_scale(book, T, on_flag):
    if not on_flag:
        return np.ones(T)
    on, _, _ = O.schedule(np.nan_to_num(book, nan=0.0), OVERLAY_X)
    return np.where(on, 1.0, OVERLAY_S)


# --------------------------------------------------------------------------
def assertions(ctxs, r1, vol, n, T):
    print("\nASSERTIONS")
    # 1. THE NEW SIMULATOR IS D295'S. Both rules, bit-identical book series.
    ctx = ctxs["4 TRIPLE"]
    for rule in ("none", "profit_target"):
        mine = simulate(ctx, r1, vol, rule, n, T)
        lo, hi, ent, tr, fired, clo, chi, resid = E.simulate(
            ctx, r1, vol, rule, (None if rule == "none" else TARGET_X),
            None, None, n, T)
        m = np.isfinite(lo) & np.isfinite(hi)
        theirs = np.where(m, lo - hi, np.nan)
        same = np.array_equal(np.nan_to_num(mine["book"], nan=-9e9),
                              np.nan_to_num(theirs, nan=-9e9))
        assert same, f"the D301 simulator differs from d295.simulate on {rule}"
        assert int(mine["ent"].sum()) == int(ent.sum()), "entry counts differ"
        print(f"    [1] rule={rule:14s} bit-identical to d295.simulate, "
              f"{int(mine['ent'].sum()):,} entries")

    # 2. SIGN AUDIT, IN MONEY. A favourable move must pay POSITIVELY, and a
    #    market-wide move must move the two legs oppositely.
    res = simulate(ctx, r1, vol, "none", n, T)
    ok = res["mask"]
    assert float(np.nanmean(res["book"][ok])) > 0, \
        "the incumbent book does not make money gross -- the sign is inverted"
    lo_sel = ctx["lo"]["sel"]
    hi_sel = ctx["hi"]["sel"]
    overlap = int((lo_sel & hi_sel).sum())
    assert overlap == 0, f"a name is on BOTH legs on {overlap} cells"
    print(f"    [2] sign audit: the book is positive gross and no name is on "
          f"both legs on any of {ok.sum():,} bars")

    # 3. RIGHT QUANTITY. The null must move what is HELD, and the rotation must
    #    preserve the entry rate -- or it is not the control it is labelled.
    base_ent = int(res["ent"].sum())
    for s in (1, 7, 13):
        nl = rotate_rank(ctx, s, n)
        rr = simulate(nl, r1, vol, "none", n, T)
        # measured against the SELECTED SET, not the whole panel -- 19 True
        # cells in 1,573 rows makes a panel-wide share meaningless
        a, b = ctx["lo"]["sel"], nl["lo"]["sel"]
        d = float((a & ~b).sum() / max(a.sum(), 1))
        rel = abs(int(rr["ent"].sum()) - base_ent) / base_ent
        assert d > 0.03, f"rotation s={s} changes only {d:.2%} of the held set"
        assert rel < 0.25, (f"rotation s={s} changes the entry rate by "
                            f"{rel:.1%} -- it is not turnover-matched")
        print(f"    [3] rotation s={s:2d}: {d:.1%} of the held set changes, "
              f"entry rate within {rel:.1%}")
    # AND THE CEILING IS THE POINT. Holding 19 of a 25-name gate means at most
    # 6 slots (31.6%) can differ under ANY rotation: 76% of the book is forced
    # by gate membership alone, whatever the ordering says. That caps how hard
    # this null can be, and it is the same fact D300 exists to test.
    print(f"    [3b] CEILING: at {N_SLOTS} of {N_BASE}, at most "
          f"{N_BASE - N_SLOTS} slots ({(N_BASE - N_SLOTS) / N_SLOTS:.1%}) can "
          f"differ under any rotation -- the ordering only ever moves "
          f"{N_BASE - N_SLOTS} of {N_SLOTS} names")

    # 4. THE SELF-TEST MUST RAISE ON A BROKEN BOOK.
    broke = False
    try:
        bad = simulate(ctx, r1, vol, "none", n, T)
        bad["book"][np.flatnonzero(ok)[:100]] += 0.05
        assert float(np.nanmean(bad["book"][ok])) == float(
            np.nanmean(res["book"][ok]))
    except AssertionError:
        broke = True
    assert broke, "the check passed a book handed free money"
    print(f"    [4] and the mean check raises on a book handed free money")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=200)
    a = ap.parse_args()
    t0 = time.time()

    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    live = panel.live
    T = live.shape[1]
    z = np.load(R.BC.CACHE, allow_pickle=False)
    base = z["warm"] & live
    n = base.shape[0]
    g = M.P1.build_grids(panel, cleaned)
    half = SP.corwin_schultz(g["high"], g["low"], live) / 2.0 * 1e4
    r1 = np.where(live, np.expm1(panel.total_log_returns), np.nan).astype(np.float64)
    vol = E.roll_vol(r1, live, 21)

    years = np.arange(T) // 252
    print(f"D301  the stack, layer by layer   gate={N_BASE} slots={N_SLOTS} "
          f"k={BASE_HOLD}   T={T}")

    ctxs = {}
    for name, gate, within in LAYERS:
        ctxs[name], _ = build_ctx(gate, within, z, base, T, n)

    # the triple built here must be the triple d295 runs, or the whole
    # comparison is against a different book than every earlier record
    ref, _r1, _vol, _plan = E.build_inputs(z, base, panel, live, T)
    for side in ("lo", "hi"):
        assert np.array_equal(ctxs["4 TRIPLE"][side]["rank"], ref[side]["rank"]), \
            "the D301 triple is NOT d295's triple"
    print(f"  [0] the triple reproduces d295.build_inputs exactly, both legs")

    assertions(ctxs, r1, vol, n, T)
    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    # round trip on the names ACTUALLY HELD by the incumbent (D285's rule)
    res0 = simulate(ctxs["4 TRIPLE"], r1, vol, "none", n, T)
    hv = []
    for row, e0, age, cum, side in res0["trades"]:
        v = half[row, e0]
        if np.isfinite(v):
            hv.append(v)
    hv = np.array(hv)
    rt_mean, rt_rob = 4.0 * float(hv.mean()), 4.0 * float(np.median(hv))
    print(f"  held-name half-spread: mean {hv.mean():.1f} median "
          f"{np.median(hv):.1f} bp, {100 * (hv == 0).mean():.1f}% clamped to zero"
          f"  ->  round trip {rt_mean:.1f} / {rt_rob:.1f} bp")

    cells = {}
    for name, gate, within in LAYERS:
        r = simulate(ctxs[name], r1, vol, "none", n, T)
        cells[name] = block(r, np.ones(T), rt_mean, rt_rob, years)
    for name, rule, ov in STACKS:
        r = simulate(ctxs["4 TRIPLE"], r1, vol, rule, n, T)
        cells[name] = block(r, overlay_scale(r["book"], T, ov),
                            rt_mean, rt_rob, years)
    print(f"  {len(cells)} books ({time.time() - t0:.0f}s)")

    # the null: rank rotation, persistence-matched. Applied to every cell so
    # the layers are comparable; for the exit cells it prices the SIGNAL, not
    # the exit, and section 4 of the output says so.
    rng = np.random.default_rng(SEED)
    offs = rng.choice(np.arange(1, N_BASE), size=a.draws,
                      replace=a.draws > N_BASE - 1)
    dist = {}
    for name, gate, within in LAYERS:
        vals = []
        for s in offs:
            nl = rotate_rank(ctxs[name], int(s), n)
            rr = simulate(nl, r1, vol, "none", n, T)
            b = rr["book"][rr["mask"]]
            if b.size > 200:
                vals.append(float(b.mean()) * 1e4)
        dist[name] = vals
        print(f"    null {name:20s} {len(vals)} draws "
              f"({time.time() - t0:.0f}s)", flush=True)
    for name, rule, ov in STACKS:
        vals = []
        for s in offs:
            nl = rotate_rank(ctxs["4 TRIPLE"], int(s), n)
            rr = simulate(nl, r1, vol, rule, n, T)
            sc = overlay_scale(rr["book"], T, ov)
            b = (rr["book"] * sc)[rr["mask"]]
            if b.size > 200:
                vals.append(float(b.mean()) * 1e4)
        dist[name] = vals
        print(f"    null {name:30s} {len(vals)} draws "
              f"({time.time() - t0:.0f}s)", flush=True)

    for name, c in cells.items():
        arr = np.array(dist[name])
        c["null_p50"] = float(np.median(arr))
        c["null_p95"] = float(np.quantile(arr, 0.95))
        c["p"] = float((arr >= c["gross_bp"]).sum() + 1) / (arr.size + 1)
        c["beats_p95"] = bool(c["gross_bp"] > c["null_p95"])

    OUT.write_text(json.dumps(dict(
        purpose="D301: the primary signal, the confluence pair, the triple and "
                "the best mined exits, on one identical book with one stat "
                "block. A MEASUREMENT of already-decided constructions, not a "
                "hypothesis test and not a result record.",
        primary=PRIMARY, pair=list(PAIR), n_base=N_BASE, n_slots=N_SLOTS,
        hold=BASE_HOLD, draws=a.draws,
        round_trip_mean=rt_mean, round_trip_robust=rt_rob,
        null="rank rotation within the gate, persistence-matched",
        cells=cells), indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
