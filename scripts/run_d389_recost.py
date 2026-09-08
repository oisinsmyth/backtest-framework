"""D389 — re-costing D163's sub-hourly closure at futures commission.

Pre-registered in `docs/decisions/D389-PREREG-the-D163-recost.md`; read that first.
Result goes to `docs/decisions/D389-RESULT-the-D163-recost.md`. **D163 is not edited.**

    .venv/Scripts/python.exe scripts/run_d389_recost.py            # full study
    .venv/Scripts/python.exe scripts/run_d389_recost.py --selftest # assertions only

WHAT THIS IS. The Donchian long-or-flat breakout (D109) down the frequency ladder
15m -> 1d, on the 8.4-year Binance 15m base (BTCUSDT/ETHUSDT), scored GROSS first
(R15) and then overlaid with two cost conventions: D163's crypto taker tier at
40 bp/side and D258's futures figure at 0.1 bp/side. Crypto spot data, so a pass is
a FEASIBILITY BOUND, never a futures backtest (D260's category).

MEMORY. One rung is resampled, scored and released before the next is built. Peak
working set is measured with psutil and reported.
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import time
import zlib
from collections import deque
from pathlib import Path

import numpy as np
import pandas as pd
import psutil

REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "data" / "fixtures" / "crypto_binance_15m_raw.csv.gz"
SUMMARY = REPO / "data" / "d389_recost_summary.json"
TEMP = REPO / "temp"

SYMBOLS = ("BTCUSDT", "ETHUSDT")
SOURCE_MINUTES = 15
MINUTES_PER_DAY = 1440
BARS_PER_DAY_SOURCE = MINUTES_PER_DAY // SOURCE_MINUTES  # 96

# The ladder. Every rung's minutes divide 1440 (D161) AND are a multiple of 15.
LADDER = (("15m", 15), ("30m", 30), ("1h", 60), ("2h", 120),
          ("4h", 240), ("6h", 360), ("12h", 720), ("1d", 1440))

BASE_N_ENTRY, BASE_N_EXIT = 40, 10          # plateau_40_10, the daily baseline
TRAIN_DAYS, TEST_DAYS = 252, 63             # D163's walk-forward convention
DROP_DAYS = TRAIN_DAYS + TEST_DAYS          # 315, dropped from the front at EVERY rung

RF_ANNUAL = 0.04
DAYS_PER_YEAR = 365.0                       # crypto calendar (D108)

COST_CONVENTIONS = {
    "crypto_taker_40bp": 40.0,              # D163's reference tier (D114)
    "futures_0.1bp": 0.1,                   # D258: ~$4-5 on ~$250k ~= 0.2 bp round trip
}

# D163's imported constants: gross annualised Sharpe, 2015-2025 DAILY, maker_0bp.
REFERENCE_GROSS_SHARPE = {"BTCUSDT": 1.27, "ETHUSDT": 0.84}

N_NULLS = 500
NULL_SEED = 20260908


# ===================================================================== load / resample


def load_base() -> dict[str, dict[str, np.ndarray]]:
    """The 15m base, one dict of float64 OHLC arrays plus a day index per symbol.

    Asserts the fixture is already on a complete, day-aligned 15m grid: the meta
    records `empty_bars_15m: 0` and `bar_count == days_kept * 96`, and D161's
    day-level drop policy was applied at fetch time. Every downstream reshape
    depends on that being true rather than assumed."""
    with gzip.open(FIXTURE, "rt") as handle:
        frame = pd.read_csv(
            handle,
            usecols=["timestamp", "symbol", "open", "high", "low", "close"],
            dtype={"symbol": "category", "open": np.float64, "high": np.float64,
                   "low": np.float64, "close": np.float64},
        )
    frame = frame[frame["symbol"].isin(SYMBOLS)]
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])

    out: dict[str, dict[str, np.ndarray]] = {}
    for symbol in SYMBOLS:
        part = frame[frame["symbol"] == symbol].sort_values("timestamp")
        ts = part["timestamp"].to_numpy()
        n = len(ts)
        if n % BARS_PER_DAY_SOURCE:
            raise ValueError(f"{symbol}: {n} bars is not a whole number of 96-bar UTC days")
        minute_of_day = (part["timestamp"].dt.hour * 60 + part["timestamp"].dt.minute).to_numpy()
        expected = np.tile(np.arange(0, MINUTES_PER_DAY, SOURCE_MINUTES),
                           n // BARS_PER_DAY_SOURCE)
        if not np.array_equal(minute_of_day, expected):
            raise ValueError(f"{symbol}: bars are not on a complete, day-aligned 15m grid (D161)")
        days = part["timestamp"].dt.floor("D").to_numpy()[::BARS_PER_DAY_SOURCE]
        out[symbol] = {
            "open": np.ascontiguousarray(part["open"].to_numpy()),
            "high": np.ascontiguousarray(part["high"].to_numpy()),
            "low": np.ascontiguousarray(part["low"].to_numpy()),
            "close": np.ascontiguousarray(part["close"].to_numpy()),
            "day": days,
            "ts": ts,
        }
    del frame
    return out


def resample(base: dict[str, np.ndarray], minutes: int) -> dict[str, np.ndarray]:
    """Exact OHLC aggregation into `minutes` buckets anchored at 00:00 UTC (D161).

    open = first, high = max, low = min, close = last. `factor` divides 96 and every
    day contributes exactly 96 consecutive in-order bars, so grouping consecutive
    `factor` bars can never straddle a day boundary — which is why the reshape is
    legitimate and not a shortcut."""
    if minutes % SOURCE_MINUTES or MINUTES_PER_DAY % minutes:
        raise ValueError(f"{minutes}m is not a whole multiple of 15m dividing a UTC day")
    factor = minutes // SOURCE_MINUTES
    n = len(base["open"])
    if n % factor:
        raise ValueError(f"{n} source bars do not divide into {factor}-bar buckets")
    view = lambda key: base[key].reshape(-1, factor)  # noqa: E731
    out = {
        "open": view("open")[:, 0].copy(),
        "high": view("high").max(axis=1),
        "low": view("low").min(axis=1),
        "close": view("close")[:, -1].copy(),
        "ts": base["ts"][::factor].copy(),
    }
    bars_per_day = MINUTES_PER_DAY // minutes
    if len(out["open"]) != len(base["day"]) * bars_per_day:
        raise ValueError(f"{minutes}m: {len(out['open'])} bars from {len(base['day'])} days")
    return out


# ===================================================================== the rule


def rolling_extreme_shifted(values: np.ndarray, window: int, kind: str) -> np.ndarray:
    """`max(values[t-window .. t-1])`, i.e. the extremum over the `window` bars STRICTLY
    BEFORE t. NaN where fewer than `window` prior bars exist. Implementation #1."""
    series = pd.Series(values)
    rolled = series.rolling(window).max() if kind == "max" else series.rolling(window).min()
    return rolled.shift(1).to_numpy()


