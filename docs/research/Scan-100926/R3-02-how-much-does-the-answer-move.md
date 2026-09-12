# `C2` — HOW MUCH DOES THE ANSWER MOVE? CONSTRUCTION DISPERSION, MEASURED

**Round 3 of `Scan-100926`.** Lane `C2` of four. Contract and the rules this brief carries:
[`00-SCHEMA.md`](00-SCHEMA.md). Slate: [`R3-00-slate.md`](R3-00-slate.md). The three round-2 lanes
whose independent collision created this lane: [`R2-01`](R2-01-the-benchmark-question.md) (`B1`, the
benchmark), [`R2-02`](R2-02-profitability-deep.md) (`B2`, the deflator),
[`R2-03`](R2-03-where-the-premium-accrues.md) (`B3`, the session boundary).

Under [R15](../../RULES.md#r15) **nothing here closes or admits anything.** **No number below was
measured on this programme's fixture.** Figures restated from our own record (33.8 bp/side, ~1,573
names, ~35.7% dead, ~10 effective instruments, `$5` floor, equal-weighted, cash-funded) are quoted,
not recomputed.

My own measurements are tagged **`[MEASURED IN BRIEF]`** and are re-runnable from
[`data/C2_measure_op_grid.py`](../../../data/C2_measure_op_grid.py) →
[`data/C2_op_grid.txt`](../../../data/C2_op_grid.txt) and
[`data/C2_measure_benchmark.py`](../../../data/C2_measure_benchmark.py) →
[`data/C2_benchmark.txt`](../../../data/C2_benchmark.txt), with machine-readable results in
`data/C2_op_grid_results.json` and `data/C2_benchmark_results.json`. Endpoint named in §5.

**Scope boundary.** This lane is about **the variance of a reported result under construction
choices**. It does not rank factors and does not combine them; signal combination and the factor zoo
are permanently spent ground. Where individual variables appear below (`GPA`, `CbOP`, `OPE`, `HML`)
they appear as *objects whose dispersion was measured by someone*, never as candidates.

---

## 0. THE ANSWER, STATED BEFORE THE EVIDENCE

**The bar was a named, quantified dispersion with its source and method, OR a finding that the field
does not measure this. The field DOES measure it — there is a named, five-year-old, fast-growing
literature with its own term of art (`non-standard errors`), its own experiments, its own reference
code, and numbers in exactly the units this brief asked for. Round 2's three independent discoveries
are not three papers' quirks; they are three nodes on a published decision grid, and two of the three
are at the TOP of the published ranking.**

Four things to carry, in descending order of value to this programme:

