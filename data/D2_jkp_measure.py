"""D2 [MEASURED IN BRIEF]: what does the SEASONALITY of the accounting input do to a
QUARTERLY profitability sort, measured on ONE library, ONE sample, ONE weighting?

Endpoint (public, no login):
  https://raw.githubusercontent.com/bkelly-lab/jkp-data/main/documentation/
      sas_to_python/data/US_factors_SAS.parquet
  (the JKP US factor return panel: 153 characteristics, monthly, vw_cap, 1926-2024)

The pairs that matter, all from JKP's own construction (documentation.tex):
  ni_be       = NI*_t  / BE*_t        NI* from quarterly data = SUM OVER LAST 4 QUARTERS
                                      -> trailing-four-quarter, seasonality-free by constr.
  niq_be      = NI_QTR*_t / BE*_{t-3} NI_QTR = ibq = ONE fiscal quarter, UNADJUSTED
  niq_be_chg1 = NIQ_BE_t - NIQ_BE_{t-12}   -> FOUR-QUARTER SEASONAL DIFFERENCE
  (same three-way for _at: ni_be has no ni_at factor, so _at gives niq_at/niq_at_chg1 only)

BOTH ni_be AND niq_be ARE REFRESHED QUARTERLY off the same filing (combine_ann_qtr_chars
substitutes the quarterly characteristic whenever its datadate is more recent), so DATA
FRESHNESS IS HELD CONSTANT and the only difference is one quarter vs the sum of four.

CONTROL THAT CAN FIRE: JKP's own CHANGELOG publishes monthly OLS information ratios for
six named US factors. If my extraction is right, mine must match theirs.
"""
import pandas as pd, numpy as np, json, sys

F = "D2_US_factors_SAS.parquet"
d = pd.read_parquet(F)
d["date"] = pd.to_datetime(d["date"])
d = d[(d.location == "usa") & (d.freq == "monthly")]
print(f"panel: {len(d):,} rows, {d.name.nunique()} characteristics, "
      f"{d.date.min().date()} -> {d.date.max().date()}, weighting={set(d.weighting)}")
print(f"direction values present: {sorted(set(d.direction))}")

wide = d.pivot_table(index="date", columns="name", values="ret", aggfunc="first")
nst = d.pivot_table(index="date", columns="name", values="n_stocks", aggfunc="first")


def nw_t(x, lags=6):
    """Newey-West t on the mean."""
    x = np.asarray(x, float)
    n = len(x)
    m = x.mean()
    e = x - m
    g0 = (e @ e) / n
    var = g0
    for L in range(1, lags + 1):
        gl = (e[L:] @ e[:-L]) / n
        var += 2 * (1 - L / (lags + 1)) * gl
    return m / np.sqrt(var / n)


def stats(x):
    x = x.dropna()
    n = len(x)
    if n < 24:
        return None
    mu, sd = x.mean(), x.std(ddof=1)
    return dict(n=n, mean_pct_mo=100 * mu, t_plain=mu / (sd / np.sqrt(n)),
                t_nw6=nw_t(x), ir_monthly=mu / sd, ir_ann=(mu / sd) * np.sqrt(12),
                sd_pct_mo=100 * sd)


# ---------------------------------------------------------------- CONTROL 1
# JKP's CHANGELOG (01-25-2021 and 03-01-2021) publishes these US monthly OLS IRs.
# A control that CAN fire: if my pipeline is wrong, these will not match.
PUBLISHED = {"niq_su": 0.19, "saleq_su": 0.05, "resff3_12_1": 0.28,
             "qmj_prof": 0.22, "bidaskhl_21d": -0.09, "zero_trades_21d": 0.09}
print("\n=== CONTROL 1: reproduce JKP's OWN published monthly OLS IRs (can fire) ===")
print(f"{'factor':<16}{'published':>10}{'mine(mo IR)':>13}{'diff':>8}{'n':>7}")
ctrl = {}
for k, v in PUBLISHED.items():
    s = stats(wide[k]) if k in wide else None
    if s is None:
        print(f"{k:<16}{v:>10.2f}{'ABSENT':>13}")
        continue
    print(f"{k:<16}{v:>10.2f}{s['ir_monthly']:>13.3f}"
          f"{s['ir_monthly']-v:>8.3f}{s['n']:>7}")
    ctrl[k] = dict(published=v, mine=s["ir_monthly"], n=s["n"])

