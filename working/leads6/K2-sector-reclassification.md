# K2 — GICS / sector reclassification and sector-ETF forced flow

External evidence only. I have no access to the programme's data and claim nothing about it.
Researched 2026-09-10. Scratchpad artefacts: `K2_*` under the session scratchpad
(`K2_docs/`), including every PDF read, the SEC N-PORT cache, and the five scripts whose
outputs are quoted below.

**Scope boundary held.** Everything below is about a company changing GICS *sector* while
its *index membership* is unchanged. Index additions, deletions and reconstitution flows
are out of scope and are not used as evidence, except where explicitly invoked as a
size comparison (clearly marked).

---

## 0. VERDICT FIRST — the flow is small relative to ADV, and the event count is worse

**The flow is small.** For the median S&P 500 name, the Select Sector SPDR that holds it
would have to sell **0.92 × its median daily dollar volume** if it were reclassified out
(q05 0.32, q25 0.61, q75 1.29, q95 2.82; n = 503 names, measured, §2). Worse for the
premise, the flow is **two-sided and nearly self-cancelling**: the old sector's fund sells
and the new sector's fund buys *at the same close*, so the net is the difference of two
similar numbers. Across all 20 sector migrations that actually happened in the last seven
years, the measured **net flow was a median 0.33 × ADV and a maximum of 0.70 × ADV** — that
maximum being Visa in March 2023, the single largest sector reclassification in the S&P 500
in at least seven years. For comparison the programme's own spent territory, index
additions, moves one-sided flow of several days' ADV. This lane's forced flow is roughly an
order of magnitude smaller *and* it is crossed against itself.

**The count is the kill.** Measured from SEC filings, gapless, 2019-09-30 → 2026-06-30
(27 consecutive quarter transitions): **20 S&P 500 GICS sector migrations in total, of which
17 occur at a single structure change (March 2023).** Idiosyncratic, between-review
reclassifications number **three in 6.75 years — Leidos, Teledyne, Roper — i.e. 0.44 per
year.** The last **twelve consecutive quarters (2023-06-30 → 2026-06-30) contain zero.**

**And the effect the literature does report is at the announcement, ~11 months early.** The
2023 change was announced 2022-03-31 and the full affected-name list published
2022-12-15, 92 days before the 2023-03-17 effective date. Every event study I located
(all on the 2016 real-estate event) finds its abnormal return at an *announcement*, and one
of them reports trading volume "not discernibly impacted".

**Disposition: I would not open this lane.** Not because the mechanism is fake — it is real
and genuinely mandate-driven — but because it produces under one tradeable event per year in
a fixture whose effective breadth is already ~10 independent instruments, and the flow it
produces is a fraction of a day's volume, netted. It fails on cause #2 of the programme's six
recurring killers (too few events) more severely than any territory would need to.

One genuine positive, stated so it is not lost: **the lane is clean on price and on cost.**
See §1.

---

## 1. PRICE FIRST (per the standing rule: size is not price)

Before any magnitude. The 20 names that actually migrated sector, priced at the quarter of
their migration (Yahoo daily closes, §6 for the data route):

| statistic | price |
|---|---|
| min | **$74.39** (PayPal, 2023Q1) |
| q25 | $113.00 |
| median | **$147.98** |
| q75 | $222.36 |
| max | $432.52 (Teledyne, 2021Q3) |
| names under $5 | **0** |

And for the broader question "what would a reclassifiable name look like", the price
distribution of all 503 current S&P 500 names for which I have a price: min $10.80, median
$145.74, max $6,116.86, **zero under $5**.

Consequences, which are favourable and should be recorded as such:

- The **$5 as-traded-close floor is satisfied by construction**. This lane cannot be a
  low-priced-names artefact. That is a real distinction from the eleven dead territories.
- IBKR commission at ~50/P bp is **~0.34 bp/side** at the $148 median, versus ~10 bp/side at
  $5. Negligible.
- These are mega- and large-cap S&P 500 constituents. The programme's measured 33.8 bp/side
  spread on its *held* names is not the relevant number here; spreads on Visa, Mastercard,
  Target, ADP are materially tighter. **I did not measure Corwin-Schultz spreads on these
  names** — I have no OHLC fixture — so I state only that the cost side of this lane is
  structurally favourable, not by how much. That is §9 item 4.

The trap is that **none of this matters** if there are 0.44 events a year.

---

## 2. THE FLOW ARITHMETIC — measured, not estimated

This is the section the brief asked to be the whole lane, so I measured it rather than
reasoning about it.

### 2.1 How much money sits in GICS sector funds

Select Sector SPDR AUM, backed out of SSGA's own daily holdings files as
`shares_held × price / weight`, holdings as of 2026-09-08, closes as of the same tape:

| fund | sector | AUM ($bn) | holdings | sector share of S&P 500 float |
|---|---|---|---|---|
| XLK | Info Tech | **122.3** | 76 | 38.37% |
| XLF | Financials | 54.5 | 80 | 12.63% |
| XLV | Health Care | 43.4 | 63 | 9.39% |
| XLE | Energy | 42.3 | 24 | 3.81% |
| XLI | Industrials | 31.7 | 86 | 8.56% |
| XLC | Comm Svcs | 22.6 | 27 | 9.87% |
| XLU | Utilities | 22.6 | 34 | 2.33% |
| XLY | Cons Disc | 21.8 | 50 | 9.26% |
| XLP | Cons Staples | 14.6 | 38 | 4.89% |
| XLB | Materials | 8.5 | 28 | 2.09% |
| XLRE | Real Estate | 8.2 | 33 | 2.08% |
| **total** | | **392.5** | | |

