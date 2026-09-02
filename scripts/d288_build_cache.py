"""D288 -- assemble the score cache: fast families here, slow families in processes.

    uv run python scripts/d288_build_cache.py [--procs 8]

Writes `temp/d288_scores.npz` with the key `run_mine_neutral.build_scores`
expects, so the screen, gate 0, gate A and gate B all load it in seconds instead
of rebuilding it four times.

THE SPLIT IS BY WHO HOLDS THE GIL, MEASURED:

    IN THIS PROCESS, serial -- all numpy, all sub-15s
      B intrabar 0.4s   F session 2.1s   E vol 4.5s
      A3-A5 price 8.9s  A1-A2 signals 14.6s

    IN SEPARATE PROCESSES -- pure Python, ~17 minutes between them
      C volume_scores          309s    4.1M np.polyfit calls
      D build_profile_scores  ~700s    density() at 0.17ms x 4.1M bars

Threading the second group was tried and MEASURED WORSE: a seven-family thread
fan-out ran at 602s of CPU across 28 minutes of wall clock -- about 36% of ONE
core of sixteen -- with the working set at 4.9 GB because every family's
intermediates were alive at once. Serial would have been ~17 minutes; threaded
was tracking to ~47. Two GIL-bound families interleave, they do not overlap, and
holding them open together costs memory for nothing.

`scripts/d288_build_worker.py --verify` proves a chunk computes what the whole
panel computes, bit-identically, before any of this is trusted.
"""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
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


M = _load("run_mine_neutral", "run_mine_neutral.py")
W = _load("d288_build_worker", "d288_build_worker.py")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, default=8)
    ap.add_argument("--reuse-chunks", action="store_true",
                    help="skip the fan-out and merge temp/chunk_*.npz as they are")
    a = ap.parse_args()

    t0 = time.time()
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    live = panel.live
    n, T = live.shape
    g = M.P1.build_grids(panel, cleaned)
    print(f"loaded {n} x {T} in {time.time() - t0:.0f}s", flush=True)

    chunks = [REPO / "temp" / f"chunk_{i}.npz" for i in range(a.procs)]
    if not a.reuse_chunks:
        print(f"  fanning C and D across {a.procs} PROCESSES", flush=True)
        t = time.time()
        procs = [subprocess.Popen(
            [sys.executable, str(REPO / "scripts" / "d288_build_worker.py"),
             "--chunk", str(i), "--of", str(a.procs), "--out", str(chunks[i])],
            cwd=str(REPO), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True) for i in range(a.procs)]
        for i, p in enumerate(procs):
            out, _ = p.communicate()
            if p.returncode != 0:
                print(out)
                raise SystemExit(f"chunk {i} failed with {p.returncode}")
        print(f"  chunks done in {time.time() - t:.0f}s", flush=True)

    # merge -- every row must be written exactly once, and that is CHECKED
    slow = {k: np.full((n, T), np.nan) for k in W.KEYS}
    seen = np.zeros(n, dtype=int)
    for c in chunks:
        z = np.load(c, allow_pickle=False)
        rows = z["rows"]
        seen[rows] += 1
        for k in W.KEYS:
            slow[k][rows] = z[k]
    assert (seen == 1).all(), (
        f"merge is not a partition: {int((seen == 0).sum())} rows unwritten, "
        f"{int((seen > 1).sum())} written twice")
    print(f"  merged {len(chunks)} chunks; every one of {n} rows written exactly once",
          flush=True)

    print(f"  fast families, serial in this process", flush=True)
    t = time.time()
    md, hs, _, _, _, _, warm = M.B.signals_ragged(panel, cleaned, 0)
    price, pwarm = M.PS.price_scores(panel, cleaned, live=live)
    sc = {"hist_L": hs, "md": md}
    for k in ("macd_hist", "macd_line", "trailing_return"):
        sc[k] = np.where(pwarm[k], price[k], np.nan)
    sc.update(M.RF.intrabar_scores(g, live))
    sc.update(M.VS.vol_level_scores(
        g, live, M.SP.corwin_schultz(g["high"], g["low"], live)))
    sc.update(M.SS.session_scores(g, live))
    sc.update(slow)
    print(f"  fast families in {time.time() - t:.0f}s", flush=True)

    missing = [c for c in M.CANDIDATES if c not in sc]
    assert not missing, f"candidates not built: {missing}"
    out = {c: sc[c] for c in M.CANDIDATES}

    M.CACHE.parent.mkdir(parents=True, exist_ok=True)
    t = time.time()
    np.savez(M.CACHE, key=np.array(M._cache_key(M.B.FIXTURE)), warm=warm, **out)
    print(f"\n  wrote {M.CACHE.relative_to(REPO)}  "
          f"{M.CACHE.stat().st_size / 1e9:.2f} GB in {time.time() - t:.0f}s")
    print(f"  TOTAL {time.time() - t0:.0f}s")
    for c in M.CANDIDATES:
        fin = int((np.isfinite(out[c]) & live).sum())
        assert fin > 0, f"{c} produced nothing"
    print(f"  all {len(out)} candidates non-empty")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
