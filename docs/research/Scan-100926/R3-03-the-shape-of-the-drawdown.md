# R3-03 — The shape of the drawdown of a long-only characteristic tilt

**Round 3 of `Scan-100926`.** Lane `C3` of four. Contract, inherited exclusions and the rules this
lane carries: [`00-SCHEMA.md`](00-SCHEMA.md). Slate: [`R3-00-slate.md`](R3-00-slate.md).
**External literature and public-data research only.** Nothing here touches the programme's private
fixture and nothing here is claimed about it.

Under [R15](../../RULES.md#r15) this brief closes and admits nothing. Both books are unchanged.

**Evidence files this brief quotes** (per the campaign rule that a quoted file is evidence):
[`../../../data/C3_drawdown_measurement.txt`](../../../data/C3_drawdown_measurement.txt) — 600 lines,
the complete console output of every measurement below including every control — and
[`../../../data/C3_drawdown_runs.py`](../../../data/C3_drawdown_runs.py) — the 1,010 lines of code
that produced it, re-runnable against the named public endpoint.

---

## 0. THE SEVEN THINGS THIS LANE FOUND

**1. THE BAR'S SECOND OUTCOME IS THE TRUE ONE, AND IT IS SHARPER THAN THE SLATE EXPECTED. Two
sources do report something called "the long leg's drawdown". Neither of them reports the drawdown
of a long-only portfolio.** Blitz, Baltussen & van Vliet (FAJ 2020) Table A5 reports a long-leg
maximum drawdown of **−10.5%** — and the same table reports that object's volatility as **2.2%** and
its market beta as **−0.02**, because the paper's own note says each leg is *"an equal 50/50
combination of the large-cap and small-cap portions, **minus the market** (50/50 Big/Small
portfolios), to neutralize market and size tilts"* [read in full, §2.1]. Novy-Marx's *Quality
Investing* Table 9 reports maximum drawdowns of **−18.9% to −55.4%** for genuinely long-only
strategies — but its own column header says **"% cumulative underperformance"**, i.e. the drawdown of
the strategy *relative to the Russell 1000/2000* [read in full, §2.2]. **A cash-funded book cannot
spend either number.** The absolute, cash-benchmarked drawdown of a long-only characteristic tilt is
**not in the literature I could reach**, so I measured it: **−52.2% value-weighted and −63.6%
equal-weighted**, 1963-07→2026-07 (§4).

**2. THE TILT'S DRAWDOWN IS THE MARKET'S DRAWDOWN, MEASURED SIX WAYS.** Correlation of the drawdown
*paths*: **0.79** (VW tilt vs VW market), **0.92** (EW tilt vs EW universe), and **0.79 to 0.98 for
every one of the ten OP deciles** without exception. At the VW tilt's own worst trough (1974-09) the
market was already **−46.5%** down, so the tilt-specific excess hole was **−5.7 pp** of a −52.2%
drawdown. The tilt does not change the drawdown. It decorates it — and in equal weighting it
decorates it **worse**, not better (§7, Table 19).

**3. THE HIGH-PROFITABILITY DECILE IS THE WORST LONG-ONLY DECILE IN THE SORT EXCEPT FOR THE JUNK
DECILE — on drawdown, on volatility, on beta, and on excess return.** Equal-weighted, 1963–2026:
decile 10 has maxDD **−63.63%**, vol **21.25%**, beta **1.21**, and beats the equal-weighted universe
by **+0.026 %/mo** — while deciles 2 through 9 all have shallower drawdowns, lower betas, **and larger
excess returns** (+0.048 to +0.086 %/mo). Decile 5 beats the universe by nearly three times as much as
decile 10 and does it at beta 1.00. Value-weighted, decile 8 dominates decile 10 on every axis
(maxDD −42.0% vs −52.2%, excess +0.128 vs +0.092 %/mo). **The drawdown is worst exactly where the
characteristic is strongest.** `[MEASURED IN BRIEF]` §7.

**4. THE DIVERSIFICATION DOES NOT SURVIVE, AND IT WAS NEVER IN THE LONG LEG TO BEGIN WITH.** The
equal-weighted tilt's market beta rises from **1.21** (all months) to **1.60** (worst 5% of market
months) to **1.66** (worst 20 months), and its excess over its own equal-weighted benchmark in the
worst 5% of market months is **−0.70 %/mo**. Inside the market's six worst drawdown *episodes* its
beta is 1.09–1.57 and it lost more than the market in **five of six**. Meanwhile `RMW` — the
market-neutral spread — beat the market by **+23 to +118 pp** inside every one of those same six
episodes at a beta of −0.61 to +0.05. Asness, Frazzini & Pedersen's documented "flight to quality" is
real and large; **all of it lives in the leg this programme cannot hold** (§6).

**5. PROFITABILITY'S WORST EPISODES ARE NOT VALUE'S. They are closer to opposite, with one shared
catastrophe.** Correlation of the drawdown paths, `RMW` vs `HML`: **−0.142**. The shared catastrophe is
1998-09→2000-02 (`RMW` −51.2%, `HML` −48.8% cumulative). Outside it they diverge: over `HML`'s worst
drawdown (2007-01→2020-09, 165 months, −79.1% cumulative) `RMW` earned **+44.2%**; in the GFC `RMW`
was **+25.9%** while the value decile was **−67.5%**. Novy-Marx & Medhat (NBER w33601, 2025) put a
number on the mechanism: `HML`'s late-sample loading on their profitability factor is **−0.57**, a
**35 bp/month drag** [read in full] (§5).

**6. FOR A CASH-BENCHMARKED BOOK THE TILT'S OWN CONTRIBUTION NEEDS 114 YEARS TO REACH `t = 2`, AND
IN EQUAL WEIGHTING OVER A THOUSAND.** Measured information ratios, 1963-07→2026-07: VW tilt minus the
VW market **IR 0.187 → 114 years**; EW tilt minus the EW universe **IR 0.057 → 1,235 years**; small-cap
high-OP minus the EW universe **IR 0.042 → 2,318 years**. Over the realised 63 years the EW tilt's
excess over its own benchmark reached **`t` = 0.45**. The 15–18 years that the tilt's *total* Sharpe
needs is the **equity risk premium's** horizon, not the tilt's (§8). Empirically, the EW tilt beat the
EW universe in **52.8% of overlapping ten-year windows** — a coin flip at a decade.

**7. AND A COST DRAG OF 0.5 %/YEAR ERASES THE WHOLE EQUAL-WEIGHTED TILT.** Charging Novy-Marx's own
large-cap cost estimate of 0.5 %/yr takes the EW tilt's excess over the EW universe from **+0.026 to
−0.015 %/mo**; at his small-cap estimate of 1.5 %/yr it is **−0.099 %/mo** and the maximum drawdown
deepens to **−66.9%** with 112 months underwater (§9.2). **This is gross-of-cost arithmetic on free
public data and it is not a statement about this programme's costs** — but the margin being erased is
4 bp/month, and that is a small number to defend.

**Two further results that were not commissioned** and that I reached after the bar was met:
**(a)** the realised maximum drawdowns of all of these objects sit at the **32nd to 50th percentile** of
a 24-month block-bootstrap null — i.e. **the drawdown depth carries no information beyond mean, vol
and serial dependence**, and two published papers independently reach the same conclusion by the same
route (§9.1); **(b)** **mean drawdown is a Sharpe statistic, not a leg statistic** — across nine series
`corr(Sharpe, mean drawdown) = 0.900` — which dissolves an apparent conflict between CFM and Blitz
that would otherwise have had to be recorded as unresolved (§10.1).

---

## 1. SOURCES, BY TYPE AND BY HOW WELL ESTABLISHED

Every figure below is tagged in the same sentence as the number taken from it.