*Internal control on this method:* the six largest holdings of each fund give six
*independent* estimates of the same AUM. They agree to **< 0.005%** in every one of the
eleven funds — the weights and share counts in SSGA's file are mutually consistent with a
single price vector. *External control:* the Select Sector SPDR Trust's own SEC N-PORT
filing reports XLK `netAssets` = **$123.91 bn** at 2026-06-30 against my $122.3 bn at
2026-09-08. Two unrelated sources, 1.3% apart across a 10-week gap. The method holds.

Vanguard's GICS sector funds, from Vanguard's own factsheets (2026-06-30). Note the
**ETF-share-class vs whole-fund distinction** — Vanguard ETFs are share classes, and it is
the *fund* that rebalances:

| fund | ETF class ($M) | **whole fund ($M)** | stocks | benchmark |
|---|---|---|---|---|
| VGT Info Tech | 146,578 | **169,218** | 321 | MSCI US IMI/Information Technology 25/50 |
| VNQ Real Estate | 38,203 | **71,396** | 143 | MSCI US IM Real Estate |
| VHT Health Care | 17,806 | 20,389 | 423 | MSCI US IMI/Health Care 25/50 |
| VFH Financials | 12,743 | 13,933 | 428 | MSCI US IMI/Financials 25/50 |
| VDE Energy | 9,013 | 10,986 | 111 | MSCI US IMI/Energy 25/50 |
| VIS Industrials | 8,480 | 9,088 | 396 | MSCI US IMI/Industrials 25/50 |
| VDC Cons Staples | 7,802 | 9,182 | 103 | MSCI US IMI/Consumer Staples 25/50 |
| VPU Utilities | 8,669 | 10,764 | 68 | MSCI US IMI/Utilities 25/50 |
| VCR Cons Disc | 6,226 | 6,827 | 283 | MSCI US IMI/Consumer Discretionary |
| VOX Comm Svcs | 5,658 | 5,945 | 112 | MSCI US IMI/Communication Services |
| VAW Materials | 3,030 | 4,473 | 111 | MSCI US IMI/Materials 25/50 |
| **total** | **264.2bn** | **332.2bn** | | |

**A material subtraction.** The second-largest US sector-ETF suite is **not GICS at all.**
iShares U.S. Technology (IYW, **$25.14 bn** net assets as of 2026-09-09) tracks the
**Russell 1000 Technology RIC 22.5/45 Capped Index** — FTSE Russell, classified under **ICB**,
not GICS, since FTSE Russell migrated the Russell US indexes from RGS to ICB in 2020. The
whole iShares U.S. sector suite therefore **does not trade on GICS dates at all**. Any
headline "sector ETF AUM" figure overstates the GICS-mandated pool.

### 2.2 The two legs, and why they cancel

For a name reclassified out of sector A into sector B:

- **SELL leg** = (its weight in A's fund) × (A's fund AUM) — forced, dated, unambiguous.
- **BUY leg** = (its float weight within B) × (B's fund AUM) — equally forced.

Both are of the same order, because the ratio *sector-fund AUM ÷ sector float market cap*
is similar across sectors (the right-hand column of §2.1 against the AUM column: $2.3–$4.6 bn
of fund per 1% of S&P 500 for eight of eleven sectors; Energy and Utilities are the outliers
at $11.1 bn and $9.7 bn). **Unlike an index addition, which is one-sided, a sector
reclassification is a simultaneous buy and sell of comparable size at the same close.** The
tradeable quantity is the *difference*, and an ETF market maker can cross most of it.

### 2.3 The distribution across every S&P 500 name — KILL NUMBER (b)

Sell-leg size as a multiple of median 6-month daily dollar volume, **SPDR family only**,
all 503 current S&P 500 lines with a price and a volume:

| quantile | sell / ADV | name at that quantile |
|---|---|---|
| q05 | 0.32 | TSCO |
| q25 | 0.61 | KHC |
| **q50** | **0.92** | MSFT |
| q75 | 1.29 | ITW |
| q95 | 2.82 | ES |

### 2.4 The measured flow for every event that actually happened

Not a hypothetical. For each of the 20 observed migrations, sell leg = (weight in the old
sector fund at quarter t−1) × (that fund's `netAssets` at t−1) and buy leg = (weight in the
new sector fund at t) × (that fund's `netAssets` at t), both read straight out of the SEC
N-PORT filings, divided by the name's median daily dollar volume over that quarter:

| name | quarter | from → to | px | ADV $M | sell $M | buy $M | sell/ADV | **net/ADV** |
|---|---|---|---|---|---|---|---|---|
| Mastercard | 2023Q1 | IT → Fin | 359.26 | 1,013 | 1,382 | 2,042 | 1.36 | 0.65 |
| **Visa** | 2023Q1 | IT → Fin | 222.36 | 1,207 | **1,591** | **2,440** | 1.32 | **0.70** |
| Teledyne | 2021Q3 | Ind → IT | 432.52 | 99 | 121 | 85 | 1.22 | 0.36 |
| ADP | 2023Q1 | IT → Ind | 219.49 | 416 | 464 | 428 | 1.12 | 0.09 |
| Broadridge | 2023Q1 | IT → Ind | 145.11 | 71 | 74 | 80 | 1.04 | 0.09 |
| Roper | 2022Q2 | Ind → IT | 393.55 | 267 | 267 | 186 | 1.00 | 0.30 |
| CoStar | 2023Q2 | Ind → RE | 90.12 | 132 | 130 | 181 | 0.99 | 0.38 |
| Paychex | 2023Q1 | IT → Ind | 113.54 | 189 | 174 | 171 | 0.92 | 0.02 |
| Fiserv | 2023Q1 | IT → Fin | 113.00 | 361 | 301 | 478 | 0.83 | 0.49 |
| Leidos | 2021Q1 | IT → Ind | 96.67 | 77 | 61 | 86 | 0.80 | 0.32 |
| Jack Henry | 2023Q1 | IT → Fin | 147.98 | 79 | 60 | 73 | 0.75 | 0.17 |
| Global Payments | 2023Q1 | IT → Fin | 103.19 | 169 | 126 | 184 | 0.74 | 0.35 |
| Target | 2023Q1 | CD → CS | 160.27 | 459 | 284 | 577 | 0.62 | 0.64 |
| Dollar General | 2023Q1 | CD → CS | 207.69 | 404 | 230 | 361 | 0.57 | 0.33 |
| Paycom | 2023Q2 | IT → Ind | 313.68 | 149 | 84 | 73 | 0.56 | 0.07 |
| Dollar Tree | 2023Q1 | CD → CS | 140.81 | 280 | 123 | 229 | 0.44 | 0.38 |
| PayPal | 2023Q1 | IT → Fin | 74.39 | 903 | 380 | 572 | 0.42 | 0.21 |
| FleetCor, FIS, Ceridian | — | — | — | (no Yahoo history under old ticker) | 63 / 189 / 65 | 104 / 215 / 49 | — | — |

**Summary: sell/ADV median 0.83, max 1.36. Net/ADV median 0.33, max 0.70.**

The largest sector reclassification of an S&P 500 constituent in seven years — Visa, 1.1% of
the index, moving out of the largest sector fund in the market — generated a net SPDR-family
imbalance of about **$0.85 bn against a $1.2 bn ADV**.

Scaling to all GICS families does **not** rescue this, for a timing reason given in §3:
SPDR-tracking and MSCI-tracking funds move on *different dates two and a half months apart*,
so the flow on any one date is roughly one family's worth, not the sum.

### 2.5 The one independently-published flow figure, for triangulation

MSCI's own implementation deck gives **simulated one-way index turnover** for the 2023
change on MSCI USA sector indexes: **Financials 20.4%, Information Technology 11.7%,
Consumer Staples 6.6%, Industrials 6.1%, Consumer Discretionary 4.3%.** Applied to VFH's
$13.9 bn that is ~$2.8 bn of turnover — but **spread over eight names, at the May review, on
a different date from the SPDR flow.** This is the issuer's number and it is consistent with
mine in magnitude. It is also the number most likely to be quoted at me as evidence the lane
is big; note that a 20.4% sector-index turnover divides into per-name flows of well under a
day's volume.

---

## 3. ANNOUNCEMENT OR EFFECTIVE DATE? — announcement, and by a mile

This is documented precisely, in primary sources, and it is bad for the lane.

For the **2023 structure change** (S&P DJI / MSCI joint press release, 2022-03-31, read in full):

| milestone | date | days before effective |
|---|---|---|
| consultation results + structure change announced | 2022-03-31 | **351** |
| "select list of large market capitalization companies affected" | by 2022-06-30 | 260 |
| **full list of affected companies to clients** | by 2022-12-15 | **92** |
| implemented in GICS Direct and S&P DJI indices, after the close | **2023-03-17** | 0 |
| **implemented in MSCI Equity Indexes — May 2023 Index Review** | ~2023-05-31 | **−75** |

Three things follow.

1. **The names are known ~3 months ahead and the change itself ~1 year ahead.** This is the
   textbook setup for the move to be fully priced before anything mechanical happens. Every
   event study I found (§4) locates its abnormal return at an announcement.
2. **The flow is deliberately split across two dates 2.5 months apart.** S&P-tracking funds
   (the SPDRs, Invesco's equal-weight sector suite, S&P-benchmarked mandates) move at the
   2023-03-17 close. MSCI-tracking funds (Vanguard's $332 bn, Fidelity's MSCI sector suite)
   move at the **May** Index Review. SSGA's own note says exactly this: "Sector ETFs that
   follow MSCI World and MSCI Europe indices will reflect the changes made at the next
   quarterly index review on 31 May 2023." A forced flow that is pre-announced *and*
   deliberately staggered is the opposite of a shock.
3. **2026 consultation → the pipeline is thin.** A live consultation opened 2026-07-17,
   closes 2026-10-30, changes announced November 2026 (so effective ~March 2027). Its
   proposals are **sub-industry and industry level**: restructuring the Semiconductors
   sub-industry, AI/HPCaaS definitions, foundation-model developers, Application Software,
   and "Classification of Listed Investment Companies". I see **no proposed new sector and no
   obvious cross-sector migration of S&P 500 constituents** in it. GICS has gone from 10 to
   11 sectors in 27 years.

### The earnings confound — in this lane's favour, with one caveat

The announcement is an **index-provider press release, not a company filing**, so it
co-files with nothing and the quarterly-earnings bundling that killed other territories does
not apply. **Fraction co-filing with earnings: zero, by construction.** Record that as a
point in the lane's favour.

**The caveat that undoes most of it:** the *idiosyncratic* reclassifications — the only ones
that happen between structure changes — are triggered by a change in the company's business
mix, which is itself earlier, larger news. Roper Technologies (Industrials → Info Tech,
2022Q2) had on 2022-06-01 agreed to sell a majority stake in its industrial businesses to
Clayton, Dubilier & Rice for ~$2.6 bn, and Roper's own 10-K states it would thereafter
benchmark against the S&P 500 Information Technology index. The GICS move was a *lagging
consequence of a disclosed corporate action*. So for the 0.44 events/year that are not part
of a structure change, the reclassification is confounded by — and predictable from — a prior
corporate event. Both branches of the lane lose their surprise, for different reasons.

---

## 4. THE BIG SCHEDULED EVENTS AND WHAT IS ACTUALLY DOCUMENTED

### 4.1 2016 — creation of the Real Estate sector (11th sector; GICS 2016-08-31, S&P index 2016-09-16)

This is where essentially all the academic literature is, and it is a **poor template** for
K2: it created a *new* sector with no pre-existing sector fund to do the buying (XLRE was
launched for it), it is confined to REITs, and it coincided with a Nareit-led promotional
effort and new S&P index products. Four papers, all on this one event:

- **Stevens**, "Do Changes in Industry Classification Systems Matter? Evidence from REITs",
  *Journal of Real Estate Research* 44(3), 2022. [PEER-REVIEWED] [abstract only — publisher
  403]. Reports **significant abnormal returns of 2.31% and 2.49% around two distinct
  announcements**; cross-sectional regressions show higher abnormal returns for **medium-cap**
  REITs, lower leverage, higher institutional ownership. **Both effects at announcements.**
- **Tang, Xie & Xu**, "Real estate as a new equity market sector: Market responses and return
  comovement", *Real Estate Economics*, 2020/2022. [PEER-REVIEWED] [abstract in full via
  Crossref; body 403]. "Real estate stocks experience **positive abnormal returns at the
  announcement** of new sector creation, and attract more investor attention after the
  announcement... comovement between real estate and financial stocks **decreases
  dramatically** after the new sector creation."
- **Fuller, Yamani & Yu**, "The impact of the new real estate sector on REITs: an event
  study", *Journal of Economics and Finance*, 2018. [PEER-REVIEWED] [abstract read in full].
  "Prior to the event date, REITs experienced **significant negative returns**. But after the
  event date, REITs also experienced **significant positive returns which dissipated over
  time**... While the magnitude of the trading volume increased noticeably prior to the event
  date, **overall trading volume was not discernibly impacted.**"
- **Bao, Brady & Wang**, "Pricing Efficiency and Bounded Rationality: Evidence Based on the
  Responses Surrounding GICS Real Estate Category Creation", *International Real Estate
  Review* 23(1), 2020, 37–63. [PEER-REVIEWED] [abstract only]. Abnormal returns at both the
  announcement and the S&P implementation; **largest for large-cap real estate stocks in the
  S&P 500**; frames it as improved pricing efficiency plus a framing effect.

**CONFLICT, recorded not adjudicated.** Stevens, Tang et al. and Bao et al. report *positive*
abnormal returns at announcement. Fuller et al. report *negative* returns **before** the event
date and positive returns after. They are not measuring the same window (announcement vs
effective) and may not be inconsistent, but the signs as stated disagree. **I would weight
Tang et al. and Stevens higher** — the journals are the stronger real-estate outlets and both
tie the effect explicitly to the announcement, which matches the §3 institutional timeline.
**But the Fuller et al. finding I would weight highest of all for this lane's purpose** is the
volume one: *overall trading volume was not discernibly impacted*. If a mandate-driven forced
flow large enough to move price had occurred, it should show in volume. That is direct
negative evidence against the mechanism, from the paper whose return signs I trust least.
Note also Bao et al.'s "largest for large-cap" versus Stevens' "medium cap" — a second,
narrower conflict I cannot resolve from abstracts.

### 4.2 2018 — Telecommunication Services → Communication Services (effective 2018-09-28)

The largest GICS change by market cap ever. I could find **no academic event study of it**
after targeted searching. What I can establish:

- Effective date **2018-09-28** [Fidelity, PRACTITIONER, read]. XLC launched 2018-06-18 —
  *three months before* the reclassification, so the buy-side vehicle existed and was funded
  in advance.
- Scale figures circulating (23 S&P 500 companies, ~$2.7 trn, 10% of S&P 500 market cap, 100%
  of telecom, 22% of consumer discretionary, 21% of tech) came to me **only through a search
  summariser**, not from a document I read. Per the summariser rule I record them as
  **[UNVERIFIED]** and do not rely on them. SSGA's own later note says the 2023 change was
  "less impactful than the moves in September 2018", which is consistent with 2018 being
  larger but is not a number.
- My own N-PORT series starts 2019-09-30 and therefore **cannot see the 2018 event.** That is
  a real coverage hole in my measurement, stated in §9.

### 4.3 2023 — the Data Processing / Retailers / REIT-granularity change (effective 2023-03-17)

Fully measured above. SSGA, the SPDR issuer, states: ~**4% of S&P 500 market cap
reclassified at sector level across 14 large-cap stocks**; IT→Financials 8 stocks = 2.7% of
the S&P 500 and 10.6% of the IT sector; IT→Industrials 3 stocks = 0.5%/1.9%;
ConsDisc→ConsStaples 3 stocks = 0.5%/4.9%. [SSGA = PRIMARY for the mechanics, SALES
INSTRUMENT for anything implying an opportunity; read in full.]

**Independent cross-validation of my whole method:** SSGA says "14 large cap stocks". My
N-PORT fund-migration count for the 2022-12-31 → 2023-03-31 transition returns **exactly
14**, and names them: Visa, Mastercard, Target, Dollar General, ADP, PayPal, Dollar Tree,
Fiserv, FIS, Paychex, Global Payments, Broadridge, FleetCor, Jack Henry. Two unrelated
sources, same count, same names.

### 4.4 The annual review cycle and between-review changes

GICS is reviewed annually; the structure has been revised **12 times since 1999** per the
provider's own materials, and the sector count has gone 10 → 11 in 27 years. Between
reviews, individual companies are reclassified when their business mix changes. MSCI's rule
for those: "If a security experiences a GICS reclassification due to a corporate event, it
will only be considered... during the **next regularly scheduled Index review**" — i.e. even
the idiosyncratic events are batched into a quarterly review, not traded on their own date.
For S&P DJI's US indices, index changes generally carry **one to five days' advance notice**
and the Select Sector indices reweight at the quarterly rebalance.

---

## 5. KILL NUMBER (a) — the event count, measured from SEC filings

### 5.1 Method, and why it is clean

The 11 plain Select Sector SPDR funds **partition the S&P 500 by GICS sector** — the S&P US
Indices methodology states it explicitly: "At each moment in time, the constituents of the
Select Sector Indices are all members of the S&P 500. Each constituent of the S&P 500 is
assigned to **one and only one** Select Sector Index." [PRIMARY DATA DOC, read.]

So: the Select Sector SPDR Trust's SEC **N-PORT-P** filings (CIK 1064641) reconstruct a free,
point-in-time GICS sector assignment for every S&P 500 constituent at every quarter end. A
CUSIP present in fund A at quarter t−1 and in fund B ≠ A at quarter t has **changed GICS
sector while remaining in the S&P 500** — exactly this territory's event, with index
add/delete excluded *by construction*, since the name must be present at both dates.

Coverage achieved: **352 filings, 28 quarter-end snapshots, 2019-09-30 → 2026-06-30, 27
consecutive transitions, zero gaps**, 473–479 company lines per snapshot.

**Two artefacts found and removed — both of the kind that would have produced a fabricated
result.** I report them because the numbers differ by 2.5×:

1. **Cash-sweep lines.** Every sector fund holds the same State Street Global Advisors
   money-market line under the *same CUSIP*, so it appears to "migrate" between sectors every
   quarter. Unfiltered, the count was **50**. Filtered, **20**. I only caught this by looking
   at the names rather than the count.
2. **Placeholder CUSIPs.** Foreign-domiciled issuers (PLC/Ltd) are filed with CUSIP
   `000000000`; several different companies collapse onto one dictionary key and fabricate
   migrations. This produced a list containing **Chicago Mercantile Exchange → Health Care,
   Eaton → Real Estate, Norwegian Cruise Line → Info Tech** — transparently false, and the
   tell was that the destinations made no sense. After excluding placeholder CUSIPs, two
   independently written filters agree on exactly the same 20 events.

**Zero-controls, reported beside the counts as required.** Every parameterised endpoint I
harvested was censused with a value that must return nothing:

| endpoint | real query | **zero-control** | control result |
|---|---|---|---|
| SSGA daily holdings xlsx by ticker | xlk…xlre → 200, 19–24 KB, weights sum 99.66–99.97% | `xlzz` | **404** |
| Yahoo chart API by ticker | 503 of 516 lines returned | `ZZZZQQ`, `ZZ9XQ` | **404, 404** |
| Vanguard fund-docs PDF by fund id | F0951…F0986 → 200, ~455 KB, parse clean | `FZZZZ` | **403, 111 bytes, not a PDF** |
| Vanguard SPA profile by ticker | vgt → 200, 267 KB | `zzqq9` | **200, 56 KB generic shell** ⚠ |

The Vanguard SPA control is the one that matters: **a bogus ticker returns HTTP 200 with a
plausible fund-profile page shell.** Anything harvested from that endpoint by URL-ticker
without a control would silently produce garbage. I did not use it; Vanguard numbers in §2.1
come from the fund-docs PDFs, whose control fails correctly.

### 5.2 The count

| transition | migrations | names |
|---|---|---|
| 2019Q3→Q4 … 2020Q3→Q4 (5) | **0** | — |
| 2020Q4→2021Q1 | 1 | Leidos (IT → Industrials) |
| 2021Q1→Q2 | 0 | |
| 2021Q2→Q3 | 1 | Teledyne (Industrials → IT) |
| 2021Q3→Q4, 2021Q4→2022Q1 | 0 | |
| 2022Q1→Q2 | 1 | **Roper** (Industrials → IT) |
| 2022Q2→Q3, Q3→Q4 | 0 | |
| **2022Q4→2023Q1** | **14** | the March-2023 structure change |
| 2023Q1→Q2 | 3 | CoStar (Ind→RE), Paycom, Ceridian (IT→Ind) |
| **2023Q2→Q3 … 2026Q1→Q2 (12 consecutive)** | **0** | **— nothing at all for three years** |
| **total** | **20** | over 27 quarters = 3.0/yr nominal |

**Reading this honestly:**

- **17 of 20 events are one structure change**, on one date (plus its three-name tail the
  following quarter). As a study population that is **n = 1 event, not n = 17** — the names
  share a date, a cause, and a direction, so they are one observation with 14 legs, not 14
  independent observations. This is the same trap as treating one market-level series as many.
- **Idiosyncratic reclassifications: 3 in 6.75 years = 0.44/year.** Generously counting the
  2023Q2 trio as individual gives 6 in 6.75 years = 0.89/year.
- **All 20 names pass a $5 close and any sane dollar-volume floor** (min price $74.39; min ADV
  $71 M/day, Broadridge). So the answer to kill number (a) as posed — events per year
  *touching names that pass the screens* — is **the same as the raw count: ~0.44/year
  idiosyncratic, plus one structure change every five to seven years.** The screens remove
  nothing here. There is simply almost nothing to remove.

### 5.3 What this does to breadth

The fixture's effective breadth is ~10 independent instruments across 1,573 names. This lane
delivers, over the whole 2010–2026 span, on the order of **three structure changes (2016,
2018, 2023) and perhaps a dozen idiosyncratic moves**, all in S&P 500 large caps that are
already the most correlated, most covered part of the universe. **It adds approximately zero
independent breadth.** Even a real, clean effect of 50 bp per event would be unmeasurable
against the nulls at this count, and the programme's own D373 rule (margin within 2 SE of the
p95 → UNRESOLVED) would almost certainly bite.

---

## 6. THE DATA QUESTION — what is free, what is paid, stated plainly

**The blunt answer: GICS classification history is a paid product.** GICS Direct is licensed
by S&P Dow Jones Indices and MSCI. There is no free, vendor-sanctioned point-in-time GICS
history. Current-day sector labels are scattered free across the web; *history with
as-of dates* is not.

**But the history is reconstructible free for S&P 500 names, and I demonstrated it.** Routes,
best first:

1. **SEC N-PORT-P filings of the Select Sector SPDR Trust (CIK 1064641).** ✅ *Demonstrated
   working.* Free, point-in-time, SEC-filed, legally attested. 352 filings give 28 quarterly
   snapshots 2019-09-30 → 2026-06-30 with a complete 11-sector partition at every one, plus
   each fund's `netAssets` for the flow arithmetic. Limits: **quarterly resolution only** (the
   public filing is the quarter-end month; a move and reversal inside a quarter is invisible,
   and the *exact effective date* is not pinned — you get ±1 quarter, which is not good enough
   to trade on and would have to be pinned from press releases); **S&P 500 only**; ~60-day
   public lag; starts 2019, so **it cannot see the 2018 event**.
   *Gotcha that cost me a run:* the document is `primary_doc.xml` for the `0001410368-*`
   filer agent but **not** for the `0001752724-*` agent used in 2021 — a parameterised-URL
   assumption that silently returned nothing and left a one-year hole that looked like
   "filings don't exist". Read each filing's `index.json` instead. Also: SEC throttles bursts;
   4 unpaced threads lost 286 of 352 filings with no error visible in the counts.
