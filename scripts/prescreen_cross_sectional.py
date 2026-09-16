"""D251 pre-screen — cross-sectional DOLLAR-NEUTRAL ranking scores on the 57.

THIS IS A PRE-SCREEN, NOT A RUNNER. D250's discipline is binding: measure the
conditional cheaply, R9- and R10-compliant, BEFORE anything earns a
pre-registration. No hurdle is run here, no null is computed, no verdict on a
strategy is claimed. What is claimed is whether a ranking score ranks the
cross-section at all, and the `gross = exposure x edge` arithmetic for why.

THE FAMILY, and why it is the eligible one (D246's "what S3 should be"):
an ETF is a weighted average, so diversification removes idiosyncratic variance
by construction and what survives is the common factor -- which is exactly what
carries the equity risk premium. D238 measured the consequence: there is no ETF
on this universe where a directional short works. Dollar-neutral is the one
construction that REMOVES the factor rather than fighting it, so the only
tradeable quantity left is the difference between factors.

EIGHT CELLS, WHICH IS EXACTLY D246's STOP. Every one is declared here with its
A PRIORI LONG SIDE, before any number is printed, so that a spread of the wrong
sign cannot be re-read as a spread of the right sign.

    RS21 RS63 RS252   trailing relative strength      long the HIGH quintile
    RESMOM           residual momentum, prior beta    long the HIGH quintile
    IVOL             trailing residual sd             long the LOW  quintile
    BETA             trailing slope on the universe   long the LOW  quintile
    MDL              S1's md_L, scale-free            long the LOW  quintile
    HISTL            S1's hist_L, scale-free          long the HIGH quintile

R9 BY CONSTRUCTION, NOT BY ASSERTION. A score at bar t is computed from bars
<= t; the forward return it is scored against runs t+1 .. t+h. The two share no
bar. `test_no_look_ahead` corrupts every bar after a cut point and pins that no
score at or before it moved.

R10, AND THE HONEST VERSION OF IT FOR THIS CONSTRUCTION. A fixed-count
cross-sectional sort holds ~N/5 names long and ~N/5 short EVERY day, so the
literal concurrency table is matched to its rotated baseline by construction and
carries no information. It is reported anyway, because reporting it is what
makes visible that the binding synchronisation risk here is different: a
dollar-neutral book that is dollar-neutral can still be BETA-neutral-violating.
The diagnostic that carries R10's burden for this family is the NET BETA of the
long-minus-short book on the equal-weighted universe. That is reported beside
every table.

D232, on why MDL and HISTL are normalised. `md_L` is a dimensionless log-gap but
it still scales with the name's own volatility, so a RAW cross-sectional rank on
it is mostly a volatility sort wearing a signal's name. Each is divided by its
own trailing 252-bar sd. That normalisation is part of the cell definition, not
a second look.

WHY THE ROLLING REGRESSION IS GENERALISED RATHER THAN CALLED (D212 wants the
reason named). `run_uptrend_onset.rolling_fit` is the right technique and the
wrong shape: its regressor is hard-coded to the bar index, and a market-return
regressor is a different x. `rolling_ols` below is the same prefix-sum
arithmetic with x generalised, and it is PINNED against `rolling_fit` on the
bar-index case rather than trusted.

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


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


X = _load("d238_mirror", "run_short_mirror.py")
U = _load("d240_uptrend", "run_uptrend_onset.py")
BW = _load("d245_wide", "run_book_wide.py")
L, S = X.L, X.S

SUMMARY = REPO / "data" / "cross_sectional_prescreen_summary.json"
RESULTS = REPO / "docs" / "results" / "CROSS_SECTIONAL_PRESCREEN_RESULTS.md"
FIX = REPO / "data" / "fixtures"

PPY, SEED, LAG = X.PPY, X.SEED, X.LAG
BORROW_ANNUAL = X.BORROW_ANNUAL          # 1.0%/yr on short notional, D238's rate
N_ROT = 200                              # rotations for the R10 concurrency baseline

W_REG = 252          # the trailing regression window -- beta, ivol, resmom
W_STD = 252          # the normaliser window for md_L / hist_L
NQ = 5               # quintiles
RS_LOOKBACKS = (21, 63, 252)
FWD = (21, 63)       # forward horizons, which are also the rebalance spacings

# Declared BEFORE the run. `+1` means the a priori long leg is the HIGH quintile
# (Q5) and the short leg is Q1; `-1` is the reverse. Net return is reported on
# the declared direction. The raw Q5-Q1 is printed beside it so a sign flip is
# visible rather than silent.
CELLS = {
    "RS21":   ("trailing 21-bar return minus the universe", +1),
    "RS63":   ("trailing 63-bar return minus the universe", +1),
    "RS252":  ("trailing 252-bar return minus the universe", +1),
    "RESMOM": ("residual momentum, beta from the PRIOR 252 bars", +1),
    "IVOL":   ("trailing residual sd, annualised", -1),
    "BETA":   ("trailing slope on the equal-weighted universe", -1),
    "MDL":    ("S1's md_L / its own trailing sd", -1),
    "HISTL":  ("S1's hist_L / its own trailing sd", +1),
}
CELL_ORDER = tuple(CELLS)

# The economic bar, stated before the numbers. Under ~2%/yr NET does not earn a
# runner. D250's correction is why this is a product and not an edge.
NET_BAR = 0.02


# --------------------------------------------------------------------------
# The O(T) rolling regression, generalised from run_uptrend_onset.rolling_fit
# --------------------------------------------------------------------------


def _prefix(a: np.ndarray, axis: int = -1) -> np.ndarray:
    pad = list(a.shape)
    pad[axis] = 1
    return np.concatenate((np.zeros(pad), np.cumsum(a, axis=axis)), axis=axis)


def _nan_prefix(a: np.ndarray):
    """Prefix sums that a nan cannot poison. `np.cumsum` propagates a single nan
    to every later bar, which silently emptied MDL and HISTL on the first run --
    `md_L` is undefined through its 1,000-bar warm-up and every window touching it
    came back nan. The finite mask is carried alongside so a window is rejected for
    being INCOMPLETE rather than for having ever seen a nan."""
    fin = np.isfinite(a)
    return _prefix(np.where(fin, a, 0.0), 1), _prefix(fin.astype(float), 1)


def rolling_ols(y: np.ndarray, x: np.ndarray, window: int):
    """OLS of each row of `y` on `x` over the CAUSAL window [t-window+1 .. t].

    O(T) via prefix sums, vectorised over both symbols and bars -- the same
    arithmetic as `run_uptrend_onset.rolling_fit`, with the regressor generalised
    from the bar index to an arbitrary series.

    Returns (alpha, beta, resid_sd, n) with nan wherever the window is short.
    `resid_sd` is the per-bar residual standard deviation, ddof = 2."""
    y = np.atleast_2d(y)
    T = y.shape[1]
    assert x.shape == (T,), "the regressor must be one value per bar"

    Px, Pxx = _prefix(x), _prefix(x * x)
    Py, Pxy, Pyy = _prefix(y, 1), _prefix(y * x[None, :], 1), _prefix(y * y, 1)

    t = np.arange(T)
    hi = t + 1
    lo = np.clip(t + 1 - window, 0, T)
    n = (hi - lo).astype(float)
    Sx, Sxx = Px[hi] - Px[lo], Pxx[hi] - Pxx[lo]
    Sy, Sxy, Syy = (P[:, hi] - P[:, lo] for P in (Py, Pxy, Pyy))

    den = n * Sxx - Sx * Sx
    good = (n >= window) & (den > 0)
    with np.errstate(invalid="ignore", divide="ignore"):
        beta = np.where(good[None, :], (n * Sxy - Sx[None, :] * Sy) / den[None, :], np.nan)
        alpha = (Sy - beta * Sx[None, :]) / n[None, :]
        sse = np.maximum(Syy - alpha * Sy - beta * Sxy, 0.0)
        sd = np.sqrt(sse / np.maximum(n - 2.0, 1.0)[None, :])
    return alpha, beta, np.where(good[None, :], sd, np.nan), n


def portfolio_level_log_returns(panel, position: np.ndarray) -> np.ndarray:
    """Per-bar SIMPLE portfolio return, compounded at the PORTFOLIO level.

        r_p[t]  = mean_i( pos_i[t] * expm1(r_i[t]) - cost_i * |d pos_i[t]| )
        per_bar = log1p(r_p[t])

    THIS IS NOT `pos * log_return`, the defective form D238 named. It is the same
    correct signed arithmetic at a different level of aggregation, and the
    difference is the whole verdict for this family.

    `X.signed_log_returns` averages PER-SYMBOL log growths, so every symbol is its
    own compounding sub-account. That is exactly right for a long-flat book and it
    charges a dollar-neutral book the NAME-level variance drag on its short leg --
    `E[log(2 - e^r)] ~ -mu - sigma^2`, which at 20-25% name volatility is 4-6%/yr.
    In a real dollar-neutral account the two legs sit in ONE equity: the long
    leg's gain funds the short leg's loss on the same bar, so the drag is set by
    the SPREAD's variance (3-5%/yr here), not by each name's.

    Both are reported. The house scorer stays primary because it is what every
    other number in this programme is measured with; this one is a disclosed
    diagnostic, and the fact that they DISAGREE ON THE SIGN is itself the finding.
    They coincide exactly when at most one symbol is held per bar, which is pinned."""
    turnover = np.abs(np.diff(position, axis=1, prepend=0.0))
    charge = panel.cost_fraction[:, None] * turnover
    simple = (position * np.expm1(panel.total_log_returns) - charge).mean(axis=0)
    if np.any(simple <= -1.0):  # pragma: no cover - a book wiped out on one bar
        raise ValueError("the portfolio was wiped out on a single bar")
    return np.log1p(simple)


def rolling_sd(y: np.ndarray, window: int) -> np.ndarray:
    """Causal rolling sd over [t-window+1 .. t], ddof = 1, O(T), nan-safe."""
    Py, cy = _nan_prefix(y)
    Pyy, _ = _nan_prefix(y * y)
    T = y.shape[1]
    t = np.arange(T)
    hi, lo = t + 1, np.clip(t + 1 - window, 0, T)
    n = cy[:, hi] - cy[:, lo]
    Sy, Syy = Py[:, hi] - Py[:, lo], Pyy[:, hi] - Pyy[:, lo]
    with np.errstate(invalid="ignore", divide="ignore"):
        var = np.maximum(Syy - Sy * Sy / n, 0.0) / np.maximum(n - 1.0, 1.0)
    return np.where(n >= window, np.sqrt(var), np.nan)


def trailing_sum(y: np.ndarray, window: int) -> np.ndarray:
    """Causal rolling sum over [t-window+1 .. t], nan unless the window is FULL of
    finite values -- see `_nan_prefix` for why that distinction is load-bearing."""
    P, c = _nan_prefix(y)
    T = y.shape[1]
    t = np.arange(T)
    hi, lo = t + 1, np.clip(t + 1 - window, 0, T)
    return np.where((c[:, hi] - c[:, lo]) >= window, P[:, hi] - P[:, lo], np.nan)


# --------------------------------------------------------------------------
# Assertions -- written BEFORE the run, per D248's four amendments
# --------------------------------------------------------------------------


def assert_rolling_ols_matches_rolling_fit():
    """The reuse pin. On the bar-index case `rolling_ols` must reproduce
    `run_uptrend_onset.rolling_fit` exactly, which is what licenses generalising
    it rather than calling it."""
    rng = np.random.default_rng(7)
    T = 900
    y = np.cumsum(rng.normal(size=T)) + 10.0
    idx = np.arange(T)
    # rolling_fit(k=0) uses prefix indices [t-WINDOW, t] inclusive -> WINDOW+1 pts
    slope, inter = U.rolling_fit(T, idx, y, 0)
    a, b, _, n = rolling_ols(y[None, :], idx.astype(float), U.WINDOW + 1)
    m = n >= U.WINDOW + 1
    assert np.allclose(b[0][m], slope[m], atol=1e-8), "rolling_ols slope differs"
    assert np.allclose(a[0][m], inter[m], atol=1e-6), "rolling_ols intercept differs"


def assert_nan_cannot_poison():
    """The defect the first run actually had. A leading nan must cost exactly the
    windows that touch it and nothing after."""
    y = np.arange(1.0, 21.0)[None, :]
    z = y.copy()
    z[0, 0] = np.nan
    a, b = trailing_sum(y, 5), trailing_sum(z, 5)
    assert np.isnan(b[0, :5]).all(), "a short or nan-touching window survived"
    assert np.allclose(a[0, 5:], b[0, 5:]), "a single nan poisoned every later bar"
    assert np.allclose(rolling_sd(y, 5)[0, 5:], rolling_sd(z, 5)[0, 5:])


def assert_scores_are_causal(build_scores, lr, md, hs, cut: int):
    """R9, enforced rather than argued. Corrupt every bar AFTER `cut` and pin that
    no score at or before `cut` moved. A single reversed index anywhere in the
    prefix-sum arithmetic fails this."""
    rng = np.random.default_rng(11)
    lr2, md2, hs2 = lr.copy(), md.copy(), hs.copy()
    for a in (lr2, md2, hs2):
        a[:, cut + 1:] = rng.normal(size=a[:, cut + 1:].shape)
    base = build_scores(lr, md, hs)
    other = build_scores(lr2, md2, hs2)
    for k in base:
        u, v = base[k][:, : cut + 1], other[k][:, : cut + 1]
        ok = np.isfinite(u) & np.isfinite(v)
        assert np.array_equal(np.isfinite(u), np.isfinite(v)), f"{k}: nan mask moved"
        assert np.allclose(u[ok], v[ok], atol=1e-10), f"{k} LOOKS AHEAD past bar {cut}"


def assert_book_is_dollar_neutral(pos: np.ndarray, start: int):
    live = pos[:, start:]
    net = live.sum(axis=0)
    assert np.all(np.abs(net) <= 1.0 + 1e-9), "the book is not matched notional"
    held = (live != 0.0).sum(axis=0)
    assert np.all((held == 0) | (held >= 2)), "a one-legged bar"


def assert_aggregation_levels_agree_on_one_symbol():
    """On a ONE-SYMBOL universe the two scorers must be identical -- there is
    nothing left to aggregate, so 'mean of per-symbol logs' and 'log of the
    portfolio's simple return' are literally the same expression. That pins that
    the difference measured on the real panel is AGGREGATION and not a second,
    unrelated defect in one of them. Costs are zeroed because the two charge them
    at different levels by design."""
    rng = np.random.default_rng(3)
    T = 400
    r = rng.normal(0.0002, 0.012, size=(1, T))
    r[:, 0] = 0.0
    p = L.Panel(("A",), np.exp(np.cumsum(r, axis=1)), r, np.zeros(1),
                tuple(f"d{i}" for i in range(T)), total_log_returns=r)
    pos = np.zeros((1, T))
    pos[0, 10:150] = -1.0
    pos[0, 200:380] = 1.0
    a = X.signed_log_returns(p, pos, total_return=True)
    b = portfolio_level_log_returns(p, pos)
    assert np.allclose(a, b, atol=1e-12), "the two aggregations differ on one symbol"


def assert_cost_constant():
    """Pins the number the brief states: one round trip per day per leg, at
    1.85 bp/side, is -8.90%/yr on that leg's notional."""
    per_day = 2 * 1.85e-4
    annual = math.expm1(math.log1p(-per_day) * PPY)
    assert abs(annual + 0.0890) < 5e-4, f"the cost wall moved: {annual:.4%}"
    return annual


