# 06 — Open source, GitHub, and backtesting frameworks that ship data

Research date: 2026-09-01. Lane: public repos, framework-bundled datasets, awesome-lists,
open-source downloaders, academic replication packages.
Requirement being tested: ES/NQ/RTY/YM (+ CL, GC, ZB, 6E), 15-minute or finer, 10+ years,
full ~23-hour Globex session, continuous or stitchable.

---

## VERDICT FIRST

**No public repo, framework bundle, or open-source project ships 10+ years of intraday CME
futures bars. Not one. Every "framework with bundled data" bundles either daily futures or
intraday equities — never both at once.**

The three headline candidates all fail, and they fail for different reasons:

| Candidate | Why it fails |
|---|---|
| **pysystemtrade** (Carver) | Ships ~200 real futures series with real depth (SP500 back to **1982**) — but the committed files are **daily**. Verified by reading the CSVs: every timestamp is `23:00:00`. There is no intraday directory in the repo at all. |
| **QuantConnect LEAN** (local) | Ships ES minute bars — **16 scattered days** between 2013-10-06 and 2020-01-06. It is a file-format demo, not a dataset. Verified by listing `Data/future/cme/minute/es`. |
| **QuantConnect cloud, free tier** | Genuinely gives you futures at minute resolution back to 2009 — but **only inside their cloud backtester**. The free tier explicitly cannot download data. The bars can never reach this repo. |

**The one thing my lane does deliver is a legitimate, free, 16-year, 1-minute, near-24-hour
proxy series — from HistData.com, wrapped by a well-maintained open-source downloader.**
It is CFD data, not CME futures: bid-only quotes, no volume. Whether that is usable is a
modelling decision, not a data-availability one. Details in §1.

---

## RANKED — what is worth cloning

| # | Project | Verdict |
|---|---|---|
| 1 | **philipperemy/FX-1-Minute-Data** → HistData.com | **Clone it.** The only free path in this lane to 10+ years of sub-15-min, near-full-session bars for ES/NQ/CL/GC/6E analogues. CFD proxies, no volume. |
| 2 | **Leo4815162342/dukascopy-node** → Dukascopy | **Clone it second.** Same idea, tick-level, and it is the only free source that covers a **YM** and an **RTY** analogue. Real history depth for the US indices is unverified and probably shallower than advertised. |
| 3 | **QuantConnect cloud free tier** | Worth an account **only if** you are willing to run research inside their IDE. Real CME futures, minute res, 2009→. Zero export. |
| 4 | **pysystemtrade** | Clone for the **roll/stitching code and the roll calendars**, not the prices. Its `roll_calendars_csv` and carry logic are the best free reference implementation of continuous-contract construction that exists. |
| — | Everything else | Nothing usable. See §5. |

---

## 1. HistData.com via `philipperemy/FX-1-Minute-Data` — the only real find

| field | |
|---|---|
| repo / project | https://github.com/philipperemy/FX-1-Minute-Data — data from https://www.histdata.com/ |
| **data included or just a client?** | **Client / downloader.** Repo is 52 KB of Python; it commits no bars. It also links a ~3 GB pre-built Google Drive mirror. |
| instruments | Index CFDs **SPXUSD** (S&P 500), **NSXUSD** (Nasdaq 100), UDXUSD (Dollar index), UKXGBP, GRXEUR, ETXEUR, JPXJPY, AUXAUD, FRXEUR, HKXHKD. Commodities **WTIUSD**, BCOUSD, **XAUUSD**, XAGUSD. Plus 66 FX pairs incl. **EURUSD**. |
| granularity | **1-minute OHLC** (and tick-level for a subset). Trivially resampled to 15-min. |
| history depth | **SPXUSD and NSXUSD: 2010 → August 2026.** Verified directly on the HistData download pages — full-year archives listed 2010–2025 plus monthly files Jan–Aug 2026. FX pairs go back to May 2000. |
| **full session or RTH?** | **Near-full session, but NOT verified by inspection.** These are OTC index CFDs which quote roughly Sun 18:00 → Fri 17:00 ET with a short daily break — i.e. structurally the Globex window. HistData's own FAQ warns of gaps averaging >90 seconds in thin periods. **You must confirm the actual bar timestamps after downloading one month.** I did not download. |
| licence | Effectively none stated. FAQ says only *"Since it's free data, you'll not get from us any kind of warranty or certification."* No explicit redistribution grant. Treat as free-to-use, do-not-redistribute. Downloader repo itself is Apache-2.0. |
| stars / maintenance | **681 stars, 171 forks, last push 2025-05-04, not archived.** Alive. |
| verified how | Fetched the HistData SPXUSD and NSXUSD 1-minute download pages and read the year lists. Fetched the instrument index page (site self-reports `DataFiles Last Updated at: 2026-08-31`). Fetched the repo README and the GitHub API metadata. **Did not download or open a bar file.** |

