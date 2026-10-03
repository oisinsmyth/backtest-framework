"""D791 EXPLORE: patterns in the oracle's China-open trades (in-sample 2016-2023, disclosed; triage only).
Scope: docs/decisions/D791-EXPLORE-patterns-in-the-oracle-s-china-open-trades-scope.md.

    python scripts/explore_d791_oracle_patterns.py --build              # SYSTEM interpreter: the tape -> temp/d791/
    uv run --no-sync python scripts/explore_d791_oracle_patterns.py --run   # scikit-learn: mining + walk-forward models

Part A: every pre-entry feature's AUC for the oracle's take/reject label (net > 0), and for big winners against big
losers, with an exact rotation null per feature and a family-max null. Part B: ridge, boosted trees and logistic
models trained on prior years only and scored on each following year (2018-2023), against 50 shuffled-label runs.
Nothing on or after 2024-01-01 is read.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
SCOPE = REPO / "docs" / "decisions" / "D791-EXPLORE-patterns-in-the-oracle-s-china-open-trades-scope.md"
CACHE = REPO / "temp" / "d791"
FEAT = CACHE / "features.csv.gz"                               # CSV: the uv environment has no parquet engine
META = CACHE / "meta.json"
OUT = REPO / "data" / "explore_d791_oracle_patterns.json"
SEAL = "2024-01-01"
SPLIT = "2020-01-01"
TAKER_COST = 5.93
TEST_YEARS = ("2018", "2019", "2020", "2021", "2022", "2023")
N_SHUFFLE, SEED = 50, 791
NON_FEATURES = ("day", "gross", "net", "gross_p", "net_p", "filled", "year", "y", "x")


class D791Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D791Error(msg)


# ================================================================================ build (system python)
def build() -> int:
    sys.path.insert(0, str(REPO / "scripts"))
    sys.path.insert(0, str(REPO / "src"))
    import stage0_d765_china_open as C
    import stage0_d767_china_open_fade_filter as F7
    import stage0_d769_yuan_fix_residual as V
    import stage0_d786_china_open_five_filters as D86
    import explore_d790_china_open_anatomy as A
    t0 = time.time()
    D86.WORKERS = 6
    B = D86.build()
    rep = D86.reproduce(B)
    e = B["e"]
    R = B["roots"]["GC"]
    sess = B["sess"]["mgc"]
    days = list(e.index)
    x = e["x"].to_numpy(float)
    sx = np.sign(x)
    print("build reproduced", f"{time.time() - t0:.0f}s", flush=True)
    F = A.session_features(R, e)
    G = A.trend_features(R, sess, e, F)
    shau, fix = D86.load_shau(), V.load_fix()
    P = D86.premium_table(R, shau, fix)
    dev = D86.dev_for_sessions(P, days)
    sd = P["d"].to_numpy()
    j = np.searchsorted(sd, np.array(days), side="left") - 1
    lvl = np.array([P["p"].iloc[i] if i >= 0 else np.nan for i in j])
    rus, rld = D86.western_returns(R, days)
    rs = D86.rstar_all(days, workers=6)
    rstar = rs["R"].to_numpy(float)
    fx = fix.set_index("date")["usdcny_fix"]
    fd = fix["date"].to_numpy()
    fchg = []
    for d in days:
        i = int(np.searchsorted(fd, d, side="left"))
        fchg.append(float(fx.iloc[i] - fx.iloc[i - 1]) if i < len(fd) and fd[i] == d and i > 0 else np.nan)
    tokyo, pre = [], []
    for d in days:
        a, k = A.price(R, C.bj(d, "08:00"))
        b, _ = A.price(R, C.bj(d, "08:30"), k if k >= 0 else None)
        c, _ = A.price(R, C.bj(d, "09:00"), k if k >= 0 else None)
        tokyo.append(b - a)
        pre.append(c - b)
    # daily closes for realised volatility (prior sessions only)
    alld = list(sess.index)
    p15 = pd.Series([A.price(R, C.bj(d, "15:00"))[0] for d in alld], index=alld).dropna()
    r = np.log(p15).diff()
    vol20 = r.rolling(20, min_periods=20).std().shift(1)
    vol250 = r.rolling(250, min_periods=200).std().shift(1)
    X = pd.DataFrame(index=e.index)
    X["abs_x"] = np.abs(x)
    X["side_long_fade"] = (sx < 0).astype(float)
    for c in F.columns:
        if c != "p0900":
            X[c] = F[c].to_numpy(float)
    for c in G.columns:
        X[c] = G[c].to_numpy(float)
    X["tokyo_along_x"] = sx * np.array(tokyo)
    X["preopen_along_x"] = sx * np.array(pre)
    X["g_along_fade"] = -sx * e["g"].to_numpy(float)
    X["gus_along_fade"] = -sx * e["g_us"].to_numpy(float)
    X["long_closure"] = (sess.loc[days, "g_kind"].to_numpy() == "day_close").astype(float)
    X["aud_along_x"] = sx * e["x6a"].to_numpy(float)
    X["sge_premium_level"] = lvl
    X["sge_dislocation_along_fade"] = -sx * dev
    X["fix_change_along_x"] = sx * np.array(fchg)
    X["us_session_along_x"] = sx * rus
    X["london_morning_along_x"] = sx * rld
    X["rstar_rel"] = rstar - D86.prior_rel(rstar)
    X["vol20"] = vol20.reindex(days).to_numpy(float)
    X["vol20_over_250"] = (vol20 / vol250).reindex(days).to_numpy(float)
    m = pd.to_datetime(pd.Series(days)).dt.month.to_numpy()
    X["month_sin"] = np.sin(2 * np.pi * m / 12)
    X["month_cos"] = np.cos(2 * np.pi * m / 12)
    X["weekday"] = pd.to_datetime(pd.Series(days)).dt.weekday.to_numpy().astype(float)
    X["est_clock"] = (~e["edt"].to_numpy(bool)).astype(float)
    X["day"] = days
    X["x"] = x
    X["y"] = e["y"].to_numpy(float)
    X["gross"] = e["gross"].to_numpy(float)
    X["net"] = e["net"].to_numpy(float)
    X["filled"] = e["filled"].to_numpy(bool)
    X["gross_p"] = np.where(X["filled"], e["gross_p"].to_numpy(float), np.nan)
    X["net_p"] = X["gross_p"] - B["cost_p"]
    X["year"] = [d[:4] for d in days]
    need(bool((X["day"] < SEAL).all()), "seal")
    CACHE.mkdir(parents=True, exist_ok=True)
    X.reset_index(drop=True).to_csv(FEAT, index=False, encoding="utf-8")
    with open(META, "w", encoding="utf-8") as fh:
        json.dump({"cost_p": B["cost_p"], "reproduced_d786": rep, "n": len(X), "built_s": round(time.time() - t0, 1),
                   "rstar_split_half": C.spearman(rs["R1"].to_numpy(float), rs["R2"].to_numpy(float))}, fh, indent=1,
                  default=str)
    print("features:", len([c for c in X.columns if c not in NON_FEATURES]), "->", FEAT.relative_to(REPO),
          f"{time.time() - t0:.0f}s", flush=True)
    return 0


# ================================================================================ part A: describe
def avg_ranks(v: np.ndarray) -> np.ndarray:
    return pd.Series(v).rank(method="average").to_numpy()


def auc(f: np.ndarray, lab: np.ndarray) -> float:
    m = np.isfinite(f) & np.isfinite(lab)
    f, lab = f[m], lab[m].astype(bool)
    n1, n0 = int(lab.sum()), int((~lab).sum())
    if n1 < 10 or n0 < 10:
        return float("nan")
    r = avg_ranks(f)
    return float((r[lab].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def describe(X: pd.DataFrame, feats: list[str], cost_p: float) -> dict[str, Any]:
    first = X["day"].to_numpy() < SPLIT
    g, gp = X["gross"].to_numpy(float), X["gross_p"].to_numpy(float)
    lab_t = (X["net"].to_numpy(float) > 0).astype(float)
    lab_p = np.where(X["filled"].to_numpy(bool), (X["net_p"].to_numpy(float) > 0).astype(float), np.nan)
    q1, q3 = np.nanquantile(g, [0.25, 0.75])
    big = np.where(g >= q3, 1.0, np.where(g <= q1, 0.0, np.nan))      # big winners against big losers
    labels = {"oracle_passive": lab_p, "oracle_taker": lab_t, "big_win_vs_big_loss": big}
    out, rot = {}, {k: [] for k in labels}
    n = len(X)
    for c in feats:
        f = X[c].to_numpy(float)
        r: dict[str, Any] = {"defined": int(np.isfinite(f).sum())}
        for ln, lab in labels.items():
            obs = auc(f, lab)
            nul = np.array([auc(np.roll(f, k), lab) for k in range(1, n)])
            dev = np.abs(nul - 0.5)
            rot[ln].append(dev)
            r[ln] = {"auc": obs, "auc_2016_19": auc(f[first], lab[first]), "auc_2020_23": auc(f[~first], lab[~first]),
                     "null_p975_dev": float(np.nanquantile(dev, 0.975)), "rank_dev": float(np.nanmean(dev < abs(obs - 0.5))),
                     "median_taken": float(np.nanmedian(f[lab == 1])), "median_rejected": float(np.nanmedian(f[lab == 0]))}
            h1, h2 = r[ln]["auc_2016_19"] - 0.5, r[ln]["auc_2020_23"] - 0.5
            r[ln]["lead"] = bool(abs(obs - 0.5) > r[ln]["null_p975_dev"] and np.sign(h1) == np.sign(h2) == np.sign(obs - 0.5))
        out[c] = r
    fam = {}
    for ln in labels:
        M = np.nanmax(np.vstack(rot[ln]), axis=0)
        best = max(feats, key=lambda c: abs(out[c][ln]["auc"] - 0.5) if np.isfinite(out[c][ln]["auc"]) else -1)
        b = abs(out[best][ln]["auc"] - 0.5)
        fam[ln] = {"best_feature": best, "best_auc": out[best][ln]["auc"], "family_p95_dev": float(np.quantile(M, 0.95)),
                   "p_family": float((1 + (M >= b).sum()) / (1 + len(M)))}
    oracle = {}
    for ln, lab, gg, cost in (("passive", lab_p, gp, cost_p), ("taker", lab_t, g, TAKER_COST)):
        m = np.isfinite(lab)
        oracle[ln] = {"pool": int(m.sum()), "taken": int(np.nansum(lab)), "take_rate": float(np.nanmean(lab)),
                      "taken_mean_net": float(np.nanmean(gg[lab == 1] - cost)), "rejected_mean_net": float(np.nanmean(gg[lab == 0] - cost))}
    return {"features": out, "family_max": fam, "oracle": oracle}


# ================================================================================ part B: learn, walk-forward
def rank_scale(train: np.ndarray, test: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Map each column to its empirical quantile in the TRAINING data (NaN -> 0.5); test uses the training CDF."""
    tr, te = np.full(train.shape, 0.5), np.full(test.shape, 0.5)
    for j in range(train.shape[1]):
        col = train[:, j]
        ok = np.isfinite(col)
        if ok.sum() < 20:
            continue
        srt = np.sort(col[ok])
        tr[ok, j] = np.searchsorted(srt, col[ok], side="right") / len(srt)
        okt = np.isfinite(test[:, j])
        te[okt, j] = np.searchsorted(srt, test[okt, j], side="right") / len(srt)
    return tr - 0.5, te - 0.5


