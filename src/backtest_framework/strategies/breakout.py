"""Long-flat Donchian breakout trend-following strategy (D109).

**THESIS LABEL (D38/D82/D117): this is a DIRECTIONAL, beta-loaded strategy and is NOT
part of this project's market-neutral thesis.** It is long or flat, never short, on a
single high-beta instrument; its returns are a filtered version of that instrument's
own returns, and the honest benchmark for it is buy-and-hold, not the risk-free rate
(D37's benchmark-frame rule, applied the other way round from the pairs book). It is
carried here as a second, deliberately contrasting research strategy — the framework's
claim is that a strategy is a swappable brick, and a long-only trend follower on crypto
is about as far from a market-neutral ETF pairs book as a strategy can get while using
the same engine. Read every number it produces as "did trend following clear crypto
fees", never as evidence about the market-neutral programme.

Flat is the default state. Entry on a confirmed upward breakout of the trailing
`n_entry`-bar high; exit on a much faster trailing `n_exit`-bar low. No shorting —
the only two states are flat and long.

Look-ahead story (D32/D56 + D44), the part that has to be exactly right:

- Both extrema are computed over bars **strictly before** the current one:
  entry compares `close(t)` against `max(high)` over t−n_entry … t−1, exit compares
  `close(t)` against `min(low)` over t−n_exit … t−1. Today's own high/low can never
  put today's close inside its own trigger level, so a bar cannot trigger on itself.
- Everything the strategy reads comes from its `DataView`, which physically holds no
  bar beyond the current index — perturbing any future bar cannot change today's
  targets, and that is asserted as a property test, not assumed.
- Trailing estimates (ATR, the SMA gate, realized vol) use windows ending at t−1,
  per D44's "vol estimates use data up to the previous bar only" rule. Only the
  breakout comparison itself reads `close(t)`, which is a completed bar at decision
  time — the fill happens at the NEXT bar's open (`fill_timing="next_open"`, D103),
  so the strategy never trades at the price that produced its signal.

Hysteresis is the point, not a side effect: the entry level (an n_entry-bar high) sits
far above the exit level (an n_exit-bar low), so the two conditions are mutually
exclusive on any single bar whenever n_exit <= n_entry (the exit window is nested in
the entry window, so max(high over the entry window) >= min(low over the exit window)
— a close cannot be strictly above the first and strictly below the second). That
inequality is enforced in __post_init__ and asserted in the tests; it is what makes
"never chatters" a structural property rather than a hope.

Filters and sizing are SEPARATE, TOGGLEABLE COMPONENTS, never hardcoded into the entry
logic: `filters` is a tuple of EntryFilter bricks consulted only on the bar an entry
would otherwise fire, and `weight_source` is a WeightSource brick that decides how big
the position is. Baseline = no filters + whatever sizing is configured; each filter
increment is the same strategy with one more brick in the tuple. Same Lego-brick shape
as CostStack (D1).

VOLUME CONFIRMATION: built, and the D111 blocker that stopped it is closed (D168).
Volume reaches strategy code by riding inside `DataView` as an aligned, optionally
present series constructed sliced exactly as the bars are — not as a field on `Bar`
(which is built at ~90 sites and which D60 already refused to widen for `timestamp`),
and not through the strategy's constructor (which would hand strategy code full-sample
data outside the D32 guard). `VolumeConfirmationFilter` reads it through
`require_volume`, so a run wired without volume fails loudly instead of quietly
rejecting every entry.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable, Mapping, Protocol, Sequence

from ..config.errors import ConfigError
from ..config.factory import FactoryRegistry
from ..engine.dataview import DataView, MissingVolumeError
from ..pipeline.sizing import TargetWeight

EntryCondition = Callable[[int], bool]
"""Absolute bar index -> "did the raw breakout condition hold on that bar?". Handed to
filters so a debounce filter can look at the condition's own history without
re-deriving it (and without any filter being able to reach past the DataView)."""


class Direction(IntEnum):
    """Which way a breakout brick trades. The value IS the sign, so channel logic can
    be written once and parameterized rather than duplicated per side.

    Phase 1 only ever constructs LONG. SHORT exists because the breakdown addon
    specifies that the channel logic must be sign-parameterizable *before* the short
    side is built, so that adding it is a configuration change rather than a rewrite
    of the strategy brick."""

    LONG = 1
    SHORT = -1


class PositionState(IntEnum):
    """What the book currently holds. The value is the sign of the exposure, so
    `state * weight` is the signed target weight with no branching.

    This replaces the boolean `_in_position` flag that Phase 1 shipped with. A bool
    cannot express {long, flat, short}, and the breakdown addon requires the state
    machine to admit all three before the short book is written — retrofitting a
    third state onto a bool later means touching every read of it."""

    SHORT = -1
    FLAT = 0
    LONG = 1


def _channel_extreme(view: DataView, start: int, end: int, sign: int) -> float:
    """The channel boundary over bars [start, end) in the `sign` direction: the
    highest high looking up, the lowest low looking down. One function for both
    sides — the sign selects the field and the extremum together."""
    if sign > 0:
        return max(view[j].high for j in range(start, end))
    return min(view[j].low for j in range(start, end))


def _beyond(price: float, level: float, sign: int) -> bool:
    """Has `price` breached `level` in the `sign` direction? Strict, so a touch is
    not a breach — the same convention Phase 1's `>` / `<` comparisons used."""
    return sign * (price - level) > 0.0


