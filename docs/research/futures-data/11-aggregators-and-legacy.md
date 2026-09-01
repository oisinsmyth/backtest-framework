# Aggregators, legacy free sources, and the long tail

**Research date: 2026-09-01.** Lane: Nasdaq Data Link (Quandl), Stooq, Barchart, Investing.com,
financial-media data pages, Dukascopy, HistData, retail-broker archives, and government sources.

Target being screened against: **ES/NQ/RTY/YM (+CL, GC, ZB, 6E), 15-minute or finer, 10+ years,
the full ~23-hour Globex session, continuous or stitchable, free.**

---

## Bottom line

Two findings dominate this lane, and they point in opposite directions.

1. **Nasdaq Data Link is dead as a free futures source. Completely.** Not degraded — dead. The
   entire free catalogue in 2026 is **one dataset**, and it is a carbon-credit calendar. Every
   piece of CHRIS/SCF/OWF/CME folklore you will find in blog posts and Stack Overflow answers is
   stale. Verified directly against their live catalogue (below). Stop looking here.

2. **Dukascopy is the real find in this lane, and it is stronger than expected.** Free,
   no-account, no-API-key **tick data** for US index CFDs — S&P 500, Nasdaq 100, Dow, *and*
   Russell 2000 — going back to **2012** for the S&P, covering the **full 24-hour session**.
   I verified this by actually downloading files, not by reading a page. It is the only source in
   this lane that meets the granularity, depth, and session requirements simultaneously.

   **The catch, and it is a real one:** these are Dukascopy's own **index CFDs**, not CME futures.
   Bid/ask quotes from a broker's feed, no exchange volume, no contract roll. See the caveats
   section — this determines whether it is usable for your purpose or not.

**Ranked, worth-trying order:**

| # | Source | Why |
|---|---|---|
| 1 | **Dukascopy** | Tick, 2012+, full session, ES/NQ/YM/RTY/CL/GC proxies, genuinely free, verified downloading |
| 2 | **HistData.com** | M1 + tick, 2010-11+, free, no account, current through Aug 2026 — but no YM or RTY proxy |
| 3 | Barchart free tier | Real futures, but shallow and record-capped; useful for cross-checking, not for building an archive |
| 4 | Darwinex | Real tick data, but requires a **funded live account** — a paywall in disguise |
| — | Everything else in this lane | Ruled out; see table |

---

## 1. Nasdaq Data Link (formerly Quandl) — the definitive answer

**This is the single biggest folklore source in free-futures-data lore. Here is what is actually true.**

| field | |
|---|---|
| source + URL | Nasdaq Data Link — https://data.nasdaq.com |
| **still alive in 2026?** | The *platform* is alive. The **free futures offering is entirely gone.** |
| **genuinely free?** | **No.** The free tier is one non-financial dataset. |
| instruments, granularity, history depth | Futures datasets exist but are **all premium**, all **daily settlement**, and **none are CME** |
| **full session or RTH?** | N/A — daily settlement only, never intraday, even historically |
| bulk/programmatic access | API v3 still exists; anonymous calls now blocked by an Imperva/Incapsula WAF (HTTP 403) |
| verified how | **Live catalogue browsed directly in a browser, 2026-09-01** + Nasdaq's own support statement |

### What I verified

I loaded the Nasdaq Data Link catalogue and applied the **"Free"** filter. The complete result set:

> **Carbon Removal Issuance Calendar** — FREE — PUBLISHED BY NASDAQ
> *(1 page, 1 result)*

That is the entirety of Nasdaq Data Link's free catalogue in 2026. With the Free filter applied,
the **Asset Class** facet collapses to a single option, "Other" — there is no Futures, Equities, or
Indexes facet available at all, because no free dataset belongs to any of them.

Clearing all filters, the *whole* catalogue (premium included) is roughly three pages. The futures
products that remain are:

- ICE Futures Settlement Prices (daily settlements, ICE exchanges, back to 2012) — **PREMIUM**
- Chinese Futures Data (Chinese commodity exchanges, to 2004) — **PREMIUM**
- ICE Europe Futures (115+ commodities) — **PREMIUM**
- ICE Canada Futures (canola) — **PREMIUM**
- Euronext.LIFFE Commodities Futures (50+ commodities) — **PREMIUM**

