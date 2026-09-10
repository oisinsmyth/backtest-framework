"""D2 [MEASURED IN BRIEF] step 2. Three things the literature does not contain:

  (A) HOW SEASONAL ARE THE ACTUAL SORTED INPUTS? Share of DE-TRENDED within-firm
      variance in Revenues / CostOfGoodsSold / SG&A explained by FISCAL-QUARTER
      PHASE, plus the peak-to-trough amplitude as a multiple of the firm's mean.
      NEGATIVE CONTROL: `Assets` is an INSTANT (a stock), not a flow. It must show
      far less fiscal-quarter structure. If it does not, the method is broken.
      De-trending matters: with ~3 years of data a growth trend would otherwise
      load onto the quarter dummies and the control could not fire.

  (B) THE FISCAL-YEAR-END DISTRIBUTION, and whether it is INDEPENDENT OF INDUSTRY
      -- because if it is not, a seasonal artefact is indistinguishable from an
      industry bet. NEGATIVE CONTROL: a randomly permuted fye must show ~zero
      association with industry under the same statistic.

  (C) DO THE SINGLE-QUARTER AND TRAILING-FOUR-QUARTER GROSS-PROFITABILITY SORTS
      PICK THE SAME NAMES? Cross-sectional Spearman rank correlation and decile
      overlap. This is the decisive question asked of the CHARACTERISTIC rather
      than of returns, which is all a lane with no return fixture can ask.

Source: SEC FSDS 2021q4-2024q4, parsed by D2_extract.py (controls in D2_extract.log).
`prevrpt` is a HINDSIGHT column and is recorded, never used to filter.
As-filed discipline: where one (cik,tag,ddate) appears in several submissions the
EARLIEST `filed` wins.
"""
import pandas as pd, numpy as np, glob, json, collections

pd.set_option("display.width", 200)
REV = ["Revenues", "SalesRevenueNet", "SalesRevenueGoodsNet",
       "RevenueFromContractWithCustomerExcludingAssessedTax",
       "RevenueFromContractWithCustomerIncludingAssessedTax"]
COST = ["CostOfGoodsSold", "CostOfGoodsAndServicesSold", "CostOfRevenue"]
SGA = ["SellingGeneralAndAdministrativeExpense", "GeneralAndAdministrativeExpense"]

df = pd.concat([pd.read_csv(f, dtype={"cik": str, "ddate": str, "fye": str,
                                      "sic": str, "filed": str})
                for f in sorted(glob.glob("D2_fsds_*_panel.csv"))],
               ignore_index=True)
print(f"raw rows {len(df):,}  ciks {df.cik.nunique():,}  tags {df.tag.nunique()}")
print(f"prevrpt=1 rows (HINDSIGHT column, recorded not used): "
      f"{int((df.prevrpt==1).sum()):,} ({100*(df.prevrpt==1).mean():.2f}%)")

# ---- as-filed dedupe: earliest filed wins -------------------------------
before = len(df)
df = df.sort_values("filed").drop_duplicates(["cik", "tag", "ddate", "qtrs"],
                                             keep="first")
print(f"after as-filed dedupe (earliest `filed` wins): {len(df):,} "
      f"(dropped {before-len(df):,} later restatements/comparatives)")

# ---- fiscal quarter from fye + ddate ------------------------------------
df["fye"] = df.fye.fillna("").str.zfill(4)
fye_m = pd.to_numeric(df.fye.str[:2], errors="coerce")
dd_m = pd.to_numeric(df.ddate.str[4:6], errors="coerce")
diff = (dd_m - fye_m) % 12
df["fq"] = diff.map({0: 4, 3: 1, 6: 2, 9: 3})
offcycle = df.fq.isna()
print(f"off-cycle rows dropped (ddate not a whole number of quarters from fye): "
      f"{int(offcycle.sum()):,} = {100*offcycle.mean():.2f}%")
