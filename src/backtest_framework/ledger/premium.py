"""The ETF premium to iNAV, its valid-minute rule, the four features, and stress (D611).

WHAT THIS IS
------------
`SETTLEMENT_FLOW_LEDGER_PREREG.md` P3.2 to P3.3 (lines 193-213). The premium is the
document's estimate of how far ETF market makers are falling behind retail demand
(Section 1), and P3.5 turns it into the hedged fraction that decides how much creation flow
lands in the settlement window. It is therefore a MODEL INPUT that has never been measured
here: Section 3.3b's 1-minute NBBO quotes for the six funds do not exist on disk (the
repository holds no equities feed), so everything below is arithmetic waiting for data, and
every test of it is hand-typed.

THE DEFINITIONS, QUOTED
-----------------------
P3.2 "Premium", lines 196-201 (the document's Greek tau is spelled `tau`, its U+2212 minus
`-`, and its `|prem|` is kept as written)::

    prem_f(tau) = (mid_f(tau) - iNAV_f(tau)) / iNAV_f(tau)

    - Uses the NBBO **midpoint**, never the last trade.
    - A minute is **valid** only if the ETF quote updated within the last 60 s **and** the
      held futures contract traded within that minute.
    - Premium is computed **only before W_start** (decision D10). After settlement, NAV
      references a fixed price while futures keep trading.

P3.3 "Features at tau (from 09:30 ET to tau, valid minutes only)", lines 205-213::

    | `prem_twa` | Time-weighted mean premium |
    | `prem_frac` | Signed fraction of minutes with |prem| > c_AP: (count above +c_AP -
                    count below -c_AP) / valid minutes |
    | `vol_x` | ETF volume / trailing 20-day mean for the same interval |
    | `sv_etf` | Aggressor-signed ETF volume x iNAV (USD) |
    | `stress` | |prem_twa| z-scored against its trailing 60-day distribution |

    `c_AP` = the authorised participant's creation cost threshold as a fraction of basket
    value. Primary 0.10%; sensitivity 0.05% and 0.20%. It is refined only via Q9 by doc edit.

THE FOUR READINGS THIS MODULE MAKES, BECAUSE THE DOCUMENT DOES NOT FIX THEM
---------------------------------------------------------------------------
1. **A crossed or locked quote raises at construction.** `Quote` refuses `bid >= ask`. A
   crossed NBBO has a midpoint and that midpoint is not a price anyone could trade; letting
   it through would put a plausible premium into `prem_twa` from a broken quote row.
2. **"Within the last 60 s" is inclusive.** An age of exactly 60.0 s is valid; line 722's
   test says a quote "not updated for MORE than 60 s" is excluded, and this is the reading
   that makes the two sentences agree.
3. **`prem_twa` is the simple mean over valid minutes.** The minutes are equal length, so
   the time weighting is a constant weight and reduces to the mean; `features` asserts the
   timestamps are strictly increasing so that a duplicated minute cannot double-weight
   itself unnoticed. An unequal-length sample would need explicit weights and this module
   would be the wrong shape for it.
4. **`stress` z-scores the ABSOLUTE premium against the distribution of ABSOLUTE premia.**
   Line 211 reads `|prem_twa|` z-scored against "its" trailing distribution, and "its" is
   read as the distribution of the same quantity -- `|prem_twa|` -- not of the signed one.
   The alternative reading gives a z that is negative on a calm day and positive on a
   stressed one in the same units, which is not a stress. D611 records the choice.

WHAT IS NOT HERE
----------------
No IIV feed (Section 3.3b, validation only, decision D14), no Lee-Ready classification
(`signed_volume` arrives already signed, from whatever the caller documents), no attention
detector (P3.7 is `att_accel` in `ledger/creations.py`'s hedged fraction and its data is
another agent's), and no fitting of anything.
"""

from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass
from typing import Sequence

from .funds import FundModelError

__all__ = [
    "C_AP_PRIMARY",
    "C_AP_SENSITIVITY",
    "Features",
    "Minute",
    "PremiumError",
    "PremiumWindowError",
    "Quote",
    "STRESS_TRAILING_DAYS",
    "features",
    "minute_feature",
    "premium",
    "stress",
    "valid_minute",
]


class PremiumError(FundModelError):
    """A premium input was impossible: a crossed quote, a non-positive iNAV, no valid minute."""


class PremiumWindowError(PremiumError):
    """A minute at or after `W_start` reached a premium feature (line 201, decision D10).

    Its own class because it is the look-ahead guard rather than a data complaint: after the
    settlement window opens, NAV references a fixed price while futures keep trading, so a
    premium computed there is measuring the window this study is trying to predict.
    """


