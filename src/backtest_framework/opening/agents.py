"""The opening agent-state model's pre-open agent pressures (OPENING_AGENT_STATE_PREREG.md s.4) under OA-A6 and
OA-A7 (ruled 2026-09-28). Pure functions over per-session arrays in time order; every value at session t uses only
information available by 09:29 ET on t (A6 by 09:31), and the tests in `tests/unit/test_opening_agents.py`
(deposit s.15, tests 4-11) prove each look-back.

Signs: + is buying pressure.
- A1 stop holders:     P1 = +(open - prior_high)/ATR20 above the prior high, -(prior_low - open)/ATR20 below the
                       prior low, else 0 (at the open).
- A2 trend followers:  target[t] = mean over L in {20, 60, 120} of sign(c[t-1]/c[t-1-L] - 1), divided by sigma20
                       at t-1; P2 = target[t] - target[t-1]. c = the front settlement, ratio back-adjusted at rolls
                       (OA-A7.1).
- A3 vol targeting:    E[t] = min(0.10 / (sigma20[t-1] * sqrt(252)), 2); P3 = E[t] - E[t-1].
- A4 options dealers:  G = sum over calls OI*gamma - sum over puts OI*gamma (dealers long calls, short puts);
                       P4 = -G * (open - prior_close). Gamma is Black-76 at rate 0 with the vol implied from the prior
                       settlement (D581's convention, OA-A7.4).
- A5 macro reactors:   P5 = r(08:29 -> 09:25)/sigma of that return over prior sessions, on release days; else 0.
- A6 index arbitrage:  d = (F/rho - E)/ATR20_etf at the 09:30 bar's close (09:31); P6 = -d. rho = the median of F/E
                       at 15:59 over the prior 20 sessions.
- A7 (measurement):    the large-lot threshold is the 90th percentile trade size over the prior 20 sessions.
Standardisation (OA-A7.3): z = P / std(P over the prior 250 sessions, or all prior sessions when at least 60).
"""
from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from scipy.special import ndtr

LOOKBACKS = (20, 60, 120)
SIGMA_N = 20
VOL_TARGET, EXPOSURE_CAP = 0.10, 2.0
STD_WINDOW, STD_MIN = 250, 60
FAIR_N = 20
LARGE_LOT_Q, LARGE_LOT_N = 0.90, 20
IV_LO, IV_HI = 0.01, 4.0
SESSIONS_PER_YEAR = 252.0


# ------------------------------------------------------------------------------ A1
def a1_stop(open_: np.ndarray, prior_high: np.ndarray, prior_low: np.ndarray, atr20: np.ndarray) -> np.ndarray:
    o, h, lo, atr = (np.asarray(x, dtype=float) for x in (open_, prior_high, prior_low, atr20))
    return np.where(o > h, (o - h) / atr, np.where(o < lo, -(lo - o) / atr, 0.0))


# ------------------------------------------------------------------------------ A2, A3
def ratio_adjust(settle: np.ndarray, new_over_old: np.ndarray) -> np.ndarray:
    """Back-adjust a front settlement series at its rolls. `new_over_old[t]` is 1 except on a roll day, where it is
    the new contract's settlement over the old one's on that day; every settlement BEFORE t is multiplied by it, so
    returns across the roll are the new contract's own."""
    s = np.asarray(settle, dtype=float)
    k = np.asarray(new_over_old, dtype=float)
    factor = np.cumprod(k[::-1])[::-1]  # factor[t] = product of k[t..end]
    back = np.append(factor[1:], 1.0)   # applied to t: the product of the rolls strictly after t
    return s * back


def sigma20_prior(close: np.ndarray, n: int = SIGMA_N) -> np.ndarray:
    """sigma of the n daily log returns ending at t-1 (known before t's open)."""
    c = np.asarray(close, dtype=float)
    r = np.full(len(c), np.nan)
    r[1:] = np.log(c[1:] / c[:-1])
    out = np.full(len(c), np.nan)
    for t in range(n + 1, len(c)):
        out[t] = np.std(r[t - n:t], ddof=1)
    return out


