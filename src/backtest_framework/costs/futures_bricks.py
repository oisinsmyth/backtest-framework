"""Futures cost bricks (D591): commission and tick crossing, against the D1 TradeCostBrick
interface, plus the table of measured lines they are built from.

WHY THIS EXISTS AT ALL
----------------------
`costs/equity_bricks.py` models equity friction: a per-share schedule, a square-root impact
law, a borrow rate. A futures round trip has neither shape. It is two numbers:

    commission   declared per contract by a broker, flat, and the thing that BINDS at micro
                 size — $3.00 on MES's $1.25 tick is 2.4 ticks before any spread (D469)
    crossing     measured, in TICKS, from the exchange's own quotes

and both are charged per fill on a whole number of contracts. Nothing in this package could
express that: every futures study here carried the answer as a scalar literal instead —
`COST_USD = 4.21` in one runner, `COST = {"CL": 4.00, ...}` in the next, `comm_rt/2 +
0.5*tick_usd` written inline in a third. `data/futures_costs.json` reconciles ten such
literals, from six runners, against seven committed measurements — and five of the numbers
turned out to disagree with each other. D591 lists all five.

THE DIVISION OF LABOUR, AND IT IS THE POINT
-------------------------------------------
`FuturesCommission` is DECLARED. `TickCrossing` is MEASURED. They are separate bricks rather
than one `round_trip_usd` number because a study that fails on cost needs to know which half
did it: a cheaper broker fixes one and nothing fixes the other. `FuturesRoundTrip` composes
the two and keeps the composition addressable — `.commission` and `.crossing` survive on it.

CROSSING IS IN TICKS, NOT IN BASIS POINTS
-----------------------------------------
A tick is fixed in price terms. Quoting crossing in bp would make the brick's charge depend
on the price level, which is right for an equity spread and wrong here: what an aggressor
pays on ES is one tick whether the index is at 2,000 or at 7,000, and D465's 0.364 bp is that
one tick divided by a particular median price. Holding the tick count and letting the bp
figure fall out is the direction that does not go stale. It is also what makes the micro's
problem visible, since a micro's tick is a tenth of its parent's and its commission is not.

WHAT THESE BRICKS DO NOT MODEL
------------------------------
Queue position, partial fills, the adverse selection a passive order pays, and the fact that
every crossing census on disk was measured on 2025-09..2026-09 and is applied by its callers
to 2016-2023 (D507/D508 both say so: a recent spread on an older window is OPTIMISTIC). The
table carries each line's window so the caller can see the extrapolation it is making; the
bricks themselves are arithmetic and claim nothing about the window.

Exchange and clearing fees are NOT modelled separately: every commission line in the table is
an all-in round-trip number a runner declared, and splitting it would be inventing a
decomposition no source here carries (D48).
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
"""The measured/declared cost table, built by `scripts/futures_cost_table.py --build`.

