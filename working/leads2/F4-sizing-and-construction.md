# F4 — position sizing and portfolio construction: external evidence

*Commissioned 2026-09-09. Research only — nothing here is a measurement on this fixture, and under
R15 this brief closes nothing and admits nothing. Where I read the paper's own text I say so; where
I have only a search snippet or a summariser's rendering I say that too, in §11.*

---

## 1. Verdict

**Equal weight is leaving very little on the table on the Sharpe axis, and essentially nothing on
the Calmar axis, but it is leaving something real on the cost axis — and the cost lever is the one
the programme has already half-pulled.** The canonical negative (DeMiguel–Garlappi–Uppal) is
decisive against anything that needs an estimated *mean*: at this programme's dimensions the
required estimation window is off by two to three orders of magnitude, and no shrinkage, Bayesian
or robust variant closes that gap. But DGU's negative does **not** reach the cheap corner of the
space — weights that use only *variances*, no correlations and no means. That corner (Kirby–Ostdiek
volatility timing; inverse-vol within a leg) is the one place in this literature where a
non-equal-weight rule beats 1/N *net of costs*, and the documented size of the win is small:
roughly **+0.01 to +0.06 Sharpe on a base of 0.51**. Volatility targeting's documented benefit is
overwhelmingly a *tail and drawdown* benefit, not a return benefit, and it exists only where a
leverage effect exists (equities and credit — negligible for bonds, FX, commodities). The most
important negative result in this brief is arithmetic rather than empirical: **under fixed-fraction
sizing the Calmar ratio is invariant to the leverage scalar** — E[MaxDD] and return both scale
linearly with exposure — so no amount of vol targeting, Kelly fractioning or risk parity can move
Calmar at all. Magdon-Ismail and Atiya's closed form says a Calmar of 18.9 over one year *is* a
Sharpe of about 7. The prop track's hurdle is a demand for a different return *shape*, and sizing
cannot supply shape. The genuinely large, well-evidenced lever is Novy-Marx and Velikov's buy/hold
band, which cut turnover 41% and trading costs 42% across 23 anomalies at small gross cost — which
is precisely the rank buffer the programme already found empirically.

---

## 2. Is 1/N hard to beat, and under what conditions

### The canonical statement, with its actual numbers

DeMiguel, Garlappi and Uppal (RFS 2009) evaluate **fourteen** optimal-portfolio models across
**seven** empirical datasets of monthly returns and find *none* consistently better than 1/N on
Sharpe ratio, certainty-equivalent return, **or turnover**. I read the paper's own text; the
operative results are:

- They derive analytically the **critical estimation-window length** M\* needed for sample
  mean-variance to beat 1/N on CEQ. It is a function of three things only: **N**, the ex-ante
  Sharpe of the tangency portfolio **S\***, and the Sharpe of 1/N **S_ew**.
- Calibrated to US stock-market data (S\* = 0.15 monthly, S_ew = 0.12): **>3,000 months for
  N = 25**, **>6,000 months for N = 50**. In practice these models are fitted on 60 or 120 months.
- Even the flattering calibrations are brutal. At S\* = 0.40, S_ew = 0.20: **>200 months at N = 25,
  ~600 at N = 50, >1,200 at N = 100**. At S\* = 0.20, S_ew = 0.10: **~1,000 months at N = 25,
  ~2,000 at N = 50**. Making 1/N four times worse than the tangency portfolio barely helps —
  270 / 530 / 1,060 months at N = 25/50/100.
- The scaling is roughly **linear in N** and steeply decreasing in the *gap* between S\* and S_ew.

### The conditions under which optimisation wins — stated concretely

DGU's own three conditions, verbatim in substance: optimising beats 1/N when **(i) the estimation
window is long, (ii) the ex-ante Sharpe of the mean-variance efficient portfolio is substantially
higher than that of 1/N, and (iii) the number of assets is small.** Their MKT/SMB/HML dataset is
the one where optimisers win, and they attribute it explicitly to **N = 3**.

Two further conditions from the same paper, both mechanisms rather than caveats:

- **Errors in means dominate errors in covariances.** The critical window rises sharply going from
  "mean known, covariance unknown" to "both unknown". Anything that does not estimate a mean is in
  a different regime.
- **Constraints are shrinkage.** A short-sale constraint on mean-variance is algebraically
  equivalent to shrinking expected returns toward zero; on minimum-variance it is equivalent
  (Jagannathan–Ma) to shrinking the extreme elements of the covariance matrix. **The
  constrained minimum-variance portfolio "min-c" performs best of all fourteen models on Sharpe** —
  and still cannot beat 1/N with statistical significance in *any* of the seven datasets, and its
  turnover is typically higher.

### Where the debate has moved since

- **Kirby and Ostdiek (JFQA 2012)** is the strongest surviving positive. They build two rules that
  need **no optimisation, no covariance inversion, no short positions**: volatility timing
  (w_i ∝ σ_i^−η) and reward-to-risk timing (w_i ∝ (μ_i/σ_i²)^η), with η a tuning parameter for how
  hard to lean. Both have **low turnover by construction**, and they beat 1/N *after* transaction
  costs. The reported magnitudes (secondary source — see §11): 1/N Sharpe **0.510 gross / 0.507
  net**, RRT **0.52 to 0.57**.
- **Tu and Zhou (2011)** combine 1/N with optimised rules; the gains largely disappear once
  transaction costs are charged, because the combining rules turn over hard.
