# J4 — Where should a price floor be set, now that the $5 convention's justification is dead?

External evidence only. I have no access to this programme's data, code or results and
claim nothing about any of them. Every number attributed to this programme below is one
that was handed to me in the commissioning brief, used as a parameter, and labelled as
such.

Scope guard: this lane asks **where the boundary should be**. The mid-hold eject-or-carry
question is settled ground (`working/leads4/H4-the-price-floor-convention.md`) and I do not
revisit it. Retail broker commission schedules, order types and execution quality are
excluded ground; I therefore parametrise the commission as `c` dollars per share
throughout and never quote a broker page.

---

## HEADLINE

**The lane clears its bar, and the answer is not a number. It is that the floor is the
wrong lever, and the literature says so in three independent places.**

Four findings, ordered by how much they should change what the programme does.

1. **Percentage spread is, to a first approximation, invariant to nominal price once size
   is held fixed — and this is measured precisely at the $5–$20 boundary.** O'Hara, Saar
   and Zhong (RAPS 2019) match NYSE common stocks priced $5–$10 and $10–$20 to
   same-industry, same-market-cap controls priced $20–$100. **Eleven of twelve tests on
   percentage quoted spread are insignificant, and the percentage effective half-spread
   differences are insignificant in both groups.** The SEC states the same mechanism in its
   own words in the Rule 612 adopting release: away from the tick constraint, a price
   change leaves "the cost of transacting in the stock, for a given dollar exposure …
   constant." **So raising the floor buys approximately nothing on the spread, which is the
   dominant cost term.** §5.

2. **What a price floor *does* buy, under a per-share commission, is exactly `20000c/P`
   basis points of round-trip commission, and that quantity is small and hyperbolically
   exhausted.** At `c = $0.005/share` the *entire* saving from raising the floor from $5 to
   infinity is **20 bp round trip**, of which **10 bp** is bought by the first step to $10
   and only 5 more by going on to $20. Against the 67.6 bp round-trip spread the brief
   supplies, the whole lever is worth under 30% of one cost component. **There is a closed
   form for the floor — `P_min = 20000c / (g − spread_rt)` — and its behaviour is the
   finding: it is not a constant, it explodes as the gross edge approaches the spread, and
   it is infinite when the spread alone eats the edge.** §4.

