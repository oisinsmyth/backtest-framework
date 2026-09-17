"""MACD and the two strictly simpler rules it must be measured against (D217).

This module exists to serve one question, and it is not "does MACD make money":

    Does the signal line add anything over the zero-line cross, and does the
    zero-line cross add anything over plain time-series momentum?

The three rungs are strictly nested, and the nesting is structural rather than
prose: `zero_line_score` and `signal_line_score` both read the SAME `MacdSeries`,
so a future edit cannot desynchronise them without deleting a test.

WHY THE LADDER IS THE STUDY
---------------------------
An EMA is linear and both EMAs' weights sum to 1, so the MACD's weighting of
price LEVELS sums to zero — and by Abel summation a zero-sum weighting of levels
is a weighting of RETURNS:

    macd_t = sum_i c_i * r_(t-i),    c_i = lam_s**(i+1) - lam_f**(i+1),
                                     lam  = (n - 1) / (n + 1)

For (12, 26) every c_i > 0: a strictly positive, hump-shaped kernel over roughly
the last 40 returns. Two exact consequences, both pinned by test:

    sum(c_i)        = (slow - 1)/2 - (fast - 1)/2 = 12.5 - 5.5 = 7.0
    centre of mass  = (a**2 - b**2)/(a - b) = a + b = 18.0 bars exactly

A flat N-bar momentum kernel has centre of mass (N - 1)/2, so the MATCHED
control is N = 37 — `MATCHED_MOMENTUM_LOOKBACK` below. It is derived, not chosen,
and D217 records that 26 (the slow period, the obvious guess) would have been
centred 12.5 bars back against the MACD's 18 and made the comparison unmatched.

And because (I - EMA_signal) annihilates constants, the SIGNAL-LINE rule's return
kernel sums to exactly ZERO: under constant drift b the MACD sits at 7b and the
signal line converges to 7b, so the histogram converges to 0. The signal line is
not more trend on top of trend — it converts a trend-LEVEL rule into a
trend-ACCELERATION rule. That is the sharpest statement of what it adds and it is
what D217's H1 and H7 test.

SEEDING, AND WHY THIS ONE
-------------------------
There is no other EMA in this codebase, so the seed convention is a decision
rather than a detail, and it is stated here the way `structure.rsi` states its
own: WHICH ONE IS USED CHANGES THE NUMBERS.

Both EMAs are SMA-seeded at the same index `slow - 1`, each over its OWN window
length — the slow leg over closes[0:slow], the fast leg over the LAST `fast`
closes, i.e. closes[slow-fast:slow]. The signal line is then SMA-seeded over the
first `signal` MACD values. alpha = 2/(n+1) throughout.

The justification is an exactness property nothing else has. Solve the steady
state of E_t = a*c_t + (1-a)*E_(t-1) on a linear path c_t = p + q*t: the offset is
q*(n-1)/2, which is exactly the mean of the last n values. So ON A RAMP THE
SMA-SEEDED EMA HAS ZERO SEED ERROR AT EVERY BAR FROM THE SEED ONWARD — hence
macd == 7q and histogram == 0 exactly, with no burn-in at all. A first-value seed
and a zero seed both carry a transient. That is a real discriminator, not taste.

Rejected alternative, recorded because it is also "SMA-seeded": seeding the fast
leg at index `fast - 1` over closes[0:fast] and running it forward. It loses the
ramp-exactness above and makes `macd` start at a bar where its two legs have seen
different amounts of history.

BURN-IN — A RESEARCH-INTEGRITY PARAMETER, NOT A NUMERICAL ONE
-------------------------------------------------------------
MACD is the FIRST IIR ESTIMATOR IN A CODEBASE BUILT ENTIRELY ON FIR WINDOWS.
Every other indicator here — Donchian, ATR, the SMA gate, realized vol, the
z-score — is a function of an explicit range(i-w, i). The MACD's value at t
depends on where the run STARTED, so two studies over different date ranges see
different MACD at the same calendar bar. Nothing else in this repo does that, and
a reader carrying the FIR mental model will misread this file without the warning.

Two seeds differing by D differ by D * lam**k after k bars, so requiring a residual
of 1e-12 * price from a worst-case O(price) seed error gives

    burn_in(n) = ceil(ln(1e-12) / ln((n-1)/(n+1)))
    n=12 -> 166      n=9 -> 124      n=26 -> 360  (binding)

`warm_up_bars(12, 26, 9)` is therefore 25 + 8 + 360 = 393 — about 15.6% of a
2,515-bar daily series, which is a real cost and is stated rather than hidden.

It is NOT zero-risk: a crossing whose margin is within 1e-12 * price of zero can
still have its sign flipped by the seed. That is a knife-edge property of the
RULE, not of the seed (D217 H7), and the honest response is to measure the
resulting turnover, which `crossings` and the position builders below support.

D44: every window here ends at the bar it is indexed by, and the caller is
responsible for the fill landing at the next open. `trailing_ma` is the one
auxiliary ESTIMATE in this module and it ends at t inclusive for the same reason
`breakout.TrendGateFilter` compares against a completed bar.
"""

