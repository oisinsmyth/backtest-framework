"""D730 Stage 0: the principal's three-part trade on NQ -- direction from the drift since the open (D727), trend
detection from the volume profile (heavy early, then steady), size from the evening-before size forecast. Spec:
docs/decisions/D730-STAGE-0-PRE-REG-volume-profile-as-the-trend-detector.md, committed before this file existed.

    uv run python scripts/stage0_d730_volume_detector.py --selftest
    uv run python scripts/stage0_d730_volume_detector.py --run --data-root <checkout>/data      # once

NQ's objects are D727's (its functions, asserted against D727's known answer). Volume from the same one-minute bars;
the normal curve per minute = the mean of the prior 20 sessions. E = volume 09:30-09:59 over normal; R_t = volume over
the 30 minutes before t over normal; Q_t = R_t / E; D_t = 1 iff E is in its walk-forward top third and Q_t >= 1.
Nothing dated 2024-01-01 or later is used.
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
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d720_size_the_direction as Z  # noqa: E402
import stage0_d727_trend_curve as T  # noqa: E402
from backtest_framework.validation.hurdle_p import p3  # noqa: E402

OUT = REPO / "data" / "stage0_d730_volume_detector.json"
CLOCKS, NMIN, EDGE = T.CLOCKS, T.NMIN, T.EDGE
KS = (0.5, 1.0, 1.5)
P = Z.P


class D730Error(AssertionError):
    pass


# ================================================================================ the volume profile
def volume_panel(pn: dict[str, Any]) -> dict[str, np.ndarray]:
    """E [day], R and Q [day, clock] on D727's kept days; the normal curve from the prior 20 sessions of ALL days."""
    raw = pn["raw"]
    mins = [T.hhmm(m) for m in range(NMIN)]
    Vall = raw.pivot(index="day", columns="hhmm", values="volume").reindex(index=pn["all_days"], columns=mins)
    Vall = Vall.fillna(0.0).to_numpy(float)
    norm = pd.DataFrame(Vall).shift(1).rolling(20, min_periods=20).mean().to_numpy(float)
    pos = pd.Series(np.arange(len(pn["all_days"])), index=pn["all_days"]).reindex(pn["days"]).to_numpy(int)
    V, Nm = Vall[pos], norm[pos]
    with np.errstate(invalid="ignore", divide="ignore"):
        E = V[:, :30].sum(axis=1) / Nm[:, :30].sum(axis=1)
        R = np.column_stack([V[:, m - 30:m].sum(axis=1) / Nm[:, m - 30:m].sum(axis=1) for m in CLOCKS])
    Q = R / E[:, None]
    if not np.allclose(Q * E[:, None], R, equal_nan=True):
        raise D730Error("right quantity: Q is not R / E")
    con = raw.groupby("day")["contract"].agg(lambda s: s.value_counts().index[0]).reindex(pn["all_days"]).to_numpy(str)
    roll_ix = np.flatnonzero(np.r_[False, con[1:] != con[:-1]])
    pre = np.zeros(len(pn["all_days"]), bool)
    for i in roll_ix:
        pre[max(0, i - 5):i] = True
    return {"E": E, "R": R, "Q": Q, "pre_roll": pre[pos], "V": V, "norm": Nm}


def volume_audit(pn: dict[str, Any], vp: dict[str, np.ndarray], sample: list[tuple[int, int]], shift: int = 0) -> None:
    """Second implementation from the raw rows: bars with start minute < t (shift = 1 includes the t bar: the canary)."""
    raw = pn["raw"]
    allpos = {d: i for i, d in enumerate(pn["all_days"])}
    for d, j in sample:
        day = pn["days"][d]
        i = allpos[day]
        prior = pn["all_days"][i - 20:i]
        m = CLOCKS[j]
        win = {T.hhmm(k) for k in range(m - 30 + shift, m + shift)}
        early = {T.hhmm(k) for k in range(0, 30)}
        today = raw[raw["day"] == day]
        past = raw[raw["day"].isin(prior)]
        num_r = float(today[today["hhmm"].isin(win)]["volume"].sum())
        den_r = float(past[past["hhmm"].isin(win)]["volume"].sum()) / 20.0
        num_e = float(today[today["hhmm"].isin(early)]["volume"].sum())
        den_e = float(past[past["hhmm"].isin(early)]["volume"].sum()) / 20.0
        if not (math.isclose(num_r / den_r, vp["R"][d, j], rel_tol=1e-9) and math.isclose(num_e / den_e, vp["E"][d], rel_tol=1e-9)):
            raise D730Error(f"lag: the volume profile at {day} {T.hhmm(m)} reads a bar at or after t")


