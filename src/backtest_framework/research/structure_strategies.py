"""The frozen wrapper, and the trades every ablation arm produces (D204, WP4/WP5).

## The wrapper is a constant, not a variable

Stop at the swing extreme that defined the structure, target at a fixed R multiple, a
channel trail once 1R in profit, and a hard hold cap. **Identical in every arm.** D203 is
the reason and it is the most transferable thing the terrain programme produced:

> Every refinement that changed the **wrapper** — entry timing, exits, stops, thresholds —
> improved the strategy against its own predecessor and left the null comparison exactly
> where the first fair test put it. The one refinement that changed the **statistic**
> (D202) fixed every defect named in its diagnosis and produced the **worst** result.

So there is no exit sweep here. The only thing that varies across arms is which filters
must hold at entry, which is the question the programme exists to answer.

## Two amendments to the pre-registration live here (D207)

**Entry is a market order at the close of the entry bar**, not a limit at the level, so
D9's two `FillAssumption` conventions do not apply and are replaced by a cost-multiplier
sweep in WP5. The reason is the ablation: the C1-only arm has **no level to rest a limit
at**, so a limit design would make the base arm structurally different from every arm above
it and the difference between arms would stop being the filters.

What that costs is stated rather than buried: **D196's adverse selection is not paid in
this study.** That study priced D9's effect at 0.138–0.195 Sharpe on a bounce strategy. A
market-at-close entry does not have that problem; it has the spread instead, which the 40
bps tier prices. Anyone implementing the course's actual limit-at-the-level method should
subtract something in D196's range.

**The primary target is 5R**, the course's own number, with `terrain_strategies.TARGET_R`'s
(2.0, 3.0) as sensitivity. The claim under test is arithmetic at 5R; running the verdict at
2R would answer a question nobody asked.

## Intra-bar ordering is pessimistic, and that is not negotiable

When a bar's range covers both the stop and the target, the **stop** is taken. A bar's OHLC
does not say which came first, and resolving that ambiguity in the strategy's favour is how
a backtest manufactures an edge it will not have (D42). Gap-through fills go at the bar's
open, not the stop price (D10) — a bug fix, never a configurable option.

## Excursions are direction-signed AND in R units, unlike `trade_diagnostics._excursions`

Two deliberate deviations, both recorded here rather than left as a surprise for whoever
next reads the two implementations side by side.

**Signed.** That function is long-only: `max(high)/entry - 1`. Half the trades here are
short, where the favourable excursion is the **low**. Feeding `feature_analysis` unsigned
excursions from a two-sided book would rank every short by how far price rose against it.

**In R, not in price fraction.** `analyse_feature` ranks on MFE, and an excursion expressed
as a fraction of the entry price is a **scale-dependent** quantity on a fixture running from
$3,000 to $100,000 across eight years and two assets. Ranking on it makes any feature
correlated with volatility look predictive: a wider stop means a wider leg means bigger
moves means a bigger price-fraction excursion, mechanically and with no information in it.

That is D187's lesson — a scale-dependent quantity applied across instruments and eras that
do not share the scale — and the first WP4 run walked straight into it: `stop_atr` came back
a CANDIDATE with rank correlations of +0.56 and +0.63 inside depth quintiles, which is the
artifact and not a finding. Dividing by the trade's own risk removes it and makes a
comparison between features an actual comparison.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from typing import Iterable, Sequence

from ..data.bars import TimestampedBar
from ..simulator.fills import StopSide, stop_fill_price
from .structure import RSI_WINDOW, Gap, ratio_price, retracement, rsi
from .structure_nulls import first_gap_in_leg
from .structure_setups import (
    ATR_WINDOW_15M,
    GOLDEN_RATIO,
    Setup,
    stop_distance,
    stop_price,
)
from .terrain import rolling_mean_true_range
from .terrain_strategies import MAX_HOLD, TRAIL_AFTER_R, TRAIL_LOOKBACK
from .trade_diagnostics import TradeEpisode

COURSE_TARGET_R = 5.0
"""The course settles here after quoting 4R-8R, and its whole edge claim is the arithmetic
at this number. Primary by D207; `terrain_strategies.TARGET_R` is the sensitivity."""


@dataclass(frozen=True)
class Wrapper:
    """Every exit parameter, in one frozen object shared by every arm.

    Frozen and passed by value so an arm cannot quietly hold a different one. That is the
    same reason `terrain_field_nulls.compare_field_to_null` takes the shared parts in its
    signature: pairing enforced by structure rather than by discipline."""

    target_r: float = COURSE_TARGET_R
    trail_after_r: float = TRAIL_AFTER_R
    trail_lookback: int = TRAIL_LOOKBACK
    max_hold: int = MAX_HOLD


@dataclass(frozen=True)
class ArmTrade:
    """One trade, before it is turned into a `TradeEpisode`."""

    setup_index: int
    entry_index: int
    exit_index: int
    direction: int
    entry_price: float
    exit_price: float
    stop_price: float
    risk: float
    reason: str

    @property
    def gross_return(self) -> float:
        return self.direction * (self.exit_price / self.entry_price - 1.0)

    @property
    def r_multiple(self) -> float:
        """Realised return in units of the risk taken. The course's own currency."""
        return self.direction * (self.exit_price - self.entry_price) / self.risk


