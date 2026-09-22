"""Unit tests for `data/attention.py` — the attention layer, D612.

CLAIMED HERE: ledger unit tests 21, 22, 23, 24 and 25, the five the settlement-flow deposit's
§12 names for P3.7 and all five of which stood at `missing` in `data/deposit_test_map.json`
before this file existed. Each is claimed by putting its number in the test function's name, the
convention `docs/results/DEPOSIT_TEST_MAP.md` scans for.

THE FOUR POINT-IN-TIME TESTS ARE THE POINT OF THIS FILE, and they are not interchangeable with
each other. They guard four different ways the same look-ahead gets in:

  21  the z-score's REFERENCE window reaches into the present;
  22  an hourly datum is read before its publisher has published it;
  23  a news item is keyed on when it HAPPENED rather than on when it was reported;
  24  a feature that is meant to measure change measures level instead.

R9 is this repository's price list for the class: an apparent effect spanning 465 percentage
points, monotone across five quintiles, produced entirely by a conditioner that was not lagged —
in a script upstream of every null and hurdle the programme had. Each guard below is therefore
asserted to RAISE on a deliberate break rather than to filter, because a filtered leak and a
window that never had one are indistinguishable from the outside.

No market fixture is read. No return of any kind is computed. Every date here is inside a
synthetic 2019 window, five years before the 2024-01-01 holdout.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pytest

from backtest_framework.data import attention as mod
from backtest_framework.data.attention import (
    BREADTH_Z,
    BURST_Z,
    MIN_MATCHED_OBS,
    AttentionError,
    GdeltItem,
    InsufficientHistory,
    LookaheadRefused,
    QueriesMalformed,
    QueriesTampered,
    ResolutionRefused,
    TrialRow,
    att_accel,
    att_breadth,
    att_level,
    available,
    gdelt_available_at,
    headline_burst,
    iter_gkg_rows,
    load_queries,
    matched_queries,
    parse_dump_line,
    parse_gkg_row,
    parse_trial_line,
    queries_hash,
    refuse_coarse_resolution,
    slot_datetime,
    trial_header,
    trial_line,
    wiki_available_at,
    wiki_is_available,
    zscore_matched,
)

REPO = Path(__file__).resolve().parents[2]
QUERIES = REPO / "data" / "attention" / "QUERIES.md"
UTC = dt.timezone.utc


def at(y: int, m: int, d: int, hh: int = 0, mm: int = 0, ss: int = 0) -> dt.datetime:
    return dt.datetime(y, m, d, hh, mm, ss, tzinfo=UTC)


# --------------------------------------------------------------------------- the query file (25)
def test_ledger_25_query_lists_load_from_queries_md_and_hash():
    """*"Query lists are loaded from `QUERIES.md` and hashed."* — the deposit's §12 item 25,
    first clause, and deposit line 116's "fixed ... before any feature is computed"."""
    qs = load_queries(QUERIES)
    assert qs.sha256 == queries_hash(QUERIES)
    assert re.fullmatch(r"[0-9a-f]{64}", qs.sha256)
    # The eight that resolved, in file order, and the six that did not or were excluded.
    assert qs.articles == (
        "Natural_gas", "Henry_Hub", "Natural_gas_prices", "Price_of_oil",
        "West_Texas_Intermediate", "Petroleum", "United_States_Oil_Fund", "ProShares",
    )
    assert qs.unresolved == (
        "United_States_Natural_Gas_Fund", "BOIL", "ProShares_Ultra_Bloomberg_Natural_Gas")
    # The trap: KOLD, UCO and SCO all answer HTTP 200 and none of them is a fund page.
    assert qs.excluded == ("KOLD", "UCO", "SCO")
    assert not set(qs.articles) & set(qs.excluded)
    assert qs.projects == ("en", "en.m")
    assert qs.social_disabled == ("social_reddit", "social_stocktwits")
    assert {q.qid for q in qs.queries} >= {"natural_gas", "crude_oil", "theme_env_oil"}
    assert {q.precision for q in qs.queries} == {"high", "low"}


