"""POWER for Stage C1 of the settlement flow ledger on NG (deposit §P3.4's baseline creation model, judged by §6's
retention rule out of sample; D632). Written before Stage C1's pre-registration and runner.

It reads NO in-sample window flow and no price. The in-sample side is the predictor panel, the funds' published NAV
and AUM (the creation flow, which is C1's own fitting target, deposit §8), and unsigned window volume. The noise is
the pre-sample's.

THE STAGES (at τ*, the Stage A panel's):
  * A: μ = P1;
  * C1: μ = P1 + Q3_hat, with Q3_hat = Σ_f L_f × ΔCreate_hat_f / (10,000 × P_held), from `ledger_fund_flows`'
    walk-forward forecast (252-day training windows, 63-day tests).

THE CEILINGS, from the flows alone: if the window flow is proportional to the funds' NET trade P1 + Q3 (Q3 is the
realised creation flow), the ratio corr(stage, P1 + Q3) / corr(P1, P1 + Q3) for:
  * perfect foresight of Q3;
  * the deposit's C1 forecast (lagged regressors only);
  * a same-day variant that adds the return to τ, which is NOT the deposit's C1 and is reported beside only.

SIMULATION: S_win = β × (P1 + Q3) + V_win × u_w, and S_plc = V_plc × u_p, where (u_w, u_p) are pre-sample window and
midday residuals (`ledger_power_stage_b.presample_noise`'s window column, drawn in 10-day blocks; the midday column
is an independent block draw of the same series), β ∈ {0 (the null), 0.03, 0.061 (D629's slope), 0.12}, 200 datasets
each.
  * Clause 1: the OOS partial correlation of C1 with S_win, net of [1, r to 14:28, flags], is ≥ 1.10 × A's.
  * The midday control (D631's lesson): C1's gain at the window must exceed its gain at midday.
Clause 2 (H2's t) is a price test and is not simulated.

    uv run python scripts/ledger_power_stage_c1.py [--check]
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
import ledger_fund_flows as FF  # noqa: E402
import ledger_power_stage_b as PB  # noqa: E402  (the pre-sample noise)

P = PB.P
OUT_JSON = REPO / "data" / "ledger_power_stage_c1.json"
TRAIN, TEST, BLOCK, SEED, REPS = 252, 63, 10, 20260928, 200
BETAS = (0.0, 0.03, 0.061, 0.12)
FLAGS = P.FLAGS["NG"]


def resid(y: np.ndarray, X: np.ndarray) -> np.ndarray:
    return y - X @ np.linalg.lstsq(X, y, rcond=None)[0]


def pcorr(a: np.ndarray, b: np.ndarray, X: np.ndarray) -> float:
    ra, rb = resid(a, X), resid(b, X)
    return float(ra @ rb / np.sqrt((ra @ ra) * (rb @ rb)))


def design() -> dict[str, Any]:
    f = pd.read_csv(P.FLOW, encoding="utf-8")
    f = f[f["root"] == "NG"]
    if (f["day"] >= P.CUT).any():
        raise RuntimeError("a flow row on or after the cut is in memory")
    star = f[f["is_tau_star"] == 1].set_index("day").sort_index()
    r28 = f[f["tau"] == "14:28"].set_index("day")["r_held"]
    rt = star["r_held"]
    days = list(star.index)
    cal = pd.read_csv(P.CAL, encoding="utf-8")
    cal = cal[cal["root"] == "NG"].set_index("date")
    fl, missing = FF.flows(days)
    ret = star["R_day"] - 1.0
    q3_true = np.zeros(len(days))
    q3_hat = np.zeros(len(days))
    q3_same = np.zeros(len(days))
    r2: dict[str, Any] = {}
    rows = np.arange(len(days))
    for fund, L in FF.FUNDS.items():
        X = FF.features(days, ret, fl[fund]).to_numpy()
        y = fl[fund].to_numpy()
        hat, _rv, _paths = FF.walk_forward_forecast(X, y, rows, TRAIN, TEST)
        Xs = np.column_stack([X, rt.to_numpy()])
        hs, _rvs, _ps = FF.walk_forward_forecast(Xs, y, rows, TRAIN, TEST)
        conv = L / (FF.MULT * star["p_held"].to_numpy())
        q3_true += y * conv
        q3_hat += np.nan_to_num(hat) * conv
        q3_same += np.nan_to_num(hs) * conv
        m = np.isfinite(hat)
        r2[fund] = {"oos_r2_c1": float(1 - np.sum((y[m] - hat[m]) ** 2) / np.sum((y[m] - y[m].mean()) ** 2)),
                    "oos_r2_same_day_variant": float(1 - np.sum((y[m] - hs[m]) ** 2) / np.sum((y[m] - y[m].mean()) ** 2)),
                    "days_without_nav": missing[fund]}
    oos = np.zeros(len(days), dtype=bool)
    oos[TRAIN:] = True
    ctrl = np.column_stack([np.ones(len(days)), r28.reindex(days).to_numpy()] +
                           [cal.loc[days, fl_].to_numpy(float) for fl_ in FLAGS])
    return {"days": days, "p1": star["q_est"].to_numpy(), "q3_true": q3_true, "q3_hat": q3_hat, "q3_same": q3_same,
            "oos": oos, "ctrl": ctrl, "r2": r2}


def volumes(days: list[str], held: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    """Trailing unsigned window and midday volumes over the held contracts (Databento, D627's panel)."""
    all_days = P.business_days("NG")
    pos = {d: i for i, d in enumerate(all_days)}
    v = pd.read_csv(P.PANEL, encoding="utf-8", usecols=["root", "kind", "day", "ym", "vol_win", "vol_plc"])
    v = v[(v["root"] == "NG") & (v["kind"] == "outright")]
    out = []
    for col in ("vol_win", "vol_plc"):
        piv = v.pivot_table(index="day", columns="ym", values=col, aggfunc="sum").reindex(all_days).fillna(0.0)
        out.append(np.array([P.abnormal(piv, all_days, pos[d], held[d].split(";"))[1] for d in days]))
    return out[0], out[1]


def build() -> dict[str, Any]:
    rng = np.random.default_rng(SEED)
    d = design()
    f = pd.read_csv(P.FLOW, encoding="utf-8")
    held = f[(f["root"] == "NG") & (f["is_tau_star"] == 1)].set_index("day")["held"]
    vw, vp = volumes(d["days"], held)
    U = PB.presample_noise()[:, 1]
    p1, q3, q3h, oos, C = d["p1"], d["q3_true"], d["q3_hat"], d["oos"], d["ctrl"]
    net = p1 + q3
    a = np.corrcoef(p1[oos], net[oos])[0, 1]
    ceilings = {"perfect_foresight": float(1 / a),
                "deposit_c1": float(np.corrcoef((p1 + q3h)[oos], net[oos])[0, 1] / a),
                "same_day_variant_not_c1": float(np.corrcoef((p1 + d["q3_same"])[oos], net[oos])[0, 1] / a),
                "sd_p1": float(p1[oos].std()), "sd_q3": float(q3[oos].std()), "sd_q3_hat": float(q3h[oos].std()),
                "corr_p1_q3": float(np.corrcoef(p1[oos], q3[oos])[0, 1])}
    n = len(p1)

    def draw() -> np.ndarray:
        idx = np.empty(n, dtype=int)
        i = 0
        while i < n:
            s = int(rng.integers(0, len(U) - BLOCK))
            k = min(BLOCK, n - i)
            idx[i:i + k] = np.arange(s, s + k)
            i += k
        return U[idx]

    sims = {}
    Co = C[oos]
    for beta in BETAS:
        ret, ratios, gains = [], [], []
        for _ in range(REPS):
            s = beta * net + vw * draw()
            sp = vp * draw()
            ra, rc = pcorr(p1[oos], s[oos], Co), pcorr((p1 + q3h)[oos], s[oos], Co)
            pa, pc = pcorr(p1[oos], sp[oos], Co), pcorr((p1 + q3h)[oos], sp[oos], Co)
            clause = ra > 0 and rc >= 1.10 * ra
            beats_midday = (rc - ra) > (pc - pa)
            ret.append(bool(clause and beats_midday))
            ratios.append(rc / ra if ra else np.nan)
            gains.append((rc - ra) - (pc - pa))
        sims[f"{beta:g}"] = {"reps": REPS, "clause1_and_midday": float(np.mean(ret)),
                             "ratio_median": float(np.nanmedian(ratios)),
                             "excess_gain_over_midday_median": float(np.median(gains))}
    return {"seed": SEED, "betas": BETAS, "n_days": n, "n_oos": int(oos.sum()), "forecast_r2": d["r2"],
            "ceilings": ceilings, "sims": sims}


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
    print(json.dumps({k: out[k] for k in ("n_days", "n_oos", "forecast_r2", "ceilings")}, indent=1))
    for k, v in out["sims"].items():
        print("beta", k, v)
    return 0


if __name__ == "__main__":
    sys.exit(main())
