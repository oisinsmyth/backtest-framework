# 09 — Crypto derivatives as a session-structure proxy for ES

**Lane:** free intraday data for a continuously-traded instrument, to study path behaviour of an
open position across a ~23-hour session against a 4% trailing drawdown on open equity.

**Date of research:** 2026-09-01. All endpoint claims below were verified by direct HTTP probe
on that date unless marked otherwise.

**Prior art assumed:** Alpha Vantage has no futures (`docs/research/futures-data/alpha_vantage_api.md`).
Brokers, commercial APIs, exchanges, GitHub, Kaggle, Yahoo and Reddit are other agents' lanes.

---

## BOTTOM LINE UP FRONT

Three findings, in descending order of importance.

1. **CME Bitcoin futures (BTC / MBT) are a real Globex contract and, for the period
   2017-12 to 2026-05-28, carried the *exact* ES session: Sunday open, Friday close, daily
   maintenance break, no weekend trading.** I verified the weekend closure empirically — 2117
   daily bars from 2018-01-02 to 2026-05-28, **zero Saturday or Sunday bars**. This is the
   genuine bridge asked for in Part 3. It is not free-free, but it is effectively free:
   Databento carries it from 2017-11-19 with an `ohlcv-1m` schema and gives $125 of signup
   credit, against an estimated cost of **well under $1** for the entire front-month 1-minute
   history.

2. **That window closed on 2026-05-30.** CME took crypto futures to 24/7 on Globex, leaving only
   a 60-minute maintenance stop Sunday 22:00–23:00 UTC. I confirmed this empirically: hourly
   `BTC=F` bars for the last month show **all 24 UTC hours and all 7 weekdays**. So CME BTC is a
   session-structure proxy for ES *historically* and *no longer prospectively*. Pull the
   pre-2026-05-30 history and treat 2026-06 onward as a different instrument.

3. **Crypto perpetuals (Binance/Bybit/OKX/BitMEX/Deribit) are free, deep, tick-level, and
   structurally wrong for this question.** They have no session, so they cannot answer a question
   *about* sessions. Their real use is as a **null model** — the control arm that shows what a
   trailing-drawdown floor does when there is no session and no gap — not as an ES stand-in.
   See Part 2, which is the load-bearing section of this document.

---

## PART 1 — THE VENUES

### Summary table

| venue + URL | instrument type | bulk download? | granularity, earliest date | rate limits | verified how |
|---|---|---|---|---|---|
| **Binance Futures**<br>`data.binance.vision` | USD-M perp + dated quarterlies; COIN-M perp + dated quarterlies | **Yes** — daily + monthly ZIP, public S3, no key | klines `1s`–`1mo`, plus aggTrades/trades tick. UM `BTCUSDT` 1m from **2020-01**; REST reaches back to **2019-09-08**. COIN-M `BTCUSD_PERP` 1m from **2020-08** | S3 bulk: none. REST `fapi` 2400 weight/min per IP; `x-mbx-used-weight-1m` header returned | S3 `ListBucket` + `fapi/v1/klines` probe |
| **Bybit**<br>`public.bybit.com` | linear USDT perp, inverse perp | **Yes** — daily `.csv.gz` per symbol, directory-listed | tick trades. `BTCUSDT` from **2020-03-25**, `BTCUSD` (inverse) from **2019-10-01**, current to **2026-08-31** | bulk: none. API 600 req / 5 s per IP *(doc-sourced)* | HTTP listing of `/trading/BTCUSDT/`, `/trading/BTCUSD/` |
| **OKX**<br>`okx.com/cdn/okex/traderecords/` | USDT/USD swaps + dated quarterlies | **Yes** — daily ZIP, undocumented but open CDN | tick trades + aggtrades. `BTC-USDT-SWAP` **404 at 2021-06-01, 200 at 2021-10-01** → starts Q3/Q4 2021. No monthly rollup (404) | bulk: none. REST 250 req/s global cap *(doc-sourced)* | HTTP HEAD on daily/quarterly ZIPs |
| **BitMEX**<br>`s3-eu-west-1.amazonaws.com/public.bitmex.com/` | inverse perp (XBTUSD), dated futures | **Yes** — one daily `.csv.gz` per day, all symbols in one file | **tick trades AND top-of-book quotes**, both from **2014-11-22**, current to **2026-08-31** | S3, no auth, no documented cap. REST API 300 req / 5 min *(doc-sourced)* | S3 `ListBucket` + HEAD + gunzip of `20200101.csv.gz` |
| **Deribit**<br>`deribit.com/api/v2/public/` | inverse perp, dated futures, options | **No** — REST/WS only, paginated | `get_tradingview_chart_data` 1m. `BTC-PERPETUAL` **no_data 2018-08-01, ok 2018-09-01**. `get_funding_rate_history` returns `interest_8h` + `interest_1h` | ~20 req/s public per IP *(doc-sourced)* | live API calls at four timestamps |
| **CME BTC / MBT via Databento**<br>`databento.com` GLBX.MDP3 | **CME-listed, Globex, real expiry/roll/settlement** | Batch download API (paid, credit-covered) | `ohlcv-1s/1m/1h/1d`, `mbo`, `mbp-1/10`, `trades`, `tbbo`, `definition`, `statistics`, `status`. **Since 2017-11-19 UTC** | usage-priced $/GB; $125 signup credit, 6-month validity | catalog page fetch |
| **CME BTC via FirstRateData**<br>`firstratedata.com/i/futures/BTC` | CME-listed | Yes — CSV ZIP | 1m/5m/30m/1h/1d, **2017-12-17 → present**; unadjusted + abs/ratio back-adjusted continuous | n/a | product page fetch |
| **CME DataMine / Portara** | CME-listed | Yes | tick / 1m | subscription only; Portara free tier withdrawn | n/a | search + vendor pages |

