"""D696 Stage 0: is D694's worst cell (ctier >= 2/3 and IV/RV percentile < 1/2: busy realised range the options market
does not price forward) real, or the worst of six by chance? Spec: docs/decisions/D696-STAGE-0-DESIGN-the-busy-low-iv-
cell.md (5ac1497b).

    uv run python scripts/stage0_d696_busy_low_iv.py --selftest
    uv run python scripts/stage0_d696_busy_low_iv.py --time
    uv run python scripts/stage0_d696_busy_low_iv.py --run      # once

A: the jointly worst of six cells (summed per-root z) on D694's E4 trades, against the enumerated rotation of the whole
IV label (A1, gating) and of its ingredient residual (A2, labelling); same offset on both roots. B: the mechanism
(exit reasons, MFE/MAE, hold-to-close, pre-entry range share), readings declared. C: the fixed cell X on D663's
opening-range break F (60-minute hold), against A1's rotation. In-sample 2018-01-09 -> 2025-02-28; the vault is never
read. Labels, trades and forecasts are D694's cached bundle. Writes data/stage0_d696_busy_low_iv.json (statistics only).
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
import stage1_d694_coiled_break as P  # noqa: E402

D, C = P.D, P.C
M, T, X = P.M, P.T, P.X
S = T.S  # D662: find_break, follow, MORNING
ROOTS = ("ES", "NQ")
EDGE, CLOSE_BAR, RTH_OPEN = 21, 15 * 60 + 59, 9 * 60 + 30
X_CELL = (2, 0)  # (ctier tercile 3, p_iv low half)
OUT = REPO / "data" / "stage0_d696_busy_low_iv.json"
D694_JSON = REPO / "data" / "stage1_d694_coiled_break.json"
D663_JSON = REPO / "data" / "stage0_d663_per_root_gamma_break.json"


class D696Error(RuntimeError):
    pass


# ================================================================================ cells and the statistic
def tercile(ct: np.ndarray, d694_rule: bool = False) -> np.ndarray:
    """0 / 1 / 2 for ctier < 1/3, 1/3-2/3, >= 2/3 (D696's declaration). `d694_rule` reproduces D694's grid, whose top
    band was ct < 1 and so dropped ctier == 1.0 (returned as -1)."""
    t = np.where(ct < 1 / 3, 0, np.where(ct < 2 / 3, 1, 2))
    if d694_rule:
        t = np.where(ct >= 1.0, -1, t)
    return np.where(np.isfinite(ct), t, -1)


def cell_z(g: np.ndarray, terc: np.ndarray, high: np.ndarray, ok: np.ndarray, sd: float) -> np.ndarray:
    """z of each of the six cells' mean: mean / (sd / sqrt(n)); rows ordered (tercile, half) with half 0 = low."""
    z = np.full((3, 2), np.nan)
    for t in range(3):
        for h in range(2):
            m = ok & (terc == t) & (high == h)
            n = int(m.sum())
            if n >= 2:
                z[t, h] = g[m].mean() / (sd / math.sqrt(n))
    return z


def joint(zs: list[np.ndarray]) -> np.ndarray:
    return (zs[0] + zs[1]) / math.sqrt(2)


# ================================================================================ the mechanism (trade 1)
def mechanism(bb: dict, i: int, D_: int, entry: float, include_entry: bool = False, past_entry: bool = False) -> dict[str, float]:
    """MFE / MAE / hold-to-close from the bar after entry (the canary `include_entry` starts at the entry bar), and the
    share of the day's RTH range made up to and including the entry bar (the canary `past_entry` reads one bar more)."""
    m, h, l, c = bb["m"], bb["h"], bb["l"], bb["c"]
    rth = (m >= RTH_OPEN) & (m <= CLOSE_BAR)
    after = rth & (np.arange(len(m)) >= (i if include_entry else i + 1))
    fav = np.r_[D_ * (h[after] / entry - 1), D_ * (l[after] / entry - 1)] * 1e4
    last = np.flatnonzero(rth)[-1]
    upto = rth & (np.arange(len(m)) <= (i + 1 if past_entry else i))
    day = float(h[rth].max() - l[rth].min())
    return {"mfe": float(fav.max()) if len(fav) else np.nan, "mae": float(fav.min()) if len(fav) else np.nan,
            "hold_close": float(D_ * (c[last] / entry - 1) * 1e4),
            "pre_share": float((h[upto].max() - l[upto].min()) / day) if day > 0 else np.nan, "entry_min": float(m[i])}


def mechanism_audit(bb: dict, i: int, D_: int, entry: float, got: dict[str, float]) -> None:
    """Second implementation by MINUTE (bars starting strictly after the entry bar's minute; up to its minute)."""
    m, h, l = bb["m"], bb["h"], bb["l"]
    mfe, mae = -np.inf, np.inf
    for k in range(len(m)):
        if m[k] > m[i] and m[k] <= CLOSE_BAR:
            for px in (h[k], l[k]):
                v = D_ * (px / entry - 1) * 1e4
                mfe, mae = max(mfe, v), min(mae, v)
    hi = max(h[k] for k in range(len(m)) if RTH_OPEN <= m[k] <= m[i])
    lo = min(l[k] for k in range(len(m)) if RTH_OPEN <= m[k] <= m[i])
    dh = max(h[k] for k in range(len(m)) if RTH_OPEN <= m[k] <= CLOSE_BAR)
    dl = min(l[k] for k in range(len(m)) if RTH_OPEN <= m[k] <= CLOSE_BAR)
    want = (mfe, mae, (hi - lo) / (dh - dl))
    have = (got["mfe"], got["mae"], got["pre_share"])
    if not np.allclose(want, have, rtol=0, atol=1e-9):
        raise D696Error(f"lag: the mechanism read uses bars on the wrong side of the entry ({have} vs {want})")


def sign_audit() -> None:
    m = np.arange(570, 960, dtype=float)
    path = 100.0 + 3.0 * (m - 570) / 389
    for sgn in (1, -1):
        p = 100.0 + sgn * (path - 100.0)
        bb = {"m": m, "o": p, "h": p + 0.01, "l": p - 0.01, "c": p}
        got = mechanism(bb, 100, sgn, float(p[100]))
        if not (got["mfe"] > 0 and got["hold_close"] > 0):
            raise D696Error(f"sign: a favourable path does not read favourable for side {sgn} ({got})")


# ================================================================================ the rotations
_W: dict[str, Any] = {}


def stats_at(k: int, kind: str, w: dict[str, Any]) -> tuple[float, float]:
    """(S over the six cells of trade 1, the fixed cell X's joint z on trade 2) with the IV label rotated by k."""
    z1, z2 = [], []
    for r in ROOTS:
        a = w[r]
        iv = a["ivrv"].copy()
        if kind == "whole":
            fin = np.isfinite(iv)
            iv[fin] = np.roll(a["ivrv"][fin], k)
        else:
            uu = a["u"][a["F"]]
            iv[a["F"]] = a["ivrv"][a["F"]] + (np.roll(uu, k) - uu)
        p = C.tiers(iv)
        for (pos, g, terc, sd), acc in ((a["t1"], z1), (a["t2"], z2)):
            pp = p[pos]
            acc.append(cell_z(g, terc, (pp >= 0.5).astype(int), np.isfinite(pp), sd))
    j1, j2 = joint(z1), joint(z2)
    return float(np.nanmin(j1)), float(j2[X_CELL])


def _init(w: dict[str, Any]) -> None:
    _W.update(w)


def _job(items: list[tuple[str, int]]) -> list[tuple[str, int, float, float]]:
    return [(kind, k, *stats_at(k, kind, _W)) for kind, k in items]


def rotations(w: dict[str, Any], items: list[tuple[str, int]], workers: int) -> dict[tuple[str, int], tuple[float, float]]:
    chunks = [items[i::workers] for i in range(workers)]
    with ProcessPoolExecutor(max_workers=workers, initializer=_init, initargs=(w,)) as pool:
        return {(kind, k): (a, b) for part in pool.map(_job, chunks) for kind, k, a, b in part}


# ================================================================================ building
def load_bars() -> tuple[dict, dict[str, pd.DataFrame]]:
    b, use, _gd, R = M.load_bars(D.DATA, False, ROOTS)
    C._R = R
    T.MULT.update(M.MULT)
    tabs = R.session_table(b, use, roots=ROOTS)
    bars = R.bar_arrays(b)
    return bars, {r: T.root_frame(b, tabs[r], r) for r in ROOTS}


def d663_breaks(r: str, dfull: pd.DataFrame, bars: dict) -> pd.DataFrame:
    rows = T.breaks(dfull, bars, r, S.MORNING)
    ka = json.loads(D663_JSON.read_text(encoding="utf-8"))["F_morning"][r]
    if len(rows) != ka["n"] or abs(float(rows["F"].mean()) - ka["mean"]) > 1e-9:
        raise D696Error(f"{r}: D663's morning F not reproduced ({len(rows)}, {rows['F'].mean()} vs {ka})")
    T.right_quantity_f(r, rows, bars)
    return rows


def d694_grid_reproduced(tr: pd.DataFrame, r: str) -> None:
    grid = json.loads(D694_JSON.read_text(encoding="utf-8"))["roots"][r]["reported"]["grid_3x2"]
    win = np.isfinite(tr[["t671", "ctier", "p_iv", "f1"]].to_numpy(float)).all(axis=1)
    terc = tercile(tr["ctier"].to_numpy(float), d694_rule=True)
    hi = tr["p_iv"].to_numpy(float) >= 0.5
    g = tr["gross"].to_numpy(float)
    for t in range(3):
        for h, nm in ((0, "iv_low"), (1, "iv_high")):
            m = win & (terc == t) & (hi == bool(h))
            want = grid[f"ctier_{t + 1}_{nm}"]
            if int(m.sum()) != want["n"] or abs(float(g[m].mean()) - want["gross_bp"]) > 1e-9:
                raise D696Error(f"{r}: D694's grid cell {t + 1}/{nm} not reproduced")


def build(workers: int, time_only: bool = False) -> dict[str, Any]:
    t0 = time.time()
    sign_audit()
    bd = P.get_bundle()
    bars, dfull = load_bars()
    w: dict[str, Any] = {}
    out: dict[str, Any] = {"spec": "D696 (5ac1497b)", "credit": "dealer gamma (GEX): SqueezeMetrics (D694's labels)", "roots": {}}
    mech_rows: dict[str, pd.DataFrame] = {}
    for r in ROOTS:
        tr, lab = bd[r]["tr"], bd[r]["lab"]
        d694_grid_reproduced(tr, r)
        sess_all = lab.index.to_numpy(str)
        lab_ok = np.isfinite(lab[["t671", "ctier", "p_iv", "f1"]].to_numpy(float)).all(axis=1)
        win_sess = set(sess_all[lab_ok])
        spos = pd.Series(np.arange(len(sess_all)), index=sess_all)
        # trade 1 (E4) in the window
        win1 = np.isfinite(tr[["t671", "ctier", "p_iv", "f1"]].to_numpy(float)).all(axis=1)
        t1 = tr[win1].reset_index(drop=True)
        g1 = t1["gross"].to_numpy(float)
        terc1 = tercile(t1["ctier"].to_numpy(float))
        pos1 = spos.reindex(t1["session"].to_numpy(str)).to_numpy(int)
        # trade 2 (D663's F) in the same window
        rows = d663_breaks(r, dfull[r], bars)
        t2 = rows[rows.index.isin(win_sess)]
        pos2 = spos.reindex(t2.index.to_numpy(str)).to_numpy(int)
        f2 = t2["F"].to_numpy(float)
        terc2 = tercile(lab["ctier"].to_numpy(float)[pos2])
        u, F, beta = P.residual(lab, (sess_all >= min(win_sess)) & (sess_all <= max(win_sess)))
        if np.allclose(u[F], lab["lniv"].to_numpy(float)[F]):
            raise D696Error("right quantity: A2 would rotate ln IV itself, not its residual")
        w[r] = {"ivrv": lab["ivrv"].to_numpy(float), "u": u, "F": F,
                "t1": (pos1, g1, terc1, float(g1.std(ddof=1))), "t2": (pos2, f2, terc2, float(f2.std(ddof=1)))}
        # the mechanism, re-deriving each E4 trade at the level
        mr = []
        old = X.TICK
        X.TICK = 0.0
        try:
            for s, D_, g_want in zip(t1["session"], t1["D"], g1):
                rec, bb = dfull[r].loc[s], bars[(r, s)]
                Lh, Ll, A = float(rec["prior_high"]), float(rec["prior_low"]), float(rec["atr20"])
                p0 = X.plain_break(bb, Lh, Ll, A)
                px0, why = X.exit_trade(bb, p0["i"], p0["D"], p0["entry"], p0["L"], A, 0.0, "E4")
                if p0["D"] != D_ or P.gross_bp(p0["D"], p0["entry"], px0) != g_want:
                    raise D696Error(f"{r} {s}: the re-derived E4 trade differs from D694's bundle")
                mm = mechanism(bb, p0["i"], p0["D"], p0["entry"])
                if len(mr) % 50 == 0:
                    mechanism_audit(bb, p0["i"], p0["D"], p0["entry"], mm)
                mr.append({**mm, "why": why})
        finally:
            X.TICK = old
        mech_rows[r] = pd.DataFrame(mr)
        extra = int((np.isfinite(t1["ctier"].to_numpy(float)) & (t1["ctier"].to_numpy(float) >= 1.0)).sum())
        out["roots"][r] = {"trades_1": int(len(t1)), "trades_2": int(len(t2)), "ctier_eq_1_trades_added_to_tercile_3": extra,
                           "a2_residual_beta": beta, "sd_1": w[r]["t1"][3], "sd_2": w[r]["t2"][3]}
    n_whole = min(int(np.isfinite(w[r]["ivrv"]).sum()) for r in ROOTS)
    n_ingr = min(int(w[r]["F"].sum()) for r in ROOTS)
    s0w, c0w = stats_at(0, "whole", w)
    s0i, c0i = stats_at(0, "ingredient", w)
    if (s0w, c0w) != (s0i, c0i):
        raise D696Error("offset 0 differs between the two rotations")
    if time_only:
        t1_ = time.time()
        for k in (21, 22, 23):
            stats_at(k, "whole", w)
            stats_at(k, "ingredient", w)
        per = (time.time() - t1_) / 6
        n = (n_whole + n_ingr - 4 * EDGE)
        print(f"{per:.3f} s an item x {n} items / {workers} workers = about {per * n / workers / 60:.1f} min")
        return {}
    # observed
    z1 = [cell_z(w[r]["t1"][1], w[r]["t1"][2], (C.tiers(w[r]["ivrv"])[w[r]["t1"][0]] >= 0.5).astype(int),
                 np.ones(len(w[r]["t1"][1]), bool), w[r]["t1"][3]) for r in ROOTS]
    j1 = joint(z1)
    S_obs = float(np.nanmin(j1))
    argmin = [int(v) for v in np.unravel_index(np.nanargmin(j1), j1.shape)]
    if S_obs != s0w:
        raise D696Error(f"offset 0 does not reproduce S ({s0w} vs {S_obs})")
    items = [("whole", k) for k in range(EDGE, n_whole - EDGE)] + [("ingredient", k) for k in range(EDGE, n_ingr - EDGE)]
    t_rot = time.time()
    rot = rotations(w, items, workers)
    wall = time.time() - t_rot
    sw = np.array([rot[i][0] for i in items if i[0] == "whole"])
    cw = np.array([rot[i][1] for i in items if i[0] == "whole"])
    si = np.array([rot[i][0] for i in items if i[0] == "ingredient"])

    def lower(x: np.ndarray, obs: float) -> dict[str, float]:
        return {"offsets": int(len(x)), "p5": float(np.quantile(x, 0.05)), "p50": float(np.median(x)), "p5_se": 0.0,
                "share_at_or_below_observed": float((x <= obs).mean())}
    a1, a2, cc = lower(sw, S_obs), lower(si, S_obs), lower(cw, c0w)
    # C-i: is X the jointly worst cell for trade 2?
    z2 = [cell_z(w[r]["t2"][1], w[r]["t2"][2], (C.tiers(w[r]["ivrv"])[w[r]["t2"][0]] >= 0.5).astype(int),
                 np.ones(len(w[r]["t2"][1]), bool), w[r]["t2"][3]) for r in ROOTS]
    j2 = joint(z2)
    c_argmin = [int(v) for v in np.unravel_index(np.nanargmin(j2), j2.shape)]
    # B: the mechanism readings
    mech = {}
    for r in ROOTS:
        a, mr = w[r], mech_rows[r]
        hi1 = C.tiers(a["ivrv"])[a["t1"][0]] >= 0.5
        terc = a["t1"][2]
        cells = {"X": (terc == 2) & ~hi1, "Y": (terc == 2) & hi1}
        cells["rest"] = ~(cells["X"] | cells["Y"])
        desc = {}
        for nm, m in cells.items():
            x = mr[m]
            desc[nm] = {"n": int(m.sum()), "stop_share": float((x["why"] == "stop").mean()),
                        "close_share": float((x["why"] == "close").mean()), "mfe_bp": float(x["mfe"].mean()),
                        "mae_bp": float(x["mae"].mean()), "hold_close_bp": float(x["hold_close"].mean()),
                        "pre_entry_range_share": float(x["pre_share"].mean()), "entry_minute": float(x["entry_min"].mean()),
                        "gross_bp": float(a["t1"][1][m].mean())}
        hx = mr.loc[cells["X"], "hold_close"].to_numpy(float)
        t_hold = D.nw_t(hx)[0]
        t_mfe, _ = P.welch(mr.loc[cells["X"], "mfe"].to_numpy(float), mr.loc[cells["Y"], "mfe"].to_numpy(float))
        reading = "REVERSAL" if (hx.mean() < 0 and t_hold <= -2) else ("SPENT RANGE" if t_mfe <= -2 else "NEITHER")
        mech[r] = {"cells": desc, "X_hold_close_t_hac": t_hold, "X_vs_Y_mfe_welch_t": t_mfe, "reading": reading}
    a1_pass = S_obs < a1["p5"]
    a2_pass = S_obs < a2["p5"]
    c_pass = c0w < cc["p5"]
    verdict = "SEARCH ARTEFACT" if not a1_pass else ("LEAD SURVIVES" if c_pass else "CONSTRUCTION-SPECIFIC")
    out.update({
        "A": {"S_observed": S_obs, "argmin_cell_tercile_half": argmin, "argmin_is_X": argmin == list(X_CELL),
              "joint_z_grid": j1.tolist(), "per_root_z_grid": {r: z.tolist() for r, z in zip(ROOTS, z1)},
              "A1_whole_label": {**a1, "pass": bool(a1_pass)}, "A2_ingredient": {**a2, "pass": bool(a2_pass)},
              "label": "IV information" if a2_pass else "the label's realised part"},
        "B": mech,
        "C": {"X_joint_z": c0w, "C_i_X_is_jointly_worst": c_argmin == list(X_CELL), "argmin_cell": c_argmin,
              "joint_z_grid": j2.tolist(), "per_root_z_grid": {r: z.tolist() for r, z in zip(ROOTS, z2)},
              "C_ii_null": {**cc, "pass": bool(c_pass)},
              "per_root_X_mean_F_bp": {r: float(w[r]["t2"][1][(w[r]["t2"][2] == 2) & (C.tiers(w[r]["ivrv"])[w[r]["t2"][0]] < 0.5)].mean()) for r in ROOTS},
              "per_root_X_n": {r: int(((w[r]["t2"][2] == 2) & (C.tiers(w[r]["ivrv"])[w[r]["t2"][0]] < 0.5)).sum()) for r in ROOTS}},
        "verdict": verdict,
        "predictions": {"1_A1_passes": bool(a1_pass), "2_A2_fails": not a2_pass,
                        "3_B_spent_range_both": all(mech[r]["reading"] == "SPENT RANGE" for r in ROOTS),
                        "4_C_ii_fails": not c_pass},
        "rotation_wall_s": round(wall, 1), "runtime_min": round((time.time() - t0) / 60, 2),
        "deviations": ["D694's grid dropped ctier == 1.0 sessions from its top band (ct < 1); D696 uses its declared "
                       "ctier >= 2/3, and the trades that adds are reported per root"]})
    return out


# ================================================================================ selftest
def selftest() -> int:
    fired: list[str] = []

    def must_raise(name: str, fn: Callable[[], Any]) -> None:
        try:
            fn()
        except (D696Error, C.D671Error):
            fired.append(name)
            return
        raise SystemExit(f"selftest: the {name} canary did not raise")

    sign_audit()
    rng = np.random.default_rng(696)
    m = np.arange(570, 960, dtype=float)
    p = 100 + np.cumsum(rng.normal(0, 0.05, len(m)))
    h, l = p + rng.random(len(m)) * 0.05, p - rng.random(len(m)) * 0.05
    i, D_, e = 120, 1, float(p[120])
    h[i] = p.max() + 5.0      # the entry bar carries the day's high: an MFE that reads it must differ
    l[i + 1] = p.min() - 5.0  # the bar after entry carries the day's low: a pre-entry share that reads it must differ
    bb = {"m": m, "o": p, "h": h, "l": l, "c": p}
    mechanism_audit(bb, i, D_, e, mechanism(bb, i, D_, e))
    must_raise("an MFE that reads the entry bar", lambda: mechanism_audit(bb, i, D_, e, mechanism(bb, i, D_, e, include_entry=True)))
    must_raise("a pre-entry share that reads one bar past the entry",
               lambda: mechanism_audit(bb, i, D_, e, mechanism(bb, i, D_, e, past_entry=True)))
    x = rng.normal(size=600)
    must_raise("a tier that ranks its own value", lambda: C.tier_audit(C.tiers(x, leak=True), x, list(range(300, 600, 40))))
    # the rotation: offset 0, processes == serial, and destruction of an injected cell
    n = 900
    w: dict[str, Any] = {}
    for r in ROOTS:
        ivrv = rng.normal(size=n)
        ivrv[:20] = np.nan
        lab = pd.DataFrame({"lniv": ivrv + rng.normal(size=n) * 0.3, "lnrv": rng.normal(size=n), "rv5": rng.normal(size=n),
                            "on_range": rng.normal(size=n), "lnatr": rng.normal(size=n), "ivrv": ivrv})
        u, F, _ = P.residual(lab, np.ones(n, bool))
        pact = C.tiers(ivrv)
        pos = np.sort(rng.choice(np.arange(300, n), 400, replace=False))
        terc = rng.integers(0, 3, 400)
        g = rng.normal(size=400) - 3.0 * ((terc == 2) & (pact[pos] < 0.5))
        w[r] = {"ivrv": ivrv, "u": u, "F": F, "t1": (pos, g, terc, float(g.std(ddof=1))), "t2": (pos, g, terc, float(g.std(ddof=1)))}
    s0, c0 = stats_at(0, "whole", w)
    zs = [cell_z(w[r]["t1"][1], w[r]["t1"][2], (C.tiers(w[r]["ivrv"])[w[r]["t1"][0]] >= 0.5).astype(int), np.ones(400, bool), w[r]["t1"][3]) for r in ROOTS]
    if float(np.nanmin(joint(zs))) != s0 or stats_at(0, "ingredient", w) != (s0, c0):
        raise SystemExit("selftest: offset 0 does not reproduce the statistic")
    items = [("whole", 21), ("whole", 40), ("ingredient", 21), ("ingredient", 33)]
    serial = {it: stats_at(it[1], it[0], w) for it in items}
    par = rotations(w, items, 2)
    if any(serial[it] != par[it] for it in items):
        raise SystemExit("selftest: the rotation's processes differ from the serial run")
    if min(v[1] for v in serial.values()) <= c0:
        raise SystemExit("selftest: rotating an injected cell does not destroy it")
    print(f"selftest: {len(fired)} canaries fired: {fired}; checks passed: sign, the mechanism's second path, offset 0, "
          "processes == serial, rotation destroys an injected cell. The known answers (D694's grid, D663's F, the "
          "re-derived E4 trades) need the fixtures and run in --run.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--time", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 4))
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.time:
        build(a.workers, time_only=True)
        return 0
    if not a.run:
        ap.print_help()
        return 1
    if OUT.exists():
        raise D696Error(f"{OUT.name} exists: D696 runs once")
    out = build(a.workers)
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: out[k] for k in ("verdict", "predictions")}, indent=1))
    print(json.dumps({"A": {k: out["A"][k] for k in ("S_observed", "argmin_is_X", "A1_whole_label", "A2_ingredient")},
                      "C": {k: out["C"][k] for k in ("X_joint_z", "C_i_X_is_jointly_worst", "C_ii_null", "per_root_X_mean_F_bp", "per_root_X_n")},
                      "B": {r: {"reading": out["B"][r]["reading"], "X": out["B"][r]["cells"]["X"], "Y": out["B"][r]["cells"]["Y"]} for r in ROOTS}},
                     indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
