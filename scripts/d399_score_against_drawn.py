"""Score a trendline construction against the principal's HAND-DRAWN lines.

    uv run python scripts/d399_score_against_drawn.py [--branch E] [--min-piv 3] [--h-annual 4]

GROUND TRUTH: `data/d399_drawn_ground_truth.json` -- seven lines the principal drew on GME bars
2429-2689 (2019-08-28 to 2020-09-08) with the whole window in view.

WHAT THIS IS AND IS NOT. The drawn lines have HINDSIGHT; every construction here is CAUSAL and
sees only bars through t. So this is an ORACLE benchmark in D394's sense: it bounds what any
causal rule could recover and says how close one gets. It CANNOT say a causal rule should have
got there, and a construction that falls short of it is not thereby refuted.

AND THE BENCHMARK OUTLIVES THE CONSTRUCTION. The principal's point, recorded because it governs
how this file should be used: a construction failing to reproduce these lines does not mean no
construction can. The ground truth is therefore stored on its own, in its own file, scored by a
runner that takes the construction as an argument -- not folded into D399's branches.

THREE THINGS ARE COMPARED, and they fail differently:
  COVERAGE  what share of the bars the human called trending does the construction also call
            trending? A construction can pick the right lines and still be silent most of the time.
  COUNT     how many segments does each side cut the series into? Too many is churn, too few is a
            fit straddling a regime change.
  SLOPE     where both are on, how far apart are the gradients, in log price per bar and
            annualised? This is the only one of the three that says the LINE is right.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
GT = REPO / "data" / "d399_drawn_ground_truth.json"
OUT = REPO / "data" / "d399_vs_drawn.json"
BARS_PER_YEAR = 252


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def human_mask(lines, n, kind):
    """Bars the human called trending on one side, the drawn slope, and the drawn LINE LEVEL.

    THE LEVEL MATTERS AND THE FIRST VERSION OF THIS FILE OMITTED IT. Branches B, C and D all take
    `rolling_fit`'s fixed-window gradient and differ ONLY in where the intercept sits, so a scorer
    that compares gradients alone reports them as identical -- which it did, and which is a flaw in
    the scorer rather than a fact about the constructions. `lvl` is the drawn line's price at every
    bar it spans, so `|log(fitted) - log(drawn)|` can separate them."""
    on = np.zeros(n, bool)
    g = np.full(n, np.nan)
    lvl = np.full(n, np.nan)
    for L in lines:
        if L["kind"] != kind:
            continue
        a, b = int(L["i0"]), int(L["i1"])
        gg = float(L["g_per_bar"])
        idx = np.arange(a, b + 1)
        on[a:b + 1] = True
        g[a:b + 1] = gg
        lvl[a:b + 1] = np.exp(np.log(float(L["p0"])) + gg * (idx - a))
    return on, g, lvl


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--branch", default="E", choices=["B", "C", "D", "E"])
    ap.add_argument("--min-piv", type=int, default=3)
    ap.add_argument("--h-annual", type=float, default=4.0)
    a = ap.parse_args()

    DR = _load("d399draw", "d399_draw_construction.py")
    UO = _load("d240_uptrend", "run_uptrend_onset.py")
    RP = _load("ragged_panel", "ragged_panel.py")
    from backtest_framework.research.structure import pivots as PV

    gt = json.loads(GT.read_text())
    sym, start, n = gt["symbol"], int(gt["start_bar"]), int(gt["n"])
    h = DR.h_of_annual(a.h_annual)

    panel, cleaned = RP.load_ragged(*DR.MINING, fee_bps=0.0, dividend_bound=True)
    bars = cleaned[sym]
    m = len(bars)
    hi = np.array([b.bar.high for b in bars], float)
    lo = np.array([b.bar.low for b in bars], float)
    ps = PV(bars, UO.K)

    res = dict(ground_truth=str(GT.relative_to(REPO)), symbol=sym, start_bar=start, n=n,
               branch=a.branch, min_piv=a.min_piv, h_annual_pct=a.h_annual, h=h,
               delta=DR.DELTA,
               note="ORACLE benchmark: the drawn lines have hindsight, the construction is causal. "
                    "Falling short of it does not refute the construction.",
               sides={})

    print(f"\n  {sym} bars {start}-{start + n}  {gt['first_date']} -> {gt['last_date']}")
    print(f"  branch {a.branch}, min_piv {a.min_piv}, h {a.h_annual:g}%/yr, delta {DR.DELTA:g}\n")

    for kind, sign, widen, px in (("support", -1, -1, lo), ("resistance", +1, +1, hi)):
        pidx = np.array([p.index for p in ps if p.sign == sign], dtype=int)
        ppx = np.log([p.price for p in ps if p.sign == sign]) if pidx.size else np.array([])
        if a.branch == "E":
            G, L, anc, win = DR.segment_windows(pidx, ppx, np.log(px), m, UO.K, h, widen,
                                                min_piv=a.min_piv, max_window=UO.WINDOW)
        else:
            # B, C and D all take rolling_fit's FIXED 252-bar gradient and differ only in the
            # intercept rule, so they share this preparation.
            g_fix, c_fix = UO.rolling_fit(m, pidx, ppx, UO.K)
            cnt, _sp = DR.pivot_support(m, pidx, UO.K, UO.WINDOW)
            ok = cnt >= a.min_piv
            if a.branch == "B":
                G, L, anc, _pu, _gv = DR.ratchet_corrected(g_fix, c_fix, np.log(px), h, widen, ok)
            else:
                RT = DR.ratchet_reset if a.branch == "D" else DR.ratchet_tight
                G, L, anc, _pu, _gv = RT(g_fix, np.log(px), h, widen, UO.WINDOW, ok)
            win = np.full(m, -1, int)
        sl = slice(start, start + n)
        Gw, Lw, ancw = G[sl], np.exp(L[sl]), anc[sl]
        hon, hg, hlvl = human_mask(gt["lines"], n, kind)
        mon = np.isfinite(Gw)

        both = hon & mon
        d = Gw[both] - hg[both]
        segs = int(ancw.sum())
        hsegs = sum(1 for L_ in gt["lines"] if L_["kind"] == kind)

        # DOES THE LINE START WHERE THE WINDOW STARTS? Measured, because it is the whole
        # question behind the recall gap: a window opens with no gradient and cannot draw a
        # line until it has earned min_piv pivots.
        lags = []
        if a.branch == "E":
            opens = np.flatnonzero(anc)
            for oi, o0 in enumerate(opens):
                o1 = opens[oi + 1] if oi + 1 < opens.size else m
                seg = np.flatnonzero(np.isfinite(G[o0:o1]))
                lags.append(int(seg[0]) if seg.size else int(o1 - o0))
        lag_med = float(np.median(lags)) if lags else None

        cell = dict(
            human_bars_on=int(hon.sum()), machine_bars_on=int(mon.sum()),
            human_share=round(float(hon.mean()), 4), machine_share=round(float(mon.mean()), 4),
            overlap_bars=int(both.sum()),
            recall=round(float((hon & mon).sum() / max(hon.sum(), 1)), 4),
            precision=round(float((hon & mon).sum() / max(mon.sum(), 1)), 4),
            human_segments=hsegs, machine_segments=segs,
            window_open_to_first_line_median=lag_med,
            window_open_to_first_line=lags or None,
            slope_abs_err_median=(round(float(np.median(np.abs(d))), 6) if d.size else None),
            slope_abs_err_p90=(round(float(np.quantile(np.abs(d), .9)), 6) if d.size else None),
            sign_agreement=(round(float((np.sign(Gw[both]) == np.sign(hg[both])).mean()), 4)
                            if d.size else None),
            # the measure that separates B, C and D: how far the fitted line sits from the drawn
            # one, in log price, at bars where both exist. 0.05 is a line 5% away from the drawn one.
            level_gap_median=(round(float(np.median(np.abs(np.log(Lw[lvok]) - np.log(hlvl[lvok])))), 5)
                              if (lvok := both & np.isfinite(Lw) & np.isfinite(hlvl)).any() else None),
            level_gap_p90=(round(float(np.quantile(np.abs(np.log(Lw[lvok]) - np.log(hlvl[lvok])), .9)), 5)
                           if lvok.any() else None),
            level_bars=int(lvok.sum()),
            median_machine_ann=(round(float(np.expm1(BARS_PER_YEAR * np.median(Gw[both]))), 4)
                                if d.size else None),
            median_human_ann=(round(float(np.expm1(BARS_PER_YEAR * np.median(hg[both]))), 4)
                              if d.size else None))
        res["sides"][kind] = cell

        print(f"  {kind.upper()}")
        print(f"    human   {cell['human_bars_on']:>4d}/{n} bars on ({100*cell['human_share']:.0f}%), "
              f"{hsegs} lines")
        print(f"    machine {cell['machine_bars_on']:>4d}/{n} bars on ({100*cell['machine_share']:.0f}%), "
              f"{segs} windows")
        if lag_med is not None:
            print(f"    the line does NOT start at the window: median {lag_med:.0f} bars from a "
                  f"window opening to its first drawn point")
        print(f"    overlap {cell['overlap_bars']:>4d} bars -- recall {100*cell['recall']:.0f}% "
              f"of what the human drew, precision {100*cell['precision']:.0f}%")
        if d.size:
            print(f"    slope error where both are on: median {cell['slope_abs_err_median']:.2e}/bar "
                  f"(p90 {cell['slope_abs_err_p90']:.2e}), sign agrees "
                  f"{100*cell['sign_agreement']:.0f}%")
            print(f"    annualised, median: machine {100*cell['median_machine_ann']:+.0f}% vs "
                  f"human {100*cell['median_human_ann']:+.0f}%")
        if cell["level_gap_median"] is not None:
            print(f"    LINE POSITION: median {100*cell['level_gap_median']:.1f}% away from the "
                  f"drawn line (p90 {100*cell['level_gap_p90']:.1f}%), over {cell['level_bars']} bars")
        print()

    OUT.write_text(json.dumps(res, indent=1))
    print(f"  [P] {OUT.relative_to(REPO)} written")
    print("\n  ORACLE benchmark. The drawn lines had the whole window in view and the construction")
    print("  did not; a shortfall here bounds what is recoverable, it does not refute anything.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
