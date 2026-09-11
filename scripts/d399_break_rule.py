"""D399 -- A BREAK NEEDS DEPTH AND PERSISTENCE, swept on the twelve names.

    uv run python scripts/d399_break_rule.py

On the one-pivot channel (height from one pivot, break together, draw together, stale W=20
D=10% closest, birth 5%): break depth in {0, 1, 2, 3}% x consecutive bars in {1, 2, 3}, at k=1
and k=2. Window counts (D4). Depth 0 / bars 1 at k=1 is the published channel page.
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

OUT = REPO / "data" / "d399_break_rule.json"
CHART = REPO / "temp" / "d399_break_rule_chart.json"


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
    draw, _rej = NS.draw_sample(panel, cleaned, UF, NS.N_DRAW)
    print(f"\n  panel loaded in {time.time() - t0:.0f}s")

    B = dict(NS.CELL_EXT, stale_w=20, stale_d=10.0, stale_stat="min", fit_tol=5.0,
             anchor_mode="pivot", pair_break=True, pair_draw=True)
    variants = []
    for k in (1, 2):
        for dd in (0.0, 1.0, 2.0, 3.0):
            for nb in (1, 2, 3):
                variants.append((f"k{k}_d{dd:g}_b{nb}", dict(B, k=k, break_depth=dd, break_bars=nb)))
    res, charts = {}, {}
    t1 = time.time()
    for key, cell in variants:
        rows, chs = [], []
        for s, st in draw:
            row, ch, _f = NS.run_one(cleaned[s], st, cell, RC, DR, PVT)
            row.update(symbol=s, start=int(st))
            rows.append(row)
            f = row["fired"]
            ch = dict(symbol=s, start_bar=int(st), n=NS.WIN, **ch)
            ch["stats"] = (f"{row['coverage']}/{row['side_bars']} on · life {row['median_life'] or 0:.0f}"
                           f" · body {f['body']} pokes {f['body_poke']} stale {f['stale']} "
                           f"partner {f['pair']} unfit {f['unfit']}")
            chs.append(ch)
        res[key], charts[key] = dict(cell=cell, rows=rows), chs
    print(f"  {len(variants)} variants x 12 names in {time.time() - t1:.0f}s")

    print(f"\n  {'variant':<12s} {'segs':>5s} {'both%':>5s} {'life':>5s} {'p90':>4s} {'body':>5s} "
          f"{'pokes':>6s} {'stale':>6s} {'unfit':>6s} {'far%':>5s}")
    summary = {}
    for key, _c in variants:
        rows = res[key]["rows"]
        lives = []
        far = tot = 0
        for ch in charts[key]:
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
        fsum = {kk: sum(r["fired"][kk] for r in rows) for kk in ("body", "body_poke", "stale", "unfit")}
        summary[key] = dict(segments=sum(r["segments"] for r in rows),
                            both_pct=round(100 * sum(r["coverage"] for r in rows) / (2 * NS.WIN * len(rows)), 1),
                            median_life=(float(np.median(lv_)) if lv_.size else 0),
                            p90_life=(float(np.percentile(lv_, 90)) if lv_.size else 0),
                            far_pct=round(100 * far / max(1, tot), 1),
                            through_body=sum(r["through_body"] for r in rows), **fsum)
        sm = summary[key]
        print(f"  {key:<12s} {sm['segments']:>5d} {sm['both_pct']:>5.0f} {sm['median_life']:>5.0f} "
              f"{sm['p90_life']:>4.0f} {sm['body']:>5d} {sm['body_poke']:>6d} {sm['stale']:>6d} "
              f"{sm['unfit']:>6d} {sm['far_pct']:>5.1f}")
    print(f"  both% = bars with the channel drawn (draw together, so on% = both%); far% as before")
    print(f"  through-body (beyond the depth) / inverted: {sum(summary[k]['through_body'] for k in summary)} / 0")

    OUT.write_text(json.dumps(dict(what="D399: a break needs depth and persistence -- the sweep",
                                   seed=NS.SEED, window=NS.WIN, base=B, summary=summary,
                                   variants=res), indent=1))
    pick = "k1_d2_b2"
    pc = res[pick]["cell"]
    CHART.write_text(json.dumps(dict(
        cell=pc, seed=NS.SEED, window=NS.WIN, charts=charts[pick],
        page=dict(title="A break needs depth and persistence",
                  lede1=("The one-pivot channel, with a break redefined: a body counts as through the "
                         "line only when it closes more than <b>2%</b> beyond it, and the break fires "
                         "only after <b>2 consecutive</b> such closes. A one-day dip is a pullback; a "
                         "sustained close through is a breakdown. The drawing guard carries the same "
                         "tolerance, so a line is still drawn through a shallow pullback. Everything "
                         "else as the channel page: k=1 tie-tolerant pivots, height from one pivot, "
                         "break together, draw together, stale after 20 bars more than 10% off, birth "
                         "check 5%.")))))
    print(f"\n  [P] {OUT.relative_to(REPO)} and {CHART.relative_to(REPO)} ({pick}) written "
          f"({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
