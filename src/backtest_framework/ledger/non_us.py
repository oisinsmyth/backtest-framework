"""P9: the non-US leveraged commodity ETPs, their FX, their index month, the restrike (D611).

WHAT THIS IS
------------
`SETTLEMENT_FLOW_LEDGER_PREREG.md` Section 3.1b (lines 72-84) and participant P9 (lines
276-297). These products are small and they carry the document's largest rebalance factor:
`L(L-1)` is 6 for a +3x product and 12 for a -3x, against 2 and 6 for the US +/-2x funds
(line 297), so a EUR 50m share line moves more of the settlement window on a big day than
its size suggests.

THE PRODUCT TABLE IS INDICATIVE AND SAYS SO
-------------------------------------------
Line 74, verbatim::

    Initial research findings (September 2026). **All figures are indicative and must be
    re-sourced point-in-time.**

Every `Product` constant below therefore carries a `status` string that repeats that
sentence, and every field the table marks "to source" or "verify" is `None` rather than a
plausible value. Four of the eight carry no `index_month_rule` or no `restrike_threshold`
for exactly that reason, and the functions that need them RAISE. Section 0 instruction 3:
*"Never fabricate data or facts."*

THE FORMULAS, QUOTED
--------------------
P9, lines 281-290 (the document's `Delta` is spelled `d`, its multiplication sign `x`, its
U+2212 minus `-`)::

    L_eff,f[t]  = effective leverage on day t
                  BetaPro: from published notional exposure / NAV where available; else
                  stated L with a flag (decision D19)
                  WisdomTree: stated +/-3
    dH_f        = AUM_f,USD[t-1] x L_eff,f x (L_eff,f - 1) x r_idx,f[t, tau]
    Q9          = sum_f dH_f x (1 - n9) / (multiplier x P_held)

    - `AUM_f,USD` uses the FX rate (CAD, EUR, GBP) at the prior day's settlement,
      point-in-time.
    - `r_idx,f` uses the product's **own index contract month**: front month for BetaPro,
      2nd-front month for WisdomTree NG. Flow is mapped to that month (consistent with D2).
    - `n9` = netting fraction for these swap providers, estimated separately from P2's `n`
      (different banks, different books).

Lines 292-294, the restrike::

    **Restrike events (WisdomTree 3x products):** if the product's intraday value falls by
    the threshold (20%), the swap resets exposure intraday. For a +/-3x product this
    corresponds to an adverse underlying move of about 6.67% from the prior reset. At that
    moment the forced rebalance dH is executed **intraday**, not at settlement, and the
    settlement-window flow is recomputed from the restrike level.
    - Restrike times are computable from futures prices and the product terms.
    - They're logged as `restrike_events.csv` with timestamp, product and estimated dH.

WHAT "FALLS BY THE THRESHOLD" IS MEASURED ON, WHICH THE DOCUMENT FIXES AND IT IS WORTH SAYING
----------------------------------------------------------------------------------------------
The threshold is on the PRODUCT's intraday value -- "if the product's intraday value falls
by the threshold (20%)" -- and the 6.67% is the UNDERLYING move that produces it at 3x. The
two are one sentence apart and they are different quantities; `Restrike.check` takes the
product value and `underlying_trigger` reports `threshold / |L|` as the derived figure.
`product_value` is the bridge, `level x (1 + L x r_underlying)`, and required unit test 29's
-6.7% / -6.5% pair is stated in underlying terms and asserted through it. At L = -3 the
adverse move is a RISE in the underlying and the same arithmetic covers it, because the
product's value is what falls in both.

WHAT IS NOT HERE
----------------
No AUM, no NAV, no units, no FX series and no published notional -- those are the deposit's
"P9 products (BetaPro, WisdomTree): NAV, units, effective leverage, FX, restrike terms",
which the infrastructure tracker records as missing. No `n9`: it is a fitted parameter in
[0, 1] (Section 8 line 472) and nothing has fitted it. `q9` takes it as an argument and
refuses a value outside the interval.
"""

from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Sequence

from .funds import FundModelError

__all__ = [
    "BETAPRO_HND",
    "BETAPRO_HNU",
    "BETAPRO_HOD",
    "BETAPRO_HOU",
    "INDICATIVE",
    "NON_US_PRODUCTS",
    "NonUsError",
    "Product",
    "Restrike",
    "RestrikeEvent",
    "RestrikeLog",
    "WT_3NGL",
    "WT_3NGS",
    "WT_3OIL",
    "WT_3OIS",
    "aum_usd",
    "delta_h",
    "effective_leverage",
    "fx_rate_prior",
    "index_month",
    "product_value",
    "q9",
    "recompute_delta_h_from_restrike",
]


