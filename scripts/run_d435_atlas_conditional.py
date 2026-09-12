"""D435 -- the conditional volume atlas. Spec docs/decisions/D435-the-conditional-volume-atlas.md (committed BEFORE this
file, R8). A MEASUREMENT: it admits nothing (R15).

    uv run python scripts/run_d435_atlas_conditional.py --selftest
    uv run python scripts/run_d435_atlas_conditional.py --run --half a|b     a = price, mom conditioners;  b = vol, ret20

Draw, score, summarise: D392's. Volume features and the shift: D434's. New here: the state x feature pools and [M].
"""
from __future__ import annotations
import argparse, importlib.util, json, sys, time
from pathlib import Path
import numpy as np

REPO = Path(__file__).resolve().parents[1]
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m
A92 = _load("d392", "run_d392_base_rate_atlas.py"); A34 = _load("d434", "run_d434_atlas_volume.py")
draw_mask, score_once, summarise, eligible_index, cell_key = A92.draw_mask, A92.score_once, A92.summarise, A92.eligible_index, A92.cell_key
SEED, DRAWS, CAP, SIDES = A92.SEED, A92.DRAWS_COND, A92.COND_CAP, A92.SIDES

CONDS = {"a": ["price", "mom"], "b": ["vol", "ret20"]}
LEVELS = ("lo", "mid", "hi")
FEATS_TERC = ["rv_lo", "rv_hi", "uv_lo", "uv_hi", "ef_lo", "ef_hi"]
FEATS_ABS = ["rv_x3", "cx_dn"]
N_TERC, N_ABS = 10_000, 3_000
OUT = {"a": REPO / "data" / "d435_atlas_cond_a.json", "b": REPO / "data" / "d435_atlas_cond_b.json"}


def shift(m, elig):
    s = np.zeros_like(m); s[1:] = m[:-1]; return s & elig


def state_pools_unshifted(P, elig):
    """price / vol / mom from D392's tercile_pools; ret20 from D434's features. All at the bar the feature is complete."""
    out = dict(A92.tercile_pools(P, elig))
    F = A34.features(P)
    A34.tercile(F["ret20"], elig, "ret20", out)
    return {k: v for k, v in out.items() if k.split("_")[0] in ("price", "vol", "mom", "ret20")}


def conditional_pools(P, elig, conds, shift_=True):
    """(state ∩ feature) for every state of the requested conditioners and every volume feature; shifted to t+1."""
    st = state_pools_unshifted(P, elig); vp, _ = A34.volume_pools_unshifted(P, elig)
    out = {}
    for c in conds:
        for lv in LEVELS:
            s = st[f"{c}_{lv}"]
            for f in FEATS_TERC + FEATS_ABS:
                m = s & vp[f]
                out[f"{c}_{lv}|{f}"] = shift(m, elig) if shift_ else m
    return out, st, vp


def assert_F(P, elig, pools, conds):
    un, _, _ = conditional_pools(P, elig, conds, shift_=False)
    for k in pools:
        assert not pools[k][0].any(), f"[F] {k} has events on bar 0"
        assert np.array_equal(pools[k][1:], un[k][:-1] & elig[1:]), f"[F] {k} is not the t-1 state-and-feature placed at t"


def assert_T(st, vp, elig, conds):
    for c in conds:
        for lv in LEVELS:
            s = st[f"{c}_{lv}"]
            for nm in ("rv", "uv", "ef"):
                lo, mid, hi = s & vp[f"{nm}_lo"], s & vp[f"{nm}_mid"], s & vp[f"{nm}_hi"]
                assert not (lo & mid).any() and not (lo & hi).any() and not (mid & hi).any(), f"[T] {c}_{lv} x {nm} overlap"
                cov = (lo | mid | hi); defined = s.any(axis=1)
                # within a state, the volume terciles (built on the whole cross-section) need not cover every state cell
                # (a cell with an undefined feature is in none), but they must cover >= 90% of the state's cells on defined bars
                assert cov[defined].sum() >= 0.9 * s[defined].sum(), f"[T] {c}_{lv} x {nm} covers < 90% of the state"


def assert_M(pools, vp, st, elig, conds):
    """[M] the union over a conditioner's three states of (state ∩ feature) equals the marginal feature pool (shifted),
    restricted to bars on which the conditioner is defined."""
    for c in conds:
        defined = (st[f"{c}_lo"] | st[f"{c}_mid"] | st[f"{c}_hi"]).any(axis=1)
        for f in FEATS_TERC + FEATS_ABS:
            u = pools[f"{c}_lo|{f}"] | pools[f"{c}_mid|{f}"] | pools[f"{c}_hi|{f}"]
            marg = shift(vp[f] & (st[f"{c}_lo"] | st[f"{c}_mid"] | st[f"{c}_hi"]), elig)
            assert np.array_equal(u, marg), f"[M] {c} x {f}: the three states do not decompose the marginal"


