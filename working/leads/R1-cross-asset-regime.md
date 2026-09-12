# R1 — cross-asset regime state: external evidence

*External-literature scan, 2026-09-09. Research only: nothing was run, no fixture
was touched. Every claim below carries a provenance tag; where I could not verify
a number I say so rather than smoothing it over.*

---

## 1. Verdict

**The outside world does not support D404 as specified, and the reason is horizon,
not sign.** The literature on credit spreads and the term structure is close to
unanimous that these variables carry information about *macroeconomic activity at
horizons of two to eight quarters*, and that their documented equity-return
predictability is (a) concentrated at the same business-cycle frequencies, (b)
in-sample far more than out-of-sample, and (c) largely dead or unstable in modern
subsamples. The single most-cited horizon results are Gilchrist–Zakrajšek (2012),
whose excess bond premium is a "year-ahead" predictor of output, and
López-Salido–Stein–Zakrajšek (2017), whose credit-sentiment effect is dated in
*years* (t−2 predicts t and t+1). A 20-trading-day gate sits roughly an order of
magnitude inside that band. Meanwhile Goyal–Welch (2008) and its 2024 update
place the default spread and term spread squarely in the group of predictors that
fail out of sample against a historical-mean benchmark. On the volatility
question the literature is more interesting than fatal but still unfriendly:
Bekaert–Engstrom–Xu (2022) find credit spreads map onto *economic uncertainty*,
while Bekaert–Hoerova (2014) find that it is the *variance premium*, not the
conditional variance, that predicts equity returns — i.e. the credit spread loads
on the volatility component that does **not** forecast returns. Confidence that a
naive 3-gate, 20-day version of D404 clears the programme's own signal criterion:
**low, ~15–20%.** Confidence that *something* survives if the horizon is stretched
to 60–125 days and the gate is orthogonalised against realised equity vol:
moderate, maybe 35%. The construction also has two mechanical defects (§9) that
would produce a biased gate before any of this economics matters.

---

## 2. THE HORIZON QUESTION

This is where D404 is most exposed. Every strong, refereed result I found places
the predictability at **quarters to years**, not weeks.

| Result | Documented horizon | Source |
|---|---|---|
| GZ excess bond premium → real GDP growth: 100 bp EBP ⇒ >1.5 pp lower growth | **next 4 quarters** ("year-ahead") | Gilchrist & Zakrajšek 2012, AER 102(4) [PEER-REVIEWED] |
| Credit-market sentiment → economic activity | **t−2 predicts t and t+1, i.e. 1–3 years** | López-Salido, Stein & Zakrajšek 2017, QJE 132(3) [PEER-REVIEWED] |
| Yield-curve slope → real activity / recessions | **4–6 quarters lead**; "beyond one quarter there is no match for the term structure" | Estrella–Mishkin lineage, as summarised by NY Fed [PRIMARY DATA DOC] |
| Term spread → equity premium | raw spread poor OOS; only the **low-frequency (trend) component** works, over 1 month–2 years | Faria & Verona 2020, J. Financial Markets 50 [PEER-REVIEWED] |
| Variance risk premium → equity returns | **strongest at the quarterly horizon**, R² >15% quarterly (1990–2005) | Bollerslev, Tauchen & Zhou 2009, RFS 22(11) [PEER-REVIEWED] |
| Business-cycle sector rotation | business-cycle **stages**, i.e. quarters–years | Molchanov 2024, Int. J. Fin. Econ. [PEER-REVIEWED] |

Three things follow.

**(a) 20 days is not a horizon these variables have been shown to live at.** I
found no refereed study documenting credit-spread or curve-slope predictability
of *aggregate equity returns* at a one-month horizon that survives out of sample.
The closest positive is Faria–Verona's wavelet **trend** of the term spread, which
they report as working from one month out — but the object that works there is the
low-frequency component *extracted by a two-sided-looking filter class*, and they
explicitly find the **raw** term spread is a poor OOS predictor. D404 uses the raw
level versus a trailing median, which is nearer to the thing that fails than the
thing that works.

**(b) The one predictor with genuine short-horizon power is the wrong one.**
Bollerslev–Tauchen–Zhou's variance risk premium peaks at *quarterly*, and they
report it dominates the **default spread** at that horizon. So even in the
short-horizon corner of this literature, the credit variable is the one being
beaten, by a volatility-derived variable — which is exactly the confound D404 is
supposed to clear.

**(c) The effective sample is tiny at this horizon and this is not fixable.** A
market-level gate is one bet per window. 2010-01-04 to 2026-08-26 is ~4,180 daily
bars ⇒ ~209 non-overlapping 20-day windows. Three binary gates define 8 states; a
"risk-off" state that is 25% of time gets ~52 independent windows. With overlapping
20-day forward returns the standard errors are worse than the nominal N suggests.
This is the same breadth ceiling the programme keeps hitting (2.2 independent ETF
instruments, ~10 over a held book) showing up in the *time* dimension instead of
the cross-section. **Whatever D404 measures, its own null distribution will be
wide, and a p95 from a sampled null will be biased lenient (D373's rule applies
with force here).**

