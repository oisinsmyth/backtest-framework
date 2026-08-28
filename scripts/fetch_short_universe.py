"""Fetch a US single-name equity universe FOR SHORT-SIDE RESEARCH, dead names included.

Sibling of `scripts/fetch_etf_holdout.py` and built to its structure (D212 — reuse is
binding): the same `--plan / --fetch / --select / --actions / --build` pipeline, the same
rate limiter, the same cache-first resumability, the same key handling, the same
structural success test on a provider that answers HTTP 200 to its own errors.

    --plan     LISTING_STATUS active + delisted (several snapshots), apply the
               metadata filters, write a PINNED RANDOM ORDER over the eligible pool
    --fetch    TIME_SERIES_DAILY_ADJUSTED for a prefix of that order (cached, resumable)
    --select   apply the pre-live liquidity screen, per symbol
    --actions  derive the SPLITS/DIVIDENDS sidecar from the cache (costs NO requests)
    --build    split-adjust, run the adjustment gates, write fixture + events + meta

NOTHING IN THIS FILE RUNS A STRATEGY, SCORES A CELL OR PROPOSES A RULE.

===========================================================================
WHY THIS FIXTURE EXISTS AND WHAT WOULD MAKE IT WORTHLESS
===========================================================================

**Survivorship bias is not a caveat for a short book, it is the whole measurement.**
D141–D144 measured it on crypto: the strategy's value was concentrated in the assets
that died — 67% of the wrecks beat matched exposure against 45% of the survivors. A
universe of currently-listed US stocks deletes exactly that cohort and would make any
short-side result meaningless in a way no disclaimer repairs.

So the dead cohort is fetched deliberately, from `LISTING_STATUS&state=delisted`, it is
counted in the meta, and `--build` REFUSES to write a fixture whose dead share falls
below `MIN_DEAD_SHARE`. A quietly biased fixture is the worst possible outcome here;
a loud "this cannot be built as specified" is a good one.

===========================================================================
WHAT THE PROVIDER ACTUALLY DOES — measured 2026-08-28, before any of this was designed
===========================================================================

`LISTING_STATUS` documentation is thin, so the two load-bearing facts were probed:

  * **`state=delisted` with no `date` is CUMULATIVE.** It returns every symbol the
    provider has ever seen delisted — 9,449 rows, 7,469 of them `assetType == "Stock"`,
    `delistingDate` spanning 1997-04-01 .. 2026-08-27. Snapshots at earlier dates are
    strict subsets: `delisted@2012-06-29` (183 rows) ⊂ `delisted@2020-06-30` (4,099) ⊂
    the cumulative set. So the per-year snapshots this pipeline queries are NOT how the
    dead cohort is discovered — the cumulative call already has it.

  * **The snapshots are still worth their 16 requests, and by far more than expected.**
    Inclusion is not monotone: symbols present in `delisted@2020-06-30` are ABSENT from
    the cumulative list today, because a ticker recycled by a new issuer drops off the
    current delisted roster. Measured over the 16 yearly snapshots, the union carries
    **8,187 distinct dead `Stock` tickers against 7,469 from the cumulative call alone —
    718 dead names, 9.6% of the cohort, that a single cumulative call does not return.**
    They also make the recycling DETECTABLE, which is what the recycled-ticker rule
    below acts on: 205 symbols turned up carrying two different (ipoDate, delistingDate)
    pairs across snapshots and are dropped rather than guessed at.

  * **Dead tickers really do serve bars.** `TIME_SERIES_DAILY_ADJUSTED` on AABA returns
    5,016 bars ending 2019-11-06, on TWTR 2,260 ending 2022-10-28, on AAI 2,567 ending
    2011-11-30 — each terminating at its delisting date. `SPLITS` and `DIVIDENDS` answer
    for dead names too.

  * **The provider's coverage of PRE-2013 delistings is thin and this is stated rather
    than smoothed over.** `delistingDate` by year: 40 in 2009, 46 in 2010, 76 in 2011,
    55 in 2012 — then 140, 185, 382, 559, 766 through 2017 and roughly 700–1,000 a year
    after. Several hundred US listings die every year in reality. **The dead cohort at
    the start of this fixture's span is materially under-sampled**, and any per-era
    comparison must carry that. The meta records the per-year histogram so a reader can
    see the shape rather than take this sentence on trust.

===========================================================================
ONE REQUEST PER SYMBOL, AND WHY THAT IS STILL THE AS-TRADED FRAME
===========================================================================

`fetch_etf_holdout.py` spends three requests a symbol: `TIME_SERIES_DAILY` for bars,
then `SPLITS` and `DIVIDENDS`. At this universe size that is ~6,000 requests and 90
minutes. `TIME_SERIES_DAILY_ADJUSTED` returns all three in one call, and — measured —
its `1..4` OHLC columns are **as-traded, not adjusted**: AAPL's 1999-11-01 close comes
back 77.62 against an `adjusted close` of 0.58, i.e. the raw columns carry none of the
2000/2005/2014/2020 splits. That is the same frame `TIME_SERIES_DAILY` serves, so D24's
immutability argument and D75's two-frame separation are untouched; only the request
count changes.

**The one thing this costs**, stated because it is a real difference: the inline actions
only cover the window the series itself covers. AABA's `SPLITS` payload lists three
splits; the inline coefficients show two, the missing one being a 1999-02 split before
the series begins. Irrelevant at a 2010 span start, and recorded here rather than
discovered later.

===========================================================================
THE SCREEN. PINNED IN THIS FILE, COMMITTED BEFORE `--select` IS RUN.
===========================================================================

**The screen is PER-SYMBOL PRE-LIVE, and that is the central design judgement.**

`fetch_etf_holdout.py` screens on a fixed calendar window before the parent fixture's
first live bar, which works because that fixture is rectangular and every symbol shares
one warm-up. A short universe cannot be rectangular — requiring every name to be present
on every date is precisely what deletes the dead ones (D245 AMENDMENT 1 hit this: one
delisted fund truncated the whole panel to 880 bars). And a fixed global pre-live window
is worse than useless here: a window before 2010 would delete every company that listed
after 2010, including most of the ones that later died.

So each symbol's screen window is **its own first `SCREEN_BARS` in-span sessions**, and
its live window is everything after. The screen is strictly before the live window for
every symbol individually, it never reads a bar the study would trade, and it touches no
return, drawdown or trade count.

**The price floor is on the SCREEN WINDOW ONLY, and this is what keeps the wrecks in.**
A company trading at $40 in its first year and $0.30 four years later passes — the screen
never sees the $0.30. A floor applied over the whole history would delete the collapses,
which would be selecting on the outcome with extra steps.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import gzip
import io
import json
import math
import os
import random
import statistics
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

KEY_FILE = Path.home() / ".config" / "alphavantage" / "key"
CACHE = REPO / "data" / "raw" / "alphavantage" / "daily_adjusted"
LISTINGS = REPO / "data" / "raw" / "alphavantage" / "listings"
POOL = CACHE / "_pool.json"
SELECTION = CACHE / "_selection.json"
EVENTS_FULL = CACHE / "_events_full.json"  # every selected symbol; --build prunes it

FIXTURE = REPO / "data" / "fixtures" / "us_shorts_daily_raw.csv.gz"
EVENTS = REPO / "data" / "fixtures" / "us_shorts_daily_raw_events.json"
META = REPO / "data" / "fixtures" / "us_shorts_daily_raw.meta.json"

BASE = "https://www.alphavantage.co/query"
REQUESTS_PER_MIN = 66  # the tier ceiling is 75; pace under it with margin
MIN_INTERVAL = 60.0 / REQUESTS_PER_MIN
MAX_CONSECUTIVE_FAILURES = 5
TIMEOUT = 90
BACKOFF_BASE = 2.0  # seconds; doubled per consecutive failure
FETCH_WORKERS = 4   # concurrent requests. The SHARED limiter still gates every start,
                    # so the aggregate never exceeds REQUESTS_PER_MIN. See RateLimiter.

# ---------------------------------------------------------------------------
# THE SPAN
# ---------------------------------------------------------------------------
SPAN_START = "2010-01-04"
SPAN_END = "2026-08-26"

# ---------------------------------------------------------------------------
# THE UNIVERSE RULE — metadata only. No price, no volume, no return.
# ---------------------------------------------------------------------------

# `state=delisted&date=...` snapshots. Redundant with the cumulative call by
# construction (see the header), queried anyway to recover recycled tickers and to
# make the recycling visible.
SNAPSHOT_DATES = tuple(f"{y}-06-30" for y in range(2011, 2027))

# THE EXCLUSION RULE, stated once and repeated verbatim into the meta.
#
# `assetType == "Stock"` is NOT common stock. The provider files warrants, units,
# rights and every preferred series under it: 'AA-W', 'AAC-U', '-P-HIZ' and 627
# five-letter tickers ending 'U' are all `Stock` in the active/delisted CSVs.
#
#   (1) any symbol containing a hyphen is excluded. The hyphen is the provider's
#       marker for a non-ordinary line or a share class: -W/-WS warrants, -U/-UN
#       units, -R rights, -P-x preferred series, -CL called. This is deliberately
#       BLUNTER than necessary — it also drops the ~40 hyphenated dual-class
#       ordinary lines (the -A/-B pairs). That cost is paid on purpose: an
#       unambiguous rule that a reader can apply by eye is worth more here than
#       forty names, and the alternative is a suffix allow-list that will be wrong
#       in a way nobody notices.
#   (2) a FIVE-letter symbol whose fifth character is W, U or R is excluded —
#       the NASDAQ fifth-letter convention for warrant, unit and right.
#   (3) fifth letter 'Q' is KEPT. Q means the issuer is in bankruptcy. It is
#       common stock, and for a short-side fixture it is the single most relevant
#       cohort on the tape. Excluding it would be the survivorship bias this
#       fixture exists to avoid, wearing a tidiness costume.
EXCLUDE_FIFTH_LETTERS = ("W", "U", "R")

# Minimum overlap between the symbol's listed life and the span, in CALENDAR days.
# Applied identically to live and dead names, from dates alone. It saves requests on
# names that cannot clear the bar screen anyway, and its per-cohort cost is reported
# rather than assumed small.
MIN_OVERLAP_DAYS = 550

# ---------------------------------------------------------------------------
# THE ROSTER-REFRESH ARTEFACT. Found by a test, kept because it is real.
#
# `delistingDate` is NOT always a delisting date. **601 of the 9,449 delisted rows —
# 6.4% of the whole dead cohort — carry 2026-08-27**, the day the roster was pulled.
# The next largest single date is 2026-05-28 with 54. Six hundred companies did not
# delist on one Thursday; the provider stamps the refresh date on names it has just
# dropped, in batches.
#
# Two consequences, handled rather than smoothed over:
#
#   (1) A symbol whose `delistingDate` is AFTER `SPAN_END` was listed for the whole
#       span, so it is `alive` FOR THIS FIXTURE whatever the roster says today. Its
#       delisting, real or stamped, happens outside the data.
#
#   (2) A symbol whose `delistingDate` is inside the span but whose bars keep coming
#       for weeks afterwards is a PROVIDER CONTRADICTION — LTCH is stamped 2026-05-28
#       and trades through 2026-08-26. The two records disagree about when it stopped
#       trading and there is no way to tell from here which is right. Those are
#       DROPPED and counted. A mislabel in either direction corrupts the one split
#       this fixture exists to support, and a dropped name that is reported is much
#       cheaper than a wrong label that is not.
DELISTING_CONTRADICTION_DAYS = 10

# The permutation seed. The eligible pool is shuffled ONCE with this seed and the
# fetch takes a PREFIX. Growing the budget extends the prefix; it never re-picks.
# That is the property that makes the pool honest: no symbol enters or leaves
# because of anything learned after the shuffle.
POOL_SEED = 20260828

# Sized from a 250-symbol PILOT off the front of the same permutation: 118 of 250
# cleared the screen, a 47.2% pass rate, so ~3,400 fetched lands ~1,600 selected inside
# the 1,500-2,500 target. **The pilot sized the budget; it did not touch the screen**,
# which is pinned above and was written before the pilot ran. The pilot's 250 are the
# first 250 of this same prefix, so nothing is re-picked and nothing is re-fetched.
POOL_SIZE = 3400

# ---------------------------------------------------------------------------
# THE SCREEN — pre-live, per symbol. See the header for why it is per-symbol.
# ---------------------------------------------------------------------------
SCREEN_BARS = 252            # each symbol's first 252 in-span sessions = its warm-up
MIN_LIVE_BARS = 126          # and at least ~6 months of bars AFTER that window
LIQUIDITY_FLOOR_USD = 1_000_000.0   # median close x volume over the screen window
MIN_SCREEN_PRICE_USD = 3.00         # median close over the screen window

# ---------------------------------------------------------------------------
# THE REFUSAL. A fixture whose dead cohort is thinner than this is not a short-side
# fixture, and `--build` stops rather than writing something misleading.
# ---------------------------------------------------------------------------
MIN_DEAD_SHARE = 0.15

# ---------------------------------------------------------------------------
# THE ADJUSTMENT GATES
# ---------------------------------------------------------------------------
# GATE A. Every sidecar split with |ratio| far from 1 and an effective date inside a
# symbol's own bars must leave NO discontinuity behind. This tests the adjustment
# directly rather than testing a proxy for it.
GATE_A_MIN_RATIO = 1.5
GATE_A_TOLERANCE = 0.50

# A provider split coefficient is checked against the price series only when it is at
# least this far from 1. See `do_actions` -- below the band the check cannot decide,
# above it the check is what stops a 66x artefact reaching the fixture.
CONFIRMATION_MIN_RATIO = 1.25

# GATE B. No adjusted bar-to-bar close ratio at or above this, anywhere, except on the
# documented list. An unadjusted 1:20 reverse split shows as x20; D226 found one as a
# +1,772% single bar that would have dominated an entire study.
#
# The gate is ASYMMETRIC on purpose. Upward: a x4 single-day move in a US common stock
# is rare enough to inspect one by one. Downward: an 80% single-day loss is a real and
# frequent event in this universe — bankruptcies, fraud disclosures, failed trials —
# and it is EXACTLY the signal a short book exists to capture. Gating hard on the
# downside would delete the payload.
GATE_B_UP_RATIO = 4.0
GATE_B_DOWN_RATIO = 0.15  # reported, never fatal

# ---------------------------------------------------------------------------
# THE CLASSIFIER. The first full build made an allow-list untenable and taught what
# to do instead.
#
# 1,580 symbols over 16 years produced 25 up-moves at or above x4, and they fell into
# THREE classes with different right answers, not one:
#
#   REVERT — a single bad print, and the price is back where it started next session.
#       PRMW 7.65 -> 0.75 -> 7.96 (2012-11-01); ARTC 24.40 -> 6.24 -> 25.45;
#       MIL 12.64 -> 105.80 -> 11.48 on the Flash Crash. **These are LEFT IN.** D6 says
#       the fixture stores RAW bars and D25's `clean()` removes spike-and-revert prints
#       at load; deleting them here would deviate from the convention every other
#       fixture in this repo follows, and would do it silently.
#
#   CORROBORATED — an enormous move carried by an enormous change in DOLLAR volume.
#       GLSI 5.20 -> 57.10 on 18.0M shares against 9.4k (GP2 trial data);
#       KRTX 17.68 -> 96.00 on 15.0M against 60k; CYCN on 258M against 27k;
#       KODK's government loan at x2,000 dollar volume. **Retained**, and listed.
#
#   UNEXPLAINED — a PERSISTENT step with no volume behind it. ORIG 0.08 -> 24.00, a
#       x300 move on x9.7 dollar volume: Ocean Rig's post-restructuring reverse split,
#       which the provider records NO coefficient for. GOTU 3.60 -> 24.97 as volume
#       collapses 1,039,092 -> 1,460, an ADS ratio change. EAR 2.57 -> 70.50 on three
#       consecutive ZERO-volume bars. **These are unrecorded corporate actions and bad
#       data, `clean()` will not remove them because they do not revert, and the SYMBOL
#       IS EXCLUDED.**
#
# The two constants below are the boundaries between those classes. Both were chosen
# after seeing the distribution, which is stated plainly rather than dressed up — but
# the separation they sit in is wide, not marginal:
#
#   * dollar-volume ratio: the unexplained cluster runs x0.0, x0.7, x1.4, x4.7, x8.4,
#     x9.7, x10.7; the corroborated cluster runs x33.7, x172, x486, x1,357, x2,000,
#     x2,283, x3,992, x5,014, x21,065, x38,595. The line goes in the gap.
#   * ratio ceiling: no corroborated event in the whole universe exceeds x11 (GLSI at
#     x10.98). x20 in one session is not a market move in US common stock.
#
# **Every x4-or-greater bar, its class, and its dollar-volume ratio go into the meta**,
# so a reader can move either line and see exactly which symbols change hands.
REVERT_BAND = 1.5              # "the price came back": within a factor of 1.5
CORROBORATION_DOLLAR_VOLUME = 20.0   # a real event moves dollar volume by at least this
IMPLAUSIBLE_RATIO = 20.0       # above this, not a market move, whatever the volume
BASELINE_WINDOW = 21           # trailing sessions the volume baseline is a median of

# A move spanning a long absence of bars is NOT a one-day return, whatever its size.
# VRM's series stops 2024-11-29 and resumes 2025-02-20 across a Chapter 11 trading
# suspension; the x6.19 between those two bars is a reorganised capital structure, not
# a day's trading, and it arrived on 34,165 shares. Halt crossings are reported
# separately, are not GATE B failures, and the downstream loader is told to treat a
# symbol carrying one as segmented rather than continuous.
HALT_GAP_DAYS = 21

# Only bar-to-bar moves larger than this are retained for the meta's "largest 25"
# list. Purely a reporting bound -- neither gate reads it.
MOVE_REPORT_FLOOR = 0.5

# Large moves verified BY HAND against the bars around them, before the classifier
# above existed. They are no longer an exemption list -- the classifier decides -- and
# they are better than one: the build ASSERTS that every entry here comes back
# `corroborated`. If the mechanical rule and the hand inspection ever disagree, one of
# them is wrong and the build says so. Same spirit as
# `test_etf_intraday_fixture.EXPECTED_SPLITS` pinning twelve splits by name.
DOCUMENTED_LARGE_MOVES: dict[tuple[str, str], str] = {
    ("KODK", "2020-07-29"): (
        "Eastman Kodak: the $765M DFC loan announcement. 2.62 -> 7.94 -> 33.20 over "
        "three sessions on 272M shares against an 80k baseline, intraday high 60.00, "
        "retraced to 14.94 inside a week. THE ONE THAT CORRECTED THE CLASSIFIER: read "
        "against the immediately preceding bar its dollar volume ratio is only x4.3, "
        "because the 28th was already a 264M-share day. That is why the baseline is a "
        "trailing median."),
    ("TLMD", "2022-02-03"): (
        "SOC Telemed: all-cash acquisition announced. 0.64 -> 2.85 on 24.8M shares "
        "against 370k, then PINNED flat at 2.83-2.93 for days — the signature of a "
        "price converging on a deal value, which a split does not produce."),
    ("VSA", "2025-01-31"): (
        "Micro-cap squeeze. 0.18 -> 0.78 on 727M shares against 1.4M, intraday "
        "0.38-1.34, fully retraced to 0.48 within five sessions. A split does not "
        "retrace."),
    ("GLSI", "2020-12-09"): (
        "Greenwich LifeSciences GP2 trial data. 5.20 -> 57.10 on 18.0M shares against "
        "9,394, and it went on to 72.22 the next session rather than reverting."),
    ("KRTX", "2019-11-18"): (
        "Karuna Therapeutics KarXT phase-2 readout. 17.68 -> 96.00 on 15.0M shares "
        "against 60,050, then 123.99."),
    ("HKD", "2022-09-14"): (
        "AMTD Digital, the 2022 low-float squeeze. 46.00 -> 189.42 on 1.53M shares "
        "against 36,630."),
}


def api_key() -> str:
    """Env first, then the file OUTSIDE the repo. The key is never logged, never
    inlined, and never written into an artifact."""
    key = os.environ.get("ALPHAVANTAGE_API_KEY")
    if key:
        return key.strip()
    if KEY_FILE.exists():
        return KEY_FILE.read_text(encoding="utf-8").strip()
    raise SystemExit(f"No API key. Set ALPHAVANTAGE_API_KEY or create {KEY_FILE}.")


class RateLimiter:
    """A plain floor on the gap between request STARTS. A fetcher that never trips the
    limit is faster than one that trips it and backs off, and politer.

    **Lock-protected, because this fetcher is concurrent and the template's is not.**
    A full daily history is a few hundred kilobytes, so a sequential loop measured
    35 requests/minute against the 66 it was pacing for -- download time dominated, and
    3,400 symbols would have been 97 minutes of it. `FETCH_WORKERS` requests are
    therefore in flight at once, and the limiter still gates the START of every one of
    them, so the aggregate rate cannot exceed `REQUESTS_PER_MIN` however many workers
    run. The ceiling is respected; only the idle time between responses is removed."""

    def __init__(self, min_interval: float) -> None:
        self.min_interval = min_interval
        self.last = 0.0
        self._lock = threading.Lock()

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            start = max(now, self.last + self.min_interval)
            self.last = start
        delay = start - time.monotonic()
        if delay > 0:
            time.sleep(delay)


def _get(params: dict, key: str, limiter: RateLimiter) -> str:
    limiter.wait()
    url = BASE + "?" + urllib.parse.urlencode({**params, "apikey": key})
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
            return r.read().decode("utf-8", "replace")
    except Exception as exc:  # noqa: BLE001
        # Re-raise WITHOUT the URL. urllib puts the full URL into HTTPError.__str__
        # on some paths and the key is in it; a traceback is an artifact too.
        raise type(exc)(f"{type(exc).__name__} on {params.get('function')} "
                        f"{params.get('symbol', params.get('date', ''))} [url redacted]") from None


# ---------------------------------------------------------------------------
# --plan
# ---------------------------------------------------------------------------

def _listing(params: dict, tag: str, key: str, limiter: RateLimiter) -> list[dict]:
    """Cached LISTING_STATUS call. The listing CSVs are point-in-time facts about the
    provider's roster, so caching them makes `--plan` reproducible offline."""
    LISTINGS.mkdir(parents=True, exist_ok=True)
    path = LISTINGS / f"{tag}.csv.gz"
    if path.exists():
        with gzip.open(path, "rt", encoding="utf-8") as f:
            body = f.read()
    else:
        body = _get({"function": "LISTING_STATUS", **params}, key, limiter)
        if not body.lstrip().startswith("symbol"):
            raise ValueError(f"LISTING_STATUS {tag} did not return CSV: {body[:120]}")
        with gzip.open(path, "wt", encoding="utf-8") as f:
            f.write(body)
    return list(csv.DictReader(io.StringIO(body)))


