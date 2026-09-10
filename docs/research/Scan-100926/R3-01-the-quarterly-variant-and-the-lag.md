# `C1` — THE QUARTERLY, POINT-IN-TIME PROFITABILITY VARIANT, AND THE LAG A FILING-DRIVEN BOOK MUST CARRY

**Round 3, lane `C1`.** Campaign contract: [`00-SCHEMA.md`](00-SCHEMA.md). Slate:
[`R3-00-slate.md`](R3-00-slate.md). Round 2: [`R2-99-record.md`](R2-99-record.md), and in
particular [`R2-02`](R2-02-profitability-deep.md) §7.5, whose open flag this lane exists to settle.

Under [R15](../../RULES.md#r15) **nothing here closes or admits anything**, nothing is elevated into
`FINDINGS.md`, `RULES.md`, the books or a decision record. Both books are unchanged. **This lane had
no access to the programme's fixture and claims nothing about it.**

---

## 0. THE ANSWER, STATED FIRST AND STATED NEGATIVELY

**The bar asked for a named quarterly construction with its lag, its evidence and its tag list — or
a finding that the quarterly advantage does not survive the constructions round 2 showed matter. IT
IS THE FIRST, AND THE THING THAT SURVIVES IS NOT THE THING ROUND 2 RECOMMENDED.**

1. **THE QUARTERLY ADVANTAGE SURVIVES THE LAGGED DEFLATOR, AND IT IS *LARGEST EXACTLY WHERE THE
   LAGGED DEFLATOR DID THE KILLING*.** Hou–Xue–Zhang measure both sides with **one-quarter-lagged**
   assets. Gross profits-to-lagged-assets goes **`0.16` [`t` 1.04] annual → `0.51` [`t` 3.40]
   quarterly**; operating profits-to-lagged-assets **`0.20` [`1.07`] → `0.72` [`3.35`]**. Round 2's
   central negative — that `t` 3+ collapses to 1.04–1.85 when you lag the deflator — **is an
   ANNUAL-FREQUENCY result. It does not reproduce at quarterly frequency.** §4.

2. **AND THE ONE DEFINITION ROUND 2 RECOMMENDED IS THE ONE THAT GAINS NOTHING.** Cash-based
   operating profitability, same table, same deflator: **`0.53` [`3.02`] annual → `0.49` [`3.02`]
   quarterly at the 1-month horizon.** Flat. `CbOP`'s advantage is an *annual* advantage; at
   quarterly frequency gross and operating profitability catch it up. §4.2. **In a different
   weighting (`P4`'s equal-weighted quintiles) `CbOP` does gain, `0.46`→`0.86`. The two sources
   disagree and I record both.** §4.3.

3. **THE FIELD HAS FIVE MUTUALLY INCOMPATIBLE QUARTERLY LAG CONVENTIONS, SPANNING ROUGHLY TWO AND A
   HALF MONTHS**, and the same author uses two different ones twelve years apart: **RDQ-month + 1**
   (Novy-Marx 2013), **RDQ-month exactly** (Novy-Marx & Velikov's own 2023 toolkit code),
   **`max(fiscal-quarter-end + 3 months, RDQ month)`** (Chen–Zimmermann), **fiscal quarter ending at
   least 4 months ago** (Hou–Xue–Zhang), **fiscal period end + 4 months** (Jensen–Kelly–Pedersen).
   §5.

4. **WHETHER IT IS JUSTIFIED OR INHERITED: BOTH, AND THE MOST HONEST DOCUMENT IN THE FAMILY IS A
   GITHUB ISSUE THREAD.** `OpenSourceAP/CrossSection` issue **#50** is a dated, measured, twelve-
   comment argument about exactly this lag, containing a **retracted** statistic, the finding that
   the 3-month assumption is a look-ahead for **4.25%** of firm-quarters with a known announcement
   date, and the maintainer's stated reason for a minimal patch rather than a correct fix: *"I don't
   want to mess people up too much who are already using the data."* **He also writes that the
   affected quarterly predictors include *"some of these from what I recall have the largest
   t-stats."*** §5.3.

5. **NOBODY MEASURES THE PREMIUM'S SENSITIVITY TO THE LAG AT THE GRANULARITY THE QUESTION NEEDS.**
   The closest is Ball, Gerakos, Linnainmaa & Nikolaev's Figure 1 — Fama-MacBeth slopes at lags from
   0 to 10 years **in six-month increments** — and **its values are in a plot, not a table.** No
   source varies the lag by one month, or by three-versus-four, holding everything else fixed. §6.1.

6. **`[MEASURED IN BRIEF]` THE SMALLEST DEFENSIBLE LAG IS NOT WHAT THE CONVENTIONS SAY, AND THE
   BINDING CONSTRAINT IS THE CLOCK, NOT THE CALENDAR.** On SEC as-filed data: the 10-Q filing lag
   has **p50 38–39 days, p90 45 days, p95 50 days**, and **97.7% of a fiscal quarter's 10-Q filers
   have filed by day 60**. Going from a 3-month to a 4-month lag buys **0.4–0.5 percentage points**
   of cross-sectional coverage. **But only 35.2% of 2025 10-Qs are accepted before 16:00 ET —
   47.9% land in the 16:00 hour alone — so for ~65% of filings the earliest tradeable close is the
   NEXT day, and a `filed`-date rule is a same-session look-ahead for 58.5% of them.** §6.

7. **`[MEASURED IN BRIEF]` THE TAG LIST SURVIVES AT QUARTERLY FREQUENCY FOR GROSS PROFITABILITY AND
   FOR NOTHING ELSE.** Single-quarter gross profitability is computable for **2,490 → 2,296 →
   2,082** CIKs (2013/2019/2025). Operating profitability: **1,285 → 1,143 → 1,066**. `CbOP`, all
   balance-sheet terms present: **11 → 12 → 9.** Not a typo. §7.

8. **`[MEASURED IN BRIEF]` THE DEFLATOR THAT MAKES THE QUARTERLY RESULT WORK IS NOT IN THE FILING
   THAT CARRIES THE NUMERATOR.** One-quarter-lagged `Assets` appears in only **3.5–5.3%** of 10-Qs;
   Reg S-X puts the *prior fiscal year end* on the comparative balance sheet, not the prior quarter.
   Stitching the previous 10-Q recovers it at **86.3% / 90.5% / 92.0%** — so the HXZ/OSAP deflator
   costs **8–14% of the computable cross-section** relative to Novy-Marx's current-quarter one. **No
   source states this.** §7.4.

**The precise negative I would put above all of this:** the quarterly variant is the version of this
family that the deflator argument does *not* kill, that XBRL does compute, and that no reference
implementation treats as a predictor — **all three of Chen–Zimmermann's quarterly profitability
variants are shipped as PLACEBOS, none has a published paper behind it, and the timing rule under
them was patched for backward compatibility rather than for correctness.**

---

## 1. SOURCES — TYPE, AND SEPARATELY, HOW WELL ESTABLISHED

| # | source | type | established |
|---|---|---|---|
| `S1` | **Novy-Marx**, *The other side of value*, **JFE 108(1), 2013** — published article, 28 pp, `oldschoolvalue-files.s3.amazonaws.com` mirror, extracted locally with `pypdf`, **title line checked** | [PEER-REVIEWED] | **[read in full]** of Appendix A.4, footnote 3 and **Table A6, every cell transcribed by me** |
| `S1d` | **The same paper's JUNE 2012 draft**, 73 pp, `mysimon.rochester.edu/novy-marx/research/OSoV.pdf` (the author's own page) | [WORKING PAPER] | **[read in full]** of the same passages, **compared cell by cell against `S1`** (§3.1) |
| `S2` | **Hou, Xue & Zhang**, *Replicating Anomalies*, **NBER w23394 (May 2017)**, 130 pp; published RFS 33(5) 2020 | [WORKING PAPER] for the text read | **[read in full]** — Appendices A.4.9–A.4.20, §3.2.4, §3.3, and **Table 3 Panel D + Table 4 columns 109–126 transcribed by me** |
| `S3` | **Chen & Zimmermann**, *Open Source Cross-Sectional Asset Pricing*, **FEDS 2021-037**, 66 pp | [WORKING PAPER] / primary data doc | **[read in full]** of §2.4's timing paragraph, footnote 13, and **Table 4's six profitability rows re-transcribed by me independently of round 2** |
| `S3c` | **The same project's CODE**: `pyCode/DataDownloads/CompustatQuarterly.py`, `LegacyStataCode/DataDownloads/C_CompustatQuarterly.do`, `Placebos/GPlag_q.{py,do}`, `Placebos/OperProfRDLagAT_q.py`, plus the 771-path repo tree | [SOFTWARE DOC] | **[read in full]**, both language ports, quoted verbatim in §5.2 and §8.3 |
| `S3i` | **`OpenSourceAP/CrossSection` GitHub issue #50**, *"Compustat quarterly data"*, opened 2021-09-04, closed 2022-02-14, **12 comments**, plus its two embedded screenshots read as images | [SOFTWARE DOC] — the field's only public argument about this lag | **[read in full]**, quoted verbatim in §5.3 |
| `S3d` | **`SignalDoc.csv`** from the same repo, 331 rows, 29 columns | [PRIMARY DATA DOC] | **[read in full]** for the twelve rows quoted; whole-file tallies computed by me |
| `S4` | **Ball, Gerakos, Linnainmaa & Nikolaev**, *Deflating profitability* (cover sheet: *Deflating Gross Profitability*), **Chicago Booth Paper 14-10, 6 May 2014**, 49 pp, `ivey.uwo.ca/media/3775544/linnainmaa.pdf`. Published **JFE 117(2), 2015** | [WORKING PAPER] | **[read in full]** — **ROUND 2 RECORDED THIS PAPER AS UNOBTAINABLE BY FOUR ROUTES.** §9.1 uses it to correct an inherited cell. **Figure 1's VALUES are in a plot and I read none of them** |
| `S5` | **Novy-Marx & Velikov**, *Assaying Anomalies* (2023) — **the paper is still not obtained; the TOOLKIT CODE is**: `velikov-mihail/AssayingAnomalies`, `getCOMPUSTATAdditionalData.m`, `getCOMPUSTATQuery.m`, `makeCOMPUSTATVariables.m`, 1,476-path tree | [SOFTWARE DOC] — **interested** (Novy-Marx authored the measure) | **[read in full]** of the three files; the quarterly timing block quoted verbatim in §5.4 |
| `S6` | **Jensen, Kelly & Pedersen**, *Global Factor Data Documentation*, 55 pp, `jkpfactors.s3.amazonaws.com/documents/Documentation.pdf` | [PRIMARY DATA DOC] | **[read in full]** of §§2, 6.1–6.4 and the Table 8 profitability rows |
| `S7` | **Sotes-Paladino, Wang & Yao**, *The Value of Growth: Changes in Profitability and Future Stock Returns*, **November 2016 working paper**, 61 pp, EFMA 2017 Athens copy; **published JBF 2023 (version NOT obtained)** | [WORKING PAPER] | **[read in full]** of §2.1, footnotes 1/5/6/7, §5.1.1 and the Appendix A3 discussion |
| `S8` | **Novy-Marx & Medhat**, *Profitability Retrospective: What Have We Learned?*, **NBER w33601 (Mar 2025)**, 78 pp. **Medhat is at Dimensional; Novy-Marx authored the measure** | [WORKING PAPER] — **interested on both counts** | **[read in full] FOR THE PURPOSE OF A NEGATIVE**: the strings `quarterly`, `REVTQ`, `RDQ`, `high frequency` and `season` were searched across the whole extracted text. §4.5 |
| `S9` | **Asness, Frazzini & Pedersen**, *Quality Minus Junk*, **9 Oct 2013 draft**, 60 pp, two independent mirrors (Yale, tevgeniou) — **both are the same October 2013 draft**; the published RAST 2019 version was **NOT obtained** | [WORKING PAPER] | **[read in full]** of §2 (Data) — and it is **annual**, so it is a negative for this lane. §5.6 |
| `M1` | **My own SEC FSDS measurement** — filing-lag distribution, acceptance clock, quarterly tag census, computability intersections, the deflator stitch, and the amendment rate, over **nine quarterly zips** (2013q2–q4, 2019q2–q4, 2025q2–q4, 838,993,284 bytes) | `[MEASURED IN BRIEF]` | scripts `data/C1_measure{,2,3,4}.py`, `data/C1_fetch_fsds.py`; results `data/C1_fsds_measurement.json`, `data/C1_fsds_intersections.json`, `data/C1_fsds_stitch.json`, `data/C1_fsds_amendments.json` |

**Interested parties, named.** `S5` and `S8` are Novy-Marx's own; `S8`'s second author is employed by
a manager selling the measure. `S9` is AQR's. `S6`'s second author is at AQR. **No asset-manager
publication is cited for any return in this brief.** `alphaarchitect.com` and an S&P Global
Market Intelligence "Quantamental Research" note titled *The (Gross Profitability) Trend is Your
Friend* surfaced on these searches and are **[SALES INSTRUMENT]**; neither is cited.

---

## 2. `Q1` — WHICH PAPERS MEASURE A QUARTERLY PROFITABILITY SORT. REPORTED SEPARATELY, NEVER POOLED

**Six distinct named sources. They do not share a sample, a universe, a weighting, a numerator, a
deflator or a lag. Each block below is self-contained and nothing in it may be carried across a
block boundary.**

### 2.1 `S1` — Novy-Marx (2013), Appendix A.4 and Table A6. **The only same-sample comparison in the family**

VW decile 10−1, NYSE breakpoints, financials excluded, **January 1972 → December 2010 for BOTH legs
of the comparison**, monthly rebalance for the quarterly strategy and June rebalance for the annual.
**Table A6 transcribed by me in full, from the published JFE article:**

| | `PMU_hf` (quarterly) | `PMU` (annual) |
|---|---|---|
| **mean excess return** | **`0.63` [`3.73`]** | **`0.33` [`2.06`]** |
| FF3 alpha | **`0.78` [`4.61`]** | `0.51` [`3.24`] |
| `MKT` / `SMB` / `HML` | −0.14 [−3.72] / −0.14 [−2.63] / −0.12 [−2.12] | −0.05 [−1.40] / −0.20 [−3.93] / −0.27 [−5.07] |
| **alpha vs the other strategy** | **`+0.42` [`3.10`]**, loading `0.64` [16.3] on `PMU` | **`−0.03` [`−0.23`]**, loading `0.57` [16.3] on `PMU_hf` |
| Adj. `R²` | 4.7% (FF3), 36.2% (spanning) | 6.7% (FF3), 36.2% (spanning) |

**Round 2 had only the prose (*"almost twice as profitable… almost eight percent per year"*). The
table says something the prose does not: the annual strategy is COMPLETELY SPANNED BY THE QUARTERLY
ONE — alpha `−0.03`, `t` `−0.23` — while the quarterly strategy has a `+0.42` [`3.10`] alpha against
the annual.** That is a stronger statement than "twice as profitable" and it is the single most
important number this lane recovered from the published literature.

**Ratio: `0.63 / 0.33` = `1.9×`, and it is the only ratio in this brief computed on one sample with
one weighting.**

### 2.2 `S2` — Hou, Xue & Zhang. **Three definitions, both frequencies, one deflator convention**

VW deciles, NYSE breakpoints, Table 4 header: *"January 1967 to December 2014, 576 Months"*. **BUT
`Gla_q`, `Ola_q` and `Cla_q` "start in January 1976" (Appendices A.4.11, A.4.17, A.4.20). THE ANNUAL
AND QUARTERLY COLUMNS BELOW ARE NOT THE SAME SAMPLE AND MUST NOT BE DIFFERENCED AS IF THEY WERE.**

| deflated by **lagged** assets/equity | annual (1967–2014) | `q1` | `q6` | `q12` (1976–2014) |
|---|---|---|---|---|
| **gross profits** `Gla` / `Gla_q` | **`0.16` [`1.04`]** | **`0.51` [`3.40`]** | `0.34` [`2.43`] | `0.29` [`2.12`] |
| **operating profits (R&D-adj)** `Ola` / `Ola_q` | **`0.20` [`1.07`]** | **`0.72` [`3.35`]** | `0.51` [`2.51`] | `0.47` [`2.46`] |
| **cash-based OP** `Cla` / `Cla_q` | **`0.53` [`3.02`]** | **`0.49` [`3.02`]** | `0.48` [`3.45`] | `0.47` [`3.57`] |
| FF-style OP-to-equity `Ole` / `Ole_q` | `0.07` [`0.37`] | `0.67` [`3.14`] | `0.45` [`2.22`] | `0.35` [`1.78`] |

| deflated by **current** assets (annual only; **HXZ ship no quarterly current-asset variant**) | |
|---|---|
| `Gpa` | `0.38` [`2.62`] |
| `Opa` | `0.37` [`1.87`] |
| `Cop` | `0.63` [`3.44`] |

**q-factor alphas from the same table, and they invert the ranking:** `Gla_q1` `0.20` [`1.41`],
`Gla_q6` `0.10` [`0.79`], `Gla_q12` `0.13` [`1.01`] — **all insignificant**. `Ola_q1` `0.37`
[`2.34`], `q6` `0.25` [`1.78`], `q12` `0.33` [`2.48`]. `Cla_q1` `0.43` [`2.69`], `q6` `0.40`
[`2.82`], `q12` `0.46` [`3.56`]. `Gpa` `0.18` [`1.24`]; `Cop` `0.69` [`4.77`]; `Cla` `0.74`
[`4.89`].

**The honest reading of that alpha column, and it cuts against the quarterly result.** The q-factor
model's third factor **is itself a quarterly profitability factor** (`Roe`, built from *"the months
immediately after the most recent public quarterly earnings announcement dates (item RDQ)"*). So
`Gla_q`'s insignificant q-alpha says *"this does not add to a model that already contains quarterly
ROE"* — which is close to circular, and I decline to read it as evidence against the raw premium.
**But it is equally not evidence for it, and a reader who takes `0.51` [`3.40`] without the
`0.20` [`1.41`] beside it has been misled.**

**`q1`/`q6`/`q12` are HOLDING PERIODS, not lags.** All three use the same information set
(fiscal quarter ending ≥4 months ago). Nothing in `S2` varies the lag.

### 2.3 `S3` — Chen & Zimmermann. **Equal-weighted quintiles, and every quarterly variant is a PLACEBO**

Table 4 caption, verbatim: *"This table lists **not-predictors and indirect signals**… **All
portfolios are equal-weighted and long-short quintiles**, unless the characteristic is discrete.
**Unlike clear and likely predictors, we do not sign these portfolios or select portfolio
implementations based on the original papers' results.** "HXZ variant" indicates our characteristic
is based on HXZ's modification of a (not necessarily predictive) characteristic in a previous
study."*

| | annual | quarterly | ratio |
|---|---|---|---|
| `GPlag` → `GPlag_q` | **`0.20` [`1.85`]** | **`0.88` [`6.17`]** | **`4.4×`** |
| `OperProfRDLagAT` → `OperProfRDLagAT_q` | **`0.05` [`0.33`]** | **`1.17` [`5.56`]** | `t` 0.33 → 5.56 |
| `CBOperProfLagAT` → `CBOperProfLagAT_q` | **`0.46` [`3.33`]** | **`0.86` [`6.19`]** | **`1.9×`** |

**All six rows are labelled `Indirect Evidence` and `HXZ variant`. All six carry NO original-paper
number in the "Original Study's Predictability Evidence" column.** `SignalDoc.csv` confirms it a
second way: `GPlag_q`, `OperProfRDLagAT_q` and `CBOperProfLagAT_q` are `Cat.Signal = Placebo` with
**`Return`, `T-Stat`, `Stock Weight`, `LS Quantile`, `Portfolio Period`, `Start Month` and `Filter`
all EMPTY**, against `GP`'s `0.31 / 2.49 / VW / 0.2 / 12 / 6`. **There is no published paper behind
any quarterly profitability number in the most-used public library.**

**And the weighting is the opposite of `S2`'s.** `S3` §2.4: *"the characteristics code and data omit
price and exchange filters, which are instead imposed in portfolio generation"* — so Table 4's
numbers carry **no price screen and no NYSE breakpoints, on equal weights**. `S2`'s entire thesis is
that this combination inflates anomalies (*"The key word is microcaps"*). **`0.88` [`6.17`] and
`0.51` [`3.40`] are not the same object and the gap between them is a weighting-and-breakpoint gap,
not new information.**

### 2.4 `S7` — Sotes-Paladino, Wang & Yao. **The year-over-year-change form**

Deciles, **NYSE breakpoints**, **stocks below `$25m` market cap excluded**, **1975–2014**.
Construction in §3.2. Their own summary of firm size, verbatim: *"the market capitalization of the
typical strong- and weak-profitability-growth firms in our sample is above the 20th NYSE percentile
below which a firm is commonly considered a microcap."*

| numerator | statistic | EW | VW |
|---|---|---|---|
| baseline `OP` = `REVTQ−COGSQ−XSGAQ−XINTQ` | **FF5 alpha** | `1.14` [`8.55`] | `0.68` [`3.89`] |
| Ball et al. `OP` = `REVTQ−COGSQ−XSGAQ+XRDQ` | FF5 alpha | `1.11` [`8.58`] | `0.67` [`3.92`] |
| **Novy-Marx gross profits = `REVTQ−COGSQ`** | **RAW average return** (Appendix Table A3) | **`0.91` [`7.55`]** | **`0.70` [`3.98`]** |

**A statistic mismatch inside one paper, recorded not resolved: the headline `1.14`/`0.68` are
FIVE-FACTOR ALPHAS ("earns five-factor alphas… of 1.14% and 0.68%"), while the gross-profit row's
`0.91`/`0.70` are described as raw outperformance and sit in a table captioned "Average Monthly
Returns". They are different objects and I have not compared them.**

**HARD-SCOPE FLAG ON THIS SOURCE, RAISED BY ME.** A *year-over-year change in quarterly profits* is
one step from earnings momentum, which is spent ground. `S2` reaches the same conclusion for the
ROE version, verbatim: *"Sorting on the four-quarter-change in return on equity (dRoe) yields a
high-minus-low average return of 0.76% per month (t = 5.43)… **We interpret the evidence as
indicating earnings seasonality.**"* **I report `S7`'s construction because sub-question 2 asks
whether the year-over-year form exists. I do not recommend it, and this lane did not pursue it.**

### 2.5 `S6` — Jensen, Kelly & Pedersen. **The trailing-four-quarter form, and it is the DEFAULT**

§6.3, verbatim: *"The value of an income or cash flow statement item is different. In the annual
data, it is calculated over one year. However, in the quarterly data, it is calculated over one
quarter. **To make quarterly income and cash flows items comparable to the corresponding annual
item, we take the sum of the item over the last four quarters.**"*

§6.2: *"We create characteristics for annual and quarterly accounting data separately. We then take
the most recent characteristics value from each dataset to create the final dataset."* And §2:
*"**We update characteristics with the most recent accounting data (which could be either annual or
quarterly) starting four months after the end of the fiscal period.**"*

**This changes what round 2's `P8` was.** `R2-02` §2.5 read JKP's replication rates for
"Profitability" off a bar chart's label ordering, treating it as an annual-frequency result.
**It is not.** JKP's `gp_at` is a **trailing-four-quarter numerator refreshed on whichever of the
annual or quarterly file is more recent, with a four-month lag**. `R2-02`'s ordering finding is
unaffected — it was about relative position — but **the object it describes is a quarterly-refresh
construction, and that should be recorded.**

JKP's deflator variants, verbatim from Table 5: `gp_at = GP*_t / AT*_t`; **`gp_atl1 = GP*_t /
AT*_{t−12}`** — *twelve* months lagged, not one quarter. Also `cop_at`, `cop_atl1 = COP*_t /
AT*_{t−12}`, `op_at`, `op_atl1`, `ope_bel1`. **JKP's "lagged" is a different lag from HXZ's
"lagged". Same word, different object.** And separately `niq_at = NI_QTR*_t / AT*_{t−3}` (single
quarter over one-quarter-lagged assets, cited to Balakrishnan, Bartov & Faurel 2010) and
`niq_at_chg1 = NIQ_AT_t − NIQ_AT_{t−12}` (the year-over-year change form).

### 2.6 `S3d` — Balakrishnan, Bartov & Faurel (2010, JAE), via `SignalDoc.csv`

`roaq`: *"Quarterly net income (ibq) divided by lagged total assets (atq)"*, **`Cat.Signal =
Predictor`**, EW deciles, `Return 0.842`%/month, **`T-Stat 6.45`**, sample **1976–2005**,
`Portfolio Period 1`, **`Filter abs(prc)>1`**. Chen & Zimmermann's own note on it, verbatim:
*"This is like a more timely version of the other profitability measures. Interestingly, they don't
cite Fama French 2006, nor Novy Marx 2013."*

**`[abstract-not-even: I did NOT open Balakrishnan, Bartov & Faurel (2010).]`** It is a
post-loss/profit-announcement-drift paper and therefore sits on this campaign's excluded ground. It
is named here **only** because it is the one *published, peer-reviewed* quarterly profitability sort
with a large `t` in the reference library, and because leaving it out would misrepresent §2's
coverage. **Its number is `[snippet-grade — a field in a reference implementation's metadata CSV,
not read from the paper]` and nothing in this brief rests on it.**

### 2.7 The one-line summary of `Q1`, with the pooling prohibition restated

**Six sources. Three numerator forms. Four deflator timings. Five lag rules. Two weighting schemes.
Samples starting in 1963, 1967, 1972, 1975 and 1976 and ending in 2005, 2010, 2014 and 2016.** The
"2–4× stronger" that round 2 flagged is **three within-source ratios — `1.9×` (`S1`, same sample),
`3.2×` (`S2`, different start dates), `4.4×` (`S3`, equal-weighted quintiles) — and it is not one
fact measured three times.**

---

## 3. `Q2` — THE EXACT CONSTRUCTION, QUOTED VERBATIM

### 3.1 `S1` — single quarter, CURRENT assets, RDQ-keyed

Appendix A.4, verbatim from the published JFE article (and **word-identical in the June 2012
draft**):

> *"Firms' revenues, costs of goods sold, and assets are available on a quarterly basis beginning in
> 1972 (Compustat data items REVTQ, COGSQ, and ATQ, respectively)… a 'high frequency' strategy,
> PMU_hf, rebalanced each month using the most recently released data (**formed on the basis of
> (REVTQ − COGSQ)/ATQ**, from Compustat quarterly data, **employed starting at the end of the month
> following a firm's report date of quarterly earnings, item RDQ**)."*

**`ATQ`, not `ATQ` lagged. The numerator is ONE fiscal quarter, not a trailing four.** Novy-Marx's
quarterly strategy therefore carries the *exact* contamination round 2 identified —
`GP/AT = (GP/AT₋₁) ÷ asset growth` — at quarterly frequency. §4 shows what happens when it is
removed.

And his stated reason for not using it, verbatim, which round 2 quoted and which still stands:

> *"Focusing on the strategy formed using annual profitability data ensures that results are truly
> driven by the level of profitability, and not surprises about profitability like those that drive
> post earnings announcement drift. The low frequency profitability strategy also incurs lower
> transaction costs, turning over only once every four years… **only a quarter as often as the high
> frequency profitability strategy.** Using the annual data has the additional advantage of
> extending the sample ten years."*

**Four reasons, and only one of them is about the signal.** The other three are cost, sample length
and scope hygiene. **The turnover ratio is the operationally important one and it is stated
precisely: the quarterly strategy turns over FOUR TIMES AS OFTEN as the annual one, which itself
turns over once every four years — i.e. roughly once a year.**

### 3.2 `S2` — single quarter, ONE-QUARTER-LAGGED assets, four-month calendar rule

A.4.11, verbatim:

> *"Gla_q is quarterly total revenue (Compustat quarterly item **REVTQ**) minus cost of goods sold
> (item **COGSQ**) divided by **one-quarter-lagged total assets (item ATQ)**. At the beginning of
> each month t, we sort stocks into deciles based on Gla_q for **the fiscal quarter ending at least
> four months ago**… For sufficient data coverage, the Gla_q portfolios start in January 1976."*

A.4.17 (`Ola_q`): *"quarterly total revenue (REVTQ) minus cost of goods sold (COGSQ), minus selling,
general, and administrative expenses (**XSGAQ**), plus research and development expenditures
(**XRDQ**, zero if missing), scaled by one-quarter-lagged book assets (ATQ)."*

A.4.20 (`Cla_q`) — **and here is a construction difference nobody has flagged**:

> *"…minus change in accounts receivable (item **RECTQ**), minus change in inventory (item
> **INVTQ**), plus change in deferred revenue (item **DRCQ** plus item **DRLTQ**), and plus change
> in trade accounts payable (item **APQ**), all scaled by one-quarter-lagged book assets (item ATQ).
> **All changes are quarterly changes in balance sheet items** and we set missing changes to zero."*

**Compare the annual `Cla` in A.4.19, which has SIX accrual terms. The quarterly `Cla_q` has FOUR:
Δ(prepaid expenses, `XPP`) and Δ(accrued expenses, `XACC`) are GONE.** Compustat quarterly carries
no `XPPQ`, and `XACCQ` is present but unused. **So `Cla_q` is not `Cla` at a higher frequency; it is
a different signal with two of its six accrual corrections deleted.** This is the second time this
campaign has found a missing accrual term in a `CbOP` tag list — round 2 found `XPP` missing from
round 1's — and here it is missing **from the published construction itself.**

**And the changes are ONE-QUARTER changes, not year-over-year.** A one-quarter change in inventory
or receivables is a seasonal quantity. §8.1.

### 3.3 `S3c` — the code, and it matches `S2` not `S1`

`Placebos/GPlag_q.do`, the whole signal-construction body, verbatim:

```stata
xtset permno time_avail_m
gen GPlag_q =   (revtq - cogsq)/l3.atq
label var GPlag_q "Gross profitability (quarterly)"
```

`l3.atq` is `atq` three months back on the monthly `time_avail_m` grid, which — because each fiscal
quarter is expanded to exactly three monthly rows — **is the previous fiscal quarter's assets.** So
`GPlag_q` = HXZ's `Gla_q`. `SignalDoc.csv` says so in words: *"Revenue (revtq) - cost of goods solds
(cogsq), divided by one quarter lagged total assets (atq)"*, `Notes: HXZ variant`.

### 3.4 The three numerator forms, side by side, as sub-question 2 asks

| form | who | exact numerator |
|---|---|---|
| **single quarter** | `S1`, `S2`, `S3`, `S6`'s `niq_at` | `REVTQ − COGSQ` for the most recent fiscal quarter |
| **trailing four quarters** | **`S6` (JKP), and it is their DEFAULT** | *"the sum of the item over the last four quarters"* |
| **year-over-year change** | `S7`, `S6`'s `niq_at_chg1`, `S2`'s `dRoe` | `OP_q − OP_{q−4}`, over `BE_{q−4}` (`S7`) |

**All three exist in the literature. Only one of them — the trailing four-quarter sum — is
seasonality-free by construction, and it is the one the profitability papers do not use.** §8.1.

---

## 4. `Q3` — DOES THE QUARTERLY ADVANTAGE SURVIVE THE DEFLATOR CONVENTION? **YES, AND IT IS THE HEADLINE**

### 4.1 The test round 2 asked for exists and it is `S2`'s Table 4

Round 2's central finding was that `GP/AT` is partly an investment signal, because
`GP/AT = (GP/AT₋₁) ÷ (AT/AT₋₁)`, and that gross profitability's `t` falls to 1.04–1.85 once the
deflator is lagged. Sub-question 3 asked whether a quarterly result measured with a **current**-asset
deflator inherits that contamination.

**It would — `S1`'s `(REVTQ−COGSQ)/ATQ` is a current-asset deflator. But `S2` and `S3` both measure
the quarterly variant with the LAGGED deflator on BOTH sides, so the test is already run.**

| deflated by lagged assets, `S2`, VW deciles, NYSE breaks | annual | quarterly `q1` | what the deflator did |
|---|---|---|---|
| gross profits | `0.16` [`1.04`] | **`0.51` [`3.40`]** | **killed it annually; did not kill it quarterly** |
| operating profits (R&D-adj) | `0.20` [`1.07`] | **`0.72` [`3.35`]** | **killed it annually; did not kill it quarterly** |
| cash-based OP | `0.53` [`3.02`] | `0.49` [`3.02`] | **no effect either way** |

**Restating that as plainly as I can: the deflator argument is an argument about ANNUAL data.** At
annual frequency, `AT/AT₋₁` is a full year of asset growth, and dividing by it imports a whole,
separately-documented anomaly. At quarterly frequency the same ratio is *one quarter* of asset
growth — a much smaller and noisier quantity — so removing it costs far less. **`[THIS
MECHANISM IS MY INFERENCE FROM THE IDENTITY, NOT A MEASUREMENT AND NOT A CLAIM ANY SOURCE MAKES. DO
NOT CARRY IT AS ONE.]`** What *is* measured is the table above.

### 4.2 The uncomfortable half: `CbOP` gains nothing

`S2` measures **no** improvement for cash-based operating profitability at the 1-month horizon
(`0.53 → 0.49`), and its `q6`/`q12` are `0.48`/`0.47`. **Round 2's recommended definition is the one
member of the family for which frequency does not matter.** Its advantage over gross and operating
profitability is an advantage that exists *only at annual frequency* — and §7 shows it is also the
one that XBRL cannot compute at quarterly frequency at all.

### 4.3 The conflict, recorded and not adjudicated

`S3`'s equal-weighted quintiles say the opposite about `CbOP`: `0.46` [`3.33`] → `0.86` [`6.19`],
a `1.9×` gain. **`S2` says `CbOP` gains nothing from quarterly data; `S3` says it nearly doubles.**

**What differs, so nobody reads this as an era effect:** (i) **weighting** — VW vs EW; (ii)
**breakpoints** — NYSE vs all-stock; (iii) **quantile** — deciles vs quintiles; (iv) **sample** —
1976–2014 vs Novy-Marx's/Ball's original windows; (v) **construction** — `Cla_q`'s four accrual
terms vs `CBOperProfLagAT_q`'s attempt at all of them.

**WHICH I WOULD WEIGHT, AND WHY.** For a book that is **equal-weighted** but **floored at `$5` with
a dollar-volume screen**, *neither* is the right object. `S2` is value-weighted with NYSE
breakpoints — a large-cap statement. `S3` is equal-weighted with no screens at all — a microcap
statement. **The programme's universe sits between them and neither source measures it.** If forced
to one: **`S2`, because its adversarial posture makes a positive result there harder to obtain, and
because `S3`'s own caption says these portfolios were not signed or specified from any paper.** I
record `S3` as unresolved, not wrong.

### 4.4 The prose-versus-table tension in `S2`, recorded and NOT resolved

`S2` §3.2.4, verbatim, on gross profitability:

> *"The high-minus-low gross profits-to-lagged assets (Gla) decile earns an average return of only
> 0.16% per month (t = 1.04)… because Gpa equals Gla divided by asset growth (current assets-to-
> lagged assets), the Gpa effect is confounded with the investment effect. **Purging the investment
> effect yields an economically small and statistically insignificant Gla effect.**"*

**Their own Table 4 reports `Gla_q1` at `0.51` [`3.40`] — the same signal, the same deflator, at
quarterly frequency, significant. `Gla_q` is discussed NOWHERE in the paper's text.** I searched the
whole extracted text: `Glaq` appears only in the variable list (Table 1), the results tables
(Tables 3–4) and Appendix A.4.11. **The paper's narrative conclusion about gross profitability is
stated without reference to the row in its own table that does not support it.** Per the campaign
rule, **I record the tension and do not resolve it.**

### 4.5 A pointed negative: the 2025 retrospective does not revisit this at all

`S8` — Novy-Marx & Medhat, *Profitability Retrospective: What Have We Learned?*, 78 pp, March 2025,
by the author of the 2013 appendix. **`[MEASURED IN BRIEF]` on its extracted text: `high frequency`
0 hits, `REVTQ` 0, `RDQ` 0, `season` 0.** Its stated timing convention, verbatim: *"**All accounting
variables are as of latest fiscal-year end**"*, *"Portfolios are rebalanced annually at the end of
June."*

**The retrospective that asks what we have learned about profitability does not mention the
quarterly strategy its lead author reported as twice as profitable and unspanned by the annual
one.** That is not evidence the quarterly result is wrong. **It is evidence that nobody has
re-examined it in twelve years**, which bears directly on how much weight a single 1972–2010 table
can carry.

---

## 5. `Q4` — THE LAG CONVENTION FOR QUARTERLY ACCOUNTING DATA, VERBATIM, AND WHETHER ANYONE JUSTIFIES IT

### 5.1 Five conventions, quoted

| # | source | rule, verbatim | effective lag from fiscal quarter end |
|---|---|---|---|
| 1 | **`S1` Novy-Marx (2013)** | *"employed starting at the end of the month following a firm's report date of quarterly earnings, item RDQ"* | RDQ month **+ 1**; ≈ **60–90 days** |
| 2 | **`S5` Novy-Marx & Velikov (2023) toolkit code** | `comp_fundq_linked.dates = 100 * year(rdq) + month(rdq);` | **the RDQ month itself**; ≈ **35–50 days** |
| 3 | **`S3` Chen & Zimmermann** | *"we use the standard six-month lag for annual accounting data availability and **a one-quarter lag for quarterly accounting data availability**… In a couple cases, we use the earnings reporting date (RDQ)… **we deviate from a few accounting studies, which use a shorter data lag**"* | `max(quarter end + 3 months, RDQ month)`; **≈ 92 days** |
| 4 | **`S2` Hou, Xue & Zhang** | *"we sort stocks into deciles based on Gla_q for **the fiscal quarter ending at least four months ago**"* | **≈ 122 days** |
| 5 | **`S6` Jensen, Kelly & Pedersen** | *"We assume that accounting variables are publically available **4 months after the end of the accounting period**"* | **≈ 122 days** |
| — | `S7` Sotes-Paladino et al. | *"the months immediately after the most recent public quarterly earnings announcement dates (item RDQ)"*, **with a three-month staleness cap** | RDQ month; ≈ 35–50 days |

**The spread between the tightest (2) and the loosest (4/5) is about two and a half months. The same
author sits at both ends of the RDQ family twelve years apart.**

### 5.2 Convention 3, in the code that implements it — and it is NOT what the paper says

`S3`'s paper says "a one-quarter lag". `S3c`'s code says something more specific, and the Python and
Stata ports agree:

```stata
// Data availability assumed as discussed in .../issues/50
gen time_avail_m = mofd(datadate) + 3            // Assume data available with a 3 month lag
replace time_avail_m = mofd(rdq) if !mi(rdq) & mofd(rdq) > time_avail_m   // Patch cases with earlier data availability
drop if mofd(rdq) - mofd(datadate) > 6 & !mi(rdq)                          // Drop cases with very late release
...
expand 3    // each fiscal quarter becomes three monthly rows
```

**Three rules the paper does not state: the RDQ override fires only when RDQ is LATER; observations
whose RDQ trails the quarter end by more than six months are DROPPED ENTIRELY; and each quarter's
data is carried for exactly three months.** Note the comment on the second line — *"Patch cases with
**earlier** data availability"* — **describes the opposite of what the line does.** The line pushes
`time_avail_m` **later**. A reader trusting the comment would have the sign backwards.

`S3` footnote 13, verbatim: *"For users of the code: **the accounting data lag is imposed in the
data download step, and is not visible in the files that generate characteristics.**"*

### 5.3 `S3i` — the answer to "justified, or inherited in silence?" is: **argued about in public, then deliberately left half-fixed**

GitHub issue **#50**, `OpenSourceAP/CrossSection`, opened by `mk0417` on 2021-09-04, closed by
`tomz23` on 2022-02-14 after 12 comments. **Read in full. Quoted verbatim.**

**The opening measurement:**
> *"`gen time_avail_m = mofd(datadate) + 3` … This may have two minor issues… 1. RDQ < datadate:
> more than 600 obs[e]rvations. 2. **RDQ > datadate+90 (day): more than 50,000 observations (that
> are not public available with 90-day lag).**"*

**The maintainer's reply, and the sentence that matters most to this lane:**
> *"This is a good catch… Fortunately this only affects about 10 predictors. **Some of these from
> what I recall have the largest t-stats though, so I think we should fix this.**"*

**A RETRACTED STATISTIC, reported here as retracted and NOT as a figure.** `chenandrewy` first wrote
*"I find 80% of obs with eps data have lag_ok overall, and that the share increases over time from
60% in 1990 to 95% in 2021. That doesn't seem great to me. Seems like using RDQ is just better."*
He then withdrew it: *"**Oh, shoot, I slipped on Stata's missing values handling!** … So it's really
just 5% of observations that are affected."* **The 60%→95% time trend is withdrawn and must not be
quoted.**

**The corrected measurement, from `mk0417`'s tabulation** (`epspxq` non-missing, `lag_ok` =
3-month rule is not earlier than the RDQ month):
- all observations: `lag_ok = 1` for **1,022,362 of 1,371,798 = 74.53%**
- **restricted to observations with a non-missing `rdq`: `lag_ok = 1` for 1,022,362 of 1,067,699 = 95.75%; the 3-month rule is a look-ahead for 45,337 firm-quarters = 4.25%.**
- late releases: *"around 1% are more than 180 days (6 months)"*, and the final filter drops
  *"**Just 0.59 percent of cases**."*

**The reason the fix was minimal, verbatim, and this is the whole answer to sub-question 4:**
> *"To be clear, I actually favor a minimal modification. That is, I don't want to replace
> `gen time_avail_m = mofd(rdq) if rdq != . & rdq > datadate` since could be a pretty significant
> change to 10 signals. **I don't want to mess people up too much who are already using the data.**"*

**A field that will not switch its quarterly timing rule to the correct one because doing so would
disturb existing users is not a field that has justified the rule. It is a field that has
grandfathered it — and, uniquely, has written down that it did so.**

Two further things the thread establishes:
- **The maintainer records a conflict with a published paper and does not resolve it:** *"Here is a
  bit more info to frame this, from the Thomas and Zhang ChTax predictor: [screenshot]. **Our
  findings about the timing of RDQ vs datadate seem to be at odds with this text.** Hopefully we can
  resolve all of this together in the next release."* **It was not resolved in the thread.**
- The embedded screenshot of `S2`'s published text, **read by me as an image**, carries HXZ's own
  justification and it is a **staleness** argument, not a look-ahead argument:
  > *"…we require the end of the fiscal quarter that corresponds to its most recent Sue to be within
  > six months prior to the portfolio formation. **We do so to exclude stale information on
  > earnings.** To avoid potentially erroneous records, **we also require the earnings announcement
  > date to be after the corresponding fiscal quarter end.**"*

**A second screenshot, also read as an image**, is a code-search listing of the *predictors* that
depend on the quarterly file as of 2021: `Cash`, `ChTax`, `EarningsSurprise`, `EarnSupBig`,
`ExclExp`, `MS`, `NumEarnIncrease`, `OScore_q`, `RevenueSurprise`, `roaq`, `ZScore_q`,
`ZZ2_AnnouncementReturn`. **None of the quarterly profitability variants appears, because they live
under `Placebos/`, not `Predictors/`.** The timing debate was conducted without them in view.

### 5.4 `S2`'s four-month rule is a **coverage** workaround that became a **timing** convention

`S2` §2, verbatim, on why four months:

> *"Hou, Xue, and Zhang (2015) start the q-factors sample in January 1972, restricted by the limited
> coverage of earnings announcement dates and book equity in Compustat quarterly files. We extend
> the sample backward to January 1967. **To overcome the lack of coverage for quarterly earnings
> announcement dates, we use the most recent quarterly earnings from the fiscal quarter ending at
> least four months prior to the portfolio formation month.**"*

**That is a justification for using a calendar rule INSTEAD OF `RDQ` where `RDQ` does not exist —
i.e. pre-1972.** But the *profitability* appendices (A.4.11, A.4.17, A.4.20) apply the four-month
calendar rule **throughout**, with no `RDQ` clause at all, on portfolios that start in 1976 when
`RDQ` is available. **The workaround's scope silently expanded from "before 1972" to "always".**

**And `S2` states elsewhere that one month of lag matters, in a different context, verbatim:**
> *"These estimates are lower than the average 3-month buy-and-hold return of 3.9% reported by
> Thomas and Zhang (2011)… Also, **the time lag between the fiscal quarter end and subsequent
> returns is only three months, not four months in our construction.**"*

**That is the only sentence I found anywhere in this literature that attributes a difference in
result to a one-month difference in lag — and it is offered alongside two other differences
(breakpoints and weighting), so it is not a clean attribution.**

### 5.5 `S5` — Novy-Marx & Velikov's own protocol code, and its rule is the most aggressive of the five

`getCOMPUSTATAdditionalData.m`, the two `dates` assignments side by side, verbatim:

```matlab
% Create the dates variable - align a given fiscal year end with next year's June
comp_funda_linked.dates = 100*(1+year(comp_funda_linked.datadate)) + 6;
...
% Create the dates variable - we'll match based on RDQ
comp_fundq_linked.dates = 100 * year(comp_fundq_linked.rdq) + month(comp_fundq_linked.rdq);
```

And the quarterly query itself is keyed on the announcement date, not the fiscal date:
`COMPUSTATQuery = 'select gvkey, RDQ';` for `fundq` against `'select gvkey, datadate'` for `funda`.

**Three consequences the code makes explicit and no prose does.** (i) **Firm-quarters with a missing
`RDQ` are dropped outright** — `idxToDrop = isnat(comp_fundq.rdq) | rdq > lastYear | rdq <
firstYear`. (ii) Where one `RDQ` month carries several fiscal quarters — *"These could be due to
restatements, or delays in announcements"* — the toolkit keeps **the latest fiscal quarter**.
(iii) `makeCOMPUSTATVariables.m` **forward-fills quarterly variables between announcements**, and
past the last one: `for r = firstR+1 : min(nMonths, lastR + 2)`. **A firm that skips a quarter
carries its stale value forward for as long as the gap lasts, and every series is extended two
months beyond its final observation.**

### 5.6 The negative: `S9` (QMJ) is not a quarterly source

Asness, Frazzini & Pedersen's 9 October 2013 draft, §2 verbatim: *"**We follow the standard
convention and align accounting variables at the end of the firm's fiscal year ending anywhere in
calendar year t−1 to June of calendar year t.**"* The only quarterly data in the paper is
`EVOL` — *"the standard deviation of quarterly ROE over the past 60 quarters"* — a volatility input,
not a profitability level. **Two independent mirrors both returned the same October 2013 draft; the
published RAST 2019 version was not obtained, so I cannot say whether it moved to quarterly
updating.** §11.

---

## 6. `Q5` — THE SMALLEST DEFENSIBLE LAG. **`[MEASURED IN BRIEF]`**

**Endpoint:** `https://www.sec.gov/files/dera/data/financial-statement-data-sets/<yyyy>q<n>.zip`,
files `sub.txt` and `num.txt`. Nine zips (2013q2–q4, 2019q2–q4, 2025q2–q4), 839 MB, paced 0.5 s
between requests, contact string in the User-Agent, **every download's first two bytes checked for
`PK` and its SHA-1 recorded** (`data/C1_fetch_fsds.py`). Restricted to `form = 10-Q` whose `period`
is the target fiscal quarter end (`20130630`, `20190630`, `20250630`), so each era's population is
one fiscal quarter's filers observed across the two calendar quarters after it. **Right-censored at
~184 days by the zip boundary, and I say so rather than reporting a `max` as if it were one.**

### 6.1 First, the literature's answer to "how much is lost by waiting": there isn't one at this granularity

**`S4`, obtained for the first time in this campaign, is the only source that varies the lag at
all.** Figure 1 plots Fama-MacBeth slopes on operating profitability *"lag[ged]… up to ten years,
increasing in **increments of six months**"*, All-but-microcaps, July 1973–December 2012, Panel A
lagging every regressor and Panel B lagging only profitability. The authors' own characterisation,
verbatim:

> *"Panel A indicates that the ability of operating profitability to predict future returns decays
> over time but is **reliably positive for at least four years** and persists perhaps as long as ten
> years."* … *"the average slope on profitability decays more slowly over time in Panel B than in
> Panel A. **It is reliably positive for most of the ten-year prediction period.**"*

**`[read in full] for the text. FIGURE 1'S VALUES ARE IN A PLOT AND I READ NONE OF THEM — the only
numbers `pypdf` recovers from those two pages are axis tick labels, and reading a series off tick
labels is exactly the fabrication this campaign has caught eleven times.]`**

**So: the finest lag increment anyone reports is SIX MONTHS, on a Fama-MacBeth slope rather than a
portfolio return. The three-versus-four month question, and the one-month question this programme
actually faces, are unmeasured in the literature I obtained.** That is the honest answer to the
second half of sub-question 5.

### 6.2 The filing-lag distribution, in days from fiscal quarter end to EDGAR acceptance

| | 2013 (n = 5,722) | 2019 (n = 4,841) | 2025 (n = 4,820) |
|---|---|---|---|
| min | 9 | 3 | 10 |
| p05 | 26 | 25 | 28 |
| p25 | 36 | 33 | 36 |
| **p50** | **39** | **39** | **38** |
| p75 | 45 | 44 | 44 |
| **p90** | **45** | **45** | **45** |
| **p95** | **50** | **50** | **50** |
| **p99** | **81** | **96** | **106** |
| max (censored) | 183 | 180 | 184 |

**The centre of this distribution has not moved in twelve years and sits exactly on the regulatory
deadlines — p90 = 45 days is the non-accelerated filer's 10-Q deadline. But the p99 has moved from
81 to 106 days. The tail is lengthening while the body is stationary.**

For contrast, the same measurement on **10-K** submissions in the same zips (any period, so the
population is the annual-report stragglers rather than a clean cohort): p50 **85 / 77 / 74** days,
p90 **107 / 207 / 192**, p99 **456 / 878 / 711**. **A six-month annual lag clears the 10-K p90 in
2013 and does not clear it in 2019 or 2025.**

### 6.3 The coverage curve — what each convention actually buys

Share of the fiscal quarter's eventual 10-Q filers who have filed by day `L`:

| `L` days | 2013 | 2019 | 2025 | which convention lands here |
|---|---|---|---|---|
| **< 0** | **0.00%** | **0.00%** | **0.00%** | **negative control — no filing can precede its own period end, and none does** |
| 20 | 0.86% | 0.93% | 0.48% | |
| 30 | 9.58% | 10.87% | 11.18% | |
| 40 | 60.47% | 70.81% | 61.18% | |
| **45** | **90.34%** | **92.73%** | **93.44%** | ≈ `S5`'s RDQ-month rule |
| 50 | 97.22% | 96.94% | 96.89% | |
| **60** | **98.15%** | **97.71%** | **97.66%** | ≈ `S1`'s RDQ + 1 month, early case |
| 75 | 98.74% | 98.41% | 98.22% | |
| **90** | **99.18%** | **98.86%** | **98.73%** | ≈ **`S3`'s 3-month rule** |
| 105 | 99.39% | 99.13% | 98.98% | |
| **120** | **99.62%** | **99.30%** | **99.23%** | ≈ **`S2`'s and `S6`'s 4-month rule** |
| 150 | 99.88% | 99.73% | 99.65% | |
| 184 (censored) | 100% | 100% | 100% | **upper negative control — by construction everything observed is ≤ 184** |

**READ THE 90 AND 120 ROWS AGAINST EACH OTHER. HOU–XUE–ZHANG'S EXTRA MONTH BUYS 0.44 / 0.44 / 0.50
PERCENTAGE POINTS OF THE CROSS-SECTION.** It costs a month of staleness on the other 99%. **The
four-month convention is not paying for coverage; there is almost no coverage left to buy above
three months.**

**And a 60-day lag already reaches 97.7%.** Coverage is not what makes a longer lag defensible. The
next section is what does.

### 6.4 The acceptance clock — and this is the constraint that actually binds

The programme trades at daily closes and must decide before the close it trades. Acceptance-hour
distribution (ET) for the same 10-Q cohorts, **cumulative**:

| accepted by end of hour… | 2013 | 2019 | 2025 |
|---|---|---|---|
| 09 (pre-open + first half hour) | 11.67% | 12.87% | 15.21% |
| 14 | 43.99% | 34.27% | 30.75% |
| **15 (i.e. BEFORE 16:00 ET)** | **52.36%** | **41.29%** | **35.19%** |
| 16 | 74.73% | 79.80% | **83.11%** |
| 17 | 91.51% | 94.09% | 95.62% |

| | 2013 | 2019 | 2025 |
|---|---|---|---|
| **accepted at or after 16:00 ET** | **47.64%** | **58.71%** | **64.81%** |
| **…AND carrying that same day's `filed` date** | **39.29%** | **50.82%** | **58.51%** |
| **filings landing in the 16:00 hour ALONE** | 22.4% | 38.5% | **47.9%** |

**Nearly half of all 2025 10-Qs are accepted inside a single one-hour window that starts at the
closing bell.** Filers submit immediately after the close, deliberately, and the practice has
intensified: the share accepted before 16:00 ET has fallen from 52.4% to 35.2% in twelve years.

**Three consequences for a book that must decide before a close.**

1. **A `filed`-date rule is a same-session look-ahead for 58.5% of 2025 10-Qs.** This is round 1's
   `A1` finding — 57.5% for pooled 10-K/10-Q submissions in 2026q2 — **reproduced independently on a
   different population (10-Q only, one fiscal cohort, three eras) and it comes out slightly
   higher.** `A1`'s 2012q2 figure was 39.3%; my 2013 cohort gives **39.29%**. Two different
   measurements landing on the same number is a coincidence worth naming as one, not a confirmation.
2. **The smallest defensible rule is not a number of months. It is: derive knowability from FSDS
   `accepted` in ET, and if acceptance is after roughly 15:45 ET the earliest tradeable close is the
   NEXT session.** Under that rule only ~35% of 10-Qs are usable at the close of their own filing
   day. **The other ~65% cost one extra bar, not one extra month.**
3. **`companyfacts` cannot express this.** It exposes `filed` (a date) and not the acceptance time.
   Round 1's fallback — *"where only `companyfacts` is available, use `filed + 1 business day`"* —
   is confirmed by this measurement as the right default, and it is **conservative for the ~35% and
   exactly correct for the ~65%.**

### 6.5 The structural point nobody has stated: **an XBRL book cannot use `RDQ` at all**

**Three of the five conventions key on the earnings announcement date. `RDQ` is a Compustat field
populated from the 8-K earnings release, which precedes the 10-Q.** A book built on EDGAR XBRL has
no equivalent: **`[MEASURED IN BRIEF]` form composition of the FSDS zips shows `8-K` at 103
submissions of 15,884 in the 2013 pair and absent from the top eight forms in the 2019 and 2025
pairs**, against 10,527–12,974 `10-Q`s. **Earnings releases are not XBRL financial-statement
filings.**

**So a filing-driven book is structurally LATER than `S1`, `S5` and `S7`, and it cannot replicate
them.** Its earliest possible information date is the 10-Q acceptance — p50 day 38–39 — where their
`RDQ` typically falls days to weeks earlier. **The two conventions a filing-driven book CAN
reproduce exactly are `S3`'s (3-month floor) and `S2`/`S6`'s (4-month rule), because both are
calendar rules on the fiscal period end.** That is a genuine constraint on which published result
this programme could ever be compared against, and no source states it.

---

## 7. `Q6` — TAG COMPUTABILITY **AT QUARTERLY FREQUENCY**. **`[MEASURED IN BRIEF]`**

### 7.1 Why not `frames`, and how the flagged hazard is addressed

Round 2's census used `https://data.sec.gov/api/xbrl/frames/...`. The slate flags — correctly —
that **`frames` returns LAST-FILED values with no `filed` and no `form`**, so a tag census on it
counts filers by their **latest vintage**, and an ASC 606 retrospective restatement could move a
filer from an old tag to a new one *for a pre-2018 period*, making a tag break look sharper and
later than it was point-in-time.

**This census does not use `frames`.** It uses the **Financial Statement Data Sets**, whose own
documentation says *"All numeric data is 'as filed'"* and *"uncorrected and 'as filed' EDGAR
document submissions"*, and where **each quarterly zip contains only the submissions accepted in
that quarter**. A tag counted here was tagged that way **in the document that was filed**, by a
filer identified through `sub.txt`'s `cik`. **The restatement hazard cannot operate on this
measurement.** Restrictions applied: `form = 10-Q`, `period` = the target quarter end,
`segments = ''` and `coreg = ''` (consolidated totals only — round 2's `B4` showed dimensioned
tagging otherwise inflates counts), `uom = USD`, and `ddate` = the current period.

### 7.2 The census, by the `qtrs` duration field — which is the question a quarterly build actually asks

Distinct CIKs. `qtrs = 0` is an instant (balance sheet); `qtrs = 1` is a single three-month period;
`qtrs = 2` is the six-month year-to-date figure that a calendar-Q2 10-Q also carries.

| tag | `qtrs` | 2013 | 2019 | 2025 |
|---|---|---|---|---|
| 10-Q submissions in the cohort | — | **5,675** | **4,789** | **4,765** |
| `Assets` | 0 | 5,571 | 4,746 | 4,727 |
| **`GrossProfit`** | **1** | **1,913** | **1,605** | **1,554** |
| `GrossProfit` | 2 | 1,632 | 1,361 | 1,362 |
| `Revenues` | 1 | 2,319 | 1,936 | 1,462 |
| `RevenueFromContractWithCustomerExcludingAssessedTax` | 1 | **0** | 1,634 | 1,905 |
| `RevenueFromContractWithCustomerIncludingAssessedTax` | 1 | **0** | 548 | 335 |
| **`SalesRevenueNet`** | 1 | 1,448 | **0** | **0** |
| `SalesRevenueGoodsNet` | 1 | 780 | **0** | **0** |
| **`CostOfGoodsSold`** | 1 | 1,121 | **0** | **0** |
| `CostOfGoodsAndServicesSold` | 1 | 644 | 1,455 | 1,176 |
| `CostOfRevenue` | 1 | 796 | 819 | 855 |
| `SellingGeneralAndAdministrativeExpense` | 1 | 1,692 | 1,481 | 1,419 |
| `GeneralAndAdministrativeExpense` (**not a substitute**) | 1 | 2,548 | 2,234 | 2,268 |
| `ResearchAndDevelopmentExpense` | 1 | 1,292 | 1,375 | 1,513 |
| `OperatingIncomeLoss` | 1 | 3,860 | 3,553 | 3,537 |
| `AccountsReceivableNetCurrent` | 0 | 2,653 | 2,355 | 2,193 |
| `InventoryNet` | 0 | 2,152 | 1,881 | 1,757 |
| **`PrepaidExpenseCurrent`** | 0 | 873 | 749 | **735** |
| **`DeferredRevenueCurrent`** | 0 | **1,067** | **336** | **255** |
| `DeferredRevenueNoncurrent` | 0 | 471 | 146 | 115 |
| `ContractWithCustomerLiabilityCurrent` | 0 | **0** | 821 | 1,004 |
| `ContractWithCustomerLiabilityNoncurrent` | 0 | **0** | 343 | 365 |
| `AccountsPayableCurrent` | 0 | 2,969 | 2,581 | 2,527 |
| **`AccruedLiabilitiesCurrent`** | 0 | 1,966 | 1,689 | **1,661** |
| `IncreaseDecreaseInAccountsReceivable` | **1** | **208** | **143** | **118** |
| `IncreaseDecreaseInAccountsReceivable` | 2 | 2,274 | 2,012 | 1,998 |
| `IncreaseDecreaseInInventories` | **1** | **174** | **117** | **92** |
| `IncreaseDecreaseInAccountsPayableAndAccruedLiabilities` | **1** | **130** | **96** | **68** |
| **control** `ZZZZNotATagC1Control` | any | **0** | **0** | **0** |
| **control** `GrossProfitZZZZ` (near-miss of a real tag) | any | **0** | **0** | **0** |
| **control** `AssetsZZZZ` | any | **0** | **0** | **0** |
| **control** `Assets` at `ddate = 20991231` | 0 | **0** | **0** | **0** |

**SIX NEGATIVE CONTROLS, IN BOTH DIRECTIONS, ALL BEHAVING.** Three invented tags return zero
everywhere; a future `ddate` returns zero; **three tags that MUST die at ASC 606 do die
(`SalesRevenueNet` 1,448 → 0 → 0, `CostOfGoodsSold` 1,121 → 0 → 0, `SalesRevenueGoodsNet` 780 → 0 →
0); and two tags that MUST NOT EXIST before ASC 606 do not (`ContractWithCustomerLiability*` and
`RevenueFromContractWithCustomer*` are 0 in 2013).** A census that only ever counts upward proves
nothing; this one is pinned at both ends.

### 7.3 The four findings that matter

**1. `GrossProfit` survives at quarterly frequency, and the single-quarter form is the DOMINANT
one.** `GrossProfit` at `qtrs = 1` runs **1,913 → 1,605 → 1,554** with no FY2018 break, confirming
round 2's annual `frames` result on an as-filed basis and a different endpoint. **And crucially
`qtrs = 1` exceeds `qtrs = 2` in every era** — the single three-month figure that `S1` and `S2`
require is *directly tagged*, not something that must be differenced out of a year-to-date series.
**The number of filers who tag the six-month figure but not the three-month one is 35 / 6 / 6.**
That was not obvious and it is good news for the `S1`/`S2` numerator.

**2. The cash-flow statement is year-to-date and effectively never single-quarter.**
`IncreaseDecreaseInAccountsReceivable` at `qtrs = 1`: **208 / 143 / 118**, against **2,274 / 2,012 /
1,998** at `qtrs = 2`. Same shape for inventories and payables. **`P2`'s cash-flow-statement route to
`CbOP` is not available at quarterly frequency without differencing consecutive year-to-date
figures** — which is exactly the `oancfy → oancfyq` conversion `S3c` performs for cash flow, and
which nobody performs for these accrual terms. **`S2`'s decision to build `Cla_q` from balance-sheet
changes only, and to drop `XPP` and `XACC`, now looks less like a choice and more like the only
thing the quarterly data permits.**

**3. Deferred revenue dies at quarterly frequency exactly as round 2 found it dying annually**, and
its replacement does not fully cover it: `DeferredRevenueCurrent` **1,067 → 336 → 255**;
`ContractWithCustomerLiabilityCurrent` **0 → 821 → 1,004**. Round 2's warning stands unchanged and
applies with more force to `Cla_q`, whose deferred-revenue term is a **one-quarter** difference
straddling the tag change.

**4. `SellingGeneralAndAdministrativeExpense` is the binding tag for everything above gross
profitability**, at 1,692 → 1,481 → **1,419** against 4,727 for `Assets`.
`GeneralAndAdministrativeExpense` is more widely tagged (2,268) but **excludes selling expense and
is a different line**; substituting it changes the numerator. This reproduces round 2's annual
finding at quarterly frequency.

### 7.4 The intersections — who can actually compute each definition, per quarter

| | 2013 | 2019 | 2025 |
|---|---|---|---|
| `Assets`, current quarter end (the ceiling) | 5,571 | 4,746 | 4,727 |
| `GrossProfit` direct route, `qtrs=1` | 1,913 | 1,605 | 1,554 |
| component route (`revenue family` ∩ `cost family`), `qtrs=1` | 2,287 | 2,210 | 1,996 |
| **component route adds over the direct tag** | **+592** | **+696** | **+529** |
| **either route ∩ current `Assets` = GROSS PROFITABILITY, `S1` deflator** | **2,490** | **2,296** | **2,082** |
| **…with ONE-QUARTER-LAGGED `Assets` from the SAME filing (`S2`/`S3` deflator)** | **172** | **127** | **105** |
| **…with one-quarter-lagged `Assets` after stitching the PRIOR 10-Q** | **2,161** | **2,083** | **1,916** |
| **stitch rate** | **86.27%** | **90.53%** | **91.98%** |
| `SellingGeneralAndAdministrativeExpense`, `qtrs=1` | 1,692 | 1,481 | 1,419 |
| **OPERATING PROFITABILITY, quarterly** | **1,285** | **1,143** | **1,066** |
| **`CbOP`, quarterly, all balance-sheet terms present** | **11** | **12** | **9** |
| **`CbOP`, quarterly, `S2`'s reduced four-term version** | **179** | **178** | **183** |

**FOUR CONCLUSIONS, AND THE SECOND IS THE ONE NO SOURCE STATES.**

1. **Gross profitability is computable at quarterly frequency for ~2,100–2,500 filers, and with the
   deflator-clean lagged denominator for ~1,900–2,200.** Both are above the programme's ~1,573
   names. **The definition that `S2` shows benefits most from quarterly data is also the one the
   data supports.** That is the opposite of round 2's annual conclusion, where the evidence and the
   computability pointed in opposite directions.

2. **THE ONE-QUARTER-LAGGED DEFLATOR IS NOT IN THE FILING THAT CARRIES THE NUMERATOR.** Only
   **3.5–5.3%** of Jun-30 10-Qs carry an `Assets` value dated Mar-31 — because Reg S-X puts the
   **prior fiscal year end** on the comparative balance sheet. Measured distribution of `Assets`
   `ddate` inside the 2025 Jun-30 cohort: `20250630` **4,727**, `20241231` **4,323**, `20240630`
   327, `20240930` 215, **`20250331` 166**. **`Gla_q` therefore requires TWO consecutive 10-Q
   filings per name per quarter**, and stitching recovers it at 86–92%. **Choosing `S2`'s deflator
   over `S1`'s costs 8–14% of the computable cross-section on top of everything else. Nobody
   states this, and it is a cost that does not exist at annual frequency**, where the prior fiscal
   year end *is* the comparative on the balance sheet you are already reading.

3. **Operating profitability at quarterly frequency (1,066 in 2025) is BELOW the programme's
   universe size**, and worse than round 2's annual figure (1,521–1,886). `XSGA` binds.

4. **`CbOP` IS NOT COMPUTABLE AT QUARTERLY FREQUENCY. NINE FILERS.** Round 2's annual strict
   intersection was 171–273 and it already called that fatal. At quarterly frequency it is
   **11 / 12 / 9**, and `S2`'s own reduced four-term construction reaches only **~180**. The binding
   terms are `PrepaidExpenseCurrent` (735) and the deferred-revenue family. **Round 2's recommended
   definition is, at quarterly frequency, a nine-name cross-section.**

### 7.5 One more measured caveat on the data source itself

**`[MEASURED IN BRIEF]` FSDS is point-in-time in its facts but NOT in every column.** `sub.txt`
carries `prevrpt` — "TRUE indicates that the submission information was subsequently amended" — which
is a **hindsight** field back-filled when DERA regenerates a zip. Measured share of 10-Qs flagged
`prevrpt = 1`: **2.41% (2013q2) → 0.80% (2019q3) → 0.00% (2025q3, 0 of 5,249)**, while genuine
`10-Q/A` submissions in those same quarters run **5.42% → 1.93% → 1.24%** of the 10-Q count.
**`prevrpt` is unusable as an amendment flag in recent vintages and reads as a look-ahead in old
ones. Use the `10-Q/A` count instead.** This qualifies round 1's *"FSDS is point-in-time BY
CONSTRUCTION"* — the facts are; one metadata column is not.

**The amendment rate itself is the honest revision risk on an as-filed quarterly panel: 5.4% of
10-Qs in 2013, 2.0% in 2019, 1.2% in 2025, were followed by a 10-Q/A.** Also measured:
**85–118 10-Q submissions per quarter carry `nciks > 1`** (multi-registrant filings, ~2%), which is
`B4`'s multi-class hazard reappearing on the submission side.

---

## 8. PAST THE SUB-QUESTIONS — THE ADJACENT QUESTION THIS BRIEF DID NOT THINK TO ASK

**Stated explicitly per the depth mandate: everything in §8 is beyond what `C1` was commissioned to
find, and §8.1 is the item I would put in front of the principal first.**

### 8.1 **A SINGLE-QUARTER PROFITABILITY SORT IS AN UNADJUSTED SEASONAL SORT, AND THE LITERATURE THAT USES IT NEVER SAYS SO**

`S1`'s `(REVTQ − COGSQ)/ATQ` and `S2`'s `Gla_q` are **raw single fiscal quarters**. A retailer's
holiday quarter and its post-holiday quarter differ by more than any cross-sectional signal in this
family. At any formation date the cross-section contains firms at **different points in their own
fiscal year**, so a rank sort on an unadjusted single-quarter ratio is partly a sort on
**fiscal-quarter phase × industry seasonality.**

**`[MEASURED IN BRIEF]` the phase spread is real but modest, and here it is:** among all 10-Q
submissions accepted in one calendar quarter, the share sharing the modal fiscal-period end is
**87.2% (2013q3) / 89.6% (2019q3) / 90.8% (2025q3)**, across **26 / 31 / 26 distinct `period`
values**. So ~9–13% of the cross-section is off-cycle *relative to each other* — **but 100% of it is
unadjusted for its OWN seasonality**, which is the larger problem and is invisible to this
measurement.

**What the sources say, and the pattern is damning:**
- **`S1`: the string `season` appears ZERO times in either the 73-page 2012 draft or the published
  28-page article.** `[MEASURED IN BRIEF]` on the extracted text of both.
- **`S8` (the 2025 retrospective): ZERO.**
- **`S4` (*Deflating profitability*): ZERO occurrences of `quarter` at all — it is a purely annual
  paper.** `[MEASURED IN BRIEF]`
- **`S2` reaches the point and applies it to a different variable.** Verbatim: *"Sorting on the
  four-quarter-change in return on equity (dRoe) yields a high-minus-low average return of 0.76%
  per month (t = 5.43)… **We interpret the evidence as indicating earnings seasonality. The
  four-quarter-change in Roe controls for seasonality, and likely better captures the underlying
  economic profitability than Roe itself.**"* **They then build `Gla_q`, `Ola_q` and `Cla_q` as raw
  single-quarter levels with one-quarter balance-sheet changes and never revisit it.**
- **`S6` (JKP) is the only library that solves it, by construction rather than by argument** —
  *"we take the sum of the item over the last four quarters"*.
- **`S7` and Akbas, Jiang & Koch solve it explicitly.** `S7` runs a *"Seasonality analysis of the
  profitability-growth effects"* section. Akbas, Jiang & Koch (2017, *The Accounting Review* 92(5))
  reportedly estimate the profit trend *"by regressing the firm's gross profit on a time trend,
  **quarterly seasonal dummies**, and a constant using the past eight quarters"* — **`[snippet only,
  via a search summariser, and therefore WEAKER than `[snippet only]` per the campaign rule. I did
  not open this paper. See §11.]`**

**The practical consequence, stated as a question rather than a finding: if this programme ever
built a quarterly gross-profitability tilt, the FIRST control is not a null — it is whether the same
sort on a TRAILING-FOUR-QUARTER numerator survives.** If the single-quarter version beats the
trailing-four-quarter version, the difference is seasonality plus surprise, and surprise is spent
ground.

### 8.2 The turnover arithmetic that `S1` states and nobody carries forward

`S1`, verbatim: the annual strategy turns over *"only once every four years… **only a quarter as
often as the high frequency profitability strategy**."* **So the quarterly strategy turns over
roughly once a year.** Against the programme's measured round trip of ~67.6 bp, one full turn a year
costs ~68 bp/year of gross return. `S1`'s quarterly VW decile spread is 0.63%/month ≈ 7.6%/year
**gross, on a long/short book, before any screen.** This lane has no fixture and computes no net
number; **the point is only that the cost multiple between the annual and quarterly versions of this
signal is 4×, stated by the source, and that no source in the family reports a cost-adjusted
quarterly number at all.** Round 2 found the same absence: `P5`'s cost-honest table predates every
quarterly variant.

### 8.3 Two reference implementations of the same signal disagree, and one claims to be a translation of the other

`Placebos/GPlag_q.py`'s own header: *"Python equivalent of GPlag_q.do, **translates line-by-line
from Stata code**."* It does not. The Stata original is four lines (§3.3). The Python port adds:

```python
# Apply comprehensive group-wise forward fill for complete data coverage
qcomp = qcomp.with_columns([
    pl.col('revtq').fill_null(strategy="forward").over('gvkey').alias('revtq'),
    pl.col('cogsq').fill_null(strategy="forward").over('gvkey').alias('cogsq'),
    pl.col('atq').fill_null(strategy="forward").over('gvkey').alias('atq')])
