"""D392 -- the base-rate atlas: what a random event set of size n earns on this universe, and its p95.

    uv run python scripts/run_d392_base_rate_atlas.py --selftest
    uv run python scripts/run_d392_base_rate_atlas.py --calibrate          measure per-draw cost, project the grid, spend nothing
    uv run python scripts/run_d392_base_rate_atlas.py --run [--part uncond|cond|conc|all]
    uv run python scripts/run_d392_base_rate_atlas.py --lookup N CAP SIDE  read the built atlas

Spec: docs/decisions/D392-the-base-rate-atlas.md (committed BEFORE this file, R8).

A MEASUREMENT record's runner (D280's class). It scores no cell of any strategy, proposes no rule
and admits nothing (R15). It answers one question: **what does a random event set of size n, held
for cap bars, earn per trade on this universe -- and what is the p95 of that?**

WHY IT IS NEEDED, in one line: five candidates died in two days and not one died on cost. D391's
long paid +43.02 bp a trade and its own MIRROR paid +43.73, and nothing in the programme said in
advance what "the same thing" was.

WHAT "RANDOM" MEANS (spec section 3, and D291 paid for this lesson):
  * the draw is over ELIGIBLE (name, bar) cells -- the same mask observed events satisfy (D351) --
    and never the excluded tail that earns +226 to +318 bp and broke D347's control A
  * events are PLACED and then HELD BY THE STUDIES' OWN KERNEL, so this measures TRADES not events
    and reports both: D391's 144,657 events collapsed to 61,835 trades
  * the primary draw is UNIFORM over eligible cells -- the honest no-information null for a
    candidate that does not exist yet
  * THE ATLAS IS NOT A'. A' rotates a specific candidate's observed events and stays the right
    control for it. This is the PRIOR a candidate is read against before it has earned a null run.

RESUMABLE AND INCREMENTAL. Every cell is written as it completes; a re-run skips finished cells.
A four-hour job that dies in a print loop must not lose seventy cells -- D371 lost its evidence
that way and D391's runner reproduced the same defect earlier the same day.

ASSERTIONS [E][K][N][SE][P][X] -- spec section 6.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


OUT = REPO / "data" / "d392_atlas.json"
COUNTS = (100, 300, 1_000, 3_000, 10_000, 30_000, 60_000)
CAPS = (5, 10, 20, 40, 60)
SIDES = ("long", "short")
DRAWS_UNCOND = 500                 # the principal's ruling, 2026-09-08
DRAWS_COND = 200
COND_COUNTS = (3_000, 10_000, 30_000)
COND_CAP = 20
CONC_LEVELS = (1.0, 0.25, 0.05)    # share of eligible names the events may land on

# THE EXTENSION (D392 RESULT section 7's first owed item). The v1 grid topped out at 42,874
# TRADES and D391 reported 61,835, so the lookup correctly refused the one size a wide event
# study actually reaches. These counts push the trade axis past it. Caps are restricted to the
# three in common use -- 60,000 x cap 60 already cost 1.03 s/draw and the cost is ~linear in n.
EXT_COUNTS = (100_000, 150_000)
EXT_CAPS = (10, 20, 40)
SEED = 20260908
BOOT = 1_000


# ------------------------------------------------------------------ the draw
def eligible_index(elig):
    """Flat indices of every eligible (bar, name) cell. Computed once; the draw is a choice on it."""
    return np.flatnonzero(elig.ravel())


def draw_mask(rng, idx, shape, n, name_pool=None, names_allowed=None):
    """n distinct eligible cells as a (T, n_names) bool mask.

    `name_pool` restricts to a conditioned subset of cells (a tercile grid, already ANDed with
    elig upstream). `names_allowed` restricts WHICH NAMES may be used, for the concentration
    sensitivity. Both are applied to the index, never to the mask afterwards, so the count is
    exact rather than approximate."""
    pool = idx if name_pool is None else name_pool
    if names_allowed is not None:
        cols = pool % shape[1]
        pool = pool[np.isin(cols, names_allowed)]
    if pool.size < n:
        return None
    take = rng.choice(pool, size=n, replace=False)
    m = np.zeros(shape[0] * shape[1], dtype=bool)
    m[take] = True
    return np.ascontiguousarray(m.reshape(shape))


def score_once(V59, P, mask, cap, side, sc):
    """One kernel run through the STUDIES' OWN path. Returns (mean bp per trade, n trades)."""
    res = (V59.run_mirror if side == "long" else V59.run_short)(P, mask, sc, "cap", cap)
    tr = res["trades"]
    if not tr:
        return None, 0
    pnl = V59.V47.pnl_bp(res)
    return float(pnl.mean()), int(len(tr))


