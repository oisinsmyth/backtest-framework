# 03 — Every other broker / trading platform as a source of intraday CME futures history

Research date: 2026-09-01. Lane: all retail brokers and trading platforms **except IBKR**
(covered in `02-ibkr.md`) and except Alpha Vantage / Yahoo (already ruled out).
Requirement being tested: ES/NQ/RTY/YM (+ CL, GC, ZB, 6E), **15-minute or finer**, **10+ years**,
**full ~23-hour Globex session**, programmatic access, continuous or stitchable.

---

## VERDICT FIRST

**Nothing in this lane is genuinely free at the required depth. But two things clear the
requirement for a small, honest cash cost, and one of those is the best answer found anywhere
so far.**

1. **Sierra Chart Historical Data Service — $26/month, no funded account, no exchange fees,
   CME 1-minute back to June 2008 and tick back to 2011, full Globex session, exports to
   CSV and to a documented binary format you can read directly from Python.** This is the
   winner of this lane by a wide margin. One month's subscription ($26) is enough to pull the
   entire corpus and cancel.

2. **AMP Global MetaTrader 5 — $100 minimum account funding, continuous contract history back
   to September 1997 for ES**, free to the account holder, driven programmatically by the
   official `MetaTrader5` Python package. Cheaper in the long run, deeper on paper, but the
   *intraday* granularity of the pre-2010 portion is **unverified** and MT5 continuous contracts
   are broker-stitched rather than raw.

Everything else fails on one of four grounds, and it is worth naming them because they recur:

- **Depth** — Tradovate (2017), Rithmic (2011/2013 but expired contracts purged), NinjaTrader
  Continuum (365 days tick), TradeStation (3 years/request but the real ceiling is the account),
  TopstepX, T4.
- **Instrument** — Schwab/thinkorswim and Alpaca simply do not serve futures bars at all.
- **Cost gate** — Tradovate's $290/month CME sub-vendor licence is the single largest number in
  this document and it is unavoidable for API chart data.
- **ToS** — TradingView's terms prohibit non-display and automated use of its market data
  outright. That is decisive regardless of the bar limits, which are also far too small.

---

## THE TABLE

### 1. Sierra Chart — **RECOMMENDED**

| field | |
|---|---|
| name + URL | Sierra Chart Historical Data Service — https://www.sierrachart.com/index.php?page=doc/SierraChartHistoricalData.php |
| **genuinely free?** | **No — $26/month.** Service Package 3 ("Base Standard"). *No funded broker account. No exchange fees. No CME licence.* The 21-day free trial does **not** work for this: trial intraday charts are capped at 10 days of data. |
| instruments, granularity, history depth | CME/CBOT/NYMEX/COMEX (so all eight target symbols), plus Eurex, ICE, US equities. **CME tick-by-tick from 2011; CME 1-minute from June 2008.** US commodity futures daily back to 1970. Eurex tick from 2013, 1-minute from 2010. |
| **full session or RTH only?** | **Full session.** Sierra Chart's own docs describe the CME session as continuous except the 17:00–17:59:59.999 US Eastern maintenance break — i.e. the whole ~23h Globex day. |
| export/automation allowed? | **Yes, well supported.** `File >> Export Bar Data to Text File` (Date, Time, O/H/L/C, Volume, Number of Trades, Bid Volume, Ask Volume), plus intraday `.scid` ⇄ `.itxt` export/import. The `.scid` binary layout is publicly documented, so you can read the data files straight off disk with Python and skip the GUI entirely. There is also a `Write Bar and Study Data To File` study for automated dumps. **ToS restriction:** the licence agreement states data "is provided for personal use only and shall not be redistributed in any form to others." Private backtesting is fine; publishing the dataset is not. |
| verified how | **Primary source** (Sierra Chart docs + their own support board) for depth, package price, trial limits, export mechanism and the redistribution clause. |

**Why this wins.** It is the only source in the lane that gives 10+ years of sub-15-minute CME
data with *no broker relationship, no funded account, and no exchange market-data fees*, because
the historical service is delivered on a 10–15 minute delay and delayed data carries no CME
entitlement cost. It also has first-class continuous-contract support (`Chart Settings >> Symbol
>> Automatically Rollover Futures Symbol`, with back-adjustment now referenced to prior-day
settlement as of v2346) and configurable rollover rules, so the stitching problem is solved
in-platform rather than by you.