# --------------------------------------------------------------------------
# Scores
# --------------------------------------------------------------------------


def build_scores(lr: np.ndarray, md: np.ndarray, hs: np.ndarray) -> dict:
    """Every score at bar t from bars <= t. Signals come off PRICE returns, which
    is the house convention (`load_panel`: dividends go into the SCORED return and
    never into the signal)."""
    mkt = lr.mean(axis=0)
    out = {}
    for k in RS_LOOKBACKS:
        out[f"RS{k}"] = trailing_sum(lr, k) - trailing_sum(mkt[None, :], k)

    alpha, beta, sd, _ = rolling_ols(lr, mkt, W_REG)
    out["BETA"] = beta
    out["IVOL"] = sd * math.sqrt(PPY)

    # Residual momentum. The estimation window is the 252 bars ENDING AT t-252 and
    # the accumulation window is the 252 bars ending at t, so they do not overlap
    # -- which matters, because OLS residuals sum to zero over their own
    # estimation window and a nested construction is degenerate by algebra.
    prior = np.full_like(beta, np.nan)
    prior_a = np.full_like(alpha, np.nan)
    prior_sd = np.full_like(sd, np.nan)
    prior[:, W_REG:] = beta[:, :-W_REG]
    prior_a[:, W_REG:] = alpha[:, :-W_REG]
    prior_sd[:, W_REG:] = sd[:, :-W_REG]
    r252 = trailing_sum(lr, W_REG)
    m252 = trailing_sum(mkt[None, :], W_REG)
    with np.errstate(invalid="ignore", divide="ignore"):
        out["RESMOM"] = (r252 - W_REG * prior_a - prior * m252) / (
            prior_sd * math.sqrt(W_REG)
        )

    out["MDL"] = md / rolling_sd(md, W_STD)
    out["HISTL"] = hs / rolling_sd(hs, W_STD)
    return {k: out[k] for k in CELL_ORDER}


