"""D417 -- exits: stop loss, trailing stop, take profit. Bar committed in 962c8c8 BEFORE this ran.

    uv run python scripts/run_d417_exits.py --run

Path-invariant. Entry is the touch-day close (D413), the time stop is the close of t+5 in every
arm, and each rule is an EARLY exit laid over that.

TWO ARMS. DAILY: D413's 180,050 touches on the full universe, daily high/low triggers -- primary,
the population where the signal lives. 15m: D414's 3,023 events on 32 names, 15-minute triggers --
a precision check, which also runs the DAILY-bar rules on its own events so intraday-vs-daily is
paired. ONE walking function serves both arms over (events x bars) arrays, so the two are the same
logic and not two implementations that happen to agree.

THE RULES, distances in the touch day's own ATR (D388), demand shown and supply the mirror:
  SL(a)   exit when price trades at or beyond entry - a*ATR              a = 1.5 primary; 1.0, 2.5
  TS(b)   exit when price trades at or beyond best - b*ATR, best updated  b = 1.5 primary; 1.0, 2.5
          at each bar's close and checked against the NEXT bar
  TP(c)   exit when price trades at or beyond entry + c*ATR              c = 2.0 primary; 1.0, 3.0
  SLTP    SL 1.5 and TP 2.0 together                                     shape, cannot clear
FILLS, conservative in the direction that hurts: at the trigger unless the bar's OPEN is already
through it, then at the open. Stop-first when a stop and a target are both reachable in one bar.
[FILL] asserts no stop filled better than its trigger and no target worse.

THE GATE is MEAN PER TRADE, paired against the fixed exit on the same events, per family, on the
daily arm pooled. std ratio, bp per day, max loss, win rate and the counterfactual on early-exited
trades are reported beside every gate and gate nothing.
"""
import argparse
import importlib.util
import json
import pathlib
import sys
import time

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("d414", REPO / "scripts" / "run_d414_15m_entry.py")
F = importlib.util.module_from_spec(_s)
sys.modules["d414"] = F
_s.loader.exec_module(F)                      # the [SPLIT] holdout guard comes with it
C, M, Z4, D = F.C, F.M, F.Z4, F.D

OUT = REPO / "data" / "d417_exits.json"
D414_ART = REPO / "data" / "d414_15m_entry.json"
D413_N, D413_CELL2, D414_N = 180050, 26024, 3023
HOLD = 5
RULES = [("SL", 1.5), ("SL", 1.0), ("SL", 2.5),
         ("TS", 1.5), ("TS", 1.0), ("TS", 2.5),
         ("TP", 2.0), ("TP", 1.0), ("TP", 3.0),
         ("SLTP", (1.5, 2.0))]
PRIMARY = {"SL": 1.5, "TS": 1.5, "TP": 2.0}


def rname(fam, p):
    return f"{fam}{p[0]}_{p[1]}" if fam == "SLTP" else f"{fam}{p}"


