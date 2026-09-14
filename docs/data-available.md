# Data available

**Inventory taken 2026-09-12, measured from disk rather than recalled.** What exists, what
it covers, where it lives, and — for each — the thing that will bite a study that reads it
without checking.

> **This is an index, not a licence.** Several fixtures carry holdout status, adjustment
> quirks or licence restrictions that decide whether a given study may read them at all.
> Those constraints live in [`RULES.md`](RULES.md), [`FINDINGS.md`](FINDINGS.md) and each
> fixture's own `.meta.json`, and this page defers to them.

---

## 1. CME futures — NEW, acquired 2026-09-11/12

**111.0 GB, 129 files, `data/raw/databento/<job-id>/*.dbn.zst`.** Databento `GLBX.MDP3` under a
one-month CME Standard subscription. Every job quoted **$0.00** against **$7,719** at
published per-schema rates; the only cost was the $199 subscription.

| schema | scope | window | on disk | files |
|---|---|---|---:|---:|
| `ohlcv-1m` | **every instrument** | 2010-06-06 → 2026-09-10 | 12.22 GB | 26 |
| `mbo` full order book | ES NQ RTY YM CL GC ZN ZB | 2026-08-11 → 2026-09-10 | 39.39 GB | 26 |
| `tbbo` trade + quote before it | **every instrument** | 2025-09-11 → 2026-09-11 | 37.30 GB | 13 |
| `statistics` OI, settlements | 41 roots | 2010-06-06 → 2026-09-11 | 10.87 GB | 17 |
| `bbo-1m` quoted spread | 41 roots | 2025-09-11 → 2026-09-11 | 8.00 GB | 13 |
| `definition` roll calendar | 41 roots | 2010-06-06 → 2026-09-11 | 2.67 GB | 17 |
| `status` halts, auctions | 41 roots | 2010-06-06 → 2026-09-11 | 0.56 GB | 17 |

**"Every instrument" means every instrument** — each contract month, each calendar spread
and each option on a future, not one stitched continuous series. That is where term
structure and carry would come from, and it is also why a naive load is not a panel.

**Verified, not assumed** ([`futures_acquisition_verification.json`](../data/futures_acquisition_verification.json)):
129/129 byte counts match Databento's manifest, 129/129 sha256 hashes match, 16/16 DBN
headers state the requested dataset and schema, and the ten `ohlcv-1m` slices **tile
2010-06-06 → 2026-09-10 with zero interior gaps and zero overlaps.**

