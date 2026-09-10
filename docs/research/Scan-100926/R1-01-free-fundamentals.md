# R1 · A1 — Free, point-in-time, dead-inclusive fundamentals

**Lane A1 of round 1, Scan-100926.** Attacks **the data constraint**: seven of the ten strongest
post-2005 survivors need Compustat-style fundamentals and this programme has none. The question is
whether that gap is **real or merely unexamined**.

Contract and rules: [`00-SCHEMA.md`](00-SCHEMA.md). Nothing here closes or admits anything (R15).

---

## 0. THE ANSWER, STATED BEFORE THE EVIDENCE

**The gap is closable. The free source is real, it is genuinely point-in-time, and it retains dead
issuers. But the obvious endpoint — the one a reasonable person reaches for first — is a silent
look-ahead, and the binding cost is not the download.**

Four findings, in the order of how much they change what a future round can consider:

1. **`companyfacts` + the Financial Statement Data Sets are point-in-time.** Both return the
   *originally filed* figure **and** every later revision, each stamped with its accession, form and
   filing date. I reconstructed Plug Power's balance sheet as it stood on six named as-of dates and
   got the right vintage each time. **[MEASURED IN BRIEF]**
2. **The `frames` API is a LOOK-AHEAD and it is the natural thing to reach for.** It returns
   *last-filed*. Kraft Heinz's FY2016 operating cash flow comes back as **2,648,000,000** carrying an
   accession filed **2019-06-07** — against the **5,238,000,000** that was knowable on 2017-02-23. A
   **98% error** on a period that ended 2016-12-31, with no `filed` field in the row to warn you.
   **[MEASURED IN BRIEF]**
3. **Dead issuers are fully retained in the XBRL products, and the free ticker map is survivors-only
   for the seventh measured time.** Sears, Bed Bath & Beyond and SVB Financial all return complete
   fact histories to the month they died. `company_tickers.json` contains none of their tickers, and
   `submissions.json` returns `tickers: []` for all three. **The identifier bridge, not the
   fundamentals, is the gap.** It is reconstructible from two free-but-heuristic routes whose union I
   measured at **94.5–97.4%**. **[MEASURED IN BRIEF]**
4. **The real cost is tag mapping, not bandwidth.** `SalesRevenueNet` falls from **2,085** filers in
   CY2015 to **1** in CY2019; `CostOfGoodsSold` from **1,296** to **0**. **85–91% of distinct tags in
   any quarter are filer-invented extensions.** A single-tag panel across 2010–2026 collapses at
   FY2018. **[MEASURED IN BRIEF]**

**And the external evidence points the opposite way from pessimism on one specific family.** Du,
Huddart & Jiang (2021) built as-filed fundamentals from exactly these free products and found the
accruals hedge pays **0.673%/month on as-filed data against 0.296%/month (insignificant) on
Compustat** — i.e. for accruals the free source is not a degraded substitute, it is the *stronger*
one. Five of twenty anomalies they test are sensitive to the data source. **That is a reason to take
this lane seriously, and it is also exactly the kind of single-paper result this programme's own rules
say to compute rather than believe.**

**The honest negatives, up front:** XBRL for this programme's small and mid names **does not exist
before 2011q3** (measured: 478 → 1,625 → **6,980** 10-K/10-Q submissions across 2010q1 → 2011q2 →
2011q3). Using `filed` as the knowability date is a **same-session look-ahead for 57.5%** of recent
10-K/10-Q submissions. And `submissions.json`'s `acceptanceDateTime` is labelled UTC but **40.2% of a
2021q2 sample was Eastern local time** — this programme's own reported-and-unrepaired defect,
reproduced here independently.

---

## 1. WHAT THE SEC'S OWN XBRL PRODUCTS PROVIDE

All five products are free, keyless, and need only a contact string in the User-Agent. Contact used
throughout: `research@backtest-framework.org`. Pacing: one request per 0.22 s in a single process,
across all `sec.gov` and `data.sec.gov` hosts.

### 1.1 The four products, side by side

| | endpoint / file | granularity | earliest | latest (2026-09-10) | lag | volume |
|---|---|---|---|---|---|---|
| **company facts** | `data.sec.gov/api/xbrl/companyfacts/CIK##########.json` | every entity-wide fact, all vintages | 2009-04 filings | real time | **< 1 min after dissemination** (SEC doc) | 2.1–4.3 MB/issuer measured |
| **company concept** | `.../companyconcept/CIK##########/us-gaap/<Tag>.json` | one concept, all vintages | same | real time | same | 3 KB/concept |
| **frames** | `.../frames/us-gaap/<Tag>/<uom>/CY####[Q#][I].json` | one fact per entity per calendar period, **last filed** | `CY2009Q1I` (80 entities) | `CY2026Q2I` (5,238 entities) | real time | 0.7–1.0 MB/call |
| **Financial Statement Data Sets** (FSDS) | `sec.gov/files/dera/data/financial-statement-data-sets/<yyyy>q<n>.zip` | every primary-statement fact per submission, **as filed** | `2009q1` (**headers only, 13 KB**) | **`2026q2`** | **~50 days after quarter end, + up to one quarter queueing** | **70 zips, 5.26 GB** |
| **Financial Statement *and Notes* Data Sets** | `.../financial-statement-notes-data-sets/<yyyy>_<mm>_notes.zip` | all facts incl. notes, text and dimensions | `2009q1` | **`2026_08`** (published **2026-09-08**) | **~8 days**, monthly since Nov 2020 | **80 files, 24.9 GB** |
| bulk mirrors | `sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip`, `.../bulkdata/submissions.zip` | all of the above two APIs | — | nightly | **recompiled ~03:00 ET nightly** (SEC doc) | not downloaded |

[PRIMARY DATA DOC] [read in full] — *EDGAR Application Programming Interfaces*,
`https://www.sec.gov/search-filings/edgar-application-programming-interfaces`, "Last Reviewed or
Updated: April 8, 2025". Note `https://www.sec.gov/edgar/sec-api-documentation` returns the **same
bytes** (`sha256_12=c64e523e39a6`, 68,430 bytes) — it is the same page under two paths, not two
sources.

[PRIMARY DATA DOC] [read in full] — *Financial Statement Data Sets* landing page, header line
"**January 2009 - June 2026**"; and `https://www.sec.gov/files/aqfs.pdf` (9 pages, extracted locally
with pypdf 6.16.2 and read in full).

### 1.2 Scope, verbatim from the official documents

> "Currently included in the APIs are the submissions history by filer and the XBRL data from
> financial statements (forms 10-Q, 10-K,8-K, 20-F, 40-F, 6-K, and their variants)."

> "The following XBRL APIs aggregate facts from across submissions that … Apply to the entire filing
> entity"

**That second clause is the single most consequential line in the API documentation**: the XBRL APIs
carry **only non-dimensional facts**. No segments, no geographies, no class-of-stock breakdowns, no
`ScenarioPreviouslyReported` rows. Confirmed by measurement — `companyfacts` for Sears Holdings
carries exactly **two** `dei` concepts (`EntityCommonStockSharesOutstanding`, `EntityPublicFloat`) and
**435** `us-gaap` concepts; `dei/TradingSymbol` returns a genuine **404**.

The FSDS documentation states its own scope as "forms 10-K, 10-K/A, 10-KT, 10-KT/A, 10-Q, 10-Q/A,
10-QT, 20-F, 20-F/A, 40-F, 40-F/A, 6-K, or 6-K/A" and "Submitted from 4/15/2009 through the 'Data
Cutoff Date' inclusive". **CONFLICT, RECORDED, NOT ADJUDICATED:** the actual `sub.txt` files carry
forms the documented scope omits — measured in `2012q2`: `S-1/A` 76, `8-K` 63, `POS AM` 59, `S-1` 51,
`S-4` 17; in `2026q2`: `11-K` **731**, `S-1` 68, `POS AM` 60. I would weight the **data** over the
PDF, because the PDF is also demonstrably behind on the NUM schema (§6.3). **Consequence: a scope
filter written from the documentation will silently admit registration-statement and benefit-plan
financials into a fundamentals panel.** Filter on `form` explicitly.

### 1.3 Field inventory that actually matters

`companyfacts` fact object, measured: `{start?, end, val, accn, fy, fp, form, filed, frame?}`.

FSDS `sub.txt`, 36 columns, measured identical in 2009q2, 2010q1, 2012q2, 2021q2, 2022q1, 2026q2.
The load-bearing ones:

| field | what it gives you | documented source |
|---|---|---|
| **`accepted`** | **acceptance date AND TIME to the second** — "Filings accepted after 5:30pm EST are considered filed on the following business day." | EDGAR |
| `filed` | the EDGAR filing date (already rolled per the 5:30pm rule) | EDGAR |
| **`prevrpt`** | TRUE if this submission **was subsequently amended** — a look-ahead flag, diagnostics only | EDGAR |
| `name` | **"the name of the legal entity as recorded in EDGAR as of the filing date"** — a point-in-time name | EDGAR |
| `sic` | **"Four digit code assigned by the SEC as of the filing date"** — a point-in-time industry code | EDGAR |
| `afs` | filer status at submission (`1-LAF`/`2-ACC`/`3-SRA`/`4-NON`/`5-SML`) — a point-in-time size band | XBRL |
| `former`, `changed` | **one** most-recent former name and its change date | EDGAR |
| `fye`, `fy`, `fp`, `period` | fiscal calendar, fiscal-year/period focus, balance-sheet date | XBRL |
| `nciks`, `aciks` | co-registrant count and CIKs (`PARTIAL` when the list overflows 120 chars) | EDGAR |
| `instance` | XBRL instance filename — **"The name often begins with the company ticker symbol"** | EDGAR |

