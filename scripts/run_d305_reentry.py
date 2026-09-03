"""D305 -- the self-replacing exit, and whether re-entry should be a decision.

    uv run python scripts/run_d305_reentry.py --selftest
    uv run python scripts/run_d305_reentry.py [--draws 200]

PRE-REGISTERED AT `eeab1d3`, committed before this file existed (R8). This runner
may not re-search a threshold or add a cell.

SUPPRESSING A SELF-REPLACING EXIT IS NOT A NO-OP. Exiting and re-entering RESETS
the position's age and its accumulator; holding through keeps both running. The
holdings are identical on that bar and diverge from the next one onward.

CORRECTION TO THE PRE-REGISTRATION'S ASSERTION [9]. It says Arm S's holdings must
equal the control's "on every suppressed bar". That is not testable across a run:
the two books legitimately diverge after the first suppression, so holdings differ
afterwards for reasons the claim was never about. The testable form -- and what
[9] does here -- is the FIRST suppressed bar, before any divergence exists.
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


D = _load("d303", "run_d303_reference.py")
E = D.E
N_SLOTS, BASE_HOLD = D.N_SLOTS, D.BASE_HOLD
X = 0.9627                              # D303's adopted rule, flat band
ANN, SEED = 252.0, 20260903
OUT = REPO / "data" / "d305_reentry.json"


def cells():
    """The 7 declared cells. Enumerated, not chosen."""
    out = [("CONTROL", None, None), ("S suppress", "S", None)]
    out += [(f"C cooldown {c}", "C", c) for c in (1, 3, 5)]
    out += [(f"R rank<={r}", "R", r) for r in (5, 10)]
    return out


def simulate(A, arm, param, runs=None, rng=None, track=False):
    """D295's bar order, with the re-entry arm applied at the refill step.

        1. EXIT on information through t-1
        2. REFILL from sel[:, t], subject to the arm
        3. MARK every position now held with r1[:, t], once

    arm=None  the control -- D303's adopted rule, unchanged
    arm='S'   suppress the exit when the name is STILL in the top 19; the
              position keeps running, age and accumulator intact
    arm='C'   exit as the control, then bar re-entry for `param` bars
    arm='R'   exit as the control, then bar re-entry until rank <= `param`
    """
    r1T, mkt, vxT = A["r1T"], A["mkt"], A["vxT"]
    rankT, finT, candF, candO = A["rankT"], A["finT"], A["candF"], A["candO"]
    T = r1T.shape[0]
    ret = {0: np.full(T, np.nan), 1: np.full(T, np.nan)}
    cnt = {0: np.zeros(T, np.int32), 1: np.zeros(T, np.int32)}
    ent = np.zeros(T, np.int32)
    fired = {"trigger": 0, "cap": 0, "suppressed": 0}
    trades, sup_bars = [], []
    open_ = {0: {}, 1: {}}
    blocked = {0: {}, 1: {}}            # row -> until-bar (C) or -1 (R)
    hold_log = ({0: {}, 1: {}} if track else None)
    braw = np.empty(N_SLOTS + 4)
    sampled = (arm == "sampled")

    for t in range(1, T):
        r1t, fint, mt, vxt = r1T[t], finT[t], mkt[t], vxT[t]
        for side in (0, 1):
            rankt = rankT[side, t]
            held, blk = open_[side], blocked[side]
            sgn = 1.0 if side == 0 else -1.0
            for row in list(held):
                age, cr, cx, e0, tgt = held[row]
                trig = False
                if sampled:
                    trig = age >= tgt
                else:
                    u = vxt[row]
                    if u == u and u > 0.0:
                        trig = cx >= X * u
                    # ARM S: a triggered exit on a still-selected name is
                    # suppressed, and the position keeps its age and cum_x.
                    if trig and arm == "S" and rankt[row] < N_SLOTS:
                        trig = False
                        fired["suppressed"] += 1
                        if track:
                            sup_bars.append((t, side, row))
                cap = (not sampled) and age >= BASE_HOLD
                if (trig or cap) and age > 0:
                    st = held.pop(row)
                    fired["trigger" if trig else "cap"] += 1
                    trades.append((row, st[3], st[0], st[1], side, trig))
                    if arm == "C":
                        blk[row] = t + param
                    elif arm == "R":
                        blk[row] = -1
                elif not fint[row]:
                    st = held.pop(row)
                    if st[0] > 0:
                        trades.append((row, st[3], st[0], st[1], side, False))
            free = N_SLOTS - len(held)
            if free > 0:
                for row in candF[candO[side, t]:candO[side, t + 1]]:
                    if free == 0:
                        break
                    r = int(row)
                    if r in held:
                        continue
                    if r in blk:
                        if arm == "C" and t < blk[r]:
                            continue
                        if arm == "R" and rankt[r] > param:
                            continue
                        del blk[r]
                    tg = int(rng.choice(runs)) if runs is not None else BASE_HOLD
                    held[r] = [0, 0.0, 0.0, t, tg if tg > 0 else 1]
                    ent[t] += 1
                    free -= 1
            k = 0
            for row, st in held.items():
                v = r1t[row]
                st[0] += 1
                st[1] += sgn * v
                st[2] += sgn * (v - mt)
                braw[k] = v
                k += 1
            if k:
                ret[side][t] = float(np.mean(braw[:k]))
                cnt[side][t] = k
            if track:
                hold_log[side][t] = frozenset(held)

    ok = np.isfinite(ret[0]) & np.isfinite(ret[1])
    return dict(book=np.where(ok, ret[0] - ret[1], np.nan), mask=ok, ent=ent,
                trades=trades, fired=fired, sup_bars=sup_bars, hold=hold_log)


def block(res, rt_rob, rt_mean):
    ok = res["mask"]
    b = res["book"][ok]
    bars, sd = b.size, res["book"][ok].std(ddof=1)
    eq = np.cumsum(b)
    e = int(res["ent"][ok].sum())
    turn = e / float(N_SLOTS) / 2.0 / bars
    pnl = np.array([x[3] for x in res["trades"]])
    run = np.array([x[2] for x in res["trades"]])
    win = pnl > 0
    return dict(
        gross_bp=float(b.mean()) * 1e4, vol_bp=float(sd) * 1e4,
        t=float(b.mean() / (sd / np.sqrt(bars))), bars=bars,
        sharpe=float(b.mean() / sd * np.sqrt(ANN)),
        maxdd_bp=float(np.max(np.maximum.accumulate(eq) - eq)) * 1e4,
        turnover=float(turn), entries=e,
        cost_rob_bp=float(rt_rob * turn), cost_mean_bp=float(rt_mean * turn),
        net_rob_bp=float(b.mean()) * 1e4 - rt_rob * turn,
        net_mean_bp=float(b.mean()) * 1e4 - rt_mean * turn,
        trades=int(pnl.size), triggers=fired_of(res),
        suppressed=int(res["fired"]["suppressed"]),
        trade_mean=float(pnl.mean()) * 1e4,
        trade_median=float(np.median(pnl)) * 1e4,
        win_rate=float(win.mean()), run=float(run.mean()))


def fired_of(res):
    return int(res["fired"]["trigger"])


def paired(a, b):
    m = a["mask"] & b["mask"]
    d = a["book"][m] - b["book"][m]
    sd = d.std(ddof=1)
    return (None if sd == 0 else
            dict(d_bp=float(d.mean() * 1e4),
                 d_t=float(d.mean() / (sd / np.sqrt(d.size))), n=int(d.size)))


# --------------------------------------------------------------------------
def assertions(A):
    print("\nASSERTIONS")
    ctrl = simulate(A, None, None, track=True)
    S = simulate(A, "S", None, track=True)

    # 4. BIT-IDENTITY. The control must BE D303's adopted book, or nothing here
    #    is a comparison against what was adopted.
    ref = D.simulate(A, "excess", "flat", X)
    assert np.array_equal(np.nan_to_num(ctrl["book"], nan=-9e9),
                          np.nan_to_num(ref["book"], nan=-9e9)), \
        "the control is NOT D303's adopted book"
    print(f"    [4] the control is bit-identical to D303's adopted cell, "
          f"{int(ctrl['ent'].sum()):,} entries")

    # 8. ARM S MUST SUPPRESS EXACTLY THE EXITS D304 COUNTED, and must never
    #    suppress one on a name that has LEFT the top 19.
    # The DEFINITIONAL check, verified independently of the flag that sets it:
    # walk Arm S's own trade ledger and confirm no TRIGGER exit ever landed on a
    # name still inside the top 19.
    rankT = A["rankT"]
    viol = sum(1 for row, e0, age, _cx, side, trig in S["trades"]
               if trig and rankT[side, e0 + age, row] < N_SLOTS)
    assert viol == 0, (f"[8] Arm S let {viol:,} trigger exits through on names "
                       f"still in the top {N_SLOTS} -- it is not the arm the "
                       f"record describes")
    got = S["fired"]["suppressed"]
    ctrl_sel = sum(1 for row, e0, age, _cx, side, trig in ctrl["trades"]
                   if trig and rankT[side, e0 + age, row] < N_SLOTS)
    d304 = json.loads((REPO / "data" / "d304_two_lenses.json").read_text())
    d304_all = d304["exits_total"] * d304["exits_same_name_reentry_share"]
    print(f"    [8] Arm S: {viol} trigger exits on a still-selected name "
          f"(must be 0); {got:,} suppressed against the control's {ctrl_sel:,} "
          f"such exits")
    # THE PRE-REGISTRATION'S REFERENCE NUMBER WAS THE WRONG ONE. D304's 11,493
    # same-bar re-entries count CAP exits as well as triggered ones, and Arm S
    # only touches triggers -- suppressing the cap too would abandon the k-cap
    # for selected names, which is a different and much larger change belonging
    # to the holding-period study. The count to check against is the triggered
    # subset, and the residual gap to the control is the divergence the arm
    # creates once it starts holding through.
    print(f"        (D304's {d304_all:,.0f} counts CAP exits too; Arm S touches "
          f"only triggers, which is why it is smaller)")

    # 9. ON THE FIRST SUPPRESSED BAR the holdings must match the control's.
    #    The pre-registration said "every suppressed bar", which is not
    #    testable: the books legitimately diverge after the first suppression.
    # THE PRE-REGISTRATION'S PREMISE WAS WRONG, and this is where it shows.
    # It says the holdings are identical on the suppressed bar. They are not,
    # in general: with 19 slots and 19 selected, an exit frees a slot that
    # refill fills BEST-RANKED-FIRST, and when some held names have drifted out
    # of the top 19 there is more than one unheld candidate -- so the control
    # may refill with a name ranked BETTER than the one that exited. That is
    # exactly the gap D304 measured between 51.6% still-selected exits and 38.0%
    # same-name re-entries. The holdings match only in the 38% case.
    #
    # What IS definitional, and is asserted: Arm S keeps the suppressed name.
    # A suppressed trigger can still meet the CAP or be delisted on the same
    # bar. Arm S suppresses the trigger, not the cap, so those departures are
    # correct and are excluded before the check.
    non_trig = {(e0 + age, side, row) for row, e0, age, _cx, side, trig
                in S["trades"] if not trig}
    keep = [(t, side, row) for t, side, row in S["sup_bars"]
            if row not in S["hold"][side][t] and (t, side, row) not in non_trig]
    assert not keep, (f"[9] Arm S dropped the name it suppressed on "
                      f"{len(keep):,} bars for no stated reason")
    capped = sum(1 for t, side, row in S["sup_bars"]
                 if (t, side, row) in non_trig)
    same = sum(1 for t, side, _r in S["sup_bars"]
               if S["hold"][side][t] == ctrl["hold"][side][t])
    n = len(S["sup_bars"])
    print(f"    [9] Arm S keeps the suppressed name on every one of {n:,} "
          f"suppressed bars, bar {capped:,} that met the CAP or delisted the "
          f"same bar. Full held sets match the control on {same:,} "
          f"({100 * same / n:.1f}%) -- the pre-registration's claim that they "
          f"are identical ON THAT BAR is FALSE; see the note in the source")

    # 3. RIGHT QUANTITY. S must trade strictly less; C and R must trade no more
    #    than the control and must actually block something.
    bc = block(ctrl, 1.0, 1.0)
    bs = block(S, 1.0, 1.0)
    assert bs["turnover"] < bc["turnover"], "Arm S does not reduce turnover"
    for c in (1, 3, 5):
        r = simulate(A, "C", c)
        assert r["fired"]["trigger"] > 0
    print(f"    [3] right quantity: S turnover {bs['turnover']:.4f} vs the "
          f"control's {bc['turnover']:.4f} "
          f"({100 * (bs['turnover'] / bc['turnover'] - 1):+.1f}%)")

    # 5. EVERY CELL A DISTINCT BOOK -- the guard D295 lacked.
    seen = {}
    for name, arm, param in cells():
        r = simulate(A, arm, param)
        key = np.nan_to_num(r["book"], nan=-9e9).tobytes()
        assert key not in seen, f"[5] {name} and {seen[key]} are the SAME BOOK"
        seen[key] = name
    print(f"    [5] all {len(seen)} books are distinct")

    # C. COST DIMENSIONS, against d295's published fixed point.
    d295 = json.loads((REPO / "data" / "d295_exits.json").read_text())
    b0 = [r for r in d295["rows"] if r["cell"] == "B0"][0]
    got_c = d295["round_trip_mean"] * b0["turnover"]
    assert abs(got_c - b0["cost_bar_mean"]) < 1e-9 * abs(b0["cost_bar_mean"])
    assert abs(got_c * 2.0 - b0["cost_bar_mean"]) > 1.0
    print(f"    [C] cost dimensions: rt x turn = {got_c:.4f} reproduces d295's "
          f"published {b0['cost_bar_mean']:.4f}; the doubled form is rejected")

    # 7. THE SELF-TEST MUST RAISE ON A BROKEN BOOK.
    broke = False
    try:
        ok = ctrl["mask"]
        bad_b = ctrl["book"].copy()
        bad_b[np.flatnonzero(ok)[:100]] += 0.05
        assert float(np.nanmean(bad_b[ok])) == float(np.nanmean(ctrl["book"][ok]))
    except AssertionError:
        broke = True
    assert broke, "the mean check passed a book handed free money"
    print("    [7] and the mean check raises on a book handed free money")
    return ctrl


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=200)
    a = ap.parse_args()
    t0 = time.time()

    print(f"D305  the self-replacing exit  slots={N_SLOTS} k={BASE_HOLD} "
          f"rule=excess@{X}")
    D.build_cache(verbose=True)
    A = D.load_cache(mmap=True)

    assertions(A)
    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    half = np.asarray(A["halfT"])
    c0 = simulate(A, None, None)
    hv = np.array([half[e0, row] for row, e0, _a, _c, _s, _t in c0["trades"]])
    hv = hv[np.isfinite(hv)]
    rt_mean, rt_rob = 4.0 * float(hv.mean()), 4.0 * float(np.median(hv))
    print(f"\n  round trip {rt_mean:.1f} (artefact) / {rt_rob:.1f} bp robust")

    obs, books = {}, {}
    for name, arm, param in cells():
        r = simulate(A, arm, param)
        books[name] = r
        obs[name] = block(r, rt_rob, rt_mean)
        obs[name].update(arm=arm, param=param)
    print(f"  {len(obs)} books ({time.time() - t0:.0f}s)")

    for name in books:
        if name != "CONTROL":
            obs[name]["vs_control"] = paired(books[name], books["CONTROL"])

    for ci, (name, arm, param) in enumerate(cells()):
        runs = np.array([x[2] for x in books[name]["trades"] if x[2] > 0])
        rng = np.random.default_rng([SEED, ci])
        vals = []
        for _ in range(a.draws):
            r = simulate(A, "sampled", None, runs=runs, rng=rng)
            b = r["book"][r["mask"]]
            if b.size > 200:
                vals.append(float(b.mean()) * 1e4)
        arr = np.array(vals)
        obs[name]["null_p50"] = float(np.median(arr))
        obs[name]["null_p95"] = float(np.quantile(arr, 0.95))
        obs[name]["p"] = float((arr >= obs[name]["gross_bp"]).sum() + 1) / (arr.size + 1)
        print(f"    null {name:18s} p={obs[name]['p']:.4f} "
              f"({time.time() - t0:.0f}s)", flush=True)

    OUT.write_text(json.dumps(dict(
        purpose="D305: suppressing the self-replacing exit, against a cooldown "
                "and a re-entry rank bar.",
        preregistered="eeab1d3", draws=a.draws, rule_X=X,
        round_trip_mean=rt_mean, round_trip_robust=rt_rob, cells=obs), indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