Every number in it is copied from a committed artefact or a named source literal and carries
its provenance and measurement window. Nothing in it was typed by hand.
"""


class FuturesCostError(ValueError):
    """A futures cost line was asked for and does not exist.

    Its own class so a caller can tell "this root is not in the table" from a generic
    ValueError raised inside the arithmetic. Never returns a default: a guessed cost is the
    D48 failure this whole package is written against, and it is worse here than elsewhere
    because a cost that is merely plausible still produces a Sharpe.
    """


def _require_future(instrument: Instrument, brick: str) -> Future:
    """The door guard. A futures cost brick applied to an equity is a category error, and it
    must raise rather than quietly charge a per-contract fee on a share (D48, D399)."""
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
    """Broker commission, DECLARED, charged half per fill and per contract.

    `per_round_trip_usd` is the all-in round-trip figure the runners carry ($3.00 on an index
    micro, $6.00 full-size — D468's convention). Half of it is charged on each of the two
    fills, so a position opened and closed pays exactly the declared number and a position
    held across the end of a study pays for the leg it actually did.

    PER CONTRACT, not per order. That is what makes commission the binding constraint at
    minimum tradable size: it does not shrink with the tick, and the micro's tick is a tenth
    of its parent's (D469, memory `commission-not-spread-binds-at-micro-size`).

    `price` is ignored, and declaredly so — `price_independent` below says it in a form
    `round_trip_usd` can read.
    """

    per_round_trip_usd: float

    price_independent: ClassVar[bool] = True
    """This brick's charge does not depend on the fill price. Read by `round_trip_usd`."""

    def __post_init__(self) -> None:
        if self.per_round_trip_usd < 0.0:
            raise ValueError(
                f"FuturesCommission(per_round_trip_usd={self.per_round_trip_usd!r}) is "
                "negative. A rebate is not modelled here; a negative cost would flatter every "
                "study that used it and no test downstream could see it."
            )

    def cost(self, instrument: Instrument, quantity: float, price: float) -> float:
        _require_future(instrument, "FuturesCommission")
        return 0.5 * self.per_round_trip_usd * abs(quantity)


@dataclass(frozen=True)
class TickCrossing:
    """The cost of crossing the spread, MEASURED, in ticks per round trip.

    `ticks_per_round_trip` is a full round trip's crossing — one tick on ES means paying half
    a tick in and half a tick out, which is what the censuses report and what D555's
    `dollar_book` charges as `0.5 * tick_usd` a side. Half is charged per fill, so the two
    fills sum to `ticks_per_round_trip * tick_usd` exactly (0.5 is a power of two; halving and
    re-doubling a double is lossless).

    The dollar value comes from the INSTRUMENT's tick, never from a literal here: the same
    1.0085687251930602 ticks is $12.61 on ES and $1.26 on MES, and that ratio is the whole
    micro-size argument.
    """

    ticks_per_round_trip: float

    price_independent: ClassVar[bool] = True
    """A tick is fixed in price terms, so this brick's charge does not depend on the fill
    price. That is the difference between it and `PercentOfNotionalSpread`, and the reason
    the table stores ticks rather than basis points."""

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
    """One instrument's whole trade-cost line: commission plus crossing, addressable apart.

    It satisfies `TradeCostBrick` itself, so a stack takes one entry rather than two — but
    `.commission` and `.crossing` survive on it, because "this failed on cost" is not a
    finding until you can say which half did it (CLAUDE.md: *cost-cutting ≠ edge-sharpening*).

    `.line`, `.window` and `.size` are the provenance of the crossing figure, carried on the
    object rather than left in the table, so a report can name the measurement it charged
    without re-opening the file.
    """

    commission: FuturesCommission
    crossing: TickCrossing
    instrument: Future | None = None
    """The contract this line was resolved FOR, when it came from the table.

    Optional, and it is not a false affordance: `cost()` never reads it — a brick is handed
    its instrument by the caller at fill time, which is what lets one declarative config serve
    a book of several roots. It is carried so a report can say which contract's tick the line
    was chosen on, and `round_trip_usd` RAISES rather than guessing when it is absent.
    """
    root: str = ""
    """The PARENT root the table entry hangs under ("ES" for MES). Empty when hand-built."""
    size: str = ""
    """"micro" or "full" — which entry of `root` this is. Empty when hand-built."""
    line: str = ""
    """Which crossing line the tick count came from ("d508_exec", "d556_one_tick", ...)."""
    window: tuple[str, ...] = ()
    """The crossing measurement's own window, as (start, end) ISO dates. Empty for a rule
    (the one-tick convention measured nothing and has no window to quote)."""

    price_independent: ClassVar[bool] = True

    @property
    def bricks(self) -> tuple[FuturesCommission, TickCrossing]:
        """The two bricks, in the order they are charged. Summing is order-free (costs/stack.py
        asserts that), but a stable order keeps a golden ledger's arithmetic reproducible."""
        return (self.commission, self.crossing)

    def cost(self, instrument: Instrument, quantity: float, price: float) -> float:
        return sum(brick.cost(instrument, quantity, price) for brick in self.bricks)

    @property
    def round_trip_usd(self) -> float:
        """Two fills of one contract of `self.instrument`, in dollars."""
        if self.instrument is None:
            raise FuturesCostError(
                "this FuturesRoundTrip carries no instrument, so it has no round-trip dollar "
                "figure of its own — crossing is priced by the tick of whichever contract is "
                "being filled. Call round_trip_usd(instrument, line.bricks) with the contract."
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
        """Compose the two bricks from `data/futures_costs.json`.

        `root` is the parent root ("ES") or the traded symbol ("MES"); a symbol resolves its
        own size and `size` must then agree if it is given at all. `size` is "micro" or
        "full" and defaults to the entry's own minimum tradable size, which is the size
        `COMPONENTS_PROP.md` scores a component at. `line` names the crossing measurement and
        defaults to the entry's `default_line`.

        Everything raises rather than defaulting: an unknown root, an unknown size, a size the
        root does not list, an unknown line, and a line that root was never measured on.
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
                f"contract: {known_here}. Lines the table defines at all: {known_any}. A "
                "missing measurement must be a loud error, not another root's number."
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
    """What one contract's round trip costs: an entry fill plus an exit fill.

    `price` may be omitted ONLY when every brick declares `price_independent = True`. It is
    not defaulted to zero: a zero price would silently zero a `PercentOfNotionalSpread` and
    return a number that looks like an answer, which is the exact D48 failure this package
    keeps finding. A brick that reads the price and is handed no price RAISES and names
    itself.

    Summed the way `CostStack.trade_cost` sums — per fill over the bricks, then the two fills
    — so a stack over the same bricks returns the identical double. `tests/unit/
    test_futures_bricks.py` quantifies over that rather than asserting it once.
    """
    bricks = tuple(bricks)
    if price is None:
        reads_price = [b for b in bricks if not getattr(b, "price_independent", False)]
        if reads_price:
            names = ", ".join(sorted(type(b).__name__ for b in reads_price))
            raise FuturesCostError(
                f"round_trip_usd was given no price, but {names} does not declare "
                "price_independent. Defaulting the price to 0.0 would silently zero that "
                "brick's charge; pass the price level the round trip happens at."
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
            f"{path} is missing. Build it with `uv run python scripts/futures_cost_table.py "
            "--build`; the bricks do not fall back to a hardcoded cost line (D48)."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "roots" not in data or "lines" not in data:
        raise FuturesCostError(f"{path} is not a futures cost table (no 'roots'/'lines' key)")
    return data


def load_cost_table(path: Path | None = None) -> dict[str, Any]:
    """The parsed cost table. Cached per path, so the file is read once per process."""
    return _load_table(path or TABLE_PATH)


def _resolve_symbol(table: dict[str, Any], root: str, size: str | None) -> tuple[str, str]:
    """(parent root, size) for a parent root or a traded symbol, raising on anything else."""
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
            f"root's traded symbols). A missing cost line must be a loud error, not a guess."
        )

    if size_key not in roots[root_key]:
        available = ", ".join(s for s in ("micro", "full") if s in roots[root_key])
        raise FuturesCostError(
            f"{root_key} has no {size_key!r} entry — it lists: {available}. "
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

    For looking at the spread of the estimates before picking one — which is the habit
    `docs/FINDINGS.md` asks for and which the default line hides by construction.
    """
    table = load_cost_table(table_path)
    root_key, size_key = _resolve_symbol(table, root, size)
    entry = table["roots"][root_key][size_key]
    return {name: float(v["value"]) for name, v in entry["crossing_ticks_rt"].items()}


def build_trade_bricks(
    root: str, size: str | None = None, line: str | None = None, *, table_path: Path | None = None
) -> tuple[FuturesCommission, TickCrossing]:
    """The two bricks for one contract, ready for `CostStack(trade_bricks=...)`."""
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
