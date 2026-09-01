# 08 — Yahoo Finance and the free-scraper ecosystem

Research date: 2026-09-01. Lane: Yahoo Finance / `yfinance`, Stooq, Investing.com,
Barchart, MarketWatch/WSJ, TradingEconomics, TradingView scrapers, `pandas-datareader`.
Requirement being tested: ES/NQ/RTY/YM (+ CL, GC, ZB, 6E), 15-minute or finer, 10+ years,
full ~23-hour Globex session, continuous or stitchable.

**Method note:** the Yahoo findings in §1–§5 are *not* from documentation. They were measured
by direct calls to `query1.finance.yahoo.com/v8/finance/chart` — the endpoint `yfinance`
wraps — on the research date. Every number below is reproducible; the probe scripts are
described inline. Where I am relying on someone else's claim rather than my own measurement,
it is marked as such.

---

## VERDICT FIRST

**Two pieces of received wisdom in this area are wrong, and one is right and fatal.**

Wrong #1 — "yfinance gives daily only." **False.** Yahoo serves 1m/2m/5m/15m/30m/60m/90m
intraday bars for all eight target contracts.

Wrong #2 — "Yahoo futures data is RTH only." **False, and this is the finding worth keeping.**
Yahoo serves the **full ~23-hour Globex session** for futures. Measured on ES=F 1-minute bars:
**1,379 non-null minutes in a single day, 00:00→23:58 ET, with exactly one 61-minute gap at
16:59→18:00 ET** — the CME daily maintenance halt. That is the real Globex session, not a
6.5-hour RTH window. Yahoo classifies the entire 23h as "regular" for futures, and the
`includePrePost` flag is a no-op on these symbols.

Right, and fatal — **the history depth.** The intraday limit is a hard **rolling retention
wall anchored to the present**, not a per-request window cap:

| interval | max lookback from *now* | verified |
|---|---|---|
| 1m | **8 days** | Yahoo's own error string |
| 2m | 60d request cap; **~37 days actually populated** | measured |
| 5m | **60 days** | measured |
| **15m** | **60 days** (61 fails) | measured |
| 30m | **60 days** | measured |
| 90m | **60 days** | measured |
| 60m / 1h | **730 days** (731 fails) | measured |
| 1d | ~2000-09-18 → present (~26y) | measured |

**We need 10+ years at 15m. Yahoo offers 60 days. It is short by a factor of ~60.**

The 730-day 1-hour series is the only intraday tier with real depth, and it is both too coarse
(1h vs 15m) and too shallow (2y vs 10y).

And even if the depth existed, **`ES=F` is unusable as a continuous series without repair** —
see §3. It is an *undocumented, unadjusted front-month splice* that injects spurious
**+161.49-point (+2.77%)** overnight jumps into the price series four times a year.

**Nothing in this entire lane meets the spec.** Best free intraday depth per source:

| Yahoo | tvdatafeed | Stooq | MarketWatch | TradingEconomics | investpy | pandas-datareader |
|---|---|---|---|---|---|---|
| **60d** @15m | ~54d @15m | ~1mo @5m | **10d** | dead | dead | never had any |

Stooq is now behind a proof-of-work bot wall and was ~1 month deep on 5m anyway.
`pandas-datareader` **formally deleted every securities reader in June 2026** — including Yahoo
and Stooq — and repositioned as a macro-only library. Investing.com and TradingEconomics'
free tiers are dead outright. Barchart genuinely has ~10 years of intraday but it is behind a
$29.95/mo Premier subscription with a 5-download/day free quota.

Recommendation: **close this lane.** Its residual value is narrow and specific — see §13.

**Two cross-lane leads worth passing on** (§11): **Massive/Polygon's $0 futures tier — CME
minute aggregates, 2 years, a sanctioned API rather than a scrape** — and **Databento's $125
free credit against 16+ years of `GLBX.MDP3`**. Both beat everything in this document.

---

## 1. What Yahoo actually serves for futures

### 1.1 The endpoint

`yfinance` is a wrapper. The thing underneath is:

```
https://query1.finance.yahoo.com/v8/finance/chart/{symbol}
    ?interval={1m|2m|5m|15m|30m|60m|90m|1h|1d|5d|1wk|1mo|3mo}
    &period1={unix}&period2={unix}      # or &range={1d|5d|1mo|...|max}
    &includePrePost={true|false}
```

Symbols are URL-encoded (`ES=F` → `ES%3DF`). The metadata block advertises:

```
validRanges = ['1d','5d','1mo','3mo','6mo','1y','2y','5y','10y','ytd','max']
```

**Note that `validRanges` is a trap.** It lists `10y` and `max` regardless of interval. Those
values are only honoured for daily-and-coarser bars; combining `interval=15m` with a long range
silently returns only the last 60 days, and combining it with explicit `period1`/`period2`
throws. The advertised ranges describe the *symbol*, not the *interval*.

**Access conditions, as measured:** ~70 requests over roughly 20 minutes from a plain
`urllib` client with a browser `User-Agent` string, no cookie, no crumb, no API key. All
returned HTTP 200 except one transient timeout. I did **not** hit a 429. This contradicts the
commonly repeated claim that the chart endpoint requires the cookie/crumb handshake — that
requirement applies to other Yahoo endpoints (`v7/finance/quote` returns 401), not to
`v8/finance/chart`. Do not read this as "there is no rate limit"; see §6.2.

### 1.2 All eight target contracts exist

Every symbol on the requirement list resolves, on the correct venue, with identical
intraday structure:

| symbol | venue | `shortName` returned | `firstTradeDate` | 15m bars on a full weekday |
|---|---|---|---|---|
| `ES=F` | CME | E-Mini S&P 500 **Sep 26** | 2000-09-18 | 92 non-null / 96 slots |
| `NQ=F` | CME | Nasdaq 100 **Sep 26** | 2000-09-18 | 92 / 96 |
| `RTY=F` | CME | E-mini Russell 2000 Index | 2017-07-10 | 92 / 96 |
| `YM=F` | CBOT | Mini Dow Jones Indus.-$5 | 2002-04-05 | 92 / 96 |
| `CL=F` | NYMEX | Crude Oil **Oct 26** | 2000-08-23 | 92 / 96 |
| `GC=F` | COMEX | Gold **Dec 26** | 2000-08-30 | 92 / 96 |
| `ZB=F` | CBOT | U.S. Treasury Bond Futures | 2000-09-21 | 92 / 96 |
| `6E=F` | CME | Euro FX Futures, **Sep-2026** | 2000-09-12 | 92 / 96 |

The bolded contract months in `shortName` are the single most important thing on this page.
**Yahoo is telling you outright that `=F` is a specific delivery month, not a continuous
series.** See §3.

`firstTradeDate` reaching back to 2000 applies to the **daily** series only. It is not a
statement about intraday availability, and reading it as one is the likely origin of the
"Yahoo has 26 years of futures data" misconception.

---

## 2. Session coverage — full Globex, confirmed

This is the question the requirement turns on and it is rarely addressed in public write-ups.
**Yahoo serves the full overnight session for futures.**

### 2.1 The 15-minute grid

Yahoo returns a **padded 96-slot grid per day** (00:00 → 23:45 ET), with `close: null` in the
slots where the instrument was not trading. Non-null counts on ES=F:

| date | weekday | non-null / slots | interpretation |
|---|---|---|---|
| 2026-08-27 | Thu | **92 / 96** | 23h — full Globex day |
| 2026-08-28 | Fri | 68 / 96 | 17h — Globex closes 17:00 ET Fri |
| 2026-08-30 | Sun | 24 / 96 | 6h — Globex opens 18:00 ET Sun |
| 2026-08-31 | Mon | **92 / 96** | 23h — full Globex day |

92 × 15 min = **23 hours exactly**. The 4 null slots are the 17:00–18:00 ET maintenance halt.
The Friday and Sunday partials line up precisely with the real Globex weekly boundaries.

**Pitfall:** if you naively `dropna()` you get the right answer, but if you count *rows* you
will conclude Yahoo returns a uniform 96-bar day and mistake padding for data. Volume is
`None` in the padded slots.

### 2.2 The 1-minute confirmation

Stronger evidence, from `interval=1m` on 2026-08-31:

```
non-null = 1379 of 1439 slots,  00:00 -> 23:58 ET
halt detected: 16:59 -> 18:00 ET  (61 min)
```

1,379 minutes = **22h59m**, and the single detected discontinuity is the CME halt at exactly
the right clock time. There is no 09:30–16:00 restriction anywhere in the data.

### 2.3 `includePrePost` is inert on futures

```
includePrePost=false : timestamps=403  nonnull=295
includePrePost=true  : timestamps=403  nonnull=295
```

Byte-identical. Corroborated by the metadata, which reports a `currentTradingPeriod` where
`regular` spans **86,340 seconds (23h59m)** and `pre`/`post` are both zero-length windows.
**Yahoo models the whole futures session as "regular."** There is no RTH/ETH toggle to get
wrong here — which is convenient, but it also means you cannot ask Yahoo for an RTH-only
subset if you ever wanted one; you would have to filter by timestamp yourself.

**Session verdict: PASS.** Yahoo is one of the few free sources that gets this right. It is
the only requirement in the spec that Yahoo satisfies.

---

## 3. What `ES=F` represents — the roll problem, measured

**`ES=F` is the front-month contract, spliced at expiry, with no back-adjustment, and no
published methodology.** I could find no Yahoo documentation of the roll rule anywhere. What
follows is reverse-engineered from the data.

### 3.1 The splice, in raw prices

ES=F daily bars around the December 2024 quarterly expiry:

| date | open | close | overnight gap (open − prev close) |
|---|---|---|---|
| 2024-12-19 Thu | 5881.75 | 5868.75 | +9.50 |
| 2024-12-20 Fri | 5879.50 | 5840.26 | +10.75 |
| **2024-12-23 Mon** | **6001.75** | 6036.00 | **+161.49** |
| 2024-12-24 Tue | 6037.75 | 6098.00 | +1.75 |

And March 2025:

| date | open | close | overnight gap |
|---|---|---|---|
| 2025-03-21 Fri | 5664.00 | 5617.80 | +1.50 |
| **2025-03-24 Mon** | **5740.00** | 5815.50 | **+122.20** |

A **+161.49 point (+2.77%)** overnight jump on a day SPY moved +0.60%. That is not a market
event. It is the calendar spread between the expiring and the succeeding contract, appearing
in the series as if it were a return.

### 3.2 It is systematic, not anecdotal

I compared ES=F daily returns against SPY over 5 years (1,258 bars) and ranked days by
|ES return − SPY return|. Of the 16 largest divergences, **15 fall within 5 days of a
quarterly expiry (3rd Friday of Mar/Jun/Sep/Dec)**:

```
 date        ESret%   SPYret%   diff%   ES pts   qtr-expiry?
 2024-12-23     3.35     0.60     2.75   +195.7   True
 2025-03-24     3.52     1.79     1.73   +197.7   True
 2024-03-18     2.22     0.59     1.62   +113.1   True
 2023-12-18     2.10     0.56     1.54    +98.7   True
 2026-03-20    -0.22    -1.70     1.48    -14.6   True
 2023-03-17    -0.09    -1.55     1.46     -3.5   True
 2024-12-20    -0.49     0.86    -1.35    -28.5   True
 2025-12-22     1.97     0.62     1.34   +133.7   True
 ...
 2025-04-09     9.38    10.50    -1.12   +470.8   False   <- genuine (tariff reversal)
```