| # | source | type | established | interest |
|---|---|---|---|---|
| **S1** | **Van Hemert, Ganz, Harvey, Rattray, Sanchez Martin & Yawitch, *Drawdowns*, Journal of Portfolio Management 46(8), Sept 2020, 34–50** | [PEER-REVIEWED] (JPM is a refereed practitioner journal) | **[read in full]** — the **published** PDF, 17 pp, from **Harvey's own Duke page**; extracted locally with `pdftotext -layout`; Exhibits 1–3 and Appendices A–B read off the layout extraction | **Four of six authors are Man AHL / Man Group; Harvey is "an advisor to Man Group"** per the paper's own byline. Man sells long-short and trend — **interested against long-only** |
| **S2** | **Blitz, Baltussen & van Vliet, *When Equity Factors Drop Their Shorts*, Financial Analysts Journal 76(4) 2020, 73–99** | [PEER-REVIEWED] | **[read in full, BOTH VERSIONS]** — (a) the **published** open-access copy from the **Erasmus institutional repository** `repub.eur.nl/pub/130144`, 1,622 extracted lines; (b) the **10 Dec 2019 Robeco-hosted working draft**, 1,040 lines. **Round 1's `A3` was refused this paper's full text; the institutional repository is the route that worked** | **All three authors are Robeco Quantitative Investments, which sells long-only factor funds — interested, and the direction of its interest is toward a mild long-leg drawdown** |
| **S3** | **Novy-Marx, *Quality Investing*** (undated working paper; sample ends Dec 2013) | [WORKING PAPER] | **[read in full]** — 37 pp from `mysimon.rochester.edu/novy-marx/research/QDoVI.pdf`; Tables 6, 7, 9, the "Long-only investors" section and the conclusion read off the layout extraction | **Novy-Marx "provides consulting services to Dimensional Fund Advisors"** (stated on S9's cover). Dimensional sells long-only profitability-tilted funds — **interested** |
| **S4** | **Novy-Marx, *The Other Side of Value: The Gross Profitability Premium*, June 2012 draft** (published JFE 108(1) 2013, 1–28) | [WORKING PAPER] for the text read | **[read in full]** — `OSoV.pdf` from the same host. **Contains ZERO instances of "drawdown"** | as S3 |
| **S5** | **Asness, Frazzini & Pedersen, *Quality minus junk*, Review of Accounting Studies 24(1) 2019, 34–112** | [PEER-REVIEWED] | **[read in full, BOTH VERSIONS]** — the **published** Springer PDF (31 pp of journal body) and the **9 Oct 2013 draft**. **BOTH contain ZERO instances of "drawdown"** | **All three authors AQR — interested.** AQR sells both long-only and long-short |
| **S6** | **Arnott, Harvey, Kalesnik & Linnainmaa, *Reports of Value's Death May Be Greatly Exaggerated*, Financial Analysts Journal 77(1) 2021, 44–67** | [PEER-REVIEWED], open access under Creative Commons | **[read in full]** — published PDF from Harvey's Duke page; Table 2, the bootstrap section and the "Is this time different?" section read off the extraction | **Arnott and Kalesnik are Research Affiliates, which sells value and fundamental-index products — interested**, and the paper's conclusion is the one a value manager wants |
| **S7** | **Arnott, Harvey, Kalesnik & Linnainmaa, *Alice's Adventures in Factorland: Three Blunders That Plague Factor Investing*, Journal of Portfolio Management 45(4), April 2019** | [PEER-REVIEWED] (refereed practitioner journal) | **[read in full]** — published PDF from Harvey's Duke page; Exhibits 9–12 and the accompanying prose | as S6. **Its conclusion cuts against factor products generally**, which makes its negative findings conservative-direction |
| **S8** | **Benaych-Georges, Bouchaud & Ciliberti, *Equity Factors: To Short Or Not To Short, That Is The Question*, arXiv 2003.10419v3, 7 Apr 2021** | [WORKING PAPER], unrefereed | **[read in full]** — downloaded and extracted **myself**; Table 1 and the Figure 8 caption verified independently of round 1's reading of the same paper | **Capital Fund Management — a long-short shop, interested AGAINST long-only**, which makes its pro-long-short numbers the conservative direction for its own claim |
| **S9** | **Novy-Marx & Medhat, *Profitability Retrospective: What Have We Learned?*, NBER w33601, March 2025** | [WORKING PAPER] — and **NBER's own cover states it has "not been peer-reviewed"** | **[read in full]** — §4.2 and the surrounding sections | **Novy-Marx consults for Dimensional; Medhat "is a listed employee of Dimensional Investment LLC"** — both stated on the paper's own cover page. **Interested**, and the paper reports profitability *outperforming* post-publication |
| **S10** | **Hou, Xue & Zhang, *Digesting Anomalies: An Investment Approach*, Review of Financial Studies 28(3) 2015, 650–705** | [PEER-REVIEWED] | **[obtained and text-searched, NOT read in full]** — from `global-q.org`; title line verified. **Contains ZERO instances of "drawdown"**; its eight price-term hits are all `1/P` as an *anomaly variable*, never a screen | — |
| **S11** | **Ang & Chen, *Asymmetric correlations of equity portfolios*, JFE 63(3) 2002, 443–494** | [PEER-REVIEWED] | **[WEAKER THAN SNIPPET ONLY]** — **I never obtained this paper.** Everything I have about it arrived through a **search summariser**, so per the campaign's summariser rule it is weaker than `[snippet only]` and **I use it for nothing** (§12, §13.5) | — |
| **S12** | **My own measurement on Ken French's data library** | `[MEASURED IN BRIEF]` | endpoint, construction, positive controls and negative controls all stated in §3 | mine |

**Restated, not re-established.** Where I quote round 1's or round 2's readings I say so and attribute
to them: `A3`'s reading of Israel & Moskowitz (JFE 2013) and of Chen & Welch, and `B2`'s reading of
Ball, Gerakos, Linck & Nikolaev (2016). **I did not re-open those papers** (§14).

**No vendor factsheet, brochure, index factsheet or fund marketing document is used as evidence for
any return or any risk figure anywhere in this brief.** Two were encountered and both are named and
rejected in §12.

---

## 2. SUB-QUESTION 4, TAKEN FIRST, BECAUSE IT REFRAMES EVERY OTHER ANSWER

**"Does any source report drawdown for the long leg alone rather than for the spread?"**

**Two do, by name. Both report a benchmark-relative object, and neither reports what a cash-funded
book experiences. That is the finding, and it is stronger than either branch of the bar.**

### 2.1 `S2` — Blitz, Baltussen & van Vliet: a "long leg" maximum drawdown of −10.5%, for an object with 2.2% volatility and a beta of −0.02

**Table A5, "Downside Risk Perspectives, July 1963–December 2018"**, read in full from the published
open-access copy:

| | Long Leg | Short Leg | Long–Short |
|---|---|---|---|
| Volatility | **2.2%** | 3.7% | 5.7% |
| Skewness | −0.1 | −0.3 | −0.2 |
| Excess kurtosis | 7.0 | 10.1 | 8.9 |
| Semi-deviation | 1.3% | 2.4% | 3.5% |
| VaR (95%) | −2.7% | −4.9% | −7.3% |
| **Maximum drawdown** | **−10.5%** | **−15.5%** | **−24.2%** |
| Regular beta | **−0.02** | −0.08 | −0.11 |
| LPM(0) beta | −0.02 | −0.06 | −0.08 |
| LPM(1σ) beta | −0.01 | −0.03 | −0.04 |
| Sharpe ratio | 1.10 | 0.69 | 0.86 |
| Sortino ratio | 1.88 | 1.07 | 1.39 |

**Three things settle what the object is, and all three are the paper's own.**

1. **The note to Table 1 says it verbatim:** *"All factors are market neutral. In Panels A and B, each
   leg is an equal 50/50 combination of the large-cap and small-cap portions, **minus the market**
   (50/50 Big/Small portfolios), to neutralize market and size tilts. Panel C is the sum of Panels A
   and B and the classical way of presenting long-short factors."*
2. **The beta row says it numerically:** regular beta **−0.02**.
3. **The volatility row says it arithmetically:** **2.2%**. Table 1's long–short factor volatilities
   in the same units are 9.7 / 14.5 / 7.5 / 6.9 / 11.0 %, so these are annualised — and **no long-only
   equity portfolio has 2.2% annualised volatility.**

**Table 1, Panel A, "Long leg of factors", July 1963–December 2018, read in full — the row that makes
the point beyond argument:**

| | HML | WML | **RMW** | CMA | VOL | **All** |
|---|---|---|---|---|---|---|
| Return (%) | 2.1 | 3.6 | **1.0** | 1.6 | 3.7 | **2.4** |
| Volatility (%) | 5.3 | 5.9 | **3.3** | 3.2 | 6.9 | **2.2** |
| Sharpe ratio | 0.40 | 0.61 | **0.31** | 0.49 | 0.53 | **1.10** |

**The PROFITABILITY long leg specifically — the one this programme's candidate family would build — is
an object with a 1.0% annual return and a 3.3% annual volatility.** Its Sharpe of 0.31 is the *lowest*
of the five long legs in the paper. **These are not the numbers of a long-only equity portfolio and the
−10.5% drawdown is not a long-only equity portfolio's drawdown.** The combined long leg at 2.4% / 2.2%
/ 1.10 is internally consistent with Table A5 and is emphatically not an equity portfolio either.

**So `S2`'s −10.5% is the maximum drawdown of a market-neutral, size-neutral, five-factor-combined,
gross-of-cost long leg.** The long-only tilt I measure over almost the same span has a maximum
drawdown of **−52.2%** value-weighted and **−63.6%** equal-weighted. **The factor of difference is 5 to
6×**, and a programme that read −10.5% as "the long leg's drawdown" would have been reasoning from a
number about an object it cannot hold.

**The main text's use of the figure, quoted so the reader can see what claim it supports:**
*"we examined tail risk, measured in terms of cumulative drawdowns, of the long and short legs over
time. Figure A4 shows that the long legs exhibited a consistently lower drawdown risk than the short
legs. The short legs were often twice as risky as the long legs and experienced significantly deeper
drawdowns… In summary, a downside risk perspective seems unlikely to explain the finding that the
long side of factors dominates the short side."* **The claim the drawdown figure supports is
long-leg-versus-short-leg, which is a correct use of it. The misuse would be mine if I read it as
long-only-versus-cash, and I do not.**

**DRAFT VERSUS PUBLISHED, CHECKED AND RECORDED.** The 10 Dec 2019 Robeco draft's Table 5 carries the
**identical** drawdown row (−10.5% / −15.5% / −24.2%) and identical volatilities, skewness, kurtosis,
semi-deviation, VaR and all four return/risk ratios. **One difference:** the draft reports
`LPM beta (1 sigma)` −0.02 and `LPM beta (2 sigma)` −0.01, whereas the published table reports
`Regular beta` −0.02, `LPM (0) beta` −0.02 and `LPM (1 sigma) beta` −0.01. **The published version
added the plain market beta row that makes the market-neutrality visible in the table itself.** No
sign flipped and no figure moved; the change runs toward disclosure. **Recorded, not resolved beyond
that.**

### 2.2 `S3` — Novy-Marx's *Quality Investing*: long-only drawdowns, but measured as cumulative underperformance

This is the only source I found that reports maximum drawdowns for portfolios that are unambiguously
**long-only**. Sample **July 1963 → December 2013**, **net of estimated transaction costs** computed
via the Hasbrouck (2009) Gibbs effective-spread estimator as in Novy-Marx & Velikov (2014), with the
paper's own statement that *"Trading costs are typically modest, on the order of 0.5%/year for large
cap strategies and 1.5%/year for small cap strategies, because quality is highly persistent so
strategies based on quality turnover infrequently."*

**Table 9, read in full. The column header is the load-bearing part:
"Max. drawdown (% cumulative underperformance)".**

| strategy | large cap, growth of \$1 | large cap maxDD | 1-yr outperf. freq. | 5-yr outperf. freq. | small cap maxDD |
|---|---|---|---|---|---|
| Benchmark (R1000 / R2000) | 111 | — | — | — | — |
| Traditional value | 269 | **−43.0** | 55.7% | 67.5% | **−36.9** |
| Graham value | 218 | −43.9 | 58.8% | 62.3% | −37.1 |
| Grantham value | 226 | −34.8 | 57.1% | 66.8% | −38.1 |
| Magic formula | 364 | −29.8 | 69.0% | 75.3% | −48.6 |
| Sloan value | 196 | −41.2 | 58.9% | 57.4% | −27.5 |
| Piotroski and So | 335 | −37.7 | 60.8% | 71.2% | −40.6 |
| Cheap defensive | 187 | **−52.2** | 48.8% | 54.0% | **−55.4** |
| **Profitable value** | **595** | **−18.9** | **72.2%** | **81.3%** | **−28.3** |

And the figure note, verbatim: *"The second panel shows the value and joint value and quality
strategies' **drawdowns relative to the large cap universe** (i.e., cumulative under-performance
relative to the benchmark)."*

**So these are relative drawdowns.** They are the same *kind* of object as the relative drawdowns I
measure in §7.2 — and my value-weighted profitability decile's worst relative drawdown against the
VW market, **−29.3%**, sits between his traditional value (−43.0%) and his profitable value (−18.9%),
which is the right neighbourhood for a univariate single-characteristic sort against a different
benchmark. **What neither his table nor any other source I reached contains is the absolute number.**

**`S3` also contains the sentence that states sub-question 5's answer before I measured it**, and it
is the author of the profitability literature saying it: *"Most of a well diversified, long-only
equity investor's risk comes from the market, however, not from tracking error relative to the
market."* And the consequence he draws, which is the sharpest thing in the lane for a cash-benchmarked
book: *"Adding quality to a value strategy can thus improve the strategy's information ratio while
simultaneously reducing the strategy's Sharpe ratio."* His Table 7 discussion: *"The table shows the
difficulties long-only investors face exploiting quality's benefits. The table shows information
ratio gains, but Sharpe ratio losses."*

**And one caveat he raises against his own long-only results:** *"Much, and sometimes all, of the
observed quality strategy three-factor alpha in Table 2 came from negative loadings on the Fama and
French factors. In these cases the strategies do not raise expected returns, but simply provided an
attractive hedge for market investors with small cap and value tilts."*

**`S3`'s long-only level figures, for the record** (Table 6, long-only quality strategies, large cap,
1963-07→2013-12, net of estimated costs; columns are mean excess return, CAPM α, FF3 α, then the FF3
loadings, all in %/year with `t` in brackets):

| sort variable | E[Rᵉ] | CAPM α | FF3 α | β(MKT) | SMB | HML |
|---|---|---|---|---|---|---|
| Book-to-price | 8.70 [3.77] | 3.36 [3.15] | −0.72 [−1.34] | 1.01 [96.8] | 0.18 | 0.68 |
| Graham's G-score | 5.66 [2.61] | 0.03 [0.14] | 0.26 [1.34] | 0.98 [262.0] | −0.07 | −0.02 |
| Grantham's quality | 5.74 [2.67] | 0.25 [0.57] | 1.39 [4.02] | 0.94 | −0.12 | −0.16 |
| ROIC | 6.11 [2.65] | 0.26 [0.49] | 1.53 [3.32] | 0.98 | −0.08 | −0.20 |
| Earnings quality | 6.13 [2.57] | 0.22 [0.30] | 0.78 [1.06] | 1.00 | −0.02 | −0.10 |
| Piotroski's F-score | 6.22 [2.91] | 0.77 [1.74] | 1.34 [3.15] | 0.94 | −0.08 | −0.08 |
| Defensive | 5.21 [2.97] | 0.99 [1.44] | 0.14 [0.25] | 0.80 | −0.16 | 0.22 |
| **Gross profitability** | **7.10 [3.11]** | **1.44 [2.03]** | **2.74 [4.17]** | **0.94 [73.4]** | −0.06 | −0.22 |

**The long-only gross-profitability CAPM alpha is 1.44%/yr at `t` 2.03 — barely clearing — and its
market beta is 0.94.** His own summary: *"Only gross profitability's CAPM alphas is statistically
significant at the 5% level."* This is the same story round 2's `B2` reached from Ball et al.'s
monthly decile alphas (long-leg CAPM α `+0.14 [t 1.95]`), arriving by a different route.

### 2.3 The confirmed absences, censused rather than asserted

I grepped the extracted text of every document I obtained. **Counts of the string "drawdown",
case-insensitive:**

| source | "drawdown" hits | what the hits are |
|---|---|---|
| `S4` Novy-Marx, *The Other Side of Value* (the founding gross-profitability paper) | **0** | — |
| `S5` Asness, Frazzini & Pedersen, *Quality minus junk*, **2013 draft** | **0** | — |
| `S5` Asness, Frazzini & Pedersen, *Quality minus junk*, **published RAS 2019** | **0** | — |
| `S10` Hou, Xue & Zhang, *Digesting Anomalies* | **0** | — |
| `S9` Novy-Marx & Medhat, *Profitability Retrospective* (2025) | **1** | *"value's post-Great Recession drawdown"* — about value, not profitability |
| `S8` CFM | 2 | mean drawdown of a **hedged** long-only and a long–short book |
| `S2` Blitz et al. (published) | 5 | the **market-neutral** long leg, §2.1 |
| `S3` Novy-Marx, *Quality Investing* | 8 | **relative** drawdown, §2.2 |
| `S7` *Alice's Adventures in Factorland* | 33 | **long–short** factors scaled to 10% vol |
| `S6` *Reports of Value's Death* | 52 | **long–short** value vs growth |
| `S1` *Drawdowns* | 153 | a general probability model, asset-class agnostic |

**The canonical profitability paper, the canonical quality paper in both its draft and its published
form, and the canonical q-factor paper contain the word "drawdown" zero times between them.** The
statistic the programme's books are judged on is absent from the family's founding literature.

**And the price census, because size is not price.** Across the **ten** documents censused in the
table above, **zero** report the
nominal share-price distribution of the names carrying the effect and **zero** impose a price screen
on the profitability portfolios. `S10`'s eight price-term hits are `1/P` used as an anomaly variable
and `share price × shares` used to build market equity — never a screen. **This extends round 2's
`B2` finding from three papers to ten.** French's own portfolio files publish an *Average Firm Size*
block and no price block, so the public data does not supply it either.

---

## 3. MY MEASUREMENT: THE CONSTRUCTION, AND EVERY CONTROL ON IT

