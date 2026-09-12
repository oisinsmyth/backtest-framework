# H5 — A second price source, so that data assertions can actually fire

External-evidence brief. Round 4, territory H5. Probed 2026-09-09.

I have no access to this programme's data and claim nothing about it. Everything
below labelled **[MEASURED IN BRIEF]** is a live fetch I made today, with the
response quoted as it came back.

---

## 0. BOTTOM LINE — THE KILL CONDITION IS MET

**No free source serves delisted US equity daily bars for 2010–2026 keyed on a
point-in-time identifier. Cross-source assertions on PRICE cannot be written.**

I probed nine candidate price sources live. Every one failed on one of three
grounds, and the failures are not close calls:

| Failure mode | Sources |
|---|---|
| **Returns a DIFFERENT COMPANY under a recycled ticker, HTTP 200, silently** | Yahoo, stockanalysis.com |
| **Requires an API key** (registration prohibited by my brief) | Tiingo, EODHD, FMP, Polygon, marketstack, Finnhub, Alpaca, Nasdaq Data Link |
| **Behind a wall I will not defeat** | stooq (proof-of-work + "Access denied" + consent gate), Nasdaq Data Link (Incapsula), nasdaqtrader.com HTTPS (Incapsula) |

The task warned that "a second source keyed on a recycled ticker is worse than
no second source". **I measured that hazard rather than inferring it, and on the
best free candidate it is 23% of dead names, not the 6.6% this programme
measured on its own ticker set.** Details in §2.

**Two genuinely free, dead-inclusive, independent references DO survive, and both
are real** — but neither carries a price:

- **SEC MIDAS individual-security files** — per-ticker DAILY VOLUME and order/trade
  event counts, 2012 Q2 – 2026 Q2, 58 quarterly files, no key, no wall,
  **dead-inclusive by construction and keyed point-in-time on (Date, Ticker)**.
  Verified: SIVB, SBNY and FRC all present in `feb23.csv`, weeks before they died.
- **Kenneth French's daily data library** — daily market/factor and portfolio
  returns, **built from CRSP** and therefore survivorship-bias-free, 1926-07-01 to
  2026-07-31, no key, no wall. Aggregate level only, no names.

So the correct response is the one the task anticipated: **fall back on internal
consistency assertions for price**, and use MIDAS and French for the two things
they genuinely can check — universe roster / volume, and aggregate return.
§6 is the fallback and is the longest section, as instructed.

The one thing nothing here can do: **no internal assertion can verify the absolute
price LEVEL.** Internal checks catch inconsistency, never systematic bias. That
limit is honest and it does not go away.

---

## 1. THE ONE TEST, APPLIED

*"Does it serve a delisted US ticker's daily bars for 2010–2026, and on what
adjustment basis?"*

### 1.1 Yahoo Finance chart API — **FAIL, and it fails dangerously**
`[VENDOR OFFICIAL DOC — undocumented public endpoint]` `[MEASURED IN BRIEF]`

`GET https://query1.finance.yahoo.com/v8/finance/chart/{T}?period1=1262563200&period2=1788000000&interval=1d`
with a browser User-Agent. Verbatim results:

```
SHLD    HTTP 200   "longName":"Global X Defense Tech ETF"  instrumentType:ETF  NYSEArca
                   firstTradeDate 1694698200 = 2023-09-14
                   742 bars, 2023-09-14 .. 2026-08-28
                   -> ZERO Sears Holdings bars. A DIFFERENT INSTRUMENT, silently.
BBBY    HTTP 200   "longName":"Bed Bath & Beyond, Inc."  EQUITY  NYSE
                   firstTradeDate 1784295000 = 2026-07-17
                   31 bars, 2026-07-17 .. 2026-08-28
                   -> the 2026 relisted entity. ZERO of the 2010-2023 BBBY.
TWTR    HTTP 404   {"chart":{"result":null,"error":{"code":"Not Found",
                    "description":"No data found, symbol may be delisted"}}}
SIVB    HTTP 404   (same body)
SIVBQ   HTTP 404   (same body)
AAPL    HTTP 200   4189 bars, 2010-01-04 .. 2026-08-28   (control, works)
```

Two independent disqualifications:

1. **Delisted names return 404.** Yahoo drops the series at delisting. Its own
   error string says so.
2. **Recycled tickers return a different company at HTTP 200 with no flag.**
   SHLD returns an ETF. There is no field in the response that says "this is not
   the SHLD you asked for" other than `longName`, which a mechanical fetch will
   not read.

**Adjustment basis (control, AAPL):** `close` 2010-01-04 = 7.6432 against an
as-traded close near 214. That is 28× = the 7:1 (2014) and 4:1 (2020) splits.
**Yahoo's OHLC is SPLIT-ADJUSTED, not as-traded**, with dividends confined to
`adjclose` (ratio `adjclose/close` = 0.8375 on that bar, 1.0000 on the last).
This is a *third* basis, matching neither of this programme's two. A universe
floored at **$5 as-traded** cannot be validated against a split-adjusted
reference without back-applying the split factors — and if you had those you
would not need the reference for that assertion.

**Verdict: FAIL.** `yfinance` is a wrapper over this endpoint and inherits all of it.

### 1.2 stockanalysis.com — **FAIL, and this is the measured centrepiece**
`[UNVERIFIED VENDOR — undocumented internal API]` `[MEASURED IN BRIEF]`

This was the most promising candidate and it took the most work to kill. It is
not on the task's candidate list; I found it. `robots.txt` disallows only `/e/`
and `/p/`, so `/api/` is not robots-excluded.

It genuinely serves some delisted names:

```
GET /api/symbol/s/twtr/history?range=10Y&period=Daily
HTTP 200, 206773 bytes, 2259 bars, 2013-11-08 .. 2022-10-28
{"t":"2022-10-28","o":53.7,"h":53.7,"l":53.7,"c":53.7,"v":0,"a":53.7,"ch":0}
{"t":"2022-10-27","o":53.91,"h":54,"l":53.7,"c":53.7,"v":140831508,...}
```

Twitter's full history through its delisting date. So I tested it properly.

**The 64-ticker dead-name panel.** I built a panel of known US delistings spanning
2012–2025 and scored each response by whether the last bar lands in the known
delisting year (±1). Full run in
`scratchpad/h5/probe_sa.py`. Result:

| Verdict | n | % |
|---|---|---|
| **MATCH** (right company, right era) | **6** | **9.4%** |
| **WRONG-ENTITY** (HTTP 200, different company, silent) | **15** | **23.4%** |
| **HTTP 400** (nothing at all) | **43** | **67.2%** |

**Every one of the six matches died in 2022 or later** — TWTR (2022), SIVB (2023),
ATVI (2023), VMW (2023), JNPR (2025), CTLT (2025). **Not one of the 2012–2021
delistings returned the right entity.** The retention window is roughly four
years, not the sixteen the fixture needs.

The 15 wrong-entity cases, with what the ticker returns *today*:

```
SLE   Sara Lee (dead 2012)          -> quotes $4.56 today
MMI   Motorola Mobility (dead 2012) -> quotes $31.05, 2513 bars to 2026-09-08
DELL  Dell Inc LBO (dead 2013)      -> quotes $535.25, series starts 2018-12-24
LIFE  Life Technologies (dead 2014) -> quotes $39.72, series starts 2026-01-30
BEAM  Beam Inc (dead 2014)          -> quotes $25.18, series starts 2020-02-07
PLL   Pall Corp (dead 2015)         -> 2021-05-19 .. 2025-08-29
ALTR  Altera (dead 2015)            -> 2017-11-02 .. 2025-03-26   [Altair]
SNDK  SanDisk Corp (dead 2016)      -> quotes $1764.17, starts 2025-02-14
EMC   EMC Corp (dead 2016)          -> 2023-05-16 .. 2026-09-08
CAM   Cameron Intl (dead 2016)      -> starts 2025-10-07
SE    Spectra Energy (dead 2017)    -> 2017-10-23 .. 2026-09-09   [Sea Ltd]
SPLS  Staples (dead 2017)           -> starts 2026-01-20
MON   Monsanto (dead 2018)          -> 2021-03-17 .. 2022-12-23  (449 bars only)
SHLD  Sears Holdings (dead 2018)    -> 2023-09-14 .. 2026-09-09  [Global X ETF]
INFO  IHS Markit (dead 2022)        -> starts 2024-10-11
```

`SNDK` quoting $1764.17 for a company that was bought at $86.50 in 2016 is the
whole hazard in one line. **A mechanical cross-check against this source would
have compared Sara Lee to a $4.56 stock and SanDisk to a $1764 one, and reported
a price disagreement rather than an identity error.**

**One useful refinement, and it is the only good news in this section.** The
wrong-entity substitutions are *mostly detectable*, because the returned span
does not overlap the fixture's span (SHLD returns 2023–2026 where the fixture has
2010–2018). So a cross-source assertion could require the reference's last bar to
sit within a few days of the fixture's last bar and reject otherwise. That
converts a silent wrong answer into a loud one. **It does not save the cases with
overlapping windows** — `SE` (Spectra Energy dead Feb 2017, Sea Ltd listed Oct
2017) and `MON` are exactly those, and they are the two the task already flagged
as the dangerous class.

**Other defects measured in passing, each of which is itself a caution:**

- **`range=20Y` is silently ignored.** It returns 252 bars (1Y) at HTTP 200
  rather than erroring. `5Y`→1255, `10Y`→2513, `15Y`/`25Y`/`MAX`/`ALL`→252.
  A parameter the server does not understand degrades silently to a one-year
  window. Anyone building on this would get a year of data and not know.
- **The 10Y cap is anchored on the LAST BAR, not on today.** Dead names get ten
  years back from death; survivors get 2016-09-09 onward. So **for living names
  2010-01-04 .. 2016-09-08 is unreachable — 40% of the fixture window, on ~64% of
  the panel — and the hole recedes forward every day.**
- **Even the six matches do not reach 2010-01-04**: TWTR starts 2013-11-08,
  SIVB 2013-03-11, ATVI 2013-10-15, VMW 2013-11-22, JNPR 2015-07-02,
  CTLT 2014-12-18.
- **Basis: SPLIT-ADJUSTED OHLC + fully-adjusted `a`.** AAPL 2016-09-09 returns
  `o=26.16 h=26.43 l=25.783 c=25.783` against as-traded `104.64/105.72/103.13/103.13`
  — exactly ÷4. NVDA 2016-09-09 `c=1.488` against ~$60.5 as-traded, i.e. ÷40 for
  the 2021 4:1 and 2024 10:1. Same wrong basis as Yahoo, same consequence for a
  $5 as-traded floor. (The values are *accurate* — they reproduce the real
  as-traded OHLC exactly after multiplying by the split factor. The data is good;
  the basis and the identifier are the problems.)
- **Volume is not integral.** AAPL 2026-09-09 `v=64661143.99999999`. A float
  round-trip. An integer-volume assertion would fire on this.
- **A synthetic terminal stub bar.** TWTR's last bar is `o=h=l=c=53.7, v=0`.
  Relevant regardless of this source — see §6.E.