- **Curran, O'Sullivan and Zalla** (working paper, 2022) revisit DGU using *fourteen econometric
  volatility models* instead of the sample covariance, on six datasets, with a **0.5% proportional
  turnover cost**. Most models beat 1/N on Sharpe, net-of-turnover Sharpe and portfolio volatility.
  **The decisive caveat is in their own design section: they deliberately chose datasets with
  N ≈ 10.** This is a result about small-N index allocation, not about a 1,573-name cross-section.
- **Ledoit–Wolf nonlinear shrinkage** wins in the regime c = N/T > 1 (more assets than
  observations); at c = 0.2 simpler estimators with an equal-weighted target dominate.
- A 2026 working paper, *Fragility of Minimum-Variance Portfolios*, locates min-var's instability
  precisely: threshold effects in the inverse covariance make the active set flip discontinuously
  **when volatilities are nearly tied and correlations are near-constant** — the exact regime a
  single-name equity book sits in.

### Where this programme sits on that line

| DGU condition | This programme | Verdict |
|---|---|---|
| Estimation window long | 4,187 daily bars ≈ **199 months** equivalent | far short |
| N small | **1,573 names**; book widths 5 to ~1,200 | far over |
| S\* ≫ S_ew | no evidence of a large cross-sectional Sharpe gap; ~10 effective instruments | no |

Interpolating DGU's US calibration (~120 months of window required per 25 assets) puts a
full mean-variance rule on a 100-name book somewhere past **12,000 months**. This is not a close
call and it is not a call that shrinkage can rescue: their simulated-data section shows the
estimation-error-aware extensions reduce the required window only *moderately*.

**But the correct reading is narrower than "don't optimise".** DGU's negative is a negative about
*estimating means and a full covariance matrix*. A within-leg inverse-vol weight estimates
**N variances, zero correlations and zero means**. That is the Kirby–Ostdiek corner, it is the one
corner with a surviving net-of-cost positive, and it is what §3 and §4 are about.

---

## 3. Volatility targeting

**The programme must keep two things apart, because the literature does and the cost answers are
opposite.**

**(a) Book-level exposure scaling** — one series, scaled through time by its own inverse realised
variance. This is Moreira–Muir. **(b) Within-leg inverse-vol weighting** — cross-sectional, weights
proportional to 1/σ_i inside a fixed selected set. This is Kirby–Ostdiek. (a) is expensive and its
out-of-sample record is bad. (b) is cheap and its record is the only positive one.

### Sharpe

- **Moreira and Muir (JF 2017)**, read directly: scaling the market by the inverse of previous
  month's realised variance gives an alpha of **4.9%/yr**, an **appraisal ratio of 0.33**, and a
  **25% increase in the buy-and-hold Sharpe ratio**. Appraisal ratios across factors run 0.33 to
  0.91 in their Table.
- **Cederburg, O'Doherty, Wang and Yan (JFE 2020)** is the strongest published negative and it is
  decisive. Across **103 equity strategies**, volatility-managed portfolios do **not** systematically
  outperform their unmanaged counterparts in direct comparison; the strategies implied by the
  spanning regressions are **not implementable in real time**; and reasonable out-of-sample
  versions earn **lower** certainty-equivalent returns and Sharpe ratios than simply holding the
  unmanaged portfolio. The cause they identify is **structural instability in the spanning
  regressions** — i.e. the in-sample coefficient is not the coefficient a real-time investor has.
- **Barroso and Detzel (JFE 2021)**: after transaction costs, using **five** cost-mitigation
  strategies, volatility management of common factors **other than the market** produces
  **zero abnormal returns and significantly reduces Sharpe ratios**. Only the managed *market*
  survives, and its profit concentrates in the most easily arbitraged stocks and only when
  sentiment is high.
- **DeMiguel, Martín-Utrera and Nogales (JF 2024)** partially rehabilitate the idea from a
  multifactor perspective (I could not retrieve the text; see §11).

### Turnover — this is the quantified catch you asked for

Moreira and Muir's own Table IV reports the **average absolute monthly change in weights** |Δw| and
the **breakeven cost** in bp needed to drive the alpha to zero. Read directly from the published
paper:

| Weight rule | \|Δw\| per month | E[R] | α | α at 14 bp | Breakeven |
|---|---|---|---|---|---|
| 1/RV² (realised variance) | **0.73** | 9.47% | 4.86% | 3.63% | **56 bp** |
| 1/RV (realised vol) | **0.38** | 9.84% | 3.85% | 3.21% | **84 bp** |
| 1/E[RV²] (forecast variance) | **0.37** | 9.47% | 3.30% | 2.68% | **74 bp** |
| min(c/RV², 1) — no leverage | **0.16** | 5.61% | 2.12% | 1.85% | **110 bp** |
| min(c/RV², 1.5) | **0.16** | 7.18% | 3.10% | 2.83% | **161 bp** |

Read the first row as: the pure inverse-variance overlay **trades 73% of notional every month**
on top of whatever the underlying book is already doing. Squaring is what costs; scaling by
**vol rather than variance halves the turnover** (0.73 → 0.38) and raises the breakeven from 56 to
84 bp, and a leverage cap takes it to 0.16 with a 110 bp breakeven. **The turnover of a vol overlay
is a design choice with a factor of 4.5 in it, and the cheap designs give up surprisingly little
alpha.** That is the single most actionable table in this brief for question 2.

Two caveats before importing those breakevens. First, they are computed against a market index —
one liquid instrument, not 1,573 single names at per-share cost. Second, Moreira and Muir's own
cost assumptions are 1 bp (Fleming–Kirby–Ostdiek) to 14 bp (Frazzini–Israel–Moskowitz at 1% of
daily volume, plus a VIX-stress adder). This programme's own record has measured **33.8 bp/side**
on held names (D285). **A 56 bp breakeven does not survive a 33.8 bp/side spread on a two-sided
overlay.** The 110 bp leverage-capped variant might.

