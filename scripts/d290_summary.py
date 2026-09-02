"""D290 stage-1 re-run -- the reporting view. Computes nothing, gates nothing.

    uv run python scripts/d290_summary.py [--top 15]

Reads `data/d290_stage1.json`. This is the file the decision record quotes.

WHAT EACH COLUMN IS, because the whole point of D290 is that these answer
different questions and D288 collapsed them into one:

  bp / t     the OBSERVED peak-evidence cell, in-sample. A max-order statistic
             over 5 N x 12 horizons, so its LEVEL is not readable -- it is here
             for magnitude, not for evidence.
  CV t       the honest one. Peak cell picked on half the NAMES, scored on the
             other half, over 10 re-randomised splits. The holdout is a disjoint
             NAME set, so this is its free in-sample proxy.
  rot/perm/tail   z against the three nulls. The PATTERN matters more than the
             minimum -- see the legend under each table.
  min z      the binding constraint, declared in advance so there is no shopping
             for the flattering null.

INTERESTING = ranks in the top decile on CV t AND min z > 0. Neither alone is
enough: CV without the nulls cannot separate a real effect from a nuisance tilt
that also generalises, and nulls without CV are measured on the sample that
picked the cell.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
D = json.loads((REPO / "data" / "d290_stage1.json").read_text())
AX = D["axes"]
R = D["results"]


def row(c, con):
    r = R[c]
    N, k, (bp, t, bars) = r["observed"][con]
    cv_m, cv_sd, _ = r["cv"][con]
    z = {n: r["z"][n][con] for n in ("rotation", "permutation", "tail")}
    return dict(c=c, ax=AX[c], N=N, k=k, bp=bp, t=t, cv=cv_m, cv_sd=cv_sd,
                zr=z["rotation"], zp=z["permutation"], zt=z["tail"],
                mn=min(z.values()), rt=round_trip(r, con), bars=bars)


def round_trip(r, con):
    """The cost bar for THIS construction, on the names it actually holds.

    Measured Corwin-Schultz per leg, not a fee assumption -- D285 guessed 15
    bp/side and the held names measured 33.81. The extremes are wider still,
    which is exactly why an N=3 book cannot be costed with an N=25 number.

      long   : one round trip on the long leg
      short  : one round trip on the short leg, PLUS BORROW, which this fixture
               cannot measure and which is therefore missing from the bar
      spread : both legs turn over
    """
    c = r.get("cost_bp_per_side") or {}
    lo, sh = c.get("long"), c.get("short")
    if con == "long":
        return 2 * lo if lo else None
    if con == "short":
        return 2 * sh if sh else None
    return (2 * lo + 2 * sh) if (lo and sh) else None


def table(con, top):
    rows = sorted((row(c, con) for c in R), key=lambda x: -x["cv"])
    cut = rows[max(int(len(rows) * 0.1), 1) - 1]["cv"]
    print(f"\n{'=' * 100}")
    print(f"  {con.upper()}-ONLY" if con != "spread" else "  SPREAD (dollar-neutral)")
    print(f"{'=' * 100}")
    print(f"  {'ax':2s} {'candidate':16s} {'N':>3s} {'k':>3s} {'bp':>9s} "
          f"{'t':>6s} | {'CV t':>7s} {'+/-':>5s} | {'rot':>6s} {'perm':>7s} "
          f"{'tail':>6s} {'min z':>6s} | {'cost':>6s} {'x bar':>6s}")
    for r in rows[:top]:
        flag = "  <== INTERESTING" if (r["cv"] >= cut and r["mn"] > 0) else ""
        print(f"  {r['ax']:2s} {r['c']:16s} {r['N']:3d} {r['k']:3d} "
              f"{r['bp']:+9.1f} {r['t']:+6.2f} | {r['cv']:+7.2f} "
              f"{r['cv_sd']:5.2f} | {r['zr']:+6.2f} {r['zp']:+7.2f} "
              f"{r['zt']:+6.2f} {r['mn']:+6.2f} | "
              + (f"{r['rt']:6.1f} {r['bp'] / r['rt']:+6.2f}" if r['rt'] else
                 f"{'--':>6s} {'--':>6s}") + flag)
    pos = [r for r in rows if r["mn"] > 0]
    print(f"  ... {len(rows) - top} more. min z > 0 on all three nulls: "
          f"{len(pos)} of {len(rows)}")
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=12)
    a = ap.parse_args()

    print(f"D290 STAGE-1 RE-RUN -- {D['n_candidates']} candidates, "
          f"{len(D['constructions'])} constructions, {D['draws']} null draws, "
          f"{D['splits']} name splits")
    print(f"  base {D['base_cells']:,} warm live cells | N {D['n_levels']} | "
          f"{D['elapsed_s'] / 60:.0f} min")

    # P1 -- the validity check. Everything below is unreadable if this fails.
    h = R["hist_L"]["observed"]["spread"]
    print(f"\n  P1 CALIBRATION  hist_L spread peak: N={h[0]} k={h[1]} "
          f"{h[2][0]:+.1f} bp, t {h[2][1]:+.3f}")
    print(f"     D286 measured t +2.86. Delta {abs(h[2][1] - 2.86):.3f}.")

    out = {con: table(con, a.top) for con in D["constructions"]}

    print(f"\n{'=' * 100}")
    print("  NULL-FAILURE PATTERN, on the SPREAD construction")
    print(f"{'=' * 100}")
    pat = {}
    for c in R:
        z = R[c]["z"]
        key = (z["rotation"]["spread"] > 0, z["permutation"]["spread"] > 0,
               z["tail"]["spread"] > 0)
        pat.setdefault(key, []).append(c)
    legend = {
        (True, True, True): "survives all three -- genuinely interesting",
        (True, False, True): "edge is WHEN it fires, not which names -> not cross-sectional",
        (True, True, False): "the edge IS the factor tilt (D283/D284)",
        (False, True, True): "a same-turnover rotated copy does as well",
    }
    for key in sorted(pat, key=lambda k: -sum(k)):
        r, p, t = key
        print(f"  rot {'+' if r else '-'}  perm {'+' if p else '-'}  "
              f"tail {'+' if t else '-'}   n={len(pat[key]):2d}   "
              f"{legend.get(key, '')}")
        print(f"      {', '.join(sorted(pat[key])[:10])}"
              + (" ..." if len(pat[key]) > 10 else ""))

    print(f"\n{'=' * 100}")
    print("  PREDICTIONS, as pre-registered")
    print(f"{'=' * 100}")
    # P2 -- does the name split shrink the top candidate by >= 40%?
    top_sp = max(R, key=lambda c: R[c]["observed"]["spread"][2][1])
    pt = R[top_sp]["observed"]["spread"][2][1]
    ct = R[top_sp]["cv"]["spread"][0]
    print(f"  P2 shrinkage: top-by-pooled-t on spread is {top_sp}, "
          f"pooled {pt:+.2f} -> CV {ct:+.2f} = {1 - ct / pt:.0%} shrink "
          f"({'CONFIRMED' if (1 - ct / pt) >= 0.40 else 'NOT CONFIRMED'}, bar 40%)")
    # P3 -- anything real on short-only?
    sh = [row(c, "short") for c in R]
    win = [r for r in sh if r["bp"] > 0 and r["mn"] > 0 and r["cv"] > 0]
    print(f"  P3 short-only: {len(win)} candidate(s) with POSITIVE bp, "
          f"min z > 0 and CV t > 0 "
          f"({'FALSIFIED' if win else 'CONFIRMED -- nothing works short-only'})")
    print(f"     BUT THE COST BAR DECIDES HOW TO READ THEM:")
    for r in sorted(win, key=lambda x: -x["cv"]):
        rt = r["rt"]
        verdict = ("CLEARS" if rt and r["bp"] > rt else
                   "below cost" if rt else "no cost")
        print(f"       {r['ax']} {r['c']:16s} N={r['N']:2d} k={r['k']:2d} "
              f"{r['bp']:+8.1f} bp  CV t {r['cv']:+5.2f}  min z {r['mn']:+6.2f}"
              + (f"  round trip {rt:5.1f} bp -> {r['bp'] / rt:+.2f}x  {verdict}"
                 if rt else "  no cost measured"))
    print("     Borrow is NOT in the short bar -- this fixture cannot measure "
          "it, so every")
    print("     short number above is optimistic by that amount.")
    # P4 -- risk terms beat rotation, fail tail
    print(f"  P4 risk terms (rotation + / tail -) on spread:")
    for c in ("ivol_21", "beta_63", "max_ret_21", "rvol21", "atr_norm"):
        z = R[c]["z"]
        print(f"       {c:14s} rot {z['rotation']['spread']:+6.2f}  "
              f"tail {z['tail']['spread']:+6.2f}  -> "
              f"{'TILT' if z['rotation']['spread'] > 0 >= z['tail']['spread'] else 'not the signature'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
