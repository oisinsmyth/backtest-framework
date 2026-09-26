"""POST HOC, after D630's one run: is NG's H2 the funds' flow, or plain continuation on big-move days? Nothing here
changes the verdict.

D630 passed (mean $66 a trade, t 5.01). Traded days are selected on |I| = 0.7 σ_d √(|Q|/V) P with Q ∝ AUM × r(τ),
so they are big-move days as well as big-fund days. The pre-registered untraded-day control (the same rule on the
908 untraded days: −$6) does not separate the two. This script, on the runner's own design (`run_h2_ng_stage_a.build`):
  * the PARTNER control (CLAUDE.md: randomise the partner, not the membership): traded against untraded days WITHIN
    deciles of the standardised move |r(τ)| / σ_d, as a regression of g on the traded flag with decile fixed
    effects, and the decile table;
  * the same with the funds' size in contracts per unit return (log) as the regressor, within move deciles;
  * the top ten trades by gross P&L, named, with their fill and exit bars (CLAUDE.md: name the top trade).
Output: `data/ledger_h2_ng_posthoc.json`.

    uv run python -W error::RuntimeWarning scripts/explore_h2_ng_partner_control.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import run_h2_ng_stage_a as R  # noqa: E402

OUT = REPO / "data" / "ledger_h2_ng_posthoc.json"


def ols_t(y: np.ndarray, X: np.ndarray, j: int) -> dict[str, float]:
    keep = [0, j] + [k for k in range(1, X.shape[1]) if k != j and np.ptp(X[:, k]) > 0]
    b, v = R.H.hc1(y, X[:, keep], j=1)
    return {"beta": b, "se": float(np.sqrt(v)), "t": b / float(np.sqrt(v)), "n": int(len(y))}


def main() -> int:
    b = R.build(read_returns=True)
    d = b["d"]
    f = R.H.load_flow("NG")[0]
    s = f[f["is_tau_star"] == 1].set_index("day")
    d["r_tau"] = s["r_held"].reindex(d["day"]).to_numpy()
    d["sigma_d"] = s["sigma_d"].reindex(d["day"]).to_numpy()
    d["c_scale"] = (s["c_long"].abs() + s["c_inverse"].abs()).reindex(d["day"]).to_numpy()
    g = R.signed(d)
    ok = np.isfinite(g) & np.isfinite(d["r_tau"]) & np.isfinite(d["sigma_d"]) & (d["sigma_d"] > 0)
    z = (d["r_tau"].abs() / d["sigma_d"]).to_numpy()
    dec = np.full(len(d), -1)
    dec[ok] = pd.qcut(z[ok], 10, labels=False)
    tr = d["traded"].to_numpy()
    out: dict[str, Any] = {"note": "POST HOC, after D630's run; the verdict is unchanged"}
    table = []
    for k in range(10):
        m = ok & (dec == k)
        a, u = g[m & tr], g[m & ~tr]
        table.append({"decile": k, "z_median": float(np.median(z[m])), "traded_n": int(len(a)),
                      "traded_mean": float(a.mean()) if len(a) else None, "untraded_n": int(len(u)),
                      "untraded_mean": float(u.mean()) if len(u) else None})
    out["by_move_decile"] = table
    FE = np.column_stack([(dec[ok] == k).astype(float) for k in range(1, 10)])
    X = np.column_stack([np.ones(ok.sum()), tr[ok].astype(float), FE])
    out["traded_within_move_deciles"] = ols_t(g[ok], X, 1)
    Xc = np.column_stack([np.ones(ok.sum()), np.log(d["c_scale"].to_numpy()[ok]), FE])
    out["log_fund_scale_within_move_deciles_all_days"] = ols_t(g[ok], Xc, 1)
    okt = ok & tr
    FEt = np.column_stack([(dec[okt] == k).astype(float) for k in range(1, 10)])
    Xt = np.column_stack([np.ones(okt.sum()), np.log(d["c_scale"].to_numpy()[okt]), FEt])
    out["log_fund_scale_within_move_deciles_traded_days"] = ols_t(g[okt], Xt, 1)
    top = np.argsort(np.where(tr & np.isfinite(g), g, -np.inf))[::-1][:10]
    out["top_ten_trades"] = [{"day": d["day"].iloc[i], "contract": d["traded_ym"].iloc[i], "t0": d["tau"].iloc[i],
                              "dir": float(d["dir"].iloc[i]), "gross_usd": float(g[i]),
                              "move_z": float(z[i]), "r_tau": float(d["r_tau"].iloc[i])} for i in top]
    tot = float(g[tr & np.isfinite(g)].sum())
    out["top_ten_share_of_gross"] = float(g[top].sum() / tot)
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True, default=float) + "\n", encoding="utf-8", newline="\n")
    for row in table:
        print(row)
    for k in ("traded_within_move_deciles", "log_fund_scale_within_move_deciles_all_days",
              "log_fund_scale_within_move_deciles_traded_days"):
        print(k, {a: round(v, 3) for a, v in out[k].items()})
    print("top ten share of gross", round(out["top_ten_share_of_gross"], 3))
    for t in out["top_ten_trades"]:
        print(t)
    return 0


if __name__ == "__main__":
    sys.exit(main())
