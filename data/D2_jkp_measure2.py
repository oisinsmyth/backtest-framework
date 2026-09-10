"""D2 [MEASURED IN BRIEF] part 2.

(a) RESOLVE CONTROL 1. JKP's CHANGELOG IRs were published 2021-01-25 / 2021-03-01.
    This parquet runs to 2024-12. If the mismatch is a VINTAGE effect, truncating my
    sample at 2020-12 should move my numbers TOWARD the published ones.
    That is a checkable prediction, so it is made before the numbers are read.

(b) THE SPANNING TEST, which is the statistic Novy-Marx's Table A6 uses to say the
    ANNUAL strategy is subsumed by the QUARTERLY one. Here the two sides are the
    SINGLE-QUARTER and the TRAILING-FOUR-QUARTER form of THE SAME ratio, both
    refreshed quarterly -- so freshness is held constant and only the seasonality
    of the numerator differs.
"""
import pandas as pd, numpy as np, json

d = pd.read_parquet("D2_US_factors_SAS.parquet")
d["date"] = pd.to_datetime(d["date"])
wide = d.pivot_table(index="date", columns="name", values="ret", aggfunc="first")


def nw_se(e, X, lags=6):
    """Newey-West SEs for OLS resid e and design X."""
    n, k = X.shape
    XtX_inv = np.linalg.inv(X.T @ X)
    S = (X * e[:, None]).T @ (X * e[:, None])
    for L in range(1, lags + 1):
        u = (X * e[:, None])
        G = u[L:].T @ u[:-L]
        S += (1 - L / (lags + 1)) * (G + G.T)
    V = XtX_inv @ S @ XtX_inv
    return np.sqrt(np.diag(V))


def ols(y, Xcols, df, lags=6):
    sub = df[[y] + Xcols].dropna()
    Y = sub[y].values
    X = np.column_stack([np.ones(len(sub))] + [sub[c].values for c in Xcols])
    b = np.linalg.lstsq(X, Y, rcond=None)[0]
    e = Y - X @ b
    se = nw_se(e, X, lags)
    ss = 1 - (e @ e) / ((Y - Y.mean()) @ (Y - Y.mean()))
    return dict(n=len(sub), alpha_pct_mo=100 * b[0], t_alpha=b[0] / se[0],
                betas={c: (bb, bb / ss_) for c, bb, ss_ in zip(Xcols, b[1:], se[1:])},
                r2=ss)


# ---------------------------------------------------------------- (a) VINTAGE
PUB = {"niq_su": 0.19, "saleq_su": 0.05, "resff3_12_1": 0.28,
       "qmj_prof": 0.22, "bidaskhl_21d": -0.09, "zero_trades_21d": 0.09}
print("=== CONTROL 1 RESOLVED? monthly OLS IR on two sample ends ===")
print("PREDICTION MADE BEFORE READING: if the gap is a vintage effect, the 2020-12")
print("column is closer to 'published' than the 2024-12 column, for most factors.\n")
print(f"{'factor':<17}{'published':>10}{'->2024-12':>11}{'->2020-12':>11}"
      f"{'|d|2024':>9}{'|d|2020':>9}{'closer':>9}")
closer = 0
rows = {}
for k, v in PUB.items():
    x_all = wide[k].dropna()
    x_20 = x_all[x_all.index <= "2020-12-31"]
    ir_all = x_all.mean() / x_all.std(ddof=1)
    ir_20 = x_20.mean() / x_20.std(ddof=1)
    d1, d2 = abs(ir_all - v), abs(ir_20 - v)
    win = "2020-12" if d2 < d1 else "2024-12"
    closer += (d2 < d1)
    print(f"{k:<17}{v:>10.2f}{ir_all:>11.3f}{ir_20:>11.3f}{d1:>9.3f}{d2:>9.3f}{win:>9}")
    rows[k] = dict(published=v, to_2024=ir_all, to_2020=ir_20)
print(f"\n  -> the 2020-12 vintage is closer for {closer} of {len(PUB)} factors")

# ---------------------------------------------------------------- (b) SPANNING
print("\n" + "=" * 96)
print("SPANNING TESTS -- single quarter vs trailing four quarters, SAME ratio,")
print("BOTH refreshed quarterly (freshness held constant). Newey-West(6) t in brackets.")
PAIRS = [("niq_be", "ni_be", "net income / book equity"),
         ("ocf_at_chg1", "ocf_at", "operating cash flow / assets"),
         ("niq_be_chg1", "niq_be", "NI/BE: seasonal difference vs single-quarter level")]
ERAS = [("full overlap", None, None),
        ("1972-2010", "1972-01-01", "2010-12-31"),
        ("2010-2024", "2010-01-01", "2024-12-31")]
out = {}
for a, b, lab in PAIRS:
    if a not in wide or b not in wide:
        print(f"  {lab}: one side absent")
        continue
    print(f"\n--- {lab}:  {a}  vs  {b}")
    for era, s, e in ERAS:
        df = wide.loc[s:e, [a, b]].dropna() if (s or e) else wide[[a, b]].dropna()
        if len(df) < 36:
            print(f"  [{era}] n={len(df)} too few")
            continue
        ra = ols(a, [b], df)
        rb = ols(b, [a], df)
        print(f"  [{era}] n={len(df)}")
        print(f"     alpha of {a:<12} vs {b:<10} = {ra['alpha_pct_mo']:+.3f} %/mo "
              f"[{ra['t_alpha']:+.2f}]  beta={ra['betas'][b][0]:.2f} "
              f"[{ra['betas'][b][1]:.1f}]  R2={ra['r2']:.3f}")
        print(f"     alpha of {b:<12} vs {a:<10} = {rb['alpha_pct_mo']:+.3f} %/mo "
              f"[{rb['t_alpha']:+.2f}]  beta={rb['betas'][a][0]:.2f} "
              f"[{rb['betas'][a][1]:.1f}]  R2={rb['r2']:.3f}")
        out[f"{lab}|{era}"] = {f"alpha_{a}_vs_{b}": ra, f"alpha_{b}_vs_{a}": rb}

json.dump({"vintage": rows, "spanning": out}, open("D2_jkp_measure2.json", "w"),
          indent=1, default=float)
print("\nwrote D2_jkp_measure2.json")