**`[MEASURED IN BRIEF]`. Endpoint:**
`https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/<file>_CSV.zip`, files
`Portfolios_Formed_on_OP`, `Portfolios_Formed_on_OP_Daily`, `Portfolios_Formed_on_BE-ME`,
`F-F_Research_Data_Factors`, `F-F_Research_Data_Factors_daily`, `F-F_Research_Data_5_Factors_2x3`,
`25_Portfolios_ME_OP_5x5`, `6_Portfolios_ME_OP_2x3`. Zip members dated **2026-09-02**; the OP file's
own header line reads **"This file was created using the 202607 CRSP database."** Monthly span
**196307–202607 (757 months)**; daily span **19630701–20260731 (15,876 days)**. Fetched with
`curl -A "Scan-100926-research/1.0 (research@backtest-framework.org)"`. Code and complete output in
`data/C3_drawdown_runs.py` and `data/C3_drawdown_measurement.txt`.

**WHAT THE CHARACTERISTIC IS, STATED PLAINLY BECAUSE IT IS A REAL LIMITATION.** French publishes
portfolios on **`OP`**, defined in the file's own header as *"operating profits (sales minus cost of
goods sold, minus selling, general, and administrative expenses, minus interest expense) divided by
book equity at the last fiscal year end of the prior calendar year"*, portfolios formed at the end of
June. **This is Fama–French operating profitability, not Novy-Marx gross profitability, and French
publishes no `GP` portfolios.** Round 2's `B2` established that the deflator and the definition matter
enormously — Ball et al.'s operating-profitability long leg has **no** market-adjusted alpha at all
(`+0.07`, `t 0.95`) while `CbOP`'s has `+0.14 [t 1.95]`. **So the characteristic I measure is, by
round 2's own evidence, the weakest member of the family on long-leg alpha.** §7's Table 19 shows why
this does not rescue the conclusion: *every* decile's drawdown path correlates 0.79–0.98 with the
benchmark's, so the drawdown conclusion is a property of long-only equity exposure, not of the sort
variable. **But I cannot and do not claim to have measured a gross-profitability tilt's drawdown.**

**Construction.** Monthly total returns in percent. A funded book's NAV is `cumprod(1 + r/100)` from
1.0 and its drawdown is `NAV / cummax(NAV) − 1`; a self-financing spread's NAV is built the same way
from the spread's monthly return, which is the convention `S6` uses and which I verify against their
published figure in §3.3. Distinct drawdown *episodes* are walked from each new high to the next
recovery to that same high, which gives peak date, trough date, depth, months-to-trough,
**months-from-trough-to-recovery**, and total months underwater, with unrecovered episodes flagged.
"Mean drawdown" is the time-average of the drawdown series — **`S8`'s own definition**, quoted in
§10.1. The equal-weighted universe benchmark is built from French's **Number of Firms** block as
`Σ nᵢ rᵢ / Σ nᵢ` across the ten deciles, so it is a true name-weighted universe rather than an
average of deciles.

### 3.1 Block proof — which stacked block I read, and its line range

French's portfolio files stack several blocks under one header. Every block in every file is
enumerated in the evidence file with its **line range, row count, date range, column count and title**.
The blocks I use:

| file | block title | lines | rows | span |
|---|---|---|---|---|
| `Portfolios_Formed_on_OP.csv` | `Average Value Weight Returns -- Monthly` | 26–782 | 757 | 196307–202607 |
| `Portfolios_Formed_on_OP.csv` | `Average Equal Weighted Returns -- Monthly` | 787–1543 | 757 | 196307–202607 |
| `Portfolios_Formed_on_OP.csv` | `Number of Firms in Portfolios` | 1680–2436 | 757 | 196307–202607 |
| `Portfolios_Formed_on_OP_Daily.csv` | `Average Value Weighted Returns -- Daily` | 24–15899 | 15,876 | 19630701–20260731 |
| `Portfolios_Formed_on_OP_Daily.csv` | `Average Equal Weighted Returns -- Daily` | 15904–31779 | 15,876 | 19630701–20260731 |
| `Portfolios_Formed_on_BE-ME.csv` | `Value Weight Returns -- Monthly` | 25–1225 | 1,201 | 192607–202607 |
| `25_Portfolios_ME_OP_5x5.csv` | `Average Equal Weighted Returns -- Monthly` | 785–1541 | 757 | 196307–202607 |

I did **not** use the *Annual*, *Average Firm Size*, *Average Market Cap* or *Value Weight Average of
OP* blocks except as controls. **The parser identifies a block by its own preceding title line, not by
position**, and the titles are printed beside the line ranges so the claim is checkable.

### 3.2 Negative controls — four of them

1. **A value that must return nothing returned nothing.** `Portfolios_Formed_on_ZZZNOTAFILE_CSV.zip`
   → **HTTP 404, 1,245 bytes, `text/html`**, not a zip, `unzip` refuses it. The endpoint does not
   fabricate.
2. **The sentinel census.** French states, in the OP file itself, *"Missing data are indicated by
   −99.99 or −999."* Every block of every file is censused for both values. **Result: the entire OP
   file, the OP daily file, both factor files, the 25-portfolio file and the 6-portfolio file contain
   ZERO sentinels.** The `BE-ME` file contains **43** instances of `−99.99` in each of its monthly VW
   and EW blocks — all in the pre-1963 era its deciles cannot fill — and **my BE-ME slice starts
   196307 and is asserted sentinel-free before use.** Round 2's lane flagged its empty `−99.99`
   bucket as its control; mine is not empty, and I say where the sentinels are.
3. **A series whose drawdown must be exactly zero.** Cumulative `RF`. **On the OP window
   (196307–202607) the maximum drawdown of cumulative `RF` is exactly `0.000000000000%` with zero
   episodes**, and `min(RF) = 0.0000%`. The machinery cannot invent a hole.
4. **And control 3 FIRED when I first ran it over the full 1926–2026 series — correctly.** It
   returned `−0.0899859958%` across 3 episodes. The cause is a **real property of French's data, not a
   bug**: `RF` has **twelve negative monthly values**, all pre-war —
   `193302 −0.03`, `193803 −0.01`, `193807 −0.01`, `193811 −0.06`, `193901 −0.01`, `193903 −0.01`,
   `193908 −0.01`, `194005 −0.02`, `194008 −0.01`, `194101 −0.01`, `194102 −0.01`, `194104 −0.01` —
   plus 98 exact zeros. **Cumulative `RF` is not monotone over the full French sample.** The control is
   therefore stated on the window actually used, where it holds exactly. **A control that had not
   fired would have taught me nothing; this one taught me a data property I did not know.**

### 3.3 Positive controls — one internal, two against PUBLISHED figures

**(a) Internal, against French's own arithmetic.** Compounding my monthly VW decile-10 returns by
calendar year and comparing to **French's own *Value Weight Returns — Annual* block**: 62 years
checked, **max absolute difference 0.0333 pp**. Compounding the **daily** VW decile-10 series to
monthly and comparing to French's **monthly** file: 757 months, mean difference **+0.0017 pp**, median
**+0.0015 pp**, **97.2% of months agree within 0.05 pp**, max **0.2563 pp** — the residual is the
expected difference between a daily-compounded portfolio and a monthly-held one, not an error. **If I
had read the wrong stacked block or mistaken percent for decimal, both checks would fail.**

**(b) Against `S1`'s published Exhibit 1 — four numbers, all four match.** Van Hemert et al.'s
baseline is normal iid monthly returns, a 10-year window, 10% annualised volatility and a 0.5
annualised Sharpe, and they publish *"It is 97.1%, 43.0%, 9.9%, and 1.5% for one, two, three, and four
sigma levels, respectively."* My own simulation, 200,000 paths:

| threshold | mine | published |
|---|---|---|
| P(maxDD ≤ −1σ = −10%) | **97.17%** | 97.1% |
| P(maxDD ≤ −2σ = −20%) | **43.07%** | 43.0% |
| P(maxDD ≤ −3σ = −30%) | **9.89%** | 9.9% |
| P(maxDD ≤ −4σ = −40%) | **1.53%** | 1.5% |

