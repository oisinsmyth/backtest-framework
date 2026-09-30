"""D703: an expected-profit filter on the reopened ES last-hour continuation at MES. Spec:
docs/decisions/D703-PRE-REG-the-last-hour-expected-profit-filter.md (6c17028a), the principal's design after D702.

    uv run python scripts/stage1_d703_last_hour_ep_filter.py --selftest
    uv run python scripts/stage1_d703_last_hour_ep_filter.py --time
    uv run python scripts/stage1_d703_last_hour_ep_filter.py --run          # development, once
    uv run python scripts/stage1_d703_last_hour_ep_filter.py --confirm --principals-word "..."   # held (s.3)

THE SIZE MODEL: D671's walk-forward sign-constrained NNLS (`size_forecast`, burn-in 250) of y = |P16:00 - P15:30| x $5
on x1 = ln(|F5| / sigma_F5) (+), x2 = G_SUM (-), x3 = ln IV (+). P = max(forecast, $1.25). THE RULE: take when
pi-hat x P >= 2 x $4.42, pi-hat the mean gross / P over EARLIER candidates (burn-in 40). DEVELOPMENT (in-sample
2016-01 -> 2023-12, walk-forward): (a) calibration slope of realised gross on projected gross > 0; (b) filtered mean
net > 0 at one-sided HAC t >= 1.645; (c) above the exact p95 of the enumerated joint rotation of the three features
against the candidates, the model refit at every offset; (d) positive without Feb-Apr 2020. The candidates, inputs and
known answers are D702's (its build is imported). The 2024-01 -> 2025-02 slice is held. Writes
data/stage1_d703_last_hour_ep_filter.json (statistics only; GEX via D688's panel, SqueezeMetrics, no per-date series).
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
import diag_d702_last_hour_oracle_mes as Z  # noqa: E402

P694, D, C = Z.P, Z.D, Z.C
OUT = REPO / "data" / "stage1_d703_last_hour_ep_filter.json"
D702_JSON = REPO / "data" / "diag_d702_last_hour_oracle_mes.json"
COST, TICK_USD, EP_K, PI_BURN, EDGE = 4.42, 1.25, 2.0, 40, 21
SIGNS = np.array([1.0, -1.0, 1.0])
FEATS = ("ln_f5z", "G_SUM", "lniv")
COVID = ("2020-02-01", "2020-04-30")
ERA_SPLIT = "2022-05-16"


class D703Error(RuntimeError):
    pass


# ================================================================================ the filter
def forecast(F: np.ndarray, y: np.ndarray, signs: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    old = C.SIGN
    C.SIGN = signs
    try:
        return C.size_forecast(F, y)
    finally:
        C.SIGN = old


def ep_filter(F: np.ndarray, y: np.ndarray, g: np.ndarray, sess: np.ndarray, signs: np.ndarray) -> dict[str, np.ndarray]:
    """P (projected $ move), pi-hat, projected gross and the take flag for every candidate, walk-forward."""
    f, B = forecast(F, y, signs)
    Pv = np.where(np.isfinite(f), np.maximum(f, TICK_USD), np.nan)
    ratio = np.where(np.isfinite(Pv), g / Pv, np.nan)
    pi, cnt = P694.pi_hat(sess, ratio)
    proj = pi * Pv
    ev = np.isfinite(Pv) & (cnt >= PI_BURN) & np.isfinite(proj)
    take = ev & (proj >= EP_K * COST)
    return {"f": f, "B": B, "P": Pv, "pi": pi, "proj": proj, "ev": ev, "take": take, "ratio": ratio}


def filtered_mean_net(F: np.ndarray, y: np.ndarray, g: np.ndarray, sess: np.ndarray, signs: np.ndarray) -> float:
    r = ep_filter(F, y, g, sess, signs)
    x = g[r["take"]] - COST
    return float(x.mean()) if len(x) else float("nan")


# ================================================================================ the rotation (processes over offsets[i::N])
_W: dict[str, Any] = {}


def rotated(F: np.ndarray, k: int) -> np.ndarray:
    """Roll the rows where all three features are finite by k among themselves; other rows unchanged."""
    fin = np.isfinite(F).all(axis=1)
    G = F.copy()
    G[fin] = np.roll(F[fin], k, axis=0)
    return G


def _init(F, y, g, sess) -> None:
    _W.update(F=F, y=y, g=g, sess=sess)


def _job(ks: list[int]) -> list[tuple[int, float]]:
    return [(k, filtered_mean_net(rotated(_W["F"], k), _W["y"], _W["g"], _W["sess"], SIGNS)) for k in ks]


def rotation(F, y, g, sess, ks: list[int], workers: int) -> dict[int, float]:
    chunks = [ks[i::workers] for i in range(workers)]
    with ProcessPoolExecutor(max_workers=workers, initializer=_init, initargs=(F, y, g, sess)) as ex:
        return dict(kv for part in ex.map(_job, chunks) for kv in part)


# ================================================================================ audits
def sigma_f5(f5: pd.Series, leak: bool = False) -> pd.Series:
    s = f5.rolling(252, min_periods=60).std()
    return s if leak else s.shift(1)


def sigma_audit(f5: pd.Series, sig: pd.Series, days: list[str]) -> None:
    """Second implementation: the std of F5 over the (up to) 252 sessions strictly before T."""
    pos = pd.Series(np.arange(len(f5)), index=f5.index)
    v = f5.to_numpy(float)
    for d in days:
        i = int(pos[d])
        w = v[max(0, i - 252):i]
        w = w[np.isfinite(w)]
        want = float(np.std(w, ddof=1)) if len(w) >= 60 else float("nan")
        got = float(sig.loc[d])
        if not ((math.isnan(want) and math.isnan(got)) or math.isclose(want, got, rel_tol=1e-9, abs_tol=1e-9)):
            raise D703Error(f"lag: sigma_F5 at {d} uses session T or later")


def sign_audit() -> None:
    for f5, p1530, p1600 in ((+5.0, 100.0, 101.0), (-5.0, 100.0, 99.0)):
        gross = np.sign(f5) * (p1600 - p1530) * 5.0
        if not gross > 0:
            raise D703Error("sign: a favourable continuation does not pay")


# ================================================================================ reporting
def book(g: np.ndarray, take: np.ndarray, days: np.ndarray, side: np.ndarray, years: float, arm: pd.Series | None) -> dict[str, Any]:
    n = int(take.sum())
    if n < 3:
        return {"trades": n}
    gt, nt = g[take], g[take] - COST
    tpy = n / years
    sd = nt.std(ddof=1)
    dn = math.sqrt(float(np.mean(np.minimum(nt, 0) ** 2)))
    daily = pd.Series(np.where(take, g - COST, 0.0), index=days)
    ddn = math.sqrt(float(np.mean(np.minimum(daily.to_numpy(), 0) ** 2)))
    eq = np.cumsum(nt)
    k1 = max(1, int(math.floor(0.01 * n)))
    srt = np.sort(nt)
    w, lo = nt[nt > 0], nt[nt <= 0]
    dt = days[take]
    yrs = pd.Series(nt, index=dt).groupby(lambda s: s[:4])
    era = dt >= ERA_SPLIT
    out = {"trades": n, "trades_per_year": tpy, "mean_gross": float(gt.mean()), "mean_net": float(nt.mean()),
           "t_net_hac": D.nw_t(nt)[0], "median_net": float(np.median(nt)), "hit_net": float((nt > 0).mean()),
           "payoff": float(w.mean() / -lo.mean()) if len(w) and len(lo) and lo.mean() < 0 else float("nan"),
           "skew": float(stats.skew(nt)), "kurtosis_excess": float(stats.kurtosis(nt)),
           "sharpe_per_trade": float(nt.mean() / sd * math.sqrt(tpy)), "sortino_per_trade": float(nt.mean() / dn * math.sqrt(tpy)) if dn > 0 else float("nan"),
           "sharpe_per_trade_gross": float(gt.mean() / gt.std(ddof=1) * math.sqrt(tpy)),
           "sharpe_daily": float(daily.mean() / daily.std(ddof=1) * math.sqrt(252)),
           "sortino_daily": float(daily.mean() / ddn * math.sqrt(252)) if ddn > 0 else float("nan"),
           "max_drawdown_usd": float(np.max(np.maximum.accumulate(eq) - eq)),
           "trim_1pct": {"ex_top": float(srt[:-k1].mean()), "ex_bottom": float(srt[k1:].mean()), "trimmed": float(srt[k1:-k1].mean())},
           "by_year": {y: {"n": int(len(v)), "net": float(v.mean())} for y, v in yrs},
           "before_after_2022_05_16_net": [float(nt[~era].mean()) if (~era).any() else float("nan"), float(nt[era].mean()) if era.any() else float("nan")],
           "long_net": float(nt[side[take] > 0].mean()) if (side[take] > 0).any() else float("nan"),
           "short_net": float(nt[side[take] < 0].mean()) if (side[take] < 0).any() else float("nan"),
           "cost_usd_round_trip": COST}
    if arm is not None:
        common = daily.index.intersection(arm.index)
        out["rho_with_macd_arm"] = float(np.corrcoef(daily.loc[common], arm.loc[common])[0, 1])
    return out


# ================================================================================ the study
def inputs() -> dict[str, Any]:
    bd = Z.build()
    X = bd["X"].sort_index()
    return {"X": X, "known": bd["known"]}


def study(workers: int) -> dict[str, Any]:
    t0 = time.time()
    sign_audit()
    m618 = Z._load("m618", "stage0_d618_sharpened_ladder.py")
    S, _ = m618.load_es()
    sig = sigma_f5(S["F5"])
    sample = list(S.index[70:: max(1, len(S) // 25)])
    sigma_audit(S["F5"], sig, sample)
    try:
        sigma_audit(S["F5"], sigma_f5(S["F5"], leak=True), sample)
    except D703Error:
        pass
    else:
        raise D703Error("the sigma_F5 lag canary did not fire")
    inp = inputs()
    X = inp["X"]
    if not np.allclose(X["f5z"].to_numpy(float), (S["F5"].abs() / sig).reindex(X.index).to_numpy(float), equal_nan=True):
        raise D703Error("D702's |F5|/sigma is not the audited sigma_F5")
    # D702's lines reproduced from the same candidates
    j702 = json.loads(D702_JSON.read_text(encoding="utf-8"))["lines"]
    g = X["gross"].to_numpy(float)
    if abs(g.mean() - j702["take_everything"]["mean_gross"]) > 1e-9 or \
            abs((g[FO.top_fraction(X["F5"].abs().to_numpy(float), 0.2)] - COST).mean() - j702["pre_entry_size_top20_by_absF5"]["mean_net"]) > 1e-9:
        raise D703Error("D702's lines are not reproduced")
    sess = X.index.to_numpy(str)
    y = X["abs_move"].to_numpy(float)
    if not np.array_equal(y, np.abs(X["P1600"] - X["P1530"]).to_numpy(float) * 5.0) or np.allclose(y, X["F5"].abs().to_numpy(float)):
        raise D703Error("right quantity: the target is not |P16:00 - P15:30| x $5")
    F = np.column_stack([np.log(X["f5z"].to_numpy(float)), X["G_SUM"].to_numpy(float), X["lniv"].to_numpy(float)])
    r = ep_filter(F, y, g, sess, SIGNS)
    C.SIGN, old = SIGNS, C.SIGN
    try:
        idx = list(range(C.BURN, len(sess), max(1, (len(sess) - C.BURN) // 20)))
        C.forecast_audit(r["f"], F, y, sess, idx)
    finally:
        C.SIGN = old
    P694.pi_audit(sess, r["ratio"], r["pi"], list(range(0, len(sess), max(1, len(sess) // 30))))
    ev, take = r["ev"], r["take"]
    years = (pd.Timestamp(str(sess[ev][-1])) - pd.Timestamp(str(sess[ev][0]))).days / 365.25
    side = X["side"].to_numpy(float)
    arm = P694.arm_daily()
    arm = arm[arm.index < "2024-01-01"]
    fb = book(g, take, sess, side, years, arm)
    cal = FO.calibration(r["proj"][ev], g[ev])
    exc = ~((sess >= COVID[0]) & (sess <= COVID[1]))
    net_ex = float((g[take & exc] - COST).mean())
    # the rotation control
    fin_n = int(np.isfinite(F).all(axis=1).sum())
    ks = list(range(EDGE, fin_n - EDGE))
    obs = filtered_mean_net(F, y, g, sess, SIGNS)
    if obs != filtered_mean_net(rotated(F, 0), y, g, sess, SIGNS) or obs != float((g[take] - COST).mean()):
        raise D703Error("rotation: offset 0 does not reproduce the filtered book")
    t_rot = time.time()
    rot = rotation(F, y, g, sess, ks, workers)
    wall = time.time() - t_rot
    nul = np.array([rot[k] for k in ks])
    nul = nul[np.isfinite(nul)]
    t_net = fb.get("t_net_hac", float("nan"))
    gates = {"a_calibration_slope": cal["slope"], "a_pass": bool(cal["slope"] > 0),
             "b_filtered_mean_net": fb.get("mean_net"), "b_t_net_hac": t_net, "b_pass": bool(fb.get("mean_net", -1) > 0 and t_net >= 1.645),
             "c_rotation": {"offsets": int(len(nul)), "p50": float(np.median(nul)), "p95": float(np.quantile(nul, 0.95)),
                            "p95_se": 0.0, "rank": float((nul < obs).mean()), "wall_s": round(wall, 1)},
             "c_pass": bool(obs > np.quantile(nul, 0.95)),
             "d_net_ex_covid": net_ex, "d_pass": bool(net_ex > 0)}
    verdict = "DEVELOPMENT PASS" if all(gates[k] for k in ("a_pass", "b_pass", "c_pass", "d_pass")) else "DEVELOPMENT FAIL"
    # reported
    placement = {"spearman_projected_vs_gross": FO.spearman(r["proj"][ev], g[ev]),
                 "assess_vs_oracle": FO.assess(r["proj"][ev], take[ev], g[ev], g[ev] - COST),
                 "size_model_spearman_P_vs_abs_move": FO.spearman(r["P"][ev], y[ev]),
                 "P_quantiles_5_50_95": [float(np.quantile(r["P"][ev], q)) for q in (0.05, 0.5, 0.95)],
                 "P_share_at_floor": float((r["P"][ev] <= TICK_USD).mean()),
                 "pi_hat_quantiles_5_50_95": [float(np.quantile(r["pi"][ev], q)) for q in (0.05, 0.5, 0.95)],
                 "final_slopes": dict(zip(FEATS, map(float, r["B"][np.flatnonzero(np.isfinite(r["B"]).all(axis=1))[-1]])))}
    ablations = {}
    for i, nm in enumerate(FEATS):
        ri = ep_filter(F[:, [i]], y, g, sess, SIGNS[[i]])
        ablations[nm] = book(g, ri["take"], sess, side, years, None)
    out = {"spec": "D703 (6c17028a)", "credit": "dealer gamma (GEX): SqueezeMetrics", "verdict": verdict, "gates": gates,
           "filtered_book": fb, "take_everything_on_evaluated": book(g, ev, sess, side, years, arm),
           "evaluated_candidates": int(ev.sum()), "evaluated_window": [str(sess[ev][0]), str(sess[ev][-1])],
           "calibration": cal, "placement": placement, "ablations_single_feature": ablations,
           "known_answer_d618": inp["known"], "runtime_min": round((time.time() - t0) / 60, 2)}
    fbn = out["filtered_book"]
    out["predictions"] = {
        "1_slope_positive_below_1": bool(0 < cal["slope"] < 1),
        "2_30_to_60_a_year_net_3_to_9": bool(30 <= fbn.get("trades_per_year", 0) <= 60 and 3 <= fbn.get("mean_net", 0) <= 9),
        "3_gate_c_passes_p95_near_0": bool(gates["c_pass"] and abs(gates["c_rotation"]["p95"]) < 3),
        "4_f5_alone_about_as_good": bool(abs(ablations["ln_f5z"].get("mean_net", 0) - fbn.get("mean_net", 0)) <= 2),
        "5_2016_17_and_post_2022_weakest": None}
    by = fbn.get("by_year", {})
    if by:
        worst = sorted(by, key=lambda k: by[k]["net"])[:3]
        out["predictions"]["5_2016_17_and_post_2022_weakest"] = {"worst_three_years": worst,
                                                                 "post_2022_below_pre": bool(fbn["before_after_2022_05_16_net"][1] < fbn["before_after_2022_05_16_net"][0])}
    return out


# ================================================================================ selftest
def selftest() -> int:
    fired: list[str] = []

    def must_raise(name: str, fn: Callable[[], Any]) -> None:
        try:
            fn()
        except (D703Error, C.D671Error, P694.D694Error):
            fired.append(name)
            return
        raise SystemExit(f"selftest: the {name} canary did not raise")
    sign_audit()
    rng = np.random.default_rng(3)
    f5 = pd.Series(rng.normal(0, 20, 600), index=[f"2017-{1 + i // 28 % 12:02d}-{1 + i % 28:02d}-{i:04d}" for i in range(600)])
    sig = sigma_f5(f5)
    days = list(f5.index[80::50])
    sigma_audit(f5, sig, days)
    must_raise("a sigma_F5 that includes session T", lambda: sigma_audit(f5, sigma_f5(f5, leak=True), days))
    # the filter on synthetic data: an injected size effect is taken; rotation offset 0 reproduces; processes == serial
    n = 900
    sess = np.array([f"s{i:05d}" for i in range(n)])
    Fz = rng.normal(size=(n, 3))
    # the template needs a mechanism before it can scale it: a small average edge that grows with the size input
    size = np.clip(25 + 12 * Fz[:, 0] - 6 * Fz[:, 1] + 4 * Fz[:, 2] + rng.normal(0, 5, n), 1.0, None)  # $ moves, as at MES
    direction = np.where(rng.random(n) < 0.55 + 0.15 * np.tanh(Fz[:, 0]), 1.0, -1.0)
    g = direction * size
    y = size
    r = ep_filter(Fz, y, g, sess, SIGNS)
    if not (r["take"].sum() > 20 and (g[r["take"]] - COST).mean() > (g[r["ev"]] - COST).mean()):
        raise SystemExit("selftest: the filter does not select the injected big-move trades")
    obs = filtered_mean_net(Fz, y, g, sess, SIGNS)
    if obs != filtered_mean_net(rotated(Fz, 0), y, g, sess, SIGNS):
        raise SystemExit("selftest: rotation offset 0 does not reproduce")
    ks = [21, 22, 57]
    serial = {k: filtered_mean_net(rotated(Fz, k), y, g, sess, SIGNS) for k in ks}
    par = rotation(Fz, y, g, sess, ks, 2)
    if any(serial[k] != par[k] and not (math.isnan(serial[k]) and math.isnan(par[k])) for k in ks):
        raise SystemExit("selftest: the rotation's processes differ from the serial run")
    old = C.SIGN
    C.SIGN = SIGNS
    try:
        fleak, _ = C.size_forecast(Fz, y, leak=True)
        must_raise("a size model fitted on its own row", lambda: C.forecast_audit(fleak, Fz, y, sess, [300, 450, 899]))
    finally:
        C.SIGN = old
    print(f"selftest OK: {len(fired)} canaries fired: {fired}; the sign audit holds; the filter selects injected big-move "
          "trades; offset 0 reproduces; processes == serial. D618's, D702's, D691's and D688's known answers need the "
          "fixtures and run in --run.")
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
            print("refused: the 2024-01 -> 2025-02 slice is held; it is read only on the principal's word (D703 s.3)")
            return 2
        raise D703Error("the confirmation path is built when the principal releases the slice (D703 s.3); not yet")
    if a.time:
        inp = inputs()
        X = inp["X"]
        F = np.column_stack([np.log(X["f5z"].to_numpy(float)), X["G_SUM"].to_numpy(float), X["lniv"].to_numpy(float)])
        y, g, sess = X["abs_move"].to_numpy(float), X["gross"].to_numpy(float), X.index.to_numpy(str)
        t0 = time.time()
        for k in (21, 22):
            filtered_mean_net(rotated(F, k), y, g, sess, SIGNS)
        per = (time.time() - t0) / 2
        nk = int(np.isfinite(F).all(axis=1).sum()) - 2 * EDGE
        print(f"{per:.2f} s an offset x {nk} offsets / {a.workers} workers = about {per * nk / a.workers / 60:.1f} min")
        return 0
    if not a.run:
        ap.print_help()
        return 1
    if OUT.exists():
        raise D703Error(f"{OUT.name} exists: D703's development run is once")
    out = study(a.workers)
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: out[k] for k in ("verdict", "gates", "evaluated_candidates", "evaluated_window", "predictions")}, indent=1, default=float))
    fb = out["filtered_book"]
    print(json.dumps({k: fb.get(k) for k in ("trades", "trades_per_year", "mean_gross", "mean_net", "t_net_hac", "hit_net", "sharpe_per_trade",
                                             "sortino_per_trade", "sharpe_daily", "sortino_daily", "max_drawdown_usd", "rho_with_macd_arm")}, indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
