"""Track 3 logging (D605) — the per-trade fill log, implementation shortfall, signal-to-fill
latency, the 50-trade cost review and the trial counter with futility looks.

THE SPEC, QUOTED VERBATIM. `docs/internal/User-Doc-Deposit/SETTLEMENT_FLOW_LEDGER_PREREG.md`
§13A.5 *"Track 3: paper / live-small trading"*, lines 853-860:

    ### 13A.5 Track 3: paper / live-small trading

    - **Preferred mode:** live-small (1 micro contract, real account), because real fills are
      the point. **Fallback:** paper or prop-evaluation simulator, with its fills flagged as
      simulated (decision D24).
    - **Log per trade:** signal time, model-intended fill price (per Section 7.3), order sent
      time, fill time, actual fill price, exit details.
    - **Implementation shortfall** = actual fill − model fill, in ticks, signed against the
      trade.
    - **Latency check:** the distribution of signal-to-fill time must be consistent with the
      t0+1 … t0+5 assumption. Report the share of fills beyond t0+5.
    - **Cost review after 50 trades:** if the mean shortfall exceeds the CostStack slippage
      assumption by more than 50%, update CostStack via doc edit and **re-run all Track 1
      results at the new cost** before continuing.
    - Track 3 starts with the Stage A signal (or A-lite) and is upgraded to the best retained
      stage only at pre-set checkpoints, with each upgrade restarting the trading count (13A.4).

and §13A.4, lines 847-851:

    - **Target sample:** N = 300 trades (both instruments combined).
    - **Futility looks** at N = 100 and N = 200: stop if the mean net return per trade < 0
      **and** t < −1.
    - **Efficacy decision only at N = 300:** mean net > 0 with t ≥ 2. Also report the DSR
      combining the backtest trial count and the forward test.
    - No parameter or rule changes during the forward test. Any change restarts the count at
      N = 0 under a new frozen file.

NOTHING HERE TRADES, AND NOTHING HERE IS A RESULT
--------------------------------------------------
No broker adapter, no scheduler, no order router, no order is sent. This module reads a log
somebody else wrote and computes four things from it. **No real fill exists yet**: every
number in the tests is synthetic and hand-typed, `data/track3/` holds the schema and no trade
file, and the shortfall of an empty log is not zero — it RAISES.

THE SIGN CONVENTION IS D364's, INHERITED RATHER THAN REINVENTED
----------------------------------------------------------------
`scripts/d364_slippage.py` is the only fill-log schema this repository had, and its rule is

    POSITIVE = THE FILL WAS WORSE FOR THE STRATEGY

with `SIDE_SIGN = {"short_entry": -1.0, "cover_exit": +1.0}`. Generalised to both directions:

    entry:  shortfall_ticks = +side_sign * (fill_px - model_fill_px) / tick_points
    exit:   shortfall_ticks = -side_sign * (exit_fill_px - model_exit_px) / tick_points

`side_sign` is +1 long, −1 short. The exit sign is inverted because an exit is the opposite
trade — a long's exit sells, so a LOWER fill is worse. On d364's two cases (a short entry and
a cover exit) the general rule reproduces its two literals exactly. Ledger unit test 35 is
asserted on both signs in money, because a sign asserted in prose inverted D280.

WHAT THE SCHEMA CANNOT DO, STATED RATHER THAN PAPERED OVER
-----------------------------------------------------------
The deposit's log list names ONE model price — the entry's, "per Section 7.3" — and calls the
rest "exit details". So there is no `model_exit_px` column, and `exit_shortfall_ticks` takes
the model exit price as an ARGUMENT. An exit shortfall is therefore not computable from the
log alone. That is a gap in the deposit; it is recorded in D605 rather than filled by
inventing a column the pre-registration does not have.

"THE CostStack SLIPPAGE ASSUMPTION" IS ALSO UNDEFINED IN THE DEPOSIT
---------------------------------------------------------------------
§13A.5 compares the mean shortfall to it and never says what it is. `cost_assumption_ticks`
declares it, per fill and in ticks:

    assumption = crossing_ticks_per_round_trip / 2 + ADVERSE_TICKS_PER_ENTRY

the first term being what D591's `TickCrossing` charges for ONE fill (it charges half a round
trip per fill) and the second being §7.3's *"plus 1 tick of adverse slippage"* on the primary
entry fill. Both halves are read from `data/futures_costs.json` and from §7.3 respectively;
neither is a literal chosen here.

REUSED, NEVER RETYPED
----------------------
`instruments/future.Future` for the tick grid; `costs/futures_bricks.FuturesRoundTrip.from_table`
for the measured crossing; `validation/frozen.assert_frozen` for §13A.4's restart rule;
`validation/power.track3_route` for §13A.7(4)'s route. `simulator/futures_fills.entry_fill`
produces the §7.3 model-intended price that a caller writes into `model_fill_px` — this module
does not recompute it, because a model price recomputed after the fill measures the
recomputation and not the slippage.

Every guard RAISES (D48) and every raise is exercised by `scripts/track3_report.py --selftest`.
"""

from __future__ import annotations

