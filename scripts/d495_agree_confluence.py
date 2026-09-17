"""D495 -- does requiring the two MACD variants to AGREE help, and is any help DIRECTION or
just fewer trades?

    uv run python scripts/d495_agree_confluence.py --self-test
    uv run python scripts/d495_agree_confluence.py --run [--json]

Pre-registered in
`docs/decisions/D495-PRE-REG-does-requiring-the-two-MACD-variants-to-AGREE-help-and.md`.
**State machine and signal code imported from D491 and D484 unchanged.**

THE DECOMPOSITION IS THE WHOLE POINT
------------------------------------
Requiring agreement does TWO things at once. It may improve direction, and it certainly
**enters less often** and pays fewer round trips. Commission is 70-86% of cost, so the second
alone could raise net Sharpe with **no directional improvement whatever**. So every arm is
scored TWICE -- gross (cost set to zero: pure direction) and net -- with trips reported.

ALSO COMPUTED: THE EXACT P5 HAIRCUT
-----------------------------------
R11's restatement caps a single day's contribution at 30% of the period's profit:
`recognised = total - max(0, best_day - 0.30*total)`. D496 had to apply a FLAT 30% because
D491 never stored the best day. This runner stores it, so the haircut -- and therefore P4's
profit-before-breach test -- becomes exact rather than an upper bound on its bite.
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
    CROSS_TICKS, COMMISSION_RT, SEGMENTS, SPECS, impulse_macd, macd_hist, rotate, series_for,
)
from d491_conditional_hold import (  # noqa: E402
    DAY_FIRST_DECIDE, INDEX_ROOTS, LAST_SEG, M_INDEX, M_NONINDEX, NONINDEX_ROOTS,
    TRADING_DAYS, simulate,
)

FIX = REPO / "data" / "fixtures" / "fut_sessions_hourly.csv.gz"
META = REPO / "data" / "fixtures" / "fut_sessions_hourly.meta.json"
OUT = REPO / "data" / "d495_agree_confluence.json"

ROOTS = INDEX_ROOTS + NONINDEX_ROOTS
ARMS = ("AGREE", "B1", "B2")
MICRO_OF = {"ES": "MES", "NQ": "MNQ", "YM": "MYM", "GC": "MGC", "CL": "MCL", "6E": "M6E"}
N_DRAWS = 2000
C_A, C_C, C_D = 0.5, -0.5, 500.0
P5_CAP = 0.30
ACCOUNT = 50_000.0
SEED = 495


class GateError(AssertionError):
    """A validation gate refused the input."""


def P(*a, **k):
    print(*a, **k, flush=True)


def p5_recognised(daily_usd: np.ndarray) -> dict:
    """R11's exact single-day haircut. `recognised = total - max(0, best - 0.30*total)`."""
    total = float(daily_usd.sum())
    best = float(daily_usd.max()) if len(daily_usd) else 0.0
    if total <= 0:
        return {"total_usd": total, "best_day_usd": best, "best_day_share": float("nan"),
                "haircut_usd": 0.0, "recognised_usd": total, "haircut_applies": False}
    excess = max(0.0, best - P5_CAP * total)
    return {"total_usd": total, "best_day_usd": best, "best_day_share": best / total,
            "haircut_usd": excess, "recognised_usd": total - excess,
            "haircut_applies": excess > 0}


def score_full(pnl_ticks: np.ndarray, tick_usd: float) -> dict:
    """Net/gross-agnostic scoring of a P&L series, plus the exact P5 haircut."""
    d = pnl_ticks * tick_usd
    mu, sd = float(d.mean()), float(d.std(ddof=1))
    sk = float(((d - mu) ** 3).mean() / sd ** 3) if sd > 0 else float("nan")
    h = p5_recognised(d)
    rec_mu = h["recognised_usd"] / len(d) if len(d) else float("nan")
    return {"n_sessions": int(len(d)), "mean_usd": mu, "daily_sigma_usd": sd,
            "sharpe": (mu / sd * np.sqrt(TRADING_DAYS)) if sd > 0 else float("nan"),
            "skew": sk,
            "recognised_sharpe": (rec_mu / sd * np.sqrt(TRADING_DAYS)) if sd > 0
            else float("nan"), **h}


