"""D290 -- the FOUR GIL-bound score families, computed in a separate PROCESS.

    uv run python scripts/d290_build_worker.py --chunk 0 --of 8 --out temp/c0.npz
    uv run python scripts/d290_build_worker.py --verify

WHICH FAMILIES AND WHY, measured rather than assumed. CLAUDE.md's rule is threads
for numpy and read-only fan-out, processes for GIL-bound pure Python. These four
are pure-Python per-symbol loops:

    C  volume_scores        ~309s   4.1M np.polyfit calls
    D  build_profile_scores ~700s   density() at 0.17 ms x 4,137,239 bars
    G  anomaly_scores       ~110s   per-symbol trailing windows
    H  structure_scores        ?s   market_structure + fair_value_gaps per symbol

Threading them was measured WORSE on D288's build: a seven-family thread fan-out
ran 602s of CPU across 28 minutes of wall clock -- 0.24 of 16 cores -- because
GIL-bound families interleave rather than overlap. Eight processes over
`symbols[i::N]` did the same work in 4 minutes at 6.1 cores.

STRIDED, NOT CONTIGUOUS. Bar counts vary by an order of magnitude and every one
of these costs scales with them, so `symbols[i::N]` balances the workers where
`symbols[a:b]` would leave one holding every long name. Measured spread across
D288's eight chunks: 8%.

THE ONE QUANTITY THAT IS NOT ROW-LOCAL, AND THE BUG CHUNKING WOULD HAVE CAUSED.
Axis G's `beta_63` and `ivol_21` regress each name on an EQUAL-WEIGHT MARKET
RETURN taken across the whole live cross-section. A worker holding 197 of 1,573
symbols that recomputed that from its own rows would regress on a 197-name
"market" -- a different estimator, with no error raised and no NaN to notice. So
the market return is computed ONCE from the FULL panel and passed into the
subset. Everything else here is strictly per-symbol.

`--verify` proves a chunk computes what the whole panel computes, bit-identically
including the NaN pattern, before any of this is trusted.
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
P1 = _load("d280p1", "d280_forecast_precheck.py")
RF = _load("ragged_features", "ragged_features.py")
PR = _load("ragged_profile", "ragged_profile.py")
AN = _load("ragged_anomaly_scores", "ragged_anomaly_scores.py")
ST = _load("ragged_structure_scores", "ragged_structure_scores.py")

KEYS = (tuple(RF.VOL_SCORES) + tuple(PR.PROFILE_SCORES)
        + tuple(AN.ANOMALY_SCORES) + tuple(ST.STRUCTURE_SCORES))


def subset_rows(panel, idx):
    """A row subset of the panel -- the same arrays, sliced."""
    syms = [panel.symbols[i] for i in idx]
    cf = panel.cost_fraction
    cf = cf[idx] if isinstance(cf, np.ndarray) and cf.ndim and \
        cf.shape[0] == len(panel.symbols) else cf
    return RP.RaggedPanel(syms, panel.dates, panel.closes[idx],
                          panel.log_returns[idx], panel.total_log_returns[idx],
                          cf, panel.live[idx],
                          {s: panel.index_of[s] for s in syms})


def build_chunk(panel, cleaned, g, mkt, idx):
    """C, D, G and H for the given symbol rows. Returns {name: (len(idx), T)}."""
    sub = subset_rows(panel, idx)
    subc = {s: cleaned[s] for s in sub.symbols}
    subg = {k: v[idx] for k, v in g.items()}
    vol, vpx = RF.volume_grids(sub, subc, live=sub.live)

    out = dict(RF.volume_scores(vol, vpx, sub.total_log_returns, sub.live))
    prof, census = PR.build_profile_scores(sub, subc, vol, 0, live=sub.live)
    out.update(prof)
    # mkt PASSED IN, never recomputed here -- see the module docstring.
    out.update(AN.anomaly_scores(subg, sub, sub.live, vol=vol, mkt=mkt))
    out.update(ST.structure_scores(subg, subc, sub, sub.live))
    return out, census


def _load_all():
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=B.FEE_BPS)
    g = P1.build_grids(panel, cleaned)
    mkt = AN.market_return(panel.total_log_returns, panel.live)
    return panel, cleaned, g, mkt


def verify() -> int:
    t0 = time.time()
    panel, cleaned, g, mkt = _load_all()
    idx = np.arange(40)
    print(f"loaded in {time.time() - t0:.0f}s; verifying on {idx.size} symbols",
          flush=True)

    whole, _ = build_chunk(panel, cleaned, g, mkt, idx)
    parts = {}
    for c in range(3):
        sub = idx[c::3]
        got, _ = build_chunk(panel, cleaned, g, mkt, sub)
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
    panel, cleaned, g, mkt = _load_all()
    idx = np.arange(len(panel.symbols))[a.chunk::a.of]
    out, census = build_chunk(panel, cleaned, g, mkt, idx)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    np.savez(a.out, rows=idx, **out)
    print(f"chunk {a.chunk}/{a.of}: {idx.size} symbols, census {census}, "
          f"{time.time() - t0:.0f}s -> {a.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
