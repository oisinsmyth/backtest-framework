# Lane 01 — Reddit and trading forums

Research date: 2026-09-01. Scope: free historical intraday CME futures data (ES/NQ/RTY/YM first;
CL/GC/ZB/6E useful), 15-min or finer, 5+ years, full ~23h Globex session, programmatic access.

---

## 0. Access constraints — read this before trusting the coverage

**Reddit was completely inaccessible from this environment.** Three independent routes were tried:

| route | result |
|---|---|
| `WebSearch` with `allowed_domains: reddit.com` | HTTP 400 — "the following domains are not accessible to our user agent" (Reddit blocks the Anthropic crawler) |
| `WebFetch` on `old.reddit.com` / `reddit.com` | refused at the tool layer |
| Browser pane `navigate` to `reddit.com` | "blocked by policy" |
| Redlib/Libreddit mirrors (`redlib.catsarch.com`, `safereddit.com`, `l.opnxng.com`) | 403 / Anubis anti-bot / socket hang up |

Unrestricted web searches also returned **zero** reddit.com links across ~10 queries, consistent with
Reddit being excluded from the search index this tool uses. **So: r/algotrading, r/quant,
r/quantfinance, r/futures, r/FuturesTrading, r/thewallstreet and r/systematictrading are UNCOVERED.**
Anything the principal expects specifically from Reddit is not in this document. That gap needs either
a human with a browser or a different tool.

Also blocked: `quant.stackexchange.com` and `api.stackexchange.com` (tool-layer refusal), so
Quant StackExchange is uncovered too.

**What I could reach:** EliteTrader (via browser pane — hard limit of ~5 guest page views per session,
which I spent on the highest-value threads), futures.io / NexusFi (browser pane, no limit hit),
Hacker News (via the Algolia API), QuantConnect forum + docs, and every vendor's own pages for
verification.

---

## 1. Sources found

### 1.1 Massive.com (formerly Polygon.io) — Futures Basic

| field | |
|---|---|
| name + URL | Massive Futures API — https://massive.com/futures , https://massive.com/pricing?product=futures |
| **genuinely free?** | **free tier** (registered account, $0/mo "Futures Basic") |
| instruments | All futures tickers on CME, CBOT, NYMEX, COMEX — ES, NQ, RTY, YM, CL, GC, ZB, 6E all in scope. Individual contracts (`ESZ6`-style symbology); continuous contracts listed as "coming soon" |
| granularity | Minute aggregates on the free tier. Paid tiers add second bars, nanosecond trades and quotes. Timespans documented: `sec, min, hour, session, week, month, quarter, year` |
| history depth | **2 years on free**; 5 years at $79/mo (Developer); 7+ years at $199/mo (Advanced) |
| **full session or RTH only?** | Full session, inferred not stated. The launch post describes futures as trading "nearly 24 hours a day, 5 days a week (typically Sunday 5:00 p.m. CT through Friday 5:45 p.m. CT, with daily maintenance windows)" and says aggregates are built from *all* trades in the period. No RTH filter is documented. **Not explicitly confirmed — verify empirically on a first pull.** |
| access method | REST API (+ WebSocket, + flat files on paid tiers) |
| verified how | **Primary source.** Pricing page, product page and launch blog all read directly. Forum trail: EliteTrader thread 387845, post #20, 22 Jan 2026 — the Massive sponsor rep publicly offering free futures-beta entitlement to a poster |
| catch | **2 years fails the 5-year minimum.** 5 API calls/minute on free is a hard throttle — a full ES/NQ/RTY/YM minute-bar backfill over 2 years across ~8 quarterly contracts each is many thousands of calls, so plan for a multi-day trickle or accept the $79 tier. No continuous contract yet, so you stitch. Futures only went GA 2026-05-28, so the product is ~3 months old — expect rough edges |

### 1.2 NexusFi (ex futures.io) — NinjaTrader Market Replay data archive

