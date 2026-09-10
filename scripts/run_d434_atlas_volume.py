"""D434 -- the volume axes of the base-rate atlas. Spec docs/decisions/D434-the-volume-axes-of-the-base-rate-atlas.md
(committed BEFORE this file, R8). A MEASUREMENT: it admits nothing (R15).

    uv run python scripts/run_d434_atlas_volume.py --selftest
    uv run python scripts/run_d434_atlas_volume.py --run --half a|b|all     two halves of the pool list, each to its own artefact

Everything that draws, scores and summarises is D392's own code, imported; only the POOLS are new.
"""
from __future__ import annotations
import argparse, importlib.util, json, sys, time
from pathlib import Path
import numpy as np

REPO = Path(__file__).resolve().parents[1]
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m
A92 = _load("d392", "run_d392_base_rate_atlas.py")
draw_mask, score_once, summarise, eligible_index, cell_key = A92.draw_mask, A92.score_once, A92.summarise, A92.eligible_index, A92.cell_key
SEED, DRAWS, COUNTS, CAP, SIDES = A92.SEED, A92.DRAWS_COND, A92.COND_COUNTS, A92.COND_CAP, A92.SIDES

POOLS_A = ["rv_lo", "rv_mid", "rv_hi", "rv_x3", "ef_lo", "ef_mid", "ef_hi", "cx_dn", "cx_up", "vt_lo", "vt_mid"]
POOLS_B = ["vt_hi", "uv_lo", "uv_mid", "uv_hi", "dv_lo", "dv_mid", "dv_hi", "pv_up_rise", "pv_up_fall", "pv_dn_rise", "pv_dn_fall"]
OUT = {"a": REPO / "data" / "d434_atlas_volume_a.json", "b": REPO / "data" / "d434_atlas_volume_b.json"}


# ------------------------------------------------------------------ the features (causal at the close of t)
def trailing_mean(V, w, end_excl=True):
    """mean over bars t-w..t-1 (end_excl) or t-w+1..t; NaN until w bars exist. Pure numpy, no future bar."""
    X = np.where(np.isfinite(V), V, 0.0); C = np.isfinite(V).astype(float)
    cs = np.cumsum(X, axis=0); cc = np.cumsum(C, axis=0)
    out = np.full_like(V, np.nan, dtype=float)
    if end_excl:
        s = cs[w - 1:-1] - np.concatenate([np.zeros((1, V.shape[1])), cs[:-w - 1]], axis=0) if False else None
    # explicit, readable window sums
    for t in range(V.shape[0]):
        lo, hi = (t - w, t) if end_excl else (t - w + 1, t + 1)
        if lo < 0:
            continue
        num = cs[hi - 1] - (cs[lo - 1] if lo > 0 else 0.0); den = cc[hi - 1] - (cc[lo - 1] if lo > 0 else 0.0)
        with np.errstate(invalid="ignore", divide="ignore"):
            out[t] = np.where(den >= 0.8 * w, num / den, np.nan)
    return out


def features(P, peek=False):
    VOL = np.asarray(P["VOL"], float); CLOSE = np.asarray(P["CLOSE"], float); DV = np.asarray(P["DV"], float)
    if peek:                                     # the deliberate break for [X]: a feature that reads the NEXT bar's volume
        VOL = np.roll(VOL, -1, axis=0)
    rvol = np.asarray(P["score"]("rvol21"), float).T
    assert VOL.shape == CLOSE.shape == DV.shape == rvol.shape, f"[SHAPE] {VOL.shape} {CLOSE.shape} {DV.shape} {rvol.shape}"
    T, N = VOL.shape
    lg = np.log(np.where(CLOSE > 0, CLOSE, np.nan))
    r1 = np.full_like(lg, np.nan); r1[1:] = lg[1:] - lg[:-1]
    ret20 = np.full_like(lg, np.nan); ret20[20:] = lg[20:] - lg[:-20]
    adv20 = trailing_mean(VOL, 20); adv5 = trailing_mean(VOL, 5); adv60 = trailing_mean(VOL, 60)
    with np.errstate(invalid="ignore", divide="ignore"):
        rv = VOL / adv20
        ef = rv / (np.abs(r1) / rvol + 0.1)
        vt = adv5 / adv60
        up = np.where(r1 > 0, VOL, 0.0); upv = trailing_mean(np.where(np.isfinite(r1), up, np.nan), 20, end_excl=False); allv = trailing_mean(np.where(np.isfinite(r1), VOL, np.nan), 20, end_excl=False)
        uv = upv / allv
        zr = r1 / rvol
    return dict(rv=rv, ef=ef, vt=vt, uv=uv, dv=DV, ret20=ret20, zr=zr)


