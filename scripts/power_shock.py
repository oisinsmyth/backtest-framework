"""Shock classifier POWER, before Gate 1 (SHOCK_CLASSIFIER_PREREG.md s.7A; D641). The principal, 2026-09-28: "Yes, run
the power study".

    python scripts/power_shock.py        # SYSTEM interpreter (pyarrow) -> data/shock/power.json + docs/results/SHOCK_CLASSIFIER_POWER.md

WHAT IT READS (and nothing else):
- the classes, counts and days of D641's shocks (z = 4, primary thresholds);
- the DISPERSION of the 30-minute move after each shock: from the close of bar t0+1 (the primary fill) to 30 minutes
  later (H1's exit), RAW, never multiplied by the shock direction or the class's trade direction. Only its standard
  deviation and its within-day correlation are computed. Its mean is never computed, so nothing about whether a class
  continues or reverts is read.

WHAT IT GIVES, per instrument (H1: the difference between INFO's and LIQ's returns in the shock direction):
- n per class;
- the day-cluster design effect 1 + (m - 1) rho, where m is the class's mean shocks per shock-day and rho the
  within-day correlation of the raw moves;
- n_eff, and SE_diff = sigma x sqrt(1/n_eff_INFO + 1/n_eff_LIQ);
- MDE at t = 2 (s.7A) and at Holm's first step across the four instruments with 80% power (z 2.498 + 0.842,
  two-sided 0.05/4), in sigma units and in bp;
- the plausible effect: the round-trip cost at micro size, D508's default crossing plus $3 commission, plus the
  deposit's one tick of adverse entry slippage (s.5.1), in bp of the fill.
A difference is a gross effect in both directions (INFO continues AND LIQ reverts), so the cost is the natural floor
the divergence has to clear to matter. A cell whose MDE exceeds it is UNDERPOWERED: s.7A says it is reported as
inconclusive, not failed.
"""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
SH = REPO / "data" / "shock"
OUT_MD = REPO / "docs" / "results" / "SHOCK_CLASSIFIER_POWER.md"
_s = importlib.util.spec_from_file_location("build_shock_phase2", REPO / "scripts" / "build_shock_phase2.py")
assert _s is not None and _s.loader is not None
P2 = importlib.util.module_from_spec(_s)
sys.modules["build_shock_phase2"] = P2
_s.loader.exec_module(P2)
# s.5.1 primary fill cost: D508's default crossing + $3 commission, plus one tick of adverse slippage (MNQ/MES/MCL/MGC)
COST = {r: (3.0 + x * t + t) / u for r, (x, t, u) in {"NQ": (2.1342, 0.5, 2.0), "ES": (1.1345, 1.25, 5.0),
                                                      "CL": (2.0312, 1.0, 100.0), "GC": (2.9335, 1.0, 10.0)}.items()}
HOLD = 30
Z_T2, Z_HOLM, Z_80 = 2.0, 2.498, 0.8416


def within_day_rho(df: pd.DataFrame) -> float:
    """The intraclass correlation of the raw moves within shock-days: pairwise products of standardised moves over
    days with at least two shocks, averaged over pairs."""
    z = (df["move_bp"] - df["move_bp"].mean()) / df["move_bp"].std(ddof=1)
    num = den = 0.0
    for _d, g in df.assign(z=z).groupby("day"):
        v = g["z"].to_numpy(float)
        if len(v) > 1:
            s = v.sum()
            num += (s * s - (v * v).sum()) / 2
            den += len(v) * (len(v) - 1) / 2
    return float(num / den) if den else 0.0