from __future__ import annotations

import math
import statistics
from collections.abc import Sequence
from dataclasses import dataclass

from backtest_framework.data.bars import TimestampedBar

# Appel 1979. Famous BECAUSE people found it worked, which makes any result at
# exactly this triple meta-in-sample by a search this project did not run and
# cannot count (D70/D22). D217 leads its report with the plateau, not this cell.
DEFAULT_FAST = 12
DEFAULT_SLOW = 26
DEFAULT_SIGNAL = 9

# Derived in the module docstring: the flat kernel whose centre of mass matches
# the MACD's 18.0 bars exactly. Pinned by test — a future edit that substitutes a
# round 20 or 50 destroys the nesting and the study with it.
MATCHED_MOMENTUM_LOOKBACK = 37

# The residual a seed difference must decay to, as a fraction of price, before the
# strategy is allowed to act on the number.
SEED_RESIDUAL = 1e-12


def _alpha(window: int) -> float:
    return 2.0 / (window + 1.0)


def _decay(window: int) -> float:
    return (window - 1.0) / (window + 1.0)


def burn_in_bars(window: int, residual: float = SEED_RESIDUAL) -> int:
    """Bars until a worst-case seed difference has decayed below `residual` * price.

    Not a numerical nicety — see the module docstring. This is what makes an IIR
    estimator safe to use in a walk-forward at all, because without it changing
    the prefix length changes every number downstream."""
    if window < 2:
        raise ValueError(f"window must be >= 2, got {window}")
    return math.ceil(math.log(residual) / math.log(_decay(window)))


def warm_up_bars(
    fast: int = DEFAULT_FAST,
    slow: int = DEFAULT_SLOW,
    signal: int = DEFAULT_SIGNAL,
    *,
    include_burn_in: bool = True,
) -> int:
    """First index at which a signal-line score may be acted on.

    `include_burn_in=False` gives the classic, live-seed MACD's first defined bar
    and exists for the golden master, which pins exactly the regime where the seed
    convention is visible. It is not a research setting."""
    _validate(fast, slow, signal)
    seeded = (slow - 1) + (signal - 1)
    return seeded + burn_in_bars(slow) if include_burn_in else seeded


def _validate(fast: int, slow: int, signal: int) -> None:
    # Loud, eager, at construction rather than at bar 400 (D99).
    if fast < 2 or slow < 2 or signal < 2:
        raise ValueError(f"windows must be >= 2, got fast={fast} slow={slow} signal={signal}")
    if fast >= slow:
        raise ValueError(f"fast must be < slow, got fast={fast} slow={slow}")


@dataclass(frozen=True)
class MacdSeries:
    """MACD, its signal line and the histogram, aligned 1:1 with the input bars.

    Entries before the relevant seed are NaN, never a partial value — the
    `terrain.rolling_mean_true_range` convention, and the reason is the same: a
    partial value is a different estimator wearing the same name."""

    macd: tuple[float, ...]
    signal: tuple[float, ...]
    histogram: tuple[float, ...]
    fast: int
    slow: int
    signal_window: int

    @property
    def first_macd_index(self) -> int:
        return self.slow - 1

    @property
    def first_signal_index(self) -> int:
        return (self.slow - 1) + (self.signal_window - 1)