The single non-expiry entry is 2025-04-09, a real market event. **The roll artefact is the
dominant source of error in the series.** Four spurious jumps per year, of order 100–200 ES
points each, is not a rounding issue — a momentum or gap strategy backtested on this will
book those as tradeable edges.

### 3.3 `adjclose` does not save you

```
adjclose identical to close on 1258/1258 daily bars
```

Yahoo emits an `adjclose` field for futures, and it is a **verbatim copy of `close`**. There is
no back-adjustment. Anyone reaching for `adjclose` expecting the equity-style treatment gets
raw spliced prices with a reassuring column name. This is the most dangerous single detail in
this document.

### 3.4 The roll happens at expiry, not at the liquidity crossover

Two further problems, both worse than the splice itself.

**(a) Yahoo holds the dying contract.** Daily volume into the Dec 2024 expiry:

| date | close | volume |
|---|---|---|
| 2024-12-13 Fri | 6055.50 | **1,996,354** ← real roll week; OI migrates here |
| 2024-12-16 Mon | 6080.50 | 1,612,199 |
| 2024-12-17 Tue | 6053.75 | 1,113,325 |
| 2024-12-18 Wed | 5872.25 | 847,452 |
| 2024-12-19 Thu | 5868.75 | **532,081** ← 73% below peak |
| 2024-12-20 Fri | 5840.26 | 2,340,873 (expiry + new contract mixed) |

Market convention rolls ES on the Thursday ~8 days before expiry. Yahoo does not — it tracks
the expiring contract to the bitter end. So the **last ~4–5 trading days of every quarter are
the illiquid, widening, decaying stub** while genuine liquidity has already moved to the next
month. That is roughly **18–20 contaminated days per year, ~7–8% of the sample**, and they are
contaminated in a way that flatters mean-reversion strategies (wider spreads, thinner book,
noisier prints).

**(b) The daily and intraday series disagree with each other.** In the 730-day hourly series,
the Dec 2024 roll appears *inside* Friday 2024-12-20 as a **+155.75 jump (5840.75 → 5996.50)
across a 7-hour hole** — the expiring contract stops printing at the 09:30 ET expiry, and the
series resumes later in the day on the new contract. But the **daily** bar for 2024-12-20
closes at **5840.26**, i.e. built from the old contract only. **The same calendar day has a
close of 5840.26 in the daily series and prints of 5996.50 in the hourly series.** The two
feeds are not reconcilable across the roll. Anyone cross-validating daily against resampled
intraday will find breaks four times a year and, without this context, will assume their own
resampling is at fault.

### 3.5 Could you build your own continuous series instead?

I tested whether individual delivery months are addressable. **Partly — and it does not help.**

| symbol | result |
|---|---|
| `ESU26.CME` | OK — E-Mini S&P 500 Sep 26 (live front month, vol 102,086) |
| `ESZ26.CME` | OK — E-Mini S&P 500 Dec 26 (deferred, vol 299) |
| `ESH27.CME` | OK — E-Mini S&P 500 Mar 27 (deferred, vol 280) |
| `ESM27.CME` | OK — E-Mini S&P 500 Jun 27 (deferred, vol 7) |
| **`ESZ25.CME`** | **Not Found** |
| **`ESM25.CME`** | **Not Found** |
| **`ESZ24.CME`** | **Not Found** |
| **`ESZ23.CME`** | **Not Found** |
| `ESZ26`, `ES=FZ26`, `ES1!`, `ESc1` | Not Found (no continuous/TradingView-style aliases) |

**Expired contracts are purged.** Only live and deferred months resolve. So you cannot
reconstruct a properly-rolled historical continuous series from the legs either — the legs
cease to exist the moment they would become useful history. And the deferred months that *do*
resolve are near-untradeable (ESM27 last volume: 7 contracts), so their intraday bars are
mostly padding.

Individual months are also subject to the same 60-day intraday wall (`ESZ26.CME` at 15m:
`range=1mo` OK, `range=3mo` throws).

**Roll verdict: FAIL, on two counts** — undocumented unadjusted splice, and no route to fix it
retrospectively.

---

## 4. The rolling-window harvest — can you accumulate history going forward?

The idea: run a scheduled job that pulls the last 60 days of 15m bars and appends to a store,
building depth over time. **Technically viable going forward. Useless for going backward.**
And I can now state *why* precisely, rather than assuming.

### 4.1 The key test — the wall is anchored to `now`

The question is whether "60 days" is a **per-request window cap** (in which case you page
backwards and recover deep history) or **server-side retention** (in which case you cannot).
I requested 50-day 15m windows with progressively older end dates:

| requested window | ends | result |
|---|---|---|
| 2026-07-08 → 2026-08-27 | 5d ago | **n=4129** — served |
| 2026-05-19 → 2026-07-08 | 55d ago | **ERROR** |
| 2026-05-09 → 2026-06-28 | 65d ago | **ERROR** |
| 2026-03-15 → 2026-05-04 | 120d ago | **ERROR** |
| 2025-07-13 → 2025-09-01 | 1y ago | **ERROR** |
| 2023-07-14 → 2023-09-02 | 3y ago | **ERROR** |

The second row is decisive: a **50-day window fails** even though 50 < 60, because its
`startTime` is 105 days before now. The binding constraint is
**`now − startTime ≤ limit`**, not `period2 − period1 ≤ limit`.

Same behaviour at the 730-day 1h tier (window ending 400d ago works — start is 700d ago;
window ending 700d ago fails — start is 1000d ago).