def main() -> int:
    sh = pd.read_csv(SH / "phase2_shocks.csv.gz", encoding="utf-8", dtype={"day": str})
    sh = sh[(sh["z"] == 4.0) & sh["class_primary"].isin(["INFO", "LIQ"])].copy()
    if (sh["day"] >= P2.RESERVED_FROM).any():
        raise RuntimeError("a sealed shock reached POWER")
    days = P2.usable_sessions()
    G = P2.grids(sorted(P2.PEERS), days)
    pos = {m: i for i, m in enumerate(P2.MINUTES)}
    mv = []
    for r in sh.itertuples():
        row = G[r.root].loc[r.day].to_numpy(float)
        i = pos[r.bar]
        fill_i, exit_i = i + 1, i + 1 + HOLD
        if exit_i >= len(row) or not (np.isfinite(row[fill_i]) and np.isfinite(row[exit_i])):
            mv.append((np.nan, np.nan))
            continue
        mv.append(((row[exit_i] / row[fill_i] - 1) * 1e4, COST[r.root] / row[fill_i] * 1e4))
    sh["move_bp"], sh["cost_bp"] = [m[0] for m in mv], [m[1] for m in mv]  # RAW: never signed here
    sh = sh.dropna(subset=["move_bp"])
    res: dict = {"spec": "s.7A; D641", "hold_min": HOLD, "cost_points": COST, "instruments": {}}
    for root in ("NQ", "ES", "CL", "GC"):
        g = sh[sh["root"] == root]
        sig = float(g["move_bp"].std(ddof=1))
        cls = {}
        for c in ("INFO", "LIQ"):
            x = g[g["class_primary"] == c]
            n = len(x)
            m = float(x.groupby("day").size().mean()) if n else 0.0
            rho = within_day_rho(x) if n > 2 else 0.0
            deff = max(1 + (m - 1) * rho, 1e-9)
            cls[c] = {"n": int(n), "shock_days": int(x["day"].nunique()), "mean_per_day": m, "rho_within_day": rho,
                      "design_effect": deff, "n_eff": min(n / deff, float(n)), "n_2024_plus": int((x["day"] >= "2024-01-01").sum())}
        ne_i, ne_l = cls["INFO"]["n_eff"], cls["LIQ"]["n_eff"]
        se_sig = math.sqrt(1 / ne_i + 1 / ne_l) if ne_i and ne_l else float("inf")
        cost = float(g["cost_bp"].mean())
        res["instruments"][root] = {
            **{f"{c}_{k}": v for c, d in cls.items() for k, v in d.items()},
            "sigma_move_bp": sig, "se_diff_sigma": se_sig, "se_diff_bp": se_sig * sig,
            "mde_t2_bp": Z_T2 * se_sig * sig, "mde_t2_sigma": Z_T2 * se_sig,
            "mde_holm80_bp": (Z_HOLM + Z_80) * se_sig * sig, "mean_cost_bp": cost,
            "underpowered_t2": bool(Z_T2 * se_sig * sig > cost),
            "underpowered_holm80": bool((Z_HOLM + Z_80) * se_sig * sig > cost),
            "deposit_plan": {"n_info": 600, "n_liq": 450, "se_sigma": 0.06, "mde_sigma": 0.12}}
    # pooled, as s.7A's first row
    ni = sum(v["INFO_n_eff"] for v in res["instruments"].values())
    nl = sum(v["LIQ_n_eff"] for v in res["instruments"].values())
    res["pooled"] = {"n_eff_info": ni, "n_eff_liq": nl, "se_diff_sigma": math.sqrt(1 / ni + 1 / nl),
                     "mde_t2_sigma": 2 * math.sqrt(1 / ni + 1 / nl), "deposit_plan_mde_sigma": 0.06}
    (SH / "power.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8", newline="\n")
    L = ["# Shock classifier: the POWER step (s.7A), before Gate 1", "",
         "*Generated by `scripts/power_shock.py` on D641's shocks (z = 4, primary thresholds, 2016-01 → 2025-02). It reads "
         "the class counts, the day clustering and the unsigned dispersion of the 30-minute move after the t0+1 fill; never "
         "its mean or its sign against the shock or the class.*", "",
         "| instrument | INFO n (n_eff) | LIQ n (n_eff) | LIQ 2024+ | σ 30-min (bp) | SE diff (σ) | MDE t=2 (bp) | "
         "MDE Holm 80% (bp) | cost (bp) | verdict | deposit plan MDE (σ) |",
         "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|"]
    for r, v in res["instruments"].items():
        verdict = "UNDERPOWERED" if v["underpowered_t2"] else ("powered at t=2; not at Holm 80%" if v["underpowered_holm80"] else "powered")
        L.append(f"| {r} | {v['INFO_n']} ({v['INFO_n_eff']:.0f}) | {v['LIQ_n']} ({v['LIQ_n_eff']:.0f}) | {v['LIQ_n_2024_plus']} | "
                 f"{v['sigma_move_bp']:.1f} | {v['se_diff_sigma']:.3f} | {v['mde_t2_bp']:.2f} | {v['mde_holm80_bp']:.2f} | "
                 f"{v['mean_cost_bp']:.2f} | {verdict} | 0.12 |")
    p = res["pooled"]
    L += ["", f"Pooled (s.7A row 1): n_eff INFO {p['n_eff_info']:.0f}, LIQ {p['n_eff_liq']:.0f}; SE diff {p['se_diff_sigma']:.3f} σ; "
          f"MDE (t = 2) {p['mde_t2_sigma']:.3f} σ, against the plan's 0.06 σ.", ""]
    OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())
