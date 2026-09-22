"""Property tests for `data/attention.py` (D612).

Conventions per D78 as amended by D537: `settings(derandomize=True, max_examples=40,
deadline=None)` — the seed is fixed but the example set is not byte-stable between a full-suite
run and a single-file run, so a failure is reproduced with the whole suite.

WHAT IS WORTH A PROPERTY HERE. The boundaries themselves are pinned by
`tests/golden/test_attention_ledger.hand.txt` and the closed cases by `tests/unit/test_attention.py`.
What no finite set of examples covers is the SHAPE of the three failures this module exists to
prevent, each of which is a statement over all inputs rather than at one point:

  * **a reference window that reaches into the present.** The leak is a relation between two
    dates, so it is quantified over both: for ANY observation set and ANY scored day, injecting
    one observation dated on or after that day must RAISE — never be filtered, never be ignored.
  * **an availability filter that is not a filter.** `available()` must return a SUBSEQUENCE of
    its input with every `publication_ts <= tau`, for any mixture of publication and event times.
    Quantified over both timestamps independently, because the defect being guarded against —
    reading `event_ts` — only shows when the two disagree, and they agree in most hand cases.
  * **an acceleration that is not exactly zero on a constant.** Exactness is a property of the
    summation order over ALL constants, including ones where the mean is not representable, so it
    is quantified over the level rather than asserted at 3.5.

No fixture is read, no return is computed, and every date is drawn inside a synthetic 2019 span —
five years before the 2024-01-01 holdout.
"""

from __future__ import annotations

import datetime as dt

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from backtest_framework.data.attention import (
    ACCEL_HOURS,
    MIN_MATCHED_OBS,
    GdeltItem,
    InsufficientHistory,
    LookaheadRefused,
    att_accel,
    att_breadth,
    available,
    gdelt_available_at,
    wiki_available_at,
    wiki_is_available,
    zscore_matched,
)

UTC = dt.timezone.utc
SETTINGS = settings(derandomize=True, max_examples=40, deadline=None)

#: A synthetic span. `day` is always a 2019-11 date so the matched window has room behind it.
scored_days = st.dates(min_value=dt.date(2019, 11, 1), max_value=dt.date(2019, 11, 30))
hours = st.integers(min_value=0, max_value=23)
levels = st.floats(min_value=-50.0, max_value=50.0, allow_nan=False, allow_infinity=False)
instants = st.datetimes(
    min_value=dt.datetime(2019, 1, 1), max_value=dt.datetime(2019, 12, 31)
).map(lambda d: d.replace(tzinfo=UTC))


def _matched(day: dt.date, hour: int, values: list[float]) -> list[tuple[dt.date, int, float]]:
    """`len(values)` observations at the same hour-of-day and weekday, one week apart, all prior."""
    return [(day - dt.timedelta(days=7 * (k + 1)), hour, v) for k, v in enumerate(values)]


# ------------------------------------------------------------------ 1. the look-ahead refusal
@SETTINGS
@given(
    day=scored_days,
    hour=hours,
    values=st.lists(levels, min_size=MIN_MATCHED_OBS, max_size=8),
    offset=st.integers(min_value=0, max_value=20),
    leak_hour=hours,
    leak_value=levels,
)
def test_an_observation_dated_at_or_after_the_scored_day_always_raises(
    day, hour, values, offset, leak_hour, leak_value
):
    """For ANY well-formed input, injecting one observation dated on or after `day` raises.

    It is never filtered. R9: a filtered leak and a window that never had one are
    indistinguishable from the outside, and the difference between them was 465 percentage points.
    """
    obs = _matched(day, hour, values) + [(day, hour, 1.0)]
    leak_day = day + dt.timedelta(days=offset)
    if leak_day == day and leak_hour == hour:
        return  # that IS the scored observation, which must be supplied
    with pytest.raises(LookaheadRefused):
        zscore_matched([*obs, (leak_day, leak_hour, leak_value)], day, hour)


@SETTINGS
@given(day=scored_days, hour=hours, values=st.lists(levels, min_size=MIN_MATCHED_OBS, max_size=8),
       older=st.integers(min_value=61, max_value=400), stale=levels)