### What this actually covers against the requirement

| Wanted | HistData analogue | Depth |
|---|---|---|
| ES | SPXUSD | 2010 → now ✅ |
| NQ | NSXUSD | 2010 → now ✅ |
| RTY | — none | ❌ |
| YM | — none | ❌ |
| CL | WTIUSD | 2010 → now ✅ |
| GC | XAUUSD | 2010 → now ✅ |
| ZB | — none | ❌ |
| 6E | EURUSD | 2000 → now ✅ (spot EURUSD tracks the 6E future near-exactly) |

### The three things that will bite you

1. **No volume.** HistData's FAQ is explicit: forex/CFD volume is broker-specific, so the
   volume column is absent or zero. Any strategy using volume, VWAP, or volume-based bars
   is dead on arrival with this data.
2. **Bid quotes, not trades.** These are quote midpoints/bids from a retail aggregator,
   not CME matched trades. Microstructure-sensitive work is invalid.
3. **Timestamps are EST with no DST adjustment.** Per the FAQ. You must shift by hand to
   align to CME session boundaries, and the offset changes twice a year relative to CT.

---

## 2. Dukascopy via `Leo4815162342/dukascopy-node`

| field | |
|---|---|
| repo / project | https://github.com/Leo4815162342/dukascopy-node — docs at https://www.dukascopy-node.app/ |
| **data included or just a client?** | **Client only.** Downloads from Dukascopy Bank's public tick archive. |
| instruments | US index CFDs: `usa500idxusd` (ES), `usatechidxusd` (NQ), **`usa30idxusd` (YM)**, **`ussc2000idxusd` (RTY)**, `dollaridxusd`, `volidxusd`. Energy: `lightcmdusd` (CL), `brentcmdusd`, `gascmdusd`, `dieselcmdusd`. Plus metals, 800+ FX/stocks/ETFs. |
| granularity | **Tick**, aggregatable to m1/m15/m30/h1/d1 by the tool. |
| history depth | Site-reported earliest dates: usa500 **1980-01-02**, usatech **1990-11-07**, usa30 **2013-01-01**, ussc2000 **2018-08-08**, lightcmd **1983-04-20**. **Treat the 1980/1983/1990 figures as instrument metadata, not tick availability.** Dukascopy's actual tick archives for index CFDs realistically begin around 2010–2013. Unverified — I could not confirm without downloading. |
| **full session or RTH?** | Dukascopy CFD sessions are near-24×5. Unverified by inspection. |
| licence | Tool is MIT. Data is Dukascopy's, provided without a redistribution grant; the project states it is "not affiliated, endorsed, or vetted by Dukascopy Bank SA." |
| stars / maintenance | Actively maintained, many forks (`knusul`, `nova-land`, `sandi2382`, `siwtom`, `flowxcode` all mirror it). |
| verified how | Fetched `dukascopy-node.app/instruments/idx_america` and `/instruments/cmd_energy` and read the earliest-date tables. Did not download data. |

**Why it ranks second despite being tick-level:** it is the *only* free source in this lane
carrying a YM and an RTY analogue. But the RTY proxy starts 2018 (7 years, short of the
10-year target) and the YM proxy starts 2013. Its headline history depths are the least
trustworthy numbers in this whole document.

---

## 3. QuantConnect — cloud yes, local no

### 3.1 LEAN local sample data — a format demo, nothing more