def macd_series(
    bars: Sequence[TimestampedBar],
    fast: int = DEFAULT_FAST,
    slow: int = DEFAULT_SLOW,
    signal: int = DEFAULT_SIGNAL,
) -> MacdSeries:
    """The full MACD triple over `bars`, on closes, seeded as the docstring states."""
    _validate(fast, slow, signal)
    closes = [b.bar.close for b in bars]
    n = len(closes)
    nan = math.nan

    macd = [nan] * n
    sig = [nan] * n
    hist = [nan] * n
    if n < slow:
        return MacdSeries(tuple(macd), tuple(sig), tuple(hist), fast, slow, signal)

    seed = slow - 1
    # Both legs seeded at the SAME index, each over its own window length. Seeding
    # the fast leg from bar 0 would leave the two legs with different amounts of
    # history at the first MACD value; see the rejected alternative in the docstring.
    ema_slow = statistics.fmean(closes[0:slow])
    ema_fast = statistics.fmean(closes[slow - fast : slow])
    a_slow, a_fast = _alpha(slow), _alpha(fast)

    macd[seed] = ema_fast - ema_slow
    for t in range(seed + 1, n):
        ema_slow += a_slow * (closes[t] - ema_slow)
        ema_fast += a_fast * (closes[t] - ema_fast)
        macd[t] = ema_fast - ema_slow

    sig_seed = seed + signal - 1
    if sig_seed < n:
        ema_sig = statistics.fmean(macd[seed : seed + signal])
        a_sig = _alpha(signal)
        sig[sig_seed] = ema_sig
        hist[sig_seed] = macd[sig_seed] - ema_sig
        for t in range(sig_seed + 1, n):
            ema_sig += a_sig * (macd[t] - ema_sig)
            sig[t] = ema_sig
            hist[t] = macd[t] - ema_sig

    return MacdSeries(tuple(macd), tuple(sig), tuple(hist), fast, slow, signal)


def return_kernel(fast: int, slow: int, terms: int) -> tuple[float, ...]:
    """The MACD's weighting of past returns, c_i = lam_s**(i+1) - lam_f**(i+1).

    Exposed because it is the study's thesis in executable form, and because a test
    that pins `sum` to 7.0 and the centre of mass to 18.0 is what stops the ladder
    quietly ceasing to be nested."""
    _validate(fast, slow, 2)
    lam_f, lam_s = _decay(fast), _decay(slow)
    return tuple(lam_s ** (i + 1) - lam_f ** (i + 1) for i in range(terms))


# --------------------------------------------------------------------------
# The three rungs. Nested by construction: R1 and R2 read the same MacdSeries.
# --------------------------------------------------------------------------


def signal_line_score(series: MacdSeries) -> tuple[float, ...]:
    """RUNG 1 — macd - signal. A trend-ACCELERATION rule (kernel sums to zero)."""
    return series.histogram


def zero_line_score(series: MacdSeries) -> tuple[float, ...]:
    """RUNG 2 — macd itself.

    This is EXACTLY the fast/slow EMA crossover: `macd > 0` is the event
    `EMA(fast) > EMA(slow)`, and the signal line plays no part in it. That it is
    the same `series.macd` rung 1 subtracts from is the structural proof of the
    nesting — there is no second, hand-rolled `ema_fast > ema_slow` comparison
    anywhere in this module, and there must never be one."""
    return series.macd


def trailing_return_score(
    bars: Sequence[TimestampedBar], lookback: int = MATCHED_MOMENTUM_LOOKBACK
) -> tuple[float, ...]:
    """RUNG 3 — the floor. close(t)/close(t-lookback) - 1, NaN before it exists.

    `lookback` defaults to the centre-of-mass-matched 37, not to a round number."""
    if lookback < 1:
        raise ValueError(f"lookback must be >= 1, got {lookback}")
    closes = [b.bar.close for b in bars]
    out = [math.nan] * len(closes)
    for t in range(lookback, len(closes)):
        prior = closes[t - lookback]
        if prior > 0.0:
            out[t] = closes[t] / prior - 1.0
    return tuple(out)


