"""D2 [MEASURED IN BRIEF] part 3 -- THE BAR, for GROSS profitability.

JKP's `gp_at` IS a seasonality-robust quarterly construction: the numerator is the
SUM OVER THE LAST FOUR QUARTERS (documentation.tex: "To make quarterly income and
cash flows items comparable to the corresponding annual item, we take the sum of the
item over the last four quarters"), refreshed whenever a quarterly filing is more
recent than the annual one (accounting_chars.sas, %combine_ann_qtr_chars), four months
after fiscal period end.

So its factor return IS "the quarterly gross-profitability sort under a
seasonality-free construction", which is the number the round-4 slate asked for.
What does NOT exist anywhere public is an ANNUAL-ONLY counterpart in the same library,
so this is a standalone level, not a quarterly-minus-annual difference.

Reported with the programme's own era split, and with the other profitability
deflators beside it so the deflator choice is visible rather than hidden.
"""
import pandas as pd, numpy as np, json

d = pd.read_parquet("D2_US_factors_SAS.parquet")
d["date"] = pd.to_datetime(d["date"])
w = d.pivot_table(index="date", columns="name", values="ret", aggfunc="first")
nst = d.pivot_table(index="date", columns="name", values="n_stocks", aggfunc="first")


def nw_t(x, lags=6):
    x = np.asarray(x, float); n = len(x); m = x.mean(); e = x - m
    v = (e @ e) / n
    for L in range(1, lags + 1):
        v += 2 * (1 - L / (lags + 1)) * ((e[L:] @ e[:-L]) / n)
    return m / np.sqrt(v / n)


NAMES = [("gp_at", "gross profits / assets          TTM, qtr-refreshed"),
         ("gp_atl1", "gross profits / LAGGED assets   TTM, qtr-refreshed"),
         ("op_at", "operating profits / assets      TTM, qtr-refreshed"),
         ("op_atl1", "operating profits / LAGGED at   TTM, qtr-refreshed"),
         ("ope_be", "operating profits / book equity TTM, qtr-refreshed"),
         ("ope_bel1", "oper profits / LAGGED equity    TTM, qtr-refreshed"),
         ("cop_at", "cash-based oper prof / assets   TTM, qtr-refreshed"),
         ("ni_be", "net income / book equity        TTM, qtr-refreshed"),
         ("niq_be", "net income / book equity        SINGLE QUARTER"),
         ("niq_at", "net income / assets             SINGLE QUARTER")]
ERAS = [("full (factor's own start)", None, None),
        ("1963-2010  publication era", "1963-01-01", "2010-12-31"),
        ("2010-2024  programme era", "2010-01-01", "2024-12-31"),
        ("2005-2024  post-2005", "2005-01-01", "2024-12-31")]
out = {}
for era, a, b in ERAS:
    print(f"\n=== {era} ===")
    print(f"  {'factor':<10}{'construction':<50}{'n':>5}{'%/mo':>8}{'t':>7}"
          f"{'tNW6':>7}{'IRann':>7}{'nstk':>6}")
    for nm, lab in NAMES:
        if nm not in w.columns:
            continue
        x = (w.loc[a:b, nm] if (a or b) else w[nm]).dropna()
        if len(x) < 24:
            print(f"  {nm:<10}{lab:<50}{len(x):>5}  too few")
            continue
        mu, sd = x.mean(), x.std(ddof=1)
        ns = (nst.loc[a:b, nm] if (a or b) else nst[nm]).dropna().mean()
        print(f"  {nm:<10}{lab:<50}{len(x):>5}{100*mu:>8.3f}"
              f"{mu/(sd/np.sqrt(len(x))):>7.2f}{nw_t(x):>7.2f}"
              f"{(mu/sd)*np.sqrt(12):>7.2f}{ns:>6.0f}")
        out[f"{era}|{nm}"] = dict(n=len(x), mean_pct_mo=100*mu,
                                  t=mu/(sd/np.sqrt(len(x))), t_nw6=nw_t(x),
                                  ir_ann=(mu/sd)*np.sqrt(12), n_stocks=ns)

print("\n=== when does each series START? (a 1950s start is the ANNUAL data) ===")
for nm, _ in NAMES:
    if nm in w.columns:
        print(f"  {nm:<10} first month {w[nm].dropna().index.min().date()}  "
              f"last {w[nm].dropna().index.max().date()}")
json.dump(out, open("D2_jkp_measure3.json", "w"), indent=1, default=float)
print("\nwrote D2_jkp_measure3.json")
