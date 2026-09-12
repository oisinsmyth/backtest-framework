# K3 — The earnings-absorption census across all 8-K item codes

**Measurement on public data. Not a signal hunt.** No private data was accessed
and nothing here claims anything about the programme's own fixtures.

Date of harvest: 2026-09-10. Data vintage: `submissions.zip` rebuilt
2026-09-09, containing filings through **2026-09-08**.

Contact string used in every request: `Backtest-Framework-Research
research@backtest-framework.org`.

---

## 0. Headline, including the part that spoils the premise

1. **The census is complete, not sampled.** Every one of the **1,185,352**
   form 8-K submissions filed 2010-01-01 to 2026-09-08, keyed on CIK,
   dead-inclusive. Sampling error is therefore zero; the residual risks are
   route error and field error, both controlled below.
2. **At item-code granularity, absorption into the earnings submission is
   SMALL and only mildly rising.** The substantive event codes the programme
   would want — 5.02 officer changes, 1.01 material agreements, 2.03 debt,
   3.02 unregistered equity, 5.07 vote results — co-file with Item 2.02 in
   **1–4.5%** of cases, rising by only **+0.3 to +1.5 pp** over sixteen years.
   They are still separately dated.
3. **The one clean, large, monotone trend is Item 7.01 (Reg FD).** Its share of
   Item 2.02 submissions rose from **12.85% to 24.04%**, increasing in
   **16 of 16** consecutive year-on-year steps (smallest step +0.06 pp, at
   2018→2019 — so "monotone" is true but one step is effectively flat). It
   survives a constant-issuer panel, so it is within-issuer behaviour change,
   not composition.
4. **THE COMMISSIONING PREMISE DOES NOT TRANSFER, AND THIS IS THE MOST
   IMPORTANT LINE IN THE BRIEF.** Dividend initiations, dividend cuts and
   stock splits **have no 8-K item code**. There is no Item for them. They are
   free text inside the body of a filing tagged 8.01, 7.01 and/or 2.02. A
   census of the `items` field therefore **cannot reproduce, confirm or refute**
   the 62.2% / 59.2% / 36–68% figures from last round. Those two lanes measured
   a *text-identified event class*; I measured *item codes*. **Different
   objects.** My census is not the screen that would have caught those lanes,
   and I should not be read as if it were. See §7.
5. **A negative control killed the route the brief suggested first.** EDGAR
   full-text search's `items` filter does not exist. Passing
   `items=9.99` — an impossible code — returned exactly the same count as
   passing nothing. Details in §1a.
6. **Controls, in one line each.** Eleven impossible item codes → **zero in
   every year**. Census denominator vs an independent SEC route → **exact, 0
   discrepancy across 163,634 filings**. 12-way parallel harvest vs a
   single-process rerun → **bit-identical, sha256 match**, and the check was
   proved able to fail. Bulk archive vs live API → **1,010 of 1,010 fields
   identical**. Per-filing `items` vs EDGAR's own index pages → **33 of 33**.
   Dead-inclusive → **45.2% of 2010 filers are gone by 2015**. Headline trend on
   a constant issuer panel → **survives**.
7. **Bonus: the programme's `acceptanceDateTime` defect is REPRODUCED, and the
   reason two of my own samples denied it is worth recording.** On 51 filings
   across 33 CIKs, **32 (62.7%) carry Eastern wall clock mislabelled as `Z`** —
   consistent with the programme's 35/60. Two earlier samples of mine returned
   0% because they were concentrated in a few large filers. Neither filer agent
   nor era predicts the defect reliably. **No number in this census is affected**
   — it buckets on `filingDate` and never parses a timestamp. §3h.

---

## 1. Route: what I tried, what failed, and what I used

### 1a. EDGAR full-text search — REJECTED, caught by negative control

**Source type:** live API. **How well established:** [MEASURED IN BRIEF],
decisive.

Endpoint `https://efts.sec.gov/LATEST/search-index`. The commissioning brief
stated that "EDGAR full-text search exposes an items filter". **I could not
confirm that and the evidence says it does not.** Every variant returned an
identical count for 2023-01-01..2023-01-31, `forms=8-K`:

| query | `hits.total.value` |
|---|---|
| `forms=8-K` (no items filter) | 1070 |
| `forms=8-K&items=2.02` | 1070 |
| `forms=8-K&items=5.02` | 1070 |
| `forms=8-K&items=2.02,5.02` | 1070 |
| `forms=8-K&items=2.02&items=5.02` | 1070 |
| **`forms=8-K&items=9.99` (IMPOSSIBLE CODE)** | **1070** |

The `items` parameter is a **silent no-op**: it is accepted, returns HTTP 200,
and changes nothing. Had I censused on this route I would have published the
same number for every item code and every year.

Two further checks confirmed the rejection rather than guessing at it:

- Other parameters on the same endpoint **do** work — `startdt/enddt` and
  `forms` change the count (2015-01 → 5721; `forms=10-K` → 121), and omitting
  `forms` and `q` returns the error `"Blank search not valid. Either entity,
  keywords, location, or filing types must be submitted."` So the endpoint is
  live and parameter-sensitive; `items` specifically is ignored.
- The count itself is wrong for a filing census anyway. EFTS indexes
  **`_index: edgar_file`** — one hit per *document*, not per submission. Its
  1070 for exactly 2023-01-01..2023-01-31 is irreconcilable with the same month
  measured on the route I did use: **5,049 unique accessions / 5,150 unique
  (CIK, accession) pairs**. EFTS reports about a fifth of the filings that
  exist, while indexing documents rather than filings, which should push it
  *up*, not down. Whatever `hits.total.value` is counting on a query with no
  `q`, it is not 8-K filings. [MEASURED IN BRIEF]
- I fetched the EDGAR full-text search UI at `https://www.sec.gov/edgar/search/`
  and grepped its markup for any item-filter control. There is none; every
  `item`-like string is site navigation (`menu__item`, `nav-item`). **[MEASURED
  IN BRIEF]**

Recorded as a conflict, not adjudicated: the brief asserts this filter exists;
I find it absent. It is possible a filter exists under a parameter name I did
not guess. I tried `items` only, in the five forms above.

### 1b. `submissions.zip` — USED

**Source type:** SEC bulk data archive, documented on
`https://www.sec.gov/search-filings/edgar-application-programming-interfaces`.
**How well established:** documented by SEC primary page AND validated by exact
agreement with a second independent SEC route (§3b). Strong.

The SEC page states submissions.zip *"contains the public EDGAR filing history
for all filers from the Submissions API"* and that it is *"recompiled nightly"*.

Exact retrieval, re-runnable:

```
GET https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip
    User-Agent: Backtest-Framework-Research research@backtest-framework.org
-> HTTP 200, Content-Length 1562536756, Last-Modified Wed, 09 Sep 2026 04:33:34 GMT
-> received exactly 1562536756 bytes in 708 s (2.2 MB/s)
-> 989,363 members (989,362 × *.json + placeholder.txt)
```

Member layout, confirmed against a live single-CIK fetch of
`https://data.sec.gov/submissions/CIK0000106640.json`:

- `CIK##########.json` — arrays under `filings.recent`
- `CIK##########-submissions-00N.json` — the same columnar arrays at top level

The fields used: `accessionNumber`, `filingDate`, `form`, `items`. **`items` is
a comma-separated STRING** (e.g. `"2.02,9.01"`), not an array — worth noting
since the commissioning brief described it as a field "carrying comma-separated
codes", which is right, but a naive `for code in items` would iterate
characters.

**Why this route and not per-CIK live fetches:** one request instead of ~20,000,
it is the same data the Submissions API serves, and it covers every filer that
ever filed rather than a ticker-keyed survivor list.

### 1c. Why the census is keyed on CIK and is dead-inclusive

`submissions.zip` is organised by CIK, not ticker, so the survivors-only defect
of `company_tickers.json` does not apply. Verified rather than assumed
(§3d): **45.2%** of the 9,130 distinct CIKs that filed an 8-K in 2010 filed no
8-K after 2015. A survivors-only source would show ≈0%.

---

## 2. Method

One pass over all 989,362 JSON members, extracting every filing whose `form`
begins `8-K`. 12 worker processes striding `namelist()[i::12]` (GIL-bound pure
Python JSON parsing, so processes not threads; stride not slice because member
sizes vary by orders of magnitude). Wall time **19 s**, 2,174,482 rows, zero
parse failures.

**De-duplication.** A single accession appears in the submissions file of
*every* co-registrant CIK. Raw rows therefore over-count submissions. The
census de-duplicates on accession number: 2,113,419 unique 8-K-family
submissions all years, **61,063** co-registrant duplicate records dropped.
Both the de-duplicated and raw counts are reported in §3b because they answer
different questions and the discrepancy is itself a control.

**Year bucketing uses `filingDate`, a DATE.** This is deliberate: the
programme has flagged `acceptanceDateTime` as timezone-inconsistent, so the
census is built to not depend on any timestamp. See §5 for what I found when I
tested the timestamp anyway. `reportDate` exists in the JSON and was **not**
used; a census on `reportDate` would differ at year boundaries and I did not
build it.