def run_arm(
    bars: Sequence[TimestampedBar],
    setups: Sequence[Setup],
    required: Iterable[str] = (),
    wrapper: Wrapper | None = None,
    allow_overlap: bool = False,
) -> list[ArmTrade]:
    """Trade one filter subset through the frozen wrapper.

    One position at a time by default: a setup whose entry falls inside an open trade is
    skipped, not stacked. Overlapping positions would make the equity path depend on a
    sizing policy this study never states, and `StrategyResult.equity_curve`'s known blind
    spot — a position entering on the exact bar another exits is silently dropped — is
    avoided by requiring a strict gap rather than by hoping it does not arise.

    `allow_overlap=True` evaluates every setup independently and is for **annotation, not
    for a book**. WP4's feature analysis needs one outcome per setup, and the one-at-a-time
    rule throws away most of them — 3,875 setups became 275 trades in the first run, which
    is a fine book and a poor sample. An overlapping population has no meaningful equity
    curve and none is computed from it.

    The signal is read on bar `t`'s close and the position fills at bar `t+1`'s close, so
    the bar that decides never also pays — D197-D201's convention, kept identical so the
    numbers are comparable with the terrain programme's."""
    wrapper = wrapper or Wrapper()
    required = tuple(required)
    trades: list[ArmTrade] = []
    open_until = -1

    for position, setup in enumerate(setups):
        signal = setup.first_entry(required)
        if signal is None or signal + 1 >= len(bars):
            continue
        if not allow_overlap and signal <= open_until:
            continue
        entry_index = signal + 1
        entry_price = bars[entry_index].bar.close
        direction = setup.direction
        stop = stop_price(setup)
        risk = stop_distance(setup, entry_price)
        # A stop at or through the entry price is not a stop. Guarded rather than left to
        # produce an infinite R multiple, which is what an unguarded division would do.
        if not (risk > 0.0) or risk >= entry_price:
            continue
        if (direction > 0 and stop >= entry_price) or (direction < 0 and stop <= entry_price):
            continue
        target = entry_price + direction * wrapper.target_r * risk

        trail = stop
        exit_index: int | None = None
        exit_price: float = 0.0
        reason = ""
        last = min(entry_index + wrapper.max_hold, len(bars) - 1)
        for j in range(entry_index + 1, last + 1):
            bar = bars[j].bar
            side = StopSide.SELL_STOP if direction > 0 else StopSide.BUY_STOP
            fill = stop_fill_price(side, trail, bar)
            hit_target = (bar.high >= target) if direction > 0 else (bar.low <= target)
            if fill is not None:  # stop first when a bar covers both (D42)
                exit_index, exit_price, reason = j, fill, "stop"
                break
            if hit_target:
                exit_index, exit_price, reason = j, target, "target"
                break
            progress = direction * (bar.close - entry_price) / risk
            if progress >= wrapper.trail_after_r:
                window = bars[max(0, j - wrapper.trail_lookback + 1) : j + 1]
                candidate = (
                    min(x.bar.low for x in window) if direction > 0
                    else max(x.bar.high for x in window)
                )
                trail = max(trail, candidate) if direction > 0 else min(trail, candidate)
        if exit_index is None:
            exit_index, exit_price, reason = last, bars[last].bar.close, "max_hold"

        trades.append(
            ArmTrade(
                setup_index=position,
                entry_index=entry_index,
                exit_index=exit_index,
                direction=direction,
                entry_price=entry_price,
                exit_price=exit_price,
                stop_price=stop,
                risk=risk,
                reason=reason,
            )
        )
        open_until = exit_index
    return trades


