"""Futures instrument (D587) — the third implementation of the `Instrument` protocol.

`Equity` and `OptionStub` were the only instruments in this package, and every futures
study here carried its own tick size and multiplier as a module constant: `TICK = 0.25`
and `MULT = {"ES": 5.0, "NQ": 2.0}` in one runner, `TICK_PTS` / `TICK_USD = 0.50` in
another, `COST_USD = 4.21` in a third. **No tick-rounding primitive existed anywhere in
the repository**, so "the fill is on the tick grid" was a property nothing could check.

This class carries the three numbers that decide what a futures price *means* — the tick
size in price points, the dollar value of one point, and the dollar value of one tick —
and reads them from the exchange's own specification file rather than from a literal.

TWO SPEC FILES, AND WHY THE FALLBACK EXISTS
--------------------------------------------
`data/futures_contract_specs.json` is the CME contract-specification service read through
each product's page (23 roots, `_provenance` records the fetch). It is the primary source
because its `usd_per_point` and `tick_points` are parsed from CME's own wording.

`data/fut_specs_from_definition.json` is the Databento GLBX definition snapshot (41 roots,
including MBT, which the CME file does not carry). It states tick size as
`tick_price_units` and, since D609, the tick VALUE as **`tick_usd_full_contract`**;
`usd_per_point` is their quotient. The fallback path is the one
`scripts/run_d555_tsmom_replication.py` already takes by hand for MBT.

**Do not read that file's `tick_usd`.** It is the snapshot's raw formula with a `/100` applied
on `unit_of_measure == "USD"` alone, and it is 100x HIGH on ZC, ZS, ZW, ZL, LE, HE and 100x LOW
on SR3 — seven roots, every one with `known_tick_usd: null`, so nothing here had ever charged
them a verified number. The field is kept unchanged because D591 and D604 quote it; the
corrected value is `tick_usd_full_contract`, decided by the notional test in
`scripts/build_fut_breadth_hourly.py`, and an entry without it raises here.

**An unknown root raises `KeyError`.** A default multiplier is the D48 failure — a number
that is wrong rather than absent, with no test able to notice, exactly as
`SqrtImpact._params_for` says of a missing ADV.

THE GRID TOLERANCE IS IN TICKS, NOT IN PRICE
---------------------------------------------
`assert_on_grid` admits a residual of `1e-9 × tick_points`. Stating the tolerance as a
fraction of a tick rather than as an absolute epsilon is the difference between a rule
that means the same thing on ES (tick 0.25) and on ZN (tick 1/64). The existing
`TRADE_THROUGH_EPS = 1e-9` in `research/terrain_strategies.py` is absolute, and that is
the disagreement D587's record names.
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
"""How far off the grid a price may sit and still be called on it, IN TICKS.