2. **Pre-2019:** the same trust has **21 N-Q filings** on EDGAR, extending the series back,
   quarterly, in a different format. I did not parse these.
3. **Today's snapshot, free and instant:** SSGA's daily holdings xlsx per fund
   (`holdings-daily-us-en-<ticker>.xlsx`) — name, ticker, CUSIP, SEDOL, weight, shares held.
   This is the file §2.1 is built on.
4. **Index-provider press releases and consultation documents** are free and are PRIMARY for
   dates and affected-name lists: the 2022-03-31 GICS press release, MSCI's implementation
   deck, the 2026 consultation. **This is the right source for exact effective dates**, which
   N-PORT cannot give you.
5. **Free proxies are poor.** SEC EDGAR stores the filer's SIC code in every filing header,
   which is genuinely free and genuinely point-in-time — but SIC is not GICS.
   Bhojraj, Lee & Oler (2003, *Journal of Accounting Research* 41(5), 745–774)
   [PEER-REVIEWED] [abstract read in full via Crossref] establish that **GICS is significantly
   better at explaining return comovement, valuation multiples and growth than SIC, NAICS or
   Fama-French, consistently year to year and "most pronounced among large firms"** — i.e.
   precisely for the large caps this lane lives in, a SIC proxy is at its worst.
   **I could not verify a specific GICS↔SIC agreement percentage.** Figures of "NAICS maps to
   SIC at 80%, Fama-French at 84%, GICS materially lower" reached me **only via a search
   summariser** and the number for GICS was truncated; SSRN returned a Cloudflare challenge
   and the publisher 403'd, so I never read the results table. **Per the summariser rule I
   record those as [UNVERIFIED] and do not use them.** What I will say on established ground:
   a SIC- or NAICS-based proxy for GICS sector is **not fit for dating a GICS reclassification
   event** — the schemes disagree on sample construction by design, and a proxy that
   mis-dates the event destroys the only thing the study would be measuring.

