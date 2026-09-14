"""Is CHECK 2's hit rate measuring what I said it measures? The principal challenged it.

TWO SUSPECTS.

  (A) TIES. The hit test is sign(p1-p0) == d, and sign(0) == 0, which never equals +/-1. So a move
      that ends EXACTLY unchanged is scored a MISS. Ties are commonest at the shortest horizon --
      which is precisely the shape reported (worst at 15 min, improving monotonically to the close).
      If the tie rate is material this artefact alone could produce the whole result.

  (B) POOLING. Up-breaks and down-breaks are pooled. If one side continues and the other reverts,
      the pooled hit rate hides both. ("A universe average hides sign flips.")

This prints the tie rate by horizon, the hit rate EXCLUDING ties, and the hit rate split by break
direction. No P&L, nothing admitted.

    python working/orb_check2_diagnostics.py
"""
from __future__ import annotations
import importlib.util
import sys
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
spec = importlib.util.spec_from_file_location("d531b", REPO / "scripts" / "run_d531_orb_session_native.py")
D531 = importlib.util.module_from_spec(spec)
sys.modules["d531b"] = D531
spec.loader.exec_module(D531)

OR_N = 6
HORIZONS = [3, 6, 12, 24]
ROOTS = ["CL", "GC", "SI", "NG", "ES", "NQ"]


def main():
    G = D531.load()
    print("CHECK 2 DIAGNOSTICS -- ties, and the up/down split\n")
    print(f"  {'root':<5}{'H':>5}{'n':>7}{'ties':>7}{'tie %':>8}{'hit (ties=miss)':>17}"
          f"{'hit (ex ties)':>15}{'hit UP':>9}{'n up':>7}{'hit DN':>9}{'n dn':>7}")
    rows = []
    for r in ROOTS:
        g = G[G.root == r]
        if not len(g):
            continue
        first, last = D531.session_span(g)
        days, A = D531.grids(g)
        d, e, x, ovol, both = D531.breakouts(A["high"], A["low"], A["open"], A["close"],
                                             A["volume"], first, last, OR_N)
        ent = np.full(len(d), -1)
        for s in range(len(d)):
            if d[s] == 0:
                continue
            oh = np.nanmax(A["high"][s, first:first + OR_N]); ol = np.nanmin(A["low"][s, first:first + OR_N])
            for b in range(first + OR_N, last):
                if A["high"][s, b] > oh or A["low"][s, b] < ol:
                    ent[s] = b + 1
                    break
        for H in HORIZONS:
            mv, dd = [], []
            for s in range(len(d)):
                if d[s] == 0 or ent[s] < 0 or ent[s] + H > last:
                    continue
                p0 = A["open"][s, ent[s]]; p1 = A["close"][s, ent[s] + H]
                if np.isfinite(p0) and np.isfinite(p1):
                    mv.append(p1 - p0); dd.append(d[s])
            mv = np.asarray(mv); dd = np.asarray(dd)
            if len(mv) < 50:
                continue
            ties = int((mv == 0).sum())
            hit_incl = float((np.sign(mv) == dd).mean())
            nz = mv != 0
            hit_excl = float((np.sign(mv[nz]) == dd[nz]).mean())
            up = dd > 0; dn = dd < 0
            h_up = float((np.sign(mv[up & nz]) == dd[up & nz]).mean()) if (up & nz).sum() > 30 else np.nan
            h_dn = float((np.sign(mv[dn & nz]) == dd[dn & nz]).mean()) if (dn & nz).sum() > 30 else np.nan
            rows.append(dict(root=r, H=5 * H, n=len(mv), ties=ties, tie_pct=100 * ties / len(mv),
                             hit_incl=hit_incl, hit_excl=hit_excl, hit_up=h_up, hit_dn=h_dn,
                             n_up=int((up & nz).sum()), n_dn=int((dn & nz).sum())))
            print(f"  {r:<5}{5*H:>5}{len(mv):>7,}{ties:>7,}{100*ties/len(mv):>7.2f}%"
                  f"{100*hit_incl:>16.2f}%{100*hit_excl:>14.2f}%{100*h_up:>8.2f}%{int((up&nz).sum()):>7,}"
                  f"{100*h_dn:>8.2f}%{int((dn&nz).sum()):>7,}")
    D = pd.DataFrame(rows)
    print("\n" + "=" * 96)
    print(f"  TIES: max tie rate {D.tie_pct.max():.2f}% (on {D.loc[D.tie_pct.idxmax(),'root']} at "
          f"{int(D.loc[D.tie_pct.idxmax(),'H'])}m); mean shift from excluding them "
          f"{100*(D.hit_excl - D.hit_incl).mean():+.2f} points")
    spl = (D.hit_up - D.hit_dn).abs()
    print(f"  UP vs DOWN: mean |difference| {100*spl.mean():.2f} points, max {100*spl.max():.2f} "
          f"(on {D.loc[spl.idxmax(),'root']} at {int(D.loc[spl.idxmax(),'H'])}m)")
    print(f"  cells where UP and DOWN fall on OPPOSITE sides of 50%: "
          f"{int(((D.hit_up-0.5)*(D.hit_dn-0.5) < 0).sum())} of {len(D)}")
    print("=" * 96)
    D.to_csv(REPO / "working" / "orb_check2_diagnostics.csv", index=False)


if __name__ == "__main__":
    main()
