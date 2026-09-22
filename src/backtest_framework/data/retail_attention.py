"""Retail attention measured from CREATIONS, ROBINHOOD HOLDERS and GDELT — D621.

THE AMENDMENT THIS MODULE IMPLEMENTS
------------------------------------
`SETTLEMENT_FLOW_LEDGER_PREREG.md` §3.3c, its line 112, names a source:

    | Wikimedia hourly pageviews | Hourly, from 2015 | Primary: public attention |

D612 recorded that this line is **wrong as written**: the Wikimedia REST per-article endpoint
serves daily and monthly only, and per-article hourly data exists solely in the
`dumps.wikimedia.org` hourly files — ~2.5 TB for 2016–2023, one file per hour covering every
project and every article on earth, of which the deposit's eight titles are of the order of
sixteen lines an hour. D612 built the parser and declined the backfill.

**On 2026-09-22 the principal dropped the hourly backfill and replaced the row.** D621 records
that amendment and this module is its code. The replacement, in the order the record argues it:

  1. **CREATIONS are the direct retail-demand measure and the hourly pageview series was a
     proxy for them.** A creation is the share count of a fund changing: money that actually
     arrived, denominated in the units the ledger's own creation model (§P3.7's C3) is written
     in. It is published daily by the issuer, it is free, it is already on disk for four funds
     (`data/fixtures/fund_nav_daily.csv.gz`, D619), and it needs no proxy at all. An hourly
     pageview count is a measure of people reading about natural gas; `Δshares_out` is a
     measure of people buying the fund.
  2. **Robinhood holder counts validate it over 2018-05-02 .. 2020-08-13**, hourly, from
     `data/raw/robintrack/` — the Barber-Huang-Odean-Schwarz archive. This is the only series
     on disk that counts RETAIL ACCOUNTS rather than dollars, and its overlap with the creation
     series is what D621 measures.
  3. **GDELT stays**, unchanged in substance, and moves to the DOC 2.0 API for the forward job.
     The raw 15-minute files remain the backfill route (D612's finding, and the API's one
     request per five seconds with a long cooldown is why).
  4. **The Wikimedia DAILY REST series is kept as a cheap secondary.** `fetch_attention.py
     --wiki-daily` already fetches it and D612's `QUERIES.md` §1a is already probed against it.
     It is daily, so it cannot carry `att_accel` as the deposit defines it (three hours against
     three hours) and it is not a primary series here.

WHAT THIS MODULE IS, AND WHAT IT REUSES RATHER THAN REPEATS
-----------------------------------------------------------
Everything in `backtest_framework.data.attention` (D612) that applies is CALLED, not copied:

  * `zscore_matched` is the same-weekday z and `holders_z` is a thin adapter onto it;
  * `att_level` IS `creation_level` — it is a mean of a mapping of z-scores with finiteness
    guards and it does not care whether the keys are sources or funds;
  * `att_accel` is called by `creation_accel` after the six daily levels are laid on a
    six-hour axis, so the exactness-on-a-constant property is inherited rather than re-derived;
  * `refuse_coarse_resolution` is called verbatim for the deposit's 15-minute features.

What is genuinely new, and why each piece could not be borrowed:

  * **a DAILY z window.** `zscore_matched` matches on hour-of-day AND weekday because a
    pageview series has both cycles. A daily creation series has neither hour-of-day nor, on
    the evidence, a weekday that is worth spending four fifths of the history on: 60 days of
    one weekday is at most ceil(60/7) = 9 observations against D612's own floor of five.
    `creation_z` therefore defaults to `match="all_days"` and offers `match="same_weekday"`,
    which delegates to `zscore_matched` itself. The two are pinned EQUAL on an input where the
    windows coincide (`tests/golden/test_retail_attention_ledger.hand.txt`, Case 3), so the
    copy of the arithmetic is a copy that is checked against its original.
  * **the two correlations.** `spearman` and `pearson` exist here rather than in a runner
    because D621's whole claim is two numbers of this shape and R9's lesson is that an ad-hoc
    analysis script gets none of the protection a library function can be given.
  * **an hourly NEWS resolution that is not the deposit's.** `refuse_coarse_resolution` refuses
    an "hour" bucket, correctly, because the deposit's `headline_burst` is a 15-minute block.
    D621's news series is hourly by construction — it is paired with a DAILY creation series —
    so `news_n_hourly` accepts "hour" **only when the caller asks for it in writing**
    (`accept_hourly=True`) and the accepted resolution travels on every returned series. The
    forward recorder job stays 15-minute; the explanation is in the record and in
    `scripts/fetch_gdelt_hourly.py`.

AVAILABILITY, WHICH IS THE PART THAT CAN ONLY BE WRONG IN ONE DIRECTION
-----------------------------------------------------------------------
Each series carries an `available_at` and each rule is stated, conservative and unconditional:

  * **creations**: `published_at = date + 1 day`. THE SOURCE STATES NO PUBLICATION TIME — the
    ProShares historical-NAV CSV has no `published_at` column at all, which `fund_nav_daily`'s
    own meta records as an ABSENT column rather than a null one. A share count dated `d` is
    struck after the close of `d` and appears on the issuer's site overnight; one full day is a
    stand-in that is never optimistic. If it is ever measured, the constant is replaced by the
    measurement and not by a guess in the other direction (D612's `gdelt_available_at` note,
    same shape, same reason).
  * **Robinhood holders**: the archive's own poll timestamp plus `HOLDERS_LAG`, one full
    polling interval. The archive is a scrape of a public endpoint, so the datum existed at the
    poll instant; the hour is the interval at which it could be OBSERVED, and a series read at
    its own observation instant is a series read with no latency at all, which no operator has.
  * **GDELT**: the publication timestamp, which is D612's `available()` and unchanged.

NO WRITER LIVES HERE, exactly as in D612. Raw responses are kept by `Recorder` (D608); derived
fixtures are written by `scripts/build_robintrack_funds.py` and `scripts/fetch_gdelt_hourly.py`.
`tests/unit/test_retail_attention.py` asserts this module's namespace holds no writer.

NO RETURN IS COMPUTED ANYWHERE IN D621, no price bar is read, and every measurement in the
record is taken on rows dated 2023-12-31 or earlier — the Robintrack archive ends 2020-08-13 and
`fund_nav_daily` is read through `panels.load_panel(..., reserved_from="2024-01-01")`.
"""

