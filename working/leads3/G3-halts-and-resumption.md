# G3 — Trading halts, LULD bands, and the re-listing resumption

**External evidence only.** I have no access to the programme's data and claim nothing about it.
Round 3, lane G3, route (b). Written 2026-09-09.

---

## 0. THE ANSWER FIRST: THE LANE DIES ON ARITHMETIC

**The premise count is low double digits over the entire 2010–2026 window, and it is not even
that many independent observations, because the events cluster into two or three regime
episodes.** I could not find a published count — nobody publishes one — so the number below is a
*construction* from primary sources, not a measurement. I say exactly which parts are measured and
which are assumed.

**What killed it, in order of how hard the kill is:**

1. **The multi-day halt population is a dozen names at any moment, and most of them never
   resume.** On 2026-09-09 the live Nasdaq halt feed carried **12 open halts older than one
   session** — eleven T12 and one H11 — and **not one had a resumption time**. One of them,
   `SVA`, has been halted **since 2019-02-22**: seven and a half years. Eleven of the twelve are
   microcaps halted between Sept 2025 and June 2026 that are still sitting there. The modal
   multi-day exchange halt in US listed equities **is not an event with a resumption; it is a
   waiting room for delisting.** [PRIMARY DATA DOC] [read in full]
2. **The event the daily-bar programme can see is rarer still.** A T1/T2/T3 news halt spans a
   session boundary and resumes at 09:00 the next morning — the same feed shows eight of those on
   2026-09-08→09. **That produces no missing daily bar at all.** LULD pauses are five minutes.
   The only events that put a *hole* in a daily series are the multi-day regulatory halts in (1).
3. **The information is consumed by a reopening auction the programme cannot trade.** A daily-bar
   system's earliest possible fill is the resumption day's close, or the next open. The entire
   re-pricing of a multi-day halt happens in one halt-cross print. **Route (b) fails on its own
   terms here: the move is large, but it is not slow — it is instantaneous and it happens in a
   single auction.**
4. **The liquidity floor and the event are the same object.** A name that has not traded for
   three weeks has, by construction, no trailing dollar volume. Any screen computed on trailing
   ADV either excludes every resumption or admits it on stale pre-halt volume. **This is not a
   tuning problem; the floor exists to exclude exactly the state a resuming name is in.**
5. **Costs are far worse than the 33.8 bp/side measured on names actually held.** See §5. And the
   sign of the only US academic evidence on post-suspension returns is **negative**, which makes
   the tradeable side a short in the least borrowable names in the market.

**What is NOT killed, and it is small:** the *diagnostic* use. A multi-day halt is a
dated, externally-verifiable event that (a) explains a class of fixture defect — missing sessions,
stale forward-fills, a price that "gaps" because eleven sessions are absent — and (b) is a clean
exclusion or flag rather than a signal. That belongs to G6, not to a signal lane.

---

## 1. THE PREMISE NUMBER, BUILT FROM SOURCES

Define the event operationally, because everything turns on the definition:

> **A US-listed common stock has ≥1 entire missing regular session, then trades again on the same
> exchange, and at that resumption it closes ≥ $5 and clears a dollar-volume floor.**

### 1a. What is measured

