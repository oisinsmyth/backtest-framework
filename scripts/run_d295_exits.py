"""D295 -- stage 2: exits and idle conditions, measured ON THE BOOK.

    uv run python scripts/run_d295_exits.py --selftest
    uv run python scripts/run_d295_exits.py [--draws 200] [--workers 6]

PRE-REGISTERED AT `b7262f5`, AMENDED AT `d33fc71`, both committed before this
file existed (R8). This runner may not re-search the base book.

THE NEW COMPONENT IS A POSITION-LEVEL SIMULATION WITH SLOTS AND RE-ENTRY, and
this programme has never had one. Everything upstream used "fresh entries earn
k-bar returns", which models no capital: a trade that exits early frees nothing
and a trade that runs long costs nothing. R14's first amendment exists because
an exit cannot be judged at trade level -- a stop that improves the average
trade and hands the freed slot to a coin flip is a book-level loss wearing a
trade-level win, and D286's `disp` beat every designed exit precisely because
its freed slot went to a better-ranked name.

    N slots per leg. Each bar t, IN THIS ORDER -- see `simulate`:
      1. exit, on information through t-1
      2. drop anything delisted out from under us
      3. refill freed slots from what was knowable at the close of t-1
      4. MARK: every position now held earns bar t, exactly once, and the
         book return is mean(long holdings) - mean(short holdings)

    Deciding first and marking second is the whole correctness argument, and
    getting it wrong in either direction produced a plausible-looking table
    twice. Assertions [2] and [5] are what now pin it.

THE BASELINE HOLD IS NOT A CAP. The first draft made it one, so every rule could
only ever SHORTEN a trade and "let the winners run" could not be expressed. B4
and B5 run past it; their holding run is an OUTPUT.

AND THE CLAIM IS ABOUT TWO NUMBERS, NOT ONE. "Trim losers, let winners run" says
the winner run should exceed the loser run. That ratio is reported for every
rule including the controls, so a rule that improves P&L WITHOUT doing the thing
is visible as such.

EVERY POSITION IS MARKED ON ITS OWN 1-BAR RETURN, so a rule that changes holding
length changes exposure honestly. Using k-bar returns here would double-count
overlapping holds.
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


C = _load("d293", "run_d293_candidate.py")
SP = _load("d285sp", "d285_spread_estimate.py")
R, M, D, ET = C.R, C.M, C.D, C.ET

OUT = REPO / "data" / "d295_exits.json"
PRIMARY, PAIR, FRAC = C.PRIMARY, C.PAIR, C.FRAC
N_BASE = 25                     # hist_L's gate, as D293 fixed it
N_SLOTS = max(1, round(FRAC * N_BASE))   # 19 -- the composite selects 19 of 25,
BASE_HOLD = 5                            # so the book cannot hold more than 19
SEED = 20260903


# --------------------------------------------------------------------------
# the declared cells
# --------------------------------------------------------------------------
def cell_list():
    """19 cells: 14 exit configurations + 5 idle. Enumerated, not chosen."""
    cells = [("B0", "none", None)]
    cells += [("B1", "reversion", None), ("B2", "displacement", None)]
    cells += [("B3", "adverse_stop", x) for x in (1.0, 1.5, 2.0)]
    cells += [("B4", "trailing", x) for x in (1.0, 1.5, 2.0)]
    cells += [("B5", "asymmetric", x) for x in (1.0, 1.5, 2.0)]
    cells += [("B6", "profit_target", x) for x in (1.0, 1.5, 2.0)]
    cells += [("C1", "disagree", x) for x in (0.50, 0.70, 0.90)]
    cells += [("C2", "idle_dispersion", None), ("C3", "idle_spread", None)]
    return cells


CAPPED = {"none", "reversion", "displacement", "adverse_stop", "profit_target"}
UNCAPPED = {"trailing", "asymmetric"}


# --------------------------------------------------------------------------
# the simulation
# --------------------------------------------------------------------------
def simulate(ctx, r1, vol, rule, param, skip_name, idle_bar, n, T):
    """One book, bar by bar, with slots and re-entry.

    `ctx[side]` carries `sel` (in the composite's selected 19), `rank` (position
    in the composite's own preference, lower better, n = unranked) and `primary`
    (in hist_L's top 25). All three are ALREADY LAGGED: the value at column t is
    derived from scores at t-1, so it is known at the close of t-1 and is what
    you can act on for bar t. Slots refill from `rank` best-first, which is what
    sends a freed slot to a better name instead of a coin flip.

    THE ORDER OF THE BAR IS THE WHOLE CORRECTNESS ARGUMENT.

        1. EXIT on information through t-1  (cum, and the lagged sel/rank/vol)
        2. drop anything with no return at t -- delisted out from under us
        3. REFILL from sel[:, t], which is known at the close of t-1
        4. MARK every position now held with r1[:, t], and mark the book

    Deciding first and marking second is what makes each bar's return belong to
    exactly one position per slot. The first version marked BEFORE the exit test
    and again AFTER the refill, so a bar on which a slot turned over was credited
    to both the position leaving and the one arriving -- one bar of return per
    turnover, created from nothing, worth +-75 to 85 bp on numbers of magnitude 7
    to 77, and it ranked the rules by how often they traded. Moving the mark
    without moving the decision then broke it the other way: the exit test saw
    bar t's return before deciding, which is look-ahead, and the oracle's
    foresight collapsed from +267 to +9.7 bp/bar because the only bar it could
    ever harvest was the double-counted one. Assertion [5] holds this to the
    trade ledger and assertion [2] holds it to the oracle; both are needed
    because each alone passed one of the two broken versions.

    Positions are marked on their own ONE-BAR return, so a rule that changes
    holding length changes exposure honestly; k-bar returns would double-count
    overlapping holds.
    """
    ret = {"lo": np.full(T, np.nan), "hi": np.full(T, np.nan)}
    cnt = {"lo": np.zeros(T, dtype=np.int32), "hi": np.zeros(T, dtype=np.int32)}
    ent = np.zeros(T, dtype=np.int32)
    fired = {"trigger": 0, "cap": 0}
    trades = []
    open_ = {"lo": {}, "hi": {}}          # row -> [age, cum, peak, target]
    runs, rng = (param if rule == "sampled_runs" else (None, None))

    for t in range(1, T):
        for side in ("lo", "hi"):
            sel, rk, prim = ctx[side]["sel"], ctx[side]["rank"], ctx[side]["primary"]
            held = open_[side]
            sgn = 1.0 if side == "lo" else -1.0

            # 1. EXIT, on information through t-1 only
            for row in list(held):
                age, cum, pk, tgt = held[row]
                u = vol[row, t]
                u = u if (np.isfinite(u) and u > 0) else np.nan
                cap = age >= BASE_HOLD
                trig = False
                if rule == "none":
                    pass
                elif rule == "reversion":
                    trig = not sel[row, t]
                elif rule == "displacement":
                    trig = not prim[row, t]
                elif rule == "adverse_stop":
                    trig = np.isfinite(u) and cum <= -param * u
                elif rule == "profit_target":
                    trig = np.isfinite(u) and cum >= param * u
                elif rule == "trailing":
                    cap = False                        # UNCAPPED: winners run
                    trig = np.isfinite(u) and (pk - cum) >= param * u
                elif rule == "trailing_capped":
                    # POST-HOC DIAGNOSTIC, not a pre-registered cell. B4 removed
                    # the cap AND changed the winner exit at once, so it cannot
                    # separate "trailing is wrong for this edge" from "uncapped
                    # is wrong". This is B4 with the cap put back.
                    trig = np.isfinite(u) and (pk - cum) >= param * u
                elif rule == "asymmetric":
                    cap = False                        # UNCAPPED on the winner
                    trig = ((np.isfinite(u) and cum <= -param * u)
                            or not sel[row, t])
                elif rule == "stop_and_target":
                    trig = np.isfinite(u) and (cum <= -param * u or
                                               cum >= param * u)
                elif rule == "rev_stop":
                    trig = (not sel[row, t]) or (np.isfinite(u) and
                                                 cum <= -param * u)
                elif rule == "rev_target":
                    trig = (not sel[row, t]) or (np.isfinite(u) and
                                                 cum >= param * u)
                elif rule == "rev_both":
                    trig = (not sel[row, t]) or (np.isfinite(u) and
                                                 (cum <= -param * u or
                                                  cum >= param * u))
                elif rule == "sampled_runs":
                    cap = False
                    trig = age >= tgt
                if (trig or cap) and age > 0:
                    fired["trigger" if trig else "cap"] += 1
                    st = held.pop(row)
                    trades.append((st[1], st[0], side))

            # 2. delisted out from under us -- no return at t, so it cannot be held
            for row in list(held):
                if not np.isfinite(r1[row, t]):
                    st = held.pop(row)
                    if st[0] > 0:
                        trades.append((st[1], st[0], side))

            # 3. REFILL from what was knowable at the close of t-1
            if not (idle_bar is not None and idle_bar[t]):
                free = N_SLOTS - len(held)
                if free > 0:
                    cand = np.flatnonzero(sel[:, t] & np.isfinite(r1[:, t]))
                    if skip_name is not None:
                        cand = cand[~skip_name[cand, t]]
                    if cand.size:
                        cand = cand[np.argsort(rk[cand, t], kind="stable")]
                        for row in cand:
                            if free == 0:
                                break
                            r = int(row)
                            if r in held:
                                continue
                            tgt = (int(rng.choice(runs)) if runs is not None
                                   else BASE_HOLD)
                            held[r] = [0, 0.0, 0.0, max(1, tgt)]
                            ent[t] += 1
                            free -= 1

            # 4. MARK. Every position now held earns bar t, once.
            earned = []
            for row in held:
                v = r1[row, t]
                st = held[row]
                st[0] += 1
                st[1] += sgn * v
                st[2] = max(st[2], st[1])
                earned.append(v)
            if earned:
                ret[side][t] = float(np.mean(earned))
                cnt[side][t] = len(earned)

    # positions still open at the end never became trades; the reconciliation in
    # assertion [5] needs their accrued P&L or it will not close
    resid = sum(st[1] for side in ("lo", "hi") for st in open_[side].values())
    return (ret["lo"], ret["hi"], ent, trades, fired,
            cnt["lo"], cnt["hi"], float(resid))


def book_stats(ret_lo, ret_hi, ent, trades, fired, clo, chi, resid,
               rt_mean, rt_med):
    """Book-level AND per-trade, side by side, per R14's amended stage-2 gate."""
    m = np.isfinite(ret_lo) & np.isfinite(ret_hi)
    if int(m.sum()) < M.MIN_BARS:
        return None
    d = ret_lo[m] - ret_hi[m]
    sd = d.std(ddof=1)
    pnl = np.array([x[0] for x in trades]) if trades else np.zeros(0)
    age = np.array([x[1] for x in trades]) if trades else np.zeros(0)
    win = pnl > 0
    per_bar_ent = float(ent[m].mean())
    turn = per_bar_ent / N_SLOTS / 2.0
    out = dict(
        bars=int(m.sum()), bp=float(d.mean() * 1e4),
        t=float(d.mean() / (sd / np.sqrt(d.size))) if sd > 0 else None,
        series=d, mask=m,
        trades=int(pnl.size),
        trade_mean=float(pnl.mean() * 1e4) if pnl.size else None,
        trade_median=float(np.median(pnl) * 1e4) if pnl.size else None,
        trade_mean_ex_top1=(float(np.mean(np.sort(pnl)[:-max(1, pnl.size // 100)])
                                  * 1e4) if pnl.size > 100 else None),
        win_rate=float(win.mean()) if pnl.size else None,
        payoff=(float(pnl[win].mean() / -pnl[~win].mean())
                if win.any() and (~win).any() else None),
        run=float(age.mean()) if age.size else None,
        run_win=float(age[win].mean()) if win.any() else None,
        run_lose=float(age[~win].mean()) if (~win).any() else None,
        entries_per_bar=per_bar_ent, turnover=turn,
        cost_bar_mean=rt_mean * turn, cost_bar_robust=rt_med * turn,
        run_dist=age.astype(int).tolist(),
        exits_trigger=fired["trigger"], exits_cap=fired["cap"],
        trigger_share=(fired["trigger"] / max(fired["trigger"] + fired["cap"], 1)))
    # THE RECONCILIATION. Total book P&L must equal total position P&L over the
    # same position-bars: summing a position's per-bar marks over its life IS
    # its trade P&L. Nothing in the original four assertions checked this, and
    # it is the one thing that would have caught the entry-bar double count.
    fl = np.isfinite(ret_lo) & (clo > 0)
    fh = np.isfinite(ret_hi) & (chi > 0)
    total_book = float((clo[fl] * ret_lo[fl]).sum() - (chi[fh] * ret_hi[fh]).sum())
    total_pos = float(pnl.sum() + resid)
    out["recon_book"] = total_book * 1e4
    out["recon_pos"] = total_pos * 1e4
    out["recon_gap_bp"] = (total_book - total_pos) * 1e4
    out["recon_rel"] = (abs(total_book - total_pos) / max(abs(total_pos), 1e-12))
    out["run_ratio"] = (out["run_win"] / out["run_lose"]
                        if out["run_win"] and out["run_lose"] else None)
    out["net_mean"] = out["bp"] - out["cost_bar_mean"]
    out["net_robust"] = out["bp"] - out["cost_bar_robust"]
    return out


def paired_t(a, b):
    """t on the per-bar difference of two book series, on their common bars."""
    m = a["mask"] & b["mask"]
    if int(m.sum()) < M.MIN_BARS:
        return None
    # rebuild both on the common mask rather than assuming alignment
    fa = np.full(m.shape, np.nan)
    fa[a["mask"]] = a["series"]
    fb = np.full(m.shape, np.nan)
    fb[b["mask"]] = b["series"]
    d = fa[m] - fb[m]
    sd = d.std(ddof=1)
    return None if sd == 0 else (float(d.mean() * 1e4),
                                 float(d.mean() / (sd / np.sqrt(d.size))),
                                 int(d.size))


# --------------------------------------------------------------------------
# the inputs the simulation reads
# --------------------------------------------------------------------------
def build_inputs(z, base, panel, live, T):
    """Everything the book reads, all lagged by `ranked` and nowhere else."""
    n = base.shape[0]
    order_a, cnt_a, _ = R.ranked(z[PRIMARY], base)
    plan = R.LegPlan(order_a, cnt_a, N_BASE, T)
    pc = {}
    for b in PAIR:
        _, cb, pb = R.ranked(z[b], base)
        pc[b] = (R.pct_at(pb, cb, plan.lo, plan.cols),
                 R.pct_at(pb, cb, plan.hi, plan.cols))
    bc = np.broadcast_to(plan.cols[None, :], plan.lo.shape)
    ctx = {}
    for si, (side, rows) in enumerate((("lo", plan.lo), ("hi", plan.hi))):
        a1, a2 = pc[PAIR[0]][si], pc[PAIR[1]][si]
        avg = (a1 + a2) / 2.0
        # low average percentile is best on the long leg, high on the short --
        # the same convention `op_meanrank` uses, so the selected set matches
        v = np.where(np.isnan(avg), np.inf, avg if side == "lo" else -avg)
        ordr = np.argsort(v, axis=0, kind="stable")
        pos = np.empty(ordr.shape, dtype=np.int32)
        np.put_along_axis(pos, ordr,
                          np.arange(avg.shape[0], dtype=np.int32)[:, None], axis=0)
        rank = np.full((n, T), n, dtype=np.int32)
        rank[rows.ravel(), bc.ravel()] = pos.ravel()
        prim = np.zeros((n, T), dtype=bool)
        prim[rows.ravel(), bc.ravel()] = True
        dis = np.full((n, T), np.nan)
        dis[rows.ravel(), bc.ravel()] = np.abs(a1 - a2).ravel()
        ctx[side] = dict(rank=rank, sel=rank < N_SLOTS, primary=prim, disagree=dis)
    r1 = np.where(live, np.expm1(panel.total_log_returns), np.nan).astype(np.float64)
    return ctx, r1, roll_vol(r1, live, 21), plan


def roll_vol(r1, live, w):
    """Trailing std of a name's OWN 1-bar returns, over its own live bars, LAGGED.

    The unit the stops are measured in, so a stop is the same size in RISK for a
    quiet name and a violent one. A stop in price terms would be a price-level
    tilt in disguise, which is what killed D284.
    """
    n, T = r1.shape
    out = np.full((n, T), np.nan)
    for i in range(n):
        at = np.flatnonzero(live[i])
        if at.size < w + 1:
            continue
        v = r1[i, at]
        good = np.isfinite(v)
        v = np.where(good, v, 0.0)
        c1 = np.concatenate([[0.0], np.cumsum(v)])
        c2 = np.concatenate([[0.0], np.cumsum(v * v)])
        cg = np.concatenate([[0], np.cumsum(good.astype(np.int64))])
        j = np.arange(w, at.size)
        cnt = cg[j + 1] - cg[j + 1 - w]
        s1 = c1[j + 1] - c1[j + 1 - w]
        s2 = c2[j + 1] - c2[j + 1 - w]
        with np.errstate(invalid="ignore", divide="ignore"):
            var = (s2 - s1 * s1 / np.maximum(cnt, 1)) / np.maximum(cnt - 1, 1)
        sd = np.sqrt(np.maximum(var, 0.0))
        sd[cnt < w // 2] = np.nan
        out[i, at[j]] = sd
    out[:, 1:] = out[:, :-1]      # a stop sized on today's close is look-ahead
    out[:, 0] = np.nan
    return out


def cell_masks(cell, ctx, half, base, n, T):
    """(skip_name, idle_bar). Arm B uses neither."""
    tag, _, param = cell
    if tag == "C1":
        d = np.fmax(np.nan_to_num(ctx["lo"]["disagree"], nan=-1.0),
                    np.nan_to_num(ctx["hi"]["disagree"], nan=-1.0))
        skip = np.zeros((n, T), dtype=bool)
        for t in range(T):
            f = d[:, t] > -1.0
            if f.sum() < 10:
                continue
            skip[f, t] = d[f, t] > np.quantile(d[f, t], param)
        return skip, None
    if tag == "C2":
        disp = np.full(T, np.nan)
        for t in range(T):
            v = ctx["lo"]["disagree"][:, t]
            v = v[np.isfinite(v)]
            if v.size > 5:
                disp[t] = v.std()
        return None, np.isfinite(disp) & (disp <= np.nanquantile(disp, 1 / 3))
    if tag == "C3":
        med = np.full(T, np.nan)
        for t in range(T):
            v = half[:, t][base[:, t] & np.isfinite(half[:, t])]
            if v.size > 20:
                med[t] = np.median(v)
        return None, np.isfinite(med) & (med >= np.nanquantile(med, 2 / 3))
    return None, None


def run_cell(cell, ctx, r1, vol, half, base, n, T, rt_mean, rt_med,
             runs=None, rng=None):
    """One cell. `runs` non-None makes it the persistence-matched null."""
    _, rule, param = cell
    skip, idle = cell_masks(cell, ctx, half, base, n, T)
    if runs is not None:
        rule, param = "sampled_runs", (runs, rng)
    lo, hi, ent, tr, fired, clo, chi, resid = simulate(
        ctx, r1, vol, rule, param, skip, idle, n, T)
    return book_stats(lo, hi, ent, tr, fired, clo, chi, resid, rt_mean, rt_med)


# --------------------------------------------------------------------------
# assertions
# --------------------------------------------------------------------------
def assertions(ctx, r1, vol, half, base, n, T, panel, live, plan, z):
    print("\n  RUNNER ASSERTIONS", flush=True)

    # 1. LAG AUDIT, SECOND IMPLEMENTATION. The book must decide bar t's holdings
    #    from scores at t-1. Rebuilt by hand from the UNLAGGED arrays so a bug in
    #    the ranking cannot hide behind itself.
    sa, s1, s2 = z[PRIMARY], z[PAIR[0]], z[PAIR[1]]
    checked = 0
    for t in range(400, T, 613):
        q = np.flatnonzero(base[:, t])
        va = sa[q, t - 1]
        qa = q[np.isfinite(va)]
        if qa.size < 60:
            continue
        pick = qa[np.argsort(sa[qa, t - 1], kind="stable")[:N_BASE]]
        pcts = []
        for src in (s1, s2):
            v = src[q, t - 1]
            qq = q[np.isfinite(v)]
            rb = qq[np.argsort(src[qq, t - 1], kind="stable")]
            rank = {int(r): i for i, r in enumerate(rb)}
            pcts.append({int(r): ((rank[int(r)] + 0.5) / len(rb)
                                  if int(r) in rank else np.nan) for r in pick})
        avg = {int(r): (pcts[0][int(r)] + pcts[1][int(r)]) / 2 for r in pick}
        fin = [r for r in avg if np.isfinite(avg[r])]
        want = set(sorted(fin, key=lambda r: (avg[r], r))[:min(N_SLOTS, len(fin))])
        got = set(np.flatnonzero(ctx["lo"]["sel"][:, t]).tolist())
        assert want == got, f"LAG AUDIT FAILED at t={t}: {want ^ got}"
        checked += 1
    assert checked >= 4, f"lag audit covered only {checked} bars"
    print(f"    [1] lag audit: the selected set rebuilt from the unlagged scores "
          f"on {checked} bars, identical")

    raised = False
    try:
        bad = {"lo": dict(ctx["lo"]), "hi": ctx["hi"]}
        bad["lo"]["sel"] = np.roll(ctx["lo"]["sel"], -1, axis=1)
        for t in range(400, T, 613):
            q = np.flatnonzero(base[:, t])
            va = sa[q, t - 1]
            qa = q[np.isfinite(va)]
            if qa.size < 60:
                continue
            assert set(np.flatnonzero(bad["lo"]["sel"][:, t]).tolist()) == \
                set(np.flatnonzero(ctx["lo"]["sel"][:, t]).tolist())
    except AssertionError:
        raised = True
    assert raised, "the lag audit PASSED a forward-shifted selection"
    print(f"    [1b] and it raises on a forward-shifted selection")

    # 2. SIGN AUDIT, IN MONEY, ON BOTH LEGS. An oracle selection must make the
    #    simulated book strongly positive -- including the SHORT leg, the sign
    #    D280 got wrong for five parts on prose.
    f1 = np.where(live, np.expm1(panel.total_log_returns), np.nan)
    orc = np.full(f1.shape, np.nan)
    orc[:, :-1] = -f1[:, 1:]     # so that AFTER lag1 the score at bar t is
                                 # minus the return bar t is about to earn
    o_ord, o_cnt, _ = R.ranked(orc, base)
    opl = R.LegPlan(o_ord, o_cnt, N_BASE, T)
    obc = np.broadcast_to(opl.cols[None, :], opl.lo.shape)
    octx = {}
    for side, rows in (("lo", opl.lo), ("hi", opl.hi)):
        rank = np.full((n, T), n, dtype=np.int32)
        rank[rows.ravel(), obc.ravel()] = np.broadcast_to(
            np.arange(N_BASE, dtype=np.int32)[:, None], rows.shape).ravel()
        prim = np.zeros((n, T), dtype=bool)
        prim[rows.ravel(), obc.ravel()] = True
        octx[side] = dict(rank=rank, sel=rank < N_SLOTS, primary=prim)
    lo, hi, ent, tr, fd, _cl, _ch, _rs = simulate(
        octx, r1, vol, "none", None, None, None, n, T)
    m = np.isfinite(lo) & np.isfinite(hi)
    lo_bp, hi_bp = float(lo[m].mean() * 1e4), float(-hi[m].mean() * 1e4)
    for nm, v in (("long", lo_bp), ("short", hi_bp)):
        assert v > 10.0, (
            f"SIGN AUDIT FAILED: the oracle's {nm} leg earns {v:+.2f} bp/bar in "
            f"the simulation; a perfect-foresight book must be strongly positive")
    print(f"    [2] sign audit in money: oracle simulates to long {lo_bp:+.1f} "
          f"bp/bar, short {hi_bp:+.1f} bp/bar")

    # 3. RIGHT QUANTITY. The baseline holds EXACTLY the baseline, and the
    #    uncapped rules can exceed it. A simulator whose holding run does not
    #    match its own rule is not simulating that rule.
    base_stat = run_cell(("B0", "none", None), ctx, r1, vol, half, base, n, T,
                         100.0, 100.0)
    assert abs(base_stat["run"] - BASE_HOLD) < 0.35, (
        f"RIGHT QUANTITY FAILED: the no-exit book holds {base_stat['run']:.2f} "
        f"bars against a baseline of {BASE_HOLD}")
    tr_stat = run_cell(("B4", "trailing", 2.0), ctx, r1, vol, half, base, n, T,
                       100.0, 100.0)
    assert tr_stat["run"] > BASE_HOLD, (
        f"RIGHT QUANTITY FAILED: the UNCAPPED trailing rule holds "
        f"{tr_stat['run']:.2f} bars, no longer than the cap it does not have")
    print(f"    [3] right quantity: no-exit holds {base_stat['run']:.2f} bars "
          f"(baseline {BASE_HOLD}); uncapped trailing holds {tr_stat['run']:.2f}")

    # 4. THE ANTI-PATTERN MUST BEHAVE LIKE ONE. A profit target caps winners, so
    #    its winning trades must be SHORTER than its losing ones. If the
    #    mechanism does not show up here the rule is mislabelled and its P&L
    #    means nothing.
    pt = run_cell(("B6", "profit_target", 1.0), ctx, r1, vol, half, base, n, T,
                  100.0, 100.0)
    assert pt["run_win"] < pt["run_lose"], (
        f"MECHANISM CHECK FAILED: the profit target's winners run "
        f"{pt['run_win']:.2f} bars against losers {pt['run_lose']:.2f}; it is "
        f"supposed to cap winners")
    print(f"    [4] the profit target caps winners as designed: win run "
          f"{pt['run_win']:.2f} vs lose run {pt['run_lose']:.2f} "
          f"(ratio {pt['run_ratio']:.2f})")

    # 5. THE RECONCILIATION, AND IT IS THE ASSERTION THIS FILE MOST NEEDED.
    #    Summing a position's per-bar marks over its life IS its trade P&L, so
    #    total book P&L must equal total position P&L exactly. Nothing in [1]-[4]
    #    checked it, and the first version of this simulator marked the book
    #    AFTER the refill -- crediting bar t to both the position leaving a slot
    #    and the one taking it. That created one bar of return per turnover,
    #    worth +-75 to 85 bp on numbers of magnitude 7 to 77, and it ranked the
    #    rules by how often they traded. [1]-[4] all passed while it did.
    #    Checked on rules with DIFFERENT turnover, because the defect was
    #    invisible on the fixed-schedule control.
    for cell in (("B0", "none", None), ("B6", "profit_target", 1.0),
                 ("B4", "trailing", 1.0), ("B3", "adverse_stop", 1.0),
                 ("B5", "asymmetric", 1.5)):
        st = run_cell(cell, ctx, r1, vol, half, base, n, T, 100.0, 100.0)
        assert st["recon_rel"] < 1e-9, (
            f"RECONCILIATION FAILED for {cell[0]}: the book totals "
            f"{st['recon_book']:+,.0f} bp and the positions total "
            f"{st['recon_pos']:+,.0f} bp, a gap of {st['recon_gap_bp']:+,.0f} "
            f"({st['recon_rel']:.2%}). The book is not marking the same bars "
            f"the positions earned.")
    print(f"    [5] reconciliation: total book P&L == total position P&L to "
          f"<1e-9 relative, on five rules spanning 7.7% to 29.5% turnover")
    return base_stat


def fmt(v, w, d=2):
    return f"{v:+{w}.{d}f}" if v is not None else f"{'--':>{w}s}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=200)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--shard", type=int, default=None)
    ap.add_argument("--nshards", type=int, default=6)
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
    ctx, r1, vol, plan = build_inputs(z, base, panel, live, T)

    bc = np.broadcast_to(plan.cols[None, :], plan.lo.shape)
    hv, lv = [], []
    for side, rows in (("lo", plan.lo), ("hi", plan.hi)):
        sel = ctx[side]["sel"][rows.ravel(), bc.ravel()].reshape(rows.shape)
        v = half[rows[sel], bc[sel]]
        v = v[np.isfinite(v)]
        (lv if side == "lo" else hv).append(v)
    rt_mean = 2 * float(lv[0].mean()) + 2 * float(hv[0].mean())
    rt_med = 2 * float(np.median(lv[0])) + 2 * float(np.median(hv[0]))
    cells = cell_list()
    print(f"D295  {PRIMARY} x mean-rank({PAIR[0]}, {PAIR[1]}) @ f={FRAC}  "
          f"N_slots={N_SLOTS}  baseline hold={BASE_HOLD}")
    print(f"  {len(cells)} cells | round trip: mean {rt_mean:.1f} bp, robust "
          f"{rt_med:.1f} bp  ({time.time() - t0:.0f}s)", flush=True)
    assert len(cells) == 20, f"expected 19 cells + the control, built {len(cells)}"

    # Assertions run in EVERY mode, shards included: a null shard scoring a
    # book the audits would reject is worse than no null at all.
    assertions(ctx, r1, vol, half, base, n, T, panel, live, plan, z)

    # ---- SHARD MODE, AND IT MUST COME BEFORE ANYTHING THAT SPAWNS ----
    # A shard runs its stride of (cell, draw) null tasks and EXITS. The first
    # version of this file lost this branch to a silent `str.replace` no-op, so
    # every child ran the parent's path and spawned six more of its own: 86
    # processes and 4 MB of free RAM. The `assert` below the spawn block is the
    # belt to this brace.
    if a.shard is not None:
        od = json.loads((REPO / "temp" / "d295_observed.json").read_text())
        tasks = [(k2, d) for k2 in sorted(od["run_dist"]) for d in range(a.draws)]
        out = {}
        for k2, d in tasks[a.shard::a.nshards]:
            runs = np.array(od["run_dist"][k2], dtype=int)
            if runs.size == 0:
                continue
            st = run_cell(tuple(od["cells"][k2]), ctx, r1, vol, half, base, n, T,
                          rt_mean, rt_med, runs=runs,
                          rng=np.random.default_rng(SEED + 7919 * d))
            if st is not None:
                out.setdefault(k2, {})[str(d)] = st["bp"] - od["ctrl_bp"]
        (REPO / "temp" / f"d295_null_{a.shard}.json").write_text(json.dumps(out))
        print(f"  shard {a.shard}/{a.nshards}: {len(tasks[a.shard::a.nshards])} "
              f"tasks in {time.time() - t0:.0f}s", flush=True)
        return 0

    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    print(f"\n  OBSERVED: {len(cells)} cells", flush=True)
    obs = {}
    for c in cells:
        s = run_cell(c, ctx, r1, vol, half, base, n, T, rt_mean, rt_med)
        if s is not None:
            obs[c[0] + (f"@{c[2]}" if c[2] is not None else "")] = (c, s)
    print(f"  {len(obs)} evaluated ({time.time() - t0:.0f}s)", flush=True)

    # what the shards need: each cell's OWN holding-run distribution, so the
    # null matches RATE and PERSISTENCE rather than count alone (D279; and the
    # mismatch that voided D291's veto arm)
    (REPO / "temp" / "d295_observed.json").write_text(json.dumps({
        "cells": {k2: list(v[0]) for k2, v in obs.items() if k2 != "B0"},
        "run_dist": {k2: v[1]["run_dist"] for k2, v in obs.items() if k2 != "B0"},
        "ctrl_bp": obs["B0"][1]["bp"]}))

    ctrl = obs["B0"][1]
    rows = []
    for key, (c, s) in obs.items():
        pt = paired_t(s, ctrl) if key != "B0" else None
        rows.append(dict(cell=key, tag=c[0], rule=c[1], param=c[2],
                         bp=s["bp"], t=s["t"], bars=s["bars"],
                         trades=s["trades"], trade_mean=s["trade_mean"],
                         trade_median=s["trade_median"],
                         trade_mean_ex_top1=s["trade_mean_ex_top1"],
                         win_rate=s["win_rate"], payoff=s["payoff"],
                         run=s["run"], run_win=s["run_win"],
                         run_lose=s["run_lose"], run_ratio=s["run_ratio"],
                         turnover=s["turnover"],
                         cost_bar_mean=s["cost_bar_mean"],
                         cost_bar_robust=s["cost_bar_robust"],
                         net_mean=s["net_mean"], net_robust=s["net_robust"],
                         trigger_share=s["trigger_share"],
                         d_bp=pt[0] if pt else None, d_t=pt[1] if pt else None))

    print(f"\n{'=' * 118}")
    print(f"  BOTH COLUMNS, AND WHICH MOVED   (control B0: {ctrl['bp']:+.2f} "
          f"bp/bar, trade mean {ctrl['trade_mean']:+.1f} bp, run "
          f"{ctrl['run']:.2f})")
    print(f"{'=' * 118}")
    print(f"  {'cell':16s} | {'PER-TRADE':>25s} | {'ON THE BOOK':>34s} | "
          f"{'run w/l':>15s}")
    print(f"  {'':16s} | {'mean':>7s} {'median':>7s} {'win%':>8s} | "
          f"{'bp/bar':>7s} {'vs ctrl':>8s} {'turn':>6s} {'net rob':>8s} | "
          f"{'win':>4s} {'lose':>5s} {'ratio':>4s}")
    for r in sorted(rows, key=lambda x: -(x["d_t"] if x["d_t"] is not None else -9)):
        print(f"  {r['cell']:16s} | {fmt(r['trade_mean'], 7, 1)} "
              f"{fmt(r['trade_median'], 7, 1)} "
              f"{(f'{r[chr(119)+chr(105)+chr(110)+chr(95)+chr(114)+chr(97)+chr(116)+chr(101)]:8.1%}' if r['win_rate'] else '       --')} | "
              f"{fmt(r['bp'], 7)} {fmt(r['d_t'], 8)} "
              f"{(f'{r[chr(116)+chr(117)+chr(114)+chr(110)+chr(111)+chr(118)+chr(101)+chr(114)]:6.1%}' if r['turnover'] else '    --')} "
              f"{fmt(r['net_robust'], 8)} | "
              f"{fmt(r['run_win'], 4, 1)} {fmt(r['run_lose'], 5, 1)} "
              f"{fmt(r['run_ratio'], 4, 1)}")

    # ---- the null, in subprocesses ----
    # THE GUARD, and it is not decoration. A shard that reached this line would
    # spawn six more of itself, each of which would spawn six more. That is
    # exactly what happened once: 86 processes and 4 MB of free RAM.
    assert a.shard is None, "a shard must never reach the spawn block"
    import subprocess
    print(f"\n  NULL: {len(obs) - 1} cells x {a.draws} rate- and "
          f"persistence-matched draws, {a.nshards} processes", flush=True)
    for i in range(a.nshards):
        (REPO / "temp" / f"d295_null_{i}.json").unlink(missing_ok=True)
    procs = [subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                               "--shard", str(i), "--nshards", str(a.nshards),
                               "--draws", str(a.draws)])
             for i in range(a.nshards)]
    codes = [pr.wait() for pr in procs]
    assert all(c == 0 for c in codes), f"a null shard failed: exit codes {codes}"
    dist = {}
    for i in range(a.nshards):
        f = REPO / "temp" / f"d295_null_{i}.json"
        assert f.exists(), f"shard {i} wrote no output"
        for key, dd in json.loads(f.read_text()).items():
            dist.setdefault(key, []).extend(dd.values())
    joint = []
    ndraw = min((len(v) for v in dist.values()), default=0)
    for d in range(ndraw):
        joint.append(max(dist[k][d] for k in dist))
    floor = float(np.percentile(joint, 95)) if joint else None
    for r in rows:
        arr = np.array(dist.get(r["cell"], []))
        r["null_p50"] = float(np.percentile(arr, 50)) if arr.size else None
        r["null_p95"] = float(np.percentile(arr, 95)) if arr.size else None
        r["beats_null"] = (bool(r["d_bp"] > r["null_p95"])
                           if (arr.size and r["d_bp"] is not None) else None)
        r["beats_floor"] = (bool(r["d_bp"] > floor)
                            if (floor is not None and r["d_bp"] is not None)
                            else None)
        r["cost_ok"] = (bool(r["cost_bar_robust"] <= ctrl["cost_bar_robust"])
                        if r["cell"] != "B0" else None)
        r["pass"] = bool(r["d_t"] is not None and r["d_t"] >= 2.0
                         and r["cost_ok"] and r["beats_null"] and r["beats_floor"])
    npass = sum(1 for r in rows if r.get("pass"))
    print(f"\n  joint max floor (best-of-{len(dist)}): {floor:+.3f} bp/bar | "
          f"{npass} of {len(rows) - 1} cells clear all four conditions")

    json.dump({"purpose": "D295 stage 2: exits and idle conditions on the "
                          "confluence, measured on the book with slots and "
                          "re-entry.",
               "preregistered": "b7262f5", "amended": "d33fc71",
               "n_slots": N_SLOTS, "baseline_hold": BASE_HOLD,
               "round_trip_mean": rt_mean, "round_trip_robust": rt_med,
               "draws": a.draws, "joint_floor": floor, "n_pass": npass,
               "rows": rows}, open(OUT, "w"), indent=1)
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
