"""D4 analysis, part 3.

(A) A BENCHMARK CATCH. French's OP deciles use NYSE breakpoints, so the ten deciles hold
    wildly different numbers of firms (Lo 10 averages 967, Hi 10 averages 322). The simple
    mean of ten decile returns is therefore NOT the sort's equal-weighted universe. Rebuild
    both universes exactly from the file's own blocks:
       EW universe = sum(n_d * r_d^EW) / sum(n_d)
       VW universe = sum(n_d * size_d * r_d^VW) / sum(n_d * size_d)
    and report how far the naive simple-mean benchmark is from each.

(B) CALIBRATION OF THE TWO ALARMING NUMBERS, under an iid Gaussian with matched t and T:
    months-to-half, and the worst leave-one-year-out mean as a fraction of the full mean.
    No fat tails, no clustering, no events -- so whatever this produces is the part of the
    alarming number that carries no information beyond t and T.
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from D4_defs import *
from D4_measure import k_half, moments, read_block

OUT3 = {}

# ---------------------------------------------------------------- (A)
h_sz, cols_sz, op_sz, cen_sz = read_block("D4_Portfolios_Formed_on_OP_CSV.zip", "Average Firm Size")
isz = {c: j for j, c in enumerate(cols_sz)}
OUT3["_A0_avg_firm_size_block"] = {"header": h_sz, "sentinels": dict(cen_sz),
                                   "n_months": len(op_sz)}

ew_univ_true, vw_univ_true, ew_univ_naive, vw_univ_naive = {}, {}, {}, {}
for m in sorted(op_ew):
    if m not in op_nf or m not in op_sz or m not in op_vw:
        continue
    n = [op_nf[m][inf[c]] for c in DEC]
    re_ = [op_ew[m][iope[c]] for c in DEC]
    rv = [op_vw[m][iop[c]] for c in DEC]
    s = [op_sz[m][isz[c]] for c in DEC]
    if any(x is None for x in n + re_ + rv + s):
        continue
    ew_univ_true[m] = sum(n[i] * re_[i] for i in range(10)) / sum(n)
    cap = [n[i] * s[i] for i in range(10)]
    vw_univ_true[m] = sum(cap[i] * rv[i] for i in range(10)) / sum(cap)
    ew_univ_naive[m] = sum(re_) / 10.0
    vw_univ_naive[m] = sum(rv) / 10.0

hi_ew = dec(op_ew, iope, "Hi 10")
hi_vw = dec(op_vw, iop, "Hi 10")


def t_of(xs):
    mo = moments(xs)
    return mo["mean"], mo["t"], mo["n"]


A = {}
for wl, (a, b) in WINDOWS.items():
    blk = {}
    for nm, leg, bm in (("EW long - EW universe TRUE", hi_ew, ew_univ_true),
                        ("EW long - simple mean of deciles", hi_ew, ew_univ_naive),
                        ("VW long - VW universe TRUE", hi_vw, vw_univ_true),
                        ("VW long - simple mean of deciles", hi_vw, vw_univ_naive),
                        ("EW universe TRUE - simple mean (the benchmark error itself)",
                         ew_univ_true, ew_univ_naive),
                        ("VW universe TRUE - VW market (size tilt of the sort's universe)",
                         vw_univ_true, MKT)):
        months = sorted(m for m in leg if m in bm and a <= m <= b)
        if len(months) < 36:
            continue
        xs = [leg[m] - bm[m] for m in months]
        mean, t, n = t_of(xs)
        kh, tot = k_half(xs)
        blk[nm] = dict(mean=round(mean, 4), t=round(t, 2), n=n, k_half=kh)
    A[wl] = blk
OUT3["A_benchmark_catch"] = A

# ---------------------------------------------------------------- (B)
def calib(T, t, draws, seed, years=None):
    """iid Gaussian, sd 1, mean t/sqrt(T). Returns the null distribution of
    (i) k_half and (ii) worst-LOO-year mean / full mean."""
    years = years or max(1, T // 12)
    rng = random.Random(seed)
    per = T // years
    khs, ratios, dropq = [], [], []
    for _ in range(draws):
        xs = [rng.gauss(t / math.sqrt(T), 1.0) for _ in range(T)]
        kh, tot = k_half(xs)
        if kh is not None:
            khs.append(kh)
        full = sum(xs) / T
        if full <= 0:
            continue
        worst = None
        for y in range(years):
            f = xs[:y * per] + xs[(y + 1) * per:]
            mm = sum(f) / len(f)
            if worst is None or mm < worst:
                worst = mm
        ratios.append(worst / full)
        s = sorted(xs)
        dropq.append((sum(s[:-3]) / (T - 3)) / full)     # drop the best 3 months
    khs.sort(); ratios.sort(); dropq.sort()

    def q(v, p):
        return v[int(p * (len(v) - 1))]
    return dict(T=T, t=t, years=years, draws=draws,
                k_half={"p05": q(khs, .05), "p50": q(khs, .5), "p95": q(khs, .95),
                        "mean": round(sum(khs) / len(khs), 2)},
                worst_LOO_over_full={"p05": round(q(ratios, .05), 3), "p50": round(q(ratios, .5), 3),
                                     "p95": round(q(ratios, .95), 3),
                                     "frac_below_0.50": round(sum(1 for r in ratios if r < 0.5) / len(ratios), 3),
                                     "frac_below_0.40": round(sum(1 for r in ratios if r < 0.4) / len(ratios), 3)},
                drop_best3_over_full={"p05": round(q(dropq, .05), 3), "p50": round(q(dropq, .5), 3),
                                      "p95": round(q(dropq, .95), 3)})


B = {}
for t in (0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0):
    B["T=132 t=%.2f" % t] = calib(132, t, 3000, 31337, years=11)
OUT3["B_calibration_T132"] = B

json.dump(OUT3, open(os.path.join(HERE, "D4_part3.json"), "w"), indent=1, default=str)
print(json.dumps(OUT3["A_benchmark_catch"], indent=1))
print("--- calibration ---")
for k, v in B.items():
    print(k, "k_half", v["k_half"], "worstLOO/full", v["worst_LOO_over_full"])