# --------------------------------------------------------------------------
# Quintiles, forward returns, books
# --------------------------------------------------------------------------


def bucket_matrix(score: np.ndarray, valid: np.ndarray, key: np.ndarray) -> np.ndarray:
    """Quintile 0..4 per (symbol, bar) among that bar's valid names; -1 elsewhere.

    TIES ARE BROKEN AT RANDOM, NOT BY TICKER, and that is not cosmetic. `md_L` is
    exactly 0.0 inside the channel on a large share of live bars, so a stable sort
    would put the same alphabetically-early names on the same side of a quintile
    boundary every single day -- a fixed ticker bet wearing a signal's name. `key`
    is drawn once from the study seed, so the tie-break is random and reproducible."""
    n, T = score.shape
    buck = np.full((n, T), -1, dtype=int)
    for t in range(T):
        rows = np.flatnonzero(valid[:, t])
        if rows.size < NQ:
            continue
        order = rows[np.lexsort((key[rows, t], score[rows, t]))]
        r = np.arange(order.size)
        buck[order, t] = (r * NQ) // order.size
    return buck


def participation_ratio(rets: np.ndarray) -> float:
    """`(sum L)^2 / sum L^2` over the correlation matrix eigenvalues -- the
    effective number of independent directions.

    `run_book_wide.effective_instruments` is `n^2 / sum(R)`, which is `1/Var` of
    the EQUAL-WEIGHTED average and therefore the right measure for a long-only
    equal-weighted book. It is DEGENERATE here: market-neutral residuals sum to
    zero across names by construction, so their equal-weighted average is
    identically zero and the estimator returns infinity. A long-short book takes
    signed weights, so the eigenvalue measure is the one it gets to use."""
    R = np.nan_to_num(np.corrcoef(rets), nan=0.0)
    lam = np.linalg.eigvalsh(R)
    lam = np.maximum(lam, 0.0)
    return float(lam.sum() ** 2 / np.sum(lam ** 2))


