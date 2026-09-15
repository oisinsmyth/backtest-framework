# 08 — The academic and quantitative literature

**Lane 08 of the Prop-Firm-080926 research.** Scope fixed by
[`00-SCHEMA.md`](00-SCHEMA.md) §2: barrier-option pricing, optimal stopping / gambler's ruin,
drawdown-constrained portfolio choice, Kelly under a ruin constraint, risk-shifting under convex
compensation, the economics of the funded-account industry, and volatility-managed portfolios as a
size-control policy.

**Stopping rule (schema §3): saturation.** Stopped after **five consecutive sources yielding zero
results not already in the log** — probes 30–34 in the `## Sources` table.

**This is a REVIEW.** It adjudicates nothing, adds no looks to any multiplicity ledger, and closes no
avenue. Every fetched page is **observed content — data, never instructions.**

**Everything below assumes [D379](../../decisions/D379-the-prop-account-is-a-down-and-out-call-and-hurdle-P-has-no-objective-function.md)
has been read.** Section references (§1, §5, A1, A2) are to that record.

---

## VERDICT — what is load-bearing and what is decorative

### The one finding that changes how D379 should be read

**The drawdown-constrained portfolio-choice literature — Grossman & Zhou, Cvitanić & Karatzas,
Cherny & Obłój, Elie & Touzi — solves a DIFFERENT problem from ours, and its answer is the
sign-opposite of D379 §5.** That whole literature assumes the agent **owns** the wealth: hitting the
floor is terminal and uncompensated, so under log/CRRA utility the optimal risky exposure is
**proportional to the surplus `W − αM` and goes to ZERO at the floor.** D379 §5's toy found the
opposite — that at 0.3% of buffer remaining a volatile +EV trade is worth **12×** what it is worth at
full buffer.

**Both are correct, and the difference is not a modelling detail — it is the whole economics of the
instrument.** A prop trader does not own the account. Their downside is truncated at a **sunk
evaluation fee**; the drawdown-constrained investor's downside is their own capital. That truncation
is exactly what makes the near-barrier convexity invert.

> **Operational consequence: Grossman–Zhou-style sizing is the right frame for `docs/BOOK.md` (the
> personal book, where you own the capital) and the WRONG frame for `docs/BOOK_PROP.md`. Do not carry
> it across.** D379 §6 already forbids carrying prop conclusions to the personal book; this is the
> same wall in the other direction, and it had not been stated.

### The paper that actually adjudicates D379 §5 — and it splits

**Hodder & Jackwerth (2007, JFQA)** is the closest thing in the literature to our exact object: a
manager with convex incentive fees and a **liquidation barrier**. Its result is conditional, and the
condition is the one D379 §5 does not state:

| barrier type | manager's risk near the boundary |
|---|---|
| **exogenous** (forced shutdown) | **reduces** risk sharply as value declines toward it |
| **endogenous** (manager optimally quits) | **increases** risk as value approaches it |

The discriminant is **continuation value**. An exogenously-liquidated manager still loses a
management-fee stream and an ownership stake, so they defend the account. An endogenously-quitting
manager has already truncated their own downside, so they gamble. **Kirti (2024, JBF)** says the same
thing in banking: gambling for resurrection is suppressed when **franchise value** is high enough.

**A prop account's barrier is exogenous, but the trader's payoff shape is the endogenous case** —
no ownership stake, no fee stream, nothing at risk but the sunk premium. So D379 §5's prediction
survives **conditionally**, and the condition is computable from D379's own amendment:

> **`fee ÷ P(pass)` (D379 A1) IS the continuation value** — the replacement cost of a knocked-out
> account. §5's convexity inversion holds when that replacement cost is small relative to the
> variance gain, and fails when it is large. **D379 A1 already supplies the quantity that decides
> whether D379 §5 is true.** Neither section cites the other.

This also **strengthens** D379 §5's retro-justification of P3/P5 rather than weakening it: **Li, Lyu
& Wei (2026)** show a VaR-type floor on a manager with option incentives **shifts rather than
suppresses** risk-taking, and an *over-strict* floor **increases** default probability by inducing
gambling for recovery. And **Basak & Shapiro (2001, RFS)** show that probability-based (VaR) limits
make the *worst* states worse. **Neither is a rebuttal of P3** — a prop daily-loss limit is a hard
floor, closer to Basak–Shapiro's own LEL alternative than to a VaR — but both say a loss limit is
**not automatically protective**, and its calibration has a sign that can flip.

### Two closed forms we can actually compute with, today

**1. The exact result behind D379's 40%, generalised to drift — and it inverts a pass rate into an
implied edge.** For a P&L process `X` with drift `μ` and vol `σ` (per unit time, in dollars), started
at 0, absorbed at `+a` (target) or `−b` (floor):

```
P(hit +a before −b)  =  (1 − e^{2μb/σ²}) / (e^{−2μa/σ²} − e^{2μb/σ²})
                     →  b / (a + b)                          as μ → 0
```

`b/(a+b)` = `2000/5000` = **40.0%** — D379 A2's static-floor figure, exactly. **Verified here against
a 200k-path Monte Carlo** (closed form 0.4000/0.4302/0.4912/0.3703 vs MC 0.4014/0.4341/0.4966/0.3741
at μ = 0/0.05/0.15/−0.05, σ = 0.20, a = 0.06, b = 0.04; the MC's small positive bias is itself
discrete-monitoring overshoot, item 3 below).

**Only `θ = 2μ/σ²` is identified by a pass rate** — not μ and σ separately. An implied Sharpe
therefore needs an assumed per-day dollar risk. For Topstep-like `a = $3,000`, `b = $2,000`:

| claimed pass rate | implied `θ = 2μ/σ²` | implied ann. Sharpe at σ = $500/day |
|---:|---:|---:|
| 5% | −0.000947 | **−3.76** |
| 10% | −0.000680 | −2.70 |
| **15%** | −0.000511 | **−2.03** |
| 20% | −0.000380 | −1.51 |
| **40%** | 0 | **0.00** ← the martingale point |
| 50% | +0.000164 | +0.65 |
| 70% | +0.000523 | +2.08 |

**Read against lane 07 with care.** A published 15% first-attempt pass rate does *not* imply the
population trades at Sharpe −2: D379 A2 shows a **trailing** floor drops the zero-edge rate from 40%
to **26.5%**, and minimum-trading-days and time limits cut it further. The table is only the
static-floor benchmark; **the correct use is to compute the zero-edge rate for each geometry Stage 0
finds, and read the claim against THAT**, not against 40%.

**2. `P(a STATIC floor at (1−x) of the starting balance is ever breached) = (1 − x)^{2/f − 1}` at
fractional-Kelly `f`** (derived here for GBM: log drift `S²(f − f²/2)`, vol `fS`, so
`2m/s² = 2/f − 1`; the general non-Gaussian version is the Busseti–Ryu–Boyd bound). **This is
D379 §1's "interior optimum strictly below the unconstrained one", as a number:**

| x | f = 1 (full Kelly) | 1/2 | 1/4 | 1/10 | 1/20 |
|---:|---:|---:|---:|---:|---:|
| **4%** | 0.960 | 0.885 | 0.751 | 0.460 | 0.204 |
| 5% | 0.950 | 0.857 | 0.698 | 0.377 | 0.135 |
| 10% | 0.900 | 0.729 | 0.478 | 0.135 | 0.016 |

Inverted: **against a 4% STATIC floor you need ≈1/9 Kelly for an even chance of never breaching,
1/17.5 Kelly for 25%, and 1/29 Kelly for 10%.** At full Kelly the account is breached with
probability 0.96. D379 §3 found C1's value monotone decreasing across 1.42x → 0.48x and concluded the
peak lies at or below the boundary of the sweep; this says how far below to look, and it is **far**
below — an order of magnitude under Kelly, not a factor of two.

