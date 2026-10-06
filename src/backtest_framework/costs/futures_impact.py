"""Square-root market impact for futures, and its depth-scaled variant.

`costs/equity_bricks.py:SqrtImpact` keys its parameters on `instrument.symbol`, which
`Future` does not have (it has a `root`), so it raises on a `Future`. This module applies the
same square-root law with a futures parameter set keyed on `Future.root`. The arithmetic is
identical: `tests/unit/test_futures_impact.py` asserts the two fractions are equal
bit-for-bit on hypothesis-drawn inputs. Commission and tick crossing
(`costs/futures_bricks.py`) are adequate at one contract; larger sizes need an impact term.

Formulas
--------
Baseline impact::

    V_d      = 20-day trailing mean daily volume of the traded contract (days t-20 ... t-1)
    sigma_d  = 20-day trailing daily return std
    I        = Y x sigma_d x sqrt(|Q_rem| / V_d) x P x sign(Q_rem)       (price units)

    Y = 0.7, fixed: inside the 0.5-1 range reported for stocks and futures (see
    DEFAULT_IMPACT_Y below), and not fitted to the contracts in the table.

Depth-scaled impact::

    D(t0)  = resting depth within +/-5 ticks on both sides of the traded contract at t0
    D_bar  = trailing 20-day same-time median of D

    I_D = Y x sigma_d x sqrt(|Q_rem| / V_d) x P x sqrt(D_bar / D(t0)) x sign(Q_rem)
          (Y = 0.7 fixed; exponent 0.5 fixed)

No parameter in either formula is fitted.

`I_D` is `I` times `sqrt(D_bar / D(t0))` only, so `D(t0) = D_bar` gives `I_D == I` exactly
(`sqrt(1.0)` is `1.0`, and multiplying a finite double by 1.0 is lossless). The test asserts
this with `==`.

Units
-----
- `impact_fraction` is dimensionless: a fraction of the price, scaling as sqrt(Q).
- `impact_for_flow` returns `I`: a signed move in quoted price points (index points on ES,
  dollars a barrel on CL).
- `impact_usd` and `cost` return dollars on the trade's own notional
  (`Future.notional` = quantity x price x usd_per_point), so total dollars scale as Q^1.5.
- `adv_contracts` is in the root's full-size contracts, and `quantity` must be too. A
  quantity in micros against a full-size ADV understates the ratio by the size factor;
  `data/futures_impact_params.json` carries each root's `size` block for the conversion.

Not modelled
------------
Temporary versus permanent impact, decay, and participation rate over a window. Each
parameter line in the table is an average over its measurement window, not the 20-day
trailing quantity in the formula; the table records each line's window, and this module
does not check it.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence

from ..instruments.base import Instrument
from ..instruments.future import Future

REPO = Path(__file__).resolve().parents[3]

TABLE_PATH = REPO / "data" / "futures_impact_params.json"
"""The futures impact parameter table; every number carries its provenance and window."""

DEFAULT_IMPACT_Y = 0.7
"""The impact coefficient `Y`, fixed at 0.7.

