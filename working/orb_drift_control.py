"""Is the up/down break asymmetry a SIGNAL, or is it just the market's drift?

THE CHALLENGE (the principal). ES hit 55.08% on upside breaks and 45.81% on downside ones. But if the
index drifts up, ANY long wins more than half the time and ANY short loses more than half -- so the
asymmetry could be drift with zero information in the break. My comparison was against 50%, which is
the wrong reference.

THE RIGHT CONTROL: hold the CLOCK POSITION fixed and rotate the SESSION. For every break at bar b on
session s, draw the move from bar b on a DIFFERENT session. That absorbs the drift AND the
time-of-day profile exactly, and leaves only "did the break add anything".

    observed   P(move agrees with break direction | break at bar b, session s)
    null       P(move agrees with the SAME direction | bar b, a different session)

Reported separately for UP and DOWN breaks, because pooling them is what hid the effect last time.
Ties are excluded, not scored as misses -- the earlier diagnostic showed that shifted the short
horizons by up to 2 points.

NO P&L, nothing admitted (R15). In sample; the 2024+ slice is not read.

    python working/orb_drift_control.py
"""
from __future__ import annotations
import importlib.util
import sys
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
spec = importlib.util.spec_from_file_location("d531c", REPO / "scripts" / "run_d531_orb_session_native.py")
D531 = importlib.util.module_from_spec(spec)
sys.modules["d531c"] = D531
spec.loader.exec_module(D531)

OR_N = 6
HORIZONS = [3, 6, 12, 24]
ROOTS = ["ES", "NQ", "CL", "GC", "SI", "NG"]
N_DRAWS = 1000
SEED = 20260915


def main():
    rng = np.random.default_rng(SEED)
    G = D531.load()
    print("DOES THE BREAK BEAT THE BASE RATE AT THAT MOMENT? clock held fixed, session rotated\n")
    print(f"  {'root':<5}{'side':<6}{'H':>5}{'n':>7}{'observed':>10}{'base p50':>10}{'base p95':>10}"
          f"{'lift':>8}{'share>=':>9}  verdict")
    rows = []
    for r in ROOTS:
        g = G[G.root == r]
        if not len(g):
            continue
        first, last = D531.session_span(g)
        days, A = D531.grids(g)
        d, _, _, _, _ = D531.breakouts(A["high"], A["low"], A["open"], A["close"], A["volume"],
                                       first, last, OR_N)
        ent = np.full(len(d), -1)
        for s in range(len(d)):
            if d[s] == 0:
                continue
            oh = np.nanmax(A["high"][s, first:first + OR_N]); ol = np.nanmin(A["low"][s, first:first + OR_N])
            for b in range(first + OR_N, last):
                if A["high"][s, b] > oh or A["low"][s, b] < ol:
                    ent[s] = b + 1
                    break
        O, C = A["open"], A["close"]
        ns = O.shape[0]
        for H in HORIZONS:
            ev = [(s, ent[s], d[s]) for s in range(ns)
                  if d[s] != 0 and ent[s] >= 0 and ent[s] + H <= last]
            for side, want in (("up", 1.0), ("down", -1.0)):
                E = [(s, b) for (s, b, dd) in ev if dd == want]
                if len(E) < 100:
                    continue
                mv = np.array([C[s, b + H] - O[s, b] for (s, b) in E])
                nz = mv != 0
                obs = float((np.sign(mv[nz]) == want).mean())
                # NULL: same bar b, a DIFFERENT session. Absorbs drift and time-of-day exactly.
                draws = np.empty(N_DRAWS)
                bars = np.array([b for (_, b) in E])
                for i in range(N_DRAWS):
                    alt = rng.integers(0, ns, size=len(E))
                    m2 = np.array([C[a, b + H] - O[a, b] for a, b in zip(alt, bars)])
                    ok = np.isfinite(m2) & (m2 != 0)
                    draws[i] = (np.sign(m2[ok]) == want).mean() if ok.sum() > 50 else np.nan
                p50 = float(np.nanmedian(draws)); p95 = float(np.nanquantile(draws, 0.95))
                share = float(np.nanmean(draws >= obs))
                v = "CLEARS" if obs > p95 else "inside"
                rows.append(dict(root=r, side=side, H=5 * H, n=int(nz.sum()), obs=obs,
                                 base_p50=p50, base_p95=p95, lift=obs - p50, share_ge=share, clears=obs > p95))
                print(f"  {r:<5}{side:<6}{5*H:>5}{int(nz.sum()):>7,}{100*obs:>9.2f}%{100*p50:>9.2f}%"
                      f"{100*p95:>9.2f}%{100*(obs-p50):>+8.2f}{100*share:>8.1f}%  {v}")
    D = pd.DataFrame(rows)
    print("\n" + "=" * 100)
    print(f"  THE DRIFT, measured: the base rate for an UP move averages "
          f"{100*D[D.side=='up'].base_p50.mean():.2f}% and for a DOWN move "
          f"{100*D[D.side=='down'].base_p50.mean():.2f}%")
    print(f"  so a naive 50% reference overstates an up-break by "
          f"{100*(D[D.side=='up'].base_p50.mean()-0.5):+.2f} points and a down-break by "
          f"{100*(D[D.side=='down'].base_p50.mean()-0.5):+.2f}")
    print(f"  LIFT over the base rate: mean {100*D.lift.mean():+.2f} points; "
          f"cells clearing their own p95: {int(D.clears.sum())} of {len(D)}")
    for side, x in D.groupby("side"):
        print(f"    {side:<5} mean lift {100*x.lift.mean():+.2f} points, clears {int(x.clears.sum())} of {len(x)}")
    print("=" * 100)
    D.to_csv(REPO / "working" / "orb_drift_control.csv", index=False)


if __name__ == "__main__":
    main()