def tercile(grid, elig, nm, out):
    lo = np.zeros_like(elig); mid = np.zeros_like(elig); hi = np.zeros_like(elig)
    for t in range(elig.shape[0]):
        col = elig[t] & np.isfinite(grid[t])
        if col.sum() < 30:
            continue
        v = grid[t, col]; a, b = np.quantile(v, [1 / 3, 2 / 3]); j = np.flatnonzero(col)
        lo[t, j[v <= a]] = True; hi[t, j[v >= b]] = True; mid[t, j[(v > a) & (v < b)]] = True
    out[f"{nm}_lo"], out[f"{nm}_mid"], out[f"{nm}_hi"] = lo, mid, hi


def median_split(grid, elig):
    above = np.zeros_like(elig); below = np.zeros_like(elig)
    for t in range(elig.shape[0]):
        col = elig[t] & np.isfinite(grid[t])
        if col.sum() < 30:
            continue
        v = grid[t, col]; m = np.median(v); j = np.flatnonzero(col)
        above[t, j[v > m]] = True; below[t, j[v <= m]] = True
    return above, below


def volume_pools_unshifted(P, elig, peek=False):
    """Pools on the bar the FEATURE is complete (close of t). NOT what the kernel needs -- see volume_pools."""
    F = features(P, peek=peek); out = {}
    for nm in ("rv", "ef", "vt", "uv", "dv"):
        tercile(F[nm], elig, nm, out)
    fin = lambda g: np.isfinite(g)
    out["rv_x3"] = elig & fin(F["rv"]) & (F["rv"] >= 3)
    out["cx_dn"] = elig & fin(F["rv"]) & fin(F["zr"]) & (F["rv"] >= 3) & (F["zr"] <= -2)
    out["cx_up"] = elig & fin(F["rv"]) & fin(F["zr"]) & (F["rv"] >= 3) & (F["zr"] >= 2)
    r_up, r_dn = median_split(F["ret20"], elig); v_rise, v_fall = median_split(F["vt"], elig)
    out["pv_up_rise"], out["pv_up_fall"] = r_up & v_rise, r_up & v_fall
    out["pv_dn_rise"], out["pv_dn_fall"] = r_dn & v_rise, r_dn & v_fall
    for k, m in out.items():
        assert not (m & ~elig).any(), f"[E] pool {k} leaves the eligible mask"
    return out, F


def volume_pools(P, elig, peek=False, shift=True):
    """ADDENDUM: the kernel enters an event placed at bar t at the OPEN of t (D340: signal from the close of t-1), so a pool
    computed from bar t's own volume and return must be placed at t+1. mask[t] = unshifted[t-1], re-ANDed with elig."""
    un, F = volume_pools_unshifted(P, elig, peek=peek)
    if not shift:
        return un, F
    out = {}
    for k, m in un.items():
        s = np.zeros_like(m); s[1:] = m[:-1]; out[k] = s & elig
    return out, F


def assert_F(P, elig, pools):
    """[F] fill alignment: every pool at t equals the unshifted pool at t-1 (on eligible cells), and row 0 is empty."""
    un, _ = volume_pools_unshifted(P, elig)
    for k in pools:
        assert not pools[k][0].any(), f"[F] pool {k} has events on bar 0"
        assert np.array_equal(pools[k][1:], un[k][:-1] & elig[1:]), f"[F] pool {k} is not the t-1 feature placed at t"


def assert_T(pools, elig):
    for nm in ("rv", "ef", "vt", "uv", "dv"):
        lo, mid, hi = pools[f"{nm}_lo"], pools[f"{nm}_mid"], pools[f"{nm}_hi"]
        assert not (lo & mid).any() and not (lo & hi).any() and not (mid & hi).any(), f"[T] {nm} terciles overlap"
        defined = (lo | mid | hi).any(axis=1)
        assert np.all((lo | mid | hi)[defined].sum(axis=1) >= 30), f"[T] {nm} a defined bar has < 30 cells"