The square-root law's prefactor is "a numerical constant of order unity", and "the Y constant
obtained for stocks and futures contracts is in the range 0.5 -> 1" (Tóth, Eisler and
Bouchaud, "The square-root impact law also holds for option markets", 2016,
arXiv:1602.03043). 0.7 is inside that range. It is not calibrated on the contracts in
`data/futures_impact_params.json`, for which no metaorder data is available, and is fixed in
advance so the cost model cannot be tuned to results. Pass `coefficient=` to override."""

DEPTH_EXPONENT = 0.5
"""The depth-scaling exponent, fixed at 0.5 (not fitted)."""


class FuturesImpactError(ValueError):
    """Raised when an impact parameter is missing or incomplete.

    A separate class, like `FuturesCostError`, so a caller can distinguish a missing ADV from
    a ValueError raised in the arithmetic. Lookups never fall back to a default value.
    """


# ------------------------------------------------------------------ parameters


@dataclass(frozen=True)
class FuturesImpactParams:
    """One root's impact inputs on one measurement line.

    The law reads `adv_contracts` and `sigma_fraction`. `sigma_usd_per_contract` and
    `notional_usd` are what the sources measure, and `sigma_fraction` is their quotient; all
    four are kept so the division can be checked.

    The measured fields are optional because not every source measures all four. The
    `hourly_2010_2026` line has a day-session sigma and a notional but no volume, so
    `adv_contracts` is None; the line is stored as is and rejected when used.
    """

    line: str
    """Measurement name: `trades_2025_2026`, `hourly_2010_2026` or `day1m_2016_2023`."""
    window: tuple[str, str]
    """Measurement window, inclusive, as ISO dates."""
    provenance: tuple[str, ...]
    """One entry per number: `file#key/path` or `script:line`. Never empty."""
    adv_contracts: float | None = None
    """Average daily volume of the root's front contract, in full-size contracts."""
    sigma_usd_per_contract: float | None = None
    """Standard deviation of the session move, in dollars on one full-size contract."""
    sigma_fraction: float | None = None
    """The same sigma as a fraction of contract notional (the formula's `sigma_d`)."""
    notional_usd: float | None = None
    """One full-size contract's notional at the line's own price level."""

    def __post_init__(self) -> None:
        if not self.line:
            raise FuturesImpactError("FuturesImpactParams needs a line name")
        if len(self.window) != 2 or not all(self.window):
            raise FuturesImpactError(
                f"{self.line}: window must be two ISO dates, got {self.window!r}. A parameter "
                "without its measurement window cannot be read for the extrapolation it is making."
            )
        if self.window[0] > self.window[1]:
            raise FuturesImpactError(
                f"{self.line}: window {self.window[0]}..{self.window[1]} ends before it starts"
            )
        if not self.provenance:
            raise FuturesImpactError(
                f"{self.line}: provenance is empty. Every number in this table is copied from a "
                "source by the builder; one that cannot say from where was typed."
            )
        for name in ("adv_contracts", "sigma_usd_per_contract", "sigma_fraction", "notional_usd"):
            value = getattr(self, name)
            if value is None:
                continue
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise FuturesImpactError(f"{self.line}: {name} must be numeric, got {value!r}")
            if not math.isfinite(float(value)) or float(value) <= 0.0:
                raise FuturesImpactError(
                    f"{self.line}: {name}={value!r} must be finite and positive"
                )

    @property
    def complete(self) -> bool:
        """True when this line carries both quantities the law reads."""
        return self.adv_contracts is not None and self.sigma_fraction is not None

    def missing(self) -> tuple[str, ...]:
        return tuple(n for n in ("adv_contracts", "sigma_fraction") if getattr(self, n) is None)


# ------------------------------------------------------------------ the brick


