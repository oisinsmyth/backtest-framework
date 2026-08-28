# Alpha Vantage: the equity provider

Reference for `scripts/fetch_etf_intraday.py`. Written 2026-08-27; extended 2026-08-28 with
`LISTING_STATUS` and `TIME_SERIES_DAILY_ADJUSTED` for `scripts/fetch_short_universe.py` (D252).

**Every claim here is tagged by provenance**, because the split matters: the
documentation is thin on exactly the points a study depends on, and several of the
load-bearing facts were established by measurement rather than reading.

| tag | meaning |
|---|---|
| **[DOC]** | stated in Alpha Vantage's own documentation, quoted |
| **[MEASURED]** | established here by a live probe call; the evidence is given |
| **[INFER]** | reasoned, not confirmed — treat as provisional |

---

## Why this provider at all

The repo's existing equity and crypto fetchers use yfinance (`EquityDataSource`, D18).
yfinance cannot serve this study:

**[DOC, D160]** yfinance retains **730 days of 1h, 60 days of 15m/30m**, no 4h or 6h
interval at all.

Impulse MACD at `(136, 36)` — the 33-hour window the crypto studies settled on — needs
**4,049 bars of warm-up** before it produces a single live signal. Sixty days of 15m ETF
data is roughly 1,560 bars. **The yfinance window is short by a factor of three before the
strategy starts.** Not thin; impossible.

Alpha Vantage serves any month back to 2000-01, one month per request. That is what makes
an intraday ETF study possible at all.

---

## The endpoint

`TIME_SERIES_INTRADAY`, at `https://www.alphavantage.co/query`.

**[DOC]** Parameters, verbatim from the documentation:

| param | required | default | notes |
|---|---|---|---|
| `function` | yes | — | `TIME_SERIES_INTRADAY` |
| `symbol` | yes | — | one ticker per call |
| `interval` | yes | — | `1min`, `5min`, `15min`, `30min`, `60min` |
| `month` | no | not set | *"in YYYY-MM format… Any month in the last 20+ years since 2000-01 is supported."* |
| `outputsize` | no | **`compact`** | *"`compact` returns only the latest 100 data points… `full` returns… the full intraday data for a specific month in history if the `month` parameter is specified."* |
| `adjusted` | no | **`true`** | *"adjusted by historical split and dividend events. Set `adjusted=false` to query raw (as-traded) intraday values."* |
| `extended_hours` | no | **`true`** | *"4:00am to 8:00pm Eastern… Set `extended_hours=false` to query regular trading hours (9:30am to 4:00pm) only."* |
| `datatype` | no | `json` | `json` or `csv` |
| `entitlement` | no | not set | *"By default… historical data is returned."* Leave unset — we never want realtime |
| `apikey` | yes | — | |

> **`outputsize=full` is mandatory on every historical call.** With `month` set, the
> default `compact` returns **100 bars** — a silent truncation that looks like real data
> and would quietly corrupt a backfill. This is the single easiest way to poison the
> fixture.

**[DOC]** There is **no multi-month request**. One call per `(symbol, month)`. Confirmed
independently by the user. The bulk endpoints are realtime snapshots only and cannot
return historical intraday.

---

## What the documentation does not state — measured

Four probe calls on **SPY, 2024-01**, before committing to ~5,900 requests. All five
answers below are **[MEASURED]**.

### Volume provenance — the question that decided whether the study could run

| | |
|---|---:|
| SPY median session volume, summed from 15m RTH bars, 2024-01 | **66,595,182 shares** |
| SPY consolidated ADV, same period | ~70–90 million |

**Consolidated tape, not a single-venue feed.** A partial feed like IEX carries ~2–3% of
consolidated volume; had the probe returned ~2M we would have been looking at a different
measurement entirely, and a volume-regime signal on a 2% sample is not the signal we think
we are testing. **The documentation never states this** — no mention of "consolidated",
"tape" or SIP anywhere.

Four requests to settle it, before 5,900. Any future study on a new provider should do the
same thing first.

### The rest

