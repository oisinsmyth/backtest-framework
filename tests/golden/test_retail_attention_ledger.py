"""Golden tests for `data/retail_attention.py` (D621).

Hand arithmetic in `test_retail_attention_ledger.hand.txt`, per CONTRIBUTING step 2: every
number below was produced by two calculators that never import this codebase — GNU `awk` with
`%.17g` and GNU `sha256sum` fed by `printf` in Git Bash, and .NET's `[Math]::Sqrt` and double
division printed with the round-trip `"R"` format from PowerShell — and they agreed on every
line. The anchor case asserts the published SHA-256 of the empty string, so a suite where
`hashlib` had been swapped for something else fails on the first assertion rather than on a
subtle one.

WHY THIS TIER. D621's whole claim rests on TWO ASSOCIATION STATISTICS between a creation series
and a holder series, and a correlation is the kind of number that cannot be checked by eye and
is changed by one convention: which rank a tie takes, which denominator the sd uses, whether the
percentile interpolates. Case 1 pins both correlations on ten rows chosen so that they DISAGREE
— 0.9394 against 0.4777 — because a case where they agree cannot tell the two functions apart.
Case 2 pins the percentile rule that defines a "creation day". Case 3 pins the daily z AND its
bit-identity with D612's hourly `zscore_matched`, which is what stops this module's arithmetic
drifting from the attention layer's. Case 4 pins `creation_accel` at exactly 0.0 on a constant,
an exactness claim about summation order that is the reason it delegates to `att_accel` rather
than re-adding six numbers.

Every input here is a literal written into the test. No fixture is read, no market bar is
touched, no return is computed, and every date lies in 2019.
"""

from __future__ import annotations

import datetime as dt
import hashlib
from pathlib import Path

import pytest

from backtest_framework.data.attention import InsufficientHistory, zscore_matched
from backtest_framework.data.retail_attention import (
    creation_accel,
    creation_z,
    pearson,
    quantile_linear,
    spearman,
)

HAND = Path(__file__).with_suffix(".hand.txt")

# --- the hand ledger's constants, transcribed from test_retail_attention_ledger.hand.txt -------
SHA_EMPTY = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

# Case 1: ten rows, y a permutation of 1..10 with one value replaced by 100.
X_HAND = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
Y_HAND = [2.0, 1.0, 4.0, 3.0, 6.0, 5.0, 8.0, 7.0, 100.0, 9.0]
PEARSON_HAND = 0.47771588185465091      # 392.5 / sqrt(82.5 * 8182.5)
SPEARMAN_HAND = 0.93939393939393945     # 77.5 / 82.5 = 31/33

# Case 2: the 90th percentile of 1..10 by linear interpolation, 1 + 0.9*(10-1).
P90_HAND = 9.1

# Case 3: five observations 10, 12, 14, 16, 18 scoring a 20.
SD_HAND = 3.1622776601683795            # sqrt(10), ddof = 1
Z_HAND = 1.8973665961010275             # 6 / sqrt(10)
MONDAYS = [(dt.date(2019, 9, 30) + dt.timedelta(days=7 * k), 10.0 + 2 * k) for k in range(5)]
SCORED_DAY = dt.date(2019, 11, 4)       # a Monday
BUSINESS = [
    (dt.date(2019, 10, 28), 10.0),
    (dt.date(2019, 10, 29), 12.0),
    (dt.date(2019, 10, 30), 14.0),
    (dt.date(2019, 10, 31), 16.0),
    (dt.date(2019, 11, 1), 18.0),
]

# Case 4: six daily levels.
RAMP = [0.5, 0.5, 0.5, 1.5, 2.5, 3.5]
ACCEL_HAND = 2.0


def test_the_hand_ledger_is_present_and_names_its_two_calculators():
    """A golden whose companion has been deleted is a golden with no ground truth."""
    assert HAND.is_file(), f"{HAND.name} is missing; the numbers below have no provenance"
    text = HAND.read_text(encoding="utf-8")
    assert "awk" in text and "sha256sum" in text
    assert "[Math]::Sqrt" in text
    assert SHA_EMPTY in text
    for token in (str(PEARSON_HAND), str(SPEARMAN_HAND), str(Z_HAND), str(SD_HAND)):
        assert token in text, f"{token} is asserted here and not written in the hand file"


def test_the_anchor_is_standard_sha256():
    """Before any digest in this suite is trusted, the hash function is checked against a
    published value: SHA-256 of the empty string."""
    assert hashlib.sha256(b"").hexdigest() == SHA_EMPTY


# ---------------------------------------------------------------- Case 1, the two correlations
def test_case_1_pearson_on_the_hand_rows():
    assert pearson(X_HAND, Y_HAND) == PEARSON_HAND


def test_case_1_spearman_on_the_hand_rows():
    assert spearman(X_HAND, Y_HAND) == SPEARMAN_HAND


def test_case_1_spearman_equals_thirty_one_over_thirty_three():
    """The same double from a different expression, as the hand file cross-checks it."""
    assert spearman(X_HAND, Y_HAND) == 31.0 / 33.0


