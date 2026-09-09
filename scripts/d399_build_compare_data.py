"""Build the side-by-side payload: the principal's drawn lines and the construction's, same bars.

    uv run python scripts/d399_build_compare_data.py [--branch E] [--min-piv 3] [--h-annual 4]

Writes temp/d399_compare_data.json -- GME's bars once, the hand-drawn lines as segments, the
construction's two lines as per-bar series, and a per-bar on/off ribbon for each side so the
COVERAGE difference is visible rather than only tabulated.

Nothing is scored here; scripts/d399_score_against_drawn.py does that. This is the drawing data.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
GT = REPO / "data" / "d399_drawn_ground_truth.json"
OUT = REPO / "temp" / "d399_compare_data.json"


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def clean(x, p=5):
    if isinstance(x, float):
        return None if not math.isfinite(x) else round(x, p)
    if isinstance(x, list):
        return [clean(v, p) for v in x]
    if isinstance(x, dict):
        return {k: clean(v, p) for k, v in x.items()}
    return x


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--branch", default="E")
    ap.add_argument("--min-piv", type=int, default=3)
    ap.add_argument("--h-annual", type=float, default=4.0)
    a = ap.parse_args()

    DR = _load("d399draw", "d399_draw_construction.py")
    UO = _load("d240_uptrend", "run_uptrend_onset.py")
    RP = _load("ragged_panel", "ragged_panel.py")
    from backtest_framework.research.structure import pivots as PV

    gt = json.loads(GT.read_text())
    sym, start, n = gt["symbol"], int(gt["start_bar"]), int(gt["n"])
    h = DR.h_of_annual(a.h_annual)

    panel, cleaned = RP.load_ragged(*DR.MINING, fee_bps=0.0, dividend_bound=True)
    bars = cleaned[sym]
    m = len(bars)
    o = np.array([b.bar.open for b in bars], float)
    hi = np.array([b.bar.high for b in bars], float)
    lo = np.array([b.bar.low for b in bars], float)
    cl = np.array([b.bar.close for b in bars], float)
    dates = [str(b.timestamp)[:10] for b in bars]
    ps = PV(bars, UO.K)
    sl = slice(start, start + n)

    out = dict(symbol=sym, start=start, n=n,
               branch=a.branch, min_piv=a.min_piv, h_annual_pct=a.h_annual, h=h, delta=DR.DELTA,
               dates=dates[sl], open=o[sl].tolist(), high=hi[sl].tolist(),
               low=lo[sl].tolist(), close=cl[sl].tolist(),
               drawn=gt["lines"], machine={}, ribbon={})

    for kind, sign, widen, px in (("support", -1, -1, lo), ("resistance", +1, +1, hi)):
        pidx = np.array([p.index for p in ps if p.sign == sign], dtype=int)
        ppx = np.log([p.price for p in ps if p.sign == sign]) if pidx.size else np.array([])
        G, L, anc, win = DR.segment_windows(pidx, ppx, np.log(px), m, UO.K, h, widen,
                                            min_piv=a.min_piv, max_window=UO.WINDOW)
        out["machine"][kind] = dict(line=np.exp(L[sl]).tolist(), g=G[sl].tolist(),
                                    anchor=anc[sl].astype(bool).tolist())
        hon = np.zeros(n, bool)
        for Ln in gt["lines"]:
            if Ln["kind"] == kind:
                hon[int(Ln["i0"]):int(Ln["i1"]) + 1] = True
        mon = np.isfinite(G[sl])
        out["ribbon"][kind] = dict(human=hon.astype(int).tolist(), machine=mon.astype(int).tolist(),
                                   human_bars=int(hon.sum()), machine_bars=int(mon.sum()),
                                   both=int((hon & mon).sum()))
        print(f"  {kind:>10s}: human {int(hon.sum()):>3d} bars, machine {int(mon.sum()):>3d}, "
              f"both {int((hon & mon).sum()):>3d}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(clean(out), allow_nan=False))
    print(f"\n  wrote {OUT.relative_to(REPO)} ({OUT.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
