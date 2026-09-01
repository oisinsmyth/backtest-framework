# 12 — Substitutes and lateral routes to a continuous 23-hour session

Date: 2026-09-01. Lane: lateral substitutes only. IBKR, brokers, commercial APIs, exchanges,
GitHub, Kaggle, Yahoo, crypto, prop platforms, aggregators and Reddit are other agents' lanes and
are not re-covered here except where a lateral finding touches them.

**The question this lane is trying to answer** is not "where is ES data". It is: *how does the
path of a held position behave across a continuous ~23-hour session, and specifically across the
20:00–04:00 ET window that our equity-ETF proxies (04:00–19:45 ET) cannot see, when it is scored
against a 4% trailing drawdown on open equity?* Everything below is ranked against that question,
not against fidelity to the ES contract.

Two candidates were verified empirically by downloading and decoding real data during this
research, not just by reading marketing pages. Those are marked **[verified by download]**.

---

## Headline findings

1. **Dukascopy's index CFDs are free, tick-level, no account required, and they demonstrably
   trade through the entire 20:00–04:00 ET window with bid/ask.** Decoded ticks confirm
   5,000–10,000 quote updates per hour overnight on the S&P 500 CFD. This is the single best
   substitute.
2. **HistData's SPXUSD 1-minute file is free, needs no account, goes back to Nov 2010, and has
   verified continuous 24h coverage** apart from a single ~1h45m late-afternoon break. It is the
   easiest thing to put into a backtest today.
3. **The literal missing window — Blue Ocean ATS prints on SPY/QQQ, 20:00–04:00 ET — is
   purchasable but not free.** The cheapest effectively-free route is Databento's $125 new-user
   credit against `OCEA.MEMOIR` at $0.40/GB usage pricing, with history from 2025-08-24 only.
4. **There is a dated free answer coming.** The SEC approved 23x5 operation of both SIPs on
   2026-07-07, go-live **2026-12-06**. From that date the consolidated tape itself carries the
   overnight session, which is the precondition for any free consolidated source ever having it.
   Today it does not exist at any price outside proprietary ATS feeds.

---

## Candidate assessments

### 1. Dukascopy index CFDs — free tick data, no account **[verified by download]**

| field | |
|---|---|
| substitute + URL | Dukascopy `USA500.IDX/USD`, `USATECH.IDX/USD`, `USA30.IDX/USD`, `DEU.IDX/EUR`, `JPN.IDX/JPY`, `VOL.IDX/USD` (VIX). Public feed: `https://datafeed.dukascopy.com/datafeed/{INSTRUMENT}/{YYYY}/{MM-1}/{DD}/{HH}h_ticks.bi5` — note the **zero-based month**. GUI: https://www.dukascopy.com/swiss/english/marketwatch/historical/ ; wrappers: https://www.dukascopy-node.app/ , https://github.com/Leo4815162342/dukascopy-node |
| **free?** | Yes. No account, no key, no registration. Plain HTTP GET. Rate-limited (503s under rapid sequential fetching — throttle to ~1 req/sec). |
| **session coverage — 20:00–04:00 ET?** | **Yes, fully.** Published hours for `USA500.IDX/USD`: Sun–Fri 22:00–20:15 GMT summer / 23:00–21:15 GMT winter, i.e. 18:00–16:15 ET, with the break in the late afternoon. Our window sits mid-session. Verified: on 2026-06-10 every hour 00:00–08:00 GMT (= 20:00 ET prior day → 04:00 ET) returned a populated tick file. |
| granularity, history depth | Raw tick (bid, ask, bid size, ask size, ms offset), aggregable to any bar. `usa500idxusd` catalogued from 1980 for daily; tick data practically starts 2012-01-16. `usatechidxusd` 1990, `usa30idxusd` 2013, `ussc2000idxusd` 2018, `volidxusd` (VIX) 2022-10-05, `dollaridxusd` 2017. |
| **how well does it proxy an ES hold?** | **Best available.** Dukascopy states the USA500.IDX price tracks the front-month S&P 500 futures contract, which is exactly the overnight reference we want — overnight there is no cash index, so the quote *is* futures-derived. It carries a genuine two-sided quote, so open-equity drawdown can be marked the way a prop firm marks it (adverse side of the spread) rather than on a mid or a last. Not the ES tape: no exchange prints, no volume, no basis or roll, and the quote is one dealer's synthetic. |
| verified how | Downloaded 8 hourly `.bi5` files for 2026-06-10, LZMA-decoded them (`FORMAT_ALONE`, 20-byte big-endian records `>iiiff`) and printed tick counts and quotes. 00 GMT: 10,271 ticks, ask 7371.958 / bid 7371.242 at open. 02 GMT: 7,337 ticks. 04 GMT: 5,793. 06 GMT: 4,993. 08 GMT: 8,191. RTH 14 GMT: 14,433. Overnight spread ≈ 0.7 index pts (~0.01%) vs ≈ 0.5 in RTH — i.e. liquidity thins overnight but does not vanish. `USATECH.IDX/USD` at 03 GMT: 91,878 compressed bytes, dense. `VOL.IDX/USD` at 02 GMT: 1,286 bytes — present but very thin overnight. |

