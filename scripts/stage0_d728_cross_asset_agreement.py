"""D728 Stage 0: does cross-asset agreement sharpen NQ's continuation from the open (D727), and does NQ's move explain
why the Dow does not continue? Spec: docs/decisions/D728-STAGE-0-PRE-REG-does-cross-asset-agreement-sharpen-nq.md,
committed before this file existed.

    uv run python scripts/stage0_d728_cross_asset_agreement.py --selftest
    uv run python scripts/stage0_d728_cross_asset_agreement.py --run --data-root <checkout>/data     # once

NQ = D727's objects, unchanged (its functions). The agreement assets (ES, YM, RTY, ZN, 6E) come from fut_day1m (bar b =
minute 09:00 + b ET), read with a filter to 2016-01-04 -> 2023-12-29. Asset open = the 09:30 bar's open; price at t =
the close of the bar starting t-1; sigma_oc = the RMS of the prior 20 sessions' 09:30 -> 15:59 moves. Nothing dated
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

OUT = REPO / "data" / "stage0_d728_cross_asset.json"
ASSETS = ("ES", "YM", "RTY", "ZN", "6E")
GROUPS = {"G_eq": ("ES", "YM", "RTY"), "G_rates": ("ZN",), "G_usd": ("6E",)}
NB, B0930, ZMIN = 420, 30, 0.5
CLOCKS = T.CLOCKS
EDGE = T.EDGE
P = Z.P


class D728Error(AssertionError):
    pass


# ================================================================================ asset panels (fut_day1m)
def load_day1m(data_root: Path) -> pd.DataFrame:
    import pyarrow.parquet as pq
    t = pq.read_table(data_root / "fixtures" / "fut_day1m.parquet",
                      filters=[("root", "in", list(ASSETS)), ("day", ">=", T.LO), ("day", "<=", T.HI)],
                      columns=["root", "day", "bar", "open", "close", "same_front", "present"])
    d = t.to_pandas()
    Z.no_session_after(d["day"].unique(), "fut_day1m")
    return d


def asset_panel(raw: pd.DataFrame, root: str) -> dict[str, Any]:
    x = raw[raw["root"] == root]
    ok_day = x.groupby("day").agg(sf=("same_front", "all"), pr=("present", "all"))
    good = ok_day.index[ok_day["sf"] & ok_day["pr"]].to_numpy(str)
    x = x[x["day"].isin(good)]
    days = np.array(sorted(x["day"].unique()))
    Cp = x.pivot(index="day", columns="bar", values="close").reindex(index=days, columns=range(NB)).to_numpy(float)
    Op = x.pivot(index="day", columns="bar", values="open").reindex(index=days, columns=range(NB)).to_numpy(float)
    C = pd.DataFrame(Cp).ffill(axis=1).to_numpy(float)
    O = np.where(np.isfinite(Op[:, B0930]), Op[:, B0930], C[:, B0930 - 1])
    oc = C[:, NB - 1] - O
    soc = np.sqrt(pd.Series(oc * oc).shift(1).rolling(20, min_periods=20).mean().to_numpy(float))
    Pt = np.column_stack([C[:, B0930 + m - 1] for m in CLOCKS])       # B0930 + m - 1 >= 59: never negative
    u = np.array(CLOCKS) / T.NMIN
    with np.errstate(invalid="ignore", divide="ignore"):
        x_ = (Pt - O[:, None]) / soc[:, None]
        y_ = (C[:, NB - 1][:, None] - Pt) / soc[:, None]
        z_ = x_ / np.sqrt(u)[None, :]
    return {"root": root, "days": days, "C": C, "O": O, "soc": soc, "Pt": Pt, "x": x_, "y": y_, "z": z_, "raw": x}


def align(panel: dict[str, Any], key: str, days: np.ndarray) -> np.ndarray:
    """The asset's [day, clock] matrix on NQ's days, joined by DATE (NaN where the asset has no such day)."""
    pos = pd.Series(np.arange(len(panel["days"])), index=panel["days"])
    ix = pos.reindex(days).to_numpy(float)
    out = np.full((len(days), len(CLOCKS)), np.nan)
    ok = np.isfinite(ix)
    out[ok] = panel[key][ix[ok].astype(int)]
    return out


def join_audit(panel: dict[str, Any], days: np.ndarray, got: np.ndarray, sample: list[int]) -> None:
    look = {d: i for i, d in enumerate(panel["days"])}
    for r in sample:
        i = look.get(days[r])
        want = panel["z"][i] if i is not None else np.full(len(CLOCKS), np.nan)
        if not np.array_equal(np.nan_to_num(want, nan=-9e9), np.nan_to_num(got[r], nan=-9e9)):
            raise D728Error(f"join: {panel['root']} at {days[r]} is not that date's row")


def lag_audit(panel: dict[str, Any], sample: list[tuple[int, int]], shift: int = 0) -> None:
    raw = panel["raw"]
    for i, j in sample:
        day = panel["days"][i]
        r = raw[raw["day"] == day].set_index("bar")
        b = B0930 + CLOCKS[j] - 1 + shift
        if b not in r.index or not np.isfinite(r.at[b, "close"]):
            continue
        if not math.isclose(float(r.at[b, "close"]), panel["Pt"][i, j], rel_tol=0, abs_tol=1e-12):
            raise D728Error(f"lag: {panel['root']} P_t at {day} clock {j} is not the close of the bar starting t-1")


# ================================================================================ statistics
def agree(zA: np.ndarray, zN: np.ndarray) -> np.ndarray:
    a = np.where(np.isfinite(zA) & (np.abs(zA) >= ZMIN), np.where(np.sign(zA) == np.sign(zN), 1.0, -1.0), 0.0)
    return np.where(np.isfinite(zN) & (zN != 0), a, 0.0)


def group_state(zs: list[np.ndarray], zN: np.ndarray) -> np.ndarray:
    """+1 agree, -1 disagree, 0 neither, per (day, clock)."""
    A = np.mean([agree(z, zN) for z in zs], axis=0)
    if len(zs) == 1:
        return A
    return np.where(A >= 1 / 3 - 1e-12, 1.0, np.where(A <= -1 / 3 + 1e-12, -1.0, 0.0))


def slope(x: np.ndarray, y: np.ndarray, m: np.ndarray) -> float:
    ok = m & np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 30:
        return float("nan")
    xs, ys = x[ok], y[ok]
    xc = xs - xs.mean()
    return float((xc * (ys - ys.mean())).sum() / (xc * xc).sum())


def dbeta(state: np.ndarray, x: np.ndarray, y: np.ndarray) -> float:
    return slope(x, y, state > 0) - slope(x, y, state < 0)


def first_entry(zN: np.ndarray, k: float) -> np.ndarray:
    hit = np.abs(zN) >= k
    return np.where(hit.any(axis=1), hit.argmax(axis=1), -1)


def book_split(state: np.ndarray, first: np.ndarray, gross: np.ndarray) -> dict[str, Any]:
    rows = np.arange(len(first))
    st = np.where(first >= 0, state[rows, np.clip(first, 0, None)], np.nan)
    out = {}
    for nm, v in (("agree", 1.0), ("silent", 0.0), ("disagree", -1.0)):
        m = (first >= 0) & (st == v) & np.isfinite(gross)
        out[nm] = {"trades": int(m.sum()), "mean_gross": float(gross[m].mean()) if m.any() else None,
                   "median_gross": float(np.median(gross[m])) if m.any() else None}
    return out


def dgross(state: np.ndarray, first: np.ndarray, gross: np.ndarray) -> float:
    s = book_split(state, first, gross)
    if not s["agree"]["trades"] or not s["disagree"]["trades"]:
        return float("nan")
    return s["agree"]["mean_gross"] - s["disagree"]["mean_gross"]


def rot_summary(obs: float, null: np.ndarray) -> dict[str, float]:
    null = null[np.isfinite(null)]
    return {"observed": obs, "offsets": int(len(null)), "p05": float(np.quantile(null, 0.05)),
            "p50": float(np.median(null)), "p95": float(np.quantile(null, 0.95)), "p95_se": 0.0,
            "rank": float((null < obs).mean()), "p_high": float((null >= obs).mean()), "p_low": float((null <= obs).mean())}


def ols2(y: np.ndarray, a: np.ndarray, b: np.ndarray) -> tuple[float, float]:
    ok = np.isfinite(y) & np.isfinite(a) & np.isfinite(b)
    X = np.column_stack([np.ones(ok.sum()), a[ok], b[ok]])
    c = np.linalg.lstsq(X, y[ok], rcond=None)[0]
    return float(c[1]), float(c[2])


def holm(ps: dict[str, float]) -> dict[str, float]:
    order = sorted(ps, key=ps.get)
    out, run = {}, 0.0
    for i, k in enumerate(order):
        run = max(run, min(1.0, ps[k] * (len(order) - i)))
        out[k] = run
    return out


# ================================================================================ the run
def run(data_root: Path) -> int:
    t0 = time.time()
    import stage1_d711_f2_mechanism as M711
    cl = M711.cost_line("NQ")
    usd, cost = float(cl["usd_per_point"]), float(cl["cost"])
    P("[D728] NQ (D727's objects) ...")
    pn = T.load_root("NQ", data_root)
    ob = T.objects(pn)
    ka = json.loads((REPO / "data" / "stage0_d727_trend_curve.json").read_text(encoding="utf-8"))["roots"]["NQ"]
    if len(pn["days"]) != ka["days"] or not math.isclose(T.beta_nw(ob["x"][:, 0], ob["y"][:, 0])["beta"],
                                                         ka["clocks"][0]["beta"], rel_tol=0, abs_tol=1e-12):
        raise D728Error("NQ's objects are not D727's")
    days, xN, yN, zN = pn["days"], ob["x"], ob["y"], ob["z"]
    P("[D728] fut_day1m assets ...")
    raw = load_day1m(data_root)
    panels = {r: asset_panel(raw, r) for r in ASSETS}
    rng = np.random.default_rng(728)
    Za = {}
    for r, pa in panels.items():
        smp = [(int(rng.integers(21, len(pa["days"]))), int(rng.integers(0, len(CLOCKS)))) for _ in range(30)]
        lag_audit(pa, smp)
        try:
            lag_audit(pa, smp, shift=1)
        except D728Error:
            pass
        else:
            raise D728Error(f"{r}: the lag canary did not fire")
        Za[r] = align(pa, "z", days)
        js = [int(v) for v in rng.integers(0, len(days), 50)]
        join_audit(pa, days, Za[r], js)
        try:
            join_audit(pa, np.roll(days, 1), Za[r], js)
        except D728Error:
            pass
        else:
            raise D728Error(f"{r}: a shifted join did not fire the audit")
    X, Y = xN, yN                                        # [day, clock]; stacked through the masks below
    out: dict[str, Any] = {"spec": "D728-STAGE-0-PRE-REG-does-cross-asset-agreement-sharpen-nq.md",
                           "seal": f"nothing on or after {Z.CUT24}", "nq_days": int(len(days)),
                           "asset_days": {r: int(len(p["days"])) for r, p in panels.items()}, "groups": {}}
    n = len(days)
    offsets = range(EDGE, n - EDGE)
    gross_k = {}
    firsts = {}
    for k in (0.5, 1.0, 1.5):
        f = first_entry(zN, k)
        rows = np.arange(n)
        side = np.where(f >= 0, np.sign(zN[rows, np.clip(f, 0, None)]), 0.0)
        entry = ob["Pt"][rows, np.clip(f, 0, None)]
        firsts[k] = f
        gross_k[k] = np.where(f >= 0, side * (ob["close"] - entry) * usd, np.nan)
    for g, members in GROUPS.items():
        P(f"[D728] {g} ...")
        zs = [Za[r] for r in members]
        st = group_state(zs, zN)
        res: dict[str, Any] = {"members": list(members),
                               "state_share": {nm: float((st == v).mean()) for nm, v in (("agree", 1), ("neither", 0), ("disagree", -1))}}
        obs = dbeta(st, X, Y)
        nullb, nullg = [], []
        for kk in offsets:
            s2 = group_state([np.roll(z, kk, axis=0) for z in zs], zN)
            nullb.append(dbeta(s2, X, Y))
            nullg.append(dgross(s2, firsts[1.0], gross_k[1.0]))
        res["S1_dbeta_pooled"] = {"beta_agree": slope(X, Y, st > 0), "beta_disagree": slope(X, Y, st < 0),
                                  "beta_neither": slope(X, Y, st == 0), "rotation": rot_summary(obs, np.array(nullb))}
        res["S1_by_clock"] = [{"t": T.hhmm(m), "beta_agree": slope(X[:, [j]], Y[:, [j]], (st[:, [j]] > 0)),
                               "beta_disagree": slope(X[:, [j]], Y[:, [j]], (st[:, [j]] < 0))} for j, m in enumerate(CLOCKS)]
        res["S2_book"] = {}
        for k in (0.5, 1.0, 1.5):
            sp = book_split(st, firsts[k], gross_k[k])
            rows = np.arange(n)
            ent_state = np.where(firsts[k] >= 0, st[rows, np.clip(firsts[k], 0, None)], np.nan)
            side_all = np.where(np.isfinite(gross_k[k]), 1.0, 0.0)
            side_agree = np.where(ent_state == 1.0, 1.0, 0.0) * side_all
            gk = np.nan_to_num(gross_k[k])
            full = T.money_book(side_all, np.zeros(n), gk / usd, usd, cost, days)
            agr = T.money_book(side_agree, np.zeros(n), gk / usd, usd, cost, days)
            res["S2_book"][str(k)] = {"split": sp, "full_book": full, "agree_only_book": agr}
        res["S2_dgross_k1"] = rot_summary(dgross(st, firsts[1.0], gross_k[1.0]), np.array(nullg))
        out["groups"][g] = res
    ph = holm({g: out["groups"][g]["S1_dbeta_pooled"]["rotation"]["p_high"] for g in GROUPS})
    pl = holm({g: out["groups"][g]["S1_dbeta_pooled"]["rotation"]["p_low"] for g in GROUPS})
    for g in GROUPS:
        r = out["groups"][g]
        b1 = r["S2_book"]["1.0"]
        better = (b1["agree_only_book"]["mean_net"] or -1e9) > (b1["full_book"]["mean_net"] or 1e9)
        r["holm_p_high"], r["holm_p_low"] = ph[g], pl[g]
        r["reading"] = ("SHARPENS" if ph[g] < 0.05 and better else "WEAKENS" if pl[g] < 0.05 else "NOTHING")
    P("[D728] S3, the Dow question ...")
    s3 = {}
    for r in ("YM", "RTY"):
        xa, ya = align(panels[r], "x", days), align(panels[r], "y", days)
        b_own, b_nq = ols2(ya.ravel(), xa.ravel(), xN.ravel())
        null = []
        for kk in offsets:
            null.append(ols2(ya.ravel(), xa.ravel(), np.roll(xN, kk, axis=0).ravel())[1])
        s3[r] = {"b_own_move": b_own, "b_nq_move": b_nq, "b_nq_rotation": rot_summary(b_nq, np.array(null)),
                 "b_own_alone": slope(xa, ya, np.ones_like(xa, bool))}
    out["S3_dow_question"] = s3
    out["wall_min"] = (time.time() - t0) / 60
    OUT.write_text(json.dumps(out, indent=1, default=Z._json) + "\n", encoding="utf-8", newline="\n")
    P("[D728] " + "; ".join(f"{g}: {out['groups'][g]['reading']}" for g in GROUPS) + f"; {out['wall_min']:.1f} min")
    return 0


# ================================================================================ self-test (synthetic only)
def selftest() -> int:
    fails: list[str] = []
    rng = np.random.default_rng(11)
    n, nc = 800, len(CLOCKS)
    zN = rng.normal(0, 1, (n, nc))
    X = zN * 0.5
    zA_inf = np.where(rng.random((n, nc)) < 0.7, np.abs(rng.normal(1, 0.3, (n, nc))) * np.sign(zN),
                      -np.abs(rng.normal(1, 0.3, (n, nc))) * np.sign(zN))
    st_true = group_state([zA_inf], zN)
    Y = np.where(st_true > 0, 0.25 * X, -0.05 * X) + rng.normal(0, 0.3, (n, nc))
    obs = dbeta(st_true, X, Y)
    null = np.array([dbeta(group_state([np.roll(zA_inf, k, axis=0)], zN), X, Y) for k in range(EDGE, n - EDGE)])
    if not rot_summary(obs, null)["p_high"] < 0.05:
        fails.append("an informative asset did not beat its rotation")
    zA_ind = rng.normal(0, 1, (n, nc))
    Y2 = 0.1 * X + rng.normal(0, 0.3, (n, nc))
    o2 = dbeta(group_state([zA_ind], zN), X, Y2)
    n2 = np.array([dbeta(group_state([np.roll(zA_ind, k, axis=0)], zN), X, Y2) for k in range(EDGE, n - EDGE)])
    if rot_summary(o2, n2)["p_high"] < 0.01:
        fails.append("an independent asset beat its rotation at 1%")
    # the date join and its shifted canary
    days = np.array([f"2019-{1 + i // 28:02d}-{1 + i % 28:02d}" for i in range(60)])
    pa = {"root": "XX", "days": days[5:], "z": rng.normal(0, 1, (55, nc))}
    got = align(pa, "z", days)
    join_audit(pa, days, got, list(range(60)))
    try:
        join_audit(pa, np.roll(days, 1), got, list(range(10, 60)))
        fails.append("a shifted join did not fire")
    except D728Error:
        pass
    if fails:
        P("SELFTEST FAILED:", fails)
        return 1
    P("SELFTEST OK: an informative asset beats its rotation, an independent one does not; the date join holds and a "
      "shifted join fires the audit")
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
            raise D728Error(f"{OUT.name} exists: D728 runs once")
        return run(a.data_root)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
