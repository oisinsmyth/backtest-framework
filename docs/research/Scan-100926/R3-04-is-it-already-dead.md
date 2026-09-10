# `C4` — IS IT ALREADY DEAD? POST-PUBLICATION DECAY FOR THE ONE FAMILY THIS PROGRAMME CAN COMPUTE

**Round 3, lane `C4`.** Campaign contract: [`00-SCHEMA.md`](00-SCHEMA.md). Slate:
[`R3-00-slate.md`](R3-00-slate.md). Round 2: [`R2-99-record.md`](R2-99-record.md), and the lane this
one serves is [`R2-02`](R2-02-profitability-deep.md).

**EXTERNAL LITERATURE AND PUBLIC-DATA ONLY.** I have no access to the programme's fixture and claim
nothing about it. Every number I measured is on Chen–Zimmermann's published portfolio files, Ken
French's published portfolio files, or SEC-filed fund reports — all named, all re-runnable.

Under [R15](../../RULES.md#r15) **nothing here closes or admits anything**, nothing is elevated into
`FINDINGS.md`, `RULES.md`, the books or a decision record. Both books are unchanged.

---

## 0. THE ANSWER, STATED FIRST AND STATED AGAINST MY OWN EXPECTATION

**IT IS NOT DEAD. IT NEVER DECAYED. AND THE THREE REASONS THAT IS LESS GOOD NEWS THAN IT SOUNDS ARE
ALL IN THIS BRIEF.**

1. **Gross profitability's post-publication long–short return is THREE TIMES its in-sample return, and
   it sits at the 99th percentile of the decay distribution of 200 published predictors.**
   `[MEASURED IN BRIEF]` on Chen–Zimmermann's own files, original-paper construction (VW quintiles,
   annual rebalance): in-sample 1963-07→2010-12 **0.303 %/mo, `t` 2.39**; post-publication
   2014-01→2024-12 **1.024 %/mo, `t` 2.65**. My in-sample figure reproduces Novy-Marx's own published
   **0.31, `t` 2.49** — which I verified in *both* his June-2012 working paper and `R2-02`'s read of
   the published JFE article. The same pipeline puts the **median** post-publication/in-sample ratio
   across 200 CZ predictors at **0.42**, independently reproducing McLean & Pontiff's published **58%
   decline**. Gross profitability's ratio is **3.01**. §3.1, §8.

2. **BUT TWO-THIRDS OF THAT WIDENING IS IN THE LEG THIS PROGRAMME CANNOT TRADE.** Benchmarking each
   leg against the **sort's own universe** (not the VW market — see point 6), gross profitability's
   **long** leg went from **+0.239 %/mo [`t` 4.71]** in-sample to **+0.405 [`t` 3.00]**
   post-publication, equal-weighted. Its **short** leg went from **−0.281** to **−0.567**. Against
   the VW market the long leg barely moved at all (**+0.187 → +0.179 %/mo, `t` 1.25**) while the short
   leg fell from **−0.110 to −0.746 [`t` −3.52]**. **Borrow is excluded ground for this programme, so
   the half of the result that grew is the half it cannot have.** §3.2.

3. **AND NOT ONE OF THE FIVE DECAY PAPERS I READ IN FULL REPORTS THE LONG LEG'S DECAY SEPARATELY FROM
   THE SPREAD — I CHECKED, BY GREP, ON ALL FIVE.** McLean & Pontiff and Jacobs & Müller use the legs
   only for *short interest* and *cross-country correlation*; the decay estimates themselves are
   long–short throughout, as are Chen & Velikov's, Chen & Zimmermann's and Falck–Rej–Thesmar's. **The
   entire post-publication decay literature therefore says nothing directly about a long-only book,
   and the 4 bp/month figure round 1 carried is a long–short, net-of-spread, post-publication AND
   post-2005 average across 204 anomalies.** §7.1, §2.3.

4. **THE EVIDENCE CANNOT SEPARATE DECAY FROM ERA-DEPENDENCE, AND TWO PUBLISHED SOURCES SAY SO IN
   THEIR OWN WORDS.** Jacobs & Müller's own abstract calls the US post-publication decline *"partly
   explained by a general time trend"*, and their §3.3 finds a linear time trend or month fixed
   effects *"subsume a substantial fraction of the explanatory power of the U.S. post-publication
   dummies."* Chen & Velikov stack the two deliberately — their headline number is *"post-publication
   and post-2005"* — and state that *"a large chunk of the post-publication profitability found by MP
   and others likely comes from observations that pre-date the modern era of information
   technology."* **My own negative control settles it for this era:** over **2013-07→2026-07** Ken
   French's **HML is −0.043 [`t` −0.15], SMB −0.151 [`t` −0.66], CMA −0.075 [`t` −0.41]** — three
   factors whose publication dates span 1981 to 2015, all dead in the same window. **A decline dated
   2013 cannot be HML's publication effect.** §4.

5. **THE LIVE FUNDS — THE ONE THING NOBODY CAN HAVE p-HACKED — SAY THE OPPOSITE OF MY MEASUREMENT IN
   LARGE CAPS.** From **SEC-filed annual shareholder reports [PRIMARY DATA DOC]**, not factsheets:
   over ten years **QUAL returned 12.75 %/yr at NAV against MSCI USA's 13.62 %** (−87 bp/yr) and
   **SPHQ 14.44 % against the S&P 500's 15.26 %** (−82 bp/yr) — and the *indexes* lost 68 and 60
   bp/yr, so it is not a fee story. Dimensional's own **DUHP**, the purest commercial
   high-profitability tilt, has returned **14.03 %/yr since Feb 2022 against the Russell 1000's
   15.27 %** (−124 bp/yr), and its filed management discussion states flatly that *"High profitability
   stocks underperformed low profitability stocks within large cap stocks"* for the year to Oct 2025.
   Only the **mid** and **small** cap tilts are positive, and thinly: **XMHQ +97 bp/yr over 5 years**,
   **XSHQ +25 bp/yr since 2017**. §5.

6. **A METHOD FINDING THAT OUTRANKS ALL OF THE ABOVE, AND IT CAUGHT ME MID-BRIEF.** I first measured
   the equal-weighted long leg against the **CRSP VW market** and got **−0.125 %/mo [`t` −0.49]**
   post-publication for gross profitability — *"the equal-weighted long-only tilt has decayed to
   zero."* That was **false**: it was measuring the death of SMB, not of profitability. Re-benchmarked
   to the sort's own equal-weighted universe the same months give **+0.405 [`t` 3.00]**. **The
   benchmark choice flips the sign of this lane's central answer, on the same data, in the same
   window** — which is `R2-01`'s finding and `C2`'s premise arriving uninvited in a third lane. §3.2,
   §7.2.

7. **THE DEFLATOR IS WORTH ABOUT 15 bp/MONTH OF LONG-LEG ALPHA AND THAT INCREMENT HAS NOT DECAYED
   EITHER.** `R2-02` could not take its deflator finding past 2014. I can: CZ ship
   **`GPlag` = (sale − cogs) / AT₋₁** as a **`Placebo`** in their own taxonomy, and I established
   empirically that the placebo portfolios are **equal-weighted** (their universe mean return
   correlates **0.9946** with the EW universe and **0.8662** with the VW one). Paired, same months,
   long-leg-minus-own-universe: **GP − GPlag = +0.194 %/mo [`t` 4.98]** in-sample and **+0.149
   [`t` 1.83]** post-publication. **Under the lagged deflator the long leg is +0.045 [`t` 0.80]
   in-sample and +0.256 [`t` 2.23] post-publication** — so the deflator's destructive effect is an
   *in-sample* phenomenon and post-2013 both conventions are positive. §3.3.

8. **SUB-QUESTION 5 SPLITS THE ANSWER BY DEFINITION, AND THE SPLIT IS THE LANE'S SECOND-BIGGEST
   FINDING.** On Chen–Zimmermann's gross profitability the EW-minus-VW long-leg alpha — the small-cap
   increment — is **+0.057 [`t` 0.83]** in-sample and **−0.068 [`t` −0.42]** post-publication: no
   measurable size increment and hence no measurable differential decay, at n=132. **But on Ken
   French's 25 Size × OP portfolios, through 2026-07, the profitability spread went to ZERO after
   2013 in every size quintile EXCEPT THE LARGEST** — VW `HiOP − LoOP` in the second and third size
   quintiles falls from **+0.378 [`t` 2.84]** and **+0.418 [`t` 2.87]** to **−0.004** and **−0.062**,
   while the largest quintile holds **+0.203 → +0.248**. **The decay is concentrated in exactly the
   small-to-mid segment this programme trades.** §6.4 shows the conflict resolves on the *definition*,
   not the dataset: French's OP is `R2-02`'s fourth definition (`/BE`, net of interest expense), and
   **CZ's data agrees with French about that definition** — `OperProf`'s long leg also decays, +0.141
   [`t` 2.58] → +0.113 [`t` 1.11]. **Two independent datasets say the Fama–French profitability
   construction is dead post-2013 in small and mid caps, and both say gross profitability is not.**
   And the founding decay paper's own cross-section says the *opposite* of both: McLean & Pontiff's
   Table 7 coefficient on **Size is −1.490 (SE 0.598, p = 0.013)** — decay *larger* in bigger stocks —
   **but its R² is 0.000 and size collapses to 0.047 (p = 0.965) under one control.** §6.

9. **THE PRE-PUBLICATION OUT-OF-SAMPLE TEST OF THIS EXACT FAMILY EXISTS AND IT SURVIVES.** Wahal
   (2019, JFE 131(2)) hand-collected Moody's Manuals for **1940–1963** — before the discovery sample
   begins — and reports, abstract verbatim: *"Controlling for value, the profitability premium emerges
   as important in this period. In contrast, there is no reliable relation between investment and
   returns… even after extending the data back to 1926."* **[abstract only, from the author's
   institutional repository; the author's own one-line summary on his own site reads "Even in the
   pre-Compustat period, the profitability premium is quite robust. Investment, not so much."]** **And
   that sets a trap for §3.3's deflator result:** `GP/AT ≡ (GP/AT₋₁) ÷ asset growth`, so the
   current-asset convention smuggles in the investment signal — **which Wahal finds absent before 1963
   and which my own §4.2 finds dead after 2013 (`CMA` −0.075 [`t` −0.41])**, and which is nonetheless
   the component worth +15 bp/month of long-leg alpha in my post-publication measurement. §6.5.

**The precise negative I would put above all of it:** this family has not decayed, but everything that
grew post-publication sits in the short leg, in the deflator convention, or in the benchmark; the one
construction for which two independent datasets agree there *has* been decay is dead precisely in
small and mid caps; and the only genuinely out-of-sample evidence at a long-only construction, the
filed fund records, is *negative* in large caps and worth 25–97 bp/yr in the segment where this
programme actually lives.

---

## 1. SOURCES — TYPE, AND SEPARATELY HOW WELL ESTABLISHED

