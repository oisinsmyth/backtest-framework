"""D399 -- THE FINAL CONSTRUCTION, as the principal handed it over, on the twelve names.

    uv run python scripts/d399_final.py

`d399_new_sample.CELL_FINAL` is the settings line from the live page transcribed field for field.
This runs it on the declared draw, prints the window counts, and writes data/d399_final.json and
temp/d399_final_chart.json for scripts/d399_splice_sample_page.py. No score: the principal chose
it by eye, and forward returns by state are the next question, not this one.
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

OUT = REPO / "data" / "d399_final.json"
CHART = REPO / "temp" / "d399_final_chart.json"


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--second", action="store_true",
                    help="a SECOND draw: new seed, and the first draw's names excluded as well")
    a = ap.parse_args()
    global OUT, CHART
    t0 = time.time()
    RC = _load("d399rc", "d399_recalc_segment.py")
    NS = _load("d399ns", "d399_new_sample.py")
    DR = _load("d399draw", "d399_draw_construction.py")
    RP = _load("rp", "ragged_panel.py")
    UF = _load("d339uf", "d339_universe_floor.py")
    from backtest_framework.research.structure import pivots_tie_tolerant as PVT

    panel, cleaned = RP.load_ragged(*DR.MINING, fee_bps=0.0, dividend_bound=True)
    draw, rej = NS.draw_sample(panel, cleaned, UF, NS.N_DRAW)
    seed = NS.SEED
    if a.second:
        # THE SECOND DRAW, declared: the same rule, seed 20260911, and every name of the first
        # draw excluded along with GME -- twelve names the construction has never been shown on.
        seed = 20260911
        first = tuple(sorted({s for s, _ in draw}))
        draw, rej = NS.draw_sample(panel, cleaned, UF, NS.N_DRAW, seed=seed,
                                   exclude=NS.EXCLUDE + first)
        OUT = OUT.with_name("d399_final_draw2.json")
        CHART = CHART.with_name("d399_final_draw2_chart.json")
        print(f"\n  SECOND DRAW (seed {seed}; excluded GME and the first draw: {', '.join(first)}; "
              f"{rej['eligible']:,} eligible pairs)")
        for s, st in draw:
            b = cleaned[s]
            print(f"    {s:<8s} bars {st:>5d}-{st + NS.WIN - 1:<5d}  "
                  f"{str(b[st].timestamp)[:10]} -> {str(b[st + NS.WIN - 1].timestamp)[:10]}")
    print(f"\n  panel loaded in {time.time() - t0:.0f}s")
    print(f"  {NS.SETTINGS_LINE_FINAL}\n")

    cell = NS.CELL_FINAL
    rows, charts = [], []
    print(f"  {'name':<6s} {'segs':>5s} {'on%':>4s} {'life':>5s} {'body':>5s} {'pokes':>6s} "
          f"{'stale':>6s} {'partner':>8s} {'unfit':>6s} {'walks':>6s}")
    for s, st in draw:
        row, ch, _f = NS.run_one(cleaned[s], st, cell, RC, DR, PVT)
        row.update(symbol=s, start=int(st), date0=ch["dates"][0], date1=ch["dates"][-1])
        rows.append(row)
        f = row["fired"]
        ch = dict(symbol=s, start_bar=int(st), n=NS.WIN, **ch)
        ch["stats"] = (f"{row['coverage']}/{row['side_bars']} on · life {row['median_life'] or 0:.0f}"
                       f" · body {f['body']} pokes {f['body_poke']} stale {f['stale']} "
                       f"({f['stale_abandoned']} left / {f['stale_unconfirmed']} never) · "
                       f"partner {f['pair']} · unfit {f['unfit']} · walks {row['extended']}")
        charts.append(ch)
        print(f"  {s:<6s} {row['segments']:>5d} {100 * row['coverage'] / row['side_bars']:>4.0f} "
              f"{(row['median_life'] or 0):>5.0f} {f['body']:>5d} {f['body_poke']:>6d} {f['stale']:>6d} "
              f"{f['pair']:>8d} {f['unfit']:>6d} {row['extended']:>6d}")
    lives = []
    far = tot = 0
    for ch in charts:
        lo, hi = np.log(np.array(ch["low"])), np.log(np.array(ch["high"]))
        for kd, e in (("support", lo), ("resistance", hi)):
            for g in ch["segments"][kd]:
                q = np.arange(g["t0"], g["t1"] + 1)
                lives.append(q.size)
                lv = g["g"] * (q + ch["start_bar"]) + g["c"]
                off = (e[q] - lv) if kd == "support" else (lv - e[q])
                far += int((off > np.log1p(0.10)).sum())
                tot += q.size
    lv_ = np.array(lives, float)
    summary = dict(
        segments=sum(r["segments"] for r in rows),
        on_pct=round(100 * sum(r["coverage"] for r in rows) / sum(r["side_bars"] for r in rows), 1),
        median_life=(float(np.median(lv_)) if lv_.size else 0),
        p90_life=(float(np.percentile(lv_, 90)) if lv_.size else 0),
        far_pct=round(100 * far / max(1, tot), 1),
        through_body=sum(r["through_body"] for r in rows),
        **{kk: sum(r["fired"][kk] for r in rows) for kk in ("body", "body_poke", "stale", "pair", "unfit")})
    print(f"\n  ALL TWELVE: {summary['segments']} segments · {summary['on_pct']:.0f}% of bars with the "
          f"channel · life median {summary['median_life']:.0f} p90 {summary['p90_life']:.0f} · "
          f"far (>10% off) {summary['far_pct']:.1f}% · through body (beyond 2%) {summary['through_body']} "
          f"· [R] [C] [Z] asserted on all")

    OUT.write_text(json.dumps(dict(what="D399: the principal's final construction on the twelve names"
                                        + (" -- SECOND draw" if a.second else ""),
                                   settings_line=NS.SETTINGS_LINE_FINAL, cell=cell, seed=seed,
                                   draw=[list(d) for d in draw], window=NS.WIN, summary=summary,
                                   rows=rows), indent=1))
    CHART.write_text(json.dumps(dict(
        cell=cell, seed=seed, window=NS.WIN, charts=charts,
        page=dict(title=("The final construction, twelve more names" if a.second
                         else "The final construction"),
                  lede1=(("A <b>second draw</b> under the same rule &mdash; seed 20260911, GME and "
                          "all eleven names of the first draw excluded &mdash; so twelve names the "
                          "construction has never been shown on. " if a.second else "") +
                         "The construction as chosen by eye on the live page and handed over as its "
                         "settings line: <b>k=2 pivots, min 2, carry 7; height deadband 20% against "
                         "the drawn line; min width 10%; a break needs 2% through for 2 bars; break "
                         "bar as provisional pivot; height from the age-weighted quantile q=0.2 under "
                         "rank decay 0.76; the walk with hand-on across body breaks, reach 130; stale "
                         "when the mean offset over 35 bars exceeds 18%; birth check 16%; the channel "
                         "breaks and draws together.</b> Each header carries the window's own counts. "
                         "The settings line is in <code>data/d399_final.json</code>.")))))
    print(f"  [P] {OUT.relative_to(REPO)} and {CHART.relative_to(REPO)} written ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
