# H1 — THE 8-K ITEM-CODE MAP

External-evidence brief. **I have no access to this programme's data and claim nothing about it.**
Everything below is either (a) SEC primary documentation fetched and read locally, (b) published
research read at the stated depth, or (c) **my own measurement against EDGAR**, whose method and
verification are stated so it can be re-run and disagreed with.

Written 2026-09-09. Excluded per brief: Items 1.01, 2.02, 3.01.

---

## 0. BOTTOM LINE, STATED AGAINST MY OWN COMMISSIONING PREMISES

Two of the premises I was handed are **wrong**, and one candidate is **not what it was thought to
be**. Those come first because they outrank the leads.

1. **WRONG PREMISE — the 22:00 ET cut-off.** The brief says "the SEC moved the relevant EDGAR
   cut-off from 17:30 to 22:00 ET on 2024-02-05". The 2024-02-05 change applies to
   **Schedule 13D, Schedule 13G and their amendments only**. Form 8-K was not touched and still
   carries a **17:30 ET** filing-date cut-off. Verified from two SEC pages (§7). If the puller's
   look-ahead repair is built on a 22:00 rule for 8-Ks it will be wrong — though, importantly,
   **in the conservative direction**, so it is not the dangerous bug. The dangerous bug is different
   and I quantify it below.

2. **WRONG PREMISE — `acceptanceDateTime` is not a usable fix on its own.** The brief treats
   switching from `filingDate` to `acceptanceDateTime` as the repair. **That field's timezone is
   inconsistent.** It is serialised with a `Z` (UTC) suffix, but on a 60-filing hand-check against
   EDGAR's own index pages and SGML headers, **35 of 60 were Eastern Time mislabelled as `Z`, and
   25 of 60 were genuine UTC** — mixed within the same day and the same filer agent. Proven
   independently: using `filingDate` plus the SEC's 17:30 ET rule as an arbiter over 577 filings,
   **34.0% can only be UTC and 5.0% can only be ET**. Both cannot be one convention.
   **The authoritative field is `<ACCEPTANCE-DATETIME>` in the submission's SGML header, which was
   consistent with `filingDate` under the 17:30 rule on 60 of 60.** §7.4.

3. **THE ACTUAL LOOK-AHEAD IS LARGE AND CANNOT BE PINNED DOWN FROM THE JSON ALONE.** On my sample of
   **577 Item 4.02 8-Ks (2018–2025)**, the share accepted after the 16:00 close while still carrying
   that day as `filingDate` is **between 30.7% and 65.7%** — the bracket is wide *because* of the
   timezone defect above. Either end is a serious leak on an overnight-edge book. And **73.0% have
   `reportDate` earlier than `filingDate`** (gaps out to 13+ calendar days), so keying on
   `reportDate` is far worse again. Numbers and the derived rule in §7.

4. **ROUTE (b) IS NOT SUPPORTED FOR ITEM 4.02, AND THE EVIDENCE AGAINST IT IS FROM 2005–2006, NOT
   FROM THE 1990s.** The 4.02 move is **fast and small**: −1.0% over three days around the event,
   −1.6% around the filing, and **+0.13% / +0.52% / +0.94% (all insignificant) over the following
   30/60/90 days**. The whole effect is in the announcement window, and it was already that small
   two decades ago. §4.

5. **THE PREMISE NUMBER KILLS TWO OF THE FOUR CANDIDATES OUTRIGHT.** Item 2.06 fires **54–180 times
   a year across every SEC filer in existence**; Item 5.02 fires **11,400–15,300 times a year**.
   One has no sample, the other is not an event. §1.

**Disposition.** Of the four candidates, **only Item 4.02 survives both ends of the count test**, and
it survives it thinly (~150–300 filings/yr recently, of which roughly half are on a major exchange
before any price or volume screen). Its published effect size is roughly **one to two times the
round-trip spread this programme measures on the names it holds**, with no drift after. Item 4.01 has
sample but a near-zero published mean. I would not commission a study on 2.06 or 5.02 on these
numbers. **This is a survey, not a recommendation — closing an avenue is the principal's call.**

---

## 1. THE PREMISE NUMBER: FILINGS PER YEAR, PER ITEM CODE

### 1.1 How I got it, and how I know it is not garbage

EDGAR full-text search (`efts.sec.gov/LATEST/search-index`) accepts an undocumented **`items=`**
filter. The `_source` of every hit carries an `items` array, so counts can be taken per code per
year directly from the SEC.

**One thing went badly wrong and two guards caught it. State all three, because the failure would
silently poison any re-run and it does not announce itself:**

- **THE FAILURE — the SEC/CDN edge caches on a key that ignores `items`.** My first harvest returned the *same*
  numbers for every code — the response for the first code queried in a given
  `(q, forms, startdt, enddt)` window was replayed for every subsequent code. A `_cb=` cache-buster
  did **not** help (the cache key drops unrecognised params). **Varying `from=` does** — it is a
  recognised parameter and does not change `hits.total`.
- **GUARD 1 — a negative control.** `items=9.99` returns **0 in every year** (bottom row of the
  table). Before the fix it returned Item 4.02's numbers, which is how I knew the filter was being
  ignored rather than merely returning odd counts.
- **GUARD 2 — an assertion on every page**: every returned hit must actually carry the requested
  code. It **fired** on the contaminated run and is silent on the clean one — i.e. I checked the
  check by watching it break something I knew to be broken.

**Documents vs filings.** For yearly windows I paged all 4,617 Item 4.02 hits, 2010–2025, and
**distinct accession numbers == document count in every single year**. The `items` filter returns one
hit per filing, not one per exhibit. No dedup factor is needed.

**Three independent cross-checks that the counts are right:**

| my EDGAR count | independent source | their number |
|---|---|---|
| 4.02 in 2019 = **103** | Audit Analytics, US 10-K filers, deduped for affiliated registrants | **85 disclosures by 82 companies** |
| 4.02 in 2021 = **866** | a commercial 8-K data vendor | **864** |
| 4.02 in 2020 = **104** | same vendor | **96** |
| 4.02 2005–06 ≈ 560/yr implied | Lerman & Livnat, 125,000 8-Ks 2005–06 | **1,124 over two years** |

Residual differences are exactly what you would expect: I count *filings by any filer*, they count
*restatements by US 10-K filers, deduped*.

### 1.2 Form 8-K filings per year carrying each item code (2010–2025)

Source: my measurement, EDGAR full-text search, `items=` filter, `forms=8-K`.
Item 5.02 row is summed from monthly windows because yearly queries hit Elasticsearch's
10,000-result cap.

