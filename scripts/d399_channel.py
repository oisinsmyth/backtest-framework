"""D399 -- THE SEGMENT IS A CHANNEL: break together, draw together, on the twelve names.

    uv run python scripts/d399_channel.py

On top of the staleness pick (closest approach over 20 bars within 10%, birth check 5%):
    A  as is (each side on its own)
    B  break together   -- any invalidation of one side resets the other
    C  break + draw together -- and a bar shows both lines or neither
    D  C at W=40
Window counts (D4); the page shows C.
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

OUT = REPO / "data" / "d399_channel.json"
CHART = REPO / "temp" / "d399_channel_chart.json"


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

    P = dict(NS.CELL_EXT, stale_w=20, stale_d=10.0, stale_stat="min", fit_tol=5.0)
    variants = [
        ("sides", "each side on its own (the staleness pick)", P),
        ("break", "break together", dict(P, pair_break=True)),
        ("channel", "break together + draw together", dict(P, pair_break=True, pair_draw=True)),
        ("channel_W40", "the same at W=40", dict(P, pair_break=True, pair_draw=True, stale_w=40)),
        # THE HEIGHT FROM ONE PIVOT (the principal): regression gradient, line through the
        # outermost founding pivot, no body consulted in placing it
        ("pivot_sides", "height from one pivot, each side on its own", dict(P, anchor_mode="pivot")),
        ("pivot_channel", "height from one pivot, channel",
         dict(P, anchor_mode="pivot", pair_break=True, pair_draw=True)),
        ("pivot_channel_c2", "the same, min pivots 2 / carry 2",
         dict(P, anchor_mode="pivot", pair_break=True, pair_draw=True, min_piv=2, carry=2)),
    ]
    res, charts = {}, {}
    for key, label, cell in variants:
        rows, chs = [], []
        for s, st in draw:
            row, ch, _f = NS.run_one(cleaned[s], st, cell, RC, DR, PVT)
            row.update(symbol=s, start=int(st))
            rows.append(row)
            f = row["fired"]
            ch = dict(symbol=s, start_bar=int(st), n=NS.WIN, **ch)
            ch["stats"] = (f"{row['coverage']}/{row['side_bars']} on · life {row['median_life'] or 0:.0f}"
                           f" · height {f['height']} body {f['body']} stale {f['stale']} "
                           f"({f['stale_abandoned']} left / {f['stale_unconfirmed']} never) · "
                           f"partner resets {f['pair']} · unfit {f['unfit']}")
            chs.append(ch)
        res[key], charts[key] = dict(label=label, cell=cell, rows=rows), chs

    print(f"\n  {'variant':<12s} {'segs':>5s} {'on%':>4s} {'both%':>5s} {'life':>5s} {'body':>5s} "
          f"{'stale':>6s} {'pair':>5s} {'unfit':>6s} {'far%':>5s}")
    summary = {}
    for key, label, _c in variants:
        rows = res[key]["rows"]
        life = [r["median_life"] for r in rows if r["median_life"] is not None]
        far = tot = both = 0
        for ch in charts[key]:
            lo, hi = np.log(np.array(ch["low"])), np.log(np.array(ch["high"]))
            on = {}
            for kd, e in (("support", lo), ("resistance", hi)):
                on[kd] = np.zeros(NS.WIN, bool)
                for g in ch["segments"][kd]:
                    q = np.arange(g["t0"], g["t1"] + 1)
                    on[kd][q] = True
                    lv = g["g"] * (q + ch["start_bar"]) + g["c"]
                    off = (e[q] - lv) if kd == "support" else (lv - e[q])
                    far += int((off > np.log1p(0.10)).sum())
                    tot += q.size
            both += int((on["support"] & on["resistance"]).sum())
        fsum = {kk: sum(r["fired"][kk] for r in rows) for kk in ("body", "stale", "pair", "unfit")}
        summary[key] = dict(label=label, segments=sum(r["segments"] for r in rows),
                            on_pct=round(100 * sum(r["coverage"] for r in rows) / (2 * NS.WIN * len(rows)), 1),
                            both_pct=round(100 * both / (NS.WIN * len(rows)), 1),
                            median_life=(float(np.median(life)) if life else None),
                            far_pct=round(100 * far / max(1, tot), 1),
                            through_body=sum(r["through_body"] for r in rows), **fsum)
        sm = summary[key]
        print(f"  {key:<12s} {sm['segments']:>5d} {sm['on_pct']:>4.0f} {sm['both_pct']:>5.0f} "
              f"{(sm['median_life'] or 0):>5.0f} {sm['body']:>5d} {sm['stale']:>6d} {sm['pair']:>5d} "
              f"{sm['unfit']:>6d} {sm['far_pct']:>5.1f}")
    print(f"  both% = share of bars with BOTH lines drawn; far% as before (>10% off, drawn side-bars)")
    print(f"  through-body / inverted: {sum(summary[k]['through_body'] for k in summary)} / 0")

    OUT.write_text(json.dumps(dict(what="D399: the segment as a channel -- break together, draw together",
                                   seed=NS.SEED, window=NS.WIN, summary=summary,
                                   variants=res), indent=1))
    pick = "pivot_channel"
    pc = res[pick]["cell"]
    CHART.write_text(json.dumps(dict(
        cell=pc, seed=NS.SEED, window=NS.WIN, charts=charts[pick],
        page=dict(title="The height from one pivot",
                  lede1=("The channel &mdash; both lines thrown away when either is invalidated, a "
                         "bar drawn only when both qualify &mdash; with the line's <b>height taken "
                         "from one pivot</b>: the gradient is still the weighted regression through "
                         "the pivots, and the line passes through the founding pivot that sits "
                         "outermost against that slope, every other pivot on or inside it. No body "
                         "is consulted in placing it; the forward body-break rule polices it from "
                         "the bar it is drawn. Otherwise the staleness pick: k=1 tie-tolerant "
                         "pivots, min_piv 4, break bar as provisional pivot, age decay 0.80, carry 3 "
                         "with the walk, stale after 20 bars more than 10% off, birth check 5%.")))))
    print(f"\n  [P] {OUT.relative_to(REPO)} and {CHART.relative_to(REPO)} written ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