def a2_trend(close: np.ndarray, lookbacks: Sequence[int] = LOOKBACKS) -> tuple[np.ndarray, np.ndarray]:
    """(target, P2). target[t] uses closes up to t-1 only."""
    c = np.asarray(close, dtype=float)
    sig = sigma20_prior(c)
    target = np.full(len(c), np.nan)
    for t in range(max(lookbacks) + 1, len(c)):
        s = np.mean([np.sign(c[t - 1] / c[t - 1 - L] - 1) for L in lookbacks])
        target[t] = s / sig[t] if sig[t] > 0 else np.nan
    p2 = np.full(len(c), np.nan)
    p2[1:] = target[1:] - target[:-1]
    return target, p2


def a3_voltarget(close: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(exposure, P3). E[t] uses sigma20 of returns to t-1."""
    sig = sigma20_prior(close) * np.sqrt(SESSIONS_PER_YEAR)
    with np.errstate(divide="ignore", invalid="ignore"):
        e = np.minimum(VOL_TARGET / sig, EXPOSURE_CAP)
    p3 = np.full(len(e), np.nan)
    p3[1:] = e[1:] - e[:-1]
    return e, p3


# ------------------------------------------------------------------------------ A4
def b76_gamma(F: np.ndarray, K: np.ndarray, sig: np.ndarray, tau: np.ndarray) -> np.ndarray:
    F, K, sig, tau = (np.asarray(x, dtype=float) for x in (F, K, sig, tau))
    sq = sig * np.sqrt(tau)
    d1 = (np.log(F / K) + 0.5 * sig * sig * tau) / sq
    return np.exp(-0.5 * d1 * d1) / np.sqrt(2 * np.pi) / (F * sq)


def b76_price(F: np.ndarray, K: np.ndarray, sig: np.ndarray, tau: np.ndarray, is_call: np.ndarray) -> np.ndarray:
    F, K, sig, tau = (np.asarray(x, dtype=float) for x in (F, K, sig, tau))
    sq = sig * np.sqrt(tau)
    d1 = (np.log(F / K) + 0.5 * sig * sig * tau) / sq
    d2 = d1 - sq
    return np.where(is_call, F * ndtr(d1) - K * ndtr(d2), K * ndtr(-d2) - F * ndtr(-d1))


def implied_vol(price: np.ndarray, F: np.ndarray, K: np.ndarray, tau: np.ndarray, is_call: np.ndarray,
                iters: int = 60) -> np.ndarray:
    """Bisection on [IV_LO, IV_HI] (D581's bracket); NaN where the price is outside it."""
    price = np.asarray(price, dtype=float)
    lo, hi = np.full(price.shape, IV_LO), np.full(price.shape, IV_HI)
    ok = (b76_price(F, K, lo, tau, is_call) <= price) & (price <= b76_price(F, K, hi, tau, is_call))
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        below = b76_price(F, K, mid, tau, is_call) < price
        lo, hi = np.where(below, mid, lo), np.where(below, hi, mid)
    return np.where(ok, 0.5 * (lo + hi), np.nan)


def dealer_gamma(F: np.ndarray, K: np.ndarray, sig: np.ndarray, tau: np.ndarray, oi: np.ndarray,
                 is_call: np.ndarray) -> float:
    """G under s.4 A4's positioning: customers long puts and short calls, dealers the other side, so dealers are
    long the calls' gamma and short the puts'. Options with a NaN vol are left out."""
    g = b76_gamma(F, K, sig, tau) * np.asarray(oi, dtype=float)
    ok = np.isfinite(g)
    return float(np.sum(np.where(np.asarray(is_call)[ok], g[ok], -g[ok])))


def a4_pressure(G: np.ndarray, open_: np.ndarray, prior_close: np.ndarray) -> np.ndarray:
    return -np.asarray(G, dtype=float) * (np.asarray(open_, dtype=float) - np.asarray(prior_close, dtype=float))


# ------------------------------------------------------------------------------ A5
A5_FROM_BAR, A5_TO_BAR = "08:28", "09:24"  # the closes at 08:29 and 09:25


def a5_return(close_by_hhmm: dict[str, float]) -> float:
    """r(08:29 -> 09:25) from one session's bar closes keyed by bar-start hh:mm: the 08:28 and 09:24 bars' closes.
    Nothing later than the 09:24 bar is read. NaN if either bar is missing."""
    a, b = close_by_hhmm.get(A5_FROM_BAR), close_by_hhmm.get(A5_TO_BAR)
    if a is None or b is None or not (np.isfinite(a) and np.isfinite(b)):
        return float("nan")
    return float(b / a - 1)


def a5_macro(r: np.ndarray, is_release: np.ndarray) -> np.ndarray:
    """P5 = r / sigma(r over the prior sessions, OA-A7.3's window) on release days, 0 otherwise."""
    r = np.asarray(r, dtype=float)
    sig = prior_std(r)
    rel = np.asarray(is_release, dtype=bool)
    return np.where(rel, r / sig, 0.0)


# ------------------------------------------------------------------------------ A6
def fair_ratio_prior(ratio_1559: np.ndarray, n: int = FAIR_N) -> np.ndarray:
    """rho[t] = the median of the last n FINITE 15:59 ratios before t (t itself excluded). A session with no ratio
    (a CME session on an NYSE holiday, a half day) is skipped, not allowed to blank the next n sessions."""
    x = np.asarray(ratio_1559, dtype=float)
    out = np.full(len(x), np.nan)
    fin = np.flatnonzero(np.isfinite(x))
    for t in range(len(x)):
        k = np.searchsorted(fin, t)  # finite observations strictly before t
        if k >= n:
            out[t] = np.median(x[fin[k - n:k]])
    return out


def on_finite(fn, series: np.ndarray) -> tuple[np.ndarray, ...]:
    """Run a per-session daily-close function on the sessions that HAVE a close, then map back (NaN elsewhere).
    A return across a skipped session is then that span's return, as a daily series across a holiday is."""
    s = np.asarray(series, dtype=float)
    fin = np.isfinite(s)
    res = fn(s[fin])
    res = res if isinstance(res, tuple) else (res,)
    outs = []
    for r in res:
        o = np.full(len(s), np.nan)
        o[fin] = r
        outs.append(o)
    return tuple(outs)


A6_BAR = "09:30"  # the first ETF print after 09:30 is this bar's close, at 09:31 (OA-A7.6)


def a6_prints(fut_close_by_hhmm: dict[str, float], etf_close_by_hhmm: dict[str, float]) -> tuple[float, float]:
    """(future, ETF) at the 09:30 bar's close. No pre-open ETF print is read, and nothing after 09:31."""
    f, e = fut_close_by_hhmm.get(A6_BAR), etf_close_by_hhmm.get(A6_BAR)
    return (float("nan") if f is None else float(f)), (float("nan") if e is None else float(e))


def a6_basis(fut_0931: np.ndarray, etf_0931: np.ndarray, rho: np.ndarray, atr20_etf: np.ndarray) -> np.ndarray:
    f, e, rho, atr = (np.asarray(x, dtype=float) for x in (fut_0931, etf_0931, rho, atr20_etf))
    d = (f / rho - e) / atr
    return -d


# ------------------------------------------------------------------------------ A7
def large_lot_threshold(sizes_by_session: Sequence[np.ndarray], q: float = LARGE_LOT_Q,
                        n: int = LARGE_LOT_N) -> np.ndarray:
    """The q-quantile of trade sizes over the n sessions BEFORE each session (NaN until n exist)."""
    out = np.full(len(sizes_by_session), np.nan)
    for t in range(n, len(sizes_by_session)):
        pool = np.concatenate([np.asarray(s, dtype=float) for s in sizes_by_session[t - n:t]])
        if pool.size:
            out[t] = np.quantile(pool, q)
    return out


# ------------------------------------------------------------------------------ standardisation
def prior_std(p: np.ndarray, window: int = STD_WINDOW, min_n: int = STD_MIN) -> np.ndarray:
    """std of the finite values among the prior `window` sessions (t excluded); NaN below `min_n` of them."""
    p = np.asarray(p, dtype=float)
    out = np.full(len(p), np.nan)
    for t in range(1, len(p)):
        w = p[max(0, t - window):t]
        w = w[np.isfinite(w)]
        if len(w) >= min_n:
            out[t] = np.std(w, ddof=1)
    return out


def standardise(p: np.ndarray, window: int = STD_WINDOW, min_n: int = STD_MIN) -> np.ndarray:
    """z = P / prior_std(P) (OA-A7.3). A zero std gives NaN, never an infinite z."""
    s = prior_std(p, window, min_n)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(s > 0, np.asarray(p, dtype=float) / s, np.nan)