def detector(etier: np.ndarray, Q: np.ndarray) -> np.ndarray:
    return ((etier[:, None] >= 2 / 3) & (Q >= 1.0)).astype(float)


# ================================================================================ statistics
def slope(x: np.ndarray, y: np.ndarray, m: np.ndarray) -> float:
    ok = m & np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 30:
        return float("nan")
    xs, ys = x[ok], y[ok]
    xc = xs - xs.mean()
    return float((xc * (ys - ys.mean())).sum() / (xc * xc).sum())


def dbeta(D: np.ndarray, X: np.ndarray, Y: np.ndarray, extra: np.ndarray | None = None) -> float:
    e = np.ones_like(D, bool) if extra is None else extra
    return slope(X, Y, (D == 1) & e) - slope(X, Y, (D == 0) & e)


def rot(obs: float, null: list[float]) -> dict[str, float]:
    a = np.array(null, float)
    a = a[np.isfinite(a)]
    return {"observed": obs, "offsets": int(len(a)), "p05": float(np.quantile(a, 0.05)), "p50": float(np.median(a)),
            "p95": float(np.quantile(a, 0.95)), "p95_se": 0.0, "rank": float((a < obs).mean())}


def entries(z: np.ndarray, k: float) -> np.ndarray:
    hit = np.abs(z) >= k
    return np.where(hit.any(axis=1), hit.argmax(axis=1), -1)


def gross_per_mnq(ob: dict[str, np.ndarray], first: np.ndarray, usd: float) -> tuple[np.ndarray, np.ndarray]:
    rows = np.arange(len(first))
    fc = np.clip(first, 0, None)
    side = np.where(first >= 0, np.sign(ob["z"][rows, fc]), 0.0)
    g = np.where(first >= 0, side * (ob["close"] - ob["Pt"][rows, fc]) * usd, np.nan)
    return g, side


def book(q: np.ndarray, g: np.ndarray, cost: float, days: np.ndarray) -> dict[str, Any]:
    tr = (q > 0) & np.isfinite(g)
    net = np.where(tr, q * (g - cost), 0.0)
    gross = np.where(tr, q * g, 0.0)
    years = np.array([s[:4] for s in days])
    by = {y: float(net[years == y].sum()) for y in np.unique(years)}
    tot = sum(by.values())
    per = (g - cost)[tr]
    out = {"trades": int(tr.sum()), "contracts": float(q[tr].sum()),
           "mean_gross_per_mnq": float(g[tr].mean()) if tr.any() else None,
           "mean_net_per_mnq": float(per.mean()) if tr.any() else None,
           "median_gross_per_mnq": float(np.median(g[tr])) if tr.any() else None,
           "net_sharpe": Z.sharpe(net), "net_sortino": Z.sortino(net), "gross_sharpe": Z.sharpe(gross),
           "gross_sortino": Z.sortino(gross), "max_dd": Z.max_dd(net), "net_usd_a_year": float(net.sum() / (len(net) / 252)),
           "per_mnq_distribution": Z.trade_dist(per) if tr.any() else {"trades": 0}, "net_by_year": by,
           "years_positive": int(sum(v > 0 for v in by.values())), "years": len(by),
           "largest_year_share": float(max(by.values()) / tot) if tot > 0 else None}
    for acc in (50_000.0, 150_000.0):
        out[f"p3a_{int(acc / 1000)}k"] = p3(net, account=acc)["p3a_breaches_per_year"] if len(net) > 2 else None
    return out


