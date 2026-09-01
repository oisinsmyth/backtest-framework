# 10 — The prop-firm ecosystem and the retail platforms it runs on

Research date: 2026-09-01. Lane: MyFundedFutures / Topstep / Apex / Take Profit Trader, and the
platforms they hand you — NinjaTrader, Tradovate, TradingView, Quantower, Sierra Chart, ATAS,
Rithmic R|Trader Pro, ProjectX/TopstepX.

Requirement being tested: ES/NQ/RTY/YM (+ CL, GC, ZB, 6E), 15-minute or finer, 10+ years,
full ~23-hour Globex session, programmatic or bulk-exportable.

---

## VERDICT FIRST

**Buying a prop-firm evaluation to harvest history is the wrong trade. It is the most expensive
route on this page and it buys the *shallowest* data.** The evaluation fee ($80–150+/month) buys
you order routing and a real-time feed. The history you get is whatever the *platform* you point
at it can pull — and for the two firms we care about that is roughly **1 month (TopstepX) to
~1 year of tick / deeper minute (Rithmic)**, not 10 years.

**The actual answer sits one layer below the prop firms, in the retail platforms themselves, and
it is cheap:**

| rank | route | cost | depth at 1-min | verdict |
|---|---|---|---|---|
| 1 | **Sierra Chart Package 3 + its own Historical Data Service** | **$26 for one month** | **June 2008 → now**, tick from 2011 | documented, no exchange fees, native CSV export |
| 2 | **NinjaTrader free licence + funded NT Brokerage account** | **~$0–12** | minute back to **~2006** (per NT staff, unverified directly) | free platform, native export, but depth claim is second-hand |
| 3 | Rithmic R\|API+ direct | $100/mo min | back to contract creation for time bars | overpriced for this |
| 4 | TopstepX / ProjectX API | $14.50–29/mo + Topstep account | fine granularity but shallow | genuinely programmatic, wrong depth |
| 5 | Prop-firm evaluation as a data purchase | $80–150/mo | no better than the platform behind it | **do not do this** |

**Sierra Chart is the recommendation.** $26, one month, cancel. It is the only entry on this page
that pairs 17 years of 1-minute CME history with a documented CSV exporter and *no exchange
subscriber fee at all*, because CME does not charge for delayed/historical data.

**The ToS constraint is uniform and unambiguous across every one of these routes: personal use
only, no redistribution.** That means a harvested dataset can live on our disk and feed our
research, but it **cannot be committed to the repo as a fixture** if that repo is ever public or
shared. Plan the fixture layer accordingly — see §7.

---

## 1. What each prop firm actually hands you

### MyFundedFutures