### Is the benefit drawdown rather than return? Yes — and that is the important finding

- **Harvey, Hoyle, Korgaonkar, Rattray, Sargaison and Van Hemert (JPM 2018)**: 60+ assets, daily
  data from 1926 to 2017, 10% vol target. Vol targeting raises the Sharpe **only for "risk assets"
  (equity and credit)**, and they attribute it to the leverage effect; for **bonds, currencies and
  commodities the Sharpe impact is negligible**. What it does *everywhere* is **reduce the
  likelihood of extreme returns and the volatility of volatility**, and **reduce maximum drawdowns**
  for balanced and risk-parity portfolios — because left-tail events arrive when volatility is
  already elevated and the target-vol book is therefore already small. *(I could not verify a
  single numerical table from this paper — see §11.)*
- **Barroso and Santa-Clara (JFE 2015)**, momentum scaled to constant vol on trailing six-month
  realised vol: Sharpe **0.53 → 0.97**, **excess kurtosis 18.24 → 2.68**, **skew −2.47 → −0.42**,
  with only a marginal turnover increase. Note what moved: the *moments*. This is a crash-risk
  result, and the Sharpe gain is the arithmetic consequence of removing a fat left tail, not of
  finding return.

**So the honest characterisation is: volatility targeting is a shape tool. It buys tail behaviour
and drawdown, and it buys Sharpe only as a by-product, and only in assets with a leverage effect.**
That is unattractive for the personal book (whose objective is Sharpe) and superficially very
attractive for the prop track (whose objective is Calmar) — until §6, where the arithmetic says
plain exposure scaling is Calmar-neutral.

---

## 4. Risk parity, and whether it degenerates at low effective breadth

**It degenerates, and at this programme's breadth it degenerates almost completely.** The
degeneracy is analytic, not empirical:

- Under **constant pairwise correlation** ρ, the equal-risk-contribution weights collapse to
  **w_i ∝ 1/σ_i** — the correlation drops out entirely. ERC *is* inverse-vol in that case.
- Under **constant correlation and equal volatilities**, ERC collapses further to **1/N exactly**.
- Maillard, Roncalli and Teiletche's general result is the sandwich **σ_minvar ≤ σ_ERC ≤ σ_EW**:
  ERC is a minimum-variance portfolio with a diversification constraint, and it can never be worse
  than equal weight or better than min-var on realised volatility.

The programme's own numbers say the correlation structure here is close to homogeneous:
**~10 effective independent instruments across a held single-name book, 2.2 across 57 ETFs, 2.17
of 57 at 15 minutes**, and **two unrelated books correlating at 0.48 with 98.5% of that unexplained
by slot mechanics, equal weighting, the eligibility floor or a shared hedge**. That last figure is
the tell: the correlation is a broad common factor, not idiosyncratic pair structure. **A broad
common factor is exactly the constant-correlation case, and in the constant-correlation case ERC
has no information beyond the individual volatilities.**

The practical reading:

1. **Full ERC buys nothing over inverse-vol here and costs a full covariance estimate.** Skip it.
2. **Inverse-vol is the whole of the available effect**, and its size is governed by one number:
   the cross-sectional dispersion of the held names' volatilities. If the held σ_i are tightly
   clustered, inverse-vol ≈ equal weight and the entire axis is dead. See §10.
3. **Min-variance is actively dangerous in this regime.** The *Fragility* paper's finding is that
   min-var flips discontinuously when inverse-volatilities are nearly tied and correlations are
   near-constant. Their toy case (n = 2, σ = 0.99 vs 1.00, ρ = 0.99) produces **14.23% turnover and
   1.73 average active positions**. On a per-share-cost book, an estimator that churns on
   estimation noise is the worst possible object.
4. **Asness, Frazzini and Pedersen's risk-parity case is an asset-allocation argument
   (leverage aversion makes safe assets cheap on a risk-adjusted basis) and it needs leverage to
   work.** It is about *across-asset-class* allocation, and this programme has one asset class. It
   does not transfer.

---

## 5. Rank/signal weighting within a leg

**This is the weakest-evidenced of the six questions and the evidence that exists is discouraging.**

- **Novy-Marx and Velikov** compare linear rank weights against equal weights and report the two
  portfolios are **83% overlapped**; only nonlinear weighting differentiates them meaningfully.
  That is the size of the prize: 17% of the book, and the difference is concentrated exactly where
  the signal estimate is noisiest.
- Practitioner-side comparisons of rank-select-weight schemes report that equal *and* inverse-vol
  weighting produce low-capacity portfolios with unintended factor exposures, while score-tilt
  weighting trades factor purity against investability. This is the MSCI/vendor literature and is a
  **[SALES INSTRUMENT]** — treat as hypothesis, not evidence.
- **Brandt, Santa-Clara and Valkanov (RFS 2009)** is the serious academic version: parameterise the
  *weight* directly as a function of the characteristic and fit the coefficients by maximising
  average realised utility, rather than modelling returns and then optimising. It is genuinely
  robust in and out of sample and it scales to the full CRSP cross-section, because it estimates a
  handful of coefficients rather than N means and N² covariances. **It is the correct technical
  answer to "should I weight by signal strength", and it answers it by fitting one number per
  characteristic instead of guessing.** But note what it is: an optimisation over the *tilt
  coefficient*, which imports the whole overfitting problem, and it does not model transaction
  costs in the base specification.