#: Line 213. Primary 0.10% as a FRACTION of basket value; the two sensitivities beside it.
C_AP_PRIMARY = 0.001
C_AP_SENSITIVITY = (0.0005, 0.002)

#: Line 200. "the ETF quote updated within the last 60 s".
MAX_QUOTE_AGE_S = 60.0

#: Line 211. "its trailing 60-day distribution".
STRESS_TRAILING_DAYS = 60


@dataclass(frozen=True)
class Quote:
    """One NBBO snapshot. `last` is carried and never read by the premium (line 199).

    It is carried precisely so that required unit test 15 can change it and assert the
    premium does not move: a field that does not exist cannot be shown to be ignored, and
    "uses the midpoint, never the last trade" is a claim about what the code ignores.
    """

    bid: float
    ask: float
    last: float
    ts: dt.datetime

    def __post_init__(self) -> None:
        for label, value in (("bid", self.bid), ("ask", self.ask), ("last", self.last)):
            if not isinstance(value, float) or not math.isfinite(value):
                raise PremiumError(f"Quote: {label} must be a finite float, got {value!r}")
        if self.bid <= 0.0 or self.ask <= 0.0:
            raise PremiumError(f"Quote: bid {self.bid!r} and ask {self.ask!r} must be positive")
        if self.bid >= self.ask:
            raise PremiumError(
                f"Quote: bid {self.bid!r} >= ask {self.ask!r}. A crossed or locked NBBO still "
                f"has a midpoint, and that midpoint is not a price: admitting it would put a "
                f"plausible premium into prem_twa from a broken quote row."
            )
        if not isinstance(self.ts, dt.datetime):
            raise PremiumError(f"Quote: ts must be a datetime, got {self.ts!r}")

    @property
    def mid(self) -> float:
        """`(bid + ask) / 2` -- the NBBO midpoint of line 199, and the only field the premium reads."""
        return (self.bid + self.ask) / 2


@dataclass(frozen=True)
class Minute:
    """One ETF minute, with everything the valid-minute rule and the four features need.

    `inav` is the fund's iNAV for this minute (`ledger/funds.inav`), carried per minute
    because the premium and `sv_etf` both need it and it moves with the futures. `volume`
    is ETF shares traded in the minute; `signed_volume` is the aggressor-signed count
    (Section 3.3b: exchange-provided or Lee-Ready, "documented" -- this module takes it as
    given and documents nothing on the caller's behalf).
    """

    ts: dt.datetime
    quote: Quote
    inav: float
    quote_age_s: float
    futures_traded: bool
    volume: float = 0.0
    signed_volume: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.ts, dt.datetime):
            raise PremiumError(f"Minute: ts must be a datetime, got {self.ts!r}")
        if not isinstance(self.quote, Quote):
            raise PremiumError(f"Minute: quote must be a Quote, got {self.quote!r}")
        if not isinstance(self.futures_traded, bool):
            raise PremiumError(
                f"Minute: futures_traded must be a bool, got {self.futures_traded!r}. A trade "
                f"COUNT passed here would be truthy at 1 and falsy at 0, which is the right "
                f"answer by accident and the wrong type to rely on."
            )
        for label, value in (
            ("inav", self.inav),
            ("quote_age_s", self.quote_age_s),
            ("volume", self.volume),
            ("signed_volume", self.signed_volume),
        ):
            if not math.isfinite(value):
                raise PremiumError(f"Minute: {label} must be finite, got {value!r}")
        if self.inav <= 0.0:
            raise PremiumError(f"Minute: inav must be positive, got {self.inav!r}")
        if self.volume < 0.0:
            raise PremiumError(f"Minute: volume must be non-negative, got {self.volume!r}")
        if abs(self.signed_volume) > self.volume:
            raise PremiumError(
                f"Minute: |signed_volume| {self.signed_volume!r} exceeds volume "
                f"{self.volume!r}. The signed count is a partition of the traded shares, so "
                f"it cannot be larger than the shares."
            )


def premium(quote: Quote, inav_value: float) -> float:
    """P3.2 line 196: `prem_f(tau) = (mid_f(tau) - iNAV_f(tau)) / iNAV_f(tau)`.

    Reads `quote.mid` and nothing else off the quote -- line 199, "never the last trade".
    Dimensionless: a fraction of iNAV, so 0.001 is 10 bp is the primary `c_AP`.
    """
    if not math.isfinite(inav_value) or inav_value <= 0.0:
        raise PremiumError(
            f"premium: iNAV must be positive and finite, got {inav_value!r}. It is the "
            f"denominator, and a zero one would turn a broken iNAV into an infinite premium "
            f"that every threshold below then reads as extreme stress."
        )
    return (quote.mid - inav_value) / inav_value


