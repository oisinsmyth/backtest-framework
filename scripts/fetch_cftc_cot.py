"""One-time (manual, NETWORK) fetch: CFTC Commitments of Traders positioning.

    uv run python scripts/fetch_cftc_cot.py --plan     # no network, just the shape
    uv run python scripts/fetch_cftc_cot.py --probe    # 3 calls: prove the API answers
    uv run python scripts/fetch_cftc_cot.py --map      # symbol -> contract code, DERIVED
    uv run python scripts/fetch_cftc_cot.py --fetch    # the series, resumable
    uv run python scripts/fetch_cftc_cot.py --build    # cache -> committed fixture

Sibling of `fetch_index_extended.py`: same mode shape, same limiter discipline, same
cache-the-raw-commit-the-derived split (D191). Stdlib only — no new dependency.

WHY THIS EXISTS
---------------
`docs/research/futures-data/data-purchase-proposal.md` §7.5 puts a staged ladder in
front of the smart-money question, cheapest rung first. **This is rung 1, and it is
free.** The CFTC surveys every reportable position in every US futures market weekly
and publishes who holds them, split by trader type. That is not a proxy for
institutional positioning — it is the official measurement of it, and it goes back
to 1986.

THE ONE SOURCE IN THIS PROGRAMME THAT MAY BE COMMITTED
------------------------------------------------------
Every CME product in the proposal is exchange-licensed and forbidden from
redistribution, which is why `.gitignore` carries `data/raw/databento/` and the
pattern is gitignored-cache-plus-committed-refetch-script.

**COT is a work of the United States government and is public domain.** The fixture
is therefore COMMITTED like any Alpha Vantage-derived fixture, and no licence
constraint attaches to it.

THE FINDING THAT MADE THIS MORE THAN RUNG 1
-------------------------------------------
The proposal costs rung 2 — separating retail from institutional flow via the
micro/mini split — at $14.28 of Databento minute bars, on the argument that ten MES
cost ~3x the fees of one ES so anyone trading size uses ES.

**The CFTC reports the micros as their own contracts.** MES `13874U`, MNQ `209747`,
M2K `239747`, MYM `124608`, MICRO GOLD `088695`, MICRO COPPER `085699` — each with
the full trader-category breakdown and its own `nonrept` (small-trader) column.

So the retail/institutional split is DIRECTLY OBSERVABLE here, weekly, for nothing,
with the CFTC classifying the traders instead of us inferring it from contract
choice. It does not replace the paid rung 2 — weekly cannot support an intraday
rule — but **the premise can be falsified for £0 before any purchase.**

THREE REPORTS, NOT ONE, AND THEY ARE NOT COMPARABLE
---------------------------------------------------
  LEGACY        1986+   every market   commercial / non-commercial / non-reportable
  DISAGGREGATED 2009-09 physicals      producer-merchant / swap / managed-money /
                                       other-reportable / non-reportable
  TFF           2010-07 financials     dealer / asset-manager / leveraged-money /
                                       other-reportable / non-reportable

**A financial contract has no `prod_merc` and a physical has no `asset_mgr`.** The
fixture is tidy — one row per (report, category) — and carries `family` on every row
so a study cannot pool categories that do not mean the same thing. Legacy is fetched
for everything as the long-history spine; it is coarser and it reaches 1986.

WHY THE SYMBOL MAP IS DERIVED AND NOT TYPED
--------------------------------------------
`--map` resolves each symbol against the live API and refuses ambiguity, because a
hand-typed code is a silent wrong answer:

  **`CRUDE OIL` matches SEVEN contracts** — 067411 WTI light sweet (the one), plus
  06741Q 1st-line, 067655 E-mini, 06765A and 06765I financial, 06765G Dubai, and
  067DU1 Oman. Picking wrong gives a DIFFERENT MARKET and nothing downstream errors.

So every symbol declares a search pattern, and optionally the exact contract name
verified by hand. Resolution rules, all of them loud:

  exact given and found      -> use it
  exact given and MISSING    -> HARD FAIL, the provider renamed something
  no exact, one candidate    -> use it, and PRINT it so it can be promoted to exact
  no exact, many candidates  -> HARD FAIL, listing every candidate

THE PROVIDER'S OWN TYPOS ARE PART OF THE CONTRACT
-------------------------------------------------
Measured against the live API, not assumed:

    swap__positions_short_all       DOUBLE underscore
    swap__positions_spread_all      DOUBLE underscore
    noncomm_postions_spread_all     "postions"

They look like defects and someone will eventually "fix" them. The field names are
asserted by test so a silent rename fails loudly instead of yielding empty columns.

RELEASE LAG IS DATA, NOT A FOOTNOTE
-----------------------------------
COT is surveyed at Tuesday's close and published Friday at 15:30 ET. A study that
keys on `report_date` is reading Tuesday's positions on Tuesday and is look-ahead
by three days — exactly what R9 forbids for a conditioning variable. So the fixture
carries `release_date_nominal` beside `report_date`.

**It is the FRIDAY OF THE REPORT'S WEEK, not a flat +3 days**, and the difference is
not pedantry — it was measured. Across 1986-2026 the survey day is Tuesday on
98-100% of weeks from 1993, and the exceptions are HOLIDAY SHIFTS: 2007-01-03 is a
Wednesday because 2007-01-02 was the National Day of Mourning for President Ford
and the markets were shut. A flat +3 would put that release on a Saturday.

**Before 1993 there was no weekly Tuesday schedule at all** — 1986 report dates are
46.8% Friday, 16.2% Monday, 16.2% Wednesday. `release_date_nominal` is therefore
EMPTY for those rows. That is a deliberate answer rather than a gap: a fabricated
release date would look usable, and a study keying on release must decide for
itself what to do with data whose publication convention nobody here knows.

Two further limits, stated rather than buried: publication is **suspended during
government shutdowns and released in batches afterwards** (2018-12 to 2019-02 most
notably), so the nominal date is OPTIMISTIC across those windows; and a study
should carry margin regardless.

BEING A GOOD CITIZEN
--------------------
  * Socrata needs no key; an app token only raises throttling, so none is used
  * paced well under any published limit, and the whole job is ~81 requests
  * every response CACHED; a cached series is never re-fetched, so a run resumes
  * exponential backoff, HARD STOP after 5 consecutive failures
  * the raw cache is NOT committed (D191); the derived fixture IS
"""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