def _excursions(
    bars: Sequence[TimestampedBar], trade: ArmTrade
) -> tuple[float, float]:
    """Direction-signed MFE and MAE, in units of the trade's own risk.

    Long: favourable is the high. Short: favourable is the low. Signed so a two-sided book
    is rankable by `feature_analysis.analyse_feature`, which was written for a long-flat
    one; divided by risk so the ranking is not dominated by volatility. See the module
    docstring — the price-fraction form made `stop_atr` look like a candidate feature when
    it is a scaling artifact."""
    highs = [bars[j].bar.high for j in range(trade.entry_index, trade.exit_index)]
    lows = [bars[j].bar.low for j in range(trade.entry_index, trade.exit_index)]
    highs.append(trade.exit_price)
    lows.append(trade.exit_price)
    best = max(highs) if trade.direction > 0 else min(lows)
    worst = min(lows) if trade.direction > 0 else max(highs)
    return (
        trade.direction * (best - trade.entry_price) / trade.risk,
        trade.direction * (worst - trade.entry_price) / trade.risk,
    )


def trigger_features(
    bars: Sequence[TimestampedBar],
    setup: Setup,
    trade: ArmTrade,
    atr: Sequence[float],
    strength: Sequence[float],
    gaps: Sequence[Gap],
) -> dict[str, float | None]:
    """The continuous readings of every component, taken at the bar that triggered entry.

    **Continuous, never boolean.** WP4a's whole power comes from ranking trades by a
    gradient rather than splitting them by a threshold, and a boolean feature has one split
    where a continuous one has four quintile boundaries. `None` means unavailable — a setup
    with no gap in its leg — and is never imputed, per the convention `terrain.density`
    established and `TradeEpisode.features` documents.

    `fib_depth` is the load-bearing one after WP3: the retracement ladder came back a
    monotone staircase in depth, so depth is the variable every other component has to beat
    rather than a control to report alongside them."""
    signal = trade.entry_index - 1
    close = bars[signal].bar.close
    band = atr[signal]
    depth = retracement(setup.leg, close)
    golden = ratio_price(setup.leg, GOLDEN_RATIO)

    midpoint, width = first_gap_in_leg(setup, gaps)
    gap_distance: float | None = None
    if midpoint is not None and math.isfinite(band) and band > 0.0:
        gap_distance = abs(close - midpoint) / band

    level_distance: float | None = None
    if math.isfinite(band) and band > 0.0 and setup.leg.span != 0.0:
        level_distance = abs(close - golden) / band

    return {
        "fib_depth": depth,
        "atr_to_golden": level_distance,
        "gap_distance_atr": gap_distance,
        "rsi": strength[signal] if math.isfinite(strength[signal]) else None,
        "stop_atr": trade.risk / band if math.isfinite(band) and band > 0.0 else None,
        "bars_waited": float(trade.entry_index - 1 - setup.choch_index),
        "direction": float(trade.direction),
    }