The documentation is explicit that these are vintage-correct:

> "EDGAR derived fields represent the most recent EDGAR assignment as of a given filing's submission
> date and do not necessarily represent the most current assignments."

**The *Notes* `sub.tsv` carries four fields the compact FSDS does not:** `pubfloatusd`, `floatdate`,
`floataxis`, `floatmems` — **a point-in-time public float with its measurement date, in the
submissions table.** Measured present in `2015q2_notes`, `2019q2_notes` and `2026_08_notes`.

### 1.4 The lag, measured rather than assumed

**[MEASURED IN BRIEF]** `period` → `filed`, 10-K/10-Q/10-K/A/10-Q/A, from `sub.txt`:

| quarter | n | p05 | p25 | **median** | p75 | p95 | max |
|---|---|---|---|---|---|---|---|
| 2009q2 | 22 | 23 | 30 | **36** | 41 | 44 | 59 |
| 2010q1 | 495 | 29 | 47 | **56** | 57 | 63 | 227 |
| 2012q2 | 9,193 | 29 | 38 | **44** | 52 | 129 | 761 |
| 2021q2 | 7,810 | 29 | 36 | **43** | 70 | 144 | **5,981** |
| 2022q1 | 7,237 | 35 | 53 | **63** | 87 | 134 | 1,978 |

The 5,981-day maximum is a filing whose `period` sits 16 years before its `filed` date. **Whatever it
is — a delinquent catch-up, a transition period, or a bad `period` — any panel builder must cap the
`period`→`filed` distance or a single row will carry a fiscal 2005 balance sheet into a 2021
cross-section.** I did not identify the issuer; see §9.4.

**Total staleness of the bulk FSDS product:** period end → filing (median ~45 d, p95 ~140 d) → the
next quarterly posting, which per the documentation is "Data contained in documents filed after
5:30pm EST on the last business day of the quarter will be included in the next quarterly posting",
published ~50 days after that quarter ends (`2026q2.zip` `Last-Modified: Wed, 19 Aug 2026`). **Worst
case ~4.5 months from fiscal period end to availability in the bulk file.** The APIs are real time.
**For a backtest this is irrelevant; for anything live, the APIs are the only option.**

---

## 2. THE QUESTION THAT DECIDES USEFULNESS — POINT-IN-TIME OR RESTATED?

This got the largest share of effort, as instructed. The answer is **product-specific**, and the
product that is easiest to use is the one that lies.

### 2.1 `frames` is RESTATED. Proven on two named issuers.

The official wording, verbatim:

> "The xbrl/frames API aggregates one fact for each reporting entity **that is last filed** that most
> closely fits the calendrical period requested."

**[MEASURED IN BRIEF]** `GET https://data.sec.gov/api/xbrl/frames/us-gaap/NetCashProvidedByUsedInOperatingActivities/USD/CY2016.json`
(200, 903,423 bytes, 5,902 entities):

```
ROW {'accn': '0001637459-19-000049', 'cik': 1637459, 'entityName': 'Kraft Heinz Co',
     'loc': 'US-PA', 'start': '2016-01-04', 'end': '2016-12-31', 'val': 2648000000}
```

Against the same company's `companyfacts` history for the same concept and period:

```
filed=2017-02-23 form=10-K    accn=0001637459-17-000007 fy=2016 fp=FY val=5238000000
filed=2018-02-16 form=10-K    accn=0001637459-18-000015 fy=2017 fp=FY val=2649000000
filed=2019-06-07 form=10-K    accn=0001637459-19-000049 fy=2018 fp=FY val=2648000000  <-- frames picks this
```

**Frames returns the value first published on 2019-06-07 for a fiscal year that ended 2016-12-31 — a
2.3-year look-ahead and a 98% error in the level.**

Second case, a formal restatement. `GET .../frames/us-gaap/Assets/USD/CY2020Q2I.json` (200, 760,721
bytes, 5,726 entities):

```
ROW cik=1093691 'Plug Power Inc' val=898719000 end=2020-06-30 accn=0001558370-22-003577
```

`0001558370-22-003577` is Plug Power's **10-K/A filed 2022-03-14**. The value knowable on 2020-08-10
from the original 10-Q was **1,030,314,000** — a 14.6% difference, 19 months early.

**And frames gives you no way to detect this.** Measured row keys: `['accn', 'cik', 'entityName',
'loc', 'end', 'val']`. **No `filed`. No `form`. No `fy`/`fp`.** You cannot filter a frame by
knowability date, and because frames keeps exactly one fact per entity per period you cannot recover
the original from it either. The accession is the only clue and it requires a second lookup.

**Verdict: `frames` is unusable for any backtest. It is also the most convenient endpoint, returns 200
with a plausible cross-section, and is what a cross-sectional study naturally reaches for. Treat it
as a trap.**

### 2.2 `companyfacts` is point-in-time RECONSTRUCTIBLE. Demonstrated end to end.