**Scope.** Tables cover `form == "8-K"` only. The amendment and successor forms
(`8-K/A` 35,900; `8-K12B` 346; `8-K12G3` 156; `8-K15D5` 10; plus 56 amendments
of those) are counted in §3c but excluded from T1–T6, because an amendment's
item codes describe the original event and would double-count it.

**Window.** 2010–2026. The whole window post-dates the August 23, 2004
restructuring of Form 8-K into the current decimal item scheme (effective date
confirmed from SEC release 33-8400). Pre-2004 filings in the archive do use
the old single-digit scheme — I observed `items` values like `"5,7"` on 2001
filings — and **none leak into the window**: all 33 codes observed in
2010–2026 are decimal.

---

## 3. Controls

### 3a. NEGATIVE CONTROL — impossible item codes [MEASURED IN BRIEF]

Eleven codes that do not exist in Form 8-K were censused identically to the
real ones. **Every one returns zero in every year 2010–2026:**

`9.99`, `2.99`, `1.99`, `0.00`, `10.01`, `3.99`, `7.99`, `4.99`, `2.07`,
`5.10`, `6.07` — **ZERO, all years.**

Note the design: `2.07`, `5.10` and `6.07` are *plausible-looking* codes
adjacent to real ones (2.06 and 5.08 and 6.06 exist), so the control is not
satisfied merely by rejecting obvious garbage.

Corroborating evidence that the code universe is real rather than whatever the
route felt like returning: exactly **33** distinct codes appear, and a
programmatic set-equality assertion confirms they are precisely the Form 8-K
universe — 1.01–1.05, 2.01–2.06, 3.01–3.03, 4.01–4.02, 5.01–5.08, 6.01–6.06,
7.01, 8.01, 9.01 — with **no missing codes and no extras**. And
**Item 1.05 (material cybersecurity incidents, effective December 2023) first
appears in 2023 with 2 filings, then 24 / 15 / 16** — a code that did not exist
before 2023 correctly shows zero before 2023. That is a negative control the
data generated for me.

### 3b. POSITIVE CONTROL — exact agreement with a second SEC route [MEASURED IN BRIEF]

Route A: `https://www.sec.gov/Archives/edgar/full-index/<YYYY>/QTR<n>/form.idx`
— built from the EDGAR dissemination feed, sharing no code path with
data.sec.gov. Each file's own `Last Data Received:` header matched the quarter
requested in all nine cases, so this also rules out a CDN replaying one
query's body for another.

Route B: submissions.zip, unique **(CIK, accession)** pairs.
Route C: submissions.zip, unique **accessions**.

| quarter | A: form.idx | B: pairs | C: accessions | B−A | C−A |
|---|---|---|---|---|---|
| 2010 Q1 | 19918 | 19918 | 19480 | **0** | −438 |
| 2010 Q3 | 18686 | 18686 | 18304 | **0** | −382 |
| 2015 Q1 | 19252 | 19252 | 18746 | **0** | −506 |
| 2015 Q3 | 17771 | 17771 | 17272 | **0** | −499 |
| 2020 Q1 | 17631 | 17631 | 17179 | **0** | −452 |
| 2023 Q1 | 18122 | 18122 | 17752 | **0** | −370 |
| 2024 Q2 | 19546 | 19546 | 19174 | **0** | −372 |
| 2025 Q1 | 16723 | 16723 | 16352 | **0** | −371 |
| 2026 Q1 | 15985 | 15985 | 15618 | **0** | −367 |
| **TOTAL** | **163634** | **163634** | **159877** | **0 (+0.000%)** | −3757 (−2.296%) |

Route B matches route A **to the filing, in every quarter, across 163,634
filings**. That is the strongest form this control can take. Route C is
2.296% lower, which is exactly the co-registrant multiplicity that route B
includes and route C collapses — i.e. the discrepancy is explained and
quantified, not waved at. The ratio tables T2/T5 are unaffected by the choice
because numerator and denominator are both on route C.

### 3c. Chunk == whole, bit-identically [MEASURED IN BRIEF]

Worker stderr was lost to a shell append race, so the "all 12 workers
completed" claim had no evidence. Replaced with a real check: the whole zip was
re-harvested in **one** process and the row multiset compared to the union of
the 12 striped outputs.

```
members read (single process): 989362
rows whole  : 2174482
rows chunked: 2174482
sha256 whole  : d2cd0ed58efe7a13f2cb0c0196841ccbcfc7cd4371e9725bed3b83ac1771078e
sha256 chunked: d2cd0ed58efe7a13f2cb0c0196841ccbcfc7cd4371e9725bed3b83ac1771078e
RESULT: chunk == whole, BIT-IDENTICAL over 2174482 rows
```

**And the check was proved capable of failing**: dropping one row → detected;
mutating one row's form from `8-K` to `8-K/A` → detected. A self-test that
cannot fail is worse than none.

8-K family form types in window (these are the counts T1–T6 exclude, except
`8-K`):

| form | 2010–2026 | all years |
|---|---|---|
| `8-K` | 1,185,352 | 2,027,300 |
| `8-K/A` | 35,900 | 84,856 |
| `8-K12B` | 346 | 379 |
| `8-K12G3` | 156 | 650 |
| `8-K12G3/A` | 17 | 116 |
| `8-K15D5` | 10 | 72 |
| `8-K12B/A` | 37 | 42 |
| `8-K15D5/A` | 2 | 4 |

### 3d. Dead-inclusive control [MEASURED IN BRIEF]

- distinct CIKs filing an 8-K in 2010: **9,130**
- of those, CIKs with no 8-K after 2015: **4,125 (45.2%)**
- distinct CIKs, all years in window: **19,995**

A survivors-only panel would show ≈0% in line 2. The census is dead-inclusive.

### 3e. Composition control on the headline trend [MEASURED IN BRIEF]

The 7.01 trend could be issuers entering and leaving rather than issuers
changing behaviour. Restricting to the **2,342 CIKs that filed an Item 2.02
8-K in both 2010–12 and 2023–25**:

| panel | 2010–12 | 2023–25 | delta |
|---|---|---|---|
| all issuers | 13.48% (n=57,475) | 22.64% (n=53,453) | **+9.16 pp** |
| constant 2,342-CIK panel | 14.47% (n=27,701) | 22.96% (n=27,584) | **+8.49 pp** |

The trend is within-issuer. Same for mean codes per 2.02 filing (all issuers
2.2116 → 2.3389; constant panel 2.2117 → 2.3340) and for 8.01 (all +1.46 pp;
panel +1.72 pp).

### 3f. Field-integrity control

Only **2** form 8-K filings in the entire 17-year window have an empty `items`
field (both 2011). The field is essentially never missing, so the census has no
meaningful "unknown" bucket.

**PER-FILING `items` CROSS-CHECK [MEASURED IN BRIEF].** The whole census rests
on the `items` field being a faithful record of the filing's actual item codes.
For one real filing per observed code, I fetched the filing's own EDGAR
filing-index page and compared the item list rendered there against the
submissions JSON's `items` string:

```
per-filing items cross-check: 33 agree / 0 disagree
```

**33 filings, 33 exact agreements, zero disagreements** (32 in the automated
pass plus 4.01 on a retry after an HTTP 503), including several multi-code
filings where an ordering or truncation defect would have shown — e.g.
`1.03,2.01,3.03,5.01,5.02,8.01,9.01`,
`1.02,2.01,3.01,3.03,5.01,5.02,5.03,9.01`, and the 14-code filing in §6, which
matched on all 14. This is the check that matters most and it passes; the limits
of what it establishes are in §10.2.

**Bulk archive vs live Submissions API [MEASURED IN BRIEF].** The archive could
in principle be a stale or lossy rebuild of what the API serves. For
CIK 0000106640 I compared the member `CIK0000106640.json` read out of the zip
against the response fetched live from
`https://data.sec.gov/submissions/CIK0000106640.json`:

```
live accessions: 1010 ; zip accessions: 1010 ; common: 1010
only in live: 0 ; only in zip: 0
field mismatches (form, filingDate, items, reportDate): 0
common 8-K filings: 187 ; `items` disagreements: 0
```

Exact agreement on all four fields for all 1,010 filings, including 187 8-Ks.
**This establishes archive == API. It does NOT establish API == filing** — for
that, see the much thinner evidence in §10.2.

### 3g. Every numeric claim re-derived programmatically [MEASURED IN BRIEF]

`K3_check_claims.py` re-computes from `K3_census.json` every figure asserted in
§0 and §5 and asserts it, rather than leaving the prose to be checked by eye.
It confirms: the 7.01 monotonicity (16/16 steps up, smallest +0.06 pp), the
mean-codes series (15/16 up, the single fall at 2021), the
baseline-rises-faster comparison, total form 8-K = 1,185,352, the 1.05
appearance pattern (2023: 2, then 24/15/16), the 33-code set equality, and each
early-vs-late pair in T3. All assertions pass. Two prose claims were corrected
as a result — the "monotone" claim now discloses its near-flat step, and the
baseline comparison is now stated on full-year 2025 rather than partial 2026.