def test_ledger_25_the_hash_is_stored_with_every_trial_in_trials_csv():
    """*"The hash is stored with every trial in `trials.csv`."* — item 25's second clause.

    D612 writes no trial. What is asserted is the SHAPE: `queries_sha256` has no default, so a
    row built without it does not construct, and a placeholder does not pass the hex guard.
    """
    qs = load_queries(QUERIES)
    assert "queries_sha256" in mod.TRIAL_FIELDS
    assert "frozen_sha256" in mod.TRIAL_FIELDS  # spelled as D605's track3.TradeRow spells it
    row = TrialRow(
        trial_id="T1", timestamp="2026-09-22T00:00:00Z", instrument="NG", model="C3",
        stage="stage1", frozen_sha256="a" * 64, queries_sha256=qs.sha256, n_trades="0",
        notes="shape only; no trial was run",
    )
    line = trial_line(row)
    back = parse_trial_line(trial_header(), line)
    assert back == row
    assert back.queries_sha256 == qs.sha256
    assert trial_header().split(",") == list(mod.TRIAL_FIELDS)

    with pytest.raises(TypeError):
        TrialRow(trial_id="T2", timestamp="t", instrument="NG", model="C3",  # type: ignore[call-arg]
                 stage="s", frozen_sha256="a" * 64)
    with pytest.raises(AttentionError, match="64 lowercase hex"):
        TrialRow(trial_id="T3", timestamp="t", instrument="NG", model="C3", stage="s",
                 frozen_sha256="a" * 64, queries_sha256="not-a-hash")


def test_a_tampered_queries_file_raises(tmp_path: Path):
    """Deposit line 116: *"not changed afterwards without a doc edit"*. The enforcement is the
    companion digest, and an edit that does not rewrite it is caught."""
    good = tmp_path / "QUERIES.md"
    good.write_bytes(QUERIES.read_bytes())
    (tmp_path / "QUERIES.sha256").write_text(queries_hash(good) + "  QUERIES.md\n",
                                             encoding="utf-8", newline="\n")
    load_queries(good)  # the good case FIRST, so the failure below is not a broken fixture

    with open(good, "ab") as fh:
        fh.write(b"\n<!-- one more byte -->\n")
    with pytest.raises(QueriesTampered, match="hashes to"):
        load_queries(good)


def test_a_queries_file_with_no_digest_raises(tmp_path: Path):
    bare = tmp_path / "QUERIES.md"
    bare.write_bytes(QUERIES.read_bytes())
    with pytest.raises(QueriesTampered, match="no committed digest"):
        load_queries(bare)


def test_the_newline_policy_is_the_files_content_not_the_checkouts(tmp_path: Path):
    """D550/D551: the same content with two newline conventions is ONE identity."""
    lf = tmp_path / "a.md"
    crlf = tmp_path / "b.md"
    lf.write_bytes(b"# Q\n- Natural_gas\n")
    crlf.write_bytes(b"# Q\r\n- Natural_gas\r\n")
    assert queries_hash(lf) == queries_hash(crlf)