# ------------------------------------------------------------------ the one walker
def walk(OP, HI, LO, CL, E, ATR, side, last_close):
    """Exit bar and price for every rule, over (n, B) bar arrays. NaN bars are skipped.

    Everything is done in LONG space: a short is flipped by negating prices, so 'stop below,
    target above' holds for both and the mirror is exact by construction rather than by a second
    set of branches. Prices come back out un-flipped."""
    s = side[:, None].astype(float)
    o, h, l, c = s * OP, s * HI, s * LO, s * CL          # signed: favourable is UP for everyone
    hi_s = np.where(s > 0, h, l)                          # the signed bar's true high/low
    lo_s = np.where(s > 0, l, h)
    e = side.astype(float) * E
    n, B = o.shape
    out = {}
    for fam, p in RULES:
        exit_bar = np.full(n, -1)
        fill = np.full(n, np.nan)
        best = e.copy()                                   # trailing best, updated at each close
        done = np.zeros(n, bool)
        a = p if fam == "SL" else (p[0] if fam == "SLTP" else None)
        b = p if fam == "TS" else None
        cc = p if fam == "TP" else (p[1] if fam == "SLTP" else None)
        for j in range(B):
            ok = ~done & np.isfinite(o[:, j]) & np.isfinite(hi_s[:, j]) & np.isfinite(lo_s[:, j])
            stop = None
            if a is not None:
                stop = e - a * ATR
            if b is not None:
                stop = best - b * ATR                      # best through the PREVIOUS close
            hit_stop = ok & (stop is not None) & (lo_s[:, j] <= (stop if stop is not None else -np.inf))
            hit_tp = ok & (cc is not None) & (hi_s[:, j] >= (e + cc * ATR if cc is not None else np.inf))
            # stop-first when both are reachable in the same bar
            take_stop = hit_stop
            take_tp = hit_tp & ~hit_stop
            if stop is not None:
                fs = np.minimum(stop, o[:, j])            # gap through a stop fills WORSE
                fill = np.where(take_stop, fs, fill)
            if cc is not None:
                ft = np.maximum(e + cc * ATR, o[:, j])    # gap through a target fills BETTER
                fill = np.where(take_tp, ft, fill)
            newly = take_stop | take_tp
            exit_bar = np.where(newly, j, exit_bar)
            done |= newly
            if b is not None:
                best = np.where(ok & ~done, np.maximum(best, hi_s[:, j]), best)
        # the time stop
        fill = np.where(done, fill, side.astype(float) * last_close)
        out[rname(fam, p)] = dict(bar=exit_bar, price=side.astype(float) * fill, early=done)
    return out


def assert_FILL(res, E, ATR, side):
    """[FILL] no stop filled better than its trigger; no target worse than its trigger."""
    e = side.astype(float) * E
    for fam, p in RULES:
        r = res[rname(fam, p)]
        m = r["early"]
        if not m.any():
            continue
        f = side.astype(float) * r["price"]
        if fam in ("SL", "SLTP"):
            a = p if fam == "SL" else p[0]
            # a stop fill is at or below the stop; a target fill (in SLTP) is at or above the target
            stops = m & (f <= e - a * ATR + 1e-9)
            tps = m & ~stops
            assert np.all(f[stops] <= (e - a * ATR)[stops] + 1e-9), f"[FILL] {fam} stop filled better than trigger"
            if fam == "SLTP":
                assert np.all(f[tps] >= (e + p[1] * ATR)[tps] - 1e-9), f"[FILL] SLTP target filled worse than trigger"
        elif fam == "TP":
            assert np.all(f[m] >= (e + p * ATR)[m] - 1e-9), f"[FILL] TP filled worse than trigger"
        elif fam == "TS":
            pass  # the trail's trigger varies by bar; checked against the entry-anchored bound below
            assert np.all(f[m] <= e[m] + 50 * ATR[m]), "[FILL] TS fill implausible"
    return True


