"""Futures fill model for intraday bars: entries, exits, passive limits and path
statistics on a tick grid.

Conventions
-----------
* Entry: the close (or optionally the open) of bar t0+1, plus `ticks_adverse` ticks
  against the position.
* Touch versus trade-through: `FillAssumption.TOUCH` counts a level as reached when the
  bar's range reaches it; `TRADE_THROUGH` requires the bar to trade one full tick beyond
  it. Using one tick as the epsilon gives the rule the same meaning on every contract. On
  a tick grid `low <= limit - tick` is equivalent to `low < limit`.
* Stops and targets may use different rules (a resting stop becomes a market order; a
  resting limit does not), and `resolve_exit` accepts both.
* A bar that breaks both a stop and a target is resolved, never skipped, so the sample
  does not change.

Costs
-----
Commission, spread and slippage beyond the tick belong to the `CostStack` bricks. This
module applies only `ticks_adverse` on a market entry and, when requested,
`stop_slippage_ticks` on a stop.

Same-bar stop and target
------------------------
If the stop and a profit exit could both be hit within the same bar, the stop is assumed.
One-minute bars do not record the order of the two touches. `resolve_exit` never returns
a target from a bar whose range also reached the stop.

Inputs
------
The primitives take numpy arrays of one session's bars, indexed by bar. `session_ohlc` is
the pandas adapter and the only function that takes a DataFrame.

Run the self-test with:

    uv run python -m backtest_framework.simulator.futures_fills
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Literal, cast

import numpy as np

from backtest_framework.instruments.future import GRID_TOLERANCE_TICKS, ULP_FLOOR, Future
from backtest_framework.simulator.fills import Bar, StopSide, stop_fill_price

__all__ = [
    "Side",
    "FillAssumption",
    "ExitKind",
    "Fill",
    "ExitResolution",
    "PassiveResult",
    "PassiveSession",
    "SessionOHLC",
    "adverse_price",
    "assert_entry_before",
    "bar_at",
    "entry_fill",
    "passive_diagnostic",
    "passive_limit",
    "resolve_exit",
    "running_peak_drawdown",
    "session_ohlc",
    "selftest",
    "stress_fill",
]


class Side(Enum):
    """The side of the position, not of the order that opens or closes it."""

    LONG = "long"
    SHORT = "short"

    @property
    def sign(self) -> float:
        """+1 for a long, -1 for a short; multiplies a price move into the position's P&L."""
        return 1.0 if self is Side.LONG else -1.0


class FillAssumption(Enum):
    """Conventions for whether a resting level was reached.

    The trade-through epsilon is one tick, the smallest amount a market can trade through
    a level by.
    """

    TOUCH = "touch"
    """Reached when the bar's range reaches the level. Optimistic: ignores queue position."""

    TRADE_THROUGH = "trade_through"
    """Reached only when the bar trades a full tick through the level. Pessimistic; suits a
    passive order, whose fill when price keeps going is the adverse selection that
    `passive_diagnostic` measures."""


class ExitKind(Enum):
    STOP = "stop"
    TARGET = "target"
    NONE = "none"


@dataclass(frozen=True)
class Fill:
    bar: int
    """Index of the bar the fill happened on, in the session arrays passed in."""
    price: float
    """Always on the tick grid."""


@dataclass(frozen=True)
class ExitResolution:
    kind: ExitKind
    price: float | None
    """None if and only if `kind is ExitKind.NONE`."""
    gapped: bool
    """True when the fill price is the bar's open rather than the level: a stop gapped
    through, or a target gapped past in the position's favour."""


@dataclass(frozen=True)
class PassiveResult:
    filled: bool
    bar: int | None
    price: float | None


@dataclass(frozen=True)
class SessionOHLC:
    """One session's bars as four aligned float arrays."""

    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray


@dataclass(frozen=True)
class PassiveSession:
    """One session's bars plus the decision bar and the side the caller would trade."""

    ohlc: SessionOHLC
    t0: int
    side: Side


# --------------------------------------------------------------------------- guards