```
item      10     11     12     13     14     15     16     17     18     19     20     21     22     23     24     25
1.02    1274   1371   1210   1062   1150   1140   1101   1076   1081    930    969   1139   1039   1020    944    991
1.03     200    158    129    120    110    100    169    114     85    112    175     71     42    158    160     88
1.04       0      1     60     32     41     25     12     15     11     16      8     10     11     10     10     10
1.05       0      0      0      0      0      0      0      0      0      0      0      0      0      3     38     19
2.01    2336   2562   2357   2351   2467   2239   1876   1822   1714   1520   1247   1755   1336   1144   1103   1173
2.03    4531   5033   4963   4950   5022   5029   4772   4918   4698   4555   5399   5089   4759   4994   5256   5165
2.04     278    227    203    173    160    181    187    154    124    154    194    117    120    198    184    153
2.05     304    278    354    312    294    325    305    264    217    256    303    122    272    469    367    269
2.06     166    145    180    141    118    123    105    101     76     98     87     54     57     73     67     70
3.02    3870   3727   3327   3465   3596   3405   3056   3254   2996   2770   3076   3965   2842   3152   3676   4115
3.03     936    980    935    965    858    947   1009    990    896    946   1025   1109   1077   1209   1180   1154
4.01    1736   1538   1231   1631   1462   1263   1007   1006    867    741    627    797    817    855   1025    811
4.02     491    428    365    339    257    222    184    146    137    103    104    866    307    269    250    149
5.01     962    981    944    867    765    717    682    671    575    483    473    640    473    428    413    431
5.02   15332  15092  14619  14246  14655  14361  13217  12902  12642  12393  12441  12987  12865  12474  11565  11446
5.03    2812   2778   2685   2793   2854   2914   2932   2699   2412   2331   2956   3082   2763   3396   2790   2602
5.05     138    139    141     98    144    113     93     92     94     74     98    109    116    119     77     75
5.06     295    405    350    322    219    140    101    109    107     63     86    188    103    119     70     56
5.07    5024   6144   5312   5170   5128   5201   5070   5395   4944   4911   4903   5184   5663   6120   5577   5323
5.08       0      2     45     67     66     68     61     71     84     98    112     88    140    134    133    139
6.02       3      3     11     24     30     16     34     13     73     36     78    499    172     98     40    505
9.99       0      0      0      0      0      0      0      0      0      0      0      0      0      0      0      0
                                                                                      ^^ negative control
```