**Committed fixtures built over it:** `fut_sessions_hourly.csv.gz` (D467, hourly session tables,
nine roots, 2016 →); **`fut_open_interest_daily.csv.gz` (D497: daily root-total open interest and
cleared volume for ES, NQ, CL, GC from the `statistics` schema, keyed on the session each figure
is first USABLE — published strictly before a 10:00 ET entry; 100% coverage, staleness one session,
builder `scripts/build_fut_open_interest.py`, 3.3 min). **CORRECTED 2026-09-13 by [D521](decisions/D521-the-three-remaining-flat-id-builders-are-ported-and-the-open-interest-fixture-was-carrying-a-phantom-CL-contract.md) — re-pull any CL total you cached before that commit.** The builder used a **FLAT `{instrument_id: symbol}` lookup** (the D520 defect) and it did bite here: instrument 42007396 was `6AF4` until 2024-01-21 and was reissued as `CLG36` in November, so the flat dict counted **an Australian-dollar contract as a 61st crude contract on 2024-01-03 … 2024-01-19**, overstating `oi_total` by 235–401 contracts (0.014–0.026%). `oi_front` was never touched — the volume rule protects it — which is exactly why the CURVE, read from `oi_total` and `oi_n_contracts`, was the exposed part. Now windowed; the other three roots and every other session are unchanged and all 63 gate scalars are identical. And **2025-07-28 is a bad session**: ES, GC and NQ simultaneously report 326, 9,158 and 82 contracts of total open interest with truncated strip counts — a one-day source dropout, unrelated to the mapping; drop it or treat it as missing. What bites: `ts_ref` is the session START,
**AND THE `statistics` SCHEMA CARRIES A SECOND MISSING-VALUE SENTINEL THAT NOTHING FILTERS — [D526](decisions/D526-the-curve-story-fails-stage-0-the-level-is-a-regime-and-the-change-carries-nothing.md).** `UNDEF` is `INT64_MAX` and every builder here filters it. **Zero is a second marker**: a settlement price of exactly `0.0` appears on **646 occasions** across CL and GC in 2016-2023 alone (CL 344, GC 302, every year, concentrated in deferred months like `CLF30`…`CLF35`). It is positive-adjacent, so no existing guard catches it — and **the fix cannot be "drop non-positive", because CL legitimately settled −37.63 on 2020-04-20.** Drop exact zeros, keep genuine negatives. The same caution applies to any `stat_type` read from this schema, not just settlements. What bites: `ts_ref` is the session START,
the evening BEFORE the trade date it describes, so a naive read is off by a day; open interest for
trade date T is first published ≈ 21:00 ET on T itself; and a per-contract series must drop expired
months or the root total carries dead open interest forever;** and **`fut_micro_flow_5m.csv.gz` (D485: signed 5-minute order flow of ES/MES
and NQ/MNQ from `tbbo`, exchange aggressor side, front month per session, 259 sessions
2025-09-11 → 2026-09-10; gates T1–T5 in its meta; builder `scripts/build_fut_micro_flow.py`,
3.3 min on 8 processes).** What bites: the ohlcv-1m span ends one session before the tbbo span,
so session 2026-09-10 cannot be cross-checked; nine holiday sessions are absent by the presence
rule and listed. And **`fut_{ES,NQ,YM,RTY}_rth_1m.csv.gz` + `fut_index_sessions.csv.gz` +
`fut_index_rolls.csv.gz` (D462: the index day session at ONE MINUTE, 09:30–15:59 ET, front month by
full-day volume, no stitching and no adjustment; ES/NQ/YM 2010-06-07 →, RTY 2017-07-10 →; builder
`scripts/build_fut_index_1m.py`, 6.2 min on 6 workers). **ALL GATES PASS as of D522** — RTY joined
the committed set there, having failed G4 on a single session until the gate was amended.** What
bites: **usable from 2016-01-04 for ES/NQ/YM** (G5 — the archive carries the evening bars but not
the day session on most earlier days: 21% coverage in 2010, 89% in 2015), and the **three
circuit-breaker sessions of March 2020 (09, 12, 16) have no continuous open** — one print at 09:30
and nothing until 09:45 — so an open-to-close study must drop them or read the open at 09:45.

And the two **breadth** fixtures, which cover **36 roots** rather than a hand-picked few:
**`fut_breadth_hourly.csv.gz`** (the hourly day session, 170,643 root-sessions, 2010-06-07 →;
builder `scripts/build_fut_breadth_hourly.py`; it is the source of the windowed `ids_of` and of
the front-month election every later futures fixture inherits) and **`fut_day5m.parquet`**
(the same 36 roots at **FIVE minutes**, 10,384,830 bars over 135,179 root-sessions, 84 bars per
full session in the 09:00–15:59 ET window, 98 MiB; builder `scripts/build_fut_day5m.py`, decode
88 min then a 2-minute build). It exists because 7 hourly bars pin a non-overlapping past/future
pair to H=3 and one observation per session; 84 bars fit the pair at every H in {3,4,6,8,12,16,20}.
It takes the front month and the `same_front`/`present` flags from the hourly fixture **by inner
join, not re-derived**, so the two cannot disagree about the front (the join keeps 26.5% of 39.2 M
raw bars; the rest are back months). Its **135,179** root-sessions are fewer than the hourly
fixture's **170,643** because the hourly session is 18:00→16:59 and counts sessions that have
overnight bars but nothing inside the day window; the 5-minute fixture holds only sessions with at
least one 09:00–15:59 bar. The 35,464-session gap is **front-loaded exactly where the archive gap
is** — 4,223 in 2011 and 3,665 in 2012 against ~1,600 a year from 2016, heaviest on CL, YM, ES, NQ,
NKD and HO — and no day5m session lies outside the hourly fixture, the inner join being exact.

