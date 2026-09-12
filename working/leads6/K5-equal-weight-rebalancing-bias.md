# K5 — THE EQUAL-WEIGHTED DAILY-REBALANCING BIAS

**Round 6, lane K5 (method). External literature only.** I have no access to this programme's data
and claim nothing about it. Under [R15](../../docs/RULES.md#r15) nothing here closes or admits
anything.

---

## THE HEADLINE, STATED NEGATIVELY FIRST

**A book that holds positions for multiple bars and only re-equalises on entry and exit does NOT
carry the large version of this bias. It carries roughly `1/H` of it, where `H` is the holding
period in bars.** That is not my inference: it falls out of a proposition I read in full in
Asparouhova–Bessembinder–Kalcheva, whose `RW(s)` estimator family has the Blume–Stambaugh
buy-and-hold portfolio as a special case, and whose bias term is **exactly zero for every bar after
the first of a hold** when the price noise is serially uncorrelated. §5 gives the algebra.

**And at this programme's own measured spread the absolute size is small.** Using the closed form
(§1, verified by enumeration) with the round-trip spread implied by the programme's measured
**33.8 bp/side** on held names:

| construction | bias per bar | annualised (252 bars) | over 4,187 bars |
|---|--:|--:|--:|
| re-equalise every bar (`H=1`) | 0.114 bp | **+0.288 %/yr** | +4.90 % total |
| `H=5` bars | 0.023 bp | +0.058 %/yr | +0.98 % |
| `H=20` bars | 0.006 bp | +0.014 %/yr | +0.24 % |
| `H=40` bars | 0.003 bp | +0.007 %/yr | +0.12 % |

*(my arithmetic, [`data/k5_rebalancing_bias_calc.py`](../../data/k5_rebalancing_bias_calc.py), output
in [`data/k5_rebalancing_bias_calc_output.txt`](../../data/k5_rebalancing_bias_calc_output.txt), from a
formula I read and independently verified — not a published figure)*

**The single most useful cross-check in this brief:** invert the formula on the programme's own
prior measurement. `J3`'s **+0.30 %/yr** for the deciles above the floor implies an effective
round-trip spread of **69.0 bp = 34.5 bp/side**. The programme independently measured
**33.8 bp/side** on held names. Those agree to **2 %**. The `+6.79 %/yr` microcap figure implies
**161 bp/side**, which is what a sub-$5 name costs. **So `J3`'s measurement, the published
mechanism, and the programme's own Corwin–Schultz spread all reconcile quantitatively, and the
mechanism is bid-ask bounce.** That is a confirmation of `J3`, not a correction of it.

**The consequence that matters operationally: the bias lives almost entirely in GROSS.** 0.114 bp
per rebalance against a 33.8 bp/side spread the book is already being charged is a factor of ~300.
Any runner that charges a realistic round-trip cost at each rebalance has already paid for the bias
several hundred times over in NET. **What the bias contaminates is the GROSS number** — the very
number `CLAUDE.md` requires reported beside NET, and the number used to separate cost failure from
signal failure.

**Where it would bite hard, and does not here:** a daily-re-equalised book on an *unfloored*
microcap universe. That is the `+6.79 %/yr` cell and the `+6.04 %/yr` published figure. **A $5 floor
plus a dollar-volume screen is precisely the correct fix, and it is already in place.**

---

## 1. THE MECHANISM AND THE FORMULA

### 1a. I DID NOT OBTAIN BLUME & STAMBAUGH (1983). Stated plainly.

**The documented failure reproduced exactly.** `urllib` GET of
`http://www-2.rotman.utoronto.ca/~kan/3032/pdf/BiasInReturns/Blume_Stambaugh_JFE_1983.pdf` returned
**HTTP 200, `Content-Type: text/html`, 1,651 bytes, magic `<!DOCTYPE html P`, `<title>404Handler</title>`**,
a client-side redirect to `apps.rotman.utoronto.ca/404handler/`. sha1 `a3daff1d9927`. **This is the
same five-way failure the prompt warned about, on this exact paper, and the byte inspection is what
caught it.**

The Wayback CDX API reports exactly one capture of that URL (20260810190930), `text/html`, 1,368
bytes — **the same 404 page, archived**. OpenAlex (`doi:10.1016/0304-405X(83)90056-9`):
`is_oa: false`, `oa_status: "closed"`, `any_repository_has_fulltext: false`, `oa_url: null`.
Semantic Scholar Graph API: `openAccessPdf.status: "CLOSED"`. No institutional access available.

**So every formula below is read from a source I did open, and I say which.** I state the
Blume–Stambaugh closed form only because I **derived and enumerated it myself** (§1c) — not because
I read it in their paper.

### 1b. The generalised Blume–Stambaugh result, READ FROM SOURCE

Asparouhova, Bessembinder & Kalcheva, *Noisy Prices and Inference Regarding Returns*, March 2011
working paper, `home.business.utah.edu/finea/HankIva2.pdf`, 59 pp., sha1 `e67bf849480c`
— **[WORKING PAPER, published version: Journal of Finance 68(2), 2013] [read in full: pp. 1–31, incl. all four propositions]**.

Observed price `P⁰ₙₜ = Pₙₜ(1 + δₙₜ)`, where `Pₙₜ` is the "true" price and `δₙₜ` is noise. Their
equation (1), *verbatim from the PDF*:

> `E(R⁰ₙₜ) ≅ E(Rₙₜ)(1 + σ²ₙ(1 − ρₙ))`
>
> "where `σ²ₙ` and `ρₙ` are the variance and first order autocorrelation of `δₙₜ` respectively. As in
> Blume and Stambaugh (1983) the differential between the mean observed and true returns increases
> with `σ²ₙ`. The differential declines with `ρₙ`, but remains strictly positive as long as `ρₙ < 1`,
> i.e. as long as the noise component of prices is indeed temporary."

They label this "a generalized version of the Blume and Stambaugh (1983) result," derived in their
Appendix; Blume–Stambaugh's own version assumes `ρₙ = 0`.

**The bias depends on exactly two things: the VARIANCE of the price noise, and its PERSISTENCE.** It
does not depend on volatility of true returns, on the number of names, or on the strategy.

**And the portfolio result, their Proposition 1** (`σ²ₙ` independent of characteristics,
`Cov(Rₙₜ, Rₙₜ₋₁) = 0`, `ρₙ = ρ`), *verbatim*:

> `plim μ_EW ≈ μ + μσ²(1 − ρ)`

**This is the analytic reason NAME COUNT DOES NOT ATTENUATE IT.** The equal-weighted portfolio bias
is the cross-sectional *average* of the individual biases — a mean, not a variance — so `N` does not
appear. `J3`'s prior finding that name count does not attenuate the effect is not an empirical
curiosity; it is what the closed form says must happen. **The programme's "effective breadth ~10
independent instruments" is irrelevant to this bias for the same reason.**

ABK's own framing of this, p. 3: noise makes "cross-sectional mean returns to equal-weighted (EW)
portfolios … upward biased by the cross-sectional average of the individual security biases."

### 1c. The bid-ask-bounce closed form — DERIVED AND VERIFIED HERE, not read from the source

The widely quoted Blume–Stambaugh special case is
**`E(R_observed) = s² / (4 − s²)`**, with `s = (A − B) / [(A + B)/2]` the relative spread.

**I found this stated only on a summariser** — a personal teaching page
(`sites.google.com/site/davesmant/...`, **[UNVERIFIED] [snippet only]**) — so per the summariser
rule I did not take it. I derived it instead. Setup: true price = midpoint, constant; observed price
is ask `A = 1 + s/2` or bid `B = 1 − s/2`, fair coin, iid across periods. Four equally likely paths:

`E[R⁰] = ¼ (A/A + A/B + B/A + B/B − 4) = ¼ (A/B + B/A − 2) = (A−B)² / (4AB) = s² / (4 − s²)`

Exhaustive enumeration ([`data/k5_rebalancing_bias_calc.py`](../../data/k5_rebalancing_bias_calc.py))
agrees to 8 decimal places at `s` = 10 %, 6.76 %, 3.23 %, 1 %.

**Two things fall out, and both are load-bearing:**

1. **It reconciles with ABK equation (1).** Here `δ = ±s/2` so `σ²_δ = s²/4`, and
   `s²/(4−s²) = (s²/4) · 1/(1 − s²/4) ≈ σ²` for small `s`. At `s = 67.6 bp` the exact value is
   `0.00114375` and `σ² = s²/4 = 0.00114244` — agreement to four significant figures. **Two
   independently obtained expressions, one read from a peer-reviewed source and one derived, give
   the same number.**
2. **The summariser's worked example is WRONG.** It states that "for a 10% bid-ask spread, the period
   return bias equals 0.3%". The formula it itself quotes gives `0.01/3.99 = 0.2506 %`. It is off by
   ~20 % — a rounding-up of its own algebra. **Flagged: the formula on that page is right, its number
   is not.** This is the third summariser arithmetic error this programme has logged.

### 1d. THE MECHANISM IS NOT WHAT THE SHORTHAND "CROSS-SECTIONAL VARIANCE" SUGGESTS

**There are TWO distinct effects, from two different papers in the same 1983 JFE issue, and they
pull in OPPOSITE directions.** The prompt's framing ("relates it to the cross-sectional variance of
returns *and* to bid-ask bounce") conflates them, and the conflation matters.

- **Blume & Stambaugh (1983) — the NOISE effect.** Driven by the variance of the price noise
  (`σ²`), positive, and the dominant term empirically. This is the bid-ask-bounce channel.
- **Roll (1983) — the CONVEXITY effect.** Present in a frictionless market with temporally
  independent returns, driven by the cross-sectional variance of *mean* returns. **This one makes
  buy-and-hold EXCEED the rebalanced portfolio**, i.e. it *reduces* the measured
  (rebalanced − buy-and-hold) gap.

**I could not obtain Roll (1983) either** (§"could not verify" #2). I derived the convexity direction
myself: under temporal independence,
`E[buy-and-hold] = (1/N) Σᵢ (1+μᵢ)^T` and `E[daily-rebalanced] = (1+μ̄)^T`, and by convexity of
`x ↦ (1+x)^T` the former is `≥` the latter, with the gap increasing in the cross-sectional variance
of `μᵢ`. **My derivation is corroborated by the source that cites Roll**: Canina et al. found the
cross-sectional-variance coefficient *positive* in their regression and wrote, *verbatim*, "It
should be noted that the sign of this coefficient is the opposite of what the theory indicates
(Roll (1983))." **That sentence only makes sense if Roll's theory predicts a negative coefficient,
which is what my derivation gives.** Recorded as a consistent reading, not as Roll read.

**Practical upshot for this programme:** do not expect high cross-sectional return dispersion to
inflate the bias. The channel to worry about is **noise variance**, and therefore **spread and
price level**.

---

## 2. WHAT DRIVES THE MAGNITUDE — AND WHICH UNIVERSE EACH NUMBER IS ON

**Every magnitude below is tagged with its universe, because they are not comparable and the
differences between them are the whole point.**

### 2a. The daily-vs-monthly figure — Canina, Michaely, Thaler & Womack (1998)

*Caveat Compounder: A Warning about Using the Daily CRSP Equal-Weighted Index to Compute Long-Run
Excess Returns*, Journal of Finance 53(1), 403–416. Read from the Cornell eCommons author manuscript,
`ecommons.cornell.edu/server/api/core/bitstreams/a1f43e07-…/content`, 22 pp., sha1 `762215be8d75`
— **[PEER-REVIEWED] [read in full]**.

**Universe: the CRSP equal-weighted index, 1964–1993, 360 months. ALL NYSE + AMEX + NASDAQ common
stocks. NO price floor. NO liquidity screen. The 1/8-tick era.** This is the single most important
caveat on the number, and it is the number everyone quotes.

- Average difference (daily-compounded minus monthly EW) = **0.427 %/month**, and **6.04 %/yr**
  measured as `1.017941¹² − 1.012924¹²`. The paper flags Jensen's inequality explicitly: the
  compounded monthly difference `1.04269¹² − 1` is **5.25 %/yr**, not 6.04 %, and the two are not
  the same quantity.
- **ONE-SIDED.** "the difference is only negative in 3 of the 360 months" → **99.2 % of months
  positive** for the EW index. *(For the VW index, 167 of 360 months — 46.4 % — are negative, i.e.
  essentially symmetric, which is the control.)* **Note the conflict with `J3`: `J3` measured ~92 %
  of months positive; Canina measured 99.2 %. I would weight `J3`'s figure for this programme** —
  it is on 2010–2026 with a floor, where the bias is an order of magnitude smaller and therefore
  much more often swamped by noise. Both recorded.
- Seasonality: largest month is **December at 0.66 %**; largest single month **+2.63 % in July 1992**;
  and surprisingly **only one January** appears in the top-20 list.
- Attribution: **about half** the month-to-month variation is explained by the theory's variables
  (`R²` ≈ 0.21 on autocorrelations alone, **0.47** using variance-of-excess-return-to-price as a
  direct bid-ask proxy, **~0.50** with both). Turnover's coefficient is negative as predicted but
  **insignificant**; dividends insignificant.
- **Two signs come out BACKWARDS versus theory, and the paper says so.** The cross-sectional
  variance coefficient is positive, "the opposite of what the theory indicates (Roll (1983))"; and
  the portfolio variation-of-excess-return-to-price coefficient is positive, "the opposite of what
  we expected (see Blume and Stambaugh (1983))." **Recorded as a live conflict in the literature, not
  adjudicated.**

### 2b. NAME COUNT DOES NOT ATTENUATE IT — the primary source for `J3`'s figure, found

**`J3`'s "7.12 % at 100 names against 7.18 % at 900" is Canina et al. (1998) §II, p. 11, and I read
it in the source.** It is a Monte Carlo, not a simulation from a later paper. Verbatim numbers,
annualised, random CRSP draws per month over 1964–93, 360 runs per size group:

| names | 10 | 100 | 300 | 600 | 900 |
|---|--:|--:|--:|--:|--:|
| annual difference | 6.51 % | **7.12 %** | 7.23 % | 7.19 % | **7.18 %** |

Their conclusion, verbatim: "(1) a significant bias exists even for a portfolio of ten stocks, and
(2) the bias has the same magnitude for all the portfolios we check." **`J3`'s figure is confirmed
against its primary source, and §1b now supplies the closed form that explains why.**

Note also their parenthetical, which is the one that reaches this programme: "using daily returns to
calculate a portfolio long-run return will result in a bias even if this portfolio is not being used
as the benchmark portfolio. Thus this problem will affect event studies that compute daily returns
on any equally-weighted portfolios in event time, regardless of the benchmark."

### 2c. THE PRICE-LEVEL EVIDENCE — and the floor is quadratic, not linear

Fisher, Weaver & Webb, *Removing Biases in Computed Returns: An Analysis of Bias in Equally-Weighted
Return Indexes of REITs*, International Real Estate Review 15(1), 2012, 43–71,
`gssinst.org/irer/wp-content/uploads/2020/10/v15n1-removing-biases-in-computed-returns.pdf`,
30 pp., sha1 `d8e2ca4fdb4d` — **[PEER-REVIEWED] [read in full]**.

**Universe: CRSP monthly equal-weighted indexes, Feb 1973 – Dec 2006, monthly rebalancing.**

- **US non-REIT stocks: average bias 12.67 bp/month.** US REITs: **9.38 bp/month**. Traditional REIT
  index **"almost 50 % larger than an unbiased index by the year 2006."**
- **Bias declines over the sample, and they name the two reasons: migration to NYSE, and — verbatim
  — "many fewer REIT stocks have low prices of under $10.00 per share."** This is the cleanest
  published statement that the driver is the **price level**, not size.
- **"spreads are a major determinant of bias"** — verbatim.
- **The closest thing to a natural experiment in this literature.** German REITs show significant
  bias; **Australian REITs show NONE**, and the stated cause is that "Australian closing prices are
  determined via a closing auction which effectively eliminates the bid-ask spread for closing
  prices. Since … spreads are a major determinant of bias, eliminating the spread eliminates most of
  the bias." **Remove the closing spread, the bias vanishes. That is as close to causal identification
  as this literature gets, and it confirms bid-ask bounce as the mechanism.**

**The floor's leverage is QUADRATIC, and this is sharper than the programme's existing note.**
`FINDINGS`-side reasoning records that "cost in bp scales inversely with price." The *bias* scales
as the **square** of that: for a roughly fixed absolute spread, `s ∝ 1/P`, and
`bias ≈ s²/4 ∝ 1/P²`. Doubling the floor quarters the bias. (My derivation from the verified closed
form; labelled as such.)

**Sanity check against `J3`:** `6.79 / 0.30 = 22.6×`, and `√22.6 = 4.75×` in implied spread;
`161.4 / 34.5 = 4.68×`. **The factor-of-eleven-to-twenty-three across the floor is the square of a
~4.7× spread ratio.** Consistent.

### 2d. THE BIAS IN A STRATEGY'S MEASURED PERFORMANCE — the part that is less written about

ABK (§1b, read in full), **universe: CRSP monthly, 1966–2009, all common stocks.** Their Table II
reports decile-sort hedge portfolio returns under `EW` (uncorrected) and `RW` (corrected). The
`EW − RW` differential is their estimate of the bias **in the long-short spread**:

| sort variable | `EW` hedge return | `EW − RW` bias | bias as share of premium |
|---|--:|--:|--:|
| firm size | −1.425 %/mo (t=4.43) | **−0.46 %/mo** (t=−13.52) | **~one third** |
| share price (low−high) | +1.252 %/mo (t=3.27) | **+0.61 %/mo** (t=15.04) | **~one half** |
| illiquidity | +1.139 %/mo (t=3.95) | **+0.36 %/mo** (t=12.77) | ~one third |
| trading volume | −1.198 %/mo (t=−4.52) | **−0.35 %/mo** | ~one third |
| book-to-market | +1.369 %/mo (t=6.03) | **+0.09 %/mo** (t=2.21) | **small** |

**Two findings here are directly decision-relevant and neither is about index construction:**

1. **The bias in a LONG-SHORT book is the DIFFERENCE of the two legs' noise variances, not a level.**
   Book-to-market sorts carry almost none (0.09 %/mo) because both legs have similar noise. Price,
   illiquidity and volume sorts carry a lot because the sort *is* a sort on noise. **So the question
   for any cell here is not "is the book equal-weighted" but "does the selector covary with spread?"**
   ABK: "The biases are particularly likely to be significant for explanatory variables that are
   cross-sectionally correlated with the variance of the noise in prices."
2. **The share-price premium does not survive correction at all.** Verbatim: "none of the
   bias-adjusted estimates support the existence of a return premium associated with share price, as
   the bias-corrected hedge portfolio t-statistics range from 0.40 (VW) to 1.74 (RW)." An apparent
   `t = 3.27` became `t ≤ 1.74`. **A published anomaly killed entirely by this artefact** — and it is
   the anomaly on the axis (price) that this programme screens on.

**And ABK's conceptual statement, which I think is the most important sentence in this brief** (p. 10,
verbatim): "an equal-weighted cross-sectional mean of observed returns should be interpreted as the
hypothetical outcome to a subset of investors who successfully execute a specific active trading
strategy, and not as the rate of growth in aggregate shareholder value." And on Hsu (2006), who
argued equal-weight rebalancing *raises* returns: "He specifically assumes that investors are able
to execute their trades at observed prices; in particular his computations pertain to an investor
who is able to sell at prices that have increased … and vice versa. The strategy improves returns if
the price changes that precipitated the trades are reversed on average, i.e., if prices contain
noise. To the extent that the noise in prices reflects liquidity demand on the part of impatient
traders, the posited rebalancing strategy is one of liquidity provision."

**Read that as a statement about backtests and it says: the daily-re-equalisation bias IS a
liquidity-provision return, harvested for free.** It is exactly the part of the return you cannot
keep once you pay the spread you crossed to get it. **Which is why it belongs in the GROSS column
and is already paid for in NET** — and why, at 0.114 bp per rebalance against 33.8 bp/side, it is
second-order here.

### 2e. A calibration conflict, recorded

ABK calibrate `σ = 0.06` per month from Brennan & Wang (2010, Table 2), all CRSP common stocks.
Proposition 1 then gives an EW monthly bias of `μσ²(1−ρ)` ≈ **36.4 bp/month** at `ρ = 0`
(→ 4.45 %/yr at monthly rebalancing), falling to 18.2 bp/month at `ρ = 0.5`.
**FWW measure 12.67 bp/month directly on the same kind of object.** These differ by ~3×.

I have not reconciled them and do not adjudicate. **I would weight FWW's 12.67 bp** for a
magnitude, because it is a direct measurement of the thing rather than a plug of a third party's
noise parameter into an approximation, and because the ABK figure inherits Brennan–Wang's `σ` which
ABK themselves say they deliberately made conservative in one direction and unskewed in another.
**I would weight ABK's Propositions for the structure**, which is what §5 uses them for.

---

## 3. THE CORRECTION — FOUR OPTIONS, AND EACH HAS ITS OWN BIAS

### 3a. What the literature recommends

**Canina et al. §III, in their own order of preference (read in full):**

1. Use the **value-weighted** index. "This portfolio does not suffer from any compounding related
   bias." *Cost: it is no longer equal-weighted, so it answers a different question.*
2. Use the **monthly** EW index rather than the daily. "Using the monthly instead of the daily
   equal-weighted index … results in a much smaller bias. In fact, the difference between a yearly
   buy-and-hold strategy and a monthly rebalancing strategy is very small (see Roll (1983))."
   *Requires splicing daily and monthly tapes at the period edges.*
3. **Buy-and-hold: "Clearly, the third alternative is the best: It produces an exact buy-and-hold
   portfolio that is clear of any biases."** Computed from the portfolio's index *level* at the two
   endpoints with dividends reinvested.

Note footnote 8, which is the honest caveat and the one that matters for a real book: "This argument
abstracts from the issue of the cost of transacting. However, we do not try to advocate an actual
monthly rebalancing of a portfolio, but the extent of the bias in its approximation of a true
buy-and-hold strategy." **The fix is a MEASUREMENT change, not a trading change.**

### 3b. The bias-corrected estimators, and their own biases

ABK assess four corrections **(read in full; Propositions 1–4)**. Every one of them is a weighted
average whose weight is proportional to the **time `t−1` observed price** — that is the whole trick:
"if the `t−1` observed price contains positive noise then the weight is increased and the time `t`
return is decreased, on average."

| method | what it is | its own bias |
|---|---|---|
| `EW` (uncorrected) | equal weights every period | `+μσ²(1−ρ)`. Unaffected by commonality in noise. |
| `IEW` (Blume–Stambaugh buy-and-hold) | equal at formation, then let weights drift | **zero after the first period if `ρ=0`**; the first period is uncorrected |
| `RW` (ABK return-weighting) | weight by prior gross return | `μσ²(1−ρ)ρ/(1+σ²(1−ρ))` — **consistent iff `ρ=0`**, upward biased if `ρ>0` |
| `VW` | weight by prior market cap | consistent under their assumptions; but shifts the estimand toward large caps |
| `AVW` | prior-December market cap | "not effective in reducing bias in months other than the first month after portfolio formation" |

**Three trade-offs worth carrying:**

- **No correction is consistent when noise has a COMMON component.** Proposition 3: with
  cross-sectional commonality `c > 0`, `EW`'s bias is unchanged but *every* correction acquires one,
  and they converge to the uncorrected estimate as `c → 1`. "Blume and Stambaugh (1983) observed
  that their proposed correction is effective due to diversification of noise. The result here
  confirms this intuition." **Corrections work by diversifying noise across names; a market-wide
  noise component defeats them. On a panel with ~10 effective independent instruments, that caveat
  is not academic.**
- **But every correction is still strictly better than none.** Verbatim: "for any range of
  parameters considered, estimates corrected by any of the methods considered are strictly less
  biased than uncorrected (equal-weighted or OLS) estimates."
- **`VW` vs `RW` is a choice of estimand, not of accuracy.** ABK: "the analysis provides little
  reason to prefer `VW` over `RW`, or vice versa" for bias removal — but `VW` also reweights toward
  large firms, while `RW` "provides corrected estimates that place equal weight on each security."
  **If the programme wants the true *equal-weighted* mean, `RW` is the correction; `VW` answers a
  different question.** And `RW` is cheap: it is a weighted mean with the prior bar's gross return
  as the weight.

### 3c. A fourth correction, and a fifth option

**Fisher–Weaver–Webb's estimator, read from the IRER paper (eq. 1–3).** Divide a two-period average
portfolio price relative ending at `t` by the one-period average ending at `t−1`:

`1 + E(R̂ₜ) = (1 + E(²R̂ₜ)) / (1 + E(R̂ₜ₋₁))`

Their claimed advantages over Blume–Stambaugh: it **allows frequent rebalancing** (buy-and-hold does
not) and it removes bias from "any random transient errors (not limited to bid-ask bounce as in
previous studies)". Assumptions: transient errors in successive observed prices independent, and all
observed prices finite and positive. **Same Achilles heel as ABK's corrections: independence of
successive errors.**

