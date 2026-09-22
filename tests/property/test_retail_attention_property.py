"""Property tests for `data/retail_attention.py` (D621).

Conventions per D78 as amended by D537: `settings(derandomize=True, max_examples=40,
deadline=None)` — the seed is fixed but the example set is not byte-stable between a full-suite
run and a single-file run, so a failure is reproduced with the whole suite.

WHAT IS WORTH A PROPERTY HERE. The boundaries and the hand arithmetic are pinned by
`tests/golden/test_retail_attention_ledger.hand.txt`, and the closed cases by
`tests/unit/test_retail_attention.py`. What no finite set of examples covers is the SHAPE of the
failures this module exists to prevent, each of which is a statement over all inputs:

  * **a reference window that reaches into the present.** The leak is a relation between two
    dates, so it is quantified over both: for ANY creation series and ANY scored day, injecting
    one observation dated after that day must RAISE — never be filtered, never be ignored. R9 is
    the price list for the alternative.
  * **a difference that does not telescope.** `creations` is the only arithmetic between a raw
    share count and every statistic downstream of it. If the differences do not sum back to the
    change in the level over the same run, the whole measurement is about something else.
  * **an acceleration that is not exactly zero on a constant.** Exactness is a property of the
    summation order over ALL constants, including ones whose mean is not representable, so it is
    quantified over the level rather than asserted at one value.
  * **a rank correlation that is not a rank correlation.** Spearman's whole claim is invariance
    under a strictly increasing transform of either side. Quantified over the values AND over
    the transform, because the defect it guards against — an ordinal rank where a fractional one
    belongs — only shows when there are ties, and hand cases rarely have them.
  * **a holder reader that invents a number.** `robinhood_holders` and `daily_holders` must
    return `None` or a value THAT WAS IN THE INPUT. A synthesised 0 across a ten-day site outage
    is the largest fictional flow this series can produce.

No fixture is read, no return is computed, and every date is drawn inside a synthetic 2019–2020
span — years before the 2024-01-01 reserved slice.
"""

from __future__ import annotations

import datetime as dt
import math

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from backtest_framework.data.attention import InsufficientHistory, LookaheadRefused
from backtest_framework.data.retail_attention import (
    ACCEL_DAYS,
    MAX_GAP_DAYS,
    MIN_CREATION_OBS,
    HolderObs,
    RetailAttentionError,
    creation_accel,
    creation_z,
    creations,
    daily_holders,
    pearson,
    quantile_linear,
    rank_average,
    robinhood_holders,
    spearman,
)

UTC = dt.timezone.utc
SETTINGS = settings(derandomize=True, max_examples=40, deadline=None)

BASE = dt.date(2019, 1, 7)  # a Monday
LEVELS = st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False)
SHARES = st.floats(min_value=1.0, max_value=1e9, allow_nan=False, allow_infinity=False)


def _days(n: int, step: int = 1) -> list[dt.date]:
    return [BASE + dt.timedelta(days=step * k) for k in range(n)]


# ----------------------------------------------------- the leak is a relation between two dates
@SETTINGS
@given(
    values=st.lists(LEVELS, min_size=MIN_CREATION_OBS + 1, max_size=20),
    future_offset=st.integers(min_value=1, max_value=400),
    future_value=LEVELS,
    match=st.sampled_from(["all_days", "same_weekday"]),
)
def test_an_observation_after_the_scored_day_always_raises(
    values, future_offset, future_value, match
):
    """For ANY series and ANY scored day, one observation dated after it must RAISE. It is not
    filtered: a filtered window is indistinguishable from one that never had a leak in it."""
    days = _days(len(values), step=7)  # every day the same weekday, so both windows can score
    scored = days[-1]
    obs = list(zip(days, values, strict=True))
    obs.append((scored + dt.timedelta(days=future_offset), future_value))
    with pytest.raises(LookaheadRefused):
        creation_z(obs, scored, match=match, trailing_days=4000)


