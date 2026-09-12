"""D4 REGIME SPLIT -- an independent check of Asness/Frazzini/Pedersen's recession claim
on a different construction (French's OP deciles and RMW, not QMJ).

NBER US contraction months are written out explicitly below as [month after the peak ..
trough month]. They are public and fixed; they are NOT read from any file.

CONTROLS
  C-R1  the VW MARKET EXCESS RETURN must be clearly NEGATIVE in the recession months.
        If it is not, the recession dating is wrong and nothing below is usable.
  C-R2  the recession and expansion month counts must sum to n exactly.
  C-R3  a deliberately WRONG dating (every recession shifted +60 months) must destroy C-R1 --
        i.e. the control must be capable of failing.
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from D4_defs import *
from D4_measure import moments, read_block

NBER = [("1969-12", "1970-11"), ("1973-12", "1975-03"), ("1980-02", "1980-07"),
        ("1981-08", "1982-11"), ("1990-08", "1991-03"), ("2001-04", "2001-11"),
        ("2008-01", "2009-06"), ("2020-03", "2020-04")]


def shift(m, k):
    y, mo = int(m[:4]), int(m[5:])
    t = y * 12 + (mo - 1) + k
    return "%04d-%02d" % (t // 12, t % 12 + 1)


def is_rec(m, off=0):
    return any(shift(a, off) <= m <= shift(b, off) for a, b in NBER)


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

TARGETS = {
    "OP Hi10 VW - VW market (LONG LEG)": SER["OP Hi10 VW - VW market"],
    "OP Hi10 VW - VW universe TRUE (LONG LEG)": {m: dec(op_vw, iop, "Hi 10")[m] - vw_univ[m]
                                                 for m in vw_univ if m in dec(op_vw, iop, "Hi 10")},
    "OP Hi10-Lo10 VW (SPREAD)": SER["OP Hi10-Lo10 VW spread"],
    "OP Lo10 VW - VW market (SHORT LEG)": SER["OP Lo10 VW - VW market"],
    "RMW published spread": SER["RMW published 2x3 spread"],
    "HML published spread": SER["HML published 2x3 spread"],
    "CONTROL market excess Mkt-RF": SER["CTRL market excess Mkt-RF"],
}

OUT = {}
for off in (0, 60):
    blk = {}
    for lab, d in TARGETS.items():
        months = sorted(d)
        rec = [d[m] for m in months if is_rec(m, off)]
        exp = [d[m] for m in months if not is_rec(m, off)]
        if len(rec) < 12:
            continue
        mr, me = moments(rec), moments(exp)
        # difference in means, unequal variances
        se = math.sqrt(mr["sd"] ** 2 / mr["n"] + me["sd"] ** 2 / me["n"])
        blk[lab] = dict(n_total=len(months), n_rec=mr["n"], n_exp=me["n"],
                        rec_mean=round(mr["mean"], 4), rec_t=round(mr["t"], 2),
                        exp_mean=round(me["mean"], 4), exp_t=round(me["t"], 2),
                        diff=round(mr["mean"] - me["mean"], 4),
                        diff_t=round((mr["mean"] - me["mean"]) / se, 2),
                        ratio=(round(mr["mean"] / me["mean"], 2) if me["mean"] else None))
    OUT["offset_%dmo" % off] = blk

mk0 = OUT["offset_0mo"]["CONTROL market excess Mkt-RF"]
mk60 = OUT["offset_60mo"]["CONTROL market excess Mkt-RF"]
OUT["_CONTROLS"] = {
    "C-R1 market excess in recessions must be clearly negative": mk0["rec_mean"],
    "C-R1 PASS": mk0["rec_mean"] < -0.5,
    "C-R2 counts sum": mk0["n_rec"] + mk0["n_exp"] == mk0["n_total"],
    "C-R3 wrong dating (+60mo) market-in-recession mean": mk60["rec_mean"],
    "C-R3 PASS (the control CAN fail: wrong dating does not give a clearly negative market)":
        not (mk60["rec_mean"] < -0.5),
    "n_recession_months_in_sample": mk0["n_rec"],
}
json.dump(OUT, open(os.path.join(HERE, "D4_regime.json"), "w"), indent=1, default=str)
print(json.dumps(OUT["_CONTROLS"], indent=1))
print()
print("series".ljust(44) + "n_rec  rec_mean  rec_t   exp_mean  exp_t   diff    diff_t  ratio")
for lab, r in OUT["offset_0mo"].items():
    print(lab[:43].ljust(44) + "%-6d %-9s %-7s %-9s %-7s %-7s %-7s %s" % (
        r["n_rec"], r["rec_mean"], r["rec_t"], r["exp_mean"], r["exp_t"], r["diff"],
        r["diff_t"], r["ratio"]))