**There is no CME product on the platform at all any more** — free or premium.

### The legacy tables, one by one

| Legacy table | Status 2026 |
|---|---|
| **CHRIS** (Wiki Continuous Futures) | **Retired.** Nasdaq support, quoted verbatim in a public GitHub issue: *"the CHRIS database has been deprecated and is no longer updated on Nasdaq Data Link"* — adding that they have no alternative feed, and that free feeds get pulled when they fail quality standards or break technically. |
| **SCF** (Stevens Continuous Futures) | **Absent from the catalogue.** Was premium in its later years regardless. |
| **CME** (per-contract settlements) | **Absent from the catalogue.** |
| **OWF** (Option Works futures options vol) | **Absent from the catalogue.** |

Dataset landing pages such as `data.nasdaq.com/data/CHRIS-*` return **HTTP 404**.

### On the API

Anonymous, key-less calls to `data.nasdaq.com/api/v3/datasets/{CHRIS,SCF,OWF,CME}/...` return
**HTTP 403** behind an Incapsula bot wall — including from a real, cookie-bearing browser session.
So the API cannot be used to distinguish "dataset removed" from "request blocked" without a key.

**This does not change the conclusion.** The catalogue is authoritative and it is unambiguous: a
free API key in 2026 reaches **no futures data of any kind**. Even in CHRIS's heyday it was
**daily settlement only** — it never carried intraday bars, so it could never have satisfied a
15-minute requirement regardless of its status.

> **Folklore flag.** Any tutorial, blog post, book chapter, or forum answer recommending
> `quandl.get("CHRIS/CME_ES1")` is stale. This includes material published well after the 2018
> Nasdaq acquisition — the pattern persisted in print for years after the data stopped updating.
> The `Qiafow75CKUdZBavHJpA` API key that circulates in search results and sample code is some
> third party's leaked key; do not use it.

---

## 2. Dukascopy — the strong lead, verified by download

| field | |
|---|---|
| source + URL | Dukascopy Bank SA — feed host `https://datafeed.dukascopy.com/datafeed/` |
| **still alive in 2026?** | **Yes — verified by live download on 2026-09-01.** Tooling actively maintained (dukascopy-node last commit 2026-07-24; dukascopy-python at v4.0.1) |
| **genuinely free?** | **Yes.** No account, no API key, no registration. Plain unauthenticated HTTPS GET. |
| instruments, granularity, history depth | 1,499 instruments. US index CFDs at **tick level from 2011–2013**. See table below. |
| **full session or RTH?** | **Full ~24h session — verified empirically**, see the hour-by-hour test |
| bulk/programmatic access | Yes — flat, predictable URL scheme; mature open-source downloaders in Node and Python |
| verified how | **Instrument metadata parsed from source + actual .bi5 tick files downloaded and byte-counted** |

### Instrument coverage for your targets

Parsed from Dukascopy's published instrument metadata (1,499 instruments enumerated):

| Your target | Dukascopy instrument | Tick data from | M1 bars from |
|---|---|---|---|
| **ES** | `USA500.IDX/USD` (US 500 Index) | **2012-01-16** | 2011-09-18 |
| **NQ** | `USATECH.IDX/USD` (US 100 Tech Index) | **2013-01-01** | 2011-09-18 |
| **YM** | `USA30.IDX/USD` (US 30 Index) | **2013-01-01** | 2013-09-30 |
| **RTY** | `USSC2000.IDX/USD` (US Small Cap 2000) | *(placeholder)* | **2018-08-08** |
| **CL** | `LIGHT.CMD/USD` (Light Sweet Crude) | 2013-01-01 | 2011-09-23 |
| — | `BRENT.CMD/USD` | 2010-12-02 | 2010-12-02 |
| **GC** | `XAU/USD` | **2003-05-05** | 2003-05-05 |
| **ZB** | *no US treasury instrument* — closest is `BUND.TR/EUR` (Euro Bund) | 2016-05-02 | 2016-05-02 |
| **6E** | `EUR/USD` (spot) | deep, pre-2010 | deep |