`companyfacts` returns **every vintage** of every entity-wide fact, each carrying `accn`, `form` and
`filed`. No deduplication: measured on Sears Holdings, `StockholdersEquity` at `end=2018-08-04`
appears twice with the **same** value from two different accessions (the original 10-Q and the next
quarter's comparative), so the API is not collapsing rows.

**[MEASURED IN BRIEF]** The reconstruction rule is `filter filed <= as_of, then take max(filed)`.
Run on Plug Power's `Assets`, from `A1_cf_0001093691.json`:

| period end | as-of 2020-09-01 | 2020-12-01 | 2021-03-01 | 2021-06-01 | 2022-06-01 | 2026-09-10 |
|---|---|---|---|---|---|---|
| 2020-06-30 | 1,030,314,000 | 1,030,314,000 | 1,030,314,000 | **898,719,000** | 898,719,000 | 898,719,000 |
| 2020-09-30 | *not yet knowable* | 1,500,629,000 | 1,500,629,000 | **1,356,093,000** | 1,356,093,000 | 1,356,093,000 |
| 2020-12-31 | *not yet knowable* | *not yet knowable* | *not yet knowable* | 2,251,282,000 | 2,251,282,000 | 2,251,282,000 |

Every cell resolves to the filing that was actually on file, the `not yet knowable` cells are empty
rather than silently back-filled, and the restatement appears exactly when the delinquent FY2020 10-K
landed on 2021-05-14. **This is the behaviour a point-in-time database is supposed to have.**

### 2.3 FSDS is point-in-time BY CONSTRUCTION, and it carries the acceptance *time*

> "All numeric data is 'as filed.'"
> "this data set represents quarterly and annual **uncorrected** and 'as filed' EDGAR document
> submissions containing multiple reporting periods (including amendments of prior submissions)"

Because each quarterly zip contains **only the submissions accepted in that quarter**, assembling
2009q2…2026q2 and filtering on `accepted <= as_of` gives a true point-in-time panel with no filtering
logic at all. **[MEASURED IN BRIEF]** Plug Power's original FY2020 10-K appears in `2021q2.zip`
(`accepted=2021-05-14 06:20:00`) and its 10-K/A in `2022q1.zip` (`filed=20220314`) — two files, two
vintages, no ambiguity.

**FSDS is the only one of the five products carrying a time of day.**

### 2.4 THE RESIDUAL LOOK-AHEAD NOBODY WARNS YOU ABOUT: `filed` IS A DATE

`companyfacts` exposes `filed` but **not** the acceptance time. And the majority of filings are
accepted **after the US close** while carrying that same day's `filed` date.

**[MEASURED IN BRIEF]** FSDS `sub.txt`, forms 10-K/10-Q/10-K/A/10-Q/A, bucketed by `accepted` hour
(ET) and whether `filed` equals the acceptance date:

| bucket | 2012q2 (n=8,638) | 2021q2 (n=6,872) | 2026q2 (n=6,000) |
|---|---|---|---|
| pre-open (<09:30), filed same day | 7.7% | 13.4% | 13.9% |
| intraday (09:30–16:00), filed same day | 45.5% | 25.6% | 20.5% |
| **after-close (16:00–17:30), filed SAME day** | **38.7%** | **50.9%** | **56.9%** |
| late (≥17:30), filed same day | 0.6% | 0.9% | 0.6% |
| late (≥17:30), filed **later** day | 7.4% | 9.2% | 8.0% |
| **`filed`-only rule is a same-session look-ahead for** | **39.3%** | **51.8%** | **57.5%** |

**Read that bottom row against this programme's shape: the book's edge is overnight and the bars are
daily. A filing accepted at 16:40 ET on day *D* carries `filed = D`. Entering at *D*'s close on a
`filed <= D` rule means trading on a document that did not yet exist.** And the share has risen from
39% to 58% over the window, so the bias is not stationary.

The documented 5:30pm roll is **approximately** but not exactly true: of 763 `2012q2` filings accepted
at or after 17:30, **700** rolled `filed` to a later day and **63 did not** (e.g. CARMAX INC,
`accepted 2012-04-25 17:31:00`, `filed 20120425`). Same pattern in 2021q2 (81 of 859) and 2026q2 (63
of 699). **So the roll cannot be relied on either.**

**Safe rule, given all of the above: derive knowability from FSDS `accepted` in ET; where only
`companyfacts` is available, use `filed + 1 business day`.**

### 2.5 `acceptanceDateTime` IN `submissions.json` IS NOT RELIABLY UTC — this programme's own defect, reproduced

The programme carries a reported-and-unrepaired "mixed-timezone `acceptanceDateTime`" defect. I
reproduced it independently by joining FSDS `accepted` (documented ET, no suffix) to
`submissions.json` `acceptanceDateTime` (suffixed `Z`) on the accession number.

**[MEASURED IN BRIEF]** 180 unstratified random 10-K/10-Q submissions drawn from `2021q2` and
`2026q2`:

```
offset hours (subsZ minus FSDS_ET): {0: 37, 4: 143, 'ADSH_NOT_IN_RECENT': 2}
  offset  0h :   37  = 20.6%
  offset  4h :  143  = 79.4%
by quarter: 2026q2:{4: 88}   2021q2:{0: 37, 4: 55}
```

April–June is EDT (UTC−4), so an honest UTC stamp must show **+4h**. **37 of 92 submissions from
2021q2 (40.2%) are Eastern local time wearing a `Z` suffix; 0 of 88 from 2026q2 are.** The same filer
agent prefix shows both offsets (`0001193125`: {4:14, 0:4}; `0001213900`: {4:10, 0:2}), so it is not
an agent property.

**Decisive discrimination.** Either field could in principle be the liar. I selected `2021q2`
submissions whose FSDS `accepted` is **≥ 17:40 ET** — where the 5:30pm roll is an independent witness
— and checked whether `filed` rolled:

```
(offset_hours, filed_rolled_to_later_day) counts = {(0, True): 26, (4, True): 32}
  offset=0h FSDS_ET=2021-04-16 18:09:00 subsZ=2021-04-16T18:08:52.000Z filed=20210419 rolled=True  adsh=0001654954-21-004299
  offset=0h FSDS_ET=2021-04-27 17:56:00 subsZ=2021-04-27T17:56:03.000Z filed=20210428 rolled=True  adsh=0001199835-21-000226
  offset=0h FSDS_ET=2021-06-22 21:44:00 subsZ=2021-06-22T21:43:41.000Z filed=20210623 rolled=True  adsh=0001104659-21-084333
```

All 58 rolled. If the `Z` were genuine UTC, `0001104659-21-084333` was accepted at 17:44 ET and must
**not** have rolled; it did. **Therefore FSDS `accepted` is ET and the `Z` on those 26 accessions is
false.** 26 of 58 = **44.8%** of late 2021q2 filings, consistent with the 40.2% unstratified figure.

**Conclusion: do not trust `acceptanceDateTime`'s `Z`. Use FSDS `accepted`.** I cannot say when or
whether the defect was fixed — 2026q2 showed 0 of 88, but two quarters are not a history (§9.2).

### 2.6 How often does it actually matter?

Two different questions, two different answers, and conflating them would overstate the problem.

**Population amendment rate** — `prevrpt=1`, the share of submissions later amended, from
`sub.txt`: **4.8%** (2012q2, 438/9,193), **5.6%** (2021q2, 435/7,810), **5.5%** (2022q1, 401/7,237).
(2026q2 shows only 3 — amendments to recent filings have not happened yet, which is itself a reminder
that `prevrpt` is a look-ahead flag.)

**Vintage-disagreement rate on selected issuers** — share of `(concept, period)` cells with more than
one filed vintage whose **first**-filed value differs from the **last**-filed value, over 13 headline
concepts:

| issuer | cells | cells with n>1 vintage | changed | % | median &#124;rel diff&#124; | max &#124;rel diff&#124; |
|---|---|---|---|---|---|---|
| Plug Power | 837 | 498 | 154 | **30.9%** | 0.0362 | 1.7561 |
| Kraft Heinz | 604 | 336 | 94 | **28.0%** | 0.0089 | 1.5778 |
| Hertz / Herc | 601 | 301 | 90 | **29.9%** | 0.0018 | 2.0000 |
| SVB Financial | 308 | 126 | 44 | **34.9%** | 0.0036 | 0.1804 |
| Sears Holdings | 458 | 363 | 90 | **24.8%** | 0.0041 | 1.7518 |
| Bed Bath & Beyond | 623 | 285 | 8 | **2.8%** | 0.0057 | 0.5639 |

**These are NOT base rates and must not be read as such.** Four of the six were chosen *because* they
restated, and "changed" here mixes genuine restatement with ASU adoption, discontinued-operations
recasting and reclassification. The Bed Bath & Beyond row — **2.8%**, a company I picked for being
dead rather than for restating — is the closest thing here to a non-restater reading. **The honest
population number is the ~5% `prevrpt` rate.** The right use of the table is the *tail*: median
disagreements are tiny (0.2–3.6%) but maxima reach **2.0**, i.e. a sign flip or a doubling. A
restatement-blind panel is mostly fine and occasionally catastrophically wrong — which is the worst
shape a defect can have.

---

## 3. HOW AMENDMENTS AND RESTATEMENTS ARE REPRESENTED

**Amended forms are first-class and carry their own accession.** Measured `form` values inside
`companyfacts`: Hertz/Herc `{'10-Q': 13776, '10-K': 9368, '10-K/A': 694, '10-Q/A': 295}`; Plug Power
`{'10-Q': 12896, '10-K': 6905, '10-K/A': 1178, 'DEF 14A': 5}`; Kraft Heinz `{'10-Q': 12483,
'10-K': 7962, '8-K': 1302, '10-Q/A': 631}`.

**Note the `8-K` and `DEF 14A` rows.** `companyfacts` admits forms the FSDS excludes, so the two
products do **not** agree on which documents count. A panel built from `companyfacts` without a
`form` filter will mix 8-K exhibit financials into the 10-K series.

**Reconstructing what was knowable on a date is fully supported, through three independent routes:**

1. **`companyfacts` `filed` + `accn`** — demonstrated in §2.2. Date granularity only.
2. **FSDS `accepted` + `adsh`** — acceptance to the second; the zip a submission lives in *is* its
   vintage.
3. **From inside the restating filing itself.** The post-Dec-2024 FSDS `segments` column exposes the
   restatement axis. Plug Power's FY2020 10-K, `ddate=20200630`:

```
tag=Assets       value=    898719000  segments=''
tag=Assets       value=   1030314000  segments='Restatement=ScenarioPreviouslyReported;'
tag=Assets       value=   -131595000  segments='Restatement=RestatementAdjustment;'
```

and `898,719,000 + 131,595,000 = 1,030,314,000` exactly. **The filer tags its own previously-reported
figure.**

**Two traps in route 3.** First, those dimensional rows are **invisible to the APIs** (§1.2) — this
route exists only in the FSDS/Notes files. Second, and more dangerous: **a naive FSDS query
`tag=='Assets' and ddate==X and uom=='USD'` now returns three rows for this filing and there is
nothing in the tag, date or unit to tell them apart.** You must filter `segments == ''` for the
consolidated value. A parser written before December 2024 did not have to.

**`prevrpt` is a look-ahead flag.** "TRUE indicates that the submission information was subsequently
amended." Useful for diagnostics and for constructing a restatement-free control; **never** a feature.

---

## 4. DEAD ISSUERS

The programme's universe is ~35.7% dead and free identifier maps have measured survivors-only six
separate times. **This is the seventh, and it is also where the lane's binding constraint actually
lives.**

### 4.1 The XBRL products RETAIN dead issuers. Verbatim results.

CIKs resolved from EDGAR company search (`browse-edgar?action=getcompany&company=…&output=atom`),
**not** from the tickers map, so the resolution is not itself survivor-biased. Negative control
`company=ZZQQXX+nonexistent+issuer` returned **0 CIKs** from a 874-byte feed.

**[MEASURED IN BRIEF]** `GET https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json`:

| probe | CIK | status | bytes | `us-gaap` concepts | facts | `filed` min → max |
|---|---|---|---|---|---|---|
| Sears Holdings Corp | 0001310067 | **200** | 2,142,027 | 435 | 14,018 | 2010-08-20 → **2018-12-13** |
| Bed Bath & Beyond | 0000886158 | **200** | 2,489,472 | 393 | 16,518 | 2009-10-07 → **2023-06-14** |
| SVB Financial Group | 0000719739 | **200** | 4,282,477 | 641 | 28,521 | 2010-08-06 → **2023-02-24** |
| Lehman Brothers Hldgs | 0000806085 | **404** | 311 | — | — | — |
| Enron Corp | 0001024401 | **404** | 311 | — | — | — |

Each dead probe's history runs to within weeks of its death (Sears' last 10-Q filed 2018-12-13,
bankruptcy October 2018; BBBY's final 10-K filed 2023-06-14, Chapter 11 April 2023; SVB's final 10-K
filed 2023-02-24, failure March 2023). **Nothing is truncated and nothing is withdrawn.**