import csv
import datetime as dt
import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from backtest_framework.costs.futures_bricks import FuturesRoundTrip
from backtest_framework.instruments.future import Future
from backtest_framework.validation.frozen import FrozenDriftError, assert_frozen
from backtest_framework.validation.power import TRACK3_TARGET_N, Track3Route, track3_route

__all__ = [
    "ADVERSE_TICKS_PER_ENTRY",
    "COST_REVIEW_ACTION",
    "COST_REVIEW_N",
    "EXCEEDS_RATIO",
    "FIELDS",
    "LATENCY_ASSUMED_MAX_BARS",
    "SIDE_SIGN",
    "CostReview",
    "Restart",
    "Track3Error",
    "Track3LogError",
    "TradeLog",
    "TradeRow",
    "TrialCounter",
    "cost_assumption_ticks",
    "cost_review",
    "exit_shortfall_ticks",
    "exit_shortfall_usd",
    "latency_bars",
    "latency_report",
    "quantile_nearest_rank",
    "shortfall_ticks",
    "shortfall_usd",
]


class Track3Error(Exception):
    """Base for everything this module refuses to do."""


class Track3LogError(Track3Error):
    """A malformed log. The message names the file, the line and the field."""


SideName = Literal["long", "short"]

SIDE_SIGN: dict[str, float] = {"long": 1.0, "short": -1.0}
"""+1 long, −1 short. The multiplier that makes a shortfall POSITIVE when the fill was worse
for the strategy — `scripts/d364_slippage.py`'s convention, generalised to both directions."""

ADVERSE_TICKS_PER_ENTRY = 1.0
"""Ledger §7.3: *"close of bar t0+1, plus 1 tick of adverse slippage (on top of CostStack)"*."""

LATENCY_ASSUMED_MAX_BARS = 5.0
"""§13A.5's *"t0+1 … t0+5 assumption"*: the share of fills beyond t0+5 is the reported number."""

COST_REVIEW_N = 50
"""§13A.5: *"Cost review after 50 trades"*."""

EXCEEDS_RATIO = 1.5
"""§13A.5: *"exceeds the CostStack slippage assumption by more than 50%"* — strictly greater."""

COST_REVIEW_ACTION = (
    "update CostStack via doc edit and re-run all Track 1 results at the new cost before "
    "continuing (SETTLEMENT_FLOW_LEDGER_PREREG.md section 13A.5). THIS IS A FLAG: nothing in "
    "track3.py edits a cost table, a config or a doc."
)

FIELDS: tuple[str, ...] = (
    "trade_id",
    "model",
    "stage",
    "frozen_sha256",
    "root",
    "size_label",
    "side",
    "qty",
    "signal_ts",
    "model_fill_px",
    "order_sent_ts",
    "fill_ts",
    "fill_px",
    "exit_signal_ts",
    "exit_fill_ts",
    "exit_fill_px",
    "simulated",
    "venue",
    "note",
)
"""The CSV column order, which is also the `TradeRow` field order. §13A.5's six logged items
are `signal_ts`, `model_fill_px`, `order_sent_ts`, `fill_ts`, `fill_px` and the exit triple."""

_REQUIRED_TEXT = ("trade_id", "model", "stage", "frozen_sha256", "root", "size_label", "venue")
_EXIT_FIELDS = ("exit_signal_ts", "exit_fill_ts", "exit_fill_px")


# --------------------------------------------------------------------------- the row


def _finite(value: float, what: str) -> float:
    x = float(value)
    if not math.isfinite(x):
        raise Track3Error(f"{what} must be a finite number, got {value!r}")
    return x


def _aware(ts: dt.datetime) -> bool:
    return ts.tzinfo is not None and ts.tzinfo.utcoffset(ts) is not None


