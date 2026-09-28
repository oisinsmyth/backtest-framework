"""POST HOC, on D630's spent in-sample: the NG settlement trade's component line (COMPONENTS_PROP.md's C-a, C-c, C-d)
at FULL size and at MNG, with and without the early exits. The ledger's standard scores a component at the instrument's
MINIMUM tradable size (MNG here); the full-size lines answer the principal's question (2026-09-28) and are not an
entry under that standard.

    uv run python scripts/explore_d630_component_full.py    # the venv -> data/ledger_d630_component_full.json

Daily P&L over every in-sample day (zeros on untraded days), as D630's component line. Windows: D630's whole in-sample
(2017-05-22 -> 2025-02-28); the ledger's futures window cut (through 2023-12-29); and without 2022. Sharpe carries its
monthly block-bootstrap SE (`component_series.sharpe_boot`, D466's). C-b is not computable: no ledger component's
daily P&L is on disk (as D630 found).
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
OUT = REPO / "data" / "ledger_d630_component_full.json"
VARIANTS = {"time exit only": (None, None, False), "stop 1x": (1.0, None, False),
            "stop 1x + target 1x (book frame)": (1.0, 1.0, False), "trailing stop 1x": (1.0, None, True),
            "trailing stop 2x": (2.0, None, True)}


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


def line(daily: np.ndarray, days: np.ndarray, traded: np.ndarray) -> dict[str, Any]:
    C = R._load_cs()
    s = pd.Series(daily)
    return {"days": int(len(daily)), "trades": int(traded.sum()), "sharpe_net": C.sharpe(daily),
            "sharpe_se": C.sharpe_boot(daily, list(days)), "sortino_net": C.sortino(daily),
            "skew_daily": float(s.skew()), "daily_sd_usd": float(daily.std(ddof=1)),
            "hit_rate_trades": float((daily[traded] > 0).mean()), "total_usd": float(daily.sum()),
            "max_dd_usd": float((np.cumsum(daily) - np.maximum.accumulate(np.cumsum(daily))).min())}


def main() -> int:
    d, rows = X.trades()
    days = d["day"].to_numpy()
    idx = np.array([r["i"] for r in rows])
    traded = np.zeros(len(d), bool)
    traded[idx] = True
    windows = {"2017-05 -> 2025-02 (D630)": np.ones(len(d), bool), "through 2023-12-29 (ledger window)":
               days <= "2023-12-29", "without 2022": np.array([x[:4] != "2022" for x in days])}
    out: dict[str, Any] = {}
    for name, (ks, kt, trail) in VARIANTS.items():
        g = np.array([X.exit_money(r["dir"], r["fill"], r["exit"], r["absI"], r["mins"], r["hi"], r["lo"], r["t0"],
                                   ks, kt, trail=trail)[0] for r in rows])
        out[name] = {}
        for size, scale, cost in (("full NG", 1.0, R.COST), ("MNG", X.RATIO, R.MNG_COST)):
            daily = np.zeros(len(d))
            daily[idx] = g * scale - cost
            out[name][size] = {w: line(daily[m], days[m], traded[m]) for w, m in windows.items()}
    if not np.isclose(out["time exit only"]["MNG"]["2017-05 -> 2025-02 (D630)"]["sharpe_net"], 0.43873573605288,
                      rtol=0, atol=1e-12):
        raise SystemExit("known answer: D630's MNG net Sharpe")
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    rows_out = []
    for name, v in out.items():
        for size, w in v.items():
            for win, x in w.items():
                rows_out.append({"exit": name, "size": size, "window": win, "Sharpe (SE)":
                                 f"{x['sharpe_net']:+.2f} ({x['sharpe_se']:.2f})", "Sortino": round(x["sortino_net"], 2),
                                 "skew": round(x["skew_daily"], 2), "sd $": round(x["daily_sd_usd"]),
                                 "hit": round(x["hit_rate_trades"], 3), "maxDD $": round(x["max_dd_usd"])})
    with pd.option_context("display.width", 250, "display.max_rows", 100):
        print(pd.DataFrame(rows_out).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
