"""D288 -- the two GIL-BOUND score families, computed in a separate PROCESS.

    uv run python scripts/d288_build_worker.py --chunk 0 --of 8 --out temp/c0.npz
    uv run python scripts/d288_build_worker.py --verify

WHY PROCESSES AND NOT THREADS, MEASURED RATHER THAN ASSUMED.

`parallel_map` threads are the right tool for nulls, candidates and draws -- all
numpy, all releasing the GIL, measured at 6.00x and 2.28x. They are the WRONG
tool for these two families and the difference is not marginal:

    C `volume_scores`        309s   4.1M np.polyfit calls, pure Python
    D `build_profile_scores` ~700s  VolumeProfileSensor.density at 0.17 ms
                                    x 4,137,239 bars, pure Python

Both hold the GIL, so threading them INTERLEAVES rather than overlaps. Measured
on the seven-family thread fan-out: 602s of CPU across 28 minutes of wall clock,
about 36% of one core, with the working set at 4.9 GB because every family's
intermediates were alive at once. Serial would have been ~17 minutes; threaded
was tracking to ~47. **Threading this made it slower.**

Processes do not share a GIL, so this is the version that actually parallelises.

WHY A SUBPROCESS RATHER THAN ProcessPoolExecutor. The modules here are loaded by
`importlib.util.spec_from_file_location`, so they are not importable by name in a
spawned child and nothing in them pickles by reference. A plain script per chunk
sidesteps that entirely, and each chunk's 19-second panel load happens in
parallel with the others.

CHUNKS ARE STRIDED, NOT CONTIGUOUS. Symbols differ in length by more than an
order of magnitude and both costs scale with bar count, so `symbols[i::N]`
balances the workers where `symbols[a:b]` would leave one holding every long
name.

NOTHING HERE IS A NEW ESTIMATOR. Both families are called with ROW-SLICED inputs
and both loop strictly per symbol, using only row `i` -- so a chunk computes the
same numbers the whole panel would. `--verify` proves that rather than asserting
it: it builds 40 symbols whole, builds them again in 3 strided chunks, and
requires BIT-IDENTICAL output including the NaN pattern.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import time
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


B = _load("d256", "run_book_single_names.py")
RP = _load("ragged_panel", "ragged_panel.py")
RF = _load("ragged_features", "ragged_features.py")
PR = _load("ragged_profile", "ragged_profile.py")

KEYS = tuple(RF.VOL_SCORES) + tuple(PR.PROFILE_SCORES)


def subset_rows(panel, idx):
    """A row subset of the panel. NOT a copy of the study -- the same arrays,
    sliced, so a chunk sees exactly what the whole panel would give it."""
    syms = [panel.symbols[i] for i in idx]
    cf = panel.cost_fraction
    cf = cf[idx] if isinstance(cf, np.ndarray) and cf.ndim and cf.shape[0] == len(
        panel.symbols) else cf
    return RP.RaggedPanel(syms, panel.dates, panel.closes[idx],
                          panel.log_returns[idx], panel.total_log_returns[idx],
                          cf, panel.live[idx],
                          {s: panel.index_of[s] for s in syms})


def build_chunk(panel, cleaned, idx):
    """C and D for the given symbol rows. Returns {name: (len(idx), T)}."""
    sub = subset_rows(panel, idx)
    subc = {s: cleaned[s] for s in sub.symbols}
    vol, vpx = RF.volume_grids(sub, subc, live=sub.live)
    out = dict(RF.volume_scores(vol, vpx, sub.total_log_returns, sub.live))
    prof, census = PR.build_profile_scores(sub, subc, vol, 0, live=sub.live)
    out.update(prof)
    return out, census


def verify() -> int:
    t0 = time.time()
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=B.FEE_BPS)
    idx = np.arange(40)
    print(f"loaded in {time.time() - t0:.0f}s; verifying on {idx.size} symbols",
          flush=True)

    whole, _ = build_chunk(panel, cleaned, idx)
    parts = {}
    for c in range(3):
        sub = idx[c::3]
        got, _ = build_chunk(panel, cleaned, sub)
        for k, v in got.items():
            parts.setdefault(k, np.full(whole[k].shape, np.nan))[sub] = v

    bad = 0
    for k in KEYS:
        a, b = whole[k], parts[k]
        fa, fb = np.isfinite(a), np.isfinite(b)
        if not np.array_equal(fa, fb):
            print(f"  {k}: NaN PATTERN MOVED on {int((fa ^ fb).sum()):,} cells")
            bad += 1
        elif not np.array_equal(a[fa], b[fb]):
            d = np.abs(a[fa] - b[fb])
            print(f"  {k}: {int((d > 0).sum()):,} cells CHANGED, max {d.max():.3e}")
            bad += 1
        else:
            print(f"  {k:16s} bit-identical, {int(fa.sum()):,} cells")
    assert bad == 0, f"{bad} score(s) differ when computed in chunks"
    print(f"\nOK  chunked == whole on all {len(KEYS)} scores  "
          f"({time.time() - t0:.0f}s)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunk", type=int)
    ap.add_argument("--of", type=int)
    ap.add_argument("--out")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    if a.verify:
        return verify()
    if a.chunk is None or a.of is None or not a.out:
        print(__doc__)
        return 0

    t0 = time.time()
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=B.FEE_BPS)
    idx = np.arange(len(panel.symbols))[a.chunk::a.of]
    out, census = build_chunk(panel, cleaned, idx)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    np.savez(a.out, rows=idx, **out)
    print(f"chunk {a.chunk}/{a.of}: {idx.size} symbols, census {census}, "
          f"{time.time() - t0:.0f}s -> {a.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