def _is_common_stock_ticker(sym: str) -> bool:
    """The exclusion rule, in one function so the test can call exactly what runs."""
    if "-" in sym:
        return False
    if len(sym) == 5 and sym[4] in EXCLUDE_FIFTH_LETTERS:
        return False
    return bool(sym) and sym.isalpha()


def _overlap_days(ipo: str, delisting: str | None) -> int:
    lo = max(ipo, SPAN_START)
    hi = min(delisting or SPAN_END, SPAN_END)
    if hi <= lo:
        return 0
    return (date.fromisoformat(hi) - date.fromisoformat(lo)).days


def do_plan(key: str, limiter: RateLimiter) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)

    active = _listing({"state": "active"}, "active_current", key, limiter)
    dead_rows = _listing({"state": "delisted"}, "delisted_cumulative", key, limiter)
    for d in SNAPSHOT_DATES:
        dead_rows += _listing({"state": "delisted", "date": d}, f"delisted_{d}", key, limiter)

    active_stock = {r["symbol"]: r for r in active if r["assetType"] == "Stock"}

    # Collapse the dead rows. A symbol carrying two DIFFERENT (ipo, delisting) pairs
    # across the snapshots has been recycled by a second issuer, and its bar series
    # cannot be attributed to one company. Those are dropped, not guessed at.
    dead_variants: dict[str, set[tuple[str, str]]] = {}
    for r in dead_rows:
        if r["assetType"] != "Stock":
            continue
        dead_variants.setdefault(r["symbol"], set()).add((r["ipoDate"], r["delistingDate"]))
    dead_stock = {s: v for s, v in dead_variants.items()}

    recycled_multi = {s for s, v in dead_stock.items() if len(v) > 1}
    recycled_relisted = set(dead_stock) & set(active_stock)
    recycled = recycled_multi | recycled_relisted

    counts = Counter()
    eligible: list[dict] = []

    def consider(sym: str, name: str, exch: str, ipo: str, delisting: str | None, cohort: str) -> None:
        counts[f"{cohort}:seen"] += 1
        if sym in recycled:
            counts[f"{cohort}:recycled ticker"] += 1
            return
        if not _is_common_stock_ticker(sym):
            counts[f"{cohort}:not common stock by ticker"] += 1
            return
        if not ipo or ipo == "null":
            counts[f"{cohort}:no ipoDate"] += 1
            return
        if _overlap_days(ipo, delisting) < MIN_OVERLAP_DAYS:
            counts[f"{cohort}:span overlap < {MIN_OVERLAP_DAYS}d"] += 1
            return
        counts[f"{cohort}:ELIGIBLE"] += 1
        eligible.append({"symbol": sym, "name": name, "exchange": exch, "ipoDate": ipo,
                         "delistingDate": delisting, "cohort": cohort})

    for sym, r in active_stock.items():
        consider(sym, r["name"], r["exchange"], r["ipoDate"], None, "alive")

    dead_meta = {r["symbol"]: r for r in dead_rows if r["assetType"] == "Stock"}
    for sym, variants in dead_stock.items():
        ipo, delisting = sorted(variants)[0]
        r = dead_meta[sym]
        consider(sym, r["name"], r["exchange"], ipo,
                 None if delisting in ("", "null") else delisting, "dead")

    # THE PINNED PERMUTATION. Shuffled once, here, before a single bar is fetched.
    eligible.sort(key=lambda e: e["symbol"])       # deterministic input to the shuffle
    random.Random(POOL_SEED).shuffle(eligible)

    delisting_hist = Counter(
        e["delistingDate"][:4] for e in eligible if e["cohort"] == "dead" and e["delistingDate"]
    )
    POOL.write_text(json.dumps({
        "order": eligible,
        "seed": POOL_SEED,
        "pool_size": POOL_SIZE,
        "counts": dict(sorted(counts.items())),
        "recycled_tickers": sorted(recycled),
        "delistings_by_year_eligible": dict(sorted(delisting_hist.items())),
    }, indent=1), encoding="utf-8")

    prefix = eligible[:POOL_SIZE]
    n_dead = sum(1 for e in eligible if e["cohort"] == "dead")
    p_dead = sum(1 for e in prefix if e["cohort"] == "dead")
    print(f"active listings          {len(active):,}   ({len(active_stock):,} assetType=Stock)")
    print(f"delisted rows (all snaps){len(dead_rows):,}   ({len(dead_stock):,} distinct dead Stock tickers)")
    print(f"recycled tickers dropped {len(recycled):,}   "
          f"({len(recycled_relisted):,} re-listed, {len(recycled_multi):,} multi-variant)")
    for k, v in sorted(counts.items()):
        print(f"  {k:44s} {v:6,}")
    print(f"\nELIGIBLE POOL            {len(eligible):,}   dead {n_dead:,} ({n_dead/len(eligible):.1%})")
    print(f"PREFIX TO FETCH          {len(prefix):,}   dead {p_dead:,} ({p_dead/len(prefix):.1%})")
    print(f"estimated fetch          {len(prefix)/REQUESTS_PER_MIN:.1f} min at {REQUESTS_PER_MIN}/min")
    print("\ndelistings by year, eligible pool:")
    print("  " + "  ".join(f"{y}:{n}" for y, n in sorted(delisting_hist.items())))


