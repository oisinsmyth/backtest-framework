"""D705: a declared SECOND LOOK -- three relative-size filters on the ES last-hour continuation at MES, scored against a
best-of-three, count-matched rotation null. Spec: docs/decisions/D705-PRE-REG-relative-size-filters-on-the-last-hour.md
(784d2824), the principal: "Ok add F1 back in. Run the tests on all them."

    uv run python scripts/stage1_d705_relative_size_filters.py --selftest
    uv run python scripts/stage1_d705_relative_size_filters.py --time
    uv run python scripts/stage1_d705_relative_size_filters.py --run           # development, once
    uv run python scripts/stage1_d705_relative_size_filters.py --confirm --principals-word "..."   # held (s.3)

THE FAMILY (top 20 %, D671's walk-forward `tiers` over the previous 250 candidates): F1 tiers(a) >= 0.8, a = |F5| /
sigma_F5; F2 tiers((tiers(a) + tiers(b)) / 2) >= 0.8, b = today's realised vol to 15:30; F3 G_SUM < 0 and tiers(a) >=
0.8. The candidates and inputs are D702's (its build is imported, with D618's, D691's and D688's known answers).
GATES per member: (a) HAC t, Holm across three, p < 0.05; (b) above the exact p95 of the best-of-three rotation (raw
inputs rotated jointly, tiers and rules re-run, max over members); (c) positive ex Feb-Apr 2020; (d) no year > 50 % of
net and at least half the years positive. UNRESOLVED below 60 trades. The 2024-01 -> 2025-02 slice is held. Writes
data/stage1_d705_relative_size_filters.json (statistics only; GEX via D688's panel, SqueezeMetrics).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
from backtest_framework.validation import filter_oracle as FO  # noqa: E402
import stage1_d703_last_hour_ep_filter as E  # noqa: E402

Z, P694, D, C = E.Z, E.P694, E.D, E.C
OUT = REPO / "data" / "stage1_d705_relative_size_filters.json"
COST, EDGE, Q = 4.42, 21, 0.8
MEMBERS = ("F1", "F2", "F3")
COVID = ("2020-02-01", "2020-04-30")


class D705Error(RuntimeError):
    pass


# ================================================================================ the family
def family(A: np.ndarray, q: float = Q) -> dict[str, Any]:
    """A = columns (a, b, G_SUM) in candidate order. Returns the tiers and each member's take flag."""
    ta, tb = C.tiers(A[:, 0]), C.tiers(A[:, 1])
    tc = C.tiers((ta + tb) / 2)
    gs = A[:, 2]
    with np.errstate(invalid="ignore"):
        take = {"F1": ta >= q, "F2": tc >= q, "F3": (gs < 0) & (ta >= q)}
    return {"ta": ta, "tb": tb, "tc": tc, "take": take}


def window(fam: dict[str, Any], gs: np.ndarray) -> np.ndarray:
    return np.isfinite(fam["ta"]) & np.isfinite(fam["tc"]) & np.isfinite(gs)


def means(A: np.ndarray, g: np.ndarray, W: np.ndarray) -> dict[str, float]:
    fam = family(A)
    out = {}
    for m in MEMBERS:
        k = fam["take"][m] & W
        out[m] = float((g[k] - COST).mean()) if k.any() else float("nan")
        out[f"{m}_n"] = int(k.sum())
    return out


# ================================================================================ the best-of-three rotation
_W: dict[str, Any] = {}


def rotated(A: np.ndarray, k: int) -> np.ndarray:
    fin = np.isfinite(A).all(axis=1)
    B = A.copy()
    B[fin] = np.roll(A[fin], k, axis=0)
    return B


def _init(A, g, W) -> None:
    _W.update(A=A, g=g, W=W)


def _job(ks: list[int]) -> list[tuple[int, dict[str, float]]]:
    return [(k, means(rotated(_W["A"], k), _W["g"], _W["W"])) for k in ks]


