"""D2 [MEASURED IN BRIEF] step 2, FOURTH pass -- and the two discarded nulls are kept
in the record because each was killed by a control, not by taste.

  pass 2: RANDOM PERMUTATION of quarter labels. WRONG -- it destroys the even spacing
          of the true labels, and with a serially correlated residual that inflates the
          null. Tell: the Assets control came in 0.105 BELOW its own null.
  pass 3: ROTATION of quarter labels. DEGENERATE -- a rotation maps the mod-4 partition
          onto itself and merely renames the groups, and R^2 / peak-trough do not depend
          on group names. Tell: excess was EXACTLY 0.000 for all four inputs.

Any statistic built on the mod-4 partition of positions is invariant to relabelling, so
a valid null must break the PERIODICITY. Two statistics are used here instead:

  S1  SPLIT-HALF FISCAL-QUARTER PROFILE CORRELATION. Split a firm's years in half,
      compute the mean de-trended fiscal-quarter profile (a centred 4-vector) in each
      half, and correlate the two. Real seasonality repeats, so it is strongly positive.
      Under no seasonality two independent centred 4-vectors correlate at about -1/3,
      NOT 0, so the benchmark is stated and also measured.
  S2  AMPLITUDE WITH AN AR(1) SURROGATE NULL. Per firm, fit an AR(1) to the de-trended
      residual, simulate 200 surrogates with the same persistence and innovation
      variance -- these have the firm's serial correlation and NO seasonality -- and
      take the statistic's null distribution from them.

`Assets` remains the standing negative control: an instant (a stock), not a flow, so it
must show far less fiscal-quarter structure than revenue or cost of goods.
"""
import pandas as pd, numpy as np, glob, json

REV = ["Revenues", "SalesRevenueNet", "SalesRevenueGoodsNet",
       "RevenueFromContractWithCustomerExcludingAssessedTax",
       "RevenueFromContractWithCustomerIncludingAssessedTax"]
COST = ["CostOfGoodsSold", "CostOfGoodsAndServicesSold", "CostOfRevenue"]
SGA = ["SellingGeneralAndAdministrativeExpense", "GeneralAndAdministrativeExpense"]

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
firms = df.drop_duplicates("cik")[["cik", "fye", "sic"]].copy()


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


def quarterly(tags):
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


Q = {"Revenues (flow)": quarterly(REV),
     "CostOfGoodsSold (flow)": quarterly(COST),
     "SG&A (flow)": quarterly(SGA),
     "Assets (INSTANT - NEG CONTROL)":
         df[df.tag == "Assets"][["cik", "dt", "fq", "value"]].copy()}

rng = np.random.default_rng(11)
NSUR = 200


def profile(e, fq):
    p = np.array([e[fq == k].mean() if (fq == k).any() else np.nan
                  for k in (1, 2, 3, 4)])
    return p - np.nanmean(p)


def one_firm(sub, min_obs=8):
    s = sub.sort_values("dt")
    y = s.value.values.astype(float)
    fq = s.fq.values
    n = len(y)
    if n < min_obs or not np.isfinite(y).all():
        return None
    mu = np.nanmean(np.abs(y))
    if mu == 0 or len(set(fq)) < 4:
        return None
    t = np.arange(n, dtype=float)
    X = np.column_stack([np.ones(n), t])
    e = y - X @ np.linalg.lstsq(X, y, rcond=None)[0]
    if e @ e <= 0:
        return None
    # ---- S1 split-half profile correlation
    h = n // 2
    pa, pb = profile(e[:h], fq[:h]), profile(e[h:], fq[h:])
    ok = np.isfinite(pa) & np.isfinite(pb)
    if ok.sum() < 3 or np.nanstd(pa[ok]) == 0 or np.nanstd(pb[ok]) == 0:
        sh = np.nan
    else:
        sh = float(np.corrcoef(pa[ok], pb[ok])[0, 1])
    # ---- S2 amplitude with AR(1) surrogate null
    amp = (np.nanmax(profile(e, fq)) - np.nanmin(profile(e, fq))) / mu
    if n > 3:
        rho = np.clip(np.corrcoef(e[:-1], e[1:])[0, 1], -0.95, 0.95)
    else:
        rho = 0.0
    sig = np.std(e) * np.sqrt(max(1e-12, 1 - rho ** 2))
    z = rng.standard_normal((NSUR, n)) * sig
    sur = np.empty((NSUR, n))
    sur[:, 0] = z[:, 0] / np.sqrt(max(1e-12, 1 - rho ** 2))
    for i in range(1, n):
        sur[:, i] = rho * sur[:, i - 1] + z[:, i]
    D = np.column_stack([(fq == k).astype(float) for k in (1, 2, 3, 4)])
    cnt = D.sum(0)
    gm = (sur @ D) / np.where(cnt == 0, np.nan, cnt)
    gm = gm - np.nanmean(gm, axis=1, keepdims=True)
    amp_sur = (np.nanmax(gm, 1) - np.nanmin(gm, 1)) / mu
    return (sh, amp, float(np.nanmean(amp_sur)),
            float(np.nanquantile(amp_sur, 0.95)),
            float((amp_sur >= amp).mean()), rho, n)


