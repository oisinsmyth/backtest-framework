"""THE LEVEL-RANDOMISED NULL -- the control D255 registered and did not build.

R7's null keeps the base book and cuts the same NUMBER of trades at RANDOM POINTS.
That asks: is this level informative about WHICH trades to cut and WHERE?

It does not ask the question a level SWEEP needs: IS THIS LEVEL SPECIAL AMONG
LEVELS? For that the null must apply the overlay CONSISTENTLY at a level drawn at
random, which is the principal's point.

Also fixes D255's best-of-N floor, which was computed across three arms with
different baselines and therefore judged S1's cells against C's null distribution.
Recomputed WITHIN each arm.
"""
import importlib.util, math, sys, time
from pathlib import Path
import numpy as np

REPO = Path(r"C:/Users/O/Desktop/Projects/Backtest Framework")
sys.path.insert(0, str(REPO / "src"))
sp = importlib.util.spec_from_file_location("d255", REPO / "scripts" / "run_stops_book.py")
m = importlib.util.module_from_spec(sp); sys.modules["d255"] = m; sp.loader.exec_module(m)
X, E = m.X, m.E

panel, start, books, ones = E.books_on(*E.FIXTURES["extended"])
closes = panel.closes
base = {k: X.score(panel, v, start)["excess_sharpe"] for k, v in books.items()}
N = 600
LO, HI = 0.02, 0.50          # the plausible level range, log-uniform


def score(pos):
    total = X.signed_log_returns(panel, pos, total_return=True)[start:]
    ex = X.excess_of(total, pos, start)
    sd = float(np.std(ex, ddof=1))
    return ((float(np.mean(ex)) / sd * math.sqrt(X.PPY)) if sd > 0 else 0.0,
            X.L.total_return_of(total))


print("LEVEL-RANDOMISED NULL -- the overlay applied CONSISTENTLY at a level drawn")
print(f"log-uniform on [{LO:.0%}, {HI:.0%}], {N} draws per (arm, type)\n")
rng = np.random.default_rng(0)
dists = {}
for arm in m.ARMS:
    for kind in ("TP", "SL"):
        sh = np.empty(N)
        t0 = time.time()
        lv = np.exp(rng.uniform(math.log(LO), math.log(HI), size=N))
        for j, level in enumerate(lv):
            pos, _ = m.apply_overlay(books[arm], closes, start,
                                     tp=float(level) if kind == "TP" else None,
                                     sl=None if kind == "TP" else float(level))
            sh[j] = score(pos)[0]
        dists[(arm, kind)] = sh
        print(f"  {arm}:{kind}  {N} levels in {time.time()-t0:4.0f}s   "
              f"median {np.median(sh):+.3f}  p95 {np.percentile(sh,95):+.3f}  "
              f"max {sh.max():+.3f}   (base {base[arm]:+.3f})")

print("\nWHERE EACH REGISTERED LEVEL LANDS AMONG RANDOM LEVELS")
print(f"  {'cell':14} {'excess Sharpe':>14} {'vs base':>9} {'pct among random levels':>26}")
print("  " + "-" * 66)
rows = []
for arm in m.ARMS:
    for name, tp, sl in m.LEVELS:
        kind = "TP" if tp is not None and sl is None else ("SL" if sl is not None and tp is None else None)
        pos, cuts = m.apply_overlay(books[arm], closes, start, tp=tp, sl=sl)
        s, _ = score(pos)
        if kind is None:
            print(f"  {arm+':'+name:14} {s:+13.3f} {s-base[arm]:+8.3f}   "
                  f"{'(combined -- no single-level null)':>26}")
            continue
        d = dists[(arm, kind)]
        pct = float((d < s).mean() * 100.0)
        rows.append((arm, name, s, pct, len(cuts)))
        flag = "  <-- special" if pct >= 95.0 else ""
        print(f"  {arm+':'+name:14} {s:+13.3f} {s-base[arm]:+8.3f}   {pct:24.1f}th{flag}")

print("\nCORRECTED BEST-OF-N FLOOR, computed WITHIN each arm (D255's was across arms)")
for arm in m.ARMS:
    d = np.maximum(dists[(arm, "TP")], dists[(arm, "SL")])
    print(f"  {arm}: within-arm best-of-2 p95 = {np.percentile(d,95):+.3f}   "
          f"base {base[arm]:+.3f}   "
          f"best registered cell {max(r[2] for r in rows if r[0]==arm):+.3f}")

print("\nDOES ANY OVERLAY LEVEL BEAT THE BASE AT ALL?")
for arm in m.ARMS:
    for kind in ("TP", "SL"):
        d = dists[(arm, kind)]
        print(f"  {arm}:{kind}  levels beating base: {np.mean(d > base[arm]):6.1%}   "
              f"best level's edge {d.max()-base[arm]:+.3f}")