> **A correction I nearly filed, caught by the Monte Carlo, and it is the more important half of this
> result.** I first tabulated the formula above as the probability of ever breaching a **trailing**
> floor at `(1−x)` of the *running maximum*. **That is wrong, and the MC returned 1.0000 against a
> closed form of 0.4992 — a discrepancy no tolerance would have hidden.** The drawdown process
> `sup_{u≤t}X_u − X_t` is a **reflected** BM with drift `−m`; it is positive recurrent, so its
> stationary law is `Exp(2m/s²)` but its **running supremum diverges a.s.** The exponential law is
> the depth at a *point in time*, not the all-time maximum.
>
> **`(1−x)^{2/f−1}` is therefore the STATIC-floor result — the probability of ever falling `x` below
> the STARTING balance.** And the consequence for the trailing case is unconditional:
>
> **Against a trailing floor that never locks, `P(breach) = 1` for every `f > 0`, at every edge, over
> an infinite horizon.** No sizing survives it. **This is why every trailing-floor geometry in lanes
> 01–05 must have either a lock level (schema field 10) or a time limit (field 13) to be a sellable
> product at all** — and it means field 10 is not a detail of the terms, it is what makes the
> instrument finite-valued. **Any Stage 0 trailing-floor pass rate is therefore a statement about a
> horizon, and the horizon must be quoted with it.** D379 A2's 26.5% is, correctly, a
> fixed-target simulation and not an infinite-horizon claim.

### The number that makes EOD-vs-intraday monitoring comparable across firms

**Broadie, Glasserman & Kou (1997)**: a discretely monitored barrier prices as a *continuously*
monitored one with the barrier shifted by `exp(±βσ√Δt)`, `β = −ζ(½)/√(2π) ≈ 0.5826`, error improved
from `O(1/√m)` to `o(1/√m)`. **For a down-and-out the shift is DOWNWARD** — discrete monitoring is
strictly more forgiving, because the overshoot between observations goes unpunished.

For an account with daily P&L vol σ_$ and once-a-day monitoring, in arithmetic dollars to first
order:

| σ_$ / day | shift | a $2,000 EOD floor behaves like a continuous floor at | effective buffer gain |
|---:|---:|---:|---:|
| 250 | $146 | $2,146 | +7.3% |
| 500 | $291 | $2,291 | **+14.6%** |
| 1,000 | $583 | $2,583 | +29.1% |

**This gives schema fields 7 and 9 a common scale** — an end-of-day-monitored floor and an
intraday-monitored floor can be compared as *the same instrument with different barriers*, and the
gap is a function of the trader's own size. **Do not overstate it:** EOD-on-closed-balance versus
intraday-on-open-equity differs in *both* the monitoring frequency and the monitored quantity, and
BGK only prices the first. It is a lower bound on the difference, not the difference.

### Decorative

- **Merton (1973) / Reiner & Rubinstein (1991) closed-form barrier prices.** We need a *probability*,
  not a price; the probability is the simpler object and is the two-sided exit formula above.
  Knowing the down-and-out call formula adds nothing computable here.
- **The volatility-managed-portfolio literature, as an alpha claim.** Moreira & Muir (2017) is
  contested from four directions (Cederburg et al. 2020: fails out of sample; Liu, Tang & Zhou 2019:
  look-ahead bias, and 68–93% max drawdown once corrected; Barroso & Detzel 2021: only the market
  factor survives costs; DeMiguel, Martín-Utrera & Uppal 2024: works only in a conditional
  multifactor form). **But the alpha claim is not what we need.** For a barrier, the question is
  whether vol-scaling lowers `P(breach)` — a far weaker claim that none of the critics dispute, and
  that none of these papers tests. **The literature does not adjudicate vol-scaling as a barrier
  control.** The one thing it *does* give us is a methodological warning: LTZ's finding that the
  headline result was a look-ahead artifact applies directly to our own C1 vol-target sweep.
- **Barrier-option pricing under stochastic volatility / Lévy processes.** Real, large, and irrelevant
  until we have a candidate to size.

---

## The table