def selftest():
    print("D435 SELF-TEST -- states x features partition, decompose the marginal, and sit one bar before the fill\n")
    rng = np.random.default_rng(5); T, N = 400, 80
    CLOSE = np.exp(np.cumsum(rng.normal(0, 0.02, (T, N)), axis=0)) * 50; VOL = rng.lognormal(12, 0.6, (T, N)); DV = CLOSE * VOL
    rv = np.full((N, T), 0.02); mom = np.cumsum(rng.normal(0, 0.05, (N, T)), axis=1)
    elig = np.ones((T, N), bool); elig[:300] = False
    P = dict(VOL=VOL, CLOSE=CLOSE, DV=DV, score=lambda nm: {"rvol21": rv, "mom_252_21": mom}[nm])
    conds = ["price", "mom", "vol", "ret20"]
    pools, st, vp = conditional_pools(P, elig, conds); assert_T(st, vp, elig, conds); assert_F(P, elig, pools, conds); assert_M(pools, vp, st, elig, conds)
    raised = False
    try:
        un, _, _ = conditional_pools(P, elig, conds, shift_=False); assert_F(P, elig, un, conds)
    except AssertionError as e:
        raised = "[F]" in str(e)
    assert raised, "[X] THE SELF-TEST CANNOT FAIL -- unshifted state pools passed [F]"
    bad = dict(pools); bad["price_lo|rv_lo"] = bad["price_lo|rv_lo"] & ~bad["price_lo|rv_lo"]   # empty one part of a decomposition
    raised = False
    try:
        assert_M(bad, vp, st, elig, ["price"])
    except AssertionError as e:
        raised = "[M]" in str(e)
    assert raised, "[X] THE SELF-TEST CANNOT FAIL -- a broken decomposition passed [M]"
    print("    [T] [F] [M] hold on a synthetic panel;  [X] unshifted pools ARE CAUGHT by [F];  [X] a broken decomposition IS CAUGHT by [M]\n\nSELF-TEST PASSED\n"); return 0


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true"); ap.add_argument("--run", action="store_true"); ap.add_argument("--half", default="a", choices=["a", "b"])
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
    conds = CONDS[a.half]
    tp = time.time(); pools, st, vp = conditional_pools(P, elig, conds); assert_T(st, vp, elig, conds); assert_F(P, elig, pools, conds); assert_M(pools, vp, st, elig, conds)
    print(f"  prep {time.time()-t0:.0f}s | [K] | half {a.half} conditioners {conds}: {len(pools)} pools in {time.time()-tp:.0f}s; [T] [F] [M] on the real panel", flush=True)
    for k in sorted(pools):
        print(f"    {k:22s} {int(pools[k].sum()):9,} cells", flush=True)
    out = OUT[a.half]
    atlas = json.loads(out.read_text()) if out.exists() else {"study": 435, "spec": "docs/decisions/D435-the-conditional-volume-atlas.md", "build": "D392's kernel and draw; D434's features; state x feature pools shifted to t+1",
                                                               "statistic": "gross mean per trade, bp; hedged; no cost", "seed": SEED, "cells": {}}
    cells = [dict(kind="cond2", n=(N_ABS if f in FEATS_ABS else N_TERC), cap=CAP, side=s, pool=f"{c}_{lv}|{f}", conc=1.0, draws=DRAWS)
             for c in conds for lv in LEVELS for f in FEATS_TERC + FEATS_ABS for s in SIDES]
    cells.sort(key=lambda c: c["n"])
    print(f"\n  half {a.half}: {len(cells)} cells, {sum(1 for c in cells if cell_key(c['kind'], c['n'], c['cap'], c['side'], c['pool'], c['conc']) in atlas['cells'])} present -- resuming", flush=True)
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
            atlas["cells"][key] = dict(status="EMPTY", reason="pool too small", skipped=skipped, pool_cells=int(pool_idx.size), n=c["n"], side=c["side"], pool=c["pool"])
        else:
            cell = summarise(vals, trades, np.random.default_rng([SEED, 7, ci])); cell.update(kind=c["kind"], n=c["n"], cap=c["cap"], side=c["side"], pool=c["pool"], conc=1.0, seconds=time.time() - t1, skipped=skipped, pool_cells=int(pool_idx.size))
            atlas["cells"][key] = cell
        out.write_text(json.dumps(atlas, indent=1))
        cc = atlas["cells"][key]
        if cc.get("status") == "EMPTY":
            print(f"    [{ci+1}/{len(cells)}] {key}  EMPTY ({cc['pool_cells']:,} cells in pool)", flush=True)
        else:
            print(f"    [{ci+1}/{len(cells)}] n={c['n']:<6,} {c['side']:<5s} {c['pool']:<20s} p50 {cc['p50']:+7.2f}  p95 {cc['p95']:+7.2f} +/- {cc['se_p95']:.2f}  ({cc['trades_mean']:,.0f} trades, {cc['seconds']:.0f}s)", flush=True)
    print(f"  [P] {out.relative_to(REPO)} written incrementally ({(time.time()-t0)/60:.0f} min)\n\nThis is a MEASUREMENT. It admits nothing (R15)."); return 0


if __name__ == "__main__":
    sys.exit(main())
