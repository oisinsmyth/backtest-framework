"""Futures cost bricks (commission and tick crossing) for the TradeCostBrick interface,
and the cost table they are built from.

A futures round trip costs two amounts, both charged per fill on whole contracts:

    commission   declared per contract by the broker, flat; the binding cost at micro
                 size ($3.00 on MES's $1.25 tick is 2.4 ticks before any spread)
    crossing     measured in ticks from the exchange's quotes

`data/futures_costs.json` holds both per root and size. They are separate bricks so a cost
failure can be attributed to one or the other (a cheaper broker changes only the
commission); `FuturesRoundTrip` combines them as `.commission` and `.crossing`.

Crossing is stored in ticks rather than basis points because a tick is fixed in price
terms: an aggressor pays one tick on ES at an index level of 2,000 or 7,000, and a figure
such as 0.364 bp is that tick divided by one particular median price. A micro's tick is a
tenth of its parent's while its commission is not.

Not modelled: queue position, partial fills, adverse selection on passive orders, and the
age of the spread measurements. The crossing figures were measured on 2025-09..2026-09, so
applying them to an older window is optimistic; the table records each line's window and
the bricks do not check it. Exchange and clearing fees are not split out: every commission
line is an all-in round-trip figure.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, ClassVar, Iterable, Sequence

from ..instruments.base import Instrument
from ..instruments.future import Future

REPO = Path(__file__).resolve().parents[3]

TABLE_PATH = REPO / "data" / "futures_costs.json"
"""The futures cost table; every number carries its provenance and measurement window."""


class FuturesCostError(ValueError):
    """Raised when a requested futures cost line does not exist.

    A separate class so a caller can distinguish a missing table entry from a ValueError
    raised in the arithmetic. Lookups never fall back to a default value.
    """


def _require_future(instrument: Instrument, brick: str) -> Future:
    """Return `instrument` if it is a Future; raise TypeError otherwise."""
    if not isinstance(instrument, Future):
        raise TypeError(
            f"{brick} charges per CONTRACT and needs a Future, but got "
            f"{type(instrument).__name__}"
            + (f" ({instrument.symbol!r})" if hasattr(instrument, "symbol") else "")
            + ". Commission and tick crossing are not defined for an instrument with no tick "
            "and no contract multiplier; use costs/equity_bricks.py for equities."
        )
    return instrument


@dataclass(frozen=True)
class FuturesCommission:
    """Declared broker commission, charged per contract, half on each fill.

    `per_round_trip_usd` is the all-in round-trip figure ($3.00 on an index micro, $6.00
    full-size in the cost table). A position opened and closed pays the full figure; a
    position still open at the end of a study pays for the one fill it made.

    The charge is per contract, not per order, and does not shrink with the tick, which is
    why it binds at micro size. `price` is ignored.
    """

    per_round_trip_usd: float

    price_independent: ClassVar[bool] = True
    """The charge does not depend on the fill price. Read by `round_trip_usd`."""

    def __post_init__(self) -> None:
        if self.per_round_trip_usd < 0.0:
            raise ValueError(
                f"FuturesCommission(per_round_trip_usd={self.per_round_trip_usd!r}) is "
                "negative. Rebates are not modelled."
            )

    def cost(self, instrument: Instrument, quantity: float, price: float) -> float:
        _require_future(instrument, "FuturesCommission")
        return 0.5 * self.per_round_trip_usd * abs(quantity)


@dataclass(frozen=True)
class TickCrossing:
    """Measured cost of crossing the spread, in ticks per round trip.

    One tick round trip on ES means half a tick in and half a tick out, `0.5 * tick_usd` a
    side. The two fills sum to `ticks_per_round_trip * tick_usd` exactly (halving by 0.5 is
    lossless in binary floating point).

    Dollars come from the instrument's tick: 1.0085687251930602 ticks is $12.61 on ES and
    $1.26 on MES.
    """

    ticks_per_round_trip: float

    price_independent: ClassVar[bool] = True
    """A tick is fixed in price terms, so the charge does not depend on the fill price
    (unlike `PercentOfNotionalSpread`)."""

    def __post_init__(self) -> None:
        if self.ticks_per_round_trip < 0.0:
            raise ValueError(
                f"TickCrossing(ticks_per_round_trip={self.ticks_per_round_trip!r}) is "
                "negative. Crossing the spread cannot pay."
            )

    def cost(self, instrument: Instrument, quantity: float, price: float) -> float:
        future = _require_future(instrument, "TickCrossing")
        return 0.5 * self.ticks_per_round_trip * future.tick_usd * abs(quantity)


@dataclass(frozen=True)
class FuturesRoundTrip:
    """One instrument's trade-cost line: commission plus crossing.

    A `TradeCostBrick` itself, so a stack takes one entry; `.commission` and `.crossing`
    remain accessible separately. `.line`, `.window` and `.size` record which measurement
    the crossing figure came from.
    """

    commission: FuturesCommission
    crossing: TickCrossing
    instrument: Future | None = None
    """The contract this line was resolved for, when built from the table.

    `cost()` does not read it; the caller passes the instrument at fill time, so one config
    can serve several roots. It records which contract's tick the line was chosen on, and
    the `round_trip_usd` property raises when it is None.
    """
    root: str = ""
    """The parent root of the table entry ("ES" for MES). Empty when hand-built."""
    size: str = ""
    """"micro" or "full": which entry of `root` this is. Empty when hand-built."""
    line: str = ""
    """The crossing line the tick count came from ("effective_exec_hours", "one_tick", ...)."""
    window: tuple[str, ...] = ()
    """The crossing measurement window as (start, end) ISO dates. Empty for a convention
    such as `one_tick`, which was not measured."""

    price_independent: ClassVar[bool] = True

    @property
    def bricks(self) -> tuple[FuturesCommission, TickCrossing]:
        """The two bricks in charging order, fixed so the golden tests are reproducible."""
        return (self.commission, self.crossing)

    def cost(self, instrument: Instrument, quantity: float, price: float) -> float:
        return sum(brick.cost(instrument, quantity, price) for brick in self.bricks)

    @property
    def round_trip_usd(self) -> float:
        """Cost in dollars of two fills of one contract of `self.instrument`."""
        if self.instrument is None:
            raise FuturesCostError(
                "this FuturesRoundTrip carries no instrument, so it has no round-trip dollar "
                "figure of its own; crossing is priced by the tick of the contract being filled. "
                "Call round_trip_usd(instrument, line.bricks) with the contract."
            )
        return round_trip_usd(self.instrument, self.bricks)

    @classmethod
    def from_table(
        cls,
        root: str,
        size: str | None = None,
        line: str | None = None,
        *,
        table_path: Path | None = None,
    ) -> FuturesRoundTrip:
        """Build the line from `data/futures_costs.json`.

        `root` is a parent root ("ES") or a traded symbol ("MES"); a symbol implies its size,
        and `size`, if given, must agree. `size` is "micro" or "full" and defaults to the
        root's minimum tradable size. `line` names the crossing measurement and defaults to
        the entry's `default_line`.

        Raises `FuturesCostError` on an unknown root or size, a size the root does not list,
        or a line not measured on that contract.
        """
        table = load_cost_table(table_path)
        root_key, size_key = _resolve_symbol(table, root, size)
        entry = table["roots"][root_key][size_key]

        line_key = line if line is not None else entry["default_line"]
        crossing = entry["crossing_ticks_rt"]
        if line_key not in crossing:
            known_here = ", ".join(sorted(crossing)) or "(none)"
            known_any = ", ".join(sorted(table["lines"]))
            raise FuturesCostError(
                f"{entry['symbol']} has no crossing line {line_key!r}. Lines measured on this "
                f"contract: {known_here}. Lines the table defines at all: {known_any}."
            )

        instrument = Future(
            root=entry["symbol"],
            tick_points=float(entry["tick_points"]),
            usd_per_point=float(entry["usd_per_point"]),
            tick_usd=float(entry["tick_usd"]),
        )
        return cls(
            instrument=instrument,
            commission=FuturesCommission(float(entry["commission_rt_usd"]["value"])),
            crossing=TickCrossing(float(crossing[line_key]["value"])),
            root=root_key,
            size=size_key,
            line=line_key,
            window=tuple(crossing[line_key].get("window") or ()),
        )


def round_trip_usd(
    instrument: Instrument,
    bricks: Iterable[Any],
    price: float | None = None,
) -> float:
    """Cost of one contract's round trip: an entry fill plus an exit fill.

    `price` may be omitted only when every brick declares `price_independent = True`;
    otherwise this raises and names the bricks that read the price.

    Summed as `CostStack.trade_cost` sums (over bricks per fill, then the two fills), so a
    stack over the same bricks returns the identical double
    (`tests/unit/test_futures_bricks.py`).
    """
    bricks = tuple(bricks)
    if price is None:
        reads_price = [b for b in bricks if not getattr(b, "price_independent", False)]
        if reads_price:
            names = ", ".join(sorted(type(b).__name__ for b in reads_price))
            raise FuturesCostError(
                f"round_trip_usd was given no price, but {names} does not declare "
                "price_independent. Pass the price level of the round trip."
            )
        price = 0.0
    entry = sum(brick.cost(instrument, 1.0, price) for brick in bricks)
    exit_ = sum(brick.cost(instrument, -1.0, price) for brick in bricks)
    return entry + exit_


# --------------------------------------------------------------------------- the table


@lru_cache(maxsize=2)
def _load_table(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FuturesCostError(
            f"{path} is missing. The futures cost bricks read their cost lines from this table "
            "and do not fall back to a hardcoded cost line."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "roots" not in data or "lines" not in data:
        raise FuturesCostError(f"{path} is not a futures cost table (no 'roots'/'lines' key)")
    return data


def load_cost_table(path: Path | None = None) -> dict[str, Any]:
    """Return the parsed cost table, cached per path (read once per process)."""
    return _load_table(path or TABLE_PATH)


def _resolve_symbol(table: dict[str, Any], root: str, size: str | None) -> tuple[str, str]:
    """Return (parent root, size) for a parent root or traded symbol; raise otherwise."""
    roots = table["roots"]
    if root in roots:
        root_key = root
        size_key = size if size is not None else roots[root]["min_size"]
    elif root in table["by_symbol"]:
        root_key, resolved = table["by_symbol"][root]
        if size is not None and size != resolved:
            raise FuturesCostError(
                f"{root!r} is the {resolved} entry of {root_key}, but size={size!r} was asked "
                f"for. Pass the parent root {root_key!r} to choose a size."
            )
        size_key = resolved
    else:
        known = ", ".join(sorted(roots))
        raise FuturesCostError(
            f"no futures cost line for {root!r}. The table carries roots: {known} (and each "
            f"root's traded symbols)."
        )

    if size_key not in roots[root_key]:
        available = ", ".join(s for s in ("micro", "full") if s in roots[root_key])
        raise FuturesCostError(
            f"{root_key} has no {size_key!r} entry; it lists: {available}. "
            f"{roots[root_key].get('no_micro_because', '')}".strip()
        )
    return root_key, size_key


def table_roots(path: Path | None = None) -> tuple[str, ...]:
    """Every parent root the table carries, sorted."""
    return tuple(sorted(load_cost_table(path)["roots"]))


def line_names(path: Path | None = None) -> tuple[str, ...]:
    """Every crossing line the table defines, sorted. Not every line covers every root."""
    return tuple(sorted(load_cost_table(path)["lines"]))


def crossing_lines_for(
    root: str, size: str | None = None, *, table_path: Path | None = None
) -> dict[str, float]:
    """Every crossing line measured on one contract, as {line name: ticks per round trip}.

    Shows the range of estimates behind the default line.
    """
    table = load_cost_table(table_path)
    root_key, size_key = _resolve_symbol(table, root, size)
    entry = table["roots"][root_key][size_key]
    return {name: float(v["value"]) for name, v in entry["crossing_ticks_rt"].items()}


def build_trade_bricks(
    root: str, size: str | None = None, line: str | None = None, *, table_path: Path | None = None
) -> tuple[FuturesCommission, TickCrossing]:
    """Return the two bricks for one contract, for `CostStack(trade_bricks=...)`."""
    return FuturesRoundTrip.from_table(root, size, line, table_path=table_path).bricks


__all__: Sequence[str] = (
    "FuturesCommission",
    "FuturesCostError",
    "FuturesRoundTrip",
    "TickCrossing",
    "TABLE_PATH",
    "build_trade_bricks",
    "crossing_lines_for",
    "line_names",
    "load_cost_table",
    "round_trip_usd",
    "table_roots",
)
