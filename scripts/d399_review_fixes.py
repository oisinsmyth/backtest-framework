"""D399 -- EVERY NUMBER SINCE THE WALK WENT IN, RE-RUN ON THE FIXED CODE, and each review
suspicion measured as a switch.

    uv run python scripts/d399_review_fixes.py            all variants, writes the record + charts

The independent review (scratchpad review.md, 2026-09-10) found three logic defects in
`recalc_pair` -- D1 the fit's points not in bar order, D2 the walk resurrecting provisional pivots,
D3 a body close untested on bars whose candidate fit was nan -- and six suspicions. The decay
sweep, the extend-back comparison and the envelope comparison were all produced by the defective
code. This script runs the twelve drawn names through the fixed construction:

  * the three published cells (frozen, extend-back, envelope), for BEFORE/AFTER counts against
    the numbers the reviewer reproduced from the defective code;
  * one variant per suspicion switch, everything else at the chosen cell:
        S1  height_mode  raw (default) vs anchored
        S2  back_tol     = dh (default) vs 5% vs 10%
        S3  walk_chain   body_only (default) vs native_only vs unbounded;
            max_reach    130 (default) vs 65 vs 260 vs off
        S4  syn_ttl      on (default) vs off (the principal's original "keep until superseded")

Window counts throughout (D4). Writes data/d399_review_fixes.json and the chart JSONs the pages
read: temp/d399_new_sample_chart.json (the chosen cell), temp/d399_envelope_chart.json,
temp/d399_review_variants_chart.json (one chart set per variant, for inspection).
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

OUT = REPO / "data" / "d399_review_fixes.json"
CHART = REPO / "temp" / "d399_new_sample_chart.json"
CHART_ENV = REPO / "temp" / "d399_envelope_chart.json"
CHART_VAR = REPO / "temp" / "d399_review_variants_chart.json"

# WHAT THE REVIEWER REPRODUCED FROM THE DEFECTIVE CODE (review.md section 4), per name in draw
# order: BA 3017, BA 3783, BRO, COST, CPRT, CRMT, HUBB, MKTX, MZTI, PFS, PHLT, SNPS.
BEFORE = dict(
    frozen=[13, 16, 8, 8, 12, 24, 11, 18, 18, 9, 25, 19],
    extend=[10, 10, 6, 7, 11, 19, 10, 18, 13, 17, 20, 8],
    envelope=[14, 7, 12, 2, 8, 12, 17, 10, 8, 12, 16, 4],
    reach=dict(frozen=dict(med=16, p90=29, max=206), extend=dict(med=28, p90=114, max=663),
               envelope=dict(med=18, p90=60, max=1691)),
    hygiene=dict(CELL=dict(fits=43129, unsorted=21936, span_le0=12428, weight_gt1=9508, dup=0),
                 CELL_EXT=dict(fits=82736, unsorted=57376, span_le0=14978, weight_gt1=19898,
                               dup=23197),
                 CELL_ENV=dict(fits=47943, unsorted=19789, dup=263, differs_from_sorted=4352)),
    d2=dict(walk_x_equals_syn=450, walk_x_in_bx=303),
    d3=dict(nan_fit_frozen_live=129, body_through_untested=66, redrawn_later=5),
)


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def main() -> int:
    t0 = time.time()
    RC = _load("d399rc", "d399_recalc_segment.py")
    NS = _load("d399ns", "d399_new_sample.py")
    DR = _load("d399draw", "d399_draw_construction.py")
    RP = _load("rp", "ragged_panel.py")
    UF = _load("d339uf", "d339_universe_floor.py")
    from backtest_framework.research.structure import pivots_tie_tolerant as PVT

    panel, cleaned = RP.load_ragged(*DR.MINING, fee_bps=0.0, dividend_bound=True)
    draw, rej = NS.draw_sample(panel, cleaned, UF, NS.N_DRAW)
    print(f"\n  panel loaded in {time.time() - t0:.0f}s; draw {[s for s, _ in draw]}")

    C, CE, CV = NS.CELL, NS.CELL_EXT, NS.CELL_ENV
    variants = [
        ("frozen", "CELL: carry=3, no walk", C),
        ("extend", "CELL_EXT: the chosen construction (all switches at default)", CE),
        ("envelope", "CELL_ENV: envelope estimator", CV),
        ("S1_anchored", "S1: height test vs the drawn (anchored) line", dict(CE, height_mode="anchored")),
        ("S2_btol5", "S2: walk tolerance 5%", dict(CE, back_tol=5.0)),
        ("S2_btol10", "S2: walk tolerance 10%", dict(CE, back_tol=10.0)),
        ("S3_native", "S3: never hand walked points on", dict(CE, walk_chain="native_only")),
        ("S3_unbounded", "S3: always hand walked points on", dict(CE, walk_chain="unbounded")),
        ("S3_reach65", "S3: max reach 65", dict(CE, max_reach=65)),
        ("S3_reach260", "S3: max reach 260", dict(CE, max_reach=260)),
        ("S3_reachoff", "S3: max reach off", dict(CE, max_reach=None)),
        ("S4_ttl_off", "S4: keep the break pivot until superseded (original rule)",
         dict(CE, syn_ttl=False)),
    ]
    res, charts = {}, {}
    t1 = time.time()
    for key, label, cell in variants:
        rows, chs = [], []
        for s, st in draw:
            row, ch, _fwd = NS.run_one(cleaned[s], st, cell, RC, DR, PVT)
            row.update(symbol=s, start=int(st), date0=ch["dates"][0], date1=ch["dates"][-1])
            rows.append(row)
            chs.append(dict(symbol=s, start_bar=int(st), n=NS.WIN, **ch))
        res[key] = dict(label=label, cell=cell, rows=rows)
        charts[key] = chs
        print(f"    {key:<14s} {time.time() - t1:>5.0f}s")

    def col(key, f):
        return [f(r) for r in res[key]["rows"]]

    def reach_stats(key):
        allr = []
        for ch in charts[key]:
            for kd in ("support", "resistance"):
                allr += [g["t0"] - g["s0"] for g in ch["segments"][kd]]
        a = np.array(allr, float)
        return (dict(med=float(np.median(a)), p90=float(np.percentile(a, 90)), max=int(a.max()))
                if a.size else dict(med=None, p90=None, max=None))

    names = [s for s, _ in draw]
    print(f"\n  SEGMENTS PER NAME, BEFORE (defective code, as the reviewer reproduced) -> AFTER")
    print(f"  {'':<10s}" + "".join(f"{s:>6s}" for s in names))
    for key in ("frozen", "extend", "envelope"):
        print(f"  {key:<10s}" + "".join(f"{v:>6d}" for v in BEFORE[key]) + "   before")
        print(f"  {'':<10s}" + "".join(f"{v:>6d}" for v in col(key, lambda r: r["segments"]))
              + "   after")
    print(f"\n  REACH (bars from first pivot to first drawn), before -> after")
    for key in ("frozen", "extend", "envelope"):
        b, a = BEFORE["reach"][key], reach_stats(key)
        print(f"    {key:<10s} med {b['med']:>4d} -> {a['med']:>4.0f}   p90 {b['p90']:>4d} -> "
              f"{a['p90']:>4.0f}   max {b['max']:>5d} -> {a['max']:>5d}")

    print(f"\n  THE SWITCHES -- window counts summed over the twelve names")
    print(f"  {'variant':<14s} {'segs':>5s} {'on%':>4s} {'life':>5s} {'reach':>6s} {'p90':>5s} "
          f"{'max':>5s} {'walks':>6s} {'pts':>5s} {'cap':>4s} {'hgt':>5s} {'body':>5s} "
          f"{'syn':>5s} {'rat':>4s} {'drop':>5s} {'shared s0':>9s}")
    summary = {}
    for key, label, _cell in variants:
        rows = res[key]["rows"]
        rs = reach_stats(key)
        life = [r["median_life"] for r in rows if r["median_life"] is not None]
        # consecutive segments sharing an origin (the reviewer's 28% fan-out statistic)
        shared = total = 0
        for ch in charts[key]:
            for kd in ("support", "resistance"):
                sg = ch["segments"][kd]
                total += len(sg)
                shared += sum(1 for i in range(1, len(sg)) if sg[i]["s0"] == sg[i - 1]["s0"])
        summary[key] = dict(
            segments=sum(r["segments"] for r in rows),
            on_pct=round(100 * sum(r["coverage"] for r in rows) / sum(r["side_bars"] for r in rows), 1),
            median_life=(float(np.median(life)) if life else None), reach=rs,
            walks=sum(r["extended"] for r in rows), walk_pts=sum(r["extended_pts"] for r in rows),
            cap_hits=sum(r["max_reach_hit"] for r in rows),
            height=sum(r["fired"]["height"] for r in rows),
            body=sum(r["fired"]["body"] for r in rows),
            syn_made=sum(r["syn_made"] for r in rows), syn_ratified=sum(r["syn_ratified"] for r in rows),
            syn_dropped=sum(r["syn_dropped"] for r in rows),
            shared_s0=shared, segments_total=total,
            nan_fit_whole=sum(r["whole"]["nan_fit"] for r in rows),
            through_body=sum(r["through_body"] for r in rows))
        sm = summary[key]
        print(f"  {key:<14s} {sm['segments']:>5d} {sm['on_pct']:>4.0f} "
              f"{(sm['median_life'] or 0):>5.0f} {(rs['med'] or 0):>6.0f} {(rs['p90'] or 0):>5.0f} "
              f"{(rs['max'] or 0):>5d} {sm['walks']:>6d} {sm['walk_pts']:>5d} {sm['cap_hits']:>4d} "
              f"{sm['height']:>5d} {sm['body']:>5d} {sm['syn_made']:>5d} {sm['syn_ratified']:>4d} "
              f"{sm['syn_dropped']:>5d} {sm['shared_s0']:>4d}/{sm['segments_total']:<4d}")
    print(f"\n  nan candidate fits over all bars, all names: "
          + ", ".join(f"{k} {summary[k]['nan_fit_whole']}" for k in summary))
    print(f"  through-body / inverted on every variant: "
          f"{sum(summary[k]['through_body'] for k in summary)} / 0 -- [R] [C] [Z] asserted on all")

    OUT.write_text(json.dumps(dict(
        what="D399: the review's defects fixed and its suspicions measured; every earlier "
             "walk-era number re-run", seed=NS.SEED, window=NS.WIN, draw=[list(d) for d in draw],
        before=BEFORE, summary=summary,
        variants={k: dict(label=v["label"], cell=v["cell"], rows=v["rows"]) for k, v in res.items()},
        overturned=[
            "the decay sweep (oldest pivot 100/95/90/80/60%) ran with the age weight applied in "
            "about half the fits -- the 0.80 choice was made on a mis-weighted construction",
            "the extend-back comparison ran with the walk resurrecting provisional pivots and "
            "chaining without bound; its reach and segment counts are replaced by this file",
            "the envelope comparison ran with the hull fed unsorted points, returning no edge "
            "where a six-touch edge existed in ~9% of calls",
        ]), indent=1))
    CHART.parent.mkdir(parents=True, exist_ok=True)
    CHART.write_text(json.dumps(dict(cell=CE, seed=NS.SEED, window=NS.WIN, charts=charts["extend"])))
    CHART_ENV.write_text(json.dumps(dict(
        cell=CE, second=CV, seed=NS.SEED, window=NS.WIN, pick=charts["extend"][0]["symbol"],
        variants=[dict(key="frozen", label="regression, with the walk (chosen)", charts=charts["extend"]),
                  dict(key="extend", label="envelope: the most-respected edge", charts=charts["envelope"])])))
    CHART_VAR.write_text(json.dumps(dict(
        seed=NS.SEED, window=NS.WIN,
        variants=[dict(key=k, label=res[k]["label"], cell=res[k]["cell"], charts=charts[k])
                  for k, _l, _c in variants])))
    print(f"\n  [P] {OUT.relative_to(REPO)}, {CHART.relative_to(REPO)}, {CHART_ENV.relative_to(REPO)}, "
          f"{CHART_VAR.relative_to(REPO)} written ({time.time() - t1:.0f}s to run)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
