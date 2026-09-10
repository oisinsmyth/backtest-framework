# `D3` — ARE THESE TWO SIGNALS THE SAME SIGNAL?

**Round 4, lane `D3`.** Campaign contract: [`00-SCHEMA.md`](00-SCHEMA.md). Slate:
[`R4-00-slate.md`](R4-00-slate.md). Round 3: [`R3-99-record.md`](R3-99-record.md). The conflict this
lane puts evidence under is round 3's `F1`, between [`R3-03`](R3-03-the-shape-of-the-drawdown.md)
(`C3`) and [`R3-04`](R3-04-is-it-already-dead.md) (`C4`).

**EXTERNAL LITERATURE AND PUBLIC-DATA ONLY.** I have no access to the programme's fixture and claim
nothing about it. Every number I measured is on Chen–Zimmermann's published portfolio files or Ken
French's published portfolio files — all named, all byte-counted, all re-runnable.

**THIS LANE DOES NOT ADJUDICATE `F1`.** Both `C3`'s and `C4`'s readings stay on the record. My job was
to say what the disagreement is *made of*. Where I hold a view, it is labelled §13 and is a view.

Under [R15](../../RULES.md#r15) **nothing here closes or admits anything**, nothing is elevated into
`FINDINGS.md`, `RULES.md`, the books or a decision record. Both books are unchanged.

**WHERE THE EVIDENCE IS.** Per `00-SCHEMA.md` §1, the quoted evidence is in
[`../../../data/`](../../../data/) prefixed `D3_` (508 KB: the three measurement scripts and their
`.txt`/`.json` outputs, the nine Chen–Zimmermann source files quoted in §5, the six Ken French
documentation extracts quoted in §1.3, the eight Wayback extracts, and `D3_fetch.py` /
`D3_pdf2txt.py` / `D3_html2txt.py`). The **raw caches** — 109 MB of PDFs, portfolio ZIPs and HTML —
went to session temp as the schema requires; every one is re-fetchable with `D3_fetch.py` and the URLs
and Google-Drive file IDs recorded in §1 and in `D3_measure_same_signal.py`'s docstring, and each
recorded byte count and sha1 prefix is there to check against.

---

## 0. THE ANSWER, STATED FIRST

**THEY ARE NOT ONE SIGNAL, THE LITERATURE DOES COMPUTE BOTH ON ONE SAMPLE, AND THE ONE NUMBER THAT
SETTLES THE SHAPE OF `F1` IS 0.54 — BUT THE SAME SOURCES ALSO SAY THE GAP BETWEEN THEM LARGELY
DISAPPEARS IN THE SIZE SEGMENT THIS PROGRAMME TRADES.**

1. **THE SHARP VERSION HAS AN ANSWER AND IT IS YES.** Hou–Xue–Zhang's *Replicating Anomalies*
   computes **Gpa** — gross profits / current total assets, Novy-Marx's measure, which is `C4`'s
   signal — and **Ope** — operating profits / current book equity, Fama–French (2015)'s measure,
   which is `C3`'s signal — **on one sample, one dataset, one construction, across fourteen
   specifications including equal weighting.** January 1967–December 2016, 600 months. Under NYSE
   breakpoints with **equal weighting**, high-minus-low deciles: **`Gpa` +0.67 %/mo (|t| 4.35),
   `Ope` +0.13 %/mo (|t| 0.66)**; under all-stock breakpoints equal-weighted, **+0.64 (3.29) vs
   +0.29 (1.03)**. `F1`'s ordering reproduces inside one paper with the dataset held fixed. **So the
   difference is construction, not dataset, and it *can* be separated from published work.** §3.

2. **AND THE GAP IS SIZE-DEPENDENT, WHICH NO LANE HAS SEEN.** The same paper's Internet Appendix adds
   six more specifications. In the **microcap-only** bucket the ordering nearly vanishes and in one
   cell inverts: **`Ope` +0.96 (|t| 3.56) vs `Gpa` +0.83 (3.65)** value-weighted; **+0.46 (1.63) vs
   +0.47 (2.20)** equal-weighted. In all-but-micro equal-weighted it is **+0.49 (2.29) vs +0.62
   (3.59)**. **`Gpa`'s large advantage over `Ope` lives in the broad and NYSE-breakpoint
   specifications, not in the small-cap ones.** §3.2.

3. **THE DEFLATOR IS NOT A FREE NODE — IT IS DETERMINED BY THE NUMERATOR, BY THE ORIGINATING PAPER'S
   OWN ARGUMENT, QUOTED.** Novy-Marx (2013), p. 2: *"I scale gross profits by book assets, not book
   equity, because gross profits are an asset level measure of earnings. They are not reduced by
   interest payments and are, thus, independent of leverage."* Fama–French (2015) subtract interest
   expense and therefore deflate by equity — and say so about their own label: *"We call this
   variable operating profitability, OP, but it is operating profitability minus interest expense."*
   **Asset-level numerator → asset deflator; equity-level numerator → equity deflator. The two
   definitions are each internally consistent pairings, and crossing them breaks the logic of both.**
   §1.

4. **THE ARITHMETIC OF THE DIFFERENCE IS A LEVERAGE TERM, AND ONE PAPER'S ENTIRE SUBJECT IS THIS.**
   Ball, Gerakos, Linnainmaa & Nikolaev, *Deflating profitability* (Chicago Booth 14-10, May 2014 →
   JFE 117(2) 2015) holds the numerator FIXED and varies only the deflator. `GP/TA` is the
   **interaction** of `GP/BE` with book leverage `BE/TA`; in a horse race among the three deflators
   *"only the version of gross profit deflated by total assets is statistically significant"*
   (all-but-microcaps), **but among microcaps *"the leverage terms matter as much as or more than the
   interactions"*** — the same size dependence as (2), from a different paper. Their abstract:
   *"We find that net income equals gross profit in predictive power when both measures are
   constructed using consistent deflators."* §2.

5. **A CORRELATION, WHICH IS WHAT THE SLATE ASKED FOR — AND THE PUBLISHED ONE DOES NOT EXIST, SO I
   MEASURED IT THREE WAYS.** No source I found reports the correlation between gross
   profits-to-assets and operating profits-to-book-equity. The closest published numbers are BGLN's
   Table 2: holding the numerator fixed and changing the deflator (assets → market equity) gives
   **Pearson 0.10, Spearman 0.41**; holding the deflator fixed and changing the numerator (gross
   profit → net income) gives **0.40 / 0.40**. **The deflator change is at least as large a change as
   the numerator change, and in Pearson terms much larger.** `[MEASURED IN BRIEF]`, construction
   forced identical on one dataset: **corr(GP, OperProf) long–short = +0.54** full overlap,
   **+0.66** from 2010. And cross-dataset at the factor level: **corr(French's RMW, CZ's OperProf)
   = +0.83**, versus **corr(French's RMW, CZ's GP) = +0.53**. **Two independent builds of the SAME
   definition agree far more than two definitions built by the same team.** §5, §6.

6. **THE LITERATURE SPLITS EXACTLY AS ROUND 2 PREDICTED IT WOULD, AND THE SPLIT IS VISIBLE IN FOUR
   NAMED BEHAVIOURS.** BGLN and HXZ treat the deflator as a *hypothesis* and test it. Novy-Marx &
   Medhat (2025) convert the whole family to **one** deflator (book equity + minority interest) and
   drop Novy-Marx's own 2013 asset-deflated measure from the horse race entirely. Fama–French (2015)
   cite Novy-Marx (2013) as the motivation for adding a profitability factor, build a different
   variable, and never compute his. Asness–Frazzini–Pedersen average **six** measures spanning three
   deflators into one equal-weighted z-score composite with no correlation reported and no
   justification beyond *"In order to put each measure on equal footing and combine them."* §4.

7. **THE FAMILY HAS SIX NAMED MEMBERS, NOT TWO OR FOUR — AND THE HYBRID THE SLATE ASKED ABOUT
   EXISTS AND IS MEASURED WEAKER.** Novy-Marx & Medhat's Table B1 is a six-row taxonomy with the
   deflator stated for each. HXZ's grid is eight (four numerators × current/lagged). And
   **gross-profits-to-BOOK-EQUITY — the hybrid — is computed, by BGLN: 0.081 (t 3.45) alone, falling
   to 0.028 (t 1.31) once `GP/TA` and `GP/ME` are in the same regression** (all-but-microcaps).
   §7.

8. **A CORRECTION TO A FIGURE THIS CAMPAIGN IS CARRYING.** `C2` reported that *"the deflator"* is
   ranked **first of twelve** at mean |Δt| **3.91** in Mitton (2022). Read in the published *RFS*
   version: that 3.91 is **Table 8, leverage regressions, total debt/total assets → total debt/MARKET
   value of assets** — book-versus-market leverage. It is neither assets-versus-book-equity nor
   current-versus-lagged. **Mitton measures BOTH of the questions the slate asked about, separately,
   and in his *profitability* column: "different denominator" (= ROA → ROE, i.e. total assets → book
   equity) at |Δt| 12.31, and "END-YEAR denominator → BEGIN-YEAR denominator" (= current → lagged) at
   |Δt| 6.73.** Both are in Table 7, not Table 8. **The answer to the slate's question 4 is
   "assets-versus-equity", at a magnitude three times the figure the campaign has been carrying —
   but in a firm-level panel regression with firm fixed effects, not a portfolio sort.** §8.

9. **THREE CODE-LEVEL FINDINGS, ALL AGAINST DOCUMENTATION THAT SAYS OTHERWISE.** (i) Chen–Zimmermann's
   `OperProf` is documented — in `SignalDoc.csv` *and* in the Python file's own `ABOUTME` header — as
   **"Fama and French 2006, Table 3 Y_t/B_t"**, and its recorded evidence is that table's **t = 2.55**.
   Fama–French (2006)'s own appendix defines **Y_t as income before extraordinary items** — that row
   is **ROE**, not operating profitability. The code implements Fama–French (**2015**)'s numerator over
   Compustat **`ceq`**. Three inconsistent provenances for one signal, and the validating t-statistic
   belongs to a different variable. (ii) CZ's `GP` uses **`revt`** in both the Stata and Python
   implementations while `SignalDoc` says *"Revenue (sale)"*; its placebo `GPlag` uses **`sale`** and
   has **no financial-firm screen**, which `GP` does have — so CZ's `GP`/`GPlag` pair differs in three
   ways, not one, and is not a clean deflator placebo. (iii) CZ's `OperProf` excludes the **smallest
   size tercile** inside the signal itself, and does **not** drop financials; `GP` drops financials and
   keeps all sizes. **In every reference implementation the deflator arrives bundled with a universe
   screen.** §5.

10. **AND KEN FRENCH'S OWN SITE HAS STATED TWO DIFFERENT DENOMINATORS FOR `OP` CONTINUOUSLY SINCE
    EARLY 2019.** `variable_definitions.html`: *"divided by the sum of book equity and minority
    interest."* `det_port_form_op.html`, the page documenting the **univariate OP decile portfolios
    `C3` used**: *"divided by book equity."* The preamble shipped inside
    `100_Portfolios_ME_OP_10x10.csv`: *"divided by book"* — the word "equity" absent. And the shipped
    preambles say **"sales** minus cost of goods sold" where the web pages say **"revenues."**
    `[MEASURED IN BRIEF]` on the Wayback Machine: the variable-definitions page still said plain
    "book equity" on **2018-12-30** and said "book equity and minority interest" by **2019-03-03** —
    which does **not** corroborate Novy-Marx & Medhat's footnote dating the revision to **August
    2018**. §1.3.

**The precise negative I would put above all of this:** the one paper whose entire subject is this
question — *Deflating profitability* — has **never been obtained in its published form** by this
campaign, in round 2 (four routes), round 3 (the 2014 working paper only), or round 4; OpenAlex and
Semantic Scholar both return `closed` with no repository full text. Everything I report from it is
the **May 2014 Chicago Booth working paper**, whose cover title is *Deflating Gross Profitability*.

---

## 1. SOURCES — TYPE, AND HOW WELL ESTABLISHED

| # | source | type | established |
|---|---|---|---|
| `P1` | **Novy-Marx**, *The other side of value: The gross profitability premium*, **JFE 108(1), 2013**, 28 pp, `oldschoolvalue-files.s3.amazonaws.com` mirror, 551,335 B sha1 `06c846f54b1f`, extracted locally with `pypdf` | [PEER-REVIEWED] | **[read in full]** of §2 intro, §2.1, Table 1, Appendix A.1–A.2 — verbatim |
| `P1d` | **The same paper's April 2010 NBER DRAFT, w15940**, *The Other Side of Value: Good Growth and the Gross Profitability Premium*, 65 pp, 685,136 B sha1 `006ee203b770` | [WORKING PAPER] | **[read in full]** of §1–2, Table 2, Table 3 — **compared line by line against `P1`** (§1.2) |
| `P2` | **Fama & French**, *A five-factor asset pricing model*, **JFE 116(1), 2015**, 22 pp, `tevgeniou.github.io` mirror, 723,705 B sha1 `6afdcd98ee47` | [PEER-REVIEWED] | **[read in full]** of §1, §2 (Panel B of Table 1's text), Table 8's caption — verbatim; grepped for every occurrence of "Novy" and "gross profit" (5 hits, all reported) |
| `P3` | **Hou, Xue & Zhang**, *Replicating Anomalies*, **NBER w23394, May 2017**, 130 pp, 821,858 B sha1 `ba224d308f2c` | [WORKING PAPER] | **[read in full]** of §3–3.2.4 and Appendix A.4.9–A.4.20; Tables 3 Panel D and 4 columns 109–126 transcribed by me |
| `P3b` | **The same paper, OCTOBER 2018 version**, `theinvestmentcapm.com/uploads/1/2/2/6/122679606/replication2018oct.pdf`, 134 pp, 892,814 B sha1 `121eece05fe1` — 452 anomalies, sample to Dec 2016 | [WORKING PAPER] — the version of record's text | **[read in full]** of §3.2.4's profitability prose and Table 3's whole profitability panel, **all eight specifications, transcribed by me** (§3.1) |
| `P3c` | **The same paper's INTERNET APPENDIX, October 2018**, `…/replication_internetappendix_2018oct.pdf`, 15 pp, 129,169 B sha1 `f1bba16737cd` | [WORKING PAPER] — supplement to the version of record | **[read in full]** of Table A4's profitability panel, **six further specifications including microcap-only, transcribed by me** (§3.2) |
| `P4` | **Ball, Gerakos, Linnainmaa & Nikolaev**, *Deflating profitability*; cover sheet *Deflating Gross Profitability*, **Chicago Booth Paper 14-10, 6 May 2014**, 49 pp, `ivey.uwo.ca/media/3775544/linnainmaa.pdf`, 540,428 B sha1 `da8bfb956cc1`. Published **JFE 117(2), 2015, 225–248** | [WORKING PAPER] | **[read in full]** of abstract, §4–5, Tables 2, 3 and 4 — transcribed by me. **The PUBLISHED version was not obtained; see §11.1** |
| `P5` | **Novy-Marx & Medhat**, *Profitability Retrospective: What Have We Learned?*, **NBER w33601, March 2025**, 78 pp, 1,889,806 B sha1 `b30d382a8c2c`. **Medhat is at Dimensional; Novy-Marx authored the measure under review** | [WORKING PAPER] — **interested on both counts** | **[read in full]** of Appendix A.3, B.1–B.2, Tables B1 and B3, footnote 25 — verbatim |
| `P6` | **Mitton**, *Methodological Variation in Empirical Corporate Finance*, **RFS 35(2), 2022, 527–575** — the typeset published article (`RFS-OP-REVF210032`), 49 pp, `liuyanecon.com` mirror, 539,062 B sha1 `44058aa1da87` | [PEER-REVIEWED] | **[read in full]** of §2.2.2–2.3, Tables 1 (Panel A), 7 and 8 — transcribed by me |
| `P7` | **Fama & French**, *Profitability, Investment, and Average Returns*, **June 2005 DRAFT** posted on French's own site, 41 pp, 224,569 B sha1 `7f182cd133db`. Published **JFE 82(3), 2006, 491–518** | [WORKING PAPER] — marked *"Not for quotation"* on its own first page | **[read in full]** of the Data appendix and Table 3 Part A. **The published version was not obtained; OpenAlex says `closed`.** §11.2 |
| `P8` | **Asness, Frazzini & Pedersen**, *Quality Minus Junk*, draft 9 October 2013, 60 pp, `tevgeniou.github.io` mirror, 1,121,698 B sha1 `7b6ebe49e92d`. Published **RAST 24(1), 2019** | [WORKING PAPER] — **AQR authors, interested** | **[read in part]** — §2's quality-measure construction and the Appendix's Profitability block, verbatim. I did **not** read its empirical tables |
| `D1` | **Ken French's Data Library documentation**, five pages fetched live 2026-09-10: `variable_definitions.html` (14,236 B sha1 `a45e5a1ac754`), `det_port_form_op.html`, `det_op_breakpoints.html`, `six_portfolios_me_op.html`, `tw_5_ports_me_op.html`, `f-f_5_factors_2x3.html` | PRIMARY DATA DOC | **[read in full]**, all five, quoted verbatim in §1.3 |
| `D1b` | **The preambles shipped INSIDE French's own CSVs** — `Portfolios_Formed_on_OP.csv`, `100_Portfolios_ME_OP_10x10.csv`, `F-F_Research_Data_5_Factors_2x3.csv` | PRIMARY DATA DOC | **[read in full]** — these disagree with the web pages and with each other (§1.3) |
| `D1c` | **Wayback Machine snapshots** of `variable_definitions.html` at 2017-12-17, 2018-12-30, 2019-03-03, 2019-06-05, 2019-11-03, 2020-05-12, 2022-08-14, and of `det_port_form_op.html` at 2025-05-12 | PRIMARY ARCHIVE | **[read in full]** of the OP paragraph in each — `[MEASURED IN BRIEF]`, §1.3 |
| `D2` | **Chen–Zimmermann `SignalDoc.csv`**, `raw.githubusercontent.com/OpenSourceAP/CrossSection/master/SignalDoc.csv`, 331 rows | PRIMARY DATA DOC | **[read in full]** for all eleven profitability-family acronyms |
| `D2c` | **Chen–Zimmermann SOURCE CODE**, seven files read whole: `Signals/pyCode/Predictors/GP.py`, `…/OperProf.py`, `Signals/LegacyStataCode/Predictors/GP.do`, `…/OperProf.do`, `Signals/pyCode/Placebos/GPlag.py`, `Signals/LegacyStataCode/Placebos/GPlag.do`, `Portfolios/Code/30_PredictorAltPorts.R`, `Portfolios/Code/20_PredictorPorts.R` | [SOFTWARE DOC] | **[read in full]**, quoted verbatim in §5. **The code contradicts the documentation three times** |
| `M1` | **My own measurements.** CZ `PredictorAltPorts_QuintilesEW.zip` (18,290,738 B sha1 `4d9f4dfd4828`), `_QuintilesVW.zip` (18,947,238 / `12fb2eaa34c6`), `_DecilesEW.zip` (32,544,201 / `18b7d1dfb2a4`), `_LiqScreen_Price_gt_5.zip` (24,987,135 / `278eb1e42c73`), `PredictorLSretWide.csv` (3,293,172 / `71fe880a8923`); French `F-F_Research_Data_5_Factors_2x3_CSV.zip` (11,948 / `c9218d2ab2ff`), `Portfolios_Formed_on_OP_CSV.zip` (135,027 / `a889a239cee5`), `100_Portfolios_ME_OP_10x10_CSV.zip` (1,446,013 / `2bc4dedd4010`) | `[MEASURED IN BRIEF]` | scripts and outputs in [`../../../data/`](../../../data/): `D3_fetch.py`, `D3_pdf2txt.py`, `D3_html2txt.py`, `D3_measure_same_signal.py`, `D3_measure_price_screen.py`, `D3_measure_factor_corr.py` and their `.txt`/`.json` outputs. **The last two CZ byte counts and sha1 prefixes match `C4`'s recorded provenance exactly** — same bytes, independent pipeline |

---

## 1.1 THE TWO DEFINITIONS, FROM PRIMARY SOURCES, VERBATIM

### Gross profitability — Novy-Marx (2013), `P1`

Numerator and denominator, from the published JFE text and its Table 1 caption:

> *"gross profits (revenues minus cost of goods sold, REVT − COGS) scaled by assets (AT)"*

And the justification for the deflator, `P1` §2's opening pages (`P5` cites the adjacent sentences as
pp. 2–3), which is the load-bearing sentence of this whole lane:

> *"Scaling by a book-based measure, instead of a market-based measure, avoids hopelessly conflating
> the productivity proxy with book-to-market. **I scale gross profits by book assets, not book
> equity, because gross profits are an asset level measure of earnings. They are not reduced by
> interest payments and are, thus, independent of leverage.**"*

Universe: *"The sample excludes financial firms [i.e., those with a one-digit standard industrial
classification (SIC) code of six], though retaining financials has little impact on the results."*
Independent variables **trimmed** at 1%/99%. July 1963–December 2010.