def trailing_ma(bars: Sequence[TimestampedBar], window: int) -> tuple[float, ...]:
    """Simple moving average ending at t INCLUSIVE — the 200-MA confluence gate.

    Inclusive because it gates a decision taken on a completed bar and filled at
    the next open, which is `breakout.TrendGateFilter`'s reading of D44: the rule
    is about trailing ESTIMATES, not about the trigger comparison itself."""
    if window < 1:
        raise ValueError(f"window must be >= 1, got {window}")
    closes = [b.bar.close for b in bars]
    out = [math.nan] * len(closes)
    for t in range(window - 1, len(closes)):
        out[t] = statistics.fmean(closes[t - window + 1 : t + 1])
    return tuple(out)


# --------------------------------------------------------------------------
# Turning a score into a position series
# --------------------------------------------------------------------------


def positions(
    score: Sequence[float],
    *,
    start: int,
    long_short: bool,
    gate: Sequence[float] | None = None,
    closes: Sequence[float] | None = None,
) -> tuple[float, ...]:
    """Position per bar from the sign of `score`, flat everywhere before `start`.

    A crossover rule is MEMORYLESS: "long on a cross above, exit on a cross below"
    produces exactly the path 1{score > 0}. Writing it as a level rule rather than
    an event rule is strictly better — it is self-healing, and it removes an entire
    class of state-desync bugs — and it is the same series either way.

    `start` is the LADDER'S common warm-up, not this arm's own. If each arm began
    on its own first eligible bar the three equity curves would cover different
    spans and the ladder would not be a comparison (D217). The caller passes the
    max across the ladder; this function does not guess it.

    Ties are flat. `score == 0.0` is exact and reachable — a perfectly flat market
    gives macd == 0.0 exactly — so the strict `>` is a stated policy, not an
    accident of floating point.

    `gate`/`closes` are the 200-MA confluence filter: a long is only taken when
    close > MA, a short only when close < MA. A gated bar stands aside rather than
    inverting, because inverting would be a different rule."""
    if gate is not None and closes is None:
        raise ValueError("a gate needs closes to compare against")

    out = [0.0] * len(score)
    for t in range(start, len(score)):
        s = score[t]
        if s != s:  # NaN — the arm cannot evaluate, so it stands aside
            continue
        side = 1.0 if s > 0.0 else (-1.0 if s < 0.0 else 0.0)
        if not long_short and side < 0.0:
            side = 0.0
        if side != 0.0 and gate is not None:
            if closes is None:
                raise ValueError(
                    "a gate series was supplied without the closes it gates: `gate` and "
                    "`closes` travel together, and only `closes` can say which side of it "
                    "the price is on"
                )
            g = gate[t]
            if g != g or (side > 0.0 and closes[t] <= g) or (side < 0.0 and closes[t] >= g):
                side = 0.0
        out[t] = side
    return tuple(out)


def crossings(position: Sequence[float]) -> int:
    """Number of bars on which the position changed — the turnover count H7 predicts."""
    return sum(1 for a, b in zip(position, position[1:]) if a != b)


