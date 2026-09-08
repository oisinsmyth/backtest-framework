"""What threshold would a stop / target need to fire on a SENSIBLE fraction of trades?

The principal's objection to D380: a stop firing on 79% of trades is not a stop for that strategy, and the same for an 81% target.
+/-200 bp was declared to avoid a sweep -- a good instinct on the wrong scale. It was set from the TERMINAL mean per trade, when the
quantity that decides the fire rate is the PATH's excursion distribution.

This is a CALIBRATION, not a result: the threshold <-> fire-rate mapping is a descriptive property of the paths and adjudicates
nothing. Reported so a corrected study can pre-register a FIRE RATE rather than a bp level -- D374's lesson applied to my own choice.
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
spec = importlib.util.spec_from_file_location("d380", REPO / "scripts" / "run_d380_exit_rules.py")
m = importlib.util.module_from_spec(spec)
sys.modules["d380"] = m
spec.loader.exec_module(m)

P = m.prep()
res0 = m.baseline(P)
C, holds0 = m.trade_paths(P, res0)
pnl0 = np.asarray(m.V47.pnl_bp(res0), float)
n = C.shape[0]

# each trade's best and worst point along its own path, within its own hold
mask = np.arange(C.shape[1])[None, :] < holds0[:, None]
up = np.where(mask, C, -np.inf).max(axis=1)
dn = np.where(mask, C, np.inf).min(axis=1)

print(f"baseline {n:,} trades  mean {pnl0.mean():+.2f}  median {np.median(pnl0):+.2f}")
print(f"  max favourable excursion: p50 {np.median(up):+8.1f}  p75 {np.percentile(up, 75):+8.1f}  p90 {np.percentile(up, 90):+8.1f}")
print(f"  max adverse    excursion: p50 {np.median(dn):+8.1f}  p25 {np.percentile(dn, 25):+8.1f}  p10 {np.percentile(dn, 10):+8.1f}")

print("\nTARGET -- threshold needed for a given fire rate (share of trades whose path ever reaches it)")
for rate in (0.05, 0.10, 0.20, 0.30, 0.50, 0.807):
    thr = float(np.quantile(up, 1.0 - rate))
    print(f"    fire {rate:>5.1%}  ->  target {thr:+9.1f} bp")
print(f"    the declared +200 bp fires on {float((up >= 200).mean()):.1%}")

print("\nSTOP -- threshold needed for a given fire rate")
for rate in (0.05, 0.10, 0.20, 0.30, 0.50, 0.791):
    thr = float(np.quantile(dn, rate))
    print(f"    fire {rate:>5.1%}  ->  stop   {thr:+9.1f} bp")
print(f"    the declared -200 bp fires on {float((dn <= -200).mean()):.1%}")

print("\nTAIL-ROBUST BASELINE, from D373's committed four_groups -- what the mean looks like without its best trades")
k = max(1, int(0.01 * n))
srt = np.sort(pnl0)
print(f"    mean            {pnl0.mean():+8.2f}")
print(f"    trimmed 1% both {srt[k:-k].mean():+8.2f}")
print(f"    ex-top 1%       {srt[:-k].mean():+8.2f}   <- compare to D380's target arm at +62.43")