def summarise(vals, trades, rng):
    """The cell: the distribution, never a point. [SE] every p95 carries its bootstrap SE."""
    v = np.asarray([x for x in vals if x is not None], float)
    assert v.size > 0, "empty cell"
    p95 = float(np.quantile(v, .95))
    boot = np.array([np.quantile(rng.choice(v, v.size, replace=True), .95) for _ in range(BOOT)])
    return dict(draws=int(v.size), p05=float(np.quantile(v, .05)), p50=float(np.median(v)),
                p95=p95, se_p95=float(np.std(boot, ddof=1)), max=float(v.max()),
                mean=float(v.mean()), sd=float(v.std(ddof=1)),
                trades_mean=float(np.mean(trades)), trades_min=int(np.min(trades)),
                trades_max=int(np.max(trades)))


# ------------------------------------------------------------------ self-test
def selftest(V59=None, P=None, elig=None) -> int:
    print("D392 SELF-TEST -- the draw, the count, and two breaks that must be caught\n")
    rng = np.random.default_rng(1)
    T, N = 50, 20
    el = np.zeros((T, N), bool)
    el[10:40, 5:15] = True
    idx = eligible_index(el)
    m = draw_mask(rng, idx, (T, N), 60)
    assert int(m.sum()) == 60, f"[N] the draw is not the requested size: {int(m.sum())}"
    assert not (m & ~el).any(), "[E] a drawn event landed off the eligible mask"
    print(f"    [N] exactly 60 cells drawn | [E] none off the eligible mask "
          f"({int(el.sum())} eligible cells available)")

    # concentration: restricting names must restrict the columns used
    allowed = np.array([5, 6])
    m2 = draw_mask(rng, idx, (T, N), 40, names_allowed=allowed)
    used = np.unique(np.flatnonzero(m2.ravel()) % N)
    assert set(used.tolist()) <= set(allowed.tolist()), f"[E] concentration leaked names: {used}"
    print(f"    concentration: 40 events restricted to names {allowed.tolist()} used only {used.tolist()}")

    # [X] break 1 -- a draw placed off the mask must be caught
    bad = m.copy()
    bad[0, 0] = True                                          # bar 0 is not eligible
    raised = False
    try:
        assert not (bad & ~el).any(), "[E] a drawn event landed off the eligible mask"
    except AssertionError:
        raised = True
    assert raised, "[X] THE SELF-TEST CANNOT FAIL -- an ineligible draw passed [E]"
    print("    [X] an event placed on an ineligible bar IS CAUGHT")

    # [X] break 2 -- a p95 without its SE must be caught
    cell = summarise([1.0, 2.0, 3.0, 4.0, 5.0], [10, 10, 10, 10, 10], np.random.default_rng(2))
    assert "se_p95" in cell and cell["se_p95"] >= 0.0, "[SE] missing"
    stripped = {k: v for k, v in cell.items() if k != "se_p95"}
    raised = False
    try:
        assert "se_p95" in stripped, "[SE] a p95 was written without its bootstrap SE"
    except AssertionError:
        raised = True
    assert raised, "[X] THE SELF-TEST CANNOT FAIL -- a p95 without an SE passed"
    print(f"    [X] a p95 written without its SE IS CAUGHT (a real cell carries "
          f"p95 {cell['p95']:.2f} +/- {cell['se_p95']:.3f})")
    print("\nSELF-TEST PASSED\n")
    return 0


# ------------------------------------------------------------------ the cells
def cell_key(kind, n, cap, side, pool="ALL", conc=1.0):
    return f"{kind}|n={n}|cap={cap}|{side}|pool={pool}|conc={conc}"