@dataclass(frozen=True)
class FuturesSqrtImpact:
    """Square-root impact on futures keyed on `Future.root`; a `TradeCostBrick`.

    `coefficient` defaults to `Y = 0.7`, where `SqrtImpact` defaults to 1.0. This is the
    only difference between the two; 1.0 would charge 43% more.
    """

    params_by_root: Mapping[str, FuturesImpactParams] = field(default_factory=dict)
    coefficient: float = DEFAULT_IMPACT_Y

    def __post_init__(self) -> None:
        if not isinstance(self.coefficient, (int, float)) or isinstance(self.coefficient, bool):
            raise FuturesImpactError(f"coefficient must be numeric, got {self.coefficient!r}")
        if not math.isfinite(float(self.coefficient)) or float(self.coefficient) <= 0.0:
            raise FuturesImpactError(
                f"coefficient={self.coefficient!r} must be finite and positive"
            )
        for root, params in self.params_by_root.items():
            if not isinstance(params, FuturesImpactParams):
                raise FuturesImpactError(
                    f"params for {root!r} is a {type(params).__name__}, not FuturesImpactParams"
                )
            if not params.complete:
                raise FuturesImpactError(
                    f"{root}: the {params.line!r} line carries no {', '.join(params.missing())}. "
                    "Choose a line that measures both ADV and sigma."
                )

    # -------------------------------------------------------------- construction

    @classmethod
    def from_table(
        cls,
        root: str,
        *,
        line: str | None = None,
        coefficient: float = DEFAULT_IMPACT_Y,
        table_path: Path | None = None,
    ) -> FuturesSqrtImpact:
        """Build one root's brick from `data/futures_impact_params.json`.

        `line` defaults to the table's `default_line` (`day1m_2016_2023`). Using a line
        outside its measurement window (for example `trades_2025_2026`, measured
        2025-09..2026-09) extrapolates it.
        """
        table = load_impact_table(table_path)
        roots = table["roots"]
        if root not in roots:
            known = ", ".join(sorted(roots)) or "(none)"
            raise FuturesImpactError(
                f"no impact parameters for root {root!r} -- known roots: {known}. A guessed ADV "
                "would produce a cost that is wrong rather than absent."
            )
        entry = roots[root]
        chosen = line or table["default_line"]
        lines = entry["lines"]
        if chosen not in lines:
            known = ", ".join(sorted(lines)) or "(none)"
            raise FuturesImpactError(
                f"{root}: no impact line {chosen!r} -- {root} carries: {known}. The trades_2025_2026 line "
                "covers nine roots only."
            )
        return cls(params_by_root={root: _params_from_json(chosen, lines[chosen])},
                   coefficient=coefficient)

    # -------------------------------------------------------------- the law

    def _params_for(self, instrument: Instrument) -> FuturesImpactParams:
        if not isinstance(instrument, Future):
            raise TypeError(
                f"FuturesSqrtImpact keys its parameters on a futures ROOT and needs a Future, but "
                f"got {type(instrument).__name__}"
                + (f" ({instrument.symbol!r})" if hasattr(instrument, "symbol") else "")
                + ". ADV in contracts and a per-contract sigma are not defined for an instrument "
                "with no contract multiplier; use costs/equity_bricks.py:SqrtImpact for equities."
            )
        params = self.params_by_root.get(instrument.root)
        if params is None:
            known = ", ".join(sorted(self.params_by_root)) or "(none)"
            raise FuturesImpactError(
                f"FuturesSqrtImpact has no impact params for root {instrument.root!r} -- known "
                f"roots: {known}."
            )
        return params

    def impact_fraction(self, instrument: Instrument, quantity: float) -> float:
        """Dimensionless price concession: `Y x sigma_d x sqrt(|Q| / V_d)`.

        Uses the same operation order as `SqrtImpact.impact_fraction`; the test compares the
        two with `==`, and different bracketing can differ by a ULP.
        """
        params = self._params_for(instrument)
        assert params.sigma_fraction is not None and params.adv_contracts is not None
        return self.coefficient * params.sigma_fraction * math.sqrt(
            abs(quantity) / params.adv_contracts
        )

    def impact_for_flow(self, instrument: Instrument, q_rem: float, price: float) -> float:
        """The formula's `I`: a signed move in quoted price points.

        The sign comes from `q_rem`: a buy moves the price up, a sell down. `q_rem == 0`
        returns 0.0 before any parameter lookup, so it does not raise for a root with no
        parameters.
        """
        if q_rem == 0:
            return 0.0
        if not math.isfinite(price):
            raise FuturesImpactError(f"impact_for_flow needs a finite price, got {price!r}")
        sign = 1.0 if q_rem > 0 else -1.0
        return sign * self.impact_fraction(instrument, q_rem) * price

    def impact_usd(self, instrument: Instrument, quantity: float, price: float) -> float:
        """Impact charge in dollars on this fill: `impact_fraction x |notional|`.

        Unsigned, as the `TradeCostBrick` contract requires: a positive amount subtracted from
        P&L for either side. `impact_for_flow` gives the signed price move.
        """
        if quantity == 0:
            return 0.0
        notional = abs(instrument.notional(quantity, price))
        return self.impact_fraction(instrument, quantity) * notional

    def cost(self, instrument: Instrument, quantity: float, price: float) -> float:
        """`TradeCostBrick` entry point; same as `impact_usd`."""
        return self.impact_usd(instrument, quantity, price)


# ------------------------------------------------------------------ depth scaling


def depth_scaled(impact: float, depth_t0: float, depth_bar_value: float) -> float:
    """Scale `impact` by `sqrt(D_bar / D(t0))`.

    Takes an already computed impact, so `I_D` is `I` times one factor and equals `I` when
    `D(t0) = D_bar`. Works on `impact_fraction`, `impact_for_flow` points or `impact_usd`
    dollars; the factor is dimensionless and preserves the sign.

    A thinner book than usual (`D(t0) < D_bar`) scales the impact up.
    """
    for name, value in (("impact", impact), ("depth_t0", depth_t0), ("depth_bar", depth_bar_value)):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise FuturesImpactError(f"depth_scaled: {name} must be numeric, got {value!r}")
        if not math.isfinite(float(value)):
            raise FuturesImpactError(f"depth_scaled: {name} is not finite: {value!r}")
    if depth_t0 <= 0.0:
        raise FuturesImpactError(
            f"depth_scaled: D(t0)={depth_t0!r} must be positive. A depth of zero means "
            "the book could not be read, and dividing by it would give an infinite impact."
        )
    if depth_bar_value <= 0.0:
        raise FuturesImpactError(
            f"depth_scaled: D_bar={depth_bar_value!r} must be positive; a zero trailing depth "
            "would zero the whole impact term."
        )
    if DEPTH_EXPONENT != 0.5:  # pragma: no cover - a fixed constant, not a knob
        raise FuturesImpactError(
            f"DEPTH_EXPONENT is {DEPTH_EXPONENT}; 8A.4 fixes it at 0.5 and `math.sqrt` below is "
            "that exponent written as the operation the standard library rounds correctly."
        )
    return impact * math.sqrt(depth_bar_value / depth_t0)