| # | source | type | established |
|---|---|---|---|
| `D1` | **McLean & Pontiff**, *Does Academic Research Destroy Stock Return Predictability?*, **23 Oct 2012 draft**, 41 pp, `hec.ca/finance/Fichier/McLean.pdf` | [WORKING PAPER] — **interested: decay finding is theirs** | **[read in full]**, local `pypdf`, 82,057 chars |
| `D1b` | **The same paper's 16 May 2013 draft**, 48 pp, `fmg.ac.uk/.../Jeffrey-Pontiff.pdf` | [WORKING PAPER] | **[read in full]**, 96,558 chars; Tables 7, 8 and 9 transcribed by me; **compared line by line against `D1`** (§2.1) |
| `D1c` | **The published article**, *Journal of Finance* **71(1), 2016, pp. 5–32** — 97 variables, 26% / 58% | [PEER-REVIEWED] | **[NOT OPENED — abstract figures via search summariser and via `D2`'s verbatim restatement]**; the Wiley page returned HTTP 403 and SSRN a Cloudflare interstitial (§9) |
| `D2` | **Chen & Zimmermann**, *Publication Bias in Asset Pricing Research*, **arXiv 2209.13623, 22 Sep 2023**, 34 pp | [WORKING PAPER] — **interested: their dataset's value rests on anomalies being real** | **[read in full]**, local `pypdf`; §§2.2, 2.3, 4.2, 4.3 quoted verbatim |
| `D3` | **Chen & Velikov**, *Zeroing In on the Expected Returns of Anomalies*, **JFQA 58(3), May 2023, pp. 968–1004**, open access via Cambridge Core, 37 pp | [PEER-REVIEWED] | **[read in full]** — title line verified; **Table 2 transcribed in full by me**, §IV.A and Figure 6's slopes read verbatim. **This closes round 1's item 11, which was `[abstract only — NOT OPENED]`** |
| `D4` | **Jacobs & Müller**, *Anomalies across the globe: Once public, no longer existent?*; text read = the **January 2017 working paper**, 55 pp, `wp.lancs.ac.uk/fofi2018`; published **JFE 135(1), 2020, pp. 213–230** | [WORKING PAPER] for the text I read | **[read in full]** — abstract, §3.2, §3.3 ("Time effects"), Table 3 Panel B, Table 9's country rows and Table 10 read verbatim |
| `D5` | **Falck, Rej & Thesmar**, *Why and how systematic strategies decay*, **arXiv 2105.01380, 4 May 2021**, 45 pp; published *Quantitative Finance* 22(11) 2022 as *When Systematic Strategies Decay* | [WORKING PAPER] — **interested: authors at Capital Fund Management** | **[read in relevant part]** — abstract and §1 read verbatim; I did **not** read their regression tables |
| `D6` | **Novy-Marx & Medhat**, *Profitability Retrospective: What Have We Learned?*, **NBER w33601, March 2025**, 78 pp | [WORKING PAPER] — **interested on both counts, from the title page verbatim:** *"Robert Novy-Marx provides consulting services to Dimensional Fund Advisors LP. Mamdouh Medhat is a listed employee of Dimensional Investment LLC"* | **[read in relevant part]** — Table B3 transcribed by me; **the §B.3 prose describing Internet Appendix Table D1 read verbatim. THE TABLE ITSELF IS STILL NOT OBTAINED** (§10.2), exactly as in `R2-02` §10 |
| `D7` | **Novy-Marx**, *The Other Side of Value: The Gross Profitability Premium*, **June 2012 working paper**, 73 pp, `mysimon.rochester.edu/novy-marx/research/OSoV.pdf` | [WORKING PAPER] | **[read in relevant part]** — Table 2's discussion and footnote 3 read verbatim, **compared against the published figures `R2-02` read in full** (§3.4) |
| `P1` | **SEC `N-CSR` annual shareholder report, Invesco Exchange-Traded Fund Trust**, accession `0001193125-26-295502`, filed 2026-07-06, FY to 2026-04-30 (56,352,734 bytes) | **[PRIMARY DATA DOC]** | **[read in relevant part]** — the XMHQ and SPHQ shareholder-report sections extracted locally and transcribed |
| `P2` | **SEC `N-CSR`, Invesco Exchange-Traded Fund Trust II**, accession `0001193125-25-271078`, filed 2025-11-07, FY to 2025-08-31 (81,562,101 bytes) | **[PRIMARY DATA DOC]** | **[read in relevant part]** — the XSHQ section transcribed |
| `P3` | **SEC `N-CSR`, iShares Trust**, accession `0001100663-25-000020`, filed 2025-10-03, FY to 2025-07-31 (31,320,307 bytes) | **[PRIMARY DATA DOC]** | **[read in relevant part]** — the QUAL section transcribed |
| `P4` | **SEC `N-CSR`, Dimensional ETF Trust**, accession `0001133228-26-000245`, filed 2026-01-09, FY to 2025-10-31 (122,393,377 bytes) | **[PRIMARY DATA DOC]** | **[read in relevant part]** — the DUHP section transcribed |
| `P5` | **SEC `497` supplement, Invesco Exchange-Traded Fund Trust II**, accession `0001193125-19-313281`, dated 2019-12-13 | **[PRIMARY DATA DOC]** | **[read in full]** — 11,188 bytes; the liquidation list transcribed |
| `P6` | **SEC `N-8F`, Oppenheimer ETF Trust**, accession `0001597123-20-000059`, filed 2020-05-04 | **[PRIMARY DATA DOC]** | **[read in relevant part]** — Schedule A Item 15(b) and Item 26(a) transcribed |
| `D8` | **Wahal**, *The profitability and investment premium: Pre-1963 evidence*, **JFE 131(2), Feb 2019, pp. 362–377** | [PEER-REVIEWED] — **interested: *"I am a consultant to Avantis Investors"*, from his own site verbatim** | **[abstract only]** — the full abstract read from ASU's institutional repository (`asu.elsevierpure.com`, 45,623 bytes), plus the author's own one-line summary on `swahal.github.io/publications`. **The article itself was NOT obtained** (§10.13) |
| `M1`–`M8` | **My own measurements** — `data/C4_cz_measurement.json`, `C4_longonly_measurement.json`, `C4_ownuniverse.json`, `C4_deflator_ew.json`, `C4_robust.json`, **`C4_french_size_op.json`**, **`C4_deflator_vs_assetgrowth.json`**, with the seven scripts `data/C4_measure_*.py`, `C4_robust.py` and the fetcher `data/C4_fetch.py` | `[MEASURED IN BRIEF]` | endpoints in §8.1; controls in §8.2 |

**No asset-manager marketing is cited for any return anywhere in this brief.** `alphaarchitect.com`,
`larryswedroe.substack.com`, `etfdb.com`, `microalphas.com`, `signaltrace.wiki`, `scientificportfolio.com`,
`bitget.com` and `studocu.com` all surfaced on these searches. **None is cited.** The one PR document I
saw (`prnewswire.com`, Invesco product-line changes) is **[SALES INSTRUMENT]** and I replaced it with
`P5`, the filed 497, before using the fact it carried (§5.4).

**Both camps carry an interest and I say so at every use.** `D1`/`D1b` authors own the decay finding;
`D2`'s authors own the dataset whose value depends on anomalies being real; `D5`'s authors run a
systematic fund; `D6`'s authors are Dimensional. `D7`'s author authored the measure under review.

---

## 2. `Q1` — WHAT IS MEASURED ABOUT POST-PUBLICATION DECAY, AND BOTH CAMPS IN FULL

### 2.1 THE DRAFT-VERSUS-PUBLISHED FINDING, AND IT IS IN THE FIELD'S FOUNDING DECAY PAPER

The lane carried the draft-versus-published hazard as central. **It fired, on the first source I
opened, and it fired on the most-cited numbers in the whole decay literature.**

| | **Oct 2012 draft (`D1`)** | **May 2013 draft (`D1b`)** | **published JF 2016 (`D1c`)** |
|---|---|---|---|
| characteristics | **82** | **82** | **97** |
| out-of-sample (post-sample, pre-publication) decay | **~10%** | **~10%** | **26%** |
| is that decay significant? | ***"not statistically different from zero"*** | ***"This finding is statistically insignificant—we cannot reject the hypothesis that there are no statistical biases."*** | presented as the data-mining upper bound |
| post-publication decay | **~35%** | **~35%** | **58%** |
| implied publication effect | ~25% | ~25% | 32% |
| the limits-to-arbitrage result, from the abstracts | decay greater where stocks are ***"large, liquid, have high dividend yields, and have low idiosyncratic risk"*** | decay greater for ***"stocks with low idiosyncratic risk"*** only | — |

**Two things changed and both matter to this lane.**

- **The statistical-bias estimate went from 10% and insignificant to 26%**, and the `D1b` text is
  explicit about what the 10% could bear: *"We are able to reject hypotheses that involve large levels
  of statistical bias. For basic specifications, we can reject with 95% confidence that post-sample
  decay is greater than 32%."* **`[read in full]`** So in 2013 the authors could reject >32%
  statistical bias; by 2016 the published point estimate of it is 26%.
- **The size and liquidity half of the limits-to-arbitrage result dropped out of the abstract between
  the two drafts** while idiosyncratic risk stayed. §6 shows why: in the body it survives
  univariately and dies under controls.

**I did not open `D1c`.** The 97 / 26% / 58% figures are carried here from a search summariser
**and** from `D2`'s verbatim restatement (*"MP replicate 97 published predictors… Returns decline by
only 26%"*), which is a [WORKING PAPER] restatement, not the article. **Two independent secondary
restatements is still not a read, and §10.1 records it.** What I *can* say at first hand is §8.3: my
own panel measurement on a different dataset reproduces **0.42** as the median post-publication/
in-sample ratio across 200 predictors, i.e. a **58% decline**.

### 2.2 THE CAMP THAT SAYS DECAY IS REAL ECONOMICS

- **`D1b`, read in full.** 82 characteristics from 68 studies; 72 replicated in-sample; **10 they
  could not replicate at all.** Decay attributed to statistical bias (10%) plus *"price pressure from
  aware investors"* (the residual 25%). Corroborating mechanism: post-publication increases in
  volume, variance and short interest, and the short-minus-long short-interest gap widening after
  publication (intercept 0.109, p = 0.045; §3.5).
- **`D2`, read in full** — the strongest statement of the counter-counter-argument and it is a review,
  so it aggregates. Four stylised facts they say demonstrate *"publication bias is not a dominant
  factor"*: almost all findings replicate; **predictability persists out-of-sample (74% of the
  in-sample mean survives the first three post-sample years)**; t-stats far exceed 2.0; predictors are
  weakly correlated. Empirical-Bayes shrinkage across three meta-studies accounts for **only 10–15%
  of in-sample mean returns** and the false-discovery rate is **under 10%**.
- **`D2`'s decomposition of the 50% post-publication decline, quoted:** *"Multiple testing statistics
  provide a direct estimate of publication bias effects… and imply a roughly 12% decline… The
  remaining 38% decline, then, is a decline in the expected return."*
- **`D2`'s identifying argument is an autocorrelation argument and it is the cleanest thing in the
  dispute:** *"monthly predictor returns have very little serial autocorrelation. The mean
  autocorrelation is 7% at 1 month and falls to zero at 3 months. So return decay driven by
  publication bias should show up just months after the original samples end, not a decade later."*
  Their event-time figure: returns decline **~25% three years post-sample**, **~40% five years**, and
  reach the full **50%** only **ten years** out.

### 2.3 THE CAMP THAT SAYS IT IS A STATISTICAL ARTEFACT — AND THE ONE THAT SAYS IT IS NEITHER

- **`D5` (Falck–Rej–Thesmar), read in relevant part.** 72 US anomalies replicated on their own data.
  Sharpe decays ~50% post-publication, consistent with `D1c`. Then the decomposition: **"The year of
  publication alone… explains 30% of the variance of Sharpe decay across factors: Every year, the
  Sharpe decay of newly-published factors increases by 5ppt"**, and *"every decade the applicable
  haircut decreases by approximately 50%"*. Two more overfitting proxies — **the number of operations
  required to calculate the signal**, and two measures of **in-sample Sharpe sensitivity to
  outliers** — add **15%** more explanatory power. **"Arbitrage-related variables only marginally
  contribute."** International, unadjusted, the drop looks like **~90%**; size-adjusted, **25–50%**.