def plan(part):
    """Every cell, CHEAPEST FIRST -- the 30k and 60k rows run last so a partial atlas is useful."""
    cells = []
    if part == "extend":
        for n in EXT_COUNTS:
            for cap in EXT_CAPS:
                for side in SIDES:
                    cells.append(dict(kind="uncond", n=n, cap=cap, side=side, pool="ALL",
                                      conc=1.0, draws=DRAWS_UNCOND))
        return sorted(cells, key=lambda c: (c["n"] * c["cap"], c["n"]))
    if part in ("uncond", "all"):
        for n in COUNTS:
            for cap in CAPS:
                for side in SIDES:
                    cells.append(dict(kind="uncond", n=n, cap=cap, side=side, pool="ALL",
                                      conc=1.0, draws=DRAWS_UNCOND))
    if part in ("cond", "all"):
        for n in COND_COUNTS:
            for pool in ("price_lo", "price_mid", "price_hi", "vol_lo", "vol_mid", "vol_hi",
                         "mom_lo", "mom_mid", "mom_hi"):
                for side in SIDES:
                    cells.append(dict(kind="cond", n=n, cap=COND_CAP, side=side, pool=pool,
                                      conc=1.0, draws=DRAWS_COND))
    if part in ("conc", "all"):
        for c in CONC_LEVELS:
            cells.append(dict(kind="conc", n=10_000, cap=COND_CAP, side="long", pool="ALL",
                              conc=c, draws=DRAWS_COND))
    return sorted(cells, key=lambda c: (c["n"] * c["cap"], c["n"]))


