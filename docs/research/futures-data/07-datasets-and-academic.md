# 07 — Dataset repositories and the academic world

**Scope of this note.** Free historical intraday CME futures data (ES/NQ/RTY/YM, plus CL/GC/ZB/6E),
15-minute or finer, ideally 10+ years, ideally the full ~23-hour Globex session — searched across
dataset repositories (Kaggle, HuggingFace, Academic Torrents, Zenodo, figshare, Dryad, OSF,
data.world, AWS Open Data, Harvard Dataverse) and the academic-access world (WRDS, replication
packages).

**Date of survey:** 2026-09-01.

**Method note on verification.** Kaggle's web pages are JS-rendered and unreadable to a fetcher, but
its *unauthenticated* metadata API is not:
`https://www.kaggle.com/api/v1/datasets/view/{owner}/{slug}` returns description, `totalBytes`,
`licenseName` and `lastUpdated` verbatim. Likewise HuggingFace exposes
`/api/datasets/{id}`, `/api/datasets/{id}/tree/main/{dir}` (per-file byte sizes) and
`datasets-server.huggingface.co/{first-rows,statistics,size}` (real column names, row counts,
min/max of any column). Everything below marked "verified" was checked through one of those, or by
HTTP range-reading the actual bytes of the file. Everything marked "description only" was not.

---

## Bottom line

There is **no free, licensed, timestamped, 10-year, full-session CME intraday dataset** in any of
these repositories. Not one.

What does exist is a narrow and slightly frustrating result:

- **One dataset has the depth we want and it has had its timestamps deleted.**
  `brkly03/CME-Globex-MDP-3.0` on HuggingFace holds ES, NQ and GC at 1-minute over roughly
  15.5 years of the full Globex session — 4.69M ES bars — and is near-certainly real exchange data.
  Its time column is a sequential integer row index `0,1,2,3…`. There are no dates in the file.
- **One dataset is genuinely usable and is too short.**
  `Khanhpham1992/es-futures-1m` is ES 1-minute, full session, real UTC timestamps, per-contract and
  stitchable — but only 2020-11-17 → 2024-07-19, and ES only. No licence declared.
- **Everything else on Kaggle that looks like futures is CFD data, TradingView scrapes, daily bars
  mislabelled, vendor teasers, or self-scraped broker feeds.** Two of them say so in their own
  description.
- **The research-data repositories (Zenodo, figshare, Dryad, OSF, Dataverse, AWS Open Data) hold
  nothing at all** for US index futures intraday. Academic Torrents holds two finance items total,
  neither of them CME.
- **WRDS is closed to us.** Academic, institution-affiliated, non-commercial only.
- **No mirror of the CME DataMine sample data was found in any repository.**

---

## Ranked: what is worth downloading

| # | Dataset | Verdict |
|---|---|---|
| 1 | `brkly03/CME-Globex-MDP-3.0` (HF) | Download **only** if you are willing to attempt timestamp reconstruction, or want an unaligned distributional cross-check. Do not build on it. |
| 2 | `Khanhpham1992/es-futures-1m` (HF) | **Download.** The only clean, timestamped, full-session, real-looking bars in this entire lane. Use as a 3.7-year ES validation set against whatever primary source we pick. |
| 3 | `tgtanalytics/nq-futures-1min-bar-2022-2025` (Kaggle) | Optional. CC0, 3 years NQ, claims RTH+ETH. Provenance unstated — treat as unverified. |
| 4 | `lynx1231/historical-futures-data-sample` (HF) | Download only to inspect a commercial vendor's field layout. It is a sales sample. |
| — | everything else below | No. |

---

## Tier 1 — the near-miss

### `brkly03/CME-Globex-MDP-3.0`