class NonUsError(FundModelError):
    """A P9 input was impossible, or a product fact the table marks "to source" was read."""


#: Line 74, carried on every constant so the warning travels with the object rather than
#: living in a docstring nobody reads at the call site.
INDICATIVE = "indicative, re-source point-in-time"

ISSUERS = ("BetaPro", "WisdomTree")
INDEX_MONTH_RULES = ("front", "second_front")


@dataclass(frozen=True)
class Product:
    """One Section 3.1b product.

    `stated_L` is the table's exposure. For BetaPro it is the "up to" figure and the table
    says so -- *"Leverage is 'up to 2x' at manager discretion"*, line 78 -- which is why
    `effective_leverage` exists and why its flag matters: the stated number is a CEILING for
    these four, not a measurement.

    `index_month_rule` is `None` wherever line 289 does not give one. It gives "front month
    for BetaPro, 2nd-front month for WisdomTree NG" and says nothing about WisdomTree WTI, so
    3OIL and 3OIS carry no rule and `index_month` raises for them.

    `restrike_threshold` is 0.20 only for the one product line 80 states it for. Lines 81-82
    say "Verify existence, index and restrike terms" for the other three WisdomTree lines, so
    they carry `None` and a restrike cannot be checked on them by accident.
    """

    name: str
    issuer: str
    stated_L: int
    currency: str
    listing: str
    index_month_rule: str | None
    restrike_threshold: float | None
    status: str
    underlying: str

    def __post_init__(self) -> None:
        if not self.name:
            raise NonUsError("Product needs a name")
        if self.issuer not in ISSUERS:
            raise NonUsError(f"{self.name}: issuer {self.issuer!r} is not one of {ISSUERS}")
        if not isinstance(self.stated_L, int) or isinstance(self.stated_L, bool):
            raise NonUsError(f"{self.name}: stated_L must be an int, got {self.stated_L!r}")
        if self.stated_L == 0:
            raise NonUsError(f"{self.name}: stated_L = 0 is not a leveraged product")
        if not self.currency or not self.listing or not self.underlying:
            raise NonUsError(f"{self.name}: currency, listing and underlying are all required")
        if self.index_month_rule is not None and self.index_month_rule not in INDEX_MONTH_RULES:
            raise NonUsError(
                f"{self.name}: index_month_rule {self.index_month_rule!r} is not one of "
                f"{INDEX_MONTH_RULES} or None (line 289 names exactly two)"
            )
        if self.restrike_threshold is not None:
            if not math.isfinite(self.restrike_threshold) or not 0.0 < self.restrike_threshold < 1.0:
                raise NonUsError(
                    f"{self.name}: restrike_threshold {self.restrike_threshold!r} is not a "
                    f"fraction in (0, 1). Line 292's threshold is 20%, written 0.20."
                )
        if not self.status:
            raise NonUsError(
                f"{self.name}: status is empty. Line 74 marks every figure in Section 3.1b "
                f"indicative, and a product constant that does not carry that warning is a "
                f"sourced fact this repository has not sourced."
            )


# Lines 78-79. BetaPro, TSX, CAD, front-month index (line 289), "up to" leverage at manager
# discretion, no restrike term in the table.
_BETAPRO_STATUS = (
    f"{INDICATIVE}; leverage is 'up to 2x' at manager discretion and may change with market "
    f"conditions and counterparty negotiations (line 78); hedge route to verify "
    f"(swaps/forwards vs futures); HND, HOU and HOD sizes to source"
)
BETAPRO_HNU = Product(
    name="HNU",
    issuer="BetaPro",
    stated_L=2,
    currency="CAD",
    listing="TSX",
    index_month_rule="front",
    restrike_threshold=None,
    status=_BETAPRO_STATUS,
    underlying="NG",
)
BETAPRO_HND = Product(
    name="HND",
    issuer="BetaPro",
    stated_L=-2,
    currency="CAD",
    listing="TSX",
    index_month_rule="front",
    restrike_threshold=None,
    status=_BETAPRO_STATUS,
    underlying="NG",
)
BETAPRO_HOU = Product(
    name="HOU",
    issuer="BetaPro",
    stated_L=2,
    currency="CAD",
    listing="TSX",
    index_month_rule="front",
    restrike_threshold=None,
    status=_BETAPRO_STATUS,
    underlying="CL",
)
BETAPRO_HOD = Product(
    name="HOD",
    issuer="BetaPro",
    stated_L=-2,
    currency="CAD",
    listing="TSX",
    index_month_rule="front",
    restrike_threshold=None,
    status=_BETAPRO_STATUS,
    underlying="CL",
)

