# 04 — Commercial data APIs: what the FREE tier actually gives for CME futures

Research date: 2026-09-01. Lane: commercial vendor APIs with free tiers or free signup credits.
Requirement being tested: ES/NQ/RTY/YM (+ CL, GC, ZB, 6E), 15-minute or finer, 10+ years,
full ~23-hour Globex session, programmatic, continuous or stitchable.

Out of lane and not re-checked: Alpha Vantage (probed, serves no futures), Yahoo/yfinance
(daily only), brokers and IBKR (other agents).

---

## VERDICT FIRST

**One vendor solves this, and it solves it completely: Databento's $125 signup credit.**

The arithmetic below is the load-bearing part of this document. Short version:
**one symbol-year of GLBX OHLCV-1m costs about $0.51.** Ten to sixteen years of
1-minute bars, full Globex session, for all eight target symbols, comes to roughly
**$65 — about half the free credit.** The credit is not a teaser that runs out three
days in; it is roughly **246 symbol-years** of 1-minute futures history.

Everything else in this lane fails, and mostly fails hard:

- **No other vendor has a free tier that serves 10+ years of intraday CME futures.** Not one.
- **Massive (formerly Polygon.io)** is the only other one with *any* free futures minute
  bars — capped at **2 years**, 5 calls/min. Genuinely free, genuinely too shallow.
- **Twelve Data, Finnhub, EODHD, Tiingo, Marketstack, FMP, Intrinio** — none of them
  carry CME futures at all, on any tier. Their "commodities" endpoints are spot/CFD
  proxies, not exchange futures.
- **Norgate** has a 3-week free trial and 30+ years of continuous futures, but states
  flatly that it does **not** provide intraday data. End-of-day only. Disqualified on
  granularity, not on price.
- **Nasdaq Data Link / Quandl** — the legacy free CME tables are dead. `CHRIS` was
  confirmed deprecated by Nasdaq's own support in September 2024. `WIKI` died in 2018.
  Nothing free and futures-shaped survives there. Even when CHRIS was alive it was
  daily bars, so it never met this requirement anyway.
- **Barchart OnDemand** publishes no free tier and no public price list. Contact-sales only.

---

## 1. DATABENTO — the cost calculation

### 1.1 The pricing model, from primary sources

Databento bills **usage-based, per gigabyte, on the uncompressed size of the data in
binary (DBN) encoding.** Requesting CSV/JSON/Parquet output costs the same as DBN —
you are billed on the binary size regardless. Compression does not reduce the bill.

