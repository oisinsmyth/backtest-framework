# Free futures data: the exhaustive search

**Twelve parallel research lanes, 2026-08-29.** The question: does a genuinely free source of
intraday CME futures data exist — ES/NQ/RTY/YM, 15-minute or finer, 10+ years, **the full ~23-hour
Globex session** — before we consider paying for one.

**Answer: yes, effectively.** One route delivers the exact specification at **$0 out of pocket**, and
two more give genuinely free full-session data of lower fidelity for cross-checking.

---

## 1. The answer — Databento's signup credit

**`GLBX.MDP3`, schema `ohlcv-1m`, paid for entirely by the $125 new-user credit.**

| | |
|---|---:|
| one symbol-year | **~$0.51** |
| **ES + NQ + RTY + YM, 15 years** | **$30** |
| all eight symbols, 16 years | **$65** |
| what the credit buys | **~246 symbol-years** |

**The rate was derived, not assumed.** Databento does not publish the per-schema $/GB table, but its
API reference publishes two worked examples of *the same query*:

- `get_billable_size(GLBX.MDP3, ESM2, trades, 2022-06-06 → 2022-06-10T12:10)` → **99,219,648 bytes**
- `get_cost(…same…)` → **$2.587353944778**

`99,219,648 / 2^30 = 0.0924055 GiB`, and `$2.587353944778 / 0.0924055 =` **exactly $28.00/GiB** —
which also proves their "GB" means 2^30. `OhlcvMsg` is a fixed 56 bytes and no bar prints for a
minute without a trade, so `1,380 min/day x 252 days x 56 B = 19.47 MB = $0.51` per symbol-year is
an **upper** bound.

**One inferred step, flagged:** whether `ohlcv-1m` bills at the same rate as `trades`. The published
OPRA `list_unit_prices` example prices `trades`, `ohlcv-1s` and `ohlcv-1m` **identically**.
Confirmable in 30 seconds post-signup via `list_unit_prices(dataset="GLBX.MDP3")`. **The conclusion
survives a 2x error.**

**It is the real thing, not a proxy.** `GLBX.MDP3` is the raw MDP 3.0 capture — **full ~23-hour
Globex, no RTH filter, no RTH variant** — from the official licensed CME distributor. **ES from
2010-06-06 (16.2 years).**

**The schema choice is what makes it free.** Same ES, 15 years: `ohlcv-1m` **$7.62**, `ohlcv-1s`
~$457, `trades` ~$2,180.

**Three traps:**
1. Use `stype_in="continuous"` (`ES.c.0`). **Never `parent`** — it resolves to every outright *plus*
   every calendar spread.
2. Use `batch.submit_job`, not streaming. **Streaming re-bills on retry**; batch bills once and
   allows 30 days of free re-downloads.
3. **The credit expires in 6 months**, one set per team, and they police farming.

**Caveat:** RTY reaches only ~9 years — the E-mini Russell moved to CME in 2017. **Market structure,
not a vendor limit**, and independently confirmed in two lanes.

---

## 2. Genuinely free, no credit — the cross-checks

### Dukascopy index CFDs — verified twice, independently, by download and decode

Free, **no account, no API key**, tick level with bid/ask. Coverage: **ES proxy from 2012, NQ and YM
from 2013, RTY from 2018, CL from 2011, GC from 2003.**

**It covers our blind window densely.** Tick counts on an ordinary session, `USA500.IDX/USD`:

| GMT hour | 00 *(20:00 ET)* | 02 | 04 | 06 | 08 | *RTH* |
|---|---:|---:|---:|---:|---:|---:|
| ticks | **10,271** | 7,337 | 5,793 | 4,993 | 8,191 | *14,433* |

Overnight spread ~0.7 index points against ~0.5 in RTH. **Dukascopy states the quote tracks the
front-month S&P future.** *(Gotcha: the feed URL uses a zero-based month.)*

**What it is not:** a broker CFD — no exchange volume, no contract roll, bid/ask only, single-feed,
and levels differ from ES by a time-varying basis. **It errs one-directionally: dealer spread
widening manufactures adverse excursions that never happened on the ES tape**, so any breach
frequency from it is a **conservative upper bound**, never a point estimate.

### HistData — solid second, strictly dominated

