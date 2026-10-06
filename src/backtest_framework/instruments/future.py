"""Futures instrument implementing the `Instrument` protocol.

`Future` holds the tick size in price points, the dollar value of one point and the dollar
value of one tick, read from the exchange specification files, and provides tick-grid
rounding and checking.

Spec files
----------
`data/futures_contract_specs.json` (primary): the CME contract-specification pages for 23
roots, with `usd_per_point` and `tick_points` parsed from CME's wording; `_provenance`
records the fetch.

`data/fut_specs_from_definition.json` (fallback): the Databento GLBX definition snapshot,
41 roots including MBT, which the CME file lacks. Tick size is `tick_price_units`, tick
value is `tick_usd_full_contract`, and `usd_per_point` is their quotient.

That file's `tick_usd` field is not used. It is the snapshot's raw formula with a `/100`
applied whenever `unit_of_measure == "USD"`, which makes it 100x high on ZC, ZS, ZW, ZL, LE,
HE and 100x low on SR3 (seven roots, all with `known_tick_usd: null`). It is kept for
compatibility; `tick_usd_full_contract`, chosen by a notional consistency test, is the
corrected value, and an entry without it raises.

An unknown root raises `KeyError`; there is no default multiplier.

Grid tolerance
--------------
`assert_on_grid` admits a residual of `1e-9 × tick_points`. Expressing it as a fraction of
a tick gives the rule the same meaning on ES (tick 0.25) and ZN (tick 1/64).
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

REPO = Path(__file__).resolve().parents[3]

SPECS_PATH = REPO / "data" / "futures_contract_specs.json"
"""CME contract specifications, the primary source (23 roots)."""

FALLBACK_SPECS_PATH = REPO / "data" / "fut_specs_from_definition.json"
"""Databento GLBX definition snapshot, the fallback (41 roots, includes MBT)."""

GRID_TOLERANCE_TICKS = 1e-9
"""Maximum distance from the grid, in ticks, for a price to count as on it.