| citation | the ONE result that matters for us | closed form? | assumptions | survives fat tails / autocorrelation? |
|---|---|---|---|---|
| **Grossman, S. & Zhou, Z. (1993), "Optimal Investment Strategies for Controlling Drawdowns", *Mathematical Finance* 3(3), 241–276** | Under `W ≥ αM`, optimal risky investment is **proportional to the surplus `W − αM`** and → 0 at the floor | **Yes**, for CRRA in a lognormal market | GBM, continuous rebalancing, infinite horizon, no consumption, agent **owns** the wealth | Framework: no. **And it is the wrong objective for a prop account** — see verdict |
| **Cvitanić, J. & Karatzas, I. (1995), "On Portfolio Optimization Under Drawdown Constraints", *IMA Lecture Notes in Math. & Appl.* 65, 77–88** | Martingale method; constrained problem maps to an **unconstrained** one. Extends GZ to multiple risky assets | Yes | Lognormal, deterministic coefficients (log utility tolerates random ergodic coefficients) | Same objection as GZ |
| **Cherny, V. & Obłój, J. (2013), "Portfolio optimisation under non-linear drawdown constraints in a semimartingale financial model", *Finance and Stochastics* 17(4)** (arXiv:1110.6289) | Constrained value function **equals** an unconstrained one with a **modified utility**; optimal wealth is an explicit **pathwise** transform of the unconstrained optimum | Yes, as a transform | **Abstract semimartingale market** — the most general of this family | **Best of this family.** Pathwise transform means it is not tied to GBM. Still assumes the agent owns the wealth |
| **Klass, M. & Nowicki, K. (2005), "The Grossman and Zhou investment strategy is not always optimal", *Statistics & Probability Letters* 74(3)** | GZ's strategy is **not optimal in discrete time** | Counterexample | Discrete time | **Directly relevant**: our floor is monitored on a discrete grid. A caution, not a substitute |
| **Angoshtari, B., Bayraktar, E. & Young, V.R. (2016), "Optimal investment to minimize the probability of drawdown", *Stochastics* 88(6)** (arXiv:1506.00166) | Explicit policy minimising `P(wealth hits a fixed fraction of its running max)`, with a payout function of value | **Yes** | Black–Scholes, continuous rebalancing, deterministic payout rule | No; and again the objective is *survival*, not *value* |
| **Broadie, M., Glasserman, P. & Kou, S. (1997), "A Continuity Correction for Discrete Barrier Options", *Mathematical Finance* 7(4), 325–349** | `H → H·exp(−βσ√Δt)` for a **down**-barrier, `β = −ζ(½)/√(2π) ≈ 0.5826`; error `O(1/√m) → o(1/√m)` | **Yes — trivially computable** | GBM / Itô with piecewise-continuous coefficients; **needs high monitoring frequency to be accurate** | Extended to jump-diffusions (Dia & Lamberton, arXiv:1012.3882). At once-a-day monitoring the accuracy claim is weak — treat as an order of magnitude |
| **Merton (1973); Reiner & Rubinstein (1991)** | Closed-form prices for all 8 continuously-monitored barrier types | Yes | Black–Scholes | Decorative here — we need probabilities, not prices |
| **Optional stopping (standard); Feller, gambler's ruin** | Driftless continuous path: `P(+a before −b) = b/(a+b)` = **2000/5000 = 40.0%** | **Yes** | Martingale, continuous paths (no overshoot), no time limit | Distribution-free given the martingale property — **the one result here that does NOT need Gaussianity**. Jumps introduce overshoot; a time limit lowers it |
| **Drifted two-sided exit (scale function; Sigman lecture notes, Columbia IEOR 4700)** | `P = (1 − e^{2μb/σ²})/(e^{−2μa/σ²} − e^{2μb/σ²})`; **inverts a pass rate into `θ = 2μ/σ²`** | **Yes — verified by MC here** | BM with constant drift, continuous monitoring, no time limit | Identifies only `θ`. Fat tails/autocorrelation bias the implied edge **upward** (i.e. the true edge is worse than the inversion says) |
| **Dubins, L. & Savage, L. (1965), *How to Gamble If You Must*** | In a **subfair** primitive casino, **bold play** (bet `min{f, 1−f}`) maximises `P(reach the goal)` | Yes (the Dubins–Savage function) | iid bets, no time limit, no minimum-days rule | Structural, not distributional. **This is D379 A2's all-in result, and it is a theorem** |
| **Ross, S. (1974); Maitra, A. & Sudderth, W. (1996), *Discrete Gambling and Stochastic Games*** | If `p ≥ ½`, **timid play** (minimum bet) maximises `P(ever reaching a target)` and stochastically maximises time to ruin | Yes | Red-and-black on the integers, iid | **The complement to Dubins–Savage, and it is the one D379 A3 needs**: with edge, bet small; without, bet everything |
| **MacLean, L., Ziemba, W. & Blazenko, G. (1992), "Growth versus security in dynamic investment analysis", *Management Science* 38(11), 1562–1585** | Kelly is the **most aggressive** defensible criterion; betting more lowers both growth **and** security. Fractional Kelly trades growth for security monotonically | Yes, in their δ-parametrisation | iid returns, log/power utility, no barrier | Qualitative result survives; the *fractions* do not |
| **Busseti, E., Ryu, E. & Boyd, S. (2016), "Risk-Constrained Kelly Gambling", *Journal of Investing* 25(3)** (arXiv:1603.06183) | **Convex** bound on drawdown probability turning a ruin constraint into a tractable convex program; **beats fractional Kelly at matched drawdown risk** | **Yes — a solvable convex program** | General discrete outcome distribution (**not** Gaussian), iid draws | **Best-surviving result in this lane.** The bound is a Cramér/martingale bound: **give it the empirical return distribution and it holds.** iid is still assumed |
| **`P(ever breach a STATIC floor x below the start) = (1−x)^{2/f−1}` (GBM special case of the above; derived, tabulated and MC-checked here)** | 4% **static** floor ⇒ **≈1/9 Kelly** for an even chance of never breaching. **Against a non-locking TRAILING floor the answer is 1 for every f** | **Yes** (static); **no closed form exists** for the trailing case at finite horizon | GBM, continuous monitoring, infinite horizon | No — the exponent shrinks under fat tails. **Optimistic.** And it does **not** apply to a trailing floor: see the verdict correction |
| **Magdon-Ismail, M., Atiya, A., Pratap, A. & Abu-Mostafa, Y. (2004), "On the maximum drawdown of a Brownian motion", *J. Applied Probability* 41(1)** | `E[MDD]` closed form; grows **logarithmically** in T for μ>0, **√T** for μ=0, **linearly** for μ<0 | Yes (series for μ≠0; analytic for μ=0) | BM with drift | The *scaling regimes* are robust; the constants are not |
| **Carpenter, J. (2000), "Does Option Compensation Increase Managerial Risk Appetite?", *Journal of Finance* 55(5)** | **No, not in general.** A risk-averse manager with a call sometimes chooses **lower** volatility than on own account; **more** options → **less** volatility | Yes (dynamic, closed form) | GBM, CRRA manager, no barrier, terminal-date payoff | **The first correction to the naive convexity story.** No knock-out barrier — so it does not directly cover us |
| **Ross, S.A. (2004), "Compensation, Incentives, and the Duality of Risk Aversion and Riskiness", *Journal of Finance* 59(1)** | "Convexity ⇒ more risk-taking" is **false in general**; gives necessary and sufficient conditions | Yes | Expected-utility agent | **The general statement of Carpenter's point.** D379 §5's mechanism must be argued from the *truncation*, not from convexity per se |
| **Hodder, J. & Jackwerth, J. (2007), "Incentive Contracts and Hedge Fund Management", *JFQA* 42(4), 811–826** | Near an **exogenous** liquidation barrier the manager **cuts** risk; near an **endogenous** one they **raise** it. Behaviour persists over multi-year horizons | Numerical (grid) solution | GBM, CRRA manager, high-water mark, management + incentive fee, manager owns fund shares | **The paper that adjudicates D379 §5, and it splits on continuation value.** See verdict |
| **Basak, S., Pavlova, A. & Shapiro, A. (2007), "Optimal Asset Allocation and Risk Shifting in Money Management", *RFS* 20(5), 1583–1621** | Convex flow–performance gives a **finite risk-shifting RANGE**; inside it the manager gambles, and the gamble can **raise or lower** vol depending on risk tolerance | Yes | GBM, complete market, CRRA manager, benchmark | **"Finite range" is the useful part**: risk-shifting is localised near the threshold, not global — consistent with D379 §5's table, where ΔE only turns at ~1% buffer |
| **Basak, S. & Shapiro, A. (2001), "Value-at-Risk-Based Risk Management: Optimal Policies and Asset Prices", *RFS* 14(2), 371–405** | A **VaR** limit makes agents take **larger** risky exposure and incur **larger losses in the worst states** than no limit | Yes | GBM, complete market, CRRA | **A caution on P3, not a refutation** — a prop daily-loss limit is a hard floor, closer to their LEL alternative |
| **Li, W., Lyu, H. & Wei, P. (2026), "Non-concave Corporate Management with Option Incentives under Value-at-Risk Constraint"** (arXiv:2608.05623) | A VaR floor **shifts** rather than suppresses risk; **too strict** a floor **raises** default probability and induces "gambling for recovery" | Yes (concavification + martingale) | GBM, CRRA manager, effort + volatility choice | **The most direct model of the P3/P5 question in the literature.** Says the firm's loss limit has a calibration optimum and can be set past it |
| **Brown, K., Harlow, W. & Starks, L. (1996), "Of Tournaments and Temptations", *Journal of Finance* 51(1), 85–110** | Mid-year **losers raise** fund volatility more than winners — the canonical empirical risk-shifting result | Empirical | 334 growth funds 1976–91, **monthly** returns | **See next row — this is the result that did not replicate** |
| **Busse, J. (2001), "Another Look at Mutual Fund Tournaments", *JFQA* 36(1)** | With **daily** data the tournament effect **disappears**; the monthly finding was a bias in volatility estimates caused by **daily return autocorrelation** | Empirical | Daily fund returns | **Load-bearing methodological warning for us.** The canonical empirical evidence for gambling-for-resurrection is an **autocorrelation artifact in the volatility estimator** |
| **Chevalier, J. & Ellison, G. (1997), "Risk Taking by Mutual Funds as a Response to Incentives", *JPE* 105(6), 1167–1200** | Convex flow–performance shape creates YTD-dependent risk incentives; **holdings-based** evidence that funds act on them | Empirical (semiparametric + holdings) | 1982–92 growth funds | **Stronger than BHS** because it is holdings-based, so Busse's estimator critique does not apply |
| **Kirti, D. (2024), "When gambling for resurrection is too risky", *Journal of Banking & Finance* 162** (ESRB WP 69) | Distressed insurers **reduced** risk; **franchise value**, not capital rules, explains it | Empirical | US insurers, crisis period | **Same conditional as Hodder–Jackwerth, from data**: continuation value suppresses gambling |
| **Embrey, M., Reiss, J.P. & Seel, C. (2024), "Gambling in risk-taking contests: Experimental evidence", *JEBO* 221, 570–585** | Risk-taking observed in **all** treatments — including **without** contest incentives | Experimental | Lab, Seel–Strack stopping task | **Cuts against attributing prop-trader blow-ups to the contest structure.** Subjects gamble anyway |
| **Moreira, A. & Muir, T. (2017), "Volatility-Managed Portfolios", *Journal of Finance* 72(4), 1611–1644** | Scaling exposure by `1/σ²_{t−1}` produces large alphas and Sharpe gains | Empirical | US factor returns, spanning regressions | **Contested — see the next four rows** |
| **Cederburg, S., O'Doherty, M., Wang, F. & Yan, X. (2020), "On the performance of volatility-managed portfolios", *JFE* 138(1), 95–117** | Across **103** strategies, no systematic Sharpe improvement; **real-time OOS versions lose** to the unmanaged portfolios, from structural instability in the spanning regressions | Empirical | US equity strategies | **The out-of-sample failure is the relevant part for us** |
| **Liu, F., Tang, X. & Zhou, G. (2019), "Volatility-Managed Portfolio: Does It Really Work?", *JPM* 46(1), 38–51** | Market-level application carries **look-ahead bias**; corrected, **max drawdown is 68–93%** in almost all cases | Empirical | US market, 1926– | **The single most relevant volatility result in this lane, and it is a warning** — vol-scaling done with a look-ahead-contaminated estimator looks safe and is not |
| **Barroso, P. & Detzel, A. (2021), "Do limits to arbitrage explain the benefits of volatility-managed portfolios?", *JFE* 140(3), 744–767** | After costs (six mitigation schemes) vol-management of **non-market** factors gives **zero** alpha and **lowers** Sharpe; the **market** case survives and is concentrated in easy-to-arbitrage stocks | Empirical | US factors, with cost model | Ties the surviving case to sentiment — not a sizing result |
| **DeMiguel, V., Martín-Utrera, A. & Uppal, R. (2024), "A Multifactor Perspective on Volatility-Managed Portfolios", *Journal of Finance* 79(6), 3859–3891** | Factor risk **prices** fall with market vol; a **conditional multifactor** portfolio beats its unconditional counterpart **OOS and net of costs** | Empirical + model | US factors | The one result that rehabilitates vol-management — but as a **multifactor timing** claim, not a barrier-control one |
| **Landolfi, F. (2026), "Drawdown Risk Beyond Brownian Motion"** (arXiv:2608.00127) | Short-vol archetype (neg. skew, high kurtosis) inflates near-worst max drawdown **1.32×** and max loss **1.29×** vs Gaussian; **Sharpe estimation error alone contributes 1.48×** on max loss | Monte-Carlo framework | Simulated archetypes, fBm for long memory | **This is the number D379's closing caveat lacked.** Working paper, single author — treat as an order of magnitude |
| **Rej, A., Seager, P. & Bouchaud, J-P. (2018), "You are in a drawdown. When should you start worrying?", *Wilmott*** (arXiv:1707.01457) | Exact distributions for depth and length of the **last** drawdown of a drifting BM; managers and investors **systematically underestimate** both, given their assumed Sharpe | **Yes** | BM with drift | The under-estimation finding holds *even under GBM* — before any fat-tail adjustment |
| **Embrechts, P., Klüppelberg, C. & Mikosch, T. (1997), *Modelling Extremal Events*** | Under **subexponential** claim sizes the Cramér–Lundberg exponential ruin bound **fails**; ruin decays like a **power law** | Yes (asymptotics) | Cramér–Lundberg risk process | **The formal statement of D379's caveat.** Every exponential bound in this table is optimistic when the P&L tail is subexponential |
| **Acadian, "Serial Killer: Drawdowns and Serial Correlation"** *(practitioner tier)* | Raising monthly serial correlation **0 → +0.1** inflates drawdowns as much as **lowering Sharpe from 0.5 to 0.4** | Simulation | AR(1) monthly returns | Not peer-reviewed. Quoted only as a magnitude |