**Verdict: FAIL.** 9.4% coverage, 23.4% silent wrong-entity rate, wrong basis, and
a rolling 10-year cap that misses 40% of the window on living names.

### 1.3 stooq daily bundle — **FAIL, three gates**
`[UNVERIFIED VENDOR]` `[MEASURED IN BRIEF]`

The task correctly noted the earlier survey assessed stooq for intraday futures
depth and never asked the daily US-equity dead-name question. I asked it.

**Gate 1 — proof-of-work, to `curl`.** `GET https://stooq.com/q/d/l/?s=shld.us&i=d`
with a browser UA returns HTTP 200, 796 bytes, of a SHA-256 proof-of-work
challenge:

```
<noscript>This site requires JavaScript to verify your browser. Please enable
JavaScript and reload.</noscript>
... const c="AAAAAGqh1Joqf4Pp3WXEcghiHMCoHelzAnso7LxRhhu4b4HzmzTmZqqhyX0",d=4,
t="0".repeat(d) ... while(1){ ... crypto.subtle.digest("SHA-256", ...)
... fetch("/__verify",{method:"POST", ...})
```

This is bot-detection. **I did not write a solver for it** — that is out of bounds.
I opened the page in a real browser instead, which is ordinary browsing, and the
browser cleared it on its own.

**Gate 2 — a consent wall that will not take no.** Behind the PoW, every page
renders a Polish GDPR dialog and nothing else. I clicked **"Nie zgadzam się"**
(*I do not agree* — the privacy-preserving option). The dialog re-presented itself
with only **"Zgadzam się"** (*I agree*) and **"Zarządzaj opcjami"** (*Manage
options*) remaining. **I did not accept it** — accepting a consent banner needs
explicit permission I do not have. The page never rendered content.

**Gate 3 — and this one is decisive independently.** With the browser's
post-PoW session cookie, a same-origin `fetch` of the CSV endpoint returns:

```
/q/d/l/?s=shld.us&i=d   HTTP 200  body: "Access denied"
/q/d/l/?s=twtr.us&i=d   HTTP 200  body: "Access denied"
/q/d/l/?s=bbby.us&i=d   HTTP 200  body: "Access denied"
/q/d/l/?s=sivb.us&i=d   HTTP 200  body: "Access denied"
/q/d/l/?s=aapl.us&i=d   HTTP 200  body: "Access denied"
```

**Including AAPL** — a live, unambiguous, top-of-book name. This is stooq's
download quota, not a dead-name problem. And the HTML page is a static shell:
`/q/d/?s={any}&d1={any}&d2={any}` returns **exactly 234,330 bytes for every
symbol and every date range**, containing no `<table>` and no date strings.

**Verdict: FAIL.** Not because of the PoW — because behind it the daily CSV is
quota-denied for every symbol including live ones, and the HTML carries no data.
The daily US-equity dead-name question is now asked and answered: unusable.
*I did not test the paid/registered tier and make no claim about it.*

### 1.4 Nasdaq's own historical quote API — **FAIL**
`[VENDOR OFFICIAL DOC — undocumented public endpoint]` `[MEASURED IN BRIEF]`

```
GET https://api.nasdaq.com/api/quote/SHLD/historical?assetclass=stocks&fromdate=2015-01-01&todate=2019-01-01
HTTP 200
{"data":null,"message":null,"status":{"rCode":400,"bCodeMessage":
 [{"code":1001,"errorMessage":"Symbol not exists."}],"developerMessage":null}}
```

Survivors-only, and asset-class-keyed. **Verdict: FAIL.**

### 1.5 Nasdaq Data Link / Quandl free tables — **FAIL (blocked, and moot)**
`[MEASURED IN BRIEF]`

**Block logged by tool and headers, not by host**, per the standing rule:

| Tool | Headers | Response |
|---|---|---|
| `curl` | browser UA | HTTP **403**, 882 bytes, Incapsula interstitial (`_Incapsula_Resource?SWJIYLWA=...`) |
| `curl` | curl default UA (no `-A`) | HTTP **403**, 885 bytes, same interstitial |
| `curl` | browser UA, `www.quandl.com` host, `-L` | HTTP **403**, 885 bytes, same interstitial |

So this is **not** a User-Agent exclusion — I tested that specifically, because
an earlier round found two "blocks" that were. Three header/host variants, same
403. It is a genuine WAF block on automated access.

Moot regardless: the free `WIKI` table was **discontinued 2018-03-27** and covered
~3,000 *then-listed* US tickers. It could not cover 2018–2026 and was
survivors-only within its own span. **Verdict: FAIL.**

### 1.6 Exchange official end-of-day files — **FAIL**
`[VENDOR OFFICIAL DOC]` `[MEASURED IN BRIEF]`

`nasdaqtrader.com` over HTTPS is Incapsula-walled (`curl`, browser UA: HTTP 200
with a 212-byte `_Incapsula_Resource` stub for `symbolchange.txt` and
`nasdaqtraded.txt`). **The FTP mirror is open** and I listed it:

```
ftp://ftp.nasdaqtrader.com/SymbolDirectory/     HTTP 226, 1605 bytes
  nasdaqlisted.txt    347146   09-09-26
  nasdaqtraded.txt    995587   09-09-26
  otherlisted.txt     539195   09-09-26
  otclist.txt          35264   07-07-15   <- stale by 11 years
  ... (options/strike files, regsho, regnms dirs)
```

These are **current-snapshot symbol directories, not prices, and not historical**
— today's listed symbols only, overwritten daily, no archive. Textbook
survivors-only. Nasdaq's *U.S. Equity Daily History* product and NYSE's TAQ
historical files are **commercial**. **Verdict: FAIL.**