def test_an_observation_older_than_the_window_never_changes_the_score(
    day, hour, values, older, stale
):
    """Old is not a leak, so it is DROPPED rather than refused — and dropping it must be
    complete: an observation outside the window cannot move the score by any amount."""
    obs = _matched(day, hour, values) + [(day, hour, 1.0)]
    try:
        base = zscore_matched(obs, day, hour)
    except InsufficientHistory:
        return  # a constant reference window has no denominator; that case is a unit test
    ancient = day - dt.timedelta(days=older)
    if ancient.weekday() != day.weekday():
        ancient -= dt.timedelta(days=(ancient.weekday() - day.weekday()) % 7)
    with_stale = zscore_matched([*obs, (ancient, hour, stale)], day, hour)
    assert with_stale == base


# ------------------------------------------------------------------- 2. the availability filter
@SETTINGS
@given(
    pubs=st.lists(instants, min_size=0, max_size=12),
    events=st.lists(instants, min_size=0, max_size=12),
    tau=instants,
)
def test_available_is_a_subsequence_on_publication_alone(pubs, events, tau):
    """`available()` returns a SUBSEQUENCE of its input, in order, holding exactly the items whose
    PUBLICATION is at or before tau — whatever the event times are.

    The event times are drawn independently of the publication times, because the defect this
    guards against (reading `event_ts`) is invisible whenever the two agree.
    """
    items = [
        GdeltItem(publication_ts=p, event_ts=(events[i] if i < len(events) else None),
                  tone=None, source_url=f"u{i}", matched_queries=("natural_gas",))
        for i, p in enumerate(pubs)
    ]
    got = available(items, tau)
    assert all(i.publication_ts <= tau for i in got)
    assert list(got) == [i for i in items if i.publication_ts <= tau]   # order preserved
    assert set(got) <= set(items)
    # and the event time carries no weight: re-stamping every event leaves the answer identical.
    reflipped = [
        GdeltItem(publication_ts=i.publication_ts, event_ts=dt.datetime(1999, 1, 1, tzinfo=UTC),
                  tone=i.tone, source_url=i.source_url, matched_queries=i.matched_queries)
        for i in items
    ]
    assert [i.source_url for i in available(reflipped, tau)] == [i.source_url for i in got]


@SETTINGS
@given(hour=instants)
def test_the_two_availability_rules_are_never_earlier_than_their_own_datum(hour):
    """A publication rule that can return an instant at or before the datum's own timestamp is a
    look-ahead with extra steps."""
    assert wiki_available_at(hour) - hour == dt.timedelta(minutes=75)
    assert wiki_is_available(hour, wiki_available_at(hour)) is True
    assert wiki_is_available(hour, wiki_available_at(hour) - dt.timedelta(seconds=1)) is False
    assert gdelt_available_at(hour) > hour


# ----------------------------------------------------------------------- 3. att_accel's zero
@SETTINGS
@given(level=levels, start=instants)
def test_att_accel_on_a_constant_series_is_exactly_zero(level, start):
    """EXACTLY 0.0 for any constant, not 'about zero'. The two means are computed from the same
    doubles in the same order, so a rewrite that reorders the sum breaks this and a tolerance
    would hide it."""
    span = 2 * ACCEL_HOURS
    series = {start + dt.timedelta(hours=k): level for k in range(span)}
    assert att_accel(series, start + dt.timedelta(hours=span - 1)) == 0.0


@SETTINGS
@given(base=levels, step=st.floats(min_value=0.0, max_value=20.0, allow_nan=False),
       start=instants)
def test_att_accel_is_translation_invariant_and_monotone_in_the_step(base, step, start):
    """Adding a constant to every hour changes nothing (it is a CHANGE, not a level), and a
    larger step gives a larger acceleration."""
    span = 2 * ACCEL_HOURS
    ramp = {start + dt.timedelta(hours=k): (0.0 if k < ACCEL_HOURS else step) for k in range(span)}
    shifted = {k: v + base for k, v in ramp.items()}
    end = start + dt.timedelta(hours=span - 1)
    assert att_accel(shifted, end) == pytest.approx(att_accel(ramp, end), abs=1e-9)
    assert att_accel(ramp, end) == pytest.approx(step, abs=1e-9)


@SETTINGS
@given(zs=st.dictionaries(st.sampled_from(["news", "wiki", "social"]), levels, max_size=3))
def test_att_breadth_never_exceeds_the_number_of_present_sources(zs):
    """A disabled source (`social`, gated on deposit Q12) has no z and cannot be counted, so the
    reachable maximum is the number of LIVE sources rather than three."""
    n = att_breadth(zs)
    assert 0 <= n <= len(zs)
    assert n == sum(1 for v in zs.values() if v > 2.0)
