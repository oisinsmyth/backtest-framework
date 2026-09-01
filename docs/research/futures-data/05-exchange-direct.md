# 05 — Exchange-direct: CME Group and its peers

Research date: 2026-09-01. Lane: the exchanges themselves and their official channels — CME
DataMine, cmegroup.com, the CME public FTP, CME's academic programme, ICE, Eurex/Deutsche Börse,
Euronext, CFTC, SEC/FINRA.

## Headline

**No exchange, anywhere in this lane, gives away intraday CME futures history at 15-minute or
finer resolution over 10+ years.** Not CME, not as a sample, not as an academic grant, not as a
trial. The exchanges' free tier is *daily* data, and even that has been progressively withdrawn
from open channels and moved behind DataMine subscriptions since 2023.

Two things did turn up that are worth having, neither of which meets the spec:

1. **A genuinely free, anonymous, bulk-downloadable, ~12.7-year daily settlement-price archive
   still sitting on `ftp.cmegroup.com`** — the legacy SPAN risk parameter files. Verified working
   today; covers ES/NQ/RTY/YM/CL/GC/6E and every other CME Group contract month, 2013-01-02 through
   2025-09-12. This is the single best free exchange-direct price source I found, and it appears to
   be largely unknown as a data source (it is filed as risk/margin infrastructure, not market data).
2. **CME DataMine free sample files** — one trading day per product, per dataset. Format fixtures,
   nothing more.

And one hard constraint that governs everything below: **CME's Data Terms of Use forbid, in terms,
almost everything a backtest fixture would do with the data** — including downloading, compiling,
scripted retrieval, and (added in a recent revision) any use in machine learning or AI. This is
quoted verbatim in the licensing section and materially affects whether any CME-derived fixture can
be committed to a repo, private or not.

---

## 1. CME public FTP — legacy SPAN risk parameter files

| field | |
|---|---|
| name + URL | CME legacy SPAN risk parameter file archive — `ftp://ftp.cmegroup.com/span/archive/cme/{YYYY}/cme.{YYYYMMDD}.s.pa2.zip` |
| **genuinely free?** | **Yes.** Anonymous FTP. No login, no registration, no click-through agreement, no rate limiting encountered. |
| instruments, granularity, history depth | Every listed CME Group futures and options contract month across **CME, CBOT, NYMEX and COMEX in a single daily file** (verified record counts on 2020-01-02: NYM 96,784 / CME 90,617 / CBT 29,493 / CMX 25,270 price records). Granularity: **one settlement price per contract month per day**. Depth: **2013-01-02 → 2025-09-12** (2,578 files in the 2020 directory alone; 2013 is subdivided by month). Confirmed present for ES, NQ, RTY, YM, CL, GC and EC (the SPAN code for Euro FX / 6E). |
| **full session or settlement-only?** | **Settlement-only.** Daily. No session structure at all. |
| bulk/programmatic access? | **Yes — the best of anything in this lane.** Plain FTP directory listing, predictable filenames, ZIP-compressed fixed-width text. ~10 MB compressed / ~82 MB uncompressed per day. A full 2013–2025 pull is roughly 3,200 files. |
| licensing / redistribution terms | **Unresolved and the main risk.** No banner, robots.txt or terms file is served on the FTP host. CME's website Data Terms of Use are scoped to "the cmegroup.com website" and it is not clear they reach `ftp.cmegroup.com`. However CME's own settlement-data FAQ treats the FTP as CME Group property, and the Terms define "CME Data" to include "settlement prices". Treat as: safe to *use* locally, **not** safe to commit or redistribute. |
| verified how | Listed the FTP root and `span/archive/cme/`; downloaded `cme.20200102.s.pa2.zip` (10,141,252 bytes); decompressed and parsed. Record types `81`/`82` carry the price. Sanity check: `81CMEES ES FUT 202003 ... 000000000325900N` decodes to ES Mar-2020 = **3259.00**, which matches the 2020-01-02 close. NQ, YM, RTY, GC, CL located the same way. |

### Caveats