The overnight/RTH tick-count ratio (≈0.35–0.7) and the spread widening are themselves usable
evidence about how much of the daily drawdown risk lives in the window we cannot currently see.

### 2. HistData SPXUSD 1-minute — free, deep, zero friction **[verified by download]**

| field | |
|---|---|
| substitute + URL | https://www.histdata.com/download-free-forex-data/?/ascii/1-minute-bar-quotes — index instruments `SPXUSD` (S&P 500), `NSXUSD` (Nasdaq 100), `GRXEUR` (DAX), `UKXGBP` (FTSE), `JPXJPY` (Nikkei), `UDXUSD` (dollar index), plus ~66 FX pairs. |
| **free?** | Yes, no account. Download is a two-step form: GET the month page, scrape the hidden `tk` token, POST `tk,date,datemonth,platform,timeframe,fxpair` to `https://www.histdata.com/get.php` with a matching `Referer`. Returns a ZIP. ($7/mo optional convenience tier for auto-updated Drive delivery; the raw data is free.) |
| **session coverage — 20:00–04:00 ET?** | **Yes, fully and continuously.** Verified on `DAT_ASCII_SPXUSD_M1_202606.csv`: 29,110 bars for June 2026, 1,295–1,320 bars in *every* hour bucket 00–15 and 18–23 (22 trading days × 60 = 1,320 = perfect), hour 16 partial (315 bars = first 15 min), hour 17 entirely absent. The only structural daily gap is 16:15→18:00 in file time; the rest of the 24h is unbroken. Timestamps are Eastern *Standard* Time with no DST adjustment — the ±1h summer offset does not touch our window, which is covered on either reading. |
| granularity, history depth | 1-minute OHLC, from **2010-11** to current month, one file per month. Also tick-level ("tick data quotes") for FX; index instruments are M1. |
| **how well does it proxy an ES hold?** | **Very good, with one real caveat: the volume column is always 0**, and there is no bid/ask — one OHLC series only, so you cannot mark open equity on the adverse side of the spread and you cannot use volume to filter thin-print artefacts. The series references the S&P 500 index level rather than the front future, so it has no basis or roll (a feature for path-shape work, a defect for P&L reproduction). The 15+ years of history is the deepest free continuous-session S&P series found in this lane, by a wide margin. |
| verified how | Full download and per-hour bar census of June 2026 (numbers above); the vendor's own `.txt` gap report in the ZIP lists the daily 16:14:5x→18:00:0x break plus a handful of sub-30-minute micro-gaps in the overnight hours (e.g. 1,185s on 2026-06-09 at 03:40 file time, 1,513s on 2026-06-17 at 05:32). Those micro-gaps are the honest cost of a broker-sourced series. |

### 3. Blue Ocean ATS via Databento — the literal missing window, near-free

