"""D727 Stage 0: the trend detection curve. Spec: docs/decisions/D727-STAGE-0-PRE-REG-the-trend-detection-curve.md,
committed before this file existed.

    uv run python scripts/stage0_d727_trend_curve.py --selftest
    uv run python scripts/stage0_d727_trend_curve.py --run --data-root <checkout>/data      # once

NQ (primary), YM and RTY (the declared transfer check), day sessions 2016-01-04 -> 2023-12-29 from fut_{root}_rth_1m.
Price at t = the close of the bar starting t-1; O = the 09:30 bar's open; C = the 15:59 bar's close; sigma_oc = the RMS
of the prior 20 sessions' open-to-close moves. beta_t = the OLS slope (with intercept) of y_t = (C - P_t)/sigma_oc on
x_t = (P_t - O)/sigma_oc, against the enumerated rotation of y across days. Nothing dated 2024-01-01 or later is used.
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

OUT = REPO / "data" / "stage0_d727_trend_curve.json"
ROOTS = ("NQ", "YM", "RTY")
LO, HI = "2016-01-04", Z.HI
NMIN, MIN_BARS, EDGE, NW_LAGS = 390, 380, 20, 5
CLOCKS = list(range(30, 331, 30))           # minutes after 09:30: 10:00 .. 15:00
KS = (0.5, 1.0, 1.5)
ZBINS = ((0, 0.5), (0.5, 1.0), (1.0, 1.5), (1.5, np.inf))
P = Z.P


class D727Error(AssertionError):
    pass


def hhmm(m: int) -> str:
    t = 9 * 60 + 30 + m
    return f"{t // 60:02d}:{t % 60:02d}"


# ================================================================================ panels
def load_root(root: str, data_root: Path) -> dict[str, Any]:
    b = pd.read_csv(data_root / "fixtures" / f"fut_{root}_rth_1m.csv.gz", encoding="utf-8",
                    dtype={"day": str, "hhmm": str, "contract": str})
    b = b[(b["day"] >= LO) & (b["day"] <= HI)]
    Z.no_session_after(b["day"].unique(), f"{root}'s one-minute bars")
    return panel_from_raw(root, b)


def panel_from_raw(root: str, b: pd.DataFrame) -> dict[str, Any]:
    mins = [hhmm(m) for m in range(NMIN)]
    b = b[b["hhmm"].isin(mins)]
    nb = b.groupby("day").size()
    days = np.array(sorted(nb.index[nb >= MIN_BARS]))
    b = b[b["day"].isin(days)]
    Cp = b.pivot(index="day", columns="hhmm", values="close").reindex(index=days, columns=mins).to_numpy(float)
    Op = b.pivot(index="day", columns="hhmm", values="open").reindex(index=days, columns=mins).to_numpy(float)
    C = pd.DataFrame(Cp).ffill(axis=1).to_numpy(float)
    O = np.where(np.isfinite(Op[:, 0]), Op[:, 0], C[:, 0])
    con = b.groupby("day")["contract"].agg(lambda s: s.value_counts().index[0]).reindex(days).to_numpy(str)
    roll = np.r_[True, con[1:] != con[:-1]]
    oc = C[:, -1] - O
    soc = np.sqrt(pd.Series(oc * oc).shift(1).rolling(20, min_periods=20).mean().to_numpy(float))
    keep = ~roll & np.isfinite(soc) & (soc > 0)
    return {"root": root, "days": days[keep], "C": C[keep], "O": O[keep], "soc": soc[keep],
            "raw": b, "all_days": days, "all_O": O, "all_C_last": C[:, -1]}


def objects(pn: dict[str, Any]) -> dict[str, np.ndarray]:
    C, O, s = pn["C"], pn["O"], pn["soc"]
    Pt = np.column_stack([C[:, m - 1] for m in CLOCKS])          # m >= 30: never a wrapped index
    close = C[:, NMIN - 1]
    x = (Pt - O[:, None]) / s[:, None]
    y = (close[:, None] - Pt) / s[:, None]
    u = np.array(CLOCKS) / NMIN
    z = x / np.sqrt(u)[None, :]
    tot = (close - O) / s
    if not np.allclose(x + y, tot[:, None], atol=1e-9):
        raise D727Error("right quantity: x + y is not the day's open-to-close move")
    return {"Pt": Pt, "close": close, "x": x, "y": y, "z": z, "tot": tot}


def lag_audit(pn: dict[str, Any], ob: dict[str, np.ndarray], sample: list[tuple[int, int]], shift: int = 0) -> None:
    """Second implementation from the raw rows: P_t = the close of the bar starting t-1 (shift = 1 reads the t bar:
    the canary); sigma_oc from the prior 20 sessions' raw open and last close."""
    raw = pn["raw"]
    pos = {d: i for i, d in enumerate(pn["all_days"])}
    for d, j in sample:
        day = pn["days"][d]
        r = raw[raw["day"] == day].set_index("hhmm")
        m = CLOCKS[j]
        bar = hhmm(m - 1 + shift)
        if bar not in r.index:
            continue
        want = float(r.at[bar, "close"])
        if not math.isclose(want, ob["Pt"][d, j], rel_tol=0, abs_tol=1e-9):
            raise D727Error(f"lag: P_t at {day} {hhmm(m)} is not the close of the bar starting t-1")
        if shift == 0:
            i = pos[day]
            oc = pn["all_C_last"][i - 20:i] - pn["all_O"][i - 20:i]
            if not math.isclose(math.sqrt(float(np.mean(oc * oc))), pn["soc"][d], rel_tol=1e-12):
                raise D727Error(f"lag: sigma_oc at {day} is not the prior 20 sessions'")