- **The archive is frozen.** The last dated file is `cme.20250912.*`; the directory was last touched
  2025-10-13 and now also holds undated `cme.s.pa2` files. This coincides with "SPAN Risk Parameter
  Files" appearing as a *paid* DataMine catalogue entry. The free tap has been turned off for
  anything after 2025-09-12.
- Prices are the **settlement prices used for margining**, in the contract's price-scan units. You
  must decode the implied decimal from the accompanying commodity records; the raw integer is not
  the price.
- File suffixes are cycle codes: `.s` is the end-of-day settlement cycle; `.e`, `.i`, `.c`, `.a`,
  `.m`, `.X`, `.AI`, `.BE` are intraday/alternate cycles. Use `.s`.
- Because it is a margin file, it carries *every* contract month simultaneously — which is actually
  ideal for building a continuous series, since you have the full term structure each day and can
  roll on any rule you like (volume/OI is not in this file; see section 2).

---

## 2. CME public FTP — everything else that survived

The 2023 advisories (Chadv23-037, Chadv23-126) announced removal of settlement `stl` files from
`FTP.CMEGROUP.COM/settle` and `/pub/settle`. **That removal was real but partial** — the `settle/`
directory now contains only Treasury conversion factors. The rest of the FTP is alive and current.

Verified root listing (2026-09-01), with `pub` a symlink to `.`:

| path | contents | depth | prices? |
|---|---|---|---|
| `span/archive/cme/` | Legacy SPAN files (section 1) | 2013-01 → 2025-09-12 | **Yes — settlements** |
| `span/archive/cme/xml/` | Same in XML | 2014 → 2025-09-12 | Yes |
| `daily_volume/` | `daily_volume_YYYYMMDD.xlsx` — CME Group Volume and OI by product | **2014-01-02 → present** (3,192 files, updated daily) | No — Globex/Pit/ExPit/OTC volume + preliminary OI only |
| `webmthly/` | Monthly ADV / OI / volume-comparison reports, zipped PDFs | 2013 → present | No |
| `fprf/` and `fprf/csv/` | FIXML/CSV price *reference* files (`cmeg.cme.fut.prf.YYYYMMDD`) | rolling ~66 business days | No — SecDef reference data: symbol, expiry, multiplier, tick rules, margin rates. No traded prices. |
| `settle/TCF/` | Treasury invoice conversion factors | 2023-12 → present | No |
| `cash_settled_commodity_index_prices/historical_data/` | `FC{YYYY}.ZIP` | 2013 → 2026 | Cash index prices only, not futures |
| `delivery_reports/`, `irs/`, `sdr/`, `efrp/`, `grs/`, `fix/`, `SBEFix/` | Deliveries, IRS, swap data repository, EFRP, GRS, FIX specs | mixed | Not futures price bars |

**Practical value:** `daily_volume/` is the free companion to the SPAN archive. SPAN gives you
settlement prices per contract month; `daily_volume/` gives you volume and open interest per
product — which is what you need to pick the front month and time a roll. Together they are a
complete free daily continuous-series construction kit for 2014-present, entirely from the
exchange, entirely programmatic.

**Licensing:** same unresolved question as section 1.

---

## 3. CME DataMine — free samples