**What bites, and the meta carries all of it computed rather than asserted.** *(i)* **A root's
SPAN IS NOT ITS USABLE SPAN, and it fails in two different ways that one flag cannot tell apart**,
so `coverage.per_root` reports both: `first_full_bars_year` (the root's own session band ≥90%
populated) and `first_clean_year` (that **and** ≥240 sessions). **ES, NQ and YM read 2011 / 2016** —
the early sessions that exist have *complete* bars and there are merely few of them (ES holds 33
sessions in 2010, 73 in 2011, 113 in 2012, 212 in 2013, 258 from 2016), which is a wholly different
object from **SR3 in 2020: 257 sessions with no five-minute slot present in more than 38% of them**
(SR3 is clean only from 2022). Others: the six FX roots, GC HG SI UB ZB ZF ZN ZT **2010/2011**; the
five grains **2013/2014**; BZ 2015; CL HE HO LE NG NKD PL RB TN **2016**; RTY 2018; BTC 2020; and
**PA NEVER** — palladium tops out at 0.80 fill and carries intermittent interior slots.
*(ii)* **The band is per root, measured not assumed:** 84 slots 09:00–16:00 for the 23-hour
markets, **58 at 09:30–14:20 for the five grains, 55 at 09:30–14:05 for livestock**. A study
applying the 84-slot window to ZC silently reads 26 empty slots.
*(ii-b)* **AND THE WORSE CASE IS THE ROOT WITH FULL BARS AND DEAD VOLUME — [D530](decisions/D530-avenue-3-closed-the-leveraged-ETF-reset-flow-is-real-and-carries-no-direction-and-16-of-36-roots-do-not-trade-in-the-day5m-close.md).**
The grains are obviously empty; **crude is not**. Share of each root's session volume in the
**15:00–15:59** hour, against the 14.3% an evenly-traded root would show: **RTY 21.1%, ES 20.4%,
NQ ~18%, YM 15.7%** (the equity closing hump, 1.10–1.48× even) · UB/TN/NKD/BTC/ZF/ZT/SR3 9.8–14.4% ·
ZN 11.0%, ZB 11.6% · the six FX 6.6–8.3% · **GC 5.4%, SI 4.4%, NG 3.9%, CL 3.1%, HG 2.6%** ·
PL/HO/PA/RB/BZ 2.7–3.4% · **LE and HE 0.02% on 18–19 sessions** · **ZC ZS ZW ZL ZM 0.00%, zero bars.**
COMEX metals close 13:30 ET, NYMEX energy 14:30, grains 14:20, livestock 14:05 — so **16 of 36 roots
have that hour essentially outside their market while still returning bars**. A close measured in an
illiquid tail bounces on the spread, and **bid-ask bounce is indistinguishable from mean reversion**:
D530 got a spurious **z = −12.6 "closing reversion"** across 19 such roots before checking this.
**Any cross-root study on this fixture must use each root's OWN session, not the 09:00–15:59
template** — and note that every price-action statistic computed over the template on a commodity
root in this programme, D515's CL and GC rows included, carries the same contamination.
*(iii)* **`present=False` does NOT mean the bar is missing.** All **443,124** such rows carry real
OHLC and **non-zero volume**; zero have a NaN close. It is the *hourly* fixture's session flag,
`isfinite(hourly_open × hourly_close)` over the root's h09..h15 window, so it marks holidays,
half-days and thin sessions — 6A on 2010-07-05 trades 29 contracts in the opening bar. 8,349 of
135,179 root-sessions (6.2%), heaviest on RB NG HO CL. `same_front=False` marks 4,408 root-sessions,
the rolls, and a return across that boundary is a roll rather than a move.

### Six things that will bite a study reading this

1. **NOT COMMITTED, AND CANNOT BE.** CME's terms forbid redistributing archived data, so
   the bars live in gitignored `data/raw/databento/`. What *is* committed is the re-fetch
   script, the manifest, the verification artifact and every hash.
   **It is re-downloadable free only until roughly 2026-10-11**, 30 days after each job
   completed; after that it is a fresh purchase at $7,719 of published rates.

   > **It was first written to `temp/databento/` and moved on 2026-09-12.** `temp/`'s own
   > README says *"if deleting a file would cost something, it does not belong here"*, and
   > 111 GB on a 30-day re-fetch clock costs plenty. `data/raw/` is the repo's established
   > home for a gitignored raw cache — D191, cache the raw and commit the derived.
2. **The last session is missing.** The pull ends **2026-09-10**, not 2026-09-11. The final
   bars slice was resubmitted with a backed-off end while chasing a stall. Any study
   quoting "through 2026-09-11" is wrong by one session.
3. **Prices are UNADJUSTED and there is no continuous series.** Databento: *"the continuous
   contract prices returned are the original, unadjusted prices."* These are raw symbols, so
   there is no roll at all yet — the roll calendar must be built from `definition`, and
   [`futures_continuous.py`](../scripts/futures_continuous.py) plus its acceptance gates
   exist for exactly that.
