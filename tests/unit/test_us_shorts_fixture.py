"""Integrity gates on the dead-inclusive US single-name short-side fixture (D252).

Four things can quietly ruin this fixture, and there is a test for each.

  **1. An unadjusted split.** Single stocks carry far more corporate actions than
  ETFs, and the failure mode is not subtle: D226 found OIH's 1:20 reverse split
  sitting in a fixture as a **+1,772% single bar**. One of those in a universe this
  size would dominate any cross-sectional statistic computed over it. Two tests, split
  apart because they fail apart — one reads the SIDECAR and checks every recorded
  split leaves no discontinuity behind, the other reads the DATA and checks no
  enormous bar survives anywhere, whether or not the sidecar knows about it.

  **2. A screen that reads the study window.** The screen is what decides which
  symbols exist, so if it can see performance the whole fixture is selection on the
  outcome. `apply_screen` is called directly with a synthetic series built to make
  the two windows disagree as loudly as possible.

  **3. A dead cohort that quietly vanishes.** This fixture exists BECAUSE dead
  companies are where a short book earns (D141-D144: 67% of the crypto wrecks beat
  matched exposure against 45% of the survivors). A build that ends up materially all
  survivors is worse than no build, so the floor is asserted here as well as enforced
  in `--build`.

  **4. The API key in an artifact.** Alpha Vantage's terms make the key the account,
  and a key committed to git is a key leaked. Every artifact this pipeline writes, and
  the source that writes them, is scanned for the literal key.
"""

from __future__ import annotations

import csv
import gzip
import importlib.util
import json
import os
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "data" / "fixtures" / "us_shorts_daily_raw.csv.gz"
EVENTS = REPO / "data" / "fixtures" / "us_shorts_daily_raw_events.json"
META = REPO / "data" / "fixtures" / "us_shorts_daily_raw.meta.json"
SCRIPT = REPO / "scripts" / "fetch_short_universe.py"


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module  # before exec_module: the module self-references
    spec.loader.exec_module(module)
    return module


F = _load("fetch_short_universe", "fetch_short_universe.py")