### Operating profitability — Fama & French (2015), `P2`

From the published JFE §2, Panel B discussion:

> *"For portfolios formed in June of year t, profitability (measured with accounting data for the
> fiscal year ending in t−1) is annual revenues minus cost of goods sold, interest expense, and
> selling, general, and administrative expenses, all divided by book equity at the end of fiscal
> year t−1. **We call this variable operating profitability, OP, but it is operating profitability
> minus interest expense.** As in all our sorts, the OP breakpoints use only NYSE firms."*

No minority interest. Denominator: **book equity**. And the paper's only substantive engagement with
Novy-Marx is a citation, twice in the introduction and once here:

> *"The profitability effect identified by Novy-Marx (2013) and others is evident in Panel B of
> Table 1."*

`P2` contains **five** occurrences of "Novy" or "gross profit" in total, counted by grep: two
introduction citations, one section-2 sentence, one reference-list entry, and one acknowledgement.
**It never computes gross profits-to-assets and never compares.**

### What actually separates them — four things at once, not one

| | gross profitability (`C4`'s signal) | operating profitability (`C3`'s signal) |
|---|---|---|
| numerator | `REVT − COGS` | `REVT − COGS − XSGA − XINT` |
| interest treatment | **not** deducted → asset-level | deducted → equity-level |
| deflator | total assets, **current** | book equity, **current** |
| financials | **excluded** (SIC 6) | **included** |
| breakpoints in source | Table 2a says NYSE; CZ's note says all-stock reproduces better | **NYSE only**, stated |
| R&D | inside neither (gross profit is above SG&A) | folded into `XSGA`, so **punished** |

**Four simultaneous differences. Not one node.** Any statement of the form "the difference is the
deflator" is at best the largest of four.

## 1.2 DRAFT VERSUS PUBLISHED — NOVY-MARX (2013), AND IT MOVED ON THIS LANE'S EXACT NODE

`P1d` (April 2010, NBER w15940) versus `P1` (JFE 2013). Same Fama–MacBeth table, Panel A:

| | 2010 draft (`P1d` Table 2) | published (`P1` Table 1) |
|---|---|---|
| sample end | December **2009** | December **2010** |
| **deflator of the comparison variables, per the table caption** | *"income before extraordinary items (IB), and free cashflow …, **each scaled by assets (AT)**"* | *"income before extraordinary items (IB) and free cash flow …, **each scaled by book equity**"* |
| outlier treatment, per the caption | *"Independent variables are **Winsorized** at the one and 99% levels"* | *"Independent variables are **trimmed** at the 1% and 99% levels"* |
| gross profitability slope [t] | 0.67 [5.06] | 0.75 [5.49] |
| earnings slope [t] | **0.77 [1.77]** | **0.22 [0.84]** |
| free cash flow slope [t] | **0.65 [2.52]** | **0.27 [2.28]** |