**(c) Against `S6`'s published drawdown AND its published bootstrap — three more numbers.** Arnott,
Harvey, Kalesnik & Linnainmaa report value's current drawdown as **−54.8%** from the 2006/12 peak to
2020/06, and report a block bootstrap (*"six-month blocks of actual long-short HML factor returns from
the live historical sample from July 1963 through December 2006"*, 57-year samples, 1 million draws)
whose *"median outcome was a −32.7% drawdown and… a −54.8% drawdown occurred in 2.3% of our
simulations."*

| | mine | published |
|---|---|---|
| French `HML` drawdown at 202006, running peak **200612** | **−54.59%** | −54.8% |
| median simulated maxDD, 6-month blocks, 196307–200612 pool, 684-month samples, B = 100,000 | **−32.49%** | −32.7% |
| P(simulated maxDD deeper than −54.8%) | **2.04%** | 2.3% |

**Seven published numbers reproduced across two independent papers, and the 2007-10-09 → 2009-03-09
market peak and trough dates fall out of the daily computation unprompted** (§9.3). The drawdown
machinery and the bootstrap are both externally validated before any new number is reported from them.

---

## 4. SUB-QUESTION 1 — DEPTH, DURATION, AND TIME TO RECOVERY

### 4.1 What the literature documents

**There is no source I reached that reports depth, duration and time-to-recovery together for a
long-only characteristic tilt measured against cash.** What exists, each with its object named:

| source | object | depth | duration | **time to recovery** |
|---|---|---|---|---|
| `S2` [read in full] | market-neutral, size-neutral, 5-factor **long leg**, 1963-07→2018-12 | **−10.5%** | Figure A4 is a plot; no table of lengths | **not reported** |
| `S2` | the same paper's **long–short** | −24.2% | — | **not reported** |
| `S3` [read in full] | **long-only** joint value+quality, large cap, **relative to R1000**, 1963-07→2013-12, net of costs | **−18.9%** (profitable value) to **−52.2%** (cheap defensive) | — | **not reported**; 1-year and 5-year **outperformance frequencies** are (72.2% / 81.3% for profitable value) |
| `S8` [read in full] | **hedged long-only**, 5 factors combined, global, 2000–2020, all costs charged, 6.4% realised vol | **mean** drawdown **−8.2%** | — | **not reported** |
| `S8` | the same paper's **long–short** | **mean** drawdown **−3.9%** | — | **not reported** |
| `S6` [read in full] | **long–short** value vs growth, 1963-07→2020-06 | **−54.8%** current, **−40.6%** at the tech-bubble bottom | **13 yrs 6 mos** current; 2 yrs 5 mos tech bubble | **the one explicit recovery figure in the literature I found**: large-cap value's back-to-back biotech+tech drawdown *"lasted 11 years and 10 months and left large-cap value investors more than 39.4% poorer than growth investors. This immense shortfall was recovered (requiring over 65% outperformance) in just 13 months."* |
| `S7` [read in full] | portfolios of **long–short** factors, all scaled to 10% vol, 1963-07→2018-06 | worst realised **−33.4%** (factors 1–6), **−42.9%** (factors 7–14), **−22.8%** (other) | *"often spanning multiple months"* | **not reported** |
| `S1` [read in full] | any series, as a probability model | the full distribution as a function of vol, window, Sharpe and autocorrelation | window is an input | **not reported as a statistic**; §3.3(b) gives the depth probabilities |

**Time to recovery is reported exactly once, by `S6`, for a long–short value spread.** The slate's
prediction that it would be "the one most often omitted" is confirmed: **it is omitted by seven of the
eight sources above.**

### 4.2 My measurement: full-sample drawdowns, 196307–202607, 757 months

Total returns, gross of costs. `p→t` = months peak to trough; `t→r` = months trough to recovery;
`UW` = total months underwater; `#DD>20%` = number of distinct episodes deeper than 20%.

| series | CAGR | vol | **maxDD** | peak | trough | recovery | p→t | **t→r** | UW | #DD>20% |
|---|---|---|---|---|---|---|---|---|---|---|
| VW market (total return) | 10.85% | 15.4% | **−50.31%** | 200710 | 200902 | 201202 | 16 | **36** | 52 | 7 |
| **EW all-name universe** | 12.66% | 20.3% | **−59.53%** | 200705 | 200902 | 201012 | 21 | **22** | 43 | 12 |
| **OP decile 10, VW — the long-only tilt** | 11.98% | 15.9% | **−52.22%** | 197212 | 197409 | 197808 | 21 | **47** | **68** | 6 |
| **OP decile 10, EW — the long-only tilt** | 12.77% | 21.2% | **−63.63%** | 196811 | 197412 | 197706 | 73 | **30** | **103** | 14 |
| OP top 30%, VW | 12.24% | 15.3% | −47.97% | 197212 | 197409 | 197807 | 21 | 46 | 67 | 7 |
| OP top 30%, EW | 13.43% | 19.8% | −59.99% | 196811 | 197412 | 197612 | 73 | 24 | 97 | 12 |
| OP decile 1, VW (junk, held long) | 7.20% | 22.8% | **−82.97%** | 200002 | 200902 | 202011 | 108 | **141** | **249** | 9 |
| OP decile 1, EW (junk, held long) | 9.54% | 27.2% | −69.32% | 202102 | 202310 | **NEVER** | 32 | — | 65 | 13 |
| **SMALL HiOP, EW** (small ∩ profitable) | 12.06% | 24.1% | **−74.13%** | 196812 | 197412 | 197803 | 72 | **39** | **111** | 16 |
| SMALL HiOP, VW | 11.88% | 23.6% | −74.43% | 196812 | 197412 | 197804 | 72 | 40 | 112 | 17 |
| BIG HiOP, VW | 11.63% | 15.1% | −48.54% | 197212 | 197409 | 197906 | 21 | 57 | 78 | 7 |
| **d10 − d1 spread, VW (long–short)** | 1.93% | 14.9% | **−61.34%** | 196506 | 198305 | 199010 | **215** | **89** | **304** | 7 |
| **d10 − d1 spread, EW (long–short)** | 0.49% | 14.4% | **−65.04%** | 199810 | 200002 | 202211 | 16 | **273** | **289** | 4 |
| `RMW` factor (FF 2×3) | 2.81% | 7.9% | −41.79% | 199808 | 200002 | 200107 | 18 | 17 | 35 | 4 |
| `HML` factor | 3.10% | 10.3% | −57.78% | 200612 | 202009 | **NEVER** | 165 | — | **235** | 4 |
| Value decile 10, VW (high BE/ME) | 14.49% | 21.7% | −69.81% | 200706 | 200902 | 201611 | 20 | **93** | 113 | 12 |

**Read the two shapes side by side, because they are not the same animal.**

- **The long-only tilt's drawdown is DEEP AND FAST.** −52.2% (VW) or −63.6% (EW); 16–21 months down in
  the market-crash episodes; 22–47 months to recover; 43–103 months underwater at worst. It is a
  market crash with a small tilt attached.
- **The long–short spread's drawdown is SHALLOWER PER YEAR AND ALMOST PERMANENT.** The VW spread's
  worst episode ran **215 months from peak to trough** and **304 months — 25 years 4 months —
  underwater**. The EW spread took **273 months to recover** from a 16-month fall.

**Time to recovery across ALL episodes deeper than 20%, which is the distribution the slate asked for
and which nothing in the literature supplies:**

| series | episodes >20% | median t→r | mean t→r | max t→r | median UW | max UW | unrecovered |
|---|---|---|---|---|---|---|---|
| VW market | 7 | **19 m** | 23.9 | 48 | 38 | 73 | 0 |
| EW universe | 12 | **15 m** | 14.5 | 30 | 23 | 87 | 0 |
| **OP d10 VW** | 6 | **20.5 m** | 21.3 | 47 | 33.5 | **68** | 0 |
| **OP d10 EW** | 14 | **13 m** | 13.0 | 30 | 20.5 | **103** | 0 |
| SMALL HiOP EW | 16 | **14 m** | 14.1 | 39 | 23 | **111** | 1 |
| d10−d1 spread VW | 7 | **38.5 m** | 42.0 | 89 | 50 | **304** | 1 |
| `RMW` | 4 | **53 m** | 53.7 | 91 | 52 | **142** | 1 |

**The median time to recover a 20%-plus hole is 13 to 20 months for a long-only tilt and 38 to 53
months for the spread or the factor.** `RMW`'s median recovery time is **2.6× the long-only tilt's**,
and one of its four deep episodes is still open.

### 4.3 Drawdown *time*, not only depth

| series | maxDD | mean DD | median DD | % months underwater | % in >10% hole | >20% | >30% | worst UW (months) |
|---|---|---|---|---|---|---|---|---|
| VW market | −50.31% | −7.27% | −2.80% | 67.1% | 25.8% | 12.4% | 4.6% | 73 |
| EW universe | −59.53% | −9.60% | −5.31% | 70.9% | 35.1% | 17.2% | 6.7% | 87 |
| **OP d10 VW** | −52.22% | **−6.38%** | −2.72% | 68.2% | 23.6% | 8.7% | 3.0% | 68 |
| **OP d10 EW** | −63.63% | **−9.44%** | −4.62% | 71.3% | 34.2% | 15.3% | 7.3% | **103** |
| SMALL HiOP EW | −74.13% | **−14.32%** | −8.88% | **78.7%** | 47.6% | 28.3% | 14.4% | **111** |
| **d10−d1 spread VW** | −61.34% | **−22.88%** | −20.72% | **94.7%** | 72.9% | 52.0% | 29.2% | **304** |
| **d10−d1 spread EW** | −65.04% | **−30.07%** | −28.72% | **97.8%** | 86.1% | 71.9% | 46.1% | **328** |
| `RMW` | −41.79% | −6.51% | −3.61% | 83.5% | 28.3% | 5.5% | 0.5% | 142 |
| `HML` | −57.78% | −12.21% | −6.09% | 82.2% | 39.9% | 25.5% | 12.7% | 235 |
| Value d10 VW | −69.81% | −9.62% | −4.02% | 68.0% | 32.8% | 17.0% | 9.4% | 113 |

**The equal-weighted spread spends 97.8% of all months underwater and 71.9% of them in a hole deeper
than 20%.** A spread that barely grows is almost never at a high. **A cash-funded long-only book is
underwater 67–71% of the time, which is the market's own figure.**

---

## 5. SUB-QUESTION 2 — ARE PROFITABILITY'S WORST EPISODES VALUE'S?

**No. They are closer to opposite, with exactly one shared catastrophe. Three independent lines say so
and I measured the fourth.**

### 5.1 What the sources say

- **`S3` [read in full], Novy-Marx's own conclusion:** *"Quality tends to perform best when
  traditional value suffers large drawdowns, and vice versa, so strategies that trade on both signals
  generate steadier returns than do strategies that trade on quality or price alone."*
- **`S4` [read in full], quoted by `S9`:** *"Strategies based on gross profitability generate
  value-like average excess returns, even though they are growth strategies that provide an excellent
  hedge for value."*
- **`S9` [read in full], the most recent authority, quantifying it.** `HML` averaged **+47 bp/month**
  July 1963–December 2006 and **−17 bp/month** January 2007–December 2023 (`t` −0.72 on its own; the
  64 bp/month difference carries `t` 2.59). Over the same late sample their profitability factor
  `PROF` went the **other way**: **+31 bp/month** to **+60 bp/month** (`t` 4.84), a +30 bp/month
  improvement at `t` 2.02. *"Over the late sample, HML's loading on PROF is −0.57. This exposure
  consequently represents a **35 bps/month drag** on HML's returns over the period."* And their own
  caution, which runs against their employer's interest: *"Profitability's exceptional late-sample
  performance, over which it realized a Sharpe ratio of 1.16, is unsustainable."*
- **`S2` [read in full] names the shared catastrophe:** *"An explanation for Figure A4 may be that
  factor performance was generally weak during the dot-com bubble of the late 1990s, but the losses on
  the short legs (risky, unprofitable, growth stocks) exceeded the losses on the long legs (stable,
  profitable, value stocks)."*
- **`S6` [read in full] dates value's episodes**, 1963-07→2020-06, for **long–short value vs growth**:
  deepest are **Current (2006/12→2020/06, 13 yrs 6 mos, −54.8%)**, **Tech bubble
  (1998/08→2000/02→2001/02, 2 yrs 5 mos, −40.6% at the bottom)**, **Iran oil crisis
  (1979/07→1980/11→1982/02, 2 yrs 6 mos)**; longest-lasting are **Current**, **Biotech bubble
  (1989/06→1991/12→1993/02)** and **Nifty Fifty (1970/08→1972/06→1973/04)**. *(I quote only the
  figures `S6`'s prose states verbatim. Its Table 2 has a second numeric column whose header
  "Bottom" the layout extraction separated from its values, so I do not assign the remaining numbers
  to rows — see §13.7.)*

### 5.2 My measurement: the episodes do not overlap

**Correlation of drawdown PATHS, 757 months:**

| | `RMW` | `HML` | spread VW | value d10 | OP d10 VW | VW market |
|---|---|---|---|---|---|---|
| `RMW` | 1.000 | **−0.142** | 0.655 | −0.262 | 0.200 | 0.055 |
| `HML` | −0.142 | 1.000 | −0.309 | 0.318 | −0.208 | −0.155 |
| spread VW | 0.655 | −0.309 | 1.000 | −0.295 | 0.164 | −0.108 |
| value d10 | −0.262 | 0.318 | −0.295 | 1.000 | 0.326 | 0.469 |
| OP d10 VW | 0.200 | −0.208 | 0.164 | 0.326 | 1.000 | **0.792** |
| VW market | 0.055 | −0.155 | −0.108 | 0.469 | 0.792 | 1.000 |

Correlation of **monthly returns**, `RMW` vs `HML` = **+0.093**; VW spread vs `HML` = **+0.117**.

**And what each object did inside the other's worst window** (long-only figures compounded; the
self-financing spreads summed, which is their own convention):

| window | n | VW mkt | EW uni | OP d10 VW | OP d10 EW | spread VW | `RMW` | `HML` | value d10 |
|---|---|---|---|---|---|---|---|---|---|
| **`RMW`'s worst** 199809–200002 | 18 | +59.9% | +85.1% | +25.8% | +39.6% | **−86.0%** | **−51.2%** | **−48.8%** | +42.8% |
| **`HML`'s worst** 200701–202009 | 165 | +232.0% | +145.3% | **+402.1%** | +122.9% | +66.4% | **+44.2%** | **−79.1%** | −4.8% |
| dot-com 199901–200002 | 14 | +23.3% | +55.4% | −3.6% | +16.9% | −71.7% | −48.5% | −35.5% | +17.4% |
| GFC 200711–200902 | 16 | −50.3% | −57.8% | −41.2% | −57.0% | +48.3% | **+25.9%** | −16.3% | **−67.5%** |
| "junk rally" 200903–201002 | 12 | +55.6% | +100.6% | +52.1% | +112.5% | −19.8% | **−1.1%** | +19.0% | +104.9% |
| COVID 202002–202003 | 2 | −20.2% | −28.2% | −19.5% | −33.6% | −0.2% | −3.0% | −17.6% | −43.6% |
| meme/rates 202011–202103 | 5 | +24.7% | +62.5% | +18.2% | +51.8% | −9.1% | −1.2% | +18.2% | +61.6% |
| recent 202311–202607 | 33 | +85.4% | +66.5% | +81.2% | +60.5% | **−21.3%** | **−17.6%** | +18.6% | +258.8% |

**Three readings.**

**(a) One shared catastrophe, and it is the dot-com bubble.** In 199809–200002 the VW spread lost
**86%** and `RMW` **51.2%** while `HML` lost **48.8%** — profitability and value were destroyed
together. This is the one episode where the slate's worry ("a tilt that drew down at the same time as
everything else") is justified, and `S2` names it as the explanation for its own Figure A4.

**(b) Outside it they are close to opposite.** Over `HML`'s 165-month worst drawdown `RMW` earned
**+44.2%**. In the GFC `RMW` was **+25.9%** while the value decile fell **−67.5%** and `HML` fell
−16.3%.

**(c) A FOLK STORY DOES NOT SURVIVE THE MEASUREMENT, AND THE TWO CONSTRUCTIONS DISAGREE.** The
standard account is that quality/profitability was destroyed in the March-2009-onward "junk rally".
On French's data, over 200903–201002, **`RMW` returned −1.1% — essentially flat — while the
OP decile-10-minus-decile-1 spread lost 19.8%.** The two constructions differ by a factor of 18 on
the same episode, because `RMW` is size-balanced (2×3) and the decile spread is not. **Which
construction you pick decides whether the junk rally was an event for profitability at all.** This is
round 2's `C2`-shaped finding arriving unbidden in a third subject area.

**(d) And the live one.** Over 202311–202607 the VW spread is **−21.3%** and `RMW` is **−17.6%** while
the market is **+85.4%** and the value decile is **+258.8%**.

---

## 6. SUB-QUESTION 3 — DOES THE DIVERSIFICATION SURVIVE THE MOMENT IT IS NEEDED?

**For the market-neutral spread, yes, emphatically. For the long-only tilt, there was nothing to
survive — and in equal weighting the exposure gets WORSE exactly when it matters.**

### 6.1 What is documented

**`S5` [read in full, both versions] is the canonical source, and it is about the SPREAD.** From the
published RAS 2019 abstract: *"QMJ returns are high during market downturns, and rather than
exhibiting crash risk, if anything QMJ exhibits a mild positive convexity, benefiting from flight to
quality during crises."* From the body: *"QMJ also performs well in extreme down markets; in fact, the
second-order polynomial showed in the graph has a positive (but insignificant) quadratic term
(meaning that the fitted curve bends upward in the extreme)… In fact, the quadratic term is
marginally significant (t-statistic of 2.0) for the profitability factor. The strong return in
extreme down markets is consistent with a flight to quality (or at least to profitability)."* And on
conditional tests: *"during periods of high and low market volatility (we measure volatility as the
1-month standard deviation of daily returns of the CRSP-value weighted index or the MSCI-World index
and split the sample in the 30% top and bottom time periods) and during periods of a large increase
or drop in aggregate volatility… We find no evidence of compensation for tail risk, if anything
quality appears to hedge (as opposed being correlated to periods) of market distress."*

**`S5` carries an internal contradiction that SURVIVED from the 2013 draft into the 2019 published
version, and per the rules I record it without resolving it.** The abstract says *"mild positive
**convexity**"*; the body, one sentence after stating that the quadratic term is positive and the
curve *"bends upward in the extreme"*, calls the same thing *"This mild **concavity**"*. Both versions
contain both words in the same places. A positive quadratic term is convexity, so the body's word
appears to be the error — **but I am not the referee, the paper says both, and I do not adjudicate.**

