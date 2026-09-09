# J1 — Stock splits: the ANNOUNCEMENT date and the EX-DATE, treated separately

External-evidence brief. Round 5. Written 2026-09-10.
**I have no access to the programme's data and claim nothing about it.** Every number below is
either from a cited external source — tagged by TYPE and by HOW WELL I ESTABLISHED IT, with the
establishment tag in the same sentence as the number — or from a measurement I made myself against
a free public endpoint, in which case the script, the raw call and the **negative control** are
named in §9 so it can be re-run.

The announcement date and the ex-date are reported **separately throughout**. They have different
literatures, different mechanisms, different decay profiles and different data problems, and
pooling them is the main way this territory has been mis-sold.

---

## 0. WHERE THE EFFECT LIVES — the commissioning premise is CORRECT, and it is the only thing in this lane that survived

**Killer 1 is genuinely off the table.** A forward stock split cannot occur in a cheap stock, the
post-split price does not come near the $5 floor, and the names are the most liquid in the
universe. I could not find a single counterexample. The 2024 US cohort, by post-split price:
NVDA $1,200→$120, CMG ~$3,000→$60, AVGO ~$1,750→$175, TSCO ~$2,700→$54, SMCI ~$600→$60,
ANET ~$400→$100, PANW ~$380→$190, WMT ~$165→$55 [PRACTITIONER / my own ratio arithmetic on names I
read off a split feed, §9.2] [read in full]. Even the small end of the population — the regional
bank holding companies that account for much of the modern count (Middlefield Banc, Landmark
Bancorp, Commerce Bancshares, First of Long Island, Pathfinder Bancorp) — splits 1.5-for-1 or
1.05-for-1 from the $20–$30 range, landing at $13–$28, still multiples of the floor. The published
anchor agrees: Lipson's NYSE sample had a **mean pre-split price of $68.50, "about twice" the
market average** [WORKING PAPER] [read in full].

So `50/P` at these prices is **0.04–0.9 bp**, against the programme's measured **33.8 bp/side** on
names actually held. **This lane would trade at roughly one-tenth to one-thirtieth the cost the
book currently pays.** That is real and it is the reason the lane deserved commissioning.

**The lane dies anyway, on killers 2, 3 and 4 — and on a fifth the commissioning note did not
list.** Taking them in the order that matters:

| | finding | where |
|---|---|---|
| **COUNT (killer 2)** | Forward splits on US exchange-listed operating companies run **roughly 40–70 distinct 8-K filers/yr post-2010**, of which the genuinely large/liquid subset is **~10–25/yr**. My own EDGAR census: **104 (2010) → 46 (2019) → 63 (2024) → 49 (2025)**. An independent read of an NYSE-only academic sample: **5 splits in 2009**. | §1, §6 |
| **DECAY (killer 3)** | The 3-day announcement bump survives (~+1.6%); the **post-announcement drift flips sign** — CAAR(0,+30) goes **+0.93%\*\*\* (2004–07) → −2.46%, insignificant (2008–11)**. The **ex-date effect is gone after decimalization** — significant in the 1/8th regime, **not** in the decimal regime. | §2, §3 |
| **ONE PRINT (killer 4)** | The announcement return is concentrated in days −1 to +1 and is ~85% of the whole-window CAAR. Post-2008 the (0,+30) residual is *negative*. | §2 |
| **CONTAMINATION (killer 5)** | **36–68% of modern split announcements arrive inside an EARNINGS 8-K (Item 2.02)** — measured by me on EDGAR. NVIDIA's 10-for-1 was a bullet point beside *"Record quarterly revenue … up 262%"*. Splitters are also high-momentum growth names by construction. **Earnings/PEAD and momentum are both on the exclusion list.** | §1.3, §2.4 |
| **WRONG SIGN ON COST** | A split makes the name **relatively more expensive and ~30% more volatile, permanently.** Proportional spreads rise, percentage depth falls >30%, return SD rises ~30% and does not revert. | §4 |

**Recommendation: do not open this as a signal lane.** The honest residual is in §8.

---

## 1. THE COUNT — kill number (a), measured myself with controls

### 1.1 What I measured, and what it is not

There is no free, dead-inclusive, point-in-time feed of US forward splits that I could verify. So I
built the count from **SEC EDGAR full-text search** (`efts.sec.gov/LATEST/search-index`), counting
**distinct CIKs that filed an 8-K containing a forward-split ratio phrase** in each year.

**This is a LOWER BOUND and I want that stated before the numbers.** An 8-K is *not* mandatory for
a stock split — Item 8.01 is the voluntary "Other Events" item — so a company that announces by
press release alone is invisible here; and foreign private issuers file 6-K, not 8-K (Shopify's
2022 10-for-1 does not appear). Against that, it is an *over*count of tradeable events in one
respect: it includes cosmetic 1.05-for-1 stock dividends and OTC shells.

**Controls, all passed before any count below was used** (§9.1):

| control | required | observed |
|---|---|---|
| nonsense phrase, 2015 | 0 | **0** |
| future window, 2035 | 0 | **0** |
| pre-coverage years 1996/1998/1999/2000 | 0 | **0, 0, 0, 0** |
| date additivity: H1 + H2 = full year 2015 | equal | **55 + 49 = 104 = 104** |
| half-year document-id overlap | 0 | **0** |
| `from=` pagination: overlap of `from=0` and `from=10` on a 100-row page | 90 | **90** |
| `from=` beyond total | 0 rows | **0 rows** |
| exact-phrase: scrambled word order | 0 | **0** |
| two-phrase AND: `X AND superset(X)` | equal | **41 = 41** |
| two-phrase AND: `X AND nonsense` | 0 | **0** |
| POSITIVE control: NVIDIA's 2024-05-22 8-K found by the corrected phrase set | ≥1 | **3 documents** |

### 1.2 The series

Distinct 8-K filers per year mentioning a forward-split ratio phrase (EDGAR FTS; **my own
measurement** [PRIMARY DATA DOC] [read in full]):

| year | distinct filers | distinct 8-Ks | "reverse stock split" 8-K mentions | fwd:rev |
|---|---|---|---|---|
| 2001 | 224 | 288 | 1,136 | 1 : 4 |
| 2004 | 453 | 996 | 1,810 | 1 : 2 |
| **2005 (peak)** | **506** | 1,114 | 3,481 | 1 : 3 |
| 2007 | 335 | 670 | 3,367 | 1 : 5 |
| 2009 | 132 | 183 | 2,937 | 1 : 16 |
| **2010** | **104** | 207 | 3,026 | 1 : 15 |
| 2012 | 119 | 242 | 2,756 | 1 : 11 |
| 2014 | 138 | 269 | 2,994 | 1 : 11 |
| 2016 | 89 | 162 | 3,470 | 1 : 21 |
| 2018 | 64 | 158 | 3,120 | 1 : 20 |
| **2019 (trough)** | **46** | 109 | 3,681 | 1 : 34 |
| 2020 | 59 | 122 | 4,056 | 1 : 33 |
| 2021 | 70 | 148 | 4,445 | 1 : 30 |
| 2022 | 62 | 121 | 4,665 | 1 : 39 |
| 2023 | 55 | 100 | 5,886 | **1 : 59** |
| 2024 | 63 | 115 | 5,892 | 1 : 51 |
| 2025 | 49 | 98 | 5,821 | 1 : 59 |
| 2026 → 08-26 | 33 | 54 | 3,829 | 1 : 71 |

