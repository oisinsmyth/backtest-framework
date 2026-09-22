"""`ledger/premium.py`: the midpoint rule, the valid minute, the window guard, stress (D611).

Three numbered required unit tests live here -- 15 (the premium reads the midpoint and never the
last trade), 16 (a stale or futures-less minute is excluded from ALL features), 17 (no premium
feature uses a minute at or after W_start) -- plus the refusals that make the first two
checkable rather than merely true today.

The hand-worked day is in `tests/golden/test_ledger_funds_ledger.hand.txt` section 3 and the
numbers are asserted in the golden file. Here the same six minutes are rebuilt so that each
claim can be exercised on its own and on variations of it.
"""

from __future__ import annotations

import datetime as dt
import math

import pytest

from backtest_framework.ledger.premium import (
    C_AP_PRIMARY,
    C_AP_SENSITIVITY,
    MAX_QUOTE_AGE_S,
    STRESS_TRAILING_DAYS,
    Minute,
    PremiumError,
    PremiumWindowError,
    Quote,
    features,
    minute_feature,
    premium,
    stress,
    valid_minute,
)

DAY = dt.date(2026, 9, 18)
W_START = dt.datetime(2026, 9, 18, 14, 28)
INAV = 25.0


def at(minute: int, second: int = 0) -> dt.datetime:
    return dt.datetime(2026, 9, 18, 14, minute, second)


def minute(
    m: int,
    bid: float = 25.02,
    ask: float = 25.04,
    last: float = 25.10,
    age: float = 10.0,
    traded: bool = True,
    volume: float = 100.0,
    signed: float = 0.0,
) -> Minute:
    return Minute(at(m), Quote(bid, ask, last, at(m)), INAV, age, traded, volume, signed)


# ------------------------------------------------------------------ the numbered claims


def test_ledger_15_the_premium_reads_the_midpoint_and_never_the_last_trade():
    """Required unit test 15, line 199, and the crossed-quote refusal beside it.

    The document's own case is "a synthetic series with trades at the ask but a constant mid
    shows zero premium", which is the harder half: a premium computed off the last trade would
    read +8 bp all day on a book whose fair value never moved.
    """
    fair = Quote(bid=24.99, ask=25.01, last=25.01, ts=at(20))
    assert fair.mid == INAV
    assert premium(fair, INAV) == 0.0

    # trades at the ask, all day, with the mid unchanged -> still exactly zero
    for trade in (25.01, 25.01, 25.01):
        assert premium(Quote(24.99, 25.01, trade, at(20)), INAV) == 0.0

    # and `last` cannot move the answer anywhere else either
    quotes = [Quote(25.02, 25.04, last, at(20)) for last in (25.02, 25.04, 25.10, 1.0)]
    values = {premium(q, INAV) for q in quotes}
    assert values == {0.0012000000000000454}

    # a crossed or locked quote has a midpoint and is refused at construction
    for bid, ask in ((25.04, 25.02), (25.03, 25.03)):
        with pytest.raises(PremiumError, match="crossed or locked"):
            Quote(bid, ask, 25.03, at(20))
    with pytest.raises(PremiumError, match="positive"):
        Quote(0.0, 25.02, 25.01, at(20))
    # the denominator is guarded too: a zero iNAV would read as infinite stress downstream
    with pytest.raises(PremiumError, match="iNAV must be positive"):
        premium(fair, 0.0)