**`S2` [read in full] supplies documented STRESSED BETAS — for the market-neutral long leg.** Table A5:
`Regular beta` **−0.02**, `LPM(0) beta` **−0.02**, `LPM(1σ) beta` **−0.01** for the long leg, against
−0.08/−0.06/−0.03 (short) and −0.11/−0.08/−0.04 (long–short). Its own framing: *"the long legs may be
less attractive than the short legs from a tail-risk perspective… [the differences] are tiny… In
summary, a downside risk perspective seems unlikely to explain the finding that the long side of
factors dominates the short side."* **These are downside betas of an object already hedged to beta
zero. They say nothing about a long-only portfolio's conditional beta, and they must not be read as
though they did.**

**`S7` [read in full] answers the ADJACENT question, and the distinction matters.** Its Blunder 3 is
that *"Cross-factor correlations are time varying, with spikes in correlation around periods of factor
underperformance, causing the **benefits of diversification to disappear during big drawdowns**"* and
*"Forming portfolios of factors does not mitigate the risk of large drawdowns to the extent we might
expect because the large drawdowns of individual factors often happen at the same time."* With a
number: *"the worst single month for the portfolio of factors 1–6 is at −16.0% and is almost identical
to the average worst month for the six constituent factors, which is −17.0%."* **But this is
correlation AMONG FACTORS, not correlation of a factor WITH THE MARKET.** Sub-question 3 asks the
second. **No source I reached reports a long-only characteristic tilt's conditional market beta in
stress.** So I measured it.

### 6.2 My measurement: conditional betas, in buckets and in episodes

Buckets defined on the VW market's own monthly total return, 757 months:

| bucket | n | mkt ret | OP d10 VW: corr / β / mean | OP d10 EW: corr / β / mean | spread VW: corr / β / mean | `RMW`: corr / β / mean |
|---|---|---|---|---|---|---|
| all months | 757 | +0.96% | 0.930 / **0.96** / +1.05% | 0.877 / **1.21** / +1.20% | −0.353 / −0.34 / +0.25% | −0.193 / −0.10 / +0.26% |
| market DOWN months | 283 | −3.43% | 0.864 / 0.97 / −3.09% | 0.835 / **1.30** / −4.05% | −0.245 / −0.34 / +1.92% | −0.120 / −0.09 / +0.78% |
| worst decile of mkt months | 75 | −7.67% | 0.799 / 0.98 / −7.17% | 0.800 / **1.46** / −9.37% | −0.166 / −0.28 / +3.71% | −0.060 / −0.06 / +1.37% |
| worst 5% of mkt months | 37 | −9.75% | 0.800 / **1.02** / −9.22% | 0.808 / **1.60** / −12.14% | −0.263 / −0.50 / +3.58% | −0.082 / −0.09 / +1.36% |
| worst 20 mkt months | 20 | −11.48% | 0.850 / **1.26** / −10.37% | 0.774 / **1.66** / −14.79% | −0.115 / −0.23 / +5.19% | +0.023 / +0.03 / +1.79% |
| best decile of mkt months | 75 | +8.28% | 0.782 / 1.12 / +8.00% | 0.618 / 1.47 / +9.55% | +0.082 / +0.17 / −2.27% | +0.071 / +0.08 / −0.40% |

**Excess over the relevant benchmark in each bucket, which is the statistic that decides the question:**

| bucket | OP d10 VW − VW mkt | OP d10 EW − EW universe | `RMW` |
|---|---|---|---|
| all months | +0.09% | **+0.03%** | +0.26% |
| market DOWN months | +0.34% | **−0.25%** | +0.78% |
| worst decile of mkt months | +0.50% | **−0.41%** | +1.37% |
| **worst 5% of mkt months** | **+0.52%** | **−0.70%** | **+1.36%** |
| **worst 20 mkt months** | **+1.11%** | **−0.42%** | **+1.79%** |
| best decile of mkt months | −0.29% | +0.71% | −0.40% |

**And inside the market's six worst drawdown EPISODES — the moment, not scattered months:**

| market episode | n | VW mkt | OP d10 VW: tot / β / excess | OP d10 EW: tot / β / excess | SMALL HiOP EW: tot / β / excess | `RMW`: tot / β / excess |
|---|---|---|---|---|---|---|
| 200710→200902 | 16 | −50.3% | −41.2 / 0.98 / **+9.1** | −57.0 / **1.30** / **−6.7** | −62.7 / 1.30 / **−12.4** | +25.9 / −0.12 / **+76.3** |
| 197212→197409 | 21 | −46.5% | −52.2 / 0.85 / **−5.7** | −57.5 / **1.57** / **−11.0** | −56.6 / 1.54 / −10.0 | −13.4 / +0.05 / **+33.1** |
| 200008→200209 | 25 | −45.0% | −26.9 / 0.62 / **+18.1** | −4.7 / 1.05 / **+40.3** | −2.5 / 0.97 / +42.5 | +73.3 / −0.61 / **+118.3** |
| 196811→197006 | 19 | −33.6% | −31.1 / 0.97 / +2.5 | −50.5 / **1.29** / **−17.0** | −58.0 / 1.37 / **−24.4** | +3.9 / −0.09 / **+37.4** |
| 198708→198711 | 3 | −29.9% | −34.2 / 1.01 / −4.3 | −36.5 / **1.39** / −6.7 | −35.7 / 1.46 / −5.9 | −0.5 / −0.18 / **+29.3** |
| 202112→202209 | 9 | −24.8% | −19.3 / 0.97 / +5.6 | −25.7 / 1.09 / −0.8 | −26.2 / 1.07 / −1.4 | −1.3 / −0.06 / **+23.5** |

**Four conclusions, and the third is the one that matters for an equal-weighted book.**

1. **Correlation with the market never falls below 0.77 for any long-only tilt in any stress bucket.**
   Whatever diversification the characteristic supplies, it is not available to a long-only holder when
   the market falls.
2. **`RMW` is genuinely, massively defensive — and it is the spread.** It beat the market by **+23 to
   +118 pp inside every one of the market's six worst drawdown episodes**, at a beta of −0.61 to +0.05.
   `S5`'s flight-to-quality is real and large. **It lives entirely in the object with a short leg.**
3. **THE EQUAL-WEIGHTED LONG-ONLY TILT IS THE OPPOSITE OF DEFENSIVE.** Its beta rises monotonically
   with stress — **1.21 → 1.30 → 1.46 → 1.60 → 1.66** — and it *lost to its own equal-weighted
   benchmark* in the worst 5% of months by **−0.70 %/mo**, having beaten it by only **+0.03 %/mo**
   unconditionally. Inside the market's six worst episodes it trailed in five of six. **The tilt gives
   back, in stress, more than twenty times what it earns in calm.**
4. **The value-weighted tilt is mildly defensive and the effect is real but small:** +0.52 %/mo in the
   worst 5% of months, +1.11 %/mo in the worst 20, at a beta that stays near 1 (0.96 → 1.02 → 1.26).
   **The sign of the answer to sub-question 3 depends on the weighting, and the weighting that answers
   "worse" is equal weighting.**

**How often is the tilt's hole deeper than the benchmark's at the same moment:**

| | all months | months the benchmark was >20% down | mean gap | worst gap |
|---|---|---|---|---|
| OP d10 VW vs VW mkt | 37.9% | **24.5%** (n=94) | +0.90 pp | −12.29 pp |
| OP d10 EW vs VW mkt | 56.8% | **44.7%** | −2.16 pp | −30.34 pp |
| OP d10 EW vs EW universe | 39.1% | **50.8%** (n=130) | +0.16 pp | −15.51 pp |
| SMALL HiOP EW vs EW universe | 63.9% | **75.4%** | −4.72 pp | −39.64 pp |
| SMALL HiOP EW vs VW mkt | 67.5% | 47.9% | −7.04 pp | −46.31 pp |

**The small-and-profitable portfolio is in a deeper hole than the equal-weighted universe in 75.4% of
the months when that universe is already more than 20% down**, and at worst it is **39.6 pp** deeper.

---

## 7. SUB-QUESTION 5 — IS THE TILT'S DRAWDOWN DISTINGUISHABLE FROM THE MARKET'S?

**No, and the cleanest demonstration needs no statistics at all.**

### 7.1 The plain demonstration, and the live one

**As at 2026-07, the long-only profitability tilts are at or near all-time highs while the factor
they are built on is in a 26% hole:**

| series | current drawdown | detail |
|---|---|---|
| OP decile 10 **EW** | **0.00%** | at a high |
| Value decile 10 VW | 0.00% | at a high |
| VW market | −1.05% | 2 months off a 202605 peak |
| OP decile 10 **VW** | −1.98% | 2 months off a 202605 peak |
| EW universe | −3.08% | 1 month off a 202606 peak |
| SMALL HiOP EW | −0.12% | ongoing since 202106; trough −31.19% at 202310, 61 months underwater |
| **d10−d1 spread EW** | **−16.19%** | ongoing from 202503; trough −28.16% at 202510 |
| **`RMW`** | **−17.67%** | **ongoing from 202310; trough −25.86% at 202606; 33 months underwater** |
| d10−d1 spread VW | **−27.07%** | ongoing from 202409; trough −30.27% at 202606; 22 months |
| **`HML`** | **−29.57%** | **ongoing from 200612 — 235 months underwater and never recovered** |

**An investor in the long-only profitability tilt is at a high. An investor in the profitability
factor is in a 26% hole that is 33 months old. They are not holding the same risk, and the drawdown
statistic is where the difference is most visible.**

### 7.2 The measured version

| comparison | corr(drawdown paths) | at the tilt's own trough | worst RELATIVE drawdown (cumulative tilt ÷ cumulative benchmark) |
|---|---|---|---|
| OP d10 VW vs VW mkt | **0.792** | 197409: tilt −52.22%, mkt **−46.51%** → tilt-specific hole **−5.71 pp** | **−29.28%**, peak 196912 → trough 198203 (147 m) → recovered 200108 (233 m) — **380 months underwater** |
| OP d10 EW vs EW universe | **0.922** | 197412: tilt −63.63%, uni **−56.65%** → **−6.98 pp** | **−29.14%**, 201108 → 202102 (114 m) → recovered 202310 (32 m) — 146 months |
| OP d10 EW vs VW mkt | 0.691 | 197412: tilt −63.63%, mkt −41.75% → −21.88 pp | **−52.50%**, 198307 → 199910 (195 m) → recovered 200308; **and an ONGOING −50.72% from 201005, 194 months and not recovered** |
| SMALL HiOP EW vs EW universe | 0.869 | 197412: −74.13% vs −56.65% → −17.48 pp | **−64.20%**, 196901 → 202003 (614 m) — **NEVER RECOVERED, 690 months underwater** |
| d10−d1 spread VW vs VW mkt | **−0.108** | 198305: spread −61.34%, mkt **0.00%** → −61.34 pp | −99.55% |
| `RMW` vs VW mkt | **+0.055** | 200002: `RMW` −41.79%, mkt **−1.57%** → −40.22 pp | −99.23% |

**Read the first column.** The long-only tilt's drawdown path explains 63% (VW) to 85% (EW) of the
variance of the benchmark's, and vice versa. **The spread's drawdown path is statistically unrelated
to the market's (−0.11, +0.06) — at `RMW`'s worst moment the market was 1.57% off its high.**
**That is the difference between the two objects, stated as a correlation.**

**And read the last column, because it is the object `S3`'s Table 9 and `S2`'s Figure A4 actually
report.** The *relative* drawdown — underperformance against the benchmark — is a completely
different, and far longer, animal than the absolute one: the VW tilt's worst relative drawdown is only
**−29.3% deep** but it was **380 months — 31.7 years — underwater**, and the small-and-profitable
portfolio's relative drawdown against the EW universe began in **January 1969** and **has never
recovered in 690 months.**

### 7.3 The decisive table: the characteristic barely moves the drawdown, and where it moves it, it moves it the wrong way

All ten OP deciles, 196307–202607. `DDcorr` is the correlation of that decile's drawdown path with the
benchmark's.

**VALUE-WEIGHTED** (benchmark = VW market: maxDD −50.31%, mean DD −7.27%)

| decile | CAGR | vol | β | maxDD | mean DD | worst UW | vs bench | DDcorr |
|---|---|---|---|---|---|---|---|---|
| d1 (junk) | 7.20% | 22.81% | 1.30 | −82.97% | −25.83% | 249 m | −0.160% | 0.638 |
| d2 | 9.15% | 18.58% | 1.10 | −68.19% | −12.32% | 160 m | −0.085% | 0.836 |
| d3 | 8.86% | 17.03% | 1.03 | −56.70% | −9.13% | 85 m | −0.130% | 0.957 |
| d4 | 10.26% | 16.02% | 0.97 | −59.02% | −7.55% | 70 m | −0.037% | 0.851 |
| d5 | 11.64% | 15.99% | 0.96 | −53.20% | −6.24% | 65 m | +0.067% | 0.930 |
| d6 | 10.71% | 15.72% | 0.96 | −57.42% | −7.79% | 72 m | −0.007% | 0.921 |
| d7 | 10.24% | 15.79% | 0.97 | −54.34% | −7.29% | 66 m | −0.042% | 0.894 |
| **d8** | **12.47%** | 15.93% | 0.98 | **−42.01%** | **−5.66%** | **50 m** | **+0.128%** | 0.850 |
| d9 | 12.27% | 15.66% | 0.96 | −47.70% | −7.72% | 85 m | +0.110% | 0.942 |
| **d10** | 11.98% | 15.95% | 0.96 | **−52.22%** | −6.38% | 68 m | **+0.092%** | 0.792 |