| field | |
|---|---|
| name + URL | brkly03/CME-Globex-MDP-3.0 — https://huggingface.co/datasets/brkly03/CME-Globex-MDP-3.0 |
| **genuinely free / open?** | Free to download, public, ungated. "Open" is a different question — see licence. |
| instruments, granularity, history depth | **ES, NQ, GC** at **1-minute**. `kronos_dataset/ES_1m_all.csv` 330,678,014 B; `NQ_1m_all.csv` 321,016,652 B; `GC_1m_all.csv` 168,854,559 B. **11,651,112 rows total**; the largest file runs to index 4,685,960, i.e. **4,685,961 ES bars**. ES price starts at 1256.00 and ends at 7605.25, which brackets roughly **Dec 2010 → mid-2026 — about 15.5 years.** NQ starts at 2220.00, consistent with the same start date. |
| **full session or RTH?** | **Full session.** 4.686M bars over ~15.5 years is ~302k bars/year. Full Globex is ~1380 min × ~250 days ≈ 345k/yr; RTH-only would be ~100k/yr. The count is only reachable with the overnight included. |
| licence | **None declared.** No `license` tag, no README (`/raw/main/README.md` → 404), no card data. Given the provenance below, redistribution is very likely not permitted, and *we* have no grant of rights of any kind. |
| provenance — real or scraped? | **Real exchange data, almost certainly.** The repo is named for Databento's dataset code `GLBX.MDP3`, the coverage start (~Dec 2010) matches Databento's GLBX history start (2010-06-06), and the prices are on the correct quarter-point tick grid. This reads as Databento CME Globex MDP 3.0 `ohlcv-1m`, re-uploaded. That also means it is redistributed against the original vendor's terms. |
| verified how | **Byte-level.** Fetched the file tree for exact sizes; `datasets-server` `/statistics` for row count and column min/max; then HTTP range-read the head and tail of `ES_1m_all.csv` and the head of `NQ_1m_all.csv` directly. |

**The defect, stated precisely.** The header is:

```
timestamps,open,high,low,close,volume,amount
0,1256.000000,1257.000000,1255.250000,1256.750000,1766,1766.000000
1,1256.750000,1257.000000,1256.500000,1256.750000,259,259.000000
```

and the last line of the ES file is:

```
4685960,7604.750000,7605.750000,7604.750000,7605.250000,143,143.000000
```

`timestamps` is a **row counter, not a time**. Every date, every session boundary, every
holiday, every roll is gone. `amount` is just `volume` copied — a filler column. This is the input
format of the **Kronos** financial foundation model, which trains on ordered bar sequences and does
not need a calendar; whoever prepared this threw the datetimes away on purpose.

**Can the timestamps be reconstructed?** Only unreliably. You would have to assume the bar sequence
is gapless and re-lay it onto a CME session calendar — but zero-volume minutes in the overnight are
routinely dropped by `ohlcv-1m` aggregation, and every dropped minute permanently desynchronises
everything after it. There is no checksum against which to detect the drift. **Treat this as
unusable for anything that needs calendar alignment** — which is to say, unusable for the
overnight/RTH split, for event studies, for roll handling, and for any walk-forward with real dates.
Its residual value is as an unaligned distributional sanity check (bar-return distributions,
volume profiles) against a source we actually trust.

---

## Tier 2 — the one usable set

### `Khanhpham1992/es-futures-1m` (and its duplicate `msj-21/es-futures-1m`)

| field | |
|---|---|
| name + URL | https://huggingface.co/datasets/Khanhpham1992/es-futures-1m — duplicate at https://huggingface.co/datasets/msj-21/es-futures-1m |
| **genuinely free / open?** | Free and ungated. No licence, so not "open" in any enforceable sense. |
| instruments, granularity, history depth | **ES only**, **1-minute**, **1,280,878 rows**, 282,383,854 B parquet across `es_continuous_1m.parquet` and `es_features_ready.parquet`. **2020-11-17 00:00:00 → 2024-07-19 20:59:00** — 3 years 8 months. **15 distinct `instrument_id` values**, i.e. the quarterly ES contracts over that window, so it is per-contract and stitchable rather than pre-rolled. |
| **full session or RTH?** | **Full session.** 1.28M bars / 3.67 yr ≈ 349k bars/yr, essentially exactly full-Globex coverage. Confirmed at row level: the first rows are 00:00, 00:01, 00:02 UTC (= 19:00 CT, deep in the overnight) carrying real volume of 227, 502, 202. |
| licence | **None declared.** No card, no licence tag on either copy. |
| provenance — real or scraped? | **Real, on strong circumstantial evidence.** Columns are `instrument_id, open, high, low, close, volume, adj_open, adj_high, adj_low, adj_close, datetime`. `instrument_id` is a Databento concept and the value seen (`19100`) is in Databento's GLBX range; prices sit on the correct 0.25 tick grid; overnight volumes are plausible. This is a vendor extract, not a chart scrape. Same caveat as above: no licence was granted to the uploader to redistribute, and none to us. |
| verified how | **Row-level.** `/api/datasets` for the file list and storage size; `datasets-server` `/size` for the row count; `/statistics` for the datetime min/max and the 15-way `instrument_id` cardinality; `/first-rows` for the actual column values. |