**Bottom line for §2: the design as pre-registered is asking a months-to-years
signal a weeks-scale question. If the runner is written unchanged, the most likely
outcome is a noisy near-zero, and the second most likely is a spurious positive
driven by two or three drawdown episodes (2011, 2015-16, 2018Q4, 2020, 2022).**

---

## 3. Is it just volatility?

The honest answer is *not exactly — and the part it is not is the part that
doesn't help you.*

**The decomposition result.** Bekaert & Hoerova (2014, J. Econometrics 183(2))
split the squared VIX into the conditional variance of stock returns and the
equity variance premium. Their finding, stated at abstract level: **the variance
premium predicts stock returns, while the conditional variance predicts economic
activity and financial instability.** [PEER-REVIEWED]

**Where credit spreads land in that split.** Bekaert, Engstrom & Xu (2022,
Management Science 68(6)) build risk-aversion and uncertainty measures from a
joint equity/corporate-bond no-arbitrage model. Their finding: **equity variance
risk premia are very informative about risk aversion, whereas credit spreads and
corporate bond volatility are highly correlated with economic uncertainty.**
[PEER-REVIEWED]

Put the two together and the implication for D404 is unfriendly: the credit spread
sits on the *uncertainty / conditional-variance* side of the decomposition — the
side Bekaert–Hoerova find predicts activity and instability, **not** returns. The
return-predicting component is the variance risk premium, which requires option
data the programme does not have and has never used.

**The raw comovement number.** Monthly correlation between VIX and ICE BofA US
High Yield OAS is reported at ~0.71 (R² ≈ 0.51) by a practitioner site
[UNVERIFIED — cassinicap.com, a vendor tool page, not a paper]. I could not find a
refereed number for this specific pair, but 0.7 is consistent with the structural
(Merton) prior that spreads are a levered function of equity vol. **Treat ~50% of
HY-spread variance as shared with equity vol as a working figure, not a citation.**

**The strongest statement in the *other* direction** is that ~half of HY-spread
variation is *not* VIX, and that Bekaert–Engstrom–Xu need corporate-bond data
*jointly with* equity data to identify their factors at all — i.e. the bond market
is not redundant. Gilchrist–Zakrajšek's whole contribution is that the EBP is the
part of the spread *not* attributable to expected default, and it forecasts
activity beyond standard controls. So there is real non-vol information in credit.
The problem is that its documented payoff is macro forecasting at annual horizons,
not equity timing at monthly ones.

**What this means for D404's own orthogonality test.** The pre-registration's
framing — "over and above what realised equity volatility already forecasts" — is
the right test, and it is the one the programme already used to withdraw a
dispersion state that turned out to be vol in disguise. But note the asymmetry the
literature implies: **realised equity vol is itself a weak-to-negative return
predictor** (Moreira–Muir 2017 report that lagged factor volatility does *not*
predict factor returns, only future volatility). So "beats realised vol" is a low
bar that a noisy variable can clear by accident. The control must be tighter than
that — see §9.

---

## 4. The effect as documented