| question | answer | evidence |
|---|---|---|
| **Timezone** | `US/Eastern` | stated by the provider inside its own `Meta Data` block — so this one *is* documented, just not in the docs |
| **Timestamp convention** | stamps mark the interval's **OPEN** | first RTH bar `09:30`, last `15:45`. A bar stamped `t` covers `[t, t+15m)` and **is not complete until `t+15m`** |
| **Bars per session** | **26** at RTH, **65** with extended hours | 26 × 15m = 390 min, exactly the 09:30–16:00 session. 21 sessions × 26 = 546 returned |
| **Error format** | **HTTP 200** with `{"Error Message": "..."}` | an unknown ticker returns 155 bytes and a 200 status |

**The timestamp convention is a look-ahead hazard**, not a formatting detail. A bar stamped
09:30 has not happened yet at 09:30. The repo's `lag=1` convention already handles it — a
position held through bar `t` is decided from bar `t−1`'s close — but the fixture's
`.meta.json` records it explicitly so nobody has to rediscover it.

**HTTP 200 on errors means success must be decided structurally.** A fetcher that trusts
the status line will write error bodies into its fixture. `fetch_etf_intraday.py` treats a
payload without a `Time Series (...)` key as a failure however healthy the status looks.

---

## A correction worth keeping

An API-mapping pass read this in the support FAQ —

> *"…adjust the open, high, low, close, **and volume** data by both splits and cash
> dividend events"*

— and concluded that `adjusted=true` (the default) would inject a cumulative,
ticker-specific drift into historical **volume**, which for a volume study would be fatal.
It recommended `adjusted=false` on that basis. The reasoning was sound and the conclusion
was right.

**The premise was wrong. [MEASURED]:**

| SPY, 2024-01-17 12:45 | `adjusted=false` | `adjusted=true` | ratio |
|---|---:|---:|---:|
| close | 471.6800 | 457.8823 | 0.970748 |
| **volume** | **1,681,393** | **1,681,393** | **1.000000** |

Only prices are adjusted. Volume is byte-identical. The FAQ evidently describes the
**daily** adjusted endpoint, not intraday.

**`adjusted=false` remains correct, for a better reason.** Adjusted prices are
*back-adjusted*: the whole history shifts every time a dividend is paid. That breaks D24's
immutable-snapshot requirement directly — the same fixture re-fetched next quarter would
hold different numbers. As-traded values never change. It also matches the daily fixture's
D75 frame, so the two are consistent.

Right answer, wrong reason, corrected — which is why the probe was worth running even
though it agreed with the recommendation.

---

## This project's settings, and why each

| setting | value | why |
|---|---|---|
| `interval` | `15min` | the crypto studies' native rate; D221 established the indicator is scale-free in bars, so matching the *window* is what matters |
| `outputsize` | `full` | mandatory with `month`; the default silently truncates to 100 bars |
| `adjusted` | `false` | immutability (D24), and consistency with the daily fixture's as-traded frame (D75) |
| `extended_hours` | `true` **to fetch** | same request cost, and bars cannot be recovered later without re-fetching 6,000 requests |
| session | **RTH only** to *build* | see below — this is not a preference |
| `entitlement` | unset | historical is the default; we never want realtime |
| span | 2018-01 → 2026-08 | matches the crypto fixture, so the two studies are directly comparable |

### Fetch the superset, build regular hours only

**[MEASURED]**, on AGG 2018-08:

| | bars | sessions | per session | span |
|---|---:|---:|---|---|
| extended hours | 652 | 23 | **27–35** | 07:00–18:30 |
| regular hours | 598 | 23 | **exactly 26, every session** | 09:30–15:45 |

Extended-hours bars exist only where something actually traded. SPY spans the full
04:00–20:00; AGG manages a sparse 07:00–18:30. **That is a liquidity-correlated difference
in bar counts — in a study whose signal is volume.** It would inject the quantity under
test straight into the sampling grid.

Regular hours give a flat 26 bars per session for every symbol. That also sidesteps the
session-completeness problem D161 solves for crypto and **cannot** solve for equities: a
390-minute session does not divide 1440, does not anchor to 00:00 UTC, and shifts with DST,
so `Frequency.__post_init__` would reject it outright. Fetching natively at 15m and never
resampling avoids the problem rather than solving it.

---

## `LISTING_STATUS` — the delisted roster, and the traps in it

Added 2026-08-28 for [D252](decisions/D252-the-dead-inclusive-us-single-name-universe.md), the
dead-inclusive single-name fixture. **The documentation for this endpoint is two sentences in a
spreadsheet add-in reference**, so everything below except the parameter list is [MEASURED].