Note the two copies are byte-identical in structure and row count — `msj-21` is a re-upload, not an
independent source. Do not treat them as corroborating each other.

The `adj_*` columns are a roll adjustment and are **broken**: `/first-rows` on the `msj-21` copy
returns `adj_open = -2246.0` against `open = 3624.5`. The adjustment has been applied with the wrong
sign or the wrong base, producing negative prices. Use the raw `open/high/low/close` and roll it
yourself.

---

## Tier 3 — usable-ish, provenance unknown

### `tgtanalytics/nq-futures-1min-bar-2022-2025`

| field | |
|---|---|
| name + URL | https://www.kaggle.com/datasets/tgtanalytics/nq-futures-1min-bar-2022-2025 |
| **genuinely free / open?** | Yes — Kaggle, free account, **CC0 Public Domain** as declared. |
| instruments, granularity, history depth | **NQ only**, 1-minute OHLCV plus a pre-computed VWAP. **~1.05M rows, 2022-12-26 → 2025-12-11.** Metadata `totalBytes` reported as 19,141,759 in the list endpoint and 72,522,264 in the view endpoint — two different versions; current is the larger. |
| **full session or RTH?** | **Full session, per the description**, which states it covers both Regular Trading Hours and Extended Trading Hours. 1.05M rows / 3 yr ≈ 350k/yr independently corroborates full Globex coverage. |
| licence | CC0 as declared by the uploader. Note: an uploader cannot CC0 data they did not have rights to in the first place, so this tells you about their intent, not about our actual position. |
| provenance — **unstated**. The description says nothing about where the bars came from. No exchange, no vendor, no methodology. It also warns you to "account for contract rollovers and slippage", implying it is a stitched series of unspecified construction. |
| verified how | **Metadata only** — Kaggle API `view` and `list` endpoints. I could not read the file contents; Kaggle file access requires an authenticated account. Session coverage is inferred from the row count and the uploader's own claim, not seen. |

Good enough for a cross-check on NQ over three years. Not good enough to be a primary source, because
you cannot tell whether it is exchange bars or a chart export.

### `lynx1231/historical-futures-data-sample`

| field | |
|---|---|
| name + URL | https://huggingface.co/datasets/lynx1231/historical-futures-data-sample |
| **genuinely free / open?** | Free, but it is explicitly **a sales sample** — "a free evaluation sample of historical futures data". The full product (2,000+ roots, 900M observations) is sold at `futuresforexandsomeindexes.com`. |
| instruments, granularity, history depth | 40 contracts across 8 roots — **CL, ES, GC, SB, SR3, VX, ZC, ZN** — being the newest 5 contract symbols per root. Two configs: `daily` and `minute`. 105,584,088 B. Depth not stated; "newest 5 contracts" implies roughly the last 1–2 years per root. |
| **full session or RTH?** | Not stated. The README does note minute data uses **DST-aware `America/Chicago` wall-clock** rather than UTC, which is at least a sign of competent handling. |
| licence | **None.** The README specifies no usage rights for the sample or the full product. |
| provenance — real or scraped? | Commercial vendor's own claim of exchange data; no independent verification available, and the vendor is not a name I can corroborate. Unverified. |
| verified how | **README and file metadata.** Read `/raw/main/README.md` verbatim plus `/api/datasets` for storage and config layout. Did not read the bars. |

Worth 10 minutes to inspect the minute-file schema — the Chicago-wall-clock convention is the one we
want. Not worth building on.

---

## Tier 4 — checked and rejected, with reasons

These matter because Kaggle's titles are systematically misleading. Each of these *looks* like what
we want in a search result.