# ================================================================================ per root S1
def s1(pn: dict[str, Any], ob: dict[str, np.ndarray], vp: dict[str, np.ndarray], etier: np.ndarray) -> dict[str, Any]:
    import stage0_d671_break_construction as C
    X, Y = ob["x"], ob["y"]
    D = detector(etier, vp["Q"])
    n = len(pn["days"])
    null = []
    for k in range(EDGE, n - EDGE):
        null.append(dbeta(detector(np.roll(etier, k), np.roll(vp["Q"], k, axis=0)), X, Y))
    on = (D == 1) & np.isfinite(X) & np.isfinite(Y)
    order = np.argsort(np.repeat(np.arange(n), len(CLOCKS)), kind="stable")
    nw_on = T.beta_nw(np.where(on, X, np.nan).ravel()[order], np.where(on, Y, np.nan).ravel()[order])
    res = {"share_detected": float(np.nanmean(D)), "beta_detected": slope(X, Y, D == 1), "beta_not": slope(X, Y, D == 0),
           "nw_detected": nw_on, "dbeta_rotation": rot(dbeta(D, X, Y), null),
           "dbeta_excl_pre_roll": dbeta(D, X, Y, ~vp["pre_roll"][:, None] & np.ones_like(D, bool)),
           "by_clock": [{"t": T.hhmm(m), "beta_detected": slope(X[:, [j]], Y[:, [j]], D[:, [j]] == 1),
                         "beta_not": slope(X[:, [j]], Y[:, [j]], D[:, [j]] == 0)} for j, m in enumerate(CLOCKS)],
           "E_tercile_alone": {nm: slope(X, Y, np.repeat(((etier >= lo) & (etier < hi))[:, None], len(CLOCKS), axis=1))
                               for nm, lo, hi in (("low", 0, 1 / 3), ("mid", 1 / 3, 2 / 3), ("high", 2 / 3, 1.01))},
           "Q_alone": {"Q>=1": slope(X, Y, vp["Q"] >= 1), "Q<1": slope(X, Y, vp["Q"] < 1)}}
    del C
    return res


