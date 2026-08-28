# D252 — The dead-inclusive US single-name universe

**Status:** Data acquisition — fixture built and committed. **No strategy was run, no cell scored, no rule proposed.**
**Date:** 2026-08-28
**Area:** Data layer

---

## What this is

A US single-name equity fixture built for **short-side** research, with **delisted companies
deliberately included**. It is data and nothing else: `scripts/fetch_short_universe.py` has no
strategy in it, `--build` computes no return, and nothing in this record says whether anything
works.

Everything downstream of the one manual network fetch is offline and deterministic — the same
contract every fetcher in this repo carries.

---

## Why survivorship bias is the whole design and not a caveat

Every equity fixture in this programme so far has been built from **currently-listed** instruments.
For a long book that is a known, bounded flattery. For a short book it is fatal, because the
companies that died are exactly where a short book earns.

This programme has already measured that, on its own data. [D141–D144](D141-one-configuration-across-the-cross-section.md),
crypto:

> the strategy's value is concentrated in the assets that died — **67% of the wrecks beat matched
> exposure against 45% of the survivors**

A universe of survivors does not weaken a short-side measurement; it removes the thing being
measured. So the delisted cohort is fetched on purpose, counted in the meta, asserted in the tests,
and **`--build` refuses outright** to write a fixture whose dead share falls below 15%.

The refusal is not decorative. It is the one guard that makes the difference between this fixture
and a quietly biased one, and it is easier to write while nobody wants a number.

---

## What the provider actually does — measured before anything was designed

`LISTING_STATUS` documentation is two sentences in a spreadsheet add-in reference. Four probe calls
settled it before ~3,400 were spent, the same discipline
[`docs/alpha_vantage_api.md`](../alpha_vantage_api.md) used on the intraday volume question.

| question | answer | evidence |
|---|---|---|
| Does `state=delisted` work on this tier? | **yes** | 9,449 rows, 7 columns |
| Is the `date` parameter a snapshot or a filter? | **cumulative-as-of** | `delisted@2012-06-29` = 183 rows, `@2020-06-30` = 4,099, both strict subsets of the undated call |
| Do dead tickers serve bars? | **yes, terminating at the delisting date** | AABA 5,016 bars → 2019-11-06; TWTR 2,260 → 2022-10-28; AAI 2,567 → 2011-11-30 |
| Do dead tickers serve corporate actions? | **yes** | AABA: 3 splits, 1 dividend (the $51.50 Altaba distribution) |

**The undated `state=delisted` call is already cumulative**, so the per-year snapshots this pipeline
queries are not how the dead cohort is discovered. They were kept anyway, and the measurement
justified them far better than expected:

| | distinct dead `Stock` tickers |
|---|---:|
| cumulative call alone | 7,469 |
| **union with 16 yearly snapshots** | **8,187** |

**718 dead names — 9.6% of the cohort — do not come back from a single cumulative call.** Inclusion
is not monotone because a ticker recycled by a new issuer drops off the current delisted roster. The
snapshots recover those names *and* make the recycling detectable, which the universe rule then acts
on.

### The coverage finding that limits what this fixture can be asked

`delistingDate` by year, across the provider's whole delisted roster:

| 2009 | 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | … | 2022 | 2023 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 40 | 46 | 76 | 55 | 140 | 185 | 382 | 559 | 766 | 756 | | 1,065 | 1,027 |

Several hundred US listings die every year, every year. **Forty in 2009 is not the tape, it is the
provider's records.** The dead cohort is materially under-sampled at the start of the span, the
histogram goes into the meta rather than this sentence being taken on trust, and any per-era
comparison run on this fixture has to carry it.

This is stated here because it is the single most likely way someone misuses the fixture: a
"delisting rate rose over time" finding read off this data would be an artefact of the provider's
archive.

---

## One request per symbol, and why it is still the as-traded frame

`fetch_etf_holdout.py` spends three requests per symbol — `TIME_SERIES_DAILY`, then `SPLITS`, then
`DIVIDENDS`. At this universe size that is ~10,000 requests.

`TIME_SERIES_DAILY_ADJUSTED` returns all three in one call, and — **measured, not assumed** — its
`1..4` OHLC columns are as-traded:

| AAPL 1999-11-01 | |
|---|---:|
| `4. close` | **77.62** |
| `5. adjusted close` | 0.58 |

The raw columns carry none of the 2000/2005/2014/2020 splits. That is the same frame
`TIME_SERIES_DAILY` serves, so [D24](D24-immutable-data-snapshots-fetch-once-freeze.md)'s
immutability argument and [D75](D75-corporate-actions-two-frames.md)'s two-frame separation are
untouched. Only the request count changes.

**What it costs, stated rather than discovered later:** the inline coefficients only cover the window
the series covers. AABA's `SPLITS` endpoint lists three splits where the inline columns show two, the
missing one predating the series. Immaterial at a 2010 span start.

**One divergence from the template is deliberate.** `--actions` divides each dividend amount by the
same cumulative split factor `--build` divides its prices by, so prices and dividends share one frame
(D75). `fetch_etf_holdout.py` takes the `DIVIDENDS` endpoint's as-declared amounts and labels them
split-adjusted. That is not repeated here.

---

## The judgement calls

### 1. The screen is per-symbol pre-live, not calendar pre-live

**This is the central design decision and it is forced.**

`fetch_etf_holdout.py` screens on a fixed calendar window ending the day before the parent fixture's
first live bar. That works because the parent is rectangular: every symbol shares one warm-up.

Neither half of that transfers.

- A **short universe cannot be rectangular** — see below.
- A **fixed global pre-live window is worse than useless here.** A window before 2010 would delete
  every company that listed after 2010, which is most of the ones that later died. The screen would
  become a listing-vintage filter wearing a liquidity costume.

So each symbol's screen window is **its own first 252 in-span sessions**, and its live window is
every bar after. The screen is strictly before the live window *for every symbol individually*, it
reads no bar the study would trade, and it touches no return, drawdown or trade count.

`apply_screen` is a pure function of one symbol's series for exactly this reason: the property is a
property of fifteen lines, not of a calendar constant, and the test calls those fifteen lines.

### 2. The price floor sits on the screen window only — this is what keeps the wrecks

`median close ≥ $3.00` and `median close × volume ≥ $1,000,000` over the screen window.

A price floor applied over the whole history would delete the collapses, which is selecting on the
outcome with extra steps. Applied to the first year only, a company trading at $40 in 2015 and $0.30
in 2019 **passes** — the screen never sees the $0.30. That cohort is the point of the fixture.

The **$1M floor rather than $5M** is a deliberate weakening of cost realism. D245 registered both as
W1 and W5 and found W1 the *better*-behaved cell; here the argument is different and simpler: at $5M
a day, most of the dead cohort disappears, and that is the bias this fixture exists to avoid. Cost
realism is weaker and is stated rather than buried — a $1M/day single name's spread is not 1 bp.

### 3. `assetType == "Stock"` is not common stock, and the fix is deliberately blunt

The provider files warrants, units, rights and every preferred series under `Stock`: `AA-W`,
`AAC-U`, `-P-HIZ`, and 627 five-letter tickers ending `U` are all `Stock` in the CSVs.

**The rule:**

- **(a)** any symbol containing a hyphen is excluded — `-W`/`-WS` warrant, `-U`/`-UN` unit, `-R`
  right, `-P-x` preferred series, `-CL` called;
- **(b)** any **five-letter** symbol whose fifth character is `W`, `U` or `R` — the NASDAQ
  fifth-letter convention;
- **(c)** fifth letter **`Q` is KEPT.**

Rule (a) is blunter than necessary and also drops the ~40 hyphenated dual-class ordinary lines. That
cost is paid on purpose: a rule a reader can apply by eye is worth more than forty names, and the
alternative is a suffix allow-list that will be wrong in a way nobody notices.

Rule (c) is the one that matters. **`Q` marks an issuer in bankruptcy.** It is common stock, and for a
short book it is the most relevant cohort on the tape. Excluding it would have been the survivorship
bias this whole record is about, wearing a tidiness costume.

### 4. Recycled tickers are dropped from both cohorts