@SETTINGS
@given(values=st.lists(LEVELS, min_size=MIN_CREATION_OBS + 1, max_size=20))
def test_the_scored_day_itself_is_never_the_leak(values):
    """The one observation dated ON the scored day is the value being scored and must be
    accepted. A guard that refused it would refuse every call."""
    days = _days(len(values), step=7)
    obs = list(zip(days, values, strict=True))
    try:
        z = creation_z(obs, days[-1], trailing_days=4000)
    except InsufficientHistory:
        return  # a constant window has no denominator; that is a different refusal
    assert math.isfinite(z)


# -------------------------------------------------------------- differences must telescope
@SETTINGS
@given(values=st.lists(SHARES, min_size=2, max_size=25))
def test_creations_telescope_over_a_contiguous_run(values):
    """Sum of the daily creations == the change in the share count over the same run. If this
    fails, every statistic downstream is about a different quantity."""
    days = _days(len(values))
    series = creations(dict(zip(days, values, strict=True)), fund="T")
    assert series.skipped == ()
    total = math.fsum(v for _d, v in series.deltas)
    assert total == pytest.approx(values[-1] - values[0], rel=1e-9, abs=1e-6)


@SETTINGS
@given(values=st.lists(SHARES, min_size=2, max_size=12), gap=st.integers(min_value=1, max_value=40))
def test_a_step_is_kept_exactly_when_its_gap_is_within_the_limit(values, gap):
    """The rule is a single inequality and it must hold at every gap, including the boundary."""
    days = [BASE, BASE + dt.timedelta(days=gap)]
    series = creations({days[0]: values[0], days[1]: values[-1]}, fund="T")
    if gap <= MAX_GAP_DAYS:
        assert len(series.deltas) == 1 and series.skipped == ()
        assert series.prev_day(days[1]) == days[0]
    else:
        assert series.deltas == () and series.skipped == ((days[1], gap),)


@SETTINGS
@given(values=st.lists(SHARES, min_size=2, max_size=20))
def test_every_delta_has_exactly_one_step_and_the_two_agree(values):
    days = _days(len(values))
    series = creations(dict(zip(days, values, strict=True)), fund="T")
    assert len(series.deltas) == len(series.steps)
    for (day, _v), (step_day, prev) in zip(series.deltas, series.steps, strict=True):
        assert day == step_day and prev < day


# ------------------------------------------------------------- exactness on a constant series
@SETTINGS
@given(level=LEVELS)
def test_creation_accel_is_exactly_zero_on_any_constant(level):
    """`== 0.0`, not `approx`. Both means are `math.fsum` over the same doubles in the same order
    divided by the same integer, so the result is the identical double and the difference is
    +0.0 for every level, including ones whose mean is not representable."""
    days = _days(2 * ACCEL_DAYS)
    assert creation_accel([(d, level) for d in days], days[-1]) == 0.0


@SETTINGS
@given(level=LEVELS, bump=st.floats(min_value=1e-6, max_value=1e5, allow_nan=False))
def test_creation_accel_is_positive_on_any_upward_step(level, bump):
    """A step up in the last three days against a flat prior three is positive, whatever the
    level it sits on."""
    days = _days(2 * ACCEL_DAYS)
    levels = [(d, level) for d in days[:ACCEL_DAYS]] + [(d, level + bump) for d in days[ACCEL_DAYS:]]
    assert creation_accel(levels, days[-1]) > 0.0


# --------------------------------------------------------------- the rank correlation is a rank
@SETTINGS
@given(values=st.lists(st.integers(min_value=-5, max_value=5), min_size=1, max_size=20))
def test_fractional_ranks_always_sum_to_n_times_n_plus_one_over_two(values):
    """The tie rule is "average of the ranks spanned", so however many ties there are the ranks
    are a redistribution of 1..n and their sum is unchanged. An ORDINAL rank would also pass
    this; the next property is the one that separates them."""
    ranks = rank_average([float(v) for v in values])
    n = len(values)
    assert math.fsum(ranks) == pytest.approx(n * (n + 1) / 2.0, rel=1e-12)