@dataclass(frozen=True)
class TradeRow:
    """One Track 3 trade, exactly as §13A.5 says to log it.

    Units: prices in the instrument's QUOTED points (5000.25 index points on MES, never
    ticks and never dollars); `qty` in whole contracts; every `_ts` a `datetime.datetime`.

    `simulated` is decision D24's flag — True for a paper or prop-evaluation fill, False for
    a real one. It is not optional and has no default: the deposit prefers live-small
    *"because real fills are the point"*, and a log that forgets to say which kind of fill it
    holds has thrown away the one distinction Track 3 exists to make.

    A row is validated on construction for everything that is a property of the ROW — finite
    prices, a positive whole `qty`, a known side, a complete-or-absent exit triple and
    timestamps that are all naive or all aware. **Ordering is NOT checked here**, because
    `TradeLog.append` is where a badly ordered row is refused and a guard that cannot be fed
    a broken case cannot be shown to fire.
    """

    trade_id: str
    model: str
    stage: str
    frozen_sha256: str
    root: str
    size_label: str
    side: SideName
    qty: int
    signal_ts: dt.datetime
    model_fill_px: float
    order_sent_ts: dt.datetime
    fill_ts: dt.datetime
    fill_px: float
    exit_signal_ts: dt.datetime | None = None
    exit_fill_ts: dt.datetime | None = None
    exit_fill_px: float | None = None
    simulated: bool = False
    venue: str = ""
    note: str = ""

    def __post_init__(self) -> None:
        for name in _REQUIRED_TEXT:
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise Track3Error(f"TradeRow.{name} must be a non-empty string, got {value!r}")
        if self.side not in SIDE_SIGN:
            raise Track3Error(
                f"TradeRow.side must be 'long' or 'short', got {self.side!r}. A side inferred "
                "from the sign of a quantity is the D280 failure."
            )
        if not isinstance(self.qty, int) or isinstance(self.qty, bool) or self.qty <= 0:
            raise Track3Error(
                f"TradeRow.qty must be a positive whole number of contracts, got {self.qty!r}; "
                "direction lives in `side`, never in the sign of the quantity."
            )
        if not isinstance(self.simulated, bool):
            raise Track3Error(
                f"TradeRow.simulated must be a bool (D24 flags a simulated fill), got "
                f"{self.simulated!r}"
            )
        _finite(self.model_fill_px, "TradeRow.model_fill_px")
        _finite(self.fill_px, "TradeRow.fill_px")

        stamps: list[tuple[str, dt.datetime]] = []
        for name in ("signal_ts", "order_sent_ts", "fill_ts"):
            value = getattr(self, name)
            if not isinstance(value, dt.datetime):
                raise Track3Error(f"TradeRow.{name} must be a datetime, got {value!r}")
            stamps.append((name, value))

        present = [n for n in _EXIT_FIELDS if getattr(self, n) is not None]
        if present and len(present) != len(_EXIT_FIELDS):
            missing = [n for n in _EXIT_FIELDS if getattr(self, n) is None]
            raise Track3Error(
                f"TradeRow {self.trade_id!r}: the exit is half-recorded -- present {present}, "
                f"missing {missing}. An exit is all three fields or none; a trade with a fill "
                "time and no fill price is not an exit, it is a lost one."
            )
        if present:
            for name in ("exit_signal_ts", "exit_fill_ts"):
                value = getattr(self, name)
                if not isinstance(value, dt.datetime):
                    raise Track3Error(f"TradeRow.{name} must be a datetime, got {value!r}")
                stamps.append((name, value))
            exit_px = self.exit_fill_px
            if exit_px is None:  # pragma: no cover - the completeness check above forbids it
                raise Track3Error("TradeRow.exit_fill_px is absent on a closed trade")
            _finite(exit_px, "TradeRow.exit_fill_px")

        awareness = {name: _aware(ts) for name, ts in stamps}
        if len(set(awareness.values())) > 1:
            aware = sorted(n for n, a in awareness.items() if a)
            naive = sorted(n for n, a in awareness.items() if not a)
            raise Track3Error(
                f"TradeRow {self.trade_id!r} mixes aware and naive timestamps: aware {aware}, "
                f"naive {naive}. Subtracting them raises a bare TypeError three functions "
                "later; it is refused here, where the row is."
            )

    # -- the three orderings, checked by the log rather than by the row ------------

    def ordering_fault(self) -> str | None:
        """The FIRST ordering violation, or None. Never raises; `TradeLog.append` does.

        Three orderings, in the order they are read: the deposit's two (§13A.5's four
        timestamps run signal → order sent → fill) and, for a closed trade, the exit pair
        after the entry fill. The third is an ADDITION of this module and is named as one in
        D605 — the deposit says only "exit details".
        """
        if self.order_sent_ts < self.signal_ts:
            return (
                f"order_sent_ts {self.order_sent_ts.isoformat()} precedes signal_ts "
                f"{self.signal_ts.isoformat()}: the order was sent before the signal existed"
            )
        if self.fill_ts < self.order_sent_ts:
            return (
                f"fill_ts {self.fill_ts.isoformat()} precedes order_sent_ts "
                f"{self.order_sent_ts.isoformat()}: filled before the order was sent"
            )
        if self.exit_signal_ts is not None and self.exit_fill_ts is not None:
            if self.exit_signal_ts < self.fill_ts:
                return (
                    f"exit_signal_ts {self.exit_signal_ts.isoformat()} precedes the entry "
                    f"fill_ts {self.fill_ts.isoformat()}: exited a position not yet held"
                )
            if self.exit_fill_ts < self.exit_signal_ts:
                return (
                    f"exit_fill_ts {self.exit_fill_ts.isoformat()} precedes exit_signal_ts "
                    f"{self.exit_signal_ts.isoformat()}"
                )
        return None

    @property
    def side_sign(self) -> float:
        return SIDE_SIGN[self.side]

    @property
    def is_closed(self) -> bool:
        return self.exit_fill_px is not None

    def to_cells(self) -> list[str]:
        """The CSV cells, in `FIELDS` order. Floats through `repr`, so a round trip is exact."""
        out: list[str] = []
        for name in FIELDS:
            value = getattr(self, name)
            if value is None:
                out.append("")
            elif isinstance(value, dt.datetime):
                out.append(value.isoformat())
            elif isinstance(value, bool):
                out.append("True" if value else "False")
            elif isinstance(value, float):
                # float() first: repr(np.float64(1.0)) is "np.float64(1.0)" under numpy >= 2,
                # which reads back as garbage. The same defect D590 fixed in component_series.
                out.append(repr(float(value)))
            elif isinstance(value, int):
                out.append(str(int(value)))
            else:
                out.append(str(value))
        return out