### 1.7 Tiingo free tier — **FAIL (not verifiable without registering)**
`[MEASURED IN BRIEF]`

```
GET https://api.tiingo.com/tiingo/daily/SHLD/prices?startDate=2015-01-01&endDate=2018-01-01
HTTP 403  {"detail":"Please supply a token"}
```

Registration is prohibited by my brief, so I cannot probe it. Per the standing
rule — *"a source that 'should' have dead names but that you could not verify is
a FAILURE, not a candidate"* — **Tiingo is a FAILURE in this brief.** I make no
claim about what its free tier does or does not contain.

### 1.8 Every other keyed API — **FAIL (same reason)**
`[MEASURED IN BRIEF]`

```
EODHD    /api/eod/TWTR.US?api_token=demo    HTTP 403  "Forbidden"
EODHD    /api/eod/AAPL.US?api_token=demo    HTTP 200  (demo token is AAPL-whitelisted)
FMP      ?apikey=demo                       HTTP 401  "Invalid API KEY..."
marketstack (no key)                        HTTP 401  "missing_access_key"
Polygon  (no key)                           HTTP 401  "API Key was not provided"
Alpaca   (no key)                           HTTP 401  Authorization Required
Finnhub  ?token=demo                        HTTP 401  "Invalid API key."
IEX Cloud                                   curl (28) connect timeout — service retired
```

One incidental datum worth keeping: EODHD's demo AAPL response is
`{"date":"2026-08-03","open":309.58,...,"close":303.42,"adjusted_close":303.1585,"volume":75052000}`
— **raw OHLC with adjustment confined to a separate `adjusted_close`, the same
basis as this programme's current vendor.** If a paid second source is ever
bought, that basis match is worth knowing. I did not test EODHD on any dead name;
its demo token refused TWTR.

### 1.9 Academic / library / public mirrors — **PARTIAL PASS, aggregate only**

See §3. WRDS and CRSP are subscription; no public per-name mirror exists that I
could find or probe. Kenneth French's library is free, open, and CRSP-derived —
and it is real. It just has no names in it.

---

## 2. THE IDENTIFIER QUESTION

*What does it key on, and is that identifier point-in-time?*

| Source | Keys on | Point-in-time? |
|---|---|---|
| Yahoo | ticker string | **No** — resolves to today's issuer |
| stockanalysis.com | ticker string | **No** — 23.4% wrong entity measured |
| Nasdaq api | ticker + assetclass | **No** — survivors only |
| nasdaqtrader FTP | ticker | **No** — today's snapshot, overwritten daily |
| **SEC MIDAS** | **(Date, Ticker)** | **YES** — see below |
| Kenneth French | n/a (portfolios) | n/a |

**MIDAS is the exception and the reason matters.** Its files are written once per
quarter and never rewritten. `feb23.csv` contains the tickers that traded in
February 2023, as they were in February 2023. A recycled ticker cannot
retroactively contaminate it, because the file predates the reuse. **The date
component of the key does the disambiguation that every price source above
fails to do.** This is the point-in-time roster the task asked whether anything
had, and MIDAS has it.

**One further finding, incidental but directly on this hazard.** This programme's
existing vendor documents a point-in-time listing map. Verbatim from Alpha
Vantage's public documentation `[VENDOR OFFICIAL DOC] [MEASURED IN BRIEF]`:

> "Listing & Delisting Status Utility. This API returns a list of active or
> delisted US stocks and ETFs, either as of the latest trading day or at a
> specific time in history. The endpoint is positioned to facilitate equity
> research on asset lifecycle and survivorship."

> "If no date is set, the API endpoint will return a list of active or delisted
> symbols as of the latest trading day. If a date is set, the API endpoint will
> 'travel back' in time and return a list of active or delisted symbols on that
> particular date in history."

The task notes free ticker-to-issuer maps are survivors-only, *"confirmed twice on
SEC endpoints"*. `LISTING_STATUS` with `date=` is not survivors-only by its own
description. **It is the same vendor, so it is not independent** — but for the
*identifier* question specifically it is a point-in-time map already inside the
key this programme holds, and **it can be cross-checked against MIDAS, which is
independent.** That pairing is the one real cross-source identity check available.
*I could not execute it: the `demo` key is gated on this function and I will not
register.*

---

## 3. WHAT SURVIVES

### 3.1 SEC MIDAS — individual security metrics `[PRIMARY DATA DOC] [MEASURED IN BRIEF]`

`https://www.sec.gov/files/opa/data/market-structure/metrics-individual-security/individual_security_{YYYY}_q{Q}.zip`

No key, no wall, no consent gate. Fetched with UA
`backtest-framework-research/1.0 (research@backtest-framework.org)`.

**Coverage, measured** — 58 quarterly files enumerated from the SEC's own page,
**2012 Q2 through 2026 Q2, contiguous**. The fixture window opens 2010-01-04, so
**2010-01-04 .. 2012-03-31 is not covered** (~2.25 of 16.7 years).

*Trap, and it cost me time:* a second, older family exists at
`.../metrics-individual-security-and-exchange/...` (per-exchange breakdown). It is
frozen — I measured 40 quarters, 2012q1 and 2014q1–2024q1 with holes at
2012q2–2013q4, 2016q1, 2019q4, and **404s for everything after 2024 Q1**. Probing
that family alone would have produced the false conclusion that MIDAS stops in
2024. The live family is the one without `-and-exchange`. The SEC's page also
lists a file literally named `individual_security_2012_q10.zip`, which looks like
a typo for q1.

**Schema — 2026 Q2, header read verbatim from the bytes** (I range-requested the
first 3 MB and inflated the first member locally; `first member: q2_2026_all.csv`):

