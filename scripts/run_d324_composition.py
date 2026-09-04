"""D324 -- is the fragility a property of the BOOK or of the SIGNAL?

    uv run python scripts/run_d324_composition.py --selftest
    uv run python scripts/run_d324_composition.py

PRE-REGISTERED AT `5544e7c`, committed before this file existed (R8).

D322 measured the incumbent's composition and found 6 names of 718 making half the
P&L and 57.3% of it in the cheapest price tercile, where commission is 7.01 bp
round trip against 0.87 in the top. D323 then found the ranking INVERTS with width
and that three candidates tie or beat the incumbent. Sharpe is tied and the
fixture cannot resolve the +0.008 between the top two; COMPOSITION is not tied and
has been measured for exactly one of them.

THE DECLARED STATISTICS, FIXED BEFORE THE NUMBERS: names to reach half the P&L
(higher is healthier, incumbent 6 of 718) and the low-price tercile's share
(lower is healthier). Everything else is reported and NOT used to rank.

k IS THE CONFOUND THAT DECIDES HOW THE CELLS READ. A 40-bar hold makes roughly an
eighth of the trades of a 5-bar hold over fewer names, and retrace_leg's best cell
is k=40 while the incumbent's is k=10 -- so an unmatched comparison would measure
the holding period and call it the signal. Every candidate is therefore run at its
OWN BEST cell and at a MATCHED k=10/dv-off cell, and trade count is printed beside
every composition statistic.

THE GROUP FUNCTIONS ARE D322's, IMPORTED NOT REWRITTEN, so the incumbent's numbers
must come back bit-identical -- which assertion [1] checks. Rewriting them would
have made a difference in composition indistinguishable from a difference in
implementation.
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


G22 = _load("d322", "d322_four_group_report.py")     # group1/2/3, costed, contribs
Y = _load("d323", "run_d323_shortlist_at_operating_point.py")
W, D, M, SP, R, F = G22.W, G22.D, G22.M, G22.SP, Y.R, Y.F
X = G22.X

DEPTH = 2
# candidate -> (own-best k, own-best dv), read from D323's result table
OWN_BEST = {"incumbent": (10, True), "retrace_leg": (40, False),
            "rev_21": (10, False), "rsi": (10, False)}
MATCHED = (10, False)
OUT = REPO / "data" / "d324_composition.json"


def build(A, z, base, finT, keep28, cand, k, dv, n, T):
    """One book: the incumbent's composite gate, or a single candidate's."""
    if cand == "incumbent":
        gate = (W.build_gate(A, verbose=False) if not dv
                else Y.gate_from(np.asarray(A["rankT"]), finT, keep28))
    else:
        rk = Y.rank_single(z, base, cand, n, T)
        gate = Y.gate_from(rk, finT, keep28 if dv else None)
    W.BASE_HOLD = k
    return W.simulate(A, gate, DEPTH, True), gate


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    t0 = time.time()

    print("D324  composition of the top candidates")
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    r1T = np.asarray(A["r1T"])
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    HALF = np.ascontiguousarray(
        (SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
    CLOSE = np.ascontiguousarray(panel.closes.T)
    VOL = np.full(CLOSE.shape, np.nan)
    sym = {s: i for i, s in enumerate(panel.symbols)}
    pos = {d: i for i, d in enumerate(panel.dates)}
    for s, bars in cleaned.items():
        i = sym.get(s)
        if i is None:
            continue
        for st in bars:
            t = pos.get(st.timestamp[:10])
            if t is not None:
                VOL[t, i] = st.bar.volume
    finT = np.asarray(A["finT"])
    DV = X.roll_mean_T(CLOSE * VOL)
    G4 = (HALF, CLOSE, DV, finT)
    keep28 = X.keep_mask(DV, finT, G22.DV_PCT, True)
    years = np.array([int(d[:4]) for d in panel.dates])
    meta = json.loads(G22.META.read_text())["symbols"]
    dead = np.array([bool(meta.get(s, {}).get("delistingDate"))
                     for s in panel.symbols])
    z = np.load(R.BC.CACHE, allow_pickle=False)
    base = z["warm"] & panel.live
    n, T = panel.live.shape
    d322 = json.loads((REPO / "data" / "d322_four_group_report.json").read_text())
    d323 = json.loads((REPO / "data" / "d323_shortlist.json").read_text())
    print(f"  panel {finT.shape}, {int(dead.sum())} delisted "
          f"({time.time() - t0:.0f}s)")

    # ---- the cells --------------------------------------------------------
    todo = []
    for cand, (k, dv) in OWN_BEST.items():
        todo.append((cand, k, dv, "own-best"))
        if (k, dv) != MATCHED:
            todo.append((cand, MATCHED[0], MATCHED[1], "matched"))
    cells = {}
    for cand, k, dv, kind in todo:
        res, gate = build(A, z, base, finT, keep28, cand, k, dv, n, T)
        c = G22.costed(res, G4)
        contrib = G22.contributions(res, r1T)
        cells[f"{cand}/k{k}/dv{int(dv)}"] = dict(
            candidate=cand, k=k, dv=dv, kind=kind, cost=c,
            group1=G22.group1(res, c, contrib, r1T),
            group2=G22.group2(res),
            group3=G22.group3(res, contrib, c, years, dead, CLOSE, HALF))
    print(f"  {len(cells)} cells built ({time.time() - t0:.0f}s)")

    # ---- assertions -------------------------------------------------------
    print("\nASSERTIONS")
    # 1. THE INCUMBENT reproduces D322 -- but D322's BASE is k=5/dv0, so the
    #    check is run on that cell explicitly rather than on a k=10 lookalike.
    res5, _ = build(A, z, base, finT, keep28, "incumbent", 5, False, n, T)
    c5 = G22.costed(res5, G4)
    g2 = G22.group2(res5)
    g3 = G22.group3(res5, G22.contributions(res5, r1T), c5, years, dead,
                    CLOSE, HALF)
    ref2 = d322["cells"]["BASE"]["group2"]
    ref3 = d322["cells"]["BASE"]["group3"]
    w2 = max(abs(g2["mean_bp"] - ref2["mean_bp"]),
             abs(g2["median_bp"] - ref2["median_bp"]),
             abs(g2["mean_trimmed_bp"] - ref2["mean_trimmed_bp"]))
    assert w2 < 1e-9, f"[1] group2 differs from D322 by {w2:.2e}"
    assert g3["names_to_half_pnl"] == ref3["names_to_half_pnl"], \
        f"[1] names-to-half {g3['names_to_half_pnl']} vs " \
        f"{ref3['names_to_half_pnl']}"
    assert abs(g3["price_low"]["share_pnl"] - ref3["price_low"]["share_pnl"]) < 1e-12
    print(f"    [1] the incumbent at k=5 reproduces D322's group 2 (max "
          f"{w2:.1e} bp) and group 3 -- names-to-half "
          f"{g3['names_to_half_pnl']}, low-price share "
          f"{g3['price_low']['share_pnl']:.4f}")

    # 1b. AND THE D323 CELLS reproduce, so the two studies score the same books.
    worst = 0.0
    for cand, (k, dv) in OWN_BEST.items():
        if cand == "incumbent":
            continue
        ref = d323["cells"][f"{cand}/k{k}/dv{int(dv)}"]
        got = cells[f"{cand}/k{k}/dv{int(dv)}"]["cost"]
        worst = max(worst, abs(got["gross_bp"] - ref["gross_bp"]))
    assert worst < 1e-9, f"[1b] differs from D323 by {worst:.2e} bp"
    print(f"    [1b] every candidate's own-best cell reproduces D323's gross to "
          f"{worst:.1e} bp")

    # 3. THE SYMMETRIC TRIM IS SYMMETRIC.
    for nm, c in cells.items():
        assert c["group2"]["n_dropped_top"] == c["group2"]["n_dropped_bottom"], \
            f"[3] {nm} trim is one-sided"
    print("    [3] every cell's 1% trim drops the same count from both tails")

    # F/S/C inherited from D322's own checks, re-run on this study's cells.
    # S. SPREAD BASIS. Earlier studies asserted the held round trip EXCEEDS the
    #    universe median, which held because every book they scored was more
    #    expensive than the universe. It fails here, and correctly: dv28 filters
    #    to high-dollar-volume names, so the incumbent's dv28 cell holds names
    #    TIGHTER than the universe median. The one-directional form was assuming
    #    a property of those books rather than testing the basis. What must be
    #    true either way is that the number comes from the names HELD, and that a
    #    hard-coded universe constant would fail.
    uni = 4.0 * float(np.nanmedian(HALF[np.isfinite(HALF)]))
    below = []
    for nm, c in cells.items():
        res_nm, _ = build(A, z, base, finT, keep28, c["candidate"], c["k"],
                          c["dv"], n, T)
        own = 4.0 * F.held_median(res_nm, HALF)
        assert abs(c["cost"]["round_trip"] - own) < 1e-9, \
            f"[S] {nm} rt is not 4 x the held-name median"
        below.append((nm, c["cost"]["round_trip"] / uni - 1.0))
    # AND THE SPREAD ACROSS CELLS proves the number is data-dependent rather than
    # a constant. Asserting that EVERY cell differs from the universe median was
    # the wrong shape twice over -- it asserts a property of the DATA, not of the
    # code, and it fails here for a real reason: dv28 filters to liquid names, so
    # the incumbent's dv28 cell lands within 5% of the universe median and one
    # cell sits BELOW it. What the basis test must catch is a hard-coded
    # constant, and a spread across cells catches exactly that.
    rng_rt = max(c["cost"]["round_trip"] for c in cells.values()) / \
        min(c["cost"]["round_trip"] for c in cells.values()) - 1.0
    assert rng_rt > 0.20, \
        f"[S] the round trip barely moves across cells ({rng_rt:.1%}) -- it may " \
        f"be a constant rather than the held-name median"
    d295 = json.loads((REPO / "data" / "d295_exits.json").read_text())
    b0 = [x for x in d295["rows"] if x["cell"] == "B0"][0]
    got = d295["round_trip_mean"] * b0["turnover"]
    assert abs(got - b0["cost_bar_mean"]) < 1e-9 * abs(b0["cost_bar_mean"])
    assert abs(got * 2.0 - b0["cost_bar_mean"]) > 1.0
    print(f"    [S] every cell's rt is 4 x its OWN held-name median, and across "
          f"cells it spans {100 * rng_rt:.0f}% -- data-dependent, not a constant."
          f"\n        Against the universe {uni:.1f}: "
          + ", ".join("%s %+.0f%%" % (b[0].split("/")[0], 100 * b[1])
                      for b in below))
    print(f"    [C] cost dimensions: rt x turn = {got:.4f} reproduces d295's")

    # 4. DISTINCT BOOKS.
    seen = {}
    for nm, c in cells.items():
        kk = round(c["cost"]["gross_bp"], 12)
        assert kk not in seen, f"[4] {nm} is identical to {seen[kk]}"
        seen[kk] = nm
    print(f"    [4] all {len(seen)} cells are distinct books")

    # 5. THE SELF-TEST MUST RAISE.
    broke = False
    try:
        bk = res5["book"].copy()
        bk[np.flatnonzero(res5["mask"])[:200]] += 5e-4
        assert abs(float(bk[res5["mask"]].mean()) * 1e4
                   - d322["cells"]["BASE"]["group1"]["gross_bp_bar"]) < 1e-9
    except AssertionError:
        broke = True
    assert broke, "[5] reproduction passed a book handed free money"
    print("    [5] and [1] raises on a book handed free money inside the mask")

    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    # ---- the two declared statistics --------------------------------------
    print("\nTHE DECLARED STATISTICS   (primary: names to half P&L, higher better)")
    print("                          (secondary: low-price share, lower better)")
    h = "%-22s %8s %8s %8s %9s %10s %9s %9s %8s"
    print(h % ("cell", "kind", "trades", "names", "NAMES/HALF", "LOW-PRICE",
               "top10", "netSHRP", "net bp"))
    print("-" * 100)
    for kind in ("matched", "own-best"):
        for nm, c in cells.items():
            if c["kind"] != kind:
                continue
            g1, g3 = c["group1"], c["group3"]
            print(h % (nm, kind, "%d" % c["group2"]["n"], "%d" % g3["names"],
                       "%d" % g3["names_to_half_pnl"],
                       "%.1f%%" % (100 * g3["price_low"]["share_pnl"]),
                       "%.1f%%" % (100 * g3["top10_name_share"]),
                       "%+.3f" % g1["sharpe_net"], "%+.2f" % g1["net_bp_bar"]))
        print("-" * 100)

    print("\nGROUP 2 -- the two-sided tail signature")
    h2 = "%-22s %9s %9s %7s %10s %9s %8s"
    print(h2 % ("cell", "mean", "median", "below?", "trim 1%", "win rate", "payoff"))
    for nm, c in cells.items():
        g2 = c["group2"]
        print(h2 % (nm, "%+.2f" % g2["mean_bp"], "%+.2f" % g2["median_bp"],
                    "YES" if g2["mean_below_median"] else "no",
                    "%+.2f" % g2["mean_trimmed_bp"],
                    "%.1f%%" % (100 * g2["win_rate"]), "%.3f" % g2["payoff"]))

    print("\nGROUP 3 -- era, dead/alive, and the price ladder")
    h3 = "%-22s %10s %10s %10s %11s %9s"
    print(h3 % ("cell", "era 1st", "dead mean", "alive mean", "dead>=alive?",
                "yrs net+"))
    for nm, c in cells.items():
        g3 = c["group3"]
        print(h3 % (nm, "%.1f%%" % (100 * g3["era_first_half"]["share_pnl"]),
                    "%+.1f" % g3["dead"]["mean_bp"],
                    "%+.1f" % g3["alive"]["mean_bp"],
                    "YES" if g3["dead"]["mean_bp"] >= g3["alive"]["mean_bp"]
                    else "NO",
                    "%d/%d" % (g3["years_profitable_net"], g3["years"])))

    # ---- predictions -------------------------------------------------------
    inc_m = cells[f"incumbent/k{MATCHED[0]}/dv{int(MATCHED[1])}"]
    base_names = inc_m["group3"]["names_to_half_pnl"]
    base_low = inc_m["group3"]["price_low"]["share_pnl"]
    matched = {nm: c for nm, c in cells.items() if c["kind"] == "matched"
               or (c["candidate"] != "incumbent" and c["k"] == MATCHED[0]
                   and not c["dv"])}
    q2 = not any(c["group3"]["names_to_half_pnl"] >= 12
                 and c["group3"]["price_low"]["share_pnl"] < base_low
                 for nm, c in matched.items() if c["candidate"] != "incumbent")
    q3 = all(c["group3"]["price_low"]["share_pnl"] > 0.45 for c in cells.values())
    q4 = all(c["group3"]["names_to_half_pnl"] <= 10 for c in matched.values())
    q6 = all(c["group3"]["dead"]["mean_bp"] >= c["group3"]["alive"]["mean_bp"]
             for c in cells.values())
    q7 = all(c["group2"]["mean_below_median"] for c in cells.values())
    res = {"note": "D324: composition of the top candidates. Declared primary = "
                   "names to half P&L; secondary = low-price tercile share.",
           "own_best": {k: list(v) for k, v in OWN_BEST.items()},
           "matched_cell": list(MATCHED), "cells": cells,
           "incumbent_matched": {"names_to_half": base_names,
                                 "low_price_share": base_low},
           "predictions": dict(Q2=bool(q2), Q3=bool(q3), Q4=bool(q4),
                               Q6=bool(q6), Q7=bool(q7))}
    print("\nPREDICTIONS")
    for k, v in (("Q2 no candidate healthier on BOTH at the matched cell "
                  "[load-bearing]", q2),
                 ("Q3 every candidate puts >45% of P&L in the low-price tercile", q3),
                 ("Q4 every matched cell needs <=10 names for half the P&L", q4),
                 ("Q6 dead names at least as profitable as alive, everywhere", q6),
                 ("Q7 mean below median everywhere", q7)):
        print(f"    {'CONFIRMED' if v else 'FALSIFIED'}  {k}")
    print("    incumbent at the matched cell: %d names to half, %.1f%% low-price"
          % (base_names, 100 * base_low))

    OUT.write_text(json.dumps(res, indent=1, default=float))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
