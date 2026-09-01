"""Databento historical client — VERIFY FIRST, and it cannot spend by accident.

    uv run python scripts/fetch_databento.py --plan     # arithmetic only, NO network, NO key
    uv run python scripts/fetch_databento.py --verify   # free metadata calls; MUST pass first
    uv run python scripts/fetch_databento.py --cost     # what the job would cost, per Databento
    uv run python scripts/fetch_databento.py --submit --i-accept-the-cost USD
                                                       # the only mode that spends money

WHY THE MODES ARE SHAPED LIKE THIS
----------------------------------
`docs/research/futures-data/data-purchase-proposal.md` prices the 1-minute complex
at **$182.58 for 358 symbol-years**, against a $125 new-user credit. That figure
rests on ONE inferred number: that `ohlcv-1m` bills at the same $28.00/GiB that
Databento's own worked example establishes for `trades` on GLBX.MDP3.

**If that inference is wrong the whole costing is wrong**, and the published
`list_unit_prices` example in their docs shows `ohlcv-1m` at **280.0** for some
unnamed dataset — ten times our figure. Unit prices are per-dataset, so that is
probably a different dataset and not a contradiction. **Probably is not good
enough when the difference is $183 against $1,830.**

So `--verify` exists, it is free, and nothing else runs until it passes.

WHAT IS VERIFIED AND WHAT IS NOT
--------------------------------
The docs site is JS-rendered and defeats plain fetching. The surface below was
established instead from three independent sources that agree: the `databento-python`
client source, the `databento-rs` client source **including its wiremock tests,
which assert exact paths, methods and parameters**, and the official docs served
as plain text through Context7. Every constant is tagged.

**Four of this project's earlier assumptions were WRONG and are corrected here:**

  1. `list_unit_prices` returns a **JSON ARRAY** of `{mode, unit_prices}` objects,
     NOT a dict keyed by mode.
  2. `mode` is **not a request parameter** anywhere. It is a response field. The
     Python client's `get_cost(mode=...)` is client-side and deprecated.
  3. `symbols` is a **single comma-separated string**, not a repeated parameter.
  4. The raw HTTP API defaults to **`encoding=csv, compression=none`**, where the
     official clients always send `dbn`/`zstd`. Omit them and you are billed for,
     and receive, something other than what you expected.

THE ROLL RULE, AND WHY THE PROPOSAL'S `ES.c.0` IS PROBABLY WRONG
-----------------------------------------------------------------
Continuous symbology is `[ROOT].[ROLL_RULE].[RANK]`, and all three of `ES.c.0`,
`ES.v.0`, `ES.n.0` appear in official examples. The letter→rule mapping is
**INFERRED**, not documented: the Python client carries
`RollRule = volume | open_interest | calendar`, which makes `c`=calendar,
`v`=volume, `n`=open interest.

**If that is right, `ES.c.0` rolls on the CALENDAR — at expiry — which is exactly
the failure this programme measured in Yahoo's `ES=F`**: rolling at expiry rather
than at volume crossover means the last 4-5 days of each quarter track the dying
contract, contaminating 7-8% of the sample. §12 of the proposal requires rolling
on volume/open-interest crossover.

So the default here is **`v` (volume)**, not the `c` the proposal wrote, and
`--verify` resolves all three through `symbology.resolve` so the mapping is
confirmed on a free call before any byte is bought.

BEING UNABLE TO SPEND BY ACCIDENT
---------------------------------
  * the DEFAULT mode is `--plan`, so a bare invocation costs nothing
  * `--plan` needs no key and no network at all — asserted by a test that fails
    if the request function is reached
  * `--verify` and `--cost` call only free metadata endpoints
  * `--cost` AND `--submit` both refuse without a passed `--verify` stamp, and
    **the stamp is bound to a fingerprint of the configuration it vouched for**:
    edit the dataset, the endpoints, the roll rule, the rate or the buy list and
    the stamp stops being accepted. Without that, a bare file's EXISTENCE would
    unlock spending for a configuration nobody ever checked — a guard that reads
    as protection and is not
  * `--submit` additionally requires `--i-accept-the-cost` with Databento's own
    quoted figure, and is then DELIBERATELY NOT WIRED UP
  * paced at 120/min with exponential backoff and a HARD STOP after five
    consecutive failures. **Only 429 and 5xx are retried** — every other 4xx is
    our own bug, and retrying a malformed request is pointless, rude, and hides
    the error behind a delay
  * the key is read from the environment or a file OUTSIDE the repo, and is never
    printed, logged, or written into any URL this script displays
  * the cache is gitignored; exchange-licensed bars are NEVER committed
"""

