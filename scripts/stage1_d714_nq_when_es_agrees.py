"""D714: an in-sample test -- NQ F2 taken only when ES F2 also takes, same direction -- against count-matched random
deletion of NQ F2 trades, on direction efficiency. Spec: docs/decisions/D714-PRE-REG-nq-f2-only-when-es-f2-agrees.md
(c1069fd5); the principal: "I would like one in sample test, to trade NQ- only when last construction agrees to trade
on both NQ and ES?"

    uv run python scripts/stage1_d714_nq_when_es_agrees.py --selftest
    uv run python scripts/stage1_d714_nq_when_es_agrees.py --run       # once

B = NQ F2 (D711 s.1 at 15:30, one MNQ, $4.07) from 2018-05-14 to 2023-12-29; A = B's trades on sessions where ES F2
(D707 s.1) takes with the same sign of F5. INCREMENT if E(A) = sum(net)/sum(|net|) beats the p95 of E over 20,000 random
|A|-subsets of B and mean net(A) > mean net(B); UNRESOLVED within 2 bootstrap SE of the p95. Found by looking (D711
addendum 1), so a pass is in-sample and post hoc. Writes data/stage1_d714_nq_when_es_agrees.json.
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

E, D = M.E, M.D
OUT = REPO / "data" / "stage1_d714_nq_when_es_agrees.json"
START, N_DRAW, SEED = "2018-05-14", 20000, 714
KNOWN_NQ = {"trades": 274, "mean_net": 20.67010517126089}
KNOWN_OVERLAP = {"both": 217, "ES_only": 33, "NQ_only": 52}


class D714Error(RuntimeError):
    pass


def efficiency(x: np.ndarray) -> float:
    s = float(np.abs(x).sum())
    return float(x.sum()) / s if s > 0 else float("nan")


def null(net_b: np.ndarray, n_a: int, n_draw: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Random |A|-subsets of B without replacement: their efficiency and mean net."""
    rng = np.random.default_rng(seed)
    ef, mu = np.empty(n_draw), np.empty(n_draw)
    for i in range(n_draw):
        k = rng.choice(len(net_b), n_a, replace=False)
        ef[i], mu[i] = efficiency(net_b[k]), float(net_b[k].mean())
    return ef, mu


def p95_se(x: np.ndarray, B: int = 1000, seed: int = 7140) -> float:
    rng = np.random.default_rng(seed)
    return float(np.std([np.quantile(x[rng.integers(0, len(x), len(x))], 0.95) for _ in range(B)], ddof=1))


def verdict(e_a: float, mean_a: float, mean_b: float, p95: float, se: float) -> str:
    if e_a > p95 and mean_a > mean_b:
        return "UNRESOLVED (within 2 SE of the p95)" if e_a - p95 < 2 * se else "INCREMENT"
    return "NO INCREMENT"


def books(g: np.ndarray, masks: dict[str, np.ndarray], sess: np.ndarray, side: np.ndarray, cost: float, years: float,
          arm: pd.Series, s_T: float) -> dict[str, Any]:
    out = {}
    with M.cost_as(cost):
        for nm, m in masks.items():
            bk = E.book(g, m, sess, side, years, arm)
            net = g[m] - cost
            bk["trims"] = T0.trims(net, g[m] / s_T)
            bk["efficiency"] = efficiency(net)
            bk["share_2022_of_net"] = M.year_share(net, sess[m])
            out[nm] = bk
    return out