# ---------------------------------------------------------------------------
# --fetch
# ---------------------------------------------------------------------------

def daily_path(symbol: str) -> Path:
    return CACHE / f"{symbol}.json.gz"


class UnknownSymbol(ValueError):
    """The provider does not serve this ticker at all, and never will.

    Distinguished from a transport failure because the two want opposite handling: a
    network error should be retried, an `Error Message` should be REMEMBERED. Eleven of
    the 2,600 first-prefix symbols answer this way — mostly names whose daily endpoint
    disagrees with the listing roster — and without a negative cache every subsequent
    run retries all eleven up front and trips the five-consecutive-failure guard before
    reaching a single new symbol. That is exactly what happened on the first extension
    of the prefix, and it is the same fix `fetch_etf_intraday.py` uses when it caches an
    empty month: a symbol the provider will not serve is a FACT, not an error."""


def _fetch_one(sym: str, key: str, limiter: RateLimiter) -> None:
    body = _get({"function": "TIME_SERIES_DAILY_ADJUSTED", "symbol": sym,
                 "outputsize": "full"}, key, limiter)
    payload = json.loads(body)
    # Alpha Vantage answers HTTP 200 to its own errors, so success is decided
    # STRUCTURALLY: no series key means failure however healthy the status line
    # looks. Writing an error body into a cache is the failure this guards.
    if "Time Series (Daily)" not in payload:
        if "Error Message" in payload:
            raise UnknownSymbol(str(payload)[:120])
        raise ValueError(str(payload)[:120])
    tmp = daily_path(sym).with_suffix(".part")
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        json.dump(payload["Time Series (Daily)"], f)
    tmp.replace(daily_path(sym))  # atomic: a killed run never leaves a truncated cache