Lehman and Enron are 404 **because they died before XBRL existed**, not because they were removed.
**That sets the hard floor of this whole lane: XBRL fundamentals begin 2009 and no free XBRL product
can reach an issuer that stopped filing before then.**

**NEGATIVE CONTROLS, reported beside the counts as required.** Three CIKs that must not exist:

```
[404] .../companyfacts/CIK0000000000.json  311 bytes  <Error><Code>NoSuchKey</Code>…
[404] .../companyfacts/CIK9999999999.json  311 bytes  <Error><Code>NoSuchKey</Code>…
[404] .../companyfacts/CIK0000000001.json  311 bytes  <Error><Code>NoSuchKey</Code>…
[404] .../submissions/CIK0000000000.json   301 bytes  <Error><Code>NoSuchKey</Code>…
```

Every failure is a **genuine 404 with an XML `NoSuchKey` body**, not a 200 shell, not a 171-byte error
body, not an empty `data` key. Frames controls behave the same: `ZZZZNotATag` → 404/325 B,
`uom=ZZZ` → 404/320 B, `CY2020Q9I` → 404, `CY1995Q4I` → 404, `CY2099Q4I` → 404. In the FSDS,
`cik=9999999999` returned **0** submissions in every one of the 20 quarters examined, and in the Notes
`txt.tsv` the tag `ZZZZNotARealTag` returned **0** rows against 12,347 for `TradingSymbol`.
**Conclusion: on these endpoints, absence means absence.** This is the one part of the harvest I am
confident is not a 200-flavoured lie.

### 4.2 THE GAP: the ticker is the broken link, not the fundamentals

**[MEASURED IN BRIEF]** `GET https://www.sec.gov/files/company_tickers.json` (200, 796,513 bytes,
`Last-Modified: Tue, 08 Sep 2026 20:53:13 GMT`), **10,407 entries**:

```
ticker AAPL   -> (320193, 'Apple Inc.')      ticker SHLD  -> None   ticker SHLDQ -> None
ticker GM     -> (1467858, 'General Motors')  ticker BBBY  -> None   ticker BBBYQ -> None
ticker NOK    -> (924613, 'NOKIA CORP')       ticker SIVB  -> None   ticker SIVBQ -> None
                                              ticker LEHMQ -> None   ticker WAMUQ -> None
name ~ 'SEARS':    0 hits        name ~ 'BED BATH': 0 hits        name ~ 'ENRON': 0 hits
name ~ 'SVB':      0 hits
name ~ 'SILICON VALLEY': 3 hits -> all (2085659, 'Silicon Valley Acquisition Corp.') — a SPAC, not SVB
name ~ 'LEHMAN':   1 hit  -> (1284143, 'LEHMAN ABS CORP GOLDMAN SACHS CAP 1 SEC BACKED SER 2004-6')
ticker ZZZZZZ_NEGCONTROL -> None        <-- negative control
```

**Survivors-only, seventh measurement.** And note the two near-misses: searching the map by *name*
for "SILICON VALLEY" or "LEHMAN" returns **a live SPAC and an asset-backed trust** — plausible hits
that are the wrong issuers. **A name-matching fallback against this file does not fail loudly; it
fails by returning something.**

`submissions.json` is no better for dead names. **[MEASURED IN BRIEF]**

```
CIK0001310067: name='SEARS HOLDINGS CORP'          tickers=[]  exchanges=[]  formerNames=[]
CIK0000886158: name='20230930-DK-Butterfly-1, Inc.' tickers=[]  exchanges=[]  formerNames=['BED BATH & BEYOND INC']
CIK0000719739: name='SVB FINANCIAL GROUP'          tickers=[]  exchanges=[]  formerNames=['SILICON VALLEY BANCSHARES']
```

**`tickers` is empty for all three.** And `companyfacts` reports Bed Bath & Beyond's `entityName` as
**`'20230930-DK-BUTTERFLY-1, INC.'`** — the post-bankruptcy shell. **The CIK is stable; the name and
the ticker are not.** A CIK-keyed fundamentals panel is safe; anything keyed on name or ticker from
the APIs is not. `dei/TradingSymbol` via `companyconcept` returns **404**.

### 4.3 The bridge that does exist, measured

Two free, dead-inclusive, point-in-time routes — both heuristic.

**Route A — FSDS `instance` filename prefix.** The documentation says the name "often begins with the
company ticker symbol". **[MEASURED IN BRIEF]** share of `sub.txt` rows whose instance matches
`^[a-z][a-z0-9.-]{0,5}[-_]?(19|20)\d{6}`:

| quarter | 2010q4 | 2012q2 | 2018q2 | 2021q2 | 2026q2 |
|---|---|---|---|---|---|
| ticker-shaped prefix | **99.7%** | 95.5% | 96.1% | 86.3% | **66.6%** |

Non-matching examples: `cik0001043121-20100930.xml`, `worldsonline-20111231.xml`,
`a10k123117_htm.xml`, `form10q_htm.xml`, `wddd10q125_htm.xml`. **The convention decays badly after
2018.**

On the dead probes it is exactly right, including through a corporate rename:

```
2012q2 Sears Holdings    traded SHLD/SHLDQ   instance=shld-20120428.xml       name=SEARS HOLDINGS CORP
2012q2 Bed Bath & Beyond  traded BBBY/BBBYQ   instance=bbby-20120225.xml       name=BED BATH & BEYOND INC
2012q2 SVB Financial      traded SIVB/SIVBQ   instance=sivb-20120331.xml       name=SVB FINANCIAL GROUP
2012q2 Hertz -> Herc      traded HTZ then HRI instance=htz-20120331.xml        name=HERTZ GLOBAL HOLDINGS INC
2021q2 Hertz -> Herc                          instance=hri-20210331_htm.xml    name=HERC HOLDINGS INC
2022q1 Bed Bath & Beyond                      instance=bbby-20211127_htm.xml   name=BED BATH & BEYOND INC
```

**Note the last line.** In 2022q1 the FSDS `name` is `BED BATH & BEYOND INC` while `companyfacts`
reports `20230930-DK-BUTTERFLY-1, INC.` for the same CIK. **FSDS is point-in-time on the name;
`companyfacts` is not.**

**Route B — `dei:TradingSymbol` in the Notes Data Sets.** Not in the APIs, but present in `txt.tsv`
with the accession. **[MEASURED IN BRIEF]** share of 10-K/10-Q submissions carrying a
`dei:TradingSymbol` fact:

| file | 2015q2_notes | 2019q2_notes | 2026_08_notes |
|---|---|---|---|
| `dei:TradingSymbol` | **34.4%** (2,537/7,385) | **55.0%** (3,540/6,440) | **82.8%** (3,454/4,172) |
| `dei:SecurityExchangeName` rows | 0 | 15 | **12,206** |

The curve is the Cover Page XBRL mandate arriving with Inline XBRL. **`SecurityExchangeName` is
effectively unavailable before 2020 — so there is no free point-in-time *exchange* for the early
window at all.**

**Route A and Route B are complementary, and their union is high.** **[MEASURED IN BRIEF]**

| | instance-prefix | `dei:TradingSymbol` | both | **UNION** | **NEITHER** |
|---|---|---|---|---|---|
| 2015q2 (n=7,385) | 96.8% | 34.4% | 33.7% | **97.4%** | **2.6%** |
| 2019q2 (n=6,440) | 90.5% | 55.0% | 51.0% | **94.5%** | **5.5%** |

**This is the load-bearing result of §4: the ticker→CIK bridge for dead issuers is reconstructible
from free SEC data at ~95–97% of filings, but it is a union of two heuristics rather than a mapping,
it carries no share class and no exchange before 2020, and I have NOT measured its false-positive
rate** (§9.1). It closes the gap enough to build on and not enough to trust unaudited.

### 4.4 THE HERTZ TRAP — a 6.9× level break inside one CIK, with no restatement

This is the hazard I did not expect and it is worse than the restatement problem.

CIK **0001364479** is reported by `companyfacts` as `entityName='HERC HOLDINGS INC.'`. Its `Assets` at
`end=2015-12-31`:

```
filed=2016-02-29 form=10-K accn=0001364479-16-000045 fy=2015 fp=FY val=23358000000
filed=2016-05-09 form=10-Q accn=0001364479-16-000058 fy=2016 fp=Q1 val=23285000000
filed=2016-08-09 form=10-Q accn=0001364479-16-000099 fy=2016 fp=Q2 val= 3397000000   <-- 6.9x down
filed=2016-11-08 form=10-Q accn=0001364479-16-000110 fy=2016 fp=Q3 val= 3397000000
filed=2017-03-15 form=10-K accn=0001364479-17-000008 fy=2016 fp=FY val= 3397000000  frame=CY2015Q4I
```

**Nothing was restated.** CIK 1364479 was *Hertz Global Holdings* until the 2016 separation, after
which it continued as *Herc Holdings* (equipment rental) while the car-rental business went to a new
CIK. The 2016 comparatives are Herc standalone. `StockholdersEquity` at 2013-12-31 similarly reads
2,858,700,000 → 2,654,000,000 → **1,877,400,000** across three vintages; the measured max relative
vintage disagreement for this CIK is **2.0000**, i.e. a complete sign or scale change.

