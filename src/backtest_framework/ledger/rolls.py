"""P8a and P8b: fund-level roll flows and the scaled tracker flag (D610).

THE FORMULAS, QUOTED VERBATIM
-----------------------------
P8a, line 324::

    Every tracked fund (US: BOIL, KOLD, UCO, SCO, UNG, USO; plus P9 products where schedules
    can be sourced) moves its position from one contract month to the next on a **published
    schedule**.

line 327::

    **UNG (verified from SEC filings):** rolls from the near month to the next month over a
    **four-day period beginning two weeks before the near month's expiration**. The benchmark
    moves 25% per day (75/25, 50/50, 25/75, then 100% next month). The issuer publishes a CSV
    of anticipated roll dates, subject to change.

line 328::

    **USO, BOIL, KOLD, UCO, SCO, P9 products:** to source from each prospectus or index
    methodology (Q19). Do not assume.

lines 332-335::

    phi_f,d        = fraction of the position rolled on day d (from the schedule; Sum_d phi = 1)
    N_old,f        = contracts held in the expiring month at the start of the roll period
                     (from holdings)
    Sell_old     = - phi_f,d x N_old,f x sign(L_f)                  (contracts, expiring month)
    Buy_new      = + phi_f,d x N_old,f x sign(L_f) x (P_old / P_new)
                     (contracts, next month, notional-matched)

line 338::

    Inverse funds (L < 0) are short, so their roll **buys** the expiring month and **sells**
    the next. The sign(L) term handles this.

line 340::

    **Backtest reconstruction:** where historical roll-date lists aren't available,
    reconstruct from the prospectus rule. **Validate** by checking that recorded holdings
    changes across the roll period match the computed phi (unit test 39). Any fund whose
    reconstruction fails validation falls back to P8b treatment.

P8b, line 348::

    Q8b = roll_flag[t] x roll_fraction[t] x beta8

line 352::

    P8b must exclude any fund already counted in P8a.

Required unit tests 37 (line 743), 38 (line 744), 39 (line 745), 40 (line 746).

THE ONE INTERPRETATION THIS MODULE HAD TO MAKE
----------------------------------------------
**"Two weeks before the near month's expiration" is read as 14 CALENDAR DAYS, and the four
roll days are four CONSECUTIVE CALENDAR DAYS from there.** The alternative reading -- ten
BUSINESS days before expiry, four consecutive business days -- is equally consistent with
line 327 and gives different dates whenever a weekend or a US holiday falls in the window.

Why the calendar reading: "two weeks" is a calendar phrase, it is what an SEC filing's plain
language means, and it is the only reading this module can implement HONESTLY, because
computing business days needs an exchange calendar and **no calendar is read here** -- this
record reads no fixture at all. A weekday approximation would silently be wrong on every
Thanksgiving and Good Friday, and would look right.

**What resolves it is not a reading at all.** Line 327's own last sentence says the issuer
publishes a CSV of anticipated roll dates, and line 340 says a reconstruction that disagrees
with recorded holdings falls back to P8b. :func:`roll_days` is therefore a RECONSTRUCTION to
be validated by :func:`validate_roll`, not an authority, and its docstring says so at the
point of use. A study that has the CSV should use the CSV.
"""

from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass
from typing import Mapping, Sequence

from .flows import LedgerError, _finite

__all__ = [
    "ROLL_SCHEDULES",
    "RollSchedule",
    "RollValidation",
    "UNG_SCHEDULE",
    "q8b",
    "roll_days",
    "roll_legs",
    "validate_roll",
]

#: Line 327's "two weeks", as this module reads it. See the module docstring.
TWO_WEEKS_DAYS = 14
#: The default absolute tolerance, in fractions of the position, for :func:`validate_roll`.
ROLL_TOLERANCE = 0.02


