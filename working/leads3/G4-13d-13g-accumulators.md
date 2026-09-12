# G4 — Schedule 13D and 13G: the outside accumulator

**Round 3, lane G4. External evidence only.** Nothing here has been measured against this
programme's fixture. Under [R15](../../docs/RULES.md#r15) nothing below closes or admits anything.

**Boundary.** This lane is the **outsider** crossing 5% with control intent — Schedule 13D under
§13(d) of the Exchange Act. It is not Form 4 (the insider), which the programme covered in
[`../leads2/F2-insider-form4.md`](../leads2/F2-insider-form4.md). Different filer, different form,
different deadline, different mechanism. I did not re-tread insider transactions and no number below
comes from a Form 4 source.

---

## 0. Bottom line, stated against the lane

**The data answer is excellent and the signal answer is bad.** Those are separable and I want them
separated, because the good data answer is worth keeping even though the lane it was built for
should not be run.

Four things, in the order they kill it:

1. **The tradeable fraction of the famous 7% is about 2%.** The canonical Brav-Jiang-Partnoy-Thomas
   number decomposes, *in the authors' own text*, into a **3.2% run-up in the ten days BEFORE the
   filing** (which is the accumulator buying, and is not available to anyone reading the filing), a
   **2.0% jump on the filing day and the day after**, and the remainder drifting out to 7.2% by
   t+20. You cannot buy the run-up. §1.
2. **What survives is in the smallest 20% of targets, average market cap $22 million.** deHaan,
   Larcker and McClure establish that the equal-weighted long-term return — the lens this programme
   uses — **is driven entirely by the smallest quintile**; the larger 80% go insignificant **within
   three months** and sit at an insignificant **−1.6% at two years**. Value-weighted, every long-run
   horizon is insignificant. A $5-close plus dollar-volume floor removes precisely the quintile that
   carries the result. §1.3.
3. **The event count after honest filtering is ~60/year, not ~1,400/year.** SEC DERA primary data
   gives a mean of **1,397 initial Schedule 13D filings per year, 2010–2025**. But the SEC's own
   staff analysis (adopting release Table 2) finds **80% of initial 13Ds are "corporate action"
   filings — not campaigns at all** — and Table 1 reports that in 2022, **60 of the 1,161 initial
   13D filings were made by prominent activists**, by **22 unique filers**. Before any price or
   liquidity floor. §6.
4. **The lag is not a lag, it is a completed trade.** SEC staff, analysing 2011–2021 campaign
   filings, find **80% of activist filers had accumulated their FULL stake by five business days
   after crossing 5%** — i.e. before the filing existed. Median trigger-to-filing is **9 days for
   prominent activists**. By publication the accumulation is done, and the pre-filing volume spike
   in the literature is that accumulation. §6.3.

And a structural hazard that would have silently corrupted a run: **the SEC changed the EDGAR
filing cut-off from 5:30 p.m. to 10:00 p.m. Eastern for 13D/G**, so a filing stamped with date `D`
may have been accepted **six hours after the close of `D`**. §5.

**One thing genuinely worth extracting even though the lane fails:** the correct EDGAR pull
direction, and two live bugs it exposes in the programme's existing puller. §4.

**This is among the most published anomalies in existence and that is itself a reason for
suspicion.** It has a dedicated commercial ecosystem (13D Monitor, FactSet SharkRepellent /
Sharkwatch 50, Insightia/Diligent, and a US mutual fund whose entire mandate is trading 13D
filings). The SEC's *own rulemaking* cites those vendors to identify activists. A signal with a
retail mutual-fund wrapper and a regulator using the vendor taxonomy is not undiscovered. §7.

---

## 1. The 13D announcement effect and post-filing drift

### 1.1 Brav, Jiang, Partnoy & Thomas (2008) — the canonical result

[PEER-REVIEWED] — *Hedge Fund Activism, Corporate Governance, and Firm Performance*, Journal of
Finance 63(4), 1729–1775. **[read in full]** — retrieved as PDF from law.duke.edu and extracted to
text locally with `pypdf`; I read the sample-construction section, Table III, Table VI and the
event-study section directly.

- **Sample:** 2001–2006. **1,059 activist events**, **236 activist hedge funds**. Built by
  purchasing a list of all Schedule 13D filers 2001–2006 and manually filtering out banks, brokers,
  insurers, and non-activist types; filers making only one 13D in the whole period with no explicit
  Item 4 purpose were excluded. Supplemented with non-13D events found via 13F holdings, but **only
  for firms with market cap above $1 billion** (their stated reason: a 13D-based search biases the
  sample toward smaller companies — their own words, and it matters below).
- **The headline and its decomposition** (their §V.A, verbatim structure): *"There is a run-up of
  about 3.2% between 10 days to 1 day prior to filing. The filing day and the following day see a
  jump of about 2.0%. Afterward the abnormal return keeps trending up to a total of 7.2% in 20
  days."*
  - **This is the single most important sentence in the lane.** The 7.2% is a (−20,+20) window. The
    3.2% run-up is pre-filing and unavailable. The **filing-day-plus-one jump is 2.0%**.
- **Dispersion:** 62% of events positive over (−20,+20); 25th/50th/75th percentiles **−5.3% / 4.6% /
  17.3%**. Wide, and the mean sits below the 75th by a long way.
- **Target size — the number that decides this lane.** Table III: **median target market
  capitalisation $160.07 million**, mean $726.56m (2001–2006 dollars). Quintile placement is
  bottom-heavy (21.4% Q1, 25.3% Q2, 11.4% Q5).