**EQUAL-WEIGHTED** (benchmark = EW universe: maxDD −59.53%, mean DD −9.60%)

| decile | CAGR | vol | β | maxDD | mean DD | worst UW | vs bench | DDcorr |
|---|---|---|---|---|---|---|---|---|
| d1 (junk) | 9.54% | 27.24% | 1.29 | −69.32% | −21.80% | 103 m | −0.104% | 0.758 |
| d2 | 13.59% | 19.93% | 1.09 | −58.74% | −9.35% | 86 m | **+0.064%** | 0.977 |
| **d3** | **14.15%** | 18.77% | 1.04 | −56.44% | −7.46% | 85 m | **+0.086%** | 0.930 |
| d4 | 13.97% | 18.08% | 1.02 | −56.27% | −7.29% | 87 m | +0.063% | 0.922 |
| **d5** | 14.23% | 17.60% | **1.00** | **−51.99%** | **−6.23%** | **46 m** | **+0.075%** | 0.916 |
| d6 | 13.79% | 17.93% | 1.02 | −57.24% | −7.05% | 87 m | +0.048% | 0.919 |
| d7 | 14.22% | 18.27% | 1.05 | −56.85% | −6.88% | 56 m | +0.084% | 0.922 |
| d8 | 14.04% | 18.68% | 1.09 | −57.18% | −7.41% | 96 m | +0.077% | 0.924 |
| d9 | 13.44% | 19.67% | 1.14 | −60.52% | −8.10% | 60 m | +0.049% | 0.914 |
| **d10** | **12.77%** | **21.25%** | **1.21** | **−63.63%** | **−9.44%** | **103 m** | **+0.026%** | 0.922 |

**Four facts from one table.**

1. **Every single long-only decile's drawdown path correlates 0.64 to 0.98 with the benchmark's.** Not
   one decile escapes. The drawdown belongs to the asset class.
2. **In equal weighting the high-profitability decile is the WORST of deciles 2–10 on drawdown
   (−63.63%), on volatility (21.25%), on beta (1.21), on mean drawdown (−9.44%), on worst underwater
   spell (103 months) — and on excess return (+0.026 %/mo, the smallest of deciles 2–9).** Decile 5
   beats the universe by **+0.075 %/mo at beta 1.00 with a −51.99% drawdown and a worst underwater
   spell of 46 months**. **The middle of the profitability distribution dominates the top on every axis
   this lane measures.** This is independently consistent with round 1's `A1` reading — *"The best
   long-only decile is decile 9 at −0.03%, indistinguishable from decile 5's −0.05%"* — reached from
   DGTW-abnormal returns rather than from drawdowns.
3. **In value weighting, decile 8 dominates decile 10 on everything:** higher CAGR (12.47% vs 11.98%),
   shallower drawdown (−42.01% vs −52.22%), smaller mean drawdown (−5.66% vs −6.38%), shorter worst
   underwater spell (50 vs 68 months) and a larger excess over the market (+0.128% vs +0.092% /mo).
4. **The profitability sort is U-shaped in beta under equal weighting** — 1.29 at the junk end, 1.00 in
   the middle, 1.21 at the quality end. **The equal-weighted high-profitability portfolio is the
   second-highest-beta long portfolio in the whole sort.** That is the mechanism behind §6.2's stress
   result, and it is the opposite of the story the word "quality" suggests.

### 7.4 The programme-era window

**201001–202607** (the span the programme's own fixture covers; reported because the era matters, not
because I have anything to say about the fixture):

| series | CAGR | vol | maxDD | peak | trough | recovery | UW | mean DD | % UW |
|---|---|---|---|---|---|---|---|---|---|
| VW market | 14.16% | 14.9% | −24.84% | 202112 | 202209 | 202312 | 24 m | −3.26% | 52.8% |
| EW universe | 10.66% | 19.7% | −36.42% | 202106 | 202310 | 202604 | 58 m | −8.63% | 73.4% |
| **OP d10 VW** | **16.14%** | 15.1% | **−19.51%** | 202001 | 202003 | 202006 | 5 m | −2.44% | 51.8% |
| **OP d10 EW** | 10.62% | 20.3% | **−38.60%** | 201808 | 202003 | 202011 | 27 m | −5.86% | 70.9% |
| SMALL HiOP EW | 6.93% | 25.6% | **−62.62%** | 201808 | 202003 | 202102 | 30 m | −13.91% | 87.4% |
| d10−d1 spread VW | 2.70% | 16.1% | −30.27% | 202409 | 202606 | **NEVER** | 22 m | −10.57% | 88.9% |
| d10−d1 spread EW | 3.77% | 16.3% | −52.38% | 201910 | 202102 | 202211 | 37 m | −9.97% | 84.4% |
| `RMW` | 1.89% | 7.7% | −25.86% | 202310 | 202606 | **NEVER** | 33 m | −4.18% | 85.9% |
| `HML` | **−0.99%** | 11.2% | −53.36% | 201004 | 202009 | **NEVER** | 195 m | −23.23% | 98.0% |
| Value d10 VW | 13.28% | 25.5% | −52.93% | 201801 | 202003 | 202103 | 38 m | −10.28% | 78.9% |

**In this era the VW tilt's drawdown was MILDER than the market's (−19.5% vs −24.8%) and the EW tilt's
was WORSE than the EW universe's (−38.6% vs −36.4%).** The same split as everywhere else in this
brief: **the weighting, not the characteristic, decides the sign.** And the small-and-profitable
equal-weighted portfolio drew down **−62.6%** in 19 months and compounded at **6.93%** while the market
compounded at 14.16%.

**So the answer to sub-question 5, stated plainly as the lane demands: IT IS THE MARKET'S DRAWDOWN
WITH A SMALL ALPHA ATTACHED — and under equal weighting, with a small NEGATIVE alpha attached in
exactly the months the drawdown happens.**

---

## 8. SUB-QUESTION 6 — HOW LONG MUST YOU HOLD BEFORE THE PREMIUM HAS ARRIVED?

**This is the question I was told to go past the others to reach, and it has the starkest answer in
the lane.**

### 8.1 What is documented

- **`S3` [read in full]** reports one-year and five-year **outperformance frequencies** for long-only
  strategies against a Russell benchmark: profitable value **72.2% / 81.3%**; traditional value
  **55.7% / 67.5%**; cheap defensive **48.8% / 54.0%** (large cap, 1963-07→2013-12, net of estimated
  costs). **This is the most directly usable horizon evidence I found in the literature.**
- **`S1` [read in full]** makes the horizon an explicit input and states the mechanism: *"the impact of
  the Sharpe ratio on the probability of reaching a certain maximum drawdown level is large, which is
  intuitive because **the Sharpe ratio captures the ability to lift yourself out of a hole**."* Its
  Exhibit 2 Panel B: *"As a return stream is evaluated over a longer window, the probability of
  hitting a certain drawdown level naturally increases."*
- **`S7` [read in full]** says it ran the equivalent test on horizons: *"In the online supplement, we
  show that the conclusions drawn from Exhibit 11 continue to apply when, instead of studying worst
  drawdowns, we study the worst one-, three-, and five-year periods for the same portfolios of factors.
  We show that, just as for the drawdowns reported in Exhibit 11, these prolonged periods of losses
  would surprise an investor who, in effect, overestimates the extent to which factors are well
  behaved."* **I did not obtain the online supplement** (§14).
- **`S6` [read in full]** supplies the single recovery figure quoted in §4.1 and notes Lev &
  Srivastava's claim that value has been unusually unprofitable *"not only during the current drawdown
  but for as long as 30 years."*

### 8.2 My measurement (a): the empirical frequencies

Fraction of **overlapping** rolling windows satisfying each condition. Overlapping windows are not
independent, so these are counts and not tests — they are reported as frequencies exactly as `S3`
reports his.

| question | 1 y | 3 y | 5 y | **10 y** | 15 y | 20 y | 30 y |
|---|---|---|---|---|---|---|---|
| VW market total return > 0 | 78.8% | 87.5% | 91.4% | 97.5% | 100% | 100% | 100% |
| EW universe total return > 0 | 73.7% | 86.7% | 94.6% | 100% | 100% | 100% | 100% |
| OP d10 VW total return > 0 | 80.2% | 88.9% | 95.1% | 99.7% | 100% | 100% | 100% |
| OP d10 EW total return > 0 | 75.3% | 89.9% | 93.6% | 100% | 100% | 100% | 100% |
| SMALL HiOP EW total return > 0 | 71.3% | 82.1% | 86.5% | 99.5% | 100% | 100% | 100% |
| OP d10 VW beats cash | 71.8% | 79.9% | 81.1% | 82.8% | 90.1% | 100% | 100% |
| OP d10 EW beats cash | 70.2% | 80.3% | 84.4% | 92.8% | 100% | 100% | 100% |
| **OP d10 VW beats the VW market** | **55.0%** | **62.0%** | **64.0%** | **70.1%** | **70.2%** | **70.7%** | 80.2% |
| **OP d10 EW beats the EW universe** | **52.0%** | **51.1%** | **52.0%** | **52.8%** | **55.0%** | **58.5%** | **59.3%** |
| OP d10 EW beats the VW market | 50.8% | 49.2% | 52.3% | 61.1% | 71.8% | 82.4% | 99.0% |
| d10−d1 spread VW cumulative > 0 | 54.4% | 60.2% | 68.9% | 76.6% | 83.6% | 91.7% | 99.7% |
| d10−d1 spread EW cumulative > 0 | 56.8% | 61.1% | 61.2% | 62.9% | 77.7% | 89.4% | 92.0% |
| `RMW` cumulative > 0 | 68.6% | 79.8% | 85.5% | 90.4% | 98.8% | 100% | 100% |
| `HML` cumulative > 0 | 61.5% | 69.8% | 75.6% | 77.7% | 83.6% | 87.8% | 100% |

**Two things jump out.**

1. **"OP d10 VW beats the VW market" PLATEAUS at ~70% and stays there from year 10 to year 20.**
   Lengthening the horizon from a decade to two decades buys **0.6 percentage points** of extra
   confidence. The usual comfort — "hold longer and the premium arrives" — **does not hold for this
   object**; it holds for the *equity premium* (row 6–7: beats cash 100% of the time by 20 years).
2. **"OP d10 EW beats the EW universe" is a coin flip at every horizon up to thirty years:** 52.0% at
   one year, **52.8% at ten**, 59.3% at thirty. **For an equal-weighted book, the profitability tilt's
   advantage over an equal-weighted universe is not detectable at any horizon a human career contains.**

### 8.3 My measurement (b): the closed form, on the measured numbers

Years for the realised information ratio to produce `t = 2`, i.e. `(2/IR)²`:

| object | mean | **IR** | realised `t` over 63 yrs | **years to `t` = 2** |
|---|---|---|---|---|
| OP d10 VW excess of cash (the *total* Sharpe) | +0.691 %/mo | 0.518 | 4.11 | **14.9** |
| OP d10 EW excess of cash (the *total* Sharpe) | +0.833 %/mo | 0.470 | 3.73 | **18.1** |
| **OP d10 VW minus the VW market** | **+0.092 %/mo** | **0.187** | **1.49** | **114.3** |
| **OP d10 EW minus the EW universe** | **+0.026 %/mo** | **0.057** | **0.45** | **1,234.6** |
| OP d10 EW minus the VW market | +0.234 %/mo | 0.262 | 2.08 | 58.2 |
| **SMALL HiOP EW minus the EW universe** | **+0.027 %/mo** | **0.042** | **0.33** | **2,318.4** |
| d10−d1 spread VW | +0.252 %/mo | 0.203 | 1.61 | 97.4 |
| `RMW` factor | +0.257 %/mo | 0.390 | 3.10 | 26.3 |

**The 15-to-18-year figure that the long-only tilt's total Sharpe delivers is the equity risk
premium's horizon, not the tilt's.** The tilt's own contribution — what the characteristic adds over
the universe the programme would otherwise hold — needs **114 years** value-weighted and **1,235
years** equal-weighted, and over the 63 years actually available it reached **`t` = 1.49** and
**`t` = 0.45** respectively. **Sixty-three years of US data is not enough to establish that the
equal-weighted profitability tilt beats an equal-weighted universe.**

**This is the same arithmetic as round 2's `B1` finding arriving as a horizon.** `B1` measured that
the benchmark choice moves a long leg's `t` from 1.95 to 5.98; here the benchmark choice moves the
required horizon from 58 years (EW tilt vs the VW market, which imports a size bet) to 1,235 years
(EW tilt vs the EW universe, which does not). **Picking the benchmark that flatters is worth a factor
of 21 on the horizon.**

---

## 9. PAST THE SUB-QUESTIONS

### 9.1 Is the observed drawdown informative at all, or is it what any series with this mean and vol produces?

**It is what any series with this mean, vol and serial dependence produces. The drawdown depth carries
no information of its own.** Bootstrap null of maximum drawdown, B = 5,000 each, same length as the
observed series. `pct(obs)` is the fraction of draws with a **deeper** drawdown than observed — low
means the realisation was mild for its mean and vol, high means extreme.