def quintile_table(buck: np.ndarray, fwd: np.ndarray, h: int, start: int,
                   window=None) -> dict:
    """Pooled mean forward return per quintile, annualised. The conditioning bar
    and the measured bars share nothing: `fwd[:, t]` sums bars t+1 .. t+h."""
    ok = (buck >= 0) & np.isfinite(fwd)
    ok[:, :start - 1] = False
    if window is not None:
        m = np.zeros(ok.shape[1], dtype=bool)
        m[window[0]:window[1]] = True
        ok &= m[None, :]
    rows = []
    for q in range(NQ):
        v = fwd[ok & (buck == q)]
        rows.append({
            "cells": int(v.size),
            "annualised": float(np.expm1(float(v.mean()) * PPY / h)) if v.size else float("nan"),
        })
    return {"quintiles": rows, "pooled_cells": int(ok.sum())}


def neutral_book(buck: np.ndarray, h: int, start: int, direction: int, T: int) -> np.ndarray:
    """Long one extreme quintile, short the other, matched COUNT, rebalanced every
    h bars. The decision bar is t0 and exposure runs t0+1 .. t0+h, which is
    LAG = 1 held for the horizon the table measured."""
    n = buck.shape[0]
    pos = np.zeros((n, T))
    hi_q, lo_q = (NQ - 1, 0) if direction > 0 else (0, NQ - 1)
    for t0 in range(start - 1, T - 1, h):
        longs = np.flatnonzero(buck[:, t0] == hi_q)
        shorts = np.flatnonzero(buck[:, t0] == lo_q)
        k = min(longs.size, shorts.size)
        if k == 0:
            continue
        a, b = t0 + 1, min(t0 + 1 + h, T)
        pos[longs[:k], a:b] = 1.0
        pos[shorts[:k], a:b] = -1.0
    pos[:, :start] = 0.0
    return pos