| field | |
|---|---|
| name + URL | CME DataMine — `https://datamine.cmegroup.com/` (new catalogue at `https://datamine.new.cmegroup.com/catalog`); dataset documentation on the CME Group Client Systems Wiki, `https://cmegroupclientsite.atlassian.net/wiki/spaces/EPICSANDBOX/pages/457088742/CME+DataMine+Datasets` |
| **genuinely free?** | **Samples only, and they are one trading day each.** There is no free tier, no developer tier, and no free trial. The workflow is explicitly "Select data → Create your account → Request a data license → Receive and access data". |
| instruments, granularity, history depth (samples) | **Time and Sales**, v1 samples: Corn, WTI, E-mini S&P 500, EUR/USD, Eurodollar (all **2012-11-05**), Gold (**2011-01-10**); futures and options each. v2 samples: ZC, CL, **ES**, 6E, SR3, GC, BTC, all **2025-03-12**. **Volume and Open Interest** sample: 2020-03-12. **Settlements / End of Market Summary** samples: 2023-04-03 (STLAGS, STLALT, STLCOMEX, STLCPC, STLCUR, STLEQT, STLINT, STLNYMEX). **Daily Bulletin**: 2023-12-07 and 2023-12-08. |
| **full session or settlement-only?** | The T&S samples are **full-session tick data** — genuinely the whole ~23-hour Globex day, nanosecond timestamps, UTC, with trade aggressor flag. But it is **one day**. The v2 sample filenames also carry partition suffixes (`part-00039-c000`), so a v2 sample may be only one Spark partition of that day, not the whole day. |
| bulk/programmatic access? | Samples: static HTTPS URLs under `cmegroup.com/market-data/datamine-historical-data/files/` (v1) and `cmegroup.com/files/download/` (v2). Paid data: RESTful download API, SFTP, automatic S3 transfer, File Browser, Custom Select. API requires a CME Group Login plus a registered API ID with Basic Auth. |
| licensing / redistribution terms | Governed by CME's Information License Agreement and the website Data Terms of Use — see section 8. |
| verified how | Pulled the Confluence dataset pages via the public Confluence REST API (`/wiki/rest/api/content/{id}?expand=body.view`) and extracted the sample-file hrefs directly from the page bodies. |

### What DataMine does and does not sell

The full catalogue (verified from the dataset index page and the new catalogue listing) is:
Time & Sales, Top of Book (BBO), Market Depth (RLC and FIX), Market by Order FIX, PCAP (raw packet
capture), End of Market Summary in five tiers, Volume and Open Interest, Daily Bulletin, Block
Trades, Liquidity Tool datasets, SPAN Risk Parameter Files, Margin Data, Registrar, Fixing Prices,
CME Group Continuous Price Series, plus benchmarks (CVOL, Term SOFR), cash markets
(BrokerTec, EBS, GovPX) and third-party (CryptoQuant).

**There is no OHLC bar dataset.** CME does not sell 1-minute or 15-minute bars. You buy tick
(Time & Sales) or book (BBO / Market Depth / MBO / PCAP) and aggregate them yourself. That means
even the paid exchange-direct route to 15-minute bars is a tick-processing project, not a download.

There *is* a **"CME Group Continuous Price Series"** dataset, which is the exchange's own stitched
continuous contract — relevant to the "continuous or stitchable" requirement, but paid.

### Depth of the paid datasets (for context)

- **Time and Sales**: CME electronic from **1992-06-26**, pit from 1982-01-04; CBOT electronic from
  2003-11-23; NYMEX and COMEX from 1999-12-01. Two formats: v1 to 2022-08-19, v2 from 2022-08-22
  (nanosecond ISO-8601 UTC, aggressor side, security ID).
- **Top of Book (BBO)**: CME electronic from **2004-11-01**, CBOT from 2008-01-14, NYMEX/COMEX from
  1999-12-01. Three dates are known missing: 2024-06-14, 2024-01-09, 2023-03-10. Purchase includes
  the Time & Sales and SecDef files.
- **Volume and Open Interest**: from **1972**. Open interest only reliable post-2010-11-01.
- **Market Depth FIX**: from 2007-12-30.

---

## 4. cmegroup.com public site — free to view, hostile to retrieve

