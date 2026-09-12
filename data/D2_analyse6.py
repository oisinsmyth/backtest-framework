"""D2 [MEASURED IN BRIEF] step 4. The step-3 control FIRED and taught something:
the CROSS-SECTIONAL R^2 of fiscal-quarter-phase dummies was 0.0390 for the
single-quarter ratio and 0.0383 for the trailing-four-quarter ratio -- essentially
IDENTICAL (1.02x). A trailing-four-quarter sum cannot carry seasonality, so that
0.038 is NOT seasonality. In a cross-section a firm's fiscal-quarter phase is fixed
by its fiscal-year-end month, and fiscal-year-end month is correlated with industry
(Cramer's V 0.119 measured in step 1), which is correlated with the profitability
level. So the cross-sectional statistic measures COMPOSITION, not seasonality.

THE CLEAN ISOLATION IS WITHIN FIRM. Inside one firm, industry is constant and the
fiscal-year-end is constant, so the only thing the fiscal-quarter label can proxy
for is that firm's OWN seasonality. So:

  for each firm, regress its own cross-sectional PERCENTILE RANK on fiscal-quarter
  dummies, separately for the single-quarter and the trailing-four-quarter ratio.

NEGATIVE CONTROL, again built in and again able to fire: the trailing-four-quarter
ratio spans all four fiscal quarters whatever the phase, so its WITHIN-FIRM rank must
show little fiscal-quarter structure. Calibrated against an AR(1) surrogate null,
because with ~10 quarters four dummies absorb variance by construction (the mistake
the Assets control caught in pass 2).
"""
import pandas as pd, numpy as np, glob, json
from scipy import stats as sps

REV = ["Revenues", "SalesRevenueNet", "SalesRevenueGoodsNet",
       "RevenueFromContractWithCustomerExcludingAssessedTax",
       "RevenueFromContractWithCustomerIncludingAssessedTax"]
COST = ["CostOfGoodsSold", "CostOfGoodsAndServicesSold", "CostOfRevenue"]

df = pd.concat([pd.read_csv(f, dtype={"cik": str, "ddate": str, "fye": str,
                                      "sic": str, "filed": str})
                for f in sorted(glob.glob("D2_fsds_*_panel.csv"))],
               ignore_index=True)
df = df.sort_values("filed").drop_duplicates(["cik", "tag", "ddate", "qtrs"],
                                             keep="first")
df["fye"] = df.fye.fillna("").str.zfill(4)
df["dt"] = pd.to_datetime(df.ddate, format="%Y%m%d", errors="coerce")
df = df.dropna(subset=["dt"])
fye_m = pd.to_numeric(df.fye.str[:2], errors="coerce")
df["fq"] = ((df.dt.dt.month - fye_m) % 12).map({0: 4, 3: 1, 6: 2, 9: 3})
df = df[df.fq.notna()].copy()
df["fq"] = df.fq.astype(int)
meta = df.drop_duplicates("cik").set_index("cik")[["sic"]]


def sic_div(s):
    try:
        n = int(str(s)[:2])
    except Exception:
        return "??"
    for lo, hi, lab in [(1, 9, "A agric"), (10, 14, "B mining"), (15, 17, "C constr"),
                        (20, 39, "D manuf"), (40, 49, "E transp/util"),
                        (50, 51, "F wholesale"), (52, 59, "G retail"),
                        (60, 67, "H fin/ins/re"), (70, 89, "I services"),
                        (91, 99, "J public")]:
        if lo <= n <= hi:
            return lab
    return "??"