- **Post-filing drift, calendar-time four-factor alphas (Table VI), monthly, %:**

  | Window (months) | EW alpha | t | VW alpha | t |
  |---|---|---|---|---|
  | (1,3) | **1.093** | **2.01** | 0.141 | 0.28 |
  | (4,6) | 0.237 | 0.52 | −0.683 | −1.24 |
  | (7,9) | −0.093 | −0.19 | −0.005 | −0.01 |
  | (10,12) | 1.124 | 1.84 | −0.041 | −0.08 |

  **Read the two columns against each other.** The only clearly significant post-filing alpha is
  equal-weighted months 1–3. **Every value-weighted alpha is insignificant at every horizon.** The
  EW/VW gap *is* the size concentration, visible in the founding paper in 2008.
- **Liquidity:** they note targets are *more* liquid than matched firms on Amihud — but that is
  relative to matched microcaps, not in absolute terms. **They nowhere price a round trip, model a
  spread, or claim the strategy is implementable.** There is no cost-honest treatment in this paper.

### 1.2 Klein & Zur (2009), and the review

[PEER-REVIEWED] *Entrepreneurial Shareholder Activism: Hedge Funds and Other Private Investors*,
Journal of Finance 64(1). **[abstract/summary only — I did not open the paper; the 10.2% and 5.1%
figures below are taken from search-result summaries and from Brav-Jiang-Kim's citation of it, not
from my own reading].** Reported: **10.2%** abnormal return around the initial 13D filing for hedge
fund targets, **5.1%** for other activist targets; 151 hedge fund campaigns and 154 other campaigns,
mostly 2003–2005.

[WORKING PAPER] Brav, Jiang & Kim, *Hedge Fund Activism: A Review* (Columbia mirror). **[read in
full]** — extracted to text locally. This is the authors' own restatement on 2001–2007, 1,172
events, and it is *more conservative* than the 2008 paper:

- Run-up t−10 to t−1: **2.6%**. Filing day **+1.0%**, next day **+1.2%**. Total **6.0%** by t+20.
- It records Klein & Zur at 7.2% for [−30,+30], Clifford and Boyson-Mooradian at **3.4% to 8.1%**
  across various windows, and **Greenwood & Schor at 3.6% for [−10,+5]**.
- **The abnormal volume spike is BEFORE the event day, not on it** — the authors write that the
  ten-day lead "seems no coincident with" the ten-day filing deadline, and offer wolf-pack investing
  and **tipping** as explanations. The pre-filing move is other people already positioned.

### 1.3 The decay, and the negatives — this is the part that matters

**The authors themselves documented the decay, in 2009.** Brav-Jiang-Kim, Figure 2 and text: the
average [−20,+20] abnormal return is *"almost 14 percent on average in 2001, but it decreases to
less than 4 percent in 2006-2007."* Their stated explanation is competition — *"hedge funds'
activist 'arbitrage' strategy intensified over the years, leading to the entry of more players into
the field, which in turn reduced the equilibrium returns to activism."* **[read in full]** A
frequently-quoted "15.9% in 2001 to 3.4% in 2006" appears in search summaries attributed to the 2008
paper; **I could not locate those two exact figures in the 2008 PDF I read** and I am not asserting
them. The ~14%→<4% pair above is what I verified in text.

**deHaan, Larcker & McClure — the decisive negative.** [PEER-REVIEWED] *Long-term economic
consequences of hedge fund activist interventions*, Review of Accounting Studies (2019); read via
the ECGI working-paper PDF. **[read in full]** — extracted locally and read directly.

- **Sample:** 2,684 13D filings by activist hedge funds 1994–2011, → **1,964 activist
  interventions**. **Note the sample ends in 2011** — see the honesty note below.
- **Headline EW results, consistent with prior work:** short-term **+5.4%** (sig. 1%); cumulative
  pre-to-post one-year **+6.8%**, two-year **+5.9%**, both sig. 1%. **But less than half of targets
  experience positive long-term returns.**
- **The decomposition:** *"equal-weighted long-term returns are driven by the smallest 20% of firms
  with an average market value of $22 million. The larger 80% of firms experience insignificant
  negative long-term returns."*
  - Smallest 20%: EW long-term return reaching **+36% at two years**, significantly positive **every
    month**.
  - Larger 80%: short-term **+4.4%** significant, but **no longer significantly positive within just
    three months**, and **−1.6% at two years, insignificant**.
- **Value-weighted:** short-term only **+2.4%** (against 5.4% EW); **VW long-term returns
  insignificantly different from zero.**
- **Method:** matched 5×5×5 portfolios with a pseudo-portfolio bootstrap (1,000 draws) rather than a
  factor model — a *more* conservative significance test than the calendar-time regressions it
  criticises, not a weaker one.
- **Their criticism of the prior literature** is exactly the criticism this programme would make:
  the field gauged long-term effects on **equal-weighted means**, which can be driven by small firms
  and can obscure negative or insignificant returns for the bulk of the sample. They note Brav et al.
  (2008)'s own Table 6 Panel C tabulates insignificant VW alphas — i.e. the negative was always
  printed, just not emphasised.

**Greenwood & Schor (2009)** [PEER-REVIEWED] *Investor activism and takeovers*, Journal of Financial
Economics 92(3), 362–375. **[abstract/summary only — not opened].** 13D filings by portfolio
investors 1993–2006: announcement and long-term abnormal returns are **high for targets ultimately
acquired, and not detectably different from zero for firms that remain independent**; activist
portfolios performed poorly when market-wide takeover interest declined.

