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


# --------------------------------------------------------------------------- D197 / S6

STOP_ATR = 2.0
"""Stop distance in ATR, for the S6 field strategy (D197).

Not inherited from D196 and the difference is the point. `bounce_rr` stopped at the far
band edge, 0.5 ATR, which is 2.1% of price on this fixture — so a 40 bps round trip cost
**0.49R** and break-even sat at 36.6%. It made money before costs and lost after them. At
2 ATR the same 40 bps is about 0.12R and break-even falls to roughly 28%.

The R multiple does not transfer between designs; the stop distance is what gives it
meaning. 3R on a 0.5-ATR stop is a 6% move, 3R on a 2-ATR stop is a 25% move."""

FIELD_TARGET_R = 3.0
"""Reward multiple for the field strategy. One value, fixed by D197 — a swept target is
the easiest way to rescue a weak signal."""


def run_field_reversal(
    bars: Sequence[TimestampedBar],
    signals: Sequence,
    atr: Sequence[float],
    cost_bps: float,
    periods_per_year: float,
    threshold: float = 0.0,
    filtered: bool = True,
    stop_atr: float = STOP_ATR,
    target_r: float = FIELD_TARGET_R,
    max_hold: int = MAX_HOLD,
) -> StrategyResult:
    """S6's reversal rule, and with `filtered=False` the erasure-only control.

    Price leaves its recent range and meets inventory that has not been tested in 40+
    bars; the trade fades the break when that inventory is correctly oriented — a break UP
    into net supply is shorted, a break DOWN into net demand is bought. The two
    continuation cells are counted elsewhere and never traded (D197).

    `filtered=False` drops the `tilt` condition and fades EVERY fire. That is the
    erasure-only control — "fade every 40-bar breakout", unfiltered — and it is the
    primary comparison rather than the null, because the erasure is a deterministic
    function of price: it is present in the real arm, in the control, and identically in
    every null draw, so a null cannot detect a confound carried by it and the control can.
    The control is deliberately NOT trade-count matched; filtering is the map's whole job,
    so both counts are reported (D189's H2 confound).

    Entry is **market at the open of the bar after the signal**, so the close that fired
    is not also the fill. The entry bar's own range is then live for the stop and the
    target — unlike `bounce_rr`, whose limit filled mid-bar and could not attribute the
    rest of that bar honestly. Intrabar ordering is pessimistic throughout: when a bar
    covers both, the STOP is taken."""
    trades: list[Trade] = []
    open_until = -1

    for sig in signals:
        t = sig.index
        if t <= open_until or t + 1 >= len(bars):
            continue
        if filtered:
            if sig.virgin:
                continue  # no mass at all: the field is silent, not neutral
            if sig.direction > 0 and not (sig.tilt < -threshold):
                continue
            if sig.direction < 0 and not (sig.tilt > threshold):
                continue
        direction = -sig.direction  # fade the break

        a = atr[t]
        if not (a == a) or a <= 0.0:
            continue
        entry_index = t + 1
        entry_price = bars[entry_index].bar.open
        risk = stop_atr * a
        # A stop wider than the price it hangs from cannot be a stop. D196's scalar band
        # produced a -105% short before this guard existed.
        if not (risk > 0.0) or risk >= entry_price:
            continue
        stop = entry_price - direction * risk
        target = entry_price + direction * target_r * risk

        exit_index, exit_price, reason = None, 0.0, ""
        for j in range(entry_index, min(entry_index + max_hold, len(bars))):
            b = bars[j].bar
            hit_stop = (b.low <= stop) if direction > 0 else (b.high >= stop)
            hit_target = (b.high >= target) if direction > 0 else (b.low <= target)
            if hit_stop:  # stop first when a bar covers both
                exit_index, exit_price, reason = j, stop, "stop"
                break
            if hit_target:
                exit_index, exit_price, reason = j, target, "target"
                break
        if exit_index is None:
            exit_index = min(entry_index + max_hold, len(bars) - 1)
            exit_price, reason = bars[exit_index].bar.close, "max_hold"

        trades.append(
            Trade(entry_index, exit_index, direction, entry_price, exit_price, reason)
        )
        open_until = exit_index

    return StrategyResult(tuple(trades), cost_bps, periods_per_year)


TRAIL_ATR = 2.0
"""Chandelier multiple for D199's trailing exit policy. Deliberately the same number as
`STOP_ATR`, so the fixed and trailing policies differ in SHAPE and not in distance."""


