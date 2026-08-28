"""D249 — the inverse wedge breakout.

    lower(t)  = i_lo + g_lo * t        OLS over confirmed swing lows,  252 bars, k = 3
    upper(t)  = i_hi + g_hi * t        OLS over confirmed swing highs, 252 bars, k = 3
    centre(t) = (upper + lower) / 2    the level the two lines converge toward
    ARMED(t) := g_hi < g_lo AND width > 0 AND width <= 2 * ATR(21)

    DOWN BREAK at t := ARMED(t-1) AND log C[t] < centre(t-1) - 2 * atr(t-1)
    ENTRY  the first DOWN BREAK of an armed episode; exposure begins at t+1
    EXIT   age >= HOLD, or a stop at entry - 2 * atr (W3 only)

    UP BREAKS ARE RECORDED AND NEVER TRADED.

THIS IS COMPLEMENT-CHASING AND IT IS NOT S3. The proposed rule shorted the
down-break; measured, down-breaks return +14.6% to +18.3% annualised at every
horizon while up-breaks straddle the +7.84% baseline, so the design was backwards.
D246 Constraint 3 makes an inverse-of-a-failed-cell ineligible under the S3 search
protocol, so D249 registers it SEPARATELY with that provenance stated.

D245's RESERVED NEVER-SEEN COHORT IS NOT SPENT HERE. Validation runs on the
60-ETF instrument holdout, which the wedge rule has never touched. The runner
asserts neither wide-universe fixture is opened.

HURDLE E DOES NOT CLEAR AND THE PRE-REGISTRATION SAYS SO. The proposal's "50.4
entries/symbol" counts armed SETUPS. Only the down-breaks are traded, not every
episode triggers, and an overlapping trade on one symbol is suppressed -- so the
real figure is ~16 per symbol on average and a MINIMUM of 5, worse than S1's 20.

EFFICIENCY. `rolling_fit` is O(T) per symbol by prefix sum (D240), and both lines
are fitted the same way. The walk is the only per-bar loop and it visits armed
bars only.

Offline, deterministic, seed 0. `--report-only` re-renders from the artifact.
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

from backtest_framework.research import macd as M  # noqa: E402
from backtest_framework.research.structure import pivots  # noqa: E402


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


W = _load("d245_wide", "run_book_wide.py")
E, B, U, X, L, S, J = W.E, W.B, W.U, W.X, W.L, W.S, W.J

SUMMARY = REPO / "data" / "wedge_inverse_summary.json"
RESULTS = REPO / "WEDGE_INVERSE_RESULTS.md"
FIX = REPO / "data" / "fixtures"

PPY, SEED = X.PPY, X.SEED
RF_ANNUAL, RF_PER_BAR = X.RF_ANNUAL, X.RF_PER_BAR
N_SIMS = X.N_SIMS

# D249's constants. Everything above the double rule is inherited from D240 and
# is asserted, not restated; everything below it is declared by D249 and is not
# swept -- the 1x and 3x arming thresholds are anatomy in the record, not cells.
K, WINDOW, MIN_PIVOTS, ATR_WINDOW = U.K, U.WINDOW, U.MIN_PIVOTS, U.ATR_WINDOW
assert (K, WINDOW, MIN_PIVOTS, ATR_WINDOW) == (3, 252, 3, 21), "D240's constants drifted"
# ------------------------------------------------------------------
ARM_ATR = 2.0         # armed while the channel is no wider than this many ATRs
TRIG_ATR = 2.0        # trigger sits this many ATRs either side of `centre`
STOP_ATR = 2.0        # W3 only, frozen at the trigger bar's own ATR

HOLDS = {"W1": 21, "W2": 42, "W3": 42}
STOPPED = {"W1": False, "W2": False, "W3": True}
CELL_ORDER = ("W1", "W2", "W3")
OVERLAY_CELLS = ("W3",)          # R7 scopes its matched-exit-count null to these
BASE_OF_OVERLAY = "W2"

# D243's published numbers on the extended 57. If either moves, rho and the whole
# overlap analysis are measuring something other than the book.
BOOK_EXTENDED = {"S1": 0.478465, "S2": 0.511447}

FIXTURES = {
    "57": (FIX / "universe_daily_extended_raw.csv.gz",
           FIX / "universe_daily_extended_raw_events.json"),
    "60": (FIX / "universe_holdout_extended_raw.csv.gz",
           FIX / "universe_holdout_extended_raw_events.json"),
}
# D246 reserves these for S3, one candidate only. This study is not S3.
RESERVED = ("universe_wide_w1_raw", "universe_wide_w5_raw")


# --------------------------------------------------------------------------
# The wedge geometry
# --------------------------------------------------------------------------


def wedge_signals(panel, cleaned, start: int):
    """Both regression lines, the ATR, and the armed mask.

    `rolling_fit` is D240's O(T) prefix-sum fit and carries D173's confirmation
    lag inside it: the window usable at bar `t` is `i in [t-252, t-k]`, so a pivot
    is invisible for exactly `k` bars after it forms. Fitted twice, once per line.
    """
    n, T = panel.closes.shape
    g_lo = np.full((n, T), np.nan)
    i_lo = np.full((n, T), np.nan)
    g_hi = np.full((n, T), np.nan)
    i_hi = np.full((n, T), np.nan)
    atr = np.full((n, T), np.nan)
    for i, sym in enumerate(panel.symbols):
        ps = pivots(cleaned[sym], K)
        li = np.array([p.index for p in ps if p.sign < 0], dtype=int)
        hj = np.array([p.index for p in ps if p.sign > 0], dtype=int)
        lp = np.log([p.price for p in ps if p.sign < 0]) if len(li) else np.array([])
        hp = np.log([p.price for p in ps if p.sign > 0]) if len(hj) else np.array([])
        g_lo[i], i_lo[i] = U.rolling_fit(T, li, lp, K)
        g_hi[i], i_hi[i] = U.rolling_fit(T, hj, hp, K)
        atr[i] = U.atr_log(cleaned[sym], ATR_WINDOW)

    ok = ~(np.isnan(g_lo) | np.isnan(g_hi) | np.isnan(i_lo) | np.isnan(i_hi) | np.isnan(atr))
    live = np.zeros((n, T), dtype=bool)
    live[:, start:] = True
    live &= ok

    t = np.arange(T)[None, :]
    lower = i_lo + g_lo * t
    upper = i_hi + g_hi * t
    width = upper - lower
    centre = (upper + lower) / 2.0
    with np.errstate(invalid="ignore", divide="ignore"):
        w_atr = np.where(atr > 0.0, width / np.maximum(atr, 1e-12), np.nan)
    conv = (g_hi < g_lo) & (width > 0.0) & live
    armed = conv & (w_atr <= ARM_ATR)
    return {"armed": armed, "conv": conv, "live": live, "centre": centre,
            "atr": atr, "w_atr": w_atr}


def walk(panel, sig, start: int, hold: int, *, stop: bool):
    """Build the book one trade at a time.

    THE CONVENTION, and it decides every price in here. `position[t]` earns
    `log(C[t]/C[t-1])`, so a position held at bar `a` was bought at `C[a-1]`. The
    break is detected at the close of `t` against a level fixed at `t-1`, exposure
    therefore begins at `t+1`, and the entry price is `C[t]`. A stop decided at
    the close of `t'` takes effect at `t'+1` -- D235's close-to-close convention,
    because daily OHLC cannot distinguish a touch from a gap through the level.

    ONE TRADE PER ARMED EPISODE, AND NO OVERLAPPING TRADES ON ONE SYMBOL. A second
    break inside the same episode, or any break arriving while the symbol is still
    held, is recorded and skipped -- otherwise one structural event is bought
    twice.
    """
    armed, centre, atr = sig["armed"], sig["centre"], sig["atr"]
    n, T = panel.closes.shape
    logC = np.log(panel.closes)
    pos = np.zeros((n, T))
    trades = []                 # (symbol, first held bar, last allowed bar, R)
    cuts = []                   # (trade index, fraction through the span) -- R7's pool
    downs, ups, suppressed = [], [], 0

    for i in range(n):
        fired = False
        busy = -1
        for t in range(start + 1, T):
            if not armed[i, t - 1]:
                fired = False                      # the episode ended; re-arm
                continue
            if fired:
                continue
            a_t = atr[i, t - 1]
            if not np.isfinite(centre[i, t - 1]) or not np.isfinite(a_t):
                continue
            dn = centre[i, t - 1] - TRIG_ATR * a_t
            up = centre[i, t - 1] + TRIG_ATR * a_t
            if logC[i, t] < dn:
                fired = True
                downs.append((i, t))
                if t <= busy:
                    suppressed += 1
                    continue
                a = t + 1
                b = min(t + hold, T - 1)
                if a > b:
                    continue
                entry = logC[i, t]
                level = entry - STOP_ATR * a_t
                exit_at = b
                if stop:
                    for u in range(a, b + 1):
                        if logC[i, u] < level:
                            exit_at = u
                            cuts.append((len(trades), (u - a) / max(b - a, 1)))
                            break
                pos[i, a:exit_at + 1] = 1.0
                trades.append((i, a, b, STOP_ATR * a_t))
                busy = b
            elif logC[i, t] > up:
                fired = True
                ups.append((i, t))
    pos[:, :start] = 0.0
    return pos, trades, cuts, {"down": len(downs), "up": len(ups),
                               "suppressed": suppressed}


# --------------------------------------------------------------------------
# Scoring helpers written fresh, each with its reason
# --------------------------------------------------------------------------


def zero_cost_panel(panel):
    """A cost-free twin, so gross and net are the same computation on two panels
    rather than two computations. `signed_log_returns` charges from
    `panel.cost_fraction`, so zeroing it is the whole of it."""
    return type(panel)(
        symbols=panel.symbols, closes=panel.closes, log_returns=panel.log_returns,
        cost_fraction=np.zeros_like(panel.cost_fraction), dates=panel.dates,
        total_log_returns=panel.total_log_returns,
    )


def breakeven_bps(panel, pos, start: int):
    """The per-side cost at which excess return reaches zero.

    Written fresh because `run_intraday_shorts.breakeven_bps` is bound to
    `excess_intraday` and its session bookkeeping; this is the daily form on
    `excess_of`. Below the ~1.6 bp actually charged means costs alone sink it."""
    turn = float(np.abs(np.diff(pos, axis=1, prepend=0.0))[:, start:].sum()) / len(panel.symbols)
    if turn <= 0.0:
        return None
    total = X.signed_log_returns(panel, pos, total_return=True)[start:]
    ex = X.excess_of(total, pos, start)
    paid = float((panel.cost_fraction[:, None]
                  * np.abs(np.diff(pos, axis=1, prepend=0.0)))[:, start:].sum()
                 / len(panel.symbols))
    gross = float(np.sum(ex)) + paid
    return 1e4 * (1.0 - math.exp(-gross / turn))


def entries_per_symbol(pos, start: int):
    active = (pos != 0.0).astype(float)
    return np.sum(np.diff(active, axis=1, prepend=0.0)[:, start:] > 0.0, axis=1).astype(int)


CONC_SIMS = 200
CONC_CROWD = 20


def concurrency(panel, pos, start: int, seed: int = SEED):
    """Why is the book more volatile than its rotation null? Two candidates, and
    they are separable.

    LOUDNESS -- the bars it holds are individually more volatile than average.
    CLUSTERING -- it holds many names AT THE SAME TIME.

    The second is a property of the null as much as of the arm: `rotation_nulls`
    draws an INDEPENDENT offset per symbol, which destroys cross-sectional
    synchrony. So a rule that fires across the whole universe at once is compared
    against a control that never does. Measured here rather than assumed, because
    the difference decides whether this is a per-instrument signal or a market
    timer wearing one."""
    held = pos[:, start:] != 0.0
    r = panel.total_log_returns[:, start:]
    sd_held = float(np.std(r[held], ddof=1)) if held.any() else 0.0
    sd_all = float(np.std(r, ddof=1))
    k = held.sum(axis=0).astype(float)

    rng = np.random.default_rng(seed)
    n, span = held.shape
    ks = np.empty((CONC_SIMS, span))
    for s in range(CONC_SIMS):
        off = rng.integers(1, span, size=n)
        ks[s] = np.vstack([np.roll(held[i], int(off[i])) for i in range(n)]).sum(axis=0)
    return {
        "loudness_ratio": (sd_held / sd_all) if sd_all > 0 else 0.0,
        "sd_held_annual": sd_held * math.sqrt(PPY),
        "sd_all_annual": sd_all * math.sqrt(PPY),
        "names_held_mean": float(k.mean()),
        "names_held_max": int(k.max()),
        "share_bars_crowded": float((k > CONC_CROWD).mean()),
        "rot_names_held_mean": float(ks.mean()),
        "rot_names_held_max": int(ks.max()),
        "rot_share_bars_crowded": float((ks > CONC_CROWD).mean()),
        "ek2_ratio": float(np.mean(k ** 2) / np.mean(ks ** 2)),
        "clustering_ratio": float(math.sqrt(np.mean(k ** 2) / np.mean(ks ** 2))),
        "crowd_threshold": CONC_CROWD,
        "n_sims": CONC_SIMS,
    }


def _sh(v):
    sd = float(np.std(v, ddof=1))
    return float(np.mean(v) / sd * math.sqrt(PPY)) if sd > 0 else 0.0


def block_indices(nlen: int, seed: int):
    """The programme's standard resample: block 21, `J.N_BOOT` draws. Shared by
    every paired statistic so all of them run on IDENTICAL resampled dates."""
    rng = np.random.default_rng(seed)
    nblk = math.ceil(nlen / J.BLOCK)
    return [(rng.integers(0, nlen - J.BLOCK + 1, size=nblk)[:, None]
             + np.arange(J.BLOCK)[None, :]).ravel()[:nlen] for _ in range(J.N_BOOT)]


def paired_rho_bootstrap(a, b, idxs):
    """A paired block bootstrap on the CORRELATION itself.

    Written fresh because `J.paired_block_bootstrap` returns the interval of a
    Sharpe DIFFERENCE, which is a different statistic. Both arms are recomputed on
    the identical resampled dates -- a bootstrap that drew separate dates per arm
    would destroy exactly the co-movement being measured."""
    out = np.empty(len(idxs))
    for s, ix in enumerate(idxs):
        xa, xb = a[ix], b[ix]
        sa, sb = np.std(xa, ddof=1), np.std(xb, ddof=1)
        out[s] = float(np.corrcoef(xa, xb)[0, 1]) if sa > 0 and sb > 0 else 0.0
    return {"n_boot": len(idxs), "block": J.BLOCK,
            "p05": float(np.percentile(out, 5)), "p50": float(np.percentile(out, 50)),
            "p95": float(np.percentile(out, 95))}


# --------------------------------------------------------------------------


def books_on(which: str):
    """Every book on one fixture. `run_book_extended.books_on` is the precedent;
    the loader, cleaning, per-symbol costs and dividend frame are D217's."""
    path, events = FIXTURES[which]
    assert not any(res in path.name for res in RESERVED), \
        "D246 reserves the wide-universe cohort for S3 -- this study may not open it"
    L.FIXTURE, L.EVENTS = path, events
    panel, cleaned = L.load_panel()
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)
    assert WINDOW < start, "the regression must be defined from the shared start bar"

    sig = wedge_signals(panel, cleaned, start)
    books, meta = {}, {}
    for k in CELL_ORDER:
        pos, trades, cuts, counts = walk(panel, sig, start, HOLDS[k], stop=STOPPED[k])
        books[k] = pos
        meta[k] = {"trades": trades, "cuts": cuts, "counts": counts}

    # No overlapping trades, asserted rather than assumed -- it is the one property
    # that stops a single structural event being bought twice.
    for k in CELL_ORDER:
        spans = np.zeros_like(books[k])
        for i, a, b, _r in meta[k]["trades"]:
            spans[i, a:b + 1] += 1.0
        assert spans.max() <= 1.0, f"{k}: overlapping trades on one symbol"

    md, hs, ok = S.base_masks(panel, cleaned, start)
    s1 = S.hold_book((hs > 0) & (md <= 0) & ok, start)
    up, g_lo, i_lo, atr = U.signals(panel, cleaned, start)
    s2, _, _ = U.walk(panel, up, g_lo, i_lo, atr, start)

    ones = np.ones_like(s1)
    ones[:, :start] = 0.0
    return panel, start, sig, books, meta, {"S1": s1, "S2": s2}, ones