**Why this is the most dangerous single finding in the lane:**

- A last-filed panel (i.e. `frames`) assigns Herc's 3.4 bn to a 2015 cross-section in which the
  company had 23.4 bn. The frames row for CY2016 confirms it: `'HERC HOLDINGS INC', val=433400000,
  accn=0001364479-19-000004`.
- A point-in-time panel is **correct** here — it takes the 2016-02-29 figure for a 2016 Q1 decision —
  so PIT discipline happens to defend against this too.
- But **`companyfacts` gives you no signal that the entity changed**, because it reports only the
  current name. **FSDS does**: `name='HERTZ GLOBAL HOLDINGS INC'` in 2012q2, `name='HERC HOLDINGS
  INC'` in 2021q2, and `instance` goes `htz-` → `hri-`.
- The `former`/`changed` pair is **not** a reliable detector: FSDS reports
  `former='HERTZ GLOBAL HOLDINGS INC'` with `changed=20060531` — a 2006 date for a 2016 rename.
  **Flagged as unreliable.**

This also matches a standing note in the programme's memory — *fixtures disagree on corporate-action
basis; `raw_price_factor` cannot fix a spinoff*. **The same is true of fundamentals: no adjustment
factor repairs a CIK whose contents changed identity.** The only defence I found is to diff the FSDS
`name` and `instance` prefix per CIK across quarters and treat any change as a break.

---

## 5. TAXONOMY STABILITY 2010–2026

### 5.1 Two phase-ins, a decade apart, and the prior round had the second one

**The 2009 XBRL rule** — XBRL itself, three annual groups by fiscal period end:
**2009-06-15** (large accelerated filers with >$5 bn float), **2010-06-15** (all other large
accelerated), **2011-06-15** (all remaining filers). Source: Du, Huddart & Jiang (2021) footnote 8
[WORKING PAPER] [read in full for the quoted passage], citing SEC (2009).

**The 2018 Inline XBRL rule** — **CONFIRMED from the SEC's own compliance guide**, by fiscal period
end: **2019-06-15** large accelerated US-GAAP filers, **2020-06-15** accelerated filers,
**2021-06-15** all other operating-company filers (US-GAAP or IFRS). [PRIMARY DATA DOC] [read in
full] — *Operating Company Inline XBRL Filing of Tagged Data*, a Small Entity Compliance Guide,
`https://www.sec.gov/resources-small-businesses/small-business-compliance-guides/operating-company-inline-xbrl-filing-tagged-data`.

**The prior round's three dates are correct and they are the INLINE XBRL dates, not the XBRL dates.**
Two extensions the prior round did not carry, both verbatim from that guide:

> "Domestic form filers, however, will not become subject to the requirement until their first Form
> 10-Q filed for a fiscal period ending on or after the applicable compliance date, as opposed to the
> first filing for a fiscal period ending on or after that date."

So a December-FY large accelerated filer's first Inline XBRL filing is its **10-Q for the quarter
ending 2019-06-30**, not its FY2019 10-K. And:

> "Operating companies will be permitted to file using Inline XBRL under the amendments prior to
> their compliance date once the EDGAR system has been … modified to accept submissions in Inline
> XBRL for all forms under the amendments, which is anticipated to be in March 2019."

**Early adoption was permitted from ~March 2019, so the transition is ragged and the compliance dates
are a floor, not a switch.**

### 5.2 THE PHASE-IN, MEASURED — and it costs this programme the start of its window

**[MEASURED IN BRIEF]** Distinct 10-K/10-Q/10-K/A/10-Q/A submissions in FSDS `sub.txt` by `afs`:

| quarter | submissions | CIKs | LAF | ACC | NON | SML | **small/non-accelerated share** |
|---|---|---|---|---|---|---|---|
| 2009q2 | 20 | 20 | 17 | 2 | 0 | 1 | 5.0% |
| 2010q1 | 478 | 471 | 461 | 7 | 8 | 2 | **2.1%** |
| 2010q2 | 478 | 474 | 461 | 9 | 6 | 2 | **1.7%** |
| 2010q3 | 1,368 | 1,345 | 1,324 | 28 | 14 | 2 | **1.2%** |
| 2010q4 | 1,438 | 1,428 | 1,390 | 31 | 11 | 6 | **1.2%** |
| 2011q1 | 1,460 | 1,437 | 1,399 | 40 | 12 | 9 | **1.4%** |
| 2011q2 | 1,625 | 1,594 | 1,492 | 65 | 15 | 53 | **4.2%** |
| **2011q3** | **6,980** | **6,880** | 1,478 | 1,437 | 813 | 3,252 | **58.2%** |
| 2011q4 | 7,376 | 7,108 | 1,492 | 1,501 | 816 | 3,567 | 59.4% |
| 2013q2 | 8,394 | 6,858 | 1,710 | 1,548 | 803 | 4,329 | 61.2% |
| 2019q2 | 6,622 | 5,626 | 2,072 | 1,245 | 3,164 | 129 | 49.9% |
| 2026q2 | 6,000 | 5,487 | 2,003 | 725 | 3,272 | 0 | 54.5% |

**The cliff is at 2011q3.** Before it, XBRL is a **~1,400-issuer large-accelerated-filer dataset**;
after it, a ~6,900-issuer universe. **This programme's window opens 2010-01-04.**

**What that costs, stated concretely.** A level signal (asset scaling, book-to-market) becomes
available for the full universe from roughly **2011-08** once the first small-filer 10-Qs land. A
signal needing a **year-on-year fundamental change** needs the prior year's filing, so its first
complete cross-section is roughly **2012q3**, and an annually-rebalanced book forming in June would
start at **June 2013** — which is exactly the formation window Du, Huddart & Jiang chose (June 30 of
2013–2019) and they say so. **Against a 2010-01-04 → 2026-08-26 window of ~4,187 bars, that is
roughly 870 bars — about 21% — unavailable for small and mid names, or available only for the
~1,400 largest filers.** For a book whose effective breadth is already ~10 independent instruments,
losing the small end of the early window is not a rounding error.

### 5.3 `afs` is NOT a stable size classifier

Measured above: `5-SML` runs 2,952 (2018q2) → **129** (2019q2) → 2 (2020q2) → **0** from 2021q2, while
`4-NON` runs 555 → **3,164** → 4,161. `3-SRA` is essentially never used (max 12). The SEC's 2020
amendment to the accelerated-filer definition reshuffled the categories mid-window. **`afs` cannot be
used as a continuous size band across 2010–2026.** Use `pubfloatusd` from the Notes `sub.tsv`, or
`dei:EntityPublicFloat`, instead.

### 5.4 TAG CHANGES — the same concept does NOT carry the same tag

**[MEASURED IN BRIEF]** `frames` entity counts, `us-gaap`, `USD`, one call per tag per calendar year
(annual tags `CY####`, instants `CY####Q4I`). 2026 is partial by construction. Full matrix saved to
`data/A1_tag_census.json`.

| tag | 2010 | 2012 | 2014 | 2015 | 2016 | 2017 | **2018** | **2019** | 2020 | 2022 | 2025 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `Revenues` | 3101 | 3879 | 3600 | 3377 | 3630 | 3875 | 3268 | 2839 | 2762 | 2792 | 2227 |
| **`SalesRevenueNet`** | 2093 | 2309 | 2207 | 2085 | 1915 | 1649 | **121** | **1** | **0** | **0** | **0** |
| `SalesRevenueGoodsNet` | 1168 | 1316 | 1267 | 1208 | 1113 | 974 | **92** | **2** | 0 | 0 | 0 |
| **`RevenueFromContractWithCustomerExcludingAssessedTax`** | **0** | **0** | **0** | 1 | 32 | 1412 | 2146 | 2799 | 3052 | 3228 | 2693 |
| `RevenueFromContractWithCustomerIncludingAssessedTax` | 0 | 1 | 2 | 13 | 448 | 855 | 1030 | 883 | 837 | 808 | 652 |
| **`CostOfGoodsSold`** | 1629 | 1826 | 1715 | 1612 | 1486 | 1296 | **113** | **2** | **1** | **0** | **0** |
| **`CostOfGoodsAndServicesSold`** | 952 | 1011 | 914 | 847 | 1620 | 2099 | 2229 | 2148 | 2086 | 2012 | 1566 |
| `CostOfRevenue` | 1184 | 1382 | 1424 | 1375 | 1413 | 1540 | 1444 | 1446 | 1508 | 1692 | 1458 |
| `NetCashProvidedByUsedInOperatingActivities` | 6653 | 6946 | 4948 | 5079 | 5902 | 6313 | 6318 | 6404 | 6597 | 6961 | 5738 |
| **`…OperatingActivitiesContinuingOperations`** | 1273 | 2903 | **3806** | 3657 | 3280 | 1759 | 708 | 489 | 471 | 484 | **321** |
| `CashAndCashEquivalentsAtCarryingValue` | 7845 | 7813 | 7310 | 6767 | 6386 | 6114 | 5871 | 5775 | 6187 | 5770 | 4917 |
| **`CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents`** | **1** | **2** | 346 | 1511 | 2770 | 3676 | 4221 | 4775 | 5525 | 5900 | 4893 |
| **`OperatingLeaseRightOfUseAsset`** | **0** | **0** | **0** | 2 | 2 | 49 | **2068** | **4358** | 4508 | 4872 | 4301 |
| `Assets` | 6512 | 7851 | 7494 | 7018 | 6672 | 6483 | 6305 | 6180 | 6849 | 6870 | 6139 |
| `Liabilities` | 4837 | 5998 | 5901 | 5602 | 5400 | 5343 | 5309 | 5284 | 6005 | 6122 | 5507 |
| `StockholdersEquity` | 6379 | 7634 | 7201 | 6770 | 6480 | 6369 | 6402 | 6448 | 6931 | 6752 | 5743 |
| `LiabilitiesAndStockholdersEquity` | 6443 | 7844 | 7492 | 7019 | 6673 | 6470 | 6293 | 6176 | 6834 | 6806 | 6021 |
| `PropertyPlantAndEquipmentNet` | 5167 | 6120 | 5935 | 5578 | 5332 | 5200 | 5143 | 4990 | 5160 | 4959 | 4201 |
| `ResearchAndDevelopmentExpense` | 2092 | 2509 | 2541 | 2427 | 2390 | 2371 | 2406 | 2542 | 2717 | 2772 | 2290 |
| `Goodwill` | 2895 | 3481 | 3530 | 3429 | 3306 | 3253 | 3240 | 3291 | 3399 | 3347 | 2909 |
| `LongTermDebtNoncurrent` | 1703 | 2099 | 2120 | 2052 | 1990 | 1968 | 1966 | 1966 | 2129 | 1981 | 1720 |
| `ZZZZZZ_NEGATIVE_CONTROL_TAG` | **0** | **0** | **0** | **0** | **0** | **0** | **0** | **0** | **0** | **0** | **0** |