- **`D3` (Chen & Velikov), read in full — and it belongs in neither camp because it refuses to
  separate them.** Their headline is explicitly *"post-publication and post-2005"*. **Table 2, Panel
  A, transcribed in full by me** (bps/month, turnover in %/month, standard errors under each):

  | | Gross Return | Turnover (2-sided) | Ave. Spread Paid | Return Reduction | **Net Return** |
  |---|---|---|---|---|---|
  | In-sample | 68 (3) | 39 (3) | 206 (6) | 74 (7) | **−7 (6)** |
  | Post-publication | 28 (4) | 40 (3) | **85 (4)** | 30 (3) | **−1 (5)** |
  | Post-pub and post-2005 | 19 (2) | 41 (4) | **68 (2)** | 24 (2) | **−5 (3)** |

  Panel B (cost-mitigated, selected in-sample) gives the **4 bps** that round 1 carried: in-sample net
  44, post-publication 9, **post-pub and post-2005 = 4**. Figure 6's slopes: **44%** post-publication,
  **28%** once post-2005 only, **25%** net. And the sentence that makes it an era paper as much as a
  decay paper: *"a large chunk of the post-publication profitability found by MP and others likely
  comes from observations that pre-date the modern era of information technology."*

**A cost coincidence worth the programme's attention.** `D3`'s **"Ave. Spread Paid" post-pub-and-post-2005
is 68 bps** and this programme's **measured round trip is 67.6 bp**. I have **not** established that
the two conventions are identical — `D3`'s column is defined only through *Return Reduction ≈
turnover × spread*, and 41% × 68 bp = 28 against a reported 24, so the arithmetic is their own
"approximate". **Treat the match as a yardstick, not an identity.** What it does establish: the
programme's cost is not an outlier — it is the literature's own post-2005 number, which is what
[`../the-reversal-round.md`](../the-reversal-round.md) §1.1 already said.

---

## 3. `Q2` — WHAT HAS GROSS PROFITABILITY DONE SINCE 2013? REPORTED SEPARATELY, NEVER POOLED

### 3.1 The long–short spread, original-paper construction `[MEASURED IN BRIEF]`

**Chen–Zimmermann `PredictorLSretWide.csv`, October-2025 release, data through 2024-12.** Each
signal's in-sample window is its own `SampleEndYear` from `SignalDoc.csv`; for `GP` that is
**1963–2010**, publication **2013**. **% per month, gross, long minus short.**

| signal | in-sample 1963-07→2010-12 | post-sample pre-pub 2011–2013 | **post-publication 2014–2024** | programme window 2010–2024 | 2020–2024 |
|---|---|---|---|---|---|
| **`GP`** gross profitability | **0.303 [`t` 2.39], n=570** | 0.438 [1.44], n=36 | **1.024 [2.65], n=132** | 0.793 [2.71], n=180 | 1.482 [1.93], n=60 |
| `CBOperProf` cash-based op. prof. | 0.474 [3.09] | 0.480 [0.91] | 0.651 [1.42] | 0.504 [1.41] | 0.360 [0.41] |
| `OperProf` FF operating prof. | 0.461 [3.07] | 0.667 [2.34] | 0.412 [1.42] | 0.409 [1.85] | 0.662 [1.26] |
| `OperProfRD` op. prof. before R&D | 0.290 [1.58] | 0.359 [0.61] | **1.079 [2.31]** | 0.795 [2.15] | 0.719 [0.83] |
| **median of 200 CZ predictors, post-pub ÷ in-sample** | — | — | **0.42** | — | — |

**Ratios and where each sits in the 200-predictor decay distribution:** `GP` **3.01 (99th
percentile)**, `OperProfRD` **3.02 (99.5th)**, `CBOperProf` **1.17 (86.5th)**, `OperProf` **1.03
(84th)**. The pooled panel: mean ratio 0.409, median 0.423, p25 0.116, p75 0.801, n = 200 predictors.

**Three things not to over-read.** (i) `GP`'s ratio is flattered by a **small denominator** — 0.303 is
a modest in-sample mean, so I report levels and `t`s beside it. (ii) **Every one of these four uses
the CURRENT-asset deflator** — I read CZ's source and confirmed it (§3.3) — so the whole table
inherits the investment-signal contamination `R2-02` §2.1 identified. (iii) The post-publication
window is **132 months**. A `t` of 2.65 on 132 months is not a decided question.

### 3.2 The LONG LEG, which is the only leg this programme can trade `[MEASURED IN BRIEF]`

**This is the section the decay literature does not contain (§7.1).** Two benchmarks, because the
choice of benchmark decides the sign (§7.2): the **CRSP value-weighted market** (Ken French
`Mkt-RF + RF`) and the **sort's own universe** (the simple mean of the sort's five quintile
portfolios, which for an equal-count sort *is* its equal-weighted universe).

**Gross profitability, `GP`, % per month:**

| construction & benchmark | window | **LONG** | `t` | **SHORT** | `t` | LS | `t` | long's share of LS |
|---|---|---|---|---|---|---|---|---|
| VW quintile, price > \$5, **vs VW market** | in-sample | **+0.187** | 2.40 | −0.110 | −1.56 | 0.296 | 2.34 | **63%** |
| " | **post-pub 2014–2024** | **+0.179** | **1.25** | **−0.746** | **−3.52** | 0.925 | 3.20 | **19%** |
| " | 2020–2024 | +0.203 | 0.78 | −1.013 | −2.53 | 1.215 | 2.21 | 17% |
| **EW quintile, vs its OWN universe** | in-sample | **+0.239** | **4.71** | −0.281 | −3.34 | 0.520 | 4.53 | 46% |
| " | **post-pub 2014–2024** | **+0.405** | **3.00** | −0.567 | −1.84 | 0.972 | 2.41 | 42% |
| " | 2010–2024 | +0.379 | 3.56 | −0.533 | −2.31 | 0.912 | 2.98 | 42% |
| " | 2020–2024 | +0.462 | 2.41 | −0.674 | −1.24 | 1.137 | 1.71 | 41% |
| **VW quintile, price > \$5, vs its OWN universe** | in-sample | +0.175 | 2.19 | −0.122 | −1.80 | — | — | — |
| " | **post-pub 2014–2024** | **+0.349** | **2.27** | −0.576 | −3.33 | — | — | — |
| **VW quintile, ME > NYSE 20th pct, vs own universe** | **post-pub 2014–2024** | **+0.429** | **2.62** | −0.592 | −3.49 | — | — | — |

**Against the market, the long leg did not decay and did not grow: +18.7 → +17.9 bp/month, and
`t` 1.25.** The entire widening of the spread is the short leg going from −11 to −75 bp/month.
**Against the sort's own universe the long leg grew, from +24 to +40 bp/month at `t` 3.00.** Both are
true of the same months; §7.2 says which I weight.

**Concentration and robustness of the post-publication long leg (VW, price > \$5, vs VW market),
`[MEASURED IN BRIEF]`:** mean **+17.9 bp [`t` 1.25]**; **drop 2023 and it is +7.2 bp [`t` 0.50]**;
drop 2020 Q1 and it is +10.7 bp [`t` 0.77]; **three of 132 months (2.3%) carry half the total**;
median **+14.5 bp** below the mean of 17.9, so the **right** tail is doing the work; symmetric 1% trim
**+16.9 bp**, ex-top **+14.1**, ex-bottom **+20.7**. **The same robustness run on `CBOperProf` and
`OperProfRD` survives everything** — worst leave-one-year-out +33.5 and +38.1 bp at `t` 2.01 and 2.25.
**So the one definition this programme can compute is the one whose long leg is fragile to a single
year.** `data/C4_robust.json`.

**Name the top trade.** The largest post-2013 monthly long–short for `GP` (VW, \$5) is **2021-07 at
+9.10%**, **7.1% of the whole post-2013 sum**; the worst is **2022-02 at −7.95%**. For `CBOperProf`
the largest single month is **2020-03 at +17.02%, which is 20.4% of its entire post-2013 sum** —
**cash-based operating profitability's post-publication long–short result is materially one COVID
crash month**, and its worst month is 2020-11 at −13.80%.

**Exposure, vol, Sharpe and maxDD `[MEASURED IN BRIEF]`** — on the monthly relative series, compounded:

| | window | mean %/mo | vol %/mo | ann. SR | **max DD** | trough |
|---|---|---|---|---|---|---|
| `GP` EW long − own universe | in-sample | 0.239 | 1.21 | 0.68 | **−23.2%** | 1980-02 |
| `GP` EW long − own universe | post-pub | 0.405 | 1.55 | 0.90 | **−6.8%** | 2016-04 |
| `GP` VW \$5 long − own universe | in-sample | 0.175 | 1.91 | 0.32 | **−40.7%** | 1980-11 |
| `GP` VW \$5 long − own universe | post-pub | 0.349 | 1.77 | 0.68 | **−16.6%** | 2022-12 |
| `GP` VW \$5 long–short | in-sample | 0.296 | 3.02 | 0.34 | **−57.7%** | 1980-06 |
| `GP` VW \$5 long–short | post-pub | 0.925 | 3.32 | 0.96 | **−23.3%** | 2022-12 |

**The worst relative drawdown of a long-only gross-profitability tilt against its own universe is
−40.7%, and it troughed in November 1980 — thirty-three years before publication.** `C3`'s lane
should have this; it is monthly, and says nothing about daily path.

**Breakeven cost, stated with its assumption named.** At `R2-02`'s turnover figure for an
annually-rebalanced profitability sort (**1.96% one-sided per month**, from Novy-Marx & Velikov), the
post-publication long leg of **+34.9 bp/month** (VW, \$5, vs own universe) breaks even at a
**round-trip cost of ≈1,780 bp**, against a measured **67.6 bp** — a margin of ~26×. `[MY ARITHMETIC
on R2-02's turnover figure and the programme's own cost number — not from any paper.]` **And a filed
cross-check exists:** `P4` reports DUHP's **portfolio turnover rate at 3% per year**, which would make
the cost term smaller still — with the caveat that an ETF's SEC-reported turnover **excludes in-kind
creations and redemptions** and therefore understates a cash-settled book's turnover. **For this
family, at this turnover, cost is not the binding constraint.** That agrees with `R2-02` §4 and
disagrees with round 1's framing.

### 3.3 THE DEFLATOR, TAKEN PAST 2014 FOR THE FIRST TIME IN THIS CAMPAIGN `[MEASURED IN BRIEF]`

`R2-02` established that the deflator decides gross profitability's significance and could only show
it **in-sample**. Two things let me extend it.