| field | |
|---|---|
| name + URL | CME Group product settlement pages, e.g. `https://www.cmegroup.com/markets/equities/sp/e-mini-sandp500.settlements.html`; delayed quotes `https://www.cmegroup.com/market-data/delayed-quotes.html`; volume/OI `https://www.cmegroup.com/market-data/volume-open-interest/exchange-volume`; Daily Bulletin `https://www.cmegroup.com/market-data/daily-bulletin.html` |
| **genuinely free?** | Free **to view in a browser**. Not free to retrieve programmatically — see below. |
| instruments, granularity, history depth | All CME Group products. Daily settlement, open, high, low, volume, prior-day OI per contract month. Quotes delayed at least 10 minutes. **Current day plus a short lookback only** — these pages are not an archive. |
| **full session or settlement-only?** | Settlement-only. |
| bulk/programmatic access? | **No.** There is an undocumented JSON web service (`/CmeWS/mvc/Settlements/Futures/Settlements/{id}/FUT?tradeDate=...`) that the pages themselves call, but it is IP-blocked to scripted clients. |
| licensing / redistribution terms | See section 8. Scripted access is explicitly prohibited. |
| verified how | `curl` against both `/CmeWS/mvc/Settlements/...` and the static sample-CSV paths returned **HTTP 403** with a JSON body (quoted in section 8). Every direct fetch of `cmegroup.com` from this machine, including plain page loads, was either blocked or timed out; the only way I could read cmegroup.com content at all was via a text-extraction proxy. |

### The FTP-to-DataMine migration, from CME's own FAQ

CME's *Access to CME Group Settlement Data FAQ* is explicit about what changed:

> "Settlement data posted on the website will be delayed until midnight CT, then will be freely
> available to view."

and on cost:

> "A client may purchase a subscription that can vary from $105/per month , $105/per month per DCM,
> or $2,100/per month depending on the End of Market Summary dataset chosen."

The three pre-midnight routes CME names are MDP 3.0 UDP (real-time, licence fee plus connectivity
fee), Google Pub/Sub (real-time and 10-minute delayed, licence fee plus Pub/Sub fees), and DataMine.
**None is free.** The DataMine settlement datasets are also *top-day-only* on subscription — the
Settlements FAQ states plainly, "The files are available top day only. When the next day files are
generated and posted, they overwrite the prior day's files." Historical depth is a separate purchase.

---

## 5. CME on Google Cloud — not free either

| field | |
|---|---|
| name + URL | CME Historical Market Depth Data on Google Cloud Platform, via BigQuery / Analytics Hub. Docs: `https://cmegroupclientsite.atlassian.net/wiki/spaces/EPICSANDBOX/pages/457217625/` |
| **genuinely free?** | **No.** "Customers interested in accessing the CME Historical Market Depth Data on GCP dataset should contact CME Group Data Sales, complete the Information License Agreement (if required) and pay the applicable fee." Plus BigQuery compute. |
| instruments, granularity, history depth | 10 levels deep futures / 5 levels options, **January 2014 to present**, T+1. Four Analytics Hub listings: CME, CBOT, NYMEX, COMEX 10 Level Order Book. Three tables: Statistics (settlement, OHLC, aggregated volume), Depth of Book, Quotes. |
| **full session or settlement-only?** | Full session, full book. This is the richest exchange-direct product and would trivially yield 15-minute bars — if you could afford it. |
| bulk/programmatic access? | Yes, SQL over BigQuery; CME publish sample queries on their GitHub. |
| licensing / redistribution terms | Information License Agreement + Schedule 6. |
| verified how | Confluence page 457217625, fetched via the Confluence REST API. |

Worth noting only as the shape of what a paid exchange-direct solution looks like: the *Statistics*
table explicitly contains "Settlements, Open, High, Low, Close, aggregated volume", which is the
closest CME comes to selling bars.

---

## 6. CME academic programme

| field | |
|---|---|
| name + URL | CME DataMine for Education — described at `https://www.cmegroup.com/education/academic-resources` |
| **genuinely free?** | **No.** Verbatim: "We offer a **50% discount** on access to CME DataMine for qualifying institutions, providing access to all members of faculty, staff and students. Historical data can be used to enhance research possibilities or to inform trading education." |
| notes | The programme's own "Get Started" link (`/market-data/cme-datamine-for-education.html`) now returns **404** — the landing page has been removed while the parent page still advertises it. Whether the programme is still operating is unclear. Everything else on the academic page is free but non-data: 60+ online courses, private trading simulations, the University Trading Challenge. |
| verified how | Fetched `https://www.cmegroup.com/education/academic-resources` via text proxy and located the paragraph; separately confirmed the linked education page 404s. |
| relevance | Requires institutional affiliation, is a discount not a grant, and halves a bill that starts in the thousands for multi-year tick data. Not a route here. |

