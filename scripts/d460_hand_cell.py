"""D460 -- THE HAND CELL: D399's pivot construction re-dialled against the principal's hand-drawn
lines, and the twelve-name page that shows both.

    uv run python scripts/d460_hand_cell.py            score the cell, write the chart JSON
    uv run python scripts/d399_splice_sample_page.py temp/d460_hand_chart.json temp/d460_hand_page.html

WHAT IT IS. The swing-envelope rebuild (`d460_swing_envelope.py`) lost on the scorecard: two-point
lines through minor swings gave noisier gradients than D399's envelope over several confirmed
pivots, which is the one estimator whose gradients matched the principal's (sign 88-92%). So the
construction that gets closest to the hand lines is D399's, with the rules that starved it of
coverage removed and the rules the hand lines obey added -- each change scored on the card:

  pair off        a side is drawn without waiting for its partner (recall 30% -> 54-59%)
  k = 1           one-bar pivot confirmation, the principal's own draw lag (lag +5 -> -2)
  min_width 0     no channel-width kill of single lines (recall -> 65%)
  break_keep 1    on a break only the newest pivot is carried across it (overstay 42% -> 26%);
                  the new switch in `recalc_pair`
  break 3% / 1    a close 3% through the line ends it, one bar (the principal's median 4.4%
                  through a line that itself sits 4% outside the wicks)
  margin 4%       the drawn level is the pivot line shifted 4% outward, the principal's offset
  stale 25 / 12   the drift end, kept from CELL_FINAL but tighter

Everything else is CELL_FINAL. The scorecard for this cell against the hand set, and the chart
of its lines on the twelve names with the hand lines overlaid, are what this script writes.
"""
from __future__ import annotations

import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
HAND = REPO / "data" / "d451_hand_drawn_lines.json"
CARD = REPO / "data" / "d451_hand_scorecard.json"
OUT = REPO / "data" / "d460_hand_scorecard.json"
CHART = REPO / "temp" / "d460_hand_chart.json"


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


NS = _load("d399ns", "d399_new_sample.py")
CELL_HAND = dict(NS.CELL_FINAL, pair_break=False, pair_draw=False, k=1, min_width=0.0,
                 break_keep=1, break_depth=3.0, break_bars=1, stale_w=25, stale_d=12.0)
MARGIN = 4.0
SETTINGS_LINE_HAND = ("k=1 mp=2 maxp=0 carry=7 dh=20 dg=0 mw=0 body=on bdepth=3 bbars=1 bkeep=1 syn=on "
                      "anchor=quantile aq=0.2 dmode=rank decay=0.76 height=anchored ttl=on walk=on "
                      "btol=-1 chain=body_only reach=130 stalew=25 staled=12 stalestat=mean "
                      "fittol=16 pairbreak=off pairdraw=off fit=ols ttol=0.37 mt=1 margin=4")


def pivots_of(PVT, bars, k):
    """The confirmed pivots per side as (bar index array, log price array) -- the one input the
    construction needs that requires the bar objects, so a worker can be handed arrays only."""
    ps = PVT(bars, k)
    piv = {}
    for kd, sg in (("support", -1), ("resistance", +1)):
        piv[kd] = (np.array([p.index for p in ps if p.sign == sg], int),
                   np.log(np.array([p.price for p in ps if p.sign == sg], float)))
    return piv


def hand_lines(RC, DR, PVT, bars, cell, margin):
    """The per-bar view: drawn level (with the margin) and gradient per side."""
    op = np.array([b.bar.open for b in bars], float)
    cl = np.array([b.bar.close for b in bars], float)
    hi = np.array([b.bar.high for b in bars], float)
    lo = np.array([b.bar.low for b in bars], float)
    return lines_from_arrays(RC, op, cl, hi, lo, pivots_of(PVT, bars, cell["k"]), cell, margin,
                             DR.DELTA, RC.INF if cell["dg"] is None else DR.h_of_annual(cell["dg"]))


def lines_from_arrays(RC, op, cl, hi, lo, piv, cell, margin, delta, max_dg):
    """The construction on arrays alone (D461's workers): no bar objects, no fixture modules."""
    m = op.size
    with np.errstate(divide="ignore"):
        body = {"support": np.log(np.minimum(op, cl)), "resistance": np.log(np.maximum(op, cl))}
        ext = {"support": np.log(lo), "resistance": np.log(hi)}
    G, L, S, why = RC.recalc_pair(
        piv, cell["k"], body, m,
        carry=cell["carry"], min_piv=cell["min_piv"],
        max_dg=max_dg,
        max_dh=math.log1p(cell["dh"] / 100), use_body=cell["use_body"],
        min_width=math.log1p(cell["min_width"] / 100), delta=delta, ext_log=ext,
        break_pivot=cell["break_pivot"], anchor_clear=cell["anchor_clear"],
        decay_end=cell["decay_end"], extend_back=cell["extend_back"],
        back_tol=None, fit_mode=cell["fit_mode"], touch_tol=cell["touch_tol"],
        min_touch=cell["min_touch"], height_mode=cell["height_mode"],
        walk_chain=cell["walk_chain"], max_reach=cell["max_reach"], syn_ttl=cell["syn_ttl"],
        stale_w=cell["stale_w"], stale_d=math.log1p(cell["stale_d"] / 100),
        stale_stat=cell["stale_stat"],
        fit_tol=None if cell["fit_tol"] is None else math.log1p(cell["fit_tol"] / 100),
        pair_break=cell["pair_break"], pair_draw=cell["pair_draw"], anchor_mode=cell["anchor_mode"],
        anchor_q=cell["anchor_q"], decay_mode=cell["decay_mode"],
        break_depth=math.log1p(cell["break_depth"] / 100), break_bars=cell["break_bars"],
        max_piv=cell["max_piv"], break_keep=cell.get("break_keep"))
    lm = math.log1p(margin / 100)
    L = {"support": L["support"] - lm, "resistance": L["resistance"] + lm}
    drawn = {kd: np.isfinite(L[kd]) for kd in ("support", "resistance")}
    return dict(m=m, cl=cl, G=G, L=L, drawn=drawn)


