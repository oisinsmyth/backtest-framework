"""How many times does each construction END a trend, against how many times one really ends?

    uv run python scripts/d399_cuts_vs_real_ends.py

The channel diagnostic established that in this 260-bar window there are exactly THREE genuine
trend endings -- the three bars where a body leaves one of the principal's three channels. Every
construction, meanwhile, cuts far more often, because all of them end a trend whenever the fitted
gradient moves.

This counts the cuts and asks how many land near a real ending. It changes no score: the scorer
compares gradients, and nothing here enters it. It measures the thing the principal's correction
made measurable -- WHEN a trend should end -- which no score so far has looked at.

Scores nothing. Admits nothing (R15).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
GT = REPO / "data" / "d399_drawn_ground_truth.json"
CH = REPO / "data" / "d399_channel_end_diagnostic.json"
OUT = REPO / "data" / "d399_cuts_vs_real_ends.json"
NEAR = 5          # a cut counts as finding a real ending if it lands within this many bars


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def main() -> int:
    DR = _load("d399draw", "d399_draw_construction.py")
    UO = _load("d240", "run_uptrend_onset.py")
    RP = _load("rp", "ragged_panel.py")
    SEG = _load("d399seg", "d399_alt_segment.py")
    PP = _load("d399pp", "d399_alt_pivotpair.py")
    from backtest_framework.research.structure import pivots as PV

    gt = json.loads(GT.read_text())
    ch = json.loads(CH.read_text())
    start, n = int(gt["start_bar"]), int(gt["n"])

    # the real endings: a BODY leaving a channel, zero tolerance -- the principal's convention
    real = sorted({p["breaks"]["body|0"]["first_break"] for p in ch["pairs"]
                   if p.get("breaks") and p["breaks"]["body|0"]["first_break"] is not None})
    print(f"\n  REAL trend endings in this window (body leaves a channel, 0% tolerance):")
    for b in real:
        which = [p for p in ch["pairs"] if p.get("breaks")
                 and p["breaks"]["body|0"]["first_break"] == b][0]
        print(f"    bar {b:>3d}  {which['breaks']['body|0']['date']}  "
              f"broke the {which['breaks']['body|0']['side']} side")
    print(f"    -> {len(real)} endings in {n} bars\n")

    panel, cleaned = RP.load_ragged(*DR.MINING, fee_bps=0.0, dividend_bound=True)
    bars = cleaned[gt["symbol"]]
    m = len(bars)
    hi = np.array([b.bar.high for b in bars], float)
    lo = np.array([b.bar.low for b in bars], float)
    ps = PV(bars, UO.K)

    def piv(sign):
        idx = np.array([p.index for p in ps if p.sign == sign], dtype=int)
        lp = np.log([p.price for p in ps if p.sign == sign]) if idx.size else np.array([])
        return idx, lp

    cuts = {}

    # branch E -- dynamic windows, min_piv 3, h 4%/yr
    h4 = DR.h_of_annual(4.0)
    cE = []
    for kind, sign, px in (("support", -1, lo), ("resistance", +1, hi)):
        idx, lp = piv(sign)
        _G, _L, anc, _w = DR.segment_windows(idx, lp, np.log(px), m, UO.K, h4, sign,
                                             min_piv=3, max_window=UO.WINDOW)
        cE += [int(b) - start for b in np.flatnonzero(anc) if start < b < start + n]
    cuts["branch E (dynamic windows)"] = sorted(cE)

    # piecewise segmentation -- its best cell
    cS = []
    for kind, sign, px in (("support", -1, lo), ("resistance", +1, hi)):
        idx, lp = piv(sign)
        ev = SEG.sliding_events(idx, lp, UO.K, "abs", 0.08, 0.0, 3)
        G, S = SEG.broadcast(ev, m, 5, True, DR.DELTA)
        Sw = S[start:start + n]
        cS += [int(j) for j in range(1, n) if Sw[j] != Sw[j - 1] and Sw[j] >= 0]
    cuts["piecewise segmentation"] = sorted(cS)

    # chartist two-pivot -- its best cell
    dat = PP.load_data(UO.K)
    cells = PP.run_cell(dat, "b_far", 0.0, 42, True, UO.K, {})
    cP = []
    for kind in ("support", "resistance"):
        G, _L, _a, _b = cells[kind]
        G = PP.apply_min_run(PP.apply_delta(G, DR.DELTA), DR.MIN_RUN)
        Gw = G[start:start + n]
        cP += [int(j) for j in range(1, n)
               if np.isfinite(Gw[j]) and (not np.isfinite(Gw[j - 1]) or Gw[j] != Gw[j - 1])]
    cuts["chartist two-pivot"] = sorted(cP)

    res = dict(real_endings=real, near_bars=NEAR, n=n, constructions={})
    print(f"  {'construction':>26s} {'cuts':>6s} {'per real ending':>16s} "
          f"{'found':>7s} {'median gap':>11s}")
    for name, cs in cuts.items():
        cs = sorted(set(cs))
        found, gaps = 0, []
        for b in real:
            d = min((abs(c - b) for c in cs), default=10 ** 9)
            gaps.append(d)
            if d <= NEAR:
                found += 1
        res["constructions"][name] = dict(n_cuts=len(cs), cuts=cs, found=found,
                                          gaps=gaps, ratio=round(len(cs) / max(len(real), 1), 1))
        print(f"  {name:>26s} {len(cs):>6d} {len(cs) / len(real):>15.1f}x "
              f"{f'{found}/{len(real)}':>7s} {np.median(gaps):>11.0f}")

    print(f"\n  'per real ending' = cuts made for every trend that actually ended.")
    print(f"  'found' = real endings with a cut within {NEAR} bars. 'median gap' = bars from a "
          f"real ending to the nearest cut.\n")

    OUT.write_text(json.dumps(res, indent=1))
    print(f"  [P] {OUT.relative_to(REPO)} written")
    print("\nDIAGNOSTIC. No score changed; nothing is admitted (R15).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