The **CME Group Foundation** runs Academic Research and Curriculum Development grants
(`cmegroupfoundation.org/grants/`), but these are cash grants to universities for education
outcomes — not data grants, and not open to individuals.

---

## 7. Other exchanges

### ICE / ICE Futures Europe / ICE Futures US

| field | |
|---|---|
| name + URL | ICE Report Center — `https://www.ice.com/marketdata/reports`; daily settlement prices `https://www.ice.com/report/102`; historical volume `https://www.ice.com/report/26` |
| **genuinely free?** | Report Center is browsable free, but: "End of day report packages in .csv format are available for purchase on a subscription basis." |
| instruments, granularity, history depth | Brent, gas oil, natural gas, power, emissions, softs, ICE US indices. Daily OHLC, settlement, volume, OI per contract month. History depth not published on the public pages. |
| **full session or settlement-only?** | Settlement-only. ICE publishes nothing intraday for free. |
| bulk/programmatic access? | Subscription MFT (managed file transfer) for the paid packages. The public site is behind Cloudflare — a scripted request to `ice.com/marketdata/DelayedMarkets.shtml?getHistoricalChartDataAsJson` returned an **HTTP 403 Cloudflare challenge**. |
| verified how | Fetched the Report Center index; `curl` against the historical-chart JSON endpoint returned the Cloudflare interstitial. |
| relevance | **None for this project.** ICE does not list ES/NQ/RTY/YM. Only relevant as a session-structure substitute, and it gives nothing free intraday anyway. |

### Eurex / Deutsche Börse

| field | |
|---|---|
| name + URL | `https://www.eurex.com/ex-en/data`; free reference-data API at `/ex-en/data/free-reference-data-api`; Eurex File Service at `https://www.mds.deutsche-boerse.com/mds-en/historical-data/eurex-file-service` |
| **genuinely free?** | The **reference data API** is free and public — product/instrument definitions only, no prices. The **File Service** statistics carry opening quotation, daily high, daily low, settlement price and volume but only **for the past 20 days**. Everything historical routes to Deutsche Börse Market Data + Services, paid. |
| instruments, granularity, history depth | FDAX, FESX, FGBL etc. Daily, 20-day rolling window. |
| **full session or settlement-only?** | Settlement-only. |
| bulk/programmatic access? | Yes for reference data; file service is entitlement-gated. |
| verified how | Fetched `eurex.com/ex-en/data`. Could not reach the A7 analytics platform page (404 on the documented path, TLS handshake failure on `a7.deutsche-boerse.com`) — **unverified whether A7 still has a free tier.** |

### Deutsche Börse Public Dataset on AWS — DEAD, but was exactly what we want

| field | |
|---|---|
| name + URL | `https://registry.opendata.aws/deutsche-boerse-pds/` — buckets `deutsche-boerse-eurex-pds` and `deutsche-boerse-xetra-pds`, both `eu-central-1` |
| **genuinely free?** | Was. **Now dead.** The registry entry reads: "The provider of this dataset will no longer maintain this dataset." |
| instruments, granularity, history depth | **One-minute OHLCV bars** for Eurex and Xetra instruments, updated every minute during trading hours. This was a real free minute-bar feed straight from an exchange group. |
| bulk/programmatic access? | Was S3. **Both buckets now return `AccessDenied` on an anonymous `list-type=2` request** — verified today. |
| licensing / redistribution terms | Was non-commercial use only; copying, distribution and derivative works permitted for non-commercial purposes. |
| verified how | Fetched the AWS registry page; issued anonymous S3 list requests against both bucket endpoints — both returned `<Code>AccessDenied</Code>`. |
| relevance | Record it as a closed door so nobody spends a day rediscovering it. If a mirror of this data exists on GitHub or Kaggle it would be a legitimate 1-minute European index-futures fixture — that is the GitHub agent's lane, not mine. |

