# D621 — Retail attention measured from creations and Robinhood holders, with GDELT hourly news through the API: the amendment that replaces the deposit's hourly-Wikipedia row

**Status:** Committed
**Date:** 2026-09-22
**Category:** Data
**Source:** `docs/internal/User-Doc-Deposit/SETTLEMENT_FLOW_LEDGER_PREREG.md` §3.3c (its lines
105–116, "News and attention data", whose **line 112** is the row this record amends) and §P3.7
(its lines 249–267, "News and virality detector (retail attention)"). The deposit is an
**untracked, read-only** source: it is quoted verbatim with line numbers here and is neither
staged, copied nor edited. **This record RECORDS an amendment and its evidence; the doc edit
itself is the principal's, and the text it should carry is drafted in the footer.**

Built on [D612](D612-the-attention-layer-and-its-point-in-time-guards.md) (the attention layer,
its hashed `QUERIES.md`, its point-in-time guards and its erratum on line 112 — this record is
what the erratum led to), [D619](D619-the-fund-panel-the-fund-facts-and-the-cme-side-census.md)
(`fund_nav_daily`, the four ProShares funds' daily NAV, shares and AUM),
[D609](D609-the-panel-loader-chokepoint-and-the-seven-root-multiplier-fix.md) (`load_panel`, the
seal on every bulk read), [D608](D608-the-forward-data-recorder.md) (`Recorder`, through which
every network read goes) and [D485](D485-micro-contracts-are-not-a-retail-identifier.md) (which
first used the Robintrack archive here). Governed by
[D48](D48-no-false-affordances-enum-values-and.md) (raise loudly),
[D78](D78-property-test-conventions.md) as amended by
[D537](D537-derandomize-does-not-mean-deterministic.md),
[D191](D191-manifest-only-storage-for-large-archives.md) (cache the raw, commit the derived),
[D550](D550-what-CI-found-in-its-first-run.md) (newline pinning), and R9 and R17 in
[`../RULES.md`](../RULES.md).

**The principal approved the plan on 2026-09-22**: *"I like this action plan"* — drop the hourly
Wikipedia backfill; keep the daily REST series as a cheap secondary; put **creations** at the
centre as the retail-demand measure; use **Robintrack** to validate it over 2018–2020; use
**GDELT hourly news counts through the free DOC API** as the news side.

---

## 1. The amendment

### 1a. What was wrong

D612 found the deposit's line 112 to be **wrong as written**. It reads:

> `| Wikimedia hourly pageviews | Hourly, from 2015 | Primary: public attention |`

The Wikimedia REST per-article endpoint serves **daily and monthly only** — an hourly request
answers HTTP 400, `granularity should be equal to one of the allowed values: [daily, monthly]`.
Per-article hourly data exists **only** in the `dumps.wikimedia.org` hourly pageview dumps: one
file per hour covering every project and every article on earth, ~56.8 MB gzipped, of which
`QUERIES.md`'s eight titles account for about sixteen lines. The 2016–2023 backfill the deposit's
feature set needs is **~2.5 TB over 70,128 files**, and D612 measured the host at **1.79 MB/s on
one connection and slower on two** — about thirteen hours of downloading for the first usable
60-day matched z-score alone. D612 recorded the erratum, built the parser, and declined the
backfill.

### 1b. What replaces it, and why creations are not a substitute but the thing itself

**The hourly pageview series was a proxy for retail demand. A creation IS retail demand.**

A creation is a fund's share count changing: an authorised participant delivering the basket and
receiving shares because someone bought them. It is denominated in the units the deposit's own
creation model is written in — §P3.7's integration line is
`ΔCreate_hat = C2 + d1·att_level + d2·att_accel + d3·att_breadth`, and `ΔCreate` is the
left-hand side. The attention features exist to **predict the creation**. Measuring the creation
directly is not a worse proxy for attention; it is the quantity the proxy was standing in for,
and it removes a modelling step rather than adding one.

Four properties decide it, and none of them is about convenience:

| | hourly Wikipedia pageviews | daily creations |
|---|---|---|
| what it counts | people reading an encyclopedia article | **money that arrived in the fund** |
| relation to `ΔCreate` | a predictor, at two removes | **it is `ΔCreate`** |
| cost to obtain 2016–2023 | ~2.5 TB, ~13 h of downloading for one z-score | **already on disk** (D619, `fund_nav_daily`, 16,402 rows, 2008-11-24 → 2026-09-18) |
| point-in-time risk | a publication buffer this repository chose | a publication time **the source does not state**, handled by a declared one-day lag |

The cost column is the weakest of the four and is listed last on purpose. If creations were the
worse measurement, being free would not matter.

**What creations are NOT.** They are daily, so they cannot carry `att_accel` as the deposit
defines it (three hours against three hours) and they cannot carry `headline_burst` at all
(15-minute blocks since 09:30). Those two features stay on the news side. And a creation is a
count of shares in a **back-adjusted** series, so it is scale-free within a fund and not
comparable in count across eras; every statistic in §3 is a rank, a z or a percentile share for
that reason.

### 1c. The four replacement series, and what each is for

| series | source | clock | state |
|---|---|---|---|
| **creations** | `fund_nav_daily` (D619), `Δshares_out` | daily | **PRIMARY.** Four funds on disk: BOIL, KOLD, UCO, SCO |
| **Robinhood holders** | `data/raw/robintrack/` | hourly | **VALIDATION, 2018-05-02 → 2020-08-13.** The only retail *account* count this repository holds |
| **GDELT news** | the raw 15-minute GKG files (backfill), the DOC 2.0 API (forward) | 15 min / hourly | **PRIMARY, unchanged in substance.** D612's route stands |
| **Wikipedia daily** | the REST per-article endpoint | daily | **SECONDARY, kept.** `fetch_attention.py --wiki-daily` already fetches it; `QUERIES.md` §1a is already probed against it. Cheap, and it is not a primary series |

---

## 2. The code

| file | what it is |
|---|---|
| `src/backtest_framework/data/retail_attention.py` | `creations`, `creation_z`, `creation_level`, `creation_accel`, the Robinhood reader and `holders_z`, `news_n_hourly`, the `RetailAttention` bundle with an `available_at` per component, and the two correlation statistics. **No writer of any kind** |
| `scripts/build_robintrack_funds.py` | `--build`, `--gates`, `--selftest` — the six tickers out of the 8,597-ticker archive |
| `scripts/fetch_gdelt_hourly.py` | `--probe`, `--from-files`, `--api`, `--gates`, `--selftest` |
| `scripts/retail_attention_report.py` | `--run`, `--check`, `--selftest` — the validation measurement |
| `data/fixtures/robintrack_energy_funds.csv.gz` + `.meta.json` | 115,290 rows, 433,420 bytes, sha256 `36864d6feadebd36e8e4a1e7f188cb7b9349213cd7a219590dfc7b94c2b90d5d` |
| `data/fixtures/gdelt_hourly_sample.csv.gz` + `.meta.json` | 672 rows, 7,185 bytes, sha256 `bbfd7cf41d49999fdc8cded3145664686c4436cf83f8db02e5da96a7878094aa` |
| `data/retail_attention_validation.json` | the measurement, 28,087 bytes, sha256 `fc8bf8ee00248f79523f0ea7aaa1cbbc7b5910109f246d8864ba69b8a5d44ba8`, **carrying no build timestamp** |

Tests: `tests/unit/test_retail_attention.py` (72), `tests/golden/test_retail_attention_ledger.py`
(17) with its `.hand.txt`, `tests/property/test_retail_attention_property.py` (19). **108 in
total. No new numbered deposit test is claimed** — tests 21–25 are D612's guards and are already
claimed by it; see §7.

### 2a. What is reused from D612 rather than rewritten

This record's module imports eight names from `attention.py` and calls them:

* **`att_level` IS `creation_level`.** It is a mean of a mapping of z-scores with finiteness
  guards; it does not care whether the keys are sources or funds, and a second copy would be a
  second thing to keep right.
* **`att_accel` computes `creation_accel`.** Six consecutive daily levels are laid on a six-hour
  axis and handed to it, so the exactness-on-a-constant property — `math.fsum` over the same
  three doubles in the same order, difference exactly `+0.0` — is inherited rather than
  re-derived. The golden asserts `== 0.0` with no tolerance and the property test quantifies it
  over the level.
* **`zscore_matched` IS `holders_z`**, and IS `creation_z(match="same_weekday")`.
* **`refuse_coarse_resolution`** is called first by `news_n_hourly`, always.
* **`TRAILING_DAYS`, `MIN_MATCHED_OBS`, `ACCEL_HOURS`** are imported, not retyped.

**The one genuinely new piece of arithmetic is the daily z window, and it is pinned against its
original.** `zscore_matched` matches on hour-of-day *and* weekday, because a pageview series has
both cycles. A daily creation series has neither, and 60 days of one weekday is at most
`ceil(60/7) = 9` observations against D612's own floor of five. So `creation_z` defaults to
`match="all_days"` and offers `match="same_weekday"`, which delegates. On an input where the two
windows select the same five numbers — five consecutive Mondays — **all three paths return the
identical double, `1.8973665961010275`**, and that equality is a test. A copy that is checked
against its original is not a second copy of a fact.

### 2b. The availability rules, each declared and each conservative

| component | may first be used at | why that and not something tighter |
|---|---|---|
| creations | `date + 1 day`, midnight UTC | **The source states no publication time.** ProShares' historical-NAV CSV has no `published_at` column at all, which `fund_nav_daily`'s own meta records as an *absent* column rather than a null one. A share count dated `d` is struck after the close of `d`; one full day is never optimistic |
| holders | the poll instant `+ 1 hour` | one full polling interval. The archive polls at a ~1.00 h median cadence; a series read at its own observation instant is a series read with no latency, which no operator has |
| GDELT | the publication timestamp | D612's `available()`, unchanged |

`RetailAttention.__post_init__` **raises** when any component's `available_at` is after the `tau`
it is being bundled at. That is the only place the three rules are enforced together, and it
raises rather than warning because a look-ahead is unfalsifiable afterwards (R9).

---

## 3. The validation measurement

`data/retail_attention_validation.json`, built by `scripts/retail_attention_report.py --run` in
**3.0 s**, and reproducible: `--check` recomputes it and compares **byte for byte**. The file
carries the sha256 of every input instead of a build timestamp, so it is a pure function of the
committed fixtures and a test asserts that it reproduces from them.

**THIS IS A DATA-QUALITY MEASUREMENT AND NOT A SIGNAL TEST.** No return is computed, no price bar
is read, no null is run, nothing is scored, and no verdict about tradeability follows from any of
it. The question is narrow: over the overlap window, does the daily change in Robinhood holders
move with the daily change in shares outstanding? If it does not, creations are not a retail
measure and §1b is wrong on its own terms.

### 3a. The conventions, because each one changes the number

1. **The interval.** A creation is `shares_out[d] − shares_out[prev(d)]` where `prev(d)` is the
   previous day *in the source*, not `d − 1 day`: a fund series has no Saturday and no Christmas.
   The holder change is differenced over **the same interval**. Steps longer than five calendar
   days are skipped and named (none occurred inside the window on any of the four funds).
2. **The daily holder cut is the last poll of the UTC day.** The archive's timestamps are UTC and
   that is a measurement, not an assumption: the hour-of-day histogram is flat across all 24
   hours on every one of the six files. 00:00 UTC is 19:00 or 20:00 New York, so the last poll of
   a UTC day is three to four hours after the US close. Cutting at 21:00 UTC instead would be
   defensible and would move the boundary by one poll; it is not used, and this sentence exists
   so that the choice is checkable.
3. **Lead and lag are in SERIES STEPS.** `lag = +k` pairs the creation at index `i` with the
   holder change at index `i+k`, so a **positive lag asks whether holders move AFTER creations**
   and a negative lag asks whether they move before.
4. **A "creation day"** is a day whose `|creation|` exceeds the 90th percentile of `|creation|`
   over that fund's own overlap rows, by linear interpolation between order statistics, compared
   **strictly**. The rule is stated because on ten points the percentile definitions differ by a
   whole rank; the golden works it by hand.
5. **A missing holder poll drops the step and is counted.** Never zero-filled. A zero across the
   nine-day January 2020 outage would show USO losing 144,000 holders overnight and regaining
   them ten days later — two of the largest flows in the sample, both fictional.
6. **Both statistics, always together**, per R17's shape applied to a correlation.

### 3b. The headline table

Overlap **2018-05-02 → 2020-08-13**, 576 trading days. `fund_nav_daily` read through
`load_panel(..., reserved_from="2024-01-01")`: 13,678 rows to **2023-12-29**, **0 reserved rows
read**.

| fund | paired steps | of which `Δshares = 0` | **non-zero n** | Spearman, lag −1 / 0 / +1 | Pearson, lag −1 / 0 / +1 |
|---|---:|---:|---:|---|---|
| **BOIL** | 480 | 371 (77%) | **109** | +0.238 / **+0.281** / +0.087 | +0.174 / +0.118 / +0.041 |
| **KOLD** | 560 | 458 (82%) | **102** | **+0.207** / +0.092 / −0.035 | +0.090 / **+0.614** / +0.146 |
| **UCO** | 560 | 200 (36%) | **360** | +0.494 / **+0.556** / +0.351 | **+0.678** / −0.077 / −0.107 |
| **SCO** | 560 | 266 (48%) | **294** | +0.189 / **+0.338** / +0.141 | +0.011 / **+0.350** / +0.091 |

*(The cells above are computed on the steps where a creation actually happened. The
whole-sample cells are in the artefact; they are lower and mean less, because a rank correlation
over a tie block covering 77% of the rows is mostly a correlation between one tied block and the
holder series. The zero mass is the honest sample-size statement and it is why the `non-zero n`
column is bold.)*

**What the table says, stated as narrowly as it supports:**

1. **Every fund is positive at lag 0 and at lag −1 on the rank statistic, and every fund is lower
   at lag +1 than at lag 0.** Four of four, on both counts. The association exists and it is not
   in the direction "creations lead holders".
2. **The magnitude is modest and it is not the same on all four.** UCO reads +0.556 at lag 0;
   KOLD reads +0.092. These are not four experiments — see §3d.
3. **Nothing here licenses a return claim.** A rank correlation of +0.3 between two retail
   measures is evidence that they measure a related thing, not that either predicts a price.

### 3c. The two statistics disagree, and that is the finding worth keeping

**UCO: Spearman +0.556 at lag 0 while Pearson reads −0.077 — and Pearson jumps to +0.678 one step
earlier.** The Pearson is a statistic about two days:

| day | `Δshares` | `Δholders` |
|---|---:|---:|
| 2020-04-20 | +38,744,000 | **+26,075** |
| 2020-04-21 | +66,200,000 | **−28,373** |

That is the negative-WTI week. Retail piled into UCO on the 20th; the creation that answered it
settled on the 21st, by which time the holder count was falling. A product-moment statistic on a
sample containing those two rows is a statistic about those two rows — and it flips sign between
lag 0 and lag −1 for exactly that reason, while the rank statistic moves by 0.06.

**KOLD is the mirror image**: Pearson +0.614 at lag 0 against Spearman +0.092, carried by
2020-08-03 (`Δshares` +105,000 with `Δholders` +157). One day, one number.

This is `CLAUDE.md`'s trade-distribution rule in a different costume, and the golden's Case 1 is
it written out on ten synthetic rows where Spearman reads **0.9394** and Pearson reads **0.4777**
on the same data. **Neither statistic is reported here without the other, at any lag, in any
cell.**

### 3d. Four funds are not four experiments

BOIL and KOLD are one issuer's long and short leveraged **natural-gas** funds; UCO and SCO are the
same pair on **crude**. Two underlyings, one issuer, two directions. **The effective number of
independent cells is about two**, the artefact says so in its own conventions block, and the four
rows above must not be read as four confirmations.

### 3e. The creation-day cut

On each fund's top decile of `|creation|` days, the share on which the holder count *rose*:

| fund | top-decile days | `Δholders > 0` | share | p90 of `|Δshares|` |
|---|---:|---:|---:|---:|
| BOIL | 43 | 22 | 0.512 | 50 |
| KOLD | 46 | 29 | **0.630** | 5,000 |
| UCO | 56 | 31 | 0.554 | 3,528,000 |
| SCO | 53 | 26 | **0.491** | 6,250 |

**This cut is weaker than the rank correlations and is reported anyway.** Three of four sit
between 0.49 and 0.55, which is a coin flip, and only KOLD reaches 0.63. The reason is visible in
the convention rather than in the data: a top-decile `|creation|` day includes large
**redemptions**, on which the holder count should *fall*, and this cell counts them as failures.
It is a sign-blind statistic on a two-sided quantity. **The rank correlations in §3b are the
measurement; this table is a diagnostic that the record declines to dress up.**

### 3f. The two funds with no creation truth

USCF publishes no free NAV or share-count history (D619: the fund page is JS-gated and no free
holdings history exists), so UNG and USO carry a holder series and nothing to correlate it
against. Differenced across the four ProShares funds' own trading-day calendar — they are NYSE
Arca listings like the other four — 561 steps each:

| | n | mean | **median** | sd | share positive | top-decile days | of which up |
|---|---:|---:|---:|---:|---:|---:|---:|
| UNG | 561 | +3.92 | **+1.00** | 25.41 | 0.501 | 54 | 40 |
| USO | 561 | +248.32 | **−1.00** | 4,472.26 | 0.478 | 56 | 45 |

**USO's mean is +248 and its median is −1.** That is `CLAUDE.md`'s tell, and here it is genuine
and uninteresting: USO gained ~215,000 Robinhood holders over the window in a handful of 2020
weeks and drifted down on most ordinary days. The number worth carrying is the median, and the
mean is reported beside it rather than instead of it.

**A first build of this cell was wrong and the error is recorded rather than quietly fixed.** It
differenced the holder series over **calendar** days, so every weekend contributed an exact zero:
257 of UNG's 815 steps — a third of the sample — said nothing, the median was 0.0 and the share
positive read 0.36. Using the ProShares trading-day calendar moved UNG's median from 0.0 to +1.0
and its share positive from 0.361 to 0.501. **A weekend is not a day on which nothing happened;
it is a day that does not exist for this series.**

### 3g. Three facts about the fixture that a later study must carry

1. **BOIL's holder series ends 2020-04-21**, four months before the other five. The archive stops
   carrying it. Nothing is padded, the per-fund span is the fund's own, and BOIL's 96 dropped
   steps are the tail — counted in the artefact, not silently absent.
2. **BOIL barely creates.** 371 of its 480 paired steps have `Δshares` exactly zero, and its
   whole-window p90 of `|Δshares|` is **50 adjusted shares**. Its cells are the thinnest here.
3. **`split_like_steps` is a flag, not a filter.** Steps moving the share count by more than 50%
   of its own level: KOLD 11 inside the window (48 over the whole series), SCO 3 (11), BOIL 1
   (7), UCO 0 (6). The ProShares series is fully back-adjusted, so a reverse split leaves no
   discontinuity at all; almost all whole-series flags sit in each fund's earliest,
   smallest-share era, where the back-adjusted count is a handful of shares and one creation
   doubles it. They are reported and not dropped.

---

## 4. GDELT: the API facts, and what is deferred

### 4a. The API refused, twice, and the second refusal was harder than the first

Two requests were made on 2026-09-22, the same URL and the same `User-Agent`, about twelve
minutes apart. Both are logged in `data/fixtures/gdelt_hourly_sample.meta.json`'s `api_state`
block, which names the tool, the URL and the order of the outcomes.

| attempt | outcome |
|---|---|
| first | **HTTP 429**, body: *"Please limit requests to one every 5 seconds or contact … for larger queries. All high-traffic users should switch to our ngrams dataset … For trend analysis, please see our daily newsletter briefings …"* |
| second | **no response at all** — `urllib.error.URLError: <urlopen error [WinError 10060] A connection attempt failed because the connected party did not properly respond after a period of time>` |

**The host escalates: a refusal body first, then a dropped connection.** D612 never got a 200 from
it all day either. So `--api` is **built and not run**, and nothing was hammered.

**Nothing was written into `data/raw/` for the second attempt**, and that is a decision. A 429 is
a *response* and `Recorder` keeps responses byte for byte; a dropped connection produces no
status line and no bytes, so the only thing available to record would be this script's own
rendering of an exception. `TransportRefused` raises instead, and the failure is logged where a
later reader looks — in the fixture's meta and here.

### 4b. The resolution rule, and why there are two of them

The DOC API **autoscales its bucket width with the span asked for** and reports what it chose in
`query_details.date_resolution`. Anything wider than a few days answers `"hour"`.

D612's `refuse_coarse_resolution` refuses `"hour"`, **correctly**: the deposit's `news_n` is a
60-minute count built out of 15-minute blocks (its lines 251 and 265) and `headline_burst` is
*"1 if `z_news` > 3 in any 15-min block since 09:30"*, which an hourly bucket cannot answer at
all. An hourly bucket is not a coarser version of the right number; it is a different number.

D621's news series is hourly **on purpose** — it is paired with a daily creation series. So:

* `news_n_hourly(..., accept_hourly=False)` → `refuse_coarse_resolution`, unchanged, 15 min or
  finer.
* `news_n_hourly(..., accept_hourly=True)` → **the same function first**; only if it refuses is
  an hourly spelling admitted, and **nothing else**. `"day"` and `"month"` still raise, from the
  original function, unwidened.

The accepted spelling travels on every `NewsSeries` object, so the widening is visible in the data
a consumer holds rather than in a flag it must remember to check. **The forward recorder job stays
15-minute** (`data/recorder/jobs.json`'s `attention` job, D612's, untouched by this record), and
the raw 15-minute files remain the historical route.

### 4c. The hourly fixture, and the comparison that is deferred

`data/fixtures/gdelt_hourly_sample.csv.gz` is built by `--from-files`: D612's own
`attention_sample.csv.gz` holds the 15-minute file-derived counts for 2019-11-04…05, and this
sums them to the hour — four slots per hour, all four required, `available_at` derived as the
latest of the four slots' own `gdelt_available_at` (which is `hour + 1 h`), tone as the
count-weighted mean of the slots that had one and `NaN` when no document matched. **672 rows: 48
hours × 14 queries.** The `source` column is `files_15m_summed` on every row and the API half is
**absent, not null-filled**.

| key | total documents, 48 h | zero hours |
|---|---:|---:|
| `theme_env_oil` | 11,974 | 0 |
| `theme_econ_oilprice` | 3,457 | 0 |
| `theme_env_naturalgas` | 3,111 | 0 |
| `theme_econ_natgasprice` | 247 | 1 |
| `natural_gas` (phrase) | 115 | 8 |
| `tk_boil` | 113 | 11 |
| `crude_oil` (phrase) | 76 | 17 |
| `tk_sco` | 41 | 26 |
| `wti` | 14 | 37 |
| `tk_uso` | 5 | 44 |
| `tk_ung` | 2 | 46 |
| `henry_hub`, `tk_kold`, `tk_uco` | **0** | 48 |

D612's finding stands at the hourly scale: **the four theme keys carry the news series and the
phrase keys are nearly empty.** Three keys matched nothing at all in two days.

**The pre-registered comparison — the API's hourly count against these file-derived counts — is
NOT RUN, and the record says now what it will be, before either is seen.** The two count
**different corpora with different matchers**: `timelinevolraw` counts documents in GDELT's DOC
index matching a DOC-query grammar, while the 15-minute route counts GKG rows matching
`QUERIES.md` §2b's title/url/theme rules. **They are not expected to be equal.** What is worth
measuring is the rank correlation of the two hourly series and the ratio of their totals. Writing
that down before the API answers is the only way whatever comes back cannot be read as confirming
a prediction nobody made.

The parser is nonetheless proved: `scripts/fetch_gdelt_hourly.py`'s `API_SHAPE` is a payload of
the DOC 2.0 **documented** response shape — the fields `scripts/fetch_attention.py`'s `gdelt_doc`
already reads — and six tests drive it, including the refusals. **It is not a recorded live
response, and this sentence is here so nobody later mistakes it for one.**

---

## 5. What is NOT done

* **No hourly Wikipedia backfill.** The ~2.5 TB is not paid and no part of it is fetched. The
  parser D612 built stays, unused, for whoever authorises it.
* **No live GDELT DOC sample.** §4a. `--api` is built, its parser is tested, and it has not run.
* **No social series.** The deposit's lines 113 and 253 gate `social_n` on **Q12**, which is
  unresolved. `QUERIES.md` lists the two social ids as `disabled (Q12)` and neither this module
  nor D612's has a code path that would read them.
* **No Google Trends.** The deposit's line 114 excludes it from modelling entirely.
* **No P9 tickers on Robinhood.** HNU and HOU — the deposit's Canadian leveraged natural-gas ETPs
  — **have no file in the 8,597-ticker export**, checked. They are TSX-listed and outside a US
  retail broker's universe. `--build` and `--gates` assert their absence so that nobody searches
  again, and the assertion is written to fire if that ever becomes false.
* **No UNG/USO creation series.** D619 established there is no free route; §3f carries holders
  alone and says why.
* **No deposit file is edited.** §7 drafts the text; the edit is the principal's.
* **No manifest or catalogue row is added.** `data/data_manifest.json` and
  `data/panel_catalogue.py` are shared documents whose counts are pinned at 128 panels by two
  tests; the two new rows are drafted in §7 for the integrator. Until they land,
  `tests/unit/test_retail_attention.py` skips on an absent fixture through its own
  `needs_d621_fixture`, which names the command that builds it.
* **No return, no signal, no trade, no null.** Every measurement is on rows dated 2023-12-29 or
  earlier; the Robintrack archive ends 2020-08-13 and cannot reach the 2024-01-01 cut at all.

---

## 6. What would change this record

* **The DOC API answering.** §4c's comparison runs, `gdelt_hourly_sample.csv.gz` gains its
  `doc_api_hourly` rows beside the file-derived ones, and the `api_state` block is replaced by a
  fetch.
* **A creation publication time being stated by the source, or measured.** The one-day lag in
  §2b is a declared stand-in and would be replaced by the measurement — not by a guess in the
  other direction.
* **A free UNG/USO share-count history appearing.** §3f gains a truth column and the sample gains
  a third underlying, which is the cheapest available improvement to §3d's effective `n` of two.
* **A retail holder series after 2020-08-13.** Robintrack ends there. Nothing in §3 says anything
  about the 2021–2026 retail regime, and the record does not pretend otherwise.
* **The seal reconciliation.** `fund_nav_daily` spans past this repository's 2024-01-01 holdout
  and into the deposit's sealed vault window (2025-03-01 → 2026-09-18). The two have not been
  reconciled in writing (D604, D619) and nothing here may score anything until they are. This
  record reads the panel through the chokepoint with the cut on and **0 reserved rows read**,
  which is the only posture available before that decision.

---

## 7. Footer drafts, for the integrator

### 7a. `docs/data-available.md` paragraphs

> **`data/fixtures/robintrack_energy_funds.csv.gz`** — the six energy funds' Robinhood holder
> counts, D621. `ticker, ts_utc, holders`, 115,290 rows, 433,420 bytes, sha256
> `36864d6feadebd36e8e4a1e7f188cb7b9349213cd7a219590dfc7b94c2b90d5d`. BOIL, KOLD, UCO, SCO, UNG
> and USO extracted from the 8,597-ticker `data/raw/robintrack/popularity_export/` archive, at
> the archive's own ~1 h poll cadence. **What bites a study that reads it unchecked:** the
> timestamps are **UTC** (measured, not assumed — every fund's hour-of-day histogram is flat
> across all 24 hours), so a daily cut at 00:00 UTC lands at 19:00 or 20:00 New York and the last
> poll of a UTC day is *after* the US close; **`holders` is a count of ACCOUNTS**, never shares
> and never dollars, so it says how many people hold and nothing about how much; the **two site
> outages** (152.5 h ending 2019-01-30 and 238.0 h ending 2020-01-16) are present in every one of
> the six files and are **not filled** — `retail_attention.robinhood_holders` returns `None`
> inside them and a study that reads a zero there manufactures the largest flow in its sample;
> and **BOIL's series ends 2020-04-21**, four months before the other five, so a common end date
> is an assumption the fixture does not support. The archive covers 2018-05-02 → 2020-08-13 and
> says nothing about the 2021–2026 retail regime.

> **`data/fixtures/gdelt_hourly_sample.csv.gz`** — GDELT news counts at the hourly scale, D621.
> `source, qid, hour_utc, available_at_utc, n_articles, tone`, 672 rows (48 hours × 14 queries),
> 7,185 bytes, sha256 `bbfd7cf41d49999fdc8cded3145664686c4436cf83f8db02e5da96a7878094aa`.
> **What bites a study that reads it unchecked:** the `source` column is `files_15m_summed` on
> every row — these are D612's 15-minute GKG counts summed to the hour, **not** the DOC API's own
> series, which is deferred because the API answered HTTP 429 and then dropped the connection on
> 2026-09-22 (the block is logged in the meta's `api_state`); the two corpora **are not expected
> to be equal** and must never be summed, which is why the column exists; **this series is hourly
> and the deposit's `headline_burst` needs 15-minute blocks** (its line 265), so it cannot carry
> that feature and `retail_attention.news_n_hourly` will only admit an hourly bucket when a
> caller passes `accept_hourly=True`; and **three of the fourteen keys matched nothing in two
> days** (`henry_hub`, `tk_kold`, `tk_uco`) while `theme_env_oil` alone totals 11,974 documents —
> the four theme keys carry the series and the phrase keys are nearly empty.

### 7b. `CHANGELOG.md` bullet

> - **D621 — retail attention from creations and Robinhood holders (ledger §3.3c line 112,
>   amended).** The deposit's hourly-Wikipedia row is replaced rather than backfilled: D612
>   measured that route at ~2.5 TB for 2016–2023 on a host sustaining 1.79 MB/s, and **a creation
>   is not a proxy for retail demand, it is the quantity `ΔCreate` the deposit's own C3 model
>   predicts.** `data/retail_attention.py` (`creations` differencing against the previous day *in
>   the source*, a daily `creation_z` whose `same_weekday` mode delegates to D612's
>   `zscore_matched` and agrees with it to the last bit on a shared input, a `creation_accel` that
>   *is* `att_accel` on a six-hour axis, a Robinhood reader whose outages are `None` and never
>   `0`, and Spearman + Pearson with a stated tie rule); `robintrack_energy_funds.csv.gz`
>   (115,290 rows, six funds, both site outages named and unfilled, BOIL's early stop recorded);
>   `gdelt_hourly_sample.csv.gz` (672 rows, file-derived). **Measured, over 2018-05-02 → 2020-08-13
>   on the steps where a creation happened: Spearman of Δholders against Δshares is positive at
>   lag 0 on all four ProShares funds (+0.09 to +0.56) and lower at lag +1 than at lag 0 on all
>   four** — holders do not follow creations. **And the two statistics disagree by half on two of
>   them**: UCO reads Spearman +0.556 against Pearson −0.077, carried by 2020-04-20/21 alone.
>   A data-quality measurement, not a signal test: no return, no null, nothing scored. The GDELT
>   DOC API answered **429 and then dropped the connection**; `--api` is built and not run, and
>   the block is logged with its tool and URL. 108 tests.

### 7c. Panel-catalogue rows

For `src/backtest_framework/data/panel_catalogue.py`'s `_ROWS`, in its alphabetical position, and
`data/data_manifest.json` rebuilt alongside (which moves the pinned panel count 128 → **130** in
`tests/unit/test_panels.py`, `tests/unit/test_running_page_figures.py`, the panels golden and its
hand file; both new panels carry no git blob id, so the blob-less count moves 13 → **15** and both
must be named on the running page):

```python
PanelSpec("gdelt_hourly_sample", "data/fixtures/gdelt_hourly_sample.csv.gz", "hour_utc", "iso_ts", "csv", ("available_at_utc",)),
PanelSpec("robintrack_energy_funds", "data/fixtures/robintrack_energy_funds.csv.gz", "ts_utc", "iso_ts", "csv", ()),
```

The wrong-cut column on the GDELT panel is `available_at_utc`, for the same reason
`attention_sample`'s is: it is a *later* instant than the row's own, so cutting on it would admit
rows whose observation lies beyond the seal. The Robintrack panel has one instant and no wrong
cut. Once both rows land, `needs_d621_fixture` in `tests/unit/test_retail_attention.py` should be
replaced by the ordinary `requires_panel` fixture — its docstring says so.

### 7d. The proposed deposit amendment

**§3.3c, its line 112, should read:**

> `| ETF creations (daily Δ shares outstanding) | Daily, from fund inception | Primary: retail demand |`

**and a row should be added beneath it:**

> `| Wikimedia per-article pageviews (REST) | Daily, from 2015 | Secondary: public attention |`

**with a footnote to the table:**

> *Per-article **hourly** Wikipedia pageviews are not available from the Wikimedia REST API,
> which serves daily and monthly only; the hourly route is the `dumps.wikimedia.org` hourly
> files, ~2.5 TB for 2016–2023 (D612's erratum). Hourly pageviews are therefore **not** a source
> of this document, and `wiki_n(h)` in §P3.7 becomes `wiki_n(d)`, daily.*

**§P3.7's raw-series block should become:**

> - `news_n(τ)`: GDELT article count matching the fixed query in the last 60 min. `news_tone(τ)`:
>   mean tone of those articles. *(unchanged)*
> - **`create_n(d)`: the change in shares outstanding of the fund over its previous trading day,
>   from the issuer's published daily share count. Available at `d + 1 day` — the source states no
>   publication time.**
> - `wiki_n(d)`: **daily** pageviews summed over the fixed article list for the completed day.
> - Optional (only if Q12 is resolved): `social_n(τ)`. *(unchanged)*

**and the normalisation and feature block should carry three consequences:**

1. `z_create` joins `z_news` and `z_wiki`. The **daily** series are z-scored against the trailing
   60 days' prior days (all of them); the **hourly** series keep the deposit's same-hour,
   same-weekday rule. The two windows differ because the cycles differ, and `creation_z` carries
   both.
2. **`att_accel` and `headline_burst` stay on the news side only.** Neither can be computed from
   a daily series — three hours against three hours, and 15-minute blocks since 09:30. A daily
   analogue exists as `creation_accel` (three days against three) and is a *different feature*
   with a different name, not the same one at a coarser scale.
3. **Unit test 22 is voided as written** (D612's finding, restated): *"an hourly pageview for
   13:00-14:00 is unavailable at τ = 14:10 and available at τ = 14:15 or later"* has no series to
   test against once the hourly row is gone. D612's implementation and its test remain, because
   the guard is correct and the dump route still exists; what changes is that no feature of this
   document depends on it. **A replacement test on the creation lag is proposed:** *"a creation
   dated `d` is unavailable at any τ before `d + 1 day` 00:00 UTC and available at or after it"*,
   which `tests/unit/test_retail_attention.py::test_the_creation_lag_is_one_full_day_and_unconditional`
   already implements and which can be given a number when the deposit is edited.

### 7e. Numbered deposit tests claimed

**None.** Tests 21–25 are D612's four point-in-time guards and its query-hash rule, and all five
were claimed by D612 in `data/deposit_test_map.json`. **They are not re-claimed here** — a test
claimed twice is a crosswalk that overcounts, and `scripts/deposit_test_map.py --scan` would
report the disagreement.

D621's 108 tests are unnumbered by design: the deposit numbers no test for a creation series,
because the deposit does not yet name a creation series among its raw inputs. **If §7d's
amendment is accepted, the replacement for test 22 named there is the one new number it
generates**, and it already has an implementation to point at.

### 7f. Decision-register row

> | [D621](decisions/D621-retail-attention-from-creations-and-robinhood-holders.md) | 2026-09-22 | Data | Retail attention from creations and Robinhood holders; the deposit's hourly-Wikipedia row amended, GDELT hourly deferred on a 429 |