| field | |
|---|---|
| repo | https://github.com/QuantConnect/Lean, `Data/future/` |
| **data included or just a client?** | Data included — but trivially small. |
| instruments | `Data/future/` has directories for cbot, cfe, **cme**, comex, eurex, hkfe, ice, krx, nymex, nyseliffe, sgx. Under `cme/minute/` there is exactly **one** symbol: `es`. |
| granularity / depth | ES minute, **16 distinct dates**, each with trade/quote/openinterest zips: 20131006–20131011, 20131014, 20131029–20131030, 20131118, 20131202–20131203, 20131218, 20131220, then a two-file jump to 20200105–20200106. Individual trade files are **1–21 KB**. |
| **full session or RTH?** | Irrelevant at this size. LEAN's format uses milliseconds-since-midnight for intraday. |
| licence | Apache-2.0 (engine). Sample data is AlgoSeek-sourced, demo only. |
| stars / maintenance | Very alive (LEAN is one of the largest OSS quant engines). |
| verified how | **Listed the actual directory via the GitHub API and read the filenames and byte sizes.** This is a hard verification, not a README claim — the README says "quotes, trades, and open interest data from AlgoSeek across six exchanges", which is technically true and wildly misleading about volume. |

### 3.2 QuantConnect cloud free tier — real data, zero export

Verified from https://www.quantconnect.com/pricing:

- Free tier **does** include the data library: "Equity, Indexes, Forex, Crypto, **Futures**,
  Options Data" with **unlimited backtesting**.
- Resolution on free tier: **minute, hour, daily**. Tick and second require a paid plan.
- Futures coverage (AlgoSeek US Futures dataset): **~70 most liquid contracts, tick→daily,
  since 2009.**
- **Free tier cannot download data.** Local data via QCC tokens starts at the Quant
  Researcher tier. Free tier gets 1 backtest node, 1 research node, 500 MB workspace,
  32 KB per file.

**Implication:** this satisfies the *data* requirement (ES/NQ/RTY/YM, minute, 2009→, full
session) and fails the *portability* requirement completely. It is only useful if the
backtest itself moves into QuantConnect's cloud. `lean data download` against
QuantConnect's own dataset market costs QCC credits per file and is not free.

There is a side door worth noting: LEAN CLI supports third-party historical data providers
(e.g. Interactive Brokers) as the download backend, which is how people get free-ish futures
data *into* a local LEAN install. That inherits the broker's depth limits — see doc 02.

---

## 4. pysystemtrade — clone the roll logic, ignore the prices

| field | |
|---|---|
| repo | https://github.com/robcarver17/pysystemtrade |
| **data included or just a client?** | **Data included, and a lot of it** — ~200 CSV files, 46 KB to ~11 MB each, in `data/futures/multiple_prices_csv/` plus `adjusted_prices_csv`, `fx_prices_csv`, `roll_calendars_csv`, `crypto_spread_roll_calendars_csv`. |
| instruments | Very broad: SP500, DOW, NASDAQ, DAX, CAC, EUROSTX, BUND, US bonds, EURIBOR, GOLD, SILVER, COPPER, CRUDE_W, BRENT_W, NATURAL_GAS, CORN, WHEAT, SOYBEAN, LEANHOG, COCOA, COFFEE, COTTON, all major FX, aluminium/zinc/nickel/tin, BITCOIN, ETHEREUM. |
| granularity | **DAILY. This is the killer.** |
| history depth | Excellent — `SP500.csv` starts **1982-09-14**. |
| **full session or RTH?** | N/A — one bar per day, stamped `23:00:00`. |
| licence | GPL-3.0 (engine). Prices are IB-derived and Carver's own; no redistribution grant is asserted for the data. |
| stars / maintenance | Very alive; Carver actively develops it and blogs at qoppac.blogspot.com. |
| verified how | **Read the raw `SP500.csv` directly.** Header is `DATETIME,CARRY,CARRY_CONTRACT,PRICE,PRICE_CONTRACT,FORWARD,FORWARD_CONTRACT`; every row is one calendar day at `23:00:00`. Also listed `data/futures/` via the GitHub API to confirm **there is no hourly or intraday directory of any kind**. |

Carver's production system stores hourly bars pulled live from Interactive Brokers into
Arctic/MongoDB — those are *not* committed to the repo, and IB's own 2-year expired-futures
ceiling (doc 02) means he could not have deep intraday history to share even if he wanted to.

**What is genuinely worth taking:** `roll_calendars_csv` and the multiple/adjusted price
machinery. The `PRICE_CONTRACT` / `FORWARD_CONTRACT` / `CARRY_CONTRACT` triplet layout is a
clean, battle-tested schema for continuous-contract stitching with carry, and the roll
calendars encode real roll dates per instrument. That is reusable regardless of where the
bars come from.

---

## 5. Verified dead ends

Each of these was checked against actual file listings or explicit documentation, not README
prose.