> "Every dataset or data feed is priced in $/GB. Every month, you pay only for the data
> that you've used. There is no monthly subscription fee."
> — [Usage-based pricing and credits FAQ](https://databento.com/docs/faqs/usage-pricing-and-data-credits)

The credit terms, verbatim from the same page:

> "All new users receive $125 in free credits upon signup. Credits can be used on
> historical data, or can be used towards the cost of the first month of a subscription
> plan. These credits are shared across your team and expire after 6 months. Each team
> is eligible for one set of credits."

Billing mechanics that matter for a bulk pull
([Metered pricing](https://databento.com/docs/api-reference-historical/basics/metered-pricing)):

- **Streaming** bills every outbound byte, and **duplicate streaming requests bill again.**
- **Batch download** bills **once**; you can then re-download from the Download Center
  free for 30 days. **Use batch for the historical backfill.** This is the single
  biggest way to waste the credit — re-running a streaming pull because your parser crashed.
- Metadata, symbology resolution, and `metadata.get_cost` are **free**. You can price
  every query exactly before you spend a cent.
- Rate limits: 100 concurrent connections, 100 timeseries req/s, 20 batch-submit req/min.
  Non-binding for this job.
- Databento recommends batch for anything over 5 GB. Our whole pull is ~2.3 GB.

### 1.2 Deriving the GLBX.MDP3 unit price

Databento does not publish the per-schema $/GB table publicly — it lives in the portal
behind login, and the marketing page only says CME historical is
**"from $0.50/GB"** ([databento.com/futures](https://databento.com/futures)), which is
the floor rate for the *largest* schema (MBO), not for aggregates.

But the API reference publishes worked examples with real numbers, and two of them are
the same query. That pins the rate exactly.

From [`Historical.metadata.get_billable_size`](https://databento.com/docs/api-reference-historical/metadata/metadata-list-unit-prices):

```python
size = client.metadata.get_billable_size(
    dataset="GLBX.MDP3", symbols=["ESM2"], schema="trades",
    start="2022-06-06T00:00:00", end="2022-06-10T12:10:00",
)
# EXAMPLE RESPONSE
99219648
```

From `Historical.metadata.get_cost`, **the identical query**:

```python
cost = client.metadata.get_cost(
    dataset="GLBX.MDP3", symbols=["ESM2"], schema="trades",
    start="2022-06-06T00:00:00", end="2022-06-10T12:10:00",
)
# EXAMPLE RESPONSE
2.587353944778
```

Divide:

```
99,219,648 bytes / 1,073,741,824 (2^30)  =  0.0924055 GiB
$2.587353944778 / 0.0924055 GiB          =  $28.0000 / GiB
```

It lands on **exactly $28.00 per binary gigabyte** — not a coincidence, and it also
tells us Databento's "GB" is 2^30, not 10^9. (In decimal GB the same figure is $26.08/GB.)

**So: GLBX.MDP3 `trades`, historical mode = $28.00/GiB.**

### 1.3 Is OHLCV-1m priced the same as trades?

The published unit-price table in the docs uses OPRA as its example, and it shows the
pricing *structure* clearly — small schemas carry a much higher $/GB rate, and
**`ohlcv-1s` and `ohlcv-1m` are priced identically to `trades`**:

| OPRA.PILLAR, mode `historical` | $/GB |
|---|---|
| cmbp-1 | 0.16 |
| cbbo-1s / cbbo-1m | 2.00 |
| tcbbo | 210.00 |
| **trades** | **280.00** |
| **ohlcv-1s** | **280.00** |
| **ohlcv-1m** | **280.00** |
| ohlcv-1h / ohlcv-1d | 600.00 |
| statistics | 11.00 |
| status / definition | 5.00 |

— [`metadata.list_unit_prices` example response](https://databento.com/docs/api-reference-historical/metadata/metadata-list-unit-prices)

Applying the same structure to GLBX: **`ohlcv-1m` on GLBX.MDP3 = $28.00/GiB**, the same
as `trades`. This is the one inferred number in the whole calculation. It is
**verifiable for free in about thirty seconds after signup**, before spending anything:

```python
client.metadata.list_unit_prices(dataset="GLBX.MDP3")
```

Below I run the numbers at $28/GiB and then stress them at 2×.

### 1.4 Record size

`OhlcvMsg` in DBN is **56 bytes**, fixed. Derived from the published field list
([Aggregate bars schema](https://databento.com/docs/schemas-and-data-formats/ohlcv)):
RecordHeader (length `uint8` + rtype `uint8` + publisher_id `uint16` + instrument_id
`uint32` + ts_event `uint64` = 16 B) + open/high/low/close (4 × `int64` = 32 B) +
volume (`uint64` = 8 B) = **56 B**.

Crucially, from the same page:

> "If no trade occurs within the interval, no record is printed."

So the bar count below is an **upper bound**. Overnight minutes with no ES print cost
nothing. RTY and YM overnight will come in materially under the estimate.

### 1.5 The arithmetic

Globex session for the equity index complex: Sunday 17:00 CT → Friday 16:00 CT with a
60-minute daily halt, i.e. **~23 h = 1,380 minutes per session**, ~252 sessions/year.
(The Sunday-evening block is already counted as part of Monday's session.)

```
bars per symbol-year      = 1,380 × 252            = 347,760
bytes per symbol-year     = 347,760 × 56 B         = 19,474,560 B
GiB per symbol-year       = 19,474,560 / 2^30      = 0.018137 GiB
COST PER SYMBOL-YEAR      = 0.018137 × $28.00      = $0.51
```

| Pull | GiB | Cost @ $28/GiB | Cost @ $56/GiB (2× stress) |
|---|---|---|---|
| 1 symbol, 1 year | 0.018 | **$0.51** | $1.02 |
| 1 symbol, 15 years | 0.272 | **$7.62** | $15.24 |
| **ES + NQ + RTY + YM, 15 years** | **1.09** | **$30.47** | **$60.94** |
| All 8 (+ CL, GC, ZB, 6E), 16 years | 2.32 | **$64.99** | $129.98 |
| ES + NQ + RTY + YM + CL + GC, 16 years | 1.74 | **$48.74** | $97.48 |

**What $125 buys: about 246 symbol-years of 1-minute Globex history.**

The four index futures over the full available history come to **$30**, leaving ~$95
of the credit unspent. All eight symbols over sixteen years is **$65**. Even at double
the assumed rate, the four-symbol pull still clears comfortably.

### 1.6 What the credit does NOT buy — the contrast that makes the point

| Schema, ES only | Approx. size/year | Cost/year @ GLBX rates | 15 years |
|---|---|---|---|
| `ohlcv-1h` | 0.32 MB | ~$0.02 (at the 1h rate) | ~$0.30 |
| **`ohlcv-1m`** | **19.5 MB** | **$0.51** | **$7.62** |
| `ohlcv-1s` | 1.17 GB | ~$30.5 | ~$457 |
| `trades` (tick) | ~5.5 GB | ~$145 | ~$2,180 |

The `trades` figure is measured, not modelled: the docs example gives 99.2 MB for ~4.5
days of ESM2 trades ⇒ ~22 MB/session ⇒ ~5.5 GB/year.

So the free credit is **~285× further** on 1-minute bars than on tick data for the same
symbol-period. Asking for 1-minute is what makes this work. Asking for 1-second blows
the credit on a single symbol.

### 1.7 Traps that would blow the credit

1. **Do not use `parent` symbology.** `ES.FUT` resolves to *every* listed ES outright
   plus every calendar spread — dozens of instruments printing bars simultaneously.
   That multiplies the bill by an order of magnitude or more for data you will throw away.
   Use **`stype_in="continuous"`** with `ES.c.0`, or enumerate raw contract months.
2. **Do not stream the backfill.** Streaming re-bills on every retry. Use
   `batch.submit_job`, which bills once and lets you re-download free for 30 days.
3. **Price it first.** `metadata.get_cost` is free and exact. Run it on the full
   request before submitting.
4. **The credit expires 6 months after signup**, one set per team, and Databento
   actively polices multi-account credit farming. Plan to do the pull in one campaign.

### 1.8 Continuous contracts

Databento has native continuous symbology, `[ROOT].[ROLL_RULE].[RANK]`, set via
`stype_in="continuous"`
([Symbology](https://databento.com/docs/standards-and-conventions/symbology)):

| Roll rule | Code | Behaviour |
|---|---|---|
| Calendar | `c` | offset from front month, rolls at expiry |
| Open interest | `n` | ranks expirations by previous close's open interest |
| Volume | `v` | ranks expirations by previous day's volume |

`ES.v.0` = highest-volume ES expiration; `ES.c.0` / `ES.c.1` = front and second month.
Note these are **raw stitched, not back-adjusted** — you still apply your own roll
adjustment. Continuous symbology is API-only; it is not selectable in the web portal.

### 1.9 Session coverage

GLBX.MDP3 is Databento's capture of the raw CME MDP 3.0 feed. There is no RTH filter
and no RTH-only variant — **you get the full electronic session, all ~23 hours,
overnight included**. One gotcha: `ohlcv-1d` is bucketed on **UTC dates**, not exchange
sessions, so if you want session-daily bars, build them yourself from `ohlcv-1m`.
That is a reason to pull 1-minute anyway.

### 1.10 History depth

ES coverage runs **"Since 2010-06-06 UTC"**
([ES catalog page](https://databento.com/catalog/cme/GLBX.MDP3/futures/ES)) — 16.2 years
as of today, comfortably past the 10-year target. NQ, YM, CL, GC, ZB, 6E should share
that start date. **RTY is the exception**: the E-mini Russell 2000 only moved to CME in
2017, so expect ~9 years there regardless of vendor. That is a market-structure fact,
not a Databento limitation.

Available schemas for ES, per the catalog page: MBO, MBP-1, MBP-10, TBBO, Trades,
BBO-1s, BBO-1m, **OHLCV-1s, OHLCV-1m**, OHLCV-1h, OHLCV-1d, Definition, Statistics, Status.

### 1.11 The subscription alternative, worth knowing

The [pricing page](https://databento.com/pricing) CME comparison shows the **Standard**
plan at **$199/month**, monthly billing, "No license fees", including
**"16+ years of L0 history"** where L0 = OHLCV-1s/1m/1h/1d + definitions + statistics +
status. And credits "can be used towards the cost of the first month of a subscription plan".

That means: **$199 − $125 = $74 net for one month**, during which 16 years of
**1-second** bars across all of CME/CBOT/NYMEX/COMEX is included rather than metered.
Usage-based, the same 1-second pull for eight symbols would be ~$3,900.

For our actual requirement (15-minute or finer), pure usage-based at ~$65 is cheaper and
needs no subscription. But if the framework ever wants 1-second bars, one month of
Standard is the route, by a factor of fifty. Caveat: I could not verify whether a
fair-use cap applies to bulk L0 downloads under a subscription.

### 1.12 Databento scorecard

| field | |
|---|---|
| name + URL | Databento — https://databento.com/datasets/GLBX.MDP3 |
| **free tier: futures yes/no** | **YES — $125 signup credit, spendable on GLBX.MDP3 historical** |
| granularity + history on the FREE tier | OHLCV-1s/1m/1h/1d, trades, MBP, MBO; ES history from 2010-06-06 (16+ yr). Credit buys ~246 symbol-years of OHLCV-1m |
| **full session or RTH only?** | **Full Globex session — raw MDP 3.0 capture, no RTH filter** |
| rate/volume limits | 100 concurrent conns; 100 timeseries req/s; 20 batch submits/min; no request size cap. Credit expires 6 months, one set per team |
| what $0 actually gets you | ES+NQ+RTY+YM, 15 yr, 1-minute, full session, continuous symbology, ~$30 of the $125. All 8 symbols × 16 yr ≈ $65. **The requirement is met with ~half the credit to spare** |
| verified how | primary — docs FAQ, metered-pricing docs, API reference worked examples, schema field list, symbology page, ES catalog page. **One inference**: OHLCV-1m unit price for GLBX assumed equal to `trades` ($28.00/GiB) by analogy to the published OPRA table |

---

## 2. MASSIVE (formerly Polygon.io) — the only other free futures bars

Polygon.io now redirects to **massive.com** (301 from `polygon.io/pricing` →
`massive.com/pricing`). Same product, rebranded. **They do serve futures now** —
CME, CBOT, NYMEX, COMEX — as a separate product line with its own plan ladder.

Futures plans ([massive.com/futures](https://massive.com/futures)):

| Plan | Price | History | Rate limit |
|---|---|---|---|
| **Futures Basic** | **$0** | **2 years** | **5 API calls/min** |
| Futures Starter | $29/mo | 2 years | unlimited, 10-min delayed |
| Futures Developer | $79/mo | 5 years | unlimited, + trades & quotes |
| Futures Advanced | $199/mo | 7+ years | unlimited, real-time |

The free tier's stated feature list is: "All Futures Tickers", "5 API Calls / Minute",
"2 Years Historical Data", "Historical Data", "Reference Data", **"Minute Aggregates"**.

So minute bars *are* on the free tier. The killer is **2 years**, and the ladder never
reaches 10 — even the $199/month top tier stops at "7+ years".

| field | |
|---|---|
| name + URL | Massive (ex-Polygon.io) — https://massive.com/futures |
| **free tier: futures yes/no** | **YES** — "Futures Basic", $0 |
| granularity + history on the FREE tier | Minute aggregates; **2 years only** |
| **full session or RTH only?** | Not stated. Sourced from CME feeds so presumably full session — **unverified** |
| rate/volume limits | 5 API calls/minute |
| what $0 actually gets you | ~2 years of 1-minute CME futures bars, painfully slowly (5 req/min). Useful as a recent-history cross-check; **fails 10+ years** |
| verified how | primary pricing page |

---

## 3. THE VENDORS THAT DO NOT CARRY CME FUTURES AT ALL

These are not "free tier too thin" results. These are "the product does not exist" results.

### Twelve Data — https://twelvedata.com/pricing

Free "Basic" plan: **8 requests/minute, 800/day**, covering "Real-time US equities and
ETFs", forex, and crypto — 3 markets. The
[API docs](https://twelvedata.com/docs) instrument-type list is:
ADR, Bond, Bond Fund, Closed-end Fund, Common Stock, Depositary Receipt, Digital
Currency, ETF, ETN, GDR, Limited Partnership, Mutual Fund, Physical Currency,
Preferred Stock, REIT, Right, Structured Product, Trust, Unit, Warrant.
**No futures type.** Their "commodities" coverage is spot/CFD-style, not CME contracts.
Intervals go down to 1min — for asset classes we don't need.

| field | |
|---|---|
| name + URL | Twelve Data — https://twelvedata.com/pricing |
| **free tier: futures yes/no** | **NO — no futures on any tier** |
| granularity + history on the FREE tier | 1min–1month intervals, equities/forex/crypto only |
| full session or RTH only? | n/a |
| rate/volume limits | 8 req/min, 800/day |
| what $0 actually gets you | nothing usable for CME futures |
| verified how | primary pricing page + primary API docs |

### Finnhub — https://finnhub.io/pricing

Two tiers only: Free and All-In-One at $3,500/month. The comparison table's asset
coverage is US/global equities, fundamentals, estimates, ETFs, mutual funds, bonds,
economic data, forex, crypto. **Futures appear nowhere.** Worse, the Free column for
"US Market Data → OHLC" and "Tick data" is **blank** — historical candles are not on
the free tier at all. Free tier is 60 API calls/minute.

| field | |
|---|---|
| name + URL | Finnhub — https://finnhub.io/pricing |
| **free tier: futures yes/no** | **NO — no futures on any tier; no OHLC candles on free** |
| granularity + history on the FREE tier | company news (1 yr), earnings calendar, websocket 50 symbols. No historical bars |
| full session or RTH only? | n/a |
| rate/volume limits | 60 API calls/minute |
| what $0 actually gets you | nothing usable |
| verified how | primary pricing page |

### EODHD — https://eodhd.com/pricing

Free plan: **20 API calls/day**, end-of-day only, stocks/ETFs/funds/forex/crypto.
Intraday requires the paid "EOD+Intraday" tier (£29.99/mo). **No CME futures listed on
any tier.**

| field | |
|---|---|
| name + URL | EODHD — https://eodhd.com/pricing |
| **free tier: futures yes/no** | **NO** |
| granularity + history on the FREE tier | daily EOD only; 30+ yr where available |
| full session or RTH only? | n/a (daily) |
| rate/volume limits | 20 calls/day |
| what $0 actually gets you | nothing usable for futures |
| verified how | primary pricing page |

### Tiingo — https://www.tiingo.com/about/pricing

Free tier: 50 req/hour, 1,000 req/day, 1 GB/month bandwidth, 500 unique symbols/month,
30+ years of history. Asset classes are equities/ETFs/mutual funds (plus crypto, forex,
news on other endpoints). **No futures.**

| field | |
|---|---|
| name + URL | Tiingo — https://www.tiingo.com/about/pricing |
| **free tier: futures yes/no** | **NO** |
| granularity + history on the FREE tier | equities only |
| full session or RTH only? | n/a |
| rate/volume limits | 50/hr, 1,000/day, 1 GB/mo, 500 symbols/mo |
| what $0 actually gets you | nothing usable for futures |
| verified how | primary pricing page |

### Marketstack — https://marketstack.com/product

Free plan: **100 requests/month**, end-of-day only, **1 year history**. Intraday
(1/5/10/15-min) starts at the Professional tier. Covers 70 stock exchanges, indices,
bonds, ETFs — **no futures**.

| field | |
|---|---|
| name + URL | marketstack — https://marketstack.com/product |
| **free tier: futures yes/no** | **NO** |
| granularity + history on the FREE tier | EOD, 1 year |
| full session or RTH only? | n/a |
| rate/volume limits | 100 requests/month |
| what $0 actually gets you | nothing usable |
| verified how | primary pricing page |

### Financial Modeling Prep — https://site.financialmodelingprep.com/pricing

Free "Basic": **250 calls/day**, **End-of-Day historical data only**, 5-year range,
500 MB/30-day bandwidth cap. **Intraday charts start at Premium ($59/mo); 1-minute
intraday is Ultimate-only ($149/mo).** FMP has a "Commodity Market Data" dataset but
those are spot/CFD-style symbols, not CME contracts with proper session and roll
semantics — and they are not on the free tier regardless, which is EOD-only.

| field | |
|---|---|
| name + URL | FMP — https://site.financialmodelingprep.com/pricing |
| **free tier: futures yes/no** | **NO** (EOD-only free tier; commodity symbols are CFD proxies) |
| granularity + history on the FREE tier | daily EOD, 5 years |
| full session or RTH only? | n/a |
| rate/volume limits | 250 calls/day, 500 MB per 30 days |
| what $0 actually gets you | nothing usable for CME futures |
| verified how | primary pricing page |

### Intrinio — https://intrinio.com/pricing

Equities, options, ETFs, indices, estimates, corporate data, mutual funds.
**No CME futures anywhere in the pricing documentation.** No free tier — the entry
plan is $150/month (Individual, personal use only); "free trial available" with no
published terms.

| field | |
|---|---|
| name + URL | Intrinio — https://intrinio.com/pricing |
| **free tier: futures yes/no** | **NO — no free tier, and no futures product** |
| granularity + history on the FREE tier | n/a |
| full session or RTH only? | n/a |
| rate/volume limits | n/a |
| what $0 actually gets you | nothing |
| verified how | primary pricing page |

---

## 4. NORGATE DATA — right coverage, wrong granularity

Norgate is the interesting near-miss: 30+ years of continuous futures contracts,
professionally maintained roll logic, and a **3-week free trial**. Subscription terms
are 6 or 12 months only (10% off annual); no monthly option; prices only visible via
their on-site calculator.

It is disqualified by one sentence on their own homepage:

> "We do not provide live quotes, delayed quotes, intra-day or 'tick' data."
> — [norgatedata.com](https://norgatedata.com/)

End-of-day only. The free trial would deliver 30 years of *daily* futures bars, which
is a fine thing to have and completely irrelevant to a 15-minute-or-finer requirement.

| field | |
|---|---|
| name + URL | Norgate Data — https://norgatedata.com/prices.php |
| **free tier: futures yes/no** | **Trial yes (3 weeks), futures yes — but EOD only** |
| granularity + history on the FREE tier | **daily bars only**; futures "Silver" package = 30+ years continuous contracts |
| **full session or RTH only?** | n/a — daily |
| rate/volume limits | not applicable (bulk local database, not an API) |
| what $0 actually gets you | 3 weeks of 30-year *daily* continuous futures. **Fails the granularity requirement outright** |
| verified how | primary — homepage statement + prices page |

---

## 5. NASDAQ DATA LINK / QUANDL — the legacy free CME tables are gone

This needed checking because every 2018–2021 tutorial still points at `CHRIS/CME_ES1`.

**`CHRIS` (Wiki Continuous Futures) is deprecated.** Nasdaq Data Link support, quoted
directly in a September 2024 issue on the *Python for Algorithmic Trading Cookbook*
repository:

> "Unfortunately, the CHRIS database has been deprecated and is no longer updated on
> Nasdaq Data Link."

— [PacktPublishing issue #5](https://github.com/PacktPublishing/Python-for-Algorithmic-Trading-Cookbook/issues/5)

They added that free feeds get pulled for "no longer meeting quality standards or due
to technical issues preventing data access", and **offered no replacement feed**.
`nasdaqdatalink.get('CHRIS/CME_ES1')` fails. The `WIKI` equities table died back in 2018.
`SRF`/Stevens Continuous Futures was always a paid product, not a free table.

I could not re-probe the API directly to enumerate what survives — `data.nasdaq.com` is
behind Incapsula bot protection and returns 403 to both `curl` and browser-context
`fetch`. But it does not matter for our purposes: **CHRIS was daily bars.** Even fully
alive it would fail the 15-minute requirement. There is no free intraday CME product
at Nasdaq Data Link and there never was.

| field | |
|---|---|
| name + URL | Nasdaq Data Link (ex-Quandl) — https://data.nasdaq.com |
| **free tier: futures yes/no** | **NO — CHRIS deprecated Sept 2024, no replacement** |
| granularity + history on the FREE tier | n/a (CHRIS was daily anyway) |
| full session or RTH only? | n/a |
| rate/volume limits | n/a |
| what $0 actually gets you | nothing. Every tutorial pointing here is stale |
| verified how | primary quote from Nasdaq support via secondary (GitHub issue). Direct API probe blocked by bot protection |

---

## 6. BARCHART ONDEMAND — no published free tier

[barchart.com/ondemand/api](https://www.barchart.com/ondemand/api) lists an extensive
API catalogue (getHistory, getQuote, etc.) with genuine futures coverage, but publishes
**no pricing and no free tier**. The page routes everything to "Contact Us":

> "Whether you're looking for a small, medium, large or enterprise solution, we'll
> create a custom package for you."

Contact is `solutions@barchart.com` / 312-566-9235. Historically Barchart ran a
time-limited trial key by request; I could not verify whether that still exists or what
it includes.

| field | |
|---|---|
| name + URL | Barchart OnDemand — https://www.barchart.com/ondemand/api |
| **free tier: futures yes/no** | **No published free tier** (trial possibly by request) |
| granularity + history on the FREE tier | unknown |
| full session or RTH only? | unknown |
| rate/volume limits | unknown |
| what $0 actually gets you | nothing without a sales conversation |
| verified how | primary page — confirms absence of published pricing; trial terms **unverified** |

---

## 7. RANKED SHORTLIST

1. **Databento, usage-based, $125 signup credit** — *the answer.* ES+NQ+RTY+YM,
   1-minute, full Globex session, 2010→present, native continuous symbology, ≈**$30**
   of a $125 credit. All eight symbols over sixteen years ≈ **$65**. Nothing else in
   this lane is within an order of magnitude of meeting the requirement.
2. **Databento Standard, one month at $199 (net $74 after credit)** — only if the
   framework later wants **1-second** bars, where it beats usage-based ~50×.
   Not needed for 15-minute-or-finer.
3. **Massive / Polygon.io "Futures Basic", $0** — 2 years of 1-minute bars at 5 req/min.
   Worth having as an **independent cross-check** against the Databento pull for the
   recent overlap window. Fails as a primary source.
4. **Norgate, 3-week trial** — 30+ years of daily continuous futures. Useful only if a
   daily-bar sanity reference is wanted. Explicitly no intraday.
5. *Everything else in this lane: no.*

---

## 8. WHAT I COULD NOT VERIFY

1. **The exact GLBX.MDP3 `ohlcv-1m` unit price.** I derived `trades` = **$28.00/GiB**
   exactly from two matching worked examples in Databento's API reference, and inferred
   `ohlcv-1m` = the same, because the published OPRA table prices `trades`, `ohlcv-1s`
   and `ohlcv-1m` identically. **Resolve this for free in 30 seconds after signup** with
   `client.metadata.list_unit_prices(dataset="GLBX.MDP3")`, before spending any credit.
   The conclusion survives a 2× error on this number.
2. **Whether those docs examples reflect current rates.** Databento changed usage rates
   on 2024-05-01. The examples may predate that. Same mitigation: `get_cost` before you buy.
3. **Whether CME exchange license fees apply on top of usage-based historical.** The
   pricing page lists "No license fees" as a *Standard-plan* feature, which raises the
   question for usage-based. Databento's usage-based card is "Historical data only" and
   license fees are discussed in the context of live data, so I believe historical
   internal-use is fee-free — **but I could not confirm it**; the licensing knowledge-base
   pages would not load. Check this on the signup questionnaire before committing.
4. **Whether a fair-use cap limits bulk L0 downloads under the $199 Standard plan.**
5. **Massive/Polygon free-tier futures details**: data delay on the $0 tier, and whether
   its aggregates cover the full electronic session or are RTH-filtered.
6. **Barchart OnDemand trial terms** — whether a free trial key still exists at all.
7. **Whether any free CME table survives at Nasdaq Data Link today.** CHRIS is
   confirmed dead; I could not enumerate the remaining catalogue because the site
   blocks programmatic access. Moot for our requirement, since nothing there was ever
   intraday.
8. **EODHD / FMP commodity endpoints** — I did not exhaustively confirm that their
   "commodities" symbols are CFD proxies rather than CME contracts. Both free tiers are
   EOD-only regardless, so it cannot change the verdict.