def study() -> dict[str, Any]:
    t0 = time.time()
    E.sign_audit()
    Xe = M.clock_frame(M.load_root("ES"), M.ANCHOR)
    Fe = M.f2_on(Xe)
    ka_es = M.es_known_answer(Xe)
    Xn = M.clock_frame(M.load_root("NQ"), M.ANCHOR)
    Fn = M.f2_on(Xn)
    M.V.audit_tiers(Xe, Fe)
    M.V.audit_tiers(Xn, Fn)
    sn = Xn.index.to_numpy(str)
    gn = Xn["gross"].to_numpy(float)
    cn = Xn.attrs["cost"]
    own = Fn["take"] & Fn["window"]
    ka_nq = {"trades": int(own.sum()), "mean_net": float((gn[own] - cn).mean())}
    if ka_nq["trades"] != KNOWN_NQ["trades"] or abs(ka_nq["mean_net"] - KNOWN_NQ["mean_net"]) > 1e-9:
        raise D714Error(f"D711's NQ book is not reproduced: {ka_nq}")
    ov = T0.overlap(Xe, Fe, Xn, Fn)["counts"]
    if {k: ov[k] for k in KNOWN_OVERLAP} != KNOWN_OVERLAP:
        raise D714Error(f"D711 addendum 1's overlap counts are not reproduced: {ov}")
    # the agreement flag, per NQ session: ES F2 takes that session with the same sign
    es_take = pd.Series(Fe["take"] & Fe["window"], index=Xe.index)
    es_side = pd.Series(Xe["side"].to_numpy(float), index=Xe.index)
    agree = (es_take.reindex(Xn.index).fillna(False).to_numpy(bool)
             & (es_side.reindex(Xn.index).to_numpy() == Xn["side"].to_numpy(float)))
    Bm = own & (sn >= START)
    Am = Bm & agree
    net = gn - cn
    net_b, net_a = net[Bm], net[Am]
    # the null
    ef0, mu0 = null(net_b, len(net_b), 3, SEED)
    if not (np.allclose(ef0, efficiency(net_b), rtol=0, atol=1e-15) and np.allclose(mu0, net_b.mean(), rtol=0, atol=1e-12)):
        raise D714Error("a subset of size |B| does not reproduce B")
    ef, mu = null(net_b, len(net_a), N_DRAW, SEED)
    p95, se = float(np.quantile(ef, 0.95)), p95_se(ef)
    e_a, e_b = efficiency(net_a), efficiency(net_b)
    v = verdict(e_a, float(net_a.mean()), float(net_b.mean()), p95, se)
    # reporting
    wd = sn[Bm]
    years = (pd.Timestamp(str(wd[-1])) - pd.Timestamp(START)).days / 365.25
    arm = E.P694.arm_daily()
    arm = arm[arm.index <= M.IN_END]
    span = Fn["window"] & (sn >= START)
    s_T = float(gn[span].std(ddof=1))
    side = Xn["side"].to_numpy(float)
    bk = books(gn, {"A_agreement": Am, "B_nq_f2": Bm, "dropped_nq_only": Bm & ~agree}, sn, side, cn, years, arm, s_T)
    # ES's own agreement book, on the same days
    se_ = Xe.index.to_numpy(str)
    ge = Xe["gross"].to_numpy(float)
    nq_take = pd.Series(Am, index=Xn.index).reindex(Xe.index).fillna(False).to_numpy(bool)
    es_agree = (Fe["take"] & Fe["window"]) & nq_take & (se_ >= START)
    s_Te = float(ge[Fe["window"] & (se_ >= START)].std(ddof=1))
    bk_es = books(ge, {"ES_on_agreement_days": es_agree, "ES_F2": Fe["take"] & Fe["window"] & (se_ >= START)}, se_,
                  Xe["side"].to_numpy(float), M.ES_COST, years, arm, s_Te)
    # rho of A's daily net with ES F2's
    es_daily = pd.Series(np.where(Fe["take"] & Fe["window"], ge - M.ES_COST, 0.0), index=Xe.index)
    a_daily = pd.Series(np.where(Am, net, 0.0), index=Xn.index)
    common = a_daily.index.intersection(es_daily.index)
    common = common[common >= START]
    by_year = {}
    for y in sorted({s[:4] for s in wd}):
        a_y, b_y = net[Am & (np.char.startswith(sn, y))], net[Bm & (np.char.startswith(sn, y))]
        by_year[y] = {"A_n": int(len(a_y)), "A_net": float(a_y.mean()) if len(a_y) else None, "B_n": int(len(b_y)),
                      "B_net": float(b_y.mean()) if len(b_y) else None,
                      "increment": float(a_y.mean() - b_y.mean()) if len(a_y) and len(b_y) else None}
    out = {"spec": "D714 (c1069fd5)", "known_answers": {"es": ka_es["d707_frozen_reproduced"], "nq": ka_nq, "overlap": ov},
           "window": [START, str(wd[-1])], "B_trades": int(Bm.sum()), "A_trades": int(Am.sum()),
           "dropped": int((Bm & ~agree).sum()),
           "efficiency": {"A": e_a, "B": e_b, "dropped": efficiency(net[Bm & ~agree])},
           "mean_net": {"A": float(net_a.mean()), "B": float(net_b.mean()), "dropped": float(net[Bm & ~agree].mean())},
           "null_efficiency": {"draws": N_DRAW, "p50": float(np.median(ef)), "p95": p95, "p95_bootstrap_se": se,
                               "rank_of_A": float((ef < e_a).mean())},
           "null_mean_net_reported": {"p50": float(np.median(mu)), "p95": float(np.quantile(mu, 0.95)),
                                      "rank_of_A": float((mu < net_a.mean()).mean())},
           "verdict": v, "books": bk, "es_books": bk_es,
           "rho_A_daily_with_es_f2_daily": float(np.corrcoef(a_daily.loc[common], es_daily.loc[common])[0, 1]),
           "by_year": by_year, "runtime_min": round((time.time() - t0) / 60, 2)}
    out["predictions"] = {
        "1_no_increment_rank_0.80_to_0.94": bool(v == "NO INCREMENT" and 0.80 <= out["null_efficiency"]["rank_of_A"] <= 0.94),
        "2_A_beats_B_by_3_to_5": bool(3 <= out["mean_net"]["A"] - out["mean_net"]["B"] <= 5),
        "3_A_holds_at_10pct_trim": bool(bk["A_agreement"]["trims"]["trim_10pct_each_tail"]["mean_net"] > 0),
        "4_A_2022_share_above_B": bool((bk["A_agreement"]["share_2022_of_net"] or 0) > (bk["B_nq_f2"]["share_2022_of_net"] or 0))}
    return out