> **1. THE DISPERSION IS ABOUT AS WIDE AS THE PREMIUM, AND HALF OF DEFENSIBLE CONSTRUCTIONS ARE
> INSIGNIFICANT.** Across 69,120 defensible portfolio-sort constructions of 68 published sorting
> variables, the mean premium is **0.28%/month** and the non-standard error is **0.19%/month**
> unweighted, **0.27%/month** when weighted by how often each choice appears in the literature — a
> dispersion **68%–96% of the premium itself**. The premium is positive in **90%** of constructions
> but **statistically significant in only 50%**, and monotonic in **45%**. For variables the original
> papers reported as significant, the significance rate is **57%**. *(Walter, Weber & Weiss, read in
> full from their own reference implementation's output tables.)*
>
> **2. ROUND 2'S THREE DISCOVERIES ARE NODES 1, 2 AND 3 ON THE PUBLISHED LIST — AND THERE ARE NINE
> MORE THIS PROGRAMME HAS NOT MET.** The two independent rankings agree and they put the **deflator
> first**: in corporate finance, changing the dependent variable's **denominator** moves the
> *t*-statistic by **3.91** on average across 65 real hypotheses, the largest of twelve decisions
> measured. Second on that same list, and entirely absent from round 2, is **outlier treatment**:
> winsorising versus retaining moves *t* by **3.74**, and even winsorising versus *trimming* at the
> same 1/99 cutoff moves it by **0.99**. In asset pricing the top node is **the number of portfolios
> you cut into**, also absent from round 2. §3 is the full ranked list and the nine new traps.
>
> **3. THE FIELD'S HEADLINE VERDICT ON ITS OWN REPLICABILITY RANGES FROM 18% TO 82.4%, AND THE
> BIGGEST SINGLE STEP IS THE BENCHMARK.** Jensen, Kelly & Pedersen's Figure 1 is a ladder from
> Hou–Xue–Zhang's **35%** replication rate to their own **82.4%**, built one construction choice at a
> time; the single largest rung, **61.3% → 82.4%**, is switching from raw return to **CAPM alpha**.
> Hou–Xue–Zhang's own multiple-testing-adjusted figure is **18%**. *Whether finance has a replication
> crisis is, arithmetically, a construction choice* — and the two choices that decide it are round 2's
> **benchmark** and **weighting**.
>
> **4. `[MEASURED IN BRIEF]` I REPRODUCED ROUND 2'S BENCHMARK FINDING ON FREE PUBLIC DATA AND GOT
> SOMETHING WORSE THAN THEY DID.** The equal-weighted high-operating-profitability long leg, over this
> programme's exact window 2010-01 → 2026-06, earns **+0.971%/month (t = +2.46) against cash** and
> **−0.322%/month (t = −2.00) against the CAPM**. Same portfolio, same 198 months, **significant at 5%
> in both directions**. Four negative controls pass, including a factor identity that reproduces
> published `RMW` to 0.005 pp. §5.

**And the honest inversion, which the brief told me not to flinch from.** If the dispersion is as wide
as the premium, a programme that makes each choice exactly once is *not* reporting a premium — it is
reporting one draw from a distribution whose width it has not measured. The literature's three
remedies (**report the distribution**, **pre-register one construction**, **average across them**) all
have published quantified objections, and the strongest objection applies hardest to averaging: if
five binary nodes are wrongly treated as arbitrary when one branch is genuinely better, the justified
region is **3% of the multiverse** and "the central tendency of effects can become misleading or
virtually meaningless." §6 lays out all three with their arguments against. **The one recommendation
that survives every objection is the cheapest: name the nodes, in writing, before the runner exists —
because the grid's size is the thing you can control and the *t*-range grows at ~1.42× per free node.**

---

## 1. THE LITERATURE EXISTS, IT HAS A NAME, AND BOTH SHAPES THE BRIEF ASKED FOR ARE PRESENT

The term of art is **non-standard error (NSE)**, coined in 2021. The slate's overlap audit recorded
`non-standard error` **0 hits** and `Menkveld` **0 hits** across `docs/`. That zero is now the most
consequential gap this campaign has closed.

### 1.1 Shape (a): many teams, one dataset, one question

| study | field | design | type | how established |
|---|---|---|---|---|
| **Menkveld et al., "Nonstandard Errors"**, *Journal of Finance* 79(3), June 2024, 2339–2390 | market microstructure | **164 research teams**, 6 pre-specified hypotheses, one proprietary sample (Deutsche Börse, 17 years of EuroStoxx 50 index futures, **720 million trade records**), plus 34 peer evaluators and 4 feedback stages | `[PEER-REVIEWED]` | **`[read in full]`** — published PDF, Mannheim institutional repository |
| **Breznau et al.**, *PNAS* 119(44), 2022, e2203150119 | sociology | **161 researchers in 73 teams**, identical cross-country survey data, one hypothesis; **1,253 models** from 71 teams with numerical results | `[PEER-REVIEWED]` | **`[read in full]`** — PNAS open access via Essex repository |
| **Huntington-Klein et al.**, IZA DP 13233 (May 2020) → *Economic Inquiry* 59(3), 2021, 944–960 | applied microeconomics | **7 replicators each** on two published causal results | `[PEER-REVIEWED]` (published) | **`[read in full]`** — the **IZA working-paper version**; the *Economic Inquiry* version was **not opened** |
| **Silberzahn et al.**, *AMPPS* 1(3), 2018, 337–356 | psychology | **29 teams, 61 analysts**, one dataset, one question (referee red cards and skin tone); **21 unique method combinations** | `[PEER-REVIEWED]` | **`[read in full]`** — author-hosted PDF |

Menkveld et al. name four further multi-analyst studies they innovate on, and Coqueret names five
(adding Gould et al. 2023 and Huber et al. 2023). Menkveld's N = 164 is, by their own statement,
**"more than twice the size of any of the other multi-analyst samples."**

### 1.2 Shape (b): one team enumerating a construction grid over a fixed question

| study | grid | type | how established |
|---|---|---|---|
| **Walter, Weber & Weiss**, "Methodological Uncertainty in Portfolio Sorts" (previously "Non-Standard Errors in Portfolio Sorts"), SSRN 4164117 | **14 decision nodes**, **68 sorting variables** (40 in the 2022 version), **69,120 feasible paths** for the asset-growth variable | `[WORKING PAPER]` | **`[read in full]` as the authors' own output tables and Internet Appendix**, from their public reference implementation; **the paper's own prose was NOT opened** — see §12 |
| **Soebhag, van Vliet & Verwijmeren**, "Non-Standard Errors in Asset Pricing: Mind Your Sorts", *Journal of Empirical Finance* 78 (2024) 101517 | **11 binary choices → 2,048 combinations** per factor, 11 factors, US 1972-01 → 2021-12 | `[PEER-REVIEWED]` | **`[read in full]`** — the **2022 FoFI conference working paper**; the **published JEF version was NOT opened** (paywall, §13) |
| **Mitton**, "Methodological Variation in Empirical Corporate Finance", *RFS* 35(2), 2022, 527–575 | census of **954 regressions in 604 articles** in the top three finance journals 2000–2018, then **512 specifications × 65 real hypotheses** and **10 binary decisions × 1,000 random variables × 6 regression families** | `[PEER-REVIEWED]` | **`[read in full]`** |
| **Coqueret**, "Forking paths in financial economics", arXiv 2401.08606v1 | up to **9 free "mappings"** across three studies (equity-premium prediction, anomalies, risk premia) | `[WORKING PAPER]` | **`[read in full]`** |
| **Hasler**, "Is the Value Premium Smaller Than We Thought?", *Critical Finance Review* (version dated 2023-01-12) | **6 decisions → 96 HML portfolios**, 1926-07 → 2021-12 | `[PEER-REVIEWED]` (CFR forthcoming) | **`[read in full]`** |
| **Menkveld et al.** *also* runs shape (b): a **weighted multiverse** over up to **9 forks (6,912 paths)** per hypothesis, each requiring the 720M trade records to be processed ~164,000 times on a 128-core national supercomputer | | `[PEER-REVIEWED]` | **`[read in full]`** |

**So the answer to sub-question 1 is unambiguous: both shapes exist, in finance specifically, and one
paper does both.** The field began measuring this in 2021 and the flow has not stopped — the most
recent item in this brief is dated **April 2026**.

---

## 2. THE DISPERSION, IN UNITS A READER CAN USE

Quoted, not paraphrased. Every figure is followed by how well the source was established.

### 2.1 Menkveld et al. (2024) — 164 teams, the same data, the same six hypotheses

`[PEER-REVIEWED]` `[read in full]`. NSE is defined as the **interquartile range of estimates across
teams**; IDR is the interdecile range.

**Estimates** (annual % change; Table I, Panel C, extracted from the published PDF):

| | RT-H1 Efficiency | RT-H2 RSpread | RT-H3 Client volume | RT-H4 Client RSpread | RT-H5 Client MOrders | RT-H6 Client GTR |
|---|---|---|---|---|---|---|
| Q(0.25) | **−6.2** | **−3.6** | −3.5 | **−2.1** | **−0.6** | **−18.2** |
| Median | −1.1 | −0.0 | −3.3 | 0.1 | −0.0 | 0.0 |
| Q(0.75) | **+0.5** | **+3.9** | −2.4 | **+3.8** | **+0.2** | **+3.2** |
| **IQR (= NSE)** | **6.7** | 7.5 | 1.2 | 5.9 | 0.8 | 21.4 |
| IDR | **27.3** | 28.4 | 3.7 | 27.1 | 2.5 | 248.5 |

> **In FIVE of the six hypotheses the interquartile range STRADDLES ZERO.** The middle half of 164
> expert teams, on one dataset, disagree about the sign. *(This sign statement is my own reading of
> their Table I; it is not a sentence they write. The quartile values are theirs verbatim.)*

***t*-statistics** (same table, the panel this brief most needs):

| | RT-H1 | RT-H2 | RT-H3 | RT-H4 | RT-H5 | RT-H6 |
|---|---|---|---|---|---|---|
| Q(0.10) | **−4.7** | **−5.7** | −37.4 | **−3.5** | **−2.3** | **−1.7** |
| Median | −0.7 | −0.1 | −1.8 | 0.1 | 0.0 | 0.0 |
| Q(0.90) | **+1.7** | **+1.5** | −0.3 | **+1.6** | **+1.7** | **+1.2** |
| **IQR of *t*** | **2.2** | **2.3** | 9.9 | **1.9** | **1.3** | **1.7** |
| IDR of *t* | 6.4 | 7.2 | 37.1 | 5.2 | 3.9 | 2.9 |

> **The interquartile range of the *t*-statistic is 1.3 to 2.3 for five of six hypotheses — about the
> width of the entire significance threshold.** On RT-H1, a tenth of teams got *t* < −4.7 and a tenth
> got *t* > +1.7, on the same data.

**NSE versus SE, in their own words:** *"For RT-H1, for example, the median SE across RTs is 2.5%. For
a Gaussian distribution, this implies an IQR of 1.35 × 2.5% = 3.4%, which compares to an NSE of
6.7%."* **So NSE ≈ 2× the sampling-error IQR.** Soebhag et al. read the same paper as implying a
**160%** NSE/SE ratio.

**What reduces it:** a one-SD rise in code reproducibility cuts NSE **25.0%**; a one-SD rise in peer
rating cuts it **33.3%**; a one-SD rise in team quality *raises* it **2.8%**. Four stages of peer
feedback cut NSE **47.2%** (IDR **68.2%**).

**Their own caveat, which biases the reading negative:** *"#fincap NSEs are likely to be an upper bound
for real-world dispersion in (published) estimates"* — published papers have more feedback stages, and
p-hacking, being selective, *narrows* dispersion while introducing bias.

### 2.2 Walter, Weber & Weiss — the asset-pricing grid, 69,120 paths

`[WORKING PAPER]`. **Established by reading the authors' own result tables in full** from their public
reference implementation (`patrick-weiss/PortfolioSorts_NSE`), cross-checked against an independently
sourced abstract figure (see the integrity note at the end of this subsection). Column definitions are
quoted verbatim from their Internet Appendix: `Ratio` = *"the ratio of the dispersion of … premia
relative to the average time-series standard error"*; `Pos.` and `Sig.` = *"the relative number of
positive … premia and t-statistics larger than 1.96"*.

**The master row, across all 68 sorting variables** (`%`/month):

| group | Mean | NSE | NSE_w | Ratio (NSE/SE) | **Pos.** | **Sig.** | Mon. |
|---|---|---|---|---|---|---|---|
| All | **0.28** | **0.19** | **0.27** | **1.10** | **0.90** | **0.50** | 0.45 |
| Significant in the original paper | 0.31 | 0.21 | 0.28 | 1.17 | 0.94 | **0.57** | 0.50 |
| Insignificant in the original paper | 0.14 | 0.13 | 0.19 | 0.69 | 0.68 | **0.15** | 0.19 |

**The profitability cluster** — the one family round 2 left standing. `GPA` is gross profits-to-assets
(Novy-Marx); `CBOP` is cash-based operating profitability; `OPE` is operating profits-to-equity, the
`RMW` variable:

| SV | Mean | NSE | NSE_w | Ratio | **Pos.** | **Sig.** | Mon. |
|---|---|---|---|---|---|---|---|
| **CBOP** | 0.59 | 0.24 | 0.28 | 1.49 | **1.00** | **0.97** | 0.99 |
| **ROE** | 0.49 | 0.26 | 0.38 | 1.55 | 1.00 | 0.91 | 0.84 |
| **ROA** | 0.46 | 0.28 | 0.39 | 1.48 | 1.00 | 0.82 | 0.71 |
| **GPA** | 0.33 | 0.19 | 0.20 | 0.94 | **1.00** | **0.61** | 0.75 |
| **OPE** | 0.32 | 0.14 | 0.18 | 0.77 | 1.00 | 0.73 | 0.64 |
| ATO\* | 0.20 | 0.14 | 0.14 | 0.75 | 1.00 | 0.21 | 0.25 |
| CTO\* | 0.12 | 0.10 | 0.10 | 0.58 | 0.96 | 0.03 | 0.07 |
| Z\* | 0.05 | 0.12 | 0.20 | 0.63 | 0.66 | 0.01 | 0.00 |
| O | 0.05 | 0.09 | 0.11 | 0.53 | 0.78 | 0.01 | 0.01 |
| BL\* | −0.04 | 0.08 | 0.12 | 0.40 | **0.23** | 0.00 | 0.00 |
| TBI | −0.10 | 0.26 | 0.30 | 0.93 | **0.30** | 0.01 | 0.02 |
| **cluster mean** | 0.23 | 0.17 | 0.22 | 0.91 | 0.81 | **0.39** | 0.39 |

(`*` = not significantly related to returns in the original reference paper, their notation.)

> **Gross profitability is positive in 100% of 69,120 defensible constructions and significant in
> 61%.** Round 2 found its *t* falling from >3 to 1.04–1.85 under a lagged deflator, in two
> replications. This is the same fact arrived at from a completely different direction, and it puts a
> number on it: **four in ten defensible constructions of gross profitability do not clear 1.96.**
> `CBOP` is the standout — 97% — which is a real positive datum for round 2's candidate, and it carries
> the cluster's second-highest NSE/SE ratio (1.49) while doing it.

**The benchmark, measured across the whole grid.** Their Internet Appendix repeats the table under
three benchmark models. The profitability rows:

| SV | raw: Mean / Sig. | CAPM α: Mean / Sig. | FF5 α: Mean / Sig. | **q5 α: Mean / Sig.** |
|---|---|---|---|---|
| **CBOP** | 0.59 / 0.97 | 0.65 / 0.99 | 0.64 / 1.00 | 0.32 / 0.82 |
| **GPA** | 0.33 / **0.61** | 0.31 / 0.53 | 0.24 / 0.65 | **0.14 / 0.04** |
| **OPE** | 0.32 / 0.73 | 0.38 / 0.82 | **−0.06 / 0.03** (Pos. **0.29**) | **−0.01 / 0.00** (Pos. 0.52) |
| ROA | 0.46 / 0.82 | 0.54 / 0.90 | 0.41 / 0.92 | 0.12 / 0.21 |
| ROE | 0.49 / 0.91 | 0.55 / 0.97 | 0.35 / 0.84 | 0.09 / 0.22 |

> **The benchmark moves gross profitability's significance rate from 61% of 69,120 constructions to
> 4%.** And **`OPE`'s alpha is positive in 100% of constructions against raw returns and in 29%
> against FF5** — a sign flip driven by nothing but the benchmark. *Caveat, stated because it matters:
> FF5 and q5 both CONTAIN a profitability factor, so those two columns are partly mechanical. The
> CAPM column is not, and it still moves `GPA` from 0.61 to 0.53 and `ROA` from 0.82 to 0.90 — in
> opposite directions for two near-identical variables.*

**NSE is itself benchmark-dependent** (mean over clusters): raw **0.19**, CAPM **0.21**, FF5 **0.19**,
q5 **0.17**; for the profitability cluster 0.17 / 0.21 / 0.16 / 0.15.

**The multiple-testing table** (Romano–Wolf StepM, 5%) carries the subtlest and most important number
in this brief. Its `Median` column is *"the fraction of premia significantly different from the sorting
variable's median premium"*:

| group | differs from own median path | premium ≠ 0 | CAPM α ≠ 0 |
|---|---|---|---|
| All 68 SVs | **0.03** | 0.28 | 0.46 |
| **GPA** | **0.00** | 0.14 | 0.18 |
| CBOP | 0.02 | 0.89 | 0.95 |

> **Only 3% of paths produce a premium statistically distinguishable from the median path's — and for
> gross profitability, 0%.** The constructions disagree materially *and* the data cannot adjudicate
> between them. **You cannot resolve a construction choice empirically within one sample.** That is the
> single hardest fact in this brief for a programme that must pick one.

**Integrity note on this source, stated plainly.** The `.tex` table files I read are not version-
stamped. I validated them against a figure obtained independently (the WU Vienna repository's abstract
and a separate search result both give the paper's headline average monthly NSE as **0.19%**, which
matches the `All` row exactly). The same repository holds **three dated Internet Appendices**, the
oldest of which describes **68** sorting variables while the 2022 abstract describes **40** — so the
tables correspond to a later version than the 2022 abstract, and I have **not** resolved which. §11.

### 2.3 Soebhag, van Vliet & Verwijmeren — 2,048 constructions per factor

`[PEER-REVIEWED]` (JEF 2024); **`[read in full]` in its 2022 FoFI working-paper form.** Metric is the
annualised Sharpe ratio; NSE is its cross-construction standard deviation.

- **`HML`: median Sharpe 0.49 across 2,048 constructions, range 0.15 to 1.24.** Value-weighted `CMA`
  0.18 to 0.90; `UMD` 0.37 to 0.78; `PEAD` 0.73 to 1.76 value-weighted and **0.67 to 2.18**
  equal-weighted. *"In relative terms, the Sharpe ratio can more than double depending on design
  choices."*
- **NSE/SE ratio: 58% (`SMB`) to 190% (`PEAD`), average 118%.** Popularity-weighted: 62% to 189%,
  average **108%**. NSE exceeds SE for 6 of 11 factors unweighted, 5 of 11 weighted.
- **Isolated effects on the average maximum Sharpe ratio:** all-exchange rather than NYSE breakpoints
  **0.55 → 0.73** (their largest single effect); including microcaps **0.59 → 0.68**; equal- rather
  than value-weighting **0.57 → 0.71**; including financials 0.62 → 0.66; 30/70 versus 20/80
  breakpoints 0.63 versus 0.65; most-recent versus June market cap 0.63 → 0.65. *"Choices that do not
  lead to substantially different average Sharpe ratios include choices related to negative book
  equity firms, price filters, and utility firms."*
- **Their census of what the profession actually chooses**, from the 323 empirical asset-pricing papers
  in Harvey & Liu (2019): NYSE breakpoints **41.5%** · value-weighting **58.5%** · include microcaps
  **88.2%** · no price filter **81.7%** · independent sorts **71.8%** · June market equity **67.4%** ·
  exclude financials **28.8%** · exclude utilities **9.9%** · no industry neutrality **88.5%** ·
  include negative book equity **78.0%**. *"No design option is selected in 100% of the cases … The
  percentages reported in Table 2 indicate that no design option in our set is extremely rare.
  **Regardless of the choice being made, a researcher can always cite at least ten other papers making
  the same choice.**"*

### 2.4 Mitton — the field-level placebo, and the ranked decision list

`[PEER-REVIEWED]` `[read in full]`. Census: **954 regressions in 604 articles** in *JF*, *JFE* and
*RFS*, 2000–2018. Then the experiment:

- **Using only the most common methodology, purely random explanatory variables are significant about
  10% / 5% / 1% of the time at the 10% / 5% / 1% levels.** *That is his calibration, and it passes —
  a genuine negative control on the whole apparatus.*
- **One binary decision:** 15% / 7% / 2%.
- **Ten binary decisions:** **94% / 73% / 23%.** *"When the researcher has discretion over 10 binary
  methodological decisions, 94% of randomly generated variables can be found significant at the 10%
  level with at least one methodological combination, 73% can be found significant at the 5% level,
  and 23% can be found significant at the 1% level."*
- **A base rate nobody should forget** (his footnote 21): **84% of quasi-random Compustat ratio
  variables, and 51% of actual proposed leverage determinants, are already significant under the
  single most common methodology.**
- **65 proposed leverage determinants × 512 common specifications: only ONE of the 65 is significant
  at the 10% level or better across all 512. On average each is significant in 43% of
  specifications.** *"Researchers should focus less on defending the robustness of a result and more
  on understanding why a result is robust in some specifications and not in others."*

### 2.5 Coqueret — the growth law of the achievable *t*-range

`[WORKING PAPER]` `[read in full]`. Defines the **average range of intervals (ARI)** — the mean width
of the "hacking interval" of achievable *t*-statistics — as a function of the number of free design
choices, and fits it:

```
ARI(n) = 0.78 × 1.42^n
```

| free choices *n* | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|
| **ARI (*t*-units)** | 0.78 | 1.66 | 2.66 | **3.85** | 5.28 | 7.05 | 9.29 | 12.15 | **15.75** |

> **Four free construction choices already buy an average *t*-range of 3.85 — wider than the entire
> −1.96 to +1.96 band.** His abstract states the growth conservatively as *"at least 30%"* per added
> degree of freedom; his fitted table says **42%**. Both are his; I weight the fitted table, because it
> is the estimate and the abstract is the rounded claim.

### 2.6 The field's verdict on itself, as a construction ladder

Jensen, Kelly & Pedersen, *JF* 78(5), 2023, 2465–2518. `[PEER-REVIEWED]` `[read in full]`, publisher
version. Their Figure 1 is the cleanest dispersion object in the discipline:

| rung | replication rate | what changed |
|---|---|---|
| 1 | **35.0%** | Hou, Xue & Zhang (2020): deciles, straight NYSE breakpoints, straight value-weights, mixed accounting-lag schemes, **raw returns** |
| 2 | **55.6%** | JKP baseline: **tercile** spreads, breakpoints from stocks above the NYSE 20th percentile, **always lag accounting data four months**, **capped** value-weighting, one-month holding, longer sample, +15 factors |
| 3 | **61.3%** | excluding 34 factors whose **original** papers found no significant alpha |
| 4 | **82.4%** | **raw return → CAPM alpha** |
| 5 | 75.6% | Benjamini–Yekutieli multiple-testing correction |
| 6 | 82.4% | their Bayesian multiple-testing treatment |
| — | **18%** | **Hou, Xue & Zhang's OWN multiple-testing-adjusted figure** |

> **18% to 82.4% — a 4.6× range on the most consequential summary statistic in empirical asset
> pricing, and every rung is a construction or inference choice.** The largest rung is the benchmark.
> The construction differences are listed verbatim in their footnote 4.

Their argument for the benchmark rung is the clearest published statement of round 2's point that the
benchmark is *a different question*: *"Hou, Xue, and Zhang (2020) analyze and test factors' raw
returns, but if we wish to learn about 'anomalies,' economic theory dictates the use of risk-adjusted
returns. … When the raw return is significant but the alpha is not, this simply means that the factor
is taking risk exposure and the risk premium is significant, which does not indicate anomalous factor
returns."* **Note what that reasoning implies for a cash-funded book: if you are paid for the risk
exposure and you are funded by cash, the raw return IS your answer and the alpha is the wrong
question.** §4.

**A third camp, which the two-camp framing hides.** JKP's footnote 1 records that Chen & Zimmermann
*"consider pure replication, attempting to use the same data and methods as the original papers for a
large number of factors. They are able to reproduce nearly 100% of factors."* `[snippet only]` — I did
not open Chen & Zimmermann. **Reproduction ≈ 100%; scientific replication 35%–82%; robustness to a
construction grid ≈ 50%.** Three different questions, three different numbers, routinely conflated.

### 2.7 The multi-analyst studies outside finance, for calibration

- **Silberzahn et al. (2018)** `[read in full]`: *"Twenty-nine teams involving 61 analysts used the
  same data set … the estimated effect sizes ranged from **0.89 to 2.93 (Mdn = 1.31)** in odds-ratio
  units. **Twenty teams (69%) found a statistically significant positive effect, and 9 teams (31%) did
  not.**"* The 29 teams used **21 unique combinations** of methods.
- **Breznau et al. (2022)** `[read in full]`: 161 researchers, 73 teams, 1,253 models, **166 distinct
  research-design decisions** coded, **no two of 1,261 models were 100% identical**, results *"ranging
  from large negative to large positive"*, and **"More than 95% of the total variance in numerical
  results remains unexplained even after qualitative coding of all identifiable decisions in each
  team's workflow."**
- **Huntington-Klein et al.** `[read in full]`, IZA version: *"No two replicators reported the same
  sample size. Statistical significance varied across replications, and for one of the studies the
  effect's sign varied as well. **The standard deviation of estimates across replications was 3–4 times
  the typical reported standard error.**"* And the detail that should be read twice by anyone who
  writes a methods section:

> *"Of particular interest are replications 1 and 7, which do not differ in sample construction in any
> obvious way, and **which likely would have reported identical data construction procedures if these
> were real studies**, but for which sample sizes differ by about 4,000. **When using identical models
> they have similarly-sized estimates of opposite signs.**"*

**Breznau's >95%-unexplained is the one that should worry this programme most.** It means the
dispersion is *not* mostly attributable to the nodes you can enumerate. Naming your nodes bounds the
part of the problem you can see; it does not bound the problem.

---

## 3. WHICH CHOICES ARE LOAD-BEARING — THE RANKED LISTS, AND THE NINE TRAPS ROUND 2 HAS NOT MET

**Two independent rankings exist, in two different subfields, and they agree on the deflator.**

### 3.1 Asset pricing: Walter, Weber & Weiss's mean-absolute-deviation ranking

Normalised MAD across branches of each node, all 68 sorting variables (`All`) and the profitability
cluster (`Pro.`). Read in full from their own `04_mad_acrossnodes.tex`.

| rank | node | All | **Pro.** | on round 2's list? |
|---|---|---|---|---|
| 1 | **Breakpoint quantiles (main)** — how many portfolios you cut into | **1.08** | 1.09 | **NO** |
| 2 | **Weighting scheme** | 0.99 | 1.01 | **yes** (`B1`) |
| 3 | **Negative earnings** — whether loss-makers are dropped | 0.94 | **1.24 (#1)** | **NO** |
| 4 | **Size exclusion** | 0.85 | 0.90 | partly |
| 5 | **Sorting-variable lag** | 0.85 | 0.64 | yes (`C1`'s lane) |
| 6 | **Breakpoint exchanges** (NYSE vs all) | 0.82 | 0.88 | **NO** |
| 7 | **Financials** | 0.75 | 1.08 | **NO** |
| 8 | **Double sort** (single / dependent / independent) | 0.69 | 0.73 | **NO** |
| 9 | Breakpoint quantiles (secondary) | 0.69 | 0.71 | **NO** |
| 10 | **Rebalancing** (monthly vs annual) | 0.59 | 0.59 | **NO** |
| 11 | Utilities | 0.51 | 0.73 | **NO** |
| 12 | Stock-age exclusion (> 2 years) | 0.43 | 0.48 | **NO** |
| 13 | **Price exclusion (none / >$1 / >$5)** | **0.35** | 0.38 | — *the programme's `$5` floor* |
| 14 | Negative book equity | 0.22 | 0.27 | **NO** |

Branch-level means from the same source (`%`/month, all 68 SVs), which put magnitudes on the top
nodes: **deciles 0.31 vs quintiles 0.25** · **all-exchange breakpoints 0.31 vs NYSE 0.25** ·
**equal-weighted 0.30 (Sig. 0.56) vs value-weighted 0.26 (Sig. 0.45)** · **no size filter 0.33
(Sig. 0.57) vs NYSE-20% filter 0.25 (Sig. 0.45)** · **price filter: $0 → 0.29, $1 → 0.28, $5 →
0.27** · lag 1m 0.27 (**Sig. 0.34**), 3m 0.28 (0.48), 6m 0.25 (0.46), Fama-French 0.25 (0.50) ·
rebalancing annual 0.26 vs monthly 0.27.

### 3.2 Corporate finance: Mitton's Table 8, average |Δ*t*| over 65 real hypotheses

| rank | decision changed | avg \|Δ*t*\| | on round 2's list? |
|---|---|---|---|
| 1 | **Dependent variable with a different DENOMINATOR** | **3.91** | **yes — `B2`'s deflator, ranked FIRST** |
| 2 | **Winsorise at 1st/99th → retain outliers** | **3.74** | **NO** |
| 3 | Continuous explanatory variable → dummy | 3.72 | **NO** |
| 4 | **Winsorise at 1/99 → winsorise at 5/95** | 1.83 | **NO** |
| 5 | Dependent variable with a different **NUMERATOR** | 1.77 | partly (`B2`) |
| 6 | **Contemporaneous → lagged explanatory variable** | 1.41 | yes (`C1`) |
| 7 | Level → logged dependent variable | 1.37 | **NO** |
| 8 | Level → logged explanatory variable | 1.10 | **NO** |
| 9 | **Winsorise at 1/99 → TRIM at 1/99** | 0.99 | **NO** |
| 10 | Most common → second most common size control | 0.67 | **NO** |
| 11 | Include all industries → exclude financials | 0.27 | **NO** |
| 12 | Add the next most common control | 0.26 | **NO** |

And for quasi-random Compustat ratios in **profitability** regressions specifically: **winsorising
changes *t* by 12.86 on average; switching the dependent variable from ROA to ROE changes it by
12.31.**

### 3.3 Menkveld's multiverse: what refracts hardest

*"Two particularly powerful ones are **sampling frequency** and **the statistical model**."* And the
mechanism they identify is an identity, not a taste: *"Using a nonlinear model at high frequency to
estimate a low-frequency trend can therefore add substantial noise (Jensen's inequality)."*
Specifically, **teams that sampled daily to estimate an annual trend and used return relatives rather
than log-differences or a trend-stationary approach got systematically different answers**, because
`E[∏ Xₜ/Xₜ₋₁] > ∏ E[Xₜ/Xₜ₋₁]` for a convex function.

> **Sampling frequency is round 2's session-boundary finding under another name, and it is one of the
> two strongest refractors in a 164-team experiment.** And arithmetic-versus-geometric compounding is
> exactly the quantity `CLAUDE.md`'s "right-quantity" assertion is meant to catch.

### 3.4 THE NINE TRAPS THIS PROGRAMME HAS NOT DISCOVERED

Consolidated from §3.1–§3.3 plus §8. Ranked by the evidence that they are load-bearing, **not** by my
guess at their relevance.

1. **OUTLIER TREATMENT.** Mitton's #2 (|Δ*t*| = 3.74 on real hypotheses, **12.86** on quasi-random
   profitability ratios), and it is *three* separate nodes: winsorise-or-not, the cutoff (1/99 vs
   5/95, |Δ*t*| 1.83), and winsorise-versus-trim (|Δ*t*| 0.99). **`CLAUDE.md` already mandates trimming
   1% from both tails when reporting trade distributions — which is a reporting convention, not a
   construction convention, and the literature says the two are different decisions with different
   effects.** Nothing in `docs/` appears to ask what the *signal construction* does with outliers.
2. **QUANTILE COUNT / SLOT COUNT.** The #1 asset-pricing node. Deciles give a 24% higher premium than
   quintiles and a *lower* monotonicity rate (0.33 vs 0.45). This programme's analogue is `N_SLOTS`,
   and `FINDINGS.md` §10 already records that `sel = rank < N_SLOTS` makes the slot count *also* the
   refill pool — so it is simultaneously a construction node and a path-dependence mechanism.
3. **DROPPING LOSS-MAKERS / NEGATIVE-DENOMINATOR FIRMS.** The **#1 node for profitability sorts**
   (MAD 1.24). Mechanically it truncates the signal distribution exactly where the signal is most
   extreme. Round 2's deflator identity `GP/AT = (GP/AT₋₁) ÷ asset growth` has a sibling here:
   whatever you do about negative numerators or denominators *is* a conditioning choice on the signal.
4. **REBALANCING FREQUENCY AND THE ARBITRARY REBALANCING DATE.** MAD 0.59. Hasler's entire paper is
   one instance: the June convention in `HML`. **And it is not arbitrary — it carries a momentum
   exposure** (§4).
5. **DATA VINTAGE.** §8.1. The same code on the same named dataset a year apart. *A third of
   long-short anomaly alphas lose significance on factor vintage alone.*
6. **THE DIVIDEND-REINVESTMENT TIMING CONVENTION INSIDE THE RETURN SERIES.** §8.1. CRSP's new tape
   reinvests on the ex-date and compounds daily; the old tape reinvested at month-end. **9.62% of
   monthly returns were rewritten by more than 1 bp.** For a book whose edge is overnight and which
   already has a finding that *"15m is fully adjusted, daily is not"*, this is the same hazard class.
7. **RETURN MEASUREMENT: LEVEL VS LOG, RELATIVES VS LOG-DIFFERENCES, AND THE COMPOUNDING AXIS.**
   Mitton |Δ*t*| 1.37/1.10; Menkveld's Jensen-inequality refractor.
8. **STOCK-AGE / LISTING-AGE FILTERS.** MAD 0.43 — small, but a node nobody here has named, and on a
   panel that is **~35.7% dead** the age filter interacts with the survivorship axis the programme
   already measures.
9. **DEPENDENT-VS-INDEPENDENT SORTING AND THE ORDER OF A MULTI-WAY SORT.** MAD 0.69. Soebhag et al.:
   *"when we consider a 2×3×3 dependent sort, it is not clear what the ordering should be, allowing
   for a wider playing field."*

**And one piece of good news, measured.** The **price filter is near the bottom of the asset-pricing
ranking** (MAD 0.35, the second-lowest of fourteen), and the branch means say a `$5` floor costs about
**2 bp/month** of measured premium relative to no floor. Soebhag et al. independently classify price
filters among *"choices that do not lead to substantially different average Sharpe ratios"* — while
also finding that **excluding sub-$5 stocks significantly reduces factor exposure but significantly
improves liquidity and reduces transaction costs**, with **10 of their 11 construction choices showing
significant effects on transaction costs** (30/70 vs 20/80 breakpoints = 6 bp; NYSE vs all-exchange
breakpoints = 15 bp). **The programme's most unusual construction choice relative to the literature's
conventions — a price floor, which 81.7% of papers do not impose — is one of the least load-bearing
for the premium and one of the more load-bearing for cost.** Given the measured 33.8 bp/side, that
trade runs in the programme's favour.

---

## 4. ARBITRARY, OR A DIFFERENT QUESTION? — THERE IS A PUBLISHED TAXONOMY, AND ROUND 2 FOUND ONE OF EACH

**Yes, the distinction is drawn explicitly, it has a name, and it is the central argument of a
peer-reviewed paper.**

**Del Giudice & Gangestad, "A Traveler's Guide to the Multiverse"**, *AMPPS* 4(1), 2021.
`[PEER-REVIEWED]` `[read in full]` (author-hosted PDF). Their taxonomy, verbatim from the abstract:

- **Type E — principled equivalence.** *"The alternative specifications can be expected to be
  practically equivalent, and choices among them can be regarded as effectively arbitrary."*
- **Type N — principled nonequivalence.** *"The alternative specifications are nonequivalent according
  to one or more nonequivalence criteria. As a result, some of the alternatives can be regarded as
  objectively more reasonable or better justified than the others."*
- **Type U — uncertainty.** *"There are no compelling reasons to expect equivalence or nonequivalence,
  or there are reasons to suspect nonequivalence but not enough information to specify which
  alternatives are better justified. In this scenario, multiverse-style analyses should be carried out
  with a deliberately exploratory approach."*

And **three criteria** for deciding: **measurement nonequivalence**, **effect nonequivalence**,
**power/precision nonequivalence**.

Simonsohn, Simmons & Nelson (*Nature Human Behaviour* 4, 2020, 1208–1214; `[PEER-REVIEWED]`
`[read in full]`) draw the same line with a worked example that transplants cleanly: controlling for
marital status when estimating the effect of children on happiness *"may be interesting and
informative, but it does not constitute an exercise in robustness because both sets of results do not
provide two a priori equally valid answers to the same research question."* Their arbitrary cases —
event-window length, which well-being measure, the full-time-equivalence of part-time work — are
Type E.

### 4.1 Placing round 2's three, and three more, in the taxonomy

| choice | type | why |
|---|---|---|
| **The deflator** (`GP/AT` vs `GP/AT₋₁`) | **N** | Round 2 established the identity: `GP/AT = (GP/AT₋₁) ÷ asset growth`. The two are not two measures of one thing; one of them is a composite of profitability and investment. **Effect nonequivalence.** Mitton ranks it #1 of twelve. |
| **The benchmark** | **N** | JKP's own argument: the alpha and the raw return answer different questions, and which one you want depends on whether you are paid for the exposure. **For a book funded by cash and competing with cash, the raw return is the answer and the alpha is a different question.** |
| **The session boundary / sampling frequency** | **N** | Menkveld's Jensen-inequality result makes the frequency choice a *systematic*, not random, shifter of a low-frequency estimate. |
| **Rebalancing month (Hasler's `HML`)** | **N, discovered to be N** | It *looks* like the purest Type E choice in finance. Hasler finds the original June convention gives *"a less negative beta with momentum than the average HML portfolio"*, and concludes: **"The inference whether or not the original value premium is biased therefore hinges on the unresolved debate whether or not momentum is an asset pricing factor."** A calendar convention turned out to encode a factor exposure. |
| **Industry neutralisation** | **N, and question-dependent** | Soebhag et al. refuse to recommend either branch: the conservative choice is not to neutralise, *"however, this choice could depend on the particular research question one is after."* |
| **Winsorise vs trim at the same cutoff** | **E, probably** | No published argument that one is better; |Δ*t*| = 0.99 anyway. The cleanest Type E node I found with a measured magnitude. |

> **The pattern, and it is the uncomfortable part: every node that looked Type E and was then examined
> closely turned out to be Type N.** The deflator was an identity. The calendar convention was a
> momentum exposure. The sampling frequency was Jensen's inequality. **Default to Type U, not Type E.**

---

## 5. `[MEASURED IN BRIEF]` — AN INDEPENDENT GRID, AND ROUND 2'S BENCHMARK FINDING REPRODUCED

**Endpoint.** `https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/` — three free files:
`Portfolios_Formed_on_OP_CSV.zip`, `6_Portfolios_ME_OP_2x3_CSV.zip`,
`F-F_Research_Data_5_Factors_2x3_CSV.zip`. All HTTP 200, `application/x-zip-compressed`, 135,027 /
105,808 / 11,948 bytes. **Vintage, stated because §8.1 makes it load-bearing: the OP file's own first
line reads `This file was created using the 202607 CRSP database.`** Monthly coverage 196307–202607;
757 months. `OP` is Fama-French operating profitability — *"operating profits (sales minus cost of
goods sold, minus selling, general, and administrative expenses, minus interest expense) divided by
book equity at the last fiscal year end of the prior calendar year"* — i.e. this is the **`OPE`** row
of §2.2, not `GPA`. Breakpoints and portfolios include utilities and financials. Pure-stdlib Python;
*t* is iid, `mean/(sd/√n)`, stated rather than assumed.

### 5.1 The four negative controls, all reported

| control | expectation | result |
|---|---|---|
| **NC1 — the factor identity.** `RMW` must equal `½(SMALL HiOP + BIG HiOP) − ½(SMALL LoOP + BIG LoOP)` rebuilt from the 6 size-OP portfolios | match to published rounding | **n = 757, max\|diff\| = 0.0050, mean\|diff\| = 0.00254** pp/month — consistent with two-decimal publication rounding. **PASS.** A parsing or column error would not produce this. |
| **NC2 — a quantity that must be exactly zero.** `Hi30 − Hi30` | 0 nonzero months | **0 of 757. PASS.** |
| **NC3 — a census that must return zero.** Missing-value sentinels (`−99.99`, `−999`) in the monthly panels; dates before 196307 | 0, 0, 0 | **0, 0, 0. PASS.** |
| **NC4 — proof I did not read one block twice.** mean\|VW Hi30 − EW Hi30\| | > 0 | **2.2166 pp/month. PASS.** |
| **NC5 — a census that returned the WRONG zero, and I am reporting it.** Months outside `[196307, 202606]` | I predicted 0 | **Returned 1.** The file extends one month further than I assumed (202607 exists). My grid caps at 202606, so no measured number is affected — but **my stated expectation was wrong, not the data**, and the control is what caught it. |

### 5.2 The construction grid — 24 cells, two lenses

`{value-weighted, equal-weighted} × {30/70 terciles, 20/80 quintiles, deciles} × {spread Hi−Lo, long
leg in excess of the risk-free rate} × {full sample, the programme's window}`. All in `%`/month.

| weighting | cut | window | lens | mean | *t* |
|---|---|---|---|---|---|
| VW | tercile | full 1963-07..2026-06 | spread | +0.224 | **+2.37** |
| VW | quintile | full | spread | +0.201 | +1.74 |
| VW | decile | full | spread | +0.246 | +1.57 |
| EW | tercile | full | spread | +0.079 | **+0.74** |
| EW | quintile | full | spread | +0.083 | +0.68 |
| EW | decile | full | spread | +0.113 | +0.75 |
| VW | tercile | **prog 2010-01..2026-06** | spread | +0.194 | +1.03 |
| VW | quintile | prog | spread | +0.099 | +0.40 |
| VW | decile | prog | spread | +0.308 | +0.93 |
| EW | tercile | prog | spread | +0.215 | +0.98 |
| EW | quintile | prog | spread | +0.245 | +0.92 |
| EW | decile | prog | spread | +0.356 | +1.08 |
| VW | tercile | full | **long leg − RF** | +0.701 | **+4.35** |
| VW | quintile | full | long leg − RF | +0.687 | +4.22 |
| VW | decile | full | long leg − RF | +0.693 | +4.12 |
| EW | tercile | full | long leg − RF | +0.856 | +4.11 |
| EW | quintile | full | long leg − RF | +0.841 | +3.91 |
| EW | decile | full | long leg − RF | +0.830 | +3.71 |
| VW | tercile | prog | long leg − RF | +1.179 | +3.92 |
| VW | quintile | prog | long leg − RF | +1.134 | +3.77 |
| VW | decile | prog | long leg − RF | +1.242 | +3.99 |
| EW | tercile | prog | long leg − RF | +0.971 | +2.46 |
| EW | quintile | prog | long leg − RF | +0.937 | +2.33 |
| EW | decile | prog | long leg − RF | +0.888 | +2.13 |

Plus the 2×3 convention: **published `RMW` is +0.243%/month (*t* = +2.97) full sample and
+0.126%/month (*t* = +0.84) over 2010-01..2026-06.**

**Five findings.**

1. **Weighting alone moves the full-sample tercile spread from +0.224 to +0.079 %/month — a factor of
   2.8 — and the *t* from +2.37 to +0.74, straight across the 1.96 line.** One node, verdict reversed.
2. **The full-sample spread's *t* ranges [+0.68, +2.37] across six defensible cells**, and **the range
   of means (0.167 pp/month) is essentially equal to the midpoint of those means (0.163 pp/month).**
   *The dispersion is as wide as the premium.* Measured, on free data, on one variable, with six cells.
3. **Narrowing the extremes raises the mean and lowers the *t*.** VW full sample: tercile 0.224
   (*t* 2.37) → quintile 0.201 (1.74) → decile 0.246 (1.57). Volatility rises faster than the spread.
   That is the mechanism behind WWS's #1 node and it is worth knowing before anyone picks a slot count.
4. **The two lenses give opposite verdicts, in both windows.** Spread: significant in **1 of 6** cells
   full-sample and **0 of 6** over the programme's window. Long leg in excess of cash: **6 of 6** and
   **6 of 6**. *The same underlying sort is "dead" or "strong" depending on which object you score —
   and a cash-funded long-only book scores the second one.*
5. **Zero sign flips in 24 cells.** This is the honest negative, and it agrees with WWS's *"their sign
   is remarkably stable."* **Construction choices here moved magnitude and significance; they did not
   move the sign.** Until the benchmark entered.

### 5.3 The benchmark, same leg, same months — round 2's finding reproduced and exceeded

Round 2's `B1` found one paper's `CbOP` long leg at **+14 bp/month (*t* 1.95) against CAPM** and
**+35 bp/month (*t* 5.98) against FF3**. I ran the analogous test on French's OP portfolios against
five benchmarks. *(`FF3+RMW` and `FF5` contain `RMW`, which is built from this very sort, so those two
columns are partly mechanical and are shown only for completeness; the load-bearing comparisons are
**cash**, **CAPM** and **FF3**.)*

**Full sample 1963-07 → 2026-06, n = 756:**

| leg | cash | CAPM α | FF3 α | FF3+RMW α | FF5 α |
|---|---|---|---|---|---|
| VW Hi30 long leg | +0.701 (*t* 4.35) | +0.119 (3.31) | +0.160 (4.88) | +0.065 (3.02) | +0.068 (3.14) |
| VW Hi20 long leg | +0.687 (4.22) | +0.107 (2.43) | +0.156 (3.83) | +0.052 (1.71) | +0.048 (1.56) |
| VW Hi10 long leg | +0.693 (4.12) | +0.113 (**1.82**) | +0.153 (2.50) | +0.024 (0.46) | +0.016 (0.31) |
| **EW Hi30 long leg** | +0.856 (4.11) | +0.166 (**1.76**) | +0.039 (**0.74**) | **−0.073** (−1.68) | −0.064 (−1.48) |
| VW Hi30−Lo30 spread | +0.224 (2.37) | +0.318 (3.47) | +0.391 (4.69) | +0.107 (2.83) | +0.088 (2.34) |
| **EW Hi30−Lo30 spread** | +0.079 (0.74) | +0.105 (0.98) | +0.060 (0.62) | **−0.204 (−2.94)** | −0.202 (−2.88) |

**The programme's window 2010-01 → 2026-06, n = 198:**

| leg | cash | CAPM α | FF3 α | FF3+RMW α | FF5 α |
|---|---|---|---|---|---|
| VW Hi30 long leg | +1.179 (*t* 3.92) | +0.130 (1.97) | +0.077 (1.51) | +0.051 (1.29) | +0.048 (1.22) |
| VW Hi20 long leg | +1.134 (3.77) | +0.096 (1.20) | +0.045 (0.65) | +0.016 (0.28) | +0.006 (0.10) |
| VW Hi10 long leg | +1.242 (3.99) | +0.199 (1.82) | +0.144 (1.39) | +0.114 (1.18) | +0.099 (1.04) |
| **EW Hi30 long leg** | **+0.971 (+2.46)** | **−0.322 (−2.00)** | −0.134 (−1.60) | −0.171 (−2.44) | −0.169 (−2.41) |
| VW Hi30−Lo30 spread | +0.194 (1.03) | +0.399 (2.16) | +0.245 (1.59) | +0.138 (1.81) | +0.120 (1.63) |
| EW Hi30−Lo30 spread | +0.215 (0.98) | +0.273 (1.20) | +0.142 (0.72) | +0.034 (0.23) | +0.038 (0.27) |

> **THE HEADLINE. The equal-weighted high-operating-profitability long leg, over 2010-01 → 2026-06,
> earns +0.971%/month with *t* = +2.46 against cash and −0.322%/month with *t* = −2.00 against the
> CAPM. Same 198 months, same portfolio, significant at 5% in BOTH DIRECTIONS. The CAPM contains no
> profitability factor, so this is not mechanical.**

The mechanism is plain and it is the *reason* the benchmark is Type N: an equal-weighted long leg over
a decade-and-a-half bull market carries a beta above one, and subtracting `β × (Mkt−RF)` removes more
than the leg earned. **Against cash you are paid for the beta. Against the CAPM you are not. This
programme is funded by cash.** That is not a nuance to be resolved by convention; it is the question.

Benchmark-induced ranges on the same leg and window (cash through FF5): VW Hi30 long leg full sample
**10.8×** (+0.065 to +0.701) with *t* never crossing 1.96; VW Hi10 long leg full sample **42.7×**
(+0.016 to +0.693) with *t* from +0.31 to +4.12; VW Hi20 long leg over the programme's window
**193×** (+0.006 to +1.134).

**The honest caveat on my own measurement.** Six construction cells is a small grid next to 69,120;
*t*-statistics are iid and not Newey-West; the long-leg-minus-`RF` lens is *not* what the NSE papers
measure (§8.3); and the whole thing sits on one CRSP vintage (§8.1). **It is a demonstration that the
published magnitudes reproduce on free data, not an independent estimate of the NSE.**

---

## 6. THE HONEST INVERSION — WHAT FOLLOWS, AND THE ARGUMENTS AGAINST EACH REMEDY

**The premise is now measured rather than feared.** Across 69,120 constructions, NSE/premium is
**0.19/0.28 = 0.68** unweighted and **0.27/0.28 = 0.96** weighted; NSE/SE averages **1.10** there,
**1.18** in Soebhag et al., and **~2×** in Menkveld et al.; only **50%** of defensible constructions
clear 1.96, and only **3%** of them differ significantly from the median path. **So: the dispersion is
of the same order as the premium, it is of the same order as or larger than the sampling error the
programme's *t*-statistics report, and it cannot be resolved from inside one sample.**

**And this programme is worse placed than the literature on the one axis that matters most.** Its
effective breadth is **~10 independent instruments**. A *t*-statistic earned on ~10 independent bets
has no room to absorb a construction grid whose average achievable *t*-range is 3.85 at four free
nodes and 15.75 at nine (Coqueret). **The NSE and the SE are not competing for the same budget — they
add — and here the SE is already large.**

The published remedies, with their published objections.

### 6.1 Report the distribution (specification curve / multiverse / specification check)

**For.** Simonsohn, Simmons & Nelson's three steps: *"(1) identifying the set of theoretically
justified, statistically valid and non-redundant specifications; (2) displaying the results
graphically, allowing readers to identify consequential specifications decisions; and (3) conducting
joint inference across all specifications."* Their joint inference uses **resampling under the null**
(the permutation machinery this programme already runs), with three test statistics — the median
effect, the count of significant specifications of the dominant sign, and a Stouffer-aggregated mean
*Z* — and they recommend reporting both the count and the aggregate. Soebhag et al., Mitton and
Coqueret all independently recommend the same thing. Coqueret's framing is the most aggressive: report
*"as if extensive robustness checks were in fact constituent of the baseline research protocol."*

**Against.**
- **It can be gamed.** Coqueret: *"it is possible to push the limits of data-snooping to the extreme
  by reporting only the combinations of design choices that fit a particular narrative."*
- **It costs what this programme is short of.** Coqueret: *"given the amount of time required to
  generate comprehensive results, the research question must be inherently simple. Each path should
  not take more than a handful of minutes."* Menkveld's multiverse needed a 128-core national
  supercomputer and *"a few days instead of a few months"* per hypothesis.
- **The sign test is not what it looks like.** Simonsohn et al.: *"because many of the different
  specifications are similar to each other … the results obtained from different specifications are
  not independent. Therefore, even with shuffled datasets we do not expect half the estimates to be
  positive and half negative."* **This is the programme's own finite-group null problem in a new
  guise: the specifications are the group, they are correlated, and the null's quantiles must be
  generated, never assumed.**

### 6.2 Pre-register one construction (and converge on a convention)

**For.** Soebhag et al.'s concrete, quantified proposal: fixing three choices — **NYSE breakpoints,
exclude microcaps, value-weighting** — *"reduces the average non-standard error by 70%"* (and 73% if
four further Fama-French conventions are fixed, i.e. almost no further gain). This is the only remedy
in the literature with a measured effect size.

**Against, and this one lands hard on this programme.**
- **Their recommended convention is the OPPOSITE of this programme's construction on all three axes.**
  The programme is equal-weighted, holds small names above a `$5` floor, and uses no NYSE breakpoints.
  Adopting the literature's NSE-minimising convention would mean abandoning the universe the
  programme exists to trade. Soebhag et al. anticipate exactly this: *"researchers might have a
  particular interest in smaller firms, or they might want to study a mechanism most applicable to
  illiquid stocks. Providing a clear explanation for design choices that deviate from the above
  recommendation in such studies appears warranted."* **The remedy for a deviating construction is
  disclosure, not conversion.**
- **Convergence destroys the ability to ask different questions.** Soebhag et al.: *"Variation in
  choices allows researchers to customize samples and empirical tests to tackle specific research
  questions."*
- **Pre-registration bounds only the nodes you named.** Breznau et al.: **>95% of the variance is
  unexplained even after coding every identifiable decision.** Huntington-Klein et al.: two
  replications *"which likely would have reported identical data construction procedures"* produced
  **opposite signs**.

### 6.3 Average across constructions

**For.** Hasler's is the cleanest instance: average the 96 `HML` portfolios monthly into one. He
justifies it — *"This average HML portfolio is a valuable proxy for the value factor because it
reflects an average decision that mitigates a decision-specific chance result"* — and he checks that
it is still one bet: **the first principal component of the 96 portfolios explains 91% of their
variation.** Coqueret agrees and adds an out-of-sample argument: *"Averaging returns, premia or
loadings across many configurations strengthens inference. We find high cross-period correlation
between anomalies returns' once they have been averaged across many paths. This removes the risk of an
outlier point from one specific set of implementation choices and increases the odds of
generalization out-of-sample."*

**Against — and this is the most quantified objection in the whole corpus.** Del Giudice & Gangestad:

> *"Just a few decisions incorrectly treated as arbitrary can quickly explode the size of the
> multiverse, drowning reasonable effect estimates in a sea of unjustified alternatives. … **Five
> binary decision nodes expand the multiverse by a factor of 32. If one alternative is justifiable
> over the other in each case, the region defined by justified choices ends up occupying just 3% of
> the total multiverse. If the decision nodes involve three alternatives each, the corresponding
> figure is 0.4%.** … **when the proportion of effects that best estimate the effect of interest is
> very small, the central tendency of effects can become misleading or virtually meaningless.**"*

And: *"the combinatorial explosion of unjustified specifications may, ironically, exaggerate the
perceived exhaustiveness and authoritativeness of the multiverse while greatly reducing the
informative fraction."* **Given §4's finding that every node examined closely turned out to be Type N,
averaging over this programme's nodes would be averaging over mostly-non-arbitrary choices. That is
the case the objection is built for.**

**Hasler also supplies the negative evidence against his own remedy, and it is the most important
single result for the `C2`/`C4` junction.** In-sample (1963-07..1991-12) the original minus the average
is **+0.08%/month (*t* 1.72)**, and the original sits **at or above 85% of the 96 alternatives**. But
**in the pre-sample the same difference is +0.07%/month (*t* 1.34)**, which he calls *"somewhat at odds
with the idea of a bias"*, and **post-sample +0.05%/month (*t* 0.72)**. *If the published
construction's advantage exists before the published sample, it is not a chance artefact of
construction search — it may simply be a better construction.* He does not resolve it; nor do I.

### 6.4 The remedy that survives every objection, because it is free

**Name the nodes in writing before the runner exists, and state which branch you took and why.** It is
what Soebhag et al. ask of deviating studies, what Simonsohn et al.'s step (1) requires before any
inference, what Del Giudice & Gangestad's Type E/N/U triage operates on, and the only lever over
Coqueret's `1.42^n`: **the exponent is the number of nodes you leave free, and writing a node down
fixes it.** This programme already has the machinery — [R8](../../RULES.md#r8)'s pre-registration
before the runner exists — and **the gap is that its pre-registrations fix the hypothesis, not the
construction grid.** Mitton's own closing advice converges here: *"researchers should focus less on
defending the robustness of a result and more on understanding why a result is robust in some
specifications and not in others."*

**One further caution on over-correction, quantified.** Mitton shows that requiring robustness checks
does cut false positives — random hypotheses found significant fall from 94%/73%/23% to **3%/1%/0%**
at ten required checks — but *"**below the baseline of 10%/5%/1%**"*, i.e. **it over-corrects into
false negatives**. *"Only rarely can a hypothesis survive every reasonable robustness check."* He
invokes Harvey's **"reverse p-hacking"**: the potential to find specifications that contradict any
hypothesis if one tries hard enough. Coqueret says the same: *"higher decision hurdles also come at
the cost of more false negatives, which may or may not matter, especially for investment purposes."*

---

## 7. HOW THE LITERATURE JOINS CONSTRUCTION DISPERSION TO MULTIPLE TESTING

**They are related but not identical, and every paper in this corpus says so explicitly.** The
relation is a *count*: a construction grid multiplies the number of hypotheses actually tested, so the
critical value must rise — but the paths are heavily correlated, so the naive Bonferroni count is
wrong in the other direction.

| source | how the grid enters the threshold | resulting critical \|*t*\| |
|---|---|---|
| Harvey, Liu & Zhu (2016), as quoted by three of my sources | multiple testing across the factor zoo | **3.0** |
| **Menkveld et al. (2024)** `[read in full]` | Bonferroni over 164 teams assumes independence; their **bootstrapped multiverse** measures the actual correlation and finds *"adjustment factors that range between 13 and 91"* | **≥ 2.9** — *"in line with the 3.0 lower bound recommended by Harvey, Liu, and Zhu"* |
| **Soebhag et al.** `[read in full]` | Bonferroni over 2,048 constructions of one factor | **4.25** — and `HML`, which rejects in 78% of constructions under classical testing, rejects in **16%** |
| **Soebhag et al.** | Bonferroni over 11 factors × 2,048 = **22,528** hypotheses | **4.78** — `UMD` now rejects in **6%** of cases |
| **Coqueret** `[read in full]` | replaces bootstrap resampling with forking paths (*"exhaustive multiple testing"*), because paths produce heavier-tailed maximum statistics than bootstraps | bootstrap **4.5**; **paths ≥ 8.2**, *"a level that few anomalies are able to pass"* |
| **Jensen, Kelly & Pedersen** `[read in full]` | Benjamini–Yekutieli, then a Bayesian joint model | replication rate 82.4% → **75.6%** → back to 82.4% |

**Three things to take from this.**

1. **The distinction the field draws.** Menkveld et al.: *"Our objective is to study dispersion in
   estimates, short of a potential bias due to p-hacking. **By design, there is no need to p-hack for
   #fincap researchers**, because anyone who completed all stages of the project had been guaranteed
   coauthorship."* Construction dispersion is the *width* of the achievable distribution;
   *t*-hacking is *selection from within it*. **The first exists whether or not anyone is selecting.**
   Soebhag et al. put the join plainly: the degrees of freedom *"allow for p-hacking if the choices
   affect outcomes."*
2. **The construction grid IS the test count**, and it is the larger of the two multipliers: Soebhag
   et al.'s 2,048 constructions of one factor push the hurdle from 1.96 to 4.25 *before* any
   cross-factor correction.
3. **THE NULL'S THRESHOLD IS ITSELF CONSTRUCTION-DEPENDENT, BY A FACTOR OF 1.8.** Coqueret's
   bootstrap-versus-paths result — **4.5 versus ≥8.2** — is a measurement of exactly that. This is the
   finding in this section with the most direct bearing on this programme's machinery, and §8.2
   develops it.

---

## 8. GOING PAST THE SUB-QUESTIONS — FIVE THINGS THE BRIEF DID NOT ASK, AND I AM SAYING SO

The brief asked me to exhaust the sub-questions and then go past them. §§1–7 are the sub-questions.
These five are not commissioned.

### 8.1 The dispersion that is not a researcher choice at all: DATA VINTAGE

Every paper above varies *what the researcher does*. Two papers vary *when the researcher downloaded*,
holding the code and the sample period fixed. **This is the dimension a pre-registration cannot
close.**

- **Akey, Robertson & Simutin, "Noisy Factors"** (October 2021 working paper; *Review of Finance*
  advance article). `[WORKING PAPER]` **`[abstract and introduction read in full]`**, Wharton-hosted
  PDF; the published *Review of Finance* version was **not** opened. Holding the sample period
  constant and varying **only the vintage of the Fama-French factors**: *"unconditional alphas of **a
  third of long-short 'anomaly' portfolios lose statistical significance**. … annual alphas of
  **almost half of individual funds** and even portfolios of funds change by more than 1%. … F-
  statistics from GRS tests of the three-factor model on standard test portfolios **vary by up to
  40%** due only to changes in factor vintages. Our results do not suggest that any particular factor
  vintage is dominant but point to a source of **latent noise that is ignored in conventional
  tests**."*
- **Schwarz, Walter & Weiss, "Rewriting CRSP's History"**, *JFQA* (accepted; version dated 2026-02-24).
  `[PEER-REVIEWED]` **`[abstract and introduction read in full]`**. *"In January 2025, CRSP
  discontinued the existing stock tape used in many published papers. **This transition rewrites 9.62%
  of monthly returns by more than 1 basis point, primarily due to a change in the dividend
  reinvestment assumption.** … on average, **11.43% of all monthly long-short returns differ by more
  than 10 basis points** — especially in early periods, NBER recessions, and return-based sorts.
  Reassuringly, average premia and their significance remain largely unaffected."* The mechanism,
  quoted by them from CRSP: the legacy tape computed *"a month-to-month holding period return with
  dividends reinvested at month-end"*; the new tape computes *"a compound daily return with dividends
  reinvested on their ex-dates."*

> **Two things this means here.** (i) **A dividend-reinvestment timing convention buried inside a
> return series rewrote a tenth of CRSP's monthly returns.** The programme already records that its own
> fixtures *"disagree on corporate-action basis — 15m is fully adjusted, daily is not"*; that is the
> same hazard class, and the literature says it is worth 9.62% of observations. For a book whose edge
> is **overnight**, where the dividend lands relative to the session boundary is a construction choice
> with the same standing as the session boundary itself. (ii) **My own §5 numbers carry a vintage
> stamp — `202607` — and Akey et al. say a third of long-short alphas would change significance on
> that axis alone.** I report it rather than hide it.

**These two sources also CONFLICT, and I am not adjudicating it** — see §9.

### 8.2 Nobody reports the non-standard error OF A NULL DISTRIBUTION

Every paper measures the dispersion of the **score**. I found exactly one measurement of the dispersion
of the **threshold**: Coqueret's bootstrap-4.5 versus paths-8.2, a **1.8× move in the critical value**
caused by changing how the null is generated rather than what is scored. No source in this corpus
reports, for a fixed hypothesis, the **spread of a null's p50 and p95 across reasonable constructions
of the null itself**.

**That is a live gap, and it is this programme's gap specifically.** `CLAUDE.md` requires p50 and p95
beside every score, carries the p95's bootstrap SE, enumerates a rotation group where it is finite,
and records a margin within 2 SE as UNRESOLVED. **All of that prices sampling error in the null and
none of it prices construction error in the null.** The memory note *"Time rotation, not name
rotation — carry both nulls and say which OBJECT is rotated on which mask"* is already an admission
that the null has construction nodes; `C2`'s finding is that **the literature has never put a number on
how far apart two defensible nulls land**, and that the one available number is **1.8×**.

### 8.3 The NSE literature measures SPREADS, not long legs — so its numbers are not the programme's

Walter, Weber & Weiss's object is the *"return differential"*; their Internet Appendix contains **zero
occurrences** of "long leg", "short leg" or "long-only" `[MEASURED IN BRIEF — text census of the
three Internet Appendix PDFs in the authors' repository]`. Soebhag et al. measure factor Sharpe ratios.
Hasler measures `HML`. Mitton measures regression coefficients. **Every quantified NSE in §2 is the NSE
of a long–short spread.**

**And §5.2 found that the spread and the cash-funded long leg give opposite verdicts in both windows —
1-of-6 and 0-of-6 significant versus 6-of-6 and 6-of-6.** So the published NSEs describe an object
this programme does not hold. **The construction-dispersion literature has the same blind spot `C3` is
expected to find in the drawdown literature, and for the same reason: the field's unit of analysis is
the spread.**

### 8.4 Published NSE grids omit the two nodes round 2 actually tripped over

Walter, Weber & Weiss's fourteen nodes are all **sample-selection and portfolio-formation** choices.
**The benchmark is not a node** — it is a separate table, run after the grid. **The accounting
variable's definition is not a node either** — the deflator lives inside the sorting variable and each
variable is a separate row. Soebhag et al.'s eleven are the same shape.

> **Therefore every published NSE in §2 is a LOWER BOUND on the dispersion round 2 encountered.** The
> 0.19%/month is the dispersion *holding the benchmark and the variable definition fixed*. Round 2's
> three discoveries were a benchmark (outside the grid), a deflator (outside the grid) and a session
> boundary (outside the grid). **The one construction family that has been exhaustively enumerated is
> the one that did not bite, and the families that bit have not been enumerated.**

### 8.5 When the analyst is an agent, the dispersion does not go to zero

This programme's construction choices are made and executed by an agent. I found one paper on what
that does.

**Cui & Alexander, "Same Prompt, Different Outcomes: Evaluating the Reproducibility of Data Analysis by
LLMs"**, arXiv 2602.14349v1, 15 February 2026. `[WORKING PAPER]` **`[abstract and significance
statement read in full]`**; the body was not read. *"We evaluate two prompting strategies, six models,
and four temperature settings, with ten independent executions per configuration, yielding **480 total
attempts**. … we find considerable variation in the analytical results **even for consistent
configurations**. … **Even at temperature zero some estimates lead to different conclusions about the
same research question.** These findings show that a single LLM-generated data analysis is insufficient
and that repeated independent executions should be standard practice."*

> **The remedy they reach is the same one Hasler and Coqueret reach for human analysts — run it many
> times and look at the distribution — and it arrives at this programme from a direction nobody
> commissioned.** `CLAUDE.md` already requires `assert_matches_scorer` once per study and bit-identity
> proofs on shards, because an agent's two implementations of the same thing diverge. **This is the
> same failure mode one level up: the agent's two *constructions* of the same study also diverge, and
> no assertion catches that, because both are correct.**

### 8.6 One adjacent hazard, recorded because it names a look-ahead inside a construction choice

**Dickerson, Robotti & Rossetti, "The Corporate Bond Factor Replication Crisis"**, arXiv 2604.07880,
April 2026. `[WORKING PAPER]` **`[abstract only]`** — a different asset class, outside this programme's
scope, and recorded for one sentence: the crisis stems from *"transaction prices whose measurement
error enters both sorting signals and return denominators, creating a correlated errors-in-variables
bias, and **asymmetric ex-post return filtering that embeds future information into factor
construction**."* **A data-cleaning filter that is applied asymmetrically is a look-ahead dressed as a
construction choice** — and this programme has already paid for one look-ahead (D391, 82% of a result).
The generalisable warning: *any filter whose threshold is evaluated on the outcome rather than the
signal is a look-ahead, however innocuous it reads.*

---

## 9. CONFLICTS, RECORDED AND NOT ADJUDICATED

1. **Does data vintage change conclusions, or only add noise?** Akey, Robertson & Simutin:
   *"unconditional alphas of a third of long-short 'anomaly' portfolios lose statistical
   significance."* Schwarz, Walter & Weiss: *"Reassuringly, average premia and their significance
   remain largely unaffected, suggesting CRSP changes mainly introduce unsystematic variation without
   altering key asset pricing conclusions."* **Both read in full (abstract and introduction).** They
   vary **different objects** — Akey et al. vary the *factor vintage*, i.e. the benchmark; Schwarz et
   al. vary the *underlying return data* — which may be the whole explanation, and may not. **I would
   weight Akey et al. for this programme**, because the object they vary (the benchmark) is the one
   §2.2 and §5.3 show is most load-bearing; but I would not discard Schwarz et al., whose object is
   closer to the programme's raw bars.
2. **Does equal-weighting raise or lower the premium?** Soebhag et al. measure equal-weighting raising
   the average maximum Sharpe ratio from 0.57 to 0.71 across 11 factors, and Walter, Weber & Weiss
   measure an equal-weighted mean premium of 0.30 against 0.26 value-weighted across 68 variables.
   **`[MEASURED IN BRIEF]` my §5.2 found the opposite for operating profitability** — the EW
   full-sample tercile spread is +0.079 against VW's +0.224, and the *t* falls from 2.37 to 0.74.
   **The sign of the weighting effect is variable-specific.** A cross-factor average does not tell you
   what it does to *your* variable.
3. **"Sign is remarkably stable" versus the tables.** Walter, Weber & Weiss's abstract: *"Irrespective
   of choices in portfolio sorts, we find pervasively positive premiums and alphas for almost all
   sorting variables. This suggests that while the size of these premiums is uncertain, their sign is
   remarkably stable."* Their own `All` row: `Pos. = 0.90` — **one specification in ten is negative** —
   `Sig. = 0.50`, and `Pos.` is **0.23** for `BL`, **0.30** for `TBI`, **0.68** for the
   originally-insignificant group. **Both are theirs. A prose-versus-tables tension, recorded not
   resolved; I weight the tables.** My own §5.2 agrees with the prose on one variable (0 sign flips in
   24 cells) and §5.3 contradicts it the moment the benchmark moves.
4. **Menkveld et al.'s introduction and table versus their own conclusion.** Introduction and Table I:
   RT-H1's median estimate is **−1.1%**. Conclusion: *"A more opaque RT hypothesis on market
   efficiency yields larger variation with an NSE of 6.7% around a median of **1.1%**."* **A sign
   discrepancy inside a paper about dispersion, between its own conclusion and its own table.** I
   weight the table (it agrees with the introduction, and with the quartiles around it), and I am not
   resolving it.
5. **The replication crisis itself.** Hou, Xue & Zhang: 65% of 452 anomalies fail |*t*| > 1.96 under
   NYSE breakpoints and value-weighting, 82% at *t* > 2.78, 18% replicate after their own multiple-
   testing adjustment. Jensen, Kelly & Pedersen: 82.4%. **Both positions reduce to a benchmark choice
   and a weighting choice.** Interested parties on **both** sides — §10. **I would weight neither as
   "the answer"; the ladder in §2.6 is the finding.** `[HXZ NOT OPENED — §12.]`

---

## 10. INTERESTED PARTIES, ON BOTH SIDES

- **Jensen, Kelly & Pedersen (no crisis).** From the paper's own footnote: Bryan Kelly is at Yale,
  **AQR Capital Management** and NBER; Lasse Heje Pedersen is at **AQR Capital Management**; *"AQR
  Capital Management is a global investment manage[ment firm]"* and *"A conflict of interest disclosure
  statement can be found on The Journal of Finance website."* **AQR sells factor products. A finding
  that most factors replicate supports that business.** Their paper also argues for the two
  construction choices that raise the replication rate (CAPM alpha; capped value-weighting with
  microcaps excluded rather than straight value-weighting).
- **Hou, Xue & Zhang (crisis).** `[NOT OPENED]`, so stated from the public record rather than the
  paper: Lu Zhang is an author of the **q-factor model** and the maintainer of `global-q.org`, which
  distributes it. **A finding that most competing anomalies fail while a small set survives is not
  neutral to the author of the surviving model.**
- **Soebhag & van Vliet** are at **Robeco Quantitative Investing** (stated on the paper's title page
  alongside Erasmus School of Economics). **Robeco sells quantitative factor products.** Their
  recommendation — converge on NYSE breakpoints, exclude microcaps, value-weight — is also the
  construction a large institutional manager can actually trade. That does not make it wrong; it
  makes it interested, and it is the construction whose adoption would cost this programme its
  universe.
- **Menkveld et al.** — the project coordinators state *"The project coordinators have read The Journal
  of Finance's disclosure policy and have no conflicts of interest to disclose."* One coordinator is at
  **Optiver Amsterdam** (a proprietary trading firm) and the author list includes staff of the **Bank
  of England**, the **Federal Reserve Bank of New York** and the **IMF**, with a disclaimer that the
  views are not those of those institutions. **The data were supplied by Deutsche Börse**, whose
  market's efficiency and spreads were the object of study.
- **Against my own reading.** I came to this lane primed by round 2 to find that construction choices
  dominate, and I found it. The honest counterweight is §5.2's zero sign flips in 24 cells, WWS's
  `Pos. = 0.90`, Menkveld's explicit *"upper bound"* caveat, Schwarz et al.'s *"largely unaffected"*,
  and Hasler's pre-sample result at odds with his own thesis. **All four are in this brief because they
  point the other way.**

---

## 11. WHAT I COULD NOT VERIFY, STATED PLAINLY

1. **Which version of Walter, Weber & Weiss the repository's tables belong to.** The `.tex` outputs are
   not version-stamped. The 2022 WU-repository abstract says **40 sorting variables** and **NSE 0.05%
   to 0.26%**; the repository's Internet Appendices say **68 sorting variables**; the `All` row's NSE
   of **0.19** matches an independently sourced 2024 figure. **I read the tables in full and can vouch
   for what they say; I cannot say which draft they correspond to, and the SV count changed between
   versions.** Every WWS number above should be read as "the version whose output is in the public
   repository as of 2026-09-10".
2. **The meaning of four columns in their `IA05_NSE_across_models` table** (`R-C`, `C-F`, `C-Q`, `F-Q`,
   values 92 to 1,504). Plausibly counts of specifications whose verdict changes between model pairs,
   plausibly a scaled distance. **I did not find the caption and I am not guessing.** Only the `Raw`,
   `CAPM`, `FF5`, `Q5` columns are quoted in §2.2.
3. **Whether Soebhag et al.'s published *Journal of Empirical Finance* version differs from the 2022
   FoFI draft I read.** Paywalled (§13). Given that the Menkveld and WWS versions both changed
   materially, **assume it may have.**
4. **Hou, Xue & Zhang's own figures.** The 35% replication rate and the 18% multiple-testing figure
   come from Jensen, Kelly & Pedersen, read in full. The 65% / 96% / 82% figures come from **a search
   summariser** and are therefore **weaker than `[snippet only]`**. I did not open HXZ.
5. **Huntington-Klein et al.'s published version.** I verified every quoted sentence against the **IZA
   working paper (May 2020)**. The *Economic Inquiry* (2021) version was not opened, and the
   possibility of a change between them is exactly the hazard this brief carries.
6. **Akey, Robertson & Simutin's published *Review of Finance* version.** I read the 2021 working
   paper's abstract and introduction. The advance article was not opened; the "a third" and "40%"
   figures are the working paper's.
7. **My own *t*-statistics are iid**, not Newey-West or clustered. Monthly portfolio returns have mild
   autocorrelation; the *t*-values in §5 are therefore slightly optimistic in absolute value. The
   *relative* comparisons across cells — which is the whole point — are unaffected, because every cell
   uses the same estimator.
8. **My §5 grid rests on one CRSP vintage (`202607`)** and §8.1 says a third of long-short alphas can
   change significance on that axis. **I have not re-run it on a second vintage and cannot.**
9. **Whether the published NSEs transfer to a daily-bar, overnight-holding, `$5`-floored,
   equal-weighted US single-name panel of ~1,573 names with ~10 effective instruments.** Every NSE
   above is monthly, long–short, and on a universe chosen by the authors. **No source measures
   anything resembling this programme's object**, and §8.3 and §8.4 say the gap is structural, not
   incidental.
10. **Menkveld et al.'s Table I, Panel C.** The layout-preserving text extraction scrambled it; I
    re-extracted with a second library and validated against the paper's own prose (RT-H1 median
    −1.1%, IQR 6.7, IDR 27.3, median SE 2.5%, RT-H3 IQR 1.2 median −3.3 — all five match). **The
    *t*-statistic panel has no prose cross-check**, so it rests on the second extraction alone.

---

## 12. WHAT I DID NOT OPEN

Separate from §11, and deliberately complete.

1. **Hou, Xue & Zhang (2020), "Replicating Anomalies", *RFS***. The single most-cited construction
   result in the field. Open PDFs were located at `global-q.org` and `theinvestmentcapm.com`; **I chose
   depth on the measurement papers instead.** Its figures above are second-hand.
2. **Walter, Weber & Weiss's actual paper text.** I read its output tables and Internet Appendix; I
   never read its prose, its method section, or its proposed two-step protocol beyond a summariser's
   description (which I therefore did not quote). The SSRN delivery endpoint is blocked (§13).
3. **Soebhag et al.'s published JEF version** (paywalled), and their **Appendix C** net-return
   analyses, which exist in the draft I have and which I read only the summary of.
4. **Jensen, Kelly & Pedersen's Internet Appendix Section I**, which *"detail[s] how each change
   affects the replication rate"* — i.e. the per-node decomposition of the 35% → 55.6% rung. **This is
   the single most valuable unopened document in this lane.** It is on Wiley; their public repository
   (`bkelly-lab/ReplicationCrisis`, 31 entries) does not carry it.
5. **Menkveld et al.'s original version**, Tinbergen Institute Discussion Paper **TI 2021-102/IV**. I
   read the published Appendix B's reconciliation of it (§14) but not the discussion paper itself.
6. **Menkveld et al.'s Internet Appendix**, including Table V's full fork list (the layout extraction
   truncated it to four rows) and Figure 6's per-fork refraction ranking.
7. **Chen & Zimmermann's open-source replication work** and the Open Source Asset Pricing library. The
   "reproduce nearly 100%" figure is JKP's characterisation of it, not theirs.
8. **Chen, "Do *t*-Statistic Hurdles Need to be Raised?"** (arXiv 2204.10275) — the counter-camp on
   hurdle inflation, located and not opened.
9. **Akey, Robertson & Simutin's body and their "suggestions to empiricists on dealing with the
   noise"** — the remedy section of the vintage paper.
10. **Schwarz, Walter & Weiss's 46-page Internet Appendix** and their body, including which sorting
    families were most affected by the tape change.
11. **Steegen et al. (2016)**, the original multiverse paper; **Patel, Burford & Ioannidis's "vibration
    of effects"**; **Gould et al. (2023)** and **Huber et al. (2023)**, the two multi-analyst studies
    Coqueret names that Menkveld does not; **Botvinik-Nezer et al. (2020)** (70 teams, fMRI), cited by
    Menkveld and not opened.
12. **Bessembinder, Cooper & Zhang** on return horizon and compounding — located via Coqueret's
    citation, not opened. Relevant to §3.4 item 7.
13. **Ince & Porter** on international data screening; **Mitton's companion paper on economic
    significance** (`Mitton-2022b`); **"Empirical Asset Pricing with Large Language Model Agents"**
    (arXiv 2409.17266); **"Look-Ahead-Bench"** (arXiv 2601.13770) — all located, none opened.
14. **Del Giudice & Gangestad's simulated worked example**, and Simonsohn et al.'s hurricanes
    application (1,728 specifications) beyond the passages quoted.
15. **The *published* Economic Inquiry, Review of Finance and JEF versions** of three papers I read in
    working-paper form.

---

## 13. BLOCKS, BY TOOL AND RESPONSE

Per the standing rule: **the tool and the response, never the host.**

1. **`curl` → `https://papers.ssrn.com/sol3/Delivery.cfm/4164117.pdf?abstractid=4164117&mirid=1`**
   → **HTTP 403**, `text/html; charset=UTF-8`, **5,711 bytes**, body begins
   `<!DOCTYPE html><html lang="en-US"><head><title>Just a moment...</title>` with
   `<meta name="robots" content="noindex,nofollow">` — a Cloudflare interstitial, not a rejection of the
   request. **Workaround that succeeded:** the authors' own public reference implementation, whose
   `Paper_Tables/*.tex` and `Internet Appendix/*.pdf` are the paper's actual output. **The numbers in
   §2.2 come from the code that produced them.**
2. **`curl` → `https://www.liuyanecon.com/wp-content/uploads/Mitton-2022a.pdf`** → **HTTP 000**, 0
   bytes, `curl: (35) schannel: next InitializeSecurityContext failed: CRYPT_E_REVOCATION_OFFLINE
   (0x80092013) - The revocation function was unable to check revocation because the revocation server
   was offline.` **A local TLS revocation-check failure, not a block.** Retried with
   `--ssl-no-revoke`: **HTTP 200, `application/pdf`, 539,062 bytes, 49 pages** — the publisher's
   typeset *RFS* version. Every subsequent fetch used that flag.
3. **`WebFetch` → `https://www.tidy-finance.org/blog/nse-portfolio-sorts/`** → returned *"only a
   redirect notice"*. Followed to `https://blog.tidy-finance.org/posts/nse-portfolio-sorts/`, which
   returned the 14-node decision table. **That table is the authors' own blog, not the paper**, so the
   node list in §1.2 was confirmed independently against their repository's
   `17_Decision_Nodes.R`-adjacent table files before use.
4. **`WebFetch` → a Semantic Scholar paper page for Del Giudice & Gangestad** → *"I don't see any web
   page content provided"* — an empty body at the tool layer. **Workaround:** the author's own hosted
   PDF, HTTP 200, `application/pdf`, 3,521,106 bytes.
5. **Elsevier ScienceDirect (Soebhag et al.'s published JEF version) and Wiley Online Library (JKP's
   Internet Appendix, Huntington-Klein's published version)** were **not attempted** — both require
   institutional authentication, which this lane does not have and would not use.

**Two integrity notes on sources.** (i) Every PDF's **title line was read before any number was taken
from it** — the hazard being a well-formed PDF of a different paper at a guessed identifier. One near
miss: the Silberzahn PDF's first page is the **Corrigendum**, and the abstract I quoted is on a later
page of the same file. (ii) Several figures in this brief were first seen in a **search summariser**;
in every case they were then either confirmed from the document (Mitton's 70%, Huntington-Klein's
3–4×, Silberzahn's 0.89–2.93, Hasler's 0.08) or are flagged as summariser-sourced and therefore weaker
than `[snippet only]` (Hou, Xue & Zhang's 65% / 96% / 82%). **One summariser account did not survive
contact with the documents:** its characterisation of the criticisms of specification-curve analysis
was discarded wholesale and replaced by Del Giudice & Gangestad's own words, which are both sharper and
quantified. **And one summariser figure was imprecise in a way worth naming:** Mitton's *"over 70%"* is
his own **abstract's** rounding; his body text gives **73%** at the 5% level, alongside 94% at the 10%
and 23% at the 1% level, which the summariser did not carry.

---

## 14. THE DRAFT-VERSUS-PUBLISHED HAZARD, WHICH IN THIS LANE IS ITSELF EVIDENCE

The brief said this hazard was unusually relevant here because *"a paper that changed between versions
is itself a datum about construction dispersion."* It is, three times over.

1. **Menkveld et al. documents its own case, in an appendix, with a joke.** *"The tables that have
   changed are Tables 3 and 4 in the original version. … In the original version, we estimate a
   heteroskedasticity model using OLS. … Quantile regressions are robust to the presence of extreme
   outliers."* And the magnitudes: in the working paper the quality result was **insignificant except
   on a 2.5%–97.5% winsorized sample**, and the peer-feedback effect was **a 9% decline in the SD on
   the unwinsorized sample and a 53.5% decline on the winsorized one**; the published version reports
   **47.2%**. Their footnote 35: *"We have changed the statistical methodology guided by the feedback
   of The Journal of Finance referees. **One could say that this 'peer feedback' likely reduced the NSE
   of our results.**"*

> **A 9%-versus-53.5% swing on one winsorization choice, inside the paper that invented the term for
> this problem, on the very estimate that is the paper's answer.** That is Mitton's #2 node
> (|Δ*t*| = 3.74) biting the authors of the field's founding paper. **It is the strongest single
> argument in this brief for §3.4 item 1.**

2. **Walter, Weber & Weiss changed title, scope and sample between versions**: "Non-Standard Errors in
   Portfolio Sorts" (July 2022, **40** sorting variables, NSE **0.05%–0.26%**) → "Methodological
   Uncertainty in Portfolio Sorts" (October 2024, headline NSE **0.19%**), with **68** sorting
   variables in the repository's Internet Appendices and **three** dated Internet Appendix PDFs in one
   folder. **Recorded, not resolved** (§11.1).
3. **Huntington-Klein et al.** exists as IZA DP 13233 (May 2020) and as *Economic Inquiry* 59(3)
   (2021). I read the former. **Every sentence I quote is the working paper's.**

---

## 15. WHAT THIS LANE LEAVES FOR THE PRINCIPAL TO DECIDE

Nothing below is a recommendation to act; `R15` forbids that and this lane has measured nothing on the
fixture.

1. **The one cheap instrument.** A construction-node register — the nodes this programme has already
   fixed, each with its branch and a one-line Type E / N / U triage — would make Coqueret's exponent
   visible and is the only remedy in §6 with no published objection. **Fourteen of its rows already
   exist**, ranked, in §3.1.
2. **The three nodes the programme has fixed silently and the literature ranks high.** Quantile/slot
   count (rank 1), weighting (rank 2), outlier handling (Mitton rank 2). **Two are written into
   `CLAUDE.md` as reporting conventions rather than construction choices.**
3. **The question §8.2 opens.** The programme prices sampling error in its nulls to 2 SE and enumerates
   finite rotation groups exactly. It does not price construction error in its nulls, and the only
   published number for that is **1.8× on the critical value**.
4. **The §5.3 result is the one to argue about.** If a cash-funded equal-weighted long leg can be
   *t* = +2.46 against cash and *t* = −2.00 against the CAPM over the same 198 months, then the
   programme's choice to compete with cash is not a presentational convenience — **it is the load-
   bearing construction choice in the whole book, and it has never been written down as one.**

---

**Lane `C2` complete.** Sources: **16 distinct works obtained and read locally** (18 PDFs and 11
result-table files on disk), of which **11 read in full** (Menkveld JF 2024 · Soebhag FoFI 2022 · Mitton RFS 2022 · Coqueret arXiv 2023 · Hasler CFR 2023
· Jensen-Kelly-Pedersen JF 2023 · Silberzahn AMPPS 2018 · Breznau PNAS 2022 · Huntington-Klein IZA 2020
· Simonsohn NHB 2020 · Del Giudice & Gangestad AMPPS 2021), **3 read in full as the authors' own output
tables and appendices** (Walter-Weber-Weiss: 11 result tables and 3 Internet Appendices), **2 read in
abstract and introduction** (Akey "Noisy Factors" · Schwarz "Rewriting CRSP's History"), **2 read in
abstract** (Cui & Alexander · Dickerson et al.). **Two independent measurements with five negative
controls**, scripts and outputs in `data/C2_*`. **Nothing closed, nothing admitted, nothing elevated.**