So: **ES ~14 years of tick data, NQ and YM ~13 years, RTY ~8 years, CL ~15 years at M1.**
The ES/NQ/YM/CL depth clears your 10-year preference. RTY does not.

> **Data-quality flag on the metadata itself.** A number of entries carry
> `startHourForTicks: 2000-01-01` — including `USSC2000.IDX`. This is plainly a placeholder
> default, not a real start date (Dukascopy did not have Russell 2000 tick data in 2000). Treat
> the tick-start field as unreliable wherever it reads exactly 2000-01-01, and probe the actual
> feed to find the true start. The M1 start dates look genuine throughout.

### Session coverage — the test that matters

Your hard requirement is the full ~23-hour session, not RTH. I probed `USA500IDXUSD` at four
hours spread across a single ordinary weekday (Wednesday 12 June 2019), UTC:

| Hour (UTC) | US Eastern | Session phase | Result |
|---|---|---|---|
| 02:00 | 22:00 prev. day | Asian session | **200 — 2,006 bytes** |
| 08:00 | 04:00 | European morning | **200 — 5,054 bytes** |
| 14:00 | 10:00 | US RTH | **200 — 9,012 bytes** |
| 20:00 | 16:00 | after US close | **200 — 891 bytes** |

**All four hours carry real ticks.** The byte counts also trace a believable liquidity profile —
heaviest during US RTH, thinnest after the close, real but sparse overnight. This is a genuine
round-the-clock feed, not an RTH product with padding.

Depth and breadth spot-checks (same method):

- `USA500IDXUSD`, **13 June 2012**, 14:00 UTC → 200, 2,123 bytes — confirms the 2012 tick start
- `USATECHIDXUSD`, 12 June 2019, 14:00 UTC → 200, 9,280 bytes
- `USSC2000IDXUSD`, 12 June 2019, 14:00 UTC → 200, 40,322 bytes
- `LIGHTCMDUSD`, 12 June 2019, 14:00 UTC → 200, 16,897 bytes
- `EURUSD`, 10 June 2015, 14:00 UTC → 200, 47,096 bytes

### Access mechanics

URL scheme — note the **zero-based month**, which is the classic trap:

```
https://datafeed.dukascopy.com/datafeed/{INSTRUMENT}/{YYYY}/{MM-1:02d}/{DD:02d}/{HH:02d}h_ticks.bi5
```

`.bi5` files are LZMA-compressed fixed-width binary tick records. One file per instrument-hour.

- A **0-byte 200 response is normal** — it means "no ticks that hour" (weekends, holidays,
  the daily maintenance break). It is not an error. My first probe hit a Saturday and returned
  0 bytes across the board, which is exactly correct behaviour.
- **The host rate-limits aggressively.** Rapid sequential requests draw `HTTP 503` and dropped
  connections. It is transient, not a block — the same URLs succeed when paced. Budget a couple of
  seconds between requests and implement retry-on-503. I also hit a period where the host 503'd
  every request including the metadata endpoint, then recovered minutes later; expect this and
  make your downloader resumable.
- Volume: one instrument-year of tick data is roughly 8,760 files. Use `dukascopy-node` or
  `dukascopy-python` rather than writing your own — both handle the month offset, the LZMA
  decoding, the price scaling factors, and retry logic.

### The caveats that decide whether this is usable

These are **index CFDs on Dukascopy's own book**, not CME futures. Concretely:

- **Not the same instrument.** `USA500.IDX` tracks the S&P 500 index; ES is a futures contract on
  it. They differ by the cost-of-carry basis, which varies over time and jumps around dividends.
  Levels are not interchangeable with ES prints.
- **No exchange volume.** The volume field in `.bi5` is Dukascopy's own indicative liquidity, not
  CME volume. Any strategy or feature depending on real futures volume, or on volume-based bar
  construction, cannot be built from this.
- **No contract roll.** A continuous CFD has no expiry and no roll gaps. This *removes* the
  stitching problem entirely — convenient — but it also means the series does not reproduce the
  roll behaviour a real ES position would experience.
- **Bid/ask only**, no last-trade prints.
- **Single-broker feed.** Quotes reflect one dealer's pricing, including its spread policy and any
  gaps in its own coverage.