### Per-venue notes that matter

**Binance — the best free bulk source overall.**
The bucket is browsable as a plain S3 endpoint:
`https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix=data/futures/um/monthly/`
Verified subdirectories under both `futures/um` and `futures/cm`:

```
aggTrades/  bookTicker/  fundingRate/  indexPriceKlines/
klines/  markPriceKlines/  premiumIndexKlines/  trades/
```

Two things here are more useful than they first look:

- **`fundingRate/` is present as bulk, from 2020-01.** Funding is the perpetual's substitute for
  carry/roll. If you want to model an *overnight hold cost* — which is exactly what a multi-day
  ES position pays through roll — funding history is the analogue, and it is free and complete.
- **Dated quarterlies exist and are downloadable.** Verified: `BTCUSDT_210326` through
  `BTCUSDT_250926` (UM), and `BTCUSD_200925` onward (COIN-M). **These expire, settle, and roll.**
  They remove one of the three structural objections to crypto as a proxy. They are far thinner
  than the perp, but they are a real quarterly ladder with a real roll calendar.

Every ZIP has a sibling `.CHECKSUM`. Note the REST/bulk asymmetry: `fapi/v1/klines` returned a
bar at `1567965420000` (2019-09-08), four months earlier than the earliest monthly ZIP.

**BitMEX — deepest history, but read the liquidity warning.**
The `public.bitmex.com` S3 bucket holds `data/trade/`, `data/quote/` and `data/porl/`, all from
2014-11-22 and current through 2026-08-31. Both trades and quotes are tick-level with
microsecond timestamps. Schema confirmed by decompressing a real file:

```
timestamp,symbol,side,size,price,tickDirection,trdMatchID,grossValue,homeNotional,foreignNotional
2020-01-01D00:00:13.469612000,ADAH20,Sell,10416,4.61e-06,MinusTick,...
```

Two gotchas:

- **The documented `https://public.bitmex.com/data/trade/YYYYMMDD.csv.gz` path returned 404.**
  The working form is `https://s3-eu-west-1.amazonaws.com/public.bitmex.com/data/trade/YYYYMMDD.csv.gz`.
- **BitMEX liquidity has collapsed.** The 2020-01-01 all-symbol trade file is **13.26 MB**
  gzipped; 2026-08-01 is **125 KB** — roughly a hundredfold drop. The 2016–2021 XBTUSD history
  is genuinely excellent and famously so; the recent tape is thin and its microstructure is not
  representative of a liquid market. Use BitMEX for the old deep history, not for recent years.

**Deribit — skip for this purpose.** No bulk download, so you would be paginating a REST API for
millions of minutes. Its depth is in options, not in the linear perp. The one thing it does well
that others do not is expose `interest_1h` alongside `interest_8h` in funding history, which is a
finer-grained carry series. Not worth the ingestion cost here.

**OKX — usable, undocumented, shallowest.** The CDN works and covers dated quarterly futures
(`BTC-USD-250926` returned 200), but history only reaches Q3/Q4 2021 and there is no monthly
rollup, so it is one HTTP request per instrument per day. Third choice behind Binance and Bybit.

---

## PART 2 — THE HONEST ASSESSMENT

This is the part that matters. The source list above is easy; this is where the lane earns or
loses its keep.

### What is actually being asked

The framework's question is: **when a position is held across a long continuous session, how does
its open equity path behave, and how often does that path touch a 4% trailing floor before the
trade's terminal P&L is realised?** This is a question about the *shape of the path*, not the
*level of the return*. The distinction is what makes a proxy conceivable at all.