def flow(tags):
    sub = df[df.tag.isin(tags)]
    pick = (sub.groupby(["cik", "tag"]).size().reset_index(name="n")
            .sort_values("n", ascending=False).drop_duplicates("cik"))
    sub = sub.merge(pick[["cik", "tag"]], on=["cik", "tag"])
    nat = sub[sub.qtrs == 1][["cik", "dt", "fq", "value"]].copy()
    a4 = sub[sub.qtrs == 4][["cik", "dt", "fq", "value"]].rename(columns={"value": "v4"})
    y3 = sub[sub.qtrs == 3][["cik", "dt", "value"]].rename(columns={"value": "v3"})
    y3["dt"] = y3.dt + pd.DateOffset(months=3)
    der = a4.merge(y3, on=["cik", "dt"], how="inner")
    der["value"] = der.v4 - der.v3
    der = der[["cik", "dt", "fq", "value"]]
    key = set(zip(nat.cik, nat.dt))
    der = der[[k not in key for k in zip(der.cik, der.dt)]]
    return pd.concat([nat, der], ignore_index=True)


rev = flow(REV).rename(columns={"value": "rev"})
cost = flow(COST).rename(columns={"value": "cost"})
gp = rev.merge(cost[["cik", "dt", "cost"]], on=["cik", "dt"], how="inner")
gp["gp"] = gp.rev - gp.cost
at = df[df.tag == "Assets"][["cik", "dt", "value"]].rename(columns={"value": "tot_at"})
gp["qi"] = gp.dt.dt.year * 4 + (gp.dt.dt.month - 1) // 3
at["qi"] = at.dt.dt.year * 4 + (at.dt.dt.month - 1) // 3
gmap = {(c, q): float(v) for c, q, v in zip(gp.cik.values, gp.qi.values, gp.gp.values)}
amap = {(c, q): float(v) for c, q, v in zip(at.cik.values, at.qi.values, at.tot_at.values)}
rows = []
for cik, qi, fq in zip(gp.cik.values, gp.qi.values, gp.fq.values):
    g0, g1 = gmap.get((cik, qi)), gmap.get((cik, qi - 1))
    g2, g3 = gmap.get((cik, qi - 2)), gmap.get((cik, qi - 3))
    a1 = amap.get((cik, qi - 1))
    if None in (g0, g1, g2, g3, a1) or a1 <= 0:
        continue
    rows.append((cik, int(qi), int(fq), g0 / a1, (g0 + g1 + g2 + g3) / a1))
P = pd.DataFrame(rows, columns=["cik", "qi", "fq", "Sq", "Ttm"])
P["sicdiv"] = P.cik.map(lambda c: sic_div(meta.sic.get(c)))

# percentile rank WITHIN each formation quarter (so the level/scale drops out)
P["rS"] = P.groupby("qi").Sq.rank(pct=True)
P["rT"] = P.groupby("qi").Ttm.rank(pct=True)
print(f"panel: {len(P):,} firm-quarters, {P.cik.nunique():,} firms, "
      f"{P.qi.nunique()} quarters")

rng = np.random.default_rng(23)
NSUR = 300


def within_firm(s, col, min_obs=8):
    s = s.sort_values("qi")
    y = s[col].values.astype(float)
    fq = s.fq.values
    n = len(y)
    if n < min_obs or len(set(fq)) < 4:
        return None
    y = y - y.mean()
    sst = y @ y
    if sst <= 0:
        return None
    D = np.column_stack([(fq == k).astype(float) for k in (1, 2, 3, 4)])
    cnt = D.sum(0)
    b = np.linalg.lstsq(D, y, rcond=None)[0]
    r2 = 1 - ((y - D @ b) @ (y - D @ b)) / sst
    rho = np.clip(np.corrcoef(y[:-1], y[1:])[0, 1], -0.95, 0.95) if n > 3 else 0.0
    sig = np.std(y) * np.sqrt(max(1e-12, 1 - rho ** 2))
    z = rng.standard_normal((NSUR, n)) * sig
    sur = np.empty((NSUR, n))
    sur[:, 0] = z[:, 0] / np.sqrt(max(1e-12, 1 - rho ** 2))
    for i in range(1, n):
        sur[:, i] = rho * sur[:, i - 1] + z[:, i]
    sur = sur - sur.mean(1, keepdims=True)
    gm = (sur @ D) / np.where(cnt == 0, np.nan, cnt)
    fit = np.nansum(gm ** 2 * cnt, axis=1)
    r2s = fit / np.einsum("ij,ij->i", sur, sur)
    return r2, float(np.nanmean(r2s)), float((r2s >= r2).mean()), np.std(y), n