**1,257 symbols** appear in both the active and delisted rosters, or carry two different
`(ipoDate, delistingDate)` pairs across snapshots. A ticker reused by a second issuer has a bar
series that cannot be attributed to one company, and a fixture for short research cannot carry a
price series that silently splices two businesses.

They are dropped from **both** cohorts, not assigned to one. That costs live names whose ticker
happened to be reused, and the count is reported rather than assumed small.

### 5. The pool is a prefix of a permutation pinned before any bar was fetched

8,601 symbols cleared the metadata rules — too many to fetch. The eligible pool is sorted, shuffled
**once** with seed `20260828`, and the fetch takes a **prefix**. Growing the budget extends the
prefix; it never re-picks.

That is the property that makes the pool honest: **no symbol enters or leaves because of anything
learned after the shuffle.**

The sample is **proportional, not dead-enriched.** 41.6% of the eligible pool is dead, which is far
above the 15% floor without any thumb on the scale, and a proportional sample keeps the fixture's
cross-sectional composition interpretable. Over-weighting the dead cohort would have bought
insurance at the price of a universe whose base rates mean nothing.

### 6. The budget was sized from a pilot; the screen was not

A 250-symbol pilot off the front of the same permutation returned a **47.2% pass rate**, which sized
the prefix at 3,400. **The pilot sized the budget. It did not touch the screen**, which was pinned in
the file before the pilot ran, and the pilot's 250 are the first 250 of the same prefix — nothing was
re-picked and nothing re-fetched.

### 7. `delistingDate` is not always a delisting date — found by a failing test

**A test failed, and the failure was the finding.** `test_the_dead_names_actually_stop_trading_inside_the_span`
turned up eight symbols labelled dead that were still printing bars at the span end.

The cause:

| `delistingDate` | rows |
|---|---:|
| **2026-08-27** — the day the roster was pulled | **601** |
| 2026-05-28 | 54 |
| 2022-12-23 | 47 |
| 2019-08-07 | 41 |

**601 of 9,449 delisted rows — 6.4% of the entire dead cohort — share one date, and it is the
refresh date.** Six hundred companies did not delist on one Thursday. The provider stamps the
refresh date on names it has just dropped, in batches.

Two rules follow, and both are enforced and tested:

1. **A `delistingDate` after `SPAN_END` means the company was listed for the whole span**, so it is
   `alive` *for this fixture* whatever today's roster says. Its delisting, real or stamped, happens
   outside the data.
2. **A `delistingDate` inside the span whose bars keep coming for weeks afterwards is a provider
   contradiction.** LTCH is stamped 2026-05-28 and trades through 2026-08-26. The two records
   disagree and there is no way to tell from here which is right, so the name is **dropped and
   counted**. A mislabel in either direction corrupts the one split this fixture exists to support,
   and a dropped name that is reported is much cheaper than a wrong label that is not.

This is recorded prominently because it is a trap for anyone else reading `LISTING_STATUS`: taking
`delistingDate` at face value would put 601 phantom same-day delistings into a survival analysis.

### 8. The reverse-split signature, rather than a threshold chosen to fit

The first build flagged four up-moves at ≥ 4×. Inspected one by one:

| | move | dollar volume | verdict |
|---|---:|---:|---|
| KODK 2020-07-29 | ×4.18 | **×2,000** | real — the $765M DFC loan; high 60.00, retraced to 14.94 in a week |
| TLMD 2022-02-03 | ×4.43 | **×296** | real — all-cash acquisition; price then pinned flat at 2.83–2.93 |
| VSA 2025-01-31 | ×4.30 | **×2,283** | real — squeeze on 727M shares against 1.4M, fully retraced in five sessions |
| VRM 2025-02-20 | ×6.19 | ×5.3 | **not a day's return** — 83 days of no bars, a Chapter 11 suspension, on 34,165 shares |

That table produced two rules better than an allow-list alone.

**GATE C — the arithmetic signature.** A reverse split multiplies the price by `r` and *divides* the
share count by `r`, so **dollar volume is invariant across it**. Real spikes move dollar volume by
two to three orders of magnitude. So the hard test is a large up-move whose dollar volume barely
changed — a criterion that follows from what a split *is*, not from a number picked after seeing
these four. It fires regardless of what the documented list says.