@pytest.mark.parametrize(
    "break_it, match",
    [
        (lambda t: t.replace("### 1a. IN THE LIST", "### 1z. IN THE LIST"), "no heading"),
        (lambda t: t.replace("| `en.m` | yes |", "| `en.m` | perhaps |"), "want exactly yes or no"),
        (lambda t: t.replace("| `tk_boil` | ticker |", "| `tk_boil` | rumour |"), "kind"),
        (lambda t: t.replace("in **title or url** | high |", "in **title** | high |"), "url"),
        (lambda t: t.replace("| 8 | `ProShares` |", "| 8 | `Natural_gas` |"), "duplicate"),
        (lambda t: t.replace("| 1 | `Natural_gas` |", "| 1 | `KOLD` |"), "both as in the article"),
    ],
)
def test_every_queries_guard_fires(tmp_path: Path, break_it, match):
    """A guard that has never been seen to fire is a guard nobody has tested. Each break below
    hits exactly the thing the guard READS, not something near it."""
    text = QUERIES.read_text(encoding="utf-8")
    broken = break_it(text)
    assert broken != text, "the break did not change the file; the guard would be untested"
    p = tmp_path / "QUERIES.md"
    p.write_text(broken, encoding="utf-8", newline="\n")
    (tmp_path / "QUERIES.sha256").write_text(queries_hash(p) + "\n", encoding="utf-8",
                                             newline="\n")
    with pytest.raises(QueriesMalformed, match=match):
        load_queries(p)


# ------------------------------------------------------------------- the publication guard (22)
def test_ledger_22_an_hourly_pageview_is_unavailable_at_1410_and_available_at_1415():
    """*"Publication-time guard: an hourly pageview for 13:00-14:00 is unavailable at tau = 14:10
    and available at tau = 14:15 or later."* — the deposit's §12 item 22, and its line 267,
    *"Hourly pageviews enter only after the hour completes plus a 15-min publication buffer."*
    """
    hour = at(2019, 11, 4, 13)
    assert wiki_available_at(hour) == at(2019, 11, 4, 14, 15)

    assert wiki_is_available(hour, at(2019, 11, 4, 14, 10)) is False   # test 22, first half
    assert wiki_is_available(hour, at(2019, 11, 4, 14, 15)) is True    # test 22, second half
    # ONE SECOND SHORT. Without this an implementation that rounds to five minutes passes.
    assert wiki_is_available(hour, at(2019, 11, 4, 14, 14, 59)) is False
    assert wiki_is_available(hour, at(2019, 11, 4, 14, 15, 1)) is True
    # and the hour itself is never available inside itself
    assert wiki_is_available(hour, at(2019, 11, 4, 13, 59, 59)) is False


def test_the_publication_buffer_has_no_branch_in_it():
    """`wiki_available_at` is unconditional across a day, a DST change and a year boundary: the
    same 75 minutes every time. A rule with a branch can take the wrong branch."""
    for hour in (at(2019, 11, 3, 1), at(2019, 3, 10, 6), at(2019, 12, 31, 23), at(2020, 2, 29, 0)):
        assert wiki_available_at(hour) - hour == dt.timedelta(minutes=75)


def test_a_naive_instant_raises_rather_than_being_assumed_utc():
    with pytest.raises(AttentionError, match="naive"):
        wiki_available_at(dt.datetime(2019, 11, 4, 13))


# ----------------------------------------------------------------- the publication key (23)
def test_ledger_23_gdelt_items_are_keyed_on_publication_not_event_time():
    """*"GDELT items are keyed on publication timestamp; items published after tau are excluded
    even if their event time is earlier."* — the deposit's §12 item 23, and its line 267,
    *"GDELT enters with its publication timestamp, not the event time."*
    """
    tau = at(2019, 11, 4, 12, 0)
    # Published BEFORE tau, event a year earlier: INCLUDED.
    old_event = GdeltItem(publication_ts=at(2019, 11, 4, 11, 45),
                          event_ts=at(2018, 11, 4), tone=-1.0, source_url="a",
                          matched_queries=("natural_gas",))
    # Published AFTER tau, event BEFORE tau: EXCLUDED. This is the whole test.
    late_report = GdeltItem(publication_ts=at(2019, 11, 4, 12, 15),
                            event_ts=at(2019, 11, 4, 9, 0), tone=2.0, source_url="b",
                            matched_queries=("natural_gas",))
    # Published exactly AT tau: included; the slot stamp ends the 15 minutes it covers.
    at_tau = GdeltItem(publication_ts=tau, event_ts=at(2030, 1, 1), tone=0.0, source_url="c",
                       matched_queries=("crude_oil",))

    got = available([old_event, late_report, at_tau], tau)
    assert got == (old_event, at_tau)
    assert late_report not in got
    # and the event time is not read: flipping it changes nothing.
    flipped = GdeltItem(publication_ts=late_report.publication_ts, event_ts=at(1999, 1, 1),
                        tone=late_report.tone, source_url="b", matched_queries=("natural_gas",))
    assert flipped not in available([old_event, flipped, at_tau], tau)