**Caveats to check before paying.** (a) There is a documented quota of **3000 historical *daily*
data requests per month** for futures/index symbols — the intraday path is separate but confirm
your download plan against it. (b) The service explicitly does **not** provide streaming
real-time or streaming delayed data; it is a historical download service. That is exactly what
we want, but do not expect it to double as a live feed.

---

### 2. AMP Global / MetaTrader 5 — **SECOND CHOICE, ONE UNVERIFIED FACT**

| field | |
|---|---|
| name + URL | AMP Global MT5 historical continuous contract data — https://faq.ampfutures.com/hc/en-us/articles/10802145313943 (403s to automated fetch; content recovered via search index) |
| **genuinely free?** | **Needs funding — $100 minimum** to open and activate a live AMP account. Data is then "included FREE for AMP Global Customers using MetaTrader 5." Placing trades additionally requires meeting day-trading margin, but *for data purposes the $100 is the gate*. A demo may not carry the deep history — AMP's wording points at live accounts. |
| instruments, granularity, history depth | Broker-built **continuous** contracts. Published start dates include **`@EP` E-mini S&P 500 — September 1997** (the ES Globex launch date), `@ENQ` E-mini Nasdaq 100 — Sept 1999, `@YM` Dow $5 Mini — April 2002, E-mini Russell 2000 — Sept 2007, `@DD` DAX — Sept 2000, `@DB` Euro Bund — Sept 2000, soybeans back to 1987. **Granularity of the deep history is not stated anywhere I could find.** MT5 builds every intraday timeframe from stored M1 records, so *if* M1 exists back to 1997 the 15-minute requirement is met trivially; if AMP only seeded daily bars pre-2010, the useful intraday window is much shorter. |
| **full session or RTH only?** | Full session (exchange-traded futures feed, not a CFD). |
| export/automation allowed? | **Yes — the best automation story in the lane.** The official `MetaTrader5` Python package exposes `copy_rates_range(symbol, TIMEFRAME_M1, start, end)` and `copy_ticks_range`, so this is a straight programmatic pull with no GUI scraping. Broker's own data, no third-party redistribution issue for private use. |
| verified how | **Secondary.** AMP's FAQ pages return 403 to automated fetch; the symbol list and 1997 start date were recovered from the search index and corroborated by an Optimus Futures announcement of the same dataset. The $100 minimum is from AMP's own FAQ. **Granularity is unverified — this is the one thing to test before committing.** |

**How to de-risk it cheaply:** install MT5, connect to AMP's *demo* server, and run
`copy_rates_range` on `@EP` for a 2001 date window at `TIMEFRAME_M15`. If bars come back, the
$100 live account buys a 28-year intraday corpus. If only daily comes back, drop this and take
Sierra Chart. Also note MT5 continuous contracts are **broker-stitched** — you inherit AMP's
rollover and adjustment convention rather than choosing your own, which matters if the framework
wants to control roll methodology.

---

### 3. Tradovate — **OUT (cost)**

| field | |
|---|---|
| name + URL | https://api.tradovate.com/ , https://support.tradovate.com/s/article/Available-Historical-Data-Tradovate |
| **genuinely free?** | **No, and expensively so.** Market data requires an approved and **funded** account; API access is **$25/month**; and API market data (which is how chart data is delivered) triggers the **CME sub-vendor requirement at $290/month payable to CME** — mandatory since 30 Sep 2022. Tradovate staff confirm the vendor licence "is required only for the md api access… which means websocket data." Chart/history requests go over that same market-data websocket. |
| instruments, granularity, history depth | CME products. **Tick and tick-based charts: 2 weeks. Minute charts: back to 1 January 2017. Daily: back to 1 January 2017.** So ~8.7 years of minute data at best. |
| **full session or RTH only?** | Full session. |
| export/automation allowed? | API-native, but requests are size-capped — a request for 200 four-hour bars returns ~120. Tradovate's own guidance is to take the oldest returned timestamp and chain requests backwards (they publish `example-api-faq/example-code/large-chart-requests`). Workable, but you are paying $315/month plus funding to do it. |
| verified how | **Primary** for the depth figures and the CME fee (Tradovate support article + Tradovate staff on their own forum). |