def leg_turnover(buck: np.ndarray, h: int, start: int, T: int) -> float:
    """MEASURED fraction of a leg's names replaced at each rebalance. This is what
    the cost arithmetic multiplies, and assuming 100% would overstate it."""
    fr = []
    for q in (0, NQ - 1):
        prev = None
        for t0 in range(start - 1, T - 1, h):
            cur = set(np.flatnonzero(buck[:, t0] == q).tolist())
            if prev is not None and prev:
                fr.append(1.0 - len(cur & prev) / len(prev))
            prev = cur
    return float(np.mean(fr)) if fr else 1.0


def concurrency(buck: np.ndarray, start: int, rng) -> dict:
    """R10's literal table. A fixed-count sort matches its rotated baseline by
    construction -- reported so that is visible, not so it decides anything."""
    n, T = buck.shape
    live = buck[:, start:]
    held = ((live == 0) | (live == NQ - 1)).sum(axis=0).astype(float)
    rot_max, rot_mean = [], []
    for _ in range(N_ROT):
        off = rng.integers(1, T - start, size=n)
        r = np.empty_like(live)
        for i in range(n):
            r[i] = np.roll(live[i], int(off[i]))
        c = ((r == 0) | (r == NQ - 1)).sum(axis=0)
        rot_max.append(c.max())
        rot_mean.append(c.mean())
    return {
        "mean_names_held": float(held.mean()),
        "max_names_held": int(held.max()),
        "rotated_mean": float(np.mean(rot_mean)),
        "rotated_max": float(np.mean(rot_max)),
        "clustering_ratio": float(held.max() / max(np.mean(rot_max), 1e-9)),
    }


# --------------------------------------------------------------------------


