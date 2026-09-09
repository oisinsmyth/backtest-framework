"""Is the segmenter cutting on pivots that CONFIRM the trend rather than break it?

For a SUPPORT line a pivot ABOVE the line is a higher low -- the trend holding. Below it is a
violation. The current test is |r| > tau, which cannot tell them apart. This counts which side
each cut fired on, and what the alternatives would look like.
"""
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
PREP = _load("prep", "d348_prep.py")
from backtest_framework.research.structure import pivots as PV

gt = json.loads((REPO / "data" / "d399_live_ground_truth.json").read_text())
start, n = gt["start_bar"], gt["n"]

P = PREP.prep(need_grids=False, verbose=False)
panel, cleaned = RP.load_ragged(*DR.MINING, fee_bps=0.0, dividend_bound=True)
i_gme = panel.symbols.index("GME")
bars = cleaned["GME"]
m = len(bars)
lo = np.array([b.bar.low for b in bars], float)
hi = np.array([b.bar.high for b in bars], float)
ps = PV(bars, UO.K)
rvol = np.asarray(P["score"]("rvol21"))[i_gme]          # (T,), the name's own 21-bar vol

TAU = 0.08
print(f"\n  Every CUT the segmenter makes, classified by which side of the line the new pivot fell.")
print(f"  For SUPPORT: above the line = a HIGHER LOW = the trend holding. Below = a violation.")
print(f"  For RESISTANCE: below = a LOWER HIGH = holding. Above = a violation.\n")

for kind, sign, px in (("support", -1, lo), ("resistance", +1, hi)):
    idx = np.array([p.index for p in ps if p.sign == sign], dtype=int)
    lp = np.log([p.price for p in ps if p.sign == sign])
    cx, cy = [], []
    conf, viol, rows = 0, 0, []
    for p in range(len(idx)):
        x, y = float(idx[p]), float(lp[p])
        if len(cx) >= 2:
            b, a = SEG.ols(cx, cy)
            if np.isfinite(b):
                r = y - (b * x + a)
                if abs(r) > TAU and start <= idx[p] < start + n:
                    # for support (sign<0) a POSITIVE residual is above the line = confirming
                    confirming = (r > 0) if sign < 0 else (r < 0)
                    conf += confirming
                    viol += (not confirming)
                    gap = int(idx[p] - cx[-1])
                    v = rvol[idx[p]] if np.isfinite(rvol[idx[p]]) else np.nan
                    rows.append((int(idx[p]), r, confirming, gap, v))
                if abs(r) > TAU:
                    cx, cy = cx[-3:], cy[-3:]
        cx.append(x); cy.append(y)
    tot = conf + viol
    print(f"  {kind.upper()}: {tot} cuts inside the window")
    print(f"    {conf} on a CONFIRMING pivot ({100*conf/tot:.0f}%) -- the trend was holding and "
          f"it cut anyway")
    print(f"    {viol} on a violating pivot ({100*viol/tot:.0f}%)")
    rr = np.array([abs(r) for _b, r, _c, _g, _v in rows])
    gg = np.array([g for _b, _r, _c, g, _v in rows], float)
    vv = np.array([v for _b, _r, _c, _g, v in rows], float)
    ok = np.isfinite(vv) & (vv > 0)
    print(f"    bars since the previous pivot at the cut: median {np.median(gg):.0f} "
          f"(range {gg.min():.0f}-{gg.max():.0f})")
    if ok.any():
        # a diffusion-consistent yardstick: expected drift over `gap` bars at this name's vol
        exp = vv[ok] * np.sqrt(gg[ok])
        print(f"    |residual| / (rvol21 * sqrt(bars since last pivot)): median "
              f"{np.median(rr[ok] / exp):.2f}  -- 1.0 means 'exactly what a random walk would do'")
        print(f"    so a FIXED 8% threshold is worth {np.median(rr[ok] / exp):.2f} sigma at the "
              f"median and varies {(rr[ok]/exp).min():.2f}-{(rr[ok]/exp).max():.2f} across cuts")
    print()
