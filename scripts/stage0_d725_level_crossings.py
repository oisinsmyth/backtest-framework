"""D725 Stage 0: when NQ crosses yesterday's levels, does it keep going, and does the crossing pay one MNQ? Spec:
docs/decisions/D725-STAGE-0-PRE-REG-crossing-yesterdays-levels.md, committed before this file existed.

    uv run python scripts/stage0_d725_level_crossings.py --selftest
    uv run python scripts/stage0_d725_level_crossings.py --run --data-root <checkout>/data   # once

D724's panels and conventions (imported unchanged): price at t = the close of the bar starting t-1; sigma_d = the mean
day range of the prior 20 sessions; one MNQ at D711's NQ cost line. A crossing is the first one-minute bar starting
09:31 -> 14:59 whose close is on the other side of the level from the 09:30 open; entry at that close, direction the
crossing's. Nothing dated 2024-01-01 or later is used.
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
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d720_size_the_direction as Z  # noqa: E402
import stage0_d724_which_mean as W  # noqa: E402

OUT = REPO / "data" / "stage0_d725_level_crossings.json"
NMIN, TICK, USD_PT = W.NMIN, 0.25, 2.0
FIRST_M, LAST_M = 1, 329                  # bars starting 09:31 .. 14:59
HS = {"15": 15, "30": 30, "60": 60, "close": None}
PRIMARY = ("L1_prior_close", "L2_prior_vwap", "L3_overnight_mid")
REPORTED = ("L4_prior_high", "L5_prior_low")
EDGE = 20
P = Z.P


class D725Error(AssertionError):
    pass


# ================================================================================ levels and crossings
def levels(pn: dict[str, Any]) -> dict[str, np.ndarray]:
    H, L, C, V = pn["H"], pn["L"], pn["C"], pn["V"]
    same = np.r_[False, pn["con"][1:] == pn["con"][:-1]]
    tp = np.where(np.isfinite(H) & np.isfinite(L), (np.nan_to_num(H) + np.nan_to_num(L) + C) / 3, C)
    vw = (tp * V).sum(axis=1) / np.where(V.sum(axis=1) > 0, V.sum(axis=1), np.nan)
    prev = lambda v: np.where(same, np.r_[np.nan, v[:-1]], np.nan)     # noqa: E731
    return {"L1_prior_close": prev(C[:, -1]), "L2_prior_vwap": prev(vw), "L3_overnight_mid": pn["on_mid"],
            "L4_prior_high": prev(np.nanmax(H, axis=1)), "L5_prior_low": prev(np.nanmin(L, axis=1))}


def crossings(C: np.ndarray, O: np.ndarray, lv: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(m, s) per day: the first bar index m in [FIRST_M, LAST_M] whose close is on the far side of lv from the open,
    and the crossing's direction s; m = -1 where there is none (or no side: |O - lv| <= one tick)."""
    side0 = np.sign(O - lv)
    ok = np.isfinite(lv) & np.isfinite(O) & (np.abs(O - lv) > TICK)
    seg = C[:, FIRST_M:LAST_M + 1]
    far = (np.sign(seg - lv[:, None]) == -side0[:, None]) & ok[:, None] & np.isfinite(seg)
    has = far.any(axis=1)
    m = np.where(has, far.argmax(axis=1) + FIRST_M, -1)
    return m, np.where(has, -side0, 0.0)


def crossings_loop(C: np.ndarray, O: np.ndarray, lv: np.ndarray, d: int, peek: int = 0) -> tuple[int, float]:
    """Second implementation, one day, plain Python, reading closes up to the bar it tests. `peek` = 1 tests the next
    bar's close instead (the canary)."""
    if not (np.isfinite(lv[d]) and np.isfinite(O[d]) and abs(O[d] - lv[d]) > TICK):
        return -1, 0.0
    side0 = 1.0 if O[d] > lv[d] else -1.0
    for m in range(FIRST_M, LAST_M + 1):
        c = C[d, m + peek]
        if np.isfinite(c) and (c - lv[d]) * side0 < 0 and c != lv[d]:
            return m, -side0
    return -1, 0.0