**From 506 filers in 2005 to 46 in 2019 — an 11× collapse — and no recovery to even a quarter of
the 2005 level in the 2024 "comeback".** Meanwhile reverse-split mentions rose from 3,026 to 5,892.
**The ratio moved from about 1:3 to about 1:59.**

My phrase set initially **missed NVIDIA, Broadcom and Supermicro** because they wrote
"ten-for-one ***forward*** stock split" — the inserted word defeats an exact-phrase query. Adding
`"forward stock split"` raises the union to roughly 280/yr in 2010, but that phrase is dominated by
OTC shells doing float engineering ahead of reverse mergers, so **the union is an upper bound on
8-K-filing forward splitters and the ratio-phrase series is the better proxy for operating
companies.** Closing the gap properly would add a handful of genuine large caps per year (three in
2024), not an order of magnitude. See §9.1 for the measured union series.

### 1.3 How many are actually tradeable — the object, inspected

A count of filers is not a count of tradeable events. I pulled the **named** forward splits from a
split feed and looked at them (§9.2). In each Q4 sampling window the population decomposes into:

- **Genuine large/mid-cap US operating companies** — 2021: ANET, MCHP, ISRG, RJF, PLUS. 2024: TSCO,
  PANW, ETR, ANET, CRVL, PATK. 2025: TPL, NOW. 2026: APH, IESC, RUSHA/RUSHB. **Two to five per
  Q4 window**, which annualises to roughly **10–25/yr**.
- **Recurring cosmetic stock dividends.** **Commerce Bancshares (CBSH) and Landmark Bancorp (LARK)
  appear with a 1.05-for-1 "split" in EVERY SINGLE YEAR 2019–2024 of my samples.** A naive feed
  screen treats these as annual split events. They are 5% stock dividends.
- **Small regional banks at 1.5-for-1** — HBNC, PBHC, FLIC, MBCN, CARO, FSFG, SSBI. High enough
  priced to clear $5, far too thin to clear a dollar-volume screen.
- **Dual share classes double-counting one event** — MKC/MKC.V, BEP/BEPC, RUSHA/RUSHB, ABV/ABEV,
  GOOG/GOOGL. One decision, two rows. Breadth-destroying.
- **Foreign ADRs** — ABEV, IBN, INFY, FMS, BSAC, SHG, WIT, SNN, DQ, VIPS.
- **Reorganisation artefacts that are not splits at all** — **QRVO "500 for 1", MBC "1,280 for 1",
  WETH "2,800 for 1", BRIA "1,000 for 1", TSLX "66.68 for 1"**. These are recapitalisations and
  holding-company formations. Any screen that takes a split feed's ratio at face value will ingest
  them, and at those ratios a sign error is catastrophic.

**So the ~40–70 filers/yr is not the usable count.** The usable count — exchange-listed, US
operating company, ratio ≥1.5, one row per economic event, liquid enough for a dollar-volume screen
— is **of order 10–25 per year, i.e. ~170–420 events across 2010-01-04 to 2026-08-26.** With the
programme's **~10 effective independent instruments** and heavy time-clustering (the events cluster
in bull markets — 2021 and 2024 are spikes, 2022–23 near-zero), `n_eff` is far below the raw count.

### 1.4 Independent corroboration of the magnitude

- **NYSE-listed splits by declaration date, 2004–2011: 416 total, high of 105 in 2005, LOW OF 5 IN
  2009; 336 in 2004–07 vs 80 in 2008–11; 2-for-1 was 90% then 71% of the total** — from Table 1/2
  of a *Journal of Finance and Accountancy* paper [PEER-REVIEWED, low-tier venue] [read in full,
  extracted locally with `pypdf` and read off the table].
- **Frequency of splitting firms peaked at 23% in 1982 and fell continuously to under 1% by 2009** —
  CFA Institute digest of "Why Are Stock Splits Declining?" [PRACTITIONER summary of a
  [PEER-REVIEWED] paper] [read in full, but **it is a digest, i.e. a summariser, and it did not name
  the underlying paper**; search results attribute it to Minnick & Raman, *Financial Management*
  2014, which I did **not** open].
- **~15% of Russell 1000 firms split each year in the late 1990s, ~5% by the mid-2000s, and splits
  "practically ceased" after 2008–09** [UNVERIFIED] [snippet only — this came back in a search
  summary and I did not open the source; treat as directional only].
- **Wall Street Horizon**, Q2 2024 = 100 split announcements across a universe of 11,000 **global**
  equities; H1 2024 = 168; **July 2024 = 30 announcements, of which 18 reverse and 10 traditional**
  [PRACTITIONER] [read in full]. Note the universe is global and 11k names; the forward share is a
  minority even in the "comeback" year. A separate snippet gives "76 forward stock splits in 2024"
  and "37 traditional forward splits in H1 2026" [UNVERIFIED] [snippet only].
- **Desai & Jain (1997) had 5,596 forward splits and 76 reverse splits over 1976–1991** [PEER-REVIEWED]
  [snippet only]. **That ratio was ~74:1 forward-to-reverse. My 2024 measurement is ~1:51 the other
  way.** The composition of US split activity has inverted completely.

**Verdict on (a): the lane dies on arithmetic before effect size is reached.** It is not that the
count is zero — it is that the count of *liquid, clean, one-per-event* forward splits is low double
digits per year, concentrated in bull-market clusters, inside a book with ~10 effective instruments.

---

## 2. THE SPLIT ANNOUNCEMENT EFFECT — and the decay, which matters more

### 2.1 The canonical results, in order

