"""Stage-0 for D332: how often is the per-bar Corwin-Schultz estimate clamped to
ZERO, by price bucket, and what would a half-tick floor add? Measures the
conditioner only; touches no book."""
import sys, time, importlib.util
import numpy as np
REPO = __import__("pathlib").Path(__file__).resolve().parents[1]
import os; os.chdir(REPO)
sys.path.insert(0, "src")
t0 = time.time()
spec = importlib.util.spec_from_file_location("p", "scripts/run_d327_rank_profile.py")
P = importlib.util.module_from_spec(spec); sys.modules["p"] = P; spec.loader.exec_module(P)
M, SP = P.M, P.SP
panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
g = M.P1.build_grids(panel, cleaned)
half = SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4     # (n, T) bp per side
px = g["close"]
fin = np.isfinite(half) & np.isfinite(px) & (px > 0)
print(f"loaded ({time.time() - t0:.0f}s); {int(fin.sum()):,} finite name-bars")

tick = np.where(px >= 1.0, 0.01, 0.0001)
floor = 0.5 * tick / px * 1e4                                             # half a tick, bp
h, p, f = half[fin], px[fin], floor[fin]
zero = h == 0.0
print(f"\nCS half-spread estimate EXACTLY ZERO on {100 * zero.mean():.1f}% of live name-bars; "
      f"median where nonzero {np.median(h[~zero]):.1f} bp; overall median {np.median(h):.1f} bp")
print("\nby price bucket:  share of bars | zero-clamped | median CS (all) | median CS (nonzero) | half-tick floor | bars where floor > CS")
edges = [0, 1, 2, 5, 10, 20, 50, 100, 1e9]
for lo, hi in zip(edges[:-1], edges[1:]):
    m = (p >= lo) & (p < hi)
    if m.sum() < 1000:
        continue
    print("  $%-4g-%-6g %6.1f%% | %10.1f%% | %8.1f bp | %8.1f bp | %8.2f bp | %10.1f%%"
          % (lo, hi if hi < 1e8 else np.inf, 100 * m.mean(), 100 * zero[m].mean(),
             np.median(h[m]), np.median(h[m & ~zero]) if (m & ~zero).any() else np.nan,
             np.median(f[m]), 100 * (f[m] > h[m]).mean()))
print("\nthe run of zeros: for a name-bar clamped to zero, is the NEXT bar also zero?")
z2 = (half[:, :-1] == 0.0) & fin[:, :-1] & fin[:, 1:]
print("  P(next also zero | zero) = %.2f   vs unconditional P(zero) = %.2f"
      % ((half[:, 1:][z2] == 0.0).mean(), zero.mean()))
print(f"\ndone ({time.time() - t0:.0f}s)")