**First, the source code, read in full.** CZ's `Predictors/GP.py`: `df["GP"] = (df["revt"] -
df["cogs"]) / df["at"]`, financials excluded by `(sic < 6000) | (sic >= 7000)`. **Current assets.**
CZ's `Placebos/GPlag.py`: `(pl.col('sale') - pl.col('cogs')) / pl.col('l12_at')`. **Lagged assets —
and it is filed under `Placebos`, with `Cat.Signal = Placebo` and `Predictability in OP = indirect` in
`SignalDoc.csv`.** And `Predictors/CBOperProf.py` carries the comment `R2-02` quoted, verbatim:

> ```
> # some confusion about lagging assets or not
> # OP 2016 JFE seems to lag assets, but 2015 JFE does not
> # Yet no lag implies results much closer to OP
> df["CBOperProf"] = df["CBOperProf"] / df["at"]
> ```

**So all four signals in §3.1 use current assets.** That is a limit on §3.1, stated here rather than
buried.

**Second, I established the placebo file's weighting empirically**, because the comparison is void
without it. Over 738 common months the `GPlag` universe mean return is **1.1712 %/mo** against the
EW-quintile universe's **1.1358** and the VW-quintile universe's **0.9118**, and correlates
**0.9946** with the EW universe versus **0.8662** with the VW one. **`PlaceboPortsFull` is
equal-weighted quintiles.**

**The deflator's effect on the LONG LEG, both equal-weighted, vs own universe, % per month:**

| | in-sample 1963-07→2010-12 | post-pub 2014–2024 | 2010–2024 | 2020–2024 |
|---|---|---|---|---|
| **`GP`** = (revt−cogs)/AT | **+0.239 [`t` 4.71]** | **+0.405 [3.00]** | +0.379 [3.56] | +0.462 [2.41] |
| **`GPlag`** = (sale−cogs)/AT₋₁ | **+0.045 [`t` 0.80]** | **+0.256 [2.23]** | +0.233 [2.56] | +0.289 [1.52] |
| **paired difference `GP` − `GPlag`** | **+0.194 [`t` 4.98]** | **+0.149 [1.83]** | +0.146 [2.22] | +0.173 [1.21] |
| `GPlag` long–short | 0.213 [1.92] | 0.599 [2.13] | 0.536 [2.37] | 0.979 [1.93] |

**Positive control:** my `GPlag` in-sample long–short of **0.213 [1.92]** reproduces `R2-02`'s reading
of CZ's own appendix, **0.20 [1.85]**.

**Read it as three statements, because they point different ways.**
1. **In-sample, the lagged deflator destroys the long leg** — `t` 4.71 → 0.80. `R2-02`'s finding
   holds on the long leg and on equal weighting, neither of which it had.
2. **Post-publication, the lagged deflator does NOT destroy it** — +25.6 bp at `t` 2.23. The ratio of
   the two conventions narrows from 5.3× to 1.6×.
3. **The increment is worth a persistent ~15–19 bp/month of long-leg alpha** and has itself not
   decayed.

**Three caveats, and they are not small.** `GPlag` differs from `GP` on **three** axes, not one:
deflator (`AT₋₁` vs `AT`), numerator (`sale` vs `revt`), and **financial firms are NOT excluded**.
**It is therefore not a clean one-variable contrast** and I will not call it one. Second, `GPlag`'s
portfolio construction was inferred by me from return correlations, not read from CZ's portfolio
code, which I did not find. Third, n = 132.

### 3.4 DRAFT VERSUS PUBLISHED ON THE FOUNDING PAPER — A CLEAN NEGATIVE

The lane was warned that a paper's version history is itself data. **For gross profitability it is
not.** `D7`, the **June 2012** 73-page working paper, Table 2's discussion read verbatim: *"the most
profitable firms earning 0.31 percent per month higher average returns than the least profitable
firms, with a test-statistic of 2.49"*, sample *"July 1963 to December 2010"*, FF3 alpha *"0.52
percent per month, with a test-statistic of 4.49"*. **Identical to the published JFE 108(1) figures
`R2-02` read in full.** The paper shrank from 73 to 28 pages; **its headline did not move.**

**A cross-lane note for `C1`, found here and not hunted for.** `D7`'s **footnote 3**, verbatim:
*"Firms' revenues, costs of goods sold, and assets are available on a quarterly basis beginning in
1972 (Compustat data items REVTQ, COGSQ and ATQ, respectively), allowing for the construction of
gross profitability strategies using more current public information than those presented here."*
**The author of the annual construction names the quarterly variant in a footnote of his own working
paper, and flags the reason to prefer it.** `C1` owns this; I stop at pointing.

### 3.5 What the sources say about post-2013, as distinct from what I measured

- **`D6`, Novy-Marx & Medhat's own reading, §B.3 verbatim:** Internet Appendix *"Table D1… repeats the
  regression in Table B3 for two sub-periods split at the year 2000. It shows results similar to those
  for the full sample in the early period **but even stronger results in the late period**, during
  which OP_R&D fully subsumes COP_R&D."* **[read in full of the sentence; the table itself still not
  obtained — §10.2.]** **The two authors most interested in profitability's survival say it is
  stronger after 2000.** Their Table B3 (1963-07→2023-12, cap-weighted WLS, `/BE+minority interest`),
  transcribed by me: `OP` **0.88 [5.85]** alone, **−1.00 [−1.96]** once `OP_R&D` enters; `COP` **0.35
  [4.57]** → **0.04 [0.42]**; `OP_R&D` **1.10 [7.91]**; and the asset-growth control `ln(AT/AT₋₁)`
  **−0.44 [−3.41]** — the investment term `R2-02` identified, still loading.
- **The same firm's own fund lost 124 bp/yr to the Russell 1000 over the same period (§5.3).** I
  record the tension; I do not resolve it. Different object: one is a cap-weighted Fama–MacBeth slope
  on trimmed characteristics, the other a net-of-fee, REIT-excluding, multi-factor portfolio.
- **`D3` covers gross profitability only as one of 204 rows.** Its per-anomaly results are not in the
  article; I did not obtain its internet appendix (§11).

---

## 4. `Q3` — DECAY VERSUS ERA-DEPENDENCE. THE EVIDENCE CANNOT SEPARATE THEM, AND TWO SOURCES SAY SO

### 4.1 What the literature says, in its own words

- **`D4` (Jacobs & Müller), read in full.** 231 anomalies (the **published** JFE version has
  **241** — a second draft-versus-published count change, §10.3), 39 markets, 1980–2015, more than two
  million anomaly country-months.
  - US baseline: **36% post-sample and 60% post-publication decline (EW); 36% and 65% (VW)** — *"in
    line with McLean and Pontiff (2016)"*, whose own figures they give as 26% and 58%.
  - **The abstract-level qualifier, verbatim: *"although these economically large estimates appear to
    be partly explained by a general time trend during our sample period."***
  - **§3.3 "Time effects", verbatim: *"In Panel A, we include a linear time trend. In Panel B, we
    alternatively include month fixed effects. Both approaches indeed subsume a substantial fraction
    of the explanatory power of the U.S. post-publication dummies, which nevertheless remain
    significant."*** And the summary: *"while general time effects appear to partly reduce the role
    of post-sample and post-publication effects in the U.S. market, they cannot fully explain the
    differences between the U.S. and [international markets]."*
  - **The cross-country identification, which is the strongest separation anyone has achieved:**
    *"none of the 38 international markets yields a reliable post-publication decline"*, and
    unconditionally the US is **not** higher than abroad (US VW 33 bp vs international 38 bp; US EW 58
    vs 49), so *"data mining is unlikely to be the major explanation."* Their Table 9 rows: **USA
    −29% post-sample / −56% post-publication (EW), −36% / −64% (VW); large developed markets −16% /
    −27% (EW), −23% / −28% (VW).**
  - **Their era number is blunt:** *"the average value-weighted long/short return in the most recent
    subsample period (2004-2015) is reduced to 16 bp in the U.S. market. This value is only
    marginally (t-stat 1.67) different from zero. In contrast, the corresponding estimate for the
    pooled international sample is 38 bp."*
- **`D3` does not separate them; it compounds them on purpose.** Its headline 4 bps is *post-publication
  **and** post-2005*, and the authors attribute the excess of 72% over 44% decay precisely to
  *"stale data"* — i.e. era.
- **`D2` names era mechanisms explicitly** for the 38% residual it calls a real decline in expected
  return: *"It should not be surprising if mispricing is traded away after it is publicized… or if
  improvements in liquidity decrease mispricing (Chordia et al. (2014))"*, and it points to declines
  **before** the original samples begin (Linnainmaa & Roberts 2018) and **outside** the US (`D4`) —
  *"these findings are important for understanding the nature of predictability, but they do not
  measure publication bias."*
- **`D5` is the one paper whose decomposition is keyed to publication and not to the calendar** — and
  its key variable is publication **recency**, which it reads as a mining proxy, not an arbitrage one.

**So the state of the field: every source that tries finds the era term absorbs a substantial fraction
of the decay and none can eliminate it. That is the honest answer the bar allowed, and it is the one
the evidence supports.**

### 4.2 My own era test, which is a proper negative control `[MEASURED IN BRIEF]`

**Ken French `F-F_Research_Data_5_Factors_2x3`, built from the 202607 CRSP database, 1963-07→2026-07,
757 months.** The publication dates of these five differ by **three decades**. If a post-2013 decline
is *publication* decay, a factor published in 1981 or 1992 should not show one in 2013.

| factor | first documented | 1963-07→2010-12 | 1963-07→2013-06 | **2013-07→2026-07** | 2010-01→2026-07 | 2020-01→2026-07 |
|---|---|---|---|---|---|---|
| `Mkt-RF` | — | 0.448 [2.36] | 0.478 [2.61] | **1.062 [3.08]** | 1.086 [3.55] | 1.073 [1.88] |
| `SMB` | Banz 1981 / FF 1993 | 0.294 [2.26] | 0.276 [2.21] | **−0.151 [−0.66]** | −0.069 [−0.36] | −0.128 [−0.35] |
| `HML` | FF 1992/1993 | 0.402 [3.36] | 0.389 [3.40] | **−0.043 [−0.15]** | −0.031 [−0.13] | 0.220 [0.45] |
| `CMA` | FF 2015 | 0.331 [3.88] | 0.331 [4.04] | **−0.075 [−0.41]** | 0.034 [0.23] | 0.061 [0.19] |
| **`RMW`** | FF 2015, lineage 2006–2013 | **0.276 [2.88]** | **0.269 [2.92]** | **+0.213 [1.12]** | 0.180 [1.14] | 0.283 [0.83] |

**Four long–short factors with publication dates spread over thirty-four years, three of them at or
below zero in the same thirteen-year window. That is an era, not four publication effects.** And the
one that retains **79% of its pre-2013 mean** is profitability — though it loses significance
(`t` 2.92 → 1.12) on 157 months.

**`RMW` is the Fama–French `/BE` definition with interest expense — `R2-02`'s FOURTH definition, which
Hou–Xue–Zhang report insignificant (`Ope`, `t` 1.2).** It is not gross profitability and I do not
treat it as such; its value here is as an independent construction, from a non-interested source,
pointing the same way.

### 4.3 And the era test applied to the family itself `[MEASURED IN BRIEF]`

**`GP`, equal-weighted quintile, long leg minus its own universe, in five-year blocks:**

| block | %/mo | `t` | | block | %/mo | `t` |
|---|---|---|---|---|---|---|
| 1965–69 | +0.262 | 2.04 | | 1995–99 | +0.549 | 3.79 |
| **1970–74** | **−0.224** | **−1.56** | | 2000–04 | +0.439 | 2.27 |
| **1975–79** | **−0.023** | **−0.18** | | **2005–09** | **+0.005** | **0.03** |
| 1980–84 | +0.539 | 3.33 | | 2010–14 | +0.346 | 2.30 |
| 1985–89 | +0.420 | 3.49 | | 2015–19 | +0.329 | 1.58 |
| 1990–94 | +0.223 | 1.39 | | 2020–24 | +0.462 | 2.41 |

**The series' two negative blocks and its one flat block all PRE-DATE publication. The three
post-publication blocks are all positive and all in line with the long-run mean. There is no break at
2013 to find.** This programme's own records report numbers inverting by era with no publication
event; **on the one family it can compute, the published record does the same thing, and three times
before anyone published it.**

---

## 5. `Q4` — THE LIVE FUNDS. PRIMARY DATA ONLY, AND THE SURVIVORSHIP PROBLEM NAMED FIRST

### 5.0 NAME THE SURVIVORSHIP PROBLEM BEFORE ANY NUMBER

**Every fund in §5.1–§5.3 is alive. That is a selected sample and the selection is on the dependent
variable.** §5.4 gives one filed death. I found **one**, and the right inference from "one found" is
that I did not search the graveyard systematically — not that there is only one grave (§10.7). **Read
every number below as an upper bound on what a 2013 investor would have experienced.** Round 2
already recorded two overnight-strategy ETFs that launched in June 2022 and closed fourteen months
later; the same mechanism operates here.

**Second selection, and it is specific to "quality".** None of these funds tracks gross profitability.
**S&P's Quality indices score on return-on-equity, accruals ratio and financial leverage**; MSCI's on
ROE, debt-to-equity and earnings variability. Round 2 and Hou–Xue–Zhang both find the `/BE` and
composite constructions weaker than `GP` or `CbOP`. **These are evidence about the adjacent
construction, and I say so at every number.**

### 5.1 Large caps: two funds, ten years each, both NEGATIVE net of fees

**`P3` — iShares MSCI USA Quality Factor ETF (QUAL), Cboe BZX, inception 2013-07-16, fee 0.15%.
Annual shareholder report filed in an N-CSR, FY to 2025-07-31. [PRIMARY DATA DOC], transcribed by
me:**

| | 1 Year | 5 Years | **10 Years** |
|---|---|---|---|
| **Fund NAV** | 8.31% | 14.34% | **12.75%** |
| MSCI USA Index | 16.96% | 15.67% | **13.62%** |
| MSCI USA Sector Neutral Quality Index **(Spliced)** | 8.47% | 14.54% | **12.94%** |

**−87 bp/yr over ten years, net. And the index itself is −68 bp/yr, so it is not the fee.** Note
**"(Spliced)"**: the benchmark index's own history is spliced, i.e. the index definition changed
during the fund's life. I did not establish when or how (§10.5).

**`P1` — Invesco S&P 500 Quality ETF (SPHQ), NYSE Arca, fee 0.15%, net assets \$17.27bn. N-CSR, FY to
2026-04-30. [PRIMARY DATA DOC]:**

| | 1 Year | 5 Years | **10 Years** |
|---|---|---|---|
| **Fund NAV** | 23.96% | 13.73% | **14.44%** |
| S&P 500 Quality Index | 24.16% | 13.92% | **14.66%** |
| S&P 500 Index | 31.05% | 13.14% | **15.26%** |

**−82 bp/yr over ten years, net; the index −60 bp/yr. Over five years it is +59 bp/yr.** And the
filing's own explanation of the last year, verbatim: *"securities with a greater exposure to the
quality factor, a composite measure of return-on-equity, leverage, and balance sheet accruals,
underperformed the S&P 500® Index."*

### 5.2 Mid and small caps: thin positives, and one contaminated record

**`P1` — Invesco S&P MidCap Quality ETF (XMHQ), fee 0.25%, net assets \$5.19bn, FY to 2026-04-30:**

| | 1 Year | 5 Years | 10 Years |
|---|---|---|---|
| **Fund NAV** | 16.80% | **8.57%** | 12.48% |
| Blended — S&P MidCap 400 Quality Index | 17.11% | 8.85% | 12.75% |
| S&P MidCap 400 Index | 29.49% | **7.60%** | 11.29% |
| S&P Composite 1500 Index | 31.17% | 12.65% | 14.91% |

**AND THE FILING DISCLOSES THE THING A FACTSHEET WOULD BURY, VERBATIM:** *"The Blended - S&P MidCap
400 ® Quality Index reflects the performance of the **Russell Midcap Equal Weight Index**, the
Fund's former underlying index, **through June 21, 2019**, followed by the performance of the Index
thereafter."* **XMHQ was not a quality fund for the first three years of its ten-year record. Its
genuine quality track record begins 2019-06-21 — about 6.9 years.** The five-year column is entirely
post-conversion, and there it is **+97 bp/yr net over the S&P MidCap 400** (8.57 vs 7.60) — **but
−408 bp/yr against the S&P 1500**, a different universe and the wrong benchmark for a mid-cap sleeve.
**The oldest-looking "quality" records are the ones most likely to be a different strategy wearing the
same ticker.**

**`P2` — Invesco S&P SmallCap Quality ETF (XSHQ), Cboe BZX, inception 2017-04-06, fee 0.29%, net
assets \$289m, FY to 2025-08-31:**

| | 1 Year | 5 Years | **Since inception (8.4 yr)** |
|---|---|---|---|
| **Fund NAV** | 5.18% | 11.94% | **8.72%** |
| S&P SmallCap 600 Quality Index | 5.51% | 12.27% | 9.08% |
| S&P SmallCap 600 Index | 3.51% | 11.64% | **8.47%** |
| S&P Composite 1500 Index | 15.06% | 14.57% | 14.21% |

**+25 bp/yr net over 8.4 years against its own cap-weighted small-cap benchmark; +61 bp/yr at the
index level. That is ~2 bp/month net, ~5 bp/month before fees.** No index-change note, so the record
appears continuous.

### 5.3 The purest commercial profitability tilt, from the research's own lineage

**`P4` — Dimensional US High Profitability ETF (DUHP), NYSE Arca, inception 2022-02-23, fee 0.20%,
net assets \$9.98bn, 176 holdings, **portfolio turnover rate 3%**. N-CSR, FY to 2025-10-31.
[PRIMARY DATA DOC]:**

| | 1 Year | **Since inception (3.7 yr)** |
|---|---|---|
| **Fund NAV** | 13.96% | **14.03%** |
| Russell 1000 Index | 21.14% | **15.27%** |

**−124 bp/yr net since launch.** And the filed management discussion, verbatim: *"High profitability
stocks underperformed low profitability stocks within large cap stocks."* Its own attribution lists
*"Emphasis on stocks with higher profitability detracted."* **3.7 years is not a verdict. It is,
however, the only live record of an explicit profitability tilt, it is from the firm that employs both
authors of `D6`, and it is negative.**

### 5.4 The death, filed

**`P5` — SEC Form 497, Invesco Exchange-Traded Fund Trust II, dated 2019-12-13, read in full.
Verbatim:** *"At a meeting held on December 12, 2019, the Board of Trustees of the Invesco
Exchange-Traded Fund Trust II approved the termination and winding down of each Fund, with the
liquidation payment to shareholders expected to take place on or about February 26, 2020."* The list
of 23 funds includes **Invesco Russell 1000® Quality Factor ETF (OQAL)** — and, at the same meeting,
**OVOL (Low Volatility), OMOM (Momentum), OSIZ (Size), OVLU (Value) and OYLD (Yield)**.

**`P6` establishes how OQAL got there:** Form N-8F, Oppenheimer ETF Trust, 2020-05-04, shows the
Oppenheimer single-factor suite — including **Oppenheimer Russell 1000® Quality Factor ETF** — was
**merged** into Invesco Exchange-Traded Fund Trust II on a shareholder vote of **2019-04-12**, then
wound down eight months later.

**Two readings, and I hold both.** (i) A quality-factor ETF existed and was liquidated: the
survivorship channel is real and a 2017-vintage investor in it was returned cash in February 2020.
(ii) **The entire single-factor product line died at one board meeting** — Quality alongside Value,
Size, Momentum, Low Vol and Yield. **That is a distribution event about one issuer's shelf, not six
simultaneous verdicts on six factors**, and treating it as factor evidence would be the same error as
treating a 2013-dated decline in HML as HML's publication effect (§4.2). I have **not** established
OQAL's inception date from a filing (§10.6).

---

## 6. `Q5`, THE LANE'S OWN PUSH — IS DECAY STRONGER IN SMALL CAPS? TWO OF MY THREE TESTS SAY SOMETHING, AND THEY DISAGREE

### 6.1 The founding decay paper answers directly — and then takes it back

**`D1b` Table 7, transcribed by me in full** (dependent variable: monthly long–short return scaled by
its in-sample mean, post-publication months only; SE in parentheses, p in brackets; random effects,
SE clustered on time; **n = 9,823 for every column**):

| | Size | Spreads | Dollar Vol. | Idio. Risk | Dividends | Sharpe | T-Stat. | R² |
|---|---|---|---|---|---|---|---|---|
| coefficient | **−1.490** | 0.999 | −1.671 | **4.054** | −1.381 | 0.129 | 0.002 | −3.906 |
| (SE) | (0.598) | (0.592) | (0.642) | (0.855) | (0.352) | (0.125) | (0.013) | (4.524) |
| [p] | **[0.013]** | [0.092] | [0.009] | **[0.000]** | [0.000] | [0.301] | [0.900] | [0.388] |
| **regression R²** | **0.000** | **0.000** | **0.001** | **0.000** | **0.001** | 0.000 | 0.000 | 0.000 |

**Sign: decay is LARGER for characteristic portfolios made of larger, more liquid, lower-idio-vol,
dividend-paying stocks.** The body states it: *"Characteristic portfolios that on average consist of
larger stocks, stocks with smaller bid ask spreads, and stocks with high dollar volume decline
more."* **And their own interpretive frame is the programme's:** *"characteristic portfolios that
consist more of stocks that are costlier to arbitrage (e.g., smaller stocks, less liquid stocks,
stocks with more idiosyncratic risk) should decline less post-publication."*

**Then Table 8 takes it back. Transcribed by me:** with Idio Risk in the regression, **Size becomes
0.047 (SE 1.086, p = 0.965)**, Spreads −1.086 (p 0.380), Dollar Vol. −0.138 (p 0.836), Dividends
−0.083 (p 0.901); only **Idio Risk survives (3.900 to 4.810, p 0.002–0.070)**. Their own summary:
*"Throughout all of the regressions in Table 8, idiosyncratic risk is the only factor that has a
significant effect on the post-publication decline."*

**Three things nobody quotes and all three are negative. The R² of every Table 7 column is 0.000–0.001.
The unit of observation is the characteristic portfolio, so the effective n is 82, not 9,823. And size
does not survive one control.** The sign favours this programme's universe; **the evidence does not
support leaning on it.**

### 6.2 What the other sources say

- **`D2`, verbatim:** *"Predictability may rely on the uninformed trades of retail investors… or
  small, illiquid stocks (Novy-Marx and Velikov (2015))"* — a level claim about where the premium
  lives, not a decay-differential claim.
- **`D5`** finds arbitrage-related variables only marginally predictive of decay at all, which if true
  removes the mechanism by which decay *should* be size-dependent.
- **`D4`** finds the US–international gap is not explained by firm size: *"the value-weighted
  results, which are dominated by larger firms, are comparable to the equally weighted results."*
- **`R2-02` §7 found `CbOP` slightly WEAKER in microcaps** (slope 2.48 [9.62] vs 2.60 [9.69]).

### 6.3 My test, and it is a null `[MEASURED IN BRIEF]`

The EW-minus-VW long-leg alpha against each construction's own universe is the small-cap increment.
Paired, same months:

| window | **EW − VW long-leg alpha** | `t` | n |
|---|---|---|---|
| in-sample 1963-07→2010-12 | +0.057 | 0.83 | 570 |
| 2011–2013 | +0.127 | 0.89 | 36 |
| **post-publication 2014–2024** | **−0.068** | **−0.42** | 132 |
| 2010–2024 | +0.019 | 0.16 | 180 |
| 2020–2024 | −0.235 | −0.81 | 60 |

**There is no measurable small-cap increment to gross profitability's long-leg alpha in any window,
and therefore no measurable differential decay by size.** `GP`'s long leg vs own universe improved
under **both** weightings (EW +0.239→+0.405; VW +0.182→+0.472) and under **both** screens (price>\$5
+0.175→+0.349; ME>NYSE20 +0.158→+0.429). The point estimates drift the way `D1b` would *not* predict —
the VW version improved more — **but not one difference clears 1.0 in `t`.** This is a power statement,
not a finding. **I record the conflict with `D1b` Table 7 and adjudicate nothing.**

### 6.4 A SECOND, INDEPENDENT MEASUREMENT THAT CONTRADICTS §6.3 — AND THE CONFLICT RESOLVES ON DEFINITION

**I flagged this as a measurement I had the bytes for and had not made. I then made it.**

**Ken French's `25 Portfolios Formed on Size and Operating Profitability`, built from the 202607 CRSP
database, 757 monthly observations 1963-07→2026-07, zero `−99.99`/`−999` cells in either returns
block.** A wholly independent construction: **FF's `OP = (sales − COGS − SG&A − interest expense) /
book equity`**, NYSE breakpoints on both legs of a 5×5 double sort, June rebalance, **utilities and
financials INCLUDED** (the file says so), split at **2013-06/2013-07**. Within a size row the five OP
cells are an equal-count partition, so the row mean is that row's own universe.

**`HiOP − LoOP`, % per month, by size quintile:**

| | **value-weighted** | | **equal-weighted** | |
|---|---|---|---|---|
| size quintile | pre-pub 1963-07→2013-06 | **post-pub 2013-07→2026-07** | pre-pub | **post-pub** |
| **ME1 small** | +0.295 [`t` 2.36] | **+0.051 [0.15]** | −0.056 [−0.49] | +0.260 [0.63] |
| **ME2** | **+0.378 [2.84]** | **−0.004 [−0.01]** | **+0.368 [2.74]** | **+0.002 [0.01]** |
| **ME3** | **+0.418 [2.87]** | **−0.062 [−0.19]** | **+0.362 [2.41]** | +0.081 [0.25] |
| **ME4** | +0.219 [1.67] | −0.093 [−0.31] | +0.204 [1.46] | +0.215 [0.77] |
| **ME5 big** | +0.203 [1.48] | **+0.248 [0.69]** | +0.111 [0.80] | +0.179 [0.53] |
| n months | 600 | **157** | 600 | 157 |

**The long leg against its own size row's universe, value-weighted:** ME2 **+0.179 [`t` 2.90] →
−0.022 [−0.13]**; ME3 **+0.187 [2.83] → −0.079 [−0.64]**; ME4 +0.120 [1.97] → −0.030 [−0.31]; ME5
+0.101 [1.50] → **+0.099 [0.74]**. **Every significant pre-2013 within-size long-leg alpha is gone,
and the only quintile whose point estimate survives intact is the largest.**

**That is the opposite direction to §6.3's null and to `R2-02`'s pre-2013 monotonic size ordering. I
do not discard either. Here is what I think drives it, and it is a definition, not a dataset.**

**French's `OP` is `R2-02`'s FOURTH definition** — `/BE`, with interest expense subtracted, R&D folded
into SG&A — which Hou–Xue–Zhang report insignificant (`Ope`, `t` 1.2) and which `D6`'s Table B3 shows
going to **−1.00 [`t` −1.96]** once `OP_R&D` enters. **And CZ's data agrees with French about that
definition:** my §3.2 `OperProf` (CZ's name for the FF `/BE` construction) has a long-leg alpha of
**+0.141 [`t` 2.58] in-sample falling to +0.113 [`t` 1.11]** post-publication equal-weighted, and
**+0.330 [`t` 3.14] falling to −0.177 [`t` −0.87]** against the VW market — the only one of the four
whose long leg turns negative. **Two independent vendors, two independent constructions of the same
definition, same verdict. The disagreement in this lane is between DEFINITIONS, not between
datasets** — and that is `R2-02`'s central finding arriving from a third direction.

**Four more things in the French data worth having.**
- **The universe shrank, and a lot.** Average firms in the small-cap HiOP cell: **300.3 pre-2013 →
  81.3 post-2013**, a 73% fall. The other nine cells move between 60 and 100. **The small-cap cell
  that carried the pre-2013 premium is a quarter of its former size**, which is a composition change
  on top of an era change, and it cuts the breadth of any small-cap profitability sleeve.
- **The recent small-cap action is all short leg.** 2021-07→2026-07, equal-weighted ME1: `HiOP − LoOP`
  **+1.050 [`t` 1.43]**, of which the long leg is **−0.254 [−0.76]** and the short leg **−1.304
  [`t` −2.38]**. **Same shape as §3.2 on a different construction and a different definition: the leg
  that moved is the one this programme cannot trade.**
- **Equal weighting and value weighting disagree about the smallest quintile even pre-2013:** VW
  **+0.295 [2.36]** against EW **−0.056 [−0.49]**. Within the same 25 cells, from the same file, over
  the same 600 months. A fifth instance for `C2`'s file.
- **FF's own warning, quoted from the file header:** *"Please be aware that some of the value-weight
  averages of operating profitability for deciles 1 and 10 are extreme. These are driven by
  extraordinary values of OP for individual firms."* The `LoOP` cell is a tail cell by construction.

### 6.5 THE PRE-1963 TEST, AND THE TRAP IT SETS FOR THE DEFLATOR

**`D8` (Wahal 2019), abstract verbatim from ASU's institutional repository:** *"I investigate the
profitability and investment premium in stock returns using hand-collected data from Moody's Manuals
for 1940–1963. Controlling for value, the profitability premium emerges as important in this period.
**In contrast, there is no reliable relation between investment and returns, regardless of whether
investment is measured using growth in total assets or book equity and even after extending the data
back to 1926.** In spanning regressions, factors constructed from profitability and book-to-market
ratios (RMW and HML, respectively) improve the mean-variance efficient tangency portfolio but the
investment factor (CMA) does not."* **[abstract only — §10.13.]** The author's own summary on his own
page: *"Even in the pre-Compustat period, the profitability premium is quite robust. Investment, not
so much."* **He discloses on the same site that he consults to Avantis Investors, which sells
profitability-tilted funds.**

**Why this is the strongest single argument against the data-mining story for THIS family:** the
premium is present in **1940–1963**, before the discovery sample begins, on hand-collected data the
original researchers did not have. Combined with §4.3 — three pre-publication five-year blocks at or
below zero, three post-publication blocks all positive — **gross profitability has an out-of-sample
record in BOTH directions in time, which almost nothing in the factor zoo has.**

**And it sets a trap, which is mine to state and not Wahal's.** `GP/AT ≡ (GP/AT₋₁) ÷ (AT/AT₋₁)`, so
the current-asset deflator is arithmetically gross profitability times the reciprocal of asset growth
(`R2-02` §2.2's identity). **The investment signal it smuggles in is the one Wahal finds ABSENT
pre-1963 and back to 1926, whose factor (`CMA`) fails his own spanning test, and which my §4.2 finds
at −0.075 [`t` −0.41] post-2013.** Yet §3.3 measures that same increment at **+0.149 %/mo [`t` 1.83]**
post-publication on the long leg. **So I went and tested it. §6.7.**

### 6.7 I TESTED MY OWN EXPLANATION OF THE DEFLATOR AND IT FAILED `[MEASURED IN BRIEF]`

**The hypothesis:** the +15 bp/month that the current-asset deflator adds to gross profitability's long
leg is exposure to the **asset-growth anomaly's** return, because of the identity above. **If so, the
monthly series `GP_long − GPlag_long` should be strongly correlated with CZ's `AssetGrowth` long leg.**

CZ's `AssetGrowth` (`Sign = −1.0`, `SampleEndYear` 2003, published 2008, EW in its original spec), same
equal-weighted quintile file, long leg minus its own universe:

| window | **deflator increment `GP−GPlag`** | `t` | **`AssetGrowth` long − own universe** | `t` | `AssetGrowth` LS | `t` | **corr(increment, AG long)** | corr(increment, AG LS) | n |
|---|---|---|---|---|---|---|---|---|---|
| in-sample 1963-07→2010-12 | +0.194 | 4.98 | **+0.414** | **3.94** | +0.908 | 7.22 | **−0.106** | +0.311 | 570 |
| **post-pub 2014–2024** | +0.149 | 1.83 | **−0.093** | **−0.43** | +0.299 | 1.19 | **−0.294** | +0.140 | 132 |
| 2010–2024 | +0.146 | 2.22 | −0.006 | −0.04 | +0.420 | 2.12 | −0.225 | +0.191 | 180 |

**Two results and the second one is against me.**

1. **The asset-growth anomaly HAS decayed, cleanly and on the tradeable leg.** Its long leg goes from
   **+0.414 [`t` 3.94]** to **−0.093 [`t` −0.43]**; its spread from +0.908 [7.22] to +0.299 [1.19].
   **That is what post-publication decay looks like when it happens**, and it is a useful contrast
   case: published 2008, dead by 2014, and consistent with `CMA` at −0.075 post-2013 (§4.2) and with
   Wahal finding no investment premium back to 1926 (§6.5). **The investment leg is the member of this
   neighbourhood that is actually dead.**
2. **But the deflator increment is NOT the asset-growth return.** `corr` with the tradeable
   asset-growth long leg is **−0.106 in-sample and −0.294 post-publication** — small, and **the wrong
   sign**. With the long–short it is +0.311 and +0.140. **So the identity is arithmetic and the return
   is not: whatever the current-asset deflator adds, it is not explained by loading on the asset-growth
   anomaly's realised return, measured this way.**

**I had a tidy story and the data took it off me.** `R2-02`'s *"gross profitability measured against
current assets is partly an investment signal in a profitability costume"* is **exactly right as an
identity** — and on this evidence it does **not** follow that the extra return is the investment
anomaly's return. **The +15 bp/month is therefore unexplained, not explained**, which is a worse
position than I was in before I ran it, and the honest one. **The conservative reading stands for a
different reason: use the LAGGED deflator, because its economics is the one with the pre-1963 support
(§6.5) — and under it the post-publication long leg is +0.256 [`t` 2.23], not +0.405 [`t` 3.00]. The
defensible number is the smaller one.**

### 6.8 And per the standing rule: SIZE IS NOT PRICE

`R2-02` §7 established that Novy-Marx (2013), Ball et al. (2016) and Chen & Welch (2026) contain
**zero** instances of "share price", "price screen" or "\$5". **I add that CZ's portfolio files carry
no price field at all — only `ret`, `signallag`, `Nlong`, `Nshort` — and that French's 25 Size × OP
file carries `Average Market Cap`, `Number of Firms`, `BE/ME`, `OP` and `investment` blocks and NO
price block. Neither public source can yield the price distribution of the names carrying this effect,
and I did not produce one.** The `price > $5` screened file tells me only that the effect survives the
screen, not where in the surviving price distribution it sits. §10.4.

---

## 7. PAST THE SUB-QUESTIONS — FOUR THINGS THIS BRIEF WAS NOT ASKED FOR

*Plus two more in §6: the independent French size × OP decay table (§6.4) and the test of my own
deflator mechanism (§6.7), both of which were found after the bar had been met.*

### 7.1 THE DECAY LITERATURE MEASURES A SPREAD. THIS PROGRAMME CANNOT TRADE A SPREAD. I CHECKED ALL FIVE

I grepped the full extracted text of the five decay papers I read for `long leg`, `long side`,
`long-only`, `long portfolio`, `long minus`:

| paper | hits | **what the legs are used for** |
|---|---|---|
| `D1b` MP 2013 draft | `long side` 5, `short side` 6 | **short-interest differences only** — *"we subtract the average short interest of the long side… from the average short interest of the short side"* |
| `D1` MP 2012 draft | `long-only` 1, `short portfolio` 7 | same |
| `D3` Chen–Velikov | `long portfolio` 1, `short portfolio` 5 | turnover accounting (*"turns over 20% of its long portfolio and 20% of its short"*) |
| `D2` Chen–Zimmermann | `short portfolio` 1 | passing |
| `D4` Jacobs–Müller | `long leg` 4, `short leg` 5 | **cross-country correlation only** — Table 10's long-leg correlation rises 0.436→0.572, but so do control stocks 0.451→0.585 |
| `D5` Falck et al. | `short leg` 6 | construction description |

**Every decay estimate in all five is long–short.** Not one reports the post-publication decay of the
long leg's **return**. **So the "is it dead?" literature has no direct bearing on a long-only book,
and §3.2 is the measurement that bears on it** — where the answer is that the long leg neither decayed
nor grew against the market, and that 67–81% of the post-publication spread sits in the short leg.
**For a programme whose borrow is excluded ground, the post-publication strengthening of this family
is almost entirely unavailable.**

### 7.2 THE BENCHMARK FLIPS THE SIGN OF THIS LANE'S ANSWER, AND I WALKED INTO IT

`R2-01` found the benchmark moved `CbOP`'s long-leg `t` from 1.95 to 5.98, and `C2` exists because
round 2 found that kind of thing three times. **It happened to me, on this lane's central question.**

| `GP` long leg, EW quintile, post-pub 2014–2024 | mean %/mo | `t` | the sentence it supports |
|---|---|---|---|
| minus **CRSP value-weighted market** | **−0.125** | −0.49 | *"the equal-weighted long-only tilt has decayed to zero"* |
| minus **its own equal-weighted universe** | **+0.405** | **+3.00** | *"the long leg grew by 70% post-publication"* |

**Same data, same months, same signal, opposite conclusions.** The first is wrong because an
equal-weighted portfolio measured against a value-weighted market is carrying `SMB`, and `SMB` over
2013-07→2026-07 is **−0.151 %/mo** (§4.2). **The second is the one I weight**, because the question
"does the sort still pay?" is a question about the sort, not about size. **The operational rule: a
long leg must be benchmarked against the universe it is drawn from and weighted the way it is
weighted, and any long-only result quoted against "the market" should be assumed to be carrying a
size bet until someone checks.**

### 7.3 WHAT DECAYS IS NOT ONLY THE MEAN — PUBLISHED SIGNALS BECOME CORRELATED WITH EACH OTHER

This programme's effective breadth is **~10 independent instruments** against 1,573 names. `D1b` §3.7
and Table 9, read in full, is about exactly that quantity and nobody in this campaign has cited it:

- *"Simple correlations between characteristic-based portfolios are lower than we expected. The mean
  pairwise correlation in our study is 0.050 and the median is 0.047."* They add that this implies
  even lower covariance than Green et al., and conclude *"multi-characteristic investing is likely to
  enjoy substantial diversification benefits."*
- **But the diversification is between PUBLISHED and UNPUBLISHED, and publication destroys it.** A
  pre-publication characteristic's beta on other pre-publication characteristics is **0.634
  (p 0.00)**; on post-publication ones it is **0.025**. The post-publication interaction is **−0.555
  (p 0.00)**, so *"once a characteristic is published, the correlation of its returns with the returns
  of other yet-to-be-published characteristic returns virtually disappears, as the overall
  coefficient reduces to 0.634 – 0.555 = 0.079."* And published characteristics become **more**
  correlated with each other.
- **The implication for a breadth-10 book:** stacking published signals buys less breadth than their
  count implies, and **the breadth is in the unpublished ones** — which is the opposite of the
  direction this campaign has been travelling, and it is the argument for `R2-02`'s conclusion being
  a *single-candidate* conclusion rather than a combination one.
- **`D2` lists "predictors are weakly correlated" as one of its four stylised facts against publication
  bias.** It is the same fact; `D1b` shows it is conditional on publication status. **I record both
  and resolve neither.**

### 7.4 One more, briefly: the programme's fixture contains no pre-publication window

`GP`'s in-sample period ends **December 2010**; its working paper is dated **June 2012** (`D7`) and
circulated from 2010 at NBER and Q Group per its own acknowledgements; the JFE article is **April
2013**. **The programme's fixture starts 2010-01-04.** So **the whole fixture is post-sample, and all
but three years of it is post-publication.** There is no in-sample contamination to worry about and no
pre-publication benchmark to compare against — **any profitability result this programme produces is
already an out-of-sample result on the published signal, which is unusual and favourable, and which
also means `R8`'s separate pre-registered out-of-sample test is testing something else: stability,
not discovery.**

---

## 8. MY MEASUREMENTS — ENDPOINTS, CONTROLS, AND THE CONTROL THAT MATTERED

### 8.1 Endpoints, all re-runnable, all paced at 0.35 s, User-Agent contact `research@backtest-framework.org`

| file | endpoint | bytes | sha1 (first 12) |
|---|---|---|---|
| `PredictorLSretWide.csv` | `drive.usercontent.google.com/download?id=10sOryk_ddjkXagaajTKUk1nwJs2ZLRiI&export=download&confirm=t` | **3,293,172** | `71fe880a8923` |
| `PredictorAltPorts_LiqScreen_Price_gt_5.zip` | `…id=1mL44YJHwiLt_ZRdjmiU7-_i4QVtWURLD` | **24,987,135** | `278eb1e42c73` |
| `PredictorAltPorts_LiqScreen_ME_gt_NYSE20pct.zip` | `…id=1Q4YatQ3soRU_V7VeACwUn2bnCnmhDUI2` | **24,381,719** | `7fce9ca3fe1a` |
| **`PlaceboPortsFull.zip`** (new to this campaign) | `…id=1ciopYrT7e9tzKCt8f1he6uwJFiaD1ZkE` | 10,732,490 | `ed0717be8c52` |
| **`PredictorAltPorts_QuintilesEW.zip`** (new) | `…id=1KjptjrRi96ko_tR8zFjXCyYfNlyiHGiI` | 18,290,738 | `4d9f4dfd4828` |
| **`PredictorAltPorts_QuintilesVW.zip`** (new) | `…id=1ef905SSlCDyh1KU9W1tJs5sfBFz0HPUt` | 18,947,238 | `12fb2eaa34c6` |
| `SignalDoc.csv` | `raw.githubusercontent.com/OpenSourceAP/CrossSection/master/SignalDoc.csv` | 181,712 | `7f7314947e45` |
| `F-F_Research_Data_5_Factors_2x3_CSV.zip` | `mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/…` | 11,948 | `c9218d2ab2ff` |
| **`25_Portfolios_ME_OP_5x5_CSV.zip`** (§6.4) | same host | 384,080 | `edf2c758af20` |
| `Portfolios_Formed_on_OP_CSV.zip` (downloaded, unopened) | same host | 135,027 | `a889a239cee5` |
| `25_Portfolios_ME_INV_5x5_CSV.zip` (downloaded, unopened) | same host | 385,156 | `380d6f9b95e4` |
| CZ predictor source code (§3.3) | `raw.githubusercontent.com/OpenSourceAP/CrossSection/master/Signals/pyCode/Predictors/GP.py`, `.../CBOperProf.py`, `.../Placebos/GPlag.py` | — | — |

**The three files round 1's `A2` also pulled came back at byte counts identical to `A2`'s record
(3,293,172 / 24,987,135 / 24,381,719).** French's files announce themselves as built from the
**202607** CRSP database and run to **2026-07**. The Drive folder listing was obtained by decoding
`window['_DRIVE_ivd']` as JSON after `unicode_escape`; the three new files above were found that way
and **`PredictorAltPorts_QuintilesEW` is the first equal-weighted CZ portfolio set this campaign has
opened.**

**How to find the folder again:** `drive.google.com/drive/folders/1qQDuTsnyvWfEJR6nPBQZ8xxlq6bkLG_y`
→ `Portfolios` (`1c7iE6BDTkZW7JJvUgpdySJlB6FDtV-SX`) → `Full Sets Alt`
(`1RrKj_SjK4RGfuo6EFjCViEZ5Itv2rEFk`) and `Full Sets OP` (`1-UPjZuikxznx0Z-LaGHKDyCdws4R2GXf`). The
full 17-file listing of `Full Sets Alt` is in my fetch log and includes `DecilesEW`, `DecilesVW`,
`FF93style`, `LiqScreen_NYSEonly`, `LiqScreen_VWforce` — **none of which I opened (§11).**

### 8.2 Controls — negative first, because a harvest without one is not a measurement

| # | control | result | must be |
|---|---|---|---|
| `C1` | a signal name that cannot exist (`ThisSignalCannotExist`) in the CZ wide file | **0 columns** | 0 |
| `C2` | `SignalDoc.csv` rows with `Cat.Data == 'Telepathy'` | **0** | 0 |
| `C3` | a quintile portfolio's return minus itself, 1963–2024, all four signals, both screened files | **max abs = 0.0 exactly** | 0 |
| `C4` | French market series minus itself | **0.0** | 0 |
| `C5` | months before 1900 in `F-F_Research_Data_5_Factors_2x3` | **0** | 0 |
| `C6` | sum of the five quintiles' deviations from their own mean, every month, every signal | **max 1.8 × 10⁻¹⁴** | 0 to float precision |
| `C7` | a file that cannot exist on the French host (`NOSUCHFILE_negative_control.zip`) | **HTTP 404, 1,245 B `text/html`** | not a 200 shell |
| `C8` | a bogus Google-Drive id | **HTTP 404, 1,652 B** | not a 200 shell |
| `C10` | months before 1963-07 in the French 25-portfolio monthly blocks | **0** | 0 |
| `C11` | a column that cannot exist in the 25-portfolio file (`ME9 OP9`) | **absent**; 25 columns found, all named | absent |
| `C12` | `−99.99` / `−999` missing-code cells in either French monthly returns block | **0 of 18,925 cells each** | reported, not assumed |
| `C13` | sum of the five OP cells' deviations from their own size-row mean, every month, every row, both weightings | **max 2.1 × 10⁻¹⁴** | 0 to float precision |
| `C9+` | **positive** — my CZ in-sample `GP` long–short | **0.303 %/mo, `t` 2.39** | `SignalDoc` + `D7` + `R2-02`: **0.31, `t` 2.49** |
| | **positive** — my `GPlag` in-sample EW quintile long–short | **0.213, `t` 1.92** | `R2-02`'s read of CZ's appendix: **0.20, `t` 1.85** |
| | **positive** — my `GP` price>\$5 long–short 2010–2024 | **0.704, `t` 3.14** | round 1 `A2`: **0.70, `t` 3.14** (exact) |
| | **positive** — my 200-predictor median post-pub ÷ in-sample ratio | **0.42** | `D1c` via `D2`: a **58%** decline |
| | **positive** — French market mean 1963-07→2024-12 | **0.9505 %/mo** | a plausible US equity total return |

**The control that changed an answer was not on this list.** It was the decision to compute the long
leg against **two** benchmarks rather than one (§7.2). **A single-benchmark measurement here would
have shipped the wrong sign,** and nothing in the control table above would have caught it — because
both measurements are arithmetically correct.

**And the second thing that changed an answer was testing my own mechanism rather than filing it.**
§6.7 states a story about the deflator that `R2-02`'s identity makes almost irresistible, and the
correlation is **−0.106 / −0.294**. **Both corrections came from computing a second thing, not from
any assertion firing.**

### 8.3 One honest weakness in my panel method

My `B_panel_decay` block defines in-sample as `year ≤ SampleEndYear` and post-publication as
`year > Year`, both at **annual** granularity, with a floor of 60 in-sample and 24 post-publication
months; it drops signals whose in-sample mean is below 0.05 %/mo before forming ratios. **That is
cruder than `D1c`'s regression framework** and it is not a replication of it. That it lands on **0.42**
against `D1c`'s published 0.58 decline is a coincidence of construction as much as a validation, and
I would not claim more than *"a crude independent pipeline on a different dataset reproduces the
published magnitude."*

---

## 9. BLOCKS, LOGGED BY TOOL AND RESPONSE — NEVER BY HOST

- `WebFetch` GET `onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12365` → **HTTP 403 Forbidden, body
  not retrieved.** This is why `D1c` is `[NOT OPENED]`.
- `urllib` GET `papers.ssrn.com/sol3/papers.cfm?abstract_id=2156623` → **HTTP 403, 5,658 bytes,
  `text/html`, body begins `<!DOCTYPE html><html lang="en-US"><head><title>Just a moment...`** — a
  Cloudflare interstitial. SSRN was the only route to `D6`'s and Novy-Marx & Velikov's pages too.
- `urllib` GET `arxiv.org/pdf/2512.11913` → **HTTP 200, `application/pdf` not returned; body begins
  `<!DOCTYPE html>`**, and `pypdf` reports `invalid pdf header: b'<!DOC'` / `EOF marker not found`.
  **A `.pdf` URL served as HTML — the flavour `B3` logged in round 2, seen again.** I abandoned that
  paper (*Not All Factors Crowd Equally*, §11).
- `urllib` GET `mysimon.rochester.edu/novy-marx/research/cr.html` → **HTTP 200, but the document is a
  Word-export HTML whose content is a Joshua Rauh paper, not the "Consulting Relationships"
  disclosure the link promises.** A new-ish flavour for the catalogue: **a correctly-named link at 200
  serving a different author's document.** I did not need it — `D6`'s NBER title page carries the
  disclosure verbatim and is better evidence.
- `urllib` GET `raw.githubusercontent.com/.../utils/saveplacebo.py` → **HTTP 200, 2,477 bytes, and the
  file contains no portfolio-construction code at all** — it only writes signal values. This is why
  §3.3's weighting had to be established empirically rather than read.
- **A NON-BLOCK I ALMOST LOGGED AS ONE.** EDGAR full-text search for the exact phrase
  `"Dimensional US High Profitability ETF"` in `N-CSR` returned high-ranked hits from **Lincoln Funds
  Trust** and **Lincoln Bain Capital Total Credit Fund** — which looked exactly like a search API
  silently dropping phrase quoting. **I fetched one and grepped it: it contains "High Profitability"
  once.** The phrase matching was honoured; the *ranking* was just unhelpful. **Relevance ranking is
  not relevance, and I checked before writing it down.**
- `urllib` GET `sec.gov/cgi-bin/browse-edgar?...&output=atom` → HTTP 200 in **17.8 s** on one call
  and 0.3–2 s on others. Slow, not blocked.
- **No tool was blocked by SEC and no 429 was earned.** Roughly 40 SEC requests at 0.35–0.50 s,
  single-threaded, plus ~25 elsewhere. Total download ~500 MB, dominated by four N-CSR documents of
  31–122 MB each.

---

## 10. WHAT I COULD NOT VERIFY, STATED PLAINLY

1. **McLean & Pontiff (2016) itself.** I read two drafts in full and **never opened the published
   article.** Its 97 / 26% / 58% figures reach this brief through a search summariser and through
   `D2`'s verbatim restatement. **Given §2.1 — where the draft figures are 82 / 10% / 35% and the
   draft calls the out-of-sample decay insignificant — the published numbers are the single most
   load-bearing unopened figures in this brief.** Nothing in §3–§8 depends on them; §2.1's comparison
   does.
2. **Novy-Marx & Medhat's Internet Appendix Table D1.** Same gap as `R2-02` §10, and I tried the
   route the mandate prescribes: the author's own page links only to SSRN, which is Cloudflare-blocked.
   The NBER PDF **describes** D1 and does not **contain** it. **"Even stronger results in the late
   period" is their prose, not their numbers.** The sub-period split for profitability post-2000
   remains unobtained by this campaign.
3. **Whether Jacobs & Müller's published JFE version changed its numbers.** I read the **January
   2017, 231-anomaly** working paper in full; the published 2020 version has **241**. The count moved.
   **I did not establish whether the 36% / 60% / 65% estimates moved with it.**
4. **The price distribution of the names carrying this effect — by anyone, including me.** CZ's
   portfolio files have no price field; French's have market cap and no price. **The `price > $5`
   screened file proves survival under the screen and nothing about position within the surviving
   price distribution.** `R2-02` §7's negative stands and I extended it to the public portfolio data
   without repairing it.
5. **When and how MSCI's Quality index history was spliced.** `P3` says *"(Spliced)"* and I did not
   chase it. QUAL's ten-year benchmark comparison may therefore contain the same contamination that
   `P1` disclosed for XMHQ — **and if it does, QUAL's −87 bp/yr is measured against a moving target.**
6. **OQAL's inception date.** I established its merger (`P6`, vote 2019-04-12) and its liquidation
   (`P5`, payment ~2020-02-26) from filings. **The launch date is not established from any filing
   here**, so "it lived about two years" is an inference, not a measurement.
7. **How many profitability or quality funds have died.** I found **one**, from a search, and then
   confirmed it in filings. **I did not run a systematic census of liquidations, and every return in
   §5 is therefore from a survivorship-biased sample.** A census would need Form 25-NSE / N-8F /
   497-supplement sweeps across issuers and I did not do it.
8. **The comparability of `GPlag` to `GP`.** Three differences, not one (§3.3). The deflator
   increment of +0.149 %/mo post-publication is an upper bound on the deflator's own contribution
   because `sale`-vs-`revt` and the inclusion of financials both load on it.
9. **Whether `D3`'s "Ave. Spread Paid" is the same quantity as this programme's 33.8 bp/side.** The
   68-vs-67.6 coincidence is striking and **unverified**; their own decomposition does not close
   arithmetically (41% × 68 = 28 against a reported 24).
10. **Anything about this programme's fixture.** I have no access to it. §7.4's statement that the
    fixture is wholly post-sample rests on the dates in `R3-00-slate.md` and `D7`, not on the data.
11. **Whether the 2005–2009 flat block in §4.3 is the same phenomenon as the 1970s blocks.** I report
    that three pre-publication blocks are at or below zero. **I did not test whether they share a
    mechanism, and "no break at 2013" is a statement about the absence of a visible break, not a
    fitted structural-break test.**
12. **Falck–Rej–Thesmar's regression tables.** I read the abstract and §1 verbatim and took the 30% /
    5pp / 15% figures from the authors' own prose. **I did not open their tables**, so I cannot say
    which specification those numbers come from.
13. **Wahal (2019) itself.** `D8` is established to **abstract level only**, from ASU's repository and
    the author's own site. I did not obtain the article, so **I cannot say how the pre-1963
    profitability premium was measured** — which profitability definition, what deflator, what
    weighting, or its magnitude and `t`. **§6.5's argument rests on a claim of robustness whose
    construction I have not seen**, and for a lane whose central finding is that the construction
    decides the answer, that is the weakest load-bearing source here.
14. **Whether §6.4's size pattern holds for gross profitability.** French publishes no gross-profit
    sorts. My §6.4 is the FF `/BE` definition; my §6.3 is `GP/AT`; **I do not have a size × gross
    profitability double sort from any public source, and CZ's EW-vs-VW contrast is a blunt instrument
    for it** (§6.3's `t`s never clear 1.0). **The size-conditional decay of gross profitability
    specifically remains unmeasured by me and, as far as I found, by anyone.**
15. **Why the French small-cap HiOP cell fell from 300 to 81 firms.** I measured the fall from the
    file's own `Number of Firms` block. **I did not establish whether it is the shrinking US listed
    universe, a breakpoint effect, a book-equity availability effect, or the `OP` denominator
    requiring positive book equity.** It bears directly on the breadth of any small-cap sleeve and I
    left it unexplained.

---

## 11. WHAT I DID NOT OPEN — separate from the above, so the unexplored edge is visible

1. **Linnainmaa & Roberts (2018 RFS), *The History of the Cross-Section of Stock Returns*.** Cited by
   `D2` as showing anomalies decline *before* the original samples begin — **the pre-sample mirror of
   post-publication decay, and the single most relevant artefact-camp test I did not read.**
2. **Wahal (2019)'s full text.** Now established to abstract level as `D8` and used in §6.5, but the
   **article itself is still unread** — I tried ASU's repository (abstract only), the author's own
   site (links to no PDF) and SSRN (Cloudflare). **It remains the highest-value single document left
   unread in this lane**, because it is the pre-discovery out-of-sample test of this exact family and
   I cannot see its construction.
3. **Chordia, Subrahmanyam & Tong (2014, JAE), *Have capital market anomalies attenuated…*.** The
   era-not-publication paper, cited by both `D2` and `D4`. Not opened.
4. **Jensen, Kelly & Pedersen (2023 JF), *Is There a Replication Crisis in Finance?*** — its
   post-publication analysis. `R2-02` read it partially and found its profitability numbers live in
   bar charts; I did not open it at all.
5. **Pénasse, *Understanding Alpha Decay***. Identified as a likely third framing of the dispute;
   never fetched.
6. **Harvey, Liu & Zhu (2016), *…and the Cross-Section of Expected Returns*** — the t>3.0 hurdle
   paper. Known through `D2`'s critique of it only.
7. **Green, Hand & Zhang (2017 RFS).** Cited by `D4` for the post-2003 decline. Not opened.
8. **Chen (2021), *The Limits of p-Hacking*** and **Chen & Zimmermann (2020 RAPS)**. Known only
   through `D2`'s summaries of them.
9. **Detzel, Novy-Marx & Velikov (2023 JF), *Model comparison with transaction costs*** — still
   paywalled, still not opened, as in `R2-02`.
10. **Novy-Marx & Velikov, *Assaying Anomalies* (SSRN 4338007)** — and, newly found and **not
    opened**, its **companion website and its `AssayingAnomalies` GitHub reference implementation**,
    both linked from Novy-Marx's page. **The protocol is said to include era and post-publication
    analysis, and a reference implementation is exactly the route the depth mandate prescribes.**
    This is the largest unexploited lead I am leaving.
11. **`Not All Factors Crowd Equally: Modeling, Measuring, and Trading on Alpha Decay`** (arXiv
    2512.11913, Dec 2025). Fetch returned HTML, not PDF (§9); abandoned. **Unrefereed preprint —
    would need `[UNVERIFIED]` treatment.**
12. **Chen & Velikov's internet appendix and their anomaly-level trading-cost dataset.** Their
    per-anomaly net returns are not in the article. **The gross-profitability row of their 204 is
    therefore unknown to me.**
13. **CZ's other eleven alt-port sets**, listed in §8.1: `DecilesEW`, `DecilesVW`, `Deciles`,
    `FF93style`, `LiqScreen_NYSEonly`, `LiqScreen_VWforce`, `Quintiles`, `HoldPer_1/3/6/12`, and
    **`DailyPortfolios/Predictor.zip` (232 MB)**. The decile versions would sharpen every leg number
    in §3.2; the hold-period versions would price the rebalancing-frequency question directly.
14. ~~French's 25 Size × OP table.~~ **DONE — it was the item I flagged as "bytes I had and a
    measurement I did not make", and making it produced §6.4, which is the second-largest finding in
    this brief.** What remains unopened *in that file*: the two **annual** returns blocks, the
    `Average Market Cap`, `BE/ME`, `OP` and `investment` characteristic blocks — all of which would
    let me characterise the cells rather than only their returns.
15. **`Portfolios_Formed_on_OP_CSV.zip`** (univariate OP deciles, 135,027 B) **and
    `25_Portfolios_ME_INV_5x5_CSV.zip`** (385,156 B, French's investment sort) — both downloaded,
    neither opened. **I wrote that the second was the one I most regretted because it would test
    whether the `GP/AT` deflator's 15 bp/month is the asset-growth leg — then realised I could run
    that test on data already in hand, and did (§6.7). French's `ME × INV` file would be the
    independent confirmation of §6.7's negative result and remains unopened.**
16. **The DFA, AQR and GMO fund families beyond DUHP.** `DUSQX`, `DFVEX`, AQR's QMJ data library,
    GMO Quality (live since 2004 — **the longest potentially-relevant record in existence**). None
    opened. AQR's QMJ series in particular would give a 1957-to-present profitability-adjacent factor
    from a third, interested, source.
17. **Vanguard `VFQY` (2018) and JPMorgan `JQUA` (2017)** — two more live quality tilts whose filed
    reports I did not pull.
18. **Any non-US evidence of my own.** `D4` is the only international source here and I measured
    nothing outside the US.

---

## 12. WHAT THIS BRIEF DOES NOT CLAIM

**Nothing here is admitted, closed, or elevated.** Both books are unchanged. **I have made no claim
about the programme's fixture**, and the single most important caveat on every number in §3, §4.3 and
§6 is that **Chen–Zimmermann's universe is not this programme's universe**: different name count,
different screens, no dollar-volume filter, a benchmark that is the sort's own universe rather than
cash, and `t`-statistics computed as if 700 names in a quintile were independent when this programme's
own effective breadth is **~10**. **A `t` of 3.00 on CZ's panel is not a `t` of 3.00 on this
programme's.** The honest summary of the lane is in §0: **the family did not decay, the part that grew
is the part this programme cannot trade, and the live funds disagree with the backtests in exactly the
segment where the money is largest.**