# ================================================================================ statistics
def beta_nw(x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    n = len(x)
    xc = x - x.mean()
    b = float((xc * (y - y.mean())).sum() / (xc * xc).sum())
    e = (y - y.mean()) - b * xc
    g = xc * e
    S = float((g * g).sum())
    for L in range(1, NW_LAGS + 1):
        S += 2 * (1 - L / (NW_LAGS + 1)) * float((g[L:] * g[:-L]).sum())
    se = math.sqrt(max(S, 0.0)) / float((xc * xc).sum())
    return {"beta": b, "t_nw": b / se if se > 0 else float("nan"), "n": n}


def rotation(x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    xc, yc = x - x.mean(), y - y.mean()
    sxx = float((xc * xc).sum())
    obs = float((xc * yc).sum() / sxx)
    if not math.isclose(float((xc * np.roll(yc, 0)).sum() / sxx), obs, rel_tol=0, abs_tol=1e-12):
        raise D727Error("rotation: offset 0 does not reproduce beta")
    null = np.array([float((xc * np.roll(yc, k)).sum() / sxx) for k in range(EDGE, len(x) - EDGE)])
    return {"observed": obs, "offsets": int(len(null)), "p05": float(np.quantile(null, 0.05)),
            "p50": float(np.median(null)), "p95": float(np.quantile(null, 0.95)), "p95_se": 0.0,
            "rank": float((null < obs).mean())}


def bins(x: np.ndarray, y: np.ndarray, z: np.ndarray) -> list[dict[str, Any]]:
    out = []
    for lo, hi in ZBINS:
        m = np.isfinite(z) & (np.abs(z) >= lo) & (np.abs(z) < hi) & (x != 0)
        sy = np.sign(x[m]) * y[m]
        out.append({"abs_z": [lo, None if hi == np.inf else hi], "days": int(m.sum()),
                    "p_continue": float((sy > 0).mean()) if m.any() else None,
                    "mean_signed_rest_sigma": float(sy.mean()) if m.any() else None})
    return out


def money_book(side: np.ndarray, entry: np.ndarray, close: np.ndarray, usd_pt: float, cost: float,
               days: np.ndarray) -> dict[str, Any]:
    tr = (side != 0) & np.isfinite(entry)
    g = np.where(tr, side * (close - entry) * usd_pt, np.nan)
    net = np.where(tr, g - cost, 0.0)
    gross = np.where(tr, g, 0.0)
    years = np.array([s[:4] for s in days])
    by = {y: float(net[years == y].sum()) for y in np.unique(years)}
    tot = sum(by.values())
    nt = g[tr] - cost
    return {"trades": int(tr.sum()), "mean_gross": float(np.nanmean(g)) if tr.any() else None,
            "median_gross": float(np.nanmedian(g)) if tr.any() else None,
            "mean_net": float(nt.mean()) if tr.any() else None,
            "net_sharpe": Z.sharpe(net), "net_sortino": Z.sortino(net), "gross_sharpe": Z.sharpe(gross),
            "gross_sortino": Z.sortino(gross), "max_dd": Z.max_dd(net),
            "net_distribution": Z.trade_dist(nt) if tr.any() else {"trades": 0}, "net_by_year": by,
            "years_positive": int(sum(v > 0 for v in by.values())), "years": len(by),
            "largest_year_share": float(max(by.values()) / tot) if tot > 0 else None}


# ================================================================================ per root
def study(root: str, data_root: Path, cl: dict[str, float]) -> dict[str, Any]:
    pn = load_root(root, data_root)
    ob = objects(pn)
    rng = np.random.default_rng(727)
    sample = [(int(rng.integers(0, len(pn["days"]))), int(rng.integers(0, len(CLOCKS)))) for _ in range(40)]
    sample += [(int(rng.integers(0, len(pn["days"]))), 0) for _ in range(5)]
    lag_audit(pn, ob, sample)
    try:
        lag_audit(pn, ob, sample, shift=1)
    except D727Error:
        pass
    else:
        raise D727Error(f"{root}: the lag canary did not fire")
    x, y, z, tot = ob["x"], ob["y"], ob["z"], ob["tot"]
    days = pn["days"]
    years = np.array([d[:4] for d in days])
    trend = np.zeros(len(days), bool)
    for yv in np.unique(years):
        m = years == yv
        a = np.abs(tot[m])
        trend[np.flatnonzero(m)] = a >= np.quantile(a, 2 / 3)
    res: dict[str, Any] = {"days": int(len(days)), "window": [str(days[0]), str(days[-1])], "cost_usd": cl["cost"],
                           "usd_per_point": cl["usd_per_point"], "trend_day_share": float(trend.mean()), "clocks": []}
    for j, m in enumerate(CLOCKS):
        bn = beta_nw(x[:, j], y[:, j])
        rot = rotation(x[:, j], y[:, j])
        cont = rot["observed"] > rot["p95"] and bn["t_nw"] >= 2
        rev = rot["observed"] < rot["p05"] and bn["t_nw"] <= -2
        st = np.sign(tot)
        rem = float(np.mean(st[trend] * y[trend, j]) / np.mean(np.abs(tot[trend])))
        det = {}
        for k in KS:
            hit = np.abs(z[:, j]) >= k
            right = hit & trend & (np.sign(z[:, j]) == st)
            det[str(k)] = {"flagged": int(hit.sum()), "precision": float(right.sum() / hit.sum()) if hit.any() else None,
                           "base_rate_trend_day": float(trend.mean()),
                           "recall": float(right.sum() / trend.sum())}
        res["clocks"].append({"t": hhmm(m), **bn, "rotation": rot,
                              "reading": "CONTINUATION" if cont else "REVERSAL" if rev else "NONE",
                              "bins": bins(x[:, j], y[:, j], z[:, j]),
                              "trend_day_share_of_move_remaining": rem, "detection": det})
    books: dict[str, Any] = {"per_clock": {}, "first_crossing": {}, "ceiling_first_crossing": {}}
    for k in KS:
        for j, m in enumerate(CLOCKS):
            side = np.where(np.abs(z[:, j]) >= k, np.sign(z[:, j]), 0.0)
            books["per_clock"][f"{hhmm(m)}_k{k}"] = money_book(side, ob["Pt"][:, j], ob["close"], cl["usd_per_point"],
                                                               cl["cost"], days)
        hit = np.abs(z) >= k
        first = np.where(hit.any(axis=1), hit.argmax(axis=1), -1)
        rows = np.arange(len(days))
        side = np.where(first >= 0, np.sign(z[rows, np.clip(first, 0, None)]), 0.0)
        entry = np.where(first >= 0, ob["Pt"][rows, np.clip(first, 0, None)], np.nan)
        books["first_crossing"][str(k)] = money_book(side, entry, ob["close"], cl["usd_per_point"], cl["cost"], days)
        books["first_crossing"][str(k)]["entry_clock_counts"] = {hhmm(CLOCKS[j]): int((first == j).sum())
                                                                 for j in range(len(CLOCKS))}
        oracle = np.where(trend & (side == np.sign(tot)), side, 0.0)
        books["ceiling_first_crossing"][str(k)] = money_book(oracle, entry, ob["close"], cl["usd_per_point"],
                                                             cl["cost"], days)
    res["books"] = books
    return res


def readings(out: dict[str, Any]) -> None:
    nq = out["roots"]["NQ"]["clocks"]
    cont = [c["reading"] == "CONTINUATION" for c in nq]
    tstar = None
    for j in range(len(cont) - 1):
        if cont[j] and cont[j + 1]:
            tstar = nq[j]["t"]
            break
    out["NQ_curve"] = f"RECOGNISABLE FROM {tstar}" if tstar else "NOT RECOGNISABLE"
    cj = [j for j, c in enumerate(cont) if c]
    tr = {}
    for r in ("YM", "RTY"):
        cl = out["roots"][r]["clocks"]
        tr[r] = {nq[j]["t"]: {"same_sign": bool(np.sign(cl[j]["beta"]) == np.sign(nq[j]["beta"])),
                              "rank": cl[j]["rotation"]["rank"]} for j in range(len(nq))}
    out["transfer_per_clock"] = tr
    if cj:
        ok = any(sum(tr[r][nq[j]["t"]]["same_sign"] and tr[r][nq[j]["t"]]["rank"] >= 0.90 for j in cj) > len(cj) / 2
                 for r in ("YM", "RTY"))
        out["transfer"] = "TRANSFERS" if ok else "DOES NOT TRANSFER"
    else:
        out["transfer"] = "n/a (no NQ CONTINUATION clock)"
    cost = out["roots"]["NQ"]["cost_usd"]
    pays = any((b["mean_gross"] or -1e9) >= 2 * cost and (b["mean_net"] or -1e9) > 0
               for b in out["roots"]["NQ"]["books"]["first_crossing"].values())
    out["GO"] = bool(tstar and out["transfer"] == "TRANSFERS" and pays)
    out["NQ_practical_book_pays_2c"] = bool(pays)


def run(data_root: Path) -> int:
    t0 = time.time()
    import stage1_d711_f2_mechanism as M711
    out: dict[str, Any] = {"spec": "D727-STAGE-0-PRE-REG-the-trend-detection-curve.md",
                           "seal": f"nothing on or after {Z.CUT24}", "roots": {}}
    for r in ROOTS:
        P(f"[D727] {r} ...")
        cl = M711.cost_line(r)
        out["roots"][r] = study(r, data_root, {"cost": float(cl["cost"]), "usd_per_point": float(cl["usd_per_point"])})
    readings(out)
    out["wall_min"] = (time.time() - t0) / 60
    OUT.write_text(json.dumps(out, indent=1, default=Z._json) + "\n", encoding="utf-8", newline="\n")
    P(f"[D727] NQ {out['NQ_curve']}; transfer {out['transfer']}; pays {out['NQ_practical_book_pays_2c']}; "
      f"GO {out['GO']}; {out['wall_min']:.1f} min")
    return 0


# ================================================================================ self-test (synthetic only)
def selftest() -> int:
    fails: list[str] = []
    rng = np.random.default_rng(9)
    n = 600

    def synth(drift_sd: float) -> dict[str, Any]:
        mu = rng.normal(0, drift_sd, n)                        # a day-level drift per minute (the trend day)
        r = rng.normal(0, 0.5, (n, NMIN)) + mu[:, None]
        C = 1000 + np.cumsum(r, axis=1)
        O = C[:, 0] - r[:, 0]
        return {"C": C, "O": O, "soc": np.full(n, 10.0), "r": r}

    trend, walk = synth(0.03), synth(0.0)
    for nm, s, want in (("drift", trend, True), ("random walk", walk, False)):
        ob = objects(s)
        rot = rotation(ob["x"][:, 6], ob["y"][:, 6])
        if (rot["observed"] > rot["p95"]) != want:
            fails.append(f"{nm}: rotation verdict {rot['observed']:.3f} vs p95 {rot['p95']:.3f}")
    # a within-day permutation keeps each day's drift in both halves, so it cannot see the trend day
    ob = objects(trend)
    perm = []
    for _ in range(20):
        rp = np.array([rng.permutation(row) for row in trend["r"]])
        Cp = trend["O"][:, None] + np.cumsum(rp, axis=1)
        perm.append(rotation(*(lambda o: (o["x"][:, 6], o["y"][:, 6]))(objects({"C": Cp, "O": trend["O"],
                                                                                 "soc": trend["soc"]})))["observed"])
    if not np.mean(perm) > 0.5 * rotation(ob["x"][:, 6], ob["y"][:, 6])["observed"]:
        fails.append("the within-day permutation did not reproduce the drift (the documentation case)")
    # the lag audit on a real (synthetic) panel: it passes, its canary fires, and it catches a wrapped price index
    rows = []
    for i in range(25):
        day = (pd.Timestamp("2019-01-01") + pd.Timedelta(days=i)).strftime("%Y-%m-%d")
        px = 100 + np.cumsum(rng.normal(0, 0.2, NMIN))
        for m_ in range(NMIN):
            rows.append({"day": day, "hhmm": hhmm(m_), "contract": "NQH9", "open": px[m_] - 0.05, "high": px[m_] + 0.1,
                         "low": px[m_] - 0.1, "close": px[m_], "volume": 10})
    pn = panel_from_raw("NQ", pd.DataFrame(rows))
    ob = objects(pn)
    smp = [(d, j) for d in range(len(pn["days"])) for j in (0, 5, 10)]
    lag_audit(pn, ob, smp)
    try:
        lag_audit(pn, ob, smp, shift=1)
        fails.append("the lag canary did not fire")
    except D727Error:
        pass
    wrapped = dict(ob)
    wrapped["Pt"] = ob["Pt"].copy()
    wrapped["Pt"][:, 0] = pn["C"][:, -1]          # D724's bug: a negative index wraps to the 15:59 close
    try:
        lag_audit(pn, wrapped, smp)
        fails.append("the lag audit missed a wrapped index")
    except D727Error:
        pass
    # sign in money
    side = np.array([1.0, -1.0])
    b = money_book(side, np.array([100.0, 100.0]), np.array([101.0, 99.0]), 2.0, 4.07, np.array(["2019-01-02", "2019-01-03"]))
    if not (math.isclose(b["mean_gross"], 2.0) and math.isclose(b["mean_net"], 2.0 - 4.07)):
        fails.append("sign in money")
    # right quantity: a broken y (from the open) breaks the x + y identity
    try:
        bad = dict(trend)
        bad["C"] = trend["C"].copy()
        o = objects(bad)
        o["y"] = (o["close"][:, None] - bad["O"][:, None]) / 10.0
        if np.allclose(o["x"] + o["y"], o["tot"][:, None]):
            fails.append("the x + y identity did not separate y from the open")
    except D727Error:
        pass
    if fails:
        P("SELFTEST FAILED:", fails)
        return 1
    P("SELFTEST OK: a day-drift series beats its cross-day rotation and a random walk does not; a within-day permutation "
      "reproduces the drift (why it is not the null); no clock wraps; sign in money; the x + y identity holds")
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
            raise D727Error(f"{OUT.name} exists: D727 runs once")
        return run(a.data_root)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