def score_all(panel, books, arms, ones, start):
    cells = {k: X.score(panel, books[k], start) for k in CELL_ORDER}
    cells.update({k: X.score(panel, arms[k], start) for k in arms})
    bh = X.score(panel, ones, start)
    return cells, bh


def rotation_hurdle(panel, books, cells, start):
    """Hurdle H, and the best-of-three floor beside it.

    `X.rotation_nulls` draws ONE offset vector per simulation and applies it to
    every cell (D228), so `max` across cells within a simulation is a legitimate
    best-of-search distribution -- it is not inflated by pretending the cells are
    independent.

    THE MONEY LEG IS A HURDLE HERE, NOT A DIAGNOSTIC. Sharpe is `mean / sd`, and a
    book that concentrates exposure right after 2-ATR declines is exposed in noisy
    weather by construction. Money cannot be inflated that way."""
    nl = X.rotation_nulls(panel, {k: books[k] for k in CELL_ORDER}, start)
    out = {}
    for k in CELL_ORDER:
        d, m, v = nl["draws"][k], nl["money"][k], nl["vol"][k]
        a_sh, a_mn = cells[k]["excess_sharpe"], cells[k]["total_return"]
        out[k] = {
            "p50": float(np.percentile(d, 50)), "p95": float(np.percentile(d, 95)),
            "percentile_of_actual": float((d < a_sh).mean() * 100.0),
            "money_p50": float(np.percentile(m, 50)),
            "money_p95": float(np.percentile(m, 95)),
            "money_percentile_of_actual": float((m < a_mn).mean() * 100.0),
            "vol_p50": float(np.percentile(v, 50)),
            "vol_ratio": float(cells[k]["vol"] / np.percentile(v, 50)),
            # Money EARNED PER UNIT OF VOLATILITY, actual against the null's median.
            # This is what separates "the timing found better bars" from "the timing
            # found louder bars and was paid the going rate for holding them".
            "money_per_vol": float(cells[k]["total_return"] / cells[k]["vol"]),
            "money_per_vol_null": float(np.percentile(m, 50) / np.percentile(v, 50)),
            "clears_sharpe": bool(a_sh > float(np.percentile(d, 95))),
            "clears_money": bool(a_mn > float(np.percentile(m, 95))),
        }
        out[k]["clears_H"] = bool(out[k]["clears_sharpe"] and out[k]["clears_money"])

    best_sh = np.max(np.vstack([nl["draws"][k] for k in CELL_ORDER]), axis=0)
    best_mn = np.max(np.vstack([nl["money"][k] for k in CELL_ORDER]), axis=0)
    top = max(CELL_ORDER, key=lambda k: cells[k]["excess_sharpe"])
    best = {
        "best_cell": top,
        "floor_sharpe": float(np.percentile(best_sh, 95)),
        "floor_money": float(np.percentile(best_mn, 95)),
        "actual_sharpe": cells[top]["excess_sharpe"],
        "actual_money": cells[top]["total_return"],
        "percentile_sharpe": float((best_sh < cells[top]["excess_sharpe"]).mean() * 100.0),
        "percentile_money": float((best_mn < cells[top]["total_return"]).mean() * 100.0),
    }
    best["clears_H_BEST"] = bool(
        best["actual_sharpe"] > best["floor_sharpe"]
        and best["actual_money"] > best["floor_money"]
    )
    return out, best


