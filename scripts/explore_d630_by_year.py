"""POST HOC, on D630's spent in-sample: why the NG settlement trade earns in 2022 and barely elsewhere. The primary
trade only (fill at the close of bar t0+1, exit at the close of 14:29, no stop or target), broken down by year.

    uv run python scripts/explore_d630_by_year.py      # the venv -> data/ledger_d630_by_year.json

Per year, on D630's own trades (known answer: the pooled trades reproduce D630's n and mean exactly):
1. PERFORMANCE: trades, the share of days traded, mean / median / t gross, hit rate, net at full size ($26) and at MNG
   ($5), MNG net Sharpe and Sortino over the year's days (zeros on untraded days).
2. SCALE: the NG price, the trade's move in dollars, in basis points of the price, and in units of the day's own
   remaining-to-settlement sigma (sigma_rem_ret at the trade's t0). Dollars = price x bp; a year that is only richer in
   dollars is a price or volatility year, not an edge year.
3. THE FUNDS: BOIL and KOLD AUM, the predicted rebalance |q| in contracts, the predicted impact |I| (dollars, bp, sigma),
   the participation |q| / the traded contract's window volume, the share of buys, and the share of |q| from the long
   fund.
4. THE CONFOUND: leveraged funds rebalance WITH the day's move, so the trade is a continuation bet on big-move days.
   The same rule on untraded days (continuation without the funds), traded minus untraded, and the trade's move
   against the day's move to t0 (r_held, in sigma).
5. THE AFTERMATH: the post-window fade (14:29 close to 15:00, against the direction).
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
sys.path.insert(0, str(REPO / "src"))
OUT = REPO / "data" / "ledger_d630_by_year.json"
PUBLISHED = REPO / "data" / "ledger_h2_ng_stage_a.json"


def _main_checkout(repo: Path) -> Path:
    p = repo
    while p.parent != p:
        if p.name == "worktrees" and p.parent.name == ".claude":
            return p.parent.parent
        p = p.parent
    return repo


def _load(name: str) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    assert s is not None and s.loader is not None
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


R = _load("run_h2_ng_stage_a")
H = sys.modules["run_h1a_stage_a"]
DATA = _main_checkout(REPO) / "data"
for mod, names in ((R, ("FLOW", "BARS", "PANEL")), (H, ("FLOW", "PANEL", "FSHARE"))):
    for n in names:
        p = getattr(mod, n)
        if not p.exists():
            setattr(mod, n, DATA / p.name)


def t_of(x: np.ndarray) -> float:
    x = x[np.isfinite(x)]
    return float(x.mean() / (x.std(ddof=1) / math.sqrt(len(x)))) if len(x) > 2 else float("nan")


def main() -> int:
    C = R._load_cs()
    d = R.build(read_returns=True)["d"]
    g = R.signed(d)
    tr = d["traded"].to_numpy()
    ok = tr & np.isfinite(g)
    pub = json.loads(PUBLISHED.read_text(encoding="utf-8"))["NG"]
    if int(ok.sum()) != pub["n"] or not math.isclose(float(g[ok].mean()), pub["gate"]["mean"], abs_tol=1e-9):
        raise SystemExit("known answer: the trades do not reproduce D630's n and mean")
    # the day's own sigma of the remaining return, at its t0; price at t0; the move to t0 (r_held at t0)
    flow = pd.read_csv(H.FLOW, encoding="utf-8", usecols=["root", "day", "tau", "r_held", "q_est", "V_d"])
    flow = flow[flow["root"] == "NG"].set_index(["day", "tau"])
    key = list(zip(d["day"], d["tau"]))
    d["r_to_t0"] = flow["r_held"].reindex(key).to_numpy()
    d["V_d"] = flow["V_d"].reindex(key).to_numpy()
    sd = np.array([d[f"sd_{t}"].iloc[i] for i, t in enumerate(d["tau"])], dtype=float)
    px = d["p_held"].to_numpy(float)
    d["g"] = g
    d["g_bp"] = g / (R.MULT * px) * 1e4
    d["g_sig"] = g / (R.MULT * px * sd)
    d["I_bp"] = d["absI_px"] / px * 1e4
    d["I_sig"] = d["absI_px"] / (px * sd)
    d["r_sig"] = d["dir"] * d["r_to_t0"] / sd  # the day's move to t0 in the trade's direction, in sigma
    d["absq"] = d["q_est"].abs()
    d["long_share"] = d["aum_long"] / (d["aum_long"] + d["aum_inverse"])
    win = pd.read_csv(R.PANEL, encoding="utf-8", usecols=["root", "kind", "day", "ym", "vol_win"])
    win = win[(win["root"] == "NG") & (win["kind"] == "outright")].set_index(["day", "ym"])["vol_win"]
    d["vol_win"] = win.reindex(list(zip(d["day"], d["traded_ym"]))).to_numpy(float)
    d["particip"] = d["absq"] / d["vol_win"]
    un = ~tr & np.isfinite(g)
    rows = []
    for y, x in d.groupby("year"):
        i = x.index.to_numpy()
        o, u = ok[i], un[i]
        gt = g[i][o]
        daily = np.where(o, g[i] * R.MNG_MULT / R.MULT - R.MNG_COST, 0.0)
        daily_full = np.where(o, g[i] - R.COST, 0.0)
        t = x[o]
        rows.append({
            "year": y, "days": int(len(x)), "trades": int(o.sum()), "share_traded": float(o.mean()),
            "mean_gross": float(gt.mean()), "median_gross": float(np.median(gt)), "t_gross": t_of(gt),
            "hit_rate_gross": float((gt > 0).mean()), "mean_net_full": float(gt.mean() - R.COST),
            "mean_net_mng": float(gt.mean() / 10 - R.MNG_COST), "sharpe_net_mng": C.sharpe(daily),
            "sortino_net_mng": C.sortino(daily), "sharpe_net_full": C.sharpe(daily_full),
            "total_net_full": float(daily_full.sum()),
            "ng_price": float(t["p_held"].mean()), "sigma_rem_ret_pct": float(np.nanmean(sd[i][o]) * 100),
            "move_bp": float(t["g_bp"].mean()), "t_bp": t_of(t["g_bp"].to_numpy()),
            "move_sigma": float(t["g_sig"].mean()), "t_sigma": t_of(t["g_sig"].to_numpy()),
            "aum_boil_musd": float(t["aum_long"].mean() / 1e6), "aum_kold_musd": float(t["aum_inverse"].mean() / 1e6),
            "abs_q_contracts": float(t["absq"].mean()), "abs_I_usd": float(t["absI_usd"].mean()),
            "abs_I_bp": float(t["I_bp"].mean()), "abs_I_sigma": float(t["I_sig"].mean()),
            "window_volume": float(t["vol_win"].mean()), "participation": float(np.nanmedian(t["particip"])),
            "share_buys": float((t["dir"] > 0).mean()), "long_fund_aum_share": float(t["long_share"].mean()),
            "day_move_to_t0_sigma": float(t["r_sig"].mean()),
            "untraded_n": int(u.sum()), "untraded_mean_gross": float(g[i][u].mean()) if u.any() else float("nan"),
            "untraded_t": t_of(g[i][u]), "untraded_move_sigma": float(x[u]["g_sig"].mean()) if u.any() else float("nan"),
            "traded_minus_untraded": float(gt.mean() - g[i][u].mean()) if u.any() else float("nan"),
            "fade_mean": float(np.nanmean(x["fade"].to_numpy()[o])), "fade_t": t_of(x["fade"].to_numpy()[o])})
    tab = pd.DataFrame(rows).set_index("year")
    # pooled: does the per-trade move in sigma differ by year once price and vol are taken out?
    o = d[ok]
    pooled = {"move_sigma_all": float(o["g_sig"].mean()), "t_sigma_all": t_of(o["g_sig"].to_numpy()),
              "move_sigma_ex2022": float(o.loc[o["year"] != "2022", "g_sig"].mean()),
              "t_sigma_ex2022": t_of(o.loc[o["year"] != "2022", "g_sig"].to_numpy()),
              "move_bp_ex2022": float(o.loc[o["year"] != "2022", "g_bp"].mean()),
              "t_bp_ex2022": t_of(o.loc[o["year"] != "2022", "g_bp"].to_numpy())}
    # within all trades: the dollar edge against price and |I| in sigma (terciles), to separate scale from dose
    for col in ("p_held", "I_sig", "r_sig", "particip"):
        q = np.nanquantile(o[col], [1 / 3, 2 / 3])
        b = np.digitize(o[col], q)
        pooled[f"by_{col}_tercile"] = {str(k): {"n": int((b == k).sum()), "mean_gross": float(o["g"][b == k].mean()),
                                               "move_sigma": float(o["g_sig"][b == k].mean()),
                                               "t_sigma": t_of(o["g_sig"][b == k].to_numpy()),
                                               "range": [float(o[col][b == k].min()), float(o[col][b == k].max())]}
                                       for k in range(3)}
    doc = {"spec": "POST HOC on D630's spent in-sample: the primary trade by year (the principal, 2026-09-28)",
           "by_year": tab.reset_index().to_dict("records"), "pooled": pooled}
    OUT.write_text(json.dumps(doc, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    pd.set_option("display.width", 250)
    cols1 = ["trades", "share_traded", "mean_gross", "median_gross", "t_gross", "hit_rate_gross", "mean_net_full",
             "mean_net_mng", "sharpe_net_mng", "sortino_net_mng", "sharpe_net_full", "total_net_full"]
    cols2 = ["ng_price", "sigma_rem_ret_pct", "move_bp", "t_bp", "move_sigma", "t_sigma", "abs_I_usd", "abs_I_bp",
             "abs_I_sigma"]
    cols3 = ["aum_boil_musd", "aum_kold_musd", "abs_q_contracts", "window_volume", "participation", "share_buys",
             "day_move_to_t0_sigma"]
    cols4 = ["untraded_n", "untraded_mean_gross", "untraded_t", "untraded_move_sigma", "traded_minus_untraded",
             "fade_mean", "fade_t"]
    for c in (cols1, cols2, cols3, cols4):
        print(tab[c].round(3).to_string(), "\n")
    print(json.dumps(pooled, indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