def _check_side(side: Any) -> Side:
    if not isinstance(side, Side):
        raise TypeError(
            f"side must be a futures_fills.Side, got {type(side).__name__} ({side!r}). "
            "A string or an int could swap long and short."
        )
    return side


def _check_rule(rule: Any, what: str) -> FillAssumption:
    if not isinstance(rule, FillAssumption):
        raise TypeError(f"{what} must be a FillAssumption, got {type(rule).__name__} ({rule!r})")
    return rule


def _as_array(values: Sequence[float] | np.ndarray, what: str) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1:
        raise ValueError(f"{what} must be one-dimensional (one session's bars), got shape {array.shape}")
    if array.size == 0:
        raise ValueError(f"{what} is empty")
    return array


def _require_bar(index: int, n_bars: int, what: str) -> None:
    """Raise when a bar the caller needs is outside the session.

    Windows are never truncated: a stress window cut short near the session close would
    weaken the stress fill on those days.
    """
    if index < 0:
        raise ValueError(f"{what}: bar index {index} is before the session start")
    if index >= n_bars:
        raise ValueError(
            f"{what}: bar index {index} is past the session end ({n_bars} bars). "
            "Skip the signal or widen the session."
        )


def _finite(value: float, what: str) -> float:
    if not math.isfinite(value):
        raise ValueError(f"{what} is not finite ({value!r}); a missing bar has no price")
    return float(value)


def _assert_all_on_grid(array: np.ndarray, fut: Future, what: str) -> None:
    """Vectorised `Future.assert_on_grid` over a whole session.

    Every bar is checked, and the error names the worst offending bar.
    """
    n = array / fut.tick_points
    residual = np.abs(n - np.floor(n + 0.5))
    tolerance = np.maximum(GRID_TOLERANCE_TICKS, ULP_FLOOR * np.spacing(np.abs(n)))
    worst = int(np.argmax(residual - tolerance))
    if float(residual[worst]) > float(tolerance[worst]):
        raise ValueError(
            f"{fut.root}: {what}[{worst}] = {float(array[worst])!r} is "
            f"{float(residual[worst]):.6g} ticks off the {fut.tick_points} grid"
        )


# ------------------------------------------------------------------ pandas adapter


def session_ohlc(
    frame: Any,
    *,
    columns: tuple[str, str, str, str] = ("open", "high", "low", "close"),
) -> SessionOHLC:
    """Convert a one-session DataFrame to `SessionOHLC`, selecting columns by name."""
    missing = [c for c in columns if c not in getattr(frame, "columns", ())]
    if missing:
        raise KeyError(f"session_ohlc: frame has no column(s) {missing}; it has {list(getattr(frame, 'columns', []))}")
    arrays = [_as_array(np.asarray(frame[c], dtype=float), c) for c in columns]
    lengths = {a.size for a in arrays}
    if len(lengths) != 1:
        raise ValueError(f"session_ohlc: columns have differing lengths {lengths}")
    return SessionOHLC(open=arrays[0], high=arrays[1], low=arrays[2], close=arrays[3])


def bar_at(ohlc: SessionOHLC, index: int) -> Bar:
    """Return bar `index` as a `simulator.fills.Bar`, the input to the stop gap rule."""
    _require_bar(index, ohlc.close.size, "bar_at")
    return Bar(
        open=_finite(float(ohlc.open[index]), f"open[{index}]"),
        high=_finite(float(ohlc.high[index]), f"high[{index}]"),
        low=_finite(float(ohlc.low[index]), f"low[{index}]"),
        close=_finite(float(ohlc.close[index]), f"close[{index}]"),
    )


# -------------------------------------------------------------------- the concession


def adverse_price(price: float, side: Side, ticks: float, fut: Future, *, closing: bool = False) -> float:
    """Move `price` by `ticks` against the position, in the instrument's tick.

    When opening, a long pays up and a short sells down. When closing (`closing=True`), the
    signs reverse: a long sells lower and a short buys higher. The caller always states
    which.

    No grid check is done here; `resolve_exit` applies it once, where the caller has said
    whether the levels are on the grid.
    """
    side = _check_side(side)
    if not math.isfinite(ticks) or ticks < 0:
        raise ValueError(f"ticks must be a finite non-negative count, got {ticks!r}")
    _finite(price, "price")
    direction = side.sign * (-1.0 if closing else 1.0)
    return price + direction * ticks * fut.tick_points