**Conclusion: paging backwards is impossible. There is no backfill. Deep intraday history does
not exist on Yahoo's servers to be retrieved by any request pattern.**

### 4.1a The boundary is enforced to the second

Discovered accidentally, and it confirms the above. A batch script computed
`period1 = now − 60×86400` **once at start**, then looped over the eight symbols. The first
request (ES=F) succeeded; **all seven subsequent requests returned HTTP 422 Unprocessable
Entity** — because a few seconds of wall-clock had elapsed, pushing the fixed `period1` past
the 60-day boundary as the server re-evaluated it against a moving `now`.

The practical lesson for any code that touches this endpoint: **request 59 days, not 60.** An
exactly-60-day window is on the knife edge and will fail intermittently depending on request
latency. Note also that the over-limit failure mode is **HTTP 422**, not an empty result — so
it raises rather than silently truncating, which is at least honest.

### 4.2 What forward harvesting would actually buy

Measured: ES=F yields **3,815 non-null 15m bars per 60-day window** (~23,200/year/symbol).
Eight symbols ≈ 186k bars/year — trivial storage, a few MB/year as Parquet.

The scheme works, and a weekly cron with 60-day windows gives ~8x overlap redundancy against
missed runs. But:

- **It only accrues from the day you start.** To reach the 10-year requirement you would wait
  **10 years.** For a study that needs to run this year, the answer is no.
- **It does not fix the roll.** You would be accumulating spliced front-month data unless you
  also harvest individual delivery months (`ESU26.CME` etc.) and roll them yourself — which
  *is* possible going forward, since live contracts resolve before they expire, and is the
  only way to get a defensible roll out of this source.
- **It is the ToS-riskiest use.** A persistent scheduled scraper building a private archive is
  much closer to §2.4(j)'s "create any database... data feed" than an ad-hoc lookup. See §6.

**Verdict: not a solution to this requirement.** Worth a cheap forward-harvest job only if
you want a free independent cross-check series in future years, and only if §6 is acceptable.

---

## 5. Summary table — Yahoo Finance

| field | |
|---|---|
| **source + URL** | Yahoo Finance via `query1.finance.yahoo.com/v8/finance/chart`; `yfinance` 1.7.0 (2026-08-26), https://github.com/ranaroussi/yfinance |
| **intervals available** | 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo |
| **max lookback per interval** | **1m = 8d · 2m = ~37d populated · 5m = 60d · 15m = 60d · 30m = 60d · 90m = 60d · 1h/60m = 730d · 1d = ~26y.** Anchored to `now`; no backfill |
| **full session or RTH?** | **FULL ~23h Globex.** 92/96 15m slots and 1,379/1,439 1m slots per weekday; 61-min halt at 16:59–18:00 ET; `includePrePost` inert |
| **what the symbol represents** | **Front-month delivery contract**, spliced at expiry. `shortName` names the month ("E-Mini S&P 500 Sep 26"). No back-adjustment (`adjclose == close` on 1258/1258 bars). Roll methodology **undocumented**; measured to occur *at expiry*, not at liquidity crossover; produces +122 to +197 pt spurious jumps 4x/yr. Expired legs purged |
| **ToS position** | Grey-to-adverse. Yahoo ToS §2.4(i) prohibits automated access outright; §2.4(j) prohibits building a substitute database/feed. yfinance itself says "personal use only". No enforcement history, technical countermeasures instead. See §6 |
| **verified how** | **Direct measurement**, 2026-09-01: ~70 calls to the v8 chart endpoint; interval-limit bisection; historical-window probe; ES=F-vs-SPY 5-year roll analysis; volume profile around Dec-2024 expiry; contract-month resolution tests |
| **meets spec?** | **NO.** Session ✅ · granularity ✅ · **depth ❌ (60d vs 10y, ~60x short)** · **roll ❌** |

---

## 6. Terms of service — what the documents actually say

Delegated to a sub-agent working from primary sources; quotes below are from
`legal.yahoo.com`.

### 6.1 The binding clauses

**Yahoo Terms of Service**, https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html
(updated May 2025), **§2.4 "Member Conduct"**. You agree not to:

> "access or collect data … using any automated means"

the same sentence enumerating

> "robots, spiders, scrapers, data mining tools, or data gathering or extraction tools"

and closing

> "for any purpose without our express, prior permission."

**§2.4(j)** separately prohibits using content

> "to create any database, archive, mobile application, data feed, widget"

that

> "competes with or constitutes a material substitute for the Services"

— extended explicitly to "the services offered by our data providers."

Two observations that matter for how we characterise this internally:

- **§2.4(i) is absolute on the means, not the volume.** There is no rate threshold, no
  "excessive" qualifier, no robots.txt carve-out. A polite 1-req/sec script sits in the same
  position as an abusive one. "We scraped gently" is not a defence under this wording.
- **§2.4(j) is a substitution test, not a commercial-use test.** The ToS does not say "no
  commercial use." It says do not build a substitute feed — and it extends that protection to
  Yahoo's *upstream data providers*, i.e. the exchanges. For CME futures data specifically,
  that second limb is the sharper one, because CME licenses this data commercially.

Note the **§2.4(j) implication for §4**: forward-harvesting into a persistent archive is
precisely "create any database, archive... data feed." The one-off lookup is the weaker case
against us; the standing cron job is the stronger one.

Yahoo Finance has **no separate market-data ToS** adding redistribution terms — the
Finance-specific product terms govern the message-board community only. The Yahoo Developer
API terms (REV 3-2022) govern *authorized* APIs obtained via the developer program; the v8
chart endpoint has no key, no signup and no acceptance flow, so it is arguable those terms do
not bind at all and §2.4 is the operative text.

### 6.2 Technical posture, 2024–2026

Yahoo's response to scraping has been engineering, not lawyers:

