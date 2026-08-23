"""Trading the terrain levels, against the same strategy on random levels.

A different question from the one `terrain_nulls.py` asks. That harness measures whether
price *behaves* differently at a sensor's levels — three reaction statistics, no costs.
This one measures whether *trading* them beats trading levels scattered at random, in
money, after fees. Costs are what have killed nearly everything in this project, and the
reaction test could never see them.

## Why the null is the same strategy, not no strategy

Every arm runs identical rules, identical costs, identical sizing. Only the level set
differs — real against `terrain_nulls.pseudo_levels`, which already matches count and
span. So the strategy's design choices largely cancel: a bad exit rule is a bad exit rule
in both arms. Comparing a level strategy against buy-and-hold, or against zero, would
confound the sensor with the strategy and could be rescued by tuning either.

**What pairing does not cancel** is D189's H2 confound. Real levels sit where price has
repeatedly been; random ones do not. A strategy that enters on a touch will therefore find
more entries near price in the real arm regardless of whether the levels mean anything.
Trade counts are reported per arm so that this is visible rather than absorbed.

## The band width is per bar, and getting that wrong is a 300x error

`half_width` is a SERIES, not a scalar, and the signatures take it that way on purpose. It
was a scalar in the first draft and the consequence was found before any result: BTC runs
from about $300 to $100,000 across this fixture, so one ATR-derived band applied to the
whole history was four times the entire price in 2015. A stop at the far edge then risked
more than 100% of capital and a single short returned -105%.

That is the same shape as D187 (a scale-dependent quantity applied across instruments and
eras that do not share the scale) and the same shape as D194's calendar matching. The band
at bar t is `cluster_atr x ATR(t)` — what the sensor itself used when it drew the level.

## The one place this design lies if you let it

Entering AT a level is a limit order, and D9 recorded why that is dangerous before any of
this existed:

> Touch != fill (queue position) and bar-level limit fills are ADVERSELY SELECTED. Keep
> both; compare sensitivity.

Adverse selection is the whole risk for a bounce strategy: you are reliably filled on the
levels price blows through and miss some it bounces off. So `FillAssumption` carries both
conventions, every limit strategy runs under both, and the pessimistic one carries the
verdict.

## Three strategies, and only one of them carries a verdict

- `touch_horizon` — enter on touch, exit after `HORIZON` bars or on invalidation. Zero new
  parameters; every constant inherited. The strategy-level analogue of `p_reversal`.
- `bounce_rr` — limit entry at the level, stop at the far band edge, target at a fixed
  R multiple, then a trailing stop once 1R in profit. The trader's version.
- `level_stop` — not implemented here: it modifies an existing book's stop rather than
  generating its own trades, so it belongs in the breakout study's harness.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence

import numpy as np

from ..data.bars import TimestampedBar
from .terrain import rolling_mean_true_range
from .terrain_nulls import HORIZON, pseudo_levels

TARGET_R = (2.0, 3.0)
"""Reward multiples of the stop distance. Two values, fixed — a swept target ratio is the
easiest way to rescue a weak signal, so the set is named before any run."""

TRAIL_AFTER_R = 1.0
"""Profit, in R, before the trailing stop engages. Below this the trail would simply be
the entry stop under another name."""

TRAIL_LOOKBACK = 10
"""Bars in the trailing channel. This is `trail_10`, the incumbent D174 benchmarked
`swing_k2` against — reused rather than re-chosen so there is a precedent behind it."""

MAX_HOLD = 60
"""Hard cap on holding period, in bars. Not an exit rule that competes with the others: a
backstop so a level that never invalidates and never reaches stop or target cannot hold a
position for the rest of the series and turn the test into a buy-and-hold comparison."""


class FillAssumption(Enum):
    """D9's two conventions, both run, pessimistic carrying the verdict."""

    TOUCH = "touch"
    """Filled if the bar's range reaches the limit. Optimistic: ignores queue position."""

    TRADE_THROUGH = "trade_through"
    """Filled only if the bar trades THROUGH the limit by epsilon. Pessimistic, and the
    honest one for a bounce strategy — being filled only when price keeps going is
    precisely the adverse selection D9 named."""


TRADE_THROUGH_EPS = 1e-9


@dataclass(frozen=True)
class Trade:
    entry_index: int
    exit_index: int
    direction: int
    entry_price: float
    exit_price: float
    reason: str

    @property
    def gross_return(self) -> float:
        return self.direction * (self.exit_price / self.entry_price - 1.0)