API = "https://publicreporting.cftc.gov/resource"
CACHE = REPO / "data" / "raw" / "cftc"
FIXTURE = REPO / "data" / "fixtures" / "cftc_cot_raw.csv.gz"
META = REPO / "data" / "fixtures" / "cftc_cot_raw.meta.json"
MAP = REPO / "data" / "fixtures" / "cftc_cot_map.json"

# Socrata dataset ids, VERIFIED against publicreporting.cftc.gov during D262's
# planning. `futures only` in every case -- the combined futures-and-options
# variants exist (jun7-fc8e, kh3c-gbw2, yw9f-hn96) and are deliberately not used,
# because an options-inclusive position is not a futures position and mixing the
# two would make `open_interest` mean two different things by row.
DATASETS = {
    "legacy": "6dca-aqww",
    "disaggregated": "72hh-3qpy",
    "tff": "gpe5-46if",
}

# First report in each family, MEASURED off the fetched series rather than taken
# from the CFTC's own page. The published starts are "September 2009" for
# disaggregated and "July 20, 2010" for TFF; the datasets actually carry
# back-history to 2006-06-13 in both cases. More history than documented is a
# pleasant surprise, but it is still a discrepancy and it is recorded as one.
FAMILY_START_PUBLISHED = {
    "legacy": "1986-01-01",
    "disaggregated": "2009-09-01",
    "tff": "2010-07-20",
}
FAMILY_START_MEASURED = {
    "legacy": "1986-01-15",
    "disaggregated": "2006-06-13",
    "tff": "2006-06-13",
}

# PROVENANCE TRAPS — a code whose series predates the instrument it names, or
# whose venue changed inside the span. Neither errors; both would silently splice
# two different things into one series.
PROVENANCE_WARNINGS = {
    "6E": (
        "Legacy rows run from 1986-01-15 under the name 'EURO FX', but THE EURO "
        "DID NOT EXIST UNTIL 1999-01-01 and continuous coverage begins exactly "
        "1999-01-05. Code 099741 carries a back-labelled predecessor (Deutsche "
        "Mark or ECU) under the euro's name, with a 644-week gap between the "
        "stragglers and the real series. USE 1999-01-05 ONWARD."
    ),
    "RTY": (
        "Legacy rows begin 2002-08-13, which is NOT pre-inception -- but the "
        "Russell 2000 E-mini traded on ICE between 2008 and 2017 before moving "
        "to CME. The series therefore spans a VENUE CHANGE, and pre-2017 rows "
        "describe a contract on a different exchange from the one the prop track "
        "would trade."
    ),
}

# When each contract first appears in COT -- which is NOT when it started trading.
# A contract enters the report only once it has enough reportable traders, and for
# the micros that lag is LONG. This bounds the free rung-2 test hard, so it is a
# constant rather than a comment.
MICRO_COT_INCEPTION = {
    "MES": "2020-07-28", "MNQ": "2020-08-04", "M2K": "2021-11-30",
    "MYM": "2022-07-26", "MGC": "2020-12-01", "MSI": "2026-01-13",
    "MHG": "2026-01-27",
}