**Verdict:** fails the 10-year test *and* costs $315/month. This matters for the prop-firm angle
because Tradovate is what many prop firms front, but as a research data source it is the worst
value in the document. Note there is a real workaround — routing through an *authorised Tradovate
vendor* removes the personal API subscription and CME ILA — but that means a third party holds
the licence and you get their product, not a bulk history export.

---

### 4. NinjaTrader — **OUT (depth + laborious)**

| field | |
|---|---|
| name + URL | https://ninjatrader.com/pricing/ , export docs at `/support/helpguides/nt8/exporting.htm` |
| **genuinely free?** | Platform and sim account: free. **Real-time market data and Market Replay unlock only on a funded account — NinjaTrader states any deposit greater than $0 qualifies, with a $5.00 ACH/debit minimum.** New accounts also get a **14-day free trial of live streaming data**. Deeper history needs a paid feed: **Kinetick End-of-Day is free but is daily-only, explicitly no minute or tick**; Kinetick real-time CME/CBOT/COMEX/NYMEX is **$13.65 per exchange per month** (so ~$55/month for all four) plus the base service. |
| instruments, granularity, history depth | Depends entirely on the connected provider. **NinjaTrader's own Continuum servers guarantee only ~365 days of tick** for popular instruments. Forum reports put minute data back to ~2006 and daily to ~2009 *on some feeds*, but this is not a documented guarantee. |
| **full session or RTH only?** | Full session available. |
| export/automation allowed? | Export exists and is clean: Historical Data window → Tick / Minute / Day × Ask / Bid / Last → text file, **UTC, end-of-bar timestamps**. **The killer is acquisition, not export:** for futures you can only download the data belonging to the specific contract you name, from its rollover to its expiry — roughly a 3-month slice per contract. Ten years × 4 quarters × 8 symbols = ~320 manual per-contract downloads before you even start stitching. Market Replay data is free but **only goes back 90 days**. |
| verified how | **Primary** for pricing, export mechanics and the 90-day replay cap; **secondary** (support-forum staff posts) for the 365-day tick and per-contract download restriction. |

---

### 5. TradeStation — **OUT (needs an account; depth ceiling unclear but ~2–3y practical)**

