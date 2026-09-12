# C1 — combining independent weak inputs: external evidence

*External literature scan. Research only — nothing here was run, backtested or
measured on this programme's fixture. Numbers attributed to papers are theirs;
numbers I computed from their published closed forms are marked **[my
arithmetic]** and the formula is given so they can be checked.*

---

## 1. Verdict

**The gloss is half right, and the half that is wrong is the half the lead was
ranked on.** "Sixteen independent *truly useless* inputs average to useless" is
correct and is not in dispute: averaging is a linear operator, and if every
constituent has a population information coefficient of exactly zero, so does
every weighted average of them. But the programme did not measure that the 16
terms are truly useless — it measured that each is *individually undetectable*,
which is a statement about power, not about truth. On that distinction the
literature is unambiguous and points the other way: Novy-Marx's identity
(2016, eq. 8) shows that for k uncorrelated equal-volatility signals the
equal-weighted composite's t-statistic is exactly `t_combo = √k × mean(t_i)`,
so orthogonality multiplies *detectability* by √k. With 13.5–15.8 effective
inputs that is a 3.7–4.0× multiplier; the nine price signals at 2.87 effective
inputs get only 1.69×. **Independence is the asset in a combination, not the
liability — the gloss inverted the sign of its own orthogonality result, and by
its own numbers the 16 OHLC terms are the better combination candidate and the
nine price signals the worse one.** So much for the encouraging half. The
decisive catch, and the reason this lead still deserves its last-place ranking
unless the design below is adopted: **that same √k is exactly what you get for
free by choosing the 16 signs in-sample.** Under the null that all 16 are
worthless, signing each to predict positive in-sample returns puts the
composite's t-statistic at E = √(2/π)·√16 = **3.19** with sd 0.60 — a "highly
significant" backtest from pure noise, and *statistically indistinguishable*
from 16 genuine independent signals each with true t ≈ 0.8. A combination study
of unsigned weak inputs is therefore not merely a search space; it is a search
space whose null is centred well above 2. It becomes a hypothesis the moment
the signs and the weights are declared in advance — and only then. See §6 and §8.

---

## 2. When does forecast combination help, and when can it not?

### The exact statement, in returns

Novy-Marx (2016) §3.1 derives the cleanest formulation for this exact setting.
For n signals whose single-signal strategy active returns are normal,
uncorrelated, and equal-volatility, a composite signal with weights ω produces a
strategy whose returns are the ω-weighted portfolio of the single-signal
strategies (his §2.1.3 — an *exact* correspondence between "integrated"
composites and "siloed" allocations, not an approximation), and its sample
t-statistic is

```
t_ω = ω'·t / ‖ω‖₂            (eq. 7)

equal weights  ω = 1:     t_EW = (Σ tᵢ)/√k = √k · mean(tᵢ)      (eq. 8)
signal weights ω = t:     t_SW = ‖t‖₂ = √(Σ tᵢ²)                (eq. 9)
```

Three consequences, and they answer the question completely:

1. **Combination cannot manufacture signal.** If E[tᵢ] = 0 for all i, then
   E[t_EW] = 0. The programme's gloss is correct at this literal reading.
2. **Combination multiplies detectability by √k.** If every constituent shares a
   common true per-signal t of μ (same sign, known in advance), the composite's
   expected t is √k·μ. Sixteen independent signals each at a true t of 0.49 —
   utterly invisible individually — produce a composite at t = 1.96.
   **[my arithmetic from eq. 8]**
3. **Equal weights are the minimum-variance combination and signal weights the
   ex-post mean-variance-efficient one** (Novy-Marx §3.1, explicitly). This is
   the same object as the forecast-combination puzzle, in returns.

The portfolio-theoretic twin is Grinold's fundamental law, `IR = IC·√BR`,
generalised for correlated signals to `IC_composite = IC·√K / √(1+(K−1)ρ)`:
at ρ = 0 the gain is the full √K, and it collapses toward 1 as ρ → 1. This is
why "13.5–15.8 effective inputs out of 16" is a *good* number and "2.87 out of
9" is a bad one. (Grinold 1989; Grinold–Kahn; Clarke–de Silva–Thorley 2002 add
the transfer coefficient for implementation constraints.)

### The forecast-combination puzzle

The best treatments are Timmermann (2006, *Handbook of Economic Forecasting*
ch. 4) for the theory and Claeskens, Magnus, Vasnev & Wang (2016,
*International Journal of Forecasting*) for the resolution. The puzzle: simple
equal weights routinely beat estimated "optimal" weights out of sample. Smith &
Wallis (2009) attributed it to estimation error in the weights; Claeskens et al.
give the rigorous version — once you derive the optimal weights *acknowledging
that they must be estimated*, the estimated-optimal combination carries extra
bias **and** variance, and the equal-weighted combination can dominate in MSE
even when the true optimal weights are not equal. Timmermann's own summary is
that "simple combinations that ignore correlations between forecast errors often
dominate more refined combination schemes".

