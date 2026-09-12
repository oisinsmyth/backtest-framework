"""SCORE THE CONSTRUCTIONS AGAINST THE PRINCIPAL'S HAND-DRAWN LINES, bar by bar.

    uv run python scripts/d451_score_hand_lines.py

THE TARGET. `data/d451_hand_drawn_lines.json`: 140 lines on the twelve page names, drawn one bar
at a time with the future hidden, each with the bar it was drawn at (`at`) and the bar it was
ended at (`until`). At bar t the principal HAD the lines with at <= t < until. That is what a
causal construction is asked to reproduce, and this is the first time it has been written down.

THE CONSTRUCTIONS, each read at every panel bar exactly as the trader would have seen it:
  PIVOT      D399's CELL_FINAL, the pivot construction (D434/D450's causal arm)
  GROW       D451's grow-right line (the trading line of D451)
  HYST       D452's line: hysteresis, trend-side breaks, 40% survive cap
  HYST-WIDE  the principal's wider candidate: wick breaks 4%, two bars, cap 60, survive tol 15.5

THE SCORE, per construction and kind (support / resistance), over the panel bars:
  recall      of the bars on which the principal had a line, the share on which the construction
              showed one
  precision   of the bars on which the construction showed a line, the share on which the
              principal had one
  sign        when both had one: the share with the same gradient sign
  |dgrad|     when both: median absolute gradient difference, % per year
  |dlevel|    when both: median absolute difference of the two lines' levels at the bar, %
  lag         per principal line: bars from its draw bar to the first bar the construction
              showed a same-kind line of the same sign (searched from 5 bars before the draw to
              the line's end); the median, and the share of lines it ever matched
  overstay    per ended principal line: the share for which the construction still showed a
              same-kind line five bars after the principal ended it

Where several of the principal's lines of one kind are alive at a bar, the most recently drawn
is the reference. Nothing here is a trade; it is a scorecard for the drawing.
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
OUT = REPO / "data" / "d451_hand_scorecard.json"

LINES = {
    "GROW": ("split=causal grow=parallel back=9 atmax=end tol=2 mt=2 basis=wick minlen=30 maxlen=1000 "
             "mw=5.5 maxw=55 maxoff=6.5 mintd=10 tau=1 brk=-1 bbars=1 bon=close"),
    "HYST": ("split=causal grow=parallel back=9 atmax=end tol=2 mt=2 basis=wick minlen=30 maxlen=1000 "
             "mw=5.5 maxw=55 maxoff=6.5 mintd=10 tau=1 brk=2 bbars=1 bon=close bside=trend surv=loose stol=4 smaxw=40"),
    "HYST-WIDE": ("split=causal grow=parallel back=9 atmax=end tol=2 mt=2 basis=wick minlen=30 maxlen=1000 "
                  "mw=5.5 maxw=55 maxoff=6.5 mintd=10 tau=1 brk=4 bbars=2 bon=wick bside=trend surv=loose stol=15.5 smaxw=60"),
}
KINDS = ("support", "resistance")
PPY = 252.0


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def hand_at(rec, t):
    """The principal's line of each kind alive at bar t (most recently drawn wins), as
    (gradient per bar in log, level in log at t) or None."""
    out = {}
    for kd in KINDS:
        best = None
        for L in rec["lines"]:
            if L["kind"] != kd or not (L["at"] <= t < L.get("until", 10 ** 9)):
                continue
            if best is None or L["at"] >= best["at"]:
                best = L
        if best is None:
            out[kd] = None
        else:
            g = (math.log(best["p2"]) - math.log(best["p1"])) / (best["x2"] - best["x1"])
            out[kd] = (g, math.log(best["p1"]) + g * (t - best["x1"]), best)
    return out


def score(N, rec, acc):
    st0, n = rec["start"], rec["n"]
    for t in range(st0, st0 + n):
        H = hand_at(rec, t)
        for kd in KINDS:
            h = H[kd]
            c_on = bool(N["drawn"][kd][t])
            a = acc[kd]
            a["hand"] += h is not None
            a["cons"] += c_on
            if h is not None and c_on:
                a["both"] += 1
                g_c, l_c = float(N["G"][kd][t]), float(N["L"][kd][t])
                a["sign"] += (g_c > 0) == (h[0] > 0)
                a["dgrad"].append(abs(100 * (math.expm1(g_c * PPY) - math.expm1(h[0] * PPY))))
                a["dlevel"].append(100 * abs(math.expm1(l_c - h[1])))
    # timing, per principal line
    for L in rec["lines"]:
        kd = L["kind"]
        g_h = (math.log(L["p2"]) - math.log(L["p1"])) / (L["x2"] - L["x1"])
        end = min(L.get("until", st0 + n), st0 + n)
        found = None
        for t in range(max(st0, L["at"] - 5), end):
            if N["drawn"][kd][t] and (float(N["G"][kd][t]) > 0) == (g_h > 0):
                found = t - L["at"]
                break
        acc[kd]["lines"] += 1
        if found is not None:
            acc[kd]["matched"] += 1
            acc[kd]["lag"].append(found)
        # OVERSTAY IS SCORED ONLY ON ENDS THAT WERE ENDS. 40% of the principal's ends were a
        # replacement -- a new same-kind line drawn the same bar -- so a construction still
        # showing a line five bars later is agreeing with the principal, not overstaying.
        # Only breaks and drifts, where the principal had NO same-kind line within a bar, count.
        replaced = any(M is not L and M["kind"] == kd and abs(M["at"] - L.get("until", -99)) <= 1 for M in rec["lines"])
        if "until" in L and L["until"] + 5 < st0 + n and not replaced:
            acc[kd]["ended"] += 1
            t5 = L["until"] + 5
            acc[kd]["overstay"] += bool(N["drawn"][kd][t5]) and (float(N["G"][kd][t5]) > 0) == (g_h > 0)


def fresh():
    return {kd: dict(hand=0, cons=0, both=0, sign=0, dgrad=[], dlevel=[], lines=0, matched=0, lag=[],
                     ended=0, overstay=0) for kd in KINDS}


def table(acc):
    rows = {}
    for kd in KINDS:
        a = acc[kd]
        rows[kd] = dict(
            recall=a["both"] / max(1, a["hand"]), precision=a["both"] / max(1, a["cons"]),
            sign=a["sign"] / max(1, a["both"]),
            dgrad_med=float(np.median(a["dgrad"])) if a["dgrad"] else float("nan"),
            dlevel_med=float(np.median(a["dlevel"])) if a["dlevel"] else float("nan"),
            lag_med=float(np.median(a["lag"])) if a["lag"] else float("nan"),
            matched=a["matched"] / max(1, a["lines"]),
            overstay=a["overstay"] / max(1, a["ended"]),
            n_hand_bars=a["hand"], n_cons_bars=a["cons"], n_lines=a["lines"])
    return rows


def main() -> int:
    t0 = time.time()
    RC = _load("d399rc", "d399_recalc_segment.py")
    CG = _load("d451cg", "d451_causal_grow.py")
    D4 = _load("d434", "run_d434_channel_trades.py")
    NS = _load("d399ns", "d399_new_sample.py")
    DR = _load("d399draw", "d399_draw_construction.py")
    RP = _load("rp", "ragged_panel.py")
    from backtest_framework.research.structure import pivots_tie_tolerant as PVT

    H = json.loads(HAND.read_text(encoding="utf-8"))
    panel, cleaned = RP.load_ragged(*DR.MINING, fee_bps=0.0, dividend_bound=True)
    print(f"  panel loaded in {time.time() - t0:.0f}s; {sum(len(r['lines']) for r in H.values())} hand lines on {len(H)} names")
    acc = {name: fresh() for name in ("PIVOT",) + tuple(LINES)}
    for k, rec in H.items():
        bars = cleaned[rec["symbol"]]
        assert len(bars) >= rec["start"] + rec["n"], k
        t1 = time.time()
        N = D4.build_lines(RC, DR, PVT, bars, NS.CELL_FINAL, True)
        score(N, rec, acc["PIVOT"])
        for name, line in LINES.items():
            P = CG.parse_line(line)
            op = np.array([b.bar.open for b in bars], float)
            cl = np.array([b.bar.close for b in bars], float)
            lo = np.log(np.array([b.bar.low for b in bars], float))
            hi = np.log(np.array([b.bar.high for b in bars], float))
            a0 = max(0, rec["start"] - (P["maxlen"] + P["back"] + 50))   # phase-free after maxlen + back
            runs = CG.causal_channels(RC, lo, hi, P, a0, rec["start"] + rec["n"], cl=np.log(cl))
            N, _ = CG.causal_lines(RC, bars, P, runs=runs)
            score(N, rec, acc[name])
        print(f"    {k:<10s} scored in {time.time() - t1:.0f}s")

    out = {name: table(a) for name, a in acc.items()}
    print(f"\n  {'':<10s} {'kind':<11s} {'recall':>7s} {'precis':>7s} {'sign':>5s} {'|dgrad|':>8s} {'|dlvl|':>7s} "
          f"{'lag':>5s} {'matched':>8s} {'overstay':>9s}")
    for name, rows in out.items():
        for kd, r in rows.items():
            print(f"  {name:<10s} {kd:<11s} {100 * r['recall']:>6.0f}% {100 * r['precision']:>6.0f}% "
                  f"{100 * r['sign']:>4.0f}% {r['dgrad_med']:>7.0f}% {r['dlevel_med']:>6.1f}% "
                  f"{r['lag_med']:>5.0f} {100 * r['matched']:>7.0f}% {100 * r['overstay']:>8.0f}%")
    OUT.write_text(json.dumps(dict(what="constructions scored against the principal's hand-drawn lines, bar by bar",
                                   lines=LINES, score=out), indent=1))
    print(f"  written {OUT.relative_to(REPO)} ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