def _prefix(limit: int | None) -> list[dict]:
    """The pool prefix. The PERMUTATION comes from the pool file, written once by
    `--plan`; the LENGTH comes from the module constant, so raising `POOL_SIZE` extends
    the prefix without re-planning and without re-picking a single symbol. Reading the
    length back out of the pool file instead silently pinned the budget to whatever it
    was when `--plan` last ran, which is how the first full fetch stopped at 2,600."""
    pool = json.loads(POOL.read_text(encoding="utf-8"))
    return pool["order"][: (limit or POOL_SIZE)]


def _known_misses() -> set[str]:
    p = CACHE / "_known_misses.json"
    return set(json.loads(p.read_text(encoding="utf-8"))) if p.exists() else set()


def do_fetch(key: str, limiter: RateLimiter, limit: int | None) -> None:
    prefix = _prefix(limit)
    known = _known_misses()
    todo = [p["symbol"] for p in prefix
            if not daily_path(p["symbol"]).exists() and p["symbol"] not in known]
    print(f"prefix {len(prefix):,}  cached "
          f"{sum(1 for p in prefix if daily_path(p['symbol']).exists()):,}  "
          f"known-unserved {len(known & {p['symbol'] for p in prefix}):,}  "
          f"to fetch {len(todo):,}  workers {FETCH_WORKERS}")

    state = {"done": 0, "consecutive": 0, "missed": [], "unknown": [], "stop": False}
    lock = threading.Lock()
    t0 = time.time()

    def worker(sym: str) -> None:
        with lock:
            if state["stop"]:
                return
        try:
            _fetch_one(sym, key, limiter)
        except UnknownSymbol:
            # A permanent, symbol-specific NO. Recorded so the next run does not ask
            # again -- but still counted toward the consecutive-failure guard, because
            # a provider-wide outage answering `Error Message` to everything must still
            # stop the run rather than being written off as 3,400 unknown tickers.
            with lock:
                state["consecutive"] += 1
                n = state["consecutive"]
                state["missed"].append(sym)
                state["unknown"].append(sym)
                if n >= MAX_CONSECUTIVE_FAILURES:
                    state["stop"] = True
            print(f"  UNSERVED {sym} (recorded; will not be asked again)", flush=True)
            return
        except (urllib.error.URLError, ValueError, TimeoutError, OSError) as e:
            with lock:
                state["consecutive"] += 1
                n = state["consecutive"]
                state["missed"].append(sym)
                if n >= MAX_CONSECUTIVE_FAILURES:
                    state["stop"] = True
            print(f"  MISS {sym}: {str(e)[:90]}", flush=True)
            # Exponential backoff, taken by the failing worker so the others keep
            # the pipe warm while the provider is given room.
            time.sleep(BACKOFF_BASE * (2 ** (min(n, 5) - 1)))
            return
        with lock:
            state["consecutive"] = 0
            state["done"] += 1
            done = state["done"]
        if done % 200 == 0:
            rate = done / (time.time() - t0) * 60
            left = (len(todo) - done) / max(rate, 1e-9)
            print(f"  {done:,}/{len(todo):,}  {rate:.0f}/min  ~{left:.1f} min left", flush=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=FETCH_WORKERS) as pool_exec:
        list(pool_exec.map(worker, todo))

    missed = state["missed"]
    print(f"fetched {state['done']:,} in {(time.time() - t0)/60:.1f} min; "
          f"{len(missed)} missed ({len(state['unknown'])} unserved by the provider)")
    if state["unknown"]:
        (CACHE / "_known_misses.json").write_text(
            json.dumps(sorted(known | set(state["unknown"])), indent=1), encoding="utf-8")
    if missed:
        (CACHE / "_fetch_misses.json").write_text(
            json.dumps(sorted(set(missed) | _known_misses()), indent=1), encoding="utf-8")
    if state["stop"]:
        raise SystemExit(
            f"{MAX_CONSECUTIVE_FAILURES} consecutive failures -- stopped rather than "
            f"hammering the API. Re-run to resume from the cache."
        )


# ---------------------------------------------------------------------------
# --select
# ---------------------------------------------------------------------------

def _load_series(sym: str) -> dict:
    with gzip.open(daily_path(sym), "rt", encoding="utf-8") as f:
        return json.load(f)


def apply_screen(series: dict) -> tuple[dict | None, str | None]:
    """THE SCREEN, as one pure function of one symbol's raw provider series.

    Returns `(verdict, None)` or `(None, reason)`.

    **It reads `series` only at `dates[:SCREEN_BARS]` and never past it.** That is the
    property the whole fixture rests on, and it is a property of these fifteen lines
    rather than of a calendar constant, which is why the function is separated out:
    `test_us_shorts_fixture.py` calls exactly this, hands it a series whose screen
    window and live window disagree violently about liquidity and price, and asserts
    the verdict tracks the screen window alone."""
    dates = sorted(d for d in series if SPAN_START <= d <= SPAN_END)
    if len(dates) < SCREEN_BARS + MIN_LIVE_BARS:
        return None, f"< {SCREEN_BARS + MIN_LIVE_BARS} in-span bars"
    screen = dates[:SCREEN_BARS]
    closes = [float(series[d]["4. close"]) for d in screen]
    dollars = [c * float(series[d]["6. volume"]) for c, d in zip(closes, screen)]
    med_close, med_dollars = statistics.median(closes), statistics.median(dollars)
    if med_close < MIN_SCREEN_PRICE_USD:
        return None, f"screen median close < ${MIN_SCREEN_PRICE_USD:.2f}"
    if med_dollars < LIQUIDITY_FLOOR_USD:
        return None, f"screen median $vol < ${LIQUIDITY_FLOOR_USD/1e6:.0f}M"
    return {
        "first_bar": dates[0], "last_bar": dates[-1], "n_bars": len(dates),
        "screen_start": screen[0], "screen_end": screen[-1],
        "live_start": dates[SCREEN_BARS], "n_live_bars": len(dates) - SCREEN_BARS,
        "screen_median_close": round(med_close, 4),
        "screen_median_dollar_volume": round(med_dollars, 1),
    }, None


def do_select(limit: int | None = None) -> None:
    """The pinned pre-live screen, applied per symbol. Reads no bar the study trades.

    `limit` shortens the PREFIX, never the screen. It exists so the pass rate can be
    estimated from a pilot before committing forty minutes of requests -- sizing the
    budget, not tuning the criterion, which is already pinned above."""
    prefix = _prefix(limit)
    kept, rejected = [], Counter()
    reclassified: list[str] = []
    contradictions: list[dict] = []
    for p in prefix:
        sym = p["symbol"]
        if not daily_path(sym).exists():
            rejected[f"{p['cohort']}:no cached bars"] += 1
            continue
        verdict, reason = apply_screen(_load_series(sym))
        if verdict is None:
            rejected[f"{p['cohort']}:{reason}"] += 1
            continue

        # The roster-refresh artefact, resolved against the bars. See the constant.
        cohort, note = p["cohort"], None
        dl = p["delistingDate"]
        if cohort == "dead" and dl:
            if dl > SPAN_END:
                cohort, note = "alive", (
                    f"delistingDate {dl} falls after the span end {SPAN_END}; listed for "
                    f"the whole span, so counted alive HERE regardless of the roster")
                reclassified.append(sym)
            else:
                cutoff = (date.fromisoformat(dl)
                          + timedelta(days=DELISTING_CONTRADICTION_DAYS)).isoformat()
                if verdict["last_bar"] > cutoff:
                    rejected["dead:provider contradiction (bars outlive delistingDate)"] += 1
                    contradictions.append({"symbol": sym, "delistingDate": dl,
                                           "last_bar": verdict["last_bar"]})
                    continue
        kept.append({**p, **verdict, "cohort": cohort, "cohort_note": note})

    kept.sort(key=lambda r: r["symbol"])
    n_dead = sum(1 for r in kept if r["cohort"] == "dead")
    SELECTION.write_text(json.dumps({
        "selected": kept,
        "rejected": dict(sorted(rejected.items())),
        "screen": {
            "kind": "PER-SYMBOL PRE-LIVE. Each symbol's screen window is its own first "
                    f"{SCREEN_BARS} in-span sessions; its live window is every bar after. "
                    "The screen reads no bar inside any symbol's live window.",
            "screen_bars": SCREEN_BARS,
            "min_live_bars": MIN_LIVE_BARS,
            "liquidity_floor_usd": LIQUIDITY_FLOOR_USD,
            "min_screen_price_usd": MIN_SCREEN_PRICE_USD,
            "metric": "median(close x volume) and median(close) over the screen window",
            "committed_before_run": True,
        },
        # A documented "could not obtain" is evidence; a silent omission is the bias
        # itself (`fetch_crypto_universe.py`, D140). The provider answers HTTP 200 with
        # an `Error Message` for a symbol its daily endpoint does not know, and those
        # names are named here rather than quietly absent from the pool.
        "fetch_failures": sorted(
            json.loads((CACHE / "_fetch_misses.json").read_text(encoding="utf-8"))
        ) if (CACHE / "_fetch_misses.json").exists() else [],
        "roster_refresh_artefact": {
            "finding": ("601 of the provider's 9,449 delisted rows carry delistingDate "
                        "2026-08-27, the day the roster was pulled; the next largest "
                        "single date is 2026-05-28 with 54. That is a batch refresh "
                        "stamp, not 601 same-day delistings."),
            "reclassified_alive_delisting_after_span_end": reclassified,
            "dropped_provider_contradiction": contradictions,
            "contradiction_tolerance_days": DELISTING_CONTRADICTION_DAYS,
        },
    }, indent=1), encoding="utf-8")

    print(f"prefix considered  {len(prefix):,}")
    for k, v in sorted(rejected.items()):
        print(f"  rejected {k:52s} {v:6,}")
    print(f"\nSELECTED           {len(kept):,}")
    print(f"  dead             {n_dead:,} ({n_dead/max(len(kept),1):.1%})")
    print(f"  alive            {len(kept)-n_dead:,}")
    print(f"  roster artefact  {len(reclassified):,} reclassified alive "
          f"(delisted after the span end), {len(contradictions):,} dropped as "
          f"provider contradictions")
    if kept:
        bars = [r["n_bars"] for r in kept]
        print(f"  bars per symbol  min {min(bars):,}  median {statistics.median(bars):,.0f}  max {max(bars):,}")
        print(f"  RAGGED PANEL: {len(set(bars)):,} distinct bar counts")