# ------------------------------------------------------------------------- entries


def entry_fill(
    close: Sequence[float] | np.ndarray,
    t0: int,
    side: Side,
    fut: Future,
    ticks_adverse: float = 1,
    *,
    at: Literal["close", "open"] = "close",
    open: Sequence[float] | np.ndarray | None = None,
) -> Fill:
    """Primary entry fill: bar t0+1, plus `ticks_adverse` ticks against the side.

    `at="close"` (the default) fills at the close of bar t0+1; `at="open"` fills at its
    open. They assume different decision times. `at="open"` requires `open` and raises
    if it is missing rather than falling back to `close`.

    Raises when t0+1 is past the session end.
    """
    side = _check_side(side)
    closes = _as_array(close, "close")
    if at == "close":
        anchor = closes
    elif at == "open":
        if open is None:
            raise ValueError(
                "entry_fill(at='open') needs the open array; the close is a different fill "
                "convention and is not substituted."
            )
        anchor = _as_array(open, "open")
        if anchor.size != closes.size:
            raise ValueError(f"open ({anchor.size}) and close ({closes.size}) have different lengths")
    else:
        raise ValueError(f"at must be 'close' or 'open', got {at!r}")

    bar = int(t0) + 1
    _require_bar(bar, anchor.size, "entry_fill(t0+1)")
    anchor_price = _finite(float(anchor[bar]), f"entry anchor {at}[{bar}]")
    fut.assert_on_grid(anchor_price, f"entry anchor {at}[{bar}]")
    price = adverse_price(anchor_price, side, ticks_adverse, fut, closing=False)
    fut.assert_on_grid(price, "entry fill")
    return Fill(bar=bar, price=price)


def stress_fill(
    close: Sequence[float] | np.ndarray,
    t0: int,
    side: Side,
    fut: Future,
    k: int = 5,
    ticks_adverse: float = 1,
) -> Fill:
    """Stress entry: the worst close among bars t0+1 ... t0+k for the side.

    Worst is highest for a long and lowest for a short; ties take the earliest bar.
    `ticks_adverse` defaults to one tick, as in `entry_fill`, so the stress fill is never
    better than the primary fill for the side (a property test checks this).

    Raises when t0+k is past the session end; the window is never truncated.
    """
    side = _check_side(side)
    closes = _as_array(close, "close")
    if int(k) < 1:
        raise ValueError(f"k must be at least 1, got {k!r}")
    first, last = int(t0) + 1, int(t0) + int(k)
    _require_bar(first, closes.size, "stress_fill(t0+1)")
    _require_bar(last, closes.size, f"stress_fill(t0+{int(k)})")
    window = closes[first : last + 1]
    if not np.isfinite(window).all():
        raise ValueError(f"stress_fill: bars {first}..{last} contain a non-finite close")
    offset = int(np.argmax(window)) if side is Side.LONG else int(np.argmin(window))
    bar = first + offset
    anchor = float(closes[bar])
    fut.assert_on_grid(anchor, f"stress anchor close[{bar}]")
    price = adverse_price(anchor, side, ticks_adverse, fut, closing=False)
    fut.assert_on_grid(price, "stress fill")
    return Fill(bar=bar, price=price)


# --------------------------------------------------------------------------- exits