@dataclass(frozen=True)
class RollSchedule:
    """One fund's published roll schedule, with the line it was read from.

    ``fractions`` are ``phi_f,d`` for the consecutive days of the roll period and must sum to
    1 (line 332's ``Sum_d phi = 1``). ``start_rule`` names the rule in words so a reader can
    see which reading :func:`roll_days` implements. ``source`` is where the schedule came
    from and is REQUIRED: line 20 of the deposit's Section 0 is "Never fabricate data or
    facts ... Every externally sourced fact is recorded in SOURCES.md with a URL and access
    date", and a schedule without a provenance string is exactly the fact line 328 forbids
    assuming.
    """

    fractions: tuple[float, ...]
    start_rule: str
    source: str

    def __post_init__(self) -> None:
        if not isinstance(self.fractions, tuple) or not self.fractions:
            raise LedgerError(f"RollSchedule.fractions must be a non-empty tuple, got {self.fractions!r}")
        for i, f in enumerate(self.fractions):
            v = _finite(f"fractions[{i}]", f)
            if not 0.0 < v <= 1.0:
                raise LedgerError(f"RollSchedule.fractions[{i}] = {v!r}; each day's phi must lie in (0, 1]")
        total = math.fsum(self.fractions)
        if total != 1.0:
            raise LedgerError(
                f"RollSchedule.fractions sum to {total!r}, not 1.0. Line 332 says Sum_d phi = 1; "
                "a schedule that does not roll the whole position is not a schedule, it is a "
                "partial one someone forgot to finish."
            )
        if not self.start_rule or not self.source:
            raise LedgerError("RollSchedule needs both a start_rule and a source (line 328: 'Do not assume')")

    @property
    def days(self) -> int:
        return len(self.fractions)

    @property
    def cumulative(self) -> tuple[float, ...]:
        """Running sum of ``fractions``; the last entry is 1.0 (required unit test 37)."""
        out: list[float] = []
        run = 0.0
        for f in self.fractions:
            run += f
            out.append(run)
        return tuple(out)

    @staticmethod
    def for_fund(fund: str) -> "RollSchedule":
        """The registered schedule for ``fund``, or a refusal.

        **There is no default.** Line 328 lists USO, BOIL, KOLD, UCO, SCO and the P9 products
        as "to source from each prospectus or index methodology (Q19). Do not assume." UNG's
        is the only one line 327 states, and handing UNG's four-day 25% schedule to USO
        because both are United States Commodity Funds products is precisely the assumption
        that sentence forbids.
        """
        if not isinstance(fund, str) or not fund:
            raise LedgerError(f"for_fund: fund must be a non-empty string, got {fund!r}")
        key = fund.strip().upper()
        if key not in ROLL_SCHEDULES:
            raise LedgerError(
                f"No roll schedule is registered for {key!r}. Line 328: 'USO, BOIL, KOLD, UCO, "
                "SCO, P9 products: to source from each prospectus or index methodology (Q19). "
                "Do not assume.' Only "
                f"{sorted(ROLL_SCHEDULES)} is sourced (line 327). Source the schedule, record it "
                "in SOURCES.md with a URL and an access date, register it here, and then call "
                "this again -- or treat the fund under P8b, which is what line 340 does with a "
                "reconstruction that cannot be validated."
            )
        return ROLL_SCHEDULES[key]


#: Line 327, verbatim in its numbers: four days, 25% each, beginning two weeks before the
#: near month's expiration. 0.25 x 4 = 1.0 exactly, so `cumulative` ends at exactly 1.0.
UNG_SCHEDULE = RollSchedule(
    fractions=(0.25, 0.25, 0.25, 0.25),
    start_rule="two_weeks_before_near_expiry",
    source=(
        "SETTLEMENT_FLOW_LEDGER_PREREG.md line 327 -- 'UNG (verified from SEC filings): rolls "
        "from the near month to the next month over a four-day period beginning two weeks "
        "before the near month's expiration. The benchmark moves 25% per day (75/25, 50/50, "
        "25/75, then 100% next month). The issuer publishes a CSV of anticipated roll dates, "
        "subject to change.'"
    ),
)

#: The registry. ONE entry, deliberately. Adding a fund means sourcing its prospectus.
ROLL_SCHEDULES: Mapping[str, RollSchedule] = {"UNG": UNG_SCHEDULE}