| source | sample | finding | tags |
|---|---|---|---|
| Fama, Fisher, Jensen & Roll 1969 | 1927–1959 | **no** abnormal return after the split | [PEER-REVIEWED] [snippet only] |
| Grinblatt, Masulis & Titman 1984, *JFE* | — | announcement effect positive; **ex-day +0.69%** and positive on the two following days | [PEER-REVIEWED] [snippet only] |
| Brennan & Copeland 1988, *JFE* 22:83–101 | large | splits are a **costly** signal *because* they raise investors' transaction costs; the model explains a substantial fraction of announcement returns | [PEER-REVIEWED] [snippet only] |
| Ikenberry, Rankine & Stice 1996, *JFQA* | 1,275 2-for-1 splits | announcement return **+3.38%**; **+7.93%** yr 1, **+12.15%** yrs 1–3 | [PEER-REVIEWED] [snippet only] |
| Desai & Jain 1997 | 5,596 splits 1976–91 | announcement-**month** abnormal return **+7.11%**; effect not fully in price within a month | [PEER-REVIEWED] [snippet only, via a quotation inside a paper I did read in full] |
| **Ikenberry & Ramnath 2000/2002** | **3,028 splits, 1988–1997** | **1-yr match-adjusted +9.00% (t=7.93)**, median **+6.31%** | [WORKING PAPER] [**read in full**] |
| **Byun & Rozeff 2003, *J. Finance* 58(3)** | **12,747 splits, 1927–1996** | for splits ≥25%, **neither** reference-portfolio-with-bootstrap **nor** calendar-time factor methods find performance significantly different from zero; evidence against efficiency "neither pervasive nor compelling" | [PEER-REVIEWED] [abstract only] |
| **Boehme & Danielsen 2007, *Financial Review*** | **1950–2000** | **no** positive long-term post-split returns; the post-announcement drift is **short** and **does not persist past the actual split date**; it is attributable to **trading frictions / price delay**, not behavioural underreaction | [PEER-REVIEWED] [abstract only] |
| Kalay & Kronlund 2014 | — | the announcement return is **earnings information after all** | [WORKING PAPER] [abstract only — SSRN returned HTTP 403 to WebFetch, §7] |

### 2.2 Where the 1990s effect lived — it is momentum and small caps

I read Ikenberry & Ramnath in full specifically to get the conditional splits, because a headline
`+9.00%` tells you nothing about tradeability:

- **By NYSE market-cap quintile:** significant in the **smaller three** quintiles; the **largest
  quintile** — the only part of the population this programme could trade cheaply — is
  **+4.42% (t=2.25) over a FULL YEAR**. That is ~1.8 bp/bar, at `t=2.25`, from a match-adjusted
  long-horizon benchmark, in 1988–1997.
- **By split factor:** **2-for-1 splits — the single most prevalent factor, and 71–90% of the
  modern population — show the LOWEST drift, +6.75% (t=3.94)**, against +13.74% (t=2.66) for
  factors above 2-for-1.
- **By momentum:** *"roughly two-thirds of the sample is classified in the highest growth
  quintile"*, and drift is **highest in momentum quintiles 4 and 5** (+10.28%, +10.12%). Splitters
  are high-momentum growth names by construction.

So even in the paper that most strongly supports the anomaly, **the tradeable slice is the weakest
slice**, it is a one-year horizon not an overnight one, and it sits on top of momentum — which is
on the exclusion list.

### 2.3 THE DECAY — the number that decides it

From Table 3 of the *Journal of Finance and Accountancy* paper, **NYSE-listed splits by declaration
date**, market-model CAARs, **read directly off the table after extracting the PDF locally**
[PEER-REVIEWED, low-tier venue] [read in full]:

| window, days rel. to announcement | 2004–2007, N=336 | 2008–2011, N=80 |
|---|---|---|
| (−30, +30) | **+2.09%\*\*\*** | **−3.28%** (not significant) |
| (−30, −2) | +1.02%\*\*\* | −0.88% (ns) |
| (−30, 0) | +1.99%\*\*\* | +0.16% (ns) |
| (−2, +2) | **+1.91%\*\*\*** | **+1.51%\*\*\*** |
| **(−1, +1)** | **+1.86%\*\*\*** | **+1.58%\*\*\*** |
| **(0, +30)** | **+0.93%\*\*\*** | **−2.46%** (not significant) |

**This single table contains killers 3 and 4 together.**

1. **The effect resolves in one print.** CAAR(−1,+1) is +1.86% while CAAR(−30,+30) is +2.09% —
   **89% of the whole two-month window lands in three days around the announcement**, and day −1 is
   inside it. A daily-bar book cannot be long before a split announcement it cannot predict.
2. **What is left after you can legally act is gone, and then negative.** The (0,+30) residual —
   the only part available to a strategy that learns of the split from the tape — falls from
   **+0.93%\*\*\* to −2.46% and loses significance**. The sample is small (N=80) and the
   insignificance cuts both ways, but the point estimate has the **wrong sign** and this is the
   modern half of the sample.

This is consistent with Boehme & Danielsen, who find the drift short-lived and attribute it to
**price delay / market friction** — i.e. the drift is largest in names that are slow to incorporate
information, which is a restatement of *illiquid and small*. It is also consistent with Byun &
Rozeff finding nothing over 1927–1996 once calendar-time methods are used.

**I could not find a post-2015 US academic event study of split announcement CARs.** The recent
split literature has moved to China (Cui, Li, Pang & Xie, *Financial Management* — **China sample,
not US** [PEER-REVIEWED] [abstract only]) or to mechanisms on the exclusion list (short interest;
the option market). **Treat the absence of a modern US replication as a negative, not as an
opening** — this is a heavily published effect with a 55-year literature; the lack of a 2015–2026
US CAR paper is more consistent with nothing left to publish than with an unexamined opportunity.

### 2.4 The contamination I did not expect to find, and it is the strongest single result in this brief

**36–68% of modern forward-split announcements arrive inside an EARNINGS 8-K.** I measured the 8-K
item codes on the **first** filing per company per year that mentions a forward-split ratio — which
approximates the announcing filing — and deduplicated per accession (an earlier per-document count
over-weighted filings with several matching exhibits, and I discarded it):

| year | companies | 1st filing has Item **8.01** | Item **7.01** | **Item 2.02 (EARNINGS)** |
|---|---|---|---|---|
| 2010 | 94 | 53% | 15% | **22%** |
| 2014 | 114 | 45% | 25% | **43%** |
| 2019 | 37 | 35% | 22% | **46%** |
| 2021 | 60 | 52% | 28% | **40%** |
| 2024 | 42 | 48% | 33% | **36%** |
| **2025** | 34 | 32% | 35% | **68%** |
| 2026→Aug | 28 | 57% | 21% | **54%** |

And the canonical case, which I read from the filing itself rather than inferring. NVIDIA's
2024-05-22 8-K, **Item 2.02 + 8.01 + 9.01**, press release `q1fy25pr.htm`, bullet list:

> *"Record quarterly revenue of $26.0 billion, up 18% from Q4 and up 262% from a year ago · Record
> quarterly Data Center revenue of $22.6 billion, up 23% from Q4 and up 427% from a year ago ·
> Ten-for-one forward stock split effective June 7, 2024 · Quarterly cash dividend raised 150%"*

**The split was the third bullet of a blowout earnings release that also raised the dividend 150%.**
Alphabet's 20-for-1 (8-K 2022-02-01, Items 2.02 + 8.01 + 9.01), Apple's 4-for-1 (2020-07-30, Items
2.02 + 9.01) and Stifel's (2024-01-24, Items 2.02 + 9.01) are the same shape.