(2025 is a partial/most-recent year in EDGAR's index at time of writing; treat it as indicative.)

### 1.3 How many land on a name that could pass a $5 + dollar-volume floor

**I cannot compute this — I have no price data.** What I *can* do is bound it three ways, and all
three say the same thing.

**(a) Direct, but survivorship-poisoned.** I joined all 4,617 Item 4.02 filers to SEC's
`company_tickers_exchange.json` (CIK → ticker → exchange, **current registrants only**):

```
year   n 4.02   SIC 6770 (blank check)   has current ticker   on NYSE/Nasdaq/AMEX today
2019    103        1 ( 1.0%)                35 (34.0%)            26 (25.2%)
2020    104        1 ( 1.0%)                59 (56.7%)            44 (42.3%)
2021    866      561 (64.8%)               262 (30.3%)           218 (25.2%)
2022    307      122 (39.7%)               116 (37.8%)            88 (28.7%)
2023    269       44 (16.4%)               162 (60.2%)           125 (46.5%)
2024    250       21 ( 8.4%)               165 (66.0%)           111 (44.4%)
2025    149        7 ( 4.7%)               118 (79.2%)            75 (50.3%)
```
The "has current ticker" column rises monotonically with recency **because older filers have since
died or deregistered** — this measures survival, not listing at the filing date, and it is therefore
a *lower* bound for older years. For the recent years where survivorship bites least, roughly
**45–50% of Item 4.02 filings are on a major exchange**, before any price or volume screen.

**(b) Contemporaneous, and much better evidence — from the Treasury study.** Measured *at the time*,
across 6,633 restatements 1997–2006: only **3,310 restatement announcements had CRSP return data —
50% of the initial sample**. And the missing half were tiny: *"Median assets (revenues) for restating
companies without return data are $17.4 ($12.6) million. This compares to median assets (revenues) of
$331.8 ($224.8) million for the remaining restating companies."* CRSP covers NYSE/AMEX/Nasdaq
common stock, so **half of the restatement population is not on a major exchange at all**, before a
$5 screen is even applied.

**(c) The 2021 contamination is enormous and structural.** **561 of 2021's 866 Item 4.02 filings
(64.8%) are SIC 6770 blank-check companies** — the SPAC warrant restatement wave triggered by the
SEC staff statement of **12 April 2021**. A commercial vendor's write-up attributes the 2021 spike
to "the COVID-19 pandemic"; that is simply wrong, and it is a reason to distrust that vendor's
analysis generally. For a dead-inclusive $5-floored universe this year is a landmine: SPACs trade at
a pinned ~$10 trust value on near-zero volume, so they can *pass* a naive $5 close screen while being
untradeable, and they will dominate any pooled 2021 result.

**My honest estimate of the tradeable count for Item 4.02:** taking recent years' ~45–50%
major-exchange share and haircutting further for a $5 close and a dollar-volume floor on a
population of firms that are by construction in accounting trouble, I would expect
**roughly 50–120 events per year**, i.e. **on the order of 1,000–1,800 over 2010-01-04 to 2026-08-26**
— and lumpy, with 2021 either dominating or excluded. Against ~10 effective independent instruments,
that is a thin but not hopeless sample. **This number is an estimate, not a measurement, and the
programme can compute it exactly from its own fixture in one pass.**

### 1.4 The verdict on the count test alone

| code | fires/yr (all filers) | too rare? | too common? | survives? |
|---|---|---|---|---|
| **4.02** | 103–866 (recent ~150–300) | borderline | no | **yes, thinly** |
| **4.01** | 627–1,736 (recent ~800–1,000) | no | no | **yes** |
| **5.02** | 11,446–15,332 | no | **yes — ~45–60 per trading day** | **no** |
| **2.06** | 54–180 (recent ~55–75) | **yes** | no | **no** |

---

## 2. THE MAP: WHICH CODES ARE DATED, MECHANICAL, FREE, DEAD-INCLUSIVE, UNSTUDIED

All 8-K codes are equally **dated** (`reportDate` + `filingDate` + `acceptanceDateTime`),
equally **free** (EDGAR), and equally **dead-inclusive** (EDGAR keeps filings by companies that
later died; there is no survivorship filter in the archive itself). So those three axes do **not**
discriminate. What discriminates is:

- **Mechanical trigger** — does an objective, dated event force the filing, or does the issuer choose?
- **Sub-paragraph collapse** — the `items` field exposes `"5.02"`, never `"5.02(b)"`. A code whose
  paragraphs carry opposite meanings is unusable without reading the document.
- **Bundling** — is the code usually filed alone, or with earnings?
- **Study saturation.**

| code | mechanical? | sub-paragraph problem | typically bundled? | literature |
|---|---|---|---|---|
| 4.02 Non-reliance | **strongly** — trigger is the dated board/officer conclusion | (a) issuer-concluded vs (b) auditor-notified; both bad news | **no — 74.4% filed alone** | large, old, decaying |
| 4.01 Auditor change | **strongly** — resignation/dismissal/engagement | (a) departure vs (b) engagement, opposite information | mostly alone | moderate, mixed |
| 5.02 Officers/directors | partly — but (c)/(d) may be delayed to the announcement day | **fatal**: (a) disagreement-exit, (b) departure, (c) appointment, (d) director election, (e) **pay grants** all share one code | often | very large, near-zero mean |
| 2.06 Impairments | yes, but with a **giant carve-out** (§3.4) | none | **~95% with earnings** | moderate |

**Others that deserve attention, from my counts and Lerman & Livnat's return map:**

- **Item 3.03 "Material modifications to rights of security holders"** — 858–1,209/yr, stable,
  and it carries the **largest positive** announcement return in the whole item map
  (**+2.84%** 3-day around event, **+2.17%** around filing, both p<0.01) with **+1.45%** at 60 days
  (p<0.10). I have not seen a dedicated literature on it and it is not on this programme's exclusion
  list. It is mechanically triggered and reasonably frequent. **This is the most interesting
  unstudied cell I found, and it is not one of the four I was asked about.** Caveat: it moved from
  periodic reports into the 8-K in 2004, and a large part of it is likely rights-plan and
  preferred-stock mechanics that may be confounded with financing events.
- **Item 2.04 "Triggering events that accelerate a direct financial obligation"** — 117–278/yr
  (too rare), but **−1.53% / −2.50% / −2.04% drift at 30/60/90 days** (p<0.10, 0.05, 0.10) — the
  strongest *drift* in the map after bankruptcy. Rare, mechanical, unambiguously negative in sign.
  Probably the best drift-per-event on the board, and probably too rare to trade here.
- **Item 5.01 "Changes in control"** — 413–981/yr, **+1.62%** at the event but **−2.06% / −3.69% /
  −3.44%** drift at 30/60/90 days. Note this overlaps merger-arbitrage territory, which is excluded.
- **Item 1.03 Bankruptcy** — huge effect (−11.9% at filing, −14.7%/−13.3%/−19.0% drift) but n=18 in
  Lerman & Livnat and 42–200/yr here, and it sits squarely in the excluded "death process".
- **Item 1.05 Material Cybersecurity Incidents** — genuinely new (§6) and genuinely unstudied, but
  my count is **3 (2023), 38 (2024), 19 (2025)**. Far rarer than the commentary implies. No sample.
- **Items 2.03 (4,500–5,400/yr) and 3.02 (2,800–4,100/yr)** are the two high-frequency mechanical
  codes nobody has mined here, but 3.02 is at-the-market/shelf-adjacent (excluded) and 2.03 is a
  debt-facility code whose published effect is **+0.25%** at the event.

---

## 3. PER-CODE EVIDENCE

Read-depth is stated in the same sentence as every number, per the brief's rule.

### 3.1 Item 4.02 — Non-reliance on previously issued financial statements

**The old, large literature.** Palmrose, Richardson & Scholz (2004), *Journal of Accounting and
Economics* 37:59–89, 403 restatements 1995–1999, mean 2-day abnormal return **about −9%**
— *[PEER-REVIEWED] [abstract/snippet only — I did not open the paper; the −9% and the sample
composition come from search-result summaries and from the Treasury report's citation of it]*.
Hennes, Leone & Miller (2008), *The Accounting Review* 83:1487–1519: mean 3-day CAR
**−7.29% for irregularity restatements vs −1.57% for errors**, with 24% irregularities / 76% errors
— *[PEER-REVIEWED] [snippet only — I did not open the paper]*.

**The decay, which is the part that matters and which I did read.** US Department of the Treasury,
April 2008, *The Changing Nature and Consequences of Public Company Financial Restatements
1997–2006* (the Scholz study) — *[PRIMARY DATA DOC — government-commissioned] [read in full: the
market-reaction and one-year-return sections, from the PDF fetched locally and extracted with
pypdf]*. Two-day CAR (announcement day + next day; equal-weighted market-adjusted; the day before is
deliberately excluded because there is little leakage):

| period | 97 | 98 | 99 | 00 | 01 | 02 | 03 | 04 | 05 | 06 |
|---|---|---|---|---|---|---|---|---|---|---|
| **mean** | −8.2% | −12.1% | −7.7% | −10.8% | −3.7% | −1.1% | −0.7% | −0.7% | −0.4% | −1.0% |
| **median** | −4.6% | −6.7% | −2.3% | −7.2% | −1.3% | −1.5% | −0.8% | −0.4% | −0.4% | −0.6% |

*"Average returns for restatements announced from 1997-2000 are -9.5%, but only -1.3% for those
announced from 2001-2006."* Overall average −2.6%, median −0.9%.
**By 2005–2006 — the first years of the Item 4.02 regime — the median was −0.4% to −0.6%.**
That is *smaller than one side* of this programme's measured 33.8 bp spread.

**The item-level number in the 8-K era.** Lerman & Livnat, *The New Form 8-K Disclosures*, March 2008
draft (published as Lerman & Livnat 2010, *Review of Accounting Studies* 15(4):752–778) — *[WORKING
PAPER] [read in full from the PDF at pages.stern.nyu.edu; I did NOT read the published version, and
the published numbers may differ]*. 125,000+ initial 8-Ks, 2005–2006, size-B/M-matched buy-and-hold
abnormal returns, n(4.02)=1,124:

| window | 4.02 |
|---|---|
| 3 days around **event date** | **−1.04%** *** |
| 3 days around **filing date** | **−1.61%** *** |
| event−1 → filing+1 | **−2.34%** *** |
| **+30 days after filing** | **+0.13%** (ns) |
| **+60 days** | **+0.52%** (ns) |
| **+90 days** | **+0.94%** (ns) |
| abnormal volume at filing | +45% *** |
| return-volatility ratio at filing | **3.83×** *** |

**A vendor's modern replication, which I must not treat as evidence for a return.** A commercial
8-K data provider reports, over **8,143 Item 4.02 disclosures 2004–2023** (event analysis 2007–2023),
mean CAR **−0.87%** at +1d and **−1.54%** at +20d; excluding 2021, **−1.10%** and **−2.00%**;
medians **−0.26%/−1.31%** and **−0.50%/−2.64%**. Market model with SPY as the proxy, no price or
liquidity filter mentioned — *[SALES INSTRUMENT] [read in full via WebFetch summariser — a
summariser reading, therefore weaker than a snippet; I did not extract the page's own HTML tables]*.
**This is not evidence for a return.** It is cited only because (i) it is the only modern
replication I found, (ii) a vendor has every incentive to overstate, and it reports a *small*
number, and (iii) its counts (864 in 2021, 96 in 2020) independently corroborate my EDGAR census.
Its causal attribution of the 2021 spike to COVID is demonstrably wrong (§1.3).

**Bundling — a genuine point in 4.02's favour, which I computed myself.** Of my 4,617 Item 4.02
filings 2010–2025, **74.4% carry Item 4.02 alone** (ignoring the boilerplate 9.01). Only 10.0%
are co-filed with 2.02 earnings; 4.3% with 4.01; 3.2% with 5.02; 1.6% with 3.01.
In 2022–2025 the picture is the same (12.3% with 2.02). **Item 4.02 is a clean, unbundled event** —
which is more than can be said for 2.06.

**Speed of resolution.** Audit Analytics, *2019 Financial Restatements: A Nineteen Year Comparison*
(July 2020) — *[PRACTITIONER] [read in full: methodology and executive summary, from the PDF]*: the
average number of days from the Item 4.02 disclosure to the actual restated filing fell from
**~30 days in 2007** to **4.1 days in 2010**, **3.2 days in 2015**, and **6.5 days in 2019**.
The uncertainty is resolved in about a week.

**The population has shifted out from under the code.** Same source: the "Big R" reissuance
restatement — the kind that requires the Item 4.02 8-K — fell from **933 disclosures by 865
companies in 2005** and **949 by 877 in 2006** to **110 by 106 in 2017**, **120 by 115 in 2018**,
and **85 by 82 in 2019**. Meanwhile "little r" revisions — *"any restatement revealed in a periodic
report or other document without a prior disclosure in Item 4.02 of an 8-K"* — reached **79.7% of
all restatements in 2019**. **Four out of five restatements now never generate an Item 4.02 filing
at all.** The severe tail did not disappear; it shrank, and the code catches only what is left.

### 3.2 Item 4.01 — Changes in registrant's certifying accountant

- Lerman & Livnat (as above, n=1,148, read in full): **−0.14% (ns)** 3-day around event,
  **−0.59%*** ** around filing, **−0.84%*** ** event→filing, and **−0.68% / −0.93% / −0.84%
  (all insignificant)** at 30/60/90 days. Abnormal volume only **+28%**, volatility ratio only
  **1.49×** — the weakest reaction of any of the four candidates.
- Griffin & Lont, *Do Investors Care About Auditor Dismissals and Resignations? What Drives the
  Response?*, *Auditing: A Journal of Practice & Theory* 29(2):189–214 (2010): **resignations** draw
  a significantly negative response; **dismissals are mostly insignificant**; the response is larger
  for firms with prior securities litigation and higher bankruptcy risk — *[PEER-REVIEWED]
  [abstract/snippet only — SSRN returned HTTP 403 to both WebFetch and curl; I did not read it]*.
- A separate line (Inderscience, *IJAF* 2019) reports a decline **beginning 60 days before**
  resignation announcements and continuing 30 days after — *[PEER-REVIEWED] [snippet only]*.
  If that holds, the announcement is late to its own news.

**Assessment.** Sample is fine (~800–1,000/yr). Effect is the smallest of the four, and it is
**conditional on resignation-vs-dismissal, which the `items` field does not expose**. The 4.01
amendment rate is also the highest of the four (§6), because Item 304 requires the predecessor
auditor's exhibit letter.

### 3.3 Item 5.02 — Departure/election of directors and officers

**This code fails on three independent grounds.**

1. **It is not an event.** 11,446–15,332 filings/yr — **roughly 45–60 per trading day**.
   Ben-Rephael, Da, Easton & Israelsen note that just **six item codes account for 96.13% of all
   8-K filings**, and 5.02 is one of the six.
2. **The unconditional mean is positive and ~zero.** Huson, Malatesta & Parrino, *Managerial
   Succession and Firm Performance* (July 2002 draft; published *JFE* 2004) — *[WORKING PAPER]
   [read in full from the PDF at faculty.washington.edu]*: *"the average announcement period abnormal
   return for 1,302 cases in our sample is 0.344%. The associated t-statistic is 2.55."*
   Two-day market-model window, WSJ-reported CEO turnovers in large US firms.
   **+34 bp — the same order as one side of this programme's measured 33.8 bp spread, and the
   opposite sign to naive intuition.** Lerman & Livnat's 8-K-era figure for the code is
   **−0.04% (ns)** at the event and **−0.11%** at the filing, with 30/60/90-day drift of
   **−0.28%/−0.36%/−0.45%** — statistically significant on n=15,056, and economically
   **~5 bp per month against a 67.6 bp round trip**.
3. **The code cannot be decoded from the header.** I verified live against
   `data.sec.gov/submissions/CIK0000320193.json` that the `items` field returns the bare string
   `"5.02"` with **no sub-paragraph letter**. Since **Item 5.02(e) (compensatory arrangements) was
   folded into this same code effective 7 November 2006** (Release 33-8732A), a routine option grant
   to a named executive officer and a director resigning over a disagreement are **the same code**.

### 3.4 Item 2.06 — Material impairments

**Two structural facts kill this before the returns matter.**

1. **The Instruction to Item 2.06 exempts the ordinary case.** Quoted verbatim from the SEC's own
   Form 8-K PDF: *"No filing is required under this Item 2.06 if the conclusion is made in connection
   with the preparation, review or audit of financial statements required to be included in the next
   periodic report due to be filed under the Exchange Act, the periodic report is filed on a timely
   basis and such conclusion is disclosed in the report."* **Item 2.06 is a residual code**: it
   catches only off-cycle impairment conclusions. That is why it fires 54–180 times a year while
   thousands of firms take impairments.
2. **Impairments arrive with earnings.** Li, Shroff & Venkataraman, *Goodwill Impairment Loss:
   Causes and Consequences* (April 2004 working draft; the published line is Li, Shroff,
   Venkataraman & Zhang 2011, *RAST*) — *[WORKING PAPER] [read in full from the PDF at
   assets.csom.umn.edu; I did NOT read the published 2011 version]*: *"roughly 95% of all
   announcements of impairment losses are made simultaneously with annual or quarterly earnings
   announcements."*

**Returns.** Same paper, 3-day (−1,0,+1) abnormal return: full sample **−0.48%** (p<0.05); firms with
a negative earnings change **−1.18%**; on the I/B/E/S subsample all firms **−1.43% (insignificant)**,
and firms with negative unexpected earnings **−5.04%**. The paper also documents anticipation:
**−4.1%** over the four quarters before, **−23.1%** (significant) over the eight quarters before.
Lerman & Livnat give **−1.13%/−1.65%/−2.31%** around event/filing/event→filing and — uniquely among
the four — **significant negative drift of −1.23%*** / −1.62%** / −1.95%** at 30/60/90 days**,
on n=532.

**Assessment.** The only candidate with real post-filing drift, and the only one with a structurally
unambiguous sign — but **~70 filings a year across every filer in the United States**, before any
listing, price or volume screen. There is no sample here.

### 3.5 The finding that spans all four codes

Ben-Rephael, Da, Easton & Israelsen, *Who Pays Attention to SEC Form 8-K?* (this version 20 Aug 2021;
published *The Accounting Review*, 2022) — *[PEER-REVIEWED, read in the working version] [read in
full from the PDF at www3.nd.edu]*:

> *"our evidence suggests that the Form 8-K filing may have little direct informational benefit,
> particularly to retail investors."*

and, in the body:

> *"These results suggest that the actual 8-K filing has limited informational benefit: institutional
> investors have already learned about the event, trade on it and the price has adjusted before the
> filing date."*

They document abnormal Bloomberg-terminal attention on **63% of event dates** against a 44%
simulated benchmark, and show that abnormal institutional attention in the pre-filing window
**reduces** filing-period price discovery by **−11.9%, −13.1% and −5.4%** for filing gaps of two,
three and four business days — and by **−9.6% specifically for Item 5.02**.

**This is the central negative for the whole territory.** The 8-K filing is, on average, the *second*
publication of the news. Anything keyed on `filingDate` or `acceptanceDateTime` is trading the echo.
Item 4.02 is the partial exception, because for a non-reliance conclusion the 8-K usually *is* the
first disclosure — but even there, 4 business days is a long time and the pre-filing gap is where
the price moves.

---

## 4. IS ANY OF THESE ROUTE (b)?

**Route (b) requires a move that is large and slow relative to the spread. Item 4.02 is neither
large enough nor slow at all, and the evidence for that is unambiguous.**

**Large?** Take the *most favourable* modern number in the file — Lerman & Livnat's **−1.61%**
three-day CAR around the filing date, from 2005–2006. This programme measures **33.8 bp/side** on
the names it actually holds, i.e. **~67.6 bp round trip**, and states that estimator is *suspected of
understating* small/illiquid spreads. So the best case is a gross move of roughly **2.4× the round
trip** — and that is before the per-share commission effect, which scales inversely with price on a
population of firms that are in accounting trouble and therefore cheap. On the Treasury's
contemporaneous 2005–2006 numbers (**mean −0.4% to −1.0%, median −0.4% to −0.6%**) the move is
**at or below one round trip**. A bid-ask toll is not a rounding error here. It is most of the trade.

**Slow?** No. Three separate readings agree:

- Lerman & Livnat: post-filing drift of **+0.13% / +0.52% / +0.94%**, all insignificant and all the
  *wrong sign*. There is no drift to harvest.
- Treasury: *"the market reaction to these restatement characteristics appears to occur mainly at
  announcement, rather than later dates"*, and the announcement return does **not** predict the
  one-year return.
- Audit Analytics: the restatement itself is filed a median **~6.5 days** later. The uncertainty
  closes in a week.

**The one counterweight, stated because bias-to-the-negative is not the same as suppression.** The
Treasury report *does* find a large negative one-year post-announcement return: **mean −4%, median
−17%**, median negative every year, 1997–2005, market-adjusted buy-and-hold or until delisting. But
(i) the regression finds *no* association between the announcement return and the one-year return,
so it is not an event-driven drift you can key on; (ii) the mean is far above the median, so a few
big winners carry it, which is the classic signature of a distress/delisting process — and **"the
death process, delisting returns and the distress anomaly" is on this programme's exclusion list**;
and (iii) the sample period brackets the dot-com bust.

**One genuinely useful finding for a $5-floored universe.** In the Treasury announcement-return
regression, the dummy for *"Stock price less than $5.00"* the day before announcement has coefficient
**+0.017, t=3.18, p=0.00** — the CAR is dependent variable, so sub-$5 names react
**1.7 percentage points LESS negatively**. In the one-year regression the same dummy is
**+0.250, t=4.91**. **This cuts the right way for this programme**: the $5 floor is not screening
out the return, it is screening out the *weaker* reactions. Whether that survives to a modern sample
is unknown.

**Verdict: Item 4.02 is not route (b) on the published evidence.** It is a fast, modest, single-day
repricing with no measurable tail. If any code in the map is route (b), the drift table points at
**Item 2.06** (−1.23%/−1.62%/−1.95% at 30/60/90) and **Item 2.04** (−1.53%/−2.50%/−2.04%) — and both
are far too rare to build on.

---

## 5. SIGN AMBIGUITY: IS THE SIGN DETERMINABLE FROM THE FILING ALONE?

"From the filing alone" I read strictly as: **from the structured metadata — the `items` array,
`form`, `reportDate`, `acceptanceDateTime`, and co-filed codes — without parsing narrative text.**
That is the distinction that decides whether a code costs an NLP pipeline.

| code | sign from metadata alone? | why |
|---|---|---|
| **2.06** | **YES — structurally negative.** | An impairment is by definition a write-down. There is no income-increasing impairment. The only free code with an unambiguous sign. |
| **4.02** | **MOSTLY — structurally negative, but not perfectly.** | The trigger is "previously issued financial statements should no longer be relied upon *because of an error*". Direction of the error is not in the header: some restatements are income-*increasing*, and Palmrose et al. find income-decreasing ones react more negatively. Also 4.02(a) (issuer concluded) vs 4.02(b) (auditor notified) is **not** in the `items` field — I verified the field returns bare `"4.02"`. Both are bad news, so the a/b collapse costs magnitude, not sign. **Call this a structurally-signed code with unknown magnitude.** |
| **4.01** | **NO.** | Resignation vs dismissal vs engagement is the whole signal, and Item 4.01(a) (departure) and 4.01(b) (engagement) collapse to `"4.01"`. Griffin & Lont: resignations negative, dismissals insignificant. An auditor *upgrade* is good news. Requires Item 304(a) narrative → NLP. |
| **5.02** | **NO, and worst of the four.** | (a) disagreement-exit, (b) departure, (c) appointment, (d) director election and (e) a routine pay grant all collapse to `"5.02"`. Even *within* (b), forced vs voluntary turnover carries opposite information (Huson/Malatesta/Parrino), and forced/voluntary is a hand-classification from press coverage, not a filing field. |

**The one cheap structural feature available for free on every code: the co-filed item vector.**
It is in the same `items` array. From my own 4.02 sample, 4.3% are co-filed with 4.01 and 1.6% with
3.01 — combinations that are unambiguously worse news than 4.02 alone. This is the only sign
refinement that costs nothing.

---

## 6. THE DATA QUESTION: WHEN EACH CODE CAME INTO EXISTENCE, DEADLINES, AMENDMENT RATES

### 6.1 Existence — the adopting release

**SEC Release Nos. 33-8400; 34-49424, "Additional Form 8-K Disclosure Requirements and Acceleration
of Filing Date"**, adopted 16 March 2004, published *Federal Register* Vol. 69 No. 58, 25 March 2004,
pp. 15594 et seq. — *[PRIMARY DATA DOC] [read in full: I fetched
`https://www.sec.gov/files/rules/final/33-8400.pdf` locally, extracted 37 pages with pypdf and read
the relevant sections]*.

> **EFFECTIVE DATE: August 23, 2004.**

> *"These amendments add eight new items to the form, transfer two items from the periodic reports
> and expand disclosures under two existing Form 8-K items. Due to the increase in reportable events
> under the form, we are reorganizing the Form 8-K items into topical categories."*

**The decimal numbering scheme itself (`X.YZ`) begins 2004-08-23.** Before that date 8-K items were
numbered 1–12. **For this programme's window (2010-01-04 onward) every candidate code exists for the
entire sample.** That is the practically important answer, and it makes the "when did it come into
existence" question moot for 4.02/4.01/5.02/2.06 — but it matters for the two codes below.

Per-candidate provenance, from the release text:

- **Item 4.02** — *"This new item…"*. Genuinely new at 2004-08-23. **No pre-2004 analogue.**
- **Item 4.01** — *"This item is substantively the same as former Item 4 of Form 8-K"*. The
  *disclosure* long predates 2004; only the code does not.
- **Item 2.06** — *"This new item…"*. New at 2004-08-23.
- **Item 5.02** — paragraph (a) *"broadens the scope of former Item 6 of Form 8-K"*. **Paragraph (e),
  compensatory arrangements, was added later** by Release 33-8732A (issued 29 August 2006),
  **applying to triggering events on or after 7 November 2006**, which simultaneously removed
  executive compensation arrangements from Items 1.01/1.02. **This is the amendment that turned 5.02
  into a high-frequency pay-disclosure code.** *[the 33-8732A date and scope: [PRIMARY DATA DOC]
  [snippet only — I read the search summary of the SEC release and of two law-firm alerts, and did
  not open 33-8732A itself]*.
- **Item 1.04 Mine Safety** — first appears in my counts in 2011 (1 filing) and 2012 (60).
- **Item 1.05 Material Cybersecurity Incidents** — first appears **2023 (3 filings)**, then 38 in
  2024. Confirmed present on the current Form 8-K.
- **Item 5.07 / 5.08** — 5.08 first appears in my counts in 2011 (2) and 2012 (45).

### 6.2 Deadlines — from the current Form 8-K itself

Quoted verbatim from the SEC's own Form 8-K PDF (`https://www.sec.gov/files/form8-k.pdf`,
SEC 873 (02-25)), General Instruction **B.1** — *[PRIMARY DATA DOC] [read in full, locally extracted]*:

> *"Unless otherwise specified, a report is to be filed or furnished within four business days after
> occurrence of the event. If the event occurs on a Saturday, Sunday or holiday on which the
> Commission is not open for business, then the four business day period shall begin to run on, and
> include, the first business day thereafter."*

Per candidate:

| code | deadline | clock starts on |
|---|---|---|
| **4.02** | 4 business days | the **date of the conclusion** of non-reliance (4.02(a)) or the date the registrant **was advised/notified** by the accountant (4.02(b)) |
| **4.02(c)** | **2 business days** | the registrant's **receipt of the accountant's letter** — filed as an amendment |
| **4.01** | 4 business days | resignation / declining re-appointment / dismissal; **the engagement of the new accountant is a separate reportable event** and often a second 8-K |
| **2.06** | 4 business days | the **date of the conclusion** that a material impairment charge is required; **amended report within 4 business days** of determining an estimate that was not available at first filing |
| **5.02** | 4 business days | the event — **except 5.02(c)**, where an Instruction lets the registrant *"delay filing the Form 8-K … until the day on which the registrant otherwise makes public announcement of the appointment"*; and **amendment within 4 business days** for information under (c)(3)/(d)(3)/(d)(4) not available at first filing; and **2 business days** for a departing director's letter under 5.02(a)(3)(iii) |

**Compliance with the deadline is high but the last day is popular.** Lerman & Livnat (read in full):
*"nearly 95 percent of filings are made within the new four business day deadline, with a third of
the timely filings for mandatory items made on the last allowed day."*

### 6.3 Amendment (8-K/A) rates — my own measurement

Same method, `forms=8-K/A`. Rate = (8-K/A carrying the code) / (8-K carrying the code) in the same
calendar year. This is an approximation: an amendment filed in January amends a filing from the prior
year, and 8-K/A counts include re-amendments.

| code | 2010 | 2014 | 2019 | 2022 | 2024 |
|---|---|---|---|---|---|
| **4.02** | 104/491 = **21.2%** | 44/257 = 17.1% | 6/103 = 5.8% | 19/307 = 6.2% | 13/250 = **5.2%** |
| **4.01** | 433/1736 = **24.9%** | 336/1462 = 23.0% | 49/741 = 6.6% | 50/817 = 6.1% | 55/1025 = **5.4%** |
| **5.02** | 504/15332 = 3.3% | 517/14655 = 3.5% | 404/12393 = 3.3% | 434/12865 = 3.4% | 412/11565 = **3.6%** |
| **2.06** | 8/166 = 4.8% | 6/118 = 5.1% | 9/98 = 9.2% | 9/57 = 15.8% | 5/67 = **7.5%** |

**Read this as a warning, not a nuisance.** The 4.01 and 4.02 amendment rates were **~21–25% in
2010–2014** and fell to **~5–6%** by 2019. A runner that treats 8-K/A as a fresh event will
manufacture ~20% spurious events in the early sample and ~5% in the late sample — **a
non-stationary contamination that mimics a decaying signal.** For 4.02 the amendment is usually the
Item 4.02(c) auditor letter, which is a genuine but second-order piece of news.

---

## 7. LOOK-AHEAD: THE EXACT TIMESTAMP RULE, DERIVED FROM SEC DOCUMENTS

### 7.1 First, the correction to the premise I was given

**The 2024-02-05 change to 22:00 ET does NOT apply to Form 8-K.** From SEC's own EDGAR Release
24.0.2 announcement page, dated **February 5, 2024** — *[PRIMARY DATA DOC] [read via WebFetch,
verbatim quotes]*:

> *"The filing 'cut-off' times will be extended for **Schedule 13D, Schedule 13G, and corresponding
> amendments**, from 5:30 p.m. to 10:00 p.m. Eastern Time."*
> *"These filings will have a 'Filing Date' identical to the EDGAR 'Received Date' even if received
> after 5:30 p.m. Eastern Time, and will be disseminated until 10:00 p.m. Eastern Time."*

And the SEC's current filer guidance, *Determine the Status of My Filing* — *[PRIMARY DATA DOC]
[read in full: I fetched the page and extracted the text; quotes are verbatim from that HTML]*:

> *"EDGAR's hours of operation are 6:00 a.m. to 10:00 p.m. ET, Monday through Friday, except for
> federal holidays. If you begin transmitting a live submission to EDGAR at or before 5:30 p.m. ET
> on a day that EDGAR is operating, and it is accepted by EDGAR, the submission will receive that
> day's filing date."*
>
> *"Most live submissions that begin transmission after 5:30 p.m. ET on a day that EDGAR is operating
> and are accepted by EDGAR will receive a filing date of 6:00 a.m. ET the next business day and
> **will not be disseminated by EDGAR until the next business day**."*
>
> *"The following submission types transmitted after 5:30 p.m. ET and before 10:00 p.m. ET … will
> receive a filing date of the date transmitted …: 3, 3/A, 4, 4/A, 5, 5/A, 144, 144/A, F-1MEF,
> F-3MEF, F-4MEF, N-14MEF, N-2MEF, POS 462B, S-11MEF, S-1MEF, S-3MEF, S-4MEF, and S-BMEF."*

**Form 8-K is not on that exception list.** (Nor, on this page, are 13D/13G — the two SEC documents
are not fully reconciled with each other, which is itself worth knowing.)

**Why this matters less than it sounds.** The 17:30 cut-off means a late 8-K gets a *later*
`filingDate` than its acceptance. Keying on `filingDate` therefore **understates** how early the
news was available — a conservative error. The dangerous case is the opposite one, and it is common.

### 7.2 The dangerous case, measured

I sampled **400 random CIKs** among Item 4.02 filers 2018–2025 and pulled `acceptanceDateTime`,
`filingDate` and `reportDate` from `data.sec.gov/submissions/`. **N = 577 Item 4.02 filings.**

**Because the field's timezone is inconsistent (§7.4), the acceptance-hour figures come as a
bracket, not a point.** Lower end = every record read as UTC; upper end = the *conservative*
arbitration (use `filingDate` + the 17:30 rule to pin down each record where it can, and where both
readings fit, take the later one).

```
                                                    all-UTC reading   arbitrated/conservative
accepted BEFORE 09:30 ET                             91 (15.8%)          53 ( 9.2%)
accepted 09:30-16:00 ET (intraday)                  264 (45.8%)          96 (16.6%)
accepted at/after 16:00 ET                          222 (38.5%)         428 (74.2%)
filingDate == that date AND accepted at/after 16:00 177 (30.7%)         379 (65.7%)   <-- look-ahead set

  (arbitration outcome: 196 records (34.0%) can ONLY be UTC,
                         29 records ( 5.0%) can ONLY be ET,
                        351 records (60.8%) fit either reading,
                          1 record  ( 0.2%) fits neither -- a holiday my
                            business-day function does not model.)

timezone-independent:
filingDate strictly AFTER acceptance date            66 (11.4%)
filingDate strictly BEFORE acceptance date            0 ( 0.0%)
reportDate strictly BEFORE filingDate               421 (73.0%)

filingDate - reportDate, calendar days:
  0d:156  1d:104  2d:48  3d:63  4d:54  5d:37  6d:57  7d:12  8d:1  9d:4  10d:3  11d:3  12d:1  13d:2
```

**Read the two load-bearing rows.**

- **Somewhere between 30.7% and 65.7% of Item 4.02 8-Ks are stamped with a `filingDate` equal to a
  day whose regular session had already closed when the filing was accepted.** A runner that enters
  at the close of `filingDate` is trading on information released after that close, on somewhere
  between one filing in three and two in three. On an overnight-edge book, that is not a small leak
  — it is the leak sitting exactly on the leg that carries the edge. **And the width of that bracket
  is itself the finding: it cannot be narrowed from the submissions JSON alone.**
- **73.0% have `reportDate` before `filingDate`, with a long right tail.** Keying on `reportDate`
  is catastrophic: it points at the *event* date, which the market has often not seen.

### 7.3 The rule a runner must key on

**Key on the SGML `<ACCEPTANCE-DATETIME>` (Eastern Time), and enter at the first regular-session
close that is strictly after it.**

Written out, with the SEC citation for each clause:

1. Get the acceptance timestamp **in ET**. **Do not use the submissions-JSON `acceptanceDateTime`
   naively — its `Z` suffix is not reliable (§7.4).** In order of preference:
   (a) `<ACCEPTANCE-DATETIME>` from `https://www.sec.gov/Archives/edgar/data/<cik>/<accession-nodash>/<accession>-index-headers.html`
   (or the same tag in the submission `.txt`), which is ET — **this matched `filingDate` under the
   17:30 rule on 60 of 60 filings I tested**; (b) failing that, read the JSON string **as ET**,
   which is the conservative branch: it can only delay a simulated entry, never advance it.
2. Let `T_acc` be that ET timestamp. Define `T_public`:
   - if `T_acc` ≤ **17:30 ET** on a business day → `T_public = T_acc` (EDGAR disseminates
     immediately; the SEC page above says submissions at or before 17:30 receive that day's filing
     date and are disseminated that day);
   - if `T_acc` > **17:30 ET**, or on a non-business day → `T_public = 06:00 ET on the next business
     day` (the SEC page: *"will receive a filing date of 6:00 a.m. ET the next business day and will
     not be disseminated by EDGAR until the next business day"*).
3. **The first tradeable entry is the first regular-session close strictly after `T_public`.**
   Equivalently: if `T_public` is at or after 16:00 ET on day D, the first entry is **D+1's close**,
   not D's.
4. **Never key on `filingDate`.** It is a derived field, wrong by one session on **30.7%–65.7%** of
   Item 4.02 filings (§7.2) and late by one session on a further 11.4%.
5. **Never key on `reportDate`.** It is the event date, not the disclosure date, and it precedes
   `filingDate` on 73% of these filings.
6. For the *pre-announcement* half of the problem, note that the SEC's own methodological choice in
   the Treasury study is instructive: *"The window does include the day after because announcements
   are often made after market close, so reactions are recorded in prices the following trading
   day."* A government study of exactly this population built its event window around this fact.

**And the honest caveat on all of it (§3.5):** even a perfectly-timed `acceptanceDateTime` rule is
trading the *second* publication for most codes. Ben-Rephael et al. show the price has largely
adjusted during the pre-filing gap.

### 7.4 A THIRD DEFECT, BEYOND THE TWO THE PROGRAMME ALREADY KNOWS ABOUT:
### `acceptanceDateTime`'s timezone is inconsistent

**This is the most consequential thing I found, and it is not one of the two bugs I was told about.**

The submissions-JSON field is formatted `2025-07-09T01:18:13.000Z`. The trailing `Z` asserts UTC.
**On some records that is true and on others the value is already Eastern Time.**

**Evidence 1 — direct comparison against EDGAR's own rendering (60 filings).** EDGAR's filing-index
page and the submission's SGML `<ACCEPTANCE-DATETIME>` both display the accepted time in ET, and I
confirmed on six spot-checks that they agree with each other exactly. Comparing the raw JSON string
against that ET value on 60 randomly-sampled Item 4.02 filings:

```
offset (raw JSON string minus EDGAR ET):   0h -> 35 filings (58%)  ... the Z is a lie; value is ET
                                           4h -> 11 filings        ... genuine UTC (EDT)
                                           5h -> 14 filings (42% combined) ... genuine UTC (EST)
```

The two groups are interleaved. **The same filer agent produces both on the same day** — e.g. on
2021-11-17, accessions `0001104659-21-140528` (UTC) and `0001104659-21-140633` (ET). So it is not the
agent, not the year, and not a clean cutover.

**Evidence 2 — `filingDate` arbitrates it independently, without touching the index page.** The SEC
rule (§7.1) says ≤17:30 ET gets that day's filing date and later gets the next business day's. So
for each record I can ask which reading is consistent with the `filingDate` EDGAR actually assigned.
Over all 577 filings: **196 (34.0%) are consistent ONLY with the UTC reading; 29 (5.0%) are
consistent ONLY with the ET reading**; 351 (60.8%) fit either. **Two disjoint non-empty sets — the
field cannot be one convention.** Worked examples:

```
0001104659-21-142117  raw "2021-11-19 21:50:45Z"  filingDate 2021-11-22 (Mon)
   as ET  -> 21:50 Fri, after 17:30 -> next business day = Mon 11-22  MATCHES
   as UTC -> 16:50 Fri, before 17:30 -> Fri 11-19                     CONTRADICTED  => value is ET

0001193125-21-331297  raw "2021-11-16 21:36:21Z"  filingDate 2021-11-16
   as ET  -> 21:36, after 17:30 -> next business day = 11-17          CONTRADICTED
   as UTC -> 16:36, before 17:30 -> 11-16                             MATCHES      => value is UTC
```

**Evidence 3 — the impossible-hours test.** Reading every record as UTC puts **38 of 577 (6.6%)
Item 4.02 filings at 01:00–05:00 ET**, outside EDGAR's stated 06:00–22:00 ET operating hours.

**Which source is authoritative: settled.** Applying the 17:30 rule to the EDGAR index/SGML time,
it reproduces the observed `filingDate` on **60 of 60** filings. Applying it to the raw JSON string
read as ET reproduces it on only **41 of 60 (68.3%)**. **`<ACCEPTANCE-DATETIME>` from the SGML header
is the field to use.**

**Operational consequence, stated as a requirement rather than a caveat.** A 4–5 hour error moves a
filing across the 16:00 close and **re-creates exactly the look-ahead the repair is meant to
eliminate** — and it does so on a minority of records, which is the worst case, because the bug will
not show up as an obvious break. Either (i) pull `<ACCEPTANCE-DATETIME>` per filing (one extra HTTP
request each, cacheable forever since it never changes), or (ii) implement the arbitration above and
take the conservative branch where both readings fit. **Do not simply parse the `Z`.**

Two honest qualifications on my own arbitration: the 65.7% upper bound in §7.2 is *deliberately*
biased late and is a bound, not an estimate; and my business-day helper does not enumerate federal
holidays, which is why one record fits neither reading.

---

## 8. WHAT I COULD NOT VERIFY, STATED PLAINLY

1. **WHY `acceptanceDateTime`'s timezone is inconsistent.** I established *that* it is (§7.4) three
   independent ways, and I established which source is authoritative (60/60). I did **not** find the
   rule that separates ET-stamped from UTC-stamped records — it is not the filer agent, not the
   year, and not a clean cutover date. It may be an artefact of how EDGAR back-filled the JSON API.
   **The practical answer does not depend on knowing why**, but a runner that assumes a pattern I
   failed to find would be building on sand.
2. **My 60-filing timezone sample is small and is Item 4.02 only.** The 58/42 ET/UTC split should not
   be assumed to hold for other item codes, other form types, or years outside 2018–2025. The
   577-filing arbitration (34.0% must-be-UTC / 5.0% must-be-ET) is the more robust statement, and it
   only establishes inconsistency, not the mix.
3. **The 30.7%–65.7% look-ahead bracket in §7.2 is a bracket, not an estimate.** The upper end is
   deliberately conservative. The true figure requires the SGML timestamps, which I did not pull for
   all 577.
4. **The count of events passing a $5 close and dollar-volume floor.** I have no price data. §1.3
   gives three bounds and an explicit *estimate* (50–120/yr for Item 4.02) that is **not a
   measurement**. The programme can compute the true figure exactly from its own fixture.
5. **Palmrose, Richardson & Scholz (2004)** — I did not open it. The −9% two-day CAR is taken from
   search summaries and from the Treasury report's citation of it. ScienceDirect is paywalled and I
   did not attempt to bypass it.
6. **Hennes, Leone & Miller (2008)** — snippet only. The −7.29%/−1.57% irregularity/error split is
   unread by me.
7. **Griffin & Lont (2010)** on auditor changes — **WebFetch → ssrn.com: HTTP 403**, and
   **curl → papers.ssrn.com: HTTP 403** for the SSRN delivery URL. Abstract-level only.
8. **Release 33-8732A** (which added Item 5.02(e)) — I did not open the SEC PDF. The 7 November 2006
   effective date and the scope come from a search summary of the SEC release plus law-firm alerts.
   The *consequence* — that 5.02 now covers pay grants — I verified directly from the **current
   Form 8-K text**, which I did read in full.
9. **Lerman & Livnat**: I read the **March 2008 working draft**, not the published 2010 *Review of
   Accounting Studies* version. Every number in this brief attributed to them is from the draft and
   may differ from the published paper. This matters because that table is doing a lot of work here.
10. **Li, Shroff & Venkataraman**: likewise the **April 2004 draft, explicitly marked "Preliminary and
   Incomplete"**, not the 2011 *RAST* publication.
11. **Huson, Malatesta & Parrino**: the **July 2002 draft**, not the published 2004 *JFE* version.
12. **No modern (post-2015) peer-reviewed event study of Item 4.02 returns was located.** The only
    modern replication I found is a vendor's blog post, which is a sales instrument and is not
    evidence for a return. **The entire "what has happened since the mid-2000s" question therefore
    rests on the Treasury study (through 2006) and Lerman & Livnat (through 2006), plus my own
    census showing the population shrank ~80%.** That is a real gap.
13. **I did not verify the 2021 SPAC attribution beyond SIC codes.** 64.8% of 2021's Item 4.02
    filings carry SIC 6770 and the SEC staff statement is dated 12 April 2021; I did not check the
    filings' text or the within-year timing.
14. **The 8-K/A rates in §6.3 are calendar-year ratios**, not matched to the filings they amend.
15. **`items` on 8-K/A**: I assumed an 8-K/A tagged `4.02` amends a `4.02` 8-K. Not verified.
16. **2025 counts** are as EDGAR's full-text index stood at fetch time and may be incomplete.
17. **Item 3.03's +2.84%** (my most interesting incidental finding) rests on a *single* source —
    the Lerman & Livnat draft, 2005–2006, n=967. **One unreplicated cell in one working paper.**
18. **Prompt-injection check.** I read no page containing text addressed to an AI assistant or
    instructing me to take an action. The one page whose content I would flag on other grounds is
    the vendor blog post in §3.1, and I have flagged it as a sales instrument rather than evidence.
    Nothing I fetched asked me to do anything.

---

## APPENDIX — SOURCES BY TYPE AND READ-DEPTH

| source | type | how established |
|---|---|---|
| SEC Release 33-8400 (Fed. Reg. 69 FR 15594, 25 Mar 2004) | [PRIMARY DATA DOC] | **read in full** (local PDF, pypdf, 37pp) |
| SEC Form 8-K, SEC 873 (02-25) | [PRIMARY DATA DOC] | **read in full** (local PDF, pypdf, 40pp) |
| SEC, *Determine the Status of My Filing* (filing-date/dissemination rule) | [PRIMARY DATA DOC] | **read in full** (fetched HTML, verbatim) |
| SEC, EDGAR Release 24.0.2 (5 Feb 2024) | [PRIMARY DATA DOC] | read via WebFetch, verbatim quotes |
| SEC Staff Statement on SPAC warrants, 12 Apr 2021 | [PRIMARY DATA DOC] | read via WebFetch |
| `data.sec.gov/submissions/` + EDGAR index pages | [PRIMARY DATA DOC] | **queried live and cross-checked by hand** |
| EDGAR full-text search `items=` census, 2010–2025 | my own measurement | method + negative control + 3 external cross-checks in §1.1 |
| US Treasury / Scholz (Apr 2008), *Changing Nature … Restatements 1997–2006* | [PRIMARY DATA DOC] | **read in full** (relevant sections, local PDF) |
| Lerman & Livnat, *The New Form 8-K Disclosures*, Mar 2008 draft | [WORKING PAPER] | **read in full** (local PDF) — **not the 2010 published version** |
| Ben-Rephael, Da, Easton & Israelsen, *Who Pays Attention to SEC Form 8-K?*, Aug 2021 | [PEER-REVIEWED] (working version) | **read in full** (local PDF) |
| Huson, Malatesta & Parrino, *Managerial Succession…*, Jul 2002 draft | [WORKING PAPER] | **read in full** (local PDF) — **not the 2004 JFE version** |
| Li, Shroff & Venkataraman, *Goodwill Impairment Loss*, Apr 2004 draft | [WORKING PAPER] | **read in full** (local PDF) — marked "Preliminary and Incomplete" |
| Audit Analytics, *2019 Financial Restatements: A Nineteen Year Comparison* | [PRACTITIONER] | **read in full** (methodology + exec summary, local PDF) |
| Palmrose, Richardson & Scholz (2004) *JAE* 37:59–89 | [PEER-REVIEWED] | **abstract/snippet only** |
| Hennes, Leone & Miller (2008) *TAR* 83:1487–1519 | [PEER-REVIEWED] | **snippet only** |
| Griffin & Lont (2010) *AJPT* 29(2):189–214 | [PEER-REVIEWED] | **abstract only** — SSRN 403 |
| Release 33-8732A (Item 5.02(e)) | [PRIMARY DATA DOC] | **snippet only** |
| commercial 8-K data vendor, Item 4.02 CAR post | [SALES INSTRUMENT] | read via WebFetch summariser — **weaker than a snippet**; cited for counts and crowding only, never for a return |

**Blocks encountered, logged by tool and response:**
- `WebFetch → ssrn.com/abstract=1079243`: HTTP 403.
- `curl → papers.ssrn.com/sol3/Delivery.cfm/...`: HTTP 403 (returned an HTML error page, not a PDF).
- `WebFetch → ecfr.gov/current/title-17/.../section-232.13`: HTTP 302 redirect to
  `unblock.federalregister.gov`, not followed. Regulation S-T Rule 13 was therefore **not** read
  directly; §7.1 rests on the two SEC.gov pages instead.
- `WebFetch → sec.gov/edgar/filer-information/current-edgar-filing-hours-holidays`: HTTP 404
  (page moved; the live equivalent was located and read).
- `curl → sec.gov/Archives/.../0000320193-26-000003-index.htm`: HTTP 503 on one attempt
  (transient; SEC rate limiting).