# ---------------------------------------------------------------- CONTROL 2
print("\n=== CONTROL 2: names that MUST NOT exist (must be absent) ===")
for bogus in ["ZZZ_D2_control", "ni_be_seasonally_adjusted", "gpq_at"]:
    print(f"  {bogus!r}: in panel = {bogus in wide.columns}   <-- must be False")

# ---------------------------------------------------------------- MAIN
TRIPLE = {
    "Net income / book equity": ["ni_be", "niq_be", "niq_be_chg1"],
    "Net income / assets": ["niq_at", "niq_at_chg1"],
    "Operating cash flow / assets": ["ocf_at", "ocf_at_chg1"],
}
LABEL = {"ni_be": "TTM (4-qtr sum)  [seasonality-free]",
         "niq_be": "SINGLE QUARTER   [unadjusted/seasonal]",
         "niq_be_chg1": "4-qtr SEASONAL DIFFERENCE",
         "niq_at": "SINGLE QUARTER   [unadjusted/seasonal]",
         "niq_at_chg1": "4-qtr SEASONAL DIFFERENCE",
         "ocf_at": "TTM (4-qtr sum)  [seasonality-free]",
         "ocf_at_chg1": "4-qtr SEASONAL DIFFERENCE"}

ERAS = [("full overlap", None, None),
        ("1972-2010 (Novy-Marx window)", "1972-01-01", "2010-12-31"),
        ("2010-2024 (programme era)", "2010-01-01", "2024-12-31")]

results = {}
for fam, names in TRIPLE.items():
    names = [n for n in names if n in wide.columns]
    sub = wide[names].dropna()           # MATCHED MONTHS: all members present
    print(f"\n{'='*94}\n{fam}   -- matched months where ALL of {names} exist: "
          f"{len(sub)} ({sub.index.min().date()} -> {sub.index.max().date()})")
    for era, a, b in ERAS:
        s2 = sub.loc[a:b] if (a or b) else sub
        if len(s2) < 24:
            print(f"  [{era}] too few months ({len(s2)})")
            continue
        print(f"  [{era}]  n={len(s2)} months")
        print(f"    {'characteristic':<14}{'construction':<40}"
              f"{'mean%/mo':>10}{'t':>7}{'t_NW6':>8}{'IR_ann':>8}")
        for n in names:
            st = stats(s2[n])
            print(f"    {n:<14}{LABEL.get(n,''):<40}{st['mean_pct_mo']:>10.3f}"
                  f"{st['t_plain']:>7.2f}{st['t_nw6']:>8.2f}{st['ir_ann']:>8.2f}")
            results[(fam, era, n)] = st
        # spanning-style difference: single quarter MINUS ttm
        if "ni_be" in names and "niq_be" in names:
            diff = s2["niq_be"] - s2["ni_be"]
            st = stats(diff)
            print(f"    {'DIFF':<14}{'niq_be MINUS ni_be (single qtr - TTM)':<40}"
                  f"{st['mean_pct_mo']:>10.3f}{st['t_plain']:>7.2f}{st['t_nw6']:>8.2f}")
            print(f"    corr(niq_be, ni_be) = {s2['niq_be'].corr(s2['ni_be']):.3f}")

# average stock counts, so nobody reads a thin portfolio as a result
print(f"\n=== mean n_stocks per factor-month (breadth check) ===")
for n in ["ni_be", "niq_be", "niq_be_chg1", "niq_at", "gp_at", "op_at"]:
    if n in nst.columns:
        print(f"  {n:<14} mean n_stocks = {nst[n].mean():.0f}, "
              f"first month = {nst[n].dropna().index.min().date()}")

out = {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in results.items()}
json.dump({"control_published_IR": ctrl, "results": out},
          open("D2_jkp_measure.json", "w"), indent=1, default=float)
print("\nwrote D2_jkp_measure.json")