# Lines 80-82. WisdomTree, LSE / Xetra / Borsa Italiana, EUR share lines quoted in the table,
# swap-routed, 2nd-front NYMEX index for the NG products (line 289).
WT_3NGL = Product(
    name="3NGL",
    issuer="WisdomTree",
    stated_L=3,
    currency="EUR",
    listing="LSE/Xetra/Borsa Italiana",
    index_month_rule="second_front",
    restrike_threshold=0.20,
    status=(
        f"{INDICATIVE}; share lines 3NGL/NGXL, roughly EUR 48-69m across them (line 80); "
        f"fully collateralised swap, BNP Paribas Arbitrage REPORTED as swap provider"
    ),
    underlying="NG",
)
WT_3NGS = Product(
    name="3NGS",
    issuer="WisdomTree",
    stated_L=-3,
    currency="EUR",
    listing="LSE/Xetra/Borsa Italiana",
    index_month_rule="second_front",
    restrike_threshold=None,
    status=(
        f"{INDICATIVE}; line 81: 'Verify existence, index and restrike terms'. Size to "
        f"source; restrike_threshold left None rather than copied across from 3NGL"
    ),
    underlying="NG",
)
WT_3OIL = Product(
    name="3OIL",
    issuer="WisdomTree",
    stated_L=3,
    currency="EUR",
    listing="LSE/Xetra/Borsa Italiana",
    index_month_rule=None,
    restrike_threshold=None,
    status=(
        f"{INDICATIVE}; line 82: 'Verify existence, index and restrike terms'. Line 289 gives "
        f"an index month rule for WisdomTree NG only, so this carries none"
    ),
    underlying="CL",
)
WT_3OIS = Product(
    name="3OIS",
    issuer="WisdomTree",
    stated_L=-3,
    currency="EUR",
    listing="LSE/Xetra/Borsa Italiana",
    index_month_rule=None,
    restrike_threshold=None,
    status=(
        f"{INDICATIVE}; line 82: 'Verify existence, index and restrike terms'. Line 289 gives "
        f"an index month rule for WisdomTree NG only, so this carries none"
    ),
    underlying="CL",
)

#: The eight of Section 3.1b, in the table's own order. NGXL is 3NGL's second share line
#: (line 80 writes them as one row, "3NGL/NGXL") and is not a ninth product.
NON_US_PRODUCTS: dict[str, Product] = {
    p.name: p
    for p in (
        BETAPRO_HNU,
        BETAPRO_HND,
        BETAPRO_HOU,
        BETAPRO_HOD,
        WT_3NGL,
        WT_3NGS,
        WT_3OIL,
        WT_3OIS,
    )
}


def effective_leverage(
    published_notional: float | None, nav: float, stated_L: int
) -> tuple[float, bool]:
    """Line 282, decision D19: published notional / NAV where available, else stated L, flagged.

    Returns `(L_eff, flagged)`. `flagged` is True exactly when the published notional was
    missing and the stated leverage was substituted -- required unit test 30 -- because for
    the four BetaPro products the stated figure is an "up to" ceiling (line 78) and a day
    running at 1.4x would be modelled at 2x with no trace unless the flag travels.
    """
    if not isinstance(stated_L, int) or isinstance(stated_L, bool):
        raise NonUsError(f"effective_leverage: stated_L must be an int, got {stated_L!r}")
    if stated_L == 0:
        raise NonUsError("effective_leverage: stated_L = 0 is not a leveraged product")
    if not math.isfinite(nav) or nav <= 0.0:
        raise NonUsError(
            f"effective_leverage: NAV = {nav!r}. It is the denominator of the ratio, and a "
            f"non-positive NAV would return a leverage of the wrong sign or an infinity that "
            f"dH then multiplies by an AUM."
        )
    if published_notional is None:
        return float(stated_L), True
    if not math.isfinite(published_notional):
        raise NonUsError(
            f"effective_leverage: published_notional must be finite or None, got "
            f"{published_notional!r}. None means 'not published for this day' and takes the "
            f"flagged route; a NaN means a parse failure and must not."
        )
    return published_notional / nav, False


