"""A rotation null that is BIT-IDENTICAL to `RP.rotation_null` and much faster.

    uv run python scripts/fast_null.py --verify        # exactness, on the real fixture
    uv run python scripts/fast_null.py --bench         # against the original

NOTHING HERE CHANGES A NUMBER, AND THAT IS THE WHOLE CONSTRAINT. A null that
differs from the original by even one float would make every percentile in
D256-D285 incomparable. Every optimisation below is either a HOISTED
COMPUTATION (identical arithmetic, done once instead of 300 times) or a SKIPPED
one (a quantity the null never reads). None reorders a floating-point sum.

WHAT WAS SLOW, measured rather than guessed
============================================

  1. `pooled_returns` recomputes `np.expm1(total_log_returns) * live` ON EVERY
     CALL -- 6.6M transcendental evaluations plus a 6.6M multiply, 300 times per
     book. **This is the single largest cost in the null and it is the same
     array every time.** Hoisted out of the sim loop.

  2. `score` computes ~15 statistics; the null reads TWO of them
     (`excess_sharpe`, `total_return`). Drawdowns, entry counts, turnover units,
     per-symbol P&L and the rest are computed 300 times per book and discarded.
     Skipped -- not reordered.

  3. The roll is 1,573 `np.roll` calls per sim on short segments. But A BOOK IS
     ~1% DENSE: `top25` has ~105k non-zero cells out of 6.6M. Rolling is exact
     integer index arithmetic, so the new column of a non-zero cell can be
     computed directly and scattered, touching 105k cells instead of 6.6M.
     The resulting dense array is IDENTICAL, element for element.

WHAT IS NOT TOUCHED, deliberately
==================================

  THE RNG DRAW SEQUENCE. The original calls `rng.integers(0, seg.size)` once per
  symbol per sim, IN SYMBOL ORDER, and **only for symbols whose window is longer
  than one bar**. Drawing a vector of offsets instead would be a different
  stream and every percentile would move. The scalar loop is kept exactly,
  because it is cheap (~0.5M calls) and it is what makes the seed mean the same
  thing it meant in D256.

  `enforce_live`. Rolling stays inside a symbol's [first, last] window, but 134
  of 1,573 symbols have INTERNAL holes, so a rolled position can land on a bar
  the name did not trade. The mask is still applied.

  THE SUMMATION ORDER of every quantity that survives.
"""

from __future__ import annotations

import argparse
import importlib.util
import math
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
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


RP = _load("ragged_panel", "ragged_panel.py")


class NullContext:
    """Everything that does not change between sims, computed once.

    Built per panel, shared by every book and every thread. It is READ-ONLY
    after construction, which is what makes the threaded path safe without a
    lock."""

    def __init__(self, panel):
        self.panel = panel
        self.live = panel.live
        # THE HOIST THAT MATTERS: identical to what `pooled_returns` builds on
        # every single call, built once here.
        self.sm = np.expm1(panel.total_log_returns) * panel.live
        self.denom = np.maximum(panel.live.sum(axis=0), 1).astype(float)
        self.cost = panel.cost_fraction[:, None]
        self.windows = [panel.index_of[s] for s in panel.symbols]
        self.starts = np.array([a for a, _ in self.windows], dtype=np.int64)
        self.lens = np.array([b - a + 1 for a, b in self.windows], dtype=np.int64)


def light_score(ctx, pos, start, rf_annual, borrow_annual, ppy):
    """`excess_sharpe` and `total_return`, by the arithmetic `RP.score` uses.

    Every surviving line is copied from `pooled_returns`, `legs` and `score` in
    their original order. What is absent is only what the null never reads."""
    p = RP.enforce_live(pos, ctx.panel, start)
    turn = np.abs(np.diff(p, axis=1, prepend=0.0))
    gross = (p * ctx.sm).sum(axis=0)
    cost = (ctx.cost * turn).sum(axis=0)
    r = ((gross - cost) / ctx.denom)[start:]

    ps = p[:, start:]
    d2 = ctx.denom[start:]
    long_f = float((np.maximum(ps, 0.0).sum(axis=0) / d2).mean())
    short_f = float((np.maximum(-ps, 0.0).sum(axis=0) / d2).mean())

    rf = math.expm1(math.log1p(rf_annual) / ppy)
    bor = math.expm1(math.log1p(borrow_annual) / ppy)
    ex = r - long_f * rf - short_f * bor
    sd = float(np.std(ex, ddof=1))
    eq = np.cumprod(1.0 + r)
    sharpe = (float(np.mean(ex)) / sd * math.sqrt(ppy)) if sd > 0 else 0.0
    return sharpe, float(eq[-1] - 1.0)