# --------------------------------------------------------------------------- the log


def _cell_error(path: Path, line: int, name: str, cell: str, why: str) -> Track3LogError:
    return Track3LogError(f"{path.name} line {line}: {name}={cell!r} {why}")


def _parse_ts(path: Path, line: int, name: str, cell: str) -> dt.datetime:
    try:
        return dt.datetime.fromisoformat(cell)
    except ValueError as exc:
        raise _cell_error(path, line, name, cell, f"is not an ISO-8601 datetime ({exc})") from exc


def _parse_float(path: Path, line: int, name: str, cell: str) -> float:
    try:
        x = float(cell)
    except ValueError as exc:
        raise _cell_error(path, line, name, cell, "is not a number") from exc
    if not math.isfinite(x):
        raise _cell_error(path, line, name, cell, "is not finite")
    return x


@dataclass(frozen=True)
class TradeLog:
    """An append-only CSV of `TradeRow`s. LF newlines on every platform (D550).

    The header is written once, when the file does not exist. `append` refuses a duplicate
    `trade_id` and any ordering fault; `read` is typed and strict in the manner of
    `scripts/d364_slippage.py:read_log` — *"a fill log that half-parses is worse than one that
    refuses"* — except that it raises `Track3LogError` rather than `SystemExit`, because
    library code that kills the interpreter cannot be tested for the message it raised.

    Append-only is enforced by never opening the file in "w" mode after creation. It is not
    enforced against an editor, and nothing here pretends otherwise: the tamper-evidence a
    Track 3 log actually needs is `frozen_sha256` on every row, not a file mode.
    """

    path: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", Path(self.path))

    # -- writing ------------------------------------------------------------------

    def _write_header_if_new(self) -> None:
        if self.path.exists():
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8", newline="\n") as fh:
            csv.writer(fh, lineterminator="\n").writerow(FIELDS)

    def append(self, row: TradeRow) -> TradeRow:
        """Add one trade. Raises on a duplicate id or an out-of-order timestamp."""
        if not isinstance(row, TradeRow):
            raise Track3Error(f"TradeLog.append takes a TradeRow, got {type(row).__name__}")
        fault = row.ordering_fault()
        if fault is not None:
            raise Track3Error(f"TradeLog.append refuses trade {row.trade_id!r}: {fault}")
        if self.path.exists():
            seen = {r.trade_id for r in self.read()}
            if row.trade_id in seen:
                raise Track3Error(
                    f"TradeLog.append refuses trade {row.trade_id!r}: already in "
                    f"{self.path.name}. A trade counted twice moves the mean, the t and the "
                    "futility verdict; the log is append-only, not idempotent."
                )
        self._write_header_if_new()
        with open(self.path, "a", encoding="utf-8", newline="\n") as fh:
            csv.writer(fh, lineterminator="\n").writerow(row.to_cells())
        return row

    # -- reading ------------------------------------------------------------------

    def read(self) -> list[TradeRow]:
        """Every row, typed. Raises naming the line and the field on anything malformed."""
        if not self.path.exists():
            raise Track3LogError(
                f"no such log: {self.path}. Track 3 has recorded no trade; an absent log is "
                "not an empty one and does not read as zero trades."
            )
        with open(self.path, encoding="utf-8", newline="") as fh:
            rows = list(csv.reader(fh))
        if not rows:
            raise Track3LogError(f"{self.path.name} is empty; it must carry the header row")
        head = tuple(c.strip() for c in rows[0])
        if head != FIELDS:
            raise Track3LogError(
                f"{self.path.name}: header is\n  {list(head)}\nexpected\n  {list(FIELDS)}"
            )
        out: list[TradeRow] = []
        for line, cells in enumerate(rows[1:], start=2):
            if not any(c.strip() for c in cells):
                continue
            out.append(self._row_from_cells(line, cells))
        return out

    def _row_from_cells(self, line: int, cells: Sequence[str]) -> TradeRow:
        path = self.path
        if len(cells) != len(FIELDS):
            raise Track3LogError(
                f"{path.name} line {line}: {len(cells)} fields, expected {len(FIELDS)}"
            )
        raw = {name: cell.strip() for name, cell in zip(FIELDS, cells, strict=True)}

        for name in _REQUIRED_TEXT + ("side", "qty", "signal_ts", "model_fill_px",
                                      "order_sent_ts", "fill_ts", "fill_px", "simulated"):
            if raw[name] == "":
                raise Track3LogError(f"{path.name} line {line}: {name} is required and is blank")

        qty_cell = raw["qty"]
        try:
            qty = int(qty_cell)
        except ValueError as exc:
            raise _cell_error(path, line, "qty", qty_cell, "is not a whole number") from exc

        simulated_cell = raw["simulated"]
        if simulated_cell not in ("True", "False"):
            raise _cell_error(
                path, line, "simulated", simulated_cell, "is not 'True' or 'False'"
            )

        side_cell = raw["side"]
        if side_cell not in SIDE_SIGN:
            raise _cell_error(path, line, "side", side_cell, "is not 'long' or 'short'")

        exit_present = [n for n in _EXIT_FIELDS if raw[n] != ""]
        if exit_present and len(exit_present) != len(_EXIT_FIELDS):
            missing = [n for n in _EXIT_FIELDS if raw[n] == ""]
            raise Track3LogError(
                f"{path.name} line {line}: the exit is half-recorded -- present {exit_present}, "
                f"missing {missing}; an exit is all three fields or none"
            )

        try:
            row = TradeRow(
                trade_id=raw["trade_id"],
                model=raw["model"],
                stage=raw["stage"],
                frozen_sha256=raw["frozen_sha256"],
                root=raw["root"],
                size_label=raw["size_label"],
                side=side_cell,  # type: ignore[arg-type]
                qty=qty,
                signal_ts=_parse_ts(path, line, "signal_ts", raw["signal_ts"]),
                model_fill_px=_parse_float(path, line, "model_fill_px", raw["model_fill_px"]),
                order_sent_ts=_parse_ts(path, line, "order_sent_ts", raw["order_sent_ts"]),
                fill_ts=_parse_ts(path, line, "fill_ts", raw["fill_ts"]),
                fill_px=_parse_float(path, line, "fill_px", raw["fill_px"]),
                exit_signal_ts=(
                    _parse_ts(path, line, "exit_signal_ts", raw["exit_signal_ts"])
                    if exit_present
                    else None
                ),
                exit_fill_ts=(
                    _parse_ts(path, line, "exit_fill_ts", raw["exit_fill_ts"])
                    if exit_present
                    else None
                ),
                exit_fill_px=(
                    _parse_float(path, line, "exit_fill_px", raw["exit_fill_px"])
                    if exit_present
                    else None
                ),
                simulated=simulated_cell == "True",
                venue=raw["venue"],
                note=raw["note"],
            )
        except Track3LogError:
            raise
        except Track3Error as exc:
            raise Track3LogError(f"{path.name} line {line}: {exc}") from exc

        fault = row.ordering_fault()
        if fault is not None:
            raise Track3LogError(f"{path.name} line {line}: {fault}")
        return row