3. **On the one published measurement of a $5 screen's effect on *net* performance, the
   screen helps, and it helps by as much as excluding microcaps does.** Soebhag, Van Vliet
   and Verwijmeren (JBF 2024) make "exclude stocks priced below $5" one of eleven
   construction nodes across 2,048 factor variants: **gross Sharpe is essentially
   unaffected** (price filters are named among the choices that "do not lead to
   substantially different average Sharpe ratios"), while **net maximum Sharpe rises from
   0.12 to 0.18** — numerically identical to the microcap exclusion's 0.12 → 0.18. But
   their cost model is a per-*value* spread model with no per-share commission, so **the
   entire 0.06 comes through the spread channel**, which finding 1 says price does not
   control once size is held fixed. The most likely reconciliation is that their $5 screen
   is working as a **size/liquidity screen by proxy** — which a dollar-volume screen does
   more directly. §1, §2.

4. **Nobody derives a universe filter from a cost model. The closest published attempt
   reports that the filter is the least effective of three levers and that a
   mean-variance investor puts zero weight on it.** Novy-Marx and Velikov (RFS 2016)
   restrict the universe to the low-lagged-trading-cost tertile within each NYSE size
   decile — a cost-measured filter, the direct generalisation of a price floor — and write:
   "**Surprisingly this procedure does not significantly reduce the trading costs for any
   of the mid-turnover strategies.**" Their buy/hold spread (trading hysteresis) beats it
   on net return 0.51 vs 0.31 per month, and the ex-post tangency portfolio "**put[s] no
   weight on the momentum factors constructed in the low cost universe**". Korajczyk and
   Sadka (JF 2004) reach the same shape of conclusion by a different route: they fix the
   cost problem by **re-weighting**, not by filtering. §4.

**Direction, with its cost stated.** The evidence does not support raising the floor to
buy spread. It supports (a) computing `20000c/P` against the strategy's own gross edge per
round trip and setting the floor from that inequality rather than from convention, and
(b) if the real target is cost, **tightening the dollar-volume screen or adding a direct
spread screen instead**, because that is the variable the evidence says carries the cost.
The honest cost of either direction is in §6: the breadth loss is paid against at most
20 bp, and at an effective breadth of ~10 independent instruments (brief's figure) the
programme has less breadth to spend than the saving is worth.

**The one thing the literature does NOT supply, stated plainly: no published work varies a
price screen across multiple levels and reports the sensitivity.** Every sensitivity
result I found is binary — $5 versus none. The $1-vs-$5-vs-$10 comparison the lane asked
for does not exist in anything I could reach. §1.5, and item 1 of the final section.

---

## SOURCES, RANKED BY HOW MUCH THEY SETTLE

| # | Source | Says what, exactly | Type / establishment |
|---|---|---|---|
| 1 | O'Hara, Saar & Zhong, "Relative Tick Size and the Trading Environment", RAPS 9(1) 47–90 (2019); Oct 2015 working version read | $5–$10 and $10–$20 NYSE stocks matched to $20–$100 controls on industry + market cap: **percentage quoted and effective spread differences insignificant** | [PEER-REVIEWED] (working version) [read in full — Table 9 and §2.1 verbatim] |
| 2 | SEC Release 34-101070 (Sept 18 2024), *Regulation NMS: Minimum Pricing Increments, Access Fees, and Transparency of Better Priced Orders* | States the price-invariance of percentage cost away from the tick constraint; GE 8-for-1 reverse split cut relative quoted spread ~8 bp → ~2 bp | [PRIMARY DATA DOC] [read in full — 518 pp. extracted, relevant sections verbatim] |
| 3 | Novy-Marx & Velikov, "A Taxonomy of Anomalies and Their Trading Costs", RFS 29(1) 104–147 (2016); NBER w20721 | Cost-measured **universe restriction is the weakest of three mitigation levers**; tangency portfolio gives it zero weight | [PEER-REVIEWED] (NBER version) [read in full — §5, §5.1, §5.4 verbatim] |
| 4 | Soebhag, Van Vliet & Verwijmeren, "Non-Standard Errors in Asset Pricing: Mind Your Sorts", *J. Banking & Finance* (2024); FoFI-2022 working version read | $5 price filter is one of 11 nodes over 2,048 variants. **Gross Sharpe: immaterial. Net max Sharpe: 0.12 → 0.18.** Survey: only **18.3%** of studies impose a price filter | [PEER-REVIEWED] (working version) [read in full — §3.1.5, §4, App. C.3 verbatim] |
| 5 | Chen & Zimmermann, "Open Source Cross-Sectional Asset Pricing", CFR 11(2) 207–264 (2022); FEDS 2021-037 read | Across 205 predictors, **the $5 price screen is the *softest* liquidity adjustment**; NYSE-only / market-equity / value-weighting each cut the typical mean from ~60 to ~40 bp/month | [PEER-REVIEWED] (FEDS version) [read in full — §5.2 verbatim] |
| 6 | Hou, Xue & Zhang, "Replicating Anomalies", RFS 33(5) 2019–2133 (2020); NBER w23394 | Explicitly **declines** a $5 screen and says why: "These stocks are mostly microcaps. Value-weighting … assigns only tiny weights to these stocks, which in turn do not need to be excluded." | [PEER-REVIEWED] (NBER version) [read in full — §3.1, App. A.1.4 verbatim] |
| 7 | Lesmond, Schill & Zhou, "The Illusory Nature of Momentum Profits", JFE 71 349–380 (2004) | Sorting **directly on estimated trading cost**: gross P3−P1 *rises* 1.4% → 8.7% across cost classes 1–4. A cost screen removes the highest-gross names | [PEER-REVIEWED] [read in full] |
| 8 | Hagströmer, "Bias in the Effective Bid-Ask Spread", JFE 142(1) (2021); Sept 2019 version read | Midpoint effective spread **overstates** cost; bias **97%** for S&P 500 stocks priced below $15, significant up to **$115** | [PEER-REVIEWED] (working version) [read in full — §1 verbatim] |
| 9 | Birru & Wang, "The Nominal Price Premium" (Mar 2016) and "Nominal price illusion", JFE 119(3) 578–598 (2016) | "**raw price does not predict return robustly**"; "**there exists no empirical relationship between nominal price and skewness after one controls for other firm characteristics**" | [WORKING PAPER] / [PEER-REVIEWED] [read in full / snippet only respectively] |
| 10 | Korajczyk & Sadka, "Are Momentum Profits Robust to Trading Costs?", JF 59(3) (2004) | Fixes the cost problem by **liquidity weighting**, not by a universe filter. No price screen in the paper | [PEER-REVIEWED] [read in full — searched for price screens, none found] |
| 11 | Bali, Cakici & Whitelaw, "Maxing Out" (Apr 2008 version) | §VII.D in full: "**Eliminating stocks with prices below $5 has little qualitative effect on the results. If anything, it strengthens the results for the equal-weighted portfolios.**" **No number is given.** | [WORKING PAPER — published JFE 2011] [read in full] |
| 12 | Bhardwaj & Brooks, "The January Anomaly: Effects of Low Share Price, Transaction Costs, and Bid-Ask Bias", JF 47(2) 553–575 (1992) | January effect is "primarily a low-share price effect and less so a market value effect" — price carries information size does not | [PEER-REVIEWED] [abstract only — 1977–86 sample, pre-decimalisation] |
| 13 | `zipline/finance/commission.py`, master branch | `DEFAULT_PER_SHARE_COST = 0.001  # 0.1 cents per share`; `DEFAULT_MINIMUM_COST_PER_EQUITY_TRADE = 0.0` | [PRIMARY DATA DOC] [read in full — source read, not executed] |
| 14 | Quantopian forum, "Working On Our Best Universe Yet: QTradableStocksUS" (archive mirror) | "**Prior day's close: If a stock's price is lower than $5, the bid-ask spread becomes larger relative to the price, and the transaction cost becomes too high.**" | [PRACTITIONER] [read — target sentences verbatim] |
| 15 | QuantConnect docs, Fundamental Universes | `where f.price > 10 && f.HasFundamentalData`; **no rationale stated** | [PRACTITIONER] [snippet only] |
| 16 | Novy-Marx & Velikov, `AssayingAnomalies` MATLAB toolkit README | Config exposes share-code, dates, cost method. **No price-filter parameter exists.** | [PRIMARY DATA DOC] [read in full — raw README, grepped] |
| 17 | Ball, Kothari & Shanken, JFE 38(1) 79–107 (1995) | Five-year contrarian returns driven by lowest-price quartile; a fractional price increase moves the mean materially | [PEER-REVIEWED] [**NOT ESTABLISHED** — RePEc carries no abstract, paywalled; see final section item 3] |

---

## 1. THE SENSITIVITY QUESTION: how much of a result is carried by the screen?

### 1.1 The best evidence is binary ($5 vs none) and says the screen is cheap on gross

**Chen & Zimmermann**, *Open Source Cross-Sectional Asset Pricing*, FEDS 2021-037, §5.2,
across 205 "clear and likely" predictors. [PEER-REVIEWED — CFR 2022] [read in full]

> "Intuitively, all liquidity adjustments lead to lower mean returns. The price screen
> (limiting to stocks with share price > $5) appears to be the softest adjustment,
> producing the smallest decline in performance. The other liquidity adjustments have
> relatively similar effects.
>
> Overall, simple liquidity adjustments reduce mean returns by a factor of about 1/3, on
> average. The typical mean return drops from around 60 bps per month to about 40 bps per
> month regardless of whether the adjustment is an NYSE only screen, a market equity
> screen, or the enforcement of value-weighting."

Read it carefully, both ways:

- A $5 screen costs **less** than one third of mean return — the other three adjustments
  cost about one third each, and the price screen costs less than they do.
- But **the paper gives no number for the price screen alone.** The magnitude lives only in
  their Figure 9, a jitter plot. The sentence is a ranking, not a measurement. I record it
  as *softest, unquantified in text*.
- This is **in-sample mean return of mostly equal-weighted long-short portfolios**, which
  is the right weighting regime for this programme and an unusually good match.

### 1.2 The one NET measurement, and it favours having a floor

**Soebhag, Van Vliet & Verwijmeren**, App. C.3, "Net Sharpe Ratios". Eleven construction
choices, all 2,048 combinations, 40 sorting variables, Jan 1972 – Dec 2021.
[PEER-REVIEWED — JBF 2024] [read in full]

> "Likewise, including microcaps yields lower net Sharpe ratios (0.12) than excluding
> microcaps (0.18). Including a price filter also improves the net Sharpe ratio (0.18 vs
> 0.12), since this excludes small illiquid stocks with high transaction costs.
> Furthermore, using value-weighting instead of equal-weighting puts less weight towards
> microcaps and yields an average Sharpe ratio of 0.20 versus 0.10. With gross returns, we
> documented that Sharpe ratios are higher when we include microcaps and use
> equal-weighting. With net returns, we thus find the opposite effect, due to the
> differential costs involved."

And on gross, the same paper, §4:

> "Choices that do not lead to substantially different average Sharpe ratios include
> choices related to negative book equity firms, price filters, and utility firms."

Their node is **exactly $5**, stated in the Figure 3 caption: "'PRC' indicates whether
stocks with a price below 5 dollar are excluded ('Yes') or included ('No')."

So the cleanest published statement of the screen's effect is: **gross, immaterial; net,
+0.06 Sharpe (0.12 → 0.18), the same size as excluding microcaps.** That is the strongest
pro-floor number in this brief, and §2.3 explains why it is probably not a price result.

A second sentence from the same paper matters for *how much* the choice is worth arguing
about at all, §C.3 context and §5:

> "thus only leaves four choices open: whether to impose price filters (but this seems less
> important now that microcaps are excluded) …"

**Their own reading is that the price filter's importance is conditional on, and largely
absorbed by, the microcap decision.**

### 1.3 The prevalence of the convention, measured

Same paper, Table 2 (survey of the published literature's reported choices):

> "Choice 5 Impose price filter No price filter 18.3% 81.7%"

and in the text:

> "Other popular options are to not impose industry neutrality (88.5%), to include
> microcaps (88.2%), to not impose a price filter (81.7%), and to include firms with
> negative book equity values (78.0%)."

**This corrects a premise worth correcting: the $5 screen is not "near-universal" in
empirical asset pricing. Slightly over four fifths of the surveyed studies impose no price
filter at all.** The convention is widespread in the *momentum and liquidity* corner that
Amihud (2002) and Jegadeesh-Titman (2001) anchor, not across the field. And on the level:

> "stocks are dropped for having share prices below a minimum, which typically varies
> between $1 and $5. In fact, the most common price filters use a minimum of exactly $1
> (e.g, Lee and Swaminathan (2000)) or exactly $5 (e.g, Amihud (2002))."

So the published levels are **$1 and $5, bimodal, and nothing above $5 is named.**

### 1.4 A worked example of a sensitivity check reported with no magnitude

**Bali, Cakici & Whitelaw**, "Maxing Out", April 2008 version, §VII.D in its entirety.
[WORKING PAPER — JFE 2011] [read in full]

> "D. Eliminating Low-Priced Stocks
> Eliminating stocks with prices below $5 has little qualitative effect on the results. If
> anything, it strengthens the results for the equal-weighted portfolios."

Two sentences, no table, no number, no t-statistic, no statement of how much the universe
shrank. I include it precisely because it is typical: **the literature's price-screen
robustness checks are mostly assertions of insensitivity with the magnitude suppressed.**
Being biased toward the negative, I record this as a *claim of insensitivity*, not as
evidence of it.

### 1.5 The multi-level sensitivity the lane asked for does not exist

I searched for published work tabulating a result at $1, $5 and $10 (and at intermediate
levels), and for any paper reporting the fraction of a cross-sectional result carried by
the $1–$5 band or the $5–$10 band. **I found none.** Every screen-sensitivity result I
located is binary: screen versus no screen, and almost always at $5. The Soebhag node is
binary at $5. The Chen-Zimmermann comparison is binary at $5. Bali et al. is binary at $5.
Hou-Xue-Zhang is binary at $5.

**Record this as an explicit negative: the marginal contribution of the $5–$10 band to a
cross-sectional result is, as far as I can establish, unmeasured in the published
literature.** It is, however, directly measurable on this programme's own fixture, and
§6 says what I would measure.

---

## 2. WHAT IS THE SCREEN ACTUALLY PROXYING FOR?

### 2.1 The leading replication study says: microcaps, and it refuses the screen on that basis

**Hou, Xue & Zhang**, *Replicating Anomalies*, NBER w23394, Appendix A.1.4.
[PEER-REVIEWED — RFS 2020] [read in full]

> "We do not impose a price screen to exclude stocks with prices per share below $5 as in
> Jegadeesh and Titman (1993). These stocks are mostly microcaps. Value-weighting returns
> assigns only tiny weights to these stocks, which in turn do not need to be excluded."

This is the most important sentence in the brief for Q2, and it is load-bearing in a way
that cuts **against** this programme. The authors' position is that **a $5 price screen is
a crude substitute for value-weighting** — both suppress microcaps, and if you
value-weight you do not need the screen.

**This programme is equal-weighted. The substitution the literature relies on is therefore
unavailable to it, and the screen is doing real work here that it does not do in most of
the papers it was inherited from.** That is a genuine reason this programme's floor
question is not the literature's floor question — and it is a reason the floor matters
*more* here, not less.

HXZ's own alternative is breakpoints plus weighting, §3.1:

> "Microcaps are stocks with the market equity below the 20th percentile of NYSE stocks.
> Microcaps are on average only 3% of the market value of the NYSE-Amex-NASDAQ universe,
> but account for about 60% of the total number of stocks. Due to high transaction costs
> and illiquidity, anomalies in microcaps are unlikely to be exploitable in practice."

and their updated Fama-French (2008) Table I, §3.1:

> "on average, there are 2,406 microcaps, which account for 61% of the total number of
> firms, 3,938. However, microcaps represent only 3.28% of the total market capitalization,
> small stocks 6.77%, and big stocks 90%."

### 2.2 Cost models built by the people who measure costs do not contain price

**Novy-Marx & Velikov**, NBER w20721, Table 1 and §2. Their cost variable is the
Hasbrouck (2009) Gibbs-sampler effective spread, and when a direct estimate is missing
they impute it from characteristics. The characteristics they choose:

> "The high observed cross sectional correlations between transaction costs and size and
> idiosyncratic volatility lead us to match on these characteristics. Specifically, in each
> month we rank all firms on market equity and estimated idiosyncratic volatility."

Their Fama-MacBeth determinants regression (Table 1) contains lagged t-costs, `log(ME)`,
`log(ME)²` and idiosyncratic volatility. **Nominal price appears nowhere.** They also warn
against the obvious parametric shortcut:

> "More generally, nonlinearities make it difficult to parametrically estimate costs
> accurately using directly observable firm characteristics. Table 14 in Appendix A.2
> highlights the danger of extrapolating transaction costs estimated on large, relatively
> liquid stocks to small stocks using a linear model."

Soebhag et al. replicate exactly this imputation (their eq. 13: Euclidean distance in
`rank(ME)`, `rank(IVOL)` space). **So the two papers that give me net numbers both model
cost on size and volatility, not on price** — which is why §1.2's net-Sharpe gain is most
plausibly a size/illiquidity effect that the $5 screen happens to pick up, not a price
effect.

### 2.3 Is a price screen the right instrument? The substitution evidence

Three pieces, and they point the same way.

**(a) Direct cost sorts remove the highest-*gross* names.** Lesmond, Schill & Zhou (JFE
2004), §5.3, sorting on estimated trading cost rather than on price:
[PEER-REVIEWED] [read in full]

> "Across trading cost classes the P3-P1 returns increase from 1.4% for the lowest cost
> class, to 4.3% for class 2, to 7.9% for class 3, to 8.7% for class 4, and finally down to
> 5.2% for the largest trading cost class."

A cost screen is therefore **not free**: the gross signal rises monotonically with cost
across four of five classes. This is the cleanest statement of the trade-off in any
instrument you pick — price, spread or dollar volume — because all three are cost proxies.
It also shows the non-monotonicity at the extreme (class 5 falls back), which is the
empirical shape that makes *some* floor defensible and an aggressive one not.

**(b) The same paper quantifies what a $5 screen does to price composition.** Table 1,
comparing the Jegadeesh-Titman (1993) universe (no price screen) with the JT (2001)
universe (`P > $5` plus smallest-NYSE-decile exclusion):

| | JT(1993), no screen | JT(2001), `P>$5` + size |
|---|---|---|
| Loser portfolio P1 mean share price | **$8.95** | **$16.20** |
| P1 median share price | **$6.32** | **$13.71** |
| P1 mean market cap ($m) | 308.0 | 556.8 |
| Gross P3−P1 monthly | 0.884% | 1.304% |

The screen roughly **doubles** the loser leg's mean and median price and raises its mean
market cap by 81%. Note that the gross spread went **up**, not down — but the universes
differ in breakpoints and exchange coverage too, so this is not a clean screen experiment
and I do not read it as one.

**(c) The modern reference toolkit has no price knob at all.** I fetched the raw README of
`velikov-mihail/AssayingAnomalies` (the toolkit accompanying Novy-Marx & Velikov 2023) and
grepped it. The configurable sample parameters are share-code (`domComEqFlag`, share codes
10/11), `SAMPLE_START`/`SAMPLE_END`, and `tcostsType` ('gibbs', 'lf_combo', 'full').
**There is no minimum-price parameter.** [PRIMARY DATA DOC] [read in full]

The direction of the field is therefore: **replace the price screen with an explicit cost
model, and handle microcaps through breakpoints and weighting.** That is a programme
this book cannot fully follow, because it is equal-weighted by design — but the
*instrument* lesson survives: if the target is cost, screen on the cost proxy (dollar
volume, measured spread), not on price.

### 2.4 But price is not *merely* a size proxy — two dissenting results

Being biased toward the negative on my own conclusion:

- **Bhardwaj & Brooks (JF 1992)** find the January effect is "primarily a low-share price
  effect and less so a market value effect" — i.e. price dominates size for that anomaly.
  [PEER-REVIEWED] [abstract only] **Caveat that matters a great deal: 1977–1986, $1/8
  ticks, pre-decimalisation.** This is the era whose microstructure Amihud's footnote 10
  invoked, and it is exactly the era the commissioning brief says stopped being relevant
  in 2001. I record it as historical, not current.
- **Birru & Wang** establish a behavioural channel that is genuinely about nominal price
  and not about size: investors systematically mis-perceive low-priced stocks. From
  "The Nominal Price Premium" (Mar 2016), quoting their own earlier paper:
  [WORKING PAPER] [read in full]

  > "Birru and Wang (2015) find that while there exists no empirical relationship between
  > nominal price and skewness after one controls for other firm characteristics, investors
  > nevertheless incorrectly perceive low-priced stocks to have greater upside potential."

  And from their abstract, on the screening-relevant point:

  > "In the cross-section, a portfolio exploiting this strategy generates a value-weighted
  > (equal-weighted) four-factor alpha of 85 (88) basis points per month, while **raw price
  > does not predict return robustly**."

  Two consequences for this lane. First, **raw nominal price is not itself a robust return
  predictor**, so a raw-price screen is unlikely to be removing or adding alpha *through
  the price dimension per se*. Second, their sign — low-priced stocks are *overpriced* —
  means a floor is asymmetric across legs: it removes a population their evidence says is
  systematically overpriced, which is a modest positive for a long book and a modest
  negative for a short one. **This is an asymmetry, not a symmetric nuisance filter, and
  any floor decision here should be dispositioned per leg.**

---

## 3. WHAT PRACTITIONERS UNDER PER-SHARE COMMISSION REGIMES USE

Short answer: **the convention is visible in code and forum posts, it is not written down
anywhere I would call credible, and the one place it is justified in writing gives the
*cost* reason rather than the tick-noise reason.** Treated sceptically throughout.

### 3.1 The most-used open-source backtester is a per-share regime, verified in source

`zipline/zipline/finance/commission.py`, master branch, lines 26–30, read as raw source:
[PRIMARY DATA DOC] [read in full — source read, not executed]

```
DEFAULT_PER_SHARE_COST = 0.001               # 0.1 cents per share
DEFAULT_PER_CONTRACT_COST = 0.85             # $0.85 per future contract
DEFAULT_MINIMUM_COST_PER_EQUITY_TRADE = 0.0  # $0 per trade
```

`class PerShare(EquityCommissionModel)` takes `cost=DEFAULT_PER_SHARE_COST`,
`min_trade_cost=DEFAULT_MINIMUM_COST_PER_EQUITY_TRADE`. This matters for one reason only:
**the retail/quant backtesting ecosystem in which the $5 universe convention circulates is
a per-share-commission ecosystem, so the cross-sectional distortion this lane is about is
baked into its defaults.** At `c = $0.001` the commission is 2 bp/side at $5 — an order of
magnitude smaller than at `c = $0.005`, so conventions inherited from this ecosystem are
calibrated to a cost this programme does not face.

### 3.2 The one practitioner statement with a stated rationale — and it is the cost rationale

Quantopian, "Working On Our Best Universe Yet: QTradableStocksUS" (read from the archive
mirror; the live site is gone). [PRACTITIONER] [read — target sentences verbatim]

> "Prior day's close: If a stock's price is lower than $5, the bid-ask spread becomes
> larger relative to the price, and the transaction cost becomes too high."

> "Dollar volume: It is important that stocks in our universe be relatively easy to trade
> when entering and exiting positions. The QTradableStocksUS manages that by including only
> stocks that have median daily dollar volume of $2.5m or more over the trailing 200 days."

> "Market cap: over $500M: This restriction eliminates many undiversifiable risks like low
> liquidity and difficulty in shorting."

Three observations, two of them unflattering.

1. **The stated reason is cost, not tick noise.** Nobody in this lane's sources restates
   Amihud's $1/8 justification. The practitioner framing had already migrated to cost.
2. **The reason given is the one §5 shows is wrong.** "If a stock's price is lower than $5,
   the bid-ask spread becomes larger relative to the price" is precisely the claim
   O'Hara-Saar-Zhong test at this boundary and fail to find, once size is matched. It is
   true unconditionally and false conditionally, and a screen has to be judged
   conditionally on the other screens already in place.
3. **With a $500M market-cap floor and a $2.5M dollar-volume floor already in the
   definition, the $5 price screen is close to redundant.** That is the structure the
   evidence supports: the binding screens are the size and liquidity ones; the price screen
   rides along.

This is a forum post by a platform vendor about its own product universe. I rate it
[PRACTITIONER] rather than [SALES INSTRUMENT] because it is a methodology post with stated
criteria and no pricing pitch, but it carries no external validation and I would not cite
it for anything but the fact that this is what they said.

### 3.3 Platform documentation exposes the knob and justifies nothing

QuantConnect Fundamental Universes documentation. [PRACTITIONER] [snippet only]

The documented examples use `where f.Price > 10 && f.HasFundamentalData` and describe an
example universe as selecting "the 500 most liquid US Equities above $10/share and $10M in
daily volume". **The documentation gives no rationale for $10.** It is an illustrative
constant in a code sample. I looked for a stated reason and there is not one.

### 3.4 What I did not find

I found **no credible written-down practitioner standard** that derives a price floor from
a per-share commission schedule. No fund document, no sell-side methodology note, no
academic appendix. The category of source that would settle Q3 — a per-share-commission
manager stating and defending its universe floor in writing — I could not locate. This is
item 2 in the final section.

---

## 4. A PRINCIPLED WAY TO SET THE LEVEL FROM THE COST MODEL

**This is the part of the lane that delivers, and it delivers a formula whose behaviour is
the finding.** The arithmetic is mine, parametric, and computed rather than asserted
(`scratchpad/j4/floor.py`); the literature contribution is that **nobody published this,
and the one paper that filters on measured cost reports that the filter barely works.**

### 4.1 The identity

Let `c` be the per-share commission in dollars per share, charged both sides. Commission
as a fraction of notional is `c/P`, independent of order size. In basis points:

```
commission per side      = 10000 · c / P   bp
commission per round trip = 20000 · c / P   bp
```

At `c = $0.005/share` this is exactly the brief's "roughly 50/P bp per side". Computed:

| P | commission bp/side | bp round trip |
|---|---|---|
| $1 | 50.00 | 100.00 |
| $2 | 25.00 | 50.00 |
| $3 | 16.67 | 33.33 |
| **$5** | **10.00** | **20.00** |
| $7.50 | 6.67 | 13.33 |
| **$10** | **5.00** | **10.00** |
| $15 | 3.33 | 6.67 |
| **$20** | **2.50** | **5.00** |
| $50 | 1.00 | 2.00 |
| $100 | 0.50 | 1.00 |

### 4.2 The break-even price, and why it is not a constant

Write `s` for the round-trip spread cost in bp (the brief supplies 67.6, flagged as a
floor) and `g` for the strategy's expected **gross** edge per round trip in bp. A trade
pays when

```
g  ≥  s  +  20000·c/P
```

so the minimum admissible price is

```
P_min  =  20000·c / (g − s)            and P_min = ∞ when g ≤ s.
```

**The shape of this is the result.** At `c = $0.005` and `s = 67.6` bp:

| gross edge `g` per round trip | `P_min` |
|---|---|
| 70 bp | **$41.67** |
| 75 bp | **$13.51** |
| 80 bp | **$8.06** |
| 90 bp | **$4.46** |
| 100 bp | **$3.09** |
| 120 bp | $1.91 |
| 150 bp | $1.21 |
| 200 bp | $0.76 |
| ≤ 67.6 bp | **no price floor can make the trade pay** |

Read what this says.

- **A $5 floor is the correct floor only for a strategy whose gross edge per round trip is
  about 87.6 bp.** Above that, $5 is conservative. Below it, $5 is too low and the right
  level climbs very fast.
- **The function is hyperbolic in `(g − s)`.** Between `g = 80` and `g = 70` — a 10 bp
  change in gross edge, well inside any reasonable estimation error — the defensible floor
  moves from $8 to $42. **Any floor claimed to be derived from the cost model inherits the
  gross edge's error bar, magnified.** A programme that cannot pin `g` to better than
  ±10 bp cannot pin its floor to better than a factor of five, and should say so rather
  than quoting a level.
- **The spread is the first-order term and the commission is second-order.** Because `s`
  enters the denominator and `c` only the numerator, the floor is far more sensitive to the
  spread estimate than to the commission rate. The brief states the 33.8 bp/side figure
  came from Corwin-Schultz and should be read as a floor; the second block of the table
  shows the consequence — at a true round-trip spread of 100 bp, a strategy needs 120 bp
  gross just to justify a $5 floor and 110 bp to justify $10. **Tightening the spread
  estimate is worth more to this decision than choosing the floor.**

### 4.3 The marginal value of raising the floor, and why it is exhausted quickly

| move | saving, round trip |
|---|---|
| $5 → $7.50 | 6.67 bp |
| $5 → $10 | **10.00 bp** |
| $5 → $15 | 13.33 bp |
| $5 → $20 | **15.00 bp** |
| $5 → $50 | 18.00 bp |
| $5 → ∞ | **20.00 bp** |

**Half the total available saving is bought by the first step to $10, and three quarters by
$20.** Beyond $20 the lever is spent: going from $20 to infinity is worth 5 bp round trip.
Against a 67.6 bp spread (itself a floor), **the entire price-floor lever is worth under
30% of one cost component, and the incremental portion above $10 is worth under 15%.**

If the programme wants one sentence to replace the convention, it is this: **the floor is
worth `20000c(1/P_old − 1/P_new)` basis points of round trip, and nothing else; compute
that against the breadth you give up, per strategy, and stop treating it as a data-quality
question.**

### 4.4 Two structural caveats that a per-share regime must carry

- **A per-order minimum is not addressed by a price floor.** If the schedule carries a
  minimum `m` dollars per order, that minimum costs `10000·m/V` bp on an order of `V`
  dollars — a function of **position size**, not of price. Raising the price floor does
  nothing to it. Where the minimum binds, it dominates the per-share term and the price
  floor is even less useful than §4.3 suggests. (Parametric; I do not quote any schedule.)
- **A per-share commission's relation to price is exact and the only exact thing here.**
  Every other term in the cost model — spread, impact, fill quality — is estimated. This
  makes `20000c/P` tempting to optimise precisely because it is the one term you can
  compute. That is a trap worth naming: **the lever you can measure exactly is the small
  one.**

### 4.5 What the literature has on choosing a filter from a cost model

**The answer is: one paper does it, it is not a price filter, and it reports that it barely
works.**

Novy-Marx & Velikov, NBER w20721, §5 and §5.1. [PEER-REVIEWED — RFS 2016] [read in full]

> "The first of these simply limits trading to the universe of stocks that we expect to be
> relatively cheap to trade."

> "The first transactions cost mitigation technique we examine is limiting the universe of
> stocks to low trading cost stocks. To this end, we use only stocks that are in the low
> lagged trading cost tertile of each NYSE size decile. Since the effective spread measure
> is fairly persistent, this procedure helps us identify the low-cost universe without
> having a look-ahead bias."

This is the principled generalisation of a price floor: **filter on the cost estimate
itself, conditionally on size.** Their result:

> "Surprisingly this procedure does not significantly reduce the trading costs for any of
> the mid-turnover strategies. The average turnover and trading costs are similar to the
> ones for the strategies, which can be most easily seen in the last column. Only the PEAD
> (CAR3) anomaly has a positive and statistically significant αFF4+net, and this comes
> primarily from an increased gross spread, not a reduction in the cost of trading the
> strategy. Restricting the universe to the low trading cost does not add much over using
> the traditional decile sort on the entire universe for the mid-turnover anomalies.
>
> For the high-turnover strategies, however, there seems to be a marked reduction in
> trading costs. While there is not much of a reduction in turnover, the trading costs for
> this lot decrease by 25% on average."

And against the alternatives (their Table 5, UMD-like factors, Jul 1973 – Dec 2012, monthly
percent):

| mitigation | E[r_gross] | T-costs | E[r_net] | α |
|---|---|---|---|---|
| Restrict to low cost universe | 0.66 | 0.35 | **0.31** | 0.17 |
| Staggered quarterly rebalancing | 0.62 | 0.26 | **0.37** | 0.19 |
| Trading hysteresis (buy/hold spread) | 0.77 | 0.26 | **0.51** | 0.33 |

> "The ex post mean-variance efficient portfolios, accounting for transaction costs, of the
> three momentum factors, or the three momentum factors and the three Fama-French factors,
> put no weight on the momentum factors constructed in the low cost universe and with
> staggered quarterly rebalancing."

**Three conclusions for this lane, in order of force.**

1. **A universe filter chosen from the cost model is the weakest of the three cost levers
   tested, and an optimiser allocates nothing to it.** The floor is the lever the programme
   is asking about; it is the lever this paper ranks last.
2. **Its one clear win is on high-turnover strategies (−25% cost).** If the programme's
   strategy is high-turnover, the filter is worth more than this summary implies; if
   mid-turnover, the paper's answer is "does not add much".
3. **The lever that works is the buy/hold spread — hysteresis** — and that is an exit-rule
   change, not a universe change. Worth noting that this is adjacent to, but distinct from,
   the settled mid-hold question: H4 asked what happens to a held name that falls through
   the floor; NMV's result says the *general* answer to cost is asymmetric entry and exit
   thresholds. The two lanes meet here.

Korajczyk & Sadka (JF 2004) reach a compatible conclusion by a different instrument. I read
the paper and searched it for price screens; **it imposes none.** Its answer to cost is
re-weighting: liquidity-weighted and hybrid liquidity/value-weighted strategies carry the
largest break-even fund sizes, and equal-weighting is the worst after costs. For an
equal-weighted programme that is a standing warning rather than an available fix.

**Explicit negative: I found no published work that derives a nominal price floor from a
cost model.** The derivation in §4.1–4.3 is arithmetic anyone could do and nobody appears
to have published. The bar asked whether such a basis exists in the literature; it does
not, and the nearest relative reports that the approach underperforms two alternatives.

---

## 5. THE POST-DECIMALISATION MICROSTRUCTURE QUESTION

### 5.1 The current regime, established

Under Rule 612 of Regulation NMS as currently in force, the minimum pricing increment is
**$0.01 for NMS stocks quoted at or above $1.00** and **$0.0001 below $1.00**. The
September 2024 amendments (Release 34-101070) adopt a second increment of **$0.005** for
"tick-constrained" stocks, defined by a Time Weighted Average Quoted Spread threshold of
**$0.015**. The SEC's own estimate, had the amendments been in force in 2023:

> "Table 7 indicates that, had the amendments been in place in 2023, approximately 66% of
> share volume and 43% of dollar volume, associated with an estimated 1,788 individual
> stocks, would likely have been assigned the $0.005 tick size."

The commissioning brief's statement that these are delayed is correct as far as I can
establish: the Commission extended temporary exemptive relief from the compliance dates for
Rules 600(b)(89)(i)(F), 610(c) and 612 **to the first business day of November 2027**. I
establish this from law-firm and trade-press reporting rather than from the exemptive order
itself — see item 4 of the final section. **The operative regime for a 2010-01-04 to
2026-08-26 fixture is the flat $0.01 tick throughout, and it will remain so.**

### 5.2 The exact relationship, and the SEC states it

The SEC sets out the price/spread relation explicitly in its reverse-split discussion:
[PRIMARY DATA DOC] [read in full]

> "A reverse split exchanges a fixed number of existing shares for a smaller number of new
> shares. The new shares have a higher price, but there are fewer of them. For example, if
> an issuer undergoes an 8-for-1 reverse split, eight shares are exchanged for one share
> that is worth the same as the eight, increasing the price by a factor of eight. All else
> equal, one would expect the quoted spread, which represents the per-share trading costs
> to also rise by a factor of eight. **Thus, the cost of transacting in the stock, for a
> given dollar exposure, would remain constant.** However, if a stock were tick
> constrained, undergoing a reverse split would cause the tick to become smaller relative
> to the (higher) stock price, thereby alleviating the tick constraint and reducing
> transaction costs."

and again, later:

> "When a stock undergoes a reverse split, its share price rises. All else equal, one would
> expect quoted spreads to widen in proportion so that the trading cost remains constant as
> a percentage of price. If the stock is tick-constrained, however, a reverse split causes
> the current penny tick to become lower relative to the (higher) post-split price,
> relieving the tick constraint and reducing trading costs as a percentage of the trade
> amount."

**This is the whole answer to Q5, from the regulator, in its own words: nominal price
affects relative transaction cost through exactly one channel — the tick constraint — and
through no other.** Two regimes follow.

**Regime A — tick-constrained.** Quoted spread pinned at one tick, so

```
quoted relative spread = 10000 · 0.01 / P  =  100/P  bp
half-spread            =                       50/P  bp
```

| P | one-tick quoted spread | half |
|---|---|---|
| $1 | 100 bp | 50 bp |
| $2 | 50 bp | 25 bp |
| **$5** | **20 bp** | **10 bp** |
| **$10** | **10 bp** | **5 bp** |
| $20 | 5 bp | 2.5 bp |
| $50 | 2 bp | 1 bp |

Note the coincidence worth naming: **at `c = $0.005/share`, the per-share commission per
side (`50/P` bp) is numerically identical to the one-tick half-spread.** Both are
cents-per-share constants divided by price. A per-share commission is, in bp terms,
mathematically a second tick.

The SEC's own worked example, and the empirical confirmation:

> "For example, suppose a stock trades at $10 per share and is tick-constrained such that
> it trades with a quoted spread of $0.01, but could sustain a quoted spread of $0.004 if
> not for the penny tick. If the stock undergoes a 5-for-1 reverse split, then the share
> price would rise to $50 (5*$10) and the quoted spread would rise to $0.02 (5*$0.004). …
> thus reducing transaction costs by 25%."

> "One study presented evidence from GE's eight-for-one reverse split, and showed that
> trading costs—as measured by the quoted spread as a fraction of the stock price—fell 75%.
> … Chart A of the study indicates that the reverse split caused the average quoted spread
> as a fraction of the share price to decline from approximately 8 basis points to 2 basis
> points."

GE at roughly 8 bp quoted pre-split is consistent with being pinned at one cent at a price
near $12.50 (`100/12.5 = 8`). **That is the signature of Regime A: a large, very liquid,
low-priced name.** The GE figures come to the SEC via a MEMX comment letter's attached
industry studies — exchange advocacy, so [SALES INSTRUMENT] in origin even though the
Commission reproduces them. I report them as the SEC's characterisation of a commenter's
study, not as peer-reviewed measurement.

**Regime B — not tick-constrained.** Spread is set by adverse selection, inventory cost and
competition; the tick is slack; and the SEC's "all else equal" says relative cost is
**invariant to nominal price**. A name whose half-spread is 33.8 bp at $10 is quoting about
6.8 cents — nearly seven ticks. **Nothing about raising its price to $20 narrows that
spread in percentage terms.** The population the commissioning brief describes — names
whose Corwin-Schultz half-spread measures 33.8 bp, with that treated as a floor — is
unambiguously in Regime B, not Regime A. **The tick-noise argument that justified the $5
convention in 1992, and the relative-spread argument that replaced it in practitioner
folklore, are both Regime-A arguments applied to a Regime-B population.**

### 5.3 Is there a documented threshold where relative spread stops improving with price? Yes — and it is below $10

**O'Hara, Saar & Zhong** measure this directly at the boundary this lane is about.
[PEER-REVIEWED — RAPS 2019] [read in full]

Design, §2.1:

> "Our sample period is May and June, 2012, and the universe of securities consists of all
> common domestic stocks listed on the NYSE. We form two groups with large relative tick
> sizes from among these stocks segmented by the stock price ranges $5–$10 and $10–$20
> (where we use the stock price on the day before the sample period begins). Within each
> price range, we sort stocks by market capitalization and choose a stratified sample of 60
> stocks in a uniform manner to represent the entire range of market capitalization."

> "Each stock in G1 and G2 is matched to a control stock with a small relative tick size,
> which means it has a higher price range (from $20 to $100), such that it is (i) in the
> same industry (using the Fama-French 10 industries classification), and (ii) closest to it
> in market capitalization."

> "The mean price of sample stocks in G1 is $7.56 (versus $32.56 for the control stocks),
> and the mean price of sample stocks in G2 is $14.55 (versus $34.95 for the control
> stocks)."

Results, Table 9 (sample-vs-matched-control differences; `MnDiff` is sample minus control):

**Panel A, dollar quoted spreads** — the low-priced groups have *tighter* dollar spreads,
strongly significant:

| group | measure | mean | median | MnDiff | p(t) |
|---|---|---|---|---|---|
| G1 ($5–$10) | $NBBOsprd | 0.023 | 0.014 | −0.060 | <.001 |
| G1 | $NYSEsprd | 0.026 | 0.017 | −0.068 | <.001 |
| G2 ($10–$20) | $NBBOsprd | 0.027 | 0.019 | −0.041 | <.001 |
| G2 | $NYSEsprd | 0.033 | 0.022 | −0.047 | <.001 |

**Panel B, percentage quoted spreads** — the differences vanish:

| group | measure | mean | median | MnDiff | p(t) |
|---|---|---|---|---|---|
| G1 ($5–$10) | %NBBOsprd | **0.33%** | 0.21% | +0.06% | 0.209 |
| G1 | %NYSEsprd | **0.38%** | 0.24% | +0.07% | 0.081 |
| G2 ($10–$20) | %NBBOsprd | **0.20%** | 0.16% | −0.008% | 0.728 |
| G2 | %NYSEsprd | **0.24%** | 0.18% | −0.003% | 0.925 |

**Panel C, percentage effective (half) spreads:**

| group | mean | median | MnDiff | p(t) |
|---|---|---|---|---|
| G1 ($5–$10) | **0.12%** | 0.07% | +0.03% | 0.048 |
| G2 ($10–$20) | **0.07%** | 0.05% | 0.00% | 0.872 |

The authors' own readings:

> "What is immediately apparent from the table is that dollar spreads for a size-stratified
> sample of NYSE stocks these days are very small: 2.6 cents in G1 (for $NYSEsprd) and 3.3
> cents in G2."

> "When we examine the results for percentage spreads, we indeed see a different picture: 11
> out of the 12 statistical tests (two spread measures x two groups x three statistical
> tests per measure/group) are not statistically different from zero at the 5% significance
> level. Hence, we find no evidence supporting a link between relative tick size and
> transactions costs in terms of percentage quoted spreads."

> "Panel C of Table 9 shows the percentage effective (half) spreads … Here as well, the
> regression coefficients in the right-most columns show no statistically significant
> difference between the sample and control stocks, strongly suggesting that these measures
> of transactions costs also do not seem to be related to the relative tick size."

> "In summary, we find that the relative tick size does not have a material effect on
> liquidity: results for depth are mixed depending on the measure, volume differences are
> insignificant, and percentage spreads differences are insignificant."

**So the documented threshold — the price above which relative spread stops improving with
price, holding size and industry fixed — is at or below $5, not above it.** Moving a name
from the $5–$10 band to the $20–$100 band buys nothing measurable in percentage quoted or
effective spread.

**Limits I am not going to soften.** NYSE-listed domestic common stocks only; two
stratified samples of 60; May–June 2012; matched on industry and market capitalisation, so
this is the *conditional* answer and deliberately so (the authors state they cannot match on
volume because volume is determined by cost). It says nothing about the unconditional
cross-section, where low price and wide spread certainly co-move because low price and
small size co-move. **It is exactly the right experiment for this lane's question, because
the question is whether price adds anything over the screens already in place — and the
answer is that it does not, once size is controlled.** It is also a different population
from any Nasdaq microcap tail.

### 5.4 One more reason to distrust a measured spread at low price

**Hagströmer** (JFE 2021; Sept 2019 version read) shows the *standard* midpoint effective
spread overstates liquidity cost, and that the overstatement is worst exactly where this
lane operates. [PEER-REVIEWED] [read in full]

> "First, the midpoint effective spread bias increases with price discreteness. This is
> because the asymmetry between bid- and ask-side effective spreads is more prevalent in
> stocks with high relative tick sizes (Anshuman and Kalay, 1998). With the minimum tick
> size being fixed at USD 0.01 for most US stocks, those with low share prices have high
> relative price discreteness. I find that the effective spread overestimation for the
> lowest priced S&P 500 stocks (below USD 15) has a bias of 97% on average. The bias remains
> statistically significant for price levels up to USD 115, representing 76% of the S&P500
> trading volume."

> "Forming quintile liquidity portfolios based on the midpoint effective spread, I find that
> only 56% of the stocks are allocated to the same portfolio as when the micro-price
> effective spread is used."

**Read this narrowly and do not let it cancel the Corwin-Schultz warning.** It is a
statement about the *midpoint* effective spread measured from trades against the quote
midpoint, on a 120-stock S&P 500 sample, where "below USD 15" means a large liquid firm —
Regime A again. It does **not** say Corwin-Schultz overstates; Corwin-Schultz is a
different estimator and the brief's note that it *understates* for small and illiquid
stocks concerns Regime B. The honest summary is: **the two leading biases in low-price
spread measurement run in opposite directions in the two regimes, and the sign of the net
bias for a Regime-B microcap population is not something I can establish from these
sources.** That is item 5 of the final section, and it is directly load-bearing on §4.2,
where `s` is the dominant parameter.

### 5.5 A flatness result at the top end, for completeness

From the SEC's economic analysis (May–October 2023 data):

> "Based on an analysis of data from May-October 2023, the average quoted spread of a stock
> priced between $250 and $1,000 was $0.71, far greater from the $0.015 that will trigger a
> smaller minimum increment. Similarly, for stocks priced between $1,000 and $10,000 the
> average quoted spread was $3.85"

$0.71 across $250–$1,000 and $3.85 across $1,000–$10,000 are both on the order of 10–15 bp
relative. **Relative spread does not keep falling as price rises; at the top of the price
range it is roughly flat and comparable to mid-priced names.** These are bucket averages
over volume-weighted prices and I treat them as directional only.

---

## 6. THE HONEST TRADE-OFF

The lane requires that no direction be reported without the cost of moving in it. Here it
is, with the two parts separated because one I can quantify and one I cannot.

**What raising the floor buys: at most 20 bp of round trip, all of it commission.**
§4.3 computes it. $5 → $10 is 10 bp; $5 → $20 is 15 bp; the asymptote is 20 bp. On the
spread — the larger term — §5.3 measures the gain as statistically indistinguishable from
zero, holding size fixed. **So the purchase is small, exact, and front-loaded.**

**What it costs: breadth, and the brief says breadth is already the binding constraint.**
The brief supplies ~1,573 names, ~35.7% dead, and an effective breadth of ~10 independent
instruments. I cannot measure how many names sit in the $5–$10 band of this universe — that
is a property of their data and I make no claim about it. But the structure of the cost is
clear and asymmetric:

- The grossest signal tends to sit in the costliest names. Lesmond et al.: gross P3−P1
  rises from 1.4% to 8.7% across cost classes 1 to 4. **A floor is a cut taken out of the
  high-gross tail.**
- Effective breadth scales like `√N` at best, and is already ~10 against 1,573 names, so
  the marginal independent instrument is expensive. A floor that removes a price band
  removes names that are disproportionately small and therefore disproportionately
  *idiosyncratic* — which is to say disproportionately useful for breadth. **Cutting the
  most idiosyncratic names to save 10 bp is the worst available trade on breadth per basis
  point.**
- The effect is asymmetric across legs. Birru & Wang's sign says low-priced names are
  systematically overpriced: removing them is mildly favourable to a long book and mildly
  unfavourable to a short one. **A single floor applied to both legs is not neutral.**

**What I would do instead, stated as the evidence's implication rather than as a
recommendation about their book.** Three things, in order:

1. **Stop calling it a data-quality screen.** It is a cost-model parameter and the brief is
   right about that. The justification to write down is `20000c/P` against `g − s`, not
   Amihud's footnote.
2. **Screen on the variable that carries the cost.** §2 is unanimous across four
   independent papers that the cost-bearing variables are size, illiquidity and volatility,
   not price. This programme already has a trailing dollar-volume screen. **Tightening that,
   or adding a direct trailing spread screen, dominates raising the price floor on the
   evidence** — and Novy-Marx & Velikov's low-cost-universe result warns that even that
   will disappoint on mid-turnover strategies.
3. **Measure the $5–$10 band's contribution, because nobody has published it.** §1.5
   establishes the gap. This programme can close it on its own fixture and the measurement
   is the one the literature cannot supply: gross mean per trade, net mean per trade, and
   breadth, for the band and for the remainder, reported under the programme's own
   four-group standard. **That is a measurement, not a convention, and it is the only way
   this lane's question gets a number that is defensible here.**

One dog that did not bark, reported because it should be: **I considered and rejected
integer-share quantisation as an argument against a high floor.** Rounding an equal-weight
slot to whole shares costs at most `P/(2V)` of the slot; at a $5,000 order it is 0.05% at
$10 and 0.20% at $20. **Real but negligible. I am not going to dress it up as a finding.**

---

## 7. CONTROLS AND HYGIENE

- **No parameterised endpoint was harvested.** Every source was a static document fetched
  once by URL. The HTTP-200-can-be-wrong control does not apply in its intended form, so I
  substituted a stronger one for the risk it guards against (a cache serving the wrong
  bytes): I extracted the title page of **every** downloaded PDF and confirmed each matches
  the work I cite it as. All twelve matched — Bali/Cakici/Whitelaw, Birru/Wang,
  Chen/Zimmermann FEDS, Hagströmer, Hou/Xue/Zhang w23394, Korajczyk/Sadka JF 2004,
  Lesmond/Schill/Zhou JFE 2004 (plus a conference version), Novy-Marx/Velikov w20721,
  O'Hara/Saar/Zhong, SEC 34-101070, Soebhag et al.
- **Negative-control greps**, which must return zero and did: `"price filter of $7"` in
  Soebhag (0), `"zzzimpossible"` in Novy-Marx/Velikov (0), `"tick size of $0.37"` in the SEC
  release (0).
- **One summariser error caught, and it is why the rule exists.** A search summariser
  reported Hagströmer's low-price effective-spread bias as **52%**. The paper says **97%**
  (and 39% for non-HFTs, 65% in a second sample). I read the sentence in the PDF. Every
  figure in this brief that carries quotation marks was read in the source document; the
  one place I rely on secondary reporting is flagged in item 4 below.
- **Arithmetic**: §4 and §5.2 are computed by `scratchpad/j4/floor.py`, not asserted. All
  downloaded PDFs and extracted text remain in the scratchpad; they are temp-grade and
  deletable. Nothing this brief *quotes* depends on a file outside `data/` except the
  scratchpad copies; if any quoted source needs to become evidence, the PDF should be moved
  into `data/`.
- **Blocks logged by tool and response**, per the rule:
  - `curl` (UA `Mozilla/5.0 (research; research@backtest-framework.org)`) → SSRN delivery
    URL for Walter/Weber/Weiss "Methodological uncertainty in portfolio sorts": **HTTP 403**,
    5,807-byte HTML body. Not retried; the Soebhag et al. paper covers the same question and
    was obtained.
  - `curl` (same UA) → `oxford-man.ox.ac.uk` slide deck for *Assaying Anomalies*: **HTTP
    403**, HTML body. Substituted the GitHub raw README, which answered the question.
  - No CAPTCHA, no login, no form, no account, nothing downloaded that was not a public
    document at a public URL.
- **No page instructed me to do anything.** I read twelve PDFs, one source file, one
  README, two vendor documentation pages and one archived forum thread, and found **no text
  addressed to an AI agent, no instruction, no injected directive.** Nothing to quote under
  the safety rule.

---

## 8. WHAT I COULD NOT VERIFY, STATED PLAINLY

1. **No published work varies a price screen across levels.** I could not find any paper
   reporting a result at $1, $5 and $10, or reporting the share of a cross-sectional result
   carried by the $1–$5 or $5–$10 band. Every sensitivity result I located is binary at $5.
   **The lane's central empirical question is, as far as I can establish, unanswered in the
   literature.** I searched for it five different ways and record the negative rather than
   substituting a proxy.
2. **No credible written-down practitioner floor for a per-share commission regime.** I
   found the convention in code defaults (zipline, per-share, verified) and in a vendor
   forum post (Quantopian, $5, with a cost rationale that §5 contradicts), and platform
   documentation that uses `price > 10` in examples with **no stated reason**. I found no
   fund document, methodology note or practitioner paper that derives a floor from a
   per-share schedule. **Absence of a source, not a source saying there is no convention.**
3. **Ball, Kothari & Shanken (1995) is NOT established.** The RePEc page returns "No
   abstract is available for this item" and the ScienceDirect full text is paywalled. The
   figures circulating for it (a 163% five-year contrarian mean driven by the lowest-price
   quartile; a fractional-dollar price increase reducing the mean by ~25%) reached me only
   through a search summariser, which is the weakest possible provenance and which I caught
   making exactly this class of error elsewhere in this lane (§7). **I have left the paper
   in the source table flagged as unestablished and have not used any of its numbers in any
   argument.** It is probably the single best classical citation for "how much of a result is
   carried by low-priced names" and someone with journal access should read it.
4. **The November 2027 compliance date is established from secondary reporting, not from
   the exemptive order.** I verified the 2024 adopting release directly (Release 34-101070,
   518 pages, read). The extension of temporary exemptive relief for Rules 600(b)(89)(i)(F),
   610(c) and 612 to the first business day of November 2027 I took from law-firm and
   trade-press accounts; **I did not read the order itself.** The direction is not in doubt
   and the brief's premise is correct, but the date carries one layer of intermediation.
5. **I cannot sign the net spread-measurement bias for a Regime-B low-price population.**
   Corwin-Schultz understates for small illiquid names (the brief's premise, which I did not
   independently verify); the midpoint effective spread overstates for high-relative-tick
   names (Hagströmer, verified, but on an S&P 500 sample). These run in opposite directions
   in different regimes and I could not find a study that nets them for a microcap
   population. **This matters because `s` is the dominant parameter in §4.2's formula.**
6. **I could not obtain a modern empirical relative-spread-versus-price curve for the $1–$20
   region across the full listed universe.** O'Hara/Saar/Zhong give the conditional answer
   on 120 NYSE names in 2012; the SEC gives bucket averages only above $250. **The
   unconditional curve across NYSE + Nasdaq for 2010–2026 is something I did not find
   published.** It is computable from the programme's own OHLC and would be worth more to
   this decision than any further literature search.
7. **Chen & Zimmermann's magnitude for the price screen alone is in a figure I did not
   read.** Their text establishes the *ranking* ("softest adjustment") verbatim; the size of
   the decline lives in Figure 9, a jitter plot I did not extract. I report the ranking, not
   a number, and the ~60→~40 bp figures quoted are explicitly theirs for the **other three**
   adjustments.
8. **Soebhag et al.'s net Sharpe figures are "maximum net Sharpe ratios by construction
   choice, averaged over factor models"** from their Figure D.4, quoted from their text. I
   did not read the figure, and I did not verify the 0.12/0.18 pair against any other table
   in the paper. Their cost model contains **no per-share commission**, so the result does
   not transfer directly to this programme's cost structure.
9. **Bhardwaj & Brooks (1992) is abstract-only**, and is a 1977–1986 fractional-tick sample.
   I did not read the paper and do not know how it separates price from size.
10. **I make no claim of any kind about this programme's universe, its price distribution,
    how many names lie in any price band, its breadth, its spreads, its turnover, or its
    gross edge.** Every such number in this brief is a parameter handed to me in the
    commissioning brief and used as an input, or is a symbol (`c`, `g`, `s`, `m`, `V`). The
    formula in §4.2 is general; the tables under it are illustrations at the brief's stated
    parameters and are not findings about their book.