### 3h. `acceptanceDateTime` timezone control — the programme's finding REPRODUCED [MEASURED IN BRIEF]

The census does not depend on timestamps (it buckets on `filingDate`), but the
brief asked whether the known defect matters for this route, so I tested it.

Method: sample 8-K filings stratified across all 17 years, **capped at 2 filings
per CIK** for issuer diversity; take `acceptanceDateTime` from
submissions.zip; fetch the filing's own dissemination file
`Archives/edgar/data/<cik>/<acc-nodashes>/<acc>.txt` and read its SGML
`<ACCEPTANCE-DATETIME>`, which EDGAR writes in US/Eastern with no zone marker;
compare as a signed hour offset allowing a date rollover.

**Result — 51 filings, 33 distinct CIKs, 2010–2026:**

| offset | meaning | count |
|---|---|---|
| **0.0 h** | **the JSON's `Z` is Eastern wall clock MISLABELLED as UTC** | **32 (62.7%)** |
| +4.0 h | genuine UTC during EDT | 10 |
| +5.0 h | genuine UTC during EST | 9 |
| | genuine UTC, combined | 19 (37.3%) |

**This reproduces the programme's finding** (35 of 60, 58.3% mislabelled) at
62.7% on an independent sample. The defect is real, frequent, and silent.

**Two earlier samples of mine CONTRADICTED it, and the reason is instructive.**
A 12-filing check on one issuer (CIK 106640, 2026) and a 39-filing check that
happened to be dominated by a few large filers both returned **0%** mislabelled.
The difference is sample composition, not measurement: without a per-CIK cap the
sampler concentrated on a handful of high-volume filers whose agents emit
genuine UTC. **A timezone check on a concentrated sample will tell you the
defect does not exist.** I record my own two wrong answers rather than only the
right one.

What predicts it — partially:

| filer-agent prefix (accession first 10 digits) | offsets observed | verdict |
|---|---|---|
| `0001213900` | {0: 8} | all mislabelled |
| `0001193125` | {0: 7, 5: 2, 4: 3} | **MIXED** |
| `0001104659` | {0: 2, 4: 2, 5: 1} | **MIXED** |
| `0001079973`, `0001005229`, `0001144204`, `0001096906`, `0001493152`, `0001013762`, `0000721748`, `0001599916`, `0001079974` | all {0: n} | all mislabelled |
| `0001437749`, `0000709283`, `0001157523`, `0000950123`, `0001062993`, `0000911421`, `0000354950`, `0001572661`, `0000928816` | all {4 or 5} | all genuine UTC |

Of 21 prefixes: 10 purely mislabelled, 9 purely genuine UTC, **2 mixed**. And
era does not rescue it either — within `0001193125` the mislabelled filings are
2013, 2019, 2021 while 2014, 2015, 2016 and 2026 are genuine UTC, which is not
monotone in time. All 9 of my 2024–2026 filings were genuine UTC and no
mislabel appears after 2023, which hints at a fix, but at 3 filings per year
that is far too thin to claim.

**Operational conclusion for the programme: neither filer agent nor era predicts
the defect reliably. Any use of `acceptanceDateTime` needs a per-filing check
against the filing's own SGML header, not a rule.** Nothing in this census is
affected, because it never parses a timestamp.

### 3i. Self-inflicted rate limit — logged by tool and response

**Tool:** Python `urllib.request`. **Response:** `HTTP Error 429: Too Many
Requests`, on all 33 requests of a titles fetch, and on a subsequent single
`curl` probe ~8 minutes later. **Scope:** all of sec.gov, confirming the limit
is cross-host and cumulative, not per-host and not purely instantaneous-rate.
Cause was cumulative volume: a 1.56 GB archive, nine form.idx files
(~25 MB each) and ~25 small requests inside one short window. **No census
number depends on anything that 429'd** — §3a–§3f and all of §4 were already
complete from the single archive. The affected items were item titles and two
extra controls, re-run after a 600 s backoff at 1 request/second (§5).

---

## 4. The census

Form `8-K` only, unique accessions, bucketed on `filingDate` year.
**2026 is PARTIAL** — the archive ends 2026-09-08, so 2026 holds about 69% of a
year (46,490 (CIK, accession) 8-K records vs 67,651 in 2025). Do not read the
2026 column as a full year; read it only as a ratio.

### Item code reference [MEASURED IN BRIEF]

Titles read off EDGAR's own filing-index pages, one real filing per code (not
from memory, not from a summariser). **All 33 retrieved** — 4.01 needed a retry
after an HTTP 503 on the first attempt.

| Code | Title | Code | Title |
|---|---|---|---|
| 1.01 | Entry into a Material Definitive Agreement | 5.01 | Changes in Control of Registrant |
| 1.02 | Termination of a Material Definitive Agreement | 5.02 | Departure of Directors or Certain Officers; Election of Directors; Appointment of Certain Officers: Compensatory Arrangements of Certain Officers |
| 1.03 | Bankruptcy or Receivership | 5.03 | Amendments to Articles of Incorporation or Bylaws; Change in Fiscal Year |
| 1.04 | Mine Safety - Reporting of Shutdowns and Patterns of Violations | 5.04 | Temporary Suspension of Trading Under Registrant's Employee Benefit Plans |
| 1.05 | Material Cybersecurity Incidents | 5.05 | Amendments to the Registrant's Code of Ethics, or Waiver of a Provision of the Code of Ethics |
| 2.01 | Completion of Acquisition or Disposition of Assets | 5.06 | Change in Shell Company Status |
| **2.02** | **Results of Operations and Financial Condition** | 5.07 | Submission of Matters to a Vote of Security Holders |
| 2.03 | Creation of a Direct Financial Obligation or an Obligation under an Off-Balance Sheet Arrangement of a Registrant | 5.08 | Shareholder Nominations Pursuant to Exchange Act Rule 14a-11 |
| 2.04 | Triggering Events That Accelerate or Increase a Direct Financial Obligation or an Obligation under an Off-Balance Sheet Arrangement | 6.01 | ABS Informational and Computational Material |
| 2.05 | Cost Associated with Exit or Disposal Activities | 6.02 | Change of Servicer or Trustee |
| 2.06 | Material Impairments | 6.03 | Change in Credit Enhancement or Other External Support |
| 3.01 | Notice of Delisting or Failure to Satisfy a Continued Listing Rule or Standard; Transfer of Listing | 6.04 | Failure to Make a Required Distribution |
| 3.02 | Unregistered Sales of Equity Securities | 6.05 | Securities Act Updating Disclosure |
| 3.03 | Material Modifications to Rights of Security Holders | 6.06 | Static Pool |
| 4.01 | Changes in Registrant's Certifying Accountant | 7.01 | Regulation FD Disclosure |
| 4.02 | Non-Reliance on Previously Issued Financial Statements or a Related Audit Report or Completed Interim Review | 8.01 | Other Events |
| | | 9.01 | Financial Statements and Exhibits |

Note 6.01–6.06 are **asset-backed securities** items. They are structurally
irrelevant to a US single-name equity programme and their tiny, erratic counts
in T1 should be read as such rather than as thin event samples.

### T1 — Filings carrying each item code, by year