| Source | Year | Sample period | Universe | Horizon | Magnitude | Cost treatment |
|---|---|---|---|---|---|---|
| Gilchrist & Zakrajšek, AER 102(4):1692–1720 [PEER-REVIEWED] | 2012 | 1973–2010, monthly/quarterly | US corporate bonds → US macro | 4 quarters ahead | 100 bp EBP ⇒ >1.5 pp lower real GDP growth over next 4 qtrs | none (macro forecasting) |
| López-Salido, Stein & Zakrajšek, QJE 132(3):1373–1426 [PEER-REVIEWED] | 2017 | **1929–2015**, annual | US aggregate | **t−2 → t, t+1** | elevated credit sentiment ⇒ decline in activity; predictable mean reversion in spreads | none |
| Goyal & Welch, RFS 21(4):1455–1508 [PEER-REVIEWED] | 2008 | ~1872–2005 (annual), 1927–2005, 1965–2005 | US aggregate equity premium (cap-weighted) | monthly, annual, 5-year | default yield spread (dfy), default return spread (dfr), term spread (tms) among the 15 that "predicted poorly both IS and OOS for 30 years" | none — but they note the models "would not have helped an investor... profitably time the market" |
| Goyal, Welch & Zafirov, RFS 37(11):3490–3557 [PEER-REVIEWED] | 2024 | through **end-2021**; 17 original + 29 post-2008 variables from 26 papers | US aggregate equity premium | monthly/annual | >1/3 of the new variables no longer significant **even in-sample**; of those that are, **half have poor OOS** | none |
| Campbell & Thompson, RFS 21(4):1509–1531 [PEER-REVIEWED] | 2008 | US, long sample | US aggregate | monthly | with sign restrictions, OOS power "small but economically meaningful" for a mean-variance investor | none |
| Bollerslev, Tauchen & Zhou, RFS 22(11):4463–4492 [PEER-REVIEWED] | 2009 | **1990–2005** | S&P 500 (cap-weighted) | **quarterly (peak)** | VRP explains >15% of quarterly excess-return variation; **dominates the default spread** | none |
| Bekaert & Hoerova, J. Econometrics 183(2):181–192 [PEER-REVIEWED] | 2014 | post-1990 (VIX era) | S&P 500 | monthly–quarterly | variance premium predicts returns; **conditional variance does not** (predicts activity/instability) | none |
| Bekaert, Engstrom & Xu, Mgmt Sci 68(6):3975–4004 [PEER-REVIEWED] | 2022 | US equities + corporate bonds | US | multiple | credit spreads ↔ **economic uncertainty**; VRP ↔ **risk aversion** | none |
| Faria & Verona, J. Fin. Markets 50 [PEER-REVIEWED]; Bank of Finland DP 7/2018 [WORKING PAPER] | 2018/2020 | US, long monthly sample | US aggregate | 1 month – 2 years | **raw term spread poor OOS**; wavelet low-frequency trend is a robust OOS predictor | claims statistical *and* economic significance; I did not verify the cost assumptions |
| Molchanov, "The myth of business cycle sector rotation", Int. J. Fin. Econ. [PEER-REVIEWED] | 2024 | **1948–2022, 15 business cycles** | US industry portfolios | cycle stages | **perfect-foresight** cycle timing = 0.16%/mo risk-adjusted *before* costs, vs 0.18%/mo for a simple market-timing rule; generalised industry-lead predictability "not different from chance" | explicitly: outperformance "quickly diminishes after allowing for transaction costs" |
| Cederburg, O'Doherty, Wang & Yan, JFE [PEER-REVIEWED] | 2020 | US, **103 equity strategies** | US equity factors | monthly | OOS vol-managed versions earn **lower** certainty-equivalent returns and Sharpe than unmanaged; cause = structural instability in the spanning regressions | OOS implementation, turnover implicit |
| Situ, "Credit-Spread Timing between High-Yield Bonds and Treasuries: Timing HYG vs IEF" SSRN 5815822 [WORKING PAPER — unrefereed] | 2025/26 | HYG era only (post-2007) | HYG/IEF pair | monthly rotation | ratio vs 9-period MA, +1% threshold, beats 50/50 benchmark | not verified; short sample; single-pair, plateau-selected parameters |

**Gap I could not close:** I tried five routes (NBER PDF, NBER conference PDF, OUP
advance PDF, SSRN, Welch's own slide decks) and **could not extract the exact
per-variable IS/OOS R² for dfy, dfr and tms from Goyal–Welch or Goyal–Welch–Zafirov.**
Every PDF returned as undecoded binary and SSRN/OUP returned 403. What is verified
is the *classification* (they are in the failing group) and the headline
conclusions quoted above, not the decimals. If those decimals matter to the
decision, the numbers are in the public dataset on Amit Goyal's site (Excel/CSV
through 2025) — reproducing the regression is a ten-minute job on data the
programme could download, and would be worth more than any further searching.

---

## 5. The strongest published negative

Ranked by how much damage each does to D404 specifically.

1. **Goyal–Welch (2008) + Goyal–Welch–Zafirov (2024).** The default spread and the
   term spread are *named members* of the group that fails out of sample against a
   historical-mean benchmark, and the 2024 update through 2021 finds the situation
   has got worse, not better. This is the reference class D404's CREDIT and CURVE
   gates belong to. [PEER-REVIEWED]

2. **Molchanov (2024), "The myth of business cycle sector rotation."** This is
   close to a direct kill for the DEFENSIVE gate. 15 cycles, 1948–2022: *even with
   perfect foresight about the business-cycle stage*, sector rotation earns
   0.16%/month risk-adjusted before costs — **less than a naive market-timing rule
   at 0.18%** — and it "quickly diminishes after allowing for transaction costs and
   incorrectly timing the business cycle." When they let any industry's excess
   return predict any other's, predictability is "not significantly different than
   what would be expected by random chance." [PEER-REVIEWED]

3. **Cederburg, O'Doherty, Wang & Yan (2020, JFE).** 103 strategies: volatility
   management does not survive honest OOS implementation, because the spanning
   regressions are structurally unstable. This matters twice over — it is the
   negative for the *baseline* D404 must beat, and it is a warning that any
   time-varying-exposure rule of this shape tends to be an artefact of in-sample
   coefficient estimation. [PEER-REVIEWED]