**Consequence: for roughly two in five modern events — two in three in 2025 — the "split
announcement return" IS an earnings announcement return plus, frequently, a dividend action.**
Earnings announcement dates, PEAD and the announcement premium are on the **exclusion list**; so
are corporate supply events and dividend policy is J2's lane. The clean-split subsample is the
~30–50% announced by a standalone Item 8.01 or 7.01 filing, which takes the usable count from
§1.3's 10–25/yr down to **single digits per year**.

This also explains Kalay & Kronlund's title. The announcement effect being "earnings information
after all" is not a subtle econometric claim — **a third to two-thirds of the time the split is
physically inside the earnings release.**

---

## 3. THE EX-DATE — separately, and it is the cleaner kill

### 3.1 What was documented

- **Grinblatt, Masulis & Titman 1984:** ex-day mean return **+0.69%**, with significantly positive
  abnormal returns on the **two following days**; the proposed mechanism is an order-flow shift —
  sell orders dominate before the split, buy orders after [PEER-REVIEWED] [snippet only].
- **Nayar & Rozeff 2001, *JFQA* 36(1):119–139:** negative abnormal returns of **about −1% near the
  RECORD date**, attributed to the trading inconvenience of buying unsplit shares (due-bill
  delivery and settlement frictions); the positive ex-date return arises **in part mechanically**,
  from the artificially depressed price of unsplit shares that the record-date effect created
  [PEER-REVIEWED] [abstract and snippets only — **both free PDF routes returned HTTP 200 with HTML
  rather than a PDF**, §7].
- **Ohlson & Penman 1985, *JFE*:** return standard deviation rises ~**30%** after the ex-date, in
  daily and weekly data, and **is not temporary** [PEER-REVIEWED] [snippet only].

### 3.2 The mechanism was a spread, and the spread is gone

**Kadapakkam, Krishnamurthy & Tse 2005, *JFQA* 40(4):873–895** — "Stock Splits, Broker Promotion,
and Decimalization": **significant positive abnormal returns around the ex-date in the 1/8th
pricing period, but NOT in the decimal pricing period** [PEER-REVIEWED] [abstract and snippet only
— I did not obtain the full text].

The mechanism they identify is the reason this matters more than a bare "it faded":

> the post-split **increase in the relative spread** is what paid brokers to promote the splitting
> stock to small investors. Decimalization cut the spread, removed the promotion economics, and the
> ex-date return went with it.

**Every link in that chain is more dead in 2026 than it was in 2005.** Retail commissions are zero,
the promoting full-service retail broker barely exists as a channel for this, the tick is a cent,
and the mega-caps that now do the splitting trade at 1–3 bp spreads where there is no promotion
rent to capture at all. *(I initially wrote that the SEC's half-cent tier was already in force and
that is **wrong**: the Rule 612 amendments creating a $0.005 increment for tick-constrained NMS
stocks had a compliance date of 2025-11-03 which has been **postponed to November 2026**
[PRACTITIONER law-firm alerts + a postponement noted in recent registrant filings] [snippet only] —
i.e. it is **not** in force as of this brief's date and does not bear on the argument either way.)*
**The ex-date leg has a mechanism that has been explicitly tested out of existence in a regime
change that happened 25 years before the programme's window opens.** The programme's window starts
2010-01-04 — **entirely inside the decimal regime in which the effect was measured absent.**

### 3.3 The other proposed ex-date mechanisms, and why none of them helps

- **Retail demand at a lower nominal price.** This is the "nominal price illusion" / catering
  literature: average NYSE nominal prices have sat near ~$35 since the Depression while the price
  level rose more than tenfold, and firms manage nominal price to cater to time-varying investor
  preferences (Weld, Michaely, Thaler & Benartzi, *JEP* 2009; Baker, Greenwood & Wurgler; Birru &
  Wang, *JFE*) [PEER-REVIEWED] [snippet only]. **This is a theory of why firms split, not a
  tradeable ex-date return**, and the authors of the survey conclude **no existing theory explains
  the constancy** — they fall back on custom and norms. Nothing here is a signal.
- **Index or fund mechanics.** The one real mechanical channel is the **price-weighted** DJIA, where
  a split changes the divisor and the name's index weight (Apple's 2020 4-for-1 is the textbook
  case). **But index reconstitution and forced index flows are on the exclusion list**, the channel
  touches only the ~30 DJIA names, and it is a one-off divisor change, not a repeatable event.
- **Tick-size and relative-spread effects.** Real, measured, and they point the **wrong way** for a
  buyer — see §4.
- **Liquidity changes.** Contested, and the favourable reading is confined to the
  announcement-to-ex window — see §4.

**Verdict on the ex-date: this is the cleanest kill in the brief.** The effect existed, the
mechanism was identified, and the mechanism was tested and found absent in exactly the pricing
regime the programme trades in.

---

## 4. WHAT A SPLIT DOES TO LIQUIDITY AND SPREAD — it gets relatively WORSE, not better

This bears directly on the commissioning question *"does a high-priced name stay cheap to trade
after it halves?"* **The documented answer is: in dollars yes, in basis points no.**

**Lipson, "Stock Splits, Liquidity and Limit Orders"** (Darden working paper; non-public NYSE system
order data; 2-for-1-and-greater NYSE splits, 1995–1996; mean pre-split price $68.50)
[WORKING PAPER] [**read in full**]:

| measure | change after the split |
|---|---|
| **dollar** quoted and effective half-spreads | **decrease** |
| **proportional** quoted and effective half-spreads | **INCREASE** (explicitly "as in Conroy, Harris and Benet (1990)") |
| cumulative depth within $1/8 **split-adjusted** | **−2,600 shares bid, −3,500 shares ask — over 30% below pre-split levels** |
| average limit-order placement distance from mid-quote | **33 bp before → 60 bp after**, with **no significant change in execution rates** |
| market-order execution cost | **increases** |
| limit-order execution cost | decreases |
| all executed orders | mean change **indistinguishable from zero**, median **−5 bp** |
| daily **share** volume | **−9%** |
| daily **dollar** volume | no significant change |

- **Conroy, Harris & Benet 1990, *J. Finance* 45(4):1285–95:** percentage spreads **increase**
  significantly after splits for 133 NYSE firms; the increase is tied to the price decline and
  explains part of the post-split variance increase [PEER-REVIEWED] [snippet only].
- **Ohlson & Penman 1985** and, with a modern causal design, **Shue & Townsend, "Can the Market
  Multiply and Divide? Non-Proportional Thinking in Financial Markets"** (CRSP, NYSE/AMEX/NASDAQ
  share codes 10–11, difference-in-differences around 2-for-1 splits) [WORKING PAPER version of a
  [PEER-REVIEWED] paper] [**read in full, the split sections**]: *"total return volatility,
  idiosyncratic volatility, and market beta increase by approximately 30 percent immediately after
  a 2-for-1 split"*, and **"the volatility does not return to pre-split levels, even after six
  months."** Their identification only requires that firm fundamentals do not change on the
  execution date, which is exactly the right assumption for a pre-announced event.