def fit_predict(kind: str, Xtr: np.ndarray, ytr: np.ndarray, Xte: np.ndarray, seed: int) -> tuple[np.ndarray, np.ndarray]:
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.linear_model import LogisticRegression, Ridge
    a, b = rank_scale(Xtr, Xte)
    if kind == "ridge":
        target = (pd.Series(ytr).rank().to_numpy() / len(ytr)) - 0.5
        m = Ridge(alpha=100.0).fit(a, target)
        return m.predict(a), m.predict(b)
    if kind == "gbm":
        target = (pd.Series(ytr).rank().to_numpy() / len(ytr)) - 0.5
        m = HistGradientBoostingRegressor(max_depth=3, learning_rate=0.05, max_iter=200, min_samples_leaf=50,
                                          random_state=seed).fit(a, target)
        return m.predict(a), m.predict(b)
    if kind == "logit":
        m = LogisticRegression(C=0.05, max_iter=2000).fit(a, (ytr > TAKER_COST).astype(int))
        return m.decision_function(a), m.decision_function(b)
    raise D791Error(kind)


def walk_forward(X: pd.DataFrame, feats: list[str], kind: str, shuffle_seed: int | None = None) -> dict[str, Any]:
    yr = X["year"].to_numpy()
    M = X[feats].to_numpy(float)
    g = X["gross"].to_numpy(float)
    pred = np.full(len(X), np.nan)
    take = np.zeros(len(X), bool)
    rng = np.random.default_rng(shuffle_seed) if shuffle_seed is not None else None
    for ty in TEST_YEARS:
        tr, te = yr < ty, yr == ty
        ytr = g[tr].copy()
        if rng is not None:                                             # shuffle labels within each training year
            for y0 in np.unique(yr[tr]):
                idx = np.flatnonzero(yr[tr] == y0)
                ytr[idx] = ytr[idx][rng.permutation(len(idx))]
        ptr, pte = fit_predict(kind, M[tr], ytr, M[te], SEED)
        pred[te] = pte
        take[te] = pte > np.quantile(ptr, 2 / 3)
    return {"pred": pred, "take": take}


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    m = np.isfinite(a) & np.isfinite(b)
    ra, rb = avg_ranks(a[m]), avg_ranks(b[m])
    ra, rb = ra - ra.mean(), rb - rb.mean()
    return float(ra @ rb / math.sqrt((ra @ ra) * (rb @ rb)))