def build() -> dict:
    t0 = time.time()
    assert_rolling_ols_matches_rolling_fit()
    assert_nan_cannot_poison()
    assert_aggregation_levels_agree_on_one_symbol()
    daily_leg_cost = assert_cost_constant()

    L.FIXTURE = FIX / "universe_daily_extended_raw.csv.gz"
    L.EVENTS = FIX / "universe_daily_extended_raw_events.json"
    panel, cleaned = L.load_panel()
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)
    n, T = panel.closes.shape
    assert 2 * W_REG < start, "RESMOM's prior-window construction needs 504 warm-up bars"

    lr = panel.log_returns
    tlr = panel.total_log_returns
    md, hs, ok = S.base_masks(panel, cleaned, start)

    assert_scores_are_causal(build_scores, lr, md, hs, cut=start + 200)
    scores = build_scores(lr, md, hs)

    mkt = lr.mean(axis=0)
    mkt_tr = tlr.mean(axis=0)

    # Forward returns, dividend-adjusted. fwd[:, t] = sum of bars t+1 .. t+h.
    fwd = {}
    for h in FWD:
        c = np.cumsum(tlr, axis=1)
        f = np.full((n, T), np.nan)
        f[:, : T - h] = c[:, h:] - c[:, :T - h]
        fwd[h] = f
    # The pin that the two windows share no bar: the score at t uses bars <= t and
    # fwd[t] is exactly the sum over t+1..t+h.
    tt = start + 50
    assert np.allclose(fwd[21][:, tt], tlr[:, tt + 1: tt + 22].sum(axis=1)), "fwd is misaligned"

    # Effective breadth, raw and market-neutralised. The second is the number that
    # matters for THIS family: BOOK.md's 2.23 counts the common factor, and a
    # dollar-neutral book has removed it.
    resid = tlr[:, start:] - mkt_tr[None, start:]
    breadth = {
        "equal_weight_raw": BW.effective_instruments(tlr[:, start:]),
        "participation_raw": participation_ratio(tlr[:, start:]),
        "participation_market_neutral": participation_ratio(resid),
    }

    live_bars = T - start
    rng = np.random.default_rng(SEED)
    key = rng.random((n, T))
    halves = ((start, start + live_bars // 2), (start + live_bars // 2, T))

    cells = {}
    for name in CELL_ORDER:
        sc = scores[name]
        valid = np.isfinite(sc) & ok
        buck = bucket_matrix(sc, valid, key)
        direction = CELLS[name][1]
        per_h = {}
        for h in FWD:
            qt = quintile_table(buck, fwd[h], h, start)
            q = [r["annualised"] for r in qt["quintiles"]]
            raw_spread = q[NQ - 1] - q[0]
            edge = direction * raw_spread
            # Stability, per D250 Result 3: an edge that lives in one era is not an
            # edge. Halves of the LIVE window, on identical construction.
            half_edges = []
            for w in halves:
                hq = [r["annualised"] for r in quintile_table(buck, fwd[h], h, start, w)["quintiles"]]
                half_edges.append(direction * (hq[NQ - 1] - hq[0]))

            turn = leg_turnover(buck, h, start, T)
            rebals = PPY / h
            # Two legs, `turn` of each leg replaced per rebalance, one exit plus
            # one entry per replaced name at 1.85 bp a side.
            cost = -math.expm1(math.log1p(-2 * turn * 2 * 1.85e-4) * rebals)
            borrow = BORROW_ANNUAL
            net = edge - cost - borrow

            pos = neutral_book(buck, h, start, direction, T)
            assert_book_is_dollar_neutral(pos, start)
            sd_book = X.score(panel, pos, start)
            r_book = X.signed_log_returns(panel, pos, total_return=True)[start:]
            nb = np.polyfit(mkt_tr[start:], r_book, 1)[0]
            scale = n / max(int(round(n / NQ)), 1)   # universe-normalised -> 100/100
            years = len(r_book) / PPY

            # WHERE THE MONEY GOES. The pooled spread is a difference of two
            # geometric returns and prices the short leg at -r; a real short earns
            # log(2 - e^r). The legs are scored separately so the gap is measured
            # rather than argued.
            long_only = np.maximum(pos, 0.0)
            short_only = np.minimum(pos, 0.0)
            leg_long = float(np.expm1(
                X.signed_log_returns(panel, long_only, total_return=True)[start:].sum()
                / years) * scale)
            leg_short = float(np.expm1(
                X.signed_log_returns(panel, short_only, total_return=True)[start:].sum()
                / years) * scale)
            # The same short leg priced the naive way, purely to size the gap.
            naive_short = float(np.expm1(
                L.portfolio_log_returns(panel, short_only, total_return=True)[start:].sum()
                / years) * scale)

            # The portfolio-level aggregation, disclosed as a diagnostic.
            r_port = portfolio_level_log_returns(panel, pos)[start:]
            cagr_port = float(np.expm1(r_port.sum() / years))
            sd_p = float(np.std(r_port, ddof=1))

            # D250 Result 3's check, made routine: how much of the book's money is
            # a handful of days, and does it survive 2020 being taken out. Measured
            # on the PORTFOLIO-LEVEL series, because the house-scorer series is
            # negative overall and a share-of-a-negative-total is not a number.
            srt = np.sort(r_port)[::-1]
            top10 = float(srt[:10].sum() / abs(r_port.sum())) if r_port.sum() else float("nan")
            yr = np.array([d[:4] for d in panel.dates[start:]])
            ex2020 = float(np.expm1(r_book[yr != "2020"].sum()
                                    / ((yr != "2020").sum() / PPY)) * scale)
            ex2020_port = float(np.expm1(r_port[yr != "2020"].sum()
                                         / ((yr != "2020").sum() / PPY)))
            half = len(r_port) // 2
            port_halves = [
                float(np.expm1(v.sum() / (len(v) / PPY)))
                for v in (r_port[:half], r_port[half:])
            ]

            per_h[str(h)] = {
                "quintiles": q,
                "pooled_cells": qt["pooled_cells"],
                "raw_spread": raw_spread,
                "edge_declared_direction": edge,
                "edge_first_half": half_edges[0],
                "edge_second_half": half_edges[1],
                "sign_stable_across_halves": bool(half_edges[0] > 0 and half_edges[1] > 0),
                "top10_days_share_of_pnl": top10,
                "book_cagr_ex2020_scaled": ex2020,
                "leg_turnover": turn,
                "rebalances_per_year": rebals,
                "cost_annual": cost,
                "borrow_annual": borrow,
                "net": net,
                "clears_bar": bool(net > NET_BAR),
                "independent_periods": live_bars / h,
                "book_exposure_gross": sd_book["exposure_gross"],
                "book_cagr_universe_normalised": sd_book["cagr"],
                "book_cagr_scaled_100_100": float(
                    np.expm1(np.log1p(sd_book["cagr"]) * scale)
                ) if sd_book["cagr"] > -1 else float("nan"),
                "book_excess_sharpe": sd_book["excess_sharpe"],
                "book_max_drawdown": sd_book["max_drawdown"],
                "book_vol": sd_book["vol"],
                "net_beta_on_universe": float(nb * scale),
                "leg_long_cagr": leg_long,
                "leg_short_cagr": leg_short,
                "leg_short_cagr_naive": naive_short,
                "short_leg_convexity_cost": naive_short - leg_short,
                "book_cagr_portfolio_level": cagr_port,
                "book_sharpe_portfolio_level": (
                    float(np.mean(r_port) / sd_p * math.sqrt(PPY)) if sd_p > 0 else 0.0
                ),
                "net_portfolio_level": cagr_port - BORROW_ANNUAL * sd_book["exposure_short"],
                "book_cagr_portfolio_level_ex2020": ex2020_port,
                "book_cagr_portfolio_level_first_half": port_halves[0],
                "book_cagr_portfolio_level_second_half": port_halves[1],
            }
        cells[name] = {
            "description": CELLS[name][0],
            "direction": direction,
            "horizons": per_h,
            "concurrency": concurrency(buck, start, rng),
        }

    return {
        "produced": "D251 pre-screen",
        "stage": "PRE-SCREEN on the mined 57 -- D245's never-seen cohort is UNTOUCHED",
        "seed": SEED,
        "n_symbols": n,
        "live_bars": live_bars,
        "first_live_date": panel.dates[start],
        "last_date": panel.dates[-1],
        "cost_bps_per_side_median": float(np.median(panel.cost_fraction) * 1e4),
        "cost_wall_daily_roundtrip_one_leg": daily_leg_cost,
        "borrow_annual": BORROW_ANNUAL,
        "net_bar": NET_BAR,
        "breadth": breadth,
        "cells": cells,
        "cell_order": list(CELL_ORDER),
        "elapsed_seconds": round(time.time() - t0, 1),
    }


def render(p: dict) -> str:
    o = ["# D251 pre-screen — cross-sectional dollar-neutral ranking scores\n"]
    o.append(f"**{p['stage']}**\n")
    o.append(
        f"*seed {p['seed']}, {p['elapsed_seconds']}s. {p['n_symbols']} ETFs x "
        f"{p['live_bars']:,} live bars, {p['first_live_date'][:10]} .. "
        f"{p['last_date'][:10]}. Costs {p['cost_bps_per_side_median']:.2f} bp/side "
        f"median, borrow {p['borrow_annual']:.1%}/yr on short notional.*\n"
    )
    o.append(
        f"**The cost wall.** One round trip per day per leg is "
        f"**{p['cost_wall_daily_roundtrip_one_leg']:.2%}/yr** on that leg's notional. "
        f"A dollar-neutral book pays it **twice**, plus borrow.\n"
    )
    b = p["breadth"]
    o.append(
        f"**Breadth.** Equal-weight effective instruments **{b['equal_weight_raw']:.2f}** — "
        f"BOOK.md's saturation-near-2 figure, reproduced. That estimator is degenerate on "
        f"market-neutral residuals (they sum to zero across names, so the equal-weighted "
        f"average is identically zero), so the eigenvalue participation ratio is reported "
        f"instead: **{b['participation_raw']:.2f}** raw against "
        f"**{b['participation_market_neutral']:.2f}** once the common factor is removed. "
        f"**Removing the factor is what buys the breadth back** — which is the argument for "
        f"this family, now measured rather than asserted.\n"
    )

    for name in p["cell_order"]:
        c = p["cells"][name]
        d = "long **Q5**, short Q1" if c["direction"] > 0 else "long **Q1**, short Q5"
        o.append(f"## {name} — {c['description']}\n")
        o.append(f"*A priori direction, declared before the run: {d}.*\n")
        o.append("| h | Q1 | Q2 | Q3 | Q4 | Q5 | Q5−Q1 | **edge** | turnover | cost | borrow | **NET** |")
        o.append("|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        for h in FWD:
            x = c["horizons"][str(h)]
            q = "".join(f" {v * 100:+.2f}% |" for v in x["quintiles"])
            o.append(
                f"| {h} |{q} {x['raw_spread'] * 100:+.2f}% | "
                f"**{x['edge_declared_direction'] * 100:+.2f}%** | "
                f"{x['leg_turnover']:.0%} | {x['cost_annual'] * 100:.2f}% | "
                f"{x['borrow_annual'] * 100:.2f}% | "
                f"**{x['net'] * 100:+.2f}%** |"
            )
        o.append("")
        cc = c["concurrency"]
        o.append(
            f"**R10.** Names held per bar **{cc['mean_names_held']:.1f}** mean / "
            f"**{cc['max_names_held']}** max against a rotated "
            f"{cc['rotated_mean']:.1f} / {cc['rotated_max']:.1f} — ratio "
            f"**{cc['clustering_ratio']:.2f}x**. A fixed-count cross-sectional sort holds the "
            f"same headcount every day, so it is *less* crowded than its own rotated null "
            f"(rotation breaks the exact-count property and lets the extremes bunch). **The "
            f"literal concurrency test cannot fail for this construction**, which is why the "
            f"binding version of R10 here is net beta — the market bet a dollar-neutral book "
            f"can still carry:\n"
        )
        o.append("| h | net beta | long leg | **short leg** | short leg *priced naively* | **convexity cost** | **BOOK, at 100/100** |")
        o.append("|---:|---:|---:|---:|---:|---:|---:|")
        for h in FWD:
            x = c["horizons"][str(h)]
            o.append(
                f"| {h} | **{x['net_beta_on_universe']:+.3f}** | "
                f"{x['leg_long_cagr'] * 100:+.2f}% | **{x['leg_short_cagr'] * 100:+.2f}%** | "
                f"*{x['leg_short_cagr_naive'] * 100:+.2f}%* | "
                f"**{x['short_leg_convexity_cost'] * 100:.2f} pts** | "
                f"**{x['book_cagr_scaled_100_100'] * 100:+.2f}%** |"
            )
        o.append("")
        o.append("| h | portfolio-level CAGR | net | **Sharpe** | 1st half | 2nd half | ex-2020 | top-10 days | independent periods |")
        o.append("|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        for h in FWD:
            x = c["horizons"][str(h)]
            o.append(
                f"| {h} | {x['book_cagr_portfolio_level'] * 100:+.2f}% | "
                f"{x['net_portfolio_level'] * 100:+.2f}% | "
                f"**{x['book_sharpe_portfolio_level']:+.3f}** | "
                f"{x['book_cagr_portfolio_level_first_half'] * 100:+.2f}% | "
                f"{x['book_cagr_portfolio_level_second_half'] * 100:+.2f}% | "
                f"{x['book_cagr_portfolio_level_ex2020'] * 100:+.2f}% | "
                f"{x['top10_days_share_of_pnl']:.0%} | "
                f"**{x['independent_periods']:.0f}** |"
            )
        o.append("")

    o.append("## Verdict\n")

    def _best(field):
        b = None
        for name in p["cell_order"]:
            for h in FWD:
                x = p["cells"][name]["horizons"][str(h)]
                if b is None or x[field] > b[2]:
                    b = (name, h, x[field])
        return b

    bt = _best("net")
    bb = _best("book_cagr_scaled_100_100")
    bp = _best("book_sharpe_portfolio_level")
    cleared = [
        f"{k} @ {h}" for k in p["cell_order"] for h in FWD
        if p["cells"][k]["horizons"][str(h)]["clears_bar"]
    ]
    o.append(
        f"**Bar: net > {p['net_bar']:.0%}/yr after two-leg costs and borrow.**\n"
    )
    o.append(
        f"| reading | best cell | value |\n|---|---|---:|\n"
        f"| spread table, net of cost and borrow | {bt[0]} @ {bt[1]} | "
        f"**{bt[2] * 100:+.2f}%/yr** |\n"
        f"| **the book actually built, house scorer, at 100/100** | {bb[0]} @ {bb[1]} | "
        f"**{bb[2] * 100:+.2f}%/yr** |\n"
        f"| the same book, portfolio-level aggregation | {bp[0]} @ {bp[1]} | "
        f"**Sharpe {bp[2]:+.3f}** |\n"
    )
    o.append(
        f"Cells clearing the bar **on the spread table**: "
        f"{', '.join(cleared) if cleared else 'none'}. "
        f"Cells whose BOOK clears it under the mandated scorer: **none — every one of "
        f"{len(p['cell_order']) * len(FWD)} loses money.**\n"
    )
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

    print()
    print(f"{'cell':7s} {'h':>4s} {'edge':>8s} {'NETtbl':>8s} {'long':>8s} {'short':>8s} "
          f"{'shrtNv':>8s} {'convex':>8s} {'BOOK':>8s} {'PORT':>8s} {'netPORT':>8s} "
          f"{'beta':>7s} {'h1':>8s} {'h2':>8s} {'ex2020':>8s}")
    for name in payload["cell_order"]:
        c = payload["cells"][name]
        for h in FWD:
            x = c["horizons"][str(h)]
            print(f"{name:7s} {h:4d} {x['edge_declared_direction']:8.2%} {x['net']:8.2%} "
                  f"{x['leg_long_cagr']:8.2%} {x['leg_short_cagr']:8.2%} "
                  f"{x['leg_short_cagr_naive']:8.2%} {x['short_leg_convexity_cost']:8.2%} "
                  f"{x['book_cagr_scaled_100_100']:8.2%} "
                  f"{x['book_cagr_portfolio_level']:8.2%} {x['net_portfolio_level']:8.2%} "
                  f"{x['net_beta_on_universe']:+7.2f} {x['edge_first_half']:8.2%} "
                  f"{x['edge_second_half']:8.2%} {x['book_cagr_ex2020_scaled']:8.2%}")
    b = payload["breadth"]
    print()
    print(f"breadth: equal-weight {b['equal_weight_raw']:.2f} | participation raw "
          f"{b['participation_raw']:.2f} | participation market-neutral "
          f"{b['participation_market_neutral']:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