**Verdict:** excellent for microstructure-agnostic work — trend, volatility, session-timing, and
cross-asset research on the US indices, where you need many years of fine-grained, full-session
data and do not depend on exchange volume or exact futures levels. **Not a substitute for CME
data** if the work depends on real volume, true futures pricing, or roll mechanics.

---

## 3. HistData.com — solid second option

| field | |
|---|---|
| source + URL | https://www.histdata.com/download-free-forex-data/ |
| **still alive in 2026?** | **Yes — SPXUSD updated 2026-08-31, verified on the live page** |
| **genuinely free?** | **Yes.** No account, no payment. |
| instruments, granularity, history depth | 66 instruments. **M1 bars and 1-second tick**, SPXUSD/NSXUSD from **Nov 2010 → Aug 2026** |
| **full session or RTH?** | **Unverified** — near-certainly near-24h (it is a broker CFD feed), but I could not complete a scripted download to confirm |
| bulk/programmatic access | Monthly zips; download form carries a JS-populated `tk` token that defeats naive scripting |
| verified how | Live instrument list scraped; SPXUSD year-coverage page read directly |

Full instrument list confirmed (66 symbols). The non-FX ones relevant to you:

- **SPX/USD** — S&P 500 → **ES proxy**
- **NSX/USD** — Nasdaq 100 → **NQ proxy**
- **WTI/USD** — crude → **CL proxy**; also **BCO/USD** (Brent)
- **XAU/USD** — gold → **GC proxy** (plus XAU in EUR/GBP/CHF/AUD, and XAG/USD)
- **EUR/USD** → **6E proxy**
- Other indices: GRX/EUR (DAX), ETX/EUR (Euro Stoxx 50), FRX/EUR (CAC), UKX/GBP (FTSE),
  JPX/JPY (Nikkei), AUX/AUD (ASX), HKX/HKD (Hang Seng)
- **UDX/USD is the US Dollar Index, not the Dow.**

**Coverage gaps vs. your target list: no YM proxy and no RTY proxy** — HistData carries no Dow and
no Russell 2000 instrument. It also has no bond instrument, so no ZB proxy. Dukascopy strictly
dominates it on instrument coverage, and beats it on granularity depth for the indices.

SPXUSD year coverage verified directly on the download page: **2010 through August 2026**,
continuous, last updated 2026-08-31 12:44.

**Access friction:** the download form posts to `/get.php` with a hidden `tk` token that is
populated by JavaScript and is empty in the served HTML. Posting without it returns zero bytes —
I confirmed this. Browser downloads work fine; scripted bulk collection needs a helper that
handles the token (the `philipperemy/FX-1-Minute-Data` project is the usual one). **I could not
complete a scripted download in this session**, so the session-hours question for HistData
remains formally unverified.

Same CFD-proxy caveats as Dukascopy apply: not CME instruments, no exchange volume, no roll.

---

## 4. Everything else — ruled out, with reasons

### Stooq.com

| field | |
|---|---|
| source + URL | https://stooq.com |
| **still alive in 2026?** | Site alive; **programmatic access effectively closed** |
| **genuinely free?** | Daily data yes; intraday is the limitation |
| instruments, granularity, history depth | Futures carried under a `.F` convention (`ES.F`, `GC.F`, `CL.F`). **Daily is the offering**; intraday exists but shallow |
| **full session or RTH?** | Moot — daily bars |
| bulk/programmatic access | **Now blocked** |
| verified how | Direct endpoint testing + documentation |

Stooq deserves a specific 2026 note. It has deployed a **SHA-256 proof-of-work JavaScript
challenge** on all requests — the page ships a puzzle that must be solved and POSTed to
`/__verify` before content is served. I implemented the solver and got past it, and the
`/q/d/l/` CSV endpoint still returns **"Access denied"** for equities and indices, and **zero
bytes** for `.f` futures symbols. Behind that sits a second consent wall. Symbol pages return an
identical ~199 KB JavaScript shell regardless of symbol, i.e. no server-rendered content at all.