**What breaks, named:**

1. **Revenue, at ASC 606 (FY2018–19).** `SalesRevenueNet` 2,085 → 1 and
   `RevenueFromContractWithCustomer…` 1 → 3,052. **Any single-tag revenue series loses most of its
   cross-section at FY2018.** And `Revenues` itself *also* falls, from 3,875 (2017) to 2,227 (2025) —
   so there is no single tag that survives.
2. **Cost of goods, same break.** `CostOfGoodsSold` 1,612 → 0; `CostOfGoodsAndServicesSold` 847 →
   2,229. **Gross profitability is exposed to both legs of this.**
3. **Operating cash flow needs a two-tag family mid-window.** `…ContinuingOperations` peaks at 3,806
   in 2014 — **more than a third of filers** — and decays to 321. A one-tag OCF series is badly
   incomplete 2012–2016, which is exactly where the accruals literature's XBRL sample sits.
4. **Cash, at ASU 2016-18 (FY2018).** The restricted-cash-inclusive tag goes 346 → 5,525.
   **Cash-scaled signals change definition mid-window.**
5. **`OperatingLeaseRightOfUseAsset`: 49 (2017) → 2,068 (2018) → 4,358 (2019).** ASC 842 moves
   operating leases onto the balance sheet. **This is a one-time mechanical jump in total `Assets` for
   ~4,400 filers. Any asset-growth or asset-scaled signal will fire spuriously across FY2019–2020 and
   it will look like a real cross-sectional effect** because it genuinely differs by lease intensity,
   i.e. by industry. **A necessary control is to net out `OperatingLeaseRightOfUseAsset` before
   differencing `Assets` across the adoption year.**
6. **`Liabilities` is under-tagged.** 5,507 filers against 6,139 for `Assets` in 2025 — **~10% of
   filers never tag total liabilities**, because the balance sheet foots to
   `LiabilitiesAndStockholdersEquity`. Total liabilities must be *derived*
   (`LiabilitiesAndStockholdersEquity − StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest`),
   and that derivation itself straddles two equity tags (`StockholdersEquity` 5,743 vs the
   including-NCI variant 2,094 in 2025), so a leverage signal needs a three-tag fallback chain.
7. **Three `us-gaap` taxonomy versions coexist in a single quarter.** Measured in `2026q2`
   `tag.txt`: `us-gaap/2026` (2,685 standard tags), `us-gaap/2025` (3,745), `us-gaap/2024` (1,323),
   plus `ifrs/2025`, `ifrs/2024`, `us-gaap-ebp/*`, `srt/*`, `dei/*`. Same shape in 2012q2
   (`us-gaap/2011`, `/2012`, `/2009`) and 2019q2. **There is no single taxonomy version to code
   against, even within one quarter.**

**A trap I walked into myself, reported because it is instructive.** I queried
`frames/us-gaap/CommonStockSharesOutstanding/USD/…` — wrong unit, shares are `shares` not `USD`. Every
call returned **404**, my counter coerced 404 to 0, and the resulting row was **indistinguishable from
my deliberate negative-control tag**: eighteen zeroes. **A 404-to-zero coercion writes a whole cohort
empty and looks exactly like a true negative.** The correct call
(`.../EntityCommonStockSharesOutstanding/shares/CY2020Q1I.json`) returns 4,774 entities. **This is the
ninth-flavour hazard inverted: not a 200 that is wrong, but a 404 that a status check turns into
data.**

---

## 6. WHAT IS NOT IN XBRL THAT COMPUSTAT HAS

### 6.1 No standardisation. Measured.

**[MEASURED IN BRIEF]** from `tag.txt` and `num.txt`:

| quarter | distinct tags | **custom (filer-invented)** | standard | **% of primary-statement FACTS on custom tags** |
|---|---|---|---|---|
| 2012q2 | 93,938 | 85,293 | 8,645 | **90.8% of tags** / **10.6% of facts** |
| 2015q2 | 70,490 | 60,215 | 10,275 | 85.4% / **7.3%** |
| 2019q2 | 76,812 | 66,238 | 10,574 | 86.2% / **8.1%** |
| 2026q2 | 92,731 | 83,190 | 9,541 | 89.7% / **8.5%** |

**~86–91% of the distinct tags in any quarter are extensions invented by a single filer, carrying
7–11% of all primary-financial-statement facts.** That is the standardisation gap in one number.
Compustat's whole product is the resolution of those 83,000 extensions into ~1,000 defined fields.
**XBRL hands you the 83,000.**

Du, Huddart & Jiang put a complementary number on it: "according to the 2020 edition of the taxonomy,
there are 643 unique balance sheet tags, 574 unique …" [WORKING PAPER] [read in full for that
passage].

### 6.2 The specific things that are absent

1. **Industry normalisation.** The only free classification is `sic` as of the filing date. **No
   GICS, no Compustat industry format.** In particular, Compustat maintains *distinct balance-sheet
   formats* for financials, utilities and industrials; XBRL does not, so `AssetsCurrent` /
   `LiabilitiesCurrent` are simply absent for banks (measured: SVB Financial's 641 `us-gaap`
   concepts include neither `Revenues` nor a current/non-current split). **Any working-capital or
   current-ratio signal silently drops the entire financial sector rather than erroring.**
2. **No point-in-time snapshot files.** There is no "as of date *X*, here is the cross-section"
   artefact. You assemble it — 70 FSDS zips or ~6,000 `companyfacts` documents with a `filed` filter.
   **That assembly is the deliverable Compustat's PIT product sells.**
3. **No split adjustment, anywhere.** XBRL share counts and per-share items are **as reported**.
   There is no split history in any XBRL product. **Every per-share and share-count signal requires
   the programme's separate corporate-actions feed.**
4. **No calendar alignment.** `frames` attempts it and the documentation warns about the result:
   "Because company financial calendars can start and end on any month or day and even change in
   length from quarter to quarter … Data users should be mindful different reporting start and end
   dates for facts contained in a frame." Measured instance: Bed Bath & Beyond appears in the
   `CY2020Q2I` frame with `end=2020-05-30`. **A 52/53-week retailer's fiscal quarter lands in a
   calendar bucket up to a month away.**
5. **No segment or dimensional data in the APIs** (§1.2). Since December 2024 the FSDS carries
   rendered dimensional rows in `segments`, but only what appears on the *primary statements*.
6. **No derived fields** the anomaly literature assumes: Compustat-definition book equity (with
   preferred stock, deferred taxes and investment tax credits), the operating/financial asset split
   for net operating assets, sales-adjusted and industry-demeaned variants, income before
   extraordinary items on a consistent basis, or a filled-forward quarterly series.
7. **No analyst, holdings, options or short data of any kind** — not a gap in XBRL, just not its
   subject.

### 6.3 THE DOCUMENTATION IS BEHIND THE DATA. Two measured conflicts.

**Conflict 1 — the NUM schema.** `aqfs.pdf` Figure 4 documents **nine** NUM fields:
`adsh, tag, version, coreg, ddate, qtrs, uom, value, footnote`. The actual header, measured identically
in 2012q2, 2021q2 and 2026q2:

```
adsh  tag  version  ddate  qtrs  uom  segments  coreg  value  footnote
```

**Ten fields, with `segments` inserted between `uom` and `coreg` — and the PDF does not mention it.**
The landing page does ("a new field 'segments' has been added"), the table definition does not.
**A fixed-position parser written from the documented schema misaligns `coreg`, `value` and
`footnote`.** I weight the data.