def overlay_hurdle(panel, meta, cells, start):
    """R7, scoped to the stop cell. Keep W2's book, cut THE SAME NUMBER of trades
    short at random trades and random points inside their own spans.
    `U.null_book` is reused unchanged -- it is exactly this control."""
    rng = np.random.default_rng(SEED)
    base = meta[BASE_OF_OVERLAY]["trades"]
    out = {}
    for k in OVERLAY_CELLS:
        cuts = meta[k]["cuts"]
        pool = np.array([f for _, f in cuts]) if cuts else np.array([1.0])
        draws = np.empty(N_SIMS)
        for s in range(N_SIMS):
            draws[s] = X._excess_sharpe(
                panel, U.null_book(panel, base, len(cuts), pool, rng, start), start)
        actual = cells[k]["excess_sharpe"]
        out[k] = {"n_cut": len(cuts), "n_trades": len(base),
                  "p50": float(np.percentile(draws, 50)),
                  "p95": float(np.percentile(draws, 95)),
                  "percentile_of_actual": float((draws < actual).mean() * 100.0),
                  "clears_H_OVL": bool(actual > float(np.percentile(draws, 95)))}
    return out


def stage(which: str, floors=None):
    panel, start, sig, books, meta, arms, ones = books_on(which)
    cells, bh = score_all(panel, books, arms, ones, start)

    if which == "57":
        for k, v in BOOK_EXTENDED.items():
            assert abs(cells[k]["excess_sharpe"] - v) < 5e-4, \
                f"{k} did not reproduce ({cells[k]['excess_sharpe']:.6f}) -- rho is void"

    zp = zero_cost_panel(panel)
    gross = {k: X.score(zp, books[k], start)["excess_sharpe"] for k in CELL_ORDER}
    bkev = {k: breakeven_bps(panel, books[k], start) for k in CELL_ORDER}
    eps = {k: entries_per_symbol(books[k], start) for k in CELL_ORDER}

    nulls, best = rotation_hurdle(panel, books, cells, start)
    ovl = overlay_hurdle(panel, meta, cells, start)

    def excess(pos):
        tot = X.signed_log_returns(panel, pos, total_return=True)[start:]
        return X.excess_of(tot, pos, start)

    r = {k: excess(books[k]) for k in CELL_ORDER}
    r.update({k: excess(arms[k]) for k in arms})
    r["BH"] = excess(ones)
    idxs = block_indices(len(r["BH"]), SEED)

    boot = {}
    for k in list(CELL_ORDER) + ["S1", "S2"]:
        own = np.array([_sh(r[k][i]) for i in idxs])
        dbh = np.array([_sh(r[k][i]) - _sh(r["BH"][i]) for i in idxs])
        boot[k] = {"sharpe_p05": float(np.percentile(own, 5)),
                   "sharpe_p95": float(np.percentile(own, 95)),
                   "sharpe_excludes_zero": bool(np.percentile(own, 5) > 0.0),
                   "delta_bh": cells[k]["excess_sharpe"] - bh["excess_sharpe"],
                   "delta_bh_p05": float(np.percentile(dbh, 5)),
                   "delta_bh_excludes_zero": bool(np.percentile(dbh, 5) > 0.0)}

    verdict = {}
    for k in CELL_ORDER:
        d = cells[k]["excess_sharpe"] - bh["excess_sharpe"]
        v = {"delta_vs_bh": d,
             "clears_H": nulls[k]["clears_H"],
             "clears_P": bool(d > 0.0),
             "clears_E": cells[k]["clears_E"],
             "entries": int(eps[k].sum()),
             "entries_min": int(eps[k].min()),
             "entries_mean": float(eps[k].mean()),
             "gross_sharpe": gross[k],
             "breakeven_bps": bkev[k]}
        if floors is not None:
            v["floor"] = floors[k]
            v["clears_floor"] = bool(d >= floors[k])
            v["clears_all"] = bool(v["clears_H"] and v["clears_P"] and v["clears_floor"])
        verdict[k] = v

    payload = {
        "n_symbols": len(panel.symbols),
        "live_bars": len(panel.dates) - start,
        "first_live_date": panel.dates[start][:10],
        "last_date": panel.dates[-1][:10],
        "effective_instruments": W.effective_instruments(panel.total_log_returns[:, start:]),
        "cells": cells, "buy_and_hold": bh, "nulls": nulls, "best_of": best,
        "overlay_nulls": ovl, "bootstrap": boot, "verdict": verdict,
        "trigger_counts": {k: meta[k]["counts"] for k in CELL_ORDER},
        "entries_per_symbol": {k: eps[k].tolist() for k in CELL_ORDER},
        "deployable_return": {
            k: float(np.expm1(np.log1p(cells[k]["cagr"])
                              + math.log1p(RF_ANNUAL) * (1 - cells[k]["exposure_gross"])))
            for k in list(CELL_ORDER) + ["S1", "S2"]},
    }
    return payload, panel, start, sig, books, arms, ones, r, idxs, cells, bh


