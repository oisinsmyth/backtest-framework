"""B1 (Scan-100926 round 2) -- [MEASURED IN BRIEF] evidence for
docs/research/Scan-100926/R2-01-the-benchmark-question.md

QUESTION. A long leg's measured alpha is `leg - benchmark`. Two benchmarks are in
dispute for this programme: the VALUE-WEIGHTED market (lane A3 / Chen-Welch) and the
sort's own NAME-WEIGHTED (equal-weighted) universe (lane A2). Their difference is an
identity:

    (leg - VW market) = (leg - EW universe) + (EW universe - VW market)

so the whole benchmark disagreement is the size of the SECOND term. This script measures
that second term on free public data.

INPUTS -- both free, keyless, downloaded 2026-09-10; both state they were built from the
202607 CRSP database:
  https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_CSV.zip
  https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Portfolios_Formed_on_ME_CSV.zip
Unzip both into the working directory, then run:  python B1_ew_vs_vw_benchmark.py

CONSTRUCTIONS.
  VW market total return   = Mkt-RF + RF (French's own market factor = CRSP VW index).
  EW ("name-weighted") universe = sum_i n_i,t * rEW_i,t / sum_i n_i,t over ME deciles i,
    from French's "Average Equal Weighted Returns" and "Number of Firms in Portfolios".
    This is exactly a name-weighted average over every bin of a sort -- lane A2's benchmark.
  Screened variants partial-include the marginal decile at its name weight, i.e. they
  ASSUME WITHIN-DECILE HOMOGENEITY of returns. Stated as a caveat in the brief.

CONTROLS (campaign rule: a harvest with no negative control is not a measurement).
  POSITIVE: cap-weighting the decile VALUE-weighted returns must reproduce the CRSP VW
    market. Measured mean deviation +0.0044 %/mo, max |dev| 0.258 %/mo, sd 0.056 %/mo.
  NEGATIVE: the "<= 0" market-equity bucket must hold zero firms in the modern sample and
    must carry French's -99.99 missing flag. Both assert below.
"""
import sys, math, statistics

sys.stdout.reconfigure(encoding="utf-8")
DEC = ["Lo 10", "2-Dec", "3-Dec", "4-Dec", "5-Dec", "6-Dec", "7-Dec", "8-Dec", "9-Dec", "Hi 10"]


def read_block(path, header_text):
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    i = next(k for k, l in enumerate(lines) if l.strip().startswith(header_text))
    cols = [c.strip() for c in lines[i + 1].split(",")]
    out = {}
    for l in lines[i + 2:]:
        p = [x.strip() for x in l.split(",")]
        if not p[0].isdigit() or len(p[0]) != 6:
            break
        out[int(p[0])] = {c: float(v) for c, v in zip(cols[1:], p[1:])}
    return out


def read_ff():
    lines = open("F-F_Research_Data_Factors.csv", encoding="utf-8", errors="replace").read().splitlines()
    i = next(k for k, l in enumerate(lines) if l.strip().startswith(",Mkt-RF"))
    out = {}
    for l in lines[i + 1:]:
        p = [x.strip() for x in l.split(",")]
        if not p[0].isdigit() or len(p[0]) != 6:
            break
        out[int(p[0])] = dict(zip(["MktRF", "SMB", "HML", "RF"], map(float, p[1:5])))
    return out


ew = read_block("Portfolios_Formed_on_ME.csv", "Average Equal Weighted Returns -- Monthly")
vw = read_block("Portfolios_Formed_on_ME.csv", "Average Value Weight Returns -- Monthly")
nf = read_block("Portfolios_Formed_on_ME.csv", "Number of Firms in Portfolios")
sz = read_block("Portfolios_Formed_on_ME.csv", "Average Firm Size")
ff = read_ff()

ALL = [t for t in sorted(ff) if t in ew and t in nf and t in sz]
MODERN = [t for t in ALL if t >= 201001]

assert "Zz 99" not in ew[201001]                      # bogus column must not resolve
assert all(nf[t]["<= 0"] == 0 for t in MODERN)        # negative control: empty bucket
assert all(ew[t]["<= 0"] == -99.99 for t in MODERN)   # negative control: missing flag
_rec = [sum(nf[t][d] * sz[t][d] * vw[t][d] for d in DEC) / sum(nf[t][d] * sz[t][d] for d in DEC)
        for t in MODERN]