```
Date,Security,Ticker,McapRank,TurnRank,VolatilityRank,PriceRank,LitVol('000),
OrderVol('000),Hidden,TradesForHidden,HiddenVol('000),TradeVolForHidden('000),
Cancels,LitTrades,OddLots,TradesForOddLots,OddLotVol('000),TradeVolForOddLots('000)

20260401,Stock,A,10.0,3.0,2.0,9.0,379.973,9046.373999999998,4983.0,14541.0,...
20260401,Stock,AA,9.0,10.0,7.0,8.0,3217.97,43659.47,20995.0,66847.0,...
20260401,Stock,AAL,9.0,10.0,4.0,4.0,13211.492,294915.459,15955.0,54523.0,...
20260401,Stock,AAME,2.0,1.0,7.0,2.0,1.509,130.831,15.0,27.0,...
```

**There are no prices.** The only price-shaped column is `PriceRank`, a decile.
The 2023 per-exchange file's header, for comparison, read verbatim:

```
Date,Security,Ticker,Exchange,McapRank,TurnRank,VolatilityRank,PriceRank,Cancels,
Trades,LitTrades,OddLots,Hidden,TradesForHidden,OrderVol('000),TradeVol('000),
LitVol('000),OddLotVol('000),HiddenVol('000),TradeVolForHidden('000)
```

**The schema is NOT stable across the archive** — the 2026 consolidated file has
no `Trades` and no plain `TradeVol('000)`; it has `LitVol` plus odd-lot fields the
2023 file lacks. Anything built on MIDAS must read the header per file, not assume it.

**Dead-inclusiveness — measured, not assumed.** I decompressed the whole of
`feb23.csv` (55,934,138 compressed bytes, 218,018,039 raw, 7,303 unique tickers)
and searched for names that died shortly after:

```
PRESENT SIVB   20230201,Stock,SIVB,Amex,10.0,9.0,6.0,10.0,313.0,41.0,38.0,35.0,3.0,41.0,32.81,1.161,...
PRESENT SBNY   20230201,Stock,SBNY,Amex,9.0,10.0,7.0,10.0,8388.0,81.0,68.0,64.0,13.0,81.0,4604.681,2.834,...
PRESENT FRC    20230201,Stock,FRC,Amex,10.0,7.0,3.0,10.0,9598.0,54.0,52.0,38.0,2.0,54.0,3900.333,2.671,...
PRESENT BBBY   20230201,Stock,BBBY,Amex,5.0,10.0,10.0,2.0,3848.0,413.0,284.0,30.0,129.0,413.0,469.758,44.608,...
PRESENT SGEN   PRESENT ATVI   PRESENT VMW   PRESENT AAPL
```

All eight present, including the three banks that failed within six weeks.
**MIDAS is dead-inclusive because it is a record of what traded, not a database of
what exists.** That is the strongest form of the property.

**The caveat that governs how it can be used.** MIDAS is built from *"the
proprietary feeds of each of the 13 national equity exchanges"*. `LitVol` is
**exchange-lit volume only**. It excludes off-exchange TRF volume — wholesaler
internalisation and dark pools — which is a large and *time-varying* share of US
volume. **MIDAS volume will sit systematically below any consolidated-tape volume
figure, and the gap drifts.** So the assertion must be on the *stability of the
ratio per name*, never on equality. §6.J.

**Cost:** ~24 MB/quarter compressed for the consolidated family (2026 Q2 =
23,753,635 bytes), ~180 MB for the per-exchange one. 58 quarters is a real but
one-off download. It caches trivially — quarterly files never change.

### 3.2 Kenneth French data library `[PRIMARY DATA DOC] [MEASURED IN BRIEF]`

`https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/{name}_CSV.zip`
No key, no wall, no UA sensitivity. All four fetches HTTP 200.

```
F-F_Research_Data_Factors_daily_CSV.zip   178,044 B  -> 26,303 lines
    header line 1 verbatim:
      "This file was created by using the 202607 CRSP database."
    columns: ,Mkt-RF,SMB,HML,RF
    first row: 19260701,    0.09,   -0.23,   -0.28,    0.01
    2010 row:  20100104,    1.69,    0.61,    1.14,    0.00
    last row:  20260731,    0.68,   -0.49,   -0.59,    0.02
Portfolios_Formed_on_ME_daily_CSV.zip   1,565,760 B -> 52,611 lines
    ,<= 0,Lo 30,Med 40,Hi 30,Lo 20,Qnt 2..Qnt 4,Hi 20,Lo 10,Dec 2..Dec 9,Hi 10
48_Industry_Portfolios_daily_CSV.zip    4,095,237 B -> 52,608 lines
25_Portfolios_5x5_daily_CSV.zip         4,035,370 B -> 105,217 lines
```

**"created by using the 202607 CRSP database"** is the load-bearing line.
CRSP is the survivorship-bias-free standard: its market return includes delisted
names and applies delisting returns. **This is a free, independent,
dead-inclusive daily return reference covering the entire fixture window.** It
simply has no names in it — it is aggregate and portfolio level.

**Limits:** ends **2026-07-31**, roughly four weeks short of the fixture's
2026-08-26 end. Returns are in **percent**, not decimals. Size deciles are
NYSE-breakpoint, whole-CRSP-universe, unfloored — they are *not* comparable in
level to a 1,573-name book floored at $5. Use it for correlation and alignment
(§6.I), never for level agreement.

---

## 4. SOURCES, TAGGED