**Fifth option — log returns.** ABK footnote 2: "Notably, there would be no upward bias in the
average log return." But they immediately cite Ferson & Korajczyk (1995) for "several reasons that it
may not be appropriate to use continuously compounded returns when testing discrete-time asset
pricing models," and FWW footnote 7 cites Bessembinder & Kalcheva (2007) that log-return estimates
"contain no bias" but "possess certain properties that limit their usefulness in many tests."
**[both snippet only — I did not read Ferson–Korajczyk or Bessembinder–Kalcheva.]**

### 3d. What I would actually recommend here, and it is cheap

**Report both lenses, which this programme's own rules already demand.** The correction that costs
least and is most legible is **`RW`: one extra weighted mean, weight = prior bar's gross return**,
reported beside the plain `EW` number. The `EW − RW` gap *is* the bias estimate, with a `t`-statistic,
exactly as ABK's Table II does it. **That turns an unknown into a measured quantity, per cell, for
roughly the cost of one extra array multiply — and it is a within-study comparison, so it does not
need a new null.**

---

## 4. THE ADJACENT PHENOMENA, BRIEFLY

**(a) Bid-ask bounce, measured returns, and autocorrelation.** Bounce induces **negative**
first-order autocorrelation in an *individual* stock's returns and **upward** bias in its mean.
Non-synchronous trading induces **positive** autocorrelation in a *portfolio's* returns. Canina's
regression separates them: mean individual autocorrelation **−6.255 %**, mean portfolio
autocorrelation **+20.22 %**, with coefficients **−0.032** and **+0.0035** — so "the securities'
autocorrelation has an effect that is more than two-and-one-half times larger than the portfolio
autocorrelation effect… the bid-ask bounce has a larger effect on the difference than non-synchronous
trading." **Individual-stock bounce, not non-synchronous trading, is the dominant channel.**

