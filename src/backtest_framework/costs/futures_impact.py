"""Square-root market impact for FUTURES, and its depth-scaled variant (D604).

THE GAP THIS CLOSES
-------------------
`costs/equity_bricks.py:SqrtImpact` is the repository's square-root impact law (D3, D66). It
keys its parameters on `instrument.symbol`, and `instruments/future.py:Future` has no `symbol`
-- it carries a `root`. So `SqrtImpact.cost(Future(...), q, p)` does not charge a futures impact
at a default; it RAISES, in `_params_for`, on the missing attribute. Every futures study here has
therefore run with commission and tick crossing (D591) and NO impact term at all, which is
sound at one contract and wrong the moment a size question is asked.

This module is that law with a futures parameter set, keyed on `Future.root`. It is deliberately
the SAME arithmetic: `test_futures_impact.py` builds a `SqrtImpact` on the same two numbers and
asserts the two fractions are equal bit-for-bit on hypothesis-drawn inputs. A second
implementation of a published formula that merely agreed to a tolerance would be a new formula.

THE TWO FORMULAS, QUOTED
------------------------
`SETTLEMENT_FLOW_LEDGER_PREREG.md` Section 5.3, *Predicted move*, verbatim::

    V_d  = 20-day trailing mean daily volume of the traded contract (days t-20 ... t-1)
    sigma_d  = 20-day trailing daily return std
    I    = Y x sigma_d x sqrt(|Q_rem| / V_d) x P x sign(Q_rem)       (price units)
    SNR  = |Q_rem| / sigma_rem

    **Y = 0.7, fixed** (decision D6).

Section 8A.4, *Depth-based impact (Stage H)*, verbatim::

    From MBO data at t0, measure resting depth `D(t0)` within +/-5 ticks on both sides of the
    traded contract, and its trailing 20-day same-time median `D_bar`.

    I_D = Y x sigma_d x sqrt(|Q_rem| / V_d) x P x sqrt(D_bar / D(t0)) x sign(Q_rem)
          (Y = 0.7 fixed; exponent 0.5 fixed)

    No new fitted parameters. The existing impact definition (5.3) remains the baseline. Stage H
    replaces it **only** if H14 passes.

(The ledger writes the Greek letters and the multiplication signs as such; they are spelled out
here because this file is source and the repository pins its encodings.)

`I_D` is `I` multiplied by `sqrt(D_bar / D(t0))` and by nothing else, so `D(t0) = D_bar` gives
`I_D == I` EXACTLY -- `sqrt(x/x)` is `sqrt(1.0)` is `1.0`, and multiplying a finite double by 1.0
is lossless. That is ledger required unit test 46 and `INDEX_REWEIGHT_FLOW_PREREG.md` required
unit test 18, and `test_futures_impact.py` asserts it with `==`, not with `approx`.

UNITS, WHICH ARE THE EASY THING TO GET WRONG HERE
-------------------------------------------------
- `impact_fraction` is DIMENSIONLESS -- a fraction of the price, the quantity that scales as
  sqrt(Q) (D66).
- `impact_for_flow` returns the ledger's `I`: a SIGNED move in QUOTED PRICE POINTS (index points
  on ES, dollars a barrel on CL), because that is what "price units" means in 5.3.
- `impact_usd` and `cost` return DOLLARS, charged on the trade's own notional
  (`Future.notional` = quantity x price x usd_per_point), so total dollars scale as Q^1.5.
- `adv_contracts` is in CONTRACTS of the root's FULL-SIZE contract, and `quantity` must be in the
  same contracts. A quantity in micros divided by a full-size ADV understates the ratio by the
  size factor; `data/futures_impact_params.json` carries each root's `size` block so a caller
  sizing at the minimum tradable size can see what it is converting between.

WHAT IS NOT MODELLED
--------------------
Temporary versus permanent impact, decay, the participation rate over a window, and the fact
that every parameter line in the table is a WINDOW average rather than the 20-day trailing
quantity 5.3 actually names. The table carries each line's window so the caller can see the
extrapolation it is making; this module is arithmetic and claims nothing about the window.
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
"""The impact parameter table, built by `scripts/futures_impact_table.py --build`.