| Item | 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026p | TOTAL |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.01 | 12728 | 12580 | 11746 | 11849 | 12199 | 11881 | 11013 | 11101 | 10390 | 9952 | 11010 | 12455 | 9918 | 10551 | 10664 | 10762 | 6974 | 187773 |
| 1.02 | 1248 | 1337 | 1176 | 1021 | 1129 | 1114 | 1084 | 1058 | 1072 | 920 | 956 | 1125 | 1032 | 1006 | 928 | 983 | 656 | 17845 |
| 1.03 | 198 | 157 | 123 | 117 | 109 | 100 | 166 | 113 | 82 | 110 | 172 | 69 | 40 | 156 | 156 | 87 | 48 | 2003 |
| 1.04 | 0 | 1 | 58 | 31 | 41 | 25 | 12 | 15 | 11 | 16 | 8 | 10 | 11 | 10 | 10 | 10 | 16 | 285 |
| 1.05 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 24 | 15 | 16 | 57 |
| 2.01 | 1924 | 2002 | 1842 | 1878 | 2036 | 1923 | 1659 | 1603 | 1533 | 1406 | 1136 | 1617 | 1231 | 1059 | 1036 | 1107 | 858 | 25850 |
| 2.02 | 19240 | 18716 | 18445 | 18105 | 18508 | 18621 | 18007 | 17561 | 17314 | 16941 | 17484 | 18227 | 18693 | 18170 | 17422 | 16824 | 12182 | 300460 |
| 2.03 | 4458 | 4942 | 4866 | 4872 | 4981 | 4958 | 4730 | 4847 | 4650 | 4513 | 5352 | 5059 | 4723 | 4954 | 5212 | 5122 | 3268 | 81507 |
| 2.04 | 272 | 222 | 196 | 169 | 160 | 178 | 180 | 152 | 119 | 147 | 191 | 112 | 118 | 194 | 183 | 152 | 83 | 2828 |
| 2.05 | 270 | 253 | 321 | 287 | 271 | 309 | 286 | 240 | 199 | 232 | 273 | 112 | 258 | 441 | 336 | 256 | 139 | 4483 |
| 2.06 | 158 | 135 | 170 | 131 | 112 | 119 | 97 | 97 | 72 | 89 | 85 | 51 | 48 | 70 | 62 | 66 | 32 | 1594 |
| 3.01 | 1022 | 997 | 948 | 784 | 641 | 888 | 1054 | 937 | 878 | 1100 | 984 | 865 | 1494 | 2412 | 2354 | 1600 | 931 | 19889 |
| 3.02 | 3614 | 3341 | 3002 | 3147 | 3327 | 3201 | 2916 | 3082 | 2884 | 2674 | 2987 | 3846 | 2745 | 3052 | 3575 | 4002 | 2987 | 54382 |
| 3.03 | 912 | 952 | 907 | 931 | 834 | 932 | 996 | 974 | 879 | 930 | 1000 | 1078 | 1063 | 1183 | 1157 | 1136 | 794 | 16658 |
| 4.01 | 1303 | 1052 | 910 | 1254 | 1126 | 1146 | 924 | 896 | 816 | 692 | 582 | 717 | 767 | 796 | 970 | 760 | 397 | 15108 |
| 4.02 | 387 | 346 | 302 | 273 | 213 | 201 | 166 | 133 | 130 | 97 | 96 | 840 | 288 | 240 | 237 | 132 | 76 | 4157 |
| 5.01 | 837 | 733 | 707 | 661 | 631 | 624 | 617 | 613 | 522 | 461 | 440 | 615 | 455 | 415 | 400 | 421 | 297 | 9449 |
| 5.02 | 14828 | 14422 | 13994 | 13663 | 14138 | 13883 | 12804 | 12439 | 12194 | 11989 | 11989 | 12569 | 12431 | 12034 | 11153 | 11052 | 7646 | 213228 |
| 5.03 | 2686 | 2583 | 2512 | 2641 | 2716 | 2819 | 2859 | 2634 | 2348 | 2283 | 2893 | 2999 | 2716 | 3323 | 2735 | 2559 | 1837 | 45143 |
| 5.04 | 81 | 61 | 59 | 46 | 50 | 51 | 44 | 36 | 46 | 35 | 34 | 31 | 28 | 23 | 17 | 24 | 4 | 670 |
| 5.05 | 136 | 132 | 137 | 93 | 137 | 109 | 92 | 87 | 91 | 73 | 88 | 82 | 110 | 115 | 76 | 73 | 40 | 1671 |
| 5.06 | 225 | 189 | 142 | 134 | 106 | 82 | 61 | 76 | 67 | 48 | 73 | 171 | 97 | 110 | 61 | 51 | 26 | 1719 |
| 5.07 | 4932 | 5253 | 5061 | 4943 | 4979 | 5114 | 4978 | 4942 | 4849 | 4780 | 4788 | 5066 | 5551 | 5838 | 5450 | 5234 | 4173 | 85931 |
| 5.08 | 0 | 2 | 41 | 67 | 65 | 66 | 60 | 70 | 82 | 98 | 110 | 86 | 140 | 131 | 127 | 136 | 60 | 1341 |
| 6.01 | 0 | 0 | 7 | 10 | 17 | 4 | 4 | 5 | 6 | 5 | 4 | 12 | 5 | 4 | 8 | 4 | 3 | 98 |
| 6.02 | 3 | 3 | 11 | 24 | 29 | 16 | 34 | 13 | 73 | 36 | 77 | 495 | 172 | 97 | 39 | 503 | 90 | 1715 |
| 6.03 | 0 | 2 | 0 | 0 | 0 | 0 | 2 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 5 |
| 6.04 | 0 | 1 | 0 | 3 | 0 | 0 | 1 | 3 | 5 | 10 | 13 | 16 | 31 | 18 | 15 | 47 | 21 | 184 |
| 6.05 | 4 | 1 | 6 | 6 | 4 | 6 | 4 | 14 | 10 | 11 | 5 | 6 | 7 | 10 | 10 | 7 | 2 | 113 |
| 6.06 | 0 | 0 | 0 | 0 | 1 | 3 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 5 |
| 7.01 | 13370 | 13523 | 13599 | 13662 | 14431 | 14821 | 14430 | 14357 | 14120 | 13889 | 16337 | 16861 | 16276 | 16872 | 16238 | 16486 | 11727 | 250999 |
| 8.01 | 19057 | 18602 | 18814 | 18778 | 18337 | 18038 | 17264 | 17199 | 16421 | 15703 | 19677 | 19433 | 15498 | 17416 | 16426 | 17127 | 11572 | 295362 |
| 9.01 | 57716 | 56053 | 55001 | 54922 | 55806 | 55567 | 52347 | 51774 | 50061 | 48659 | 53429 | 56616 | 52492 | 53913 | 51178 | 50357 | 34789 | 890680 |

### T2 — Of filings carrying each code, PERCENT also carrying Item 2.02

`-` = no filings. `(n)` = fewer than 25 filings that year; the raw count is
shown instead of a meaningless percentage. **Read the sparse rows (1.03, 1.04,
1.05, 2.04, 5.04, 5.05, 5.06, 5.08, all of 6.xx) as noise, not trend.**