def resolve_exit(
    bar: Bar,
    stop: float | None,
    target: float | None,
    side: Side,
    fut: Future,
    *,
    stop_rule: FillAssumption = FillAssumption.TOUCH,
    target_rule: FillAssumption = FillAssumption.TOUCH,
    stop_slippage_ticks: float = 0,
    gap_through: bool = True,
    levels_on_grid: bool = True,
) -> ExitResolution:
    """Resolve one bar against a stop and a target; the stop wins when both are reached.

    Defaults: touch on both orders, the gap-through rule on the stop (a gapped stop fills
    at the open), no slippage beyond the level, levels on the tick grid. Common variants:

    * `stop_rule=TRADE_THROUGH, target_rule=TOUCH`: the stop needs a trade-through
      (`low <= stop - tick`, equivalent to `low < stop` on the grid); the target fills on
      touch.
    * `stop_slippage_ticks=1, gap_through=False`: a trailing stop that fills at
      `stop - tick` and ignores the open.
    * `levels_on_grid=False`: for a level that is not a tradeable price, such as a target
      at 0.95 of yesterday's range. The grid checks on levels and fills are skipped and
      the caller is responsible for them.

    Raises when `high < low`, when the open or close is outside the bar's range, or on an
    invalid side.
    """
    side = _check_side(side)
    stop_rule = _check_rule(stop_rule, "stop_rule")
    target_rule = _check_rule(target_rule, "target_rule")
    for name, value in (("open", bar.open), ("high", bar.high), ("low", bar.low), ("close", bar.close)):
        _finite(value, f"bar.{name}")
    if bar.high < bar.low:
        raise ValueError(f"resolve_exit: bar.high ({bar.high!r}) < bar.low ({bar.low!r})")
    if not (bar.low <= bar.open <= bar.high):
        raise ValueError(f"resolve_exit: bar.open ({bar.open!r}) outside [{bar.low!r}, {bar.high!r}]")
    if not (bar.low <= bar.close <= bar.high):
        raise ValueError(f"resolve_exit: bar.close ({bar.close!r}) outside [{bar.low!r}, {bar.high!r}]")
    if levels_on_grid:
        if stop is not None:
            fut.assert_on_grid(stop, "stop level")
        if target is not None:
            fut.assert_on_grid(target, "target level")

    if stop is not None:
        resolved = _stop_branch(bar, float(stop), side, fut, stop_rule, gap_through)
        if resolved is not None:
            raw, gapped = resolved
            price = adverse_price(raw, side, stop_slippage_ticks, fut, closing=True)
            if levels_on_grid:
                fut.assert_on_grid(price, "stop fill")
            return ExitResolution(ExitKind.STOP, price, gapped)

    if target is not None:
        resolved = _target_branch(bar, float(target), side, fut, target_rule)
        if resolved is not None:
            price, gapped = resolved
            if levels_on_grid:
                fut.assert_on_grid(price, "target fill")
            return ExitResolution(ExitKind.TARGET, price, gapped)

    return ExitResolution(ExitKind.NONE, None, False)


def _stop_branch(
    bar: Bar, stop: float, side: Side, fut: Future, rule: FillAssumption, gap_through: bool
) -> tuple[float, bool] | None:
    """Return (price before slippage, gapped), or None when the stop was not reached."""
    if side is Side.LONG:
        threshold = stop if rule is FillAssumption.TOUCH else stop - fut.tick_points
        if not bar.low <= threshold:
            return None
        stop_side, gapped = StopSide.SELL_STOP, bar.open <= stop
    else:
        threshold = stop if rule is FillAssumption.TOUCH else stop + fut.tick_points
        if not bar.high >= threshold:
            return None
        stop_side, gapped = StopSide.BUY_STOP, bar.open >= stop
    if not gap_through:
        return stop, False
    price = stop_fill_price(stop_side, stop, bar)
    if price is None:  # pragma: no cover - the trigger above implies a touch
        raise ValueError(
            f"_stop_branch: {side} stop {stop!r} triggered on bar {bar!r} but "
            "stop_fill_price says untouched -- the two rules have drifted apart"
        )
    return price, gapped


