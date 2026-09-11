"""D399 -- AGE ON THE ENVELOPE: the twelve names at decay 1.0 / 0.9 / 0.8, side by side.

    uv run python scripts/d399_envelope_age.py

`envelope_fit` now takes `decay_end`: each touching pivot supports an edge by 1 at the newest
pivot down to `decay_end` at the oldest, and the edge with the largest support wins (longest
span on a tie). Candidates, validity and qualification are unchanged, and decay_end = 1.0 is
bit-identical to the unweighted choice (`audit_envelope_age`, [A]).

This runs CELL_ENV at the three weights on the drawn twelve, reports window counts side by
side, and writes one chart JSON with the 36 panels grouped by name (three per name, weight in
the label) for scripts/d399_splice_sample_page.py. Everything else in the cell is CELL_ENV.
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

OUT = REPO / "data" / "d399_envelope_age.json"
CHART = REPO / "temp" / "d399_envelope_age_chart.json"
WEIGHTS = (1.0, 0.9, 0.8)


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

    RC.audit_envelope_age()                       # [A] before any number is drawn
    panel, cleaned = RP.load_ragged(*DR.MINING, fee_bps=0.0, dividend_bound=True)
    draw, _rej = NS.draw_sample(panel, cleaned, UF, NS.N_DRAW)
    print(f"\n  panel loaded in {time.time() - t0:.0f}s; [A] OK")

    res, charts = {}, {}
    for w in WEIGHTS:
        cell = dict(NS.CELL_ENV, decay_end=w)
        rows, chs = [], []
        for s, st in draw:
            row, ch, _f = NS.run_one(cleaned[s], st, cell, RC, DR, PVT)
            row.update(symbol=s, start=int(st))
            rows.append(row)
            ch = dict(symbol=f"{s} · decay {w:g}", start_bar=int(st), n=NS.WIN, **ch)
            ch["stats"] = (f"{row['coverage']}/{row['side_bars']} on · life "
                           f"{row['median_life'] or 0:.0f} · reach med {row['median_reach'] or 0:.0f} "
                           f"max {row['max_reach'] or 0} · height {row['fired']['height']} "
                           f"body {row['fired']['body']}")
            chs.append(ch)
        res[w], charts[w] = rows, chs

    # the control must be the envelope as published this morning: same segments per name
    names = [s for s, _ in draw]
    print(f"\n  SEGMENTS PER NAME (window)      " + "".join(f"{s:>6s}" for s in names))
    for w in WEIGHTS:
        print(f"  decay {w:<4g}                      "
              + "".join(f"{r['segments']:>6d}" for r in res[w]))
    print(f"\n  {'decay':<6s} {'segs':>5s} {'on%':>4s} {'life':>5s} {'reach':>6s} {'p90':>5s} "
          f"{'max':>5s} {'hgt':>5s} {'body':>5s} {'walks':>6s}")
    summary = {}
    for w in WEIGHTS:
        rows = res[w]
        allr = [g["t0"] - g["s0"] for ch in charts[w] for kd in ("support", "resistance")
                for g in ch["segments"][kd]]
        a = np.array(allr, float)
        life = [r["median_life"] for r in rows if r["median_life"] is not None]
        summary[w] = dict(
            segments=sum(r["segments"] for r in rows),
            on_pct=round(100 * sum(r["coverage"] for r in rows) / sum(r["side_bars"] for r in rows), 1),
            median_life=(float(np.median(life)) if life else None),
            reach=dict(med=float(np.median(a)), p90=float(np.percentile(a, 90)), max=int(a.max()))
            if a.size else None,
            height=sum(r["fired"]["height"] for r in rows), body=sum(r["fired"]["body"] for r in rows),
            walks=sum(r["extended"] for r in rows), through_body=sum(r["through_body"] for r in rows))
        sm, rs = summary[w], summary[w]["reach"] or dict(med=0, p90=0, max=0)
        print(f"  {w:<6g} {sm['segments']:>5d} {sm['on_pct']:>4.0f} {(sm['median_life'] or 0):>5.0f} "
              f"{rs['med']:>6.0f} {rs['p90']:>5.0f} {rs['max']:>5d} {sm['height']:>5d} {sm['body']:>5d} "
              f"{sm['walks']:>6d}")
    print(f"  through-body / inverted: {sum(summary[w]['through_body'] for w in WEIGHTS)} / 0 -- "
          f"[R] [C] [Z] asserted on all")

    OUT.write_text(json.dumps(dict(
        what="D399: age on the envelope -- weighted touch support at 1.0 / 0.9 / 0.8",
        seed=NS.SEED, window=NS.WIN, cell=NS.CELL_ENV, weights=list(WEIGHTS),
        summary={str(w): summary[w] for w in WEIGHTS},
        rows={str(w): res[w] for w in WEIGHTS}), indent=1))
    grouped = [ch for i in range(len(draw)) for w in WEIGHTS for ch in [charts[w][i]]]
    CHART.parent.mkdir(parents=True, exist_ok=True)
    CHART.write_text(json.dumps(dict(
        cell=NS.CELL_ENV, seed=NS.SEED, window=NS.WIN, charts=grouped,
        page=dict(title="Age on the envelope",
                  lede1=("The envelope on the same twelve draws at three age weights, three panels "
                         "per name. Age enters the envelope at its one decision &mdash; which valid "
                         "edge wins: each touching pivot supports an edge by 1 at the newest pivot "
                         "down to the weight at the oldest, the largest sum wins, longest span on a "
                         "tie. Candidates, validity and the touch count that qualifies a line are "
                         "unchanged; <b>decay 1.0 is the envelope exactly as before</b>. Each "
                         "header carries the window's own counts.")))))
    print(f"\n  [P] {OUT.relative_to(REPO)} and {CHART.relative_to(REPO)} written "
          f"({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