def agree_signal(b1: np.ndarray, b2: np.ndarray) -> np.ndarray:
    """§1: sign(B1) where the two agree and neither is zero; 0 otherwise."""
    s1, s2 = np.nan_to_num(b1, nan=0.0), np.nan_to_num(b2, nan=0.0)
    return np.where((s1 == s2) & (s1 != 0), s1, 0.0)


def do_self_test() -> int:
    fails = []

    def chk(label, cond, detail=""):
        P(f"    [{'PASS' if cond else 'FAIL'}] {label:66} {detail}")
        if not cond:
            fails.append(label)

    # --- the AGREE gate
    b1 = np.array([1.0, 1.0, -1.0, -1.0, 0.0, 1.0, np.nan])
    b2 = np.array([1.0, -1.0, -1.0, 1.0, 1.0, 0.0, 1.0])
    a = agree_signal(b1, b2)
    chk("AGREE passes a matching pair", a[0] == 1.0 and a[2] == -1.0, f"{a[:3]}")
    chk("AGREE blocks a disagreeing pair", a[1] == 0.0 and a[3] == 0.0)
    chk("AGREE blocks when either is zero", a[4] == 0.0 and a[5] == 0.0)
    chk("AGREE blocks a NaN", a[6] == 0.0)
    chk("AGREE is a SUBSET of each variant's entries",
        int((a != 0).sum()) <= min(int((np.nan_to_num(b1) != 0).sum()),
                                   int((np.nan_to_num(b2) != 0).sum())),
        f"{int((a != 0).sum())} of {int((np.nan_to_num(b1) != 0).sum())}/"
        f"{int((np.nan_to_num(b2) != 0).sum())}")
    rg = np.random.default_rng(3)
    r1 = np.sign(rg.standard_normal(100_000))
    r2 = np.sign(rg.standard_normal(100_000))
    chk("on independent signs, AGREE fires about half the time",
        abs(float((agree_signal(r1, r2) != 0).mean()) - 0.5) < 0.01,
        f"{float((agree_signal(r1, r2) != 0).mean()):.3f}")
    chk("and on identical signals AGREE reproduces them exactly",
        bool(np.array_equal(agree_signal(r1, r1), r1)))

    # --- THE P5 HAIRCUT, on cases computable by hand
    h = p5_recognised(np.array([1000.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0,
                                100.0, 100.0, 100.0]))
    # total 1900, best 1000, 30% of total = 570, excess = 430, recognised = 1470
    chk("haircut: total 1900 best 1000 -> excess 430, recognised 1470",
        abs(h["total_usd"] - 1900) < 1e-9 and abs(h["haircut_usd"] - 430) < 1e-9
        and abs(h["recognised_usd"] - 1470) < 1e-9,
        f"recognised {h['recognised_usd']:.0f}, share {h['best_day_share']:.3f}")
    flat = p5_recognised(np.full(10, 100.0))
    chk("haircut: a perfectly even series is untouched",
        flat["haircut_usd"] == 0.0 and not flat["haircut_applies"],
        f"best share {flat['best_day_share']:.3f} <= 0.30")
    chk("haircut: it bites exactly when the best day exceeds 30% of the total",
        p5_recognised(np.array([31.0, 23.0, 23.0, 23.0]))["haircut_applies"]
        and not p5_recognised(np.array([29.0, 24.0, 24.0, 23.0]))["haircut_applies"])
    chk("haircut: a LOSING series is not haircut (total <= 0)",
        not p5_recognised(np.array([-10.0, -20.0]))["haircut_applies"])
    chk("haircut can only REDUCE profit, never raise it",
        all(p5_recognised(x)["recognised_usd"] <= p5_recognised(x)["total_usd"] + 1e-9
            for x in (np.array([5.0, 1.0]), np.full(50, 2.0),
                      rg.standard_normal(200) + 0.1)))
    # and the D496 flat-30% assumption is shown to be an UPPER BOUND on the bite
    d = rg.standard_normal(2000) * 50 + 5
    hh = p5_recognised(d)
    chk("D496's flat 30% haircut is an UPPER BOUND on the real bite",
        hh["haircut_usd"] <= 0.30 * hh["total_usd"] + 1e-9,
        f"real {hh['haircut_usd']/hh['total_usd']:.1%} vs flat 30%")

    # --- gross vs net must differ by exactly cost x trips
    n_seg = 23
    O = np.tile(np.arange(n_seg, dtype=float), (400, 1))
    C_ = O + 0.5
    sig = np.ones((400, n_seg))
    pg, tg = simulate(O, C_, sig, 0, 1, 0.0, 1.0)
    pn, tn = simulate(O, C_, sig, 0, 1, 4.0, 1.0)
    chk("net = gross - cost x trips, exactly",
        np.allclose(pn, pg - 4.0 * tg) and np.array_equal(tg, tn),
        f"gross {pg[0]:.2f}, net {pn[0]:.2f}, trips {tg[0]:.0f}")
    chk("and the TRIP COUNT is identical -- cost cannot change behaviour here",
        bool(np.array_equal(tg, tn)))

    # --- scoring
    sc = score_full(np.full(500, 2.0) * 0 + np.tile([3.0, -1.0], 250), 1.0)
    chk("score_full returns both a Sharpe and a recognised Sharpe",
        np.isfinite(sc["sharpe"]) and np.isfinite(sc["recognised_sharpe"]))
    chk("recognised Sharpe <= Sharpe when the haircut bites, equal otherwise",
        sc["recognised_sharpe"] <= sc["sharpe"] + 1e-12)

    # --- costs, now available for six of eight roots
    spec = json.loads(SPECS.read_text(encoding="utf-8"))
    for r, m in MICRO_OF.items():
        chk(f"{r} -> {m} cost available", m in spec,
            f"{COMMISSION_RT/spec[m]['tick_usd'] + CROSS_TICKS:.3f} tk" if m in spec else "")
    chk("ZN and ZB have NO micro and are scored at one FULL contract",
        "ZN" not in MICRO_OF and "ZB" not in MICRO_OF)
    chk("6E uses the GLOBEX tick ($6.25), not ClearPort's $1.25",
        abs(spec["6E"]["tick_usd"] - 6.25) < 1e-9 and "VENUE_SPLIT_WARNING" in spec["6E"])

    if fails:
        P(f"\n  SELF-TEST FAILED: {fails}")
        return 1
    P("\n  SELF-TEST PASSED.")
    return 0


