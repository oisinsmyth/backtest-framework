"""D426 extra: rung-2 return in cell 2 by the gap to its prior touch and by the prior's side; and the
prior (rung-1) trade's own return by the same gap. Reads existing arrays only."""
import importlib.util, json, pathlib, sys
import numpy as np
REPO = pathlib.Path(r"C:\Users\O\Desktop\Projects\Backtest Framework")
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s); sys.modules[name] = m; s.loader.exec_module(m); return m
RF = _load("d426f", "d426_rung_flags.py")
I, P, B, fl, M, zones = RF.load(); F = RF.flags(I, fl)
c2, rb, side = I["c2"], I["r_base"], I["side"]
prim = fl["s2any"] & c2; g = F["prev_gap"]; pk = F["prev_k"]; same = pk >= 0
out = {}
print("rung 2 & cell 2 (9,411): return by gap to the prior touch, prior same-side vs opposite-side")
for lo, hi in ((1, 2), (3, 5), (6, 10), (11, 20)):
    m = prim & (g >= lo) & (g <= hi)
    row = {}
    for lab, mm in (("all", m), ("same-side prior", m & same), ("opposite prior", m & ~same)):
        x = rb[mm]; x = x[np.isfinite(x)]
        row[lab] = dict(n=int(x.size), mean=float(1e4 * x.mean()), se=float(1e4 * x.std(ddof=1) / np.sqrt(x.size)))
    out[f"gap {lo}-{hi}"] = row
    print(f"  gap {lo:2d}-{hi:2d}   " + "   ".join(f"{lab} n {r['n']:5,} {r['mean']:+7.2f} ± {r['se']:5.2f}" for lab, r in row.items()))
print("\nthe PRIOR trade's own 5-day return (the rung-1 unit that would be doubled), same-side priors in cell 2, by gap")
for lo, hi in ((1, 2), (3, 5), (6, 10), (11, 20)):
    m = prim & same & (g >= lo) & (g <= hi)
    kk = pk[m]; x = rb[kk]; f = np.isfinite(x) & c2[kk]
    print(f"  gap {lo:2d}-{hi:2d}   prior in cell 2 n {f.sum():5,}   prior's own return {1e4*x[f].mean():+8.2f} ± {1e4*x[f].std(ddof=1)/np.sqrt(max(f.sum(),2)):5.2f}   "
          f"share of priors that are rung 1: {100*F['r1'][kk].mean():.0f}%")
    out[f"prior gap {lo}-{hi}"] = dict(n=int(f.sum()), prior_return=float(1e4 * x[f].mean()))
print("\nrung 1 & cell 2 (7,974): return split by whether a same-side rung 2 follows within 5 sessions (A) -- i.e. the doubled vs the undoubled first touches")
K = np.flatnonzero(F["r1"] & c2); dbl = np.zeros(len(rb), bool); dbl[pk[F["add_A"]]] = True
for lab, m in (("doubled (a second zone follows in <=5)", dbl[K]), ("not doubled", ~dbl[K])):
    x = rb[K][m]; x = x[np.isfinite(x)]
    print(f"  {lab:42s} n {x.size:5,}  mean {1e4*x.mean():+8.2f} ± {1e4*x.std(ddof=1)/np.sqrt(x.size):5.2f}   median {1e4*np.median(x):+7.2f}   win {100*(x>0).mean():.1f}%")
    out[lab] = dict(n=int(x.size), mean=float(1e4 * x.mean()), median=float(1e4 * np.median(x)))
json.dump(out, open(REPO / "data" / "d426_gap_split.json", "w"), indent=1)
print("wrote data/d426_gap_split.json")