Its asset-pricing counterpart is DeMiguel, Garlappi & Uppal (2009, RFS 22(5)
1915–1953): across 14 optimising models and 7 datasets, **none consistently beat
1/N** on Sharpe, certainty equivalent or turnover; the estimation window needed
for sample mean-variance to beat 1/N is ~3,000 months for 25 assets and ~6,000
months for 50. In returns, the empirical evidence for the combination puzzle is
Rapach, Strauss & Zhou (2010, RFS 23(2) 821–862): the simple *average* of
individual predictive-regression forecasts beats the "kitchen sink" model that
uses all predictors jointly, with statistically and economically significant
out-of-sample gains over the historical mean.

### When it cannot help

- When the constituents are truly zero (point 1 above).
- When they are highly correlated: the √K becomes √(K/(1+(K−1)ρ)) and dies.
- **When the signs are estimated from the same sample.** This is the case that
  matters here, and §3/§6 quantify it. It is not a variance problem; it is a
  bias problem, and no amount of data reduces it.

---

## 3. The multiple-testing deflation

### The headline hurdles

| Source | Recommended t-hurdle | Basis |
|---|---|---|
| Harvey, Liu & Zhu (2016, RFS 29(1) 5–68) | **> 3.0** | 316 published factors; multiple-testing framework (Bonferroni/Holm/BHY); cutoff rises through time |
| Hou, Xue & Zhang (2020, RFS 33(5) 2019–2133) | **2.78** (BHY, 5%) | 452 anomalies replicated |
| Chordia, Goyal & Saretto (2020, RFS 33(5) 2134–2179) | **3.8** time-series, **3.4** cross-sectional | >2 million randomly generated trading strategies on real data |

Hou–Xue–Zhang's result is the strongest published negative in the classical
mould and is worth stating precisely, because its construction is the mirror
image of this programme's: **with microcaps mitigated via NYSE breakpoints and
value-weighted returns, 65% of 452 anomalies fail even the plain |t| > 1.96
hurdle (96% of the trading-frictions category); at the 2.78 multiple-test
hurdle the failure rate is 82.1%.** Even the survivors have economic magnitudes
"much smaller than originally reported". Note what is doing the work: *NYSE
breakpoints and value weighting*, i.e. the two choices this programme has
explicitly refused (§8).

### The strongest counter-negative — do not skip this

The deflation literature is itself contested, and by serious people. Reporting
only the hurdle-raisers would be exactly the selective citation this house
objects to.

- **Chen (2024), "Do t-Statistic Hurdles Need to be Raised?"** (Federal Reserve
  Board; arXiv:2204.10275v4, 6 Apr 2024). Central claim: calls to raise hurdles
  are **weakly identified**, because published data are censored — results
  failing the existing hurdle are unobserved, so πF (the share of false factors)
  must be extrapolated, and values of πF from 0 to 2/3 imply nearly identical
  distributions in the observed region. Statistics that target only *published*
  findings are strongly identified: he estimates published t-stats are biased
  upward **by at most 28%**, and the FDR among published predictors is **at most
  22%, with 95% confidence**, robust across 10 alternative specifications. His
  theoretical result is sharp: at a 5% FDR target, the hurdle should be raised
  **iff** πF exceeds the share of t-stats above 1.96. Each additional test is
  also another data point about factors in general — more testing is not
  automatically more bad news.
- **Chen & Zimmermann (2022, Critical Finance Review 11(2) 207–264)**: 319
  predictors reproduced from code; of the 161 clearly significant originals,
  **98% reproduce with t > 1.96**; regression of reproduced on original t-stats
  gives slope 0.90, R² 83%. Coding error and fraud are ruled out as sources of
  the zoo.
- **Jensen, Kelly & Pedersen (2023, JF 78(5) 2465–2518)**: a Bayesian hierarchical
  replication model concludes the majority of factors *do* replicate, cluster
  into 13 themes, work out of sample in 93 countries, and — the interesting bit —
  that the evidence is **strengthened, not weakened, by the large number of
  observed factors**, because the factors are correlated and inform one another.

**Where this leaves the concrete number.** The classical literature's 2.78–3.8
range is defensible as a *design* hurdle even if Chen is right that it is not
identifiable as a *publication* hurdle, and this programme has an independent
reason to prefer the conservative end: it is spending its own capital, not
seeking a referee's approval, so the asymmetry of loss favours the higher bar.
But none of 2.78 / 3.0 / 3.4 / 3.8 is the right hurdle for a *combination*,
because all of them price selection bias only. §6 gives the right one.