**[DOC]** `state` is `active` or `delisted`, default `active`. `date` is *"Get listing status for
this date. Default is most recent trading date"*, format `YYYY-MM-DD`, supported from 2010-01-01.

**[MEASURED]** Returns CSV with `symbol, name, exchange, assetType, ipoDate, delistingDate, status`.

| | rows | `assetType == "Stock"` |
|---|---:|---:|
| `state=active` | 14,389 | 8,609 |
| `state=delisted` | 9,449 | 7,469 |

**`state=delisted` with no `date` is CUMULATIVE, not a snapshot.** It returns every symbol the
provider has ever seen delisted — `delistingDate` spanning 1997-04-01 to the day of the call. Dated
calls are strict subsets: 183 rows at `2012-06-29`, 4,099 at `2020-06-30`.

**Dated snapshots are still worth querying, because inclusion is not monotone.** A ticker recycled
by a new issuer drops off the current delisted roster. The union of 16 yearly snapshots holds
**8,187** distinct dead `Stock` tickers against **7,469** from the cumulative call — **718 dead
names, 9.6% of the cohort, that a single call does not return.**

### Three traps, each of which would corrupt a survivorship analysis

**1. `assetType == "Stock"` is not common stock.** Warrants, units, rights and every preferred
series are filed under it: `AA-W`, `AAC-U`, `-P-HIZ`, and 627 five-letter tickers ending `U`.
Filtering by `assetType` alone gives a universe roughly a third of which is not equity.

**2. `delistingDate` is often a roster-refresh stamp.** **601 of the 9,449 delisted rows — 6.4% —
carry `2026-08-27`**, the day the roster was pulled; the next largest single date is `2026-05-28`
with 54. Six hundred companies did not delist on one Thursday. Taking the field at face value puts
601 phantom same-day delistings into any survival curve. Some rows also *contradict* the bars: LTCH
is stamped `2026-05-28` and trades through `2026-08-26`.

**3. Delisting coverage before ~2013 is thin.** By year: 40 (2009), 46, 76, 55, then 140, 185, 382,
559, 766, and roughly 700–1,000 a year after 2016. Several hundred US listings die every year in
reality, so **any "delistings rose over time" reading off this endpoint is an artefact of the
archive**, not a fact about the tape.

### Dead tickers do serve data

**[MEASURED]** `TIME_SERIES_DAILY_ADJUSTED` on delisted symbols returns full history terminating at
the delisting date — AABA 5,016 bars to 2019-11-06, TWTR 2,260 to 2022-10-28, AAI 2,567 to
2011-11-30 — and `SPLITS` / `DIVIDENDS` answer for them too. Not every delisted symbol resolves
(LEHMQ returns `Error Message`), so failures must be counted rather than assumed absent.

---

## `TIME_SERIES_DAILY_ADJUSTED` — three payloads in one request

**[MEASURED]** Fields: `1. open`, `2. high`, `3. low`, `4. close`, `5. adjusted close`, `6. volume`,
`7. dividend amount`, `8. split coefficient`.

**Columns 1–4 are AS-TRADED.** AAPL 1999-11-01 returns `4. close` **77.62** against
`5. adjusted close` **0.58** — the raw columns carry none of the 2000/2005/2014/2020 splits. So this
endpoint serves the same frame as `TIME_SERIES_DAILY` *plus* the corporate actions inline, at one
request instead of three. D24's immutability argument and D75's two-frame separation are unaffected;
splits must still be applied by the consumer.

**The one cost:** the inline actions cover only the window the series covers. AABA's `SPLITS`
endpoint lists three splits where the inline coefficients show two, the missing one predating the
series. Immaterial for a span starting well after the series start; not for one that does not.

**[MEASURED] Throughput is payload-bound, not limit-bound.** A full daily history is a few hundred
kilobytes. A sequential loop paced for 66/min measured **35/min**; four concurrent workers behind one
shared limiter measured **38/min**. Budget ~90 minutes per 3,400 symbols and do not expect
concurrency to fix it.

---

## Rate limits and tiers

**[DOC]** Free tier: **25 requests per day**, and historical intraday is premium-gated
regardless. Unusable for any backfill.

**[DOC]** Premium, monthly — all with *"No daily limits"*:

| req/min | monthly | annual |
|---:|---:|---:|
| **75** | **$49.99** | $499 |
| 150 | $99.99 | $999 |
| 300 | $149.99 | $1499 |
| 600 | $199.99 | $1999 |
| 1200 | $249.99 | $2499 |