def signal_vectorised(high, low, close, n_entry, n_exit) -> np.ndarray:
    """`sig[t]` = the state the rule is IN at the close of bar t (1 long, 0 flat).

    The trade is filled at `open[t+1]` (next_open, D103); this function returns the
    decision, never the position. See `positions_from_signal`."""
    entry_hi = rolling_extreme_shifted(high, n_entry, "max")
    exit_lo = rolling_extreme_shifted(low, n_exit, "min")
    n = len(close)
    sig = np.zeros(n, dtype=np.int8)
    state = 0
    for t in range(n):
        if state == 0:
            if not np.isnan(entry_hi[t]) and close[t] > entry_hi[t]:
                state = 1
        else:
            if not np.isnan(exit_lo[t]) and close[t] < exit_lo[t]:
                state = 0
        sig[t] = state
    return sig


def signal_second_implementation(high, low, close, n_entry, n_exit) -> np.ndarray:
    """ASSERTION 1 — the lag audit. A monotonic-deque rolling extremum plus an explicit
    state machine, sharing no code path with `rolling_extreme_shifted`. It maintains the
    window over the bars strictly before t by construction: the deque is updated with
    bar t only AFTER bar t has been read. Must agree bit-for-bit."""
    n = len(close)
    sig = np.zeros(n, dtype=np.int8)
    hi_dq: deque[int] = deque()   # indices, decreasing high
    lo_dq: deque[int] = deque()   # indices, increasing low
    state = 0
    for t in range(n):
        while hi_dq and hi_dq[0] < t - n_entry:
            hi_dq.popleft()
        while lo_dq and lo_dq[0] < t - n_exit:
            lo_dq.popleft()
        if state == 0:
            if len(hi_dq) and t >= n_entry and close[t] > high[hi_dq[0]]:
                state = 1
        else:
            if len(lo_dq) and t >= n_exit and close[t] < low[lo_dq[0]]:
                state = 0
        sig[t] = state
        while hi_dq and high[hi_dq[-1]] <= high[t]:
            hi_dq.pop()
        hi_dq.append(t)
        while lo_dq and low[lo_dq[-1]] >= low[t]:
            lo_dq.pop()
        lo_dq.append(t)
    return sig