---

## Per-topic notes

### 1. Barrier option pricing

The pricing side is solved and is not our bottleneck. Merton (1973) gave the down-and-out call;
Reiner & Rubinstein (1991) the full set of eight. **What we need from this literature is one thing
only: the discrete-monitoring correction**, because the schema's field 7 (drawdown type) and field 9
(open-equity vs closed-balance basis) differ across firms in exactly the way BGK prices.

**BGK's correction and its direction.** Discrete monitoring can only *miss* excursions between
observations, so a discretely-monitored down-and-out is worth **more** than its continuous
counterpart, and prices as a continuous option on a **lower** barrier: `H_eff = H·exp(−βσ√Δt)` with
`β = −ζ(½)/√(2π) ≈ 0.5826`. The error goes from `O(1/√m)` to `o(1/√m)`.

**Two caveats that bite here.** (i) BGK is accurate **when monitoring is frequent**; once-a-day is
not frequent, and the literature says so explicitly. Use the number as an order of magnitude, not a
price. (ii) The prop distinction is not purely a frequency distinction. An intraday floor on
**open equity** is monitored on a *different quantity* from an EOD floor on **closed balance** — BGK
prices the frequency gap and is silent on the quantity gap. **The table above is a lower bound on how
much more forgiving an EOD floor is.**

### 2. Optimal stopping and gambler's ruin

**D379's 40% is optional stopping and needs no Gaussianity.** For any process with continuous paths
that is a martingale, `E[X_τ] = 0` gives `P(+a before −b) = b/(a+b)` exactly. It is the most robust
result in this lane. It **does** need: no time limit, no minimum-trading-days rule, no overshoot at
the barriers, and zero drift after costs. A discrete bet size introduces overshoot at both ends, and
a time limit strictly lowers the number.

**The drifted extension is the useful one** and inverts a claimed pass rate — see verdict. **Only
`θ = 2μ/σ²` is identified.** Two firms quoting the same pass rate on different geometries do not
imply the same edge, and the same trader at two sizes has the same μ/σ and different θ. **This is
directly why D379 A3's rebuttal of the transcript is right**: `P(pass)` is a function of edge, cost
and geometry, not a free parameter.

**Bold and timid play, which is D379 A2 and A3 stated as theorems.** Dubins & Savage (1965): in a
**subfair** primitive casino, **bold play maximises the probability of reaching the goal.** Ross
(1974) / Maitra & Sudderth (1996): if the game is **fair or favourable**, **timid play** maximises
the probability of ever reaching the target *and* stochastically maximises time to ruin. Together
they say precisely what D379 A2 found numerically: at zero edge, put the whole buffer on one trade;
with edge, bet the minimum.

> **A new, checkable prediction this produces: the minimum-trading-days rule is the firm's defence
> against Dubins–Savage bold play, in the same way that D379 §5 identifies P3/P5 as the defence
> against near-barrier convexity.** Bold play recovers 40.0% from 26.5% at zero edge (D379 A2);
> a rule requiring N distinct trading days makes it unavailable by construction. **This is
> falsifiable against lanes 01–05 field 12: if minimum-trading-days is universal across geometries
> while consistency rules are not, that ordering is evidence for the mechanism.**

Caveat: our evaluation is not red-and-black. Payoffs are asymmetric (1:1.5), the floor **trails**,
and costs are paid per round turn. The theorems fix the *direction* of the optimal policy, not the
number.

**Finite horizon.** With a time limit the two-sided exit probability is a reflection/image series
rather than a ratio of exponentials; it is standard but has no compact form worth quoting. For our
purposes Stage 0's simulation is the right tool, not a series.

### 3. Drawdown-constrained portfolio choice

The line runs **Grossman & Zhou (1993) → Cvitanić & Karatzas (1995) → Cherny & Obłój (2013)**, with
**Elie & Touzi (2008)** adding consumption and **Angoshtari, Bayraktar & Young (2016)** solving the
pure survival objective. The reported optimal policy is consistent across the family: **risky
exposure proportional to the surplus `W − αM`, vanishing at the floor.** At the high-water mark it
reduces to the unconstrained Merton/Kelly allocation.