# ---------------------------------------------------------------------------
# --actions  (derived from the cache; costs NO requests)
# ---------------------------------------------------------------------------

def do_actions() -> None:
    """Derive the events sidecar from the cached daily payloads. Costs NO requests.

    **A recorded split is applied only if the PRICE SERIES corroborates it**, and this
    is the correction the first full build forced. The provider's raw OHLC is as-traded
    for AAPL and demonstrably NOT as-traded for others, and its `8. split coefficient`
    is unreliable in at least three distinct ways:

      * **final-bar artefacts.** RSPP's last bar carries a 0.32 coefficient on ZERO
        volume with the price unchanged at 47.83. FMSA the same, 0.2 on zero volume.
      * **coefficients on continuous prices.** CHMT carries 0.015 on bar 12 of 1,662
        with the close flat at ~15.50; AMRC carries 2.0 on bar 2 with the close flat at
        ~10. Applying either manufactures a 66x or 2x jump where the data has none.
      * **spinoffs modelled as splits.** ADEA's 2022-10-03 coefficient of 3.78 is the
        Xperi separation. The raw price halved, which is what a spinoff does; dividing
        the prior history by 3.78 would turn that into a +92% bar.

    So the test is empirical and one line: **keep the coefficient only if applying it
    moves the effective bar CLOSER to continuity than leaving it out.** D75's precedent
    is exact -- there, too, the provider frame was assumed and the data said otherwise,
    and the data won. Rejected coefficients are written to `_unconfirmed_splits.json`
    with observed against expected, and are NOT carried in the sidecar: a loader that
    applied them would reintroduce precisely the discontinuity this removes.

    **The dividend amounts are converted into the split-adjusted frame here**, by
    dividing each by the same cumulative factor `--build` divides its prices by. D75:
    the two must share one frame or every total-return number computed from them is
    wrong by the split ratio. `fetch_etf_holdout.py` takes the DIVIDENDS endpoint's
    as-declared amounts and labels them split-adjusted; that is not repeated here, and
    the divergence from the template is deliberate rather than accidental."""
    selected = json.loads(SELECTION.read_text(encoding="utf-8"))["selected"]
    out: dict[str, dict[str, list]] = {"dividends": {}, "splits": {}}
    unconfirmed: list[dict] = []
    for r in selected:
        sym = r["symbol"]
        series = _load_series(sym)
        dates = sorted(series)
        idx = {d: i for i, d in enumerate(dates)}
        sp = []
        for d in dates:
            ratio = float(series[d]["8. split coefficient"])
            if ratio == 1.0:
                continue
            i = idx[d]
            if i == 0:
                unconfirmed.append({"symbol": sym, "date": d, "ratio": ratio,
                                    "reason": "no prior bar to test against"})
                continue
            prev_close = float(series[dates[i - 1]]["4. close"])
            observed = (float(series[d]["4. close"]) / prev_close) if prev_close > 0 else float("nan")

            # THE TEST ONLY RUNS WHERE IT CAN DECIDE. A 1.03 stock dividend moves the
            # price by 3% and an ordinary session moves it by more than that, so
            # "did the price jump?" cannot distinguish an applied 1.03 from an
            # unapplied one -- and second-guessing the provider on 2% of noise would
            # be worse than trusting it. Below this band the coefficient is applied as
            # stated; the worst case is a few percent on a single bar. Above it, a
            # wrong call is CHMT's 66x or ACTA's 20x, which is the failure D226 is
            # about, and there the price series is decisive.
            if 1.0 / CONFIRMATION_MIN_RATIO < ratio < CONFIRMATION_MIN_RATIO:
                sp.append([d + "T00:00:00", ratio])
                continue
            # Applying the split multiplies the observed ratio by `ratio` (prices before
            # the effective date are divided by it, the effective bar is not). Keep it
            # only if that lands CLOSER to continuity than leaving it out.
            if observed == observed and \
                    abs(math.log(max(observed * ratio, 1e-12))) < abs(math.log(max(observed, 1e-12))):
                sp.append([d + "T00:00:00", ratio])
            else:
                unconfirmed.append({
                    "symbol": sym, "date": d, "ratio": ratio,
                    "observed_close_ratio": round(observed, 6),
                    "expected_if_real": round(1.0 / ratio, 6),
                    "volume_on_the_bar": float(series[d]["6. volume"]),
                    "bar_index": i, "n_bars": len(dates),
                    "reason": "applying it would CREATE a discontinuity, not remove one",
                })
        dv = []
        for d in dates:
            a = float(series[d]["7. dividend amount"])
            if a != 0.0:
                dv.append([d + "T00:00:00", a / split_factor_at(d, sp)])
        out["splits"][sym] = sp
        out["dividends"][sym] = dv

    # Written to the CACHE, not to the fixture sidecar. `--build` prunes this down to
    # the symbols that survive its data-quality gates and writes the committed sidecar
    # itself. Having `--build` read and rewrite the SAME file made it non-idempotent:
    # the second run saw a sidecar with the excluded symbols' splits already removed,
    # did not apply them, reached a different verdict, and produced a different
    # fixture. A committed artifact must not depend on how many times the builder ran.
    EVENTS_FULL.write_text(json.dumps(out, indent=1, sort_keys=True), encoding="utf-8")
    (CACHE / "_unconfirmed_splits.json").write_text(
        json.dumps(unconfirmed, indent=1), encoding="utf-8")
    n_div = sum(len(v) for v in out["dividends"].values())
    n_spl = sum(len(v) for v in out["splits"].values())
    n_rev = sum(1 for v in out["splits"].values() for _, f in v if f < 1.0)
    print(f"events written (0 API requests): {n_div:,} dividends, {n_spl:,} splits "
          f"({n_rev:,} reverse)")
    print(f"UNCONFIRMED splits dropped: {len(unconfirmed)} -- coefficients the price "
          f"series does not corroborate")
    for u in unconfirmed[:15]:
        print(f"    {u['symbol']:6s} {u['date']}  coef {u['ratio']:<10.6g} "
              f"observed {u.get('observed_close_ratio', float('nan')):<10.4g} "
              f"vol {u.get('volume_on_the_bar', 0):,.0f}")


# ---------------------------------------------------------------------------
# --build
# ---------------------------------------------------------------------------

def _stable_gzip_text(path: Path):
    """A gzip text writer whose bytes are a function of the CONTENT and nothing else.

    Same construction as `backtest_framework.data.csv_fixture._open_text`, and imported
    from nowhere so this script stays a standalone fetcher like its sibling."""
    raw = open(path, "wb")
    binary = gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0)
    return io.TextIOWrapper(binary, encoding="utf-8", newline="")


def split_factor_at(stamp: str, splits: list) -> float:
    """Product of every split ratio effective AFTER this bar.

    PRICES ARE DIVIDED by this and VOLUMES MULTIPLIED, and the opposite directions
    are the point: a 2:1 split halves the price and doubles the share count. D226
    found twelve unadjusted splits in a fixture built without this, the worst showing
    as a +1,772% single bar."""
    factor = 1.0
    for eff, ratio in splits:
        if eff[:10] > stamp[:10]:
            factor *= ratio
    return factor