def forward(C: np.ndarray, m: np.ndarray, h: int | None) -> np.ndarray:
    """The price h minutes after entry (entry = the close of bar m, the price at minute m+1): the close of bar m+h, or
    of the 15:59 bar for the close; NaN where m = -1 or m + h passes 15:59. Never a wrapped index."""
    out = np.full(len(m), np.nan)
    e = np.where(m >= 0, (NMIN - 1) if h is None else m + h, -1)
    ok = (m >= 0) & (e <= NMIN - 1) & (e >= 0)
    out[ok] = C[np.flatnonzero(ok), e[ok]]
    return out


def forward_audit(C: np.ndarray, m: np.ndarray, h: int | None, got: np.ndarray, days: list[int]) -> None:
    for d in days:
        if m[d] < 0:
            continue
        e = (NMIN - 1) if h is None else m[d] + h
        want = C[d, e] if e <= NMIN - 1 else np.nan
        if not ((np.isnan(want) and np.isnan(got[d])) or math.isclose(want, got[d], rel_tol=0, abs_tol=1e-9)):
            raise D725Error(f"right quantity: the forward price at day {d} is not bar m+h (a wrapped index?)")


# ================================================================================ statistics
def week_of(days: np.ndarray) -> np.ndarray:
    iso = pd.to_datetime(pd.Series(days)).dt.isocalendar()
    return (iso["year"].astype(str) + "-" + iso["week"].astype(str)).to_numpy()


def clustered(x: np.ndarray, groups: np.ndarray) -> dict[str, float]:
    ok = np.isfinite(x)
    x, g = x[ok], groups[ok]
    n = len(x)
    if n < 5:
        return {"n": n, "mean": float("nan"), "t": float("nan")}
    mu = float(x.mean())
    s = pd.Series(x - mu).groupby(g).sum().to_numpy()
    se = math.sqrt(float((s * s).sum())) / n
    t = mu / se if se > 0 else float("nan")
    return {"n": n, "mean": mu, "median": float(np.median(x)), "t": t, "p_two": float(2 * stats.norm.sf(abs(t)))}


def event_stats(g_pts: np.ndarray, sig: np.ndarray, weeks: np.ndarray) -> dict[str, Any]:
    return {"sigma_units": clustered(g_pts / sig, weeks), "usd": clustered(g_pts * USD_PT, weeks)}


def rotation(C: np.ndarray, O: np.ndarray, lv: np.ndarray, sig: np.ndarray, elig: np.ndarray) -> dict[str, float]:
    """Enumerated rotation of the level's offset from the open, (L - O), across the eligible sessions."""
    idx = np.flatnonzero(elig)
    off = (lv - O)[idx]

    def stat(lvr: np.ndarray) -> float:
        m, s = crossings(C, O, lvr)
        f = forward(C, m, 60)
        g = np.where(m >= 0, s * (f - np.where(m >= 0, C[np.arange(len(m)), np.clip(m, 0, None)], np.nan)), np.nan)
        v = g[idx] / sig[idx]
        return float(np.nanmean(v))

    obs = stat(lv)
    base = np.full(len(lv), np.nan)
    base[idx] = O[idx] + off
    if not math.isclose(stat(base), obs, rel_tol=0, abs_tol=1e-12):
        raise D725Error("rotation: offset 0 does not reproduce the observed statistic")
    null = []
    for k in range(EDGE, len(idx) - EDGE):
        lr = np.full(len(lv), np.nan)
        lr[idx] = O[idx] + np.roll(off, k)
        null.append(stat(lr))
    null = np.array(null)
    return {"observed": obs, "offsets": int(len(null)), "p05": float(np.quantile(null, 0.05)),
            "p50": float(np.median(null)), "p95": float(np.quantile(null, 0.95)), "p95_se": 0.0,
            "rank": float((null < obs).mean())}


