"""D373 -- is `mean > median > 0` a property of the EDGE, or of the trade SEGMENTATION?

    uv run python scripts/d373_segmentation_probe.py            writes data/d373_segmentation.json

POST-HOC DIAGNOSTIC. Not pre-registered. Written after H7 came back at +0.935 and must be labelled as post-hoc wherever it is quoted.

THE QUESTION. D365 (the retired momentum book) and D373 (the winners' dip) share 70.1% of their held name-bars, yet D365 fails the
chain (mean +334.85, median -141.37) and D373 passes it (+160.55, +51.55). The obvious confound is that D365 averages 99.4 bars per
trade and D373 averages 39.9: the per-trade median is a statistic of how exposure is CUT INTO TRADES, and the two books cut it
differently.

THE TEST. Re-cut D365's OWN stored per-bar hedged paths -- the identical exposure, nothing else changed -- into fixed-length segments,
and recompute the chain at each length. Nothing about the book changes; only the trade boundaries move.

THE ANSWER, and it is against the criterion: D365's exposure PASSES the chain at a 40-bar cut (+111.18 / +10.73) and FAILS it at its
native ~99-bar hold (+334.85 / -141.37). Compared at equal segmentation the two books AGREE -- both pass at 40, both fail at 100. The
contrast the criterion appeared to draw is hold length, not edge quality.

WHY IT IS MECHANICAL, not a quirk of this book: summing fat-tailed returns over a longer window raises the mean and lowers the median,
so a long-hold construction eventually fails the chain and a short-hold one eventually passes, edge or no edge.

WHAT IT DOES NOT BREAK. The WITHIN-STUDY null comparisons (D373's H1/H2/H3) hold segmentation FIXED on both sides -- every null draw is
scored through the same exit at the same cap -- so those remain fair. What is broken is CROSS-CONSTRUCTION comparison of a per-trade
median between books with different holding periods, which is what this record proposed to do.

This is CLAUDE.md section 10 biting where it says it will: path-invariant (per TRADE) and path-variant (per BAR) statistics are never
compared on the same footing, and a per-trade criterion inherits whatever the exit rule does to trade boundaries.
"""

from __future__ import annotations

import collections
import csv
import gzip
import json
import statistics as st
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PATHS = REPO / "data" / "d365_trade_paths_95_80.csv.gz"
OUT = REPO / "data" / "d373_segmentation.json"
CUTS = (5, 10, 20, 40, 60, 100)
# D373's own cap grid, from data/d373_stage0.json's horizon profile. Quoted, not recomputed, so this probe stays a pure re-cut of D365.
D373_GRID = {5: (39.11, 15.98, 8665), 10: (68.62, 36.64, 7290), 20: (122.36, 52.50, 5450), 40: (160.55, 51.55, 3932), 60: (235.73, 134.40, 3210)}


def chain(mean, median):
    """The hurdle as pre-registered in D373 section 5, at the principal's ruling: mean > median > 0."""
    return bool(mean > median > 0)


def load_paths():
    p = collections.defaultdict(list)
    with gzip.open(PATHS, "rt") as f:
        for r in csv.DictReader(f):
            p[r["trade_id"]].append((int(r["k"]), float(r["r_hedged_bp"])))
    for t in p:
        p[t].sort()
    # the stored paths must reproduce D365's published per-trade mean, or this probe is re-cutting the wrong object
    whole = [sum(x for _k, x in v) for v in p.values()]
    assert abs(st.mean(whole) - 334.85) < 0.05, f"[SEG] the stored paths give mean {st.mean(whole):+.2f}, not D365's +334.85"
    assert abs(st.median(whole) - (-141.37)) < 0.05, f"[SEG] the stored paths give median {st.median(whole):+.2f}, not D365's -141.37"
    return p


def recut(p, k):
    segs = []
    for v in p.values():
        rs = [x for _k, x in v]
        if k is None:
            segs.append(sum(rs))
        else:
            for i in range(0, len(rs), k):
                segs.append(sum(rs[i:i + k]))
    return segs


def main() -> int:
    p = load_paths()
    lens = [len(v) for v in p.values()]
    rows = []
    for k in (*CUTS, None):
        s = recut(p, k)
        m, md = st.mean(s), st.median(s)
        rows.append(dict(cut=k, n=len(s), mean_bp=m, median_bp=md, chain_passes=chain(m, md)))
    out = dict(study=373, kind="POST-HOC DIAGNOSTIC, not pre-registered",
               question="is `mean > median > 0` a property of the edge or of the trade segmentation?",
               source=str(PATHS.relative_to(REPO)),
               d365=dict(trades=len(p), name_bars=sum(lens), mean_hold_bars=sum(lens) / len(lens)),
               recut=rows,
               d373_own_grid=[dict(cap=k, mean_bp=v[0], median_bp=v[1], n=v[2], chain_passes=chain(v[0], v[1])) for k, v in D373_GRID.items()],
               finding=("D365's own exposure PASSES the chain at a 40-bar cut and FAILS at its native ~99-bar hold. At equal "
                        "segmentation the two books agree. The criterion is confounded with holding period and cannot compare "
                        "constructions that hold for different lengths."),
               scope=("Does NOT invalidate D373's within-study null comparisons, which hold segmentation fixed on both sides. Does "
                      "invalidate cross-construction comparison of a per-trade median."))
    OUT.write_text(json.dumps(out, indent=2))          # persist before rendering
    print(f"wrote {OUT}")
    print(f"\nD365: {len(p):,} trades, {sum(lens):,} name-bars, mean hold {sum(lens) / len(lens):.1f} bars")
    print(f"\n  {'cut':>7} {'n':>8} {'mean':>10} {'median':>10}   chain")
    for r in rows:
        print(f"  {str(r['cut'] or 'whole'):>7} {r['n']:>8,} {r['mean_bp']:>+10.2f} {r['median_bp']:>+10.2f}   {'PASS' if r['chain_passes'] else 'FAIL'}")
    print(f"\n  {out['finding']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