def tercile_pools(P, elig):
    """Cross-sectional terciles per bar, among ELIGIBLE names, for the three axes that killed
    things: price (D284), volatility (C1/D390) and momentum (D373/FINDINGS 52)."""
    out = {}
    CLOSE = np.asarray(P["CLOSE"])                                  # (T, n)
    src = {"price": CLOSE,
           "vol": np.asarray(P["score"]("rvol21")).T,
           "mom": np.asarray(P["score"]("mom_252_21")).T}
    for nm, grid in src.items():
        lo = np.zeros_like(elig)
        mid = np.zeros_like(elig)
        hi = np.zeros_like(elig)
        for t in range(elig.shape[0]):
            col = elig[t] & np.isfinite(grid[t])
            if col.sum() < 30:
                continue
            v = grid[t, col]
            a, b = np.quantile(v, [1 / 3, 2 / 3])
            j = np.flatnonzero(col)
            lo[t, j[v <= a]] = True
            hi[t, j[v >= b]] = True
            mid[t, j[(v > a) & (v < b)]] = True
        out[f"{nm}_lo"], out[f"{nm}_mid"], out[f"{nm}_hi"] = lo, mid, hi
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--part", default="all",
                    choices=["uncond", "cond", "conc", "all", "extend"])
    ap.add_argument("--lookup", nargs=3, metavar=("N", "CAP", "SIDE"))
    a = ap.parse_args()

    if a.selftest:
        return selftest()
    if a.lookup:
        atlas = json.loads(OUT.read_text())
        n, cap, side = int(a.lookup[0]), int(a.lookup[1]), a.lookup[2]
        print(json.dumps(lookup(atlas, n, cap, side), indent=1))
        return 0
    if not (a.calibrate or a.run):
        ap.error("pass --calibrate or --run")
    selftest()

    t0 = time.time()
    PREP = _load("d348p", "d348_prep.py")
    V59 = _load("d359r", "run_d359_loser_rally_short.py")
    P = PREP.prep(need_grids=True)
    T, N = P["T"], P["n"]
    elig = np.asarray(P["elig"])
    idx = eligible_index(elig)
    sc = np.full((T, N), 50.0)                                      # unused under exit="cap"
    print(f"  prep in {time.time() - t0:.0f}s | {N} names x {T} bars | "
          f"{idx.size:,} eligible (bar, name) cells", flush=True)

    # ---- [K] the kernel is the studies' own --------------------------------
    rngk = np.random.default_rng(SEED)
    mk = draw_mask(rngk, idx, (T, N), 2_000)
    r1 = V59.run_mirror(P, mk, sc, "cap", 20)
    r2 = V59.run_mirror(P, mk, np.full((T, N), 17.0), "cap", 20)
    m1, c1 = score_once(V59, P, mk, 20, "long", sc)
    assert len(r1["trades"]) == len(r2["trades"]), "[K] the score changed a cap-exit ledger"
    assert abs(m1 - float(V59.V47.pnl_bp(r1).mean())) < 1e-12 and c1 == len(r1["trades"]), \
        "[K] score_once differs from run_d359's path"
    print(f"    [K] score_once == run_d359's own path to 0.0 on a 2,000-event probe "
          f"({c1:,} trades, {m1:+.2f} bp); the cap exit ignores the score", flush=True)

    # ---- calibration: cost the grid before spending it (D373's precedent) --
    if a.calibrate:
        print("\n  CALIBRATION -- one draw per (n, cap), measured. Nothing is spent.\n")
        print(f"  {'n':>8s} {'cap':>4s} {'trades':>9s} {'s/draw':>8s}")
        cells = plan(a.part)
        pairs = sorted({(c["n"], c["cap"]) for c in cells})
        calfile = REPO / "data" / "d392_calibration.json"
        per = {}
        if calfile.exists():                      # keep what was already measured
            per = {tuple(int(x) for x in k.split("|")): v
                   for k, v in json.loads(calfile.read_text()).items()}
        for n, cap in pairs:
            if (n, cap) in per:
                continue
            m = draw_mask(np.random.default_rng([SEED, n, cap]), idx, (T, N), n)
            t1 = time.time()
            _mu, ntr = score_once(V59, P, m, cap, "long", sc)
            dt = time.time() - t1
            per[(n, cap)] = dt
            print(f"  {n:>8,} {cap:>4d} {ntr:>9,} {dt:>8.3f}", flush=True)
        total = sum(per[(c["n"], c["cap"])] * c["draws"] for c in cells)
        print(f"\n  PROJECTED for --part {a.part}: {total / 3600:.2f} h over {len(cells)} cells "
              f"({sum(c['draws'] for c in cells):,} kernel runs)")
        calfile.write_text(json.dumps({f"{n}|{cap}": v for (n, cap), v in per.items()}, indent=1))
        print(f"  wrote {calfile.relative_to(REPO)}")
        return 0

    # ---- the run: incremental, resumable ----------------------------------
    atlas = json.loads(OUT.read_text()) if OUT.exists() else {
        "study": 392, "spec": "docs/decisions/D392-the-base-rate-atlas.md",
        "build": "load_ragged(dividend_bound=True); keep_v2 floor; F0; next-open fill; "
                 "EB.simulate_event via run_d359 (R16)",
        "statistic": "gross mean per trade, bp; no cost, no borrow; hedged by the floored market",
        "seed": SEED, "cells": {}}
    pools = None
    cells = plan(a.part)
    done = sum(1 for c in cells if cell_key(c["kind"], c["n"], c["cap"], c["side"], c["pool"],
                                            c["conc"]) in atlas["cells"])
    print(f"\n  {len(cells)} cells planned, {done} already present -- resuming\n", flush=True)

    for ci, c in enumerate(cells):
        key = cell_key(c["kind"], c["n"], c["cap"], c["side"], c["pool"], c["conc"])
        if key in atlas["cells"]:
            continue
        if c["pool"] != "ALL" and pools is None:
            tp = time.time()
            pools = tercile_pools(P, elig)
            print(f"    tercile pools built in {time.time() - tp:.0f}s", flush=True)
        pool_idx = None if c["pool"] == "ALL" else np.flatnonzero(pools[c["pool"]].ravel())
        names_allowed = None
        if c["conc"] < 1.0:
            rngn = np.random.default_rng([SEED, 99])
            k = max(1, int(round(c["conc"] * N)))
            names_allowed = rngn.choice(np.arange(N), size=k, replace=False)
        rng = np.random.default_rng([SEED, c["n"], c["cap"], hash(c["side"]) % 97,
                                     hash(c["pool"]) % 97])
        vals, trades, t1, skipped = [], [], time.time(), 0
        for d in range(c["draws"]):
            m = draw_mask(rng, idx, (T, N), c["n"], name_pool=pool_idx, names_allowed=names_allowed)
            if m is None:
                skipped += 1
                continue
            assert not (m & ~elig).any(), "[E] a drawn event landed off the eligible mask"
            mu, ntr = score_once(V59, P, m, c["cap"], c["side"], sc)
            if mu is not None:
                vals.append(mu)
                trades.append(ntr)
        if not vals:
            atlas["cells"][key] = dict(status="EMPTY", reason="pool too small", skipped=skipped)
        else:
            cell = summarise(vals, trades, np.random.default_rng([SEED, 7, ci]))
            cell.update(kind=c["kind"], n=c["n"], cap=c["cap"], side=c["side"], pool=c["pool"],
                        conc=c["conc"], seconds=time.time() - t1, skipped=skipped)
            atlas["cells"][key] = cell
        # [P] PERSIST EVERY CELL AS IT COMPLETES, before anything is rendered
        OUT.write_text(json.dumps(atlas, indent=1))
        cc = atlas["cells"][key]
        if cc.get("status") == "EMPTY":
            print(f"    [{ci + 1}/{len(cells)}] {key}  EMPTY (pool too small)", flush=True)
        else:
            print(f"    [{ci + 1}/{len(cells)}] n={c['n']:<6,} cap={c['cap']:<3d} {c['side']:<5s} "
                  f"{c['pool']:<9s} p50 {cc['p50']:+7.2f}  p95 {cc['p95']:+7.2f} "
                  f"+/- {cc['se_p95']:.2f}  ({cc['trades_mean']:,.0f} trades, "
                  f"{cc['seconds']:.0f}s)", flush=True)

    print(f"\n  [P] {OUT.relative_to(REPO)} written incrementally; "
          f"{len(atlas['cells'])} cells total  ({(time.time() - t0) / 60:.0f} min)")
    print("\nThis is a MEASUREMENT. It admits nothing (R15).")
    return 0