class EntryFilter(Protocol):
    """A veto on an entry that would otherwise fire. Never consulted on exits — a
    filter can keep you out of a trade, never trap you in one."""

    @property
    def name(self) -> str:
        """Read-only by declaration: every concrete filter is a frozen dataclass, and
        a settable protocol attribute would mark them all non-conforming — the same
        variance trap audit F20 found on Instrument.quote_currency."""
        ...

    @property
    def requires_volume(self) -> bool:
        """Whether this filter cannot function without a volume series (D168).

        Declared rather than discovered, so the strategy can check for the data ONCE
        and fail loudly, instead of every bar quietly rejecting entries because the
        volume it wanted was never wired through."""
        ...

    def warm_up_bars(self, n_entry: int, n_exit: int) -> int:
        """Minimum `current_index` at which this filter can be evaluated. Takes the
        strategy's windows because a debounce filter's requirement is stated relative
        to them (it needs the raw condition evaluable m bars back), while an ATR or
        SMA filter's is absolute."""
        ...

    def accepts(self, view: DataView, entry_condition: EntryCondition) -> bool: ...

    def config(self) -> dict[str, Any]:
        """Declarative description (D52) — the dict the TrialRegistry logs is the dict
        `build_entry_filter` rebuilds this brick from (D102: hash what you run)."""
        ...


class WeightSource(Protocol):
    """Decides the target weight of an open position, as a fraction of the strategy's
    allocated capital (D27's unit)."""

    @property
    def name(self) -> str:
        """Read-only by declaration — see EntryFilter.name."""
        ...

    @property
    def cap(self) -> float:
        """The largest weight this source can ever return, as a fraction of allocated
        capital. Declared rather than inferred, because the short book's per-trade
        position cap is non-optional (D169) and a cap that has to be discovered by
        sampling the output is not a cap."""
        ...

    @property
    def rebalance(self) -> str:
        """"at_entry" — the weight is computed once when the trade opens and held for
        its life; "every_bar" — recomputed each bar the position is open. The
        distinction is load-bearing at crypto fee levels: recomputing a vol target
        daily churns the position every day, which is a real cost, not a modelling
        artifact."""
        ...

    def warm_up_bars(self) -> int: ...

    def weight(self, view: DataView) -> float | None:
        """None means "cannot size on this bar" (degenerate estimate) — the strategy
        then stays flat rather than guessing."""
        ...

    def config(self) -> dict[str, Any]: ...


# --------------------------------------------------------------------------- sizing


@dataclass(frozen=True)
class FixedWeight:
    """Fixed-fractional sizing: the same fraction of capital on every trade.

    This is the stopgap the breakout spec names for the case where inverse-vol sizing
    isn't available — kept because it's also the honest control for measuring what
    vol targeting actually buys, and because a constant weight of 1.0 is the only
    sizing that generates no rebalancing churn at all (desired quantity = NAV/price
    tracks the position exactly when fully invested)."""

    fraction: float = 1.0
    name: str = field(default="fixed", init=False)
    rebalance: str = field(default="every_bar", init=False)

    @property
    def cap(self) -> float:
        return self.fraction

    def __post_init__(self) -> None:
        if not 0.0 < self.fraction <= 1.0:
            raise ValueError(f"fraction must be in (0, 1], got {self.fraction}")

    def warm_up_bars(self) -> int:
        return 0

    def weight(self, view: DataView) -> float | None:
        return self.fraction

    def config(self) -> dict[str, Any]:
        return {"type": "fixed_weight", "fraction": self.fraction}


