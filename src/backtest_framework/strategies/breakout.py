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

NOT IMPLEMENTED — volume confirmation (D111). A "trigger bar volume > 1.5× 20-day
average volume" filter cannot be written against the current interfaces: `Bar` carries
open/high/low/close and nothing else, `TimestampedBar` adds only a timestamp, and
`DataView` hands strategies `Bar` objects. Volume exists in the fixtures and snapshots
but stops at the data layer (csv_fixture is explicit that "TimestampedBar carries no
volume field (D59/D60), and inventing one here would be a false affordance (D48)").
Smuggling a volume series into the strategy's constructor would hand it full-sample
data outside the DataView guard — precisely the look-ahead hole D32 exists to close —
so the filter is absent rather than faked. See docs/decisions/D111-*.md.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Protocol, Sequence

from ..config.errors import ConfigError
from ..config.factory import FactoryRegistry
from ..engine.dataview import DataView
from ..pipeline.sizing import TargetWeight

EntryCondition = Callable[[int], bool]
"""Absolute bar index -> "did the raw breakout condition hold on that bar?". Handed to
filters so a debounce filter can look at the condition's own history without
re-deriving it (and without any filter being able to reach past the DataView)."""


class EntryFilter(Protocol):
    """A veto on an entry that would otherwise fire. Never consulted on exits — a
    filter can keep you out of a trade, never trap you in one."""

    @property
    def name(self) -> str:
        """Read-only by declaration: every concrete filter is a frozen dataclass, and
        a settable protocol attribute would mark them all non-conforming — the same
        variance trap audit F20 found on Instrument.quote_currency."""
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
    """Higher-timeframe gate: take entries only when close(t) is above the trailing
    `sma_window`-bar simple moving average of closes. The SMA window ends at t−1
    (D44); the comparison uses today's close, which is the same completed-bar quantity
    the breakout condition itself uses."""

    sma_window: int = 200
    name: str = field(default="trend_gate", init=False)

    def __post_init__(self) -> None:
        if self.sma_window < 2:
            raise ValueError(f"sma_window must be at least 2, got {self.sma_window}")

    def warm_up_bars(self, n_entry: int, n_exit: int) -> int:
        return self.sma_window

    def accepts(self, view: DataView, entry_condition: EntryCondition) -> bool:
        i = view.current_index
        sma = statistics.fmean(view[j].close for j in range(i - self.sma_window, i))
        return view[i].close > sma

    def config(self) -> dict[str, Any]:
        return {"type": "trend_gate", "sma_window": self.sma_window}


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
    """Long-flat Donchian breakout. Holds per-run mutable state (`_in_position`,
    `_held_weight`) — construct a fresh instance per backtest run, the same contract
    ZScorePairsStrategy carries (D68)."""

    strategy_id: str
    instrument_id: str
    n_entry: int = 40
    n_exit: int = 10
    weight_source: WeightSource = field(default_factory=lambda: FixedWeight(1.0))
    filters: tuple[EntryFilter, ...] = ()

    _in_position: bool = field(default=False, init=False, repr=False)
    _held_weight: float = field(default=0.0, init=False, repr=False)

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

    # ---- signal primitives, both strictly over COMPLETED bars before the current one

    def entry_level(self, view: DataView, index: int) -> float:
        """max(high) over index−n_entry … index−1. Today's own high is excluded, so a
        bar can never trigger on itself."""
        return max(view[j].high for j in range(index - self.n_entry, index))

    def exit_level(self, view: DataView, index: int) -> float:
        """min(low) over index−n_exit … index−1."""
        return min(view[j].low for j in range(index - self.n_exit, index))

    def entry_condition(self, view: DataView, index: int) -> bool:
        return view[index].close > self.entry_level(view, index)

    def exit_condition(self, view: DataView, index: int) -> bool:
        return view[index].close < self.exit_level(view, index)

    def warm_up_bars(self) -> int:
        """Minimum `current_index` at which every component can be evaluated."""
        required = max(self.n_entry, self.n_exit)
        required = max(required, self.weight_source.warm_up_bars())
        for f in self.filters:
            required = max(required, f.warm_up_bars(self.n_entry, self.n_exit))
        return required

    # ---- the D27 interface

    def generate_targets(self, views: Mapping[str, DataView]) -> list[TargetWeight]:
        view = views[self.instrument_id]
        i = view.current_index

        if i < self.warm_up_bars():
            # Warm-up self-guard (the same shape ZScorePairsStrategy uses): stand
            # aside until every component has the history it needs.
            return self._targets(0.0)

        if self._in_position:
            if self.exit_condition(view, i):
                self._in_position, self._held_weight = False, 0.0
            elif self.weight_source.rebalance == "every_bar":
                w = self.weight_source.weight(view)
                if w is not None:
                    self._held_weight = w
        elif self.entry_condition(view, i) and all(
            f.accepts(view, lambda j: self.entry_condition(view, j)) for f in self.filters
        ):
            w = self.weight_source.weight(view)
            if w is not None and w > 0.0:
                self._in_position, self._held_weight = True, w

        return self._targets(self._held_weight)

    def _targets(self, weight: float) -> list[TargetWeight]:
        return [
            TargetWeight(
                strategy_id=self.strategy_id, instrument_id=self.instrument_id, weight=weight
            )
        ]

    def config(self) -> dict[str, Any]:
        """Declarative description of the whole strategy (D52/D102) — what the
        registry hashes, and what `build_breakout_strategy` rebuilds."""
        return {
            "type": "breakout_long_flat",
            "n_entry": self.n_entry,
            "n_exit": self.n_exit,
            "weight_source": self.weight_source.config(),
            "filters": [f.config() for f in self.filters],
        }


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
    "trend_gate",
    lambda c: TrendGateFilter(sma_window=int(_optional_number(c, "sma_window", 200, "trend_gate"))),
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
        weight_source=build_weight_source(config["weight_source"]),
        filters=tuple(build_entry_filter(f) for f in filters),
    )
