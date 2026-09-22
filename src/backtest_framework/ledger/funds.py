"""The six US commodity LETFs, the self-computed iNAV, and Gate 0b (D611).

WHAT THIS IS
------------
`SETTLEMENT_FLOW_LEDGER_PREREG.md` (v1.9, untracked, in `docs/internal/User-Doc-Deposit/`)
models the flow that six leveraged commodity ETFs push into the CME natural gas and crude
settlement window. Before any of that can be scored, two objects have to exist and be
right: the fund universe with its leverage and its contract multiplier, and the intraday
fair value the premium is measured against.

This module is those two and nothing else. It reads no data, opens no file and computes no
strategy return; every function is a formula quoted from the document with its line number,
and every test of it is a hand calculation. That is not modesty about scope -- the fund
panel (NAV, shares outstanding, holdings by contract month) does not exist on disk, and
`er` below is `None` on all six funds for exactly that reason.

THE FUND UNIVERSE, QUOTED
-------------------------
Section 3.1 "Fund universe", lines 58-65, verbatim (the document writes the minus sign as
U+2212; this file is source and the repository pins its encodings, so it is spelled `-`)::

    | Fund | Underlying | L | Role |
    |---|---|---|---|
    | BOIL | Natural gas (index-based futures) | +2 | Rebalance + creations |
    | KOLD | Natural gas | -2 | Rebalance + creations |
    | UCO | Crude oil | +2 | Rebalance + creations |
    | SCO | Crude oil | -2 | Rebalance + creations |
    | UNG | Natural gas | +1 | Creations only (L(L-1) = 0) |
    | USO | Crude oil | +1 | Creations only |

The multipliers are NOT in the deposit: they are the contract size of the root each fund
holds, read out of this repository's `data/futures_contract_specs.json`, where
`CL.usd_per_point` is 1000.0 ("1,000 barrels") and `NG.usd_per_point` is 10000.0
("10,000 MMBtu"). They enter the ledger's flow formulas as the `multiplier` in
`Create_flow = L_f x dCreate_f / (multiplier x P_held)` (line 231), which converts USD into
contracts of the held month.

THE iNAV, QUOTED
----------------
Section 4, P3.1 "iNAV (self-computed)", line 184, and the two definitions at 187-188::

    iNAV_f(tau) = NAV_f[t-1] x (1 + L_f x r_held,f(tau)) + NAV_f[t-1] x (y_cash / 360 - ER_f / 365)

    - `r_held,f` = holdings-weighted return of fund f's held contracts from the prior
      settlement to tau.
    - `y_cash` = collateral yield (T-bill rate, point-in-time). `ER_f` = expense ratio.
    - If the prospectus shows NAV is struck on a different price basis (Q10), the formula is
      amended by doc edit before use.

**The two day counts differ and that is deliberate.** Collateral yield accrues ACT/360, the
expense ratio ACT/365, and `inav` below divides by those two constants and no others. A
single `/365` would move a fund's daily accrual by about 1.4% of itself -- invisible in one
day and a systematic drift over a sample, landing straight in Gate 0b's 5 bp budget.

**The accrual is ONE day.** The document writes `y_cash / 360` with no day count multiplier,
which is one day's fraction of an annual rate. A gap of more than one calendar day between
`t-1` and `t` (a weekend, a holiday) accrues more than the formula charges, and nothing here
compensates: the deposit's formula is what this module implements, and the discrepancy is
named in D611 rather than silently fixed with a day count the document does not have.

GATE 0b, QUOTED
---------------
Line 191::

    **Gate 0b (iNAV validation):** per fund, |iNAV at settlement - official NAV[t]| <= 5 bp on
    >= 95% of days. Failures are investigated (holdings timing, roll weights, accrual) before
    any P3 work.

`gate_0b` computes the per-day errors in basis points of the OFFICIAL NAV, counts the share
within the limit, and returns the verdict with both. It is a gate on a fund's arithmetic, so
it never returns a default: a length mismatch, an empty sample or a non-positive NAV raises.

WHAT IS NOT HERE
----------------
No expense ratio, no collateral yield, no creation cut-off, no roll schedule. Those are
Section 3.2 "Fund facts to source and verify (Gate 0)" and instruction 3 of Section 0 --
*"Never fabricate data or facts. This includes fund holdings, creation cut-offs, settlement
window times"*. `Fund.er` is `None` on all six constants and `inav` RAISES when handed
`None`, so a caller cannot reach a number by accident; the value arrives from
`data/fund_facts/` when something has sourced it with a URL and an access date.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

__all__ = [
    "BOIL",
    "CL_MULTIPLIER",
    "KOLD",
    "NG_MULTIPLIER",
    "SCO",
    "UCO",
    "UNG",
    "USO",
    "US_FUNDS",
    "Fund",
    "FundModelError",
    "Gate0b",
    "gate_0b",
    "inav",
]


class FundModelError(ValueError):
    """A fund-model input was impossible, unsourced, or not the thing it claims to be.

    Its own class so a caller can tell "this fund has no sourced expense ratio" from a
    generic `ValueError` raised inside the arithmetic. Nothing in this package returns a
    plausible default in place of a missing fact: a made-up expense ratio still produces an
    iNAV, and an iNAV still produces a premium, a hedged fraction and a trade (D48).
    """


#: `usd_per_point` for CL, `data/futures_contract_specs.json#CL` -- "1,000 barrels".
CL_MULTIPLIER = 1000.0

#: `usd_per_point` for NG, `data/futures_contract_specs.json#NG` -- "10,000 MMBtu".
NG_MULTIPLIER = 10000.0

#: The two day counts of line 184, named so that a reader looking for the asymmetry finds it
#: stated rather than inferring it from two integer literals.
CASH_DAY_COUNT = 360.0
EXPENSE_DAY_COUNT = 365.0

#: Gate 0b's two numbers (line 191).
GATE_0B_BP_LIMIT = 5.0
GATE_0B_SHARE = 0.95


@dataclass(frozen=True)
class Fund:
    """One US fund from Section 3.1, with the contract it converts USD into.

    `L` is an INTEGER because the document's six are, and because the rebalance factor
    `L(L-1)` is what makes UNG and USO creation-only: `1 x 0 = 0` exactly, which a float
    leverage would only reach by luck. `L_eff` for the non-US products IS a float and lives
    in `ledger/non_us.py`, where the deposit says it is a ratio of two published numbers.

    `er` is `None` until something sources it (Section 3.2). `index_month_rule` is likewise
    `None`: Section 3.1 says the held months "may not be the front month" and that flow is
    mapped "to the contract months actually held (from holdings)", so there is no rule to
    encode for the US funds -- there is a holdings file nobody has yet.
    """

    name: str
    L: int
    underlying_root: str
    multiplier: float
    currency: str = "USD"
    er: float | None = None
    index_month_rule: str | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise FundModelError("Fund needs a name")
        if not isinstance(self.L, int) or isinstance(self.L, bool):
            raise FundModelError(f"{self.name}: L must be an int, got {self.L!r}")
        if self.L == 0:
            raise FundModelError(f"{self.name}: L = 0 is not a leveraged or unleveraged fund")
        if not self.underlying_root:
            raise FundModelError(f"{self.name}: needs an underlying root")
        if not math.isfinite(self.multiplier) or self.multiplier <= 0.0:
            raise FundModelError(
                f"{self.name}: multiplier must be a positive finite contract size, got "
                f"{self.multiplier!r}. It divides into a USD flow at line 231 and a zero or "
                f"negative one silently inverts or explodes the contract count."
            )
        if not self.currency:
            raise FundModelError(f"{self.name}: needs a currency")
        if self.er is not None:
            if not math.isfinite(self.er) or not 0.0 <= self.er < 0.25:
                raise FundModelError(
                    f"{self.name}: er = {self.er!r} is not an expense ratio as an annual "
                    f"fraction in [0, 0.25). A percentage typed as 0.95 instead of 0.0095 is "
                    f"the failure this refuses."
                )

    @property
    def rebalance_factor(self) -> int:
        """`L(L-1)`: 2 for a +2x fund, 6 for a -2x, and 0 for the two unleveraged ones.

        Section 1: the required rebalance is `AUM x L(L-1) x day's return`, "always in the
        direction of the day's move" -- which is what makes the factor positive for both
        signs of L. Required unit test 2 is that L = +1 contributes zero rebalance flow, and
        here that is `1 * 0`, an integer zero, not a float that happens to be small.
        """
        return self.L * (self.L - 1)


# Section 3.1, lines 60-65. `er=None` on all six: Section 3.2 is the fact list, and nothing
# has sourced it. See the module docstring.
BOIL = Fund(name="BOIL", L=2, underlying_root="NG", multiplier=NG_MULTIPLIER)
KOLD = Fund(name="KOLD", L=-2, underlying_root="NG", multiplier=NG_MULTIPLIER)
UCO = Fund(name="UCO", L=2, underlying_root="CL", multiplier=CL_MULTIPLIER)
SCO = Fund(name="SCO", L=-2, underlying_root="CL", multiplier=CL_MULTIPLIER)
UNG = Fund(name="UNG", L=1, underlying_root="NG", multiplier=NG_MULTIPLIER)
USO = Fund(name="USO", L=1, underlying_root="CL", multiplier=CL_MULTIPLIER)

#: The six of Section 3.1 in the document's own order, keyed by ticker.
US_FUNDS: dict[str, Fund] = {f.name: f for f in (BOIL, KOLD, UCO, SCO, UNG, USO)}


def inav(nav_prev: float, L: int, r_held: float, y_cash: float, er: float | None) -> float:
    """P3.1 line 184, in the document's own order of operations.

        iNAV_f(tau) = NAV_f[t-1] x (1 + L_f x r_held,f(tau))
                      + NAV_f[t-1] x (y_cash / 360 - ER_f / 365)

    `y_cash` and `er` are ANNUAL fractions (0.05 is 5.00%); the two divisions are one day's
    accrual on the two day counts the document names. `r_held` is the holdings-weighted
    return of the held contracts from the prior settlement to tau, as a fraction.

    Returned in the fund's own NAV currency per share -- the same units as `nav_prev`.

    RAISES rather than defaults on `er=None`, because that is what every one of the six
    `Fund` constants carries: the expense ratio is a Section 3.2 fact to be sourced, and an
    invented one would move the accrual term this formula exists to carry.
    """
    if er is None:
        raise FundModelError(
            "inav: er is None. The expense ratio is a Section 3.2 fact to be sourced into "
            "data/fund_facts/ with a URL and an access date, and Section 0 instruction 3 "
            "forbids fabricating it. Pass the sourced annual fraction."
        )
    for label, value in (("nav_prev", nav_prev), ("r_held", r_held), ("y_cash", y_cash), ("er", er)):
        if not math.isfinite(value):
            raise FundModelError(f"inav: {label} must be finite, got {value!r}")
    if nav_prev <= 0.0:
        raise FundModelError(
            f"inav: nav_prev = {nav_prev!r}. A fund's prior NAV per share is positive; a zero "
            f"or negative one makes the premium's denominator meaningless downstream."
        )
    if not isinstance(L, int) or isinstance(L, bool):
        raise FundModelError(f"inav: L must be an int, got {L!r}")
    return nav_prev * (1 + L * r_held) + nav_prev * (
        y_cash / CASH_DAY_COUNT - er / EXPENSE_DAY_COUNT
    )


@dataclass(frozen=True)
class Gate0b:
    """The outcome of Gate 0b for ONE fund over a set of days.

    `bp_errors` is signed and per day, in basis points of the official NAV, in the order the
    inputs were given. The gate reads `abs`, and the sign is kept because a gate that fails
    with every error on one side is a different defect (a missed accrual, a stale holdings
    file) from one that fails with errors scattered around zero (noise in the strike).
    """

    bp_errors: tuple[float, ...]
    share_within: float
    passes: bool
    n_days: int
    n_within: int
    bp_limit: float
    share_required: float

    @property
    def worst_bp(self) -> float:
        """The largest absolute error, in basis points. Reported, never the gate itself."""
        return max(abs(bp) for bp in self.bp_errors)


def gate_0b(
    inav_at_settle: Sequence[float],
    official_nav: Sequence[float],
    bp_limit: float = GATE_0B_BP_LIMIT,
    share: float = GATE_0B_SHARE,
) -> Gate0b:
    """Line 191: per fund, |iNAV at settlement - official NAV[t]| <= 5 bp on >= 95% of days.

    The error is a FRACTION of the official NAV, in basis points:

        bp = (inav_at_settle - official_nav) / official_nav * 1e4

    The document writes the difference without saying what it is a fraction of. It is read
    as the official NAV because that is the published number and the one a 5 bp tolerance is
    conventionally quoted against; D611 records the reading. At 5 bp the two denominators
    differ by 5 parts in 10^4 of each other, so the choice moves the error by 0.0025 bp and
    could only decide a day sitting on the boundary to four decimals.

    BOTH comparisons are inclusive: an error of exactly `bp_limit` is within, and a share of
    exactly `share` passes. The 19-of-20 hand case in the golden sits on the second of those
    boundaries deliberately.
    """
    n = len(inav_at_settle)
    if n != len(official_nav):
        raise FundModelError(
            f"gate_0b: {n} iNAV values against {len(official_nav)} official NAVs. A gate that "
            f"silently zipped to the shorter would report a share over the wrong denominator."
        )
    if n == 0:
        raise FundModelError(
            "gate_0b: no days. An empty sample passes every share test vacuously, which is "
            "the one way this gate could report a pass having measured nothing."
        )
    if not math.isfinite(bp_limit) or bp_limit <= 0.0:
        raise FundModelError(f"gate_0b: bp_limit must be positive and finite, got {bp_limit!r}")
    if not 0.0 < share <= 1.0:
        raise FundModelError(f"gate_0b: share must be in (0, 1], got {share!r}")
    errors: list[float] = []
    for i, (iv, nav) in enumerate(zip(inav_at_settle, official_nav)):
        if not math.isfinite(iv) or not math.isfinite(nav):
            raise FundModelError(f"gate_0b: day {i} has a non-finite value ({iv!r}, {nav!r})")
        if nav <= 0.0:
            raise FundModelError(
                f"gate_0b: day {i} has official NAV {nav!r}. A non-positive NAV is a broken "
                f"panel row, and dividing by it would turn that into a plausible error in bp."
            )
        errors.append((iv - nav) / nav * 1e4)
    n_within = sum(1 for bp in errors if abs(bp) <= bp_limit)
    share_within = n_within / n
    return Gate0b(
        bp_errors=tuple(errors),
        share_within=share_within,
        passes=share_within >= share,
        n_days=n,
        n_within=n_within,
        bp_limit=bp_limit,
        share_required=share,
    )