from __future__ import annotations

import datetime as dt
import gzip
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .attention import (
    ACCEL_HOURS,
    MIN_MATCHED_OBS,
    TRAILING_DAYS,
    AttentionError,
    InsufficientHistory,
    LookaheadRefused,
    ResolutionRefused,
    att_accel,
    att_level,
    refuse_coarse_resolution,
    zscore_matched,
)

__all__ = [
    "ACCEL_DAYS",
    "CREATION_LAG",
    "CREATION_TRAILING_DAYS",
    "GDELT_HOURLY_OK",
    "HOLDERS_LAG",
    "HOLDER_COLUMNS",
    "MAX_GAP_DAYS",
    "MIN_CREATION_OBS",
    "NO_WRITER_HERE",
    "OUTAGES",
    "ROBINTRACK_SPAN",
    "CreationSeries",
    "HolderObs",
    "NewsSeries",
    "RetailAttention",
    "RetailAttentionError",
    "creation_accel",
    "creation_available_at",
    "creation_level",
    "creation_z",
    "creations",
    "daily_holders",
    "holders_available_at",
    "holders_z",
    "in_outage",
    "news_n_hourly",
    "pearson",
    "quantile_linear",
    "rank_average",
    "read_holder_fixture",
    "robinhood_holders",
    "spearman",
]

UTC = dt.timezone.utc

# ------------------------------------------------------------------ the constants, each declared
#: The z window for a DAILY series, in CALENDAR days. Same number as the deposit's line 255 and
#: D612's `TRAILING_DAYS`, imported rather than retyped so the two cannot drift.
CREATION_TRAILING_DAYS = TRAILING_DAYS

#: D612's floor on matched observations, imported for the same reason. A z over fewer than five
#: points is a ratio of two noisy numbers whatever the series is.
MIN_CREATION_OBS = MIN_MATCHED_OBS

#: The deposit's line 262 window, three against three, imported from `ACCEL_HOURS` because
#: `creation_accel` DELEGATES to `att_accel` and a second copy of the 3 could disagree with the
#: function it is passed to.
ACCEL_DAYS = ACCEL_HOURS

#: THE LONGEST GAP BETWEEN TWO CONSECUTIVE OBSERVATIONS THAT IS STILL ONE STEP OF THE SERIES.
#: A daily fund series is a TRADING-day series: Friday to Monday is three calendar days and is
#: one step; Thursday to the following Tuesday over a long weekend is five and is still one
#: step. Six or more means a suspension, a delisting or a hole in the source, and a difference
#: taken across it is not a day's creation. Days beyond this are DROPPED AND NAMED
#: (`CreationSeries.skipped`), never silently differenced and never interpolated.
MAX_GAP_DAYS = 5

#: **The creation publication lag, declared conservative.** See the module docstring: the source
#: states no publication time, so a share count dated `d` is treated as first usable at the start
#: of `d + 1 day`. Unconditional and with no branch in it, for D612's reason — a rule with a
#: branch can take the wrong branch, and the wrong branch here is a look-ahead (R9).
CREATION_LAG = dt.timedelta(days=1)

#: **The Robinhood holder lag, declared conservative.** The archive polled at a ~1.00 h median
#: cadence (measured over all six funds' full series, 2026-09-22), so one full interval after the
#: poll is the first instant a reader on the same cadence could hold the number.
HOLDERS_LAG = dt.timedelta(hours=1)

#: The archive's span, from `docs/data-available.md` §3 and re-measured here on the six funds.
ROBINTRACK_SPAN = (dt.date(2018, 5, 2), dt.date(2020, 8, 13))

#: **The two site outages, as half-open UTC intervals `[start, end)`.** Measured on all six
#: fund files, 2026-09-22: every one of them has its longest two gaps at exactly these two
#: places, 152.5 h and 238.0 h. An hour inside one of these is `None` — NO DATUM — and never 0,
#: which is the one substantive reading error this series invites: a zero holder count for a
#: fund with 137,000 holders would be a -137,000 change on the day the site came back.
OUTAGES: tuple[tuple[dt.datetime, dt.datetime], ...] = (
    (dt.datetime(2019, 1, 23, 23, 45, tzinfo=UTC), dt.datetime(2019, 1, 30, 8, 15, tzinfo=UTC)),
    (dt.datetime(2020, 1, 6, 8, 49, tzinfo=UTC), dt.datetime(2020, 1, 16, 6, 46, tzinfo=UTC)),
)