def assert_C(P, elig, pools, peek=False):
    """[C] causality against the FILL: an event placed at t is filled at t's open, so perturbing VOL and CLOSE at bars >= t0
    must leave every pool at or before t0 unchanged; perturbing bar t0-1 (one name's volume) must change some pool at t0.
    t0 is an ELIGIBLE bar in the middle of the eligible span."""
    el_bars = np.flatnonzero(elig.any(axis=1)); t0 = int(el_bars[len(el_bars) // 2])
    Q = dict(P); VOL = np.array(P["VOL"], float); CL = np.array(P["CLOSE"], float)
    V2, C2 = VOL.copy(), CL.copy(); V2[t0:] *= 7.0; C2[t0:] *= 1.3
    Q["VOL"], Q["CLOSE"] = V2, C2
    p2, _ = volume_pools(Q, elig, peek=peek)
    for k in pools:
        assert np.array_equal(pools[k][:t0 + 1], p2[k][:t0 + 1]), f"[C] pool {k} at or before t0 changed when bars from t0 on were perturbed -- it reads the fill bar"
    j = int(np.flatnonzero(elig[t0])[0]); V3 = VOL.copy(); V3[t0 - 1, j] *= 50.0; Q["VOL"], Q["CLOSE"] = V3, CL
    p3, _ = volume_pools(Q, elig, peek=peek)
    assert any(not np.array_equal(pools[k][t0], p3[k][t0]) for k in ("rv_lo", "rv_mid", "rv_hi", "rv_x3")), "[C] perturbing bar t0-1's volume changed nothing at t0 -- the check cannot fail"


def selftest():
    print("D434 SELF-TEST -- the features are causal and the terciles partition\n")
    rng = np.random.default_rng(3); T, N = 120, 60
    CLOSE = np.exp(np.cumsum(rng.normal(0, 0.02, (T, N)), axis=0)) * 50; VOL = rng.lognormal(12, 0.6, (T, N)); DV = CLOSE * VOL
    rvol = np.full((N, T), 0.02); elig = np.ones((T, N), bool); elig[:65] = False
    P = dict(VOL=VOL, CLOSE=CLOSE, DV=DV, score=lambda nm: rvol)
    pools, F = volume_pools(P, elig); assert_T(pools, elig); assert_C(P, elig, pools); assert_F(P, elig, pools)
    # [X] break 1: a feature that reads the NEXT bar's volume must be caught by [C]
    raised = False
    try:
        pk, _ = volume_pools(P, elig, peek=True); assert_C(P, elig, pk, peek=True)
    except AssertionError as e:
        raised = "[C]" in str(e)
    assert raised, "[X] THE SELF-TEST CANNOT FAIL -- a pool that depends on the next bar passed [C]"
    # [X] break 2: the UNSHIFTED pools (the first run's error -- placed on the bar the kernel fills) must be caught by [C] and by [F]
    un, _ = volume_pools(P, elig, shift=False); raised_c = raised_f = False
    try:
        assert_C(P, elig, un)
    except AssertionError as e:
        raised_c = "[C]" in str(e)
    try:
        assert_F(P, elig, un)
    except AssertionError as e:
        raised_f = "[F]" in str(e)
    assert raised_c and raised_f, "[X] THE SELF-TEST CANNOT FAIL -- pools placed on the fill bar passed [C] or [F]"
    print("    [T] terciles partition every defined bar;  [C] no pool at t reads the fill bar or later, and a perturbation at t-1 moves it;  [F] every pool is the t-1 feature placed at t;\n"
          "    [X] a next-bar dependence IS CAUGHT by [C];  [X] the first run's unshifted pools ARE CAUGHT by [C] and by [F]")
    print("\nSELF-TEST PASSED\n"); return 0


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true"); ap.add_argument("--run", action="store_true"); ap.add_argument("--half", default="all", choices=["a", "b", "all"])
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.run:
        ap.error("pass --selftest or --run")
    selftest(); t0 = time.time()
    PREP = _load("d348p", "d348_prep.py"); V59 = _load("d359r", "run_d359_loser_rally_short.py")
    P = PREP.prep(need_grids=True); T, N = P["T"], P["n"]; elig = np.asarray(P["elig"]); idx = eligible_index(elig); sc = np.full((T, N), 50.0)
    mk = draw_mask(np.random.default_rng(SEED), idx, (T, N), 2_000); r1 = V59.run_mirror(P, mk, sc, "cap", 20); m1, c1 = score_once(V59, P, mk, 20, "long", sc)
    assert abs(m1 - float(V59.V47.pnl_bp(r1).mean())) < 1e-12 and c1 == len(r1["trades"]), "[K]"
    print(f"  prep {time.time()-t0:.0f}s | {N} names x {T} bars | {idx.size:,} eligible cells | [K] score_once == run_d359's path", flush=True)
    tp = time.time(); pools, F = volume_pools(P, elig); assert_T(pools, elig); assert_C(P, elig, pools); assert_F(P, elig, pools)
    print(f"  22 volume pools built in {time.time()-tp:.0f}s; [T] [C] [F] on the real panel (ADDENDUM: pools placed at t+1, filled at t+1's open)", flush=True)
    for k in POOLS_A + POOLS_B:
        print(f"    {k:11s} {int(pools[k].sum()):9,} cells", flush=True)
    halves = ["a", "b"] if a.half == "all" else [a.half]
    for h in halves:
        out = OUT[h]; names = POOLS_A if h == "a" else POOLS_B
        atlas = json.loads(out.read_text()) if out.exists() else {"study": 434, "spec": "docs/decisions/D434-the-volume-axes-of-the-base-rate-atlas.md",
                                                                   "build": "D392's kernel and draw; pools from VOL/DV/CLOSE/rvol21", "statistic": "gross mean per trade, bp; hedged; no cost", "seed": SEED, "cells": {}}
        cells = [dict(kind="cond", n=n, cap=CAP, side=s, pool=p, conc=1.0, draws=DRAWS) for n in COUNTS for p in names for s in SIDES]
        cells.sort(key=lambda c: c["n"])
        print(f"\n  half {h}: {len(cells)} cells, {sum(1 for c in cells if cell_key(c['kind'], c['n'], c['cap'], c['side'], c['pool'], c['conc']) in atlas['cells'])} present -- resuming", flush=True)
        for ci, c in enumerate(cells):
            key = cell_key(c["kind"], c["n"], c["cap"], c["side"], c["pool"], c["conc"])
            if key in atlas["cells"]:
                continue
            pool_idx = np.flatnonzero(pools[c["pool"]].ravel())
            rng = np.random.default_rng([SEED, c["n"], c["cap"], hash(c["side"]) % 97, hash(c["pool"]) % 97])
            vals, trades, t1, skipped = [], [], time.time(), 0
            for d in range(c["draws"]):
                m = draw_mask(rng, idx, (T, N), c["n"], name_pool=pool_idx)
                if m is None:
                    skipped += 1; continue
                assert not (m & ~elig).any(), "[E]"
                mu, ntr = score_once(V59, P, m, c["cap"], c["side"], sc)
                if mu is not None:
                    vals.append(mu); trades.append(ntr)
            if not vals:
                atlas["cells"][key] = dict(status="EMPTY", reason="pool too small", skipped=skipped, pool_cells=int(pool_idx.size))
            else:
                cell = summarise(vals, trades, np.random.default_rng([SEED, 7, ci])); cell.update(kind=c["kind"], n=c["n"], cap=c["cap"], side=c["side"], pool=c["pool"], conc=1.0, seconds=time.time() - t1, skipped=skipped, pool_cells=int(pool_idx.size))
                atlas["cells"][key] = cell
            out.write_text(json.dumps(atlas, indent=1))
            cc = atlas["cells"][key]
            if cc.get("status") == "EMPTY":
                print(f"    [{ci+1}/{len(cells)}] {key}  EMPTY ({cc['pool_cells']:,} cells in pool)", flush=True)
            else:
                print(f"    [{ci+1}/{len(cells)}] n={c['n']:<6,} {c['side']:<5s} {c['pool']:<11s} p50 {cc['p50']:+7.2f}  p95 {cc['p95']:+7.2f} +/- {cc['se_p95']:.2f}  ({cc['trades_mean']:,.0f} trades, {cc['seconds']:.0f}s)", flush=True)
        print(f"  [P] {out.relative_to(REPO)} written incrementally ({(time.time()-t0)/60:.0f} min so far)", flush=True)
    print("\nThis is a MEASUREMENT. It admits nothing (R15)."); return 0


if __name__ == "__main__":
    sys.exit(main())