| series | observed | iid p5 / p50 / p95 | iid pct(obs) | **24-m block p5 / p50 / p95** | **block pct(obs)** |
|---|---|---|---|---|---|
| VW market | −50.31% | −56.60 / −39.69 / −28.44 | 13.6% | −66.82 / **−50.31** / −33.55 | **49.7%** |
| EW universe | −59.53% | −68.95 / −49.74 / −35.96 | 18.3% | −75.61 / −58.58 / −41.87 | **46.4%** |
| OP d10 VW | −52.22% | −56.41 / −39.51 / −28.22 | 9.5% | −64.54 / −48.20 / −34.20 | **32.2%** |
| OP d10 EW | −63.63% | −72.60 / −53.20 / −38.80 | 17.8% | −78.06 / −60.08 / −45.85 | **35.7%** |
| SMALL HiOP EW | −74.13% | −79.40 / −60.18 / −44.78 | 12.1% | −86.89 / −69.80 / −56.08 | **34.8%** |
| d10−d1 spread VW | −61.34% | −83.89 / −61.03 / −41.39 | 49.3% | −87.65 / −66.01 / −45.44 | **64.4%** |
| `RMW` | −41.79% | −46.28 / −29.37 / −18.93 | 10.7% | −56.84 / −39.92 / −21.89 | **41.2%** |

**Under iid resampling every realised drawdown looks extreme (9.5–18% of draws are deeper). Once
24-month blocks preserve the volatility clustering, every one of them lands between the 32nd and the
50th percentile of its own null.** Nothing here is an outlier. *(The market's block p50 printing as
−50.31%, identical to the observed value at two decimals, is a coincidence: a sanity check over 3,000
draws found **0 exact reproductions** of the original ordering and 2,204 distinct maxDD values.)*

**TWO PUBLISHED PAPERS REACH THE SAME CONCLUSION BY THE SAME ROUTE, WHICH IS WHY I TRUST IT.**

- **`S1` [read in full]:** *"For the case of a 10-year window and Sharpe ratio of 0.5, we had a 43%
  probability of hitting a two-sigma drawdown… This probability **increases to 55% for the
  bootstrapped actual returns**… This increased probability of hitting a drawdown level is a result of
  both nonnormality of monthly returns and heteroskedasticity (clustering of volatility)."* And they
  used **the same block length I did**: *"we bootstrap **two-year blocks** from US equity returns since
  1926… As a robustness check, we reran our analysis with blocks longer than 24 months and found
  similar results."*
- **`S7` [read in full]:** for its factors 1–6 portfolio, worst realised drawdown **−33.4%**; the
  average largest drawdown in simulation is **−21.5% under normality** with *"Just 2.7% of the 10,000
  simulations delivered a drawdown worse than the real-world worst-case drawdown of 33.4%"*; under a
  one-month block bootstrap the average largest is **−25.8%** and *"just 12.4% of the simulated largest
  drawdowns are bigger"*; and under a **12-month block bootstrap** the average largest is **−30.4%**
  and *"in over a quarter of the simulations, the largest drawdown exceeds the actual largest
  drawdown."* Their own summary: *"if we account for the cross, auto-, and cross-serial correlation
  structures in factor returns, these large drawdowns are not that surprising."*

**The lesson for any future runner is methodological and it is sharp: a drawdown reported without a
serial-dependence-preserving null is a number that looks alarming and means nothing.** `S7`'s own
2.7% → 29.1% and my 9.5% → 32.2% are the same arithmetic.

### 9.2 What a cost drag does to the drawdown of a cash-funded tilt

Costs charged as a flat annual drag on the monthly series. The two reference levels are **`S3`'s own
estimates for quality strategies: ~0.5%/yr large cap and ~1.5%/yr small cap**, which he justifies by
quality's low turnover.

| series | drag/yr | CAGR | maxDD | mean DD | worst UW | **excess over its own benchmark** |
|---|---|---|---|---|---|---|
| OP d10 VW | 0.0% | 11.98% | −52.22% | −6.38% | 68 m | **+0.092 %/mo** |
| OP d10 VW | **0.5%** | 11.43% | −52.65% | −6.68% | 68 m | **+0.050 %/mo** |
| OP d10 VW | **1.5%** | 10.33% | −53.50% | −7.33% | 80 m | **−0.033 %/mo** |
| OP d10 VW | 3.0% | 8.69% | −54.76% | −8.63% | 92 m | −0.158 %/mo |
| OP d10 EW | 0.0% | 12.77% | −63.63% | −9.44% | 103 m | **+0.026 %/mo** |
| OP d10 EW | **0.5%** | 12.21% | −64.74% | −9.84% | 106 m | **−0.015 %/mo** |
| OP d10 EW | **1.5%** | 11.10% | −66.85% | −10.69% | 112 m | **−0.099 %/mo** |
| OP d10 EW | 3.0% | 9.46% | −69.80% | −12.05% | 113 m | −0.224 %/mo |
| SMALL HiOP EW | 0.0% | 12.06% | −74.13% | −14.32% | 111 m | **+0.027 %/mo** |
| SMALL HiOP EW | **0.5%** | 11.50% | −74.91% | −14.79% | 111 m | **−0.015 %/mo** |
| SMALL HiOP EW | **1.5%** | 10.40% | −76.40% | −15.75% | 113 m | **−0.098 %/mo** |
| SMALL HiOP EW | 3.0% | 8.77% | −78.48% | −17.44% | 115 m | −0.223 %/mo |

**A drag of 0.5 %/yr — the cheaper of `S3`'s two own estimates, for LARGE caps — is enough to turn the
equal-weighted profitability tilt's excess over an equal-weighted universe NEGATIVE.** At his
small-cap figure of 1.5 %/yr it is −0.099 %/mo and the drawdown deepens by 3.2 pp with nine more
months underwater. **The margin being defended is 2.6 bp/month.** *(A flat drag is a crude cost model
and I say so; it is an attribution of the drag to the series, not a turnover model. The point survives
the crudeness because the margin is smaller than any plausible cost.)*

### 9.3 Does monthly sampling hide the drawdown? Mostly no — a useful negative result

Every drawdown figure in the literature above is monthly. The programme trades daily bars. **I
measured the same objects on French's daily files (15,876 days, 19630701–20260731):**

| series | daily maxDD | peak | trough | recovery | days p→t | days t→r | days UW | monthly maxDD | **daily is deeper by** |
|---|---|---|---|---|---|---|---|---|---|
| VW market | **−54.57%** | 20071009 | 20090309 | 20120228 | 355 | 750 | 1,105 | −50.31% | **+4.25 pp** |
| OP d10 VW | **−54.57%** | 19730123 | 19741004 | 19780802 | 429 | 966 | 1,395 | −52.22% | **+2.35 pp** |
| OP d10 EW | **−62.93%** | 20070713 | 20081120 | 20100309 | 344 | 324 | 668 | −63.63% | **−0.70 pp** |
| d10−d1 spread VW | **−63.53%** | 19981008 | 20000307 | 20010917 | 355 | 382 | 737 | −61.34% | **+2.19 pp** |

**Monthly sampling understates maximum drawdown by only about 2 to 4 percentage points, and for the
EW tilt the monthly figure is deeper because the two frequencies pick different episodes.** These
drawdowns are multi-year; sampling frequency barely touches them. **The monthly literature is not
materially misleading on depth** — which is worth knowing, because it was a plausible objection and it
turns out not to bite. *(The market's and the VW tilt's daily maxDD both printing −54.57% is a
coincidence of two digits in two entirely different episodes — 2007-09 versus 1973-74 — not a bug.)*
**And the peak/trough dates 2007-10-09 → 2009-03-09 are the universally cited market peak and trough
dates, falling out of the computation unprompted: a third positive control I did not plan.**

### 9.4 Does concentrating the tilt change the drawdown? Yes — for the worse, twice over

| portfolio | CAGR | vol | maxDD | mean DD | % UW | worst UW | excess vs benchmark |
|---|---|---|---|---|---|---|---|
| OP top 10% VW | 11.98% | 15.95% | **−52.22%** | −6.38% | 68.2% | 68 m | +0.092 %/mo |
| OP top 20% VW | 12.02% | 15.43% | −49.95% | −6.67% | 66.7% | 68 m | +0.088 %/mo |
| OP top 30% VW | **12.24%** | 15.29% | **−47.97%** | −6.15% | 63.9% | 67 m | **+0.102 %/mo** |
| OP top 10% EW | 12.77% | 21.25% | **−63.63%** | −9.44% | 71.3% | 103 m | +0.026 %/mo |
| OP top 20% EW | 13.10% | 20.40% | −61.66% | −8.68% | 69.5% | 62 m | +0.036 %/mo |
| OP top 30% EW | **13.43%** | 19.80% | **−59.99%** | −8.18% | 67.9% | 97 m | **+0.051 %/mo** |

**Concentrating from the top 30% to the top 10% makes the drawdown 4.3 pp deeper (VW) or 3.6 pp deeper
(EW) AND the excess return smaller (+0.102 → +0.092 VW; +0.051 → +0.026 EW).** There is no trade-off
here to manage — concentration is worse on both axes at once. **This is the same shape as Table 19's
decile gradient and it is a second, independent sighting of it.**

---

## 10. CONFLICTS, RECORDED AND NOT ADJUDICATED

### 10.1 `S8` versus `S2` on whether the long leg or the spread has the worse drawdown — and the mechanism that dissolves it

**`S8` [read in full], verified by me from the arXiv bytes rather than restated:** the Figure 8
caption reads *"Right: Drawdown time series (AUM − Peak Value/AUM) for both implementations. The mean
depth for LH amounts to **−8.2%**, but only **−3.9%** for LS."* Table 1: hedged long-only Sharpe 0.56,
mean drawdown **−8.2%**, returns+dividends 8.4%/yr, trading cost −2.8%, financing −2.0%, no borrow;
long–short Sharpe 0.98, mean drawdown **−3.9%**, 14.2% / −4.8% / −2.6% / −0.6%. Both at 6.4% realised
volatility, global, five factors equally weighted, 2000–2020, \$1bn AUM.

**`S2` [read in full]:** the market-neutral long leg's **maximum** drawdown is **−10.5%** against the
long–short's **−24.2%** — the **opposite ordering**.

**Both are correct, and they are not in conflict, because mean drawdown is a Sharpe statistic and
neither paper says so.** Across nine series on my own data:

| series | ann. return | ann. vol | Sharpe\* | mean DD | maxDD | % UW |
|---|---|---|---|---|---|---|
| VW market | 10.85% | 15.41% | 0.42 | −7.27% | −50.31% | 67.1% |
| EW universe | 12.66% | 20.28% | 0.41 | −9.60% | −59.53% | 70.9% |
| OP d10 VW | 11.98% | 15.95% | **0.47** | **−6.38%** | −52.22% | 68.2% |
| OP d10 EW | 12.77% | 21.25% | 0.39 | −9.44% | −63.63% | 71.3% |
| SMALL HiOP EW | 12.06% | 24.11% | **0.32** | **−14.32%** | −74.13% | 78.7% |
| Value d10 VW | 14.49% | 21.69% | 0.46 | −9.62% | −69.81% | 68.0% |
| d10−d1 spread VW | 1.93% | 14.90% | **0.13** | **−22.88%** | −61.34% | 94.7% |
| `RMW` | 2.81% | 7.91% | 0.35 | −6.51% | −41.79% | 83.5% |
| `HML` | 3.10% | 10.28% | 0.30 | −12.21% | −57.78% | 82.2% |

\* excess-of-cash for the funded books, raw for the self-financing spreads.

**`corr(Sharpe, mean drawdown) = 0.900`**, and OLS gives
`mean DD(%) = −27.0 + 44.5 × Sharpe`. **`S1` states the mechanism in words** — *"the Sharpe ratio
captures the ability to lift yourself out of a hole"* — **and the regression puts a slope on it.**
`S8`'s ordering follows because its long–short Sharpe (0.98) is nearly twice its hedged long-only's
(0.56) **at matched volatility**; my ordering reverses because the OP spread's Sharpe (0.13) is a
quarter of the long-only tilt's (0.47). **Same law, opposite inputs. The conflict was never about
legs.**

### 10.2 `S5`'s abstract versus `S5`'s body on convexity

Recorded in §6.1: *"mild positive convexity"* (abstract) versus *"This mild concavity"* (body), in
**both** the 2013 draft and the 2019 published version, describing the same positive quadratic term.
**Reported, not resolved.**

### 10.3 `S9`'s own caution against `S9`'s own result

`S9` reports profitability's late-sample Sharpe of **1.16** and then writes that it *"is unsustainable."*
**An interested party's headline and its own caveat point in opposite directions; both are recorded.**

### 10.4 `S6` and `S7` versus `S6`'s and `S7`'s interest

Both are Research Affiliates papers. `S6` argues value is not dead — **the conclusion its sponsor's
product line needs.** `S7` argues factors are far riskier than investors believe — **a conclusion that
cuts against the whole smart-beta industry its sponsor sells into.** I weight `S7`'s negative findings
more heavily than `S6`'s positive ones for exactly that reason, and I say so rather than hiding the
asymmetry.

---

## 11. WHAT I WOULD WEIGHT, AND WHY

**Weighted most heavily:** my own measurement's **structural** results — drawdown-path correlations of
0.64–0.98 for every long-only decile, the U-shaped beta, the decile gradient, and the IR arithmetic —
because they are reproducible from a named free endpoint, they were validated against seven published
numbers before any new number was reported from them, they are internally consistent across three
weightings, two frequencies and ten deciles, and they do not depend on a single paper's construction.