# --------------------------------------------------------------------------
# Impulse MACD (LazyBear, 2015) — D218
#
# NOT a MACD variant. There is no difference of two EMAs of one series anywhere
# in it. It is a zero-lag mid price measured against a slow smoothed high/low
# channel, with a dead zone, and an SMA signal line on top. Structurally it is
# closer to this project's Donchian breakout book than to the ladder above.
#
# The two exact properties that make it worth running, both pinned by test:
#
#   * `smma(x, n)` is Wilder smoothing — an EMA with alpha = 1/n, NOT the
#     2/(n+1) convention used above. Effective period 2n-1 = 67 at n=34, and it
#     lags a linear ramp by exactly (n-1)*b = 33b.
#   * `zlema = 2*EMA1 - EMA2` has centre of mass EXACTLY ZERO: EMA1 lags a ramp
#     by (n-1)/2 and EMA2 by (n-1), so the combination lags by
#     2*(n-1)/2 - (n-1) = 0. The name is accurate.
#
# So on constant drift b with no bar range, mi = c_t and hi = c_t - 33b, giving
# **md = 33b** — the same shape as `macd = 7b` above — and since SMA(md, 9)
# converges to 33b as well, **sh -> 0**.
#
# THE SAME LEVEL/ACCELERATION DECOMPOSITION, ON A CONSTRUCTION THAT SHARES NO
# ARITHMETIC WITH MACD. `md` is a trend-LEVEL rule; `sh` is a trend-ACCELERATION
# rule. That is why D218 is a replication of D217 rather than a new indicator.
# --------------------------------------------------------------------------

IMPULSE_LENGTH = 34
IMPULSE_SIGNAL = 9


def burn_in_for_alpha(alpha: float, residual: float = SEED_RESIDUAL) -> int:
    """Bars until a worst-case seed difference decays below `residual` * price.

    `burn_in_bars` above assumes alpha = 2/(n+1). Wilder smoothing uses 1/n, which
    decays far more slowly, and hard-coding the wrong alpha here would understate
    the burn-in by a factor of nearly three."""
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")
    return math.ceil(math.log(residual) / math.log(1.0 - alpha))


def _recurse(values: Sequence[float], alpha: float, seed_index: int, seed: float) -> list[float]:
    out = [math.nan] * len(values)
    if seed_index >= len(values):
        return out
    current = seed
    out[seed_index] = current
    for t in range(seed_index + 1, len(values)):
        current += alpha * (values[t] - current)
        out[t] = current
    return out


def smma(values: Sequence[float], window: int) -> tuple[float, ...]:
    """Wilder's smoothed moving average, SMA-seeded — the Pine `calc_smma`.

    `s[t] = (s[t-1]*(n-1) + x[t]) / n` is algebraically `s + (1/n)(x - s)`, i.e.
    an EMA with alpha = 1/n. Seeded with the simple mean of the first `n` values
    at index `n-1`, which is what Pine's `na(smma[1]) ? sma(src, len)` does on the
    first bar where the window is full."""
    if window < 2:
        raise ValueError(f"window must be >= 2, got {window}")
    if len(values) < window:
        return tuple([math.nan] * len(values))
    seed = statistics.fmean(values[:window])
    return tuple(_recurse(values, 1.0 / window, window - 1, seed))


def zlema(values: Sequence[float], window: int) -> tuple[float, ...]:
    """Zero-lag EMA — the Pine `calc_zlema`: `e1 + (e1 - e2)` where `e2 = ema(e1)`.

    Both legs use alpha = 2/(n+1) and the SMA seed this module already uses. `e2`
    cannot start until `e1` has `n` values of its own, so the result first exists
    at index `2(n-1)` — 66 bars at n=34, before any burn-in."""
    if window < 2:
        raise ValueError(f"window must be >= 2, got {window}")
    n = len(values)
    if n < 2 * window - 1:
        return tuple([math.nan] * n)
    alpha = _alpha(window)
    e1 = _recurse(values, alpha, window - 1, statistics.fmean(values[:window]))
    second_seed = 2 * (window - 1)
    e2 = _recurse(e1, alpha, second_seed, statistics.fmean(e1[window - 1 : 2 * window - 1]))
    return tuple(
        math.nan if math.isnan(e2[t]) else 2.0 * e1[t] - e2[t] for t in range(n)
    )


def _sma(values: Sequence[float], window: int) -> tuple[float, ...]:
    out = [math.nan] * len(values)
    for t in range(len(values)):
        chunk = values[t - window + 1 : t + 1]
        if len(chunk) == window and not any(v != v for v in chunk):
            out[t] = statistics.fmean(chunk)
    return tuple(out)