> **Folklore flag.** The widely-repeated `stooq.com/q/d/l/?s=SYMBOL&i=d` one-liner — the basis of
> `pandas-datareader`'s Stooq reader and many tutorials — **no longer works unauthenticated.**

Even setting access aside, Stooq is a **daily-data site**; its documentation and download UI are
built around the daily interval, and its intraday history is far too short for a 10-year
15-minute requirement. **Ruled out on the merits, not just on access.**

### Barchart

| field | |
|---|---|
| source + URL | https://www.barchart.com/ondemand/api |
| **still alive in 2026?** | Yes |
| **genuinely free?** | Limited free tier; real pricing is quote-on-request |
| instruments, granularity, history depth | Genuine CME futures. `getHistory` does tick / minute / EOD |
| **full session or RTH?** | Not established |
| bulk/programmatic access | `getQuote` + `getHistory` on the free tier; **1,000 records per call** unless `maxRecords` is raised; intraday results cached and **delayed up to 20 minutes** |
| verified how | Vendor API docs and FAQ; **free-tier quotas partially unverified** |

Barchart has the *right* data — actual CME futures — but the free tier's record cap makes
assembling ten years of 15-minute bars impractical, and pricing for anything beyond it is
"contact sales." Barchart also appears as a *premium publisher* on Nasdaq Data Link, which tells
you how they view this data commercially.

**Could not verify:** the exact free-tier call quota, and the separate website download allowance
for logged-in free accounts (my web-search budget was exhausted before I could confirm the
commonly-cited figures — do not trust the numbers floating around without checking).

### Investing.com / investpy

| field | |
|---|---|
| **still alive in 2026?** | `investpy` **broken**; `investiny` is the stopgap |
| **genuinely free?** | Scraping against ToS; not a stable basis for anything |
| verified how | investpy README read directly |

The investpy README still carries its own warning: *"investpy is not working fine currently due to
some Investing.com changes in their APIs."* Investing.com put Cloudflare v2 in front of both
`/instruments/HistoricalDataAjax` and `api.investing.com/api/financialdata/historical`, which
403s the library. The author points users to **`investiny`**, which goes through
`tvc6.investing.com` and does reach intraday data.

**Ruled out.** It is an undocumented private endpoint being scraped against the site's terms,
with a maintainer who describes his own fix as temporary. Not a foundation for a research archive.

> **Folklore flag.** Any guide recommending `investpy.get_index_historical_data(...)` is stale.

### MarketWatch / WSJ / CNBC / Bloomberg

| field | |
|---|---|
| **still alive in 2026?** | Pages alive; data access closed |
| **genuinely free?** | No |
| bulk/programmatic access | **No** |
| verified how | Direct endpoint testing |

- **MarketWatch** — the `downloaddatapartial` CSV endpoint (the one every scraping tutorial uses)
  returns **HTTP 401**. Requires a subscription session. **Folklore flag: this is dead.**
- **CNBC** — the quote service responds, but querying the front-month E-mini (`@ES.1`) returns a
  bare `{"symbol":"@ES.1","code":1}` — no data payload. The historical bars endpoint used by older
  scrapers returns **404**. CNBC's public chart depth is days of intraday at best regardless.
- **WSJ / Bloomberg** — paywalled, no public bulk endpoint, and scraping is squarely against terms.
  **Not attempted.** Neither offers ten years of intraday futures to anonymous users under any
  reading of their terms.

All four are quote-display surfaces, not data sources. **Ruled out.**

### FRED / government and central-bank sources

| field | |
|---|---|
| source + URL | https://fred.stlouisfed.org |
| **still alive in 2026?** | Yes, and genuinely free with a documented API |
| instruments, granularity, history depth | **Daily at best**, and almost no futures |
| verified how | Release catalogue; search UI is JS-gated to scripts |