4. **`ohlcv-1m` arrived in TEN jobs, not one.** Two wide jobs stalled and were split. The
   slices tile cleanly, but a loader must read all ten directories, and the job-to-window
   map is in the manifest rather than inferable from filenames.
5. **FILTERING TO "FRONT MONTH" NEEDS ID *WINDOWS*, NOT AN ID SET.** ES trades its deferred
   contract thinly for months before the roll, so a mask of the form
   `isin(instrument_id, front_month_ids)` admits **two expiries at once**, priced ~60 index
   points apart — the calendar basis. This bit twice on 2026-09-12, in
   [`d465`](../scripts/d465_es_spread_and_mae_bias.py) and again in
   [`d469`](../scripts/d469_scalping_feasibility.py):

   - **Only 3.9% of records were wrong, and it moved a published number by ~1 pp**, because
     the statistic was a **running max**. A max reads the extremes, so a *sparse* contaminant
     dominates it. Per-record measurements (a spread reads bid and ask off the same record)
     were barely touched; anything walking a path across records was wrecked.
   - The tell was **a p99 that did not move with the horizon** — 240 ticks at 10 s and at
     15 min alike, against a median of 2. A constant tail across horizons is a basis, not
     a move.
   - **Clip every id to its own date window, then assert at most one `instrument_id` per
     second**, and drop any pair whose two ends are different contracts. Both scripts now
     carry that gate and prove it fires.

   > **AND IT BITES IN THE OTHER DIRECTION TOO — [D520](decisions/D520-the-sessions-builder-labelled-bars-from-a-flat-id-dict-and-it-was-ingesting-a-quarter-million-foreign-bars-that-never-reached-the-panel.md).**
   > A `{instrument_id: symbol}` dict built from `store.metadata.mappings` with the
   > `start_date`/`end_date` discarded is the same defect wearing the opposite hat: an id is
   > **not** a stable handle on a contract. CME reuses the single-digit-year slot at expiry
   > (`CLN9` is July-2019 then July-2029) *and* rotates a live contract onto a new id — but the
   > large term is that an id which is one of your outrights in one window is an **option, a
   > calendar spread or a different product** in another, for which no window exists at all.
   > Measured over the whole `ohlcv-1m` archive on nine roots: **229,206 of 77,151,155 bars
   > (0.297%, and 4.31% on the worst file)**, including 79,479 bars of Micro AUD/USD labelled
   > `6EF3` and spreads at **negative prices** labelled `NQM3`. **Build the windows, label each
   > bar from the window containing its timestamp, and raise if one id's windows overlap** —
   > `scripts/build_fut_breadth_hourly.py` and `scripts/build_fut_sessions_hourly.py` both do.
   > A front-by-volume rule happens to be insulated (the reused slots are the months nothing
   > trades), **except on a holiday**, where ten spurious contracts elected the euro's front
   > month on 2021-12-24.
   >
   > **[D521](decisions/D521-the-three-remaining-flat-id-builders-are-ported-and-the-open-interest-fixture-was-carrying-a-phantom-CL-contract.md) finished the job: NO builder in the repository labels a bar from a flat dict any
   > more**, and the three it ported were rebuilt and diffed. `fut_micro_flow_5m` and all six
   > `fut_index_1m` outputs came back **byte-identical** — the index build ingested **16,077
   > foreign RTH bars (0.229%, 18 of 26 files)** and the front-by-volume rule dropped every
   > one, insulated exactly as above. **`fut_open_interest_daily` did NOT**: it is the one
   > fixture here with a column that has no volume filter in front of it (`oi_total`), and it
   > was wrong on 12 CL sessions. **The rule of thumb: front-month columns are insulated,
   > totals and strip counts are not.**
   >
   > **AND THE FLAT DICT IS NOT DETERMINISTIC — [D524](decisions/D524-the-day5m-fixture-verifies-clean-and-a-flat-id-dict-is-non-reproducibly-wrong.md).**
   > `store.metadata.mappings` iterates in a different order in every process, so "the last
   > write wins" picks a different winner each run: on the 2019 file **all 8 ambiguous ids get a
   > different label depending on the process** (8 of 8 over six hash seeds, 0 appearing stable
   > against 0.25 expected by chance) — id 73454 reads the Nikkei `NKDU0` five times and then
   > **silver `SIF9`** on the sixth, so a five-read probe would have called it stable. The
   > *count* of mislabelled windows is stable; the
   > *identities* are not. Two flat-dict builds of the same code over the same archive therefore
   > produce **different fixtures**, and **a flat-built fixture cannot be reproduced or audited
   > after the fact** — distrust any pre-D520 flat-built artefact beyond the rows a diff happened
   > to catch. The exposure is far larger on the **36-root** list than on the index roots:
   > **29 mislabelled outright windows and 14,139 foreign windows**, against **0 and 712** for
   > ES/NQ/YM/RTY. `fut_day5m` itself verifies clean: rebuilt byte-identical, and its 5-minute
   > bars fold into the hourly fixture with **0 differences across 906,905 root-session-hours**
   > in o/h/l/c/v **and trade count**.

