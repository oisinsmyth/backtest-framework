"""Integrity gates on the extended-hours SPY/QQQ/IWM/DIA fixture.

**Two of these gates exist because the failure they catch is SILENT**, and a silent
failure here would be worse than no fixture at all — everything downstream would look
fine and be wrong.

  `test_the_extended_session_actually_arrived`
      `extended_hours=true` falling back to regular hours gives exactly 26 bars over
      09:30-15:45. Three of the four windows this fixture exists to measure would
      collapse to nothing, and the payload would look entirely healthy. Gated on the
      grid being materially wider than RTH, in BOTH directions, on essentially every
      session.

  `test_the_month_parameter_was_honoured`
      `FX_INTRADAY` silently ignores `month` and returns the trailing weeks instead —
      no error, no note, just the wrong data (measured 2026-08-29). Equities are
      BELIEVED to honour it, and belief is not a gate. Verified from the data: every
      month the fetch asked for is present, and the span is the declared one.

The third is D226's, and on this fixture it caught something else entirely:

  `test_no_unexplained_bar_move_above_fifteen_percent`
      run over the RAW series this gate fires on QQQ 2025-06-16 at +19.43% — not a
      split but a BAD PRINT, `low` and `close` both 16% away from an unmoved `open`
      and `high`. So the gate runs on non-suspect bars and the bad prints get their
      own tests, below.

And the one that is not about data at all:

  `test_the_api_key_never_appears_in_anything_the_fetcher_emits`
      the key is read from outside the repo and must never reach a log, a printed
      URL, the fixture, or the meta.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "data" / "fixtures" / "index_extended_15m_raw.csv.gz"
META = REPO / "data" / "fixtures" / "index_extended_15m_raw.meta.json"
EVENTS = REPO / "data" / "fixtures" / "index_extended_15m_raw_events.json"


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module          # before exec_module: it self-references
    spec.loader.exec_module(module)
    return module


F = _load("fetch_index_extended", "fetch_index_extended.py")

MOVE_LIMIT = 0.15


@pytest.fixture(scope="module")
def frame():
    """The whole 958k-row fixture, read ONCE and shared."""
    pd = pytest.importorskip("pandas")
    if not FIXTURE.exists():  # pragma: no cover - the artifact is committed
        pytest.skip("run scripts/fetch_index_extended.py --build first")
    df = pd.read_csv(FIXTURE)
    df["day"] = df["timestamp"].str.slice(0, 10)
    df["hhmm"] = df["timestamp"].str.slice(11, 16)
    return df.sort_values(["symbol", "timestamp"], kind="stable").reset_index(drop=True)


@pytest.fixture(scope="module")
def meta():
    return json.loads(META.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# 1. The extended session arrived — the gate that makes the fixture worth having
# --------------------------------------------------------------------------


def test_the_extended_session_actually_arrived(frame):
    """THE GATE. A silent fallback to regular hours is the failure that would
    invalidate everything downstream while looking perfectly healthy.

    Read from the data, not the meta, because the meta is written by the same code
    that would be wrong."""
    per_session = frame.groupby(["symbol", "day"], sort=False).size()
    assert per_session.median() >= 55, (
        f"median {per_session.median()} bars/session — regular hours alone is 26, so "
        "this is a partial or absent extended session"
    )
    assert per_session.median() > 2 * F.RTH_SESSION_BARS

    times = set(frame["hhmm"])
    assert "04:00" in times, "no 04:00 bar exists anywhere — the pre-market is absent"
    assert "19:45" in times, "no 19:45 bar exists anywhere — the post-market is absent"
    assert min(times) == "04:00" and max(times) == "19:45"

    # Both directions, on essentially every session. One-sided coverage would still
    # break the decomposition and would not show up in a bar count.
    by_session = frame.groupby(["symbol", "day"], sort=False)["hhmm"]
    has_pre = by_session.min() < F.RTH_OPEN
    has_post = by_session.max() > F.RTH_LAST_BAR
    assert has_pre.mean() > 0.99, f"only {has_pre.mean():.2%} of sessions have a pre-market"
    assert has_post.mean() > 0.99, f"only {has_post.mean():.2%} of sessions have a post-market"


def test_the_grid_is_on_fifteen_minute_boundaries_and_stops_at_the_session_end(frame):
    """Bars stamped 20:00 and later exist in the raw feed — 20:00 in roughly half of
    sessions, 20:15-23:45 in 5-9% — and are past the documented 8:00pm close. They are
    dropped at build so `16:00 -> 20:00` means the same thing on every day."""
    times = sorted(set(frame["hhmm"]))
    assert len(times) == F.FULL_SESSION_BARS == 64, f"{len(times)} distinct bar times"
    assert times[0] == "04:00" and times[1] == "04:15" and times[-1] == "19:45"
    assert all(t[3:] in ("00", "15", "30", "45") for t in times)


def test_the_meta_records_the_gate_results_and_they_all_passed(meta):
    g = meta["gates"]
    assert g["extended_session_arrived"] is True
    assert g["the_04_00_and_19_45_bars_exist"] is True
    assert g["month_honoured"] is True
    assert g["no_unexplained_large_bar"] is True
    assert g["slices_without_extended_session"] == []
    assert g["median_bars_per_session"] >= 55
    assert g["rth_only_would_be"] == 26
    assert meta["session"].startswith("extended_hours")


def test_the_clock_anchor_coverage_is_recorded_per_symbol_and_era(meta):
    """Not a pass/fail — a DISCLOSURE, and the one a consumer most needs.

    An extended-hours bar exists only where something traded, so the exact 04:00 bar
    is liquidity-conditioned: SPY prints it on 91.6% of 2010-2019 sessions and DIA on
    22.1%. Keying a measurement on the clock would select on activity and then measure
    returns. This pins that the numbers are recorded, and pins the specific fact that
    early-era DIA coverage is poor, so a future re-fetch that silently 'fixes' it
    cannot pass unnoticed."""
    cov = meta["gates"]["anchor_bar_coverage_by_symbol_and_era"]
    assert set(cov) == {f"{s}|{e}" for s in F.SYMBOLS for e in F.ERAS}
    for v in cov.values():
        assert v["sessions"] > 200
        assert v["any_pre"] > 0.99 and v["any_post"] > 0.99
    assert cov["SPY|2021-2026"]["04:00"] > 0.99
    assert cov["DIA|2010-2019"]["04:00"] < 0.40, (
        "DIA's early-era 04:00 coverage is the documented reason the consumer uses "
        "first/last PRINT rather than a clock anchor; if this improved, that "
        "reasoning needs revisiting rather than silently inheriting"
    )
    assert "LIQUIDITY-CONDITIONED" in meta["gates"]["anchor_coverage_note"]


# --------------------------------------------------------------------------
# 2. `month` was honoured — the FX_INTRADAY failure mode
# --------------------------------------------------------------------------


def test_the_month_parameter_was_honoured(frame, meta):
    """`FX_INTRADAY` silently ignores `month` and returns the trailing weeks. No
    error, no note, just the wrong data — which is the dangerous kind.

    If equities did the same, every slice would hold the same recent window and the
    fixture would cover a few weeks pretending to be sixteen years."""
    assert meta["gates"]["month_honoured"] is True
    assert meta["gates"]["bars_outside_requested_month"] == 0

    months = set(frame["timestamp"].str.slice(0, 7))
    expected = set(F.months(F.START_MONTH, F.END_MONTH))
    assert months == expected, f"missing months: {sorted(expected - months)[:5]}"
    assert len(months) == 200
    assert frame["day"].min() == "2010-01-04"
    assert frame["day"].max()[:7] == "2026-08"


def test_month_honoured_rejects_the_fx_intraday_failure_shape():
    """The detector itself, on a synthetic payload shaped like the FX failure: asked
    for 2020-03, handed the trailing weeks."""
    good = {"2020-03-02 09:30:00": {}, "2020-03-31 15:45:00": {}}
    ok, foreign, _ = F.month_honoured(good, "2020-03")
    assert ok and foreign == 0

    fx_shaped = {"2026-08-27 09:30:00": {}, "2026-08-28 15:45:00": {}}
    ok, foreign, span = F.month_honoured(fx_shaped, "2020-03")
    assert not ok and foreign == 2 and "2026-08-27" in span

    # One stray bar is still a failure: a partially-wrong slice is not a healthy one.
    ok, foreign, _ = F.month_honoured({**good, "2020-04-01 09:30:00": {}}, "2020-03")
    assert not ok and foreign == 1

    # An empty month is a FACT about the symbol, not a violation.
    assert F.month_honoured({}, "2020-03")[0] is True


def test_extended_session_present_rejects_a_regular_hours_fallback():
    """The other detector, on a synthetic RTH-only payload — 26 bars, 09:30-15:45,
    which is exactly what a silently ignored `extended_hours` returns."""
    rth_times = [f"{9 + (30 + 15 * i) // 60:02d}:{(30 + 15 * i) % 60:02d}"
                 for i in range(26)]
    rth_only = {f"2020-03-{d:02d} {t}:00": {} for d in range(2, 20) for t in rth_times}
    g = F.extended_session_present(rth_only)
    assert g["ok"] is False
    assert g["median_bars"] == 26 and g["median_rth_bars"] == 26
    assert g["share_with_premarket"] == 0.0 and g["share_with_postmarket"] == 0.0

    # And it must ACCEPT a thin-but-genuine extended session. IWM 2010-01 measured 48
    # bars/session over 04:15-19:45 — the first version of this gate rejected that at
    # a 55-bar floor, which was wrong: pre- and post-market bars were present on 19 of
    # 19 sessions and RTH was exactly 26. The gate is "wider than RTH", not "as wide
    # as SPY".
    thin = dict(rth_only)
    thin.update({f"2020-03-{d:02d} {t}:00": {}
                 for d in range(2, 20)
                 for t in ("04:15", "07:00", "08:30", "16:00", "17:30", "19:45")})
    g = F.extended_session_present(thin)
    assert g["ok"] is True
    assert g["share_with_premarket"] == 1.0 and g["share_with_postmarket"] == 1.0


# --------------------------------------------------------------------------
# 3. Corporate actions and bad prints — D226's gate, and what it turned up
# --------------------------------------------------------------------------


def test_the_events_sidecar_records_zero_splits_and_a_populated_dividend_list():
    """ZERO splits is the expected answer for these four and it was CHECKED, not
    assumed. D226 found twelve unadjusted splits across the 57-ETF fixture, one of
    them a +1,772% single 15-minute bar; a build that assumes the answer fails
    silently. If any of these four ever splits, this fails and the fixture must be
    rebuilt rather than quietly carrying a step in the price series."""
    events = json.loads(EVENTS.read_text(encoding="utf-8"))
    assert set(events["splits"]) == set(F.SYMBOLS)
    assert all(v == [] for v in events["splits"].values()), events["splits"]
    assert sum(len(v) for v in events["dividends"].values()) > 350
    for symbol, rows in events["dividends"].items():
        assert rows, f"{symbol} has no dividends — the sidecar is not populated"
        for day, amount in rows:
            assert amount >= 0.0, f"{symbol} {day} is a NEGATIVE distribution"
            assert F.START_MONTH <= day[:7] <= F.END_MONTH


def test_no_unexplained_bar_move_above_fifteen_percent(frame):
    """D226's gate — an unadjusted corporate action shows up as an enormous single
    bar and nothing else in a price series looks like it.

    Restricted to non-suspect bars ON PURPOSE. Over the raw series this fires on QQQ
    2025-06-16 17:00 at +19.43%, which is a bad print, not a split — a true positive
    for a different question and useless for this one. The bad prints have their own
    tests below."""
    clean = frame[frame["suspect"] == 0]
    moves = clean.groupby("symbol", sort=False)["close"].pct_change()
    big = clean.loc[moves.abs() > MOVE_LIMIT, ["timestamp", "symbol"]]
    assert big.empty, (
        "undocumented >15% bar moves — an unadjusted split looks exactly like this: "
        f"{[tuple(r) for r in big.itertuples(index=False)][:10]}"
    )
    assert frame["suspect"].isin((0, 1)).all()


def test_the_bad_print_census_is_recorded_and_the_pathology_is_where_it_was_found(meta):
    """The finding this fetch turned up that nobody was looking for.

    QQQ 2025-06-16 16:45: open 534.18, high 534.25, low 447.2455, close 447.2455 —
    and the same bogus value repeats across three consecutive bars. Across the whole
    fixture the worst raw lower wick is +907%. It is a POST-MARKET pathology and a
    RECENT one, and both facts are pinned here because either changing would mean the
    filter is doing something different from what it was designed to do."""
    c = meta["bad_prints"]
    assert 0 < c["suspect_rate"] < 0.01, c["suspect_rate"]
    assert c["worst_lower_wick_raw"] > 5.0, "the 907% wick has vanished — re-derive"
    assert c["by_segment"]["post"] > 10 * max(c["by_segment"]["pre"], 1)
    # Extremes are filtered in the EXTENDED session only: in regular hours the large
    # wicks are genuine dislocations (2010-05-06, 2015-08-24, 2018-02-06, 2025-04-09)
    # and erasing them would delete the exact tail a drawdown study is about.
    assert c["by_segment"]["rth"] == 0
    recent = sum(v for y, v in c["by_year"].items() if y >= "2023")
    assert recent > 0.8 * c["suspect_bars"], (
        "the pathology was measured as a post-2022 feed change; if it is now spread "
        "evenly across the span the diagnosis was wrong"
    )
    assert c["tolerance"] == F.SUSPECT_TOL == 0.03


def test_the_suspect_flag_leaves_the_real_dislocations_alone(frame):
    """The complement, and the one that stops the filter being a beautifier.

    A corroboration rule must keep an extreme that neighbouring bars corroborate. If
    these were flagged, the filter would be erasing the worst days in the sample —
    precisely the observations a trailing-drawdown measurement is about."""
    real = [("QQQ", "2010-05-06 14:45:00"),    # the Flash Crash
            ("SPY", "2010-05-06 14:45:00"),
            ("QQQ", "2015-08-24 09:30:00"),    # the ETF dislocation open
            ("SPY", "2018-02-06 15:30:00"),    # Volmageddon
            ("SPY", "2020-03-16 09:30:00"),    # the limit-down open
            ("QQQ", "2025-04-09 14:15:00")]    # the tariff reversal
    for symbol, stamp in real:
        row = frame[(frame["symbol"] == symbol) & (frame["timestamp"] == stamp)]
        assert len(row) == 1, f"{symbol} {stamp} is missing from the fixture"
        assert int(row["suspect"].iloc[0]) == 0, (
            f"{symbol} {stamp} was flagged as a bad print — it is a real dislocation "
            "and the filter is erasing the tail it exists to let through"
        )


def test_flag_bad_prints_catches_the_qqq_signature_and_spares_a_real_move():
    """The detector on hand-built bars, so a change in the rule fails HERE rather
    than shifting a headline number by a few basis points somewhere downstream."""
    def bar(ts, o, h, lo, c):
        return (ts, "QQQ", o, h, lo, c, 1000.0)

    # The measured signature, transcribed from QQQ 2025-06-16: open and high unmoved,
    # low (and on the 16:45 bar the close too) 16% away, with the SAME bogus value
    # repeating across three consecutive bars while the neighbours sit at the true
    # price. The clean bars either side are what make the middle three flaggable.
    df, census = F.flag_bad_prints([
        bar("2025-06-16 16:30:00", 534.1100, 534.3000, 533.7500, 534.2100),
        bar("2025-06-16 16:45:00", 534.1800, 534.2500, 447.2455, 447.2455),
        bar("2025-06-16 17:00:00", 534.0000, 534.3600, 442.4496, 534.1250),
        bar("2025-06-16 17:15:00", 534.1250, 534.3500, 447.2455, 534.3000),
        bar("2025-06-16 17:30:00", 534.3000, 534.4900, 534.2600, 534.4700),
    ])
    assert list(df["suspect"]) == [0, 1, 1, 1, 0]
    assert census["by_segment"]["post"] == 3

    # A genuine fast move: every bar steps down together, so each is corroborated by
    # its neighbours and nothing is flagged. This is what keeps 2020-03-16 in.
    df, _ = F.flag_bad_prints([
        bar("2025-06-16 16:15:00", 547.00, 547.30, 533.50, 534.00),
        bar("2025-06-16 16:30:00", 534.00, 534.20, 520.00, 521.00),
        bar("2025-06-16 16:45:00", 521.00, 521.50, 505.00, 506.00),
        bar("2025-06-16 17:00:00", 506.00, 507.00, 495.00, 496.00),
        bar("2025-06-16 17:15:00", 496.00, 497.00, 487.00, 488.00),
    ])
    assert list(df["suspect"]) == [0, 0, 0, 0, 0], (
        "a monotone fall was flagged — each bar IS corroborated by its neighbours "
        "and this is the case that keeps real dislocations in the sample"
    )


def test_flag_bad_prints_exempts_the_first_and_last_bar_of_each_symbol():
    """A corroboration rule needs corroborators, and the series ends have only one.

    A one-sided band is pulled by whichever neighbour exists, so a falling series
    flags its own last bar. Eight bars in 958,217 on the real fixture — but it is a
    false positive by construction, not by luck, so the rule exempts them explicitly
    rather than leaving a known-wrong verdict in the data."""
    def bar(ts, o, h, lo, c):
        return (ts, "QQQ", o, h, lo, c, 1000.0)

    df, census = F.flag_bad_prints([
        bar("2025-06-16 16:30:00", 534.00, 534.20, 520.00, 521.00),
        bar("2025-06-16 16:45:00", 521.00, 521.50, 505.00, 506.00),
        bar("2025-06-16 17:00:00", 506.00, 507.00, 495.00, 496.00),
    ])
    assert list(df["suspect"]) == [0, 0, 0]
    assert census["edge_bars_exempt"] == 2


def test_largest_clean_close_move_ignores_suspect_bars():
    """The gate must test what it is named for. Run over the raw series it reports a
    bad print and says nothing about corporate actions."""
    import pandas as pd
    df = pd.DataFrame({
        "timestamp": ["2025-06-16 16:30:00", "2025-06-16 16:45:00",
                      "2025-06-16 17:00:00"],
        "symbol": ["QQQ"] * 3,
        "close": [534.21, 447.24, 534.12],
        "suspect": [0, 1, 0],
    })
    got = F.largest_clean_close_move(df)
    assert got["move"] < 0.01, got          # 534.21 -> 534.12, the two clean bars
    df["suspect"] = 0
    assert F.largest_clean_close_move(df)["move"] > 0.15


# --------------------------------------------------------------------------
# 4. Grid integrity and self-description
# --------------------------------------------------------------------------


def test_all_four_symbols_are_present_with_the_same_session_calendar(frame, meta):
    assert F.SYMBOLS == ("SPY", "QQQ", "IWM", "DIA")
    assert sorted(frame["symbol"].unique()) == sorted(F.SYMBOLS)
    assert len(set(meta["sessions_per_symbol"].values())) == 1, (
        "the four symbols do not share a session calendar: "
        f"{meta['sessions_per_symbol']}"
    )


def test_regular_hours_are_still_exactly_twenty_six_bars(frame):
    """The RTH core must be unchanged by keeping the extended session — if it is not,
    something other than the session width changed and every comparison to the
    existing RTH fixture is off."""
    rth = frame[(frame["hhmm"] >= F.RTH_OPEN) & (frame["hhmm"] <= F.RTH_LAST_BAR)]
    per_session = rth.groupby(["symbol", "day"], sort=False).size()
    assert (per_session <= 26).all(), "a regular session has EXTRA bars"
    assert (per_session == 26).mean() > 0.99


def test_the_meta_row_count_and_symbol_counts_are_the_actual_ones(frame, meta):
    assert meta["rows"] == len(frame)
    assert sum(meta["bars_per_symbol"].values()) == meta["rows"]
    counts = frame["symbol"].value_counts()
    for symbol, n in meta["bars_per_symbol"].items():
        assert counts[symbol] == n, symbol


def test_half_days_are_flagged_and_deliberately_not_dropped(frame, meta):
    """A departure from `fetch_etf_intraday.py`, which drops them. Here the grid is
    ragged by construction, so rectangularity is not available and dropping would
    discard real sessions for a property that cannot be attained. The consumer
    excludes them where they matter — a 13:00 close has no 16:00->20:00 window."""
    half = set(meta["half_days_flagged_not_dropped"])
    assert 15 <= len(half) <= 40, len(half)
    assert half <= set(frame["day"].unique()), "a flagged half-day is not in the data"
    assert "KEPT and flagged" in meta["half_day_policy"]


def test_the_timezone_and_bar_boundary_are_recorded(meta):
    """US/Eastern is DST-shifting, so NOT the crypto fixtures' 'naive means UTC'
    convention (D108). And the stamp marks the interval's OPEN, which is what makes
    the 15:45 bar's close the 16:00 print and the 19:45 bar's close the 20:00 print —
    the entire window decomposition rests on that."""
    assert meta["timezone"] == F.TZ == "US/Eastern"
    assert "OPEN" in meta["bar_boundary"] and "[t, t+15m)" in meta["bar_boundary"]
    assert "19:45" in meta["session_note"] and "20:00 print" in meta["session_note"]
    assert "adjusted=false" in meta["source"] and "D24" in meta["source"]


# --------------------------------------------------------------------------
# 5. The fetcher's own logic, and the key
# --------------------------------------------------------------------------


def test_the_api_key_never_appears_in_anything_the_fetcher_emits(monkeypatch, capsys):
    """The key is read from the environment or from OUTSIDE the repo, and must never
    reach a log, a printed URL, the fixture or the meta. `--plan` is the one path
    that both reads the key location and prints, so it is the one that gets checked."""
    secret = "ZZTOPSECRETKEY99"
    monkeypatch.setenv("ALPHAVANTAGE_API_KEY", secret)
    assert F.api_key() == secret
    F.do_plan()
    out = capsys.readouterr().out
    assert secret not in out
    assert "env ALPHAVANTAGE_API_KEY" in out, "the plan must name the SOURCE, not the key"

    for path in (META, EVENTS):
        assert secret not in path.read_text(encoding="utf-8")
    meta_text = META.read_text(encoding="utf-8")
    for token in ("apikey", "apiKey", "api_key"):
        assert token not in meta_text, f"{token} leaked into the meta"


def test_api_key_prefers_the_environment_over_the_file(monkeypatch):
    monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "  fromenv  ")
    assert F.api_key() == "fromenv"
    monkeypatch.delenv("ALPHAVANTAGE_API_KEY")
    monkeypatch.setattr(F, "KEY_FILE", Path("does-not-exist"))
    with pytest.raises(SystemExit):
        F.api_key()


def test_months_covers_the_declared_span_inclusively():
    """200 months x 4 symbols is the request budget, and the whole pacing argument
    rests on that number being right."""
    got = F.months("2010-01", "2026-08")
    assert len(got) == 200
    assert got[0] == "2010-01" and got[-1] == "2026-08"
    assert got == sorted(got)
    assert "2010-12" in got and "2011-01" in got          # the year rollover
    assert F.months("2020-05", "2020-05") == ["2020-05"]


def test_the_rate_limiter_actually_sleeps():
    """Good citizenship has to be structural. The tier ceiling is 75/min and the
    fetcher paces at 66 — but only if `wait` really blocks. A limiter that records
    timestamps without sleeping would sail through a review and then hammer the
    provider for eight hundred requests."""
    limiter = F.RateLimiter(0.25)
    limiter.wait()                            # the first call never sleeps
    t0 = time.monotonic()
    limiter.wait()
    assert time.monotonic() - t0 >= 0.25 * 0.9
    assert F.MIN_INTERVAL == 60.0 / F.REQUESTS_PER_MIN
    assert F.REQUESTS_PER_MIN < 75, "pacing must sit under the tier limit"
    assert F.MAX_CONSECUTIVE_FAILURES == 5


def test_split_factor_at_back_adjusts_only_bars_before_the_effective_date():
    """These four have no splits in span, so this helper is currently a no-op on real
    data — which is exactly why it needs its own test. If one of them ever splits, the
    build starts using a code path nothing else exercises."""
    splits = [("2020-04-15T00:00:00", 0.05), ("2024-01-24T00:00:00", 0.25)]
    assert F.split_factor_at("2020-04-14 15:45:00", splits) == 0.05 * 0.25
    assert F.split_factor_at("2020-04-15 09:30:00", splits) == 0.25
    assert F.split_factor_at("2024-01-24 09:30:00", splits) == 1.0
    assert F.split_factor_at("2019-01-02 09:30:00", []) == 1.0


def test_the_era_split_is_fixed_in_one_place():
    """D247's +8.59% is era-dependent, so every number is split the same way. The
    fetcher and the consumer must not be able to disagree about the boundaries."""
    assert F.ERAS == ("2010-2019", "2020", "2021-2026")
    assert F.era_of("2010-01-04") == "2010-2019"
    assert F.era_of("2019-12-31") == "2010-2019"
    assert F.era_of("2020-01-01") == "2020"
    assert F.era_of("2020-12-31") == "2020"
    assert F.era_of("2021-01-01") == "2021-2026"
    assert F.era_of("2026-08-26") == "2021-2026"