@dataclass(frozen=True)
class StrategyResult:
    trades: tuple[Trade, ...]
    cost_bps: float
    periods_per_year: float

    @property
    def n_trades(self) -> int:
        return len(self.trades)

    @property
    def net_returns(self) -> list[float]:
        """Per-trade net return: gross less a round-trip charge in basis points."""
        charge = 2.0 * self.cost_bps / 10_000.0
        return [t.gross_return - charge for t in self.trades]

    @property
    def total_return(self) -> float:
        equity = 1.0
        for r in self.net_returns:
            equity *= 1.0 + r
        return equity - 1.0

    @property
    def hit_rate(self) -> float:
        rs = self.net_returns
        return sum(1 for r in rs if r > 0) / len(rs) if rs else 0.0

    def equity_curve(self, bars: Sequence[TimestampedBar]) -> list[float]:
        """Equity per BAR, marked to market while a position is open.

        Needed because the verdict is compared against buy-and-hold, and a per-trade
        Sharpe is not comparable to a daily one — a strategy holding 20 positions a decade
        would look spectacular on trade-frequency annualisation and flat on a curve.
        Marking to market rather than stepping at exits also stops a strategy from hiding
        an open drawdown between its entry and its stop.

        Full equity per trade, no leverage, one position at a time. A stated assumption,
        identical in both arms, and not a sizing recommendation."""
        equity = [1.0] * len(bars)
        charge = 2.0 * self.cost_bps / 10_000.0
        current = 1.0
        by_entry = {t.entry_index: t for t in self.trades}
        open_trade: Trade | None = None
        for i in range(len(bars)):
            if open_trade is None and i in by_entry:
                open_trade = by_entry[i]
            if open_trade is not None:
                move = open_trade.direction * (
                    bars[i].bar.close / open_trade.entry_price - 1.0
                )
                equity[i] = current * (1.0 + move)
                if i >= open_trade.exit_index:
                    realised = open_trade.gross_return - charge
                    current = current * (1.0 + realised)
                    equity[i] = current
                    open_trade = None
            else:
                equity[i] = current
        return equity

    def curve_sharpe(self, bars: Sequence[TimestampedBar], periods_per_year: float) -> float:
        """Annualised Sharpe of the per-bar equity curve. Comparable to buy-and-hold."""
        curve = self.equity_curve(bars)
        rets = [
            math.log(b / a) for a, b in zip(curve, curve[1:]) if a > 0.0 and b > 0.0
        ]
        if len(rets) < 3:
            return 0.0
        sd = statistics.stdev(rets)
        if sd <= 0.0:
            return 0.0
        return (statistics.fmean(rets) / sd) * math.sqrt(periods_per_year)

    def curve_total_return(self, bars: Sequence[TimestampedBar]) -> float:
        return self.equity_curve(bars)[-1] - 1.0

    def max_drawdown(self, bars: Sequence[TimestampedBar]) -> float:
        curve = self.equity_curve(bars)
        peak, worst = curve[0], 0.0
        for x in curve:
            peak = max(peak, x)
            if peak > 0.0:
                worst = min(worst, x / peak - 1.0)
        return worst

    def sharpe(self, bars_held_total: int) -> float:
        """Per-trade Sharpe annualised by realised trade frequency.

        Annualising by trade count rather than by bar would flatter a strategy that
        trades rarely, which is exactly the defect the final report records in the
        inverse-vol weighting — a book paid for being absent."""
        rs = self.net_returns
        if len(rs) < 3:
            return 0.0
        sd = statistics.stdev(rs)
        if sd <= 0.0:
            return 0.0
        trades_per_year = len(rs) * self.periods_per_year / max(bars_held_total, 1)
        return (statistics.fmean(rs) / sd) * math.sqrt(max(trades_per_year, 1e-9))


def band_half_widths(
    bars: Sequence[TimestampedBar], atr_window: int, cluster_atr: float
) -> list[float]:
    """The band half-width at every bar — `cluster_atr x ATR(t)`, NaN before warm-up.

    Reuses D194's rolling ATR, which is pinned against the per-call form by test."""
    return [
        w * cluster_atr if w == w else float("nan")
        for w in rolling_mean_true_range(bars, atr_window)
    ]