```

and changes the Stata `keep(match)` inner join to `how='left'`. **A group-wise forward fill with no
horizon cap means a firm that stops filing carries its last quarterly gross profit forward
indefinitely.** That is not a look-ahead — it is stale-data extension — but it changes the panel, and
`OperProfRDLagAT_q.py` in the same directory does **not** do it and keeps the inner join. **Two
quarterly profitability placebos in one repository, with different missing-data semantics, one of
which is documented as a faithful translation and is not.**

A third divergence in the same family: the **zero-fill lists differ between the annual and quarterly
pipelines.** Annual (`P4c`, quoted by round 2) zero-fills `revt, cogs, xsga, xrd, rect, invt, xpp,
drc, drlt, ap, xacc`. Quarterly (`C_CompustatQuarterly.do`, read in full) zero-fills
`acoq actq apq cheq dpq drcq invtq intanq ivaoq gdwlq lcoq lctq loq mibq prstkcy rectq sstky
txditcq` — **`drltq` and `xaccq` are selected but NOT zero-filled, and `revtq`/`cogsq`/`xsgaq`/`xrdq`
are not zero-filled at all.** **The annual and quarterly versions of "the same" signal do not treat
missingness the same way**, which means any annual-versus-quarterly comparison inside `S3` — including
the `4.4×` in §2.3 — is partly a comparison of two missing-data conventions.

### 8.4 A live instance of the wrong-HTTP-200 catalogue, logged

Guessing `https://www.federalreserve.gov/econres/feds/files/2020037pap.pdf` for `S3` returned
**HTTP 200, `application/pdf`, 2,191,581 bytes, a perfectly well-formed 62-page PDF — of an entirely
different paper**: Medhat & Palazzo, *Equity Financing Risk*, FEDS 2020-037. **Caught only by
printing the title line before reading anything else.** This is flavour #11 in the campaign's
catalogue, reproduced here for the third time. The correct file is `2021-037pap.pdf` — **with a
hyphen**; `2021037pap.pdf` returns HTTP 404 with an 81,196-byte HTML body.

