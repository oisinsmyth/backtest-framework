"""D399 -- draw the construction on real candles. A DIAGNOSTIC, not a measurement.

    uv run python scripts/d399_draw_construction.py            writes temp/d399_chart_data.json

It scores nothing, proposes nothing and admits nothing. Its whole purpose is to put the object on
a chart so the principal can confirm the mechanic before anything is measured on it -- the lesson
of `look-at-the-object-before-reporting-it`.

THE CORRECTED RATCHET (the principal, 2026-09-09), and it is NOT what the first D399 runner built:

    hold G. each bar:
        if |g_fresh - G| > h:   RE-ANCHOR: G := g_fresh, L := the fresh fit's level, ratchet resets
        else:                   L := L + G            the line advances at the HELD gradient
                                if price VIOLATES L:  push L away from price just far enough
                                                      that the trend is respected again

The intercept therefore moves ONLY on a violation, and only by the amount of the violation. If the
trend is respected, the intercept does not move at all. `run_d399_ratcheted_line.ratchet` instead
took `min(L + G, fresh_fit)` every bar -- it tracked the refit and never looked at price, which is
why its line was dragged onto price and "touched" 264,501 times.

WHICH PRICE "RESPECTS" THE LINE. On candles the natural reading is the WICK: a rising support line
is respected while the LOW stays above it, a falling resistance line while the HIGH stays below.
That is what is drawn. It is a choice, it is drawn so it can be seen, and `--on-close` shows the
alternative.
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


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


FIX = REPO / "data" / "fixtures"
OUT = REPO / "temp" / "d399_chart_data.json"
MINING = (FIX / "us_shorts_daily_raw.csv.gz", FIX / "us_shorts_daily_raw_events.json")
DELTA = 1e-3
H = DELTA

# THE PRINCIPAL'S RULE, 2026-09-09: "A trend has to be based on at least 5 bars with at least the
# minimum gradient. In those spaces we just don't trend."
#
# TWO CONDITIONS, and the measurement says only the second can bite.
MIN_PIV = 5     # the fit must rest on >= 5 pivots.  MEASURED NON-BINDING: over 47,220 fits on the
                # six charted names the minimum is 14 pivots, median 23, spanning a median 238
                # bars. It is implemented and asserted anyway so the rule is in the code and its
                # bite is reported rather than assumed.
MIN_RUN = 5     # the state must hold for >= 5 CONSECUTIVE bars before it counts as a trend.
                # This is what bites, and it is the literal reading of "5 bars with at least the
                # minimum gradient".
#
# WHAT THE PRINCIPAL IS ACTUALLY SEEING, and neither condition fixes it: after a push the line's
# POSITION is set to exactly one bar's wick. The SLOPE rests on ~23 pivots; the INTERCEPT rests on
# a single low. `gov` below records which bar currently pins the line, so it can be drawn.


def pivot_support(n_bars, idx, k, window):
    """(count, span) of the pivots inside the window `rolling_fit` uses at each bar.

    A second implementation of the same window -- prefix counting by searchsorted rather than
    rolling_fit's cumulative sums -- so `[NPIV]` compares two derivations, not one against itself.
    `idx` must be ascending: pivots() sorts by (confirmed_at, index) and confirmed_at = index + k
    for a single sign, so it is, and the caller asserts it."""
    t = np.arange(n_bars)
    hiw = np.clip(t - k + 1, 0, n_bars)
    low = np.clip(t - window, 0, n_bars)
    if idx.size == 0:
        return np.zeros(n_bars, int), np.zeros(n_bars, int)
    a = np.searchsorted(idx, low, "left")
    b = np.searchsorted(idx, hiw, "left")
    cnt = b - a
    lastp = idx[np.clip(b - 1, 0, idx.size - 1)]
    firstp = idx[np.clip(a, 0, idx.size - 1)]
    return cnt, np.where(cnt > 0, lastp - firstp, 0)


def enforce_min_run(state, min_run):
    """Zero any run of a non-zero state shorter than `min_run`. 'In those spaces we just don't
    trend' -- so a two-bar flicker of a steep gradient is not a trend and is dropped whole."""
    out = state.copy()
    i, m = 0, state.size
    while i < m:
        if out[i] == 0:
            i += 1
            continue
        j = i
        while j + 1 < m and out[j + 1] == out[i]:
            j += 1
        if (j - i + 1) < min_run:
            out[i:j + 1] = 0
        i = j + 1
    return out