**Conflict 2 — form scope** (§1.2). I weight the data.

### 6.4 THE WHOLE HISTORICAL ARCHIVE WAS REPROCESSED ON 2024-12-27

Measured `Last-Modified` headers: `2026q2.zip` → `Wed, 19 Aug 2026`; **every** older zip I downloaded
(2009q2, 2010q1–2012q1, 2013q2, 2015q2, 2018q2–2022q1, 2024q2) → **`Fri, 27 Dec 2024`**. The landing
page explains:

> "Note: In December 2024, reprocessed Financial Statement Data Sets were posted. The Financial
> Statements Data Sets were refreshed to only include the submissions and the numeric data from the
> primary financial statements as rendered by the Commission. Previously, the data sets were compiled
> to present only data that was applicable to the entire filing entity (non-dimensional) or for a
> co-registrant."

**The extraction rule changed retroactively for the entire 2009–2024 archive.** The 2012q2 file
downloaded today is **not** the file a researcher had in 2013: it now includes dimensional rows and
excludes non-rendered ones. **A study replicated against "the FSDS" without recording a download date
is not replicable.** The Notes sets carry their own list of retroactive corrections (2010q1–2013q4
updated 2024-09-26; 2011q1–2013q4 updated 2024-04-01; 2019q1 updated 2021-06-15 for 67 rows).
**Record the `Last-Modified` of every zip you ingest.**

### 6.5 THE EXTERNAL EVIDENCE CUTS AGAINST PESSIMISM ON ONE FAMILY

[WORKING PAPER] **Du, Kai; Huddart, Steven; Jiang, Xin Daniel — "Lost in Standardization: Revisiting
Accounting-based Return Anomalies Using As-filed Financial Statement Data", draft September 2021.**
Downloaded (832,045 bytes, `sha256_12=11d7b87ab5b8`) from Columbia Business School / CEASA and
extracted locally with pypdf; 64 pages. **[read in full] for the abstract, §1, §2.1, §5.4 and
Appendix C.1; [snippet only] for the tables, which I located by line but did not read cell by cell.**

Abstract, verbatim:

> "Discrepancies between as-filed and Compustat data, potentially a result of Compustat's
> standardizations, affect inferences about the existence and magnitude of the accruals anomaly:
> accruals calculated from as-filed data do predict returns and accruals calculated from Compustat
> data do not."

Their numbers, quoted from the body text rather than the tables:

- Sample **2012–2018**, portfolios formed **30 June of each year t from 2013 to 2019**, quintile
  sorts on accruals.
- **Compustat hedge portfolio excess return 0.296%/month** — "not significantly different from zero".
- **As-filed hedge portfolio excess return 0.673%/month** — "more than twice the Compustat raw
  return".
- A control hedge portfolio built where "Compustat disagrees with as-filed data in the classification
  of extreme quintiles" returns **−0.844%, t = −2.72**.
- FactSet substituted for Compustat **does** show the anomaly but smaller — "divergent
  standardization practices among commercial data aggregators".
- Of **19 other** anomalies taken from Green et al. (2017) and Hou, Xue & Zhang (2020), **four** are
  affected: **Ou & Penman (1989) earnings-before-depreciation-to-debt; Fairfield, Whisenant & Yohn
  (2003) growth in long-term net operating assets; Fama & French (2015) / Ball et al. (2016)
  operating profitability; Lev & Nissim (2004) taxable income.** Their stated reason: those five
  "involve data items that are more deeply embedded in the financial statements", i.e. Compustat's
  adjustments bite where its collection task is hardest. **Fifteen of the nineteen are unaffected.**

**Their data sources are exactly the free ones in this brief, plus one more:** "Our 'as-filed'
financial statement data are based on the Financial Statement and Notes Data Sets compiled by the
SEC", together with "the annual U.S. GAAP taxonomy for the years 2009 to 2019 from the FASB's
website" — used to impute a missing high-level tag from its children via the **calculation linkbase**.
They state the mapping is "unambiguous and is not subject to the researcher's discretion" because the
linkbase encodes the accounting identities. **That is the method for §5.4's under-tagging problem, and
it is free.**

**[PEER-REVIEWED]** supporting, **[abstract only]** via search result text and the SSRN listing, **not
opened**: Chychyla, R. & Kogan, A., "Using XBRL to Conduct a Large-Scale Study of Discrepancies
between the Accounting Numbers in Compustat and SEC 10-K Filings", *Journal of Information Systems*
29(1), 2015 — reported as comparing 30 accounting items for ~5,000 companies over 2011-10-01 to
2012-09-30 and finding **17 of 30** Compustat variables differ from the XBRL filings. **I did not open
this paper and the figures are from a summariser, which under this campaign's rules is weaker than a
snippet. Treat them as unverified.** Du, Huddart & Jiang cite it (line 249) alongside Bostwick (2016)
and Boritz & No (2020), which is the only corroboration I have.

**How I would weight this.** The Du/Huddart/Jiang result is a single unpublished working paper on a
seven-year sample, it is a *relative* claim (as-filed beats Compustat) not an absolute one about
tradeability, and **0.673%/month gross on an annually-rebalanced quintile hedge says nothing about
this programme's long-only, ~10-effective-instrument, overnight book.** What it *does* establish, and
this is the part that matters for the lane, is that **the free as-filed data are of research grade —
good enough that a peer-reviewed-track paper built its main result on them and argued they are
*better* than the paid alternative for five named signals.** That retires the assumption that free
fundamentals are a degraded substitute.

---

## 7. THE PAYOFF — WHICH SIGNALS BECOME COMPUTABLE

Each row states the tags actually needed and the specific obstacle measured in this brief. "Price
panel" means the daily OHLCV the programme already holds. Everything here assumes the PIT
reconstruction of §2.2/§2.3, a tag-family fallback chain per §5.4, and the identifier bridge of §4.3.

### 7.1 UNLOCKED

| signal | needs | obstacle measured here |
|---|---|---|
| **Asset growth** (Cooper, Gulen & Schill 2008) | `Assets` alone | **ASC 842 FY2019 break (§5.4.5) — must net out `OperatingLeaseRightOfUseAsset`.** Otherwise the cleanest signal in the set. |
| **Accruals** (Sloan 1996), cash-flow form `NI − CFO` | `NetIncomeLoss`, OCF family, `Assets` | Two-tag OCF family 2012–2016 (§5.4.3). **Has direct as-filed evidence (§6.5).** |
| **Gross profitability** (Novy-Marx 2013) | revenue family × COGS family × `Assets` | **Both legs break at FY2018 (§5.4.1–2).** Needs a four-tag revenue chain and a three-tag cost chain. |
| **Operating profitability** (Fama & French 2015; Ball et al. 2016) | + `SellingGeneralAndAdministrativeExpense`, `InterestExpense`, book equity | Named by Du et al. as **standardisation-sensitive**; book equity needs the three-tag equity chain (§5.4.6). |
| **Investment / capex growth** | `PropertyPlantAndEquipmentNet`, `PaymentsToAcquirePropertyPlantAndEquipment` | PP&E tagged by 4,201 filers in 2025, falling — the thinnest of the headline balance-sheet tags. |
| **Book-to-market** | `StockholdersEquity` (+NCI variant) × price panel | No Compustat-definition book equity (preferred, deferred taxes) — **a different variable, not the same one.** |
| **Net operating assets / growth in long-term NOA** (Hirshleifer et al. 2004; Fairfield et al. 2003) | full balance-sheet operating/financial split | **No such split in XBRL**; derivable, fragile, and Du et al. name growth-in-LTNOA as standardisation-sensitive. |
| **Distress / failure probability** (Campbell, Hilscher & Szilagyi 2008), O-score, Z-score, **Piotroski F-score** | the above plus `Liabilities` (derived), `CashAndCashEquivalents*` family | Every input is available; every input has a family problem. F-score's nine binaries each inherit one. |
| **Taxable income** (Lev & Nissim 2004) | `IncomeTaxExpenseBenefit` + current/deferred split | Named standardisation-sensitive. |
| **Change in asset turnover, cash-flow-to-price, earnings-to-price** | above × price panel | Same families. |
| **Point-in-time size and industry**, as *controls* rather than signals | `pubfloatusd`/`floatdate` (Notes `sub.tsv`), `dei:EntityPublicFloat`, `sic`-at-filing | **A genuinely useful free by-product.** `EntityPublicFloat` measured at 4,987 entities in `CY2012Q2I`, one observation per issuer per year, and present for dead issuers (BBBY: 2008-08-30 through 2014-08-30 measured). |

### 7.2 NOT UNLOCKED