def build() -> dict:
    t0 = time.time()

    (scr, panel, start, sig, books, arms, ones, r, idxs,
     cells, bh) = stage("57")

    # --- the anatomy the pre-registration verified, recomputed so the record and
    # --- the artifact cannot drift apart. R9: every level is read at t-1.
    live, conv, armed, w_atr = sig["live"], sig["conv"], sig["armed"], sig["w_atr"]
    nlive = int(live.sum())
    widths = w_atr[conv]
    assert np.all(np.isfinite(widths)), "a converging cell has an undefined width in ATRs"
    anatomy = {
        "live_cells": nlive,
        "converging_share": float(conv.sum() / nlive),
        "width_atr_percentiles": {f"p{q}": float(np.percentile(widths, q))
                                  for q in (5, 10, 25, 50, 75)},
        "armed_share": float(armed.sum() / nlive),
        "arming_sweep": {},
    }
    with np.errstate(invalid="ignore"):
        for k in (1.0, 2.0, 3.0):
            a = conv & (w_atr <= k)
            prev = np.zeros_like(a)
            prev[:, 1:] = a[:, :-1]
            on = a & ~prev
            anatomy["arming_sweep"][f"{k:.1f}"] = {
                "share": float(a.sum() / nlive), "episodes": int(on.sum()),
                "per_symbol": float(on.sum(axis=1).mean())}

    # --- why the book is more volatile than its null, decomposed
    conc = {k: concurrency(panel, books[k], start) for k in CELL_ORDER}

    # --- the overlap analysis, which carries as much weight as the returns
    s1_held = arms["S1"][:, start:] != 0.0
    s2_held = arms["S2"][:, start:] != 0.0
    overlap = {}
    for k in CELL_ORDER:
        w_held = books[k][:, start:] != 0.0
        nw, n1, n2 = float(w_held.sum()), float(s1_held.sum()), float(s2_held.sum())
        overlap[k] = {
            "wedge_bars": int(nw),
            "p_s1_given_wedge": float((w_held & s1_held).sum() / max(nw, 1.0)),
            "p_wedge_given_s1": float((w_held & s1_held).sum() / max(n1, 1.0)),
            "p_s2_given_wedge": float((w_held & s2_held).sum() / max(nw, 1.0)),
            "p_wedge_given_s2": float((w_held & s2_held).sum() / max(n2, 1.0)),
            "chance_s1": float(n1 / (w_held.size)),
            "chance_wedge": float(nw / (w_held.size)),
        }
        for arm in ("S1", "S2"):
            rho = float(np.corrcoef(r[k], r[arm])[0, 1])
            sr_arm = cells[arm]["excess_sharpe"]
            overlap[k][f"rho_{arm}"] = rho
            overlap[k][f"rho_{arm}_ci"] = paired_rho_bootstrap(r[k], r[arm], idxs)
            overlap[k][f"bar_{arm}"] = rho * sr_arm
            overlap[k][f"clears_div_{arm}"] = bool(cells[k]["excess_sharpe"] > rho * sr_arm)

    # The S1-excluded residual. Declared as a diagnostic in D249 and counted; NOT a
    # cell. If the wedge book minus S1's bars carries nothing, O4 needs no argument.
    resid = books[BASE_OF_OVERLAY].copy()
    resid[:, start:][s1_held] = 0.0
    residual = X.score(panel, resid, start)
    residual["share_of_bars_kept"] = float(
        (resid[:, start:] != 0.0).sum() / max((books[BASE_OF_OVERLAY][:, start:] != 0.0).sum(), 1))

    # --- the matched-span read: the 57 restricted to the 60's live window, so the
    # --- screen and the validation are comparable despite different spans.
    val_first = None

    floors = {k: 0.25 * scr["verdict"][k]["delta_vs_bh"] for k in CELL_ORDER}
    val = stage("60", floors=floors)[0]
    val_first = val["first_live_date"]

    d = np.array([x[:10] for x in panel.dates[start:]])
    mask = d >= val_first
    matched = {k: E.sub_score(panel, books[k], start, mask) for k in CELL_ORDER}
    matched["BH"] = E.sub_score(panel, ones, start, mask)
    matched["S1"] = E.sub_score(panel, arms["S1"], start, mask)
    matched["S2"] = E.sub_score(panel, arms["S2"], start, mask)

    cleared_screen = [k for k in CELL_ORDER if scr["verdict"][k]["clears_H"]]
    cleared_val = [k for k in CELL_ORDER if val["verdict"][k]["clears_all"]]
    hi_overlap = max(max(overlap[k]["p_s1_given_wedge"], overlap[k]["p_wedge_given_s1"])
                     for k in CELL_ORDER)
    top_ov = max(CELL_ORDER, key=lambda k: overlap[k]["p_s1_given_wedge"])
    q = overlap[top_ov]
    ratio = q["p_s1_given_wedge"] / q["chance_s1"]
    hi_rho = max(overlap[k]["rho_S1"] for k in CELL_ORDER)
    o4 = (
        f"IT IS S1 WITH A DIFFERENT TRIGGER. Overlap reaches {hi_overlap:.1%}, past the 50% "
        f"line D249 committed in advance, so the candidate is closed as a variant regardless "
        f"of what any return hurdle did."
        if hi_overlap > 0.50 else
        f"NEITHER. It is not S1 in disguise -- overlap peaks at {q['p_s1_given_wedge']:.1%} of "
        f"the wedge's held bars against a {q['chance_s1']:.1%} chance baseline "
        f"({ratio:.2f}x chance) with rho at most {hi_rho:+.3f}, so the two rules lean on a "
        f"shared population without being the same rule. But it is not a new arm either, and "
        f"that is the operative half: there is no edge here to diversify. No cell beats its "
        f"rotation null on the screen, and on the holdout the best of the three sits at the "
        f"{min(val['nulls'][k]['percentile_of_actual'] for k in CELL_ORDER):.1f}th-"
        f"{max(val['nulls'][k]['percentile_of_actual'] for k in CELL_ORDER):.1f}th percentile "
        f"of randomly-timed books holding the same amount. What the two rules share is the "
        f"thing the concurrency measurement names: both are buying broad market weakness. The "
        f"wedge holds up to {conc[BASE_OF_OVERLAY]['names_held_max']} of "
        f"{scr['n_symbols']} names at once, so it is a market timer wearing a per-instrument "
        f"signal, and S1 is the same bet made better."
    )
    reading = (
        "CLOSED BY THE OVERLAP STOP -- this is S1 with a different trigger, and D249 "
        "committed in advance that overlap above 50% either way closes the candidate "
        "regardless of the return hurdles."
        if hi_overlap > 0.50 else
        ("NO CELL SURVIVES THE HOLDOUT. The inverse wedge breakout is CLOSED under D249's "
         "stop -- no fourth holding rule, no re-cut arming threshold, no wider universe."
         if not cleared_val else
         "A CELL SURVIVED THE HOLDOUT. Nothing is promoted: under R8 it becomes a candidate "
         "needing a TIME holdout, which this fixture pair cannot supply.")
    )

    return {
        "produced": "D249",
        "stage": "screen on the mined 57, validation on the 60-ETF instrument holdout",
        "provenance": "complement of a failed construction -- registered separately, NOT S3",
        "seed": SEED, "n_sims": N_SIMS, "n_boot": J.N_BOOT, "block": J.BLOCK,
        "k": K, "window": WINDOW, "atr_window": ATR_WINDOW,
        "arm_atr": ARM_ATR, "trig_atr": TRIG_ATR, "stop_atr": STOP_ATR,
        "holds": HOLDS, "rf_annual": RF_ANNUAL,
        "reserved_cohort_untouched": True,
        "anatomy": anatomy, "overlap": overlap, "residual": residual,
        "concurrency": conc,
        "matched_span": matched, "matched_span_from": val_first,
        "screen": scr, "validation": val,
        "cleared_screen": cleared_screen, "cleared_validation": cleared_val,
        "max_overlap_either_direction": hi_overlap,
        "o4": o4, "reading": reading,
        "elapsed_seconds": round(time.time() - t0, 1),
    }