def positions_from_signal(sig: np.ndarray) -> np.ndarray:
    """`pos[k]` = weight held over `[open[k], open[k+1])`, and it equals `sig[k-1]`.

    That one shift IS the next_open fill: a decision taken at the close of bar k-1 is
    worked at the open of bar k. `pos[k]` therefore cannot see `close[k]`, which is what
    the perturbation audit checks."""
    pos = np.zeros(len(sig), dtype=np.float64)
    pos[1:] = sig[:-1]
    return pos


# ===================================================================== scoring


def score_book(pos: np.ndarray, open_: np.ndarray, day_idx: np.ndarray,
               rate_per_side: float, bars_per_day: int) -> dict:
    """One book, one cost rate. Open-to-open returns, because that is what a next_open
    fill actually earns. Costs are charged at the open of the bar the weight changes on.

    `rate_per_side` is a FRACTION (0.004 == 40 bp), charged on |delta weight|."""
    r = np.zeros(len(open_), dtype=np.float64)
    r[:-1] = open_[1:] / open_[:-1] - 1.0          # return over [open[k], open[k+1])
    turn = np.abs(np.diff(pos, prepend=0.0))
    step = (1.0 - rate_per_side * turn) * (1.0 + pos * r)
    equity = np.cumprod(step)

    n = len(pos)
    years = n / (bars_per_day * DAYS_PER_YEAR)
    ppy = bars_per_day * DAYS_PER_YEAR

    # Daily NAV, so Sharpe and vol are comparable ACROSS rungs (D164's units argument).
    last_of_day = np.flatnonzero(np.diff(day_idx, append=day_idx[-1] + 1) != 0)
    nav = equity[last_of_day]
    daily_ret = nav[1:] / nav[:-1] - 1.0
    d_mean, d_sd = float(daily_ret.mean()), float(daily_ret.std(ddof=1))
    sharpe_daily_nav = ((d_mean - RF_ANNUAL / DAYS_PER_YEAR) / d_sd * math.sqrt(DAYS_PER_YEAR)
                        if d_sd > 0 else float("nan"))
    ann_vol = d_sd * math.sqrt(DAYS_PER_YEAR)

    # D163's own convention, kept so the two can be compared: annualised on the BAR.
    bar_ret = step - 1.0
    b_sd = float(bar_ret.std(ddof=1))
    sharpe_bar = ((float(bar_ret.mean()) - RF_ANNUAL / ppy) / b_sd * math.sqrt(ppy)
                  if b_sd > 0 else float("nan"))

    peak = np.maximum.accumulate(nav)
    max_dd = float((1.0 - nav / peak).max())

    total_return = float(equity[-1] - 1.0)
    cagr = float((1.0 + total_return) ** (1.0 / years) - 1.0) if total_return > -1 else -1.0
    turnover_annual = float(turn.sum() / years)

    return {
        "total_return": total_return,
        "cagr": cagr,
        "sharpe_daily_nav": sharpe_daily_nav,
        "sharpe_bar_annualised": sharpe_bar,
        "annual_vol": ann_vol,
        "max_drawdown": max_dd,
        "exposure": float(pos.mean()),
        "annual_turnover": turnover_annual,
        "fee_drag_annual": turnover_annual * rate_per_side,
        "years": years,
        "_nav": nav,
        "_last_of_day": last_of_day,
    }