def _touch_entries(
    bars: Sequence[TimestampedBar],
    levels_by_index: dict[int, tuple[float, ...]],
    half_width: Sequence[float],
) -> list[tuple[int, float, int]]:
    """(bar, level price, direction) for the first bar of each approach into a band.

    The same "first bar of an approach" convention `terrain_nulls.level_reactions` uses,
    so a price sitting inside a band for a week is one entry rather than seven. Direction
    is toward the side price came from: an approach from above is a long (demand), from
    below a short (supply). That is the bounce hypothesis and nothing else."""
    schedule = sorted(levels_by_index)
    if not schedule:
        return []
    active: tuple[float, ...] = ()
    inside: dict[float, bool] = {}
    next_change = 0
    out: list[tuple[int, float, int]] = []

    for t in range(schedule[0], len(bars)):
        if next_change < len(schedule) and t >= schedule[next_change]:
            active = tuple(levels_by_index[schedule[next_change]])
            inside = {lv: False for lv in active}
            next_change += 1
        if not active or t == 0:
            continue
        hw = half_width[t]
        if not (hw > 0.0):  # NaN before warm-up, and NaN fails every comparison
            continue
        close, prev = bars[t].bar.close, bars[t - 1].bar.close
        for level in active:
            in_band = abs(close - level) <= hw
            was = inside.get(level, False)
            inside[level] = in_band
            if not in_band or was:
                continue
            out.append((t, level, 1 if prev > level else -1))
    return out


def run_touch_horizon(
    bars: Sequence[TimestampedBar],
    levels_by_index: dict[int, tuple[float, ...]],
    half_width: Sequence[float],
    cost_bps: float,
    periods_per_year: float,
    horizon: int = HORIZON,
) -> StrategyResult:
    """Enter on touch at the close, exit `horizon` bars later. Zero new parameters."""
    trades = []
    for t, level, direction in _touch_entries(bars, levels_by_index, half_width):
        exit_index = min(t + horizon, len(bars) - 1)
        if exit_index <= t:
            continue
        trades.append(
            Trade(t, exit_index, direction, bars[t].bar.close,
                  bars[exit_index].bar.close, "horizon")
        )
    return StrategyResult(tuple(trades), cost_bps, periods_per_year)


def run_bounce_rr(
    bars: Sequence[TimestampedBar],
    levels_by_index: dict[int, tuple[float, ...]],
    half_width: Sequence[float],
    cost_bps: float,
    periods_per_year: float,
    target_r: float,
    fill: FillAssumption,
    trail_lookback: int = TRAIL_LOOKBACK,
    max_hold: int = MAX_HOLD,
) -> StrategyResult:
    """Limit entry at the level, stop at the far band edge, target at `target_r`, then a
    trailing channel stop once 1R in profit.

    Intrabar ordering is pessimistic throughout and deliberately so: when a bar's range
    covers both the stop and the target, the STOP is taken. A bar's OHLC does not say
    which came first, and resolving that ambiguity in the strategy's favour is how a
    backtest manufactures an edge it will not have."""
    trades: list[Trade] = []
    open_until = -1

    for t, level, direction in _touch_entries(bars, levels_by_index, half_width):
        if t <= open_until or t + 1 >= len(bars):
            continue  # one position at a time; entries are evaluated on the NEXT bar

        hw = half_width[t]
        stop = level - direction * hw
        risk = abs(level - stop)
        # A band wider than the price it sits at cannot be a stop. Guarded rather than
        # left to produce a -105% short, which is what the scalar version did.
        if not (risk > 0.0) or risk >= level:
            continue
        target = level + direction * target_r * risk

        entry_index = None
        for j in range(t + 1, min(t + 1 + horizon_window(), len(bars))):
            b = bars[j].bar
            if fill is FillAssumption.TOUCH:
                reached = b.low <= level <= b.high
            else:
                reached = (b.low < level - TRADE_THROUGH_EPS) if direction > 0 else (
                    b.high > level + TRADE_THROUGH_EPS
                )
            if reached:
                entry_index = j
                break
        if entry_index is None:
            continue

        trail = stop
        exit_index, exit_price, reason = None, 0.0, ""
        for j in range(entry_index + 1, min(entry_index + 1 + max_hold, len(bars))):
            b = bars[j].bar
            hit_stop = (b.low <= trail) if direction > 0 else (b.high >= trail)
            hit_target = (b.high >= target) if direction > 0 else (b.low <= target)
            if hit_stop:  # stop first when a bar covers both — see the docstring
                exit_index, exit_price, reason = j, trail, "stop"
                break
            if hit_target:
                exit_index, exit_price, reason = j, target, "target"
                break
            progress = direction * (b.close - level) / risk
            if progress >= TRAIL_AFTER_R:
                window = bars[max(0, j - trail_lookback + 1) : j + 1]
                candidate = (
                    min(x.bar.low for x in window) if direction > 0
                    else max(x.bar.high for x in window)
                )
                trail = max(trail, candidate) if direction > 0 else min(trail, candidate)
        if exit_index is None:
            exit_index = min(entry_index + max_hold, len(bars) - 1)
            exit_price, reason = bars[exit_index].bar.close, "max_hold"

        trades.append(Trade(entry_index, exit_index, direction, level, exit_price, reason))
        open_until = exit_index

    return StrategyResult(tuple(trades), cost_bps, periods_per_year)


