"""Gate 1h: nulls for BOTH directions of the spread, in one pass.

    uv run python scripts/d290_direction_nulls.py [--draws 100] [--workers 6]
    uv run python scripts/d290_direction_nulls.py --selftest

WHY IT IS NEEDED. `spread(-s) = -spread(s)` exactly, so the reversed direction's
POINT ESTIMATE is free. Its NULL is not: the best-of-grid statistic is asymmetric,
`max(-t) != -max(t)`. D290 scored one direction and priced neither, leaving 29 of
51 reaching |t| >= 2 reversed and 18 of those capturable — the largest untested
block in the study.

ONE PASS SERVES BOTH. Under a given draw the reversed grid is the exact negation
of the forward grid, so recording `max(t)` AND `min(t)` per draw gives the forward
null and the reversed null together. The reversed direction costs nothing extra
once the pass is run at all.

--------------------------------------------------------------------------
THREE EXACT OPTIMISATIONS. Hoisting and skipping only -- no float is reordered.
Measured baseline, per draw per candidate per null: 822 ms.

  rank_columns 297  bar_sums 283  legs 154  rotate 89

1. THE PERMUTATION NULL NEEDS NO SORT. Shuffling the score across names inside a
   bar leaves the same multiset, so the shuffled ranking IS the observed ranking
   with rows permuted -- and the resulting BOOK is a uniform random N-subset of
   that bar's finite names. Drawing iid uniform keys and taking the smallest 2N
   by `argpartition` gives exactly that, in O(n) rather than O(n log n), with no
   ties to break because random floats do not collide.

2. ONE GATHER, NOT TWELVE. `bar_sums` re-gathered `f[rows, cols]` once per
   horizon when the row and column indices are identical across horizons. The
   twelve horizon grids are stacked into one array and gathered once.

3. `rotate` WAS A PYTHON LOOP over 1,573 symbols. It is now a single fancy index
   through a precomputed per-symbol offset map.

--------------------------------------------------------------------------
AND A REPRODUCIBILITY DEFECT, FOUND WHILE OPTIMISING AND FIXED HERE.

`run_stage1_rerun` seeded each candidate with `SEED + hash(c) % 100000`. **Python
randomises `hash()` per process**, so two runs of D290 drew different rotations:

    hash("close_in_range") = 45078138007182838   (one process)
                             5916037220325522427 (the next)

D290's z-values are VALID -- the draws were legitimate random rotations -- but
they are NOT REPRODUCIBLE. This file uses `zlib.crc32`, which is stable across
processes, so its nulls can be regenerated exactly.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
import zlib
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


M = _load("run_mine_neutral", "run_mine_neutral.py")
BC = _load("d290_build_cache", "d290_build_cache.py")
B, C, FN = M.B, M.C, M.FN

OUT = REPO / "data" / "d290_direction_nulls.json"
S1 = json.loads((REPO / "data" / "d290_stage1.json").read_text())
NS = tuple(S1["n_levels"])
KS = tuple(S1["horizons"])
SEED = 20260902


def seed_for(name):
    """Stable across processes, unlike hash(). See the module docstring."""
    return SEED + (zlib.crc32(name.encode()) % 1_000_000)


def build_rot_index(live):
    """Per-symbol positions of each name's own live bars, for a vectorised roll."""
    return [np.flatnonzero(live[i]) for i in range(live.shape[0])]


def rotate(score, ats, off, out):
    """Roll each symbol's values within its own live bars, into a reused buffer."""
    out.fill(np.nan)
    for i, at in enumerate(ats):
        if at.size:
            out[i, at] = score[i, at[(np.arange(at.size) - off[i]) % at.size]]
    return out


def grid_minmax(order, cnt, FW, base_shape, T):
    """(max t, min t) over the N x horizon grid, from one ranking.

    ONE GATHER PER LEG. `FW` is the horizon-stacked forward-return array, so the
    row/column fancy index happens once instead of once per horizon.
    """
    mx, mn = -9e9, 9e9
    for N in NS:
        ev_lo, ev_hi, _ = M.legs_from_order(order, cnt, N, base_shape)
        lr, lc = np.nonzero(ev_lo)
        hr, hc = np.nonzero(ev_hi)
        if lr.size == 0 or hr.size == 0:
            continue
        VL = FW[:, lr, lc]          # (K, n_events) -- one gather
        VH = FW[:, hr, hc]
        for i in range(len(KS)):
            vl, vh = VL[i], VH[i]
            fl, fh = np.isfinite(vl), np.isfinite(vh)
            sl = np.bincount(lc[fl], weights=vl[fl].astype(np.float64), minlength=T)
            cl = np.bincount(lc[fl], minlength=T)
            sh = np.bincount(hc[fh], weights=vh[fh].astype(np.float64), minlength=T)
            ch = np.bincount(hc[fh], minlength=T)
            m = (cl > 0) & (ch > 0)
            if int(m.sum()) < M.MIN_BARS:
                continue
            d = sl[m] / cl[m] - sh[m] / ch[m]
            sd = d.std(ddof=1)
            if sd <= 0:
                continue
            t = float(d.mean() / (sd / np.sqrt(d.size)))
            mx = max(mx, t)
            mn = min(mn, t)
    return mx, mn


def perm_order(cnt, base, rng, T):
    """The permutation null's ranking, WITHOUT a sort. See optimisation 1."""
    keys = rng.random(base.shape, dtype=np.float32)
    keys[~base] = np.inf
    kth = min(2 * max(NS), base.shape[0] - 1)
    order = np.argpartition(keys, kth, axis=0)
    return order


