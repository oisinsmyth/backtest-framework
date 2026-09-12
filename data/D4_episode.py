"""D4 THE EPISODE TEST -- drop the single clustered window and report what is left,
and then drop the WORST window of the same length so the test is symmetric.

CONTROL: dropping a window must leave n reduced by exactly the window length.
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from D4_defs import *
from D4_measure import moments, read_block

h_sz, cols_sz, op_sz, cen_sz = read_block("D4_Portfolios_Formed_on_OP_CSV.zip", "Average Firm Size")
isz = {c: j for j, c in enumerate(cols_sz)}
vw_univ = {}
for m in sorted(op_vw):
    if m not in op_nf or m not in op_sz:
        continue
    n = [op_nf[m][inf[c]] for c in DEC]
    rv = [op_vw[m][iop[c]] for c in DEC]
    s = [op_sz[m][isz[c]] for c in DEC]
    if any(x is None for x in n + rv + s):
        continue
    cap = [n[i] * s[i] for i in range(10)]
    vw_univ[m] = sum(cap[i] * rv[i] for i in range(10)) / sum(cap)

T = {
    "OP Hi10 VW - VW market (LONG)": SER["OP Hi10 VW - VW market"],
    "OP Hi10 VW - VW universe TRUE (LONG)": {m: dec(op_vw, iop, "Hi 10")[m] - vw_univ[m]
                                             for m in vw_univ if m in dec(op_vw, iop, "Hi 10")},
    "OP Hi10-Lo10 VW (SPREAD)": SER["OP Hi10-Lo10 VW spread"],
    "RMW published spread": SER["RMW published 2x3 spread"],
    "HML published spread": SER["HML published 2x3 spread"],
    "CONTROL market excess Mkt-RF": SER["CTRL market excess Mkt-RF"],
}

# windows are the BEST windows my permutation test identified, plus their mirror image
CASES = [
    ("in-sample 1963-07..2013-12", ("1963-07", "2013-12"),
     [("best 36mo dot-com unwind", "2000-03", "2003-02"),
      ("best 12mo", "2000-10", "2001-09")]),
    ("full 1963-07..2026-07", ("1963-07", "2026-07"),
     [("best 36mo dot-com unwind", "2000-03", "2003-02")]),
    ("post-pub 2014-01..2024-12", ("2014-01", "2024-12"),
     [("best 12mo 2022 rate shock", "2021-11", "2022-10"),
      ("best 36mo", "2021-10", "2024-09")]),
]

OUT = {}
ctrl_ok = True
for wl, (a, b), wins in CASES:
    OUT[wl] = {}
    for lab, d in T.items():
        months = sorted(m for m in d if a <= m <= b)
        if len(months) < 60:
            continue
        xs = [d[m] for m in months]
        mo = moments(xs)
        row = {"full": dict(n=mo["n"], mean=round(mo["mean"], 4), t=round(mo["t"], 2))}
        for nm, wa, wb in wins:
            keep = [d[m] for m in months if not (wa <= m <= wb)]
            drop = [d[m] for m in months if wa <= m <= wb]
            if len(drop) == 0:
                continue
            mk = moments(keep)
            row["EXCL " + nm] = dict(n=mk["n"], n_dropped=len(drop),
                                     mean=round(mk["mean"], 4), t=round(mk["t"], 2),
                                     dropped_window_mean=round(sum(drop) / len(drop), 4),
                                     share_of_total_sum=(round(sum(drop) / sum(xs), 3)
                                                         if sum(xs) > 0 else None))
            # SYMMETRIC mirror: drop the WORST window of the same length instead
            L = len(drop)
            worst_i, worst_v = None, None
            for i in range(len(xs) - L + 1):
                v = sum(xs[i:i + L])
                if worst_v is None or v < worst_v:
                    worst_i, worst_v = i, v
            keep2 = xs[:worst_i] + xs[worst_i + L:]
            m2 = moments(keep2)
            row["MIRROR excl worst %dmo" % L] = dict(
                window=[months[worst_i], months[worst_i + L - 1]], n=m2["n"],
                mean=round(m2["mean"], 4), t=round(m2["t"], 2),
                share_of_total_sum=(round(worst_v / sum(xs), 3) if sum(xs) > 0 else None))
            if mk["n"] != mo["n"] - L:
                ctrl_ok = False
        OUT[wl][lab] = row

OUT["_CONTROL_n_reduced_by_window_length"] = ctrl_ok
json.dump(OUT, open(os.path.join(HERE, "D4_episode.json"), "w"), indent=1, default=str)
print("CONTROL n-reduction:", "PASS" if ctrl_ok else "FAIL")
for wl in OUT:
    if wl.startswith("_"):
        continue
    print("\n===", wl)
    for lab, row in OUT[wl].items():
        print("  " + lab)
        for k, v in row.items():
            print("     %-34s n=%-5s mean=%-9s t=%-7s %s" % (
                k[:34], v["n"], v["mean"], v["t"],
                ("share=%s" % v.get("share_of_total_sum", "")) if "share_of_total_sum" in v else ""))