def _target_branch(
    bar: Bar, target: float, side: Side, fut: Future, rule: FillAssumption
) -> tuple[float, bool] | None:
    """Return (fill price, gapped), or None when the target was not reached.

    A limit fills at its level, or at the open when the bar gaps past it. Trade-through
    means the bar traded a full tick beyond the level, as for the stop.
    """
    if side is Side.LONG:
        threshold = target if rule is FillAssumption.TOUCH else target + fut.tick_points
        if not bar.high >= threshold:
            return None
        return max(target, bar.open), bar.open > target
    threshold = target if rule is FillAssumption.TOUCH else target - fut.tick_points
    if not bar.low <= threshold:
        return None
    return min(target, bar.open), bar.open < target


# ------------------------------------------------------------------- passive orders


def passive_limit(
    open: Sequence[float] | np.ndarray,
    high: Sequence[float] | np.ndarray,
    low: Sequence[float] | np.ndarray,
    close: Sequence[float] | np.ndarray,
    t0: int,
    side: Side,
    fut: Future,
    cancel_after: int = 5,
    rule: FillAssumption = FillAssumption.TRADE_THROUGH,
) -> PassiveResult:
    """Simulate a resting limit at the t0 close, working bars t0+1 ... t0+cancel_after.

    `TOUCH` fills when the bar's range reaches the limit. `TRADE_THROUGH` (the default,
    the conservative choice for a passive order) requires a trade one tick through it.

    The fill price is always the limit. `open` is read only to validate the bars; a gap
    past the limit earns no price improvement, which would make a passive backtest
    optimistic.

    Raises when t0+cancel_after is past the session end.
    """
    side = _check_side(side)
    rule = _check_rule(rule, "rule")
    arrays = [_as_array(a, n) for a, n in ((open, "open"), (high, "high"), (low, "low"), (close, "close"))]
    if len({a.size for a in arrays}) != 1:
        raise ValueError(f"passive_limit: OHLC arrays have differing lengths {[a.size for a in arrays]}")
    o, h, lo, c = arrays
    n = c.size
    if int(cancel_after) < 1:
        raise ValueError(f"cancel_after must be at least 1, got {cancel_after!r}")
    first, last = int(t0) + 1, int(t0) + int(cancel_after)
    _require_bar(int(t0), n, "passive_limit(t0)")
    _require_bar(last, n, f"passive_limit(t0+{int(cancel_after)})")

    limit = _finite(float(c[int(t0)]), f"close[{int(t0)}]")
    fut.assert_on_grid(limit, "limit price")
    for j in range(first, last + 1):
        _finite(float(o[j]), f"open[{j}]")
        bar_hi, bar_lo = _finite(float(h[j]), f"high[{j}]"), _finite(float(lo[j]), f"low[{j}]")
        if bar_hi < bar_lo:
            raise ValueError(f"passive_limit: bar {j} has high {bar_hi!r} < low {bar_lo!r}")
        if not (bar_lo <= float(o[j]) <= bar_hi):
            raise ValueError(f"passive_limit: bar {j} open {float(o[j])!r} outside [{bar_lo!r}, {bar_hi!r}]")
        if side is Side.LONG:
            threshold = limit if rule is FillAssumption.TOUCH else limit - fut.tick_points
            reached = bar_lo <= threshold
        else:
            threshold = limit if rule is FillAssumption.TOUCH else limit + fut.tick_points
            reached = bar_hi >= threshold
        if reached:
            return PassiveResult(filled=True, bar=j, price=limit)
    return PassiveResult(filled=False, bar=None, price=None)