| Item | 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026p | ALL |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.01 | 2.0 | 2.1 | 1.8 | 2.1 | 2.0 | 2.3 | 2.1 | 2.6 | 2.2 | 2.1 | 3.0 | 1.9 | 2.3 | 2.5 | 2.4 | 2.6 | 2.7 | 2.3 |
| 1.02 | 1.7 | 1.8 | 1.6 | 2.3 | 2.4 | 2.0 | 2.5 | 3.0 | 2.4 | 2.5 | 2.7 | 2.8 | 2.6 | 2.6 | 3.2 | 2.8 | 3.8 | 2.5 |
| 1.03 | 0.5 | 0.6 | 2.4 | 3.4 | 2.8 | 1.0 | 1.8 | 0.9 | 7.3 | 0.0 | 2.3 | 1.4 | 0.0 | 1.3 | 0.6 | 1.1 | 0.0 | 1.6 |
| 1.04 | - | (1) | 0.0 | 0.0 | 2.4 | 0.0 | (12) | (15) | (11) | (16) | (8) | (10) | (11) | (10) | (10) | (10) | (16) | 1.1 |
| 1.05 | - | - | - | - | - | - | - | - | - | - | - | - | - | (2) | (24) | (15) | (16) | 1.8 |
| 2.01 | 1.3 | 1.4 | 1.8 | 1.5 | 1.9 | 1.8 | 1.9 | 1.7 | 2.0 | 1.7 | 3.0 | 1.2 | 1.2 | 1.7 | 2.1 | 2.2 | 1.6 | 1.7 |
| 2.02 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| 2.03 | 1.2 | 1.7 | 1.3 | 1.4 | 1.5 | 1.7 | 1.9 | 2.0 | 2.0 | 1.4 | 2.8 | 1.4 | 2.0 | 2.1 | 1.6 | 1.7 | 1.9 | 1.8 |
| 2.04 | 1.5 | 1.4 | 4.6 | 4.1 | 3.1 | 1.1 | 2.8 | 1.3 | 6.7 | 0.7 | 2.1 | 1.8 | 0.8 | 4.1 | 2.2 | 2.0 | 1.2 | 2.4 |
| **2.05** | 14.1 | 22.1 | 20.9 | 23.0 | 20.7 | 22.3 | 23.4 | 22.5 | 24.1 | 24.1 | 20.5 | 22.3 | 25.2 | 28.3 | 25.6 | 29.3 | 36.7 | **23.6** |
| **2.06** | 19.0 | 20.0 | 27.6 | 24.4 | 23.2 | 21.8 | 20.6 | 19.6 | 16.7 | 11.2 | 16.5 | 13.7 | 16.7 | 21.4 | 19.4 | 13.6 | 9.4 | **19.9** |
| 3.01 | 2.2 | 1.3 | 2.4 | 2.9 | 2.2 | 1.9 | 1.1 | 1.5 | 1.1 | 1.4 | 2.1 | 0.6 | 1.0 | 1.2 | 1.2 | 1.4 | 1.0 | 1.5 |
| 3.02 | 1.2 | 1.2 | 1.0 | 1.2 | 1.2 | 1.4 | 1.4 | 1.8 | 2.1 | 1.8 | 2.3 | 1.2 | 2.3 | 2.0 | 2.3 | 1.8 | 1.7 | 1.6 |
| 3.03 | 1.2 | 1.3 | 0.8 | 1.4 | 1.8 | 1.3 | 1.7 | 2.0 | 1.7 | 1.3 | 2.0 | 1.9 | 1.6 | 1.5 | 2.2 | 1.1 | 1.1 | 1.5 |
| 4.01 | 1.1 | 0.2 | 0.1 | 0.4 | 0.5 | 0.9 | 0.6 | 0.8 | 0.6 | 0.9 | 1.5 | 1.1 | 0.8 | 1.3 | 1.4 | 1.1 | 0.8 | 0.8 |
| **4.02** | 10.1 | 7.5 | 14.9 | 15.4 | 13.1 | 13.4 | 13.3 | 10.5 | 12.3 | 13.4 | 15.6 | 4.4 | 9.7 | 14.6 | 13.5 | 15.2 | 7.9 | **10.7** |
| 5.01 | 1.6 | 1.0 | 1.4 | 0.5 | 1.7 | 2.1 | 1.9 | 1.5 | 1.7 | 1.7 | 1.6 | 0.5 | 1.8 | 1.4 | 2.2 | 1.2 | 2.0 | 1.5 |
| 5.02 | 2.6 | 2.8 | 2.9 | 3.0 | 3.0 | 3.4 | 3.6 | 3.6 | 3.4 | 3.7 | 4.4 | 3.5 | 4.1 | 4.0 | 4.5 | 4.3 | 4.1 | 3.5 |
| 5.03 | 2.0 | 1.8 | 1.7 | 2.0 | 2.0 | 2.1 | 2.0 | 2.1 | 1.9 | 1.8 | 2.1 | 1.9 | 2.7 | 1.7 | 2.0 | 1.4 | 1.9 | 2.0 |
| 5.04 | 0.0 | 3.3 | 6.8 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 2.2 | 2.9 | 0.0 | 0.0 | 0.0 | (23) | (17) | (24) | (4) | 1.2 |
| 5.05 | 1.5 | 3.8 | 6.6 | 4.3 | 8.0 | 5.5 | 7.6 | 9.2 | 5.5 | 5.5 | 3.4 | 2.4 | 7.3 | 6.1 | 6.6 | 8.2 | 12.5 | 5.8 |
| 5.06 | 4.0 | 1.6 | 2.8 | 1.5 | 0.9 | 6.1 | 9.8 | 3.9 | 9.0 | 10.4 | 1.4 | 1.2 | 3.1 | 1.8 | 14.8 | 5.9 | 0.0 | 3.7 |
| 5.07 | 2.3 | 2.4 | 2.5 | 2.3 | 2.5 | 2.2 | 2.2 | 2.3 | 1.9 | 1.7 | 1.6 | 1.4 | 1.2 | 1.2 | 1.2 | 1.0 | 1.1 | 1.8 |
| 5.08 | - | (2) | 4.9 | 4.5 | 9.2 | 6.1 | 6.7 | 5.7 | 6.1 | 2.0 | 2.7 | 1.2 | 2.9 | 4.6 | 0.8 | 0.7 | 3.3 | 3.6 |
| 6.01 | - | - | (7) | (10) | (17) | (4) | (4) | (5) | (6) | (5) | (4) | (12) | (5) | (4) | (8) | (4) | (3) | 0.0 |
| 6.02 | (3) | (3) | (11) | (24) | 0.0 | (16) | 0.0 | (13) | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 6.03 | - | (2) | - | - | - | - | (2) | (1) | - | - | - | - | - | - | - | - | - | 0.0 |
| 6.04 | - | (1) | - | (3) | - | - | (1) | (3) | (5) | (10) | (13) | (16) | 0.0 | (18) | (15) | 0.0 | (21) | 0.0 |
| 6.05 | (4) | (1) | (6) | (6) | (4) | (6) | (4) | (14) | (10) | (11) | (5) | (6) | (7) | (10) | (10) | (7) | (2) | 0.9 |
| 6.06 | - | - | - | - | (1) | (3) | - | - | (1) | - | - | - | - | - | - | - | - | 0.0 |
| **7.01** | 18.5 | 18.4 | 18.4 | 18.7 | 18.6 | 18.8 | 20.1 | 20.5 | 21.7 | 21.7 | 20.8 | 21.3 | 23.7 | 23.3 | 23.4 | 23.5 | 25.0 | **21.0** |
| 8.01 | 5.1 | 5.7 | 5.9 | 6.3 | 6.9 | 7.2 | 7.0 | 6.8 | 7.2 | 7.1 | 6.7 | 6.4 | 7.9 | 6.7 | 7.7 | 7.6 | 8.1 | 6.8 |
| 9.01 | 32.1 | 32.1 | 32.2 | 31.7 | 32.0 | 32.3 | 33.2 | 32.9 | 33.5 | 33.9 | 31.8 | 31.3 | 34.7 | 32.7 | 33.0 | 32.4 | 34.0 | 32.6 |

---

## 5. The trend, and which codes are being absorbed fastest

### T3 — early window vs late window (codes with ≥100 filings in both)

Sorted by change. `n` is the number of filings carrying the code in that window.

| Item | n 2010–12 | %2.02 2010–12 | n 2023–25 | %2.02 2023–25 | delta pp |
|---|---|---|---|---|---|
| 2.05 | 844 | 19.1 | 1033 | **27.7** | **+8.6** |
| 7.01 | 40492 | 18.4 | 49596 | **23.4** | **+5.0** |
| 4.02 | 1035 | 10.6 | 609 | 14.3 | +3.7 |
| 5.06 | 556 | 2.9 | 222 | 6.3 | +3.4 |
| 5.05 | 405 | 4.0 | 264 | 6.8 | +2.9 |
| 8.01 | 56473 | 5.6 | 50969 | 7.3 | +1.7 |
| 5.02 | 43244 | 2.8 | 34239 | 4.3 | +1.5 |
| 1.02 | 3761 | 1.7 | 2917 | 2.9 | +1.2 |
| 3.02 | 9957 | 1.1 | 10629 | 2.0 | +0.9 |
| 4.01 | 3265 | 0.5 | 2526 | 1.3 | +0.7 |
| 9.01 | 168770 | 32.1 | 155448 | 32.7 | +0.6 |
| 1.01 | 37054 | 2.0 | 31977 | 2.5 | +0.5 |
| 2.04 | 690 | 2.3 | 529 | 2.8 | +0.5 |
| 2.01 | 5768 | 1.5 | 3202 | 2.0 | +0.5 |
| 3.03 | 2771 | 1.1 | 3476 | 1.6 | +0.5 |
| 2.03 | 14266 | 1.4 | 15288 | 1.8 | +0.4 |
| 5.01 | 2277 | 1.3 | 1236 | 1.6 | +0.3 |
| 1.03 | 478 | 1.0 | 399 | 1.0 | −0.0 |
| 5.03 | 7781 | 1.9 | 8617 | 1.7 | −0.2 |
| 3.01 | 2967 | 2.0 | 6366 | 1.3 | −0.7 |
| 5.07 | 15246 | 2.4 | 16522 | 1.1 | **−1.3** |
| 2.06 | 463 | 22.5 | 198 | 18.2 | **−4.3** |

### Being absorbed fastest

**Ranked by delta, with the caveat that only two of the top five have the N to
support a trend claim:**

1. **7.01 Reg FD disclosure — the only large, clean, monotone case.**
   18.4% → 23.4% on n≈40–50k per window. Seen from the 2.02 side (T4) it is
   even starker and strictly monotone: **12.85% → 24.04%, up in 16 of 16
   consecutive years, no reversal anywhere.** Survives the constant-issuer
   panel at +8.49 pp. This is issuers routinely dual-tagging the earnings
   release as both 2.02 and 7.01.
2. **2.05 costs associated with exit or disposal activities** — 19.1% → 27.7%,
   and 2026 partial is 36.7%. n is only 844/1033, so treat the level as solid
   and the slope as suggestive. Mechanically sensible: restructuring charges
   are announced with the quarter they hit.
3. **4.02 non-reliance on previously issued financials** — 10.6% → 14.3%, but
   **this row is not trustworthy as a trend**: n falls from 1035 to 609, and
   2021 is a visible outlier (840 filings at 4.4%, against 96 in 2020 and 288
   in 2022). I did not establish the cause of that spike.
4. **8.01 other events** — 5.6% → 7.3%, on very large n. Small but real and it
   matters more than its size suggests, because 8.01 is where text-identified
   events without their own code live (§7).
5. **5.02 departure/election of directors and officers** — 2.8% → 4.3%. Large
   n, clean direction, but the *level* is still only 4.3%.

**5.06 and 5.05 are in the T3 top five by delta and should be discounted**:
n = 222 and 264 in the late window, and their year-by-year rows in T2 swing
between 0.9% and 14.8% with no shape. I am reporting them only because
suppressing them would be a silent shortcut.

### Moving the other way

- **2.06 material impairments: 22.5% → 18.2%, and 2019 was 11.2%.** The one
  substantive code that became *less* entangled. n is small (463→198) so this
  is weak, but it is the opposite sign to the story and is stated as such.
- **5.07 submission of matters to a vote: 2.4% → 1.1%, more than halved.** Good
  n (15k→16.5k). Annual-meeting results are drifting *away* from the earnings
  submission.
- **3.01 notice of delisting / failure to satisfy listing rules: 2.0% → 1.3%**,
  on rising volume (2,967 → 6,366).

### T4 — Reverse view: what travels with Item 2.02

