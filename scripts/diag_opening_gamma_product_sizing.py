"""The paper prize-sizing for the gamma-product design (D662 s.2), INPUTS ONLY: no return after the open is read. Per
in-sample ES session (2016-01-04 -> 2025-02-28, the runners' sealed loader), the dealer rebalancing flow each shock
implies and its square-root-law push, against D661's bar.

    uv run python scripts/diag_opening_gamma_product_sizing.py --data-root "C:/Users/O/Desktop/Projects/Backtest Framework/data"

G$ (dollars of hedge per 1% move) = G x $50 x F^2 x 0.01, G from data/opening/agents.csv (A4's column: OI at the prior
close, Black-76 gamma at the prior settlement, options alive after 09:30), F = the prior RTH close.
Shock 1, the gap: Q = |G$| x |gap| (%), the lagged hedge of the overnight move.
Shock 2, the stop run: Q = |G$| x p (%), p = how far the 09:30-10:00 range penetrated the prior RTH high or low
(0 if neither), the lagged hedge of the stop-driven move. Stops' own flow is not added (CFTC: 0.9% of ES volume).
Push = Y sigma_d sqrt(Q / V): sigma_d the prior 20 sessions' RTH close-to-close sd, V the prior 20 sessions' mean RTH
dollar volume; Y = 1 (best case) and 0.5. Writes data/opening/gamma_product_sizing.json.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "opening" / "gamma_product_sizing.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    sys.path.insert(0, str(REPO / "scripts"))
    import diag_opening_mechanics as M

    V = M.load_v2()
    b, use, _ = V.load_inputs(a.data_root, False)
    bar = json.loads((REPO / "data" / "opening" / "prize_bar.json").read_text(encoding="utf-8"))["bar"]["ES"]
    x = b[(b["root"] == "ES") & (b["hhmm"] >= "09:30") & (b["hhmm"] <= "15:59")]
    g = x.groupby("session")
    d = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(), "close": g["close"].last(),
                      "dv": (x["close"] * x["volume"] * 50.0).groupby(x["session"]).sum()})
    orng = x[x["hhmm"] < "10:00"].groupby("session")
    d["or_hi"], d["or_lo"] = orng["high"].max(), orng["low"].min()
    d["pc"], d["ph"], d["pl"] = d["close"].shift(1), d["high"].shift(1), d["low"].shift(1)
    d["sig"] = (np.log(d["close"] / d["pc"]) * 1e4).shift(1).rolling(20, min_periods=15).std()
    d["V"] = d["dv"].shift(1).rolling(20, min_periods=15).mean()
    ag = pd.read_csv(REPO / "data" / "opening" / "agents.csv", encoding="utf-8", dtype={"session": str},
                     usecols=["root", "session", "G"])
    d["G"] = ag[ag["root"] == "ES"].set_index("session")["G"].reindex(d.index)
    d = d[(d.index >= "2016-01-04") & (d.index < "2025-03-01") & d.index.isin(set(use))].dropna(
        subset=["pc", "sig", "V", "G", "or_hi", "or_lo"])
    gd = d["G"] * 50.0 * d["pc"] ** 2 * 0.01  # $ of hedge per 1% move
    gap_pct = (d["open"] / d["pc"] - 1) * 100
    pen_pct = np.maximum(d["or_hi"] / d["ph"] - 1, 0) * 100 + np.maximum(1 - d["or_lo"] / d["pl"], 0) * 100
    out: dict = {"sessions": int(len(d)), "G_dollar_per_1pct_bn": {k: float(v) for k, v in
                                                                  (gd / 1e9).describe(percentiles=[.05, .5, .95]).items()},
                 "short_gamma_share": float((gd < 0).mean()), "bar_daily_60min_bp": bar["daily_60min"]["s_needed_bp"],
                 "bar_break_even_bp": bar["break_even_s_bp"], "shocks": {}}
    for name, mv in (("gap", gap_pct.abs()), ("stop_run", pen_pct)):
        q = gd.abs() * mv  # $ per session
        for y in (1.0, 0.5):
            push = y * d["sig"] * np.sqrt(q / d["V"])
            out["shocks"].setdefault(name, {})[f"Y{y}"] = {
                "flow_bn_median": float((q / 1e9).median()), "flow_bn_p90": float((q / 1e9).quantile(0.9)),
                "push_bp_mean": float(push.mean()), "push_bp_median": float(push.median()),
                "push_bp_p90": float(push.quantile(0.9)), "share_days_push_ge_daily_bar": float((push >= out["bar_daily_60min_bp"]).mean()),
                "share_days_shock_nonzero": float((mv > 0).mean()),
                "push_bp_mean_short_gamma_days": float(push[gd < 0].mean())}
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
