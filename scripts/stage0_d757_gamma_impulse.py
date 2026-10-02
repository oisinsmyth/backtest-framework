"""D757 Stage 0: strong long gamma AND a 10:30 impulse as a reverting-day detector (prop book), as pre-registered in
docs/decisions/D757-STAGE-0-PRE-REG-gamma-and-impulse-reverting-days.md (fb58ae7f).

    uv run --no-sync python scripts/stage0_d757_gamma_impulse.py --selftest
    uv run --no-sync python scripts/stage0_d757_gamma_impulse.py --run       # once; writes data/stage0_d757_gamma_impulse.json

D756's panels, label (RD) and costs, read-only. G = GEX at the prior close in its walk-forward top tercile;
I = |z at 10:30| >= 1.5 (D727's z, clock index 1). The 10:30 fade's prize and p* on impulse days; T1 (one-sided exact
rotation of G against the label, impulse fixed), T2 precision >= p*, T3 >= 150 detector days; pooled over ES, YM, RTY,
NQ reported only. In-sample (<= 2023-12-29); development, not admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d756_reverting_days as V  # noqa: E402  (read-only)

SPEC = REPO / "docs" / "decisions" / "D757-STAGE-0-PRE-REG-gamma-and-impulse-reverting-days.md"
OUT = REPO / "data" / "stage0_d757_gamma_impulse.json"
D756_OUT = REPO / "data" / "stage0_d756_reverting_days.json"
DECIDE = ("ES", "YM", "RTY")
J1030, Z_IMP, MIN_N = 1, 1.5, 150
ALPHA, T_MIN, PRIZE_K = 0.05, 2.0, 3.0


class D757Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D757Error(msg)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def gamma_cells(gex: np.ndarray) -> np.ndarray:
    """1 = G (top walk-forward tercile), 0 = not G, -1 = unknown."""
    c = V.wf_tercile(gex)
    return np.where(c < 0, -1, (c == 2).astype(int))


def prec_pair(G: dict, I: dict, RD: dict, roots, shift: int = 0) -> tuple[float, float, int, int]:
    """Pooled P(RD | G & I) and P(RD | notG & I), G rotated by shift mod each root's length."""
    a1 = n1 = a0 = n0 = 0
    for r in roots:
        g = np.roll(G[r], shift % G[r].size)
        m1, m0 = I[r] & (g == 1), I[r] & (g == 0)
        a1 += int(RD[r][m1].sum()); n1 += int(m1.sum()); a0 += int(RD[r][m0].sum()); n0 += int(m0.sum())
    return (a1 / n1 if n1 else float("nan")), (a0 / n0 if n0 else float("nan")), n1, n0


def prec_pair_loop(G, I, RD, roots, shift):
    a1 = n1 = a0 = n0 = 0
    for r in roots:
        n = G[r].size
        for i in range(n):
            gi = G[r][(i - shift) % n]
            if not I[r][i]:
                continue
            if gi == 1:
                n1 += 1; a1 += int(RD[r][i])
            elif gi == 0:
                n0 += 1; a0 += int(RD[r][i])
    return a1 / n1 - a0 / n0


def rotation(G, I, RD, roots) -> dict:
    K = max(G[r].size for r in roots)
    p1, p0, n1, n0 = prec_pair(G, I, RD, roots)
    obs = p1 - p0
    vals = np.empty(K)
    for k in range(K):
        a, b, _, _ = prec_pair(G, I, RD, roots, k)
        vals[k] = a - b
    need(vals[0] == obs, "rotation: offset 0 is not the observed")
    fin = vals[np.isfinite(vals)]
    return {"precision_G_and_I": p1, "precision_notG_and_I": p0, "n_G_and_I": n1, "n_notG_and_I": n0, "diff": obs,
            "offsets": int(K), "p_high": float(np.mean(fin >= obs)), "null_p50": float(np.percentile(fin, 50)),
            "null_p95": float(np.percentile(fin, 95)), "_vals": vals}


def cell_report(G, I, RD, r) -> dict:
    out = {}
    for name, m in {"G_and_I": (G[r] == 1) & I[r], "I": I[r], "G": G[r] == 1, "notG_and_I": (G[r] == 0) & I[r],
                    "G_and_notI": (G[r] == 1) & ~I[r], "all": np.ones(I[r].size, bool)}.items():
        out[name] = {"n": int(m.sum()), "share": float(m.mean()), "rd_rate": float(RD[r][m].mean()) if m.any() else None}
    return out