def do_build() -> None:
    sel = json.loads(SELECTION.read_text(encoding="utf-8"))
    selected = sel["selected"]
    if not EVENTS_FULL.exists():
        raise SystemExit("REFUSING TO BUILD AN UNADJUSTED FIXTURE. Run --actions first.")
    events = json.loads(EVENTS_FULL.read_text(encoding="utf-8"))
    splits_by = events["splits"]
    unconfirmed_splits = json.loads(
        (CACHE / "_unconfirmed_splits.json").read_text(encoding="utf-8")
    ) if (CACHE / "_unconfirmed_splits.json").exists() else []

    n_dead0 = sum(1 for r in selected if r["cohort"] == "dead")
    if n_dead0 / max(len(selected), 1) < MIN_DEAD_SHARE:
        raise SystemExit(
            f"REFUSING TO BUILD. The dead cohort is {n_dead0:,}/{len(selected):,} = "
            f"{n_dead0/max(len(selected),1):.1%}, below the {MIN_DEAD_SHARE:.0%} floor. "
            f"A universe that is materially all survivors deletes the cohort a short "
            f"book earns in (D141-D144), and shipping it with a caveat would be worse "
            f"than shipping nothing. Widen the pool prefix or relax the screen, and "
            f"say which."
        )

    # -----------------------------------------------------------------------
    # PASS 1 -- classify. Nothing is written until every symbol has been judged,
    # because the verdict on one bar decides whether a whole symbol belongs in the
    # fixture and a half-written file would be worse than none.
    # -----------------------------------------------------------------------
    gate_a_failures: list[dict] = []
    classified: list[dict] = []
    halt_crossings: list[dict] = []
    excluded: dict[str, list[dict]] = {}

    for r in selected:
        sym = r["symbol"]
        series = _load_series(sym)
        sp = splits_by.get(sym, [])
        split_dates = {e[:10]: ratio for e, ratio in sp}
        dates = sorted(d for d in series if SPAN_START <= d <= SPAN_END)
        adj_c, adj_dollars = [], []
        for d in dates:
            b = series[d]
            fct = split_factor_at(d, sp)
            c = float(b["4. close"]) / fct
            adj_c.append(c)
            adj_dollars.append(c * float(b["6. volume"]) * fct)

        problems: list[dict] = []
        corroborated_dates: set[str] = set()
        for i in range(1, len(dates)):
            prev, cur, d = adj_c[i - 1], adj_c[i], dates[i]
            if prev <= 0 or cur <= 0:
                continue
            ratio = cur / prev

            if ratio < GATE_B_UP_RATIO:
                continue
            gap = (date.fromisoformat(d) - date.fromisoformat(dates[i - 1])).days
            # THE VOLUME BASELINE IS A TRAILING MEDIAN, NOT THE PREVIOUS BAR, and the
            # correction was forced by KODK. Its 2020-07-29 close is x4.18 on 272M
            # shares, unambiguously the government-loan news -- but the PREVIOUS bar
            # was already a 264M-share day, because the move started on the 28th. Read
            # against that bar the dollar-volume ratio is x4.3 and the classifier calls
            # a famous event unexplained. Read against the quiet weeks before it,
            # x53,000. A multi-day event inflates its own denominator, so the
            # denominator has to come from before the event.
            lo, hi = max(0, i - BASELINE_WINDOW - 2), i - 2
            if hi <= lo:
                lo, hi = 0, i
            base = statistics.median(adj_dollars[lo:hi]) if hi > lo else 0.0
            dv = (adj_dollars[i] / base) if base > 0 else None
            rec = {"symbol": sym, "date": d, "ratio": round(ratio, 3),
                   "dollar_volume_ratio": round(dv, 1) if dv is not None else None,
                   "gap_days": gap, "split_on_this_date": split_dates.get(d)}
            if gap > HALT_GAP_DAYS:
                # Not a one-day return; a suspension or a reorganisation.
                rec["klass"] = "halt_crossing"
                halt_crossings.append(rec)
                continue
            # Did the price simply come back? Either direction of the pair: the
            # offending print may be THIS bar (t+1 returns) or the PREVIOUS one
            # (t returns to t-2, as when a bad down-print is followed by recovery).
            back = []
            if i + 1 < len(adj_c) and prev > 0:
                back.append(adj_c[i + 1] / prev)
            if i >= 2 and adj_c[i - 2] > 0:
                back.append(cur / adj_c[i - 2])
            reverts = any(1.0 / REVERT_BAND <= b_ <= REVERT_BAND for b_ in back)
            if reverts:
                # LEFT IN THE FIXTURE. D6 stores raw bars; D25's `clean()` removes
                # spike-and-revert prints at load. Removing them here would silently
                # depart from the convention every other fixture follows.
                rec["klass"] = "revert"
            elif ratio >= IMPLAUSIBLE_RATIO:
                rec["klass"] = "unexplained"
                rec["why"] = (f"x{ratio:.1f} in one session; no US common stock does "
                              "that, so it is an unrecorded corporate action")
                problems.append(rec)
            elif dv is not None and dv >= CORROBORATION_DOLLAR_VOLUME:
                rec["klass"] = "corroborated"
                corroborated_dates.add(d)
            else:
                rec["klass"] = "unexplained"
                rec["why"] = (f"persistent step on dollar volume "
                              f"x{dv if dv is not None else 0:.1f} against its own trailing "
                              f"median; a real event moves it by orders of magnitude")
                problems.append(rec)
            classified.append(rec)

        # GATE A runs AFTER the classifier so it can defer to it. A split date can
        # carry a genuine event on top of the split -- TAOP's 2020-07-30 is a 1:6
        # reverse AND a x4.3 move on 109M shares against 563k -- and there the
        # adjustment DID take; the residual is the market, not a defect.
        for i in range(1, len(dates)):
            d = dates[i]
            if d not in split_dates or d in corroborated_dates:
                continue
            rr = split_dates[d]
            if not (rr >= GATE_A_MIN_RATIO or rr <= 1.0 / GATE_A_MIN_RATIO):
                continue
            if adj_c[i - 1] <= 0 or adj_c[i] <= 0:
                continue
            ratio = adj_c[i] / adj_c[i - 1]
            if abs(ratio - 1.0) > GATE_A_TOLERANCE:
                rec = {"symbol": sym, "date": d, "split_ratio": rr,
                       "adjusted_ratio": round(ratio, 4),
                       "why": "a confirmed split still leaves a discontinuity"}
                gate_a_failures.append(rec)
                problems.append(rec)

        if problems:
            excluded[sym] = problems

    # The hand-verified list is now a CROSS-CHECK on the classifier rather than an
    # exemption from it. Disagreement means one of the two is wrong.
    by_key = {(c["symbol"], c["date"]): c for c in classified}
    for key, why in DOCUMENTED_LARGE_MOVES.items():
        c = by_key.get(key)
        if c is None or c["klass"] != "corroborated":
            raise SystemExit(
                f"DOCUMENTED_LARGE_MOVES disagrees with the classifier at {key}: "
                f"hand-verified as a real event ({why[:60]}...) but classified "
                f"{c['klass'] if c else 'ABSENT'}. Resolve before building."
            )

    keep = [r for r in selected if r["symbol"] not in excluded]
    n_dead = sum(1 for r in keep if r["cohort"] == "dead")
    dead_share = n_dead / max(len(keep), 1)
    if dead_share < MIN_DEAD_SHARE:
        raise SystemExit(
            f"REFUSING TO BUILD. After data-quality exclusions the dead cohort is "
            f"{n_dead:,}/{len(keep):,} = {dead_share:.1%}, below the "
            f"{MIN_DEAD_SHARE:.0%} floor."
        )

    # -----------------------------------------------------------------------
    # PASS 2 -- write.
    # -----------------------------------------------------------------------
    rows = 0
    adjusted_bars = 0
    moves: list[tuple[float, str, str]] = []
    big_drops: list[dict] = []
    per_symbol: dict[str, dict] = {}
    selected = keep

    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    # mtime=0 and no embedded filename, matching `csv_fixture._open_text`: gzip stamps
    # the current time into its header, so an otherwise-identical rebuild would produce
    # a whole-file diff -- and a diff that always appears is a diff that stops being
    # read. The point of committing a fixture is that changing it is VISIBLE (D70/D24).
    with _stable_gzip_text(FIXTURE) as fh:
        w = csv.writer(fh)
        w.writerow(["timestamp", "symbol", "open", "high", "low", "close", "volume"])
        for r in selected:
            sym = r["symbol"]
            series = _load_series(sym)
            sp = splits_by.get(sym, [])
            dates = sorted(d for d in series if SPAN_START <= d <= SPAN_END)
            split_dates = {e[:10]: ratio for e, ratio in sp}
            prev = None
            prev_date = None
            prev_dollars = 0.0
            peak = 0.0
            last_close = 0.0
            max_gap = 0
            for d in dates:
                b = series[d]
                fct = split_factor_at(d, sp)
                if fct != 1.0:
                    adjusted_bars += 1
                o = float(b["1. open"]) / fct
                h = float(b["2. high"]) / fct
                lo = float(b["3. low"]) / fct
                c = float(b["4. close"]) / fct
                v = float(b["6. volume"]) * fct
                dollars = c * v
                if prev and prev > 0 and c > 0:
                    ratio = c / prev
                    gap = (date.fromisoformat(d) - date.fromisoformat(prev_date)).days
                    max_gap = max(max_gap, gap)
                    # Only candidates for the "largest 25" list are retained. Keeping
                    # every bar-to-bar ratio would be several million tuples held in
                    # memory to report twenty-five of them.
                    if abs(ratio - 1.0) > MOVE_REPORT_FLOOR:
                        moves.append((ratio, sym, d))
                    if ratio <= GATE_B_DOWN_RATIO:
                        big_drops.append({"symbol": sym, "date": d, "ratio": round(ratio, 4)})
                prev = c
                prev_date = d
                prev_dollars = dollars
                peak = max(peak, c)
                last_close = c
                w.writerow([d + "T00:00:00", sym, f"{o:.6f}", f"{h:.6f}", f"{lo:.6f}",
                            f"{c:.6f}", f"{v:.1f}"])
                rows += 1
            per_symbol[sym] = {
                "cohort": r["cohort"], "exchange": r["exchange"],
                "first_bar": dates[0], "last_bar": dates[-1], "n_bars": len(dates),
                "screen_end": r["screen_end"], "live_start": r["live_start"],
                "n_live_bars": r["n_live_bars"],
                "delistingDate": r["delistingDate"],
                "cohort_note": r.get("cohort_note"),
                "terminal_drawdown_from_peak": round(1.0 - last_close / peak, 4) if peak else None,
                "n_splits": len(sp),
                "n_dividends": len(events["dividends"].get(sym, [])),
                "max_gap_days": max_gap,
            }

    # The committed sidecar is `_events_full.json` PRUNED to exactly the symbols in the
    # fixture. A sidecar carrying events for symbols that are not there invites a loader
    # to build a longer index than the data supports, and it makes "sidecar and fixture
    # agree" untestable. The full version stays in the cache and is what `--build`
    # reads, so this pruning never feeds back into the next run.
    EVENTS.parent.mkdir(parents=True, exist_ok=True)
    EVENTS.write_text(json.dumps(
        {k: {s: v for s, v in sect.items() if s in per_symbol} for k, sect in events.items()},
        indent=1, sort_keys=True), encoding="utf-8")

    # HINDSIGHT LABELS. Exactly the crypto convention (D140/`fetch_crypto_universe.py`):
    # these are computed from the outcome, they are used ONLY to split results after the
    # fact, and NOTHING in the selection above can see them.
    for sym, m in per_symbol.items():
        td = m["terminal_drawdown_from_peak"]
        if m["cohort"] == "dead":
            m["status"] = "delisted"
        elif td is not None and td >= 0.90:
            m["status"] = "collapsed"
        else:
            m["status"] = "survived"

    moves.sort(key=lambda t: -abs(t[0] - 1.0))
    top_moves = [{"symbol": s, "date": d, "ratio": round(rt, 4),
                  "move_pct": round((rt - 1.0) * 100, 2)} for rt, s, d in moves[:25]]

    n_dead_final = sum(1 for m in per_symbol.values() if m["cohort"] == "dead")
    status_counts = Counter(m["status"] for m in per_symbol.values())

    meta = {
        "fixture": FIXTURE.name,
        "purpose": "US single-name equity base for SHORT-SIDE research. Built dead-inclusive.",
        "n_symbols": len(per_symbol),
        "rows": rows,
        "span": {"start": SPAN_START, "end": SPAN_END,
                 "first_bar": min(m["first_bar"] for m in per_symbol.values()),
                 "last_bar": max(m["last_bar"] for m in per_symbol.values())},

        "SURVIVORSHIP_BIAS_STATEMENT": (
            "THIS FIXTURE DELIBERATELY CONTAINS DEAD COMPANIES AND IS STILL NOT FREE OF "
            f"SURVIVORSHIP BIAS. {n_dead_final:,} of {len(per_symbol):,} symbols "
            f"({n_dead_final/max(len(per_symbol),1):.1%}) carry a delistingDate; the rest "
            "were listed at the span end. Three residual biases are known and none is "
            "repaired by the construction: "
            "(1) PROVIDER COVERAGE. Alpha Vantage's delisted roster records 40-76 "
            "delistings a year for 2009-2012 against 700-1,000 a year after 2016. "
            "Hundreds of US listings die every year in reality, so the dead cohort is "
            "materially UNDER-SAMPLED at the start of the span and any per-era split "
            "must carry that. The per-year histogram is in `delistings_by_year` below "
            "rather than left to this sentence. "
            "(2) THE HISTORY FLOOR. A symbol needs "
            f"{SCREEN_BARS + MIN_LIVE_BARS} in-span sessions to enter, which removes "
            "companies that listed and died inside about eighteen months - "
            "disproportionately SPACs and micro-caps, and disproportionately the fastest "
            "failures. The rejection counts by cohort are in `screen_rejections`. "
            "(3) THE SCREEN ITSELF. A $1M/day and $3 floor over each symbol's FIRST year "
            "removes names that were never liquid enough to short, and those skew dead. "
            "The floors sit on the screen window only, so a company that was liquid in "
            "year one and worthless in year four IS retained - that is the cohort this "
            "fixture exists for - but a company that was never liquid is gone. "
            "(4) DATA-QUALITY EXCLUSIONS. "
            f"{len(excluded)} symbols were dropped for discontinuities that could not be "
            "explained - unrecorded reverse splits, ADS ratio changes, zero-volume stub "
            "bars. Those failures are not random with respect to distress: a company "
            "does a 1-for-300 reverse split because it is in trouble. Every excluded "
            "name and the reason is in `gates.excluded_for_data_quality`, and "
            f"{len(json.loads((CACHE / '_fetch_misses.json').read_text(encoding='utf-8'))) if (CACHE / '_fetch_misses.json').exists() else 0} "
            "more are in `fetch_failures` - the provider's daily endpoint does not serve "
            "them at all, and all of those were dead names. "
            "WHAT THIS FIXTURE IS NOT: it is not a point-in-time reconstruction of the "
            "US tape, and no cross-sectional base rate taken from it (delisting rate, "
            "failure rate, the fraction of names that fall 90%) should be read as a "
            "market base rate."
        ),

        "cohorts": {
            "dead": n_dead_final,
            "alive": len(per_symbol) - n_dead_final,
            "dead_share": round(n_dead_final / max(len(per_symbol), 1), 4),
            "min_dead_share_enforced": MIN_DEAD_SHARE,
        },
        "status_counts": dict(sorted(status_counts.items())),
        "status_definition": (
            "delisted = carries a LISTING_STATUS delistingDate ON OR BEFORE the span end "
            "(a delistingDate after the span end means the company was listed for the "
            "whole span and is counted alive here -- see roster_refresh_artefact); "
            "collapsed = still listed at the span end but final close is 90% or more "
            "below its own in-span peak; survived = neither. HINDSIGHT BY CONSTRUCTION "
            "(D140). Used only to split results after the fact, NEVER to decide what is "
            "traded."
        ),
        "delistings_by_year": dict(sorted(Counter(
            m["delistingDate"][:4] for m in per_symbol.values()
            if m["cohort"] == "dead" and m["delistingDate"]
        ).items())),
        "roster_refresh_artefact": {
            **sel["roster_refresh_artefact"],
            "reclassified_alive_delisting_after_span_end": [
                s for s in sel["roster_refresh_artefact"]
                ["reclassified_alive_delisting_after_span_end"] if s in per_symbol],
        },
        "fetch_failures": sel["fetch_failures"],

        "universe_rule": {
            "source": ("LISTING_STATUS state=active (current) UNION state=delisted "
                       "(cumulative) UNION state=delisted at " + ", ".join(SNAPSHOT_DATES)),
            "delisted_endpoint_behaviour": (
                "MEASURED 2026-08-28: state=delisted with no date is CUMULATIVE - every "
                "symbol ever delisted, 9,449 rows, delistingDate 1997-04-01..2026-08-27. "
                "Dated snapshots are strict subsets (183 rows at 2012-06-29, 4,099 at "
                "2020-06-30). The snapshots are queried anyway because inclusion is not "
                "quite monotone - 14 symbols in the 2020 snapshot are absent from the "
                "cumulative list today - and because they make ticker recycling visible."
            ),
            "asset_type": "assetType == 'Stock'",
            "exclusion_rule": (
                "assetType=='Stock' is NOT common stock - the provider files warrants, "
                "units, rights and every preferred series under it. EXCLUDED: (a) any "
                "symbol containing a hyphen (-W/-WS warrant, -U/-UN unit, -R right, "
                "-P-x preferred series, -CL called); (b) any FIVE-letter symbol whose "
                "fifth character is W, U or R (the NASDAQ fifth-letter convention). "
                "KEPT: fifth letter 'Q', which marks an issuer in bankruptcy - that is "
                "common stock and it is the most relevant cohort on the tape for a short "
                "book. Rule (a) is deliberately blunt and also drops roughly 40 "
                "hyphenated dual-class ordinary lines; that cost is paid for a rule a "
                "reader can apply by eye."
            ),
            "recycled_tickers_dropped": (
                "A symbol present in BOTH the active and delisted rosters, or carrying "
                "two different (ipoDate, delistingDate) pairs across snapshots, has been "
                "reused by a second issuer and its bar series cannot be attributed to one "
                "company. Dropped from BOTH cohorts rather than guessed at."
            ),
            "min_span_overlap_days": MIN_OVERLAP_DAYS,
            "pool_permutation_seed": POOL_SEED,
            "pool_size": POOL_SIZE,
            "pool_note": ("The eligible pool is shuffled ONCE with the pinned seed and the "
                          "fetch takes a PREFIX. Growing the budget extends the prefix; it "
                          "never re-picks. No symbol enters or leaves because of anything "
                          "learned after the shuffle."),
        },

        "screen": sel["screen"],
        "screen_is_pre_live": True,
        "screen_rejections": sel["rejected"],

        "panel_shape": "RAGGED",
        "panel_note": (
            "Per-symbol start and end dates; symbols have "
            f"{len({m['n_bars'] for m in per_symbol.values()})} distinct bar counts. "
            "THIS IS DELIBERATE. A rectangular panel requires every symbol present on "
            "every date, which is exactly the requirement that deletes delisted names - "
            "D245 AMENDMENT 1 recorded one delisted fund truncating a whole panel to 880 "
            "bars. `run_macd_ladder.load_panel` REFUSES a ragged panel: it raises "
            "ValueError('symbols have different bar counts') by design, and that refusal "
            "is correct for a rectangular daily universe. A DOWNSTREAM LOADER IS "
            "THEREFORE REQUIRED and does not exist yet. What it must do: "
            "(1) build a union date index and place each symbol on it with an explicit "
            "presence mask, never a forward-fill and never a zero - a filled bar is a "
            "fabricated price and a zero is a -100% return; "
            "(2) mask returns, positions, costs and the equity contribution to zero "
            "outside a symbol's own [first_bar, last_bar]; "
            "(3) treat a delisting as a FORCED EXIT at the last bar's close and say what "
            "that assumes - a real short is bought back or the position is settled, and "
            "assuming a fill at the final print of a company being delisted is optimistic; "
            "(4) drop each symbol's own pre-live window using the per-symbol `live_start` "
            "recorded below, so no bar the screen read is ever traded; "
            "(5) normalise cross-sectional aggregates by the LIVE COUNT on each date, not "
            "by the symbol count, or every breadth statistic is diluted by absent names. "
            "None of that is written here - this file builds data and nothing else."
        ),

        "split_adjusted": True,
        "split_adjusted_bars": adjusted_bars,
        "adjustment_frame": (
            "TIME_SERIES_DAILY_ADJUSTED columns 1-4 are AS-TRADED (measured: AAPL "
            "1999-11-01 close 77.62 against adjusted close 0.58), so splits are applied "
            "here from the inline coefficients: prices DIVIDED by the product of ratios "
            "effective after the bar, volumes MULTIPLIED. Sidecar dividend amounts are "
            "divided by the same factor so prices and dividends share one frame (D75)."
        ),
        "inline_actions_caveat": (
            "Splits and dividends come from the daily payload's own `8. split "
            "coefficient` and `7. dividend amount` columns, one request per symbol "
            "instead of three. They cover only the window the series covers: AABA's "
            "SPLITS endpoint lists three splits where the inline coefficients show two, "
            "the missing one predating the series. Immaterial at a 2010 span start, "
            "recorded rather than discovered later."
        ),
        "gates": {
            "gate_a": {
                "definition": (f"every CONFIRMED split with ratio >= {GATE_A_MIN_RATIO} or "
                               f"<= 1/{GATE_A_MIN_RATIO} must leave |close(t)/close(t-1) - 1| "
                               f"<= {GATE_A_TOLERANCE} at its effective date. A symbol that "
                               "fails is EXCLUDED, not excused"),
                "failures": [f for f in gate_a_failures if f["symbol"] in per_symbol],
                "excluded_symbols": sorted({f["symbol"] for f in gate_a_failures}),
            },
            "gate_b": {
                "definition": (
                    f"every adjusted close ratio >= {GATE_B_UP_RATIO} is CLASSIFIED, and "
                    "the classes have different right answers. `revert` = the price is "
                    f"back within a factor of {REVERT_BAND} either side, so it is a single "
                    "bad print and is LEFT IN -- D6 stores raw bars and D25's clean() "
                    "removes spike-and-revert prints at load. `corroborated` = dollar "
                    f"volume moved by at least x{CORROBORATION_DOLLAR_VOLUME} and the "
                    f"ratio is under x{IMPLAUSIBLE_RATIO}, so it is a real event and is "
                    "retained. `unexplained` = a persistent step with no volume behind it, "
                    "or a ratio no US common stock reaches in a session; that is an "
                    "unrecorded corporate action or bad data, clean() will NOT remove it "
                    "because it does not revert, and THE SYMBOL IS EXCLUDED. The gate is "
                    "ASYMMETRIC: an 80% down-day is a real and frequent event here and is "
                    "the signal a short book exists to capture, so gating hard on the "
                    "downside would delete the payload"),
                "thresholds": {"up_ratio": GATE_B_UP_RATIO, "revert_band": REVERT_BAND,
                               "corroboration_dollar_volume": CORROBORATION_DOLLAR_VOLUME,
                               "implausible_ratio": IMPLAUSIBLE_RATIO},
                "hand_verified_cross_check": {
                    f"{s} {d}": why for (s, d), why in DOCUMENTED_LARGE_MOVES.items()},
                "hand_verified_note": (
                    "The build ASSERTS every hand-verified entry comes back "
                    "`corroborated`. It is a cross-check on the classifier, not an "
                    "exemption from it -- disagreement stops the build."),
                "all_classified_moves": classified,
                "failures": [c for c in classified
                             if c["klass"] == "unexplained" and c["symbol"] in per_symbol],
            },
            "excluded_for_data_quality": {
                "definition": ("symbols dropped because a discontinuity in them could not "
                               "be explained. Reported in full: an excluded name is a fact "
                               "about the provider's data, and hiding it would be the "
                               "same mistake as hiding a delisted one"),
                "count": len(excluded),
                "by_symbol": excluded,
                "cohorts": dict(Counter(
                    r["cohort"] for r in sel["selected"] if r["symbol"] in excluded)),
            },
            "unconfirmed_splits": {
                "definition": ("provider split coefficients the PRICE SERIES does not "
                               "corroborate, dropped rather than applied. See the "
                               "`do_actions` docstring: final-bar artefacts on zero "
                               "volume, coefficients on continuous prices, and spinoffs "
                               "modelled as splits"),
                "count": len(unconfirmed_splits),
                "dropped": unconfirmed_splits,
            },
            "moves_across_a_trading_halt": {
                "definition": (f"a close ratio >= {GATE_B_UP_RATIO} where the previous bar "
                               f"is more than {HALT_GAP_DAYS} calendar days earlier. NOT a "
                               "one-day return, so not a GATE B failure. A symbol carrying "
                               "one has been through a suspension or a reorganisation and "
                               "the downstream loader should treat it as SEGMENTED rather "
                               "than continuous - see per-symbol `max_gap_days`"),
                "count": len(halt_crossings),
                "crossings": halt_crossings,
            },
            "large_drops_reported_not_gated": {
                "definition": f"adjusted close ratio <= {GATE_B_DOWN_RATIO}",
                "count": len(big_drops),
                "largest_25": sorted(big_drops, key=lambda x: x["ratio"])[:25],
            },
            "largest_25_moves": top_moves,
        },

        "dividends": "in the sidecar, SAME split-adjusted frame as the prices (D75)",
        "timestamps": "naive exchange-local dates at T00:00:00 (D75)",
        "provider": "Alpha Vantage TIME_SERIES_DAILY_ADJUSTED, outputsize=full",
        "raw_cache_committed": False,
        "raw_cache_note": "D191: the raw cache is not committed; only the derived fixture is.",
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "symbols": per_symbol,
    }
    META.write_text(json.dumps(meta, indent=1, sort_keys=False), encoding="utf-8")

    print(f"symbols       {len(per_symbol):,}   dead {n_dead_final:,} "
          f"({n_dead_final/len(per_symbol):.1%})   alive {len(per_symbol)-n_dead_final:,}")
    print(f"status        {dict(sorted(status_counts.items()))}")
    print(f"rows          {rows:,}   RAGGED, "
          f"{len({m['n_bars'] for m in per_symbol.values()})} distinct bar counts")
    print(f"splits        applied to {adjusted_bars:,} bars")
    print(f"GATE A        {len(gate_a_failures)} failures, all in EXCLUDED symbols "
          f"({sum(1 for f in gate_a_failures if f['symbol'] in per_symbol)} left in)")
    klasses = Counter(c["klass"] for c in classified)
    print(f"GATE B        {sum(klasses.values())} moves >= x{GATE_B_UP_RATIO}: "
          f"{dict(sorted(klasses.items()))}")
    for c in classified:
        if c["klass"] == "corroborated" and c["symbol"] in per_symbol:
            print(f"    KEPT      {c['symbol']:6s} {c['date']}  x{c['ratio']:<7.2f} "
                  f"$vol x{c['dollar_volume_ratio']:,}")
    print(f"unconfirmed splits dropped  {len(unconfirmed_splits)}")
    print(f"EXCLUDED for data quality   {len(excluded)} symbols "
          f"{dict(sorted(Counter(r['cohort'] for r in sel['selected'] if r['symbol'] in excluded).items()))}")
    for s, ps in list(excluded.items())[:30]:
        print(f"    {s:6s} {ps[0].get('why', ps[0].get('adjusted_ratio'))}"[:110])
    print(f"halt crossings{len(halt_crossings):3d} (reported, not gated)")
    for f in halt_crossings[:10]:
        print(f"    {f['symbol']:6s} {f['date']}  x{f['ratio']:.2f}  after {f['gap_days']}d of no bars")
    print(f"large drops   {len(big_drops)} at <= x{GATE_B_DOWN_RATIO} (reported, not gated)")
    print(f"fixture       {FIXTURE.name}  {FIXTURE.stat().st_size/1e6:.1f} MB")
    residual = [c for c in classified
                if c["klass"] == "unexplained" and c["symbol"] in per_symbol]
    if residual or any(f["symbol"] in per_symbol for f in gate_a_failures):
        print("\nGATES FAILED. The fixture on disk is NOT clean -- fix before use.")
        return
    print("\ngates clean.")


def main() -> int:
    ap = argparse.ArgumentParser()
    for flag in ("plan", "fetch", "select", "actions", "build"):
        ap.add_argument(f"--{flag}", action="store_true")
    ap.add_argument("--limit", type=int, default=None,
                    help="fetch only the first N of the pinned pool order")
    args = ap.parse_args()

    limiter = RateLimiter(MIN_INTERVAL)
    needs_key = args.plan or args.fetch
    key = api_key() if needs_key else ""
    if needs_key:
        src = "env ALPHAVANTAGE_API_KEY" if os.environ.get("ALPHAVANTAGE_API_KEY") else str(KEY_FILE)
        print(f"key       {src}")  # the SOURCE, never the value

    if args.plan:
        do_plan(key, limiter)
    if args.fetch:
        do_fetch(key, limiter, args.limit)
    if args.select:
        do_select(args.limit)
    if args.actions:
        do_actions()
    if args.build:
        do_build()
    if not any(v for k, v in vars(args).items() if k != "limit"):
        ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