**Halt crossings are not one-day returns.** A price change across an 83-day trading suspension is a
reorganised capital structure. Those are reported with their gap, exempt from GATE B, and the
per-symbol `max_gap_days` tells the downstream loader which symbols need segmenting rather than
treating as continuous.

The three real events remain pinned by name in `DOCUMENTED_LARGE_MOVES`, with the evidence for each,
exactly as `test_etf_intraday_fixture.EXPECTED_SPLITS` pins its twelve splits.

### 9. The panel is ragged, on purpose

**A rectangular panel needs every symbol present on every date, and that requirement is precisely
what deletes the dead names.** [D245 AMENDMENT 1](D245-the-wide-universe.md) recorded exactly this:
one delisted fund truncated the whole intersection to 880 bars, and the completeness screen that
fixed it was itself survivorship bias.

So the fixture is ragged, with per-symbol start and end dates.

**`run_macd_ladder.load_panel` refuses this fixture** — `raise ValueError("symbols have different
bar counts")` — and that refusal is *correct* for a rectangular daily universe. It is not weakened.
**A downstream loader is required and does not exist.** What it must do is written into the meta and
repeated here:

1. build a **union date index** and place each symbol on it with an **explicit presence mask** —
   never a forward-fill and never a zero. A filled bar is a fabricated price; a zero is a −100%
   return;
2. mask returns, positions, costs and equity contribution to zero outside each symbol's own
   `[first_bar, last_bar]`;
3. treat a delisting as a **forced exit at the last bar's close**, and say what that assumes — a real
   short is bought back or settled, and assuming a fill at the final print of a company being
   delisted is **optimistic**;
4. drop each symbol's own pre-live window using the per-symbol `live_start` in the meta, so no bar the
   screen read is ever traded;
5. normalise cross-sectional aggregates by the **live count on each date**, not the symbol count, or
   every breadth statistic is diluted by absent names.

**None of that is written here.** This record builds data.

### 10. Concurrency, and why it is still respectful

The template's limiter paces at 66/min against the 75/min ceiling. A full daily history is a few
hundred kilobytes, and a sequential loop measured **35 requests/minute** — download time dominated
the pacing entirely.

Four workers now run behind **one shared, lock-protected limiter that still gates the start of every
request**, so the aggregate cannot exceed 66/min however many workers run. Only the idle time between
responses is removed.

**It barely helped: 38/min measured against 35.** The bottleneck is bandwidth, not latency. The honest
conclusion is that this fetch takes ~90 minutes and no amount of concurrency changes that — recorded
so the next person does not re-derive it.

---

## The adjustment gates

Single stocks carry far more corporate actions than ETFs, and [D226](D226-the-volume-gate-on-57-etfs-at-15-minutes.md)
established the stakes: an unadjusted 1:20 reverse split appeared as a **+1,772% single bar**. One of
those in a universe this size dominates any cross-sectional statistic computed over it.

**GATE A — the adjustment took.** Every sidecar split with ratio ≥ 1.5 or ≤ 1/1.5 whose effective
date lands on an in-span bar must leave `|close(t)/close(t−1) − 1| ≤ 0.50`. This tests the adjustment
directly on the dates where the raw series is *known* to jump.

**GATE B — nothing was missed.** No adjusted bar-to-bar close ratio ≥ **4.0** anywhere, except on a
documented list. This reads the data rather than the sidecar, so it catches splits the sidecar does
not know about.

**GATE B is asymmetric and that is the point.** Upward, a ×4 single-day move in US common stock is
overwhelmingly a missed reverse split, so it is a hard failure. Downward, an 80% single-day loss is a
real and frequent event in this universe — bankruptcy, fraud, a failed trial — and **it is exactly the
signal a short book exists to capture.** A symmetric gate would delete the payload. Large drops are
therefore reported in the meta and never fatal.

---

## The residual biases this construction does NOT repair

Written into the meta as `SURVIVORSHIP_BIAS_STATEMENT`, and asserted by a test so it cannot quietly
disappear:

