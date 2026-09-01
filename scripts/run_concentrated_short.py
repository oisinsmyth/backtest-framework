"""D279 -- the concentrated short on the dead-inclusive daily universe.
Pre-registered in
`docs/decisions/D279-the-concentrated-short-on-dead-inclusive-names.md`,
commit 0c94da3, BEFORE this file was written.

    uv run python scripts/run_concentrated_short.py

ONE CHANGE FROM D256: hold only the TOP N qualifying names at each bar, ranked
by the signal's own continuous score, instead of every name that qualifies.
D256 held 76.5% of live names at once and FINDINGS 9 identified that as the
defect -- an equal-weighted book over 1,580 names IS a diversified basket.

HURDLE C IS THE ONE THAT DECIDES IT. `random-N` holds N qualifying names chosen
AT RANDOM: same N, same count, same bars. If concentration alone explains the
result, the ranking carries nothing. D267 found strength is not
magnitude-calibrated and D278 watched five strength filters reverse sign, so the
burden is on the ranking to beat random selection at matched concentration.

Every constant is D256's, unvaried: 5 bp/side, borrow 3%/yr, rf 4%, PPY 252,
Impulse 34/9, k=3, window 252, age cap 63.
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
RP, U = B.RP, B.U

OUT = REPO / "data" / "d279_concentrated_summary.json"
N_LEVELS = (10, 25, 50)
N_SIMS, SEED = 300, 0
PPY, RF, BORROW, FEE = B.PPY, B.RF_ANNUAL, B.BORROW_ANNUAL, B.FEE_BPS


def lag1(a):
    """Shift a score grid one bar forward, exactly as `hold_book` shifts a mask.

    R9. THE FIRST VERSION OF `top_n` DID NOT DO THIS AND THE RESULT WAS ENTIRELY
    LOOK-AHEAD. `hold_book` lags the qualifying MASK (`p[:, 1:] = mask[:, :-1]`)
    and `pooled_returns` earns bar t's return on the position held at bar t, so
    the base book was aligned. But ranking with `score[:, t]` chose WHICH N
    qualifiers to hold using `hist_L` computed from the close of the very bar the
    position was about to be paid for.

    Measured, not argued: `corr(hist_L at t, return at t) = +0.0737`, against
    `corr(hist_L at t-1, return at t) = -0.0103`. Ranking ascending on the
    unlagged score selects names that had ALREADY fallen that bar. `top25` scored
    +2.250 Sharpe unlagged and -0.638 lagged; `top50` +1.865 and -0.659.

    The lag lives inside `top_n` rather than at the call site because three other
    modules call it and a convention that must be remembered is one that will be
    forgotten. Column 0 becomes NaN and ranks last -- there is no prior bar."""
    out = np.full_like(a, np.nan)
    out[:, 1:] = a[:, :-1]
    return out


def top_n(base, score, n, rng=None):
    """Keep only the N strongest qualifying names at each bar.

    `score` ASCENDING selects the strongest short -- most negative `hist_L`, or
    steepest `g_lo`. IT IS LAGGED ONE BAR HERE, unconditionally; see `lag1`. With
    `rng` supplied the N are drawn AT RANDOM from the qualifying set instead,
    which is hurdle C's control: same N, same count, same bars, no ranking."""
    out = np.zeros_like(base)
    score = lag1(score)
    n_sym, T = base.shape
    for t in range(T):
        q = np.flatnonzero(base[:, t] != 0.0)
        if q.size == 0:
            continue
        if q.size <= n:
            out[q, t] = base[q, t]
            continue
        if rng is None:
            s = score[q, t]
            s = np.where(np.isfinite(s), s, np.inf)     # unscored names rank last
            pick = q[np.argsort(s, kind="stable")[:n]]
        else:
            pick = rng.choice(q, size=n, replace=False)
        out[pick, t] = base[pick, t]
    return out


def breakeven_borrow(panel, pos, start, sc):
    """The borrow rate at which this cell's net return reaches zero.

    A property of the book, not of the 3%/yr assumed -- the same role
    `breakeven_bps` plays in D264, and the reason it is the primary cost
    statistic here: a book holding the ten weakest names holds the
    hard-to-borrow ones, and 3% general collateral is certainly wrong for it."""
    short_frac = sc["exposure_short"]
    if short_frac <= 0:
        return None
    yrs = (pos.shape[1] - start) / PPY
    paid = np.log1p(BORROW) * short_frac * yrs
    gross = np.log1p(sc["cagr"]) * yrs + paid
    return float(np.expm1(gross / (short_frac * yrs)))


def per_symbol_concentration(panel, pos, start):
    """Share of total P&L from the single best name. E' does not guard against a
    result carried by a handful of names, so D279 requires this beside every cell."""
    r = panel.total_log_returns[:, start:]
    pnl = (pos[:, start:] * r).sum(axis=1)
    tot = pnl.sum()
    if tot == 0:
        return None
    return float(np.max(pnl) / tot)