# --------------------------------------------------------------- implementation shortfall


def _check_instrument(fut: Future, row: TradeRow) -> Future:
    if not isinstance(fut, Future):
        raise Track3Error(
            f"shortfall needs a Future for the tick grid, got {type(fut).__name__}. The tick "
            "is what turns a price difference into the deposit's unit."
        )
    if fut.root != row.root:
        raise Track3Error(
            f"trade {row.trade_id!r} was logged on root {row.root!r} and the shortfall was "
            f"asked for on {fut.root!r}. One tick size is not another's: the same 0.25 is "
            "$1.25 on MES and $12.50 on ES."
        )
    return fut


def shortfall_ticks(row: TradeRow, fut: Future) -> float:
    """ENTRY implementation shortfall in TICKS, positive when the fill was worse.

    §13A.5: *"Implementation shortfall = actual fill − model fill, in ticks, signed against
    the trade."* Signed against the trade means `side_sign` — +1 long, −1 short — so a long
    filled above the model price and a short filled below it both record a POSITIVE number.

    Ledger unit test 35: a long filled 2 ticks above the model price gives +2; a short filled
    2 ticks below gives +2.
    """
    _check_instrument(fut, row)
    return row.side_sign * (row.fill_px - row.model_fill_px) / fut.tick_points


def shortfall_usd(row: TradeRow, fut: Future) -> float:
    """The entry shortfall in DOLLARS: ticks × `tick_usd` × `qty`, same sign.

    The dollars carry the size and the ticks do not, which is why the mean the cost review
    reads is a mean of ticks: §13A.5 states the shortfall in ticks, and a mean of dollars over
    rows of different `qty` is a size-weighted quantity the deposit never asked for.
    """
    _check_instrument(fut, row)
    return shortfall_ticks(row, fut) * fut.tick_usd * row.qty


def exit_shortfall_ticks(row: TradeRow, fut: Future, model_exit_px: float) -> float:
    """EXIT shortfall in ticks, with the sign INVERTED — an exit is the opposite trade.

    A long's exit sells, so a lower fill is worse; a short's exit buys, so a higher fill is
    worse. Both give a positive number, which is d364's `SIDE_SIGN["cover_exit"] = +1.0`
    generalised to the other direction.

    `model_exit_px` is an argument because the deposit's log has no column for it: §13A.5
    names one model price, the entry's. Raises on a trade that is still open — an exit
    shortfall computed from a missing exit price is a number that is wrong rather than absent.
    """
    _check_instrument(fut, row)
    if row.exit_fill_px is None:
        raise Track3Error(
            f"trade {row.trade_id!r} has no exit fill recorded, so it has no exit shortfall. "
            "An open trade is not a zero-shortfall one."
        )
    _finite(model_exit_px, "model_exit_px")
    return -row.side_sign * (row.exit_fill_px - model_exit_px) / fut.tick_points


def exit_shortfall_usd(row: TradeRow, fut: Future, model_exit_px: float) -> float:
    """The exit shortfall in dollars: ticks × `tick_usd` × `qty`."""
    return exit_shortfall_ticks(row, fut, model_exit_px) * fut.tick_usd * row.qty