4. **Novy-Marx (2014, JFE 112(2):137–146).** Sunspots, planetary conjunctions,
   Manhattan weather, El Niño and the party of the President all show "significant
   power" predicting anomaly performance in standard OLS predictive regressions.
   Predictive regressions of real returns on *simulated* regressors reject the null
   far too often. D404 is exactly this shape: a handful of persistent market-level
   state variables, regressed on forward returns, on ~200 effective observations.
   **Standard t-stats are not admissible evidence here.** [PEER-REVIEWED]

5. **Cakici, Fieberg, Neumaier, Poddig & Zaremba (2025, JF), "Pockets of
   Predictability: A Replication."** The original Farmer–Schmidt–Timmermann (2023,
   JF) result — that predictability is local in time, which is the closest thing in
   the literature to a theoretical licence for regime gating — is reported by the
   replication to have used a **two-sided kernel and in-sample estimation, leaking
   future information into the forecasts**, contrary to the paper's own
   description. The flagship "predictability comes in regimes" paper has a
   look-ahead problem. [PEER-REVIEWED]

6. **Downing, Underwood & Xing (2009, JFQA 44(5):1081–1102).** The folk claim that
   "credit leads equities" is backwards at high frequency: **hourly stock returns
   lead bond returns** for junk- and BBB-rated non-convertibles, and the
   predictable bonds are those of firms in financial distress. The corporate bond
   market is the *less* informationally efficient of the two. For a *daily-bar*
   gate this is directly on point — it argues the equity book already contains the
   credit information by the time HYG prints. [PEER-REVIEWED]

7. **Dacco & Satchell (1999, J. Forecasting 18(1):1–16), "Why do regime-switching
   models forecast so badly?"** Non-linear regime models fit beautifully in sample
   and are beaten by a random walk out of sample. See §7. [PEER-REVIEWED]

---

## 6. Post-2010 decay

What is actually established:

- **The decay predates 2010 and is not specifically a QE story.** The recurring
  finding is that economic indicators "work well only until the 1970s and lose
  predictive power thereafter" (per the DIW / Int. J. Forecasting line on the
  instability of economic vs technical indicators) [PEER-REVIEWED, verified at
  abstract level only]. Goyal–Welch's framing is the same: poor performance "for
  30 years" as of 2008, i.e. since ~1975.
- **Goyal–Welch–Zafirov (2024) extends the verdict through end-2021**, which covers
  three-quarters of the programme's fixture. More than a third of post-2008
  published predictors no longer work even in-sample when the sample is extended;
  half the survivors fail OOS. This is the most directly relevant post-2010
  evidence I found. [PEER-REVIEWED]
- **Predictors revive in crises.** The same literature notes economic indicators
  predict the equity premium "quite well in crisis periods." That is a warning, not
  a comfort: it means a 2010–2026 backtest of a credit gate will have its result
  determined by 2011, 2015–16, 2018Q4, 2020 and 2022 — a handful of episodes. The
  programme's own concentration discipline (names to reach half the P&L, top-1
  share) has a time analogue that D404 must report: **how many distinct episodes
  produce the gate's entire benefit.** If it is four, it is not a result.
- **The curve gate has a documented modern failure.** The 2s10s inverted in
  2022 and stayed inverted into late 2024 — the longest sustained inversion on
  record — with no NBER-dated recession following as of mid-2026 [UNVERIFIED as to
  the NBER dating; widely reported]. Commentary attributes this to QE-compressed
  term premia making the slope a different object than it was pre-2008
  [SALES INSTRUMENT / broker commentary: US Bank, TD, Credit Suisse]. D404's CURVE
  gate is `log(IEF/SHY)`, a *price-ratio proxy* for the belly-vs-front slope, and
  it sits entirely inside the period where the slope's classical interpretation is
  most contested.
- **No study I found tests HYG/IEF, IEF/SHY or a defensive/cyclical ETF ratio as an
  equity-book gate in a refereed venue.** The only direct HYG-vs-IEF timing work I
  located is an unrefereed SSRN working paper (§4) with a plateau-selected
  parameter and a post-2007 sample. **That absence is itself informative: this
  construction has not been vetted anywhere I can point to.**

---

## 7. Regime classifiers — worth the machinery?

**No, not on this evidence, and not for this programme.**

- The classic negative, **Dacco & Satchell (1999)**, is titled "Why do
  regime-switching models forecast so badly?" — non-linear regime techniques give
  good in-sample fits and are "usually outperformed by random walks or random walks
  with drift" out of sample. That paper is on FX, but the mechanism (a small
  misclassification probability destroys the conditional-mean advantage) is generic
  and has never been convincingly rebutted for return forecasting.
