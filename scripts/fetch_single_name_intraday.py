"""D264 WP1 -- 15-minute bars for the eight-name single-stock sample.

    uv run python scripts/fetch_single_name_intraday.py --plan      # no network
    uv run python scripts/fetch_single_name_intraday.py --actions   # splits+dividends
    uv run python scripts/fetch_single_name_intraday.py --fetch     # the long job
    uv run python scripts/fetch_single_name_intraday.py --build     # cache -> fixture

NOTHING IN THIS FILE RUNS A STRATEGY, SCORES A CELL OR PROPOSES A RULE.

=========================================================================
PROVENANCE OF THE EIGHT SYMBOLS -- they were not chosen here
=========================================================================

`scripts/select_single_name_intraday.py` fixed the rule and ran it ONCE against
the committed DAILY fixture over 2013-01-02 .. 2017-12-29, a window DISJOINT
from the 2018-2026 test span. Its output is frozen below as a literal tuple so
the sample cannot drift. `data/single_name_intraday_selection.json` carries the
full ranked pool for audit.

  LOW  stratum   PG 14.1%  LMT 15.8%  PM 16.1%  MO 16.2%   (annualised vol)
  HIGH stratum   RH 53.7%  YELP 56.2%  SM 64.8%  CLF 78.0%

A 5.5x volatility spread is the DESIGN: FINDINGS 1b says a short pays a variance
tax scaling with sigma^2, FINDINGS 2 says idiosyncratic variance is where a short
edge lives, and those two pull in opposite directions. Spanning the axis is how
the screen finds out which one binds.

=========================================================================
THE SURVIVORSHIP LIMIT -- a provider fact, measured, not a preference
=========================================================================

PROBED 2026-09-01, five calls: `TIME_SERIES_INTRADAY` serves NOTHING for a
delisted ticker.

  AAPL 2022-06    546 bars, 21 sessions, 26.0/session      <- control, works
  TWTR 2022-06    155 bytes, `Invalid API call`
  FRC  2023-03    155 bytes, `Invalid API call`
  SIVB 2023-02    155 bytes, `Invalid API call`
  AABA 2019-06    155 bytes, `Invalid API call`

`TIME_SERIES_DAILY_ADJUSTED` DOES serve dead names -- that is how D252 built a
35.7%-dead daily fixture. The intraday endpoint does not, on this tier.

SIZE OF THE HOLE: 496 of the 1,192 names trading in 2013-2017 are not survivors.
41.6% of the cohort is unreachable at this frequency.

The bias and its DIRECTION are declared in the study's pre-registration, not
here. This file states the fact and stops.

=========================================================================
REGULAR HOURS ONLY, and why the extended session is not an option
=========================================================================

26 bars per session, 09:30..15:45 stamped at the interval OPEN. This matches
`etf_intraday_15m_panel.csv.gz`, which is what D247 ran, so the two results are
directly comparable rather than merely adjacent.

`fetch_etf_intraday.py --build --extended` REFUSES to write a wide extended
fixture, and its reasons apply here with more force: extended-hours bars exist
only where something traded, so bar counts become liquidity-correlated -- and
this sample deliberately spans a 5.5x liquidity/volatility range. That would put
the axis under test straight into the sampling grid.

Bars are FETCHED with extended_hours=true because the request cost is identical
and bars cannot be recovered later without re-fetching; the BUILD keeps 09:30
..15:45. Same trade the ETF fetcher makes, same reason.

=========================================================================
WHY SPLITS ARE LOAD-BEARING HERE AND WERE MERELY IMPORTANT THERE
=========================================================================

The ETF cache held twelve unadjusted splits in 3.2M bars. Single names split far
more often, and `--build` REFUSES to run without the sidecar. Beyond that, this
builder adds a gate the ETF one does not have, because PICKUP.md records the
failure it is for:

  XLF closed 23.63 on 2016-09-16 and opened 19.30, then HELD there all day on
  5.9M shares -- the XLRE spin-off. Alpha Vantage's SPLITS reports ZERO splits
  for XLF. SPLITS + DIVIDENDS between them do not cover spin-offs.

So `--build` reports every residual session-boundary step above 15% (D226's
threshold, unchanged) and classifies it by D252's test -- does it revert, does it
persist at volume, or is it corroborated -- rather than silently adjusting or
silently keeping it.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import importlib.util
import io
import json
import sys
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# The ETF fetcher's helpers are reused rather than copied. Every one of these
# resolves only globals that are IDENTICAL for this study -- same API host, same
# 15min interval, same raw cache tree, same key file, same timeout -- so the
# reuse is safe. The constants that DIFFER (symbols, span, fixture triple) are
# owned here and never reach back into that module. D212 is binding: do not
# reimplement a tested helper.
E = _load("d264_etf_intraday", "fetch_etf_intraday.py")

api_key = E.api_key
months = E.months
slice_path = E.slice_path
fetch_slice = E.fetch_slice
fetch_action = E.fetch_action
series_of = E.series_of
split_factor_at = E.split_factor_at
in_session = E.in_session
_half_days = E._half_days
RateLimiter = E.RateLimiter
MIN_INTERVAL = E.MIN_INTERVAL
REQUESTS_PER_MIN = E.REQUESTS_PER_MIN
MAX_CONSECUTIVE_FAILURES = E.MAX_CONSECUTIVE_FAILURES
INTERVAL = E.INTERVAL
TZ = E.TZ
CACHE = E.CACHE

# --------------------------------------------------------------------------
# CONSTANTS OWNED HERE. Nothing below is read from the ETF module.
# --------------------------------------------------------------------------

# Frozen output of select_single_name_intraday.py, run once on 2013-2017.
LOW_VOL = ("PG", "LMT", "PM", "MO")
HIGH_VOL = ("CLF", "SM", "YELP", "RH")
SYMBOLS = LOW_VOL + HIGH_VOL
STRATUM = {**{s: "low" for s in LOW_VOL}, **{s: "high" for s in HIGH_VOL}}

# D247's exact span, so the ETF result is a comparison and not an analogy.
START_MONTH = "2018-01"
END_MONTH = "2026-08"

RTH_SESSION_BARS = 26

FIX = REPO / "data" / "fixtures"
FIXTURE = FIX / "single_name_intraday_15m_raw.csv.gz"
META = FIX / "single_name_intraday_15m_raw.meta.json"
EVENTS = FIX / "single_name_intraday_15m_raw_events.json"

# D226's threshold, unchanged. A residual session-boundary step above this is
# REPORTED and classified, never silently adjusted.
STEP_THRESHOLD = 0.15


def do_plan() -> int:
    plan = [(s, m) for s in SYMBOLS for m in months(START_MONTH, END_MONTH)]
    cached = sum(1 for s, m in plan if slice_path(s, m).exists())
    ms = months(START_MONTH, END_MONTH)
    print(f"symbols   {len(SYMBOLS)}  ({' '.join(SYMBOLS)})")
    print(f"  low vol   {' '.join(LOW_VOL)}")
    print(f"  high vol  {' '.join(HIGH_VOL)}")
    print(f"months    {len(ms)}  ({ms[0]} .. {ms[-1]})")
    print(f"slices    {len(plan):,}   cached {cached:,}   remaining {len(plan) - cached:,}")
    print(f"pacing    {REQUESTS_PER_MIN}/min (tier limit 75)")
    print(f"ETA       {(len(plan) - cached) * MIN_INTERVAL / 60:.1f} minutes")
    print(f"actions   {2 * len(SYMBOLS)} further calls (SPLITS + DIVIDENDS)")
    print(f"cache     {CACHE}  (NOT committed -- D191)")
    print(f"fixture   {FIXTURE.name}  (committed)")
    return 0


def do_fetch(limit: int | None) -> int:
    import time

    key = api_key()
    limiter = RateLimiter(MIN_INTERVAL)
    plan = [(s, m) for s in SYMBOLS for m in months(START_MONTH, END_MONTH)]
    todo = [(s, m) for s, m in plan if not slice_path(s, m).exists()]
    cached = len(plan) - len(todo)
    if limit:
        todo = todo[:limit]

    print(f"{len(plan):,} slices planned, {cached:,} already cached, "
          f"{len(todo):,} to fetch this run")
    if not todo:
        print("nothing to do -- cache is complete")
        return 0
    print(f"pacing at {REQUESTS_PER_MIN}/min, ETA {len(todo) * MIN_INTERVAL / 60:.1f} min\n")

    fetched = empty = consecutive = 0
    t0 = time.monotonic()
    for i, (symbol, month) in enumerate(todo, 1):
        path = slice_path(symbol, month)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            payload = fetch_slice(symbol, month, key, limiter)
        except (RuntimeError, urllib.error.URLError, TimeoutError, OSError) as exc:
            consecutive += 1
            msg = str(exc)[:140]
            if any(w in msg.lower() for w in ("rate", "frequency", "note")):
                back = min(60.0 * consecutive, 300.0)
                print(f"  [{i}/{len(todo)}] {symbol} {month}: THROTTLED -- "
                      f"backing off {back:.0f}s\n      {msg}")
                time.sleep(back)
            else:
                print(f"  [{i}/{len(todo)}] {symbol} {month}: {msg}")
            if consecutive >= MAX_CONSECUTIVE_FAILURES:
                print(f"\nSTOPPING after {consecutive} consecutive failures. "
                      f"Re-run to resume; cached slices are kept.")
                return 1
            continue

        consecutive = 0
        n = len(series_of(payload))
        if n == 0:
            empty += 1
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            json.dump(payload, fh, separators=(",", ":"))
        fetched += 1
        if i % 50 == 0 or i == len(todo):
            done = time.monotonic() - t0
            rate = i / done * 60 if done else 0
            print(f"  [{i:,}/{len(todo):,}] {symbol} {month}  {n:,} bars  "
                  f"| {rate:.0f}/min | {(len(todo) - i) * MIN_INTERVAL / 60:.1f} min left")

    print(f"\ndone: {fetched:,} slices cached ({empty:,} empty)")
    return 0


def do_actions() -> int:
    """SPLITS and DIVIDENDS -> the events sidecar. 16 free calls.

    `--build` REFUSES to run without this. Single names split far more often than
    the ETF universe did, and the fixture is as-traded."""
    key = api_key()
    limiter = RateLimiter(MIN_INTERVAL)
    dividends: dict[str, list] = {}
    splits: dict[str, list] = {}

    print(f"fetching SPLITS and DIVIDENDS for {len(SYMBOLS)} symbols "
          f"({2 * len(SYMBOLS)} calls)\n")
    for i, symbol in enumerate(SYMBOLS, 1):
        try:
            raw_splits = fetch_action("SPLITS", symbol, key, limiter)
            raw_divs = fetch_action("DIVIDENDS", symbol, key, limiter)
        except (RuntimeError, urllib.error.URLError, TimeoutError, OSError) as exc:
            print(f"  [{i}/{len(SYMBOLS)}] {symbol}: FAILED -- {str(exc)[:140]}")
            return 1
        splits[symbol] = sorted(
            [f"{d['effective_date']}T00:00:00", float(d["split_factor"])]
            for d in raw_splits
            if START_MONTH <= d["effective_date"][:7] <= END_MONTH
        )
        dividends[symbol] = sorted(
            [f"{d['ex_dividend_date']}T00:00:00", float(d["amount"])]
            for d in raw_divs
            if START_MONTH <= d["ex_dividend_date"][:7] <= END_MONTH
            and d["amount"] not in ("None", "")
        )
        print(f"  [{i}/{len(SYMBOLS)}] {symbol:5s} {len(dividends[symbol]):3d} dividends"
              + (f"   SPLITS {splits[symbol]}" if splits[symbol] else ""))

    EVENTS.write_text(json.dumps({"dividends": dividends, "splits": splits},
                                 indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"\nwrote {EVENTS.name}: {sum(len(v) for v in splits.values())} splits, "
          f"{sum(len(v) for v in dividends.values())} dividends")
    return 0


def _session_counts() -> dict:
    counts: dict[tuple[str, str], int] = {}
    for symbol in SYMBOLS:
        for month in months(START_MONTH, END_MONTH):
            path = slice_path(symbol, month)
            if not path.exists():
                continue
            with gzip.open(path, "rt", encoding="utf-8") as fh:
                series = series_of(json.load(fh))
            for stamp in series:
                if not in_session(stamp, True):
                    continue
                k = (symbol, stamp[:10])
                counts[k] = counts.get(k, 0) + 1
    return counts


def do_build() -> int:
    if not EVENTS.exists():
        raise SystemExit(
            "REFUSING TO BUILD AN UNADJUSTED FIXTURE.\n"
            "The events sidecar is missing. This fixture is as-traded, and single\n"
            "names split. Run `--actions` first."
        )
    all_splits = {s: [(d, float(r)) for d, r in v]
                  for s, v in json.loads(EVENTS.read_text())["splits"].items()}
    n_split_events = sum(len(v) for v in all_splits.values())

    counts = _session_counts()
    if not counts:
        raise SystemExit("no cached slices; run `--fetch` first")
    half_days = _half_days(counts, RTH_SESSION_BARS)

    short_sessions: dict[str, int] = {}
    missing_bars: dict[str, int] = {}
    total_sessions: dict[str, int] = {}
    for (sym, day), n in counts.items():
        if day in half_days:
            continue
        total_sessions[sym] = total_sessions.get(sym, 0) + 1
        if n != RTH_SESSION_BARS:
            short_sessions[sym] = short_sessions.get(sym, 0) + 1
            missing_bars[sym] = missing_bars.get(sym, 0) + (RTH_SESSION_BARS - n)

    rows = zero_volume = dropped_half_day_bars = adjusted_bars = 0
    per_symbol: dict[str, int] = {}
    first: dict[str, str] = {}
    last: dict[str, str] = {}
    prev_close: dict[str, float] = {}
    prev_stamp: dict[str, str] = {}
    max_move = {"symbol": None, "timestamp": None, "move": 0.0}
    # Session-boundary steps above D226's 15%. Overnight gaps, so they are the
    # place a spin-off hides -- SPLITS does not report one (PICKUP.md, XLF/XLRE).
    steps: list[dict] = []

    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    with open(FIXTURE, "wb") as _raw, \
            gzip.GzipFile(filename="", fileobj=_raw, mode="wb", mtime=0) as _gz, \
            io.TextIOWrapper(_gz, encoding="utf-8", newline="") as out:
        w = csv.writer(out)
        w.writerow(["timestamp", "symbol", "open", "high", "low", "close", "volume"])
        for symbol in SYMBOLS:
            for month in months(START_MONTH, END_MONTH):
                path = slice_path(symbol, month)
                if not path.exists():
                    continue
                with gzip.open(path, "rt", encoding="utf-8") as fh:
                    series = series_of(json.load(fh))
                for stamp in sorted(series):
                    if not in_session(stamp, True):
                        continue
                    if stamp[:10] in half_days:
                        dropped_half_day_bars += 1
                        continue
                    b = series[stamp]
                    f = split_factor_at(stamp, all_splits.get(symbol, []))
                    if f != 1.0:
                        adjusted_bars += 1
                    o = float(b["1. open"]) / f
                    h = float(b["2. high"]) / f
                    lo = float(b["3. low"]) / f
                    c = float(b["4. close"]) / f
                    v = float(b["5. volume"]) * f
                    if v == 0.0:
                        zero_volume += 1
                    pc = prev_close.get(symbol)
                    if pc:
                        move = abs(c / pc - 1.0)
                        if move > max_move["move"]:
                            max_move = {"symbol": symbol, "timestamp": stamp, "move": move}
                        crosses_session = prev_stamp[symbol][:10] != stamp[:10]
                        if crosses_session and move > STEP_THRESHOLD:
                            steps.append({"symbol": symbol,
                                          "from": prev_stamp[symbol], "to": stamp,
                                          "step": c / pc - 1.0,
                                          "prev_close": pc, "close": c,
                                          "volume": v})
                    prev_close[symbol] = c
                    prev_stamp[symbol] = stamp
                    w.writerow([stamp, symbol, f"{o:.6f}", f"{h:.6f}",
                                f"{lo:.6f}", f"{c:.6f}", f"{v:.2f}"])
                    rows += 1
                    per_symbol[symbol] = per_symbol.get(symbol, 0) + 1
                    first.setdefault(symbol, stamp)
                    last[symbol] = stamp

    meta = {
        "fixture": FIXTURE.name,
        "purpose": ("15-minute bars for the eight-name stratified single-stock "
                    "sample. DATA ONLY -- no strategy, no cell, no rule."),
        "symbols_requested": list(SYMBOLS),
        "symbols_included": sorted(per_symbol),
        "symbols_excluded": [s for s in SYMBOLS if s not in per_symbol],
        "strata": STRATUM,
        "selection": {
            "artefact": "data/single_name_intraday_selection.json",
            "script": "scripts/select_single_name_intraday.py",
            "window": ["2013-01-02", "2017-12-29"],
            "note": ("the selection window is DISJOINT from the test span, so no "
                     "statistic that picked a name has seen a bar this fixture holds"),
        },
        "SURVIVORSHIP_BIAS_STATEMENT": (
            "SURVIVOR-ONLY, AND NOT BY CHOICE. Probed 2026-09-01: "
            "TIME_SERIES_INTRADAY returns `Invalid API call` (155 bytes) for every "
            "delisted ticker tried -- TWTR, FRC, SIVB, AABA -- against AAPL's clean "
            "546 bars. TIME_SERIES_DAILY_ADJUSTED does serve dead names, which is "
            "how D252 built a 35.7%-dead DAILY fixture; the intraday endpoint does "
            "not, on this tier. 496 of the 1,192 names trading in 2013-2017 are not "
            "survivors, so 41.6% of the cohort is unreachable at this frequency. "
            "D252 holds that survivorship is not a caveat for a short book but the "
            "whole measurement. The direction of the bias and what it does and does "
            "not license are stated in the study's pre-registration."
        ),
        "start": START_MONTH, "end": END_MONTH, "interval": INTERVAL,
        "session": "regular_hours_09:30-15:45",
        "bars_per_full_session": RTH_SESSION_BARS,
        "bar_boundary": ("timestamps mark the interval's OPEN, so a bar stamped t "
                         "covers [t, t+15m) and is not complete until t+15m"),
        "timezone": TZ,
        "source": ("Alpha Vantage TIME_SERIES_INTRADAY, outputsize=full, "
                   "month=YYYY-MM, adjusted=false, extended_hours=true at fetch; "
                   "BUILT regular-hours-only. adjusted=false because adjusted "
                   "prices are BACK-adjusted and drift as dividends are paid, "
                   "breaking D24's immutable-snapshot requirement."),
        "split_adjusted": True,
        "split_events_applied": n_split_events,
        "split_adjusted_bars": adjusted_bars,
        "splits_by_symbol": {s: v for s, v in all_splits.items() if v},
        "largest_residual_bar_move": max_move,
        "session_boundary_steps_over_threshold": steps,
        "step_threshold": STEP_THRESHOLD,
        "step_policy": ("D226's 15% threshold, unchanged. A step above it is "
                        "REPORTED and classified by D252's test -- reverts (bad "
                        "print), persists at volume (corporate action), or is "
                        "corroborated (real) -- never silently adjusted. "
                        "SPLITS+DIVIDENDS do not cover spin-offs: XLF's XLRE "
                        "spin-off is a -18.3% step Alpha Vantage reports as zero "
                        "splits (PICKUP.md)."),
        "half_days_dropped": sorted(half_days),
        "half_day_bars_dropped": dropped_half_day_bars,
        "half_day_policy": ("US early closes DERIVED, not hardcoded: a session "
                            "where at least half the sample is short. Dropped at "
                            "every symbol so the calendar is uniform."),
        "incomplete_sessions_excluding_half_days": sum(short_sessions.values()),
        "incomplete_session_rate": (sum(short_sessions.values()) / sum(total_sessions.values())
                                    if total_sessions else 0.0),
        "missing_bars_excluding_half_days": sum(missing_bars.values()),
        "per_symbol_short_sessions": {
            s: {"short_sessions": n, "rate": n / total_sessions[s],
                "bars_missing": missing_bars.get(s, 0)}
            for s, n in sorted(short_sessions.items(), key=lambda kv: -kv[1])},
        "rows": rows,
        "bars_per_symbol": per_symbol,
        "first_bar": first, "last_bar": last,
        "zero_volume_bars": zero_volume,
        "zero_volume_rate": zero_volume / rows if rows else 0.0,
        "empty_bar_disclosure": ("D192 requires any intraday study on a new "
                                 "universe to measure and report its own empty-bar "
                                 "rate; it must be quoted in the pre-registration."),
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    META.write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")

    print(f"wrote {FIXTURE.name}: {rows:,} rows, {FIXTURE.stat().st_size / 1e6:.1f} MB")
    print(f"  symbols       {len(per_symbol)}/{len(SYMBOLS)}")
    for s in SYMBOLS:
        n = per_symbol.get(s, 0)
        print(f"    {s:5s} {STRATUM[s]:4s} {n:8,} bars  "
              f"{first.get(s, '-')[:10]} .. {last.get(s, '-')[:10]}  "
              f"short {short_sessions.get(s, 0):4d}/{total_sessions.get(s, 0):4d}")
    print(f"  half-days     {len(half_days)} dropped ({dropped_half_day_bars:,} bars)")
    print(f"  incomplete    {sum(short_sessions.values()):,} sessions "
          f"({meta['incomplete_session_rate'] * 100:.3f}%), "
          f"{sum(missing_bars.values()):,} bars missing")
    print(f"  zero-volume   {zero_volume:,} ({meta['zero_volume_rate'] * 100:.4f}%)")
    print(f"  splits        {n_split_events} events -> {adjusted_bars:,} bars")
    print(f"  largest move  {max_move['move'] * 100:.2f}%  "
          f"({max_move['symbol']} {max_move['timestamp']})")

    # ---- GATES ----
    ok = True
    if steps:
        print(f"\n  {len(steps)} SESSION-BOUNDARY STEP(S) OVER "
              f"{STEP_THRESHOLD:.0%} -- CLASSIFY EACH BEFORE USE:")
        for s in steps:
            print(f"    {s['symbol']:5s} {s['from'][:10]} -> {s['to'][:10]}  "
                  f"{s['step'] * 100:+7.2f}%   {s['prev_close']:.2f} -> {s['close']:.2f}")
        print("    Persisting at volume => corporate action the sidecar missed.")
        print("    Reverting            => bad print.")
        print("    Corroborated         => real, and the fixture keeps it.")
    if rows and zero_volume / rows > 0.05:
        print("  GATE FAIL: zero-volume rate above 5% (D192)")
        ok = False
    if meta["incomplete_session_rate"] > 0.05:
        print("  GATE FAIL: incomplete-session rate above 5%")
        ok = False
    missing = [s for s in SYMBOLS if s not in per_symbol]
    if missing:
        print(f"  GATE FAIL: no bars for {missing}")
        ok = False
    print("\n  GATES: " + ("PASS" if ok else "FAIL -- fixture written, DO NOT USE"))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--plan", action="store_true", help="cost only, no network")
    ap.add_argument("--fetch", action="store_true", help="the long job, resumable")
    ap.add_argument("--actions", action="store_true", help="SPLITS + DIVIDENDS sidecar")
    ap.add_argument("--build", action="store_true", help="cache -> committed fixture")
    ap.add_argument("--limit", type=int, default=None, help="cap slices this run")
    a = ap.parse_args()
    if a.plan:
        return do_plan()
    if a.actions:
        return do_actions()
    if a.fetch:
        return do_fetch(a.limit)
    if a.build:
        return do_build()
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