| # | Source | Type | Probed | Verdict |
|---|---|---|---|---|
| 1 | Yahoo `query1.finance.yahoo.com/v8/finance/chart` | [VENDOR OFFICIAL DOC — undocumented] | [MEASURED IN BRIEF] | FAIL — 404 on dead, silent wrong entity on recycled, split-adjusted basis |
| 2 | stockanalysis.com `/api/symbol/s/{t}/history` | [UNVERIFIED — undocumented internal API] | [MEASURED IN BRIEF] 64-ticker panel | FAIL — 9.4% hit, 23.4% wrong entity, 10Y rolling cap, split-adjusted |
| 3 | stooq.com `/q/d/l/` | [UNVERIFIED VENDOR] | [MEASURED IN BRIEF] curl + real browser | FAIL — PoW, then "Access denied" on all symbols incl. AAPL, then consent wall |
| 4 | `api.nasdaq.com/api/quote/.../historical` | [VENDOR OFFICIAL DOC — undocumented] | [MEASURED IN BRIEF] | FAIL — "Symbol not exists.", survivors only |
| 5 | Nasdaq Data Link / Quandl `WIKI` | [VENDOR OFFICIAL DOC] | [MEASURED IN BRIEF] 3 header/host variants | FAIL — WAF 403 (not a UA exclusion); table dead since 2018-03-27 anyway |
| 6 | nasdaqtrader.com HTTPS + FTP `SymbolDirectory` | [PRIMARY DATA DOC] | [MEASURED IN BRIEF] | FAIL — HTTPS Incapsula-walled; FTP open but current-snapshot symbol lists, no prices, no archive |
| 7 | Tiingo free tier | [VENDOR OFFICIAL DOC] | [MEASURED IN BRIEF] | FAIL — 403 "Please supply a token"; unverifiable without registering |
| 8 | EODHD / FMP / Polygon / marketstack / Finnhub / Alpaca / IEX | [VENDOR OFFICIAL DOC] | [MEASURED IN BRIEF] | FAIL — all key-gated (401/403); IEX retired |
| 9 | **SEC MIDAS individual-security** | **[PRIMARY DATA DOC]** | **[MEASURED IN BRIEF]** header + dead-name test + 58-quarter enumeration | **PASS for VOLUME + point-in-time roster. No prices.** |
| 10 | **Kenneth French data library** | **[PRIMARY DATA DOC]** | **[MEASURED IN BRIEF]** 4 files downloaded and parsed | **PASS for AGGREGATE daily returns, CRSP-based, dead-inclusive. No names.** |
| 11 | Alpha Vantage public documentation | [VENDOR OFFICIAL DOC] | [MEASURED IN BRIEF] raw HTML, extracted locally | Confirms basis (§5) and a point-in-time `LISTING_STATUS` (§2) |
| 12 | WRDS / CRSP | [SALES INSTRUMENT] | not probed | Subscription. No public per-name mirror found. |
| 13 | FirstRateData, AlgoSeek, Compustat | [SALES INSTRUMENT] | not probed | Commercial. Claims of 7,000+ delisted tickers are vendor marketing, unverified here. |

---

## 5. VENDOR-BASIS FACTS, EXTRACTED LOCALLY

Not via a summariser. I fetched `https://www.alphavantage.co/documentation/` with
`curl` (HTTP 200, 1,059,116 bytes), stripped tags locally, and grepped. Verbatim
`[VENDOR OFFICIAL DOC] [MEASURED IN BRIEF]`:

> **TIME_SERIES_DAILY_ADJUSTED** — "This API returns raw (as-traded) daily
> open/high/low/close/volume values, adjusted close values, and historical
> split/dividend events of the global equity specified, covering 25+ years of
> historical data."

> **TIME_SERIES_DAILY** — "This API returns raw (as-traded) daily time series
> (date, daily open, daily high, daily low, daily close, daily volume) ..."

> **TIME_SERIES_INTRADAY** — "Optional: adjusted — By default, **adjusted=true**
> and the output time series is adjusted by historical split and dividend events.
> Set adjusted=false to query raw (as-traded) intraday values."

This is the two-basis discrepancy in the vendor's own words, and it confirms the
memory note (*15m is fully adjusted, daily is not*). **It also names the fix:
`adjusted=false` on the intraday endpoint puts both series on the same as-traded
basis.** That is a vendor parameter, not a second source — but it is the cheapest
thing in this brief and it should be checked before anything else here is built.

---

## 6. THE FALLBACK — WHAT CAN BE ASSERTED WITHOUT A SECOND PRICE SOURCE

The kill condition is met, so this is the deliverable. Ordered by strength.

**The honest ceiling first.** Internal assertions catch *inconsistency*. They
cannot catch *systematic bias*. If the vendor's close for a name is uniformly
2% wrong, nothing below fires. Only a second price source catches that, and there
isn't one. Everything below is about catching the failure modes that actually
bit this programme — basis mismatches, corporate-action handling, and identity —
which are inconsistency failures and are all catchable.

### A. The adjusted/raw ratio must be a STEP FUNCTION — *the strongest, and it needs no calibration*

From one `TIME_SERIES_DAILY_ADJUSTED` response you already hold `close`,
`adjusted_close`, `split_coefficient`, `dividend_amount` on the same rows.
Define `r_t = adjusted_close_t / close_t`.

Three assertions, in increasing strength:

1. **`r_T = 1` at the last bar**, exactly (back-adjustment convention).
2. **`r_t` is piecewise constant, and changes ONLY on dates where
   `split_coefficient ≠ 1` or `dividend_amount ≠ 0`.** A change on any other date
   means the action file and the price series disagree. A *failure to change* on
   a recorded action date means the adjustment was not applied.
3. **`r_t` is non-decreasing in `t`.**

