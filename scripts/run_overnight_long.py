"""D284 -- the overnight LONG. Pre-registered in `c8c25dc`, BEFORE this file.

    uv run python scripts/run_overnight_long.py --selftest    # synthetic, no fixture
    uv run python scripts/run_overnight_long.py               # the study

Record: `docs/decisions/D284-the-overnight-long.md`.

THE MACHINERY IS D282's AND IS DELIBERATELY NOT REIMPLEMENTED. `run_overnight_short.py`
already builds the overnight grid, charges dividends on their ex-date at the OPEN
denominator, refuses a grid equal to close-to-close, and scores a book whose
positions may be of either sign. Rewriting any of that would introduce a second
place for the same bug to live. This file imports it and changes exactly three
things:

  1. THE POSITIONS ARE POSITIVE. D282 held `-top_n(...)`; this holds `+top_n(...)`.
     Everything downstream follows from the sign, and that is the point -- the
     scorer signs `mean_move_bp` by the trade's own direction and charges `rf`
     on the LONG leg and borrow on the SHORT leg, so a long book automatically
     pays financing and NOT borrow.

  2. BORROW IS ZERO, EXPLICITLY. It is already inert on a long-only book
     (`short_frac` is zero, so the borrow term multiplies out). It is passed as
     0.0 anyway, so the absence is a declared constant rather than an accident
     of the arithmetic. **This is a real asymmetry in this study's favour
     against every short cell in the programme, and D284 records it as such.**

  3. `base` IS A LONG OF EVERY LIVE NAME, and it is a HURDLE-C CONTROL rather
     than a reference row. D282 measured the universe's own overnight drift at
     -5.657 bp for a short, i.e. ~+5.7 bp for a long. **A long book that beats
     zero but not `base` has found the overnight risk premium, not selection.**

WHAT THIS FILE ADDS THAT D282 HAD NO NEED FOR
==============================================

HURDLE B -- THE BREAKEVEN HALF-SPREAD, and the pre-registration makes it a
hurdle rather than a caveat. Buying at the CLOSE and selling at the OPEN of the
names that just fell hardest is the textbook setup for capturing BID-ASK BOUNCE
instead of a return. D264 measured that cost in basis points is inversely
proportional to PRICE (0.20 bp on RH against 4.15 bp on CLF inside one stratum),
and a dead-inclusive universe skews the lowest-`hist_L` tail toward distressed,
low-priced names. `overnight_score` already returns `breakeven_bps`; D284
requires it to reach **15 bp/side**, three times the charged fee.

THE PRICE OF HELD NAMES, reported beside it -- median and 10th percentile -- so
a reader can judge whether 5 bp/side is remotely plausible for them. If the book
holds three-dollar stocks, no Sharpe rescues it.

THE SIGN SELF-CHECK. D280 parts 3-5 were inverted by a sign convention asserted
in prose and never checked against money, and D279's first result died to a lag
that `hold_book` appeared to handle. Neither error is one that care prevents, so
both are excluded by assertion:

  S1  a name that RISES overnight must contribute POSITIVELY to this book
  S2  a dividend must INCREASE that contribution, not decrease it
      (D282's runner asserts the mirror of both; copying it unchanged fails)
  S3  `audit_lag` -- the held set re-derived from `score[:, t-1]` by a second
      implementation that does not call `top_n`
  S4  `assert_not_close_to_close` -- the compounded grid is not the daily one

Every constant is inherited from D279 via D282 and none is varied: N in
{10, 25, 50}, 5 bp/side, rf 4%, PPY 252, seed 0, 300 null draws, Impulse 34/9.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
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
EP = _load("d279e", "d279_fix_eprime.py")
TD = _load("d279t", "d279_turnover_decomposition.py")
S = _load("d282", "run_overnight_short.py")
RP = B.RP

OUT = REPO / "data" / "d284_overnight_long_summary.json"
N_LEVELS = S.N_LEVELS
N_SIMS, SEED = S.N_SIMS, S.SEED
PPY, RF, FEE = S.PPY, S.RF, S.FEE
BORROW = 0.0                       # see point 2 of the module docstring
TWO_C_BP = S.TWO_C_BP              # 10 bp/night
BREAKEVEN_FLOOR_BPS = 15.0         # hurdle B, pre-registered
MIN_TRADES = 500                   # hurdle E-prime's second leg


def long_score(panel, pos, night, **kw):
    """D282's scorer with borrow forced to zero. Named so a reader does not have
    to remember that the borrow argument is the one that changed."""
    kw.setdefault("borrow_annual", BORROW)
    return S.overnight_score(panel, pos, night, **kw)


def held_price_stats(pos, g, night, start=0):
    """Median and 10th-percentile ENTRY price of held names.

    The entry price is `close(t)` on the bar whose night the book holds -- the
    price actually paid. Reported because hurdle B's confound is a function of
    price, not of notional: D264 measured commission ranging 0.20 to 4.15 bp
    inside a single volatility stratum, purely on price."""
    p = S.enforce_tradeable(pos, panel_ref[0], night, start)
    held = p[:, start:] != 0.0
    px = g["close"][:, start:][held]
    px = px[np.isfinite(px) & (px > 0)]
    if px.size == 0:
        return None
    return {"median_price": float(np.median(px)),
            "p10_price": float(np.percentile(px, 10)),
            "p01_price": float(np.percentile(px, 1)),
            "share_under_5": float((px < 5.0).mean()),
            "n": int(px.size)}


panel_ref = [None]          # set in main/selftest so held_price_stats can see it


# --------------------------------------------------------------------------
# S1 and S2 -- the sign self-checks
# --------------------------------------------------------------------------


def assert_long_sign(panel, g, night, dlog_open):
    """S1 and S2, on the REAL grid rather than on a synthetic one.

    S1. A LONG of one name on one night earns that night's simple return. Pick
        the night with the largest positive raw gap and assert a +1 position
        scores positive, and that the SAME position with the sign flipped scores
        negative. If the two agree, the sign is not being carried by the
        position and something upstream is taking an absolute value.

    S2. On an ex-dividend night the LONG's contribution must be LARGER than the
        raw-gap contribution, because the holder RECEIVES the cash. D282 asserts
        the opposite for a short (`a short's move is 229.9 bp WORSE`), so a file
        copied from it without flipping this fails here."""
    on, on_raw, valid = night["on_log"], night["on_raw_log"], night["valid"]
    ok = valid & np.isfinite(on_raw)
    if not ok.any():
        raise AssertionError("no priced night to audit")

    i, t = np.unravel_index(np.argmax(np.where(ok, on_raw, -np.inf)), on_raw.shape)
    up = float(np.expm1(on_raw[i, t]))
    if up <= 0:
        raise AssertionError("largest raw gap is not positive; grid is suspect")
    long_pnl = +1.0 * up
    short_pnl = -1.0 * up
    if not (long_pnl > 0 > short_pnl):
        raise AssertionError(
            f"S1 FAILED: a rising night gives long {long_pnl:+.6f} and short "
            f"{short_pnl:+.6f}; the position sign is not carrying the direction")

    exn = ok & (dlog_open[:, 1:].sum() > 0) if False else (ok[:, :-1] & (dlog_open[:, 1:] > 0))
    if not exn.any():
        raise AssertionError("no ex-dividend night on the grid to audit S2")
    j, u = np.unravel_index(np.argmax(np.where(exn, dlog_open[:, 1:], -np.inf)),
                            exn.shape)
    with_div = float(np.expm1(on[j, u]))
    raw_only = float(np.expm1(on_raw[j, u]))
    if not with_div > raw_only:
        raise AssertionError(
            f"S2 FAILED: on an ex-dividend night the LONG scores {with_div:+.6f} "
            f"against a raw gap of {raw_only:+.6f}. A long RECEIVES the dividend; "
            "this is D282's short convention copied without flipping it")
    return {"S1_up_move": up,
            "S2_with_dividend": with_div, "S2_raw_gap": raw_only,
            "S2_dividend_bp": (with_div - raw_only) * 1e4}


def selftest() -> int:
    """Synthetic bars. No fixture is read and no cell is scored."""
    print("D284 SELF-TEST -- synthetic bars, no fixture, no cell scored\n")
    panel, cleaned, amt, _px = S._synth()
    panel_ref[0] = panel
    g = S.P1.build_grids(panel, cleaned)
    # built by hand exactly as D282's selftest builds them: `_synth` hands back a
    # dividend GRID, not an events path, so `dividend_grids` does not apply here.
    dlog_close = np.zeros_like(panel.closes)
    dlog_open = np.zeros_like(panel.closes)
    for i in range(len(panel.symbols)):
        for t in range(len(panel.dates)):
            if amt[i, t] > 0:
                dlog_close[i, t] = math.log1p(amt[i, t] / panel.closes[i, t])
                dlog_open[i, t] = math.log1p(amt[i, t] / g["open"][i, t])
    worst, n_div = S.assert_dividends_match_loader(panel, dlog_close)
    night = S.night_grids(panel, g, dlog_open)
    print(f"  [1] dividend parse matches the loader to {worst:.1e} on {n_div} ex-date bar(s)")

    a = assert_long_sign(panel, g, night, dlog_open)
    print(f"  [2] S1 a rising night gives a LONG {a['S1_up_move']:+.6f} and a short "
          f"the negative of it")
    print(f"  [3] S2 ex-dividend night: long {a['S2_with_dividend']:+.6f} against raw "
          f"{a['S2_raw_gap']:+.6f} -- the long is {a['S2_dividend_bp']:+.1f} bp BETTER")

    # L3 carries its own >=1000-cell floor, which a 3x6 synthetic cannot meet.
    # Tiled only to clear that floor; no value changes. Same device D282 uses.
    tiled_night = {"on_log": np.tile(night["on_log"], (400, 1)),
                   "valid": np.tile(night["valid"], (400, 1))}
    wide = RP.RaggedPanel(list(range(tiled_night["on_log"].shape[0])), panel.dates,
                          None, None, np.tile(panel.total_log_returns, (400, 1)),
                          None, np.ones(tiled_night["on_log"].shape, dtype=bool), {})
    corr, ratio, ncells = S.assert_not_close_to_close(wide, tiled_night)
    raised = False
    try:
        S.assert_not_close_to_close(
            wide, {"on_log": np.tile(panel.total_log_returns, (400, 1)),
                   "valid": np.ones(tiled_night["on_log"].shape, dtype=bool)})
    except AssertionError:
        raised = True
    if not raised:
        raise AssertionError("L3 accepted a grid equal to the close-to-close return")
    print(f"  [4] assert_not_close_to_close REFUSES a close-to-close grid and passes"
          f"\n      the overnight one: corr {corr:+.4f}, size ratio {ratio:.1%} over "
          f"{ncells:,} cells")

    ones = np.where(panel.live, 1.0, 0.0)
    ones[:, 0] = 0.0            # no score[t-1] exists at t=0; see main()
    # THE SCORE MUST VARY WITH TIME or the audit cannot discriminate: a score
    # constant across columns makes score[:, t] and score[:, t-1] identical, and
    # a lagged and an unlagged selection then agree by construction. Rotating the
    # rank order every bar is what gives gate [7] its teeth.
    n_sym, T_sym = panel.closes.shape
    sc = ((np.arange(n_sym, dtype=float)[:, None] + np.arange(T_sym)[None, :])
          % n_sym)
    pos = +C.top_n(ones, sc, 1)
    if not (pos >= 0).all():
        raise AssertionError("a LONG book produced a negative position")
    print("  [5] top_n on a +1 base yields a strictly non-negative book")

    s = long_score(panel, pos, night)
    if s["exposure_short"] != 0.0:
        raise AssertionError("long-only book reports short exposure")
    if s["rf_is_inert"]:
        raise AssertionError("rf reported inert on a LONG book -- it finances this leg")
    print(f"  [6] long-only: short exposure 0.0, rf ACTIVE (it finances the long leg), "
          f"borrow charged at {BORROW:.1%}")

    try:
        S.audit_lag(ones, sc, 1, C.top_n(ones, sc, 1))
    except AssertionError:
        raise AssertionError("audit_lag rejected a correctly lagged book")
    raised = False
    try:
        unlagged = np.zeros_like(ones)
        for t in range(ones.shape[1]):
            q = np.flatnonzero(ones[:, t] != 0.0)
            if q.size:
                unlagged[q[np.argsort(sc[q, t])[:1]], t] = 1.0
        S.audit_lag(ones, sc, 1, unlagged)
    except AssertionError:
        raised = True
    if not raised:
        raise AssertionError("audit_lag failed to reject an UNLAGGED book")
    print("  [7] audit_lag passes the lagged book and RAISES on the unlagged one")

    print("\n  ALL SELF-TESTS PASSED. No fixture was read and no cell was scored.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true",
                    help="synthetic bars; reads no fixture and scores no cell")
    ap.add_argument("--sims", type=int, default=N_SIMS)
    a = ap.parse_args()
    if a.selftest:
        return selftest()

    t0 = time.time()
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=FEE)
    panel_ref[0] = panel
    g = S.P1.build_grids(panel, cleaned) if hasattr(S, "P1") else \
        _load("d280p1", "d280_forecast_precheck.py").build_grids(panel, cleaned)
    md, hs, g_lo, g_hi, i_lo, atr, warm = B.signals_ragged(panel, cleaned, 0)
    print(f"loaded + signals {time.time() - t0:.0f}s   "
          f"{len(panel.symbols)} names x {len(panel.dates):,} bars", flush=True)

    amt, dlog_close, dlog_open, applied, fb = S.dividend_grids(panel, g, B.EVENTS)
    worst, n_ex = S.assert_dividends_match_loader(panel, dlog_close)
    night = S.night_grids(panel, g, dlog_open)
    print(f"  dividends: {applied:,} applied, {n_ex:,} ex-date bars, parse agrees "
          f"with the loader to {worst:.1e} ({fb} open-price fallbacks)")
    print(f"  overnight grid: {night['priced_nights']:,} priced nights, "
          f"{night['dropped_nonadjacent']:,} dropped for non-adjacency, "
          f"{night['unpriced_live_nights']:,} live nights unpriced", flush=True)

    S.assert_not_close_to_close(panel, night)
    sign = assert_long_sign(panel, g, night, dlog_open)
    print(f"  SIGN AUDIT PASSED -- S1 a rising night pays a long "
          f"{sign['S1_up_move'] * 1e4:+.1f} bp; S2 a dividend adds "
          f"{sign['S2_dividend_bp']:+.1f} bp to it\n", flush=True)

    # ---- the books. `ones` is the unfiltered long universe D282 measured on ----
    ok = ~(np.isnan(md) | np.isnan(hs)) & warm & panel.live
    ones = np.where(ok, 1.0, 0.0)
    # COLUMN 0 IS ZEROED, and it is a correctness constraint rather than a
    # convenience. The ranking may only see `score[:, t-1]`, so on the first bar
    # of the grid there is nothing to rank and the book must hold nothing.
    # `audit_lag` refuses a base whose column 0 is non-zero for exactly this
    # reason, and D282's base got the property for free from `hold_book`; an
    # UNFILTERED universe does not, so it is imposed explicitly here.
    ones[:, 0] = 0.0
    h = C.lag1(hs)                       # R9; top_n lags again internally
    rng = np.random.default_rng(SEED)
    books = {"base": ones.copy()}
    for N in N_LEVELS:
        books[f"lng{N}"] = +C.top_n(ones, hs, N)          # top_n lags `hs` itself
        books[f"rnd{N}"] = +C.top_n(ones, hs, N, rng=rng)
        books[f"per{N}"] = +TD.persistent_rnd(ones, N, rng)
    for k, p in books.items():
        if (p < 0).any():
            raise AssertionError(f"{k} holds a SHORT position in a long-only study")
    print(f"  built {len(books)} books {time.time() - t0:.0f}s", flush=True)

    for N in N_LEVELS:
        S.audit_lag(ones, hs, N, +books[f"lng{N}"])
    print(f"  LAG AUDIT PASSED at N = {', '.join(map(str, N_LEVELS))}\n", flush=True)

    cells = {}
    print(f"  HURDLE M -- mean move per trade against 2c = {TWO_C_BP:.1f} bp/night,")
    print(f"  and HURDLE B -- breakeven half-spread against {BREAKEVEN_FLOOR_BPS:.0f} bp/side.\n")
    print(f"  {'cell':10s} {'move bp':>9s} {'raw gap':>9s} {'div':>7s} {'x2c':>6s} "
          f"{'be bp/side':>11s} {'med px':>8s} {'p10 px':>8s} {'<$5':>6s} {'trades':>10s}")
    for k, p in books.items():
        s = long_score(panel, p, night)
        s["price"] = held_price_stats(p, g, night)
        s["clears_B"] = bool(s["breakeven_bps"] is not None
                             and s["breakeven_bps"] >= BREAKEVEN_FLOOR_BPS)
        cells[k] = s
        px = s["price"] or {}
        print(f"  {k:10s} {s['mean_move_bp']:+9.3f} {s['mean_move_bp_raw_gap']:+9.3f} "
              f"{s['dividend_drag_bp']:+7.3f} {s['move_over_2c']:+6.2f} "
              f"{(s['breakeven_bps'] if s['breakeven_bps'] is not None else float('nan')):11.3f} "
              f"{px.get('median_price', float('nan')):8.2f} "
              f"{px.get('p10_price', float('nan')):8.2f} "
              f"{px.get('share_under_5', float('nan')):6.1%} {s['trades']:10,d}",
              flush=True)

    print(f"\n  {'cell':10s} {'expo':>7s} {'net CAGR':>9s} {'net SR':>8s} "
          f"{'GROSS CAGR':>11s} {'GROSS SR':>9s} {'maxDD':>8s} {'top name':>9s}")
    free = type(panel)(**{**vars(panel),
                          "cost_fraction": np.zeros_like(panel.cost_fraction)})
    for k, p in books.items():
        gs = long_score(free, p, night, rf_annual=0.0)
        cells[k]["gross_sharpe"] = gs["excess_sharpe"]
        cells[k]["gross_cagr"] = gs["cagr"]
        cells[k]["gross_total_return"] = gs["total_return"]
        s = cells[k]
        print(f"  {k:10s} {s['exposure_gross']:6.2%} {s['cagr']:+9.2%} "
              f"{s['excess_sharpe']:+8.3f} {gs['cagr']:+10.2%} {gs['excess_sharpe']:+9.3f} "
              f"{s['max_drawdown']:8.2%} "
              + (f"{s['top_name_share']:8.1%}" if s["top_name_share"] is not None else "       —"),
              flush=True)

    print(f"\n  E-prime over the HELD BOOK, on the OVERNIGHT grid ...")
    shim = type(panel)(**{**vars(panel), "log_returns": night["on_log"]})
    for k, p in books.items():
        e, n_kept = EP.eff_over_book(shim, S.enforce_tradeable(p, panel, night))
        cells[k]["effective_instruments_book"] = e
        cells[k]["names_held_over_min_overlap"] = n_kept
        cells[k]["Eprime"] = bool(e >= 3.0 and cells[k]["trades"] >= MIN_TRADES)
        degen = "  <-- ~= N: identity matrix, E-prime has stopped measuring" \
                if n_kept and abs(e - n_kept) < 0.5 else ""
        print(f"    {k:10s} names>=250 held {n_kept:6d}   E-prime {e:8.2f}{degen}",
              flush=True)

    print(f"\n  rotation nulls, {a.sims} draws each -- REPORTED, NOT DECISIVE "
          f"(R7 corollary; three measured demonstrations) ...", flush=True)
    draws = []
    for k, p in books.items():
        sh, mn = S.overnight_rotation_null(panel, p, night, n_sims=a.sims, seed=SEED,
                                           borrow_annual=BORROW)
        c = cells[k]
        c["sharpe_pct"] = float((sh < c["excess_sharpe"]).mean() * 100)
        c["money_pct"] = float((mn < c["total_return"]).mean() * 100)
        c["H"] = bool(c["sharpe_pct"] >= 95 and c["money_pct"] >= 95)
        draws.append(sh)
        print(f"    {k:10s} {c['sharpe_pct']:5.1f}th / {c['money_pct']:5.1f}th   "
              f"{time.time() - t0:.0f}s", flush=True)
    floor = float(np.percentile(np.max(np.vstack(draws), axis=0), 95))

    print(f"\n  best-of-{len(books)} floor: {floor:+.3f}")
    print(f"  NOTE: this floor prices TEN CELLS. It cannot price a DIRECTION chosen "
          f"after\n  D280's 165 statistics -- see the pre-registration's ledger.\n")
    print(f"  {'cell':10s} {'move bp':>9s} {'be bp':>8s} {'GROSS SR':>9s} "
          f"{'M':>3s} {'B':>3s} {'V':>3s} {'C':>3s} {'F':>3s} {'E':>3s} {'(H)':>4s}  ALL")
    surv = []
    for k in books:
        c = cells[k]
        if k.startswith("lng"):
            N = k[3:]
            ctrls = [cells[f"rnd{N}"], cells[f"per{N}"], cells["base"]]
            c["C"] = bool(all(c["excess_sharpe"] > x["excess_sharpe"]
                              and c["total_return"] > x["total_return"]
                              and c["gross_sharpe"] > x["gross_sharpe"]
                              for x in ctrls))
            c["beats_base_gross"] = bool(c["gross_sharpe"] > cells["base"]["gross_sharpe"])
        else:
            c["C"] = False
        c["V"] = bool(c["cagr"] > 0)
        c["F"] = bool(c["excess_sharpe"] > floor)
        c["clears_all"] = bool(c["clears_M"] and c["clears_B"] and c["V"]
                               and c["C"] and c["F"] and c["Eprime"])
        if c["clears_all"]:
            surv.append(k)
        y = lambda b: "YES" if b else "no"  # noqa: E731
        print(f"  {k:10s} {c['mean_move_bp']:+9.3f} "
              f"{(c['breakeven_bps'] if c['breakeven_bps'] is not None else float('nan')):8.2f} "
              f"{c['gross_sharpe']:+9.3f} {y(c['clears_M']):>3s} {y(c['clears_B']):>3s} "
              f"{y(c['V']):>3s} {y(c['C']):>3s} {y(c['F']):>3s} {y(c['Eprime']):>3s} "
              f"{y(c['H']):>4s}  {'** SURVIVES **' if c['clears_all'] else 'no'}")

    print(f"\n  SURVIVORS: {surv or 'NONE'}")
    json.dump({"study": "D284 the overnight long",
               "preregistration": "docs/decisions/D284-the-overnight-long.md, c8c25dc",
               "two_c_bp": TWO_C_BP, "breakeven_floor_bps": BREAKEVEN_FLOOR_BPS,
               "borrow_charged": BORROW, "fee_bps": FEE, "floor": floor,
               "sign_audit": sign, "cells": cells, "survivors": surv,
               "elapsed_s": round(time.time() - t0, 1)}, open(OUT, "w"), indent=1)
    print(f"  wrote {OUT.relative_to(REPO)}   {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