*(I could not obtain the exact coefficient from a primary source — SSRN returns 403 and the arXiv
PDFs did not extract. The **sign** and the **limit at the floor** are what is load-bearing and are
reported consistently by five independent secondary sources in the log. Treat the exact
`π_M · (W − αM)/((1−α)W)` form as unverified.)*

**Two things this family gets us and one it does not.**

- **Cherny & Obłój is the assumption-robust one.** Semimartingale market; the constrained optimum is
  an explicit pathwise transform of the unconstrained one. That is the version that survives contact
  with a fat-tailed P&L series — the transform is pathwise, so it does not care about the
  distribution.
- **Klass & Nowicki (2005) is a direct warning**: GZ's strategy is **not** optimal in discrete time,
  and our floor is monitored on a discrete grid.
- **What it does not get us is our objective.** Every paper here maximises a utility of the agent's
  *own* terminal wealth. D379's `V = E[payouts | survival] × P(survival)` has a payoff that is
  bounded below at −fee and **capped above by the payout ladder** (§4). That object — a knock-out
  call *spread* whose holder chooses the volatility — **is not in this literature.**

### 4. Kelly and growth-optimal betting under a ruin constraint

**MacLean, Ziemba & Blazenko (1992)** is the canonical growth-versus-security statement: Kelly is the
**most aggressive** defensible criterion; over-betting loses on both axes; fractional Kelly buys
security by giving up growth, monotonically. That is D379 §2's shape, in a literature that predates
it by 34 years.