def chandelier_level(
    bars: Sequence[TimestampedBar],
    entry_index: int,
    index: int,
    direction: int,
    atr: Sequence[float],
    multiple: float = TRAIL_ATR,
) -> float:
    """The trade's best excursion since entry, less `multiple` x ATR — unratcheted.

    Restates `strategies.breakout.ChandelierStop.stop_level` on a bare bar sequence,
    because a research sensor has no `DataView`. The two are pinned against each other by
    test rather than trusted to agree, which is the same arrangement
    `terrain.mean_true_range` has with `strategies.breakout._mean_true_range` and
    `terrain_swing._is_swing_bars` has with `_is_swing`. A restatement is only valid if it
    is provably the same number."""
    window = bars[entry_index : index + 1]
    best = (
        max(b.bar.high for b in window) if direction > 0
        else min(b.bar.low for b in window)
    )
    return best - direction * multiple * atr[index]


def run_field_trailing(
    bars: Sequence[TimestampedBar],
    signals: Sequence,
    atr: Sequence[float],
    cost_bps: float,
    periods_per_year: float,
    threshold: float = 0.0,
    filtered: bool = True,
    stop_atr: float = STOP_ATR,
    trail_atr: float = TRAIL_ATR,
    max_hold: int = MAX_HOLD,
) -> StrategyResult:
    """D199's trailing exit policy: a ratcheting chandelier and NO fixed target.

    The target is dropped on purpose. D196 measured a trail sitting behind a 3R target and
    the target resolved first on all 115 stop exits, so a trail-plus-target cell would
    re-run a known null result. The two policies are therefore compared as whole policies:
    "fixed stop plus fixed target" against "a stop that follows the trade".

    **Ratcheting is not optional** and the reason is `TrailingChannelStop`'s: the raw
    chandelier level moves both ways as ATR breathes, and a level that can loosen is not a
    stop — it would let a loss grow after having promised not to. The tightest level ever
    proposed is kept for the life of the trade, so the initial 2-ATR stop is also a floor
    the trail can only improve on.

    Entry, sizing, costs, one-position-at-a-time and the pessimistic intrabar convention
    are all `run_field_reversal`'s, unchanged."""
    trades: list[Trade] = []
    open_until = -1

    for sig in signals:
        t = sig.index
        if t <= open_until or t + 1 >= len(bars):
            continue
        if filtered:
            if sig.virgin:
                continue
            if sig.direction > 0 and not (sig.tilt < -threshold):
                continue
            if sig.direction < 0 and not (sig.tilt > threshold):
                continue
        direction = -sig.direction

        a = atr[t]
        if not (a == a) or a <= 0.0:
            continue
        entry_index = t + 1
        entry_price = bars[entry_index].bar.open
        risk = stop_atr * a
        if not (risk > 0.0) or risk >= entry_price:
            continue
        level = entry_price - direction * risk  # the initial stop is the trail's floor

        exit_index, exit_price, reason = None, 0.0, ""
        for j in range(entry_index, min(entry_index + max_hold, len(bars))):
            b = bars[j].bar
            if (b.low <= level) if direction > 0 else (b.high >= level):
                exit_index, exit_price = j, level
                reason = "stop" if j == entry_index else "trail"
                break
            aj = atr[j]
            if aj == aj and aj > 0.0:
                candidate = chandelier_level(
                    bars, entry_index, j, direction, atr, trail_atr
                )
                # ratchet: tighten only
                level = max(level, candidate) if direction > 0 else min(level, candidate)
        if exit_index is None:
            exit_index = min(entry_index + max_hold, len(bars) - 1)
            exit_price, reason = bars[exit_index].bar.close, "max_hold"

        trades.append(
            Trade(entry_index, exit_index, direction, entry_price, exit_price, reason)
        )
        open_until = exit_index

    return StrategyResult(tuple(trades), cost_bps, periods_per_year)


# --------------------------------------------------------------------------- D201

