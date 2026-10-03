"""D790 EXPLORE: the anatomy of gold's China open (in-sample 2016-2023, disclosed; triage only).
Scope: docs/decisions/D790-EXPLORE-anatomy-of-gold-s-china-open-scope.md.

    python scripts/explore_d790_china_open_anatomy.py --selftest
    python scripts/explore_d790_china_open_anatomy.py --run

Part 1: the mean GC move in every Beijing half-hour of the CME day, and what predicts the open's direction x.
Part 2: shape features of the 09:00-09:30 path (one-minute closes, isolated prints skipped; bar volumes).
Part 3: trend features against prior daily closes (P15:00 Beijing, prior sessions only).
Every feature is scored against the fade's gross (taker and passive, D786's build) in 2016-19, 2020-23 and the whole,
with an exact rotation null per feature and a family-max null across features. Nothing on or after 2024-01-01.
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
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))
import stage0_d765_china_open as C  # noqa: E402
import stage0_d767_china_open_fade_filter as F7  # noqa: E402
import stage0_d769_yuan_fix_residual as V  # noqa: E402
import stage0_d786_china_open_five_filters as D86  # noqa: E402

SCOPE = REPO / "docs" / "decisions" / "D790-EXPLORE-anatomy-of-gold-s-china-open-scope.md"
OUT = REPO / "data" / "explore_d790_china_open_anatomy.json"
SEAL = "2024-01-01"
MULT = 10.0
SPLIT = "2020-01-01"
LEAD_HALF = 0.03


class D790Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D790Error(msg)


def price(R: dict[str, Any], t: int, k: int | None = None) -> tuple[float, int]:
    """P(t) = the close of the bar starting at t - 1 minute (D765's p_at); NaN on an isolated print or another
    contract than k."""
    i = C.p_at(R, t)
    if i is None or R["iso_c"][i] or (k is not None and int(R["K"][i]) != k):
        return float("nan"), -1
    return float(R["C"][i]), int(R["K"][i])


# ================================================================================ part 1
def half_hour_drift(R: dict[str, Any], days: list[str]) -> dict[str, Any]:
    starts = [f"{h:02d}:{m:02d}" for h in range(7, 24) for m in (0, 30)] + \
             [f"{h:02d}:{m:02d}" for h in range(0, 5) for m in (0, 30)]
    rows = []
    for d in days:
        need(d < SEAL, "seal")
        nxt = (pd.Timestamp(d) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        edt = C.edt_by_zoneinfo(C.bj(d, "09:00"))
        for s in starts:
            dd = d if s >= "07:00" else nxt
            t = C.bj(dd, s)
            a, k = price(R, t)
            b, _ = price(R, t + 30, k if k >= 0 else None)
            if np.isfinite(a) and np.isfinite(b) and k >= 0:
                rows.append((d, s, edt, (b - a) * MULT))
    D = pd.DataFrame(rows, columns=["day", "start", "edt", "move"])
    D["year"] = D["day"].str[:4]

    def agg(g):
        v = g["move"].to_numpy(float)
        return {"n": int(len(v)), "mean": round(float(v.mean()), 3), "t": round(F7.tstat(v), 2),
                "share_up": round(float((v > 0).mean()), 3), "mean_abs": round(float(np.abs(v).mean()), 2)}
    out = {"all": {s: agg(g) for s, g in D.groupby("start", sort=False)},
           "EDT": {s: agg(g) for s, g in D[D["edt"]].groupby("start", sort=False)},
           "EST": {s: agg(g) for s, g in D[~D["edt"]].groupby("start", sort=False)},
           "open_0900_by_year": {y: agg(g) for y, g in D[D["start"] == "09:00"].groupby("year")}}
    return out


def x_drivers(e: pd.DataFrame, B: dict[str, Any]) -> dict[str, Any]:
    R = B["roots"]["GC"]
    days = list(e.index)
    shau = D86.load_shau()
    fix = V.load_fix()
    P = D86.premium_table(R, shau, fix)
    dev = D86.dev_for_sessions(P, days)
    sd = P["d"].to_numpy()
    j = np.searchsorted(sd, np.array(days), side="left") - 1
    lvl = np.array([P["p"].iloc[i] if i >= 0 else np.nan for i in j])
    fx = fix.set_index("date")["usdcny_fix"]
    fdates = fix["date"].to_numpy()
    fchg = []
    for d in days:
        i = int(np.searchsorted(fdates, d, side="left"))
        fchg.append(float(fx.iloc[i] - fx.iloc[i - 1]) if i < len(fdates) and fdates[i] == d and i > 0 else np.nan)
    x = e["x"].to_numpy(float)
    out = {"mean_x_usd": float(x.mean() * MULT), "t_x": F7.tstat(x), "share_up": float((x > 0).mean()), "n": int(len(x))}
    for nm, v, when in (("g_overnight", e["g"].to_numpy(float), "before 09:00"),
                        ("g_us_afternoon", e["g_us"].to_numpy(float), "before 09:00"),
                        ("sge_premium_level_prior_day", lvl, "before 09:00"),
                        ("sge_premium_20d_dislocation", dev, "before 09:00"),
                        ("cny_fix_change", np.array(fchg), "09:15, inside x"),
                        ("aud_same_window", e["x6a"].to_numpy(float), "contemporaneous")):
        m = np.isfinite(v) & np.isfinite(x)
        out[nm] = {"rho_with_x": C.spearman(v, x), "n": int(m.sum()), "se": 1 / math.sqrt(max(m.sum() - 1, 1)), "when": when}
    out["mean_x_by_premium_level_tercile"] = {}
    m = np.isfinite(lvl)
    q1, q2 = np.quantile(lvl[m], [1 / 3, 2 / 3])
    for nm, mm in (("low", m & (lvl <= q1)), ("mid", m & (lvl > q1) & (lvl <= q2)), ("high", m & (lvl > q2))):
        out["mean_x_by_premium_level_tercile"][nm] = {"n": int(mm.sum()), "mean_x_usd": float(x[mm].mean() * MULT),
                                                      "share_up": float((x[mm] > 0).mean())}
    return out


# ================================================================================ part 2 and 3 features
def session_features(R: dict[str, Any], e: pd.DataFrame) -> pd.DataFrame:
    rows = []
    vol = R["df"]["volume"].to_numpy(float)
    for d, x in zip(e.index, e["x"].to_numpy(float)):
        need(d < SEAL, "seal")
        t0 = C.bj(d, "09:00")
        p0, k = price(R, t0)
        c = np.array([p0] + [price(R, t0 + m, k)[0] for m in range(1, 31)])
        sx = 1.0 if x > 0 else -1.0
        f: dict[str, Any] = {"day": d}
        if k < 0 or np.isnan(c[0]) or np.isnan(c[30]) or np.isfinite(c).sum() < 25:
            rows.append(f)
            continue
        cf = pd.Series(c).ffill().to_numpy()                       # a skipped print carries the last good close
        dm = np.diff(cf)
        ax = abs(cf[30] - cf[0])
        tot = np.abs(dm).sum()
        along = sx * (cf - cf[0])
        ext = along.max()
        f["S1_spike"] = float(np.abs(dm).max() / tot) if tot > 0 else np.nan
        f["S2_burst3"] = float(max(sx * (cf[i + 3] - cf[i]) for i in range(28)) / ax) if ax > 0 else np.nan
        f["S3_time_of_extreme"] = float(np.argmax(along) / 30)
        f["S4_retrace"] = float((ext - along[30]) / ext) if ext > 0 else np.nan
        f["S5_efficiency"] = float(ax / tot) if tot > 0 else np.nan
        f["S6_first_minute"] = float(along[1] / ax) if ax > 0 else np.nan
        f["S7_first_five"] = float(along[5] / ax) if ax > 0 else np.nan
        f["S8_last_ten"] = float((along[30] - along[20]) / ax) if ax > 0 else np.nan
        i0 = int(np.searchsorted(R["S"], t0, side="left"))
        i1 = int(np.searchsorted(R["S"], t0 + 30, side="left"))
        v = vol[i0:i1][R["K"][i0:i1] == k]
        if len(v) >= 25 and v.sum() > 0:
            f["S9_volume_top3"] = float(np.sort(v)[-3:].sum() / v.sum())
            ts = R["S"][i0:i1][R["K"][i0:i1] == k]
            f["S10_late_volume"] = float(v[ts >= t0 + 20].sum() / v.sum())
        f["p0900"] = float(cf[0])
        rows.append(f)
    F = pd.DataFrame(rows).set_index("day").reindex(e.index)
    F["S11_relative_size"] = np.abs(e["x"].to_numpy(float)) / F7.prior_median_abs(e["x"].to_numpy(float))
    return F


def trend_features(R: dict[str, Any], sess: pd.DataFrame, e: pd.DataFrame, F: pd.DataFrame) -> pd.DataFrame:
    """Daily closes P(15:00 Beijing) over every weekday session in D765's table (prior sessions only)."""
    days = list(sess.index)
    p15 = np.array([price(R, C.bj(d, "15:00"))[0] for d in days])
    s = pd.Series(p15, index=days).dropna()
    prior = s.shift(1)                                              # the close strictly before the session
    out = pd.DataFrame(index=s.index)
    for n in (200, 50, 20):
        out[f"sma{n}"] = s.rolling(n, min_periods=n).mean().shift(1)
    out["hi250"] = s.rolling(250, min_periods=250).max().shift(1)
    ch = s.diff()
    up = ch.clip(lower=0).rolling(14, min_periods=14).mean().shift(1)
    dn = (-ch.clip(upper=0)).rolling(14, min_periods=14).mean().shift(1)
    out["rsi14"] = 100 - 100 / (1 + up / dn)
    out["ret20"] = (prior / s.shift(21) - 1)
    T = out.reindex(e.index)
    sx = np.sign(e["x"].to_numpy(float))
    p0 = F["p0900"].to_numpy(float)
    G = pd.DataFrame(index=e.index)
    for n, nm in ((200, "T1"), (50, "T2"), (20, "T3")):
        dist = 100 * (p0 / T[f"sma{n}"].to_numpy(float) - 1)
        G[f"{nm}u_dist_sma{n}"] = dist
        G[f"{nm}s_along_x_sma{n}"] = sx * dist
    G["T4_vs_250d_high"] = 100 * (p0 / T["hi250"].to_numpy(float) - 1)
    G["T5s_rsi14_along_x"] = sx * (T["rsi14"].to_numpy(float) - 50)
    G["T6s_ret20_along_x"] = sx * 100 * T["ret20"].to_numpy(float)
    return G


# ================================================================================ statistics
def rho_rot(f: np.ndarray, g: np.ndarray) -> np.ndarray:
    """rho(roll(f, k), g) for k = 0 .. n-1 (exact), on the finite pairs of each offset."""
    n = len(f)
    out = np.empty(n)
    for k in range(n):
        out[k] = C.spearman(np.roll(f, k), g)
    return out


def score(F: pd.DataFrame, e: pd.DataFrame, cost_p: float) -> dict[str, Any]:
    gt = e["gross"].to_numpy(float)
    gp = np.where(e["filled"].to_numpy(bool), e["gross_p"].to_numpy(float), np.nan)
    days = e.index.to_numpy()
    first = days < SPLIT
    y = e["y"].to_numpy(float)
    x = e["x"].to_numpy(float)
    cont = np.sign(y) == np.sign(x)
    bigrev = gt >= np.nanquantile(gt, 0.75)
    res, rots = {}, {"taker": [], "passive": []}
    for col in F.columns:
        f = F[col].to_numpy(float)
        r: dict[str, Any] = {"defined": int(np.isfinite(f).sum())}
        for book, g, cost in (("taker", gt, 5.93), ("passive", gp, cost_p)):
            rot = rho_rot(f, g)
            need(abs(rot[0] - C.spearman(f, g)) < 1e-12, f"{col}: rotation offset 0")
            rots[book].append(np.abs(rot[1:]))
            nul = np.abs(rot[1:])
            obs = rot[0]
            h1 = C.spearman(f[first], g[first])
            h2 = C.spearman(f[~first], g[~first])
            m = np.isfinite(f) & np.isfinite(g)
            q1, q2 = np.quantile(f[m], [1 / 3, 2 / 3])
            terc = {}
            for nm, mm in (("low", m & (f <= q1)), ("mid", m & (f > q1) & (f <= q2)), ("high", m & (f > q2))):
                terc[nm] = {"n": int(mm.sum()), "mean_gross": round(float(g[mm].mean()), 2),
                            "mean_net": round(float(g[mm].mean() - cost), 2), "t_gross": round(F7.tstat(g[mm]), 2)}
            lead = bool(abs(obs) > np.quantile(nul, 0.975) and np.sign(h1) == np.sign(h2) == np.sign(obs)
                        and abs(h1) >= LEAD_HALF and abs(h2) >= LEAD_HALF)
            r[book] = {"rho": obs, "rho_2016_19": h1, "rho_2020_23": h2, "null_abs_p50": float(np.quantile(nul, 0.5)),
                       "null_abs_p975": float(np.quantile(nul, 0.975)), "rank_abs": float((nul < abs(obs)).mean()),
                       "terciles": terc, "lead": lead}
        r["median_by_class"] = {"continuation": float(np.nanmedian(f[cont])), "reversal": float(np.nanmedian(f[~cont])),
                                "big_reversal_top_quartile": float(np.nanmedian(f[bigrev]))}
        res[col] = r
    fam = {}
    for book in ("taker", "passive"):
        M = np.vstack(rots[book]).max(axis=0)
        best = max(res, key=lambda c: abs(res[c][book]["rho"]))
        fam[book] = {"best_feature": best, "best_abs_rho": abs(res[best][book]["rho"]),
                     "family_max_p50": float(np.quantile(M, 0.5)), "family_max_p95": float(np.quantile(M, 0.95)),
                     "p_family": float((1 + (M >= abs(res[best][book]["rho"])).sum()) / (1 + len(M)))}
    return {"features": res, "family_max": fam}


# ================================================================================ run and self-test
def run() -> int:
    need(not OUT.exists(), f"{OUT.name} exists: D790 is run-once")
    t0 = time.time()
    B = D86.build()
    rep = D86.reproduce(B)
    e = B["e"]
    R = B["roots"]["GC"]
    sess = B["sess"]["mgc"]
    print("build reproduced", f"{time.time() - t0:.0f}s", flush=True)
    elig = [d for d in sess.index if sess.loc[d, "why"] == "eligible"]
    part1 = {"half_hour_drift": half_hour_drift(R, elig), "x_drivers": x_drivers(e, B)}
    print("part 1 done", f"{time.time() - t0:.0f}s", flush=True)
    F = session_features(R, e)
    G = trend_features(R, sess, e, F)
    feats = pd.concat([F.drop(columns=["p0900"]), G], axis=1)
    print("features built:", {c: int(feats[c].notna().sum()) for c in feats.columns}, flush=True)
    sc = score(feats, e, B["cost_p"])
    res = {"scope": SCOPE.name, "seal": f"nothing on or after {SEAL}", "reproduced_d786": rep, "part1": part1,
           "part23": sc, "wall_s": round(time.time() - t0, 1)}
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, default=str)
    for c, r in sc["features"].items():
        p, t = r["passive"], r["taker"]
        print(f"{c:24s} passive rho {p['rho']:+.3f} ({p['rho_2016_19']:+.3f} / {p['rho_2020_23']:+.3f}) rank {p['rank_abs']:.3f}"
              f" {'LEAD' if p['lead'] else ''} | taker {t['rho']:+.3f} ({t['rho_2016_19']:+.3f} / {t['rho_2020_23']:+.3f})"
              f" rank {t['rank_abs']:.3f} {'LEAD' if t['lead'] else ''}", flush=True)
    print("family:", sc["family_max"], f"| {res['wall_s']}s ->", OUT.relative_to(REPO), flush=True)
    return 0


def selftest() -> int:
    # shape features on a planted path: an up-open that spikes in one minute then drifts back
    rng = np.random.default_rng(1)
    g = rng.standard_t(3, 600) * 30
    f = g + rng.normal(scale=200, size=600)
    rot = rho_rot(f, g)
    need(abs(rot[0] - C.spearman(f, g)) < 1e-12 and (np.abs(rot[1:]) < abs(rot[0])).mean() > 0.95, "rotation: a planted feature")
    sh = rng.permutation(f)
    r2 = rho_rot(sh, g)
    need((np.abs(r2[1:]) < abs(r2[0])).mean() < 0.99, "rotation: a shuffled feature looked planted")
    R = C.load_root("GC")
    p, k = price(R, C.bj("2022-03-01", "09:00"))
    need(np.isfinite(p) and k >= 0, "price: no 09:00 price on a normal session")
    need(bool((R["df"]["day"] < SEAL).all()), "seal: the GC bars reach 2024")
    print("selftest OK", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args(argv)
    return selftest() if a.selftest else run() if a.run else 1


if __name__ == "__main__":
    sys.exit(main())