| field | |
|---|---|
| substitute + URL | `OCEA.MEMOIR` — https://databento.com/datasets/OCEA.MEMOIR , announcement https://databento.com/blog/blue-ocean-ats-now-available |
| **free?** | **Effectively, at research scale.** Usage-based historical pricing from **$0.40/GB with no subscription required**, and new users get **$125 in credits usable against historical data from any dataset** (expire after 6 months, one set per team). OHLCV-1m or trades for a handful of symbols over one year of overnight sessions is a small number of MB — well inside the credit. Live streaming, by contrast, needs a paid plan. |
| **session coverage — 20:00–04:00 ET?** | **Exactly, and only, that window.** The Blue Ocean session is 20:00–04:00 ET, Sunday through Thursday. **There is no Friday-night session** — the week ends 04:00 ET Friday and resumes 20:00 ET Sunday — because prints clear through the NYSE TRF, which is shut on Saturdays. |
| granularity, history depth | Captured from the MEMOIR Depth feed: L1/L2/L3 order book, trades, OHLCV, statistics. **History begins 2025-08-24** — barely 12 months as of today. |
| **how well does it proxy an ES hold?** | It is not a proxy at all — it is the *actual* overnight prints on the *actual* instruments (SPY, QQQ and 12,000+ US equities) in the *actual* missing hours. That makes it the ground truth against which any CFD proxy should be validated. Its limits are severe though: one ATS, not a consolidated market, so overnight quotes are wide, depth is thin, and prints are sparse relative to RTH; and one year of history cannot support a distributional claim about tail drawdowns. Best used as a **calibration set for the CFD**, not as the backtest input. |
| verified how | Databento dataset page and pricing page fetched; Blue Ocean session mechanics cross-checked against Tiingo's overnight-API writeup and Blue Ocean's own FAQ/FIF deck. |