def roll_days(near_expiry: dt.date, schedule: RollSchedule = UNG_SCHEDULE) -> list[dt.date]:
    """Required unit test 37: the schedule's days, as calendar dates.

    Day one is ``near_expiry - 14 days`` and the rest are consecutive calendar days. See the
    module docstring for why 14 calendar days rather than ten business days, and for the fact
    that this is a RECONSTRUCTION: line 327's issuer CSV is the authority and line 340 sends a
    fund whose reconstruction fails validation to P8b.

    **No exchange calendar is consulted and none of these days is adjusted.** Four consecutive
    calendar days will contain a weekend unless day one is a Monday or a Tuesday, and a US
    holiday can fall in any of them. The returned dates are what the rule says, not what the
    exchange was open for, and a study must reconcile them against the issuer's published
    dates before using them.
    """
    if not isinstance(near_expiry, dt.date) or isinstance(near_expiry, dt.datetime):
        raise LedgerError(
            f"roll_days: near_expiry must be a datetime.date (not a datetime), got {near_expiry!r}"
        )
    if not isinstance(schedule, RollSchedule):
        raise LedgerError(f"roll_days: schedule must be a RollSchedule, got {type(schedule).__name__}")
    if schedule.start_rule != "two_weeks_before_near_expiry":
        raise LedgerError(
            f"roll_days implements only the 'two_weeks_before_near_expiry' rule and this "
            f"schedule declares {schedule.start_rule!r}. A second start rule is a second "
            "sourced fact and gets its own function, not a branch nobody registered."
        )
    first = near_expiry - dt.timedelta(days=TWO_WEEKS_DAYS)
    return [first + dt.timedelta(days=i) for i in range(schedule.days)]


def roll_legs(
    phi: float, n_old: float, L: float, p_old: float, p_new: float
) -> tuple[float, float]:
    """Lines 334-335: ``(Sell_old, Buy_new)`` in contracts, for one fund on one roll day.

    Only ``sign(L)`` enters, never L's magnitude: ``n_old`` is already the contract count the
    fund holds and the leverage is inside it. A long fund (``L > 0``) sells the expiring month
    and buys the next; an inverse fund (``L < 0``) does the reverse, which is line 338.

    ``Buy_new`` is scaled by ``P_old / P_new`` so the two legs match in notional (line 335,
    "notional-matched"). The match is exact only when ``P_old / P_new`` is a binary fraction;
    in general ``Buy_new x P_new`` differs from ``|Sell_old| x P_old`` in the last places, and
    the property test asserts it to a relative tolerance for that reason.

    ``L = 0`` raises: ``sign(0)`` has no direction, and a fund with no leverage holds no
    position to roll.
    """
    f = _finite("phi", phi)
    if not 0.0 < f <= 1.0:
        raise LedgerError(f"phi must lie in (0, 1], got {f!r}")
    n = _finite("n_old", n_old)
    if n < 0.0:
        raise LedgerError(
            f"n_old must be non-negative, got {n!r}. Line 333 defines N_old as the CONTRACTS "
            "HELD in the expiring month; the short side of an inverse fund is carried by "
            "sign(L), not by a negative count, and carrying it in both double-counts it."
        )
    lev = _finite("L", L)
    if lev == 0.0:
        raise LedgerError("L = 0 has no sign, and a fund with no leverage holds no position to roll")
    po = _finite("p_old", p_old)
    pn = _finite("p_new", p_new)
    if po <= 0.0 or pn <= 0.0:
        raise LedgerError(f"p_old and p_new must be positive, got {po!r} and {pn!r}")
    sign = math.copysign(1.0, lev)
    sell_old = -f * n * sign
    buy_new = +f * n * sign * (po / pn)
    return sell_old, buy_new


@dataclass(frozen=True)
class RollValidation:
    """The verdict of line 340's holdings check.

    ``fallback_to_p8b`` is the document's own consequence -- "Any fund whose reconstruction
    fails validation falls back to P8b treatment" -- carried as a field rather than left for a
    caller to infer, so that a study cannot record a failed validation and go on using P8a.
    """

    passes: bool
    fallback_to_p8b: bool
    max_abs_deviation: float
    reason: str


