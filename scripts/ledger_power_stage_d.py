"""POWER for Stage D of the settlement flow ledger on NG (deposit §P5: Q5 = + TAS_imb[t, τ]; P5/P6 collapsed because
the funds' TAS use is unknown, D4/G10; judged by §6's retention rule with D631's midday control; D633). Written before
Stage D's pre-registration and runner.

It reads NO window flow and no price. The in-sample side is the predictor panel, the TAS imbalance panel (Stage D's
own input, `build_tas_imbalance_panel.py`) and unsigned window volume. The noise is the pre-sample's.

THE STAGES (at τ*, the Stage A panel's; Stage D has no fitted parameter, deposit §6):
  * A: μ = P1;
  * D: μ = P1 + TAS_imb(τ*), the outright TAS in the held months from the session open to τ*, in contracts.
  * Midday: P1(11:30) + TAS_imb(11:30), against the 11:50–12:20 flow.

SIMULATION: S_win = 0.061 × P1 + γ × TAS_imb(τ*) + V_win × u_w, and S_plc = V_plc × u_p (pre-sample residuals, 10-day
blocks; `ledger_power_stage_c1`'s volumes and noise). γ, the window's aggressive contracts per contract of TAS
imbalance (the liquidity providers' hedge), is in {0 (the null), 0.03, 0.061, 0.12, 0.25}; 200 datasets each.
Reported: the rate of clause 1 (ratio ≥ 1.10) together with clause 3 (the window gain exceeds the midday gain); the
median ratio; the scale of TAS_imb against P1. Clause 2 (H2's t) is a price test and is not simulated.

    uv run python scripts/ledger_power_stage_d.py [--check]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import ledger_power_stage_b as PB  # noqa: E402
import ledger_power_stage_c1 as PC  # noqa: E402

P = PB.P
TAS = REPO / "data" / "ledger_tas_imbalance_daily.csv.gz"
OUT_JSON = REPO / "data" / "ledger_power_stage_d.json"
SEED, REPS, BLOCK = 20260929, 200, 10
GAMMAS = (0.0, 0.03, 0.061, 0.12, 0.25)
FLAGS = P.FLAGS["NG"]


def tas_sum(days: list[str], held: pd.Series, col: str) -> np.ndarray:
    t = pd.read_csv(TAS, encoding="utf-8", usecols=["day", "ym", col])
    if (t["day"] >= P.CUT).any():
        raise RuntimeError("a TAS row on or after the cut is in memory")
    piv = t.pivot_table(index="day", columns="ym", values=col, aggfunc="sum")
    out = []
    for d in days:
        row = piv.loc[d] if d in piv.index else pd.Series(dtype=float)
        out.append(float(row.reindex(held[d].split(";")).fillna(0.0).sum()))
    return np.array(out)


def build() -> dict[str, Any]:
    rng = np.random.default_rng(SEED)
    f = pd.read_csv(P.FLOW, encoding="utf-8")
    f = f[f["root"] == "NG"]
    if (f["day"] >= P.CUT).any():
        raise RuntimeError("a flow row on or after the cut is in memory")
    star = f[f["is_tau_star"] == 1].set_index("day").sort_index()
    days = list(star.index)
    held = star["held"]
    p1 = star["q_est"].to_numpy()
    p1_plc = f[f["tau"] == "11:30"].set_index("day")["q_est"].reindex(days).to_numpy()
    tas = {t: tas_sum(days, held, f"net_to_{t}") for t in ("1350", "1400", "1410", "1130")}
    idx = star["tau"].map({"13:50": "1350", "14:00": "1400", "14:10": "1410"}).to_numpy()
    q5 = np.array([tas[k][i] for i, k in enumerate(idx)])
    q5_plc = tas["1130"]
    r28 = f[f["tau"] == "14:28"].set_index("day")["r_held"].reindex(days).to_numpy()
    cal = pd.read_csv(P.CAL, encoding="utf-8")
    cal = cal[cal["root"] == "NG"].set_index("date")
    C = np.column_stack([np.ones(len(days)), r28] + [cal.loc[days, fl].to_numpy(float) for fl in FLAGS])
    ok = np.isfinite(p1) & np.isfinite(p1_plc) & np.isfinite(r28)
    vw, vp = PC.volumes(days, held)
    U = PB.presample_noise()[:, 1]
    n = int(ok.sum())
    Co = C[ok]
    scale = {"sd_p1": float(np.std(p1[ok])), "sd_tas_imb_at_tau_star": float(np.std(q5[ok])),
             "median_abs_tas_imb": float(np.median(np.abs(q5[ok]))), "corr_p1_tas_imb": float(np.corrcoef(p1[ok], q5[ok])[0, 1]),
             "share_days_with_tas": float(np.mean(q5[ok] != 0))}

    def draw() -> np.ndarray:
        ix = np.empty(n, dtype=int)
        i = 0
        while i < n:
            s = int(rng.integers(0, len(U) - BLOCK))
            k = min(BLOCK, n - i)
            ix[i:i + k] = np.arange(s, s + k)
            i += k
        return U[ix]

    a, dd = p1[ok], (p1 + q5)[ok]
    ap_, dp_ = p1_plc[ok], (p1_plc + q5_plc)[ok]
    sims = {}
    for g in GAMMAS:
        hits, ratios = [], []
        for _ in range(REPS):
            s = 0.061 * a + g * q5[ok] + vw[ok] * draw()
            sp = vp[ok] * draw()
            ra, rd = PC.pcorr(a, s, Co), PC.pcorr(dd, s, Co)
            pa, pd_ = PC.pcorr(ap_, sp, Co), PC.pcorr(dp_, sp, Co)
            hits.append(bool(ra > 0 and rd >= 1.10 * ra and (rd - ra) > (pd_ - pa)))
            ratios.append(rd / ra)
        sims[f"{g:g}"] = {"reps": REPS, "clause1_and_midday": float(np.mean(hits)),
                          "ratio_median": float(np.median(ratios))}
    return {"seed": SEED, "gammas": GAMMAS, "n_days": n, "scale": scale, "sims": sims}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    out = build()
    text = json.dumps(out, indent=1, sort_keys=True, default=float) + "\n"
    if a.check:
        if OUT_JSON.read_text(encoding="utf-8") != text:
            raise RuntimeError(f"{OUT_JSON.name} does not reproduce")
        print(f"[check] {OUT_JSON.name} reproduces byte for byte")
        return 0
    OUT_JSON.write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps({k: out[k] for k in ("n_days", "scale")}, indent=1))
    for k, v in out["sims"].items():
        print("gamma", k, v)
    return 0


if __name__ == "__main__":
    sys.exit(main())