---

## 4. Does ML return prediction survive costs and the exclusion of microcaps?

### What Gu, Kelly & Xiu (2020, RFS 33(5) 2223–2273) actually claimed

Universe: ~30,000 US stocks, **1957–2016**, monthly, 94 stock-level
characteristics × 8 macro series + 74 industry dummies = **920 predictors**;
30-year out-of-sample test period. Headline results, from the NBER w25398
version I read directly:

- Monthly stock-level out-of-sample R² : **0.33%–0.40%** for trees and neural
  nets (NN3 = 0.40%). OLS on all features gives **−3.46%** — worse than
  forecasting zero.
- Long-short decile spread, NN4: **value-weighted** 2.26%/month, annualised
  Sharpe **1.35** (Table 7); **equal-weighted** 3.33%/month, Sharpe **2.45**
  (Table A.9).
- Turnover: **114%–127% per month** (NN4: 126.8% VW, 114.2% EW; Table 8).
- **No transaction costs are applied anywhere in the paper.** GKX say only that
  "value-weight portfolios are less sensitive to trading cost considerations".

### The decisive numbers are in GKX's own appendix

Table A.10 repeats the equal-weight portfolios **excluding stocks below the NYSE
20th percentile**. NN4's long-short spread falls from **3.33% → 2.26%/month** and
Sharpe from **2.45 → 1.69**. That is a **32% loss of mean and 31% loss of Sharpe
from one size screen, before a single basis point of cost, at ~114% monthly
turnover.** GKX's own defence of the result is that R² among the top-1,000
stocks is 0.52%–0.70%, i.e. the *forecast accuracy* is not illiquidity-driven;
but the *portfolio* gains plainly are, in part, and they never net them.

### The follow-up that closes it

- **Avramov, Cheng & Metzker (2023, Management Science 69(5) 2587–2619),
  "Machine Learning vs. Economic Restrictions".** Deep-learning signals "extract
  profitability from difficult-to-arbitrage stocks and during high
  limits-to-arbitrage market states"; **excluding microcaps, distressed stocks,
  or high-volatility episodes considerably attenuates profitability**, and
  performance "further deteriorates in the presence of reasonable trading costs
  because of high turnover and extreme positions". This is precisely the paper
  the lead asked me to find. *I could not retrieve the exact attenuation
  percentages — SSRN returned HTTP 403 and Management Science is paywalled; the
  qualitative claim above is quoted from the abstract as returned by search, and
  the magnitudes remain unverified by me.*
- **Blitz, Hanauer, Hoogteijling & Howard (2023), "The Term Structure of Machine
  Learning Alpha"** (J. Financial Data Science 5(4) 40). ML models have high
  full-sample **gross** alphas, but **net of costs performance is close to zero
  after 2004**; training on longer prediction horizons (3/6/12-month) plus
  efficient trading rules restores significant positive net returns. Authors are
  at Robeco, an asset manager — **[SALES INSTRUMENT — mitigated]**: the finding
  is *against* their commercial interest in ML products and it is peer-reviewed,
  so I weight it, but the "our design choices fix it" framing is house marketing
  and should be discounted.
- **Chen & Velikov (2019/2023), "Accounting for the Anomaly Zoo: a Trading Cost
  Perspective".** 120 anomalies, effective bid-ask spreads from ISSM/TAQ.
  **The average equal-weighted long-short portfolio nets −3 bp/month
  post-publication after costs.** Cost-optimised versions (value weighting +
  buy/hold spreads) net **4–13 bp/month**; the strongest cost-optimised anomalies
  net **10–20 bp/month**. And they note their effective-spread costs are a *lower
  bound* for a market-order trader, before short-sale costs of 10–20 bp/month.
- **Novy-Marx & Velikov (2016, RFS 29(1) 104–147), "A Taxonomy of Anomalies and
  Their Trading Costs":** most anomalies **under 50% monthly turnover** generate
  significant net spreads when cost-mitigated; **few above it do.** Execution
  costs of 20–57 bp for the mid-turnover group. The single most effective simple
  mitigation is a **buy/hold spread**.