A caution from ABK on attribution: bid-ask spreads are only one source of price noise. Their list,
with "arguably most important" attached to the last: "bid-ask spreads, nonsynchronous trading, a
discrete price grid, and arguably most important, the accumulated price impacts of order imbalances."
They cite Hendershott, Li, Menkveld & Seasholes (2011) for "a quarter of the variance in monthly
returns to NYSE stocks is due to transitory price changes" **[snippet only via ABK]**. **So a
Corwin–Schultz spread estimate is a LOWER bound on `σ`, and the bias computed from it is a lower
bound on the bias.** That cuts against the reassuring arithmetic in my headline and should be carried
with it.

**(b) Equal-weighted INDEX versus equal-weighted PORTFOLIO compounded daily.** Canina's footnote 2
settles this, verbatim: "We can consider the comparison between the daily and monthly indices to be
the same as the comparison of the one-month buy-and-hold strategy (the monthly index) to a daily
rebalancing (the daily index)." **An "equal-weighted index" is only defined once you state its
rebalancing schedule, and the schedule is the bias parameter.** CRSP's daily EW index is a
daily-rebalanced portfolio; its monthly EW index is a monthly-rebalanced one; they differ by
0.427 %/month on 1964–93 data. **Two series with the same name and a 6 %/yr gap.**

