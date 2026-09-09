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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--on-close", action="store_true",
                    help="respect the CLOSE instead of the wick, for comparison")
    ap.add_argument("--bars", type=int, default=260)
    a = ap.parse_args()

    from backtest_framework.research.structure import pivots as PV
    UO = _load("d240_uptrend", "run_uptrend_onset.py")
    RP = _load("ragged_panel", "ragged_panel.py")

    panel, cleaned = RP.load_ragged(*MINING, fee_bps=0.0, dividend_bound=True)
    pos = {s: i for i, s in enumerate(panel.symbols)}

    # names chosen to SHOW the mechanic, not to flatter it: a clean trender, a violent one,
    # a mean-reverter and a decliner. All are in the 48 that have 15-minute bars.
    WANT = ["MSFT", "GME", "INTC", "F", "WYNN", "DVN"]
    out = {"delta": DELTA, "h": H, "respect": "close" if a.on_close else "wick",
           "min_piv": MIN_PIV, "min_run": MIN_RUN,
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
        G_lo, L_lo, anc_lo, push_lo, gov_lo = ratchet_corrected(
            fits["lo"][0], fits["lo"][1], respect_lo, H, -1, ok_lo)
        G_hi, L_hi, anc_hi, push_hi, gov_hi = ratchet_corrected(
            fits["hi"][0], fits["hi"][1], respect_hi, H, +1, ok_hi)

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