def horizon_window() -> int:
    """Bars a resting limit order stays live after the touch that placed it.

    `HORIZON`, inherited rather than chosen. An order that rests indefinitely would be
    filled by an unrelated visit to the price weeks later and attributed to the touch that
    placed it."""
    return HORIZON


@dataclass
class NullComparison:
    """One strategy, real levels against `n_sims` matched random level sets."""

    real: StrategyResult
    null_returns: list[float] = field(default_factory=list)
    null_sharpes: list[float] = field(default_factory=list)
    null_trades: list[int] = field(default_factory=list)

    def percentile(self, values: Sequence[float], observed: float) -> float:
        """Mid-rank percentile, matching `breakout_nulls.summarise_null`."""
        if not values:
            return 0.0
        below = sum(1 for v in values if v < observed)
        equal = sum(1 for v in values if v == observed)
        return 100.0 * (below + 0.5 * equal) / len(values)

    def to_dict(self, bars, periods_per_year: float) -> dict:
        real_sharpe = self.real.curve_sharpe(bars, periods_per_year)
        null_mean = statistics.fmean(self.null_sharpes) if self.null_sharpes else 0.0
        return {
            "n_trades_real": self.real.n_trades,
            "n_trades_null_mean": (
                statistics.fmean(self.null_trades) if self.null_trades else 0.0
            ),
            "real_total_return": self.real.curve_total_return(bars),
            "real_max_drawdown": self.real.max_drawdown(bars),
            "real_hit_rate": self.real.hit_rate,
            "real_mean_trade_net": (
                statistics.fmean(self.real.net_returns) if self.real.n_trades else 0.0
            ),
            "real_sharpe": real_sharpe,
            "null_sharpe_mean": null_mean,
            "null_sharpe_p05": (
                float(np.percentile(self.null_sharpes, 5)) if self.null_sharpes else 0.0
            ),
            "null_sharpe_p95": (
                float(np.percentile(self.null_sharpes, 95)) if self.null_sharpes else 0.0
            ),
            "sharpe_delta": real_sharpe - null_mean,
            "sharpe_percentile": self.percentile(self.null_sharpes, real_sharpe),
            "return_percentile": self.percentile(self.null_returns, self.real.total_return),
            "n_sims": len(self.null_sharpes),
        }


def compare_to_null(
    bars: Sequence[TimestampedBar],
    levels_by_index: dict[int, tuple[float, ...]],
    run,
    n_sims: int,
    seed: int,
    periods_per_year: float = 365.0,
) -> NullComparison:
    """Run `run(levels)` on the real levels and on `n_sims` matched random sets.

    `run` is a closure over everything except the levels, so the two arms cannot differ in
    any other respect — the pairing is enforced by the signature rather than by care."""
    comparison = NullComparison(real=run(levels_by_index))
    rng = np.random.default_rng(seed)
    for _ in range(n_sims):
        result = run(pseudo_levels(levels_by_index, rng))
        comparison.null_returns.append(result.curve_total_return(bars))
        comparison.null_sharpes.append(result.curve_sharpe(bars, periods_per_year))
        comparison.null_trades.append(result.n_trades)
    return comparison


def buy_and_hold(
    bars: Sequence[TimestampedBar], start: int, periods_per_year: float
) -> dict:
    """The passive benchmark, over the span the strategy actually trades.

    A strategy that beats its null and loses to buy-and-hold has not found anything worth
    doing — D188's lesson, where the portfolio's edge had to be measured against a matched
    basket rather than against zero."""
    window = bars[start:]
    rets = [
        math.log(b.bar.close / a.bar.close)
        for a, b in zip(window, window[1:])
        if a.bar.close > 0.0 and b.bar.close > 0.0
    ]
    sd = statistics.stdev(rets) if len(rets) > 2 else 0.0
    peak, worst = window[0].bar.close, 0.0
    for x in window:
        peak = max(peak, x.bar.close)
        worst = min(worst, x.bar.close / peak - 1.0)
    return {
        "total_return": window[-1].bar.close / window[0].bar.close - 1.0,
        "sharpe": (statistics.fmean(rets) / sd) * math.sqrt(periods_per_year) if sd > 0 else 0.0,
        "max_drawdown": worst,
        "bars": len(window),
    }
