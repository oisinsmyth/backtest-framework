"""POST HOC, on D630's spent in-sample: how much of D630's gate and of the L1a impact filter rests on f_est, the funds'
futures share interpolated between quarter-ends with the NEXT filing (not point-in-time; build_predicted_flow_panel's
own note)? `f_pit` (the latest quarter-end FILED on or before the day) is the point-in-time reading, and the panel
stores q_pit beside q_est. (The principal, 2026-09-28: "can any of these be used point in time?")

    uv run python scripts/explore_d630_pit_check.py    # the venv -> data/ledger_d630_pit_check.json

I scales as sqrt(|Q|) at fixed sigma_d, V_d and price (I = 0.7 sigma_d sqrt(|Q|/V_d) P), so the point-in-time impact is
I_pit = I x sqrt(|q_pit| / |q_est|). THE PIT GATE re-applies D630's binding clause, |I_pit| >= 3 x the round-trip cost
in price, at the day's own t0; the SNR clause is not recomputed (sigma_Q depends on f too) and is reported as a
limitation. The direction, sign(q), does not depend on f (f > 0).
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
OUT = REPO / "data" / "ledger_d630_pit_check.json"


def _load(name: str, fn: str) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    assert s is not None and s.loader is not None
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


L = _load("explore_d630_levers", "explore_d630_levers.py")
X, R, H = L.X, L.R, L.H


def main() -> int:
    C = R._load_cs()
    d, rows = X.trades()
    idx = np.array([r["i"] for r in rows])
    tr = d.iloc[idx]
    f = pd.read_csv(H.FLOW, encoding="utf-8", usecols=["root", "day", "tau", "q_est", "q_pit", "I", "rt_cost"])
    f = f[f["root"] == "NG"].set_index(["day", "tau"])
    k = list(zip(tr["day"], tr["tau"]))
    q_est, q_pit = f["q_est"].reindex(k).to_numpy(), f["q_pit"].reindex(k).to_numpy()
    I = f["I"].reindex(k).to_numpy()
    rt = f["rt_cost"].reindex(k).to_numpy()
    if not np.allclose(np.abs(I) * R.MULT, tr["absI_usd"].to_numpy(), rtol=1e-12):
        raise SystemExit("known answer: the panel's I is not D630's |I|")
    ratio = np.abs(q_pit) / np.abs(q_est)
    I_pit = np.abs(I) * np.sqrt(ratio)
    gate_pit = I_pit >= 3 * rt
    g = np.array([r["g_primary"] for r in rows])
    years = tr["year"].to_numpy()
    absI_pit_usd = I_pit * R.MULT
    hi_pit = L.pit_quantile(absI_pit_usd, 2 / 3)
    L1a_est = tr["absI_usd"].to_numpy() >= L.pit_quantile(tr["absI_usd"].to_numpy(), 2 / 3)
    L1a_pit = gate_pit & (absI_pit_usd >= hi_pit)
    price = tr["p_held"].to_numpy(float)

    def line(take: np.ndarray) -> dict[str, Any]:
        out = {"trades": int(take.sum())}
        for cls, scale, cost in (("full", 1.0, R.COST), ("micro", X.RATIO, R.MNG_COST)):
            daily = np.zeros(len(d))
            daily[idx[take]] = g[take] * scale - cost
            x22 = d["year"].to_numpy() != "2022"
            out[cls] = {"net_per_trade": float((g[take] * scale - cost).mean()), "sharpe_net": C.sharpe(daily),
                        "sharpe_se": C.sharpe_boot(daily, list(d["day"])), "sharpe_ex2022": C.sharpe(daily[x22])}
        out["trades_by_year"] = {y: int((take & (years == y)).sum()) for y in sorted(set(years))}
        return out

    every = np.ones(len(rows), bool)
    doc = {"q_ratio_pit_over_est": {"share_differs_1pct": float((np.abs(ratio - 1) > 0.01).mean()),
                                    "share_differs_10pct": float((np.abs(ratio - 1) > 0.10).mean()),
                                    "median": float(np.median(ratio)), "p05": float(np.quantile(ratio, 0.05)),
                                    "p95": float(np.quantile(ratio, 0.95))},
           "gate_pit_keeps": float(gate_pit.mean()),
           "lines": {"D630 base (f_est gate)": line(every), "base, PIT gate": line(gate_pit),
                     "L1a on f_est |I|": line(L1a_est), "L1a on PIT |I| and PIT gate": line(L1a_pit),
                     "L1a + L2 + L3-free (PIT, price >= 3)": line(L1a_pit & (price >= 3.0))},
           "limitation": "the SNR clause of D630's gate is not recomputed at f_pit"}
    OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in doc.items() if k != "lines"}, indent=1))
    for name, v in doc["lines"].items():
        print(f"{name:40s} n {v['trades']:4d} | full net {v['full']['net_per_trade']:7.1f} Sh {v['full']['sharpe_net']:+.2f} "
              f"({v['full']['sharpe_se']:.2f}) ex22 {v['full']['sharpe_ex2022']:+.2f} | MNG net {v['micro']['net_per_trade']:6.2f} "
              f"Sh {v['micro']['sharpe_net']:+.2f} ex22 {v['micro']['sharpe_ex2022']:+.2f} | {v['trades_by_year']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