**(c) Bias in a RETURN SERIES vs bias in a STRATEGY's measured performance.** This is §2d, and it is
the right framing for this lane. The published literature is overwhelmingly about benchmark series.
The strategy question has exactly one strong published answer I could identify: **Conrad & Kaul
(1993)**, whose contrarian-strategy profits were "largely explained by biases attributable to noisy
prices" and who found "the remaining 'true' returns to loser or winner firms have no relation to
overreaction" **[PEER-REVIEWED, Journal of Finance 48(1), 39–63] [abstract only — see §"could not
verify" #3; characterised from ABK and FWW, both of whom cite it as implementing the same
buy-and-hold correction with a three-year rebalance]**.

**The asymmetry that matters: Conrad & Kaul's was a selector keyed on past returns.** A selector
keyed on past returns selects on the noise itself — buys names whose observed price sits at the bid
— and therefore the entry price is *systematically* on the wrong side of the midpoint. **That version
of the bias does NOT shrink with holding period and is NOT fixed by holding longer.** It is a
selection effect, not a rebalancing effect. §5b.

**(d) The diversification/rebalancing return is a DIFFERENT thing.** Real periodic rebalancing of a
real portfolio has a genuine convexity effect (Hsu 2006 and the "diversification return" literature).
ABK's reply is the distinction to hold onto: "Gains and losses from active trading are zero-sum
across all agents in the economy… noise in prices does not increase the rate of growth in expected
prices or in the expected wealth of traders in aggregate." **One is a measurement artefact; the other
is a real return that someone on the other side pays. They are easy to conflate and the literature
does conflate them.** *(Position sizing and weighting-scheme choice are on the exclusion list; I note
this only to keep the boundary clean.)*

