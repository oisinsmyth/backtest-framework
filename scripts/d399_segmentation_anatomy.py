"""Take the segmentation apart on the real GME window: cuts, residuals, blind gaps, buffer sizes."""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(r"C:\Users\O\Desktop\Projects\Backtest Framework\.claude\worktrees\signal-hunt-part2")
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


SEG = _load("seg", "d399_alt_segment.py")
DR = _load("dr", "d399_draw_construction.py")
UO = _load("uo", "run_uptrend_onset.py")
RP = _load("rp", "ragged_panel.py")
from backtest_framework.research.structure import pivots as PV

gt = json.loads((REPO / "data" / "d399_live_ground_truth.json").read_text())
start, n, seen_to = gt["start_bar"], gt["n"], gt["seen_through"]

panel, cleaned = RP.load_ragged(*DR.MINING, fee_bps=0.0, dividend_bound=True)
bars = cleaned["GME"]
m = len(bars)
lo = np.array([b.bar.low for b in bars], float)
hi = np.array([b.bar.high for b in bars], float)
ps = PV(bars, UO.K)

TAU, CARRY, MINPIV = 0.08, 3, 5
print(f"\n  CONFIG: slide / abs / tau={TAU} / carry={CARRY} / min_piv={MINPIV} / delta-gate")
print(f"  tau = {TAU} in LOG price, i.e. a pivot more than {100*(np.expm1(TAU)):.1f}% off the "
      f"current line breaks the segment\n")

for kind, sign, px in (("support", -1, lo), ("resistance", +1, hi)):
    idx = np.array([p.index for p in ps if p.sign == sign], dtype=int)
    lp = np.log([p.price for p in ps if p.sign == sign])
    inwin = (idx >= start) & (idx < start + n)
    print(f"  {kind.upper()}: {int(inwin.sum())} confirmed pivots inside the 260-bar window "
          f"(median {np.median(np.diff(idx[inwin])):.0f} bars apart)")

    # replay the segmenter, recording every decision
    cx, cy, cuts, bufs, resids = [], [], [], [], []
    for p in range(len(idx)):
        x, y = float(idx[p]), float(lp[p])
        cut = False
        if len(cx) >= 2:
            b, a = SEG.ols(cx, cy)
            if np.isfinite(b):
                r = y - (b * x + a)
                resids.append((int(idx[p]), abs(r)))
                if abs(r) > TAU:
                    cut = True
                    cx, cy = cx[-CARRY:], cy[-CARRY:]
        cx.append(x); cy.append(y)
        if start <= idx[p] < start + n:
            bufs.append(len(cx))
            if cut:
                cuts.append(int(idx[p]))
    rr = np.array([r for b_, r in resids if start <= b_ < start + n])
    print(f"    residual of each new pivot from the running line: median "
          f"{100*np.expm1(np.median(rr)):.1f}%, p90 {100*np.expm1(np.quantile(rr,.9)):.1f}%, "
          f"max {100*np.expm1(rr.max()):.0f}%")
    print(f"    CUTS inside the window: {len(cuts)} at bars {cuts}")
    print(f"    buffer size when a state is emitted: median {np.median(bufs):.0f} pivots, "
          f"min {min(bufs)}, max {max(bufs)}")
    below = sum(1 for b_ in bufs if b_ < MINPIV)
    print(f"    emissions with FEWER than min_piv={MINPIV} pivots (so: no trend): "
          f"{below}/{len(bufs)}")

    ev = SEG.sliding_events(idx, lp, UO.K, "abs", TAU, 0.0, CARRY)
    G, S = SEG.broadcast(ev, m, MINPIV, True, DR.DELTA)
    Gw = G[start:start + n]
    on = np.isfinite(Gw)
    runs, i = [], 0
    while i < n:
        if not on[i]:
            i += 1; continue
        j = i
        while j + 1 < n and on[j + 1] and Gw[j + 1] == Gw[i]:
            j += 1
        runs.append(j - i + 1); i = j + 1
    print(f"    -> state ON for {int(on.sum())}/{n} bars in {len(runs)} runs, "
          f"median run {np.median(runs):.0f} bars\n")

print(f"  the principal, drawn live: 25 lines, median life {gt['median_live_bars']:.0f} bars, "
      f"no trend on {100*gt['bars_no_trend']/221:.0f}% of bars he saw")