def one(name, score, base, FW, ats, T, draws):
    rng = np.random.default_rng(seed_for(name))
    order, cnt = M.rank_columns(score, base)
    obs_mx, obs_mn = grid_minmax(order, cnt, FW, base.shape, T)
    buf = np.empty_like(score)
    nulls = {k: {"max": [], "min": []} for k in ("rotation", "permutation", "tail")}
    n = base.shape[0]
    for _ in range(draws):
        off = rng.integers(1, T, size=n)
        ro, rc = M.rank_columns(rotate(score, ats, off, buf), base)
        a, b = grid_minmax(ro, rc, FW, base.shape, T)
        nulls["rotation"]["max"].append(a)
        nulls["rotation"]["min"].append(b)

        po = perm_order(cnt, base, rng, T)
        a, b = grid_minmax(po, cnt, FW, base.shape, T)
        nulls["permutation"]["max"].append(a)
        nulls["permutation"]["min"].append(b)

        # TAIL-RANDOMISED reuses the OBSERVED ordering: the 2N most extreme names
        # are unchanged, only the side assignment is random. So it needs no sort.
        shuf = order.copy()
        top = 2 * max(NS)
        idx = rng.permuted(np.arange(top)[:, None].repeat(T, axis=1), axis=0)
        shuf[:top] = np.take_along_axis(order[:top], idx, axis=0)
        a, b = grid_minmax(shuf, cnt, FW, base.shape, T)
        nulls["tail"]["max"].append(a)
        nulls["tail"]["min"].append(b)

    out = {"observed": {"forward": obs_mx, "reversed": -obs_mn}, "z": {}}
    for k, v in nulls.items():
        fm = np.array([x for x in v["max"] if x > -8e9])
        rm = np.array([-x for x in v["min"] if x < 8e9])
        out["z"][k] = {
            "forward": (float((obs_mx - fm.mean()) / fm.std(ddof=1))
                        if fm.size > 4 and fm.std(ddof=1) > 0 else None),
            "reversed": (float((-obs_mn - rm.mean()) / rm.std(ddof=1))
                         if rm.size > 4 and rm.std(ddof=1) > 0 else None)}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=100)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    t0 = time.time()
    z = np.load(BC.CACHE, allow_pickle=False)
    assert str(z["key"]) == BC.cache_key(B.FIXTURE), "CACHE IS STALE -- rebuild"
    panel, _ = M.RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=B.FEE_BPS)
    live = panel.live
    base = z["warm"] & live
    T = live.shape[1]
    fwd = M.forward_returns(panel, live)
    FW = np.stack([fwd[k] for k in KS])
    ats = build_rot_index(live)
    print(f"loaded in {time.time() - t0:.0f}s | horizons stacked "
          f"{FW.nbytes / 1e6:.0f} MB", flush=True)

    if a.selftest:
        # The optimised rotate must equal the reference loop, exactly.
        s = z["close_in_range"]
        rng = np.random.default_rng(1)
        off = rng.integers(1, T, size=live.shape[0])
        ref = np.full(s.shape, np.nan)
        for i, at in enumerate(ats):
            if at.size:
                ref[i, at] = np.roll(s[i, at], int(off[i]))
        got = rotate(s, ats, off, np.empty_like(s))
        fr, fg = np.isfinite(ref), np.isfinite(got)
        assert np.array_equal(fr, fg), "rotate: NaN pattern moved"
        assert np.array_equal(ref[fr], got[fg]), "rotate: values differ"
        print("  [1] vectorised rotate == np.roll reference, bit-identical")
        t = time.time()
        one("close_in_range", s, base, FW, ats, T, 3)
        per = (time.time() - t) / 3 / 3
        print(f"  [2] {per * 1000:.0f} ms per draw per null "
              f"(baseline was 822) -> {per * 100 * 51 * 3 / 60:.0f} min serial, "
              f"~{per * 100 * 51 * 3 / 60 / 2.3:.0f} min at {a.workers} threads")
        return 0

    cands = list(BC.CANDIDATES)
    print(f"  {len(cands)} candidates x {a.draws} draws x 3 nulls x BOTH "
          f"directions | {a.workers} threads", flush=True)
    res = FN.parallel_map(
        lambda c, s: one(c, s, base, FW, ats, T, a.draws),
        [(c, z[c]) for c in cands], workers=a.workers, progress=True)

    rows = []
    for c, v in res.items():
        for d in ("forward", "reversed"):
            zs = [v["z"][k][d] for k in ("rotation", "permutation", "tail")]
            rows.append((c, d, v["observed"][d],
                         min(x for x in zs if x is not None) if all(
                             x is not None for x in zs) else None))
    rows.sort(key=lambda r: -(r[3] if r[3] is not None else -9e9))
    print(f"\n  {'candidate':16s} {'dir':9s} {'obs max t':>10s} {'min z':>7s}")
    for c, d, o, mz in rows[:20]:
        print(f"  {c:16s} {d:9s} {o:+10.2f} "
              + (f"{mz:+7.2f}" if mz is not None else f"{'--':>7s}"))
    rev = [r for r in rows if r[1] == "reversed" and r[3] is not None and r[3] > 0]
    print(f"\n  REVERSED direction with min z > 0 on all three nulls: {len(rev)}")

    OUT.write_text(json.dumps(
        {"purpose": "Gate 1h -- nulls for both directions of the spread. "
                    "spread(-s) = -spread(s) so the point estimate is free, but "
                    "max(-t) != -max(t) so the null is not.",
         "draws": a.draws, "seed": SEED, "seed_note": "zlib.crc32, stable across "
         "processes -- run_stage1_rerun used hash(), which Python randomises, so "
         "D290's nulls are valid but NOT reproducible",
         "results": res, "elapsed_s": round(time.time() - t0, 1)}, indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}   {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
