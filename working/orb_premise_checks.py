"""THE TWO PREMISE CHECKS for the inventory-transfer story of the opening range.

THE STORY. Overnight a contract trades in a thin book, so whoever absorbs flow accumulates inventory
they did not choose. The open is the first moment liquidity exists in size, so the first stretch of
the session is fourteen hours of risk being transferred. A break of the opening range is then not
momentum -- it is the standing book on that side being EXHAUSTED.

IT MAKES TWO CHECKABLE CLAIMS, and D531 already failed in the way it predicts, because D531 held to
the session close and inventory clearing is over long before that.

  CHECK 1  SIZE.  Conditional on a range exit, is E|move| over the next 60-120 minutes large against
                  the round trip -- and LARGER than an unconditional move of the same length? If the
                  exit does not select a moment of elevated movement, the story is untradeable even
                  if true. That is how ZN died.

  CHECK 2  SHAPE. Does the push DECAY? Hit rate at 15 / 30 / 60 / 120 minutes and to the close. The
                  story predicts a HUMP -- best at 60-120, deteriorating to the close, because
                  D487 measured the first half-hour reversing into the last at -4.3 SE. If the
                  profile is FLAT, the mechanism is not inventory clearing and the story is wrong.

NO P&L is claimed, no position is taken, nothing is admitted (R15). Reported in hit rate, per D529.
In sample 2016-01-04..2023-12-29; the 2024+ slice is NOT read.

    python working/orb_premise_checks.py
"""
from __future__ import annotations
import importlib.util
import sys
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

spec = importlib.util.spec_from_file_location("d531", REPO / "scripts" / "run_d531_orb_session_native.py")
D531 = importlib.util.module_from_spec(spec); sys.modules["d531"] = spec.loader and spec.loader.exec_module(D531) or D531  # noqa: E501

OR_N = 6                                   # 30 minutes, D531's primary
HORIZONS = [3, 6, 12, 24]                  # 15, 30, 60, 120 minutes
CAND = ["CL", "GC", "SI", "NG"]
CALIB = ["ES", "NQ"]
# round trip = $3 commission + the MEASURED median spread of that root's micro (working/stage0_micro_spread.py)
COST = {"CL": 3.0 + 1 * 1.00, "GC": 3.0 + 2 * 1.00, "SI": 3.0 + 1 * 5.00, "NG": 3.0 + 2 * 1.00,
        "ES": 3.0 + 1 * 1.25, "NQ": 4.21}