Three specific reasons to expect signal weighting to *hurt* on this fixture, all from the
programme's own record rather than the literature:

1. **Concentration is already the binding diagnostic.** D285's top 1% of trades carried 196.9% of
   P&L. Signal weighting raises weight on the extreme ranks, which is the same operation as raising
   the concentration the reporting standard is designed to catch.
2. **The extreme ranks turn over fastest.** Weighting by rank puts the most capital in the
   positions with the shortest expected holding run, i.e. it buys turnover with the money that is
   most expensive to move.
3. **Per-share costs invert the ranking.** Cost in bp scales inversely with price. Extreme-rank
   names in a US single-name universe skew low-priced. Signal weighting concentrates capital where
   the bp cost is highest.

**Recommendation: do not test signal weighting before testing inverse-vol, and if it is tested,
test it as a Brandt–Santa-Clara–Valkanov tilt coefficient (one fitted parameter, with the
pre-registered null being the coefficient = 0 case, which is equal weight) rather than as an
ad-hoc rank weight.**

---

## 6. Kelly and sizing under a HARD DRAWDOWN BARRIER

**The literature does answer this one, unusually well, and the answer has an uncomfortable second
half.**

### The closed form exists

**Grossman and Zhou (Mathematical Finance 1993, "Optimal investment strategies for controlling
drawdowns")** solve exactly this problem: maximise long-run growth subject to
**W_t ≥ λ·M_t** where M_t is the running maximum — a *trailing* drawdown barrier, which is the prop
track's rule. The solution: **invest the free-Kelly fraction of the CUSHION, not of wealth**:

> γ(W_t) = α_K · (W_t − λ·M_t)

Under this rule the barrier is never breached in continuous time, because exposure goes to zero as
the cushion goes to zero. Extended to multi-asset by **Cvitanić and Karatzas (1995)** and to general
semimartingales by **Cherny and Obłój (2013)**. There is also a published counterexample — *"The
Grossman and Zhou investment strategy is not always optimal"* — so the result is not unconditional.

**Busseti, Ryu and Boyd (Journal of Investing 2016, "Risk-Constrained Kelly Gambling")** give the
computable version, and I read the paper. Their bound:

> if **E[(rᵀb)^−λ] ≤ 1** then **Prob(W_min < α) < α^λ**

so to guarantee "no more than a β chance of ever drawing down past α", set **λ = log β / log α**
and solve a convex problem. It is one parameter, it has a clean risk-aversion reading, and their
numerical results say what it costs:

| Bet | growth rate | Prob(drawdown > 30%) |
|---|---|---|
| Full Kelly | 0.062 | **39.7%** |
| RCK, λ = 6.456 (guarantees ≤ 10%) | 0.043 | 7.3% |
| RCK, λ = 5.500 (tuned to ≈10%) | 0.047 | 9.9% |
| **Fractional Kelly at the same 10% risk** | **≈0.035** | 10% |

Two things to take. **(i) Imposing a 10% cap on the probability of a 30% drawdown costs roughly
a quarter of the growth rate** (0.062 → 0.047). **(ii) The optimised rule beats fractional Kelly by
about a third at the same drawdown risk** (0.047 vs 0.035) — so *how* you shrink matters, not just
how much. Their quadratic approximation (QRCK), which is the Markowitz-shaped one, is **worse** than
the exact convex problem at matched risk.

On fractional Kelly generally: half-Kelly is conventionally quoted as giving ~75% of full-Kelly
growth at much lower volatility, but the two secondary sources I found **disagree on the second
number** (one says 75% volatility reduction, one says 50%) — see §11. Do not cite either.

### The uncomfortable half: sizing cannot raise Calmar

**Magdon-Ismail and Atiya (2004)**, whose paper I read, give the closed form for the expected
maximum drawdown of a Brownian motion with drift μ > 0:

> **E[MDD] → (σ²/μ) · (0.63519 + 0.5·log T + log(μ/σ))**

and hence, with Shrp = μ/σ,

> **Calmar(T) = μT / E[MDD] → T·Shrp² / (0.63519 + 0.5·log T + log Shrp)**

Three consequences, and they are the crux of the prop-track question:

1. **Calmar is invariant to the leverage scalar.** Scale exposure by f: μ → fμ, σ → fσ, Sharpe is
   unchanged, E[MDD] scales linearly with f, return scales linearly with f. **Calmar is unchanged.**
   Volatility targeting, fractional Kelly, risk parity's leverage step — none of these can move
   Calmar at all, to first order. (Compounding makes it strictly worse at high f, via the −f²σ²/2
   term.)
2. **A Calmar of 18.9 is a Sharpe of about 7 over one year, or about 5 over two years.** Solving
   S²/(0.635 + log S) = 18.9 gives S ≈ 7.0; over T = 2, 2S²/(0.982 + log S) = 18.9 gives S ≈ 5.0.
   That is what the prop hurdle demands from a roughly Gaussian, roughly i.i.d. equity curve. The
   programme's own note that the best audited intraday CME programme in a 199-programme database
   scores 1.07 is consistent with this: Calmar 18.9 is not a risk-management setting, it is a
   different distribution.
3. **Grossman–Zhou does not raise Calmar either.** Cushion-proportional sizing caps MaxDD at
   (1−λ) *and* shrinks the growth rate roughly proportionally. What it buys is **survival of the
   barrier**, converting an unbounded ruin risk into a bounded one. That is worth having — a book
   that would be terminated on a normal retracement is worth nothing regardless of its Calmar — but
   it is not a route to the hurdle.

### What the literature does not answer, stated plainly

- **Nothing addresses a barrier measured on unrealised INTRADAY equity.** Grossman–Zhou is a
  continuous-time barrier on wealth; the RCK bound is on a discrete wealth path. A barrier on the
  intraday low of open equity is strictly tighter than either, and a book whose edge is overnight
  is exposed to gap risk that breaks the "never breached" guarantee — the continuous-time result
  depends on being able to reduce exposure as the cushion shrinks, and a gap gives no chance to.
- **There is no closed form for maximising Calmar.** Magdon-Ismail and Atiya note explicitly that
  Calmar-based portfolio optimisation is not prevalent, and their contribution is a *normalisation*
  (the τ-normalised Calmar, scaling by γ_τ(T, Shrp)) so that Calmar ratios over different track
  lengths can be compared at all — not an optimiser. Their point that **"knowing the Calmar ratio
  of a portfolio without knowing T is useless"** applies directly to the 18.9 figure: it needs a
  horizon attached before it means anything.
- **I found no peer-reviewed treatment of prop-firm evaluation-account rules.** Everything returned
  on that search was vendor and blog material and is not evidence.

---

## 7. Cost-aware construction: no-trade regions and rank buffers

**This is the best-evidenced section in the brief, and the programme has independently rediscovered
its main result.**

### The theory

- **Constantinides (1986)** and **Davis and Norman (1990)**: with proportional transaction costs
  the optimal policy is a **no-trade region**, and when you leave it you rebalance **to the nearer
  boundary — never back to the target**. This is the sS inventory rule of Arrow, Harris and
  Marschak (1951).
- **How wide?** **Abel and Eberly (1996)**, cited in Novy-Marx and Velikov's own footnote: even
  tiny transaction costs produce non-trivial inaction regions, and **the size of the region is
  proportional to the CUBE ROOT of the price wedge for small wedges**, which makes its derivative
  with respect to the wedge infinite at zero. Two things follow for setting a band: **(i) the
  optimal band is much wider than linear intuition suggests** — a 4× cost increase widens the band
  only ~1.6×, so bands should be set generously; and **(ii) the band is extremely insensitive to
  the cost estimate over the relevant range, so do not tune it against a noisy cost number.** Pick
  the order of magnitude from the cube-root law and verify robustness across a wide sweep. That is
  the theoretical answer to "how do I set the band".
- **Gârleanu and Pedersen (JF 2013)** give the dynamic, multi-signal version: **"aim in front of the
  target, and trade partially towards the current aim."** The aim portfolio is a weighted average of
  the current Markowitz target and all future expected targets, and **predictors with slower alpha
  decay get more weight in the aim.** For a programme with signals at different horizons, this is
  the right structure: fast signals should be traded less aggressively than their raw weight
  implies, because the position they justify will be gone before the round trip amortises.

### The empirics, read from the paper

Novy-Marx and Velikov (RFS 2016, NBER w20721), 23 anomalies, US equities:

- **The buy/hold spread is the single most effective simple mitigation technique.** An sS rule:
  buy only when the signal enters the extreme **s%**, hold until it leaves the extreme **S%**. Their
  parameterisations: **10%/20%** for mid-turnover strategies, **10%/50%** for high-turnover.
- **Mid-turnover, 10%/20% band: average turnover −41%, transaction costs −42%**, gross returns
  slightly lower, **net returns higher**. The mechanism they state is that stocks in the 75–80%
  band are near-substitutes for stocks in the 80–85% band, so holding the substitute costs almost
  no signal.
- **All three techniques together** (cheap-to-trade half of each size decile + staggered partial
  rebalancing + banding) gives **turnover −60%, costs −59%** — but **generally does not improve on
  banding alone** for mid-turnover strategies. Multi-mitigation only pays for the high-turnover
  cases.
- In the ex-post tangency portfolio across the three techniques, **most weight goes to the sS
  variants.**
- **Novy-Marx and Velikov (FAJ 2019)**: banding beats reducing rebalancing frequency, because it
  achieves similar cost reductions **while maintaining better exposure to the underlying signal**.
  That is the precise reason to prefer a rank buffer over trading less often.

### The turnover thresholds, which are the survival bar

- **Most anomalies with one-sided monthly turnover below 50% still generate significant net spreads
  when designed to mitigate costs. Few above that do** — only **two** of their >50%/month
  strategies had significant net spreads even when designed for cost.
- **Transaction costs reduce realised spreads by more than 1% of monthly one-sided turnover**: 20%
  monthly turnover on the long side ⇒ at least **20 bp/month** off the spread. That is a usable
  back-of-envelope for any candidate here.
- Mid-turnover (14–35%/month per side) costs run **20 to 57 bp/month**, often more than half the
  gross spread. High-turnover costs **always exceed 1%/month** absent mitigation.
- **Round-trip costs for value-weighted strategies average in excess of 50 bp; equal-weighted
  strategies cost two to three times as much.** Read that sentence twice — it is aimed directly at
  the programme's incumbent.

The programme's own −1.5%/yr → +6.5%/yr from a rank buffer is the same result, on this fixture,
with a larger effect size than NMV report. That is a reason to push the parameter, not to consider
it done: NMV's band is **asymmetric, defined in rank-percentile space, and wide** (10%/50% for fast
signals), and the theory says the width should scale with the **cube root of the cost** and with the
**alpha-decay speed** of the signal being traded.