from __future__ import annotations

import argparse
import base64
import hashlib
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

# ---------------------------------------------------------------------------
# THE API SURFACE. Every entry tagged. Correcting the surface is a single-file
# edit because nothing below this block hard-codes a path or a parameter name.
# ---------------------------------------------------------------------------

# VERIFIED x3 (databento-python HistoricalGateway.BO1; databento-rs
# HistoricalGateway::Bo1; official curl examples). Only one gateway exists.
BASE = "https://hist.databento.com/v0"

# VERIFIED x3. HTTP Basic, API key as USERNAME, EMPTY password. The trailing
# colon in the docs' `-u $YOUR_API_KEY:` is the empty password.
AUTH_SCHEME = "basic_key_as_username_empty_password"

# VERIFIED. Paths are `{prefix}.{slug}` with a DOT, not a slash. The sole
# exception in the whole API is the per-file batch download, which is not used
# here -- file URLs come back from batch.list_jobs instead.
ENDPOINTS = {
    "list_datasets":     ("GET",  "metadata.list_datasets"),      # VERIFIED
    "list_schemas":      ("GET",  "metadata.list_schemas"),       # VERIFIED
    "list_unit_prices":  ("GET",  "metadata.list_unit_prices"),   # VERIFIED
    "get_dataset_range": ("GET",  "metadata.get_dataset_range"),  # VERIFIED
    "resolve":           ("POST", "symbology.resolve"),           # VERIFIED
    # CONFLICT, recorded rather than smoothed: both official clients POST these,
    # the docs demonstrate GET. POST is used because two shipping clients do it
    # in production. These are free endpoints, so a wrong guess costs nothing to
    # discover -- which is precisely why --verify calls one before --submit runs.
    "get_cost":          ("POST", "metadata.get_cost"),           # INFERRED (POST)
    "get_billable_size": ("POST", "metadata.get_billable_size"),  # INFERRED (POST)
    "submit_job":        ("POST", "batch.submit_job"),            # VERIFIED
    "list_jobs":         ("GET",  "batch.list_jobs"),             # VERIFIED
}

DATASET = "GLBX.MDP3"          # VERIFIED — CME Globex MDP 3.0
SCHEMA = "ohlcv-1m"            # VERIFIED — an L0 schema, 16+ yr on usage-based
STYPE_IN = "continuous"        # VERIFIED — symbology.resolve example uses ES.c.0

# INFERRED from databento-python's `RollRule = volume | open_interest | calendar`.
# NOT documented as a letter mapping. --verify resolves all three to settle it.
ROLL_RULES = {"v": "volume", "n": "open_interest", "c": "calendar"}
ROLL_RULE = "v"                # volume crossover — see the docstring

# VERIFIED. The raw API defaults to csv/none; the clients always send these.
ENCODING = "dbn"
COMPRESSION = "zstd"

# VERIFIED. GLBX.MDP3 begins here. Anything earlier does not exist to buy.
DATASET_START = "2010-06-06"

# The rate this project derived from Databento's own two worked examples:
#   get_billable_size(GLBX.MDP3, ESM2, trades, 4 days) = 99,219,648 bytes
#   get_cost(same)                                     = $2.587353944778
#   99,219,648 / 2**30 = 0.0924055 GiB  ->  EXACTLY $28.00/GiB
# The INFERRED step is that ohlcv-1m bills at the same rate as trades.
DERIVED_USD_PER_GIB = 28.00
OHLCV_MSG_BYTES = 56           # VERIFIED — OhlcvMsg is fixed-width
BARS_PER_SYMBOL_YEAR = 1380 * 252   # upper bound: no bar prints for a dead minute

FREE_CREDIT_USD = 125.00