def test_a_gkg_row_takes_its_publication_timestamp_from_the_slot():
    qs = load_queries(QUERIES)
    row = _gkg(title="Henry Hub cash prices fall", url="https://x.com/a-natural-gas-story",
               themes="ENV_OIL;TAX_FNCACT", tone="1.5,2.0,0.5,2.5,10.0,0.5,100")
    item = parse_gkg_row(row, qs.queries)
    assert item is not None
    assert item.publication_ts == slot_datetime("20191104001500")
    assert item.event_ts is None  # the GKG file carries no event date and none is invented
    assert item.tone == 1.5
    assert set(item.matched_queries) == {"natural_gas", "henry_hub", "theme_env_oil"}


def test_a_gdelt_slot_is_available_one_full_slot_after_its_stamp():
    """A DECLARED conservative stand-in for an unmeasured posting lag, and it is never optimistic."""
    slot = at(2019, 11, 4, 0, 15)
    assert gdelt_available_at(slot) == at(2019, 11, 4, 0, 30)
    assert gdelt_available_at(slot) > slot


def test_an_absent_tone_is_none_and_never_zero():
    """A zero tone is neutral coverage; an absent tone is no measurement. Collapsing the second
    into the first biases every mean that reads it toward neutral."""
    qs = load_queries(QUERIES)
    blank = parse_gkg_row(_gkg(title="natural gas today", tone=""), qs.queries)
    assert blank is not None and blank.tone is None
    zero = parse_gkg_row(_gkg(title="natural gas today", tone="0.0,1,1,2,3,0,10"), qs.queries)
    assert zero is not None and zero.tone == 0.0


def test_a_document_matches_a_query_at_most_once():
    """`news_n` is a DOCUMENT count (deposit line 251), never a mention count."""
    qs = load_queries(QUERIES)
    row = _gkg(title="natural gas natural gas natural gas",
               url="https://x.com/natural-gas/natural-gas")
    item = parse_gkg_row(row, qs.queries)
    assert item is not None
    assert item.matched_queries.count("natural_gas") == 1


def test_a_ticker_matches_on_the_title_only():
    """`QUERIES.md` §2b: the bare tickers are ordinary words and a URL path segment `/uso/`
    appears on sites that have nothing to do with the fund."""
    qs = load_queries(QUERIES)
    title_hit = matched_queries(" uso ", " nothing ", frozenset(), qs.queries)
    url_only = matched_queries(" nothing ", " https example com uso index html ",
                               frozenset(), qs.queries)
    assert "tk_uso" in title_hit
    assert "tk_uso" not in url_only


def test_a_gkg_record_is_not_a_line():
    """V2EXTRASXML carries a source page's `<PAGE_LINKS>` verbatim, and those can hold a raw
    newline — found on the real 2019-11-04 12:15 slot. Splitting on `\\n` yields fragments."""
    one = _gkg(title="natural gas", extras_tail=b"<PAGE_LINKS>a\nb\nc</PAGE_LINKS>")
    two = one.replace(b"20191104001500-1", b"20191104001500-2")
    rows = iter_gkg_rows(one + b"\n" + two)
    assert len(rows) == 2
    assert rows[0] == one and rows[1] == two
    assert len((one + b"\n" + two).split(b"\n")) == 6  # six physical lines, two records
    with pytest.raises(AttentionError, match="GKGRECORDID"):
        iter_gkg_rows(b"&HomeUrl=http://example.invalid/x\tstray\n")