---

## 9. CORRECTIONS AND ADDITIONS TO INHERITED FACTS

### 9.1 `R2-02` §2.1's deflator cell for operating profitability is wrong, and `S4` settles it

Round 2's table records the 2015 source paper's deflator as *"assets lagged one year (`P2` App.,
restating 2015)"*, established at second hand because **`P2`'s appendix says "All three variables are
deflated by the book value of total assets in year t−1"** and separately says the numerator *"follows
Ball, Gerakos, Linnainmaa and Nikolaev (2015)"*. Round 2 could not obtain the 2015 paper.

**I obtained it. `S4` deflates by CURRENT total assets.** Its abstract: *"**Gross profit scaled by
book value of total assets** predicts the cross-section of average returns."* Its data section:
*"we use the Novy-Marx (2013) definition of gross profitability by deflating gross profit by
**total book assets**."* Its Figure 1 caption, describing the operating-profitability measure:
*"deflated by **the book value of total assets**."* **`[MEASURED IN BRIEF]` the strings `lagged
assets` and `lagged total assets` do not appear anywhere in the 49-page document; the only lags in
it are the six-month availability lag and Figure 1's horizon lags.**

**So `P2`'s `t−1` deflator is `P2`'s OWN choice, not a restatement of 2015.** This confirms, from the
primary source, what round 2 could only establish from Chen & Zimmermann's code comment —
*"OP 2016 JFE seems to lag assets, but 2015 JFE does not"* — and it means **`S3d`'s note is the
correct account**: *"OP states they lag denominator, but 2015 JFE does not lag, **no clear
motivation to lag**, and our replications much closer to OP without lag."*

