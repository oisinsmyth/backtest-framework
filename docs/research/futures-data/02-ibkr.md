# 02 — Interactive Brokers as a source of free intraday CME futures history

Research date: 2026-09-01. Lane: IBKR (TWS API + Client Portal / Web API).
Requirement being tested: ES/NQ/RTY/YM (+ CL, GC, ZB, 6E), 15-minute or finer, 10+ years,
full ~23-hour Globex session, programmatic, stitchable to a continuous series.

---

## VERDICT FIRST

**IBKR cannot supply 10 years of intraday CME futures history. The hard ceiling is
approximately 2 years, and it is a documented, non-negotiable server-side limit.**

The blocker is one sentence in IBKR's own documentation:

> "Expired futures data older than two years counting from the future's expiration date"

— listed under *Unavailable Historical Data*
([historical_limitations.html](https://interactivebrokers.github.io/tws-api/historical_limitations.html)).

Restated affirmatively on the contracts page:

> "Historical data for futures is available up to 2 years after they expire by setting the
> includeExpired flag within the Contract class to True."

— ([basic_contracts.html](https://interactivebrokers.github.io/tws-api/basic_contracts.html))

Because a listed ES contract only trades for ~1 year before expiry, and IBKR purges it 2 years
after expiry, the deepest stitchable series you can assemble *today* from expired contracts is
roughly **2–3 years back from now**, not 10. The continuous-futures (`CONTFUT`) route does not
rescue this — see §2 — because IBKR refuses `endDateTime` on CONTFUT requests, so you cannot
page backwards through it at all.

Everything else about IBKR is good: the session coverage is right (full Globex via `useRTH=0`),
the cost is effectively zero for an existing account, and the pacing limits are survivable.
The depth is what kills it.

**Sizing for what IS achievable:** ~2 years of 15-min, full-session, for all 8 symbols is
roughly **200–400 paced requests, i.e. under 2 hours of wall-clock**, at $0–10/month. That is
a perfectly good *recent-history* source. It is not a 10-year backtest corpus.

---

## 1. What the TWS API actually serves

### 1.1 `reqHistoricalData` signature

Parameters, per [historical_bars.html](https://interactivebrokers.github.io/tws-api/historical_bars.html):

| Parameter | Meaning |
|---|---|
| `tickerId` | unique request id |
| `contract` | `IBApi.Contract` |
| `endDateTime` | request end; empty string = "now" |
| `durationString` | how far back from `endDateTime` |
| `barSizeSetting` | granularity |
| `whatToShow` | data type |
| `useRTH` | "Whether (1) or not (0) to retrieve data generated only within Regular Trading Hours" |
| `formatDate` | date formatting |
| `keepUpToDate` | stream updates (API v973.03+) |

### 1.2 Valid bar sizes (verbatim)

> "1 secs, 5 secs, 10 secs, 15 secs, 30 secs, 1 min, 2 mins, 3 mins, 5 mins, 10 mins, 15 mins,
> 20 mins, 30 mins, 1 hour, 2 hours, 3 hours, 4 hours, 8 hours, 1 day, 1 week, 1 month"

`15 mins` is present. Requirement met on granularity.

### 1.3 Valid duration units (verbatim)

> "S (Seconds), D (Day), W (Week), M (Month), Y (Year)"

### 1.4 THE DURATION / BAR-SIZE TABLE ("Step Sizes")

Reproduced from
[interactivebrokers.github.io/tws-api/historical_limitations.html](https://interactivebrokers.github.io/tws-api/historical_limitations.html).
This is IBKR's own table and it is stated as *duration → allowed bar sizes*, i.e. read it
backwards to get "max duration for a given bar size":

| Duration | Allowed Bar Sizes |
|---|---|
| 60 S | 1 sec - 1 mins |
| 120 S | 1 sec - 2 mins |
| 1800 S (30 mins) | 1 sec - 30 mins |
| 3600 S (1 hr) | 5 secs - 1 hr |
| 14400 S (4 hr) | 10 secs - 3 hrs |
| 28800 S (8 hrs) | 30 secs - 8 hrs |
| 1 D | 1 min - 1 day |
| 2 D | 2 mins - 1 day |
| 1 W | 3 mins - 1 week |
| 1 M | 30 mins - 1 month |
| 1 Y | 1 day - 1 month |

**Reading this for our case (15-min bars):** the table's strict reading caps a 15-min request at
`1 W` duration (since `1 M` only admits `30 mins` and coarser). In practice this table is a
guideline, not an enforced schema — IBKR later stated that "Historical Data Limitations for
barSize of '1 mins' and greater have been lifted", and practitioners routinely pull `1 M` and
sometimes `1 Y` of 15-min bars in a single call. Treat `1 M` per request as the safe planning
figure and `1 W` as the guaranteed-safe fallback.

**Caveat on `Y`:** the long-standing IBrokers R binding documents "At present the limit for
years is 1", i.e. no `10 Y` / `30 Y` duration strings. I could not find IBKR restating this in
the current TWS API docs, so treat the 1-year-per-request ceiling as *probable but not
verified from primary source*.

### 1.5 Bars ≤ 30 seconds

> "bars whose size is 30 seconds or less are not available older than six months"

Irrelevant to us (we want 15-min), but it rules out ever reconstructing finer data from ticks
beyond 6 months.

---

## 2. How far back futures history goes

### 2.1 Expired contracts — the 2-year wall

Three independent confirmations:

1. IBKR docs, *Unavailable Historical Data*: "Expired futures data older than two years counting
   from the future's expiration date."
2. IBKR docs, *Basic Contracts*: "Historical data for futures is available up to 2 years after
   they expire by setting the includeExpired flag within the Contract class to True."
3. Practitioner writeup (wrighters.io): summarises the practical lookback as **US equities
   40+ years, futures ~2 years, forex back to ~2005**.

So: yes, IBKR **does** serve expired contracts — that part of the requirement is met, and
`includeExpired=True` on the `Contract` is the mechanism. It just only serves them for 2 years
past expiry.

Community reports match. In [ib_insync discussion #562](https://github.com/erdewit/ib_insync/discussions/562)
a user requesting ES `202301` / `202302` after those expired got
`"No security definition has been found for the request"`, while `202303` and later worked.

### 2.2 Continuous futures (`CONTFUT`) — and why it is not the escape hatch

IBKR does publish its own continuous series, available from the API since TWS v971.
It is **ratio back-adjusted**: per IBKR's own guide, continuous futures are "a series of
monthly/quarterly contracts spliced together", where the ratio of closing prices between the
expiring contract and its successor on the roll date is applied to all prior history
([ibkrguides continuous-futures](https://www.ibkrguides.com/traderworkstation/continuous-futures.htm)).
That is a legitimate stitching method and would have been convenient.

Two disqualifying constraints:

- **"Continuous futures cannot be used with real time data or to place orders, but only for
  historical data."** (fine — we only want history)
- **`endDateTime` must be left as an empty string when requesting historical data for
  continuous futures contracts.** Attempting otherwise returns:
  `"Setting end date/time for continuous future security type is not allowed."`

The second one is fatal for bulk backfill. The standard technique for deep history — walk
backwards, setting `endDateTime` to the oldest bar you just received, repeat until empty — is
**structurally impossible on CONTFUT**. You get exactly one request's worth of duration ending
at "now", and nothing more.

This is not theoretical. A user on the Quantra/QuantInsti community forum attempted **precisely
our requirement — "10 years of 15min historical data" for futures from IBKR** — timed out on
the single-shot request, tried to chunk it with `endDateTime`, and hit that exact error. The
advice given was to fall back to `reqContractDetails(includeExpired=True)`, enumerate the
individual contracts, pull each one separately and splice manually — which then runs straight
into the 2-year wall of §2.1.
([Quantra community thread](https://quantra.quantinsti.com/community/t/fetching-historical-futures-data-from-ibkr/26271))

### 2.3 How deep is CONTFUT itself?

Unresolved. IBKR does not document a depth for CONTFUT. One community log shows
`reqHeadTimeStamp` for **MNQ CONTFUT returning 2019-10-31** — which is close to that
instrument's launch, suggesting CONTFUT head timestamps track instrument inception rather than
a rolling 2-year window. Another secondary source claims continuous futures give "at least
50 days of history at 1-minute resolution, ~10 days at 1-second". These conflict and I could
not resolve them. It is moot regardless: without `endDateTime` you cannot page back to whatever
the head timestamp is, only forward-anchored from now, bounded by max duration per request.

**The one cheap empirical test worth running on the principal's live account:** call
`reqHeadTimeStamp` on `ES CONTFUT` (and on `ES` with `includeExpired`), then try a single
`durationStr="1 Y"`, `barSizeSetting="15 mins"`, `endDateTime=""` CONTFUT request and see how
many bars come back. That settles §2.3 in about 30 seconds and costs nothing.

---

## 3. Market data subscription and cost

### 3.1 The rule that matters

> "Receiving historical data from the API has the same market data subscription requirement as
> receiving streaming top-of-book live data."

and, decisively:

> "unlike TWS, which can create 'delayed charts' for most instruments without any market data
> subscriptions that have data up until 10-15 minutes prior to the current moment; **the API
> always requires Level 1 streaming real time data to return historical data**."

— [historical_data.html](https://interactivebrokers.github.io/tws-api/historical_data.html)

**So: no free tier, and delayed data is not a cheaper path.** You need a live L1 CME
subscription on the account to get *any* historical futures bars out of the API. The TWS GUI
will draw you a delayed chart for free; the API will not hand you the bars.

### 3.2 Prices

`interactivebrokers.com` returns HTTP 403 to automated fetch across every hostname I tried
(`www`, `investors`, `.co.uk`, `.ie`, and the `ibkrcampus.com` alias, which 301-redirects
straight back into the blocked host). **The figures below are therefore secondary-sourced and
should be confirmed in the principal's own Account Management → Market Data Subscriptions
page, which will show the exact current price for his account classification.**

| Subscription | Monthly (USD) | Covers | Waiver |
|---|---|---|---|
| US Securities Snapshot and Futures Value Bundle | 10.00 | Top-of-book for CBOT, CME, COMEX, NYMEX (+ US equities snapshot) | Waived if the account generates ≥ USD 30 commissions/month |
| US Futures Value Bundle PLUS | 5.00 | Adds market **depth** on CBOT/CME/COMEX/NYMEX | Not waivable |
| CME Real-Time (NP, L1) | not verified | CME Group L1 | — |

Sources: quantlabsnet summary of IBKR market data costs; IBKR pricing-page snippets surfaced in
search (top-of-book bundle, the USD 30 commission waiver, and the USD 5 PLUS tier).

**Practical read for an active account:** the Value Bundle is the relevant line, it is
**USD 10/month, and it is waived outright once the account pays USD 30/month in commissions.**
For a principal already trading futures at IBKR this is genuinely free. Depth (PLUS, $5) is not
needed for OHLCV bars — do not buy it.

Note the professional/non-professional classification changes everything about market data
pricing at IBKR. The above assumes non-professional. Professional CME fees are materially
higher and are set by CME, not IBKR.

---

## 4. Pacing limits (verbatim)

From [historical_limitations.html](https://interactivebrokers.github.io/tws-api/historical_limitations.html):

> "The maximum number of simultaneous open historical data requests from the API is 50."

A pacing violation occurs when:

> - "Making identical historical data requests within 15 seconds"
> - "Making six or more historical data requests for the same Contract, Exchange and Tick Type within two seconds"
> - "Making more than 60 requests within any ten minute period"

Plus:

> "When BID_ASK historical data is requested, each request is counted **twice**."

And IBKR's closing position:

> limitations are mandatory and cannot be overcome; clients whose needs exceed IB's offering
> should contact a specialised data provider.

### 4.1 Additional operational notes

- MultiCharts' knowledge base states a pacing violation can be cleared by restarting TWS or
  pressing **Ctrl+Alt+F** in the TWS window; and that after a violation you should not request
  more data for at least 10 minutes.
- IBKR also runs a **"soft" limit** that load-balances client requests against server response —
  the guidance "If your request will return more than a few thousand bars you should consider
  splitting it up" is IBKR's own.
- `ib_insync` / `ib_async` expose `ib.client.setConnectionOptions('+PACEAPI')`, which pushes
  pacing enforcement into TWS itself and prevents the disconnects that otherwise occur during
  large backfills. This is the single most useful practical flag for bulk download.
- Reported practical experience: the *enforced* limits are somewhat more lenient than the
  published ones, and requests for very small bars (1 sec) trip violations far faster than
  minute-and-above bars. Do not build a plan that relies on the leniency.

### 4.2 What the 60/10min limit means in wall-clock

The widely-cited worked example: 2 years of **1-minute** bars for one instrument, pulled in
1-day chunks, is ~504 requests; at 60 requests per 10 minutes that is **~84 minutes for a
single instrument**.

For our actual target — 15-minute bars, pulled in `1 M` chunks — the arithmetic is far kinder
(see §7).

---

## 5. HMDS vs the live feed

There is a distinction, but it is smaller and more mundane than the question implies.

**On the TWS API side**, there is no separately-priced or separately-deep "HMDS" product exposed
to the user. What exists is a *historical data farm* (the `hmds` farm you see in the
`connectionOK`/`Market data farm connection` messages) versus the live market data farms. The
documented behavioural difference is content, not depth:

> "Historical data at IB is filtered for trade types which occur away from the NBBO such as
> combo legs, block trades, and derivative trades. For that reason the daily volume from the
> (unfiltered) real time data functionality will generally be larger than the (filtered)
> historical volume reported by historical data functionality. Differences are also expected in
> other fields such as the VWAP between the real time and historical data feeds."

— [historical_data.html](https://interactivebrokers.github.io/tws-api/historical_data.html)

**This matters for us**: IBKR's historical volume is *filtered* and will not match CME's
official volume. If any signal in the book keys off volume, IBKR bars are not a clean substitute
for exchange data.

**On the Client Portal / Web API side**, `HMDS` was a literal endpoint:

- `/hmds/history` — historical market data server. **Now deprecated and removed from the docs.**
  IBKR's guidance is to use `/iserver/marketdata/history` instead.
- `/iserver/marketdata/history` — the current endpoint. Parameters `conid` (required), `period`,
  `bar`, `startTime`, and **`outsideRth`** (boolean; "if set to true it will include outside of
  regular trading hours in the payload response for contracts that support it").
  Documented **limit of 5 concurrent requests**, and a **maximum of 1000 rows per response**.
  As of Feb 2026 a `source` parameter was added to declare which historical data type to fetch.

The 1000-row cap makes the Web API strictly worse than TWS API for bulk backfill: 1000 rows of
15-min data is about 11 session-days. The TWS API is the right tool.

---

## 6. The 23-hour question — this one IBKR gets right

**Yes. `useRTH=0` returns the full electronic/Globex session including the overnight.**

- `useRTH=1` → "data generated only within Regular Trading Hours". For ES, IBKR does not use the
  exchange's RTH but its own **"Liquid Trading Hours"** — IBKR states it "has determined 'Liquid
  Trading Hours' during which the contract has historically been more liquid", roughly
  09:30–16:15 ET for ES. This is the wrong setting for us.
- `useRTH=0` → everything the contract traded, i.e. IBKR's full **Trading Hours** for the
  contract. For ES that is the Globex session IBKR lists as 17:00 → 15:15 next day, then
  15:30 → 16:00 ET.

This is corroborated by working code: the widely-used
[wrighter historical-data downloader gist](https://gist.github.com/wrighter/dd201adb09518b3c1d862255238d2534)
sets `useRTH = 0` for all intraday requests specifically to capture extended hours, and flips to
`useRTH = 1` only for daily-and-coarser bars "to get accurate daily closing prices". The
kilobytes.substack IBKR sync guide likewise sets `useRTH=0` with the comment "Use all available
data, not just Regular Trading Hours".

**One futures-specific wrinkle to be aware of:** for daily bars, "The close price of daily bars
can be the settlement price if provided by the exchange", and settlement may not arrive until
several hours after the session closes (or Saturday, for a Friday close). Also "A daily bar will
refer to a trading session which may cross calendar days" — so an ES daily bar is the Globex
session, not the calendar day. This only affects daily aggregation, not 15-min bars.

---

## 7. Practical reality — what people actually pull

### Tooling

- **`ib_insync`** (erdewit) — the de facto Python wrapper; now unmaintained, succeeded by
  **`ib_async`** (ib-api-reloaded). Provides a `ContFuture` class. Known trick from the
  maintainer's own guidance: to get the adjusted continuous series you must **not qualify the
  continuous contract itself but a copy of it**, so `lastTradeDateOrContractMonth` stays empty
  on the request.
- **wrighter's CLI downloader** (gist above) — the most complete public example. Behaviour:
  calls `reqHeadTimeStamp` first, warns and terminates early if the requested range predates
  available data; chunks intraday in **1-day** windows walking backwards; uses `1 Y` / `365 D`
  single-shot for daily+; supports futures via `--localsymbol` (e.g. `ESM1`) or `CONTFUT`.
  Notably it implements **no explicit throttling** — the author's answer to the 60-per-10-minutes
  question was "cap args.symbol to 60 symbols". Commenters report tripping pacing violations on
  small bar sizes and `invalid step: 1` errors on `1 secs`.

### The recurring complaints

1. Pacing violations and consequent disconnections during long backfills (fixed by `+PACEAPI`).
2. Expired futures returning "no security definition" — i.e. hitting the 2-year wall.
3. `Setting end date/time for continuous future security type is not allowed` when trying to
   chunk CONTFUT.
4. **Survivorship bias** generally: IBKR's history excludes delisted names and expired
   derivatives, so it is not a clean research corpus.

### Sizing the achievable pull

15-min bars, full Globex session ≈ **92 bars/session**; ~252 sessions/year ≈ **23,200 bars per
symbol-year**.

Assume the safe planning chunk of `1 M` per request (fall back to `1 W` if `1 M` is rejected for
15-min):

| Scope | Requests (1 M chunks) | Requests (1 W chunks) | Wall-clock @ 60/10min |
|---|---|---|---|
| 2 yrs, 1 symbol | ~24 | ~104 | 4 min / 18 min |
| 2 yrs, 8 symbols (ES NQ RTY YM CL GC ZB 6E) | ~190 | ~830 | ~32 min / ~2.3 hrs |

Add contract-boundary overhead for stitching (you request per expired contract, not per calendar
month, so expect ~1.5× the above). **Call it 1–4 hours for the full 8-symbol, 2-year, 15-minute,
full-session pull.** That is entirely tractable — the 60/10min limit is not the binding
constraint here. The 2-year depth is.

### Recommended shape, if IBKR is used at all

1. `reqContractDetails` with `includeExpired=True` per root symbol → enumerate every contract
   still inside the 2-year window.
2. For each contract, `reqHistoricalData` with `barSizeSetting="15 mins"`, `useRTH=0`,
   `whatToShow="TRADES"`, chunking on `endDateTime`.
3. Stitch yourself with an explicit roll rule (volume/OI crossover) and your own back-adjustment
   — do **not** rely on CONTFUT, both because you cannot page it and because IBKR's ratio
   adjustment is opaque and not reproducible from the bars you hold.
4. Run with `+PACEAPI` and a 60-request/10-minute token bucket.

---

## 8. Where this leaves the lane

IBKR is the right shape and the wrong depth.

- Session coverage: **correct** (`useRTH=0`, full Globex).
- Granularity: **correct** (15-min and finer, 1-min available for the whole 2-year window).
- Cost: **effectively free** for an existing commission-paying account.
- Programmatic access: **excellent** (mature API, mature Python wrappers).
- Expired contracts for stitching: **available, but only 2 years deep**.
- Volume field: **filtered, will not match exchange volume**.
- 10-year requirement: **not met, and not workaroundable within IBKR**.

The honest framing: IBKR is an excellent *ongoing capture* source — stand it up now, and in ten
years you own ten years. It is not a *backfill* source. If the book needs 10 years of history
today, IBKR must be paired with a different provider for the deep tail, and IBKR's filtered
volume means the seam between the two sources will not be clean on volume-derived features.

---

## What I could NOT verify

1. **Exact CME market-data subscription pricing from primary source.** Every
   `interactivebrokers.com` hostname (`www`, `investors`, `.co.uk`, `.ie`) returned **HTTP 403**
   to automated fetch, as did the `ibkrcampus.com` alias (301 → blocked host) and the
   `cdcdyn.interactivebrokers.com` webinar PDF. `web.archive.org` is blocked in this
   environment. The USD 10 Value Bundle / USD 30 commission waiver / USD 5 PLUS figures are
   **secondary-sourced** (quantlabsnet, search snippets of the IBKR pricing page) and were not
   read off IBKR's live pricing table. The principal can settle this in one click in Account
   Management.
2. **The current (post-2023 "campus") version of the duration/bar-size table.** The table
   reproduced in §1.4 is from the **deprecated** `interactivebrokers.github.io/tws-api` docs.
   IBKR's current docs at `/campus/ibkr-api-page/twsapi-doc/#step-sizes` exist and are cited by
   third parties, but are behind the 403. The newer docs may present a "max duration per bar
   size" table rather than the "duration → allowed bar sizes" form shown here. I would not bet
   money on the 15-min row without re-checking it manually in a browser.
3. **The maximum `Y` duration string.** "At present the limit for years is 1" comes from the
   IBrokers R package documentation, not from IBKR. Whether `2 Y` / `10 Y` are accepted for
   daily bars today is unconfirmed.
4. **CONTFUT history depth.** Directly contradictory secondary claims: one community log shows
   MNQ CONTFUT head timestamp = 2019-10-31 (≈ instrument inception), another source claims
   ~50 days at 1-min. Unresolved. Trivially testable on the live account via `reqHeadTimeStamp`.
5. **Whether delayed market data (`reqMarketDataType(3/4)`) can ever satisfy a historical
   request.** IBKR's docs say flatly that the API "always requires Level 1 streaming real time
   data to return historical data", which I take as decisive, but I found no test result
   confirming that delayed-only accounts get a hard rejection rather than partial data.
6. **The exact `period` / `bar` enumerations and any deeper limits on the Web API's
   `/iserver/marketdata/history`.** The 5-concurrent and 1000-row figures are from secondary
   summaries of the (403-blocked) official reference.
7. **`ib_async`'s current pacing behaviour** versus `ib_insync`'s. I confirmed `ib_async` is the
   maintained successor but did not read its rate-limiter implementation.
8. **Whether IBKR's 2-year expired-futures window is measured in calendar days or is a coarser
   purge cycle**, i.e. whether you get exactly 24 months or somewhat more in practice.

---

## Sources

- [TWS API: Historical Data Limitations](https://interactivebrokers.github.io/tws-api/historical_limitations.html)
- [TWS API: Historical Bar Data](https://interactivebrokers.github.io/tws-api/historical_bars.html)
- [TWS API: Historical Market Data](https://interactivebrokers.github.io/tws-api/historical_data.html)
- [TWS API: Basic Contracts](https://interactivebrokers.github.io/tws-api/basic_contracts.html)
- [TWS API: Finding Earliest Data Point (reqHeadTimeStamp)](https://interactivebrokers.github.io/tws-api/head_timestamp.html)
- [IBKR Guides: Continuous Futures](https://www.ibkrguides.com/traderworkstation/continuous-futures.htm)
- [wrighters.io: How to get historical market data from Interactive Brokers using Python](https://www.wrighters.io/how-to-get-historical-market-data-from-interactive-brokers-using-python/)
- [wrighter: IB historical data CLI downloader (gist)](https://gist.github.com/wrighter/dd201adb09518b3c1d862255238d2534)
- [Quantra Community: Fetching historical futures data from IBKR](https://quantra.quantinsti.com/community/t/fetching-historical-futures-data-from-ibkr/26271)
- [ib_insync discussion #562: Get ES futures historical data](https://github.com/erdewit/ib_insync/discussions/562)
- [erdewit/ib_insync](https://github.com/erdewit/ib_insync) / [ib_async](https://ib-api-reloaded.github.io/ib_async/)
- [MultiCharts: Avoiding Interactive Brokers Historical Data Pacing Violations](https://www.multicharts.com/trading-software/index.php?title=Interactive_Brokers_Pacing_Violation)
- [WealthLab: "Setting end date/time for continuous future security type is not allowed"](https://wealth-lab.com/Discussion/IBKR-Setting-end-date-time-for-continuous-future-security-type-is-not-allowed-11825)
- [kilobytes.substack: Syncing Historical Data from IBKR](https://kilobytes.substack.com/p/syncing-historical-data-from-ibkr)
- [quantlabsnet: IBKR market data cost for options, futures and other derivatives](https://www.quantlabsnet.com/post/ibkr-market-data-cost-for-options-futures-and-other-derivatives)
- [IBrokers R package: reqHistoricalData](https://rdrr.io/cran/IBrokers/man/reqHistoricalData.html)
- IBKR pricing pages (403 to automated fetch, cited via search snippets):
  [Market Data Pricing](https://www.interactivebrokers.com/en/pricing/market-data-pricing.php),
  [Market Data](https://www.interactivebrokers.com/en/pricing/research-news-marketdata.php)