6. **THE ENERGY DAY SESSION IS NOT IN THE ARCHIVE BEFORE JUNE 2015** (D520, extending D462's
   index-futures finding). **CL, NG, RB and HO** carry the same pre-2016 gap on hours 21→14 ET
   that ES/NQ/YM do, **and additionally lose 15:00–16:59 ET entirely until 2015-06**: in 2013
   the front contract's bars run out at **14:30–15:17 ET** and hour 15 is populated on **0 of
   308 days**, against 250 for GC, SI, ZN, ZB and 6E, which are complete from 2010. The
   switch-on is abrupt — 0–7 days a month carry an h15 bar through May 2015, then **22 in June
   2015**. BZ is unaffected, and GC had a pit and is complete, so "pit-traded products" is not
   the rule; the mechanism is unknown and the coverage is the fact. Anything computing a
   day-session statistic on the energy complex must start at 2015-06 or later, and
   `fut_sessions_hourly`'s G5 already gates CL to 2016-01-04.

### Compression measured per schema, and it spans 10x

`status` 27.99x · `definition` 29.39x · `statistics` 5.24x · `ohlcv-1m` 4.21–4.92x ·
`bbo-1m` 4.05x · `tbbo` 3.09x · `mbo` 2.89x

**Never apply one schema's ratio to another.** Doing so once would have under-reserved disk
by roughly tenfold; see [`decode_pipeline_bench.json`](../data/decode_pipeline_bench.json).

### Reading it costs more than it looks

Profiled on this machine: **zstd decompression is the bottleneck at 754 MB/s per core,
while the numpy parse runs 8,755 MB/s** — the DBN format is nearly free to read and the
decompression is the whole cost. One worker consumes 254 MB/s of compressed disk read, so
twelve workers want ~3 GB/s. Against 31.7 GB of RAM and a ~200 GiB universe, **this is
out-of-core work**: studies stream rather than load once.

### Not bought, and why

`mbp-1` (212 h of download, and `tbbo` answers the spread question) · `mbp-10` (Databento's
own docs say derive it from `mbo`) · `ohlcv-1s` (excluded by the principal; 1-minute only) ·
`definition`/`statistics` at full universe (520 B per instrument **per day** traded or not —
496 GiB, larger than the bars) · `bbo-1m` at full universe (**3,190 GiB**, 12.5 GiB/day,
because it snapshots every option strike every minute).

**Path resolution is a staircase:** 2010–2025 is 1-minute only, the last 12 months are
trade-by-trade, the last month is order-by-order.

---

## 2. US equities and ETFs — committed fixtures

`data/fixtures/*.csv.gz`, each with a `.meta.json` and usually an `_events.json`.
**`ragged_panel.py:76-111` refuses to load any fixture whose meta lacks a passing `gates`
block** — that is the chokepoint, not a convention.

### Single names, daily

| fixture | names | rows | span |
|---|---:|---:|---|
| `us_shorts_daily_raw` | **1,573** | 4.14 M | 2010-01-04 → 2026-08-26 |
| `us_shorts_daily_holdout` | 803 | 2.16 M | same |
| `us_shorts_daily_holdout2` | 576 | 1.53 M | same |

**Both daily holdouts are SPENT** — 2026-09-10, by the D412–D433 second-zone line. The
touch effect reproduced at +10/+10/+13 bp gross on three name sets and net Sharpe was ~0 on
all three. **Never re-read these fixtures for that construction.** Holdout spend is per
line, though: a holdout spent by an unrelated strategy is still unseen by a new one, so
this is not a blanket ban.

### ETFs