**This does not weaken round 2's deflator finding.** `S2`'s identity argument stands on its own. It
does mean the deflator disagreement is **between the 2015 and 2016 papers of the SAME four authors**,
not between the authors and their replicators.

### 9.2 `R2-02`'s reading of `P8` (JKP) needs a frequency label

See §2.5. JKP's profitability characteristics are **trailing-four-quarter numerators refreshed on
whichever of the annual or quarterly file is more recent, four months after fiscal period end.**
Round 2's finding — that "Profitability" sits 5th and 4th from the bottom of 13 themes in two figures
— is unaffected in substance, but **it is a statement about a quarterly-refresh construction, and it
should be recorded as one.**

### 9.3 An addition, not a correction: round 1's `$5`-and-price absence extends to the quarterly family

Round 2 confirmed by grep that the profitability literature reports **size and not price**. This lane
adds a second, independent line of evidence: **`S3d`'s `Filter` column, which records each original
paper's own screens, is EMPTY for `GP`, `OperProfRD`, `CBOperProf` and every `_q` variant** — while it
reads `abs(prc)>1` for `roaq` and `abs(prc)>5` for `RoE`. **The reference implementation has a field
for the price screen and the profitability papers leave it blank.**

**AND THE HONEST LIMIT ON THIS LANE'S SIZE-IS-NOT-PRICE OBLIGATION:** `S7` is the only quarterly
source that reports anything about the size of the names carrying the effect (*"above the 20th NYSE
percentile below which a firm is commonly considered a microcap"*, and a decile-by-decile
market-capitalisation panel), and **it reports capitalisation, not price.** FSDS carries no price
field, so **I could not measure the price distribution of the computable set and I did not
estimate one.** §10 item 6.