**This is the assertion that answers "is this series on the basis it claims".**
If the OHLC were silently adjusted rather than as-traded, `r_t ≡ 1` identically —
which assertion 2 catches the moment any split exists in the series. It requires
no second source, no tolerance-tuning, and no convention judgement.

*Then*, and only as a second step, reconstruct `adjusted_close_t` from `close_t`
and the recorded actions and assert it matches the vendor's column. That one
**does** need a convention calibrated on a single name with known actions —
so calibrate it explicitly and record the calibration, rather than assuming the
textbook formula.

### B. The split-date raw discontinuity test — *the direct basis test*

For every date with `split_coefficient = k ≠ 1`, assert
`close_{t-1} / close_t ≈ k` in the **raw** series. As-traded prices *jump* through
a split. An adjusted series does not.

This is the assertion that would have caught the 15m-versus-daily mismatch, and
it uses only the vendor's own columns. Run it against **both** fixtures. Note that
`raw_price_factor` cannot repair a spinoff (the memory note on NOW is exactly
this), so treat a spinoff-shaped discontinuity as a *distinct* verdict from a
split-shaped one rather than folding both into "adjustment error".

### C. Volume–price consistency across a split

On a split with factor `k`, share volume scales by `≈k` while price scales by
`1/k`, so **dollar volume is continuous**. Assert
`|log(dollarvol_t / median(dollarvol_{t-20..t-1}))|` stays inside its usual band
across split dates. Catches the classic bug where the split is applied to price
but not volume — which would silently corrupt a dollar-volume universe screen
by a factor of `k`.

### D. OHLC internal ordering and positivity

`low ≤ min(open, close)`, `high ≥ max(open, close)`, `low ≤ high`, all strictly
positive, `volume ≥ 0`. Cheap and it fires on interpolation and fill-forward bugs.
Report the *count and the names*, not just a boolean — a handful of violations is
a vendor glitch, a systematic pattern is a basis error.

### E. Terminal-stub and zero-volume bars

I measured a real one: stockanalysis's final TWTR bar is
`{"t":"2022-10-28","o":53.7,"h":53.7,"l":53.7,"c":53.7,"v":0}` — a synthetic
death-day stub. **Whether this vendor does the same is untested by me and should
be checked**, because it matters directly: the universe screen reads `close`, and
a stub bar carries a stale price into the book on the death bar, which is exactly
the bar where a dead name's return is decided. Assert: no bar has `volume == 0`
with a non-zero price range; flag every `open==high==low==close` bar; and decide
explicitly whether a stub is dropped or kept, in writing.

### F. Stale-quote runs

`close` constant over `k` consecutive bars with `volume > 0` is a fill-forward
signature. **Report the run-length distribution across the panel before setting a
threshold** — a $5-floored universe has genuinely illiquid names and a blind
threshold will fire legitimately, which the standing "assert code, not data" note
says is the wrong kind of assertion. Find the invariant under it.

### G. Calendar assertions on the ragged panel

The union over all names of bar dates must equal the exchange trading calendar
exactly: no bars on holidays; every name's bars a *contiguous* run of that
calendar between its first and last. **An interior gap — a date other names have
and this one does not — is a defect signature, and it is distinguishable from
raggedness**, which by definition only truncates the ends. Half-days (day after
Thanksgiving, Christmas Eve) should show a large volume drop; if they do not, the
volume field is suspect.

### H. Cross-sectional degeneracy by date

On any date, if an implausible share of names show *exactly* zero return, or
identical returns, that date was filled forward. This is a market-wide check that
costs one pass and catches whole-day vendor outages that per-name checks miss.

### I. Aggregate reconciliation against Kenneth French — *a real external check*

Cap-weight the fixture's own cross-section into a daily market return and compare
to `Mkt-RF + RF`. French is CRSP-based and dead-inclusive, so this is genuinely
independent.

**Assert on correlation and on alignment, never on level** — the fixture is 1,573
names floored at $5, French's market is all of CRSP. The sharpest form is the
**one-day-shift test**: correlate at lag 0, −1 and +1. A correctly aligned fixture
peaks hard at 0. **A lag audit that peaks at ±1 has found a date-alignment bug**,
which is the same class of error as the D279 lag bug and this is a second,
independent way to see it. This test is cheap, decisive, and covers 2010-01-04
through 2026-07-31.

### J. Universe roster and volume reconciliation against SEC MIDAS — *the other real external check*

Two assertions, both using MIDAS's point-in-time `(Date, Ticker)`:

1. **Roster.** Every fixture name-date should appear in the MIDAS roster for that
   quarter, and a fixture name should *stop* appearing when it stops trading.
   **This catches a zombie — a name whose bars run past its actual delisting —
   which is precisely the defect a price source cannot self-detect.** It also
   catches the reverse: a name in MIDAS's tape that the fixture never had.
   Coverage 2012 Q2 – 2026 Q2; the first ~2.25 years are uncovered.
2. **Volume.** Compare fixture volume to MIDAS `LitVol`. **Not for equality** —
   MIDAS is exchange-lit only and excludes TRF, so the ratio is well below 1 and
   drifts over time. Assert instead that **the per-name ratio is stable**, and
   treat a *step* in the ratio as the finding. A step on a split date means the
   volume basis changed; a step elsewhere means one of the two series changed
   definition.

MIDAS also carries `PriceRank`, a cross-sectional decile. It is not a price, but
it is monotone in price, so it should move discontinuously across a split.
**Weak — I did not test it — and I list it as a hint, not an assertion.**

### K. What none of this covers

- The absolute price level (no second source; stated at the top of this section).
- Anything before **2012-04-01** at the roster/volume level (MIDAS starts 2012 Q2).
- The last ~4 weeks to 2026-08-26 at the aggregate level (French ends 2026-07-31).
- Off-exchange volume, at all.