def ratchet_reset(g, px_respect, h, widen, window, ok=None):
    """BRANCH D -- C's tightening, but the window RESETS at every re-anchor.

    WHAT BRANCH C LOST. The principal's rule was 'update the gradient AND RESET THE RATCHET'.
    Branch B had that reset; Branch C replaced the accumulator with a rolling minimum over a fixed
    trailing `window`, and in doing so threw the reset away. So a re-anchor at bar j -- a declared
    change of trend -- still let a low from up to 252 bars earlier, belonging to the OLD gradient,
    pin the NEW line. The old regime kept voting after it had been retired.

    THE FIX: the offset minimises only over bars SINCE the last re-anchor.

        L_j = min over i in [anchor, j] of  (px[i] - G*(i-j))          support
        L_j = max over the same                                        resistance

    still capped at `window` so a gradient that never re-anchors cannot look back forever. On the
    re-anchor bar itself the window is one bar, so the line starts pinned exactly there and the
    new trend is measured from its own beginning. No new parameter: the window boundary is the
    construction's own event."""
    m = g.size
    G = np.full(m, np.nan)
    L = np.full(m, np.nan)
    anc = np.zeros(m, bool)
    push = np.zeros(m)
    gov = np.full(m, -1, int)
    Gh = np.nan
    anchor = 0
    for j in range(m):
        gj = g[j]
        usable = (ok is None or ok[j]) and np.isfinite(gj)
        if usable and (not np.isfinite(Gh) or abs(gj - Gh) > h):
            Gh = gj
            anc[j] = True
            anchor = j                                # THE RESET: history before j stops counting
        if not np.isfinite(Gh):
            continue
        lo_i = max(anchor, j - window + 1)
        idx = np.arange(lo_i, j + 1)
        det = px_respect[idx] - Gh * (idx - j)
        fin = np.isfinite(det)
        if not fin.any():
            continue
        det = det[fin]
        pick = int(np.argmin(det)) if widen < 0 else int(np.argmax(det))
        Lh = det[pick]
        gv = int(idx[fin][pick])
        if j > 0 and np.isfinite(L[j - 1]) and not anc[j]:
            moved = Lh - (L[j - 1] + Gh)
            if (widen < 0 and moved < 0) or (widen > 0 and moved > 0):
                push[j] = abs(moved)
        G[j], L[j], gov[j] = Gh, Lh, gv
    return G, L, anc, push, gov


def ratchet_tight(g, px_respect, h, widen, window, ok=None):
    """BRANCH C -- the gradient is still sticky; the INTERCEPT is the TIGHTEST offset that keeps
    the trailing window respected.

    WHY BRANCH B NEEDED THIS. Its intercept could only loosen. MSFT ran 233 bars with no re-anchor
    and no push, so the line simply advanced at G and ended ~30% below the lows, drifting further
    every bar; GME's resistance was dragged onto a spike high and could never come back down. Both
    are the same defect: `push away until respected` fires in one direction only, and nothing ever
    tightens the line again.

    THE FIX, and it introduces NO new parameter. The line at bar i is `L_j + G*(i-j)`. Support is
    respected over the window iff `L_j + G*(i-j) <= low[i]` for every i in it, so the TIGHTEST
    admissible offset is

        L_j = min over i in (j-window, j] of  (low[i] - G*(i-j))

    which is a rolling minimum of the DETRENDED wick. It still pushes away the instant price
    violates the line -- bar j is in its own window -- but it also tightens as old bars age out.
    `window` is S2's fit window, reused rather than chosen.

    Returns (G, L, anchored, pushed, gov) with the same meanings as `ratchet_corrected`; `pushed`
    is now the amount the line moved AWAY on bars where the current bar set the offset."""
    m = g.size
    G = np.full(m, np.nan)
    L = np.full(m, np.nan)
    anc = np.zeros(m, bool)
    push = np.zeros(m)
    gov = np.full(m, -1, int)
    Gh = np.nan
    for j in range(m):
        gj = g[j]
        usable = (ok is None or ok[j]) and np.isfinite(gj)
        if usable and (not np.isfinite(Gh) or abs(gj - Gh) > h):
            Gh = gj                                   # RE-ANCHOR the gradient
            anc[j] = True
        if not np.isfinite(Gh):
            continue
        lo_i = max(0, j - window + 1)
        idx = np.arange(lo_i, j + 1)
        det = px_respect[idx] - Gh * (idx - j)        # detrend onto bar j's coordinate
        fin = np.isfinite(det)
        if not fin.any():
            continue
        det = det[fin]
        pick = int(np.argmin(det)) if widen < 0 else int(np.argmax(det))
        Lh = det[pick]
        gv = int(idx[fin][pick])
        if j > 0 and np.isfinite(L[j - 1]):
            moved = Lh - (L[j - 1] + Gh)              # against where it would have advanced to
            if (widen < 0 and moved < 0) or (widen > 0 and moved > 0):
                push[j] = abs(moved)
        G[j], L[j], gov[j] = Gh, Lh, gv
    return G, L, anc, push, gov