---

## 10. WHAT I COULD NOT VERIFY, STATED PLAINLY

1. **Every return number in §2 is transcribed from a table I read; NONE is recomputed.** This lane
   ran no portfolio, held no returns data, and has no fixture. If `S2`'s Table 4 contains a
   typesetting error in the `Gla_q1` column, this brief inherits it.
2. **`S1`'s Table A6 column assignment is my reading, not the paper's labelling.** The table prints
   six intercepts, two `MKT`/`SMB`/`HML` triples, one `PMU` slope, one `PMU_hf` slope and four
   `Adj. R²` values under headers `(1)…(6)`. I assigned them as {mean, FF3, spanning} × {`PMU_hf`,
   `PMU`} because `0.63 − 0.64 × 0.33 = 0.42` reproduces column (3)'s intercept to the cent, and
   because the published caption adds *"Regressors include the three Fama and French factors."*
   **It is an inference from an arithmetic identity and a caption, not a printed label.** The
   **cell values themselves are identical in the 2012 draft and the published article**, which is
   the one thing I can state without inference.
3. **`S4`'s Figure 1 values are unread.** The lag-sensitivity evidence exists; its magnitudes do
   not appear in any text or table I could extract. I report only the authors' own words.
4. **I did not obtain the published versions of `S4` (JFE 2015), `S7` (JBF 2023), `S9` (RAST 2019)
   or `S2` (RFS 2020).** For `S2` I read the NBER working paper and one screenshot of the published
   text; for the other three I have only drafts. **The campaign has already caught one sign flip
   between draft and publication. Three of my sources are unchecked on that axis.**