# The category columns, per family. Tuples are (category, long, short, spread) and
# `spread` is None where the family does not report one. EVERY NAME HERE WAS READ
# OFF A LIVE RECORD -- including the two double-underscore and one "postions" typo.
CATEGORIES = {
    "legacy": [
        ("commercial", "comm_positions_long_all", "comm_positions_short_all", None),
        ("noncommercial", "noncomm_positions_long_all", "noncomm_positions_short_all",
         "noncomm_postions_spread_all"),
        ("nonreportable", "nonrept_positions_long_all", "nonrept_positions_short_all",
         None),
    ],
    "disaggregated": [
        ("producer_merchant", "prod_merc_positions_long", "prod_merc_positions_short",
         None),
        ("swap_dealer", "swap_positions_long_all", "swap__positions_short_all",
         "swap__positions_spread_all"),
        ("managed_money", "m_money_positions_long_all", "m_money_positions_short_all",
         "m_money_positions_spread"),
        ("other_reportable", "other_rept_positions_long", "other_rept_positions_short",
         "other_rept_positions_spread"),
        ("nonreportable", "nonrept_positions_long_all", "nonrept_positions_short_all",
         None),
    ],
    "tff": [
        ("dealer", "dealer_positions_long_all", "dealer_positions_short_all",
         "dealer_positions_spread_all"),
        ("asset_manager", "asset_mgr_positions_long", "asset_mgr_positions_short",
         "asset_mgr_positions_spread"),
        ("leveraged_money", "lev_money_positions_long", "lev_money_positions_short",
         "lev_money_positions_spread"),
        ("other_reportable", "other_rept_positions_long", "other_rept_positions_short",
         "other_rept_positions_spread"),
        ("nonreportable", "nonrept_positions_long_all", "nonrept_positions_short_all",
         None),
    ],
}

# symbol -> (primary family, LIKE pattern, exact contract_market_name or None)
#
# `exact` is filled in where the name was read off the live API during planning.
# Where it is None the pattern must resolve to exactly one candidate or --map
# fails; the resolved name is printed so it can be promoted to `exact` here.
#
# The MICROS are first-class, not an afterthought: they are the free half of the
# proposal's rung 2 and the reason this fetcher is worth more than rung 1.
SYMBOLS: dict[str, tuple[str, str, str | None]] = {
    # --- equity index, financial -> TFF ---
    "ES":  ("tff", "%E-MINI S&P 500%", "E-MINI S&P 500"),
    "MES": ("tff", "%MICRO E-MINI S&P 500%", "MICRO E-MINI S&P 500 INDEX"),
    "NQ":  ("tff", "%NASDAQ MINI%", "NASDAQ MINI"),
    "MNQ": ("tff", "%MICRO E-MINI NASDAQ%", "MICRO E-MINI NASDAQ-100 INDEX"),
    "YM":  ("tff", "%DJIA x $5%", "DJIA x $5"),
    "MYM": ("tff", "%MICRO E-MINI DJIA%", "MICRO E-MINI DJIA (x$0.5)"),
    "RTY": ("tff", "%RUSSELL E-MINI%", "RUSSELL E-MINI"),
    "M2K": ("tff", "%MICRO E-MINI RUSSELL%", "MICRO E-MINI RUSSELL 2000 INDX"),
    # --- rates, financial -> TFF ---
    "ZB":  ("tff", "%UST BOND%", "UST BOND"),
    "ZN":  ("tff", "%UST 10Y NOTE%", "UST 10Y NOTE"),
    "ZF":  ("tff", "%UST 5Y NOTE%", "UST 5Y NOTE"),
    # --- FX, financial -> TFF ---
    "6E":  ("tff", "%EURO FX%", "EURO FX"),
    "6J":  ("tff", "%JAPANESE YEN%", "JAPANESE YEN"),
    "6B":  ("tff", "%BRITISH POUND%", "BRITISH POUND"),
    # --- crypto, financial -> TFF ---
    "BTC": ("tff", "%BITCOIN%", "BITCOIN"),
    # --- energy, physical -> DISAGGREGATED ---
    # CL is the seven-way trap named in the docstring. The exact name is pinned.
    "CL":  ("disaggregated", "%CRUDE OIL%", "CRUDE OIL, LIGHT SWEET-WTI"),
    # NG is a SECOND trap, and a nastier one than CL's. The CFTC abbreviates, so
    # '%NATURAL GAS%' does not match the main Henry Hub contract AT ALL -- it
    # returns only 'E-MINI NATURAL GAS' and a San Juan index. The liquid NYMEX
    # contract is named 'NAT GAS NYME'. A pattern that misses the obvious answer
    # and returns two plausible wrong ones is precisely how a hand-typed map goes
    # wrong quietly.
    "NG":  ("disaggregated", "%NAT GAS NYME%", "NAT GAS NYME"),
    # --- metals, physical -> DISAGGREGATED ---
    "GC":  ("disaggregated", "%GOLD%", "GOLD"),
    "MGC": ("disaggregated", "%MICRO GOLD%", "MICRO GOLD"),
    "SI":  ("disaggregated", "%SILVER%", "SILVER"),
    "MSI": ("disaggregated", "%MICRO SILVER%", "MICRO SILVER"),
    "HG":  ("disaggregated", "%COPPER%", "COPPER- #1"),
    "MHG": ("disaggregated", "%MICRO COPPER%", "MICRO COPPER"),
    # --- ags, physical -> DISAGGREGATED ---
    "ZC":  ("disaggregated", "%CORN%", "CORN"),
    "ZS":  ("disaggregated", "%SOYBEANS%", "SOYBEANS"),
    "ZW":  ("disaggregated", "%WHEAT-SRW%", "WHEAT-SRW"),
    "LE":  ("disaggregated", "%LIVE CATTLE%", "LIVE CATTLE"),
    "HE":  ("disaggregated", "%LEAN HOGS%", "LEAN HOGS"),
}

