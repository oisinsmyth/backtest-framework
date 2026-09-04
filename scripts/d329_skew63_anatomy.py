"""What are the names skew_63 ranks at its extremes? One jump day, or something
else -- and are they delisting-adjacent? Diagnostic only; nothing is scored.

The rolling max/min is taken on the (n, T) TRANSPOSE so the window axis is
contiguous. The first version reduced along a 12 KB stride over 414M elements
and did not finish in ten minutes.
"""
import sys, time, importlib.util
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

REPO = __import__("pathlib").Path(__file__).resolve().parents[1]
import os; os.chdir(REPO)
sys.path.insert(0, "src")
t0 = time.time()
spec = importlib.util.spec_from_file_location("p", "scripts/run_d327_rank_profile.py")
P = importlib.util.module_from_spec(spec); sys.modules["p"] = P; spec.loader.exec_module(P)
R, D, M = P.R, P.D, P.M
D.build_cache(verbose=False)
A = D.load_cache(mmap=True)
r1T, finT = np.asarray(A["r1T"]), np.asarray(A["finT"])
panel, _ = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
z = np.load(R.BC.CACHE, allow_pickle=False)
base = z["warm"] & panel.live
_, cnt, pos = R.ranked(z["skew_63"], base)
T, n = finT.shape
print(f"loaded ({time.time() - t0:.0f}s)", flush=True)

WIN = 63
lr = np.ascontiguousarray(np.log1p(np.nan_to_num(r1T, nan=0.0)).T)   # (n, T)
Wv = sliding_window_view(lr, WIN, axis=1)                            # (n, T-62, 63), inner axis contiguous
mx = np.full((n, T), np.nan); mn = np.full((n, T), np.nan)
mx[:, WIN - 1:] = Wv.max(axis=2); mn[:, WIN - 1:] = Wv.min(axis=2)
print(f"rolling extremes ({time.time() - t0:.0f}s)", flush=True)

alive60 = np.zeros((T, n), bool); alive60[:-60] = finT[60:]
rows = {"S0 (shorted)": [], "S1": [], "L0 (longed)": [], "universe": []}
rng = np.random.RandomState(20260904)
for t in range(200, T - 60):
    c = int(cnt[t])
    if c < 100:
        continue
    p = pos[t]; ok = (p < c) & finT[t]
    picks = {"S0 (shorted)": np.flatnonzero(ok & (p == c - 1)),
             "S1": np.flatnonzero(ok & (p == c - 2)),
             "L0 (longed)": np.flatnonzero(ok & (p == 0))}
    if not all(v.size for v in picks.values()):
        continue
    u = np.flatnonzero(ok)
    picks["universe"] = np.array([u[rng.randint(u.size)]])
    for k, idx in picks.items():
        i = int(idx[0])
        rows[k].append((mx[i, t], mn[i, t], z["skew_63"][i, t], alive60[t, i]))

print(f"\nWHAT THE EXTREME-RANK NAMES ARE  (medians over {len(rows['S0 (shorted)'])} bars)")
print("%-14s %13s %13s %9s %15s" % ("bucket", "max 63d day", "min 63d day", "skew_63", "still live +60"))
for k, v in rows.items():
    v = np.array(v, float)
    print("%-14s %+12.1f%% %+12.1f%% %9.2f %14.0f%%" % (
        k, 100 * np.expm1(np.nanmedian(v[:, 0])), 100 * np.expm1(np.nanmedian(v[:, 1])),
        np.nanmedian(v[:, 2]), 100 * np.nanmean(v[:, 3])))


def xs(a, b):
    out = []
    for t in range(200, T, 25):
        m = base[:, t] & np.isfinite(a[:, t]) & np.isfinite(b[:, t])
        if m.sum() < 100:
            continue
        ra = np.argsort(np.argsort(a[m, t])); rb = np.argsort(np.argsort(b[m, t]))
        out.append(np.corrcoef(ra, rb)[0, 1])
    return float(np.median(out))


print("\ncross-sectional Spearman with skew_63, median over bars:")
for k in ("max_ret_21", "rev_21", "rev_5", "rvol21", "cs_spread", "mom_252_21", "price_log"):
    print("  %-12s %+.2f" % (k, xs(z["skew_63"], z[k])))
print(f"\ndone ({time.time() - t0:.0f}s)")