5. **`S5`'s paper (*Assaying Anomalies*) is still not obtained** — SSRN returned **HTTP 403 with a
   5,704-byte HTML body** to `curl` with the project contact string. Everything I say about `S5` is
   from its **code**, which may not match what its paper claims.
6. **NO PRICE DISTRIBUTION.** Neither the literature nor FSDS gives one. `S7` gives market
   capitalisation. **Any price distribution for a quarterly profitability sort would be an original
   measurement with nothing to check it against**, exactly as round 2 concluded for the annual case.
7. **My filing-lag distributions are right-censored at ~184 days** by the two-zip window, and the
   coverage curve's denominator is "filers observed within 184 days", not "filers who will ever
   file". The p99 figures (81/96/106) are inside the window and unaffected; the maxima are not
   meaningful.
8. **My census counts CIKs, not tradeable securities.** A CIK is not a `permno`; multi-class issuers,
   the successor-entity defect round 2 documented, and non-common-stock registrants are all
   uncorrected here. The 2,082 figure in §7.4 is an upper bound on names, not a count of them.
9. **I measured ONE fiscal quarter per era (the June quarter) in three eras.** Filing behaviour
   around the fourth fiscal quarter — where the 10-K replaces the 10-Q — is not measured, and the
   Q4 gap is a real structural feature of any quarterly panel that I did not quantify.