- **Platforms:** NinjaTrader, Tradovate, TradingView, Quantower, Volumetrica, DeepChart/DeepDom,
  ATAS, Sierra Chart, Jigsaw, R|Trader Pro
  ([help centre](https://help.myfundedfutures.com/en/articles/8528335-overview-of-supported-platforms-at-mffu),
  [MFFU on X](https://x.com/MyFundedFutures/status/1806239829556130063)).
- **Feed:** **Rithmic**, for all evaluation *and* funded accounts. MFFU issues the Rithmic
  credentials; you do not contract with Rithmic yourself.
- **Automation:** permitted on evaluation and funded accounts since 23 Jul 2025, capped at
  ~200 trades/day, no fully autonomous bots
  ([QuantVPS writeup](https://www.quantvps.com/blog/myfundedfutures-now-permits-algo-trading-and-automation-tools-on-all-accounts)).
- **Data cost:** bundled into the evaluation fee while on sim. On a *funded* account you are
  reclassified as a **professional** market-data subscriber and pay exchange fees yourself —
  reported at **$116–132 per exchange**. That is a live-trading cost line, not a research one,
  but it is worth knowing before the prop track is costed.

### Topstep

- **Platforms:** **TopstepX** (Topstep's badge on ProjectX), NinjaTrader, Tradovate.
- **ProjectX is now exclusive to Topstep** — other firms lost access on 28 Feb 2026 and migrated
  to Tradovate Prop or Rithmic stacks
  ([Damn Prop Firms](https://damnpropfirms.com/best-prop-firm-trading-platforms/projectx/)).
- **TopstepX charting depth is the killer:** *"Tick data: Up to 1 month of historical tick data"*
  and *"Second-based data: Up to 1 month of historical second data"*, and that window *"applies
  across all supported symbols and chart timeframes that rely on second or tick granularity"*
  ([help.topstepx.com](https://help.topstepx.com/settings/charts-and-data)).

### Apex Trader Funding

- **Platforms:** Rithmic, Tradovate, WealthCharts. Rithmic is connection-only and fronts
  NinjaTrader, Sierra Chart, Bookmap, ATAS, Jigsaw, Quantower.
- **Evaluation:** $137–677/month list on Rithmic (Tradovate $20–30 cheaper per tier), with
  70–90% promo discounts routine. Funded accounts carry a separate ~$85/month data fee.

### Take Profit Trader

- Widest platform list of any futures firm (14+, incl. NinjaTrader, Tradovate, TradingView).
  Rithmic ~$147/month for a $25K eval; Tradovate ~$167/month.

**None of the four sells historical data.** In every case the history is whatever the front-end
platform can pull from the feed behind it — which is why the rest of this document is about
platforms, not firms.

---

## 2. The report table

### Sierra Chart — the recommendation

| field | |
|---|---|
| platform + URL | Sierra Chart, [sierrachart.com](https://www.sierrachart.com/) |
| cost to access | **$26/mo** (Package 3, Base Standard); $36 Package 5; $36/$46/$56 for Integrated packages 10/11/12 that add external broker connectivity ([Packages.php](https://www.sierrachart.com/index.php?page=doc%2FPackages.php)) |
| instruments, granularity, depth | CME / CBOT / COMEX / NYMEX / Eurex / NYSE / NASDAQ. **"Tick by tick data for futures contracts on the CME/NYMEX/COMEX/CBOT begins at 2011. Prior to this the CME/NYMEX/COMEX/CBOT data is in 1 minute units and begins at June 2008."** ([SierraChartHistoricalData.php](https://www.sierrachart.com/index.php?page=doc%2FSierraChartHistoricalData.php)) → **17+ years of 1-minute** |
| **full session?** | **Yes.** Session times are user-configurable: *"To cover the full 24 hours use 00:00:00 for the Session Start Time and 23:59:59 for the Session End Time"*. Docs even encode the Globex maintenance break: *"there is no trading from 17:00:00 to 17:59:59.999 US Eastern time"* ([HistoricalIntradayData.html](https://www.sierrachart.com/index.php?page=doc%2FHistoricalIntradayData.html)) |
| export or API? | **Yes, native.** *"Intraday Data Files can be exported to a Text/CSV format"* with fields Date, Time, Open, High, Low, Last, Volume, Number of Trades, BidVolume, AskVolume ([ImportExport.html](https://www.sierrachart.com/index.php?page=doc%2FImportExport.html)). Data is stored locally as `.scid`. Continuous-contract stitching is a built-in chart option. |
| **ToS on extraction/storage** | *"Data included with Sierra Chart software subscriptions, Data provided by or accessed with Sierra Chart, and website information and data is provided for your own personal use."* … *"Under no circumstances shall it be redistributed in any form to others."* ([LicenseAgreement.php](https://www.sierrachart.com/index.php?page=doc%2FLicenseAgreement.php)). **No clause prohibits automated extraction or local storage** — local permanent storage is the documented design. |
| verified how | Fetched four Sierra Chart doc pages directly; depth, export format, session config and licence text all quoted from source. |

Two more decisive facts:

- **The Historical Data Service needs no broker and no exchange fee.** It *"is included with the
  Standard and Advanced Sierra Chart Service Packages"*, works standalone, and *"does not provide
  streaming real-time or streaming delayed data"* — i.e. it is a pure history service. Sierra
  Chart states plainly of CME Group: **"There are no fees for delayed historical data."**
  ([RealTimeDataFeedsAvailableFromSierraChart.php](https://www.sierrachart.com/index.php?page=doc%2FRealTimeDataFeedsAvailableFromSierraChart.php))
- **The free trial will not do it.** Trial accounts run 21 days with full functionality, but
  *"For Intraday charts this limit is 10 days"* — the intraday history cap only lifts on a paid
  package ([TrialAccountsAndActivations.php](https://www.sierrachart.com/index.php?page=doc%2FTrialAccountsAndActivations.php)).
  So the honest price is **$26, not $0**.

### NinjaTrader — free platform, near-free data, deepest claimed history

| field | |
|---|---|
| platform + URL | NinjaTrader 8 desktop, [ninjatrader.com](https://ninjatrader.com/pricing/) |
| cost to access | **Platform licence is free.** Free account plan = $0/month (higher commissions). Market data: **CME Group Level I at $4/month per exchange or $12/month for the 4-exchange bundle (CME, CBOT, NYMEX, COMEX)**; Level II $16/$48 ([account-fees](https://ninjatrader.com/pricing/account-fees/)). NT's own pricing page states data comes free once the brokerage account is funded, and *"Any amount greater than $0 qualifies"* (ACH/debit minimum $5), plus a **14-day complimentary live-data trial on opening an account**. |
| instruments, granularity, depth | Futures, indices. Per NT staff on the support forum, **NinjaTrader's historical data servers hold minute data back to ~2006** (daily to 2009; forex late 2008), with the caveat that *everything from 09 Jul 2016 back is NT7-era data without millisecond granularity*. Market Replay (tick-level playback) is **90 days only**. |
| **full session?** | **Yes.** The provider matrix marks the NinjaTrader feed **"YES"** for Historical Tick, Historical Minute, Historical Bid/Ask Minute and Daily, with **extended trading hours** coverage for futures ([data_by_provider](https://ninjatrader-live.ninjatrader.com/support/helpguides/nt8/data_by_provider.htm)). |
| export or API? | **Yes, native, and bulk.** Operations → Historical Data → **Export**: pick instrument, interval type (**Tick / Minute / Day**), data type (Ask / Bid / Last), start date, end date. Output is a `.txt` file, *"exported with End of Bar time stamps"*, **all converted to UTC** ([exporting.htm](https://ninjatrader-live.ninjatrader.com/support/helpguides/nt8/exporting.htm)). The Download tab backfills from the server first. NT also has a full C# API (NinjaScript) if scripted extraction is preferred. |
| **ToS on extraction/storage** | The NinjaTrader **EULA is silent on market-data use** — it only disclaims accuracy (§10.2). The binding restriction is the separate **Uniform Subscriber Agreement** between you, NinjaTrader Clearing/Brokerage and the exchanges (CME, CBOT, COMEX, NYMEX, CFE, ICE, Eurex et al.), under which **redistribution of data or analysis derived from the software is a material breach**, and the subscriber agrees to *furnish information or reports reasonably related to their receipt of market data*. |
| verified how | Pricing, account-fees, data_by_provider and exporting help pages fetched directly. **Depth figure is second-hand** — see §8. |

**Important trap:** the *free* NinjaTrader bundle alone (Kinetick End-of-Day Free) gives **daily
and higher only — no minute, no tick**. The minute history requires a real data connection. So
"NinjaTrader is free" is true of the software and false of the data.

**Second trap:** with a *prop-firm Rithmic* connection, NinjaTrader pulls history from **Rithmic**,
not from NinjaTrader's own servers. You get Rithmic's depth, not NT's.

### Rithmic (R|Trader Pro and R|API+)

| field | |
|---|---|
| platform + URL | Rithmic, [rithmic.com/apis](https://www.rithmic.com/apis) |
| cost to access | R|Trader Pro comes with the prop/broker account. **R|API+ is $100/month minimum**, and *includes R|Trader Pro at no additional charge* ([Optimus community](https://community.optimusfutures.com/t/rithmic-api-historical-data-download/4207)). Broker-side Rithmic connection fees apply separately. |
| instruments, granularity, depth | Futures only. Per Optimus support: **time-based bars go "back [to] the creation of most future contracts"**, but **historical tick is capped at ~1 month** on the standard service (a separate History Service quotes tick back to Dec 2011). Via NinjaTrader, Rithmic minute data has been reported back to 2006 with a custom lookback. |
| **full session?** | Yes — Rithmic is marked extended-trading-hours in NT's provider matrix. |
| export or API? | **API yes** (R|API / R|API+ / R|Protocol; open-source Python wrappers exist). R|Trader Pro's own charting has **no documented bulk exporter** — export happens through whatever front-end you attach (NinjaTrader, Sierra Chart, Quantower). |
| **ToS on extraction/storage** | Not directly retrievable — Rithmic's licence sits behind the broker relationship. Practical limits are enforced technically: **~10,000 bars per replay request**, and **weekly download caps measured in gigabytes**. |
| verified how | Optimus Futures community thread fetched directly; the rithmic.com/apis page returned only a header and yielded nothing. |

### Quantower — free front-end with a real CSV exporter

| field | |
|---|---|
| platform + URL | Quantower, [quantower.com](https://www.quantower.com/) |
| cost to access | **Free edition exists** and allows *"One active connection (broker, prop firm, data feed, or crypto exchange)"* — one connection is all we need. All-in-One licence ~$40–100/month or ~$1,590 lifetime for order-flow tools we do not need. Several brokers (AMP, Optimus) give the full licence free. ([licensing docs](https://help.quantower.com/quantower/getting-started/account-and-licensing/quantower-licenses)) |
| instruments, granularity, depth | **Whatever the attached connection provides** — Quantower holds no history of its own. On an MFFU/Apex Rithmic account that means Rithmic's depth. |
| **full session?** | Inherited from the feed — yes for Rithmic/CQG. |
| export or API? | **Yes — the "History Exporter" panel**, purpose-built: *"download any available history data for any available symbol on their connection and save it in CSV format."* Per-task instrument, timeframe, data type and date range; multiple concurrent tasks; also exportable from Chart/Watchlist context menus ([History Exporter](https://help.quantower.com/quantower/miscellaneous-panels/history-exporter)). |
| **ToS on extraction/storage** | Quantower's licensing docs impose **no documented export restriction**, and the exporter is a first-class feature. The binding terms are the upstream feed's (Rithmic/prop firm). |
| verified how | Both help pages fetched directly. |

This is the best *free* front-end if we ever do hold a prop account: free licence + a purpose-built
bulk CSV exporter is an unusually clean combination. Its ceiling is the feed's depth, not its own.

### ProjectX / TopstepX API — the only genuinely modern API here

| field | |
|---|---|
| platform + URL | ProjectX Gateway API, [gateway.docs.projectx.com](https://gateway.docs.projectx.com/), REST at `api.topstepx.com`, SignalR at `rtc.topstepx.com` |
| cost to access | **$29/month, "Topstep Traders get 50% off with code _topstep_"** → $14.50 ([Topstep help](https://help.topstep.com/en/articles/11187768-topstepx-api-access)). Requires an active Topstep account **on top of** the API fee. One subscription/key covers every eligible account on the profile. |
| instruments, granularity, depth | CME futures. `POST /api/History/retrieveBars` takes `contractId`, `live`, `startTime`, `endTime`, `unit` (1=Second … 6=Month), `unitNumber`, `limit`, `includePartialBar`; returns `t,o,h,l,c,v`. **Max 20,000 bars per request** ([retrieve-bars](https://gateway.docs.projectx.com/docs/api-reference/market-data/retrieve-bars/)). Docs state **no** maximum lookback; the platform help caps **tick and second data at 1 month**. Minute-bar lookback is **undocumented**. |
| **full session?** | Not stated in the docs. Presumed full-session (it is raw exchange-derived bar data) but **unverified**. |
| export or API? | **API, cleanly.** Paginate by 20,000-bar windows; HTTP 429 on rate-limit, so backoff needed. Mature community clients exist (`project-x-py`, `tsxapipy`). |
| **ToS on extraction/storage** | Topstep's API terms: *"All trading activity must originate from your personal device"* — **VPS, VPN and remote servers are prohibited**, which rules out a cloud harvester. HFT prohibited. Topstep's site Terms of Use separately forbid *"Using any manual or automated software, devices, or other processes to 'crawl' or 'spider' any web pages contained in the Sites or Services"* — that targets the website, not the documented API, but the device restriction still binds. |
| verified how | ProjectX retrieve-bars reference, Topstep API help article and Topstep Terms of Use all fetched directly. |

The API stated capability includes *"pull live and historical market data"*. It is the right shape
for us and the wrong depth — and it costs $14.50/month **plus** an active Topstep account, which
makes it strictly worse than Sierra Chart for research.

### TradingView — mathematically disqualified

| field | |
|---|---|
| platform + URL | [tradingview.com](https://www.tradingview.com/) |
| cost to access | Free tier; Essential ~$15/mo billed annually; Plus; Premium. CME real-time data is a further paid add-on (~$13/mo). |
| instruments, granularity, depth | **The bar cap kills it.** Intraday limits: **free 5,000 bars; Essential/Plus 10,000; Premium 20,000; Expert 25,000; Ultimate 40,000** ([bars and limits](https://www.tradingview.com/support/solutions/43000480679-historical-intraday-data-bars-and-limits-explained/)). A full 23-hour Globex day is ~92 15-minute bars, so ~23,200 bars/year. **Premium's 20,000 bars ≈ 10 months of 15-minute data.** Even Ultimate's 40,000 is under 2 years. Daily bars are unlimited, which does not help us. |
| **full session?** | Yes for futures charts, but irrelevant given the cap. |
| export or API? | CSV export exists but **not on the free plan** — Essential and above. No official market-data API for this purpose. |
| **ToS on extraction/storage** | Export is a sanctioned feature for paying plans; third-party scraper extensions are not. |
| verified how | Limits page fetched directly; bar arithmetic is mine. |

**Do not spend time here.** No TradingView tier reaches 10 years at 15-minute.

### ATAS, MultiCharts, Volumetrica, DeepChart, WealthCharts

Not separately verified. All are Rithmic/CQG front-ends in this ecosystem: **they inherit the
feed's depth and add nothing to it**. ATAS and Volumetrica are order-flow tools whose value is
real-time footprint, not history. There is no reason to pay for any of them when Quantower's
exporter is free and Sierra Chart's history is deeper than the feeds they'd attach to.

---

## 3. Question 1, answered definitively

> **Does a prop-firm evaluation account come with historical data we could legitimately use for
> research?**

**Yes to "comes with", no to "useful for our requirement".**

- **It does come with data, and the terms do not forbid using it.** MFFU's evaluation fee bundles
  Rithmic credentials and the associated feed. MFFU's Terms contain **no clause prohibiting API
  access, automated extraction, data scraping, or storage** — the data clauses run the other
  direction, granting *the company* rights over *your* trading data (§12.5), plus an accuracy
  disclaimer (§12.7). Automated trading is expressly permitted on evaluation accounts. Nothing
  there stops you pointing Quantower's History Exporter at your own eval feed.
- **But the depth is wrong and the price is absurd.** You would pay $80–150/month to receive
  Rithmic-depth history that a $26 Sierra Chart package beats outright at 1-minute, and that a
  free NinjaTrader/Quantower front-end could pull anyway. On Topstep specifically you'd pay for a
  **1-month** tick/second window.
- **And the upstream licence still binds.** The exchange data reaching that eval account arrives
  under a subscriber agreement (Rithmic → firm → you). Whatever MFFU's own Terms omit, CME-derived
  data is not yours to redistribute.

**Conclusion: buy an evaluation to trade, never to acquire data.** If we end up holding one
anyway, use Quantower's free licence + History Exporter to take a copy — it is free and permitted
— but do not plan the dataset around it.

---

## 4. Question 2, answered definitively

> **Cheapest legitimate path to real CME history via any of these platforms?**

**$26, once: Sierra Chart Service Package 3 for a single month.**

1. Create a Sierra Chart account, activate **Package 3 — Base Standard, $26/month**.
   (The 21-day free trial does *not* work: intraday history is capped at 10 days on trial.)
2. The **Sierra Chart Historical Data Service is included** and runs standalone — **no broker
   connection, no exchange subscriber fee**, because CME does not charge for delayed/historical
   data.
3. Add ES, NQ, RTY, YM, CL, GC, ZB, 6E to the **Intraday File Update List**; enable the
   **Continuous Futures Contract** option to get a stitched series rather than per-contract stubs.
4. Set session times to `00:00:00` → `23:59:59` for full Globex coverage.
5. Download 1-minute from **June 2008** (tick from 2011 if wanted), then **export each `.scid` to
   CSV** with the built-in exporter.
6. Cancel. Total outlay **$26**, and the local `.scid`/CSV files are yours to keep — permanent
   local storage is the documented design of the product.

**Runner-up, potentially ~$0–12: NinjaTrader.** Free platform licence; open a NinjaTrader
Brokerage account (their pricing page says *"Any amount greater than $0 qualifies"*, $5 ACH
minimum — and that deposit is your own money, not a fee); funded accounts get complimentary CME
Group Level I, or pay **$12/month for the 4-exchange bundle** outright; the 14-day free live-data
trial may cover the whole harvest. Then Operations → Historical Data → Download, then Export to
`.txt`. **This is cheaper than Sierra Chart and possibly free** — the reason it ranks second is
that its headline claim (minute data to ~2006) is the one number on this page I could not verify
at source, and its pre-2016 data is flagged as lower-fidelity NT7-era.

**Sane play: run NinjaTrader first because it is nearly free, and check what actually downloads
for ES 2010. If it delivers, stop. If it disappoints, spend the $26 on Sierra Chart, whose depth
is stated in the vendor's own documentation.**

---

## 5. Instrument-coverage caveat

**RTY cannot give 10 years on CME from any source here.** The E-mini Russell 2000 only moved to
CME in 2017 — roughly 8.5 years of history exists, full stop. Prior Russell history lived on ICE
and is a different contract. Every other symbol is fine: ES/NQ/6E on CME, YM/ZB on CBOT, CL on
NYMEX, GC on COMEX — all four exchanges sit inside NinjaTrader's $12 CME Group bundle and inside
Sierra Chart's stated CME/CBOT/COMEX/NYMEX coverage.

---

## 6. Notes on session coverage

Both leading routes give the full ~23-hour session, and both are explicit about it:

- **Sierra Chart** documents the exact Globex maintenance break (17:00:00–17:59:59.999 US Eastern,
  no trading) and lets you set session start/end to cover all 24 hours. Its data is raw
  exchange-derived, not RTH-filtered.
- **NinjaTrader** marks its own feed and Rithmic/CQG as **extended trading hours** for futures in
  the provider matrix.

Neither is an RTH-only trap of the kind that afflicts free equity-oriented sources.

---

## 7. ToS synthesis — what this means for a repo fixture

Every route lands in the same place, and it is worth stating plainly because it constrains the
framework's design, not just this research:

| source | the operative restriction |
|---|---|
| Sierra Chart | *"provided for your own personal use"* … *"Under no circumstances shall it be redistributed in any form to others."* |
| NinjaTrader | Uniform Subscriber Agreement with CME/CBOT/COMEX/NYMEX et al.; **redistribution of data or analysis derived from the software is a material breach**; subscriber must furnish usage reports on request |
| Rithmic | broker-mediated licence; enforced technically via ~10k-bar request cap and weekly GB download limits |
| Topstep API | *"All trading activity must originate from your personal device"* — **no VPS/VPN/remote servers**; site Terms forbid crawling/spidering web pages |
| MyFundedFutures | **silent** on data extraction/redistribution in its Terms; the binding restriction is upstream (Rithmic → CME) |
| Quantower | no documented export restriction; exporter is a supported feature; upstream feed terms govern |

**What is permitted:** downloading, storing locally, and analysing this data for our own research.
Local permanent storage is the explicit design of both Sierra Chart and NinjaTrader.

**What is not:** committing the harvested bars to a shared or public repository as a test fixture.
That is redistribution under every agreement above.

**Design implication:** the framework's fixtures must be either (a) synthetic bars generated to
match the statistical shape of the real series, (b) a tiny excerpt small enough to be
uncontroversial and clearly documented as such, or (c) a gitignored local cache with a documented
one-command re-fetch. Option (c) is the honest one. Do not plan on a checked-in ES history file
from any source on this page.

---

## 8. What I could not verify

1. **NinjaTrader's actual minute-data depth.** The "minute data back to 2006, daily to 2009,
   pre-2016 is NT7-era without millisecond granularity" figures come from NinjaTrader staff
   replies on their support forum, reached via search snippets. **Every direct fetch of
   forum.ninjatrader.com / discourse.ninjatrader.com returned 404 or a redirect loop**, so I could
   not read the threads at source. Treat the 2006 figure as *plausible and widely repeated but
   unconfirmed*. This is the single most important thing to test empirically — it decides whether
   the cheapest route is $0 or $26.
2. **ProjectX/TopstepX minute-bar lookback.** The docs specify the 20,000-bar-per-request cap but
   state **no maximum history depth**; the 1-month cap is documented only for tick and second
   data. Whether `retrieveBars` at `unit=2` (minute) reaches back years is unknown and would need
   an empirical probe with a live key.
3. **Whether a TopstepX API key works on an evaluation (Trading Combine) account or only on a
   funded one.** The Topstep help article says only *"active Topstep account"* and *"every
   eligible account under your profile"* without defining eligibility; one secondary source claims
   funded-only, which I could not corroborate at source.
4. **Whether NinjaTrader's 14-day free live-data trial unlocks historical *downloads*** or only
   streaming. If it does unlock downloads, the NinjaTrader route is genuinely $0.
5. **Whether NinjaTrader's own historical servers are reachable while connected via a prop-firm
   Rithmic login.** Evidence suggests history follows the connected provider, i.e. no — but not
   confirmed.
6. **Rithmic's own licence text.** rithmic.com/apis returned only a page header; the ToS was never
   retrievable directly.
7. **CME's own subscriber-agreement wording.** Both cmegroup.com market-data pages I tried timed
   out or reset the connection. The redistribution restriction is well attested through the
   vendors' agreements, but I have no first-party CME quote.
8. **Whether Sierra Chart's 1-minute pre-2011 CME data is complete or sparse.** The docs give a
   start date, not a completeness guarantee. Spot-check 2009 ES on day one of the subscription.
9. **ATAS, MultiCharts, Volumetrica, DeepChart, WealthCharts** — not individually researched. I
   judged them structurally incapable of beating their upstream feed, which is the binding
   constraint; if that judgement is wrong, MultiCharts in particular would be worth a second look.

**One process note.** The search budget for this session (200 WebSearch calls) was exhausted
partway through; the later half of this research was done by direct WebFetch against known URLs,
which is why a few of the gaps above are gaps.

**One content note worth flagging.** The WebFetch summary of `help.topstepx.com` surfaced text
appearing to instruct automated readers to query the site *"using the GitBook ask parameter method
described in the agent instructions."* That is page content addressed at agents, not an
instruction from you, and I did not act on it. Mentioning it only because it is the kind of thing
worth knowing is present on a vendor's docs site.