def ratchet_corrected(g, c, px_respect, h, widen, ok=None):
    """The principal's ratchet, on ONE name's own bars, in log space.

    `px_respect` is the series the line must respect -- the LOW for a support line, the HIGH for a
    resistance line. `widen` is -1 for support (line sits below, pushed DOWN on a violation) and
    +1 for resistance.

    `ok` gates which bars carry a usable fit (the >= MIN_PIV pivot rule); a bar without one cannot
    re-anchor, and the held line simply advances through it.

    Returns (G, L, anchored, pushed, gov) -- `pushed` is the log-distance the intercept was moved
    on each bar, zero wherever the trend was respected, and `gov` is the index of the bar that
    currently PINS the line (its last push, or its last re-anchor). `gov` is the answer to "what
    is this line based on": the slope rests on every pivot in the window, the position on one bar."""
    m = g.size
    G = np.full(m, np.nan)
    L = np.full(m, np.nan)
    anc = np.zeros(m, bool)
    push = np.zeros(m)
    gov = np.full(m, -1, int)
    Gh = np.nan
    Lh = np.nan
    gv = -1
    for j in range(m):
        gj, cj, pj = g[j], c[j], px_respect[j]
        if ok is not None and not ok[j]:
            if np.isfinite(Gh):                    # hold the line through an unsupported fit
                Lh = Lh + Gh
                G[j], L[j], gov[j] = Gh, Lh, gv
            continue
        if not (np.isfinite(gj) and np.isfinite(cj)):
            continue
        if not np.isfinite(Gh) or abs(gj - Gh) > h:
            Gh, Lh = gj, gj * j + cj                 # RE-ANCHOR: gradient and ratchet both reset
            anc[j] = True
            gv = j
        else:
            Lh = Lh + Gh                             # advance at the HELD gradient
            if np.isfinite(pj):
                if widen < 0 and pj < Lh:            # support line broken from above
                    push[j] = Lh - pj
                    Lh = pj                          # pushed AWAY, exactly as far as needed
                    gv = j
                elif widen > 0 and pj > Lh:          # resistance line broken from below
                    push[j] = pj - Lh
                    Lh = pj
                    gv = j
        G[j] = Gh
        L[j] = Lh
        gov[j] = gv
    return G, L, anc, push, gov


def h_of_annual(pct):
    """The per-bar log-slope dead band equivalent to `pct` percent of annual trend drift.

    h is a gradient in log price per BAR; a reader thinks in percent a year. 252 bars a year, so
    h = ln(1 + pct/100) / 252. The two dials are separate and must not be conflated:
    DELTA filters (is this a trend at all), h updates (has the slope changed enough to re-fit)."""
    return float(np.log1p(pct / 100.0) / 252.0)