| field | |
|---|---|
| name + URL | https://nexusfi.com/local_links.php?catid=28 (category "NinjaTrader Market Replay Data") |
| **genuinely free?** | **free with account** — entries show "Login to Download". The paid-only category is called out separately as "The Elite Circle" (618 entries, "Elite Members only"); Market Replay sits under the ordinary NinjaTrader category (1529 entries). **I did not register, so "free account is sufficient" is inferred from the site's own category labelling, not tested.** |
| instruments | Filter tags on the category page: `6e, cac40, cl, es, fdax, fesx, fgbs, nq, tf, ym, zb, zn`. That is ES, NQ, YM, TF (the pre-RTY Russell), CL, ZB, ZN, 6E — nearly the whole target list. No GC |
| granularity | Tick-by-tick with Level 2 (NinjaTrader `.nrd` market-replay records) |
| history depth | **~2017 to Aug 2026.** Oldest entry seen sorting ascending: "Market Replay CL 01-17 (NT8)", uploaded 2017-04-23. Newest: "Market Replay CL 08-26", 2026-08-02. ~400 entries across 40 pages, still actively maintained |
| **full session or RTH only?** | Full session. Market replay records the whole electronic session. Caveat from the uploader's own notes: "these downloads are likely not to include Sundays data", and archives contain "only the dates with the most volume for this contract" — i.e. the front-month window only |
| access method | Manual per-file download (many are multi-part 7z, ~99 MB per part; ES 06-26 was 11 parts). No API |
| verified how | **Primary source** — I read the live category and search listings in the browser pane |
| catch | Three real ones. (1) `.nrd` is NinjaTrader's proprietary binary; you need NinjaTrader 8 installed (Windows) to load and re-export to CSV — that's a conversion pipeline, not a download. (2) Front-month-only coverage is actually convenient for stitching but means no full contract lifecycles. (3) **Licensing is grey**: this is member-uploaded data originally sourced from a broker/vendor feed (IQFeed/CQG lineage), redistributed on a forum. Fine for private research; do not assume it is redistributable |

### 1.3 QuantConnect — AlgoSeek US Futures (cloud)

| field | |
|---|---|
| name + URL | https://www.quantconnect.com/data/algoseek-us-futures , docs at https://www.quantconnect.com/docs/v2/writing-algorithms/datasets/algoseek/us-futures |
| **genuinely free?** | **free with account, cloud-only.** Dataset page states verbatim: "Free access to the most popular US Futures in QuantConnect Cloud for backtest and research" |
| instruments | 157–162 of the most actively traded contracts across CME, CBOT, NYMEX, COMEX, CFE, ICE |
| granularity | Tick / second / minute / hour / daily |
| history depth | **May 2009 → present.** ~17 years — the deepest genuinely-free option found |
| **full session or RTH only?** | Full session — `extended_market_hours=True` is a supported algorithm parameter and the docs describe both regular and extended hours. Documented quirk: AlgoSeek daily volume differs from CME's because pit trades are excluded |
| access method | Cloud IDE / research notebooks only. LEAN CLI bulk download requires a paid plan |
| verified how | **Primary source** for the dataset facts. The free-tier resolution question is only forum-verified (see catch) |
| catch | **You cannot get the data out.** QuantConnect's own forum: "Due to licensing restrictions, QuantConnect cannot currently offer futures for local download"; and "the terms of QuantConnect's deals with data vendors allow them to provide data for free use in the IDE but they aren't allowed to provide it for free download". Second, there is a **direct contradiction I could not resolve**: the pricing page implies minute/hour/daily are all included on Free, while forum discussion 19781 says "Daily and Hourly history is available broadly; minute/second/tick have shorter trailing windows" on the free plan. If the second is right, free-tier minute history is a short trailing window and this source collapses. **Must be tested by signing up and running a `QuantBook` history call for ES minute bars back to 2010.** People do exfiltrate CSVs via a backtest that writes to the project output folder — that is a licence violation, not a workaround |