**(e) One low-weighted corroborating item, flagged.** A working paper retrieved at
`datayyy.com/doc_pdf/paper74.pdf` ("On the Consistency Between the Fama-French Daily and Monthly
Factors", May 2011, 30 pp., sha1 `84ade8f1997a` — **[WORKING PAPER] [read in full] [UNVERIFIED
provenance: no author name on the title page of the copy I hold, no journal, hosted on a personal
file directory]**) reports that compounding the **daily** SMB factor **understates** the size effect
by ~49.7 % over 1964–93, about **−2.51 %/yr**, and that daily UMD understates momentum by 201 %. It
also documents a **"switching effect"** where the sign of the bias reverses between adjacent 4-year
windows (HML: +3.9 % then −0.9 %). **I weight this low and do not rely on it.** But the direction is
worth one line: **it is NEGATIVE, the opposite of the EW-index case**, which is consistent with FF
factors being built from *value-weighted* sub-portfolios, so the noise channel is small and a pure
long-short compounding artefact dominates. **If any cell here reports a compounded CAGR of a
long-short spread series, the sign of its compounding artefact is not guaranteed positive.**

---

## 5. THE DECIDING QUESTION: DOES A MULTI-BAR-HOLD BOOK CARRY IT?

### 5a. THE ANSWER, FROM THE SOURCE

**The bias is paid ONCE PER REBALANCE, not once per bar.** The mechanism is a noisy *denominator*:
`E[P⁰ₜ / P⁰ₜ₋₁]` is biased because `P⁰ₜ₋₁` is noisy and sits in the denominator. Over a hold of `H`
bars there is **one** entry denominator, not `H` of them.

FWW state the mechanism in exactly those words (read in full): **"The average bias inherent in
observed returns is due to pricing errors at the beginning of the holding period. By invoking the law
of large numbers, the expected bias in observed prices at time `t` is zero, leaving only the bias in
observed prices at the beginning of the period."**

**ABK make it quantitative, and this is the passage that settles the lane** (read in full, §III.A.2):