Three things follow.

1. **The comparison variables' deflator changed from assets to book equity between draft and print**,
   and the earnings and free-cash-flow coefficients fell by roughly two thirds — consistent with a
   smaller denominator, as a deflator change to book equity would produce.
2. **The published paper's own appendix was not updated.** `P1` Table A1's caption still reads
   *"gross profitability [(REVT − COGS)/A], earnings (**IB/A**), free cash flow (**…)/A**)"* and
   describes itself as the correlations *"between the independent variables employed in the Fama and
   MacBeth regressions of Table 1."* **Table 1 says book equity; Table A1 says assets. Same paper,
   same variables.** The correlations were re-estimated on the longer sample (the GP/A–IB/A
   test-statistic moves 58.8 → 58.7) but the caption did not change.
3. **The caption also changed from "Winsorized" to "trimmed"** — which is `C2`'s #2 ranked node,
   Mitton's |Δt| 0.99 for purely random regressors and **3.37 for quasi-random profitability ratios**.
   I cannot attribute the coefficient changes to it, because the sample changed too. **But the
   originating paper of this family states two different outlier treatments in two versions, and
   nobody in this campaign had checked.**

**Consequence for sub-question 2:** the only published Spearman correlation involving gross
profitability and an equity-deflated profitability measure is **`P1` Table A1's 0.45 between GP/A and
"earnings"** — and the paper labels that variable `IB/A` in the appendix and `IB/BE` in the main text.
**I therefore cannot use 0.45 as a GP/A-versus-equity-deflated correlation.** Reported, unused.

For completeness, from `P1` Appendix A.1 and A.2, all [snippet-free, transcribed by me]: GP/A with
IB/A **0.45**, with FCF/A **0.31**, with B/M **−0.18**, with ME **−0.03**; and EBITDA/A and XSGA/A
have Spearman correlations with GP/A of **0.51** and **0.77**.

## 1.3 KEN FRENCH'S DOCUMENTATION SAYS FOUR DIFFERENT THINGS, AND THE PAGE `C3` RELIED ON IS THE ODD ONE OUT

All four fetched live on 2026-09-10. Emphasis mine.

| where | what it says the denominator is | what it says the numerator starts from |
|---|---|---|
| `variable_definitions.html` | *"divided by the sum of **book equity and minority interest** for the last fiscal year ending in t−1"* | *"annual **revenues** minus cost of goods sold, interest expense, and selling, general, and administrative expense"* |
| `det_port_form_op.html` — **the univariate OP decile portfolios, which is `C3`'s object** | *"divided by **book equity** for the last fiscal year end in t−1"* | *"annual **revenues** minus cost of goods sold, interest expense, and selling, general, and administrative expenses"* |
| `det_op_breakpoints.html`, `six_portfolios_me_op.html`, `tw_5_ports_me_op.html` | *"divided by **book equity**"* | *"annual **revenues** …"* |
| the preamble inside `Portfolios_Formed_on_OP.csv` | *"divided by **book equity** at the last fiscal year end of the prior calendar year"* | *"operating profits (**sales** minus cost of goods sold, minus selling, general, and administrative expenses, minus interest expense)"* |
| the preamble inside `100_Portfolios_ME_OP_10x10.csv` | *"divided by **book** at the last fiscal year end of the prior calendar year"* — the word "equity" is absent | *"(**sales** − cost of goods sold − selling, general and administrative expenses − interest expense)"* |

So: **two denominators** (book equity; book equity + minority interest) and **two numerator revenue
items** (revenues; sales — `REVT` and `SALE` are different Compustat items) on one website, at one
moment, describing portfolios formed on one variable.

**When it changed — `[MEASURED IN BRIEF]` on the Wayback Machine.** Novy-Marx & Medhat (`P5`)
footnote 25 states: *"In August 2018, the definition of operating profits-to-book equity on Ken
French's website was revised to include minority interest (MIB) in the denominator."* The archived
page text does not support that date:

| snapshot | `variable_definitions.html` OP denominator |
|---|---|
| 2017-12-17 | book equity |
| **2018-12-30** | **book equity** |
| **2019-03-03** | **book equity and minority interest** |
| 2019-06-05, 2019-11-03, 2020-05-12, 2022-08-14, live 2026-09-10 | book equity and minority interest |
| `det_port_form_op.html` @ 2025-05-12, and live 2026-09-10 | **book equity** |

**The page text changed between 30 December 2018 and 3 March 2019, not in August 2018.** Either the
*data* changed in August 2018 and the documentation lagged by up to nine months, or `P5`'s date is
wrong. I cannot tell which from the archive, and I note that `P5` is describing a change to a
construction its own authors replicate, so it has reason to know. **What is certain is that the
univariate OP portfolio pages have never been updated, and that French's site has stated two
different denominators simultaneously for over seven years.**

One more, small and recorded because it shows the pages are hand-maintained: the `<title>` tag of
`det_port_form_op.html` reads *"Kenneth R. French - Detail for Portfolios Formed on Earnings/Price"*
while its body heading reads *"Detail for Portfolios Formed on Operating Profitability"*; and
`det_op_breakpoints.html` still carries `Dimensional Fund Advisors` Word metadata from 2008-08-28 in
its extracted text.

---

## 2. THE PAPER WHOSE ENTIRE SUBJECT IS THE DEFLATOR

`P4`, Ball, Gerakos, Linnainmaa & Nikolaev. Abstract, verbatim:

> *"Gross profit scaled by book value of total assets predicts the cross-section of average returns.
> Novy-Marx (2013) concludes that it outperforms other measures of profitability such as earnings,
> cash flows, and dividends. One potential explanation for the measure's predictive ability is that
> its numerator — gross profit — is a "cleaner" measure of economic profitability. An alternative
> explanation lies in the measure's deflator. **We find that net income equals gross profit in
> predictive power when both measures are constructed using consistent deflators.** We then construct
> an alternative measure of profitability, operating profitability, which better matches current
> expenses with current revenue. This measure exhibits a far stronger link with expected returns than
> either net income or gross profit."*

### 2.1 The 2 × 3 grid — numerator and deflator varied independently, one sample

`P4` Table 3 Panel A, **all-but-microcaps**, Fama–MacBeth slopes [t], July 1963–December 2012,
regressors trimmed 1/99, controls `log(BE/ME)`, `log(ME)`, `r1,1`, `r12,2`. Transcribed by me.

| numerator | deflated by total assets | deflated by book equity | deflated by market equity |
|---|---|---|---|
| **gross profit** | **0.840 [5.40]** | 0.271 [4.39] | 0.329 [3.50] |
| **income before extraordinary items** | **3.455 [5.98]** | 1.330 [4.13] | 1.838 [3.17] |

Panel B, **microcaps**: gross profit 0.876 [6.55] / 0.143 [2.79] / 0.106 [1.92]; income before
extraordinary items 2.035 [3.41] / 0.752 [2.39] / 0.458 [1.06].

Read down the columns: **with the deflator held fixed, the numerator barely matters** (t 5.40 vs 5.98
on assets; 4.39 vs 4.13 on book equity). Read across the rows: **with the numerator held fixed, the
deflator orders the result** — assets first, market equity or book equity after. This is the paper's
title claim and it is the cleanest published isolation of the node.

### 2.2 A spanning test in both directions, numerator held fixed

`P4` Table 4 puts the three deflated versions of **the same numerator** into one regression.
All-but-microcaps, slopes [t]:

| | (1) | (2) | (4) | (5) | (8) all three |
|---|---|---|---|---|---|
| gross profit **to total assets** | 0.724 [5.28] | | | 0.595 [4.03] | 0.725 [5.12] |
| gross profit **to book equity** | | 0.081 [3.45] | 0.102 [4.05] | 0.054 [2.10] | **0.028 [1.31]** |
| gross profit to market equity | | | | | −0.052 [−0.60] |
| book equity to total assets (book leverage) | | | 0.298 [1.72] | 0.045 [0.25] | |

`P4`'s own words on what this means:

> *"Gross profit deflated by the book value of total assets is the interaction between the other two
> regressors, a measure of profitability (π/BE) and book leverage (BE/TA). In this specification, the
> t-value for gross profit to the book value of equity remains statistically significant but
> attenuates by almost half."*

> *"Finally, in column (8) we run a horserace among the three deflators. When the three versions of
> gross profit with the different deflators are included in the same regression along with the
> control variables, **only the version of gross profit deflated by total assets is statistically
> significant**."*

> *"The results in Table 4 are consistent with gross profitability deriving a large part of its
> explanatory power from the interactions arising from the mismatch in the deflators between the
> dependent and independent variables. **However, among Microcaps the leverage terms on their own
> have as much or more explanatory power as their interactions with profitability.**"*

Microcap Panel B, same columns: gross profit to total assets 0.340 [2.86] / 0.136 [0.97] / 0.408
[3.08] / 0.354 [2.57]; gross profit to book equity 0.029 [1.64] / 0.042 [2.29] / **0.105 [2.89]** /
0.055 [1.89]; book leverage **0.671 [4.10]** and **0.784 [4.59]**. `P4`, on column (5) of Panel B:
*"the leverage term (book equity to total assets) is highly significant as is gross profit to book
equity, while gross profit to total assets is not."*

**So the deflator spanning result is size-conditional, and it is the small end where the
asset-deflated version stops winning.** This is the first of two independent sources saying that.

### 2.3 The identity that makes the two definitions non-equivalent

`P4` states it for market equity; it holds for book equity the same way:

```
GP / TA  =  (GP / BE) × (BE / TA)
```

**The assets-deflated measure is an equity-deflated profitability measure multiplied by book
leverage.** This is the exact sibling of `C2`'s identity for the other deflator question,
`GP/AT = (GP/AT₋₁) ÷ asset growth`. **Both deflator changes smuggle a second characteristic into the
sorting variable: current-versus-lagged smuggles investment, assets-versus-equity smuggles
leverage.** In `C2`'s taxonomy both are Type N — effect non-equivalence, not arbitrary choice.

### 2.4 Correlations, holding one thing fixed at a time — `P4` Table 2

Pearson (Panel A) and Spearman (Panel B), 1963–2012, transcribed by me:

| held fixed | changed | Pearson | Spearman |
|---|---|---|---|
| deflator (total assets) | numerator: gross profit → income before extraordinary items | **0.40** | **0.40** |
| numerator (gross profit) | deflator: total assets → market equity | **0.10** | **0.41** |
| numerator (income b.e.i.) | deflator: total assets → market equity | 0.19 | 0.73 |

**`P4` does not report a book-equity column in Table 2, so the GP/TA-versus-GP/BE correlation is still
not published anywhere I found.** What is published is that changing the deflator while holding the
numerator fixed produces a variable **0.10 correlated in levels** with the original — a weaker
relationship than changing the numerator produces. `P4`'s own summary of the row: *"When the variables
are deflated by market value of equity, the Pearson correlation is 0.27 but the Spearman rank
correlations is zero."*

---

## 3. THE SHARP VERSION: A PUBLISHED MEASUREMENT OF BOTH DEFINITIONS ON ONE SAMPLE

**It exists.** Hou–Xue–Zhang's *Replicating Anomalies* builds the whole family on one sample with one
set of procedures and reports each separately. Appendix definitions, verbatim from `P3`:

- **A.4.9 `Gpa`:** *"Following Novy-Marx (2013), we measure gross profits-to-assets, Gpa, as total
  revenue (Compustat annual item REVT) minus cost of goods sold (item COGS) divided by total assets
  (item AT, the denominator is current, not lagged, total assets)."* — **this is `C4`'s signal.**