| signal | why not |
|---|---|
| **Net share issuance / composite equity issuance** (Pontiff & Woodgate; Daniel & Titman) | Needs **split-adjusted** share counts. XBRL has no split history at all (§6.2.3). Requires the corporate-actions feed as a hard dependency. Also `dei:EntityCommonStockSharesOutstanding` is dated at the **cover-page date**, not the fiscal period end — a mismatched timestamp on top of the split problem. |
| **Segment-level signals** (segment profitability dispersion, geographic mix, segment growth) | Excluded from the APIs by design (§1.2). Post-Dec-2024 FSDS `segments` carries only what is *rendered on the primary statements* — not the segment footnote. The Notes sets would carry more; I did not test whether the segment footnote is reconstructible (§9.3). |
| **Anything needing analyst forecasts, institutional holdings, short interest, options, or intraday data** | Not in XBRL. Three of these are on the exclusion list in any case. |
| **Anything needing pre-2011 fundamentals for small and mid names** | §5.2. Roughly the first 870 bars of the programme's window, ~21%, are large-accelerated-only. |
| **Anything needing pre-2009 fundamentals at all** | XBRL does not exist. Lehman and Enron return 404 and this is not fixable from any free SEC product. |
| **A complete real-time cross-section from the bulk files** | FSDS lag is ~50 days plus up to a quarter of queueing (§1.4). For live use the APIs are the only route, which means ~6,000 `companyfacts` documents — a 2.1–4.3 MB each, ~20 GB per full refresh, against the nightly `companyfacts.zip` mirror. |

### 7.3 The verdict in one paragraph

**Seven of the ten strongest survivors need Compustat-style fundamentals; most of the *families* those
seven come from are computable from free SEC XBRL, point-in-time, dead-inclusive, from roughly
mid-2011 for the full universe and from 2010 for large accelerated filers only.** The exceptions are
issuance (needs split history) and anything segment-level. **The price of entry is not the download —
it is a tag-family fallback chain per concept, a FASB-calculation-linkbase imputation step for
under-tagged high-level concepts, an identifier bridge assembled from two heuristics at ~95%, and a
corporate-identity break detector for the Hertz case.** That is weeks of engineering, not an
afternoon, and **three of its four failure modes are silent**: the frames look-ahead returns a
plausible cross-section, the `filed`-date look-ahead returns plausible dates, and a single-tag revenue
series returns a plausible but decimated panel. **None of them error.**

---

## 8. SOURCES

**[PRIMARY DATA DOC]**
1. *EDGAR Application Programming Interfaces* — `https://www.sec.gov/search-filings/edgar-application-programming-interfaces` (68,430 B, `sha256_12=c64e523e39a6`, Last-Modified 2026-09-09). **[read in full]**
2. *Financial Statement Data Sets* landing page — `https://www.sec.gov/data-research/sec-markets-data/financial-statement-data-sets` (121,116 B). **[read in full]**
3. *Financial Statement Data Sets* documentation PDF — `https://www.sec.gov/files/aqfs.pdf` (189,267 B, `sha256_12=de96d6ea5030`, 9 pages, extracted with pypdf 6.16.2). **[read in full]**
4. *Financial Statement and Notes Data Sets* landing page — `https://www.sec.gov/data-research/sec-markets-data/financial-statement-notes-data-sets` (130,345 B). **[read in full]**
5. *Operating Company Inline XBRL Filing of Tagged Data* (Small Entity Compliance Guide) — `https://www.sec.gov/resources-small-businesses/small-business-compliance-guides/operating-company-inline-xbrl-filing-tagged-data` (69,075 B). **[read in full]**

**[WORKING PAPER]**
6. Du, K., Huddart, S., Jiang, X.D. — *Lost in Standardization: Revisiting Accounting-based Return Anomalies Using As-filed Financial Statement Data*, draft September 2021. `https://business.columbia.edu/sites/default/files-efs/imce-uploads/CEASA/Events%20Page/revisiting_accounting-based_return_anomalies.pdf` (832,045 B, `sha256_12=11d7b87ab5b8`, 64 pages). **[read in full] for abstract, §1, §2.1, §5.4, Appendix C.1; [snippet only] for the tables.**

**[PEER-REVIEWED] [abstract only — NOT OPENED, figures from a summariser and therefore UNVERIFIED]**
7. Chychyla, R. & Kogan, A., *Journal of Information Systems* 29(1), 2015 — "Using XBRL to Conduct a Large-Scale Study of Discrepancies between the Accounting Numbers in Compustat and SEC 10-K Filings". Located at `https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2304473` and `https://publications.aaahq.org/jis/article-abstract/29/1/37/1076/`.

**[MEASURED IN BRIEF]** — all endpoints named inline. Helper and probe scripts, all prefixed `A1_`,
are in session scratch at
`…/268972c6-b281-4926-b9db-c5611e52a2c6/scratchpad/A1_work/` (`A1_fetch.py` is the paced fetcher;
`A1_probe1`…`A1_probe22` are the measurements). Derived evidence this brief quotes is copied to
[`data/`](../../../data/) as `A1_tag_census.json` (the full §5.4 matrix, 29 tags × 18 years) and
`A1_measurement_logs.txt`.

**BLOCKS, logged by tool and response.** **None.** Every `sec.gov` and `data.sec.gov` request returned
200 or a genuine 404 with an XML `NoSuchKey` body. No 403, no 429, no CAPTCHA, no robots refusal. The
Columbia PDF returned 200. No summariser tool returned a "corrupted PDF" or a block. **No page I
fetched contained text addressed to a researcher or instructing an action** — the only imperative
language encountered was the SEC's own "Send your recommendations regarding how we are implementing
our APIs to webmaster@sec.gov", which is ordinary page content and was not acted on.

**Pacing.** Single process, ≥0.22 s between requests across all `sec.gov` hosts, well inside the
10 req/s fair-access limit. Total downloaded ≈ 2.5 GB (20 FSDS zips, 3 Notes zips, ~700 frames calls,
~250 submissions/companyfacts documents). **No unpaced threads were used at any point.**

---

## 9. WHAT I COULD NOT VERIFY, STATED PLAINLY

1. **The false-positive rate of the `instance`-prefix ticker heuristic.** I measured how often the
   prefix *looks like* a ticker (66.6–99.7%) and confirmed it is *correct* for five named issuers. I
   did **not** measure how often a ticker-shaped prefix is the wrong ticker, a subsidiary's ticker, or
   a stale ticker after a change. **The 94.5–97.4% union figure in §4.3 is a coverage rate, not an
   accuracy rate, and the difference could be material.** Validating it needs a dead-inclusive
   ground-truth ticker history, which is the very thing the programme does not have.
2. **Whether the `acceptanceDateTime` timezone defect was fixed, and when.** I measured 40.2%
   mislabelled in `2021q2` and 0 of 88 in `2026q2`. **Two quarters are not a history.** I did not
   sweep intermediate years, so I cannot date the change, cannot rule out that it recurs, and cannot
   rule out that `2026q2` is simply a favourable draw (0/88 is consistent with a true rate up to ~3%
   at 95% confidence). **Any code depending on that field should assume the defect is live.**
3. **Whether the segment footnote is reconstructible from the Notes Data Sets.** I confirmed the
   APIs exclude dimensional facts and that the post-2024 FSDS `segments` column carries only
   primary-statement dimensions. The Notes sets contain `dim.tsv` (61.6 MB in `2026_08`) and I read
   its existence but **did not parse it**, so I cannot say whether a usable segment panel is
   extractable. **This is the single largest unexplored capability in the lane.**
4. **The identity of the 5,981-day `period`→`filed` outlier**, and therefore whether it is a
   delinquent catch-up, a transition-period filing, or a corrupt `period` field. I measured the
   maximum and did not look at the row. **Per this programme's own rule, a concentration statistic is
   not finished until the top item is named — this one is not named.**
5. **Population base rates for restatement magnitude.** §2.6's 2.8–34.9% figures are on six
   deliberately selected issuers and mix restatement with reclassification and ASU adoption. **The
   only population figure I have is the ~5% `prevrpt` amendment rate.** A real base rate needs a
   full-archive pass over all 70 FSDS zips, which I did not run.
6. **Whether `companyfacts` ever *omits* an original vintage.** I verified non-deduplication on
   several named cases and verified the original 10-Q value is present for Plug Power. I did **not**
   systematically test for vintages present in the FSDS zips but absent from `companyfacts` — which
   is the failure mode that would silently break the §2.2 reconstruction. **A cross-product
   reconciliation (FSDS `num.txt` vs `companyfacts`, same CIK, same concept, same period) would
   settle it and I did not run one.**
7. **Anything about the quality of the FASB calculation-linkbase imputation** that Du, Huddart &
   Jiang rely on for under-tagged high-level concepts. I read their description of it; I did not
   download a taxonomy or test the imputation. **Their claim that the mapping "is not subject to the
   researcher's discretion" is their claim, not my measurement.**
8. **The Chychyla & Kogan figures** (30 items, ~5,000 companies, 17 of 30 differing). **From a
   summariser, paper not opened.** Under this campaign's rules that is weaker than a snippet.
9. **Whether any of this produces a tradeable edge for *this* book.** Nothing in this brief is a
   return measurement. The one external return figure I carry (0.673%/month) is a gross,
   annually-rebalanced, two-sided quintile hedge on a 2013–2019 formation window — **a different
   statistic for a different book, and this programme's long-only, overnight, ~10-effective-instrument
   shape is not what it measures.** §7 says what becomes *computable*, which is not the same as what
   becomes *profitable*.
10. **IFRS filers.** `ifrs/2025` appears with 1,006 standard tags in `2026q2` and I did not examine
    `ifrs-full` coverage or whether 20-F/40-F filers are usable. If the programme's universe includes
    foreign private issuers on US exchanges, that is an unexamined slice.