| field | |
|---|---|
| name + URL | https://api.tradestation.com/docs/ |
| **genuinely free?** | Requires a TradeStation brokerage account. No published funding minimum for API access itself, but this is a brokerage relationship, not an open API. |
| instruments, granularity, history depth | Documented **request** limits are generous: max **57,600 bars per intraday request** regardless of interval; bars-back requests capped at **500,000 total minutes** (bars × interval); **a single date-range request may span at most 3 calendar years** of minute data. Credit-based rate limiting: 200 credits/minute, 1 credit = 100,000 one-minute bars or 365 calendar days. **What is not documented anywhere is the server-side archive depth for expired futures** — the request limits tell you what you may *ask* for, not what exists. |
| **full session or RTH only?** | Full session selectable. |
| export/automation allowed? | Yes, REST + streaming, well documented. |
| verified how | **Primary** for the limits (TradeStation's own rate-limiting docs). **Unverified** on actual futures archive depth — that is the number that decides it, and it is not published. |

Worth a probe *only* if you already have or want a TradeStation account. The 3-year-per-request
cap is a paging inconvenience, not a blocker; the unknown archive depth is the risk.

---

### 6. Charles Schwab / thinkorswim (ex-TDA API) — **OUT (no futures bars)**

| field | |
|---|---|
| name + URL | https://developer.schwab.com — Market Data Production API |
| **genuinely free?** | Free with a Schwab account, but irrelevant. |
| instruments, granularity, history depth | **`priceHistory` serves equities and ETFs only.** `schwab-py`, the most-used community client, documents flatly that it does not provide price history for options, futures, or any other instrument. Futures **quotes** exist and there is undocumented futures data on the CHART streaming channel, but **there is no historical futures bar endpoint** — futures requests return HTTP 400. |
| **full session or RTH only?** | N/A |
| export/automation allowed? | N/A |
| verified how | **Primary** (schwab-py docs) + **secondary** (multiple independent write-ups of the Schwab API's futures gaps). |

The thinkorswim *desktop* platform does chart futures with history, but offers no supported
bulk export and no API — not a pipeline.

---

### 7. Tastytrade — **OUT (depth unverified, likely ~1 year; needs account)**

| field | |
|---|---|
| name + URL | https://developer.tastytrade.com/streaming-market-data/ |
| **genuinely free?** | Free to open an account; futures *trading* requires meaningful net liq, but data access follows the account. |
| instruments, granularity, history depth | Market data is delivered by **dxFeed over DXLink**. Historical bars come as `Candle` time-series events with a `fromTime` parameter, and futures are supported. **The advertised pattern in tastytrade's own JS SDK is "5-minute candles starting from 1 year ago" — no documented multi-year depth.** dxFeed's underlying `Candlewebservice` can serve long ranges, but what tastytrade's *entitlement* exposes is not published. |
| **full session or RTH only?** | Full session. |
| export/automation allowed? | Yes — official JS and Python SDKs, plus community Rust clients. Streaming-subscription model rather than a REST history endpoint, which makes bulk backfill awkward. |
| verified how | **Secondary.** Tastytrade's docs page indexes "Candle Events" but the depth specifics were not retrievable. **Unverified on 10-year depth — assume no until proven.** |

Cheap to test if you already hold a tastytrade account: subscribe a `Candle` event for `/ESH15`
or an equivalent 2015 window and see whether anything comes back.

---

### 8. Alpaca — **OUT (no futures)**

| field | |
|---|---|
| name + URL | https://alpaca.markets/data |
| **genuinely free?** | Free tier exists — irrelevant. |
| instruments, granularity, history depth | **No CME futures.** Alpaca Derivatives LLC obtained FCM registration and NFA membership, but that was for **prediction markets / event contracts**, and Alpaca has stated it cannot list markets in-house without DCM status and would need an intermediary. Community answers confirm no real-time or historical E-mini data. |
| verified how | **Secondary** (Alpaca community forum + trade press on the FCM registration). |

Revisit in a year, not now.

---

### 9. Rithmic — **OUT (expired contracts purged; needs broker + funding)**

| field | |
|---|---|
| name + URL | https://yyy3.rithmic.com/?page_id=9 (R\|API+), community docs at https://async-rithmic.readthedocs.io |
| **genuinely free?** | **No.** Requires a broker relationship (AMP, Optimus, EdgeClear etc.), a funded account, a Rithmic data subscription, CME non-pro exchange fees, and a signed API agreement. **Legacy R\|API no longer serves historical data at all — you need R\|API+.** |
| instruments, granularity, history depth | Reported **~minute bars for ES from December 2011 (~14 years) and tick from February 2013**. That would clear the depth bar. **But: Rithmic does not allow historical download from expired contracts — once a contract expires, its data cannot be pulled.** That is fatal for building a stitched continuous series from raw contract legs. |
| **full session or RTH only?** | Full session. |
| export/automation allowed? | Programmatic, yes. But it is hostile: **a single replay request returns at most ~10,000 bars** (clients must paginate), there are **weekly download limits measured in gigabytes**, and community reports say **Rithmic may ban accounts that request large tick intervals**. |
| verified how | **Secondary** throughout (Optimus Futures community, `async_rithmic` docs, MultiCharts forum). Rithmic publishes essentially nothing about history availability. |

The ban risk plus the expired-contract purge makes this a bad bet even though the nominal depth
is adequate.

---

### 10. CQG — **OUT (paid per-dataset or partner-licensed)**

| field | |
|---|---|
| name + URL | https://www.cqg.com/products/cqg-apis , https://www.cqgdatafactory.com/ |
| **genuinely free?** | No. **CQG Data Factory sells historical data per dataset** (>20 years EOD, **>7 years intraday** incl. time & sales and intraday bar; some series back to the 1930s). CQG WebAPI historical access requires a broker/partner licence. |
| instruments, granularity, history depth | 60+ exchanges, tick / intraday bar / daily. 7 years intraday is *below* the 10-year target from the retail product. |
| export/automation allowed? | Yes, it is sold as data. |
| verified how | **Primary** (CQG's own product pages). |

If it comes to paying for data outright, this belongs in the same bucket as FirstRate/Databento
and should be compared on price per symbol-year — but that is a different lane from "broker APIs."

---

### 11. TradingView — **OUT ON ToS. Decisive.**

| field | |
|---|---|
| name + URL | https://www.tradingview.com/policies/ |
| **genuinely free?** | Free tier exists; **CSV export is paid-tier only**. |
| instruments, granularity, history depth | Intraday **bar caps by plan: Free 5,000 · Essential/Plus 10,000 · Premium 20,000 · Expert 25,000 · Ultimate 40,000**. At 15-minute bars on a ~23h Globex session (~92 bars/day), **Premium's 20,000 bars ≈ 217 trading days ≈ 10 months.** Even the top Ultimate tier at 40,000 bars is under 2 years. **Off by an order of magnitude.** |
| **full session or RTH only?** | Full session available on the chart — moot. |
| export/automation allowed? | **No.** TradingView's terms prohibit "any automated data collection methods, including scripts, APIs, screen scraping, data mining, robots, or other data gathering and extraction tools, regardless of their intended purposes," and separately prohibit using its market data "for any form of automated trading, algorithmic decision-making, or any other non-display purposes," naming price referencing and backtesting-adjacent machine-driven processes. Accounts are banned for detected violations. Manual CSV export of the visible bars is a product feature, but *using the exported data to drive a systematic strategy is a non-display use.* |
| verified how | **Primary** for the bar limits (TradingView support article) and **primary/secondary** for ToS wording (policies page + TradingView's own ban-reason support article citing paragraph 3). |

Two independent disqualifiers. Do not build on this, and do not use the many
`tradingview-scraper` packages floating around npm/PyPI — they are ToS violations with a
documented ban outcome.

---

### 12. MetaTrader 5 generally (non-AMP brokers) — **CONDITIONAL, see §2**

| field | |
|---|---|
| name + URL | https://www.mql5.com/en/docs/python_metatrader5 |
| **genuinely free?** | Terminal is free; data depth is **entirely broker-determined**. |
| instruments, granularity, history depth | MT5 stores **M1 as the base record and derives M5/M15/H1/H4 from it**, so any broker with deep M1 satisfies the granularity requirement automatically. But "the broker sets limits to how far back they will go," and most MT5 brokers offering *index CFDs* rather than exchange futures carry only a few years. **AMP Global is the standout because it publishes real exchange-traded futures continuous contracts with 1987–2007 start dates.** |
| **full session or RTH only?** | Full session for genuine exchange-traded futures symbols; CFD symbols follow the broker's own trading hours (close to 24h but *not* exchange data). |
| export/automation allowed? | Excellent — `MetaTrader5` Python package, `copy_rates_range` / `copy_ticks_range`. |
| verified how | **Primary** (MQL5 docs) for the mechanism; broker depth is per-broker and mostly **unverified**. |

**Important distinction:** an MT5 broker offering "US500" as a *CFD* is not giving you exchange
data — it is giving you their own synthetic price. AMP is different: those are real CME futures
symbols. Do not conflate the two.

---

### 13. CFD providers as an ES proxy — **WEAK. Use only as a sanity cross-check.**

| provider | free? | history | automation | verdict |
|---|---|---|---|---|
| **OANDA** (https://www.oanda.com/platforms/rest-api/) | **Genuinely free — unrestricted FxTrade Practice sandbox mirrors production endpoints, no funding** | Candles from 5-second to monthly; OANDA states pricing history back to 2005 (for FX — index CFD start dates are later and not published) | Excellent: v20 REST, `oandapyV20`, `InstrumentsCandlesFactory` pages long ranges automatically | **Best of the CFD group** purely on access. But `SPX500_USD` is OANDA's own synthetic price, not CME. Also note OANDA's *US* entity does not offer index CFDs at all — this only works on a non-US entity. |
| **IG** (https://labs.ig.com) | Demo account free (must reuse live-account email) | Intraday candles available | REST API, `trading-ig` Python client | **Killed by quota: 10,000 historical price data points per user per week.** 10 years of 15-min ES ≈ 230,000 bars = **23 weeks of continuous quota-farming for one symbol.** Unusable. |
| **Capital.com** (https://open-api.capital.com/) | Demo API server free (`demo-api-capital.backend-capital.com`) | `GET /api/v1/history/prices` with `MINUTE, MINUTE_5, MINUTE_15, MINUTE_30, HOUR, HOUR_4, DAY, WEEK` — **granularity is fine, depth is not documented and is believed short** | 10 req/sec general limit | Untested depth; CFD synthetic price. Low priority. |
| **Saxo Bank** (https://developer.saxobank.com) | Free simulation account | Real CME futures available (not just CFDs); `/chart/v1/charts` **capped at 1200 datapoints per request**, pageable via `Mode`/`Time` | REST, well documented | 1200/request means ~190 requests per symbol-decade at 15-min — tolerable. **But sim-account tokens expire every 24 hours and refresh is manual**, which makes a long unattended backfill painful. Archive depth unverified. |
| **Plus500** | — | — | — | **No retail API at all.** Their FIX/WebSocket APIs are institutional-only. Note: Plus500 owns *Futures Technologies* (ex-CTS **T4**), which does have a real futures API and a **free 2-week simulator with API access** — but T4's chart history depth is short and undocumented. Not worth the effort. |
| **CMC Markets** | — | — | — | No retail public API; institutional "Connect" only. Dead end. |

**The structural problem with all of them:** an index CFD is the broker's own price, derived from
but not identical to the CME future. Basis, financing adjustments, broker-specific spreads and
broker-specific session breaks all contaminate it. Fine for a "does the shape of my signal
survive" smoke test; **not fine as the price series a backtest reports P&L against**, and
certainly not for anything microstructural.

---

### 14. Prop-firm platform APIs — **OUT (depth + subscription + consolidation)**

| field | |
|---|---|
| name + URL | ProjectX Gateway API — https://gateway.docs.projectx.com/ ; TopstepX — https://help.topstep.com/en/articles/11187768-topstepx-api-access |
| **genuinely free?** | **No.** Requires an active Topstep account (evaluation or funded — itself a monthly subscription) **plus** ProjectX API Access at **$29/month** (≈$14.50 with a discount code), billed separately. |
| instruments, granularity, history depth | `POST /api/History/retrieveBars`. Unit types: **1=Second, 2=Minute, 3=Hour, 4=Day, 5=Week, 6=Month** with a custom unit multiplier, so 15-minute bars are constructible. **Max 20,000 bars per request; the endpoint is rate-limited and returns HTTP 429 on excess. Archive depth is not documented at all.** |
| **full session or RTH only?** | Full session. |
| export/automation allowed? | REST + SignalR websockets; `project-x-py` SDK exists. |
| verified how | **Primary** for the endpoint limits (ProjectX docs); **secondary** for pricing. |

Relevant context for the prop track: **ProjectX ended third-party prop-firm licensing with a
cutoff of 28 February 2026 and is now exclusive to Topstep.** So this API is no longer a general
prop-firm data route — it is a Topstep-only one, gated behind two stacked subscriptions, with
undocumented history depth. Not a research data source.

---

## RANKED: WHAT IS ACTUALLY WORTH TRYING

1. **Sierra Chart, $26 for one month.** Pull ES/NQ/RTY/YM/CL/GC/ZB/6E at 1-minute from June 2008
   (and tick from 2011 if wanted), full Globex session, export to CSV or read `.scid` directly
   from Python, cancel. This is the single highest expected-value action in the whole lane.
   *Do not use the free trial for this* — trial intraday is capped at 10 days.

2. **AMP Global MT5 demo probe, free, ~30 minutes.** Install MT5, connect AMP demo, call
   `copy_rates_range('@EP', TIMEFRAME_M15, 2005-01-01, 2005-02-01)`. If intraday bars come back
   from 2005, the $100 live-account route buys history back to September 1997 with a clean Python
   API — better than Sierra Chart on depth, worse on rollover control. If only daily comes back,
   discard.

3. **TradeStation probe — only if an account already exists.** The documented request limits are
   fine; the undocumented archive depth is the unknown. Cheap to answer if you're already inside.

4. **Tastytrade `Candle` probe — only if an account already exists.** Ask for a 2015 futures
   window over DXLink and see what returns. Low expected value; the 1-year figure in their own
   examples is not encouraging.

5. **OANDA practice account** as a *free, zero-friction* 24-hour index series for smoke-testing
   pipeline plumbing — explicitly not as a backtest price source.

**Do not pursue:** TradingView (ToS, and 20× short on depth), Tradovate ($315/month for 8 years),
Rithmic (expired-contract purge + ban risk), Schwab (no futures bars), Alpaca (no futures),
IG (10k points/week), Plus500, CMC, TopstepX/ProjectX.

---

## THE ToS PICTURE, SUMMARISED

- **TradingView** — prohibits automated extraction *and* non-display use. Two-strike
  disqualification, enforced by account bans. **Treat as closed.**
- **Sierra Chart** — permissive for our purpose: personal use, no redistribution. Backtesting
  privately is squarely inside that; publishing the dataset or a derived data product is not.
- **Rithmic** — no explicit prohibition found, but *operationally* hostile: gigabyte-per-week
  caps and reported account bans for aggressive tick requests. Behaves like a prohibition.
- **Tradovate / CME** — not a ToS problem but a *licensing* one: CME's sub-vendor rules
  (post-30 Sep 2022) put a $290/month floor under API market data. This is the same class of
  constraint that will resurface with any vendor delivering CME data over an API in real time.
  **Note the shape of the exemption: delayed data escapes it.** That is exactly why Sierra
  Chart's 10–15-minute-delayed historical service costs $26 and Tradovate's costs $315.
- **AMP / MT5, TradeStation, Tastytrade, Saxo, OANDA, Capital.com** — standard broker terms;
  data is for your own use, redistribution prohibited. No obstacle to private backtesting.

---

## HONEST GAPS

- **AMP MT5 intraday granularity pre-2010 is the single most important unverified fact in this
  document.** If it is M1 all the way back, it beats Sierra Chart. Test it before paying anyone.
- **TradeStation's actual futures archive depth** is not published anywhere I could find. The
  rate-limit docs describe permission, not inventory.
- **Tastytrade's dxFeed candle entitlement depth** is not published.
- AMP's FAQ pages return **403 to automated fetch**; their symbol list and start dates here come
  from the search index and a corroborating Optimus Futures post, not from a direct read of AMP's
  page. Confirm by eye before spending the $100.
- Kinetick and IQFeed were only skimmed — both are paid feeds in the $55–$150/month range and
  neither obviously beats Sierra Chart's $26, but a careful IQFeed depth check was not done.
- **Databento, FirstRate, Portara/PortaraCQG, Norgate** are paid third-party vendors, not brokers,
  and are out of this lane. If the conclusion becomes "we must pay," they belong in the same
  comparison as Sierra Chart and CQG Data Factory.

---

## SOURCES

Sierra Chart: [historical data service](https://www.sierrachart.com/index.php?page=doc%2FSierraChartHistoricalData.php) ·
[futures data inclusion](https://www.sierrachart.com/index.php?page=doc%2FFuturesData.php) ·
[packages & pricing](https://www.sierrachart.com/index.php?page=doc%2FPackages.php) ·
[free trial contents](https://www.sierrachart.com/index.php?page=doc/helpdetails59.php) ·
[import/export](https://www.sierrachart.com/index.php?page=doc%2FImportExport.html) ·
[continuous contract charts](https://www.sierrachart.com/index.php?page=doc%2FContinuousFuturesContractCharts.html) ·
[historical data cost thread](https://www.sierrachart.com/SupportBoard.php?ThreadID=85009)

AMP / MT5: [AMP MT5 exchange-traded futures history FAQ](https://faq.ampfutures.com/hc/en-us/articles/10802145313943-MetaTrader-5-MT5-Exchange-Traded-Futures-Historical-Continuous-Contract-Data) ·
[AMP minimum capital FAQ](https://faq.ampfutures.com/hc/en-us/articles/33479414576279-Is-there-a-minimum-capital-requirement-to-open-an-account) ·
[Optimus announcement of ES MT5 history](https://community.optimusfutures.com/t/e-mini-s-p-500-historical-data-for-mt5/1851) ·
[MQL5 copy_rates_range](https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesrange_py)

Tradovate: [API docs](https://api.tradovate.com/) ·
[available historical data](https://support.tradovate.com/s/article/Available-Historical-Data-Tradovate) ·
[CME sub-vendor $290/mo thread](https://community.tradovate.com/t/is-cme-sub-vendor-requirement-for-api-access-is-290-per-month/6215) ·
[chunking historical requests](https://community.tradovate.com/t/how-to-get-historical-data-for-more-than-one-month/3657)

NinjaTrader: [pricing](https://ninjatrader.com/pricing/) ·
[exporting historical data](https://ninjatrader.com/support/helpguides/nt8/exporting.htm) ·
[Market Replay 90-day limit](https://forum.ninjatrader.com/forum/ninjatrader-8/platform-technical-support-aa/1116925-market-replay-data-download) ·
[Continuum tick depth](https://forum.ninjatrader.com/forum/ninjatrader-8/platform-technical-support-aa/1217893-ninja-trader-continuum-historical-tick-data) ·
[Kinetick CME fees](https://kinetick.com/CME)

TradeStation: [historical bar limits](https://api.tradestation.com/docs/fundamentals/rate-limiting/historical-bar/) ·
[rate limiting](https://api.tradestation.com/docs/fundamentals/rate-limiting/)

Schwab: [schwab-py HTTP client docs](https://schwab-py.readthedocs.io/en/latest/client.html)

Tastytrade: [streaming market data](https://developer.tastytrade.com/streaming-market-data/) ·
[dxFeed candle requests](https://kb.dxfeed.com/en/data-services/aggregated-services/how-to-request-candles.html)

Alpaca: [futures data forum thread](https://forum.alpaca.markets/t/does-alpaca-offer-real-time-price-data-for-e-mini-s-p-500-futures/8520)

Rithmic: [async_rithmic history docs](https://async-rithmic.readthedocs.io/en/latest/historical_data.html) ·
[Optimus RAPI+ historical download thread](https://community.optimusfutures.com/t/rithmic-api-historical-data-download/4207) ·
[Rithmic programmatic interfaces](https://yyy3.rithmic.com/?page_id=9)

CQG: [Data Factory](https://www.cqgdatafactory.com/) · [client APIs](https://www.cqg.com/products/cqg-apis/client-apis)

TradingView: [intraday bar limits](https://www.tradingview.com/support/solutions/43000480679-historical-intraday-data-bars-and-limits-explained/) ·
[policies / terms](https://www.tradingview.com/policies/) ·
[suspicious activity bans](https://www.tradingview.com/support/solutions/43000674726-why-is-my-account-banned-due-to-suspicious-activity/)

CFD providers: [OANDA v20 REST](https://www.oanda.com/sg-en/platforms/rest-api/) ·
[oandapyV20 candles factory](https://oanda-api-v20.readthedocs.io/en/latest/contrib/factories/instrumentscandlesfactory.html) ·
[IG 10,000-point weekly limit](https://labs.ig.com/node/113) ·
[Capital.com public API](https://open-api.capital.com/) ·
[Saxo chart endpoint](https://developer.saxobank.com/openapi/referencedocs/chart/v3/charts) ·
[Plus500 T4 API](https://futures-technologies.plus500.com/api/)

Prop platforms: [ProjectX retrieveBars](https://gateway.docs.projectx.com/docs/api-reference/market-data/retrieve-bars/) ·
[TopstepX API access](https://help.topstep.com/en/articles/11187768-topstepx-api-access)