#: The `date_resolution` spellings `news_n_hourly` accepts when the caller passes
#: `accept_hourly=True`. Anything coarser — "day", "month" — is refused by
#: `refuse_coarse_resolution` exactly as before, and anything at or below 15 minutes is accepted
#: by it. This set is the WIDENING and it is the only widening.
GDELT_HOURLY_OK = ("hour", "hourly", "1hour", "1 hour", "60min", "60 min", "hours")

NO_WRITER_HERE = (
    "This module never writes a file. Raw responses are kept by "
    "backtest_framework.data.recorder.Recorder (D608); the two derived fixtures are written by "
    "scripts/build_robintrack_funds.py and scripts/fetch_gdelt_hourly.py, and the validation "
    "JSON by scripts/retail_attention_report.py. There is no writer in this namespace and there "
    "must never be one."
)
#: D612's guard, unchanged: the only public name that may match is the constant stating the rule.
FORBIDDEN_NAME_RE = re.compile(r"write|save|dump_to|upload|post_|put_|persist|store", re.I)

_TICKER_RE = re.compile(r"^[A-Z]{1,6}$")


class RetailAttentionError(AttentionError):
    """Base for D621's own loud failures. Subclasses D612's `AttentionError` so a caller that
    already catches the attention layer's base catches these too; D48, no silent default."""


def _aware_utc(when: dt.datetime, what: str) -> dt.datetime:
    if not isinstance(when, dt.datetime):
        raise RetailAttentionError(f"{what} must be a datetime, got {type(when).__name__}")
    if when.tzinfo is None:
        raise RetailAttentionError(f"{what} is naive: {when!r}. Every instant here is aware UTC.")
    return when.astimezone(UTC)


def _plain_date(day: object, what: str) -> dt.date:
    if not isinstance(day, dt.date) or isinstance(day, dt.datetime):
        raise RetailAttentionError(f"{what} must be a datetime.date, got {type(day).__name__}")
    return day


def _finite(value: object, what: str) -> float:
    v = float(value)  # type: ignore[arg-type]
    if not math.isfinite(v):
        raise RetailAttentionError(f"{what} is not finite: {value!r}")
    return v


# ============================================================================== CREATIONS
@dataclass(frozen=True)
class CreationSeries:
    """One fund's daily creations, and the day-steps that were refused.

    `deltas` is `(day, shares_out[day] - shares_out[prev])` for every day whose predecessor is
    within `MAX_GAP_DAYS` calendar days, in date order. `skipped` is `(day, gap_days)` for every
    day whose predecessor is further away than that: the day is in the source, its difference is
    not a day's creation, and it is NAMED rather than dropped quietly.

    The first day of a series appears in neither list: it has no predecessor, so it has no
    creation, and inventing one from zero would make the fund's launch look like its largest
    creation day ever.
    """

    fund: str
    deltas: tuple[tuple[dt.date, float], ...]
    skipped: tuple[tuple[dt.date, int], ...]
    steps: tuple[tuple[dt.date, dt.date], ...] = ()
    """`(day, the day it was differenced against)`, in the same order as `deltas`. Carried so
    that a caller pairing a SECOND series against these creations differences it over the SAME
    interval rather than over `day - 1 day`. D621's validation pairs a holder count against a
    share count and the intervals must be the same interval or the correlation is between two
    different windows."""

    @property
    def days(self) -> tuple[dt.date, ...]:
        return tuple(d for d, _ in self.deltas)

    def value(self, day: dt.date) -> float:
        for d, v in self.deltas:
            if d == day:
                return v
        raise RetailAttentionError(f"{self.fund}: no creation for {day}")

    def prev_day(self, day: dt.date) -> dt.date:
        for d, p in self.steps:
            if d == day:
                return p
        raise RetailAttentionError(f"{self.fund}: no step ending {day}")


