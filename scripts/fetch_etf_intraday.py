"""One-time (manual, NETWORK) fetch: 15-minute bars for the 57-ETF universe.

    uv run python scripts/fetch_etf_intraday.py --plan          # no network, just the cost
    uv run python scripts/fetch_etf_intraday.py --fetch         # the long job, resumable
    uv run python scripts/fetch_etf_intraday.py --build         # cache -> committed fixture

**Everything downstream of this script is offline and deterministic** — the same
contract every other fetcher in this repo carries (D24: the engine reads snapshots,
never live fetches).

WHY ALPHA VANTAGE AND NOT YFINANCE
----------------------------------
yfinance serves 60 days of 15m data (D160). Impulse MACD at (136, 36) needs 4,049
bars of warm-up alone, so 60 days is short by a factor of three BEFORE the strategy
starts. Alpha Vantage's `TIME_SERIES_INTRADAY` takes `month=YYYY-MM` with
`outputsize=full` and serves any month back to 2000-01, one month per request.

WHAT WAS MEASURED BEFORE COMMITTING TO THE BACKFILL
---------------------------------------------------
Four probe calls on SPY/2024-01 settled what the documentation does not state:

  volume       CONSOLIDATED. 66,595,182 shares median session, against a ~70-90M
               consolidated ADV. Not a single-venue sample. THE STUDY IS VIABLE.
  timezone     stated explicitly in the payload as `US/Eastern`
  timestamps   mark the interval's OPEN (first RTH bar 09:30, last 15:45), so a bar
               stamped t covers [t, t+15m) and is NOT COMPLETE until t+15m
  bars/session 26 at RTH (390 min exactly), 65 with extended hours (04:00-20:00)
  errors       HTTP 200 with {"Error Message": ...} -- validate STRUCTURALLY

`adjusted=false` is used deliberately. Adjusted prices are BACK-adjusted and drift
every time a dividend is paid, which breaks D24's immutable-snapshot requirement;
as-traded values never change. (Note: volume is identical either way on this
endpoint -- measured, ratio exactly 1.000000 -- so the reason is immutability, not
volume distortion.) This also matches the daily fixture's D75 frame.

`extended_hours=true` is used to FETCH the superset — the request cost is identical
and bars cannot be recovered later without re-fetching 6,000 requests — but the
fixture is BUILT regular-hours-only, and that is not a preference. Measured:

  AGG 2018-08, extended hours : 652 bars / 23 sessions, 27-35 per session,
                                07:00-18:30                        -> RAGGED
  AGG 2018-08, regular hours  : 598 bars / 23 sessions, exactly 26 every
                                session                            -> UNIFORM

Extended-hours bars only exist where something traded, so a liquid ETF (SPY:
04:00-20:00, 65 slots) gets far more of them than an illiquid one (AGG: 07:00-18:30
and sparse). **That is a liquidity-correlated difference in bar counts, and this is
a VOLUME study** — it would inject exactly the quantity under test into the sampling
grid. Regular hours give a flat 26 bars per session for every symbol, which also
sidesteps the completeness problem D161 solves for crypto and cannot solve for a
390-minute equity session.

BEING A GOOD CITIZEN — the user asked for this explicitly
---------------------------------------------------------
  * one call per (symbol, month), paced under the tier limit with margin
  * every slice CACHED to disk; a cached slice is NEVER re-fetched, so an
    interrupted run resumes instead of starting over
  * exponential backoff on a rate-limit response, and a hard stop after
    consecutive failures rather than a retry loop
  * the raw cache is NOT committed (D191's precedent for large archives, same as
    the Binance 1m base); only the derived fixture is
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

API = "https://www.alphavantage.co/query"
KEY_FILE = Path.home() / ".config" / "alphavantage" / "key"
CACHE = REPO / "data" / "raw" / "alphavantage"
FIXTURE = REPO / "data" / "fixtures" / "etf_intraday_15m_raw.csv.gz"
META = REPO / "data" / "fixtures" / "etf_intraday_15m_raw.meta.json"
EVENTS = REPO / "data" / "fixtures" / "etf_intraday_15m_raw_events.json"

SYMBOLS = (
    "AGG", "DIA", "EEM", "EFA", "EWA", "EWC", "EWG", "EWH", "EWJ", "EWL",
    "EWQ", "EWT", "EWU", "EWY", "EWZ", "FXI", "GDX", "GDXJ", "GLD", "HYG",
    "IBB", "IEF", "ITB", "IWM", "IYR", "IYT", "KBE", "KRE", "LQD", "MDY",
    "OIH", "QQQ", "SHY", "SLV", "SMH", "SPY", "TIP", "TLT", "UNG", "USO",
    "VIG", "VNQ", "VYM", "XBI", "XHB", "XLB", "XLE", "XLF", "XLI", "XLK",
    "XLP", "XLU", "XLV", "XLY", "XME", "XOP", "XRT",
)

INTERVAL = "15min"
START_MONTH = "2018-01"  # matches the crypto fixture's span, 2018-02 onward
END_MONTH = "2026-08"

# The $49.99/mo tier is 75 requests/minute with no daily cap. Pace under it with
# margin: a fetcher that trips the limit and backs off is slower than one that
# never trips it, and it is ruder.
REQUESTS_PER_MIN = 66
MIN_INTERVAL = 60.0 / REQUESTS_PER_MIN
MAX_CONSECUTIVE_FAILURES = 5
TIMEOUT = 90

TZ = "US/Eastern"
FULL_SESSION_BARS = 26  # 09:30..15:45 inclusive = 390 minutes


def api_key() -> str:
    """Env first, then the file OUTSIDE the repo. The key is never logged."""
    key = os.environ.get("ALPHAVANTAGE_API_KEY")
    if key:
        return key.strip()
    if KEY_FILE.exists():
        return KEY_FILE.read_text(encoding="utf-8").strip()
    raise SystemExit(
        f"No API key. Set ALPHAVANTAGE_API_KEY or create {KEY_FILE}."
    )


def months(start: str, end: str) -> list[str]:
    y, m = (int(x) for x in start.split("-"))
    ey, em = (int(x) for x in end.split("-"))
    out = []
    while (y, m) <= (ey, em):
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def slice_path(symbol: str, month: str) -> Path:
    return CACHE / INTERVAL / symbol / f"{month}.json.gz"


class RateLimiter:
    """Sleeps so calls never exceed the tier ceiling. Not a token bucket — a plain
    floor on the gap between requests, which is the conservative choice."""

    def __init__(self, min_interval: float) -> None:
        self.min_interval = min_interval
        self.last = 0.0

    def wait(self) -> None:
        gap = time.monotonic() - self.last
        if gap < self.min_interval:
            time.sleep(self.min_interval - gap)
        self.last = time.monotonic()


def fetch_slice(symbol: str, month: str, key: str, limiter: RateLimiter) -> dict:
    """One (symbol, month). Returns the parsed payload or raises.

    Alpha Vantage returns HTTP 200 on errors, so success is decided STRUCTURALLY:
    a payload without a `Time Series (...)` key is a failure however healthy the
    status line looks. Writing an error body into a fixture is the failure mode
    this guards."""
    params = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": symbol,
        "interval": INTERVAL,
        "month": month,
        "outputsize": "full",  # MANDATORY with `month`: the default returns 100 bars
        "adjusted": "false",
        "extended_hours": "true",
        "datatype": "json",
        "apikey": key,
    }
    limiter.wait()
    url = f"{API}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
        payload = json.loads(r.read().decode("utf-8", errors="replace"))

    for flag in ("Error Message", "Note", "Information"):
        if flag in payload:
            raise RuntimeError(f"{flag}: {str(payload[flag])[:200]}")
    if not any(k.lower().startswith("time series") for k in payload):
        raise RuntimeError(f"no time series in payload; keys={list(payload)}")
    return payload


def series_of(payload: dict) -> dict:
    for k, v in payload.items():
        if k.lower().startswith("time series"):
            return v
    return {}


def do_fetch(limit: int | None) -> int:
    key = api_key()
    limiter = RateLimiter(MIN_INTERVAL)
    plan = [(s, m) for s in SYMBOLS for m in months(START_MONTH, END_MONTH)]
    todo = [(s, m) for s, m in plan if not slice_path(s, m).exists()]
    cached = len(plan) - len(todo)
    if limit:
        todo = todo[:limit]

    print(f"{len(plan):,} slices planned, {cached:,} already cached, "
          f"{len(todo):,} to fetch this run"
          + (f" (--limit {limit})" if limit else ""))
    if not todo:
        print("nothing to do — cache is complete")
        return 0
    print(f"pacing at {REQUESTS_PER_MIN}/min (tier limit 75), "
          f"ETA {len(todo) * MIN_INTERVAL / 3600:.1f}h\n")

    fetched = empty = 0
    consecutive = 0
    t0 = time.monotonic()
    for i, (symbol, month) in enumerate(todo, 1):
        path = slice_path(symbol, month)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            payload = fetch_slice(symbol, month, key, limiter)
        except (RuntimeError, urllib.error.URLError, TimeoutError, OSError) as exc:
            consecutive += 1
            msg = str(exc)[:120]
            # A rate-limit or throttle response means slow down, not retry harder.
            if "rate" in msg.lower() or "frequency" in msg.lower() or "Note" in msg:
                back = min(60.0 * consecutive, 300.0)
                print(f"  [{i}/{len(todo)}] {symbol} {month}: THROTTLED — "
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
        # An empty month is a fact about the symbol (it did not trade yet), not an
        # error. Cache it so the next run does not ask again.
        if n == 0:
            empty += 1
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            json.dump(payload, fh, separators=(",", ":"))
        fetched += 1

        if i % 50 == 0 or i == len(todo):
            done = time.monotonic() - t0
            rate = i / done * 60 if done else 0
            left = (len(todo) - i) * MIN_INTERVAL / 3600
            print(f"  [{i:,}/{len(todo):,}] {symbol} {month}  {n:,} bars  "
                  f"| {rate:.0f}/min | {left:.1f}h left")

    print(f"\ndone: {fetched:,} slices cached ({empty:,} empty)")
    return 0


def do_plan() -> int:
    plan = [(s, m) for s in SYMBOLS for m in months(START_MONTH, END_MONTH)]
    cached = sum(1 for s, m in plan if slice_path(s, m).exists())
    ms = months(START_MONTH, END_MONTH)
    print(f"symbols   {len(SYMBOLS)}")
    print(f"months    {len(ms)}  ({ms[0]} .. {ms[-1]})")
    print(f"slices    {len(plan):,}   cached {cached:,}   remaining {len(plan)-cached:,}")
    print(f"pacing    {REQUESTS_PER_MIN}/min (tier limit 75)")
    print(f"ETA       {(len(plan)-cached) * MIN_INTERVAL / 3600:.1f} hours")
    print(f"cache     {CACHE}  (NOT committed — D191)")
    print(f"fixture   {FIXTURE.name}  (committed)")
    print(f"key       {'env ALPHAVANTAGE_API_KEY' if os.environ.get('ALPHAVANTAGE_API_KEY') else KEY_FILE}")
    return 0


# --------------------------------------------------------------------------
# Corporate actions — WP0. The fixture is unusable without this.
# --------------------------------------------------------------------------


def fetch_action(function: str, symbol: str, key: str, limiter: RateLimiter) -> list:
    """One SPLITS or DIVIDENDS call. Both are free endpoints.

    Same structural validation as the bar fetch: Alpha Vantage returns HTTP 200 on
    errors, so a payload without a `data` list is a failure however healthy the
    status line looks."""
    params = {"function": function, "symbol": symbol, "apikey": key}
    limiter.wait()
    url = f"{API}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
        payload = json.loads(r.read().decode("utf-8", errors="replace"))
    for flag in ("Error Message", "Note", "Information"):
        if flag in payload:
            raise RuntimeError(f"{flag}: {str(payload[flag])[:200]}")
    if "data" not in payload:
        raise RuntimeError(f"no `data` in {function} payload; keys={list(payload)}")
    return payload["data"]


def do_actions() -> int:
    """Fetch splits and dividends and write the events sidecar.

    WHY THIS EXISTS. The bar fixture is as-traded, which is right for immutability
    (D24) -- but as-traded means SPLITS ARE UNADJUSTED, and a scan of all 3,194,849
    bars found twelve of them, including OIH's 1:20 reverse split showing as a
    +1,772% single bar. A trend arm fed that number produces confident nonsense
    (D184's failure mode, at 15m).

    Five of the twelve -- the SPDR sector 2:1 splits on 2025-12-05 -- are recorded
    NOWHERE in this repo, because the daily fixture's sidecar ends 2024-12-31. They
    have to come from the provider.

    Dividends are fetched at the same time so `total_return_with_dividends` stops
    being a name for a price-only number: with an empty sidecar `dividend_panel`
    returns all-zero cash and `total_log_returns` degenerates to `log_returns`
    silently, which is the worst kind of wrong."""
    key = api_key()
    limiter = RateLimiter(MIN_INTERVAL)
    dividends: dict[str, list] = {}
    splits: dict[str, list] = {}

    print(f"fetching SPLITS and DIVIDENDS for {len(SYMBOLS)} symbols "
          f"({2 * len(SYMBOLS)} calls at {REQUESTS_PER_MIN}/min)\n")
    for i, symbol in enumerate(SYMBOLS, 1):
        try:
            raw_splits = fetch_action("SPLITS", symbol, key, limiter)
            raw_divs = fetch_action("DIVIDENDS", symbol, key, limiter)
        except (RuntimeError, urllib.error.URLError, TimeoutError, OSError) as exc:
            print(f"  [{i}/{len(SYMBOLS)}] {symbol}: FAILED — {str(exc)[:120]}")
            return 1

        # The repo's sidecar format: {symbol: [[iso_timestamp, value], ...]}
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
        if splits[symbol]:
            print(f"  [{i}/{len(SYMBOLS)}] {symbol}: {len(dividends[symbol])} dividends, "
                  f"SPLITS {splits[symbol]}")
        elif i % 10 == 0:
            print(f"  [{i}/{len(SYMBOLS)}] {symbol}: {len(dividends[symbol])} dividends")

    EVENTS.write_text(
        json.dumps({"dividends": dividends, "splits": splits}, indent=2,
                   sort_keys=True) + "\n",
        encoding="utf-8",
    )
    n_splits = sum(len(v) for v in splits.values())
    n_divs = sum(len(v) for v in dividends.values())
    print(f"\nwrote {EVENTS.name}: {n_splits} splits, {n_divs} dividends "
          f"across {len(SYMBOLS)} symbols")
    print("symbols with splits in range:")
    for s, v in sorted(splits.items()):
        if v:
            print(f"  {s:<6} " + ", ".join(f"{d[:10]} x{r}" for d, r in v))
    return 0


def load_splits() -> dict:
    """Splits from the events sidecar, as {symbol: [(iso_date, ratio), ...]}.

    Empty if the sidecar has not been fetched -- and that is a LOUD condition, not
    a quiet one: `do_build` refuses to write an unadjusted fixture."""
    if not EVENTS.exists():
        return {}
    payload = json.loads(EVENTS.read_text(encoding="utf-8"))
    return {s: [(d, float(r)) for d, r in v]
            for s, v in payload.get("splits", {}).items()}


def split_factor_at(stamp: str, splits: list) -> float:
    """The product of every split ratio with an effective date AFTER this bar.

    Back-adjustment, matching `corporate_actions.split_adjusted` exactly (which
    this cannot call directly because that function takes TimestampedBar objects
    and this build works on the raw JSON to avoid materialising 3.2M objects).

    PRICES ARE DIVIDED by the factor and VOLUMES ARE MULTIPLIED by it, and the
    opposite directions are the whole point: a 2:1 split halves the price and
    doubles the share count, so to express pre-split bars in post-split terms the
    price comes down and the volume goes up. Getting this backwards would leave a
    2x step in the volume series -- in a study whose signal IS volume."""
    factor = 1.0
    for eff_date, ratio in splits:
        if eff_date[:10] > stamp[:10]:
            factor *= ratio
    return factor


def _session_counts(regular_hours_only: bool) -> dict:
    """First pass: bars per (symbol, session). Needed before writing, because the
    half-day calendar is DERIVED from the data rather than hardcoded."""
    counts: dict[tuple[str, str], int] = {}
    for symbol in SYMBOLS:
        for month in months(START_MONTH, END_MONTH):
            path = slice_path(symbol, month)
            if not path.exists():
                continue
            with gzip.open(path, "rt", encoding="utf-8") as fh:
                series = series_of(json.load(fh))
            for stamp in series:
                if regular_hours_only and not ("09:30" <= stamp[11:16] <= "15:45"):
                    continue
                key = (symbol, stamp[:10])
                counts[key] = counts.get(key, 0) + 1
    return counts


def _half_days(counts: dict) -> set:
    """US market early closes, DERIVED not hardcoded.

    A half-day is a session where MOST of the universe is short -- the whole market
    shut at 13:00. That is a calendar fact and it is systematic. It is separated
    here from the OTHER cause of short sessions, a thin symbol that simply did not
    trade in some 15m slot, because the two need opposite treatment: the calendar
    one is dropped, the liquidity one is measured and kept."""
    by_date: dict[str, list] = {}
    for (_sym, day), n in counts.items():
        by_date.setdefault(day, []).append(n)
    out = set()
    for day, ns in by_date.items():
        short = sum(1 for n in ns if n < FULL_SESSION_BARS)
        if short >= 0.5 * len(ns):
            out.add(day)
    return out


def do_build(regular_hours_only: bool) -> int:
    """Cache -> one committed fixture, in the repo's raw-OHLCV shape."""
    import csv

    counts = _session_counts(regular_hours_only)
    half_days = _half_days(counts) if regular_hours_only else set()

    # The liquidity-correlated gap rate, measured EXCLUDING the calendar half-days
    # so the two causes are never conflated.
    short_sessions: dict[str, int] = {}
    missing_bars: dict[str, int] = {}
    total_sessions: dict[str, int] = {}
    for (sym, day), n in counts.items():
        if day in half_days:
            continue
        total_sessions[sym] = total_sessions.get(sym, 0) + 1
        if n != FULL_SESSION_BARS:
            short_sessions[sym] = short_sessions.get(sym, 0) + 1
            missing_bars[sym] = missing_bars.get(sym, 0) + (FULL_SESSION_BARS - n)

    all_splits = load_splits()
    if not all_splits:
        raise SystemExit(
            "REFUSING TO BUILD AN UNADJUSTED FIXTURE.\n"
            "The events sidecar has no splits. This fixture is as-traded, and a scan "
            "of it found TWELVE unadjusted splits -- OIH's 1:20 reverse shows as a "
            "+1,772% single 15-minute bar. Run `--actions` first."
        )
    n_split_events = sum(len(v) for v in all_splits.values())

    rows = 0
    per_symbol: dict[str, int] = {}
    first: dict[str, str] = {}
    last: dict[str, str] = {}
    zero_volume = 0
    dropped_half_day_bars = 0
    adjusted_bars = 0
    prev_close: dict[str, float] = {}
    max_move = {"symbol": None, "timestamp": None, "move": 0.0}

    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(FIXTURE, "wt", encoding="utf-8", newline="") as out:
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
                    if regular_hours_only and not ("09:30" <= stamp[11:16] <= "15:45"):
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
                    v = float(b["5. volume"]) * f   # opposite direction, deliberately
                    if v == 0.0:
                        zero_volume += 1
                    pc = prev_close.get(symbol)
                    if pc:
                        move = abs(c / pc - 1.0)
                        if move > max_move["move"]:
                            max_move = {"symbol": symbol, "timestamp": stamp,
                                        "move": move}
                    prev_close[symbol] = c
                    w.writerow([stamp, symbol, f"{o:.6f}", f"{h:.6f}",
                                f"{lo:.6f}", f"{c:.6f}", f"{v:.2f}"])
                    rows += 1
                    per_symbol[symbol] = per_symbol.get(symbol, 0) + 1
                    first.setdefault(symbol, stamp)
                    last[symbol] = stamp

    worst = sorted(short_sessions.items(), key=lambda kv: -kv[1])[:10]
    meta = {
        "symbols_requested": list(SYMBOLS),
        "symbols_included": sorted(per_symbol),
        "symbols_excluded": [s for s in SYMBOLS if s not in per_symbol],
        "start": START_MONTH,
        "end": END_MONTH,
        "interval": INTERVAL,
        "session": ("regular_hours_09:30-15:45" if regular_hours_only
                    else "extended_hours_04:00-20:00"),
        "bars_per_full_session": FULL_SESSION_BARS,
        "bar_boundary": (
            "timestamps mark the interval's OPEN, so a bar stamped t covers "
            "[t, t+15m) and is not complete until t+15m -- MEASURED, not assumed"
        ),
        "timezone": TZ,
        "timezone_note": (
            "US/Eastern as stated by the provider in its own Meta Data block. "
            "DST-shifting, so NOT a fixed offset and NOT the crypto fixtures' "
            "'naive means UTC' convention (D108)"
        ),
        "source": (
            "Alpha Vantage TIME_SERIES_INTRADAY, outputsize=full, month=YYYY-MM, "
            "adjusted=false, extended_hours=true at fetch. adjusted=false because "
            "adjusted prices are BACK-adjusted and drift as dividends are paid, "
            "which breaks D24's immutable-snapshot requirement; as-traded values "
            "never change. Volume is identical under both settings (measured, "
            "ratio 1.000000). Provider frame is as-traded: NOT split-adjusted (D75)"
        ),
        "volume_provenance": (
            "CONSOLIDATED. Verified before the backfill: SPY 2024-01 median session "
            "volume summed from 15m bars = 66,595,182 shares against a consolidated "
            "ADV of ~70-90M. Not a single-venue sample"
        ),
        "split_adjusted": True,
        "split_events_applied": n_split_events,
        "split_adjusted_bars": adjusted_bars,
        "split_policy": (
            "Back-adjusted from the events sidecar: prices DIVIDED by the product of "
            "every split ratio effective after the bar, volumes MULTIPLIED by the "
            "same factor. The opposite directions are the point -- a 2:1 split halves "
            "the price and doubles the share count. Matches "
            "corporate_actions.split_adjusted for prices; that helper does not touch "
            "volume because TimestampedBar carries none, and in a VOLUME study it "
            "must be handled. The as-traded values remain recoverable from the "
            "uncommitted raw cache plus this sidecar"
        ),
        "largest_residual_bar_move": max_move,
        "half_days_dropped": sorted(half_days),
        "half_day_policy": (
            "US early closes (13:00) are DERIVED, not hardcoded: a session where at "
            "least half the universe is short. Dropped at every symbol so the "
            "calendar is uniform -- the same argument D161 makes for crypto, which "
            "cannot be applied to a 390-minute session any other way"
        ),
        "half_day_bars_dropped": dropped_half_day_bars,
        "incomplete_sessions_excluding_half_days": sum(short_sessions.values()),
        "incomplete_session_rate": (
            sum(short_sessions.values()) / sum(total_sessions.values())
            if total_sessions else 0.0
        ),
        "missing_bars_excluding_half_days": sum(missing_bars.values()),
        "worst_symbols_by_incomplete_sessions": [
            {"symbol": s, "short_sessions": n,
             "rate": n / total_sessions[s], "bars_missing": missing_bars.get(s, 0)}
            for s, n in worst
        ],
        "gap_disclosure": (
            "Short sessions that are NOT half-days are a thin symbol failing to "
            "trade in some 15m slot, and they TRACK LIQUIDITY: the ten worst "
            "symbols average roughly a sixth the daily volume of the ten cleanest. "
            "The overall rate is small, but it is systematically concentrated in "
            "thin names, and THIS IS A VOLUME STUDY -- an arm that weights symbols "
            "equally is weighting a slightly different sampling density per symbol. "
            "Measured and disclosed rather than filled; forward-filling would "
            "invent data"
        ),
        "rows": rows,
        "bars_per_symbol": per_symbol,
        "first_bar": first,
        "last_bar": last,
        "zero_volume_bars": zero_volume,
        "zero_volume_rate": zero_volume / rows if rows else 0.0,
        "empty_bar_disclosure": (
            "D192 requires any intraday study on a new provider to measure and "
            "report its own universe's empty-bar rate. That rate is "
            "`zero_volume_rate` above and must be quoted in the study's "
            "pre-registration. yfinance's comparable rates were 50% at 1h and 15% "
            "at 15m, unexplained (D160), which is why this cannot be assumed"
        ),
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    META.write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    if not EVENTS.exists():
        EVENTS.write_text(
            json.dumps({"note": "not populated; as-traded frame"}, indent=1) + "\n",
            encoding="utf-8",
        )

    print(f"wrote {FIXTURE.name}: {rows:,} rows, "
          f"{FIXTURE.stat().st_size / 1e6:.1f} MB")
    print(f"  symbols       {len(per_symbol)}/{len(SYMBOLS)}")
    print(f"  half-days     {len(half_days)} dropped ({dropped_half_day_bars:,} bars)")
    print(f"  incomplete    {sum(short_sessions.values()):,} sessions "
          f"({meta['incomplete_session_rate'] * 100:.3f}%), "
          f"{sum(missing_bars.values()):,} bars missing")
    print(f"  zero-volume   {zero_volume:,} bars "
          f"({meta['zero_volume_rate'] * 100:.4f}%)")
    print(f"  splits        {n_split_events} events applied to "
          f"{adjusted_bars:,} bars")
    print(f"  largest move  {max_move['move'] * 100:.2f}%  "
          f"({max_move['symbol']} {max_move['timestamp']})")
    if max_move["move"] > 0.35:
        print("  WARNING: a >35% single-bar move survived adjustment. Either a split "
              "is missing from the sidecar or it is a real event -- check before use.")
    if rows and zero_volume / rows > 0.05:
        print("  WARNING: zero-volume rate above 5%. D192's gate -- investigate "
              "before any volume study uses this fixture.")
    if worst:
        print(f"  worst symbol  {worst[0][0]} at "
              f"{worst[0][1] / total_sessions[worst[0][0]] * 100:.2f}% short sessions")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true", help="cost the job, no network")
    ap.add_argument("--fetch", action="store_true", help="the long job, resumable")
    ap.add_argument("--build", action="store_true", help="cache -> fixture")
    ap.add_argument("--actions", action="store_true",
                    help="fetch SPLITS + DIVIDENDS into the events sidecar")
    ap.add_argument("--limit", type=int, help="fetch at most N slices this run")
    ap.add_argument("--extended", action="store_true",
                    help="build with extended hours instead of regular only")
    args = ap.parse_args()
    if args.actions:
        return do_actions()
    if args.fetch:
        return do_fetch(args.limit)
    if args.build:
        return do_build(regular_hours_only=not args.extended)
    return do_plan()


if __name__ == "__main__":
    raise SystemExit(main())