**Verdict on data:** the classification *history* for S&P 500 names is free via SEC filings
at quarterly resolution, and the *exact event dates* are free via provider press releases.
Combining the two is workable. Nothing free covers the non-S&P-500 part of a 1,573-name
universe, and nothing free gives daily-resolution sector history.

---

## 7. ADJACENT — methodology changes that reshuffle weights without changing membership

Short, as instructed, and it points the same way.

The Select Sector indices are **capped**, and the capping is where weight-only reshuffles
live [S&P U.S. Indices Methodology, PRIMARY DATA DOC, read — note this was an **older vintage**
obtained from a mirror, see §8, so treat the exact thresholds as indicative]:

- Rebalanced quarterly after the close of the **second-to-last calculation day** of March,
  June, September, December; reference date two business days prior to the last calculation
  day.
- If any company exceeds **24%**, it is capped at **23%** (a 2% buffer under the 25% RIC
  diversification limit); excess is redistributed equally to uncapped names, iteratively.
- The sum of companies weighing more than **4.8%** cannot exceed **50%** of the index; if
  breached, the largest offender is cut to **4.6%** and the excess redistributed to names
  below 4.6%, iteratively.

Two observations:

- These caps are **mechanical, dated, pre-announced and quarterly**, and they bind on the very
  largest names — a handful of mega-caps in XLK, XLC and XLE. That is a tiny, highly
  concentrated population in the most liquid names in the market, with the same breadth
  problem as §5.3, and it is *structurally closer to index reconstitution mechanics* than to
  the sector-membership question. It is also where the 2023 change had its most interesting
  second-order effect: loading Visa, Mastercard and PayPal into Financials pushed that
  sector's concentration up and changed which names the 25/20 caps bind on.