def test_a_short_gkg_row_raises_rather_than_being_padded():
    qs = load_queries(QUERIES)
    with pytest.raises(AttentionError, match="27 tab fields"):
        parse_gkg_row(b"20191104001500-1\t20191104001500\tonly three", qs.queries)


# ------------------------------------------------------------------------- the z-score (21)
MONDAYS = [(dt.date(2019, 9, 30) + dt.timedelta(days=7 * k), 14, 10.0 + 2 * k) for k in range(5)]
SCORED = [(dt.date(2019, 11, 4), 14, 20.0)]
Z_HAND = 1.8973665961010275  # tests/golden/test_attention_ledger.hand.txt, Case 2


def test_ledger_21_zscores_use_only_the_prior_sixty_matched_days():
    """*"Attention z-scores on day t use only data from days t-60 ... t-1 for the same
    hour-of-day and day-of-week."* — the deposit's §12 item 21, and its line 255.

    THE GOOD CASE FIRST, so that the refusals below are not a broken fixture.
    """
    z = zscore_matched(MONDAYS + SCORED, dt.date(2019, 11, 4), 14)
    assert z == pytest.approx(Z_HAND, abs=1e-15)

    # A SAME-DAY observation is REFUSED, not filtered. R9: a filtered leak and a window that
    # never had one are indistinguishable from the outside.
    with pytest.raises(LookaheadRefused, match="at or after the scored day"):
        zscore_matched(MONDAYS + SCORED + [(dt.date(2019, 11, 4), 15, 99.0)],
                       dt.date(2019, 11, 4), 14)
    # A FUTURE observation likewise.
    with pytest.raises(LookaheadRefused):
        zscore_matched(MONDAYS + SCORED + [(dt.date(2019, 11, 11), 14, 99.0)],
                       dt.date(2019, 11, 4), 14)

    # The WRONG WEEKDAY at the right hour does not enter the reference set: adding six of them,
    # all enormous, leaves the score untouched.
    tuesdays = [(dt.date(2019, 10, 1) + dt.timedelta(days=7 * k), 14, 1e6) for k in range(5)]
    assert zscore_matched(MONDAYS + tuesdays + SCORED, dt.date(2019, 11, 4), 14) == pytest.approx(
        Z_HAND, abs=1e-15)
    # The WRONG HOUR on the right weekday likewise.
    other_hour = [(d, 15, 1e6) for d, _h, _v in MONDAYS]
    assert zscore_matched(MONDAYS + other_hour + SCORED, dt.date(2019, 11, 4), 14) == pytest.approx(
        Z_HAND, abs=1e-15)


def test_an_observation_older_than_the_window_is_dropped_not_refused():
    """Old is not a leak. It is dropped, and the score is the same."""
    ancient = [(dt.date(2019, 8, 26), 14, 1e6)]  # t-70, a Monday at hour 14
    assert zscore_matched(MONDAYS + ancient + SCORED, dt.date(2019, 11, 4), 14) == pytest.approx(
        Z_HAND, abs=1e-15)


def test_too_few_matched_observations_raises():
    assert MIN_MATCHED_OBS == 5
    with pytest.raises(InsufficientHistory, match="below the stated minimum"):
        zscore_matched(MONDAYS[:4] + SCORED, dt.date(2019, 11, 4), 14)


def test_a_constant_reference_window_raises_rather_than_dividing_by_zero():
    flat = [(d, 14, 7.0) for d, _h, _v in MONDAYS]
    with pytest.raises(InsufficientHistory, match="no denominator"):
        zscore_matched(flat + SCORED, dt.date(2019, 11, 4), 14)


def test_a_missing_scored_observation_raises():
    with pytest.raises(AttentionError, match="nothing to score"):
        zscore_matched(MONDAYS, dt.date(2019, 11, 4), 14)


