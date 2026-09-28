"""The component lines CLAUDE.md requires of D643's RESULT (D642 put the book-frame groups in Phase 5, which Gate 1 stopped).
Descriptive only: no test and no selection. Each class's trade is scored exactly as D642's runner scored it (the
t0+1 fill, a 30-minute time exit, one micro and s.5.1's cost in dollars), and those trades are summed into a daily
dollar series. It is path-invariant: overlapping trades are all kept, since the slot-limited book is Phase 5's.

    python scripts/shock_component_line.py      # SYSTEM interpreter (pyarrow) -> data/shock/phase3_component_lines.json

Per instrument x class (INFO follows the shock, LIQ fades it):
- the daily net and gross Sharpe and Sortino over every usable session (sqrt(252)), on the ledger's 2016-2023 window
  and on the whole in-sample window 2016-01-04 -> 2025-02-28;
- hit rate (net $ > 0), per-trade skew, mean gross and net $, trades per year;
- the correlation with D466's committed ledger series K1..K6 over 2016-2023, the same source D640 used.
"""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]


def _load(name: str, fn: str) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    assert s is not None and s.loader is not None
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


R = _load("run_shock_signal", "run_shock_signal.py")
OUT = REPO / "data" / "shock" / "phase3_component_lines.json"
LEDGER_END = "2023-12-29"


def shp(x: np.ndarray) -> float | None:
    s = x.std(ddof=1)
    return float(x.mean() / s * math.sqrt(252)) if s > 0 else None


def srt(x: np.ndarray) -> float | None:
    dn = x[x < 0]
    dd = math.sqrt((dn ** 2).sum() / len(x)) if len(dn) else 0.0
    return float(x.mean() / dd * math.sqrt(252)) if dd > 0 else None


def main() -> int:
    days = R.P2.usable_sessions()
    sh = pd.read_csv(R.SH / "phase2_shocks.csv.gz", encoding="utf-8", dtype={"day": str})
    R.check_counts(sh, R.committed_counts())
    sh = sh[sh["z"] == 4.0].reset_index(drop=True)
    G = R.P2.grids(list(R.TRADED), days)
    GA = {r: G[r].to_numpy(float) for r in R.TRADED}
    V = {r: np.ones_like(GA[r]) for r in R.TRADED}
    o = R.outcomes(sh, GA, V, days)
    # the same numbers the runner reported: a guard that this is the object D643 scored
    sig = json.loads(R.OUT.read_text(encoding="utf-8"))
    for r in R.TRADED:
        for c in ("INFO", "LIQ"):
            q = o[(o["root"] == r) & (o["class_primary"] == c)]
            want = sig["instruments"][r]["groups"][c]["gross_bp"]["mean"]
            if not math.isclose(float(q["pnl"].mean()), want, rel_tol=1e-12):
                raise SystemExit(f"{r} {c}: the trades differ from phase3_signal.json ({q['pnl'].mean()} vs {want})")
    D466 = _load("run_d466_components", "run_d466_components.py")
    _cal, S, _act, desc = D466.build_series()
    cal = pd.Index([d for d in days if d >= R.P2.START])
    doc: dict[str, Any] = {"spec": "CLAUDE.md component line for D643; trades as D642's runner (t0+1 fill, 30-min exit)",
                           "size": "1 micro (MNQ, MES, MCL, MGC)", "rt_cost_usd": R.COST_USD,
                           "sessions": [cal[0], cal[-1], len(cal)], "ledger": "D466 build_series, 2016-01-04 -> 2023-12-29",
                           "ledger_desc": desc, "lines": {}}
    for r in R.TRADED:
        for c in ("INFO", "LIQ"):
            q = o[(o["root"] == r) & (o["class_primary"] == c)]
            gross = (q["pnl"] / 1e4 * q["fill"] * R.USD_PER_POINT[r]).to_numpy(float)
            net = gross - R.COST_USD[r]
            sg = pd.Series(gross, index=q["day"].to_numpy()).groupby(level=0).sum().reindex(cal, fill_value=0.0)
            sn = pd.Series(net, index=q["day"].to_numpy()).groupby(level=0).sum().reindex(cal, fill_value=0.0)
            led = sn[sn.index <= LEDGER_END]
            line: dict[str, Any] = {
                "trades": int(len(q)), "trades_per_year": round(len(q) / (len(cal) / 252), 1),
                "net_sharpe_2016_2023": shp(led.to_numpy()),
                "net_sortino_2016_2023": srt(led.to_numpy()),
                "gross_sharpe_2016_2023": shp(sg[sg.index <= LEDGER_END].to_numpy()),
                "net_sharpe_full": shp(sn.to_numpy()), "net_sortino_full": srt(sn.to_numpy()),
                "gross_sharpe_full": shp(sg.to_numpy()), "gross_sortino_full": srt(sg.to_numpy()),
                "hit_net": float((net > 0).mean()), "skew_per_trade_usd": R.skew(gross),
                "mean_gross_usd": float(gross.mean()), "mean_net_usd": float(net.mean()),
                "net_sharpe_ex_2020": shp(sn[~sn.index.str.startswith("2020")].to_numpy()),
                "correlation": {}}
            for k, v in S.items():
                j = pd.concat([led, v], axis=1, join="inner").dropna()
                if len(j) > 30 and j.iloc[:, 0].std() > 0 and j.iloc[:, 1].std() > 0:
                    line["correlation"][k] = {"rho": round(float(j.corr().iloc[0, 1]), 4), "n_days": int(len(j))}
            doc["lines"][f"{r}_{c}"] = line
    OUT.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    for k, v in doc["lines"].items():
        print(f"{k:8s} n {v['trades']:5d} ({v['trades_per_year']}/yr)  net Sh 16-23 {v['net_sharpe_2016_2023']:+.2f} "
              f"So {v['net_sortino_2016_2023']:+.2f} gross {v['gross_sharpe_2016_2023']:+.2f} | full net {v['net_sharpe_full']:+.2f} "
              f"gross {v['gross_sharpe_full']:+.2f} | ex-2020 {v['net_sharpe_ex_2020']:+.2f} | hit {v['hit_net']:.3f} skew "
              f"{v['skew_per_trade_usd']:+.2f} | $ {v['mean_gross_usd']:+.2f}/{v['mean_net_usd']:+.2f} | rho "
              + " ".join(f"{a}{b['rho']:+.2f}" for a, b in v["correlation"].items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