def valid_minute(quote_age_s: float, futures_traded: bool) -> bool:
    """Line 200, both clauses.

        A minute is valid only if the ETF quote updated within the last 60 s AND the held
        futures contract traded within that minute.

    Inclusive at 60.0 s: reading 2 in the module docstring. Returns a bool; it never raises
    on a stale quote, because staleness is the ordinary case this predicate exists to name.
    """
    if not isinstance(futures_traded, bool):
        raise PremiumError(f"valid_minute: futures_traded must be a bool, got {futures_traded!r}")
    if not math.isfinite(quote_age_s) or quote_age_s < 0.0:
        raise PremiumError(
            f"valid_minute: quote_age_s must be a non-negative finite number of seconds, got "
            f"{quote_age_s!r}. A negative age is a quote stamped after the minute it is being "
            f"read in, which is a clock or a join defect and not a stale quote."
        )
    return quote_age_s <= MAX_QUOTE_AGE_S and futures_traded


def minute_feature(minute: Minute, inav_value: float) -> float | None:
    """The premium for one minute, or `None` when line 200 excludes it.

    `None` and NEVER 0.0. Required unit test 16 is that an excluded minute is "excluded from
    all features", and a zero would be included in every one of them: it enters `prem_twa`'s
    mean as an observation of no premium, it lands inside the `c_AP` band in `prem_frac`, and
    it raises the denominator of both. A missing measurement and a measurement of zero are
    different facts and this returns different objects for them.

    The iNAV is passed explicitly rather than read off `minute.inav` so that this is the
    formula and nothing else; `features` passes `m.inav`.
    """
    if not valid_minute(minute.quote_age_s, minute.futures_traded):
        return None
    return premium(minute.quote, inav_value)


@dataclass(frozen=True)
class Features:
    """P3.3's four features at tau, plus the count they are all computed over.

    `vol_x` is `None` when the caller supplied no trailing 20-day mean -- the same rule as
    `minute_feature`: the trailing mean is a measurement nobody here has made, and a 1.0
    standing in for it would read as "volume exactly normal".
    """

    prem_twa: float
    prem_frac: float
    vol_x: float | None
    sv_etf: float
    n_valid: int
    c_ap: float


def features(
    minutes: Sequence[Minute],
    *,
    w_start: dt.datetime,
    c_ap: float = C_AP_PRIMARY,
    trailing_volume_mean: float | None = None,
) -> Features:
    """P3.3 lines 205-213 over the valid minutes of `minutes`, all four at once.

    `minutes` is 09:30 ET to tau in order. Every minute must be strictly before `w_start`
    (line 201, decision D10) or this raises `PremiumWindowError` naming the first offender --
    the filtering is NOT done silently, because a caller that hands in the whole session and
    gets a quiet answer has a look-ahead defect it will never see.

    `sv_etf` is in USD: aggressor-signed shares times that minute's iNAV, summed over valid
    minutes in the order given. `vol_x` is the valid minutes' ETF volume over the caller's
    trailing 20-day mean for the same interval.
    """
    if not isinstance(w_start, dt.datetime):
        raise PremiumError(f"features: w_start must be a datetime, got {w_start!r}")
    if not math.isfinite(c_ap) or c_ap <= 0.0:
        raise PremiumError(f"features: c_ap must be a positive fraction, got {c_ap!r}")
    if trailing_volume_mean is not None:
        if not math.isfinite(trailing_volume_mean) or trailing_volume_mean <= 0.0:
            raise PremiumError(
                f"features: trailing_volume_mean must be positive, got "
                f"{trailing_volume_mean!r}. vol_x divides by it."
            )
    if not minutes:
        raise PremiumError("features: no minutes given")
    previous: dt.datetime | None = None
    for m in minutes:
        if (m.ts.tzinfo is None) != (w_start.tzinfo is None):
            raise PremiumError(
                f"features: minute {m.ts!r} and w_start {w_start!r} disagree on whether they "
                f"carry a timezone. Comparing them would raise deep inside the loop, and "
                f"aligning them by assumption is how a DST hour goes missing."
            )
        if previous is not None and m.ts <= previous:
            raise PremiumError(
                f"features: minutes must be strictly increasing in time; {m.ts!r} follows "
                f"{previous!r}. prem_twa weights each minute equally, so a repeated timestamp "
                f"would weight that minute twice and nothing else would say so."
            )
        previous = m.ts
        if m.ts >= w_start:
            raise PremiumWindowError(
                f"features: minute {m.ts!r} is at or after W_start {w_start!r}. Line 201: the "
                f"premium is computed ONLY before W_start (decision D10)."
            )
    prem_sum = 0.0
    above = 0
    below = 0
    sv = 0.0
    vol = 0.0
    n_valid = 0
    for m in minutes:
        p = minute_feature(m, m.inav)
        if p is None:
            continue
        n_valid += 1
        prem_sum = prem_sum + p
        if p > c_ap:
            above += 1
        elif p < -c_ap:
            below += 1
        sv = sv + m.signed_volume * m.inav
        vol = vol + m.volume
    if n_valid == 0:
        raise PremiumError(
            f"features: 0 of {len(minutes)} minutes are valid under line 200, so prem_twa and "
            f"prem_frac have no denominator. A day with no valid minute is a day with no "
            f"premium measurement, not a day with a premium of zero."
        )
    return Features(
        prem_twa=prem_sum / n_valid,
        prem_frac=(above - below) / n_valid,
        vol_x=None if trailing_volume_mean is None else vol / trailing_volume_mean,
        sv_etf=sv,
        n_valid=n_valid,
        c_ap=c_ap,
    )