**Other Blue Ocean routes, none free:** Tiingo sells the same feed at **$9/mo on top of the $30/mo
Power plan (~$39/mo)** — 12,000+ symbols, top-of-book quotes, last trade, and overnight intraday
OHLC bars, REST + WebSocket (https://www.tiingo.com/blog/overnight-stock-data-api/). dxFeed
(partnership since Apr 2024), Bloomberg (real-time overnight order book since 2025) and ICE
Consolidated History also carry it, all at institutional prices. If the $125 Databento credit is
spent or refused, **Tiingo at $39/mo is the cheapest paid door to this exact window.**

### 4. Wait for the SIP — a dated, free, and certain answer

| field | |
|---|---|
| substitute + URL | CTA/CQ and UTP SIP 23x5 extension. Approved 2026-07-07; go-live **2026-12-06**. Background: https://sapinover.com/insights/sip-23x5-second-domino |
| **free?** | The SIP itself is not free, but *every* free consolidated data source downstream (and every cheap API) derives from it. Until it runs overnight, no free source can carry the window; after it does, they mechanically can. |
| **session coverage — 20:00–04:00 ET?** | Sunday 21:00 ET → Friday 20:00 ET with a daily 20:00–21:00 ET maintenance window. Our window is covered from 21:00 ET, **not** 20:00–21:00 ET. Six industry UAT weekends run 2026-10-02 → 2026-12-04. |
| granularity, history depth | Consolidated NBBO and last sale for all NMS securities. **Zero history** — it begins accumulating on go-live. |
| **how well does it proxy an ES hold?** | Not a proxy; it is the future of the real thing for equities. Strategically important and operationally useless for a decision that has to be made now: on 2026-12-06 it starts producing data, and a year of it exists in Dec 2027. |
| verified how | Fetched the SIP-23x5 writeup; corroborated by the Blue Ocean FAQ noting ATS activity is currently *absent* from the SIP and that the SIPs do not even operate during the 20:00–21:00 hour. |

### 5. 24X National Exchange — real, regulated, and not yet in our window

| field | |
|---|---|
| substitute + URL | https://equities.24exchange.com/ |
| **free?** | No. Proprietary feeds are priced at roughly $500/mo (Last Sale), $750–2,000/mo (Top), $1,500–2,500/mo (Depth) by distributor class. Delayed, end-of-day and historical subscribers are exempted from signing a data agreement but are not permitted to redistribute. |
| **session coverage — 20:00–04:00 ET?** | **Not today.** Live since 2025-10-15 but currently only 04:00–20:00 ET — precisely the coverage we already have. 23/5 operation (20:00 ET Sunday → 20:00 ET Friday, one-hour daily pause) is targeted for **H2 2026**, pending approvals. |
| granularity, history depth | Full exchange feeds, but history starts Oct 2025 and the overnight portion does not exist yet. |
| **how well does it proxy an ES hold?** | Irrelevant for now. Worth a calendar note: 24X going 23/5 plus the SIP going 23x5 in December is what will eventually make free overnight equity data ordinary. |
| verified how | Launch and hours from the Oct 2025 exchange announcements and The TRADE; fee schedule from the SEC/Federal Register rule filings on the 24X depth-of-book enterprise fee. |

### 6. OANDA v20 practice API — free with a demo account

| field | |
|---|---|
| substitute + URL | https://developer.oanda.com/rest-live-v20/ — instruments `SPX500_USD`, `NAS100_USD`, `US2000_USD`, `DE30_EUR`, `UK100_GBP`, `JP225_USD` |
| **free?** | Yes with a free practice account; API access is free, only trading incurs cost. Client library `oandapyV20`. |
| **session coverage — 20:00–04:00 ET?** | **Yes.** OANDA runs Sunday ~17:00 ET → Friday 17:00 ET with a short daily all-instrument halt at 16:59–17:05 ET. Our window is mid-session. |
| granularity, history depth | Candles from S5 (5-second) up, bid/ask/mid available. **5,000 candles per request** — deep history requires paginating (`InstrumentsCandlesFactory` handles it). S5 retention is shorter than M1; M1 goes back years. |
| **how well does it proxy an ES hold?** | Comparable in kind to Dukascopy, with two frictions: it needs an account, and **OANDA's index CFDs are not offered to US clients**, so a US-registered practice account may not expose `SPX500_USD` at all. Treat as a fallback behind Dukascopy, not ahead of it. |
| verified how | API docs and wrapper documentation; hours from OANDA's hours-of-operation material. Not download-verified (account required) — **flagged as unverified**. |

### 7. FX as a continuous-session laboratory — free, deep, wrong asset **[verified by download]**

| field | |
|---|---|
| substitute + URL | FXCM public candle server `https://candledata.fxcorporate.com/m1/{PAIR}/{YYYY}/{ISOWEEK}.csv.gz` (no account, still updating in 2026); HistData FX tick and M1 (same site as above); TrueFX (free, registration); Dukascopy FX ticks back to 2003. |
| **free?** | Yes, all of them. FXCM's is the lowest-friction: a plain gzipped CSV per instrument per ISO week. |
| **session coverage — 20:00–04:00 ET?** | **Yes — 24/5, genuinely unbroken.** Verified: `EURUSD` week 10 of 2026 returned 7,192 M1 rows against a 7,200 theoretical maximum (5 days × 1,440), i.e. 99.9% of every minute from Sunday evening to Friday close, with separate bid and ask OHLC. |
| granularity, history depth | FXCM: M1 bid/ask OHLC, weekly files, multi-year (2019 and 2026 both fetched successfully). HistData/Dukascopy FX: tick, back to 2003–2010. |
| **how well does it proxy an ES hold?** | **It does not proxy an ES hold at all** — and it should not be sold as one. EURUSD's intraday variance profile, its overnight/RTH split, its gap behaviour and its tail shape are all structurally different from a US equity index. What it *can* do is serve as a clean, artefact-free test bed for the **methodology**: building the running-maximum open-equity curve, applying a 4% trailing rule, and confirming the machinery behaves before pointing it at a noisier CFD series. Answering the equity-index question on EURUSD would be a category error. |
| verified how | Downloaded FXCM `EURUSD` 2019 and 2026 week-10 files and counted rows and timestamps (first `03/08/2026 21:03`, last `03/13/2026 20:59`). Confirmed the same server returns **404 for every index symbol tried** (`SPX500`, `NAS100`, `US30`, `GER30`, `JPN225`, `SPXUSD`, `SPX500USD`, `US500`, `USA500`, `GER40`, `XAUUSD`) — **FXCM's free server is FX-only**, contrary to a common assumption. |

### 8. International index futures and other index CFDs

DAX, FTSE, Nikkei: no free *futures* source surfaced in this lane (Eurex and OSE license their
historical data commercially). The free route to those markets is the same CFD route — Dukascopy
`DEU.IDX/EUR` and `JPN.IDX/JPY`, HistData `GRXEUR`, `UKXGBP`, `JPXJPY` — all on the same
22-hour CFD session as the US index CFDs, which means they add *different overlap*, not different
hours. Their genuine analytic value: the Nikkei and DAX CFDs are liquid during our blind window
(their own cash sessions run inside 20:00–04:00 ET), so they can independently corroborate that a
US index CFD quote overnight is tracking real global price discovery rather than a dealer's stale
mark. Dukascopy `VOL.IDX/USD` (VIX, tick from 2022-10) trades the same near-23h session but is
**very thin overnight** (1,286 compressed bytes in an hour vs 31,000+ for the S&P CFD), so it is
usable as a regime tag, not as a path.

**Stooq** — a free source that would otherwise be a candidate for index/futures intraday — is now
behind a JavaScript proof-of-work challenge on its download endpoints (`/q/d/l/`), so it is no
longer scriptable without a headless browser. Verified by direct request.

### 9. Index options implied paths — assessed and rejected

Cboe's Global Trading Hours session runs **20:15 ET → 09:25 ET** for SPX, XSP, VIX and RUT
options, i.e. it covers nearly the whole missing window with quoted, tradable instruments. The
lateral idea is sound in principle and fails on two counts.

First, **cost**: GTH option quotes are a Cboe DataShop product; no free sample or free intraday
time-and-sales for that session was found. Second, and fatally, **options price a distribution at
expiry, not a path**. A 4% trailing drawdown on open equity is a functional of the running maximum
of the price path — a path-dependent, barrier-type quantity. From European option prices you can
recover the risk-neutral terminal density (Breeden–Litzenberger) and, with a term structure, an
implied local-volatility surface, from which a *simulated* path distribution follows. That
simulation would be a model output, not a measurement, and it would be risk-neutral rather than
real-world — systematically overstating downside drift for an equity index. It cannot establish
what fraction of *realized* historical overnight sessions would have tripped the trailing rule,
which is the actual question. **Not worth pursuing.**

### 10. Micro futures (MES, MNQ) — no source treats them differently

Nothing found in this lane treats micros as a separate free tier. Micros are CME products on the
same Globex sessions under the same exchange data licensing as ES/NQ; every vendor prices them
inside the same GLBX dataset. There is no "micros are cheaper data" loophole. The only asymmetry
is instrument-level, not data-level: MES's smaller multiplier changes what a 4% trailing drawdown
means in contracts, not what the data costs.

### 11. Retail 24-hour equity venues (Robinhood 24 Hour Market, IBKR Overnight)

Noted for completeness, and deliberately not chased since brokers/prop platforms belong to other
lanes: both route to the same overnight liquidity pool. Robinhood's 24 Hour Market and IBKR's
overnight equity session are, in the relevant part, Blue Ocean (and IBKR's own IBEOS) — so their
data is the same data as item 3, with the same problem: it is not published free, and it is not on
the tape.

---

## Ranked list

Ranked by how well each answers *"how does a held position's path behave across the continuous
session, scored against a 4% trailing drawdown on open equity"* — not by fidelity to ES.

1. **Dukascopy `USA500.IDX/USD` ticks** — free, no account, tick-level with bid/ask, 2012→present,
   overnight coverage *verified by download*, and futures-referenced. Best answer available today.
2. **HistData `SPXUSD` M1** — free, no account, 2010-11→present, 24h coverage *verified by
   download*. Deepest history in the lane; costs you bid/ask and volume. **Use 1 and 2 together:**
   HistData for the long-horizon distribution, Dukascopy for spread-aware marking on a recent subset.
3. **Blue Ocean `OCEA.MEMOIR` via Databento's $125 credit** — the real prints in the real window on
   SPY/QQQ, effectively free at research scale, but only since 2025-08-24 and only one ATS. **Its
   right role is validating 1 and 2, not replacing them.**
4. **OANDA v20 practice API** — same class of instrument as 1, account- and region-gated, unverified.
5. **Dukascopy `USATECH.IDX/USD` / `DEU.IDX/EUR` / `JPN.IDX/JPY`** — corroboration that the overnight
   quote reflects real global price discovery; `NSXUSD`/`GRXEUR`/`JPXJPY` on HistData likewise.
6. **The SIP 23x5 go-live, 2026-12-06** — free-adjacent, certain, and useless until roughly Dec 2027
   once a year of history exists. Put it in the calendar; do not wait for it.
7. **Tiingo Blue Ocean add-on, ~$39/mo** — the cheapest paid door if the Databento credit falls through.
8. **FXCM / HistData / TrueFX FX** — genuinely continuous and genuinely free, but a different asset
   class. Methodology test bed only.
9. **Dukascopy `VOL.IDX/USD` (VIX)** — too thin overnight for a path; useful as a regime tag.
10. **24X National Exchange** — right idea, wrong year, paid data.
11. **Index options implied paths** — infeasible for a path-dependent barrier question, and not free.
12. **Micro futures as a distinct data route** — does not exist.

## What a substitute could establish, and what it could not

**Could establish.** With Dukascopy or HistData index-CFD data a proxy can honestly measure the
*shape* of the overnight problem: the overnight-to-RTH variance ratio; the distribution of maximum
adverse excursion inside 20:00–04:00 ET for a position entered at any given time; how often that
overnight MAE alone exceeds 4% of the position's high-water mark; what fraction of the full-day
peak-to-trough drawdown is contributed by the hours our ETF proxy cannot see; whether overnight
excursions are mean-reverting into the cash open or persist; and how sensitive a trailing-drawdown
rule is to the decision to hold across the session at all. It can also establish the *negative*
result cleanly — if overnight MAE almost never approaches 4%, the ETF-proxy gap is not
load-bearing and the whole line of inquiry can be closed on free data.

**Could not establish.** A CFD is one dealer's synthetic quote. It has no exchange prints, no
volume (HistData's column is literally zero), no order book, and no basis or roll. So it cannot
establish executable fills, realistic slippage, gap-through behaviour at the ES level, or the P&L
of an actual futures position — the CFD tracks an index, the contract does not. Critically, it
cannot establish **the prop firm's own mark**: MyFundedFutures computes trailing drawdown on its
platform's ES feed, and in exactly the tail cases that matter (holiday sessions, limit moves, roll
days, dealer spread blowouts) a CFD-derived MAE will diverge from that mark — and it will diverge
*upward*, since dealer widening manufactures adverse excursions that never occurred on the tape.
Any headline number from this data therefore carries a one-sided error and should be reported as a
**conservative upper bound on breach frequency**, never as a point estimate. The FX substitutes
establish nothing whatsoever about the SPX overnight path; they only de-risk the code. And no
substitute can tell you what the *consolidated* overnight equity market did, because before
2026-12-06 no such consolidated record exists.

**Recommended validation before trusting any of it.** Both proxies overlap our existing ETF window
(04:00–19:45 ET) completely. Re-run the same MAE and trailing-drawdown measurement on the CFD and
on the ETF proxy over that shared window; if the CFD reproduces the ETF's intraday MAE
distribution, its extension into 20:00–04:00 ET is credible, and the size of the residual in the
overlap gives you a calibrated error bar to attach to the overnight number. Then spend the
Databento credit on twelve months of Blue Ocean SPY 1-minute bars and check the CFD's overnight
MAE against the real overnight prints on the one year where both exist. That is a three-source
triangulation on free data, and it is the strongest thing this lane can offer.

---

## Reproduction notes

Dukascopy tick fetch (month is **zero-based**; throttle to ~1 request/second or you get 503s):

```
https://datafeed.dukascopy.com/datafeed/USA500IDXUSD/2026/05/10/02h_ticks.bi5   # = 2026-06-10 02:00 GMT
```

Decode: `lzma.LZMADecompressor(format=lzma.FORMAT_ALONE).decompress(raw)`, then 20-byte records
`struct.unpack('>iiiff', ...)` = (ms offset within the hour, ask×1000, bid×1000, ask vol, bid vol).

HistData is a token-gated form POST, not a direct link: GET
`https://www.histdata.com/download-free-forex-data/?/ascii/1-minute-bar-quotes/spxusd/2026/6`,
scrape the hidden `tk` value, then POST `tk,date,datemonth,platform=ASCII,timeframe=M1,fxpair=SPXUSD`
to `https://www.histdata.com/get.php` with a matching `Referer` header. Returns a ZIP containing the
CSV (`YYYYMMDD HHMMSS;O;H;L;C;0`, semicolon-delimited) and a vendor gap report.

FXCM FX (no account): `https://candledata.fxcorporate.com/m1/EURUSD/2026/10.csv.gz` — ISO week
number, gzipped CSV with separate bid and ask OHLC. FX symbols only; all index symbols 404.