FRED's futures-derived content is essentially **NYMEX natural gas and crude oil contract
settlement series** (EIA-sourced; the relevant grouping is "Natural Gas Spot and Futures Prices
(NYMEX)", about six series — 1st through 4th month contracts), plus assorted Nasdaq-published
*index* series such as excess-return and decrement indices, which are index levels rather than
futures prices.

**There are no CME equity index futures price series on FRED, and nothing intraday anywhere on the
platform.** FRED is a macroeconomic time-series repository; daily is its finest resolution for
these series. **Ruled out for this purpose** — though it remains the right place for the risk-free
rate and macro series a backtest may need alongside price data.

No other government or central-bank source carries intraday futures prices. Exchanges themselves
are another agent's lane.

### Retail broker archives

| Source | Status | Verdict |
|---|---|---|
| **Darwinex** | Free tick data from **Oct 2017**, index CFDs included, delivered over **FTP** — but **requires a live funded trading account** to request credentials | **Paywalled in practice.** Shallower than Dukascopy and costs an account deposit. Page fetch failed (redirect loop); details from secondary sources — **partially unverified.** |
| **TrueFX** | Alive, free with registration, tick data from **2009**, but **15–16 FX pairs only** | **Ruled out** — no indices, no futures. Relevant only as a 6E proxy, where Dukascopy already does better. |
| **FXCM** | Historically published a free public M1/tick archive covering FX and some indices | **Unverified** — search budget exhausted before I could confirm 2026 status. Worth a look, but expect index coverage thinner than Dukascopy's. |
| **Oanda** | Historical rates via API, tied to an account; FX-centric | **Unverified.** Unlikely to beat Dukascopy on index coverage or depth. |
| **Pepperstone / IC Markets** | No public free historical archive found; both point clients at MT4/MT5 platform history, which is broker-side, shallow, and not bulk-retrievable | **Ruled out** (low confidence — not directly verified). |

---

## Stale folklore, collected

Every one of these appears in currently-indexed tutorials, blog posts, and published books, and
every one is **wrong in 2026**:

1. **`quandl.get("CHRIS/CME_ES1")`** — CHRIS is retired; Nasdaq has confirmed it in writing and
   offers no replacement. Persisted in print long after the data froze.
2. **"Nasdaq Data Link has a generous free tier"** — the free tier is **one carbon-credit dataset**.
3. **"SCF / OWF / CME tables on Quandl"** — all absent from the catalogue.
4. **`stooq.com/q/d/l/?s=...`** — now behind a proof-of-work challenge and returning "Access denied".
   This breaks `pandas-datareader`'s Stooq reader.
5. **MarketWatch `downloaddatapartial`** — HTTP 401.
6. **`investpy`** — broken by Cloudflare; the maintainer says so in his own README.
7. **CNBC historical bars endpoints** — 404.

A 2019 blog post saying a source is free is not evidence about 2026. In this lane the base rate of
folklore being wrong was roughly **seven out of nine**.

---

## What I could not verify

Stated plainly, so nothing here is mistaken for confirmed:

- **Nasdaq Data Link's API behaviour with a valid free key.** Anonymous calls are WAF-blocked
  (403), so I could not directly observe whether legacy CHRIS endpoints return frozen data or 404.
  The catalogue evidence is definitive that nothing free and futures-related is *offered*; whether
  a stale endpoint still answers a keyed request is unknown and, given the data would be years
  out of date and daily-only, not worth pursuing.
- **HistData's session hours.** Blocked by the JS-populated download token. Near-certainly a
  near-24h broker feed, but I did not confirm it from an actual file.
- **Barchart's exact free-tier quotas** and the free website download allowance.
- **FXCM and Oanda current free archives** — web-search budget exhausted.
- **Darwinex's page content** — redirect loop; findings are from secondary sources.
- **Pepperstone / IC Markets** — negative finding based on absence of evidence, not direct checking.

## Recommended next step

**Pull a single instrument-month of Dukascopy `USA500.IDX/USD` tick data and validate it against a
known reference** — bar counts per session, the overnight gap structure, spread behaviour around
the daily break, and the basis against a same-period ES series if you can obtain one from another
agent's lane. That single test tells you whether the CFD-vs-futures gap is tolerable for your
purpose. If it is, Dukascopy solves the granularity, depth, and full-session requirements
outright, and it does so for ES, NQ, YM, RTY, CL, GC, and 6E proxies at once.

If exchange volume or true futures pricing turns out to be non-negotiable, then **nothing in this
lane will serve** — the answer lies in the broker/exchange lanes, not among the aggregators.