# ================================================================================ the run
def run(data_root: Path) -> int:
    t0 = time.time()
    import stage0_d671_break_construction as C
    import stage0_d724_which_mean as W
    import stage1_d711_f2_mechanism as M711
    out: dict[str, Any] = {"spec": "D730-STAGE-0-PRE-REG-volume-profile-as-the-trend-detector.md",
                           "seal": f"nothing on or after {Z.CUT24}", "roots": {}}
    ka = json.loads((REPO / "data" / "stage0_d727_trend_curve.json").read_text(encoding="utf-8"))["roots"]
    rng = np.random.default_rng(730)
    built = {}
    for r in ("NQ", "YM", "RTY"):
        P(f"[D730] {r} ...")
        pn = T.load_root(r, data_root)
        ob = T.objects(pn)
        if len(pn["days"]) != ka[r]["days"] or not math.isclose(T.beta_nw(ob["x"][:, 0], ob["y"][:, 0])["beta"],
                                                                ka[r]["clocks"][0]["beta"], rel_tol=0, abs_tol=1e-12):
            raise D730Error(f"{r}'s objects are not D727's")
        vp = volume_panel(pn)
        smp = [(int(rng.integers(0, len(pn["days"]))), int(rng.integers(0, len(CLOCKS)))) for _ in range(25)]
        smp = [(d, j) for d, j in smp if np.isfinite(vp["E"][d]) and np.isfinite(vp["R"][d, j])]
        volume_audit(pn, vp, smp)
        try:
            volume_audit(pn, vp, smp, shift=1)
        except D730Error:
            pass
        else:
            raise D730Error(f"{r}: the volume lag canary did not fire")
        Ef = np.where(np.isfinite(vp["E"]), vp["E"], np.nan)
        etier = C.tiers(Ef)
        C.tier_audit(etier, Ef, list(range(0, len(Ef), max(1, len(Ef) // 30))))
        built[r] = (pn, ob, vp, etier)
        out["roots"][r] = {"S1": s1(pn, ob, vp, etier)}
        D = detector(etier, vp["Q"])
        dk = (D == 1)
        out["roots"][r]["S1"]["reading"] = (
            "VOLUME DETECTS" if (out["roots"][r]["S1"]["dbeta_rotation"]["observed"] > out["roots"][r]["S1"]["dbeta_rotation"]["p95"]
                                 and out["roots"][r]["S1"]["nw_detected"]["t_nw"] >= 2) else
            "VOLUME ANTI-DETECTS" if out["roots"][r]["S1"]["dbeta_rotation"]["observed"] < out["roots"][r]["S1"]["dbeta_rotation"]["p05"]
            else "NOTHING")
        del dk
    # ---- S2 on NQ
    pn, ob, vp, etier = built["NQ"]
    cl = M711.cost_line("NQ")
    usd, cost = float(cl["usd_per_point"]), float(cl["cost"])
    days, n = pn["days"], len(pn["days"])
    P("[D730] F_close (D724's) ...")
    lab = W.build_labels(data_root).reindex(days)
    fclose = lab["F_close"].to_numpy(float)
    ftier = C.tiers(fclose)
    C.tier_audit(ftier, fclose, list(range(0, n, max(1, n // 30))))
    trend = np.zeros(n, bool)
    years = np.array([d[:4] for d in days])
    for yv in np.unique(years):
        m = years == yv
        a = np.abs(ob["tot"][m])
        trend[np.flatnonzero(m)] = a >= np.quantile(a, 2 / 3)
    D = detector(etier, vp["Q"])
    rows_ok = np.isfinite(ob["z"])
    prec = []
    for j, m in enumerate(CLOCKS):
        right = trend & (np.sign(ob["z"][:, j]) == np.sign(ob["tot"]))
        on = (D[:, j] == 1) & rows_ok[:, j]
        prec.append({"t": T.hhmm(m), "precision_detected": float(right[on].mean()) if on.any() else None,
                     "precision_all": float(right[rows_ok[:, j]].mean())})
    out["roots"]["NQ"]["S1"]["oracle_precision"] = prec
    S2: dict[str, Any] = {}
    win = np.isfinite(ftier)
    for k in KS:
        first = entries(ob["z"], k)
        g, _ = gross_per_mnq(ob, first, usd)
        rows = np.arange(n)
        fcl = np.clip(first, 0, None)
        det_at = np.where(first >= 0, D[rows, fcl], 0.0) == 1
        q_all = np.where(first >= 0, 1.0, 0.0)
        q_det = np.where(det_at, 1.0, 0.0)
        q_det_f = np.where(det_at, np.where(ftier >= 2 / 3, 2.0, 1.0), 0.0)
        q_det_e = np.where(det_at, np.where(etier >= 0.9, 2.0, 1.0), 0.0)
        S2[str(k)] = {"i_all": book(q_all, g, cost, days), "ii_detected": book(q_det, g, cost, days),
                      "ii_detected_Fclose_window": book(q_det * win, g, cost, days),
                      "iii_detected_sized_Fclose": book(q_det_f * win, g, cost, days),
                      "iv_detected_sized_E": book(q_det_e, g, cost, days)}
        if k == 1.0:
            def filt_gain(Dm: np.ndarray) -> float:
                da = np.where(first >= 0, Dm[rows, fcl], 0.0) == 1
                a, b = (g - cost)[da & np.isfinite(g)], (g - cost)[(first >= 0) & np.isfinite(g)]
                return float(a.mean() - b.mean()) if len(a) else float("nan")
            obs_f = filt_gain(D)
            null_f = [filt_gain(detector(np.roll(etier, kk), np.roll(vp["Q"], kk, axis=0))) for kk in range(EDGE, n - EDGE)]
            S2["filter_gain_k1_rotation"] = rot(obs_f, null_f)
            base_sh = Z.sharpe(np.where(q_det * win > 0, g - cost, 0.0)[win])

            def size_gain(ft: np.ndarray) -> float:
                qq = np.where(det_at, np.where(ft >= 2 / 3, 2.0, 1.0), 0.0) * win
                return Z.sharpe(np.where(qq > 0, qq * (g - cost), 0.0)[win]) - base_sh
            fw = ftier[win]
            idx = np.flatnonzero(win)
            null_s = []
            for kk in range(EDGE, len(fw) - EDGE):
                ftr = np.full(n, np.nan)
                ftr[idx] = np.roll(fw, kk)
                null_s.append(size_gain(ftr))
            S2["size_gain_k1_rotation"] = rot(size_gain(ftier), null_s)
    out["roots"]["NQ"]["S2"] = S2
    s = out["roots"]["NQ"]["S1"]
    b1 = S2["1.0"]
    go = (s["reading"] == "VOLUME DETECTS"
          and (b1["ii_detected"]["mean_net_per_mnq"] or -1e9) > (b1["i_all"]["mean_net_per_mnq"] or 1e9)
          and (b1["ii_detected"]["mean_gross_per_mnq"] or -1e9) >= 2 * cost)
    out["SIZE_HELPS"] = bool(S2["size_gain_k1_rotation"]["observed"] > S2["size_gain_k1_rotation"]["p95"])
    out["GO"] = bool(go)
    out["wall_min"] = (time.time() - t0) / 60
    OUT.write_text(json.dumps(out, indent=1, default=Z._json) + "\n", encoding="utf-8", newline="\n")
    P(f"[D730] NQ {s['reading']}; YM {out['roots']['YM']['S1']['reading']}; RTY {out['roots']['RTY']['S1']['reading']}; "
      f"SIZE_HELPS {out['SIZE_HELPS']}; GO {go}; {out['wall_min']:.1f} min")
    return 0


# ================================================================================ self-test (synthetic only)
def selftest() -> int:
    fails: list[str] = []
    rng = np.random.default_rng(13)
    n, nc = 900, len(CLOCKS)
    X = rng.normal(0, 0.7, (n, nc))
    loud = rng.random(n) < 0.35
    etier = np.where(loud, rng.uniform(0.7, 1.0, n), rng.uniform(0, 0.65, n))
    Q = np.where(loud[:, None], rng.uniform(1.0, 1.5, (n, nc)), rng.uniform(0.5, 1.3, (n, nc)))
    Y = np.where(loud[:, None], 0.25 * X, 0.0 * X) + rng.normal(0, 0.4, (n, nc))
    D = detector(etier, Q)
    o = dbeta(D, X, Y)
    null = [dbeta(detector(np.roll(etier, k), np.roll(Q, k, axis=0)), X, Y) for k in range(EDGE, n - EDGE)]
    if not rot(o, null)["observed"] > rot(o, null)["p95"]:
        fails.append("a profile that marks the drift days did not beat its rotation")
    Y2 = 0.05 * X + rng.normal(0, 0.4, (n, nc))
    o2 = dbeta(D, X, Y2)
    n2 = [dbeta(detector(np.roll(etier, k), np.roll(Q, k, axis=0)), X, Y2) for k in range(EDGE, n - EDGE)]
    if rot(o2, n2)["rank"] > 0.99:
        fails.append("an unrelated profile sat above 99% of its rotation")
    # the volume audit on a synthetic panel, its canary, and Q = R / E
    rows = []
    for i in range(30):
        day = (pd.Timestamp("2019-01-01") + pd.Timedelta(days=i)).strftime("%Y-%m-%d")
        px = 100 + np.cumsum(rng.normal(0, 0.2, NMIN))
        vol = rng.integers(10, 200, NMIN)
        for m_ in range(NMIN):
            rows.append({"day": day, "hhmm": T.hhmm(m_), "contract": "NQH9", "open": px[m_], "high": px[m_] + 0.1,
                         "low": px[m_] - 0.1, "close": px[m_], "volume": int(vol[m_])})
    pn = T.panel_from_raw("NQ", pd.DataFrame(rows))
    vp = volume_panel(pn)
    smp = [(d, j) for d in range(len(pn["days"])) for j in (0, 4, 10)]
    volume_audit(pn, vp, smp)
    try:
        volume_audit(pn, vp, smp, shift=1)
        fails.append("the volume canary did not fire")
    except D730Error:
        pass
    # sign in money: q = 2 pays twice q = 1
    g = np.array([10.0, -6.0])
    b1 = book(np.array([1.0, 1.0]), g, 4.07, np.array(["2019-01-02", "2019-01-03"]))
    b2 = book(np.array([2.0, 2.0]), g, 4.07, np.array(["2019-01-02", "2019-01-03"]))
    if not math.isclose(b2["net_usd_a_year"], 2 * b1["net_usd_a_year"]):
        fails.append("sign in money: q = 2 does not pay twice q = 1")
    if fails:
        P("SELFTEST FAILED:", fails)
        return 1
    P("SELFTEST OK: a drift-marking profile beats its rotation, an unrelated one does not; the volume audit passes and "
      "its canary fires; q = 2 pays twice q = 1")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.run:
        if OUT.exists():
            raise D730Error(f"{OUT.name} exists: D730 runs once")
        return run(a.data_root)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