1. **Provider coverage.** 40–76 recorded delistings a year for 2009–2012 against 700–1,000 a year
   after 2016. The dead cohort is under-sampled at the start of the span.
2. **The history floor.** A symbol needs 378 in-span sessions to enter, which removes companies that
   listed and died inside about eighteen months — disproportionately SPACs and micro-caps, and
   disproportionately the *fastest* failures.
3. **The screen itself.** A $1M/day and $3 floor over each symbol's first year removes names that
   were never liquid enough to short, and those skew dead.

**What this fixture is not:** a point-in-time reconstruction of the US tape. **No cross-sectional
base rate taken from it — delisting rate, failure rate, the fraction of names that fall 90% —
should be read as a market base rate.**

The `survived / collapsed / delisted` labels follow the crypto convention
([`fetch_crypto_universe.py`](../../scripts/fetch_crypto_universe.py), D140): **hindsight by
construction**, used only to split results after the fact, never to decide what is traded. Nothing in
the selection can see them.

---

## Reuse — R1 and D212 are binding

`fetch_short_universe.py` is a **sibling of `fetch_etf_holdout.py` built to its structure**, not a new
fetcher: the same `--plan / --fetch / --select / --actions / --build` phases, the same key handling,
the same cache-first resumability, the same structural success test on a provider that answers
HTTP 200 to its own errors, the same `split_factor_at` back-adjustment.

**Written fresh:** the delisted-cohort discovery, the recycled-ticker rule, the per-symbol pre-live
screen, the ragged writer, the two gates, and the shared-limiter concurrency. Nothing else.

---

## Security and terms

- The key is read from `ALPHAVANTAGE_API_KEY`, falling back to `~/.config/alphavantage/key` —
  **outside the repository.** It is never inlined, never printed, never logged. Only the *source* of
  the key is printed.
- `urllib` puts the full request URL — key included — into `HTTPError.__str__` on some paths, and a
  traceback is an artifact too. `_get` re-raises with the URL stripped.
- A test scans the fixture, the events sidecar, the meta, this record and the fetcher source for the
  literal key.
- Paced at 66/min against a 75/min ceiling, exponential backoff, **hard stop after 5 consecutive
  failures** rather than a retry loop. Every response cached, so a re-run costs nothing and an
  interrupted run resumes rather than restarting. Cache writes are atomic via a `.part` rename, so a
  killed run never leaves a truncated payload that a later run would trust.
- **D191:** the raw cache is not committed. `data/raw/alphavantage/` is gitignored; only the derived
  fixture, the events sidecar and the meta are committed.
- Alpha Vantage's terms make commercial redistribution the line that matters, and
  `docs/alpha_vantage_api.md` already records that making this repository public would in all
  likelihood cross it. **This repository stays private.**

---

## Verification

`tests/unit/test_us_shorts_fixture.py`:

| test | what it stops |
|---|---|
| every recorded split leaves no discontinuity | the adjustment being dropped, inverted, or applied on the wrong side of the effective date |
| no adjusted bar multiplies the price by ≥ 4 outside the documented list | a split the sidecar never knew about — D226's +1,772% bar |
| the screen reads the pre-live window and nothing after it | the fixture being selection on the outcome |
| a name illiquid only in its screen window is rejected | the test above passing because the screen does nothing |
| the price floor sits on the screen window | a whole-history floor deleting the collapses |
| every symbol's live window starts after its screen window | the per-symbol claim, checked against the bars rather than the file that made it |
| the delisted cohort is non-empty and above the floor | the failure mode this whole record is about |
| dead names actually stop trading inside the span | a mislabel reintroducing survivorship into the cohort split |
| the meta carries an explicit survivorship statement | the three residual biases going quiet |
| the panel is ragged and the meta says a loader is required | a rectangular rebuild deleting the dead names |
| `load_panel` really does refuse this fixture | the meta's claim about it drifting out of date |
| bankrupt `Q` tickers are kept, warrants/units/rights/preferreds are not | the exclusion rule silently changing |
| the key appears in no artifact and no source | a leaked key in the one class of file this project commits |

---

## RESULT

<!-- filled in from the actual build below -->