- **A.4.12 `Ope`:** *"Following Fama and French (2015), we measure operating profitability to equity,
  Ope, as total revenue (item REVT) minus cost of goods sold (item COGS, zero if missing), minus
  selling, general, and administrative expenses (item XSGA, zero if missing), and minus interest
  expense (item XINT, zero if missing), scaled by book equity (the denominator is current, not
  lagged, book equity). We require at least one of the three expense items (COGS, XSGA, and XINT) to
  be non-missing. Book equity is stockholders' book equity, plus balance sheet deferred taxes and
  investment tax credit (item TXDITC) if available, minus the book value of preferred stock…"* —
  **this is `C3`'s signal, and the book-equity construction is Davis–Fama–French's, i.e. French's
  own, with no minority interest.**
- Plus `Gla`, `Ole`, `Opa`, `Ola`, `Cop`, `Cla` — the lagged-deflator and other-numerator members.

Common procedures, verbatim: *"we form testing deciles with NYSE breakpoints and value-weighted
returns… sort all stocks at the end of June of each year t… **Financial firms and firms with negative
book equity are excluded**"* — excluded for **every** anomaly, so that nuisance is matched across the
two definitions, which it is **not** in either lane's dataset.

### 3.1 `P3b` Table 3, eight specifications, Jan 1967–Dec 2016, 600 months

High-minus-low decile average return `R` (%/mo) and **absolute** t, transcribed by me from
`P3b`'s profitability panel. `SS` = the original studies' shorter samples.

| signal | numerator | deflator | NYSE-VW | **NYSE-EW** | All-VW | **All-EW** | FM-WLS | FM-OLS | NYSE-VW-SS | FM-WLS-SS |
|---|---|---|---|---|---|---|---|---|---|---|
| **`Gpa`** | `REVT−COGS` | AT, current | 0.37 [2.63] | **0.67 [4.35]** | 0.58 [2.83] | **0.64 [3.29]** | 0.12 [2.05] | 0.18 [3.97] | 0.41 [2.64] | 0.12 [1.96] |
| `Gla` | `REVT−COGS` | AT, lagged | 0.17 [1.13] | 0.24 [1.54] | 0.31 [1.67] | 0.24 [1.24] | 0.06 [0.96] | 0.04 [0.92] | 0.16 [1.03] | 0.06 [0.85] |
| **`Ope`** | `−XSGA −XINT` | **BE, current** | 0.27 [1.34] | **0.13 [0.66]** | 0.57 [1.88] | **0.29 [1.03]** | 0.17 [2.08] | 0.11 [1.38] | 0.26 [1.20] | 0.18 [2.06] |
| `Ole` | `−XSGA −XINT` | BE, lagged | 0.11 [0.58] | −0.13 [0.70] | 0.68 [2.40] | 0.14 [0.52] | 0.07 [1.22] | 0.04 [0.51] | 0.07 [0.38] | 0.07 [1.17] |
| `Opa` | `−XSGA +XRD` | AT, current | 0.41 [2.09] | 0.43 [2.43] | 0.81 [2.58] | 0.59 [2.49] | 0.13 [1.86] | 0.17 [2.39] | 0.34 [1.70] | 0.12 [1.59] |
| `Ola` | `−XSGA +XRD` | AT, lagged | 0.20 [1.11] | 0.03 [0.14] | 0.62 [2.18] | 0.20 [0.86] | 0.03 [0.42] | 0.05 [0.85] | 0.17 [0.91] | 0.01 [0.17] |
| `Cop` | cash-based | AT, current | 0.63 [3.57] | 0.69 [4.81] | 0.82 [3.34] | 0.81 [4.15] | 0.16 [2.42] | 0.23 [4.13] | 0.62 [3.41] | 0.16 [2.33] |
| `Cla` | cash-based | AT, lagged | 0.55 [3.23] | 0.46 [3.03] | 0.93 [3.97] | 0.72 [3.68] | 0.10 [1.57] | 0.20 [3.67] | 0.52 [3.01] | 0.10 [1.45] |

**What this table answers.**

- **Sub-question 6: YES.** Both definitions, one sample, one construction. `F1`'s ordering survives
  holding the dataset fixed, and under **equal weighting** — which is the programme's weighting and
  both lanes' weighting — the gap is **+0.54 %/mo** (NYSE breakpoints) or **+0.35** (all-stock).
- **Equal weighting WIDENS the gap, and in opposite directions.** `Gpa` goes VW 0.37 → EW 0.67;
  `Ope` goes VW 0.27 → EW **0.13**. Whatever makes `Ope` weak, equal weighting makes it weaker, and
  whatever makes `Gpa` strong, equal weighting makes it stronger.
- **Within-table node isolation, to the extent this grid allows it.** Holding the deflator at current
  assets and changing the numerator from gross to operating-plus-R&D: NYSE-EW 0.67 → 0.43. Changing
  the deflator from current assets to current book equity (with `XINT`/`XRD` also differing):
  0.43 → 0.13. **Both steps matter under equal weighting; neither is the whole gap.** Current →
  lagged is comparable in size to either: `Gpa` 0.67 → `Gla` 0.24, `Ope` 0.13 → `Ole` −0.13,
  `Opa` 0.43 → `Ola` 0.03.
- **The only member significant in all eight specifications is `Cop`** — cash-based operating
  profitability over current assets, which is `R2-02`'s recommendation and the one `C1` measured as
  reaching **nine** filers on as-filed SEC XBRL.

`P3`'s own prose on the mechanism, verbatim, and it is the `C2`-style argument:

> *"Because Gpa equals Gla divided by asset growth, the Gpa premium is confounded with the investment
> premium. Purging the investment premium yields an economically small and statistically
> insignificant gross profitability premium."*

> *"Operating profits-to-book equity (Ope), which is the sorting variable underlying the Fama-French
> (2015) robust-minus-weak profitability factor (RMW), also fails to replicate."*

### 3.2 `P3c` Table A4, six MORE specifications — and the gap is size-dependent

Internet Appendix to the October 2018 version. `ABM` = all-but-micro breakpoints; `EM` = microcaps
purged after forming deciles; `Micro` = **microcap breakpoints, microcaps only**. Transcribed by me.

| signal | ABM-VW | **ABM-EW** | NYSE-VW-EM | FM-WLS-EM | **Micro-VW** | **Micro-EW** |
|---|---|---|---|---|---|---|
| **`Gpa`** | 0.49 [2.77] | **0.62 [3.59]** | 0.33 [2.29] | 0.09 [1.75] | **0.83 [3.65]** | **0.47 [2.20]** |
| `Gla` | 0.19 [1.15] | 0.29 [1.90] | 0.14 [0.94] | 0.05 [0.81] | 0.48 [2.09] | 0.06 [0.27] |
| **`Ope`** | 0.19 [0.80] | **0.49 [2.29]** | 0.21 [1.01] | 0.08 [1.53] | **0.96 [3.56]** | **0.46 [1.63]** |
| `Ole` | 0.16 [0.76] | 0.21 [1.17] | 0.05 [0.29] | 0.04 [0.81] | 0.85 [3.26] | 0.37 [1.33] |
| `Opa` | 0.37 [1.79] | 0.65 [3.45] | 0.33 [1.72] | 0.06 [1.28] | 1.44 [6.48] | 0.74 [3.06] |
| `Ola` | 0.22 [1.16] | 0.30 [1.82] | 0.15 [0.80] | 0.00 [0.08] | 1.13 [5.46] | 0.46 [1.95] |
| `Cop` | 0.70 [3.75] | 0.77 [5.11] | 0.62 [3.58] | 0.11 [2.14] | 1.52 [8.17] | 1.14 [5.94] |
| `Cla` | 0.56 [3.09] | 0.64 [4.38] | 0.54 [3.25] | 0.07 [1.25] | 1.47 [8.12] | 1.06 [5.27] |

**THIS IS THE FINDING THAT CAME AFTER THE BAR WAS MET.** Across fourteen specifications on one
sample, the `Gpa`-over-`Ope` gap is:

| specification family | `Gpa` − `Ope` (%/mo) |
|---|---|
| NYSE-EW | **+0.54** |
| All-EW | +0.35 |
| ABM-EW (all-but-micro, equal-weighted) | **+0.13** |
| Micro-EW (microcaps only, equal-weighted) | **+0.01** |
| Micro-VW (microcaps only, value-weighted) | **−0.13** — `Ope` larger |

**In the two size buckets closest to a small-to-mid equal-weighted universe, the two definitions
are indistinguishable in magnitude, and in one of them `Ope` is the larger.** `Ope`'s |t| rises from
0.66 (NYSE-EW) to 2.29 (ABM-EW) to 3.56 (Micro-VW). The large `Gpa`-over-`Ope` gap that reproduces
`F1` is a property of the **broad-universe, NYSE-breakpoint** specifications.

This is the second independent source with the same size conditionality: `P4` §2.2's microcap panel
says the same thing from the deflator side.

**What it does NOT say.** These are **long–short decile spreads**, not long legs. `C3` and `C4` both
measured **long legs against their own universe**, which is a different object and need not inherit
the spread's ordering — `C4` itself measured that gross profitability's post-2013 widening was
roughly two-thirds in the short leg. **`P3`/`P3c` cannot settle `F1` because they never report a leg.
That is round 3's own most reusable finding arriving again: three literatures do not report the long
leg, and this is a fourth.**

### 3.3 DRAFT VERSUS PUBLISHED — `P3`, and it matters for what round 2 could have known

| | `P3` NBER w23394, **May 2017** | `P3b` **October 2018** |
|---|---|---|
| anomalies | 447 | 452 |
| sample | Jan 1967 – **Dec 2014** | Jan 1967 – **Dec 2016**, 600 months |
| occurrences of `NYSE-EW` | **0** | **28** |
| equal-weighted decile spreads reported | **none** | **four** specifications in Table 3, **six more** in the Internet Appendix |
| `Gpa` (NYSE-VW) | 0.38 [2.62] | 0.37 [2.63] |
| `Gla` | 0.16 [1.04] | 0.17 [1.13] |
| `Ope` | 0.25 [1.20] | 0.27 [1.34] |
| `Ole` | 0.07 [0.37] | 0.11 [0.58] |
| **`Opa`** | **0.37 [1.87]** | **0.41 [2.09]** — crosses 1.96 |
| `Ola` | 0.20 [1.07] | 0.20 [1.11] |
| `Cop` | 0.63 [3.44] | 0.63 [3.57] |
| `Cla` | 0.53 [3.02] | 0.55 [3.23] |

Two consequences and one defect.

1. **The equal-weighted evidence exists only in the later version.** Round 2's `R2-02` recorded its
   HXZ source as *"text read = NBER w23394 (May 2017)"* — the version with **zero** equal-weighted
   columns. **A lane reading w23394 would correctly conclude the paper has no EW evidence. It does
   now, and the EW numbers are the ones this programme needs.**
2. **`Opa` crosses the conventional threshold between versions on two extra years of data alone**
   (1.87 → 2.09). A construction node did not move; the sample did.
3. **The October 2018 version's prose carries stale figures its own table contradicts.** Its §3.2.4
   still reads *"the high-minus-low gross profits-to-lagged assets (Gla) decile earns an average
   return of only 0.16% per month (t = 1.04). This estimate is lower than 0.38% (t = 2.62) for the
   high-minus-low gross profits-to-assets (Gpa) decile"* — the **2014-sample** numbers — while its
   Table 3 says 0.17 [1.13] and 0.37 [2.63]. The `Ope`, `Ole` and `Opa` sentences **were** updated.
   **The update was partial, and the un-updated sentence is the gross-profitability one, which is the
   figure secondary sources quote.**

---

## 4. DOES THE LITERATURE TREAT THEM AS ONE FAMILY OR AS TWO SIGNALS? FOUR DISTINCT BEHAVIOURS

