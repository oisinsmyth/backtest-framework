# `B4` — Shares outstanding, float, and the split-history gap

**Lane `B4` of Scan-100926 round 2.** Commissioned to settle round 1's `D9`: `A2` named net share
issuance the cheapest non-free survivor, needing *"only a split-adjusted share count"*; `A1` found
**no split history anywhere in XBRL**. Both were right about different halves. This lane decides
whether the route can be rescued.

Campaign contract: [`00-SCHEMA.md`](00-SCHEMA.md). Under [R15](../../RULES.md#r15) **nothing here
closes or admits anything, and nothing is elevated out of `docs/research/`.**

---

## 0. THE ANSWER, FIRST

**The route is rescued, and not by closing the split gap. The split gap CANNOT be closed from free
data — and it does not need to be, because the signal has a split-free formulation that the
literature already states and already ships as code.**

Three findings carry the lane, in descending order of importance.

**`F1` — THE SAME-FILING RATIO. Net share issuance computed as the ratio of two comparative periods
presented in ONE filing is split-immune by construction, and I measured its error rate.** Accounting
rules require every period presented in a filing to be restated onto the current share basis, so the
split factor appears in numerator and denominator and cancels. **Measured on 865 paired observations
across 161 CIKs: where a level restatement intervened (n=58), 32.8% of same-filing ratios agreed
EXACTLY, p95 deviation 0.50%, and ZERO of 58 showed a split-sized error. The naive cross-filing
construction was contaminated on 11 of 11 known split events in the same names, by factors of 0.099
to 1,049.** §5, §6.

**`F2` — I FOUND A SPLIT-RATIO TAG IN XBRL, WHICH CONTRADICTS `A1`, AND IT IS NOT A SPLIT TABLE.**
`us-gaap:StockholdersEquityNoteStockSplitConversionRatio1` exists in the company-concept API and
returns correct ratios for Apple (7, 4), NVIDIA (4, 10), Tesla (5, 3), GE (0.125), Citigroup (0.1),
Chesapeake (0.005), Rite Aid (0.05) — **2,280 distinct CIKs carry it 2009–2026.** But measured: its
date is sometimes the board-approval date, sometimes a whole month, sometimes the fiscal year end;
the same period carries **two conflicting ratios** for Tesla; **30% of its non-unit ratios are dated
before the issuer was a reporting registrant** (pre-IPO reverse splits and preferred-conversion
ratios, not splits of a traded security); it is tagged with a `Range=Minimum/Maximum` axis so the API
can hand you an **authorised bound rather than an executed ratio**; and it arrives **44 to 294 days
after the event**. **A conflict with `A1` recorded, not adjudicated — and a route rejected on its
own measured properties rather than on absence.** §4.

**`F3` — BOTH FREE SPLIT DETECTORS FAIL, AND I CAN NAME THE FABRICATION.** Restatement-based and
jump-based detection disagree with the tag on roughly half of all events in both directions, and the
jump detector fabricates a corporate action in a mega-cap: **HP Inc's 10-K/A tagged its cover-page
share count as 165,228,387 while the same document's cover page reads, verbatim, "The number of
shares of HP Inc. common stock outstanding as of November 30, 2017 was 1,645,228,387 shares."** A
dropped digit. A jump detector reads that as a 1-for-10 reverse split in November 2017 and a 10-for-1
forward split in January 2018. HP never split. §7.

**And the lane's own commissioning premise was wrong.** The brief supposed the source literature
"will not state" the split-free formulation "because it assumes split-adjusted vendor data."
**Daniel & Titman (2006) state it in so many words**, and Chen–Zimmermann's open-source code
implements it with no share count at all. §8.

| sub-question | verdict |
|---|---|
| **1. Free share-count series?** | **YES.** `dei:EntityCommonStockSharesOutstanding` + a `us-gaap` WASO fallback chain reaches **91.0% of XBRL filers**, dead names fully retained on CIK, **median as-of→filed lag 5 days**. §2, §3 |
| **2. Split detectable without a split table?** | **NO, by any of the four candidate routes.** §4, §7 |
| **3. Measured error rate of the inference?** | **Measured, and disqualifying for every inference route. Zero inference is needed for `F1`.** §6, §7 |
| **4. What else a panel unlocks** | Buyback dollars yes, buyback **quantities** no (~10–25% coverage); float is annual and lagged up to 9 months; insider fraction **not in XBRL at all**. §9 |
| **5. The honest alternative** | **EXISTS, is the literature's own construction, and is the lane's recommendation.** §5, §8 |

**Bar met on the second horn AND the first.** `D9` closes: the split gap is not closable from free
data, and the signal does not need it.

---

## 1. Method, and the negative controls

**All live probes single-threaded through one paced fetcher**
(`B4_fetch.py`, `MIN_GAP = 0.22 s`, ~4.5 req/s, well under SEC's documented 10/s), contact string
`research@backtest-framework.org` in the `User-Agent` on every call.
**Total: 1,110 requests, 138.3 MB, 816×200 and 294×404, and ZERO 429/403/503.** Every response cached
to disk as raw bytes and parsed from bytes, never from status.

**Negative controls, reported beside every count, per the campaign rule.** Twelve in total, all clean:

| control | endpoint | result |
|---|---|---|
| fabricated tag `ZZZNotATagB4NegativeControl` | `companyconcept`, 10 CIKs | **404**, 349-byte XML `<Error><Code>NoSuchKey` |
| plausible-sounding fake `SharesOutstandingSplitAdjustedB4Control` | `companyconcept`, 10 CIKs | **404**, 361 bytes |
| `dei/TradingSymbol` (prior lane's known genuine 404) | `companyconcept`, 10 CIKs | **404**, 331 bytes ✓ reproduces `A1` |
| pre-XBRL frame period `CY1995Q1I` | `frames` | **404** |
| future frame period `CY2031Q1I` | `frames` | **404** |
| wrong unit (`USD` on a `shares` concept) | `frames` | **404** — `A1`'s own trap, reproduced |
| wrong taxonomy (`us-gaap` on a `dei` concept) | `frames` | **404** |
| duration period on an instant concept (`CY2020Q1`) | `frames` | **404** |
| fabricated tag in FSDS `num.txt` | `2025q2.zip` | **0 rows** |
| non-split names for the split tag (Sears, BBBY, SVB) | `companyconcept` | **404** — correct: they had no splits |
| `TreasuryStockCommonShares` (tag does not exist) | `frames` ×3 periods | **404** ×3 |
| pre-listing split ratios must precede first cover page | cross-check | fired on **28 of 91** ✓ |

**A TWELFTH HTTP-200 FLAVOUR, NEW, AND DIRECTLY IN THE PATH OF THIS LANE.** `A1`'s catalogue has
"valid JSON with no data key". This is worse:

```
GET https://data.sec.gov/api/xbrl/companyconcept/CIK0000895126/dei/EntityCommonStockSharesOutstanding.json
HTTP 200, 650 bytes:
{"cik":895126,"taxonomy":"dei","tag":"EntityCommonStockSharesOutstanding", ... ,
 "entityName":"EXPAND ENERGY CORPORATION","units":{"shares":{}}}
```

**HTTP 200. Valid JSON. `units` key present. The correct unit key `shares` present. Zero facts.** A
check on status passes, a check on `"units" in obj` passes, a check on `obj["units"]` being non-empty
passes, and only `len(obj["units"]["shares"]) > 0` catches it. Measured on **Chesapeake/Expand Energy,
Chubb and Ford** — three large, currently-listed issuers. A harvester that counts filled series would
write them as genuine zeroes. `[MEASURED IN BRIEF]`

**A THIRTEENTH, which bit me and which I report because it inverts a coverage number by a factor of
two.** A single `frames` instant bucket (`CY2025Q4I`) returned the cover-page count for only **2,186
of 6,139** Assets-filers — 35.6%. That is not coverage; it is the calendar misalignment `A1` warned
about. A 10-K filed in February 2026 carries a **February 2026** cover date, which lands in
`CY2026Q1I`. Taking the **union over four consecutive quarters** gives the true figure: **81.4%**.
**A single-frame coverage census is wrong by more than a factor of two, in the pessimistic
direction.** Both numbers are reported in §2 so neither is hidden.

**Defects found in the data, reported whether or not they matter to the route:**

- **21 non-positive share-count facts** in the 161-CIK sample, including `val: 0` in 10-Ks and
  **`val: -0.01` shares** (`accn 0001121781-14-000051`, FY2013 10-K, filed 2014-03-18), and one
  `-3,829,975,800` that crashed my first detector pass. **A negative weighted-average share count
  passes SEC validation and sits in the API.**
- **10 of 2,890 cover-page observations (0.35%) have a NEGATIVE as-of→filed lag** — an as-of date
  after the filing date, which is impossible.
- `companyfacts`/`companyconcept` **shows only the CURRENT entity name**, confirmed: CIK 895126
  returns `"EXPAND ENERGY CORPORATION"`, CIK 1137789 returns `"Seagate Technology Holdings plc"`,
  CIK 1754301 returns `"Fox Corp"`. **Three of my own hand-written labels were wrong and the API
  corrected them.** Never assume a CIK's identity; read it back.

---

## 2. Sub-question 1 — what free sources carry a share-count time series

### 2.1 The tags that exist, measured per issuer

`[PRIMARY DATA DOC]` `[MEASURED IN BRIEF]` — `https://data.sec.gov/api/xbrl/companyconcept/CIK{10-digit}/{taxonomy}/{Tag}.json`, 10 issuers × 12 tags = 120 calls.

| tag | what it is | earliest seen | frequency | notes |
|---|---|---|---|---|
| **`dei:EntityCommonStockSharesOutstanding`** | cover-page count, **an instant at the COVER DATE** | **2009-06-27** (Apple) | ~4/yr | the best-dated series in the whole product |
| `dei:EntityPublicFloat` | cover-page float in **dollars** | 2008-06-30 | **1/yr** | §9 |
| `us-gaap:CommonStockSharesOutstanding` | balance-sheet / equity-note count at period end | 2008-09-27 | ~4/yr | thinner, and **dies on multi-class** |
| `us-gaap:CommonStockSharesIssued` | issued incl. treasury | 2008-09-27 | ~4/yr | 404 for Sears entirely |
| **`us-gaap:WeightedAverageNumberOfSharesOutstandingBasic`** | income-statement denominator | **2007-09-29** | **many per filing** (Q, YTD and prior-year comparatives) | **the route's raw material**, §5 |
| `us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding` | diluted version | 2007-09-29 | same | |
| `us-gaap:WeightedAverageNumberOfShareOutstandingBasicAndDiluted` | combined, used by loss-makers | 2012-12-31 | thin | **3/20 multi-class, 1/6,139 in a CY2025 frame** — a near-dead tag |
| `us-gaap:StockholdersEquityNoteStockSplitConversionRatio1` | the split ratio | 2010 | event | §4 |
| `us-gaap:StockholdersEquityNoteStockSplitConversionRatio` | **older spelling, era-dependent** | 2011 (Citi) | event | **0 rows in FSDS 2025q2** — obsolete |

**Two spellings of the split tag, and the choice is era-dependent.** Citigroup's 1-for-10 reverse
split appears only under the **non-`1`** spelling (`accn 0001047469-12-010096`, filed 2012-11-06);
every post-2014 issuer I probed uses the `1` spelling. **A single-tag query misses an era.**

### 2.2 Coverage, the honest number and the artefact beside it

`[MEASURED IN BRIEF]` — `https://data.sec.gov/api/xbrl/frames/{taxo}/{Tag}/{uom}/{period}.json`

**Coverage over time of the cover-page count** (instant frames, entity counts):

| period | entities | | period | entities |
|---|---|---|---|---|
| `CY2009Q1I` | **29** | | `CY2016Q1I` | 5,791 |
| `CY2009Q3I` | 444 | | `CY2018Q1I` | 5,263 |
| `CY2010Q1I` | 501 | | `CY2020Q1I` | 4,774 |
| `CY2010Q3I` | 1,309 | | `CY2022Q1I` | 5,276 |
| `CY2011Q1I` | **1,600** | | `CY2024Q1I` | 4,960 |
| **`CY2011Q3I`** | **6,716** ← the phase-in cliff | | `CY2026Q1I` | 4,611 |
| `CY2012Q1I` | 7,016 | | | |

**The cliff is exactly where `A1` put it: `2011q3`.** For the programme's window, **2010-01-04 →
mid-2011 has a cover-page share count for only 501–1,600 issuers**, against ~7,000 afterwards. That
is ~1.5 years of the 16.6-year window, and it is large-accelerated-filers only. **The share-count
panel inherits the same 2011q3 floor as the rest of XBRL — no better, no worse.**

**The clean cross-sectional coverage number, union over four consecutive quarters**
(`CY2025Q3I` ∪ `CY2025Q4I` ∪ `CY2026Q1I` ∪ `CY2026Q2I`), against `us-gaap:Assets` filers as the
denominator:

| series | CIKs | % of 6,532 Assets-filers |
|---|---|---|
| `dei:EntityCommonStockSharesOutstanding` | 5,320 | **81.4%** |
| `us-gaap:CommonStockSharesOutstanding` | 4,750 | 72.7% |
| any quarterly WASO tag, 2025–2026 | 5,296 | 81.1% |
| **cover-page count OR any WASO** | **5,944** | **91.0%** |
| **no share count of any kind** | **507** | **7.8%** |

**And the single-bucket artefact, reported beside it:** the same census on `CY2025Q4I` alone gives
**35.6%** for the cover-page count and 20.1% missing on `CY2026Q1I` alone. **The fallback chain is
load-bearing: neither tag alone reaches 82%, and together they reach 91%.**

### 2.3 Lag and spacing — the one place this series is genuinely good

`[MEASURED IN BRIEF]` — 80 randomly drawn CIKs (seed 20260910, drawn from the `CY2015Q1I` frame),
**2,890 cover-page observations**:

| quantity | p05 | p25 | p50 | p75 | p90 | p95 | p99 | max |
|---|---|---|---|---|---|---|---|---|
| **as-of (`end`) → `filed`, days** | 0 | — | **5** | — | 26 | — | 109 | 637 |
| gap between consecutive as-of dates, days | 38 | 82 | **91** | 99 | — | 147 | — | 3,092 |

- observations per CIK: min 4, **p50 30**, p90 63, max 69
- **1.4% of gaps exceed 200 days** — a missed quarter or worse
- **10 observations (0.35%) have a negative lag**, which is impossible

**A 5-day median as-of→filed lag is far tighter than any income-statement item**, because the
cover-page count is stated as of a date a few days before the filing rather than as of the fiscal
period end. `A1` flagged the cover-date/period-end mismatch as a hazard for a fundamentals panel;
**for a share count it is an advantage, and it is exactly the date you need** to pair the count with
an as-traded close (§5.3).

### 2.4 Dead-name retention — confirmed, and the binding gap is the ticker, as `A1` said

`[MEASURED IN BRIEF]`

| issuer | CIK | last `dei:ECSSO` as-of | last `filed` | `n` cover-page facts | WASO-basic facts |
|---|---|---|---|---|---|
| **Sears Holdings** | 1310067 | 2018-12-07 | **2018-12-13** | 34 | 96 |
| **Bed Bath & Beyond** | 886158 | 2023-05-09 | **2023-06-14** | 57 | 184 |
| **SVB Financial** | 719739 | 2023-01-31 | **2023-02-24** | 51 | 154 |
| Rite Aid | 84129 | 2024-07-22 | 2024-07-25 | 56 | 172 |

**All three named dead issuers are fully retained, keyed on CIK, right up to the last filing before
deregistration.** Sears' series starts 2010-08-13 — late, consistent with the phase-in — and BBBY's
starts **2009-08-29**. Sears' `us-gaap:CommonStockSharesIssued` is a **genuine 404**; its cover-page
and WASO series are intact. **`A1`'s finding holds: the data is there, the ticker is the gap.**

### 2.5 The Financial Statement Data Sets — a DIFFERENT product, and better for one thing

`[PRIMARY DATA DOC]` `[MEASURED IN BRIEF]` —
`https://www.sec.gov/files/dera/data/financial-statement-data-sets/2025q2.zip`, **HTTP 200,
78,973,768 bytes**, `PK\x03\x04` magic confirmed, members `sub.txt` 2.1 MB, `pre.txt` 93.7 MB,
**`num.txt` 498.2 MB**, `tag.txt` 18.9 MB. **`num.txt` header is the TEN-field version with
`segments`** — confirming `A1`'s documentation conflict, measured independently in a different
quarter.

| tag | rows | filings | non-dimensional rows | **DIMENSIONED rows** |
|---|---|---|---|---|
| `EntityCommonStockSharesOutstanding` | **3** | **2** | 2 | 1 |
| `EntityPublicFloat` | **0** | 0 | 0 | 0 |
| `CommonStockSharesOutstanding` | 25,960 | **5,882** | 10,090 | **15,870** |
| `CommonStockSharesIssued` | 19,617 | 5,953 | 10,365 | 9,252 |
| `WeightedAverageNumberOfSharesOutstandingBasic` | 15,279 | **5,451** | 12,209 | **3,070** |
| `WeightedAverageNumberOfDilutedSharesOutstanding` | 14,971 | 5,367 | 12,103 | 2,868 |
| `StockholdersEquityNoteStockSplitConversionRatio1` | 101 | 44 | 63 | 38 |
| `StockholdersEquityNoteStockSplitConversionRatio` | **0** | 0 | 0 | 0 |
| **`ZZZNotATagB4NegativeControl`** | **0** | **0** | **0** | **0** ✓ |

Two consequences, opposite in sign.

**Against FSDS: it does NOT carry the cover-page count.** 3 rows in 7,009 submissions. The documented
scope is primary financial statements, and the cover page is not one. **`dei:EntityPublicFloat` is
likewise absent.** So the best-dated and the float series are **API-only**.

**For FSDS: its `segments` field RECOVERS the class-dimensioned counts the API drops.** Verbatim
examples:

```
CommonStockSharesOutstanding   adsh=0000003570-25-000049  ddate=20241231  value=224000000  segments='EquityComponents=CommonStock;'
CommonStockSharesIssued        adsh=0000002488-25-000047  ddate=20241231  value=1622000000 segments='ClassOfStock=CommonStock;'
WASO-basic                     adsh=0000016918-25-000022  ddate=20240229  value=183307000  segments='ClassOfStock=CommonClassA;'
WASO-basic                     adsh=0000016918-25-000022  ddate=20230228  value=23206000   segments='ClassOfStock=CommonClassB;'
```

**61% of `CommonStockSharesOutstanding` rows and 20% of WASO-basic rows are dimensioned** — and those
are precisely the rows the non-dimensional API discards (§3). **FSDS is the only free product that
reaches the multi-class names.** It also carries `adsh` + `ddate` + `qtrs` directly, so **the
same-filing comparative structure of §5 is computable from `num.txt` alone** — one 5.26 GB download
rather than ~6,000 API documents, **as filed** rather than latest-vintage, which is what
point-in-time wants. Its cost is `A1`'s measured lag: **~50 days after quarter end plus up to one
quarter of queueing.**

FSDS `sub.txt` form tally for `2025q2`, reproducing `A1`'s conflict in a third quarter: `10-Q` 5,224,
`10-K` 624, **`20-F` 538**, `6-K` 86, `S-1/A` 83, `POS AM` 81, `10-K/A` 80, `S-1` 57, `S-4/A` 41.
**Filter on `form` explicitly or a registration statement's financials enter the panel.**

---

## 3. THE COVERAGE FINDING THE LANE WAS NOT COMMISSIONED TO FIND — multi-class issuers

**The cover-page share count silently loses every multi-class issuer, in one of three different
shapes, and the loss is GROWING.**

`[MEASURED IN BRIEF]` — `us-gaap:Assets` filers in a frame, minus those with
`dei:EntityCommonStockSharesOutstanding` in the same frame:

| frame | Assets filers | no cover-page count | % | **no cover-page count AND no `us-gaap:CSSO`** |
|---|---|---|---|---|
| `CY2012Q1I` | 7,606 | 924 | 12.1% | 444 |
| `CY2018Q1I` | 5,946 | 911 | 15.3% | 484 |
| `CY2024Q1I` | 5,849 | 1,067 | 18.2% | 694 |
| **`CY2026Q1I`** | 5,544 | **1,112** | **20.1%** | **824** |

*(Single-bucket figures, so read them as a trend rather than as a level — §2.2.)*

**The twenty largest affected issuers by Assets in `CY2026Q1I`, verbatim from the frame:**

| CIK | Assets (USD) | entityName | has `us-gaap:CSSO`? |
|---|---|---|---|
| 1067983 | 1,252,271,000,000 | BERKSHIRE HATHAWAY INC | **NEITHER TAG** |
| 1652044 | 703,919,000,000 | Alphabet Inc. | CSSO yes |
| 1326801 | 395,250,000,000 | Meta Platforms, Inc. | **NEITHER TAG** |
| 37996 | 282,434,000,000 | Ford Motor Co | **NEITHER TAG** |
| 1166691 | 260,002,000,000 | COMCAST CORPORATION | **NEITHER TAG** |
| 798941 | 235,959,000,000 | FIRST CITIZENS BANCSHARES INC | **NEITHER TAG** |
| 1381197 | 218,749,000,000 | INTERACTIVE BROKERS GROUP, INC. | **NEITHER TAG** |
| 1156375 | 201,993,500,000 | CME GROUP INC. | **NEITHER TAG** |
| 1403161 | 95,049,000,000 | VISA INC. | **NEITHER TAG** |
| 1090727 | 71,809,000,000 | United Parcel Service, Inc. | **NEITHER TAG** |
| 1467373 | 67,064,216,000 | Accenture plc | **NEITHER TAG** |

**Every one of these is a dual- or multi-class issuer.** Berkshire A/B, Alphabet A/B/C, Meta A/B,
Ford common/Class B, Comcast A/B, Visa A/B/C, UPS A/B, Accenture A/X, CME A/B, Charter A/B. The
mechanism is exactly the one `A1` identified in §1.2 of its brief — **the XBRL APIs carry only
non-dimensional facts** — applied to the cover page, where a multi-class issuer must tag each class
on a `ClassOfStock` axis. The API then returns **404** (Alphabet, Meta, News Corp, Under Armour,
First Citizens, Dell), **200 with an empty fact list** (Expand Energy, Chubb, Ford), or **a series
that stops dead the quarter the filer moved to dimensioned tagging** (Berkshire: 7 facts,
2009-10-29 → **2011-04-29**, then nothing for 15 years; Mastercard: 4 facts ending 2010-10-27;
21st Century Fox: 2 facts ending 2010-01-29).

`company_tickers.json` `[PRIMARY DATA DOC]` `[MEASURED IN BRIEF]`: **10,407 ticker rows, 8,013
distinct CIKs, 1,441 CIKs with more than one ticker = 18.0%** — the same order of magnitude, from an
independent file. *(That file is current-only and carries no dead issuers, which is `A1`'s ticker
gap.)*

### 3.1 And this is the second reason to prefer the WASO route

`[MEASURED IN BRIEF]` — the same 20 issuers, every candidate tag:

| tag | survives on how many of the 20? |
|---|---|
| `dei:EntityCommonStockSharesOutstanding` | 12/20 — and 8 of those 12 stop before 2012 |
| `us-gaap:CommonStockSharesOutstanding` | **5/20** |
| **`us-gaap:WeightedAverageNumberOfSharesOutstandingBasic`** | **16/20** |
| `us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding` | 15/20 |
| `WeightedAverageNumberOfShareOutstandingBasicAndDiluted` | 3/20 |

Meta 2010→2026 (186 facts), Comcast 2008→2026 (211), UPS (212), Accenture (357), CME (229),
Mastercard (305), Under Armour (190), Charter (183), First Citizens (202) — **all have a full
income-statement share-count series where their cover-page count is absent or frozen in 2010.**
Because basic EPS is usually reported as one combined denominator on the face of the income
statement. **Four still fail on every tag: Ford, Chubb, Expand Energy, Visa.**

**So the route that §5 recommends is also the route with the better multi-class coverage.** That was
not designed; it fell out.

---

## 4. Sub-question 2, route (d) — THE EXPLICIT SPLIT TAG. `A1` MISSED IT, AND IT STILL FAILS

### 4.1 The conflict with `A1`, recorded not adjudicated

`A1` §6.2.3 states: *"No split adjustment, anywhere. … There is no split history in any XBRL
product."* `[quoted from R1-01, read in full]`

**That is not correct as stated.** `[MEASURED IN BRIEF]`
`https://data.sec.gov/api/xbrl/companyconcept/CIK{...}/us-gaap/StockholdersEquityNoteStockSplitConversionRatio1.json`

| issuer | CIK | tagged ratios | first `filed` | event date | **latency** |
|---|---|---|---|---|---|
| Apple | 320193 | **7** @ 2014-06-06; **4** @ 2020-08-28 | 2014-07-23 | split eff. 2014-06-09 | **44 d** |
| NVIDIA | 1045810 | **4** @ 2021-06-03 *and* @ 2021-07-19; **10** @ May *and* June 2024 | 2021-08-20 | eff. 2021-07-20 | 31 d |
| Tesla | 1318605 | **5** @ 2020-08-10; **3** @ 2022-08-05 | 2020-10-26 | eff. 2020-08-31 | 56 d |
| General Electric | 40545 | **0.125** @ 2021-07-30 | 2021-10-26 | eff. 2021-08-02 | **85 d** |
| Citigroup | 831001 | **0.1** @ 2011-05-06 (*old spelling*) | **2012-11-06** | eff. 2011-05-09 | **547 d** |
| Rite Aid | 84129 | **0.05** @ 2019-04-18 *and* @ 2019-04-22; plus a **`val=1`** | 2019-10-03 | eff. 2019-04-18 | 168 d |
| Chesapeake | 895126 | **0.005** @ 2020-04-14 | **2021-02-02** | eff. 2020-04-14 | **294 d** |
| Sears, BBBY, SVB | — | **404** ✓ | — | **no splits** | ✓ |

Frames census across 2009–2026, both spellings, all instant/duration/annual periods (324 calls, 173
non-empty): **2,280 distinct CIKs**, 2–78 issuers per quarter-instant. **This is a real, substantial,
free artefact and `A1` did not find it.** I would weight my measurement over `A1`'s statement,
because mine is an endpoint and a byte count; and I note `A1`'s statement is **operationally right
for the wrong reason** — the tag exists and is still unusable, for five separately measured reasons.

### 4.2 Why it still fails — five measured defects

**(i) The date is not the ex-date, and sometimes is not a date.** NVIDIA's 2021 split is tagged at
both **2021-06-03** (board approval) and **2021-07-19**, with the ex-date 2021-07-20; its 2024 split
is tagged as a **duration** `start=2024-05-01 end=2024-05-31` and again `start=2024-06-01
end=2024-06-30`, value 10 both times, against an actual ex-date of 2024-06-10. **A month-long range
is not an ex-date.** Tesla's tag is used as a whole-fiscal-year duration in 20 of its 22 facts.

**(ii) The same period carries contradictory ratios.** Tesla, CIK 1318605, `start=2020-01-01
end=2020-12-31`: **`val=5`** in the FY2020 10-K (`accn 0001564590-21-004599`) and **`val=3`** in the
FY2022 10-K (`accn 0000950170-23-001409`). Same tag, same period, two values, no flag. A
"latest-filed wins" rule returns 3 for a 2020 period in which the 3-for-1 had not happened.

**(iii) 28 of 91 — 30.8% — of its non-unit ratios are not splits of a traded security.**
`[MEASURED IN BRIEF]` On the 59-CIK tagged sample, comparing each ratio's date with the issuer's
**first cover-page observation**:

| | count |
|---|---|
| ratio dated **after** first cover-page observation | 63 |
| **ratio dated BEFORE first cover-page observation** | **28 (30%)** |
| issuer has no cover-page series at all | 5 |
| **ratio is exactly 1** (not a split) | 3 |

The pre-listing ones are unambiguous: **Duckhorn Portfolio 1,017,134.6**, **WideOpenWest 66,498.8**,
**Yiren Digital 10,000**, **State National 0.0014** — LLC-unit and up-C reorganisation exchange
ratios — plus pre-IPO reverse splits (Avalara 0.5 dated 2018-05-10 against a first cover page of
2018-07-31; Sana 0.25; Acceleron 0.25; Esperion 0.1431; Tarsus 0.1346; Metacrine 0.196078). **The tag
is a grab-bag of splits, pre-IPO reverse splits, preferred-conversion ratios, up-C exchange ratios,
de-SPAC recapitalisation ratios and ratios of one.**

**(iv) It can carry an AUTHORISED RANGE rather than an executed ratio — and the API strips the axis
that tells you so.** From FSDS `2025q2` `num.txt`, verbatim:

```
tag=StockholdersEquityNoteStockSplitConversionRatio1  adsh=0000022701-25-000005  ddate=20231231  value=0.5000
   segments='Range=Minimum;SubsidiarySaleOfStock=June2024ReverseStockSplit;'
tag=StockholdersEquityNoteStockSplitConversionRatio1  adsh=0000022701-25-000002  ddate=20240731  value=0.0050
   segments='Range=Maximum;SubsidiarySaleOfStock=October2024ReverseStockSplit;'
tag=StockholdersEquityNoteStockSplitConversionRatio1  adsh=0000022701-25-000005  ddate=20250331  value=0.0050
   segments='Range=Maximum;SubsequentEventType=SubsequentEvent;SubsidiarySaleOfStock=April2025ReverseStockSplit;'
```

**38 of 101 rows are dimensioned.** Those dimensions distinguish a minimum from a maximum, and one
proposed split from another. **The company-concept API drops dimensions, so it hands you one number
from an authorised range with nothing to say it is a bound.** 0.5 and 0.005 differ by a factor of
100. **This is the "field whose name lies" hazard, at its worst.**

**(v) The latency is 31–547 days.** A tag that arrives 294 days after a 1-for-200 reverse split
cannot maintain a universe floored on an as-traded `$5` close.

**Route (d): REJECTED on measured properties.** Its one legitimate use is as a *confirming* third
source on an event already located by something else (§10).

---

## 5. SUB-QUESTION 5 FIRST, BECAUSE IT IS THE ANSWER — the split-free formulation

### 5.1 The construction

A split multiplies every share count by `f` at one instant. **US GAAP requires retroactive
restatement of share and per-share amounts for splits and stock dividends, so within a single filing
every period presented is stated on the SAME post-split basis.** Therefore, for two annual periods
`e0` and `e1` both reported in ONE filing:

```
          WASO(e1 | accn A)      f · WASO_true(e1)      WASO_true(e1)
  R_A  =  ------------------  =  -----------------  =  --------------       f CANCELS, EXACTLY
          WASO(e0 | accn A)      f · WASO_true(e0)      WASO_true(e0)
```

**This is not an inference. No split is detected, no ratio is estimated, nothing is snapped to a
simple rational. The split factor is algebraically absent.** §6 measures what is left.

### 5.2 Demonstrated across eight known splits

`[MEASURED IN BRIEF]` — `WeightedAverageNumberOfSharesOutstandingBasic`, annual-duration facts
(330–400 day spans), grouped by `accn`. Full per-filing output in the session cache; the decisive
comparison:

| issuer | event | **SAME-FILING annual ratio** | **CROSS-FILING annual ratio (naive)** |
|---|---|---|---|
| **Apple** | 7:1 2014 | 0.98985 then **0.93952** | **6.57664** ← contaminated |
| **Apple** | 4:1 2020 | 0.93188 then **0.93941** | **3.75763** ← contaminated |
| **NVIDIA** | 4:1 2021 | 1.01314 then **1.01148** | **4.04538** ← contaminated |
| **NVIDIA** | 10:1 2024 | 0.99276 then **0.99453** | **9.94532** ← contaminated |
| **NVIDIA** | *units→millions 2012* | 1.04659 then **1.04950** | **1049.49607** ← contaminated |
| **Tesla** | 5:1 2020 | 1.03986 then **1.05186** | **5.27119** ← contaminated |
| **Tesla** | 3:1 2022 | 1.05754 then **1.05779** | **3.17444** ← contaminated |
| **Amazon** | 20:1 2022 | 1.01119 then **1.00712** | **20.13636** ← contaminated |
| **Walmart** | 3:1 2024 | 0.97553 then **0.98850** | **2.96512** ← contaminated |
| **General Electric** | 1:8 2021 | 1.00275 then **1.00366** | **0.12544** ← contaminated |
| **Citigroup** | 1:10 2011 | 1.01119 then **1.00715** | **0.10112** ← contaminated |
| **Rite Aid** | 1:20 2019 | clean throughout | contaminated |

**Eleven split events, eleven contaminated cross-filing ratios, zero contaminated same-filing
ratios.** And the NVIDIA 2012 row is a bonus: **the same-filing construction is also immune to a
filer changing its reporting scale** (575,177 thousands → 603,646,000 units), which the naive
construction reads as a 1,049-fold issuance.

**The honest counter-example, which is the reason the lane cannot stop here.** Citigroup's
**same-filing** ratios are **2.19704** for 2008→2009 and **2.48749** for 2009→2010. Those are
genuine crisis-era issuance, correctly reported. **A 2.5× share-count increase in one year is not a
split, and no magnitude test can tell the two apart.** §7 makes that quantitative.

### 5.3 And the price-paired variant, for a monthly signal

`Daniel & Titman`'s composite issuance needs no annual filing at all, only a contemporaneous
pairing. **Market capitalisation is split-invariant at every instant**, because a split scales raw
shares up and the raw price down at the same moment. So pair
`dei:EntityCommonStockSharesOutstanding` with the as-traded close **on its own `end` date** — which
§2.3 measured at a **5-day median lag** and which is precisely what that date is for — and the split
never enters. §8 gives the literature's own algebra and the identity that recovers the pure
share-growth version from it.

### 5.4 Availability of the same-filing comparative

`[MEASURED IN BRIEF]` over all 161 CIKs:

| | |
|---|---|
| annual WASO periods present | **1,319** |
| **annual periods with a same-filing prior-year comparative** | **1,154 = 87.5%** |
| CIKs with a WASO-basic series | 143 / 161 |
| **CIKs with ≥1 usable same-filing ratio** | **132 / 161 (82.0%)** |
| CIKs with no WASO-basic series at all | 18 (11.2%) |

**87.5% of annual periods carry the comparative**, and a 10-K normally presents **three** years of
income statement, so a two-year same-filing ratio is directly available and a five-year ratio needs
only two or three chained links rather than five. *(Smaller reporting companies present two years,
so for them a five-year window needs four links — see §11.6.)*

---

## 6. SUB-QUESTION 3 — THE MEASURED ERROR RATE. This is the number the lane exists to produce

**The route needs no ground truth to be measured, which is its best property.** The same annual
period-pair is normally reported in two consecutive 10-Ks. Both are internally split-consistent, so
both must give the same ratio. **Where they disagree, the disagreement IS the error.** Splitting by
whether a level restatement intervened isolates exactly the case the route exists to survive.

`[MEASURED IN BRIEF]` — 161 CIKs, **772 period-pairs reported two or more times** (382 reported once),
**865 consecutive-report comparisons**. Full table at
[`data/B4-same-filing-ratio-error-rate.csv`](../../../data/B4-same-filing-ratio-error-rate.csv).

| | **LEVEL RESTATED between the two reports** (the split / stock-dividend / recast case) | **level unchanged** (control) |
|---|---|---|
| n | **58** | **807** |
| **exactly zero deviation** | **19 (32.8%)** | **792 (98.1%)** |
| p50 \|log dev\| | 9.2e-07 = **0.0001%** | **0** |
| p90 | 1.6e-03 = **0.164%** | 0 |
| **p95** | 5.0e-03 = **0.498%** | 0 |
| p99 | 3.3e-01 = 33.08% | 1.0e-05 = 0.001% |
| max | **33.08%** | 50.42% |
| share > 1% | **3.45% (2 of 58)** | 0.12% (1 of 807) |
| share > 5% | 1.72% (1 of 58) | 0.12% |
| **share > 40% — a SPLIT-SIZED error** | **0.00% — ZERO of 58** | 0.12% (1 of 807) |

**The headline: on a named test set of 58 restatement events — level factors running from 0.001
(a reporting-scale change) through 1-for-10 reverse splits to 20-for-1 forward splits — the
same-filing construction produced NOT ONE split-sized error. The naive construction produced eleven
out of eleven on the same names.**

**What the residual 0.5% is, and it is not a split error.** It is **reporting-precision loss**.
After an 8-for-1 reverse split GE's 8,753,000,000 becomes 1,094,000,000 — four significant figures
instead of five — and the ratio shifts by 5.7e-04. The five largest true-split residuals, named:

| CIK | issuer | period pair | ratio early | ratio late | level factor | deviation |
|---|---|---|---|---|---|---|
| 1318605 | Tesla | 2018→2019 | 1.03509 | 1.03986 | **4.9883** | **0.460%** |
| 800240 | The ODP Corporation | 2018→2019 | 0.985533 | 0.981818 | 0.09946 | 0.378% |
| 1045810 | NVIDIA | 2020→2021 | 1.01314 | 1.01148 | 4.00493 | 0.164% |
| 1018724 | Amazon | 2020→2021 | 1.01200 | 1.01119 | 20.010 | 0.080% |
| 40545 | General Electric | 2019→2020 | 1.00332 | 1.00275 | 0.12506 | 0.057% |

Against a cross-sectional share-growth signal whose own interquartile range is **0.98658 to 1.05200**
(§7.2), **a 0.06–0.46% rounding error is two orders of magnitude below the signal** and an order of
magnitude below the interquartile spread.

**And the tail is one micro-cap, named.** Both extremes — the 33.08% restated case and the 50.42%
control case — are **Erin Energy Corp., CIK 1402281** (formerly CAMAC Energy), a serial
reverse-merger shell. One name produces both outliers in 865 comparisons. **This is the false-positive
mechanism of §7.4 appearing in the measurement, as it should.**

**`PaymentsForRepurchaseOfCommonStock` was checked as a non-share control**; it is a dollar amount and
cannot be restated by a split, and it is not part of this statistic.

### 6.1 What I could NOT measure about this route, stated here rather than buried

- **I did not measure the error on period-pairs reported only ONCE (382 of 1,154, 33%).** By
  construction the within-filing consistency cannot be checked there. The route is still
  algebraically split-free for those; what is unmeasured is the *reporting* error, not the split
  error.
- **I did not establish the accounting rule from an authoritative primary source.** The retroactive
  restatement requirement is ASC 260-10-55-12; **the FASB Codification is behind a login and the
  campaign forbids accounts, so I did not read it.** `[UNVERIFIED as to the citation]` **What I did
  do is measure the behaviour directly on 58 events, which is the stronger evidence for the route's
  purpose.** If the principal wants the rule cited, it needs a source I was not permitted to reach.

---

## 7. Sub-question 2, routes (a)–(c) — the detectors, and the fabrication they produce

### 7.1 Three independent detectors, cross-tabulated

- **`T` (tag)** — `StockholdersEquityNoteStockSplitConversionRatio[1]`, §4.
- **`R` (restatement)** — the level restatement of prior-period WASO between two filings. *Strict*
  requires **≥2 prior periods restated by the same factor at the same filing boundary**, since a
  split restates everything prior while an error correction restates one.
- **`J` (jump)** — a discrete jump in `dei:EntityCommonStockSharesOutstanding`, which is a cover-page
  instant and is never restated, so a split appears in it only as a jump.

`[MEASURED IN BRIEF]` — 161 CIKs: 22 hand-picked **NAMED**, 80 **RANDOM** (seed 20260910, from the
`CY2015Q1I` frame — the false-positive census population), 59 **TAGPOS** (seed 20260911, from the
2,280 tag-carrying CIKs). Per-CIK outcomes at
[`data/B4-split-detector-crosstab.csv`](../../../data/B4-split-detector-crosstab.csv).

| cohort | n | `T+R+` | `T+R−` | **`T−R+`** | `T−R−` | no WASO series |
|---|---|---|---|---|---|---|
| NAMED | 22 | 12 | 1 | 2 | 5 | 2 |
| **RANDOM** | 80 | 11 | 2 | **14** | 40 | 13 |
| **TAGPOS** | 59 | 26 | **28** | 0 | 2 | 3 |

**Both detectors miss roughly half of what the other finds.** Among the 56 TAGPOS CIKs with a WASO
series, `R`-strict fires on **26 — 46% recall against the tag.** Among the 67 RANDOM CIKs with a WASO
series, `R` fires on 25 and the tag on 11 — **44% recall for `T` against `R`.** **Fifty per cent
mutual disagreement is not a detector; it is two noisy instruments.**

**Why `R` misses tagged events** (the 28 `T+R−` cases, inspected individually): **26 of 28 show NO
deviation at all** in their WASO series. Their tagged ratios are the pre-listing grab-bag of §4.2(iii)
— Acceleron 0.25, Sana 0.25, Avalara 0.5, Esperion 0.1431, Stonegate 12.86, Avolon 246.55,
WideOpenWest 66,498.8, Duckhorn 1,017,134.6, Hemab 22.0. **The events happened before the security
traded, so no restatement of a reported period was needed. `R` is right and `T` is off-target.**

### 7.2 `J` is catastrophic, and the number is 157

`[MEASURED IN BRIEF]` — threshold `|log r| > 0.20`:

| cohort | CIKs | with ≥1 jump | total jump events | on tag-carrying CIKs | **on CIKs with NO split tag** |
|---|---|---|---|---|---|
| NAMED | 22 | 13 | 24 | 22 | 2 |
| **RANDOM** | 80 | 49 | **221** | 64 | **157** |
| TAGPOS | 59 | 37 | 123 | 121 | 2 |

**157 jump events above 20% on 80 randomly drawn CIKs with no split tag.** Inspected, they are:
genuine micro-cap dilution (TOTALIGENT 10,748,884 → 165,853,304 in two months; KiNRG
3,033,806,158 → 12,132,794,404), **reporting-scale flips** (First Mid Bancshares crosses 1000× four
times in 18 months: 6,031,920 → 6,032,682,000 → 5,932,206 → 5,950,522,000), and outright garbage
(MTR Gaming 28,386,084 → **1,000** shares).

**And `J` cannot recover the ratio even on the cleanest possible case.** Apple's cover-page series
through its two splits, verbatim:

```
2014-04-11 -> 2014-07-11     861,381,000 ->  5,987,867,000   ratio = 6.95147   (true split: 7)
2020-07-17 -> 2020-10-16   4,275,634,000 -> 17,001,802,000   ratio = 3.97644   (true split: 4)
```

**0.69% and 0.59% off, because the two cover dates are three months apart and real buybacks sit in
between.** For a 3-for-2 or 1-for-1.5 split that slack is a material fraction of the gap to the next
candidate ratio. **Route (c): REJECTED.**

### 7.3 THE FABRICATION, NAMED, AND CONFIRMED AGAINST THE PRIMARY DOCUMENT

`[PRIMARY DATA DOC]` `[read in full for the cover page]` — HP Inc, CIK 47217, 10-K/A,
`accn 0000047217-17-000045`, document `hp-103117x10ka.htm` (4,334,047 bytes, fetched and parsed
locally).

**The XBRL value:**
```
dei:EntityCommonStockSharesOutstanding  end=2017-11-30  val=165228387  form=10-K/A  filed=2017-12-15
```
**The same document's own cover page, verbatim:**
> "The aggregate market value of the registrant's common stock held by non-affiliates was
> $31,655,134,100 based on the last sale price of common stock on April 30, 2017. **The number of
> shares of HP Inc. common stock outstanding as of November 30, 2017 was 1,645,228,387 shares.**"

**A dropped digit — 1,645,228,387 tagged as 165,228,387 — in a $30 billion issuer, on a 10-K/A, and
the human-readable document proves the XBRL wrong.** Detector `J` reads the surrounding series
(1,670,254,371 → 165,228,387 → 1,641,373,766) as **a 1-for-10 reverse split on 2017-11-30 followed by
a 10-for-1 forward split on 2018-01-31**. HP has never split. **Under the programme's `$5` as-traded
floor that fabrication is a universe-membership error as well as a return error — exactly the class of
incident the brief said has happened three times.**

**And HP carries a second, independent defect in the same window.** `us-gaap:CommonStockSharesOutstanding`
at instant `end=2017-10-31`:
```
1,650,000,000   10-K/A   filed 2017-12-15
1,712,000,000   10-Q     filed 2018-03-01     <-- same instant, +3.8%
1,650,000,000   10-Q     filed 2018-06-05     <-- and back
1,650,000,000   10-K     filed 2018-12-13
```
**The same tag disagrees with itself about the same instant by 3.8% across vintages, then reverts.**
A "latest-filed wins" rule picks the wrong value for three months.

### 7.4 The false-positive mechanisms of route (a), tallied

Over the RANDOM cohort's `R`-strict events: **19 of 47 are exact powers of 1000** — reporting-scale
changes (Washington Trust 1000.03, XL Group 1000, Jabil 0.001 then 1000, Chicago Bridge & Iron 1000
then 0.001, Limestone Bancorp, Cambium, Global Brokerage, Income Opportunity Realty). **These are
filterable because they are exactly 10³ — but an unfiltered detector fabricates a 1000-for-1 split in
Washington Trust Bancorp.** The remaining 28 are real dilution, **de-SPAC and reverse-merger
recapitalisations** (which DO retroactively recast historical share counts at the exchange ratio and
are therefore indistinguishable from splits by this test — **Lucid Group's recovered factor is exactly
0.1 and it was a de-SPAC, not a split**), IPO-year WASO jumps, and error corrections.

**And the distribution closes the door on thresholding.** The same-filing annual share-count ratio,
n = 2,019 observations:

| p1 | p5 | p25 | p50 | p75 | p95 | p99 | min | max |
|---|---|---|---|---|---|---|---|---|
| 0.87177 | 0.93587 | 0.98658 | **1.00588** | 1.05200 | 1.69885 | **4.79468** | 0.634073 | **330.377** |

**6.49% of genuine annual share-count ratios exceed a 49% change**, reaching **330×** (Daniels
Corporate Advisory 2012→2013). Splits begin at 1.5×. **The genuine-issuance distribution and the
split distribution overlap completely, so no magnitude threshold separates them at any error rate.**
Routes (a) and (c) are not rescuable by tuning.

### 7.5 Route (b) — the ratio test between totals and per-share figures

**Not separately testable as a split detector, and I say so plainly.** `EPS × WASO = NetIncome` holds
*within* a filing by construction, so it is a consistency check, not a split detector — a split scales
EPS down and WASO up inside the same filing and the product is unchanged. Across filings it carries
the same contamination as any cross-filing ratio and adds a second rounded quantity. **It is strictly
worse than route (a) and I did not pursue it further.** `[not measured]`

### 7.6 THE SUCCESSOR-ENTITY DEFECT — tested as instructed, and present, and it defeats BOTH vintage rules

The brief asked me to test for the defect a prior lane found — Assets reading 23.4 bn then 3.4 bn
across vintages with no restatement, because the company became a different company. **For a share
count it is present and it is worse, because it breaks the obvious point-in-time rule.**

`[MEASURED IN BRIEF]` CIK 895126, `us-gaap:CommonStockSharesOutstanding`, every fact, verbatim:

```
end=2009-12-31   val=648,549,000     10-Q   filed 2011-05-10
end=2011-06-30   val=659,108,000     10-Q   filed 2011-08-09
end=2019-02-01   val=717,376,170     10-Q   filed 2019-05-09
end=2019-02-01   val=717,376,170     10-Q   filed 2019-08-06
end=2019-02-01   val=717,376,170     10-Q   filed 2019-11-05
end=2019-02-01   val=717,376,170     10-K   filed 2020-02-27
end=2019-02-01   val=  3,600,000     8-K    filed 2021-02-02     <-- SAME INSTANT, 199x SMALLER
end=2020-04-10   val=1,957,000,000   10-Q   filed 2020-08-10
```

**The same CIK, the same tag, the same instant date 2019-02-01: 717,376,170 and 3,600,000.** The 8-K
filed 2021-02-02 restated the 2019 count onto the post-1-for-200-reverse-split basis. The API keeps
both, flags neither, and **reports the entity as `"EXPAND ENERGY CORPORATION"` throughout** — a name
the company did not hold until 2024, for a period in which its equity was Chesapeake common stock
that Chapter 11 subsequently cancelled.

**The consequence is sharper than the warning.** "Latest filed wins" — the natural point-in-time-safe
rule — returns **3,600,000** for a date **fourteen months before the split**, a 199× error.
"First filed wins" returns the pre-split basis for every date after a split. **There is no vintage
rule that is correct on both sides of a split without knowing the split.** Which is the final
argument for §5: **do not form a level; form a ratio inside one filing.**

Chesapeake is also a coverage disaster in its own right: its cover-page count is the `200-with-empty-
fact-list` of §1, its WASO series is empty, and `CommonStockSharesOutstanding` exists only for
2009–2011 and 2019–2020. **A large, liquid, `$5`+ name for most of the window has no usable
share-count series in the XBRL APIs at all.**

---

## 8. The literature — and the lane's own premise was WRONG

**The commissioning brief hypothesised that the source literature "will not state" the split-free
formulation "because it assumes split-adjusted vendor data". It states it explicitly.**

`[PEER-REVIEWED]` `[read in full for the passage, extracted locally with pypdf 6.16.2 from a PDF I
downloaded myself]` — Daniel & Titman, *"Market Reactions to Tangible and Intangible Information"*,
**Journal of Finance 61(4), 2006, p. 1614**, from `https://www.kentdaniel.net/papers/published/jf_06.pdf`
(332,482 bytes, 39 pages). Verbatim:

> "Note that, based on equations (7) and (9), ι can be written as
> **ι(t − τ, t) = log(N_t / N_{t−τ}) + log(P_t / P_{t−τ}) − r(t − τ, t) = log(ME_t / ME_{t−τ}) −
> r(t − τ, t).**
> That is, ι(t − τ, t) is the part of a firm's growth in market value that is not attributable to
> stock returns. **As such, corporate actions such as splits and stock dividends leave ι
> unchanged.**"

and, on the adjustment factor it replaces:

> "In the latter case, to adjust total sales growth, **splits and stock dividends are not a
> concern**, whereas share-issues, repurchases, and equivalent actions must be taken into account
> using the composite share issuance measure ι(t − τ, t)."

and the definition of the return it uses:

> "where f_s, a price adjustment factor from s − 1 to s, adjusts for splits and rights issues, D_s is
> the value of all cash distributions … **We follow CRSP in this definition. Our f_s is equivalent to
> the CRSP factor to adjust price in period.**"

**`SOFTWARE DOC` `[read in full]` — and the code ships exactly that.** Chen & Zimmermann's
Open Source Asset Pricing repository, `Signals/LegacyStataCode/Predictors/CompEquIss.do` (477 bytes),
verbatim and entire:

```stata
* CompEquIss
use permno time_avail_m ret mve_c using "$pathDataIntermediate/SignalMasterTable", clear
bys permno (time_avail): gen tempIdx = 1 if _n == 1
bys permno (time_avail): replace tempIdx = (1 + ret)*l.tempIdx if _n > 1
gen tempBH = (tempIdx - l60.tempIdx)/l60.tempIdx
gen CompEquIss = log(mve_c/l60.mve_c) - tempBH
```

and `Signals/pyCode/Predictors/CompEquIss.py`, header verbatim:

> `# ABOUTME: Composite equity issuance following Daniel and Titman 2006, Table 3`
> `# ABOUTME: calculates 5 year growth rate of market value minus 5 year stock return`
> `Inputs: - SignalMasterTable.parquet: Monthly signal master table with columns [permno, time_avail_m, ret, mve_c]`

**`CompEquIss` takes only a market capitalisation and a total return. No share count. No split
factor. No `cfacshr`.** The split-free route is not a clever workaround this lane invented; **it is
the literature's published operational definition, and `A2` already reported its post-2005
cost-honest evidence** (`S1`: net equity financing 0.39 %/month, rank 9; `S3`: Net Issuance gross 0.57
→ **net 0.37, *t* 2.43** at 14.4% turnover).

### 8.1 A CONFLICT with `A2`'s quotation, recorded not adjudicated

`A2` quotes `S4`'s definition as *"number of shares is `shrout/cfacshr` to adjust for splits"*. **The
code divides the other way.** `ShareIss1Y.do` and `ShareIss5Y.do`, verbatim:

```stata
gen temp = shrout*cfacshr
gen ShareIss1Y = (l6.temp - l18.temp)/l18.temp       // t-18 -> t-6, matching A2's window
gen ShareIss5Y = (l5.temp - l65.temp)/l65.temp       // 60-month window, 5-month lag
```

**`shrout*cfacshr`, multiplied.** `A2` may be quoting the prose documentation while I am quoting the
code; I weight the code, because it is what produced the published series, and because CRSP's own
convention is adjusted shares `= shrout × cfacshr` against adjusted price `= prc / cfacpr`. **Both
readings are recorded and neither is discarded.** This matters operationally: **with the factor
inverted, a 7-for-1 split becomes a 49-fold error rather than a 1-fold one.**

### 8.2 The code's own look-ahead note, which is directly on this lane's subject

`ShareIss1Y.do` carries this comment, verbatim:

> "Note: The implementation below constructs the share adjustment factor from `facshr` as described in
> Pontiff and Woodgate (2008). **Results are almost identical** and we stick with the simpler
> implementation by using `cfacshr` directly. **Note that the signal does not suffer from look-ahead
> bias despite using `cfacshr`**, see `https://github.com/OpenSourceAP/CrossSection/issues/152#issue-2462197349`"

**Two things the programme should take from it.** First, Pontiff & Woodgate's own event-built factor
and CRSP's cumulative factor give "almost identical" results — so the construction is not sensitive to
which is used. Second, and more important here: **a CUMULATIVE split factor is a forward-looking
object.** `cfacshr` as of today encodes every split up to today, so using it to adjust a historical
level is look-ahead; using it inside a **ratio** is not, because the cumulative base cancels. **That
is the same cancellation as §5, from the opposite direction, and it is why the ratio formulations are
the safe ones.**

### 8.3 Literature I did NOT get, and a caught mis-identification

- **Pontiff & Woodgate (2008) itself: NOT OBTAINED.** Log by tool and response: `urllib` GET
  `https://www2.bc.edu/jeffrey-pontiff/Documents/11_pontiff-woodgate.pdf` → **`URLError: [Errno 11001]
  getaddrinfo failed`** (DNS, not a block). `urllib` GET
  `https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2008.01335.x` → **`HTTP 403
  Forbidden`**. **`[NOT OBTAINED]`** — nothing in this brief rests on it beyond the OSAP code comment
  that names it.
- **A CAUGHT MIS-IDENTIFICATION, reported because the campaign's hazard list predicts it.** The
  search returned `https://www7.uc.cl/.../LU-May%202011-bl.pdf` under a Pontiff–Woodgate query; it
  fetched at **HTTP 200, 360,269 bytes, `%PDF-1.5`**, 38 pages. **It is not Pontiff & Woodgate.**
  Extracted locally, its first line reads: *"Share Issuance and Cross-Sectional Returns: The
  Importance of Controllers' Stakes — Borja Larrain and Francisco Urzúa I."* — **Chilean data, a
  different paper, a similar title.** Had I cited it from the search result I would have attributed
  a Chilean ownership study to a US anomaly paper. It does contain a useful corroborating sentence,
  correctly attributed: *"Issuance (ISSUE) is defined as the log-change in the number of shares
  outstanding in the previous year … **Shares outstanding are adjusted for splits.**"*
  `[PEER-REVIEWED / working paper, read in full for that passage]`
- **ASC 260-10-55-12: NOT READ.** §6.1.

---

## 9. Sub-question 4 — what else a share-count panel unlocks

### 9.1 Buyback verification against the share count — **a DATA question, in scope, and HALF possible**

`[MEASURED IN BRIEF]` — annual `frames`, issuer counts:

| tag | unit | CY2012 | CY2018 | CY2024 |
|---|---|---|---|---|
| **`PaymentsForRepurchaseOfCommonStock`** | USD | **2,507** | **2,367** | **2,496** |
| `TreasuryStockValueAcquiredCostMethod` | USD | 1,097 | 946 | 887 |
| **`TreasuryStockSharesAcquired`** | **shares** | **639** | **593** | **531** |
| **`StockRepurchasedDuringPeriodShares`** | **shares** | **491** | **397** | **504** |
| `StockRepurchasedAndRetiredDuringPeriodShares` | shares | 242 | 237 | 253 |
| `StockIssuedDuringPeriodSharesNewIssues` | shares | 431 | 316 | 345 |
| **`TreasuryStockCommonShares`** *(negative control)* | shares | **404** | **404** | **404** ✓ |

**The dollars are broadly available (~2,400–2,500 issuers/yr, i.e. 33% of the 7,606 `CY2012Q1I`
Assets-filers rising to 45% of the 5,544 in `CY2026Q1I`). The share QUANTITIES are not — 237 to 639
issuers, roughly 4–12% of filers.** So:

- **Dollars-against-count verification: YES, and it is the useful one.** `Payments ÷ Δ(share count)`
  gives an implied average repurchase price, which can be checked against the period's VWAP from the
  programme's own bars. A mismatch flags either a bad share count or a bad dollar figure. **This is a
  genuine free cross-check on a panel the programme would otherwise have to trust.** The programme
  could use it as a data-quality screen.
- **Quantity-against-quantity verification: NO.** At 4–12% coverage the cross-check exists for a
  small, self-selected minority — and a check available only on the issuers that tag carefully is not
  a check.

*(The buyback SIGNAL is excluded ground; this is the verification question only.)*

### 9.2 Public float — **weak, and the reason is the lag**

`[MEASURED IN BRIEF]` — `dei:EntityPublicFloat`, USD:

| frame | `EntityPublicFloat` | cover-page count | float-but-no-count | count-but-no-float |
|---|---|---|---|---|
| `CY2012Q2I` | 4,987 | 6,546 | 565 | 2,124 |
| `CY2018Q2I` | 4,453 | 5,189 | 619 | 1,355 |
| `CY2024Q2I` | 4,356 | 4,743 | 768 | 1,155 |
| **`CY2026Q2I`** | **22** | 4,406 | 5 | 4,389 |

`CY2024Q2I` values: n = 4,356, **355 zero-or-null (8.1%)**, median **$281,030,947**.

**The `CY2026Q2I` collapse to 22 is the finding, not an error.** Float is stated **once a year** on
the 10-K cover, as of the last business day of the most recent second fiscal quarter — so a float
measured 2026-06-30 appears in a 10-K filed in early **2027**. **Annual frequency and a lag of up to
nine months.** Plus 8.1% zeroes and 25% of count-carrying issuers with no float at all. **Too stale
and too sparse to carry a monthly or annual cross-sectional signal.** Its legitimate use is as a
**size/filer-status band** — which is what the SEC uses it for, and which `A1` already has from
`sub.txt`'s point-in-time `afs` field more cheaply.

### 9.3 Insider-held fraction — **NOT AVAILABLE, state it plainly**

**Not in XBRL in any form.** The cover page gives float in **dollars** and the count in **shares**;
the implied non-affiliate *share* count requires a price on the float measurement date, and the
residual "affiliate-held" is not the insider-held fraction — it includes affiliated institutions.
**The only free sources for insider holdings are Form 4/Form 3 and 13D/13G, both permanently excluded
ground.** **Route dead, and the programme should not spend a lane on it.**

### 9.4 What the panel unlocks that the lane was not asked about

**The share-count series is the missing leg of a free market-capitalisation panel.** §5.3's pairing —
cover-page count at its own `end` date × as-traded close on that date — yields **point-in-time market
cap with a 5-day as-of lag, dead names retained on CIK, at 81% cross-sectional coverage.** That
unlocks `CompEquIss` directly, and it is also the denominator for every price-scaled characteristic
(B/M, E/P, S/P) that `A2` surveyed. **Worth noting because `B2`'s profitability work needs a
denominator too.**

---

## 10. What I would build, if anything

**One route, and a short list of non-negotiables.**

1. **Form net issuance as a SAME-FILING ratio of annual `WeightedAverageNumberOfSharesOutstandingBasic`,
   with `...DilutedSharesOutstanding` as the first fallback and `...BasicAndDiluted` as the second.**
   Coverage 81% alone, **91% in a chain with the cover-page count**, and the better coverage on
   multi-class names. **Zero split inference.** Measured p95 error **0.498%**, zero split-sized errors
   in 58 restatement events.
2. **Never form a share-count LEVEL across filings, for any purpose.** §7.6 shows both vintage rules
   are wrong across a split, and the same-filing ratio is the only construction immune to that.
3. **Harvest from FSDS `num.txt` (`adsh` + `ddate` + `qtrs`), not from the company-concept API.** As
   filed rather than latest-vintage; one bulk download; **and it is the only free product carrying the
   class-dimensioned rows that reach Berkshire, Meta, Comcast, UPS, Visa and Accenture.** Accept the
   ~50-day-plus-queueing lag, which an annually-rebalanced signal does not notice.
4. **Assert the cancellation, do not assume it.** For every period-pair reported twice, assert the
   two ratios agree to within 1%; **and assert the assertion FIRES on a deliberately cross-filing
   pair.** `CLAUDE.md`'s rule that a self-test which cannot fail is worse than none applies exactly
   here: the cross-filing pair is the ready-made deliberate break, and §5.2 gives eleven named cases
   where it must trip.
5. **Filter exact powers of 1000 out of any level series** — 19 of 47 restatement events in the random
   cohort were reporting-scale changes, and the ratio construction already absorbs them, but a level
   series does not.
6. **Use the split tag ONLY as a confirming third source**, never as the locator, and never without
   checking whether its value sits on a `Range=Minimum/Maximum` axis in FSDS.
7. **And the stage-0 check before any of it.** The programme's own per-name question is whether the
   surviving signal has any spread after the `$5` screen — `A2` measured `ShareIss1Y` falling from
   **1.06 to 0.48 %/month** under that screen with **35% long / 65% short**. **The data question is
   now answered; the tradeability question `A2` raised is not, and nothing here changes it.** A
   share-count panel makes the signal computable. It does not make it profitable, and `A2`'s verdict
   that the long-only residual is indistinguishable from the cost **stands unaltered by this lane.**

---

## 11. What I could not verify, stated plainly

1. **ASC 260-10-55-12, the retroactive-restatement requirement the whole `F1` route rests on, I did
   not read.** The FASB Codification is behind a login and the campaign forbids accounts. **I measured
   the behaviour on 58 events instead, which is better evidence for the route and worse evidence for
   the rule.** If the rule's exact scope matters — in particular whether it covers stock dividends and
   reverse splits identically, and what it says about reverse recapitalisations — that needs a source
   I was not permitted to reach.
2. **Pontiff & Woodgate (2008) — NOT OBTAINED.** DNS failure on `www2.bc.edu`, HTTP 403 on Wiley
   (§8.3). Every figure in this brief attributed to the share-issuance literature comes from
   Daniel & Titman (read in full for the passage), the OSAP code (read in full), or `A2`'s brief
   (quoted). **Nothing rests on Pontiff & Woodgate.**
3. **I did not measure the same-filing route's error on the 33% of period-pairs reported only once.**
   The statistic is structurally unavailable there. The algebra still holds; the reporting error is
   unmeasured.
4. **I did not establish a ground-truth split list independent of both XBRL detectors.** The §7
   cross-tabulation measures mutual disagreement, which bounds both error rates from below but does
   not give either one absolutely. **For the routes I REJECT that is sufficient — 50% mutual
   disagreement disqualifies them whichever is right.** For `F1` it does not matter, because `F1`
   detects nothing.
5. **My test sample is 161 CIKs, not 1,573, and it is not the programme's universe.** It is 22
   hand-picked, 80 random from a 6,258-CIK frame, and 59 drawn from tag-carriers — **deliberately
   over-weighted toward splitters**, which makes the §6 error rate a measurement on split-heavy names
   and therefore conservative for the route, but it says nothing about the programme's `$5`-floored,
   dollar-volume-screened cross-section. **I could not apply that screen, because I have no price
   data.**
6. **The five-year chaining question is reasoned, not measured.** A 10-K presents three years of
   income statement, so a five-year ratio needs two or three chained same-filing links; at p95 =
   0.498% per link that compounds to ~1.0–1.5%. **I did not measure the chained error, and I did not
   measure how many issuers present only two years** (smaller reporting companies are permitted to,
   which would force four links).
7. **The FSDS multi-class recovery is demonstrated on ONE quarter (`2025q2`) and four named example
   rows.** I did **not** verify that the `segments` field is populated consistently back through the
   whole 2009–2026 archive, nor that `ClassOfStock` member names are stable enough to map classes to
   tickers. `A1` reports the archive was reprocessed 2024-12-27, which is a reason to expect
   consistency and not evidence of it. **Before anything is built on FSDS, that needs one more
   quarter from 2012 and one from 2019.**
8. **I did not measure the multi-class coverage loss on a union-of-quarters basis** — the 12.1% →
   20.1% trend in §3 is from single frame buckets, and §1 shows a single bucket can be wrong by a
   factor of two. **Read that trend as a direction, not a level.** The union-based figure I do trust
   is the 91.0%/7.8% of §2.2.
9. **The split ratios I call "true" for Apple, NVIDIA, Tesla, Amazon, Walmart, GE, Citigroup,
   Chesapeake and Rite Aid are confirmed only by the XBRL tag agreeing with the restatement factor
   recovered independently.** Two instruments agreeing is not a primary record of an ex-date. **My
   own prior beliefs were wrong twice — I expected Rite Aid 1-for-4 (it is 1-for-20) and Walmart no
   split in the window (it split 3-for-1 in 2024), and the measurement corrected me both times.**
   Three of my hand-written CIK labels were also wrong and the API's `entityName` corrected them.
10. **I did not price the full harvest.** `A1` measured 70 FSDS zips at 5.26 GB; I downloaded one
    (79 MB, 3.4 M `num.txt` rows). **I did not time or run the full extraction**, so the build cost in
    §10 is `A1`'s figure, not mine.
11. **`A1`'s "no split history in any XBRL product" and my 2,280 tag-carrying CIKs are both recorded
    and I adjudicate neither.** I weight my measurement because it names an endpoint and a byte count
    — but `A1`'s conclusion that XBRL gives no usable split adjustment is one I reach independently
    and by a different road, so the disagreement is about a tag's existence and not about the verdict.
12. **Nothing here is tested against the programme's own corporate-actions feed or vendor adjustment
    column.** The same-filing route is a free *alternative* to them; whether it *agrees* with them is
    an unmeasured and obvious next check, and it is the one that would turn this into a
    cross-validation of a feed the programme already pays for.

---

**Files this brief quotes, written to `data/` per the schema:**
[`data/B4-same-filing-ratio-error-rate.csv`](../../../data/B4-same-filing-ratio-error-rate.csv)
(865 rows — every paired observation behind §6) and
[`data/B4-split-detector-crosstab.csv`](../../../data/B4-split-detector-crosstab.csv)
(161 rows — per-CIK outcomes for detectors `T`, `R` and `J` behind §7).
Raw response caches and probe scripts (`B4_*`) remain in session temp and are deletable.