def trade_table(pos: np.ndarray, open_: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(entry index, exit index, gross simple return) per closed trade. A trade is a run
    of pos == 1; it is entered at `open[entry]` and closed at `open[exit]`."""
    flag = (pos > 0).astype(np.int8)
    edges = np.diff(flag, prepend=0, append=0)
    entries = np.flatnonzero(edges == 1)
    exits = np.flatnonzero(edges == -1)
    keep = exits < len(open_)                      # a still-open trade is not a closed trade
    entries, exits = entries[keep], exits[keep]
    ret = open_[exits] / open_[entries] - 1.0
    return entries, exits, ret


def _moment(x: np.ndarray, k: int) -> float:
    if len(x) < 3:
        return float("nan")
    sd = x.std(ddof=0)
    return float((((x - x.mean()) / sd) ** k).mean()) if sd > 0 else float("nan")


def trade_distribution(ret: np.ndarray, hold_bars: np.ndarray, bars_per_day: int,
                       round_trip_cost: float) -> dict:
    """Group 2. The 1% two-tail trim is reported as ALL THREE means (CLAUDE.md), because
    dropping only winners is a flag and not a verdict."""
    n = len(ret)
    if n == 0:
        return {"n_trades": 0}
    bp = ret * 1e4
    order = np.sort(bp)
    k = max(1, int(round(0.01 * n)))
    wins = bp[bp > 0]
    losses = bp[bp <= 0]
    return {
        "n_trades": int(n),
        "mean_bp": float(bp.mean()),
        "median_bp": float(np.median(bp)),
        "sd_bp": float(bp.std(ddof=1)) if n > 1 else float("nan"),
        "win_rate": float((bp > 0).mean()),
        "payoff": float(wins.mean() / abs(losses.mean())) if len(wins) and len(losses) else float("nan"),
        "mean_hold_days": float(hold_bars.mean() / bars_per_day),
        "median_hold_days": float(np.median(hold_bars) / bars_per_day),
        "skew": _moment(bp, 3),
        "kurtosis": _moment(bp, 4),
        "mean_ex_top1pct_bp": float(order[:-k].mean()) if n > k else float("nan"),
        "mean_ex_bottom1pct_bp": float(order[k:].mean()) if n > k else float("nan"),
        "mean_trimmed_bp": float(order[k:-k].mean()) if n > 2 * k else float("nan"),
        "trimmed_n_each_tail": int(k),
        "round_trip_cost_bp": round_trip_cost * 1e4,
        "mean_minus_2c_bp": float(bp.mean() - round_trip_cost * 1e4),
        "breakeven_bp_per_side": float(bp.mean() / 2.0),
    }


def winner_dependence(ret: np.ndarray, entry_ts: np.ndarray) -> dict:
    """Group 3. `ret` in simple terms; concentration is measured on P&L contribution."""
    n = len(ret)
    if n == 0:
        return {}
    order = np.argsort(-ret)
    sorted_ret = ret[order]
    total = float(ret.sum())
    out: dict = {}
    if total > 0:
        cum = np.cumsum(sorted_ret)
        out["trades_to_half_pnl"] = int(np.searchsorted(cum, 0.5 * total) + 1)
    else:
        out["trades_to_half_pnl"] = None
    for k in (1, 5, 10):
        take = min(k, n)
        out[f"top{k}_share_of_pnl"] = float(sorted_ret[:take].sum() / total) if total != 0 else float("nan")
    # The top trade, NAMED and dated -- a concentration report is not finished without it.
    top = int(order[0])
    out["top_trade_bp"] = float(ret[top] * 1e4)
    out["top_trade_entry"] = str(pd.Timestamp(entry_ts[top]))
    years = pd.DatetimeIndex(entry_ts).year
    by_year: dict[str, float] = {}
    for y in np.unique(years):
        by_year[str(int(y))] = float(ret[years == y].sum() * 1e4)
    out["pnl_bp_by_entry_year"] = by_year
    out["profitable_years"] = f"{sum(1 for v in by_year.values() if v > 0)}/{len(by_year)}"
    era = years >= 2022
    out["era_pre2022_mean_bp"] = float(ret[~era].mean() * 1e4) if (~era).any() else float("nan")
    out["era_2022plus_mean_bp"] = float(ret[era].mean() * 1e4) if era.any() else float("nan")
    out["era_pre2022_n"] = int((~era).sum())
    out["era_2022plus_n"] = int(era.sum())
    return out


def rotation_null(pos: np.ndarray, open_: np.ndarray, n_sims: int, seed: int) -> dict:
    """Group 4. A CIRCULAR ROTATION of the position vector against the price series.

    Rotation preserves exposure, trade count, the holding-run distribution and turnover
    EXACTLY, and destroys only the alignment between the rule's timing and the market.
    It is matched on the nuisance, not merely on the count (CLAUDE.md).

    Two statistics are carried, because they can disagree: gross mean per trade, and
    gross total return."""
    rng = np.random.default_rng(seed)
    n = len(pos)
    r = np.zeros(n, dtype=np.float64)
    r[:-1] = open_[1:] / open_[:-1] - 1.0
    means = np.empty(n_sims)
    totals = np.empty(n_sims)
    for i in range(n_sims):
        rolled = np.roll(pos, int(rng.integers(1, n)))
        _, _, tr = trade_table(rolled, open_)
        means[i] = tr.mean() * 1e4 if len(tr) else np.nan
        totals[i] = float(np.cumprod(1.0 + rolled * r)[-1] - 1.0)
    return {
        "n_sims": n_sims,
        "mean_bp_p50": float(np.nanpercentile(means, 50)),
        "mean_bp_p95": float(np.nanpercentile(means, 95)),
        "mean_bp_p05": float(np.nanpercentile(means, 5)),
        "mean_bp_max": float(np.nanmax(means)),
        "total_return_p50": float(np.nanpercentile(totals, 50)),
        "total_return_p95": float(np.nanpercentile(totals, 95)),
        "_means": means,
        "_totals": totals,
    }


def corwin_schultz(high: np.ndarray, low: np.ndarray, mask: np.ndarray | None = None) -> float:
    """Corwin-Schultz two-day (here: two-BAR) high-low spread estimator, in bp/side.

    CLAUDE.md group 1: estimate the spread of the names HELD off the OHLC rather than
    trusting a fee assumption. Negative estimates are set to zero, the standard
    treatment, and the median across bars is reported."""
    hi, lo = np.log(high), np.log(low)
    beta = (hi[:-1] - lo[:-1]) ** 2 + (hi[1:] - lo[1:]) ** 2
    h2 = np.maximum(high[:-1], high[1:])
    l2 = np.minimum(low[:-1], low[1:])
    gamma = (np.log(h2) - np.log(l2)) ** 2
    k = 3.0 - 2.0 * math.sqrt(2.0)
    alpha = (math.sqrt(2.0) * np.sqrt(beta) - np.sqrt(beta)) / k - np.sqrt(gamma / k)
    spread = 2.0 * (np.exp(alpha) - 1.0) / (1.0 + np.exp(alpha))
    spread = np.where(np.isfinite(spread), spread, np.nan)
    spread = np.maximum(spread, 0.0)
    if mask is not None:
        spread = spread[mask[:-1]]
    if spread.size == 0 or np.all(np.isnan(spread)):
        return float("nan")
    return float(np.nanmedian(spread) / 2.0 * 1e4)   # half-spread, bp per side


# ===================================================================== assertions


class AssertionFailed(RuntimeError):
    pass


def audit_lag(high, low, close, n_entry, n_exit, label: str) -> None:
    """ASSERTION 1a — second implementation, bit-identical."""
    a = signal_vectorised(high, low, close, n_entry, n_exit)
    b = signal_second_implementation(high, low, close, n_entry, n_exit)
    if not np.array_equal(a, b):
        bad = int(np.flatnonzero(a != b)[0])
        raise AssertionFailed(
            f"{label}: lag audit failed — the two implementations first disagree at bar {bad} "
            f"({a[bad]} vs {b[bad]}); {int((a != b).sum())} of {len(a)} bars differ"
        )


def audit_no_lookahead(high, low, close, open_, n_entry, n_exit, label: str,
                       rng: np.random.Generator) -> None:
    """ASSERTION 1b — perturb every bar STRICTLY AFTER t and require pos[:t+2] unchanged.

    `pos[k]` is worked at `open[k]` off the close of bar `k-1`, so nothing at index >= k
    may touch it."""
    pos = positions_from_signal(signal_vectorised(high, low, close, n_entry, n_exit))
    t = len(close) // 2
    h2, l2, c2 = high.copy(), low.copy(), close.copy()
    bump = 1.0 + rng.uniform(0.05, 0.5, size=len(close) - (t + 1))
    h2[t + 1:] *= bump
    l2[t + 1:] *= bump
    c2[t + 1:] *= bump
    pos2 = positions_from_signal(signal_vectorised(h2, l2, c2, n_entry, n_exit))
    if not np.array_equal(pos[: t + 2], pos2[: t + 2]):
        raise AssertionFailed(
            f"{label}: LOOK-AHEAD — perturbing bars after {t} changed the position at or "
            f"before {t + 1}"
        )


def audit_sign_in_money(bars_per_day: int, label: str) -> None:
    """ASSERTION 2 — the sign audit, in money.

    On a monotonically rising synthetic series a long-or-flat book must EARN; on the
    mirrored series the same book must not earn the same money; and raising the cost
    rate must STRICTLY reduce net P&L wherever turnover is non-zero."""
    n = 4000
    up = 100.0 * np.exp(np.linspace(0, 1.2, n))
    day = np.repeat(np.arange(n // bars_per_day + 1), bars_per_day)[:n]
    pos = np.ones(n)
    pos[0] = 0.0
    free = score_book(pos, up, day, 0.0, bars_per_day)
    if not free["total_return"] > 0:
        raise AssertionFailed(f"{label}: SIGN — long book on a rising series returned "
                              f"{free['total_return']:+.4%}, expected positive")
    down = up[::-1].copy()
    mirrored = score_book(pos, down, day, 0.0, bars_per_day)
    if not mirrored["total_return"] < 0:
        raise AssertionFailed(f"{label}: SIGN — long book on a falling series returned "
                              f"{mirrored['total_return']:+.4%}, expected negative")
    # Costs must bite, and bite monotonically.
    churn = np.zeros(n)
    churn[::2] = 1.0
    cheap = score_book(churn, up, day, 0.00001, bars_per_day)
    dear = score_book(churn, up, day, 0.0040, bars_per_day)
    if not dear["total_return"] < cheap["total_return"]:
        raise AssertionFailed(
            f"{label}: COST SIGN — 40 bp/side ({dear['total_return']:+.4%}) did not cost more "
            f"than 0.1 bp/side ({cheap['total_return']:+.4%})")


def audit_right_quantity(rungs: dict, label: str) -> None:
    """ASSERTION 3 — the grid scored is the one meant.

    Designs A and B are the SAME rule at 1d by construction (40 bars == 40 days) and a
    DIFFERENT rule at every other rung. If they agree anywhere above 1d, the design
    switch is not wired to anything."""
    a1d = rungs[("1d", "A")]["gross"]["total_return"]
    b1d = rungs[("1d", "B")]["gross"]["total_return"]
    if a1d != b1d:
        raise AssertionFailed(
            f"{label}: RIGHT-QUANTITY — designs A and B differ at 1d ({a1d:+.6%} vs "
            f"{b1d:+.6%}); they are the same 40/10-bar rule there and must be identical")
    same = [name for (name, design) in rungs if design == "A" and name != "1d"
            and rungs[(name, "A")]["gross"]["total_return"]
            == rungs[(name, "B")]["gross"]["total_return"]]
    if same:
        raise AssertionFailed(
            f"{label}: RIGHT-QUANTITY — designs A and B are identical at {same}, so the "
            "design switch is not reaching the window lengths")


def prove_assertions_can_fail(bars_per_day: int) -> list[str]:
    """A self-test that cannot fail is worse than none. Every audit above is run against
    a deliberately broken input and MUST raise."""
    proofs = []
    rng = np.random.default_rng(0)
    n = 3000
    close = 100.0 * np.cumprod(1.0 + rng.normal(0, 0.004, n))
    high = close * 1.002
    low = close * 0.998
    open_ = np.roll(close, 1)
    open_[0] = close[0]

    # 1a — break the second implementation by altering one bar's state.
    real = signal_second_implementation

    def peeking(high, low, close, n_entry, n_exit):
        sig = real(high, low, close, n_entry, n_exit).copy()
        sig[n_entry + 5] ^= 1
        return sig

    try:
        globals()["signal_second_implementation"] = peeking
        try:
            audit_lag(high, low, close, 40, 10, "break")
            raise SystemExit("lag audit did NOT raise on a deliberately altered second "
                             "implementation — the audit is inert")
        except AssertionFailed as exc:
            proofs.append(f"lag audit raises: {exc}")
    finally:
        globals()["signal_second_implementation"] = real

    # 1b — break the fill by removing the shift, so pos[k] sees close[k].
    real_pos = positions_from_signal
    try:
        globals()["positions_from_signal"] = lambda sig: sig.astype(np.float64)
        try:
            audit_no_lookahead(high, low, close, open_, 40, 10, "break", np.random.default_rng(1))
            raise SystemExit("look-ahead audit did NOT raise with the next_open shift removed "
                             "— the audit is inert")
        except AssertionFailed as exc:
            proofs.append(f"look-ahead audit raises: {exc}")
    finally:
        globals()["positions_from_signal"] = real_pos

    # 2 — break the sign by flipping the return in the scorer.
    real_score = score_book
    try:
        globals()["score_book"] = lambda pos, open_, day, rate, bpd: real_score(
            pos, open_[::-1].copy(), day, rate, bpd)
        try:
            audit_sign_in_money(bars_per_day, "break")
            raise SystemExit("sign audit did NOT raise with the price series reversed — the "
                             "audit is inert")
        except AssertionFailed as exc:
            proofs.append(f"sign audit raises: {exc}")
    finally:
        globals()["score_book"] = real_score

    # 3 — break the right-quantity check by scoring design B with design A's windows.
    fake = {("1d", "A"): {"gross": {"total_return": 0.10}},
            ("1d", "B"): {"gross": {"total_return": 0.11}},
            ("1h", "A"): {"gross": {"total_return": 0.20}},
            ("1h", "B"): {"gross": {"total_return": 0.20}}}
    try:
        audit_right_quantity(fake, "break")
        raise SystemExit("right-quantity audit did NOT raise on a grid where A and B "
                         "disagree at 1d — the audit is inert")
    except AssertionFailed as exc:
        proofs.append(f"right-quantity audit raises: {exc}")
    return proofs


# ===================================================================== the study


def run_symbol(symbol: str, base: dict[str, np.ndarray], proc: psutil.Process) -> dict:
    results: dict[tuple[str, str], dict] = {}
    rng = np.random.default_rng(NULL_SEED)
    audited: set[tuple[str, str]] = set()

    for name, minutes in LADDER:
        bars_per_day = MINUTES_PER_DAY // minutes
        rung = resample(base, minutes)
        drop = DROP_DAYS * bars_per_day
        open_ = rung["open"]
        day_idx = np.repeat(np.arange(len(base["day"])), bars_per_day)
        ts = rung["ts"]

        for design in ("A", "B"):
            multiple = bars_per_day if design == "A" else 1
            n_entry, n_exit = BASE_N_ENTRY * multiple, BASE_N_EXIT * multiple
            sig = signal_vectorised(rung["high"], rung["low"], rung["close"], n_entry, n_exit)
            pos_full = positions_from_signal(sig)

            # --- assertions, run on the two extreme rungs of each design (the cheapest
            # place a bug of this kind shows, and the most expensive to get wrong).
            if name in ("15m", "1d") and (name, design) not in audited:
                audit_lag(rung["high"], rung["low"], rung["close"], n_entry, n_exit,
                          f"{symbol}/{name}/{design}")
                audit_no_lookahead(rung["high"], rung["low"], rung["close"], open_,
                                   n_entry, n_exit, f"{symbol}/{name}/{design}", rng)
                audited.add((name, design))

            pos = pos_full[drop:]
            o = open_[drop:]
            d = day_idx[drop:]
            t = ts[drop:]

            entries, exits, gross_ret = trade_table(pos, o)
            hold = (exits - entries).astype(np.float64)

            cell: dict = {
                "frequency": name, "minutes": minutes, "design": design,
                "n_entry_bars": n_entry, "n_exit_bars": n_exit,
                "n_entry_days": n_entry / bars_per_day, "n_exit_days": n_exit / bars_per_day,
                "n_scored_bars": int(len(pos)),
                "span_start": str(pd.Timestamp(t[0])), "span_end": str(pd.Timestamp(t[-1])),
            }
            gross = score_book(pos, o, d, 0.0, bars_per_day)
            cell["gross"] = {k: v for k, v in gross.items() if not k.startswith("_")}
            cell["trades"] = trade_distribution(gross_ret, hold, bars_per_day, 0.0)
            cell["winners"] = winner_dependence(gross_ret, t[entries])

            for conv, bps in COST_CONVENTIONS.items():
                rate = bps / 1e4
                net = score_book(pos, o, d, rate, bars_per_day)
                cell[f"net_{conv}"] = {k: v for k, v in net.items() if not k.startswith("_")}
                cell[f"net_{conv}"]["cost_drag_sharpe_units"] = (
                    net["fee_drag_annual"] / gross["annual_vol"] if gross["annual_vol"] > 0
                    else float("nan"))
                cell[f"net_{conv}"]["mean_per_trade_minus_2c_bp"] = (
                    cell["trades"].get("mean_bp", float("nan")) - 2 * bps)
                gross_pnl = gross["total_return"]
                total_cost = gross["total_return"] - net["total_return"]
                cell[f"net_{conv}"]["cost_share_of_gross"] = (
                    total_cost / gross_pnl if gross_pnl != 0 else float("nan"))

            # Group 4 — the null, on the gross book (R15: the criterion is gross).
            # Deterministic per cell: Python's hash() is salted per process, so it must
            # never appear in a seed. zlib.crc32 is stable across runs and machines.
            tag = f"{symbol}|{name}|{design}".encode()
            null = rotation_null(pos, o, N_NULLS, NULL_SEED + zlib.crc32(tag))
            score = cell["trades"].get("mean_bp", float("nan"))
            cell["null"] = {k: v for k, v in null.items() if not k.startswith("_")}
            cell["null"]["observed_mean_bp"] = score
            cell["null"]["percentile"] = (
                float((null["_means"] < score).mean() * 100) if not math.isnan(score) else float("nan"))
            cell["null"]["decisive"] = bool(score > null["mean_bp_p95"])
            cell["null"]["observed_total_return"] = gross["total_return"]
            cell["null"]["total_return_percentile"] = float(
                (null["_totals"] < gross["total_return"]).mean() * 100)

            results[(name, design)] = cell
            del sig, pos_full, pos, o, d, t, null

        # Spread of the instrument actually held, off THIS rung's own OHLC.
        if name == "1d":
            results[("1d", "A")]["corwin_schultz_bp_per_side"] = corwin_schultz(
                rung["high"][drop:], rung["low"][drop:])
        del rung, open_, day_idx, ts

    audit_right_quantity(results, symbol)
    return {f"{k[0]}|{k[1]}": v for k, v in results.items()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    proc = psutil.Process()
    t0 = time.time()

    print("proving every assertion can fail ...")
    for line in prove_assertions_can_fail(96):
        print("  OK  " + line[:160])
    if args.selftest:
        return

    print("loading the 15m base ...")
    base = load_base()
    for symbol in SYMBOLS:
        print(f"  {symbol}: {len(base[symbol]['open']):,} bars, "
              f"{len(base[symbol]['day']):,} complete UTC days, "
              f"{pd.Timestamp(base[symbol]['ts'][0])} -> {pd.Timestamp(base[symbol]['ts'][-1])}")

    out: dict = {
        "record": "D389",
        "prereg": "docs/decisions/D389-PREREG-the-D163-recost.md",
        "fixture": FIXTURE.name,
        "cost_conventions_bp_per_side": COST_CONVENTIONS,
        "reference_gross_sharpe_2015_2025_daily": REFERENCE_GROSS_SHARPE,
        "n_nulls": N_NULLS,
        "drop_days_front": DROP_DAYS,
        "symbols": {},
    }
    for symbol in SYMBOLS:
        print(f"scoring {symbol} ...")
        out["symbols"][symbol] = run_symbol(symbol, base[symbol], proc)
        print(f"  peak WS so far: {proc.memory_info().peak_wset / 1e9:.2f} GB")

    peak = proc.memory_info().peak_wset / 1e9
    out["peak_working_set_gb"] = peak
    out["elapsed_seconds"] = time.time() - t0
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(out, indent=2, default=float))
    print(f"\nwrote {SUMMARY}  ({time.time() - t0:.0f}s, peak working set {peak:.2f} GB)")


if __name__ == "__main__":
    main()