@dataclass(frozen=True)
class InverseVolatilityWeight:
    """Inverse-volatility sizing: weight = target vol / trailing realized vol, capped.

    Realized vol is the sample stdev of `vol_window` log returns ENDING AT THE
    PREVIOUS BAR (D44), annualised by √periods_per_year. The cap is what "capped at
    1.0× capital" means: this strategy never levers up, it only sizes down when the
    instrument is volatile relative to the target.

    Placement note (D110): the framework's portfolio layer has no vol-targeting
    sizer — `pipeline.sizing.Sizer` converts a weight to a quantity and nothing more,
    by design (D55). Under D27 the *weight itself* is the strategy's output, so vol
    targeting belongs in the signal → target-weight stage, and this brick is where it
    lives. It is genuine inverse-vol sizing, not the fixed-fractional stopgap."""

    target_annual_vol: float = 0.40
    vol_window: int = 20
    periods_per_year: float = 365.0
    max_weight: float = 1.0
    rebalance: str = "at_entry"
    name: str = field(default="inverse_vol", init=False)

    @property
    def cap(self) -> float:
        return self.max_weight

    def __post_init__(self) -> None:
        if self.vol_window < 2:
            raise ValueError(f"vol_window must be at least 2, got {self.vol_window}")
        if self.target_annual_vol <= 0:
            raise ValueError(f"target_annual_vol must be positive, got {self.target_annual_vol}")
        if self.rebalance not in ("at_entry", "every_bar"):
            raise ValueError(f"rebalance must be 'at_entry' or 'every_bar', got {self.rebalance!r}")

    def warm_up_bars(self) -> int:
        # vol_window returns ending at bar i-1 need closes at i-1-vol_window .. i-1.
        return self.vol_window + 1

    def weight(self, view: DataView) -> float | None:
        i = view.current_index
        closes = [view[j].close for j in range(i - 1 - self.vol_window, i)]
        returns = [math.log(b / a) for a, b in zip(closes, closes[1:])]
        sd = statistics.stdev(returns)
        if sd == 0.0:
            return None  # degenerate window — stand aside rather than size infinitely
        realized_annual = sd * math.sqrt(self.periods_per_year)
        return min(self.target_annual_vol / realized_annual, self.max_weight)

    def config(self) -> dict[str, Any]:
        return {
            "type": "inverse_vol_weight",
            "target_annual_vol": self.target_annual_vol,
            "vol_window": self.vol_window,
            "periods_per_year": self.periods_per_year,
            "max_weight": self.max_weight,
            "rebalance": self.rebalance,
        }


# -------------------------------------------------------------------------- filters


@dataclass(frozen=True)
class ConsecutiveCloseFilter:
    """Close-confirmation debounce: the raw breakout condition must hold on `m`
    consecutive closes before an entry is accepted. m = 1 is the identity filter (the
    baseline), kept explicit so "no debounce" and "1-close debounce" are the same
    configuration rather than two code paths."""

    m: int = 2
    name: str = field(default="debounce", init=False)
    requires_volume: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.m < 1:
            raise ValueError(f"m must be at least 1, got {self.m}")

    def warm_up_bars(self, n_entry: int, n_exit: int) -> int:
        # The raw condition must be evaluable at i-(m-1), i.e. i-(m-1) >= n_entry.
        return n_entry + self.m - 1

    def accepts(self, view: DataView, entry_condition: EntryCondition) -> bool:
        i = view.current_index
        return all(entry_condition(i - k) for k in range(self.m))

    def config(self) -> dict[str, Any]:
        return {"type": "consecutive_close", "m": self.m}


@dataclass(frozen=True)
class VolatilityContractionFilter:
    """Volatility-contraction precondition: accept a trigger only when
    ATR(short) / ATR(long) < threshold — i.e. the market has been coiling rather than
    already expanding when the breakout fires.

    ATR here is the arithmetic mean of true range (Wilder's smoothing is a different
    estimator; the plain mean is the one this study states and tests). Both windows
    end at bar i−1 (D44), so the trigger bar's own range does not decide whether the
    trigger bar is admissible."""

    threshold: float = 1.0
    short_window: int = 20
    long_window: int = 100
    name: str = field(default="vol_contraction", init=False)
    requires_volume: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.short_window < 1 or self.long_window < 1:
            raise ValueError("ATR windows must be positive")
        if self.short_window >= self.long_window:
            raise ValueError(
                f"short_window ({self.short_window}) must be below long_window "
                f"({self.long_window}) — the ratio would be meaningless otherwise"
            )

    def warm_up_bars(self, n_entry: int, n_exit: int) -> int:
        # True range at bar j needs close(j-1); the long window ends at i-1 and starts
        # at i-long_window, so the earliest bar touched is i-long_window-1 >= 0.
        return self.long_window + 1

    def accepts(self, view: DataView, entry_condition: EntryCondition) -> bool:
        i = view.current_index
        atr_short = _mean_true_range(view, i - self.short_window, i)
        atr_long = _mean_true_range(view, i - self.long_window, i)
        if atr_long == 0.0:
            return False  # degenerate — a flat long window admits nothing
        return atr_short / atr_long < self.threshold

    def config(self) -> dict[str, Any]:
        return {
            "type": "volatility_contraction",
            "threshold": self.threshold,
            "short_window": self.short_window,
            "long_window": self.long_window,
        }