def build_panel(d_all, meta, spec):
    nseg = len(SEGMENTS)
    panel = {}
    for r in ROOTS:
        s = series_for(r, d_all, meta)
        k = len(s["log_close"]) // nseg
        g = lambda a: np.exp(a[:k * nseg]).reshape(k, nseg)   # noqa: E731
        md = impulse_macd(s["log_high"], s["log_low"], s["log_close"])[1][:k * nseg]
        b1 = np.where(md == 0.0, 0.0,
                      np.sign(impulse_macd(s["log_high"], s["log_low"],
                                           s["log_close"])[0][:k * nseg])).reshape(k, nseg)
        b2 = np.sign(macd_hist(s["log_close"])[:k * nseg]).reshape(k, nseg)
        pure = s["pure"][:k * nseg].reshape(k, nseg)
        first = DAY_FIRST_DECIDE if r in INDEX_ROOTS else 0
        keep = pure[:, first:LAST_SEG + 1].all(axis=1)
        micro = MICRO_OF.get(r)
        sized = micro if micro else r
        panel[r] = {"O": g(s["log_open"])[keep], "C": g(s["log_close"])[keep],
                    "B1": b1[keep], "B2": b2[keep],
                    "AGREE": agree_signal(b1, b2)[keep],
                    "first": first, "tick_pts": spec[r]["tick_points"],
                    "tick_usd": spec[sized]["tick_usd"], "sized_as": sized,
                    "cost": COMMISSION_RT / spec[sized]["tick_usd"] + CROSS_TICKS,
                    "n": int(keep.sum())}
    return panel


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

    panel = build_panel(pd.read_csv(FIX), meta, spec)
    P("  root  sized as   sessions   cost tk   agree rate")
    for r in ROOTS:
        p = panel[r]
        lo = p["first"]
        ar = float((p["AGREE"][:, lo:LAST_SEG] != 0).mean())
        P(f"  {r:>5}{p['sized_as']:>10}{p['n']:>11}{p['cost']:>10.3f}{ar:>13.1%}")

    cells = []
    for r in ROOTS:
        p = panel[r]
        Ms = M_INDEX if r in INDEX_ROOTS else M_NONINDEX
        for arm in ARMS:
            for M in Ms:
                pg, tg = simulate(p["O"], p["C"], p[arm], p["first"], M, 0.0, p["tick_pts"])
                pn, tn = simulate(p["O"], p["C"], p[arm], p["first"], M, p["cost"],
                                  p["tick_pts"])
                sg = score_full(pg, p["tick_usd"])
                sn = score_full(pn, p["tick_usd"])
                cells.append({"root": r, "arm": arm, "M": M, "sized_as": p["sized_as"],
                              "cost_ticks": p["cost"],
                              "trips_per_session": float(tn.mean()),
                              "gross_sharpe": sg["sharpe"], "net_sharpe": sn["sharpe"],
                              "net_recognised_sharpe": sn["recognised_sharpe"],
                              "net_mean_usd": sn["mean_usd"],
                              "daily_sigma_usd": sn["daily_sigma_usd"],
                              "skew": sn["skew"],
                              "net_total_usd": sn["total_usd"],
                              "net_recognised_usd": sn["recognised_usd"],
                              "best_day_usd": sn["best_day_usd"],
                              "best_day_share": sn["best_day_share"],
                              "haircut_usd": sn["haircut_usd"],
                              "C_a": bool(sn["sharpe"] > C_A),
                              "C_c": bool(sn["skew"] >= C_C),
                              "C_d": bool(sn["daily_sigma_usd"] <= C_D)})

    def best(arm, root, key):
        sub = [c for c in cells if c["arm"] == arm and c["root"] == root]
        return max(sub, key=lambda z: z[key] if z[key] == z[key] else -9)

    P(f"\n  BY ROOT -- best cell per arm, NET Sharpe (and GROSS in brackets):")
    P(f"  {'root':>5}{'AGREE':>18}{'B1':>18}{'B2':>18}{'net lift':>10}{'gross lift':>12}")
    lifts_n, lifts_g = [], []
    per_root = {}
    for r in ROOTS:
        a = best("AGREE", r, "net_sharpe")
        b1 = best("B1", r, "net_sharpe")
        b2 = best("B2", r, "net_sharpe")
        single_n = max(b1["net_sharpe"], b2["net_sharpe"])
        ag = best("AGREE", r, "gross_sharpe")
        single_g = max(best("B1", r, "gross_sharpe")["gross_sharpe"],
                       best("B2", r, "gross_sharpe")["gross_sharpe"])
        ln, lg = a["net_sharpe"] - single_n, ag["gross_sharpe"] - single_g
        lifts_n.append(ln)
        lifts_g.append(lg)
        per_root[r] = {"agree_net": a["net_sharpe"], "agree_M": a["M"],
                       "best_single_net": single_n, "net_lift": ln,
                       "agree_gross": ag["gross_sharpe"], "best_single_gross": single_g,
                       "gross_lift": lg,
                       "agree_trips": a["trips_per_session"],
                       "single_trips": (b1 if b1["net_sharpe"] >= b2["net_sharpe"]
                                        else b2)["trips_per_session"]}
        P(f"  {r:>5}{a['net_sharpe']:>+11.3f} ({a['gross_sharpe']:+.2f})"
          f"{b1['net_sharpe']:>+11.3f} ({b1['gross_sharpe']:+.2f})"
          f"{b2['net_sharpe']:>+11.3f} ({b2['gross_sharpe']:+.2f})"
          f"{ln:>+10.3f}{lg:>+12.3f}")
    P1 = max(c["net_sharpe"] for c in cells if c["arm"] == "AGREE")
    P2n, P2g = float(np.mean(lifts_n)), float(np.mean(lifts_g))
    P(f"\n  P1 family-max NET Sharpe over the {sum(1 for c in cells if c['arm']=='AGREE')} "
      f"AGREE cells: {P1:+.3f}")
    P(f"  P2 pooled lift:  NET {P2n:+.4f}   GROSS {P2g:+.4f}")

    # ---- §3 null: rotate BOTH series by the SAME offset, re-run the machine
    rg = np.random.default_rng(SEED)
    P(f"  R1 null, {N_DRAWS:,} draws (both series rotated by ONE common offset) ...")
    n1 = np.empty(N_DRAWS)
    n2n = np.empty(N_DRAWS)
    n2g = np.empty(N_DRAWS)
    for i in range(N_DRAWS):
        bm, ln_, lg_ = -9.0, [], []
        for r in ROOTS:
            p = panel[r]
            Ms = M_INDEX if r in INDEX_ROOTS else M_NONINDEX
            sh = p["B1"].shape
            k = int(rg.integers(1, p["B1"].size - 1))
            rb1 = rotate(p["B1"].ravel(), k).reshape(sh)
            rb2 = rotate(p["B2"].ravel(), k).reshape(sh)
            rag = agree_signal(rb1, rb2)
            bn = {"AGREE": -9.0, "B1": -9.0, "B2": -9.0}
            bg = dict(bn)
            for arm, sgl in (("AGREE", rag), ("B1", rb1), ("B2", rb2)):
                for M in Ms:
                    pn, _ = simulate(p["O"], p["C"], sgl, p["first"], M, p["cost"],
                                     p["tick_pts"])
                    pg, _ = simulate(p["O"], p["C"], sgl, p["first"], M, 0.0, p["tick_pts"])
                    for arr, v in ((bn, pn), (bg, pg)):
                        sd = v.std(ddof=1)
                        if sd > 0:
                            arr[arm] = max(arr[arm],
                                           v.mean() / sd * np.sqrt(TRADING_DAYS))
            bm = max(bm, bn["AGREE"])
            ln_.append(bn["AGREE"] - max(bn["B1"], bn["B2"]))
            lg_.append(bg["AGREE"] - max(bg["B1"], bg["B2"]))
        n1[i] = bm
        n2n[i] = float(np.mean(ln_))
        n2g[i] = float(np.mean(lg_))

    def band(x, obs):
        p50, p95 = float(np.quantile(x, .50)), float(np.quantile(x, .95))
        boot = np.array([np.quantile(rg.choice(x, len(x), replace=True), .95)
                         for _ in range(400)])
        se = float(boot.std(ddof=1))
        return {"p50": p50, "p95": p95, "se_of_p95": se, "observed": obs,
                "margin_in_se": (obs - p95) / se, "clears_by_2se": bool(obs - p95 > 2 * se)}

    b1b, b2n, b2g = band(n1, P1), band(n2n, P2n), band(n2g, P2g)
    P(f"\n  === VERDICTS ===")
    for name, b in (("P1 family-max net", b1b), ("P2 lift NET", b2n),
                    ("P2 lift GROSS", b2g)):
        P(f"    {name:20} obs {b['observed']:+.4f}  p50 {b['p50']:+.4f}  "
          f"p95 {b['p95']:+.4f} (SE {b['se_of_p95']:.4f})  -> {b['margin_in_se']:+.1f} SE  "
          f"{'CLEARS' if b['clears_by_2se'] else 'no'}")
    conf_signal = b1b["clears_by_2se"]
    helps = b2n["clears_by_2se"]
    direction = b2g["clears_by_2se"]
    P(f"\n  **CONFLUENCE SIGNAL: {'YES' if conf_signal else 'no'} · "
      f"HELPS (net): {'YES' if helps else 'no'} · "
      f"HELPS ON DIRECTION (gross): {'YES' if direction else 'no'}**")

    bestA = max((c for c in cells if c["arm"] == "AGREE"), key=lambda z: z["net_sharpe"])
    cand = bool(conf_signal and bestA["C_a"] and bestA["C_c"] and bestA["C_d"])
    P(f"  best AGREE cell: {bestA['root']} M={bestA['M']} net {bestA['net_sharpe']:+.3f} "
      f"(recognised {bestA['net_recognised_sharpe']:+.3f}) · C-a {bestA['C_a']} "
      f"C-c {bestA['C_c']} C-d {bestA['C_d']}  -> COMPONENT CANDIDATE: "
      f"{'YES' if cand else 'no'}")

    # ---- the EXACT P5 haircut, which D496 could only bound
    P(f"\n  === THE EXACT P5 HAIRCUT (D496 had to assume a flat 30%) ===")
    P(f"  {'root':>5}{'arm':>7}{'M':>3}{'total$':>9}{'best day$':>11}{'share':>8}"
      f"{'haircut$':>10}{'recognised$':>13}{'Sharpe->rec':>14}")
    prof = [c for c in cells if c["net_total_usd"] > 0]
    for c in sorted(prof, key=lambda z: -z["net_sharpe"])[:10]:
        P(f"  {c['root']:>5}{c['arm']:>7}{c['M']:>3}{c['net_total_usd']:>9.0f}"
          f"{c['best_day_usd']:>11.0f}{c['best_day_share']:>8.1%}{c['haircut_usd']:>10.0f}"
          f"{c['net_recognised_usd']:>13.0f}"
          f"   {c['net_sharpe']:+.3f}->{c['net_recognised_sharpe']:+.3f}")
    bites = sum(1 for c in prof if c["haircut_usd"] > 0)
    P(f"  the haircut BITES on {bites} of {len(prof)} profitable cells")

    # ---- §5 predictions
    ua = b2n["clears_by_2se"]
    ub = not b2g["clears_by_2se"]
    tr_a = float(np.mean([per_root[r]["agree_trips"] for r in ROOTS]))
    tr_s = float(np.mean([per_root[r]["single_trips"] for r in ROOTS]))
    uc = (tr_s - tr_a) / tr_s >= 0.15
    pos_idx = [r for r in INDEX_ROOTS if per_root[r]["agree_net"] > 0]
    pos_non = [r for r in NONINDEX_ROOTS if per_root[r]["agree_net"] > 0]
    ud = pos_idx == ["NQ"] and pos_non == ["CL"]
    zb = [c for c in cells if c["root"] == "ZB"]
    ue = (not any(c["C_d"] for c in zb)) and (not any(
        c["C_a"] for c in cells if c["root"] == "ZN"))
    P(f"\n  === PRE-REGISTERED PREDICTIONS (D495 §5) ===")
    P(f"    U-a net lift clears its null         {'HELD' if ua else 'BROKEN':>7}")
    P(f"    U-b gross lift does NOT clear        {'HELD' if ub else 'BROKEN':>7}")
    P(f"    U-c AGREE trips >=15% fewer          {'HELD' if uc else 'BROKEN':>7}  "
      f"{tr_a:.2f} vs {tr_s:.2f} ({(tr_s-tr_a)/tr_s:+.1%})")
    P(f"    U-d only NQ (index) and CL positive  {'HELD' if ud else 'BROKEN':>7}  "
      f"index {pos_idx}, non-index {pos_non}")
    P(f"    U-e ZB fails C-d, ZN fails C-a       {'HELD' if ue else 'BROKEN':>7}")

    res = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "pre_registration": "docs/decisions/D495-PRE-REG-does-requiring-the-two-MACD-"
                               "variants-to-AGREE-help-and-is-any-help-direction-or-just-"
                               "fewer-trades.md",
           "cells": cells, "per_root": per_root,
           "P1_family_max_net": P1, "P2_lift_net": P2n, "P2_lift_gross": P2g,
           "nulls": {"P1": b1b, "P2_net": b2n, "P2_gross": b2g},
           "verdict": {"confluence_signal": conf_signal, "helps_net": helps,
                       "helps_on_direction": direction,
                       "component_candidate": cand, "best_agree_cell": bestA},
           "p5_haircut_bites_on": bites, "p5_profitable_cells": len(prof),
           "predictions": {"U-a": bool(ua), "U-b": bool(ub), "U-c": bool(uc),
                           "U-d": bool(ud), "U-e": bool(ue)},
           "limitations": [
               "111 cells against D491's 24; P1's null covers the 37 AGREE cells only",
               "ZN and ZB are scored at one FULL contract (no micro exists)",
               "6E uses the GLOBEX tick $6.25, not ClearPort's $1.25",
               "execution is open-of-next-segment at the measured half-spread: no queue, no "
               "partial fills, no slippage on a flip; fills need mbp-10 (D471)",
               "the volume-clock exit (D472, +10.4%) is not applied",
               "the index window is six hours, so the conditional exit has little room there",
               "in-sample only; 2024+ sealed"]}
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