@SETTINGS
@given(values=st.lists(st.integers(min_value=-3, max_value=3), min_size=2, max_size=20))
def test_equal_values_always_get_equal_ranks(values):
    """This is what an ordinal rank fails: with an ordinal rule two equal values get different
    ranks and the statistic depends on the input's order."""
    floats = [float(v) for v in values]
    ranks = rank_average(floats)
    for i, a in enumerate(floats):
        for j, b in enumerate(floats):
            if a == b:
                assert ranks[i] == ranks[j]


@SETTINGS
@given(
    xs=st.lists(st.integers(min_value=-50, max_value=50), min_size=3, max_size=20),
    shift=st.floats(min_value=-1e4, max_value=1e4, allow_nan=False),
    scale=st.floats(min_value=1e-3, max_value=1e3, allow_nan=False),
)
def test_spearman_is_exactly_invariant_under_a_strictly_increasing_transform(xs, shift, scale):
    """Spearman's whole claim. `t(v) = scale*v + shift` with `scale > 0` and `t(v) = v**3` are
    both strictly increasing, so the ranks are identical and the statistic must be THE SAME
    DOUBLE, not approximately equal."""
    x = [float(v) for v in xs]
    y = [float(v) * 2.0 - 1.0 for v in xs[::-1]]
    assume(len(set(x)) > 1 and len(set(y)) > 1)
    base = spearman(x, y)
    assert spearman([scale * v + shift for v in x], y) == base
    assert spearman(x, [v**3 for v in y]) == base


@SETTINGS
@given(
    xs=st.lists(st.integers(min_value=-50, max_value=50), min_size=3, max_size=20),
    scale=st.floats(min_value=1e-2, max_value=1e2, allow_nan=False),
)
def test_pearson_is_invariant_under_an_affine_transform_only(xs, scale):
    x = [float(v) for v in xs]
    y = [float(v) * 3.0 + 7.0 for v in xs[::-1]]
    assume(len(set(x)) > 1 and len(set(y)) > 1)
    base = pearson(x, y)
    assert pearson([scale * v + 11.0 for v in x], y) == pytest.approx(base, rel=1e-9, abs=1e-12)


@SETTINGS
@given(
    xs=st.lists(st.integers(min_value=-50, max_value=50), min_size=3, max_size=20),
    ys=st.lists(st.integers(min_value=-50, max_value=50), min_size=3, max_size=20),
)
def test_both_correlations_stay_inside_minus_one_and_one(xs, ys):
    """A correlation outside [-1, 1] is an arithmetic defect and nothing downstream would catch
    it. Quantified over independent inputs, so the pairs are usually uncorrelated."""
    n = min(len(xs), len(ys))
    x = [float(v) for v in xs[:n]]
    y = [float(v) for v in ys[:n]]
    assume(len(set(x)) > 1 and len(set(y)) > 1)
    for value in (pearson(x, y), spearman(x, y)):
        assert -1.0 <= value <= 1.0


@SETTINGS
@given(xs=st.lists(st.integers(min_value=-50, max_value=50), min_size=3, max_size=20))
def test_a_series_correlates_with_itself_at_exactly_one(xs):
    x = [float(v) for v in xs]
    assume(len(set(x)) > 1)
    assert spearman(x, x) == 1.0
    assert pearson(x, x) == pytest.approx(1.0, rel=1e-12)


# ---------------------------------------------------------------------- the quantile is a rule
@SETTINGS
@given(
    values=st.lists(LEVELS, min_size=1, max_size=30),
    p=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
)
def test_a_quantile_is_bounded_by_the_order_statistics(values, p):
    q = quantile_linear(values, p)
    assert min(values) <= q <= max(values)