10. **The `roaq` numbers in §2.6 come from a metadata CSV, not from Balakrishnan, Bartov & Faurel
    (2010), which I did not open.** Treat them as weaker than `[snippet only]`.
11. **The Akbas, Jiang & Koch (2017) construction in §8.1 is from a search summariser and nothing
    else.** Per the campaign rule that is **weaker than `[snippet only]`. It is quoted to show what
    I would check, not as evidence.**
12. **I did not verify that `S3`'s quarterly placebos are actually generated by the code I read.**
    The FEDS paper's Table 4 was produced by an earlier vintage of the repository than the `master`
    I fetched, and the GitHub issue shows the timing code changed in February 2022 — **after** the
    2021 paper. **The `0.88 [6.17]` in §2.3 may have been computed under the UNPATCHED 3-month rule
    with no RDQ override.** I could not establish which.

---

## 11. WHAT I DID NOT OPEN

**Separate from §10 by the depth mandate's requirement. These are documents I identified, judged
relevant or plausibly relevant, and did not read.**

1. **Balakrishnan, Bartov & Faurel (2010), *Journal of Accounting and Economics*** — the one
   published, peer-reviewed quarterly profitability sort with a large `t` in the reference library.
   **Not opened deliberately: it is a post-loss/profit-announcement-drift paper and this lane's hard
   scope excludes that ground.** A future lane that wants the quarterly ROA line must open it.