def run() -> int:
    need(not OUT.exists(), f"{OUT.name} exists: run-once")
    t0 = time.time()
    import stage0_d727_trend_curve as T7
    costs = json.loads(V.COSTS.read_text(encoding="utf-8"))["roots"]
    d756 = json.loads(D756_OUT.read_text(encoding="utf-8"))
    PN, RD, I, G, GEXV, UNIT, NET10, NET1030 = {}, {}, {}, {}, {}, {}, {}, {}
    for r in V.ROOTS:
        P = V.load_root_panel(T7, r)
        pn = T7.load_root(r, V.DATA)
        ob = T7.objects(pn)
        need(np.array_equal(np.asarray(pn["days"], str), P["days"]), f"{r}: panel days differ between loads")
        need(max(P["days"]) < V.SEAL, f"the seal: {r}")
        PN[r] = dict(P, P1030=ob["Pt"][:, J1030], z1030=ob["z"][:, J1030])
        need(T7.CLOCKS[J1030] == 60, "clock index 1 is not 10:30")
        RD[r] = V.rd_label(P["E"], P["days"])
        I[r] = np.isfinite(PN[r]["z1030"]) & (np.abs(PN[r]["z1030"]) >= Z_IMP)
        GEXV[r] = V.gex_prior(P["days"])
        G[r] = gamma_cells(GEXV[r])
        ce = costs[r]["micro"]
        UNIT[r] = dict(upp=float(ce["usd_per_point"]), cost=float(ce["commission_rt_usd"]["value"]
                       + ce["crossing_ticks_rt"][ce["default_line"]]["value"] * ce["tick_usd"]))
        NET10[r] = V.fade(P["O"], P["P10"], P["C"], UNIT[r]["upp"], UNIT[r]["cost"])[1]
        NET1030[r] = V.fade(P["O"], PN[r]["P1030"], P["C"], UNIT[r]["upp"], UNIT[r]["cost"])[1]
    # the known answer: D756's label and prize
    rd_n = sum(int(RD[r].sum()) for r in V.ROOTS)
    rd_mean = float(np.nanmean(np.concatenate([NET10[r][RD[r]] for r in V.ROOTS])))
    need(rd_n == d756["prize"]["RD_days"]["n"] and math.isclose(rd_mean, d756["prize"]["RD_days"]["mean"], rel_tol=1e-9),
         f"known answer: RD {rd_n} mean {rd_mean}")
    # the lag canary: day t's own GEX must differ from the prior-close value somewhere
    import pandas as pd
    g = pd.read_csv(V.DIX, usecols=["date", "gex"], dtype={"date": str}, encoding="utf-8")
    g = g[g["date"] < V.SEAL].set_index("date")["gex"]
    same_day = g.reindex(PN["ES"]["days"]).to_numpy(float)
    both = np.isfinite(same_day) & np.isfinite(GEXV["ES"])
    need(both.any() and np.any(same_day[both] != GEXV["ES"][both]), "the GEX lag canary (day t's own value) never differed")
    # the prize on impulse days (ES, YM, RTY)
    net_rd = np.concatenate([NET1030[r][I[r] & RD[r]] for r in DECIDE])
    net_no = np.concatenate([NET1030[r][I[r] & ~RD[r]] for r in DECIDE])
    cost_rd = np.concatenate([np.full(int((I[r] & RD[r]).sum()), UNIT[r]["cost"]) for r in DECIDE])
    s_rd, s_no = V.stats(net_rd), V.stats(net_no)
    Z = bool(s_rd.get("mean", -1) > 0 and s_rd.get("t", 0) >= T_MIN and s_rd["mean_abs"] >= PRIZE_K * float(cost_rd.mean()))
    mu1, mu0 = s_rd["mean"], s_no["mean"]
    pstar = (-mu0 / (mu1 - mu0)) if (mu1 > 0 > mu0) else (0.0 if mu0 >= 0 else None)
    # T1-T3
    rot = rotation(G, I, RD, DECIDE)
    ks = list(range(0, rot["offsets"], max(1, rot["offsets"] // 50)))[:50]
    for k in ks:
        need(math.isclose(prec_pair_loop(G, I, RD, DECIDE, k), rot["_vals"][k], rel_tol=1e-12, abs_tol=1e-15),
             f"rotation vector != loop at {k}")
    T1 = rot["p_high"] <= ALPHA and rot["diff"] > 0
    T2 = pstar is not None and rot["precision_G_and_I"] >= pstar
    T3 = rot["n_G_and_I"] >= MIN_N
    if not Z:
        reading = "NO PRIZE"
    elif T1 and T2 and T3:
        reading = "DETECTOR WORTH IT"
    elif T1:
        reading = "RECOGNISABLE, NOT WORTH IT"
    else:
        reading = "NOT A DETECTOR"
    res = {"record": "D757 (fb58ae7f)", "reading": reading, "Z_1030": Z, "p_star": pstar, "T1": T1, "T2": T2, "T3": T3,
           "prize_impulse_days": {"RD": s_rd, "other": s_no, "mean_cost_on_RD": float(cost_rd.mean())},
           "rotation": {k: v for k, v in rot.items() if not k.startswith("_")},
           "cells": {r: cell_report(G, I, RD, r) for r in V.ROOTS},
           "pooled_decide_cells": {name: {"n": sum(cell_report(G, I, RD, r)[name]["n"] for r in DECIDE)} for name in ("G_and_I", "I", "G")},
           "known_answer": {"rd_n": rd_n, "rd_fade_10_mean": rd_mean},
           "runner_sha256": sha(Path(__file__).resolve()), "prereg_sha256": sha(SPEC), "wall_s": round(time.time() - t0, 1)}
    with open(OUT, "x", encoding="utf-8", newline="\n") as fh:
        json.dump(V._strip(res), fh, indent=1)
        fh.write("\n")
    show(res)
    return 0


def show(res: dict) -> None:
    p, rot = res["prize_impulse_days"], res["rotation"]
    print(f"[D757] {res['reading']}  (Z {res['Z_1030']}, T1 {res['T1']}, T2 {res['T2']}, T3 {res['T3']})")
    print(f"  prize on impulse days: RD {p['RD']}  other {p['other']}  p* {res['p_star']}")
    print(f"  G&I precision {rot['precision_G_and_I']:.3f} (n {rot['n_G_and_I']}) vs notG&I {rot['precision_notG_and_I']:.3f} "
          f"(n {rot['n_notG_and_I']}); diff {rot['diff']:+.4f}, p_high {rot['p_high']:.4f}, null p50 {rot['null_p50']:+.4f} p95 {rot['null_p95']:+.4f}")
    for r, c in res["cells"].items():
        print(f"  {r}: " + "  ".join(f"{k} {v['n']}/{v['rd_rate'] if v['rd_rate'] is None else round(v['rd_rate'], 3)}" for k, v in c.items()))
    print(f"[D757] wall {res['wall_s']} s")


def selftest() -> int:
    fails = []
    rng = np.random.default_rng(7571)
    # gamma cells: top tercile of the past only
    x = rng.normal(size=600)
    c = gamma_cells(x)
    x2 = x.copy()
    x2[450:] += 50
    if not np.array_equal(c[:450], gamma_cells(x2)[:450]):
        fails.append("gamma_cells reads the future")
    # sign in money (D756's fade): a short after a rise pays when the close is below the entry
    _, n_, s = V.fade(np.array([100.0]), np.array([104.0]), np.array([101.0]), 2.0, 4.0)
    if not (s[0] == -1 and math.isclose(n_[0], 2.0)):
        fails.append("sign in money")
    # the rotation: a planted G equal to the label on impulse days; vector == loop
    RD = {"A": rng.random(800) < 1 / 3, "B": rng.random(600) < 1 / 3}
    I = {k: rng.random(v.size) < 0.4 for k, v in RD.items()}
    Gp = {k: np.where(RD[k], 1, 0) for k in RD}
    r = rotation(Gp, I, RD, ("A", "B"))
    if not r["p_high"] < 0.01:
        fails.append(f"planted G p {r['p_high']}")
    Gn = {k: rng.integers(-1, 2, v.size) for k, v in RD.items()}
    for k in range(0, 800, 41):
        a, b, _, _ = prec_pair(Gn, I, RD, ("A", "B"), k)
        if not math.isclose(a - b, prec_pair_loop(Gn, I, RD, ("A", "B"), k), rel_tol=1e-12, abs_tol=1e-15):
            fails.append("rotation vector != loop")
            break
    try:
        need(False, "x")
        fails.append("need() did not raise")
    except D757Error:
        pass
    for f in fails:
        print(f"[SELFTEST FAIL] {f}")
    print(f"[D757] selftest: {'FAIL' if fails else 'all passed'}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args()
    return selftest() if a.selftest else run()


if __name__ == "__main__":
    sys.exit(main())
