# `D1` — THE NINE UNEXAMINED CONSTRUCTION NODES, ASKED FOR A LONG LEG

**Round 4, lane `D1`, campaign `Scan-100926`.** External literature and public data only. This lane
has **no access to the programme's fixture and claims nothing about it**. Every number below is
either quoted from a named source with its TYPE and how well it was established, or marked
`[MEASURED IN BRIEF]` with its endpoint named.

Downstream of [`R3-02`](R3-02-how-much-does-the-answer-move.md) (`C2`), which handed over a ranked
list of twelve construction nodes and recorded that this programme had independently discovered
three of them. Nothing here is elevated out of `docs/research/`. Nothing is closed, admitted or
recommended.

---

## 0. THE ANSWER, STATED BEFORE THE EVIDENCE

1. **The bar is met in the *stronger* form, and the organising fact of round 3 now has a fourth
   instance that is not silence but deliberate discard.** In Walter, Weber & Weiss's own reference
   implementation the long leg **is computed and then thrown away on the next line**:
   `premium = ret[portfolio == max(portfolio)] - ret[portfolio == min(portfolio)]`, and three lines
   later `saveRDS(data_premium |> select(month, premium), ...)`. The leg exists as an expression for
   the length of one statement and is never retained. Soebhag et al. go further: they **define
   long-leg turnover as an equation, compute it, and then sum it into the long–short factor's
   turnover** before reporting. Text censuses across four documents return **zero** occurrences of
   "long leg", "short leg" or "long-only" — including the **full published JFQA text** of Schwarz,
   Walter & Weiss, which round 3 had read only in abstract and introduction.
2. **But "spread-only" is not the whole truth, and the exception is the most useful finding in this
   lane.** Cattaneo, Crump, Farrell & Schaumburg (*REStat* 2020) derive **two different optimal
   quantile counts for the same sort** — one for testing a spread, `J_t = K·n_t^{1/2}·T^{1/4}`, and
   one for **factor construction**, `J_t = K·n_t^{1/3}·T^{1/3}` — and state that the construction
   optimum **diverges more slowly**, i.e. *the portfolio you hold should be cut into fewer buckets
   than the test you run*. They call this *"a further contribution of our paper … new to the
   literature."* **The field's #1-ranked node has a derived answer, and the answer is different for
   the object the programme holds.** `[MEASURED IN BRIEF]` on French's published OP portfolios, the
   equal-weighted long leg's `t` falls monotonically as the sort gets finer — **4.11 → 3.91 → 3.71**
   (tercile → quintile → decile, 1963-07..2026-06) and **2.46 → 2.33 → 2.13** (2010-01..2026-06) —
   while the spread's mean *rises*. Two independent routes, same direction.
3. **Outlier treatment — the #2 node — is a REGRESSION node, and for a quantile sort most of its
   branches are EXACTLY ZERO.** A sort is a rank statistic. `[MEASURED IN BRIEF]` on a real
   2,612-filer GP/AT cross-section from SEC XBRL, winsorising the characteristic at 1/99, 2.5/97.5 or
   **5/95 moves 0 names out of 2,612** and turns over **0.0% of the top decile**; log, square-root and
   z-score transforms move **0 of 2,401**. Trimming at the same cutoff is not equivalent: 1/99 turns
   over **8.9%** of the long leg and 5/95 turns over **79.4%**. The boundary is exact and checkable:
   winsorisation is a no-op **while and only while the cutoff `q` is smaller than the bucket width
   `1/J`** — at `q = 20%` with deciles, **88.9% of the long leg turns over**.
4. **`C2`'s classification of "winsorise versus trim at the same cutoff" as the cleanest Type E node
   is wrong for a sort, and I can prove it.** It is Type E for a regression (Mitton's |Δ*t*| = 0.99 on
   leverage determinants). For a sort, one branch is an exact identity on membership and the other is
   not. **The genuinely arbitrary node is next door and nobody has named it: any monotone
   re-expression of the SORTING VARIABLE — level versus log, z-score, rank — is an exact identity,
   while the identical words applied to the RETURN SERIES are Type N with a derivable sign.**
5. **The level-versus-log node's sign FLIPS between a long leg and a spread, and the magnitude
   matches the mechanism to within 0.02 pp/month.** `[MEASURED IN BRIEF]`: switching from arithmetic
   to log returns moves the OP **spread** by **+0.112, +0.112, +0.107, +0.123** pp/month across four
   cells, against the predicted `½(σ²_Lo − σ²_Hi)` of **+0.121, +0.111, +0.113, +0.127**; it moves the
   **long leg** by **−0.194, −0.110, −0.176, −0.103**. The value-weighted OP spread crosses the 1.96
   line on this choice alone (`t` 1.61 → 2.30, 1963–2026). Walter, Weber & Weiss's own unreported
   output table shows the same sign across all 68 sorting variables: **mean 0.28 → 0.32 %/month and
   the significant-path share 0.50 → 0.56**.
6. **Dropping loss-makers is a SHORT-LEG node.** Walter, Weber & Weiss's profitability panel:
   including loss-makers gives mean **0.27 %/mo** and a 0.43 significant-path share; excluding them
   gives **0.18** and 0.35 — a **one-third fall in the premium** from a filter that cannot touch the
   top of a profitability sort. In Fama and French's own E/P construction the node **cannot** move
   the long leg: *"Firms with negative earnings are in only the Earnings < 0 portfolio."*
   `[MEASURED IN BRIEF]` the long leg is identical under both branches to the last decimal, by
   construction, while the spread moves by −0.073 to +0.262 pp/month depending on window and weight.
7. **Outlier treatment and dropping loss-makers are the SAME node for one deflator and DIFFERENT
   nodes for the other, and the hinge is round 2's own discovery.** Total assets cannot be negative;
   book equity can. `[MEASURED IN BRIEF]` on SEC XBRL for CY2023: of 4,911 filers reporting both
   stockholders' equity and operating income, **1,006 (20.5%) have a negative numerator AND a negative
   denominator, so their OP/BE is POSITIVE — and 633 of those 1,006 (62.9%) exceed the 90th percentile
   of the well-defined OP/BE distribution.** They would enter the **top decile** of an unfiltered
   OP/BE sort. For GP/AT the same census finds **2** firms, and both have assets of exactly zero
   rather than negative. **Fama and French's one-parenthesis requirement of "(positive) book equity"
   in the OP portfolios is not hygiene; it is the filter that keeps a fifth of the filer population
   out of the long leg.**
8. **On justify-versus-inherit, round 2's split survives and Mitton already measured it.** His Table 5
   is a ranked justification table nobody in this campaign has carried: authors state a specific
   reason for **lagging** an explanatory variable **50%** of the time, for excluding financials
   **28%**, and for their **method of outlier treatment 1%** and their **outlier cutoffs 1%** (94%
   and 95% give no reason at all). **The node Mitton measures as nearly the most disruptive is the
   node his sample explains least.** Soebhag et al. put the same point in one line: *"Regardless of
   the choice being made, a researcher can always cite at least ten other papers making the same
   choice."*
9. **Two explicit, written admissions of arbitrariness, by Fama and French, 22 years apart, on the
   node the measurement ranks first.** 1993: *"The splits are arbitrary, however, and we have not
   searched over alternatives. The hope is that the tests here and in Fama and French (1992b) are not
   sensitive to these choices. We see no reason to argue that they are."* 2015: *"When we developed
   the three-factor model, we did not consider alternative definitions of SMB and HML. The choice of
   a 2 × 3 sort on Size and B/M is, however, arbitrary. To test the sensitivity of asset pricing
   results to this choice, we construct versions … with 2 × 2 sorts."* And in the same 2015 paragraph
   they show why it is not equivalence-arbitrary after all: a 2 × 3 HML *"is not neutral with respect
   to profitability and investment … the average HML return is a mix of premiums."*
10. **Three negative controls fired and all three taught something.** One was a tolerance I set too
    tight, which calibrated my reconstruction to ±0.024 pp/month. One was a 2-decimal rounding
    coincidence in 1 month of 757. **One caught a real population: 33 of 6,428 filers report total
    assets of exactly ZERO — a deflator that cannot go negative can still go to zero, and a zero
    denominator is a different failure from a negative one (undefined, not merely extreme). No
    percentile rule creates or removes it.**

**What this lane does NOT establish.** It does not rank the nodes for a long leg — no source does,
and my own measurements cover three nodes out of nine. It does not resolve the direction of the
loss-maker node, where the published branch effect and my own reconstruction **disagree in sign** on
different signals (§9.1). Every node-level magnitude quoted is a **spread** magnitude unless marked
otherwise. And the most important unexamined node in the list — **data vintage** — is not a
researcher choice at all and no remedy in the literature closes it.

---

## 1. WHAT THIS LANE OBTAINED, WITH TYPE AND HOW WELL ESTABLISHED