def lookup(atlas, n, cap, side, pool="ALL", by="trades", conc=1.0):
    """atlas.floor(n, cap, side, pool): p95 and its SE, log-linear, RAISING outside the grid.

    `by="trades"` IS THE DEFAULT AND IT IS A CORRECTION. The atlas is INDEXED on event count, but
    the statistic depends on the TRADE count -- the kernel holds one position per name at a time,
    so 60,000 events become 42,874 trades at cap 20 and 26,958 at cap 60. A candidate reporting
    61,835 trades (D391) must be read against the trade axis, not against the cell labelled
    n=60,000. The concentration cells made this unmissable: at 5% of names, 10,000 events collapse
    to 4,116 trades, less than half the 9,337 the same event count gives unconstrained.

    Pass `by="events"` only when the caller genuinely has an event count and wants the event axis.
    Outside the grid this RAISES rather than extrapolating -- the atlas states what it measured."""
    key = (lambda c: c["trades_mean"]) if by == "trades" else (lambda c: c["n"])
    # conc must be filtered or the concentration cells -- which are pool="ALL" -- pollute the
    # main curve. Caught by testing the lookup rather than by reading it.
    got = [(key(c), c) for c in atlas["cells"].values()
           if c.get("cap") == cap and c.get("side") == side and c.get("pool") == pool
           and c.get("conc", 1.0) == conc and c.get("status") != "EMPTY"]
    if not got:
        raise KeyError(f"no cells for cap={cap} side={side} pool={pool}")
    # the conc=1.0 CONTROL cell duplicates the unconditional cell at fewer draws, so the curve
    # would carry two points at the same n. Keep the better-sampled one.
    got.sort()
    merged = []
    for k, c in got:
        if merged and abs(k - merged[-1][0]) <= 0.01 * max(k, 1.0):      # within 1% == the same point
            if c["draws"] > merged[-1][1]["draws"]:
                merged[-1] = (k, c)
            continue
        merged.append((k, c))
    got = merged
    ns = [x[0] for x in got]
    # the endpoints are MEANS over draws, so a caller quoting a rounded trade count must not fall
    # off the end by 0.4 of a trade. 0.1% tolerance, then clamp.
    tol = 1e-3
    if ns[0] * (1 - tol) <= n < ns[0]:
        n = ns[0]
    if ns[-1] < n <= ns[-1] * (1 + tol):
        n = ns[-1]
    if n < ns[0] or n > ns[-1]:
        raise ValueError(f"{by}={n:,.0f} outside the atlas grid "
                         f"[{ns[0]:,.0f}, {ns[-1]:,.0f}] for cap={cap} {side} pool={pool} -- "
                         "the atlas does not extrapolate. Extend the grid or report the nearest "
                         "in-grid floor AS the nearest, saying so.")
    for (n0, c0), (n1, c1) in zip(got, got[1:]):
        if n0 <= n <= n1:
            w = 0.0 if n1 == n0 else (np.log(n) - np.log(n0)) / (np.log(n1) - np.log(n0))
            return dict(p95=float(c0["p95"] + w * (c1["p95"] - c0["p95"])),
                        p50=float(c0["p50"] + w * (c1["p50"] - c0["p50"])),
                        se_p95=float(max(c0["se_p95"], c1["se_p95"])),
                        interpolated=bool(n not in ns), between=[n0, n1], pool=pool)
    c = dict(got[-1][1])
    return dict(p95=c["p95"], p50=c["p50"], se_p95=c["se_p95"], interpolated=False,
                between=[c["n"], c["n"]], pool=pool)


if __name__ == "__main__":
    raise SystemExit(main())