@dataclass(frozen=True)
class PositionResult:
    """An always-in book, held as a POSITION SERIES rather than a list of trades.

    ## Why this exists rather than reusing StrategyResult

    `StrategyResult.equity_curve` picks a trade up only when `open_trade is None` at the
    top of the bar, so a position entering on the exact bar another exits is **silently
    dropped**. D196-D199 never hit that because `open_until = exit_index` forced a gap
    between trades. A rule that flips from long to short holds no such gap, and every
    flipped position would vanish from the curve — a strategy that traded and a curve that
    did not, with nothing raising an error.

    A position series is also the honest representation of the thing: exposure per bar,
    with cost charged on CHANGES. `test_terrain_field.py` pins this curve against
    `StrategyResult`'s on a non-overlapping trade set, where the two must agree exactly.

    `position[t]` is the exposure held THROUGH bar t, decided on bar t-1's information.
    Interface matches `StrategyResult` so `compare_field_to_null` consumes either."""

    position: tuple[float, ...]
    """Exposure held THROUGH each bar, in [-1, +1]. Fractional since D202: sizing on the
    signal's magnitude is the thing D196 found had never been tested, because every
    strategy in that study read level prices and never scores."""
    returns: tuple[float, ...]
    """Log return of the underlying, bar over bar; `returns[0]` is 0."""
    cost_bps: float
    periods_per_year: float

    @property
    def n_trades(self) -> int:
        """Bars on which the position changed to something non-flat.

        Meaningful for a binary book and nearly every bar for a continuous one, so the
        D202 runner reports `turnover` and `sign_changes` instead. Kept unchanged so
        D201's committed summary re-renders identically."""
        return sum(
            1 for a, b in zip(self.position, self.position[1:]) if a != b and b != 0
        )

    @property
    def sign_changes(self) -> int:
        """Direction flips — the decision count for a continuously sized book. D201's
        result turned on there being only nine of these, so it is reported explicitly."""
        signs = [(1 if p > 0 else (-1 if p < 0 else 0)) for p in self.position]
        nz = [x for x in signs if x != 0]
        return sum(1 for a, b in zip(nz, nz[1:]) if a != b)

    @property
    def net_exposure(self) -> float:
        """Average signed exposure. D201's BTC book ran at +0.78, which is why most of
        its Sharpe was beta — and why a timing control was needed and missing."""
        return sum(self.position) / len(self.position) if self.position else 0.0

    @property
    def turnover(self) -> float:
        """Units of exposure traded, so a long-to-short flip counts 2 and a trim from
        0.6 to 0.5 counts 0.1. This is what cost is charged on."""
        return sum(abs(b - a) for a, b in zip(self.position, self.position[1:]))

    @property
    def share_long(self) -> float:
        held = [p for p in self.position if p != 0]
        return sum(1 for p in held if p > 0) / len(held) if held else 0.0

    def equity_curve(self, bars: Sequence[TimestampedBar] | None = None) -> list[float]:
        """Compounded equity per bar, cost charged on every unit of exposure changed."""
        charge = self.cost_bps / 10_000.0
        equity: list[float] = []
        current = 1.0
        prev: float = 0.0
        for i, pos in enumerate(self.position):
            # Cost lands on the bar the exposure CHANGES INTO, and that bar's return is
            # earned at THIS bar's position, not the previous one. Applying `prev` here
            # was the first draft and it held one bar past every exit while missing the
            # first bar of every position — caught by the pin against StrategyResult,
            # which is the entire reason that pin exists.
            current *= 1.0 - charge * abs(pos - prev)
            if i > 0:
                current *= math.exp(pos * self.returns[i])
            prev = pos
            equity.append(current)
        return equity

    def curve_sharpe(
        self, bars: Sequence[TimestampedBar], periods_per_year: float
    ) -> float:
        curve = self.equity_curve()
        rets = [math.log(b / a) for a, b in zip(curve, curve[1:]) if a > 0.0 and b > 0.0]
        if len(rets) < 3:
            return 0.0
        sd = statistics.stdev(rets)
        if sd <= 0.0:
            return 0.0
        return (statistics.fmean(rets) / sd) * math.sqrt(periods_per_year)

    def curve_total_return(self, bars: Sequence[TimestampedBar] | None = None) -> float:
        return self.equity_curve()[-1] - 1.0

    def max_drawdown(self, bars: Sequence[TimestampedBar] | None = None) -> float:
        peak, worst = 1.0, 0.0
        for x in self.equity_curve():
            peak = max(peak, x)
            if peak > 0.0:
                worst = min(worst, x / peak - 1.0)
        return worst

    @property
    def hit_rate(self) -> float:
        """Share of HELD BARS that made money — a position series has no trade-level
        outcome to count, and inventing one would not be comparable to D196-D199's."""
        held = [
            self.position[i] * self.returns[i]
            for i in range(len(self.position))
            if self.position[i] != 0
        ]
        return sum(1 for r in held if r > 0) / len(held) if held else 0.0

    def leg(self, direction: int) -> "PositionResult":
        """The same book with only one side held; the other side is flat."""
        return PositionResult(
            tuple(p if p * direction > 0 else 0.0 for p in self.position),
            self.returns,
            self.cost_bps,
            self.periods_per_year,
        )