- **Nagel (2025), "Seemingly Virtuous Complexity in Return Prediction"** (NBER
  w34104). The most surgical negative in the whole scan. Kelly, Malamud & Zhou's
  "virtue of complexity" (JF 79(1) 459–503, 2024) claims out-of-sample
  performance *improves* with parameterisation past the interpolation threshold.
  Nagel shows that when P ≫ T the random-Fourier-feature forecast collapses
  algebraically into a similarity-weighted average of the T training returns; in
  a 12-month window similarity is dominated by temporal proximity, so the
  "learned" strategy **is** a volatility-timed momentum strategy that does not
  learn from the training data at all. His falsification is the one this house
  would design: **run the same method on artificial data with reversals instead
  of momentum — it builds the same volatility-timed momentum strategy, and loses
  money.** That is a mechanism test, not a significance test, and it is decisive.

**Verdict for §4: no.** The affirmative case is gross, value-weighted-optional,
untraded, and concentrated in the size decile a retail per-share cost model
cannot touch. Every attempt to net it out lands between "close to zero" and
"−3 bp/month".

---

## 5. Simple vs complex out of sample

The weight of evidence favours simple, with one honest caveat.

- **For simple:** DeMiguel–Garlappi–Uppal (1/N beats 14 optimisers on 7
  datasets); Rapach–Strauss–Zhou (forecast average beats the kitchen sink);
  Claeskens et al. and Smith–Wallis (estimated weights lose to equal weights on
  MSE once estimation is accounted for); Timmermann's survey.
- **For complex:** GKX's nonlinear models genuinely beat OLS and beat linear
  regularised models on R², and the gap traces to nonlinear predictor
  interactions. Kelly–Malamud–Zhou argue for a "virtue of complexity". Kozak,
  Nagel & Santosh (2020, JFE) find that *characteristics-sparse* SDFs with four
  or five factors **cannot** summarise the cross-section — "not enough redundancy
  among cross-sectional return predictors" — but a small number of **principal
  components** of the candidate factor set approximates the SDF well.
- **The caveat, and it cuts toward simple:** Nagel (2025) dismantles the flagship
  complexity result by showing it never learned; Blitz et al. show the complex
  models' edge is a turnover artefact post-2004; and GKX's own strongest numbers
  are the equal-weighted, microcap-inclusive, uncosted ones.

The Kozak–Nagel–Santosh result is the most interesting one for this programme,
because it says the right simple object is **not a hand-picked sparse subset but
a low-dimensional projection of the whole declared set** — which is a
pre-specifiable form (§6).

---

## 6. Combination forms that need NO fitted parameter

Ranked by how little discretion they leave. Every one of these can be written
down in a pre-registration before the runner exists, which is what R8 requires.