def book(g_usd: np.ndarray, cost: float, days: np.ndarray, elig: np.ndarray) -> dict[str, Any]:
    tr = np.isfinite(g_usd) & elig
    net = np.where(tr, g_usd - cost, 0.0)[elig]
    gross = np.where(tr, g_usd, 0.0)[elig]
    years = np.array([s[:4] for s in days[elig]])
    by = {y: float(net[years == y].sum()) for y in np.unique(years)}
    tot = sum(by.values())
    nt = (g_usd - cost)[tr]
    return {"trades": int(tr.sum()), "net_sharpe": Z.sharpe(net), "net_sortino": Z.sortino(net),
            "gross_sharpe": Z.sharpe(gross), "gross_sortino": Z.sortino(gross),
            "mean_gross": float(g_usd[tr].mean()) if tr.any() else None,
            "median_gross": float(np.median(g_usd[tr])) if tr.any() else None,
            "net_distribution": Z.trade_dist(nt), "net_by_year": by,
            "years_positive": int(sum(v > 0 for v in by.values())), "years": len(by),
            "largest_year_share": float(max(by.values()) / tot) if tot > 0 else None}


def split(g_usd: np.ndarray, lab: np.ndarray) -> dict[str, Any]:
    out = {}
    for nm, lo, hi in (("low", 0, 1 / 3), ("mid", 1 / 3, 2 / 3), ("high", 2 / 3, 1.01)):
        m = np.isfinite(g_usd) & np.isfinite(lab) & (lab >= lo) & (lab < hi)
        out[nm] = {"trades": int(m.sum()), "mean_gross": float(g_usd[m].mean()) if m.any() else None,
                   "median_gross": float(np.median(g_usd[m])) if m.any() else None}
    return out