def selftest() -> int:
    rng = np.random.default_rng(1)
    hits, worlds = 0, 200
    for _ in range(worlds):
        x = rng.normal(8, 130, 270)
        lab = rng.random(270) < 0.8
        ef, _ = null(x, int(lab.sum()), 1000, int(rng.integers(1e9)))
        p95 = float(np.quantile(ef, 0.95))
        hits += int(efficiency(x[lab]) > p95 and x[lab].mean() > x.mean())
    rate = hits / worlds
    if rate > 0.09:
        raise SystemExit(f"selftest: a random label gave INCREMENT-shaped results in {rate:.3f} of worlds (about 0.05 expected)")
    x = rng.normal(8, 130, 270)
    lab = np.ones(270, bool)
    lab[np.argsort(x)[:54]] = False  # the planted label drops the worst fifth
    ef, _ = null(x, int(lab.sum()), 2000, 5)
    if verdict(efficiency(x[lab]), x[lab].mean(), x.mean(), float(np.quantile(ef, 0.95)), p95_se(ef, 200)) != "INCREMENT":
        raise SystemExit("selftest: a label that drops the losers did not read INCREMENT")
    ef0, mu0 = null(x, 270, 2, 3)
    if not np.allclose(mu0, x.mean(), rtol=0, atol=1e-12):
        raise SystemExit("selftest: a full-size subset does not reproduce the book")
    if verdict(0.30, 10.0, 12.0, 0.2, 0.01) != "NO INCREMENT" or verdict(0.205, 13.0, 12.0, 0.2, 0.01) != "UNRESOLVED (within 2 SE of the p95)":
        raise SystemExit("selftest: the verdict logic")
    print(f"selftest OK: a random label passes {rate:.3f} of {worlds} worlds (about 0.05); a label that drops the losers reads "
          "INCREMENT; a full-size subset reproduces the book; a lower mean reads NO INCREMENT and a margin inside 2 SE "
          "reads UNRESOLVED. The known answers (D707's ES F2, D711's NQ book, the 217/33/52 overlap) run first in --run.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.run:
        ap.print_help()
        return 1
    if OUT.exists():
        raise D714Error(f"{OUT.name} exists: D714's run is once")
    out = study()
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: out[k] for k in ("verdict", "B_trades", "A_trades", "dropped", "efficiency", "mean_net",
                                          "null_efficiency", "null_mean_net_reported", "predictions", "runtime_min")},
                     indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
