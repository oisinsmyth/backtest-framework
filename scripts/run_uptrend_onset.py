"""D240 — the uptrend-onset arm, with stops and targets.

    UPTREND := g_lo > 0 AND g_hi > 0     OLS slopes of log swing-low / swing-high
                                         prices over a trailing 252 bars, k = 3

    ENTRY   the first bar of an UPTREND episode (onset; no re-entry within one)
    EXIT    the earliest of  age >= 63  |  the state ends  |  a stop  |  a target

Five cells: A0 base, A1 the structural sloped stop, A2 a fixed -8% stop,
A3 a +2R target, A4 both.

WHY THE PRIMARY HURDLE IS A NULL THAT DID NOT EXIST. R7 requires an overlay to be
controlled against a null that keeps the base book and randomises only the
overlay's decisions, matched on how many it makes. For an EXIT overlay that means
cutting THE SAME NUMBER OF TRADES short at random points inside their own spans.
`run_risk_controls.overlay_null` is bar-level position scaling and does not do
this; `run_stops_targets`'s committed runner only ever called a ROTATION null,
whose p95 of -0.284 anything not actively harmful would clear. Written fresh here.

EFFICIENCY IS A DESIGN REQUIREMENT. The naive rolling OLS refits at every
(symbol, bar) -- 86k regressions. Instead every pivot deposits its
(1, x, y, x^2, xy) contribution at its own bar index, one cumulative sum turns
those into prefix sums, and a window sum is a single subtraction. O(T) per symbol,
vectorised over bars, measured at 0.2s for all 57.

STAGE 1 ONLY. The holdout 60 and the 2025-2026 forward window are not touched.

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


X = _load("d238_mirror", "run_short_mirror.py")
L, S, J = X.L, X.S, X.J

SUMMARY = REPO / "data" / "uptrend_onset_summary.json"
RESULTS = REPO / "docs" / "results" / "UPTREND_ONSET_RESULTS.md"

PPY, SEED, LAG = X.PPY, X.SEED, X.LAG
RF_ANNUAL, RF_PER_BAR = X.RF_ANNUAL, X.RF_PER_BAR
N_SIMS = X.N_SIMS

# Declared in D240. k is fixed by D173 and is not a free parameter.
K = 3
WINDOW = 252
MIN_PIVOTS = 3
AGE_CAP = 63              # one quarter, and where the measured decay crosses the market
ATR_WINDOW = 21
STOP_ATR = 1.0            # buffer below the line
FLOOR_ATR = 2.0           # amendment 2 -- never closer than this to entry
FIXED_STOP = 0.08         # A2
TARGET_R = 2.0            # A3, in units of the A1 stop distance

CELL_ORDER = ("A0", "A1", "A2", "A3", "A4")
OVERLAYS = ("A1", "A2", "A3", "A4")


# --------------------------------------------------------------------------
# The O(T) rolling regression
# --------------------------------------------------------------------------


def rolling_fit(n_bars: int, idx: np.ndarray, logpx: np.ndarray, k: int):
    """Rolling OLS slope AND intercept at every bar, O(T) via prefix sums.

    CAUSALITY. A pivot at index i is knowable only at i + k (D173, enforced by
    `Pivot.confirmed_at`), so the window usable at bar t is i in [t-WINDOW, t-k] --
    NOT [t-WINDOW, t]. In prefix form that is exactly P[t-k+1] - P[t-WINDOW]."""
    z = np.zeros(n_bars)
    cnt, sx, sy, sxx, sxy = (z.copy() for _ in range(5))
    if len(idx):
        x = idx.astype(float)
        for arr, val in ((cnt, 1.0), (sx, x), (sy, logpx), (sxx, x * x), (sxy, x * logpx)):
            np.add.at(arr, idx, val)
    P = [np.concatenate(([0.0], np.cumsum(a))) for a in (cnt, sx, sy, sxx, sxy)]

    t = np.arange(n_bars)
    hi = np.clip(t - k + 1, 0, n_bars)
    lo = np.clip(t - WINDOW, 0, n_bars)
    n, Sx, Sy, Sxx, Sxy = (p[hi] - p[lo] for p in P)
    den = n * Sxx - Sx * Sx
    good = (n >= MIN_PIVOTS) & (den > 0)
    with np.errstate(invalid="ignore", divide="ignore"):
        slope = np.where(good, (n * Sxy - Sx * Sy) / den, np.nan)
        inter = np.where(good, (Sy - slope * Sx) / np.where(n > 0, n, np.nan), np.nan)
    return slope, inter


def atr_log(bars, window: int) -> np.ndarray:
    """True range in LOG units, Wilder-smoothed. `M.smma` is reused rather than
    restated -- it is the same alpha = 1/n the Impulse legs use."""
    h = np.array([math.log(b.bar.high) for b in bars])
    lo = np.array([math.log(b.bar.low) for b in bars])
    c = np.array([math.log(b.bar.close) for b in bars])
    pc = np.concatenate(([c[0]], c[:-1]))
    tr = np.maximum(h - lo, np.maximum(np.abs(h - pc), np.abs(lo - pc)))
    return np.asarray(M.smma(list(tr), window), dtype=float)


def signals(panel, cleaned, start: int):
    n, T = panel.closes.shape
    g_lo = np.full((n, T), np.nan)
    g_hi = np.full((n, T), np.nan)
    i_lo = np.full((n, T), np.nan)
    atr = np.full((n, T), np.nan)
    for i, sym in enumerate(panel.symbols):
        ps = pivots(cleaned[sym], K)
        li = np.array([p.index for p in ps if p.sign < 0], dtype=int)
        hj = np.array([p.index for p in ps if p.sign > 0], dtype=int)
        g_lo[i], i_lo[i] = rolling_fit(
            T, li, np.log([p.price for p in ps if p.sign < 0]) if len(li) else np.array([]), K
        )
        g_hi[i], _ = rolling_fit(
            T, hj, np.log([p.price for p in ps if p.sign > 0]) if len(hj) else np.array([]), K
        )
        atr[i] = atr_log(cleaned[sym], ATR_WINDOW)
    ok = ~(np.isnan(g_lo) | np.isnan(g_hi) | np.isnan(atr))
    up = (g_lo > 0) & (g_hi > 0) & ok
    up[:, :start] = False
    return up, g_lo, i_lo, atr


# --------------------------------------------------------------------------
# The state machine
# --------------------------------------------------------------------------


def onsets(up: np.ndarray, start: int):
    """(symbol, onset bar) for the first bar of every uptrend episode."""
    prev = np.zeros_like(up)
    prev[:, 1:] = up[:, :-1]
    on = up & ~prev
    on[:, :start] = False
    return list(zip(*np.where(on)))


def walk(panel, up, g_lo, i_lo, atr, start, *, stop_mode=None, target=False):
    """Build the book one trade at a time.

    THE CONVENTION, and it decides every price in here: `position[t]` earns
    `log(C[t]/C[t-1])`, so a position held at bar `a` was bought at `C[a-1]`. Onset
    is detected at the close of `t0`, exposure therefore begins at `t0+1`, and the
    entry price is `C[t0]` -- which is also the last bar the frozen line and ATR may
    read. An exit decided at the close of `t` takes effect at `t+1`. Nothing reads a
    price it could not have seen."""
    n, T = panel.closes.shape
    logC = np.log(panel.closes)
    pos = np.zeros((n, T))
    cuts = []                      # (trade_index, fraction through the span)
    trades = []
    for tix, (i, t0) in enumerate(onsets(up, start)):
        entry = logC[i, t0]
        a = t0 + 1
        b = min(t0 + AGE_CAP, T - 1)          # last bar the age cap allows
        while b > a and not up[i, b - 1]:     # the state ended earlier
            b -= 1
        if b < a:
            continue
        # frozen at entry
        sl, ic, at = g_lo[i, t0], i_lo[i, t0], atr[i, t0]
        r_struct = entry - min(ic + sl * t0 - STOP_ATR * at, entry - FLOOR_ATR * at)
        tgt = entry + TARGET_R * r_struct

        exit_at = b
        for t in range(a, b + 1):
            hit = False
            if stop_mode == "struct":
                lvl = min(ic + sl * t - STOP_ATR * at, entry - FLOOR_ATR * at)
                hit = logC[i, t] < lvl
            elif stop_mode == "fixed":
                hit = logC[i, t] < entry + math.log1p(-FIXED_STOP)
            if not hit and target and logC[i, t] >= tgt:
                hit = True
            if hit:
                exit_at = t
                cuts.append((tix, (t - a) / max(b - a, 1)))
                break
        pos[i, a : exit_at + 1] = 1.0
        trades.append((i, a, b, r_struct))
    pos[:, :start] = 0.0
    return pos, trades, cuts


def null_book(panel, trades, n_cut, frac_pool, rng, start):
    """R7's control for an EXIT overlay: keep the base book, cut the SAME NUMBER of
    trades short, at random trades and at random points inside their own spans.

    Cut fractions are drawn from the real overlay's own pool, following D236's
    pattern of drawing magnitudes from the real distribution. That matches the
    amount of exposure removed in expectation, so what is left varying is only
    WHICH trades were cut and WHERE -- which is precisely the claim under test."""
    n, T = panel.closes.shape
    pos = np.zeros((n, T))
    chosen = set(rng.choice(len(trades), size=min(n_cut, len(trades)), replace=False)) \
        if n_cut else set()
    for tix, (i, a, b, _r) in enumerate(trades):
        e = b
        if tix in chosen:
            f = float(rng.choice(frac_pool))
            e = a + int(round(f * max(b - a, 1)))
            e = max(a, min(e, b))
        pos[i, a : e + 1] = 1.0
    pos[:, :start] = 0.0
    return pos


def build() -> dict:
    t0 = time.time()
    panel, cleaned = L.load_panel()
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)
    assert WINDOW < start, "the regression must be defined from the shared start bar"

    up, g_lo, i_lo, atr = signals(panel, cleaned, start)

    md, hs, ok0 = S.base_masks(panel, cleaned, start)
    s1 = S.hold_book((hs > 0) & (md <= 0) & ok0, start)

    specs = {
        "A0": dict(stop_mode=None, target=False),
        "A1": dict(stop_mode="struct", target=False),
        "A2": dict(stop_mode="fixed", target=False),
        "A3": dict(stop_mode=None, target=True),
        "A4": dict(stop_mode="struct", target=True),
    }
    books, cutinfo = {}, {}
    for k, kw in specs.items():
        p, trades, cuts = walk(panel, up, g_lo, i_lo, atr, start, **kw)
        books[k] = p
        cutinfo[k] = (trades, cuts)
    base_trades = cutinfo["A0"][0]

    ones = np.ones_like(s1)
    ones[:, :start] = 0.0
    cells = {k: X.score(panel, books[k], start) for k in CELL_ORDER}
    cells["S1"] = X.score(panel, s1, start)
    bh = X.score(panel, ones, start)
    assert abs(cells["S1"]["excess_sharpe"] - 0.746) < 5e-4, "S1 moved -- rho is void"

    def excess(pos):
        tot = X.signed_log_returns(panel, pos, total_return=True)[start:]
        return X.excess_of(tot, pos, start)

    r_s1 = excess(s1)
    sr_s1 = cells["S1"]["excess_sharpe"]

    # B -- the entry rule's own control, a rotation null on A0
    nl = X.rotation_nulls(panel, {"A0": books["A0"]}, start)
    d = nl["draws"]["A0"]
    rot = {
        "p50": float(np.percentile(d, 50)), "p95": float(np.percentile(d, 95)),
        "percentile_of_actual": float((d < cells["A0"]["excess_sharpe"]).mean() * 100.0),
        "money_percentile_of_actual": float(
            (nl["money"]["A0"] < cells["A0"]["total_return"]).mean() * 100.0
        ),
        "vol_ratio": float(cells["A0"]["vol"] / np.percentile(nl["vol"]["A0"], 50)),
        "clears_B": bool(cells["A0"]["excess_sharpe"] > float(np.percentile(d, 95))),
    }

    # A -- R7's matched-exit-count overlay null, one per overlay cell
    rng = np.random.default_rng(SEED)
    onull = {}
    for k in OVERLAYS:
        cuts = cutinfo[k][1]
        pool = np.array([f for _, f in cuts]) if cuts else np.array([1.0])
        draws = np.empty(N_SIMS)
        for s in range(N_SIMS):
            draws[s] = X._excess_sharpe(
                panel, null_book(panel, base_trades, len(cuts), pool, rng, start), start
            )
        actual = cells[k]["excess_sharpe"]
        onull[k] = {
            "n_cut": len(cuts), "n_trades": len(base_trades),
            "p50": float(np.percentile(draws, 50)), "p95": float(np.percentile(draws, 95)),
            "percentile_of_actual": float((draws < actual).mean() * 100.0),
            "clears_A": bool(actual > float(np.percentile(draws, 95))),
        }

    # C -- the diversification condition
    p1 = {}
    for k in CELL_ORDER:
        rho = float(np.corrcoef(r_s1, excess(books[k]))[0, 1])
        p1[k] = {"rho": rho, "bar": rho * sr_s1, "actual": cells[k]["excess_sharpe"],
                 "clears_C": bool(cells[k]["excess_sharpe"] > rho * sr_s1)}

    bh_sh = bh["excess_sharpe"]
    sqrt_f = {}
    for k in CELL_ORDER:
        f = cells[k]["exposure_gross"]
        pred = bh_sh * math.sqrt(f) if f > 0 else 0.0
        sqrt_f[k] = {"exposure": f, "prediction": pred,
                     "selection_quality": (cells[k]["excess_sharpe"] / pred - 1.0) if pred else None}

    # Block bootstrap. NOT a registered hurdle -- D240 omitted one, which was a gap
    # given D230 (8 deltas cleared as scored, ZERO as claimed once the bootstrap leg
    # was built). Computed as a diagnostic so nobody reads a point estimate as a
    # result. Paired: every arm is recomputed on the SAME resampled dates.
    rng_b = np.random.default_rng(SEED)
    nlen = len(r_s1)
    nblk = math.ceil(nlen / J.BLOCK)
    idxs = [(rng_b.integers(0, nlen - J.BLOCK + 1, size=nblk)[:, None]
             + np.arange(J.BLOCK)[None, :]).ravel()[:nlen] for _ in range(J.N_BOOT)]

    def _sh(v):
        sd = float(np.std(v, ddof=1))
        return float(np.mean(v) / sd * math.sqrt(PPY)) if sd > 0 else 0.0

    r_bh = excess(ones)
    boot = {}
    for k in list(CELL_ORDER) + ["S1"]:
        v = r_s1 if k == "S1" else excess(books[k])
        own = np.array([_sh(v[i]) for i in idxs])
        dlt = np.array([_sh(v[i]) - _sh(r_bh[i]) for i in idxs])
        boot[k] = {
            "sharpe_p05": float(np.percentile(own, 5)),
            "sharpe_p95": float(np.percentile(own, 95)),
            "sharpe_excludes_zero": bool(np.percentile(own, 5) > 0.0),
            "delta_vs_bh": _sh(v) - _sh(r_bh),
            "delta_p05": float(np.percentile(dlt, 5)),
            "delta_p95": float(np.percentile(dlt, 95)),
            "delta_excludes_zero": bool(np.percentile(dlt, 5) > 0.0),
        }

    # The combined-book arithmetic. Closed form on numbers already computed -- NOT a
    # new book and NOT a cell. Adding arm B raises the maximum attainable Sharpe to
    # sqrt((Sa^2 + Sb^2 - 2*rho*Sa*Sb) / (1 - rho^2)).
    def _yrs(sr):
        return (1.96 ** 2) * (1 + sr * sr / 2) / (sr * sr) if sr > 0 else float("inf")
    combined = {"S1_alone": {"sharpe": sr_s1, "years_to_significance": _yrs(sr_s1)}}
    for k in CELL_ORDER:
        sb, rho = cells[k]["excess_sharpe"], p1[k]["rho"]
        cb = math.sqrt(max(sr_s1 ** 2 + sb ** 2 - 2 * rho * sr_s1 * sb, 0.0) / (1 - rho ** 2))
        combined[f"S1_plus_{k}"] = {"sharpe": cb, "gain": cb - sr_s1,
                                    "years_to_significance": _yrs(cb)}

    # diagnostics, not cells
    rs = np.array([t[3] for t in base_trades])
    diag = {
        "n_onsets": len(base_trades),
        "r_distribution": {f"p{q}": float(np.expm1(np.percentile(rs, q)))
                           for q in (5, 25, 50, 75, 95)},
        "r_dispersion_ratio": float(np.percentile(rs, 95) / max(np.percentile(rs, 5), 1e-12)),
        "entries_per_symbol_min": cells["A0"]["min_entries_per_symbol"],
        "age_cap": AGE_CAP,
    }

    return {
        "produced": "D240",
        "stage": "screen (mined 57) -- the holdout and forward window are untouched",
        "seed": SEED, "n_sims": N_SIMS,
        "k": K, "window": WINDOW, "age_cap": AGE_CAP, "atr_window": ATR_WINDOW,
        "stop_atr": STOP_ATR, "floor_atr": FLOOR_ATR,
        "fixed_stop": FIXED_STOP, "target_r": TARGET_R,
        "n_symbols": len(panel.symbols), "live_bars": len(panel.dates) - start,
        "first_live_date": panel.dates[start], "last_date": panel.dates[-1],
        "cells": cells, "buy_and_hold": bh,
        "deployable_return": {
            k: float(np.expm1(np.log1p(cells[k]["cagr"])
                              + math.log1p(RF_ANNUAL) * (1 - cells[k]["exposure_gross"])))
            for k in list(CELL_ORDER) + ["S1"]
        },
        "rotation_null_A0": rot, "overlay_nulls": onull, "p1": p1, "sqrt_f": sqrt_f,
        "bootstrap": boot, "combined": combined, "diagnostics": diag,
        "elapsed_seconds": round(time.time() - t0, 1),
    }


def render(p: dict) -> str:
    c, dep, sf = p["cells"], p["deployable_return"], p["sqrt_f"]
    b, rot, on, p1, dg = (p["buy_and_hold"], p["rotation_null_A0"], p["overlay_nulls"],
                          p["p1"], p["diagnostics"])
    names = {"A0": "base — onset + age cap", "A1": "+ structural sloped stop",
             "A2": "+ fixed −8% stop", "A3": "+ target at +2R", "A4": "+ stop and target"}
    o = ["# D240 — the uptrend-onset arm, with stops and targets\n"]
    o.append(f"**STAGE 1 — A SCREEN, NOT A VERDICT.** {p['stage']}\n")
    o.append(
        f"*seed {p['seed']}, {p['n_sims']:,} sims, {p['elapsed_seconds']}s. "
        f"{p['n_symbols']} ETFs x {p['live_bars']:,} live bars, "
        f"{p['first_live_date'][:10]} .. {p['last_date'][:10]}. "
        f"k={p['k']}, window {p['window']}, age cap {p['age_cap']}, "
        f"ATR({p['atr_window']}), stop {p['stop_atr']:g}xATR, floor {p['floor_atr']:g}xATR.*\n"
    )
    o.append("## The cells\n")
    o.append("| | | exposure | excess Sharpe | CAGR | **deployable** | vol | max DD | Calmar | E |")
    o.append("|---|---|---:|---:|---:|---:|---:|---:|---:|:--:|")
    for k in CELL_ORDER:
        x = c[k]
        cal = x["cagr"] / abs(x["max_drawdown"]) if x["max_drawdown"] else float("nan")
        o.append(
            f"| **{k}** | {names[k]} | {x['exposure_gross']:.1%} | "
            f"**{x['excess_sharpe']:+.3f}** | {x['cagr'] * 100:.2f}% | "
            f"**{dep[k] * 100:.2f}%** | {x['vol'] * 100:.1f}% | "
            f"{x['max_drawdown'] * 100:+.2f}% | {cal:.3f} | "
            f"{'✓' if x['clears_E'] else '✗'} |"
        )
    for lab, x, dd in (("S1", c["S1"], dep["S1"]), ("B&H", b, b["cagr"])):
        cal = x["cagr"] / abs(x["max_drawdown"])
        o.append(
            f"| *{lab}* | *for scale* | *{x['exposure_gross']:.1%}* | "
            f"*{x['excess_sharpe']:+.3f}* | *{x['cagr'] * 100:.2f}%* | *{dd * 100:.2f}%* | "
            f"*{x['vol'] * 100:.1f}%* | *{x['max_drawdown'] * 100:+.2f}%* | *{cal:.3f}* | — |"
        )
    o.append("")

    o.append("## A — R7's matched-exit-count overlay null, which carries the overlay verdict\n")
    o.append(
        "*Keep A0's book; cut **the same number of trades** short at random trades and random "
        "points inside their own spans, with cut fractions drawn from the real overlay's own "
        "pool. What varies is only **which** trades and **where** — the claim under test.*\n"
    )
    o.append("| | trades cut | actual | null p50 | null p95 | **percentile** | A |")
    o.append("|---|---:|---:|---:|---:|---:|:--:|")
    for k in OVERLAYS:
        n = on[k]
        o.append(
            f"| **{k}** | {n['n_cut']} of {n['n_trades']} | "
            f"**{c[k]['excess_sharpe']:+.3f}** | {n['p50']:+.3f} | {n['p95']:+.3f} | "
            f"**{n['percentile_of_actual']:.1f}th** | {'✓' if n['clears_A'] else '✗'} |"
        )
    o.append("")

    o.append("## B — the rotation null on the entry rule\n")
    o.append(
        f"| | actual | null p50 | null p95 | percentile | money pct | vol ratio | B |\n"
        f"|---|---:|---:|---:|---:|---:|---:|:--:|\n"
        f"| **A0** | **{c['A0']['excess_sharpe']:+.3f}** | {rot['p50']:+.3f} | "
        f"{rot['p95']:+.3f} | **{rot['percentile_of_actual']:.1f}th** | "
        f"{rot['money_percentile_of_actual']:.1f}th | {rot['vol_ratio']:.3f}x | "
        f"{'✓' if rot['clears_B'] else '✗'} |\n"
    )

    o.append("## C — the diversification condition, which decides whether this is arm two\n")
    o.append("*Adding an arm raises the book's maximum attainable Sharpe iff `SR_B > ρ · SR_S1`.*\n")
    o.append("| | ρ with S1 | bar `ρ × 0.746` | actual | C |")
    o.append("|---|---:|---:|---:|:--:|")
    for k in CELL_ORDER:
        q = p1[k]
        o.append(f"| **{k}** | {q['rho']:+.4f} | {q['bar']:+.3f} | **{q['actual']:+.3f}** | "
                 f"{'✓' if q['clears_C'] else '✗'} |")
    o.append("")

    o.append("## D — versus buy-and-hold, with the √f decomposition\n")
    o.append("| | exposure | √f predicts | actual | selection quality | beats B&H |")
    o.append("|---|---:|---:|---:|---:|:--:|")
    for k in CELL_ORDER:
        q = sf[k]
        sq = f"{q['selection_quality'] * 100:+.1f}%" if q["selection_quality"] is not None else "—"
        o.append(f"| **{k}** | {q['exposure']:.1%} | {q['prediction']:+.3f} | "
                 f"{c[k]['excess_sharpe']:+.3f} | **{sq}** | "
                 f"{'✓' if c[k]['excess_sharpe'] > b['excess_sharpe'] else '✗'} |")
    o.append("")

    o.append("## Bootstrap — NOT a registered hurdle, and that was a gap\n")
    o.append(
        "*D240 registered no bootstrap. Given D230 — where 8 deltas cleared as scored and "
        "**zero** cleared as claimed once the leg was built — that was an omission, so it is "
        "computed here as a diagnostic. Block 21, paired on identical resampled dates.*\n"
    )
    bt = p["bootstrap"]
    o.append("| | excess Sharpe | p05 | p95 | excludes 0 | Δ vs B&H | p05 | p95 | excludes 0 |")
    o.append("|---|---:|---:|---:|:--:|---:|---:|---:|:--:|")
    for k in list(CELL_ORDER) + ["S1"]:
        q = bt[k]
        o.append(
            f"| **{k}** | {c[k]['excess_sharpe']:+.3f} | {q['sharpe_p05']:+.3f} | "
            f"{q['sharpe_p95']:+.3f} | {'✓' if q['sharpe_excludes_zero'] else '✗'} | "
            f"{q['delta_vs_bh']:+.3f} | {q['delta_p05']:+.3f} | {q['delta_p95']:+.3f} | "
            f"{'✓' if q['delta_excludes_zero'] else '✗'} |"
        )
    o.append("")

    o.append("## What the pairing would be worth\n")
    o.append(
        "*Closed form on numbers already in the table — **not a new book and not a cell.** "
        "Adding arm B raises the maximum attainable Sharpe to "
        "`sqrt((Sa² + Sb² − 2ρSaSb) / (1 − ρ²))`.*\n"
    )
    cm = p["combined"]
    o.append("| pairing | combined Sharpe | gain over S1 | years to significance |")
    o.append("|---|---:|---:|---:|")
    o.append(f"| S1 alone | {cm['S1_alone']['sharpe']:.3f} | — | "
             f"{cm['S1_alone']['years_to_significance']:.1f}y |")
    for k in CELL_ORDER:
        q = cm[f"S1_plus_{k}"]
        o.append(f"| **S1 + {k}** | **{q['sharpe']:.3f}** | {q['gain']:+.3f} | "
                 f"**{q['years_to_significance']:.1f}y** |")
    o.append("")

    o.append("## Diagnostics — reported, never hurdles\n")
    rd = dg["r_distribution"]
    o.append(
        f"**{dg['n_onsets']} onsets**, {dg['entries_per_symbol_min']} minimum entries per symbol "
        f"against the 30 hurdle E requires.\n"
    )
    o.append("**The R dispersion amendment 2 flagged**, measured:\n")
    o.append("| p5 | p25 | p50 | p75 | p95 | p95/p5 |")
    o.append("|---:|---:|---:|---:|---:|---:|")
    o.append(f"| {rd['p5']:.2%} | {rd['p25']:.2%} | **{rd['p50']:.2%}** | {rd['p75']:.2%} | "
             f"{rd['p95']:.2%} | **{dg['r_dispersion_ratio']:.1f}x** |")
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

    c, dep, on, p1 = (payload["cells"], payload["deployable_return"],
                      payload["overlay_nulls"], payload["p1"])
    print()
    print(f"{'cell':5s} {'expo':>7s} {'exSh':>8s} {'CAGR':>8s} {'deploy':>8s} {'maxDD':>8s} "
          f"{'rho':>7s} {'bar':>7s}  C   {'ovl pct':>8s}  A")
    for k in CELL_ORDER:
        x, q = c[k], p1[k]
        n = on.get(k)
        print(f"{k:5s} {x['exposure_gross']:7.1%} {x['excess_sharpe']:+8.3f} {x['cagr']:8.2%} "
              f"{dep[k]:8.2%} {x['max_drawdown']:+8.2%} {q['rho']:+7.3f} {q['bar']:+7.3f}  "
              f"{'Y' if q['clears_C'] else 'N'}   "
              + (f"{n['percentile_of_actual']:7.1f}th  {'Y' if n['clears_A'] else 'N'}"
                 if n else f"{'—':>8s}   -"))
    print(f"{'S1':5s} {c['S1']['exposure_gross']:7.1%} {c['S1']['excess_sharpe']:+8.3f} "
          f"{c['S1']['cagr']:8.2%} {dep['S1']:8.2%} {c['S1']['max_drawdown']:+8.2%}")
    b = payload["buy_and_hold"]
    print(f"{'B&H':5s} {100.0:6.1f}% {b['excess_sharpe']:+8.3f} {b['cagr']:8.2%} "
          f"{b['cagr']:8.2%} {b['max_drawdown']:+8.2%}")
    r = payload["rotation_null_A0"]
    print(f"\nB (entry rotation null): A0 at {r['percentile_of_actual']:.1f}th percentile, "
          f"money {r['money_percentile_of_actual']:.1f}th -> "
          f"{'CLEARS' if r['clears_B'] else 'FAILS'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
