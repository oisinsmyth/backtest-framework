"""Run rotation nulls for many books ACROSS PROCESSES, bit-identically.

    from parallel_nulls import run_nulls
    res = run_nulls(books, fixture, events, fee_bps=5.0, ppy=252,
                    rf_annual=0.04, borrow_annual=0.03, n_sims=300, seed=0)
    sh, mn = res["S1_short|top25"]

NOTHING HERE CHANGES A NUMBER. It changes only WHERE the same number is
computed. `RP.rotation_null` is deterministic given `(panel, position, seed)`
and every book's null is independent of every other, so distributing books over
processes is EXACTLY EQUIVALENT by construction rather than by approximation.
`--verify` asserts that on the real fixture, and it must be run after any change
to this file.

WHY PROCESSES AND NOT THREADS. The inner loop is 300 sims x ~1,570 per-symbol
`np.roll` calls on short segments, plus 300 full `score` passes. Small numpy ops
do not release the GIL for long enough to overlap, so threads buy almost
nothing; the work is CPU-bound and must go to separate interpreters.

WHY THE PANEL IS NOT PICKLED. It is ~260 MB of dense grids. Each worker LOADS IT
ONCE from the fixture in an initializer and keeps it in a module global, so the
cost is paid once per worker rather than once per task.

WHY POSITIONS ARE SENT SPARSE. A book holds 10-50 names out of 1,573, so a dense
position grid is 6.6M cells of which ~99% are zero -- 52 MB each, ~950 MB for a
grid of eighteen. Sent as (rows, cols, values) it is a few hundred kilobytes.
The worker rebuilds the dense array, so the array the null sees is identical.

WINDOWS NOTE. There is no `fork` here, so workers start via `spawn` and re-import
this module. Everything a worker needs is therefore at module scope and the
entry point is guarded.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
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

_PANEL = None          # per-worker, set by _init


def _init(fixture: str, events: str, fee_bps: float) -> None:
    """Load the panel ONCE per worker. Called by the pool, never directly."""
    global _PANEL
    _PANEL, _ = RP.load_ragged(Path(fixture), Path(events) if events else None,
                               fee_bps=fee_bps)


def to_sparse(pos: np.ndarray):
    """(rows, cols, values, shape). A held book is ~1% dense; see the docstring."""
    r, c = np.nonzero(pos)
    return r.astype(np.int32), c.astype(np.int32), pos[r, c].astype(np.float64), pos.shape


def from_sparse(payload) -> np.ndarray:
    r, c, v, shape = payload
    out = np.zeros(shape, dtype=np.float64)
    out[r.astype(np.intp), c.astype(np.intp)] = v
    return out


def _work(task):
    key, payload, start, kw = task
    pos = from_sparse(payload)
    sh, mn = RP.rotation_null(_PANEL, pos, start, **kw)
    return key, sh, mn


def run_nulls(books: dict, fixture, events, *, fee_bps: float, start: int = 0,
              workers: int | None = None, progress=True, **kw) -> dict:
    """Rotation nulls for every book in `books`, one process per worker.

    `kw` is forwarded verbatim to `RP.rotation_null` -- n_sims, seed, ppy,
    rf_annual, borrow_annual. Returns {key: (sharpe_draws, money_draws)}.

    Falls back to running in-process when `workers == 1`, which is what the
    equivalence check compares against."""
    keys = list(books)
    if workers is None:
        workers = max(1, min(len(keys), (os.cpu_count() or 2) - 2))

    if workers == 1:
        out = {}
        for k in keys:
            sh, mn = RP.rotation_null(_PANEL_OR_LOAD(fixture, events, fee_bps),
                                      books[k], start, **kw)
            out[k] = (sh, mn)
        return out

    tasks = [(k, to_sparse(books[k]), start, kw) for k in keys]
    out, done, t0 = {}, 0, time.time()
    with ProcessPoolExecutor(max_workers=workers, initializer=_init,
                             initargs=(str(fixture), str(events) if events else "",
                                       fee_bps)) as ex:
        for key, sh, mn in ex.map(_work, tasks):
            out[key] = (sh, mn)
            done += 1
            if progress:
                print(f"    [{done}/{len(keys)}] {key:24s} "
                      f"{time.time() - t0:6.0f}s", flush=True)
    return out


def run_nulls_threaded(panel, books: dict, start: int = 0, workers=None, **kw) -> dict:
    """Same nulls, THREADS in one process, sharing the panel with no copy.

    Kept because the question "would threads have been enough" deserves a
    measurement rather than an assertion. The expectation is that they are not:
    the inner loop is ~1,570 per-symbol `np.roll` calls on SHORT segments per
    sim, and numpy releases the GIL only around large operations, so most of
    this work holds it. `--bench` reports what actually happens."""
    if workers is None:
        workers = max(1, min(len(books), (os.cpu_count() or 2) - 2))
    out = {}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(RP.rotation_null, panel, p, start, **kw): k
                for k, p in books.items()}
        for f, k in futs.items():
            out[k] = f.result()
    return out


def _PANEL_OR_LOAD(fixture, events, fee_bps):
    """Serial path: load once into the module global and reuse it."""
    global _PANEL
    if _PANEL is None:
        _init(str(fixture), str(events) if events else "", fee_bps)
    return _PANEL


# --------------------------------------------------------------------------
# the equivalence check -- run this after ANY change to this file
# --------------------------------------------------------------------------


def verify(n_books: int = 3, n_sims: int = 40) -> int:
    """Assert the parallel path reproduces the serial one EXACTLY.

    Not 'to within a tolerance'. `rotation_null` is deterministic given
    (panel, position, seed), so any difference at all is a defect -- and a null
    that differs by even a float would make every past percentile
    incomparable."""
    B = _load("d256", "run_book_single_names.py")
    C = _load("d279", "run_concentrated_short.py")
    print(f"verifying on {B.FIXTURE.name}, {n_books} books x {n_sims} sims\n")

    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=B.FEE_BPS)
    md, hs, g_lo, g_hi, i_lo, atr, warm = B.signals_ragged(panel, cleaned, 0)
    ok = ~(np.isnan(md) | np.isnan(hs)) & warm
    s1 = -B.hold_book((hs < 0) & (md >= 0) & ok, warm)
    books = {f"top{N}": C.top_n(s1, hs, N) for N in (10, 25, 50)[:n_books]}

    kw = dict(n_sims=n_sims, seed=0, ppy=B.PPY, rf_annual=B.RF_ANNUAL,
              borrow_annual=B.BORROW_ANNUAL)

    t0 = time.time()
    serial = {k: RP.rotation_null(panel, p, 0, **kw) for k, p in books.items()}
    t_ser = time.time() - t0

    # sparse round-trip must be lossless before the pool is even involved
    for k, p in books.items():
        if not np.array_equal(from_sparse(to_sparse(p)), p):
            raise AssertionError(f"{k}: sparse round-trip is not lossless")
    print("  [1] sparse round-trip is exact on every book")

    t0 = time.time()
    par = run_nulls(books, B.FIXTURE, B.EVENTS, fee_bps=B.FEE_BPS,
                    workers=min(len(books), (os.cpu_count() or 2) - 2),
                    progress=False, **kw)
    t_par = time.time() - t0

    for k in books:
        a_sh, a_mn = serial[k]
        b_sh, b_mn = par[k]
        if not (np.array_equal(a_sh, b_sh) and np.array_equal(a_mn, b_mn)):
            worst = max(float(np.max(np.abs(a_sh - b_sh))),
                        float(np.max(np.abs(a_mn - b_mn))))
            raise AssertionError(
                f"{k}: parallel null differs from serial by {worst:.3e} -- "
                "refusing to ship a null that is not bit-identical")
    print(f"  [2] every draw is BIT-IDENTICAL across {len(books)} books")
    print(f"\n  serial {t_ser:6.1f}s   parallel {t_par:6.1f}s   "
          f"speedup {t_ser / t_par:.2f}x on {len(books)} books")
    print("  (speedup grows with the number of books; the pool's start-up and\n"
          "   per-worker panel load are paid once, not per book)")
    return 0


def bench(n_books: int = 6, n_sims: int = 100) -> int:
    """SERIAL vs THREADS vs PROCESSES on the real fixture.

    Every path is checked BIT-IDENTICAL to serial before any timing is believed.
    A parallel null that is merely close is not a faster null, it is a different
    null, and every past percentile would become incomparable."""
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
    books = dict(list(books.items())[:n_books])
    w = max(1, min(len(books), (os.cpu_count() or 2) - 2))
    kw = dict(n_sims=n_sims, seed=0, ppy=B.PPY, rf_annual=B.RF_ANNUAL,
              borrow_annual=B.BORROW_ANNUAL)
    print(f"\n  {len(books)} books x {n_sims} sims, {w} workers, "
          f"{os.cpu_count()} cpus\n")

    t0 = time.time()
    ser = {k: RP.rotation_null(panel, p, 0, **kw) for k, p in books.items()}
    t_ser = time.time() - t0
    print(f"  SERIAL     {t_ser:7.1f}s   baseline", flush=True)

    t0 = time.time()
    thr = run_nulls_threaded(panel, books, workers=w, **kw)
    t_thr = time.time() - t0
    ok_thr = all(np.array_equal(ser[k][0], thr[k][0])
                 and np.array_equal(ser[k][1], thr[k][1]) for k in books)
    print(f"  THREADS    {t_thr:7.1f}s   {t_ser / t_thr:5.2f}x   "
          f"bit-identical: {ok_thr}", flush=True)

    t0 = time.time()
    par = run_nulls(books, B.FIXTURE, B.EVENTS, fee_bps=B.FEE_BPS,
                    workers=w, progress=False, **kw)
    t_par = time.time() - t0
    ok_par = all(np.array_equal(ser[k][0], par[k][0])
                 and np.array_equal(ser[k][1], par[k][1]) for k in books)
    print(f"  PROCESSES  {t_par:7.1f}s   {t_ser / t_par:5.2f}x   "
          f"bit-identical: {ok_par}", flush=True)
    if not (ok_thr and ok_par):
        raise AssertionError("a parallel path is not bit-identical to serial")
    print("\n  Process timing INCLUDES pool start-up and a per-worker panel load,")
    print("  both paid ONCE, so the ratio improves with the book count.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--verify", action="store_true",
                    help="assert the parallel path is bit-identical to the serial one")
    ap.add_argument("--bench", action="store_true",
                    help="serial vs threads vs processes, all verified identical")
    ap.add_argument("--books", type=int, default=3)
    ap.add_argument("--sims", type=int, default=40)
    a = ap.parse_args()
    if a.verify:
        raise SystemExit(verify(a.books, a.sims))
    if a.bench:
        raise SystemExit(bench(a.books, a.sims))
    ap.print_help()
    raise SystemExit(2)