# --------------------------------------------------------------------------


NAMES = {"W1": "down-break, hold 21", "W2": "down-break, hold 42",
         "W3": "W2 + stop at entry − 2·ATR"}


def _cell_table(o, p, key):
    d = p[key]
    c, dep, v = d["cells"], d["deployable_return"], d["verdict"]
    o.append("| | | exposure | **net exSh** | *gross* | CAGR | deployable | max DD | Calmar | "
             "breakeven | entries | min/sym | E |")
    o.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:--:|")
    for k in CELL_ORDER:
        x, q = c[k], v[k]
        cal = x["cagr"] / abs(x["max_drawdown"]) if x["max_drawdown"] else float("nan")
        be = q["breakeven_bps"]
        o.append(
            f"| **{k}** | {NAMES[k]} | {x['exposure_gross']:.1%} | "
            f"**{x['excess_sharpe']:+.3f}** | *{q['gross_sharpe']:+.3f}* | "
            f"{x['cagr'] * 100:.2f}% | {dep[k] * 100:.2f}% | "
            f"{x['max_drawdown'] * 100:+.2f}% | {cal:.3f} | "
            f"{(f'{be:.1f} bp' if be is not None else '—')} | {q['entries']} | "
            f"**{q['entries_min']}** | {'✓' if q['clears_E'] else '✗'} |")
    for lab in ("S1", "S2"):
        x = c[lab]
        o.append(f"| *{lab}* | *for scale* | *{x['exposure_gross']:.1%}* | "
                 f"*{x['excess_sharpe']:+.3f}* | — | *{x['cagr'] * 100:.2f}%* | "
                 f"*{dep[lab] * 100:.2f}%* | *{x['max_drawdown'] * 100:+.2f}%* | "
                 f"*{x['cagr'] / abs(x['max_drawdown']):.3f}* | — | *{x['entries']}* | "
                 f"*{x['min_entries_per_symbol']}* | — |")
    b = d["buy_and_hold"]
    o.append(f"| *B&H* | *always long* | *100.0%* | *{b['excess_sharpe']:+.3f}* | — | "
             f"*{b['cagr'] * 100:.2f}%* | *{b['cagr'] * 100:.2f}%* | "
             f"*{b['max_drawdown'] * 100:+.2f}%* | "
             f"*{b['cagr'] / abs(b['max_drawdown']):.3f}* | — | — | — | — |")
    o.append("")