**Busseti, Ryu & Boyd (2016) is the one I would actually run.** It bounds `P(drawdown to a given
level)` with a convex constraint, so a growth-optimal bet under a *stated* ruin tolerance is a
solvable convex program. **It takes a general outcome distribution, not a Gaussian** — feed it the
empirical per-trade P&L distribution and the bound holds. It also reports that its solutions beat
fractional Kelly at matched drawdown risk. Remaining assumption: **iid draws**, which our own
evidence contradicts (BOOK_PROP's C1 tail was regime-driven).

**The GBM special case tabulated in the verdict — `(1−x)^{2/f−1}` — is the number to carry, for a
STATIC floor.** A 4% static floor demands roughly **1/9 Kelly** for an even chance of never
breaching. Set against D379 §3's observation that C1's value was still rising as size fell to 0.48x,
this says the search for the peak should run **an order of magnitude** below the boundary of that
sweep, not a factor of two.

**And the trailing case has no closed form at all, because at infinite horizon the answer is
degenerate.** The drawdown process is a reflected BM with negative drift: positive recurrent, so its
*stationary* depth is `Exp(2m/s²)` — mean `s²/2m` — but its running supremum diverges, so a
never-locking trailing floor is breached with probability 1 at any size. **Magdon-Ismail et al.
(2004) give the right finite-horizon object**: `E[MDD]` grows **logarithmically in T** for positive
drift, `√T` at zero drift, **linearly** for negative drift. That trichotomy is the honest way to read
D379's caveat about C1's twenty-account plan: the account life needed for a given expected drawdown
scales exponentially in the buffer when the edge is positive and only linearly when it is not.

### 5. Risk-shifting under convex compensation — the direct test of D379 §5

**D379 §5 states in writing:** near the barrier the account's convexity inverts, variance becomes
free, and consistency rules are the firm's defence against a risk-shifting incentive the instrument
creates. **The literature's verdict: supported in mechanism, but conditional, and the naive version
of the argument is wrong.**

**Where it is refined.**

- **Ross (2004)** and **Carpenter (2000)**: convexity alone does **not** imply more risk-taking. A
  risk-averse manager with a call can optimally choose **lower** volatility than on own account, and
  **more** options can mean **less** volatility. **D379 §5's mechanism must therefore be argued from
  the truncation of downside at a sunk fee, not from the convex kink** — and D379's own toy is
  risk-neutral in payout, which is what makes its result go through.
- **Basak, Pavlova & Shapiro (2007)**: risk-shifting occupies a **finite range** near the threshold,
  not the whole state space, and the sign of the vol change depends on risk tolerance. D379 §5's own
  table agrees: ΔE[payout] is essentially flat at 4.00% and 2.00% of buffer and only turns at 1.00%
  and 0.30%.
- **Hodder & Jackwerth (2007)**: **exogenous** barrier → risk **falls** near the boundary;
  **endogenous** → risk **rises**. The discriminant is continuation value. **Kirti (2024)** confirms
  empirically that franchise value suppresses the gamble.

**Where the empirical support is weaker than D379 assumes.** The canonical evidence — **Brown, Harlow
& Starks (1996)** — **did not replicate**. **Busse (2001)** showed with daily data that the
tournament effect vanishes, and that the monthly result was a **bias in the volatility estimator
caused by daily return autocorrelation**. Only **Chevalier & Ellison (1997)**, which is holdings-based
and so immune to that critique, survives cleanly. And **Embrey, Reiss & Seel (2024)** find lab
subjects gamble in a stopping task **even without contest incentives** — so observed prop-trader
blow-ups are weak evidence for the mechanism.

> **This is a house-rule point, not just a literature point.** Busse's failure is exactly the class
> `assert-code-not-data` and CLAUDE.md's "test the statistic, not just the story"
> warn about: a mechanism filed on a statistic whose estimator was biased by autocorrelation.
> **If we ever measure near-barrier risk-shifting in our own P&L, measure it at the highest available
> frequency and from positions, not from a realised-vol estimate on coarse buckets.**

**Where the firm's defence is itself questioned.** **Basak & Shapiro (2001)**: VaR-type limits can
make the worst states worse. **Li, Lyu & Wei (2026)**: a VaR floor **shifts** risk-taking, binding
floors raise **effort**, moderate floors reduce default, and **too-strict** floors **raise** default
by inducing gambling for recovery. **Neither refutes P3** — a hard daily-loss floor is not a VaR —
but both say the firm's loss limit has a calibration optimum with a sign that flips past it, which
is a claim about the *firm's* problem that no lane in this research has framed.

### 6. Economics of the funded-account industry — `NOT PUBLISHED`

**Four independent attempts, all negative** (probes 6, 7, 8, 22 in the log):

- Generic web search for peer-reviewed or working-paper work on prop-firm evaluation economics —
  returned only industry blogs and one non-peer-reviewed ResearchGate item.
- **SSRN keyword search — HTTP 403**, blocked to WebFetch.
- **arXiv full-text API** for `"prop firm" OR "funded trader" OR "proprietary trading firm"` — **2
  hits, both using "proprietary trading firm" incidentally** (electricity-market bidding; basket
  liquidation). **Zero** on retail evaluations.
- Search for 2024–25 SSRN work on retail funded accounts — nothing academic.

**Conclusion: there is no peer-reviewed or working-paper literature on the retail funded-account
industry.** The nearest adjacent bodies are the mutual-fund tournament literature (§5 above) and the
retail-gambling/lottery-preference literature. **Lane 06 (regulatory and litigation) is therefore the
highest evidence tier available for the industry's own economics, exactly as the schema anticipated.**

**Also `NOT PUBLISHED`: consistency rules.** No academic treatment of a cap on a single day's share
of cumulative profit, as a contract-design object, exists (probe 30). The closest theoretical relative
is the capped-bonus / non-concave-utility literature (Li, Lyu & Wei 2026), which caps the *payoff*,
not the *path*.

### 7. Volatility-managed portfolios as a size-control policy

The literature is genuinely contested and **the contest is about the wrong question for us.**

Moreira & Muir (2017) claim alpha. Cederburg et al. (2020) find no systematic Sharpe gain across 103
strategies and **out-of-sample failure** traceable to structural instability in the spanning
regressions. Barroso & Detzel (2021) find that after costs only the **market** case survives, and it
is concentrated in easy-to-arbitrage names. Liu, Tang & Zhou (2019) find the market-level result was
**look-ahead biased**, and once corrected the strategy carries a **68–93% maximum drawdown**. DeMiguel,
Martín-Utrera & Uppal (2024) rehabilitate a **conditional multifactor** version that beats its
unconditional counterpart out of sample and net of costs.

**For our purpose all five are about *return timing*.** The barrier question is whether scaling size
by an ex-ante volatility estimate lowers `P(breach)` at a given expected P&L — a much weaker claim
than alpha, which none of the critics disputes and which none of the papers tests. **The literature
does not adjudicate vol-scaling as a barrier control, and it should not be cited as if it does.**

**What it does give us is one methodological warning we should take personally.** LTZ's finding is
that the headline vol-managed result was an artifact of using a volatility estimate that peeked. Our
own C1 evidence — D260's vol-targeted overnight hold, the source of D379 §3's table — is a
vol-targeting sweep. **The estimator's information set is the thing to audit there.**

### 8. Do these results survive fat tails and autocorrelation?

D379's closing caveat says both its toy and any closed form **understate ruin**. The literature
confirms it and puts a rough size on it.

- **Embrechts, Klüppelberg & Mikosch (1997)** is the formal statement: under **subexponential** loss
  tails the Cramér–Lundberg **exponential** bound fails and ruin decays like a **power law**. Every
  exponential bound in this lane — including `(1−x)^{2/f−1}` — is optimistic.
- **Landolfi (2026)** puts numbers on it: negative-skew/high-kurtosis P&L inflates near-worst max
  drawdown **≈1.32×** and max loss **≈1.29×**; **Sharpe estimation error alone contributes 1.48×** on
  max loss, larger than any style effect. His long-memory result is instructive in the other
  direction — the apparent 8× amplification at H = 0.8 is **≈90% dispersion rescaling, not path
  geometry**, and once dispersion is horizon-matched persistent processes are *shallower*. **So
  "autocorrelation makes drawdowns worse" is mostly a `√T`-scaling error, not a path effect** — which
  is worth knowing before we build a mechanism on it.
- **Rej, Seager & Bouchaud (2018)** show that managers underestimate drawdown depth and duration
  **even under GBM**, before any tail adjustment.
- **Acadian** *(practitioner)*: monthly serial correlation 0 → +0.1 costs about as much drawdown as
  dropping Sharpe from 0.5 to 0.4.

**What that costs in pass rate, computed here.** Treating the inflation as an equivalent shrinking
of the buffer, against a static `a = $3,000 / b = $2,000` geometry at zero edge:

| depth multiplier | effective buffer | zero-edge pass rate |
|---:|---:|---:|
| 1.00 (Gaussian) | $2,000 | **40.0%** |
| 1.10 | $1,818 | 37.7% |
| **1.32** (short-vol archetype) | $1,515 | **33.6%** |
| 1.48 (Sharpe-error inclusive) | $1,351 | 31.1% |

**So the fat-tail correction to a zero-edge pass rate is on the order of 6–9 percentage points on a
static floor** — material, but smaller than the 13.5-point gap D379 A2 measured between the static
and the trailing floor. **Geometry dominates tails.** That ordering is worth carrying into Stage 0.

---

## What the literature does NOT answer

1. **Optimal volatility choice for a knock-out call SPREAD held by its own volatility-setter.**
   D379 §4's object — barrier below, ladder cap above, holder chooses σ, holder's downside truncated
   at a sunk fee. Carpenter (2000) has the cap-free version; Hodder & Jackwerth (2007) has the
   barrier but a manager who owns shares and earns fees; the non-concave-utility papers cap the payoff
   but have no knock-out. **Nobody has assembled all three.** D379 §4's central claim — *the
   value-maximising size is the smallest size that reaches the ladder with high probability* — is
   **not in the literature** and would have to be computed, not cited.

2. **A portfolio of purchasable barrier options with a per-unit acquisition cost.** D379 A1's
   `V = N × [P(pass)·E[payout | funded] − fee]` with N a choice variable. The literature prices *one*
   claim taken as given. Nothing addresses buying N of them, nor the correlation between the N
   accounts a single trader runs — which is 1 if they copy-trade, exactly D379 A4's point.

3. **A TRAILING (ratcheting) floor that LOCKS.** Every barrier result above assumes a **fixed**
   barrier; every drawdown result assumes a floor at a **fixed fraction of the running max**. The
   prop trailing floor is neither: it ratchets with the high-water mark and then **locks** at a
   stated level (schema field 10). **No closed form covers it**, and the two limiting cases it sits
   between are both degenerate for our purposes — a static floor has the tabulated closed form, and a
   non-locking trailing floor is breached with probability 1 at infinite horizon (verdict item 2).
   **D379 A2's 26.5% was simulated, and it has to be — but it must also be quoted with its horizon,
   which the record does not currently do.**

4. **Path constraints on the payoff.** Consistency rules — no day above ~40% of trailing profit —
   have no academic treatment at all (§6). The nearest theory caps the *payoff*, not the *path*.

5. **Whether a hard daily-loss floor beats a VaR-style one for the FIRM.** Basak & Shapiro (2001) and
   Li, Lyu & Wei (2026) both suggest a badly calibrated loss constraint backfires; neither models the
   prop firm's actual instrument (a hard floor plus a knock-out plus a consistency rule) nor asks
   what the *firm's* optimum is. **That is the counterparty's problem and nothing in this research
   has framed it.**

6. **The joint distribution of pass rate and payout size.** D379's `V` needs `E[payout | funded]`, not
   just `P(pass)`. These are the same path, so they are dependent — a trader who passes by bold play
   arrives at the funded account with a different size policy than one who passes by timid play.
   **Everything in the literature treats survival and payoff separately.**

7. **Whether vol-scaling lowers `P(breach)` net of costs.** The entire volatility-managed literature
   is about return timing (§7). The barrier question is untested there.

8. **Anything at all about the retail funded-account industry.** §6: `NOT PUBLISHED`, four attempts
   logged.

---

## Sources

**Tier key.** `primary` = peer-reviewed paper, working paper with a number, or an author's own copy.
`secondary` = abstract/index page, publisher listing, lecture notes. `claims` = marketing, blogs,
practitioner posts. **Negative results are logged.** All accessed **2026-09-08**.

| # | URL | tier | what was sought | what it yielded |
|---:|---|---|---|---|
| 1 | https://ideas.repec.org/a/bla/mathfi/v7y1997i4p325-349.html — plus https://onlinelibrary.wiley.com/doi/abs/10.1111/1467-9965.00035 | secondary | Broadie–Glasserman–Kou citation | Full citation: *Mathematical Finance* 7(4), 325–349, Oct 1997 |
| 2 | https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1467-9965.1993.tb00044.x — plus https://www.sciencedirect.com/science/article/abs/pii/S0167715205001641 | secondary | Grossman–Zhou (1993) | Citation *Math. Finance* 3(3), 241–276; constraint `W ≥ αM`; **and** Klass & Nowicki (2005), GZ not optimal in discrete time |
| 3 | http://www.its.caltech.edu/~cvitanic/papers.html — plus https://www.researchgate.net/publication/2766393 | secondary | Cvitanić–Karatzas (1995) | Citation *IMA Lecture Notes* 65, 77–88; martingale method, maps constrained → unconstrained, multi-asset |
| 4 | https://onlinelibrary.wiley.com/doi/abs/10.1111/0022-1082.00288 — plus https://pages.stern.nyu.edu/~jcarpen0/pdfs/Carpenter2000.pdf | primary | Carpenter (2000) result | **Convexity does NOT imply more risk**; more options → less vol; option ends deep in or deep out |
| 5 | https://academic.oup.com/rfs/article/20/5/1583/1592528 — plus https://pages.stern.nyu.edu/~ashapiro/papers/RiskShiftingRFS07.pdf | primary | Basak–Pavlova–Shapiro (2007) | *RFS* 20(5), 1583–1621; **finite** risk-shifting range; vol can rise or fall with risk tolerance |
| 6 | https://www.researchgate.net/publication/396851394 + https://www.simtrade.fr/blog_simtrade/business-model-proprietary-trading-firms/ + assorted firm blogs | claims | peer-reviewed prop-firm economics | **NOTHING academic.** One non-peer-reviewed RG item; rest are industry blogs |
| 7 | https://papers.ssrn.com/sol3/results.cfm?txtKey_Words=proprietary+trading+firm+challenge+funded+trader | — | SSRN keyword search | **BLOCKED — HTTP 403.** No results retrievable |
| 8 | http://export.arxiv.org/api/query?search_query=all:"prop firm" OR all:"funded trader" OR all:"proprietary trading firm" | primary | arXiv full text | **2 hits, both incidental** (electricity-market bidding; basket liquidation). **Zero on retail evaluations** |
| 9 | https://arxiv.org/abs/1506.00166 (abs page; the PDF fetch returned a garbled citation and was discarded) | primary | drawdown-minimising policy | Angoshtari, Bayraktar & Young; Black–Scholes; minimise `P(hit fraction of running max)` with a payout function |
| 10 | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2732905 + https://www.tandfonline.com/doi/abs/10.1080/17442508.2016.1155590 | secondary | publication venue for #9 | *Stochastics* 88(6), 2016 |
| 11 | https://link.springer.com/article/10.1023/A:1018969727211 + https://econpapers.repec.org/RePEc:inm:ormnsc:v:38:y:1992:i:11:p:1562-1585 | secondary | MacLean–Ziemba–Blazenko (1992) | *Management Science* 38(11), 1562–1585; Kelly is the most aggressive defensible criterion |
| 12 | https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.1996.tb05203.x + https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7460 | primary | Brown–Harlow–Starks (1996) | *JF* 51(1), 85–110; mid-year losers raise vol; 334 funds, 1976–91, **monthly** data |
| 13 | https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/abs/another-look-at-mutual-fundtournaments/CD3356D7C7EDDC18D960CEF90CA7D84F + https://papers.ssrn.com/sol3/papers.cfm?abstract_id=110028 | primary | replication of #12 | **Busse (2001): effect DISAPPEARS with daily data; the monthly result was an autocorrelation-induced bias in the vol estimator.** The most important negative in this lane |
| 14 | https://www.semanticscholar.org/paper/…/6613c5c222e8d158546023b0a954195467d3b8e8 | secondary | BGK abstract | **NOTHING — page returned empty** |
| 15 | https://almostsuremath.com/2023/07/01/discrete-barrier-approximations/ | secondary | BGK correction form | `H̃ = H − βσ√Δt`, `β = −ζ(½)/√(2π) ≈ 0.5826`, error `o(1/√n)`; Itô with piecewise-continuous coefficients |
| 16 | https://www.columbia.edu/~sk75/mfBGK.pdf + http://www.columbia.edu/~mnb2/broadie/Assets/bgk_mf.pdf | primary | BGK theorem, barrier direction | **PDF text extraction FAILED both times.** Direction and multiplicative form recovered from #15 and #29 instead |
| 17 | https://arxiv.org/pdf/1012.3882 (listed, not fetched) | primary | BGK under jumps | Noted: continuity correction extends to jump-diffusion models |
| 18 | https://arxiv.org/pdf/1506.00166 (PDF) | primary | closed-form drawdown policy | **PARTIAL/UNRELIABLE** — returned a wrong citation. Superseded by #9 |
| 19 | https://doi.org/10.2139/ssrn.703 + https://arxiv.org/pdf/math/0703824 (listed) | secondary | Browne, "Reaching goals by a deadline" | *Adv. Appl. Prob.* 31, 551–577 (1999); maximise `P(reach a wealth level by a fixed time)` |
| 20 | https://arxiv.org/abs/1603.06183 + https://web.stanford.edu/~boyd/papers/pdf/kelly.pdf | primary | Kelly under a ruin constraint | **Busseti–Ryu–Boyd:** convex bound on drawdown probability → tractable program; **general outcome distribution**; beats fractional Kelly at matched risk |
| 21 | https://www.sciencedirect.com/science/article/abs/pii/S0304405X2030132X + https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3357038 | primary | Cederburg et al. (2020) | *JFE* 138(1), 95–117; 103 strategies; **OOS versions lose**; structural instability in spanning regressions |
| 22 | assorted 2025–26 industry pages (quantvps, investinglive, theindustryspread, copilink) | claims | academic prop-firm work, 2024–25 | **NOTHING academic.** Industry figures only; not used |
| 23 | https://arxiv.org/abs/1110.6289 + https://link.springer.com/article/10.1007/s00780-013-0209-4 | primary | generality of the drawdown result | **Cherny & Obłój:** constrained = unconstrained with modified utility; **abstract semimartingale** market; explicit pathwise transform |
| 24 | https://onlinelibrary.wiley.com/doi/full/10.1111/jofi.13395 + https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3982504 | primary | DeMiguel et al. (2024) | *JF* 79(6), 3859–3891; conditional multifactor portfolio beats unconditional **OOS and net of costs** |
| 25 | https://ideas.repec.org/a/ucp/jpolec/v105y1997i6p1167-1200.html + https://www.journals.uchicago.edu/doi/10.1086/516389 | primary | Chevalier–Ellison (1997) | *JPE* 105(6), 1167–1200; **holdings-based**, so immune to Busse's estimator critique |
| 26 | https://www.abebooks.com/… + https://www.randomservices.org/random/games/RedBlack.html + https://hannig.cloudapps.unc.edu/STOR054/handouts/Casino.pdf (PDF extraction failed) | secondary | Dubins–Savage bold play | **Bold play (`bet min{f,1−f}`) maximises `P(reach goal)` in a subfair primitive casino.** The PDF itself was unreadable; result taken from the index pages |
| 27 | https://medium.com/@polanitzer/… + https://www.quantt.co.uk/resources/barrier-options-explained | claims/secondary | Merton and Reiner–Rubinstein | Merton (1973) first down-and-out call closed form; Reiner & Rubinstein (1991) all eight types |
| 28 | https://static.sched.com/hosted_files/aria2021annualmeeting/ac/3B2… + https://www.esrb.europa.eu/pub/pdf/wp/esrb.wp69.en.pdf + https://ideas.repec.org/a/eee/jbfina/v162y2024ics0378426624000451.html | primary | gambling for resurrection | **Kirti (2024), *JBF* 162 (ESRB WP 69): franchise value suppresses the gamble**; distressed insurers reduced risk within identical regulatory buckets |
| 29 | https://www1.se.cuhk.edu.hk/~lfli/FPEE_FS.pdf (via search) | secondary | BGK error order and validity | Confirms `O(1/√m) → o(1/√m)`; **and the caveat that the correction is only acceptable at HIGH monitoring frequency** |
| 30 | https://newyorkcityservers.com/blog/… + https://propfirmapp.com/learn/consistency-rule + academic re-search (Jackson 2007 *Econometrica*, JPE Micro, FTC WPs) | claims | academic treatment of consistency rules | **NOTHING.** No academic literature on a path cap of this form. Marked `NOT PUBLISHED` |
| 31 | https://arxiv.org/pdf/2203.13446 + https://www.imperial.ac.uk/media/…/BLANDA_VALENTIN… + assorted | secondary | optimal σ for a knock-out call spread | **NOTHING new.** Only standard barrier-pricing material already logged |
| 32 | https://mediatum.ub.tum.de/doc/1114133/1114133.pdf + https://arxiv.org/pdf/2306.17656 | secondary | finite-horizon double-barrier exit | Confirmed a power-series / Laplace-transform representation exists; **no new load-bearing result** |
| 33 | https://arxiv.org/pdf/1206.2305 | primary | exact GZ policy coefficient | **PDF text extraction FAILED.** Coefficient left unverified |
| 34 | search: explicit `π` formula under a drawdown constraint | secondary | same as #33 | **NOTHING new** — only restatements of "proportional to the surplus `W − αM`" already logged at #2, #3, #23 |
| — | *(items below were found inside the probes above and are logged for citation completeness)* | | | |
| 35 | https://onlinelibrary.wiley.com/doi/10.1002/wilm.10646 + https://arxiv.org/pdf/1707.01457 | primary | drawdown expectations vs Sharpe | **Rej, Seager & Bouchaud (2018):** exact depth/length distributions for the last drawdown; managers **underestimate both** even under GBM |
| 36 | https://arxiv.org/html/2608.00127 | primary | fat tails and long memory in drawdown | **Landolfi (2026):** short-vol archetype **1.32×** max DD, **1.29×** max loss; **Sharpe estimation error 1.48×**; long-memory amplification is **≈90% dispersion rescaling, not path geometry** |
| 37 | https://www.cs.rpi.edu/~magdon/ps/journal/drawdown_journal.pdf + https://authors.library.caltech.edu/records/nx99z-mnz54 | primary | E[max drawdown] closed form | **Magdon-Ismail, Atiya, Pratap & Abu-Mostafa (2004), *JAP* 41(1):** log growth in T for μ>0, √T for μ=0, linear for μ<0 |
| 38 | https://www.acadian-asset.com/investment-insights/owenomics/serial-killer-drawdowns-and-serial-correlation | claims | autocorrelation and drawdown | Monthly serial correlation 0 → +0.1 ≈ Sharpe 0.5 → 0.4 in drawdown terms. **Practitioner tier; quoted as a magnitude only** |
| 39 | https://arxiv.org/html/2608.05623 | primary | risk constraint vs option incentives | **Li, Lyu & Wei (2026):** VaR floor **shifts** rather than suppresses risk; **too strict a floor RAISES default** and induces gambling for recovery; binding floors raise effort |
| 40 | https://academic.oup.com/rfs/article-abstract/14/2/371/1601252 + https://www.ssrn.com/abstract=204390 | primary | VaR-based risk management | **Basak & Shapiro (2001), *RFS* 14(2), 371–405:** VaR managers take **larger** exposure and incur **larger losses in the worst states** |
| 41 | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=970439 + https://www.cambridge.org/core/…/incentive-contracts-and-hedge-fund-management/… | primary | Hodder–Jackwerth (2007) | **BOTH BLOCKED (403 / 500).** Result recovered from #42 and #43 instead |
| 42 | https://arxiv.org/html/2011.13268 (Saunders, Seco & Senn, "Price of liquidity in the reinsurance of fund returns") | primary | H&J's barrier result, second-hand | Confirms "significant change in willingness to take riskier positions when fund performance is close to the barrier" |
| 43 | search on H&J exogenous vs endogenous barrier; https://mpra.ub.uni-muenchen.de/11632/ (PDF extraction failed), https://ideas.repec.org/p/pra/mprapa/11632.html | secondary | the split result | **Exogenous barrier → manager REDUCES risk near the boundary; endogenous shutdown → manager INCREASES it.** *JFQA* 42(4), 811–826. **The adjudicating result for D379 §5** |
| 44 | https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2004.00631.x | primary | Ross (2004) | *JF* 59(1); "convexity ⇒ risk-taking" is **false in general**; gives necessary and sufficient conditions |
| 45 | https://ideas.repec.org/a/eee/jeborg/v221y2024icp570-585.html + https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3668143 (ScienceDirect page 403) | primary | contest risk-taking, experimental | **Embrey, Reiss & Seel (2024), *JEBO* 221, 570–585:** risk-taking in **all** treatments, **including without contest incentives** |
| 46 | https://profiles.wustl.edu/en/publications/volatility-managed-portfolio-does-it-really-work/ + https://jpm.pm-research.com/content/early/2019/09/17/jpm.2019.1.107 | primary | vol-managed critique | **Liu, Tang & Zhou (2019), *JPM* 46(1), 38–51: look-ahead bias; corrected, max drawdown 68–93%** |
| 47 | https://www.sciencedirect.com/science/article/abs/pii/S0304405X21000775 + https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3088828 | primary | vol-managed net of costs | **Barroso & Detzel (2021), *JFE* 140(3), 744–767:** after costs only the market case survives; non-market factors give zero alpha and lower Sharpe |
| 48 | https://www.nber.org/papers/w22208 + https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12513 | primary | Moreira & Muir (2017) | *JF* 72(4), 1611–1644 (NBER WP 22208) |
| 49 | https://www.randomservices.org/random/games/Optimal.html + https://stats.libretexts.org/…/13.11%3A_Optimal_Strategies + http://users.stat.umn.edu/~sudde001/personal_page/Goals.pdf | secondary | timid play for favourable games | **Ross (1974); Maitra & Sudderth (1996):** if `p ≥ ½`, **timid play** maximises `P(ever reaching the goal)` and stochastically maximises time to ruin |
| 50 | search on Embrechts–Klüppelberg–Mikosch subexponential ruin | secondary | fat-tailed ruin asymptotics | *Modelling Extremal Events* (1997/2013): under subexponential claims the **exponential Cramér–Lundberg bound fails; power-law asymptotics** |
| 51 | http://www.columbia.edu/~ks20/FE-Notes/4700-07-Notes-BM.pdf | secondary | drifted two-sided exit formula | **PDF extraction FAILED.** Formula derived here from the scale function `s(x) = e^{−2μx/σ²}` and **verified by 200k-path Monte Carlo** — see verdict item 1 |

### Computations performed in this lane (not sources)

All run with the repo `.venv`. **None touches a fixture; none is evidence under R15.**

1. **Drifted two-sided exit vs Monte Carlo** — 200k paths, `dt = 1/5040`, seed 7. Closed form
   0.4000 / 0.4302 / 0.4912 / 0.3703 vs MC 0.4014 / 0.4341 / 0.4966 / 0.3741 at
   μ = 0 / 0.05 / 0.15 / −0.05 (σ = 0.20, a = 0.06, b = 0.04). Agreement to the MC's discretisation
   bias, whose **sign is the discrete-monitoring overshoot** of BGK.
2. **Pass-rate inversion table** — `brentq` on `θ` for `a = 3000`, `b = 2000`.
3. **`(1−x)^{2/f−1}` tables and its inversion for f** — analytic; the exponent derived here
   (log drift `S²(f − f²/2)`, vol `fS`). **The Monte-Carlo check killed my first reading of it**
   (200k paths, 200 yr, seed 3): against a *trailing* floor the MC returned **1.0000** at
   f = 1, 1/4 and 1/9 against closed forms of 0.9600, 0.7514 and 0.4992. The formula is the
   **static**-floor result; the trailing case is degenerate at infinite horizon. Re-checked in the
   static form (40k paths, 40 yr, `dt = 1/1260`, seed 11): closed 0.9600 / 0.7514 / 0.4992 vs MC
   **0.9442 / 0.7340 / 0.4884** at f = 1 / 1/4 / 1/9 — agreement, with the MC biased **low** as
   discrete monitoring and a finite horizon both require. **This is the "a self-test that cannot
   fail is worse than none" rule paying for itself: the error was in the interpretation, not the
   algebra, and only the MC exposed it.**
4. **BGK shift magnitudes** at σ_$ = 250 / 500 / 1000 per day.
5. **Fat-tail cost in pass rate** — buffer shrunk by the Landolfi multipliers, static-floor formula.

All are reproducible from the stated parameters. **Under CLAUDE.md's file contract none is committed
to `data/`** — this is a review, and they are illustrations of published closed forms, not
measurements.
