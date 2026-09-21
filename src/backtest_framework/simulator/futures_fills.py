"""The shared futures fill model (D587) — one place for conventions five scripts each owned.

WHAT THIS REPLACES
-------------------
Every intraday futures runner here re-derived the same four decisions inline, and they
did not agree:

* `run_d490_range_reversion.py:simulate` enters at the next bar's OPEN plus one tick,
  fills a trailing stop at `stop - TICK` with no gap rule, and takes its target at
  `max(T, O[j])`. Its stop trigger is `low < stop` — trade-through — while its target
  trigger is `high >= T` — touch. **Two different assumptions in one loop**, which is
  defensible (a resting stop becomes a market order; a resting limit does not) but was
  nowhere written down.
* `engine/backtest.py:_sweep_intrabar_stops` treats the stop as the only intrabar order
  (D42): nothing there can span a stop and a target in one bar, so the pessimism rule
  never had to be stated.
* `research/terrain_strategies.py:run_bounce_rr` checks the stop before the target — the
  same pessimism — and defines `FillAssumption.TOUCH` / `TRADE_THROUGH` with
  `TRADE_THROUGH_EPS = 1e-9`, an ABSOLUTE epsilon. On ES that is 4e-9 of a tick; on a
  contract quoted in 32nds it is a different rule. **Here the epsilon is one tick**, and
  on a tick grid `low <= limit - tick` is exactly `low < limit`, which is what D490's
  strict inequality already meant.
* `run_d531_orb_session_native.py:breakouts` SKIPS a bar that breaks both sides — a third
  convention, and the only one that discards the observation rather than resolving it.
  It is recorded here and NOT adopted: a skipped bar is a silent sample change.

WHAT IT IS NOT
---------------
**Not a cost model.** Commission, spread and slippage-beyond-the-tick belong to the
`CostStack` bricks (D1, D2). The only concession this module applies is the one the
deposit pre-registrations name in their fill sections: `ticks_adverse` on a market entry,
and `stop_slippage_ticks` on a stop when a caller's convention demands it.

THE PESSIMISM RULE, AND WHERE IT COMES FROM
--------------------------------------------
`SHOCK_CLASSIFIER_PREREG.md` §5.3, `SETTLEMENT_FLOW_LEDGER_PREREG.md` §7.4 and
`OPENING_AGENT_STATE_PREREG.md` §6.3 all say the same sentence: *if the stop and a profit
exit could both be hit within the same bar, assume the stop*. One-minute bars do not
record the order of the two touches, so the choice is between a rule and a wish.
`resolve_exit` implements the rule; nothing in it can return a target from a bar whose
stop was also inside.

ARRAY-FIRST
------------
The primitives take numpy arrays of one session's bars, indexed by bar, because that is
what every runner already holds after its pivot. `session_ohlc` is the pandas adapter and
is deliberately the only place a DataFrame appears.

Run the audits with:

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
    """The side of the POSITION, not of the order that opens or closes it."""

    LONG = "long"
    SHORT = "short"

    @property
    def sign(self) -> float:
        """+1 for a long, -1 for a short. The multiplier a signed move is scored with."""
        return 1.0 if self is Side.LONG else -1.0


class FillAssumption(Enum):
    """D9's two conventions for whether a resting level was reached.

    The name is deliberately the same as `research/terrain_strategies.py`'s; the
    EPSILON is not. There it is `TRADE_THROUGH_EPS = 1e-9` in price units; here it is one
    tick, which is the smallest amount a market can actually trade through a level by.
    """

    TOUCH = "touch"
    """Reached when the bar's range reaches the level. Optimistic: ignores queue position."""

    TRADE_THROUGH = "trade_through"
    """Reached only when the bar trades through the level by a full tick. Pessimistic, and
    the honest one for a passive order — being filled only when price keeps going is the
    adverse selection the passive diagnostic exists to measure."""


class ExitKind(Enum):
    STOP = "stop"
    TARGET = "target"
    NONE = "none"


@dataclass(frozen=True)
class Fill:
    bar: int
    """Index of the bar the fill happened on, in the session arrays passed in."""
    price: float
    """On the tick grid, always."""


@dataclass(frozen=True)
class ExitResolution:
    kind: ExitKind
    price: float | None
    """None exactly when `kind is ExitKind.NONE`."""
    gapped: bool
    """True when the fill price came from the bar's OPEN rather than from the level —
    a stop gapped through (D10) or a target gapped past in the position's favour."""


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
            "A string or an int would silently transpose long and short, which is the "
            "class of bug D280 was inverted by."
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
    """Raise when a bar the caller needs is outside the session. NEVER truncate.

    Silently shortening a five-bar stress window to whatever the session had left is how
    a stress fill stops being a stress fill on exactly the days near the close, which are
    the days it matters on.
    """
    if index < 0:
        raise ValueError(f"{what}: bar index {index} is before the session start")
    if index >= n_bars:
        raise ValueError(
            f"{what}: bar index {index} is past the session end ({n_bars} bars). "
            "The window is not silently truncated -- the caller decides whether to skip "
            "the signal or to widen the session."
        )