This project is on the **75/min tier**. Higher tiers buy hours, not capability — there is
no bulk endpoint to unlock.

### Fetch discipline — a requirement, not a courtesy

- **Paced at 66/min against the 75/min ceiling.** A fetcher that trips the limit and backs
  off is both slower and ruder than one that never trips it.
- **Every slice is cached** under `data/raw/alphavantage/{interval}/{symbol}/{month}.json.gz`
  and **a cached slice is never re-fetched.** An interrupted run resumes; it does not
  restart.
- **Exponential backoff on a throttle response**, and a **hard stop after 5 consecutive
  failures** rather than a retry loop.
- **An empty month is cached too** — a symbol that had not listed yet is a fact, not an
  error, and caching it stops the next run asking again.
- The raw cache is **not committed** (D191's precedent, same as the Binance 1m base). Only
  the derived fixture is.

**One-time manual NETWORK fetch; everything downstream is offline and deterministic** —
the same contract every other fetcher in this repo carries.

---

## Credentials

The key is read from **`ALPHAVANTAGE_API_KEY`**, falling back to
**`~/.config/alphavantage/key`** — deliberately *outside* the repository. It is never
inlined in source and never written to a log; the probe scripts redact it from printed
URLs. `.gitignore` carries `*.key`, `.secrets/` and `alphavantage*.txt` as belt-and-braces,
and `data/raw/` was already ignored.

---

## Terms of use

**[DOC]** The Terms of Service (4 pages, Massachusetts law) are **silent** on storage,
caching, retention, redistribution, derived works and attribution. **[INFER]** There is
therefore no clause prohibiting a committed fixture in a private repository — the document
simply does not contemplate storage.

**[DOC]** The live constraint is the personal/non-commercial grant. Usage becomes
*commercial* if, among other criteria:

> *"(iii) You plan to use or provide information accessed through the Alpha Vantage
> Platform as part of any type of commercial activity that allows individuals or entities
> other than User to access information directly or indirectly…*
> *(iv) You are currently employed or have an active affiliation with a financial planning
> advisor, insurance company, investment advisor, investment bank, money manager,
> registered representative, securities broker-dealer…"*

**Two practical consequences.** Criterion (iv) turns on employment status alone and only
the account holder can evaluate it. Criterion (iii) means **making this repository public
would in all likelihood cross the line** — keep it private.

---

## Still unknown

Flagged rather than guessed:

- **No response schema is published.** The docs show query URLs and never a payload. The
  shapes recorded here come from live responses, so they are measured for `15min`/JSON and
  **unverified for CSV and for other intervals**.
- **Nothing is documented about data quality** — no admissions about missing bars,
  zero-volume bars, gaps, or restatement. yfinance's zero-volume rates were 50% / 4% / 15%
  at 1h / 30m / 15m and nobody has explained why, so **D192 requires the empty-bar rate of
  this universe to be measured and reported in any study's pre-registration.**
  `fetch_etf_intraday.py --build` computes it into the fixture's `.meta.json`.
- **Splits are not applied** at `adjusted=false`, by design. Any study needing
  split-adjusted intraday prices must apply them itself, using the free
  `SPLITS` endpoint. As-traded is the frame this fixture ships in.

---

## See also

- `scripts/fetch_etf_intraday.py` — the fetcher, with `--plan` / `--fetch` / `--build`
- `scripts/fetch_short_universe.py` — the dead-inclusive single-name fetcher; the
  `LISTING_STATUS` and `TIME_SERIES_DAILY_ADJUSTED` measurements above were made for it
- `docs/decisions/D252-the-dead-inclusive-us-single-name-universe.md` — what was built on them
- `docs/decisions/D160-intraday-data-reality-and-the-1h-study-base.md` — the yfinance
  retention wall that forced this provider
- `docs/decisions/D161-the-resampling-contract.md` — the UTC-bucket contract that does not
  transfer to equities
- `docs/decisions/D192-zero-volume-at-one-minute-is-real.md` — the empty-bar obligation
- `docs/decisions/D24-immutable-data-snapshots-fetch-once-freeze.md` — why `adjusted=false`
- `docs/decisions/D191-manifest-only-storage-for-large-archives.md` — cache the raw, commit
  the derived