def stress(
    prem_twa: float,
    trailing: Sequence[tuple[dt.date, float]],
    *,
    day: dt.date,
    min_obs: int = 20,
) -> float:
    """Line 211: `|prem_twa|` z-scored against its trailing 60-day distribution.

        z = (|prem_twa| - mean(|trailing|)) / sd(|trailing|)

    `trailing` is `(day, prem_twa)` pairs from PRIOR days only, and that is checked rather
    than trusted: an entry dated `day` or later raises. The alternative -- a bare sequence of
    floats and a docstring asking the caller to pass only prior days -- is the shape of
    look-ahead this project keeps finding in throwaway analysis scripts (R9), and here the
    contaminating value would be today's own premium, which would drag the z toward zero on
    exactly the extreme days the feature exists to flag.

    `sd` is the SAMPLE standard deviation (ddof = 1) and a zero one raises: a constant
    trailing window gives an infinite or undefined z, and clipping it would report a finite
    stress from no dispersion at all.
    """
    if not isinstance(day, dt.date) or isinstance(day, dt.datetime):
        raise PremiumError(f"stress: day must be a date (not a datetime), got {day!r}")
    if not math.isfinite(prem_twa):
        raise PremiumError(f"stress: prem_twa must be finite, got {prem_twa!r}")
    if min_obs < 2:
        raise PremiumError(f"stress: min_obs must be at least 2, got {min_obs!r}")
    seen: set[dt.date] = set()
    values: list[float] = []
    for entry in trailing:
        d, v = entry
        if not isinstance(d, dt.date) or isinstance(d, dt.datetime):
            raise PremiumError(f"stress: trailing key must be a date, got {d!r}")
        if d >= day:
            raise PremiumError(
                f"stress: trailing entry dated {d} is not before {day}. The trailing window "
                f"is prior days only; today's own prem_twa in its own reference distribution "
                f"pulls the z toward zero on the days it is meant to flag."
            )
        if d in seen:
            raise PremiumError(f"stress: trailing has two entries for {d}")
        seen.add(d)
        if not math.isfinite(v):
            raise PremiumError(f"stress: trailing value for {d} is not finite ({v!r})")
        values.append(abs(v))
    n = len(values)
    if n < min_obs:
        raise PremiumError(
            f"stress: {n} trailing observation(s), below min_obs = {min_obs}. A z-score on a "
            f"handful of days is an estimate of a standard deviation from a handful of days."
        )
    if n > STRESS_TRAILING_DAYS:
        raise PremiumError(
            f"stress: {n} trailing observations, more than the {STRESS_TRAILING_DAYS}-day "
            f"window of line 211. Truncating silently would make the window a property of "
            f"how much history the caller happened to pass; slice it yourself and say so."
        )
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / (n - 1)
    sd = math.sqrt(variance)
    if sd == 0.0:
        raise PremiumError(
            f"stress: the trailing {n} days of |prem_twa| are constant at {mean!r}, so the "
            f"z-score has no denominator."
        )
    return (abs(prem_twa) - mean) / sd