| Dataset | Size / licence | Why it fails |
|---|---|---|
| `bpwqsdd/us-futures-1-minute-candlesticks` — https://www.kaggle.com/datasets/bpwqsdd/us-futures-1-minute-candlesticks | **4.75 GB**, licence Unknown | **The author disqualifies it himself.** Full description: *"array of Candle class with o,h,l,c,t values, saved with pickle. ended up using cfds because the futures data was not correct"*. It is **CFD** data, not futures, in a pickled Python class. The largest "US futures" set on Kaggle by an order of magnitude, and it is not futures. |
| `mlippo/futures-market-dataset` | 799,927 B, CC0 | **MetaTrader 5 CFD index products**, not exchange futures — "Usa500", "UsaTec", "UsaRus", "Ger40" etc. The description concedes some series were "sourced from monthly contracts due to MetaTrader5 limitations". |
| `youneseloiarm/nasdaq-cme-future-nq` | 1,265,360 B, CC0 | Description states the data was **"obtained from TradingView"**. 1.2 MB across 1-minute through monthly means the 1-minute slice is only whatever TradingView's chart window returns. Scraped, shallow. |
| `youneseloiarm/nasdaq-future-data` | 3,153,405 B, Unknown | Same uploader, same approach, no licence. |
| `choweric/cme-es`, `cme-nasdaq`, `cme-euro`, `cme-jpy` | 383 KB / 353 KB / 677 KB / 585 KB, CC BY-SA 4.0 | **Daily bars, not intraday.** 383 KB cannot hold 22 years of intraday anything. Per-contract OHLC + volume + open interest, 2000–2022. Well-made and honestly documented (open interest lagged one day to avoid lookahead) — and useless for our purpose. |
| `sentinelx/s-and-p500-1min-historical-data` | 10,983,798 B, "Apache 2.0" | **An advertisement.** Description is a pitch — sample period 2025-10-02 → 2026-04-03 only, with the full 2008-present set sold at an external shop link. Six months, and it is "SPX500", i.e. a CFD symbol, not ES. |
| `finnhub/sp-500-futures-tick-data-sp` | ~50 MB (list) / 481 MB (view), "Other (specified in description)" | Claims S&P futures **tick** 2000–2019. That is the **SP** pit contract, not ES. 481 MB for 20 years of tick is off by two or three orders of magnitude — it is not tick data as the word is normally used. Vendor-restricted licence. Last updated 2020. |
| `brtnsmth/intraday-market-data` | **8.28 GB**, CC0 | Honest and explicitly **self-scraped**: *"3-second interval price data from TD Ameritrade's ThinkorSwim platform, captured via Excel RTD interface and SQL Server"*. RTD polling snapshots are not exchange bars — volume and OHLC are approximations of whatever the terminal happened to display. Covers Sunday 18:00 → Friday 18:00 ET so session coverage is right; history is short (weekly captures, recent). Interesting as a construction, unusable as a reference. |
| `tednovak/1m-mes-11-23` | 82,231,813 B, Unknown | ES/MES 1-minute, roughly Nov 2023 → Nov 2024. **One year**, no description, no licence, no provenance. |
| `dougeedavis/futures-15-minute-data` / `dougeedavis/fifteen-minute-nq-futures-data` | 7,635,921 B (CC0) / 611,252 B (GPL 2) | Right granularity, wrong scale. Empty descriptions, no provenance, no stated range. 611 KB of 15-minute NQ is a couple of years at most. |
| `wentinglu/highfrequency-futures-data-china`, `alphonsezhu777/china-financial-futures-1-minute-data`, `cccheung/hsifutures`, `brunotavares/ibovespa-emini-future-contracts`, the `lusfernandotorres/*` Brazilian series | various | Wrong exchanges — China, Hong Kong, Brazil. Noted only to record that Kaggle's non-crypto futures inventory is largely non-US. |
| `Francois/futures_es` (HF) | **0 bytes** | Empty repository. Contains `.gitattributes` and nothing else. `usedStorage: 0`. |
| `getdatafinance/*oil-1m-*` (Kaggle) | 0.5–2.4 MB, MIT | Teaser samples for `getdata.finance`. "USOIL"/"UKOIL" are CFD symbols, not CL/BZ. |

---

## Repositories that returned nothing