def delta_h(aum_usd_prev: float, L_eff: float, r_idx: float) -> float:
    """P9 line 284: `dH_f = AUM_f,USD[t-1] x L_eff,f x (L_eff,f - 1) x r_idx,f[t, tau]`.

    In USD of required notional, signed, in the document's own left-to-right order. Positive
    is a buy for both signs of `L_eff` on a favourable move, which is line 297's point: the
    factor is `L(L-1)`, 6 at +3x and 12 at -3x.

    `aum_usd_prev` is the PRIOR day's AUM, already converted at the prior settlement's FX
    (line 288 -- `aum_usd` below is the conversion and required unit test 27 is that it
    refuses today's rate).
    """
    for label, value in (
        ("aum_usd_prev", aum_usd_prev),
        ("L_eff", L_eff),
        ("r_idx", r_idx),
    ):
        if not math.isfinite(value):
            raise NonUsError(f"delta_h: {label} must be finite, got {value!r}")
    if aum_usd_prev < 0.0:
        raise NonUsError(f"delta_h: AUM cannot be negative, got {aum_usd_prev!r}")
    return aum_usd_prev * L_eff * (L_eff - 1) * r_idx


def q9(delta_h_total: float, n9: float, multiplier: float, p_held: float) -> float:
    """P9 line 285: `Q9 = sum_f dH_f x (1 - n9) / (multiplier x P_held)`, in contracts.

    `delta_h_total` is the sum over products ALREADY TAKEN -- the sum is the caller's, because
    which products are in it on a given day is a data question (line 84: further candidates
    are out of scope until the table is verified) and not an arithmetic one.

    `n9` is the swap providers' netting fraction, in [0, 1] per Section 8 line 472, and
    "estimated separately from P2's `n` (different banks, different books)" (line 290).
    Nothing has estimated it; this function refuses a value outside the interval and has no
    default.
    """
    for label, value in (
        ("delta_h_total", delta_h_total),
        ("n9", n9),
        ("multiplier", multiplier),
        ("p_held", p_held),
    ):
        if not math.isfinite(value):
            raise NonUsError(f"q9: {label} must be finite, got {value!r}")
    if not 0.0 <= n9 <= 1.0:
        raise NonUsError(
            f"q9: n9 = {n9!r} is outside [0, 1] (Section 8 line 472). Above 1 the netting "
            f"flips the sign of the flow; below 0 it invents flow that no product owes."
        )
    if multiplier <= 0.0:
        raise NonUsError(f"q9: multiplier must be positive, got {multiplier!r}")
    if p_held <= 0.0:
        raise NonUsError(f"q9: p_held must be positive, got {p_held!r}")
    return delta_h_total * (1 - n9) / (multiplier * p_held)


def fx_rate_prior(fx_by_day: Mapping[str, float], day: dt.date) -> tuple[dt.date, float]:
    """Line 288: the FX rate at the PRIOR day's settlement, point-in-time.

    `fx_by_day` maps an ISO date string to USD per one unit of the local currency. The rate
    returned is the one on the latest key STRICTLY BEFORE `day`; if the only rates available
    are for `day` itself or later, this raises. That is required unit test 27, and it is a
    raise rather than a fallback because the fallback -- "use today's if yesterday's is
    missing" -- is precisely the look-ahead the line exists to forbid, and on a big move day
    the two rates differ by the move.

    Returns `(rate_day, rate)` so the caller can record which settlement was used.
    """
    if not isinstance(day, dt.date) or isinstance(day, dt.datetime):
        raise NonUsError(f"fx_rate_prior: day must be a date (not a datetime), got {day!r}")
    if not fx_by_day:
        raise NonUsError("fx_rate_prior: no FX rates given")
    best_day: dt.date | None = None
    best_rate = math.nan
    for key, rate in fx_by_day.items():
        try:
            parsed = dt.date.fromisoformat(key)
        except (TypeError, ValueError) as exc:
            raise NonUsError(f"fx_rate_prior: {key!r} is not an ISO date") from exc
        if not math.isfinite(rate) or rate <= 0.0:
            raise NonUsError(f"fx_rate_prior: rate for {key} is {rate!r}; it must be positive")
        if parsed < day and (best_day is None or parsed > best_day):
            best_day, best_rate = parsed, rate
    if best_day is None:
        raise NonUsError(
            f"fx_rate_prior: no FX rate dated before {day}; the earliest available is "
            f"{min(fx_by_day)}. Line 288 uses the PRIOR day's settlement, and using the "
            f"current day's rate would price a foreign AUM at a rate struck after the move "
            f"the rebalance is a response to."
        )
    return best_day, best_rate