def passive_diagnostic(
    sessions: Iterable[PassiveSession],
    fut: Future,
    *,
    horizon: int,
    cancel_after: int = 5,
    rule: FillAssumption = FillAssumption.TRADE_THROUGH,
) -> dict[str, float]:
    """Compare outcomes of signals whose passive limit filled with those that did not.

    The outcome is the move from the t0 close to the t0+horizon close, in ticks, signed
    in the position's direction. No costs or entry concession are applied; they would
    shift both means equally.

    Returns `unfilled_rate`, `mean_outcome_filled`, `mean_outcome_unfilled`, `n`,
    `n_filled` and `n_unfilled`. The mean of an empty group is `nan`.
    """
    if int(horizon) < 1:
        raise ValueError(f"horizon must be at least 1 bar, got {horizon!r}")
    filled_outcomes: list[float] = []
    unfilled_outcomes: list[float] = []
    for i, s in enumerate(sessions):
        if not isinstance(s, PassiveSession):
            raise TypeError(f"sessions[{i}] must be a PassiveSession, got {type(s).__name__}")
        side = _check_side(s.side)
        n = s.ohlc.close.size
        _require_bar(int(s.t0), n, f"passive_diagnostic(sessions[{i}].t0)")
        _require_bar(int(s.t0) + int(horizon), n, f"passive_diagnostic(sessions[{i}].t0+{int(horizon)})")
        result = passive_limit(
            s.ohlc.open, s.ohlc.high, s.ohlc.low, s.ohlc.close,
            s.t0, side, fut, cancel_after=cancel_after, rule=rule,
        )
        move = _finite(float(s.ohlc.close[int(s.t0) + int(horizon)]), "horizon close") - _finite(
            float(s.ohlc.close[int(s.t0)]), "t0 close"
        )
        outcome = fut.ticks(move * side.sign)
        (filled_outcomes if result.filled else unfilled_outcomes).append(outcome)

    total = len(filled_outcomes) + len(unfilled_outcomes)
    if total == 0:
        raise ValueError("passive_diagnostic: no sessions, so the unfilled rate is undefined")
    return {
        "unfilled_rate": len(unfilled_outcomes) / total,
        "mean_outcome_filled": float(np.mean(filled_outcomes)) if filled_outcomes else float("nan"),
        "mean_outcome_unfilled": float(np.mean(unfilled_outcomes)) if unfilled_outcomes else float("nan"),
        "n": float(total),
        "n_filled": float(len(filled_outcomes)),
        "n_unfilled": float(len(unfilled_outcomes)),
    }


# ------------------------------------------------------------------ path statistics


def running_peak_drawdown(
    high: Sequence[float] | np.ndarray,
    low: Sequence[float] | np.ndarray,
    side: Side,
    fut: Future,
) -> float:
    """Worst drawdown from the running peak over a hold, in price points (pessimistic).

    For a long: `max_j( max_{i<=j} high_i  -  low_j )`; for a short, the mirror off the
    running trough. The peak includes bar j's own high, which assumes high-then-low within
    every bar and overstates the true drawdown. Only this convention is implemented.

    This is what a trailing drawdown limit on open equity measures; divided by the entry
    price it is the pessimistic maximum adverse excursion as a fraction.

    `fut` is used to check the bars are on the grid; NaN or off-grid bars raise.
    """
    side = _check_side(side)
    hi, lo = _as_array(high, "high"), _as_array(low, "low")
    if hi.size != lo.size:
        raise ValueError(f"high ({hi.size}) and low ({lo.size}) have different lengths")
    if not np.isfinite(hi).all() or not np.isfinite(lo).all():
        raise ValueError("running_peak_drawdown: bars must be finite")
    if bool(np.any(hi < lo)):
        j = int(np.argmax(hi < lo))
        raise ValueError(f"running_peak_drawdown: bar {j} has high {hi[j]!r} < low {lo[j]!r}")
    _assert_all_on_grid(hi, fut, "high")
    _assert_all_on_grid(lo, fut, "low")
    if side is Side.LONG:
        return float(np.max(np.maximum.accumulate(hi) - lo))
    return float(np.max(hi - np.minimum.accumulate(lo)))


# ------------------------------------------------------------------- timing guards


def assert_entry_before(bar_ts: Any, window_start: Any, min_minutes: float = 3) -> None:
    """Raise unless the entry completes at least `min_minutes` before `window_start`.

    `bar_ts` is when the entry is complete: the close of the fill bar, not of the decision
    bar. A rejection raises `ValueError` rather than returning a flag a caller could ignore.
    """
    if min_minutes < 0:
        raise ValueError(f"min_minutes must be non-negative, got {min_minutes!r}")
    try:
        lead_minutes = (window_start - bar_ts).total_seconds() / 60.0
    except (AttributeError, TypeError) as exc:
        raise TypeError(
            f"assert_entry_before needs two subtractable timestamps whose difference has "
            f"total_seconds(); got {type(bar_ts).__name__} and {type(window_start).__name__}"
        ) from exc
    if lead_minutes < min_minutes:
        raise ValueError(
            f"entry completes at {bar_ts} which is {lead_minutes:.4g} min before the window "
            f"start {window_start}; the rule needs at least {min_minutes} min. No trade."
        )