### The three structural breaks — stated plainly

**1. No expiry, no roll, no settlement.**
A perpetual has no terminal date. It is held together by a funding mechanism that pins it to spot.
ES has a quarterly roll, a settlement, and a well-defined carry embedded in the basis. Any study
of *how a position behaves as expiry approaches* — pin risk, roll slippage, term-structure drift,
the settlement print — is simply unaskable on a perpetual. **Mitigation: Binance's dated
quarterlies (`BTCUSDT_YYMMDD`, `BTCUSD_YYMMDD`) do have all three.** If roll matters to the
study, use those, not the perp. If it does not, the perp is fine on this axis.

**2. Volatility is 3–5x higher.**
This is the objection that is most often stated and least often stated correctly. It does **not**
merely mean "the numbers will be bigger." It means:

- Any drawdown statistic measured in **absolute percent** — "P(hit 4% trailing floor)" — transfers
  as pure garbage. A 4% trailing floor on BTC is a scalp-tight stop; on ES it is a wide one.
  Transporting that number is a category error, not a calibration error.
- Any statistic in **vol-normalised units** — "P(hit a floor set at k sigma of the holding-period
  distribution)" — has a chance of transferring, but only if the *shape* of the return
  distribution matches, and crypto's kurtosis and jump intensity are materially higher than ES's.
  So even the normalised number is biased, and biased in a known direction: **crypto will
  overstate floor-hit frequency.**
- Practical consequence: any result you carry across is an **upper bound**, not an estimate.

**3. Different participant mix, different intraday seasonality.**
ES has a US-centric volume profile with a cash-open spike, a lunch lull, and a close ramp — all of
which are artefacts of the *session*. Crypto has a flatter, Asia-weighted profile with no
structural open or close. Intraday-seasonality-dependent results do not transfer at all.

### The thing crypto genuinely gives you

Set against those three, there is one real capability, and it is the reason this lane exists:

**A continuously-traded instrument is a clean control for isolating what the session contributes.**

Consider the trailing-floor question. On ES, an overnight adverse excursion has two possible
causes tangled together: (a) the price drifted against you during continuous overnight trade, and
(b) the price *gapped* across a session break where you could not act. Equity-ETF proxies covering
16 of 23 hours make this worse, not better — they add a fake 8-hour gap that ES does not have.

On a 24/7 instrument, **(b) is identically zero**. Every adverse excursion is (a). That gives you
a measurement you cannot get any other way: the pure continuous-path contribution to
trailing-drawdown risk, with the gap term structurally removed.

Then, separately, **CME BTC pre-2026-05-30 is the same asset with the ES session imposed on it.**
Same underlying, same volatility regime, same participants at the margin — but with a Friday
close, a weekend, and a daily maintenance break. **Differencing the two isolates the session
effect on a single asset, controlling for volatility.** That is a genuinely strong research design,
and it is the strongest argument this lane can make. It is available free-to-cheap today, and the
CME leg's clean period ends 2026-05-28.

### What such a proxy CAN establish

- **That the mechanics of a trailing floor on open equity are implemented correctly.** A 24/7
  tick series with no gaps and no session boundaries is the ideal test harness for the
  drawdown-accounting code itself. Ambiguities — does the floor ratchet on marks or on closes,
  what happens at a session boundary, how is open equity marked when the market is shut — are all
  either eliminated or made trivially checkable. **This alone justifies pulling the data.**
- **The qualitative shape of drawdown accumulation with holding period.** Whether maximum adverse
  excursion grows roughly as sqrt(t), sub-sqrt, or super-sqrt over a multi-hour to multi-day hold
  is a property of the price process's dependence structure, and that shape is far more portable
  across assets than any level is.
- **The relative ordering of hold horizons.** That a 3-day hold has materially more floor-touch
  risk than a 1-day hold, and roughly by what multiple, is a rank-order result that survives a
  volatility change even when the absolute numbers do not.
- **An upper bound on floor-hit probability at matched vol-normalised floor width.** Crypto's
  fatter tails make it strictly harsher; if a rule survives on crypto it will likely survive on ES.
- **The size of the gap term, by subtraction** — but only against the CME BTC leg, not against ES
  directly.

### What such a proxy CANNOT establish

- **Any absolute number that will be quoted in the strategy's risk budget.** "This book has a
  6.2% chance of breaching the 4% trailing drawdown per 30-day evaluation window" cannot be
  derived from crypto. Not with scaling, not with vol-normalisation, not with a fudge factor.
  If a number is going into the prop-firm hurdle calculation, it must come from ES.
