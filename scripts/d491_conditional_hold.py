"""D491 -- the conditional hold: exit when the signal flips, with a minimum hold time.

    uv run python scripts/d491_conditional_hold.py --self-test
    uv run python scripts/d491_conditional_hold.py --run [--json]

Pre-registered in
`docs/decisions/D491-PRE-REG-the-conditional-hold-exit-when-the-signal-flips-with-a.md`
(amended before this file existed to make B2 co-primary). **Signal code imported from D484
unchanged.**

WHY THIS DIFFERS FROM EVERYTHING BEFORE IT
------------------------------------------
D484/D486/D488 fixed the holding period, so the **trade count was an input and therefore the
bill was an input**. Here the exit keys on the signal, so **the trade count is an OUTPUT** --
and since commission is 70-86% of cost and fixed per round trip, that is the quantity that
decides everything. The minimum hold M is what stops a flickering signal paying the fee on
every flicker.

**AND IT PRODUCES A REAL P&L SERIES**, so C-a, C-c and C-d are computed directly rather than
through an edge-versus-cost proxy. No earlier record in this line produced a P&L series at all.

THE STATE MACHINE IS VECTORISED OVER SESSIONS, NOT LOOPED
---------------------------------------------------------
Sessions are independent, so the machine steps through the 23 segments with all ~2,000 sessions
updated at once: 22 vectorised operations instead of ~44,000 scalar ones. That is what makes a
2,000-draw rotation null affordable when each draw must RE-RUN the whole simulation.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from d484_offdiagonal_and_macd import (  # noqa: E402
    CROSS_TICKS, COMMISSION_RT, IN_SAMPLE, MICRO_OF, SEGMENTS, SPECS,
    impulse_macd, macd_hist, rotate, series_for,
)

FIX = REPO / "data" / "fixtures" / "fut_sessions_hourly.csv.gz"
META = REPO / "data" / "fixtures" / "fut_sessions_hourly.meta.json"
OUT = REPO / "data" / "d491_conditional_hold.json"

INDEX_ROOTS = ("ES", "NQ", "YM")
NONINDEX_ROOTS = ("ZN", "ZB", "GC", "CL", "6E")
ROOTS = INDEX_ROOTS + NONINDEX_ROOTS
M_NONINDEX = (1, 2, 3, 5, 8)                 # §1
M_INDEX = (1, 2, 3, 5)                       # §1: only a 6-hour window exists
LAST_SEG = 21                                # §2: P2, flat at the close of h15 (4pm ET)
DAY_FIRST_DECIDE = 15                        # §2: closure -- decide at h09, execute at h10
N_DRAWS = 2000                               # §4
C_A, C_C, C_D = 0.5, -0.5, 500.0             # COMPONENTS_PROP.md
TRADING_DAYS = 252
SEED = 491


class GateError(AssertionError):
    """A validation gate refused the input."""


def P(*a, **k):
    print(*a, **k, flush=True)


# ------------------------------------------------------------------ the machine

def simulate(O, C, sig, first_decide: int, M: int, cost_ticks: float, tick_pts: float):
    """§1's state machine, vectorised over sessions.

    O, C, sig : (n_sessions, 23) opens, closes, signal sign. NaN sig is treated as 0.
    Decide at the CLOSE of segment t, execute at the OPEN of t+1 -- never at the close just
    observed. Exit is evaluated BEFORE entry within a segment, so a flip closes and re-opens
    at the same price and pays two legs.

    Returns (pnl_ticks per session, round_trips per session).
    """
    n = O.shape[0]
    pos = np.zeros(n)
    entry_px = np.zeros(n)
    entry_t = np.full(n, -1, dtype=np.int64)
    pnl = np.zeros(n)
    trips = np.zeros(n)
    s_all = np.nan_to_num(sig, nan=0.0)

    for t in range(first_decide, LAST_SEG):        # execution at t+1 <= LAST_SEG
        s = s_all[:, t]
        px = O[:, t + 1]
        live = pos != 0
        # ---- EXIT: minimum hold satisfied AND the signal is no longer in our favour
        elapsed = t - entry_t
        ex = live & (elapsed >= M) & (s * pos <= 0) & np.isfinite(px)
        pnl = np.where(ex, pnl + pos * (px - entry_px) / tick_pts - cost_ticks, pnl)
        trips = np.where(ex, trips + 1, trips)
        pos = np.where(ex, 0.0, pos)
        # ---- ENTER
        en = (pos == 0) & (s != 0) & np.isfinite(px)
        entry_px = np.where(en, px, entry_px)
        entry_t = np.where(en, t, entry_t)
        pos = np.where(en, s, pos)

    # ---- FORCED EXIT at the close of the last eligible segment (P2)
    cpx = C[:, LAST_SEG]
    still = (pos != 0) & np.isfinite(cpx)
    pnl = np.where(still, pnl + pos * (cpx - entry_px) / tick_pts - cost_ticks, pnl)
    trips = np.where(still, trips + 1, trips)
    return pnl, trips


def score(pnl_ticks: np.ndarray, tick_usd: float) -> dict:
    """§3: the daily P&L series in dollars, and C-a / C-c / C-d from it."""
    d = pnl_ticks * tick_usd
    n = len(d)
    if n < 100:
        return {"n_sessions": n, "sharpe": float("nan")}
    mu, sd = float(d.mean()), float(d.std(ddof=1))
    sk = (float(((d - mu) ** 3).mean() / sd ** 3) if sd > 0 else float("nan"))
    return {"n_sessions": n, "mean_usd": mu, "daily_sigma_usd": sd,
            "sharpe": (mu / sd * np.sqrt(TRADING_DAYS)) if sd > 0 else float("nan"),
            "skew": sk, "total_usd": float(d.sum())}


# ------------------------------------------------------------------ self-test

def do_self_test() -> int:
    fails = []

    def chk(label, cond, detail=""):
        P(f"    [{'PASS' if cond else 'FAIL'}] {label:68} {detail}")
        if not cond:
            fails.append(label)

    n_seg = 23
    # a single session, price rising 1 point per segment, signal always long
    O = np.tile(np.arange(n_seg, dtype=float), (1, 1))
    C = O + 0.5
    sig = np.ones((1, n_seg))
    pnl, tr = simulate(O, C, sig, 0, M=1, cost_ticks=0.0, tick_pts=1.0)
    # enters at open of 1 (=1.0), forced exit at close of 21 (=21.5) -> +20.5 ticks, 1 trip
    chk("a permanently-long signal on a rising tape: one trip, entry to forced exit",
        abs(pnl[0] - 20.5) < 1e-9 and tr[0] == 1, f"pnl {pnl[0]:+.2f}, trips {tr[0]:.0f}")
    chk("and it pays cost ONCE per round trip",
        abs(simulate(O, C, sig, 0, 1, 3.0, 1.0)[0][0] - (20.5 - 3.0)) < 1e-9)

    # a signal that flips every segment must churn -- unless M forbids it
    alt = np.tile(np.where(np.arange(n_seg) % 2 == 0, 1.0, -1.0), (1, 1))
    _, tr1 = simulate(O, C, alt, 0, M=1, cost_ticks=0.0, tick_pts=1.0)
    _, tr5 = simulate(O, C, alt, 0, M=5, cost_ticks=0.0, tick_pts=1.0)
    _, tr8 = simulate(O, C, alt, 0, M=8, cost_ticks=0.0, tick_pts=1.0)
    chk("an alternating signal CHURNS at M=1", tr1[0] >= 10, f"{tr1[0]:.0f} trips")
    chk("THE MINIMUM HOLD SUPPRESSES IT: trips fall as M rises",
        tr1[0] > tr5[0] > tr8[0], f"M=1 {tr1[0]:.0f}, M=5 {tr5[0]:.0f}, M=8 {tr8[0]:.0f}")
    chk("and that is the whole point -- fewer trips is less commission",
        tr8[0] <= 3, f"{tr8[0]:.0f} trips at M=8")

    # DIRECTION: a short signal on a rising tape must LOSE exactly what long gains
    pl, _ = simulate(O, C, np.ones((1, n_seg)), 0, 1, 0.0, 1.0)
    ps, _ = simulate(O, C, -np.ones((1, n_seg)), 0, 1, 0.0, 1.0)
    chk("a short on a rising tape loses exactly what a long gains (sign audit)",
        abs(pl[0] + ps[0]) < 1e-9, f"long {pl[0]:+.2f}, short {ps[0]:+.2f}")

    # NO LOOK-AHEAD, as a PAIR. The first version spiked open-21 against a never-flipping
    # signal, which never executes there -- it exits at the forced close. The signal must
    # actually flip at t=20 for open-21 to be the execution price.
    flip20 = np.ones((1, n_seg))
    flip20[0, 20:] = -1.0                       # decide at close of 20 -> exit at open of 21
    base, _ = simulate(O, C, flip20, 0, 1, 0.0, 1.0)
    O2 = O.copy()
    O2[0, 21] = 1000.0
    pnl2, _ = simulate(O2, C, flip20, 0, 1, 0.0, 1.0)
    chk("execution uses the OPEN of t+1 (spiking open-21 IS felt when the signal flips at 20)",
        abs(pnl2[0] - base[0]) > 900.0, f"{base[0]:+.2f} -> {pnl2[0]:+.2f}")
    C2 = C.copy()
    C2[0, 20] = 1000.0
    pnl3, _ = simulate(O, C2, flip20, 0, 1, 0.0, 1.0)
    chk("and NOT the close of t -- spiking close-20 changes NOTHING (no look-ahead)",
        abs(pnl3[0] - base[0]) < 1e-9, f"{base[0]:+.2f} unchanged")

    # the zero state must CLOSE a position (B1's behaviour under a conditional exit)
    z = np.ones((1, n_seg))
    z[0, 10:] = 0.0
    _, trz = simulate(O, C, z, 0, M=1, cost_ticks=0.0, tick_pts=1.0)
    pz, _ = simulate(O, C, z, 0, M=1, cost_ticks=0.0, tick_pts=1.0)
    chk("a ZERO signal closes the position -- and does not re-open",
        trz[0] == 1 and abs(pz[0] - (11.0 - 1.0)) < 1e-9,
        f"{trz[0]:.0f} trip, pnl {pz[0]:+.2f} (exit at open 11)")
    chk("THE PRINCIPAL'S POINT: a zero state buys an extra exit that plain MACD never pays",
        trz[0] >= 1)

    # §2's windows
    _, tri = simulate(O, C, sig, DAY_FIRST_DECIDE, M=1, cost_ticks=0.0, tick_pts=1.0)
    pi, _ = simulate(O, C, sig, DAY_FIRST_DECIDE, 1, 0.0, 1.0)
    chk("the day-session window enters at the open of 16 and exits at the close of 21",
        abs(pi[0] - (21.5 - 16.0)) < 1e-9, f"{pi[0]:+.2f} ticks")
    chk("index M=5 leaves almost no room -- a stated limitation, not a bug",
        max(M_INDEX) + DAY_FIRST_DECIDE + 1 >= LAST_SEG,
        f"M=5 from decide-15 exits at {DAY_FIRST_DECIDE+1+5}")

    # scoring
    sc = score(np.array([1.0] * 500 + [-1.0] * 500), 1.25)
    chk("score: a zero-mean series has Sharpe 0", abs(sc["sharpe"]) < 1e-9)
    sc2 = score(np.full(500, 2.0), 1.25)
    chk("score: a constant positive series has infinite Sharpe (sd 0) -> nan, not a number",
        not np.isfinite(sc2["sharpe"]))
    rg = np.random.default_rng(1)
    d = rg.standard_normal(2000) + 0.05
    sc3 = score(d, 1.0)
    chk("score: Sharpe = mean/sd * sqrt(252)",
        abs(sc3["sharpe"] - d.mean() / d.std(ddof=1) * np.sqrt(252)) < 1e-9,
        f"{sc3['sharpe']:+.3f}")
    chk("score: skew of a symmetric series ~ 0", abs(sc3["skew"]) < 0.2,
        f"{sc3['skew']:+.3f}")
    chk("score: a left-skewed series reads NEGATIVE (C-c has teeth)",
        score(-np.abs(rg.standard_normal(4000)) ** 2, 1.0)["skew"] < -1.0)

    # costs from the committed specs
    spec = json.loads(SPECS.read_text(encoding="utf-8"))
    chk("MES cost 3.409 ticks, MNQ 7.009 -- per ROUND TRIP",
        abs(COMMISSION_RT / spec["MES"]["tick_usd"] + CROSS_TICKS - 3.409) < 1e-3
        and abs(COMMISSION_RT / spec["MNQ"]["tick_usd"] + CROSS_TICKS - 7.009) < 1e-3)

    if fails:
        P(f"\n  SELF-TEST FAILED: {fails}")
        return 1
    P("\n  SELF-TEST PASSED.")
    return 0


# ------------------------------------------------------------------ run

def do_run(as_json: bool) -> int:
    import pandas as pd

    meta = json.loads(META.read_text(encoding="utf-8"))
    spec = json.loads(SPECS.read_text(encoding="utf-8"))
    for r in ROOTS:
        g = meta["gates"].get(r)
        bad = [k for k, v in (g or {}).items()
               if isinstance(v, dict) and v.get("passes") is False]
        if g is None or bad:
            raise GateError(f"[FIXTURE] {r}: {'missing' if g is None else bad}")
    P("  RTY excluded (G2). Index roots confined to the day session by the closure.\n")

    d_all = pd.read_csv(FIX)
    nseg = len(SEGMENTS)
    panel = {}
    for r in ROOTS:
        s = series_for(r, d_all, meta)
        k = len(s["log_close"]) // nseg
        def grid(a):
            return np.exp(a[:k * nseg]).reshape(k, nseg)
        O, C = grid(s["log_open"]), grid(s["log_close"])
        Hh, Ll = grid(s["log_high"]), grid(s["log_low"])
        pure = s["pure"][:k * nseg].reshape(k, nseg)
        lc = s["log_close"][:k * nseg]
        md = impulse_macd(s["log_high"], s["log_low"], s["log_close"])[1][:k * nseg]
        b1 = np.where(md == 0.0, 0.0,
                      np.sign(impulse_macd(s["log_high"], s["log_low"],
                                           s["log_close"])[0][:k * nseg]))
        b2 = np.sign(macd_hist(s["log_close"])[:k * nseg])
        first = DAY_FIRST_DECIDE if r in INDEX_ROOTS else 0
        keep = pure[:, first:LAST_SEG + 1].all(axis=1)
        panel[r] = {"O": O[keep], "C": C[keep],
                    "B1": b1.reshape(k, nseg)[keep], "B2": b2.reshape(k, nseg)[keep],
                    "first": first, "tick_pts": spec[r]["tick_points"] if r in spec else None,
                    "micro": MICRO_OF.get(r)}
        P(f"  {r:4} {int(keep.sum()):>5} clean sessions of {k} · decide from segment {first}")

    # ---- primary: the costable roots
    cells, series_out = [], {}
    P(f"\n  PRIMARY -- ES/NQ/YM at one micro, cost charged per ROUND TRIP:")
    P(f"  {'root':>5}{'var':>4}{'M':>3}{'trips/sess':>12}{'mean $':>9}{'sigma $':>9}"
      f"{'Sharpe':>8}{'skew':>7}   {'C-a':>4}{'C-c':>4}{'C-d':>4}")
    for r in INDEX_ROOTS:
        p = panel[r]
        micro = p["micro"]
        cost = COMMISSION_RT / spec[micro]["tick_usd"] + CROSS_TICKS
        tick_usd = spec[micro]["tick_usd"]
        for var in ("B1", "B2"):
            for M in M_INDEX:
                pnl, tr = simulate(p["O"], p["C"], p[var], p["first"], M, cost,
                                   p["tick_pts"])
                sc = score(pnl, tick_usd)
                ok_a = sc["sharpe"] > C_A
                ok_c = sc["skew"] >= C_C
                ok_d = sc["daily_sigma_usd"] <= C_D
                cells.append({"root": r, "variant": var, "M": M, "micro": micro,
                              "cost_ticks": cost, "trips_per_session": float(tr.mean()),
                              **sc, "C_a": bool(ok_a), "C_c": bool(ok_c),
                              "C_d": bool(ok_d)})
                series_out[f"{r}_{var}_{M}"] = None
                P(f"  {r:>5}{var:>4}{M:>3}{tr.mean():>12.2f}{sc['mean_usd']:>9.2f}"
                  f"{sc['daily_sigma_usd']:>9.0f}{sc['sharpe']:>+8.2f}{sc['skew']:>+7.2f}"
                  f"   {'Y' if ok_a else '.':>4}{'Y' if ok_c else '.':>4}"
                  f"{'Y' if ok_d else '.':>4}")

    best = max(cells, key=lambda z: z["sharpe"] if np.isfinite(z["sharpe"]) else -9)
    obs = best["sharpe"]
    P(f"\n  family maximum net Sharpe over {len(cells)} costable cells: {obs:+.3f}  "
      f"({best['root']} {best['variant']} M={best['M']})")

    # ---- §4 null: rotate the signal and RE-RUN the machine, so the trade count is
    # preserved and the null pays a comparable bill
    rg = np.random.default_rng(SEED)
    P(f"  R1 rotation null, {N_DRAWS:,} draws (the machine is re-run on every draw) ...")
    nullmax = np.empty(N_DRAWS)
    for i in range(N_DRAWS):
        bestd = -9.0
        for r in INDEX_ROOTS:
            p = panel[r]
            micro = p["micro"]
            cost = COMMISSION_RT / spec[micro]["tick_usd"] + CROSS_TICKS
            tick_usd = spec[micro]["tick_usd"]
            ns = p["O"].shape[0]
            for var in ("B1", "B2"):
                flat = p[var].ravel()
                rot = rotate(flat, int(rg.integers(1, len(flat) - 1))).reshape(p[var].shape)
                for M in M_INDEX:
                    pnl, _ = simulate(p["O"], p["C"], rot, p["first"], M, cost,
                                      p["tick_pts"])
                    d = pnl * tick_usd
                    sd = d.std(ddof=1)
                    if sd > 0:
                        s = d.mean() / sd * np.sqrt(TRADING_DAYS)
                        bestd = max(bestd, s)
        nullmax[i] = bestd
    p50, p95 = float(np.quantile(nullmax, .50)), float(np.quantile(nullmax, .95))
    boot = np.array([np.quantile(rg.choice(nullmax, len(nullmax), replace=True), .95)
                     for _ in range(400)])
    se = float(boot.std(ddof=1))
    marg = (obs - p95) / se
    signal = bool(marg > 2)
    P(f"  null family-max: p50 {p50:+.3f}  p95 {p95:+.3f}  (SE {se:.3f})  "
      f"-> margin {marg:+.1f} SE")
    cand = bool(signal and best["C_a"] and best["C_c"] and best["C_d"])
    P(f"\n  **SIGNAL: {'YES' if signal else 'no'} · "
      f"COMPONENT CANDIDATE: {'YES' if cand else 'no'}**")

    # ---- secondary: non-index roots, GROSS only, no cost line
    P(f"\n  SECONDARY -- non-index roots, GROSS ticks per session, NO cost line "
      f"(MGC/MCL/M6E absent; nothing guessed):")
    P(f"  {'root':>5}{'var':>4}{'M':>3}{'trips/sess':>12}{'gross tk/sess':>15}")
    gross = []
    skipped = [r for r in NONINDEX_ROOTS if panel[r]["tick_pts"] is None]
    for r in NONINDEX_ROOTS:
        p = panel[r]
        if p["tick_pts"] is None:
            # 6E has no entry in futures_contract_specs.json at all, so not even a GROSS
            # figure in ticks is expressible. Reported as skipped rather than converted
            # through a guessed tick size.
            continue
        for var in ("B1", "B2"):
            for M in M_NONINDEX:
                pnl, tr = simulate(p["O"], p["C"], p[var], p["first"], M, 0.0,
                                   p["tick_pts"])
                gross.append({"root": r, "variant": var, "M": M,
                              "trips_per_session": float(tr.mean()),
                              "gross_ticks_per_session": float(pnl.mean())})
                if M in (1, 8):
                    P(f"  {r:>5}{var:>4}{M:>3}{tr.mean():>12.2f}"
                      f"{pnl.mean():>+15.3f}")

    if skipped:
        P(f"  skipped entirely (no tick size in the committed specs, so not even a GROSS "
          f"tick figure is expressible): {', '.join(skipped)}")

    # ---- §6 predictions
    d488 = json.loads((REPO / "data" / "d488_extended_hold.json").read_text(encoding="utf-8"))
    d488_best = max((t["gross_over_cost"] for t in d488["S3_tradeability"]), default=0.0)
    nq = [c for c in cells if c["root"] == "NQ"]
    nq_best = max(nq, key=lambda z: z["sharpe"]) if nq else None
    trips_by_m = {M: float(np.mean([c["trips_per_session"] for c in cells if c["M"] == M]))
                  for M in M_INDEX}
    sh_by_m = {M: float(np.nanmean([c["sharpe"] for c in cells if c["M"] == M]))
               for M in M_INDEX}
    interior = (max(sh_by_m, key=sh_by_m.get) not in (min(M_INDEX), max(M_INDEX)))
    b1m = float(np.nanmean([c["sharpe"] for c in cells if c["variant"] == "B1"]))
    b2m = float(np.nanmean([c["sharpe"] for c in cells if c["variant"] == "B2"]))
    b1t = float(np.mean([c["trips_per_session"] for c in cells if c["variant"] == "B1"]))
    b2t = float(np.mean([c["trips_per_session"] for c in cells if c["variant"] == "B2"]))
    va = bool(nq_best is not None and nq_best["sharpe"] > 0)
    vb = bool(trips_by_m[min(M_INDEX)] > trips_by_m[max(M_INDEX)] and interior)
    vc = bool(b1m > b2m)
    vd = not signal
    ve = all(c["C_d"] for c in cells)
    P(f"\n  === PRE-REGISTERED PREDICTIONS (D491 §6) ===")
    P(f"    trips/session by M: " + "  ".join(f"M{M} {trips_by_m[M]:.2f}" for M in M_INDEX))
    P(f"    Sharpe by M:        " + "  ".join(f"M{M} {sh_by_m[M]:+.2f}" for M in M_INDEX))
    P(f"    V-a conditional beats D488's best    {'HELD' if va else 'BROKEN':>7}  "
      f"NQ best Sharpe {nq_best['sharpe']:+.2f} (D488 gross/cost {d488_best:.2f})")
    P(f"    V-b trips fall in M, Sharpe interior {'HELD' if vb else 'BROKEN':>7}")
    P(f"    V-c B1 beats B2                      {'HELD' if vc else 'BROKEN':>7}  "
      f"B1 {b1m:+.2f} ({b1t:.2f} trips) vs B2 {b2m:+.2f} ({b2t:.2f})")
    P(f"      -> the PRINCIPAL's counter-hypothesis (B2 wins, B1's zeros buy extra trips): "
      f"{'CONFIRMED' if b2m > b1m else 'not confirmed'}")
    P(f"    V-d no cell clears the family bar    {'HELD' if vd else 'BROKEN':>7}")
    P(f"    V-e C-d not binding                  {'HELD' if ve else 'BROKEN':>7}")

    res = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "pre_registration": "docs/decisions/D491-PRE-REG-the-conditional-hold-exit-when-"
                               "the-signal-flips-with-a-minimum-hold-time.md",
           "purpose": "D491: conditional exit on a MACD sign flip with a minimum hold. "
                      "Produces a real P&L series, so C-a/C-c/C-d are computed directly.",
           "cost": {"commission_rt": COMMISSION_RT, "crossing_ticks": CROSS_TICKS,
                    "charged": "per completed round trip"},
           "primary_cells": cells, "family_max_observed": obs, "best_cell": best,
           "null_family_max": {"p50": p50, "p95": p95, "se_of_p95": se,
                               "margin_in_se": marg},
           "verdict": {"signal": signal, "component_candidate": cand},
           "secondary_gross_noncostable": gross,
           "secondary_skipped_no_tick_size": skipped,
           "trips_by_M": trips_by_m, "sharpe_by_M": sh_by_m,
           "variant_means": {"B1_sharpe": b1m, "B2_sharpe": b2m,
                             "B1_trips": b1t, "B2_trips": b2t},
           "predictions": {"V-a": va, "V-b": vb, "V-c": vc, "V-d": vd, "V-e": ve},
           "limitations": [
               "only ES/NQ/YM can be costed; the largest D484 edges (GC, CL) remain "
               "unpriceable because MGC/MCL/M6E are absent and nothing is guessed",
               "execution is open-of-next-segment at the measured half-spread: no queue, no "
               "partial fills, no slippage on a flip -- fills need mbp-10 (D471), so every "
               "figure is an upper bound",
               "the volume-clock exit (D472, +10.4%) is not applied",
               "hourly resolution: a flip inside an hour is invisible",
               "in-sample only; 2024+ sealed",
               "the index window is 6 hours, so at M=5 the construction is nearly a fixed-H "
               "hold -- a feature of the closure, not of the idea"]}
    if as_json:
        OUT.write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
        P(f"\nwrote {OUT.relative_to(REPO)}")
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