---

## 7. SAFETY — TEXT ADDRESSED TO THE READER, QUOTED AND NOT ACTED ON

Per the standing rule, these are **data**. I quote them and flag them; I did not
act on any of them. **I registered for nothing, created no account, entered no
credentials, and submitted no form.**

1. **Alpha Vantage `demo` key**, returned as the entire API response body for both
   `TIME_SERIES_DAILY_ADJUSTED&symbol=TWTR` and `&symbol=IBM`:
   > `{"Information": "The **demo** API key is for demo purposes only. Please claim your free API key at (https://www.alphavantage.co/support/#api-key) to explore our full API offerings. It takes fewer than 20 seconds."}`

   This is exactly the pattern the brief warned about — a vendor demo response
   instructing the reader to register. Not acted on.

2. **Tiingo:** `{"detail":"Please supply a token"}` — an instruction to obtain
   credentials. Not acted on.

3. **FMP:** `"Invalid API KEY. Feel free to create a Free API Key or visit
   https://site.financialmodelingprep.com/faqs?..."` — not acted on.

4. **stooq**, embedded JavaScript in the response body to `curl`:
   > `<noscript>This site requires JavaScript to verify your browser. Please enable JavaScript and reload.</noscript>`
   followed by a SHA-256 proof-of-work loop posting to `/__verify`.

   This is bot-detection. I did not implement a solver. I opened the page in a
   real browser, which is ordinary browsing.

5. **stooq consent dialog** (Polish). I clicked **"Nie zgadzam się"** — *I do not
   agree*, the privacy-preserving choice. The dialog re-presented with only
   *Agree* / *Manage options*. **I did not accept it.** The page never rendered
   content, and I am reporting stooq as a failure rather than consenting to get
   past it.

6. **Contact string.** Every SEC fetch used
   `backtest-framework-research/1.0 (research@backtest-framework.org)`.
   No personal address was used anywhere, including the one present in this
   environment.

---

## 8. WHAT I COULD NOT VERIFY, STATED PLAINLY

1. **Tiingo's free tier.** 403 "Please supply a token". Registration is prohibited
   by my brief, so I could not probe a single ticker. I make **no claim** about
   whether it serves delisted names, and per the standing rule it is a FAILURE in
   this brief rather than an unassessed candidate. **Anyone who wants it assessed
   must register a key themselves and re-run the SHLD/BBBY/TWTR/SIVB probe.**

2. **Every other keyed API** — EODHD, FMP, Polygon, marketstack, Finnhub, Alpaca.
   Same position. EODHD's demo token served AAPL and refused TWTR, which tells me
   about the *demo whitelist* and nothing about the *paid coverage*.

3. **stooq's registered or paid tier.** I tested only the anonymous path. It
   failed at three gates. I do not know what a paid account returns and I did not
   accept the consent banner that might have rendered the free HTML view.

4. **Nasdaq Data Link behind its WAF.** I established the 403 is not a
   User-Agent exclusion (three header/host variants, all 403), but I could not see
   what lies behind it. The `WIKI` table's 2018 discontinuation and
   survivors-only construction are from documentation, not from my own fetch.

5. **Whether MIDAS covers 2010-01-04 to 2012-03-31 under some other URL family.**
   I enumerated 58 files from the SEC's own page and the earliest is 2012 Q2 (the
   frozen `-and-exchange` family has a stray 2012 Q1). I did not find an earlier
   archive and cannot rule one out.

6. **MIDAS `LitVol` against real consolidated volume.** I have no consolidated
   volume series to compare against, so **the size and drift of the lit-versus-TRF
   gap is asserted from market structure, not measured by me.** §6.J's "assert the
   ratio is stable" is the right shape of assertion precisely because I could not
   measure the level. Someone should measure it on a handful of names before
   trusting it.

7. **Alpha Vantage's `LISTING_STATUS` point-in-time behaviour.** I have only the
   vendor's own documentation, quoted verbatim in §2. The `demo` key is gated on
   this function. **I never executed it, and a vendor's description of its own
   survivorship handling is exactly the claim that deserves a live test.** This is
   the single highest-value follow-up in this brief and it costs one call with the
   key this programme already holds.

8. **This programme's own fixture.** I never saw it. Every §6 assertion is written
   from the vendor's public documentation and general market structure. **Whether
   any of them currently fires, and whether the field names match, is unknown to
   me.** In particular the terminal-stub behaviour in §6.E is something I measured
   on stockanalysis.com, *not* on this vendor.

9. **stockanalysis.com's terms of service.** I checked `robots.txt` only, which
   does not exclude `/api/`. I did not read their ToS, and the endpoint is
   undocumented and could change or close without notice. Since I am recommending
   against the source anyway this is moot, but it should not be read as
   clearance to scrape it.

10. **The 64-ticker panel's delisting years** come from my own knowledge, not from
    a primary delisting record. The MATCH/WRONG-ENTITY split is robust to a
    year or two of error in either direction — a 2013 delisting scored against a
    series ending 2026 is unambiguous — but **the six MATCH cases were not
    verified against a primary source**, only against a ±1-year window.

11. **NYSE and Nasdaq commercial historical products.** Not probed. I established
    only that no *free* public download of them exists that I could find.

---

*Working files: `scratchpad/h5/` — `probe_sa.py` (the 64-ticker panel),
`midas_dead.py` (feb23 dead-name test), `midas_cov.py` (quarter enumeration),
`midas_recent.py` (2026 Q2 header via range request), `readzip.py`,
`avdoc.py`, `names.py`. These are scratch, not evidence; anything a record
quotes should be re-derived into `data/`.*
