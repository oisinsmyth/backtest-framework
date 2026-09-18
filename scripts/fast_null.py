"""Fast, BIT-IDENTICAL rotation nulls and threaded fan-out, for ANY study.

    uv run python scripts/fast_null.py --verify     # exactness on a real fixture
    uv run python scripts/fast_null.py --bench      # against the original

    from fast_null import NullContext, rotation_null, run_nulls, parallel_map
    ctx = NullContext(panel)                        # close-to-close, the default
    ctx.assert_matches_scorer(pos, my_scorer)       # DO THIS ONCE PER STUDY
    draws = run_nulls(ctx, books, n_sims=300, seed=0, ppy=252,
                      rf_annual=0.04, borrow_annual=0.03)

THE CONSTRAINT IS EXACTNESS, NOT TOLERANCE. A null differing from the original
by one float would make every percentile in D256-D285 incomparable. Every
optimisation here is a HOISTED computation (identical arithmetic, done once
instead of `n_sims` times) or a SKIPPED one (a quantity the null never reads).
**Nothing reorders a floating-point sum.**

WHAT WAS SLOW, measured rather than guessed
============================================
  1. `pooled_returns` recomputes `np.expm1(total_log_returns) * live` ON EVERY
     CALL -- 6.6M transcendental evaluations plus a 6.6M multiply, `n_sims`
     times per book, producing the SAME array each time. The largest single
     cost. Hoisted into the context.
  2. `score` computes ~15 statistics; a null reads TWO. Drawdowns, entry counts,
     turnover units and per-symbol P&L were computed and discarded `n_sims`
     times.
  3. The roll was ~1,570 `np.roll` calls per sim, but A BOOK IS ~1% DENSE:
     `top25` has ~105k non-zero cells of 6.6M. Rolling is exact integer index
     arithmetic, so each non-zero's new column is computed directly and
     scattered. Identical array, ~60x fewer cells touched.

Measured on the daily fixture, 6 books x 100 sims, 16 cpus:
`original serial 199.6s -> fast serial 87.4s (2.28x) -> fast + 6 threads 33.3s
(6.00x)`, every path bit-identical.

WHAT IS DELIBERATELY NOT TOUCHED
=================================
  THE RNG DRAW SEQUENCE. The original draws `rng.integers(0, L)` once per symbol
  per sim, IN SYMBOL ORDER, and **only where the window is longer than one bar**.
  A vectorised draw is a different stream and every percentile would move.
  `enforce_live`. 134 of 1,573 symbols have INTERNAL holes, so a rolled position
  can land on a bar the name did not trade.
  THE SUMMATION ORDER of every surviving quantity.

GENERALITY -- this is not tied to one fixture or one scorer
============================================================
`NullContext` takes the returns grid, the tradeability mask and the turnover
convention as arguments, so it covers both study families in this repo:

  CLOSE-TO-CLOSE (D256, D279, D281, D283, D285)
      NullContext(panel)                       # defaults
  OVERNIGHT (D282, D284), whose scorer compounds `open[t+1]/close[t]` and
  charges `2*|pos|` every night rather than `|diff(pos)|`
      NullContext(panel, simple=night["simple"], mask=night["valid"],
                  turnover="per_bar_2x", divide="before")

**AND EVERY STUDY MUST CALL `assert_matches_scorer` ONCE before using this.**
It runs the study's OWN scorer and this module's light one on the real book and
asserts they agree exactly. That is what makes "bit-identical" a property of
your study rather than a claim inherited from mine.
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

DEFAULT_WORKERS = max(1, (os.cpu_count() or 4) - 2)


class NullContext:
    """Everything invariant across sims, computed once. READ-ONLY after
    construction, which is what makes the threaded path safe without a lock.

    `simple`    per-bar SIMPLE returns. Defaults to the close-to-close grid
                `expm1(total_log_returns) * live`. Pass an overnight grid to
                score an overnight book.
    `mask`      extra tradeability mask multiplied into every position on top of
                `panel.live` -- e.g. an overnight book's priced-night mask.
    `turnover`  "diff" charges `|diff(pos)|` (close-to-close); "per_bar_2x"
                charges `2*|pos|` every bar, which is what a book that enters
                and exits every period actually pays.
    `divide`    "after" is `(gross - cost)/nlive`, what `RP.pooled_returns`
                does; "before" is `gross/nlive - cost/nlive`, what D282's
                overnight scorer does. **They differ in the last bit**, which
                is exactly the kind of thing `assert_matches_scorer` exists to
                catch rather than let a null silently inherit.
    """

    def __init__(self, panel, simple=None, mask=None, turnover="diff",
                 divide="after"):
        if turnover not in ("diff", "per_bar_2x"):
            raise ValueError(f"unknown turnover convention {turnover!r}")
        if divide not in ("after", "before"):
            raise ValueError(f"unknown divide convention {divide!r}")
        self.divide = divide
        self.panel = panel
        self.turnover = turnover
        self.mask = mask
        self.simple = (np.expm1(panel.total_log_returns) * panel.live
                       if simple is None else simple)
        self.denom = np.maximum(panel.live.sum(axis=0), 1).astype(float)
        self.cost = panel.cost_fraction[:, None]
        self.starts = np.array([panel.index_of[s][0] for s in panel.symbols],
                               dtype=np.int64)
        self.lens = np.array([panel.index_of[s][1] - panel.index_of[s][0] + 1
                              for s in panel.symbols], dtype=np.int64)

    def enforce(self, pos, start):
        out = RP.enforce_live(pos, self.panel, start)
        return out if self.mask is None else out * self.mask

    def light_score(self, pos, start, rf_annual, borrow_annual, ppy):
        """`excess_sharpe` and `total_return`, by the arithmetic the full
        scorers use, in their original order. What is absent is only what a null
        never reads."""
        p = self.enforce(pos, start)
        turn = (np.abs(np.diff(p, axis=1, prepend=0.0)) if self.turnover == "diff"
                else 2.0 * np.abs(p))
        gross = (p * self.simple).sum(axis=0)
        cost = (self.cost * turn).sum(axis=0)
        # THE DIVISION ORDER IS A CONVENTION AND IT IS WORTH ONE ULP.
        # `RP.pooled_returns` computes (gross - cost)/nlive; D282's overnight
        # scorer computes gross/nlive - cost/nlive. The two differ in the last
        # bit, which `assert_matches_scorer` catches and refuses -- so the
        # convention is selected here rather than assumed.
        r = (((gross - cost) / self.denom) if self.divide == "after"
             else (gross / self.denom - cost / self.denom))[start:]

        ps, d2 = p[:, start:], self.denom[start:]
        lf = float((np.maximum(ps, 0.0).sum(axis=0) / d2).mean())
        sf = float((np.maximum(-ps, 0.0).sum(axis=0) / d2).mean())
        rf = math.expm1(math.log1p(rf_annual) / ppy)
        bor = math.expm1(math.log1p(borrow_annual) / ppy)
        ex = r - lf * rf - sf * bor
        sd = float(np.std(ex, ddof=1))
        eq = np.cumprod(1.0 + r)
        mu = float(np.mean(ex))
        # ZERO VARIANCE IS sign(mu) * inf, NOT 0.0 -- `analytics.metrics.sharpe`'s
        # convention and D49's argument (D542). A book with zero excess variance and a
        # NEGATIVE mean is infinitely bad risk-adjusted; calling it 0.0 ranks it above
        # every losing draw in the distribution.
        #
        # What is and is not reachable, measured rather than assumed. The two conventions
        # agree whenever mu == 0, so the all-flat rotation -- the case this looked like it
        # mis-scored -- is NOT affected: a flat book has r == 0, lf == sf == 0, so ex == 0
        # and both say 0.0. The divergence needs a CONSTANT NON-ZERO excess, which needs a
        # book that HOLDS while every held bar returns exactly zero (padded or halted
        # bars, which these fixtures do carry). Then ex == -lf*rf - sf*bor, a constant
        # negative, and the old branch scored that draw 0.0 where the truth is -inf.
        #
        # So the old behaviour scored such a null draw TOO HIGH, which DEFLATES the real
        # book's percentile. It was conservative, not flattering -- the opposite of what
        # the audit that found it claimed.
        return ((mu / sd * math.sqrt(ppy)) if sd > 0 else (math.inf * mu if mu != 0 else 0.0),
                float(eq[-1] - 1.0))

    def assert_matches_scorer(self, pos, scorer, start=0, *, rf_annual, borrow_annual,
                              ppy, sharpe_key="excess_sharpe",
                              money_key="total_return"):
        """CALL THIS ONCE PER STUDY, before any null is run.

        Runs the study's OWN scorer and this module's light one on the real book
        and asserts they agree EXACTLY. Without it, "bit-identical" is a claim
        inherited from whichever study this file was written against; with it,
        it is a property of yours. Costs one scoring call."""
        ref = scorer(pos)
        a, b = self.light_score(pos, start, rf_annual, borrow_annual, ppy)
        for name, got, want in ((sharpe_key, a, ref[sharpe_key]),
                                (money_key, b, ref[money_key])):
            if got != want:
                raise AssertionError(
                    f"light_score disagrees with the study's scorer on {name}: "
                    f"{got!r} vs {want!r}. The context's `simple`, `mask` or "
                    f"`turnover` does not match this study's conventions -- "
                    f"refusing to run a null that scores a different book.")
        return True


def rotation_null(ctx, position, start=0, *, n_sims, seed, ppy, rf_annual,
                  borrow_annual):
    """Bit-identical replacement for `RP.rotation_null`, for any context."""
    rng = np.random.default_rng(seed)
    pos = ctx.enforce(position, start)
    nz_i, nz_t = np.nonzero(pos)
    nz_v = pos[nz_i, nz_t]
    a_of, L_of = ctx.starts[nz_i], ctx.lens[nz_i]
    rel = nz_t - a_of                       # offset inside the symbol's window

    sh, mn = np.empty(n_sims), np.empty(n_sims)
    offs = np.empty(len(ctx.lens), dtype=np.int64)
    rot = np.zeros_like(pos)
    for k in range(n_sims):
        # the original's draw order, symbol by symbol, skipped for a one-bar
        # window exactly as the original skips it
        for i, L in enumerate(ctx.lens):
            offs[i] = int(rng.integers(0, L)) if L > 1 else 0
        rot[:] = 0.0
        # np.roll(seg, off)[j] = seg[(j - off) % L], so a value at window offset
        # `rel` lands at (rel + off) % L -- exact integer arithmetic on the ~1%
        # of cells that are non-zero.
        rot[nz_i, a_of + (rel + offs[nz_i]) % L_of] = nz_v
        sh[k], mn[k] = ctx.light_score(rot, start, rf_annual, borrow_annual, ppy)
    return sh, mn


EFFICIENCY_FLOOR = 0.70


def parallel_map(fn, items, workers=None, progress=None):
    """Threaded fan-out for ANY independent per-item work -- building books,
    scoring cells, computing per-cell diagnostics, not only nulls.

    Threads rather than processes: measured at 2.28x against 2.23x for processes
    on this workload, with no pickling, no per-worker panel reload and no spawn.
    `fn` must not mutate shared state; every context here is read-only.

    ALWAYS REPORTS ACHIEVED PARALLEL EFFICIENCY, and says so loudly below
    EFFICIENCY_FLOOR. Threads are the right call ONLY while the work releases the
    GIL, and that is a property of the workload, not of the decision -- D288 got
    0.24 of 16 cores, and D385 ran 92 minutes at 3.28x on 6 workers (55%) because
    nothing measured the scaling. Per-call cost is not scaling: the number below
    is sum(item time) / wall, which no amount of profiling one call will reveal.
    Under the floor, the fix is usually processes over `items[i::N]`."""
    items = list(items)
    workers = workers or max(1, min(len(items), DEFAULT_WORKERS))
    out, done, t0, spent = {}, 0, time.time(), []

    def _timed(k, v):
        s = time.time()
        try:
            return fn(k, v)
        finally:
            spent.append(time.time() - s)          # list.append is atomic under the GIL

    # A DUPLICATE KEY WOULD VANISH SILENTLY, AND THE PROGRESS LINE WOULD NOT SAY SO.
    # `out` is keyed by `k`, so two items sharing a key collapse to one while `done` still
    # counts to `len(items)` -- the run reports N results and returns fewer. The one
    # in-repo caller passes `books.items()`, where keys are unique by construction, but
    # the docstring above advertises this for ANY per-item work, and a caller passing a
    # list of pairs gets silent loss. Refusing costs one pass (D542).
    seen = [k for k, _ in items]
    if len(set(seen)) != len(seen):
        duplicates = sorted({k for k in seen if seen.count(k) > 1})
        raise ValueError(
            f"parallel_map keys its results by item key and {len(duplicates)} key(s) "
            f"repeat: {duplicates[:5]}. The later result would overwrite the earlier one "
            f"and the returned dict would be shorter than the {len(items)} the progress "
            f"line reports. Pass distinct keys."
        )

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_timed, k, v): k for k, v in items}
        for f in futs:
            k = futs[f]
            out[k] = f.result()
            done += 1
            if progress:
                print(f"    [{done}/{len(items)}] {k:24s} "
                      f"{time.time() - t0:6.0f}s", flush=True)

    wall = max(time.time() - t0, 1e-9)
    work = sum(spent)
    speedup = work / wall
    eff = speedup / max(workers, 1)
    if work < 5.0 or workers < 2:
        return out                                 # too small to measure; a ratio here is noise
    if progress or eff < EFFICIENCY_FLOOR:
        print(f"    [SPEED] {work:.0f}s of work in {wall:.0f}s wall on {workers} workers "
              f"-- {speedup:.2f}x, {100*eff:.0f}% efficiency", flush=True)
    if eff < EFFICIENCY_FLOOR:
        print(f"    [SPEED] BELOW THE {100*EFFICIENCY_FLOOR:.0f}% FLOOR: "
              f"{workers - speedup:.1f} of {workers} workers are idle. This work does not "
              f"release the GIL as assumed -- use processes over items[i::N], and prove the "
              f"chunked result matches the whole bit-identically first.", flush=True)
    return out


def run_nulls(ctx, books: dict, start=0, workers=None, progress=None, **kw):
    """Rotation nulls for every book, one thread each. Returns {key: (sh, mn)}."""
    return parallel_map(lambda k, p: rotation_null(ctx, p, start, **kw),
                        books.items(), workers=workers, progress=progress)


# --------------------------------------------------------------------------
# exactness and timing, on real fixtures
# --------------------------------------------------------------------------


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


def verify(n_books=4, n_sims=30) -> int:
    B, panel, books = _fixture_books(n_books)
    ctx = NullContext(panel)
    kw = dict(n_sims=n_sims, seed=0, ppy=B.PPY, rf_annual=B.RF_ANNUAL,
              borrow_annual=B.BORROW_ANNUAL)
    print(f"\n  {len(books)} books x {n_sims} sims -- EXACTNESS, not tolerance\n")

    ctx.assert_matches_scorer(
        books[next(iter(books))],
        lambda p: RP.score(panel, p, 0, ppy=B.PPY, rf_annual=B.RF_ANNUAL,
                           borrow_annual=B.BORROW_ANNUAL),
        rf_annual=B.RF_ANNUAL, borrow_annual=B.BORROW_ANNUAL, ppy=B.PPY)
    print("  [0] light_score agrees EXACTLY with RP.score on the real book")

    bad = 0
    for k, p in books.items():
        a_sh, a_mn = RP.rotation_null(panel, p, 0, **kw)
        b_sh, b_mn = rotation_null(ctx, p, 0, **kw)
        same = np.array_equal(a_sh, b_sh) and np.array_equal(a_mn, b_mn)
        print(f"    {k:8s} identical: {str(same):5s}   max abs diff "
              f"{max(float(np.max(np.abs(a_sh - b_sh))), float(np.max(np.abs(a_mn - b_mn)))):.3e}")
        bad += 0 if same else 1
    if bad:
        raise AssertionError(f"{bad} book(s) differ -- refusing to ship")
    print("\n  ALL BIT-IDENTICAL.")
    return 0


def bench(n_books=6, n_sims=100) -> int:
    B, panel, books = _fixture_books(n_books)
    ctx = NullContext(panel)
    w = max(1, min(len(books), DEFAULT_WORKERS))
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
    f2 = run_nulls(ctx, books, workers=w, **kw)
    t_f2 = time.time() - t0
    print(f"  FAST + {w} threads      {t_f2:7.1f}s   {t_ser / t_f2:5.2f}x", flush=True)

    for name, got in (("fast/serial", f1), ("fast/threaded", f2)):
        for k in books:
            if not (np.array_equal(ser[k][0], got[k][0])
                    and np.array_equal(ser[k][1], got[k][1])):
                raise AssertionError(f"{name} {k}: NOT bit-identical")
    print("\n  every path BIT-IDENTICAL to the original.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--bench", action="store_true")
    ap.add_argument("--books", type=int, default=4)
    ap.add_argument("--sims", type=int, default=30)
    a = ap.parse_args()
    if a.verify:
        raise SystemExit(verify(a.books, a.sims))
    if a.bench:
        raise SystemExit(bench(a.books, a.sims))
    ap.print_help()
    raise SystemExit(2)
