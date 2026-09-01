"""Integrity gates on the 57-ETF 15-minute fixture and the fetcher that builds it.

**The one that matters is the split gate.** The fixture is fetched `adjusted=false`
— deliberately, because back-adjusted prices drift every time a dividend is paid and
D24 requires an immutable snapshot. But as-traded means SPLITS ARE UNADJUSTED, and a
scan of all 3,194,849 bars found twelve of them sitting in the price series as
enormous single-bar returns. OIH's 1:20 reverse split on 2020-04-15 appears as a
**+1,772% 15-minute bar**. Hand that to a trend arm and it produces confident
nonsense, the way D184 did at daily frequency.

The build therefore back-adjusts from the events sidecar, and the two halves of that
are tested separately because they fail separately:

  `test_the_events_sidecar_pins_all_twelve_splits_by_name`
      pins each split by symbol, date and ratio. A re-fetch that silently returns a
      shorter SPLITS payload — five of the twelve are the 2025-12-05 SPDR sector
      splits, recorded NOWHERE else in this repo — would leave the fixture
      unadjusted with a sidecar that no longer knows it. This makes that loud.

  `test_no_bar_to_bar_move_exceeds_fifteen_percent_outside_the_known_events`
      reads the data rather than the sidecar. If the adjustment is ever dropped,
      applied in the wrong direction, or applied to the wrong side of the effective
      date, twelve enormous bars reappear and this fails naming them.

The rest are the boring gates that stop a re-fetch from quietly changing the shape of
the grid underneath a published study: 26 bars a session, regular hours only, no
zero-volume bars (D192), and a dividends sidecar that is actually populated — with an
EMPTY one `run_macd_ladder.dividend_panel` returns all-zero cash and
`total_log_returns` degenerates to `log_returns` in silence, which would make every
`*_with_dividends` number in the repo a lie.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "data" / "fixtures" / "etf_intraday_15m_raw.csv.gz"
META = REPO / "data" / "fixtures" / "etf_intraday_15m_raw.meta.json"
EVENTS = REPO / "data" / "fixtures" / "etf_intraday_15m_raw_events.json"


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module  # before exec_module: the module self-references
    spec.loader.exec_module(module)
    return module


F = _load("fetch_etf_intraday", "fetch_etf_intraday.py")


# --------------------------------------------------------------------------
# The twelve splits, pinned by name.
# --------------------------------------------------------------------------
# Alpha Vantage's SPLITS payload is the only record of five of these anywhere in
# this repo — the daily fixture's sidecar ends 2024-12-31, so the 2025-12-05 SPDR
# sector 2:1s exist nowhere else. Pinning them by name means a re-fetch that loses
# one fails HERE, loudly, instead of silently un-adjusting a price series.
EXPECTED_SPLITS = {
    ("IYT", "2024-03-07"): 4.0,     # 4:1 forward (ratio > 1 forward, < 1 reverse)
    ("OIH", "2020-04-15"): 0.05,    # 1:20 reverse — the +1,772% bar
    ("SMH", "2023-05-05"): 2.0,     # 2:1 forward
    ("UNG", "2018-01-05"): 0.25,    # 1:4 reverse
    ("UNG", "2024-01-24"): 0.25,    # 1:4 reverse, the second one
    ("USO", "2020-04-29"): 0.125,   # 1:8 reverse, the negative-futures aftermath
    ("XLB", "2025-12-05"): 2.0,     # SPDR sector 2:1 cluster, recorded nowhere else
    ("XLE", "2025-12-05"): 2.0,
    ("XLK", "2025-12-05"): 2.0,
    ("XLU", "2025-12-05"): 2.0,
    ("XLY", "2025-12-05"): 2.0,
    ("XOP", "2020-03-30"): 0.25,    # 1:4 reverse
}

MOVE_LIMIT = 0.15

# Bar-to-bar close moves above MOVE_LIMIT that are REAL market events, not
# corporate actions. Every one of these is an overnight gap into the 09:30 bar
# (except the USO 2020-04-02 intraday one) and every one has a named cause. This
# list is the reason the gate can be strict: anything NOT here is a defect.
#
# Sizes are the measured moves in the split-adjusted frame; they are stable under
# split adjustment because a ratio cancels out of a return everywhere except the
# effective-date bar itself.
KNOWN_REAL_MOVES = {
    # 2020-03-09: OPEC+ collapsed on the 6th, Saudi Arabia opened a price war, and
    # WTI gapped down ~25% overnight. First limit-down circuit breaker since 1997.
    ("XOP", "2020-03-09 09:30:00"),   # -29.7%
    ("OIH", "2020-03-09 09:30:00"),   # -23.9%
    ("USO", "2020-03-09 09:30:00"),   # -21.3%
    ("XLE", "2020-03-09 09:30:00"),   # -19.1%
    # 2020-03-12 and 2020-03-16: the other two circuit-breaker days of that fortnight
    # (WHO pandemic declaration, then the Fed's emergency Sunday cut). Non-US equity
    # ETFs gap hardest because their home markets moved while New York was shut.
    ("EWZ", "2020-03-12 09:30:00"),   # -16.9%, Brazil
    ("EWZ", "2020-03-16 09:30:00"),   # -15.9%, Brazil
    ("EWA", "2020-03-16 09:30:00"),   # -15.4%, Australia
    ("XLF", "2020-03-16 09:30:00"),   # -15.3%, banks into a zero-rate cut
    # 2020-03-19: the forced-liquidation low in precious metals. Junior miners were
    # sold to raise cash; this one is INTRADAY (15:45), not an overnight gap.
    ("GDXJ", "2020-03-19 15:45:00"),  # -15.5%
    # April 2020, USO's negative-futures episode. The May WTI contract settled at
    # -$37.63 on the 20th; USO was rolling through it, changed its mandate mid-month
    # under regulatory pressure, and reverse-split on the 29th.
    ("USO", "2020-04-02 10:30:00"),   # +17.3%, the OPEC-cut headline
    ("USO", "2020-04-27 09:30:00"),   # -16.7%, the forced roll out of the front month
    # 2020-11-09: the Pfizer efficacy announcement. The largest single-day
    # value/energy rotation on record; energy and regional banks gapped up together.
    ("OIH", "2020-11-09 09:30:00"),   # +17.8%
    ("XOP", "2020-11-09 09:30:00"),   # +15.4%
    ("KRE", "2020-11-09 09:30:00"),   # +15.1%
    # UNG is unlevered front-month natural gas, the most volatile thing in the
    # universe. Weather and LNG outages move it 15-20% overnight routinely; these
    # are gas, not corporate actions. Both UNG SPLITS are pinned above separately.
    ("UNG", "2022-06-14 09:30:00"),   # -15.5%, the Freeport LNG explosion
    ("UNG", "2024-12-30 09:30:00"),   # +19.8%, a cold-snap forecast revision
    ("UNG", "2026-01-20 09:30:00"),   # +16.8%
    ("UNG", "2026-02-02 09:30:00"),   # -18.8%
}


@pytest.fixture(scope="module")
def frame():
    """The whole 3.19M-row fixture, read ONCE and shared. It is a few seconds of
    gzip either way; paying it per-test would make this file unrunnable."""
    pd = pytest.importorskip("pandas")
    if not FIXTURE.exists():  # pragma: no cover - the artifact is committed
        pytest.skip("run scripts/fetch_etf_intraday.py --build first")
    df = pd.read_csv(FIXTURE)
    return df.sort_values(["symbol", "timestamp"], kind="stable").reset_index(drop=True)


@pytest.fixture(scope="module")
def meta():
    return json.loads(META.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def events():
    return json.loads(EVENTS.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# 1. The split gate
# --------------------------------------------------------------------------


def test_the_events_sidecar_pins_all_twelve_splits_by_name(events):
    """Exactly twelve splits, each by symbol, effective date and ratio.

    Not a count — a count would pass on twelve wrong ones. The five 2025-12-05 SPDR
    sector splits in particular exist in no other file in this repo, so if a re-fetch
    returns a truncated SPLITS payload this is the only place it can be caught."""
    got = {
        (symbol, day[:10]): ratio
        for symbol, rows in events["splits"].items()
        for day, ratio in rows
    }
    assert got == EXPECTED_SPLITS
    assert sum(len(v) for v in events["splits"].values()) == 12


def test_no_bar_to_bar_move_exceeds_fifteen_percent_outside_the_known_events(frame):
    """THE GATE. Read from the data, not from the sidecar.

    If the split adjustment is ever dropped, inverted, or applied to the wrong side
    of the effective date, the twelve corporate actions reappear as returns of up to
    +1,772% and this fails naming every one of them. Everything above the threshold
    must be on KNOWN_REAL_MOVES, and each entry there has a documented cause."""
    moves = frame.groupby("symbol", sort=False)["close"].pct_change()
    big = frame.loc[moves.abs() > MOVE_LIMIT, ["timestamp", "symbol"]]
    found = {(row.symbol, str(row.timestamp)) for row in big.itertuples()}
    assert not (found - KNOWN_REAL_MOVES), (
        "undocumented >15% bar moves — an un-adjusted split looks exactly like "
        f"this: {sorted(found - KNOWN_REAL_MOVES)}"
    )
    # Equality, not containment. A stale allow-list entry is a hole in the gate:
    # it would wave through a future split that happened to land on that bar.
    assert not (KNOWN_REAL_MOVES - found), (
        "allow-list entries no longer present in the data — the list has gone "
        f"stale and must be trimmed: {sorted(KNOWN_REAL_MOVES - found)}"
    )


def test_every_split_effective_date_is_a_quiet_bar_in_the_adjusted_frame(frame):
    """The complement. The gate above proves nothing survived the threshold; this
    proves the twelve specific bars were actually TOUCHED. A fixture that simply
    dropped those sessions would pass the gate and fail here."""
    moves = frame.groupby("symbol", sort=False)["close"].pct_change()
    seen = 0
    for (symbol, day), ratio in EXPECTED_SPLITS.items():
        at = frame.index[
            (frame["symbol"] == symbol) & (frame["timestamp"].str.startswith(day))
        ]
        assert len(at) > 0, f"{symbol} {day} is missing from the fixture entirely"
        first = at[0]
        move = moves.iloc[first]
        assert abs(move) <= MOVE_LIMIT, (
            f"{symbol} {day} still carries a {move:+.1%} bar — the x{ratio} split "
            "is UNADJUSTED"
        )
        seen += 1
    assert seen == 12


def test_the_meta_records_that_the_split_adjustment_was_applied(meta):
    """Belt to the data gate's braces: the build must say so in the snapshot, so a
    reader of the meta alone cannot mistake the frame."""
    assert meta.get("split_adjusted") is True
    assert meta.get("split_events_applied") == 12
    assert meta.get("split_adjusted_bars", 0) > 0
    assert meta["largest_residual_bar_move"]["move"] <= MOVE_LIMIT * 2


# --------------------------------------------------------------------------
# 2. Grid integrity
# --------------------------------------------------------------------------


def test_all_fifty_seven_symbols_are_present(frame, meta):
    assert len(F.SYMBOLS) == 57
    assert sorted(frame["symbol"].unique()) == sorted(F.SYMBOLS)
    assert meta["symbols_excluded"] == []


def test_only_regular_hours_bars_are_in_the_fixture(frame):
    """The build fetched extended hours and must have thrown them away. Extended
    bars exist only where something traded, so they are LIQUIDITY-CORRELATED — in a
    volume study that would inject the quantity under test into the sampling grid."""
    times = sorted(frame["timestamp"].str.slice(11, 16).unique())
    assert times[0] == "09:30" and times[-1] == "15:45"
    assert len(times) == F.FULL_SESSION_BARS == 26
    assert times[1] == "09:45", "the grid is not on 15-minute boundaries"


def test_the_vast_majority_of_sessions_are_exactly_twenty_six_bars(frame):
    """390 RTH minutes / 15 = 26, every session, every symbol. The residue is thin
    symbols failing to print in some slot — measured and disclosed by the build
    rather than forward-filled, because filling would invent data."""
    per_session = frame.groupby(
        ["symbol", frame["timestamp"].str.slice(0, 10)], sort=False
    ).size()
    full = (per_session == F.FULL_SESSION_BARS).mean()
    assert full > 0.995, f"only {full:.4%} of sessions are full"
    assert (per_session <= F.FULL_SESSION_BARS).all(), "a session has EXTRA bars"


def test_the_eighteen_half_days_were_dropped_entirely_and_are_not_the_short_sessions(
    frame, meta
):
    """The two causes of a short session need opposite treatment: a 13:00 early
    close is a calendar fact and is dropped at every symbol so the grid stays
    uniform; a thin symbol missing one print is a measurement and is kept. If the
    half-days leaked back in they would masquerade as the second kind."""
    half_days = meta["half_days_dropped"]
    assert len(half_days) == 18
    days = set(frame["timestamp"].str.slice(0, 10).unique())
    assert not (set(half_days) & days), "a dropped half-day is back in the fixture"

    per_session = frame.groupby(
        ["symbol", frame["timestamp"].str.slice(0, 10)], sort=False
    ).size()
    short_days = {
        day for (_sym, day), n in per_session.items() if n != F.FULL_SESSION_BARS
    }
    assert not (short_days & set(half_days))


def test_the_span_is_the_declared_one(frame, meta):
    assert (meta["start"], meta["end"]) == ("2018-01", "2026-08")
    assert frame["timestamp"].min()[:10] == "2018-01-02"
    assert frame["timestamp"].max()[:10] == "2026-08-26"


# --------------------------------------------------------------------------
# 3. Meta consistency — the snapshot must describe itself
# --------------------------------------------------------------------------


def test_the_meta_row_count_is_the_actual_row_count(frame, meta):
    assert meta["rows"] == len(frame)
    assert sum(meta["bars_per_symbol"].values()) == meta["rows"]


def test_symbols_included_is_exactly_what_is_in_the_data(frame, meta):
    """Both directions. A symbol listed but absent, or present but unlisted, both
    silently change what an equal-weight arm is averaging over."""
    assert set(meta["symbols_included"]) == set(frame["symbol"].unique())
    assert set(meta["bars_per_symbol"]) == set(meta["symbols_included"])
    counts = frame["symbol"].value_counts()
    for symbol, n in meta["bars_per_symbol"].items():
        assert counts[symbol] == n, symbol


def test_there_are_no_zero_volume_bars_and_the_meta_agrees(frame, meta):
    """D192's gate: an intraday study on a new provider must MEASURE its own
    universe's empty-bar rate, not assume it — yfinance's was 50% at 1h and 15% at
    15m, unexplained (D160). Verified against the data, not read off the meta,
    because the meta is written by the same code that would be wrong."""
    assert (frame["volume"] > 0).all(), "the fixture has zero-volume bars"
    assert meta["zero_volume_bars"] == 0
    assert meta["zero_volume_rate"] == 0.0


# --------------------------------------------------------------------------
# 4. Provenance — the things a re-fetch could change in silence
# --------------------------------------------------------------------------


def test_the_timezone_and_bar_boundary_are_recorded(meta):
    """US/Eastern is DST-shifting, so it is NOT the crypto fixtures' 'naive means
    UTC' convention (D108), and the timestamp marks the interval's OPEN — a bar
    stamped t is not complete until t+15m. Both were measured off the payload, and
    a strategy that reads either one backwards is peeking."""
    assert meta["timezone"] == F.TZ == "US/Eastern"
    assert "US/Eastern" in meta["timezone_note"]
    assert "OPEN" in meta["bar_boundary"]
    assert "[t, t+15m)" in meta["bar_boundary"]


def test_the_source_records_the_deliberate_adjusted_false_fetch(meta):
    """`adjusted=false` is a decision, not a default. Adjusted prices are
    BACK-adjusted and drift every time a dividend is paid, which breaks D24's
    immutable-snapshot requirement; as-traded values never change. The reason has to
    survive in the snapshot or the next person will 'fix' it."""
    assert "adjusted=false" in meta["source"]
    assert "D24" in meta["source"]
    assert "immutable" in meta["source"]


def test_the_dividends_sidecar_is_populated(events):
    """With an EMPTY sidecar `run_macd_ladder.dividend_panel` returns all-zero cash
    and `total_log_returns` degenerates to `log_returns` SILENTLY — no error, no
    warning — which would make every `*_with_dividends` key in this repo a lie about
    a price-only number. Non-emptiness is the only thing standing between the two."""
    dividends = events["dividends"]
    assert set(dividends) == set(F.SYMBOLS)
    total = sum(len(v) for v in dividends.values())
    assert total > 1_900, f"only {total} dividend records"
    paying = [s for s, v in dividends.items() if v]
    # GLD/SLV/UNG/USO are non-distributing commodity vehicles; everything else pays.
    assert len(paying) == 53
    zero = []
    for symbol, rows in dividends.items():
        for day, amount in rows:
            assert amount >= 0.0, f"{symbol} {day} is a NEGATIVE distribution"
            assert "2018-01" <= day[:7] <= "2026-08", f"{symbol} {day} out of span"
            if amount == 0.0:
                zero.append((symbol, day[:10]))
    # Exactly one zero-amount row exists: IEF 2023-12-28, a declared-then-zeroed
    # distribution the provider still returns. Harmless (it adds zero cash) but
    # pinned, because a payload that suddenly returns MANY zeros is a broken
    # payload and would drain `dividend_panel` without emptying the sidecar.
    assert zero == [("IEF", "2023-12-28")], zero


# --------------------------------------------------------------------------
# 5. The fetcher's own logic
# --------------------------------------------------------------------------


def test_months_covers_the_declared_span_inclusively():
    """104 months is the request budget per symbol; the plan's ETA and the whole
    good-citizen pacing argument are built on that number being right."""
    got = F.months("2018-01", "2026-08")
    assert len(got) == 104
    assert got[0] == "2018-01" and got[-1] == "2026-08"
    assert got == sorted(got)
    assert "2018-12" in got and "2019-01" in got  # the year rollover
    assert F.months("2020-05", "2020-05") == ["2020-05"]


def test_half_days_flags_a_market_wide_early_close_and_not_a_thin_symbol():
    """The distinction the whole half-day policy rests on. A 13:00 early close is a
    CALENDAR fact — most of the universe is short at once — and gets dropped. One
    thin symbol missing a print is a LIQUIDITY fact and must be kept and measured.
    Conflating them would either bin real sessions or leave a ragged grid."""
    counts = {}
    for i, symbol in enumerate(F.SYMBOLS):
        counts[(symbol, "2019-11-29")] = 13 if i < 40 else 26  # market-wide close
        counts[(symbol, "2019-11-27")] = 25 if i == 0 else 26  # one thin symbol
        counts[(symbol, "2019-11-26")] = 26                    # ordinary session
    got = F._half_days(counts, F.RTH_SESSION_BARS)
    assert got == {"2019-11-29"}


def test_half_days_takes_the_session_length_rather_than_assuming_it():
    """`_half_days` used to read a module-level FULL_SESSION_BARS of 26, which is
    the REGULAR-hours figure. The extended build's session is 64 slots, so the
    length is now a parameter -- otherwise an extended session of 40 bars would
    look complete and no early close would ever be detected."""
    counts = {(s, "2019-11-29"): (32 if i < 40 else 64)
              for i, s in enumerate(F.SYMBOLS)}
    assert F._half_days(counts, F.EXT_SESSION_BARS) == {"2019-11-29"}
    # Judged against the RTH length, every one of those sessions looks complete.
    assert F._half_days(counts, F.RTH_SESSION_BARS) == set()


def test_half_days_needs_only_half_the_universe_short_not_all_of_it():
    """The threshold is exactly half, and it has to be: on a 13:00 close the thin
    names print FEWER than 13 bars and the liquid ones exactly 13, so a rule keyed
    on a single shared count would miss it."""
    counts = {(s, "2020-07-03"): (13 if i % 2 == 0 else 26)
              for i, s in enumerate(F.SYMBOLS)}
    assert F._half_days(counts, F.RTH_SESSION_BARS) == {"2020-07-03"}
    counts = {(s, "2020-07-03"): (13 if i < 5 else 26)
              for i, s in enumerate(F.SYMBOLS)}
    assert F._half_days(counts, F.RTH_SESSION_BARS) == set()


def test_the_rate_limiter_actually_sleeps():
    """Good citizenship has to be structural. The tier ceiling is 75/min and the
    fetcher paces at 66 with margin — but only if `wait` really blocks. A limiter
    that records timestamps without sleeping would sail through a review and hammer
    the provider for six thousand requests."""
    limiter = F.RateLimiter(0.25)
    limiter.wait()          # the first call never sleeps: last is 0.0
    t0 = time.monotonic()
    limiter.wait()
    elapsed = time.monotonic() - t0
    assert elapsed >= 0.25 * 0.9, f"wait() returned after {elapsed:.3f}s"
    assert F.MIN_INTERVAL == 60.0 / F.REQUESTS_PER_MIN
    assert F.REQUESTS_PER_MIN < 75, "pacing must sit under the tier limit"


def test_split_factor_at_back_adjusts_only_bars_before_the_effective_date():
    """The direction that would be silently wrong. Back-adjustment expresses OLD
    bars in NEW terms, so the factor applies strictly BEFORE the effective date; the
    effective-date bar itself is already post-split and must be left alone. Off by
    one day here leaves a full split step in the series."""
    splits = [("2020-04-15T00:00:00", 0.05), ("2024-01-24T00:00:00", 0.25)]
    assert F.split_factor_at("2020-04-14 15:45:00", splits) == 0.05 * 0.25
    assert F.split_factor_at("2020-04-15 09:30:00", splits) == 0.25
    assert F.split_factor_at("2024-01-23 15:45:00", splits) == 0.25
    assert F.split_factor_at("2024-01-24 09:30:00", splits) == 1.0
    assert F.split_factor_at("2026-08-26 15:45:00", splits) == 1.0
    assert F.split_factor_at("2019-01-02 09:30:00", []) == 1.0


def test_build_targets_never_share_a_path_between_the_two_sessions():
    """THE REGRESSION GUARD FOR A REAL BUG. The first version of the extended
    build parameterised the fixture and the events sidecar but MISSED THE META,
    so `--extended` overwrote the committed regular-hours meta -- the exact
    destructive failure the separate-fixture change was written to prevent, and
    it was found only because git reported the committed file as modified."""
    rth = F.build_targets(True)
    ext = F.build_targets(False)
    assert rth == (F.FIXTURE, F.META, F.EVENTS)
    assert ext == (F.EXT_FIXTURE, F.EXT_META, F.EXT_EVENTS)
    assert not (set(rth) & set(ext)), "an output path is shared between sessions"
    assert len(set(rth)) == 3 and len(set(ext)) == 3


def test_do_build_writes_through_the_parameterised_paths_only():
    """Three constants with two of them swapped is a pattern that hides the one
    you forget. `do_build` must reach for none of the module-level output
    constants directly -- only the tuple `build_targets` hands it."""
    import inspect
    src = inspect.getsource(F.do_build)
    for name in ("FIXTURE", "META", "EVENTS", "EXT_FIXTURE", "EXT_META",
                 "EXT_EVENTS"):
        for forbidden in (f"{name}.write_text(", f"{name}.parent",
                          f"gzip.open({name}", f"open({name},"):
            assert forbidden not in src, (
                f"do_build writes through the unparameterised {name}"
            )