Round 2 found the field splits between sources that justify a construction choice and sources that
inherit it silently. **The same split holds on "is this one signal," and it resolves into four
behaviours rather than two.**

**(a) Treated as a hypothesis and TESTED — explicit.** `P4` is built to test whether the deflator or
the numerator carries gross profitability's power, and answers it. `P3` builds eight members of the
family on one sample and reports each separately with a stated reason for each pairing. **Two sources
out of eight treat "is it one signal" as an empirical question.**

**(b) Treated as one family by assumption, via AVERAGING — the strongest silent inheritance.** `P8`,
Asness–Frazzini–Pedersen, verbatim from its Appendix:

> *"We compute a profitability z-score by averaging z-scores of gross profits over assets (GPOA),
> return on equity (ROE), return on assets (ROA), cash flow over assets (CFOA), gross margin (GMAR)
> and low accruals (ACC)."*

and the justification, in full:

> *"In order to put each measure on equal footing and combine them, each month we convert each
> variable into ranks and standardize to obtain a z-score."*

**Six measures, three different deflators (total assets, book equity, sales), equal weights, no
correlation reported, and the stated reason is commensurability of units rather than equivalence of
content.** `P4`'s Table 2 says GPOA and an equity-deflated earnings measure are 0.40 correlated at
best; `P8` gives them equal weight in one score.

**(c) Treated as one family by CITATION, then replaced — silent inheritance of the effect, not the
variable.** `P2`, Fama–French (2015), cites Novy-Marx (2013) as the motivation for adding a
profitability factor, constructs a different variable with a different numerator and a different
deflator, and writes *"The profitability effect identified by Novy-Marx (2013) and others is evident
in Panel B of Table 1."* **The continuity is asserted; it is never measured.** And `P3` then reports
that the sorting variable underlying the factor this paper introduced *"fails to replicate."*

**(d) Treated as one family by CONVERSION — the most recent authority, and it drops its own measure.**
`P5`, Novy-Marx & Medhat (2025). Their Table B1 is the field's own six-row taxonomy, transcribed by
me:

| measure | formula | deflator, per `P5` | source |
|---|---|---|---|
| Gross profits | `REVT − COGS` | total assets; **excludes financials** | Novy-Marx (2013) |
| Operating profits before R&D and interest | `GP − (XSGA − XRD)` | total assets; excludes financials | Ball et al. (2015) |
| **Operating profits after R&D and interest** | `GP − XSGA − XINT` | **book equity** | **Fama & French (2015)** |
| Cash profits before R&D and interest | `GP − (XSGA − XRD) − ACC` | **average** total assets; excludes financials | Ball et al. (2016) |
| Cash profits after R&D and interest | `GP − XSGA − ACC − XINT` | book equity | Fama & French (2018); Detzel et al. (2022) |
| Operating profits before R&D minus interest | `GP − (XSGA − XRD) − XINT` | book equity | Fama & French (2016a); Jagannathan et al. (2023); **this paper** |

**The deflator is not an independent axis in this taxonomy — it is bundled with the numerator and
with a financial-firm screen.** Asset-deflated measures are the Novy-Marx/Ball lineage and exclude
financials; equity-deflated measures are the Fama–French lineage and do not. **In the published
literature the deflator never travels alone.**

And `P5`'s horse race, Table B3: *"All profit measures are scaled by **book equity (BE) plus minority
interest (MIB)**."* Four measures compete — `OP`, `OP_R&D`, `COP`, `COP_R&D` — and

- `OP_R&D` subsumes `OP` (`OP` goes to **−1.00 [t −1.96]** alongside `OP_R&D` at **1.99 [4.11]**) and
  subsumes `COP` (**0.04 [0.42]** vs **1.09 [6.99]**);
- **gross profits-to-assets is not in the horse race at all.**

**Novy-Marx's 2025 retrospective converts the entire family to one deflator — book equity plus
minority interest — and never tests his own 2013 asset deflator against it.** `P5` contains no
correlation matrix of profitability definitions; I grepped it (11 hits for "correlat", all reported
in §11.4, none of them between definitions).

**Score on sub-question 3: two sources test it, six assume it, and the two that test it disagree with
each other about which deflator wins once you condition on size.**

---

## 5. HOW THE REFERENCE DATASETS ACTUALLY BUILD THESE — FROM THE CODE, NOT THE DOCUMENTATION

Round 3 found a reference repository's code comment contradicting three second-hand restatements, and
the code comment was right. **Here the code contradicts the repository's own documentation three
times.**

### 5.1 `GP` — documentation says `sale`, both code implementations say `revt`

`Signals/pyCode/Predictors/GP.py`, verbatim:

```python
# ABOUTME: Gross profitability following Novy-Marx 2013, Table 2a
df = df[(df["sic"] < 6000) | (df["sic"] >= 7000)]
df["GP"] = (df["revt"] - df["cogs"]) / df["at"]
```

`Signals/LegacyStataCode/Predictors/GP.do`, verbatim: `gen GP = (revt-cogs)/at`, preceded by
`keep if (sic < 6000 | sic >= 7000)`.

`SignalDoc.csv`'s Detailed Definition for `GP`: *"Revenue (**sale**) - cost of goods solds (cogs),
divided by total assets (at). Drop if financial."* **Both implementations use `REVT`; the
documentation says `SALE`.** `P3` A.4.9 also uses `REVT`. Novy-Marx's own published Table 1 caption
says `REVT − COGS`; his **2010 draft** says *"Compustat REVT - COGS"* too.

### 5.2 `GPlag` is not a clean deflator placebo — it differs in THREE ways

`Signals/LegacyStataCode/Placebos/GPlag.do`, verbatim and complete:

```stata
use gvkey permno time_avail_m sale cogs at using "$pathDataIntermediate/m_aCompustat", clear
xtset permno time_avail_m
gen GPlag = (sale-cogs)/l12.at
```

and `Signals/pyCode/Placebos/GPlag.py`, whose header says *"translates line-by-line from Stata code"*,
does the same: `(pl.col('sale') - pl.col('cogs')) / pl.col('l12_at')`.

| | `GP` | `GPlag` |
|---|---|---|
| revenue item | **`revt`** | **`sale`** |
| deflator | `at` | `l12.at` |
| financial-firm screen | **yes**, SIC 6000–6999 dropped | **none** |