- The positive HMM literature I found is overwhelmingly **arXiv preprints and
  practitioner posts** reporting self-selected backtests — e.g. one claiming 19.41%
  annualised, Sharpe 1.22, 19.5% maxDD over Nov-2004 to Jan-2026 [WORKING PAPER /
  UNVERIFIED, arXiv 2605.27848]. None of these carry a pre-registration, a cost
  model I can inspect, or a null distribution. By the house standard they are not
  evidence.
- **The one refereed regime-flavoured result that is most cited — Farmer, Schmidt &
  Timmermann's "pockets of predictability" — has a published replication (Cakici et
  al. 2025, JF) reporting a two-sided-kernel look-ahead leak.**
- Mechanically, an HMM buys you a *probabilistic, smoothed* state rather than a
  hard threshold. On ~209 independent 20-day windows, the extra parameters (a 2×2
  transition matrix plus per-state means and variances = ~8 free parameters
  minimum) are estimated on a sample that cannot support them. A trailing-median
  threshold has **zero** free parameters beyond the window, which is the right
  choice at this sample size.

**Recommendation: do not build the machinery. D404's trailing-median threshold is
the statistically correct instrument for the amount of data available. If the
threshold version shows nothing, an HMM will not find it — it will only make the
overfit harder to see.**

---

## 8. Does it transfer to OUR universe

Bluntly, against the four bullets.

**1,573 US single names, daily, dead-inclusive, ragged.** The predictability
literature is almost entirely about the **cap-weighted aggregate** (S&P 500 or CRSP
value-weighted excess return). None of the horizon or magnitude numbers in §4 were
estimated on an equal-weighted dead-inclusive small/mid panel. The *direction* of
transfer is arguably favourable: credit-spread widening is documented to hit
small-cap, high-beta and low-quality names hardest (flight to quality) [the
academic backing here is the distress-risk / leverage-overlap literature; the
specific "large beats small when HY spreads widen" statement I found only on
practitioner sites — SSGA, Neuberger Berman, RBA — all **[SALES INSTRUMENT]**]. So
the gate might well have *more* to bite on in this universe than in the S&P 500.
**But that same fact makes the confound worse, not better:** an equal-weighted
dead-inclusive book is a levered bet on exactly the risk factor the credit spread
measures, so a gate that "works" may just be a beta-timing artefact with the
book's own drawdowns on both sides of the equation.

**Equal-weighted, never value-weighted; $5 floor + dollar-volume window.** The
literature offers nothing on this universe. The $5 floor is relevant in one
specific way: the names most sensitive to credit conditions are the ones that fall
through the floor during exactly the risk-off episodes the gate is meant to catch.
**That is a survivorship channel inside the gate's own test** — the eligibility
mask moves with the state variable. The programme's own memory note
(*null-lives-in-the-tradeable-universe*, D347→D351) is precisely this failure mode:
a state variable whose apparent power comes from the composition of the eligible
set changing under it.

**IBKR per-share costs, bp inversely with price.** A gate is a *turnover reducer*,
not a turnover adder — suppressing exposure in risk-off states removes trades. So
the cost transfer is favourable in sign. But CLAUDE.md's rule bites: **cost-cutting
is not edge-sharpening.** A gate that raises net Sharpe by trading less has to be
reported as such, with edge-per-unit-exposure separated from cost-per-trade, or it
will read as signal when it is thrift. And the exposure figure has to be in the
headline — a gate that is off 30% of the time and shows a higher CAGR has said
nothing until exposure is beside it (D279, D284).

**Breadth saturates near 2.2 / ~10 instruments.** This is the binding one. A
market-level gate adds **one** time-series bet, applied to every name at once. It
does not add breadth; it modulates the breadth you already have. Three gates built
from six ETFs, two of which (CREDIT and DEFENSIVE) are both proxies for the same
risk-appetite factor, are far fewer than three independent instruments — the
Bekaert–Engstrom–Xu result implies CREDIT and equity vol share an uncertainty
factor, and defensive/cyclical rotation is the equity market's own expression of
the same thing. **My prior is that the three gates carry closer to 1.2 independent
signals than 3.**

---

## 9. What would sharpen or kill D404

Concrete, in the design's own terms.

**Two mechanical defects to fix before the runner is written.**