# ================================================================================ the run
def run(data_root: Path) -> int:
    t0 = time.time()
    import stage0_d671_break_construction as C671
    import stage1_d711_f2_mechanism as M711
    cost = float(M711.cost_line("NQ")["cost"])
    P("[D725] panels ...")
    pn = W.load_panels(data_root)
    C, O, sig, days = pn["C"], pn["O0"], pn["sig"], pn["days"]
    Lv = levels(pn)
    weeks = week_of(days)
    P("[D725] F_close (the evening-before size) ...")
    lab = W.build_labels(data_root).reindex(days)
    fclose = lab["F_close"].to_numpy(float)
    tau_close = C671.tiers(fclose)
    C671.tier_audit(tau_close, fclose, list(range(0, len(fclose), max(1, len(fclose) // 30))))
    day_range = (np.nanmax(pn["H"], axis=1) - np.nanmin(pn["L"], axis=1)) / sig
    real_ter = np.full(len(days), np.nan)
    fin = np.isfinite(day_range)
    real_ter[fin] = stats.rankdata(day_range[fin]) / fin.sum()
    mu = {}
    for hn, h in HS.items():                                   # same-clock drift per entry bar, in sigma units
        mu[hn] = np.array([np.nanmean((forward(C, np.full(len(days), m), h) - C[:, m]) / sig) for m in range(NMIN)])
    rng = np.random.default_rng(725)
    audit_days = sorted(int(x) for x in rng.choice(np.flatnonzero(np.isfinite(sig)), 80, replace=False))
    out: dict[str, Any] = {"spec": "D725-STAGE-0-PRE-REG-crossing-yesterdays-levels.md", "seal": f"nothing on or after {Z.CUT24}",
                           "days": int(len(days)), "window": [str(days[0]), str(days[-1])], "mnq_cost": cost, "levels": {}}
    for name in PRIMARY + REPORTED:
        P(f"[D725] {name} ...")
        lv = Lv[name]
        elig = np.isfinite(lv) & np.isfinite(sig)
        m, s = crossings(C, O, lv)
        m = np.where(elig, m, -1)
        for d in audit_days:
            if not elig[d]:
                continue
            if crossings_loop(C, O, lv, d) != (int(m[d]), float(s[d])):
                raise D725Error(f"lag: {name}'s crossing at day {d} differs from the plain-Python loop")
        fired = any(crossings_loop(C, O, lv, d, peek=1) != (int(m[d]), float(s[d])) for d in audit_days if elig[d] and m[d] >= 0)
        if not fired:
            raise D725Error(f"{name}: the peek canary did not fire")
        entry = np.where(m >= 0, C[np.arange(len(m)), np.clip(m, 0, None)], np.nan)
        M = 2 * O - lv
        mm, ms = crossings(C, O, np.where(elig, M, np.nan))
        mentry = np.where(mm >= 0, C[np.arange(len(mm)), np.clip(mm, 0, None)], np.nan)
        res: dict[str, Any] = {"eligible_days": int(elig.sum()), "events": int((m >= 0).sum()),
                               "mirror_events": int((mm >= 0).sum())}
        g_by_h = {}
        for hn, h in HS.items():
            f = forward(C, m, h)
            forward_audit(C, m, h, f, audit_days)
            g = s * (f - entry)
            g_by_h[hn] = g
            gm = ms * (forward(C, mm, h) - mentry)
            both = np.isfinite(g) & np.isfinite(gm)
            drift = np.where(m >= 0, s * mu[hn][np.clip(m, 0, None)], np.nan)
            res[hn] = {"level": event_stats(g, sig, weeks), "mirror": event_stats(gm, sig, weeks),
                       "level_minus_mirror_paired_sigma": clustered(np.where(both, (g - gm) / sig, np.nan), weeks),
                       "level_after_drift_sigma": clustered(g / sig - drift, weeks)}
        g60 = g_by_h["60"]
        hold = np.where(m >= 0, s * (forward(C, m, 60) - lv) > 0, np.nan)
        mhold = np.where(mm >= 0, ms * (forward(C, mm, 60) - M) > 0, np.nan)
        res["P2_holding_60"] = {"level": float(np.nanmean(hold)), "mirror": float(np.nanmean(mhold))}
        if name in PRIMARY:
            res["rotation_60"] = rotation(C, O, np.where(elig, lv, np.nan), sig, elig)
        clk = {"09:31-11:59": (m >= 1) & (m < 150), "12:00-13:59": (m >= 150) & (m < 270), "14:00-14:59": m >= 270}
        res["by_clock_60_usd"] = {k: clustered(np.where(v, g60 * USD_PT, np.nan), weeks) for k, v in clk.items()}
        res["P3"] = {}
        for hn in ("60", "close"):
            gu = g_by_h[hn] * USD_PT
            res["P3"][hn] = {"book": book(gu, cost, days, elig),
                             "oracle_realised_day_size_tercile": split(gu, real_ter),
                             "F_close_tercile": split(gu, tau_close),
                             "F_close_window": book(gu, cost, days, elig & np.isfinite(tau_close))}
        out["levels"][name] = res
    ps = {n: out["levels"][n]["60"]["level"]["sigma_units"]["p_two"] for n in PRIMARY}
    order = sorted(PRIMARY, key=lambda n: ps[n])
    holm, run_max = {}, 0.0
    for i, n in enumerate(order):
        run_max = max(run_max, min(1.0, ps[n] * (len(order) - i)))
        holm[n] = run_max
    go = False
    for n in PRIMARY:
        L = out["levels"][n]
        st = L["60"]["level"]["sigma_units"]
        cont = (st["mean"] > 0 and holm[n] < 0.05 and L["rotation_60"]["observed"] > L["rotation_60"]["p95"]
                and L["60"]["level_minus_mirror_paired_sigma"]["mean"] > 0 and L["60"]["level_minus_mirror_paired_sigma"]["t"] >= 2
                and L["60"]["level_after_drift_sigma"]["mean"] > 0)
        rd = ("CONTINUES" if cont else "REVERTS" if (st["mean"] < 0 and holm[n] < 0.05)
              else "NOT DISTINCT" if st["mean"] > 0 else "NOTHING")
        L["holm_p_60"] = holm[n]
        L["reading"] = rd
        pays = any((L["P3"][h]["book"]["mean_gross"] or -1e9) >= 2 * cost or
                   any((v["mean_gross"] or -1e9) >= 2 * cost for v in L["P3"][h]["F_close_tercile"].values())
                   for h in ("60", "close"))
        L["pays_2c"] = bool(pays)
        go = go or (cont and pays)
    out["GO"] = go
    out["wall_min"] = (time.time() - t0) / 60
    OUT.write_text(json.dumps(out, indent=1, default=Z._json) + "\n", encoding="utf-8", newline="\n")
    P("[D725] " + "; ".join(f"{n}: {out['levels'][n]['reading']}" for n in PRIMARY) + f"; GO {go}; {out['wall_min']:.1f} min")
    return 0


# ================================================================================ self-test (synthetic only)
def selftest() -> int:
    fails: list[str] = []
    rng = np.random.default_rng(5)
    nd = 300
    C = 100 + np.cumsum(rng.normal(0, 0.3, (nd, NMIN)), axis=1)
    O = C[:, 0] - rng.normal(0, 0.3, nd)
    lv = O + rng.choice([-1.5, 1.5], nd)
    m, s = crossings(C, O, lv)
    for d in range(40):
        if crossings_loop(C, O, lv, d) != (int(m[d]), float(s[d])):
            fails.append("vector and loop crossings differ")
            break
    if not any(crossings_loop(C, O, lv, d, peek=1) != (int(m[d]), float(s[d])) for d in range(40) if m[d] >= 0):
        fails.append("the peek canary did not fire")
    f = forward(C, m, 60)
    forward_audit(C, m, 60, f, list(range(nd)))
    bad = f.copy()
    late = np.flatnonzero((m >= 0) & (m + 60 > NMIN - 1))
    wrapped = np.where(m >= 0, C[np.arange(nd), (np.clip(m, 0, None) + 400) % NMIN], np.nan)
    try:
        forward_audit(C, m, 400, wrapped, list(range(nd)))
        fails.append("the forward audit missed a wrapped index")
    except D725Error:
        pass
    del bad, late
    # sign in money: a crossing up that rises pays; a crossing down that falls pays
    Cx = np.full((2, NMIN), 100.0)
    Cx[0, 10:] = 101.0
    Cx[0, 70:] = 103.0
    Cx[1, 10:] = 99.0
    Cx[1, 70:] = 97.0
    mx, sx = crossings(Cx, np.array([100.0, 100.0]), np.array([100.5, 99.5]))
    gx = sx * (forward(Cx, mx, 60) - Cx[np.arange(2), mx]) * USD_PT
    if not (gx[0] > 0 and gx[1] > 0 and math.isclose(gx[0], 4.0) and math.isclose(gx[1], 4.0)):
        fails.append(f"sign in money: {gx}")
    # the mirror sits at the level's distance from the open
    M = 2 * O - lv
    if not np.allclose(np.abs(M - O), np.abs(lv - O)):
        fails.append("the mirror is not equidistant")
    # rotation: offset 0 reproduces; a level that carries continuation beats its rotation
    Ct = C.copy()
    for d in range(nd):
        if m[d] >= 0:
            Ct[d, m[d] + 1:] += s[d] * 1.0
    rot = rotation(Ct, O, lv, np.full(nd, 5.0), np.ones(nd, bool))
    if not rot["observed"] > rot["p95"]:
        fails.append("an informative level did not beat its rotation")
    if fails:
        P("SELFTEST FAILED:", fails)
        return 1
    P("SELFTEST OK: the vectorised crossings equal the loop and the peek canary fires; the forward audit catches a "
      "wrapped index; sign in money both ways; the mirror is equidistant; an informative level beats its rotation")
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
            raise D725Error(f"{OUT.name} exists: D725 runs once")
        return run(a.data_root)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