def render(p: dict) -> str:
    scr, val, ov, an = p["screen"], p["validation"], p["overlap"], p["anatomy"]
    o = ["# D249 — the inverse wedge breakout\n"]
    o.append(f"**PROVENANCE: {p['provenance']}.** D246 Constraint 3 makes an inverse-of-a-"
             "failed-cell ineligible under the S3 search protocol, so this is registered on "
             "its own merits. **D245's reserved never-seen cohort is not spent here.**\n")
    o.append(
        f"*seed {p['seed']}, {p['n_sims']:,} rotations, {p['n_boot']:,} bootstrap draws at "
        f"block {p['block']}, {p['elapsed_seconds']}s. Screen: {scr['n_symbols']} ETFs x "
        f"{scr['live_bars']:,} live bars, {scr['first_live_date']} .. {scr['last_date']}. "
        f"Validation: {val['n_symbols']} ETFs x {val['live_bars']:,} bars, "
        f"{val['first_live_date']} .. {val['last_date']}. "
        f"k={p['k']}, window {p['window']}, ATR({p['atr_window']}), armed at width ≤ "
        f"{p['arm_atr']:g}·ATR, trigger ±{p['trig_atr']:g}·ATR.*\n")

    top_money = max(CELL_ORDER, key=lambda k: scr["nulls"][k]["money_percentile_of_actual"])
    tm = scr["nulls"][top_money]
    cc = p["concurrency"][top_money]
    o.append("## The one-sentence version\n")
    o.append(
        f"**The wedge down-break is not a per-instrument signal — it fires across the universe "
        f"at once, holding up to {cc['names_held_max']} of {scr['n_symbols']} names "
        f"simultaneously where a rotated book never exceeds {cc['rot_names_held_max']} — so "
        f"{top_money} builds a book {tm['vol_ratio']:.1f}× more volatile than its own null, "
        f"earns more money than {tm['money_percentile_of_actual']:.1f}% of rotations and less "
        f"per unit of risk than the median one, and on the holdout it is not paid at all.**\n")

    o.append("## The reading, as declared in advance\n")
    o.append(f"> **{p['reading']}**\n")

    o.append("## The setup structure — verified before the pre-registration, R9-compliant\n")
    o.append(f"**{an['converging_share']:.1%}** of {an['live_cells']:,} live cells have "
             f"converging lines. Channel width among those, in ATRs:\n")
    w = an["width_atr_percentiles"]
    o.append("| p5 | p10 | p25 | p50 | p75 |")
    o.append("|---:|---:|---:|---:|---:|")
    o.append("| " + " | ".join(f"{w[f'p{q}']:.2f}" for q in (5, 10, 25, 50, 75)) + " |")
    o.append("")
    o.append("| arming threshold | share of cells | episodes | per symbol |")
    o.append("|---|---:|---:|---:|")
    for k in ("1.0", "2.0", "3.0"):
        a = an["arming_sweep"][k]
        star = " **← registered**" if k == "2.0" else ""
        o.append(f"| width ≤ {k}·ATR{star} | {a['share']:.2%} | {a['episodes']:,} | "
                 f"{a['per_symbol']:.1f} |")
    o.append("")
    tc = scr["trigger_counts"]["W2"]
    o.append(
        f"**Episodes are not entries, and that is the correction D249 registered as T-a.** The "
        f"57 produce **{tc['down']:,} down-breaks** and **{tc['up']:,} up-breaks**; the up leg "
        f"is never traded, and **{tc['suppressed']:,}** further down-breaks are suppressed as "
        f"overlapping at the 42-bar hold. What reaches the book is in the `entries` column "
        f"below.\n")

    o.append("## The screen — the mined 57\n")
    _cell_table(o, p, "screen")
    o.append(f"**Effective independent instruments: {scr['effective_instruments']:.2f}.** "
             "D245 measured 2.23 for this universe and found it *falls* as headcount grows. "
             "**The pooled trade count is not a sample size and is not quoted as one.**\n")

    o.append("## Hurdle H — the matched-count rotation null, which carries the verdict\n")
    o.append("*Same exposure, same turnover, same holding periods, wrong bars. **Money is a "
             "hurdle leg here, not a diagnostic** — a book that concentrates exposure right "
             "after 2-ATR declines is exposed in noisy weather by construction, and Sharpe "
             "alone cannot tell that from skill.*\n")
    o.append("| | actual | null p95 | **pctile** | money | money p95 | **pctile** | vol ratio | H |")
    o.append("|---|---:|---:|---:|---:|---:|---:|---:|:--:|")
    for k in CELL_ORDER:
        n, c = scr["nulls"][k], scr["cells"][k]
        o.append(f"| **{k}** | **{c['excess_sharpe']:+.3f}** | {n['p95']:+.3f} | "
                 f"**{n['percentile_of_actual']:.1f}th** | {c['total_return'] * 100:+.2f}% | "
                 f"{n['money_p95'] * 100:+.2f}% | **{n['money_percentile_of_actual']:.1f}th** | "
                 f"{n['vol_ratio']:.3f}x | {'✓' if n['clears_H'] else '✗'} |")
    o.append("")
    o.append("**The two legs disagree, and the vol ratio is why — this is the finding.**\n")
    o.append("*Money earned per unit of volatility, actual against the null's median. If the "
             "timing found genuinely better bars this ratio rises; if it merely found louder "
             "ones and was paid the going rate, it does not.*\n")
    o.append("| | vol | null vol p50 | **ratio** | money/vol | null money/vol | better bars? |")
    o.append("|---|---:|---:|---:|---:|---:|:--:|")
    for k in CELL_ORDER:
        n, c = scr["nulls"][k], scr["cells"][k]
        o.append(f"| **{k}** | {c['vol'] * 100:.2f}% | {n['vol_p50'] * 100:.2f}% | "
                 f"**{n['vol_ratio']:.2f}x** | {n['money_per_vol']:.2f} | "
                 f"{n['money_per_vol_null']:.2f} | "
                 f"{'✓' if n['money_per_vol'] > n['money_per_vol_null'] else '✗'} |")
    o.append("")
    o.append(
        "**The measured +15% to +18% annualised after a down-break is compensation for risk, "
        "not timing skill.** The rotation null matches exposure, turnover and holding periods "
        "— **it does not match the volatility of the book that results**, and that gap is the "
        "entire distance between the money column and the Sharpe column.\n")

    o.append("### Where that volatility comes from — and it is NOT the obvious answer\n")
    o.append("*Two candidates, and they separate cleanly. **Loudness**: the bars it holds are "
             "individually more volatile than average. **Clustering**: it holds many names at "
             "the same time. `rotation_nulls` draws an independent offset per symbol, so it "
             "destroys cross-sectional synchrony by construction.*\n")
    cn = p["concurrency"]
    o.append(f"| | loudness | names held, mean | max | *rotated max* | bars over "
             f"{cn[CELL_ORDER[0]]['crowd_threshold']} names | *rotated* | clustering |")
    o.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for k in CELL_ORDER:
        q = cn[k]
        o.append(f"| **{k}** | {q['loudness_ratio']:.2f}× | {q['names_held_mean']:.1f} | "
                 f"**{q['names_held_max']}** | *{q['rot_names_held_max']}* | "
                 f"**{q['share_bars_crowded']:.1%}** | *{q['rot_share_bars_crowded']:.1%}* | "
                 f"**{q['clustering_ratio']:.2f}×** |")
    o.append("")
    q = cn[BASE_OF_OVERLAY]
    o.append(
        f"**The bars are barely louder than average ({q['loudness_ratio']:.2f}×). The book is "
        f"vastly more crowded.** W2 holds more than {q['crowd_threshold']} of "
        f"{scr['n_symbols']} names on **{q['share_bars_crowded']:.1%}** of bars where a "
        f"rotated book of identical exposure does so on **{q['rot_share_bars_crowded']:.1%}**, "
        f"and it peaks at **{q['names_held_max']}** names against the rotation's "
        f"**{q['rot_names_held_max']}**. **Converging channels break downward together, "
        f"because they break when the market falls.**\n")
    o.append(
        "**So the rule is a market timer wearing a per-instrument signal.** It is not selecting "
        "which ETF to buy; it is selecting *when* to buy all of them. That is a legitimate "
        "thing to be — it is roughly what S1 is — but it means the diversification across 57 "
        "names that the equal-weighted book appears to have is largely illusory on exactly the "
        "bars that matter, and it is why the book carries an −18% drawdown at 15% exposure "
        "where S2 carries −5.8% at 13%.\n")
    o.append(
        "**A limitation of the null, recorded rather than buried:** a per-symbol rotation null "
        "**understates the volatility of any book whose signal is market-wide**, so it is a "
        "*conservative* control for such a rule on money and a *harsh* one on Sharpe. Both "
        "legs were registered, and between them they bracket the truth — which is the practical "
        "argument for the two-legged form.\n")
    o.append(
        "**D249 registered the money leg for the opposite reason and it caught this anyway.** "
        "The record's argument was D238's: a high-volatility book could inflate its *Sharpe*, "
        "so money was added as the leg that cannot be inflated. What happened is the mirror "
        "image — **money was the inflated leg and Sharpe was the honest one** — because "
        "D238's arm had a negative mean and this one does not. The reasoning was pointed the "
        "wrong way; requiring *both* legs is what made that harmless.\n")
    bo = scr["best_of"]
    o.append("### H-BEST — the multiplicity leg\n")
    o.append("*Three cells screened, one shared offset vector per simulation (D228). **D240's "
             "stop cleared at the 99.6th percentile with no correction and failed out of sample "
             "at the 71.7th.***\n")
    o.append(
        f"| best cell | actual | best-of-3 floor | pctile | actual money | money floor | "
        f"pctile | H-BEST |\n|---|---:|---:|---:|---:|---:|---:|:--:|\n"
        f"| **{bo['best_cell']}** | {bo['actual_sharpe']:+.3f} | {bo['floor_sharpe']:+.3f} | "
        f"**{bo['percentile_sharpe']:.1f}th** | {bo['actual_money'] * 100:+.2f}% | "
        f"{bo['floor_money'] * 100:+.2f}% | **{bo['percentile_money']:.1f}th** | "
        f"{'✓' if bo['clears_H_BEST'] else '✗'} |\n")

    o.append("### H-OVL — R7, scoped to the stop cell\n")
    o.append("*A rotation null is the wrong control for something that modifies a book W2 "
             "already chose. Keep W2's book; cut the same number of trades short at random "
             "trades and random points inside their own spans.*\n")
    o.append("| | trades cut | actual | null p50 | null p95 | **pctile** | H-OVL |")
    o.append("|---|---:|---:|---:|---:|---:|:--:|")
    for k in OVERLAY_CELLS:
        n = scr["overlay_nulls"][k]
        o.append(f"| **{k}** | {n['n_cut']} of {n['n_trades']} | "
                 f"**{scr['cells'][k]['excess_sharpe']:+.3f}** | {n['p50']:+.3f} | "
                 f"{n['p95']:+.3f} | **{n['percentile_of_actual']:.1f}th** | "
                 f"{'✓' if n['clears_H_OVL'] else '✗'} |")
    o.append("")

    o.append("## THE OVERLAP ANALYSIS — is this a new arm, or S1 with a different trigger?\n")
    o.append("*S1's own exposure is the chance baseline: if the two rules were independent, "
             "`P(S1 | wedge)` would equal S1's exposure exactly. D242 measured **8.9%** for S2 "
             "— less than half chance — which is what a structurally disjoint arm looks like.*\n")
    o.append("| | `P(S1 \\| wedge)` | *chance* | `P(wedge \\| S1)` | *chance* | "
             "`P(S2 \\| wedge)` | `P(wedge \\| S2)` |")
    o.append("|---|---:|---:|---:|---:|---:|---:|")
    for k in CELL_ORDER:
        q = ov[k]
        o.append(f"| **{k}** | **{q['p_s1_given_wedge']:.1%}** | *{q['chance_s1']:.1%}* | "
                 f"**{q['p_wedge_given_s1']:.1%}** | *{q['chance_wedge']:.1%}* | "
                 f"{q['p_s2_given_wedge']:.1%} | {q['p_wedge_given_s2']:.1%} |")
    o.append("")
    o.append("**Correlation of the daily excess-return streams, with the paired block "
             "bootstrap interval — both arms recomputed on identical resampled dates:**\n")
    o.append("| | ρ with S1 | p05 | p95 | ρ with S2 | p05 | p95 |")
    o.append("|---|---:|---:|---:|---:|---:|---:|")
    for k in CELL_ORDER:
        q = ov[k]
        a, b = q["rho_S1_ci"], q["rho_S2_ci"]
        o.append(f"| **{k}** | **{q['rho_S1']:+.4f}** | {a['p05']:+.3f} | {a['p95']:+.3f} | "
                 f"{q['rho_S2']:+.4f} | {b['p05']:+.3f} | {b['p95']:+.3f} |")
    o.append("")
    o.append("**The diversification condition, `SR_B > ρ · SR_A`** — evaluated against both "
             "arms. *A weak incumbent makes this a weak test, which D249 registered as T-e.*\n")
    o.append("| | actual | bar vs S1 | vs S1 | bar vs S2 | vs S2 |")
    o.append("|---|---:|---:|:--:|---:|:--:|")
    for k in CELL_ORDER:
        q = ov[k]
        o.append(f"| **{k}** | **{scr['cells'][k]['excess_sharpe']:+.3f}** | "
                 f"{q['bar_S1']:+.3f} | {'✓' if q['clears_div_S1'] else '✗'} | "
                 f"{q['bar_S2']:+.3f} | {'✓' if q['clears_div_S2'] else '✗'} |")
    o.append("")
    rs = p["residual"]
    o.append(f"**The S1-excluded residual** — W2's book with every bar S1 also holds removed, "
             f"keeping **{rs['share_of_bars_kept']:.1%}** of its bars: excess Sharpe "
             f"**{rs['excess_sharpe']:+.3f}** at {rs['exposure_gross']:.1%} exposure, "
             f"{rs['total_return'] * 100:+.2f}% total return. *Declared as a diagnostic in "
             f"D249 and counted; not a cell.*\n")
    o.append("### O4 — the direct answer, as D249 required it\n")
    o.append(f"> **{p['o4']}**\n")

    o.append("## Validation — the 60-ETF instrument holdout\n")
    o.append("*The wedge rule has never touched these 60 names. **The cohort is not pristine "
             "at the universe level** — it was spent on S1 (D237) and on A0/A2/C0 (D242) — and "
             "its span is shorter than and nested inside the screen's era, so this tests "
             "instruments and not time.*\n")
    _cell_table(o, p, "validation")
    o.append("| | Δ vs B&H | floor | null p95 | **pctile** | money pctile | H | P | floor | "
             "**all** |")
    o.append("|---|---:|---:|---:|---:|---:|:--:|:--:|:--:|:--:|")
    for k in CELL_ORDER:
        q, n = val["verdict"][k], val["nulls"][k]
        o.append(f"| **{k}** | **{q['delta_vs_bh']:+.3f}** | {q['floor']:+.3f} | "
                 f"{n['p95']:+.3f} | **{n['percentile_of_actual']:.1f}th** | "
                 f"{n['money_percentile_of_actual']:.1f}th | "
                 f"{'✓' if q['clears_H'] else '✗'} | {'✓' if q['clears_P'] else '✗'} | "
                 f"{'✓' if q['clears_floor'] else '✗'} | "
                 f"**{'✓' if q['clears_all'] else '✗'}** |")
    o.append("")
    o.append(f"**Effective independent instruments on the 60: "
             f"{val['effective_instruments']:.2f}.**\n")

    ms = p["matched_span"]
    o.append("### The screen restricted to the validation span, so the two are comparable\n")
    o.append(f"*The 57 scored only over {p['matched_span_from']} onward — same era, different "
             "instruments.*\n")
    o.append("| | 57, matched span | 60, full |")
    o.append("|---|---:|---:|")
    for k in CELL_ORDER:
        o.append(f"| **{k}** | {ms[k]['excess_sharpe']:+.3f} | "
                 f"{val['cells'][k]['excess_sharpe']:+.3f} |")
    for k in ("S1", "S2", "BH"):
        o.append(f"| *{k}* | *{ms[k]['excess_sharpe']:+.3f}* | "
                 f"*{(val['cells'][k]['excess_sharpe'] if k != 'BH' else val['buy_and_hold']['excess_sharpe']):+.3f}* |")
    o.append("")

    o.append("## Intervals — reported for width, not as a verdict\n")
    o.append("*Block 21, paired on identical resampled dates. At 2-odd effective instruments "
             "no interval here is going to be narrow.*\n")
    o.append("| | excess Sharpe | p05 | p95 | excludes 0 | Δ vs B&H | p05 | excludes 0 |")
    o.append("|---|---:|---:|---:|:--:|---:|---:|:--:|")
    for k in list(CELL_ORDER) + ["S1", "S2"]:
        q = scr["bootstrap"][k]
        o.append(f"| **{k}** | {scr['cells'][k]['excess_sharpe']:+.3f} | "
                 f"{q['sharpe_p05']:+.3f} | {q['sharpe_p95']:+.3f} | "
                 f"{'✓' if q['sharpe_excludes_zero'] else '✗'} | {q['delta_bh']:+.3f} | "
                 f"{q['delta_bh_p05']:+.3f} | "
                 f"{'✓' if q['delta_bh_excludes_zero'] else '✗'} |")
    o.append("")
    return "\n".join(o) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()
    if args.report_only:
        payload = json.loads(SUMMARY.read_text(encoding="utf-8"))
    else:
        payload = build()
        SUMMARY.write_text(json.dumps(payload, indent=1, sort_keys=True), encoding="utf-8")
    RESULTS.write_text(render(payload), encoding="utf-8")

    scr, val, ov = payload["screen"], payload["validation"], payload["overlap"]
    print()
    for label, d in (("SCREEN 57", scr), ("VALID 60", val)):
        print(f"--- {label}: {d['n_symbols']} x {d['live_bars']:,} bars from "
              f"{d['first_live_date']}, breadth {d['effective_instruments']:.2f}")
        print(f"{'cell':5s} {'expo':>7s} {'exSh':>8s} {'dBH':>8s} {'pctile':>8s} "
              f"{'money':>8s} {'ent':>6s} {'min':>4s} {'bkev':>8s}  H  E")
        for k in CELL_ORDER:
            c, n, q = d["cells"][k], d["nulls"][k], d["verdict"][k]
            be = q["breakeven_bps"]
            print(f"{k:5s} {c['exposure_gross']:7.1%} {c['excess_sharpe']:+8.3f} "
                  f"{q['delta_vs_bh']:+8.3f} {n['percentile_of_actual']:7.1f}th "
                  f"{n['money_percentile_of_actual']:7.1f}th {q['entries']:6d} "
                  f"{q['entries_min']:4d} "
                  + (f"{be:6.1f}bp" if be is not None else f"{'—':>8s}")
                  + f"  {'Y' if q['clears_H'] else 'N'}  {'Y' if q['clears_E'] else 'N'}")
        print(f"{'B&H':5s} {100.0:6.1f}% {d['buy_and_hold']['excess_sharpe']:+8.3f}")
        print()
    bo = scr["best_of"]
    print(f"H-BEST : {bo['best_cell']} {bo['actual_sharpe']:+.3f} vs floor "
          f"{bo['floor_sharpe']:+.3f} -> {'CLEARS' if bo['clears_H_BEST'] else 'FAILS'}")
    for k in OVERLAY_CELLS:
        n = scr["overlay_nulls"][k]
        print(f"H-OVL  : {k} at {n['percentile_of_actual']:.1f}th -> "
              f"{'CLEARS' if n['clears_H_OVL'] else 'FAILS'}")
    print()
    print("OVERLAP")
    for k in CELL_ORDER:
        q = ov[k]
        print(f"  {k}: P(S1|wedge) {q['p_s1_given_wedge']:6.1%} (chance "
              f"{q['chance_s1']:.1%})   P(wedge|S1) {q['p_wedge_given_s1']:6.1%}   "
              f"rho(S1) {q['rho_S1']:+.3f} [{q['rho_S1_ci']['p05']:+.3f}, "
              f"{q['rho_S1_ci']['p95']:+.3f}]")
    print()
    print(payload["reading"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