def main():
    sp = D531.specs()
    G = D531.load()
    print("THE INVENTORY-TRANSFER STORY -- two premise checks. No P&L, nothing admitted.\n")

    print("CHECK 1 -- SIZE. E|move| after a range exit vs an unconditional move of the same length.")
    print(f"  {'root':<5}{'cost $':>8}{'H':>5}{'n':>7}{'E|mv| cond $':>14}{'uncond $':>11}"
          f"{'ratio':>8}{'x cost':>9}")
    rows = []
    store = {}
    for r in CAND + CALIB:
        g = G[G.root == r]
        if not len(g):
            continue
        first, last = D531.session_span(g)
        days, A = D531.grids(g)
        d, e, x, ovol, both = D531.breakouts(A["high"], A["low"], A["open"], A["close"], A["volume"],
                                             first, last, OR_N)
        point = sp[r]["usd_per_point"]
        store[r] = (d, e, A, first, last, point)
        # the entry BAR index per session, re-derived so the horizon can be applied from it
        ent_bar = np.full(len(d), -1)
        for s in range(len(d)):
            if d[s] == 0:
                continue
            for b in range(first + OR_N, last):
                if A["high"][s, b] > np.nanmax(A["high"][s, first:first + OR_N]) or \
                   A["low"][s, b] < np.nanmin(A["low"][s, first:first + OR_N]):
                    ent_bar[s] = b + 1
                    break
        store[r] = store[r] + (ent_bar,)
        for H in HORIZONS:
            cond, unc = [], []
            for s in range(len(d)):
                if d[s] == 0 or ent_bar[s] < 0 or ent_bar[s] + H > last:
                    continue
                p0 = A["open"][s, ent_bar[s]]; p1 = A["close"][s, ent_bar[s] + H]
                if np.isfinite(p0) and np.isfinite(p1):
                    cond.append(abs(p1 - p0) * point)
            for s in range(len(d)):                       # unconditional: every valid start bar
                for b in range(first, last - H):
                    p0 = A["open"][s, b]; p1 = A["close"][s, b + H]
                    if np.isfinite(p0) and np.isfinite(p1):
                        unc.append(abs(p1 - p0) * point)
                if s > 400:                               # 400 sessions is ample for a mean
                    break
            if len(cond) < 50:
                continue
            c, u = float(np.mean(cond)), float(np.mean(unc))
            rows.append(dict(root=r, H=H, n=len(cond), cond=c, unc=u, ratio=c / u, xcost=c / COST[r]))
            print(f"  {r:<5}{COST[r]:>8.2f}{5*H:>5}{len(cond):>7,}{c:>14.2f}{u:>11.2f}"
                  f"{c/u:>8.2f}{c/COST[r]:>9.1f}")

    print("\nCHECK 2 -- SHAPE. Hit rate by exit horizon. The story predicts a HUMP, best at 60-120 min,")
    print("           deteriorating to the close. FLAT means the mechanism is not inventory clearing.")
    print(f"  {'root':<5}" + "".join(f"{str(5*h)+'m':>9}" for h in HORIZONS) + f"{'close':>9}{'shape':>10}")
    shp = []
    for r in CAND + CALIB:
        if r not in store:
            continue
        d, e, A, first, last, point, ent_bar = store[r]
        hits = []
        for H in HORIZONS + ["close"]:
            ok = 0; n = 0
            for s in range(len(d)):
                if d[s] == 0 or ent_bar[s] < 0:
                    continue
                b1 = last if H == "close" else ent_bar[s] + H
                if b1 > last:
                    continue
                p0 = A["open"][s, ent_bar[s]]; p1 = A["close"][s, b1]
                if not (np.isfinite(p0) and np.isfinite(p1)):
                    continue
                n += 1; ok += int(np.sign(p1 - p0) == d[s])
            hits.append(ok / n if n else np.nan)
        peak = int(np.nanargmax(hits[:len(HORIZONS)]))
        hump = bool(hits[peak] > hits[-1] + 0.005 and hits[peak] > hits[0] + 0.005)
        shp.append(dict(root=r, hits=hits, peak_min=5 * HORIZONS[peak], hump=hump))
        print(f"  {r:<5}" + "".join(f"{100*h:>8.2f}%" for h in hits)
              + f"{('HUMP@' + str(5*HORIZONS[peak]) + 'm') if hump else 'flat/none':>10}")

    print("\n" + "=" * 78)
    D = pd.DataFrame(rows)
    cands = D[D.root.isin(CAND)]
    print(f"  CHECK 1: on the candidate roots the conditional move is "
          f"{cands.groupby('H')['ratio'].mean().min():.2f}-{cands.groupby('H')['ratio'].mean().max():.2f}x "
          f"the unconditional one")
    best = cands[cands.H == 12]
    print(f"           at 60 min it is {best['xcost'].min():.1f}-{best['xcost'].max():.1f}x the round trip "
          f"(the arm's gross is 3.2x its cost)")
    n_hump = sum(1 for s in shp if s["hump"] and s["root"] in CAND)
    print(f"  CHECK 2: {n_hump} of {len(CAND)} candidate roots show the predicted hump")
    print("=" * 78)
    D.to_csv(REPO / "working" / "orb_premise_size.csv", index=False)
    pd.DataFrame([{**{'root': s['root'], 'peak_min': s['peak_min'], 'hump': s['hump']},
                   **{f'h{5*h}': s['hits'][i] for i, h in enumerate(HORIZONS)},
                   'close': s['hits'][-1]} for s in shp]).to_csv(
        REPO / "working" / "orb_premise_shape.csv", index=False)


if __name__ == "__main__":
    main()