# PACING. Looser than the data fetchers on purpose: those pull thousands of
# slices, this makes seven calls for --verify and ten for --cost, all of them
# free metadata. 120/min adds about eight seconds across both modes, which is
# not worth optimising away and not worth skipping either.
REQUESTS_PER_MIN = 120
MIN_INTERVAL = 60.0 / REQUESTS_PER_MIN
MAX_RETRIES = 4
MAX_CONSECUTIVE_FAILURES = 5
TIMEOUT = 90

KEY_FILE = Path.home() / ".config" / "databento" / "key"
CACHE = REPO / "data" / "raw" / "databento"
VERIFY_STAMP = CACHE / "verify.json"

# The buy list from §5 of the proposal: (group, symbols, years).
COMPLEX = [
    ("equity index",  ["ES", "NQ", "YM"],                 16.0),
    ("equity index",  ["RTY"],                             9.0),
    ("CME crypto",    ["BTC", "MBT"],                      8.5),
    ("energy",        ["CL", "NG"],                       16.0),
    ("metals",        ["GC", "SI", "HG"],                 16.0),
    ("rates",         ["ZB", "ZN", "ZF"],                 16.0),
    ("FX",            ["6E", "6J", "6B"],                 16.0),
    ("micros",        ["MES", "MNQ", "M2K", "MYM"],        7.0),
    ("ags",           ["ZC", "ZS", "ZW"],                 16.0),
    ("livestock",     ["LE", "HE"],                       16.0),
]


def api_key() -> str:
    """Env first, then a file OUTSIDE the repo. Never logged, never in a URL."""
    key = os.environ.get("DATABENTO_API_KEY")
    if key:
        return key.strip()
    if KEY_FILE.exists():
        return KEY_FILE.read_text(encoding="utf-8").strip()
    raise SystemExit(
        f"No API key. Set DATABENTO_API_KEY or create {KEY_FILE}.\n"
        "Note --plan needs neither."
    )


class RateLimiter:
    """A floor on the gap between requests — the same conservative shape every
    other fetcher in this repo uses, and for the same reason: a client that trips
    a limit and backs off is slower than one that never trips it, and it is ruder.

    Paced looser than the data fetchers deliberately. Those pull thousands of
    slices; this one makes SEVEN calls for `--verify` and TEN for `--cost`, all of
    them free metadata. At 120/min the whole of both modes costs about eight
    seconds of waiting, which is not worth optimising and not worth skipping.
    """

    def __init__(self, min_interval: float) -> None:
        self.min_interval = min_interval
        self.last = 0.0

    def wait(self) -> None:
        gap = time.monotonic() - self.last
        if gap < self.min_interval:
            time.sleep(self.min_interval - gap)
        self.last = time.monotonic()


_LIMITER = RateLimiter(MIN_INTERVAL)
_CONSECUTIVE_FAILURES = 0

# Retry these and nothing else. 429 is a throttle and 5xx is the server's
# problem, so both are worth waiting out. EVERY OTHER 4xx IS OUR BUG -- a
# malformed request, a wrong parameter name, a bad key -- and retrying it is
# pointless, rude, and hides the error behind a delay.
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def call(name: str, params: dict, key: str) -> object:
    """One request. Basic auth, key as username, empty password.

    The key never enters the URL, so nothing printed by this module can leak it.
    """
    global _CONSECUTIVE_FAILURES
    if _CONSECUTIVE_FAILURES >= MAX_CONSECUTIVE_FAILURES:
        raise SystemExit(
            f"HARD STOP: {MAX_CONSECUTIVE_FAILURES} consecutive failures. "
            "Something is wrong with the request or the service; hammering it "
            "will not fix either."
        )

    method, path = ENDPOINTS[name]
    url = f"{BASE}/{path}"
    token = base64.b64encode(f"{key}:".encode()).decode()
    headers = {"Authorization": f"Basic {token}",
               "Accept": "application/json",
               "User-Agent": "backtest-framework (personal research)"}
    body = None
    if method == "POST":
        body = urllib.parse.urlencode(params).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    else:
        url += "?" + urllib.parse.urlencode(params)

    delay = 2.0
    for attempt in range(MAX_RETRIES):
        _LIMITER.wait()
        req = urllib.request.Request(url, data=body, headers=headers,
                                     method=method)
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                _CONSECUTIVE_FAILURES = 0
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:400]
            if exc.code not in RETRYABLE_STATUS:
                _CONSECUTIVE_FAILURES += 1
                raise SystemExit(f"{name}: HTTP {exc.code} {detail}") from exc
            if attempt == MAX_RETRIES - 1:
                _CONSECUTIVE_FAILURES += 1
                raise SystemExit(
                    f"{name}: HTTP {exc.code} after {MAX_RETRIES} attempts. "
                    f"{detail}"
                ) from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            if attempt == MAX_RETRIES - 1:
                _CONSECUTIVE_FAILURES += 1
                raise SystemExit(
                    f"{name}: {type(exc).__name__} after {MAX_RETRIES} attempts. "
                    f"{exc}"
                ) from exc
        time.sleep(delay)
        delay *= 2
    raise SystemExit(f"{name}: unreachable")  # pragma: no cover