REQUESTS_PER_MIN = 30
MIN_INTERVAL = 60.0 / REQUESTS_PER_MIN
MAX_CONSECUTIVE_FAILURES = 5
TIMEOUT = 90
PAGE = 50_000            # Socrata's JSON ceiling; every series fits well inside it

# COT is surveyed at Tuesday's close and published Friday 15:30 ET -- but only
# once the weekly Tuesday schedule existed, and the survey day SHIFTS on holidays.
#
# MEASURED across the whole 1986-2026 span rather than assumed:
#   * from 1993 the report date is Tuesday on ~98-100% of weeks
#   * the remainder are holiday shifts, Monday or Wednesday. 2007-01-03 is a
#     Wednesday because 2007-01-02 was the National Day of Mourning for President
#     Ford and the markets were shut
#   * BEFORE 1993 there was no weekly Tuesday schedule at all -- 1986 report dates
#     are 46.8% Friday, 16.2% Monday, 16.2% Wednesday
#
# So the release is "the FRIDAY OF THE REPORT'S WEEK", not a flat +3 days, and it
# is left EMPTY before the convention existed. Stamping a fabricated release date
# on 1986 data would be worse than admitting we do not know it.
TUESDAY_CONVENTION_FROM = "1993-01-01"
RELEASE_WEEKDAY = 4  # Friday

# Publication suspensions. Weeks inside these are released late and in batches, so
# `release_date_nominal` is OPTIMISTIC across them. Recorded, not silently ignored.
KNOWN_SUSPENSIONS = [
    ("2018-12-18", "2019-02-05", "35-day federal government shutdown"),
    ("2013-10-01", "2013-10-16", "16-day federal government shutdown"),
]

# A weekly series may legitimately skip a week (holiday); three in a row means the
# series stopped rather than paused, and the gate reports it.
MAX_GAP_WEEKS = 3


class RateLimiter:
    """A floor on the gap between requests. Not a token bucket — the conservative
    choice, and the same one every other fetcher in this repo makes."""

    def __init__(self, min_interval: float) -> None:
        self.min_interval = min_interval
        self.last = 0.0

    def wait(self) -> None:
        gap = time.monotonic() - self.last
        if gap < self.min_interval:
            time.sleep(self.min_interval - gap)
        self.last = time.monotonic()