# --------------------------------------------------------------------------- att_accel (24)
def test_ledger_24_att_accel_is_positive_on_a_ramp_and_zero_once_flat():
    """*"`att_accel` on a synthetic step increase in attention is positive during the ramp and
    returns to about zero once the level is flat."* — the deposit's §12 item 24, and its line
    262, *"Change in `att_level` over the last 3 hours vs the prior 3 hours"*."""
    base = at(2019, 11, 4, 9)
    ramp = {base + dt.timedelta(hours=k): v
            for k, v in enumerate([0.5, 0.5, 0.5, 1.5, 2.5, 3.5])}
    assert att_accel(ramp, base + dt.timedelta(hours=5)) == pytest.approx(2.0, abs=1e-15)

    # "about zero once the level is flat" — and on a constant series it is EXACTLY zero, because
    # the two means are the same doubles summed in the same order. A tolerance here would hide a
    # reordered sum.
    flat = {base + dt.timedelta(hours=k): 3.5 for k in range(6)}
    assert att_accel(flat, base + dt.timedelta(hours=5)) == 0.0

    # and it is a CHANGE, not a level: a high flat level still gives zero.
    high = {base + dt.timedelta(hours=k): 40.0 for k in range(6)}
    assert att_accel(high, base + dt.timedelta(hours=5)) == 0.0
    # a DOWN ramp is negative, which is the half of "positive during the ramp" that the deposit
    # does not say and a sign error would pass without.
    down = {base + dt.timedelta(hours=k): v
            for k, v in enumerate([3.5, 2.5, 1.5, 0.5, 0.5, 0.5])}
    assert att_accel(down, base + dt.timedelta(hours=5)) == pytest.approx(-2.0, abs=1e-15)


def test_att_accel_refuses_a_hole_rather_than_interpolating():
    base = at(2019, 11, 4, 9)
    full = {base + dt.timedelta(hours=k): float(k) for k in range(6)}
    att_accel(full, base + dt.timedelta(hours=5))  # the good case
    holed = {k: v for k, v in full.items() if k != base + dt.timedelta(hours=2)}
    with pytest.raises(InsufficientHistory, match="not interpolated"):
        att_accel(holed, base + dt.timedelta(hours=5))


# ------------------------------------------------------------------- the remaining features
def test_att_level_is_the_mean_of_the_z_scores_that_exist():
    assert att_level({"news": 1.0, "wiki": 3.0}) == 2.0
    # An absent source contributes NOTHING, not a zero: a zero z is exactly-average attention.
    assert att_level({"news": 4.0}) == 4.0
    with pytest.raises(InsufficientHistory):
        att_level({})


def test_att_breadth_counts_strictly_above_two():
    assert BREADTH_Z == 2.0
    assert att_breadth({"news": 2.0, "wiki": 2.0}) == 0
    assert att_breadth({"news": 2.0000001, "wiki": 2.0}) == 1
    assert att_breadth({"news": 9.0, "wiki": 3.0}) == 2
    # The reachable maximum is the number of LIVE sources, and social is disabled under Q12.
    assert att_breadth({"news": 9.0, "wiki": 9.0}) == 2


def test_headline_burst_is_strictly_above_three_and_only_after_0930_new_york():
    assert BURST_Z == 3.0
    day = dt.date(2019, 11, 4)          # EST: 09:30 ET is 14:30 UTC
    pre = at(2019, 11, 4, 13, 0)
    post = at(2019, 11, 4, 15, 0)
    assert headline_burst({pre: 99.0}, day) == 0          # before the open, however loud
    assert headline_burst({post: 3.0}, day) == 0          # strictly greater
    assert headline_burst({post: 3.0000001}, day) == 1
    # DST: on 2019-07-01 09:30 ET is 13:30 UTC, so the same 13:00 UTC block is still pre-open,
    # and 14:00 UTC is post-open — a hard-coded offset gets one of these two wrong.
    summer = dt.date(2019, 7, 1)
    assert headline_burst({at(2019, 7, 1, 13, 0): 9.0}, summer) == 0
    assert headline_burst({at(2019, 7, 1, 14, 0): 9.0}, summer) == 1
    # tau caps the scan: a block after tau is not read.
    assert headline_burst({post: 9.0}, day, tau=at(2019, 11, 4, 14, 45)) == 0


