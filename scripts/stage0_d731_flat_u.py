"""D731 Stage 0: the flatness of NQ's volume U -- the midday trough against the morning peak, relative to normal -- as a
dose-response on the continuation from the open. Spec: docs/decisions/D731-STAGE-0-PRE-REG-a-flatter-u-continues-more.md,
committed before this file existed.

    uv run python scripts/stage0_d731_flat_u.py --selftest
    uv run python scripts/stage0_d731_flat_u.py --run --data-root <checkout>/data      # once

NQ's objects are D727's; the volume and its normal curve are D730's `volume_panel` (both imported unchanged). Peak =
09:30-09:59, trough = 11:30 -> min(t, 13:30); F_t = (V_trough/V_peak) / (N_trough/N_peak) at t >= 12:00. Nothing dated
2024-01-01 or later is used.
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
import stage0_d730_volume_detector as V  # noqa: E402

OUT = REPO / "data" / "stage0_d731_flat_u.json"
FCLOCKS = [150, 180, 210, 240, 270, 300, 330]          # 12:00 .. 15:00
JIX = [T.CLOCKS.index(m) for m in FCLOCKS]
PEAK, TR0, TR1 = (0, 30), 120, 240                     # 09:30-09:59; trough 11:30 -> 13:29
J1330 = FCLOCKS.index(240)
KS = (0.5, 1.0, 1.5)
EDGE, NW = T.EDGE, T.NW_LAGS
P = Z.P


class D731Error(AssertionError):
    pass


# ================================================================================ flatness
def flatness(vp: dict[str, np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    """(F, raw) as [day, flat-clock] matrices."""
    Vv, Nm = vp["V"], vp["norm"]
    vpk, npk = Vv[:, PEAK[0]:PEAK[1]].sum(axis=1), Nm[:, PEAK[0]:PEAK[1]].sum(axis=1)
    F, raw = [], []
    for m in FCLOCKS:
        e = min(m, TR1)
        vt, nt = Vv[:, TR0:e].sum(axis=1), Nm[:, TR0:e].sum(axis=1)
        with np.errstate(invalid="ignore", divide="ignore"):
            raw.append(vt / vpk)
            F.append((vt / vpk) / (nt / npk))
    F, raw = np.column_stack(F), np.column_stack(raw)
    late = [j for j, m in enumerate(FCLOCKS) if m >= TR1]
    if not all(np.allclose(F[:, late[0]], F[:, j], equal_nan=True) for j in late):
        raise D731Error("right quantity: F moved after the trough closed at 13:30")
    return F, raw


def flat_audit(pn: dict[str, Any], F: np.ndarray, sample: list[tuple[int, int]], shift: int = 0) -> None:
    raw = pn["raw"]
    allpos = {d: i for i, d in enumerate(pn["all_days"])}
    for d, j in sample:
        day = pn["days"][d]
        i = allpos[day]
        prior = pn["all_days"][i - 20:i]
        e = min(FCLOCKS[j], TR1) + shift
        tw = {T.hhmm(k) for k in range(TR0, e)}
        pw = {T.hhmm(k) for k in range(*PEAK)}
        today, past = raw[raw["day"] == day], raw[raw["day"].isin(prior)]
        vt = float(today[today["hhmm"].isin(tw)]["volume"].sum())
        vpk = float(today[today["hhmm"].isin(pw)]["volume"].sum())
        nt = float(past[past["hhmm"].isin(tw)]["volume"].sum()) / 20.0
        npk = float(past[past["hhmm"].isin(pw)]["volume"].sum()) / 20.0
        want = (vt / vpk) / (nt / npk)
        if not math.isclose(want, F[d, j], rel_tol=1e-9):
            raise D731Error(f"lag: flatness at {day} {T.hhmm(FCLOCKS[j])} reads a bar at or after t")


# ================================================================================ statistics
def stack(X: np.ndarray, Y: np.ndarray, Fc: np.ndarray, mask: np.ndarray | None = None) -> tuple[np.ndarray, ...]:
    m = np.isfinite(X) & np.isfinite(Y) & np.isfinite(Fc)
    if mask is not None:
        m &= mask
    return X[m], Y[m], Fc[m], np.flatnonzero(m.ravel())


def gamma(X: np.ndarray, Y: np.ndarray, Fc: np.ndarray, mask: np.ndarray | None = None, with_t: bool = False) -> dict[str, float]:
    x, y, f, _ = stack(X, Y, Fc, mask)
    if len(x) < 50:
        return {"gamma": float("nan"), "t_nw": float("nan"), "n": int(len(x))}
    Xm = np.column_stack([np.ones(len(x)), x, x * (f - 0.5)])
    c, *_ = np.linalg.lstsq(Xm, y, rcond=None)
    out = {"beta": float(c[1]), "gamma": float(c[2]), "n": int(len(x))}
    if with_t:
        e = y - Xm @ c
        XtX_inv = np.linalg.inv(Xm.T @ Xm)
        g = Xm * e[:, None]
        S = g.T @ g
        for L in range(1, NW + 1):
            w = 1 - L / (NW + 1)
            G = g[L:].T @ g[:-L]
            S += w * (G + G.T)
        V_ = XtX_inv @ S @ XtX_inv
        out["t_nw"] = float(c[2] / math.sqrt(V_[2, 2])) if V_[2, 2] > 0 else float("nan")
    return out


def slope(x: np.ndarray, y: np.ndarray, m: np.ndarray) -> float:
    ok = m & np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 30:
        return float("nan")
    xs, ys = x[ok], y[ok]
    xc = xs - xs.mean()
    return float((xc * (ys - ys.mean())).sum() / (xc * xc).sum())


def terciles(X: np.ndarray, Y: np.ndarray, f: np.ndarray) -> dict[str, float]:
    return {nm: slope(X, Y, np.isfinite(f) & (f >= lo) & (f < hi))
            for nm, lo, hi in (("low", 0, 1 / 3), ("mid", 1 / 3, 2 / 3), ("high", 2 / 3, 1.01))}


def rot(obs: float, null: list[float]) -> dict[str, float]:
    a = np.array(null, float)
    a = a[np.isfinite(a)]
    return {"observed": obs, "offsets": int(len(a)), "p05": float(np.quantile(a, 0.05)), "p50": float(np.median(a)),
            "p95": float(np.quantile(a, 0.95)), "p95_se": 0.0, "rank": float((a < obs).mean())}


def tiers_by_clock(M: np.ndarray, audit: bool = True) -> np.ndarray:
    import stage0_d671_break_construction as C
    out = np.full(M.shape, np.nan)
    for j in range(M.shape[1]):
        col = np.where(np.isfinite(M[:, j]), M[:, j], np.nan)
        out[:, j] = C.tiers(col)
        if audit:
            C.tier_audit(out[:, j], col, list(range(0, len(col), max(1, len(col) // 25))))
    return out


def s1(pn: dict[str, Any], ob: dict[str, np.ndarray], vp: dict[str, np.ndarray]) -> tuple[dict[str, Any], np.ndarray]:
    X, Y = ob["x"][:, JIX], ob["y"][:, JIX]
    F, raw = flatness(vp)
    f = tiers_by_clock(F)
    fr = tiers_by_clock(raw, audit=False)
    n = len(pn["days"])
    g = gamma(X, Y, f, with_t=True)
    null = [gamma(X, Y, np.roll(f, k, axis=0))["gamma"] for k in range(EDGE, n - EDGE)]
    pre = ~vp["pre_roll"][:, None] & np.ones_like(f, bool)
    res = {"gamma": g, "rotation": rot(g["gamma"], null), "gamma_excl_pre_roll": gamma(X, Y, f, pre)["gamma"],
           "beta_by_flat_tercile": terciles(X, Y, f), "beta_by_raw_ratio_tercile": terciles(X, Y, fr),
           "by_clock": [{"t": T.hhmm(m), **terciles(X[:, [j]], Y[:, [j]], f[:, [j]])} for j, m in enumerate(FCLOCKS)],
           "F_median_by_clock": [float(np.nanmedian(F[:, j])) for j in range(len(FCLOCKS))]}
    tb = res["beta_by_flat_tercile"]
    det = (g["gamma"] > res["rotation"]["p95"] and (g.get("t_nw") or 0) >= 2 and tb["high"] > tb["mid"] > tb["low"])
    res["reading"] = ("FLATNESS DETECTS" if det else
                      "FLATNESS ANTI-DETECTS" if g["gamma"] < res["rotation"]["p05"] else "NOTHING")
    return res, f


def book(q: np.ndarray, g: np.ndarray, cost: float, days: np.ndarray) -> tuple[dict[str, Any], np.ndarray]:
    tr = (q > 0) & np.isfinite(g)
    net = np.where(tr, q * (g - cost), 0.0)
    gross = np.where(tr, q * g, 0.0)
    years = np.array([s[:4] for s in days])
    by = {y: float(net[years == y].sum()) for y in np.unique(years)}
    tot = sum(by.values())
    per = (g - cost)[tr]
    from backtest_framework.validation.hurdle_p import p3
    out = {"trades": int(tr.sum()), "contracts": float(q[tr].sum()),
           "mean_gross_per_mnq": float(g[tr].mean()) if tr.any() else None,
           "mean_net_per_mnq": float(per.mean()) if tr.any() else None,
           "median_gross_per_mnq": float(np.median(g[tr])) if tr.any() else None,
           "net_sharpe": Z.sharpe(net), "net_sortino": Z.sortino(net), "gross_sharpe": Z.sharpe(gross),
           "gross_sortino": Z.sortino(gross), "max_dd": Z.max_dd(net),
           "p3a_50k": p3(net, account=50_000.0)["p3a_breaches_per_year"],
           "p3a_150k": p3(net, account=150_000.0)["p3a_breaches_per_year"],
           "per_mnq_distribution": Z.trade_dist(per) if tr.any() else {"trades": 0}, "net_by_year": by,
           "years_positive": int(sum(v > 0 for v in by.values())), "years": len(by),
           "largest_year_share": float(max(by.values()) / tot) if tot > 0 else None}
    return out, net


# ================================================================================ the run
def run(data_root: Path) -> int:
    t0 = time.time()
    import stage1_d711_f2_mechanism as M711
    ka = json.loads((REPO / "data" / "stage0_d727_trend_curve.json").read_text(encoding="utf-8"))["roots"]
    out: dict[str, Any] = {"spec": "D731-STAGE-0-PRE-REG-a-flatter-u-continues-more.md",
                           "seal": f"nothing on or after {Z.CUT24}", "roots": {}}
    rng = np.random.default_rng(731)
    keep = {}
    for r in ("NQ", "YM", "RTY"):
        P(f"[D731] {r} ...")
        pn = T.load_root(r, data_root)
        ob = T.objects(pn)
        if len(pn["days"]) != ka[r]["days"] or not math.isclose(T.beta_nw(ob["x"][:, 0], ob["y"][:, 0])["beta"],
                                                                ka[r]["clocks"][0]["beta"], rel_tol=0, abs_tol=1e-12):
            raise D731Error(f"{r}'s objects are not D727's")
        vp = V.volume_panel(pn)
        F, _ = flatness(vp)
        smp = [(int(rng.integers(0, len(pn["days"]))), int(rng.integers(0, 3))) for _ in range(25)]
        smp = [(d, j) for d, j in smp if np.isfinite(F[d, j])]
        flat_audit(pn, F, smp)
        try:
            flat_audit(pn, F, smp, shift=1)
        except D731Error:
            pass
        else:
            raise D731Error(f"{r}: the flatness canary did not fire")
        res, f = s1(pn, ob, vp)
        out["roots"][r] = {"S1": res}
        keep[r] = (pn, ob, f)
    pn, ob, f = keep["NQ"]
    cl = M711.cost_line("NQ")
    usd, cost = float(cl["usd_per_point"]), float(cl["cost"])
    days, n = pn["days"], len(pn["days"])
    j = T.CLOCKS.index(240)
    f13 = f[:, J1330]
    S2: dict[str, Any] = {}
    nets = {}
    for k in KS:
        side = np.where(np.abs(ob["z"][:, j]) >= k, np.sign(ob["z"][:, j]), 0.0)
        g = np.where(side != 0, side * (ob["close"] - ob["Pt"][:, j]) * usd, np.nan)
        qa = np.where(side != 0, 1.0, 0.0)
        qb = np.where((side != 0) & (f13 >= 2 / 3), 1.0, 0.0)
        qc = np.where(side != 0, np.where(f13 >= 2 / 3, 2.0, np.where(f13 >= 1 / 3, 1.0, 0.0)), 0.0)
        qc = np.where(np.isfinite(f13), qc, 0.0)
        S2[str(k)] = {}
        for nm, q in (("a_all", qa), ("b_flat_top_third", qb), ("c_flat_sized", qc)):
            S2[str(k)][nm], nets[(k, nm)] = book(q, g, cost, days)
        if k == 1.0:
            def gain(ft: np.ndarray) -> float:
                b_ = (side != 0) & (ft >= 2 / 3) & np.isfinite(g)
                a_ = (side != 0) & np.isfinite(g)
                return float((g[b_] - cost).mean() - (g[a_] - cost).mean()) if b_.any() else float("nan")
            S2["flat_filter_gain_k1_rotation"] = rot(gain(f13), [gain(np.roll(f13, kk)) for kk in range(EDGE, n - EDGE)])
    P("[D731] ledger line (the arm, NQ F2) ...")
    arm, _ = Z.build_arm()
    f2, _ = Z.build_f2()
    cal = pd.Index(days)
    arm_d = arm.groupby("day")["net1"].sum().reindex(cal).fillna(0.0).to_numpy()
    f2_d = f2.groupby("day")["net1"].sum().reindex(cal).fillna(0.0).to_numpy()
    b = nets[(1.0, "b_flat_top_third")]
    S2["ledger_rho_k1_b"] = {"macd_arm": float(np.corrcoef(b, arm_d)[0, 1]), "nq_f2": float(np.corrcoef(b, f2_d)[0, 1])}
    out["roots"]["NQ"]["S2"] = S2
    s = out["roots"]["NQ"]["S1"]
    b1 = S2["1.0"]
    out["GO"] = bool(s["reading"] == "FLATNESS DETECTS"
                     and (b1["b_flat_top_third"]["mean_net_per_mnq"] or -1e9) > (b1["a_all"]["mean_net_per_mnq"] or 1e9)
                     and (b1["b_flat_top_third"]["mean_gross_per_mnq"] or -1e9) >= 2 * cost)
    out["wall_min"] = (time.time() - t0) / 60
    OUT.write_text(json.dumps(out, indent=1, default=Z._json) + "\n", encoding="utf-8", newline="\n")
    P(f"[D731] NQ {s['reading']}; YM {out['roots']['YM']['S1']['reading']}; RTY {out['roots']['RTY']['S1']['reading']}; "
      f"GO {out['GO']}; {out['wall_min']:.1f} min")
    return 0


# ================================================================================ self-test (synthetic only)
def selftest() -> int:
    fails: list[str] = []
    rng = np.random.default_rng(17)
    n, nc = 900, len(FCLOCKS)
    X = rng.normal(0, 0.6, (n, nc))
    fl = rng.uniform(0, 1, n)
    f = np.repeat(fl[:, None], nc, axis=1)
    Y = (0.02 + 0.2 * (fl[:, None] - 0.5)) * X + rng.normal(0, 0.3, (n, nc))
    g = gamma(X, Y, f, with_t=True)
    null = [gamma(X, Y, np.roll(f, k, axis=0))["gamma"] for k in range(EDGE, n - EDGE)]
    r_ = rot(g["gamma"], null)
    if not (r_["observed"] > r_["p95"] and g["t_nw"] >= 2):
        fails.append("a flatness that raises continuation did not read as detecting")
    Y2 = 0.03 * X + rng.normal(0, 0.3, (n, nc))
    g2 = gamma(X, Y2, f)
    n2 = [gamma(X, Y2, np.roll(f, k, axis=0))["gamma"] for k in range(EDGE, n - EDGE)]
    if rot(g2["gamma"], n2)["rank"] > 0.99:
        fails.append("an unrelated flatness sat above 99% of its rotation")
    # the flatness audit on a synthetic panel, its canary, and F constant after 13:30
    rows = []
    for i in range(30):
        day = (pd.Timestamp("2019-01-01") + pd.Timedelta(days=i)).strftime("%Y-%m-%d")
        px = 100 + np.cumsum(rng.normal(0, 0.2, T.NMIN))
        vol = rng.integers(10, 300, T.NMIN)
        for m_ in range(T.NMIN):
            rows.append({"day": day, "hhmm": T.hhmm(m_), "contract": "NQH9", "open": px[m_], "high": px[m_] + 0.1,
                         "low": px[m_] - 0.1, "close": px[m_], "volume": int(vol[m_])})
    pn = T.panel_from_raw("NQ", pd.DataFrame(rows))
    vp = V.volume_panel(pn)
    F, _ = flatness(vp)
    smp = [(d, j) for d in range(len(pn["days"])) for j in (0, 1, 2, 4)]
    flat_audit(pn, F, smp)
    try:
        flat_audit(pn, F, [(d, j) for d, j in smp if j < 3], shift=1)
        fails.append("the flatness canary did not fire")
    except D731Error:
        pass
    # sign in money
    gg = np.array([10.0, -6.0])
    d2 = np.array(["2019-01-02", "2019-01-03"])
    _, n1 = book(np.array([1.0, 1.0]), gg, 4.07, d2)
    _, n2_ = book(np.array([2.0, 2.0]), gg, 4.07, d2)
    _, n0 = book(np.array([0.0, 0.0]), gg, 4.07, d2)
    if not (np.allclose(n2_, 2 * n1) and np.all(n0 == 0)):
        fails.append("sign in money")
    if fails:
        P("SELFTEST FAILED:", fails)
        return 1
    P("SELFTEST OK: a continuation-raising flatness detects against its rotation, an unrelated one does not; the "
      "flatness audit passes and its canary fires; F is constant after 13:30; q = 2 pays twice q = 1, q = 0 nothing")
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
            raise D731Error(f"{OUT.name} exists: D731 runs once")
        return run(a.data_root)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
