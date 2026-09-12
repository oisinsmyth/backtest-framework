# `B2` — THE PROFITABILITY FAMILY, IN DEPTH

**Round 2, lane `B2`.** Campaign contract: [`00-SCHEMA.md`](00-SCHEMA.md). Slate:
[`R2-00-slate.md`](R2-00-slate.md). Round 1: [`R1-99-record.md`](R1-99-record.md).

Under [R15](../../RULES.md#r15) **nothing here closes or admits anything**, nothing is elevated into
`FINDINGS.md`, `RULES.md`, the books or a decision record. Both books are unchanged.

---

## 0. THE ANSWER, STATED FIRST AND STATED NEGATIVELY

**The bar asked for one named definition or a finding that the definitions disagree. IT IS BOTH, AND
THE DISAGREEMENT IS THE MORE IMPORTANT HALF.**

1. **The family is not one candidate. It is three signals whose significance is decided by a choice
   that is not part of any of their names: WHETHER THE DEFLATOR IS CURRENT OR LAGGED ASSETS.** Under
   the lagged-asset deflator — which is the one the source paper for operating and cash-based
   profitability *specifies in its own appendix* — **gross profitability drops to `t` 1.04–1.85 and
   operating profitability to `t` 0.33–1.07**, in two independent replications. Cash-based operating
   profitability survives both conventions (`t` 3.02–3.44). **One definition survives. Two do not, and
   they do not fail on cost, era or universe — they fail on one line of construction.** §2, §4.

2. **The surviving definition is CASH-BASED OPERATING PROFITABILITY (`CbOP`), Ball, Gerakos,
   Linnainmaa & Nikolaev (2016), JFE 121(1).** Construction quoted verbatim in §3.1. It is the only
   member that is significant in the proposing paper's own raw value-weighted decile sort, in
   Hou–Xue–Zhang's adversarial replication, in Chen–Zimmermann's independent code, under both
   deflators, under equal AND value weighting, in big stocks alone, and post-2005.

3. **AND THE ONE AUTHORITY THAT DISAGREES IS THE MOST RECENT.** Novy-Marx & Medhat (NBER w33601, Mar
   2025) run the horse race on 1963–2023 and report that **operating profits unpunished for R&D
   SUBSUMES `CbOP`** (`t` 6.99 vs **0.42**), and that post-2000 it *fully* subsumes it. Their
   measures are deflated by **book equity + minority interest**, not assets, and they use
   **cap-weighted WLS**. So the conflict is real and it is again a deflator-and-weighting conflict,
   not an era conflict. **Both sides are interested parties.** §2.4.

4. **LONG-ONLY, WHICH IS THE QUESTION THAT MATTERS HERE: the source literature reports the long leg's
   market-adjusted alpha, and it is `+7` to `+16` bp/month at `t` `0.95` to `1.98`.** Ball et al.'s
   published Table 4 gives CAPM alphas *per decile*: `CbOP` decile 10 **`+0.14` [`t` 1.95]**, decile 1
   **`−0.50` [`t` −4.59]**; operating profitability decile 10 **`+0.07` [`t` 0.95]**. **Against a
   market benchmark, 70–77% of the premium is in the short leg and the long leg does not reach
   `t` 1.96.** §5.

5. **THE TWO PRIOR LANES DID NOT ACTUALLY DISAGREE.** `A3`'s `−0.04%/month` is the **cross-sectional
   mean of long-minus-market over all ~170 anomalies**, read verbatim from Chen & Welch's Table 2 by
   me. The *same table's* profitability rows are **`+0.40`, `+0.26`, `+0.14`** long-minus-market,
   post-2005, top-90%-of-cap. `A2`'s `+44 bp` was its own measurement of a raw long leg. **Three
   different objects; no contradiction. §5.1 reconciles them arithmetically.**

6. **COMPUTABILITY INVERTS THE RANKING.** `[MEASURED IN BRIEF]` on SEC `frames`: **`GrossProfit` is
   itself a stable us-gaap tag — `3,346` filers in 2011 to `2,407` in 2025, NO FY2018 break** — so
   gross profitability needs **two tags and survives the collapse** that killed its component legs.
   `CbOP` needs **twelve**, one of which — **deferred revenue — dies exactly at FY2018**
   (`DeferredRevenueCurrent` `1,654` → `801` → `484`), and **`XSGA` is tagged by only ~30% of
   filers**. **The definition with the evidence is the one the data does worst.** §6.

7. **NO SOURCE IN THIS FAMILY REPORTS THE NOMINAL PRICE DISTRIBUTION OF ITS LEGS. CONFIRMED, NOT
   ASSUMED:** Novy-Marx (2013), Ball et al. (2016) and Chen & Welch (2026) contain **zero** instances
   of "share price", "price screen" or "`$5`" — I grepped the extracted text of all three. §7.

**The precise negative I would put above all of this:** the profitability family's long-short results
rest on a deflator choice that the proposing papers themselves disagree about, the reference
implementation's own source code records that disagreement in a comment, and the one definition that
is robust to it is the one whose tag list breaks.

---

## 1. SOURCES — TYPE, AND HOW WELL ESTABLISHED

| # | source | type | established |
|---|---|---|---|
| `P1` | **Novy-Marx**, *The other side of value: The gross profitability premium*, **JFE 108(1), 2013** — the published article, 28 pp, extracted locally with `pypdf` | [PEER-REVIEWED] | **[read in full]** — construction footnote 2, §2.2, Tables 2–4, footnote 3 and Appendices A.2–A.6 read verbatim |
| `P2` | **Ball, Gerakos, Linnainmaa & Nikolaev**, *Accruals, cash flows, and operating profitability in the cross section of stock returns*, **JFE 121(1), 2016, pp. 28–45** — the published article, 18 pp, `anderson.ucla.edu` mirror | [PEER-REVIEWED] | **[read in full]** — §3 (Data), Tables 1–5, Fig. 2 discussion and the Appendix read verbatim |
| `P2d` | **The same paper's 17 Apr 2015 DRAFT**, 47 pp, `ivey.uwo.ca` mirror — sample ends Dec 2013 | [WORKING PAPER] | **[read in full]** of its Tables 3–4 and appendix, **compared line by line against `P2`** (§3.3) |
| `P3` | **Hou, Xue & Zhang**, *Replicating Anomalies*; text read = **NBER w23394 (May 2017)**, 130 pp; published RFS 33(5) 2020 | [WORKING PAPER] for the text I read | **[read in full]** — §3.2.4 (Profitability) and Appendices A.4.9–A.4.20 read verbatim; Table 4's `Gpa`/`Cop`/`Cla` columns transcribed by me |
| `P4` | **Chen & Zimmermann**, *Open Source Cross-Sectional Asset Pricing*, **FEDS 2021-037** (Federal Reserve Board), 66 pp | [WORKING PAPER] / primary data doc | **[read in full]** — §2.2–2.3, §5.2–5.3, Table 2 and the "Indirect Evidence" appendix table read verbatim |
| `P4c` | **The same project's SOURCE CODE**, `github.com/OpenSourceAP/CrossSection`, `Signals/pyCode/Predictors/CBOperProf.py` + the 771-path repo tree | [SOFTWARE DOC] | **[read in full]** — the whole predictor file, quoted verbatim in §2.3 |
| `P5` | **Novy-Marx & Velikov**, *A Taxonomy of Anomalies and Their Trading Costs*; text read = **NBER w20721 (Dec 2014)**, 61 pp; published RFS 29(1) 2016. **Novy-Marx discloses he "currently consults with Dimensional Fund Advisors"** | [WORKING PAPER] — **interested** | **[read in full]** of Table 3 Panel A; the `Gross Profitability` row transcribed by me and it matches `A2`'s inherited figure exactly |
| `P6` | **Novy-Marx & Medhat**, *Profitability Retrospective: What Have We Learned?*, **NBER w33601 (Mar 2025)**, 78 pp. **Medhat is at Dimensional Fund Advisors; Novy-Marx authored the measure under review** | [WORKING PAPER] — **interested on both counts** | **[read in full]** of Appendix B (Tables B1–B4) and §§2–4; Table A5's layout is mangled by extraction and I flag it where used |
| `P7` | **Chen & Welch**, *What Useful Alphas?*, **arXiv 2607.06502 v1, 8 Jul 2026** — the paper `A3`/`A2` used as `S1` | [WORKING PAPER] | **[read in full]** — **Table 2 and Table 3 re-extracted and transcribed by me, independently of round 1** |
| `P8` | **Jensen, Kelly & Pedersen**, *Is There a Replication Crisis in Finance?*; text read = **NBER w28432 (Feb 2021)**, 54 pp; published JF 78(5) 2023 | [WORKING PAPER] for the text I read | **[partially read]** — §§ on size groups and theme clusters read in full, **but its profitability numbers live in BAR CHARTS and I could extract only the ORDERING of labels, not values** (§2.5) |
| `P9` | **Chen & Velikov**, *Zeroing In on the Expected Returns of Anomalies*, **JFQA 58(3), 2023, pp. 968–1004** (open access) | [PEER-REVIEWED] | **[read in full]** — and it contains **no** "Long − Mkt" column and **no** "Standard universe"; **it is not the source of round 1's long-leg numbers** (§5.1) |
| `M1` | **My own `frames` census** of 33 us-gaap tags × 11 years, with two negative controls, `data/B2_profitability_tag_census.json` | `[MEASURED IN BRIEF]` | endpoint and script in `data/B2_tagcensus.py` |
| `M2` | **My own tag-INTERSECTION measurement** — how many filers carry every tag a definition needs, 5 years, `data/B2_profitability_tag_intersections.json` | `[MEASURED IN BRIEF]` | script in `data/B2_intersect.py` |

**Sources I could NOT obtain, named here so nobody mistakes them for established.**
**`Ball, Gerakos, Linnainmaa & Nikolaev (2015), "Deflating profitability", JFE 117(2)` — the source
paper for OPERATING profitability — I could not get the full text** (four routes, §10.1). Its
construction is established here only at **second hand, from three independent restatements**
(`P2`'s Appendix, `P3`'s A.4.15, `P6`'s Table B1) which agree. **Novy-Marx & Velikov, *Assaying
Anomalies* (SSRN 4338007)** — not obtained, as in round 1; the only `assayinganomalies` PDF I
retrieved is the **Monetary-Policy-Exposure online appendix**, which is a methodology template and
carries no profitability number. **Detzel, Novy-Marx & Velikov (2023 JF)** — paywalled; its abstract
claim that cost-adjusted models "employing cash profitability perform better still" is
**[abstract only, via a search summariser] and is NOT used as a figure anywhere in this brief.**

**No asset-manager publication is cited for any return.** `alphaarchitect.com`, `medium.com`,
`summitward.com`, `etftrends.com` and `larryswedroe.substack.com` surfaced on profitability searches
and are **[SALES INSTRUMENT]**; none is cited. **`P5` and `P6` both carry Dimensional disclosures and
`P6`'s second author is a Dimensional employee — I treat `P6`'s verdict against `CbOP` as interested
testimony and say so every time I use it.**

---

## 2. `Q1` — WHICH DEFINITION SURVIVES, REPORTED SEPARATELY AND NEVER POOLED

### 2.1 The three definitions are not three flavours of one thing

| | gross profitability | operating profitability | cash-based operating profitability |
|---|---|---|---|
| **numerator** | `REVT − COGS` | `REVT − COGS − (XSGA − XRD)` | operating profits **minus accruals** |
| **source** | Novy-Marx (2013) `P1` | Ball et al. (2015) — **paper not obtained** | Ball et al. (2016) `P2` |
| **deflator, as the source states it** | **total assets, CURRENT** (`P1` footnote 2, read in full) | **assets lagged one year** (`P2` App., restating 2015) | **assets lagged one year** (`P2` App., read in full) |
| **line items** | 3 | 5 | **12** |
| **a competing definition exists** | `GP/AT` vs `GP/AT₋₁` | `/AT₋₁` vs `/AT`, **and Fama–French's `/BE` with interest expense** | `/AT₋₁` vs `/AT`; balance-sheet vs cash-flow-statement accruals |

**Fama & French's operating profitability is a FOURTH definition, not the same one.** Ken French's own
portfolio documentation, `[read in full]` at `mba.tuck.dartmouth.edu/.../det_port_form_op.html`,
defines it as *"annual revenues minus cost of goods sold, interest expense, and selling, general, and
administrative expenses divided by **book equity**"*, with *"OP for June of year `t`"* using *"book
equity for the last fiscal year end in `t−1`"*, **NYSE breakpoints**. **It subtracts interest expense,
does not undo Compustat's folding of R&D into `XSGA`, and divides by EQUITY not ASSETS.** `P3` names
this variable `Ope` and reports it **insignificant** (§2.2).

### 2.2 The headline numbers, never pooled, each with its sample and weighting

**All value-weighted, NYSE breakpoints, annual June rebalance, financials excluded, unless stated.**

| definition | construction scored | sample | long−short | `t` | source, how established |
|---|---|---|---|---|---|
| **gross profitability** | `GP/AT` **current**, VW **quintiles** | 1963-07→2010-12 | **0.31** | **2.49** | `P1` Table 2 **[read in full]** |
| gross profitability | `GP/AT` current, VW **deciles** (`Gpa`) | 1967-01→2014-12 | 0.38 | 2.62 | `P3` Table 4 row 120 **[read in full]** |
| gross profitability | `GP/AT₋₁` **lagged** (`Gla`), VW deciles | 1967→2014 | **0.16** | **1.04** | `P3` §3.2.4 **[read in full]** |
| gross profitability | `GP/AT₋₁` (`GPlag`), **EW quintiles** | orig. in-sample | **0.20** | **1.85** | `P4` appendix table **[read in full]** |
| **operating profitability** (R&D-adj, `/AT`) | `Opa`, VW deciles | 1967→2014 | **0.37** | **1.87** | `P3` §3.2.4 **[read in full]** |
| operating profitability, **as its own paper sorts it** | VW deciles, 10−1 | 1963-07→2014-12 | **0.29** | **1.84** | **`P2` Table 4 Panel A [read in full]** |
| operating profitability (`/AT₋₁`, `Ola`) | VW deciles | 1967→2014 | **0.20** | **1.07** | `P3` §3.2.4 **[read in full]** |
| operating profitability (`/AT₋₁`, `OperProfRDLagAT`) | **EW quintiles** | orig. in-sample | **0.05** | **0.33** | `P4` appendix table **[read in full]** |
| Fama–French `Ope` (`/BE`, with `XINT`) | VW deciles | 1967→2014 | **0.25** | **1.2** | `P3` §3.2.4 **[read in full]** |
| FF `Ope` lagged (`Ole`) | VW deciles | 1967→2014 | **0.07** | **0.37** | `P3` §3.2.4 **[read in full]** |
| **cash-based operating profitability** | VW **deciles** 10−1 | 1963-07→2014-12 | **0.47** | **3.17** | **`P2` Table 4 Panel A [read in full]** |
| cash-based operating profitability | VW **quintiles** | 1963-07→2013-12 | **0.377** | **3.33** | `P2d` draft Table 4 **[read in full]** |
| cash-based operating profitability (`Cop`, `/AT`) | VW deciles | 1967→2014 | **0.63** | **3.44** | `P3` Table 4 row 119 **[read in full]** |
| cash-based operating profitability (`Cla`, `/AT₋₁`) | VW deciles | 1967→2014 | **0.53** | **3.02** | `P3` Table 4 **[read in full]** |
| cash-based operating profitability (`CBOperProfLagAT`) | **EW quintiles** | orig. in-sample | **0.46** | **3.33** | `P4` appendix table **[read in full]** |

**Read the `t`-statistics column top to bottom. Nine of the fourteen rows are below 1.96, and every
one of them is a gross or operating profitability row.** `CbOP` is below 1.96 in none of them.

**`P3`'s own sentence on why the gross/operating rows fail, `[read in full]`:** *"Because both profits
and assets are measured at the end of a period in Compustat, profits should be scaled by lagged
assets, which in turn produce current profits… because `Gpa` equals `Gla` divided by asset growth
(current assets-to-lagged assets), the `Gpa` effect is confounded with the investment effect. Purging
the investment effect yields an economically small and statistically insignificant `Gla` effect."`

**This is not a replication quibble. It is an identity:** `GP/AT = (GP/AT₋₁) ÷ (AT/AT₋₁)`. **Gross
profitability measured against current assets is arithmetically gross profitability times the
reciprocal of asset growth** — and asset growth is a separate, documented anomaly that this programme
could compute from `Assets` alone. **`P3`'s `Gpa` is partly an investment signal in a profitability
costume.** `P3` Table 4 makes the same point a second way: `Gpa`'s **q-factor alpha is `0.18` with
`t` `1.24`** — its mean return survives a `t` test and its alpha against investment-and-ROE does not.
`Cop`'s q-alpha is **`0.69`, `t` `4.77`**.

**Cost-honest, on the one member for which a cost-honest number exists.** `P5` Table 3 Panel A,
VW decile long/short, NYSE breakpoints, 1963–2012, **transcribed by me [read in full]**:

> `Gross Profitability` — gross `0.40` [`2.94`], `αFF4` gross `0.52` [`3.83`], **turnover `1.96`**,
> **T-costs `0.03`**, **net `0.37` [`2.74`]**, `αFF4` net `0.51` [`3.77`]

**`P5` predates `P2`. There is no cost-honest long/short number for `CbOP` in any source I obtained.**
`P5`'s own summary sentence, read in full, is that *"only the net issuance, earnings momentum strategy…
and momentum and its derivative anomalies, achieve net excess returns that are statistically
significantly larger than zero"* — and **gross profitability is not in that list**, despite its net
`t` of 2.74, because `P5`'s significance claim is about the *net minus gross* difference. I record the
tension rather than resolve it: **the table says net `t` 2.74; the text's survivor list omits it.**

### 2.3 The reference implementation's own source code records the ambiguity

`P4c`, `Signals/pyCode/Predictors/CBOperProf.py`, **quoted verbatim**:

```python
# some confusion about lagging assets or not
# OP 2016 JFE seems to lag assets, but 2015 JFE does not
# Yet no lag implies results much closer to OP
```

and the line that follows it:

```python
df["CBOperProf"] = df["CBOperProf"] / df["at"]      # CURRENT assets
```

**The most-used public implementation of `CbOP` divides by CURRENT assets against the published
paper's stated `t−1`, and its authors wrote down that they chose the version whose results matched
the target table.** They ship the lagged version as `Placebos/CBOperProfLagAT.py` — **a placebo, not a
predictor.** For `CbOP` this is survivable (`0.46`/`3.33` lagged vs `0.46`/`3.20` current in `P4`'s own
table). **For gross and operating profitability it is the whole result.**

Two further things that file establishes, and that a summary would not have:
- **`revt` and `cogs` are among the variables filled with zero when missing** (`zero_fill_vars`
  includes `revt`, `cogs`, `xsga`, `xrd`, `rect`, `invt`, `xpp`, `drc`, `drlt`, `ap`, `xacc`). A firm
  with missing revenue is scored as having zero revenue, not dropped.
- **`xpp` (prepaid expenses) IS in the implementation.** Round 1's `A2` tag list for `CbOP`
  (`revt, cogs, xsga, xrd, rect, invt, drc, drlt, ap, xacc, at`) **omits `xpp`**. That is a real gap
  of one accrual term, and I correct it here rather than inherit it.

### 2.4 THE CONFLICT: the most recent authority says the opposite, and both sides are interested

`P6` (Novy-Marx & Medhat, Mar 2025) Table B3, **read in full**. Fama–MacBeth, **WLS with market cap as
weight**, all measures scaled by **book equity + minority interest**, 1963-07→2023-12, trimmed at 1%/99%:

| specification | `OP` | `OP_R&D` | `COP` | `COP_R&D` |
|---|---|---|---|---|
| (1)–(4) univariate | 0.88 [5.85] | **1.10 [7.91]** | 0.35 [4.57] | 0.47 [6.60] |
| (5) `OP_R&D` vs `OP` | −1.00 [**−1.96**] | **1.99 [4.11]** | | |
| (6) `OP_R&D` vs `COP` | | **1.09 [6.99]** | **0.04 [0.42]** | |
| (7) `OP_R&D` vs `COP_R&D` | | **0.90 [5.69]** | | 0.22 [2.57] |

and, verbatim: *"Table D1 in the Internet Appendix repeats the regression in Table B3 for two
sub-periods split at the year 2000. It shows results similar to those for the full sample in the early
period but **even stronger results in the late period, during which `OP_R&D` fully subsumes
`COP_R&D`**."*

**Against `P2` Table 2 column 7, read in full, the same horse race on 1963–2014 with assets as the
deflator and OLS split by size group: `CbOP` `t` `5.27`, operating profitability `t` `1.56`.** `P2`'s
text: *"operating profitability loses most of its predictive power and its `t`-value decreases to 1.56.
Cash-based operating profitability wins this horse race with a `t`-value of 5.27."*

**WHAT DIFFERS, SO THAT NOBODY READS THIS AS AN ERA EFFECT:** (i) **deflator** — `BE + MIB` vs
**lagged assets**; (ii) **estimator** — cap-weighted WLS vs OLS run separately on all-but-microcaps
and microcaps; (iii) **numerator** — `P6`'s `OP_R&D` subtracts **interest expense** and `P2`'s does
not; (iv) sample end 2023 vs 2014. **`P6` changes three things at once and reports the aggregate.**

**WHICH I WOULD WEIGHT, AND WHY.** For *this* programme: **`P2`+`P3`+`P4`, i.e. `CbOP`.** Three
reasons, all about this book rather than about the literature. **(a) Independence of the replication.**
`P3` is an adversarial replication by authors whose thesis is that most anomalies fail, and it
*confirms* `CbOP` at `t` 3.02–3.44 while killing `Gpa`-lagged, `Opa`, `Ola`, `Ope` and `Ole`. `P4` is a
third team's code and agrees. `P6` is a single team, one of whom authored the losing measure and the
other of whom works for a manager selling the winning one. **(b) The estimator.** `P6`'s WLS
cap-weighting is the *opposite* of this programme's equal weighting; a result that requires
cap-weighted WLS is a result about mega-caps. **(c) The deflator.** `P6`'s `BE + MIB` needs a book-
equity chain that §6 shows is the least stable thing in XBRL. **I record `P6` as unresolved, not
wrong. If the principal wants one number to carry forward it is `CbOP`; if the principal wants one
number to be nervous about, it is `P6`'s `[0.42]`.**

### 2.5 What `P8` adds, and the honest limit on it

`P8` (Jensen–Kelly–Pedersen) is the one large study that *defends* the literature — 84.0% US
replication rate, **77.3% in mega stocks, 81.5% in large stocks**, read verbatim. **But its
profitability numbers are in bar charts.** From the label ORDER alone — these figures are sorted, and
the label sequence is all the PDF text carries — **"Profitability" sits 5th from the bottom of 13
themes in Figure 4's replication rates and 4th from the bottom of 13 in Figure 11 Panel A's
size-group alphas, below Value, Quality, Momentum, Low Risk, Investment, Accruals and Debt
Issuance.** **I did not read a single profitability value from `P8` and I am not reporting one.** The
ordering is `[snippet only]` in effect and it is a *negative* for profitability, not a positive.

---

## 3. `Q3` — THE EXACT CONSTRUCTION, VERBATIM, PRECISELY ENOUGH TO IMPLEMENT

### 3.1 Cash-based operating profitability — `P2`'s Appendix, QUOTED

> *"This appendix describes how we define operating profitability, cash-based operating profitability,
> and accruals. **All three variables are deflated by the book value of total assets in year `t−1`.**
> The names of Compustat variables are provided in parentheses.*
>
> **Operating profitability**
> *The definition of operating profitability follows Ball, Gerakos, Linnainmaa and Nikolaev (2015):*
>
> *Operating profitability ≡ Revenue (REVT) − Cost of goods sold (COGS) − Reported sales, general, and
> administrative expenses (XSGA − XRD),*
>
> *in which "Reported sales, general, and administrative expenses" subtracts off expenditures on
> research and development to undo the adjustment that Standard & Poor's makes to firms' accounting
> statements.*
>
> **Cash-based operating profitability**
> *We convert operating profitability to a cash basis by adding or subtracting changes in the balance
> sheet items associated with the income statement items that enter the calculation of operating
> profitability,*
>
> *Cash-based operating profitability = Operating profitability − Δ(Accounts receivable (RECT)) −
> Δ(Inventory (INVT)) − Δ(Prepaid expenses (XPP)) + Δ(Deferred revenue (DRC+DRLT)) + Δ(Trade accounts
> payable (AP)) + Δ(Accrued expenses (XACC)).*
>
> ***All changes are computed on a year-to-year basis. Instances where balance sheet accounts have
> missing values are replaced with zero values for the computation of cash-based operating
> profitability.***
>
> *In Table 3, we use cash flow statement accruals to convert operating profitability to a cash basis,*
>
> *Cash-based operating profitability = Operating profitability + Decrease in accounts receivable
> (RECCH) + Decrease in inventory (INVCH) + Increase in accounts payable and accrued liabilities
> (APALCH)."*

**`P3`'s A.4.18 restates the same formula and differs on exactly one word** — *"all scaled by book
assets (item AT, **the denominator is current, not lagged**, total assets)"* — while claiming to
follow `P2`. **`P6`'s footnote 31 restates it a third time and agrees with `P2` on every sign.** Three
independent statements, one disagreement, and it is the deflator.

**Winsorisation / trimming, verbatim from `P2`:** *"we… follow Novy-Marx (2013) and Ball, Gerakos,
Linnainmaa and Nikolaev (2015) in trimming all independent variables to the 1st and 99th
percentiles… we trim on a consistent table-by-table basis, with the exception of column 1."*
**`P1` footnote to Table 1: *"Independent variables are trimmed at the 1% and 99% levels."*** Both
**trim** (drop), not winsorise (clip). **Trimming applies to the regressions; the portfolio sorts in
`P1` Table 2 and `P2` Table 4 are NOT described as trimmed.** That distinction is load-bearing and
every source leaves it implicit.

**Sample filters, verbatim from `P2` §3:** *"all firms traded on NYSE, Amex, and Nasdaq, and exclude
securities other than ordinary common shares… if a delisting return is missing and the delisting is
performance-related, we impute a return of −30%… We exclude financial firms, which are defined as
firms with one-digit Standard Industrial Classification codes of six"*, and — a filter that changes
the universe — *"we include only those stocks with non-missing values for all three variables"*
(OP, accruals, `CbOP`).

### 3.2 THE LAG CONVENTION, WHICH IS THE LOOK-AHEAD RISK — AND THE SOURCES DO NOT AGREE

**Four conventions, all in use, quoted:**

| convention | verbatim | who | what it means for look-ahead |
|---|---|---|---|
| **Fixed June, FY in calendar `t−1`** | `P1`: *"employ accounting data for a given fiscal year starting **at the end of June of the following calendar year**"* | Novy-Marx; Ken French's OP portfolios; `P3` (*"At the end of June of each year `t`, we sort stocks into deciles based on `Cop` for the fiscal year ending in calendar year `t−1`"*) | **Safe but wasteful.** A Dec FYE gets a 6-month lag; a **Jan FYE gets 17 months**. |
| **Rolling six-month lag** | `P2`: *"we… **lag annual accounting information by six months.** For example, if a firm's fiscal year ends in December, we assume that this information is public by the end of the following June."* | `P2`'s Fama–MacBeth regressions | **Safe for Dec FYE; a 10-K is due 60–90 days after FYE, so 6 months clears it.** |
| **BOTH, in the same paper** | `P2`: *"In Fama and MacBeth (1973) regressions, we **re-compute the explanatory variables every month**… In portfolio sorts, we **rebalance the portfolios annually at the end of June**."* | `P2` | **`P2`'s regression `t`-statistics and its portfolio `t`-statistics are on two different signals.** |
| **Actual report date** | `P1` App. A.4: the quarterly strategy is *"formed on the basis of `(REVTQ − COGSQ)/ATQ`… **employed starting at the end of the month following a firm's report date of quarterly earnings, item RDQ**"* | `P1`; `P4` *"in a couple cases"* | **The only genuinely point-in-time convention — and the only one XBRL gives natively.** |

**`P4`'s standard, verbatim:** *"For almost all characteristics, we use the **standard six-month lag**
for annual accounting data availability and a **one-quarter lag** for quarterly accounting data
availability… **the accounting data lag is imposed in the data download step, and is not visible in
the files that generate characteristics.**"*

**The operational consequence for this programme, stated plainly.** A fixed-June formation is what
every headline number in §2.2 was computed under. A six-month rolling lag is what `P4`'s portfolios —
and therefore `A2`'s round-1 measurements — were computed under. **These are not interchangeable, and
neither is what an XBRL build would naturally produce**, because XBRL hands you the **filing
acceptance date**, which is the `RDQ` convention and is *earlier* than both. **Using the filing date
would make the signal fresher than any published result and would therefore not be a replication of
any of them.** Conversely it is the only convention with no look-ahead by construction.

### 3.3 The draft-versus-published check, run because the campaign requires it

**`P2d` (17 Apr 2015 draft, sample to Dec 2013) against `P2` (published, to Dec 2014):**

| quantity | draft `P2d` | published `P2` | verdict |
|---|---|---|---|
| OP decile 10−1, excess | 0.289 [1.84] | 0.29 [1.84] | agree |
| `CbOP` decile 10−1, excess | 0.474 [3.16] | 0.47 [3.17] | agree |
| `CbOP` decile 10, FF3 α | 0.347 [5.90] | 0.35 [5.98] | agree |
| `CbOP` decile 1, FF3 α | −0.556 [−6.75] | −0.55 [−6.67] | agree |
| accruals decile 10−1 | −0.384 [−2.76] | −0.35 [−2.55] | agree in sign and size |
| Appendix formula, incl. `Δ(XPP)` | present | present | agree |
| **CAPM alphas per decile** | **absent** | **present** | **the published version is the ONLY place the long leg is measured against the market** |
| **quintile 10−1 row** | **present** (`CbOP` 0.377 [3.33]; OP 0.218 [1.87]) | **absent** | **the draft is the only place the quintile sort is reported** |

**No sign disagreement and no magnitude disagreement. Each version carries one number the other does
not, and both of those numbers are used above.** This is the cleanest draft/published comparison in
this campaign so far and it is a *negative* result for the hazard — which is worth recording too.

---

## 4. `Q1` CONTINUED — ERA, AND WHAT "POST-2005 COST-HONEST" ACTUALLY EXISTS

**There is no post-2005, cost-honest, leg-decomposed, equal-weighted result for any profitability
definition in any source I obtained.** What exists is four partial things, and I name which part each
supplies.

1. **Post-2005, top-90%-of-cap, long-short AND long-minus-market — `P7` Table 2, transcribed by me
   [read in full]:**

   | signal | LS %/mo | **Long − Mkt %/mo** | shrunk LS | shrunk Long−Mkt |
   |---|---|---|---|---|
   | Cash-based oper. profitability | **0.66** | **0.40** | 0.06 | 0.00 |
   | Oper. profit. (R&D adj) | 0.60 | 0.26 | 0.05 | 0.00 |
   | Gross profitability | 0.44 | 0.14 | 0.04 | 0.00 |
   | **mean, all 170 anomalies** | **0.08** | **−0.04** | 0.01 | 0.00 |

   and `P7` Table 3: **`Profitability` is the only category with a healthy median — `N` 9, mean 0.25,
   median 0.24, 25th 0.09, 75th 0.44, 78% positive** — against `Value/Fundamentals` −0.02/−0.04/47%
   and `Momentum` 0.01/0.05/53%. **No costs. No legs other than long−mkt. No `t`-statistics per
   signal.**

2. **Cost-honest, but 1963–2012 and long-short only — `P5`, §2.2: gross profitability net `0.37`,
   `t` `2.74`, one-sided monthly turnover `1.96%`, T-costs `0.03%/month`.** Nothing for `CbOP`.

3. **Post-2000 split, but cap-weighted WLS and `BE`-deflated — `P6`'s Table D1 statement that
   `OP_R&D` FULLY SUBSUMES `COP_R&D` post-2000.** I did not obtain the Internet Appendix table itself;
   **this is `[read in full]` of the sentence describing it, not of the numbers.**

4. **Rolling `t`-statistics through 2014 — `P2` Fig. 1, ten-year rolling Fama–MacBeth `t`s for OP,
   accruals and `CbOP`, All-but-microcaps.** I read the description, not the plotted values.

**THE ARITHMETIC THIS PROGRAMME ACTUALLY NEEDS, and it is mine, not theirs.** `P5`'s one-sided monthly
turnover for an annually-rebalanced profitability sort is **1.96%**. At this programme's own measured
**67.6 bp round trip**, a long-only book turning over 1.96% of its capital a month pays
**1.96% × 67.6 bp ≈ 1.3 bp/month ≈ 16 bp/year**. Against `P7`'s post-2005 long-minus-market of
**14–40 bp/month** for this family, **cost is 3–9% of the gross.** `[MY ARITHMETIC on P5's turnover
and the programme's own cost figure — not a number from any paper.]`

**That is the single most favourable fact in this brief, and it says the opposite of what round 1's
framing implied: for THIS family, at THIS turnover, cost is not the binding constraint. The binding
constraint is whether the long leg has a positive expected return at all.** §5.

---

## 5. `Q2` — LONG-ONLY EVIDENCE FOR THE SURVIVING DEFINITION, AND THE BENCHMARK FOR EVERY FIGURE

### 5.1 First, the reconciliation the slate asked for

**`A3`'s `−0.04%/month` and `A2`'s `+44 bp` are not in conflict because they are not the same object.**
I re-extracted `P7` myself to check, and `P7` Table 2's own note, **verbatim**:

> *"Mean Long – Mkt is the mean signal-month return of the long leg minus the raw Fama-French market
> return, computed as Mkt – RF plus RF… For LS returns, `Var(t) = 1.09` implies a factor of about
> 0.084. For Long – Mkt returns, `Var(t) = 0.98` is below 1, so the factor is zero, and every adjusted
> mean is zero. **The last two rows report the cross-sectional mean and standard deviation of each
> column across all ∼170 anomalies, not only the top 10.**"*

So:
- **`−0.04%/month` is the MEAN OVER ~170 ANOMALIES of long-minus-market.** It is not a profitability
  number and `P7` never claims it is.
- **The same column gives profitability `+0.40`, `+0.26`, `+0.14`.** Those three are among the highest
  values in a 170-row column whose SD is `0.13`. **`CbOP`'s `+0.40` is ~3.4 SD above that column's
  mean.**
- **`A2`'s `+44 bp, t 2.48` was its own measurement** on `P4`'s portfolio files under a `$5` screen —
  a raw long-leg return, not long-minus-market, shrunk by `A2` itself to `15 bp`.
- **And `15 bp` is what you get independently from `P2`'s published table.** `P2` Table 5 gives the
  market's average annualised excess return as **6.09%**, i.e. **0.5075%/month**. `P2` Table 4's
  `CbOP` decile-10 excess return is **0.64%/month**. **`0.64 − 0.51 = +0.13%/month` long-minus-market
  — and `P2`'s own CAPM alpha for that decile is `+0.14`.** `[MY ARITHMETIC on P2's Tables 4 and 5.]`
  **`A2`'s shrunk `15 bp` and `P2`'s published `14 bp` agree to one basis point, by two completely
  different routes.**

**`P9` — which round 1 catalogued as `S1` — does not contain the "Long − Mkt" column or the "Standard
(N3000, 90%)" universe at all.** I grepped the full extracted text of the published JFQA article:
zero hits for `Long – Mkt`, `Standard universe`, `top 90`. **Round 1's `S1` is `P7` (Chen & Welch),
and its source table is attributed correctly in `R1-02`'s source list; I note it only so that nobody
later looks for these numbers in Chen & Velikov.**

### 5.2 THE LEG NUMBERS THE SOURCE LITERATURE ACTUALLY REPORTS, WITH THE BENCHMARK NAMED

**`P2` Table 4 Panel A, read in full. VW, NYSE decile breakpoints, annual June rebalance,
1963-07→2014-12, financials excluded.** This is the only place in the family's literature where a leg
is measured against the market.

| | operating profitability | | | cash-based operating profitability | | |
|---|---|---|---|---|---|---|
| decile | excess ret | **CAPM α** | FF3 α | excess ret | **CAPM α** | FF3 α |
| **10 (long)** | 0.58 [2.98] | **0.07 [0.95]** | 0.29 [4.80] | 0.64 [3.37] | **0.14 [1.95]** | 0.35 [5.98] |
| **1 (short)** | 0.29 [1.13] | **−0.35 [−2.89]** | −0.45 [−4.33] | 0.16 [0.63] | **−0.50 [−4.59]** | −0.55 [−6.67] |
| **10 − 1** | 0.29 [1.84] | 0.42 [2.81] | 0.74 [5.98] | 0.47 [3.17] | 0.65 [4.74] | 0.89 [8.48] |

**And Panel B, split at the NYSE median:**

| | OP 10 | OP 1 | OP 10−1 | `CbOP` 10 | `CbOP` 1 | `CbOP` 10−1 |
|---|---|---|---|---|---|---|
| **Small**, excess | 1.04 [3.99] | 0.26 [0.82] | 0.78 [5.72] | 1.13 [4.37] | 0.26 [0.84] | 0.87 [7.48] |
| **Big**, excess | 0.55 [2.83] | 0.37 [1.73] | **0.17 [1.21]** | 0.65 [3.41] | 0.22 [0.94] | **0.43 [3.31]** |
| **Big, CAPM α** | 0.06 [0.67] | −0.18 [−1.79] | 0.23 [1.63] | **0.16 [1.98]** | **−0.38 [−4.30]** | 0.55 [4.34] |

**What this says, stated against the benchmark each time:**

- **Against the VALUE-WEIGHTED MARKET (CAPM α), the long leg of the best definition earns
  `+14 bp/month`, `t` `1.95`, over 51½ years.** It does not clear 1.96. In big stocks alone it is
  `+16 bp`, `t` `1.98` — it clears 1.96 by 0.02.
- **`0.50 / 0.65 = 77%` of `CbOP`'s CAPM alpha is in the SHORT leg.** In big stocks, `0.38/0.55 = 69%`.
- **Against FF3 — a benchmark containing `SMB` and `HML`, neither of which this programme can hold —
  the long leg's alpha is `+0.35`, `t` `5.98`, i.e. `39%` of the 0.89 spread.** **The long leg's
  apparent strength is entirely a function of which benchmark you choose, and the two choices differ
  by a factor of 2.5 on the share and by a factor of 3 on the `t`.** That is `B1`'s question, arriving
  here as an arithmetic fact rather than an opinion.
- **For OPERATING profitability the long leg has NO market-adjusted alpha at all: `+0.07`, `t`
  `0.95`.** Anyone implementing long-only operating profitability is implementing a zero.

### 5.3 The other long-only evidence, and why I am cautious about it

**`P1` Table 2, read in full — VW quintiles, NYSE breaks, 1963-07→2010-12:** high-GP/A quintile excess
return **`0.62` [`3.12`]**, FF3 α **`+0.34` [`5.01`]**, `βMKT` `0.92`; low quintile excess `0.31`
[`1.65`], FF3 α **`−0.18` [`−2.54`]**. **`0.34/0.52 = 65%` of gross profitability's FF3 alpha is in
the LONG leg — the opposite split from `CbOP`'s CAPM split, because the benchmark is different.**
**`P1` reports no CAPM alphas, so gross profitability's long-minus-market is not available from its
own paper.**

**`P6` Table A5 reports a long-only profitability portfolio** — a 0.8× deleveraged
high-profitability/low-investment book — **with α `0.58` [`4.68`] and `0.52` [`4.22`]**. **I am not
using those as evidence.** Three reasons: the table's column-to-regressor mapping is **mangled by PDF
extraction** so I cannot state which benchmark each α is against; the portfolio **mixes profitability
with investment**, so it is not a profitability long leg; and the authors are interested. **Recorded,
flagged, not relied on.**

### 5.4 The cost-honest long-only number that does not exist

**No source I obtained reports a NET long-only profitability return.** `P5` nets long/short only. `P7`
reports long-minus-market gross. `P2` reports no costs. **The only long-only net figure in this
programme's possession is round 1's `~8 bp/month net on a long-only profitability sort under the `$5`
screen`, which is `A2`'s own measurement and inherits `A2`'s construction.** §4's arithmetic says the
cost term is ~1.3 bp/month at this turnover, so the gap between `A2`'s 8 bp and `P2`'s 14 bp is about
shrinkage and universe, not about cost.

---

## 6. `Q5` — THE COMPUTABILITY DETAIL: WHICH TAGS, AND DO THEY SURVIVE

**`[MEASURED IN BRIEF]`** — `https://data.sec.gov/api/xbrl/frames/us-gaap/{tag}/USD/{CY####|CY####Q4I}.json`,
distinct CIKs per calendar-year frame, `0.25 s` between calls, contact string in the User-Agent.
Script `data/B2_tagcensus.py`, full matrix `data/B2_profitability_tag_census.json`. **Two negative
controls, both behaved:** an invented tag `ZZZZNotATagB2Control` returned **`HTTP404` in all eleven
years** and I report the 404 rather than coercing it to zero (round 1's ninth-flavour trap); a
**wrong-unit control** (`AccountsReceivableNetCurrent` in `EUR`) returned **1–6 entities**, proving the
endpoint is unit-sensitive and alive, so a 404 means "no such frame", not "endpoint broken".

### 6.1 The census, by definition

| concept | us-gaap tag | 2011 | 2015 | 2017 | **2018** | **2019** | 2022 | 2025 | verdict |
|---|---|---|---|---|---|---|---|---|---|
| **gross profit, DIRECT** | **`GrossProfit`** | **3346** | 2881 | 2666 | **2643** | **2698** | 2879 | **2407** | **STABLE. No FY2018 break.** |
| revenue | `Revenues` | 3858 | 3377 | 3875 | 3268 | 2839 | 2792 | 2227 | erodes 42% |
| revenue | `SalesRevenueNet` | 2366 | 2085 | 1649 | **121** | **1** | 404 | 404 | **DEAD** |
| revenue | `RevenueFromContractWithCustomerExcludingAssessedTax` | 404 | 32 | 2146 | 2799 | 3052 | 3228 | 2693 | replacement |
| cost | `CostOfGoodsSold` | 1875 | 1612 | 1296 | **113** | **2** | 404 | 404 | **DEAD** |
| cost | `CostOfGoodsAndServicesSold` | 1067 | 847 | 2099 | 2229 | 2148 | 2012 | 1566 | replacement |
| cost | `CostOfRevenue` | 1401 | 1375 | 1540 | 1444 | 1446 | 1692 | 1458 | stable |
| assets | `Assets` | 8166 | 7018 | 6483 | 6305 | 6180 | 6870 | 6139 | stable |
| **`XSGA`** | **`SellingGeneralAndAdministrativeExpense`** | **2674** | 2304 | 2175 | 2140 | 2140 | 2184 | **1822** | **STABLE BUT THIN — ~30% of `Assets` filers** |
| (not a substitute) | `GeneralAndAdministrativeExpense` | 4226 | 3725 | 3417 | 3347 | 3430 | 3815 | 3073 | **different concept** |
| `XRD` | `ResearchAndDevelopmentExpense` | 2443 | 2427 | 2371 | 2406 | 2542 | 2772 | 2290 | stable; zero-if-missing is correct |
| `RECT` | `AccountsReceivableNetCurrent` | 4094 | 3603 | 3390 | 3347 | 3335 | 3594 | 3111 | stable |
| `INVT` | `InventoryNet` | 3387 | 2961 | 2744 | 2699 | 2674 | 2807 | 2470 | stable |
| `XPP` | `PrepaidExpenseCurrent` | 1770 | 1593 | 1527 | 1489 | 1460 | 1963 | 1633 | stable, **thin** |
| **`DRC`** | **`DeferredRevenueCurrent`** | **1856** | 1770 | **1654** | **801** | **610** | 693 | **484** | **COLLAPSES AT FY2018** |
| **`DRLT`** | **`DeferredRevenueNoncurrent`** | 825 | 876 | **811** | **355** | **281** | 305 | **197** | **COLLAPSES AT FY2018** |
| replacement | `ContractWithCustomerLiabilityCurrent` | 404 | 4 | 1154 | 1664 | 1757 | 2054 | 1899 | post-2017 only |
| replacement | `ContractWithCustomerLiabilityNoncurrent` | 404 | 1 | 529 | 787 | 816 | 897 | 789 | post-2017 only |
| `AP` | `AccountsPayableCurrent` | 4723 | 4150 | 3881 | 3839 | 3803 | 4268 | 3573 | stable |
| (not the Compustat analogue) | `AccountsPayableTradeCurrent` | 437 | 439 | 412 | 416 | 407 | 436 | 364 | **~400 filers only** |
| `XACC` | `AccruedLiabilitiesCurrent` | 3238 | 2910 | 2757 | 2699 | 2639 | 2996 | 2527 | stable |
| `RECCH` | `IncreaseDecreaseInAccountsReceivable` | 4264 | 3769 | 3485 | 3453 | 3566 | 3725 | 3104 | stable |
| `INVCH` | `IncreaseDecreaseInInventories` | 3477 | 3024 | 2821 | 2776 | 2780 | 2908 | 2420 | stable |
| `APALCH` | `IncreaseDecreaseInAccountsPayableAndAccruedLiabilities` | 2937 | 2610 | 2336 | 2272 | 2208 | 2252 | 1685 | stable, erodes 43% |
| **control** | `ZZZZNotATagB2Control` | **404** | **404** | **404** | **404** | **404** | **404** | **404** | correct |
| **control** | `AccountsReceivableNetCurrent` (`EUR`) | 6 | 4 | 3 | 4 | 4 | 4 | 1 | correct |

### 6.2 THE FINDING THAT MATTERS MOST, AND IT WAS NOT EXPECTED

**`GrossProfit` is itself a standard us-gaap tag, reported by 2,407–3,346 filers, and it does not
break at FY2018.** Compustat's `GP` item *is* `REVT − COGS`, and the XBRL taxonomy carries that
subtotal directly. **Gross profitability therefore needs exactly TWO tags — `GrossProfit` and
`Assets` — both of which survive ASC 606, with a four-tag revenue chain × three-tag cost chain only
as a FALLBACK.** Round 1's `R1-01` §7.1 recorded gross profitability as *"Both legs break at FY2018…
Needs a four-tag revenue chain and a three-tag cost chain."* **That is true of the component route and
it understates what is available, because the subtotal tag was not in that census.** `R1-01`'s
collapse finding stands exactly as written; **this is an addition to it, not a correction of it.**

**And the symmetric bad news: the definition with the evidence is the one the tags punish.**
`CbOP` needs twelve tags and **its deferred-revenue term dies at FY2018 in the same event that killed
the revenue tags**: `DeferredRevenueCurrent` `1,654` (2017) → `801` (2018) → `610` (2019) → `484`
(2025), replaced by `ContractWithCustomerLiabilityCurrent` `1,154` → `1,664` → `1,899`.

**This is WORSE than a rename, for a reason specific to `CbOP`'s formula.** `CbOP` uses
**`Δ(DRC + DRLT)`**, a year-on-year difference. Across FY2018 that difference is taken **between two
different tags AND across an accounting-standard change that carries a cumulative-effect transition
adjustment to the opening balance.** The result is a **one-time mechanical jump in one of `CbOP`'s six
accrual terms, for ~1,700 filers, concentrated in subscription and software businesses — i.e. it
differs by industry and will therefore look like a real cross-sectional effect.** This is
structurally identical to `R1-01`'s ASC 842 finding on `Assets`, and it needs the same treatment: a
named transition control across the adoption year, or `CbOP` is not measurable across FY2018–2019.

### 6.3 The intersection: how many filers carry EVERYTHING a definition needs

**`[MEASURED IN BRIEF]`**, script `data/B2_intersect.py`, results
`data/B2_profitability_tag_intersections.json`. Distinct CIKs in the intersection of the required tag
sets, same calendar-year frame.

| | 2013 | 2016 | 2019 | 2022 | 2024 |
|---|---|---|---|---|---|
| `Assets` (the ceiling) | 7722 | 6672 | 6180 | 6870 | 6263 |
| `GrossProfit` tag alone | 3214 | 2768 | 2698 | 2879 | 2623 |
| revenue family ∩ cost family | 3274 | 3265 | — | 3487 | 3204 |
| **gross profitability, either route ∩ `Assets`** | **3796** | **3504** | — | **3476** | **3191** |
| **operating profitability** (+ `XSGA`) | **1886** | **1748** | — | **1681** | **1521** |
| `CbOP`, balance-sheet, **strict** (all six accrual terms present) | **171** | **194** | — | **273** | **233** |
| `CbOP`, balance-sheet, **`P2`-style** (missing changes → 0; `RECT`+`AP` required) | **1207** | **1124** | — | **1129** | **997** |
| `CbOP`, **cash-flow-statement** variant (`RECCH`+`INVCH`+`APALCH`) | **359** | **328** | — | **293** | **253** |

**Three things follow, and the middle one is a trap.**

1. **Gross profitability is computable for ~3,200–3,800 filers a year — comfortably above this
   programme's ~1,573 names. Operating profitability for ~1,500–1,900, which is AT the universe size.
   `CbOP` for ~1,000–1,200 under `P2`'s own missing-to-zero rule.** So all three are nominally
   reachable and the ordering is the reverse of the evidence ordering.

2. **THE TRAP: `P2`'s "missing values are replaced with zero" means something different in XBRL than
   it does in Compustat, and the difference is not small.** In Compustat, a missing `XPP` means the
   *vendor* could not populate the field after standardising the filing. In XBRL, an absent
   `PrepaidExpenseCurrent` means **this filer did not use THAT TAG** — they may have used
   `PrepaidExpenseAndOtherAssetsCurrent` (a superset, 2,546–3,099 filers), or a filer-invented
   extension, and the underlying balance may be large. **Setting it to zero in an XBRL build silently
   deletes a real accrual term for the ~75% of filers who do not use the exact tag.** The strict
   intersection — **171 to 273 filers** — is the honest measure of how often you can actually see all
   six accrual terms. **`CbOP` from XBRL is not `CbOP`; it is `CbOP` with most of its accrual
   correction missing at random-with-respect-to-industry, which is the construction whose whole claim
   is the accrual correction.**

3. **The cash-flow-statement variant does NOT rescue it.** Its three tags are individually stable
   across FY2018 — that is genuinely good — but their intersection with the operating-profit route is
   **253–359 filers**, even thinner than the strict balance-sheet route. And `P2` itself uses it only
   for its Table 3 post-1988 robustness check, not for its headline.

**The binding tag for operating profitability and `CbOP` is the same one:
`SellingGeneralAndAdministrativeExpense`, at 1,822–2,674 filers against 6,139–8,166 for `Assets`.**
`GeneralAndAdministrativeExpense` is more widely tagged (3,073–4,226) but **excludes selling expense
and is a different line**; substituting it would change the numerator. **There is no single us-gaap tag
corresponding to Compustat `XSGA` for the majority of filers.** That is the single most important new
computability fact in this brief after `GrossProfit`.

### 6.4 What `P4`'s own paper says about free-data grade, which bears on all of this

`P4` §2.3, verbatim: *"we implicitly assume data at the end of month `t` can be used to make trades in
closing auctions on the last day of month `t`"* and *"the hypothetical traders in our portfolio tests
would add demand to the closing auctions for the long legs, thereby increasing the buying prices and
reducing trading profits."* **The reference implementation states that its own long legs are traded at
a price its own demand would move.**

---

## 7. `Q4` — BREADTH, AND `Q6` — SCREENS AND WEIGHTING

### 7.1 How many names per leg the reported results need

| source | sort | names per leg | where |
|---|---|---|---|
| `P1` Table 2 | VW quintiles, NYSE breaks, all stocks | **`n` = 771 (low), 598, 670, 779, 938 (high)** | read in full |
| `P1` Table 4 Panel B | VW quintiles within the **BIG** size quintile | **63, 64, 60, 62, 72** | read in full |
| `P1` Table 3 | the big size quintile itself | **335 firms = 8.25% of firms, 75.1% of market cap** | read in full |
| `P2` Table 2 | Fama–MacBeth, All-but-microcaps | — | **`P2` does not report `N`; `P6` Table B3 reports Avg. `N` = 3,345–3,371 for its cap-weighted version** |
| `P6` Table B2 | component regressions | **Avg. `N` = 2,353–2,373** | read in full |

**So the all-stock quintile result needs ~600–950 names a leg, and the large-cap result needs ~60–70.**
**Neither is a breadth problem for this programme's 1,573 names.** The problem is the other one.

**THE TOP-90%-OF-CAP QUESTION, ANSWERED THREE WAYS, ALL NEGATIVE FOR GROSS AND OPERATING
PROFITABILITY:**

- **`P1` Table 4, read in full: the GP/A spread DECREASES MONOTONICALLY IN SIZE — `0.67` [4.59],
  `0.53` [3.97], `0.41` [2.88], `0.38` [2.82], `0.26` [1.88] from small to big.** `P1`'s own text:
  *"Among the largest stocks, the profitability spread of 26 basis points per month (test-statistic of
  1.88)…"* **In the largest quintile, gross profitability does not clear 1.96 in its own founding
  paper.** The top 90% of cap is roughly size quintiles 3–5 (`6.13 + 12.6 + 75.1 = 93.8%` of cap per
  `P1` Table 3), i.e. spreads of `0.41`, `0.38`, `0.26`.
- **And the Sharpe ratios `P1` reports for the large-cap version are worse than the market's:**
  *"the two strategies' realized annual Sharpe ratios over the period are only 0.27 and 0.14"* for
  large-cap profitability and large-cap value — **against `0.34` on the market**, read in full. The
  0.44 `P1` advertises is the **50/50 mix** of the two, and the 0.85 is the **all-stock** mix.
- **`P2` Table 4 Panel B: OP's big-stock 10−1 is `0.17` [`1.21`] raw and `0.23` [`1.63`] CAPM —
  insignificant both ways. `CbOP`'s big-stock 10−1 is `0.43` [`3.31`] raw and `0.55` [`4.34`] CAPM.**
  **`CbOP` is the only definition that survives in big stocks.**

### 7.2 The ~10-effective-instruments question, answered plainly

**No source in this family reports an effective number of independent bets, a cross-correlation of its
legs' residuals, or anything from which breadth could be computed.** I checked `P1`, `P2`, `P3`, `P4`,
`P5`, `P6` and `P7`. **What they report is `n` (names) and, in two cases, a realised Sharpe ratio.**

**What can be said, and it is arithmetic rather than a citation.** `P1`'s large-cap profitability
strategy has a realised annual Sharpe of **0.27** on ~70 names a leg over 47½ years. `P1`'s all-stock
quintile strategy's `t` of `2.49` over 570 months implies an annualised Sharpe of roughly
`2.49/√47.5 ≈ 0.36`. **Neither is a result that requires a hundred independent bets — they are both
results that a handful of independent bets, held for decades, can produce.** A strategy whose `t` is
2.49 over 47 years is earning about **0.36 units of Sharpe**, and at ~10 effective instruments that is
not obviously out of reach. **But the corollary is the one to carry: a `t` of 2.49 over 47 years is a
`t` of about `2.49 × √(16.6/47.5) = 1.47` over this programme's 16.6-year fixture, IN THE ABSENCE OF
ANY DECAY.** `[MY ARITHMETIC.]` **Add `P7`'s post-2005 shrinkage and the expected in-sample `t` on
this fixture is below 1.** That, not breadth, is the reachability constraint.

### 7.3 Equal versus value weighting — and the prior source's claim does NOT transfer

**The claim the slate flagged — that a related anomaly was "not at all present in equal-weighted
portfolios" — is the OPPOSITE of what holds for this family.** Equal weighting is where profitability
looks BETTER, not worse, which is the usual direction and is itself the reason to distrust it:

- **`P4`'s baseline portfolios are mostly EQUAL-WEIGHTED, by their own statement:** *"our baseline
  portfolios follow the original papers as much as possible… These portfolios likely overstate the
  profits traders could have earned from these predictors, however, **as most of them are
  equal-weighted**."* Under that baseline, `CBOperProf` is **`0.46`, `t` `3.20`**; the EW-quintile
  lagged-asset variant is **`0.46`, `t` `3.33`**.
- **`P4` §5.2, verbatim: *"imposing value-weighting or market equity screens reduces mean returns by
  roughly a factor of 1/3."*** So EW → VW costs about a third of the mean across the whole library.
- **`P3`'s entire thesis is that equal weighting plus NYSE-Amex-Nasdaq breakpoints inflates anomalies
  through microcaps:** *"on average, there are 2,406 microcaps, which account for 61% of the total
  number of firms… However, microcaps represent only 3.28% of the total market capitalization."*
- **But `P2` Panel B measures profitability IN microcaps separately and finds it NOT a microcap
  artefact: `CbOP` slope `2.48` [`9.62`] in microcaps against `2.60` [`9.69`] in all-but-microcaps —
  i.e. slightly WEAKER in microcaps.** Read in full. **That is unusual and it is the strongest
  methodological point in `CbOP`'s favour.**

**For an equal-weighted book, the relevant row is `P4`'s EW quintile column, and it says: gross
profitability `0.20` [`1.85`], operating profitability `0.05` [`0.33`], cash-based operating
profitability `0.46` [`3.33`].** Equal weighting does not kill `CbOP`. It does not save the other two.

### 7.4 The price screen — the one place a source speaks directly to this programme's floor

**`P4` §5.2, verbatim:** *"Intuitively, all liquidity adjustments lead to lower mean returns. **The
price screen (limiting to stocks with share price > `$5`) appears to be the softest adjustment,
producing the smallest decline in performance.** The other liquidity adjustments have relatively
similar effects."*

**That is a direct, quotable statement that a `$5` floor is the least damaging of the standard
liquidity screens**, measured across `P4`'s whole library rather than on profitability alone. It is
consistent with `A2`'s round-1 measurement that `GP` *rises* slightly under the `$5` screen
(`0.79 → 0.70 → 0.77` with `t` `2.71 → 3.14 → 3.39`) while `ShareIss1Y` falls by more than half.

**Rebalancing frequency, which bears on the 3–6-month breakeven hold.** `P4` §5.3, verbatim:
*"Performance declines monotonically as the rebalancing frequency decreases from 1- to 12-months.
This pattern is intuitive as less frequent rebalancing implies less exposure to the predictive
signal."* **This is about REBALANCE FREQUENCY, not holding period, and it is not the same statistic as
`A2`'s flat 1-to-12-month premium.** The sources that speak to HOLDING period are more favourable:
`P1` footnote 3 — *"its profitability persists for more than three years"*, and the annual strategy
*"turn[s] over only once every four years"* — and `P2`'s Fig. 2, verbatim: *"operating profitability
and cash-based operating profitability predict returns persistently over at least a ten-year
horizon… While the predictive ability decays over time, it remains reliably positive."* **By contrast
`P2` Fig. 2 Panel C: accruals predict only one year ahead.**

### 7.5 AND THE FACT THAT CUTS THE OTHER WAY: the quarterly version is roughly twice as strong

**`P1` Appendix A.4, read in full:** the quarterly strategy is built from *"Compustat data items
`REVTQ`, `COGSQ`, and `ATQ`"*, formed *"starting at the end of the month following a firm's report date
of quarterly earnings, item `RDQ`"*, and *"the high frequency strategy was almost twice as profitable…
generated excess returns of almost 8% per year."* **`P4`'s own table corroborates it across all three
definitions:** `GPlag_q` **`0.88` [`6.17`]**, `CBOperProfLagAT_q` **`0.86` [`6.19`]**,
`OperProfRDLagAT_q` **`1.17` [`5.56`]** — against `0.20` [1.85], `0.46` [3.33], `0.05` [0.33] for the
annual versions.

**This is a genuine tension with this programme's stated horizon and I am flagging it rather than
smoothing it.** `P1` chose annual data deliberately — *"Focusing on the strategy formed using annual
profitability data ensures that results are truly driven by the level of profitability, and not
surprises about profitability like those that drive post earnings announcement drift"* — and **PEAD is
excluded ground for this campaign.** So: **the quarterly variant is two to four times stronger in
three independent measurements, it is natively point-in-time from XBRL filing dates, and its author
says part of why it is stronger is an effect this programme may not pursue.** Not resolvable here.
**Recorded as the largest unexploited fact in the lane.**

---

## 8. `Q6` / SIZE-IS-NOT-PRICE — THE PRICE DISTRIBUTION, AND ITS CONFIRMED ABSENCE

**`[MEASURED IN BRIEF]` on the extracted text of four sources:** count of case-insensitive matches for
`share price` ∪ `price screen` ∪ `$5` ∪ `price of $`:

| source | matches |
|---|---|
| `P1` Novy-Marx (2013), JFE, 28 pp | **0** |
| `P2` Ball et al. (2016), JFE, 18 pp | **0** |
| `P7` Chen & Welch (2026), 24 pp | **0** |
| `P3` Hou–Xue–Zhang, 130 pp | 20 — **and every one is about OTHER anomalies' screens, or about `Pps` (share price) as a separate PREDICTOR**; `P3` states *"We do not impose such a price screen"* |

**Confirmed, not assumed: the profitability literature does not report the nominal share-price
distribution of its legs.** `P1` Table 2 reports `GP/A`, `B/M`, **`ME`** and `n` per portfolio.
`P2` Table 1 reports `log(ME)`. **Both report SIZE and neither reports PRICE.** So the round-1 finding
generalises to this family specifically, and the single figure a prior lane found ($55.60 long vs
$7.03 short) has **no counterpart for any profitability sort.**

**What can be inferred, and it is weak, so it is labelled.** `P1` Table 4 Panel B gives the
book-to-market of each size × GP/A cell: in the **Big** size quintile the GP/A deciles run
`B/M` `0.97, 0.82, 0.92, 0.42, 0.27` from low to high profitability. **High-profitability large firms
are the lowest-book-to-market names in the cross-section.** Low `B/M` at large `ME` implies high market
equity per unit of book, which *tends* to come with higher nominal prices — **but nominal price is
`ME / shares outstanding` and nothing in any of these papers pins down the share count.**
`[INFERENCE, NOT A MEASUREMENT. Do not carry it as one.]`

**Operationally: if this programme builds a profitability sort, the price distribution of its own legs
is an ORIGINAL measurement, not a replication, and there is nothing to check it against.**

---

## 9. WHAT I WOULD CARRY FORWARD, AS ONE SPECIFICATION

Stated so it can be implemented or rejected, not as a recommendation to trade.

| | |
|---|---|
| **definition** | **Cash-based operating profitability**, Ball, Gerakos, Linnainmaa & Nikolaev (2016), JFE 121(1), Appendix — formula quoted verbatim at §3.1 |
| **numerator** | `REVT − COGS − (XSGA − XRD) − Δ RECT − Δ INVT − Δ XPP + Δ(DRC + DRLT) + Δ AP + Δ XACC`, all changes year-on-year |
| **deflator** | **Report BOTH `AT₋₁` (the paper) and `AT` (the reference implementation).** They are not the same signal and `P3`/`P4` differ on which is meant. Their long-shorts are `0.53`/`3.02` and `0.63`/`3.44` in `P3`; `0.46`/`3.33` and `0.46`/`3.20` in `P4` |
| **trim** | independent variables at 1% and 99% for any regression; **portfolio sorts are NOT described as trimmed in any source** — state which you did |
| **lag** | **six-month rolling** to replicate `P2`/`P4`, or **fixed end-of-June on FY ending in `t−1`** to replicate `P1`/`P3`. **Filing-acceptance-date timing is fresher than every published result and replicates none of them** |
| **sort** | deciles or quintiles; NYSE breakpoints if replicating, **equal-weighted universe breakpoints if serving this book** — and say which |
| **filters** | exclude SIC 6xxx financials; ordinary common shares only; **require non-missing OP, accruals and `CbOP` together** (`P2`'s own filter, which changes the universe) |
| **hold** | **annual rebalance.** One-sided turnover for this family is **1.96%/month** (`P5`, gross profitability); at `67.6 bp` round trip that is **~1.3 bp/month** of cost `[MY ARITHMETIC]`. `P2` Fig. 2: predictive power *"remains reliably positive"* at a ten-year lag |
| **benchmark, named** | **Report the long leg against the value-weighted market AND against the equal-weighted universe, separately.** `P2`'s CAPM α for the long leg is `+0.14` `[1.95]`; its FF3 α is `+0.35` `[5.98]`. **The choice moves the answer by 2.5×** |
| **tags needed** | `GrossProfit` *or* (`Revenues` ∪ `RevenueFromContractWithCustomer*` ∪ `SalesRevenueNet`) ∩ (`CostOfGoodsSold` ∪ `CostOfGoodsAndServicesSold` ∪ `CostOfRevenue`); `SellingGeneralAndAdministrativeExpense`; `ResearchAndDevelopmentExpense`; `AccountsReceivableNetCurrent`; `InventoryNet`; `PrepaidExpenseCurrent` (∪ `PrepaidExpenseAndOtherAssetsCurrent`); **`DeferredRevenueCurrent` + `DeferredRevenueNoncurrent` PRE-FY2018 and `ContractWithCustomerLiabilityCurrent` + `…Noncurrent` POST**; `AccountsPayableCurrent`; `AccruedLiabilitiesCurrent`; `Assets` |
| **the dealbreaker to test FIRST** | **the FY2018 deferred-revenue transition.** `Δ(DRC+DRLT)` across the adoption year crosses a tag change AND a cumulative-effect restatement for ~1,700 filers, concentrated by industry. **If that term cannot be made continuous, `CbOP` is not measurable across FY2018–2019** and the honest fallback is **gross profitability from `GrossProfit`/`Assets`, which is two stable tags and `t` `1.04`–`2.62` depending on a deflator choice** |

**And the arithmetic that should decide whether any of this is worth building:** `P1`'s all-stock
result is `t` `2.49` on 570 months. On a 16.6-year fixture, with no decay at all, that is `t ≈ 1.47`.
`P7` says the post-2005 long-minus-market shrinks to zero under its own empirical-Bayes estimator.
**A positive gross mean per trade above the nulls is the stated criterion, and `P2`'s published
long-leg CAPM `t` of `1.95` over fifty-one years is the most favourable published number there is.**

---

## 10. WHAT I COULD NOT VERIFY, STATED PLAINLY

1. **Ball, Gerakos, Linnainmaa & Nikolaev (2015), "Deflating profitability", JFE 117(2) — THE SOURCE
   PAPER FOR OPERATING PROFITABILITY — I did not obtain.** Four routes tried: two
   `faculty.tuck.dartmouth.edu` paths (**`WebFetch`/`curl` → HTTP 404, `text/html`, 14,704 bytes**),
   `faculty.chicagobooth.edu` (**HTTP 404, 3,389 bytes**), and SSRN abstract pages which do not serve
   the PDF. **Its construction here rests on three second-hand restatements that agree (`P2`'s
   Appendix, `P3`'s A.4.15, `P6`'s Table B1), and its own reported result — `P3` says BGLN(2015)
   report `Opa` 10−1 at `0.29`, `t` `1.95` — is `[snippet only, via P3]`.** A search summariser
   asserted that the paper's point is that *"deflating profit by the book value of total assets results
   in a variable that is the product of profitability and the ratio of the market value of equity to
   the book value of total assets, which is priced"* — **that is a SUMMARISER claim, it is exactly the
   deflator question this brief turns on, and I am NOT treating it as established.**
2. **`P6`'s Internet Appendix Table D1 — the post-2000 sub-period split in which `OP_R&D` "fully
   subsumes `COP_R&D`" — I did not obtain.** I read the sentence describing it in the main text, not
   the numbers. **So the most recent, most era-relevant claim against `CbOP` is `[read in full]` of a
   sentence about a table I never saw.**
3. **`P6` Table A5's long-only numbers (`α` `0.58` `[4.68]`, `0.52` `[4.22]`) — the column-to-regressor
   mapping is destroyed by PDF text extraction.** I could not determine which benchmark each α is
   against, and the portfolio mixes profitability with investment. **Not used as evidence.**
4. **`P8` (Jensen–Kelly–Pedersen): every profitability figure is in a bar chart.** I extracted only
   the label ORDERING, which places Profitability 4th–5th from the bottom of 13 themes. **I report no
   value from `P8` and the ordering inference depends on those figures being sorted, which I inferred
   rather than confirmed.**
5. **There is no cost-honest long/short number for cash-based or operating profitability anywhere I
   looked.** `P5` predates both and covers gross profitability only. **The 1.3 bp/month cost figure in
   §4 and §9 is MY arithmetic on `P5`'s gross-profitability turnover applied to this programme's own
   67.6 bp, not a published net return for `CbOP`.**
6. **Detzel, Novy-Marx & Velikov (2023 JF) — paywalled.** Its abstract's claim that cost-adjusted
   models "employing cash profitability perform better still" is **[abstract only, via a search
   summariser]** and is cited nowhere as a figure. **It would be the single most valuable missing
   source for this lane** — it is the one paper that nets `CbOP`-based factors.
7. **Novy-Marx & Velikov, *Assaying Anomalies* (SSRN 4338007) — not obtained, as in round 1.** The
   only `assayinganomalies` PDF I retrieved was the **Monetary Policy Exposure online appendix**
   (`bpb-us-e1.wpmucdn.com/sites.psu.edu/.../MPE.pdf`, 25 pp, HTTP 200, genuine PDF, **wrong subject**)
   and it carries no profitability number.
8. **`P2`'s own internal ambiguity about its deflator is unresolved by me.** Its Appendix and Table 1
   legend say *"total assets lagged by one year"* / *"in year `t−1`"*; **its Table 4 legend says only
   *"scaled by the book value of total assets"*** with no "lagged". **The headline `0.47` `[3.17]` may
   or may not be the lagged-asset version, and the paper does not say.** `P3` and `P4` read it
   differently from each other (§2.3).
9. **`P5`'s Table 3 says gross profitability nets `0.37` at `t` `2.74`; `P5`'s own text lists the
   strategies that "achieve net excess returns that are statistically significantly larger than zero"
   and gross profitability is not among them.** I read both, they are in tension, and I did not resolve
   which claim `P5` intends (§2.2).
10. **My intersection measurement (§6.3) understates coverage for non-December fiscal-year filers.**
    The `frames` API matches facts to calendar frames, so a firm whose FY ends in, say, September may
    be absent from a `CY####` or `CY####Q4I` frame even though it tagged the item. **`Assets` at
    6,139–8,166 suggests most filers are captured, but I did not quantify the non-calendar-FY loss and
    the absolute counts should be read as lower bounds.** The RELATIVE comparisons between tags in the
    same frame are unaffected.
11. **I did not verify a single return figure against any raw data.** Every return, `t`-statistic,
    turnover and alpha in this brief is transcribed from a source PDF I extracted and read locally.
    **My own measurements in this brief are confined to the SEC XBRL tag census and intersections
    (§6), and to arithmetic on published figures which I have marked `[MY ARITHMETIC]` every time.**
12. **One HTTP-200 hazard measured here, logged by tool and response as the campaign requires.**
    `curl` → `https://www.nber.org/system/files/working_papers/w30091/w30091.pdf` returned **HTTP 200,
    `application/pdf`, 322,561 bytes, a genuine well-formed PDF** — **of "A Theory of Visionary
    Disruption" by Joshua Gans**, not the paper I had guessed at that number. **Caught only by reading
    the title line of the extracted text.** And a second: `curl` →
    `https://pdfs.semanticscholar.org/df4a/...pdf` returned **HTTP 200, `application/pdf`, 1,410,508
    bytes** — a genuine PDF, **but a 34-page CONFERENCE SLIDE DECK of Novy-Marx (2013), 9,268
    characters of text, not the 28-page article**. Both were discarded. **Two more flavours for the
    tabulation: a plausible working-paper number serving a different paper, and a slide deck served at
    a paper's PDF URL.**

---

## 11. EVIDENCE FILES WRITTEN

| file | what |
|---|---|
| `data/B2_profitability_tag_census.json` | `[MEASURED IN BRIEF]` — 33 us-gaap tags × 11 calendar years, distinct-entity counts, two negative controls |
| `data/B2_tagcensus.py` | the script, with endpoint, pacing and contact string, so it can be re-run |
| `data/B2_profitability_tag_intersections.json` | `[MEASURED IN BRIEF]` — per-definition tag intersections, 5 years |
| `data/B2_intersect.py` | the script, including the definition-to-tag-set mapping used |

**Nothing in this brief is elevated out of `docs/research/`. Neither book is touched. Nothing is
closed and nothing is admitted.**