def run_field_imbalance(
    bars: Sequence[TimestampedBar],
    imbalance: Sequence[float],
    atr: Sequence[float],
    cost_bps: float,
    periods_per_year: float,
    threshold: float = 0.0,
    use_stop: bool = False,
    stop_atr: float = STOP_ATR,
) -> PositionResult:
    """Hold long while the imbalance is above `threshold`, short while below `-threshold`.

    The signal is read on bar `t`'s close and the position is held from bar `t+1`, so the
    close that decided is never also the bar that pays — the same convention D197-D199 use
    for entry.

    **`use_stop`** adds a protective `stop_atr` x ATR(20) level fixed at the price the
    position was opened at. After a stop-out the book stays FLAT until the signal CHANGES
    STATE, because re-entering while the signal still reads the same way would just be
    stopped again next bar, and repeatedly. No target: adding one would change two things
    at once and D199 already showed what a target does to a trailing policy.

    Intrabar convention is D196's, pessimistic: the stop is checked against the bar's low
    for a long and its high for a short, so it is taken whenever the bar reached it."""
    n = len(bars)
    position: list[float] = [0.0] * n
    entry_price: float | None = None
    stopped_state: int | None = None  # the signal state we were stopped out of
    held: float = 0.0

    for t in range(n - 1):
        x = imbalance[t]
        target = 0 if not (x == x) else (1 if x > threshold else (-1 if x < -threshold else 0))

        if stopped_state is not None:
            if target != stopped_state:
                stopped_state = None  # the signal moved on; the book may trade again
            else:
                target = 0

        if use_stop and held != 0 and entry_price is not None:
            b = bars[t].bar
            a = atr[t]
            if a == a and a > 0.0:
                level = entry_price - held * stop_atr * a
                hit = (b.low <= level) if held > 0 else (b.high >= level)
                if hit:
                    stopped_state = 1 if held > 0 else -1
                    target = 0

        if target != held:
            entry_price = bars[t + 1].bar.open if target != 0 else None
            held = target
        position[t + 1] = held

    closes = [b.bar.close for b in bars]
    returns = [0.0] + [
        math.log(b / a) if a > 0.0 and b > 0.0 else 0.0
        for a, b in zip(closes, closes[1:])
    ]
    return PositionResult(tuple(position), tuple(returns), cost_bps, periods_per_year)


def run_field_position(
    bars: Sequence[TimestampedBar],
    signal: Sequence[float],
    atr: Sequence[float],
    cost_bps: float,
    periods_per_year: float,
    continuous: bool = True,
    use_stop: bool = False,
    stop_atr: float = STOP_ATR,
) -> PositionResult:
    """Hold exposure equal to the signal (D202), or its sign when `continuous=False`.

    The signal is read on bar `t`'s close and held from `t+1` — D197-D201's convention, so
    the close that decides never also pays.

    **Continuous sizing is the point.** D196 found that every strategy in that study read
    level *prices* and never *scores*, which is why S5b came back bit-identical to S5 and
    was never tested; D201 then built a field with a magnitude everywhere and thresholded
    it at zero, discarding the same information a second time. Here exposure IS the
    magnitude, so conviction and size are the same number and cost is charged on the change
    in exposure rather than on a flip.

    That also makes exposure fall as conviction falls, which is the natural risk control,
    and is why `use_stop` is a sensitivity rather than the primary. A hard stop on a scaled
    position is ill-defined, and D201 measured what one does to a book with multi-year runs:
    94.3% of bars flat after a single stop-out.

    `use_stop` closes to flat when price runs `stop_atr` x ATR against the level the
    position was last opened or increased at, and stays flat until the signal's SIGN
    changes — D201's rule, kept identical so the comparison means something."""
    n = len(bars)
    position = [0.0] * n
    ref_price: float | None = None
    stopped_sign: int | None = None
    held = 0.0

    for t in range(n - 1):
        x = signal[t]
        if not (x == x):
            x = 0.0
        target = max(-1.0, min(1.0, x)) if continuous else float(
            1 if x > 0.0 else (-1 if x < 0.0 else 0)
        )
        sign = 1 if target > 0 else (-1 if target < 0 else 0)

        if stopped_sign is not None:
            if sign != stopped_sign:
                stopped_sign = None
            else:
                target = 0.0

        if use_stop and held != 0.0 and ref_price is not None:
            b = bars[t].bar
            a = atr[t]
            if a == a and a > 0.0:
                d = 1 if held > 0 else -1
                level = ref_price - d * stop_atr * a
                if (b.low <= level) if d > 0 else (b.high >= level):
                    stopped_sign = d
                    target = 0.0

        if target != held:
            # The stop hangs from the price the exposure was last INCREASED at; trimming a
            # position does not move the level, which would otherwise let a losing trade
            # walk its own stop away from itself.
            if target != 0.0 and (held == 0.0 or abs(target) > abs(held)
                                  or (target > 0) != (held > 0)):
                ref_price = bars[t + 1].bar.open
            elif target == 0.0:
                ref_price = None
            held = target
        position[t + 1] = held

    closes = [b.bar.close for b in bars]
    returns = [0.0] + [
        math.log(b / a) if a > 0.0 and b > 0.0 else 0.0
        for a, b in zip(closes, closes[1:])
    ]
    return PositionResult(tuple(position), tuple(returns), cost_bps, periods_per_year)