def test_ledger_16_a_stale_or_futureless_minute_is_excluded_from_all_features():
    """Required unit test 16, line 200. The exclusion returns None, not 0.0."""
    assert valid_minute(10.0, True) is True
    assert valid_minute(MAX_QUOTE_AGE_S, True) is True  # inclusive at 60 s
    assert valid_minute(60.001, True) is False
    assert valid_minute(10.0, False) is False
    assert valid_minute(90.0, False) is False

    assert minute_feature(minute(20), INAV) == 0.0012000000000000454
    assert minute_feature(minute(22, age=90.0), INAV) is None
    assert minute_feature(minute(23, traded=False), INAV) is None

    # "excluded from ALL features": the denominator is the valid count, and the excluded
    # minutes' volume is not in vol_x or sv_etf either.
    good = [minute(20, volume=1000.0, signed=1000.0), minute(21, volume=1000.0, signed=1000.0)]
    with_junk = [
        good[0],
        minute(22, age=90.0, volume=1e9, signed=1e9),
        minute(23, traded=False, volume=1e9, signed=1e9),
        Minute(at(24), Quote(25.02, 25.04, 25.10, at(24)), INAV, 10.0, True, 1000.0, 1000.0),
    ]
    clean = features(good, w_start=W_START, trailing_volume_mean=4000.0)
    noisy = features(with_junk, w_start=W_START, trailing_volume_mean=4000.0)
    assert noisy.n_valid == clean.n_valid == 2
    assert noisy.prem_twa == clean.prem_twa
    assert noisy.prem_frac == clean.prem_frac
    assert noisy.vol_x == clean.vol_x == 0.5
    assert noisy.sv_etf == clean.sv_etf == 50000.0

    # A day with no valid minute has no premium; it does not have a premium of zero.
    with pytest.raises(PremiumError, match="0 of 2 minutes are valid"):
        features(
            [minute(20, age=90.0), minute(21, traded=False)],
            w_start=W_START,
        )


def test_ledger_17_no_premium_feature_uses_a_minute_at_or_after_w_start():
    """Required unit test 17, line 201 / decision D10. The guard raises; it does not filter."""
    before = [minute(20), minute(27, volume=100.0)]
    assert features(before, w_start=W_START).n_valid == 2

    at_w_start = Minute(W_START, Quote(25.02, 25.04, 25.10, W_START), INAV, 10.0, True)
    after = Minute(at(29), Quote(25.02, 25.04, 25.10, at(29)), INAV, 10.0, True)
    for offender in (at_w_start, after):
        with pytest.raises(PremiumWindowError, match="W_start"):
            features([minute(20), offender], w_start=W_START)

    # one second before is admissible, so the boundary is where line 201 puts it
    edge = Minute(at(27, 59), Quote(25.02, 25.04, 25.10, at(27, 59)), INAV, 10.0, True)
    assert features([edge], w_start=W_START).n_valid == 1

    # an invalid minute after W_start still raises: the guard is on the input, not on what
    # survives the valid-minute filter, because look-ahead is a property of what was read.
    with pytest.raises(PremiumWindowError):
        features(
            [minute(20), Minute(at(29), Quote(25.02, 25.04, 25.1, at(29)), INAV, 900.0, False)],
            w_start=W_START,
        )


# ------------------------------------------------------------------ the rest of the guards


def test_c_ap_is_the_documents_primary_and_its_two_sensitivities():
    """Line 213: primary 0.10%, sensitivity 0.05% and 0.20%, as fractions of basket value."""
    assert C_AP_PRIMARY == 0.001
    assert C_AP_SENSITIVITY == (0.0005, 0.002)
    # +12 bp, -4 bp and -36 bp: one outside each band, one inside every band, one outside all.
    minutes = [minute(20), minute(21, bid=24.98, ask=25.00), minute(24, bid=24.90, ask=24.92)]
    assert [minute_feature(m, INAV) for m in minutes] == [
        0.0012000000000000454,
        -0.00039999999999992044,
        -0.0035999999999999943,
    ]
    # at the primary and at the tight sensitivity the two tails cancel...
    assert features(minutes, w_start=W_START, c_ap=C_AP_PRIMARY).prem_frac == 0.0
    assert features(minutes, w_start=W_START, c_ap=C_AP_SENSITIVITY[0]).prem_frac == 0.0
    # ...and at the wide one the +12 bp minute falls inside the band and the sign appears.
    assert features(minutes, w_start=W_START, c_ap=C_AP_SENSITIVITY[1]).prem_frac == -1 / 3
    with pytest.raises(PremiumError, match="c_ap"):
        features(minutes, w_start=W_START, c_ap=0.0)