| Year | 2.02 filings | mean codes per 2.02 filing | mean codes per any 8-K | 2.02 share of all 8-K |
|---|---|---|---|---|
| 2010 | 19240 | 2.200 | 2.058 | 24.5% |
| 2011 | 18716 | 2.213 | 2.062 | 24.3% |
| 2012 | 18445 | 2.220 | 2.063 | 24.5% |
| 2013 | 18105 | 2.234 | 2.084 | 24.4% |
| 2014 | 18508 | 2.243 | 2.098 | 24.7% |
| 2015 | 18621 | 2.254 | 2.108 | 25.0% |
| 2016 | 18007 | 2.263 | 2.112 | 25.5% |
| 2017 | 17561 | 2.277 | 2.138 | 25.5% |
| 2018 | 17314 | 2.280 | 2.136 | 26.1% |
| 2019 | 16941 | 2.281 | 2.132 | 26.2% |
| 2020 | 17484 | 2.324 | 2.160 | 24.8% |
| 2021 | 18227 | 2.298 | 2.213 | 25.0% |
| 2022 | 18693 | 2.313 | 2.176 | 27.4% |
| 2023 | 18170 | 2.325 | 2.191 | 25.7% |
| 2024 | 17422 | 2.335 | 2.210 | 26.0% |
| 2025 | 16824 | 2.351 | 2.225 | 25.4% |
| 2026p | 12182 | 2.355 | 2.235 | 26.8% |

**The brief predicted "a rising average number of codes per earnings submission
is the same phenomenon seen from the other side". That prediction is CONFIRMED
in direction but it is SMALL: 2.200 → 2.355, i.e. +0.155 codes, +7.0% over
sixteen years.** It rises in 15 of 16 year-on-year steps (the exception is
2020→2021). It is not a regime change; it is a slow drift.

Two things keep that drift honest:

- **The baseline drifts too, and slightly faster.** On full years 2010→2025,
  mean codes per *any* 8-K went 2.058 → 2.225 (**+0.167**) while the 2.02
  subset went 2.200 → 2.351 (**+0.151**). Including partial 2026 the gap is the
  same direction (+0.178 vs +0.155). **Item 2.02 submissions are not accreting
  codes faster than 8-K filings in general — they are accreting them slightly
  more slowly.** On this statistic the "earnings submissions are becoming
  bundles" story is not specific to earnings submissions at all. [MEASURED IN
  BRIEF]
- **2.02's share of all 8-K filings is flat**: 24.5% → 25.4% (2025), 26.8% on
  partial 2026. About three quarters of 8-K filings are still not earnings
  submissions.

Companion codes, as percent of that year's 2.02 filings:

| Companion | 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 9.01 | 96.17 | 96.13 | 96.06 | 96.16 | 96.48 | 96.50 | 96.60 | 97.02 | 96.94 | 97.44 | 97.19 | 97.35 | 97.38 | 97.12 | 96.83 | 97.02 | 97.06 |
| **7.01** | **12.85** | 13.27 | 13.58 | 14.14 | 14.49 | 14.97 | 16.14 | 16.75 | 17.71 | 17.77 | 19.47 | 19.70 | 20.68 | 21.59 | 21.80 | 23.03 | **24.04** |
| 8.01 | 5.06 | 5.65 | 6.04 | 6.53 | 6.82 | 6.97 | 6.71 | 6.69 | 6.80 | 6.58 | 7.52 | 6.86 | 6.57 | 6.46 | 7.22 | 7.72 | 7.68 |
| 5.02 | 2.03 | 2.13 | 2.21 | 2.29 | 2.27 | 2.54 | 2.57 | 2.55 | 2.37 | 2.64 | 3.02 | 2.38 | 2.74 | 2.63 | 2.89 | 2.85 | 2.55 |
| 1.01 | 1.31 | 1.40 | 1.17 | 1.34 | 1.32 | 1.47 | 1.31 | 1.64 | 1.32 | 1.26 | 1.88 | 1.30 | 1.25 | 1.45 | 1.48 | 1.65 | 1.53 |
| 5.07 | 0.59 | 0.67 | 0.69 | 0.62 | 0.66 | 0.60 | 0.62 | 0.64 | 0.52 | 0.47 | 0.43 | 0.38 | 0.34 | 0.39 | 0.37 | 0.32 | 0.36 |
| 2.03 | 0.27 | 0.46 | 0.34 | 0.39 | 0.41 | 0.46 | 0.51 | 0.56 | 0.55 | 0.38 | 0.87 | 0.38 | 0.50 | 0.56 | 0.49 | 0.53 | 0.51 |
| 2.05 | 0.20 | 0.30 | 0.36 | 0.36 | 0.30 | 0.37 | 0.37 | 0.31 | 0.28 | 0.33 | 0.32 | 0.14 | 0.35 | 0.69 | 0.49 | 0.45 | 0.42 |
| 3.02 | 0.22 | 0.21 | 0.17 | 0.20 | 0.21 | 0.24 | 0.23 | 0.31 | 0.36 | 0.28 | 0.40 | 0.26 | 0.34 | 0.34 | 0.47 | 0.43 | 0.41 |
| 5.03 | 0.28 | 0.25 | 0.23 | 0.29 | 0.29 | 0.32 | 0.32 | 0.31 | 0.25 | 0.24 | 0.35 | 0.32 | 0.40 | 0.30 | 0.32 | 0.21 | 0.28 |
| 2.01 | 0.13 | 0.15 | 0.18 | 0.15 | 0.21 | 0.18 | 0.18 | 0.16 | 0.17 | 0.14 | 0.19 | 0.10 | 0.08 | 0.10 | 0.13 | 0.14 | 0.11 |
| 4.02 | 0.20 | 0.14 | 0.24 | 0.23 | 0.15 | 0.14 | 0.12 | 0.08 | 0.09 | 0.08 | 0.09 | 0.20 | 0.15 | 0.19 | 0.18 | 0.12 | 0.05 |
| 1.02 | 0.11 | 0.13 | 0.10 | 0.13 | 0.15 | 0.12 | 0.15 | 0.18 | 0.15 | 0.14 | 0.15 | 0.18 | 0.14 | 0.14 | 0.17 | 0.17 | 0.21 |
| 2.06 | 0.16 | 0.14 | 0.25 | 0.18 | 0.14 | 0.14 | 0.11 | 0.11 | 0.07 | 0.06 | 0.08 | 0.04 | 0.04 | 0.08 | 0.07 | 0.05 | 0.02 |

**Read this table the right way round.** The rise in codes per 2.02 submission
is **almost entirely 7.01** (+11.2 pp) plus a little 8.01 (+2.6 pp). Every
substantive corporate-event code stays under 3% of earnings submissions for the
whole seventeen years, and several *fall*. **9.01 at ~97% is not an event** —
it is the "financial statements and exhibits" housekeeping code that tags the
press-release exhibit, and it should be excluded from any absorption reading.

### T5 — the other absorption channel: same issuer, same DAY, separate submission

The brief's framing is about whether an event is *separately dated*. A code can
be in its own submission yet still land on the issuer's earnings day. For every
8-K that does **not** itself carry 2.02, I asked whether the same CIK filed a
2.02 8-K on the same `filingDate`. **This channel is small:** typically
**1–4%**, e.g. 5.02 steady at 1.6→2.0%, 1.01 1.0→2.1%, 7.01 2.1→3.7%,
8.01 1.5→1.6%, 5.07 1.4→1.0%. The largest well-populated entry is 4.02 at
3.6% overall.

### T6 — combined absorption (same submission OR same issuer-day)

| Item | n 2010–12 | abs% 2010–12 | n 2023–25 | abs% 2023–25 | delta pp |
|---|---|---|---|---|---|
| 2.02 | 56401 | 100.0 | 52416 | 100.0 | — |
| 9.01 *(not an event)* | 168770 | 33.3 | 155448 | 34.3 | +1.0 |
| 2.05 | 844 | 21.7 | 1033 | 28.5 | +6.8 |
| 7.01 | 40492 | 20.4 | 49596 | 26.0 | +5.7 |
| 2.06 | 463 | 24.8 | 198 | 18.2 | −6.7 |
| 4.02 | 1035 | 13.3 | 609 | 18.1 | +4.7 |
| 8.01 | 56473 | 7.2 | 50969 | 8.8 | +1.6 |
| 5.05 | 405 | 5.9 | 264 | 8.7 | +2.8 |
| 5.06 | 556 | 2.9 | 222 | 6.8 | +3.9 |
| 5.02 | 43244 | 4.3 | 34239 | 6.3 | +1.9 |
| 1.02 | 3761 | 3.4 | 2917 | 5.0 | +1.7 |
| 1.01 | 37054 | 3.2 | 31977 | 4.3 | +1.1 |
| 2.04 | 690 | 2.8 | 529 | 3.6 | +0.8 |
| 2.03 | 14266 | 3.2 | 15288 | 3.3 | +0.2 |
| 2.01 | 5768 | 2.3 | 3202 | 3.2 | +0.9 |
| 3.02 | 9957 | 1.6 | 10629 | 3.2 | +1.6 |
| 5.03 | 7781 | 3.1 | 8617 | 2.8 | −0.2 |
| 3.03 | 2771 | 1.9 | 3476 | 2.6 | +0.7 |
| 5.01 | 2277 | 1.4 | 1236 | 2.6 | +1.1 |
| 5.07 | 15246 | 3.8 | 16522 | 2.3 | −1.5 |
| 4.01 | 3265 | 0.7 | 2526 | 2.0 | +1.2 |
| 3.01 | 2967 | 2.5 | 6366 | 1.8 | −0.7 |
| 1.03 | 478 | 1.3 | 399 | 1.3 | −0.0 |