Every number in it is copied by the builder from a committed artefact key path or from a fixture
it recomputes; nothing in it was typed by hand, and `--selftest` re-derives the whole file and
compares the committed bytes by sha256.
"""

LEDGER_Y = 0.7
"""`Y = 0.7, fixed` (SETTLEMENT_FLOW_LEDGER_PREREG.md 5.3, decision D6). A default, not a
parameter to fit: the ledger registers no free coefficient for the impact model, and Stage H
(8A.4) adds none."""

DEPTH_EXPONENT = 0.5
"""`exponent 0.5 fixed` (8A.4). Present as a named constant so that a reader looking for the
fitted parameter finds the sentence saying there is not one."""


class FuturesImpactError(ValueError):
    """An impact parameter was asked for and does not exist, or exists incomplete.

    Its own class, like `FuturesCostError`, so a caller can tell "this root has no measured ADV"
    from a generic ValueError raised inside the arithmetic. It never returns a default: an impact
    number that is merely plausible still produces a Sharpe (D48).
    """


# ------------------------------------------------------------------ parameters


@dataclass(frozen=True)
class FuturesImpactParams:
    """One root's impact inputs on ONE measurement line.

    `adv_contracts` and `sigma_fraction` are the two the law reads. `sigma_usd_per_contract` and
    `notional_usd` are carried because they are what the sources actually measure and because
    `sigma_fraction` is their quotient -- keeping all four means a reader can check the division
    instead of taking it.

    THREE FIELDS ARE OPTIONAL AND THAT IS THE POINT. Not every committed source measures all four.
    `data/fixtures/fut_breadth_hourly.meta.json` carries a day-session sigma and a notional but no
    volume at all, so its line has `adv_contracts = None`. Storing the line with a hole in it, and
    refusing at the point of USE, is the D48 shape: the alternative is either dropping a measured
    sigma or filling the ADV from a different window and letting the join disappear into a float.
    """

    line: str
    """Which measurement this is -- `d511`, `breadth_meta`, `day1m_2016_2023`."""
    window: tuple[str, str]
    """The measurement window, inclusive, as ISO dates."""
    provenance: tuple[str, ...]
    """One entry per number: `file#key/path` or `script:line`. Never empty."""
    adv_contracts: float | None = None
    """Average daily volume in FULL-SIZE contracts of the root's front contract."""
    sigma_usd_per_contract: float | None = None
    """Session move standard deviation, in dollars on one FULL-SIZE contract."""
    sigma_fraction: float | None = None
    """The same sigma as a fraction of contract notional -- the ledger's `sigma_d`."""
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
                    f"{self.line}: {name}={value!r} must be finite and positive; a zero or missing "
                    "ADV or sigma must be a loud error, not a silent zero cost (D48)"
                )

    @property
    def complete(self) -> bool:
        """True when this line carries BOTH quantities the law reads."""
        return self.adv_contracts is not None and self.sigma_fraction is not None

    def missing(self) -> tuple[str, ...]:
        return tuple(n for n in ("adv_contracts", "sigma_fraction") if getattr(self, n) is None)


# ------------------------------------------------------------------ the brick