# --------------------------------------------------------------------------- latency


def latency_bars(row: TradeRow, bar_seconds: float) -> float:
    """Signal-to-fill time in BARS: `(fill_ts − signal_ts) / bar_seconds`.

    Bars rather than seconds because §13A.5's assumption is stated in bars — *"consistent with
    the t0+1 … t0+5 assumption"* — and a latency in seconds cannot be compared to it without
    the bar length, which is a property of the model and not of the log.
    """
    if not math.isfinite(bar_seconds) or bar_seconds <= 0.0:
        raise Track3Error(f"bar_seconds must be finite and positive, got {bar_seconds!r}")
    delta = (row.fill_ts - row.signal_ts).total_seconds()
    return delta / float(bar_seconds)


def quantile_nearest_rank(values: Sequence[float], num: int, den: int) -> float:
    """The `num/den` quantile by NEAREST RANK, with the rank computed in integers.

    `rank = ceil(num * n / den) = (num * n + den - 1) // den`, and the result is the value at
    `rank - 1` of the sorted sample. Integer arithmetic on purpose: 0.95 is not a binary
    fraction, so `0.95 * (n - 1)` is 4.750000000000001 rather than 4.75 at n = 6 and an
    interpolated p95 would depend on the last bit of a constant. Every value returned here is
    one that actually occurred.
    """
    if num <= 0 or den <= 0 or num > den:
        raise Track3Error(f"quantile needs 0 < num <= den, got {num}/{den}")
    n = len(values)
    if n == 0:
        raise Track3Error("quantile of an empty sample")
    rank = (num * n + den - 1) // den
    return float(sorted(values)[rank - 1])


def latency_report(
    rows: Sequence[TradeRow],
    bar_seconds: float,
    assumed_max: float = LATENCY_ASSUMED_MAX_BARS,
) -> dict[str, Any]:
    """§13A.5's latency check: the DISTRIBUTION, and the share of fills beyond t0+5.

    Returns `n`, `bar_seconds`, `assumed_max`, `min`, `p50`, `p95`, `max`, `n_beyond`,
    `share_beyond_t0_plus_5` and the `latency_bars` themselves in log order. The share counts
    a latency STRICTLY greater than `assumed_max`: a fill exactly at t0+5 is inside the
    assumption, which is what "t0+1 … t0+5" says.

    An empty log RAISES. The share of an empty sample is not 0.0 — it is the absence of a
    measurement, and 0.0 would read as "no fill was ever late".
    """
    if not math.isfinite(assumed_max) or assumed_max <= 0.0:
        raise Track3Error(f"assumed_max must be finite and positive, got {assumed_max!r}")
    if len(rows) == 0:
        raise Track3Error(
            "latency_report on an empty log. No fill has been recorded, so there is no "
            "distribution; an empty log does not report a 0.0 share beyond t0+5."
        )
    lat = [latency_bars(r, bar_seconds) for r in rows]
    n_beyond = sum(1 for x in lat if x > assumed_max)
    return {
        "n": len(lat),
        "bar_seconds": float(bar_seconds),
        "assumed_max": float(assumed_max),
        "min": float(min(lat)),
        "p50": quantile_nearest_rank(lat, 1, 2),
        "p95": quantile_nearest_rank(lat, 19, 20),
        "max": float(max(lat)),
        "n_beyond": n_beyond,
        "share_beyond_t0_plus_5": n_beyond / len(lat),
        "latency_bars": tuple(lat),
    }


# ----------------------------------------------------------------------- the cost review


def cost_assumption_ticks(
    root: str,
    size: str | None = None,
    line: str | None = None,
    *,
    table_path: Path | None = None,
) -> float:
    """The CostStack slippage assumption PER FILL, in ticks.

        assumption = crossing_ticks_per_round_trip / 2 + ADVERSE_TICKS_PER_ENTRY

    THE DEPOSIT DOES NOT DEFINE "the CostStack slippage assumption" and this function does.
    The first term is D591's `TickCrossing` charge for one fill — it charges half a round trip
    per fill, so half the table's round-trip figure is one fill's crossing. The second is
    §7.3's *"plus 1 tick of adverse slippage"* on the primary entry fill, which is the model
    price the shortfall is measured against, so it belongs in the assumption that shortfall is
    compared to.

    Everything raises rather than defaulting: `FuturesRoundTrip.from_table` refuses an unknown
    root, size or line, and a line that root was never measured on.
    """
    trip = FuturesRoundTrip.from_table(root, size, line, table_path=table_path)
    return trip.crossing.ticks_per_round_trip / 2.0 + ADVERSE_TICKS_PER_ENTRY


@dataclass(frozen=True)
class CostReview:
    """§13A.5's 50-trade cost review. `mean_shortfall_ticks`, `assumption_ticks` in TICKS."""

    n: int
    required_n: int
    sufficient: bool
    assumption_ticks: float
    mean_shortfall_ticks: float | None
    ratio: float | None
    exceeds_by_50pct: bool | None
    action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "n": self.n,
            "required_n": self.required_n,
            "sufficient": self.sufficient,
            "assumption_ticks": self.assumption_ticks,
            "mean_shortfall_ticks": self.mean_shortfall_ticks,
            "ratio": self.ratio,
            "exceeds_by_50pct": self.exceeds_by_50pct,
            "action": self.action,
        }


