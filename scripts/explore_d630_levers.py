"""POST HOC, on D630's spent in-sample: can the NG settlement trade earn more per trade? Four levers singled out, then
stacked in a declared order (the principal, 2026-09-28: "explore 1-5, parse out the results, then combine their
effects"). Exploratory: every threshold here is chosen by the author after D630 and the year breakdown were read, so
nothing here is a result; a lever worth keeping must be pre-registered and read in the joint vault run.

    uv run python scripts/explore_d630_levers.py      # the venv -> data/ledger_d630_levers.json

THE BASE: D630's primary trade (fill at the close of bar t0+1, one tick of slippage, exit at the close of 14:29).

THE LEVERS (all information is available at t0; every filter threshold is POINT-IN-TIME: a quantile of the PRIOR
traded days only, with at least MIN_PRIOR of them, so the first MIN_PRIOR trades are never taken by a filter. The same
filter with whole-sample thresholds is reported beside it as a LOOK-AHEAD upper bound):
  L1a  predicted impact: trade only when |I| is at or above the prior trades' 2/3 quantile.
  L1b  size of the flow against the market: |q| / V_d (the funds' predicted contracts over the held contracts' mean
       whole-session volume, t-20..t-1) inside the prior trades' middle tercile. The year breakdown's band used the
       SAME day's window volume, which is not known at entry; this is its point-in-time stand-in.
  L1s  size by impact: 1, 2 or 3 contracts by the prior-trade tercile of |I| (a sizing rule, not a filter).
  L2   price floor: trade only when the held contract's price at t0 is at least $3.00 (L2b: $4.00). Round numbers,
       declared here; the cost is fixed in dollars and the edge is in basis points.
  L3   passive entry: a limit at the close of bar t0+1, filled only if a bar from t0+2 to t0+4 trades THROUGH it by a
       tick (a touch is not a fill); no fill, no trade. It saves the tick of slippage (full: $26 -> $16; MNG: $5 -> $4)
       and pays in missed trades and adverse selection.
  L4   the fade leg: at 14:29 reverse and hold to the close of the 14:59 bar (D630's section 7.5 fade), one extra round
       trip at the base cost.
  L5   other markets: NOT RUN. CL's H2 has never been read, and running it post hoc would spend CL's in-sample for any
       later pre-registered test; the gold and silver pairs have no flow panel. The principal's decision.
THE LADDER (declared before the run): base -> +L1a -> +L2 -> +L3 -> +L4, and the same ladder with L1b in place of L1a.

REPORTED per variant, at full size (NG, 10,000 MMBtu) and at MNG (1/10): trades, gross and net per trade, net Sharpe
(monthly block-bootstrap SE) and Sortino, daily skew, max drawdown, profitable years, net Sharpe without 2022, and
2022's share of the net total. Daily series run over all 1,936 in-sample days, zeros on untraded days.
KNOWN ANSWER (raises): the base reproduces D630's full and MNG net Sharpes exactly.
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
OUT = REPO / "data" / "ledger_d630_levers.json"
MIN_PRIOR = 100
FLOOR, FLOOR_B = 3.00, 4.00
TICK = 0.001
LIMIT_BARS = 3
COST_LIMIT = {"full": 16.0, "micro": 4.0}


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
R, H = X.R, X.H


def pit_quantile(v: np.ndarray, q: float) -> np.ndarray:
    """The q-quantile of the PRIOR entries of v (NaN until MIN_PRIOR of them)."""
    out = np.full(len(v), np.nan)
    for k in range(MIN_PRIOR, len(v)):
        out[k] = np.quantile(v[:k], q)
    return out


def limit_entry(r: dict[str, Any]) -> float | None:
    """Gross full-contract dollars of the passive entry, or None when the limit is not traded through in time."""
    first, last = R.add_min(r["t0"], 2), R.add_min(r["t0"], 2 + LIMIT_BARS)
    L = r["fill"]
    for m, h, lw in zip(r["mins"], r["hi"], r["lo"]):
        if first <= m < last and ((lw <= L - TICK) if r["dir"] > 0 else (h >= L + TICK)):
            return R.money(r["dir"], L, r["exit"])
    return None


def main() -> int:
    C = R._load_cs()
    d, rows = X.trades()
    days = d["day"].to_numpy()
    years = np.array([x[:4] for x in days])
    idx = np.array([r["i"] for r in rows])
    n = len(rows)
    flow = pd.read_csv(H.FLOW, encoding="utf-8", usecols=["root", "day", "tau", "V_d"])
    flow = flow[flow["root"] == "NG"].set_index(["day", "tau"])["V_d"]
    tr = d.iloc[idx]
    g = np.array([r["g_primary"] for r in rows])
    absI = tr["absI_usd"].to_numpy(float)
    part = (tr["q_est"].abs().to_numpy() / flow.reindex(list(zip(tr["day"], tr["tau"]))).to_numpy())
    price = tr["p_held"].to_numpy(float)
    fade = tr["fade"].to_numpy(float)
    lim = [limit_entry(r) for r in rows]
    lim_filled = np.array([x is not None for x in lim])
    g_lim = np.array([x if x is not None else np.nan for x in lim])

    i_hi_pit = pit_quantile(absI, 2 / 3)
    i_lo_pit = pit_quantile(absI, 1 / 3)
    p_lo_pit, p_hi_pit = pit_quantile(part, 1 / 3), pit_quantile(part, 2 / 3)
    L1a = absI >= i_hi_pit
    L1a_la = absI >= np.quantile(absI, 2 / 3)
    L1b = (part >= p_lo_pit) & (part <= p_hi_pit)
    q1, q2 = np.quantile(part, [1 / 3, 2 / 3])
    L1b_la = (part >= q1) & (part <= q2)
    size_s = np.where(np.isnan(i_hi_pit), 0, 1 + (absI >= i_lo_pit).astype(int) + (absI >= i_hi_pit).astype(int))
    L2, L2b = price >= FLOOR, price >= FLOOR_B

    def book(take: np.ndarray, size: np.ndarray | None = None, limit: bool = False, fade_leg: bool = False
             ) -> dict[str, Any]:
        size = np.ones(n) if size is None else size
        res: dict[str, Any] = {}
        for cls, scale, cost in (("full", 1.0, R.COST), ("micro", X.RATIO, R.MNG_COST)):
            per = np.full(n, np.nan)
            gross = np.full(n, np.nan)
            if limit:
                ok = take & lim_filled
                gross[ok] = g_lim[ok] * scale
                per[ok] = gross[ok] - COST_LIMIT[cls]
            else:
                ok = take.copy()
                gross[ok] = g[ok] * scale
                per[ok] = gross[ok] - cost
            if fade_leg:
                gross[ok] += fade[ok] * scale
                per[ok] += fade[ok] * scale - cost
            per, gross = per * size, gross * size
            daily = np.zeros(len(d))
            daily[idx[ok]] = per[ok]
            x22 = years != "2022"
            tot = daily.sum()
            yr = pd.Series(daily).groupby(years).sum()
            res[cls] = {"trades": int(ok.sum()), "contract_trades": float(size[ok].sum()),
                        "gross_per_trade": float(np.nanmean(gross[ok])), "net_per_trade": float(np.nanmean(per[ok])),
                        "sharpe_net": C.sharpe(daily), "sharpe_se": C.sharpe_boot(daily, list(days)),
                        "sortino_net": C.sortino(daily), "skew_daily": float(pd.Series(daily).skew()),
                        "max_dd": float((np.cumsum(daily) - np.maximum.accumulate(np.cumsum(daily))).min()),
                        "total_net": float(tot), "profitable_years": int((yr > 0).sum()), "years": int(len(yr)),
                        "share_2022": float(yr.get("2022", 0.0) / tot) if tot != 0 else float("nan"),
                        "sharpe_net_ex2022": C.sharpe(daily[x22]),
                        "trades_by_year": {y: int((ok & (tr["year"].to_numpy() == y)).sum()) for y in sorted(set(years))},
                        "net_per_trade_by_year": {y: float(np.nanmean(per[ok & (tr["year"].to_numpy() == y)]))
                                                  if (ok & (tr["year"].to_numpy() == y)).any() else None
                                                  for y in sorted(set(years))}}
        return res

    every = np.ones(n, bool)
    variants: dict[str, dict[str, Any]] = {
        "base (D630 primary)": book(every),
        "L1a |I| top tercile (PIT)": book(L1a), "L1a |I| top tercile (look-ahead)": book(L1a_la),
        "L1b |q|/V_d middle tercile (PIT)": book(L1b), "L1b |q|/V_d middle tercile (look-ahead)": book(L1b_la),
        "L1s size 1/2/3 by |I| tercile (PIT)": book(size_s > 0, size=size_s.astype(float)),
        "L2 price >= $3": book(L2), "L2b price >= $4": book(L2b),
        "L3 passive entry": book(every, limit=True),
        "L4 fade leg": book(every, fade_leg=True),
        "ladder A1: L1a": book(L1a), "ladder A2: L1a + L2": book(L1a & L2),
        "ladder A3: L1a + L2 + L3": book(L1a & L2, limit=True),
        "ladder A4: L1a + L2 + L3 + L4": book(L1a & L2, limit=True, fade_leg=True),
        "ladder B1: L1b": book(L1b), "ladder B2: L1b + L2": book(L1b & L2),
        "ladder B3: L1b + L2 + L3": book(L1b & L2, limit=True),
        "ladder B4: L1b + L2 + L3 + L4": book(L1b & L2, limit=True, fade_leg=True)}
    pub = json.loads((REPO / "data" / "ledger_h2_ng_stage_a.json").read_text(encoding="utf-8"))["NG"]
    b = variants["base (D630 primary)"]
    if not (np.isclose(b["full"]["sharpe_net"], pub["performance"]["sharpe_net"], rtol=0, atol=1e-12)
            and np.isclose(b["micro"]["sharpe_net"], pub["component_mng"]["sharpe_net"], rtol=0, atol=1e-12)):
        raise SystemExit("known answer: the base does not reproduce D630's net Sharpes")
    diag = {"limit_fill_rate": float(lim_filled.mean()),
            "limit_filled_mean_gross_market_entry": float(g[lim_filled].mean()),
            "limit_unfilled_mean_gross_market_entry": float(g[~lim_filled].mean()),
            "limit_filled_mean_gross_limit_entry": float(np.nanmean(g_lim)),
            "fade_mean_gross": float(fade.mean()), "pit_filters_undefined_first_trades": MIN_PRIOR,
            "L1a_pit_vs_lookahead_agreement": float((L1a == L1a_la).mean()),
            "L1b_pit_vs_lookahead_agreement": float((L1b == L1b_la).mean())}
    OUT.write_text(json.dumps({"spec": __doc__.split("\n\n")[0], "diagnostics": diag, "variants": variants},
                              indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(diag, indent=1))
    for cls in ("full", "micro"):
        print(f"\n{'FULL NG ($26 RT; passive $16)' if cls == 'full' else 'MNG ($5 RT; passive $4)'}")
        tab = pd.DataFrame({k: {"trades": v[cls]["trades"], "gross/tr": round(v[cls]["gross_per_trade"], 2),
                                "net/tr": round(v[cls]["net_per_trade"], 2),
                                "Sharpe (SE)": f"{v[cls]['sharpe_net']:+.2f} ({v[cls]['sharpe_se']:.2f})",
                                "Sortino": round(v[cls]["sortino_net"], 2), "skew": round(v[cls]["skew_daily"], 2),
                                "maxDD": round(v[cls]["max_dd"]), "yrs+": f"{v[cls]['profitable_years']}/{v[cls]['years']}",
                                "Sh ex22": round(v[cls]["sharpe_net_ex2022"], 2),
                                "2022 share": round(v[cls]["share_2022"], 2)} for k, v in variants.items()}).T
        with pd.option_context("display.width", 250):
            print(tab.to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