### Academic Torrents — https://academictorrents.com
Searching `futures` returns **"Nothing found!"** Searching `tick` returns exactly two items, only one
of which is financial: **10 years of Dukascopy Forex Tick Data (2008-2019)**, 475 files, 65.03 GB,
added 2021-02-21
(https://academictorrents.com/details/8baee145786f4311b66bea5d13ef30eedce04a24). That is a
**retail broker's FX feed** — Dukascopy's own aggregated spot quotes, not exchange data, and not
CME 6E. It has some marginal relevance as an FX proxy and none for the index complex. The only other
finance item on the site is a US stock end-of-day set scraped from Google Finance.
**AT hosts no CME futures data.** *(Verified by browsing the live search pages; the site's
anti-bot interstitial blocks plain fetchers, so this required a real browser.)*

### Zenodo — https://zenodo.org
Two independent queries (`futures intraday high-frequency`; `"index futures" AND (minute OR intraday
OR "high-frequency")`). Zenodo does hold genuine intraday futures deposits — but all of them are the
wrong markets: 1-minute B3 (Brazil) DI and USD futures around US macro announcements
(10.5281/zenodo.22167087, 10.5281/zenodo.22119345, CC-BY-4.0), Chinese commodity futures
2022–2023 (10.5281/zenodo.15726389, 171 MB), Chinese futures and A-share minute data 2012–2022
(10.5281/zenodo.22217961, ~150 MB), and a Hyperliquid crypto L4 order book set (~116 GB). **Nothing
for CME.** Warning for anyone repeating this search: querying Zenodo for `"E-mini"` returns
taxonomy papers, because *emini* is a species epithet — `Cricetomys emini`, `Thrinchostoma emini`,
`Gonimbrasia emini`. And `CME` matches "cystoid macular edema".

### Dryad — https://datadryad.org
`futures intraday minute` → **0 results.** The one adjacent item found via Zenodo's aggregation is
Dryad 10.5061/dryad.g4f4qrfr2, 1-minute Euro Stoxx 50 and FTSE 100 prices for a causal-coupling
study — **11 KB**, European indices, CC0. Not usable.

### figshare, OSF
No financial futures intraday data surfaced. figshare's article search is dominated by biomedical
supplementary material; OSF's project index for "futures" returns social-science work on
*futures thinking*, not markets.

### Harvard Dataverse — https://dataverse.harvard.edu
One relevant hit: *"The difference in the intraday return-volume relationships of spot and futures:
a quantile regression approach"* (doi:10.7910/DVN/MCOVPQ). It is an analysis deposit — regression
output — not the underlying bars, and the market is not US.

### AWS Open Data Registry — https://registry.opendata.aws
**No financial market data of any kind.** The registry is scientific, environmental and geospatial.
The only business-adjacent entry is an Amazon logistics routing challenge.

### data.world
**Dead.** The Open Data Community was retired on **2026-07-13** and the site now states that the
open data community datasets are "no longer accessible or available for download". Cross it off
permanently.

### Google Dataset Search, Azure Open Datasets
Not separately reachable within this session's search budget. Both are metadata indexes over the
repositories already covered above rather than independent hosts, so the marginal return is low —
Google Dataset Search primarily indexes Kaggle, HuggingFace, Zenodo, figshare and Dataverse, all of
which were queried directly here.

---

## WRDS (Wharton Research Data Services)

**Not available to us, and not the right data anyway.**

| field | |
|---|---|
| URL | https://wrds-www.wharton.upenn.edu/ |
| **genuinely free / open?** | **No.** Institutional subscription only. |
| Who gets an account | Standing faculty, full-time research staff, currently-enrolled PhD students, and full-time Masters (and at some schools undergraduate) students **at subscribing institutions**. Research assistants and visiting scholars are at WRDS's discretion. There is **no individual tier**, no trial for unaffiliated people, and no public pricing — WRDS sells annual institutional contracts through its own interface, and a faculty member with funding must go through "Contact WRDS Support" even to get a sample. |
| Licence / permitted use | Terms of Use restrict WRDS to **academic and non-commercial research**; users may not use downloaded data "for any non-academic or commercial endeavor". A private trading strategy is squarely a non-academic endeavour. Even with access, using it to build this book would breach the terms. |
| Does it even have what we need? | **Not really.** WRDS's intraday strength is **TAQ (US equities)** and the derived "Intraday Indicators by WRDS", which is NYSE/TAQ-based. Futures come in via **Datastream/Refinitiv** — ~140,000 commodity series from 1951 and futures prices from 1972, but at **daily** frequency. Genuine intraday futures would come via **LSEG/Refinitiv Tick History**, which is a *separate, additionally-licensed* product that many WRDS subscribers do not carry, and which universities typically wrap in further restrictions. |
| verified how | WRDS Terms of Use plus the eligibility statements published by several subscribing libraries (NYU, Columbia, Berkeley, Tulane, GWU, FSU, USF, Yale). Description-level; I have no account. |

**Conclusion: a non-affiliated private researcher has no route into WRDS.** If you ever acquire an
affiliation, the useful product is LSEG Tick History (via a university library, e.g. Yale's guide at
guides.library.yale.edu/LSEG_Tick_History), not WRDS core — and the non-commercial restriction
would still bind.

---

## Replication packages

**Nothing found, and there is a structural reason.**

I could not locate a single replication package for an intraday US index-futures study that ships the
underlying bars. This is expected rather than bad luck: intraday CME data reaches academics through
**TAQ-equivalents, LSEG/Refinitiv Tick History, Tick Data LLC, or CME DataMine**, every one of which
forbids redistribution. So the standard deposit for these papers is *code plus derived estimates* —
regression tables, realised-variance series, event-window aggregates — with a data-availability
statement pointing you back at the paid vendor. The Harvard Dataverse hit above is exactly this
pattern, and so are the Zenodo B3 and Chinese deposits (those are redistributable only because the
Brazilian and Chinese exchanges permit it, which CME does not).

The corollary is worth stating plainly for the project file: **if a free full-history intraday CME
dataset existed anywhere legitimate, the academic literature would already be using it, and it would
be cited constantly. It is not. That absence is itself evidence.**

---

## CME DataMine sample data — is it mirrored anywhere?

**No mirror found in any dataset repository.** Searched Kaggle, HuggingFace, Academic Torrents,
Zenodo and AWS Open Data specifically for it.

The relevant facts:

- CME's **Packet Capture Dataset** (raw MDP 3.0 pcap) is documented on the CME client wiki
  (`cmegroup.com/confluence/display/EPICSANDBOX/Packet+Capture+Dataset`, and the per-channel pages
  such as Channel 490), but obtaining a sample requires **setting up an S3 account and then emailing
  `CMEDataSales@cmegroup.com`**. It is gated on a human at CME, not a download link.
- What *is* freely mirrored is **tooling, not data**: `CMEGroupPublic/datamine_python` (CME's own
  DataMine client), `vincent212/CME-Market-Data-Handler` (C++ MDP 3.0 pcap reader),
  `epam/java-cme-mdp3-handler`, `PeregrineTradersDevTeam/md-data-reader-cme` (pcap → Parquet).
  These are all decoders waiting for a pcap you do not have.
- Even if a sample were obtained, DataMine samples are **days, not years** — they exist to let you
  test a decoder, not to backtest.

Note also that the one HuggingFace dataset *named* `CME-Globex-MDP-3.0` (Tier 1 above) is **not**
DataMine sample data — it is aggregated 1-minute bars with the timestamps stripped, and the naming
appears to be a nod to the Databento dataset code rather than to CME's own product.

---

## Incidental finding, likely another agent's lane

`nexusfi.com` (formerly futures.io) hosts a large free **NinjaTrader Market Replay** archive —
tick-level `.nrd` files by contract for ES, NQ, CL, YM, ZB, ZN, TF, 6E, FDAX, FESX and others,
40 pages of listings, ~99 MB per part with multi-part archives per contract. Registration is
required to download, and the note on each entry says *"the archive contains only the dates with the
most volume for this contract, meaning, this is data relevant only to when the contract becomes the
front month"* — which is actually the right slice for a stitched front-month series. Format is
NinjaTrader-proprietary and would need conversion. Flagging it because it did not obviously fall
inside my brief and it is the largest free tick archive I encountered anywhere in this survey.

---

## What this lane changes about the project's options

1. **Rule out the dataset-repository route as a primary source.** It has been searched properly now.
   The ceiling here is ~3.7 years of ES (Tier 2) or 15 years with no dates (Tier 1).
2. **`Khanhpham1992/es-futures-1m` is worth having anyway** as an independent 2020–2024 ES
   cross-check against whichever primary source we choose — it is full-session, real-timestamped,
   per-contract, and almost certainly vendor-sourced. Cheap insurance against a silent bug in our
   own ingest.
3. **`brkly03/CME-Globex-MDP-3.0` is a lesson, not a resource.** It is the shape of the thing we
   want, ruined by one preprocessing decision. If a timestamped version of the same extract ever
   surfaces, it would be a direct hit.
4. **The licence position is uniform across every real-data candidate found here: absent.** None of
   Tier 1, 2 or 4's genuine-looking sets declares a licence, and the ones that declare CC0 are
   uploaders asserting rights they probably do not hold. For private research on our own machine
   this is a low practical risk, but nothing in this lane can support anything published or sold.
5. **WRDS and the academic route are closed** without an institutional affiliation, and closed by
   terms-of-use even with one, for a commercial trading application.