def cost_review(
    rows: Sequence[TradeRow],
    fut: Future,
    assumption_ticks: float,
    n: int = COST_REVIEW_N,
) -> CostReview:
    """*"Cost review after 50 trades: if the mean shortfall exceeds the CostStack slippage
    assumption by more than 50%, update CostStack via doc edit and re-run all Track 1 results
    at the new cost before continuing."*

    Read on the FIRST `n` rows, not on every row logged so far: the deposit's review happens
    *after 50 trades*, and a review that silently widens its window every time it is called is
    a different test each time it runs.

    Fewer than `n` rows returns `sufficient=False` with the count and NO verdict — `mean`,
    `ratio` and `exceeds_by_50pct` are all None. "Within budget" computed on six trades is a
    verdict manufactured out of an empty sample.

    The action is a FLAG. Nothing here edits `data/futures_costs.json`, a `CostStack` or a
    doc; the deposit says *"via doc edit"*, and a doc edit is a human act.
    """
    if n <= 0:
        raise Track3Error(f"cost_review needs a positive trade count, got {n}")
    if not math.isfinite(assumption_ticks) or assumption_ticks <= 0.0:
        raise Track3Error(
            f"cost_review needs a finite positive assumption in ticks, got "
            f"{assumption_ticks!r}. A zero assumption makes every ratio infinite."
        )
    have = len(rows)
    if have < n:
        return CostReview(
            n=have,
            required_n=n,
            sufficient=False,
            assumption_ticks=float(assumption_ticks),
            mean_shortfall_ticks=None,
            ratio=None,
            exceeds_by_50pct=None,
            action=(
                f"INSUFFICIENT: {have} of {n} trades logged. No mean, no ratio, no verdict "
                "(section 13A.5 reviews after 50 trades)."
            ),
        )
    window = list(rows[:n])
    ticks = [shortfall_ticks(r, fut) for r in window]
    mean = sum(ticks) / len(ticks)
    ratio = mean / float(assumption_ticks)
    exceeds = ratio > EXCEEDS_RATIO
    return CostReview(
        n=have,
        required_n=n,
        sufficient=True,
        assumption_ticks=float(assumption_ticks),
        mean_shortfall_ticks=mean,
        ratio=ratio,
        exceeds_by_50pct=exceeds,
        action=COST_REVIEW_ACTION if exceeds else "none: mean shortfall within the assumption",
    )


# -------------------------------------------------------------------- the trial counter


@dataclass(frozen=True)
class Restart:
    """One §13A.4 restart: *"Any change restarts the count at N = 0 under a new frozen file."*"""

    at_n: int
    reason: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {"at_n": self.at_n, "reason": self.reason, "message": self.message}