def creations(
    shares_out_by_day: Mapping[dt.date, float],
    *,
    fund: str = "",
    max_gap_days: int = MAX_GAP_DAYS,
) -> CreationSeries:
    """`Δshares_out` per day — the ledger's own creation quantity, computed once, here.

    A creation is `shares_out[d] - shares_out[prev(d)]` where `prev(d)` is the IMMEDIATELY
    PRECEDING DAY PRESENT IN THE SOURCE, not `d - 1 day`: a fund series has no Saturday and no
    Christmas, and differencing against an absent calendar day would make every Monday a
    three-day creation labelled as one day's. Gaps longer than `max_gap_days` are refused and
    listed in `CreationSeries.skipped`.

    Note on UNITS, because it decides what the number means: `fund_nav_daily`'s `shares_out` is
    the issuer's published count multiplied by 1000 and is exact to 10 shares (D619's meta), and
    the ProShares series is FULLY BACK-ADJUSTED for reverse splits. Back-adjustment is what makes
    a difference meaningful here — an unadjusted series jumps by a factor of ten at a 1:10
    reverse split with no money moving at all — but it also means the unit is adjusted shares and
    a creation in 2018 is not comparable in COUNT to one in 2026. Every statistic D621 computes
    is scale-free within a fund (a rank correlation, a z, a percentile share), so the adjustment
    does not enter; a study that wants dollars must multiply by the same day's NAV.
    """
    if not isinstance(max_gap_days, int) or isinstance(max_gap_days, bool) or max_gap_days < 1:
        raise RetailAttentionError(f"max_gap_days must be an int >= 1, got {max_gap_days!r}")
    items: list[tuple[dt.date, float]] = []
    for key, value in shares_out_by_day.items():
        day = _plain_date(key, "shares_out_by_day key")
        items.append((day, _finite(value, f"shares_out[{day}]")))
    items.sort(key=lambda kv: kv[0])
    seen = {d for d, _ in items}
    if len(seen) != len(items):
        raise RetailAttentionError("shares_out_by_day holds a day twice; a day has one count")

    deltas: list[tuple[dt.date, float]] = []
    skipped: list[tuple[dt.date, int]] = []
    steps: list[tuple[dt.date, dt.date]] = []
    for i in range(1, len(items)):
        prev_day, prev_val = items[i - 1]
        day, val = items[i]
        gap = (day - prev_day).days
        if gap > max_gap_days:
            skipped.append((day, gap))
            continue
        deltas.append((day, val - prev_val))
        steps.append((day, prev_day))
    return CreationSeries(
        fund=str(fund), deltas=tuple(deltas), skipped=tuple(skipped), steps=tuple(steps)
    )


def creation_available_at(day: dt.date) -> dt.datetime:
    """**When a creation dated `day` may first be used**: midnight UTC at the start of
    `day + CREATION_LAG`. Unconditional, never optimistic; see the module docstring."""
    d = _plain_date(day, "day")
    return dt.datetime.combine(d + CREATION_LAG, dt.time(0, 0), tzinfo=UTC)


Match = Literal["all_days", "same_weekday"]


def creation_z(
    deltas: Sequence[tuple[dt.date, float]],
    day: dt.date,
    *,
    match: Match = "all_days",
    trailing_days: int = CREATION_TRAILING_DAYS,
    min_obs: int = MIN_CREATION_OBS,
) -> float:
    """z of `day`'s creation against the SAME FUND's prior creations in the trailing window.

    `match="same_weekday"` is D612's rule and DELEGATES to `attention.zscore_matched` — the
    observations are handed to it on a constant pseudo-hour of 0, so the hour clause is satisfied
    trivially and the weekday clause is the one that bites. `match="all_days"` is the default and
    uses every prior day in the window; the two agree exactly when the window's members happen to
    share the scored day's weekday, which the golden pins.

    Both refuse a same-day or later observation with `LookaheadRefused` rather than filtering it.
    R9 is the price list for a filtered window: a monotone effect spanning 465 percentage points
    that vanished entirely once its conditioner was lagged by one bar, in a script whose author
    did not think a descriptive cut needed a guard.

    The window is `day - trailing_days <= obs <= day - 1`, both ends inclusive, which is the
    deposit's `t-60 ... t-1` (its unit test 21). An observation older than the window is DROPPED,
    not an error — it is not a leak, it is old. The denominator is the SAMPLE standard deviation,
    ddof = 1, which is `zscore_matched`'s choice and is pinned in the golden.
    """
    scored_day = _plain_date(day, "day")
    if match not in ("all_days", "same_weekday"):
        raise RetailAttentionError(f"match must be all_days|same_weekday, got {match!r}")
    if not isinstance(trailing_days, int) or trailing_days < 1:
        raise RetailAttentionError(f"trailing_days must be an int >= 1, got {trailing_days!r}")

    obs: list[tuple[dt.date, int, float]] = []
    for i, item in enumerate(deltas):
        if not isinstance(item, tuple) or len(item) != 2:
            raise RetailAttentionError(f"deltas[{i}] must be (day, value), got {item!r}")
        d = _plain_date(item[0], f"deltas[{i}][0]")
        obs.append((d, 0, _finite(item[1], f"deltas[{i}][1]")))

    if match == "same_weekday":
        return zscore_matched(
            obs, scored_day, 0, trailing_days=trailing_days, min_obs=min_obs
        )

    # ---- all_days. The SAME arithmetic zscore_matched runs, over a wider window. The equality
    # is asserted in the golden and in tests/unit/test_retail_attention.py on an input where the
    # two windows coincide; two copies of one fact are this repository's most repeated defect,
    # and a copy that is checked against its original is not one.
    first = scored_day - dt.timedelta(days=trailing_days)
    scored: float | None = None
    matched: list[float] = []
    for i, (d, _h, v) in enumerate(obs):
        if d == scored_day:
            if scored is not None:
                raise RetailAttentionError(f"two creations for the scored day {scored_day}")
            scored = v
            continue
        if d > scored_day:
            raise LookaheadRefused(
                f"deltas[{i}] is dated {d}, after the scored day {scored_day}. The window is "
                f"days t-{trailing_days} to t-1 (deposit line 255); an observation from the "
                f"future is not filtered here, it is refused."
            )
        if d < first:
            continue
        matched.append(v)

    if scored is None:
        raise RetailAttentionError(
            f"no creation for the scored day {scored_day}; there is nothing to score against "
            f"the trailing window."
        )
    if len(matched) < min_obs:
        raise InsufficientHistory(
            f"{len(matched)} prior creations in the {trailing_days} days before {scored_day}, "
            f"below the stated minimum of {min_obs}."
        )
    n = len(matched)
    mean = math.fsum(matched) / n
    var = math.fsum((x - mean) ** 2 for x in matched) / (n - 1)
    sd = math.sqrt(var)
    if sd == 0.0:
        raise InsufficientHistory(
            f"the {n} prior creations before {scored_day} are all {mean}; a z-score has no "
            f"denominator. This is a fund whose share count did not move, not a quiet one."
        )
    return (scored - mean) / sd