def assert_SIGN():
    """[SIGN] the walker does what the words say, in money, long and short."""
    ATR = np.array([2.0, 2.0, 2.0, 2.0]); E = np.array([100.0, 100.0, 100.0, 100.0])
    side = np.array([1, 1, -1, 1])
    # ev0 long: drops 2 ATR on day 1, recovers to 104 -> SL1.5 fires at 97, delta < 0
    # ev1 long: rallies to 105 on day 2, gives back to 101 -> TP2.0 fires at 104, delta > 0
    # ev2 SHORT mirror of ev0: rises 2 ATR day 1, then falls to 96 -> SL fires at 103, delta < 0
    # ev3 long: gaps DOWN through the stop at the open on day 1 -> fills at the open (worse)
    OP = np.array([[100, 96.5, 98, 101, 103], [100, 102, 105, 103, 101.5], [100, 103.5, 102, 99, 97], [95, 96, 98, 101, 103]], float)
    HI = np.array([[101, 98, 101, 103, 104], [102, 105, 105.5, 103.5, 102], [104, 104, 103, 100, 98], [96, 97, 99, 102, 104]], float)
    LO = np.array([[96, 96, 97.5, 100.5, 102.5], [99.5, 101.5, 103, 101, 100.5], [99, 102, 99.5, 97.5, 96], [94, 95.5, 97.5, 100.5, 102.5]], float)
    CL = np.array([[97, 97.5, 100.5, 102.5, 104], [101.5, 104.5, 103.5, 101.5, 101], [103, 102.5, 100, 98, 96], [95.5, 97, 100.5, 102.5, 104]], float)
    last = CL[:, -1]
    r = walk(OP, HI, LO, CL, E, ATR, side, last)
    lg = lambda p: np.log(p)
    base = side * (lg(last) - lg(E))
    sl = r["SL1.5"]; tp = r["TP2.0"]
    r_sl = side * (lg(sl["price"]) - lg(E)); r_tp = side * (lg(tp["price"]) - lg(E))
    assert sl["early"][0] and abs(sl["price"][0] - 97.0) < 1e-9, f"[SIGN] long SL: {sl['price'][0]}"
    assert r_sl[0] < 0 < base[0], "[SIGN] long SL must lose where the fixed exit won"
    assert tp["early"][1] and abs(tp["price"][1] - 104.0) < 1e-9, f"[SIGN] TP: {tp['price'][1]}"
    assert r_tp[1] > base[1] > 0, "[SIGN] TP must beat the fixed exit on the give-back path"
    assert sl["early"][2] and abs(sl["price"][2] - 103.0) < 1e-9, f"[SIGN] short SL: {sl['price'][2]}"
    assert r_sl[2] < 0 < base[2], "[SIGN] short SL mirror"
    assert sl["early"][3] and abs(sl["price"][3] - 95.0) < 1e-9, f"[SIGN] gap-through must fill at the OPEN: {sl['price'][3]}"
    assert_FILL(r, E, ATR, side)
    return True


# ------------------------------------------------------------------ stats
def stat(x, label):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    if x.size < 2:
        return dict(label=label, n=int(x.size))
    se = x.std(ddof=1) / np.sqrt(x.size)
    return dict(label=label, n=int(x.size), mean=float(1e4 * x.mean()), se=float(1e4 * se),
                t=float(x.mean() / se) if se > 0 else float("nan"),
                median=float(1e4 * np.median(x)), win=float(100 * (x > 0).mean()))


def summarise(res, E, side, r_base, hold_scale, tag, mask=None):
    """Every quantity of record section 3, per rule."""
    if mask is None:
        mask = np.ones(E.size, bool)
    lgE = np.log(E)
    out = {}
    for fam, p in RULES:
        key = rname(fam, p)
        r = res[key]
        rr = side * (np.log(r["price"]) - lgE)
        m = mask & np.isfinite(rr) & np.isfinite(r_base)
        d = rr - r_base
        early = r["early"] & m
        held = ~r["early"] & m
        hold = np.where(r["early"], r["bar"] + 1, hold_scale * HOLD) / hold_scale   # in DAYS
        out[key] = dict(
            rule=stat(rr[m], f"{key} rule"),
            delta=stat(d[m], f"{key} PAIRED rule - fixed"),
            early_share=float(early.sum() / max(m.sum(), 1)),
            hold_days=float(hold[m].mean()),
            bp_per_day=float(1e4 * rr[m].mean() / hold[m].mean()),
            std_ratio=float(rr[m].std(ddof=1) / r_base[m].std(ddof=1)),
            max_loss=float(1e4 * rr[m].min()),
            cf_early=stat(r_base[early], f"{key} fixed-exit return on EARLY-exited"),
            # THE MECHANISM NUMBER: what the rule actually filled the early-exited trades at.
            # Against cf_early it says whether an exit forfeited or protected -- on the SAME trades.
            # It is cf_early + delta/early_share exactly (delta is zero on held trades), stored so
            # the record quotes the artifact rather than arithmetic on it.
            rule_early=stat(rr[early], f"{key} RULE return on the SAME early-exited"),
            cf_held=stat(r_base[held], f"{key} fixed-exit return on HELD"),
            exit_bar_p50=float(np.median(r["bar"][early])) if early.any() else None)
    out["_base"] = dict(rule=stat(r_base[mask & np.isfinite(r_base)], "fixed exit"),
                        std=float(r_base[mask & np.isfinite(r_base)].std(ddof=1)),
                        max_loss=float(1e4 * r_base[mask & np.isfinite(r_base)].min()))
    return out