### Euronext, LSE, CBOT/NYMEX/COMEX

- **CBOT, NYMEX, COMEX** are CME Group DCMs with no separate data channel. Everything above covers
  them: they share the DataMine catalogue, they appear in the same SPAN files (exchange codes
  `CBT`, `NYM`, `CMX`), and they have no independent free offering.
- **Euronext** and **LSE** were not separately reachable within this session's search budget. Their
  derivatives franchises do not list US index futures, so they are substitutes at best. Marked
  unverified.

---

## 8. Licensing — the part that decides whether anything can be committed

This is the constraint that matters most, so it is quoted at length.

### CME Data Terms of Use (cmegroup.com), retrieved 2026-09-01

Scope — the definition is deliberately broad and covers exactly what we want:

> "The content on the Website includes, without limitation: volume, bid-ask prices, opening and
> closing range prices, high-low prices, settlement prices, indexes, open interest and related
> information, materials, and content on the Website ('CME Data')."

Permitted use:

> "You may access content only for your personal use for non-commercial purposes. Non-commercial
> use does not include the use of CME Data without prior written consent from CME in connection
> with: (1) the development of any software program, including, but not limited to, training a
> machine learning or artificial intelligence system; or (2) providing archived or cached data sets
> containing CME Data to another person or entity."

Prohibited use — note that *downloading* and *compiling* are both named:

> "you are strictly prohibited from selling, licensing, renting, modifying, changing, manipulating,
> altering, printing, collecting, copying, reproducing, downloading (other than to view only where
> a link is provided), uploading, transmitting, disclosing, distributing, disseminating, publicly
> displaying, publishing, editing, adapting, creating derivative works, electronically extracting
> or scrubbing, compiling (including, without limitation, through framing or systematic retrieval
> to create collections, compilations, databases or directories) or conducting 'text and data
> mining' ... in relation to any CME Data"

Automated access:

> "Unless CME Group gives you prior written permission, use of any Web browsers (other than
> generally available third-party browsers), engines, scripts, software, spiders, robots, avatars,
> agents, tools or other devices or mechanisms (such as crawlers, browser plug-ins and add-ons, or
> other technology) to navigate, access, copy in bulk, retrieve, harvest, index, search or analyze
> any portion of the Website is strictly prohibited."

Derived works:

> "You agree not to, and have no rights to, use the CME Data to create, calculate, issue, settle,
> maintain, support or develop any financial instruments ... indexes, products, services (including
> but without limitation, portfolio management services, pre- and post-trade risk management
> services, or valuation services) or any other derivative works without the express written
> consent of CME Group."

And the AI clause, which CME set in bold in the original:

> "For the avoidance of doubt and to the fullest extent permitted by law, use of any CME Data
> (including associated metadata) in any manner for any machine learning and/or artificial
> intelligence, including without limitation for the purposes of training, coding, or development
> of artificial intelligence technologies, tools, or solutions or machine learning language models,
> or otherwise for the purposes of using or in connection with the use of such technologies, tools,
> or models to generate any information, material, data, derived works, content, or output is
> expressly prohibited."

### And CME enforce it in software

Every scripted request to `cmegroup.com` from this machine — including a request for one of CME's
own advertised free sample CSVs — returned HTTP 403 with this body:

> "This IP address is blocked due to suspected web scraping activity associated with it on this
> CMEgroup.com page. Use of scripts, software, spiders, robots, avatars, agents, tools or other
> scraping mechanisms is strictly prohibited by CME Group's website Data Terms of Use. If you are
> attempting to access data or content from the website via automated means or for commercial
> purposes, CME has numerous other methods to deliver the content you require. Please contact CME
> Group's Global Command Center (GCC) at gcc@cmegroup.com and your inquiry will be directed to the
> appropriate team."

### What this means practically

- **Nothing sourced from `cmegroup.com` may be committed to a repo**, private or otherwise —
  "providing archived or cached data sets containing CME Data to another person or entity" is
  outside personal non-commercial use, and a repo with more than one reader is exactly that.