@dataclass(frozen=True)
class TrendGateFilter:
    """Higher-timeframe gate: take entries only when close(t) sits on the trading side
    of the trailing `sma_window`-bar simple moving average of closes. The SMA window
    ends at t−1 (D44); the comparison uses today's close, which is the same
    completed-bar quantity the breakout condition itself uses.

    Direction-aware by construction: LONG admits entries above the average, SHORT
    admits them below it. The breakdown addon specifies the short book activates on
    the inverse of the long book's gate — that is this brick with `direction=SHORT`,
    not a second class."""

    sma_window: int = 200
    direction: Direction = Direction.LONG
    name: str = field(default="trend_gate", init=False)
    requires_volume: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.sma_window < 2:
            raise ValueError(f"sma_window must be at least 2, got {self.sma_window}")

    def warm_up_bars(self, n_entry: int, n_exit: int) -> int:
        return self.sma_window

    def accepts(self, view: DataView, entry_condition: EntryCondition) -> bool:
        i = view.current_index
        sma = statistics.fmean(view[j].close for j in range(i - self.sma_window, i))
        return _beyond(view[i].close, sma, self.direction)

    def config(self) -> dict[str, Any]:
        config: dict[str, Any] = {"type": "trend_gate", "sma_window": self.sma_window}
        if self.direction is not Direction.LONG:
            config["direction"] = self.direction.name.lower()
        return config


@dataclass(frozen=True)
class OpenPosition:
    """What an exit rule may know about the trade it is being asked to close.

    `entry_reference` is the TRIGGER BAR'S CLOSE, not the fill price. The strategy
    decides on a close and the engine fills at the next open (D103), so the strategy
    genuinely does not know what it paid — and inventing a fill price here would be a
    false affordance. Every exit rule is therefore a signal-level rule measured against
    the information the strategy actually had."""

    state: PositionState
    entry_index: int
    entry_reference: float
    stop_level: float

    @property
    def direction(self) -> int:
        return int(self.state)


class ExitRule(Protocol):
    """A condition that closes an open position, consulted alongside the trailing
    channel exit. Any rule firing closes the trade; the channel exit remains the
    safety net underneath them all.

    Exit rules are the mirror of EntryFilter: a filter can only keep you OUT of a
    trade, an exit rule can only get you OUT of one. Neither can do the other's job."""

    @property
    def name(self) -> str: ...

    def warm_up_bars(self, n_entry: int, n_exit: int) -> int: ...

    def exits(self, view: DataView, position: OpenPosition) -> bool: ...

    def config(self) -> dict[str, Any]: ...


@dataclass(frozen=True)
class ChannelStopExit:
    """Hard per-trade stop at the entry channel's OPPOSITE boundary, fixed at entry.

    For a short entering below an n_entry-bar low, the stop sits at the n_entry-bar
    HIGH measured at the trigger bar — the top of the channel whose floor just broke.
    Mechanical, unambiguous, and exactly what BREAKDOWN_SHORT_STRATEGY.md specifies.
    Symmetric for a long, though the long book does not require it.

    **This is a CLOSE-BASED stop, and that is a real limitation, not a detail (D169).**
    The engine has no intrabar stop execution: `simulator/fills.stop_fill_price` exists
    with correct D10 gap semantics and is explicitly a Step-2 demonstration vehicle
    wired only to `config/fill_model.py`, never to `run_backtest`. So this rule can only
    observe a CLOSE beyond the stop and exit at the NEXT OPEN. An overnight gap goes
    straight through it and fills wherever the next open lands.

    The consequence must be stated rather than assumed: the squeeze tail is **not**
    truncated by construction, which is the premise the brief's "short expectancy is
    only calculable with the tail truncated" rests on. The study therefore MEASURES the
    gap — stop level versus realised fill on every stop exit — so the shortfall is a
    reported number instead of an unstated assumption."""

    name: str = field(default="channel_stop", init=False)

    def warm_up_bars(self, n_entry: int, n_exit: int) -> int:
        return n_entry

    def exits(self, view: DataView, position: OpenPosition) -> bool:
        if view.current_index <= position.entry_index:
            return False  # never on the decision bar itself
        return _beyond(view[view.current_index].close, position.stop_level, -position.direction)

    def config(self) -> dict[str, Any]:
        return {"type": "channel_stop"}