- Float adjustment (IWF) changes and share-count updates are applied at the same quarterly
  rebalance with the same advance notice. Same conclusion.

I did not research this further because it shades into INDEX RECONSTITUTION, which is
excluded ground.

---

## 8. SOURCES — tagged by TYPE and by how well established

**Primary, index provider (PRIMARY for methodology and dates; SALES INSTRUMENT for anything
performance-flavoured):**
1. S&P DJI / MSCI, "S&P Dow Jones Indices and MSCI Announce Revisions to the GICS Structure
   in 2023", press release, 2022-03-31. [PRIMARY DATA DOC] [**read in full**, 6 pp]. Source of
   the §3 timetable.
2. MSCI, "Implementation of the 2023 GICS Structure Changes in the MSCI Equity Indexes",
   October 2022, 15 pp. [PRIMARY DATA DOC] [**read in full** for pp 1–8]. Source of the
   **May 2023** implementation rule and the simulated one-way sector-index turnover
   (USA: Fin 20.4%, IT 11.7%, CS 6.6%, Ind 6.1%, CD 4.3%).
3. S&P DJI / MSCI, "Consultation on Potential Changes to the GICS Structure", 2026-07-17,
   24 pp. [PRIMARY DATA DOC] [read pp 1–4 + TOC]. Consultation opens 2026-07-17, closes
   2026-10-30, changes announced November 2026, for 2027. Sectors 10→11 since 1999.