def creation_level(zs: Mapping[str, float]) -> float:
    """**This IS the deposit's `att_level`** (line 261, *"Mean of available z-scores"*), called
    rather than re-implemented, with the mapping keyed on FUND instead of on source.

    A fund with no z is absent from the mapping and contributes nothing — it does not contribute
    a zero, because a zero z is "an exactly average creation day" and an absent fund is "no
    measurement". An empty mapping raises, in `att_level` itself.
    """
    return att_level(zs)


def creation_accel(
    levels: Sequence[tuple[dt.date, float]],
    day: dt.date,
    *,
    max_gap_days: int = MAX_GAP_DAYS,
) -> float:
    """The daily analogue of `att_accel`: mean of the last three days minus mean of the prior
    three, **computed by `attention.att_accel` itself**.

    The six daily levels ending at `day` are laid on a six-hour axis and handed to `att_accel`,
    so the arithmetic — `math.fsum` over three doubles, divided by the integer 3, subtracted —
    is D612's and not a second copy of it. Two consequences come with the delegation and both
    are wanted: a constant series returns EXACTLY 0.0, and a hole RAISES.

    A "hole" here is a calendar gap longer than `max_gap_days` between two of the six
    observations. Six consecutive entries must exist in `levels` ending at `day`; a missing
    market day inside the run is caught by the gap test, and fewer than six entries raises.
    """
    scored_day = _plain_date(day, "day")
    span = 2 * ACCEL_DAYS
    items: list[tuple[dt.date, float]] = []
    for i, item in enumerate(levels):
        if not isinstance(item, tuple) or len(item) != 2:
            raise RetailAttentionError(f"levels[{i}] must be (day, value), got {item!r}")
        items.append((_plain_date(item[0], f"levels[{i}][0]"), _finite(item[1], f"levels[{i}][1]")))
    items.sort(key=lambda kv: kv[0])
    index = [d for d, _ in items]
    if scored_day not in index:
        raise InsufficientHistory(
            f"creation_accel at {scored_day}: that day is not in the level series at all, so "
            f"there is no window ending on it."
        )
    end = index.index(scored_day)
    if end + 1 < span:
        raise InsufficientHistory(
            f"creation_accel at {scored_day} needs {span} consecutive daily levels ending on it; "
            f"the series holds {end + 1} up to and including that day."
        )
    window = items[end + 1 - span : end + 1]
    for k in range(1, span):
        gap = (window[k][0] - window[k - 1][0]).days
        if gap > max_gap_days:
            raise InsufficientHistory(
                f"creation_accel at {scored_day}: {window[k - 1][0]} to {window[k][0]} is a gap "
                f"of {gap} calendar days, beyond {max_gap_days}. A missing stretch is not "
                f"interpolated and the six days are not six days."
            )
    base = dt.datetime(2000, 1, 1, 0, 0, tzinfo=UTC)
    by_hour = {base + dt.timedelta(hours=k): v for k, (_d, v) in enumerate(window)}
    return att_accel(by_hour, base + dt.timedelta(hours=span - 1))


# ======================================================================= ROBINHOOD HOLDERS
@dataclass(frozen=True)
class HolderObs:
    """One row of `data/fixtures/robintrack_energy_funds.csv.gz`.

    `ts_utc` is the archive's own poll instant. `holders` is the count of Robinhood accounts
    holding the ticker at that poll — an ACCOUNT count, never a share count and never a dollar
    amount, which is the whole reason the series is worth pairing with creations.
    """

    ticker: str
    ts_utc: dt.datetime
    holders: int


def in_outage(when: dt.datetime, *, outages: Sequence[tuple[dt.datetime, dt.datetime]] = OUTAGES
              ) -> bool:
    """True iff `when` falls inside a declared site outage, `[start, end)`."""
    t = _aware_utc(when, "when")
    return any(_aware_utc(a, "outage start") <= t < _aware_utc(b, "outage end") for a, b in outages)


