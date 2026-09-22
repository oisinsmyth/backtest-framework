"""Properties of the panel loader's cut (D609).

Three things that must hold for EVERY input, not for the ones I thought of:

  1. `convert_cut` is order-preserving — it is the whole reason a lexical comparison against a
     converted cut is a chronological comparison, and it is asserted rather than argued.
  2. the filter and the assert AGREE, on frames built to straddle the cut. Layer 1 and layer 2
     are deliberately not the same code path (`frozen.py`), so their agreement is a property
     worth quantifying over rather than a tautology.
  3. `panel_status` is total and exclusive: every path gets exactly one of three answers, and
     which one is decided by two independent facts (does it exist, is the basename listed).

`derandomize=True`, `max_examples=40`, `deadline=None` — the repository's settings, and D537
is the record of why they are pinned rather than left to the library's defaults.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from backtest_framework.data import panels as P
from backtest_framework.data.panels import PanelCutError, convert_cut, panel_status
from backtest_framework.validation.frozen import (
    ReservedSliceError,
    assert_none_at_or_after,
    filter_before,
)

SETTINGS = settings(derandomize=True, max_examples=40, deadline=None)

years = st.integers(min_value=1970, max_value=2099)
months = st.integers(min_value=1, max_value=12)
days = st.integers(min_value=1, max_value=28)


def iso(y: int, m: int, d: int) -> str:
    return f"{y:04d}-{m:02d}-{d:02d}"


month_starts = st.builds(lambda y, m: iso(y, m, 1), years, months)
year_starts = st.builds(lambda y: iso(y, 1, 1), years)
any_days = st.builds(iso, years, months, days)


# ------------------------------------------------------------------ 1. order preserving


@SETTINGS
@given(month_starts, month_starts)
def test_convert_cut_preserves_order_for_both_monthly_formats(a: str, b: str):
    for fmt in ("yyyymm", "yyyy_mm"):
        assert (convert_cut(fmt, a) < convert_cut(fmt, b)) == (a < b)
        assert (convert_cut(fmt, a) == convert_cut(fmt, b)) == (a == b)


@SETTINGS
@given(year_starts, year_starts)
def test_convert_cut_preserves_order_for_year_prefix(a: str, b: str):
    assert (convert_cut("year_prefix", a) < convert_cut("year_prefix", b)) == (a < b)


@SETTINGS
@given(any_days)
def test_a_day_format_takes_the_cut_unchanged_and_a_period_format_refuses_a_mid_period_cut(d: str):
    for fmt in ("iso_day", "iso_ts", "date32"):
        assert convert_cut(fmt, d) == d
    if d.endswith("-01"):
        assert len(convert_cut("yyyymm", d)) == 6
    else:
        with pytest.raises(PanelCutError):
            convert_cut("yyyymm", d)
    if d[5:] == "01-01":
        assert convert_cut("year_prefix", d) == d[:4]
    else:
        with pytest.raises(PanelCutError):
            convert_cut("year_prefix", d)


# ------------------------------------------------------------------ 2. filter and assert agree


@SETTINGS
@given(st.lists(any_days, min_size=0, max_size=30), any_days)
def test_the_filter_keeps_exactly_what_the_assert_tolerates_on_a_day_panel(rows, cut):
    frame = pd.DataFrame({"day": rows, "v": list(range(len(rows)))})
    kept = filter_before(frame, "day", cut)
    assert_none_at_or_after(kept, "day", cut)  # must not raise, ever
    assert list(kept["day"]) == [r for r in rows if r < cut]
    if any(r >= cut for r in rows):
        with pytest.raises(ReservedSliceError):
            assert_none_at_or_after(frame, "day", cut)
    else:
        assert_none_at_or_after(frame, "day", cut)


@SETTINGS
@given(st.lists(st.tuples(years, months), min_size=0, max_size=30), month_starts)
def test_the_same_holds_on_a_period_panel_in_the_panels_own_units(pairs, cut_iso):
    rows = [f"{y:04d}{m:02d}" for y, m in pairs]
    cut = convert_cut("yyyymm", cut_iso)
    frame = pd.DataFrame({"period": rows, "v": list(range(len(rows)))})
    kept = P._period_filter(frame, "period", cut, "yyyymm")
    P._period_assert(kept, "period", cut, "yyyymm")
    assert list(kept["period"]) == [r for r in rows if r < cut]
    # and the lexical comparison agrees with the arithmetic one, which is the claim
    assert [r < cut for r in rows] == [
        (y, m) < (int(cut[:4]), int(cut[4:])) for y, m in pairs
    ]


@SETTINGS
@given(st.lists(st.tuples(years, months, st.integers(1, 4), st.booleans()),
                min_size=1, max_size=20), year_starts)
def test_a_stacked_monthly_and_quarterly_column_cuts_on_the_year_they_share(pairs, cut_iso):
    """`hkm_factors`'s shape: `197001` beside `19701`. The key is the leading four digits, so
    the answer cannot depend on which frequency a row happens to be."""
    rows = [f"{y:04d}{m:02d}" if monthly else f"{y:04d}{q}" for y, m, q, monthly in pairs]
    cut = convert_cut("year_prefix", cut_iso)
    frame = pd.DataFrame({"period": rows, "v": list(range(len(rows)))})
    kept = P._period_filter(frame, "period", cut, "year_prefix")
    P._period_assert(kept, "period", cut, "year_prefix")
    assert list(kept["period"]) == [r for r in rows if r[:4] < cut]
    assert list(kept["period"]) == [
        r for r, (y, _m, _q, _f) in zip(rows, pairs) if y < int(cut)
    ]


# ------------------------------------------------------------------ 3. status is total


@SETTINGS
@given(st.sampled_from(sorted(P.panel_names())[:40]), st.booleans())
def test_panel_status_is_total_and_decided_by_two_independent_facts(name: str, listed: bool):
    """A tmp-free property: the answer for a path that does not exist is `absent_listed` iff
    its BASENAME is in the manifest, whatever the directory. That is what makes the rule a
    statement about the repository's data and not about a path spelling."""
    base = Path("Z:/no/such/directory/d609")
    listed_path = base / name
    unlisted_path = base / (name + ".not-a-panel" if listed else "totally_made_up.csv.gz")
    assert panel_status(listed_path) == "absent_listed"
    assert panel_status(unlisted_path) == "absent_unlisted"
    for p in (listed_path, unlisted_path):
        assert panel_status(p) in ("present", "absent_listed", "absent_unlisted")
