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

**111.0 GB, 129 files, `temp/databento/<job-id>/*.dbn.zst`.** Databento `GLBX.MDP3` under a
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

### Four things that will bite a study reading this

1. **NOT COMMITTED, AND CANNOT BE.** CME's terms forbid redistributing archived data, so
   the bars live in gitignored `temp/`. What *is* committed is the re-fetch script, the
   manifest, the verification artifact and the hashes. `temp/` is deletable by contract —
   **this data is re-downloadable free only until roughly 2026-10-11**, 30 days after each
   job completed. After that it is a fresh purchase.
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
| `temp/databento` | 129 | 111 GB | **the futures, above** |

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