- **Brennan & Copeland 1988** make this the *point*: the split works as a signal **because** it is
  costly, and it is costly because it raises investor transaction costs [PEER-REVIEWED] [snippet only].

**The counterweight, stated fairly.** **Lin, Singh & Yu 2009, *JFE* 93(3):474–489:** the incidence
of **non-trading** falls and **liquidity risk** falls after splits, implying lower latent trading
costs and a lower cost of equity; announcement returns correlate with liquidity improvements; and
**less liquid firms benefit more** [PEER-REVIEWED] [snippet only]. And a *Journal of Economics and
Finance* (2013) paper reports that the liquidity improvement is **short-term, observed only between
the announcement date and the ex-date, with liquidity declining in the long run** [PEER-REVIEWED]
[snippet only].

**Reconciliation, and it is unfavourable.** The favourable liquidity result is about *non-trading
incidence* and *liquidity risk* and it is **strongest in the less liquid firms** — i.e. it does not
apply to the high-priced mega-caps that are this lane's only tradeable subset. The unfavourable
result — proportional spread up, percentage depth down >30%, volatility up ~30% permanently — is
measured on exactly the NYSE high-priced population the lane wants.

**Two honest qualifications in the programme's favour.** (i) The 33→60 bp numbers are from 1995–96
under a $1/8 tick; they do **not** transfer to a $200 stock in 2024. (ii) In absolute terms the
effect is immaterial at these prices: a 1-cent tick on NVDA at $1,200 is 0.083 bp and at $120 is
0.83 bp — both negligible against a 67.6 bp round trip. **So the spread story does not kill the
lane on cost. What it kills is the premise that the ex-date is a liquidity *improvement* you could
harvest, and it adds a ~30% permanent volatility bump at precisely the moment a post-ex-date
strategy would be long.** For an equal-weighted book with ~10 effective instruments, that is a
Sharpe headwind.

**Note what this means for the one robustly established modern fact in this territory: it is a
VOLATILITY fact, not a RETURN fact.** Shue & Townsend's ~30% is causally identified, modern, and
replicates Ohlson & Penman across 35 years. Nothing on the return side in this lane is that solid.

---

## 5. REVERSE SPLITS — briefly, and they are squarely in the killer zone

**FLAG, as instructed: reverse splits are the mirror image on price. They happen in cheap stocks
and therefore land in killer 1.** I did not spend the lane on them.

- **They are a delisting-compliance mechanic, not a corporate decision about trading range.** A
  Nasdaq issuer that trades below $1.00 for 30 consecutive business days gets a 180-day compliance
  period and typically cures it with a reverse split (Listing Rule 5810(c)(3)(A)). On **2024-10-07
  the SEC approved a Nasdaq rule change** tightening this, and Rule 5810(c)(3)(A)(iv) denies the
  180-day period to a company that has already done reverse splits totalling **250-for-1 or more
  over the prior two years** [PRIMARY DATA DOC / law-firm client alerts: Alston & Bird, Skadden,
  Hunton, Dechert] [read in full via search summaries of the alerts — **[snippet only]** for the
  rule text itself]. **A 250:1 cumulative-ratio threshold tells you the price level of this
  population.** These are sub-$1 names: `50/P` at $0.80 is **62 bp per side on commission alone.**
- **Returns are negative and large.** Desai & Jain 1997: **−10.76% at one year and −33.90% at three
  years** for reverse splits [PEER-REVIEWED] [snippet only]. Kim et al. 2008 report poor price and
  operating performance over three years post ex-date, with **−54% CAR over three years** vs matched
  controls [PEER-REVIEWED] [snippet only].
- **There is a short candidate here and the programme cannot take it.** A persistent −30% to −54%
  three-year drift in sub-$1 names is unshortable at retail: borrow is expensive or absent, and
  **short interest, days-to-cover, borrow fees and securities lending are all on the exclusion
  list**, as is the death process / distress anomaly, which is what this drift largely *is*.
- **The count has exploded while forward splits collapsed.** My EDGAR measurement: reverse-split
  8-K mentions **3,026 (2010) → 5,892 (2024)**, against forward-split filers falling 104 → 63.
  Desai & Jain's 1976–91 sample had **5,596 forward vs 76 reverse**. The composition has inverted by
  a factor of several thousand.

---

## 6. THE DATA QUESTION — and the warning the lane was told to issue

### 6.1 ⚠ WARNING, EXPLICITLY: AN EXISTING SPLIT FEED'S DATES ARE **EX**-DATES

**Every free and commercial corporate-action split feed I examined is keyed on the EX-DATE (or the
"effective"/"payable" date), NOT the announcement date.** The split feed I harvested labels its
column `Date` with no qualifier, and its values are ex-dates: NVIDIA appears at **2024-06-10**, its
ex-date, not 2024-05-22, its announcement. Apple appears at 2020-08-31, not 2020-07-30.

**If a split feed's date is mistaken for an announcement date, every announcement study in this
territory is run on a date 19 to 167 days late, and it will look like the effect does not exist —
or worse, it will land on a different, real event.** I measured the gap on 17 named splits whose
announcement dates I cross-checked (§9.3):

| | days from announcement to ex-date |
|---|---|
| minimum | **19** (NVDA, TPL) |
| median | **34** |
| mean | **67** |
| maximum | **167** (GOOGL 2022) |

**There is no fixed offset.** TPL and NVDA are 19 days; Alphabet is 167; Lam Research 135; Palo
Alto 119; Tesla's 2022 split 150. **You cannot recover an announcement date from an ex-date by
subtracting a constant**, and a ±1-month window around a guessed offset will straddle an earnings
date more often than not (§2.4).

### 6.2 What carries a usable announcement date, and how far back

**SEC EDGAR full-text search (`efts.sec.gov/LATEST/search-index`) is the answer, with caveats.**

**Coverage boundary, measured:** `"stock split"` in 8-K returns **0 for 1996, 1998, 1999 and 2000,
and 3,079 for 2001**. **EDGAR full-text search begins in 2001.** The programme's window opens
2010-01-04, so **coverage is complete for the window** — this is the one unambiguously good news
item in the data section. Anything pre-2001 needs a different route entirely.

**The endpoint is well-behaved and I verified it** (full control table in §1.1): exact-phrase
semantics, honoured and additive date parameters, honoured `from=` pagination at a 100-row page,
working two-phrase AND, and a passing positive control.

**There is NO single 8-K item code that identifies a split.** From §2.4, the announcing filing
carries **Item 8.01 in 32–57% of cases, Item 7.01 in 18–42%, and Item 2.02 in 22–68%** — and
**Item 5.03 (charter amendment) in only 2–14%**, so a charter-amendment screen misses most of the
population. **A screen on "8-K Item 8.01" alone finds roughly a third to a half of split
announcements.** The 8-K item-code map is itself on the exclusion list; this brief's contribution is
only that it does **not** solve the retrieval problem here.