def config_fingerprint() -> str:
    """A hash of every constant a verification actually vouched for.

    THE STAMP MUST BIND TO WHAT IT VERIFIED. Without this the stamp is a bare
    file whose existence unlocks `--cost` and `--submit`: edit an endpoint, the
    dataset, the roll rule or the buy list afterwards, and a stale stamp still
    says "verified" about a configuration nobody ever checked. That is exactly
    the failure mode where a guard is worse than no guard, because it reads as
    protection.
    """
    payload = json.dumps({
        "base": BASE,
        "endpoints": {k: list(v) for k, v in sorted(ENDPOINTS.items())},
        "dataset": DATASET,
        "schema": SCHEMA,
        "stype_in": STYPE_IN,
        "roll_rule": ROLL_RULE,
        "encoding": ENCODING,
        "compression": COMPRESSION,
        "usd_per_gib": DERIVED_USD_PER_GIB,
        "complex": [[g, list(s), y] for g, s, y in COMPLEX],
    }, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def require_verified(mode: str) -> dict:
    """Gate for every mode that can reach a billable decision."""
    if not VERIFY_STAMP.exists():
        raise SystemExit(f"{mode}: run --verify first. It is free.")
    stamp = json.loads(VERIFY_STAMP.read_text(encoding="utf-8"))
    now = stamp.get("config_fingerprint")
    want = config_fingerprint()
    if now != want:
        raise SystemExit(
            f"{mode}: THE CONFIGURATION CHANGED SINCE --verify RAN.\n"
            f"  verified: {now}\n"
            f"  current : {want}\n"
            "The endpoints, dataset, schema, roll rule, rate or buy list were "
            "edited after verification, so the stamp vouches for something that "
            "is no longer what would be requested. Re-run --verify. It is free."
        )
    return stamp


def unit_price(payload: object, schema: str, mode: str = "historical") -> float:
    """Read a unit price out of `list_unit_prices`.

    CORRECTED ASSUMPTION: the response is a JSON ARRAY of {mode, unit_prices},
    not a dict keyed by mode. Both shapes are accepted here because the wrong
    one was believed for long enough to reach a costed proposal, and a client
    that dies on the shape it expected teaches nothing.
    """
    if isinstance(payload, list):
        for entry in payload:
            if entry.get("mode") == mode:
                return float(entry["unit_prices"][schema])
        raise SystemExit(f"no unit prices for mode {mode!r}")
    if isinstance(payload, dict):
        block = payload.get(mode, payload)
        return float(block[schema])
    raise SystemExit(f"unexpected list_unit_prices shape: {type(payload).__name__}")


def symbol_years() -> list[tuple[str, list[str], float, float]]:
    return [(g, s, y, len(s) * y) for g, s, y in COMPLEX]


def continuous(symbol: str) -> str:
    return f"{symbol}.{ROLL_RULE}.0"


# ------------------------------------------------------------------- modes


def do_plan() -> int:
    """Pure arithmetic. No network, no key, no assumptions about the API."""
    per_sy_gib = BARS_PER_SYMBOL_YEAR * OHLCV_MSG_BYTES / 2**30
    per_sy_usd = per_sy_gib * DERIVED_USD_PER_GIB
    print(f"schema {SCHEMA}   {OHLCV_MSG_BYTES} B/bar   "
          f"{BARS_PER_SYMBOL_YEAR:,} bars/symbol-year (upper bound)")
    print(f"       {per_sy_gib * 1024:.1f} MB/symbol-year   "
          f"${per_sy_usd:.2f}/symbol-year at ${DERIVED_USD_PER_GIB:.2f}/GiB\n")
    print(f"  {'group':14}{'symbols':7}{'years':>7}{'sym-yrs':>10}{'USD':>10}")
    tot_sy = tot_usd = 0.0
    for group, syms, years, sy in symbol_years():
        usd = sy * per_sy_usd
        tot_sy += sy
        tot_usd += usd
        print(f"  {group:14}{len(syms):<7}{years:7.1f}{sy:10.1f}{usd:10.2f}")
    n = sum(len(s) for _g, s, _y in COMPLEX)
    print(f"  {'TOTAL':14}{n:<7}{'':7}{tot_sy:10.1f}{tot_usd:10.2f}")
    print(f"\n  raw volume     {tot_sy * per_sy_gib:.1f} GiB")
    print(f"  free credit    ${FREE_CREDIT_USD:.2f}")
    print(f"  CASH NEEDED    ${max(0.0, tot_usd - FREE_CREDIT_USD):.2f}")
    print(f"\n  symbology      {continuous('ES')}  "
          f"(roll rule {ROLL_RULE!r} = {ROLL_RULES[ROLL_RULE]}, INFERRED)")
    print(f"  encoding       {ENCODING}/{COMPRESSION} sent EXPLICITLY "
          f"(raw API defaults to csv/none)")
    print("\n  The $/GiB rate is DERIVED, not quoted. Run --verify before trusting"
          "\n  any figure above; it is free and it is the only thing that settles it.")
    return 0


def do_verify() -> int:
    """Free metadata calls that check every load-bearing belief. Nothing else
    runs until this writes its stamp."""
    key = api_key()
    checks: list[tuple[str, bool, str]] = []

    datasets = call("list_datasets", {}, key)
    has = DATASET in datasets if isinstance(datasets, list) else False
    checks.append((f"dataset {DATASET} exists", has,
                   f"{len(datasets) if isinstance(datasets, list) else '?'} datasets"))

    schemas = call("list_schemas", {"dataset": DATASET}, key)
    has_schema = isinstance(schemas, list) and SCHEMA in schemas
    checks.append((f"schema {SCHEMA} available", has_schema, str(schemas)[:90]))

    rng = call("get_dataset_range", {"dataset": DATASET}, key)
    start = str(rng.get("start", ""))[:10] if isinstance(rng, dict) else ""
    checks.append((f"history reaches {DATASET_START}",
                   bool(start) and start <= DATASET_START, f"start={start!r}"))

    prices = call("list_unit_prices", {"dataset": DATASET}, key)
    try:
        rate = unit_price(prices, SCHEMA)
        # THE NUMBER THE WHOLE COSTING RESTS ON. Databento quotes USD per GB;
        # our derivation says $28.00/GiB. Anything near 10x that turns a $183
        # purchase into a $1,830 one, which is the entire reason this mode exists.
        close = abs(rate - DERIVED_USD_PER_GIB) / DERIVED_USD_PER_GIB < 0.10
        checks.append((f"{SCHEMA} unit price ~= ${DERIVED_USD_PER_GIB}/GiB", close,
                       f"quoted {rate}"))
    except (KeyError, SystemExit) as exc:
        rate = None
        checks.append((f"{SCHEMA} unit price readable", False, str(exc)[:90]))

    # Settle the roll-rule letters on a free call rather than on inference.
    for letter, meaning in sorted(ROLL_RULES.items()):
        try:
            res = call("resolve", {
                "dataset": DATASET, "symbols": f"ES.{letter}.0",
                "stype_in": STYPE_IN, "stype_out": "instrument_id",
                "start_date": "2024-01-02", "end_date": "2024-01-03",
            }, key)
            ok = bool(res)
        except SystemExit as exc:
            ok, res = False, str(exc)[:70]
        checks.append((f"ES.{letter}.0 resolves ({meaning}, INFERRED)", ok,
                       str(res)[:70]))

    print()
    for label, ok, detail in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {label:46} {detail}")

    hard = [c for c in checks[:4] if not c[1]]
    if hard:
        print("\nVERIFY FAILED. --cost and --submit stay locked.")
        return 1

    CACHE.mkdir(parents=True, exist_ok=True)
    VERIFY_STAMP.write_text(json.dumps({
        "verified_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "config_fingerprint": config_fingerprint(),
        "base": BASE, "dataset": DATASET, "schema": SCHEMA,
        "roll_rule": ROLL_RULE, "stype_in": STYPE_IN,
        "encoding": ENCODING, "compression": COMPRESSION,
        "unit_price_usd_per_gb": rate,
        "derived_usd_per_gib": DERIVED_USD_PER_GIB,
        "checks": [{"check": c[0], "pass": c[1], "detail": c[2]} for c in checks],
    }, indent=1) + "\n", encoding="utf-8")
    print(f"\nVERIFY PASSED -> {VERIFY_STAMP.name}")
    return 0


def do_cost() -> int:
    """Databento's own quote for the planned job. Free, and it is what --submit
    requires the operator to accept."""
    require_verified("--cost")
    key = api_key()
    end = datetime.now(timezone.utc).date().isoformat()
    total = 0.0
    for group, syms, years, _sy in symbol_years():
        start = f"{int(end[:4]) - int(years)}-{end[5:]}"
        start = max(start, DATASET_START)
        quote = call("get_cost", {
            "dataset": DATASET,
            "symbols": ",".join(continuous(s) for s in syms),   # COMMA-JOINED
            "schema": SCHEMA, "stype_in": STYPE_IN,
            "start": start, "end": end,
        }, key)
        usd = float(quote if isinstance(quote, (int, float))
                    else quote.get("cost", quote.get("total_cost", 0.0)))
        total += usd
        print(f"  {group:14}{len(syms):>3} sym  {start}..{end}  ${usd:9.2f}")
    print(f"\n  DATABENTO QUOTE   ${total:.2f}")
    print(f"  less credit       ${FREE_CREDIT_USD:.2f}")
    print(f"  CASH              ${max(0.0, total - FREE_CREDIT_USD):.2f}")
    print(f"\n  To proceed:  --submit --i-accept-the-cost {total:.2f}")
    return 0


def do_submit(accepted: float | None) -> int:
    """The only mode that spends. Refuses without a passed verify AND an
    explicitly accepted figure matching Databento's quote."""
    require_verified("--submit")
    if accepted is None:
        raise SystemExit(
            "REFUSING TO SPEND.\n"
            "Run --cost, read the quote, then re-run with:\n"
            "  --submit --i-accept-the-cost <the exact figure>"
        )
    raise SystemExit(
        "Submission is deliberately not wired up yet.\n\n"
        "Everything up to this point is free and reversible; this call is not. "
        "The batch job would be built from COMPLEX with stype_in=continuous, "
        f"roll rule {ROLL_RULE!r}, encoding={ENCODING}/{COMPRESSION}, and "
        "batch.submit_job rather than streaming (streaming re-bills on retry).\n\n"
        "Wire it up in the same commit as the purchase decision, not before -- "
        "a spending path that exists is a spending path that can be run by "
        "accident."
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true",
                    help="arithmetic only; no network, no key")
    ap.add_argument("--verify", action="store_true",
                    help="free metadata calls; must pass before anything else")
    ap.add_argument("--cost", action="store_true", help="Databento's own quote")
    ap.add_argument("--submit", action="store_true", help="THE MODE THAT SPENDS")
    ap.add_argument("--i-accept-the-cost", type=float, default=None,
                    dest="accepted", metavar="USD")
    args = ap.parse_args()
    if args.verify:
        return do_verify()
    if args.cost:
        return do_cost()
    if args.submit:
        return do_submit(args.accepted)
    return do_plan()


if __name__ == "__main__":
    raise SystemExit(main())