def tstat(v: np.ndarray) -> float:
    v = v[np.isfinite(v)]
    return float(v.mean() / (v.std(ddof=1) / math.sqrt(len(v)))) if len(v) > 2 else float("nan")


def book(X: pd.DataFrame, take: np.ndarray, cost_p: float) -> dict[str, Any]:
    yr = X["year"].to_numpy()
    oos = np.isin(yr, TEST_YEARS)
    out = {}
    for nm, g, cost, valid in (("passive", X["gross_p"].to_numpy(float), cost_p, X["filled"].to_numpy(bool)),
                               ("taker", X["gross"].to_numpy(float), TAKER_COST, np.ones(len(X), bool))):
        k = take & oos & valid
        all_ = oos & valid
        net = g[k] - cost
        by = pd.Series(net).groupby(yr[k]).mean()
        out[nm] = {"n": int(k.sum()), "mean_gross": float(g[k].mean()), "mean_net": float(net.mean()), "t_net": tstat(net),
                   "t_gross": tstat(g[k]), "control_mean_net_all_oos": float((g[all_] - cost).mean()),
                   "profitable_years": f"{int((by > 0).sum())} of {len(by)}",
                   "net_by_year": {k2: round(float(v), 2) for k2, v in by.items()}}
    return out


def learn(X: pd.DataFrame, feats: list[str], cost_p: float) -> dict[str, Any]:
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.inspection import permutation_importance
    g = X["gross"].to_numpy(float)
    yr = X["year"].to_numpy()
    oos = np.isin(yr, TEST_YEARS)
    lab = (X["net"].to_numpy(float) > 0).astype(float)
    res = {}
    for kind in ("ridge", "gbm", "logit"):
        w = walk_forward(X, feats, kind)
        sp = spearman(w["pred"][oos], g[oos])
        by = {ty: spearman(w["pred"][yr == ty], g[yr == ty]) for ty in TEST_YEARS}
        nul = np.array([spearman(walk_forward(X, feats, kind, SEED + 1000 + i)["pred"][oos], g[oos]) for i in range(N_SHUFFLE)])
        res[kind] = {"oos_spearman_with_gross": sp, "oos_by_year": by, "years_positive": int(sum(v > 0 for v in by.values())),
                     "oos_auc_oracle_taker": auc(w["pred"][oos], lab[oos]),
                     "shuffled_null_p50": float(np.quantile(nul, 0.5)), "shuffled_null_p95": float(np.quantile(nul, 0.95)),
                     "rank_vs_shuffled": float((nul < sp).mean()),
                     "lead": bool(sp > np.quantile(nul, 0.95) and sum(v > 0 for v in by.values()) >= 4),
                     "top_third_book": book(X, w["take"], cost_p)}
        print(f"{kind}: OOS rho {sp:+.4f} (shuffled p95 {res[kind]['shuffled_null_p95']:+.4f}) years+ "
              f"{res[kind]['years_positive']}/6 | passive {res[kind]['top_third_book']['passive']['mean_net']:+.2f} "
              f"t {res[kind]['top_third_book']['passive']['t_net']:.2f}", flush=True)
    # ridge coefficients on the full in-sample (descriptive) and the boosted model's out-of-sample permutation importance
    from sklearn.linear_model import Ridge
    a, _ = rank_scale(X[feats].to_numpy(float), X[feats].to_numpy(float)[:1])
    target = (pd.Series(g).rank().to_numpy() / len(g)) - 0.5
    coef = Ridge(alpha=100.0).fit(a, target).coef_
    res["ridge_coefficients_full_sample"] = dict(sorted(zip(feats, map(float, coef)), key=lambda kv: -abs(kv[1]))[:15])
    tr, te = yr < "2020", yr >= "2020"
    a_tr, a_te = rank_scale(X[feats].to_numpy(float)[tr], X[feats].to_numpy(float)[te])
    t_tr = (pd.Series(g[tr]).rank().to_numpy() / tr.sum()) - 0.5
    t_te = (pd.Series(g[te]).rank().to_numpy() / te.sum()) - 0.5
    m = HistGradientBoostingRegressor(max_depth=3, learning_rate=0.05, max_iter=200, min_samples_leaf=50,
                                      random_state=SEED).fit(a_tr, t_tr)
    pi = permutation_importance(m, a_te, t_te, n_repeats=20, random_state=SEED, scoring="r2")
    res["gbm_permutation_importance_train_2016_19_test_2020_23"] = dict(
        sorted(((f, float(v)) for f, v in zip(feats, pi.importances_mean)), key=lambda kv: -kv[1])[:15])
    return res