def rotation(A, g, W, ks: list[int], workers: int) -> dict[int, dict[str, float]]:
    chunks = [ks[i::workers] for i in range(workers)]
    with ProcessPoolExecutor(max_workers=workers, initializer=_init, initargs=(A, g, W)) as ex:
        return dict(kv for part in ex.map(_job, chunks) for kv in part)


def best_of(r: dict[str, float]) -> float:
    v = [r[m] for m in MEMBERS if np.isfinite(r[m])]
    return max(v) if v else float("nan")


# ================================================================================ gates
def concentration(net: np.ndarray, days: np.ndarray, years_in_window: list[str]) -> dict[str, Any]:
    ys = pd.Series(net, index=days).groupby(lambda s: s[:4]).sum()
    tot = float(net.sum())
    share = float(ys.max() / tot) if tot > 0 else float("nan")
    pos = int(sum(ys.get(y, 0.0) > 0 for y in years_in_window))
    return {"total_net": tot, "max_year_share": share, "max_year": str(ys.idxmax()) if len(ys) else None,
            "positive_years": f"{pos} of {len(years_in_window)}",
            "pass": bool(tot > 0 and share <= 0.5 and pos >= math.ceil(len(years_in_window) / 2))}


# ================================================================================ the study
def study(workers: int) -> dict[str, Any]:
    t0 = time.time()
    E.sign_audit()
    X = E.inputs()["X"]
    g = X["gross"].to_numpy(float)
    j702 = json.loads(E.D702_JSON.read_text(encoding="utf-8"))["lines"]
    if abs(g.mean() - j702["take_everything"]["mean_gross"]) > 1e-9 or \
            abs((g[FO.top_fraction(X["F5"].abs().to_numpy(float), 0.2)] - COST).mean() - j702["pre_entry_size_top20_by_absF5"]["mean_net"]) > 1e-9:
        raise D705Error("D702's lines are not reproduced")
    sess = X.index.to_numpy(str)
    A = np.column_stack([X["f5z"].to_numpy(float), X["rv_today"].to_numpy(float), X["G_SUM"].to_numpy(float)])
    fam = family(A)
    step = max(1, len(sess) // 12)
    for nm, t, src in (("a", fam["ta"], A[:, 0]), ("b", fam["tb"], A[:, 1]), ("composite", fam["tc"], (fam["ta"] + fam["tb"]) / 2)):
        C.tier_audit(t, src, list(range(0, len(src), step)))
    W = window(fam, A[:, 2])
    wd = sess[W]
    years = (pd.Timestamp(str(wd[-1])) - pd.Timestamp(str(wd[0]))).days / 365.25
    years_in_window = sorted({d[:4] for d in wd})
    side = X["side"].to_numpy(float)
    arm = P694.arm_daily()
    arm = arm[arm.index < "2024-01-01"]
    exc = ~((sess >= COVID[0]) & (sess <= COVID[1]))
    obs = means(A, g, W)
    if obs != means(rotated(A, 0), g, W):
        raise D705Error("rotation: offset 0 does not reproduce the members' books")
    fin_n = int(np.isfinite(A).all(axis=1).sum())
    ks = list(range(EDGE, fin_n - EDGE))
    t_rot = time.time()
    rot = rotation(A, g, W, ks, workers)
    wall = time.time() - t_rot
    mx = np.array([best_of(rot[k]) for k in ks])
    mx = mx[np.isfinite(mx)]
    p95 = float(np.quantile(mx, 0.95))
    res: dict[str, Any] = {}
    pvals = {}
    for m in MEMBERS:
        take = fam["take"][m] & W
        nt = g[take] - COST
        t_, _ = D.nw_t(nt) if take.sum() > 10 else (float("nan"), float("nan"))
        pvals[m] = float(stats.norm.sf(t_)) if np.isfinite(t_) else 1.0
        counts = np.array([rot[k][f"{m}_n"] for k in ks])
        score = fam["tc"] if m == "F2" else fam["ta"]
        res[m] = {"trades": int(take.sum()), "mean_net": obs[m], "t_net_hac": t_,
                  "ex_covid_net": float((g[take & exc] - COST).mean()) if (take & exc).any() else float("nan"),
                  "concentration": concentration(nt, sess[take], years_in_window),
                  "rotation_count_range": [int(counts.min()), int(np.median(counts)), int(counts.max())],
                  "rank_vs_best_of_three": float((mx < obs[m]).mean()),
                  "book": E.book(g, take, sess, side, years, arm),
                  "assess_vs_oracle": FO.assess(score[W], take[W], g[W], g[W] - COST)}
        q33 = family(A, 2 / 3)["take"][m] & W
        res[m]["top33_reported"] = E.book(g, q33, sess, side, years, None)
    holm = P694.T.holm(pvals)
    for m in MEMBERS:
        r = res[m]
        r["holm_p"] = holm[m]
        r["gates"] = {"a_edge_holm": bool(r["mean_net"] > 0 and holm[m] < 0.05),
                      "b_above_best_of_three_p95": bool(r["mean_net"] > p95),
                      "c_positive_ex_covid": bool(r["ex_covid_net"] > 0),
                      "d_not_one_year": r["concentration"]["pass"]}
        if r["trades"] < 60:
            r["verdict"] = "UNRESOLVED"
        else:
            r["verdict"] = "DEVELOPMENT PASS" if all(r["gates"].values()) else "DEVELOPMENT FAIL"
    passing = [m for m in MEMBERS if res[m]["verdict"] == "DEVELOPMENT PASS"]
    out = {"spec": "D705 (784d2824)", "credit": "dealer gamma (GEX): SqueezeMetrics", "second_look": True,
           "window": [str(wd[0]), str(wd[-1])], "window_candidates": int(W.sum()), "years": years,
           "best_of_three_null": {"offsets": int(len(mx)), "p50": float(np.median(mx)), "p95": p95, "p95_se": 0.0,
                                  "wall_s": round(wall, 1)},
           "members": res, "passing": passing, "family_verdict": ("PASS: " + ", ".join(passing)) if passing else "NONE PASSES",
           "take_everything_on_window": E.book(g, W, sess, side, years, arm),
           "runtime_min": round((time.time() - t0) / 60, 2)}
    f1, f2, f3 = (res[m] for m in MEMBERS)
    out["predictions"] = {
        "1_F1_passes_all_with_t_near_2": bool(f1["verdict"] == "DEVELOPMENT PASS"),
        "2_F2_at_or_below_F1": bool(f2["mean_net"] <= f1["mean_net"]),
        "3_F3_highest_net_fewest_trades_and_fails_d_or_unresolved": bool(
            f3["mean_net"] >= max(f1["mean_net"], f2["mean_net"]) and f3["trades"] <= min(f1["trades"], f2["trades"])
            and (not f3["gates"]["d_not_one_year"] or f3["verdict"] == "UNRESOLVED")),
        "4_all_weaker_after_2022_05_16": bool(all(res[m]["book"].get("before_after_2022_05_16_net", [0, 1])[1]
                                                  < res[m]["book"].get("before_after_2022_05_16_net", [0, 1])[0] for m in MEMBERS)),
        "5_best_of_three_p95_between_3_and_5": bool(3 <= p95 <= 5)}
    return out


# ================================================================================ selftest
def selftest() -> int:
    fired: list[str] = []

    def must_raise(name: str, fn: Callable[[], Any]) -> None:
        try:
            fn()
        except (D705Error, C.D671Error):
            fired.append(name)
            return
        raise SystemExit(f"selftest: the {name} canary did not raise")
    E.sign_audit()
    rng = np.random.default_rng(705)
    x = rng.normal(size=700)
    C.tier_audit(C.tiers(x), x, list(range(0, 700, 40)))
    must_raise("a tier that ranks its own value", lambda: C.tier_audit(C.tiers(x, leak=True), x, list(range(300, 700, 40))))

    def world(effect: bool, n: int = 900) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        # the composite tier needs two 250-value burn-ins in sequence, so the window opens near candidate 500
        A = np.column_stack([np.abs(rng.normal(size=n)) + 0.1, rng.normal(size=n), rng.normal(size=n)])
        size = 10 + 25 * A[:, 0]
        p = 0.5 + (0.12 * np.tanh(A[:, 0] - 1.0) if effect else 0.0)
        g = np.where(rng.random(n) < p, 1.0, -1.0) * size + 1.0
        W = window(family(A), A[:, 2])
        return A, g, W
    A, g, W = world(True, 900)
    ob = means(A, g, W)
    if not ob["F1"] > (g[W] - COST).mean():
        raise SystemExit("selftest: F1 does not select an injected relative-size effect")
    if means(rotated(A, 0), g, W) != ob:
        raise SystemExit("selftest: offset 0 does not reproduce")
    ks = [21, 22, 57]
    serial = {k: means(rotated(A, k), g, W) for k in ks}
    par = rotation(A, g, W, ks, 2)
    if any(serial[k] != par[k] for k in ks):
        raise SystemExit("selftest: the rotation's processes differ from the serial run")
    # the best-of-three null's size on worlds with no effect (sub-sampled offsets for speed)
    hits = 0
    worlds = 30
    for _ in range(worlds):
        A0, g0, W0 = world(False)
        fin = int(np.isfinite(A0).all(axis=1).sum())
        mx0 = np.array([best_of(means(rotated(A0, k), g0, W0)) for k in range(EDGE, fin - EDGE, 6)])
        o0 = means(A0, g0, W0)
        hits += int(o0["F1"] > np.quantile(mx0[np.isfinite(mx0)], 0.95))
    rate = hits / worlds
    if rate > 0.15:
        raise SystemExit(f"selftest: with no effect, F1 cleared the best-of-three p95 in {rate:.2f} of worlds")
    print(f"selftest OK: {len(fired)} canary fired: {fired}; F1 finds an injected relative-size effect; offset 0 "
          f"reproduces; processes == serial; with no effect F1 clears the best-of-three p95 in {rate:.2f} of {worlds} worlds "
          "(<= 0.15). D618's, D702's, D691's and D688's known answers need the fixtures and run in --run.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--time", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--confirm", action="store_true")
    ap.add_argument("--principals-word", default=None)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 4))
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.confirm:
        if not (a.principals_word or "").strip():
            print("refused: the 2024-01 -> 2025-02 slice is held; it is read only on the principal's word (D705 s.3)")
            return 2
        raise D705Error("the confirmation path is built when the principal releases the slice (D705 s.3); not yet")
    if a.time:
        X = E.inputs()["X"]
        A = np.column_stack([X["f5z"].to_numpy(float), X["rv_today"].to_numpy(float), X["G_SUM"].to_numpy(float)])
        g = X["gross"].to_numpy(float)
        W = window(family(A), A[:, 2])
        t0 = time.time()
        for k in (21, 22, 23):
            means(rotated(A, k), g, W)
        per = (time.time() - t0) / 3
        nk = int(np.isfinite(A).all(axis=1).sum()) - 2 * EDGE
        print(f"{per:.3f} s an offset x {nk} offsets / {a.workers} workers = about {per * nk / a.workers / 60:.1f} min")
        return 0
    if not a.run:
        ap.print_help()
        return 1
    if OUT.exists():
        raise D705Error(f"{OUT.name} exists: D705's development run is once")
    out = study(a.workers)
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    brief = {m: {k: out["members"][m][k] for k in ("verdict", "trades", "mean_net", "t_net_hac", "holm_p", "ex_covid_net", "rank_vs_best_of_three", "gates")}
             | {"concentration": out["members"][m]["concentration"], "count_range": out["members"][m]["rotation_count_range"]} for m in MEMBERS}
    print(json.dumps({"family_verdict": out["family_verdict"], "window": out["window"], "null": out["best_of_three_null"],
                      "members": brief, "predictions": out["predictions"]}, indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