2. **Akbas, Jiang & Koch, *The Trend in Firm Profitability and the Cross Section of Stock Returns*,
   The Accounting Review 92(5), 2017** (SSRN 2538867). **Not opened** — SSRN is blocked to this
   lane's tooling and I did not find another host. It is the source that most directly bears on
   §8.1's seasonality question and it should be the first thing a follow-up gets.
3. **Chiu, *Gross Profit Surprises and Future Stock Returns*** (LMU mirror, URL in hand). **Not
   opened: "surprises" places it on the excluded PEAD ground.**
4. **"Profitability Context and the Cross-Section of Stock Returns", BFI working paper 2023-76**
   (URL in hand). Not opened; surfaced late and I could not judge its quarterly content from the
   title.
5. **Banz & Breen (1986), *Sample-Dependent Results Using Accounting and Market Data*, JF 41(4)** —
   the classical measurement of Compustat look-ahead bias. **Not opened; Wiley paywall and I found
   no open copy.** It is the closest thing to a *quantified* look-ahead cost in this literature.
6. **The published versions of `S2` (RFS 33(5) 2020), `S4` (JFE 117(2) 2015), `S7` (JBF 2023) and
   `S9` (RAST 2019).** All paywalled. See §10 item 4.
7. **Novy-Marx & Velikov, *Assaying Anomalies* — the paper.** SSRN 403. Only the code was read.
8. **`S6`'s companion code repositories** — `bkelly-lab/ReplicationCrisis` and `bkelly-lab/jkp-data`.
   I read JKP's *documentation* but not the SAS/Python that implements the four-month rule and the
   trailing-four-quarter sum. **This is the most valuable unopened item on the list**, because it is
   the only place a trailing-four-quarter quarterly construction is implemented in public code.
9. **JKP's downloadable factor return series at `jkpfactors.com`.** They would permit an independent
   check of a quarterly-refresh `gp_at` against something — but there is no annual-only counterpart
   in their library to compare it to, which is why I did not pursue it.
10. **`S3`'s published Critical Finance Review (2022) version.** Only the FEDS working paper was
    read. Given §10 item 12, the published version may carry a different vintage of the numbers.
11. **The remaining 23 `_q` placebos in `SignalDoc.csv`** (`AssetTurnover_q`, `CapTurnover_q`,
    `PM_q`, `RetNOA_q`, `sgr_q`, and 18 others). I read the four profitability ones. **Whether the
    quarterly-versus-annual gap is specific to profitability or is a property of the whole `_q`
    family is unmeasured, and it is the single cheapest follow-up available** — the data is in a
    file already in `data/`.
12. **The other seven comment threads and the commit `3472fdf98b03` referenced in issue #50.** I read
    the issue and its two images; I did not read the diff.
13. **FSDS `pre.txt` and `tag.txt`.** I used `sub.txt` and `num.txt` only. `pre.txt` carries the
    statement and line-ordering of each fact, which would let a build distinguish an income-statement
    `GrossProfit` from one tagged elsewhere; I did not use it.
14. **Every fiscal quarter other than the June cohort, and every year other than 2013/2019/2025.**
    Nine zips of seventy.

---

## 12. WHAT THIS BRIEF DOES NOT CLAIM

**Nothing here is elevated out of `docs/research/`.** Both books are unchanged. Nothing is closed and
nothing is admitted. **No claim of any kind is made about the programme's fixture, which this lane
could not see.** Every literature figure is transcribed from a document named and graded in §1;
every measurement is marked `[MEASURED IN BRIEF]`, names its endpoint, carries a negative control,
and is reproducible from the scripts and JSON in `data/` prefixed `C1_`.

**And the one sentence I would put to the principal if only one survived:** *the quarterly variant is
the version of this family that survives the deflator argument, that XBRL computes for ~1,900–2,100
filers a quarter, and that no reference implementation is willing to call a predictor — and the lag
it needs is not a number of months but a rule about the acceptance clock, because two-thirds of
10-Qs now arrive after the close they would have to be traded on.*