### 1.4 Dukascopy Historical Data Export (index/commodity CFD proxy)

| field | |
|---|---|
| name + URL | https://www.dukascopy.com/swiss/english/marketwatch/historical/ ; community wrappers `dukascopy-node` (https://www.dukascopy-node.app) and `dukascopy-python` |
| **genuinely free?** | **free**, no account needed for the web export tool; JForex demo account for the platform route |
| instruments | **Not CME futures — CFD proxies.** `usa500idxusd` (S&P 500), `usatechidxusd` (Nasdaq 100), `usa30idxusd` (Dow), `ussc2000idxusd` (Russell 2000), plus energy/metals/agriculture CFDs and FX |
| granularity | Tick-by-tick upward, through 1-min to monthly |
| history depth | Instrument pages list earliest dates of 1980 (usa500), 1990 (usatech), 2013 (usa30), 2018 (ussc2000) — **but those are almost certainly the daily-series starts. Tick/minute history for index CFDs typically begins ~2010–2012. I could not verify the intraday start dates and the search budget ran out.** |
| **full session or RTH only?** | Near-24h CFD sessions, close to but not identical to Globex hours (different daily break, different holiday calendar) |
| access method | Web export tool (manual), JForex Historical Data Manager, or fully programmatic via `dukascopy-node` / `dukascopy-python` pulling the same binary tick archives |
| verified how | **Primary source** for the free/tick/CFD facts and the instrument IDs; the intraday depth is **not verified** |
| catch | It is a broker's CFD price stream, not exchange data: no real contract volume, no open interest, broker-specific spreads and quote filtering, and prices are the broker's synthesis. Fine for testing session/overnight *shape*, dangerous for anything volume-sensitive or fill-realistic. Corroborates the March 2026 EliteTrader claim that "many large, reputable CFD brokers provide free tick data going back several years" |

### 1.5 Interactive Brokers TWS API

| field | |
|---|---|
| name + URL | https://www.interactivebrokers.com/en/software/api/apiguide/tables/historical_data_limitations.htm |
| **genuinely free?** | free with a funded account (+ ~$10–15/mo CME data subscription in practice) |
| instruments | All CME futures |
| granularity | 1-second to daily bars |
| history depth | **Fatal: expired futures are filtered out beyond ~2 years past expiry.** `includeExpired` gets you inside that window and no further |
| **full session or RTH only?** | Both — `useRTH=0` returns the full electronic session |
| access method | API (`ib_insync` / `ibapi`) |
| verified how | **Primary source** (IBKR docs) + corroborated on EliteTrader thread 367585 post #12, 9 Jun 2022: "it is only available for futures contracts which are either not expired, or expired within the last two years" |
| catch | The 2-year expired-contract wall makes a 10-year stitched history impossible. Also heavy pacing limits, and a 2025-era forum verdict: "Run away from the IBKR API like the plague" (opinion, one poster). Useful only as a rolling forward-collector |

### 1.6 Community tick-data sharing threads (NexusFi)

| field | |
|---|---|
| name + URL | "Official tick data sharing thread for raw data, GomRecorder and QCollector" (1,515 replies, IQFeed-sourced via QCollector); "CME Futures Historical DATA (FREE)" https://futures.io/brokers/36820-cme-futures-historical-data-free.html |
| **genuinely free?** | free with account (some threads are Elite Circle = paid) |
| instruments | Thread 36820: 6A/6B/6C/6E/6S/6J, ES, NQ, YM, NKD, TK, CL, GC, SI, PL, HG, ZC, ZS, ZW, ZL, ZN, ZB + calendar spreads |
| granularity | Full MBO — every DOM limit-order change plus every trade, microsecond timestamps |
| history depth | **Dec 2013 → mid-2014 only.** Thread posted 2015-08-27, last activity 2015-08-28 |
| **full session or RTH only?** | Full session |
| access method | Manual — a `cloud.mail.ru` public folder link |
| verified how | **Primary source** — I read the thread. But the *link* is an 11-year-old third-party cloud share; I did not test it and would assume it is dead |
| catch | Stale, far too shallow (7 months), acknowledged gaps, undocumented provenance, and a bespoke `A;/B;/T;` text format. Listed only so it is not rediscovered as a lead. **Dead end.** |