**Phrase-based retrieval is BRITTLE, and I measured the failure.** My first phrase set —
`"two-for-one stock split"`, `"ten-for-one stock split"`, and 16 siblings — scored **3 exact hits
out of 16 named real splits**, with the rest either missed or returning a *later* filing that
merely references the completed split:

| ticker | phrase tried | reported annc | earliest 8-K found | why it failed |
|---|---|---|---|---|
| NVDA | `"ten-for-one stock split"` | 2024-05-22 | 2024-11-20 | wrote **"ten-for-one FORWARD stock split"** |
| AVGO | `"10-for-1 stock split"` | 2024-06-12 | not found | wording |
| SMCI | `"10-for-1 stock split"` | 2024-08-06 | not found | wording |
| WMT | `"three-for-one stock split"` | 2024-01-30 | not found | wrote "3-for-1" |
| GOOGL | `"20-for-1 stock split"` | 2022-02-01 | not found | wording; found by entity query |
| SHOP | `"10-for-1 stock split"` | 2022-04-11 | not found | **foreign private issuer — files 6-K, not 8-K** |
| LRCX, AAPL, TSLA | matching phrase | — | **exact** | — |

**The better route is a PER-COMPANY query, not a market-wide phrase query:**
`q="stock split"` + `entityName=<10-digit CIK>` + a 400-day window running back from the ex-date,
then take the earliest 8-K. **I scored it on 16 named splits and it is usable but MUST be
filtered:**

| outcome | n | cases |
|---|---|---|
| **exact match to the reported announcement date** | **8** | AAPL, TSLA, GOOGL, AMZN, NVDA, AVGO, LRCX, ODFL |
| **+1 day** — 8-K filed the morning after an after-hours release; effectively correct | **2** | CMG, WMT |
| +8 days — missed the release, landed on the shareholder-vote 8-K (Item 5.07) | 1 | DXCM |
| **grabbed an UNRELATED EARLIER 8-K** whose boilerplate merely says "stock split" | **4** | **SMCI −194d, ANET −198d, TPL −94d, PANW −264d** |
| not found — **foreign private issuer, files 6-K** | 1 | SHOP |

**So 10 of 16 land within a day, and 5 of 16 are wrong by 8 to 264 days.** The failure mode is
specific and fixable: *"stock split"* is anti-dilution boilerplate in equity-plan (Item 5.02) and
annual-meeting (Item 5.07) filings, so the earliest-match rule grabs those. **PANW's recovered date
is 264 days early — a full year's error that would silently place the event in the wrong regime.**
The obvious hardening — require a ratio phrase, or drop filings whose only items are 5.02/5.07, or
shorten the window — I did **not** test, so I quote no recall figure for the hardened version.

**Three traps in that route:**

1. **`company_tickers.json` is NOT dead-inclusive.** The SEC's ticker→CIK map contains **current**
   registrants only. I checked: `ENRNQ` and `LEHLQ` are absent. **A ticker→CIK map built from it
   will silently drop the dead names — 35.7% of this universe — and bias the sample to survivors.**
   A point-in-time CIK map must come from historical EDGAR company indices, not this file.
2. **An 8-K is voluntary for a split.** Item 8.01 is "Other Events". A company that announces by
   press release and files nothing leaves no EDGAR trace until the next 10-Q.
3. **Foreign private issuers file 6-K.** Any `forms=8-K` filter drops them.

**Other routes, assessed:**

- **Press releases / exchange notices.** Nasdaq's daily-list and corporate-action files are not
  archived in a free, point-in-time, dead-inclusive form that I could find. `api.nasdaq.com`'s
  splits calendar endpoint **failed to connect at all** (§7) and is forward-looking in any case.
- **A free split feed for ex-dates.** Usable for ex-dates and for *naming* events, with the
  caveats in §1.3 and §9.2. **It is not a source of announcement dates.**
- **Commercial feeds** (Wall Street Horizon and similar) do carry announcement dates. **Vendor
  material is never evidence for a return** and I treat their counts as practitioner data only.

---

## 7. BLOCKS AND DEFECTS, logged by TOOL AND RESPONSE

Per the programme's rule, by tool and response, never by host.

| tool | target | response | consequence |
|---|---|---|---|
| WebFetch | CNBC article on the 2024 split comeback | **HTTP 403 Forbidden** | count datum taken from search summary instead; tagged [snippet only] |
| WebFetch | SSRN abstract page (Kalay & Kronlund) | **HTTP 403 Forbidden** | Kalay & Kronlund is [abstract only] from search summaries |
| curl | Cambridge Core PDF path for Nayar & Rozeff | **HTTP 200, `content-type: text/html`, 821,724 bytes** — an HTML interstitial, not a PDF | Nayar & Rozeff is [abstract and snippets only] |
| curl | JSTOR `stable/pdf/2676200.pdf` | **HTTP 200, `content-type: text/html`, 3,038 bytes** | same |
| curl | `api.nasdaq.com/api/calendar/splits?date=…` | **HTTP 000, 0 bytes** — connection failed | no Nasdaq calendar route |
| curl | `stooq.com/q/d/l/?s=…` price CSV | **HTTP 200, 796 bytes, a JavaScript proof-of-work bot-verification page — IDENTICAL FOR A REAL TICKER AND A BOGUS ONE** | no price harvest; **I did not attempt to defeat the proof-of-work** |
| urllib (6 workers × 2 concurrent scripts) | `efts.sec.gov` | **HTTP 403 Forbidden**, sustained, across all queries | SEC fair-access limit hit; recovered on serial retry with escalating backoff; one test left untested (§8.1) |

### 7.1 TWO SILENT 200s THAT WOULD HAVE FABRICATED RESULTS, both caught by controls

**This is the part of the brief I would most want re-checked, because both of these produced
plausible, publishable, wrong numbers at HTTP 200.**

**(i) A paging parameter silently ignored.** The split feed's data endpoint accepts
`?p=2`, `?page=2` and `?p=5` and returns **HTTP 200 with page 1 every time** — I verified the
returned rows were byte-identical across all three. Any harvest that trusted pagination would have
silently re-counted the same 50 rows N times. **Caught by comparing the first three dates across
pages.**

**(ii) A field that looks like a count and is an index.** The same endpoint returns a field
literally named **`fullCount`**. Taken at face value it gives:

> 2000: 218 · 2005: 221 · 2010: 230 · 2015: 233 · 2020: 231 · 2024: 236 · 2026: 213

**which I nearly reported as "US splits per year are flat at ~230 for 27 years".** That is false and
it contradicts everything in §1. `fullCount` is a **devalue-style back-reference index into the
payload's flat array**, and `len(flat)` equals it +1 in every single year — it is a function of the
50-row page size, not of split activity. I caught it **only** because near-constancy across 27 years
was implausible against the known collapse in splitting, and confirmed it by decoding the payload
and finding `fullCount`→`"Oct 29, 2015"` for one year and an out-of-range index for another.

