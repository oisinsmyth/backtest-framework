"""D2 [MEASURED IN BRIEF] step 3 -- THE DECISIVE CHARACTERISTIC-LEVEL TEST.

A lane with no return fixture cannot measure what a sort EARNS. It can measure
whether the two sorts are THE SAME SORT, and whether the single-quarter one is
contaminated by fiscal-quarter phase while the trailing-four-quarter one is not.

At each formation quarter-end D, for every firm with the data:
    S(D) = GP(D)                                  / AT(D-1q)   SINGLE QUARTER
    T(D) = GP(D)+GP(D-1)+GP(D-2)+GP(D-3)          / AT(D-1q)   TRAILING FOUR QUARTERS
  where GP = Revenues - CostOfGoodsSold, both single-quarter (qtrs=1, segments empty),
  and AT = Assets one quarter earlier (the Hou-Xue-Zhang / Chen-Zimmermann deflator).

Reported per formation quarter and then pooled:
  * Spearman rank correlation between S and T  -- do they rank the same names?
  * top-decile and bottom-decile overlap       -- would they HOLD the same names?
  * R^2 of FISCAL-QUARTER PHASE dummies on the cross-sectional rank of each

NEGATIVE CONTROL, and it is built into the construction: a trailing-four-quarter sum
spans all four fiscal quarters WHATEVER the firm's phase, so T's cross-sectional rank
MUST be almost unrelated to fiscal-quarter phase. If T loads on phase as much as S
does, the measurement is broken rather than informative.
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
meta = df.drop_duplicates("cik").set_index("cik")[["sic", "fye"]]


def sic_div(s):
    try:
        n = int(str(s)[:2])
    except Exception:
        return "??"
    for lo, hi, lab in [(1, 9, "A"), (10, 14, "B"), (15, 17, "C"), (20, 39, "D"),
                        (40, 49, "E"), (50, 51, "F"), (52, 59, "G"),
                        (60, 67, "H"), (70, 89, "I"), (91, 99, "J")]:
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
at = (df[df.tag == "Assets"][["cik", "dt", "value"]]
      .rename(columns={"value": "tot_at"}))
print(f"single-quarter GP observations: {len(gp):,} over {gp.cik.nunique():,} firms")
print(f"Assets observations:            {len(at):,} over {at.cik.nunique():,} firms")

# quarter index so lags are unambiguous
gp["qi"] = gp.dt.dt.year * 4 + (gp.dt.dt.month - 1) // 3
at["qi"] = at.dt.dt.year * 4 + (at.dt.dt.month - 1) // 3
rows = []
gmap = {(c, q): float(v) for c, q, v in
        zip(gp.cik.values, gp.qi.values, gp.gp.values)}
amap = {(c, q): float(v) for c, q, v in
        zip(at.cik.values, at.qi.values, at.tot_at.values)}
for cik, qi, fq in zip(gp.cik.values, gp.qi.values, gp.fq.values):
    g0 = gmap.get((cik, qi))
    g1 = gmap.get((cik, qi - 1))
    g2 = gmap.get((cik, qi - 2))
    g3 = gmap.get((cik, qi - 3))
    a1 = amap.get((cik, qi - 1))
    if None in (g0, g1, g2, g3, a1) or a1 <= 0:
        continue
    rows.append((cik, int(qi), int(fq), g0 / a1, (g0 + g1 + g2 + g3) / a1))
P = pd.DataFrame(rows, columns=["cik", "qi", "fq", "Sq", "Ttm"])
P.Sq = pd.to_numeric(P.Sq, errors="coerce").astype(float)
P.Ttm = pd.to_numeric(P.Ttm, errors="coerce").astype(float)
P = P[np.isfinite(P.Sq.values) & np.isfinite(P.Ttm.values)]
P["sicdiv"] = P.cik.map(lambda c: sic_div(meta.sic.get(c)))
print(f"\nformation observations with BOTH constructions computable: {len(P):,} "
      f"over {P.cik.nunique():,} firms and {P.qi.nunique()} quarters")
print(f"NOTE single-quarter S is 1 quarter of GP over lagged assets; T is 4 quarters")
print(f"over the SAME lagged assets, so T is ~4x the level of S by construction:")
print(f"  median S = {P.Sq.median():.4f}   median T = {P.Ttm.median():.4f}   "
       f"ratio {P.Ttm.median()/P.Sq.median():.2f}")


def dec_overlap(a, b, q=0.1, top=True):
    n = len(a)
    k = max(1, int(round(q * n)))
    ia = np.argsort(a.values)
    ib = np.argsort(b.values)
    sa = set(ia[-k:] if top else ia[:k])
    sb = set(ib[-k:] if top else ib[:k])
    return len(sa & sb) / k


def r2_dummies(rank, labels):
    lv = pd.Categorical(labels)
    D = np.column_stack([(lv.codes == i).astype(float)
                         for i in range(len(lv.categories))])
    y = rank - rank.mean()
    b = np.linalg.lstsq(D, y, rcond=None)[0]
    r = y - D @ b
    sst = y @ y
    return 1 - (r @ r) / sst if sst > 0 else np.nan


out = []
for qi, s in P.groupby("qi"):
    if len(s) < 150:
        continue
    rs = sps.spearmanr(s.Sq, s.Ttm).statistic
    rS = sps.rankdata(s.Sq) / len(s)
    rT = sps.rankdata(s.Ttm) / len(s)
    out.append(dict(qi=qi, n=len(s), spearman=rs,
                    top_dec=dec_overlap(s.Sq, s.Ttm, top=True),
                    bot_dec=dec_overlap(s.Sq, s.Ttm, top=False),
                    r2_phase_S=r2_dummies(rS, s.fq.values),
                    r2_phase_T=r2_dummies(rT, s.fq.values),
                    r2_ind_S=r2_dummies(rS, s.sicdiv.values),
                    r2_ind_T=r2_dummies(rT, s.sicdiv.values)))
R = pd.DataFrame(out)
print(f"\nformation quarters with n>=150: {len(R)}  (median n = {R.n.median():.0f})")
print("\n(C) DO THE TWO CONSTRUCTIONS RANK THE SAME NAMES? median across quarters")
print(f"   Spearman rank corr(single quarter, trailing 4 quarters) = "
      f"{R.spearman.median():.3f}  [min {R.spearman.min():.3f}, max {R.spearman.max():.3f}]")
print(f"   TOP-decile overlap     = {R.top_dec.median():.3f}  "
      f"(1.00 = identical long leg; 0.10 = random)")
print(f"   BOTTOM-decile overlap  = {R.bot_dec.median():.3f}")
print("\n(C2) IS THE SINGLE-QUARTER RANK CONTAMINATED BY FISCAL-QUARTER PHASE?")
print(f"   R^2 of fiscal-quarter-phase dummies on the cross-sectional rank")
print(f"     SINGLE QUARTER  : {R.r2_phase_S.median():.5f}")
print(f"     TRAILING 4 QTRS : {R.r2_phase_T.median():.5f}   <-- NEGATIVE CONTROL,")
print(f"       must be near zero: a 4-quarter sum spans every phase by construction")
print(f"   ratio S/T = {R.r2_phase_S.median()/max(1e-9,R.r2_phase_T.median()):.2f}x")
print(f"\n   for scale, R^2 of INDUSTRY DIVISION dummies on the same ranks:")
print(f"     SINGLE QUARTER  : {R.r2_ind_S.median():.5f}")
print(f"     TRAILING 4 QTRS : {R.r2_ind_T.median():.5f}")

json.dump(dict(n_obs=int(len(P)), n_firms=int(P.cik.nunique()),
               n_quarters=int(len(R)),
               spearman_med=float(R.spearman.median()),
               top_dec=float(R.top_dec.median()), bot_dec=float(R.bot_dec.median()),
               r2_phase_S=float(R.r2_phase_S.median()),
               r2_phase_T=float(R.r2_phase_T.median()),
               r2_ind_S=float(R.r2_ind_S.median()),
               r2_ind_T=float(R.r2_ind_T.median())),
          open("D2_sq_vs_ttm.json", "w"), indent=1)
R.to_csv("D2_sq_vs_ttm_byquarter.csv", index=False)
print("\nwrote D2_sq_vs_ttm.json, D2_sq_vs_ttm_byquarter.csv")
