"""D711 addendum 2 (post hoc, the principal: "Ok last one I would like to see the Descision times of NQ and ES side by
side, and a per time corrlation?"). Descriptive only, in-sample to 2023-12-29; nothing gates, nothing is fitted.

F2's rule (D707 s.1 with the clock replaced, D711 s.1) at 10:30 / 11:30 / 12:30 / 13:30 / 14:30 / 15:30, each held 30
minutes, on ES (1 MES, $4.42) and NQ (1 MNQ, $4.07), on one common window. Per clock and root: the book (net, t, z in the
clock's take-everything sd, median, the 10 % trim, the lift over take-everything). Per clock, ES against NQ: rho of the
unfiltered gross on common candidate sessions, rho of the filtered daily net, rho of gross on the days both take, the
overlap counts and direction agreement, and each root's net on the days both take.

    uv run python scripts/diag_d711_nq_es_clocks.py --run
Writes data/diag_d711_nq_es_clocks.json.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import diag_d711_trims_and_overlap as T0  # noqa: E402
import stage1_d711_f2_mechanism as M  # noqa: E402

D = M.D
OUT = REPO / "data" / "diag_d711_nq_es_clocks.json"
CLOCKS = M.PLACEBO + (M.SHOULDER, M.ANCHOR)
ROOTS = ("ES", "NQ")


def book(X: pd.DataFrame, F: dict[str, np.ndarray], lo: str) -> dict[str, Any]:
    sess = X.index.to_numpy(str)
    span = F["window"] & (sess >= lo)
    g = X["gross"].to_numpy(float)
    c = X.attrs["cost"]
    s_T = float(g[span].std(ddof=1))
    take = F["take"] & span
    net = g[take] - c
    k = T0.trim_idx(net, 0.10)
    return {"trades": int(take.sum()), "mean_net": float(net.mean()), "t_net_hac": D.nw_t(net)[0],
            "mean_gross": float(g[take].mean()), "t_gross_hac": D.nw_t(g[take])[0],
            "mean_z": float((g[take] / s_T).mean()), "median_net": float(np.median(net)), "hit": float((net > 0).mean()),
            "trim10_net": float(net[k].mean()), "trim10_t": D.nw_t(net[k])[0],
            "take_everything_z": float((g[span] / s_T).mean()), "lift_z": float((g[take] / s_T).mean() - (g[span] / s_T).mean()),
            "share_2022_of_net": T0.M.year_share(net, sess[take]), "s_T_usd": s_T}


def pair(Xe: pd.DataFrame, Fe: dict[str, np.ndarray], Xn: pd.DataFrame, Fn: dict[str, np.ndarray], lo: str) -> dict[str, Any]:
    e = pd.DataFrame({"take": Fe["take"] & Fe["window"], "win": Fe["window"], "side": Xe["side"].to_numpy(float),
                      "g": Xe["gross"].to_numpy(float)}, index=Xe.index)
    n = pd.DataFrame({"take": Fn["take"] & Fn["window"], "win": Fn["window"], "side": Xn["side"].to_numpy(float),
                      "g": Xn["gross"].to_numpy(float)}, index=Xn.index)
    cand = e.index.intersection(n.index)
    cand = cand[cand >= lo]
    e, n = e.loc[cand], n.loc[cand]
    w = e["win"].to_numpy(bool) & n["win"].to_numpy(bool)
    e, n = e[w], n[w]
    et, nt = e["take"].to_numpy(bool), n["take"].to_numpy(bool)
    both = et & nt
    same = e["side"].to_numpy() == n["side"].to_numpy()
    ce, cn = Xe.attrs["cost"], Xn.attrs["cost"]
    de = np.where(et, e["g"].to_numpy() - ce, 0.0)
    dn = np.where(nt, n["g"].to_numpy() - cn, 0.0)
    return {"common_candidate_sessions": int(len(e)),
            "rho_gross_unfiltered": float(np.corrcoef(e["g"], n["g"])[0, 1]),
            "same_direction_unfiltered": float(same.mean()),
            "rho_filtered_daily_net": float(np.corrcoef(de, dn)[0, 1]),
            "rho_gross_when_both_take": float(np.corrcoef(e["g"].to_numpy()[both], n["g"].to_numpy()[both])[0, 1]) if both.sum() > 5 else None,
            "counts": {"both": int(both.sum()), "ES_only": int((et & ~nt).sum()), "NQ_only": int((~et & nt).sum())},
            "jaccard": float(both.sum() / (et | nt).sum()),
            "same_direction_when_both_take": float(same[both].mean()) if both.any() else None,
            "both_take_net": {"ES": float((e["g"].to_numpy()[both] - ce).mean()), "NQ": float((n["g"].to_numpy()[both] - cn).mean())},
            "one_root_only_net": {"ES_only": float((e["g"].to_numpy()[et & ~nt] - ce).mean()) if (et & ~nt).any() else None,
                                  "NQ_only": float((n["g"].to_numpy()[~et & nt] - cn).mean()) if (~et & nt).any() else None},
            "share_of_net_on_both_days": {"ES": float(de[both].sum() / de.sum()) if de.sum() > 0 else None,
                                          "NQ": float(dn[both].sum() / dn.sum()) if dn.sum() > 0 else None}}


def run() -> dict[str, Any]:
    t0 = time.time()
    L = {r: M.load_root(r) for r in ROOTS}
    X = {(r, T): M.clock_frame(L[r], T) for r in ROOTS for T in CLOCKS}
    F = {k: M.f2_on(v) for k, v in X.items()}
    M.es_known_answer(X[("ES", M.ANCHOR)])
    for k, v in X.items():
        M.V.audit_tiers(v, F[k])
    lo = max(str(v.index.to_numpy(str)[F[k]["window"]][0]) for k, v in X.items())
    j = json.loads(T0.D711_JSON.read_text(encoding="utf-8"))
    if lo != j["A1"]["common_start"]:
        print(f"note: the common window starts {lo} (D711 A1's ES-only window started {j['A1']['common_start']})")
    out = {"spec": "D711 addendum 2, post hoc and descriptive (the principal's request, 2026-09-30)", "common_start": lo,
           "clocks": {}}
    for T in CLOCKS:
        out["clocks"][T] = {r: book(X[(r, T)], F[(r, T)], lo) for r in ROOTS}
        out["clocks"][T]["ES_vs_NQ"] = pair(X[("ES", T)], F[("ES", T)], X[("NQ", T)], F[("NQ", T)], lo)
    out["runtime_min"] = round((time.time() - t0) / 60, 2)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if not a.run:
        ap.print_help()
        return 1
    out = run()
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    for T, c in out["clocks"].items():
        es, nq, p = c["ES"], c["NQ"], c["ES_vs_NQ"]
        print(T, f"ES n{es['trades']} net {es['mean_net']:+.2f} t{es['t_net_hac']:.2f} z{es['mean_z']:.3f} tr10 {es['trim10_net']:+.2f} |",
              f"NQ n{nq['trades']} net {nq['mean_net']:+.2f} t{nq['t_net_hac']:.2f} z{nq['mean_z']:.3f} tr10 {nq['trim10_net']:+.2f} |",
              f"rho unf {p['rho_gross_unfiltered']:.2f} daily {p['rho_filtered_daily_net']:.2f} both {p['rho_gross_when_both_take']:.2f} jac {p['jaccard']:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