### 1.7 Ruled out — checked and rejected

| source | why it fails |
|---|---|
| **Kibot free samples** (kibot.com/free_historical_data.aspx) | Free files are **US equities only** (IBM, OIH 1-min; IVE, WDC tick), **regular session only 09:30–16:00 ET**, 1–3 months. Futures samples exist only through the paid custom-order builder. Verified on Kibot's own page. Fails on instrument, session and depth simultaneously |
| **Stooq** (stooq.com/db/) | 5-minute bundle is capped at ~2000 bars ≈ 1 month, and the download is CAPTCHA-gated. Hourly bundle is coarser than our 15-min floor. Daily only is genuinely useful. Fails on depth + access |
| **eoddata.com** | Paid, and intraday tops out at 30-min for US *stocks*. Plus a specific quality complaint on EliteTrader 367585 #10 (Jun 2022): "Many errors or simply missing chunks of data, even in ES... they don't have enough personnel to monitor/correct the data anymore" |
| **CSI Data / Norgate / Pinnacle / Metastock-Reuters** | Every one of these is the forum consensus for *quality*, and every one is **EOD only** for futures. A poster called CSI directly on 2022-06-09: "just called them, they only have EOD." Paid |
| **marketreplaydata.com** | $6–7/month, ~3–4 years back. Not free, but cheap; NinjaTrader-format like 1.2 |
| **ANFutures** | ~$96 one-off for overnight-session minute data. Not free, 2016-vintage recommendation, not re-verified |
| **TradingBlox free historical data** (tradingblox.com) | Named on Hacker News in **2009**. Daily futures only. Assume stale |
| **Alpaca free 1-min** | Named on EliteTrader 2026-03-05 as free 1-min — but **equities/ETFs only (SPY, QQQ)**, not futures. Only useful as an RTH-biased proxy |
| **dxFeed via tastytrade, Rithmic, CQG, Tradovate, IQFeed, Kinetick, Sierra Chart Denali** | All broker/vendor feeds. Live-data-first; historical access is subscription-gated or needs a funded account. The Dec 2025 EliteTrader thread established the CME licensing wall: NinjaTrader/Tradovate quoted "We only offer professional prices... $600 per month up to about $1500 per month" for API redistribution |
| **AlgoSeek, TickData.com, Portara/CQG, FirstRate** | Free *samples* only. AlgoSeek is the upstream of the QuantConnect dataset (1.3), which is the better way to touch it for free |

---

## 2. Ranked shortlist — what is actually worth trying

1. **Massive.com Futures Basic (free tier)** — the only source in this lane that is free, programmatic,
   real CME data, minute granularity, and full-session, all at once. Its single failure is depth
   (2 years vs. the 5-year minimum). Start here because it costs nothing to prove out, and if the
   pipeline works, $79/mo buys 5 years on the same code path. **Test first: does a minute-bar pull for
   `ESZ5` return overnight bars (18:00–08:00 CT)?**

2. **QuantConnect / AlgoSeek US Futures (free, cloud)** — by far the deepest free data (May 2009,
   minute, extended hours, 157+ contracts). Worth an afternoon *purely to resolve the contradiction*:
   sign up on Free, run a `QuantBook` history request for ES minute bars in 2012, see whether it
   returns. If it does, this is the strongest free dataset in existence for this spec — with the
   permanent caveat that the data cannot legally leave QuantConnect Cloud, so it forces the backtest
   to live there rather than in this repo's framework.

3. **NexusFi NinjaTrader Market Replay archive** — free with registration, ES/NQ/YM/TF/CL/ZB/ZN/6E,
   tick+L2, 2017→2026 (~9 years), full session. The best depth-plus-breadth combination that you can
   actually hold on disk. Costs: a NinjaTrader-8 conversion pipeline, manual multi-part downloading of
   hundreds of ~100 MB archives, front-month-only windows, and grey redistribution provenance. Rank it
   third on effort, not on data quality.