@dataclass
class TrialCounter:
    """§13A.4's forward-test counter: target N, two futility looks and one efficacy decision.

    `add` takes the NET return per trade, in whatever unit the model declares (the ledger says
    "mean net return per trade" and never fixes a unit). Whatever it is, it must be the same
    on every call: `t` is scale-free but `mean` is not.

    `counts_as_efficacy=False` makes `efficacy()` return False at every N. That is
    `INDEX_REWEIGHT_FLOW_PREREG.md` unit test 28 — *"Track 3 January trades are never counted
    as independent efficacy evidence"* — because five execution days a year cannot reach N =
    300 in any useful time. Futility is UNAFFECTED: a January book can still be shown to be
    losing, and the asymmetry is the point of the flag.
    """

    model: str
    target: int = TRACK3_TARGET_N
    looks: tuple[int, ...] = (100, 200)
    frozen_path: str | Path | None = None
    counts_as_efficacy: bool = True
    efficacy_reason: str = ""
    returns: list[float] = field(default_factory=list)
    restarts: list[Restart] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.model, str) or not self.model.strip():
            raise Track3Error(f"TrialCounter needs a model name, got {self.model!r}")
        if not isinstance(self.target, int) or self.target < 2:
            raise Track3Error(f"TrialCounter target must be an int >= 2, got {self.target!r}")
        looks = tuple(int(x) for x in self.looks)
        if len(set(looks)) != len(looks) or list(looks) != sorted(looks):
            raise Track3Error(f"looks must be strictly increasing and unique, got {self.looks!r}")
        for look in looks:
            if look < 2 or look >= self.target:
                raise Track3Error(
                    f"futility look {look} must satisfy 2 <= look < target ({self.target}); a "
                    "look at or past the target is the efficacy decision wearing another name"
                )
        self.looks = looks
        if not self.counts_as_efficacy and not self.efficacy_reason.strip():
            raise Track3Error(
                "counts_as_efficacy=False needs an efficacy_reason. A counter that silently "
                "never returns efficacy is indistinguishable from one that is broken."
            )

    # -- state --------------------------------------------------------------------

    def add(self, net_return_per_trade: float) -> int:
        """Record one trade's net return. Returns the new N."""
        x = _finite(net_return_per_trade, "net_return_per_trade")
        self.returns.append(x)
        return len(self.returns)

    def extend(self, values: Iterable[float]) -> int:
        for v in values:
            self.add(v)
        return len(self.returns)

    @property
    def n(self) -> int:
        return len(self.returns)

    @property
    def mean(self) -> float:
        if self.n == 0:
            raise Track3Error(f"{self.model}: mean of no trades. N = 0 is not a mean of 0.0.")
        return sum(self.returns) / self.n

    @property
    def sd(self) -> float:
        """Sample standard deviation, ddof = 1. Raises below N = 2."""
        n = self.n
        if n < 2:
            raise Track3Error(
                f"{self.model}: the sample sd is undefined at N = {n} (ddof = 1 divides by "
                "N - 1). It is not 0.0."
            )
        mean = self.mean
        return math.sqrt(sum((x - mean) ** 2 for x in self.returns) / (n - 1))

    @property
    def t(self) -> float:
        """`mean / (sd / sqrt(n))`, ddof = 1. Raises below N = 2 and on a constant series."""
        sd = self.sd
        if sd == 0.0:
            raise Track3Error(
                f"{self.model}: every one of {self.n} trades returned {self.returns[0]!r}, so "
                "sd = 0 and t is undefined. A constant series is a data fault, not an "
                "infinitely significant result."
            )
        return self.mean * math.sqrt(self.n) / sd

    # -- the two decisions ---------------------------------------------------------

    def at_look(self) -> bool:
        return self.n in self.looks

    def futility(self) -> bool:
        """§13A.4: *"Futility looks at N = 100 and N = 200: stop if the mean net return per
        trade < 0 **and** t < −1."*

        True ONLY at a look, and only when BOTH hold. The rule is signed: `t < −1`, never
        `|t| > 1` — a winning book at t = +2 satisfies the absolute form and must not stop.

        Ledger unit test 36: at N = 100, mean < 0 and t < −1 → True; mean < 0 and t > −1 →
        False; mean > 0 → False. At N = 99 it is False whatever the numbers say, because 99 is
        not a look.
        """
        if not self.at_look():
            return False
        return self.mean < 0.0 and self.t < -1.0

    def efficacy(self) -> bool:
        """§13A.4: *"Efficacy decision only at N = 300: mean net > 0 with t ≥ 2."*

        Only at exactly N = target, and always False when `counts_as_efficacy` is False.
        """
        if not self.counts_as_efficacy:
            return False
        if self.n != self.target:
            return False
        return self.mean > 0.0 and self.t >= 2.0

    # -- the protocol --------------------------------------------------------------

    def check_frozen(
        self,
        params: Mapping[str, Any],
        code_paths: Iterable[str | Path],
        fixture_paths: Iterable[str | Path] = (),
    ) -> Restart | None:
        """§13A.4: *"Any change restarts the count at N = 0 under a new frozen file."*

        Delegates to `validation/frozen.assert_frozen` (D594) and returns None when nothing
        drifted. On `FrozenDriftError` the count is RESET to 0 and a `Restart` carrying the
        drift message is appended to `.restarts` and returned.

        It does not re-raise. The deposit makes drift a protocol event with a defined
        consequence — restart — rather than an error, and re-raising after the reset would
        leave the caller with a reset it never learned about. The drift is not silent: the
        returned record is truthy and `to_dict()` carries every restart.
        """
        if self.frozen_path is None:
            raise Track3Error(
                f"{self.model}: check_frozen needs a frozen_path. Section 13A.4 restart rule is "
                "defined against FROZEN_<stage>.json; there is nothing to compare to."
            )
        try:
            assert_frozen(
                self.frozen_path,
                params=params,
                code_paths=code_paths,
                fixture_paths=fixture_paths,
            )
        except FrozenDriftError as exc:
            restart = Restart(at_n=self.n, reason="frozen drift", message=str(exc))
            self.returns = []
            self.restarts.append(restart)
            return restart
        return None

    def restart(self, reason: str) -> Restart:
        """An explicit restart — §13A.5's upgrade to a better stage, or a parameter change."""
        if not reason.strip():
            raise Track3Error("a restart must name its reason; 13A.4 restarts are on the record")
        record = Restart(at_n=self.n, reason=reason, message=reason)
        self.returns = []
        self.restarts.append(record)
        return record

    def route(self, edge_sigma: float) -> Track3Route:
        """§13A.7(4), delegated to `validation/power.track3_route` — never retyped here."""
        return track3_route(edge_sigma, n=self.target)

    def to_dict(self) -> dict[str, Any]:
        n = self.n
        sd = self.sd if n >= 2 else None
        readable = sd is not None and sd != 0.0
        return {
            "model": self.model,
            "n": n,
            "target": self.target,
            "looks": list(self.looks),
            "mean": self.mean if n >= 1 else None,
            "sd": sd,
            "t": self.t if readable else None,
            "at_look": self.at_look(),
            "futility": self.futility() if readable else False,
            "efficacy": self.efficacy() if readable else False,
            "counts_as_efficacy": self.counts_as_efficacy,
            "efficacy_reason": self.efficacy_reason,
            "frozen_path": str(self.frozen_path) if self.frozen_path is not None else None,
            "restarts": [r.to_dict() for r in self.restarts],
        }