# ------------------------------------------------------------------------ selftest


def _expect_raise(fn: Any, exc: type[BaseException], what: str, log: Any = print) -> None:
    """Assert that `fn` raises `exc`."""
    try:
        fn()
    except exc as e:
        log(f"    RAISES on {what}: {type(e).__name__}: {str(e)[:78]}")
        return
    raise AssertionError(f"self-test check did not raise on {what}")


def selftest(log: Any = print) -> int:
    """Run each guard on a valid and an invalid input. Returns 0, or raises."""
    es = Future(root="ES", tick_points=0.25, usd_per_point=50.0, tick_usd=12.5)
    o = np.array([100.00, 100.25, 100.50, 100.25, 100.00], dtype=float)
    h = np.array([100.50, 100.75, 101.00, 100.50, 100.25], dtype=float)
    lo_ = np.array([99.75, 100.25, 100.25, 99.75, 99.50], dtype=float)
    c = np.array([100.25, 100.50, 100.75, 100.00, 99.75], dtype=float)

    log("  [1] the tick grid")
    es.assert_on_grid(100.25)
    assert es.round_to_tick(100.30, "down") == 100.25
    assert es.round_to_tick(100.30, "up") == 100.50
    assert es.round_to_tick(100.30, "nearest") == 100.25
    _expect_raise(lambda: es.assert_on_grid(100.30), ValueError, "an off-grid price")
    _expect_raise(lambda: Future.from_specs("NOPE"), KeyError, "an unknown root")
    _expect_raise(
        lambda: Future(root="ES", tick_points=0.25, usd_per_point=50.0, tick_usd=13.0),
        ValueError, "tick_usd disagreeing with usd_per_point x tick_points",
    )

    log("  [2] entry and stress fills")
    f = entry_fill(c, 0, Side.LONG, es)
    assert f == Fill(bar=1, price=100.75), f
    assert entry_fill(c, 0, Side.SHORT, es) == Fill(bar=1, price=100.25)
    assert entry_fill(c, 0, Side.LONG, es, at="open", open=o) == Fill(bar=1, price=100.50)
    s = stress_fill(c, 0, Side.LONG, es, k=4)
    assert s == Fill(bar=2, price=101.00), s
    assert stress_fill(c, 0, Side.SHORT, es, k=4) == Fill(bar=4, price=99.50)
    assert s.price >= f.price, "stress is never better than the primary fill"
    _expect_raise(lambda: entry_fill(c, 4, Side.LONG, es), ValueError, "t0+1 past the session end")
    _expect_raise(lambda: stress_fill(c, 1, Side.LONG, es, k=5), ValueError, "t0+k past the session end")
    _expect_raise(lambda: entry_fill(c, 0, cast(Side, "long"), es), TypeError, "a side that is not a Side")
    _expect_raise(lambda: entry_fill(c, 0, Side.LONG, es, at="open"), ValueError, "at='open' with no open array")

    log("  [3] intra-bar pessimism")
    spanning = Bar(open=100.00, high=101.00, low=99.00, close=100.00)
    r = resolve_exit(spanning, stop=99.50, target=100.50, side=Side.LONG, fut=es)
    assert r.kind is ExitKind.STOP and r.price == 99.50 and not r.gapped, r
    r = resolve_exit(spanning, stop=100.50, target=99.50, side=Side.SHORT, fut=es)
    assert r.kind is ExitKind.STOP and r.price == 100.50, r
    r = resolve_exit(spanning, stop=None, target=100.50, side=Side.LONG, fut=es)
    assert r.kind is ExitKind.TARGET and r.price == 100.50, r
    gap = Bar(open=99.00, high=99.50, low=98.50, close=99.25)
    r = resolve_exit(gap, stop=99.75, target=101.00, side=Side.LONG, fut=es)
    assert r.kind is ExitKind.STOP and r.price == 99.00 and r.gapped, r
    r = resolve_exit(Bar(open=101.00, high=101.50, low=100.75, close=101.25), 99.00, 100.50, Side.LONG, es)
    assert r.kind is ExitKind.TARGET and r.price == 101.00 and r.gapped, r
    r = resolve_exit(Bar(open=100.00, high=100.25, low=99.75, close=100.00), 99.00, 101.00, Side.LONG, es)
    assert r.kind is ExitKind.NONE and r.price is None, r
    _expect_raise(
        lambda: resolve_exit(Bar(open=100.0, high=99.0, low=101.0, close=100.0), 99.0, 101.0, Side.LONG, es),
        ValueError, "a bar with high < low",
    )
    _expect_raise(
        lambda: resolve_exit(spanning, stop=99.30, target=100.50, side=Side.LONG, fut=es),
        ValueError, "an off-grid stop level",
    )

    log("  [4] trade-through stop with slippage")
    stopped = resolve_exit(
        Bar(open=100.00, high=100.25, low=99.50, close=99.75), stop=99.75, target=101.00, side=Side.LONG, fut=es,
        stop_rule=FillAssumption.TRADE_THROUGH, stop_slippage_ticks=1, gap_through=False,
    )
    assert stopped.kind is ExitKind.STOP and stopped.price == 99.50, stopped
    not_through = resolve_exit(
        Bar(open=100.00, high=100.25, low=99.75, close=99.75), stop=99.75, target=101.00, side=Side.LONG, fut=es,
        stop_rule=FillAssumption.TRADE_THROUGH, stop_slippage_ticks=1, gap_through=False,
    )
    assert not_through.kind is ExitKind.NONE, not_through

    log("  [5] passive limit and its diagnostic")
    p = passive_limit(o, h, lo_, c, 0, Side.LONG, es, cancel_after=3)
    assert p == PassiveResult(True, 3, 100.25), p
    p_touch = passive_limit(o, h, lo_, c, 0, Side.LONG, es, cancel_after=1, rule=FillAssumption.TOUCH)
    assert p_touch == PassiveResult(True, 1, 100.25), p_touch
    p_tt = passive_limit(o, h, lo_, c, 0, Side.LONG, es, cancel_after=1)
    assert p_tt == PassiveResult(False, None, None), p_tt
    diag = passive_diagnostic(
        [PassiveSession(SessionOHLC(o, h, lo_, c), 0, Side.LONG)], es, horizon=4, cancel_after=3
    )
    assert diag["n"] == 1.0 and diag["unfilled_rate"] == 0.0, diag
    assert diag["mean_outcome_filled"] == -2.0, diag
    _expect_raise(
        lambda: passive_limit(o, h, lo_, c, 0, Side.LONG, es, cancel_after=5),
        ValueError, "a cancel window past the session end",
    )
    _expect_raise(lambda: passive_diagnostic([], es, horizon=1), ValueError, "a diagnostic over no sessions")

    log("  [6] running-peak drawdown")
    assert running_peak_drawdown(h, lo_, Side.LONG, es) == 1.50, running_peak_drawdown(h, lo_, Side.LONG, es)
    assert running_peak_drawdown(h, lo_, Side.SHORT, es) == 1.25
    _expect_raise(
        lambda: running_peak_drawdown(np.array([1.0]), np.array([2.0]), Side.LONG, es),
        ValueError, "a bar with high < low",
    )

    log("  [7] the entry timing constraint")
    start = datetime(2019, 6, 3, 14, 28)
    assert_entry_before(start - timedelta(minutes=3), start)
    _expect_raise(
        lambda: assert_entry_before(start - timedelta(minutes=2), start),
        ValueError, "an entry completing 2 min before the window",
    )
    log("  selftest OK")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(selftest())