| fixture | symbols | rows | span | session |
|---|---:|---:|---|---|
| `etf_wide_daily_raw` | **551** | 2.22 M | 2010-01-04 → 2026-08-26 | daily |
| `etf_intraday_15m_raw` | 57 | 3.19 M | 2018-01 → 2026-08 | **regular hours only** |
| `index_extended_15m_raw` | 4 (SPY QQQ IWM DIA) | 0.96 M | 2010-01 → 2026-08 | **extended 04:00–19:45** |
| `wide_extended_15m_raw` | 11 | 2.44 M | 2010-01 → 2026-08 | extended |
| `universe_daily_2015_2024_raw` | 57 | | 2015 → 2024 | daily |
| `universe_holdout_daily_raw` | 60 | 0.15 M | | daily |
| `universe_wide_w1/w5_raw` | ~96 / ~95 | | | daily |

**The 15-minute and daily fixtures disagree on corporate-action basis** — 15m is fully
adjusted, daily is not. That has already put one name at 5x its own prices, and
`raw_price_factor` cannot repair a spinoff. Check the basis before crossing them.

### Intraday cohorts

`cohort3` (8 names, 0.45 M rows) · `cohort4` (24, 1.35 M) · `single_name_intraday_15m_raw`
(8, 0.45 M) · `holdout_intraday_15m_raw` (16, 0.90 M) — all 15-minute, 2018-01 → 2026-08.

### Crypto

`crypto_universe_2015_2025_raw` (63 coins, daily) · `crypto_binance_15m_raw` (25 MB, 15m,
2017 → 2026) · 30m and 1h slices · `crypto_book_2018_raw`.

### Positioning — the one price-free, fully committable series

`cftc_cot_raw`: **28 symbols, 210,717 rows, 1986-01-15 → 2026-08-25.** US government public
domain, so unlike every CME product here it may live in the repo. Commercial /
non-commercial / non-reportable open interest per contract. See [`cftc_cot.md`](cftc_cot.md).

---

## 3. Raw caches — gitignored, re-fetchable

| cache | files | size | what |
|---|---:|---:|---|
| `data/raw/alphavantage` | 50,886 | 1,584 MB | every 15-min and daily slice ever pulled; a cached slice is never re-fetched, so a run resumes |
| `data/raw/edgar` | 1,592 | 1,088 MB | SEC filings behind the 8-K and insider lines |
| `data/raw/binance` | 279 | 486 MB | crypto |
| `data/raw/cftc` | 84 | 21 MB | COT |
| `data/raw/databento` | 129 | 111 GB | **the futures, above** |
| `data/raw/robintrack` | 8,597 + archive | 4.0 GB | **Robinhood holder counts, hourly, 8,597 tickers, 2018-05-02 → 2020-08-13** (the Barber–Huang–Odean–Schwarz data); two ~10-day site outages ending 2019-01-30 and 2020-01-16; 959 / 512 / 341 names overlap the three daily fixtures; the 504 MB `.tar.gz` from robintrack-data.ameo.design is kept beside the extraction. Re-fetchable while the mirror lives; treat as not |

---

## 4. Reference data committed alongside

[`futures_contract_specs.json`](../data/futures_contract_specs.json) — multiplier, tick size
and tick value for 29 CME products, read from CME's own contract-spec service. **The 4% MLL
is a dollar limit, so a path in index points is unusable without this.**

[`cme_product_census.json`](../data/cme_product_census.json) — all 1,592 listed CME futures
products by open interest. **1,069 carry zero open interest**; only 246 carry 1,000
contracts or more; the 41-root buy list is 92.3% of all CME futures open interest.

Plus ~622 committed JSON artifacts in `data/` holding the numbers decision records quote.

---

## 5. What is still missing

- **No futures fixture yet.** 111 GB of DBN sits decoded-by-nobody. The next phase needs the
  seven validation gates in [`fetch_futures_1m.py`](../scripts/fetch_futures_1m.py) reworked:
  they were written for a *continuous stitched* series and this is *raw-symbol full-universe
  across seven schemas*, so the roll gates do not transfer.
- **No equity options.** [D84](decisions/D84-options-scoping-writeup.md) scoped it: chain data
  at 100–1000x volume plus 6–10 weeks of engine surgery for the expiry lifecycle.
- **Nothing pre-2010-06-06 on futures.** `GLBX.MDP3` starts there; it does not exist to buy.
- **No `mbo` before 2017-05-21** even inside the subscription — that is the schema's own start.