**The general lesson for the programme is the one already in the shared rules, and it bit twice in
one lane: a 200 with a plausible-looking number is not a measurement.** Both were caught by
controls, not by reading the response.

---

## 8. WHAT WOULD HAVE TO BE TRUE, and the honest residual

### 8.1 The residual

I am not closing anything — only the principal closes an avenue. The residual, stated as precisely
as I can:

1. **The one solid modern fact here is a volatility fact.** Shue & Townsend's ~30% permanent
   volatility/beta jump at the split execution date, diff-in-differences identified, replicating
   Ohlson & Penman across 35 years, is the most robust result in this territory. **If the programme
   ever wants a clean instrument for "a price-level change with fundamentals held fixed", the split
   ex-date is it** — for studying the *price-level* question (J4's territory), not for a return.
2. **The clean-announcement subsample was never measured.** Nobody in the literature I found
   separates splits announced in a standalone Item 8.01/7.01 filing from splits announced inside an
   Item 2.02 earnings release. My §2.4 measurement says that is a ~30–50% / ~36–68% split of the
   modern population. **That is a genuinely unexamined question** — but the clean subsample is
   single-digit events per year, which kills it on §1's arithmetic before it starts.
3. **A per-company announcement-date route WORKS, at 10/16 within a day, and its failures are
   diagnosable** (§6.2). That is enough to build on. It is also the only part of this lane I would
   call reusable: the same route recovers announcement dates for *any* 8-K-disclosed corporate
   event, which is worth more to the programme than the split territory itself.

### 8.2 Pre-registered predictions, each computable from what this brief already holds

Per the programme's rule that a prediction must be checkable in the runner's own quantities:

1. **If the programme counts forward splits in its own corporate-action feed, restricted to
   as-traded close ≥ $5, a dollar-volume screen, ratio ≥ 1.5, one row per economic event
   (collapsing dual share classes), and excluding ratios above 20:1 as reorganisation artefacts,
   the count will be between 10 and 30 per year for 2010–2026, and 2022 and 2023 will be the two
   lowest years.** Computable from the existing feed with no new data.
2. **Commerce Bancshares and Landmark Bancorp will each appear as a "split" in at least 6 of the
   17 years**, at ratios near 1.05-for-1. If they do not, the feed is filtering stock dividends and
   §1.3's decomposition needs re-deriving.
3. **The median post-split as-traded close across that cohort will exceed $40, and no event will
   fall below $5.** If any does, my §0 claim that killer 1 is structurally absent is wrong.
4. **At least one-third of those events will have an earnings date within ±2 trading days of the
   announcement date**, if announcement dates are obtained. This is the §2.4 confound in the
   programme's own quantities.

### 8.3 What would change the verdict

Only one thing: **a post-2010 US CAR measurement on the clean (non-earnings) subsample showing a
positive GROSS mean per trade above the nulls, with the count large enough to matter.** §1 says the
count is not large enough to matter. I would want the principal to overrule §1's arithmetic, not
§2's or §3's evidence, because the arithmetic is the binding constraint and it is the part I
measured myself.

---

## 9. METHOD — scripts, raw calls, and negative controls

All scripts are in the session scratchpad
(`…/268972c6-b281-4926-b9db-c5611e52a2c6/scratchpad/`). **Nothing here is in `data/`; if any number
in this brief is to be quoted by a record, the script and its output belong in `data/` first.**

### 9.1 EDGAR forward-split census
`edgar_census.py` (first pass, filing counts), **`edgar_harvest2.py`** (the series in §1.2, threaded,
`[SPEED] req=571 fails=0 sum(item)=492s wall=77s ratio=6.36× on 6 workers (106%)`),
`edgar_items.py` (per-filing item profile, §2.4), `edgar_recall.py` (coverage boundary, first-filing
profile, the 16-case phrase recall test), `edgar_phrase_test.py` (exact-phrase semantics; found the
`"20-for-1 stock split"` all-forms count of 499 in 2024 is **Goldman Sachs 424B2 structured-note
boilerplate**, removed by `forms=8-K`, which leaves 1), `edgar_and_test.py` (AND semantics; NVIDIA's
wording), `edgar_final.py` (wording-complete set; this is the run that hit the 403),
`edgar_gentle.py` (serial finisher with escalating backoff).

Endpoint: `https://efts.sec.gov/LATEST/search-index?q=<phrase>&forms=8-K&startdt=&enddt=&from=`
User-Agent: `BacktestFramework Research research@backtest-framework.org` (a project mailbox, per the
shared rules; **no personal address was used anywhere in this lane**).

Controls as tabulated in §1.1. **Union series** (ratio-phrase filers vs adding `"forward stock
split"`, the wording that caught NVIDIA), from `edgar_gentle.py`, complete 2010–2026:

| year | ratio-phrase filers | `"forward stock split"` filers | UNION |
|---|---|---|---|
| 2010 | 104 | 193 | 290 |
| 2011 | 127 | 161 | 281 |
| 2012 | 119 | 155 | 264 |
| 2013 | 113 | 173 | 278 |
| 2014 | 138 | 156 | 290 |
| 2015 | 105 | 129 | 230 |
| 2016 | 89 | 128 | 212 |
| 2017 | 85 | 103 | 185 |
| 2018 | 64 | 82 | 144 |
| **2019** | **46** | 93 | **137** |
| 2020 | 59 | 117 | 174 |
| 2021 | 70 | 156 | 221 |
| 2022 | 62 | 120 | 176 |
| 2023 | 55 | 144 | 194 |
| 2024 | 63 | 167 | 213 |
| 2025 | 49 | **184** | 214 |
| 2026 → 08-26 | 33 | 110 | 134 |

**The two columns move in OPPOSITE directions after 2019** — ratio-phrase filers are flat-to-down
(46 → 49) while `"forward stock split"` filers nearly double (93 → 184). That is the signature of
the second population, not of a split revival: `"forward stock split"` is the wording of OTC shells
doing float engineering ahead of reverse mergers, and it tracked the 2020–2025 microcap boom.
**It is an upper bound, not a correction**, and the ratio-phrase series in §1.2 remains the better
proxy for operating companies. The union never regains half its 2010 level on either measure.

### 9.2 Split feed, used for ex-dates and for NAMING events
`sa_probe.py`, `sa_years.py` (**the run that produced the false `fullCount` series — kept
deliberately as the record of the defect**), `sa_decode.py` (the decode that exposed it),
`sa_rate.py` (the windowed samples and the named objects in §1.3).

Endpoint: `https://stockanalysis.com/actions/splits/<year>/__data.json`
**Negative controls:** years **1970, 1990, 2035, 9999 all return `{"type":"error","message":"not
found"}`**; 1999 is the earliest year with data. **Positive/content control:** every one of the 50
returned rows falls inside the requested year, asserted in code (`assert all(parse_date(r["date"]).year == yr …)`)
for all 27 years — **this is what proves the year path is honoured**, given that `fullCount` is not.
**Known limits:** the endpoint returns only the newest 50 rows of each year, pagination is silently
ignored (§7.1), so all per-year rates derived from it are **Q4-window estimates with a 21–148 day
window annualised**, which is why §1.3 is stated as an order of magnitude and not a count. I did
not rely on these rates for any headline; §1.2's EDGAR series and §1.4's published counts carry the
argument.

### 9.3 Announcement-to-ex-date gaps (§6.1)
Computed from 17 named splits. **Announcement dates verified against the primary filing for NVDA
(2024-05-22, read from `nvda-20240522.htm` Item 8.01 and `q1fy25pr.htm`), GOOGL (2022-02-01 8-K),
CMG (8-K 2024-03-20 against a reported 2024-03-19), WMT (8-K 2024-01-31 against a reported
2024-01-30), LRCX (2024-05-21), AAPL (2020-07-30), TSLA (2020-08-11).** The remaining ten
announcement dates are from secondary sources and my own knowledge and are **[UNVERIFIED]**; the
19-day minimum and the 167-day maximum both come from *verified* cases (TPL/NVDA and GOOGL), so the
"no fixed offset" conclusion does not rest on the unverified ones.

### 9.4 Announcement-date retrieval test (§6.2)
`annc_route.py` / Job B of `edgar_gentle.py`. Route:
`q="stock split"` + `entityName=<CIK>` + `forms=8-K` + window `[ex−400d, ex]`, earliest `file_date`.
**Controls:** SEC `company_tickers.json` loaded 10,407 tickers; bogus `ZZQXWV` **absent** (must be);
dead `ENRNQ` and `LEHLQ` **both absent** — which is not a control failure but **the §6.2 finding
that the map is not dead-inclusive.** Scored 8 exact / 2 off-by-one-day / 1 off by 8 days / 4 wrong
by 94–264 days / 1 not found, on 16 named splits. **The 4 large errors are the real result** and are
diagnosed in §6.2.

### 9.5 PDFs extracted and read locally
`pypdf` extraction, then pattern-grep with ±380 characters of context, via `pdfgrep.py`. **No
figure in this brief tagged [read in full] came from a summariser.** Files: `ikenberry.pdf`
(Ikenberry & Ramnath), `Splits_2001_WP.pdf` (Lipson), `131684.pdf` (the 2004–2011 NYSE CAAR paper —
Table 3 read off the extracted text), `NPT-Shue-202006.pdf` (Shue & Townsend), `w13762.pdf`
(Baker, Greenwood & Wurgler, downloaded, **not read**).

### 9.6 Safety
**No page, PDF or search result in this lane contained text addressed to me or instructing me to
take any action.** I downloaded no file I did not name, created no account, entered no credentials,
submitted no form and logged into nothing. The Stooq proof-of-work bot-check (§7) I declined to
defeat. One page's content is worth flagging as *data* rather than instruction: the split feed's
`meta description` reads *"A list of all stock splits on the US stock market in 2015, including both
regular (forward) and reverse splits"* — the word **"all"** is the vendor's claim about its own
coverage and I did not verify it; §1.3 shows the feed also contains non-splits.

---

## 10. What I could not verify, stated plainly

1. **The true count of US forward splits per year on exchange-listed operating companies.** I have a
   measured **lower bound** (distinct 8-K filers, §1.2), a measured but **Q4-biased** estimate from a
   50-row-capped feed (§1.3), and **three independent published anchors** (§1.4) that agree on the
   order of magnitude. I do **not** have a clean, dead-inclusive, one-row-per-event count, and I
   could not find a free source that provides one. **The 10–25/yr "tradeable" figure in §1.3 is my
   own inference from named Q4 windows, not a census.**
2. **How many would pass a $5-close and dollar-volume floor — the $5 half is settled, the
   dollar-volume half is not.** No forward split I examined lands near $5 post-split, and I am
   confident on that. **I could not price a single event myself**: the only free price endpoint I
   found returns a bot-verification page at HTTP 200 for real and bogus tickers alike (§7), and I
   would not defeat it. So the dollar-volume screen's bite — which I expect falls hardest on the
   small regional banks in §1.3 — is **unmeasured**.
3. **Nayar & Rozeff 2001 and Kadapakkam, Krishnamurthy & Tse 2005 — the two papers that carry the
   entire ex-date section — were NOT read in full.** Both are [abstract and snippet only]. The
   decimalization result in §3.2 is the single most load-bearing claim in §3 and it rests on an
   abstract plus search-summary paraphrase. **If the lane is revisited, read that paper first.**
4. **No post-2015 US academic event study of split announcement CARs was located.** I am treating
   the absence as weak negative evidence. It is possible one exists behind a paywall my tools did
   not reach. The most recent US CAR numbers I read in full stop at **2011**.
5. **The announcement-date route was scored on 16 cases only, and the HARDENED version was not
   scored at all.** The 10/16-within-a-day figure is for the naive earliest-match rule. The obvious
   fixes — require a ratio phrase, drop 5.02/5.07-only filings, shorten the window — are untested,
   so **there is no recall figure for the version anyone would actually use.** n=16 is also far too
   small to characterise a route that has to work on hundreds of events.
6. **The Item 2.02 confound share (36–68%) is an approximation.** It is measured on the *earliest*
   8-K per company per year that mentions a forward-split ratio phrase. That is a proxy for the
   announcing filing, not the announcing filing itself: a company whose split was first mentioned in
   an earnings 8-K *after* a standalone press release with no 8-K would be misclassified. The
   direction of the error is unknown to me.
7. **The CFA digest in §1.4 did not name its underlying paper.** The attribution to Minnick & Raman
   (*Financial Management* 2014) comes from a search result title, not from the digest, and **I did
   not open the paper.** The 23%→<1% figures are from a summariser and should be treated as the
   weakest numbers in §1.
8. **The Russell 1000 "15% → 5% → practically ceased" series is [snippet only] and unsourced** in
   what I read. I report it as directional and would not quote it.
9. **The "76 forward stock splits in 2024" and "37 in H1 2026" figures are [snippet only]** from a
   practitioner blog's search summary; the Wall Street Horizon article I *did* read in full gives
   different, global, mixed forward/reverse counts, and I could not reconcile them.
10. **The union census in §9.1 is complete for 2010–2026, but its interpretation is not measured.**
    I assert that the `"forward stock split"` column is dominated by OTC shells; that rests on the
    named objects I inspected in §1.3 (`!otc/` prefixes, sub-$1 names, 1,000-for-1 ratios), **not on
    a classification of the 184 filers in 2025.** I did not classify them.
11. **Whether the DJIA divisor channel at a split ex-date is material.** I did not measure it; it is
    on the exclusion list and I stopped at noting it exists.
12. **Every one of the reverse-split return figures in §5 is [snippet only].** I opened none of
    those papers.