Floored at `ULP_FLOOR` units in the last place of the price. A nanotick is finer than a
double can resolve once `price / tick_points` is large: on 6E (tick 5e-05) a price of 5,000
has a representation error of 2.2e-09 ticks, so `5000 + k * 5e-05` would fail the check for
a third of k. 6E trades near 1.10, where the plain rule suffices; the floor only prevents
false alarms on extreme inputs.
"""

ULP_FLOOR = 4.0
"""Lower bound on the grid tolerance, in units in the last place. Four rather than one
because the residual is a difference of two rounded quantities."""

RoundingDirection = Literal["nearest", "up", "down"]


@lru_cache(maxsize=2)
def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} is missing. Future.from_specs reads the exchange's own specification "
            "file; it does not fall back to a hardcoded multiplier."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a JSON object")
    return data


@dataclass(frozen=True)
class Future:
    """One futures contract root, satisfying the `Instrument` protocol.

    `root` is the exchange root ("ES", "MES", "CL"), not a contract month: it is meant for
    a continuous front-month series, and tick and multiplier belong to the root.

    `tick_points` is the minimum price increment in quoted units (0.25 index points for
    ES). `usd_per_point` is the dollar value of a one-point move on one contract ($50 for
    ES, $5 for MES). `tick_usd` is their product; it is stored rather than derived so the
    spec file's value can be checked against the other two.
    """

    root: str
    tick_points: float
    usd_per_point: float
    tick_usd: float
    quote_currency: str = "USD"

    def __post_init__(self) -> None:
        if not self.root:
            raise ValueError("Future needs a root symbol")
        for name in ("tick_points", "usd_per_point", "tick_usd"):
            value = getattr(self, name)
            if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                raise ValueError(f"{self.root}: {name} must be a finite number, got {value!r}")
            if float(value) <= 0.0:
                raise ValueError(f"{self.root}: {name} must be positive, got {value!r}")
        implied = self.usd_per_point * self.tick_points
        if abs(implied - self.tick_usd) > 1e-9 * self.tick_usd:
            raise ValueError(
                f"{self.root}: usd_per_point * tick_points = {implied!r} but tick_usd = "
                f"{self.tick_usd!r}. The specification file asserts these agree "
                "(_provenance in data/futures_contract_specs.json); a Future that carries "
                "three numbers which disagree would price every fill wrong."
            )

    # ------------------------------------------------------------------ construction

    @classmethod
    def from_specs(
        cls,
        root: str,
        *,
        specs_path: Path | None = None,
        fallback_path: Path | None = None,
    ) -> Future:
        """Build from the exchange specification files. Raises `KeyError` on an unknown root.

        The CME file is tried first, then the Databento definition snapshot. Both paths can
        be overridden, for example to point a test at a fixture.
        """
        specs = _load_json(specs_path or SPECS_PATH)
        entry = specs.get(root)
        if isinstance(entry, dict) and "usd_per_point" in entry:
            return cls(
                root=root,
                tick_points=float(entry["tick_points"]),
                usd_per_point=float(entry["usd_per_point"]),
                tick_usd=float(entry["tick_usd"]),
            )

        fallback = _load_json(fallback_path or FALLBACK_SPECS_PATH).get("specs", {})
        definition = fallback.get(root) if isinstance(fallback, dict) else None
        if isinstance(definition, dict) and definition.get("present"):
            tick_points = float(definition["tick_price_units"])
            # Use `tick_usd_full_contract`, not `tick_usd`. The raw `tick_usd` applies `/100`
            # whenever `unit_of_measure == "USD"`, which is wrong for seven roots: ZC, ZS, ZW
            # (cents per bushel), ZL, LE, HE (cents per pound) come out 100x high, and SR3 100x
            # low because the percent-of-par divide applies to a `unit_of_measure_qty` already
            # in dollars per point. All seven have `known_tick_usd: null`, and
            # `__post_init__`'s product check cannot catch the error because `usd_per_point`
            # is derived from `tick_usd` here. `tick_usd_full_contract` is chosen by a notional
            # consistency test and agrees with CME on all 17 roots where CME's value is on file.
            if "tick_usd_full_contract" not in definition:
                raise KeyError(
                    f"{root!r} in {FALLBACK_SPECS_PATH.name} carries no "
                    "'tick_usd_full_contract', the tick value chosen by a notional consistency "
                    "test. The raw 'tick_usd' field is 100x off on seven cent-quoted roots "
                    "and is not used."
                )
            tick_usd = float(definition["tick_usd_full_contract"])
            known = definition.get("known_tick_usd")
            if known is not None and abs(tick_usd - float(known)) > 1e-9 * abs(float(known)):
                # An independent check: the tick value against CME's published value for the
                # same root. Unlike `__post_init__`, whose numbers here are derived from one
                # another, an arithmetic error in the definition table cannot pass it.
                raise ValueError(
                    f"{root}: tick_usd_full_contract = {tick_usd!r} but "
                    f"{FALLBACK_SPECS_PATH.name} records known_tick_usd = {known!r} from CME. "
                    "The definition snapshot's scaling disagrees with the exchange."
                )
            return cls(
                root=root,
                tick_points=tick_points,
                usd_per_point=tick_usd / tick_points,
                tick_usd=tick_usd,
                quote_currency=str(definition.get("currency", "USD")),
            )

        known_cme = sorted(k for k in specs if not k.startswith("_"))
        known_def = sorted(k for k in fallback) if isinstance(fallback, dict) else []
        raise KeyError(
            f"no contract specification for root {root!r}. "
            f"{SPECS_PATH.name} carries {', '.join(known_cme) or '(none)'}; "
            f"{FALLBACK_SPECS_PATH.name} carries {', '.join(known_def) or '(none)'}."
        )

    # ------------------------------------------------------------------ the tick grid

    def round_to_tick(self, price: float, direction: RoundingDirection = "nearest") -> float:
        """Snap `price` onto the tick grid.

        "up" and "down" round toward +inf and -inf, since futures prices can be negative
        (CL settled at -37.63 on 2020-04-20). Both absorb a residual of
        `GRID_TOLERANCE_TICKS`, so float noise never moves an on-grid price by a tick.

        "nearest" breaks a half-tick tie toward +inf, unlike `round()`, whose banker's
        rounding depends on the parity of the tick index.
        """
        if not math.isfinite(price):
            raise ValueError(f"{self.root}: cannot round a non-finite price {price!r}")
        n = price / self.tick_points
        epsilon = max(GRID_TOLERANCE_TICKS, ULP_FLOOR * math.ulp(abs(n)))
        if direction == "nearest":
            k = math.floor(n + 0.5)
        elif direction == "up":
            k = math.ceil(n - epsilon)
        elif direction == "down":
            k = math.floor(n + epsilon)
        else:
            raise ValueError(
                f"direction must be 'nearest', 'up' or 'down', got {direction!r}"
            )
        return k * self.tick_points

    def assert_on_grid(self, price: float, what: str = "price") -> None:
        """Raise unless `price` is on the tick grid to within `GRID_TOLERANCE_TICKS`.

        The futures fill model calls this on every price it returns.
        """
        if not math.isfinite(price):
            raise ValueError(f"{self.root}: {what} is not finite: {price!r}")
        residual = abs(price - self.round_to_tick(price, "nearest"))
        tolerance = max(GRID_TOLERANCE_TICKS * self.tick_points, ULP_FLOOR * math.ulp(abs(price)))
        if residual > tolerance:
            raise ValueError(
                f"{self.root}: {what} {price!r} is off the {self.tick_points} grid by "
                f"{residual / self.tick_points:.6g} ticks (tolerance "
                f"{tolerance / self.tick_points:.6g} ticks). Nothing fills between ticks."
            )

    def ticks(self, price_diff: float) -> float:
        """Return a price difference in ticks, signed and unrounded."""
        if not math.isfinite(price_diff):
            raise ValueError(f"{self.root}: price_diff is not finite: {price_diff!r}")
        return price_diff / self.tick_points

    def usd(self, price_diff: float, quantity: float) -> float:
        """Return a price difference on `quantity` contracts in dollars, signed."""
        if not math.isfinite(price_diff) or not math.isfinite(quantity):
            raise ValueError(
                f"{self.root}: usd() needs finite arguments, got "
                f"price_diff={price_diff!r}, quantity={quantity!r}"
            )
        return price_diff * self.usd_per_point * quantity

    # ------------------------------------------------------------------ the protocol

    def notional(self, quantity: float, price: float) -> float:
        """Contract value: `quantity × price × usd_per_point`.

        One ES at 4,000 is $200,000 of index exposure; `risk.gross_exposure` uses this.
        """
        return quantity * price * self.usd_per_point

    def carry_components(self) -> tuple[str, ...]:
        """Return an empty tuple: a future has no borrow or dividend.

        The cost of carry is already in the futures price through the basis. The protocol
        treats an empty tuple as "none apply".
        """
        return ()

    def tradeable_quantity(self, raw_quantity: float) -> float:
        """Round to whole contracts."""
        return float(round(raw_quantity))