---

## 8. The honest ceiling from sizing alone

**Sharpe, on a fixed signal, from weights alone: +0.0 to +0.1, and the central estimate is closer
to +0.03.** The evidence:

- DGU: fourteen models, seven datasets, **zero** consistent wins over 1/N. The best performer
  (constrained min-var) is never statistically superior in any dataset.
- Kirby–Ostdiek, the surviving positive: **0.510 → 0.52–0.57 net**, i.e. **+0.01 to +0.06**, or
  **+2% to +12% relative** — and that is at small N with no per-share cost structure.
- Curran et al.: broad but modest wins at N ≈ 10 with 50 bp costs, which is a friendlier regime
  than this one on every axis.

**The exception, and it is the only one, is when the book has a fat left tail driven by volatility
clustering.** Barroso–Santa-Clara's momentum result (0.53 → 0.97) is a near-doubling, and it comes
from removing excess kurtosis of 18.24. **That is a shape fix and it is only available to a book
whose drawdowns are concentrated in identifiable high-volatility episodes.** If a book's drawdowns
are a slow bleed, vol scaling has nothing to grip.

**Calmar, from sizing alone: zero.** See §6 — E[MDD] and return both scale linearly with exposure,
so every leverage-scalar rule is Calmar-neutral. Drawdown-conditional sizing (Grossman–Zhou, RCK)
caps the drawdown and pays for it in growth. The only sizing operation that moves Calmar is one
that changes the *shape* of the return distribution, and the only documented such operation is
volatility targeting on a vol-clustered, leverage-effect asset.