def main() -> int:
    t0 = time.time()
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=FEE)
    n, T = panel.closes.shape
    md, hs, g_lo, g_hi, i_lo, atr, warm = B.signals_ragged(panel, cleaned, 0)
    print(f"loaded + signals {time.time() - t0:.0f}s   {n} names x {T:,} bars", flush=True)

    ok = ~(np.isnan(md) | np.isnan(hs)) & warm
    sok = ~(np.isnan(g_lo) | np.isnan(g_hi) | np.isnan(atr)) & warm
    s1 = -B.hold_book((hs < 0) & (md >= 0) & ok, warm)
    s2 = -B.walk_state(panel, (g_lo < 0) & (g_hi < 0) & sok, warm, U.AGE_CAP)
    arms = {"S1_short": (s1, hs), "S2_short": (s2, g_lo)}

    eff = RP.effective_instruments(panel, 0)
    print(f"effective independent instruments over the panel: {eff:.2f}\n", flush=True)

    sc = lambda p: RP.score(panel, p, 0, ppy=PPY, rf_annual=RF, borrow_annual=BORROW)
    rng = np.random.default_rng(SEED)
    cells, books = {}, {}
    for arm, (base, score) in arms.items():
        books[f"{arm}|all"] = base
        for N in N_LEVELS:
            books[f"{arm}|top{N}"] = top_n(base, score, N)
            books[f"{arm}|rnd{N}"] = top_n(base, score, N, rng=rng)
    print(f"built {len(books)} books {time.time() - t0:.0f}s\n", flush=True)

    print(f"  {'cell':22s} {'expo':>6s} {'CAGR':>8s} {'SR':>7s} {'maxDD':>8s} "
          f"{'trades':>7s} {'min/sym':>7s} {'be borrow':>10s} {'top name':>9s}")
    for k, p in books.items():
        s = sc(p)
        s["breakeven_borrow"] = breakeven_borrow(panel, p, 0, s)
        s["top_name_share"] = per_symbol_concentration(panel, p, 0)
        s["conc"] = RP.concurrency(panel, p, 0, seed=SEED)
        cells[k] = s
        print(f"  {k:22s} {s['exposure_gross']:5.2%} {s['cagr']:+7.2%} "
              f"{s['excess_sharpe']:+7.3f} {s['max_drawdown']:7.2%} "
              f"{s['entries']:7,d} {s['min_entries_per_traded_symbol']:7d} "
              + (f"{s['breakeven_borrow']:9.1%}" if s['breakeven_borrow'] is not None else "        —")
              + (f" {s['top_name_share']:8.1%}" if s['top_name_share'] is not None else "        —"))

    print(f"\nrotation nulls, {N_SIMS} draws ...", flush=True)
    floor_draws = []
    for k, p in books.items():
        sh, mn = RP.rotation_null(panel, p, 0, n_sims=N_SIMS, seed=SEED, ppy=PPY,
                                  rf_annual=RF, borrow_annual=BORROW)
        cells[k]["sharpe_pct"] = float((sh < cells[k]["excess_sharpe"]).mean() * 100)
        cells[k]["money_pct"] = float((mn < cells[k]["total_return"]).mean() * 100)
        cells[k]["H"] = bool(cells[k]["sharpe_pct"] >= 95 and cells[k]["money_pct"] >= 95)
        cells[k]["V"] = bool(cells[k]["cagr"] > 0)
        floor_draws.append(sh)
        print(f"  {k:22s} {cells[k]['sharpe_pct']:5.1f}th / "
              f"{cells[k]['money_pct']:5.1f}th   {time.time() - t0:.0f}s", flush=True)
    floor = float(np.percentile(np.max(np.vstack(floor_draws), axis=0), 95))

    print(f"\nbest-of-{len(books)} floor: {floor:+.3f}\n")
    print(f"  {'cell':22s} {'CAGR':>8s} {'SR':>7s} {'vs random':>10s} "
          f"{'H':>3s} {'V':>3s} {'C':>3s} {'F':>3s} {'E-prime':>8s}  ALL")
    surv = []
    for k in books:
        arm, mode = k.split("|")
        c = cells[k]
        if mode.startswith("top"):
            r = cells[f"{arm}|rnd{mode[3:]}"]
            c["C"] = bool(c["excess_sharpe"] > r["excess_sharpe"]
                          and c["total_return"] > r["total_return"])
            vs = f"{c['excess_sharpe'] - r['excess_sharpe']:+.3f}"
        else:
            c["C"] = False
            vs = "—"
        c["F"] = bool(c["excess_sharpe"] > floor)
        c["Eprime"] = bool(eff >= 3.0 and c["entries"] >= 500)
        c["clears_all"] = bool(c["H"] and c["V"] and c["C"] and c["F"] and c["Eprime"])
        if c["clears_all"]:
            surv.append(k)
        y = lambda b: "YES" if b else "no"  # noqa: E731
        print(f"  {k:22s} {c['cagr']:+7.2%} {c['excess_sharpe']:+7.3f} {vs:>10s} "
              f"{y(c['H']):>3s} {y(c['V']):>3s} {y(c['C']):>3s} {y(c['F']):>3s} "
              f"{y(c['Eprime']):>8s}  {'** YES **' if c['clears_all'] else 'no'}")

    print(f"\n  SURVIVORS: {surv or 'NONE'}")
    json.dump({"floor": floor, "effective_instruments": eff, "n_levels": list(N_LEVELS),
               "borrow_charged": BORROW, "fee_bps": FEE,
               "cells": {k: {kk: vv for kk, vv in v.items() if kk != "conc"}
                         for k, v in cells.items()},
               "survivors": surv, "elapsed_s": round(time.time() - t0, 1)},
              open(OUT, "w"), indent=1)
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