def aum_usd(aum_local: float, fx_by_day: Mapping[str, float], day: dt.date) -> float:
    """`AUM_f,USD` of line 288: local AUM at the prior settlement's rate.

    `fx_by_day` is USD per one unit of `aum_local`'s currency (CAD, EUR, GBP).
    """
    if not math.isfinite(aum_local) or aum_local < 0.0:
        raise NonUsError(f"aum_usd: aum_local must be finite and non-negative, got {aum_local!r}")
    _, rate = fx_rate_prior(fx_by_day, day)
    return aum_local * rate


def index_month(product: Product, curve: Sequence[str]) -> str:
    """Line 289: "front month for BetaPro, 2nd-front month for WisdomTree NG".

    `curve` is the product's own index curve in ascending maturity, front first, as contract
    month codes. Returns the code the product's flow is mapped to (consistent with decision
    D2: flow goes to the month actually held, never to the front by default).

    Raises for a product whose rule the document does not give -- 3OIL and 3OIS -- and for a
    curve too short to have the month the rule names. Both are the same refusal: picking the
    front month "because it is there" is how flow from a 2nd-front product lands on the wrong
    contract and the mapping error is invisible in the total.
    """
    if not isinstance(product, Product):
        raise NonUsError(f"index_month: expected a Product, got {product!r}")
    if product.index_month_rule is None:
        raise NonUsError(
            f"index_month: {product.name} has no index month rule. Line 289 gives one for "
            f"BetaPro (front) and for WisdomTree NG (2nd-front) and for nothing else; "
            f"{product.name}'s index is marked 'verify' in Section 3.1b."
        )
    needed = 1 if product.index_month_rule == "front" else 2
    if len(curve) < needed:
        raise NonUsError(
            f"index_month: {product.name} needs the {product.index_month_rule} month and the "
            f"curve has {len(curve)} contract(s)"
        )
    for code in curve[:needed]:
        if not code:
            raise NonUsError(f"index_month: {product.name} curve has an empty contract code")
    return curve[needed - 1]


def product_value(last_reset_level: float, L: int, r_underlying: float) -> float:
    """The product's intraday value after an underlying move, from its last reset level.

        value = last_reset_level x (1 + L x r_underlying)

    The bridge between line 292's two quantities: the threshold is on the PRODUCT's value and
    the 6.67% is the UNDERLYING move that reaches it at 3x. This is the daily-leverage
    identity within one reset period, which is what "from the prior reset" means.
    """
    if not isinstance(L, int) or isinstance(L, bool):
        raise NonUsError(f"product_value: L must be an int, got {L!r}")
    if not math.isfinite(last_reset_level) or last_reset_level <= 0.0:
        raise NonUsError(f"product_value: last_reset_level must be positive, got {last_reset_level!r}")
    if not math.isfinite(r_underlying):
        raise NonUsError(f"product_value: r_underlying must be finite, got {r_underlying!r}")
    return last_reset_level * (1 + L * r_underlying)


@dataclass(frozen=True)
class RestrikeEvent:
    """One restrike: what fell, by how much, and the level the next period measures from."""

    drawdown: float
    """`(value - last_reset_level) / last_reset_level`, negative, at or beyond -threshold."""
    new_reset_level: float
    """The product value at the restrike. Line 292: the window flow is recomputed from here."""
    threshold: float
    L: int
    timestamp: dt.datetime | None = None
    product: str | None = None
    estimated_dh: float | None = None
    """Line 294's third column. `None` until an AUM exists to compute it from."""