def to_episodes(
    bars: Sequence[TimestampedBar],
    setups: Sequence[Setup],
    trades: Sequence[ArmTrade],
    cost_bps: float,
    atr: Sequence[float] | None = None,
    strength: Sequence[float] | None = None,
    gaps: Sequence[Gap] | None = None,
) -> list[TradeEpisode]:
    """Turn arm trades into the episode objects `feature_analysis` already knows how to read.

    Reusing `TradeEpisode` rather than inventing a record is deliberate: it carries the
    promotion criteria with it. `analyse_feature`'s three gates — |rho| >= 0.2, sign
    agreement across halves, quintile means stepping monotonically — are thresholds this
    project already committed to, and restating them here would be re-choosing them.

    P&L is stated per unit of notional (one unit bought or sold at the entry price), so
    `net_pnl`'s sign is the trade's sign and nothing depends on a position-sizing policy
    this study never states."""
    if atr is None:
        atr = rolling_mean_true_range(bars, ATR_WINDOW_15M)
    if strength is None:
        strength = rsi(bars, RSI_WINDOW)
    if gaps is None:
        gaps = []
    charge = cost_bps / 10_000.0

    episodes: list[TradeEpisode] = []
    for trade in trades:
        setup = setups[trade.setup_index]
        mfe, mae = _excursions(bars, trade)
        notional = trade.entry_price + trade.exit_price
        episodes.append(
            TradeEpisode(
                entry_timestamp=bars[trade.entry_index].timestamp,
                exit_timestamp=bars[trade.exit_index].timestamp,
                entry_index=trade.entry_index,
                exit_index=trade.exit_index,
                bars_held=trade.exit_index - trade.entry_index,
                entry_price=trade.entry_price,
                exit_price=trade.exit_price,
                gross_pnl=trade.direction * (trade.exit_price - trade.entry_price),
                costs=charge * notional,
                rebalance_costs=0.0,
                traded_notional=notional,
                n_fills=2,
                mfe=mfe,
                mae=mae,
                features=trigger_features(bars, setup, trade, atr, strength, gaps),
            )
        )
    return episodes


def r_multiples(trades: Sequence[ArmTrade], cost_bps: float) -> list[float]:
    """Net R per trade — the course's own currency, with the toll deducted.

    Cost is charged as a round trip on notional and converted into R by the trade's own
    risk, which is what makes WP2's friction arithmetic and WP5's book the same statement
    rather than two numbers that happen to point the same way."""
    charge = cost_bps / 10_000.0
    out: list[float] = []
    for trade in trades:
        friction = charge * (trade.entry_price + trade.exit_price) / trade.risk
        out.append(trade.r_multiple - friction)
    return out


def expectancy(trades: Sequence[ArmTrade], cost_bps: float) -> dict[str, float]:
    """Hit rate, mean R, median R, and the share of trades that are untradeable.

    Reported together because each alone misleads.

    A 60% hit rate at 0.2R and a 20% hit rate at 5R are different businesses, and the
    course's entire pitch is the second one — so hit rate never appears without mean R.

    **Mean R alone is unusable here, and the first WP4 run proved it: it came back −104.**
    Not a bug. A stop placed at the swing extreme, entered at a shallow retracement, can sit
    a few basis points from the entry price, and a 40 bps round trip against a 4 bps stop
    really is 10R. What that number describes is a position size nobody can take, so
    `share_untradeable` — the fraction of trades whose round trip costs at least their whole
    risk — is reported beside it, with the median and the mean over the takeable trades."""
    values = r_multiples(trades, cost_bps)
    if not values:
        return {
            "n": 0, "hit_rate": 0.0, "mean_r": 0.0, "median_r": 0.0, "total_r": 0.0,
            "share_untradeable": 0.0, "mean_r_tradeable": 0.0,
        }
    charge = cost_bps / 10_000.0
    frictions = [charge * (t.entry_price + t.exit_price) / t.risk for t in trades]
    untradeable = [f >= 1.0 for f in frictions]
    wins = [v for v in values if v > 0.0]
    losses = [v for v in values if v <= 0.0]
    takeable = [v for v, bad in zip(values, untradeable) if not bad]
    return {
        "n": len(values),
        "hit_rate": len(wins) / len(values),
        "mean_r": sum(values) / len(values),
        "median_r": statistics.median(values),
        "total_r": sum(values),
        "mean_win_r": sum(wins) / len(wins) if wins else 0.0,
        "mean_loss_r": sum(losses) / len(losses) if losses else 0.0,
        "share_untradeable": sum(untradeable) / len(untradeable),
        "mean_r_tradeable": (
            sum(takeable) / len(takeable) if takeable else float("nan")
        ),
    }