@dataclass(frozen=True)
class ImpulseSeries:
    """Impulse MACD and its parts, aligned 1:1 with the input bars."""

    md: tuple[float, ...]
    signal: tuple[float, ...]
    histogram: tuple[float, ...]
    mi: tuple[float, ...]
    hi: tuple[float, ...]
    lo: tuple[float, ...]
    mid: tuple[float, ...]
    """`smma(close, length)` — the channel collapsed to one average. Not part of the
    published indicator; it is the I3 control that deletes the dead zone."""
    length: int
    signal_window: int

    @property
    def first_md_index(self) -> int:
        return 2 * (self.length - 1)

    @property
    def first_signal_index(self) -> int:
        return self.first_md_index + self.signal_window - 1


def impulse_macd_series(
    bars: Sequence[TimestampedBar],
    length: int = IMPULSE_LENGTH,
    signal: int = IMPULSE_SIGNAL,
) -> ImpulseSeries:
    """Impulse MACD as published, plus the one extra series the I3 control needs."""
    if length < 2 or signal < 2:
        raise ValueError(f"windows must be >= 2, got length={length} signal={signal}")
    highs = [b.bar.high for b in bars]
    lows = [b.bar.low for b in bars]
    closes = [b.bar.close for b in bars]
    hlc3 = [(h + lo + c) / 3.0 for h, lo, c in zip(highs, lows, closes)]

    hi = smma(highs, length)
    lo = smma(lows, length)
    mid = smma(closes, length)
    mi = zlema(hlc3, length)

    md: list[float] = []
    for m, h, low in zip(mi, hi, lo):
        if m != m or h != h or low != low:
            md.append(math.nan)
        elif m > h:
            md.append(m - h)
        elif m < low:
            md.append(m - low)
        else:
            md.append(0.0)  # the dead zone — a stated value, not a missing one

    sig = _sma(md, signal)
    hist = tuple(
        math.nan if (a != a or b != b) else a - b for a, b in zip(md, sig)
    )
    return ImpulseSeries(tuple(md), sig, hist, mi, hi, lo, mid, length, signal)


def impulse_warm_up_bars(
    length: int = IMPULSE_LENGTH,
    signal: int = IMPULSE_SIGNAL,
    *,
    include_burn_in: bool = True,
) -> int:
    """First index at which an Impulse MACD score may be acted on.

    The Wilder legs dominate and they dominate badly: alpha = 1/34 decays so slowly
    that the seed takes **926 bars** to become irrelevant at 1e-12 of price, against
    360 for the 26-period EMA above. Total warm-up is 1,000 bars — about four years
    of daily data — and that is a real property of the indicator worth knowing
    before anyone runs it on a short series."""
    seeded = 2 * (length - 1) + (signal - 1)
    if not include_burn_in:
        return seeded
    return seeded + max(burn_in_for_alpha(1.0 / length), burn_in_for_alpha(_alpha(length)))


# The three rungs. I1 and I2 read the SAME ImpulseSeries, for the same reason the
# MACD rungs above do: nestedness has to be structural or it drifts.


def impulse_signal_score(series: ImpulseSeries) -> tuple[float, ...]:
    """RUNG I1 — `sh = md - sma(md, 9)`. Trend ACCELERATION (kernel sums to zero)."""
    return series.histogram


def impulse_band_score(series: ImpulseSeries) -> tuple[float, ...]:
    """RUNG I2 — `md` itself: the band state, dead zone included.

    `md > 0` is exactly `mi > hi` and `md < 0` is exactly `mi < lo`; inside the
    channel it is exactly `0.0`, so a sign rule stands aside there rather than
    guessing. Trend LEVEL."""
    return series.md


def impulse_no_deadzone_score(series: ImpulseSeries) -> tuple[float, ...]:
    """RUNG I3 — `mi - smma(close, length)`: I2 with the channel collapsed to its
    midpoint, so the ONLY difference between I2 and I3 is the dead zone."""
    return tuple(
        math.nan if (m != m or c != c) else m - c for m, c in zip(series.mi, series.mid)
    )