**Weighted heavily:** `S2`'s Table A5 **as a statement about a market-neutral object**, and `S3`'s
Table 9 **as a statement about a relative object**, because both are read in full from primary text
and both declare their own construction in their own notes. The value of both is the construction, not
the figure.

**Weighted with the interest flagged at the point of use:** `S6`, `S7`, `S8`, `S9`, `S1` — every one
has an author or sponsor with a commercial position, in both directions, and I name it in §1 and again
where each is used.

**Weighted at nothing:** `S11`, which I never obtained and which reached me only through a search
summariser.

**What would change the answer.** A source reporting the **absolute, cash-benchmarked** drawdown of a
long-only **gross-profitability** portfolio — `GP`, not French's `OP` — on US data, with its
construction stated. I did not find one. If one exists, the thing to check first is its benchmark, and
the second thing is whether its "long leg" has a market beta.

---

## 12. BLOCKS AND WRONG-200s, LOGGED BY TOOL AND RESPONSE

**Four of these are genuine catalogue instances, and one is a flavour the catalogue does not yet have.**

1. **`Bash`/`curl` on `http://rnm.simon.rochester.edu/research/OSoV.pdf` → HTTP 200, 19,490 bytes,
   `text/html`.** The same call on `.../QDoVI.pdf` → HTTP 200, **19,490 bytes, byte-identical**
   (`md5 f5c08d362fc5aa5cd068dad27c266680` for both). Both were the author's rebuilt homepage
   (`<title>Robert Novy-Marx | Simon Business School</title>`). **This is the catalogue's
   `.pdf`-served-as-`text/html` flavour with a new and nastier twist: TWO DIFFERENT REQUESTED PAPERS
   RETURNED IDENTICAL BYTES AT HTTP 200.** The control that caught it was comparing the md5 of two
   different requests — **a value that must differ did not**. The working host is
   `https://mysimon.rochester.edu/novy-marx/research/`, recovered by reading the `href`s out of the
   HTML that was served instead. *(Negative control on the new host:
   `.../ZZZBOGUSPAPER.pdf` → **HTTP 404**, 20,658 bytes `text/html`, md5 distinct from both real
   papers. The new host does not fabricate.)*
2. **`Bash`/`curl` on `https://www.nber.org/system/files/working_papers/w8643/w8643.pdf` → HTTP 200,
   343,782 bytes, a genuine well-formed 48-page PDF — OF AN ENTIRELY DIFFERENT PAPER.** I guessed the
   working-paper number for Ang & Chen's *Asymmetric correlations of equity portfolios*; w8643 is Ang,
   Chen & **Xing**, *Downside Risk and the Momentum Effect*. **Caught by reading the title line, which
   is the documented remedy.** Ang & Chen therefore stays `[UNVERIFIED / weaker than snippet]` and is
   used for nothing.
3. **`Bash`/`curl` on `https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/papers.html` → HTTP
   404, 1,245 bytes.** A guessed path; no papers index at that URL. Fama & French (2015) was therefore
   not obtained (§14).
4. **`Bash`/`curl` on `https://www.columbia.edu/~aa610/papers/AsymmetricCorrelations.pdf` → HTTP 404,
   1,174 bytes `text/html`; `https://www0.gsb.columbia.edu/faculty/aang/papers/asym.pdf` → HTTP 404,
   58,033 bytes `text/html` (a styled site-error page at 404, not a paper).** Both guessed paths.
5. **`Bash`/`curl` on `https://link.springer.com/content/pdf/10.1007/s11142-018-9470-2.pdf` → HTTP 200,
   1,904,397 bytes, PDF — but the effective URL carried `?error=cookies_not_supported`.** The bytes
   were nonetheless the correct paper (`Review of Accounting Studies (2019) 24:34-112`, title line
   verified). **A consent/cookie error in the redirect chain does not always mean the payload is
   wrong — but the title line is what settles it, not the URL.**

**Two sales instruments encountered and rejected as evidence, named so the rejection is visible:**
an MSCI "Quality Time — Understanding Factor Investing" document and a Research Affiliates "Why Factor
Tilts Are Not Smart 'Smart Beta'" article, the latter arguing for its own host's Fundamental Index
against factor-replicated portfolios. **Neither is used for any return or risk figure in this brief.**
Both appeared in search results; neither was opened beyond the result snippet.

**Summariser hygiene.** `WebSearch` and `WebFetch` were used **only to locate documents**. Every figure
in this brief came from bytes I downloaded and extracted locally with `curl` and `pdftotext -layout`,
or from my own code. Three summariser claims were encountered and **none is relied on**: that Ang &
Chen find *"stocks which are smaller, have higher book-to-market ratios, or have low past returns
exhibit greater asymmetric correlations"* (unverified — and note that my own §6.2 measurement of the
same phenomenon on the actual object is independent of it); PIMCO's *"information ratio of 0.2 →
about 20 years at 80% confidence"* (not opened, not used — §8.3 computes the equivalent from measured
numbers instead); and an S&P Global claim that *"100% of quality indices' rolling 10-year return beat
their corresponding benchmarks"* (**an index provider's own marketing about its own indices, and it
contradicts my measured 52.8%/70.1% — I do not use it and I do not treat the contradiction as a
conflict between comparable objects, because one side is a sales instrument**).

---

## 13. WHAT I COULD NOT VERIFY, STATED PLAINLY

1. **I did not measure a gross-profitability tilt.** French publishes portfolios on **operating**
   profitability (`OP` = (sales − COGS − SG&A − interest expense) / book equity), not on Novy-Marx's
   **gross** profitability (`GP` = gross profits / assets), and publishes no `GP` portfolios. Round 2's
   `B2` established that the deflator and the definition decide the long leg's alpha. **Every absolute
   drawdown number I report is for `OP`.** My defence that the conclusion survives — that all ten
   deciles' drawdown paths correlate 0.64–0.98 with the benchmark's, so the drawdown is a property of
   long-only equity rather than of the sort variable — **is an argument, not a measurement of `GP`.**
2. **I could not find the absolute, cash-benchmarked drawdown of a long-only characteristic tilt
   anywhere in the literature I reached.** I searched for it directly and found only market-neutral
   and benchmark-relative objects. **I cannot prove no such source exists** — only that **eleven web
   searches and twelve documents obtained (eleven read in full, one text-searched)** did not produce
   one.
3. **`S6`'s Table 2 has a second numeric column whose header ("Bottom") the layout extraction
   separated from its values.** I therefore quote only the figures `S6`'s **prose** states verbatim
   (−54.8%, −40.6%, −39.4%, 13 yrs 6 mos, 11 yrs 10 mos, 13 months) and **do not assign the remaining
   table values to rows.** Per the prose-versus-tables rule, the tension is recorded and not resolved.
4. **`S7`'s Exhibit 12 (factor returns 1963:7–2003:6 versus 2003:7–2018:6) could not be read reliably**
   — the row labels and the numeric rows are offset by one in the layout extraction because the first
   row label carries no numbers on its own line. **I quote nothing from Exhibit 12.** Its subject is
   post-publication decay, which is `C4`'s lane.
5. **Ang & Chen (2002) was never obtained.** Four URL attempts, all logged in §12. Its claim about
   characteristic-sorted correlation asymmetry would have been the ideal peer-reviewed corroboration
   for §6.2 and **I do not have it.**
6. **`S7`'s online supplement on worst one-, three- and five-year periods was not obtained**, so the
   one piece of published horizon evidence closest to my §8.2 is known only from the main text's
   description of it.
7. **`S1`'s Exhibit B1 (historical gap moves by security) is badly column-scrambled in the layout
   extraction** — rows and values do not align. **I quote nothing from Exhibit B1.**
8. **My rolling-window frequencies (§8.2) use OVERLAPPING windows**, which are not independent. They
   are descriptive counts, exactly as `S3` reports his, and **they are not tests.** The closed-form
   `t`-statistics in §8.3 are the inferential version and they use the full non-overlapping sample.
9. **My cost sensitivity (§9.2) applies a flat annual drag, not a turnover model.** French publishes no
   turnover for these portfolios. The figures show what a given drag does; they do not estimate what
   the drag would be.
10. **The bootstrap nulls in §9.1 use B = 5,000 draws**, so their percentiles carry sampling error I
    did not quantify with a bootstrap SE. The conclusion — that realised maxDDs sit near the middle of
    the block-bootstrap null rather than in its tail — is a 15-to-20-percentile-point move and is not
    sensitive to that error, **but a margin of a few percentile points in any single row is not
    resolved.**
11. **`S8`'s cost model is undisclosed and in-house**, a point round 1's `A3` also made. Its −8.2% and
    −3.9% mean drawdowns are only as good as that model.
12. **I did not open a single filed fund document.** A prospectus's "worst quarter" for a live
    long-only quality ETF would have been primary filed evidence on sub-question 5 and **I chose the
    daily-frequency measurement (§9.3) over it**, on the judgement that 63 years of public data beats
    12 years of one product. That judgement may be wrong and the gap is real.
13. **Nothing in this brief is a measurement of, or a claim about, the programme's fixture, universe,
    costs or books.** All figures are from Ken French's public library and from the named documents.

---

## 14. WHAT I DID NOT OPEN

Separate from §13, and deliberately visible.

1. **Fama & French (2015), *A five-factor asset pricing model*, JFE 116(1).** Intended for the
   "drawdown" census; the Dartmouth papers path 404'd (§12.3) and I did not pursue another route. **Its
   drawdown count is therefore unknown**, though my expectation is zero.
2. **Ball, Gerakos, Linck & Nikolaev (2016), *Accruals, cash flows, and operating profitability*,
   JFE.** Round 2's `B2` read it in full; I restate `B2`'s figures and **did not re-open it**.
3. **Israel & Moskowitz (2013), *The role of shorting, firm size, and time on market anomalies*,
   JFE 108(2).** Round 1's `A3` read it in full and reported Sharpes, volatilities and betas but **no
   drawdown**; I restate `A3` and **did not re-open it**.
4. **Chen & Welch, *What Useful Alphas?*** Round 1's `A3` read it in full; restated, not re-opened.
5. **`S7`'s online supplement** (§13.6).
6. **Ang & Chen (2002)** (§13.5) — four failed URLs, not pursued further.
7. **Korn, Möller & Schwehm (2020), *Drawdown Measures: Are They All the Same?*** Cited by `S1` as the
   measurement reference. **Not opened**, and it is the obvious next read for anyone who wants to know
   whether maxDD, mean drawdown and time-underwater can disagree about which book is riskier — a
   question my §10.1 answers empirically and this paper presumably answers formally.
8. **Magdon-Ismail & Atiya and the analytic expected-maximum-drawdown literature** `S1` cites in its
   footnote 1. **Not opened.**
9. **Lev & Srivastava (2019)**, cited by `S6` for the claim that value has been unprofitable *"for as
   long as 30 years."* **Not opened.**
10. **EDHEC-Risk / Scientific Beta's "extreme relative risk" and "extreme tracking error" literature**
    (Amenc, Goltz, Martellini and co-authors). Search results indicate this is the one body of work
    that systematically reports **relative drawdown for long-only factor indices** — which is the
    object sub-question 1 circles. **I obtained none of it.** It is commercially affiliated (Scientific
    Beta licenses indices), so it would need the interested-party treatment. **This is the largest
    identified gap in the lane.**
11. **Any SEC-filed fund document** — prospectus, N-CSR or N-1A — for any live long-only quality,
    profitability or multifactor fund (§13.12).
12. **`S10` Hou, Xue & Zhang was text-searched, not read in full.** Only its zero drawdown count and
    its price-term hits are used.
13. **Blitz et al.'s Figure A4 and `S8`'s Figure 8** are plots of drawdown time series. I read their
    captions and the surrounding prose; **I did not attempt to digitise either plot**, so the duration
    information they contain visually is unextracted. **For `S2` this is the single thing that would
    most improve §4.1's table** — its Figure A4 probably contains the long leg's drawdown *durations*,
    which its tables do not report.
14. **Ang, Chen & Xing, *Downside Risk and the Momentum Effect* (NBER w8643)** — obtained by accident
    (§12.2), title verified, **not read**. Momentum is inherited excluded ground.

---

## 15. WHAT THIS BRIEF DOES NOT CLAIM

**It does not close or admit anything** ([R15](../../RULES.md#r15)). It does not recommend a
construction, a weighting, a decile, a concentration, a cost assumption, a holding period or a
risk target — **position sizing, risk targeting, vol targeting, stop rules and portfolio construction
are inherited excluded ground and §7.3's decile table is a description of what happened, not a
prescription.** It does not claim that French's `OP` is the programme's candidate characteristic, that
its drawdowns transfer to a `$5`-floored, dollar-volume-screened, 35.7%-dead ragged panel of 1,573
US names, or that anything measured here would reproduce on a fixture I have never seen and cannot
see. **It does not claim the literature contains no absolute long-only drawdown figure — only that eleven
web searches and twelve documents obtained did not produce one, and that the two sources which appear
to report one are reporting something else.**

**`docs/BOOK.md` and `docs/BOOK_PROP.md` are unchanged. Nothing here is elevated out of
`docs/research/`.**