@dataclass(frozen=True)
class TimeStopExit:
    """Exit a position that has not moved in its favour within `n_bars` of entry.

    Rationale from the brief: a short not in profit within roughly 3-5 bars is carrying
    squeeze risk for no compensation, and stagnation is information. Measured against
    the trigger bar's close, for the same reason `OpenPosition` carries a reference
    rather than a fill price."""

    n_bars: int = 5
    name: str = field(default="time_stop", init=False)

    def __post_init__(self) -> None:
        if self.n_bars < 1:
            raise ValueError(f"n_bars must be at least 1, got {self.n_bars}")

    def warm_up_bars(self, n_entry: int, n_exit: int) -> int:
        return 0

    def exits(self, view: DataView, position: OpenPosition) -> bool:
        i = view.current_index
        if i - position.entry_index < self.n_bars:
            return False
        # "In profit" means the price has moved IN the trade's direction since entry.
        return not _beyond(view[i].close, position.entry_reference, position.direction)

    def config(self) -> dict[str, Any]:
        return {"type": "time_stop", "n_bars": self.n_bars}


@dataclass(frozen=True)
class VolumeConfirmationFilter:
    """Volume confirmation: accept a trigger only when the trigger bar's volume exceeds
    `multiple` times the mean volume over the preceding `window` bars.

    This is the filter the original brief specified and D111 recorded as BLOCKED — the
    `Bar` schema carried no volume, and neither workaround was acceptable (a schema
    change to the framework's most load-bearing type, or smuggling a full-sample series
    into the strategy's constructor outside the D32 guard). D168 closed the gap the
    third way: volume rides inside `DataView`, constructed sliced exactly as bars are,
    so this filter reads it under the same structural look-ahead guarantee as prices.

    The averaging window ENDS AT t−1 (D44), so the trigger bar's own volume is compared
    against a baseline it is not part of — otherwise a large trigger bar would inflate
    the very average it has to beat, and the filter would understate its own threshold.

    **Stated gap policy: any missing volume rejects the entry.** A `None` on the trigger
    bar or anywhere inside the averaging window means the entry is refused. You cannot
    confirm on data you do not have, and the conservative direction for a confirmation
    filter is to decline. This is a policy choice, it is documented, and it is tested —
    the alternative (skip the gaps and average what is left) silently changes the window
    length per trigger, which is worse.

    `requires_volume` is True: a run that reaches this filter without a volume series is
    a configuration error, and `require_volume` raises rather than rejecting everything
    and returning a plausible, wrong result."""

    multiple: float = 1.5
    window: int = 20
    name: str = field(default="volume_confirmation", init=False)
    requires_volume: bool = field(default=True, init=False)

    def __post_init__(self) -> None:
        if self.window < 1:
            raise ValueError(f"window must be at least 1, got {self.window}")
        if self.multiple <= 0:
            raise ValueError(f"multiple must be positive, got {self.multiple}")

    def warm_up_bars(self, n_entry: int, n_exit: int) -> int:
        # The window ends at i-1 and starts at i-window, so the earliest bar touched is
        # i-window; i >= window is enough.
        return self.window

    def accepts(self, view: DataView, entry_condition: EntryCondition) -> bool:
        i = view.current_index
        trigger = view.require_volume(i)
        if trigger is None:
            return False
        baseline = [view.require_volume(j) for j in range(i - self.window, i)]
        if any(v is None for v in baseline):
            return False
        mean_volume = sum(v for v in baseline if v is not None) / self.window
        if mean_volume <= 0.0:
            return False  # a dead window confirms nothing
        return trigger > self.multiple * mean_volume

    def config(self) -> dict[str, Any]:
        return {
            "type": "volume_confirmation",
            "multiple": self.multiple,
            "window": self.window,
        }


def _mean_true_range(view: DataView, start: int, end: int) -> float:
    """Mean true range over bars [start, end). Each bar's TR needs the previous
    close, so `start` must be at least 1."""
    total = 0.0
    for j in range(start, end):
        bar, prev_close = view[j], view[j - 1].close
        total += max(bar.high - bar.low, abs(bar.high - prev_close), abs(bar.low - prev_close))
    return total / (end - start)


# ------------------------------------------------------------------------- strategy