1. **Dividend/distribution drift will bias every gate toward "risk-off."** If the
   ETF closes are *unadjusted*, `log(HYG/IEF)` drifts down mechanically at roughly
   the distribution-yield gap. Current aggregator figures: HYG ~5.9%, IEF ~4.0%,
   XLU ~2.8%, XLP ~2.6%, XLK ~0.5%, XLY ~0.8% [UNVERIFIED — stockanalysis.com /
   dividend.com aggregators, not fund documents]; over 2010–2020 the HYG−IEF gap
   was materially wider (IEF yielded ~2%). That is a downward drift of ~2–5%/yr in
   CREDIT and ~2%/yr in DEFENSIVE, **against a 252-day trailing median whose centre
   sits ~126 bars in the past**. A monotone drift of *d* per year puts the current
   value roughly *d*/2 below its own trailing median for free. The gate would
   therefore read risk-off well over half the time for reasons that have nothing to
   do with credit. **This is the programme's own `fixtures-disagree-on-corporate-
   action-basis` note, in a new place.** Fix: use total-return (adjusted) series, or
   build the state from cumulated log *return* differences rather than price ratios,
   and *assert* in the runner that the state is above its median on 45–55% of bars
   in a no-signal shuffle.
2. **`(XLU+XLP)/(XLY+XLK)` is a sum of share prices, not a portfolio.** The ratio
   is dominated by whichever fund has the higher share price and moves with any
   split. Use `0.5*(r_XLU + r_XLP) − 0.5*(r_XLY + r_XLK)` cumulated, so the object
   is an equal-weighted long/short return, and assert it is invariant to a
   synthetic 2-for-1 split of any leg.

**Four things that would sharpen it.**

3. **Report the horizon curve, not the horizon.** Compute forward-drift
   discrimination at h ∈ {5, 10, 20, 40, 60, 125, 252} days. The literature's
   prediction is monotone-increasing in h, peaking at 125–252. **If the h=20 number
   is the peak of that curve, that is a red flag for overfitting, not a
   confirmation** — nothing in the outside evidence predicts a 20-day peak. If the
   curve rises into 125 days, that is the strongest possible corroboration
   available from this data and would justify re-specifying D404 at a quarterly
   gate. **This one addition converts D404 from a pass/fail into a test that can
   agree or disagree with the outside world.**
4. **Make the volatility control the right one.** "Beats realised equity vol" is a
   low bar because realised vol is itself close to a non-predictor of returns
   (Moreira–Muir). Control instead on: (i) trailing 20d and 63d realised market
   vol, (ii) the *level* of the equity book's own drawdown, and (iii) the trailing
   63-day market return — the programme has already measured that this last one
   forecasts **rebound** (block corr −0.23), so a credit gate that is merely
   picking up "the market just fell" will look like a gate and be a reversal signal
   with the wrong sign. Report the gate's marginal contribution after each control
   separately, not jointly.
5. **Enumerate the null.** Per CLAUDE.md and D361: a time rotation of a *single
   market-level series* over ~4,180 bars is `Td−1` offsets — **enumerate it, do not
   sample.** The SE is then exactly 0 and the p95 is exact. This is the one place
   where D404's structure is unusually favourable: three market-level series, all
   enumerable, ~6 min a cell. Do not report a 200-draw p95 here.
6. **Report the episode concentration.** The time analogue of "names to reach half
   the P&L": how many distinct risk-off *episodes* (contiguous runs of the gate
   being off) produce half the benefit, and name the largest one with its dates. If
   2020Q1 alone carries it, the answer is known before any statistic is computed.
   Section 6 says this is the likely outcome.

**Three things that would kill it, and should be treated as pre-registered kill
conditions.**

7. **DEFENSIVE fails first and should be tested first, cheaply.** Molchanov (2024)
   is close to dispositive: even *perfect* business-cycle foresight yields 0.16%/mo
   before costs, below a naive timing rule. Before building the three-gate runner,
   run the Stage-0 premise check the programme's own memory prescribes: **measure
   whether the DEFENSIVE state is leading or coincident** — cross-correlate the
   defensive/cyclical return spread against the equal-weighted book's own return at
   lags −20…+20. My expectation, and the literature's, is that the peak is at lag 0
   or slightly *lagging*. **A coincident indicator cannot gate.** If the peak is at
   lag ≤ 0, drop DEFENSIVE from the design rather than carrying it as a third gate
   that inflates the multiple-testing surface.
8. **If the equity book leads HYG at daily frequency, CREDIT is redundant.**
   Downing–Underwood–Xing found stocks lead bonds intraday for junk credits. Run
   the same lead-lag on daily bars: `corr(book return_t−k, HYG−IEF return_t)` for
   k = −5…+5. If the credit series lags the book, the gate is reading the book's own
   past, and the programme has already measured that the book's own trailing return
   forecasts *rebound*. That would predict a gate with the **wrong sign**, which is
   a specific, falsifiable, checkable prediction — write it into the pre-reg.
9. **Multiple testing.** Three gates × two directions × a horizon choice × a
   lookback choice is a surface Novy-Marx's sunspots would clear. Pre-register the
   *single* headline cell (which gate, which horizon, which threshold) before
   looking, and report the other cells as a family with the enumerated null applied
   to all of them.

**What I would actually recommend.** Re-specify D404 before writing the runner:
one gate (CREDIT), on total-return series, tested across the full horizon curve
with the enumerated time-rotation null and the trailing-63d-return control, with
DEFENSIVE demoted to a Stage-0 lead/lag premise check and CURVE dropped or held
back (its modern behaviour is contested and Goyal–Welch put it in the failing
group). That is a smaller study, it answers the question the outside evidence
actually leaves open, and it does not spend the fixture's degrees of freedom on
two gates the literature has already argued against.

---

## 10. Sources

**Safety note:** none of the pages or search results I read contained text
addressed to me, instructions, or attempts to direct my behaviour. Nothing was
downloaded, no forms were submitted, no accounts created. Several PDFs were
auto-cached by the fetch tool as a side effect of reading; I did not open or run
anything.

**Peer-reviewed**
- Gilchrist & Zakrajšek, "Credit Spreads and Business Cycle Fluctuations", AER 102(4):1692–1720, 2012 — https://www.aeaweb.org/articles?id=10.1257%2Faer.102.4.1692 [PEER-REVIEWED]
- López-Salido, Stein & Zakrajšek, "Credit-Market Sentiment and the Business Cycle", QJE 132(3):1373–1426, 2017 — https://academic.oup.com/qje/article-abstract/132/3/1373/3787666 [PEER-REVIEWED]
- Goyal & Welch, "A Comprehensive Look at the Empirical Performance of Equity Premium Prediction", RFS 21(4):1455–1508, 2008 — https://academic.oup.com/rfs/article-abstract/21/4/1455/1565737 [PEER-REVIEWED]
- Goyal, Welch & Zafirov, "A Comprehensive 2022 Look at the Empirical Performance of Equity Premium Prediction", RFS 37(11):3490–3557, 2024 — https://academic.oup.com/rfs/article/37/11/3490/7749383 [PEER-REVIEWED]
- Campbell & Thompson, "Predicting Excess Stock Returns Out of Sample: Can Anything Beat the Historical Average?", RFS 21(4):1509–1531, 2008 — https://academic.oup.com/rfs/article-abstract/21/4/1509/1567518 [PEER-REVIEWED]
- Bollerslev, Tauchen & Zhou, "Expected Stock Returns and Variance Risk Premia", RFS 22(11):4463–4492, 2009 — https://public.econ.duke.edu/~boller/Published_Papers/rfs_09.pdf [PEER-REVIEWED]
- Bekaert & Hoerova, "The VIX, the variance premium and stock market volatility", J. Econometrics 183(2):181–192, 2014 — https://www.sciencedirect.com/science/article/abs/pii/S0304407614001110 [PEER-REVIEWED]
- Bekaert, Engstrom & Xu, "The Time Variation in Risk Appetite and Uncertainty", Management Science 68(6):3975–4004, 2022 — https://pubsonline.informs.org/doi/10.1287/mnsc.2021.4068 [PEER-REVIEWED]
- Faria & Verona, "The yield curve and the stock market: Mind the long run", J. Financial Markets 50, 2020 — https://www.sciencedirect.com/science/article/abs/pii/S138641811930134X [PEER-REVIEWED]
- Molchanov, "The myth of business cycle sector rotation", Int. J. Finance & Economics, 2024 — https://onlinelibrary.wiley.com/doi/full/10.1002/ijfe.2882 (open copy: https://mro.massey.ac.nz/server/api/core/bitstreams/1f32a859-5ef9-442d-a5f8-ac8e0f5b1a83/content) [PEER-REVIEWED]
- Cederburg, O'Doherty, Wang & Yan, "On the performance of volatility-managed portfolios", JFE, 2020 — https://www.sciencedirect.com/science/article/abs/pii/S0304405X2030132X [PEER-REVIEWED]
- Moreira & Muir, "Volatility Managed Portfolios", J. Finance, 2017 — https://www.anderson.ucla.edu/documents/areas/adm/Volatility%20Managed%20Portfolios.pdf [WORKING PAPER version of a PEER-REVIEWED article]
- Novy-Marx, "Predicting anomaly performance with politics, the weather, global warming, sunspots, and the stars", JFE 112(2):137–146, 2014 — https://www.sciencedirect.com/science/article/abs/pii/S0304405X14000208 [PEER-REVIEWED]
- Farmer, Schmidt & Timmermann, "Pockets of Predictability", J. Finance, 2023 — https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.13229 [PEER-REVIEWED]
- Cakici, Fieberg, Neumaier, Poddig & Zaremba, "Pockets of Predictability: A Replication", J. Finance, 2025 — https://onlinelibrary.wiley.com/doi/10.1111/jofi.13484 [PEER-REVIEWED]
- Downing, Underwood & Xing, "The Relative Informational Efficiency of Stocks and Bonds: An Intraday Analysis", JFQA 44(5):1081–1102, 2009 — https://www.ruf.rice.edu/~yxing/bondinfoeff.pdf [PEER-REVIEWED]
- Dacco & Satchell, "Why do regime-switching models forecast so badly?", J. Forecasting 18(1):1–16, 1999 — https://onlinelibrary.wiley.com/doi/abs/10.1002/(SICI)1099-131X(199901)18:1%3C1::AID-FOR685%3E3.0.CO;2-B [PEER-REVIEWED]
- Hong, Torous & Valkanov, "Do industries lead stock markets?", JFE 83(2):367–396, 2007 — https://www.sciencedirect.com/science/article/abs/pii/S0304405X06001383 ; authors' 2014 OOS extension note — https://rady.ucsd.edu/_files/faculty-research/valkanov/Note_10282014.pdf [PEER-REVIEWED / author note]

**Working papers**
- Faria & Verona, "The equity risk premium and the low frequency of the term spread", Bank of Finland Research DP 7/2018 — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3430161 [WORKING PAPER]
- "Understanding the Excess Bond Premium", arXiv:2412.04063, 2024 — https://arxiv.org/abs/2412.04063 [WORKING PAPER]
- Situ, "Credit-Spread Timing between High-Yield Bonds and Treasuries: Timing HYG vs IEF with Price-Ratio and Return-Spread Signals", SSRN 5815822 — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5815822 [WORKING PAPER — unrefereed, short sample, plateau-selected parameter; read as a hypothesis, not evidence]
- "Regime-Based Portfolio Allocation Using Hidden Markov Models and Reinforcement Learning", arXiv:2605.27848 — https://arxiv.org/abs/2605.27848 [WORKING PAPER — self-reported backtest, no null, no cost model; not evidence by this house's standard]

**Primary data / official**
- Amit Goyal's equity-premium prediction dataset (through 2025, Excel/CSV/Matlab) — https://sites.google.com/view/agoyal145 [PRIMARY DATA DOC] — **this is the cheapest way to close the §4 gap**
- NY Fed, "The Yield Curve as a Leading Indicator: FAQ" — https://www.newyorkfed.org/medialibrary/media/research/capital_markets/ycfaq.pdf [PRIMARY DATA DOC]
- Federal Reserve FEDS Notes, "Recession Risk and the Excess Bond Premium" (2016) and its update — https://www.federalreserve.gov/econresdata/notes/feds-notes/2016/recession-risk-and-the-excess-bond-premium-20160408.html [PRIMARY DATA DOC]

**Sales instruments / practitioner (cited only where flagged)**
- AQR, "Market Timing: Sin a Little" — https://www.aqr.com/-/media/AQR/Documents/Insights/White-Papers/Market-Timing-Sin-a-Little.pdf [SALES INSTRUMENT]
- SSGA, "Why Credit Spreads Matter for Stock Selection" — https://www.ssga.com/library-content/pdfs/insights/why-credit-spreads-matter-for-stock-selection.pdf [SALES INSTRUMENT]
- Neuberger Berman, "The Importance of Monitoring Credit Spreads" — https://www.nb.com/handlers/documents.ashx?id=684d6ab9-5da9-4d8d-9111-505599c9d5c2 [SALES INSTRUMENT]
- Alpha Architect summary of Cederburg et al. — https://alphaarchitect.com/the-performance-of-volatility-managed-portfolios/ [SALES INSTRUMENT — practitioner blog]
- Cassini Capital, VIX vs HY OAS correlation tool (source of the ~0.71 / R²≈0.51 figure) — https://www.cassinicap.com/t-plus/credit-spread-and-vix/index.php [UNVERIFIED]
- thetrading.tools / systemtrader.co / hostilecharts credit-spread trackers, source of the folk claim "credit spreads lead equities" — [SALES INSTRUMENT; contradicted at daily/intraday frequency by Downing–Underwood–Xing]
- ETF distribution yields (HYG 5.89%, IEF 4.01%, XLU 2.81%, XLP 2.57%, XLK 0.49%, XLY 0.79%, Sept 2026) — stockanalysis.com / dividend.com aggregators [UNVERIFIED — not fund fact sheets; directionally certain, decimals not]

**Could not verify**
- Exact per-variable IS/OOS R² for dfy, dfr, tms in Goyal–Welch (2008) and Goyal–Welch–Zafirov (2024). Five fetch routes failed (PDFs returned undecoded; SSRN and OUP returned HTTP 403). Only the *classification* and the headline conclusions are verified.
- Gilchrist–Zakrajšek's own equity-return regressions (as opposed to output-growth regressions): the PDF would not decode. The "year-ahead output growth" horizon and the 1.5 pp magnitude are verified from Fed FEDS Notes summaries; the equity-return specifics are not.
- The claimed NBER non-dating of a recession after the 2022–2024 inversion is widely reported but I did not confirm it against the NBER Business Cycle Dating Committee page.