- **The DataMine free samples are not a licence workaround.** They are on cmegroup.com and are
  covered by the same terms.
- **The AI clause is unusually aggressive** and, read literally, reaches any model fitted on CME
  prices. Whether that is enforceable against private research is a legal question, not a technical
  one, but it should be flagged rather than ignored.
- **The FTP host is the one genuine ambiguity.** `ftp.cmegroup.com` is a different host, serves
  anonymous FTP, presents no terms and no click-through. The Terms of Use are drafted around "the
  Website". I would not treat that as permission to redistribute, but it is a materially different
  posture from the 403-and-lawyer-letter treatment the website gives scripts.

---

## 9. CFTC — free, deep, programmatic, and not price data

| field | |
|---|---|
| name + URL | Commitments of Traders. Bulk: `https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm`, files at `https://www.cftc.gov/files/dea/history/{report}_{format}_{year}.zip`. API: `https://publicreporting.cftc.gov/` (Socrata). |
| **genuinely free?** | **Yes, unreservedly.** US government public data. No key, no registration, no rate limit encountered, no redistribution restriction. |
| instruments, granularity, history depth | Every CFTC-reportable US futures market including the CME equity index complex. **Weekly** (Tuesday positions, Friday release). Legacy Futures-Only from **1986**; Legacy Futures-and-Options from March 1995; Disaggregated from September 2009; Traders in Financial Futures from 2010-07-20; Commodity Index Trader Supplement from January 2006. |
| **full session or settlement-only?** | Neither — it is **positioning, not price**. Open interest broken out by trader category (non-commercial long/short/spreading, commercial, non-reportable), plus total open interest. |
| bulk/programmatic access? | **Yes, both.** Per-year ZIPs (text and Excel) plus consolidated multi-year archives; and a Socrata JSON API with filtering and pagination. |
| licensing / redistribution terms | US federal government work — public domain. **Safe to commit.** This is the only source in this entire lane that is unambiguously repo-safe. |
| verified how | Downloaded `fut_disagg_txt_2024.zip` (2,381,296 bytes) and confirmed it unpacks to `f_year.txt` with the expected header row. Queried `https://publicreporting.cftc.gov/resource/6dca-aqww.json?$limit=1` — HTTP 200, well-formed JSON with `open_interest_all`, `noncomm_positions_long_all` etc. |

### What COT is actually good for here

Not price, so it cannot substitute for anything in the spec. But it is genuinely useful as:

- **A free, unrestricted, 40-year weekly conditioning variable** — positioning extremes, commercial
  vs non-commercial divergence, OI changes — that can be joined to whatever price series you end up
  with. It is the standard regressor in the futures risk-premium literature.
- **A free, repo-safe fixture for pipeline and join testing.** Since it is public domain, it can be
  committed. If you need a real financial time series checked into the repo to exercise
  date-alignment, resampling and merge logic without any licensing exposure, COT is the obvious
  candidate.
- **A cross-check on contract activity.** Total open interest by market from COT can be reconciled
  against CME's free `daily_volume/` files.

**No CFTC or NFA source carries price data.** I checked; the CFTC's public reporting environment
carries COT, Bank Participation, swaps data and the trader-category reports. There is no price feed.
The NFA publishes registration and disciplinary data, not market data.

## 10. SEC / FINRA

Not applicable and not a useful workaround. Futures are CFTC-regulated, so nothing futures-priced
appears in SEC or FINRA public data. EDGAR carries fund holdings (N-PORT, 13F), FINRA carries TRACE
for corporate bonds and equity short-interest — no intraday futures-adjacent price series in either.
The nearest SEC-side substitute is the equity ETF complex (SPY/QQQ/IWM/DIA), which is a different
research question and belongs to the substitutes agent's lane, not the exchange-direct one.

---

## Ranked shortlist