def test_a_coarse_doc_api_resolution_is_refused():
    assert refuse_coarse_resolution("15min") == "15min"
    for coarse in ("hour", "HOUR", "day", "month", "", None):
        with pytest.raises(ResolutionRefused):
            refuse_coarse_resolution(coarse)


# ------------------------------------------------------------------------- the dump parser
def test_a_pageview_dump_line_parses():
    hour = at(2019, 11, 4, 13)
    w = parse_dump_line(b"en Natural_gas 45 0", hour)
    assert (w.project, w.article, w.views, w.hour_start_utc) == ("en", "Natural_gas", 45, hour)
    # The article is kept EXACTLY as the dump spells it; no redirect is resolved.
    assert parse_dump_line(b"en.m Price_of_oil 17 0", hour).project == "en.m"


@pytest.mark.parametrize("bad", [b"en Natural_gas 45", b"en Natural_gas 45 0 extra",
                                 b"en Natural_gas x 0", b"en Natural_gas -3 0"])
def test_a_malformed_dump_line_raises(bad: bytes):
    with pytest.raises(AttentionError):
        parse_dump_line(bad, at(2019, 11, 4, 13))


# ---------------------------------------------------------------------------- the namespace
def test_the_module_exposes_no_writer():
    """D608 asserts its own namespace holds no `fill_gap`; this is the same assertion for a
    different guarantee. A promise about code that does not exist can only be tested here."""
    bad = [n for n in dir(mod) if not n.startswith("_") and mod.FORBIDDEN_NAME_RE.search(n)]
    assert bad == ["NO_WRITER_HERE"], bad
    for name in ("write", "save", "write_fixture", "persist", "store"):
        assert not hasattr(mod, name)
    # and the regex is not vacuous: it would catch the thing it is for.
    assert mod.FORBIDDEN_NAME_RE.search("write_residue")


def test_the_module_source_opens_nothing_for_writing():
    """The namespace assertion above is about NAMES. This one is about the file: `attention.py`
    contains no `open(..., "w")`, no `write_text`, and no `write_bytes`."""
    import ast

    path = REPO / "src" / "backtest_framework" / "data" / "attention.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
    assert len(calls) > 50, "the AST walk found almost no calls; it is not reading the module"
    called = {getattr(c.func, "id", None) for c in calls} | {
        getattr(c.func, "attr", None) for c in calls}
    # `replace` is deliberately absent from this list: `bytes.replace` is a string method and
    # `attention.py` uses it in `_normalise_newlines`. Break what the assertion READS.
    for writer in ("open", "write", "write_text", "write_bytes", "writelines", "mkdir",
                   "touch", "unlink", "to_csv", "savez", "makedirs"):
        assert writer not in called, f"attention.py calls {writer}(); it must not write"
    # and the walk is not vacuous: it does find the reads this module is allowed to make.
    assert {"read_bytes", "read_text"} <= called


def _gkg(*, title: str = "", url: str = "https://example.invalid/x", themes: str = "",
         tone: str = "0.5,1,1,2,3,0,10", extras_tail: bytes = b"") -> bytes:
    """One synthetic 27-field GKG record. Written field by field so a test states its input."""
    fields = [b""] * 27
    fields[0] = b"20191104001500-1"
    fields[1] = b"20191104001500"
    fields[4] = url.encode("utf-8")
    fields[7] = themes.encode("ascii")
    fields[15] = tone.encode("ascii")
    fields[26] = b"<PAGE_TITLE>" + title.encode("utf-8") + b"</PAGE_TITLE>" + extras_tail
    return b"\t".join(fields)