def sweep_h(sym, pcts, a, UO, PV, RP, panel, cleaned):
    """One symbol, one window, the SAME data -- redrawn at each gradient update band."""
    out = []
    i = panel.symbols.index(sym)
    bars = cleaned[sym]
    m = len(bars)
    o = np.array([b.bar.open for b in bars], float)
    hi = np.array([b.bar.high for b in bars], float)
    lo = np.array([b.bar.low for b in bars], float)
    cl = np.array([b.bar.close for b in bars], float)
    dates = [str(b.timestamp)[:10] for b in bars]

    ps = PV(bars, UO.K)
    fits, sup = {}, {}
    for sign, key in ((-1, "lo"), (+1, "hi")):
        idx = np.array([p.index for p in ps if p.sign == sign], dtype=int)
        lp = np.log([p.price for p in ps if p.sign == sign]) if idx.size else np.array([])
        fits[key] = UO.rolling_fit(m, idx, lp, UO.K)
        sup[key] = pivot_support(m, idx, UO.K, UO.WINDOW)
    ok_lo = sup["lo"][0] >= MIN_PIV
    ok_hi = sup["hi"][0] >= MIN_PIV
    r_lo = np.log(cl if a.on_close else lo)
    r_hi = np.log(cl if a.on_close else hi)

    start, w = a.start, min(a.bars, m)
    sl = slice(start, start + w)
    for pct in pcts:
        hh = h_of_annual(pct)
        RT = ratchet_reset if a.branch == "D" else ratchet_tight
        G_lo, L_lo, anc_lo, push_lo, gov_lo = RT(fits["lo"][0], r_lo, hh, -1, UO.WINDOW, ok_lo)
        G_hi, L_hi, anc_hi, push_hi, gov_hi = RT(fits["hi"][0], r_hi, hh, +1, UO.WINDOW, ok_hi)
        st = np.where((G_lo > DELTA) & (G_hi > DELTA), 1,
                      np.where((G_lo < -DELTA) & (G_hi < -DELTA), -1, 0))
        st[:UO.WINDOW] = 0
        st[~(ok_lo & ok_hi)] = 0
        st = enforce_min_run(st, MIN_RUN)
        out.append(dict(
            symbol=sym, label=f"{pct:g}% / yr", h_annual_pct=pct, h=hh,
            start=start, n=w, dates=dates[sl],
            open=o[sl].tolist(), high=hi[sl].tolist(), low=lo[sl].tolist(), close=cl[sl].tolist(),
            line_lo=np.exp(L_lo[sl]).tolist(), line_hi=np.exp(L_hi[sl]).tolist(),
            anchor_lo=anc_lo[sl].tolist(), anchor_hi=anc_hi[sl].tolist(),
            push_lo=push_lo[sl].tolist(), push_hi=push_hi[sl].tolist(),
            state=st[sl].tolist(),
            gov_lo=(gov_lo[sl] - start).tolist(), gov_hi=(gov_hi[sl] - start).tolist(),
            n_anchor_lo=int(anc_lo[sl].sum()), n_anchor_hi=int(anc_hi[sl].sum()),
            n_push_lo=int((push_lo[sl] > 0).sum()), n_push_hi=int((push_hi[sl] > 0).sum()),
            min_npiv=int(min(sup["lo"][0][sl].min(), sup["hi"][0][sl].min())),
            dropped_by_min_run=0))
        c = out[-1]
        print(f"  h = {pct:>2g}%/yr ({hh:.3e})  re-anchors {c['n_anchor_lo']:>3d}/{c['n_anchor_hi']:>3d}  "
              f"moves {c['n_push_lo']:>3d}/{c['n_push_hi']:>3d}  "
              f"state on {int((st[sl] != 0).sum()):>3d}/{w}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweep-h", metavar="SYMBOL",
                    help="redraw ONE symbol at a range of gradient update bands")
    ap.add_argument("--start", type=int, default=1541, help="window start bar for --sweep-h")
    ap.add_argument("--on-close", action="store_true",
                    help="respect the CLOSE instead of the wick, for comparison")
    ap.add_argument("--bars", type=int, default=260)
    ap.add_argument("--branch", default="D", choices=["B", "C", "D"],
                    help="B = one-way ratchet (drifts); C = tightest offset over a fixed trailing "
                         "window; D = C but the window RESETS at every re-anchor")
    ap.add_argument("--h-annual", type=float, default=4.0,
                    help="gradient update band, in %% of annual trend drift")
    a = ap.parse_args()
    a.h = h_of_annual(a.h_annual)

    from backtest_framework.research.structure import pivots as PV
    UO = _load("d240_uptrend", "run_uptrend_onset.py")
    RP = _load("ragged_panel", "ragged_panel.py")

    panel, cleaned = RP.load_ragged(*MINING, fee_bps=0.0, dividend_bound=True)
    pos = {s: i for i, s in enumerate(panel.symbols)}

    if a.sweep_h:
        pcts = [1, 2, 3, 4, 5, 6, 7, 8]
        print(f"  {a.sweep_h}: DELTA held at {DELTA:g} (the FILTER); sweeping h (the UPDATE band)\n")
        charts = sweep_h(a.sweep_h, pcts, a, UO, PV, RP, panel, cleaned)
        res = {"delta": DELTA, "respect": "close" if a.on_close else "wick",
               "min_piv": MIN_PIV, "min_run": MIN_RUN, "branch": "C", "sweep": "h",
               "note": "DIAGNOSTIC ONLY -- one symbol, one window, one dataset, redrawn at eight "
                       "gradient update bands. DELTA is unchanged throughout.",
               "charts": charts}
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(res))
        print(f"\n  wrote {OUT.relative_to(REPO)} ({OUT.stat().st_size / 1024:.0f} KB)")
        print("\nDIAGNOSTIC. Nothing was scored and nothing is admitted (R15).")
        return 0

    # names chosen to SHOW the mechanic, not to flatter it: a clean trender, a violent one,
    # a mean-reverter and a decliner. All are in the 48 that have 15-minute bars.
    WANT = ["MSFT", "GME", "INTC", "F", "WYNN", "DVN"]
    out = {"delta": DELTA, "h": H, "respect": "close" if a.on_close else "wick",
           "min_piv": MIN_PIV, "min_run": MIN_RUN, "branch": a.branch,
           "h": a.h, "h_annual_pct": a.h_annual,
           "note": "DIAGNOSTIC ONLY -- no score, no hurdle, no null. D399's corrected ratchet.",
           "charts": []}

    for sym in WANT:
        if sym not in pos:
            print(f"  {sym}: not in the fixture, skipped")
            continue
        i = pos[sym]
        bars = cleaned[sym]
        m = len(bars)
        o = np.array([b.bar.open for b in bars], float)
        hi = np.array([b.bar.high for b in bars], float)
        lo = np.array([b.bar.low for b in bars], float)
        cl = np.array([b.bar.close for b in bars], float)
        dates = [b.timestamp if isinstance(b.timestamp, str) else str(b.timestamp) for b in bars]

        ps = PV(bars, UO.K)
        fits, sup = {}, {}
        for sign, key in ((-1, "lo"), (+1, "hi")):
            idx = np.array([p.index for p in ps if p.sign == sign], dtype=int)
            assert idx.size == 0 or np.all(np.diff(idx) > 0), f"{sym}: pivot indices not ascending"
            lp = np.log([p.price for p in ps if p.sign == sign]) if idx.size else np.array([])
            fits[key] = UO.rolling_fit(m, idx, lp, UO.K)
            sup[key] = pivot_support(m, idx, UO.K, UO.WINDOW)
            # [NPIV] two derivations of the same window must agree on which bars have a fit
            got = np.isfinite(fits[key][0])
            want = sup[key][0] >= UO.MIN_PIVOTS
            assert np.array_equal(got[UO.WINDOW:], want[UO.WINDOW:]), \
                f"{sym}/{key}: pivot_support disagrees with rolling_fit about which fits exist"

        ok_lo = sup["lo"][0] >= MIN_PIV
        ok_hi = sup["hi"][0] >= MIN_PIV
        respect_lo = np.log(cl if a.on_close else lo)
        respect_hi = np.log(cl if a.on_close else hi)
        if a.branch == "B":
            G_lo, L_lo, anc_lo, push_lo, gov_lo = ratchet_corrected(
                fits["lo"][0], fits["lo"][1], respect_lo, H, -1, ok_lo)
            G_hi, L_hi, anc_hi, push_hi, gov_hi = ratchet_corrected(
                fits["hi"][0], fits["hi"][1], respect_hi, H, +1, ok_hi)
        else:
            RT = ratchet_reset if a.branch == "D" else ratchet_tight
            G_lo, L_lo, anc_lo, push_lo, gov_lo = RT(
                fits["lo"][0], respect_lo, a.h, -1, UO.WINDOW, ok_lo)
            G_hi, L_hi, anc_hi, push_hi, gov_hi = RT(
                fits["hi"][0], respect_hi, a.h, +1, UO.WINDOW, ok_hi)

        raw_state = np.where((G_lo > DELTA) & (G_hi > DELTA), 1,
                             np.where((G_lo < -DELTA) & (G_hi < -DELTA), -1, 0))
        raw_state[:UO.WINDOW] = 0
        raw_state[~(ok_lo & ok_hi)] = 0            # the >= MIN_PIV rule
        state = enforce_min_run(raw_state, MIN_RUN)     # the >= MIN_RUN rule
        dropped = int((raw_state != 0).sum() - (state != 0).sum())
        thin = int(((sup["lo"][0] < MIN_PIV) | (sup["hi"][0] < MIN_PIV))[UO.WINDOW:].sum())

        # pick the window with the most state-on bars, so the chart shows the object working
        w = min(a.bars, m)
        on = (state != 0).astype(int)
        if on.sum() == 0:
            start = max(0, m - w)
        else:
            cs = np.concatenate(([0], np.cumsum(on)))
            best = np.argmax(cs[w:] - cs[:-w]) if m > w else 0
            start = int(best)
        sl = slice(start, start + w)

        out["charts"].append(dict(
            symbol=sym, start=start, n=w,
            dates=dates[sl], open=o[sl].tolist(), high=hi[sl].tolist(),
            low=lo[sl].tolist(), close=cl[sl].tolist(),
            line_lo=np.exp(L_lo[sl]).tolist(), line_hi=np.exp(L_hi[sl]).tolist(),
            g_lo=G_lo[sl].tolist(), g_hi=G_hi[sl].tolist(),
            anchor_lo=anc_lo[sl].tolist(), anchor_hi=anc_hi[sl].tolist(),
            push_lo=push_lo[sl].tolist(), push_hi=push_hi[sl].tolist(),
            state=state[sl].tolist(), raw_state=raw_state[sl].tolist(),
            gov_lo=(gov_lo[sl] - start).tolist(), gov_hi=(gov_hi[sl] - start).tolist(),
            npiv_lo=sup["lo"][0][sl].tolist(), npiv_hi=sup["hi"][0][sl].tolist(),
            n_anchor_lo=int(anc_lo[sl].sum()), n_anchor_hi=int(anc_hi[sl].sum()),
            n_push_lo=int((push_lo[sl] > 0).sum()), n_push_hi=int((push_hi[sl] > 0).sum()),
            min_npiv=int(min(sup["lo"][0][sl].min(), sup["hi"][0][sl].min())),
            dropped_by_min_run=int((raw_state[sl] != 0).sum() - (state[sl] != 0).sum()),
        ))
        c = out["charts"][-1]
        print(f"  {sym:>5s}  bars {start}-{start + w}  "
              f"state {int((state[sl] != 0).sum()):>3d}/{w} "
              f"(was {int((raw_state[sl] != 0).sum()):>3d}, MIN_RUN dropped "
              f"{c['dropped_by_min_run']:>3d})  "
              f"anchors {c['n_anchor_lo']}/{c['n_anchor_hi']}  "
              f"pushes {c['n_push_lo']}/{c['n_push_hi']}  "
              f"min pivots {c['min_npiv']}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out))
    print(f"\n  wrote {OUT.relative_to(REPO)} ({OUT.stat().st_size / 1024:.0f} KB)")
    print("\nDIAGNOSTIC. Nothing was scored and nothing is admitted (R15).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