**`GP` minus `GPlag` is not the deflator alone.** `C4`'s deflator-versus-asset-growth check
(`data/C4_measure_deflator_vs_assetgrowth.py`, and `R3-04`'s prediction that *"the monthly series
`GP_long − GPlag_long` should be strongly correlated with CZ's `AssetGrowth` long leg"*) and round 2's
`B2` deflator result both lean on this pair.
I make no claim about what the confound does to those numbers — I have not recomputed them — **but
the pair is not a one-node comparison and should not be described as one.** `P3`'s `Gpa`/`Gla` pair
**is** clean: same `REVT`, financials excluded throughout, deflator the only difference.

### 5.3 `OperProf` — three inconsistent provenances, and its validating t-statistic belongs to ROE

`Signals/pyCode/Predictors/OperProf.py`, verbatim:

```python
# ABOUTME: Operating profitability following Fama and French 2006, Table 3 Y_t/B_t
# ABOUTME: calculates operating profits scaled by book equity, excluding smallest size tercile
# Notes:
# Excludes smallest size tercile to simulate NYSE size breakpoints
# Operating profitability = (revenue - cogs - sga - interest) / equity
# Removing SGA expenses significantly improves signal strength (similar to Novy-Marx)
df["tempprof"] = (df["revt"] - df["cogs"] - df["xsga"] - df["xint"]) / df["ceq"]
df.loc[df["tempsizeq"] == 1, "tempprof"] = pd.NA
```

`Signals/LegacyStataCode/Predictors/OperProf.do`, verbatim, including its own comments:

```stata
// dirty simulation of NYSE size breakpoints:
// Fama and French use NYSE market cap median to form size groups,
// independently sort on OperProf, and then equally weight the two
// size groups with high OperProf in the long portfolio
// (see RFS paper footnote to Table 1)
      * more complicated denominator (ceq-pstk+min(txdi,0)) does not help
      * removing xsga helps a _lot_, and is pretty much the Novy Marx signal
gen tempprof = (revt - cogs - xsga - xint)/ceq
egen tempsizeq = fastxtile(mve_c), by(time_avail_m) n(3)
replace tempprof = . if tempsizeq == 1
```

Four findings from this one file.

1. **The denominator is Compustat `ceq` — ordinary common equity.** It is **not** French's book
   equity (which adds balance-sheet deferred taxes and the investment tax credit and subtracts
   preferred stock), **not** book equity + minority interest, and **not** `P3`'s `Ope` denominator.
   The code's own comment records that the fuller denominator was tried and rejected on fit:
   *"more complicated denominator (ceq-pstk+min(txdi,0)) does not help."*
2. **The signal excludes the smallest size tercile, inside the signal itself** — so it cannot be
   un-excluded by choosing a different portfolio file, and it is the opposite of what an
   equal-weighted small-to-mid programme would want.
3. **Three inconsistent provenances.** `SignalDoc` and the Python `ABOUTME` both say **Fama and
   French 2006, Table 3 `Y_t/B_t`**. The Stata comment cites an **RFS** paper's footnote to Table 1.
   The formula implemented is **Fama–French (2015)**'s numerator. Three different papers for one
   signal.
4. **The comment `"removing xsga helps a _lot_, and is pretty much the Novy Marx signal"` cannot be
   reconciled with the code on either reading.** The code *subtracts* `xsga`; Novy-Marx's signal does
   *not*, and his whole argument is that SG&A should not be deducted because it contains investment in
   growth. The Python port restates it as *"Removing SGA expenses significantly improves signal
   strength (similar to Novy-Marx)"* — the same ambiguity, carried forward. **The code is
   unambiguous and identical in both languages; only the comment is ambiguous, and the comment is
   what a reader would rely on.** I record this as an ambiguity, not as an error, because I cannot
   determine which reading was intended.

**And the validating statistic belongs to a different variable.** `SignalDoc` records for `OperProf`:
`Key Table in OP` = **"3 Y_t/B_t"**, `T-Stat` = **2.55**, `Test in OP` = "mv reg", sample
**1977–2003**. From `P7`, Fama–French's own Data appendix, verbatim:

> *"The base accounting variables, from Compustat, are: A_t, total assets (Compustat data item 6);
> **Y_t, income before extraordinary items (18)**; … and B_t, book equity (total assets (6), minus
> liabilities (181), plus balance sheet deferred taxes and investment tax credit (35) if available,
> minus preferred stock liquidating value (10)…)."*

And `P7`'s Table 3 Part A, second specification, has `Y_t/B_t` slope **1.10, t = 2.55** — the exact
t-statistic `SignalDoc` records. **Fama–French (2006)'s `Y_t/B_t` is income before extraordinary
items over book equity. It is ROE.** CZ's `OperProf` is built as Fama–French (**2015**)'s operating
profits over `ceq` and validated against Fama–French (**2006**)'s ROE slope. `P5`'s Table B1
independently attributes the equity-level operating-profits definition to **Fama and French (2015)**,
not 2006. Two further small mismatches: `P7`'s t = 2.55 row runs **July 1963–December 2004**, not the
1977–2003 window `SignalDoc` records (1977–2003 is `P7`'s window for specifications requiring
`I_t/B_t`); and the document I read is the **June 2005 draft** marked *"Not for quotation"*, not the
published JFE 82(3) — see §11.2.

### 5.4 Which CZ portfolio file holds construction fixed — from `30_PredictorAltPorts.R`

This matters because it determines whether any measurement on CZ data is comparing definitions or
comparing constructions. Verbatim:

```r
## Price > 5
port <- loop_over_strategies(
  strategylist0 %>% mutate(filterstr = "abs(prc) > 5")
)
…
## QUINTILE SORTS
# force equal weighting
port <- loop_over_strategies(
  strategylistcts %>% mutate(q_cut = 0.2, sweight = 'EW')
)
```

**The `LiqScreen_Price_gt_5` file changes only the filter; every signal keeps its SignalDoc
construction.** And SignalDoc's constructions differ by signal:

| | `GP` | `OperProf` | `OperProfRD` | `CBOperProf` |
|---|---|---|---|---|
| `Stock Weight` | **VW** | **EW** | VW | VW |
| `LS Quantile` | 0.2 | *(blank)* | 0.1 | 0.1 |
| `Quantile Filter` | *(none)* | *(none)* | NYSE | NYSE |

**In the price-screened file, `GP` is value-weighted and `OperProf` is equal-weighted.** Only the
`Quintiles*`/`Deciles*` files force one construction on every predictor. `[MEASURED IN BRIEF]`
confirmation: `GP`'s long–short series in the price-screened file correlates **+0.44** with the same
signal in the forced-EW file, while `OperProf`'s correlates **+0.95** — exactly what you would expect
if `GP` is VW in the first file and `OperProf` is already EW. **`C4`'s headline numbers come from
`QuintilesEW`, so they are not affected; but anyone reaching for the `$5`-screened file to match this
programme's floor gets a value-weighted gross-profitability leg without being told.**

---

## 6. `[MEASURED IN BRIEF]` — THE CORRELATION NOBODY PUBLISHES, THREE WAYS, WITH CONTROLS THAT FIRE

Scripts and full outputs: `data/D3_measure_same_signal.py` + `.txt`/`.json`,
`data/D3_measure_price_screen.py` + `.txt`/`.json`, `data/D3_measure_factor_corr.py` + `.txt`/`.json`.

### 6.1 Controls first, including the ones designed to be able to fail

| control | what it tests | result |
|---|---|---|
| **`P1` reproduction** | my pipeline against CZ's own published figure for `GP`, original-paper construction, `SignalDoc`'s own in-sample window 1963-07→2010-12 | mean **0.3030**, t **2.39**, n 570 vs `SignalDoc`'s **0.31 / 2.49**. **PASS** — and it matches `C4`'s independently computed 0.303 / 2.39 exactly |
| **`P2` identity** | `LS` must equal top minus bottom portfolio, every month, in all three forced files, for both signals | max abs deviation **9.1 × 10⁻¹⁴ to 1.0 × 10⁻¹³**, six of six. **PASS** |
| **`P3` block proof** | compound French's **monthly equal-weighted** `Hi 10` block and match French's own **annual equal-weighted** `Hi 10` block, 62 years | worst abs diff **0.0325 pp**. **PASS** — same standard `C3` met at 0.0333 |
| **`N5` block discrimination — A CONTROL THAT CAN FIRE** | the same compounding test run against the **value-weighted** monthly block, the block I did *not* mean to read | worst abs diff **37.49 pp**. **FIRES** — the test can tell the stacked blocks apart |
| **`N3c` deliberate break — A CONTROL THAT CAN FIRE** | add 1.00 to one month of a `LS` series and re-run the `P2` identity check | identity deviation jumps to **1.0000**. **FIRES** |
| **`N3` date-key integrity** | corr(`GP`, `GP`) must be exactly 1; corr(`GP`, `GP` shifted one month) must not be | **1.000000000000** and **0.1505**. **PASS** — positional misalignment would have shown as 1.0 |
| **`N4` file distinctness** | the forced-EW and forced-VW files must not be the same bytes in disguise | `GP` `LS` corr **0.5529**, max abs diff **11.68 pp**. **PASS** |
| **`N1` negative control — the one that decides whether the headline correlation means anything** | correlate `GP`'s `LS` with non-profitability predictors on the same file and construction | `AssetGrowth` **−0.278**, `BM` **−0.142**, `Mom12m` **+0.327**, `Beta` **−0.253**. **PASS** — all well below the 0.54 treatment |
| **sentinel census — a value that MUST return zero** | French declares *"Missing data are indicated by -99.99 or -999"*; count such cells in the files I used | **0 of 57,888** numeric cells in `Portfolios_Formed_on_OP.csv`, **0 of 618,000** in `100_Portfolios_ME_OP_10x10.csv`, **0** in the FF5 file. The only `-99.99` string in either OP file is the preamble sentence announcing the convention |
| CZ `NA` census | `NA`/blank returns silently included in any statistic | **0** across all four CZ files, 43,188–79,178 rows kept each |

**All controls pass; two of them fire on the inputs they were built to reject.** Note honestly: the
sentinel census returns zero, so it proves the hazard does not bind on these files — it does **not**
prove my sentinel filter would catch one. The `N5` block test is what proves I read the block I meant
to.

### 6.2 Construction held fixed, one dataset: how correlated are the two signals?

CZ `PredictorAltPorts_QuintilesEW.csv` — `q_cut = 0.2`, `sweight = 'EW'` forced on every continuous
predictor, all-stock breakpoints, annual June rebalance, the same lag convention for both.

| | full overlap (n = 738, 1963-07→2024-12) | from 2010-01 (n = 180) | from 2014-01 (n = 132) |
|---|---|---|---|
| corr(`GP`, `OperProf`) **long–short** | **+0.5400** | **+0.6628** | +0.6735 |
| corr(`GP`, `OperProf`) **long leg** | +0.9308 | +0.9407 | +0.9294 |

Deciles, equal-weighted: long–short **+0.6432 / +0.6612 / +0.6676**. Quintiles value-weighted:
**+0.3743 / +0.5395 / +0.6123**.

**Read the two rows together.** The long legs are 0.93 correlated **because they are both long
equities** — that number is market beta, not signal agreement. The spreads, which net the market out,
are **0.54**: about **29% shared variance**. Against the `N1` negative controls at |0.14| to |0.33|,
0.54 is clearly a relationship; against a same-definition benchmark (§6.4) it is clearly not the same
signal.

And in the price-screened file, where `GP` is VW and `OperProf` EW, the same correlation reads
**+0.19** full and **+0.11** from 2010 — **so roughly two-thirds of the two signals' apparent
independence in that file is the construction mismatch, not the definition.** A reader comparing
definitions across CZ files without checking `30_PredictorAltPorts.R` would overstate their
independence by a factor of three.

### 6.3 The same table, re-measured as long legs against their own equal-weighted universe

Benchmark = the equal-weighted average of the five quintile portfolios, i.e. the sort's own universe —
the `B1` benchmark both lanes used. `%`/mo, [t].

| | in-sample-era full overlap | **2010-01 → 2024-12** | **2014-01 → 2024-12** |
|---|---|---|---|
| **`GP` long − own universe** | +0.2579 [6.06], n 882 | **+0.3789 [3.56]**, n 180 | **+0.4046 [3.00]**, n 132 |
| **`OperProf` long − own universe** | +0.1420 [3.06], n 738 | **+0.1298 [1.65]**, n 180 | **+0.1125 [1.11]**, n 132 |
| `OperProfRD` long − own universe | +0.0966 [1.92] | +0.1552 [1.51] | — |
| `CBOperProf` long − own universe | +0.2100 [5.41] | +0.1792 [2.05] | — |

**My `GP` figures reproduce `C4`'s headline to four decimal places**: `C4` recorded +0.3789 [3.56] for
2010–2024 and +0.4046 [3.00] for 2014–2024; I get +0.3789 [3.56] and +0.4046 [3.00] from the same
bytes through an independently written pipeline. That is the cross-lane positive control.

**So, holding dataset, construction, weighting, cut, lag and era fixed, and changing ONLY the
definition, `C4`'s headline moves from +0.405 [t 3.00] to +0.113 [t 1.11] — close to `C3`'s
near-nothing.**

**AND — this must be said plainly — `C4` already had this.** `C4_ownuniverse.json` contains the
`OperProf` row, and `R3-04` states it in its §6.4 and in its own point 8: *"CZ's data agrees with
French about that definition — `OperProf`'s long leg also decays, +0.141 [t 2.58] → +0.113 [t 1.11]"*
and *"The disagreement in this lane is between DEFINITIONS, not between datasets."* My numbers are
`C4`'s numbers. **What `F1` records — that the differences are "named, not ranked" — understates what
`C4` had already put on the record.** I note that as a fact about the record, not as a verdict on
`C3`: `C3`'s object is French's OP **deciles** over **1963–2026**, including financials and
microcaps, on a **book-equity (or book-equity-plus-minority-interest, §1.3) denominator**, and CZ's
`OperProf` is **quintiles**, **`ceq`**, **excluding the smallest size tercile** and **including**
financials. **Those residual differences are exactly the size and universe dimensions §3.2 shows the
answer depends on.**

### 6.4 Cross-dataset, cross-team: is the definition or the implementation the binding difference?

French's `RMW` is built from French's own `OP` on French's own book equity from CRSP+Compustat by one
team. CZ's `OperProf` is the same *definition* built by a different team from different intermediate
files with `ceq`, a size-tercile exclusion and no financial screen. CZ's `GP` is a *different
definition* built by the same team from the same files as CZ's `OperProf`.

**Design:** `RMW ~ CZ OperProf` is the positive control — definition held, everything else changed.
`RMW ~ CZ GP` is the treatment — definition changed, team and dataset also changed.

| CZ file | signal | full overlap (n 738) | from 2010-01 (n 180) |
|---|---|---|---|
| **EW quintiles** | **`OperProf`** (same definition) | **+0.8348** | **+0.7869** |
| EW quintiles | **`GP`** (different definition) | **+0.5285** | +0.5897 |
| EW quintiles | `OperProfRD` | +0.5115 | +0.6276 |
| EW quintiles | `CBOperProf` | +0.4583 | +0.6095 |
| **VW quintiles** | **`OperProf`** | **+0.7584** | **+0.6762** |
| VW quintiles | `GP` | +0.4598 | +0.5540 |
| VW quintiles | `OperProfRD` | +0.5574 | +0.5995 |
| VW quintiles | `CBOperProf` | +0.4407 | +0.5772 |

**Two independent builds of the SAME definition, by different teams, on different intermediate data,
with different denominators (`BE+MIB` vs `ceq`), different universes and different cuts, correlate
0.76–0.83. Two definitions built by the SAME team on the SAME files correlate 0.46–0.59.** The
definition dominates the implementation, by a wide margin, and it does so in both weightings and in
both eras.

**This is the number I would put in front of the principal if only one survived the edit.** It is not
an adjudication of `F1` — it is a statement that `C3` and `C4` were measuring objects that two
independent implementations of each definition would agree are different objects.

---

## 7. GOING PAST THE SUB-QUESTIONS: THE FAMILY HAS AT LEAST SIX MEMBERS, AND THE HYBRID EXISTS

Sub-question 7 asked whether there is a third convention. There are at least four more.

| member | numerator | deflator | who | is it measured against the other two? |
|---|---|---|---|---|
| gross profits-to-assets | `REVT − COGS` | AT current | Novy-Marx 2013 | yes — `P3`, `P4` |
| gross profits-to-**lagged** assets | `REVT − COGS` | AT lagged | HXZ's `Gla`; CZ's `GPlag` | yes — `P3` |
| **gross profits-to-BOOK EQUITY** | `REVT − COGS` | **BE current** | **`P4`'s Table 4** | **yes, and it loses** |
| gross profits-to-market equity | `REVT − COGS` | ME | `P4` | yes |
| operating profits-to-assets | `−XSGA +XRD` | AT current | Ball et al. 2015 | yes — `P3`'s `Opa` |
| operating profits-to-book equity | `−XSGA −XINT` | BE current | FF 2015 | yes — `P3`'s `Ope` |
| operating profits-to-BE+MIB | `−XSGA −XINT` | **BE + MIB** | French's site since ~2019; `P5`'s `RMW` | partially — `P5` Table A3 |
| operating profits before R&D, minus interest, / BE+MIB | `−(XSGA−XRD) −XINT` | BE + MIB | `P5`'s own `PROF` | yes — `P5` Table B3 |
| cash-based operating profits / assets | `−(XSGA−XRD) −ACC` | **average** AT per `P5`; **current** AT per `P3` and CZ's code | Ball et al. 2016 | yes |
| cash profits / book equity | `−XSGA −ACC −XINT` | BE | FF 2018; Detzel et al. 2022 | yes — `P5` |

**Three things worth flagging.**

1. **The hybrid the slate asked about is real and published.** `P4` Table 4 computes gross
   profits-to-book-equity: **0.081 [t 3.45]** on its own, **0.102 [4.05]** controlling for book
   leverage, **0.054 [2.10]** against `GP/TA`, and **0.028 [1.31]** in the three-deflator horse race
   (all-but-microcaps). Among **microcaps** it reaches **0.105 [2.89]** and survives while `GP/TA`
   becomes insignificant. **By Novy-Marx's own leverage argument this hybrid should not work — a
   pre-interest numerator over an equity deflator is internally inconsistent — and it is indeed the
   weaker of the two, except among small stocks.**
2. **`P5` and `P3`/CZ disagree on the cash-based member's deflator.** `P5` Table B1 says Ball et al.
   (2016) scale by *"**average** total assets"*; `P3` A.4.18 says *"book assets (item AT, the
   denominator is current, not lagged, total assets)"*; CZ's `CBOperProf.py` divides by `at`. **Three
   restatements of one paper's deflator, two of which agree and one of which does not — and the
   published version of the paper in question was the one round 2 could not obtain.** I did not
   resolve it; it is item 3 of §11.