**Floored at `ULP_FLOOR` units in the last place of the price itself.** A nanotick is a
tighter tolerance than a double can carry once `price / tick_points` gets large: on 6E
(tick 5e-05) a price of 5,000 has a representation error of 2.2e-09 ticks, so
`5000 + k * 5e-05` would be declared off its own grid for a third of k. 6E trades at 1.10
and never goes near 5,000, so the plain rule is sufficient for every fixture on disk — the
floor is here so that the guard degrades to "as tight as the float can express" rather
than to a false alarm, on a contract nobody has loaded yet.
"""

ULP_FLOOR = 4.0
"""Units in the last place the grid tolerance never goes below. Four, not one, because the
residual is a difference of two rounded quantities and each contributes."""

RoundingDirection = Literal["nearest", "up", "down"]


@lru_cache(maxsize=2)
def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} is missing. Future.from_specs reads the exchange's own specification "
            "file; it does not fall back to a hardcoded multiplier (D48)."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a JSON object")
    return data


@dataclass(frozen=True)
class Future:
    """One futures contract root, satisfying the `Instrument` protocol (D12).

    `root` is the exchange root ("ES", "MES", "CL"), not a contract month: every study
    here trades a continuous front-month series and the tick and multiplier are
    properties of the root, not of the expiry.

    `tick_points` is the minimum price increment in the units the price is QUOTED in
    (0.25 index points for ES). `usd_per_point` is the dollar value of a one-point move
    of one contract ($50 for ES, $5 for MES). `tick_usd` is their product and is carried
    rather than derived so that the specification file's own third number is checked
    against the other two instead of being thrown away.
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

        The CME file is tried first; the Databento definition snapshot second. Both paths
        are overridable so a test can point at a fixture, and neither is guessed at.
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
            # `tick_usd_full_contract`, NOT `tick_usd` -- D609. `tick_usd` is the definition
            # snapshot's raw formula with a `/100` applied on `unit_of_measure == "USD"` alone,
            # and that rule is wrong for seven roots: ZC, ZS, ZW (cents per bushel), ZL, LE, HE
            # (cents per pound) came out 100x HIGH, and SR3 100x LOW because the percent-of-par
            # divide fires on a `unit_of_measure_qty` that is already dollars per point. Every
            # one of the seven has `known_tick_usd: null`, so `__post_init__`'s product identity
            # could not catch it: it holds by construction, because `usd_per_point` is DERIVED
            # from `tick_usd`. `tick_usd_full_contract` is decided by the notional test in
            # `scripts/build_fut_breadth_hourly.py:decide_scaling` and agrees with CME on all 17
            # roots where CME's own value is on file.
            if "tick_usd_full_contract" not in definition:
                raise KeyError(
                    f"{root!r} in {FALLBACK_SPECS_PATH.name} carries no "
                    "'tick_usd_full_contract'. That field is the NOTIONAL-decided tick value "
                    "(D609); the file's own 'tick_usd' is 100x wrong on seven roots and is kept "
                    "only because D591 and D604 quote it. Re-run "
                    "`python scripts/probe_definition_specs.py --rescale`. A missing multiplier "
                    "must be a loud error, not a guessed one (D48)."
                )
            tick_usd = float(definition["tick_usd_full_contract"])
            known = definition.get("known_tick_usd")
            if known is not None and abs(tick_usd - float(known)) > 1e-9 * abs(float(known)):
                # NOT satisfiable by construction, which is the point. `__post_init__` compares
                # three numbers two of which are derived from the third; this compares the one
                # number that matters against CME's own published value for the same root, from
                # a different file, and it is the only check in this class that an arithmetic
                # error in the definition table cannot pass.
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
            f"{FALLBACK_SPECS_PATH.name} carries {', '.join(known_def) or '(none)'}. "
            "A missing multiplier must be a loud error, not a guessed one (D48)."
        )

    # ------------------------------------------------------------------ the tick grid

    def round_to_tick(self, price: float, direction: RoundingDirection = "nearest") -> float:
        """Snap `price` onto the tick grid.

        "up" and "down" are toward +inf and -inf respectively, NOT away from and toward
        zero — futures prices go negative (CL settled at -37.63 on 2020-04-20) and a
        rounding rule that changes meaning at zero is a trap. Both absorb a residual of
        `GRID_TOLERANCE_TICKS`, so a price already on the grid is never pushed a whole
        tick by float noise in the division.

        "nearest" breaks a half-tick tie upward (toward +inf), which is a choice, not a
        law: it is stated here because `round()`'s banker's rounding would make the tie
        depend on the parity of the tick index, which nothing could reason about.
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
        """Raise unless `price` sits on the tick grid to within `GRID_TOLERANCE_TICKS`.

        This is the door guard the fill model leans on: every price it returns passes
        here, so "the fill is tradeable" stops being a claim in prose.
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
        """A price DIFFERENCE expressed in ticks. Signed, and not rounded."""
        if not math.isfinite(price_diff):
            raise ValueError(f"{self.root}: price_diff is not finite: {price_diff!r}")
        return price_diff / self.tick_points

    def usd(self, price_diff: float, quantity: float) -> float:
        """A price DIFFERENCE on `quantity` contracts, in dollars. Signed."""
        if not math.isfinite(price_diff) or not math.isfinite(quantity):
            raise ValueError(
                f"{self.root}: usd() needs finite arguments, got "
                f"price_diff={price_diff!r}, quantity={quantity!r}"
            )
        return price_diff * self.usd_per_point * quantity

    # ------------------------------------------------------------------ the protocol

    def notional(self, quantity: float, price: float) -> float:
        """Contract value: `quantity × price × usd_per_point`.

        One ES at 4,000 is $200,000 of index exposure, which is what
        `risk.gross_exposure` needs and what makes a futures book's leverage visible.
        """
        return quantity * price * self.usd_per_point

    def carry_components(self) -> tuple[str, ...]:
        """Empty, and deliberately so.

        A future has no borrow and pays no dividend: the cost of carry is already in the
        futures price through the basis. The protocol names the empty tuple a legitimate
        answer — "none apply", not a missing implementation — and listing a component no
        brick declares would be the D48 false affordance `Equity` had to delete.
        """
        return ()

    def tradeable_quantity(self, raw_quantity: float) -> float:
        """Whole contracts. There is no fractional future."""
        return float(round(raw_quantity))