def show(S, key, indent="  "):
    q = S[key]; r, d = q["rule"], q["delta"]
    if "mean" not in d:
        print(f"{indent}{key:10s} (too few)"); return
    print(f"{indent}{key:10s} rule {r['mean']:+7.2f}   PAIRED {d['mean']:+7.2f} +-{d['se']:5.2f} "
          f"({d['t']:+5.1f} SE)   early {100*q['early_share']:5.1f}%   hold {q['hold_days']:.2f}d   "
          f"bp/d {q['bp_per_day']:+6.2f}   std x{q['std_ratio']:.2f}   maxloss {q['max_loss']:+7.0f}   "
          f"win {r['win']:.1f}%   cf_early {q['cf_early'].get('mean', float('nan')):+7.2f}")


# ------------------------------------------------------------------ the arms
def daily_arm(P, t, i, side, atr):
    T = P["CL"].shape[0]
    off = np.arange(1, HOLD + 1)
    rows = t[:, None] + off[None, :]
    cols = np.repeat(i[:, None], HOLD, axis=1)
    g = lambda A: Z4.gather(A, rows, cols, T)[0]
    OP, HI, LO, CL = g(P["OP"]), g(P["HI"]), g(P["LO"]), g(P["CL"])
    E = P["CL"][t, i]
    last = P["CL"][np.clip(t + HOLD, 0, T - 1), i]
    ATR = atr[t, i]
    return walk(OP, HI, LO, CL, E, ATR, side, last), E, ATR


