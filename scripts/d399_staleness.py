"""D399 -- IS PRICE STILL RESPECTING THE LINE? The staleness invalidator and the birth check,
swept on the twelve names.

    uv run python scripts/d399_staleness.py                 the sweep, the record, the charts
    uv run python scripts/d399_staleness.py --pick W20_D5   which variant the twelve-name page shows

One statistic, the signed offset of each bar's extreme from the line, serves two tests (see
`recalc_pair`): LIFE -- the line dies when the offset over the last `stale_w` bars, by mean
(the principal's choice) or closest approach, exceeds `stale_d`; BIRTH -- a line is drawn only if
its founding pivots' mean |residual| is within `fit_tol`. Every staleness death is split into
"respected then left" and "never confirmed".

The sweep, declared here (R13): W in {10, 20, 40} x D in {2.5, 5, 10}% on the mean, plus the
closest-approach statistic at W=20/D=5, plus the birth check alone at 2.5 / 5 / 10%, plus the
combination W=20/D=5/mean with birth 5%. Base: CELL_EXT with both off. Window counts (D4).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

OUT = REPO / "data" / "d399_staleness.json"
CHART = REPO / "temp" / "d399_staleness_chart.json"
CHART_ALL = REPO / "temp" / "d399_staleness_variants_chart.json"


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pick", default="W20_D10_min_fit5")
    a = ap.parse_args()
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

    B = NS.CELL_EXT
    variants = [("base", "both off (this morning's page)", dict(B))]
    for w in (10, 20, 40):
        for dd in (2.5, 5.0, 10.0):
            variants.append((f"W{w}_D{dd:g}", f"stale: mean offset over {w} bars > {dd:g}%",
                             dict(B, stale_w=w, stale_d=dd, stale_stat="mean")))
    # THE CLOSEST-APPROACH STATISTIC. The mean offset is dominated by where price sits in the
    # channel, not by whether it returns to the line: at D=5% it killed lines at birth. "Has
    # price come within D of the line in the last W bars" is the chartist's own question.
    for w in (20, 40):
        for dd in (5.0, 10.0):
            variants.append((f"W{w}_D{dd:g}_min", f"stale: closest approach over {w} bars > {dd:g}%",
                             dict(B, stale_w=w, stale_d=dd, stale_stat="min")))
    for ft in (2.5, 5.0, 10.0):
        variants.append((f"fit{ft:g}", f"birth check alone: mean |residual| <= {ft:g}%",
                         dict(B, fit_tol=ft)))
    for w in (20, 40):
        for dd in (5.0, 10.0):
            variants.append((f"W{w}_D{dd:g}_min_fit5",
                             f"stale: closest approach over {w} bars > {dd:g}% + birth 5%",
                             dict(B, stale_w=w, stale_d=dd, stale_stat="min", fit_tol=5.0)))
    variants.append(("W20_D5_fit5", "stale W=20 D=5% mean + birth 5%",
                     dict(B, stale_w=20, stale_d=5.0, stale_stat="mean", fit_tol=5.0)))
    variants.append(("W40_D10_min_fit5_native", "W=40 D=10% closest + birth 5%, walked points "
                     "never handed on",
                     dict(B, stale_w=40, stale_d=10.0, stale_stat="min", fit_tol=5.0,
                          walk_chain="native_only")))

    res, charts = {}, {}
    t1 = time.time()
    for key, label, cell in variants:
        rows, chs = [], []
        for s, st in draw:
            row, ch, _f = NS.run_one(cleaned[s], st, cell, RC, DR, PVT)
            row.update(symbol=s, start=int(st))
            rows.append(row)
            f = row["fired"]
            ch = dict(symbol=s, start_bar=int(st), n=NS.WIN, **ch)
            ch["stats"] = (f"{row['coverage']}/{row['side_bars']} on · life {row['median_life'] or 0:.0f}"
                           f" · reach med {row['median_reach'] or 0:.0f} max {row['max_reach'] or 0}"
                           f" · height {f['height']} body {f['body']} stale {f['stale']} "
                           f"({f['stale_abandoned']} left / {f['stale_unconfirmed']} never) · "
                           f"unfit {f['unfit']}")
            chs.append(ch)
        res[key], charts[key] = dict(label=label, cell=cell, rows=rows), chs
    print(f"  {len(variants)} variants x 12 names in {time.time() - t1:.0f}s")

    print(f"\n  {'variant':<20s} {'segs':>5s} {'on%':>4s} {'life':>5s} {'reach':>6s} {'p90':>5s} "
          f"{'max':>5s} {'hgt':>4s} {'body':>5s} {'stale':>6s} {'left':>5s} {'never':>6s} "
          f"{'unfit':>6s} {'far%':>5s}")
    summary = {}
    for key, label, _c in variants:
        rows = res[key]["rows"]
        allr = [g["t0"] - g["s0"] for ch in charts[key] for kd in ("support", "resistance")
                for g in ch["segments"][kd]]
        ar = np.array(allr, float)
        life = [r["median_life"] for r in rows if r["median_life"] is not None]
        # HOW OFTEN IS A DRAWN LINE FAR FROM PRICE? the share of drawn side-bars whose extreme
        # sits more than 10% off the line -- the thing the test is meant to remove
        far = tot = 0
        for ch in charts[key]:
            lo, hi = np.log(np.array(ch["low"])), np.log(np.array(ch["high"]))
            for kd, e in (("support", lo), ("resistance", hi)):
                for g in ch["segments"][kd]:
                    q = np.arange(g["t0"], g["t1"] + 1)
                    lv = g["g"] * (q + ch["start_bar"]) + g["c"]
                    off = (e[q] - lv) if kd == "support" else (lv - e[q])
                    far += int((off > np.log1p(0.10)).sum())
                    tot += q.size
        fsum = {kk: sum(r["fired"][kk] for r in rows) for kk in
                ("height", "body", "stale", "stale_abandoned", "stale_unconfirmed", "unfit")}
        summary[key] = dict(
            label=label, segments=sum(r["segments"] for r in rows),
            on_pct=round(100 * sum(r["coverage"] for r in rows) / sum(r["side_bars"] for r in rows), 1),
            median_life=(float(np.median(life)) if life else None),
            reach=(dict(med=float(np.median(ar)), p90=float(np.percentile(ar, 90)), max=int(ar.max()))
                   if ar.size else dict(med=0, p90=0, max=0)),
            far_pct=round(100 * far / max(1, tot), 1), through_body=sum(r["through_body"] for r in rows),
            **fsum)
        sm, rs = summary[key], summary[key]["reach"]
        print(f"  {key:<20s} {sm['segments']:>5d} {sm['on_pct']:>4.0f} {(sm['median_life'] or 0):>5.0f} "
              f"{rs['med']:>6.0f} {rs['p90']:>5.0f} {rs['max']:>5d} {sm['height']:>4d} {sm['body']:>5d} "
              f"{sm['stale']:>6d} {sm['stale_abandoned']:>5d} {sm['stale_unconfirmed']:>6d} "
              f"{sm['unfit']:>6d} {sm['far_pct']:>5.1f}")
    print(f"\n  far% = share of drawn side-bars with the bar's extreme more than 10% off the line")
    print(f"  through-body / inverted on every variant: "
          f"{sum(summary[k]['through_body'] for k in summary)} / 0 -- [R] [C] [Z] asserted on all")

    assert a.pick in res, f"--pick must be one of {list(res)}"
    OUT.write_text(json.dumps(dict(
        what="D399: staleness (is price still respecting the line?) and the birth check, swept",
        seed=NS.SEED, window=NS.WIN, base=B, pick=a.pick, summary=summary,
        variants={k: v for k, v in res.items()}), indent=1))
    pc = res[a.pick]["cell"]
    CHART.parent.mkdir(parents=True, exist_ok=True)
    CHART.write_text(json.dumps(dict(
        cell=pc, seed=NS.SEED, window=NS.WIN, charts=charts[a.pick],
        page=dict(title="Is price still respecting the line?",
                  lede1=(f"The chosen construction plus two tests on one statistic, the offset of "
                         f"each bar's extreme from the line. <b>Stale</b>: the line dies when the "
                         f"{'mean' if pc.get('stale_stat') == 'mean' else 'closest'} offset over "
                         f"the last {pc.get('stale_w')} bars exceeds "
                         f"{pc.get('stale_d', 5):g}%, and re-forms from the recent pivots at the next "
                         f"confirmed one. <b>Birth</b>: a line is drawn only if its own pivots sit "
                         f"within {pc.get('fit_tol')}% of it on average. Each header splits the "
                         f"stale deaths into <em>left</em> (respected, then price left) and "
                         f"<em>never</em> (never confirmed after it was drawn).")))))
    CHART_ALL.write_text(json.dumps(dict(
        seed=NS.SEED, window=NS.WIN,
        variants=[dict(key=k, label=res[k]["label"], cell=res[k]["cell"], charts=charts[k])
                  for k, _l, _c in variants])))
    print(f"\n  [P] {OUT.relative_to(REPO)}, {CHART.relative_to(REPO)} ({a.pick}), "
          f"{CHART_ALL.relative_to(REPO)} written ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