| Form | Free parameters | Literature standing |
|---|---|---|
| **Equal-weight cross-sectional z-score composite** of a declared signal set, signs declared in advance | none (given the set and the signs) | Minimum-variance combination (Novy-Marx §3.1); the 1/N result (DeMiguel et al.); the combination puzzle's winner |
| **Rank-average composite** — average each name's cross-sectional percentile rank | none | Stambaugh & Yuan (2017, RFS 30(4) 1270–1315) build both mispricing factors this way: average rankings within a cluster. Robust to the outliers and fat tails a z-score inherits |
| **First principal component** of the declared signal set's covariance, sign fixed by a declared convention | none, but the loadings *are* estimated from data — needs a rolling/expanding window declared in advance | Kozak–Nagel–Santosh: a few PCs of the candidate factor set approximate the SDF well; sparse characteristic subsets do not |
| **Risk-parity across single-signal strategies** (weight ∝ 1/σ of each signal's own strategy) | none beyond a declared vol window | Novy-Marx footnote 4: this is the natural generalisation of equal-weighting when constituent vols differ |
| **Count/score composite** — sum of binary "this signal is in its favourable tail" indicators (Piotroski F-score form) | none, given declared thresholds | Widely used; Novy-Marx names F-score as an instance and it inherits the same bias analysis |

**Three warnings that attach to all of them.**

1. **Equal weights are not innocent.** They are innocent of *weight*-fitting.
   They are not innocent of *sign*-fitting or of *set*-selection, and those are
   the larger biases (see the table in §7). Novy-Marx's Figure 1 shows the pure
   overfitting bias from equal-weighting all n signals is already "significantly
   more acute than the more familiar multiple testing bias".
2. **Signal-weighting is strictly worse.** Weighting each signal by its own
   in-sample strength is the ex-post mean-variance portfolio; its null
   distribution is `‖t‖₂` rather than `√k·mean(t)`, which is uniformly larger
   (L2 ≥ L1/√k, tight only when all constituents are equal). It is exactly the
   "more freedom to overweight good signals" that Novy-Marx shows drives the
   critical value up.
3. **Novy-Marx's own conclusion is not "don't combine".** Verbatim: "while one
   should combine multiple signals they believe in, one should not believe in a
   combination of signals simply because they backtest well together." The
   marginal contribution of each constituent must be evaluated *individually*.
   That is a design instruction, and it is compatible with a disciplined test.

---

## 7. How to floor a combination study honestly

### The floor this programme already uses is the wrong null for a combination

The exact best-of-N permutation floor prices **selection** bias: "I looked at N
candidates and am reporting the best." Novy-Marx's central point is that a
composite carries a *second, larger* bias — **overfitting bias from signing each
constituent to predict positive in-sample returns** — which is present *even when
the researcher uses every signal considered and selects nothing*. A best-of-N
floor does not see it at all.

The two biases compound multiplicatively. His power law: **combining the best k
of n candidate signals is about as biased as selecting the single best of n^k
candidates.**

### Concrete hurdles for this programme's own signal counts

From Novy-Marx's closed forms — eq. (10) for pure selection, eq. (15) for the
equal-weighted pure-overfitting case, eq. (12) for the signal-weighted case.
**[my arithmetic; formulas reproduced below so they can be checked]** He notes
that empirical critical values from real CRSP returns run *slightly above* these
model values, because of excess kurtosis and heteroskedasticity absent from the
model — so treat these as lower bounds.

```
eq (10)  t*(best 1-of-n)        = Φ⁻¹( (1 − p/2)^(1/n) )
eq (15)  t*(equal-wt, k = n)    = √(2/π)·√n + √(1 − 2/π)·Φ⁻¹(1 − np/(n+1))
eq (12)  t*(signal-wt, k = n)   = √( χ²ₙ quantile at 1 − p )
```

| n | best-1-of-n (selection only) | **equal-weight composite of all n** | signal-weighted composite of all n |
|---|---|---|---|
| 9 (the price family) | 2.77 | **3.42** | 4.11 |
| 13.5 (16 OHLC terms, effective) | 2.90 | **3.94** | 4.87 |
| 16 (16 OHLC terms, nominal) | 2.95 | **4.20** | 5.13 |
| 52 (the whole catalogue) | 3.30 | **6.75** | 8.36 |

Two things fall out of this table.

- The best-1-of-52 value, **3.30**, independently reproduces the published
  hurdles: Harvey–Liu–Zhu's 3.0, Hou–Xue–Zhang's 2.78, Chordia–Goyal–Saretto's
  3.4. That is a useful sanity check on the arithmetic and on those papers.
- **The 5% hurdle for a sign-fitted equal-weight composite of the 16 OHLC terms
  is ~4.2, not 1.96 and not 3.0.** Under the null, such a composite's t-statistic
  is centred at **√(2/π)·√16 = 3.19** with sd 0.60 — worthless inputs backtest at
  t ≈ 3.2 as a matter of arithmetic. Novy-Marx reports constructions where random
  signals backtest above t = 5 and 5% significance requires **t > 7**.

### The value of pre-registering the signs, quantified

This is the single most actionable number in the report. **[my arithmetic from
eq. 8; 50%-power convention, i.e. the true effect at which the composite's
*expected* t reaches the hurdle]**

| 16-term equal-weight composite | 5% hurdle | Per-constituent true t needed |
|---|---|---|
| Signs chosen in-sample | **4.20** | **≈ 0.82** |
| Signs declared before looking | **1.96** (t_EW ~ N(0,1) exactly) | **≈ 0.49** |

Pre-registering the 16 signs collapses the null from centre-3.19 to centre-0 and
roughly **halves the per-signal true effect the study can detect** — from ~0.82
to ~0.49. It is the difference between a study that can find something and a
study that cannot. It costs nothing but discipline, and this programme already
has the R8 machinery for it.

### The published floors, and which suit correlated candidates

- **White's Reality Check** (2000, Econometrica 68(5) 1097–1126) — stationary
  bootstrap over the full candidate set. Known to be conservative: a single poor
  candidate drags the null.
- **Hansen's SPA** (2005, JBES 23(4) 365–380) — studentises and removes
  irrelevant poor candidates; strictly more powerful than the Reality Check.
- **Romano & Wolf stepwise** (2005, Econometrica 73(4) 1237–1282) — **the right
  family when candidates are highly correlated**, because the bootstrap
  resamples candidates *jointly* and so absorbs their dependence rather than
  assuming independence; the stepwise structure then identifies as many
  significant candidates as possible instead of one. Hsu, Hsu & Kuan (2010, JEF)
  give a stepwise-SPA that is more powerful still.
- **Harvey & Liu, "Lucky Factors"** (2021, JFE 141(2) 413–435) — bootstrap with
  a first-step **orthogonalisation** of the candidate against the incumbent
  model, so the null of no incremental explanatory power holds *exactly
  in-sample*. This is the closest published analogue to what a combination study
  needs: it prices the marginal contribution of one more input, which is
  precisely the question "does adding signal 17 do anything".
- **Deflated Sharpe Ratio** (Bailey & López de Prado 2014) — adjusts the Sharpe
  threshold for number of trials, skew, kurtosis and sample length; the
  companion Minimum Backtest Length says how long a backtest must be before a
  given Sharpe is not expected from N trials alone. **Practical caveat:** it
  needs the *number of independent trials*, which nobody honestly knows, and it
  assumes a normal-approximation extreme-value distribution — exactly the
  approximation this programme has already rejected in favour of exact
  enumeration.

### What I would actually recommend as this programme's floor

Keep the exact permutation machinery — it is better than all of the above at
what it does — but **change what it permutes**. A combination study's null draw
must reproduce *both* biases:

1. draw n synthetic signals with no predictive power on the real bar grid,
   satisfying the same eligibility mask as the observed events (the programme's
   own D347/D351 rule);
2. **sign each one in-sample exactly as the treatment does**;
3. combine them with the identical declared form;
4. score, and enumerate/repeat.

The resulting null will centre near 3.19 for n = 16, and the exact enumeration
will give the p95 without the sample-p95 downward bias the D373 rule guards
against. This is the same construction as Novy-Marx's empirical experiment, and
it is the same construction as the "falsification audit against synthetic
zero-predictability reference classes" proposed in Nikolopoulos (2026),
arXiv:2604.15531 — a single-author unrefereed preprint I would not otherwise
cite, listed only because its recipe corroborates the one above.

---

## 8. Does any of this transfer to OUR universe — bluntly

**Mostly no, and where it does the transfer is unfavourable.**

- **Every affirmative result in §4 and §5 is monthly, and most are
  value-weighted.** This programme is daily and equal-weighted. Blitz et al.'s
  central finding is that ML alpha's **term structure** is the whole story:
  short-horizon models had the best gross alphas and net ~zero after 2004.
  Novy-Marx & Velikov put the break at **50% monthly turnover**. A daily
  cross-sectional composite is on the wrong side of both lines by a wide margin,
  and nothing in the literature supports it there.
- **The one universe fact that flatters this programme:** the strongest negative,
  Hou–Xue–Zhang's 65%/82% failure rate, is produced *by* NYSE breakpoints and
  value weighting. Their result is therefore not "anomalies are false" but
  "anomalies live in small names". This programme deliberately holds the small
  names. That is not vindication — it is the reason Chen & Velikov's **−3 bp/month
  for the average equal-weighted long-short after costs** is the single most
  directly transferable number in this document, and it is a killing one.
- **Dead-inclusive at 43.5% is a genuine edge over most of this literature.**
  Chen & Velikov's post-publication decay and McLean–Pontiff's ~50% transient
  component are survivorship-adjacent effects that a dead-inclusive fixture
  handles honestly.
- **Per-share IBKR costs invert the usual analysis.** The literature nets in
  basis points; a per-share charge scales inversely with price, which is the
  programme's own D284 finding. Corwin–Schultz on the names actually held
  (the D285 rule) is the right measurement and is *not* something any of these
  papers do.
- **The nine price signals at 2.87 effective inputs are not a combination
  candidate.** √2.87 = 1.69 of detectability gain against a sign-fitting hurdle
  of 3.42 — the bias grows faster than the benefit. The 16 OHLC terms at
  13.5–15.8 effective are the only family in the catalogue where the arithmetic
  is even close, and only with pre-registered signs.
- **What none of this literature has that the programme has:** an exact
  enumerable null, a lag audit in a second implementation, and a sign audit in
  money. Novy-Marx's bias is *invisible* to a t-statistic and *visible* to a
  synthetic-signal null of the kind this programme already builds. The
  programme's methodology is better than the literature's here; what it lacks is
  the right *null object*, not the machinery.

**The one disciplined test the evidence supports.** Not a search over 6,348
combinations — that is the thing every paper in §3 and §7 says will fail. One
pre-registered composite: the 16 OHLC terms, equal-weighted cross-sectional
ranks (not z-scores — fat tails), **every sign declared in writing before the
runner exists**, floored against a synthetic-signal null that itself performs the
in-sample signing, reported gross first per this house's signal criterion, with
the per-constituent detectability arithmetic (0.49) stated in the pre-registration
as the effect size the test can and cannot see. If it does not clear its own
null's p95 by more than 2 SE, it is UNRESOLVED, and the avenue is not closed —
only the principal closes an avenue.

---

## 9. Sources

**Multiple testing and deflation**
- Harvey, Liu & Zhu, "…and the Cross-Section of Expected Returns", RFS 29(1) 5–68, 2016. https://academic.oup.com/rfs/article/29/1/5/1843824 · https://people.duke.edu/~charvey/Research/Published_Papers/P118_and_the_cross.PDF **[PEER-REVIEWED]**
- Hou, Xue & Zhang, "Replicating Anomalies", RFS 33(5) 2019–2133, 2020. https://theinvestmentcapm.com/uploads/1/2/2/6/122679606/houxuezhang2019rfs.pdf **[PEER-REVIEWED]**
- Chordia, Goyal & Saretto, "Anomalies and False Rejections", RFS 33(5) 2134–2179, 2020. https://academic.oup.com/rfs/article/33/5/2134/5739455 **[PEER-REVIEWED]**
- **Novy-Marx, "Testing Strategies Based on Multiple Signals", March 2016** (NBER w21329 as "Backtesting Strategies Based on Multiple Signals"). https://mysimon.rochester.edu/novy-marx/research/MSES.pdf · https://www.nber.org/papers/w21329 **[WORKING PAPER — read in full; all §7 formulas and the CRSP 1995–2014 / 100,000-draw experiments are from this PDF]**
- Chen, "Do t-Statistic Hurdles Need to be Raised?", arXiv:2204.10275v4, Apr 2024. https://arxiv.org/abs/2204.10275 **[WORKING PAPER — final publication venue not verified]**
- Chen & Zimmermann, "Open Source Cross-Sectional Asset Pricing", Critical Finance Review 11(2) 207–264, 2022. https://www.openassetpricing.com/ · https://github.com/OpenSourceAP/CrossSection **[PEER-REVIEWED + PRIMARY DATA DOC]**
- Jensen, Kelly & Pedersen, "Is There a Replication Crisis in Finance?", JF 78(5) 2465–2518, 2023. https://onlinelibrary.wiley.com/doi/full/10.1111/jofi.13249 · code https://github.com/bkelly-lab/ReplicationCrisis **[PEER-REVIEWED]** (AQR hosts a copy; the authors are affiliated with AQR — note the interest, the journal is not.)

**Floors and test procedures**
- White, "A Reality Check for Data Snooping", Econometrica 68(5), 2000. **[PEER-REVIEWED]**
- Hansen, "A Test for Superior Predictive Ability", JBES 23(4), 2005. **[PEER-REVIEWED]**
- Romano & Wolf, "Stepwise Multiple Testing as Formalized Data Snooping", Econometrica 73(4), 2005. http://www-stat.wharton.upenn.edu/~steele/Courses/956/Resource/MultipleComparision/RomanoWolf05.pdf **[PEER-REVIEWED]**
- Hsu, Hsu & Kuan, stepwise-SPA for technical analysis, JEF 2010. https://homepage.ntu.edu.tw/~ckuan/pdf/Step-SPA-20090720.pdf **[PEER-REVIEWED]**
- Harvey & Liu, "Lucky Factors", JFE 141(2) 413–435, 2021. https://people.duke.edu/~charvey/Research/Published_Papers/P146_Lucky_factors.pdf **[PEER-REVIEWED]**
- Bailey & López de Prado, "The Deflated Sharpe Ratio", 2014. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551 **[WORKING PAPER]**
- Nikolopoulos, "Spurious Predictability in Financial Machine Learning", arXiv:2604.15531, Apr 2026. https://arxiv.org/abs/2604.15531 **[WORKING PAPER — UNVERIFIED, single-author unrefereed preprint; cited only for methodological corroboration]**

**Forecast combination**
- Timmermann, "Forecast Combinations", Handbook of Economic Forecasting vol. 1 ch. 4, 135–196, 2006. https://www.sciencedirect.com/science/article/abs/pii/S1574070605010049 **[PEER-REVIEWED]**
- Claeskens, Magnus, Vasnev & Wang, "The forecast combination puzzle: A simple theoretical explanation", IJF, 2016. https://www.sciencedirect.com/science/article/abs/pii/S0169207016000327 **[PEER-REVIEWED]**
- Smith & Wallis, "A Simple Explanation of the Forecast Combination Puzzle", OBES, 2009. **[PEER-REVIEWED]**
- DeMiguel, Garlappi & Uppal, "Optimal Versus Naive Diversification", RFS 22(5) 1915–1953, 2009. https://academic.oup.com/rfs/article-abstract/22/5/1915/1592901 **[PEER-REVIEWED]**
- Rapach, Strauss & Zhou, "Out-of-Sample Equity Premium Prediction: Combination Forecasts and Links to the Real Economy", RFS 23(2) 821–862, 2010. https://academic.oup.com/rfs/article-abstract/23/2/821/1604687 **[PEER-REVIEWED]**
- Grinold, "The Fundamental Law of Active Management", JPM 1989; Clarke, de Silva & Thorley, "Portfolio Constraints and the Fundamental Law", 2002. https://joim.com/wp-content/uploads/emember/downloads/p0158.pdf **[PEER-REVIEWED]**

**Machine learning, costs and complexity**
- Gu, Kelly & Xiu, "Empirical Asset Pricing via Machine Learning", RFS 33(5) 2223–2273, 2020. https://www.nber.org/system/files/working_papers/w25398/w25398.pdf **[PEER-REVIEWED — Tables 7, 8, A.9, A.10 read directly from the NBER PDF]**
- Avramov, Cheng & Metzker, "Machine Learning vs. Economic Restrictions", Management Science 69(5) 2587–2619, 2023. https://pubsonline.informs.org/doi/abs/10.1287/mnsc.2022.4449 **[PEER-REVIEWED — abstract only; full text paywalled and SSRN returned 403]**
- Blitz, Hanauer, Hoogteijling & Howard, "The Term Structure of Machine Learning Alpha", J. Financial Data Science 5(4) 40, 2023. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4474637 **[PEER-REVIEWED, authors at Robeco — SALES-ADJACENT, finding runs against their commercial interest]**
- Robeco's own write-ups of the above: https://www.robeco.com/en-us/insights/2023/07/the-term-structure-of-machine-learning-alpha and https://www.robeco.com/en-int/insights/2024/12/better-by-design-why-human-choices-matter-for-return-predictions-via-machine-learning **[SALES INSTRUMENT — asset-manager marketing; use the SSRN paper instead]**
- Novy-Marx & Velikov, "A Taxonomy of Anomalies and Their Trading Costs", RFS 29(1) 104–147, 2016. https://www.nber.org/system/files/working_papers/w20721/w20721.pdf **[PEER-REVIEWED]**
- Chen & Velikov, "Accounting for the Anomaly Zoo: a Trading Cost Perspective", Sept 2019. https://jacobslevycenter.wharton.upenn.edu/wp-content/uploads/2019/09/Accounting-for-the-Anomaly-Zoo.pdf **[WORKING PAPER — read in full; later published as "Zeroing in on the Expected Returns of Anomalies", JFQA, which I did not verify]**
- Kelly, Malamud & Zhou, "The Virtue of Complexity in Return Prediction", JF 79(1) 459–503, 2024. https://onlinelibrary.wiley.com/doi/full/10.1111/jofi.13298 **[PEER-REVIEWED]**
- Nagel, "Seemingly Virtuous Complexity in Return Prediction", NBER w34104, Aug 2025. https://www.nber.org/papers/w34104 · https://bfi.uchicago.edu/wp-content/uploads/2025/08/BFI_WP_2025-104.pdf **[WORKING PAPER — abstract read verbatim]**
- Kozak, Nagel & Santosh, "Shrinking the Cross-Section", JFE, 2020. https://cpb-us-w2.wpmucdn.com/voices.uchicago.edu/dist/f/575/files/2020/07/SCS.pdf **[PEER-REVIEWED]**
- Stambaugh & Yuan, "Mispricing Factors", RFS 30(4) 1270–1315, 2017. https://academic.oup.com/rfs/article/30/4/1270/2965095 **[PEER-REVIEWED]**
- Alpha Architect's summary of Novy-Marx: https://alphaarchitect.com/backtesting-strategies-based-multiple-signals-beware-overfitting-biases/ **[SALES INSTRUMENT — asset-manager blog; the primary PDF is linked above and was used instead]**

### What I could not verify
- **Avramov, Cheng & Metzker's exact magnitudes** — the attenuation percentages from excluding microcaps and the net-of-cost Sharpe figures. SSRN 403'd, Management Science is paywalled. The qualitative claim in §4 is from the abstract; the numbers are not in hand.
- **Green, Hand & Zhang (2017, RFS)** on how many of 94 characteristics carry independent information once microcaps are excluded — I know of this paper and it is directly relevant to §5, but my web-search budget was exhausted before I could retrieve it. **Not cited above because I will not quote a number I did not read.** Worth one lookup by whoever picks this up.
- **The exact publication venue of Chen (2024)** and of Chen & Velikov's final journal version.
- **Whether any of Novy-Marx's critical values have been re-derived for daily
  rebalancing.** His experiments are annual-rebalance, 20-year, CRSP. The
  t-statistic distribution theory (§3.1) does not depend on the rebalance
  frequency under his assumptions, but the empirical excess over the model
  (which he attributes to kurtosis and heteroskedasticity) plausibly grows at
  daily frequency. Nobody appears to have checked this. It is checkable here.