def main() -> int:
    t0 = time.time()
    RC = _load("d399rc", "d399_recalc_segment.py")
    DR = _load("d399draw", "d399_draw_construction.py")
    RP = _load("rp", "ragged_panel.py")
    SC = _load("d451sc", "d451_score_hand_lines.py")
    from backtest_framework.research.structure import pivots_tie_tolerant as PVT

    H = json.loads(HAND.read_text(encoding="utf-8"))
    panel, cleaned = RP.load_ragged(*DR.MINING, fee_bps=0.0, dividend_bound=True)
    print(f"  panel in {time.time() - t0:.0f}s\n  {SETTINGS_LINE_HAND}")
    acc = SC.fresh()
    charts = []
    lm = math.log1p(MARGIN / 100)
    for k, rec in H.items():
        bars = cleaned[rec["symbol"]]
        N = hand_lines(RC, DR, PVT, bars, CELL_HAND, MARGIN)
        SC.score(N, rec, acc)
        row, ch, _f = NS.run_one(bars, rec["start"], CELL_HAND, RC, DR, PVT)
        for kd, sg in (("support", -1.0), ("resistance", 1.0)):
            for g in ch["segments"][kd]:
                g["c"] = g["c"] + sg * lm                     # the drawn level carries the margin
        ch = dict(symbol=rec["symbol"], start_bar=int(rec["start"]), n=rec["n"], **ch)
        ch["hand"] = rec["lines"]
        f = row["fired"]
        ch["stats"] = (f"{row['coverage']}/{row['side_bars']} on · life {row['median_life'] or 0:.0f} · "
                       f"body {f['body']} stale {f['stale']} unfit {f['unfit']} · "
                       f"hand lines {len(rec['lines'])}")
        charts.append(ch)
        print(f"    {k:<10s} segs {row['segments']:>3d}  on {100 * row['coverage'] / row['side_bars']:>3.0f}%  "
              f"life {(row['median_life'] or 0):>3.0f}  hand lines {len(rec['lines'])}")
    rows = SC.table(acc)
    card = json.loads(CARD.read_text(encoding="utf-8"))["score"]
    print(f"\n  {'':<10s} {'kind':<11s} {'recall':>7s} {'precis':>7s} {'sign':>5s} {'|dgrad|':>8s} {'|dlvl|':>7s} "
          f"{'lag':>5s} {'matched':>8s} {'overstay':>9s}")

    def fmt(name, rr):
        for kd, r in rr.items():
            print(f"  {name:<10s} {kd:<11s} {100 * r['recall']:>6.0f}% {100 * r['precision']:>6.0f}% "
                  f"{100 * r['sign']:>4.0f}% {r['dgrad_med']:>7.0f}% {r['dlevel_med']:>6.1f}% "
                  f"{r['lag_med']:>5.0f} {100 * r['matched']:>7.0f}% {100 * r['overstay']:>8.0f}%")

    for name in ("PIVOT", "GROW", "HYST", "HYST-WIDE"):
        fmt(name, card[name])
    fmt("HAND-CELL", rows)
    OUT.write_text(json.dumps(dict(what="D460: D399's construction re-dialled against the hand-drawn lines",
                                   settings_line=SETTINGS_LINE_HAND, cell=CELL_HAND, margin=MARGIN,
                                   score=rows, others=card), indent=1))
    CHART.write_text(json.dumps(dict(
        cell=CELL_HAND, seed=None, window=NS.WIN, charts=charts,
        page=dict(title="The hand cell against the hand lines",
                  eyebrow="D460 &middot; the pivot construction re-dialled against the principal's hand-drawn lines",
                  cfg=SETTINGS_LINE_HAND,
                  lede1=("D399's pivot construction re-dialled against the principal's hand-drawn lines "
                         "(D460): <b>pair rules off, one-bar pivots, no width kill, one pivot carried across "
                         "a break, a 3% close break, a 4% margin, staleness 25/12</b>. Solid lines are the "
                         "construction's, read causally bar by bar; <b>dashed lines are the principal's</b>, "
                         "drawn on the step page with the future hidden, from anchor to anchor, dotted on "
                         "to the bar they were ended. Same colours: blue support, orange resistance."),
                  lede2=(f"Scorecard against the 140 hand lines: recall {100 * rows['support']['recall']:.0f}% / "
                         f"{100 * rows['resistance']['recall']:.0f}%, sign {100 * rows['support']['sign']:.0f}% / "
                         f"{100 * rows['resistance']['sign']:.0f}%, gradient within {rows['support']['dgrad_med']:.0f}% / "
                         f"{rows['resistance']['dgrad_med']:.0f}% a year, lag {rows['support']['lag_med']:.0f} / "
                         f"{rows['resistance']['lag_med']:.0f} bars, overstay {100 * rows['support']['overstay']:.0f}% / "
                         f"{100 * rows['resistance']['overstay']:.0f}% (support / resistance)."))), separators=(",", ":")))
    print(f"  written {OUT.relative_to(REPO)} and {CHART.relative_to(REPO)} ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