@SETTINGS
@given(
    values=st.lists(LEVELS, min_size=2, max_size=30),
    a=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    b=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
)
def test_a_quantile_is_monotone_in_p(values, a, b):
    lo, hi = (a, b) if a <= b else (b, a)
    assert quantile_linear(values, lo) <= quantile_linear(values, hi)


@SETTINGS
@given(values=st.lists(LEVELS, min_size=1, max_size=30))
def test_the_endpoints_are_the_min_and_the_max_exactly(values):
    assert quantile_linear(values, 0.0) == min(values)
    assert quantile_linear(values, 1.0) == max(values)


# ------------------------------------------------------- the holder reader never invents a value
@SETTINGS
@given(
    counts=st.lists(st.integers(min_value=0, max_value=500_000), min_size=0, max_size=12),
    offsets=st.lists(st.integers(min_value=0, max_value=71), min_size=0, max_size=12),
    probe=st.integers(min_value=-2, max_value=74),
)
def test_a_holder_read_is_none_or_a_value_that_was_in_the_input(counts, offsets, probe):
    """The one substantive reading error this series invites is a missing poll read as a zero.
    Quantified: whatever is asked for, the answer is `None` or one of the supplied counts."""
    n = min(len(counts), len(offsets))
    hours_present = sorted(set(offsets[:n]))
    rows = [
        HolderObs(
            ticker="USO",
            ts_utc=dt.datetime(2019, 1, 7, tzinfo=UTC) + dt.timedelta(hours=h),
            holders=c,
        )
        for h, c in zip(hours_present, counts[:n], strict=False)
    ]
    hour = dt.datetime(2019, 1, 7, tzinfo=UTC) + dt.timedelta(hours=probe)
    got = robinhood_holders(rows, "USO", hour)
    assert got is None or got in {r.holders for r in rows}
    day = (dt.datetime(2019, 1, 7, tzinfo=UTC) + dt.timedelta(hours=probe)).date()
    daily = daily_holders(rows, "USO", day)
    assert daily is None or daily in {r.holders for r in rows}


@SETTINGS
@given(
    counts=st.lists(st.integers(min_value=0, max_value=500_000), min_size=1, max_size=8),
    day_offset=st.integers(min_value=0, max_value=5),
)
def test_the_daily_cut_is_the_last_poll_of_that_utc_day(counts, day_offset):
    """The rule is "the last poll of the UTC day", so the answer is the count of the largest
    timestamp inside the day and of no other."""
    day = dt.date(2019, 1, 7) + dt.timedelta(days=day_offset)
    rows = [
        HolderObs(
            ticker="USO",
            ts_utc=dt.datetime.combine(day, dt.time(0, 0), tzinfo=UTC) + dt.timedelta(hours=2 * k),
            holders=c,
        )
        for k, c in enumerate(counts)
    ]
    # plus a poll on the NEXT day, which must never be returned for `day`
    rows.append(
        HolderObs(
            ticker="USO",
            ts_utc=dt.datetime.combine(day + dt.timedelta(days=1), dt.time(1), tzinfo=UTC),
            holders=999_999,
        )
    )
    inside = [r for r in rows if r.ts_utc.date() == day]
    want = max(inside, key=lambda r: r.ts_utc).holders if inside else None
    assert daily_holders(rows, "USO", day) == want
    assert daily_holders(rows, "USO", day) != 999_999 or want == 999_999


@SETTINGS
@given(ticker=st.text(min_size=0, max_size=10))
def test_a_ticker_that_is_not_one_to_six_uppercase_letters_raises(ticker):
    assume(not (1 <= len(ticker) <= 6 and ticker.isascii() and ticker.isalpha()
                and ticker.isupper()))
    with pytest.raises(RetailAttentionError):
        daily_holders([], ticker, dt.date(2019, 1, 7))