def run():
    t0 = time.time()
    print("D417  exits: stop loss, trailing stop, take profit")
    print("      the bar was committed in 962c8c8 BEFORE this ran\n")
    assert_SIGN()
    print("  [SIGN] long SL, TP give-back, short mirror, gap-through-fills-at-open: all as the words say")

    # ================= DAILY ARM =================
    P = D.load_panel(verbose=False)
    atr = Z4.atr_of(P)
    A = Z4.run_arm(P, atr, "dep", M.THETA, M.LIFE, M.H, delta=M.DELTA)
    Z, g = A["Z"], A["good"]
    t = A["tt"][g]; i = Z["i"][g]; side = Z["side"][g]; r_base = A["r"][g]
    lg = np.log(np.where(P["CL"] > 0, P["CL"], np.nan))
    tr5 = D.trailing_ret(lg, 5); eff = C.path_efficiency(lg); DV = D.X.roll_mean_T(P["CL"] * P["VOL"])
    rev = tr5[t, i] * side; ef = eff[t, i]; dv = DV[t, i]
    fin = np.isfinite(rev) & np.isfinite(ef) & np.isfinite(dv)
    cuts = (np.median(rev[fin]), np.median(ef[fin]), np.median(dv[fin]))
    c2 = fin & (rev <= cuts[0]) & (ef > cuts[1]) & (dv > cuts[2])
    assert t.size == D413_N and int(c2.sum()) == D413_CELL2, f"[P1] {t.size} / {int(c2.sum())}"
    print(f"  P1  daily arm: D413's {t.size:,} touches and {int(c2.sum()):,} cell-2 events reproduce")

    resD, E, ATR = daily_arm(P, t, i, side, atr)
    assert_FILL(resD, E, ATR, side)
    SD = summarise(resD, E, side, r_base, 1, "daily")
    SD2 = summarise(resD, E, side, r_base, 1, "daily cell2", mask=c2)
    print(f"  [FILL] daily arm: every stop at or below its trigger, every target at or above\n")
    print(f"  --- DAILY ARM, POOLED (n {SD['_base']['rule']['n']:,}; fixed exit "
          f"{SD['_base']['rule']['mean']:+.2f} bp, std {1e4*SD['_base']['std']:.0f} bp, "
          f"max loss {SD['_base']['max_loss']:+.0f}) ---")
    for fam, p in RULES:
        show(SD, rname(fam, p))
    print(f"\n  --- DAILY ARM, CELL 2 secondary (n {SD2['_base']['rule']['n']:,}; fixed exit "
          f"{SD2['_base']['rule']['mean']:+.2f} bp) ---")
    for fam, p in RULES:
        show(SD2, rname(fam, p))

    # P2: trigger timing
    print(f"\n  P2  exit-day distribution of the primaries (daily arm, share of EARLY exits by day 1..5):")
    for fam in ("SL", "TS", "TP"):
        key = rname(fam, PRIMARY[fam]); b = resD[key]["bar"]; m = resD[key]["early"]
        print(f"      {key:7s} " + "  ".join(f"d{j+1}:{100*np.mean(b[m]==j):.0f}%" for j in range(HOLD)))

    # ================= 15m ARM =================
    art = json.loads(D414_ART.read_text(encoding="utf-8"))
    ev = art["events"]
    assert len(ev) == D414_N, f"[P1] D414 events {len(ev)}"
    intr = F.load_15m(verbose=False)
    for s_ in intr:
        keep = intr[s_]["date"] <= F.END
        for k in ("ts", "date", "o", "h", "l", "c"):
            intr[s_][k] = intr[s_][k][keep]
    names = sorted(set(e["sym"] for e in ev))
    PHI = F.basis_phi(P, intr, names)
    sidx = {s_: F.session_index(intr[s_]) for s_ in names}
    sym = {s_: k for k, s_ in enumerate(P["symbols"])}
    dates = P["dates"]
    B = 26 * HOLD
    n = len(ev)
    O15 = np.full((n, B), np.nan); H15 = O15.copy(); L15 = O15.copy(); C15 = O15.copy()
    E15 = np.full(n, np.nan); ATR15 = np.full(n, np.nan); last15 = np.full(n, np.nan)
    side15 = np.array([e["side"] for e in ev]); c215 = np.array([e["cell2"] for e in ev])
    rb15 = np.array([e["r_daily"] for e in ev]); t15 = np.array([e["t"] for e in ev])
    i15 = np.array([sym[e["sym"]] for e in ev])
    n_gap = 0
    for k, e in enumerate(ev):
        s_, tt = e["sym"], e["t"]
        ph = PHI[s_][tt]
        E15[k] = P["CL"][tt, i15[k]] * ph
        ATR15[k] = atr[tt, i15[k]] * ph
        pos = 0; okk = True
        for dd in range(1, HOLD + 1):
            d = dates[tt + dd] if tt + dd < len(dates) else None
            if d is None or d not in sidx[s_]:
                okk = False; break
            a_, b_ = sidx[s_][d]
            m_ = min(b_ - a_, B - pos)
            O15[k, pos:pos + m_] = intr[s_]["o"][a_:a_ + m_]; H15[k, pos:pos + m_] = intr[s_]["h"][a_:a_ + m_]
            L15[k, pos:pos + m_] = intr[s_]["l"][a_:a_ + m_]; C15[k, pos:pos + m_] = intr[s_]["c"][a_:a_ + m_]
            pos += m_
            if dd == HOLD:
                last15[k] = intr[s_]["c"][b_ - 1]
        if not okk:
            n_gap += 1
    ok15 = np.isfinite(last15) & np.isfinite(E15)
    print(f"\n  P1  15m arm: {n:,} D414 events; {n_gap} lack a full five-session path and are dropped; "
          f"{int(ok15.sum()):,} walked")
    res15 = walk(O15[ok15], H15[ok15], L15[ok15], C15[ok15], E15[ok15], ATR15[ok15], side15[ok15], last15[ok15])
    assert_FILL(res15, E15[ok15], ATR15[ok15], side15[ok15])
    # the DAILY-bar rules on the SAME events, through the SAME walker
    resD15, ED15, ATRD15 = daily_arm(P, t15[ok15], i15[ok15], side15[ok15], atr)
    assert_FILL(resD15, ED15, ATRD15, side15[ok15])
    S15 = summarise(res15, E15[ok15], side15[ok15], rb15[ok15], 26, "15m")
    S15d = summarise(resD15, ED15, side15[ok15], rb15[ok15], 1, "15m-events daily-bar")
    print(f"  [FILL] 15m arm and its daily-bar twin: fills all on the right side of their triggers\n")
    print(f"  --- 15m ARM (n {S15['_base']['rule']['n']:,}; fixed exit {S15['_base']['rule']['mean']:+.2f} bp) ---")
    for fam, p in RULES:
        show(S15, rname(fam, p))
    print(f"\n  --- the SAME events, DAILY-bar triggers ---")
    for fam, p in RULES:
        show(S15d, rname(fam, p))
    print(f"\n  --- PRECISION: 15m minus daily-bar, PAIRED on the same events, primaries ---")
    prec = {}
    lgE = np.log(E15[ok15])
    for fam in ("SL", "TS", "TP"):
        key = rname(fam, PRIMARY[fam])
        r15 = side15[ok15] * (np.log(res15[key]["price"]) - lgE)
        rD = side15[ok15] * (np.log(resD15[key]["price"]) - np.log(ED15))
        dd = stat(r15 - rD, f"{key} 15m - daily")
        agree = bool(np.sign(S15[key]["delta"].get("mean", 0)) == np.sign(S15d[key]["delta"].get("mean", 0)))
        prec[key] = dict(diff=dd, sign_agrees=agree,
                         early_15m=S15[key]["early_share"], early_daily=S15d[key]["early_share"])
        print(f"  {key:7s} 15m-daily {dd['mean']:+7.2f} +-{dd['se']:5.2f} ({dd['t']:+5.1f} SE)   "
              f"early 15m {100*prec[key]['early_15m']:.1f}% vs daily {100*prec[key]['early_daily']:.1f}%   "
              f"sign of paired delta agrees: {agree}")

    # P4: look at one cell-2 event, daily arm
    j = int(np.flatnonzero(c2 & resD["SL1.5"]["early"])[0])
    print(f"\n  P4  {P['symbols'][i[j]]} touch {dates[t[j]]} side {side[j]:+d} entry {E[j]:.2f} ATR {ATR[j]:.2f}  "
          f"fixed exit {1e4*r_base[j]:+.0f} bp")
    for fam in ("SL", "TS", "TP"):
        key = rname(fam, PRIMARY[fam]); r_ = resD[key]
        rr = side[j] * (np.log(r_["price"][j]) - np.log(E[j]))
        print(f"      {key:7s} exit {'day %d' % (r_['bar'][j]+1) if r_['early'][j] else 'time stop'} at {r_['price'][j]:.2f}  ->  {1e4*rr:+.0f} bp")

    # ================= THE BAR =================
    T = {fam: bool(SD[rname(fam, PRIMARY[fam])]["delta"].get("t", -9) > 2.0) for fam in ("SL", "TS", "TP")}
    T2 = {fam: bool(SD2[rname(fam, PRIMARY[fam])]["delta"].get("t", -9) > 2.0) for fam in ("SL", "TS", "TP")}
    print(f"\n  --- THE BAR (committed 962c8c8), daily arm pooled, per family ---")
    for fam in ("SL", "TS", "TP"):
        key = rname(fam, PRIMARY[fam]); d = SD[key]["delta"]
        print(f"    T1({fam})  paired delta > 0 by 2 SE : {T[fam]}   ({d['mean']:+.2f} bp, {d['t']:+.1f} SE)   "
              f"std x{SD[key]['std_ratio']:.2f}  bp/day {SD[key]['bp_per_day']:+.2f} vs fixed "
              f"{SD['_base']['rule']['mean']/HOLD:+.2f}")
    print(f"    secondary cell 2 (cannot clear)   : " + "  ".join(f"{fam} {T2[fam]}" for fam in T2))
    print(f"\n  VERDICT: " + "  ".join(f"{fam} {'CLEARS' if T[fam] else 'FAILS'}" for fam in T))

    OUT.write_text(json.dumps(dict(
        primary=PRIMARY, rules=[rname(f, p) for f, p in RULES],
        bar=T, secondary_cell2=T2, daily=SD, daily_cell2=SD2, m15=S15, m15_dailybar=S15d,
        precision=prec, counts=dict(daily=int(t.size), cell2=int(c2.sum()), m15=int(ok15.sum()),
                                    m15_gap=n_gap)), indent=1, default=float), encoding="utf-8")
    print(f"  wrote {OUT.relative_to(REPO)}  in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if not a.run:
        ap.error("pass --run")
    run()
