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


def ratchet_corrected(g, c, px_respect, h, widen):
    """The principal's ratchet, on ONE name's own bars, in log space.

    `px_respect` is the series the line must respect -- the LOW for a support line, the HIGH for a
    resistance line. `widen` is -1 for support (line sits below, pushed DOWN on a violation) and
    +1 for resistance.

    Returns (G, L, anchored, pushed) -- `pushed` is the log-distance the intercept was moved on
    each bar, which is zero wherever the trend was respected."""
    m = g.size
    G = np.full(m, np.nan)
    L = np.full(m, np.nan)
    anc = np.zeros(m, bool)
    push = np.zeros(m)
    Gh = np.nan
    Lh = np.nan
    for j in range(m):
        gj, cj, pj = g[j], c[j], px_respect[j]
        if not (np.isfinite(gj) and np.isfinite(cj)):
            continue
        if not np.isfinite(Gh) or abs(gj - Gh) > h:
            Gh, Lh = gj, gj * j + cj                 # RE-ANCHOR: gradient and ratchet both reset
            anc[j] = True
        else:
            Lh = Lh + Gh                             # advance at the HELD gradient
            if np.isfinite(pj):
                if widen < 0 and pj < Lh:            # support line broken from above
                    push[j] = Lh - pj
                    Lh = pj                          # pushed AWAY, exactly as far as needed
                elif widen > 0 and pj > Lh:          # resistance line broken from below
                    push[j] = pj - Lh
                    Lh = pj
        G[j] = Gh
        L[j] = Lh
    return G, L, anc, push


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
        fits = {}
        for sign, key in ((-1, "lo"), (+1, "hi")):
            idx = np.array([p.index for p in ps if p.sign == sign], dtype=int)
            lp = np.log([p.price for p in ps if p.sign == sign]) if idx.size else np.array([])
            fits[key] = UO.rolling_fit(m, idx, lp, UO.K)

        respect_lo = np.log(cl if a.on_close else lo)
        respect_hi = np.log(cl if a.on_close else hi)
        G_lo, L_lo, anc_lo, push_lo = ratchet_corrected(fits["lo"][0], fits["lo"][1],
                                                        respect_lo, H, -1)
        G_hi, L_hi, anc_hi, push_hi = ratchet_corrected(fits["hi"][0], fits["hi"][1],
                                                        respect_hi, H, +1)

        state = np.where((G_lo > DELTA) & (G_hi > DELTA), 1,
                         np.where((G_lo < -DELTA) & (G_hi < -DELTA), -1, 0))
        state[:UO.WINDOW] = 0

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
            state=state[sl].tolist(),
            n_anchor_lo=int(anc_lo[sl].sum()), n_anchor_hi=int(anc_hi[sl].sum()),
            n_push_lo=int((push_lo[sl] > 0).sum()), n_push_hi=int((push_hi[sl] > 0).sum()),
        ))
        c = out["charts"][-1]
        print(f"  {sym:>5s}  bars {start}-{start + w}  "
              f"state on {int((state[sl] != 0).sum()):>3d}/{w}  "
              f"anchors lo/hi {c['n_anchor_lo']}/{c['n_anchor_hi']}  "
              f"pushes lo/hi {c['n_push_lo']}/{c['n_push_hi']}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out))
    print(f"\n  wrote {OUT.relative_to(REPO)} ({OUT.stat().st_size / 1024:.0f} KB)")
    print("\nDIAGNOSTIC. Nothing was scored and nothing is admitted (R15).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
