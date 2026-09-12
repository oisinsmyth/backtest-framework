# Scan-100926 · Round 4 — record

**Slate:** [`R4-00-slate.md`](R4-00-slate.md) · **contract:** [`00-SCHEMA.md`](00-SCHEMA.md) ·
**round 3:** [`R3-99-record.md`](R3-99-record.md) · **round 2:** [`R2-99-record.md`](R2-99-record.md) ·
**round 1:** [`R1-99-record.md`](R1-99-record.md).

**STATUS: COMPLETE — all four lanes in.**

**Under [R15](../../RULES.md#r15) nothing here closes or admits anything.** Nothing is elevated out of
`docs/research/`. **Conflicts are recorded, not adjudicated** — and this round **corrected two errors in
round 3's record, both MINE**, and **opened a new head-on conflict between `D2` and `C1`** that is left
standing (§4, `G1`).

---

## 0. THE SHAPE OF THE ROUND

| lane | tokens | round 3 |
|---|---|---|
| `D1` the nine unexamined nodes | **366k** | 368k |
| `D2` is the quarterly advantage seasonal | **352k** | 335k |
| `D3` are these two signals the same signal | **368k** | 334k |
| `D4` when does the premium arrive | **324k** | 407k |
| **round 4** | **~1.41M** | ~1.44M |

**Inside the revised ~1.3–1.5M band, second round running.** The contract's arithmetic now holds at two
different depths: ~1.13M pre-mandate, ~1.4M under it.

**THE ROUND'S ORGANISING FACT: THREE OF THE FOUR LANES TOOK A FINDING THIS CAMPAIGN WAS CARRYING AND
SHOWED IT WAS SOMETHING ELSE.**

- `D4` took the number that commissioned it — *"three of 132 months carry half the total"* — and showed
  **it is a restatement of the `t`-statistic, not a measurement of arrival.**
- `D1` took `C2`'s taxonomy call and showed **the node's type depends on the estimator, not on the node.**
- `D3` took `F1`'s "different definition, dataset and cut, all named, not ranked" and showed **the
  disagreement is construction, separable from published work, and `C4` had already said so.**

**And the long-leg blind spot reached its fourth and fifth independent confirmations — one of them from
source code.** `D1` found that in one reference implementation **the long leg is computed and discarded on
the very next line**, and that another paper **defines long-leg turnover as an equation, computes it, and
sums it into the spread.** `D4` censused six full texts for *"drawdown"*, *"months to half"* and
*"fraction of months positive"* and found **zero in all six.**

---

## 1. CORRECTIONS TO ROUND 3's RECORD — BOTH MINE, BOTH MADE IN PLACE

**Recorded here as well as in `R3-99` so the round that caught them carries them too.**

1. **I collapsed a working paper into a published article.** `R3-99` §2.2 said *"`C1` obtained it: the
   **2015 paper** deflates by CURRENT assets."* **`C1` read the 6 May 2014 Chicago Booth working paper**,
   tagged it `[WORKING PAPER]`, cited it by number, page count and URL, and **listed the published
   JFE 117(2) 2015 among the versions it could NOT verify.** `D3` caught it and reports the published
   article has now **failed in three consecutive rounds** — five routes with byte counts, including a
   **Wayback wrong-200 serving a 404 page at a `.pdf` URL**, and two bibliographic APIs both returning
   `closed`. **Everything this campaign holds from that paper is the 2014 working paper.** `C1` was
   precise; my record was not. **This is the draft-versus-published hazard the campaign has caught four
   times in other people's papers, committed by me in a record.**
2. **I repeated an over-claimed mapping.** `R3-99` called a ranked row *"the deflator… independently
   confirming `B2`."* **It is not `B2`'s deflator.** `C2`'s section heading was accurate — *"Mitton's
   **Table 8**, average |Δ`t`| over **65 real hypotheses"*, corporate finance — but its mapping column
   said *"yes — `B2`'s deflator, ranked FIRST"*, and I repeated that. `D3` found the right rows in
   **Table 7, the profitability column: `ROA`→`ROE` (assets→book equity) at |Δ`t`| 12.31**, and
   **end-year→begin-year (current→lagged) at 6.73**. **The corrected evidence is STRONGER for `B2` than
   the figure I misattributed, and the 12.31 row is the assets-versus-equity node that bears on `F1`.**

---

## 2. `F1` — WHAT ROUND 4 PUT UNDER IT, WITHOUT ADJUDICATING IT

**`D3` was sent to say what the disagreement is made of. It did, and the answer is that it is separable.**

**Hou–Xue–Zhang's replication computes BOTH definitions on ONE sample with ONE construction**, across
**fourteen specifications including equal weighting**, Jan 1967 – Dec 2016. NYSE breakpoints,
equal-weighted: **gross profits / current assets +0.67 %/mo (|t| 4.35)** against **operating profits /
current book equity +0.13 (|t| 0.66)**. **`F1`'s ordering reproduces with the dataset held fixed. So the
disagreement is CONSTRUCTION, not dataset.**

**And the gap is size-dependent, which nobody had seen.** From the same paper's Internet Appendix, the
`Gpa − Ope` gap runs **+0.54** (NYSE-EW) → **+0.35** (all-EW) → **+0.13** (all-but-micro EW) → **+0.01**
(microcap EW) → **−0.13** (microcap VW, where `Ope` is the *larger*). The deflator paper agrees from the
other side: its three-deflator horse race leaves only the asset-deflated version significant among
all-but-microcaps, but *"among Microcaps the leverage terms on their own have as much or more explanatory
power."* **THE CASE FOR GROSS PROFITABILITY IS WEAKEST IN THE SIZE SEGMENT THIS PROGRAMME TRADES.**

**The deflator is not a free node**, and the author says so in print: *"I scale gross profits by book
assets, not book equity, because gross profits are an asset level measure of earnings. They are not
reduced by interest payments and are, thus, independent of leverage."* And it is an identity:
`GP/TA = (GP/BE) × (BE/TA)` — **the deflator change multiplies in book leverage exactly as current-vs-lagged
divides by asset growth.**

**Which axis dominates is now measured.** Correlation of French's `RMW` with the other dataset's
**same-definition** series is **+0.83**; with the **different definition**, **+0.53**. **The definition
dominates the implementation.** `D3`'s figures **reproduce `C4`'s headline to four decimal places**
through an independent pipeline from the same bytes (+0.3789 / `t` 3.56; +0.4046 / `t` 3.00); **swapping
only the definition** gives **+0.130 / `t` 1.65** and **+0.113 / `t` 1.11**.

**AND `D4` INDEPENDENTLY VINDICATED `C3`'s CONSTRUCTION WHILE FINDING A HAZARD THAT COULD HAVE BROKEN
BOTH LANES.** French's OP deciles use **NYSE breakpoints** — `Lo 10` averages **967 firms**, `Hi 10`
**322** — so **the simple mean of ten deciles is not the equal-weighted universe**, an error of
**13.6 bp/month post-2013, larger than the quantity being measured, and it flips the sign.**

- **`C3` did not make that error.** Its script builds the universe **firm-count-weighted from the file's
  own firm-count block**, and the proof is arithmetic: **`D4`'s corrected full-sample figure is
  +0.0262 [t +0.45], which is `C3`'s +0.026 [t 0.45]** — different script, different lane, same number.
- **What is open is `C4`'s construction**, and `D4` frames it exactly right: it quotes `C4`'s own
  definition — the simple mean of five quintiles, *"which **for an equal-count sort** is its
  equal-weighted universe"* — notes **the conditional is the right one**, and says what it cannot check
  is whether that dataset's quintiles are equal-count. **Its words: "flagged as a question for `C4`'s
  construction, NOT as a refutation of it."**
- **The hazard is specific to equal weighting** — for value weighting the two benchmarks nearly agree —
  **which is this programme's own weighting.**

**`F1` REMAINS OPEN.** Round 4 did not resolve it; it **named what would**, and the two candidates are
now specific: whether the other dataset's quintiles are equal-count, and which size segment the answer is
read in. **One fair criticism of my framing, verified and accepted:** `C4` had **already** reached the
"definitions, not datasets" conclusion and **had the operating-profitability numbers in its own JSON** —
five of its committed evidence files contain them. **`F1`'s "named, not ranked" framing understated what
`C4` already had in hand.**

---

## 3. What each lane returned

### `D1` — the nine unexamined nodes

**The blind spot is BY DESIGN, and the evidence is the code.** In one reference implementation the long
leg **is computed and discarded on the very next line**; another paper **defines long-leg turnover as an
equation, computes it, and sums it into the spread.** Censuses return zero for *"long leg"*, *"short leg"*
and *"long-only"* across four documents **including the full published JFQA text round 3 had only in
abstract and introduction.** **Two counterexamples named rather than a clean absence reported:** a 2020
*REStat* paper derives **two different optimal quantile counts — one exponent for testing a spread, a
different and smaller one for factor construction** — and a June 2026 paper studies construction
dependence **entirely on long-only portfolios**.

**`C2`'s Type-E call is corrected with a proof.** **Outlier treatment — the #2 ranked node — is EXACTLY
ZERO for a sort** `[MEASURED IN BRIEF]` on **2,612 real SEC filers**: winsorising `GP/AT` at 1/99,
2.5/97.5 or 5/95 **moves ZERO names**. **Trimming** at the same cutoff turns over **8.9%** of the long leg
at 1/99 and **79.4%** at 5/95. So the two branches are not two equally valid answers to one question —
**one changes the portfolio and one cannot.** `C2`'s call is **correct for a regression** (|Δ`t`| 0.99).
**`D1`'s generalisation is the keeper: THE NODE'S TYPE DEPENDS ON THE ESTIMATOR, NOT ON THE NODE.**

**The boundary is exact and checkable: winsorisation of a characteristic is a no-op iff `q < 1/J`.** With
deciles, 5% is safe and 20% destroys **88.9%** of the long leg. **A slot-based long-only book's effective
`1/J` is its slot share of the eligible universe, so the safe cutoff SHRINKS as the book concentrates.**
Nothing in the published grids states this, **because none of them has an outlier node at all.**

**And it found the genuinely arbitrary node `C2` said did not exist.** `C2` reported every node it
examined closely was non-arbitrary. **Level versus log of the SORTING VARIABLE is an exact identity for a
sort** — 0 of 2,401 names move — **while the same node ranks among the largest for regressions** (|Δ`t`|
8.01 on quasi-random ratios). **Its arbitrariness is provable rather than asserted.**

**Three nodes kept strictly separate where conflating them would be an error** — winsorising the
*characteristic*, log of the *sorting variable*, log of the *return*. **Log of the RETURN is the one that
bites, and its sign FLIPS between objects:** **−0.10 to −0.19 pp/mo on the LEG** against **+0.11 to +0.12
on the SPREAD**. `D1` derived the prediction from Jensen's term, **½(σ²_Lo − σ²_Hi)**, and **confirmed it
to 0.009 pp in four of four cells.** The VW OP spread goes **`t` 1.61 → 2.30** on that choice alone.
**The convention hurts the leg and helps the spread, and this programme holds the leg.**

**Dropping loss-makers — the #1 node for profitability sorts — is a SHORT-LEG node.** One panel falls
0.27 → 0.18 %/mo (−33%), and **in French's construction the long leg is unchanged by construction.** The
dropped set is **37.4% of the cross-section over 2010–2026** and **outperformed the bottom decile over 75
years** (+1.229 vs +0.967 EW).

**Bearing directly on `D3`: 20.5% of filers have negative book equity AND negative operating income, so
the ratio comes out POSITIVE — and 62.9% of those sit above the well-defined p90, which means they ENTER
THE LONG LEG.** For `GP/AT` the same count is **two firms**. **So outlier treatment, loss-makers and the
deflator are ONE node for `OP/BE` and three for `GP/AT`.**

**The field knows its nodes are arbitrary and says so.** A measured justify-versus-inherit ranking:
lagging explained **50%** of the time, **outlier method 1%, cutoffs 1%.** **Fama and French declare the
#1-ranked node arbitrary in writing, twice, 22 years apart** — *"The splits are arbitrary, however, and we
have not searched over alternatives"* (1993). And **French's own OP documentation justifies doing
NEITHER** on outliers, because the extreme values *"accurately reflect the data in the firm's accounting
statements."*

**Three controls fired, all productive** — one caught **33 filers reporting total assets of exactly
ZERO**, and *a zero denominator is a different failure from a negative one, invisible to every outlier
rule*; one calibrated the reconstruction to ±0.024 pp/mo; one was a **1-in-757 rounding coincidence**,
reported rather than dropped. **Two further draft-versus-published breaks**, including **a remedy absent
from a published abstract** and **a rebalancing node added in revision**.

**And the contract change paid in a way I did not anticipate: `D1` opened two items from `C2`'s "what I
did not open" list and upgraded one of `C2`'s weakest citations from summariser-sourced to read-in-full.**
The list was added so the unexplored edge would be visible. **A later lane used it as a work queue.**

### `D2` — is the quarterly advantage seasonal?

**The seasonal-artefact hypothesis is NOT supported, and the decisive evidence was already latent in
public data.** `C1` reported that HXZ reach the seasonality point for `ROE` and **never apply it** to the
gross-profitability variant. **`D2` found the other half of that passage: HXZ report BOTH sides on one
sample.** Unadjusted single-quarter `Roe` **0.69 [3.07]**; seasonality-controlled `dRoe` **0.76 [5.43]**.
**Removing seasonality makes it STRONGER.** `D2`'s own panel agrees independently.

**And it built a cleaner test than the literature's.** One library ships **both** the trailing-four-quarter
and the single-quarter form **and refreshes both quarterly off the same filing** — so **freshness is held
constant and only the numerator window differs**, which is strictly better than the annual-versus-quarterly
comparison round 3 relied on (that confounds freshness, rebalance frequency and seasonality). On **701
matched months**: single-quarter α against trailing-four-quarter **+0.130 %/mo [NW6 +3.26]**; reverse α
**−0.075 [−1.54]**. **So the quarterly advantage is neither staleness nor seasonality — but the
seasonality-free form still gives up 28% of the mean, significantly.**

**The contamination is real and `D2` measured it anyway, WITHIN FIRM**, where industry and fiscal-year-end
are constant by construction. Single-quarter rank: fiscal-phase `R²` **+0.0129** over its AR(1) null,
**14.0% of firms significant**. Trailing-four-quarter rank: **−0.0682**, **1.0%** against a nominal 5%.
Paired difference **+0.0700, Wilcoxon p = 1.3 × 10⁻³⁸**. **Concentrated in retail (+0.1678) and
wholesale — the same two industries that are most non-December fiscal-year-end** (43.3%, 40.5% against
7.8% for financials; Cramér's V 0.119 against 0.038 permuted). **The mechanism exists and is located; it
just does not cost the sort its edge.**

**The bar is met in the affirmative**: a seasonality-robust quarterly gross-profitability sort earns
**0.303 %/mo [NW6 3.64]** over 890 months and **0.377 [NW6 1.98]** in this programme's era. **`D2` states
the caveat itself: it is only MARGINAL post-2010, and every member of the family except cash-based
operating profitability falls below `t` = 2 on NW6 over 2010–2024.** And `cop_at` is **0.515 [NW6 8.31]**,
far the strongest — **which restates this campaign's central bind exactly, because `C1` measured that same
definition at NINE CIKs quarterly from as-filed data. THE STRONGEST SIGNAL REMAINS THE LEAST COMPUTABLE.**

**Five controls fired and four killed `D2`'s own statistics** — a raw fiscal-quarter `R²`, a permutation
null, **a rotation null that was degenerate by construction** (rotations map the mod-4 partition onto
itself), and **the entire cross-sectional phase design**, whose failure is what forced the within-firm
test that became the lane's decisive measurement. **The fifth fired and REMAINS UNEXPLAINED:** two of the
source library's **own six published information ratios fail to reproduce, one sign-reversed**, after
ruling out vintage, sign convention and build language. **Reported unexplained rather than explained away.**

**Three further findings.** A reference library's **documentation misstates both** of its
seasonally-differenced variants **while the code is right — the third such instance this campaign.**
**No source anywhere builds a seasonally-adjusted profitability LEVEL.** And a hard constraint on this
programme's own route: **fiscal Q4 is largely absent from as-filed XBRL as a single quarter — 5,598 firms
fall to 583 without deriving it — which would itself manufacture a phase selection.**

### `D3` — are these two signals the same signal?

**§2 carries its central result.** Beyond it, **three corrections to things the field itself carries
wrong:**

1. **One dataset's `OperProf` is validated against the WRONG VARIABLE** — documented in its `SignalDoc`
   *and* its code header as a 2006 table row, but that paper's appendix defines the numerator as income
   before extraordinary items, **so the row is `ROE`**. The code implements the **2015** numerator.
   **Three provenances, one signal.**
2. **That dataset's `GP`/`GPlag` pair is NOT a clean deflator placebo** — `GP` uses one revenue field and
   drops financials; `GPlag` uses a different field and drops nothing. **Round 2's and `C4`'s deflator
   checks lean on it.**
3. **French's site has stated TWO different OP denominators simultaneously since early 2019** — *"book
   equity and minority interest"* on one page, plain *"book equity"* on the page documenting the
   univariate OP deciles `C3` used, and *"divided by **book**"* in a shipped CSV preamble. **Wayback-dated
   to between 2018-12-30 and 2019-03-03 — NOT August 2018 as a published footnote states.**

**And a version caveat on its own headline:** **HXZ's equal-weighted columns exist only in the October
2018 version** — zero occurrences of the relevant column label in the **May 2017 version round 2 read** —
with one signal **crossing `t` 1.96 between versions on two extra years alone**, and the 2018 version's
prose still carrying **stale 2014-sample figures its own table contradicts.**

**It did not adjudicate `F1`.** Ten named differences, **no source reports either definition's long leg**,
and the dimension with the largest published sensitivity — **size composition** — is one where the two
lanes' universes differ **and the published answer reverses.** Its own view, **labelled as a view**,
favours gross profits / assets **on computability, not performance**.

### `D4` — when does the premium arrive?

**The number that commissioned the lane is a restatement of the `t`-statistic, not a measurement of
arrival.** `D4` built its null: at **`T` = 132 and `t` = 1.25** — `C4`'s long leg exactly — an **iid
Gaussian** with no fat tails, no skew, no clustering and no events gives months-to-half of
**p05 1 / median 4 / p95 8.** `C4` observed **3.** And the decisive control: **the CRSP value-weighted
market's own equity premium reaches half its 1963–2013 total in 14 of 606 months — 2.31%, against `C4`'s
2.27%.** On a scale-free measure **all thirteen series measured, controls included, fall in 0.243–0.332.
There is no excess distributional concentration anywhere.**

**But arrival IS clustered, and the statistic was structurally blind to it** — `months-to-half` is an
order statistic. Against a permutation null preserving the marginal exactly: **73.7% of the profitability
long leg's entire 1963–2013 total arrived in the twelve months 2000-10 → 2001-09 (`p` = 0.003).** The VW
`Hi10−Lo10` spread is **99.8% the 36 months 2000-03 → 2003-02**, and **excluding them the in-sample spread
is 0.0004 %/mo at `t` = 0.00.** The same test on the market gives **`p` = 0.60**, and **the market LOST
money in that window** (−18.2% of its own total) — **so the cluster is cross-sectional, not calendar.**

**The literature never computes any of it**, censused on six full texts: *"drawdown"* **zero in all six**;
*"months to half"* **zero in all six**; *"fraction of months positive"* **zero in all six** once false
positives are removed.

**Three controls fired, and the census was rebuilt TWICE before any result was reported** — the
must-be-positive probe fired twice because one author writes *"test-statistic"* and never *"t-statistic"*
and another writes *"standard error"*. **A census that cannot find a phrase the document does not use is
measuring its own vocabulary.** The regime control was **built to be breakable**: shifting recession dates
forward 60 months turns the market's recession return from −0.64 to +0.90.

**Horizon, including the number nobody publishes:** **114.2 years** by the standard arithmetic;
**77.3 years merely to be 95% sure of a positive realisation**; and **26.7% of all actual overlapping
ten-year windows were NEGATIVE, and 23.4% of twenty-year windows.** The
EW-against-own-EW-universe figure of **1,234.6 years** independently reproduces round 3's **1,235** on
different data.

**Ex ante identifiability is a recorded, unadjudicated conflict:** one paper claims a pure timing
portfolio at **Sharpe 0.71 and never costs it**; another applied that method and reports it *"meager"*,
with an out-of-sample break-even of **1.8 bp per dollar traded** and net-of-cost returns *"likely de
minimis."*

**Name-level concentration for a characteristic sort is stated as unmeasurable from free portfolio-level
data and apparently unpublished** — and the obvious counter-citation is **correctly rejected**, because it
sorts on outcome and measures the market.

---

## 4. CONFLICTS — RECORDED, NOT ADJUDICATED

| | the conflict | readings |
|---|---|---|
| **G1** | **Does a QUARTERLY profitability sort survive the one-quarter-LAGGED deflator?** | **`C1`: YES** — 0.51 [`t` 3.40], **read from HXZ's published table**, 1967–2016, NYSE breakpoints, VW deciles. **`D2`: NO** — its **own measurement** of the same construction (TTM numerator, quarterly-refreshed, one-quarter-lagged deflator) gives **0.163 [`t` 1.43], insignificant**, 1963–2010, different library, different breakpoints, different weighting — **three for three across gross, operating and operating-to-equity.** `D2`'s position: round 3's headline should be *"marked provisional on the deflator, not on the season."* **Recorded as `D2`'s position, NOT adopted. Both stand.** |
| **G2** | **Is "winsorise versus trim at the same cutoff" an arbitrary choice?** | **`C2`: YES**, the cleanest Type E node it found (|Δ`t`| 0.99). **`D1`: NO for a SORT, and provably** — winsorising moves **0 of 2,612 names** while trimming turns over 8.9–79.4% of the leg. **`C2` is right for a regression.** `D1`'s resolution — *the node's type depends on the estimator* — **is recorded as `D1`'s generalisation, and both original readings stand in their own domains.** |
| **G3** | **Is `C4`'s own-universe benchmark correctly constructed?** | **`C4`:** the simple mean of its five quintiles, *"which for an equal-count sort is its equal-weighted universe."* **`D4`:** the conditional is right, but **if those quintiles use NYSE breakpoints the simple mean is NOT the EW universe**, and on French's deciles the same error is **13.6 bp/month and flips the sign.** **`D4` explicitly flags this as a QUESTION for `C4`'s construction, not a refutation.** **Unresolved, and it is one of the two things that would settle `F1`.** |
| **G4** | **Is a pure factor-timing portfolio worth anything?** | One paper: **Sharpe 0.71**, never costed. Another, applying that method: *"meager"*, break-even **1.8 bp per dollar traded**, net returns *"likely de minimis."* **Both stand.** |
| **G5** | **`D2`'s unexplained control.** | Two of a reference library's **own six published information ratios fail to reproduce, one SIGN-REVERSED**, after ruling out vintage, sign convention and build language. **`D2` reports it unexplained. Recorded as unexplained, not as a defect in either party.** |
| **G6** | **Three more documentation-versus-code disagreements**, all with the code right: a signal validated against the wrong variable; a placebo pair that is not a clean placebo; and a library whose documentation misstates both of its seasonally-differenced variants. **Round 3 found the first of this class; round 4 found three more. The class is now five instances and should be assumed, not discovered.** |

**`F1`–`F7`, `E1`–`E11` and `D1`–`D10` all still stand.** **`F2` is directly affected by `G1`** and both
are open.

### 4a. AND EVERY LANE RECORDS FURTHER CONFLICTS INSIDE ITS OWN BRIEF

**`G1`–`G6` are the cross-lane conflicts. They are not all of them.** `D1` §3.2 carries its taxonomy
placements node by node; `D2` carries its five fired controls with what each killed; `D3` §9 names **ten**
differences separating the two definitions and §13 labels its own preference **as a view**; `D4` carries
the ex-ante conflict and its rejection of a counter-citation. **Nothing is deleted and nothing is merged
away.**

---

## 5. MY OWN WRONG PREMISES THIS ROUND, RECORDED AS MINE

1. **I called `C4`'s three-of-132-months the most decision-relevant number of the round, and built a lane
   on it.** It is **not a measurement of arrival** — the market itself is at 2.31% against `C4`'s 2.27%,
   and an iid Gaussian null at the same `T` and `t` gives a median of 4. **I over-read a passing remark.**
   The lane was not wasted — it found the real finding — but **the premise was mine and it was wrong.**
2. **My slate conjectured that a spread's arrival might be smoother than its long leg's because the two
   legs' bad months offset.** **They do not offset — they COINCIDE.** The short leg's premium peaks in the
   **same 36 months** at 108.7% of its own total (`p` = 0.004). **The spread COMPOUNDS the long leg's
   clustering rather than smoothing it.**
3. **The two round-3 record errors in §1 are mine**, and the first is the draft-versus-published hazard
   this campaign has caught four times in other people's work.
4. **`F1`'s framing understated what `C4` already had.** I wrote the differences as *"named, not
   ranked"*; `C4` had already concluded *"resolves on definition"* and **had the comparison numbers in
   five of its own committed evidence files.**

---

## 6. What this record does not claim

**Nothing here was measured on this programme's fixture.** Every measurement is on Ken French's public
files, public anomaly libraries, or public SEC filings — **no `$5` floor, no trailing dollar-volume
screen, no dead-name inclusion, no overnight decomposition, and not one of this programme's own bars.**

**`D2`'s affirmative result and `G1` point opposite ways and neither is adopted.** A seasonality-robust
quarterly sort earning **0.377 [NW6 1.98]** in this programme's era is **not a green light**, and `D2`
says so itself: marginal post-2010, and **every member of the family except the least computable one falls
below `t` = 2.** **No backtest was run, no null drawn on our data, no candidate exists, no territory is
closed, and NO AVENUE IS CLOSED** ([R15](../../RULES.md#r15): only the principal closes an avenue).
**Both books are unchanged**, [`FINDINGS.md`](../../FINDINGS.md) and [`PICKUP.md`](../../../PICKUP.md) are
untouched, **and nothing in this folder is elevated out of `docs/research/`.**