@dataclass(frozen=True)
class FuturesSqrtImpact:
    """Square-root impact on futures, keyed on `Future.root`, against the D1 `TradeCostBrick`
    interface.

    `coefficient` defaults to the ledger's fixed `Y = 0.7`, NOT to `SqrtImpact`'s order-of-
    magnitude 1.0. The two modules deliberately differ here and only here: 5.3 registers 0.7 as a
    decision (D6), and a futures brick that silently used 1.0 would charge 43% more than the
    document it implements.
    """

    params_by_root: Mapping[str, FuturesImpactParams] = field(default_factory=dict)
    coefficient: float = LEDGER_Y

    def __post_init__(self) -> None:
        if not isinstance(self.coefficient, (int, float)) or isinstance(self.coefficient, bool):
            raise FuturesImpactError(f"coefficient must be numeric, got {self.coefficient!r}")
        if not math.isfinite(float(self.coefficient)) or float(self.coefficient) <= 0.0:
            raise FuturesImpactError(
                f"coefficient={self.coefficient!r} must be finite and positive; zero would silently "
                "zero the whole brick (D48)"
            )
        for root, params in self.params_by_root.items():
            if not isinstance(params, FuturesImpactParams):
                raise FuturesImpactError(
                    f"params for {root!r} is a {type(params).__name__}, not FuturesImpactParams"
                )
            if not params.complete:
                raise FuturesImpactError(
                    f"{root}: the {params.line!r} line carries no {', '.join(params.missing())}. "
                    "It is a real measurement with a hole in it, not a usable impact parameter -- "
                    "choose a line that measures both, or the brick would charge a number the "
                    "source never measured."
                )

    # -------------------------------------------------------------- construction

    @classmethod
    def from_table(
        cls,
        root: str,
        *,
        line: str | None = None,
        coefficient: float = LEDGER_Y,
        table_path: Path | None = None,
    ) -> FuturesSqrtImpact:
        """Build one root's brick from `data/futures_impact_params.json`.

        `line` defaults to the table's own `default_line`, which is the IN-SAMPLE measurement
        (`day1m_2016_2023`). The other two lines are measured on 2025-09..2026-09, inside the
        deposit's sealed vault window, and a study that reaches for one is making a claim the
        table cannot make for it.
        """
        table = load_impact_table(table_path)
        roots = table["roots"]
        if root not in roots:
            known = ", ".join(sorted(roots)) or "(none)"
            raise FuturesImpactError(
                f"no impact parameters for root {root!r} -- known roots: {known}. A guessed ADV "
                "would produce a cost that is wrong rather than absent (D48)."
            )
        entry = roots[root]
        chosen = line or table["default_line"]
        lines = entry["lines"]
        if chosen not in lines:
            known = ", ".join(sorted(lines)) or "(none)"
            raise FuturesImpactError(
                f"{root}: no impact line {chosen!r} -- {root} carries: {known}. The d511 line "
                "covers nine roots only; naming it for a tenth must raise rather than fall back "
                "to a neighbouring window."
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
                f"roots: {known}. Missing ADV must be a loud error, not a silent zero cost (D48)."
            )
        return params

    def impact_fraction(self, instrument: Instrument, quantity: float) -> float:
        """The dimensionless price concession: `Y x sigma_d x sqrt(|Q| / V_d)`.

        Written in exactly the association `SqrtImpact.impact_fraction` uses, because the golden
        test asserts the two are equal with `==`: change the bracketing and a ULP appears.
        """
        params = self._params_for(instrument)
        assert params.sigma_fraction is not None and params.adv_contracts is not None
        return self.coefficient * params.sigma_fraction * math.sqrt(
            abs(quantity) / params.adv_contracts
        )

    def impact_for_flow(self, instrument: Instrument, q_rem: float, price: float) -> float:
        """The ledger's `I`: a SIGNED move in QUOTED PRICE POINTS (5.3).

        `sign(Q_rem)` is taken from the signed flow and nothing else, so a buy pushes the price up
        and a sell down. **Zero `Q_rem` gives exactly zero** -- ledger required unit test 7 -- and
        it gives it without evaluating `sqrt(0/V_d)`, so a root whose ADV were somehow absent
        still returns zero for a zero order rather than raising on a parameter no trade needed.
        """
        if q_rem == 0:
            return 0.0
        if not math.isfinite(price):
            raise FuturesImpactError(f"impact_for_flow needs a finite price, got {price!r}")
        sign = 1.0 if q_rem > 0 else -1.0
        return sign * self.impact_fraction(instrument, q_rem) * price

    def impact_usd(self, instrument: Instrument, quantity: float, price: float) -> float:
        """The impact charge in DOLLARS on this fill: `impact_fraction x |notional|`.

        Unsigned, because it is a COST: the D1 `TradeCostBrick` contract is that `cost` is a
        positive number subtracted from P&L whichever way the trade went. The signed price move is
        `impact_for_flow`.
        """
        if quantity == 0:
            return 0.0
        notional = abs(instrument.notional(quantity, price))
        return self.impact_fraction(instrument, quantity) * notional

    def cost(self, instrument: Instrument, quantity: float, price: float) -> float:
        """`TradeCostBrick`. Identical to `impact_usd`; both names exist because the protocol
        demands `cost` and the ledger's readers look for `impact`."""
        return self.impact_usd(instrument, quantity, price)