**Turnover, from cost-aware construction: −40% to −60%, well documented.** This is arithmetic, not
estimation — it does not depend on forecasting anything. On a book whose net = gross − (turnover ×
cost), it is the largest reliable lever in this brief, and it is the one the programme has already
found.

**So the honest ranking of levers, largest first: (1) band/buffer width and its dependence on
signal decay speed; (2) inverse-vol weighting within a leg, if and only if the held names' vols are
dispersed; (3) everything else, which is noise.** That is much less than the portfolio-optimisation
literature claims for itself, and this brief's own strongest sources say so.

---

## 9. What transfers to OUR situation

**Bluntly, given ~10 effective instruments and per-share costs:**

1. **Full mean-variance and any rule needing an estimated mean is dead on arrival.** DGU's critical
   window at these dimensions is two to three orders of magnitude beyond the fixture. Do not spend
   a study on it.
2. **Risk parity/ERC is dead for a different reason: it degenerates.** With a near-homogeneous
   correlation block — which is what "~10 effective instruments and 98.5% of a 0.48 cross-book
   correlation unexplained by mechanics" describes — ERC *equals* inverse-vol, and if vols are also
   tight it equals 1/N. There is no third thing for it to find.
3. **Minimum-variance is worse than dead — it is unstable in exactly this regime** (near-tied
   inverse-vols, near-constant correlation), and instability on a per-share-cost book converts
   estimation noise directly into commission.
4. **Inverse-vol within a leg is the one live candidate, and it is cheap in the one way that
   matters here: volatility is persistent, so inverse-vol weights move slowly, so incremental
   turnover is small.** This is the opposite of book-level vol targeting, which trades 16–73% of
   notional per month.
5. **Per-share costs cut both ways on inverse-vol, and the sign is an empirical question.**
   Inverse-vol *underweights* high-vol names, which in a US single-name universe skew low-priced,
   which is where bp cost is worst. So inverse-vol may cut cost as a side effect — **or** it may
   underweight exactly where this programme's edge lives (the record's own price splits killed
   D284). Both must be measured, on the same held set.
6. **Equal weighting is not a neutral incumbent, and this is the least-appreciated point in the
   brief.** Plyakha, Uppal and Vilkov attribute a large share (reported as 42%) of equal weight's
   outperformance to the **rebalancing itself**, which is a contrarian, reversal-harvesting
   operation. **Moving from equal weight to inverse-vol therefore removes an implicit short-horizon
   reversal exposure** — and reversal is a variable this programme has studied extensively. Any
   EW-vs-IV comparison must be read as *sizing plus a change in reversal exposure*, not sizing
   alone. That is a nuisance the control must share.
7. **Equal weighting is also the expensive weighting.** NMV: equal-weighted strategies cost two to
   three times value-weighted ones. The programme's $5 floor and dollar-volume window mitigate this
   but do not remove it, and Hou–Xue–Zhang's replication result (with NYSE breakpoints and
   value-weighting, **65%** of 452 anomalies fail a t = 1.96 hurdle and **82.1%** fail t = 2.78) is
   a warning about how much of an equal-weighted result can be microcap.
8. **For the prop track, the transferable content is one closed form and one piece of arithmetic.**
   The closed form is Grossman–Zhou / Busseti–Ryu–Boyd: size on the **cushion above the barrier**,
   not on equity, with λ = log β / log α. The arithmetic is that this makes the barrier survivable
   and does **not** raise Calmar — and that Calmar 18.9 over a one-year track corresponds to a
   Sharpe near 7. **The prop hurdle is not a sizing problem and should stop being treated as one.**
9. **The controls this brief implies, in the house's own terms.** Any EW-vs-alternative test must
   hold the **selected set** fixed bar by bar — otherwise it measures selection, not sizing. A
   matched-count control is not enough (D279); a matched-*turnover* control is what is needed here,
   because every alternative weight scheme changes turnover, and turnover is the programme's
   chronic killer. And both lenses apply: weights are a path-variant object, so the slot-limited
   book in bp/bar is the right scorer, never the per-trade statistic.

---

## 10. The premise number to compute first

**One number, computable in a single pass over the existing fixture, with no optimiser, no
forecast and no look-ahead:**

