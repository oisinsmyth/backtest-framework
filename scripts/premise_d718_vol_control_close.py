"""D718 PREMISE -- proposal A: does ES's 15:45 -> 16:00 move follow the sign of the projected vol-control flow?
Design: docs/decisions/D718-PREMISE-DESIGN-vol-control-flow-at-the-close.md (committed before this runner). The principal:
"Ok do the cheap check please". No trade is scored as a result; trade lines are reported only.

    uv run python scripts/premise_d718_vol_control_close.py --selftest
    uv run python scripts/premise_d718_vol_control_close.py --run --data-root "<main checkout>/data"

f(d) = w(d) - w(d-1), w(d) = min(1, 0.10 / (sigma_hat(d-1) sqrt 252)), sigma_hat^2 an EWMA (lambda 0.94) of daily
close-to-close log returns (same contract; a roll leaves it unchanged), through the previous close. Regression per window:
y = a + beta z(f) + gamma z(the day's move to the window start), NW(5), on days with f != 0. G1 beta_close > 0, t >= 2;
G2 above the enumerated rotation p95 of f; G3 the 11:45 placebo t < 2 and beta_close > beta_mid; G4 f(d-1) t < 2.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d688_gamma_close as S688              # noqa: E402
import stage0_d689_short_gamma_continuation as Q    # noqa: E402

OUT = REPO / "data" / "premise_d718_vol_control_close.json"
WARM, LO, HI, CUT = "2015-06-01", "2016-01-04", "2023-12-29", "2024-01-01"
LAM, TARGET, ANN = 0.94, 0.10, math.sqrt(252)
BARS = ("11:44", "11:59", "14:29", "15:29", "15:44", "15:59")
ROT_MIN = 20
COST, USD = 4.42, 5.0


class D718Error(RuntimeError):
    pass


def P(*a, **k):
    print(*a, **k, flush=True)


def seal(days, what):
    d = pd.Series(np.asarray(days)).astype(str)
    if len(d) and (d >= CUT).any():
        raise D718Error(f"[SEAL] {what}: a row dated {d[d >= CUT].min()} reached the build")


def weights(r: np.ndarray, lam: float = LAM, cap: bool = True, leak: bool = False) -> np.ndarray:
    """w(d) from sigma_hat through d-1 (leak=True uses d as well: the self-test's broken book)."""
    n = len(r)
    w = np.full(n, np.nan)
    fin = np.flatnonzero(np.isfinite(r))
    if len(fin) < 21:
        return w
    s2 = float(np.var(r[fin[:20]], ddof=1))
    start = fin[19] + 1
    for d in range(start, n):
        if leak and np.isfinite(r[d]):
            s2 = lam * s2 + (1 - lam) * r[d] ** 2
        v = TARGET / (math.sqrt(s2) * ANN)
        w[d] = min(1.0, v) if cap else v
        if not leak and np.isfinite(r[d]):
            s2 = lam * s2 + (1 - lam) * r[d] ** 2
    return w


def load(data_root: Path, log=P) -> pd.DataFrame:
    fx = data_root / "fixtures"
    sess = pd.read_csv(fx / "fut_index_sessions.csv.gz", usecols=["root", "day", "bars"], dtype={"root": str, "day": str}, encoding="utf-8")
    cal = set(sess[(sess["root"] == "ES") & (sess["bars"] >= 380) & (sess["day"] >= WARM) & (sess["day"] <= HI)]["day"])
    b = pd.read_csv(fx / "fut_ES_rth_1m.csv.gz", usecols=["day", "hhmm", "contract", "close"], dtype={"day": str, "hhmm": str, "contract": str}, encoding="utf-8")
    b = b[(b["day"] >= WARM) & (b["day"] <= HI)]
    seal(b["day"], "ES bars")
    nb = b.groupby("day").size()
    days = np.array(sorted(d for d in cal if nb.get(d, 0) >= 380))
    kb = b[b["day"].isin(set(days)) & b["hhmm"].isin(BARS)].pivot(index="day", columns="hhmm", values=["close", "contract"]).reindex(days)
    D = pd.DataFrame(index=days)
    D["contract"] = kb[("contract", "15:59")]
    one = np.ones(len(days), bool)
    for h in BARS:
        one &= (kb[("contract", h)] == D["contract"]).to_numpy()
    D["one"] = one
    for h in BARS:
        D[f"P{h.replace(':', '')}"] = kb[("close", h)].astype(float)
    prevc = D["P1559"].shift(1)
    same = (D["contract"] == D["contract"].shift(1)).to_numpy()
    D["r"] = np.where(same & one, np.log(D["P1559"] / prevc), np.nan)
    D["prev_close_same"] = np.where(same, prevc, np.nan)
    log(f"  {len(days)} ES sessions {days[0]} .. {days[-1]} (warm-up from {WARM})")
    return D


def build(D: pd.DataFrame, lam: float = LAM, cap: bool = True) -> pd.DataFrame:
    X = D.copy()
    X["w"] = weights(X["r"].to_numpy(float), lam, cap)
    X["f"] = X["w"] - X["w"].shift(1)
    X["f_lag"] = X["f"].shift(1)
    pc = X["prev_close_same"]
    X["y_close"] = 1e4 * np.log(X["P1559"] / X["P1544"])
    X["mom_close"] = np.log(X["P1544"] / pc)
    X["y_mid"] = 1e4 * np.log(X["P1159"] / X["P1144"])
    X["mom_mid"] = np.log(X["P1144"] / pc)
    X["hour_1430"] = np.log(X["P1529"] / X["P1429"])
    return X


def z(x):
    x = np.asarray(x, float)
    return (x - x.mean()) / x.std(ddof=1)


def reg(y, cols):
    Xm = sm.add_constant(np.column_stack([z(c) for c in cols]))
    r = sm.OLS(np.asarray(y, float), Xm).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
    return {"beta": float(r.params[1]), "t": float(r.tvalues[1]), "n": int(len(y)), "controls": [float(v) for v in r.params[2:]]}


def rotation_beta(y, f, ctrl):
    """beta of z(f rotated) with the controls held (FWL: residualise y once, and each rotated f on [1, controls])."""
    y = np.asarray(y, float); zf = z(f)
    C = np.column_stack([np.ones(len(y))] + [z(c) for c in ctrl])
    proj = C @ np.linalg.pinv(C)
    ry = y - proj @ y
    n = len(y)
    ks = np.concatenate([[0], np.arange(ROT_MIN, n - ROT_MIN + 1)])
    Fr = np.column_stack([np.roll(zf, k) for k in ks])
    Rf = Fr - proj @ Fr
    betas = (Rf * ry[:, None]).sum(0) / (Rf * Rf).sum(0)
    return float(betas[0]), betas[1:]


def blk(obs, null):
    return {"observed": float(obs), "p50": float(np.percentile(null, 50)), "p95": float(np.percentile(null, 95)), "n_offsets": int(len(null)),
            "p95_se": 0.0, "pct_rank": float((null < obs).mean()), "above_p95": bool(obs > np.percentile(null, 95))}


def lag_audit(D: pd.DataFrame, X: pd.DataFrame, sample, log=P):
    """Second implementation: a plain loop from the first return, sigma through d-1 only."""
    r = D["r"].to_numpy(float)
    fin = [i for i in range(len(r)) if math.isfinite(r[i])]
    for d in sample:
        s2 = float(np.var([r[i] for i in fin[:20]], ddof=1))
        for i in range(fin[19] + 1, d):
            if math.isfinite(r[i]):
                s2 = LAM * s2 + (1 - LAM) * r[i] * r[i]
        want = min(1.0, TARGET / (math.sqrt(s2) * ANN))
        if not math.isclose(want, X["w"].iloc[d], rel_tol=1e-10):
            raise D718Error(f"[LAG] {X.index[d]}: w {X['w'].iloc[d]!r} vs the loop's {want!r}")
    log(f"  lag audit: w re-derived by a plain loop on {len(sample)} days: equal")


def run(data_root: Path, log=P) -> int:
    t0 = time.time()
    D = load(data_root, log)
    X = build(D)
    rng = np.random.default_rng(718)
    lag_audit(D, X, rng.choice(np.flatnonzero(np.isfinite(X["w"].to_numpy(float)) & (X.index >= LO)), 40, replace=False), log)
    need = ["f", "y_close", "mom_close", "y_mid", "mom_mid", "f_lag", "hour_1430"]
    ok = (X.index >= LO) & X["one"].to_numpy(bool) & np.isfinite(X[need].to_numpy(float)).all(1) & (X["f"].to_numpy(float) != 0)
    S = X[ok]
    if (S.index >= CUT).any():
        raise D718Error("[SEAL] a scored day on or after 2024-01-01")
    g1 = reg(S["y_close"], [S["f"], S["mom_close"]])
    b0, null = rotation_beta(S["y_close"], S["f"], [S["mom_close"]])
    if not math.isclose(b0, g1["beta"], rel_tol=1e-9):
        raise D718Error(f"[RIGHT-QUANTITY] the rotation's offset 0 {b0!r} is not the regression's beta {g1['beta']!r}")
    g2 = blk(b0, null)
    g3 = reg(S["y_mid"], [S["f"], S["mom_mid"]])
    g4 = reg(S["y_close"], [S["f_lag"], S["mom_close"]])
    gates = {"G1_exists": {**g1, "pass": bool(g1["beta"] > 0 and g1["t"] >= 2.0)},
             "G2_not_chance": {**g2, "pass": bool(g2["above_p95"])},
             "G3_close_not_day": {"midday": g3, "pass": bool(g3["t"] < 2.0 and g1["beta"] > g3["beta"])},
             "G4_today_not_yesterday": {"f_lag": g4, "pass": bool(g4["t"] < 2.0)}}
    p = {k: v["pass"] for k, v in gates.items()}
    reading = "PRESENT" if all(p.values()) else ("ABSENT" if not (p["G1_exists"] and p["G2_not_chance"]) else "NOT THE FUNDS")
    # ---- reported ----
    rep = {}
    rep["with_the_14_30_hour_controlled"] = reg(S["y_close"], [S["f"], S["mom_close"], S["hour_1430"]])
    sgn = np.sign(S["f"].to_numpy(float))
    gross = sgn * (S["P1559"] - S["P1544"]).to_numpy(float) * USD
    net = gross - COST
    days_all = np.array(sorted(S.index))
    di = np.searchsorted(days_all, S.index.to_numpy())
    arm = S688.d685().load_arm()
    fg = Q.four_groups(gross, net, di, sgn, days_all, len(days_all), arm, COST)
    def tl(mask):
        g_, n_ = gross[mask], net[mask]
        nw = lambda x: float(sm.OLS(x, np.ones((len(x), 1))).fit(cov_type="HAC", cov_kwds={"maxlags": 5}).tvalues[0]) if len(x) > 10 else float("nan")
        return {"trades": int(mask.sum()), "per_year": float(mask.sum() / 8), "mean_gross": float(g_.mean()), "t_gross": nw(g_), "mean_net": float(n_.mean()),
                "t_net": nw(n_), "win": float((n_ > 0).mean()), "mean_bp": float((sgn[mask] * S["y_close"].to_numpy(float)[mask]).mean())}
    absf = np.abs(S["f"].to_numpy(float))
    big = absf >= np.quantile(absf, 2 / 3)
    letf = sgn == np.sign(S["mom_close"].to_numpy(float))
    rep["sign_trade_all"] = {**tl(np.ones(len(S), bool)), "four_groups": fg}
    rep["sign_trade_largest_third_abs_f"] = tl(big)
    rep["sign_trade_letf_agrees"] = tl(letf)
    up = S["mom_close"].to_numpy(float) > 0
    yv = S["y_close"].to_numpy(float); fv = S["f"].to_numpy(float)
    rep["up_day_contrast_bp"] = {"vol_rise_days_f_neg": float(yv[up & (fv < 0)].mean()), "vol_fall_days_f_pos": float(yv[up & (fv > 0)].mean()),
                                 "n": [int((up & (fv < 0)).sum()), int((up & (fv > 0)).sum())],
                                 "note": "the mechanism predicts vol-rise up days continue LESS (the funds sell)"}
    shapes = {}
    for lab, lam, cap in (("uncapped", LAM, False), ("lambda_0.90", 0.90, True), ("lambda_0.97", 0.97, True)):
        Xs = build(D, lam, cap)
        oks = (Xs.index >= LO) & Xs["one"].to_numpy(bool) & np.isfinite(Xs[["f", "y_close", "mom_close"]].to_numpy(float)).all(1) & (Xs["f"].to_numpy(float) != 0)
        shapes[lab] = reg(Xs.loc[oks, "y_close"], [Xs.loc[oks, "f"], Xs.loc[oks, "mom_close"]])
    rep["shapes"] = shapes
    yr = S.index.str[:4]
    rep["beta_by_year"] = {y: reg(S.loc[yr == y, "y_close"], [S.loc[yr == y, "f"], S.loc[yr == y, "mom_close"]]) for y in sorted(set(yr))}
    Xi = X[(X.index >= LO) & np.isfinite(X["f"].to_numpy(float))]
    rep["share_f_nonzero_by_year"] = {y: float((Xi.loc[Xi.index.str[:4] == y, "f"] != 0).mean()) for y in sorted(set(Xi.index.str[:4]))}
    # ---- F2 alignment and rho (the other session's request) ----
    try:
        rep["F2"] = f2_alignment(data_root, S, net)
    except Exception as e:     # reported, never gating: an F2 rebuild failure is written, not fatal
        rep["F2"] = {"error": f"{type(e).__name__}: {e}"}
    out = {"spec": "D718 PREMISE (in-sample 2016-2023; ES only; no trade scored as a result)", "reading": reading, "gates": gates,
           "scored_days": int(len(S)), "reported": rep, "timing_s": round(time.time() - t0, 1)}
    OUT.write_text(json.dumps(out, indent=1, default=lambda x: x.item() if hasattr(x, "item") else str(x)) + "\n", encoding="utf-8", newline="\n")
    log(f"  G1 beta {g1['beta']:+.3f} bp/sd (t {g1['t']:+.2f}); G2 pct {g2['pct_rank']:.3f} (p95 {g2['p95']:+.3f}); G3 midday {g3['beta']:+.3f} (t {g3['t']:+.2f}); "
        f"G4 f_lag {g4['beta']:+.3f} (t {g4['t']:+.2f}) -> {reading}")
    st = rep["sign_trade_all"]
    log(f"  sign trade: {st['trades']} ({st['per_year']:.0f}/yr) gross ${st['mean_gross']:+.2f} (t {st['t_gross']:+.2f}) net ${st['mean_net']:+.2f}; {out['timing_s']} s")
    return 0


def f2_alignment(data_root: Path, S: pd.DataFrame, net_sign: np.ndarray) -> dict:
    import importlib.util
    fx = Path(data_root) / "fixtures"
    if "m618" not in sys.modules:
        sp = importlib.util.spec_from_file_location("m618", REPO / "scripts" / "stage0_d618_sharpened_ladder.py")
        m = importlib.util.module_from_spec(sp); sys.modules["m618"] = m; sp.loader.exec_module(m)
    m618 = sys.modules["m618"]
    m618.FIX = fx
    m618.OPTS, m618.CUTS, m618.ES_1M = fx / "fut_es_options_eod.csv.gz", fx / "fut_es_0dte_volume_cutoffs.csv.gz", fx / "fut_ES_rth_1m.csv.gz"
    m618.STRIP, m618.SESSIONS = fx / "fut_settle_strip.csv.gz", fx / "fut_index_sessions.csv.gz"
    import vault_d716_nq_f2 as N
    N.M.FIX = fx
    V = N.V
    Xe = V.frame(); Fe = V.f2(Xe)
    bd = N.build()
    out = {}
    fs = pd.Series(np.sign(S["f"].to_numpy(float)), index=S.index)
    for lab, idx, side, take in (("ES_F2", Xe.index.to_numpy(str), Xe["side"].to_numpy(float), Fe["take"] & Fe["window"]),
                                 ("NQ_F2", bd["sn"], bd["Xn"]["side"].to_numpy(float), bd["Fn"]["take"] & bd["Fn"]["window"])):
        s_ = pd.Series(side, index=idx)
        common = s_.index.intersection(fs.index)
        tk = pd.Series(take, index=idx).reindex(common).to_numpy(bool)
        agree = (fs.reindex(common).to_numpy() == s_.reindex(common).to_numpy())
        out[lab] = {"take_days_scored": int(tk.sum()), "share_flow_sign_equals_side_on_take_days": float(agree[tk].mean()) if tk.any() else None,
                    "share_on_all_candidate_days": float(agree.mean()), "days": int(len(common))}
    sn, Fn, netn = bd["sn"], bd["Fn"], bd["net"]
    own = Fn["take"] & Fn["window"]
    nq = pd.Series(np.where(own, netn, 0.0)[Fn["window"]], index=sn[Fn["window"]])
    ours = pd.Series(net_sign, index=S.index)
    allq = pd.Series(0.0, index=nq.index).add(ours, fill_value=0.0).reindex(nq.index)
    out["rho_sign_trade_daily_net_with_NQ_F2"] = float(np.corrcoef(allq, nq)[0, 1])
    return out


def selftest() -> int:
    rng = np.random.default_rng(7180)
    r = rng.normal(0, 0.01, 1500)
    w = weights(r)
    if np.allclose(w[25:], weights(r, leak=True)[25:], equal_nan=True):
        raise SystemExit("selftest: the leaked sigma equals the prior-only one; the audit could not fire")
    n = 1500
    f = rng.normal(0, 1, n); mom = rng.normal(0, 1, n)
    y = 1.5 * f + 0.5 * mom + rng.normal(0, 14, n)
    rr = reg(y, [f, mom])
    b0, null = rotation_beta(y, f, [mom])
    if not (rr["t"] >= 2 and blk(b0, null)["above_p95"] and math.isclose(b0, rr["beta"], rel_tol=1e-9)):
        raise SystemExit(f"selftest: a planted flow effect failed G1/G2 ({rr})")
    fails = sum(reg(0.5 * mom + rng.normal(0, 14, n), [f, mom])["t"] < 2 for _ in range(200))
    if fails < 188:
        raise SystemExit(f"selftest: noise passed G1 {200 - fails} of 200 times")
    try:
        seal(["2023-12-29", "2024-01-02"], "canary")
    except D718Error:
        pass
    else:
        raise SystemExit("selftest: the seal did not fire")
    print(f"SELFTEST OK: the leaked sigma differs; a planted flow passes G1-G2 (offset 0 = beta); noise failed G1 {fails}/200; the seal fires")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    sys.exit(run(a.data_root) if a.run else 1)