`SPXUSD` and `NSXUSD` 1-minute, **Nov 2010 → Aug 2026**, free. Verified by download: **1,295–1,320
bars in every hour bucket 00–15 and 18–23**, one structural break 16:15–18:00 ET. **Volume is always
zero and there is no bid/ask.** Its 66-symbol list has **no Dow and no Russell proxy**, so Dukascopy
dominates it. *(The download token is JS-populated — a plain HTTP client cannot obtain it.)*

### Others worth knowing

| source | what it gives | why it is not primary |
|---|---|---|
| **Massive** (ex-Polygon), Futures Basic **$0** | CME/CBOT/NYMEX/COMEX **minute aggregates**, sanctioned API | **2 years only**, 5 calls/min |
| **QuantConnect cloud, free** | **May 2009→present, minute, extended hours, 157+ contracts** | **Cannot be downloaded** — licensing |
| **NexusFi Market Replay archive** | ES/NQ/YM/CL/ZB/6E, **tick + L2, 2017→2026, full session**, free with registration | `.nrd` proprietary binary, needs NT8 on Windows; manual multi-part downloads |
| **`ftp.cmegroup.com` SPAN archive** | **Daily settlements, all contract months, 2013 → 2025-09-12**, anonymous | **Daily only.** Excellent for roll calendars |
| **CFTC COT** | 1986→present, bulk + Socrata API, **public domain** | Not price data |
| **CME BTC futures** | A **genuine Globex contract running the exact ES session template, 2017-12-17 → 2026-05-28** | CME went 24/7 on 2026-05-30, closing the window. <$1 of Databento credit |

---

## 3. The governing constraint — two independent confirmations

**Harvested exchange data cannot be committed to this repo, private or not.**

- **CME's Data Terms** prohibit *"downloading"*, *"compiling … through systematic retrieval to
  create collections, compilations, databases"*, scripted access, and — in a **bolded** clause — any
  use *"for any machine learning and/or artificial intelligence"*. Personal use explicitly excludes
  *"providing archived or cached data sets containing CME Data to another person or entity"*.
- **Sierra Chart:** *"Under no circumstances shall it be redistributed in any form to others."*
- **NinjaTrader's** Uniform Subscriber Agreement makes redistribution of data **or derived analysis**
  a material breach.

**This breaks [D24](../../decisions/D24-immutable-data-snapshots-fetch-once-freeze.md)'s
commit-the-derived-fixture convention for any futures fixture.** The pattern must instead be a
**gitignored cache, a committed re-fetch script, and a committed `.meta.json`** recording what the
cache should contain — which is what `fetch_short_universe.py` already does for its raw layer.

*(One genuine ambiguity, recorded as unresolved rather than assumed either way: `ftp.cmegroup.com`
is a different host with anonymous access, no banner and no click-through, and CME's Terms are
drafted around "the Website".)*

---

## 4. Ruled out, with evidence

**Roughly seven of every nine commonly-cited "free futures data" claims proved stale.**

| | why |
|---|---|
| **Nasdaq Data Link / Quandl** | With the **"Free" filter applied the entire catalogue returns ONE dataset — a carbon-credit issuance calendar.** CHRIS retired ("no longer updated", Nasdaq support); SCF/OWF/CME tables absent. **And CHRIS was daily even in its prime** |
| **Yahoo / yfinance** | **Serves the full 23-hour session** (1,379 non-null minutes, one 61-min maintenance gap) — but **15m caps at 60 days**, and backfill is impossible because the constraint is `now − startTime`, not window width |
| **IBKR** | *"Expired futures data older than two years counting from the future's expiration date."* **~2–3 year ceiling.** `CONTFUT` cannot take an `endDateTime`, so walk-backwards backfill is structurally impossible |
| **TradingView** | ToS prohibits automated collection **and** non-display use. And Premium's 20,000 bars ÷ 92/day ≈ **10 months** |
| **Tradovate** | $315/mo ($25 API + $290 CME sub-vendor licence), minute only to 2017 |
| **Rithmic** | **Purges expired contracts** — fatal for stitching |
| **Stooq** | **SHA-256 proof-of-work bot wall**; CSV endpoint returns "Access denied" even when solved. Daily anyway |
| **`pandas-datareader`** | **Deleted every securities reader in June 2026.** Macro-only now |
| Schwab, Alpaca | No futures history at all |
| Norgate, CSI, Pinnacle | *"We do not provide … intra-day or 'tick' data"* — EOD only |
| Twelve Data, Finnhub, EODHD, Tiingo, Marketstack, FMP, Intrinio | **No futures at any tier** |
| Academic Torrents, Zenodo, Dryad, figshare, OSF, AWS Open Data | Nothing. **data.world's Open Data Community retired 2026-07-13** |
| WRDS | Institutional affiliation required **and** non-commercial only — closed twice over |
| Deutsche Börse AWS open data | Free 1-minute Eurex bars, **withdrawn** — both buckets `AccessDenied` |

