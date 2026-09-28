"""POST HOC, on D630's spent in-sample: filter on the trade's PROJECTED dollars (the principal, 2026-09-28: "if we can
project before the trade whether it would be profitable, filter by that").

    uv run python scripts/explore_d630_projected_profit.py    # the venv -> data/ledger_d630_projected_profit.json

D630's gate is already a projected-profit filter: |I| >= 3 x cost, which assumes the realized move equals the predicted
impact. This measures the realized PASS-THROUGH, b = realized move / predicted impact, and filters on the projection
the pass-through implies:

    b_t = sum(g_j x I_j) / sum(I_j^2) over PRIOR traded days j < t (OLS through the origin; at least MIN_PRIOR of them)
    E[$]_t = b_t x |I_t| x 10,000 (full contract; / 10 for MNG)
    trade when E[$]_t >= k x the round-trip cost, k in {1.0, 1.5, 2.0} (declared here)

Everything is point-in-time: |I_t| uses AUM at t-1, trailing volume and the price at t0, and b_t only prior trades'
outcomes. |I| is in price, so the projection already scales with the NG price (no separate price floor). The same
rule at MNG uses MNG's cost against a tenth of the projection. The rule's form was chosen after seeing D630 and the
year breakdown, so this remains exploratory.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
OUT = REPO / "data" / "ledger_d630_projected_profit.json"
MIN_PRIOR = 100
KS = (1.0, 1.5, 2.0)


def _load(name: str, fn: str) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    assert s is not None and s.loader is not None
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


X = _load("explore_d630_exits_micro", "explore_d630_exits_micro.py")
R = X.R


def main() -> int:
    C = R._load_cs()
    d, rows = X.trades()
    idx = np.array([r["i"] for r in rows])
    tr = d.iloc[idx]
    g = np.array([r["g_primary"] for r in rows])          # realized gross, full-contract dollars
    I = tr["absI_usd"].to_numpy(float)                     # predicted impact, full-contract dollars
    years = tr["year"].to_numpy()
    n = len(g)
    b = np.full(n, np.nan)
    sgI, sII = np.cumsum(g * I), np.cumsum(I * I)
    for t in range(MIN_PRIOR, n):
        b[t] = sgI[t - 1] / sII[t - 1]  # prior trades only
    proj_full = b * I
    by_year = {y: {"trades": int((years == y).sum()), "mean_I_usd": float(I[years == y].mean()),
                   "mean_realized_usd": float(g[years == y].mean()),
                   "pass_through": float((g[years == y] * I[years == y]).sum() / (I[years == y] ** 2).sum())}
               for y in sorted(set(years))}

    def line(take: np.ndarray) -> dict[str, Any]:
        out: dict[str, Any] = {"trades": int(take.sum()),
                               "trades_by_year": {y: int((take & (years == y)).sum()) for y in sorted(set(years))}}
        for cls, scale, cost in (("full", 1.0, R.COST), ("micro", X.RATIO, R.MNG_COST)):
            daily = np.zeros(len(d))
            daily[idx[take]] = g[take] * scale - cost
            x22 = d["year"].to_numpy() != "2022"
            yr = pd.Series(daily).groupby(d["year"].to_numpy()).sum()
            out[cls] = {"net_per_trade": float((g[take] * scale - cost).mean()) if take.any() else float("nan"),
                        "sharpe_net": C.sharpe(daily), "sharpe_se": C.sharpe_boot(daily, list(d["day"])),
                        "sortino_net": C.sortino(daily), "sharpe_ex2022": C.sharpe(daily[x22]),
                        "skew_daily": float(pd.Series(daily).skew()), "profitable_years": int((yr > 0).sum()),
                        "share_2022": float(yr.get("2022", 0.0) / daily.sum())}
        return out

    lines = {"D630 base": line(np.ones(n, bool))}
    for k in KS:
        lines[f"projected full $ >= {k} x $26"] = line(proj_full >= k * R.COST)
        lines[f"projected MNG $ >= {k} x $5"] = line(proj_full * X.RATIO >= k * R.MNG_COST)
    doc = {"pass_through_by_year": by_year, "pass_through_pooled": float((g * I).sum() / (I * I).sum()),
           "b_t_last": float(b[-1]), "b_t_range": [float(np.nanmin(b)), float(np.nanmax(b))], "lines": lines}
    OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("pass-through b = realized / predicted, by year:")
    print(pd.DataFrame(by_year).T.round(3).to_string())
    print(f"pooled {doc['pass_through_pooled']:.3f}; b_t (prior trades only) ranges {doc['b_t_range']}")
    for name, v in lines.items():
        f, m = v["full"], v["micro"]
        print(f"{name:34s} n {v['trades']:4d} | full net {f['net_per_trade']:7.1f} Sh {f['sharpe_net']:+.2f} ({f['sharpe_se']:.2f}) "
              f"ex22 {f['sharpe_ex2022']:+.2f} yrs+ {f['profitable_years']} | MNG net {m['net_per_trade']:6.2f} "
              f"Sh {m['sharpe_net']:+.2f} ex22 {m['sharpe_ex2022']:+.2f} yrs+ {m['profitable_years']} | {v['trades_by_year']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