def robinhood_holders(
    observations: Sequence[HolderObs], ticker: str, hour: dt.datetime
) -> int | None:
    """The holder count for `ticker` in the hour STARTING at `hour`, or `None`.

    `None` and never 0. **The one substantive reading error this series invites is a missing
    poll read as a zero**: the archive's two site outages are 6.4 and 9.9 days long, and a zero
    across one of them would show USO losing 144,000 holders overnight and regaining them ten
    days later — two of the largest "flows" in the sample, both fictional. A caller that wants a
    number where there is none must say so in its own code, where it is visible.

    When the hour holds more than one poll the LAST one is returned, because an hour's datum is
    what a reader at the end of it would have seen.
    """
    t = _aware_utc(hour, "hour")
    if t != t.replace(minute=0, second=0, microsecond=0):
        raise RetailAttentionError(f"hour {hour!r} is not on an hour boundary")
    tick = _checked_ticker(ticker)
    end = t + dt.timedelta(hours=1)
    best: HolderObs | None = None
    for i, obs in enumerate(observations):
        if not isinstance(obs, HolderObs):
            raise RetailAttentionError(f"observations[{i}] is a {type(obs).__name__}, not HolderObs")
        if obs.ticker != tick:
            continue
        ts = _aware_utc(obs.ts_utc, "HolderObs.ts_utc")
        if t <= ts < end and (best is None or ts >= _aware_utc(best.ts_utc, "best")):
            best = obs
    return None if best is None else int(best.holders)


def daily_holders(
    observations: Sequence[HolderObs], ticker: str, day: dt.date
) -> int | None:
    """The holder count at the END of the UTC day `day`, or `None` when the day holds no poll.

    **The daily cut is the END OF THE UTC DAY and this is a declared choice, not an inherited
    one.** The archive polls around the clock at a ~1 h cadence and its timestamps are UTC (the
    hour-of-day histogram is flat across all 24 hours on all six funds, which a US-local-time
    series could not be). 00:00 UTC is 19:00 or 20:00 New York, so the last poll of a UTC day is
    three to four hours AFTER the US close and the count it carries is the day's finished count.
    The alternative — cutting at 21:00 UTC, the close — would be defensible too and would move
    the boundary by one poll; it is not used, and the record says so, because a boundary chosen
    silently is a boundary nobody can check.
    """
    d = _plain_date(day, "day")
    tick = _checked_ticker(ticker)
    start = dt.datetime.combine(d, dt.time(0, 0), tzinfo=UTC)
    end = start + dt.timedelta(days=1)
    best: HolderObs | None = None
    for i, obs in enumerate(observations):
        if not isinstance(obs, HolderObs):
            raise RetailAttentionError(f"observations[{i}] is a {type(obs).__name__}, not HolderObs")
        if obs.ticker != tick:
            continue
        ts = _aware_utc(obs.ts_utc, "HolderObs.ts_utc")
        if start <= ts < end and (best is None or ts >= _aware_utc(best.ts_utc, "best")):
            best = obs
    return None if best is None else int(best.holders)


#: The three columns of `data/fixtures/robintrack_energy_funds.csv.gz`, in order.
HOLDER_COLUMNS: tuple[str, ...] = ("ticker", "ts_utc", "holders")


def read_holder_fixture(path: str | Path) -> list[HolderObs]:
    """The holder fixture back as `HolderObs`, through the same guards its builder applied.

    THE READER LIVES HERE, NOT IN THE BUILDER, so that the report script does not have to import
    a sibling runner to read a fixture. `scripts/` is not a package and importing a runner by
    path runs its module body; a two-script cycle over one CSV reader is not worth that, and a
    reader is library surface in any case. **This still writes nothing** — the module's no-writer
    guarantee is about writers, and `open(..., "rt")` on a gzip stream is not one.

    Every failure raises. A `holders` cell that is not a non-negative integer, a timestamp that
    is not `YYYY-MM-DDTHH:MM:SSZ`, or a header that is not `HOLDER_COLUMNS` stops the read rather
    than being coerced: a coerced holder count is the fictional flow this whole series exists to
    avoid.
    """
    out: list[HolderObs] = []
    with gzip.open(path, "rt", encoding="utf-8", newline="") as fh:
        header = tuple(fh.readline().rstrip("\n").split(","))
        if header != HOLDER_COLUMNS:
            raise RetailAttentionError(f"fixture header {header}, want {HOLDER_COLUMNS}")
        for n, line in enumerate(fh, start=2):
            parts = line.rstrip("\n").split(",")
            if len(parts) != len(HOLDER_COLUMNS):
                raise RetailAttentionError(f"line {n} has {len(parts)} cells, want 3: {line!r}")
            ticker, stamp, holders = parts
            if not holders.isdigit():
                raise RetailAttentionError(
                    f"line {n}: holders {holders!r} is not a non-negative integer"
                )
            try:
                when = dt.datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
            except ValueError as exc:
                raise RetailAttentionError(
                    f"line {n}: ts_utc {stamp!r} is not 'YYYY-MM-DDTHH:MM:SSZ'"
                ) from exc
            out.append(
                HolderObs(ticker=_checked_ticker(ticker), ts_utc=when, holders=int(holders))
            )
    return out


def holders_available_at(ts_utc: dt.datetime) -> dt.datetime:
    """**When a holder poll may first be used** — its own instant plus `HOLDERS_LAG`."""
    return _aware_utc(ts_utc, "ts_utc") + HOLDERS_LAG


def holders_z(
    observations: Sequence[tuple[dt.date, int, float]],
    day: dt.date,
    hour: int,
    *,
    trailing_days: int = CREATION_TRAILING_DAYS,
    min_obs: int = MIN_CREATION_OBS,
) -> float:
    """**D612's `zscore_matched`, applied to the hourly holder series.** Same hour-of-day, same
    weekday, trailing 60 days, prior data only, sample sd.

    This function exists so that the holder series is scored by the rule the deposit's line 255
    states for its attention series and not by a second rule invented here. It adds nothing and
    is deliberately three lines long; the argument for why the DAILY creation series does NOT use
    this window is in `creation_z` and in the record.
    """
    return zscore_matched(
        observations, _plain_date(day, "day"), hour, trailing_days=trailing_days, min_obs=min_obs
    )