def run() -> int:
    need(not OUT.exists(), f"{OUT.name} exists: D791 is run-once")
    need(FEAT.exists(), "run --build first (system interpreter)")
    t0 = time.time()
    X = pd.read_csv(FEAT, dtype={"day": str, "year": str}, encoding="utf-8")
    meta = json.load(open(META, encoding="utf-8"))
    need(bool((X["day"] < SEAL).all()), "seal")
    need(len(X) == 1697 and round(float(X["gross"].mean()), 2) == 3.14, "right quantity: the cache is not D767's pool")
    feats = [c for c in X.columns if c not in NON_FEATURES]
    A = describe(X, feats, meta["cost_p"])
    print("part A done", f"{time.time() - t0:.0f}s", flush=True)
    for c, r in sorted(A["features"].items(), key=lambda kv: -abs(kv[1]["oracle_passive"]["auc"] - 0.5))[:12]:
        p = r["oracle_passive"]
        print(f"  {c:28s} passive AUC {p['auc']:.3f} ({p['auc_2016_19']:.3f} / {p['auc_2020_23']:.3f}) rank {p['rank_dev']:.3f}"
              f" {'LEAD' if p['lead'] else ''} | big win/loss AUC {r['big_win_vs_big_loss']['auc']:.3f}", flush=True)
    print("family:", A["family_max"], flush=True)
    Bres = learn(X, feats, meta["cost_p"])
    res = {"scope": SCOPE.name, "seal": f"nothing on or after {SEAL}", "build_meta": meta, "n_features": len(feats),
           "features": feats, "describe": A, "learn": Bres, "wall_s": round(time.time() - t0, 1)}
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, default=str)
    print(f"done {res['wall_s']}s ->", OUT.relative_to(REPO), flush=True)
    return 0


def selftest() -> int:
    rng = np.random.default_rng(1)
    lab = rng.random(800) < 0.45
    f = lab + rng.normal(scale=1.5, size=800)
    a = auc(f, lab.astype(float))
    need(0.6 < a < 0.75, f"auc on a planted feature {a}")
    need(abs(auc(rng.permutation(f), lab.astype(float)) - 0.5) < 0.06, "auc on a shuffled feature")
    tr = rng.normal(size=(300, 3))
    te = rng.normal(size=(50, 3))
    a1, b1 = rank_scale(tr, te)
    need(a1.min() >= -0.5 and a1.max() <= 0.5 and np.isfinite(b1).all(), "rank_scale range")
    print("selftest OK", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    return build() if a.build else run() if a.run else selftest() if a.selftest else 1


if __name__ == "__main__":
    sys.exit(main())
