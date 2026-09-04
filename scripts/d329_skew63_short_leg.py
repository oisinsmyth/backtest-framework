"""skew_63's SHORT leg, trade by trade: the P&L distribution (reporting rule 2),
and whether the names that die within 60 bars are PINNED (a deal price: tiny
daily range, ~0 return to death) or COLLAPSING (large range, large negative
return). The event file has no delisting reasons, so the tape has to say.

Every npz array is loaded ONCE. The previous diagnostic re-read `z["skew_63"]`
from the archive on every loop iteration and took ten minutes doing it.
"""
import sys, time, importlib.util
import numpy as np

REPO = __import__("pathlib").Path(__file__).resolve().parents[1]
import os; os.chdir(REPO)
sys.path.insert(0, "src")
t0 = time.time()


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, f"scripts/{filename}")
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m)
    return m


V6 = _load("d326", "run_d326_both_lenses.py")
Y, W, D, M, SP, R = V6.Y, V6.W, V6.D, V6.M, V6.SP, V6.R
D.build_cache(verbose=False)
A = D.load_cache(mmap=True)
r1T, finT = np.asarray(A["r1T"]), np.asarray(A["finT"])
panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
g = M.P1.build_grids(panel, cleaned)
HALF = np.ascontiguousarray((SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
RANGE = np.ascontiguousarray(((g["high"] - g["low"]) / g["close"]).T)      # (T, n)
z = np.load(R.BC.CACHE, allow_pickle=False)
base = z["warm"] & panel.live
n, T = panel.live.shape
rk = Y.rank_single(z, base, "skew_63", n, T)
print(f"loaded ({time.time() - t0:.0f}s)", flush=True)

K = 20
inv, res = V6.invariant(A, rk, finT, K, HALF)
tr = [t for t in res["trades"] if t[4] == 1]                 # the SHORT leg
pnl = np.array([t[3] for t in tr]) * 1e4
two_c = 2.0 * float(np.nanmedian([HALF[t[1], t[0]] for t in tr]))
print(f"\nskew_63 SHORT leg, invariant, k={K}: {len(tr)} trades, 2c = {two_c:.1f} bp")

# --- reporting rule 2: the distribution, and trim BOTH tails ---------------
s = np.sort(pnl); m = len(s); c1 = max(1, m // 100)
print("  mean %+7.1f  median %+7.1f  win %.0f%%  skew %+.2f  kurt %+.1f" % (
    pnl.mean(), np.median(pnl), 100 * (pnl > 0).mean(),
    ((pnl - pnl.mean()) ** 3).mean() / pnl.std() ** 3,
    ((pnl - pnl.mean()) ** 4).mean() / pnl.std() ** 4 - 3))
print("  ex-top-1%% %+7.1f   ex-bottom-1%% %+7.1f   trimmed-both %+7.1f" % (
    s[:-c1].mean(), s[c1:].mean(), s[c1:-c1].mean()))
tot = pnl.sum()
print("  top 1%% of trades = %.0f%% of P&L; top 5%% = %.0f%%; bottom 1%% = %.0f%%" % (
    100 * s[-c1:].sum() / tot, 100 * s[-5 * c1:].sum() / tot, 100 * s[:c1].sum() / tot))

# --- the names that DIE: pinned or collapsing? ------------------------------
last_live = np.full(n, -1)
for i in range(n):
    w = np.flatnonzero(finT[:, i])
    if w.size:
        last_live[i] = w[-1]
rows = []
for row, e0, age, p, _s in tr:
    ll = last_live[row]
    dies = (ll - e0) <= 60 and ll < T - 1
    v = r1T[e0:ll + 1, row]
    to_death = float(np.expm1(np.log1p(np.nan_to_num(v, nan=0.0)).sum())) if dies else np.nan
    rng = float(np.nanmedian(RANGE[e0:e0 + age, row]))
    rows.append((p * 1e4, dies, to_death, rng, HALF[e0, row], ll - e0))
rows = np.array(rows, float)
dies = rows[:, 1] > 0
print(f"\n  trades whose name is DEAD within 60 bars of entry: {dies.sum()} of {len(rows)} "
      f"({100 * dies.mean():.0f}%)")
for lbl, msk in (("dies within 60", dies), ("survives", ~dies)):
    r = rows[msk]
    print("  %-15s n=%4d  P&L/trade %+7.1f  median daily range %.2f%%  half-spread %5.1f bp  "
          "bars to death %s" % (
              lbl, len(r), r[:, 0].mean(), 100 * np.nanmedian(r[:, 3]),
              np.nanmedian(r[:, 4]),
              ("%.0f (median)" % np.median(r[:, 5])) if lbl.startswith("dies") else "-"))
d = rows[dies]
td = d[:, 2]
print("\n  for the dying names, return from entry to the last live bar:")
print("    median %+.1f%%   p25 %+.1f%%   p75 %+.1f%%" % tuple(100 * np.nanpercentile(td, [50, 25, 75])))
pinned = np.abs(td) < 0.05
print("    |return| < 5%% (PINNED, deal-like): %d of %d (%.0f%%)  -- their short-leg P&L/trade %+.1f, "
      "daily range %.2f%%" % (pinned.sum(), len(td), 100 * pinned.mean(),
                              d[pinned, 0].mean() if pinned.any() else np.nan,
                              100 * np.nanmedian(d[pinned, 3]) if pinned.any() else np.nan))
coll = td < -0.30
print("    return < -30%% (COLLAPSE):           %d of %d (%.0f%%)  -- their short-leg P&L/trade %+.1f, "
      "daily range %.2f%%" % (coll.sum(), len(td), 100 * coll.mean(),
                              d[coll, 0].mean() if coll.any() else np.nan,
                              100 * np.nanmedian(d[coll, 3]) if coll.any() else np.nan))
print(f"\ndone ({time.time() - t0:.0f}s)")