def _finite(value: float, what: str) -> float:
    if not math.isfinite(value):
        raise ValueError(f"{what} is not finite ({value!r}); a missing bar is not a price")
    return float(value)


def _assert_all_on_grid(array: np.ndarray, fut: Future, what: str) -> None:
    """The vectorised form of `Future.assert_on_grid`, for a whole session at once.

    Checking only the first bar would be a gate that cannot fire on the bar that is
    actually wrong, which is the shape of audit this repository keeps finding.
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
    """The one place a DataFrame appears. Columns are named, never positional."""
    missing = [c for c in columns if c not in getattr(frame, "columns", ())]
    if missing:
        raise KeyError(f"session_ohlc: frame has no column(s) {missing}; it has {list(getattr(frame, 'columns', []))}")
    arrays = [_as_array(np.asarray(frame[c], dtype=float), c) for c in columns]
    lengths = {a.size for a in arrays}
    if len(lengths) != 1:
        raise ValueError(f"session_ohlc: columns have differing lengths {lengths}")
    return SessionOHLC(open=arrays[0], high=arrays[1], low=arrays[2], close=arrays[3])


def bar_at(ohlc: SessionOHLC, index: int) -> Bar:
    """One bar as the `simulator.fills.Bar` the gap rule (D10) already speaks."""
    _require_bar(index, ohlc.close.size, "bar_at")
    return Bar(
        open=_finite(float(ohlc.open[index]), f"open[{index}]"),
        high=_finite(float(ohlc.high[index]), f"high[{index}]"),
        low=_finite(float(ohlc.low[index]), f"low[{index}]"),
        close=_finite(float(ohlc.close[index]), f"close[{index}]"),
    )


# -------------------------------------------------------------------- the concession


def adverse_price(price: float, side: Side, ticks: float, fut: Future, *, closing: bool = False) -> float:
    """Move `price` by `ticks` AGAINST the position, in the instrument's tick.

    Opening, a long pays up and a short sells down. CLOSING, the signs reverse: a long
    sells lower and a short buys higher. `closing` is a required distinction rather than
    an inferred one — the sign of a concession asserted in prose is what inverted D280.

    No grid check happens here: this is arithmetic, and `resolve_exit` applies the grid
    guard once, at the level where the caller has said whether the levels are on-grid.
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
    """The primary entry fill: bar t0+1, plus `ticks_adverse` ticks against the side.

    `at="close"` is the DEFAULT and is the deposit documents' convention — all three of
    `SETTLEMENT_FLOW_LEDGER_PREREG.md` §7.3, `SHOCK_CLASSIFIER_PREREG.md` §5.1 and
    `OPENING_AGENT_STATE_PREREG.md` §6.3 say "close of bar t0+1, plus 1 tick".

    `at="open"` is `run_d490_range_reversion.py`'s convention — the NEXT BAR'S OPEN plus
    one tick — and exists because the two are genuinely different assumptions about when
    the decision is made, not because one is a bug. It requires `open` to be supplied;
    it does not fall back to `close` (a fill model that quietly answers a different
    question than it was asked is the D48 failure).

    Raises when t0+1 is past the session end.
    """
    side = _check_side(side)
    closes = _as_array(close, "close")
    if at == "close":
        anchor = closes
    elif at == "open":
        if open is None:
            raise ValueError(
                "entry_fill(at='open') needs the open array; it will not substitute the "
                "close, because that is a different fill convention, not a default."
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
    """The stress entry: the WORST close among bars t0+1 … t0+k for the direction.

    Worst means highest for a long (you paid the most) and lowest for a short. Ties take
    the earliest bar, so the result does not depend on scan order.

    `ticks_adverse` carries over from the primary fill and defaults to the same one tick.
    The deposit documents define the stress fill only as the worst close, but a stress
    fill that dropped the concession could come out BETTER than the primary fill whenever
    bar t0+1 is itself the worst — which would make "stress" a misnomer on exactly the
    paths it is meant to describe. The property test pins `stress >= entry` for the side.

    Raises when t0+k is past the session end — the window is never truncated.
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
    """Resolve one bar against a stop and a target. **The stop wins whenever both are in.**

    The defaults are the deposit documents' conventions: touch on both orders, the D10
    gap rule on the stop, no slippage beyond the level, levels on the tick grid.

    The knobs exist because the runners in this repository genuinely disagree, and each
    one names a caller:

    * `stop_rule=TRADE_THROUGH, target_rule=TOUCH` is D490's mix. On a tick grid,
      trade-through is `low <= stop - tick`, which is exactly its `Ll[j] < stop`.
    * `stop_slippage_ticks=1, gap_through=False` is D490's trailing stop, which fills at
      `stop - TICK` and does not consult the open.
    * `levels_on_grid=False` is for a level computed as a fraction of a range (D490's
      target sits at 0.95 of yesterday's range and is not a tradeable price). The grid
      guard is then skipped on the way in AND on the way out, and the caller owns it.

    Raises when `high < low`, when the open or close sits outside the bar's range, or on
    an invalid side.
    """
    side = _check_side(side)
    stop_rule = _check_rule(stop_rule, "stop_rule")
    target_rule = _check_rule(target_rule, "target_rule")
    for name, value in (("open", bar.open), ("high", bar.high), ("low", bar.low), ("close", bar.close)):
        _finite(value, f"bar.{name}")
    if bar.high < bar.low:
        raise ValueError(f"resolve_exit: bar.high ({bar.high!r}) < bar.low ({bar.low!r}) is not a bar")
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
    """(price before slippage, gapped) or None when the stop was not reached."""
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
    """(fill price, gapped) or None. A limit fills at its level, or BETTER on a gap past it.

    Trade-through on a limit means the bar traded a full tick beyond it, the same
    epsilon the stop uses — not `research/terrain_strategies.py`'s absolute 1e-9.
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
    """A resting limit at the t0 close, working bars t0+1 … t0+cancel_after.

    `TOUCH` fills when the bar's range reaches the limit. `TRADE_THROUGH` — the default,
    because it is the honest one for a passive order — requires the bar to trade through
    the limit by ONE TICK, not by an absolute 1e-9.

    **The fill price is the limit, never the open.** `open` is read to validate the bars,
    and a passive order is not credited with price improvement on a gap: assuming the
    queue cleared at a better price is the optimism that makes a passive backtest look
    like an edge.

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
    """The adverse-selection comparison the shock document's §5.1 asks for.

    Outcome is the signed move from the t0 close to the t0+horizon close, in the
    position's direction, MEASURED IN TICKS. No costs and no entry concession enter it:
    the comparison is between filled and unfilled signals on the same scale, and a cost
    applied to both sides would only shift both means.

    Returns `unfilled_rate`, `mean_outcome_filled`, `mean_outcome_unfilled`, `n`, and the
    two group counts — because a mean over an empty group is `nan`, and a `nan` with no
    count beside it is unreadable.
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
        raise ValueError("passive_diagnostic: no sessions -- an unfilled RATE over nothing is not a number")
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
    """Worst drawdown from the RUNNING PEAK over a hold, in price points, pessimistically.

    For a long that is `max_j( max_{i<=j} high_i  -  low_j )`; for a short the mirror off
    the running trough. "Pessimistic" names an assumption about the unobserved intra-bar
    path: the peak includes bar j's OWN high and the trough is bar j's own low, i.e.
    high-then-low inside every bar. It OVERSTATES.

    This is the quantity a trailing drawdown on open equity measures — hurdle P1 — and is
    `scripts/d465_es_spread_and_mae_bias.py:mae_three_ways`'s pessimistic branch, which
    expresses it as a fraction of the entry price. **Only the pessimistic convention is
    implemented here**: d465 computes three in order to BRACKET the truth, which is its
    question, not this module's, and a convention no caller reads would be a D48
    affordance. Dividing this by the entry price recovers d465's number exactly.

    `fut` is read for the grid guard on the bars, which is what makes a silently
    off-grid or NaN-padded session fail here rather than three steps later.
    """
    side = _check_side(side)
    hi, lo = _as_array(high, "high"), _as_array(low, "low")
    if hi.size != lo.size:
        raise ValueError(f"high ({hi.size}) and low ({lo.size}) have different lengths")
    if not np.isfinite(hi).all() or not np.isfinite(lo).all():
        raise ValueError("running_peak_drawdown: a non-finite bar is not a path")
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
    """The ledger's hard timing constraint (§7.3, unit test 10).

    `bar_ts` is the moment the ENTRY IS COMPLETE — the close of the fill bar, not the
    close of the decision bar — and the entry is rejected unless it completes at least
    `min_minutes` before `window_start`. Raises; it does not return a flag, because a
    caller that forgets to read the flag trades the rejected signal.
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
    """A clean case is not a gate. Every audit below must also RAISE on a real break."""
    try:
        fn()
    except exc as e:
        log(f"    RAISES on {what}: {type(e).__name__}: {str(e)[:78]}")
        return
    raise AssertionError(f"audit did not raise on {what}")


def selftest(log: Any = print) -> int:
    """Every guard, once clean and once broken. Returns 0, or raises."""
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

    log("  [3] intra-bar pessimism (shock 9, ledger 11)")
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

    log("  [4] the D490 conventions reproduce")
    d490 = resolve_exit(
        Bar(open=100.00, high=100.25, low=99.50, close=99.75), stop=99.75, target=101.00, side=Side.LONG, fut=es,
        stop_rule=FillAssumption.TRADE_THROUGH, stop_slippage_ticks=1, gap_through=False,
    )
    assert d490.kind is ExitKind.STOP and d490.price == 99.50, d490
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

    log("  [7] the entry timing constraint (ledger 10)")
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