print("=" * 110)
print("(A) HOW SEASONAL IS THE SORTED INPUT ITSELF?  S1 split-half profile")
print("    correlation; S2 amplitude vs an AR(1) surrogate null (200/firm)")
res, store = {}, {}
for fam, q in Q.items():
    out = []
    for cik, s in q.groupby("cik"):
        r = one_firm(s)
        if r:
            out.append((cik, *r))
    a = pd.DataFrame(out, columns=["cik", "splithalf", "amp", "amp_sur",
                                   "amp_sur_p95", "p_emp", "rho", "nobs"])
    store[fam] = a
    res[fam] = dict(
        n_firms=len(a), splithalf_med=a.splithalf.median(),
        share_splithalf_gt_0=100 * (a.splithalf > 0).mean(),
        share_splithalf_gt_05=100 * (a.splithalf > 0.5).mean(),
        amp_med=a.amp.median(), amp_sur_med=a.amp_sur.median(),
        amp_ratio_med=(a.amp / a.amp_sur).median(),
        share_p_under_05=100 * (a.p_emp < 0.05).mean(),
        amp_p90=a.amp.quantile(.90), rho_med=a.rho.median(),
        med_nobs=a.nobs.median())
print(f"\n{'input':<34}{'firms':>6}{'splitHalf':>10}{'%>0':>7}{'%>.5':>7}"
      f"{'amp':>7}{'ampSur':>8}{'ratio':>7}{'%p<.05':>8}{'rho':>7}")
for fam, r in res.items():
    print(f"{fam:<34}{r['n_firms']:>6}{r['splithalf_med']:>10.3f}"
          f"{r['share_splithalf_gt_0']:>7.1f}{r['share_splithalf_gt_05']:>7.1f}"
          f"{r['amp_med']:>7.3f}{r['amp_sur_med']:>8.3f}{r['amp_ratio_med']:>7.2f}"
          f"{r['share_p_under_05']:>8.1f}{r['rho_med']:>7.2f}")
print("\n  splitHalf: correlation of the fiscal-quarter profile in the first half of a")
print("  firm's years with the second half. Under NO seasonality two independent")
print("  centred 4-vectors correlate at about -1/3, so ~0 already means 'some'.")
print("  %p<.05: share of firms whose amplitude beats 95% of their own AR(1) surrogates.")

rv = store["Revenues (flow)"].merge(firms[["cik", "div"]], on="cik", how="left")
print("\nRevenue seasonality BY INDUSTRY DIVISION:")
print(f"   {'division':<14}{'n':>6}{'splitHalf':>11}{'%>.5':>7}{'amp':>7}"
      f"{'ratio':>7}{'%p<.05':>8}")
gg = rv.groupby("div").agg(n=("cik", "size"), sh=("splithalf", "median"),
                           sh5=("splithalf", lambda s: 100 * (s > .5).mean()),
                           amp=("amp", "median"),
                           ratio=("amp", "median"),
                           p=("p_emp", lambda s: 100 * (s < .05).mean()))
rat = rv.assign(r=rv.amp / rv.amp_sur).groupby("div").r.median()
for d, r in gg[gg.n >= 25].sort_values("sh", ascending=False).iterrows():
    print(f"   {d:<14}{int(r.n):>6}{r.sh:>11.3f}{r.sh5:>7.1f}{r.amp:>7.3f}"
          f"{rat.get(d, np.nan):>7.2f}{r.p:>8.1f}")

json.dump(res, open("D2_fsds_seasonality4.json", "w"), indent=1, default=float)
for k, v in store.items():
    v.to_csv(f"D2_seas4_{k.split()[0].replace('&','and')}.csv", index=False)
print("\nwrote D2_fsds_seasonality4.json + per-firm CSVs")