> **This is a fatal adjacency for the programme.** If the surviving part of the 13D effect is
> takeover-conditional, then the lane is **merger-arbitrage and deal prediction**, which is on the
> exclusion list. G4 cannot be rescued by conditioning on "will it be acquired" without walking
> straight into excluded ground.

**Cremers et al. (2018)** and **Allaire & Dauphin (2016)** are cited *by the SEC itself* as
researchers arguing the price reaction may reflect activists' ability to **select** issuers likely
to be taken over or to mean-revert, rather than any effect of the intervention. **[snippet only — I
saw these only as SEC footnote 830 citations; I did not open either paper.]**

### 1.4 What survives post-2010 — stated honestly, because it is thin

**I could not establish a clean, cost-honest, post-2015 replication.** What I have:

- **Lilienfeld-Toal & Schnitzler (2020)**, J. Corp. Fin. 62, 101620: **7–8% around initial 13D
  filings, 2001–2016, irrespective of filer type.** **[snippet only — this number is the SEC's
  characterisation in footnote 827 of the adopting release; I did not open the paper.]** This is the
  strongest positive evidence I found extending past 2010, and it is a *gross announcement window*,
  not a net return.
- **Swanson et al. (2022)**: **5% around initial 13D filings 1994–2014**, with **no statistically
  significant difference** between hedge funds and other private activists. **[snippet only — again
  the SEC's characterisation, footnote 827.]** The no-difference result undercuts the whole
  "activist skill" story: if a random other private activist gets the same reaction, the effect is
  about the 5% disclosure, not the filer.
- **Brav et al. (2022)**: **~2–3% announcement return for the largest two terciles** of targets,
  against **~9% for the smallest tercile**. **[snippet only — SEC footnote 829's characterisation; I
  did not open the paper.]** Note this is *another independent statement of the size concentration*,
  from the founding author, on a modern sample.
- **deHaan's sample stops at 2011.** So the strongest negative and the strongest size-decomposition
  do **not** cover the programme's 2010-01-04 → 2026-08-26 window except at its very start. **The
  post-2010 decay question is genuinely open in the literature**, and anyone who tells you it is
  settled in either direction is overreaching. What is *not* open is the size concentration: three
  separate papers across three eras (Brav 2008 EW-vs-VW; deHaan 1994–2011; Brav et al. 2022) all say
  the same thing.

**Cost-honest treatment: I found none.** Not one paper in this literature that I read or saw
summarised models a bid-ask spread, a per-share commission, or a price-impact function on the
targets actually held. The SEC's own adopting release discusses liquidity only qualitatively. **This
is a literature of gross returns on microcaps.**

---

## 2. 13G versus 13D, and conversions

**13G is the passive form.** Available to Qualified Institutional Investors (Rule 13d-1(b)), Passive
Investors under 20% with no control intent (13d-1(c)), and Exempt Investors (13d-1(d)).

**Volume — SEC primary data (DERA CSV, §4.1), initial filings per year:**

| Year | initial 13D | initial 13G |
|---|---|---|
| 2010 | 1,974 | 7,553 |
| 2015 | 1,528 | 7,467 |
| 2020 | 1,148 | 6,454 |
| 2022 | 1,164 | 8,432 |
| 2025 | 1,115 | 7,820 |

**13G outnumbers 13D roughly 6:1 on initial filings**, and by far more on amendments (2022: 18,090
13G/A against 4,014 13D/A).

**Is the passive filing informative? Structurally, mostly no.** SEC adopting release **Table 4**
(initial 13G filings in 2022, 8,433 of them) **[PRIMARY DATA DOC] [read in full]**:

| | QII | Exempt | Passive | Total |
|---|---|---|---|---|
| unique lead filers | 567 | 1,340 | 793 | 2,633 |
| initial filings | 4,660 | 1,508 | 2,222 | 8,433 |
| **median days trigger→filing** | **40** | **45** | **10** | **39** |
| median ownership reported | 6% | 15% | 6% | 7% |
| also files Form 13F | 84% | 10% | 31% | 30% |

- **QIIs are over half the filings from a fifth of the filers** — these are index and large asset
  managers crossing 5% mechanically. **Median 40 days from trigger to filing.** A signal 40 days
  stale, generated by an index fund's passive drift across a threshold, is not information about the
  issuer.
- Only the **Passive Investor** category (2,222 filings, median **10 days**) is even timely enough
  to consider, and its defining legal characteristic is a certification of **no control intent**.
- **A 1.64% market-adjusted abnormal return around 13G disclosure** appears in my search results.
  **[UNVERIFIED — this figure came from a search-result summary that blended a law-review note with
  two vendor marketing pages; I could not attribute it to a specific paper and I did not read any
  source containing it. Do not use this number.]**

**13G→13D conversion as a distinct event.** Legally real and mechanically clean: a 13G filer who
loses passive eligibility must file a 13D. Under the amended rules the deadline is **five business
days after becoming ineligible**, and the SEC's Table 1 footnote confirms the trigger date for such
a filer is *"the date on which the investor becomes ineligible to report on Schedule 13G."*

- The intuition that conversions should produce a sharper reaction than a fresh 13D — because the
  stake was already public and the *only* new information is the change of intent — is appealing
  **and I found no peer-reviewed measurement of it.** The one place I saw it asserted was vendor
  marketing copy. **[SALES INSTRUMENT] [snippet only] — not evidence.**
- **Giglia, "A Little Letter, A Big Difference"**, Columbia Law Review 116 (2016) **[law review
  student note — treat as neither peer-reviewed empirical finance nor primary data] [partially read
  — I extracted the PDF locally and read its framing and structure, but my keyword search did not
  surface the abnormal-return tables, so I am not quoting numbers from it].** Its subject is
  genuinely on point: whether activist investors **misuse** the passive 13G to avoid the attention a
  13D draws. If that misuse is common, then 13G-as-passive is a contaminated label and conversions
  are partly re-labelling rather than genuine intent changes.

**Assessment:** 13G is not a promising lane on its own — dominated by mechanical institutional
crossings at a 40-day median lag. The **conversion** event is the only interesting object here, it
is unmeasured in the literature I could reach, and it inherits every size and cost problem of §1
while being *rarer* than 13D.

---

## 3. THE DEADLINE — a structural break in the middle of the sample

**Primary source, read in full.** SEC, *Modernization of Beneficial Ownership Reporting*, **Release
Nos. 33-11253; 34-98704; File No. S7-06-22**, RIN 3235-AM93, adopted **October 10, 2023**. Fetched
as `sec.gov/files/rules/final/2023/33-11253.pdf` and extracted to text locally (295 pages).
**[PRIMARY DATA DOC] [read in full — the DATES section, the §II.A comparison table, and §II.G
compliance dates were read verbatim].**

### 3.1 Dates, verbatim

- *"DATES: Effective dates: The amendments are effective on **February 5, 2024**."*
- **Schedule 13G deadlines:** *"compliance with the revised Schedule 13G filing deadlines under
  Rules 13d-1 and 13d-2 will not be required before **September 30, 2024**... beneficial owners will
  continue to be required to comply with the current Schedule 13G filing deadlines through September
  29, 2024."*
- **Structured data:** *"compliance with the structured data requirement for Schedules 13D and 13G
  will not be required until **December 18, 2024**"*, with voluntary early compliance permitted from
  **December 18, 2023**.
- **No transition period was given for the 13D deadline changes** — they bind from the effective
  date, **February 5, 2024**.

### 3.2 Old versus new, from the release's own comparison table

| Item | Current 13D | **New 13D** | Current 13G | **New 13G** |
|---|---|---|---|---|
| Initial deadline | 10 calendar days after crossing 5% | **5 business days** | QII/Exempt: 45d after **year**-end; QII: 10d after month-end >10%; Passive: 10 days | QII/Exempt: **45d after calendar QUARTER-end**; QII: **5 business days** after month-end >10%; Passive: **5 business days** |
| Amendment deadline | "**Promptly**" after triggering event | **Within 2 business days** | All: 45d after year-end; QII: 10d after month-end; Passive: promptly | All: **45d after quarter-end**; QII: **5 bd** after month-end; Passive: **2 bd** |
| Amendment trigger | Material change | unchanged | **Any** change | **Material** change |
| **Filing cut-off time** | **5:30 p.m. ET** (Rule 13(a)(2) Reg S-T) | **10:00 p.m. ET** (Rule 13(a)(4)) | **5:30 p.m. ET** | **10:00 p.m. ET** |

### 3.3 How the sample splits — declare this in advance

A study spanning 2010-01-04 → 2026-08-26 **straddles four regimes**, not two:

| Segment | Regime |
|---|---|
| 2010-01-04 → **2024-02-04** | 13D: 10 calendar days, "prompt" amendments. 13G: annual cadence. Cut-off 5:30 p.m. ET. |
| **2024-02-05** → 2024-09-29 | 13D: **5 business days**, 2-bd amendments, **10 p.m. cut-off**. 13G: still on OLD deadlines. |
| **2024-09-30** → 2024-12-17 | 13G now on new deadlines (**quarterly** cadence). Both forms still HTML/ASCII. |
| **2024-12-18** → 2026-08-26 | **Structured XML mandatory**, and the EDGAR **form-type string changes** (§4.2). |

That is **~14.1 years of the 16.6-year sample in the old regime and ~2.5 years in the new**, with
two narrow transition strips. Any per-era split must use these four boundaries, and the
**2024-12-18** boundary is the one that breaks code rather than statistics.

**Observable consequence I verified directly.** The 13G cadence change from annual to quarterly is
visible in the raw daily indices: on **2018-02-14** (old regime, 45 days after year-end) I counted
**1,120 initial 13Gs and 2,781 13G/As in a single day**; on **2026-05-14** (new regime, 45 days
after Q1-end) **210 initial and 383 amendments**. The seasonal spike moved from one annual mid-
February wall to four smaller quarterly ones. Any study using 13G will see its event density
restructured at 2024-09-30 for purely regulatory reasons.

---

## 4. THE DATA QUESTION

This is where the lane pays for itself even though it fails.

### 4.1 What to pull, free, dead-inclusive, point-in-time

**Use the EDGAR full-index, not a ticker map.** Verified by fetching real files:

- **Quarterly:** `https://www.sec.gov/Archives/edgar/full-index/{YYYY}/QTR{1-4}/form.idx` — verified
  present for 2015Q1 alongside `company.idx`, `master.idx`, `crawler.idx` and `.gz`/`.zip`/`.Z`
  variants. **[PRIMARY DATA DOC] [read — directory listing fetched]**
- **Daily:** `https://www.sec.gov/Archives/edgar/daily-index/{YYYY}/QTR{n}/form.{YYYYMMDD}.idx` —
  verified for 8 separate dates spanning 2011-06-15 to 2026-05-14, business days only. **[read — I
  downloaded and parsed all eight]**
- **Format**, verified verbatim from the 2015-03-04 file: fixed-width, 11 header lines, then
  `Form Type | Company Name | CIK | Date Filed | File Name`, where File Name is
  `edgar/data/{CIK}/{accession}.txt`.

**Why this direction is right, and why the programme's current direction is wrong.** The full-index
is **a record of what was filed that day**. A company that delisted in 2013 still has its 2012
filings in the 2012 index, permanently. Enumerating events from the index is **dead-inclusive by
construction** and needs no ticker map at all. You then join CIK → symbol only for CIKs that appear,
which is a much smaller problem than enumerating a universe.

**The `company_tickers.json` trap is real and the programme is already exposed to it.**
`scripts/d331_edgar_deals.py:1-46` documents its symbol→CIK path as (a) `company_tickers.json`, (b)
`include/ticker.txt`, (c) EDGAR full-text search. **(a) and (b) are current-state files: they map
tickers that exist today.** The existing puller is aware enough to grade confidence
high/low/unresolved and to cross-check against filing history — but the *direction* (symbol → CIK)
is the survivorship-exposed one. **For 13D/G, invert it: index → accession → subject CIK → symbol.**

**A second, independent count source:** SEC DERA publishes filing counts by form type and year at
`https://www.sec.gov/files/dera/data/number-edgar-filings-form-type/filings_type_year_0626.csv`
(1993 → June 2026, columns `Year,Type,Count`, updated quarterly). **[PRIMARY DATA DOC] [read in full
— downloaded and parsed the raw CSV locally rather than trusting a summary, which mattered: the
fetch tool's summary of this file shifted every year by one row].**

### 4.2 The bug that would have silently zeroed the modern sample

**The EDGAR form-type string for these filings changed at the structured-data mandate.** Verified
four independent ways:

| Evidence | Old | New |
|---|---|---|
| daily `form.idx` 2015-03-04 | `SC 13D`, `SC 13D/A`, `SC 13G`, `SC 13G/A` | — |
| daily `form.idx` 2025-03-04 | — | `SCHEDULE 13D`, `SCHEDULE 13D/A`, `SCHEDULE 13G`, `SCHEDULE 13G/A` |
| EDGAR FTS `form_filter` bucket, 2015-03-03/05 | `SC 13D` (60 docs) | — |
| EDGAR FTS `form_filter` bucket, 2025-03-03/05 | `forms=SC 13D` returns **0 hits** | `SCHEDULE 13D` (67 docs) |

And the DERA CSV dates the changeover exactly:

| Year | `SC 13D` | `SCHEDULE 13D` |
|---|---|---|
| 2023 | 1,260 | 0 (1 `SCHEDULE 13G` — voluntary early filer) |
| 2024 | 1,024 | **76** |
| 2025 | 0 | **1,115** |

> **A runner filtering `form == "SC 13D"` returns zero filings from ~2024-12-18 onward and will not
> raise.** It will produce a clean-looking backtest whose modern era is empty. This is precisely the
> class of failure the programme's *"assert code, not data"* and *"a self-test that cannot fail is
> worse than none"* rules exist to catch. **Match `form.upper().startswith(("SC 13", "SCHEDULE
> 13"))` and assert both spellings appear in the expected eras.**

### 4.3 The issuer identifier — CIK is certain, and there is a subtlety

**Verified on a real filing** (accession `0000921895-25-000684`, fetched its `-index.htm`):

- The filing index page carries **explicit `Filed by` and `Subject Company` labels, each with a
  CIK**: filed by *Radoff Bradley Louis* (CIK 0001380585), subject company *Atea Pharmaceuticals,
  Inc.* (CIK 0001593899).
- **But the full-index does NOT label which is which.** Verified on 2025-03-04: accession
  `0000921895-25-000684` appears on **two rows** — one under the issuer's CIK, one under the filer's
  CIK. Same for `0001104659-25-020048` (Sanford Glenn Darrel / eXp World Holdings). Across all four
  form buckets on both sample days, **distinct accessions were exactly rows÷2**.
- **Consequence:** you cannot take the CIK from the index row. You must fetch the filing's header or
  index to separate subject from filer. A group filing with several reporting persons produces more
  than two rows, so `rows÷2` is a diagnostic, **not** a rule to rely on.
- **CUSIP:** the Schedule 13D cover page has carried a CUSIP field since long before EDGAR, and the
  structured filing makes it an XML element. **[UNVERIFIED as to whether it is a *required* element
  — see §8.3.]** CUSIP is in any case **not point-in-time safe on its own**: it is reassigned and it
  changes on reorganisation. **Use CIK as the join key.** CIK is permanent, never recycled, and
  survives ticker changes and delisting — it is the only identifier here that is genuinely
  point-in-time.
- **Ticker does not reliably appear** in the filing body or header in a machine-readable place. The
  `submissions` API returns a `tickers` array **for the entity as it stands today**, which is a
  survivorship artefact and must not be used to reconstruct what the ticker was on the filing date.

### 4.4 Structured data

- **Mandatory from 2024-12-18** (voluntary from 2023-12-18) per §II.G of the adopting release.
- Primary document is `primary_doc.xml` — confirmed on the Atea filing, 24,808 bytes, listed as the
  primary document with type `SCHEDULE 13D`.
- Spec: *EDGAR Schedule 13D and 13G XML Technical Specification 2.0*, `sec.gov/file/schedule-13d-13g-tech-specs-20`.
  **[PRIMARY DATA DOC] [UNVERIFIED CONTENT — WebFetch → sec.gov/file/schedule-13d-13g-tech-specs-20:
  HTTP 200 but the page is a landing page whose payload is a 692.54 KB ZIP; I did not download or
  open the ZIP, so I have not read the element names or cardinalities.]**
- **Practical consequence for a 2010–2026 study: the structured era is only the last ~1.7 years.**
  For 14+ years you are parsing free-text HTML/ASCII 13Ds. The structured format does not rescue the
  historical sample; it only makes the tail of it easier and *changes the form-type string* (§4.2).

### 4.5 Access mechanics

- Rate limit and User-Agent: the existing puller
  (`scripts/d331_edgar_deals.py:34-38`) already records the operational truth — *"the SEC edge
  returns 403 to any User-Agent without an email-shaped token"* — and self-limits to **≤8
  requests/second** with backoff on 429/403/5xx and on-disk caching of raw 200s. That machinery is
  directly reusable.
- **Implementation distance is genuinely short** — index parsing plus a header fetch per accession.
  At ~1,400 initial 13Ds/year × 16 years ≈ **22,400 accessions**, at 8 rps that is roughly **47
  minutes** of fetching, cacheable. That is the *only* cheap thing about this lane.

---

## 5. Look-ahead rules — what timestamp a runner must key on

**Key on `acceptanceDateTime`, never on `filingDate`.** Three verified facts:

1. **The submissions API exposes it.** `https://data.sec.gov/submissions/CIK##########.json` →
   `filings.recent.acceptanceDateTime`, an **ISO-8601 UTC** string, e.g.
   `"2026-09-03T22:30:44.000Z"`. **[verified by fetching CIK0000320193 and reading the schema]**
   Note that example: **22:30 UTC is 18:30 ET — two and a half hours after the close.**
2. **Filings ARE accepted after the close, and carry that day's date.** Before 2024-02-05 the
   cut-off was **5:30 p.m. ET**; from 2024-02-05 it is **10:00 p.m. ET** for 13D/G specifically
   (Rule 13(a)(4) of Reg S-T). So a 13D stamped `filingDate = D`:
   - pre-2024: could have been accepted up to **1.5 hours after** the 4 p.m. close of D;
   - post-2024-02-05: up to **6 hours after** the close of D.
3. **The programme's existing puller does not capture it.** `grep` over
   `scripts/d331_edgar_deals.py` finds `filingDate` (line 254, 271) and **no occurrence of
   `acceptance`**. Any 13D work built on that code inherits a look-ahead of up to six hours.

**The rule a runner must implement:**

```
accept_et = acceptanceDateTime (UTC) -> America/New_York
if accept_et < 16:00 on a trading day D:  first tradeable bar = next session's OPEN after D
else:                                     first tradeable bar = the OPEN of the session after D
```
In practice both branches land on the next open, which is the safe and simple rule: **never trade
the close of the filing date.** Doing so is look-ahead in every era of this sample, and the
exposure roughly quadrupled on 2024-02-05.

**A second look-ahead trap specific to this form.** The `filingDate` is not the event date the
literature uses either — the SEC's Table 1 shows a **median 9–10 calendar days** between the
*trigger date* (crossing 5%) and the filing. The trigger date is disclosed **inside** the filing.
Keying on the trigger date is a look-ahead of about ten days; keying on filing date is correct but
means the run-up is already spent (§1.1).

**Timezone hazard worth an assertion:** `acceptanceDateTime` is UTC and the ET offset changes with
DST. A naive `-5` shift mis-times every filing between March and November. `assert` the converted
hour distribution has no mass after 22:00 ET.

---

## 6. THE PREMISE NUMBERS

### 6.1 Count of initial 13D filings per year — SEC DERA primary data

**[PRIMARY DATA DOC] [read in full — parsed the raw CSV locally]**

| Year | initial 13D | Year | initial 13D |
|---|---|---|---|
| 2010 | 1,974 | 2018 | 1,290 |
| 2011 | 1,870 | 2019 | 1,117 |
| 2012 | 1,488 | 2020 | 1,148 |
| 2013 | 1,462 | 2021 | 1,557 |
| 2014 | 1,535 | 2022 | 1,164 |
| 2015 | 1,528 | 2023 | 1,260 |
| 2016 | 1,409 | 2024 | 1,100 |
| 2017 | 1,336 | 2025 | 1,115 |

**Total 2010–2025: 22,353. Mean 1,397/year.** 2026 through June: 574 (≈1,148 annualised).

**Triangulation, three ways, all agreeing:**
- SEC staff text in the adopting release: *"for the years 2011 through 2022, the average number of
  filings per year were roughly **1,400** and 4,100 for initial and amended Schedule 13D filings
  respectively"* (against ~2,800 and ~5,200 for 1997–2010 — **the form has been in secular decline,
  which SEC staff attribute to the falling number of listed companies**).
- SEC Table 1: **1,161** initial 13D filings in 2022 (DERA CSV: 1,164 — a 3-filing discrepancy,
  immaterial).
- **My own independent count** from 8 raw daily indices: 4.3–5.5 initial 13Ds/day → **1,080–1,386
  per year.** Consistent.

**These counts are of FILINGS, not of US operating companies.** They include filings on foreign
private issuers, closed-end funds, trusts, SPACs and non-operating shells. **I did not measure the
operating-company fraction** — see §8.1.

### 6.2 The count that actually matters — and it is ~60, not ~1,400

**SEC adopting release Table 2**, initial 13D filings **2011–2021** (staff programmatic + manual
review of transaction histories). **[PRIMARY DATA DOC] [read in full]**

| | Number | % of all | Prominent Activists | Other Institutions | Other Individuals |
|---|---|---|---|---|---|
| **Non-corporate-action** (SEC: *"more likely to involve activist campaigns"*) | **3,067** | **20%** | 28% | 65% | 7% |
| **Corporate action** | **12,657** | **80%** | 3% | 67% | 30% |

**SEC adopting release Table 1**, initial 13D filings in **2022** by filer type:

| | Prominent Activists | Other Institutions | Other Individuals | All |
|---|---|---|---|---|
| unique lead filers | **22** | 720 | 252 | 994 |
| **initial filings** | **60** | 843 | 258 | **1,161** |
| median days trigger→filing | **9** | 10 | 11 | 10 |
| median ownership reported | 6.6% | 15.0% | 10.5% | 13.0% |

**The funnel, on primary SEC data:**

```
~1,400 initial 13D filings/year          <- the number a naive study would use
  x 20% non-corporate-action              -> ~280/year plausibly a campaign at all
     of which 28% prominent activists     -> ~78/year  (2011-2021 basis)
  SEC Table 1 direct count, 2022          -> 60/year by 22 filers
```

**80% of initial 13Ds are not campaigns.** They arise from mergers, reorganisations, private
placements, conversions and control transfers — the SEC's own label is "corporate action filings",
and 30% of them are filed by *individuals*. A study that trades every 13D is trading ~80% noise, and
a large part of that noise is **deal-related**, i.e. excluded ground.

### 6.3 The lag — SEC Table 3, and it is worse than "a lag"

**SEC adopting release Table 3**, non-corporate-action initial 13Ds, **2011–2021**:

| Percent of stake accumulated by the (new) 5-business-day deadline | 100% (full stake) | <100% | <90% | <75% |
|---|---|---|---|---|
| campaigns | **1,907** | 463 | 78 | 16 |
| % of sample | **80%** | 20% | 3% | 1% |
| avg campaigns/year | **173** | 42 | 7 | 1 |

**In 80% of activist campaigns the filer had finished buying before five business days had
elapsed** — i.e. before the filing was made, since median trigger→filing is 9–10 days. Only **1%**
had less than three-quarters of their stake at that point.

**This is the honest statement of the lag: by the time it is public, the accumulation is not
"already under way" — it is finished.** And the pre-filing price run-up (3.2% over t−10..t−1) and
volume spike are that finished accumulation, plus, per Brav-Jiang-Kim, possible wolf-packing and
tipping. **What is left for a reader of the filing is the 2.0% filing-day jump and whatever drifts
after.**

Also from the release: in 2022 only **71%** of initial 13Ds were filed inside the old 10-day window;
**34%** were filed *on* the deadline; **~29% were late**. Late filing is common enough that
"trigger + 10 days" is not a usable proxy for the filing date.

### 6.4 What the $5 and dollar-volume floors do — the kill

**I cannot compute the exact pass rate without the fixture, and I will not invent it.** What the
external evidence pins down:

- **Brav et al. (2008): median target market cap $160m**, 2001–2006 dollars. Their own methodology
  section concedes a 13D-based search *"could bias the sample toward smaller"* companies, which is
  why they hand-added large-cap events with a **$1bn** cutoff.
- **deHaan et al.: the entire equal-weighted long-run result comes from the smallest quintile, whose
  average market cap is $22 million.** The other 80% is +4.4% short-term decaying to an insignificant
  −1.6% over two years.
- **Brav et al. (2022) [snippet only, via SEC fn. 829]: ~9% announcement for the smallest tercile,
  ~2–3% for the largest two.**
- **SEC fn. 829, in the regulator's own voice:** *"the degree of impact ... varies significantly with
  an issuer's market capitalization, with smaller-cap issuers experiencing significantly larger
  returns (expressed as a percentage) ... than larger-cap issuers."*

**The arithmetic against this programme's cost structure:**

- Measured spread on names actually held: **33.8 bp/side → ~67.6 bp round trip**, before IBKR
  per-share commission, and **cost in bp scales inversely with price**, so a $5–8 stock is worse
  than the 33.8 bp average, not better.
- Against a **2.0% filing-day-plus-one** gross jump you cannot capture (it happens while the filing
  is being read, and you may only get the next open), and a post-filing drift that is **~1.09%/month
  for three months equal-weighted and statistically zero value-weighted**, the round trip eats a
  meaningful share of a drift that is *itself* only significant in the size bucket the floor
  removes.
- **The floor and the signal are anti-correlated by construction.** A $5-close plus dollar-volume
  screen is, almost exactly, a filter that removes deHaan's smallest quintile — the only quintile
  where the effect survives two years.

**Event count after floors — an estimate, flagged as an estimate.** Starting from ~60 prominent-
activist 13Ds/year and applying *any* price/liquidity floor to a population whose median cap is
~$160m and whose profitable tail averages $22m, **the surviving count is plausibly a few dozen per
year at best**. At 15 years that is a few hundred events, equal-weighted, on a two-sided fat-tailed
distribution where **fewer than half of targets have positive long-term returns** — an N at which
this programme's own D307/D373 experience says the trimmed-mean and null-margin machinery will
return UNRESOLVED rather than a verdict. **This number is not measured. §8.1.**

---

## 7. Vendors — cited only as evidence of crowding, never of return

**None of the following is evidence for a return. Every one is a [SALES INSTRUMENT].**

- **13D Monitor** (`13dmonitor.com`) — activism research subscription. **[snippet only]**
- **13D Activist Fund** (`13dactivistfund.com`, mutual fund share class **DDDIX**) — a registered US
  mutual fund whose stated mandate is investing alongside 13D filers. **[snippet only]** Its
  existence is the crowding datum: **this signal has a retail wrapper.** Search results also
  surfaced practitioner commentary that activist hedge funds trailed the S&P 500 over 1-, 3-, 5- and
  7-year windows through end-2015 **[UNVERIFIED — search-summary only, not opened; do not cite the
  performance claim]**.
- **FactSet SharkRepellent / "Sharkwatch 50"** — the activist-identification database. Notably, **the
  SEC itself used it** to build the "prominent activists" category in Table 1/Table 2, and noted a
  commenter challenging whether the data is *"accurate and current."*
- **Insightia** (now Diligent) — activist rankings; the SEC supplemented Sharkwatch 50 with
  Insightia's annual top-activist ranking.
- **Meridian, HedgeTrace, StockCliff, Toppan Merrill, Workiva** — content-marketing pages surfaced by
  my searches. The 13G/13D return figures in my search results traced back to these, which is why
  §2's 1.64% is marked UNVERIFIED and unusable.

**The crowding read.** When the *regulator* adopts a vendor's activist taxonomy in a rulemaking, and
a retail mutual fund exists to trade the filings, and the founding academic paper's own authors
attribute a 14%→4% decay to competitive entry — the prior that a further-decayed 2020s version of
this effect is available to a daily-bar, equal-weighted, cost-honest retail book is very low.

---

## 8. What I could not verify, stated plainly

1. **The operating-company and floor-pass rates — the two numbers the commission asked for most
   directly.** I established the total (1,397 initial 13Ds/year, 2010–2025) from SEC primary data
   and independently from raw daily indices. **I did NOT establish (a) how many land on US
   *operating* companies rather than funds, trusts, foreign private issuers and shells, nor (b) how
   many pass a $5-close plus dollar-volume screen on the filing date.** Neither is derivable from
   any published source I found; both require joining the filings to price data, which is exactly
   what this programme has and I do not. **The method is in §4: pull the full-index, split
   subject-vs-filer CIK from the filing header, join CIK→symbol, and evaluate the floor on the
   filing date.** My "a few dozen per year" in §6.4 is an inference from median market caps, not a
   measurement, and should be treated as a hypothesis to test, not a finding.
2. **Post-2015 announcement returns.** The strongest post-2010 positive evidence I have
   (Lilienfeld-Toal & Schnitzler 2020, 7–8% through 2016; Swanson et al. 2022, 5% through 2014;
   Brav et al. 2022 tercile split) reached me **only as the SEC's characterisation in footnotes 827
   and 829 of the adopting release. I did not open any of those three papers.** Every number
   attributed to them in this brief carries that caveat in the same sentence. **There is no
   post-2020 measurement in this brief at all**, from any source, and I could not find one.
3. **The Schedule 13D/G XML element names and cardinalities.** WebFetch →
   `sec.gov/file/schedule-13d-13g-tech-specs-20`: HTTP 200, but the page is a landing page whose
   payload is a 692.54 KB **ZIP**, which I did not download or open. **So I could not confirm
   whether CUSIP is a *required* element, nor the tag names for percent-of-class, voting/dispositive
   power, or the Item 4 purpose text.** My §4.3 recommendation to key on CIK does not depend on
   this, but anyone planning to parse the structured filings must open that ZIP first.
4. **Federal Register text.** WebFetch → `federalregister.gov`: **HTTP 302** redirect to
   `unblock.federalregister.gov`. I did not follow it. **I substituted the SEC's own conformed
   copy** (`sec.gov/files/rules/final/2023/33-11253.pdf`), which is stated on its face to be
   *"Conformed to Federal Register version"* — so §3 rests on an SEC primary document, not on the
   blocked one.
5. **Klein & Zur (2009) and Greenwood & Schor (2009).** **Abstract/summary only — I did not open
   either.** The 10.2%/5.1% figures and the "zero for firms that remain independent" finding are
   reported as summaries, not as my readings. Greenwood & Schor's takeover-conditionality is
   load-bearing for my §1.3 exclusion-list warning, and it deserves a direct read before anyone
   relies on that warning.
6. **The Columbia Law Review note (Giglia 2016) on 13G misuse.** PDF extracted locally and its
   framing read, **but my keyword search did not surface its empirical tables**, so I quote **no
   numbers** from it. Its question — whether activists systematically mis-file as passive — is
   directly relevant to whether 13G→13D conversions are real intent changes, and it is unresolved
   here.
7. **The "1.64% around 13G disclosure" figure.** Traced only to a blended search summary drawing on
   vendor marketing pages. **[UNVERIFIED — do not use.]** I found **no** peer-reviewed measurement
   of 13G announcement returns or of 13G→13D conversion returns that I could read.
8. **The "15.9% (2001) → 3.4% (2006)" decay pair.** Widely repeated in search results and attributed
   to Brav et al. (2008). **I read that PDF in full and could not locate those two figures.** I
   report instead the ~14%→<4% pair that I did verify in Brav-Jiang-Kim's text.
9. **Whether `rows ÷ 2` holds generally in the full-index.** It held exactly on both sample days
   across all four form buckets, but a group filing with several reporting persons will produce more
   than two rows. **Do not rely on it; dedupe on accession and read the header.**
10. **Vendor performance claims.** No vendor return figure in §7 was verified and none should be
    used. I did not access any product, create any account, or submit any form.

### Safety note

**No page, PDF or search result I read contained text addressed to me or instructing me to take any
action.** Nothing required quoting and flagging on those grounds. The one thing worth recording is
mechanical rather than adversarial: the **fetch tool's summary of the DERA CSV silently shifted
every year by one row**, which I caught only by downloading the raw file and parsing it myself. Two
academic PDFs and the 295-page SEC release also came back from the fetch tool as
"corrupted/unreadable" and were fine once extracted locally with `pypdf`. **Where a number in this
brief is marked [read in full], it was read from a locally extracted file, not from a tool
summary.**