def validate_roll(
    holdings_changes: Sequence[float],
    schedule: RollSchedule = UNG_SCHEDULE,
    *,
    tol: float = ROLL_TOLERANCE,
) -> RollValidation:
    """Required unit test 39: do recorded holdings changes match the computed ``phi``?

    ``holdings_changes`` are the observed per-day FRACTIONS of the starting position moved out
    of the expiring month, one per roll day, in order. Line 340 asks that they "match the
    computed phi"; it does not say how closely, so ``tol`` is a declared absolute tolerance in
    fractions of the position, default 0.02 -- two percentage points, which admits rounding in
    a published holdings file and refuses a schedule that is wrong by a whole day.

    The check has two clauses and the failing one is named: every day within ``tol`` of its
    ``phi``, and the total within ``tol`` of 1. A reconstruction that moved 100% on day one
    fails the first clause by 0.75 and passes the second, which is exactly required unit test
    39's second case.
    """
    if not isinstance(schedule, RollSchedule):
        raise LedgerError(f"validate_roll: schedule must be a RollSchedule, got {type(schedule).__name__}")
    if isinstance(holdings_changes, (str, bytes)) or not isinstance(holdings_changes, Sequence):
        raise LedgerError(f"validate_roll: holdings_changes must be a sequence, got {holdings_changes!r}")
    t = _finite("tol", tol)
    if t <= 0.0:
        raise LedgerError(f"validate_roll: tol must be positive, got {t!r}")
    if len(holdings_changes) != schedule.days:
        raise LedgerError(
            f"validate_roll: {len(holdings_changes)} observed day(s) against a {schedule.days}-day "
            "schedule. A length mismatch is not a tolerance question: the roll period itself is "
            "wrong, and comparing the days that happen to line up would hide that."
        )
    obs = [_finite(f"holdings_changes[{i}]", v) for i, v in enumerate(holdings_changes)]
    devs = [abs(o - p) for o, p in zip(obs, schedule.fractions)]
    worst = max(devs)
    total = math.fsum(obs)
    total_dev = abs(total - 1.0)
    if worst > t:
        i = devs.index(worst)
        reason = (
            f"day {i + 1} of {schedule.days} moved {obs[i]:.4f} of the position against a "
            f"scheduled phi of {schedule.fractions[i]:.4f} (deviation {worst:.4f} > tol {t:g}); "
            "line 340 sends this fund to P8b"
        )
        return RollValidation(False, True, worst, reason)
    if total_dev > t:
        reason = (
            f"the observed fractions sum to {total:.4f}, not 1 (deviation {total_dev:.4f} > tol "
            f"{t:g}): the roll period is incomplete even though each day matches; line 340 sends "
            "this fund to P8b"
        )
        return RollValidation(False, True, worst, reason)
    return RollValidation(
        True,
        False,
        worst,
        f"all {schedule.days} days within {t:g} of phi (worst {worst:.4f}) and the total within "
        f"{t:g} of 1",
    )


def q8b(
    roll_flag: int | bool,
    roll_fraction: float,
    beta8: float,
    *,
    fund: str,
    p8a_funds: Sequence[str] | frozenset[str],
) -> float:
    """Line 348: ``Q8b = roll_flag[t] x roll_fraction[t] x beta8``, with line 352's exclusion.

    Required unit test 40: a fund already counted in P8a contributes EXACTLY ``0.0`` to P8b.
    Not "approximately zero" and not "a small residual" -- the term is not computed at all, so
    no choice of ``beta8`` can make it non-zero. That is the only shape in which line 352's
    "must exclude" is a guarantee rather than a hope.

    ``beta8`` is Section 6's one free parameter for stage F and is FITTED elsewhere (line 351:
    "a single scale parameter, estimated (tracker AUM is too uncertain to compute directly)").
    Nothing here estimates it.
    """
    if not isinstance(fund, str) or not fund:
        raise LedgerError(f"q8b: fund must be a non-empty string, got {fund!r}")
    if isinstance(p8a_funds, (str, bytes)) or not isinstance(p8a_funds, (Sequence, frozenset, set)):
        raise LedgerError(
            f"q8b: p8a_funds must be a collection of fund names, got {type(p8a_funds).__name__}. "
            "A bare string would test membership character by character and silently exclude "
            "every fund whose name is a substring of it."
        )
    excluded = {str(f).strip().upper() for f in p8a_funds}
    if fund.strip().upper() in excluded:
        return 0.0
    if isinstance(roll_flag, bool):
        flag = 1 if roll_flag else 0
    elif isinstance(roll_flag, int):
        flag = roll_flag
    else:
        raise LedgerError(f"q8b: roll_flag must be 0, 1 or a bool, got {roll_flag!r}")
    if flag not in (0, 1):
        raise LedgerError(
            f"q8b: roll_flag must be 0 or 1, got {flag}. It is a FLAG (line 348); a roll's SIZE "
            "lives in roll_fraction and its scale in beta8, and a flag carrying magnitude would "
            "make beta8 unidentifiable."
        )
    frac = _finite("roll_fraction", roll_fraction)
    if not 0.0 <= frac <= 1.0:
        raise LedgerError(f"q8b: roll_fraction must lie in [0, 1], got {frac!r}")
    b8 = _finite("beta8", beta8)
    return flag * frac * b8