def get(dataset: str, params: dict, limiter: RateLimiter) -> list:
    """One Socrata GET, with backoff. No key is sent, so nothing here is secret —
    but the URL is still printed only on failure and only in its unparameterised
    form, to keep the habit uniform across fetchers."""
    url = f"{API}/{dataset}.json?" + urllib.parse.urlencode(params)
    delay = 2.0
    for attempt in range(5):
        limiter.wait()
        try:
            req = urllib.request.Request(
                # ASCII only: HTTP headers are latin-1 encoded, so a non-ASCII
                # User-Agent raises UnicodeEncodeError before the socket opens.
                url, headers={"Accept": "application/json",
                              "User-Agent": "backtest-framework (personal research)"}
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return json.loads(r.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
                json.JSONDecodeError) as exc:
            if attempt == 4:
                raise RuntimeError(f"{dataset}: {type(exc).__name__} {exc}") from exc
            time.sleep(delay)
            delay *= 2
    return []


def cache_path(family: str, code: str) -> Path:
    return CACHE / family / f"{code}.json.gz"


def read_cache(path: Path) -> list | None:
    if not path.exists():
        return None
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return json.load(fh)


def write_cache(path: Path, payload: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        json.dump(payload, fh)


def release_date_of(report_date: str) -> str:
    """The Friday of the report's week, or '' where the convention did not exist.

    Empty is a deliberate, load-bearing answer: a study that keys on release
    simply cannot use pre-1993 rows without supplying its own convention, which
    is correct, because nobody here knows what it was."""
    d = date.fromisoformat(report_date[:10])
    if d.isoformat() < TUESDAY_CONVENTION_FROM:
        return ""
    rel = d + timedelta(days=(RELEASE_WEEKDAY - d.weekday()) % 7)
    # A report dated on a FRIDAY would otherwise release on itself -- zero lag,
    # which is look-ahead by construction. Four such dates survive after 1993
    # (1997-12-19, 2001-12-21, 2001-12-28, 2003-02-14), all year-end or holiday
    # schedule anomalies in the CFTC's own history. Push to the following Friday:
    # a report cannot be published before it is surveyed, and erring LATE is the
    # only safe direction for a conditioning variable.
    if rel <= d:
        rel += timedelta(days=7)
    return rel.isoformat()


def in_suspension(report_date: str) -> str | None:
    for lo, hi, why in KNOWN_SUSPENSIONS:
        if lo <= report_date[:10] <= hi:
            return why
    return None


# ---------------------------------------------------------------- modes


def do_plan() -> int:
    fams: dict[str, int] = {}
    for _sym, (fam, _pat, _exact) in SYMBOLS.items():
        fams[fam] = fams.get(fam, 0) + 1
    pinned = sum(1 for _s, (_f, _p, e) in SYMBOLS.items() if e)
    print(f"symbols      {len(SYMBOLS)}")
    print(f"  primary    " + ", ".join(f"{k}={v}" for k, v in sorted(fams.items())))
    print(f"  name pinned {pinned}/{len(SYMBOLS)}  "
          f"(unpinned must resolve to exactly one candidate)")
    unpinned = [s for s, (_f, _p, e) in SYMBOLS.items() if not e]
    if unpinned:
        print(f"  UNPINNED   {', '.join(unpinned)}")
    print(f"families     {len(DATASETS)}  "
          + ", ".join(f"{k}={v}" for k, v in DATASETS.items()))
    print(f"requests     ~{len(SYMBOLS)} for --map + "
          f"{len(SYMBOLS) * len(DATASETS)} for --fetch")
    print(f"pacing       {REQUESTS_PER_MIN}/min")
    print(f"ETA          "
          f"{len(SYMBOLS) * (1 + len(DATASETS)) * MIN_INTERVAL / 60:.1f} minutes")
    print(f"cache        {CACHE}  (NOT committed -- D191)")
    print(f"fixture      {FIXTURE.name}  (COMMITTED -- US government public domain)")
    print(f"map          {MAP.name}  (committed)")
    print("auth         none -- Socrata needs no key for this volume")
    return 0


def do_probe() -> int:
    """Three calls. Proves the API answers and the schemas are what we think."""
    limiter = RateLimiter(MIN_INTERVAL)
    ok = True
    for family, dataset in DATASETS.items():
        rows = get(dataset, {"$limit": 1}, limiter)
        if not rows:
            print(f"  {family:14} EMPTY RESPONSE")
            ok = False
            continue
        row = rows[0]
        missing = []
        for _cat, lo, sh, sp in CATEGORIES[family]:
            for f in (lo, sh, sp):
                if f and f not in row:
                    missing.append(f)
        for f in ("open_interest_all", "report_date_as_yyyy_mm_dd",
                  "cftc_contract_market_code", "contract_market_name"):
            if f not in row:
                missing.append(f)
        if missing:
            print(f"  {family:14} MISSING FIELDS: {missing}")
            ok = False
        else:
            print(f"  {family:14} OK  {len(row)} fields  "
                  f"sample={row['contract_market_name'][:34]!r}")
    print("\nprobe:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def do_map() -> int:
    """Resolve every symbol to exactly one contract code. Ambiguity is fatal."""
    limiter = RateLimiter(MIN_INTERVAL)
    resolved: dict[str, dict] = {}
    failures: list[str] = []

    for symbol, (family, pattern, exact) in SYMBOLS.items():
        dataset = DATASETS[family]
        rows = get(dataset, {
            "$select": "cftc_contract_market_code,contract_market_name",
            "$where": f"contract_market_name like '{pattern}'",
            "$group": "cftc_contract_market_code,contract_market_name",
            "$limit": 200,
        }, limiter)
        cands = {r["contract_market_name"]: r["cftc_contract_market_code"]
                 for r in rows}

        if exact is not None:
            if exact not in cands:
                failures.append(
                    f"{symbol}: pinned name {exact!r} NOT FOUND in {family}. "
                    f"Candidates: {sorted(cands)}"
                )
                continue
            name, code = exact, cands[exact]
            how = "pinned"
        elif len(cands) == 1:
            name, code = next(iter(cands.items()))
            how = "sole candidate"
        else:
            failures.append(
                f"{symbol}: {len(cands)} candidates for {pattern!r} in {family} — "
                f"pin one in SYMBOLS. Candidates: "
                + ", ".join(f"{c}={n!r}" for n, c in sorted(cands.items()))
            )
            continue

        resolved[symbol] = {"code": code, "contract_name": name,
                            "primary_family": family, "resolved_by": how}
        flag = "" if how == "pinned" else "   <-- PROMOTE TO `exact` IN SYMBOLS"
        print(f"  {symbol:4} {code:8} {name!r}{flag}")

    if failures:
        print("\nRESOLUTION FAILED -- nothing written:\n")
        for f in failures:
            print(f"  {f}\n")
        print("A hand-typed code is a silent wrong answer. Fix SYMBOLS and re-run.")
        return 1

    MAP.parent.mkdir(parents=True, exist_ok=True)
    MAP.write_text(json.dumps({
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": f"{API}/{{dataset}}.json — derived by --map, never hand-typed",
        "why_derived": (
            "contract_market_name 'CRUDE OIL' matches SEVEN contracts (WTI light "
            "sweet, 1st-line, E-mini, two financials, Dubai, Oman). A typed code "
            "silently selects a different market and nothing downstream errors."
        ),
        "symbols": dict(sorted(resolved.items())),
    }, indent=1) + "\n", encoding="utf-8")
    print(f"\nwrote {MAP.name}: {len(resolved)} symbols")
    return 0


def do_fetch() -> int:
    """Every (symbol, family) series. Cached, resumable, and tolerant of a symbol
    that a family does not carry — a micro contract predating TFF, say."""
    if not MAP.exists():
        raise SystemExit("No symbol map. Run --map first.")
    mapping = json.loads(MAP.read_text(encoding="utf-8"))["symbols"]
    limiter = RateLimiter(MIN_INTERVAL)

    todo = [(s, f) for s in mapping for f in DATASETS
            if not cache_path(f, mapping[s]["code"]).exists()]
    print(f"series {len(mapping) * len(DATASETS)}   cached "
          f"{len(mapping) * len(DATASETS) - len(todo)}   remaining {len(todo)}\n")

    consecutive = 0
    absent: list[str] = []
    for i, (symbol, family) in enumerate(todo, 1):
        code = mapping[symbol]["code"]
        try:
            rows = get(DATASETS[family], {
                "$where": f"cftc_contract_market_code='{code}'",
                "$order": "report_date_as_yyyy_mm_dd",
                "$limit": PAGE,
            }, limiter)
        except RuntimeError as exc:
            consecutive += 1
            print(f"  [{i}/{len(todo)}] {symbol:4} {family:14} FAILED {exc}")
            if consecutive >= MAX_CONSECUTIVE_FAILURES:
                print(f"\nHARD STOP after {MAX_CONSECUTIVE_FAILURES} consecutive "
                      f"failures. Re-run to resume.")
                return 1
            continue
        consecutive = 0
        write_cache(cache_path(family, code), rows)
        if not rows:
            absent.append(f"{symbol}/{family}")
        print(f"  [{i}/{len(todo)}] {symbol:4} {family:14} {len(rows):5} reports")

    if absent:
        print(f"\nno rows (expected where a family predates a contract): "
              f"{', '.join(absent)}")
    return 0


def do_build() -> int:
    """Cache -> one committed TIDY fixture: a row per (report, category)."""
    if not MAP.exists():
        raise SystemExit("No symbol map. Run --map first.")
    mapping = json.loads(MAP.read_text(encoding="utf-8"))["symbols"]

    rows_out = 0
    per_symbol: dict[str, int] = {}
    per_family: dict[str, int] = {}
    spans: dict[str, list[str]] = {}
    identity_checked = 0
    identity_ok = 0
    suspension_rows = 0
    no_release_rows = 0
    seen: set[tuple[str, str, str, str]] = set()
    duplicates = 0
    empty_series: list[str] = []

    # BYTE-REPRODUCIBLE OUTPUT, and it takes more than `gzip.open`.
    #
    # gzip stamps an MTIME into bytes 4-7 of its header, so two builds of
    # identical content differ in the file hash and D252's non-idempotent-build
    # defect reappears -- measured here before this was fixed: same 210,717 rows,
    # different md5. `gzip.open` gives no way to suppress it, so the GzipFile is
    # constructed directly with mtime=0 and an empty embedded filename.
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    with open(FIXTURE, "wb") as _raw, \
            gzip.GzipFile(filename="", fileobj=_raw, mode="wb", mtime=0) as _gz, \
            io.TextIOWrapper(_gz, encoding="utf-8", newline="") as out:
        w = csv.writer(out)
        w.writerow(["report_date", "release_date_nominal", "symbol", "code",
                    "family", "contract_name", "open_interest", "traders_total",
                    "category", "long", "short", "spread"])

        for symbol in sorted(mapping):
            code = mapping[symbol]["code"]
            for family in sorted(DATASETS):
                cached = read_cache(cache_path(family, code))
                if cached is None:
                    raise SystemExit(
                        f"{symbol}/{family}: not cached. Run --fetch first."
                    )
                if not cached:
                    empty_series.append(f"{symbol}/{family}")
                    continue

                for rec in cached:
                    rd = rec.get("report_date_as_yyyy_mm_dd", "")[:10]
                    if not rd:
                        continue
                    key = (symbol, family, rd, code)
                    if key in seen:
                        duplicates += 1
                        continue
                    seen.add(key)

                    oi = rec.get("open_interest_all")
                    name = rec.get("contract_market_name", "")
                    traders = rec.get("traders_tot_all", "")
                    rel = release_date_of(rd)
                    if not rel:
                        no_release_rows += len(CATEGORIES[family])
                    if in_suspension(rd):
                        suspension_rows += 1

                    # THE ARITHMETIC IDENTITY, and getting it right took one wrong
                    # attempt worth recording. A SPREAD position is one long AND
                    # one short held by the same trader: it sits inside open
                    # interest but OUTSIDE the directional columns. So the identity
                    # is not `OI == sum(long)` -- that fails on 94% of rows -- it is
                    #
                    #     OI == sum(long) + sum(spread) == sum(short) + sum(spread)
                    #
                    # BOTH sides are checked, because requiring both is a strictly
                    # stronger proof that every column landed in its right slot: a
                    # transposition that preserved one side would still break the
                    # other. Measured on ES 2026-08-25 the residual is EXACTLY zero,
                    # so the tolerance below is for defensiveness, not for slack.
                    if oi:
                        tot_l = tot_s = tot_sp = 0.0
                        have = True
                        for _cat, lo, sh, sp in CATEGORIES[family]:
                            vl, vs = rec.get(lo), rec.get(sh)
                            if vl is None or vs is None:
                                have = False
                                break
                            tot_l += float(vl)
                            tot_s += float(vs)
                            if sp and rec.get(sp) is not None:
                                tot_sp += float(sp and rec[sp])
                        if have:
                            identity_checked += 1
                            tol = max(1.0, float(oi) * 0.005)
                            if (abs(tot_l + tot_sp - float(oi)) <= tol
                                    and abs(tot_s + tot_sp - float(oi)) <= tol):
                                identity_ok += 1

                    for cat, lo, sh, sp in CATEGORIES[family]:
                        w.writerow([
                            rd, rel, symbol, code, family, name,
                            oi if oi is not None else "",
                            traders,
                            cat,
                            rec.get(lo, ""),
                            rec.get(sh, ""),
                            rec.get(sp, "") if sp else "",
                        ])
                        rows_out += 1
                        per_symbol[symbol] = per_symbol.get(symbol, 0) + 1
                        per_family[family] = per_family.get(family, 0) + 1
                    spans.setdefault(f"{symbol}|{family}", []).append(rd)

    # Gaps, measured per series and excluding known suspensions.
    long_gaps: list[dict] = []
    for key, dates in spans.items():
        ds = sorted(set(dates))
        for a, b in zip(ds, ds[1:]):
            weeks = (date.fromisoformat(b) - date.fromisoformat(a)).days / 7.0
            if weeks > MAX_GAP_WEEKS and not in_suspension(a):
                long_gaps.append({"series": key, "from": a, "to": b,
                                  "weeks": round(weeks, 1)})

    unresolved = [s for s in SYMBOLS if s not in mapping]
    meta = {
        "symbols_requested": sorted(SYMBOLS),
        "symbols_resolved": sorted(mapping),
        "rows": rows_out,
        "rows_per_family": dict(sorted(per_family.items())),
        "reports_per_symbol": {k: v for k, v in sorted(per_symbol.items())},
        "span": {
            "first": min((min(v) for v in spans.values()), default=None),
            "last": max((max(v) for v in spans.values()), default=None),
        },
        "shape": (
            "TIDY -- one row per (report_date, symbol, family, category). The three "
            "report families use DIFFERENT trader taxonomies and a study must not "
            "pool them; `family` is on every row so it cannot be lost."
        ),
        "source": (
            f"CFTC Socrata open data, {API}/{{dataset}}.json, futures-only variants: "
            + ", ".join(f"{k}={v}" for k, v in sorted(DATASETS.items()))
            + ". Combined futures-and-options datasets exist and are deliberately "
            "NOT used -- an options-inclusive position is not a futures position."
        ),
        "licence": (
            "Work of the US government, PUBLIC DOMAIN. This is the only source in "
            "the futures data layer that may be committed; every CME-derived "
            "product is licensed and gitignored."
        ),
        "release_convention": (
            "Surveyed at Tuesday's close, published Friday 15:30 ET, so "
            "release_date_nominal = THE FRIDAY OF THE REPORT'S WEEK. Not a flat "
            "+3 days: the survey day shifts on holidays (2007-01-03 is a "
            "Wednesday because 2007-01-02 was the National Day of Mourning for "
            "President Ford). A study MUST key on release, not report -- keying "
            "on report_date is three days of look-ahead, exactly what R9 forbids "
            "of a conditioning variable."
        ),
        "release_convention_measured": {
            "tuesday_schedule_from": TUESDAY_CONVENTION_FROM,
            "before_that": (
                "There was NO weekly Tuesday schedule. 1986 report dates are "
                "46.8% Friday, 16.2% Monday, 16.2% Wednesday, 12.3% Tuesday. "
                "release_date_nominal is therefore EMPTY before "
                f"{TUESDAY_CONVENTION_FROM} -- a fabricated release date would be "
                "worse than an admitted gap, because it would look usable."
            ),
            "rows_without_a_release_date": no_release_rows
        },
        "release_convention_fails_here": [
            {"from": lo, "to": hi, "why": why} for lo, hi, why in KNOWN_SUSPENSIONS
        ],
        "rows_inside_a_suspension": suspension_rows,
        "provider_typos_preserved_verbatim": [
            "swap__positions_short_all", "swap__positions_spread_all",
            "noncomm_postions_spread_all",
        ],
        "gates": {
            "every_symbol_resolved": not unresolved,
            "unresolved_symbols": {"failures": unresolved},
            "no_duplicate_report_rows": duplicates == 0,
            "duplicate_rows_dropped": duplicates,
            "open_interest_identity": {
                "checked": identity_checked,
                "passed": identity_ok,
                "rate": round(identity_ok / identity_checked, 6)
                if identity_checked else None,
                "note": (
                    "sum of per-category LONG positions must equal open interest, "
                    "within 0.5% or 1 contract. This is the cheapest available "
                    "proof that columns landed in the right slots."
                ),
                "failures": [] if identity_checked and
                identity_ok / identity_checked >= 0.99 else
                [f"identity held on only {identity_ok}/{identity_checked}"],
            },
            "no_unexplained_gap_over_3_weeks": {
                "failures": long_gaps[:40],
                "count": len(long_gaps),
            },
            "series_with_no_rows": {
                "failures": [],
                "absent": empty_series,
                "note": (
                    "A family that predates a contract legitimately returns nothing "
                    "-- TFF begins 2010-07 and the micros begin 2019. Recorded, not "
                    "treated as failure."
                ),
            },
        },
        "family_first_report_published": FAMILY_START_PUBLISHED,
        "family_first_report_measured": FAMILY_START_MEASURED,
        "family_first_report_note": (
            "The CFTC publishes 2009-09 for disaggregated and 2010-07-20 for TFF. "
            "Both datasets actually carry back-history to 2006-06-13. Recorded as "
            "a discrepancy rather than silently taking the better number."
        ),
        "first_report_per_symbol_family": {
            k: min(v) for k, v in sorted(spans.items())
        },
        "provenance_warnings": PROVENANCE_WARNINGS,
        "micro_cot_inception": MICRO_COT_INCEPTION,
        "micro_cot_inception_note": (
            "A contract enters COT only once it has enough REPORTABLE traders, "
            "which is much later than its listing date -- the micros launched "
            "2019-05-06 but MES first reports 2020-07-28 and MYM not until "
            "2022-07-26. MSI and MHG have under a year of history. This BOUNDS the "
            "free weekly form of the proposal's rung 2: ES/MES and NQ/MNQ carry ~6 "
            "years, M2K ~4.7, MYM ~4, and the metal micros are unusable. Any "
            "micro/mini study must be scoped to the pairs that have history."
        ),
        "built_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    META.write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")

    print(f"wrote {FIXTURE.name}: {rows_out:,} rows, "
          f"{FIXTURE.stat().st_size / 1e6:.1f} MB")
    print(f"  span        {meta['span']['first']} .. {meta['span']['last']}")
    print(f"  families    " + ", ".join(f"{k}={v:,}" for k, v in per_family.items()))
    print(f"  identity    {identity_ok:,}/{identity_checked:,} "
          f"({identity_ok / identity_checked * 100:.2f}%)" if identity_checked
          else "  identity    not checkable")
    if long_gaps:
        print(f"  LONG GAPS   {len(long_gaps)} over {MAX_GAP_WEEKS} weeks")
    if empty_series:
        print(f"  no rows     {len(empty_series)} (family predates contract)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true", help="shape the job, no network")
    ap.add_argument("--probe", action="store_true", help="3 calls: schemas as expected")
    ap.add_argument("--map", action="store_true", help="symbol -> code, DERIVED")
    ap.add_argument("--fetch", action="store_true", help="the series, resumable")
    ap.add_argument("--build", action="store_true", help="cache -> committed fixture")
    args = ap.parse_args()
    if args.probe:
        return do_probe()
    if args.map:
        return do_map()
    if args.fetch:
        return do_fetch()
    if args.build:
        return do_build()
    return do_plan()


if __name__ == "__main__":
    raise SystemExit(main())