# ------------------------------------------------------------------ Stage H


def depth_scaled(impact: float, depth_t0: float, depth_bar_value: float) -> float:
    """Ledger 8A.4: scale `impact` by `sqrt(D_bar / D(t0))`.

    Takes the impact rather than recomputing it, so that `I_D` is literally `I` times one factor
    and the identity at `D(t0) = D_bar` is arithmetic rather than a coincidence of two code paths.
    Works on `impact_fraction`, on `impact_for_flow`'s signed points and on `impact_usd`'s dollars
    alike -- the factor is dimensionless and the sign rides through unchanged.

    A thinner book than usual (`D(t0) < D_bar`) scales the impact UP, which is the direction 8A.4
    intends and the one worth stating, because the ratio is the easy thing to invert.
    """
    for name, value in (("impact", impact), ("depth_t0", depth_t0), ("depth_bar", depth_bar_value)):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise FuturesImpactError(f"depth_scaled: {name} must be numeric, got {value!r}")
        if not math.isfinite(float(value)):
            raise FuturesImpactError(f"depth_scaled: {name} is not finite: {value!r}")
    if depth_t0 <= 0.0:
        raise FuturesImpactError(
            f"depth_scaled: D(t0)={depth_t0!r} must be positive. A zero measured depth is a book "
            "the panel could not read, not a book with no orders in it, and dividing by it would "
            "return inf and charge an infinite impact (D48)."
        )
    if depth_bar_value <= 0.0:
        raise FuturesImpactError(
            f"depth_scaled: D_bar={depth_bar_value!r} must be positive; a zero trailing depth "
            "would zero the whole impact term."
        )
    if DEPTH_EXPONENT != 0.5:  # pragma: no cover - the constant is the document's, not a knob
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
    """`D_bar`: the trailing same-time depth of the `lookback_days` days BEFORE `day`.

    `observations` are `(day, depth)` pairs already restricted to ONE root and ONE minute-of-day --
    8A.4 says "same-time", so a mean over the whole session would be a different statistic.

    **A row at or after `day` RAISES.** It is not filtered out quietly: a same-day row reaching a
    trailing window is the look-ahead ledger required unit test 45 exists to forbid, and a filter
    that silently drops it leaves the caller believing a guard ran (memory:
    `declared-outputs-need-a-guard-not-prose`).

    MEDIAN, AND A DISAGREEMENT RECORDED. 8A.4 writes "trailing 20-day same-time MEDIAN"; D604's
    brief asked for the trailing MEAN. The quoted document wins the default and `stat="mean"` is
    offered beside it, because on a right-skewed depth series the two are not the same number.
    D604 measures the gap on `fut_book_depth_1m` and records it. Whichever a study uses, it must
    say which.
    """
    if stat not in ("median", "mean"):
        raise FuturesImpactError(f"depth_bar: stat must be 'median' or 'mean', got {stat!r}")
    if lookback_days <= 0:
        raise FuturesImpactError(f"depth_bar: lookback_days must be positive, got {lookback_days}")
    leaked = sorted({d for d, _ in observations if d >= day})
    if leaked:
        raise FuturesImpactError(
            f"depth_bar: {len(leaked)} observation(s) at or after the evaluation day {day} reached "
            f"the trailing window, first {leaked[0]}. D_bar is a PRIOR-days quantity (ledger "
            "required unit test 45); a same-day depth in it is look-ahead."
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
            f"{lookback_days}. A short window silently averaged is how a warm-up period becomes a "
            "result; the caller must skip the day or ask for a shorter lookback in writing."
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
            f"{path} is missing. It is built by `scripts/futures_impact_table.py --build` and is "
            "tracked; this module does not fall back to a hardcoded ADV (D48)."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "roots" not in data or "default_line" not in data:
        raise FuturesImpactError(f"{path} is not an impact parameter table")
    return data


def load_impact_table(path: Path | None = None) -> dict[str, Any]:
    """The committed parameter table. Cached on the path, like `futures_bricks.load_cost_table`."""
    return _load(path or TABLE_PATH)


def impact_params(root: str, line: str | None = None,
                  table_path: Path | None = None) -> FuturesImpactParams:
    """One (root, line)'s parameters, raising the same way `from_table` does."""
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