_mkt = [ff[t]["MktRF"] + ff[t]["RF"] for t in MODERN]
_dev = [a - b for a, b in zip(_rec, _mkt)]
assert abs(statistics.mean(_dev)) < 0.01 and max(abs(x) for x in _dev) < 0.30  # positive control
print("CONTROLS PASS: cap-weighted deciles reproduce CRSP VW market to "
      f"{statistics.mean(_dev):+.4f} %/mo mean, {max(abs(x) for x in _dev):.3f} %/mo max deviation; "
      "the <=0 market-equity bucket is empty and flagged -99.99 throughout 2010-2026.")


def ew_universe(t, keep):
    return sum(nf[t][d] * ew[t][d] for d in keep) / sum(nf[t][d] for d in keep)


def ew_topk(t, k):
    num, den, left = 0.0, 0.0, k
    for d in reversed(DEC):
        take = min(left, nf[t][d])
        if take <= 0:
            break
        num += take * ew[t][d]; den += take; left -= take
    return num / den


def ew_topcap(t, share):
    cap = {d: nf[t][d] * sz[t][d] for d in DEC}
    tot = sum(cap.values())
    num, den, acc = 0.0, 0.0, 0.0
    for d in reversed(DEC):
        if acc >= share * tot:
            break
        frac = min(1.0, (share * tot - acc) / cap[d])
        num += frac * nf[t][d] * ew[t][d]; den += frac * nf[t][d]; acc += cap[d]
    return num / den


def ols(y, x):
    n = len(y); mx, my = statistics.mean(x), statistics.mean(y)
    sxx = sum((a - mx) ** 2 for a in x)
    b = sum((a - mx) * (c - my) for a, c in zip(x, y)) / sxx
    a0 = my - b * mx
    resid = [c - a0 - b * a for a, c in zip(x, y)]
    s2 = sum(r * r for r in resid) / (n - 2)
    return a0, a0 / math.sqrt(s2 * (1.0 / n + mx * mx / sxx)), b, math.sqrt(s2 / sxx)


WINDOWS = [(201001, 202607, "THIS PROGRAMME'S WINDOW 2010-01..2026-07"),
           (200601, 202607, "post-2005 (Chen-Welch / Muravyev et al. era)"),
           (196307, 201812, "Blitz et al. 1963-07..2018-12"),
           (192607, 202607, "full CRSP history")]

for t0, t1, lab in WINDOWS:
    ts = [t for t in ALL if t0 <= t <= t1]
    mkt = [ff[t]["MktRF"] + ff[t]["RF"] for t in ts]
    print(f"\n=== {lab}   N={len(ts)} months, avg {statistics.mean([sum(nf[t][d] for d in DEC) for t in ts]):.0f} CRSP names")
    print(f"  VW market (CRSP VW): {statistics.mean(mkt):.3f} %/mo")
    rows = [("EW, all CRSP names", [ew_universe(t, DEC) for t in ts]),
            ("EW, largest 1573", [ew_topk(t, 1573) for t in ts]),
            ("EW, top 90% of cap", [ew_topcap(t, 0.90) for t in ts]),
            ("EW, ME deciles 4-10", [ew_universe(t, DEC[3:]) for t in ts]),
            ("EW, ME deciles 6-10", [ew_universe(t, DEC[5:]) for t in ts])]
    print(f"  {'name-weighted universe':<24}{'mean':>8}{'  minus VW mkt':>15}{'se':>8}{'t':>7}{'sd(gap)':>9}"
          f"{'CAPM a':>9}{'t(a)':>7}{'beta':>7}")
    for name, s in rows:
        d = [a - b for a, b in zip(s, mkt)]
        m, sd, n = statistics.mean(d), statistics.stdev(d), len(d)
        se = sd / math.sqrt(n)
        a0, ta, beta, seb = ols([v - ff[t]["RF"] for v, t in zip(s, ts)], [ff[t]["MktRF"] for t in ts])
        print(f"  {name:<24}{statistics.mean(s):>8.3f}{m:>15.3f}{se:>8.3f}{m/se:>7.2f}{sd:>9.2f}"
              f"{a0:>9.3f}{ta:>7.2f}{beta:>7.3f}")

print("""
READING. The 'minus VW mkt' column IS the benchmark disagreement, in %/month, added to any
equal-weighted long leg's measured alpha when the benchmark is switched from the
value-weighted market to the sort's own name-weighted universe. 'sd(gap)' is the monthly
volatility that the mismatched benchmark injects into every leg series -- the mechanism by
which a mismatched benchmark shrinks every t-statistic and hence the cross-sectional Var(t).
'beta' is the name-weighted universe's beta on the VW market: a simple subtraction imposes
beta = 1 and therefore leaves a beta bet of (beta - 1) inside the reported alpha.""")
