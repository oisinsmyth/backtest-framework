"""D290 -- ONE ranking per construction, using every diagnostic the study produced.

    uv run python scripts/d290_unified_rank.py [--top 20]

D290's headline ranked on name-split CV alone. That column cannot see
microstructure -- bid-ask bounce generalises across names perfectly well -- so
`lower_wick` led the short book on CV +6.19 while keeping NOTHING after one
skipped bar. This file folds in what was learned afterwards.

FOUR QUESTIONS, ASKED IN ORDER. A candidate has to answer all four, and they are
genuinely different:

  1. IS IT REAL?          min z > 0 across rotation, permutation and
                          tail-randomised nulls. Beats chance given turnover,
                          market regime, and its own factor tilt.
  2. DOES IT GENERALISE?  CV t > 0 -- holds on names it was not selected on.
  3. CAN YOU CATCH IT?    open-entry t. Enter at open[t] rather than at the
                          close that generated the signal. This is the question
                          the skip test could NOT answer, because skipping a bar
                          removes a real fast signal and an entry artifact
                          alike.
  4. DOES IT PAY?         effect against the MEASURED round trip on the names
                          actually held. Reported, never used to rank -- D289's
                          amendment defers magnitude to stage 2.

TIERS, and the boundary that matters is 1 vs 2.

  TIER 1  real, generalises, AND capturable (open-entry t >= 2)
  TIER 2  real and generalises but NOT capturable -- the edge exists and sits
          between the close you would trade at and the next open
  TIER 3  fails the null or the name split

Ranked WITHIN tier by open-entry t, because evidence you can act on is the only
evidence that ranks.

THE THREE CONSTRUCTIONS ARE RANKED SEPARATELY AND DO NOT SHARE A VERDICT. Long
carries beta and its nulls are brutal. Short pays borrow that this fixture cannot
measure. Spread removes the drift term. A signal can be excellent in one and
absent in another, and D290's whole point was to stop collapsing them.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
S1 = json.loads((REPO / "data" / "d290_stage1.json").read_text())
ENT = json.loads((REPO / "data" / "d290_entry_test.json").read_text())
SKIP = json.loads((REPO / "data" / "d290_skip_all.json").read_text())
AX = S1["axes"]
SKIPV = {r["c"]: r for r in SKIP["rows"]}
# GATE 1h: nulls for BOTH directions. D290 fixed long=lowest by fiat, so the
# reversed direction was never scored -- and it held wick_asym at t +10.51 with
# min z +5.07, which the study had dismissed at tier 3.
DIRN = json.loads((REPO / "data" / "d290_direction_nulls.json").read_text())["results"]
NMAX, KMAX = max(S1["n_levels"]), max(S1["horizons"])
CAPTURABLE_T = 2.0


def round_trip(c, con):
    cost = (S1["results"][c].get("cost_bp_per_side") or {})
    lo, sh = cost.get("long"), cost.get("short")
    if con == "long":
        return 2 * lo if lo else None
    if con == "short":
        return 2 * sh if sh else None
    return (2 * lo + 2 * sh) if (lo and sh) else None


def row(c, con):
    r = S1["results"][c]
    N, k, (bp, t, _) = r["observed"][con]
    cv = r["cv"][con][0]
    z = [r["z"][n][con] for n in ("rotation", "permutation", "tail")]
    mn = min(v for v in z if v is not None) if all(v is not None for v in z) else None
    e = (ENT["results"].get(c) or {}).get(str(N)) or {}
    ce = (e.get("close_entry") or {}).get(str(k))
    oe = (e.get("open_entry") or {}).get(str(k))
    on = e.get("overnight_k1")
    tot = e.get("total_k1")
    ce_v = ce[con] if ce else None
    oe_v = oe[con] if oe else None
    kept = (oe_v[0] / ce_v[0]) if (oe_v and ce_v and ce_v[0]) else None
    on_share = None
    if on and tot and tot[con][0]:
        on_share = on[con][0] / tot[con][0]
    rt = round_trip(c, con)
    real = mn is not None and mn > 0
    gen = cv > 0
    cap = oe_v is not None and oe_v[1] >= CAPTURABLE_T
    tier = 1 if (real and gen and cap) else 2 if (real and gen) else 3
    # GATE 1i: a peak at the edge of the sweep means the statistic was still
    # climbing when the grid ran out. Reported, and it demotes nothing on its own
    # -- but an edge peak is UNRESOLVED rather than concluded.
    edge = ("corner" if (N == NMAX and k == KMAX) else
            "edge" if (N == NMAX or k == KMAX) else "interior")
    return dict(c=c, ax=AX[c], N=N, k=k, bp=bp, t=t, cv=cv, mn=mn, edge=edge,
                oe_bp=oe_v[0] if oe_v else None, oe_t=oe_v[1] if oe_v else None,
                kept=kept, on_share=on_share, rt=rt,
                xbar=(bp / rt) if rt else None, tier=tier,
                skip=SKIPV.get(c, {}).get("verdict"))


def table(con, top):
    rows = [row(c, con) for c in S1["results"]]
    rows.sort(key=lambda r: (r["tier"], -(r["oe_t"] if r["oe_t"] is not None
                                          else -9e9)))
    label = {"long": "LONG-ONLY  (net long: carries beta)",
             "short": "SHORT-ONLY  (pays borrow, NOT in the cost column)",
             "spread": "SPREAD  (dollar-neutral: removes the drift term)"}[con]
    print(f"\n{'=' * 112}")
    print(f"  {label}")
    print(f"{'=' * 112}")
    print(f"  {'ax':2s} {'candidate':16s} {'N':>3s} {'k':>3s} | {'bp':>8s} "
          f"{'CV t':>6s} {'min z':>6s} | {'open bp':>8s} {'open t':>7s} "
          f"{'kept':>6s} | {'on%':>6s} | {'x bar':>6s} | tier")
    shown = 0
    for r in rows:
        if shown >= top and r["tier"] > 1:
            continue
        shown += 1
        f = lambda v, w, d=1: (f"{v:+{w}.{d}f}" if v is not None
                               else f"{'--':>{w}s}")            # noqa: E731
        print(f"  {r['ax']:2s} {r['c']:16s} {r['N']:3d} {r['k']:3d} | "
              f"{f(r['bp'], 8)} {f(r['cv'], 6, 2)} {f(r['mn'], 6, 2)} | "
              f"{f(r['oe_bp'], 8)} {f(r['oe_t'], 7, 2)} "
              f"{(f'{r[chr(107)+chr(101)+chr(112)+chr(116)]:+6.0%}' if r['kept'] is not None else '    --'):>6s} | "
              f"{(f'{r[chr(111)+chr(110)+chr(95)+chr(115)+chr(104)+chr(97)+chr(114)+chr(101)]:+6.0%}' if r['on_share'] is not None else '    --'):>6s} | "
              f"{f(r['xbar'], 6, 2)} | {r['tier']}")
    t1 = [r for r in rows if r["tier"] == 1]
    t2 = [r for r in rows if r["tier"] == 2]
    print(f"  TIER 1 (real, generalises, capturable): {len(t1)}   "
          f"TIER 2 (real but not capturable): {len(t2)}   "
          f"TIER 3: {len(rows) - len(t1) - len(t2)}")
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=14)
    a = ap.parse_args()
    print("D290 UNIFIED RANKING -- every diagnostic, three constructions")
    print("  real = min z > 0 on all three nulls | generalises = CV t > 0")
    print(f"  capturable = open-entry t >= {CAPTURABLE_T} | x bar = effect / "
          f"MEASURED round trip on names held")
    print("  on% = share of the k=1 return earned between the close and the next open")
    out = {con: table(con, a.top) for con in ("spread", "short", "long")}
    json.dump({"purpose": "D290's unified ranking: null survival, name-split "
                          "generalisation, entry capturability and measured cost, "
                          "ranked separately per construction.",
               "capturable_t": CAPTURABLE_T,
               "rows": out}, open(REPO / "data" / "d290_unified_rank.json", "w"),
              indent=1)
    print(f"\n  wrote data/d290_unified_rank.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