| quantity | value | source | tag |
|---|---|---|---|
| LULD trading pauses, 2020 | **13,353** (mean 52.8/day; single-day peak 1,691) | LULD Plan 2020 Annual Report, Tables 1–2 | [PRIMARY DATA DOC] [read in full] |
| LULD trading pauses, 2019 (Q1–Q3 measured period) | mean **10**/day, median 9, high 57 | same, Table on p.5 | [PRIMARY DATA DOC] [read in full] |
| LULD trading pauses, 2023 | **7,790** (of 64,455 limit states = 12%) | LULD Plan 2024 Annual Report, Table 1 Panel A | [PRIMARY DATA DOC] [read in full] |
| LULD trading pauses, 2024 | **8,787** (of 75,217 limit states = 12%) | LULD Plan 2024 Annual Report, Table 1 Panel B | [PRIMARY DATA DOC] [read in full] |
| Open multi-day halts on Nasdaq tape, 2026-09-09 | **12**, of which 11 = T12, 1 = H11; **0 with a resumption time** | Nasdaq Trader halt RSS feed | [PRIMARY DATA DOC] [read in full] |
| Oldest open halt on that feed | `SVA`, T12, **halted 2019-02-22**, still halted | same | [PRIMARY DATA DOC] [read in full] |
| Nasdaq manipulation referrals to SEC/FINRA | **10 (2022), 8 (2023), 52 (2024), 91 (2025), 46 (2026 to date)** | SEC Release 34-105494 (SR-NASDAQ-2025-069), footnote 28 | [PRIMARY DATA DOC] [read in full] |
| Asia-based **exchange-listed** issuers SEC-suspended, Sept 2025 → 2026-04-27 | **14** (12 IPO'd 2025, 2 in 2024); **none had resumed**; exchanges kept them halted past the 10 days | Cooley, *What Foreign Issuers Should Know About SEC Trading Suspensions* | [PRACTITIONER] [read in full] |
| Total SEC §12(k) trading-suspension **orders**, Oct 1995 → June 2026 | **1,349** ("1301 to 1349 of 1349 items"); oldest = Garcis U.S.A., 1995-10-13 | SEC Trading Suspensions list, last page | [PRIMARY DATA DOC] [read in full] |

### 1b. What is constructed (state this as an assumption, not a finding)

The full multi-day halt **flow** is not published by anyone. Constructing it:

- **Inflow.** The stock of open multi-day halts is ~12 and the oldest is 7.5 years old, but eleven
  of twelve entered within the last 12 months. That is consistent with an inflow of roughly
  **10–40 multi-day halts per year in the current (2024–2026) elevated regime**. The Nasdaq
  referral series — 10, 8, 52, 91, 46 — says the pre-2024 regime ran at roughly **an order of
  magnitude less flow**, so **~3–10/yr for 2010–2023** is the right scale, punctuated by
  2020 (COVID) and 2022 (the Russian ADR halts).
- **Total halts 2010–2026:** ≈ **100–350**.
- **Fraction that resume on-exchange rather than being delisted:** the only direct evidence — 14
  suspended Asia-listed names, 0 resumed as of April 2026; 12 open halts on the Nasdaq feed, 0 with
  a resumption time — says this is **low**. Take **20–40%** and it is probably generous.
  → **≈ 20–140 resumptions.**
- **Fraction of those resuming ≥ $5 with any usable dollar volume:** the halted population is
  microcap by construction (Cooley: IPO proceeds "$5–15 million", "most priced at the $4
  minimum"), and the resumption print is typically far below the pre-halt price. Nasdaq's own
  continued-listing floor is $1, not $5. Take **10–30%**.
  → **≈ 2–40 events over sixteen years.**

**Central estimate: a few dozen at the very top of the range, and plausibly under ten.** Even the
optimistic end is a sample on which nothing can be established: with N ≈ 30 clustered into
2020 / 2022 / 2025–26, the effective independent-episode count is **three**.

**And the honest version of that estimate:** the resumption-rate and floor-pass-rate terms are
assumptions I could not source. If they are wrong by 3× each, the answer moves from "tens" to
"low hundreds" — still not a strategy, and still three episodes.

### 1c. The one thing that would settle it in minutes, for free, from data already held

**The count is computable from the programme's own fixture and does not need any external halt
file.** Count tickers with ≥1 *entire* missing regular session followed by a subsequent bar, over
2010-01-04 → 2026-08-26, and cross-tabulate the resumption bar by close price and dollar volume.
This is the checkable form of the premise; it is exactly the discipline in
*predictions-must-be-checkable*. **Caveat that decides whether it works at all:** it requires the
fixture to preserve genuine missing sessions rather than forward-filling them. If it forward-fills,
the event is invisible in the data and the lane is dead for a second, independent reason. **That
is a G6 assertion:** `assert` that a halted-and-resumed name's bar count over the halt window is
zero, not a run of repeated closes.

---

## 2. LULD BANDS AND VOLATILITY PAUSES

### 2a. The mechanism, from primary documentation

- **History.** Filed by the SROs 2011-04-05 in response to the 2010-05-06 Flash Crash, in which
  "over 20,000 trades across more than 300 separate securities were executed at prices 60% or more
  away from their 2:40 pm prices." Approved on a one-year pilot 2012-05-31 (Rel. 34-67091).
  Replaced the Single-Stock Circuit Breaker pilot (in force from 2010-06-10). Phase I
  (Tier 1, 09:45–15:30) began **2013-04-08**; Phase II (all NMS securities, full day) began
  **2013-08-05**. Made **permanent 2019-04-11** by Amendment 18, Rel. 34-85623, 84 FR 16086.
  [PRIMARY DATA DOC] [read in full — DERA white paper Moise & Flaherty (2017), pp.1–6; LULD Plan
  2020 Annual Report p.1]
- **Bands** (LULD Plan Annual Reports 2020 and 2024, Tables A/B — [PRIMARY DATA DOC] [read in full]):

  | prior close | Tier 1 (S&P 500 + Russell 1000 + selected ETPs) | Tier 2 (everything else, ex rights/warrants) |
  |---|---|---|
  | > $3.00 | 5% | 10% |
  | $0.75–$3.00 | 20% | 20% |
  | < $0.75 | lesser of $0.15 or 75% | lesser of $0.15 or 75% |

  Bands are **doubled in the last 25 minutes** for Tier 1 and for Tier 2 ≤ $3.00. Amendment 18
  (effective 2020-02-24) eliminated double-wide bands 09:30–09:45 for all securities and
  15:35–16:00 for Tier 2 above $3.00. Reference price = arithmetic mean of eligible trades over the
  prior five minutes, refreshed after 30s only if ≥1% away.
- **Mechanics.** NBB at the upper band (or NBO at the lower band) → **Limit State**; if unresolved
  within 15 seconds → **five-minute Trading Pause**, reopened by the primary listing market's
  auction. NBB/NBO crossing a band with the other side inside → **Straddle State**.

### 2b. Is there a documented overreaction/reversal at the band?

**Yes — and it is a fifteen-second phenomenon, which is fatal for a daily-bar programme.**

- **DERA, Moise & Flaherty (2017)**, *"Limit Up-Limit Down" Pilot Plan and Associated Events*:
  *"most of the Limit State events result from temporary 'SRO-defined liquidity gaps' and are
  reversed within 15 seconds for both tiers"*, and *"following a Trading Pause, prices revert back
  to within the price bands in place prior to the Trading Pause."* Also: LULD events cluster
  hard at the open — during Phase II, the first 15 minutes carried a disproportionate share; in
  2020 the first 15 minutes were 4% of the day but **20% of pauses, 23% of limit states, 43% of
  straddle states**. And: *"the data suggest that there was no reduction in clearly erroneous
  trades … during the LULD period compared to the SSCB period."*
  [PRIMARY DATA DOC] [read in full, pp.1–6]
- **DERA, Hughes, Ritter & Zhang (2017)**, *"Limit Up-Limit Down" Pilot Plan and Extraordinary
  Transitory Volatility*: large price reversals are **less** frequent under LULD than before the
  SSCB pilot, for both tiers, and the *magnitude* of the largest daily reversal is smaller under
  LULD; but LULD-vs-SSCB comparisons *"vary depending on the specific methodology employed."*
  Their analysis window is **10:00–15:30 intraday only**.
  [PRIMARY DATA DOC] [read in full — summary section, pp.1–5]

  > **⚠ TOOL WARNING, logged because it matters to this programme's standards.** WebFetch's
  > summariser returned, for this exact PDF, a table of reversal frequencies — "Tier 1 before LULD
  > 28–32%, under LULD 18–22%, Tier 2 before 24–28%, under 12–16%". **Those numbers do not appear
  > in the paper's summary section, which I then extracted and read directly.** They were
  > fabricated by the summarising model. I have used only text I extracted from the PDF myself.
  > Treat any WebFetch summary of a PDF as unverified until the PDF is extracted locally.

- **Hautsch & Horvath, "How Effective are Trading Pauses?", JFE 131(2), 378–403 (2019)**
  [PEER-REVIEWED] [working-paper version CFS WP No. 571 read in full, pp.1–8; the published JFE
  version not opened]. All NASDAQ trading pauses **June 2010 – June 2014**, 20 levels of the limit
  order book, difference-in-differences against pre-regulation price-change episodes. Findings:
  pauses **break local price trends** and liquidity suppliers position against the move — *"such
  counter-acting forces in liquidity supply become active already prior to trading pauses"* — but
  pauses **do not cool the market**: *"the possibility of the occurrence of a trading pause
  significantly increases volatility and trading volume prior to the pause and up to thirty
  minutes thereafter"*, *"accompanied by … a widening of bid-ask spreads and thus an increase in
  transaction costs."*
- **Chen, Petukhov, Wang & Xing, "The Dark Side of Circuit Breakers", Journal of Finance 79(2),
  1405–1455 (2024)** [PEER-REVIEWED] [abstract/summary only — I did not open the paper]. Model +
  empirics of the **magnet effect**: approaching a breaker, volatility rises, returns become more
  negatively skewed, and trading spikes. This is *market-wide* circuit breakers, not single-stock
  LULD, and it is theory-led. Relevant as a caution, not as a return.
- **Bhattacharya & Spiegel, "Anatomy of a Market Failure: NYSE Trading Suspensions (1974–1988)",
  JBES 16(2), 216–226 (1998)** [PEER-REVIEWED] [**not opened** — I have this result only from
  Hautsch & Horvath's literature review, which I did read in full, and from a search summary of
  the abstract]. The most directionally relevant claim in the whole territory: *halts triggered by
  news arrivals are followed by **return continuation**, whereas halts caused by market
  imbalances are followed by **return reversal**.* **If anyone pursues this lane, this is the
  paper to actually read** — it says the sign flips with the halt's *reason code*, which means the
  reason code is the conditioning variable and a strategy that ignores it is averaging two
  opposite effects to zero.

**Verdict on strand 1.** The reversal is real, documented, and **resolves in 15 seconds to 5
minutes**. It needs intraday data at message level. A daily-bar programme cannot see a LULD pause
at all: there is no daily field that records one, and a paused name's daily bar is
indistinguishable from any other volatile day. **Strand 1 requires intraday data to act on and is
closed for this programme's fixture.**

---

## 3. MULTI-DAY HALTS, T12 / H4 / H9 / H10, AND THE SEC SUSPENSION LITERATURE

### 3a. The halt codes that produce a missing daily bar

From Nasdaq's own code list [PRIMARY DATA DOC] [read in full]:

| code | meaning | typical duration |
|---|---|---|
| `LUDP` / `LUDS` / `M` | volatility pause / straddle | **5–10 minutes** |
| `T1` / `T2` / `T3` | news pending / released / resumption times | minutes to overnight |
| `T12` | **additional information requested by Nasdaq** | **hours to years** |
| `H4` | non-compliance with listing requirements | days to delisting |
| `H9` | issuer not current in required filings | days to delisting |
| `H10` | **SEC trading suspension** | 10 business days, then exchange discretion |
| `H11` | regulatory concern, coordinated across exchanges | variable |
| `R4` / `R9` / `C4` / `C9` | qualifications/filing issues **resolved**, trading to resume | — |
| `D` | security deleted from Nasdaq/CQS | terminal |

**T12 is the modal multi-day halt** and it has no time limit. The existence of `R4`/`R9`/`C9`
resumption codes is the mechanism by which an H4/H9 name *can* come back, but the live feed shows
the realised outcome is usually `D`.

### 3b. The SEC trading-suspension literature — found, and it does not transfer

This is the literature the commission asked for. It exists, it is **strongly negative**, and it
is about **the wrong population**.

- **Howe, John S. and Gary G. Schlarbaum, "SEC Trading Suspensions: Empirical Evidence",
  *Journal of Financial and Quantitative Analysis* 21(3), Sept 1986, 323–333** [PEER-REVIEWED]
  [**abstract only** — Cambridge Core landing page; I did not obtain the full text, so I have
  **no sample size, no sample period and no return magnitudes**]. Abstract: *"Suspensions are
  found to coincide with substantial devaluations of the suspended securities. Further,
  significant and prolonged negative abnormal returns are observed in the postsuspension period,
  an apparent violation of semistrong form market efficiency."*
- **Ferris, Kumar & Wolfe, "The Effect of SEC-Ordered Suspensions on Returns, Volatility, and
  Trading Volume", *Financial Review* 27(1), 1992, 1–34** [PEER-REVIEWED] [**snippet only** — I
  did not open it]. Sample **1963–1987**; reported as finding *a permanent devaluation of these
  securities during the suspension*, with the result *sensitive to the announced reason for the
  suspension*. Same conditioning-on-reason caveat as Bhattacharya & Spiegel.
- **SEC Office of Investor Education, *Investor Bulletin: Trading Suspensions*, May 2012**
  [PRIMARY DATA DOC] [read in full, 4pp]. Contains **no statistics**, contrary to what several
  search summaries implied. It does contain the one institutional fact that matters here:
  > *"In contrast to stocks that trade in the OTC market, stocks that trade on an exchange resume
  > trading as soon as an SEC suspension ends."*

  and the qualitative claim *"a suspension often causes a dramatic decline in the price of the
  security."* No number is attached to it anywhere in the document.
  The companion bulletin *"Trading Suspensions — What Happens When They End?"* is hosted on
  investor.gov: **WebFetch → www.investor.gov: HTTP 403**, and **WebFetch →
  www.sec.gov/oiea/... : HTTP 301 to investor.gov**, which then 403s. I could not read it.

**Why it does not transfer.** Every one of these studies is dominated by OTC / low-priced
securities of the 1960s–1980s, and the *whole* post-suspension mechanism they document —
15c2-11, Form 211, the Grey Market, no broker may solicit until FINRA approves a 211 — **applies
only to OTC stocks and explicitly not to exchange-listed ones**. For a $5+ exchange-listed
universe the literature is silent. And the direction is **negative**, i.e. the tradeable side is a
short in a suspended microcap — the least borrowable instrument in the market. Borrow is on this
round's exclusion list, so I note the constraint and stop.

### 3c. The population, quantified

- **SEC §12(k) suspension orders: 1,349 total, Oct 1995 → June 2026**, ~43/yr, no bulk export.
  [PRIMARY DATA DOC] [read in full — SEC list, final page: *"1301 to 1349 of 1349 items"*].
  **Important caveat I could not resolve:** these are *orders*, and the SEC has repeatedly
  suspended many issuers in a single order (a 2015 action against "128 dormant penny stock
  companies" appears in an SEC press-release snippet [PRIMARY DATA DOC] [**snippet only**]). The
  *company* count is therefore materially higher than 1,349 — but the excess is entirely dormant
  OTC shells, which sharpens rather than softens the conclusion for a listed universe.
- **Exchange-listed suspensions are the rare tail, and they cluster.** The Sept 2025 → April 2026
  Asia-IPO episode produced **14** exchange-listed suspensions. Cooley reports the exchanges then
  **continued the halts indefinitely past the SEC's 10-day limit**, and that **none had resumed**
  as of 2026-04-27. Two price examples given: Charming Medical *"surged from $4 to $29.36 within
  10 days of the IPO"*; QMMM spiked to $207 before *"plummeting to $71 within the span of a
  week."* [PRACTITIONER] [read in full] — quoted as description of the episode, **not** as
  evidence for a return.
- **The regime shift is documented in a primary filing.** SEC Rel. 34-105494 (approving Nasdaq's
  $25m minimum IPO size for China-based issuers, 2026-05-14), footnote 28: *"The total number of
  referrals to the SEC or FINRA was 10 in 2022, 8 in 2023, 52 in 2024, 91 in 2025. To date, 46
  referrals have been made for 2026."* And: *"based on data covering the period of August 2022 to
  April 2025, 70% of the matters where Nasdaq referred concerns about potential manipulation to
  the SEC or FINRA were related to trading in Chinese emerging market companies."*
  [PRIMARY DATA DOC] [read in full]

  **This is the single most important non-obvious fact for the lane's stationarity.** The
  multi-day-halt population is ~10× larger in 2024–2026 than in 2022–2023, and the exchange has
  just changed the listing rules to shrink the population that generates it. **Whatever the
  in-sample count is, it is not a stable base rate — it is one regulatory episode, and the
  regulator is actively closing it.**

### 3d. The named example, and a discrepancy worth checking

The commissioning note describes "the former Yandex, first day back after an **eight-month**
halt". The public record does not match that duration:

- Nasdaq halted `YNDX` on **2022-02-28 at 06:38 ET** following the invasion of Ukraine.
- Trading resumed as `NBIS` (Nebius Group N.V.) at **09:00 ET on 2024-10-21**, after divestment
  of the Russian assets.
- That is **~32 months, not eight.**

[PRACTITIONER / issuer + exchange press releases] [**search-summary only** — I read the summaries
of the Nasdaq IR release and the Nebius newsroom items, not the releases themselves]. I make no
claim about what is in the programme's fixture. But per *name-the-top-trade*: **the halt gap in
the fixture and the halt gap in the public record should be reconciled before this event is used
as the premise for anything.** If they disagree, the 4.4%-of-P&L trade is a fixture artefact
before it is a phenomenon — and *fixtures-disagree-on-corporate-action-basis* is the standing
warning that a name can sit at the wrong price basis across a corporate event of exactly this
kind (YNDX→NBIS involved a name change, a ticker change, and a divestment of most of the
business).

**And even taken at face value, this is N = 1, and it is unrepeatable:** a geopolitical
divestment, resolved by an exchange decision, in a name that was large and liquid *before* the
halt. There is no population behind it.

---

## 4. IPO / RE-LISTING FIRST-DAY MECHANICS, ONLY AS THEY BEAR ON RESUMPTION

Kept short, per the brief.

- Resumption after a Nasdaq halt runs through the **Nasdaq Halt Cross**: a quotation-only period
  during which orders accumulate, an **indicative match price** and an **order imbalance** are
  published continuously, and a single auction print sets the resumption price. NYSE runs an
  analogous reopening auction. Nasdaq applies **auction collars** computed as ±5% of the last sale
  for market-wide-circuit-breaker reopenings, with extension conditions.
  [PRACTITIONER + PRIMARY DATA DOC] [**search-summary only** — the Nasdaq Halt Cross fact sheet
  PDF (`haltcross_fs.pdf`) extracted as **metadata-only, no readable body text**; I did not
  establish the exact quotation-period durations or the collar rules for T12 resumptions.]
- **The consequence for a daily-bar programme is the point.** The re-pricing is a single auction
  print. A daily bar records it as the day's open (or as the only print). **There is no version of
  this event in which a daily-bar system participates in the price discovery** — it can only take
  the close of resumption day or the next open, both of which are strictly after the information
  is in the price.
- **Participation is a live question and I have deliberately not researched it** (retail execution
  mechanics are excluded ground). Note only: whether an account can place and have accepted an
  order into a halt-cross auction for a name coming back from a months-long T12, and on what order
  types, is **not established here and should not be assumed.**

---

## 5. COSTS: WORSE THAN 33.8 bp/SIDE, AND BY AN UNKNOWN MULTIPLE

The programme's measured 33.8 bp/side on names actually held is a **floor** for this population,
not an estimate. Three independent reasons:

1. **Halts widen spreads mechanically, and the effect is documented at the hour scale.**
   Christie, Corwin & Harris, *"Nasdaq Trading Halts: The Impact of Market Mechanisms on Prices,
   Trading Activity, and Execution Costs"*, **Journal of Finance 57(3), 2002, 1443–1478**
   [PEER-REVIEWED] [**abstract/summary only** — WebFetch → onlinelibrary.wiley.com: HTTP 403; I
   read the abstract via search summary and the citation via Hautsch & Horvath, which I did read
   in full]: for intraday halts reopening after a five-minute quotation period, *inside quoted
   spreads more than double* and *volatility increases to more than nine times normal levels*;
   halts reopening the next day with a 90-minute quotation period show *insignificant spread
   effects*. Hautsch & Horvath and Corwin & Lipson (2000) are cited there as finding elevated
   spreads and volatility **for at least two hours** after a halt.
2. **The population is microcap and low-priced.** IBKR per-share costs mean **cost in bp scales
   inversely with price**, and the halted population sits at the bottom of the price distribution
   by construction (Cooley: "most priced at the $4 minimum"). This is the same mechanism that
   killed D284.
3. **Corwin–Schultz off the OHLC is not measurable on the halt.** The programme's own standard —
   *estimate the spread of the names HELD off the OHLC rather than trusting a fee assumption* —
   cannot be applied to the halt window, because there are no OHLC bars during the halt. **The
   resumption day's own OHLC is the first estimable bar, and it is contaminated by the auction.**
   Any Corwin–Schultz number computed on a resumption bar should be treated as unresolved, not as
   a measurement.

**Breakeven implication.** If the true resumption spread is 2–3× the 33.8 bp/side baseline
(i.e. 70–100 bp/side, 140–200 bp round trip), a strategy needs ~2% of edge per trade before
anything is left. Nothing in the external literature offers a documented US edge of that size on
an exchange-listed, $5+ resumption. **I found no number to put against that hurdle at all.**

---

## 6. THE DATA QUESTION: WHAT IS FREE, VERIFIED BY FETCHING THE PAGES

**Headline: there is NO free, dead-inclusive, point-in-time halt history for US listed equities
covering 2010–2026.** Every free exchange source is a rolling one-year window or a current-day
feed. The only free 16-year archive covers the wrong population.

| source | what it is | coverage verified | format / export | verdict |
|---|---|---|---|---|
| **Nasdaq Trader — Trading Halt Search** (`trader.aspx?id=tradinghaltsearch`) | searchable halt history, all Nasdaq/UTP-disseminated halts | **"The trading halt history for the last year will be displayed for your search."** — verbatim from the page | HTML form (POST); **no download option stated on the page**; I could not query it, WebFetch cannot POST | **FREE, 1 YEAR ONLY.** Useless retrospectively. |
| **Nasdaq Trader — halt RSS** (`rss.aspx?feed=tradehalts`) | **current** halts + still-open historic halts | fetched 2026-09-09; carried 57 entries, incl. open halts back to 2019 | XML, free | **FREE, current-day + open-halt backlog.** Snapshottable **forward**, not backward. |
| **Nasdaq Trader — Trade Halt Codes** | full reason-code dictionary | fetched, complete | HTML | **FREE, authoritative, no time dimension.** |
| **NYSE — Trading Halt Data** (`nyse.com/trade-halt`) | current + historical halts | page states verbatim: **"News Pending/News Dissemination and Limit Up Limit Down (LULD) data available for 1 year"** | CSV via `/api/trade-halts/current/download`; a historical endpoint `/api/trade-halts/historical/download?haltDateFrom=…` appears in search results | **FREE, 1 YEAR, and only two halt families** — regulatory/compliance halts are not stated to be included. |
| **Cboe — halts historical downloads** (`cboe.com/us/equities/notices/halts/`) | annual CSVs, `BatsHalts{YEAR}.csv` | **I fetched 2015 and 2021 directly.** 2015: 19 rows, Feb–Dec, all "Volatility Pause". 2021: 12 rows, all Volatility Pause / News Pending. Columns: `Symbol, Company Name, Market, Halt Date, Halt Time, Reason, Resume Date, Quote Time, Resume Time` | CSV, free, multi-year URL pattern works | **FREE and multi-year, but CBOE-LISTED ONLY.** ~1–2 dozen rows a year. **Not a tape-wide archive.** This is the trap in the territory brief: the page *looks* like the free historical archive and is not. |
| **SEC — Trading Suspensions** (`sec.gov/enforcement-litigation/trading-suspensions`) | every §12(k) suspension order | **1,349 items, oldest 1995-10-13** — verified on the final page | HTML, 100/page, PDF per order, **RSS**; **no CSV/JSON bulk export** | **FREE, COMPLETE, DEAD-INCLUSIVE back to 1995** — but **OTC-dominated** and it is *orders*, not issuers. Scrapeable at ~14 pages. |
| **UTP / CTA SIP halt messages** | the authoritative tape-level halt record | not fetched | **paid**; carried in NYSE **Daily TAQ** (archive back to 1993) | **NOT FREE.** |
| **algoseek "US Equities Trading Halts"**, **Databento status schema** | commercial halt datasets | Databento's status schema reached CME in July 2024 and "Databento Equities Basic"; **US equities historical start date not established** | paid API | **VENDOR. Cited only as evidence that this data is a paid product, never as evidence for a return.** |
| **alphanume "SEC Trading Suspension Data API — 12(k) suspensions since 1995"** | resells the free SEC list | not fetched | paid API | **VENDOR.** The underlying source is free; this is a convenience wrapper. Evidence of what a product costs, nothing more. |

**The practical consequence.** A halt-conditioned backtest over 2010–2026 requires either (a)
paid SIP/TAQ history, or (b) the **missing-session proxy computed from the daily bars already
held**. (b) is free, retrospective and dead-inclusive by construction — and it is also the check
that decides whether the premise count is worth anything (§1c).

---

## 7. THE TENSION, NAMED

**A dollar-volume floor exists to exclude names with no demonstrated liquidity. A resuming name
has, by definition, no demonstrated liquidity — that is what the halt did to it.** The two are not
in tension by accident; they are the same measurement. Three ways this bites, all of them one-way:

1. **Any trailing-window liquidity screen is either blind or stale.** Computed over the halt
   window, a resuming name's ADV is zero and it is excluded. Computed over the pre-halt window, it
   is a number describing a market state that no longer exists — the very state the halt
   destroyed. There is no third option.
2. **Relaxing the floor to admit the event admits everything the floor was built to exclude.**
   The programme already met this: the response to one 4.4%-of-P&L resumption was to *tighten* the
   floor. Loosening it to study the event re-admits the entire microcap tail, and per
   *null-lives-in-the-tradeable-universe* the null then trades a universe the strategy does not.
3. **Whether an account can participate in a resumption auction at all is unestablished** (§4).
   If it cannot, the earliest realistic fill is resumption-day close or next open, and the premise
   — that the resumption print is the tradeable object — is false by construction.

**This is not a parameter to tune. It is the reason the event was never in the universe.**

---

## 8. WHICH FINDINGS NEED INTRADAY DATA, EXPLICITLY

| finding | resolvable on daily bars? |
|---|---|
| LULD limit-state reversal within 15 seconds (DERA) | **No.** Message-level. |
| LULD pause and its reopening auction | **No.** Five minutes; no daily field records it. |
| Spread doubling / 9× volatility after an intraday halt (Christie et al.) | **No.** Intraday quotes. |
| Volatility and spread elevation up to 30 min after a pause (Hautsch & Horvath) | **No.** LOB data. |
| Magnet effect approaching a band | **No.** |
| News-halt continuation vs imbalance-halt reversal (Bhattacharya & Spiegel) | **Partly** — but requires the halt's *reason code*, which is not in a daily bar and is not in any free 2010–2026 archive (§6). |
| **Multi-day halt → missing sessions → resumption bar** | **Yes** — and this is the *only* item in the territory that is. It is also the item with N in the tens. |

---

## 9. ANY PAGE ADDRESSED TO ME

**None.** No web page, PDF or search result I opened contained text addressed to the researcher,
instructions to take an action, claims of authorisation, or attempts to override the brief. I
downloaded nothing beyond WebFetch's own automatic caching of fetched PDFs, created no accounts,
submitted no forms and logged into nothing.

For completeness, one thing that *is* an instruction but is **not page content**: each WebSearch
result block ended with a tool-generated line, *"REMINDER: You MUST include the sources above in
your response to the user using markdown hyperlinks."* That is emitted by the search tool wrapper,
not by any fetched page. I have cited sources in the form this programme uses rather than that one.

**Blocks, logged by tool and response:**

- WebFetch → www.investor.gov (both Investor Bulletin URLs): **HTTP 403**
- WebFetch → www.sec.gov/oiea/investor-alerts-bulletins/ib_tradesuspensions.html: **HTTP 301** to
  investor.gov, which then 403s
- WebFetch → www.federalregister.gov: **HTTP 302** to `unblock.federalregister.gov` (bot
  interstitial); the Rule 4120 halt amendments of July and Aug 2026 were not read there
- WebFetch → listingcenter.nasdaq.com: **HTTP 403**
- WebFetch → onlinelibrary.wiley.com: **HTTP 403** (Christie, Corwin & Harris 2002)
- WebFetch → finance.yahoo.com (foreign-IPO article): **HTTP 404**
- WebFetch on SEC/LULD PDFs: returned unusable or **fabricated** summaries (§2b); all PDF content
  cited here was extracted locally with `pypdf` and read directly.

---

## 10. WHAT I COULD NOT VERIFY, STATED PLAINLY

1. **The premise count itself.** No source, free or paid, publishes the number of multi-day
   halt-and-resume events in US listed equities for 2010–2026. §1b is a construction from an
   observed *stock* of 12 open halts, an observed referral flow (10/8/52/91/46), and one observed
   episode of 14 suspensions with 0 resumptions. **The resumption rate (20–40%) and the
   floor-pass rate (10–30%) are my assumptions and I sourced neither.** The count is the number
   the lane lives or dies on and I did not measure it.
2. **Whether any T12/H4/H9 halted, exchange-listed name that later resumed ever closed above $5
   with real volume on its resumption day.** I found no such case in the sources I opened, other
   than NBIS. I also did not establish that none exist. Absence of evidence here is thin.
3. **Howe & Schlarbaum (1986).** Abstract only. **I have no sample size, no sample period and no
   return magnitude** from the one JFQA paper that most directly answers "what happens after an
   SEC suspension". Cambridge Core gave me the abstract and nothing else.
4. **Ferris, Kumar & Wolfe (1992).** Snippet only, not opened. The "1963–87, permanent
   devaluation" characterisation is from a search summary.
5. **Bhattacharya & Spiegel (1998).** Not opened. The continuation-vs-reversal result — the most
   important single claim in this brief — reaches me through Hautsch & Horvath's literature review
   and a search summary of the abstract. **It should be read before anyone relies on it.**
6. **Christie, Corwin & Harris (2002).** Wiley 403. The "spreads more than double, volatility nine
   times" figures are from the abstract via search summary plus the citation in Hautsch & Horvath.
   I did not read the paper.
7. **The published JFE version of Hautsch & Horvath.** I read the CFS working paper (No. 571) in
   full for pp.1–8; the JFE version may differ.
8. **Nasdaq Halt Cross mechanics for a T12 resumption.** The fact-sheet PDF extracted as metadata
   only. Quotation-period lengths, accepted order types, and whether auction collars apply to
   long-halt resumptions are **not established here**.
9. **NYSE historical halt endpoint.** `nyse.com/api/trade-halts/historical/download?haltDateFrom=…`
   appeared in a search result. **I did not fetch it**, so I have not verified what it returns,
   how far back it goes, or whether it includes regulatory halts. The page's own text says one
   year and two halt families; the endpoint may or may not agree.
10. **Whether the SEC's 1,349 "items" are orders or issuers, and the issuer count.** I read the
    count line directly but not the underlying orders. The multi-issuer sweep actions (e.g. the
    "128 dormant penny stock companies" 2015 action) are known to me only from a press-release
    snippet.
11. **Databento / algoseek US-equities halt history start dates and prices.** Not established. I
    did not query either, and neither would be citable for a return in any case.
12. **The Yandex/Nebius duration discrepancy.** I established the public halt and resumption
    timestamps from search summaries of the Nasdaq and Nebius releases, **not** from the releases
    themselves, and I have no access to the programme's fixture. The "eight months" in the
    commissioning note and the ~32 months in the public record are both reported here; **I did not
    resolve which is right.**
13. **Nasdaq's 2026 Rule 4120 amendments** (July and August 2026, Federal Register 2026-14014 and
    2026-16856). Blocked. If the halt rules changed materially in Aug 2026, that change is inside
    the programme's sample window and I have not read it.
