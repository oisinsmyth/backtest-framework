"""D280 part 4 -- combine the things that ACTUALLY WORKED into one forecast.

    uv run python scripts/d280_combined_forecast.py

NOTHING HERE SCORES A CELL. Measurement, same standing as parts 1-3.

Parts 1-3 produced four survivors, and none of them is a directional signal on
its own. Put together they are not four findings, they are the four parts of a
DISTRIBUTION forecast for the next bar:

    PERSISTENCE ("tomorrow = today") beat every extrapolation in ~60
        comparisons                                   -> the CENTRE
    RANGE is predictable at corr +0.87 (volatility clusters, returns do not)
                                                      -> the WIDTH
    The overnight GAP is 51.5% of the body            -> WHERE IN THE DAY it lands
    Derivatives of the score flip the IC toward tradeable inside the qualifying
        set (v -0.00286, a -0.00388 against h's +0.00462)  -> the TILT

A point forecast was the wrong object. A cross-sectional book does not need to
know tomorrow's price; it needs to RANK. So the question is not "can we predict
the bar" but "does combining these produce a better RANKING than `hist_L`".

FOUR QUESTIONS, and A is the one that could invalidate the backtest itself
==========================================================================

A. WHERE DOES THE EDGE LIVE -- OVERNIGHT OR INTRADAY?
   The gap is 51.5% of the body, and a close-to-close backtest silently books
   both halves. Decomposed here:

       gap(t+1)      = open(t+1)  / close(t)   - 1
       intraday(t+1) = close(t+1) / open(t+1)  - 1

   This strategy holds overnight, so gap-borne edge IS capturable -- but if the
   whole IC sits in the gap it means the signal is about overnight repricing,
   not tradeable flow, and NO intraday stop, target or exit rule can ever touch
   it. That would close the entire exit-overlay branch for this construction in
   one measurement. If it sits intraday instead, the position could be taken at
   the open and the overnight risk dropped altogether.

B. DOES VOLATILITY NORMALISATION HELP? Two names with the same `hist_L` and
   three times the expected range are not equally attractive shorts, and D279
   ranked on the raw score, conflating signal strength with volatility. Range is
   predictable at 0.87, so the denominator is reliable. This is the most direct
   way the range finding can be put to work.

C. DOES A FIXED-WEIGHT COMBINATION BEAT ITS PARTS? Each component is
   cross-sectionally standardised WITHIN the bar, then summed with UNIT weights.
   No fitting -- weights are 1, so this cannot overfit and needs no train/test.
   If unit weights do not help, fitted weights are a much longer conversation.

D. IS THE GAP ITSELF FORECASTABLE cross-sectionally? corr(gap, body) = -0.0429
   pooled, which hints at mild overnight reversal. Measured properly here.

THE BAR, unchanged: D279's corrected decomposition puts the ranking at +0.203
gross Sharpe and the book at -0.432 gross. An IC near -0.004 buys roughly the
former. Reaching zero needs the IC roughly TRIPLED, to about -0.013. **A
combination that improves the IC from -0.005 to -0.007 is real and still does
not save the strategy**, and that must be said plainly when the numbers land.

A NOTE ON WHAT IS BEING CORRELATED. `gap` and `intraday` are built from RAW
OHLC and therefore exclude dividends, while `total_log_returns` includes them.
The two do not sum exactly to the total return and are not meant to -- the
decomposition is about WHEN the move happens, not about restating the P&L.
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


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


B = _load("d256", "run_book_single_names.py")
C = _load("d279", "run_concentrated_short.py")
P1 = _load("d280p1", "d280_forecast_precheck.py")
P3 = _load("d280p3", "d280_score_extrapolation.py")
RP = B.RP

OUT = REPO / "data" / "d280_combined_forecast.json"
SPLIT_DATE = P3.SPLIT_DATE
ic_series, report_row, d1 = P3.ic_series, P3.report, P3.d1


def zscore(x, live):
    """Cross-sectional z-score WITHIN each bar, over live names only.

    Standardising within the bar is what makes unit weights meaningful: without
    it, whichever component happens to have the largest raw scale would dominate
    the sum and the 'combination' would be that component in disguise."""
    m = live & np.isfinite(x)
    out = np.full_like(x, np.nan)
    for t in range(x.shape[1]):
        col = m[:, t]
        if col.sum() < P3.MIN_NAMES:
            continue
        v = x[col, t]
        sd = v.std()
        if sd > 0:
            out[col, t] = (v - v.mean()) / sd
    return out


def main() -> int:
    t0 = time.time()
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=C.FEE)
    md, hs, g_lo, g_hi, i_lo, atr, warm = B.signals_ragged(panel, cleaned, 0)
    live = panel.live
    g = P1.build_grids(panel, cleaned)
    O, H, L, Cl = g["open"], g["high"], g["low"], g["close"]
    dates = np.array(panel.dates)
    oos = live & (dates >= SPLIT_DATE)[None, :]
    print(f"loaded {time.time() - t0:.0f}s\n", flush=True)

    def nxt(x):
        out = np.full_like(x, np.nan)
        ok = live[:, 1:] & live[:, :-1]
        out[:, :-1] = np.where(ok, x[:, 1:], np.nan)
        return out

    total = nxt(np.expm1(panel.total_log_returns))
    gap = nxt(O) / Cl - 1.0
    intraday = nxt(Cl) / nxt(O) - 1.0

    # the qualifying set D279 actually ranked inside
    okm = ~(np.isnan(md) | np.isnan(hs)) & warm
    qual = oos & (-B.hold_book((hs < 0) & (md >= 0) & okm, warm) != 0.0)

    h = C.lag1(hs)                       # R9-lagged, as the fixed top_n uses it
    v, = (d1(h, live),)
    a = d1(v, live)
    rng = (H - L) / Cl                   # fractional range, cross-comparable
    rng_l = C.lag1(rng)                  # yesterday's range = the best predictor
    atr_l = C.lag1(atr)

    rows = {}

    # ---------------- A: where does the edge live? ----------------
    print("  A -- WHERE THE EDGE LIVES. Cross-sectional IC of the lagged score")
    print("       against each PART of the next bar. Negative = tradeable short.\n")
    print(f"  {'universe':>10s} {'target':>12s} {'mean IC':>9s} {'t':>7s} {'bars':>7s}")
    for uname, mask in (("ALL", oos), ("QUAL", qual)):
        for tname, tgt in (("total", total), ("gap", gap), ("intraday", intraday)):
            ics = ic_series(h, tgt, mask)
            if ics.size < 30:
                continue
            mu, t = ics.mean(), ics.mean() / (ics.std(ddof=1) / np.sqrt(ics.size))
            rows[f"A|{uname}|{tname}"] = {"mean_ic": float(mu), "t": float(t),
                                          "bars": int(ics.size)}
            print(f"  {uname:>10s} {tname:>12s} {mu:+9.5f} {t:+7.2f} {ics.size:7,d}",
                  flush=True)
    print()

    # ---------------- B: volatility normalisation ----------------
    print("  B -- VOLATILITY NORMALISATION. Does dividing the score by a")
    print("       predicted width improve the ranking? Target = total return.\n")
    print(f"  {'universe':>10s} {'score':>26s} {'mean IC':>9s} {'t':>7s}")
    safe = lambda d: np.where(np.isfinite(d) & (d > 0), d, np.nan)  # noqa: E731
    b_cands = {"h (baseline)": h,
               "h / lagged range": h / safe(rng_l),
               "h / ATR": h / safe(atr_l),
               "h / sqrt(lagged range)": h / np.sqrt(safe(rng_l))}
    for uname, mask in (("ALL", oos), ("QUAL", qual)):
        for nm, s in b_cands.items():
            ics = ic_series(s, total, mask)
            if ics.size < 30:
                continue
            mu, t = ics.mean(), ics.mean() / (ics.std(ddof=1) / np.sqrt(ics.size))
            rows[f"B|{uname}|{nm}"] = {"mean_ic": float(mu), "t": float(t)}
            print(f"  {uname:>10s} {nm:>26s} {mu:+9.5f} {t:+7.2f}", flush=True)
        print()

    # ---------------- C: the fixed-weight combination ----------------
    print("  C -- COMBINATION. Each part z-scored WITHIN the bar, unit weights,")
    print("       nothing fitted. Target = total return.\n")
    zh, zv, za = zscore(h, live), zscore(v, live), zscore(a, live)
    zr = zscore(rng_l, live)
    c_cands = {
        "zh": zh,
        "zh + zv": zh + zv,
        "zh + zv + za": zh + zv + za,
        "zh / lagged range": zscore(h / safe(rng_l), live),
        "(zh + zv + za) / range": zscore((zh + zv + za) / safe(rng_l), live),
        "zh + zv + za - zr": zh + zv + za - zr,
        "zh + zv + za + zr": zh + zv + za + zr,
    }
    print(f"  {'universe':>10s} {'score':>26s} {'mean IC':>9s} {'t':>7s} {'vs zh':>9s}")
    for uname, mask in (("ALL", oos), ("QUAL", qual)):
        base = None
        for nm, s in c_cands.items():
            ics = ic_series(s, total, mask)
            if ics.size < 30:
                continue
            mu, t = ics.mean(), ics.mean() / (ics.std(ddof=1) / np.sqrt(ics.size))
            if base is None:
                base = mu
            rows[f"C|{uname}|{nm}"] = {"mean_ic": float(mu), "t": float(t)}
            print(f"  {uname:>10s} {nm:>26s} {mu:+9.5f} {t:+7.2f} {mu - base:+9.5f}",
                  flush=True)
        print()

    # ---------------- D: is the gap itself forecastable? ----------------
    print("  D -- IS THE GAP FORECASTABLE cross-sectionally? Target = gap only.\n")
    print(f"  {'universe':>10s} {'score':>26s} {'mean IC':>9s} {'t':>7s}")
    ret_l = C.lag1(np.expm1(panel.total_log_returns))
    d_cands = {"h": h, "yesterday's return": ret_l,
               "lagged range": rng_l, "h / lagged range": h / safe(rng_l)}
    for uname, mask in (("ALL", oos), ("QUAL", qual)):
        for nm, s in d_cands.items():
            ics = ic_series(s, gap, mask)
            if ics.size < 30:
                continue
            mu, t = ics.mean(), ics.mean() / (ics.std(ddof=1) / np.sqrt(ics.size))
            rows[f"D|{uname}|{nm}"] = {"mean_ic": float(mu), "t": float(t)}
            print(f"  {uname:>10s} {nm:>26s} {mu:+9.5f} {t:+7.2f}", flush=True)
        print()

    json.dump({"purpose": ("combines the four surviving findings of D280 parts "
                           "1-3 into one cross-sectional ranking test; scores "
                           "no cell"),
               "split_date": SPLIT_DATE,
               "ic_needed_to_reach_zero_gross": -0.013,
               "results": rows, "elapsed_s": round(time.time() - t0, 1)},
              open(OUT, "w"), indent=1)
    print(f"wrote {OUT.relative_to(REPO)}   {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