@pytest.fixture(scope="module")
def meta() -> dict:
    if not META.exists():
        pytest.skip("meta not built on this machine")
    return json.loads(META.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def closes_by_symbol(requires_panel) -> dict[str, list[tuple[str, float, float]]]:
    """(date, adjusted close, adjusted volume) per symbol, in file order. One pass.

    THE PANEL GUARD LIVES HERE, not on the tests. A module-level
    `@needs_fixture = pytest.mark.skipif(not FIXTURE.exists(), ...)` used to decorate
    20 tests, and 14 of them never opened the panel at all — they read only META and
    EVENTS, which are TRACKED and present on every clone. So a clone without the
    69 MB gzip (D191: the raw cache is local and gitignored) silently skipped its
    sidecar, meta, screen and exclusion gates: they were never run, and a regression
    in any of them would have been invisible outside this machine. The starkest was
    `test_load_panel_really_does_refuse_this_fixture`, whose whole body is a source
    grep of scripts/run_macd_ladder.py. Gating the READER rather than the tests is
    the pattern the sibling fixtures already use —
    tests/unit/test_etf_intraday_fixture.py:137 and
    tests/unit/test_index_extended_fixture.py:70 — and it keeps the skip attached to
    the thing that actually needs the file."""
    requires_panel(FIXTURE)
    out: dict[str, list[tuple[str, float, float]]] = defaultdict(list)
    with gzip.open(FIXTURE, "rt", newline="") as f:
        for row in csv.DictReader(f):
            out[row["symbol"]].append(
                (row["timestamp"][:10], float(row["close"]), float(row["volume"]))
            )
    return dict(out)


# ===========================================================================
# 1. THE SPLIT-ADJUSTMENT GATE
# ===========================================================================

def test_every_recorded_split_leaves_no_discontinuity_in_the_adjusted_prices(closes_by_symbol):
    """GATE A, recomputed from the data rather than read out of the meta.

    A split is the one place we KNOW the raw series jumps. If the adjustment were
    dropped, applied in the wrong direction, or applied on the wrong side of the
    effective date, the jump would still be there on exactly these dates. Reverse
    splits are the dangerous half — a 1:20 leaves x20 behind — so the test walks
    every recorded split of ratio >= 1.5 or <= 1/1.5 and demands the bar look
    ordinary."""
    events = json.loads(EVENTS.read_text(encoding="utf-8"))
    meta_ = json.loads(META.read_text(encoding="utf-8"))
    # A split date can carry a genuine event ON TOP of the split. TAOP's 2020-07-30 is
    # a 1:6 reverse AND a x4.3 move on 109M shares against a 563k baseline; there the
    # adjustment did take and the residual is the market. The test defers to the
    # classifier exactly as the build does, rather than carrying its own opinion.
    corroborated = {(c["symbol"], c["date"])
                    for c in meta_["gates"]["gate_b"]["all_classified_moves"]
                    if c["klass"] == "corroborated"}
    failures = []
    checked = 0
    for sym, splits in events["splits"].items():
        series = closes_by_symbol.get(sym)
        if not series:
            continue
        idx = {d: i for i, (d, _c, _v) in enumerate(series)}
        for eff, ratio in splits:
            d = eff[:10]
            i = idx.get(d)
            if i is None or i == 0:
                continue  # the split predates this symbol's in-span bars
            if not (ratio >= F.GATE_A_MIN_RATIO or ratio <= 1.0 / F.GATE_A_MIN_RATIO):
                continue
            if (sym, d) in corroborated:
                continue
            checked += 1
            moved = series[i][1] / series[i - 1][1]
            if abs(moved - 1.0) > F.GATE_A_TOLERANCE:
                failures.append((sym, d, ratio, round(moved, 3)))
    assert checked > 0, "no in-span splits of consequence — the gate would be vacuous"
    assert not failures, (
        f"{len(failures)} of {checked} recorded splits still show a discontinuity in the "
        f"ADJUSTED prices, i.e. the adjustment did not take: {failures[:12]}"
    )


def test_no_adjusted_bar_multiplies_the_price_outside_the_documented_events(closes_by_symbol):
    """GATE B, and it reads the DATA, not the sidecar.

    The previous test can only find splits the sidecar knows about. This one finds the
    ones it does not: any bar-to-bar close ratio at or above 4x is, in US common stock,
    overwhelmingly a reverse split that was missed. Anything not on
    `DOCUMENTED_LARGE_MOVES` is a defect, and that list is what lets the gate be strict.

    **The gate is deliberately one-sided.** An 80% single-day LOSS is a real and common
    event in this universe — bankruptcy, fraud, a failed trial — and it is precisely
    what a short book exists to capture. A symmetric gate would delete the payload.

    Two classes are exempt and both are reported rather than waved through. A move
    spanning a trading HALT is not a one-day return — an 83-day Chapter 11 suspension
    is a reorganised capital structure. And a spike that REVERTS is a single bad print,
    which D6 leaves in the raw fixture for D25's `clean()` to remove at load; deleting
    it here would silently depart from the convention every other fixture follows."""
    import statistics as _st

    offenders = []
    for sym, series in closes_by_symbol.items():
        dollars = [c * v for _d, c, v in series]
        for i in range(1, len(series)):
            d, cur, _ = series[i]
            prev = series[i - 1][1]
            if prev <= 0 or cur <= 0 or cur / prev < F.GATE_B_UP_RATIO:
                continue
            if (date.fromisoformat(d) - date.fromisoformat(series[i - 1][0])).days > F.HALT_GAP_DAYS:
                continue
            back = []
            if i + 1 < len(series):
                back.append(series[i + 1][1] / prev)
            if i >= 2 and series[i - 2][1] > 0:
                back.append(cur / series[i - 2][1])
            if any(1 / F.REVERT_BAND <= b <= F.REVERT_BAND for b in back):
                continue
            lo, hi = max(0, i - F.BASELINE_WINDOW - 2), i - 2
            if hi <= lo:
                lo, hi = 0, i
            base = _st.median(dollars[lo:hi]) if hi > lo else 0.0
            dv = (dollars[i] / base) if base > 0 else None
            corroborated = (dv is not None and dv >= F.CORROBORATION_DOLLAR_VOLUME
                            and cur / prev < F.IMPLAUSIBLE_RATIO)
            if not corroborated:
                offenders.append((sym, d, round(cur / prev, 2),
                                  round(dv, 1) if dv else None))
    assert not offenders, (
        f"{len(offenders)} persistent up-steps of >= x{F.GATE_B_UP_RATIO} with no volume "
        "behind them survived into the fixture. Each is an unrecorded corporate action "
        "or bad data — ORIG's x300 was Ocean Rig's post-restructuring reverse split, "
        f"which the provider records no coefficient for: {offenders[:15]}"
    )


def test_build_never_reads_the_sidecar_it_writes():
    """`--build` must be a pure function of the cache and the selection.

    It was not. `--actions` wrote the committed sidecar, `--build` read it, pruned it
    to the symbols that survived the data-quality gates, and wrote it back — so the
    SECOND `--build` saw a sidecar with the excluded symbols' splits already gone, did
    not apply them, reached a different verdict, and produced a different fixture.
    1,580 -> 1,573 -> 1,574 symbols across three runs of unchanged code.

    A committed artifact must not depend on how many times the builder ran. The full
    sidecar now lives in the cache; the committed one is derived from it and never fed
    back."""
    src = SCRIPT.read_text(encoding="utf-8")
    build = src[src.index("def do_build("):]
    assert "EVENTS_FULL.read_text" in build, "build must read the CACHED full sidecar"
    assert "EVENTS.read_text" not in build, "build must not read the artifact it writes"
    actions = src[src.index("def do_actions("):src.index("def do_build(")]
    assert "EVENTS.write_text" not in actions, "--actions must write the cache, not the sidecar"


def test_the_committed_sidecar_is_exactly_the_fixtures_symbols(meta):
    """The committed sidecar and the fixture must name the same symbols. A sidecar
    listing events for absent symbols invites a loader to build a longer index than the
    data supports."""
    events = json.loads(EVENTS.read_text(encoding="utf-8"))
    assert set(events["splits"]) == set(meta["symbols"])
    assert set(events["dividends"]) == set(meta["symbols"])
    full = F.EVENTS_FULL
    if full.exists():
        cached = json.loads(full.read_text(encoding="utf-8"))
        assert set(events["splits"]) <= set(cached["splits"]), "sidecar is not a subset of the cache"
        for sym in events["splits"]:
            assert events["splits"][sym] == cached["splits"][sym], sym


def test_the_symbols_excluded_for_data_quality_really_are_absent(meta):
    """An exclusion that did not take is worse than no exclusion, because the meta then
    describes a fixture that is not the one on disk."""
    ex = meta["gates"]["excluded_for_data_quality"]
    assert ex["count"] == len(ex["by_symbol"])
    assert set(ex["by_symbol"]).isdisjoint(meta["symbols"]), "an excluded symbol is present"
    for sym, problems in ex["by_symbol"].items():
        assert problems, sym
        for p in problems:
            assert p["symbol"] == sym
            assert p.get("why") or p.get("adjusted_ratio") is not None, (sym, p)
    # The cohort breakdown must be published: these failures are NOT random with
    # respect to distress, so hiding them would be the same mistake as hiding a
    # delisted name.
    assert set(ex["cohorts"]) <= {"dead", "alive"}
    assert sum(ex["cohorts"].values()) == ex["count"]


def test_every_hand_verified_large_move_is_classified_corroborated(meta):
    """`DOCUMENTED_LARGE_MOVES` is a CROSS-CHECK on the classifier, not an exemption
    from it — and it earned its keep. KODK's 2020-07-29 loan bar was hand-verified as
    real, the classifier called it unexplained, and the classifier was wrong: it was
    reading dollar volume against the immediately preceding bar, which was already a
    264M-share day because the move started the day before. The baseline is a trailing
    median because this disagreement forced it."""
    by_key = {(c["symbol"], c["date"]): c for c in meta["gates"]["gate_b"]["all_classified_moves"]}
    for (sym, d) in F.DOCUMENTED_LARGE_MOVES:
        c = by_key.get((sym, d))
        assert c is not None, f"{sym} {d} is hand-verified but no longer a >= x4 bar"
        assert c["klass"] == "corroborated", (sym, d, c["klass"])


def test_no_split_coefficient_the_price_series_contradicts_was_applied(meta):
    """The provider's `8. split coefficient` is unreliable in at least three ways, and
    each would put a fabricated jump into the prices: final-bar artefacts on ZERO
    volume (RSPP's 0.32, FMSA's 0.2), coefficients on continuous prices (CHMT's 0.015
    on a close flat at ~15.50, AMRC's 2.0 on a close flat at ~10), and spinoffs
    modelled as splits. Only coefficients the price series corroborates are applied,
    and the rejects are published rather than dropped quietly."""
    unc = meta["gates"]["unconfirmed_splits"]
    assert unc["count"] == len(unc["dropped"])
    assert unc["count"] > 0, "no coefficient was rejected — the check may have stopped running"
    events = json.loads(EVENTS.read_text(encoding="utf-8"))
    for u in unc["dropped"]:
        applied = {e[:10] for e, _r in events["splits"].get(u["symbol"], [])}
        assert u["date"] not in applied, f"{u['symbol']} {u['date']} was rejected AND applied"
        # Small coefficients are never tested, because a 3% stock dividend cannot be
        # distinguished from a 3% session. Anything rejected must be outside that band.
        assert not (1 / F.CONFIRMATION_MIN_RATIO < u["ratio"] < F.CONFIRMATION_MIN_RATIO), u


def test_the_meta_records_its_own_gates_as_clean(meta):
    """The build writes its gate failures into the meta. An empty list there and a
    passing test above should agree; if they ever disagree, the fixture on disk was
    not produced by the code in the tree."""
    assert meta["gates"]["gate_a"]["failures"] == []
    assert meta["gates"]["gate_b"]["failures"] == []
    assert meta["split_adjusted"] is True
    assert meta["split_adjusted_bars"] > 0, "no bar was split-adjusted — implausible at this size"


def test_every_documented_large_move_is_actually_in_the_fixture(closes_by_symbol):
    """A hand-verified entry that no longer corresponds to a bar has stopped doing its
    job as a cross-check, and would go on silently agreeing with nothing."""
    stale = []
    for (sym, d) in F.DOCUMENTED_LARGE_MOVES:
        series = closes_by_symbol.get(sym)
        if not series:
            stale.append((sym, d, "symbol not in fixture"))
            continue
        idx = {dd: i for i, (dd, _c, _v) in enumerate(series)}
        i = idx.get(d)
        if not i:
            stale.append((sym, d, "date not a bar for this symbol"))
            continue
        if series[i][1] / series[i - 1][1] < F.GATE_B_UP_RATIO:
            stale.append((sym, d, "bar no longer moves >= the gate"))
    assert not stale, f"stale DOCUMENTED_LARGE_MOVES entries: {stale}"


def test_moves_across_a_trading_halt_are_reported_rather_than_excused_silently(meta):
    """Halt crossings are exempt from GATE B because a return across a months-long
    suspension is not a one-day return. Exempt is not the same as invisible: each one
    is recorded with its gap, and the per-symbol `max_gap_days` lets a loader find
    every symbol that needs segmenting."""
    halts = meta["gates"]["moves_across_a_trading_halt"]
    assert halts["count"] == len(halts["crossings"])
    for c in halts["crossings"]:
        assert c["gap_days"] > F.HALT_GAP_DAYS
        assert meta["symbols"][c["symbol"]]["max_gap_days"] >= c["gap_days"]
    assert "SEGMENTED" in halts["definition"]
    assert all("max_gap_days" in m for m in meta["symbols"].values())


def test_the_events_sidecar_is_populated_for_both_actions(meta):
    """An EMPTY sidecar is a lie (D48), and a silently empty one is worse: a total
    return computed against zero dividends degenerates to price return without
    saying so."""
    events = json.loads(EVENTS.read_text(encoding="utf-8"))
    assert set(events) == {"dividends", "splits"}
    assert set(events["splits"]) == set(meta["symbols"]), "sidecar and fixture disagree on symbols"
    n_splits = sum(len(v) for v in events["splits"].values())
    n_divs = sum(len(v) for v in events["dividends"].values())
    assert n_splits > 0 and n_divs > 0, f"splits={n_splits} dividends={n_divs}"
    n_reverse = sum(1 for v in events["splits"].values() for _, r in v if r < 1.0)
    assert n_reverse > 0, "no reverse split anywhere — the +1,772% hazard would be untested"


# ===========================================================================
# 2. THE PRE-LIVE SCREEN
# ===========================================================================

def _synthetic(n_screen: int, n_live: int, screen_close: float, screen_vol: float,
               live_close: float, live_vol: float) -> dict:
    """A provider-shaped series whose two windows disagree on purpose."""
    series, day = {}, 0
    from datetime import date, timedelta
    start = date(2012, 1, 2)
    for i in range(n_screen + n_live):
        c, v = (screen_close, screen_vol) if i < n_screen else (live_close, live_vol)
        d = start + timedelta(days=day)
        while d.weekday() >= 5:
            day += 1
            d = start + timedelta(days=day)
        series[d.isoformat()] = {
            "1. open": f"{c}", "2. high": f"{c}", "3. low": f"{c}", "4. close": f"{c}",
            "5. adjusted close": f"{c}", "6. volume": f"{v}",
            "7. dividend amount": "0.0000", "8. split coefficient": "1.0",
        }
        day += 1
    return series


def test_the_screen_reads_the_pre_live_window_and_nothing_after_it():
    """THE test that decides whether this fixture is selection on the outcome.

    Two series, identical in their first `SCREEN_BARS` bars and maximally different
    afterwards: one becomes an illiquid $0.02 husk, the other a $900 momentum name.
    A screen that could see the study window would separate them. This one must not.
    """
    n_s, n_l = F.SCREEN_BARS, F.MIN_LIVE_BARS + 400
    wreck = _synthetic(n_s, n_l, screen_close=40.0, screen_vol=500_000,
                       live_close=0.02, live_vol=100)
    rocket = _synthetic(n_s, n_l, screen_close=40.0, screen_vol=500_000,
                        live_close=900.0, live_vol=50_000_000)

    v_wreck, r_wreck = F.apply_screen(wreck)
    v_rocket, r_rocket = F.apply_screen(rocket)

    assert r_wreck is None and r_rocket is None, (r_wreck, r_rocket)
    # Identical verdicts on every screen-derived number — the live window is invisible.
    for field in ("screen_start", "screen_end", "live_start",
                  "screen_median_close", "screen_median_dollar_volume"):
        assert v_wreck[field] == v_rocket[field], field
    assert v_wreck["screen_median_close"] == 40.0
    assert v_wreck["screen_median_dollar_volume"] == 40.0 * 500_000


def test_a_name_that_is_illiquid_only_in_its_screen_window_is_rejected():
    """The converse, so the test above cannot pass by the screen doing nothing at all.
    The screen window is the ONLY thing that decides, so a name that is thin there and
    enormous afterwards must still fail."""
    late_bloomer = _synthetic(F.SCREEN_BARS, F.MIN_LIVE_BARS + 400,
                              screen_close=40.0, screen_vol=100,      # $4,000/day
                              live_close=40.0, live_vol=50_000_000)   # $2bn/day
    verdict, reason = F.apply_screen(late_bloomer)
    assert verdict is None and "vol" in reason, (verdict, reason)


def test_the_price_floor_sits_on_the_screen_window_so_the_wrecks_survive_it():
    """A price floor over the whole history would delete exactly the cohort this
    fixture is for. Applied to the first year only, a company that traded at $40 in
    year one and $0.02 in year four is RETAINED."""
    verdict, reason = F.apply_screen(_synthetic(
        F.SCREEN_BARS, F.MIN_LIVE_BARS + 400,
        screen_close=40.0, screen_vol=500_000, live_close=0.02, live_vol=100))
    assert reason is None and verdict is not None
    assert verdict["screen_median_close"] >= F.MIN_SCREEN_PRICE_USD


def test_every_symbols_recorded_live_window_starts_after_its_screen_window(meta, closes_by_symbol):
    """The per-symbol claim, checked against the fixture's own bars rather than
    against the selection file that made it."""
    for sym, m in meta["symbols"].items():
        series = closes_by_symbol[sym]
        dates = [d for d, _c, _v in series]
        assert m["screen_end"] < m["live_start"], sym
        assert dates[F.SCREEN_BARS - 1] == m["screen_end"], sym
        assert dates[F.SCREEN_BARS] == m["live_start"], sym
        assert m["n_live_bars"] == len(dates) - F.SCREEN_BARS, sym
        assert m["n_live_bars"] >= F.MIN_LIVE_BARS, sym
    assert meta["screen_is_pre_live"] is True


# ===========================================================================
# 3. THE DEAD COHORT
# ===========================================================================

def test_the_delisted_cohort_is_non_empty_and_above_the_stated_floor(meta):
    """The refusal condition, asserted here as well as enforced in `--build`.

    D141-D144 measured why: on crypto, 67% of the wrecks beat matched exposure against
    45% of the survivors. A short-side universe of survivors deletes the measurement,
    and no caveat repairs it."""
    dead = meta["cohorts"]["dead"]
    total = meta["n_symbols"]
    assert dead > 0, "the delisted cohort is EMPTY — this is not a short-side fixture"
    assert dead / total >= F.MIN_DEAD_SHARE, (
        f"dead cohort {dead}/{total} = {dead/total:.1%}, below the "
        f"{F.MIN_DEAD_SHARE:.0%} floor"
    )
    # And the meta's own count must agree with the per-symbol records it ships.
    counted = sum(1 for m in meta["symbols"].values() if m["cohort"] == "dead")
    assert counted == dead
    assert all(m["delistingDate"] for m in meta["symbols"].values() if m["cohort"] == "dead")


def test_the_dead_names_actually_stop_trading_inside_the_span(meta):
    """A 'delisted' symbol whose bars run to the span end is a mislabel, and a
    mislabel here would silently reintroduce survivorship into the cohort split."""
    span_end = meta["span"]["end"]
    bad = [s for s, m in meta["symbols"].items()
           if m["cohort"] == "dead" and m["last_bar"] >= span_end]
    assert not bad, f"{len(bad)} 'dead' symbols still trading at the span end: {bad[:10]}"


def test_the_roster_refresh_artefact_is_handled_and_not_smoothed_over(meta):
    """`delistingDate` is not always a delisting date.

    **601 of the provider's 9,449 delisted rows carry 2026-08-27**, the day the roster
    was pulled; the next largest single date is 2026-05-28 with 54. Six hundred
    companies did not delist on one Thursday. This test was written because an earlier
    test FAILED on it — eight 'dead' names were still trading at the span end — and the
    finding is pinned rather than papered over.

    Two rules follow, and both are checked: a delisting after the span end means the
    company was listed for the whole span and is `alive` here; a delisting inside the
    span whose bars keep coming for weeks is a provider contradiction and the name is
    dropped."""
    art = meta["roster_refresh_artefact"]
    assert "2026-08-27" in art["finding"]

    for sym in art["reclassified_alive_delisting_after_span_end"]:
        m = meta["symbols"][sym]
        assert m["cohort"] == "alive", sym
        assert m["delistingDate"] > meta["span"]["end"], sym
        assert m["cohort_note"], sym

    dropped = {c["symbol"] for c in art["dropped_provider_contradiction"]}
    assert dropped.isdisjoint(meta["symbols"]), "a contradictory name reached the fixture"

    tol = art["contradiction_tolerance_days"]
    for sym, m in meta["symbols"].items():
        if m["cohort"] != "dead":
            continue
        assert m["delistingDate"] <= meta["span"]["end"], sym
        cutoff = (date.fromisoformat(m["delistingDate"]) + timedelta(days=tol)).isoformat()
        assert m["last_bar"] <= cutoff, (sym, m["delistingDate"], m["last_bar"])


def test_the_dead_cohort_is_spread_across_the_span_not_bunched_at_one_end(meta):
    """A dead cohort that all died in 2024 tests one regime, not a span. This does not
    assert the spread is uniform — the provider's pre-2013 coverage is thin and the
    meta says so — only that more than one era is represented."""
    years = meta["delistings_by_year"]
    assert len(years) >= 8, f"delistings span only {len(years)} years: {years}"
    assert min(years) <= "2015" and max(years) >= "2022", years


def test_the_meta_carries_an_explicit_survivorship_bias_statement(meta):
    """Not a style check. The statement names three residual biases that the
    construction does NOT repair, and a reader who takes a base rate off this fixture
    without seeing them will be wrong. If it goes missing, that is a real regression."""
    s = meta["SURVIVORSHIP_BIAS_STATEMENT"]
    assert isinstance(s, str) and len(s) > 800
    for phrase in ("STILL NOT FREE OF", "UNDER-SAMPLED", "delistingDate",
                   "not a point-in-time reconstruction"):
        assert phrase in s, phrase
    assert meta["status_definition"].count("HINDSIGHT BY CONSTRUCTION") == 1


# ===========================================================================
# 4. THE PANEL IS RAGGED, AND SAYS SO
# ===========================================================================

def test_the_panel_is_ragged_and_the_meta_says_a_loader_is_required(meta, closes_by_symbol):
    """Raggedness is the DESIGN, not a defect: a rectangular panel needs every symbol
    on every date, which is exactly what deletes the delisted names (D245 AMENDMENT 1).
    `run_macd_ladder.load_panel` refuses a ragged panel by design, so the meta has to
    say a downstream loader is required and what it must do."""
    counts = {len(v) for v in closes_by_symbol.values()}
    assert len(counts) > 1, "the panel is rectangular — dead names have been deleted"
    assert meta["panel_shape"] == "RAGGED"
    note = meta["panel_note"]
    for phrase in ("load_panel", "REFUSES", "presence mask", "forward-fill",
                   "FORCED EXIT", "live_start"):
        assert phrase in note, phrase


def test_load_panel_really_does_refuse_this_fixture():
    """The meta's claim about `run_macd_ladder.load_panel`, verified against the
    source rather than asserted. A comment that drifts out of date is a comment that
    misleads the next person to try it."""
    src = (REPO / "scripts" / "run_macd_ladder.py").read_text(encoding="utf-8")
    assert 'raise ValueError(f"symbols have different bar counts' in src


# ===========================================================================
# 5. THE EXCLUSION RULE
# ===========================================================================

@pytest.mark.parametrize("sym", ["AA-W", "AAC-U", "-P-HIZ", "BRK-A", "ABCDW", "ABCDU", "ABCDR"])
def test_non_common_stock_tickers_are_excluded(sym):
    assert not F._is_common_stock_ticker(sym)


@pytest.mark.parametrize("sym", ["AAPL", "A", "GOOGL", "SHLDQ", "BBBYQ", "ABCDQ"])
def test_common_stock_tickers_including_bankrupt_ones_are_kept(sym):
    """The 'Q' fifth letter marks an issuer IN BANKRUPTCY. It is common stock and it
    is the single most relevant cohort on the tape for a short book. Excluding it
    would be the survivorship bias this fixture exists to avoid, wearing a tidiness
    costume."""
    assert F._is_common_stock_ticker(sym)


def test_no_excluded_ticker_reached_the_fixture(meta):
    bad = [s for s in meta["symbols"] if not F._is_common_stock_ticker(s)]
    assert not bad, bad
    assert "fifth character is W, U or R" in meta["universe_rule"]["exclusion_rule"]


# ===========================================================================
# 6. THE KEY IS NOWHERE
# ===========================================================================

def _the_key() -> str | None:
    k = os.environ.get("ALPHAVANTAGE_API_KEY")
    if k:
        return k.strip()
    if F.KEY_FILE.exists():
        return F.KEY_FILE.read_text(encoding="utf-8").strip()
    return None


def test_the_api_key_appears_in_no_artifact_and_in_no_source():
    """Alpha Vantage's key IS the account, and its terms keep this repository private.
    A key in a committed fixture is a key leaked, and it would be leaked in the one
    class of file this project deliberately commits."""
    key = _the_key()
    if not key or len(key) < 8:
        pytest.skip("no key available on this machine to scan for")
    targets = [SCRIPT, Path(__file__), REPO / "docs" / "alpha_vantage_api.md"]
    targets += [p for p in (META, EVENTS, F.POOL, F.SELECTION) if p.exists()]
    targets += sorted((REPO / "docs" / "decisions").glob("D252-*.md"))
    for p in targets:
        assert key not in p.read_text(encoding="utf-8", errors="replace"), p
    if FIXTURE.exists():
        with gzip.open(FIXTURE, "rt", errors="replace") as f:
            assert not any(key in line for line in f), FIXTURE


def test_the_fetcher_never_puts_a_url_into_an_exception_or_a_log():
    """`urllib` puts the full request URL — key and all — into `HTTPError.__str__` on
    some paths, and a traceback is an artifact too. `_get` re-raises with the URL
    stripped, and the only thing `main` prints about the key is where it was read
    from."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "[url redacted]" in src
    assert "print(f\"key       {src}\")" in src  # the SOURCE, never the value
    # No literal key material in the file: nothing that looks like an AV key constant.
    assert "apikey=" not in src.replace('"apikey": key', "")


def test_the_gzip_header_carries_no_timestamp_so_a_rebuild_is_a_content_diff(requires_panel):
    """`gzip` stamps the current time into bytes 4-7 of its header, so an otherwise
    identical rebuild would show as a whole-file diff — and a diff that always appears
    is a diff that stops being read. The point of committing a fixture is that changing
    it is VISIBLE (D70/D24). Same pin `csv_fixture` carries."""
    # The only test in this file that touches the panel WITHOUT going through
    # `closes_by_symbol`, so it is the only one that still carries its own guard.
    requires_panel(FIXTURE)
    with open(FIXTURE, "rb") as f:
        header = f.read(10)
    assert header[:2] == b"\x1f\x8b", "not a gzip file"
    assert header[4:8] == b"\x00\x00\x00\x00", (
        f"gzip MTIME is {int.from_bytes(header[4:8], 'little')}, not 0 — rebuilds will "
        "produce spurious whole-file diffs"
    )


def test_the_raw_cache_is_not_committed():
    """D191: cache the raw, commit the derived."""
    ignore = (REPO / ".gitignore").read_text(encoding="utf-8")
    assert "data/raw/alphavantage/" in ignore
    assert F.CACHE.is_relative_to(REPO / "data" / "raw")