3. **`P5`'s `PROF` versus `RMW` spanning test is the one published spanning result on a pure
   numerator change with the deflator held at BE+MIB**, and it is asymmetric, verbatim: *"RMW does not
   earn positive abnormal return relative to PROF, while the converse is not true: PROF earns highly
   significant abnormal returns relative to RMW and the remaining Fama and French (2015) factors."*
   US averages: `RMW` 0.28 %/mo [t 3.44], `PROF` 0.39 [5.91]. **`PROF` differs from `RMW` only by
   undoing Compustat's folding of R&D into SG&A.** That is the numerator node, isolated, and it is
   worth 0.11 %/mo and 2.5 t-points in a value-weighted 2×3 factor.

---

## 8. SUB-QUESTION 4, ANSWERED AND CORRECTED: WHICH DEFLATOR QUESTION IS MITTON'S #1 NODE?

`C2` brought back: *"One ranked list puts **the deflator first** (mean |Δt| = **3.91**, largest of
twelve) — independently confirming `B2` from a source `B2` never read."* Read in the published *RFS*
version, `P6`:

**The 3.91 is Table 8, and Table 8 is about LEVERAGE regressions.** `P6` §2.2.3, verbatim:

> *"Row 1 shows that the most impactful methodological decision in these tests is the decision to use
> the most common dependent variable (**total debt/total assets**) or the next most common variable
> with a different denominator (**total debt/market value of assets**). Across all 65 leverage
> determinants tested, the decision of whether to use **book leverage or market leverage** changes the
> t-statistic on the coefficient for the determinant by 3.91, on average."*

**It is a book-versus-market denominator change on the dependent variable of a leverage regression.
It is neither assets-versus-book-equity nor current-versus-lagged.** `C2` reported the figure
correctly; the attribution to *"`B2`'s deflator"* is what needs qualifying.

**And Mitton measures BOTH of the questions the slate asked, separately, in his profitability
column.** `P6` Table 7 — quasi-random Compustat ratios, 1,000 per regression category, firm and year
fixed effects, 1963–2018, column (3) = **Profitability**:

| row | decision changed | **Prof.** |Δt| | ALL |
|---|---|---|---|
| (1) | winsorise at 1/99 → retain outliers | **12.86** | 9.20 |
| (2) | continuous explanatory → dummy | 7.81 | 8.70 |
| (3) | level dependent → logged dependent | 7.90 | 8.01 |
| **(4)** | **most common dependent variable → next most common with a different DENOMINATOR** | **12.31** | 7.92 |
| (5) | winsorise 1/99 → winsorise 5/95 | 9.82 | 6.71 |
| (6) | contemporaneous explanatory → lagged explanatory | 6.46 | 4.71 |
| **(8)** | **END-YEAR denominator on dependent variable → BEGIN-YEAR denominator** | **6.73** | 4.26 |
| (9) | most common dependent → next most common with a different NUMERATOR | 3.35 | 3.94 |
| (10) | winsorise 1/99 → **trim** 1/99 | 3.37 | 2.62 |
| (13) | include all industries → exclude financial firms | 0.57 | 0.52 |

And what row (4) *is*, from `P6` §1's own summary: *"in profitability regressions, winsorizing
outliers changes the t-statistic by 12.86 on average and **changing the dependent variable from ROA
to ROE** changes the t-statistic by 12.31 on average."* `P6` Table 1 Panel A, the usage census over
260 profitability-regression dependent variables in top finance journals, confirms which variables
those are: most common **EBITDA/TA 14%**, then **Net income/TA 10%**, Operating income/TA 8%,
Operating income before depreciation/TA 7%, **Net income/BE 6%**, EBIT/TA 5% — and *"In total, **61
unique measures** of profitability are used as dependent variables."*

**So the answer to sub-question 4 is: assets-versus-book-equity, at |Δt| 12.31; current-versus-lagged
is a separate row at 6.73; and the 3.91 the campaign has been carrying is a third thing entirely.**
Both of the slate's candidate readings are measured, the one it hoped for is the larger, and neither
is the headline figure.

**Three caveats, and they are load-bearing.**

1. **Mitton's setting is a firm-level panel regression with firm and year fixed effects explaining a
   corporate-finance outcome, not a portfolio sort predicting returns.** The deflator there is on the
   **dependent** variable. A sorting variable's deflator is a different object, and the |Δt|
   magnitudes should not be read across.
2. **These are quasi-random Compustat ratios, not hypothesised variables.** `P6`'s own Table 8 is the
   actual-hypotheses version and its magnitudes are **2–4× smaller** (3.91, 3.74, 3.72, 1.83, 1.77,
   1.41, 1.37, 1.10, 0.99, 0.67, 0.27, 0.26). For purely random regressors (Table 6) the
   ROA→ROE figure is **0.93**. **The same node reads 0.93, 3.91-analogue, or 12.31 depending on which
   of three experiments you quote.**
3. **There is no profitability-sort ranking that includes the deflator at all.** `C2` established
   that Walter–Weber–Weiss's fourteen-node grid has no deflator node — the variable's definition sits
   outside it — and my reading of `P3`'s and `P4`'s grids is consistent with that: the deflator is
   varied in the *papers about deflators*, never in the construction-grid literature. I did not
   re-open Walter–Weber–Weiss's files (§12).

---

## 9. WHAT THE DISAGREEMENT IS MADE OF — THE ANSWER IN ONE TABLE

Every difference I could establish between `C3`'s object and `C4`'s object, with a source and, where
one exists, a magnitude. **This is the lane's deliverable.**

| # | difference | `C3`'s object | `C4`'s object | established by | magnitude, where published or measured |
|---|---|---|---|---|---|
| 1 | **deflator** | book equity (or BE+MIB — `C3` cannot know which, §1.3) | total assets | `P1`, `P2`, `D1` | `P4`: horse race — only the asset-deflated version survives, **all-but-micro**; the reverse among microcaps. `P6`: |Δt| 12.31 in a panel setting |
| 2 | **interest expense** | deducted → equity-level | not deducted → asset-level | `P1` p. 2, `P2` §2 | not separately measured anywhere I found |
| 3 | **SG&A / R&D** | SG&A deducted with R&D inside it | neither deducted | `P1`, `P2`, `P5` Table B1 | `P5` Table A3: undoing the R&D fold is worth **+0.11 %/mo and t 3.44 → 5.91** at the factor level |
| 4 | **financial firms** | **included** | **excluded** (SIC 6) | `D1`, `D2c` GP code | `P6` Table 7 row 13: |Δt| **0.57** — his *smallest* node |
| 5 | **quantile count** | deciles | quintiles | both lanes | `C2`'s Walter–Weber–Weiss: ranked **#1** of fourteen, normalised MAD 1.09 in profitability. My own: GP long-minus-universe 2010+ is **+0.379** quintiles vs **+0.413** deciles |
| 6 | **dataset / implementation** | French | Chen–Zimmermann | both lanes | **§6.4: worth 0.17–0.24 of correlation, versus 0.30–0.35 for the definition.** The implementation is the smaller term |
| 7 | **universe size composition** | all NYSE/AMEX/NASDAQ with positive BE | CZ's `GP` all sizes; CZ's `OperProf` **drops the smallest size tercile** | `D1`, `D2c` | **§3.2: this is the dimension the answer depends on.** The `Gpa`−`Ope` gap runs +0.54 (NYSE-EW) → +0.13 (ABM-EW) → +0.01 (Micro-EW) → **−0.13** (Micro-VW) |
| 8 | **era** | 1963-07→2026-07 | CZ data ends 2024-12 | both lanes | both lanes report era splits; `P3b` adds two years to `P3` and moves `Opa` across 1.96 |
| 9 | **breakpoint exchange** | NYSE | all-stock for `GP` per CZ's code note | `D1`, `D2` | `C2`'s Walter–Weber–Weiss: ranked #6, MAD 0.88 |
| 10 | **object reported** | long leg vs own EW universe | long leg vs own EW universe | both lanes | **the same, and this is the one thing they agree on — and the one thing no published source reports** |

**Differences 1, 2 and 3 are the definition. They are bundled in every published source and in every
reference implementation. Nobody separates them on a portfolio sort.** `P4` separates 1 from 2+3 on
Fama–MacBeth slopes, with the numerator held at gross profit, and that is the closest anyone comes.

---

## 10. WHAT THE LANE CAN AND CANNOT CLOSE

**Can.**

- There **is** a published measurement of both definitions on one sample with one construction,
  including equal weighting: `P3b` Table 3 and `P3c` Table A4, fourteen specifications. **`F1` is not
  beyond published work.**
- The two are **not one signal** on any measure I can construct: 0.54 spread correlation with
  construction forced identical; 0.53 versus 0.83 against a same-definition benchmark across datasets.
- The deflator is **not an arbitrary node** — it is pinned to the numerator by a stated argument in
  the originating paper, and the two versions differ by a multiplicative leverage term.
- `C2`'s 3.91 attribution needs correcting, and the correct figures are 12.31 and 6.73, in a
  different table and a different setting.

**Cannot.**

- **No source reports either definition's LONG LEG.** `P3`/`P3c` report spreads; `P4` reports
  Fama–MacBeth slopes and value-weighted quintile/decile portfolio returns; `P2` reports
  size-OP portfolios but not against a matched universe. `C3` and `C4` are measuring an object the
  literature does not publish. **This is round 3's blind-spot finding recurring for a fourth
  literature.**
- **No source varies the deflator alone on a portfolio sort.** `P4` does it on regression slopes;
  `P3`'s `Opa`-versus-`Ope` comparison changes `XINT` and `XRD` at the same time.
- **No source reports corr(GP/TA, OP/BE).** `P4` reports the assets-versus-market-equity version
  (0.10 Pearson) and `P1` the same-deflator numerator version (0.45 Spearman, with a caption
  ambiguity). §6 is the only number of its kind I know of, and it is mine.
- **`F1` itself is not settled by any of this**, because `C3`'s and `C4`'s objects differ on **ten**
  dimensions (§9), and because **the one dimension with the largest published sensitivity — size
  composition — is a dimension on which the two lanes' universes differ and on which the published
  answer reverses.**

---

## 11. WHAT I COULD NOT VERIFY, STATED PLAINLY

