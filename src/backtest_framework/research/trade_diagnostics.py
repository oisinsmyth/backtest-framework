"""Per-trade diagnostics for a single-instrument long-flat strategy (D112).

The engine reports FILLS, not trades — deliberately, since a fill is the primitive the
simulator actually produces and "a trade" is an interpretation layered on top (D77).
This module is that interpretation, stated once so every number downstream means the
same thing.

**Episode, not fill.** A trade is a POSITION EPISODE: from the fill that takes the book
from flat to long, to the fill that returns it to flat. Rebalancing fills in between
(vol targeting recomputes the target weight, or constant-fraction sizing tracks a
changing NAV) belong to the episode that contains them — their costs are charged to
that episode rather than being counted as extra trades. Without that rule a
vol-targeted strategy would report hundreds of one-bar "trades" that are really one
position being trimmed, and every per-trade statistic would be meaningless.

**Excursions.** MFE/MAE are measured against the ENTRY FILL PRICE, over the bars the
position was actually held: the full high/low range of bars [entry_bar, exit_bar), plus
the exit fill price itself. The exit bar's post-open range is excluded — the position
was already closed at that bar's open, so counting the rest of that bar's excursion
would credit or blame the trade for a move it wasn't in.

**Everything here is arithmetic on `BacktestResult`**, not a second simulator: fills,
their costs, and the equity curve come from the one engine that ran the backtest.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Callable, Mapping, Sequence

from ..analytics.metrics import max_drawdown
from ..data.bars import TimestampedBar
from ..engine.backtest import BacktestResult

FLAT_TOLERANCE = 1e-9
"""Position sizes are crypto-precision (8 dp) floats; anything smaller than this is
flat, not a residual holding (D47's stated-epsilon policy, applied to quantities)."""


FEATURE_NAMES = ("F1", "F2", "F3", "F4", "F5", "F6")
"""At-trigger features, numbered per BREAKOUT_REVERSAL_FEATURES.md. The numbering is
open-ended by design — the terrain addon continues it at F7 — so this tuple and the
`TradeEpisode.features` map both grow without a schema migration."""

FEATURE_UNAVAILABLE = {
    "F5": "no perpetual-futures open-interest or funding plumbing in the data layer; "
          "exchange-native APIs are identified but unbuilt",
}
"""Why a feature is None everywhere, for the features that are blocked rather than
merely degenerate. Logged as an honest stub instead of being silently omitted."""


@dataclass(frozen=True)
class TradeEpisode:
    entry_timestamp: datetime
    exit_timestamp: datetime | None
    """None for an episode still open at the end of the run (the final window can end
    long). Open episodes are reported separately and excluded from closed-trade
    statistics — including them would silently mix realized and unrealized P&L."""
    entry_index: int
    exit_index: int | None
    bars_held: int
    entry_price: float
    exit_price: float | None
    gross_pnl: float
    """Cash P&L before trade costs: −Σ(signed quantity × fill price) over the episode,
    plus the mark-to-market of any still-open position at the final bar's close."""
    costs: float
    """Every trade cost charged inside the episode, entry and exit and any rebalance."""
    rebalance_costs: float
    """The subset of `costs` charged on INTERIOR fills — neither the fill that opened
    the position nor the one that closed it. This is the price of sizing policy rather
    than of the signal, and separating the two is the only way to answer "is vol
    targeting paying for itself?" (D112)."""
    traded_notional: float
    """Σ|quantity × price| over the episode's fills — turnover, before costs."""
    n_fills: int
    mfe: float
    """Max favourable excursion as a fraction of the entry price (>= 0 by
    construction only when the trade ever moved up; a trade that never traded above
    its entry has a negative MFE, which is information, not a bug)."""
    mae: float
    """Max adverse excursion as a fraction of the entry price."""

    features: Mapping[str, float | None] = field(default_factory=dict)
    """At-trigger feature values, keyed by F-number (BREAKOUT_REVERSAL_FEATURES.md).

    Open by construction: new features are new keys, never new columns, so the
    terrain addon's F7/F8/F9 can be logged onto the same episodes without a schema
    migration. `None` means UNAVAILABLE at this trigger — a blocked data source, or a
    window that does not reach back far enough — and is never imputed. Absent keys
    mean the feature was not computed for this run at all, which is a different
    statement from `None`.

    Populated once at construction; the dataclass is frozen but this mapping is not
    deep-frozen, so treat it as read-only by convention."""

    @property
    def net_pnl(self) -> float:
        return self.gross_pnl - self.costs

    @property
    def is_open(self) -> bool:
        return self.exit_index is None

@dataclass(frozen=True)
class DiagnosticsSummary:
    n_closed_trades: int
    n_open_at_end: int
    win_rate: float
    mean_mfe: float
    mean_mae: float
    median_mfe: float
    median_mae: float
    mean_bars_held: float
    median_bars_held: float
    p90_bars_held: float
    mean_bars_to_stop_out_losers: float
    median_bars_to_stop_out_losers: float
    whipsaw_rate: float
    """Closed trades exited within `whipsaw_bars` bars of entry, as a fraction of all
    closed trades."""
    exposure: float
    """Fraction of OOS bars with a non-flat position."""
    total_costs: float
    rebalance_cost_share: float
    """Interior (sizing-driven) costs as a fraction of total costs — 0 means every
    penny of cost bought a signal-driven entry or exit."""
    traded_notional: float
    annual_turnover: float
    """Traded notional per unit of average equity per year."""
    gross_pnl: float
    net_pnl: float
    cost_share_of_gross: float
    """Round-trip costs as a fraction of |gross P&L|. NaN when gross P&L is zero."""
    upside_capture: float
    downside_participation: float
    downside_avoided: float
    drawdown_avoided: float

    def to_metrics(self) -> dict[str, float]:
        """Flat dict for the TrialRegistry (JSON-serialisable scalars only)."""
        return {name: float(getattr(self, name)) for name in self.__dataclass_fields__}


def extract_episodes(
    result: BacktestResult,
    instrument_id: str,
    bars: Sequence[TimestampedBar],
    features_at: Callable[[int], Mapping[str, float | None]] | None = None,
) -> list[TradeEpisode]:
    """`bars` must be the EXECUTION series the backtest ran on, in the same order —
    excursions are read off it by timestamp.

    `features_at` is called with the TRIGGER index (the bar before the entry fill, see
    the at-trigger features section) and returns that episode's feature map. Omitted
    means no features are logged, which leaves `TradeEpisode.features` empty — a
    different statement from a feature present but None."""
    index_by_timestamp = {tb.timestamp: i for i, tb in enumerate(bars)}
    fills = [f for f in result.fills if f[1] == instrument_id]

    episodes: list[TradeEpisode] = []
    position = 0.0
    open_state: dict | None = None

    for timestamp, _instrument, quantity, price, cost in fills:
        bar_index = index_by_timestamp[timestamp]
        was_flat = abs(position) < FLAT_TOLERANCE
        if was_flat:
            open_state = {
                "entry_timestamp": timestamp,
                "entry_index": bar_index,
                "entry_price": price,
                "cash": 0.0,
                "fills": [],
            }
        assert open_state is not None  # a fill on a flat book always opens an episode
        open_state["cash"] -= quantity * price
        open_state["fills"].append((quantity, price, cost))
        position += quantity

        if abs(position) < FLAT_TOLERANCE:
            position = 0.0
            mfe, mae = _excursions(bars, open_state["entry_index"], bar_index, open_state["entry_price"], price)
            episode_fills = open_state["fills"]
            episodes.append(
                TradeEpisode(
                    entry_timestamp=open_state["entry_timestamp"],
                    exit_timestamp=timestamp,
                    entry_index=open_state["entry_index"],
                    exit_index=bar_index,
                    bars_held=bar_index - open_state["entry_index"],
                    entry_price=open_state["entry_price"],
                    exit_price=price,
                    gross_pnl=open_state["cash"],
                    costs=sum(c for _q, _p, c in episode_fills),
                    rebalance_costs=sum(c for _q, _p, c in episode_fills[1:-1]),
                    traded_notional=sum(abs(q * p) for q, p, _c in episode_fills),
                    n_fills=len(episode_fills),
                    mfe=mfe,
                    mae=mae,
                    features=dict(features_at(open_state["entry_index"] - 1)) if features_at else {},
                )
            )
            open_state = None

    if open_state is not None:
        # Still long at the end of the run: mark to the final close so the episode's
        # P&L is comparable, but flag it open so it can be excluded from closed-trade
        # statistics rather than quietly averaged in with them.
        final_index = len(bars) - 1
        final_close = bars[final_index].bar.close
        mfe, mae = _excursions(bars, open_state["entry_index"], final_index + 1, open_state["entry_price"], final_close)
        episode_fills = open_state["fills"]
        episodes.append(
            TradeEpisode(
                entry_timestamp=open_state["entry_timestamp"],
                exit_timestamp=None,
                entry_index=open_state["entry_index"],
                exit_index=None,
                bars_held=final_index - open_state["entry_index"],
                entry_price=open_state["entry_price"],
                exit_price=None,
                gross_pnl=open_state["cash"] + position * final_close,
                costs=sum(c for _q, _p, c in episode_fills),
                # Still open: only the opening fill is known not to be the closing one.
                rebalance_costs=sum(c for _q, _p, c in episode_fills[1:]),
                traded_notional=sum(abs(q * p) for q, p, _c in episode_fills),
                n_fills=len(episode_fills),
                mfe=mfe,
                mae=mae,
                features=dict(features_at(open_state["entry_index"] - 1)) if features_at else {},
            )
        )
    return episodes


def _excursions(
    bars: Sequence[TimestampedBar], entry_index: int, exit_index: int, entry_price: float, exit_price: float
) -> tuple[float, float]:
    """High/low range over bars [entry_index, exit_index), plus the exit price — see
    the module docstring on why the exit bar's post-open range is excluded."""
    highs = [bars[j].bar.high for j in range(entry_index, exit_index)] + [exit_price]
    lows = [bars[j].bar.low for j in range(entry_index, exit_index)] + [exit_price]
    return max(highs) / entry_price - 1.0, min(lows) / entry_price - 1.0


def summarise(
    episodes: Sequence[TradeEpisode],
    equity_curve: Sequence[tuple[datetime, float]],
    instrument_bars: Sequence[TimestampedBar],
    n_oos_bars: int,
    whipsaw_bars: int = 3,
    periods_per_year: float = 365.0,
) -> DiagnosticsSummary:
    """`equity_curve` and `instrument_bars` must cover the SAME timestamps (the OOS
    span), so capture ratios compare like with like."""
    closed = [e for e in episodes if not e.is_open]
    n_open = len(episodes) - len(closed)
    losers = [e for e in closed if e.net_pnl < 0]
    held = [e.bars_held for e in closed]

    strategy_returns = [b / a - 1.0 for (_, a), (_, b) in zip(equity_curve, equity_curve[1:])]
    instrument_returns = [
        b.bar.close / a.bar.close - 1.0 for a, b in zip(instrument_bars, instrument_bars[1:])
    ]
    if len(strategy_returns) != len(instrument_returns):
        raise ValueError(
            f"equity curve has {len(strategy_returns)} returns but the instrument series has "
            f"{len(instrument_returns)} — capture ratios would compare different samples"
        )

    up_instrument = sum(r for r in instrument_returns if r > 0)
    down_instrument = sum(r for r in instrument_returns if r < 0)
    up_strategy = sum(s for s, r in zip(strategy_returns, instrument_returns) if r > 0)
    down_strategy = sum(s for s, r in zip(strategy_returns, instrument_returns) if r < 0)
    upside_capture = up_strategy / up_instrument if up_instrument != 0 else float("nan")
    downside_participation = down_strategy / down_instrument if down_instrument != 0 else float("nan")

    instrument_equity = [(tb.timestamp, tb.bar.close) for tb in instrument_bars]
    instrument_mdd = max_drawdown(instrument_equity)
    strategy_mdd = max_drawdown(list(equity_curve))

    gross = sum(e.gross_pnl for e in episodes)
    costs = sum(e.costs for e in episodes)
    rebalance_costs = sum(e.rebalance_costs for e in episodes)
    traded_notional = sum(e.traded_notional for e in episodes)
    bars_in_market = sum(e.bars_held for e in episodes)
    mean_equity = statistics.fmean([nav for _, nav in equity_curve]) if equity_curve else float("nan")
    years = n_oos_bars / periods_per_year if n_oos_bars else float("nan")

    return DiagnosticsSummary(
        n_closed_trades=len(closed),
        n_open_at_end=n_open,
        win_rate=_fraction(sum(1 for e in closed if e.net_pnl > 0), len(closed)),
        mean_mfe=_mean([e.mfe for e in closed]),
        mean_mae=_mean([e.mae for e in closed]),
        median_mfe=_median([e.mfe for e in closed]),
        median_mae=_median([e.mae for e in closed]),
        mean_bars_held=_mean(held),
        median_bars_held=_median(held),
        p90_bars_held=_percentile(held, 0.90),
        mean_bars_to_stop_out_losers=_mean([e.bars_held for e in losers]),
        median_bars_to_stop_out_losers=_median([e.bars_held for e in losers]),
        whipsaw_rate=_fraction(sum(1 for e in closed if e.bars_held <= whipsaw_bars), len(closed)),
        exposure=_fraction(bars_in_market, n_oos_bars),
        total_costs=costs,
        rebalance_cost_share=rebalance_costs / costs if costs else 0.0,
        traded_notional=traded_notional,
        annual_turnover=traded_notional / mean_equity / years if mean_equity and years else float("nan"),
        gross_pnl=gross,
        net_pnl=gross - costs,
        cost_share_of_gross=costs / abs(gross) if gross != 0 else float("nan"),
        upside_capture=upside_capture,
        downside_participation=downside_participation,
        downside_avoided=1.0 - downside_participation,
        drawdown_avoided=1.0 - strategy_mdd / instrument_mdd if instrument_mdd > 0 else float("nan"),
    )


def _fraction(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else float("nan")


def _mean(values: Sequence[float]) -> float:
    return statistics.fmean(values) if values else float("nan")


def _median(values: Sequence[float]) -> float:
    return statistics.median(values) if values else float("nan")


def _percentile(values: Sequence[float], q: float) -> float:
    """Nearest-rank percentile — stated explicitly because the alternatives
    (interpolated, exclusive) give different answers on the small trade counts a
    breakout strategy produces, and a silently-chosen convention is how two tables in
    the same report end up disagreeing."""
    if not values:
        return float("nan")
    ordered = sorted(values)
    rank = max(1, math.ceil(q * len(ordered)))
    return float(ordered[rank - 1])


# ------------------------------------------------------------------ at-trigger features
#
# These are LOGGED, never acted on. BREAKOUT_REVERSAL_FEATURES.md is explicit that
# logging carries no multiplicity cost and that promotion to a live filter is a
# separate, later exercise with its own TrialRegistry accounting. Nothing in this
# section can change a fill, a weight, or a cost.
#
# THE TRIGGER BAR IS NOT THE ENTRY BAR. Fills are next-open (D103): the decision is
# taken on bar t's close and filled at bar t+1's open, so an episode whose
# `entry_index` is t+1 was triggered on bar t. Every feature below is computed at
# t = entry_index - 1, from bars at or before t, which is exactly the information the
# strategy had when it decided. Reading them off the entry bar instead would be a
# one-bar look-ahead in the diagnostics.


def _true_range(bars: Sequence[TimestampedBar], index: int) -> float:
    bar, prev_close = bars[index].bar, bars[index - 1].bar.close
    return max(bar.high - bar.low, abs(bar.high - prev_close), abs(bar.low - prev_close))


def _atr(bars: Sequence[TimestampedBar], end: int, window: int) -> float | None:
    """Mean true range over the `window` bars ENDING AT end-1 (D44). Plain mean, not
    Wilder's — the same estimator VolatilityContractionFilter uses, so F1 and the
    volatility-contraction filter speak the same units."""
    start = end - window
    if start < 1:
        return None
    return sum(_true_range(bars, j) for j in range(start, end)) / window


def last_friday(year: int, month: int) -> date:
    """Last Friday of the month — the Deribit monthly options expiry date."""
    first_of_next = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    last_day = first_of_next - timedelta(days=1)
    return last_day - timedelta(days=(last_day.weekday() - 4) % 7)


def hours_to_next_expiry(timestamp: datetime) -> float:
    """Hours from `timestamp` to the next Deribit monthly options expiry (last Friday
    of the month, 08:00 UTC). Pure calendar arithmetic — zero data dependencies, which
    is why F6's expiry half is computable now while its funding half is not.

    Timestamps in this project's fixtures are naive UTC; treated as such here."""
    for year, month in ((timestamp.year, timestamp.month),
                        (timestamp.year + (timestamp.month == 12), timestamp.month % 12 + 1)):
        expiry = datetime.combine(last_friday(year, month), datetime.min.time()) + timedelta(hours=8)
        if expiry >= timestamp:
            return (expiry - timestamp).total_seconds() / 3600.0
    raise AssertionError("next expiry is always within two months")


def breadth_series(
    bars_by_symbol: Mapping[str, Sequence[TimestampedBar]],
    *,
    high_window: int = 20,
    sma_window: int = 50,
) -> dict[datetime, float]:
    """F4's cross-sectional input: per timestamp, the fraction of the universe whose
    close is above its own `high_window`-bar high OR its own `sma_window`-bar SMA.

    Look-ahead discipline matches the strategy's: both windows END AT THE PREVIOUS BAR
    and only the current close is compared against them, so the value at timestamp t
    uses nothing after t. Symbols without enough history at t are excluded from the
    denominator rather than counted as False — "not yet measurable" is not "not
    participating".

    Low power is expected and was predicted: with a two-instrument universe the
    fraction can only take the values 0, 0.5 and 1."""
    participating: dict[datetime, list[bool]] = {}
    warm_up = max(high_window, sma_window)
    for bars in bars_by_symbol.values():
        for i in range(warm_up, len(bars)):
            close = bars[i].bar.close
            above_high = close > max(bars[j].bar.high for j in range(i - high_window, i))
            above_sma = close > statistics.fmean(bars[j].bar.close for j in range(i - sma_window, i))
            participating.setdefault(bars[i].timestamp, []).append(above_high or above_sma)
    return {ts: sum(flags) / len(flags) for ts, flags in participating.items() if flags}


def trigger_features(
    bars: Sequence[TimestampedBar],
    trigger_index: int,
    *,
    breadth: Mapping[datetime, float] | None = None,
    volumes: Sequence[float | None] | None = None,
) -> dict[str, float | None]:
    """The at-trigger feature vector for a decision taken on `bars[trigger_index]`.

    Every key in FEATURE_NAMES is always present. `None` means unavailable at this
    trigger — either blocked at the data layer (F2, F5; see FEATURE_UNAVAILABLE) or
    short of warm-up — and is never imputed."""
    features: dict[str, float | None] = {name: None for name in FEATURE_NAMES}
    if trigger_index < 0 or trigger_index >= len(bars):
        return features
    bar = bars[trigger_index].bar

    # F1 — extension at trigger: (close − SMA(50)) / ATR(20), windows ending at t−1.
    atr = _atr(bars, trigger_index, 20)
    if atr is not None and atr > 0.0 and trigger_index >= 50:
        sma50 = statistics.fmean(bars[j].bar.close for j in range(trigger_index - 50, trigger_index))
        features["F1"] = (bar.close - sma50) / atr

    # F2 — trigger volume ratio: trigger-bar volume over the mean of the preceding
    # `window` bars. The baseline ENDS AT t-1 for the same reason the filter's does — a
    # big trigger bar must not inflate the average it is being measured against.
    # Unblocked by D168; the D111 gap that made this None is closed.
    if volumes is not None and trigger_index >= 20:
        window = [volumes[j] for j in range(trigger_index - 20, trigger_index)]
        trigger_volume = volumes[trigger_index]
        if trigger_volume is not None and not any(v is None for v in window):
            mean_volume = sum(v for v in window if v is not None) / 20
            if mean_volume > 0.0:
                features["F2"] = trigger_volume / mean_volume


    # F3 — close location value: where in the bar's own range the close landed.
    span = bar.high - bar.low
    if span > 0.0:
        features["F3"] = (bar.close - bar.low) / span

    # F4 — cross-sectional breadth at the trigger timestamp.
    if breadth is not None:
        features["F4"] = breadth.get(bars[trigger_index].timestamp)

    # F5 — leverage decomposition: blocked, no derivatives plumbing.

    # F6 — known-flow proximity. Only the options-expiry half is computable: on daily
    # bars with a 00:00 UTC boundary every close sits exactly on a perp funding stamp
    # (00/08/16 UTC), so the funding half is identically zero and carries no
    # information at this frequency. Logging the expiry distance alone, and saying so.
    features["F6"] = hours_to_next_expiry(bars[trigger_index].timestamp)

    return features
