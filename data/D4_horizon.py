"""D4 HOW LONG MUST IT BE HELD? Three answers to one question, on the same series.

  (1) (z/IR)^2 -- the closed form round 3 used, written out for z = 2 (expect t = 2) and
      z = 1.645 (95% sure the REALISED premium is positive). They are not the same question.
  (2) the OVERLAPPING-WINDOW empirical frequency: of all actual H-month windows in the
      history, what share were negative? Preserves every bit of autocorrelation and clustering.
  (3) an IID BOOTSTRAP of H months drawn with replacement: destroys clustering, keeps the
      marginal. The gap between (2) and (3) IS the effect of clustering on the required horizon.

CONTROLS
  C-H1 a zero-variance series must give P(negative) = 0 at every horizon, and a zero-mean
       series must give P(negative) ~ 0.50.
  C-H2 the overlapping-window count must equal n - H + 1 exactly.
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from D4_defs import *
from D4_measure import moments, read_block

HOR = [36, 60, 120, 240, 360]
OUTH = {}


def overlapping(xs, H):
    if len(xs) < H:
        return None
    wins = [sum(xs[i:i + H]) for i in range(len(xs) - H + 1)]
    neg = sum(1 for w in wins if w < 0)
    wins_s = sorted(wins)
    return dict(n_windows=len(wins), frac_negative=neg / len(wins),
                p05=wins_s[int(0.05 * (len(wins) - 1))], p50=wins_s[len(wins) // 2],
                worst=wins_s[0], best=wins_s[-1])


def boot(xs, H, draws, seed):
    rng = random.Random(seed)
    n = len(xs)
    neg = 0
    tot = []
    for _ in range(draws):
        s = 0.0
        for _ in range(H):
            s += xs[rng.randrange(n)]
        tot.append(s)
        if s < 0:
            neg += 1
    tot.sort()
    return dict(draws=draws, frac_negative=neg / draws,
                p05=tot[int(0.05 * (draws - 1))], p50=tot[draws // 2])


def closed(mean, sd, H):
    """Normal approximation: P(sum over H months < 0) = Phi(-mean*sqrt(H)/sd)."""
    z = mean * math.sqrt(H) / sd
    return 0.5 * (1.0 - math.erf(z / math.sqrt(2.0)))


# ---- C-H1: the self-test
OUTH["_CH1_selftest"] = {
    "zero_variance_pos_mean_frac_neg_expect_0": overlapping([0.3] * 400, 120)["frac_negative"],
    "zero_mean_frac_neg_boot_expect_~0.50": round(boot([1.0, -1.0] * 200, 120, 4000, 5)["frac_negative"], 3),
    "overlap_count_expect_281": overlapping([0.1] * 400, 120)["n_windows"],
}
OUTH["_CH1_PASS"] = (OUTH["_CH1_selftest"]["zero_variance_pos_mean_frac_neg_expect_0"] == 0.0
                     and 0.44 < OUTH["_CH1_selftest"]["zero_mean_frac_neg_boot_expect_~0.50"] < 0.56
                     and OUTH["_CH1_selftest"]["overlap_count_expect_281"] == 281)

# ---- the true universes, rebuilt as in part 3
h_sz, cols_sz, op_sz, cen_sz = read_block("D4_Portfolios_Formed_on_OP_CSV.zip", "Average Firm Size")
isz = {c: j for j, c in enumerate(cols_sz)}
vw_univ, ew_univ = {}, {}
for m in sorted(op_vw):
    if m not in op_nf or m not in op_sz or m not in op_ew:
        continue
    n = [op_nf[m][inf[c]] for c in DEC]
    rv = [op_vw[m][iop[c]] for c in DEC]
    re_ = [op_ew[m][iope[c]] for c in DEC]
    s = [op_sz[m][isz[c]] for c in DEC]
    if any(x is None for x in n + rv + re_ + s):
        continue
    cap = [n[i] * s[i] for i in range(10)]
    vw_univ[m] = sum(cap[i] * rv[i] for i in range(10)) / sum(cap)
    ew_univ[m] = sum(n[i] * re_[i] for i in range(10)) / sum(n)

TARGETS = {
    "OP Hi10 VW - VW market": SER["OP Hi10 VW - VW market"],
    "OP Hi10 VW - VW universe TRUE": {m: dec(op_vw, iop, "Hi 10")[m] - vw_univ[m]
                                      for m in vw_univ if m in dec(op_vw, iop, "Hi 10")},
    "OP Hi10 EW - EW universe TRUE": {m: dec(op_ew, iope, "Hi 10")[m] - ew_univ[m]
                                      for m in ew_univ if m in dec(op_ew, iope, "Hi 10")},
    "RMW published spread": SER["RMW published 2x3 spread"],
    "HML published spread": SER["HML published 2x3 spread"],
    "BM Hi10 VW - VW market": SER["BM Hi10 VW - VW market"],
    "CTRL market excess Mkt-RF": SER["CTRL market excess Mkt-RF"],
}

for lab, d in TARGETS.items():
    months = sorted(d)
    xs = [d[m] for m in months]
    mo = moments(xs)
    ir = mo["mean"] / mo["sd"] * math.sqrt(12)
    rec = dict(window=[months[0], months[-1]], n=mo["n"], mean_pct_mo=round(mo["mean"], 4),
               sd_pct_mo=round(mo["sd"], 3), t=round(mo["t"], 2), ann_IR=round(ir, 4),
               years_for_Et_eq_2=(round((2.0 / ir) ** 2, 1) if ir > 0 else None),
               years_for_95pct_sure_positive=(round((1.6449 / ir) ** 2, 1) if ir > 0 else None))
    for H in HOR:
        ov = overlapping(xs, H)
        bt = boot(xs, H, 20000, 9090 + H)
        rec["H=%dmo (%.0fy)" % (H, H / 12)] = dict(
            closed_form_P_neg=round(closed(mo["mean"], mo["sd"], H), 4),
            overlapping_frac_neg=(round(ov["frac_negative"], 4) if ov else None),
            overlapping_n=(ov["n_windows"] if ov else None),
            bootstrap_frac_neg=round(bt["frac_negative"], 4),
            overlapping_worst_sum_pct=(round(ov["worst"], 1) if ov else None),
            overlapping_median_sum_pct=(round(ov["p50"], 1) if ov else None))
    OUTH[lab] = rec

json.dump(OUTH, open(os.path.join(HERE, "D4_horizon.json"), "w"), indent=1, default=str)
print("C-H1:", OUTH["_CH1_selftest"], "PASS" if OUTH["_CH1_PASS"] else "FAIL")
print()
hdr = ["series", "n", "mean", "IR", "yrs E[t]=2", "yrs 95% pos"] + ["P(neg) %dy  ov/boot" % (H // 12) for H in HOR]
print("".join(h.ljust(22) for h in hdr))
for lab, r in OUTH.items():
    if lab.startswith("_"):
        continue
    row = [lab[:21], str(r["n"]), str(r["mean_pct_mo"]), str(r["ann_IR"]),
           str(r["years_for_Et_eq_2"]), str(r["years_for_95pct_sure_positive"])]
    for H in HOR:
        k = "H=%dmo (%.0fy)" % (H, H / 12)
        row.append("%s / %s" % (r[k]["overlapping_frac_neg"], r[k]["bootstrap_frac_neg"]))
    print("".join(c.ljust(22) for c in row))
