"""One-time (manual, NETWORK) fetch: EXTENDED-HOURS 15-minute bars for SPY/QQQ/IWM/DIA.

    uv run python scripts/fetch_index_extended.py --plan      # no network, just the cost
    uv run python scripts/fetch_index_extended.py --probe     # 4 calls: prove the gates CAN pass
    uv run python scripts/fetch_index_extended.py --fetch     # the long job, resumable
    uv run python scripts/fetch_index_extended.py --actions   # SPLITS + DIVIDENDS sidecar
    uv run python scripts/fetch_index_extended.py --build     # cache -> committed fixture

Sibling of `fetch_etf_intraday.py`, same shape, same limiter, same key handling, and
**the same raw slice cache** — `data/raw/alphavantage/15min/{symbol}/{month}.json.gz`.
That sharing is deliberate and it is most of the request budget: the 57-ETF fetch
already ran `extended_hours=true` over 2018-01..2026-08, so those 416 slices for these
four symbols are already on disk and are never re-fetched. Only 2010-01..2017-12 is new.

WHY THIS EXISTS — the existing fixture threw the extended session away
----------------------------------------------------------------------
`etf_intraday_15m_raw` is BUILT regular-hours-only, and for a volume study that was
right: extended bars exist only where something traded, so on a 57-name universe
including AGG and TIP the bar count per session is liquidity-correlated, and that
would inject the quantity under test into the sampling grid.

**That argument does not apply here.** Four of the most liquid index ETFs in the world,
and the question is not volume — it is where the overnight drift accrues. D247 measured
+8.59%/yr overnight against -0.36% intraday, but "overnight" there is a close-to-open
GAP WITH NO INTERIOR. With the extended session it has an interior:

    16:00 -> 20:00   post-market      traded, exitable
    20:00 -> 04:00   untraded         STILL A GAP -- a position cannot be exited here
    04:00 -> 09:30   pre-market       traded, thin
    09:30 -> 16:00   regular hours

R11's amendment makes that decomposition load-bearing rather than curious: hurdle P1
measures a trailing drawdown on OPEN equity, so what matters is the PATH and not the
endpoints, and the one segment above with no path is the one you cannot stop out of.

WHAT THE GATES ARE FOR
----------------------
Two silent failure modes would each produce a fixture that looks fine and is wrong:

  extended_hours ignored   A fallback to regular hours gives 26 bars/session,
                           09:30-15:45, and every window above except the last
                           collapses to nothing. Gated: bars/session near 64, and
                           an 04:00 and a 19:45 bar must exist.
  `month` ignored          FX_INTRADAY silently ignores `month` and returns the
                           trailing weeks instead -- no error, no note, just the
                           wrong data (measured 2026-08-29). Equities are believed
                           to honour it. VERIFIED PER SLICE, not assumed: every
                           returned timestamp must fall in the requested month.

The third gate is D226's. The fixture is as-traded (`adjusted=false`, for D24
immutability), so splits sit in the price series unadjusted -- OIH's 1:20 reverse
shows as a +1,772% single 15-minute bar. The build back-adjusts from the events
sidecar and refuses to run without one.

THE SESSION WINDOW, AND WHY IT IS 04:00-19:45
----------------------------------------------
Measured over the cached slices: 04:00..19:45 is 64 slots and is present in
essentially every session. A bar stamped 20:00 appears in about half of sessions and
20:15..23:45 in 5-9% of them. Timestamps mark the interval's OPEN, so a bar stamped
19:45 covers [19:45, 20:00) and its close IS the 20:00 print; a bar stamped 20:00 is
already past the documented 8:00pm session end. Those late bars are DROPPED and
counted, so the grid is the documented session and nothing else.

BEING A GOOD CITIZEN
--------------------
  * one call per (symbol, month), paced at 66/min against the 75/min tier ceiling
  * every slice CACHED; a cached slice is NEVER re-fetched, so a run resumes
  * exponential backoff on a throttle, HARD STOP after 5 consecutive failures
  * the raw cache is NOT committed (D191); only the derived fixture is
  * the key is read from the environment or from OUTSIDE the repo, and is never
    printed, logged, or written into any URL this script displays
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

API = "https://www.alphavantage.co/query"
KEY_FILE = Path.home() / ".config" / "alphavantage" / "key"
CACHE = REPO / "data" / "raw" / "alphavantage"
FIXTURE = REPO / "data" / "fixtures" / "index_extended_15m_raw.csv.gz"
META = REPO / "data" / "fixtures" / "index_extended_15m_raw.meta.json"
EVENTS = REPO / "data" / "fixtures" / "index_extended_15m_raw_events.json"

# The three index products with futures analogues (ES / NQ / RTY), plus DIA (YM),
# which costs 96 extra requests and is therefore cheap enough to take.
SYMBOLS = ("SPY", "QQQ", "IWM", "DIA")

INTERVAL = "15min"
START_MONTH = "2010-01"   # coverage is thin before 2010 (44.9 bars/session in 2005)
END_MONTH = "2026-08"

REQUESTS_PER_MIN = 66
MIN_INTERVAL = 60.0 / REQUESTS_PER_MIN
MAX_CONSECUTIVE_FAILURES = 5
TIMEOUT = 90

TZ = "US/Eastern"

# The documented extended session, on the OPEN-stamp convention.
SESSION_OPEN = "04:00"
SESSION_LAST_BAR = "19:45"          # covers [19:45, 20:00) -- its close is the 20:00 print
RTH_OPEN = "09:30"
RTH_LAST_BAR = "15:45"              # covers [15:45, 16:00) -- its close is the 16:00 print
FULL_SESSION_BARS = 64              # 04:00..19:45 inclusive, 960 minutes / 15
RTH_SESSION_BARS = 26

# Gate thresholds. Stated here so a reader does not have to infer them from asserts.
#
# MIN_MEDIAN_BARS_PER_SESSION was set at 55 on the first pass and that was WRONG, in
# an instructive way. The probe fired on IWM/DIA 2010-01 at 48 and 46 bars/session —
# but the thing it is supposed to catch is a silent fallback to REGULAR HOURS, which
# gives exactly 26 bars over 09:30-15:45. Measured on those slices: pre-market and
# post-market bars on 19 of 19 sessions, RTH median exactly 26. The extended session
# HAD arrived; it is simply thinner on the less liquid names in 2010, because an
# extended-hours bar exists only where something actually traded.
#
# So the gate is restated as "materially wider than RTH, on essentially every
# session" and the RAGGEDNESS is measured and disclosed rather than gated. The
# specific anchor bars the decomposition wants — 04:00, 18:00, 19:45 — are sparse on
# IWM and DIA in the early era (DIA 2014-06 prints an 04:00 bar in 0 of 21 sessions)
# and that is a first-class finding for the consumer, not a reason to reject a slice.
MIN_MEDIAN_BARS_PER_SESSION = 32    # a silent RTH fallback would give exactly 26
MIN_SESSION_SHARE_WITH_EXTENDED = 0.90
MOVE_LIMIT = 0.15                   # D226: an unadjusted split looks exactly like this

# Clock times whose per-session availability is reported. 18:00 is the MyFundedFutures
# Globex entry; the rest are the four-window boundaries.
ANCHOR_TIMES = (SESSION_OPEN, "18:00", SESSION_LAST_BAR, RTH_OPEN, RTH_LAST_BAR)

# D247's +8.59% is era-dependent — the intraday leg reads -0.33% full-sample, +1.44%
# excluding 2020 and +3.05% from 2021. Every number this fixture supports is split
# the same way, and the split is fixed HERE so the fetcher and the consumer cannot
# disagree about it.
ERAS = ("2010-2019", "2020", "2021-2026")


def era_of(day: str) -> str:
    year = int(day[:4])
    if year <= 2019:
        return "2010-2019"
    if year == 2020:
        return "2020"
    return "2021-2026"


def api_key() -> str:
    """Env first, then the file OUTSIDE the repo. The key is never logged."""
    key = os.environ.get("ALPHAVANTAGE_API_KEY")
    if key:
        return key.strip()
    if KEY_FILE.exists():
        return KEY_FILE.read_text(encoding="utf-8").strip()
    raise SystemExit(f"No API key. Set ALPHAVANTAGE_API_KEY or create {KEY_FILE}.")


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


def series_of(payload: dict) -> dict:
    for k, v in payload.items():
        if k.lower().startswith("time series"):
            return v
    return {}


# --------------------------------------------------------------------------
# The two gates that decide whether this fixture is worth anything at all
# --------------------------------------------------------------------------


def month_honoured(series: dict, month: str) -> tuple[bool, int, str]:
    """Did the provider return the month we ASKED for?

    `FX_INTRADAY` silently ignores `month` and returns the trailing weeks instead —
    no error, no note, just the wrong data. Equities are believed to honour it, and
    belief is not a gate. Returns (ok, n_foreign, span)."""
    stamps = sorted(series)
    if not stamps:
        return True, 0, ""           # an empty month is a fact, not a violation
    foreign = sum(1 for s in stamps if s[:7] != month)
    return foreign == 0, foreign, f"{stamps[0]} -> {stamps[-1]}"


def extended_session_present(series: dict) -> dict:
    """Did `extended_hours=true` actually arrive?

    A silent fallback to regular hours gives exactly 26 bars/session over
    09:30-15:45, and three of the four windows this fixture exists to measure would
    collapse to nothing — while the payload looked entirely healthy.

    The test is therefore NOT "is the session as wide as SPY's". It is "is this
    wider than RTH, on essentially every session, in both directions". Raggedness
    inside the extended session is a liquidity fact about the symbol and is
    measured, not rejected."""
    if not series:
        return {"ok": True, "sessions": 0}
    by_day: dict[str, set] = {}
    for stamp in series:
        by_day.setdefault(stamp[:10], set()).add(stamp[11:16])
    n = len(by_day)
    med = statistics.median(len(v) for v in by_day.values())
    rth_med = statistics.median(
        sum(1 for t in v if RTH_OPEN <= t <= RTH_LAST_BAR) for v in by_day.values()
    )
    pre = sum(1 for v in by_day.values() if any(t < RTH_OPEN for t in v)) / n
    post = sum(1 for v in by_day.values() if any(t > RTH_LAST_BAR for t in v)) / n
    times = sorted(s[11:16] for s in series)
    return {
        "ok": bool(med >= MIN_MEDIAN_BARS_PER_SESSION
                   and pre >= MIN_SESSION_SHARE_WITH_EXTENDED
                   and post >= MIN_SESSION_SHARE_WITH_EXTENDED),
        "sessions": n,
        "median_bars": float(med),
        "median_rth_bars": float(rth_med),
        "share_with_premarket": pre,
        "share_with_postmarket": post,
        "earliest": times[0],
        "latest": times[-1],
    }


def fetch_slice(symbol: str, month: str, key: str, limiter: RateLimiter) -> dict:
    """One (symbol, month). Returns the parsed payload or raises.

    Alpha Vantage returns HTTP 200 on errors, so success is decided STRUCTURALLY:
    a payload without a `Time Series (...)` key is a failure however healthy the
    status line looks."""
    params = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": symbol,
        "interval": INTERVAL,
        "month": month,
        "outputsize": "full",       # MANDATORY with `month`: the default returns 100 bars
        "adjusted": "false",        # D24 immutability; as-traded values never change
        "extended_hours": "true",   # THE POINT OF THIS FETCH
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

    series = series_of(payload)
    ok, foreign, span = month_honoured(series, month)
    if not ok:
        raise RuntimeError(
            f"MONTH NOT HONOURED: asked {month}, got {span} "
            f"({foreign}/{len(series)} bars outside the requested month). "
            "This is the FX_INTRADAY failure mode and the fixture is not safe."
        )
    return payload


# --------------------------------------------------------------------------
# --probe: four calls that prove the gates CAN pass before spending 384
# --------------------------------------------------------------------------


def do_probe() -> int:
    """Four requests, on the oldest and newest months this fetch will ask for.

    The point is to find out that `extended_hours` or `month` is broken for 2010
    BEFORE paying for 384 slices, not after. Nothing is cached by this path — it is
    a read of the answer, not part of the backfill."""
    key = api_key()
    limiter = RateLimiter(MIN_INTERVAL)
    checks = [("SPY", START_MONTH), ("SPY", "2013-06"),
              ("IWM", START_MONTH), ("DIA", START_MONTH), ("QQQ", "2014-06")]
    bad = 0
    print(f"probing {len(checks)} slices (network), key from "
          f"{'env' if os.environ.get('ALPHAVANTAGE_API_KEY') else KEY_FILE}\n")
    for symbol, month in checks:
        try:
            payload = fetch_slice(symbol, month, key, limiter)
        except Exception as exc:                        # noqa: BLE001 - report, do not raise
            print(f"  {symbol} {month}: FAILED — {str(exc)[:200]}")
            bad += 1
            continue
        series = series_of(payload)
        g = extended_session_present(series)
        # Cache it: a probe slice is a real slice and re-fetching it would be waste.
        path = slice_path(symbol, month)
        path.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            json.dump(payload, fh, separators=(",", ":"))
        print(f"  {symbol} {month}: {len(series):,} bars / {g['sessions']} sessions"
              f"  {g['earliest']}->{g['latest']}"
              f"  median {g['median_bars']:.0f}/session (RTH {g['median_rth_bars']:.0f})"
              f"  pre {g['share_with_premarket']:.0%} post {g['share_with_postmarket']:.0%}"
              f"  {'EXTENDED OK' if g['ok'] else 'NOT EXTENDED — STOP'}")
        if not g["ok"]:
            bad += 1
    if bad:
        print(f"\n{bad} probe(s) failed. DO NOT RUN --fetch. "
              "A fixture that quietly contains regular hours only would be worse "
              "than none, because everything downstream would look fine and be wrong.")
        return 1
    print("\nall probes clear: `month` honoured and the extended session arrived.")
    return 0


def do_plan() -> int:
    plan = [(s, m) for s in SYMBOLS for m in months(START_MONTH, END_MONTH)]
    cached = sum(1 for s, m in plan if slice_path(s, m).exists())
    ms = months(START_MONTH, END_MONTH)
    print(f"symbols   {len(SYMBOLS)}  ({', '.join(SYMBOLS)})")
    print(f"months    {len(ms)}  ({ms[0]} .. {ms[-1]})")
    print(f"slices    {len(plan):,}   cached {cached:,}   remaining {len(plan)-cached:,}")
    print("          (the 57-ETF fetch already ran extended_hours=true over "
          "2018-01..2026-08 and shares this cache)")
    print(f"pacing    {REQUESTS_PER_MIN}/min (tier limit 75)")
    print(f"ETA       {(len(plan)-cached) * MIN_INTERVAL / 60:.1f} minutes")
    print(f"cache     {CACHE}  (NOT committed — D191)")
    print(f"fixture   {FIXTURE.name}  (committed)")
    print(f"key       {'env ALPHAVANTAGE_API_KEY' if os.environ.get('ALPHAVANTAGE_API_KEY') else KEY_FILE}")
    return 0


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
          f"ETA {len(todo) * MIN_INTERVAL / 60:.1f} min\n")

    fetched = empty = not_extended = 0
    consecutive = 0
    t0 = time.monotonic()
    for i, (symbol, month) in enumerate(todo, 1):
        path = slice_path(symbol, month)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            payload = fetch_slice(symbol, month, key, limiter)
        except (RuntimeError, urllib.error.URLError, TimeoutError, OSError) as exc:
            consecutive += 1
            msg = str(exc)[:160]
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
        series = series_of(payload)
        n = len(series)
        if n == 0:
            empty += 1
        else:
            g = extended_session_present(series)
            if not g["ok"]:
                not_extended += 1
                print(f"  [{i}/{len(todo)}] {symbol} {month}: NOT EXTENDED — "
                      f"median {g['median_bars']:.0f} bars/session "
                      f"(RTH {g['median_rth_bars']:.0f}), "
                      f"{g['earliest']}->{g['latest']}, "
                      f"pre {g['share_with_premarket']:.0%} "
                      f"post {g['share_with_postmarket']:.0%}")
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            json.dump(payload, fh, separators=(",", ":"))
        fetched += 1

        if i % 50 == 0 or i == len(todo):
            done = time.monotonic() - t0
            rate = i / done * 60 if done else 0
            left = (len(todo) - i) * MIN_INTERVAL / 60
            print(f"  [{i:,}/{len(todo):,}] {symbol} {month}  {n:,} bars  "
                  f"| {rate:.0f}/min | {left:.1f} min left")

    print(f"\ndone: {fetched:,} slices cached ({empty:,} empty, "
          f"{not_extended:,} NOT extended)")
    if not_extended:
        print("  WARNING: some slices came back without the extended session. "
              "--build gates on this; do not use the fixture until it is understood.")
    return 0


# --------------------------------------------------------------------------
# Corporate actions — D226. The fixture is unusable without this.
# --------------------------------------------------------------------------


def fetch_action(function: str, symbol: str, key: str, limiter: RateLimiter) -> list:
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
    """Fetch SPLITS and DIVIDENDS and write the events sidecar.

    The bars are as-traded, which is right for immutability (D24) and means splits
    sit in the price series UNADJUSTED. D226 found twelve of them across the 57-ETF
    fixture, OIH's 1:20 reverse showing as a +1,772% single 15-minute bar. None of
    these four is known to have split in span — which is exactly the claim that has
    to be CHECKED rather than assumed, because a fixture built on that assumption
    fails silently."""
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
        print(f"  [{i}/{len(SYMBOLS)}] {symbol}: {len(dividends[symbol])} dividends, "
              f"{len(splits[symbol])} splits {splits[symbol] or ''}")

    EVENTS.write_text(
        json.dumps({"dividends": dividends, "splits": splits}, indent=2,
                   sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"\nwrote {EVENTS.name}: "
          f"{sum(len(v) for v in splits.values())} splits, "
          f"{sum(len(v) for v in dividends.values())} dividends")
    return 0


def load_splits() -> dict:
    if not EVENTS.exists():
        return {}
    payload = json.loads(EVENTS.read_text(encoding="utf-8"))
    return {s: [(d, float(r)) for d, r in v]
            for s, v in payload.get("splits", {}).items()}


def split_factor_at(stamp: str, splits: list) -> float:
    """The product of every split ratio with an effective date AFTER this bar.

    Back-adjustment: PRICES ARE DIVIDED by the factor and VOLUMES MULTIPLIED, and
    the opposite directions are the point — a 2:1 split halves the price and doubles
    the share count. Off by one day here leaves a full split step in the series."""
    factor = 1.0
    for eff_date, ratio in splits:
        if eff_date[:10] > stamp[:10]:
            factor *= ratio
    return factor


# --------------------------------------------------------------------------
# Bad prints — the thing this fetch found that nobody was looking for
# --------------------------------------------------------------------------
#
# The RTH fixture never saw this because it threw the extended session away. Once
# the post-market is kept, the feed carries a population of ERRONEOUS PRINTS that
# would wreck the one measurement this fixture exists to make.
#
# The signature is unmistakable. QQQ, 2025-06-16 16:45 ET:
#
#     open 534.18   high 534.25   low 447.2455   close 447.2455
#
# open and high are the real price; low and close are 16% away and the SAME bogus
# value repeats across the 16:45, 17:00 and 17:15 bars. Measured across the whole
# fixture, the largest lower wick is +907%.
#
# THREE FACTS DECIDED THE TREATMENT:
#
#   1. It is a POST-MARKET pathology. Bars with a >5% uncorroborated wick:
#      1,290 post-market, 71 pre-market, 16 regular-hours.
#   2. It is RECENT — 4-12 a year through 2022, then 108 / 301 / 571 / 349 in
#      2023 / 2024 / 2025 / 2026. That is a feed change, not a market change.
#   3. The regular-hours cases are mostly REAL. 2010-05-06 (the Flash Crash),
#      2015-08-24 (the ETF dislocation open), 2018-02-06 (Volmageddon),
#      2025-04-07 and 2025-04-09 (the tariff reversal) all appear, and a filter
#      that erased them would be deleting the exact tail a drawdown study is
#      about. The RTH cases that are NOT real cluster on HALF-DAYS — 2023-11-24,
#      2024-07-03, 2024-12-24, 2025-07-03, 2025-11-28 are all 13:00 closes, and
#      the offending bars are stamped AFTER the close.
#
# So the rule is CORROBORATION, not magnitude: an extreme is suspect when no
# neighbouring bar's body comes near it. In a real dislocation the adjacent bars
# also trade at the extreme and nothing is flagged — SPY 2020-03-16 09:30, a
# limit-down open, is NOT flagged. In a bad print the neighbours sit 16% away.
#
# WHAT THE RULE CANNOT DO, stated because it bounds every path number downstream:
# an isolated REAL spike that reverses inside one 15-minute bar is indistinguishable
# from a bad print without a second data source. In the extended session we accept
# that trade — such a move is barely fillable anyway — and the consumer reports the
# raw and closes-only variants alongside, so the reader sees the bracket.

SUSPECT_TOL = 0.03


def flag_bad_prints(records: list[tuple]):
    """Return (frame with a `suspect` column, census dict).

    For each bar, the corroborating anchor is the median of the OPENs of the bar
    and its two neighbours — robust to any single bad open, and it TRACKS a fast
    real move, which is what stops it flagging genuine dislocations. A bar is
    suspect when its low falls below, its high rises above, or its close sits
    outside a +/-SUSPECT_TOL band around the local anchor range."""
    import numpy as np
    import pandas as pd

    df = pd.DataFrame(records, columns=["timestamp", "symbol", "open", "high",
                                        "low", "close", "volume"])
    df = df.sort_values(["symbol", "timestamp"], kind="stable").reset_index(drop=True)
    g = df.groupby("symbol", sort=False)["open"]
    prev_o, next_o = g.shift(1), g.shift(-1)
    anchor = np.nanmedian(
        np.vstack([prev_o.to_numpy(dtype=float),
                   df["open"].to_numpy(dtype=float),
                   next_o.to_numpy(dtype=float)]), axis=0)
    lo_band = np.minimum.reduce([
        np.nan_to_num(prev_o.to_numpy(dtype=float), nan=np.inf), anchor,
        np.nan_to_num(next_o.to_numpy(dtype=float), nan=np.inf)]) * (1 - SUSPECT_TOL)
    hi_band = np.maximum.reduce([
        np.nan_to_num(prev_o.to_numpy(dtype=float), nan=-np.inf), anchor,
        np.nan_to_num(next_o.to_numpy(dtype=float), nan=-np.inf)]) * (1 + SUSPECT_TOL)

    hhmm = df["timestamp"].str.slice(11, 16)
    seg = np.where(hhmm < RTH_OPEN, "pre",
                   np.where(hhmm <= RTH_LAST_BAR, "rth", "post"))
    extended = seg != "rth"

    bad_close = (df["close"].to_numpy() < lo_band) | (df["close"].to_numpy() > hi_band)
    bad_extreme = (df["low"].to_numpy() < lo_band) | (df["high"].to_numpy() > hi_band)

    # A CORROBORATION rule needs corroborators. The first and last bar of each
    # symbol have only one neighbour, so their band is one-sided and is pulled by
    # whichever side exists — a falling series flags its own last bar. Eight bars in
    # 958,217 here, but it is a false positive by construction rather than by luck,
    # so it is excluded rather than tolerated.
    edge = (prev_o.isna() | next_o.isna()).to_numpy()

    # The extreme test runs on the EXTENDED session only. In regular hours the
    # contamination is 16 bars in 435,166 and the large wicks are dominated by
    # genuine dislocations that a tail measurement must keep. The CLOSE test runs
    # everywhere, because a bad close corrupts a window boundary wherever it lands.
    suspect = (bad_close | (bad_extreme & extended)) & ~edge
    df["suspect"] = suspect.astype(int)

    census = {
        "rule": (
            "anchor = median(open[t-1], open[t], open[t+1]); a bar is suspect when "
            "its CLOSE leaves a +/-3% band around the local anchor range (all "
            "sessions), or its HIGH/LOW leaves that band (EXTENDED SESSION ONLY)"
        ),
        "tolerance": SUSPECT_TOL,
        "suspect_bars": int(suspect.sum()),
        "suspect_rate": float(suspect.mean()),
        "edge_bars_exempt": int(edge.sum()),
        "by_segment": {s: int(suspect[seg == s].sum()) for s in ("pre", "rth", "post")},
        "rate_by_segment": {
            s: (float(suspect[seg == s].mean()) if (seg == s).any() else 0.0)
            for s in ("pre", "rth", "post")
        },
        "by_symbol": {
            s: int(suspect[df["symbol"].to_numpy() == s].sum()) for s in SYMBOLS
        },
        "by_year": {
            y: int(suspect[df["timestamp"].str.slice(0, 4).to_numpy() == y].sum())
            for y in sorted(df["timestamp"].str.slice(0, 4).unique())
        },
        "worst_lower_wick_raw": float(
            (np.minimum(df["open"], df["close"]) / df["low"] - 1.0).max()
        ),
        "why_extremes_are_only_filtered_in_the_extended_session": (
            "In regular hours the large wicks are dominated by GENUINE dislocations "
            "-- 2010-05-06 (Flash Crash), 2015-08-24, 2018-02-06, 2025-04-07/09 -- "
            "and erasing them would delete the exact tail a drawdown study is about. "
            "In the extended session there is no comparable population of real 5% "
            "15-minute index-ETF moves, and the count is two orders of magnitude "
            "larger. The residual RTH bad prints cluster on HALF-DAYS, on bars "
            "stamped after a 13:00 close"
        ),
    }
    return df, census


def largest_clean_close_move(df) -> dict:
    """D226's gate, restricted to non-suspect bars.

    The gate exists to catch an UNADJUSTED CORPORATE ACTION. Run over the raw
    series it fires instead on a bad print (QQQ 2025-06-16 17:00, +19.43%), which
    is a true positive for a different question and makes the gate useless for its
    own. Suspect bars are excluded so the gate tests what it is named for; the bad
    prints have their own census and their own disclosure."""
    clean = df[df["suspect"] == 0]
    moves = clean.groupby("symbol", sort=False)["close"].pct_change().abs()
    if moves.notna().sum() == 0:
        return {"symbol": None, "timestamp": None, "move": 0.0}
    i = moves.idxmax()
    return {"symbol": str(clean.loc[i, "symbol"]),
            "timestamp": str(clean.loc[i, "timestamp"]),
            "move": float(moves.loc[i])}


# --------------------------------------------------------------------------
# --build
# --------------------------------------------------------------------------


def do_build() -> int:
    """Cache -> one committed fixture, in the repo's raw-OHLCV shape.

    NO HALF-DAY DROPPING, and that is a departure from `fetch_etf_intraday.py`.
    That build drops early closes so a 57-name RTH grid stays exactly rectangular.
    Here the grid is ragged by construction — extended bars exist only where
    something traded — so rectangularity is not available and pretending to it would
    mean discarding real sessions. Half-days are KEPT, FLAGGED in the meta, and the
    consumer excludes them where they matter. A 13:00 close has no 16:00->20:00
    window, so any measurement of that window must handle it explicitly rather than
    inherit a silent drop."""
    import csv

    all_splits = load_splits()
    if not EVENTS.exists():
        raise SystemExit(
            "REFUSING TO BUILD AN UNADJUSTED FIXTURE.\n"
            "There is no events sidecar. This fixture is as-traded and D226 found an "
            "unadjusted 1:20 reverse split showing as a +1,772% single 15-minute "
            "bar. Run `--actions` first."
        )
    n_split_events = sum(len(v) for v in all_splits.values())

    missing_slices = [(s, m) for s in SYMBOLS for m in months(START_MONTH, END_MONTH)
                      if not slice_path(s, m).exists()]
    if missing_slices:
        raise SystemExit(
            f"{len(missing_slices)} slices are not cached (first: "
            f"{missing_slices[0]}). Run `--fetch` first — a fixture built on a "
            "partial cache has silent holes in its calendar."
        )

    zero_volume = 0
    adjusted_bars = 0
    dropped_late = 0                 # bars stamped 20:00 or later
    month_violations = 0
    not_extended_slices: list[str] = []
    records: list[tuple] = []

    for symbol in SYMBOLS:
        for month in months(START_MONTH, END_MONTH):
            with gzip.open(slice_path(symbol, month), "rt", encoding="utf-8") as fh:
                series = series_of(json.load(fh))
            ok_month, foreign, _ = month_honoured(series, month)
            if not ok_month:
                month_violations += foreign
            if series and not extended_session_present(series)["ok"]:
                not_extended_slices.append(f"{symbol}/{month}")
            for stamp in sorted(series):
                hhmm = stamp[11:16]
                if hhmm < SESSION_OPEN or hhmm > SESSION_LAST_BAR:
                    dropped_late += 1
                    continue
                b = series[stamp]
                f = split_factor_at(stamp, all_splits.get(symbol, []))
                if f != 1.0:
                    adjusted_bars += 1
                v = float(b["5. volume"]) * f
                if v == 0.0:
                    zero_volume += 1
                records.append((
                    stamp, symbol,
                    float(b["1. open"]) / f, float(b["2. high"]) / f,
                    float(b["3. low"]) / f, float(b["4. close"]) / f, v,
                ))

    rows = len(records)
    df, bad_print_census = flag_bad_prints(records)
    max_move = largest_clean_close_move(df)

    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(FIXTURE, "wt", encoding="utf-8", newline="") as out:
        w = csv.writer(out)
        w.writerow(["timestamp", "symbol", "open", "high", "low", "close",
                    "volume", "suspect"])
        for r in df.itertuples(index=False):
            w.writerow([r.timestamp, r.symbol, f"{r.open:.6f}", f"{r.high:.6f}",
                        f"{r.low:.6f}", f"{r.close:.6f}", f"{r.volume:.2f}",
                        int(r.suspect)])

    per_symbol: dict[str, int] = {}
    first: dict[str, str] = {}
    last: dict[str, str] = {}
    session_bars: dict[tuple[str, str], int] = {}
    rth_bars: dict[tuple[str, str], int] = {}
    anchors: dict[tuple[str, str], set] = {}
    for stamp, symbol, *_ in records:
        hhmm = stamp[11:16]
        per_symbol[symbol] = per_symbol.get(symbol, 0) + 1
        first.setdefault(symbol, stamp)
        last[symbol] = stamp
        key = (symbol, stamp[:10])
        session_bars[key] = session_bars.get(key, 0) + 1
        if RTH_OPEN <= hhmm <= RTH_LAST_BAR:
            rth_bars[key] = rth_bars.get(key, 0) + 1
        slot = anchors.setdefault(key, set())
        if hhmm in ANCHOR_TIMES:
            slot.add(hhmm)
        if hhmm < RTH_OPEN:
            slot.add("any_pre")
        elif hhmm > RTH_LAST_BAR:
            slot.add("any_post")

    # ---- the gates, computed from the data that was actually written ----
    counts = sorted(session_bars.values())
    median_bars = counts[len(counts) // 2] if counts else 0
    mean_bars = sum(counts) / len(counts) if counts else 0.0
    n_sessions = len(session_bars)
    # A market-wide early close, not one thin symbol short a print: at least half the
    # universe short at once. Same rule the consumer applies, deliberately — two
    # different half-day definitions in a fetcher and its runner is a bug waiting.
    short_by_day: dict[str, int] = {}
    total_by_day: dict[str, int] = {}
    for (_s, day), n in rth_bars.items():
        total_by_day[day] = total_by_day.get(day, 0) + 1
        if n < RTH_SESSION_BARS:
            short_by_day[day] = short_by_day.get(day, 0) + 1
    half_days = sorted(d for d, t in total_by_day.items()
                       if short_by_day.get(d, 0) >= 0.5 * t)
    probe_times = (*ANCHOR_TIMES, "any_pre", "any_post")

    def _cov(pred) -> dict:
        keys = [k for k in anchors if pred(k)]
        if not keys:
            return {t: 0.0 for t in probe_times} | {"sessions": 0}
        out = {t: round(sum(1 for k in keys if t in anchors[k]) / len(keys), 6)
               for t in probe_times}
        out["sessions"] = len(keys)
        return out

    anchor_cov = _cov(lambda k: True)
    # Per symbol AND per era, because a pooled coverage number hides exactly the
    # thing the consumer needs: DIA prints no 04:00 bar at all in some early months.
    anchor_cov_detail = {
        f"{sym}|{era}": _cov(lambda k, s=sym, e=era: k[0] == s and era_of(k[1]) == e)
        for sym in SYMBOLS for era in ERAS
    }

    gates = {
        # THE gate: is this materially wider than RTH on essentially every session,
        # in both directions? A silent RTH fallback gives exactly 26 over
        # 09:30-15:45 and would fail all three legs at once.
        "extended_session_arrived": bool(
            median_bars >= MIN_MEDIAN_BARS_PER_SESSION
            and anchor_cov["any_pre"] >= MIN_SESSION_SHARE_WITH_EXTENDED
            and anchor_cov["any_post"] >= MIN_SESSION_SHARE_WITH_EXTENDED
            and not not_extended_slices
        ),
        "the_04_00_and_19_45_bars_exist": bool(
            anchor_cov[SESSION_OPEN] > 0.0 and anchor_cov[SESSION_LAST_BAR] > 0.0
        ),
        "median_bars_per_session": median_bars,
        "mean_bars_per_session": round(mean_bars, 2),
        "rth_only_would_be": RTH_SESSION_BARS,
        "month_honoured": month_violations == 0,
        "bars_outside_requested_month": month_violations,
        "slices_without_extended_session": not_extended_slices,
        "no_unexplained_large_bar": max_move["move"] <= MOVE_LIMIT,
        "large_bar_threshold": MOVE_LIMIT,
        "anchor_bar_coverage": anchor_cov,
        "anchor_bar_coverage_by_symbol_and_era": anchor_cov_detail,
        "anchor_coverage_note": (
            "READ THIS BEFORE USING THE CLOCK ANCHORS. `any_pre`/`any_post` are near "
            "1.0 — the extended session arrived on essentially every session. The "
            "SPECIFIC clock bars are a different matter: an extended-hours bar is "
            "printed only where something traded, so 04:00, 18:00 and 19:45 are "
            "sparse on IWM and DIA in the early era (DIA prints no 04:00 bar at all "
            "in some 2010-2014 months). A consumer that keys on exact clock times "
            "therefore selects a LIQUIDITY-CONDITIONED subsample. Boundary prices "
            "should be taken as the FIRST/LAST print inside each window, not at a "
            "fixed clock time, and the realised boundaries disclosed"
        ),
    }

    meta = {
        "symbols": list(SYMBOLS),
        "start": START_MONTH,
        "end": END_MONTH,
        "interval": INTERVAL,
        "session": "extended_hours_04:00-19:45_open_stamped",
        "session_note": (
            "Timestamps mark the interval's OPEN, so the last bar 19:45 covers "
            "[19:45, 20:00) and its close IS the 20:00 print; the RTH last bar "
            "15:45 covers [15:45, 16:00) and its close IS the 16:00 print. Bars "
            "stamped 20:00 or later are DROPPED — they are past the documented "
            "8:00pm session end, appear in roughly half of sessions at 20:00 and "
            "5-9% beyond it, and a ragged tail would make the 16:00->20:00 window "
            "mean different things on different days"
        ),
        "bars_per_full_session": FULL_SESSION_BARS,
        "bars_dropped_after_session_end": dropped_late,
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
            "adjusted=false, extended_hours=true. adjusted=false because adjusted "
            "prices are BACK-adjusted and drift as dividends are paid, which breaks "
            "D24's immutable-snapshot requirement; as-traded values never change. "
            "The PROVIDER frame is as-traded; the BUILD back-adjusts splits from the "
            "events sidecar, so this FIXTURE is split-adjusted and dividends are "
            "supplied separately (D75's two frames)"
        ),
        "gates": gates,
        "gate_note": (
            "Two silent failure modes are gated here because each would produce a "
            "fixture that looks fine and is wrong. (1) extended_hours ignored -> a "
            "26-bar 09:30-15:45 session, and three of the four windows this fixture "
            "exists to measure collapse to nothing. (2) `month` ignored -> "
            "FX_INTRADAY does exactly this, silently returning the trailing weeks "
            "instead of the month requested (measured 2026-08-29). Both are verified "
            "per slice at fetch AND recomputed here from the written data"
        ),
        "split_adjusted": True,
        "split_events_applied": n_split_events,
        "split_adjusted_bars": adjusted_bars,
        "split_note": (
            "ZERO splits for all four symbols over 2010-01..2026-08, from the "
            "provider's own SPLITS endpoint. That is the expected answer and it was "
            "CHECKED rather than assumed, because a build that assumes it fails "
            "silently -- D226 found twelve unadjusted splits across the 57-ETF "
            "fixture, one of them a +1,772% single 15-minute bar"
        ),
        "largest_residual_bar_move": max_move,
        "bad_prints": bad_print_census,
        "suspect_column": (
            "The fixture ships RAW as-traded OHLCV and a `suspect` flag; no price is "
            "modified, so D24's immutability holds and the judgement is visible "
            "rather than baked in. A consumer measuring a PATH (highs and lows) must "
            "decide what to do with these bars and say so. A consumer measuring only "
            "window boundaries is far less exposed, but a suspect CLOSE lands on a "
            "boundary too, which is why the close test runs in every session"
        ),
        "sessions": n_sessions,
        "sessions_per_symbol": {
            s: len({d for (sym, d) in session_bars if sym == s}) for s in SYMBOLS
        },
        "half_days_flagged_not_dropped": half_days,
        "half_day_policy": (
            "KEPT and flagged, unlike fetch_etf_intraday.py which drops them. That "
            "build drops early closes so a 57-name RTH grid stays exactly "
            "rectangular; here the extended grid is ragged by construction and "
            "rectangularity is not available, so dropping would discard real "
            "sessions for a property that cannot be attained anyway. A 13:00 close "
            "has no 16:00->20:00 window and the consumer must handle that "
            "explicitly rather than inherit a silent drop"
        ),
        "rows": rows,
        "bars_per_symbol": per_symbol,
        "first_bar": first,
        "last_bar": last,
        "zero_volume_bars": zero_volume,
        "zero_volume_rate": zero_volume / rows if rows else 0.0,
        "empty_bar_disclosure": (
            "D192 requires an intraday study on a provider to measure its own "
            "universe's empty-bar rate rather than assume it. Note this rate is NOT "
            "comparable to the RTH fixture's: extended-hours bars are printed only "
            "where something traded, so a thin pre-market slot is absent rather than "
            "zero-volume, and absence shows up in bars-per-session, not here"
        ),
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    META.write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")

    print(f"wrote {FIXTURE.name}: {rows:,} rows, "
          f"{FIXTURE.stat().st_size / 1e6:.1f} MB")
    print(f"  symbols       {len(per_symbol)}/{len(SYMBOLS)}")
    print(f"  sessions      {n_sessions:,}  "
          f"({min(meta['sessions_per_symbol'].values())}-"
          f"{max(meta['sessions_per_symbol'].values())} per symbol)")
    print(f"  bars/session  median {median_bars}, mean {mean_bars:.2f}  "
          f"(RTH-only would be {RTH_SESSION_BARS})")
    print(f"  late bars     {dropped_late:,} dropped (stamped 20:00 or later)")
    print(f"  half-days     {len(half_days)} flagged, NOT dropped")
    print(f"  zero-volume   {zero_volume:,} bars "
          f"({meta['zero_volume_rate'] * 100:.4f}%)")
    print(f"  splits        {n_split_events} events applied to {adjusted_bars:,} bars")
    print(f"  bad prints    {bad_print_census['suspect_bars']:,} suspect bars "
          f"({bad_print_census['suspect_rate'] * 100:.4f}%)  "
          f"by segment {bad_print_census['by_segment']}")
    print(f"                worst raw lower wick "
          f"{bad_print_census['worst_lower_wick_raw'] * 100:,.1f}%")
    print(f"  largest move  {max_move['move'] * 100:.2f}%  "
          f"({max_move['symbol']} {max_move['timestamp']})  [non-suspect bars only]")
    print("\n  GATES")
    print(f"    extended session arrived   "
          f"{'PASS' if gates['extended_session_arrived'] else 'FAIL'}  "
          f"(median {median_bars} bars/session vs {RTH_SESSION_BARS} for RTH; "
          f"pre {anchor_cov['any_pre']:.1%}, post {anchor_cov['any_post']:.1%})")
    print(f"    04:00 and 19:45 bars exist "
          f"{'PASS' if gates['the_04_00_and_19_45_bars_exist'] else 'FAIL'}")
    print(f"    month honoured             "
          f"{'PASS' if gates['month_honoured'] else 'FAIL'} "
          f"({month_violations} foreign bars)")
    print(f"    no unexplained large bar   "
          f"{'PASS' if gates['no_unexplained_large_bar'] else 'FAIL'} "
          f"(threshold {MOVE_LIMIT:.0%})")
    print("\n  CLOCK-ANCHOR COVERAGE (share of sessions printing that exact bar)")
    print(f"    {'':<14}" + "".join(f"{t:>9}" for t in probe_times))
    for sym in SYMBOLS:
        for era in ERAS:
            c = anchor_cov_detail[f"{sym}|{era}"]
            print(f"    {sym + ' ' + era:<14}"
                  + "".join(f"{c[t] * 100:8.1f}%" for t in probe_times))
    if not all((gates["extended_session_arrived"],
                gates["the_04_00_and_19_45_bars_exist"],
                gates["month_honoured"],
                gates["no_unexplained_large_bar"])):
        print("\n  A GATE FAILED. Do not use this fixture. A fixture that quietly "
              "contains\n  regular hours only would be worse than none, because "
              "everything downstream\n  would look fine and be wrong.")
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true", help="cost the job, no network")
    ap.add_argument("--probe", action="store_true",
                    help="4 calls: prove the gates CAN pass before spending 384")
    ap.add_argument("--fetch", action="store_true", help="the long job, resumable")
    ap.add_argument("--actions", action="store_true",
                    help="fetch SPLITS + DIVIDENDS into the events sidecar")
    ap.add_argument("--build", action="store_true", help="cache -> fixture")
    ap.add_argument("--limit", type=int, help="fetch at most N slices this run")
    args = ap.parse_args()
    if args.probe:
        return do_probe()
    if args.actions:
        return do_actions()
    if args.fetch:
        return do_fetch(args.limit)
    if args.build:
        return do_build()
    return do_plan()


if __name__ == "__main__":
    raise SystemExit(main())