**The painful near-miss:** `brkly03/CME-Globex-MDP-3.0` on HuggingFace holds **4,685,961 ES 1-minute
bars, ~Dec 2010 → mid-2026, full Globex session** — and **the timestamp column is a sequential row
counter.** Prepared as foundation-model training data. Reconstruction is unreliable because
zero-volume minutes are dropped by `ohlcv-1m` aggregation and each drop permanently desynchronises
everything after it.

---

## 5. Two corrections to our own prior assertions

1. **"yfinance is daily only" and "Yahoo futures are RTH only" are BOTH WRONG.** Yahoo serves 1m–90m
   and the **full 23-hour session**. Both claims appeared in this project's own briefs and were
   repeated rather than tested. What kills Yahoo is **depth**, not coverage.
2. **A cross-agent correction worth keeping:** one lane reported "96 bars/day, full 24h" for Yahoo;
   another measured **92** and identified the difference as **padded slots versus the 61-minute
   maintenance halt**. 92 x 15 min = 23h exactly.

---

## 6. The roll warning — applies to every source, not just the free ones

`ES=F` is the **front-month contract spliced at expiry, undocumented and unadjusted**:

- 2024-12-20 close **5840.26** → Monday open **6001.75**: a **+161.49 pt (+2.77%) spurious gap** on a
  day SPY moved +0.60%
- **15 of the top 16 ES-vs-SPY divergences over five years fall on quarterly expiries**
- **`adjclose` is a verbatim copy of `close` on 1258/1258 bars**
- Yahoo rolls **at expiry, not at volume crossover**, so the last 4–5 days of each quarter track the
  dying contract (volume 1,996k → 532k) — **contaminating 7–8% of the sample**

**Any purchased source must be acceptance-tested for exactly this**, and
`pysystemtrade`'s `roll_calendars_csv` plus its `PRICE_CONTRACT`/`FORWARD_CONTRACT`/`CARRY_CONTRACT`
schema is the best free reference implementation of correct stitching.

---

## 7. What the search could not cover

**Reddit was inaccessible from every route** — `WebSearch` with `allowed_domains: reddit.com`
returns HTTP 400, `WebFetch` and the browser pane refuse it by policy, and three redlib mirrors
returned 403 or hung. **r/algotrading, r/quant, r/futures and r/systematictrading are uncovered**,
and Quant StackExchange is blocked at the tool layer. **That lane needs a human with a browser.** It
was compensated with EliteTrader, futures.io and Hacker News, but the gap is real.

**Also unverified:** Databento's `ohlcv-1m` unit price directly (30 seconds post-signup); whether
CME licence fees apply on top of usage-based historical; NinjaTrader's claimed ~2006 depth (every
forum fetch 404'd); IBKR's live pricing table (403 to automated fetch on every hostname).

---

## 8. A structural argument, and it is the strongest thing here

> **Replication packages for intraday US futures studies ship derived estimates, never bars, because
> every academic channel — Tick History, Tick Data LLC, DataMine — forbids redistribution. If a free
> full-history intraday CME dataset existed legitimately, the literature would cite it constantly.
> Its absence is itself evidence.**

The search is therefore best read not as "did we miss something" but as **"does the licensing regime
have a gap"** — and the answer is that it has exactly one: **a licensed distributor's promotional
credit, priced per byte, against a schema small enough that 16 years costs $30.**

---

## 9. Recommendation

1. **Take the Databento credit.** ES/NQ/RTY/YM, `ohlcv-1m`, `stype_in="continuous"`,
   `batch.submit_job`. **$30 of $125.** Confirm the unit price first with `list_unit_prices`.
2. **Pull CME BTC futures 2017-12-17 → 2026-05-28** in the same job — a genuine Globex contract on the
   ES session template, for well under $1.
3. **Pull one instrument-month of Dukascopy `USA500.IDX/USD` free** and check its basis against the
   real ES series. **That single test calibrates the free cross-check for everything after.**
4. **Build the cache gitignored**, with a committed re-fetch script and meta. **Do not commit bars.**
5. **Acceptance-test the roll** against §6 before any study reads the fixture.