**Even on the most generous definition of absorption, every substantive event
code except 2.05, 7.01, 2.06 and 4.02 sits at or below 6.3% in 2023–25.**

---

## 6. Looking at the object, not just the statistic

A concentration statistic is not finished until the top object is named and
looked at. The largest item count on any single submission in the window is
**14 codes**:

```
accession       0001213900-26-025222
issuer          PRESIDIO PRODUCTION Co   (CIK 2083125)
filingDate      2026-03-09    periodOfReport 2026-03-04
items (JSON)    1.01,2.01,2.03,3.01,3.02,3.03,4.01,5.01,5.02,5.03,5.05,5.06,8.01,9.01
items (EDGAR index page) IDENTICAL, 14 of 14
url             https://www.sec.gov/Archives/edgar/data/2083125/000121390026025222/0001213900-26-025222-index.htm
```

It carries **no 2.02**. The maximal bundle in this dataset is not an earnings
submission at all — the item set has the signature of a completed reverse
merger or change-of-control transaction (5.01 change in control, 5.02 new
directors and officers, 5.03 charter amendment, 4.01 auditor change, 3.01
listing notice, 3.02 unregistered share issuance, 2.01 completed acquisition).
**I did not read the filing body, so "reverse merger" is an inference from the
item set, not an established fact.** What *is* established is that the extreme
bundles in this census are transaction closings rather than earnings releases —
a useful corrective to the "8-K filings are becoming earnings bundles" reading.

---

## 7. Interpretation for the programme — and the limit of this screen

### 7a. What this census can and cannot screen

**It screens item codes. It does not screen events.** The census reads one
metadata field and never opens a filing body. Consequences:

- **If a candidate event has its own item code, this census is the screen.**
  Look up the code in T2/T6 and you have the absorption rate and its trend,
  complete, with zero sampling error.
- **If a candidate event has NO item code, this census is blind to it, and a
  low number here is NOT evidence the event is separately dated.** Dividend
  initiations and cuts, stock splits, buyback authorisations, guidance changes
  — none has an Item. They are prose inside filings tagged 8.01, 7.01 and/or
  2.02. An event described in the body of an earnings 8-K is invisible here.
- **That is exactly the failure mode that killed the two lanes last round.**
  This census would not have caught them. 8.01 shows 7.3% co-filing with 2.02
  — while the dividend-initiation measurement reported 62.2%. Both can be true:
  dividend announcements are a small minority of 8.01 filings that happen to be
  heavily earnings-bundled. **My numbers neither confirm nor refute the 62.2% /
  59.2% / 36–68% figures. I did not measure the same thing.**

So the correct screen for a future lane is two-stage: **(i)** if the event has
an item code, use T2/T6 here; **(ii)** if it does not, a *text-level*
measurement on filing bodies is mandatory and nothing in this brief substitutes
for it.

### 7b. Codes that remain separately dated enough to be worth a lane

On absorption alone (T6, 2023–25 combined, and volume from T1). I am reporting
separate-datedness only; I am **not** asserting any of these has an effect, and
per the programme's rule only the principal closes or opens an avenue.

Absorption is the T6 **combined** figure (same submission OR same issuer-day),
i.e. the least favourable reading. Volume is the 2023–25 mean from T1.

| Code | 2023–25 combined absorption | in-submission only | volume/yr | note |
|---|---|---|---|---|
| 5.02 officers/directors | 6.3% | 4.3% | ~11,400 | largest well-dated event code by far |
| 1.01 material agreements | 4.3% | 2.5% | ~10,700 | large, but heterogeneous content |
| 2.03 debt obligations | 3.3% | 1.8% | ~5,100 | **adjacent to excluded ground** (corporate supply) |
| 5.07 vote results | 2.3% | 1.1% | ~5,500 | and absorption is *falling* |
| 3.02 unregistered equity sales | 3.2% | 2.0% | ~3,540 | **adjacent to excluded ground** (ATM issuance) |
| 5.03 charter/fiscal-year change | 2.8% | 1.7% | ~2,870 | |
| 3.03 modification of security holder rights | 2.6% | 1.6% | ~1,160 | |
| 4.01 auditor change | 2.0% | 1.3% | ~840 | |
| 3.01 delisting notice | 1.8% | 1.3% | ~2,120 | **adjacent to excluded ground** (death process) |
| 1.05 cybersecurity incidents | 1.8% | 1.8% | ~20 | cleanly separate, but N is far too small to use |

Flagged rather than recommended, because three of these sit next to named
exclusions (corporate supply events, ATM issuance, the death process) and
2.01 completion of acquisition sits next to merger-arbitrage. Whether the
adjacency disqualifies them is not mine to decide.

### 7c. Codes that are effectively part of the earnings event now

- **9.01** — 32.7% overall, but it is the exhibits housekeeping code and ~97%
  of earnings submissions carry it. Never treat it as an event.
- **7.01 Reg FD** — 23.4% in-submission, 26.0% combined, rising monotonically
  for sixteen straight years. **Treat a 7.01 filing as earnings-contaminated by
  default and require an explicit non-2.02, non-earnings-day filter.** This is
  the single most decision-relevant line of the census.
- **2.05 exit/disposal costs** — 27.7% in-submission, 28.5% combined, rising.
  Effectively an earnings-release line item.
- **2.06 material impairments** — 18.2%, though *falling*.
- **4.02 non-reliance / restatement** — 14.3% in-submission, 18.1% combined, so
  roughly one in six is earnings-entangled. **Treat the trend as unusable**: the
  2021 cell is a visible outlier (840 filings at 4.4%, against 96 in 2020 and
  288 in 2022). I have *not* established what caused that spike — the SPAC
  warrant-restatement wave is the obvious candidate and I did not check it, so
  it stays an unverified guess (§10.14).

### 7d. The honest summary

The absorption phenomenon is **real, visible, monotone and small** at item-code
granularity, and it is **concentrated in one procedural code (7.01) rather than
spread across substantive event codes**. The "earnings submissions are becoming
bundles" reading survives only in a weak form, and even that weakens once you
notice that non-2.02 8-K filings accreted codes slightly *faster* than 2.02
filings did. For the specific events that killed two lanes last round, this
census has nothing to say, and saying so is the main result.

---

## 8. Exact re-run recipe

```
# 1. the archive (one request, ~1.56 GB)
GET https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip
    User-Agent: Backtest-Framework-Research research@backtest-framework.org

# 2. independent positive control (one request per quarter)
GET https://www.sec.gov/Archives/edgar/full-index/<YYYY>/QTR<n>/form.idx

# 3. per-filing item validation and item titles  (works in all eras)
GET https://www.sec.gov/Archives/edgar/data/<cik>/<accession-nodashes>/<accession>-index.htm

# 4. per-filing acceptance timestamp in EASTERN, for the §3h timezone check.
#    Use the dissemination .txt -- read only the first ~3 kB.
GET https://www.sec.gov/Archives/edgar/data/<cik>/<accession-nodashes>/<accession>.txt

# 5. single-CIK live route (structure check, archive-vs-API control)
GET https://data.sec.gov/submissions/CIK##########.json

# REJECTED route, do not use for items:
GET https://efts.sec.gov/LATEST/search-index?forms=8-K&items=<code>&startdt=&enddt=
    -> the items parameter is SILENTLY IGNORED (§1a)

# BROKEN FOR HISTORICAL FILINGS, do not use pre-2014:
GET .../<accession>-index-headers.html
    -> HTTP 404 for every 2010-2013 filing tested
```

Two further operational notes for whoever re-runs this:

- **SEC ignores the `Range` header** on `Archives/` files. A `curl -r 0-300` on
  a 96 MB `form.idx` downloaded the whole file. To read only a prefix, open the
  stream and read N bytes rather than asking the server for them.
- The 429 in §3i came from cumulative volume, not burst rate. Budget the
  1.56 GB archive as a large part of your quota and leave a gap before doing
  per-filing fetches.

Scripts, all prefixed `K3_`, in the session scratchpad:

| script | role |
|---|---|
| `K3_harvest.py` | map: zip member → 8-K rows (run via `K3_run_harvest.sh`, 12 procs) |
| `K3_reduce.py` | census + same-issuer-day pass → `K3_census.json` |
| `K3_tables.py` | renders T1–T6 → `K3_tables.md` |
| `K3_control_formidx.py`, `K3_poscontrol.py` | §3b positive control |
| `K3_verify_chunk.py` | §3c chunk==whole, with deliberate-break self-test |
| `K3_extra.py` | §3d dead-inclusive, §3e composition, data cutoff |
| `K3_check_claims.py` | §3g re-derives every published figure and asserts it |
| `K3_zip_vs_live.py` | §3f archive-vs-live-API, zero network requests |
| `K3_net_extras.py` | §3f per-filing `items` cross-check + §4 titles |
| `K3_tz3.py` | §3h timezone control (the version that works) |
| `K3_tzcheck.py`, `K3_tz_stratified.py`, `K3_tz2.py` | earlier timezone attempts, **kept because they are the wrong answers described in §3h** |

Intermediate data: `K3_census.json`, `K3_tables.md`, `K3_rows_*.tsv`,
`K3_titles.json`, `K3_items_crosscheck.json`, `K3_tz_stratified.json`,
`K3_control_formidx.json`.

**Per the programme's file contract these live in `temp/`-equivalent scratch and
are deletable. Any figure quoted above that a record relies on should be
promoted into `data/` as evidence.**

---

## 9. Sources, by type and by how well established

| # | Source | Type | How well established |
|---|---|---|---|
| 1 | `submissions.zip`, 1,562,536,756 bytes, Last-Modified 2026-09-09 | SEC bulk archive (primary) | **Strong.** Documented on SEC's EDGAR-APIs page; validated to the filing against an independent SEC route (§3b) |
| 2 | SEC EDGAR APIs page, `sec.gov/search-filings/edgar-application-programming-interfaces` | SEC primary documentation | **Good.** Fetched; confirms submissions.zip contents and "recompiled nightly". Does **not** document the `items` field or a numeric rate limit |
| 3 | `full-index/<Y>/QTR<n>/form.idx`, 9 quarters | SEC primary index | **Strong.** Fetched directly; each file's own `Last Data Received` header matched the quarter requested |
| 4 | `data.sec.gov/submissions/CIK0000106640.json` | SEC live API | **Good.** Fetched; established the field names and that `items` is a comma-separated string |
| 5 | EDGAR `<acc>-index.htm` filing-index pages, 34 filings | SEC primary per-filing | **Good.** Source of all 33 item titles and of the 33/33 `items` cross-check (§3f). Scale limits in §10.2 |
| 5b | EDGAR `<acc>-index-headers.html` | SEC primary per-filing | **Partial — route fails pre-2014.** Returns HTTP 404 for every 2010–2013 filing tested; do not use it for historical work |
| 5c | EDGAR dissemination file `edgar/data/<cik>/<acc-nodashes>/<acc>.txt`, 51 filings | SEC primary per-filing | **Strong.** Works in both eras; carries the SGML `<ACCEPTANCE-DATETIME>` in Eastern. Basis of §3h |
| 6 | SEC release 33-8400 landing page | SEC primary | **Weak/partial.** Confirmed release number and **effective date August 23, 2004**; the page did not carry the item list, and the Federal Register text (69 FR 15593) was not fetched |
| 7 | `sec.gov/files/form8-k.pdf` | SEC primary form | **Failed as a text source.** Downloaded (1 MB) but item titles could not be extracted from its encoded streams; titles came from source 5 instead. See §10.1 |
| 8 | `efts.sec.gov/LATEST/search-index` | SEC live API | **Strong as a NEGATIVE finding.** Six query variants and an impossible-code control all returned 1070 |
| 9 | `sec.gov/edgar/search/` UI markup | SEC primary UI | **Good.** Fetched and grepped; contains no 8-K item filter control |

No summariser output is used for any number in this brief. Where a page was
fetched through a summarising tool, the figures taken from it are limited to
non-numeric facts (field names, the effective date, the quoted sentence about
submissions.zip), and every published count comes from my own parsing of the
raw archive or raw index files.

**Safety note.** No page, index file or JSON encountered contained text
addressed to me or instructing me to take any action. Nothing was treated as an
instruction. No accounts, credentials, forms or logins were involved.

---

## 10. What I could not verify, stated plainly

1. **Item titles come from EDGAR filing-index pages, not from the Form 8-K
   itself.** The Form 8-K PDF's text streams would not decode to readable item
   headings and the 33-8400 landing page did not carry the item list, so the
   reference table in §4 is EDGAR's rendering rather than the form's own
   wording. The two should agree but I did not verify that they do. No number in
   T1–T6 depends on a title; the tables are keyed on code only.
2. **The per-filing `items` cross-check is 33 filings, one per code — not a
   statistical sample.** §3f reports 33 agreements out of 33, which is strong
   evidence the field is not *systematically* corrupt, and §3f's archive-vs-API
   comparison adds 1,010 filings of agreement between the two SEC
   representations. But 33 hand-checked filings out of 1,185,352 cannot bound a
   *rare* defect: if 1 filing in 10,000 has a wrong `items` string, my check
   would almost certainly miss it and the census would be wrong by ~118
   filings. I have **not** bounded the error rate, only shown it is not large.
   The census's entire numerator rests on this field.
3. **The number of filings per year whose `items` I verified is zero for most
   years.** The 33 cross-checked filings were chosen one per *code*, not spread
   across time, so they cluster wherever each code's first example happened to
   fall (2010–2026, but unevenly). I did not test whether the `items` field's
   fidelity varies by era.
4. **`reportDate` was not used and no census is offered on it.** A census keyed
   on period-of-report rather than filing date would differ at year boundaries
   and for late filings. I did not build it.
5. **2026 is a partial year** (through 2026-09-08, ~69% of a year). Its counts
   in T1 are not comparable to full years; only its ratios are.
6. **`8-K/A` amendments are excluded from T1–T6** (35,900 in window). If an
   event's only filing is an amendment, it is absent from the census. I did not
   measure how often that happens.
7. **Sparse rows cannot carry trends.** 1.03, 1.04, 1.05, 2.04, 5.04, 5.05,
   5.06, 5.08 and all of 6.01–6.06 have years with fewer than 25 filings. T2
   shows raw counts there instead of percentages. 2.05, 2.06 and 4.02 — three
   of the most interesting rows — have only a few hundred filings per
   three-year window, so their *levels* are reasonably estimated but their
   *slopes* are weak. I have not computed confidence intervals for any cell.
8. **I did not establish why 7.01 is rising.** Dual-tagging the earnings release
   as Reg FD disclosure is the obvious mechanism and it fits the monotone shape
   and the constant-issuer result, but I tested the statistic, not the
   mechanism. I did not read a single 7.01+2.02 filing body.
9. **"Same issuer-day" uses `filingDate`, not the actual timestamp.** A 2.02
   filed at 16:05 and a 5.02 filed at 09:00 the same morning count as the same
   day, and T5 cannot distinguish "filed alongside the earnings release" from
   "filed nine hours earlier". A timestamp-aware version is blocked on the
   unresolved `acceptanceDateTime` defect (§3h) — and per §3h the fix is a
   per-filing header check, which at ~1.19 M filings is a different project.
   **`filingDate` is also the EDGAR filing date, not the event date**: a filing
   accepted after 17:30 ET carries the next business day, so a small number of
   same-evening pairs are split across two `filingDate` values and T5
   under-counts them. I did not quantify how many.
10. **The timezone sample is 51 filings at ~3 per year.** §3h reproduces the
    defect decisively in aggregate (32/51), but the per-year and per-filer-agent
    breakdowns in that section rest on 1–3 observations per cell and must not be
    read as rates. In particular "no mislabel after 2023" is 9 filings and is
    not evidence of a fix.
11. **The co-registrant question is resolved for counts but not for semantics.**
    61,063 duplicate records were dropped. Where a filing has several
    registrants, T5's same-issuer-day logic attributes it to each of them; I
    did not check whether that is the right attribution for an operating
    subsidiary filing alongside a parent.
12. **I could not confirm the commissioning brief's claim that EDGAR full-text
    search exposes an items filter.** I tested the parameter name `items` in
    five forms on `efts.sec.gov/LATEST/search-index` and grepped the search
    UI's markup. A filter under some other parameter name may exist and I
    would not have found it.
13. **No documented numeric rate limit was found on SEC's own pages.** The
    "10 requests/second" figure is the programme's operating rule, not
    something I verified from SEC primary documentation; the EDGAR APIs page
    states no numeric limit. My own HTTP 429 (§3i) shows the real constraint
    includes cumulative volume, not just instantaneous rate, and I do not know
    its actual parameters.
14. **I did not explain the 2021 spike in Item 4.02.** 840 filings in 2021
    against 96 in 2020 and 288 in 2022, at an unusually low 4.4% co-filing rate.
    The SPAC warrant-restatement wave is the obvious candidate; **I did not check
    it**, did not look at the issuers, and the 4.02 trend in T3/T6 should be
    treated as unusable until someone does.
15. **I did not measure absorption inside 8.01 or 7.01 bodies, which is where
    the question the programme actually cares about lives.** §7a explains why.
    This is not a limitation of the harvest — it is a different measurement that
    this brief does not attempt, and the single most important follow-up.