print(f"  fye months present: {sorted(set(fye_m.dropna().astype(int)))}")
df = df[~offcycle].copy()
df["fq"] = df.fq.astype(int)
df["qid"] = (pd.to_numeric(df.ddate.str[:4]) * 4
             + (pd.to_numeric(df.ddate.str[4:6]) - 1) // 3)

# ============================================================== (B) FYE x SIC
print("\n" + "=" * 92)
print("(B) FISCAL-YEAR-END DISTRIBUTION AND ITS DEPENDENCE ON INDUSTRY")
firms = df.drop_duplicates("cik")[["cik", "fye", "sic"]].copy()
firms["fye_m"] = pd.to_numeric(firms.fye.str[:2], errors="coerce")
firms = firms.dropna(subset=["fye_m"])
firms["fye_m"] = firms.fye_m.astype(int)
vc = firms.fye_m.value_counts().sort_index()
print(f"filers with a usable fye: {len(firms):,}")
print("fiscal-year-end month, share of filers:")
for m, c in vc.items():
    print(f"   month {m:>2}: {c:>6,}  {100*c/len(firms):>6.2f}%")
nondec = 100 * (firms.fye_m != 12).mean()
print(f"  -> NON-DECEMBER fiscal year end: {nondec:.2f}% of filers "
      f"({int((firms.fye_m!=12).sum()):,} of {len(firms):,})")


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


firms["div"] = firms.sic.map(sic_div)


def cramers_v(a, b):
    t = pd.crosstab(a, b)
    chi2 = ((t - np.outer(t.sum(1), t.sum(0)) / t.values.sum()) ** 2
            / (np.outer(t.sum(1), t.sum(0)) / t.values.sum())).values.sum()
    n = t.values.sum()
    return np.sqrt(chi2 / (n * (min(t.shape) - 1))), chi2, t.shape


v, chi2, shp = cramers_v(firms["div"], firms.fye_m)
print(f"\nindustry division x fye month: Cramer's V = {v:.4f} "
      f"(chi2={chi2:,.0f}, table {shp})")
rng = np.random.default_rng(0)
vs = [cramers_v(firms["div"], pd.Series(rng.permutation(firms.fye_m.values),
                                        index=firms.index))[0] for _ in range(30)]
print(f"NEGATIVE CONTROL -- fye PERMUTED across firms, 30 draws: "
      f"V = {np.mean(vs):.4f} (p95 {np.quantile(vs,0.95):.4f}).  "
      f"Observed/permuted = {v/np.mean(vs):.1f}x")
print("\nNON-DECEMBER share BY INDUSTRY DIVISION (the industry-bet channel):")
g = firms.groupby("div").agg(n=("cik", "size"),
                             nondec=("fye_m", lambda s: 100 * (s != 12).mean()))
g = g[g.n >= 40].sort_values("nondec", ascending=False)
for d, r in g.iterrows():
    print(f"   {d:<14} n={int(r.n):>5}  non-Dec {r.nondec:>6.2f}%")

# ============================================================ (A) SEASONALITY
print("\n" + "=" * 92)
print("(A) FISCAL-QUARTER SEASONALITY IN THE SORTED INPUTS ITSELF")
print("    de-trended within firm, then R^2 of fiscal-quarter dummies")


def seas_stats(sub, min_obs=8):
    """sub: one firm, one tag, columns qid/fq/value."""
    s = sub.sort_values("qid")
    y = s.value.values.astype(float)
    if len(y) < min_obs or not np.isfinite(y).all():
        return None
    if np.nanmean(np.abs(y)) == 0:
        return None
    t = np.arange(len(y), dtype=float)
    X = np.column_stack([np.ones(len(y)), t])
    try:
        b = np.linalg.lstsq(X, y, rcond=None)[0]
    except np.linalg.LinAlgError:
        return None
    e = y - X @ b
    sse_tot = e @ e
    if sse_tot <= 0:
        return None
    fq = s.fq.values
    if len(set(fq)) < 4:
        return None
    D = np.column_stack([(fq == k).astype(float) for k in (1, 2, 3, 4)])
    bd = np.linalg.lstsq(D, e, rcond=None)[0]
    r = e - D @ bd
    r2 = 1 - (r @ r) / sse_tot
    mu = np.nanmean(np.abs(y))
    fqm = {k: y[fq == k].mean() for k in set(fq)}
    amp = (max(fqm.values()) - min(fqm.values())) / mu
    return r2, amp, len(y)


FAMS = {"Revenues (flow)": REV, "CostOfGoodsSold (flow)": COST,
        "SG&A (flow)": SGA, "Assets (INSTANT - NEGATIVE CONTROL)": ["Assets"]}
rows = {}
perfirm = {}
for fam, tags in FAMS.items():
    sub = df[df.tag.isin(tags)]
    # one tag per firm: the tag it reports most often
    pick = (sub.groupby(["cik", "tag"]).size().reset_index(name="n")
            .sort_values("n", ascending=False).drop_duplicates("cik"))
    sub = sub.merge(pick[["cik", "tag"]], on=["cik", "tag"])
    out = []
    for cik, s in sub.groupby("cik"):
        r = seas_stats(s)
        if r:
            out.append((cik, *r))
    a = pd.DataFrame(out, columns=["cik", "r2", "amp", "nobs"])
    perfirm[fam] = a
    rows[fam] = dict(n_firms=len(a), r2_median=a.r2.median(), r2_mean=a.r2.mean(),
                     r2_p75=a.r2.quantile(.75), r2_p90=a.r2.quantile(.90),
                     amp_median=a.amp.median(), amp_p90=a.amp.quantile(.90),
                     share_r2_over_50pct=100 * (a.r2 > .5).mean())
print(f"\n{'input':<38}{'firms':>7}{'medR2':>8}{'p75':>7}{'p90':>7}"
      f"{'%R2>.5':>8}{'med amp':>9}{'p90 amp':>9}")
for fam, r in rows.items():
    print(f"{fam:<38}{r['n_firms']:>7}{r['r2_median']:>8.3f}{r['r2_p75']:>7.3f}"
          f"{r['r2_p90']:>7.3f}{r['share_r2_over_50pct']:>8.1f}"
          f"{r['amp_median']:>9.3f}{r['amp_p90']:>9.3f}")
print("\n  'amp' = (largest fiscal-quarter mean - smallest) / mean level.")
print("  amp 1.00 means the peak quarter exceeds the trough by a FULL YEAR-MEAN quarter.")

# revenue seasonality by industry
rv = perfirm["Revenues (flow)"].merge(firms[["cik", "div"]], on="cik", how="left")
print("\nRevenue seasonality BY INDUSTRY DIVISION (median within firm):")
gg = rv.groupby("div").agg(n=("cik", "size"), medR2=("r2", "median"),
                           medamp=("amp", "median"), p90amp=("amp", lambda s: s.quantile(.9)))
for d, r in gg[gg.n >= 25].sort_values("medamp", ascending=False).iterrows():
    print(f"   {d:<14} n={int(r.n):>5}  medR2 {r.medR2:>6.3f}  "
          f"med amp {r.medamp:>6.3f}  p90 amp {r.p90amp:>6.3f}")

json.dump({"seasonality": rows,
           "fye": {"non_december_pct": nondec, "cramers_v": v,
                   "cramers_v_permuted_mean": float(np.mean(vs)),
                   "n_firms": int(len(firms)),
                   "fye_month_share": {int(k): float(100*c/len(firms)) for k, c in vc.items()}}},
          open("D2_fsds_seasonality.json", "w"), indent=1, default=float)
print("\nwrote D2_fsds_seasonality.json")