def depth_bar(
    observations: Sequence[tuple[str, float]],
    day: str,
    lookback_days: int = 20,
    stat: str = "median",
) -> float:
    """`D_bar`: the trailing same-time depth over the `lookback_days` days before `day`.

    `observations` are `(day, depth)` pairs for one root and one minute of day. A row on or
    after `day` is look-ahead and raises rather than being dropped. So do non-positive or
    non-finite depths, duplicate days, and fewer than `lookback_days` prior days.

    The default `stat="median"` matches the formula; `stat="mean"` differs on a right-skewed
    depth series.
    """
    if stat not in ("median", "mean"):
        raise FuturesImpactError(f"depth_bar: stat must be 'median' or 'mean', got {stat!r}")
    if lookback_days <= 0:
        raise FuturesImpactError(f"depth_bar: lookback_days must be positive, got {lookback_days}")
    leaked = sorted({d for d, _ in observations if d >= day})
    if leaked:
        raise FuturesImpactError(
            f"depth_bar: {len(leaked)} observation(s) at or after the evaluation day {day} reached "
            f"the trailing window, first {leaked[0]}. D_bar is a prior-days quantity; "
            "a same-day depth in it is look-ahead."
        )
    for d, value in observations:
        if not math.isfinite(value) or value <= 0.0:
            raise FuturesImpactError(
                f"depth_bar: depth on {d} is {value!r}; a non-positive or non-finite depth cannot "
                "enter a trailing average that something will later divide by."
            )
    days = [d for d, _ in observations]
    if len(set(days)) != len(days):
        dup = sorted({d for d in days if days.count(d) > 1})
        raise FuturesImpactError(
            f"depth_bar: {len(dup)} day(s) appear twice in the trailing window, first {dup[0]}. "
            "One (root, minute, day) is one observation; a repeat double-weights that day."
        )
    prior = sorted(observations)[-lookback_days:]
    if len(prior) < lookback_days:
        raise FuturesImpactError(
            f"depth_bar: only {len(prior)} prior day(s) before {day}, and the window asks for "
            f"{lookback_days}. Skip the day or pass a shorter lookback."
        )
    values = sorted(v for _, v in prior)
    if stat == "mean":
        return math.fsum(values) / len(values)
    n = len(values)
    return values[n // 2] if n % 2 else 0.5 * (values[n // 2 - 1] + values[n // 2])


# ------------------------------------------------------------------ the table


def _params_from_json(line: str, entry: Mapping[str, Any]) -> FuturesImpactParams:
    return FuturesImpactParams(
        line=line,
        window=(str(entry["window"][0]), str(entry["window"][1])),
        provenance=tuple(str(p) for p in entry["provenance"]),
        adv_contracts=entry.get("adv_contracts"),
        sigma_usd_per_contract=entry.get("sigma_usd_per_contract"),
        sigma_fraction=entry.get("sigma_fraction"),
        notional_usd=entry.get("notional_usd"),
    )


@lru_cache(maxsize=4)
def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FuturesImpactError(
            f"{path} is missing. The futures impact brick reads its parameters from this table "
            "and does not fall back to a hardcoded ADV."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "roots" not in data or "default_line" not in data:
        raise FuturesImpactError(f"{path} is not an impact parameter table")
    return data


def load_impact_table(path: Path | None = None) -> dict[str, Any]:
    """Return the parsed parameter table, cached by path like `futures_bricks.load_cost_table`."""
    return _load(path or TABLE_PATH)


def impact_params(root: str, line: str | None = None,
                  table_path: Path | None = None) -> FuturesImpactParams:
    """Return one (root, line)'s parameters; raises as `from_table` does."""
    table = load_impact_table(table_path)
    if root not in table["roots"]:
        known = ", ".join(sorted(table["roots"])) or "(none)"
        raise FuturesImpactError(f"no impact parameters for root {root!r} -- known roots: {known}")
    lines = table["roots"][root]["lines"]
    chosen = line or table["default_line"]
    if chosen not in lines:
        known = ", ".join(sorted(lines)) or "(none)"
        raise FuturesImpactError(f"{root}: no impact line {chosen!r} -- {root} carries: {known}")
    return _params_from_json(chosen, lines[chosen])