def test_case_1_the_two_statistics_disagree_and_that_is_the_point():
    """A rank statistic reads a near-monotone relation; a product-moment statistic reads the one
    outlier. Reporting either alone on a fat-tailed holder series is reporting half the fact."""
    assert spearman(X_HAND, Y_HAND) - pearson(X_HAND, Y_HAND) > 0.45


def test_case_1_the_outlier_is_what_moves_the_pearson():
    """Replace the 100 with the 10 it would have been and the two statistics converge — which is
    the evidence that the gap above is the outlier and not the ordering."""
    tame = [*Y_HAND[:8], 10.0, Y_HAND[9]]
    assert pearson(X_HAND, tame) == pytest.approx(spearman(X_HAND, tame), abs=1e-12)


# ------------------------------------------------------------------- Case 2, the creation day
def test_case_2_the_ninetieth_percentile_is_linear_interpolation():
    assert quantile_linear([abs(v) for v in X_HAND], 0.90) == P90_HAND
    assert quantile_linear(X_HAND, 0.90) == 1.0 + 0.9 * (10.0 - 1.0)


def test_case_2_the_comparison_is_strict_and_selects_one_row():
    picked = [(x, y) for x, y in zip(X_HAND, Y_HAND, strict=True) if abs(x) > P90_HAND]
    assert picked == [(10.0, 9.0)]
    assert sum(1 for _x, y in picked if y > 0) / len(picked) == 1.0


def test_case_2_the_endpoints_are_the_order_statistics():
    """p = 0 and p = 1 must return the min and the max exactly, or the interpolation is wrong at
    the ends and every quantile between them is suspect."""
    assert quantile_linear(X_HAND, 0.0) == 1.0
    assert quantile_linear(X_HAND, 1.0) == 10.0


# ------------------------------------------------------------ Case 3, the daily z and D612's z
def test_case_3_the_daily_z_on_five_mondays():
    assert creation_z([*MONDAYS, (SCORED_DAY, 20.0)], SCORED_DAY) == Z_HAND


def test_case_3_all_three_paths_return_the_same_double():
    """THE POINT OF THE CASE. `all_days`, `same_weekday` and D612's own `zscore_matched` agree
    exactly on an input where the two windows select the same five numbers, so this module's
    copy of the arithmetic is a copy that is checked against its original."""
    obs = [*MONDAYS, (SCORED_DAY, 20.0)]
    z_all = creation_z(obs, SCORED_DAY, match="all_days")
    z_weekday = creation_z(obs, SCORED_DAY, match="same_weekday")
    z_d612 = zscore_matched([(d, 0, v) for d, v in obs], SCORED_DAY, 0)
    assert z_all == z_weekday == z_d612 == Z_HAND


def test_case_3_the_contrast_on_five_business_days():
    """`all_days` scores it; `same_weekday` has one matched observation and refuses."""
    obs = [*BUSINESS, (SCORED_DAY, 20.0)]
    assert creation_z(obs, SCORED_DAY, match="all_days") == Z_HAND
    with pytest.raises(InsufficientHistory):
        creation_z(obs, SCORED_DAY, match="same_weekday")


def test_case_3_the_denominator_is_the_sample_sd():
    """ddof = 1. With ddof = 0 the sd would be sqrt(8) and the z would be 2.121..., so the two
    choices are far apart and the hand file's sqrt(10) identifies which one is in the code."""
    obs = [*MONDAYS, (SCORED_DAY, 20.0)]
    assert creation_z(obs, SCORED_DAY) == 6.0 / SD_HAND
    # sqrt(10) squared is 10.000000000000002, one ulp above 10: the round trip through a square
    # root is not exact and this line is a sanity check on WHICH variance, not on exactness.
    assert SD_HAND * SD_HAND == pytest.approx(10.0, abs=1e-14)
    assert SD_HAND != 8.0**0.5, "sqrt(8) would be the population sd; the code uses ddof = 1"


# ------------------------------------------------------------------- Case 4, creation_accel
def test_case_4_accel_on_the_ramp():
    levels = list(zip([d for d, _v in BUSINESS] + [SCORED_DAY], RAMP, strict=True))
    assert creation_accel(levels, SCORED_DAY) == ACCEL_HAND


def test_case_4_accel_on_a_constant_is_exactly_zero():
    """`== 0.0`, with no tolerance. Both means are `math.fsum` over the same three doubles in the
    same order divided by the same integer, so a rewrite that reorders the sum breaks this."""
    days = [d for d, _v in BUSINESS] + [SCORED_DAY]
    for level in (3.5, 0.1, -7.3, 1e9, 1.0 / 3.0):
        levels = [(d, level) for d in days]
        assert creation_accel(levels, SCORED_DAY) == 0.0, level


def test_case_4_a_hole_raises_rather_than_carrying_forward():
    days = [d for d, _v in BUSINESS] + [SCORED_DAY]
    holed = [(d, v) for d, v in zip(days, RAMP, strict=True) if d != dt.date(2019, 10, 30)]
    with pytest.raises(InsufficientHistory):
        creation_accel(holed, SCORED_DAY)