4. S&P DJI, *S&P U.S. Indices Methodology*. [PRIMARY DATA DOC] [**read in full**, 30 pp] —
   but an **older vintage** retrieved from the `spice-indices.com` mirror (9 sectors, Technology
   = IT + Telecom), because the current file on `spglobal.com` is 403 to me. Select Sector
   partition rule and capping methodology.
5. Select Sector SPDR Trust, **SEC Forms N-PORT-P**, CIK 1064641, 352 filings,
   2019-09-30 → 2026-06-30. [PRIMARY DATA DOC] [**harvested and parsed in full**]. The
   event count and the measured per-event flow.
6. SSGA daily holdings files, 11 Select Sector SPDRs, as of 2026-09-08. [PRIMARY DATA DOC]
   [**parsed in full**]. Fund AUM and name weights.
7. Vanguard sector ETF factsheets, 11 funds, as of 2026-06-30. [PRIMARY DATA DOC]
   [**parsed in full**]. ETF-class vs whole-fund assets; MSCI US IMI 25/50 benchmarks.
8. iShares U.S. Technology ETF (IYW) product page, 2026-09-09. [PRIMARY DATA DOC]
   [read the relevant fields]. Net assets $25,135,161,553; benchmark **Russell 1000
   Technology RIC 22.5/45 Capped Index** — establishes the suite is ICB, not GICS.

**Practitioner / issuer commentary:**
9. SSGA (Chesworth), "GICS Changes Incoming: What it Means for S&P and MSCI Sectors",
   Feb 2023, 5 pp. [PRACTITIONER — and a **SALES INSTRUMENT**, SSGA is the SPDR issuer]
   [**read in full**]. 14 S&P 500 stocks, ~4% of index market cap; the per-bucket weights;
   and the statement that MSCI-tracking sector ETFs move at the 31 May 2023 review.
10. Fidelity, "Sectors Are Shifting: The Impact of the New GICS Framework", 8 pp.
    [PRACTITIONER] [skimmed; one passage read]. 2018 effective date 2018-09-28.
11. FTSE Russell, Russell 1000 ICB Capped index materials; ICB migration from RGS completed
    September 2020. [PRIMARY DATA DOC] [**snippet only**].

**Peer-reviewed:**
12. Stevens, "Do Changes in Industry Classification Systems Matter? Evidence from REITs",
    *J. Real Estate Research* 44(3), 2022. [PEER-REVIEWED] [**abstract only** — tandfonline 403].
13. Tang, Xie & Xu, "Real estate as a new equity market sector: Market responses and return
    comovement", *Real Estate Economics*, 2020. [PEER-REVIEWED] [**abstract read in full** via
    Crossref; body 403].
14. Fuller, Yamani & Yu, "The impact of the new real estate sector on REITs: an event study",
    *J. Economics and Finance*, 2018. [PEER-REVIEWED] [**abstract read in full**].
15. Bao, Brady & Wang, "Pricing Efficiency and Bounded Rationality... GICS Real Estate
    Category Creation", *International Real Estate Review* 23(1), 2020, 37–63.
    [PEER-REVIEWED] [**abstract only**].
16. Bhojraj, Lee & Oler, "What's My Line? A Comparison of Industry Classification Schemes for
    Capital Market Research", *J. Accounting Research* 41(5), 2003, 745–774. [PEER-REVIEWED]
    [**abstract read in full** via Crossref].
17. "GICS and the Real Estate Reclassification Revolution", *J. Real Estate Portfolio
    Management* 27(2), 2021. [PEER-REVIEWED] [**title only** — 403, never read].

**Unverified / summariser-only — recorded, not relied on:**
18. The 2018 scale figures (23 companies, $2.7 trn, 10% of S&P 500 market cap, 100%/22%/21%
    of telecom/ConsDisc/tech) — **[UNVERIFIED]**, search-summariser only.
19. "$2 trillion moved across sector boundaries overnight, forcing institutional managers to
    rebalance immediately" — **[UNVERIFIED]**, search-summariser prose with no source
    document. This is exactly the kind of sentence that makes this lane look tradeable; I
    could not attach it to any document and I do not believe the word "immediately" survives
    §3.
20. GICS↔SIC/NAICS/Fama-French agreement percentages — **[UNVERIFIED]**, truncated in the
    summariser, never read in the paper.
21. "12 updates to the classification system since inception" — **[UNVERIFIED]** as to the
    exact count; the 10→11 sector figure *is* established from source 3.

### Blocks, logged by TOOL and RESPONSE (never by host)