def rotation_null(ctx, position, start, *, n_sims, seed, ppy, rf_annual,
                  borrow_annual):
    """Bit-identical replacement for `RP.rotation_null`."""
    rng = np.random.default_rng(seed)
    pos = RP.enforce_live(position, ctx.panel, start)
    nz_i, nz_t = np.nonzero(pos)
    nz_v = pos[nz_i, nz_t]
    a_of = ctx.starts[nz_i]
    L_of = ctx.lens[nz_i]
    rel = nz_t - a_of                       # position inside the symbol's window

    sh = np.empty(n_sims)
    mn = np.empty(n_sims)
    offs = np.empty(len(ctx.windows), dtype=np.int64)
    rot = np.zeros_like(pos)
    for k in range(n_sims):
        # THE DRAW SEQUENCE IS THE ORIGINAL'S, symbol by symbol, and skipped for
        # a one-bar window exactly as the original skips it.
        for i, L in enumerate(ctx.lens):
            offs[i] = int(rng.integers(0, L)) if L > 1 else 0
        rot[:] = 0.0
        # np.roll(seg, off)[j] = seg[(j - off) % L], so a value at window offset
        # `rel` lands at (rel + off) % L. Exact integer arithmetic on the ~1% of
        # cells that are non-zero.
        new_t = a_of + (rel + offs[nz_i]) % L_of
        rot[nz_i, new_t] = nz_v
        sh[k], mn[k] = light_score(ctx, rot, start, rf_annual, borrow_annual, ppy)
    return sh, mn


def run_nulls_threaded(ctx, books: dict, start: int = 0, workers=None, **kw) -> dict:
    """One thread per book, sharing the read-only context with no copy."""
    if workers is None:
        workers = max(1, min(len(books), (os.cpu_count() or 2) - 2))
    out = {}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(rotation_null, ctx, p, start, **kw): k
                for k, p in books.items()}
        for f, k in futs.items():
            out[k] = f.result()
    return out


def _fixture_books(n_books):
    B = _load("d256", "run_book_single_names.py")
    C = _load("d279", "run_concentrated_short.py")
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=B.FEE_BPS)
    md, hs, g_lo, g_hi, i_lo, atr, warm = B.signals_ragged(panel, cleaned, 0)
    ok = ~(np.isnan(md) | np.isnan(hs)) & warm
    s1 = -B.hold_book((hs < 0) & (md >= 0) & ok, warm)
    rng = np.random.default_rng(0)
    books = {}
    for N in (10, 25, 50):
        books[f"top{N}"] = C.top_n(s1, hs, N)
        books[f"rnd{N}"] = C.top_n(s1, hs, N, rng=rng)
    books["all"] = s1
    return B, panel, dict(list(books.items())[:n_books])


def verify(n_books=4, n_sims=40) -> int:
    B, panel, books = _fixture_books(n_books)
    ctx = NullContext(panel)
    kw = dict(n_sims=n_sims, seed=0, ppy=B.PPY, rf_annual=B.RF_ANNUAL,
              borrow_annual=B.BORROW_ANNUAL)
    print(f"\n  {len(books)} books x {n_sims} sims -- EXACTNESS, not tolerance\n")
    bad = 0
    for k, p in books.items():
        a_sh, a_mn = RP.rotation_null(panel, p, 0, **kw)
        b_sh, b_mn = rotation_null(ctx, p, 0, **kw)
        same = np.array_equal(a_sh, b_sh) and np.array_equal(a_mn, b_mn)
        worst = max(float(np.max(np.abs(a_sh - b_sh))),
                    float(np.max(np.abs(a_mn - b_mn))))
        print(f"    {k:8s} identical: {str(same):5s}   max abs diff {worst:.3e}")
        bad += 0 if same else 1
    if bad:
        raise AssertionError(f"{bad} book(s) differ -- refusing to ship")
    print("\n  ALL BIT-IDENTICAL.")
    return 0


def bench(n_books=6, n_sims=100) -> int:
    B, panel, books = _fixture_books(n_books)
    ctx = NullContext(panel)
    w = max(1, min(len(books), (os.cpu_count() or 2) - 2))
    kw = dict(n_sims=n_sims, seed=0, ppy=B.PPY, rf_annual=B.RF_ANNUAL,
              borrow_annual=B.BORROW_ANNUAL)
    print(f"\n  {len(books)} books x {n_sims} sims, {w} threads, "
          f"{os.cpu_count()} cpus\n")

    t0 = time.time()
    ser = {k: RP.rotation_null(panel, p, 0, **kw) for k, p in books.items()}
    t_ser = time.time() - t0
    print(f"  ORIGINAL, serial       {t_ser:7.1f}s   baseline", flush=True)

    t0 = time.time()
    f1 = {k: rotation_null(ctx, p, 0, **kw) for k, p in books.items()}
    t_f1 = time.time() - t0
    print(f"  FAST, serial           {t_f1:7.1f}s   {t_ser / t_f1:5.2f}x", flush=True)

    t0 = time.time()
    f2 = run_nulls_threaded(ctx, books, workers=w, **kw)
    t_f2 = time.time() - t0
    print(f"  FAST + {w} threads      {t_f2:7.1f}s   {t_ser / t_f2:5.2f}x", flush=True)

    for name, got in (("fast/serial", f1), ("fast/threaded", f2)):
        for k in books:
            if not (np.array_equal(ser[k][0], got[k][0])
                    and np.array_equal(ser[k][1], got[k][1])):
                raise AssertionError(f"{name} {k}: NOT bit-identical")
    print(f"\n  every path BIT-IDENTICAL to the original.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--bench", action="store_true")
    ap.add_argument("--books", type=int, default=4)
    ap.add_argument("--sims", type=int, default=40)
    a = ap.parse_args()
    if a.verify:
        raise SystemExit(verify(a.books, a.sims))
    if a.bench:
        raise SystemExit(bench(a.books, a.sims))
    ap.print_help()
    raise SystemExit(2)
