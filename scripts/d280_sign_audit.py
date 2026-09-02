"""D280 SIGN AUDIT -- settle the direction with money, not with a correlation sign.

    uv run python scripts/d280_sign_audit.py

NOTHING HERE SCORES A CELL. This exists because I asserted a sign convention in
parts 3-5 and D281 asserts the opposite, and a sign error would invert every
conclusion drawn from those parts.

WHAT I WROTE, in `d280_score_extrapolation.py` and repeated in parts 4 and 5:

    "a SHORT ranks ASCENDING, so a NEGATIVE IC is the tradeable direction --
     low score, low forward return."

**That gloss is self-contradictory.** A negative correlation means low score goes
with HIGH forward return. Shorting the lowest-scoring names would then be
shorting the names that RISE. If the gloss is wrong, then part 4's headline --
"a real, correctly-signed overnight edge" -- is backwards, and the overnight gap
IC of -0.01531 means the ascending short LOSES overnight rather than wins.

D281 reached the opposite reading independently: it reports that the
qualifying-set IC of +0.00462 is the one correctly signed for this arm, which is
why D279's filtered ranking ADDED +0.203 gross while D281's unfiltered ranking
SUBTRACTED -0.116.

CORRELATION SIGNS ARE EASY TO TALK YOURSELF INTO EITHER WAY. This file does not
reason about them at all. It takes the ACTUAL BOOK -- the N lowest lagged
`hist_L` among live names, which is exactly what `top_n` selects -- and reports
what a SHORT of those names EARNS, in basis points, against the cross-sectional
mean of the same bar.

    short P&L = -(selected mean return - universe mean return)

Positive = the short makes money. Negative = it loses. Reported separately for
the overnight gap, the intraday session and the total, so the part-4
decomposition is re-stated in money rather than in correlation.

No costs are charged. This is the GROSS cross-sectional edge, which is the
quantity parts 3-5 were about, and it is directly comparable to D265's bar of
`mean move per trade >= 2c` (10 bp at 5 bp/side).
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

OUT = REPO / "data" / "d280_sign_audit.json"
SPLIT_DATE = P3.SPLIT_DATE
N_LEVELS = (10, 25, 50)


def main() -> int:
    t0 = time.time()
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=C.FEE)
    md, hs, g_lo, g_hi, i_lo, atr, warm = B.signals_ragged(panel, cleaned, 0)
    live = panel.live
    g = P1.build_grids(panel, cleaned)
    O, Cl, H, L = g["open"], g["close"], g["high"], g["low"]
    dates = np.array(panel.dates)
    oos = live & (dates >= SPLIT_DATE)[None, :]
    print(f"loaded {time.time() - t0:.0f}s\n", flush=True)

    def nxt(x):
        out = np.full_like(x, np.nan)
        ok = live[:, 1:] & live[:, :-1]
        out[:, :-1] = np.where(ok, x[:, 1:], np.nan)
        return out

    targets = {"overnight gap": nxt(O) / Cl - 1.0,
               "intraday session": nxt(Cl) / nxt(O) - 1.0,
               "total (close-to-close)": nxt(np.expm1(panel.total_log_returns))}

    # TWO ALIGNMENTS, BOTH LEGITIMATE, AND THE FIRST VERSION OF THIS FILE MIXED
    # THEM. Found by the D283 agent, verified here rather than taken on trust.
    #
    #   STALE   hs[t-1] -> the quantity at column t.  D282's convention: `top_n`
    #           lags internally, so the book entering at close(t) ranks on the
    #           PREVIOUS close. Conservative by one full session.
    #   FRESH   hs[t]   -> the quantity at column t.  Also honest for an
    #           OVERNIGHT book and NOT look-ahead: `hist_L` at close(t) is known
    #           at close(t), which is exactly when the position is entered.
    #
    # For the overnight gap both are defensible and STALE is what D282 scored.
    # For the CLOSE-TO-CLOSE target STALE is over-lagged by one bar, because a
    # close-to-close position taken at t earns return[t], not return[t+1] --
    # that was the defect. Both are computed and printed; neither is asserted.
    h_stale = C.lag1(hs)
    h_fresh = hs
    rng_l = C.lag1((H - L) / Cl)
    safe = np.where(np.isfinite(rng_l) & (rng_l > 0), rng_l, np.nan)

    okm = ~(np.isnan(md) | np.isnan(hs)) & warm
    qual = oos & (-B.hold_book((hs < 0) & (md >= 0) & okm, warm) != 0.0)

    scores = {"h (STALE hs[t-1])": h_stale,
              "h (FRESH hs[t])": h_fresh,
              "h / lagged range": h_stale / safe}
    rows = {}

    print("  A SHORT of the N LOWEST-scoring names, against the cross-sectional")
    print("  mean of the same bar. POSITIVE bp = THE SHORT MAKES MONEY.")
    print("  No costs charged. D265's bar for one round trip is 2c = 10 bp.\n")
    print(f"  {'universe':>6s} {'score':>20s} {'N':>4s} {'window':>24s} "
          f"{'short bp':>10s} {'t':>7s} {'bars':>7s}")

    for uname, umask in (("ALL", oos), ("QUAL", qual)):
        for sname, s in scores.items():
            for N in N_LEVELS:
                for tname, tgt in targets.items():
                    per_bar = []
                    for t in range(s.shape[1]):
                        m = umask[:, t] & np.isfinite(s[:, t]) & np.isfinite(tgt[:, t])
                        k = int(m.sum())
                        if k < max(P3.MIN_NAMES, N + 5):
                            continue
                        sc, rt = s[m, t], tgt[m, t]
                        pick = np.argsort(sc, kind="stable")[:N]   # the N LOWEST
                        # short P&L = -(selected - universe), in the same bar
                        per_bar.append(-(rt[pick].mean() - rt.mean()))
                    if len(per_bar) < 30:
                        continue
                    v = np.array(per_bar)
                    mu = v.mean()
                    tt = mu / (v.std(ddof=1) / np.sqrt(v.size))
                    rows[f"{uname}|{sname}|N{N}|{tname}"] = {
                        "short_bp": float(mu * 1e4), "t": float(tt),
                        "bars": int(v.size), "pct_positive": float((v > 0).mean())}
                    print(f"  {uname:>6s} {sname:>20s} {N:4d} {tname:>24s} "
                          f"{mu * 1e4:+10.2f} {tt:+7.2f} {v.size:7,d}", flush=True)
                print()

    print("  READING. The overnight and intraday rows should sum to roughly the")
    print("  total row; they will not sum exactly because the gap and session are")
    print("  built from RAW OHLC while the total carries dividends.\n")
    print("  WHICHEVER WINDOW IS POSITIVE IS THE ONE THE SHORT SHOULD BE IN, and")
    print("  the number to hold against 10 bp is that window's `short bp`.")

    json.dump({"purpose": ("settles the sign of D280 parts 3-5 by measuring what "
                           "the actual short book earns; scores no cell"),
               "split_date": SPLIT_DATE, "cost_bar_bp": 10.0,
               "results": rows, "elapsed_s": round(time.time() - t0, 1)},
              open(OUT, "w"), indent=1)
    print(f"\nwrote {OUT.relative_to(REPO)}   {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