- **Anything about the overnight/RTH interaction specific to equities** — the cash open, the
  16:15 CT close, the Sunday-evening reopen, the reaction to US macro prints at 08:30 CT. These
  are the *content* of the 23-hour ES session, and crypto has none of them.
- **Roll cost, term structure, or expiry behaviour** on the perpetual leg. (The quarterly leg can
  speak to roll mechanics, not to ES roll magnitudes.)
- **Anything about liquidity, slippage, or fill quality at ES scale.** Different books, different
  tick sizes, different queue dynamics.
- **The weekend-gap term for ES specifically.** ES weekends and BTC weekends are driven by
  different news flows.

### Verdict

**This can substitute for a mechanism study and a null-model control. It cannot substitute for a
risk-parameter estimate.**

Concretely: use it to build and validate the trailing-floor machinery, to establish the *shape* of
drawdown-versus-holding-period, and — via the CME BTC pre-2026 leg — to size the session-gap
contribution on a controlled single asset. Then re-estimate every number that touches the actual
4% hurdle on ES data from another lane. If this lane's output ends up as a percentage in a
go/no-go decision on the prop track, the lane has been misused.

---

## PART 3 — CME BITCOIN FUTURES AS THE BRIDGE

I chased this hard, as instructed. Here is the full result.

### It is a real CME Globex contract

CME Bitcoin futures (`BTC`, 5 BTC) and Micro Bitcoin futures (`MBT`, 0.1 BTC) list on Globex,
clear through CME Clearing, have quarterly-plus-serial expiries, a published settlement procedure,
and a real roll calendar. Everything ES has structurally, BTC has. There is also `MIB`
(BTIC on Micro Bitcoin, London close), which exists but is not relevant here.

### The session — and the deadline

**Pre-2026-05-30**, CME crypto futures ran the standard CME Globex schedule: Sunday afternoon
open through Friday afternoon close, with a daily 60-minute maintenance break and **no weekend
trading**. This is the same session template as ES.

I verified the weekend closure directly rather than taking it on trust. Daily bars for `BTC=F`,
2018-01-02 through 2026-05-28 — **2117 bars, weekday distribution:**

```
Tue 436   Wed 432   Thu 428   Fri 425   Mon 396   Sat 0   Sun 0
```

Zero weekend bars across eight and a half years. The session was real.

**On 2026-05-30, CME took Bitcoin and Ether futures and options to 24/7 on Globex**, retaining
only a 60-minute maintenance window Sunday 22:00–23:00 UTC. I confirmed the current state
empirically: one month of hourly `BTC=F` bars shows **all 24 distinct UTC hours and all seven
weekdays present**. The famous "CME gap" is gone.

**Implication, stated bluntly:** CME BTC is a valid ES session proxy for **2017-12-17 through
2026-05-28** and is **not** one after that date. The usable window is historical, it is
eight-and-a-half years long, and it is closed. Pull it as a fixed historical dataset. Do not build
a live pipeline expecting the session to persist.

### Is it obtainable free?

Not strictly free from any source I could verify. But the cheapest path is close enough to free
that the distinction is academic:

**Best option — Databento GLBX.MDP3.**
- Coverage for `BTC`: **since 2017-11-19 UTC** (definition messages precede the 2017-12-17 first
  trade date). `MBT` also available.
- Schemas confirmed on the catalog page: `mbo`, `mbp-1`, `mbp-10`, `tbbo`, `trades`, `bbo-1s`,
  `bbo-1m`, `ohlcv-1s`, `ohlcv-1m`, `ohlcv-1h`, `ohlcv-1d`, `definition`, `statistics`, `status`.
  Note `definition` and `statistics` — those give you the contract calendar and the official
  settlement prices, i.e. the roll and settlement information the perpetuals cannot provide.
- **$125 signup credit, valid 6 months, usable against any historical data.** Historical is
  usage-priced by uncompressed size, advertised "from $0.50/GB".
- **Cost estimate for what we need.** A DBN OHLCV record is 56 bytes. Front-month CME BTC at
  roughly 1380 tradeable minutes/day x ~252 days/year x ~8.4 years is about 2.9M bars, or
  **~165 MB uncompressed**. Even at a per-GB rate several times the advertised floor, that is
  **well under one dollar** against a $125 credit. Pulling every outright in the BTC and MBT
  chains at 1-minute would still be single-digit dollars.
  *This is my arithmetic from the published record size and advertised rate — I could not fetch
  the exact GLBX $/GB figure, which Databento exposes only through its authenticated cost
  estimator. Confirm with the estimator before committing.*