def test_vol_x_is_none_without_a_trailing_mean():
    """The 20-day mean is a measurement nobody has made; 1.0 would read as 'volume normal'."""
    f = features([minute(20)], w_start=W_START)
    assert f.vol_x is None
    with pytest.raises(PremiumError, match="trailing_volume_mean"):
        features([minute(20)], w_start=W_START, trailing_volume_mean=0.0)


def test_features_refuses_a_repeated_or_reordered_minute():
    """prem_twa weights minutes equally, so a duplicate would weight one of them twice."""
    with pytest.raises(PremiumError, match="strictly increasing"):
        features([minute(20), minute(20)], w_start=W_START)
    with pytest.raises(PremiumError, match="strictly increasing"):
        features([minute(21), minute(20)], w_start=W_START)
    with pytest.raises(PremiumError, match="no minutes"):
        features([], w_start=W_START)


def test_features_refuses_a_timezone_mismatch():
    """Comparing an aware minute with a naive W_start raises deep inside the loop otherwise."""
    aware = dt.datetime(2026, 9, 18, 14, 20, tzinfo=dt.timezone.utc)
    m = Minute(aware, Quote(25.02, 25.04, 25.10, aware), INAV, 10.0, True)
    with pytest.raises(PremiumError, match="timezone"):
        features([m], w_start=W_START)


def test_the_minute_refuses_a_signed_volume_larger_than_its_volume():
    with pytest.raises(PremiumError, match="exceeds volume"):
        minute(20, volume=100.0, signed=101.0)
    with pytest.raises(PremiumError, match="volume must be non-negative"):
        minute(20, volume=-1.0)
    with pytest.raises(PremiumError, match="inav must be positive"):
        Minute(at(20), Quote(25.02, 25.04, 25.1, at(20)), 0.0, 10.0, True)
    with pytest.raises(PremiumError, match="futures_traded must be a bool"):
        Minute(at(20), Quote(25.02, 25.04, 25.1, at(20)), INAV, 10.0, 1)  # type: ignore[arg-type]


def test_valid_minute_refuses_a_negative_quote_age():
    """A quote stamped after the minute it is read in is a join defect, not a stale quote."""
    with pytest.raises(PremiumError, match="non-negative"):
        valid_minute(-1.0, True)
    with pytest.raises(PremiumError, match="quote_age_s"):
        valid_minute(math.nan, True)


def _trailing(n: int = 60, day: dt.date = DAY) -> list[tuple[dt.date, float]]:
    return [(day - dt.timedelta(days=n - i), 0.001 if i < n // 2 else 0.003) for i in range(n)]


def test_stress_refuses_a_trailing_entry_that_is_not_prior():
    """R9's shape inside a feature: today's own premium in its own reference distribution."""
    trailing = _trailing()
    assert stress(0.004, trailing, day=DAY) == 1.9832633040858023
    contaminated = trailing[1:] + [(DAY, 0.02)]
    with pytest.raises(PremiumError, match="not before"):
        stress(0.004, contaminated, day=DAY)
    later = trailing[1:] + [(DAY + dt.timedelta(days=1), 0.02)]
    with pytest.raises(PremiumError, match="not before"):
        stress(0.004, later, day=DAY)
    duplicated = trailing[:-1] + [(trailing[-2][0], 0.005)]
    with pytest.raises(PremiumError, match="two entries"):
        stress(0.004, duplicated, day=DAY)


def test_stress_refuses_a_window_that_is_too_short_too_long_or_flat():
    assert STRESS_TRAILING_DAYS == 60
    with pytest.raises(PremiumError, match="below min_obs"):
        stress(0.004, _trailing(10), day=DAY)
    with pytest.raises(PremiumError, match="more than the 60-day"):
        stress(0.004, _trailing(62), day=DAY)
    flat = [(DAY - dt.timedelta(days=60 - i), 0.001) for i in range(60)]
    with pytest.raises(PremiumError, match="constant"):
        stress(0.004, flat, day=DAY)
    with pytest.raises(PremiumError, match="must be a date"):
        stress(0.004, _trailing(), day=dt.datetime(2026, 9, 18))  # type: ignore[arg-type]
