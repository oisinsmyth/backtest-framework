"""D290 -- assemble the 51-candidate score cache.

    uv run python scripts/d290_build_cache.py [--procs 8] [--reuse-chunks]

Writes `temp/d290_scores.npz`. The screen, the nulls, the name-split CV and the
confluence sweep all read it, so the build is paid once rather than four times.

THE SPLIT IS BY WHO HOLDS THE GIL, which is CLAUDE.md's rule and was measured on
D288's build rather than assumed:

    IN THIS PROCESS, serial -- numpy, all sub-15s
      B intrabar 0.4s   F session 2.1s   E vol 4.5s   A345 price 8.9s
      A12 signals 14.6s

    IN 8 PROCESSES -- pure-Python per-symbol loops
      C volume ~309s    D profile ~700s    G anomaly ~110s    H structure ~7min+

Threading the second group was measured WORSE: 602s of CPU across 28 minutes of
wall clock, 0.24 of 16 cores, because GIL-bound families interleave rather than
overlap. Eight processes did D288's C+D in 4 minutes at 6.1 cores. H alone is
slower single-threaded than C and D were, so the fan-out matters more here, not
less.

`d290_build_worker.py --verify` proves a chunk computes what the whole panel
computes, bit-identically, before any of this is trusted.
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


B = _load("d256", "run_book_single_names.py")
RP = _load("ragged_panel", "ragged_panel.py")
P1 = _load("d280p1", "d280_forecast_precheck.py")
SP = _load("d285sp", "d285_spread_estimate.py")
RF = _load("ragged_features", "ragged_features.py")
PS = _load("ragged_price_scores", "ragged_price_scores.py")
PR = _load("ragged_profile", "ragged_profile.py")
VS = _load("ragged_vol_scores", "ragged_vol_scores.py")
SS = _load("ragged_session_scores", "ragged_session_scores.py")
AN = _load("ragged_anomaly_scores", "ragged_anomaly_scores.py")
ST = _load("ragged_structure_scores", "ragged_structure_scores.py")
W = _load("d290_build_worker", "d290_build_worker.py")

CACHE = REPO / "temp" / "d290_scores.npz"

# The 51. Axis A now carries SEVEN, not five: `rsi` and `impulse_nodz` were built
# for D288 and disclosed as "built but NOT screened, by pre-registration". They
# are in the same module and cost nothing, so under a re-run they are screened.
AXES = {
    "A": ("hist_L", "md") + tuple(PS.PRICE_SCORES),
    "B": tuple(RF.INTRABAR_SCORES),
    "C": tuple(RF.VOL_SCORES),
    "D": tuple(PR.PROFILE_SCORES),
    "E": tuple(VS.VOL_LEVEL_SCORES),
    "F": tuple(SS.SESSION_SCORES),
    "G": tuple(AN.ANOMALY_SCORES),
    "H": tuple(ST.STRUCTURE_SCORES),
}
CANDIDATES = tuple(c for ax in "ABCDEFGH" for c in AXES[ax])
AXIS_OF = {c: ax for ax, cs in AXES.items() for c in cs}
assert len(set(CANDIDATES)) == len(CANDIDATES), "duplicate candidate name"


def cache_key(fixture):
    st = Path(fixture).stat()
    parts = [f"{Path(fixture).name}:{st.st_size}:{int(st.st_mtime)}"]
    for f in ("run_book_single_names.py", "ragged_features.py",
              "ragged_price_scores.py", "ragged_profile.py",
              "ragged_vol_scores.py", "ragged_session_scores.py",
              "ragged_anomaly_scores.py", "ragged_structure_scores.py",
              "d285_spread_estimate.py"):
        parts.append(f"{f}:{int((REPO / 'scripts' / f).stat().st_mtime)}")
    parts.append("|".join(CANDIDATES))
    return "\n".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, default=8)
    ap.add_argument("--reuse-chunks", action="store_true")
    a = ap.parse_args()

    t0 = time.time()
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=B.FEE_BPS)
    live = panel.live
    n, T = live.shape
    g = P1.build_grids(panel, cleaned)
    print(f"loaded {n} x {T} in {time.time() - t0:.0f}s | "
          f"{len(CANDIDATES)} candidates across {len(AXES)} axes", flush=True)

    chunks = [REPO / "temp" / f"d290_chunk_{i}.npz" for i in range(a.procs)]
    if not a.reuse_chunks:
        print(f"  fanning C, D, G, H across {a.procs} PROCESSES", flush=True)
        t = time.time()
        procs = [subprocess.Popen(
            [sys.executable, str(REPO / "scripts" / "d290_build_worker.py"),
             "--chunk", str(i), "--of", str(a.procs), "--out", str(chunks[i])],
            cwd=str(REPO), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True) for i in range(a.procs)]
        for i, p in enumerate(procs):
            out, _ = p.communicate()
            if p.returncode != 0:
                print(out)
                raise SystemExit(f"chunk {i} failed with {p.returncode}")
            print(f"    {out.strip().splitlines()[-1]}", flush=True)
        print(f"  chunks done in {time.time() - t:.0f}s", flush=True)

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
    print(f"  merged {len(chunks)} chunks; all {n} rows written exactly once",
          flush=True)

    print(f"  fast families, serial in this process", flush=True)
    t = time.time()
    md, hs, _, _, _, _, warm = B.signals_ragged(panel, cleaned, 0)
    price, pwarm = PS.price_scores(panel, cleaned, live=live)
    sc = {"hist_L": hs, "md": md}
    for k in PS.PRICE_SCORES:
        sc[k] = np.where(pwarm[k], price[k], np.nan)
    sc.update(RF.intrabar_scores(g, live))
    sc.update(VS.vol_level_scores(
        g, live, SP.corwin_schultz(g["high"], g["low"], live)))
    sc.update(SS.session_scores(g, live))
    sc.update(slow)
    print(f"  fast families in {time.time() - t:.0f}s", flush=True)

    missing = [c for c in CANDIDATES if c not in sc]
    assert not missing, f"candidates not built: {missing}"
    out = {c: sc[c] for c in CANDIDATES}

    CACHE.parent.mkdir(parents=True, exist_ok=True)
    t = time.time()
    np.savez(CACHE, key=np.array(cache_key(B.FIXTURE)), warm=warm, **out)
    print(f"\n  wrote {CACHE.relative_to(REPO)}  "
          f"{CACHE.stat().st_size / 1e9:.2f} GB in {time.time() - t:.0f}s")

    base = warm & live
    print(f"\n  COVERAGE, shared base {int(base.sum()):,} warm live cells")
    for ax in "ABCDEFGH":
        cs = AXES[ax]
        cov = [np.isfinite(out[c] & base if out[c].dtype == bool
                           else np.where(base, out[c], np.nan)).sum() for c in cs]
        lo, hi = min(cov) / base.sum(), max(cov) / base.sum()
        print(f"    {ax}  {len(cs)} candidates   coverage {lo:5.1%} .. {hi:5.1%}")
        assert min(cov) > 0, f"axis {ax} has an empty candidate"
    print(f"  TOTAL {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