4. **Dukascopy tick CFDs** — free, programmatic, deep, and *not CME futures*. Only worth it as a
   cross-check on overnight session shape, or as a stand-in while a real feed is being sorted. Do not
   let CFD prices into a production backtest that cares about volume or fills.

5. **Interactive Brokers** — not a historical source (2-year expired-contract wall), but the cheapest
   way to *start accumulating* your own full-session minute bars going forward.

Not ranked but repeatedly converged on by every recent forum thread (Dec 2025 – Apr 2026) as "the"
answer for futures history: **Databento** — already established as offering $125 free credits. Every
serious 2025–2026 EliteTrader thread on futures data ends there.

---

## 3. What I could NOT verify

- **All of Reddit.** No r/algotrading, r/quant, r/futures etc. See §0. This is the largest gap and it
  is the lane the principal specifically expected leads from.
- **Quant StackExchange** — domain refused by the fetcher.
- **Whether a free (non-Elite) NexusFi account can actually download the Market Replay files.** Inferred
  from category labelling; not tested. Register and try one small CL archive.
- **Whether QuantConnect's Free tier serves *minute* futures history back to 2009**, or only a short
  trailing window. The pricing page and the community forum contradict each other.
- **Whether Massive's free minute aggregates include the overnight session.** Strongly implied
  (aggregates built from all trades, no RTH parameter documented) but never stated.
- **Dukascopy intraday start dates** for the index CFDs. The published "earliest date" figures (1980,
  1990) are certainly daily-series starts and must not be read as tick history.
- **The `cloud.mail.ru` link** in NexusFi thread 36820 — not clicked, presumed dead after 11 years.
- Forum threads on EliteTrader beyond the five I could open before hitting the guest view cap:
  notably "Futures Data - For Sale? Anyone?" (Feb 2026), "Best Affordable Historical Tick Data for
  /MNQ" (Feb 2026), "~1h delayed CME and ICE US trade data" (Jun 2026), and page 3 of thread 387845.

---

## 4. Thread index (for anyone re-treading this)

| thread | date | value |
|---|---|---|
| [EliteTrader 387845 — API data feed for futures compatible with Python](https://www.elitetrader.com/et/threads/api-data-feed-for-futures-which-is-compatible-with-python-suggestions.387845/) | Dec 2025 – Jan 2026 | **High.** Establishes the CME licensing wall and surfaces the free Massive futures beta |
| [EliteTrader 388921 — Backtesting futures](https://www.elitetrader.com/et/threads/backtesting-futures.388921/) | Mar – Apr 2026 | Medium. "10 years of history" ask; answers converge on Databento + the free-CFD-tick-data hint |
| [EliteTrader 367585 — Sources of historical futures data](https://www.elitetrader.com/et/threads/sources-of-historical-futures-data.367585/) | Jun 2022 | Medium. Rob Carver's own list. All EOD. Source of the IBKR 2-year and eoddata-quality findings |
| [EliteTrader 304351 — Historical Intraday (1 minute) NQ data](https://www.elitetrader.com/et/threads/historical-intraday-1-minute-nq-data.304351/) | Nov – Dec 2016 | Low/stale. NinjaTrader-export and marketreplaydata.com leads |
| [NexusFi downloads — NinjaTrader Market Replay Data](https://nexusfi.com/local_links.php?catid=28) | 2017 – Aug 2026 | **High.** The archive itself |
| [NexusFi 36820 — CME Futures Historical DATA (FREE)](https://futures.io/brokers/36820-cme-futures-historical-data-free.html) | Aug 2015 | Dead end, documented so it is not rediscovered |
| Hacker News (Algolia API, `free futures historical data`) | 2009 – 2020 | Low. Everything named is stale or equities-focused |
