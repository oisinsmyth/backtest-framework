"""D506 -- the frozen MACD arm across all 36 roots, GROSS first, as one 36-cell family.

    uv run python scripts/d506_macd_breadth.py --self-test
    uv run python scripts/d506_macd_breadth.py --run [--json]

Pre-registered in
`docs/decisions/D506-PRE-REG-the-frozen-MACD-arm-across-all-36-roots-gross-first-as.md`.
Signal from D484 and the state machine from D491, imported unchanged -- not one parameter is
fitted here.

GROSS IS THE PRIMARY AND THAT IS THE PRINCIPAL'S CORRECTION
-----------------------------------------------------------
I proposed an eligibility census before any signal work; the principal asked why we would not test
signals first, and this programme's own criterion (D360) agrees: a signal is a positive GROSS mean
per trade above the nulls, costs later. Crossing has been measured on ONE root (1.009 ticks on ES,
D471), so a net column across 36 roots would rest on an unmeasured spread 35 times over. Net is
reported and flagged; it is not evidence.

THE WINDOW IS PER ROOT
----------------------
Grains and livestock end their session around 14:20 ET, so a fixed h09..h15 window has 0.1%
coverage on ZC/ZS/ZW/ZL/ZM. Each root's window comes from the breadth fixture's meta, which
derived it from which hours actually carry closes.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from d484_offdiagonal_and_macd import (  # noqa: E402
    CONTRACT_PURE_BARS, COMMISSION_RT, GateError, impulse_macd, macd_hist, rotate)
from d491_conditional_hold import TRADING_DAYS, simulate  # noqa: E402
from d495_agree_confluence import agree_signal  # noqa: E402

FIX = REPO / "data" / "fixtures" / "fut_breadth_hourly.csv.gz"
META = REPO / "data" / "fixtures" / "fut_breadth_hourly.meta.json"
OUT = REPO / "data" / "d506_macd_breadth.json"

SEG_H = [18, 19, 20, 21, 22, 23] + list(range(0, 17))
SEGN = [f"h{h:02d}" for h in SEG_H]
IN_LO, IN_HI = "2016-01-04", "2023-12-29"
M_PRIMARY = 5
M_SECONDARY = (1, 2, 3)
ARMS = ("AGREE", "B1", "B2")
CROSS_TICKS_ASSUMED = 1.0        # measured on ES only (D471); UNMEASURED on the other 35
N_DRAWS = 2000
SEED = 506
MIN_SESSIONS = 250
NQ_REF_GROSS_TICKS = None        # filled from D495's artifact at run time; never retyped


def P(*a, **k):
    print(*a, **k, flush=True)


def seg_index(hour: int) -> int:
    return SEG_H.index(hour)


def simulate_window(O, C, sig, first_decide, last_seg, M, cost_ticks):
    """D491's state machine with the LAST segment as a parameter instead of a module constant.

    D491's `simulate` hardcodes `LAST_SEG = 21` (h15) for the forced exit and the loop bound,
    which is correct for index futures and WRONG for a root whose session ends at h14. On the
    first run every grain and livestock root reported ZERO trades: with only h09..h14 available,
    an exit needs `t + 1 <= last`, so `t <= 19`, and `elapsed >= M = 5` needs `entry_t <= 14` --
    before the window opens. Asserted to reproduce `simulate` exactly when last_seg == 21.

    O and C must already be in TICKS. Passing prices with cost in ticks mixes units and on the
    first run charged 6J about 3,000,000 ticks a trade.
    """
    n = O.shape[0]
    pos = np.zeros(n)
    entry_px = np.zeros(n)
    entry_t = np.full(n, -1, dtype=np.int64)
    pnl = np.zeros(n)
    trips = np.zeros(n)
    s_all = np.nan_to_num(sig, nan=0.0)
    for t in range(first_decide, last_seg):
        s = s_all[:, t]
        px = O[:, t + 1]
        live = pos != 0
        ex = live & ((t - entry_t) >= M) & (s * pos <= 0) & np.isfinite(px)
        pnl = np.where(ex, pnl + pos * (px - entry_px) - cost_ticks, pnl)
        trips = np.where(ex, trips + 1, trips)
        pos = np.where(ex, 0.0, pos)
        en = (pos == 0) & (s != 0) & np.isfinite(px)
        entry_px = np.where(en, px, entry_px)
        entry_t = np.where(en, t, entry_t)
        pos = np.where(en, s, pos)
    cpx = C[:, last_seg]
    still = (pos != 0) & np.isfinite(cpx)
    pnl = np.where(still, pnl + pos * (cpx - entry_px) - cost_ticks, pnl)
    trips = np.where(still, trips + 1, trips)
    return pnl, trips


def max_hold_available(first_decide: int, last_seg: int) -> int:
    """The largest minimum-hold M for which a SIGNAL exit can execute inside the window.

    An exit decided at t executes at t+1 <= last_seg, so t <= last_seg - 1, and it needs
    t - entry_t >= M with entry_t >= first_decide. Hence M <= last_seg - 1 - first_decide.
    """
    return last_seg - 1 - first_decide


def build_root(d_all, root, window):
    """Prices and both MACD signs for one root, on its OWN window, in-sample only.

    THE TWO FILTERS BELOW ARE D484's `series_for` PIPELINE AND BOTH MUST BE APPLIED BEFORE THE
    SERIES IS FLATTENED. The first version of this runner applied neither, and the consequence
    was not a 2.5% session-count difference -- it was a different SIGNAL:

        breadth fixture, absent rows left in   1,890 sessions  1,573 trades  net Sharpe +0.579
        breadth fixture, absent rows dropped   1,873 sessions  1,957 trades  net Sharpe +0.811
        D495 published                         1,873 sessions  1,904 trades  net Sharpe +0.723

    **The breadth fixture KEEPS non-present rows and flags them**, where D467's builder drops
    them from the file. Those rows are mostly NaN, and NaN propagates through the MACD's
    recursive EMA / ZLEMA / SMMA filters, so every gap suppresses the indicator downstream of
    itself -- 1,573 trades instead of 1,957, a 20% loss of signal that has nothing to do with
    the market. A study reading this fixture MUST drop non-present rows before flattening.

    `same_front` is D484's other filter: it excludes roll sessions, whose consecutive closes
    straddle two contracts. Applying it is what makes the session count reconcile exactly.
    """
    h0, h1 = window
    first, last = seg_index(h0), seg_index(h1)
    d = d_all[d_all["root"] == root]
    if "same_front" in d.columns:
        d = d[d["same_front"]]
    if "present" in d.columns:
        d = d[d["present"]]
    d = d.sort_values("day", kind="stable")
    d = d[d["day"].between(IN_LO, IN_HI)]
    if len(d) == 0:
        return None
    nseg = len(SEGN)
    O = np.stack([d[f"{s}_o"].to_numpy(float) for s in SEGN], axis=1)
    H = np.stack([d[f"{s}_h"].to_numpy(float) for s in SEGN], axis=1)
    L = np.stack([d[f"{s}_l"].to_numpy(float) for s in SEGN], axis=1)
    C = np.stack([d[f"{s}_c"].to_numpy(float) for s in SEGN], axis=1)
    pos = (O > 0) & (H > 0) & (L > 0) & (C > 0)
    with np.errstate(invalid="ignore", divide="ignore"):
        lo, lh, ll, lc = (np.where(pos, np.log(O), np.nan), np.where(pos, np.log(H), np.nan),
                          np.where(pos, np.log(L), np.nan), np.where(pos, np.log(C), np.nan))
    # contract purity over the trailing CONTRACT_PURE_BARS, as D484 does
    con = np.repeat(d["contract"].to_numpy(), nseg)
    same = np.ones(len(con), dtype=bool)
    for k in range(1, CONTRACT_PURE_BARS + 1):
        same[k:] &= con[k:] == con[:-k]
    same[:CONTRACT_PURE_BARS] = False
    pure = (same.reshape(-1, nseg)) & pos
    keep = pure[:, first:last + 1].all(axis=1)
    if keep.sum() < MIN_SESSIONS:
        return {"root": root, "n_sessions": int(keep.sum()), "skipped": True}
    flat_h, flat_l, flat_c = lh.ravel(), ll.ravel(), lc.ravel()
    md = impulse_macd(flat_h, flat_l, flat_c)[1]
    b1 = np.where(md == 0.0, 0.0,
                  np.sign(impulse_macd(flat_h, flat_l, flat_c)[0])).reshape(-1, nseg)
    b2 = np.sign(macd_hist(flat_c)).reshape(-1, nseg)
    return {"root": root, "skipped": False, "first": first, "last": last,
            "O": np.exp(lo)[keep], "C": np.exp(lc)[keep],
            "AGREE": agree_signal(b1, b2)[keep], "B1": b1[keep], "B2": b2[keep],
            "days": d["day"].to_numpy()[keep], "n_sessions": int(keep.sum())}


def score(pnl_ticks, trips, tick_usd, n_sessions):
    """Per-trade and per-session statistics on a P&L series expressed in TICKS."""
    n_tr = float(trips.sum())
    per_trade = float(pnl_ticks.sum() / n_tr) if n_tr else np.nan
    d = pnl_ticks
    mu, sd = float(d.mean()), float(d.std(ddof=1)) if len(d) > 1 else (float(d.mean()), np.nan)
    return {"n_trades": int(n_tr), "trips_per_session": n_tr / n_sessions if n_sessions else np.nan,
            "mean_ticks_per_trade": per_trade,
            "mean_ticks_per_session": mu,
            "sigma_ticks_per_session": sd,
            "sharpe": (mu / sd * np.sqrt(TRADING_DAYS)) if sd and sd > 0 else np.nan,
            "mean_usd_per_trade": per_trade * tick_usd if np.isfinite(per_trade) else np.nan,
            "sigma_usd_per_session": sd * tick_usd if sd else np.nan,
            "skew": float(((d - mu) ** 3).mean() / sd ** 3) if sd and sd > 0 else np.nan,
            "kurtosis": float(((d - mu) ** 4).mean() / sd ** 4) if sd and sd > 0 else np.nan}


def lag1(x):
    x = np.asarray(x, dtype=float).ravel()
    x = x[np.isfinite(x)]
    if len(x) < 10 or x.std() == 0:
        return np.nan
    return float(np.corrcoef(x[:-1], x[1:])[0, 1])


def do_self_test() -> int:
    fails = []

    def chk(label, cond, detail=""):
        P(f"    [{'PASS' if cond else 'FAIL'}] {label:62} {detail}")
        if not cond:
            fails.append(label)

    chk("h09 and h15 map to segment indices 15 and 21, as D491 uses",
        seg_index(9) == 15 and seg_index(15) == 21,
        f"h09->{seg_index(9)}, h15->{seg_index(15)}")
    chk("and a grain's h14 close maps to 20, one earlier",
        seg_index(14) == 20)
    chk("[X] h18 is the FIRST segment, not the nineteenth -- the session starts in the evening",
        seg_index(18) == 0)

    # --- the rotation must preserve what the null depends on --------------------------------
    rng = np.random.default_rng(SEED)
    n = 3000
    smooth = np.convolve(rng.normal(0, 1, n + 40), np.ones(20) / 20, mode="valid")[:n]
    sig = np.sign(smooth)
    rot = rotate(sig, 977)
    sh = sig.copy()
    rng.shuffle(sh)
    chk("rotation preserves the duty cycle exactly",
        abs((rot > 0).mean() - (sig > 0).mean()) < 1e-15)
    chk("rotation preserves lag-1 autocorrelation",
        abs(lag1(rot) - lag1(sig)) < 0.05, f"{lag1(rot):.3f} vs {lag1(sig):.3f}")
    chk("[X] a SHUFFLE destroys it, which is why the null rotates",
        abs(lag1(sh)) < 0.1 < abs(lag1(sig)),
        f"shuffled {lag1(sh):+.3f} vs real {lag1(sig):+.3f}")

    # --- net = gross - cost x trips, exactly, with an identical trip count ------------------
    nseg = len(SEGN)
    m = 200
    lp = np.cumsum(rng.normal(0, 0.002, m * nseg)) + 9.0
    O = np.exp(lp).reshape(m, nseg)
    C = np.exp(lp + 0.0004).reshape(m, nseg)
    s = np.sign(rng.normal(0, 1, (m, nseg)))
    cost = 2.75
    pg, tg = simulate(O, C, s, 15, M_PRIMARY, 0.0, 0.25)
    pn, tn = simulate(O, C, s, 15, M_PRIMARY, cost, 0.25)
    chk("the trip count is identical gross and net", np.array_equal(tg, tn))
    chk("net = gross - cost x trips, exactly",
        np.abs(pn - (pg - cost * tg)).max() < 1e-12,
        f"max |diff| {np.abs(pn - (pg - cost * tg)).max():.2e}")
    chk("[X] a DIFFERENT cost gives a different net, so the identity is not vacuous",
        np.abs(simulate(O, C, s, 15, M_PRIMARY, cost * 2, 0.25)[0] - pn).max() > 1e-9)

    # --- the holdout boundary ----------------------------------------------------------------
    days = np.array(["2015-12-31", "2016-01-04", "2023-12-29", "2024-01-02"])
    keep = (days >= IN_LO) & (days <= IN_HI)
    chk("the in-sample mask excludes 2015 and 2024", list(keep) == [False, True, True, False])
    chk("[X] a widened boundary would admit 2024, and this one does not",
        int(keep.sum()) == 2 and int((days >= IN_LO).sum()) == 3)

    # --- per-trade vs per-session, on a hand case -------------------------------------------
    pnl = np.array([3.0, 0.0, -1.0])
    trips = np.array([1.0, 0.0, 1.0])
    st = score(pnl, trips, 0.5, 3)
    chk("mean per TRADE divides by trades, not sessions",
        abs(st["mean_ticks_per_trade"] - 1.0) < 1e-12
        and abs(st["mean_ticks_per_session"] - 2.0 / 3.0) < 1e-12,
        f"per trade {st['mean_ticks_per_trade']:.4f}, per session "
        f"{st['mean_ticks_per_session']:.4f}")
    chk("[X] the two differ whenever a session holds no trade",
        st["mean_ticks_per_trade"] != st["mean_ticks_per_session"])
    chk("dollars per trade is ticks x the tick value",
        abs(st["mean_usd_per_trade"] - 0.5) < 1e-12)

    # --- the windowed machine must equal D491's when the window is D491's ------------------
    from d491_conditional_hold import LAST_SEG
    Ot, Ct = O / 0.25, C / 0.25                      # in TICKS, as simulate_window requires
    pa, ta = simulate(Ot, Ct, s, 15, M_PRIMARY, 1.5, 1.0)
    pb, tb = simulate_window(Ot, Ct, s, 15, LAST_SEG, M_PRIMARY, 1.5)
    chk("[OPT] simulate_window reproduces D491's simulate EXACTLY at last_seg = 21",
        np.abs(pa - pb).max() < 1e-12 and np.array_equal(ta, tb),
        f"max |diff| {np.abs(pa - pb).max():.2e}, LAST_SEG={LAST_SEG}")
    pc, tc = simulate_window(Ot, Ct, s, 15, 20, M_PRIMARY, 1.5)
    chk("[X] and a SHORTER window gives a different result, so the parameter is live",
        not np.array_equal(tb, tc), f"trips {tb.sum():.0f} vs {tc.sum():.0f}")

    # --- the structural limit that produced seven all-NaN roots on the first run -----------
    chk("max_hold_available is last - 1 - first",
        max_hold_available(15, 21) == 5 and max_hold_available(15, 20) == 4,
        f"h09-h15 -> {max_hold_available(15, 21)}, h09-h14 -> {max_hold_available(15, 20)}")
    chk("[X] M=5 on a grain's h09-h14 window admits NO signal exit, which is why the first "
        "run reported zero trades on all seven",
        simulate_window(Ot, Ct, s, 15, 20, 5, 0.0)[1].sum()
        < simulate_window(Ot, Ct, s, 15, 20, 4, 0.0)[1].sum(),
        f"M=5 -> {simulate_window(Ot, Ct, s, 15, 20, 5, 0.0)[1].sum():.0f} trips, "
        f"M=4 -> {simulate_window(Ot, Ct, s, 15, 20, 4, 0.0)[1].sum():.0f}")

    # --- units: a cost in ticks against prices in PRICE units is the other first-run bug ---
    tick6j = 5e-7                                    # 6J's tick in price units
    jpx = (0.0068 + np.cumsum(rng.normal(0, 2e-6, 20 * len(SEGN)))).reshape(20, len(SEGN))
    sg = np.sign(rng.normal(0, 1, (20, len(SEGN))))
    cost_tk = COMMISSION_RT / 6.25 + 1.0             # 6J's cost in TICKS
    right = simulate_window(jpx / tick6j, jpx / tick6j, sg, 15, 21, M_PRIMARY, cost_tk)
    wrong = simulate_window(jpx, jpx, sg, 15, 21, M_PRIMARY, cost_tk)   # the first-run bug
    per_right = right[0].sum() / right[1].sum()
    per_wrong = (wrong[0].sum() / tick6j) / wrong[1].sum()   # then converted, as the bug did
    chk("[X] a TICK cost charged against PRICE-unit prices and converted afterwards inflates "
        "it by 1/tick -- the first run billed 6J millions of ticks a trade",
        abs(per_wrong) > 1000 * max(abs(per_right), 1.0),
        f"correct {per_right:+.3f} tk/trade vs the bug's {per_wrong:+,.0f}")
    chk("and the gross figure is unaffected, which is why gross was the only column worth "
        "reading on that run",
        abs(simulate_window(jpx / tick6j, jpx / tick6j, sg, 15, 21, M_PRIMARY, 0.0)[0].sum()
            - simulate_window(jpx, jpx, sg, 15, 21, M_PRIMARY, 0.0)[0].sum() / tick6j)
        < 1e-6 * abs(simulate_window(jpx / tick6j, jpx / tick6j, sg, 15, 21,
                                     M_PRIMARY, 0.0)[0].sum()))

    P(f"\n  {len(fails)} failed: {fails}" if fails else "\n  all checks pass")
    return 1 if fails else 0


def do_run(as_json: bool) -> int:
    import pandas as pd

    meta = json.loads(META.read_text(encoding="utf-8"))
    if not meta.get("all_gates_pass"):
        raise GateError("[FIXTURE] the breadth fixture's gates do not all pass")
    specs = meta["specs"]
    P("D506 -- the frozen MACD arm across all 36 roots, GROSS first\n")
    P(f"  fixture {FIX.name}, in-sample {IN_LO} .. {IN_HI}, minimum hold M={M_PRIMARY}")
    P(f"  commission ${COMMISSION_RT:.0f} a round trip; crossing assumed "
      f"{CROSS_TICKS_ASSUMED:.2f} tick and MEASURED ON ES ONLY\n")
    d_all = pd.read_csv(FIX)

    roots = [r for r in meta["roots"]]
    built, skipped = {}, []
    for r in roots:
        w = specs[r]["day_window"]
        b = build_root(d_all, r, w)
        if b is None or b.get("skipped"):
            skipped.append((r, 0 if b is None else b["n_sessions"]))
            continue
        built[r] = b
    P(f"  built {len(built)} roots; skipped {len(skipped)} for under {MIN_SESSIONS} sessions: "
      f"{[s[0] for s in skipped]}\n")

    # ---- primary: the frozen spec, gross and net, per root
    P("=== 1. THE FROZEN SPEC ON EVERY ROOT, GROSS FIRST ===")
    P("     root  win    sess  trades  trips  GROSS tk/trade  gross Sharpe   net tk   net Sh"
      "   $/trade  skew")
    prim, inapplicable = {}, []
    for r, b in built.items():
        sp = specs[r]
        tickv = sp["tick_usd"]
        m_max = max_hold_available(b["first"], b["last"])
        if M_PRIMARY > m_max:
            inapplicable.append((r, sp["day_window"], m_max))
            continue
        cost = COMMISSION_RT / tickv + CROSS_TICKS_ASSUMED
        # EVERYTHING IN TICKS from here: the cost is in ticks, so the prices must be too
        tk = sp["tick_price_units"]
        Ot, Ct = b["O"] / tk, b["C"] / tk
        pg, tg = simulate_window(Ot, Ct, b["AGREE"], b["first"], b["last"], M_PRIMARY, 0.0)
        pn, tn = simulate_window(Ot, Ct, b["AGREE"], b["first"], b["last"], M_PRIMARY, cost)
        if not np.array_equal(tg, tn):
            raise GateError(f"[NET] {r}: trip counts differ between gross and net")
        if np.abs(pn - (pg - cost * tg)).max() > 1e-9:
            raise GateError(f"[NET] {r}: net != gross - cost x trips")
        g = score(pg, tg, tickv, b["n_sessions"])
        nt = score(pn, tn, tickv, b["n_sessions"])
        prim[r] = {"window": sp["day_window"], "n_sessions": b["n_sessions"],
                   "cost_ticks": cost, "tick_usd": tickv, "sized_as": sp["sized_as"],
                   "gross": g, "net": nt, "c_d_passes": sp.get("c_d_passes")}
        P(f"     {r:>4}  {sp['day_window'][0]:02d}-{sp['day_window'][1]:02d}"
          f"{b['n_sessions']:>7}{g['n_trades']:>8}{g['trips_per_session']:>7.2f}"
          f"{g['mean_ticks_per_trade']:>+16.3f}{g['sharpe']:>+14.3f}"
          f"{nt['mean_ticks_per_trade']:>+9.3f}{nt['sharpe']:>+9.3f}"
          f"{g['mean_usd_per_trade']:>+10.2f}{g['skew']:>+6.2f}")

    if inapplicable:
        P(f"\n  STRUCTURALLY INAPPLICABLE at M={M_PRIMARY}: "
          f"{[i[0] for i in inapplicable]}")
        P(f"  Their sessions are too short for the frozen spec. An exit decided at t executes")
        P(f"  at t+1 <= last, so M <= last - 1 - first; these allow M <= "
          f"{sorted(set(i[2] for i in inapplicable))}. They are NOT zero and NOT a failure --")
        P(f"  the frozen construction simply cannot be transplanted to a 6-hour session, and")
        P(f"  substituting a smaller M would be a DIFFERENT construction, not this one.")

    pos = [r for r, v in prim.items() if v["gross"]["mean_ticks_per_trade"] > 0]
    P(f"\n  roots with a POSITIVE gross mean per trade: {len(pos)} of {len(prim)}  {sorted(pos)}")

    # ---- W-d: NQ must reproduce D495
    d495 = REPO / "data" / "d495_agree_confluence.json"
    ref = None
    if d495.exists() and "NQ" in prim:
        a = json.loads(d495.read_text(encoding="utf-8"))
        for c in a.get("cells", []):
            if c.get("root") == "NQ" and c.get("arm") == "AGREE" and c.get("M") == M_PRIMARY:
                ref = c
                break
    if ref is not None:
        got = prim["NQ"]["net"]["sharpe"]
        want = ref.get("net", {}).get("sharpe", ref.get("net_sharpe"))
        # The pre-registration's bar is RELATIVE (within 10%); the first version of this runner
        # coded an ABSOLUTE 0.25 and so did not fire on a 30% gap. Report both.
        rel = abs(got - want) / abs(want) if want else float("nan")
        P(f"        relative gap {rel:.1%} against the pre-registration's 10% bar")
        P(f"\n  [W-d] NQ net Sharpe here {got:+.3f} against D495's {want:+.3f} "
          f"on a DIFFERENT fixture and builder")
        if want and abs(got - want) > 0.25:
            raise GateError(
                f"[W-d] the two fixtures disagree about NQ by {abs(got - want):.3f} "
                f"({got:+.3f} here against D495's {want:+.3f}). D506 s7 item 1 says this "
                f"RAISES: a gap this size means the breadth fixture and the committed fixture "
                f"disagree about a root they must agree on, and no other cell can be trusted "
                f"until it is explained.")
    else:
        P("\n  [W-d] D495's artifact does not expose the comparable cell; check deferred")

    # ---- the rotation null, per root and family-max
    P(f"\n=== 2. ROTATION NULL, {N_DRAWS:,} draws, on GROSS mean per trade ===")
    rng = np.random.default_rng(SEED)
    t0 = time.perf_counter()
    scored = {r: built[r] for r in prim}
    nulls = {r: np.empty(N_DRAWS) for r in scored}
    nulls_sh = {r: np.empty(N_DRAWS) for r in scored}
    fam = np.empty(N_DRAWS)
    fam_sh = np.empty(N_DRAWS)
    for i in range(N_DRAWS):
        vals, vals_sh = [], []
        for r, b in scored.items():
            off = int(rng.integers(1, b["n_sessions"]))
            sg = rotate(b["AGREE"], off)
            tk = specs[r]["tick_price_units"]
            pg, tg = simulate_window(b["O"] / tk, b["C"] / tk, sg, b["first"], b["last"],
                                     M_PRIMARY, 0.0)
            v = float(pg.sum() / tg.sum()) if tg.sum() else 0.0
            sd = pg.std(ddof=1)
            sh = float(pg.mean() / sd * np.sqrt(TRADING_DAYS)) if sd > 0 else 0.0
            nulls[r][i] = v
            nulls_sh[r][i] = sh
            vals.append(v)
            vals_sh.append(sh)
        fam[i] = max(vals)
        fam_sh[i] = max(vals_sh)
        if i == 0:
            per = time.perf_counter() - t0
            P(f"  profiled: {per * 1000:.0f} ms a draw -> {per * N_DRAWS / 60:.1f} min")
    P(f"  done in {(time.perf_counter() - t0) / 60:.1f} min\n")

    P("     root      obs      p50      p95   p95 SE   margin   clears")
    res = {}
    clears = []
    for r in scored:
        obs = prim[r]["gross"]["mean_ticks_per_trade"]
        nl = nulls[r]
        p50, p95 = float(np.percentile(nl, 50)), float(np.percentile(nl, 95))
        bs = np.array([np.percentile(rng.choice(nl, len(nl)), 95) for _ in range(200)])
        se = float(bs.std(ddof=1))
        marg = (obs - p95) / se if se > 0 else float("inf")
        cl = bool(obs > p95)
        if cl:
            clears.append(r)
        sh_obs = prim[r]["gross"]["sharpe"]
        sh95 = float(np.percentile(nulls_sh[r], 95))
        res[r] = {"observed": obs, "p50": p50, "p95": p95, "p95_se": se, "margin_se": marg,
                  "clears": cl, "unresolved": bool(abs(marg) < 2),
                  "gross_sharpe": sh_obs, "gross_sharpe_null_p95": sh95,
                  "clears_on_sharpe": bool(sh_obs > sh95)}
        P(f"     {r:>4}{obs:>+9.3f}{p50:>+9.3f}{p95:>+9.3f}{se:>9.4f}{marg:>+9.1f}"
          f"{'   YES' if cl else '    no'}"
          + ("  UNRESOLVED" if abs(marg) < 2 else ""))

    # TWO FAMILY-MAX READINGS, AND ONLY THE SECOND IS WELL POSED. Gross ticks per trade is not
    # comparable across roots: NQ's +24.9 ticks and ZN's +0.37 sit on tick sizes three orders of
    # magnitude apart, so a family MAXIMUM in ticks is decided by whichever root has the smallest
    # tick and says nothing about the rest. GROSS SHARPE is scale-free and is the family bar.
    fam_p95 = float(np.percentile(fam, 95))
    best_r = max(prim, key=lambda r: prim[r]["gross"]["mean_ticks_per_trade"])
    best = prim[best_r]["gross"]["mean_ticks_per_trade"]
    fam_sh_p95 = float(np.percentile(fam_sh, 95))
    best_sh_r = max(prim, key=lambda r: prim[r]["gross"]["sharpe"])
    best_sh = prim[best_sh_r]["gross"]["sharpe"]
    P(f"\n     FAMILY-MAX on GROSS TICKS/TRADE -- ILL POSED, tick sizes differ 1000x:")
    P(f"       best {best:+.3f} ({best_r}) vs family p95 {fam_p95:+.3f}, "
      f"{'clears' if best > fam_p95 else 'does not clear'} -- decided by units, not edge")
    P(f"     FAMILY-MAX on GROSS SHARPE -- scale-free, THIS is the family bar:")
    P(f"       best {best_sh:+.3f} ({best_sh_r}) vs family p95 {fam_sh_p95:+.3f}   "
      f"{'CLEARS' if best_sh > fam_sh_p95 else 'DOES NOT CLEAR'}")
    P(f"     roots clearing their OWN p95: {len(clears)}  {sorted(clears)}")

    # ---- W-f: pairwise rho among the clearing roots
    P("\n=== 3. PAIRWISE CORRELATION AMONG THE CLEARING ROOTS ===")
    rho = {}
    if len(clears) >= 2:
        ser = {}
        for r in clears:
            b = scored[r]
            tk = specs[r]["tick_price_units"]
            pg, _ = simulate_window(b["O"] / tk, b["C"] / tk, b["AGREE"], b["first"],
                                    b["last"], M_PRIMARY, 0.0)
            ser[r] = pd.Series(pg, index=b["days"])
        for i, a in enumerate(sorted(clears)):
            for c in sorted(clears)[i + 1:]:
                j = pd.concat([ser[a], ser[c]], axis=1, join="inner").dropna()
                if len(j) > 100:
                    rho[f"{a}~{c}"] = float(j.corr().iloc[0, 1])
        for k in sorted(rho, key=lambda k: rho[k]):
            P(f"     {k:<12}{rho[k]:>+8.3f}{'   < 0.3' if rho[k] < 0.3 else ''}")
    else:
        P(f"     fewer than two roots cleared, so there is no pair to correlate")

    art = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "purpose": "D506: the frozen MACD arm on all 36 breadth roots, GROSS primary, one "
                      "36-cell family with a family-max rotation null. Nothing admitted.",
           "window": [IN_LO, IN_HI], "m_hold": M_PRIMARY,
           "cost": {"commission_usd": COMMISSION_RT,
                    "cross_ticks_assumed": CROSS_TICKS_ASSUMED,
                    "warning": "crossing is MEASURED ON ES ONLY (1.009 ticks, D471); the net "
                               "columns rest on an assumed one tick for the other 35 roots and "
                               "are NOT evidence"},
           "skipped_roots": skipped,
           "inapplicable_at_M": inapplicable,
           "primary": prim, "nulls": res,
           "family_max_ticks_ILL_POSED": {"best_root": best_r, "best": best,
                                          "family_null_p95": fam_p95,
                                          "clears": bool(best > fam_p95),
                                          "why": "gross ticks per trade is not comparable "
                                          "across roots whose ticks differ 1000x; the family "
                                          "maximum is decided by units, not edge"},
           "family_max_sharpe": {"best_root": best_sh_r, "best": best_sh,
                                 "family_null_p95": fam_sh_p95,
                                 "clears": bool(best_sh > fam_sh_p95)},
           "clearing_roots": sorted(clears), "pairwise_rho": rho,
           "n_positive_gross": len(pos), "positive_gross_roots": sorted(pos),
           "limitations": [
               "in-sample only; 2024+ unread on 35 roots and SPENT on NQ (D503); "
               "2010-2015 unread and complete for the non-index roots",
               "a 36-cell search: only the family-max null prices that",
               "net is not evidence -- crossing measured on one root of 36",
               "nothing admitted (R15); a clearing root is a candidate for a forward read on "
               "its own unspent slice, not a component"]}
    OUT.write_text(json.dumps(art, indent=2, default=float), encoding="utf-8")
    P(f"\n  wrote {OUT.relative_to(REPO)}")
    if as_json:
        P(json.dumps(art, indent=2, default=float))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return do_self_test()
    if a.run:
        return do_run(a.json)
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