def _checked_ticker(ticker: object) -> str:
    if not isinstance(ticker, str) or not _TICKER_RE.match(ticker):
        raise RetailAttentionError(f"ticker {ticker!r} is not 1-6 uppercase letters")
    return ticker


# =============================================================================== GDELT, HOURLY
@dataclass(frozen=True)
class NewsSeries:
    """A parsed `timelinevolraw` (or `timelinetone`) response.

    `resolution` is the API's OWN `query_details.date_resolution`, carried on the object so that
    a consumer can never mistake an hourly series for the deposit's 15-minute one. `points` is
    `(instant, value)` in the order the API returned them, each instant aware UTC.
    """

    query: str
    mode: str
    resolution: str
    points: tuple[tuple[dt.datetime, float], ...]

    @property
    def total(self) -> float:
        return math.fsum(v for _t, v in self.points)


_API_STAMP = re.compile(r"^\d{8}T\d{6}Z$")


def news_n_hourly(
    payload: Mapping[str, object], *, accept_hourly: bool, mode: str = "timelinevolraw"
) -> NewsSeries:
    """Parse a GDELT DOC 2.0 timeline response into a `NewsSeries`, refusing a coarse bucket.

    **THE RESOLUTION RULE, AND WHY THERE ARE TWO OF THEM.** The deposit's `news_n` is a 60-minute
    count built out of 15-minute blocks (its lines 251 and 265), so `headline_burst` cannot be
    computed from an hourly bucket at all and `attention.refuse_coarse_resolution` refuses one.
    D621's news series is hourly on purpose — it is paired with a daily creation series — and the
    API autoscales its bucket to the span asked for, answering "hour" for anything wider than a
    few days. So:

        accept_hourly=False  ->  attention.refuse_coarse_resolution, unchanged. 15 min or finer.
        accept_hourly=True   ->  the same function first; if it refuses, an hourly spelling from
                                 GDELT_HOURLY_OK is accepted and NOTHING ELSE. "day" and "month"
                                 still raise.

    The accepted spelling travels on `NewsSeries.resolution`, so the widening is visible in every
    row a consumer holds rather than in a flag it has to remember to check.

    The API's own stamp format is `YYYYMMDDTHHMMSSZ`; anything else raises rather than being
    guessed at, because a misparsed instant is a series silently shifted in time.
    """
    if not isinstance(accept_hourly, bool):
        raise RetailAttentionError(f"accept_hourly must be a bool, got {accept_hourly!r}")
    details = payload.get("query_details")
    if not isinstance(details, Mapping):
        raise RetailAttentionError(
            "the response carries no query_details mapping, so its bucket width is unknown. An "
            "unlabelled timeline is not recorded as a feature value."
        )
    raw_resolution = details.get("date_resolution")
    try:
        resolution = refuse_coarse_resolution(raw_resolution)
    except ResolutionRefused:
        text = str(raw_resolution).strip().lower()
        if not accept_hourly or text not in GDELT_HOURLY_OK:
            raise
        resolution = text

    timeline = payload.get("timeline")
    if not isinstance(timeline, Sequence) or isinstance(timeline, str | bytes) or not timeline:
        raise RetailAttentionError(f"the response carries no timeline array: {timeline!r}")
    series = timeline[0]
    if not isinstance(series, Mapping):
        raise RetailAttentionError(f"timeline[0] is a {type(series).__name__}, not a mapping")
    data = series.get("data")
    if not isinstance(data, Sequence) or isinstance(data, str | bytes):
        raise RetailAttentionError(f"timeline[0].data is not an array: {data!r}")

    points: list[tuple[dt.datetime, float]] = []
    for i, row in enumerate(data):
        if not isinstance(row, Mapping):
            raise RetailAttentionError(f"timeline[0].data[{i}] is not a mapping: {row!r}")
        stamp = str(row.get("date", ""))
        if not _API_STAMP.match(stamp):
            raise RetailAttentionError(
                f"timeline[0].data[{i}].date is {stamp!r}; the DOC API's stamp is "
                f"YYYYMMDDTHHMMSSZ and a stamp this module cannot parse is not guessed at."
            )
        when = dt.datetime.strptime(stamp, "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
        points.append((when, _finite(row.get("value"), f"data[{i}].value")))
    for k in range(1, len(points)):
        if points[k][0] <= points[k - 1][0]:
            raise RetailAttentionError(
                f"the timeline is not strictly increasing at index {k}: "
                f"{points[k - 1][0].isoformat()} then {points[k][0].isoformat()}"
            )
    return NewsSeries(
        query=str(details.get("query") or payload.get("query") or ""),
        mode=str(mode),
        resolution=resolution,
        points=tuple(points),
    )


# ============================================================================== THE BUNDLE
@dataclass(frozen=True)
class RetailAttention:
    """The three replacement series at one instant, each with the time it became usable.

    **Nothing is combined here.** The deposit's `att_level` is a mean of z-scores and D621 does
    not take one across series measured on different clocks: a daily creation z and an hourly
    news z are not two readings of one quantity. The bundle's job is to make the three
    availability times visible side by side, and to RAISE when a component is quoted at an
    instant it could not have been read at.
    """

    tau: dt.datetime
    creation_day: dt.date | None = None
    creation_value: float | None = None
    holders_ts: dt.datetime | None = None
    holders_value: int | None = None
    news: NewsSeries | None = None
    news_published_at: dt.datetime | None = None

    def __post_init__(self) -> None:
        tau = _aware_utc(self.tau, "tau")
        if (self.creation_day is None) != (self.creation_value is None):
            raise RetailAttentionError("creation_day and creation_value travel together or not at all")
        if (self.holders_ts is None) != (self.holders_value is None):
            raise RetailAttentionError("holders_ts and holders_value travel together or not at all")
        if (self.news is None) != (self.news_published_at is None):
            raise RetailAttentionError("news and news_published_at travel together or not at all")
        for name, when in self.available_at().items():
            if when > tau:
                raise LookaheadRefused(
                    f"{name} became available at {when.isoformat()}, after tau "
                    f"{tau.isoformat()}. A component is not carried into a bundle that predates "
                    f"it; that is the look-ahead the point-in-time rules exist to stop."
                )

    def available_at(self) -> dict[str, dt.datetime]:
        """`{component: the instant it may first be used}`, for the components that are present."""
        out: dict[str, dt.datetime] = {}
        if self.creation_day is not None:
            out["creations"] = creation_available_at(self.creation_day)
        if self.holders_ts is not None:
            out["holders"] = holders_available_at(self.holders_ts)
        if self.news_published_at is not None:
            out["news"] = _aware_utc(self.news_published_at, "news_published_at")
        return out


# =========================================================================== THE STATISTICS
def rank_average(values: Sequence[float]) -> tuple[float, ...]:
    """Fractional ranks, 1-based, ties taking the AVERAGE of the ranks they span.

    The tie rule is stated because it is a choice and because it changes the number: on
    `[1, 2, 2, 3]` the average rule gives `(1, 2.5, 2.5, 4)` where an ordinal rule would give
    `(1, 2, 3, 4)` and make the result depend on the input's order.
    """
    vals = [_finite(v, f"values[{i}]") for i, v in enumerate(values)]
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    ranks = [0.0] * len(vals)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        shared = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = shared
        i = j + 1
    return tuple(ranks)


def pearson(x: Sequence[float], y: Sequence[float]) -> float:
    """The product-moment correlation. Raises on fewer than three pairs or a constant input."""
    xs, ys = _paired(x, y)
    n = len(xs)
    mx = math.fsum(xs) / n
    my = math.fsum(ys) / n
    sxx = math.fsum((v - mx) ** 2 for v in xs)
    syy = math.fsum((v - my) ** 2 for v in ys)
    sxy = math.fsum((a - mx) * (b - my) for a, b in zip(xs, ys, strict=True))
    if sxx == 0.0 or syy == 0.0:
        raise InsufficientHistory(
            "a correlation with a constant series has no denominator; there is nothing to "
            "correlate with, and returning 0.0 would read as 'measured, no relationship'."
        )
    return sxy / math.sqrt(sxx * syy)


def spearman(x: Sequence[float], y: Sequence[float]) -> float:
    """The rank correlation — `pearson` of `rank_average`, ties averaged.

    Reported BESIDE the Pearson and never instead of it. A holder series with one meme-era spike
    in it is exactly the input on which the two disagree by half, and the golden's Case 1 is that
    disagreement written out: 0.9394 against 0.4777 on ten rows where one value is an outlier.
    """
    xs, ys = _paired(x, y)
    return pearson(rank_average(xs), rank_average(ys))


def quantile_linear(values: Sequence[float], p: float) -> float:
    """The `p`-quantile by linear interpolation between order statistics (numpy's default,
    Hyndman-Fan type 7). Stated rather than inherited: the rule changes the answer by a whole
    rank on ten points, and D621's "creation day" is defined by it."""
    vals = sorted(_finite(v, f"values[{i}]") for i, v in enumerate(values))
    if not vals:
        raise InsufficientHistory("no values to take a quantile of")
    q = _finite(p, "p")
    if not 0.0 <= q <= 1.0:
        raise RetailAttentionError(f"p must be in [0, 1], got {p!r}")
    h = (len(vals) - 1) * q
    lo = math.floor(h)
    hi = math.ceil(h)
    if lo == hi:
        return vals[lo]
    return vals[lo] + (h - lo) * (vals[hi] - vals[lo])


def _paired(x: Sequence[float], y: Sequence[float]) -> tuple[list[float], list[float]]:
    xs = [_finite(v, f"x[{i}]") for i, v in enumerate(x)]
    ys = [_finite(v, f"y[{i}]") for i, v in enumerate(y)]
    if len(xs) != len(ys):
        raise RetailAttentionError(f"x has {len(xs)} values and y has {len(ys)}; pairs are pairs")
    if len(xs) < 3:
        raise InsufficientHistory(
            f"{len(xs)} pairs is not a correlation. Two points correlate at exactly +/-1 by "
            f"construction and one point has no variance at all."
        )
    return xs, ys