> **The ratio of the ARITHMETIC MEAN to the HARMONIC MEAN of the realised volatilities of the names
> actually HELD, measured bar by bar over the held set.**

That ratio *is* the entire inverse-vol effect. If it is ≈ 1.00–1.03, the held names' volatilities
are too tightly clustered for inverse-vol weighting to differ materially from equal weight and
**the whole of §3, §4 and §5 is dead before a runner is written**. If it is ≥ 1.15, there is a real
dispersion to exploit and the axis is worth a study. It costs one pass and it is the Stage-0
premise check the axis has never had.

**Two companions, both cheap, both needed before any runner:**

- **Persistence of the conditioner.** Regress next-bar log book variance on current log book
  variance (or the AR(1) on log realised variance that Moreira and Muir use to build their
  forecast). Report the R². Vol targeting is a bet that variance is forecastable at the rebalance
  horizon; if that R² is near zero, the exposure-scaling axis is dead for the same reason. Report
  it alongside the *return* regression — vol targeting also needs vol **not** to forecast return,
  which is Moreira and Muir's Figure 1 claim.
- **The Calmar feasibility check.** Compute the book's realised annualised Sharpe and evaluate
  **Calmar(T) = T·S² / (0.635 + 0.5·log T + log S)**. If the implied Calmar at the prop track's
  actual evaluation horizon is not within reach of 18.9, then **no sizing rule closes the gap**, and
  the prop track needs a distributional change (skew, tail, or a genuinely regime-conditional
  exposure), not a leverage setting. This is a five-line computation and it should be done before
  any further prop-track sizing work.

**And one negative control the brief demands:** run the EW-vs-IV comparison on the *same held set*
and also on a **volatility-matched random partner** rather than a re-drawn random subset — a random
subset re-draws each bar and churns (D291's 2.4× entries), which would flatter any low-turnover
weighting scheme by construction.

---

## 11. Sources

**Primary text read directly (I extracted and read the PDF body):**

- DeMiguel, Garlappi, Uppal, *Optimal Versus Naive Diversification: How Inefficient is the 1/N
  Portfolio Strategy?* — https://users.nber.org/~confer/2006/si2006/ap/uppal.pdf (conference
  version of RFS 2009, 22(5), 1915–1953) — **[PEER-REVIEWED]** (this file is the working version;
  the published article is at https://academic.oup.com/rfs/article-abstract/22/5/1915/1592901).
  All §2 numbers are read from this text.
- Novy-Marx, Velikov, *A Taxonomy of Anomalies and their Trading Costs*, NBER w20721 —
  https://www.nber.org/system/files/working_papers/w20721/w20721.pdf (published RFS 2016, 29(1),
  104–147) — **[WORKING PAPER]** / published version **[PEER-REVIEWED]**. All §7 numbers, and the
  Abel–Eberly cube-root citation, read from this text.
- Busseti, Ryu, Boyd, *Risk-Constrained Kelly Gambling* —
  https://web.stanford.edu/~boyd/papers/pdf/kelly.pdf (Journal of Investing, Fall 2016, 25(3))
  — **[PEER-REVIEWED]**. The α^λ bound and Tables 1–3 read from this text.
- Moreira, Muir, *Volatility-Managed Portfolios*, Journal of Finance 2017 —
  https://amoreira2.github.io/alan-moreira.github.io/VolPortfolios_published.pdf —
  **[PEER-REVIEWED]**. Table IV turnover/breakeven figures read from this text.
- Magdon-Ismail, Atiya, *An Analysis of the Maximum Drawdown Risk Measure* —
  https://www.cs.rpi.edu/~magdon/ps/journal/drawdown_RISK04.pdf (Risk, 2004) —
  **[PEER-REVIEWED]**. E[MDD] and Calmar formulas read from this text.
- Curran, O'Sullivan, Zalla, *Can Volatility Solve the Naive Portfolio Puzzle?*, arXiv:2005.03204v4
  (Feb 2022) — https://arxiv.org/pdf/2005.03204 — **[WORKING PAPER]**. The **N ≈ 10** design
  constraint and the 0.5% cost assumption read from this text.

**Read via an HTML summariser (content is the summariser's rendering, not my reading of the full
text — treat as one step weaker):**

- *Fragility of Minimum-Variance Portfolios*, arXiv:2607.18624 — https://arxiv.org/html/2607.18624
  — **[WORKING PAPER]**
- *Which Portfolios? The Construction Dependence of Factor Model Performance*, arXiv:2606.19550 —
  https://arxiv.org/html/2606.19550 — **[WORKING PAPER]**. Relevant context for §5/§9: pricing
  errors on identical stock sets range ~10 bp to 490 bp purely on weighting and post-formation
  weight-management choices, CRSP daily 1967–2024, **no cost treatment**.

**Known only from search-result snippets — numbers NOT verified against the paper:**

- Cederburg, O'Doherty, Wang, Yan, *On the performance of volatility-managed portfolios*, JFE 2020,
  138(1), 95–117 — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3357038 —
  **[PEER-REVIEWED]**. The "103 strategies", "not implementable in real time" and "structural
  instability" characterisations are from snippets; I did not read the paper.
- Barroso, Detzel, *Do limits to arbitrage explain the benefits of volatility-managed portfolios?*,
  JFE 2021, 140(3), 744–767 — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3088828 —
  **[PEER-REVIEWED]**, snippet only.
