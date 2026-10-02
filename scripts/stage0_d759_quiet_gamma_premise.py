"""D759 Stage 0: the premise check for quiet long-gamma days (prop book), as pre-registered in
docs/decisions/D759-STAGE-0-PRE-REG-quiet-long-gamma-premise.md (1c2de7e3).

    uv run --no-sync python scripts/stage0_d759_quiet_gamma_premise.py --selftest
    uv run --no-sync python scripts/stage0_d759_quiet_gamma_premise.py --run     # once; writes data/stage0_d759_quiet_gamma_premise.json

D757's G, I and D756's RD, costs and fade, read-only. Computes ONLY the 10:30 fade's prize and p* on non-impulse days
(pooled ES, YM, RTY; NQ reported) and compares the seen precision q = P(RD | G and not I). It never computes the fade's
net on G-and-not-I days, nor (a deliberate omission from the pre-registration's report list, disclosed in the result)
p* split by gamma state, since with q that would reveal the selected days' net.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d756_reverting_days as V  # noqa: E402
import stage0_d757_gamma_impulse as W  # noqa: E402

SPEC = REPO / "docs" / "decisions" / "D759-STAGE-0-PRE-REG-quiet-long-gamma-premise.md"
OUT = REPO / "data" / "stage0_d759_quiet_gamma_premise.json"
D757_OUT = REPO / "data" / "stage0_d757_gamma_impulse.json"
DECIDE = ("ES", "YM", "RTY")
T_MIN, PRIZE_K = 2.0, 3.0


class D759Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D759Error(msg)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def pstar(mu1: float, mu0: float):
    return (-mu0 / (mu1 - mu0)) if (mu1 > 0 > mu0) else (0.0 if mu0 >= 0 else None)


def reading(Z: bool, q: float, se: float, ps) -> str:
    if not Z or ps is None:
        return "NO PRIZE"
    if q < ps:
        return "NO ROOM"
    if q < ps + 2 * se:
        return "THIN"
    return "ROOM"


def run() -> int:
    need(not OUT.exists(), f"{OUT.name} exists: run-once")
    t0 = time.time()
    import stage0_d727_trend_curve as T7
    costs = json.loads(V.COSTS.read_text(encoding="utf-8"))["roots"]
    d757 = json.loads(D757_OUT.read_text(encoding="utf-8"))
    RD, I, G, NET = {}, {}, {}, {}
    for r in V.ROOTS:
        P = V.load_root_panel(T7, r)
        pn = T7.load_root(r, V.DATA)
        ob = T7.objects(pn)
        need(max(P["days"]) < V.SEAL, f"the seal: {r}")
        RD[r] = V.rd_label(P["E"], P["days"])
        z = ob["z"][:, W.J1030]
        I[r] = np.isfinite(z) & (np.abs(z) >= W.Z_IMP)
        G[r] = W.gamma_cells(V.gex_prior(P["days"]))
        ce = costs[r]["micro"]
        cost = float(ce["commission_rt_usd"]["value"] + ce["crossing_ticks_rt"][ce["default_line"]]["value"] * ce["tick_usd"])
        NET[r] = V.fade(P["O"], ob["Pt"][:, W.J1030], P["C"], float(ce["usd_per_point"]), cost)[1]
        NET[r + "_cost"] = cost
    # the known answer: D757's G and not-I cells, and its impulse-day p*
    for r in V.ROOTS:
        m = (G[r] == 1) & ~I[r]
        want = d757["cells"][r]["G_and_notI"]
        need(int(m.sum()) == want["n"] and math.isclose(float(RD[r][m].mean()), want["rd_rate"], rel_tol=1e-12),
             f"known answer: {r} G and not-I {int(m.sum())} / {RD[r][m].mean()}")
    a = np.concatenate([NET[r][I[r] & RD[r]] for r in DECIDE])
    b = np.concatenate([NET[r][I[r] & ~RD[r]] for r in DECIDE])
    ps_imp = pstar(V.stats(a)["mean"], V.stats(b)["mean"])
    need(math.isclose(ps_imp, d757["p_star"], rel_tol=1e-12), f"known answer: impulse p* {ps_imp} vs {d757['p_star']}")
    # the prize on non-impulse days (ALL gamma states)
    def prize(roots):
        nr = np.concatenate([NET[r][~I[r] & RD[r]] for r in roots])
        nn = np.concatenate([NET[r][~I[r] & ~RD[r]] for r in roots])
        c_rd = np.concatenate([np.full(int((~I[r] & RD[r]).sum()), NET[r + "_cost"]) for r in roots])
        s1, s0 = V.stats(nr), V.stats(nn)
        Z = bool(s1["mean"] > 0 and s1["t"] >= T_MIN and s1["mean_abs"] >= PRIZE_K * float(c_rd.mean()))
        return dict(RD=s1, other=s0, Z=Z, p_star=pstar(s1["mean"], s0["mean"]), mean_cost_on_RD=float(c_rd.mean()))
    pr = prize(DECIDE)
    n1 = sum(int(((G[r] == 1) & ~I[r]).sum()) for r in DECIDE)
    k1 = sum(int(RD[r][(G[r] == 1) & ~I[r]].sum()) for r in DECIDE)
    q = k1 / n1
    se = math.sqrt(q * (1 - q) / n1)
    rd = reading(pr["Z"], q, se, pr["p_star"])
    per_root = {}
    for r in V.ROOTS:
        m = (G[r] == 1) & ~I[r]
        p_r = prize((r,))
        per_root[r] = dict(prize=p_r, q=float(RD[r][m].mean()), n=int(m.sum()),
                           reading=reading(p_r["Z"], float(RD[r][m].mean()),
                                           math.sqrt(RD[r][m].mean() * (1 - RD[r][m].mean()) / m.sum()), p_r["p_star"]))
    res = {"record": "D759 (1c2de7e3)", "reading": rd, "q_seen_post_hoc": q, "q_se": se, "n_G_and_notI": n1,
           "prize_non_impulse": pr, "per_root": per_root, "known_answer_impulse_p_star": ps_imp,
           "omitted": "p* split by gamma state (listed as reported in the pre-registration): with q it reveals the net "
                      "on G-and-not-I days, the held slice's test. Not computed.",
           "runner_sha256": sha(Path(__file__).resolve()), "prereg_sha256": sha(SPEC), "wall_s": round(time.time() - t0, 1)}
    with open(OUT, "x", encoding="utf-8", newline="\n") as fh:
        json.dump(V._strip(res), fh, indent=1)
        fh.write("\n")
    print(f"[D759] {rd}: q {q:.4f} (SE {se:.4f}, n {n1}); p* {pr['p_star']}; Z {pr['Z']}")
    print(f"  prize on non-impulse days: RD {pr['RD']}  other {pr['other']}")
    for r, x in per_root.items():
        print(f"  {r}: q {x['q']:.4f} (n {x['n']}); p* {x['prize']['p_star']}; RD mean {x['prize']['RD']['mean']:.2f}, "
              f"other {x['prize']['other']['mean']:.2f} -> {x['reading']}")
    print(f"[D759] wall {res['wall_s']} s")
    return 0


def selftest() -> int:
    fails = []
    if pstar(30.0, -20.0) != 0.4:
        fails.append("pstar")
    if reading(True, 0.39, 0.013, 0.40) != "NO ROOM" or reading(True, 0.41, 0.013, 0.40) != "THIN" \
            or reading(True, 0.45, 0.013, 0.40) != "ROOM" or reading(False, 0.9, 0.01, 0.1) != "NO PRIZE":
        fails.append("reading")
    try:
        need(False, "x")
        fails.append("need() did not raise")
    except D759Error:
        pass
    for f in fails:
        print(f"[SELFTEST FAIL] {f}")
    print(f"[D759] selftest: {'FAIL' if fails else 'all passed'}")
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