1. **The PUBLISHED version of *Deflating profitability* (JFE 117(2), 2015, 225–248) — the single most
   on-point paper in this lane — was not obtained, and this is now the third consecutive round in
   which that is true.** Routes tried, with tool and response: `Bash`/`urllib` GET on
   `faculty.tuck.dartmouth.edu/images/uploads/faculty/joseph-gerakos/Ball,_Gerakos,_Linnainmaa,_et_al._2015.pdf`
   → **HTTP 404, 14,704 B, `text/html`** (a 404 page at a `.pdf` URL); the same with a browser-like
   User-Agent and a Referer → **404** again; `sciencedirect.com/.../pdfft` → **HTTP 403, 832,803 B
   `text/html`**; `web.archive.org/web/2020/` on the Tuck URL → **HTTP 200, 12,988 B, `text/html`** —
   **a wrong-200: the archived 404 page served at a `.pdf` URL**; `juhanilinnainmaa.com` → DNS
   failure (`getaddrinfo failed`). Two independent indexes say there is nothing to get:
   **Semantic Scholar `openAccessPdf.status = "CLOSED"`** and **OpenAlex `oa_status: "closed",
   any_repository_has_fulltext: false`**. Everything I report from `P4` is the **May 2014** Chicago
   Booth working paper. **Its figures may have changed in print; round 3's own record shows `P3`'s
   did.**
2. **The published Fama–French (2006), JFE 82(3), was not obtained** — OpenAlex `closed`, no
   repository full text. `P7` is the **June 2005 draft** from French's own site, marked *"Not for
   quotation"* on its first page. The `Y_t` = income before extraordinary items definition and the
   Table 3 `Y_t/B_t` t = 2.55 are from that draft. **The §5.3 finding rests on it**, corroborated
   indirectly by `P5` Table B1 attributing the equity-level operating-profits definition to
   Fama–French (2015) rather than 2006, but **not** corroborated against the published 2006 text.
3. **Whether Ball et al. (2016) deflate cash-based operating profitability by CURRENT or AVERAGE total
   assets is unresolved.** `P5` Table B1 says *"average total assets"*; `P3` A.4.18 says current;
   CZ's code divides by `at`. I did not obtain the 2016 published paper (round 2 did, via an
   `anderson.ucla.edu` mirror, and read it as current assets). **Three restatements, two agreeing.**
4. **No correlation between any asset-deflated and any book-equity-deflated profitability measure was
   found in any source.** I grepped `P5` (11 hits for "correlat", none between definitions), `P4`
   (Table 2 has assets and market-equity columns only), `P1`/`P1d` (Table A1/Table 3, same-deflator
   only), `P3`/`P3b`/`P3c` (none). **If one exists, I did not find it.**
5. **I cannot tell whether French's OP *data* changed in August 2018 as `P5` footnote 25 says.** The
   archived page *text* changed between 2018-12-30 and 2019-03-03. Whether the minority-interest
   revision applies to the univariate OP decile files at all is **not determinable from French's
   documentation**, because those pages still say plain book equity in September 2026.
6. **CZ's `OperProf` Stata comment `"removing xsga helps a _lot_, and is pretty much the Novy Marx
   signal"` cannot be reconciled with the code on either English reading.** I report the ambiguity; I
   did not determine the intent, and I did not search CZ's issue tracker or commit history for it.
7. **I did not recompute round 2's or round 3's deflator results under the `revt`/`sale`/financials
   confound I found in CZ's `GP`/`GPlag` pair.** I state the confound; I make no claim about its
   effect on `B2`'s `t` 1.04–1.85 or on `C4`'s asset-growth check.
8. **My §6 measurements are on CZ's and French's published PORTFOLIO returns, not on firm-level
   characteristics.** I therefore measured **return** correlations, not **characteristic** (Pearson or
   Spearman rank) correlations. Those are different quantities and the published numbers in §2.4 are
   the characteristic kind. **My 0.54 is not comparable to `P4`'s 0.10.**
9. **`P8` (Quality Minus Junk) was read only for its construction sections.** I did not read its
   empirical tables and do not know whether it reports correlations among its six profitability
   measures somewhere I did not open.
10. **HTTP/rate-limit events logged by tool and response, not by host:** `Bash`/`urllib` GET on
    `archive.org/wayback/available` → **HTTP 429, 117 B, `text/html`** ("Too Many Requests"), twice,
    which is why the Wayback work in §1.3 uses `web.archive.org/web/<ts>/` directly;
    `Bash`/`urllib` GET on `papers.ssrn.com/sol3/Delivery.cfm/SSRN_ID3009750_code1542588.pdf` →
    **HTTP 403, 5,836 B, `text/html`**; `Bash`/`urllib` GET on
    `mba.tuck.dartmouth.edu/.../det_form_op.html` → **HTTP 404, 1,245 B** (my guessed filename; the
    real one is `det_port_form_op.html`).
11. **The search summariser offered the dead Tuck PDF URL as a working source twice, in two separate
    queries, and both times it was a 404.** It also produced the Mitton 3.91 gloss that I then had to
    correct against the paper. **Both are reported here as summariser output I did not use.**

---

## 12. WHAT I DID NOT OPEN

Separate from §11. These are documents and datasets I know exist, that bear on this lane, and that I
chose not to spend the budget on.

1. **Walter, Weber & Weiss's replication repository and their `04_mad_acrossnodes.tex`** — `C2` read
   it and established that the variable's definition sits outside their fourteen-node grid. **I relied
   on `C2` and did not re-verify.** If the deflator *is* in their grid somewhere, I would not know.
2. **Ball, Gerakos, Linnainmaa & Nikolaev (2016), JFE 121(1)** — *Accruals, cash flows, and operating
   profitability*. Round 2 read it in full. I did not re-open it, including for the cash-based
   deflator question in §11.3.
3. **Fama & French (2018), *Choosing factors*, JFE 128(2)**, and **Fama & French (2016), *Dissecting
   anomalies with a five-factor model*, RFS 29(1)** — the latter is almost certainly the "RFS paper
   footnote to Table 1" CZ's Stata comment cites, and I did not confirm that.
4. **Detzel, Novy-Marx & Velikov** on cash profitability and transaction costs — named in `P5` Table
   B1 as a source for the fifth family member.
5. **Jagannathan et al. (2023)** — named in `P5` Table B1 as a co-source for `P5`'s own preferred
   measure.
6. **`P5`'s Internet Appendix Tables D1–D3** — the sub-period (split at 2000) and non-US repeats of
   the Table B3 horse race. `P5`'s prose says the early period resembles the full sample; I did not
   read the tables, and **the post-2000 split is the era this programme trades.**
7. **`P3c`'s and `P3b`'s remaining panels** — I read the profitability panels in full and did not read
   momentum, value, investment, intangibles or frictions.
8. **CZ's `PredictorAltPorts_Deciles.zip`, `_DecilesVW.zip`, `_Quintiles.zip`, `_FF93style.zip`,
   `_HoldPer_{1,3,6,12}.zip`, `_LiqScreen_NYSEonly.zip`, `_LiqScreen_VWforce.zip`,
   `_LiqScreen_ME_gt_NYSE20pct.zip`, and `PlaceboPortsFull.zip`** — I enumerated all sixteen files in
   CZ's "Full Sets Alt" folder with their Drive IDs (decoded from the folder's `_DRIVE_ivd` payload;
   IDs recorded in `data/D3_measure_same_signal.py`) and downloaded **four**. `PlaceboPortsFull.zip`
   is where `GPlag`, `OperProfLag`, `OperProfRDLagAT` and `CBOperProfLagAT` live — **the lagged-
   deflator members. I did not measure a single lagged-deflator portfolio.**
9. **CZ's `SignalDoc-Browser.html`, `Release Notes 2025.10.docx`, `storage_checks.txt`,
   `storage_checks_part2.txt`, and the `Firm Level Characteristics` folder** — the firm-level
   characteristic files are what a **characteristic** correlation (§11.8) would require.
10. **CZ's GitHub issues 156 and 174**, linked from openassetpricing.com's own data page, and the
    repository's commit history for `OperProf.do`'s ambiguous comment.
11. **`P4`'s Figure 1 values** — they are in a plot and `C1` recorded the same limitation.
12. **French's `25_Portfolios_BEME_OP_5x5`, `32_Portfolios_ME_BEME_OP`, `16_Portfolios_ME_BEME_OP_INV`
    and the OP breakpoint file itself** — I read their documentation pages but downloaded only
    `Portfolios_Formed_on_OP`, `100_Portfolios_ME_OP_10x10` and the FF5 factors.
13. **AQR's published QMJ factor series**, which would have allowed a third cross-team correlation of
    a composite against both definitions.
14. **Anything on whether the deflator choice interacts with transaction costs or borrow**, which is
    where this programme's constraint bites and which I did not look for at all.

---

## 13. MY VIEW, LABELLED AS A VIEW AND NOT A FINDING

The slate invites this and requires it be marked. **None of the following is established by anything
above; it is what I would do, with reasons, and the principal should read it as an opinion.**

For a cash-funded, equal-weighted, small-to-mid, long-only book with borrow excluded, I would build
**gross profits over current total assets**, and I would not build Fama–French's operating
profitability — but **not** for the reason `F1` appears to offer.

My reasons, in order of how much weight I put on them.

1. **Computability, which is not a preference but a constraint.** `C1` measured gross profit at
   **2,082** filers on as-filed SEC XBRL in 2025, operating profitability at **1,066**, and
   cash-based operating profitability at **nine**. Whatever the literature says about which
   definition is best, two of the three are not buildable at this programme's breadth from its data
   route. **That argument alone decides it, and it has nothing to do with `F1`.**
2. **Fewer estimated components is fewer places for the construction to move.** `REVT − COGS` is two
   tags. French's OP is four tags plus a book-equity construction that itself takes five Compustat
   items with three fallbacks, plus an undocumented minority-interest term (§1.3), plus a
   zero-if-missing rule on three expense items that `P3` states and French's own stock screen
   implies. **Every one of those is a node, and `C2`'s measured dispersion across defensible
   constructions was 68–96% of the premium.**
3. **I distrust the asset deflator's own strongest result, and I would carry that distrust into the
   book.** `P4` and `P3` agree that `GP/TA` = `GP/AT₋₁` ÷ asset growth and `GP/TA` = `GP/BE` ×
   leverage — so the measure I am recommending is **explicitly a composite** of profitability with
   investment and with leverage, and both papers say so. `P3`'s sentence is the honest one: *"Purging
   the investment premium yields an economically small and statistically insignificant gross
   profitability premium."* **I would not tell myself I was buying profitability. I would tell myself
   I was buying profitability-times-low-investment-times-leverage and that the literature cannot
   say which of the three is paying.**
4. **And I would hold the §3.2 result against my own recommendation.** In the microcap and
   all-but-micro equal-weighted buckets — the buckets closest to this programme's universe — the two
   definitions' spreads are **0.01 to 0.13 %/mo apart**, and value-weighted among microcaps the
   *operating* definition is larger. **The case for gross profitability over operating profitability
   is strongest precisely where this programme does not trade.** If the deciding argument were
   performance rather than computability, I would not think the evidence supports a choice at all.

What I would **not** do: treat §6.4's 0.83-versus-0.53 as evidence that `C4` is right and `C3` is
wrong. It is evidence that they measured different things. **Which of the two different things is
worth owning is a separate question that this lane did not ask and did not answer.**

---

## 14. WHAT THIS BRIEF DOES NOT CLAIM

Nothing here closes or admits anything. `F1` is **open** and this brief does not lean on either side
of it; `C3`'s +0.026 [t 0.45] and `C4`'s +0.405 [t 3.00] both stand on the record exactly as written.
No figure from the programme's fixture appears here and none is implied. Both books are unchanged,
nothing is elevated out of `docs/research/`, and the one correction I propose — to `C2`'s attribution
of Mitton's 3.91 — is a correction to a *citation*, not to `C2`'s conclusion that construction
choices move `t`-statistics by as much as the premium itself, which §8's 12.31 and 12.86 support
rather than undermine.