@dataclass
class BreakoutStrategy:
    """Donchian breakout, one direction at a time. Holds per-run mutable state
    (`_state`, `_held_weight`) — construct a fresh instance per backtest run, the same
    contract ZScorePairsStrategy carries (D68).

    `direction` selects the side. Phase 1 constructs only LONG, and a LONG instance
    behaves exactly as the original long-flat brick did — the sign parameterization is
    forward compatibility for the breakdown addon, not a behaviour change."""

    strategy_id: str
    instrument_id: str
    n_entry: int = 40
    n_exit: int = 10
    direction: Direction = Direction.LONG
    weight_source: WeightSource = field(default_factory=lambda: FixedWeight(1.0))
    filters: tuple[EntryFilter, ...] = ()
    exit_rules: tuple[ExitRule, ...] = ()

    _state: PositionState = field(default=PositionState.FLAT, init=False, repr=False)
    _held_weight: float = field(default=0.0, init=False, repr=False)
    _checked_volume: bool = field(default=False, init=False, repr=False)
    _entry_index: int = field(default=-1, init=False, repr=False)
    _entry_reference: float = field(default=0.0, init=False, repr=False)
    _stop_level: float = field(default=0.0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.n_entry < 1 or self.n_exit < 1:
            raise ValueError(f"n_entry and n_exit must be positive, got {self.n_entry}/{self.n_exit}")
        if self.n_exit > self.n_entry:
            raise ValueError(
                f"n_exit ({self.n_exit}) must not exceed n_entry ({self.n_entry}) — the exit "
                "window must nest inside the entry window for the hysteresis band to be "
                "non-empty; otherwise entry and exit can fire on the same bar (D109)"
            )
        names = [f.name for f in self.filters]
        if len(names) != len(set(names)):
            raise ValueError(f"duplicate filter names {names} — each filter may appear at most once")
        exit_names = [r.name for r in self.exit_rules]
        if len(exit_names) != len(set(exit_names)):
            raise ValueError(
                f"duplicate exit rule names {exit_names} — each rule may appear at most once"
            )

        # TAIL DISCIPLINE IS NON-OPTIONAL ON THE SHORT SIDE (D169).
        #
        # BREAKDOWN_SHORT_STRATEGY.md: "hard per-trade stop above the entry channel
        # high; per-trade position cap. Short expectancy is only calculable with the
        # squeeze tail truncated by construction. No configuration may disable these."
        #
        # A short's loss is unbounded in a way a long's is not: the long book's worst
        # case is the instrument going to zero, the short book's worst case has no
        # ceiling at all. So this is enforced at construction and there is deliberately
        # no flag to turn it off — a config that omits the stop does not run.
        if self.direction is Direction.SHORT:
            if not any(isinstance(r, ChannelStopExit) for r in self.exit_rules):
                raise ValueError(
                    "a SHORT breakout strategy must carry a ChannelStopExit — the per-trade "
                    "stop is non-optional tail discipline, not a configurable filter "
                    "(BREAKDOWN_SHORT_STRATEGY.md, D169). Refusing to construct an unprotected "
                    "short book"
                )
            if self.weight_source.cap > 1.0:
                raise ValueError(
                    f"a SHORT breakout strategy may not be levered: weight source "
                    f"{self.weight_source.name!r} caps at {self.weight_source.cap}, above the "
                    "1.0 per-trade position cap (D169)"
                )

    # ---- signal primitives, both strictly over COMPLETED bars before the current one

    def entry_level(self, view: DataView, index: int) -> float:
        """The entry channel boundary over index−n_entry … index−1, taken IN the trade
        direction: max(high) for a long, min(low) for a short. Today's own bar is
        excluded, so a bar can never trigger on itself."""
        return _channel_extreme(view, index - self.n_entry, index, self.direction)

    def exit_level(self, view: DataView, index: int) -> float:
        """The exit channel boundary over index−n_exit … index−1, taken AGAINST the
        trade direction: min(low) for a long, max(high) for a short."""
        return _channel_extreme(view, index - self.n_exit, index, -self.direction)

    def entry_condition(self, view: DataView, index: int) -> bool:
        return _beyond(view[index].close, self.entry_level(view, index), self.direction)

    def exit_condition(self, view: DataView, index: int) -> bool:
        return _beyond(view[index].close, self.exit_level(view, index), -self.direction)

    def warm_up_bars(self) -> int:
        """Minimum `current_index` at which every component can be evaluated."""
        required = max(self.n_entry, self.n_exit)
        required = max(required, self.weight_source.warm_up_bars())
        for f in self.filters:
            required = max(required, f.warm_up_bars(self.n_entry, self.n_exit))
        for r in self.exit_rules:
            required = max(required, r.warm_up_bars(self.n_entry, self.n_exit))
        return required

    # ---- the D27 interface

    def generate_targets(self, views: Mapping[str, DataView]) -> list[TargetWeight]:
        view = views[self.instrument_id]
        i = view.current_index
        self._check_volume_available(view)

        if i < self.warm_up_bars():
            # Warm-up self-guard (the same shape ZScorePairsStrategy uses): stand
            # aside until every component has the history it needs.
            return self._targets(0.0)

        if self._state is not PositionState.FLAT:
            position = OpenPosition(
                state=self._state,
                entry_index=self._entry_index,
                entry_reference=self._entry_reference,
                stop_level=self._stop_level,
            )
            # The trailing channel remains the safety net UNDERNEATH every added rule:
            # any one of them firing closes the trade, so a rule can only ever make the
            # book flatter, never keep it in a position the channel wanted out of.
            if self.exit_condition(view, i) or any(r.exits(view, position) for r in self.exit_rules):
                self._state, self._held_weight = PositionState.FLAT, 0.0
                self._entry_index = -1
            elif self.weight_source.rebalance == "every_bar":
                w = self.weight_source.weight(view)
                if w is not None:
                    self._held_weight = w
        elif self.entry_condition(view, i) and all(
            f.accepts(view, lambda j: self.entry_condition(view, j)) for f in self.filters
        ):
            w = self.weight_source.weight(view)
            if w is not None and w > 0.0:
                self._state = PositionState(int(self.direction))
                self._held_weight = w
                self._entry_index = i
                self._entry_reference = view[i].close
                # The stop is the entry channel's opposite boundary, fixed at entry:
                # max(high) over the entry window for a short, min(low) for a long.
                self._stop_level = _channel_extreme(view, i - self.n_entry, i, -self.direction)

        # The state IS the sign, so a short book emits a negative target weight with
        # no branch here. `_held_weight` stays a magnitude in every state.
        return self._targets(self._state * self._held_weight)

    def _check_volume_available(self, view: DataView) -> None:
        """Fail loudly, once, if any filter needs volume and the view has none (D168).

        **Why the first call and not construction:** the strategy is built before it
        ever sees a view, so construction-time validation would mean handing the
        strategy its data — precisely the look-ahead hole this design exists to avoid.
        The first call is bar 0, not bar 3,000, which satisfies the spirit of D35's
        "fail at factory time" as closely as the architecture allows. The trade-off is
        deliberate, not an oversight."""
        if self._checked_volume:
            return
        self._checked_volume = True
        needed = [f.name for f in self.filters if f.requires_volume]
        if needed and not view.has_volume:
            raise MissingVolumeError(
                f"filter(s) {needed} require volume but instrument {self.instrument_id!r} was "
                "given a DataView without a volume series — pass volumes_by_instrument to "
                "run_backtest. Refusing to run rather than silently rejecting every entry (D168)"
            )

    def _targets(self, weight: float) -> list[TargetWeight]:
        return [
            TargetWeight(
                strategy_id=self.strategy_id, instrument_id=self.instrument_id, weight=weight
            )
        ]

    def config(self) -> dict[str, Any]:
        """Declarative description of the whole strategy (D52/D102) — what the
        registry hashes, and what `build_breakout_strategy` rebuilds."""
        config: dict[str, Any] = {
            "type": "breakout_long_flat",
            "n_entry": self.n_entry,
            "n_exit": self.n_exit,
            "weight_source": self.weight_source.config(),
            "filters": [f.config() for f in self.filters],
        }
        # Emitted only when non-empty, so every long-flat config produced before exit
        # rules existed still hashes identically (the same compatibility rule D166
        # applies to `direction`).
        if self.exit_rules:
            config["exit_rules"] = [r.config() for r in self.exit_rules]
        # `direction` is emitted only when it is not the LONG default, so every
        # config a long-flat run produces hashes exactly as it did before the sign
        # parameterization existed and the v1 trial registry stays comparable
        # (D166). Absence still determines the run: the default is pinned here.
        if self.direction is not Direction.LONG:
            config["direction"] = self.direction.name.lower()
        return config


# ------------------------------------------------------------------------ factories


def _required_int(config: dict, key: str, kind: str) -> int:
    if key not in config:
        raise ConfigError(f"{kind} config is missing required key {key!r}")
    value = config[key]
    if not isinstance(value, int) or isinstance(value, bool):
        raise ConfigError(f"{kind} config key {key!r} must be an int, got {type(value).__name__}")
    return value


def _optional_number(config: dict, key: str, default: float, kind: str) -> float:
    if key not in config:
        return default
    value = config[key]
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ConfigError(f"{kind} config key {key!r} must be numeric, got {type(value).__name__}")
    return float(value)


def _direction(config: dict, kind: str) -> Direction:
    """Parse the optional `direction` key. Absent means LONG — the default is pinned
    here and in `config()`, so an omitted key is unambiguous rather than merely
    unspecified (D166)."""
    if "direction" not in config:
        return Direction.LONG
    value = config["direction"]
    if not isinstance(value, str) or value.upper() not in Direction.__members__:
        raise ConfigError(
            f"{kind} config key 'direction' must be one of "
            f"{sorted(n.lower() for n in Direction.__members__)}, got {value!r}"
        )
    return Direction[value.upper()]


ENTRY_FILTER_REGISTRY = FactoryRegistry(kind="entry_filter")
ENTRY_FILTER_REGISTRY.register(
    "consecutive_close", lambda c: ConsecutiveCloseFilter(m=_required_int(c, "m", "consecutive_close"))
)
ENTRY_FILTER_REGISTRY.register(
    "volatility_contraction",
    lambda c: VolatilityContractionFilter(
        threshold=_optional_number(c, "threshold", 1.0, "volatility_contraction"),
        short_window=int(_optional_number(c, "short_window", 20, "volatility_contraction")),
        long_window=int(_optional_number(c, "long_window", 100, "volatility_contraction")),
    ),
)
ENTRY_FILTER_REGISTRY.register(
    "volume_confirmation",
    lambda c: VolumeConfirmationFilter(
        multiple=_optional_number(c, "multiple", 1.5, "volume_confirmation"),
        window=int(_optional_number(c, "window", 20, "volume_confirmation")),
    ),
)
ENTRY_FILTER_REGISTRY.register(
    "trend_gate",
    lambda c: TrendGateFilter(
        sma_window=int(_optional_number(c, "sma_window", 200, "trend_gate")),
        direction=_direction(c, "trend_gate"),
    ),
)

EXIT_RULE_REGISTRY = FactoryRegistry(kind="exit_rule")
EXIT_RULE_REGISTRY.register("channel_stop", lambda c: ChannelStopExit())
EXIT_RULE_REGISTRY.register(
    "time_stop", lambda c: TimeStopExit(n_bars=_required_int(c, "n_bars", "time_stop"))
)

WEIGHT_SOURCE_REGISTRY = FactoryRegistry(kind="weight_source")
WEIGHT_SOURCE_REGISTRY.register(
    "fixed_weight", lambda c: FixedWeight(fraction=_optional_number(c, "fraction", 1.0, "fixed_weight"))
)
WEIGHT_SOURCE_REGISTRY.register(
    "inverse_vol_weight",
    lambda c: InverseVolatilityWeight(
        target_annual_vol=_optional_number(c, "target_annual_vol", 0.40, "inverse_vol_weight"),
        vol_window=int(_optional_number(c, "vol_window", 20, "inverse_vol_weight")),
        periods_per_year=_optional_number(c, "periods_per_year", 365.0, "inverse_vol_weight"),
        max_weight=_optional_number(c, "max_weight", 1.0, "inverse_vol_weight"),
        rebalance=c.get("rebalance", "at_entry"),
    ),
)


def build_entry_filter(config: dict[str, Any]) -> EntryFilter:
    return ENTRY_FILTER_REGISTRY.build(config)


def build_weight_source(config: dict[str, Any]) -> WeightSource:
    return WEIGHT_SOURCE_REGISTRY.build(config)


def build_exit_rule(config: dict[str, Any]) -> ExitRule:
    return EXIT_RULE_REGISTRY.build(config)


def build_breakout_strategy(
    config: dict[str, Any], strategy_id: str, instrument_id: str
) -> BreakoutStrategy:
    """Rebuild a strategy from the exact dict `BreakoutStrategy.config()` produces —
    the strategy-level half of D102's "hash what you run"."""
    if config.get("type") != "breakout_long_flat":
        raise ConfigError(
            f"breakout strategy config key 'type' must be 'breakout_long_flat', got {config.get('type')!r}"
        )
    filters: Sequence[dict] = config.get("filters", [])
    return BreakoutStrategy(
        strategy_id=strategy_id,
        instrument_id=instrument_id,
        n_entry=_required_int(config, "n_entry", "breakout_long_flat"),
        n_exit=_required_int(config, "n_exit", "breakout_long_flat"),
        direction=_direction(config, "breakout_long_flat"),
        weight_source=build_weight_source(config["weight_source"]),
        filters=tuple(build_entry_filter(f) for f in filters),
        exit_rules=tuple(build_exit_rule(r) for r in config.get("exit_rules", [])),
    )