> "Note that `RW(s)` coincides with `IEW` when the relation between `s` and `t` (the number of
> periods since `IEW` portfolio formation) is `t − s = 1`. Thus, the `IEW` method equates to `RW(1)`
> in `t = 2`, to `RW(2)` in `t = 3`, etc. In their empirical analysis Blume and Stambaugh compute
> weighted returns up to time `t = 12`, when the portfolio is once again rebalanced to equal weights.
> Estimates are averaged across months, and therefore are equivalent to the average across `RW(0)`
> to `RW(11)`."

Combine with Proposition 1: `plim μ_RW(s) ≈ μ + μ σ²(1−ρ)ρˢ / (1 + σ²(1−ρˢ))`.

**Set `ρ = 0` (serially independent noise — Blume–Stambaugh's own assumption). Then `ρˢ = 0` for all
`s ≥ 1`, so the `RW(s)` bias is EXACTLY ZERO for every `s ≥ 1`, and equals the full `EW` bias only at
`s = 0`.** A hold of `H` bars averages `RW(0) … RW(H−1)`: one biased term, `H−1` unbiased ones.

> **Bias per bar for an `H`-bar hold ≈ (1/H) · σ²(1−ρ), against σ²(1−ρ) for a book that re-equalises
> every bar.**

ABK's own note on the residual: the `IEW` method "assigns equal weights to each security in the first
period after the portfolio is formed (`t = 1`), implying the absence of any correction for the
effects of noise in the first period." **The first bar of every hold carries the full bias. Bars 2
through `H` carry none.**

**Stated plainly, as the bar requires:**

- **The LARGE version is carried by a book that re-sets every position to equal weight EVERY BAR** —
  i.e. one that recomputes `weight = 1/N` from that bar's observed close for names it already holds.
  This is what the CRSP *daily* EW index is, and it is what `+6.04 %/yr` and `+6.79 %/yr` measure.
- **The SMALL version — roughly `1/H` of it — is carried by a book that buys at entry, holds, and
  only touches weights on entry and exit.** With holds of tens of bars the bias is
  `~0.007–0.03 %/yr` at this programme's measured spread. **That is not a number that changes any
  conclusion.**
- **I cannot tell which this programme's books are**, and will not guess. **The check is one grep:
  does the weight array get recomputed from the current bar's close for names already held, or only
  at entry?** If weights are set at entry and then left alone (or carried as share counts rather than
  dollar weights), the large version is absent by construction. **If `sel = rank < N_SLOTS` drives a
  fresh `1/N_SLOTS` dollar weight each bar, it is present.**

### 5b. TWO WAYS IT STILL BITES A MULTI-BAR BOOK — and these do not shrink with `H`

**Honest caveats, because `1/H` is not "zero".**

1. **A selector that covaries with the spread.** §2d: the bias in a long-short or ranked book is the
   *difference* in noise variance between what is held and what is not. ABK found it to be **one
   third** of the size premium, **one half** of the share-price premium, and **enough to kill the
   share-price premium entirely**. **Any cell here that ranks on a price-based quantity — past
   return, reversal, price level, dollar volume, illiquidity — is selecting on `σ²` and carries a
   bias that is a property of the SELECTOR, not of the rebalancing schedule.** Lengthening the hold
   does not touch it. This is the Conrad & Kaul (1993) failure mode.
2. **Non-zero noise persistence.** Everything above with `ρ = 0` is the best case. ABK's whole point
   in relaxing Blume–Stambaugh is that `ρ > 0` is realistic (they cite Brennan–Wang 2010 and
   Hendershott et al. 2011), in which case `RW(s)` bias `∝ ρˢ` decays geometrically rather than
   vanishing at `s = 1`. The `1/H` is then an under-statement — though ABK also report that "for
   moderate violations of the independence assumption … the remaining bias in the corrected estimates
   is minimal."

**Neither caveat is reached by a rebalancing-schedule change. Both are reached by the `EW − RW`
diagnostic in §3d.**

---

## 6. THE OPEN QUESTION: DAILY AUTOCORRELATION OF AN EQUAL-WEIGHTED US EQUITY PORTFOLIO

**I found a modern, directly-measured, peer-reviewed set of figures. It is not a single full-sample
CRSP-EW-index number, but it is better than one for this purpose, and it adds to both prior
readings without adjudicating between them.**

### 6a. First, the 20.22 % figure's provenance is now CONFIRMED from its source

**It is Canina, Michaely, Thaler & Womack (1998), §II, and I read the sentence: "The mean portfolio
autocorrelation is 20.22 percent, and the mean securities' autocorrelation is −6.255 percent."**

**The earlier round's reading of its construction is correct, and footnote 5 of the paper is the
confirmation, verbatim:** "As there are 21 trading days in most months, we use 20 observations to
compute the first-order autocorrelation, 19 to compute the second, and 18 to compute the third
(missing observations are excluded)." Each stock's and the portfolio's autocorrelation is estimated
**within a single month from ~20 daily observations**, then averaged over the 360 months of
1964–1993. **So: a mean of 360 twenty-observation within-month estimates, on CRSP all-exchange
1964–93 with no price floor.** The reading on the record is verified. I add to it; I do not choose
between the two readings.

### 6b. The modern figure

Anderson, Eom, Hahn & Park, *Sources of stock return autocorrelation*, version dated 22 April 2012,
`eml.berkeley.edu/~anderson/Sources-042212.pdf`, 63 pp., sha1 `7847d79dff76`
— **[WORKING PAPER; published as "Autocorrelation and partial price adjustment", Journal of
Empirical Finance 24 (2013) 78–93] [read in full: abstract, §2 literature, §3 method, §4 data, §5.2
results, Table 8 Panels A–C]**.

**Universe, read from their §4 and notably close to this programme's:** NYSE-listed common stocks,
trades from TAQ, **1993–2008**, eight two-year subperiods. Excludes closed-end funds, trusts, ETFs,
names with no trade for 30+ consecutive days, the fifty smallest by market cap, **and any name whose
prior-day CRSP close was below $2**. **1,000 firms** selected to spread evenly across the whole
market-cap range, split into **ten groups of 100**, each group formed into an **equally-weighted
portfolio**. Portfolio daily return = equal-weighted average of constituents' daily returns.

**Table 8, Panel A (Pearson), first-order autocorrelation of daily equal-weighted portfolio
returns.** Standard error 0.045 per two-year subperiod, **0.016 for 1993–2008, 0.022 for each half**.

| portfolio | 93–94 | 95–96 | 97–98 | 99–00 | 01–02 | 03–04 | 05–06 | 07–08 | **93–08** | **93–00** | **01–08** |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| Smallest | .221** | .136** | .300** | .231** | .144** | .051 | .059 | −.102* | .008 | .233** | −.034 |
| 2 | .240** | .142** | .286** | .211** | −.003 | .026 | .009 | −.089* | −.006 | .232** | −.049* |
| 3 | .210** | .212** | .276** | .157** | −.035 | .001 | .019 | −.059 | .009 | .216** | −.037 |
| 4 | .258** | .174** | .287** | .092* | −.052 | −.027 | .006 | −.023 | .016 | .201** | −.025 |
| 5 | .264** | .192** | .211** | .151** | .028 | .044 | .073 | .006 | .060** | .194** | .023 |
| 6 | .258** | .192** | .201** | .085 | .046 | .025 | .083 | −.022 | .048** | .162** | .009 |
| 7 | .220** | .170** | .208** | .080 | .097* | .032 | .058 | −.016 | .053** | .158** | .020 |
| 8 | .217** | .158** | .141** | .111* | .058 | .006 | .024 | −.028 | .035* | .144** | −.001 |
| 9 | .139** | .146** | .054 | .112* | .085 | −.041 | −.003 | −.073 | .007 | .098** | −.026 |
| Largest | .025 | .115** | −.003 | .083 | .028 | −.068 | −.054 | −.082 | −.017 | .048* | −.047* |

*`**` 1 %, `*` 5 %, two-sided, as in the source. Panels B (Andrews HAC) and C (Kendall τ) are in the
paper and broadly agree; Kendall's 93–08 column is significant for most portfolios at 0.026–0.073.*

**What this says, and it is a substantial addition to the record:**

- **A modern full-sample figure exists: 1993–2008 daily first-order autocorrelation of an
  equal-weighted US equity portfolio is +0.01 to +0.06 (Pearson), against Canina's +0.2022 on
  1964–93.** An order of magnitude smaller.
- **In 2001–2008 it is indistinguishable from zero, and where significant it is NEGATIVE**
  (portfolio 2: −0.049*, largest: −0.047*). The paper's own summary: "in the second half of our data
  period, the null hypothesis is not rejected for any portfolio or any correlation test."
- **The decline is structural, not noise.** "there is a significant paradigm shift between 1993–2000
  and 2001–2008, and this shift affects both individual stock and portfolio return autocorrelation
  across all firm size groups in a consistent direction, from more positive autocorrelation towards
  more negative autocorrelation… most likely reflects either an increase in the popularity of
  momentum strategies, resulting in overshooting, or an increase in the volume of high-frequency
  trading, or a combination of the two."
- **It is monotone in size, in the direction the mechanism predicts:** "As the firm size becomes
  larger, the first-order autocorrelation of portfolio return becomes smaller."
- **And the attribution is NOT what the 1983 papers assumed.** This paper's whole contribution is
  that non-synchronous trading and bid-ask bounce ("spurious") are *not* the main drivers; **partial
  price adjustment ("genuine") is** — "PPA is the main source of portfolio return autocorrelation in
  all time subperiods and all size groups except the largest; even there, it falls just below 50 %."
  They also find the SPDR's own daily autocorrelation **negative and significant at the 0.1 % level
  for 1993–2008**, surviving a correction for the maximum possible bid-ask contribution.

**Caveats I will not bury:** NYSE only (no Nasdaq, where the bias is largest); $2 floor not $5;
1993–2008, so still ~18 years stale relative to 2010–2026; 100 names per portfolio, not 1,573; and
**I read the April 2012 working paper, not the published Journal of Empirical Finance version — the
tables may differ.** It also does **not** report the autocorrelation of a single market-wide
CRSP-style EW index, which is the object both prior readings were looking for.

**So the honest statement of the open question's status:** *a* modern full-sample figure for the
daily autocorrelation of an equal-weighted US equity portfolio is now on the record, and it is
**near zero for 2001–2008, with the 20 % figure confirmed as a 1964–93 artefact that the modern
period does not reproduce**. **A modern figure for the CRSP equal-weighted INDEX specifically — the
exact object of the two prior rounds — I still did not find, and I searched for it.** Both prior
readings stand; this is an addition.

**One note on relevance, against my own find:** ABK equation (1) says the bias depends on the
autocorrelation **of the NOISE (`ρ`)**, not on the autocorrelation of **returns**. Canina used
return autocorrelations as a proxy and got two signs backwards (§2a). **So the autocorrelation
figures above bound the mechanism's plausibility but do not plug into the bias formula.** Treat them
as context, not as an input.

---

## 7. SOURCE LEDGER

| source | type | how well established | file |
|---|---|---|---|
| Canina, Michaely, Thaler & Womack (1998), *Caveat Compounder*, JF 53(1) 403–416 | **[PEER-REVIEWED]** | **[read in full]** — author manuscript, Cornell eCommons, 22 pp., sha1 `762215be8d75` | `K5_canina1998_cornell.pdf` |
| Asparouhova, Bessembinder & Kalcheva, *Noisy Prices and Inference Regarding Returns*, Mar 2011 WP (pub. JF 68(2), 2013) | **[WORKING PAPER]** | **[read in full]** — 59 pp., sha1 `e67bf849480c` | `K5_abk_noisy_prices.pdf` |
| Fisher, Weaver & Webb (2012), IRER 15(1) 43–71 | **[PEER-REVIEWED]** | **[read in full]** — 30 pp., sha1 `d8e2ca4fdb4d` | `K5_fww_irer_reits.pdf` |
| Anderson, Eom, Hahn & Park, *Sources of stock return autocorrelation*, Apr 2012 WP (pub. J. Empirical Finance 24, 2013, 78–93) | **[WORKING PAPER]** | **[read in full: abstract, §2–§4, §5.2, Table 8]** — 63 pp., sha1 `7847d79dff76` | `K5_anderson_sources.pdf` |
| *On the Consistency Between the Fama-French Daily and Monthly Factors*, May 2011 | **[WORKING PAPER] [UNVERIFIED provenance — no author, no venue]** | **[read in full]** — 30 pp., sha1 `84ade8f1997a` | `K5_yan_ff_daily_monthly.pdf` |
| **Blume & Stambaugh (1983), JFE 12(3) 387–404** | **[PEER-REVIEWED]** | **NOT OBTAINED — see §1a** | the 1,651-byte 404 page served at HTTP 200 is kept as evidence: [`data/k5_rotman_blume_stambaugh_404_at_http200.html`](../../data/k5_rotman_blume_stambaugh_404_at_http200.html), sha1 `a3daff1d9927` |
| **Roll (1983), JFE 12(3) 371–386** | **[PEER-REVIEWED]** | **NOT OBTAINED** | — |
| **Conrad & Kaul (1993), JF 48(1) 39–63** | **[PEER-REVIEWED]** | **[abstract only]** | — |
| **Fisher, Weaver & Webb (2010), RQFA 35 137–161** | **[PEER-REVIEWED]** | **[abstract only]** — Springer paywall | — |
| `sites.google.com/site/davesmant/…` teaching notes | **[UNVERIFIED]** | **[snippet only]** — formula correct, worked number wrong by ~20 % (§1c). **Not relied upon.** | — |
| My own derivations and arithmetic | — | reproducible | [`data/k5_rebalancing_bias_calc.py`](../../data/k5_rebalancing_bias_calc.py) + [`…_output.txt`](../../data/k5_rebalancing_bias_calc_output.txt) |

**The five PDFs above are NOT copied into the repo** (they are third-party copyrighted articles). Each
row carries its retrieval URL and a sha1 of the exact bytes I read, so any claim here is re-checkable
by re-fetching and comparing the hash.

**Blocks and failures, logged by TOOL AND RESPONSE:**

- `urllib.request` GET, Rotman PDF → **HTTP 200, `text/html`, 1,651 bytes, `<title>404Handler</title>`**. Not a host block; a 404 served as 200.
- `web.archive.org` CDX API via `urllib` → **HTTP 200**, one capture, `text/html`, 1,368 bytes. The archive holds the 404 page.
- `archive.org/wayback/available` via `urllib` → **HTTP 429 Too Many Requests**.
- `api.fatcat.wiki` via `urllib` → **`URLError WinError 10060`, connection timeout**.
- `WebFetch` on `semanticscholar.org/paper/…` → returned **"I don't see any web page content provided"** — empty body passed to the summariser model. Worked around via the Semantic Scholar Graph API.
- `WebSearch` with `allowed_domains` including `web.archive.org` → **HTTP 400, "The following domains are not accessible to our user agent"**. A tool-level domain restriction, not a site block.
- Semantic Scholar Graph API and OpenAlex both returned valid JSON reporting **`CLOSED` / `is_oa: false`** for the Blume–Stambaugh DOI. Not a block — an accurate negative.

**Nothing in any fetched page addressed instructions to me, and I found no injected text to quote.**

---

## 8. WHAT I COULD NOT VERIFY, STATED PLAINLY

1. **Blume & Stambaugh (1983) itself. I never read one word of it.** Every statement attributed to it
   here is read from a paper that cites it (ABK, Canina et al., FWW), or derived by me. **The closed
   form `s²/(4−s²)` in §1c is MY derivation, enumerated and cross-checked against ABK's equation (1),
   and I do not claim it is the form the paper prints.** I also did not verify their headline ("bias
   accounts for approximately half of the observed small firm premium", 1963–80) against the paper —
   that is ABK's characterisation of it.
2. **Roll (1983) itself.** The cross-sectional-variance / convexity direction in §1d is **my
   derivation**, corroborated only by the *sign* implied by one sentence in Canina et al. I did not
   read Roll's formula, do not know its exact form, and could be wrong about what he assumed.
3. **Conrad & Kaul (1993).** Abstract only. The three-year rebalance and "contrarian profits largely
   explained by noise" come from ABK's and FWW's descriptions, not from the paper.
4. **Fisher, Weaver & Webb (2010).** Paywalled. I read only their 2012 IRER application. **So I could
   not resolve the programme's logged "52 % vs 97 %" conflict.** My best reading — unverified
   inference, not a finding — is that the two are **the same fact in two framings**: if the NASDAQ EW
   index ran 100 → 17,975 by 2006 and "nearly half of the increase" is bias, then the unbiased index
   is ≈ 9,000 and the traditional one is ≈ **97–99 % larger**. "Half the increase" and "97 % larger"
   would then both be correct and neither a fabrication. **I could not confirm this and it should not
   be recorded as resolved.** The 2012 paper's parallel REIT statement — "almost 50 % larger than an
   unbiased index" — is a *third* number on a *different* universe and must not be conflated with
   either.
5. **The ABK (36.4 bp/month implied) versus FWW (12.67 bp/month measured) gap, ~3×.** Recorded, not
   reconciled. §2e says which I would weight and why.
6. **Canina's 99.2 % of months positive versus `J3`'s ~92 %.** Recorded, not adjudicated. Different
   decades, different universes, different floors.
7. **No modern (post-2010) re-measurement of the EW daily-rebalancing bias magnitude exists that I
   could find.** Every published magnitude I obtained ends in 1993 (Canina), 2006 (FWW) or 2009
   (ABK). **`J3`'s 2010–2026 measurement may be the only one in existence on the modern period, and
   nothing I found contradicts it.** A confirmed absence.
8. **No modern figure for the CRSP equal-weighted INDEX's daily autocorrelation specifically.** §6b
   gives equal-weighted *portfolios* on NYSE, $2 floor, 1993–2008 — a close substitute, not the same
   object. The two prior rounds' readings both stand.
9. **Anderson et al.: I read the April 2012 working paper, not the published 2013 Journal of
   Empirical Finance version.** Table 8's numbers may have changed in revision. I did not obtain the
   published version.
10. **The Fama-French-consistency working paper's authorship and venue.** The copy I hold has no
    author on its title page and is hosted on a personal file directory. Tagged `[UNVERIFIED]`,
    weighted low, and none of this brief's conclusions rest on it.
11. **Whether THIS programme's books re-equalise every bar.** I have no access to the code and make
    no claim. **§5a names the one check that decides it, and the whole of §5's conclusion is
    conditional on that check.** My headline table is arithmetic on a published formula and two
    numbers the commission handed me — `33.8 bp/side` and the `+0.30 %` / `+6.79 %` figures — and is
    **not** a measurement of anything in this repository.
12. **The `σ` implied by a Corwin–Schultz spread estimate is a LOWER bound on total price noise.**
    ABK call accumulated order-imbalance price impact "arguably most important" among noise sources,
    and cite a quarter of monthly NYSE return variance as transitory. **So every magnitude I computed
    from the 33.8 bp spread is a lower bound, and the reassuring smallness in my headline is a
    lower-bound reassurance.** I did not read Hendershott et al. (2011) or Brennan & Wang (2010) and
    cannot quantify the gap.