- **Caveat:** requires creating an account. That is a user action, not one I can or should perform.
- Also note: **usage-based pricing for CME *live* data was discontinued 2025-04-16** and CME live
  now requires a subscription (Standard ~$179/mo). This does **not** affect historical, which
  remains usage-priced. Since the useful window is historical and closed, this is irrelevant to us.

**Second option — FirstRateData.** 1-minute CME BTC from **2017-12-17**, in unadjusted plus
absolute- and ratio-adjusted continuous forms, with a free sample download to inspect the format
and a paid full dataset (~$100/yr renewal after the first month). The ratio-adjusted continuous
series is genuinely convenient if you do not want to build roll logic yourself. Verify the sample
covers enough to test the ingestion path before paying.

**Ruled out:** CME DataMine is subscription-only per dataset. Portara's free tier is withdrawn.
CME's free FTP material is end-of-day/reference, not intraday bars. Coinbase Derivatives
(nano bitcoin `BIT`, a real CFTC-regulated DCM) publishes no free bulk historical files that I
could find — its data is routed through Coin Metrics and its own institutional marketplace, and
in any case Coinbase Derivatives has itself moved to 24/7, so it carries the same
session-obsolescence problem as CME with far less history.

### Recommended plan for this lane

1. **Pull CME BTC (and MBT) `ohlcv-1m` from Databento for 2017-12-17 → 2026-05-28**, plus the
   `definition` and `statistics` schemas for the roll calendar and settlement prints. Cost should
   be under a dollar against the free credit; verify with the cost estimator first. This is the
   real deliverable of the lane: **a genuine CME Globex contract with the exact ES session,
   real roll, and real settlement, at 1-minute resolution, for eight and a half years.**
2. **Pull Binance USD-M `BTCUSDT` 1m klines plus `fundingRate` from data.binance.vision** as the
   24/7 control arm. Free, no key, checksummed. Same underlying asset, no session.
3. **Difference (1) and (2)** to isolate the session-and-gap contribution to trailing-drawdown
   risk on a single asset with volatility held constant. This is the only design in this lane that
   produces a defensible causal statement.
4. **Do not carry any absolute percentage from either into the 4% hurdle calculation.** Re-estimate
   on ES.

---

## Sources

- [binance/binance-public-data](https://github.com/binance/binance-public-data) — data types, intervals, URL structure, CHECKSUM convention
- [data.binance.vision](https://data.binance.vision/) — bucket, probed directly via its S3 endpoint
- [public.bybit.com](https://public.bybit.com/) — directory listings probed directly
- [public.bitmex.com](https://public.bitmex.com/?prefix=data/trade/) — S3 ListBucket, HEAD and gunzip probes
- [Deribit API v2](https://docs.deribit.com/) — `get_tradingview_chart_data`, `get_funding_rate_history` called live
- [Deribit rate limits](https://docs.deribit.com/articles/rate-limits)
- [Bybit rate limits](https://bybit-exchange.github.io/docs/v5/rate-limit)
- [Binance REST limits](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/limits)
- [BitMEX REST API](https://www.bitmex.com/app/restAPI)
- [Databento CME Bitcoin Futures (BTC) catalog](https://databento.com/catalog/cme/GLBX.MDP3/futures/BTC) — coverage since 2017-11-19, schema list
- [Databento CME Micro Bitcoin Futures (MBT)](https://databento.com/catalog/cme/GLBX.MDP3/futures/MBT)
- [Databento pricing](https://databento.com/pricing) — $125 credits, 6-month validity, $/GB model
- [Databento: new CME pricing plans](https://databento.com/blog/introducing-new-cme-pricing-plans) — live usage pricing discontinued 2025-04-16
- [FirstRateData CME Bitcoin Futures](https://firstratedata.com/i/futures/BTC) — 1m from 2017-12-17, free sample
- [Portara CME Bitcoin intraday](https://portaracqg.com/futures/int/btc)
- [CME DataMine](https://www.cmegroup.com/datamine.html)
- [CoinMarketCap: Bitcoin CME futures go 24/7](https://coinmarketcap.com/academy/article/%20bitcoin-cme-futures-24-7-trading) — 2026-05-30 launch, Sunday 22:00–23:00 UTC maintenance
- [CoinDesk: CME ends bitcoin weekend gaps](https://www.coindesk.com/markets/2026/05/28/bitcoin-s-famous-cme-gaps-are-about-to-disappear-though-three-remain-unresolved)
- [OKX rate limits](https://github.com/dojez25/okx-rate-limits-explained)
- [CryptoDataDownload](https://www.cryptodatadownload.com/data/binance/) — secondary mirror, not needed given primary sources