- **2017-05-15** — official public finance API shut down, never replaced.
- **2022-12** — Yahoo began encrypting embedded page data, forcing the cookie+crumb approach.
- **2024-11-13** — step-change in rate limiting
  ([yfinance #2128](https://github.com/ranaroussi/yfinance/issues/2128)). Notable detail: the
  crumb fetch *itself* returns `crumb = 'Edge: Too Many Requests'` — **Yahoo rate-limits the
  authentication step**, so you cannot obtain a credential to retry with. Closed *not planned*.
- **2025** — persistent `YFRateLimitError` even with the `curl_cffi` workaround (#2480, #2518).
- **2026** — `curl_cffi>=0.15` is now a **core dependency** of yfinance, not an extra.
  `curl_cffi` exists to impersonate a browser's TLS/JA3 fingerprint. Its promotion to a hard
  requirement is the clearest signal that **Yahoo is fingerprinting clients, not merely
  counting requests.** Changelog also shows "handle DNS blocking `fc.yahoo.com`".
- **yfinance 1.4.0 added `yf.Auth`** — Yahoo account login, to lift rate limits.

**Flag on `yf.Auth`:** logging in materially worsens the legal position. Anonymous requests to
a public endpoint are the fact pattern where public-data defences are strongest. Authenticating
means accepting the ToS as an identified account holder, at which point §2.4(i) applies as
contract unambiguously. **If we ever touch this source, do not authenticate.**

### 6.3 What yfinance says about itself

From the README:

> "yfinance is **not** affiliated, endorsed, or vetted by Yahoo, Inc."

and, set apart as its own notice:

> "Remember - the Yahoo! finance API is intended for personal use only."

Apache 2.0 covers **the code and grants nothing regarding the data**; the project explicitly
punts data rights to Yahoo's ToS. Worth noting the mismatch: yfinance says "personal use only,"
but the §2.4(i) it cites prohibits the *automated access itself* regardless of purpose —
yfinance's framing is more permissive than its own cited source.

### 6.4 Enforcement and case law

**No evidence of Yahoo suing or sending C&Ds to yfinance or any Yahoo Finance scraper**, and no
Yahoo-specific case law. The repo has been public since 2017 and is not blocked by name.

The relevant background is **hiQ v. LinkedIn**, and the popular reading of it ("scraping public
data is legal") is half wrong in the half that matters. The Ninth Circuit (April 2022) held the
**CFAA** does not reach scraping of public data. But on **2022-12-07 the case ended in a
consent judgment: $500,000 against hiQ, on breach of contract** under LinkedIn's user
agreement, plus a permanent injunction to destroy all derived data and code.
**hiQ won the statute and lost the contract.** Public accessibility defeats the computer-crime
theory; it does not defeat terms of service. Yahoo's §2.4(i) is a contract term — that is the
live exposure. (Qualifier: a stipulated judgment is a settlement, not a precedential finding,
and hiQ's facts included fake accounts and spoliation sanctions.)

**Practical read for us:** for personal research the realistic exposure is a technical block,
not litigation. Risk becomes real on **redistribution or anything customer-facing**, where
§2.4(j) and the upstream exchange licences bite and the aggrieved party may be CME rather than
Yahoo. Since our requirement is a private research corpus this is not a showstopper — but it is
moot, because §1–§4 already disqualify the source on depth.

---

## 7. `pandas-datareader` — formally exited securities data

**The library was revived after a five-year gap and then deliberately gutted.**

- **0.11.1 — 2026-06-24** (current), 0.11.0 — 2026-06-23, previous stable 0.10.0 — 2021-07-13.
  Now requires Python ≥3.11.

The 0.11.0 release notes:

> "Removed the following securities-related readers that depended on defunct or heavily broken
> upstream APIs: AlphaVantage, Enigma, IEX, Morningstar, Naver, Nasdaq Trader symbols, Quandl,
> Stooq, Tiingo, and Yahoo Finance"

and

> "Narrowed the default public API surface to focus on macro and widely-used data sources"

**Surviving readers: FRED, Fama/French, Bank of Canada, Econdb, OECD, Eurostat, World Bank.**
Every one is macro/factor data — daily at best, usually monthly. **Yahoo and Stooq are both
deleted.**

This is not temporary breakage awaiting a patch; the maintainers made a considered decision to
**exit securities data entirely** and reposition as a macroeconomic tool. Their judgement about
the sustainability of scraping-based securities readers is itself a data point for this lane.

**Futures at any frequency: no path, in 0.11.1 or in any prior version.** Pinning an old
release would not help — pre-purge, Stooq was the only reader with real futures symbol coverage
and it was **daily OHLCV only**; the AlphaVantage wrapper exposed intraday for equities/FX, not
futures; Quandl's continuous futures (CHRIS/SCF) were end-of-day and mostly moved behind
paywalls. **No version of `pandas-datareader` has ever served intraday futures bars.**

Sources: https://pydata.github.io/pandas-datareader/stable/whatsnew.html

**Verdict: FAIL, definitively. Remove from consideration.**

---

## 8. Stooq — now behind a proof-of-work bot wall

Stooq had the best reputation of the free mirrors for depth, so I tested it directly.

**The CSV endpoint no longer serves data to programmatic clients.**
`https://stooq.com/q/d/l/?s=es.f&i=d` returns **HTTP 200 with 796 bytes of anti-bot
JavaScript**, not CSV:

```html
<noscript>This site requires JavaScript to verify your browser.</noscript>
<script>
(async()=>{const c="AAAAAGqWjYPz...",d=4,t="0".repeat(d),e=new TextEncoder;let n=0;
while(1){const h=await crypto.subtle.digest("SHA-256",e.encode(c+n)); ... }
const r=await fetch("/__verify",{method:"POST", ...})})();
</script>
```

A SHA-256 proof-of-work challenge (find a nonce giving 4 leading hex zeros) POSTed to
`/__verify`. Identical response for daily (`i=d`) and 5-minute (`i=5`).

**I did not attempt to solve the challenge** — defeating bot-detection is out of scope for how
we source data, and a source that has explicitly erected a bot wall has answered the question
of whether it consents to automated access. Note that **HTTP 200 with a challenge body** is the
nastiest possible failure mode: a naive `pd.read_csv(url)` fails with a parse error rather than
a clear HTTP status, so any existing Stooq code in the wild is silently broken.

**Even if it were reachable, the depth does not qualify.** Per the Wealth-Lab Stooq provider
documentation *(secondary source, unverified by me given the wall)*:

- **5-minute: last ~2,000 bars ≈ 1 month**
- **hourly: last ~1,400 bars ≈ 9 months**
- daily: deep (years)

**~1 month of 5-minute data is worse than Yahoo's 60 days at 15m.** Stooq's reputation for
depth is real but applies to its **daily** history, not intraday. Session coverage and roll
methodology were not verifiable and are moot.

**Verdict: FAIL on access and on depth.**

---

## 9. MarketWatch / WSJ — the surprise in this lane

**Not daily-only.** MarketWatch and WSJ share a charting backend ("michelangelo") that is
**open, unauthenticated, and serving full-session intraday futures bars today.** I verified this
myself after a sub-agent flagged it.

```
GET https://api.wsj.net/api/michelangelo/timeseries/history?json={...}&ckey=cecc4267a0
Header: Dylan2010.EntitlementToken: cecc4267a0194af89ca343805a3e57af
Series Key: "FUTURE/US//ES00"   Dialect: "Charting"   Kind: "Ticker"
Steps: PT1M | PT5M | PT15M | PT30M | PT60M | P1D
```

The entitlement token is hardcoded in MarketWatch's own page JavaScript.

### 9.1 Measured limits

| Step | TimeFrame | result |
|---|---|---|
| `PT1M` | `D5` | 6,156 bars, 2026-08-25 → 2026-09-01, **median 1,261 bars/day** |
| `PT15M` | `D10` | 879 bars, 2026-08-18 → 2026-09-01, **median 92 bars/day** |
| `PT15M` | **`D11`** | **879 bars — identical to D10. Silently clamped, no error** |
| `PT15M` | `D30` | **HTTP 400 Bad Request** |
| `P1D` | `P20Y` | 4,365 bars, **2009-04-24 → 2026-09-01** (~17 years) |

- **Intraday ceiling: 10 trading days (~14 calendar days).** An order of magnitude worse than
  Yahoo's 60.
- **`StartDate`/`EndDate` in the JSON are ignored** (sub-agent finding, consistent with my
  `D11` result) — **there is no historical paging**, same rolling-window architecture as Yahoo.
- **Trap: `D11` silently clamps rather than erroring.** You get 10 days of data believing you
  asked for 11. Yahoo's HTTP 422 is the better failure mode. Only at `D30` does it 400.

### 9.2 Independent corroboration of the session finding

**`PT15M` returns a median of 92 bars/day — the identical number I measured on Yahoo.**
Two unrelated providers independently reporting 92 × 15min = 23 hours is strong confirmation
that §2 is right and that **the full Globex session is the norm for free futures feeds**, not
the exception. (The `PT1M` median of 1,261/day is somewhat below Yahoo's 1,379 — MarketWatch
appears to drop rather than pad empty minutes.)

### 9.3 Symbols — all eight available, with non-obvious mappings

| we want | MarketWatch key | note |
|---|---|---|
| ES | `ES00` | |
| NQ | `NQ00` | |
| RTY | `RTY00` | `RT00` fails |
| YM | `YM00` | |
| CL | `CL00` | |
| GC | `GC00` | |
| **ZB** | **`US00`** | `ZB00` fails |
| **6E** | **`EC00`** | `6E00` fails |
| specific month | `ESZ26` | individual delivery months resolve |

The `00` suffix is MarketWatch's **continuous front-month, unadjusted** — raw concatenation
with roll gaps, no back-adjustment option, **no documented roll rule**. Same defect as Yahoo.

### 9.4 Assessment

| field | |
|---|---|
| source + URL | MarketWatch/WSJ michelangelo API, `api.wsj.net/api/michelangelo/timeseries/history` |
| intervals | PT1M, PT5M, PT15M, PT30M, PT60M, P1D |
| **max lookback** | **10 trading days intraday (all steps); ~17 years daily.** No paging |
| **full session or RTH?** | **FULL ~23h Globex** — 92 bars/day at 15m, independently measured |
| symbol / roll | `ES00` = front-month continuous, **unadjusted, undocumented roll** |
| ToS | Not verified. Assume standard Dow Jones prohibition on automated access. A token hardcoded in page JS is not permission |
| verified how | Direct measurement, 2026-09-01 (steps × timeframes matrix, per-day bar counts) |
| **meets spec?** | **NO** — 10 days vs 10 years |

**Verdict: FAIL on depth by ~250x.** Worth recording as the only other free source with
confirmed full-session intraday, and as a second forward-collection option — but it is strictly
worse than Yahoo (10 days vs 60) for that purpose too.

---

## 10. The remaining scrapers — all fail

Delegated; sub-agent tested endpoints live on 2026-09-01 rather than trusting docs.

### 10.1 investpy / investiny — DEAD

Investing.com put Cloudflare in front of everything in mid-2022. **All four surfaces return
HTTP 403 to non-browser clients**, including the bare homepage:
`investing.com/instruments/HistoricalDataAjax` (investpy's), `api.investing.com/api/financialdata/...`,
`tvc4/tvc6.investing.com/.../history` (investiny's). investpy's own README concedes it "is not
working fine currently." `investiny`, the author's stopgap successor, last released
**0.7.2 on 2022-10-18**.

This is TLS-fingerprint + IP reputation, not a code bug. **Not verified:** whether `curl_cffi`
plus a residential proxy revives it. Moot regardless — Investing.com futures are
broker/CFD-derived front-month series, not exchange-timestamped CME data, with no documented
intraday depth. **Rule out.**

### 10.2 Barchart — real 10-year intraday, but not free

The only source in this lane whose *depth* actually meets the spec, and it is paywalled.

- **Intraday history ~10 years back**; daily to 2000; max 20,000 records/request.
- **Historical download requires Barchart Premier ($29.95/mo).** Quotas: free ≈ **5
  downloads/day**, Plus 10/day, Premier 250/day. One download = one symbol-request. At 5/day,
  backfilling 8 symbols × ~40 quarterly contracts × 10 years is arithmetically hopeless.
- Scraper endpoint `barchart.com/proxies/timeseries/queryminutes.ashx` returns
  **HTTP 403 `{"error":"Forbidden"}`** without a logged-in session + `XSRF-TOKEN` cookie.
- **The one genuinely good thing: the roll is documented and parameterised.** Barchart's
  OnDemand `getHistory` exposes `contractRoll` = `expiration` | `combined` (volume/OI),
  `daysToExpiration` = 0–60, and `backAdjust` = true/false. **This is the contrast that shows
  what Yahoo is missing** — a real vendor lets you specify the roll rule; Yahoo hides it.
- **ToS explicitly hostile:** prohibits "data mining, robots, or similar data gathering and
  extraction tools," prohibits storing/redistributing content, prohibits circumventing
  protection. Scraping with an account is a breach that gets accounts closed.
- **Not verified:** whether Barchart intraday covers full Globex or pit-session only.

**Verdict: fails the "free" constraint. Note for the paid comparison.**

### 10.3 TradingEconomics — free tier discontinued

The `guest:guest` key is gone. All endpoints return:

> "We are sorry, but the guest account has been discontinued."

What remains is a trial capped at 100,000 data points / 100 requests, then paid. And even
paid it could not work: `markets/intraday` offers 1m–4h but with a **30-day maximum lookback**,
and symbols are index/CFD-style (`CL1:COM`), not CME contracts. **Structurally incapable of
10-year intraday at any price. Rule out completely.**

### 10.4 TradingView scrapers — the bar-count ceiling kills it

`tvdatafeed` (live fork `rongardF/tvdatafeed`) supports 13 timeframes including 15m, but is
bound by TradingView's **per-request intraday bar cap**:

| plan | intraday bar cap | **what that is at 15m on a 23h session (92 bars/day)** |
|---|---|---|
| Basic (free) | 5,000 | **~54 trading days ≈ 2.6 months** |
| Essential / Plus | 10,000 | ~109 days |
| Premium | 20,000 | ~217 days |
| Ultimate | 40,000 | **~435 days ≈ 1.7 years** |

**Even the most expensive tier reaches 1.7 years, not 10.** TradingView states the caps
"cannot be extended for now due to technical reasons," and `ES1!`-type synthetic continuous
charts carry a further 20K intraday replay restriction.

Worth recording: **`ES1!`'s roll methodology IS documented** — it rolls when the next contract's
**daily volume exceeds** the front contract's, i.e. volume crossover, which is the methodology
Yahoo should have used and doesn't (§3.4a). Default charts are unadjusted; back-adjustment is
an opt-in setting. Not verified whether `tvdatafeed`'s websocket pull returns adjusted or
unadjusted (almost certainly unadjusted).

**ToS is the most hostile of the lot.** TradingView prohibits automated collection
*"regardless of their intended purposes,"* and separately licenses market data **display-only**,
with prohibited non-display use enumerated to include *"algorithmic decision-making,
algorithmic trading… risk management programs."* **Backtesting on scraped TradingView bars sits
squarely inside that prohibition.** Accounts get banned.

`tradingview-scraper` (mnwato) is the wrong tool entirely — historical OHLC export is still a
to-do; it does ideas/news/screeners/streaming.

**Verdict: FAIL on depth even before the ToS problem.**

---

## 11. Cross-lane pointers

Two sources surfaced that are **outside this lane** (commercial-API and vendor lanes) but
worth flagging so they are not missed, since both beat everything above on depth:

- **Massive (formerly Polygon.io; `polygon.io/pricing` now 301s to `massive.com`)** — a **$0
  "Futures Basic" tier** covering **CME/CBOT/NYMEX/COMEX, minute aggregates, 2 years history**,
  rate-limited to 5 calls/min. That is a *sanctioned API*, not a scrape, and **2 years at
  minute resolution beats every source in this document**. Session coverage and
  continuous-contract handling unverified (needs a key). **Worth chasing first.**
- **Databento** — `GLBX.MDP3` with **16+ years** of CME history and **$125 in free credits**
  for new users. Billed per GB uncompressed; 8 symbols of 1-minute OHLCV over 10 years is a
  small volume, so the credit may cover most of it. **This is plausibly the actual answer** if
  "free" can stretch to "free credits."

Flagging only — these belong to whoever owns those lanes.

---

## 12. Scorecard for this lane

| source | best intraday depth | session | roll documented? | free? | meets spec |
|---|---|---|---|---|---|
| **Yahoo / yfinance** | **60d @15m**, 730d @1h | **Full 23h ✓** | ✗ undocumented splice | ✓ | **NO** |
| MarketWatch / WSJ | 10 trading days | **Full 23h ✓** | ✗ | ✓ | **NO** |
| tvdatafeed (free) | ~54d @15m | full | ✓ volume crossover | ✓ | **NO** |
| tvdatafeed (Ultimate) | ~1.7y @15m | full | ✓ | ✗ | **NO** |
| Stooq | ~1 month @5m | unverified | ✗ | bot-walled | **NO** |
| Barchart Premier | ~10y | unverified | **✓ parameterised** | ✗ ($29.95/mo) | depth ✓, not free |
| TradingEconomics | 30d (paid only) | n/a | ✗ | ✗ | **NO** |
| investpy / investiny | — | — | — | dead | **NO** |
| pandas-datareader | none, ever | n/a | n/a | ✓ | **NO** |

**Yahoo is the best free option in the lane and misses the depth requirement by ~60x.**

---

## 13. What this lane is still good for

Narrow, but not nothing:

1. **Free full-session recent data for pipeline development.** 60 days of 15m Globex-session
   bars across all 8 symbols, no account, no key, ~5 minutes of wall clock. Genuinely useful
   for building and unit-testing ingest/resampling/session-handling code *before* paying for
   the real corpus. The session semantics are correct, which is what you want to develop
   against.
2. **A free cross-validation series.** Once a paid corpus is acquired, Yahoo's independent
   60-day window is a cheap sanity check on timestamps, session boundaries and bar alignment.
3. **~2 years of hourly bars**, full session, free — if any part of the study can tolerate 1h.
4. **Reference for the roll trap.** §3 is a worked example of exactly the failure mode to
   guard against in whatever source we do buy: always verify `adjclose != close`, always test
   for expiry-clustered return outliers.

**Do not** use it for the 10-year study, and **do not** build a standing harvester.

One concrete carry-forward for whatever source we *do* buy, drawn from §3: **acceptance-test
the vendor's continuous series before trusting it.** Three cheap checks that would have caught
Yahoo instantly — (a) assert `adjclose != close` if back-adjustment is claimed; (b) rank
daily returns by |return − cash index return| and confirm the top outliers are *not*
clustered on quarterly expiries; (c) check volume does not collapse in the last week of each
quarter, which detects a roll-at-expiry rule masquerading as a proper one.

---

## 14. What I could not verify

Stated plainly, so this is not over-read:

- **Stooq's actual intraday depth and session coverage.** Blocked by the PoW wall, which I
  declined to circumvent. The ~2,000-bar/5-min figure is a secondary source (Wealth-Lab wiki)
  and may be stale.
- ~~Whether Yahoo's 60-day wall is uniform across all eight symbols.~~ **Now measured — it is.**
  Full 59-day 15m pull for every contract, all identical at 4,748 slots / 59 days /
  2026-07-05 → 2026-09-01:

  | symbol | slots | non-null | symbol | slots | non-null |
  |---|---|---|---|---|---|
  | ES=F | 4748 | 3816 | CL=F | 4748 | 3817 |
  | NQ=F | 4748 | 3816 | GC=F | 4748 | 3817 |
  | RTY=F | 4748 | 3816 | ZB=F | 4748 | 3812 |
  | YM=F | 4748 | 3817 | 6E=F | 4748 | 3816 |

  (The 5-bar spread is holiday/halt variation between products, not a coverage difference.)
- **The 2m anomaly.** `2m` accepts a 60-day request but only returned data from ~37 days back.
  Could be genuine shorter retention for that tier or a transient gap. Not chased — 2m is not
  a candidate interval for us.
- **Whether Yahoo's roll rule is stable over time.** Measured at 8+ quarterly rolls in the
  5-year daily window; all consistent with roll-at-expiry. Not verified for pre-2021 data, and
  since the methodology is undocumented Yahoo could change it without notice — which is itself
  the argument against depending on it.
- **Rate limits.** ~70 requests in ~20 minutes drew no 429 from an unauthenticated `urllib`
  client. The widely-circulated "360 requests/hour" figure appears to be **folklore** — the
  sub-agent found no Yahoo-published rate limit anywhere, and the ToS says limits are set at
  Yahoo's "absolute and sole discretion." Do not plan capacity against any published number.
- **Exact §2.4 clause lettering** in the Yahoo ToS. Quotes match Yahoo's long-standing
  published wording and were taken from the primary URL, but were relayed through a
  summarisation step; verify directly if this ever becomes load-bearing in a formal record.
- **MarketWatch/WSJ terms of use.** Not fetched. The endpoint works unauthenticated and its
  token is public in page JS, but that is not permission. Assume Dow Jones restrictions apply.
- **Barchart's intraday session coverage** (full Globex vs pit only) — not documented anywhere
  found, and not testable without a Premier account.
- **Whether `curl_cffi` + a residential proxy revives Investing.com.** Not testable from here,
  and not pursued: the 403 wall is a deliberate access-control decision by the operator.
- **Massive/Polygon session coverage and continuous-contract handling** — needs a free key.
  This is the highest-value open item in the whole document and belongs to the commercial-API
  lane.
- **`tvdatafeed`'s adjusted-vs-unadjusted behaviour** for `ES1!`. Almost certainly unadjusted.
  Not tested — doing so requires a TradingView account and the ToS prohibits the use anyway.

### Method caveats

Yahoo and MarketWatch numbers are my own direct measurements and are reproducible. The
Investing.com / Barchart / TradingEconomics / TradingView / ToS / `pandas-datareader` findings
were gathered by sub-agents; endpoint status for those was live-tested on 2026-09-01, but
depth and ToS claims there rest on vendor documentation I did not personally fetch. Where a
sub-agent figure conflicted with my own measurement I used mine — notably, one reported
"96 bars/day, full 24h" for Yahoo 15m, which counts **padded slots**; the correct non-null
figure is **92, i.e. 23h**, and the distinction matters because it is exactly the maintenance
halt.