| source | what it is | TYPE | how established |
|---|---|---|---|
| **Mitton, "Methodological Variation in Empirical Corporate Finance"**, *RFS* 35(2) 2022, 527–575 | 604 articles, 954 regressions, JF/JFE/RFS 2000–2018; 14 decision nodes; 65 leverage determinants | `[PEER-REVIEWED]` | **`[read in full]`** — publisher's typeset PDF, 49 pages, extracted locally (`D1_mitton2022a.txt`, 2,736 lines) |
| **Walter, Weber & Weiss, "Methodological Uncertainty in Portfolio Sorts"**, SSRN 4164117 | 14 nodes, 68 sorting variables, 69,120 paths | `[WORKING PAPER]` | **`[read in full as the authors' own code, result tables and Internet Appendices]`** — 5 R source files, 15 `.tex` result tables, all **3** Internet Appendix PDFs. **The paper's prose was NOT opened** (§14.1) |
| **Soebhag, van Vliet & Verwijmeren, "Non-Standard Errors in Asset Pricing: Mind Your Sorts"** | 11 binary choices → 2,048 constructions, 11 factors, 323-article meta-analysis | `[WORKING PAPER]` (FoFI 2022 draft) | **`[read in full]`** — Lancaster FoFI conference PDF, 2,222 lines. The **published *JEF* 78 (2024) version was NOT opened**; its abstract was read third-hand (§10.2) |
| **Hou, Xue & Zhang, "Replicating Anomalies"**, *RFS* 33(5) 2020, 2019–2133 | 452 anomalies, 1967–2016, four sort procedures | `[PEER-REVIEWED]` | **`[read in full]`** — `global-q.org` PDF, 6,824 extracted lines. **`C2` listed this as its single most valuable unopened paper; it is now opened.** |
| **Hou, Xue & Zhang**, NBER WP 23394, May 2017 | the draft of the same | `[WORKING PAPER]` | `[abstract and introduction read in full]` — draft-versus-published break recorded in §10.1 |
| **Cattaneo, Crump, Farrell & Schaumburg, "Characteristic-Sorted Portfolios: Estimation and Inference"**, *REStat* 102(3) 2020, 531–551 | portfolio sorting as a nonparametric estimator; MSE-optimal number of portfolios | `[PEER-REVIEWED]` | **`[read in full]`** — author-hosted typeset PDF, 1,155 / 2,200 extracted lines (two-column and reading-order extractions) |
| **Fama & French, "Common risk factors…"**, *JFE* 33 (1993) 3–56 | the founding construction | `[PEER-REVIEWED]` | `[read in the passages quoted]` — full PDF on disk, 3.49 MB; the three construction passages read verbatim |
| **Fama & French, "A five-factor asset pricing model"**, *JFE* 116 (2015) 1–22 | 2×3 vs 2×2 vs 2×2×2×2 | `[PEER-REVIEWED]` | `[read in the passages quoted]` — full PDF on disk |
| **Kenneth R. French, Data Library, "Detail for Portfolios Formed on Operating Profitability"** and **"… on Earnings/Price"** | the canonical construction, stated by its author | **`[PRIMARY DATA DOC]`** | **`[read in full]`** — both pages, HTTP 200, text extracted |
| **Schwarz, Walter & Weiss, "Rewriting CRSP's History"**, *JFQA*, accepted, dated 2026-02-24 | the CRSP tape change; 68 sorting variables × several thousand paths | `[PEER-REVIEWED]` | **`[read in full]`** — publisher's open-access PDF, 4,943 extracted lines. **`C2` had abstract and introduction only; the body is now read.** Its **46-page Internet Appendix was NOT opened** |
| **Adams, Hayunga, Mansi, Reeb & Verardi, "Identifying and treating outliers in finance"**, *Financial Management* 48(2) 2019, 345–384 | the methods paper the field cites for this node (Mitton's footnote 12) | `[PEER-REVIEWED]` | **`[abstract only]`** — no open-access location exists (OpenAlex and Unpaywall both return none); paywalled at Wiley, not attempted |
| **Shin, "Which Portfolios? The Construction Dependence of Factor Model Performance"**, arXiv 2606.19550v1, 17 June 2026 | construction dependence of **long-only** test assets; selection × weighting × holding × rebalancing | `[WORKING PAPER]` | `[abstract read in full; the construction and rebalancing sections read in the passages quoted]` |
| **"Deep into Negative Territory: Who Negative Book Equity Stocks Are and Their Risk-Return Implications"** (AUT Centre for Financial Research copy, no date on the file) | the case against excluding negative-BE firms | `[WORKING PAPER]` | `[read in full]` — 631 KB PDF, 1,416 extracted lines. **Authors are not named on the copy I hold** (§12.5) |
| **Novy-Marx & Velikov, "A Taxonomy of Anomalies and their Trading Costs"**, *RFS* 29(1) 2016 | the buy/hold-spread construction node | `[PEER-REVIEWED]` | **`[snippet only]`** — located, not opened; one named mechanism carried in §8.4 |

Plus **`C2`'s own reads**, cited as `C2` where I rely on them rather than re-establishing them:
Menkveld et al. (*JF* 2024), Coqueret (arXiv 2023), Hasler (*CFR* 2023), Jensen-Kelly-Pedersen
(*JF* 2023), Del Giudice & Gangestad (*AMPPS* 2021), Akey-Robertson-Simutin, Mitton 2022b.

**My own measurements**, all `[MEASURED IN BRIEF]`, scripts and outputs in
`data/D1_measure_nodes.py` · `data/D1_measurement.txt` · `data/D1_measurement.json` ·
`data/D1_diag.py` · `data/D1_diag.txt` · `data/D1_sec_signflip.py` · `data/D1_sec_signflip.txt` ·
`data/D1_sec_diag.py` · `data/D1_sec_diag.txt` · `data/D1_rank_invariance.py` ·
`data/D1_rank_invariance.txt`. Endpoints:
`https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/` (vintage stamp inside every file:
`This file was created using the 202607 CRSP database.`) and
`https://data.sec.gov/api/xbrl/frames/us-gaap/<tag>/USD/<period>.json`. **Fourteen negative controls,
three of which fired** (§7.5, §5.4, §4.4).

---

## 2. NODE BY NODE: WHAT THE LITERATURE **JUSTIFIES** AND WHAT IT **INHERITS**

### 2.1 Mitton already measured the justification rate, and the campaign has not carried it

**Mitton Table 5** `[PEER-REVIEWED]` `[read in full]` reports, for each decision, how often authors
give a **specific reason**, how often they say they **follow prior literature**, and how often they
give **no reason**, across 604 articles:

| Mitton's question | occurrences | specific reason | follows prior lit. | **no reason** |
|---|---|---|---|---|
| Why is the explanatory variable **lagged**? | 263 | **50%** | 12% | 38% |
| Why is the **dependent variable logged**? | 100 | 29% | 18% | 53% |
| Why are **financial firms excluded**? | 429 | 28% | 16% | 56% |
| Why are **utilities excluded**? | 290 | 27% | 18% | 54% |
| Why is the **explanatory variable logged**? | 53 | 26% | 11% | 62% |
| Why is **firm size** a control? | 755 | 18% | 19% | 63% |
| Why convert a continuous variable to a **dummy**? | 131 | 15% | 4% | 81% |
| Why this **dependent-variable proxy**? | 954 | 10% | 13% | 78% |
| Why the **beginning-of-year denominator** on flow/stock variables? | 150 | **7%** | 17% | **77%** |
| Why this **industry-dummy definition**? | 275 | 3% | 3% | 94% |
| Why this **firm-size proxy**? | 755 | **1%** | 7% | **92%** |
| **Why this method of outlier treatment?** | 542 | **1%** | 4% | **94%** |
| **Why these outlier cutoffs?** | 542 | **1%** | 4% | **95%** |

Mitton's own gloss: *"Thus, the available information suggests that a lack of theoretical guidance
leaves a great deal of latitude for methodological choices in corporate finance."* And the honest
caveat, in his words: *"it is possible that authors omit explanations not for a lack of theoretical
basis, but simply to avoid explaining what they view as routine or unimportant, or to reduce the
length of a paper."*

> **THE PATTERN, AND IT IS EXACTLY ROUND 2'S SPLIT.** The decisions that carry an **identification or
> economic claim** get justified — lagging (50%), logging the dependent variable (29%), excluding an
> industry whose leverage mechanism differs (28%). The decisions that **read as data hygiene** get
> nothing — size proxy (1%), industry definition (3%), **outlier method (1%) and outlier cutoff
> (1%)**. **And the inversion is the finding: the node Mitton measures as nearly the most disruptive
> is the least explained in his sample.**

**One internal discrepancy, recorded.** Mitton's introduction says authors *"explain their method of
outlier treatment only 6% of the time"*; Table 5 row 9 gives **1% specific + 4% prior = 5%**. A
one-point rounding difference between the prose and the table of the same paper. I quote the table.

### 2.2 The split tested on the nodes `C2` did not examine, in the papers' own words

**(a) Hou, Xue & Zhang (2020) — the most-cited construction paper in the field. Two nodes get
paragraphs; two get a clause.** `[PEER-REVIEWED]` `[read in full]`

*Justified, at length:* **value-weighting** — *"First, value-weighting accurately reflects the wealth
effect experienced by investors (Fama 1998). Second, microcaps are influential in equal-weighted
returns. Microcaps are on average only 3% of the aggregate market capitalization of the
NYSE-Amex-NASDAQ universe but account for about 60% of the total number of stocks … Because of high
transaction costs, anomalies in microcaps are difficult to exploit in practice."* And **NYSE
breakpoints** — *"We emphasize NYSE breakpoints because the cross-sectional dispersion of anomaly
variables is the largest among microcaps … With NYSE-Amex-NASDAQ breakpoints, microcaps can account
for more than 60% of the stocks in extreme deciles. These microcaps can inflate the magnitude of
anomalies, especially when combined with equal-weighted returns."*

*Inherited in a clause, with no reason:* **"We exclude financial firms and firms with negative book
equity."** That is the entire treatment of the #3-ranked node in an RFS paper whose subject is
construction. **Quantile count** gets less than that — *"For portfolio sorts (into deciles)"*, in
parentheses.

*Explicitly declined, and flagged:* **price screens** — *"Some studies exclude stocks with prices per
share lower than $1 or $5. We do not impose such a screen. In particular, microcaps are included in
our sample."*

**(b) Fama and French.** The justification is sometimes a **frequency claim** rather than an economic
one, and sometimes a named bias with a citation. Both verbatim from *JFE* 33 (1993):

- Negative book equity: *"**We do not use negative-BE firms, which are rare before 1980**, when
  calculating the breakpoints for BE/ME or when forming the size-BE/ME portfolios."* A
  data-frequency claim about a period that ended 46 years ago, in a subordinate clause.
- Stock age: *"Moreover, **to avoid the survival bias inherent in the way COMPUSTAT adds firms to its
  tapes [Banz and Breen (1986)], we do not include firms until they have appeared on COMPUSTAT for
  two years.** (COMPUSTAT says it rarely includes more than two years of historical data when it adds
  firms)."* A named bias, a named mechanism, a named citation. **Fully justified** — and note it is a
  **listing age on the accounting database**, not a stock age on the price series (§6.4).

**(c) Soebhag et al. run the test and name the result.** `[WORKING PAPER]` `[read in full]` Their
meta-analysis of 323 articles finds that **no design option is chosen 100% of the time, and none is
rare**: *"Regardless of the choice being made, a researcher can always cite at least ten other papers
making the same choice."* Their framing of the test is the same as round 2's: *"If choices are being
made randomly, the proportion of studies in which a particular option is selected will be close to
50% … However, if there are good reasons for particular design choices, or if authors build on the
choices being made in earlier work, then we might expect some choice options to be selected (close
to) 100% of the time."*

**(d) Kenneth French's own data documentation justifies the OUTLIER choice, and the justification is
"the numbers are real."** `[PRIMARY DATA DOC]` `[read in full]`, verbatim from the Operating
Profitability detail page:

> *"Please be aware that some of the value-weight averages of operating profitability for deciles 1
> and 10 are extreme. These are driven by extraordinary values of OP for individual firms. **We have
> spot checked the accounting data that produce the extraordinary values and all the numbers we
> examined accurately reflect the data in the firm's accounting statements.**"*

**That is the canonical reference implementation of the programme's one computable family stating, in
writing, that it applies NEITHER winsorisation NOR trimming, and giving its reason.** It is the only
*justified* outlier decision I found anywhere in this corpus.

### 2.3 How often each branch is actually chosen — and the two meta-analyses disagree

Walter, Weber & Weiss hard-code literature frequencies for every node in
`01_replication_code/17_Decision_Nodes.R`, for **two** samples (56 papers and 109 papers). Soebhag
et al. report theirs for 323 articles. `[read in full as the authors' own code]` /
`[read in full]`.

| node | branch | WWW 56 papers | WWW 109 papers | Soebhag 323 articles |
|---|---|---|---|---|
| quantiles (main) | 5 / 10 | 48.5 / 51.5 | 51.1 / 48.9 | 30-70 ≈ 20-80 ("roughly equals") |
| quantiles (secondary) | 2 / 5 | 55.6 / 44.4 | 52.6 / 47.4 | — |
| breakpoint exchanges | NYSE / all | 30.7 / 69.3 | 26.6 / 73.4 | **41.5** / 58.5 |
| **weighting** | **VW / EW** | **43.4 / 56.6** | **45.5 / 54.5** | **58.5 / 41.5** |
| sorting method | single / dep / indep | 58.0 / 16.2 / 25.8 | 57.6 / 17.8 / 24.6 | independent **71.8** |
| formation time | monthly / FF-June | 20.9 / 79.1 | 21.9 / 78.1 | June size **67.4** |
| financials | included | 55.2 | 63.2 | **71.2** (28.8 exclude) |
| utilities | included | 83.3 | 81.5 | **90.1** (9.9 exclude) |
| size exclusion | none / 10% / NYSE-20% | 66.2 / 1.4 / 32.4 | 61.5 / 3.6 / 34.9 | include microcaps **88.2** |
| price exclusion | $0 / $1 / **$5** | 86.2 / 5.0 / **8.8** | 79.3 / 6.1 / **14.6** | no filter **81.7** |
| **stock age ≥ 2 years** | **imposed** | **67.2** | **57.0** | — |
| **negative earnings dropped** | **yes** | **16.7** | **18.2** | — (not a node) |
| negative book equity dropped | yes | 27.6 | **41.7** | **22.0** |

Four facts in this table matter to a programme that is equal-weighted, floored at `$5`, and
long-only:

1. **The two NSE papers disagree about which weighting scheme is the majority convention.**
   WWW's code says equal-weighting is the majority (56.6% / 54.5%); Soebhag says value-weighting is
   (58.5%). **Recorded, not adjudicated** (§9.2).
2. **A two-year stock-age filter is the MAJORITY convention — 57% to 67% of papers — and it is the
   one node in the list that nobody here has ever named.** It is also the only node whose original
   justification is a named database artefact rather than an economic argument.
3. **Dropping loss-makers is a MINORITY convention — about one paper in six.** The #1-ranked node for
   profitability sorts is the branch most papers decline.
4. **A `$5` price floor is used by 8.8% to 14.6% of papers**, and WWW's own two samples disagree by a
   factor of 1.7 on how rare it is.

**And the negative-book-equity frequency spreads from 22.0% to 41.7% across three measurements of
the same literature.** I could not determine what distinguishes WWW's 56-paper from their 109-paper
sample without the paper's prose (§12.1).

---

## 3. ARBITRARY, OR A DIFFERENT ECONOMIC QUESTION?

`C2` established the taxonomy (Del Giudice & Gangestad's Type E / Type N / Type U) and reported that
**every node it examined closely turned out to be Type N**. The brief asked me to test that on the
nodes `C2` did not examine. **It survives, with one correction and one genuine Type E discovery.**

### 3.1 Fama and French declare a node arbitrary twice, in writing, and then disprove their own claim

*JFE* 33 (1993), on the 2×3 design:

> *"Our decision to sort firms into three groups on BE/ME and only two on ME follows the evidence in
> Fama and French (1992a) that book-to-market equity has a stronger role in average stock returns
> than size. **The splits are arbitrary, however, and we have not searched over alternatives. The hope
> is that the tests here and in Fama and French (1992b) are not sensitive to these choices. We see no
> reason to argue that they are.**"*

*JFE* 116 (2015), twenty-two years later:

> *"When we developed the three-factor model, we did not consider alternative definitions of SMB and
> HML. **The choice of a 2 × 3 sort on Size and B/M is, however, arbitrary.** To test the sensitivity
> of asset pricing results to this choice, we construct versions of SMB, HML, RMW, and CMA in the same
> way as in the 2 × 3 sorts, but with 2 × 2 sorts on Size and B/M, OP, and Inv, using NYSE medians as
> breakpoints for all variables."*

And then, in the same paragraph, the reason it is **not** Type E:

> *"Since HML is constructed without controls for OP and Inv, however, it is not neutral with respect
> to profitability and investment. **This likely means that the average HML return is a mix of
> premiums related to B/M, profitability, and investment.** Similar comments apply to RMW and CMA."*

> **So the node the measurement ranks FIRST (WWW MAD 1.08 overall, 1.09 for profitability) is the node
> its own authors twice called arbitrary — and the same authors show it carries unintended factor
> exposures. That is the third independent instance of the pattern `C2` found in Hasler's June
> convention: a choice that looks like a taste turns out to encode an exposure.** The other two,
> from this lane: Soebhag et al. on unconditional sorting — *"constructing the unconditional value
> factor overweights sectors that contain stocks with high book-to-market ratios, such as utility
> firms in the long leg, whereas the short value leg gets excess exposure towards technology
> stocks"* — and Fama and French above.

### 3.2 `[MEASURED IN BRIEF]` THE ONE PROVABLY ARBITRARY NODE, AND IT IS NOT WHERE ANYBODY LOOKED

A quantile sort is a **rank** statistic. Therefore any **weakly monotone** transform of the sorting
variable leaves every portfolio's membership unchanged, and any transform that **deletes**
observations moves every breakpoint. That is a theorem; the question is whether it survives real,
tie-heavy, fat-tailed data. **Endpoint:**
`https://data.sec.gov/api/xbrl/frames/us-gaap/{GrossProfit,Assets}/USD/{CY2023,CY2023Q4I}.json`.
Cross-section: **2,612 filers**, GP/AT, with `min −2.463`, `p99 +3.585`, **`max +844.539`** (the
extreme is 236× the 99th percentile) and **52 tied values**. Decile sort, `J = 10`, deterministic
tie-breaking.

| change to the sorting variable | names whose decile changes | **% of the LONG LEG that turns over** |
|---|---|---|
| level → **log** (x > 0 subsample, n = 2,401) | **0 of 2,401** | **0.0%** |
| level → **square root** | **0 of 2,401** | 0.0% |
| level → **z-score** | **0 of 2,401** | 0.0% |
| **winsorise at 1/99** | **0 of 2,612** | **0.0%** |
| **winsorise at 2.5/97.5** | **0 of 2,612** | 0.0% |
| **winsorise at 5/95** | **0 of 2,612** | **0.0%** |
| winsorise at **20/80** (coarser than a decile) — *control P2, must fire* | **520 of 2,612** | **88.9%** |
| **trim at 1/99** (n 2,612 → 2,560) | **104 of 2,560** | **8.9%** |
| **trim at 5/95** (n 2,612 → 2,352) | **520 of 2,352** | **79.4%** |
| non-monotone `x − 0.5x²` — *control P1, must fire* | **559 of 2,612** | 55.2% |

**Three results, and each of them is a correction to something the campaign was carrying.**

1. **`C2`'s Type-E call on "winsorise versus trim at the same cutoff" is wrong for a SORT.** One
   branch is an exact identity on membership; the other turns over 8.9% of the long leg at 1/99 and
   79.4% at 5/95. The two branches are **not** two equally valid answers to the same question; one
   changes the portfolio and one does not. `C2`'s call is correct for a **regression**, where Mitton
   measures |Δ*t*| = 0.99 on 65 leverage determinants and 3.37 on quasi-random profitability ratios.
   **The node's type depends on the estimator, not on the node.**
2. **There IS a genuinely Type E node in the list, and it is Mitton's #7/#8 read one way round.**
   *Level versus log of the SORTING VARIABLE* is an exact identity for a sort — 0 of 2,401 names move.
   Mitton ranks level→log at |Δ*t*| 1.37 and 1.10 for regressions, and 8.01 for quasi-random
   Compustat ratios. **The same node is exactly zero for a sort and among the largest for a
   regression.** This is the cleanest Type E node anybody in this campaign has identified, and its
   arbitrariness is *provable* rather than asserted.
3. **The boundary condition is exact and the programme can check it.** Winsorisation of a
   characteristic is a no-op **if and only if the cutoff `q` is strictly inside the extreme bucket**,
   i.e. `q < 1/J`. With deciles, 5% is safe and 20% destroys 88.9% of the long leg. **A slot-based
   long-only book has an effective `1/J` equal to its slot share of the eligible universe** — so the
   safe cutoff shrinks as the book concentrates. Nothing in the published grids states this, because
   none of them has an outlier node at all (§4.2).

### 3.3 The placements, with what each one encodes

| node | type | what it encodes, and the evidence |
|---|---|---|
| **Monotone re-expression of the sorting variable** (level/log/sqrt/z-score/rank) | **E, proven** | Nothing. Exact identity, 0 of 2,401 names `[MEASURED IN BRIEF]`. |
| **Winsorise the characteristic at `q < 1/J`** | **E, proven** | Nothing — for the sort. 0 of 2,612 names `[MEASURED IN BRIEF]`. It is **not** nothing for a composite index or a regression (§4.2). |
| **Winsorise vs TRIM the characteristic at the same cutoff** | **N** | Trimming moves every breakpoint and turns over 8.9%–79.4% of the long leg `[MEASURED IN BRIEF]`. **Corrects `C2`.** |
| **Outlier treatment of the RETURN series** | **N** | Symmetric trims raise the mean of a left-skewed series. On the EW OP long leg, 1963–2026, `t` 3.73 → 5.43 at 5/95 `[MEASURED IN BRIEF]`. |
| **Quantile count** | **N, with a derived optimum** | CCFS: MSE-optimal `J` exists, is data-driven, and **differs between testing and construction**. Soebhag's mechanism: extremity versus **breadth**. |
| **Dropping loss-makers** | **N, and it is a claim about the SHORT leg** | WWW profitability panel 0.27 → 0.18 %/mo; French's construction puts them in their own bucket. |
| **Dropping negative book equity** | **N, contested** | Soebhag: *"Firms with negative book equity value might have particularly high default risk."* Directly contested (§9.3). And for a **ratio deflated by book equity it is a sign-flip filter**, not a distress filter (§4.4). |
| **Level vs LOG of the RETURN** | **N, with a derivable sign that FLIPS between the two objects** | `½(σ²_Lo − σ²_Hi)` predicts the spread's shift to within 0.02 pp/mo in four of four cells `[MEASURED IN BRIEF]`. |
| **Dependent vs independent sort** | **N** | Soebhag: independent sorting *"may result in sparse portfolios, with the consequence that a factor portfolio is not well-diversified"* (Ang et al. 2006, Novy-Marx 2013, Wahal & Yavuz 2013). |
| **The ORDER of a multi-way dependent sort** | **U** | Soebhag: *"implementing a dependent sorting procedure raises the question of what order"* — raised, not resolved. The only clean Type U node in the list. |
| **Rebalancing / formation date** | **N** (`C2`: Hasler's momentum exposure) | And a **new sub-node**: *within-period weight management*, buy-and-hold versus constant-weight (§6.3). |
| **Stock-age filter** | **N**, for a database reason | FF1993's Compustat-backfill survivor bias, with a citation. |
| **Data vintage** | **not a choice at all** | `C2` §8.1; Schwarz et al. confirmed in full (§6.6). |
| **Breakpoint exchanges** | **N** | HXZ's microcap-dispersion argument; Soebhag's largest single Sharpe effect. |

> **`C2`'s rule survives and should be stated more sharply: DEFAULT TO TYPE U, and when a node does
> turn out to be Type E it will be because it is a MONOTONE RE-EXPRESSION — the only class of change
> a rank statistic cannot see.**

---

## 4. OUTLIER TREATMENT — THE #2 NODE, IN FULL

### 4.1 What is standard: winsorise; at 1/99; on the characteristic; never on the return

All from **Mitton Table 4**, `[PEER-REVIEWED]` `[read in full]`, 604 articles:

| Panel D — outlier treatment | Profitability regressions | ALL | ALL 2016–18 |
|---|---|---|---|
| **Winsorise** | 49% | **48%** | **62%** |
| **Retain (do nothing)** | 43% | **43%** | 34% |
| **Trim** | 8% | **9%** | 4% |

| Panel E — cutoff, conditional on treating | Profitability | ALL | ALL 2016–18 |
|---|---|---|---|
| **1st/99th** | 74% | **75%** | 79% |
| 5th/95th | 9% | 8% | 9% |
| 0.5th/99.5th | 5% | 6% | 5% |
| 2.5th/97.5th | 3% | 3% | 1% |
| 2nd/98th, 3rd/97th, 10th/90th | 1% each | 1% each | ≤1% |
| other / not specified | 4% | 6% | 4% |

And the trend, in Mitton's words: *"While the percentage of papers winsorizing data was usually below
20% in the earlier years of the sample, the percentage trended upward over the years to **as high as
75% in 2016** … In more recent years, **over 70% of studies that treat outliers … do so at the 1st
and 99th percentiles.**"* Outlier treatment is the **one** node in his sample where a consensus is
forming.

**Frequency: per cross-section.** Both reference implementations I read do it the same way. Hou, Xue
& Zhang: *"When performing monthly cross-sectional regressions, we winsorize the regressors at the
1%-99% level **each month** to mitigate the impact of outliers."* Walter, Weber & Weiss's code does it
`group_by(year)`, i.e. per annual cross-section, with a rank-replacement function. **Nobody
winsorises once over a pooled panel, and nobody winsorises a return.**

**Applied to what: the CHARACTERISTIC, and only when the characteristic is a COMPOSITE.** This is the
sharpest thing in §4 and it is established from two reference implementations at once.

- **Hou, Xue & Zhang winsorise the REGRESSORS in Fama-MacBeth regressions and NOT the sorting
  variables for their portfolio sorts.** The asymmetry is deliberate and they state the reason on the
  regression side: ordinary least squares *"tend[s] to put more weights on outliers with volatile
  returns and extreme anomaly variables, which most likely belong to microcaps."* Separately they
  winsorise a handful of **individual characteristics** inside their own definitions (`Sue`, `Oca`, a
  PPE-based ratio, the O-score inputs) — *"To alleviate the impact of outliers, we winsorize Oca at
  the 1st and 99th percentiles"*.
- **Walter, Weber & Weiss's code winsorises exactly four composites' inputs and nothing else.** From
  `14_Sorting_variables_yearly.R`: the eleven Altman-Z / Ohlson-O components
  (`wcta, reta, ebitta, metl, saleta, log_ta, tlta, clca, nita, futl, chin`), the real-estate ratio
  `rer`, and the five Whited-Wu components (`cf, tltd, lnta, isg, sg`) — each at `cut = 0.01`, per
  fiscal year, by a two-sided quantile replacement. Their own Internet Appendix confirms it and names
  its source: *"We follow Hou et al. (2020) and winsorize all variables except for dummy variables at
  the 1% and 99% quantile of their respective distribution."* **Nothing else in 68 sorting variables
  is winsorised, and outlier treatment is not one of the 14 decision nodes.**
- **Kenneth French does neither, on the programme's own family, and says why** (§2.2(d)).

> **So the field's practice is coherent once you see the mechanism: winsorise where the estimator is
> NOT rank-based (a regression, or a linear composite index whose ranks depend on its inputs'
> levels), and leave a univariate ratio sort alone, because there the treatment is an exact no-op
> (§3.2). The reason the #2-ranked node is absent from every published NSE grid is not an oversight.
> It is that for the object those grids measure, most of its branches do nothing.**

### 4.2 What it is worth, in the units each literature uses — and the two rankings disagree

**Mitton's |Δ*t*| is a regression quantity and must be read against his own calibration.** He reports
that, with purely random explanatory variables, the expected |Δ*t*| is **1.13** for replacing the
variable with an entirely new random one and **0.00** for rounding it to two decimals. In
profitability regressions, winsorise→retain gives **1.11** — *"implying that outlier treatment is
almost as disruptive to the regression as if an entirely new explanatory variable were generated."*
That is the best single sentence on this node's magnitude, and it is better than the raw 3.74, which
must be read against a mean |*t*| of **4.80** (continuous) / **2.64** (dummy) across his simulation.

| Mitton's node | Table 8 (65 **leverage** determinants) | Table 7 ALL (quasi-random) | Table 7 **PROFITABILITY** |
|---|---|---|---|
| Winsorise 1/99 → **retain** | **3.74** | **9.20** | **12.86** |
| Dependent variable, different **denominator** | **3.91** | 7.92 | **12.31** |
| Continuous → dummy | 3.72 | 8.70 | 7.81 |
| Winsorise 1/99 → **5/95** | 1.83 | 6.71 | **9.82** |
| Level → logged dependent variable | 1.37 | 8.01 | — |
| Contemporaneous → lagged | 1.41 | 4.71 | 6.46 |
| **End-year → beginning-year denominator** | — | 4.26 | **6.73** |
| Winsorise 1/99 → **TRIM 1/99** | 0.99 | 2.62 | **3.37** |
| Most → second-most common size control | 0.67 | 2.40 | 4.90 |
| **Include all industries → exclude financials** | **0.27** | **0.52** | **0.57** |

**Two things the campaign has been reading slightly wrong, corrected here.**

- **The 12.86 is not a profitability *sort*.** It is a regression in which the **dependent** variable
  is a profitability measure (most commonly ROA) and the **explanatory** variable is a ratio built
  from two randomly chosen Compustat items. Mitton's own framing: *"in profitability regressions,
  winsorizing outliers changes the t-statistic by 12.86 on average."* It bears on a profitability
  regression, not on a profitability-sorted portfolio.
- **The 3.74 is the LEVERAGE table.** 65 proposed determinants of leverage, 49 continuous and 16
  dummy.

**And a ranking disagreement that matters more than either number.** Mitton's **least** impactful
node of twelve is *exclude financial firms* (0.27 / 0.52 / 0.57). Walter, Weber & Weiss rank
**Financials 7th of 14 overall (MAD 0.75) and it is 1.08 for the profitability cluster** — the
fourth-largest node there. **The regression ranking and the sort ranking disagree, in opposite
directions, on the one node both measure cleanly.** Recorded in §9.4.

**Mitton also measures the programme's round-2 deflator discovery, and nobody has carried it.**
Panel G: on flow-over-stock dependent variables, the **end-of-year denominator is used 62% of the
time, the beginning-of-year 33%, an average of the two 4%** — and Table 5 row 12 says the
beginning-of-year choice is explained with a specific reason **7%** of the time, 77% not at all.
Table 7 prices it at **6.73** in profitability regressions. **Round 2 discovered `GP/AT` vs `GP/AT₋₁`
as an identity; Mitton has it as a ranked node with a usage split and a justification rate, in the
same paper `C2` read.**

### 4.3 `[MEASURED IN BRIEF]` OUTLIER TREATMENT OF THE RETURN, ON A LONG LEG AND ON A SPREAD

No source in this corpus applies an outlier rule to a return series and reports the effect on a long
leg. **Endpoint:** French's `Portfolios_Formed_on_OP_CSV.zip` and
`F-F_Research_Data_5_Factors_2x3_CSV.zip`, vintage `202607`. Object 1 is `Hi 10 − RF` (a cash-funded
long leg); Object 2 is `Hi 10 − Lo 10` (the spread). Same months, same file, same sort.
`t` is the iid `mean / (sd/√n)`; no Newey-West, stated because it matters.

**1963-07 .. 2026-06, equal-weighted, n = 757**

| treatment of the monthly return series | LONG LEG mean / `t` / \|Δ`t`\| | SPREAD mean / `t` / \|Δ`t`\| |
|---|---|---|
| **raw** | **+0.833 / +3.73 / —** | **+0.131 / +0.86 / —** |
| winsorise 1/99 | +0.842 / +3.98 / 0.25 | +0.176 / +1.27 / 0.40 |
| trim 1/99 | +0.870 / +4.43 / 0.70 | +0.197 / +1.54 / 0.68 |
| winsorise 5/95 | +0.849 / +4.61 / 0.88 | +0.189 / +1.66 / 0.80 |
| **trim 5/95** | **+0.902 / +5.43 / 1.70** | **+0.256 / +2.59 / 1.72** |
| **trim TOP 1% only** (drop winners) | +0.642 / +3.01 / 0.72 | **+0.010 / +0.07 / 0.79** |
| **trim BOTTOM 1% only** (drop losers) | +1.061 / +5.11 / 1.38 | +0.316 / +2.36 / 1.50 |

**1963-07 .. 2026-06, value-weighted, n = 757**

| treatment | LONG LEG | SPREAD |
|---|---|---|
| **raw** | **+0.691 / +4.11 / —** | **+0.252 / +1.61 / —** |
| winsorise 1/99 | +0.715 / +4.43 / 0.32 | +0.253 / +1.69 / 0.09 |
| trim 1/99 | +0.725 / +4.74 / 0.63 | +0.229 / +1.62 / **0.01** |
| winsorise 5/95 | +0.702 / +4.88 / 0.76 | +0.202 / +1.52 / 0.09 |
| **trim 5/95** | **+0.762 / +5.92 / 1.81** | **+0.209 / +1.78 / 0.17** |
| trim TOP 1% only | +0.569 / +3.49 / 0.62 | +0.107 / +0.73 / 0.88 |
| trim BOTTOM 1% only | +0.846 / +5.35 / 1.24 | +0.374 / +2.49 / 0.88 |

2010-01 .. 2026-06 (n = 198) is in `data/D1_measurement.txt`; |Δ`t`| there ranges 0.03 to 1.01.

**Four readings.**

1. **Magnitude.** On a return series the node is worth |Δ`t`| **0.01 to 1.81** — real, but far below
   Mitton's 3.74 in regressions and nowhere near 12.86. **Outlier treatment is a big node for a
   regression, a moderate node for a return series, and exactly zero for a univariate sort's
   membership.** Those three statements are all true and the literature runs them together.
2. **The long leg is MORE exposed than the spread, under value weighting decisively so.** At 5/95
   symmetric trimming: EW full sample 1.70 (leg) vs 1.72 (spread) — equal; **VW full sample 1.81 vs
   0.17 — a factor of ten**; EW 2010–2026 0.64 vs 0.54; VW 2010–2026 1.01 vs 0.08. The mechanism is
   mechanical: **a spread differences out the common market tail and a long leg keeps it.** A
   value-weighted long leg is almost pure market tail, so its extreme months are exactly the months
   an outlier rule removes.
3. **Every symmetric treatment RAISES the long leg's mean and `t`**, in both windows and both
   weightings, because the series is left-skewed — crashes are bigger than rallies. **An outlier rule
   applied to returns flatters a long-only book.**
4. **`CLAUDE.md`'s symmetric-trim rule is vindicated, with numbers.** Dropping only the top 1% of
   months costs the EW long leg **0.191 pp/month** (0.833 → 0.642) and costs the EW spread **92% of
   its mean** (0.131 → 0.010). Dropping only the bottom 1% *adds* 0.228 and 0.185. The two one-sided
   trims move `t` by 0.72 and 1.38 in opposite directions; the symmetric trim's net is 0.70.
   **Reporting one tail and not the other would have changed the verdict on the full-sample EW spread
   from "nothing" to "dead" or to "significant".**

### 4.4 `[MEASURED IN BRIEF]` THE INTERACTION WITH THE DEFLATOR, AND A CONTROL THAT FIRED ON REAL DATA

The brief asked whether the outlier choice interacts with the deflator, *"given that a profitability
ratio with a near-zero denominator produces exactly the extreme values outlier rules bite on."* It
does, and the interaction is sharper than near-zero: **a denominator that changes SIGN inverts the
ratio's meaning, and a rank sort cannot see it.** Total assets cannot be negative. Book equity can.

**Endpoint:** `https://data.sec.gov/api/xbrl/frames/us-gaap/<tag>/USD/<period>.json`, CY2023Q4I
(instantaneous) and CY2023 (duration). Fact counts as returned: `Assets` 6,428 · `StockholdersEquity`
6,265 · `GrossProfit` 2,788 · `OperatingIncomeLoss` 5,348 · `NetIncomeLoss` 6,380. The file's own
`label` field was read before any number was taken from it; `StockholdersEquity` self-describes as
**"Stockholders' Equity Attributable to Parent"**, which is **not** the same construct as Compustat's
book equity (no minority interest, no deferred-tax or preferred-stock adjustments) — stated because
the field name is narrower than the concept.

Of **4,911 filers reporting both StockholdersEquity and OperatingIncomeLoss**:

| | count | share |
|---|---|---|
| negative book equity | 1,147 | **23.4%** |
| negative operating income | 2,894 | 58.9% |
| **both negative → OP/BE is POSITIVE (sign flip)** | **1,006** | **20.5%** |
| negative BE, positive OI → ratio turns negative | 141 | 2.9% |
| positive BE, negative OI | 1,888 | 38.4% |
| positive BE, positive OI | 1,875 | 38.2% |

The sign-flipped values: **n = 1,006, min +0.000, median +0.599, max +197.660; 358 exceed +1.00.**
The well-defined distribution (BE > 0, n = 3,763) has **p90 = +0.356** and p99 = +2.022. Therefore
**633 of the 1,006 sign-flipped firms (62.9%) sit above the top-decile cutoff of the well-defined
OP/BE distribution.** On the deflator that cannot flip: of 2,614 filers with both GrossProfit and
Assets, **2** have a non-positive denominator.

**Negative controls.** `C1` an impossible period (`CY1890Q1I`) must return no facts → **HTTP 404, 320
bytes, 0 facts. PASS.** `C3` negative stockholders' equity must be non-zero → 1,361 of 6,265. **PASS.**
`C4` the two frames must be different documents → fact counts 6,428 vs 6,265, symmetric CIK
difference 619. **PASS.** `C2` **FIRED.**

> **THE CONTROL THAT FIRED, AND WHAT IT CAUGHT.** I asserted that `Assets ≤ 0` must be **exactly zero
> firms**, as an accounting identity. It fired: **33 of 6,428.** Diagnosis: **`Assets` strictly
> negative is 0 of 6,428 — the identity holds — and the 33 are filers reporting total assets of
> EXACTLY ZERO**, all dormant or shell entities by name (`CHINA CHANGJIANG MINING & NEW ENERGY`,
> `CONECTISYS CORPORATION`, `LVPAI GROUP LIMITED`, `Eline Entertainment Group`, `ATLANTICA, INC.`,
> `NEURALBASE AI LTD.`). Two of them also report GrossProfit, both zero: **GP/AT = 0/0.** The firing
> taught a distinction I had not drawn: **a deflator that cannot go negative can still go to zero,
> and a zero denominator is a different failure from a negative one — undefined rather than extreme.
> No percentile rule creates it and no percentile rule removes it; only a positivity filter does.**
> 0.51% of filers, and the case is invisible to the entire outlier literature.

**The era check, because "is it correlated with era" was asked.** Share of filers with negative
stockholders' equity: **25.4% (CY2011Q4I, n 7,928) · 24.7% (CY2015) · 24.6% (CY2019) · 21.7% (CY2023)
· 19.5% (CY2025, n 5,743)**. Stable and slightly **declining** — not an era effect.

**The caveat, stated plainly and before anyone asks.** The SEC frames universe is **all XBRL filers**,
which includes shells, blank-check vehicles, funds and unlisted registrants. The negative-BE
literature quotes **approximately 5% of all traded stocks** since the mid-1980s for **listed common
stocks**. These two numbers are not in conflict; they are different universes, and **the 5% is the
number that bears on a tradeable book**. My 19.5%–25.4% is an **upper bound** on the listed share and
should be read only as "the sign-flip population is not a rounding error."

> **THE STRUCTURAL POINT, WHICH IS THE CORE OF THIS LANE.** The campaign was handed three separate
> nodes: **outlier treatment (#2)**, **dropping loss-makers (#1 for profitability)** and — from round
> 2 — **the deflator**. On `GP/AT` they are three nodes. **On `OP/BE` they are ONE node**, because a
> loss-maker with negative book equity is simultaneously a loss-maker, an outlier, and a firm whose
> ratio has the wrong sign, and the only thing that removes it is the deflator's positivity
> requirement. `C2` ranked the deflator as round 2's Type N discovery; it is also the switch that
> decides whether the other two nodes exist.

### 4.5 What the methods literature actually recommends: neither winsorise nor trim

**Adams, Hayunga, Mansi, Reeb & Verardi (2019)**, *Financial Management* 48(2) 345–384 —
the paper Mitton's footnote 12 points to. `[PEER-REVIEWED]` **`[abstract only]`**, verbatim:

> *"Outliers represent a fundamental challenge in the empirical finance research. **We investigate
> whether the routine techniques used in finance research to identify and treat outliers are
> appropriate for the data structures we observe in practice.** Specifically, we propose a
> multivariate identification strategy that can effectively detect outliers. We also introduce an
> estimator that minimizes the bias outliers caused in both cross-sectional and panel regressions and
> provide outlier mitigation guidance. **Using replications of four recently published studies in
> premier finance journals, we show how adjusting for multivariate outliers can lead to significantly
> different results.**"*

Its own keywords are *"outliers; univariate vs multivariate identification; robust regressions;
winsorizing; trimming; bias."*

**So the only methods paper on this node argues that the branch everybody debates — 1/99 versus 5/95,
winsorise versus trim — is the wrong axis, because outliers in finance are multivariate and the
routine techniques are univariate.** That branch appears in **no** NSE grid and in **none** of
Mitton's twelve decisions. And note what it is again: a **regression** argument. I could not obtain
the body (§13.4), so I do not know whether their four replications are sorts or regressions, or what
their estimator does to a portfolio.

---

## 5. DROPPING LOSS-MAKERS — #1 FOR THE PROGRAMME'S ONE COMPUTABLE FAMILY

### 5.1 Who drops them, who does not, and what they say

- **About one paper in six drops them**: 16.7% (WWW 56-paper sample) and 18.2% (109-paper sample).
  **Soebhag et al. do not have the node at all** — their eleven choices include negative *book
  equity* but not negative *earnings*.
- **Hou, Xue & Zhang do not drop loss-makers** and do not mention them; they drop negative book
  equity in a clause.
- **Fama and French drop them for E/P-type ratios, unconditionally and by construction**, and say so
  in the primary data documentation: *"Portfolios: Earnings < 0; bottom 30%, middle 40%, top 30%;
  quintiles; deciles. **Firms with negative earnings are in only the Earnings < 0 portfolio.**"* The
  deciles are formed on positive-E/P firms with NYSE breakpoints.
- **The same convention is hard-coded in WWW's code, below the node layer.** `sv_em = if_else(ib >= 0,
  ib / mktcap, NA_real_)` — earnings-to-price is simply **undefined** for loss-makers, regardless of
  which branch of the `drop_earnings` node is taken. And `sv_tbi = if_else(pi < 0 | ni < 0, NA_real_,
  pi / ni)` — the taxable-income-to-book-income ratio is dropped when **either** is negative, with no
  comment, because the ratio of two negatives is positive and meaningless. **The sign-flip mechanism
  of §4.4 is handled in the code of the paper whose node list does not contain it.**
- **The node, when it is a node, is a universe filter not a variable filter.** WWW's
  `21_portfolio_sorts_cluster.R`: `if(drop_earnings) { ... filter(filter_earnings > 0) }`, where
  `filter_earnings = ib` (income before extraordinary items). It removes the firms from the whole
  sample before breakpoints are computed.

**The stated reason, where one exists, is an economic claim about meaning — "a loss-maker's
profitability ratio is not meaningful" — and it is never written down as such.** The closest thing to
an argument in this corpus is Soebhag et al. on the sibling node: *"Firms with negative book equity
value might have particularly high default risk, and the relation between default risk and leverage
is different for financial firms than for other firms (Fama and French (1992))."* That is a **distress
claim**, not a measurement claim, and it is contested (§9.3).

### 5.2 What the branch is worth, from the authors' own output tables

`Paper_Tables/E05_NSE_nodes_drop_earnings.tex`, read from the repository.
`[WORKING PAPER]` `[read in full as the authors' own output]`. Mean premium in %/month across all
methodological paths; `Sig.` is the share of paths with a significant premium; `Mon.` the share that
are monotone.

| sorting-variable group | loss-makers **INCLUDED** mean / Sig. / Mon. | loss-makers **EXCLUDED** | Δ mean | Δ mean, % |
|---|---|---|---|---|
| Financing | 0.35 / 0.76 / 0.48 | 0.27 / 0.70 / 0.48 | −0.08 | −23% |
| Intangibles | 0.24 / 0.36 / 0.32 | 0.20 / 0.32 / 0.37 | −0.04 | −17% |
| Investment | 0.42 / 0.96 / 0.60 | 0.40 / 0.96 / 0.79 | −0.02 | −5% |
| Momentum | 0.49 / 0.82 / 0.70 | 0.44 / 0.79 / 0.70 | −0.05 | −10% |
| **PROFITABILITY** | **0.27 / 0.43 / 0.41** | **0.18 / 0.35 / 0.37** | **−0.09** | **−33%** |
| Size | 0.09 / 0.07 / 0.10 | 0.09 / 0.10 / 0.20 | 0.00 | 0% |
| Trading frictions | 0.16 / 0.14 / 0.13 | 0.13 / 0.16 / 0.14 | −0.03 | −19% |
| Valuation | 0.30 / 0.36 / 0.53 | 0.24 / 0.31 / 0.49 | −0.06 | −20% |

**Profitability is the worst-hit family, by proportion, of all eight** — a 33% fall in the measured
premium and an 8-point fall in the share of constructions that reach significance. That is why it
ranks **#1 by MAD for the profitability cluster (1.24)** while ranking 3rd overall (0.94).

**And for context, here is what the OTHER profitability-cluster nodes do to the branch mean** — read
from `E04`, `E06`, `E10`, `E11`, `E14` in the same folder. This table has not been carried anywhere in
the campaign and it is the single most decision-relevant table in the lane:

| node, profitability cluster | branch A | branch B | Δ mean | Δ Sig. | Δ Mon. |
|---|---|---|---|---|---|
| **negative earnings** | included **0.27** / .43 / .41 | excluded **0.18** / .35 / .37 | **−0.09** | **−0.08** | −0.04 |
| quantile count | 5: 0.20 / .37 / **.39** | 10: 0.25 / .41 / **.30** | +0.05 | +0.04 | **−0.09** |
| sorting method | dep 0.22/.42 · indep 0.23/.41 | single 0.22/**.30** | ~0 | −0.12 (single) | ~0 |
| stock age | none 0.23 / .39 / .38 | ≥2y 0.22 / .40 / .40 | −0.01 | +0.01 | +0.02 |
| negative book equity | incl 0.22 / .39 / .39 | excl 0.23 / .39 / .39 | +0.01 | 0.00 | 0.00 |
| weighting | EW 0.23 / **.41** / .37 | VW 0.22 / **.38** / .41 | −0.01 | −0.03 | +0.04 |
| formation time | FF-June 0.16 / .27 / .29 | monthly 0.18 / .30 / .32 | +0.02 | +0.03 | +0.03 |

> **For a profitability sort, the ONLY node with a large branch-level effect on the premium is the
> loss-maker drop.** Weighting, stock age, negative book equity and sort dependence each move the
> mean by **0.01 %/month or less**. Deciles over quintiles buys +0.05 and costs 0.09 of monotonicity.
> **Equal-weighting is the slightly BETTER branch here (Sig. 0.41 vs 0.38), which is the opposite of
> the usual presumption that equal-weighted results are a microcap artefact** — for this family, on
> this grid, on a spread.

### 5.3 `[MEASURED IN BRIEF]` HOW LARGE IS THE AFFECTED SUBSET, AND WHAT DOES IT EARN

**Endpoint:** French's `Portfolios_Formed_on_E-P_CSV.zip`, vintage `202607`, 195107–202607, 901
monthly observations. French reports the loss-makers as their own portfolio **with firm counts and
average firm size**, so the dropped set is directly observable rather than inferred.

| | 1951-07 .. 2026-07 (n = 901) | 2010-01 .. 2026-06 (n = 198) |
|---|---|---|
| **loss-makers as a share of all sorted firms** | mean **21.30%**, min 0.22%, max 48.17% | mean **37.36%**, min 25.75%, max 48.17% |
| average firm size, loss-makers | $527 m | $1,736 m |
| average firm size, lowest E/P decile | $4,383 m | $15,410 m |
| average firm size, highest E/P decile | $1,364 m | $4,105 m |

- **The subset is enormous and era-dependent: a fifth of the cross-section over the full history and
  over a THIRD in the programme's window.** It ranges from 0.22% (early 1950s) to 48.17%. A node that
  "drops the loss-makers" drops **more than one name in three** in recent data.
- **It is strongly size-tilted.** Loss-makers average roughly **one eighth** the average firm size of
  the lowest positive-E/P decile, in both windows. (`Average Firm Size` is a mean and is dominated by
  its own right tail; this is a tilt, not a distribution.)

**And what the dropped set earns, which is the part nobody expected:**

| | EW mean / `t` | VW mean / `t` |
|---|---|---|
| **full sample** | | |
| loss-makers (`<= 0`) | **+1.229 / +4.63** | +1.122 / +4.70 |
| lowest positive-E/P decile | +0.967 / +4.69 | +0.981 / +5.32 |
| highest E/P decile (the long leg) | +1.570 / +7.98 | +1.348 / +7.68 |
| **2010-01 .. 2026-06** | | |
| loss-makers | +0.782 / +1.50 | **+1.575 / +3.51** |
| lowest positive-E/P decile | +1.084 / +2.87 | +1.508 / +3.83 |
| highest E/P decile | +1.217 / +2.49 | +1.027 / +2.62 |

**Over the full 75 years the dropped set OUTPERFORMED the lowest positive-E/P decile by 26 bp/month
equal-weighted, and in 2010–2026 value-weighted it was the best-performing of the three** — ahead of
the long leg. **The set the convention discards is not a pile of losers.** (This is a *pooled* bucket
of every loss-maker, not a sorted portfolio; it is a fact about the excluded population, not a
strategy.)

### 5.4 It is a SHORT-LEG node, and in this construction the long leg is untouched to the last decimal

Reconstructing a bottom leg that **keeps** the loss-makers, by firm-count weights for the
equal-weighted case and count × average-size weights for the value-weighted case:

| | bottom leg, dropped | bottom leg, kept | **LONG LEG, both branches** | spread, dropped | spread, kept | **node's effect on the SPREAD** | **on the LONG LEG** |
|---|---|---|---|---|---|---|---|
| full, EW | +0.967 (`t` 4.69) | +1.039 (`t` 4.37) | **+1.570 (`t` 7.98)** | +0.603 (`t` 6.06) | +0.531 (`t` 4.67) | **−0.073** | **0.000** |
| full, VW | +0.981 (5.32) | +0.948 (5.10) | **+1.348 (7.68)** | +0.367 (2.58) | +0.400 (2.96) | **+0.033** | **0.000** |
| prog, EW | +1.084 (2.87) | +0.822 (1.68) | **+1.217 (2.49)** | +0.133 (0.58) | +0.395 (1.52) | **+0.262** | **0.000** |
| prog, VW | +1.508 (3.83) | +1.470 (3.72) | **+1.027 (2.62)** | −0.482 (−1.44) | −0.443 (−1.53) | **+0.039** | **0.000** |

**The zero is not an estimate; it is a property of the construction.** French's deciles are formed on
positive-E/P firms with NYSE breakpoints and the loss-makers occupy a separate bucket, so whether you
report that bucket or not cannot change `Hi 10` at all. **The #1-ranked node for the programme's one
computable family operates entirely through the leg the programme cannot trade.**

> **Negative control NC5 FIRED and it calibrated the reconstruction.** I asserted that the
> firm-count-weighted average of EW deciles 1–3 must reproduce French's published EW `Lo 30` to
> within 0.02 pp/month. It fired at **max |diff| = 0.0243 pp**. Diagnosis over 901 months:
> **mean |diff| 0.0040 pp, median 0.0033, p95 0.0112, max 0.0243.** French publishes returns and
> counts rounded to two decimals, so an error of this order is arithmetic rounding, not a logic
> error; the tolerance I pre-set was too tight by 0.005 pp. **The calibration taken from the firing:
> the reconstruction is accurate to about ±0.024 pp/month, three to ten times smaller than every
> effect in the table above.** A control that fires and then bounds the thing it was guarding is
> worth more than one that passes.

---

## 6. THE REMAINING NODES

### 6.1 Quantile count — the #1 node, and the only one with a derived optimum

**Cattaneo, Crump, Farrell & Schaumburg**, *REStat* 102(3) 2020, 531–551. `[PEER-REVIEWED]`
`[read in full]`. They cast a portfolio sort as a **nonparametric estimator** in which the number of
portfolios is the tuning parameter, and derive an MSE-optimal choice. Verbatim:

- *"In both empirical applications, we find that the optimal number of portfolios varies
  substantially over time and is **much larger than the standard choice of ten** routinely used in the
  empirical finance literature and, more important, that **substantive conclusions change with the
  number of portfolios chosen** for analysis."*
- Size: *"the optimal number of portfolios can be as small as about **50** in the 1920s and can rise
  to **above 200** in the late 1990s"*; elsewhere *"approximately **250** in the largest cross section
  and around **50** in the smallest."* Momentum: *"about **10** in the 1920s and about **50** in the
  late 1990s"*, with a maximum around **55**.
- Scale: *"in our data, **n ranges from 500 to nearly 8,000** … and the optimal choice of `J_t`, for
  example, **varies from 13 to 52** for the momentum anomaly."*
- **And the two different optima, which is the finding.** For **testing** `H₀: μ(z_H) − μ(z_L) = 0`,
  `J_t = K·n_t^{1/2}·T^{1/4}`. *"Turning to **factor construction**, we find a different choice of `J`
  will be optimal, `J_t = K·n_t^{1/3}·T^{1/3}` … The major difference here is that **for point
  estimation, the optimal number of portfolios diverges more slowly than for hypothesis testing** …
  This formal choice is a further contribution of our paper and is new to the literature. However, it
  does seem that at least informally, **the status quo is to use fewer portfolios for factor
  construction than for testing.**"*
- They also separate the legs when the question demands it: *"We found that the **"short" side** of
  the momentum spread trade has become more profitable in later subperiods."*

`[MEASURED IN BRIEF — arithmetic on CCFS's published rates only]` the ratio of the two optima scales
as `n^{1/6}·T^{−1/12}`; at `n ≈ 1,500` and `T ≈ 200` that is **≈ 2.2×**, before the unknown constants
`K`, which differ between the two problems and which I cannot evaluate. **Directional only.**

**`[MEASURED IN BRIEF]` and the data agree with the direction.** French's OP portfolios, same months,
same sort, only the bucket count changing:

| window / weight | tercile 30/70 | quintile 20/80 | decile 10/90 |
|---|---|---|---|
| full, EW — **LONG LEG** | **+0.856 (`t` 4.11)** | +0.841 (`t` 3.91) | +0.830 (`t` **3.71**) |
| full, EW — SPREAD | +0.079 (0.74) | +0.083 (0.68) | **+0.113** (0.75) |
| full, VW — **LONG LEG** | **+0.701 (4.35)** | +0.687 (4.22) | +0.693 (**4.12**) |
| full, VW — SPREAD | **+0.224 (2.37)** | +0.201 (1.74) | +0.246 (1.57) |
| prog, EW — **LONG LEG** | **+0.971 (2.46)** | +0.937 (2.33) | +0.888 (**2.13**) |
| prog, EW — SPREAD | +0.215 (0.98) | +0.245 (0.92) | **+0.356** (1.08) |
| prog, VW — LONG LEG | +1.179 (3.92) | +1.134 (3.77) | **+1.242 (3.99)** |
| prog, VW — SPREAD | +0.194 (1.03) | +0.099 (0.40) | **+0.308** (0.93) |

**The signs oppose in three of the four cells: going finer raises the spread's mean and lowers the
long leg's.** For the equal-weighted long leg the `t` falls **monotonically** in both windows —
**4.11 → 3.91 → 3.71** and **2.46 → 2.33 → 2.13**. The magnitudes are small (|Δmean| ≤ 0.14
pp/month) and **I did not test the difference for significance**; the claim is a consistent direction,
not a measured effect. This reproduces `C2`'s §5.2 grid to the third decimal from an independent
script, which is worth saying.

**Against this, the stated mechanism for the other direction.** Soebhag et al.: *"Intuitively, if
expected returns are monotonically related to a given stock characteristic, then taking positions in
stocks with more extreme characteristics would naturally result into higher returns and Sharpe
ratios."* And their own counter-argument, in the set-3 discussion: *"Not selecting 20-80 breakpoints
could be defended as such breakpoints **reduce portfolio breadth** and could tilt towards stocks with
more exposure towards a certain factor, potentially biasing the portfolio returns upward."*
**Breadth versus extremity — and breadth is the quantity this programme has the least of.**

**The overall grid number, for completeness.** WWW across all 68 SVs: deciles mean **0.31**, NSE 0.21,
Sig. 0.51, **Mon. 0.33**; quintiles mean **0.25**, NSE 0.16, Sig. 0.50, **Mon. 0.45**. **The
#1-ranked node moves the point estimate by 24% and the significance rate by one percentage point**,
because the standard error scales with it. It is a **scaling** node for a spread, not an inference
node — which makes CCFS's construction-versus-testing distinction the substantive question rather
than the significance rate.

### 6.2 Sort dependence, and the only clean Type U node in the list

Soebhag et al. `[read in full]`: *"Independent sorting is the most commonly used sorting procedure
deployed in the literature. **A major drawback is that independent sorting may result in sparse
portfolios, with the consequence that a factor portfolio is not well-diversified.** In some cases
independent sorting [produces empty portfolios in some] samples (Ang et al. (2006), Novy-Marx (2013),
Wahal and Yavuz (2013)). … **However, implementing a dependent sorting procedure raises the question
of what order of sorting should be used.**"* (The bracketed words are mine where the PDF line wrapped;
the citation list is verbatim.)

So: **dependent-versus-independent is justified, with a named failure mode (sparse or empty
portfolios) and three citations. The ORDER of a multi-way dependent sort is raised and not resolved
anywhere I read — the one clean Type U node.** Magnitudes: WWW MAD 0.69 (all) / 0.73 (profitability);
branch means essentially identical (dependent 0.28, independent 0.28, single 0.28 overall; 0.22 /
0.23 / 0.22 for profitability) but **single sorts have a materially lower significant-path share for
profitability: 0.30 against 0.42 and 0.41.** Soebhag: *"The Sharpe ratios for independent and
dependent sorts are approximately similar."*

### 6.3 Rebalancing frequency — and a sub-node that is not in anybody's grid

**What the grids measure.** WWW's node is named *"Rebalancing"* in the paper's table but is coded as
`formation_time = c("monthly", "FF")` — **monthly re-formation versus Fama-French June formation.**
That conflates a *frequency* change with a *date-convention* change, so **Hasler's finding that the
June convention carries a momentum exposure (`C2` §4) sits inside this node, unseparated.** The
magnitudes: MAD 0.59 (all) / 0.59 (profitability). Branch means, all SVs: FF-June 0.26 (NSE 0.14,
Sig. 0.51), monthly 0.27 (NSE 0.17, Sig. 0.49). Profitability: **FF-June 0.16 (Sig. 0.27, Mon. 0.29)
versus monthly 0.18 (Sig. 0.30, Mon. 0.32)** — monthly re-formation is the slightly better branch on
all three statistics, before costs.

**What changed between Soebhag's draft and publication.** The 2022 draft's eleven choices contain no
rebalancing node at all. **The published *JEF* abstract names it:** *"Other important design choices
relate to excluding microcaps, industry-adjusting, and **the rebalancing frequency**, which highlights
the need for researchers to clearly describe and motivate these choices."* `[snippet only —
third-party reproduction of the published abstract; the published article was not opened]` **A node
was added in revision and promoted to the abstract.**

**And the sub-node nobody has named: within-period weight management.** Shin, arXiv 2606.19550v1
(17 June 2026) `[WORKING PAPER]` `[abstract read in full; construction sections read in the passages
quoted]` varies *"stock selection, initial weighting, holding, and rebalancing"* on
**characteristic-unsorted random portfolios** and reports that *"**buy-and-hold favors FF5 and FF6,
whereas daily constant-weighting favors FF3**, the most stable model across designs"* and that
*"changing the holding or rebalancing rule changes the return process"* because *"**the weight path
itself generates a distinct tradable return process**."* Under constant-weighting *"the portfolio is
rebalanced after each trading day to restore the initial target weights."*

> **This is a construction node distinct from re-formation frequency: whether an equal-weighted book's
> weights DRIFT within a holding period or are reset to equal each bar. It changes which factor model
> wins a horse race. It appears in no NSE grid. And — see §7.3 — Shin's entire paper is conducted on
> LONG-ONLY portfolios.**

### 6.4 Stock-age filters — the majority convention, justified for a database reason

FF1993's justification is verbatim in §2.2(b): Compustat backfill survivor bias, citing Banz and
Breen (1986). Usage: **67.2% / 57.0%** of papers impose a two-year filter (WWW's two samples).
Magnitude: WWW MAD **0.43** (all) / **0.48** (profitability) — 12th of 14. Branch means, all SVs: none
0.29 (Sig. 0.52), ≥2 years 0.26 (Sig. 0.50); profitability: 0.23 (Sig. .39, Mon. .38) vs 0.22
(Sig. .40, Mon. .40).

**One conflation worth recording.** FF's rule is *age on the accounting database* — it protects
against a backfill artefact in Compustat. WWW code it as `drop_stock_age_at = 2`, a filter on the
**stock's** age. These are different objects with different failure modes: the first guards a data
artefact, the second changes the population (young listings have different return distributions).
**A programme whose panel is ~35.7% dead has a third object again — survivorship on the exit side,
which an age filter on the entry side does not touch.**

### 6.5 Level versus log — and the node whose SIGN flips between the two objects

This is the sharpest long-leg result in the lane and it comes in three pieces that agree.

**(i) Walter, Weber & Weiss computed it and did not report it in the paper's headline.** Their code
carries `log_premium = log(1 + ret[max]) - log(1 + ret[min])` alongside the arithmetic premium, and their
Internet-Appendix tables report the whole grid both ways. Comparing
`Paper_Tables/02i_NSE_acrosssvs_overall.tex` with
`Paper_Tables/IA18i_NSE_log_acrosssvs_overall.tex`, all 68 SVs, 69,120 paths:

| | mean | NSE | NSE_w | Ratio | Skew | Kurt | Pos. | **Sig.** |
|---|---|---|---|---|---|---|---|---|
| **arithmetic (level)** | 0.28 | 0.19 | 0.27 | 1.10 | 0.75 | 4.26 | 0.90 | **0.50** |
| **LOG** | **0.32** | 0.20 | 0.28 | 1.14 | 0.74 | 4.06 | 0.91 | **0.56** |
| level, originally significant SVs | 0.31 | 0.21 | — | — | — | — | 0.94 | 0.57 |
| **log**, originally significant SVs | **0.36** | 0.22 | — | — | — | — | 0.95 | **0.63** |

**Switching the return convention raises the mean premium by 14% and raises the share of
constructions that reach significance from 50% to 56%, across the entire grid.** That is a six-point
gain in significance from a measurement convention, on 69,120 paths, holding every other node fixed.

**(ii) The mechanism is Jensen's inequality and it predicts a SIGN.**
`E[log(1+r)] ≈ E[r] − ½σ²`. For a spread, the two halves subtract:
`Δ ≈ ½(σ²_Lo − σ²_Hi)`. The low-profitability leg is the more volatile one, so the log convention
**rewards** a spread. A long leg has no second leg whose variance can cancel, so the log convention
**subtracts half its own variance** and **penalises** it.

**(iii) `[MEASURED IN BRIEF]` the prediction, computed and confirmed in four of four cells.**

| window / weight | **LONG LEG** level → log | **SPREAD** level → log | **predicted `½(σ²_Lo − σ²_Hi)`** | error |
|---|---|---|---|---|
| full, EW | +0.833 (`t` 3.73) → +0.639 (`t` **2.84**) = **−0.194** | +0.131 (0.86) → +0.242 (**1.66**) = **+0.112** | **+0.121** | 0.009 |
| full, VW | +0.691 (4.11) → +0.581 (3.45) = **−0.110** | +0.252 (1.61) → +0.364 (**2.30**) = **+0.112** | **+0.111** | 0.001 |
| prog, EW | +0.888 (2.13) → +0.713 (1.70) = **−0.176** | +0.356 (1.08) → +0.463 (1.42) = **+0.107** | **+0.113** | 0.006 |
| prog, VW | +1.242 (3.99) → +1.139 (3.69) = **−0.103** | +0.308 (0.93) → +0.431 (1.30) = **+0.123** | **+0.127** | 0.004 |

> **The node's sign is OPPOSITE on the two objects, in every cell, and the spread's shift matches a
> closed-form prediction to within 0.009 pp/month. And it is decisive at the margin: the
> value-weighted OP spread goes from `t` = 1.61 to `t` = 2.30 — from insignificant to significant over
> 1963–2026 — on the choice between arithmetic and log returns alone, with no other change.**
> Mitton's regression |Δ*t*| for this node is 1.37 / 1.10 (leverage) and 8.01 (quasi-random); `C2`
> carried Menkveld's Jensen-inequality refractor. **This is the same effect, measured on a sort, with
> its sign, on both objects, for the first time in this campaign.**

### 6.6 Data vintage and dividend-reinvestment timing — the node that is not a choice

`C2` read **Schwarz, Walter & Weiss** in abstract and introduction and listed the body and the 46-page
Internet Appendix as unopened. **The published JFQA version is open access and is now read in full.**
`[PEER-REVIEWED]` `[read in full]`, 4,943 extracted lines.

- The headline, verbatim: *"This transition rewrites **9.62%** of monthly returns by more than one
  basis point, primarily due to a change in the dividend reinvestment assumption … on average,
  **11.43%** of all monthly long-short returns differ by more than 10 basis points — especially in
  early periods, NBER recessions, and return-based sorts. **Reassuringly, average premia and their
  significance remain largely unaffected**, suggesting CRSP changes mainly introduce unsystematic
  variation without altering key asset pricing conclusions."*
- **New from the body: 45.78% of all monthly long-short returns differ by more than 1 bp**, and the
  per-family split — *"We find the largest share … for **momentum** variables and their methodological
  paths (**14.58%**). In contrast, we find the lowest share for **profitability**-related variables, as
  **8.97%** of their monthly long-short portfolio returns differ by at least 10 bp."* And *"the share
  of long-short returns that differ by at least 10 bp … is **at least 5.6% for all sorting variables
  separately**."*
- **And the attribution, which nobody has carried:** *"around **72% (48%)** of the differences in
  monthly portfolio returns exceeding 1 bp (10 bp) … are driven by altering the **reinvestment
  assumption** from the old to the new CRSP tape"* — as opposed to trading gaps, IPO months, or
  delistings. Of the underlying stock-return differences, **97.7%** come from the reinvestment change.
- The mechanism, quoted by them from CRSP: the legacy tape computed a month-to-month holding-period
  return with dividends reinvested at **month-end**; the new tape computes a compound **daily** return
  with dividends reinvested on their **ex-dates**.

**So the good news for a profitability programme is that profitability sorts are the family LEAST
disturbed by the largest data-vintage event in the field's history — 8.97% of monthly long-short
returns moving by more than 10 bp, against 14.58% for momentum.** The bad news is unchanged: this is
not a choice any pre-registration can close.

> **An integrity note on my own extraction.** `pdftotext -layout` shifted the `N10 bp` column of the
> paper's Table 2 by one row, because the Momentum cell wrapped. Read naively, the table appears to
> assign **14.58%** to Profitability and **8.97%** to Size. **I caught it by reading the paper's prose
> against its own table**, which states momentum largest and profitability lowest, and which
> reconciles the displaced values exactly — including the `11.43%` that also appears in the abstract.
> The numbers above are the corrected reading. This is the table-extraction hazard, caught the only
> way it can be caught.

### 6.7 Breakpoint exchanges and size exclusion — not on the brief's list, but they dominate

Included because they turn out to be the largest-magnitude nodes in two of the three rankings and
because they act on the long leg's **composition**, which is the lane's subject.

- **Soebhag: *"Using NAN breakpoints instead of NYSE breakpoints improves Sharpe ratios from 0.55 to
  0.73, which is the largest increase within our set of choices."*** (Draft. The published abstract
  says **0.46 to 0.63** — §10.2.) Including microcaps: 0.59 → 0.68. **Equal- versus value-weighting:
  0.71 versus 0.57.**
- **WWW branch means, all SVs:** all-exchange breakpoints 0.31 (Sig. 0.53) vs NYSE 0.25 (Sig. 0.48);
  no size filter 0.33 (Sig. 0.57) vs NYSE-20% 0.25 (Sig. 0.45); EW 0.30 (Sig. 0.56) vs VW 0.26
  (Sig. 0.45).
- **And the long-leg composition effect, measured by HXZ and reported in composition rather than
  return:** *"in the value versus growth category, **the high decile assigns on average 7.4% to
  microcaps** under [NYSE breakpoints and value weighting] **but 64.2%** under [all-exchange
  breakpoints and equal weighting]."* For momentum's low decile, 8% versus 63.9%.
- Context for a `$5`-floored universe: HXZ report that at end-2016 the **NYSE 20th percentile of
  market equity was $724 million** and the NYSE median **$2.6 billion**; microcaps were 2.5% of
  aggregate market cap in 1967, peaked at **6.2% in 1984**, and were **1.6% in 2016**, while being
  **60.7%** of the number of stocks.

> **This is the one node in the corpus whose effect on a LONG LEG is actually published, and it is
> published as composition, not return: the breakpoint × weighting pair moves the long leg from 7%
> microcaps to 64% microcaps.** A dollar-volume screen and a price floor are not the same instrument
> as a breakpoint choice — they bound the tradeable set, they do not bound the *weight* the long leg
> puts on the bottom of it.

---

## 7. THE LONG LEG: THE FOURTH INSTANCE, AND WHY IT IS STRONGER THAN SILENCE

### 7.1 The reference implementation computes the leg and discards it on the next line

`01_replication_code/21_portfolio_sorts_cluster.R`, lines 357–371, read from the repository:

```r
  # Compute premium
  data_premium <- data |>
    ...
    summarize(premium     = ret[portfolio == max(portfolio)] - ret[portfolio == min(portfolio)],
              log_premium = log(1 + ret[portfolio == max(portfolio)]) - log(1 + ret[portfolio == min(portfolio)]),
    ...
  # Save premium
  saveRDS(data_premium |> select(month, premium), ...)
```

`ret[portfolio == max(portfolio)]` **is** the long leg. It exists inside one expression, is
differenced against the short leg in the same statement, and the saved object is
`select(month, premium)`. **The leg is available, free, and deliberately not retained**, for all
69,120 paths and all 68 sorting variables. A census of absence can be an oversight; **this is a
design decision visible in four lines of code.**

### 7.2 Soebhag et al. go one step further: they define the leg, compute it, and sum it away

*"The turnover of the long leg of a factor is then defined as: `TO_long,i,t = Σ|W_i,t − W_i,t−1,end|`
… The turnover of the short-leg is defined in a similar way. **The turnover of the long-short factor
is defined as the sum of both the long and the short portfolios.**"* Their only other use of the
phrase is the industry illustration in §3.1. **Long-leg turnover is computed and then aggregated
before anything is reported.**

### 7.3 The censuses — and the two genuine counterexamples

| document | "long leg" | "short leg" | "long-only" | "outlier" | "winsor" |
|---|---|---|---|---|---|
| WWW Internet Appendix, `NSE_PortfolioSorts_InternetAppendix.pdf` | **0** | **0** | **0** | **0** | 1 |
| WWW Internet Appendix, `NSE_InternetAppendix.pdf` ("Methodological uncertainty") | **0** | **0** | **0** | **0** | 4 |
| WWW Internet Appendix, `NSE_InternetAppendix_20231108.pdf` | **0** | **0** | **0** | **0** | 0 |
| Soebhag et al., FoFI 2022 draft, full text | 2 (§7.2) | 1 (§7.2) | **0** | **0** | **0** |
| **Schwarz, Walter & Weiss, published JFQA text, in full** | **0** | **0** | **0** | — | — |

`[MEASURED IN BRIEF — text census of locally extracted PDFs]`. This reproduces `C2`'s census
independently and extends it to two documents `C2` did not have, **and adds that "outlier" appears
zero times in all three of WWW's appendices.**

**The two counterexamples, and they change the answer.**

1. **CCFS (2020)** derive a *different* optimal quantile count for **factor construction** than for
   **hypothesis testing**, and state that the construction optimum is smaller (§6.1). That is exactly
   the long-leg/spread distinction, formalised, in a peer-reviewed econometrics paper — and it is the
   single most useful thing this lane found.
2. **Shin (2026)** studies construction dependence on portfolios that are **entirely long-only** —
   *"All portfolios are long-only, and the initial weights sum to one"* — and states the limitation
   honestly: *"The analysis is limited to long-only portfolios of U.S. common stocks. Whether the same
   construction dependence appears in international markets, other asset classes, **short-enabled
   portfolios**, or settings with realistic trading frictions remains open."* **A 2026 construction
   paper whose default object is long-only and whose open question is the short-enabled case — the
   exact inversion of the field's habit.**

> **THE HONEST VERDICT ON THE BAR.** The **non-standard-errors literature proper** is spread-only, and
> not by omission: the leg is computed and discarded (WWW), or computed and aggregated (Soebhag), or
> absent from a full published text (Schwarz). **That is round 3's organising fact for the fourth
> time, established at the level of the reference implementation rather than a word count.** But the
> adjacent literatures are **not** silent: the econometrics of sorting says the held portfolio and the
> tested spread have different optimal constructions, and at least one 2026 paper takes long-only as
> its default. **A node ranking built on spreads does not transfer, and for two nodes I can now show
> it transfers with the OPPOSITE SIGN.**

### 7.4 Per-node long-leg verdicts, as far as the evidence goes

| node | what the spread literature says | **what happens to a LONG LEG** | how established |
|---|---|---|---|
| **Outlier treatment of the CHARACTERISTIC** | absent from every NSE grid; Mitton #2 for regressions | **EXACTLY ZERO** while `q < 1/J`; **8.9%–79.4% of the leg turns over if you TRIM instead** | `[MEASURED IN BRIEF]`, 2,612 filers, with two controls that fired as designed |
| **Outlier treatment of the RETURN** | nobody does it | |Δ`t`| up to **1.81**; the leg is **more** exposed than the spread under value weighting (1.81 vs 0.17) | `[MEASURED IN BRIEF]` |
| **Dropping loss-makers** | #1 for profitability; premium −33% | **ZERO, by construction**, in the FF convention | `[MEASURED IN BRIEF]` + `[PRIMARY DATA DOC]` |
| **Negative book equity** | smallest node of 14 (MAD 0.22) | **admits 20.5% of filers into the top region of an OP/BE sort**; 62.9% of them above the well-defined p90 | `[MEASURED IN BRIEF]`, SEC XBRL |
| **Quantile count** | #1 node; +24% on the mean | mean and `t` **fall** as the sort gets finer in 3 of 4 cells; EW `t` falls monotonically | `[MEASURED IN BRIEF]` + CCFS's derivation |
| **Level vs log of the RETURN** | +0.04 %/mo and +6pp on the significant share | **sign FLIPS**: −0.10 to −0.19 pp/mo on the leg against +0.11 to +0.12 on the spread | `[MEASURED IN BRIEF]`, prediction confirmed to 0.009 pp |
| **Level vs log of the CHARACTERISTIC** | Mitton 1.37/1.10/8.01 for regressions | **EXACTLY ZERO** | `[MEASURED IN BRIEF]`, 0 of 2,401 names |
| **Breakpoints × weighting** | largest Sharpe effect in Soebhag | **long-leg microcap weight 7.4% → 64.2%** | `[PEER-REVIEWED]` `[read in full]` (HXZ) |
| **Rebalancing / formation date** | MAD 0.59; carries a momentum exposure | **unknown**; and the within-period weight-path sub-node is unmeasured on a signal portfolio | not established |
| **Stock age** | MAD 0.43, 12th of 14 | **unknown** | not established |
| **Sort dependence and its ORDER** | MAD 0.69; Type U on the order | **unknown** | not established |
| **Data vintage** | 9.62% of monthly returns; profitability least affected | **unknown**; the tape change is firm-specific, so a long leg cannot difference it out | not established |

**Four of twelve rows say "unknown". That is the honest state of it.**

### 7.5 All eleven negative controls, and the three that fired

| control | what must be true | result |
|---|---|---|
| NC1 | winsorising at `q = 0` is an exact identity | **PASS** (max |Δ| = 0.0, 0 values altered) |
| NC2 | a rank winsorisation at 1/99 alters exactly `2·floor(0.01n) = 14` observations | **PASS** |
| NC3 | sentinel values (−99.99, −999) appear 0 times in every block used | **PASS** |
| NC4 | the long-leg series is never identical to the spread series | **FIRED** → 1 of 757 months (2018-04, `RF` equals EW `Lo 10` at the published 2 d.p.). **A rounding coincidence, not a double read**; restated as "the two series are not identical", it passes |
| NC5 | count-weighted EW deciles 1–3 reproduce published EW `Lo 30` to 0.02 pp | **FIRED** at 0.0243 pp → diagnosed as 2-d.p. rounding (mean 0.0040, median 0.0033, p95 0.0112); **calibrates the reconstruction to ±0.024 pp/month** |
| NC6 | symmetric trimming moves a symmetric series less than the real one | **PASS** (0.0018 pp vs 0.0357 pp) — the test has power |
| NC7 | months with firms in the `<= 0` bucket but a sentinel return = 0 | **PASS** |
| SEC C1 | an impossible period (`CY1890Q1I`) returns no facts | **PASS** (HTTP 404, 320 bytes, 0 facts) |
| SEC C2 | `Assets ≤ 0` is exactly zero firms | **FIRED** → 0 strictly negative, **33 exactly zero**; see §4.4. The firing produced a finding |
| SEC C3 | negative stockholders' equity is non-zero | **PASS** (1,361 of 6,265) |
| SEC C4 | the two frames are different documents | **PASS** (6,428 vs 6,265 facts; 619 CIKs in one only) |
| P1 | a non-monotone transform changes sort membership | **PASS** (559 of 2,612 move) |
| P2 | winsorising coarser than the bucket changes membership | **PASS** (520 move; 88.9% of the leg) |
| P3 | the characteristic contains genuine extremes and ties | **PASS** (max/p99 = 235.6; 52 ties) |

---

## 8. GOING PAST THE SUB-QUESTIONS — SIX THINGS THE BRIEF DID NOT ASK

### 8.1 The published grids omit the node that is #1 in the other ranking, and the omission is correct

`C2` concluded that *"every published NSE in §2 is a LOWER BOUND"* because the benchmark and the
variable definition sit outside the grid. **Outlier treatment is a third thing outside the grid, but
for a different reason: for a univariate ratio sort it would contribute exactly zero variance.** WWW's
14 nodes, Soebhag's 11, Mitton's 12 — **no grid contains an outlier node for a sort, and §3.2 shows
why that is the right design.** The lower-bound argument therefore needs splitting: the benchmark and
the deflator are **missing** nodes (real variance, unmeasured); outlier treatment of the
characteristic is a **null** node for the sort and a **large** node for anything that is not
rank-based — a composite index, a signal-weighted portfolio, a Fama-MacBeth regression, or a
breakpoint computed on a *weighted* rather than a counted quantile.

### 8.2 The node probabilities are in the code, and they make a path-probability weight available

WWW's `17_Decision_Nodes.R` carries not just the node list but a **probability per branch**, from two
literature samples, plus conditional distributions for the lag node — the machinery for a
**probability-weighted** NSE rather than an equal-weighted one (their `NSE_w` column, 0.27 against the
unweighted 0.19). **The published NSE of 0.19 is the equal-weighted-over-paths number; the
usage-weighted one is 0.27, i.e. 42% larger.** Weighting the paths by how often researchers actually
make each choice makes the dispersion **worse**, not better — because the popular branches are the
permissive ones (all-exchange breakpoints, no size filter, equal weighting, keep loss-makers). I did
not see this stated anywhere.

### 8.3 `[MEASURED IN BRIEF]` The outlier cutoff and the slot count are the SAME parameter

The boundary in §3.2 is `q < 1/J`. A quantile sort with `J` buckets has bucket width `1/J`; a
slot-based long-only book holding `N` of `M` eligible names has an effective top-bucket width `N/M`.
**So the safe winsorisation cutoff is a function of the book's concentration, and a concentrating
book crosses the boundary without anybody changing the outlier rule.** At `J = 10`, 5% is safe. At an
effective top bucket of 1.3% (say 20 slots from 1,500 eligible names), **a 1% winsorisation is still a
no-op and a 2.5% winsorisation is not.** `CLAUDE.md` already mandates trimming 1% from both tails as
a *reporting* convention; this is the *construction* side of the same number, and the two have
different boundary conditions. The programme can check its own `N/M` against any cutoff it uses.

### 8.4 The cost literature has a construction node the NSE grids do not, and the programme is a special case of it

Novy-Marx & Velikov (*RFS* 29(1) 2016) `[PEER-REVIEWED]` **`[snippet only]`**: *"Introducing a
buy/hold spread, which allows investors to continue to hold stocks that they would not actively trade
into, is the single most effective simple cost mitigation strategy."* A buy/hold spread is a
**two-threshold** membership rule — enter above one rank, exit below a looser one.

> **`FINDINGS.md` §10 records that `sel = rank < N_SLOTS` makes the slot count simultaneously the
> refill pool, so an exit on a still-selected name re-enters it. That IS a degenerate buy/hold spread
> with the two thresholds set equal. The cost literature names the node, reports it as the single most
> effective cost mitigation available, and no NSE grid contains it.** The opportunity-cost question
> `CLAUDE.md` flags as unmeasured here is the same node seen from the other side.

### 8.5 Soebhag's own recommendation is the exact inverse of a cash-funded long-only book, and they say when to ignore it

Their remedy — *"consistently use NYSE breakpoints, exclude microcaps, and employ value-weighting"* —
reduces the average non-standard error by **70%** (set 2) and **73%** (set 3), with the PEAD factor's
NSE falling from above 0.10 to about 0.02, **a 76% decline**. Note two things. First, the
justification is a **cost and liquidity** argument, not a return argument: *"Transaction costs for
microcaps are high and liquidity is low, which makes this segment of the market difficult for
investors."* Second, they pre-authorise the exception: *"researchers might have a particular interest
in smaller firms, or they might want to study a mechanism most applicable to illiquid stocks.
**Providing a clear explanation for design choices that deviate from the above recommendation in such
studies appears warranted.**"*

**And set 3 does not help.** *"Set 3 does not yield a substantial additional decline in non-standard
errors for most factors. **For some factors, the non-standard errors are even higher for set 3 than
for set 2.**"* Set 3 is the one that adds *exclude negative book equity, exclude financials, 30-70
breakpoints, June market equity* — **four Fama-French conventions which, imposed together, do not
reduce construction dispersion and sometimes increase it.** The same pattern appears in WWW's own
output: their `IA14` "fixed choices" tables give NSE **0.20** against the base **0.19**. **Fixing more
nodes is not monotonically stabilising, in two independent grids.**

### 8.6 Where the code and the paper diverge, and — this time — where they agree

Round 3 found a reference repository's code comment contradicting three second-hand restatements. I
looked for the same thing and found **three divergences and one agreement**, all worth recording:

1. **Divergence of name, not of number.** WWW's paper calls the node *"Rebalancing"*; the code calls
   it `formation_time` with branches `"monthly"` and `"FF"`. The paper's name hides that the branch
   change is simultaneously a frequency change and a date-convention change (§6.3).
2. **Divergence of coverage.** The code applies a loss-maker filter **twice**: once as the
   `drop_earnings` node, and once unconditionally inside individual sorting variables
   (`sv_em`, `sv_tbi`). **The node's measured MAD therefore understates the convention's reach**,
   because for some variables the filter is on in both branches.
3. **Divergence of emphasis.** The code carries `log_premium` beside `premium` for every path and
   reports the entire grid both ways in an Internet Appendix table; the paper's headline is the
   arithmetic number. The log grid has a **higher** significant-path share (§6.5).
4. **Agreement, stated because it is evidence too.** The appendix says *"we winsorize the
   distributions of all five sub-variables of the Z-score at the 1% and 99% quantile in each fiscal
   year"* and *"we follow Hou et al. (2020) and winsorize all variables except for dummy variables"*;
   the code's single `across(...)` call covers exactly those variables, excludes the dummies (`in2`,
   `oeneg`), and is grouped by year. **Here the code and the paper agree, and the agreement confirms
   the mechanism in §4.1.**

---

## 9. CONFLICTS, RECORDED AND NOT ADJUDICATED

### 9.1 The loss-maker node's DIRECTION: the published branch effect and my own measurement disagree in sign

- **WWW's profitability panel:** including loss-makers gives a **higher** premium (0.27 vs 0.18). So
  excluding them **narrows** the spread, which implies loss-makers **drag the bottom leg down**.
- **`[MEASURED IN BRIEF]` on French's E/P sort, full sample, equal-weighted:** including them
  **narrows** the spread by 0.073 pp/month, because the loss-maker bucket **outperformed** the lowest
  positive-E/P decile (+1.229 vs +0.967). Opposite sign. In the programme window, EW, the sign flips
  back to WWW's (+0.262).
- **Why they can both be right, and I am not adjudicating it.** (i) Different signals: WWW's
  profitability cluster sorts on profitability ratios, where loss-makers land at the bottom by
  construction; my measurement is on **E/P**, a valuation ratio, where French puts them in a separate
  bucket and **does not rank them at all**. (ii) Different operations: WWW's `drop_earnings` removes
  the firms from the **universe before breakpoints are computed**; my reconstruction merges a
  pre-existing bucket into a pre-existing decile, leaving breakpoints untouched. (iii) Different
  weights and windows: my own four cells disagree among themselves.
- **Which I would weight, and why.** For the question *"what does this node do to a profitability
  spread"*, **WWW's**, because it is measured on profitability sorting variables across 69,120 paths
  and it recomputes breakpoints. For the question *"can this node move a long leg"*, **mine**, because
  there the answer is exactly zero for a structural reason and that reason is in French's own
  documentation. **Both stay on the record.**

### 9.2 The two NSE papers' meta-analyses disagree about the majority weighting convention

WWW's code: value-weighting 43.4% (56 papers) / 45.5% (109 papers) — **equal-weighting is the
majority**. Soebhag et al., 323 articles: value-weighting **58.5%** — **value-weighting is the
majority**. Both are counts of the published literature; both are from NSE papers; neither cites the
other's count. They also disagree on NYSE breakpoints (30.7%/26.6% versus **41.5%**) and on excluding
negative book equity (27.6%/41.7% versus **22.0%**). **I would weight Soebhag's slightly, because its
sample frame is named and public (Harvey & Liu's 323-article list) whereas WWW's 56-versus-109
distinction is not documented in anything I opened. Both stay on the record.** Either way, the
programme's equal weighting is somewhere between "the majority convention" and "a 42% minority" — not
exotic.

### 9.3 Is excluding negative book equity a distress claim or a mistake?

- **For:** Soebhag et al. — *"Firms with negative book equity value might have particularly high
  default risk."* Fama & French (1993) — *"rare before 1980."* Davis, Fama & French (2000), as quoted
  in the negative-BE paper — *"it should be noted that no firms in the sample has a negative book
  value of equity. Accordingly, the treatment of negative book values is not an issue in this study."*
- **Against:** the negative-BE paper `[WORKING PAPER]` `[read in full]` — *"**We believe that the
  omission of negative BE stocks is a mistake.** Firstly, indeed, negative BE stocks were rare prior
  to 1980. However, since the mid-1980s, their numbers have gradually increased and stabilised to
  approximately **5% of all traded stocks** … these stocks inevitably exert significant influence on
  any value-based asset pricing models … However, they are **arbitrarily excluded**."* Their measured
  answer: negative-BE stocks *"do carry higher default risks"* but *"whether the higher risks are
  compensated by higher returns is conditional on firm size and book-to-market ratio."*
- **Where I would stand, and it is a third position.** Both sides are arguing about **distress**, and
  for a ratio deflated by book equity that is the wrong axis. **The operative fact is arithmetic: a
  negative denominator inverts the ratio's ordering, and 62.9% of the sign-flipped firms land above
  the well-defined top-decile cutoff** (§4.4). The filter earns its place as a **well-definedness**
  requirement whatever the distress argument resolves to. **All three positions stay on the record.**

### 9.4 The regression ranking and the sort ranking disagree on the node both measure

Exclude-financials is Mitton's **least** impactful node of twelve (|Δ*t*| 0.27 / 0.52 / 0.57) and
WWW's **7th of 14** overall (MAD 0.75), rising to **1.08 — fourth-largest — for the profitability
cluster**. **I would weight the sort ranking for a sort and the regression ranking for a regression,
and the disagreement is the point: these are not two measurements of one ordering.** Which is exactly
why importing Mitton's #2 into a sorting programme needed checking (§3.2, §4.2).

### 9.5 Does fixing nodes reduce dispersion?

Soebhag: set 2 reduces NSE by 70%; **set 3, which fixes four more, gives 73% overall but is worse than
set 2 for some factors.** WWW's own `IA14` "fixed choices" tables: NSE **0.20** versus the base
**0.19** — no reduction. `C2` recorded Jensen-Kelly-Pedersen's ladder going the other way (35% → 55.6%
replication with better construction). **Recorded. I could not determine what WWW's `IA14` fixes
without the paper's prose** (§12.1).

---

## 10. DRAFT VERSUS PUBLISHED — THREE RECORDS, AND THE HAZARD BIT TWICE MORE

The brief flagged this hazard because the paper that invented "non-standard errors" has a 9%-versus-
53.5% swing on one winsorization choice between versions (`C2` §14.1). **It bit two more central
papers in this lane.**

### 10.1 Hou, Xue & Zhang: 447 → 452 variables, and the accusation was removed

| | NBER WP 23394, May 2017 | *RFS* 33(5), 2020 |
|---|---|---|
| opening sentence of the abstract | **"The anomalies literature is infested with widespread p-hacking."** | *(absent)* |
| anomaly variables | **447** | **452** |
| insignificant at 5% under NYSE-VW | **286 (64%)** | **65%** |
| the worst category | **95 of 102 liquidity variables (93%)** | **96% of trading frictions** |
| the raised hurdle | **t > 3 → 380 (85%)** | **2.78 → 82%** |
| significant anomalies | **161**, of which the q-factor model leaves **115** alphas insignificant | *(not in the abstract)* |

**`C2` flagged HXZ's 65% / 96% / 82% as summariser-sourced and therefore weaker than
`[snippet only]`. All three are now confirmed from the published PDF's own abstract, and the draft's
different numbers are recorded beside them.** The hurdle itself changed from a round `3.00` to a
Benjamini-Hochberg-Yekutieli-derived `2.78`, and the published footnote says applying BHY directly to
their 452 anomalies *"yields |t|-cutoffs of 3.47 and 4.27"* — higher still, which *"would only
strengthen our conclusion."*

### 10.2 Soebhag et al.: the branch Sharpe ratios moved, the headline claim was withdrawn, and a NODE WAS ADDED

| | FoFI draft, August 2022 `[read in full]` | *JEF* 78 (2024) `[snippet only — third-party reproduction of the abstract]` |
|---|---|---|
| NAN vs NYSE breakpoints | Sharpe **0.55 → 0.73** | Sharpe **0.46 → 0.63** |
| the headline remedy | *"simple suggestions that **reduce the average non-standard error by 70%**"* | **absent from the abstract** |
| the important nodes named in the abstract | — | *"excluding microcaps, industry-adjusting, and **the rebalancing frequency**"* |
| construction count | *"2048 (2¹¹)"*, stated in the abstract and body | not stated in the abstract |

**A node that is not among the draft's eleven choices appears in the published abstract as one of the
most important. The 70% remedy — which `C2` carried as a headline — is not in the published
abstract.** I did not open the published article, so I cannot say whether the remedy survives in the
body; **this is recorded as a version difference, not as a withdrawal.**

### 10.3 Walter, Weber & Weiss: title, scope, sample, and three dated appendices

`C2` recorded the title change ("Non-Standard Errors in Portfolio Sorts" → "Methodological Uncertainty
in Portfolio Sorts") and the 40 → 68 sorting-variable change. **I add that the repository carries
three Internet Appendix PDFs with three different titles and sizes — 929,211 bytes ("Methodological
uncertainty in portfolio sorts"), 2,314,747 and 2,318,954 bytes (both "Non-Standard Errors in
Portfolio Sorts") — and that the winsorisation disclosure appears 4 times in the newest, once in one
of the older ones, and zero times in the other.** The disclosure of the node that outranks everything
in the other ranking was **added in revision**.

---

## 11. INTERESTED PARTIES, ON BOTH SIDES

- **Soebhag, van Vliet & Verwijmeren.** The acknowledgements thank *"seminar participants at **Robeco
  Institutional Asset Management**"* and the footnote states *"The views expressed in this paper are
  not necessarily shared by Robeco Institutional Asset Management."* The same footnote ends
  *"**Declarations of interest: none.**"* **Robeco is a commercial factor-investing manager with a
  direct interest in how factors are constructed. Recorded without accusation: the disclosure says
  none and the page names the firm twice.** Their recommendation — NYSE breakpoints, exclude
  microcaps, value-weight — is also the construction that best matches an institutional mandate.
- **Hou, Xue & Zhang** maintain `global-q.org` and `theinvestmentcapm.com`, which publish the
  q-factor model. Their paper's conclusion that most anomalies fail and that the q-factor model prices
  the survivors advances their own model. Their footnote 6 cites *"$680 Bn at the end of August 2018"*
  in smart-beta ETFs as motivation. **The construction choices they advocate (NYSE breakpoints,
  value-weighting, WLS) are also the choices that most reduce rival anomalies' measured magnitudes.**
- **Fama and French** license index and factor data and are affiliated with Dimensional Fund Advisors.
  Kenneth French's data library is the field's public good and also the reference implementation of
  their own conventions. **Noted because §2.2(d) and §5.1 lean on his documentation as a primary
  source.**
- **The negative-BE paper** argues for including a segment that commercial value managers have an
  interest in (O'Shaughnessy Asset Management's public commentary on "veiled value" makes the same
  argument; `[SALES INSTRUMENT]`, located in a search result, **not opened and not relied on**).
- **No commercial interest is apparent** in Mitton, CCFS, Walter-Weber-Weiss, Schwarz-Walter-Weiss,
  Adams et al. or Shin. Mitton thanks *"many researchers"* who shared data.
- **This lane's own interest.** The programme is equal-weighted, long-only and floored at `$5`, and
  several findings here are convenient for it (equal-weighting is the better branch for
  profitability; the price floor is near the bottom of the ranking; profitability is the family least
  disturbed by the CRSP tape change). **I flag that as a risk of motivated reading and note the
  inconvenient findings in the same breath: Soebhag's 70%-NSE-reduction remedy is the exact inverse of
  the programme's construction, and the breakpoint × weighting pair puts 64% of a long leg's weight in
  microcaps.**

---

## 12. WHAT I COULD NOT VERIFY, STATED PLAINLY

1. **What distinguishes Walter, Weber & Weiss's "56 papers" from their "109 papers".** Both
   probability sets are hard-coded in `17_Decision_Nodes.R` and they disagree materially (negative
   book equity 27.6% vs 41.7%; stock age 32.8% vs 43.0% for "no filter"; `$5` floor 8.8% vs 14.6%).
   The paper's prose would say; I did not open it.
2. **What WWW's `IA14` "fixed choices" tables fix.** They report NSE 0.20 against the base 0.19, i.e.
   no reduction, which matters for §9.5. The file names and numbers are read; their meaning is not.
3. **Whether Soebhag et al.'s published *JEF* version retains the 70% remedy in its body.** Only the
   abstract was read, and third-hand.
4. **Whether Adams et al.'s four replications are sorts or regressions, and what their robust
   estimator does to a portfolio.** Abstract only; no open-access version exists.
5. **The authorship and date of the negative-book-equity paper.** The PDF I hold, from the AUT Centre
   for Financial Research, carries a title, an abstract and a body but **no author names and no date
   on the copy I obtained**. Every quotation from it is therefore attributed to the document, not to a
   person. Its own quotations of Fama & French (1993) p.8 and Davis, Fama & French (2000) p.1583 are
   second-hand; **I verified the FF1993 passage directly against the *JFE* PDF and it matches.** I did
   **not** verify the Davis-Fama-French quotation.
6. **Whether `StockholdersEquity` in SEC XBRL is comparable to Compustat book equity.** Its own label
   is *"Stockholders' Equity Attributable to Parent"* — no minority interest, no deferred-tax or
   preferred-stock adjustments. **My 23.4% negative-BE share is therefore not the same construct as
   the literature's ~5%, on top of being a different universe.** Both caveats are stated at the
   measurement.
7. **Whether the SEC frames universe's composition explains the whole 19.5%–25.4% versus ~5% gap.**
   I could not separate listed operating companies from shells, SPACs and funds in the frames data.
   The census is an upper bound and I use it only to establish that the population is not negligible.
8. **`frames` returns last-filed values.** The programme's own notes record this and that `prevrpt`
   is a hindsight column. My SEC measurements are **cross-sectional counts**, which this does not
   invalidate, but they are **not** a point-in-time panel and nothing time-series should be built on
   them.
9. **My `t`-statistics are iid** — `mean / (sd/√n)` — with no Newey-West and no autocorrelation
   adjustment. WWW use Newey-West. Comparisons of my `t` levels against theirs are therefore not
   like-for-like; my **differences** between treatments of the same series are.
10. **The quantile-count sign opposition is a direction, not a tested effect.** Three of four cells;
    |Δmean| ≤ 0.14 pp/month; I did not compute a standard error on the difference.
11. **CCFS's `J_test / J_construct ≈ 2.2×` arithmetic ignores the two unknown constants `K`**, which
    differ between the problems. Directional only.
12. **The loss-maker reconstruction uses `Number of Firms` and `Average Firm Size` as weights.**
    Average firm size is a mean, so my value-weighted recombination is an approximation of a
    value-weighted merge, not the real thing; NC5 bounds the equal-weighted version at ±0.024
    pp/month and **does not bound the value-weighted one**.
13. **Everything in this brief is measured on public data whose vintage is `202607` (French) or
    last-filed (SEC).** `C2` established, via Akey, Robertson & Simutin, that a third of long-short
    alphas change significance on vintage alone.

---

## 13. WHAT I DID NOT OPEN

Separate from §12, and deliberately complete.

1. **Walter, Weber & Weiss's paper text** — the same gap `C2` had. I read five code files, fifteen
   result tables and all three Internet Appendices; **I never read the prose, the method section, or
   the two-step protocol.** The SSRN delivery endpoint is blocked (§14.1) and no repository, preprint
   server, institutional archive, OpenAlex location or Unpaywall record carries a PDF.
2. **Soebhag et al.'s published *JEF* 78 (2024) article**, and their Appendix C net-return analyses.
3. **Adams, Hayunga, Mansi, Reeb & Verardi's body** — the only methods paper on the #2 node. Also
   their **Mendeley data deposit** (`data.mendeley.com/datasets/95fgpmyg3d/1`), located and not
   downloaded.
4. **Schwarz, Walter & Weiss's 46-page Internet Appendix**, including Table IA.10 (the per-variable
   shares), IA.12 (the reinvestment-attribution decomposition) and IA.VI (the bootstrap design). The
   body is read; the appendix is not.
5. **Hou, Xue & Zhang's Internet Appendix**, including the ABM/Micro breakpoint supplement their
   footnote 7 describes, and their full 452-variable appendix tables beyond the definitions I grepped.
6. **Jensen, Kelly & Pedersen's Internet Appendix Section I** — the per-node decomposition of the
   35% → 55.6% replication ladder. `C2` called it *"the single most valuable unopened document in this
   lane"*; it remains unopened, on Wiley, and absent from `bkelly-lab/ReplicationCrisis`. **I did not
   attempt it.** I also did not open the **JKP global factor data documentation or code**, which would
   show whether they winsorise characteristics.
7. **Cattaneo, Crump, Farrell & Schaumburg's supplemental appendix** (their Figure A1, the
   cross-sectional sample sizes, and the plug-in constants `K`), and the **NY Fed Staff Report 788**
   version, which is on disk and unread.
8. **Shin (2026) beyond the abstract and the construction/rebalancing passages** — its tables, its
   pricing-error results, and its appendix.
9. **Fama & French (2008), "Dissecting Anomalies"** — the source of the 3%/60% microcap figures that
   HXZ and Soebhag both cite second-hand. **Located, not opened.** Also **Fama & French (1992)**,
   cited by Soebhag as the authority for excluding negative book equity and for June size
   breakpoints.
10. **Novy-Marx (2013), "The Other Side of Value"** — three attempts, all returning the author's
    faculty landing page at HTTP 200 (§14.2). The gross-profitability construction's own outlier and
    negative-value treatment is therefore **unread**, which is a real gap for this programme's family.
11. **Novy-Marx & Velikov (2016)** beyond one quoted sentence; and **Chen & Velikov** on net anomaly
    returns, not located in this lane.
12. **"Methodological ESG uncertainty in portfolio sorts"** (*Research in International Business and
    Finance*, 2025) — a direct follow-on to WWW that may add nodes. Located in a search result, not
    opened.
13. **The IRFA paper at `d-nb.info/1259731723/34`** that surfaced in the first Mitton search and may
    be a further NSE application. Located, not opened.
14. **Patton & Timmermann on monotonicity tests**, cited by CCFS as prior work on the shape of a sort
    — directly relevant to the monotonicity column in WWW's tables. Located via citation, not opened.
15. **Bessembinder, Chen, Choi & Wei, "How Should Investors' Long-Term Returns be Measured?"**
    (SSRN 4528681) — surfaced while searching for the CRSP paper, squarely on the level-versus-log and
    compounding node of §6.5. **Located and not opened, and it is the single most relevant unopened
    document in this lane.**
16. **Mitton (2022b), "Economic Significance in Corporate Finance"** — downloaded to disk
    (571,745 bytes, HTTP 200, `application/pdf`) and **not read**. It is the companion paper on
    magnitudes rather than `t`-statistics.
17. **Menkveld et al.'s Internet Appendix and the Tinbergen discussion-paper version** — `C2`'s gaps,
    not closed here.
18. **Del Giudice & Gangestad's simulated worked example** — `C2`'s gap, not closed.
19. **CRSP's own documentation of the tape change**, quoted second-hand through Schwarz et al.

---

## 14. BLOCKS, BY TOOL AND RESPONSE

Per the standing rule: the tool and the response, never the host.

1. **`curl` → `https://papers.ssrn.com/sol3/Delivery.cfm/SSRN_ID5074864_code1234.pdf?abstractid=5074864`**
   → **HTTP 403**, `text/html; charset=UTF-8`, **5,741 bytes**. The same Cloudflare interstitial `C2`
   recorded. **Workaround that succeeded:** the **publisher's own open-access PDF** at JFQA,
   HTTP 200, `application/pdf`, **1,470,535 bytes**, 4,943 extracted lines — the full published
   version, which `C2` had only in abstract and introduction.
2. **`curl` → `http://rnm.simon.rochester.edu/research/OSoV.pdf`** and
   **`https://rnm.simon.rochester.edu/research/OSoV.pdf`** → **HTTP 200, `text/html; charset=UTF-8`,
   19,490 bytes both times**, body beginning
   `<!DOCTYPE html>…<title>Robert Novy-Marx | Simon Business School</title>`. **A `.pdf` URL served
   as `text/html` — wrong-200 flavour eleven — but a new variant of it: not a consent page, a
   FACULTY LANDING PAGE.** The host appears to rewrite unknown paths under the faculty directory to
   the author's bio at 200. Caught by reading the first 400 bytes. **No workaround found; Novy-Marx
   (2013) is unread (§13.10).**
3. **`curl` → `https://global-q.org/uploads/1/2/2/6/122679606/HouXueZhang2020RFS.pdf`** →
   **HTTP 404, `text/html`, 9 bytes.** A nine-byte body at a guessed capitalisation.
   **Workaround:** the all-lowercase filename `houxuezhang2020rfs.pdf` → HTTP 200,
   `application/pdf`, 859,985 bytes. **Both the title line and the abstract were read before any
   number was taken.**
4. **`curl` → `https://www.sciencedirect.com/science/article/pii/S0304405X14002323`** → **HTTP 403**,
   `text/html`, 1,207,783 bytes — a 1.2 MB rejection page. **Workaround:** a course-site copy of the
   *JFE* typeset PDF, HTTP 200, `application/pdf`, 723,705 bytes; **title page verified against the
   journal, volume and page numbers before quoting.**
5. **`curl` → `https://epub.wu.ac.at/cgi/search?q=non-standard+errors+portfolio+sorts`** →
   **HTTP 404, `text/html; charset=utf-8`, 207 bytes.** The search endpoint does not exist at that
   path.
6. **OpenAlex `works?filter=title.search:methodological uncertainty portfolio sorts`** → **HTTP 200,
   valid JSON, `meta.count = 0`.** **Semantic Scholar `graph/v1/paper/search`** for the same title →
   **HTTP 200, valid JSON, empty `data` array.** Two indexes returning well-formed nothing for a paper
   that exists. Resolved by querying the **DOI** instead (`10.2139/ssrn.4164117`), which returns the
   work under its **old title** — *"Non-Standard Errors in Portfolio Sorts", 2022* — with `oa_url`
   pointing back to the DOI itself and `url_for_pdf: null` in Unpaywall. **A wrong-200 of a
   thirteenth kind, which I will name: a bibliographic index that answers a title query with zero
   results because the work is filed under a superseded title.**
7. **`WebFetch` → `https://www.wiwi.uni-konstanz.de/ag-walter/research/`** → HTTP 200, useful, and
   explicitly *"The page displays SSRN abstract links only."* Confirms that no author-hosted PDF
   exists; the block in (1) is therefore not circumventable by a different host.
8. **Wiley Online Library (Adams et al.) and Elsevier ScienceDirect (Soebhag's published version)**
   were **not attempted** for full text beyond (4) — both require institutional authentication, which
   this lane does not have and would not use. The published Soebhag abstract was taken from a
   **third-party bibliographic reproduction** and is labelled as such wherever it is used.

**Two integrity notes.** (i) **Every PDF's title line was read before any number was taken from it** —
the hazard being a well-formed PDF of a different paper at a guessed identifier. The HXZ capitalisation
miss in (3) is exactly how that hazard begins. (ii) **One table-extraction error was caught by reading
the prose against the table** (§6.6) — a column shifted by one row would have inverted which
sorting-variable family is most disturbed by the CRSP tape change. **No figure in this brief comes
from a search summariser.** Where a search summary first pointed me at a number — Mitton's 75%-in-2016
trend, HXZ's 65%, CCFS's "larger than five or ten", Soebhag's 70% — the number was then read from the
document, and the published Soebhag abstract, which I could not read from the document, is labelled
`[snippet only]` in the same sentence as its numbers.

---

## 15. WHAT THIS LANE LEAVES FOR THE PRINCIPAL

Nothing below is a recommendation to act; `R15` forbids it and this lane has measured nothing on the
fixture.

1. **The construction-node register `C2` proposed can now be filled in with a LONG-LEG column**, and
   four of twelve rows would read "unknown" (§7.4). The three rows that are filled in are the three
   nodes the campaign was told to worry about, and two of them are **zero** for a long leg.
2. **The single checkable number in this brief is `q < 1/J`.** Whatever outlier cutoff a construction
   uses, compare it to the top bucket's share of the eligible universe. Below that boundary,
   winsorising the characteristic is provably nothing; above it, 88.9% of a long leg can turn over.
   And `CLAUDE.md`'s 1%-both-tails **reporting** rule and a 1% **construction** rule are different
   decisions with different boundary conditions (§8.3).
3. **The deflator is not just round 2's Type N discovery; it is the switch that decides whether two
   of the nine nodes exist at all.** `GP/AT` cannot sign-flip (2 of 2,614 filers, both zero-asset
   shells); `OP/BE` sign-flips for 20.5% of filers and 62.9% of those land above the well-defined
   top-decile cutoff. **Round 4's `D3` lane is asking what separates those two definitions; this is a
   mechanical answer to part of it.**
4. **The return-measurement convention is worth `t` 1.61 → 2.30 on a spread and `t` 3.73 → 2.84 on a
   long leg, in opposite directions, with a closed-form prediction that holds to 0.009 pp/month.**
   If anything in this brief should be written into a runner assertion, it is that the arithmetic and
   log conventions are not two ways of reporting one number.
5. **CCFS's two optima are the most actionable published result in the lane**: the portfolio you hold
   should be cut into fewer buckets than the test you run, `n^{1/3}T^{1/3}` against `n^{1/2}T^{1/4}`.
   French's equal-weighted OP long leg agrees — its `t` falls monotonically as the sort gets finer, in
   both windows.
6. **The loss-maker subset is a third of the cross-section in the programme's window and it
   outperformed the bottom decile over 75 years.** Whatever is done with it, it is not a tail.
7. **A two-year stock-age filter is the majority convention in the literature, has a named
   justification, has never been named here, and on a panel that is ~35.7% dead it interacts with a
   survivorship axis the original justification was not about** (§6.4).
8. **The node the grids are missing is the one the cost literature already named**: a buy/hold spread
   is a two-threshold membership rule, the programme's `sel = rank < N_SLOTS` is its degenerate case,
   and Novy-Marx & Velikov call it the single most effective simple cost mitigation available (§8.4).

---

**Lane `D1` complete.** Sources: **14 distinct works obtained and read locally** (16 PDFs, 5 R source
files, 15 LaTeX result tables, 2 primary data-documentation pages and 4 public data archives on disk),
of which **9 read in full** (Mitton *RFS* 2022 · Hou-Xue-Zhang *RFS* 2020 · Cattaneo-Crump-Farrell-
Schaumburg *REStat* 2020 · Soebhag et al. FoFI 2022 · Schwarz-Walter-Weiss *JFQA* 2026 · the
negative-book-equity working paper · both of French's construction-detail pages · Walter-Weber-Weiss
as code, tables and all three appendices), **2 read in the passages quoted** (Fama-French 1993,
Fama-French 2015), **2 read in abstract** (Adams et al. 2019 · Shin 2026, the latter also in its
construction sections), **1 read third-hand** (Soebhag et al.'s published *JEF* abstract).
**Three independent measurements, fourteen negative controls, three of which FIRED and all three of
which produced a finding or a calibration.** Scripts and outputs in `data/D1_*`. Two entries on
`C2`'s "did not open" list are now opened (Hou-Xue-Zhang; Schwarz-Walter-Weiss's body); one of
`C2`'s classifications is corrected with a proof; one of `C2`'s weakest citations is upgraded from
summariser-sourced to `[read in full]`. **Nothing closed, nothing admitted, nothing elevated.**