| tool | target | response |
|---|---|---|
| `curl` (UA `backtest-framework-research/1.0`) | `spglobal.com/spdji/.../methodology-gics.pdf` | **HTTP 403**, 2,011-byte HTML page titled "Error \| S&P" |
| `curl` (UA `Mozilla/5.0 …backtest-framework-research…`) | same path, `methodology-sp-us-indices.pdf` | **HTTP 403**, same error page. Workaround: `spice-indices.com` mirror → 200 (older vintage) |
| `curl` | `spice-indices.com/.../1451156_gicsstructurechangedoc31march2022.pdf` | **HTTP 404**, HTML |
| `curl` | `msci.com/documents/10199/bbdd3ff9-…` (2018 Comm Svcs research insight) | **302 → redirect loop, curl error 47, max 50 redirects** |
| `curl` | `stooq.com/q/d/l/?s=nvda.us` | **HTTP 200 carrying a JavaScript proof-of-work challenge**, no CSV. An HTTP 200 that is not the data. Switched to Yahoo chart API |
| `curl` | `sectorspdrs.com/sectorspdr/sector/xlf/holdings` | **HTTP 200 but final URL `ssga.com/uk/en_gb`** — served a different page than requested. Used SSGA's xlsx endpoint instead |
| `WebFetch` | `tandfonline.com/doi/abs/10.1080/08965803.2022.2026582` | **HTTP 403** |
| `WebFetch` | `onlinelibrary.wiley.com/doi/10.1111/1540-6229.12314` | **HTTP 403** |
| `WebFetch` | `link.springer.com/article/10.1007/s12197-018-9436-z` | **HTTP 303** to `idp.springer.com/authorize`. Workaround: `curl` → 200, abstract extracted |
| `curl` | `papers.ssrn.com/sol3/papers.cfm?abstract_id=356840` | **HTTP 403**, Cloudflare challenge page |
| `curl` | `api.vanguard.com/rs/ire/01/ind/fund/0958/profile.jsonp` | **200**, Vanguard web-server error page, not JSON |
| `urllib` (4 threads, unpaced) | `sec.gov/Archives/.../primary_doc.xml` × 352 | **286 silent failures.** SEC throttles bursts. Fixed with a 0.17 s global pacer |

**No page instructed me to do anything.** I found no text addressed to the reader/agent in
any document fetched, and nothing presenting itself as an instruction. Every document was
treated as data.

---

## 9. What I could not verify, stated plainly

1. **The 2018 Communication Services event is not measured here.** My N-PORT series begins
   2019-09-30, so the largest GICS change by market cap in history is outside my measurement
   window entirely. I found no academic event study of it. Everything I have on its scale is
   summariser-only and tagged [UNVERIFIED]. If anyone wants to revive this lane, 2018 is the
   one event that could in principle carry a real flow effect, and I have *not* ruled it out —
   I have only failed to find evidence about it. The N-Q filings on EDGAR (21 of them) are the
   route to measuring it free, and I did not parse them.
2. **Event dates are pinned only to ±1 quarter.** N-PORT gives quarter-end snapshots. I know
   *that* Leidos, Teledyne and Roper moved sector in a given quarter; I did not establish the
   exact effective date of any of the three from an S&P DJI announcement, because
   `spglobal.com` 403'd every document request. Any study would have to pin these from
   provider announcements first.
3. **The flow figures are the SPDR family plus Vanguard only.** I did not measure Fidelity's
   MSCI sector ETFs, Invesco's equal-weight S&P 500 sector suite, State Street's SPDR
   industry (Select Industry) funds, the new "Premium Income" covered-call sector SPDRs that
   appear in the EDGAR series list from 2025, or any institutional separate-account sector
   mandate. My multiplier on the measured SPDR numbers is therefore a **lower bound on total
   GICS-mandated AUM** — though §3's staggering argument means the flow *on any one date* is
   closer to one family's worth than to the sum, which cuts the other way. I did not resolve
   this tension quantitatively.
4. **I did not measure spreads on these names.** I assert only that mega-cap spreads are
   structurally tighter than the programme's 33.8 bp/side measured on its held names. I have
   no OHLC fixture and computed **no Corwin-Schultz estimate**. The claim "cost is favourable
   here" is directional, not quantified.
5. **Select Sector capping is not incorporated into the flow arithmetic.** The Select Sector
   indices apply 23%/4.8%-50% caps (from an *older vintage* of the methodology — the current
   document is 403 to me). My buy-leg estimates use uncapped float weights and so are
   **approximate for the largest names**, precisely the ones — Visa, Mastercard — whose numbers
   matter most. The direction of the error is that capping would *reduce* the buy leg, making
   the net flow smaller, so this does not threaten the conclusion; but the figures in §2.4
   are not exact.
6. **The academic sign conflict is unresolved**, and so is Bao et al.'s "largest for large-cap"
   versus Stevens' "medium cap". I read four abstracts and zero full papers on the 2016 event —
   every publisher blocked the body. The "volume not discernibly impacted" finding that I
   weight most heavily against this lane is therefore **[abstract only]** and I have not seen
   the test behind it.
7. **I did not establish a GICS↔SIC error rate.** The specific agreement percentages are
   unverified (§6, §8 item 20). So the statement "a free SIC proxy is unfit for dating these
   events" rests on Bhojraj et al.'s *general* finding plus the structural argument that
   mis-dating destroys the measurement, not on a measured misclassification rate.
8. **Non-S&P-500 sector reclassifications are entirely unmeasured.** My method sees only the
   S&P 500. The fixture spans 1,573 names. Mid- and small-cap names change GICS sector too,
   and there are S&P MidCap 400 / SmallCap 600 capped sector indices and MSCI IMI sector funds
   that hold them — but at far smaller AUM. I assert the flow there is proportionally smaller;
   **I did not measure it**, and it is the one place where the event count could be materially
   higher than 0.44/year.
9. **I did not verify that the 2026 consultation will not produce cross-sector moves.** I read
   its summary and the topic list, which are sub-industry/industry level, and concluded the
   2027 pipeline looks thin for *sector* migrations. The "Classification of Listed Investment
   Companies" topic is the one I cannot dismiss — I did not read pp 20–22. Closed-end funds and
   BDCs are ineligible for S&P US indices, which is why I de-weighted it, but that is inference.
10. **Whether the published effects are ex-post or contaminated, I did not assess.** I never
    read a methods section. For a lane I am recommending against on count alone, I judged that
    the wrong place to spend effort — but it means the programme's "published effect is ex-post
    or contaminated" killer is **untested** here rather than cleared.