| Project | What it actually has | Verified how |
|---|---|---|
| **backtrader** (`mementum/backtrader`, `datas/`) | 22 files, all equities: nvda/orcl/yhoo daily 1995–2015, plus 2006 minute samples of an unnamed index. **No futures.** Largest file 1.8 MB. | Listed `datas/` via GitHub API |
| **TheSnowGuru/Stocks-Futures-…-Tick-Bar-Data** | Dukascopy CFD exports (`USA500IDXUSD_M15.csv` etc., 11.5 MB) — but **2013-05-23 to 2019-12-27 only**, and last push 2024-09. Name promises futures; contents are CFDs, 6.5 years, stale by 7 years. 46 stars, MIT. | Listed dirs; **read the D1 file's first and last rows** to get the exact date range |
| **FutureSharks/financial-data** | Data lives in `pyfinancialdata/data/{cryptocurrencies,currencies,stocks}` — and `stocks/` contains only a `histdata` folder. It is a **thin re-wrapper of HistData**, superseded by §1. Its README's "S&P 500" is SPXUSD, 2010–2018. | Walked the directory tree via GitHub API |
| **Microsoft qlib** | `get_data.py` fetches CN and US **equity** data from Yahoo, 1d and 1min. Columns are open/close/high/low/volume/factor. **No futures collector.** | Docs + repo README |
| **nautilus_trader** | Databento **adapter**, not data. Ships only tiny DBN test fixtures. Getting real futures bars means paying Databento. | Docs + example scripts |
| **vectorbt** | No bundled data at all; pulls from yfinance/ccxt at runtime. | — |
| **zipline / zipline-reloaded** | Futures support in the DataPortal has been broken/incomplete for years (issues #1429, #1781, #2347, #2705, #2789 — `KeyError: ContinuousFuture` on custom futures bundles). Stock bundles are equities-only. **Do not build on this for futures.** | Issue tracker |
| **norgatedata** | Client only, requires a paid Norgate subscription. And decisively: **Norgate is EOD-only** — "does not provide live quotes, delayed quotes, intra-day or 'tick' data." Their futures package (100+ markets, some to the 1980s, adjusted + unadjusted continuous) is excellent *daily* data and irrelevant here. | Norgate FAQ |
| **yfinance** | Confirms the established finding and sharpens it: `ES=F` etc. **do** return intraday, but Yahoo caps intraday at **60 days** for 2m/5m/15m/30m and ~7–8 days for 1m. 15-min ES is available — for two months. Not a corpus. | yfinance docs + issue #2451 |
| **pandas-datareader** | No futures intraday path. | awesome-quant listing |
| **awesome-systematic-trading** (paperswithbacktest) | Mined the Data Sources section: yfinance, TuShare, AkShare, pandas-datareader, Quandl, findatapy, investpy, plus crypto feeds. **Zero free futures intraday sources listed.** | Read the README |
| **awesome-quant** (wilsonfreitas) | Mined Market Data section. Futures/commodity entries are: oilpriceapi (spot oil/gas), Trading Strategy (DeFi), FXMacroData (FX), and `lse-data`. | Read the README |
| **londonstrategicedge/lse-data** | The one awesome-quant entry claiming futures. It is a **client for a commercial platform**, MIT-licensed code, requires an API key. History is US stocks to 2003, FX to 2009 — **futures depth is not stated**. Data terms forbid redistribution. Has a free tier; worth a 10-minute look but it is a commercial API, not open data. | Read the README |
| **keithcheungowl/SP500Futures** | README claims 13.8 M rows of SP tick data 2000–2019. Repo contains **three files: a README, an 82 KB xlsx, and a 631 KB notebook.** The CSV is not committed. **Textbook README overstatement.** | Listed repo root via GitHub API |
| **robertmartin8/research**, **Jackal08/financial-data-structures** | ES samples used for López de Prado dollar-bar demos — **1 year and 20 days** respectively, from Tick Data LLC. Illustrative only. | Search results + repo descriptions |
| **SDGDGFSDAD/NQ_FUTURES_1_MIN_PREDICTION** | **Repo returns HTTP 404** — deleted or made private since it was indexed. Unverifiable. | GitHub API 404 |
| **michaelsmusing/sources-for-intraday-…** | A curated list of intraday sources. Contains **no free futures entry**; futures vendors listed (CQG, eSignal) are paid. | Read the README |
| **Hugging Face** | Searched for CME futures bar datasets. Found crypto-futures and US-equity minute datasets (`mito0o852/OHLCV-1m`, 1992–2026 stocks) but **no ES/NQ CME minute dataset**. | Search |
| **Kaggle** | Two NQ datasets exist (`tgtanalytics/nq-futures-1min-bar-2022-2025`, `youneseloiarm/nasdaq-cme-future-nq`). Depth is **3 years, not 10**. Session coverage, contract construction, and licence are **undocumented on the dataset page** — I could not confirm any of them. Provenance is anonymous. Low trust. | Attempted fetch; page returned only the title |

### Why GitHub does not have this data

Two structural reasons, worth recording so this lane is not re-litigated:

1. **File size.** 10 years of 1-minute full-session bars for one CME instrument is roughly
   3.5 million rows, ~150–250 MB uncompressed. GitHub warns at 50 MB and hard-blocks at
   100 MB per file without LFS. Anyone with this data cannot casually commit it — which is
   exactly why the repos that *claim* it (keithcheungowl) turn out not to have it.
2. **Licence.** CME market data is licensed, and redistribution of derived bars is
   restricted. Vendors who resell it (FirstRate, Portara, Kibot, Databento, AlgoSeek) have
   contracts that forbid public mirroring. The data that *is* freely mirrorable is precisely
   the data nobody licensed from CME — i.e. OTC CFD feeds like HistData and Dukascopy.

Those two facts together predict the result found: **the free intraday index data that
exists is CFD data, and the real CME data that exists is behind a paywall or a cloud IDE.**

---

## 6. Recommendation

1. **Download one month of HistData SPXUSD 1-minute and open it.** This is the single
   highest-value next action in this lane and it costs ten minutes. The three unknowns that
   decide everything — actual session coverage, gap density, and whether the volume column
   is zero or absent — are all answered by looking at one file. If the bars span ~23 hours
   with tolerable gaps, you have a free 2010–2026 15-min corpus for ES/NQ/CL/GC/6E analogues.
2. **If step 1 passes, pull the full SPXUSD + NSXUSD + WTIUSD + XAUUSD + EURUSD archives**
   via `philipperemy/FX-1-Minute-Data`. Accept that RTY, YM, and ZB have no coverage here,
   and that nothing has volume.
3. **Take pysystemtrade's `roll_calendars_csv` and its multiple/adjusted price schema** as
   the reference design for continuous-contract stitching, whatever the bar source ends up
   being. Do not take its prices.
4. **Test the Dukascopy `usa30idxusd` and `ussc2000idxusd` tick archives** only if YM and
   RTY are load-bearing for the strategy. Expect their real history to start well after the
   advertised dates.
5. **Open a QuantConnect free account only if** running the backtest in their cloud is
   acceptable. It is the only free source in this lane with genuine CME futures minute bars
   back to 2009, and the data can never leave.

**The honest summary of this lane: it produced one usable proxy dataset and one reusable
piece of stitching code. It did not produce CME futures bars.**

---

## Appendix — sources

- https://github.com/robcarver17/pysystemtrade — `data/futures/`, raw `SP500.csv`
- https://github.com/QuantConnect/Lean — `Data/future/`, `Data/future/cme/minute/es`, `Data/future/readme.md`
- https://www.quantconnect.com/pricing
- https://www.quantconnect.com/docs/v2/writing-algorithms/datasets/algoseek/us-futures
- https://github.com/philipperemy/FX-1-Minute-Data
- https://www.histdata.com/ — 1-minute instrument index, SPXUSD page, NSXUSD page, FAQ
- https://github.com/Leo4815162342/dukascopy-node — https://www.dukascopy-node.app/instruments/idx_america, /cmd_energy
- https://github.com/mementum/backtrader — `datas/`
- https://github.com/TheSnowGuru/Stocks-Futures-Financial-Time-series-Tick-Bar-Data
- https://github.com/FutureSharks/financial-data
- https://github.com/microsoft/qlib
- https://github.com/nautechsystems/nautilus_trader — `docs/integrations/databento.md`
- https://github.com/wilsonfreitas/awesome-quant
- https://github.com/paperswithbacktest/awesome-systematic-trading
- https://github.com/londonstrategicedge/lse-data
- https://norgatedata.com/data-package-faq.php
- https://github.com/keithcheungowl/SP500Futures
- https://github.com/ranaroussi/yfinance — issue #2451
- quantopian/zipline issues #1429, #1781, #2347, #2705, #2789