@dataclass(frozen=True)
class Restrike:
    """Line 292's rule for one product: a 20% fall in the PRODUCT's intraday value.

    `underlying_trigger` is `threshold / |L|` -- 0.2 / 3 = 0.06666666666666667, the document's
    "about 6.67%". It is DERIVED and reported; the check is on the product value, because
    that is what the swap terms reset on.
    """

    threshold: float = 0.20
    L: int = 3

    def __post_init__(self) -> None:
        if not isinstance(self.L, int) or isinstance(self.L, bool):
            raise NonUsError(f"Restrike: L must be an int, got {self.L!r}")
        if self.L == 0:
            raise NonUsError("Restrike: L = 0 has no restrike")
        if not math.isfinite(self.threshold) or not 0.0 < self.threshold < 1.0:
            raise NonUsError(
                f"Restrike: threshold {self.threshold!r} is not a fraction in (0, 1); line 292 "
                f"writes 20% as 0.20"
            )

    @property
    def underlying_trigger(self) -> float:
        """`threshold / |L|`: the adverse UNDERLYING move that reaches the threshold."""
        return self.threshold / abs(self.L)

    def check(
        self,
        intraday_value: float,
        last_reset_level: float,
        *,
        timestamp: dt.datetime | None = None,
        product: str | None = None,
    ) -> RestrikeEvent | None:
        """`RestrikeEvent` when the product value has fallen by AT LEAST the threshold, else None.

            drawdown = (intraday_value - last_reset_level) / last_reset_level
            fires when drawdown <= -threshold

        Inclusive at exactly -threshold. The new reset level is the value at the restrike, so
        the next period's drawdown is measured from there (line 292: "from the prior reset").
        """
        if not math.isfinite(last_reset_level) or last_reset_level <= 0.0:
            raise NonUsError(
                f"Restrike.check: last_reset_level must be positive, got {last_reset_level!r}"
            )
        if not math.isfinite(intraday_value):
            raise NonUsError(f"Restrike.check: intraday_value must be finite, got {intraday_value!r}")
        drawdown = (intraday_value - last_reset_level) / last_reset_level
        if drawdown > -self.threshold:
            return None
        return RestrikeEvent(
            drawdown=drawdown,
            new_reset_level=intraday_value,
            threshold=self.threshold,
            L=self.L,
            timestamp=timestamp,
            product=product,
        )


def recompute_delta_h_from_restrike(
    aum_at_restrike: float, L: float, r_from_restrike: float
) -> float:
    """Line 292: after a restrike, the settlement-window flow is recomputed FROM the restrike level.

    The same `dH` of line 284, with the AUM and the return both measured from the restrike
    rather than from the prior settlement. A separate name rather than a comment at the call
    site, because the difference between the two is the entire content of the sentence: the
    return that matters after a restrike is the one since the reset, and reusing the
    settlement-to-tau return would double-count the move that caused the restrike.
    """
    return delta_h(aum_at_restrike, L, r_from_restrike)


@dataclass
class RestrikeLog:
    """Line 294: `restrike_events.csv` with timestamp, product and estimated dH.

    Mutable by design -- events are appended as a session is scanned -- and it writes ONLY to
    the path the caller names. There is no default path and no `data/` location: nothing here
    has produced a real restrike, and a module that knew where to put one would create an
    empty artefact that reads like a measurement.
    """

    events: list[RestrikeEvent] = field(default_factory=list)

    HEADER = ("timestamp", "product", "estimated_dH")

    def add(self, event: RestrikeEvent) -> None:
        if not isinstance(event, RestrikeEvent):
            raise NonUsError(f"RestrikeLog.add: expected a RestrikeEvent, got {event!r}")
        if event.timestamp is None or event.product is None:
            raise NonUsError(
                "RestrikeLog.add: line 294's row is timestamp, product and estimated dH; an "
                "event with no timestamp or no product cannot be written as one."
            )
        self.events.append(event)

    def write(self, path: Path) -> Path:
        """Write the CSV to `path`. Refuses to overwrite; returns the path written.

        ASCII, LF endings, UTF-8, `timestamp` as ISO 8601. `estimated_dH` is written as the
        empty string when it is None -- an event whose dH nobody computed is not an event of
        zero dollars, and the column would read as the latter.
        """
        path = Path(path)
        if path.exists():
            raise NonUsError(
                f"RestrikeLog.write: {path} exists. A restrike log is evidence of what the "
                f"detector found on a run; overwriting one silently replaces that record."
            )
        lines = [",".join(self.HEADER)]
        for e in self.events:
            assert e.timestamp is not None and e.product is not None  # add() enforces both
            if "," in e.product:
                raise NonUsError(f"RestrikeLog.write: product {e.product!r} contains a comma")
            dh = "" if e.estimated_dh is None else repr(e.estimated_dh)
            lines.append(f"{e.timestamp.isoformat()},{e.product},{dh}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        return path