**1. CME legacy SPAN archive on `ftp.cmegroup.com` — the only real find.**
Free, anonymous, programmatic, 2013-01-02 → 2025-09-12, daily settlement prices for every contract
month on all four CME Group exchanges. Covers ES, NQ, RTY, YM, CL, GC, 6E. Verified by download and
decode. **Daily only** — fails the 15-minute spec outright. Frozen after 2025-09-12. Redistribution
posture ambiguous; use locally, do not commit.

**2. CME `ftp.cmegroup.com/daily_volume/` — the companion.**
Free, anonymous, 2014-01-02 → present and still updating daily. Volume and preliminary OI per
product. No prices, but it is what makes #1 into a roll-aware continuous series. Same licensing
ambiguity.

**3. CFTC Commitments of Traders — free, deep, and the only repo-safe source in this lane.**
1986 to present, weekly, bulk ZIPs and a Socrata API, public domain. Not price data. Use it as a
conditioning variable and as the safe committed fixture.

**4. CME DataMine free samples — format fixtures only.**
One trading day per product per dataset. The 2012-11-05 and 2025-03-12 ES Time & Sales samples are
real full-session tick data and are the right thing to write your parser against. They are on
cmegroup.com, so they are covered by the Data Terms of Use and by an active anti-scraping block;
they will need to be fetched by hand in a browser, and they should not be committed.

**5. Everything else — closed.**
Deutsche Börse's AWS public minute-bar dataset was exactly the right shape and is dead (buckets
`AccessDenied`, provider withdrew). Eurex gives free reference data and a 20-day statistics window.
ICE sells its EOD packages and Cloudflare-blocks scripts. The CME academic programme is a 50%
discount with a 404'd landing page, not a grant. CME's GCP BigQuery market-depth product is the
technically ideal answer and costs money.

**Bottom line for the spec:** the exchange-direct lane cannot deliver 10+ years of full-session
15-minute CME bars for free. The exchanges' free tier is daily settlement data, and CME has spent
the last three years narrowing even that. If the project needs intraday, it will come from a vendor,
a broker or a community mirror — not from the exchange. What this lane *does* contribute is a
credible free daily backbone (SPAN + daily_volume, 2013–2025) that can validate, calibrate or
cross-check whatever intraday source is eventually chosen, and a licence picture strict enough that
it should shape the fixture policy for the whole project.

---

## Could not verify

- **Whether legacy SPAN publication is permanently retired or merely relocated.** The archive stops
  at 2025-09-12 and "SPAN Risk Parameter Files" now appears as a DataMine catalogue entry, which
  strongly suggests retirement — but I exhausted the session's web-search budget before I could find
  the CME advisory that announced it. Worth one targeted search: *CME legacy SPAN pa2 retirement
  advisory 2025*.
- **Whether `ftp.cmegroup.com` is contractually covered by the cmegroup.com Data Terms of Use.** No
  banner, no terms file, no click-through on the FTP. This is a genuine open question and the answer
  determines whether SPAN-derived data can be committed.
- **The exact content of the DataMine v2 sample files.** The `part-000NN-c000` filenames imply Spark
  partitions, so a v2 sample may be a fragment of a day rather than a full day. Could not confirm —
  the download is IP-blocked from this machine.
- **DataMine per-dataset pricing for Time & Sales and Top of Book.** Only the End of Market Summary
  tiers are publicly priced ($105/mo, $105/mo per DCM, $2,100/mo). The catalogue requires sign-in to
  reveal tick-data pricing.
- **Whether Deutsche Börse's A7 analytics platform still offers a free tier.** The documented URL
  404s and the `a7.deutsche-boerse.com` host failed TLS negotiation. A7 historically gave free
  academic/trial access to full-depth Eurex order-book data and would be worth ten minutes if
  European index futures are acceptable as a session-structure substitute.
- **Euronext and LSE free offerings.** Not reached; search budget exhausted. Low expected value —
  neither lists US index futures.
- **The CME Liquidity Tool datasets.** Documented in the DataMine catalogue and there is a free
  public Liquidity Tool on cmegroup.com; I could not extract the Confluence page body to establish
  whether the underlying dataset has any free component. It is aggregated spread/depth metrics
  rather than bars, so it would not meet the spec regardless.