res = {}
for col, lab in [("rS", "SINGLE QUARTER rank"),
                 ("rT", "TRAILING 4 QTR rank  [NEG CONTROL]")]:
    out = []
    for cik, s in P.groupby("cik"):
        r = within_firm(s, col)
        if r:
            out.append((cik, *r))
    a = pd.DataFrame(out, columns=["cik", "r2", "r2_sur", "p_emp", "sd", "n"])
    a["excess"] = a.r2 - a.r2_sur
    res[lab] = a
    print(f"\n{lab}: firms {len(a)}")
    print(f"   within-firm R^2 of fiscal-quarter dummies : median {a.r2.median():.4f}")
    print(f"   AR(1) surrogate null                      : median {a.r2_sur.median():.4f}")
    print(f"   EXCESS over null                          : median {a.excess.median():+.4f}")
    print(f"   share of firms with p_emp < 0.05           : {100*(a.p_emp<0.05).mean():.1f}%")
    print(f"   median within-firm sd of the rank          : {a.sd.median():.4f}")

A = res["SINGLE QUARTER rank"].set_index("cik")
B = res["TRAILING 4 QTR rank  [NEG CONTROL]"].set_index("cik")
J = A.join(B, lsuffix="_S", rsuffix="_T", how="inner")
print(f"\nfirms with BOTH computed: {len(J)}")
print(f"  median excess R^2  single quarter  = {J.excess_S.median():+.4f}")
print(f"  median excess R^2  trailing 4 qtr  = {J.excess_T.median():+.4f}")
print(f"  paired difference (S - T)          = {(J.excess_S-J.excess_T).median():+.4f}")
t = sps.wilcoxon(J.excess_S, J.excess_T)
print(f"  Wilcoxon signed-rank on the pair: stat={t.statistic:.0f}, p={t.pvalue:.2e}")
print(f"  median within-firm rank sd: single quarter {J.sd_S.median():.4f} "
      f"vs trailing 4 qtr {J.sd_T.median():.4f}  "
      f"(ratio {J.sd_S.median()/J.sd_T.median():.2f}x)")

# by industry
J2 = J.join(P.drop_duplicates("cik").set_index("cik")[["sicdiv"]], how="left")
print(f"\nby industry division (median paired excess S - T):")
print(f"   {'division':<16}{'n':>5}{'exc_S':>9}{'exc_T':>9}{'S-T':>9}{'sdS/sdT':>9}")
for d, s in J2.groupby("sicdiv"):
    if len(s) < 20:
        continue
    print(f"   {d:<16}{len(s):>5}{s.excess_S.median():>9.4f}"
          f"{s.excess_T.median():>9.4f}{(s.excess_S-s.excess_T).median():>9.4f}"
          f"{s.sd_S.median()/s.sd_T.median():>9.2f}")

json.dump({k: dict(n=int(len(v)), r2=float(v.r2.median()),
                   r2_sur=float(v.r2_sur.median()),
                   excess=float(v.excess.median()),
                   share_p05=float(100*(v.p_emp < .05).mean()),
                   sd=float(v.sd.median())) for k, v in res.items()}
          | {"paired": dict(n=int(len(J)),
                            excess_S=float(J.excess_S.median()),
                            excess_T=float(J.excess_T.median()),
                            diff=float((J.excess_S-J.excess_T).median()),
                            wilcoxon_p=float(t.pvalue),
                            sd_ratio=float(J.sd_S.median()/J.sd_T.median()))},
          open("D2_withinfirm.json", "w"), indent=1)
print("\nwrote D2_withinfirm.json")