- Harvey, Hoyle, Korgaonkar, Rattray, Sargaison, Van Hemert, *The Impact of Volatility Targeting*,
  JPM 2018, 45(1), 14 — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3175538 —
  **[PEER-REVIEWED]**. **I could not verify a single number from this paper.** SSRN, Alpha
  Architect and QuantPedia all returned 403 or contentless pages; the Man Group page
  (https://www.man.com/insights/the-impact-of-volatility-targeting — **[SALES INSTRUMENT]**, it is
  the authors' own employer) states the qualitative findings and explicitly gives no figures and
  **no turnover or transaction-cost discussion at all**. Everything in §3 attributed to this paper
  is qualitative and second-hand.
- Barroso, Santa-Clara, *Momentum has its moments*, JFE 2015 —
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2041429 — **[PEER-REVIEWED]**. The
  0.53→0.97, kurtosis 18.24→2.68, skew −2.47→−0.42 figures are from a snippet and are widely
  repeated but I did not read the table.
- Kirby, Ostdiek, *It's All in the Timing*, JFQA 2012, 47(2), 437–467 —
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1530022 — **[PEER-REVIEWED]**. The 1/N
  0.510/0.507 and RRT 0.52–0.57 figures come from a secondary literature review, **not** from the
  paper. Verify before citing in a record.
- Maillard, Roncalli, Teiletche, *On the properties of equally-weighted risk contributions
  portfolios*, JPM 2010, 36(4) — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1271972 —
  **[PEER-REVIEWED]**. **The author's own PDF (thierry-roncalli.com/download/erc.pdf) failed on a
  TLS certificate error and I could not read it.** The constant-correlation ⇒ inverse-vol and
  equal-vol-and-correlation ⇒ 1/N collapses, and the σ_minvar ≤ σ_ERC ≤ σ_EW sandwich, are stated
  from snippets plus standard derivation. **UNVERIFIED against the source — verify before citing.**
- Grossman, Zhou, *Optimal Investment Strategies for Controlling Drawdowns*, Mathematical Finance
  1993, 3, 241–276 — https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1467-9965.1993.tb00044.x —
  **[PEER-REVIEWED]**, snippet only; the γ = α_K(W_t − λM_t) form is from a snippet of a citing
  paper. Counterexample: *The Grossman and Zhou investment strategy is not always optimal*,
  Statistics & Probability Letters —
  https://www.sciencedirect.com/science/article/abs/pii/S0167715205001641 — **[PEER-REVIEWED]**.
- MacLean, Ziemba, Blazenko growth-security tradeoff and the half-Kelly figures — **[UNVERIFIED
  AND INTERNALLY INCONSISTENT]**: two secondary sources gave incompatible numbers (75% vs 50%
  volatility reduction at half-Kelly). Do not cite either without reading Management Science 1992.
- Gârleanu, Pedersen, *Dynamic Trading with Predictable Returns and Transaction Costs*, JF 2013,
  68(6), 2309–2340 — https://www.nber.org/papers/w15205 — **[PEER-REVIEWED]**, snippet only.
- Novy-Marx, Velikov, *Comparing Cost-Mitigation Techniques*, FAJ 2019, 75(1), 85–102 —
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3253359 — **[PEER-REVIEWED]**, snippet only
  (SSRN returned 403).
- Detzel, Novy-Marx, Velikov, *Model Comparison with Transaction Costs*, JF 2023, 78(3), 1743–1775
  — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3805379 — **[PEER-REVIEWED]**, snippet
  only. Relevant as a caution: ignoring costs biases model comparison toward high-cost factors.
- Brandt, Santa-Clara, Valkanov, *Parametric Portfolio Policies*, RFS 2009, 22(9), 3411–3447 —
  https://www.nber.org/papers/w10996 — **[PEER-REVIEWED]**, snippet only.
- Hou, Xue, Zhang, *Replicating Anomalies*, RFS 2020 —
  https://global-q.org/uploads/1/2/2/6/122679606/houxuezhang2020rfs.pdf — **[PEER-REVIEWED]**,
  snippet only (the 65% / 82.1% failure rates).
- Plyakha, Uppal, Vilkov, *Why Does an Equal-Weighted Portfolio Outperform Value- and
  Price-Weighted Portfolios?* — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2724535 —
  **[WORKING PAPER]**, snippet only (the 2.71%/yr and "42% from rebalancing" figures).
- Asness, Frazzini, Pedersen, *Leverage Aversion and Risk Parity*, FAJ 2012, 68(1), 47–59 —
  https://pages.stern.nyu.edu/~lpederse/papers/LeverageAversionRP.pdf — **[PEER-REVIEWED]**,
  snippet only. Note the authors are principals of AQR, which sells risk-parity products.
- DeMiguel, Martín-Utrera, Nogales, *A Multifactor Perspective on Volatility-Managed Portfolios*,
  JF 2024 — https://onlinelibrary.wiley.com/doi/full/10.1111/jofi.13395 — **[PEER-REVIEWED]**.
  **Fetch returned 403; I know only the title.** This is the most likely counterweight to §3's
  negatives and it is the first thing to read if the vol-targeting axis is pursued.

**Labelled sales instruments, cited only as hypothesis:** MSCI weighting-scheme commentary; Man
Group's own summary of Harvey et al.; ReSolve/Invest Resolve risk-parity whitepapers; QuantPedia;
Alpha Architect. **This area is unusually thick with them** — most first-page search results for
every one of the seven questions were vendor material, and none of it is used for a number here.

**Nothing in this brief was blocked or refused, and no page contained instructions addressed to
the researcher.** The only failures were technical: SSRN, Wiley, tandfonline and Alpha Architect
returned HTTP 403 to automated fetches, and thierry-roncalli.com failed TLS verification.
