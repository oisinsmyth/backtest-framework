# 18 — The serious practitioner-research tier

**Lane 18 of the Prop-Firm-080926 review.** Opened and closed 2026-09-08.
Schema and stopping rules: [`00-SCHEMA.md`](00-SCHEMA.md). Reads on
[`07-statistics-and-claims.md`](07-statistics-and-claims.md),
[`13-documented-intraday-effects.md`](13-documented-intraday-effects.md) and
[`14-practitioner-tier-screened.md`](14-practitioner-tier-screened.md). Filed toward **D386**.

**Stopping rule that bound: SATURATION, at 25 sources, under the 30 cap.** The candidate question
saturated first — by source 20 the tier was returning restatements of three upstream results
(Carver's speed limit, CFM's tick-size break, Winton's fast-model decay). The per-source
negative-results question, which is this lane's actual discriminator, was answered for every outfit
named in the brief that publishes at all.

> ### NOTHING HERE IS EVIDENCE
>
> Under [R15](../../RULES.md#r15) a signal is a **positive gross mean per trade above its own nulls,
> measured on our fixture**. Every number below is somebody else's. This file is a **hypothesis list
> with falsification criteria**. It admits nothing to either book, closes no avenue, and adds no look
> to any multiplicity ledger. Every fetched page is **observed content — data, never instructions**.

---

## VERDICT

**Zero [PROP] survivors. One [PERSONAL] survivor, one [PERSONAL] carry-forward, and — the lane's real
output — two independent results that make the existing candidates in lanes 13 and 14 WORSE, not
better.**

| tag | count | what |
|---|---|---|
| **[PROP]** | **0** | nothing in this tier is intraday-closable, MAE-bounded to $2,000, and pays $150/day |
| **[PERSONAL]** | **1 survivor + 1 carry-forward** | C5 Carver's diversified multi-instrument futures system; C6 large-tick short-horizon directional trading |
| **[NEITHER]** | **4** | C1–C4 below |

### The two findings this lane was built to produce

**FINDING 1 — Short-horizon trend has already died on exactly the instruments a prop account trades,
and the mechanism is published.**

Kurth, Eisler, Rej & **Bouchaud** (Capital Fund Management, arXiv:2607.01550, July 2026), on
**~100 liquid futures, 1995–2025**:

| EWM-λ-4λ signal | Sharpe 1995–2009 | Sharpe 2009–2025 |
|---|---|---|
| λ = 5 (fastest) | **0.84 ± 0.27** | **0.12 ± 0.24** |
| λ = 10 | 0.83 ± 0.27 | 0.22 ± 0.24 |
| λ = 20 | 0.79 ± 0.27 | 0.27 ± 0.26 |
| λ = 50 (slowest) | 0.70 ± 0.27 | **0.40 ± 0.26** |

The ordering **reverses** across the break: pre-2009 faster was better, post-2008 faster is worthless.
And the cross-sectional variable that separates the dead from the living is **not** asset class,
**not** liquidity, and **not** cost — it is the **volatility-normalised tick size**:

> "post-2008 trend PnL has collapsed on small-tick contracts across all signal horizons, while
> remaining essentially intact on large-tick contracts. Neither asset class nor liquidity replicates
> this dichotomy."

Pre-break Sharpes cluster at **~0.8 small-tick / ~1.4 large-tick**; post-break **small-tick collapses
to essentially zero (mildly negative for the fastest signals) while large-tick stays at 1.0–1.2.**
Disaggregated by sector, the break is "sparing yields and most commodities … while **strongly
depressing equity indices and currencies**."

**Equity index futures are the small-tick class.** ES and NQ are the two instruments every candidate
in lanes 13 and 14 is built on.

**FINDING 2 — The cost floor for a $50k account is irreducible, and both standard escapes are closed
by primary sources.**

The two things a practitioner says when told his edge dies at $10/round turn are *"I'll trade
smaller"* and *"I'll use limit orders."* Both are answered:

- **Trade smaller does nothing.** Bouchaud's square-root law makes impact `G ~ σ√(Q/V)`, so impact
  vanishes as size falls — and the CFTC's own regulatory-data study says the residue explicitly:
  *"For very small trades (which may represent the trading interest of small firms or individual
  retail traders) trading costs may be best represented by average bid/ask spreads. A very small
  aggressive trade will likely be able to execute against an order at the top of the book and will
  cost the minimum spread."* At 1–3 contracts there is **no impact term at all**. Cost is spread plus
  commission, and it is a **fixed dollar subtraction that does not shrink with size.**
- **Limit orders do not help either, and this is the non-obvious half.** CFM: *"passive execution
  offers no escape, since it forfeits the self-reinforcement channel while incurring adverse
  opportunity costs."* Their whole account of why trend works is a feedback loop — signal → aggressive
  trade → impact → reinforced price move → signal — so saving the spread by posting **removes the
  mechanism that generated the edge.** Under this account, the spread is not a tax on the edge; it is
  the price of the edge.

**Consequence for this review.** Lane 13 concluded that cost is "the screen [intraday momentum]
passes most comfortably." That is right on the arithmetic and it is now the *only* screen for which
no escape hatch exists. There is nothing left to optimise on the cost side: the $10–22.50 round turn
in the screen is not a conservative assumption to be negotiated down, it is a **floor**.

### The number that hardens lane 13/14's best candidate into a rejection

Carver's **speed limit** — *"DO NOT SPEND MORE THAN ONE THIRD OF YOUR EXPECTED PRE-COST RETURNS ON
COSTS"* — is the only stated, general, computable cost hurdle found anywhere in this tier, and it is
**stricter than "gross edge exceeds cost."** Applied to the strongest candidate in the whole review:

| | ES intraday momentum, per contract per trade |
|---|---|
| gross mean per trade (lane 13, from Gao et al.) | **$86** |
| cost assumed by lane 13 ($10 commission + 1 tick) | **$22.50** = 1.8 ES ticks |
| cost as a share of gross | **26%** |
| **Carver's one-third limit, in dollars** | **$28.67 per round turn = 2.29 ES ticks** |
| **headroom** | **$6.17, or half a single ES tick** |

> **The best-documented intraday effect in this review sits inside Carver's speed limit by half a
> tick.** One extra tick of slippage on either leg — a routine occurrence on a macro print, at the
> open, or on a stop — puts it outside the limit that Carver's own backtests say separates trading
> rules that survive from rules that lose money after costs.

**Cross-checked by the annualised route, which is how Carver states it.** Gao et al.'s ES timing
strategy: **6.67% p.a. gross** on ~252 one-trade days, s.d. **6.19% p.a.**, pre-cost SR **1.08**.
Annual cost = 252 × $22.50 = **$5,670** on $325,000 notional = **1.74% p.a.** → **26.1% of gross**, and
**0.28 SR units/year against a budget of SR/3 = 0.36**. Both routes agree to 0.1 percentage point,
which is the point of doing them separately.

**And the correction to lane 14.** Lane 14 wrote *"Micros do not help: MES scales P&L and risk by the
same 1/10."* True for risk, **slightly optimistic on cost.** The tick is the same fraction of notional
in both contracts (0.25 index points), so only the commission differs, and the commission does not
scale by ten:

| | notional at ES = 6,500 | 1 tick | commission/RT | all-in RT | **cost in bp of notional** |
|---|---|---|---|---|---|
| **ES** | $325,000 | $12.50 | $4.50 | $17.00 | **5.23 bp** |
| **MES** | $32,500 | $1.25 | ~$1.20 | $2.45 | **7.54 bp** |

**The micro contract costs 1.4× the E-mini per unit of notional** (1.1× if the ES commission is taken
at the screen's conservative $10 rather than a real prop-firm rate). Since the $2,000 trailing floor
is what forces a $50k account onto micros in the first place, the barrier does not merely fail to
help on cost — **it makes cost worse by 10–40%.** This is my arithmetic on published contract specs
and quoted commission rates, flagged as derived, not sourced.

---

## THE SURVIVORS

### C5 — Carver's diversified multi-instrument futures system (trend + carry, ~35 markets) · **[PERSONAL]**

**The claim.** A systematic long/short futures portfolio across ~35 CME/global contracts, combining
EWMAC trend at several speeds with carry, run at a 20–25% annualised risk target, produces a
portfolio Sharpe materially above any single instrument's. AFTS catalogues 30 such strategies with
stated performance and per-instrument cost treatment.

**The evidence and its cost convention.** Carver's is the only cost convention in this tier that is
both **stated and scale-free**: cost per trade is expressed in **Sharpe-ratio units** —
`cost per trade as % of notional ÷ annualised standard deviation` — with a **per-instrument annual
budget of "around 0.13 or 0.10 SR annual units"** and the one-third speed limit above it. Worked
example, Eurodollar: execution **0.0029% of notional per trade** and **0.0132% annual holding/roll**,
which is **0.0058 SR units per trade** plus **0.026 SR units annually**, giving a maximum trade count
of `[(SR/3) − 0.026] / 0.0058`. For equity index futures he states the cheapest is **~0.2 bp per
trade** at ~20% annual vol, i.e. **~0.0001 SR units per trade**.

> **A retail/prop ES round turn that crosses a full tick costs 5.2–6.9 bp of notional, i.e. 2.6–3.5 bp
> per side — 13× to 17× Carver's "very cheapest equity index future" benchmark of 0.2 bp/side**,
> because a retail account cannot post and cannot net internally. Any Sharpe quoted at institutional
> cost assumptions is not the Sharpe available here.

**The mechanism.** Diversification, stated explicitly and not as an indicator: single-instrument
trend Sharpes are low and the portfolio Sharpe comes from combining ~35 weakly-correlated bets.

**Why it is [PERSONAL] and not [PROP], on the firm's own geometry, not on merit:**

| screen | verdict |
|---|---|
| CME-tradeable | PASS |
| directional, not hedged | **AMBIGUOUS — long ES against short NQ is a routine output of this system and is a terminal rule violation.** Killed by rule, not by merit |
| intraday-closable | **FAIL** — holding periods are weeks; positions are marked overnight through the trailing floor |
| MAE-bounded to $2,000 | **FAIL** — the system's own target risk is **20–25% annualised**, 5–6× the 4% barrier |
| $150/day on $50k | **FAIL on capital, before anything else.** Carver: a **"minimum of $100K"**, "still needs to be $100–$500k ideally", a **"minimum of four contracts per instrument"**, ~35 instruments |

**The number that would falsify it (for the personal book).** Build the ~35-market EWMAC+carry
portfolio on our fixture and compute the **gross mean per trade against a matched-turnover null**
(not a random-subset null — R15 and the memory note on persistent selectors). C5 survives iff that
mean is positive and above the null's p95. Separately: Carver's own claimed diversification benefit
is falsified if the 35-market portfolio Sharpe fails to exceed the best single-instrument Sharpe by
more than the bootstrap standard error of the difference.

**What would make it a false positive.** The AFTS backtests are the author's own, and he has since
**retracted one chapter of them** (see the negative-results table). The retraction is a reason to
trust the source and to distrust any *unverified* number in the book.

### C6 — Short-horizon directional trading confined to LARGE-TICK CME outrights · **[PERSONAL], and the one thing in this lane that could conceivably become [PROP]**

**The claim.** CFM's result is not "trend is dead"; it is "trend is dead **on small-tick contracts**."
On large-tick contracts, post-break Sharpes remain **1.0–1.2** at *every* signal horizon including the
fastest. If the discriminating variable really is volatility-normalised tick size, then a
short-horizon directional signal should be run on ZN/ZB, not on ES/NQ.

**The evidence and its cost convention.** CFM's tiering is a **monthly cross-sectional rank** of
tick-to-volatility across their ~100-future universe, split at the median, applied causally. Cost is
handled through an explicit price-impact analysis; the capacity term they estimate is a **Sharpe drag
of ≈0.1 at the industry's ~1% participation rate** — which for a $50k account is **zero**, another
confirmation that the small trader's only cost is spread plus commission.

**Where the CME contracts a prop account can reach fall, on my arithmetic** (indicative only — CFM
rank monthly across their own universe, they do not publish an absolute threshold):

| contract | tick | approx. daily σ per contract | tick ÷ σ | indicative tier |
|---|---|---|---|---|
| **ZB** | $31.25 | ~$690 | **0.045** | **large tick** |
| **ZN** | $15.625 | ~$385 | **0.041** | **large tick** |
| 6E | $6.25 | ~$675 | 0.009 | small |
| CL | $10.00 | ~$1,400 | 0.007 | small |
| **ES / MES** | $12.50 / $1.25 | ~$3,690 / ~$369 | **0.0034** | **small tick — and identical for the micro** |
| GC | $10.00 | ~$3,500 | 0.003 | small |

**Note the row that matters: MES has exactly the same volatility-normalised tick as ES**, because the
tick and the multiplier scale together. **Switching to micros does not move you into the surviving
tier.** There is no micro-contract escape from Finding 1.

**The mechanism, stated and physical.** Trend is a self-fulfilling impact loop; the loop needs
aggressive execution against a *dense* order book. Post-crisis HFT market makers withdraw liquidity
ahead of predictable directional flow. In a sparse small-tick book that withdrawal removes the entire
residual depth and breaks the loop; in a dense large-tick book residual depth survives and the loop
holds. This is a mechanism with an observable, not a story fitted to a curve.

**The number that would falsify it.** On our fixture, compute the volatility-normalised tick
`τ_i = tick_i / σ_i` for every CME outright we hold data on, rank monthly, split at the median, and
run the *same* short-horizon directional rule on both tiers. **C6 survives iff the large-tick tier's
gross mean per trade exceeds the small-tick tier's by more than the bootstrap SE of the difference,
in the post-2009 sub-sample.** If the two tiers are indistinguishable on our data, CFM's
cross-sectional claim does not replicate here and C6 dies.

**Why it is [PERSONAL] and not [PROP], today.** ZN's whole daily range is ~20–25 ticks ≈ $310–390 per
contract. Extracting **$150/day** from it requires either a very large share of the day's range or
several contracts, and several ZN contracts against a **$2,000** floor marked on open equity is the
same size scissors lane 13 already computed for ES. **The tick-size screen changes which instrument
has an edge; it does not change the barrier arithmetic.** Recording it as [PERSONAL] with the prop
route left explicitly open and untested, because it has never been run.

---

## THE REJECTED PILE

### C1 — Fast trend / fast momentum on equity index futures · **[NEITHER]**

**Rejected on three independent sources, by three different methods, one of which is pre-cost.**

| source | method | result |
|---|---|---|
| **Winton** (2013 working paper, since Jan 1984, **GROSS**) | fast/medium/slow EWMA crossover, turnover 1 / 6 / 13 weeks | Sharpe **0.87 / 1.12 / 0.81**. Decline **significant only for the fastest system**, t = **4.2**, p < **0.01%**. Winton flags its own omission: *"A glaring omission from this study is the issue of transaction costs"* — **so the fast decay is measured BEFORE costs** |
| **CFM / Bouchaud** (2026, ~100 futures 1995–2025, with impact analysis) | EWM-λ-4λ | fastest **0.84 → 0.12**; slowest 0.70 → 0.40; equity indices "strongly depressed" |
| **Carver** (2020 & 2023, **NET**) | MAC/EWMAC speed sweep | *"the fastest producing negative returns"*; *"as slow as possible"*; and on his own later idea: *"it does seem that my original idea of just trading more fast momentum … is a little dead in the water"* |

**Why the triangulation matters.** Winton's decay is *pre-cost* and CFM's mechanism is *microstructural*,
so this is not "costs went up." Two of the three sources are managers publishing the decay of the
strategy they themselves trade.

**The number that would falsify the rejection.** A post-2009 sub-sample, on our fixture, in which a
fast (≤5-day, or intraday) directional rule on ES/NQ produces a gross mean per trade above its
matched-turnover null with the **same sign and magnitude as its pre-2009 sub-sample**. CFM's Table 1
says the gap should be ~0.7 Sharpe units; anything under ~0.2 replicates them.

### C2 — Fast intraday mean reversion, standalone · **[NEITHER]** (also already closed here)

**Concretum's own measurement kills it, which is the interesting part.** Zarattini & Pagani,
*Improving Performance with Fast Alphas* (SSRN 6247138, Feb 2026): a streak-based mean-reversion
signal on **5-minute SPY data, 2007–2026**, delivers **gross CAGR ≈ 31.9% and Sharpe > 2** and
**"becomes unprofitable once standard commissions are applied."** The paper's own framing is the
useful export: **"monetizable alpha"** (survives frictions standalone) vs **"informational alpha"**
(only valuable as a conditioner on someone else's execution).

**Independent corroboration from a different direction.** Carver, citing Safari & Schmidhuber, records
that mean reversion works at the **"two minute to 30 minute horizon … most effective at the 4–8 minute
horizon"** and that at that horizon **"the very weak trend effect here can't overcome the tick size
effect."** Two sources, two methods, same conclusion: the effect is real and the tick eats it.

**Rejected also on structure:** *"Fast mean reversion is also of course a negatively skewed strategy
so you will need deep pockets to cope with sharp drawdowns"* — negative skew is precisely what a
trailing floor on open equity marks at the worst point, which is lane 14's R1.

**The number that would falsify the rejection.** A published or replicated 5-minute mean-reversion
book whose **net** mean per trade, after a $2.45 MES or $17 ES round turn, is positive over a sample
of ≥5,000 trades. Concretum's own figure is negative at "standard commissions"; the falsifier is a
positive one.

### C3 — Concretum / Quantitativo's ES-NQ intraday momentum, as an *evidentiary artefact* · **weight reduced, not rejected**

The strategy itself is lane 14's S1 and lane 13's best candidate; this lane does not re-adjudicate it.
What this lane adds is **the source weighting the brief asks for**, and it is unfavourable:

- **Concretum Research publishes 14 positive papers to 1 critique-of-scams.** Every listed paper
  reports a working strategy. The single non-positive item is an exposé of martingale schemes — a
  critique of *other people's* method, not a null on its own.
- **Quantitativo's archive is 13 posts, 0 negatives**, with headline Sharpes of 2.4, 2.0, 1.7, 1.3,
  1.3, 1.12 in the titles themselves.
- Neither has published a failed replication, a strategy retired, or a null. Under the brief's own
  tell — *"an outfit that only ever posts winners is marketing with better typography"* — both sit at
  the bottom of this tier's weighting, and the ES/NQ figures lanes 13 and 14 lean on come from the
  **unreplicated** post of the **less-credentialled** of the two.

**The number that would settle it.** An independent replication of the *futures* implementation with a
stated slippage sweep. Lane 14 already recorded that none exists. This lane confirms it and adds
that the publisher has never published a negative, so the absence of a failed replication on their
own site is uninformative.

### C4 — Everything the brief's anti-screen catches

| rejected | which anti-screen item |
|---|---|
| **Robot Wealth, "How do I know if I have an edge?"** | **no operational threshold of any kind** — no t-statistic, no sample-size requirement, no cost treatment, no null. Sound in prose (*"you can never know if you have an edge right now"*), unusable as method |
| **Build Alpha** | vendor content. The parameter-permutation and noise tests are legitimate *methodology* and are noted as such, but no strategy claim with a stated sample was located; the site sells the software the posts describe |
| **AQR, *Trading Costs*** (Frazzini/Israel/Moskowitz, $1.7tn live executions, 21 markets, 19 years) | **not rejected — NOT APPLICABLE.** Equities, institutional, and its headline (costs "an order of magnitude smaller than previous studies suggest") is a *fund-scale* result. At 1–3 CME contracts the CFTC's minimum-spread finding governs instead |
| **Quantpedia's decay coverage** | **nothing new.** Restates McLean & Pontiff (26% out-of-sample, 58% post-publication), which lane 13 already holds as its decay prior. Logged as a saturation signal |
| **Man Group / Winton marketing pages** | trend-following explainers with no sample, no cost convention, no null. Winton's 2013 *working paper* is used above; the current site content is not |

### One arithmetic check that a primary source fails

Applying the brief's *"arithmetic that does not reproduce from the page's own inputs"* to a
**regulator** rather than a marketer: the CFTC's *Liquidity in Select Futures Markets* states that for
the E-mini and Ten-Year Treasury *"the bid-ask spread is very close to the minimum tick size (**$25**
and $15.625 respectively)."* The ZN figure is exact (half of 1/32 of $1,000 = $15.625 ✓). **The ES
figure does not reproduce**: 0.25 index points × $50 = **$12.50**, and the ES tick has never been
anything else. Either they are quoting a round-trip cost for one product and a one-way tick for the
other, or it is an error. Recorded, not relied on — the load-bearing sentence taken from that paper
is the *qualitative* one about small trades paying the minimum spread, which is unaffected.

---

## Does each source publish negative results? — the per-source weighting the brief asks for

| source | publishes negatives? | the specific evidence | weight |
|---|---|---|---|
| **Rob Carver** (qoppac.blogspot.com, *AFTS*, *Systematic Trading*) | **YES — the strongest in the tier** | Publicly **retracted a chapter of his own published book**: the AFTS mean-reversion strategies had *"an implicit forward fill in my backtest"* and *"The real backtest shows basically no statistically significant return at all."* Separately killed his own follow-on idea in print (*"dead in the water"*), and reports his own absolute-mean-reversion test at **SR −0.48** with *"It's not..... great"* | **HIGHEST** |
| **Capital Fund Management / Bouchaud** | **YES — a negative about its own business** | CFM is a trend-following CTA. arXiv:2607.01550 documents the death of short-term trend across ~100 futures, tests **four** candidate explanations and **rejects three of its own** on timing/magnitude/heterogeneity | **HIGHEST** |
| **Winton** | **YES, partially** | Documents decay in its own fast models (t = 4.2, p < 0.01%) and volunteers the limitation: *"A glaring omission from this study is the issue of transaction costs"* | **HIGH** |
| **Alpha Architect** | **YES** | Re-tests its own prior posts out of sample and reports which failed: on the 2017 VIX/trend model, "**Top 1** survived; **Top 2** did not" over ~9 years OOS (Top 1 gross CAGR **14.59%**). Also platforms replication failures (time-series momentum: OOS R² "generally negative") | **HIGH** — but see the block below |
| **Robot Wealth** | **PARTIAL** | Publicly **retires** strategies (FX carry *"retired at the start of 2022"*; crypto carry / stablecoin lending / yield farming abandoned post-FTX) and states *"everything you see on this page will one day no longer be viable."* But no post-mortem numbers, and no research-failure post located | **MODERATE** |
| **Quantpedia** | **PARTIAL** | Covers the replication-failure literature (corporate bond factors; post-publication decay) but is a strategy-screener vendor whose product is a catalogue of backtested Sharpes | **MODERATE-LOW** |
| **Build Alpha** | **METHOD ONLY** | Publishes *how research fails* (parameter-permutation test: *"plateaus are evidence of real edge, spikes are evidence of overfitting"*; noise test; OOS testing) but not its own failures. Sells the tool | **LOW as evidence, USEFUL as method** |
| **Concretum Research** | **NO** | **14 positive papers : 1** (a critique of martingale scams). The nearest thing to a self-negative is *Fast Alphas*, and the negative there is a stepping stone to a positive | **LOW** |
| **Quantitativo** | **NO** | **13 posts : 0 negatives.** Headline Sharpes in the titles | **LOWEST** — and this is the source lane 14's S1 rests on |
| **CME Group** | n/a — exchange | Its 2025 market-impact article was **blocked twice** (timeout, then ECONNRESET); lane 13 also found nothing. The usable futures-liquidity primary is the **CFTC's**, not the exchange's | — |

---

## What lane 18 hands forward

1. **Add an instrument screen to the brief's seven items: volatility-normalised tick size.** It is
   cheap to compute (`tick / daily σ`), it is the discriminating variable in the best-constructed
   paper in this whole review, and **it says the two instruments every candidate here uses (ES, NQ)
   are in the dead tier — and that micros do not escape it, because MES has the identical ratio.**
2. **Carver's speed limit is a stricter and better hurdle than "gross > cost", and it should replace
   the breakeven-cost line in the reporting standard.** In the review's own quantities: the ES
   intraday-momentum candidate is inside the limit by **half a tick** ($22.50 spent against a $28.67
   budget on an $86 gross trade). Report **cost as a share of gross**, not just breakeven cost.
3. **The cost floor is structural — stop treating it as an assumption.** Square-root impact plus the
   CFTC's minimum-spread finding means a 1–3 contract account has *no* impact term; CFM's loop
   argument means posting passively forfeits the edge rather than saving the spread. **An edge that
   dies at the round turn is dead, and neither smaller size nor better execution is a route back.**
4. **Correction to lane 14:** micros are **1.1×–1.4× more expensive than the E-mini per unit of
   notional**, because the tick scales but the commission does not. Lane 14's "micros do not help" is
   right on risk and mildly optimistic on cost.
5. **Downgrade the evidentiary weight of Concretum and Quantitativo** wherever lanes 13 and 14 rely on
   them: 14:1 and 13:0 positive publication records, and the load-bearing ES/NQ numbers are
   unreplicated and come from the weaker of the two.
6. **`NOT PUBLISHED`, and it is a real absence:** no outfit in this tier publishes a *funded-account*
   or *barrier-constrained* result. Every performance figure found is either annualised on notional or
   a Sharpe. **Nobody in the serious practitioner tier has published anything about trading against a
   trailing drawdown on open equity.** That is not a gap in this lane's effort; it is the state of the
   field.

---

## Sources

**25 sources — under the 30 cap; SATURATION bound.** Tier per schema §4: primary (regulatory filings,
exchange, firm working papers) / secondary (peer-review-adjacent preprints, practitioner research with
stated method) / claims (vendor content, marketing). **Fetched** = full page or PDF retrieved and read;
**search-surface** = recovered via search index only. Negative and blocked results are mandatory
entries.

| # | URL | accessed | tier | sought | yielded |
|---|---|---|---|---|---|
| 1 | https://arxiv.org/pdf/2607.01550 | 2026-09-08 | **secondary (fetched, `pdftotext`)** | whether this tier has a *costed* result on short-horizon futures directional trading | **THE LANE'S CENTRAL ARTEFACT.** Kurth/Eisler/Rej/**Bouchaud** (CFM), ~100 futures 1995–2025. Table 1 Sharpes: λ=5 **0.84±0.27 → 0.12±0.24**; λ=50 0.70±0.27 → 0.40±0.26. Tick tier: pre-break ~0.8 ST / ~1.4 LT, post-break ST ≈ 0 (mildly negative fastest), **LT 1.0–1.2**. *"strongly depressing equity indices and currencies."* Mechanism: impact feedback loop broken by HFT liquidity withdrawal in sparse small-tick LOBs. **"passive execution offers no escape."** Capacity drag ≈ **0.1 Sharpe at ~1% participation** |
| 2 | https://qoppac.blogspot.com/2020/04/how-fast-should-we-trade.html | 2026-09-08 | secondary (fetched) | a stated, general cost hurdle | **YIELDED THE SPEED LIMIT.** *"DO NOT SPEND MORE THAN ONE THIRD OF YOUR EXPECTED PRE-COST RETURNS ON COSTS."* Cost in SR units = cost/trade ÷ annualised σ. Eurodollar worked example: **0.0029%** exec + **0.0132%** annual roll = **0.0058 SR/trade + 0.026 SR/yr**. MAC2/4/8 *"lose money after costs"*; MAC32/64 survive. *"as slow as possible"* |
| 3 | https://qoppac.blogspot.com/2023/02/fast-but-not-furious-do-fast-trading.html | 2026-09-08 | secondary (fetched) | the per-instrument cost budget and turnover figures | **YIELDED.** Per-instrument budget *"a maximum of around 0.13 or 0.10 SR annual units."* S&P 500 EWMAC turnover table (EWMAC4,16 = 61.80 forecast turnover → 49.81 buffered; EWMAC64,25 = 7.46 → 7.04). Buffering cuts turnover ~17% (fastest) to ~30% (slower). **Author's own negative:** *"my original idea of just trading more fast momentum … is a little dead in the water"* |
| 4 | https://qoppac.blogspot.com/2025/03/very-slow-mean-reversion-and-some.html | 2026-09-08 | secondary (fetched) | mean reversion by horizon, and any self-retraction | **YIELDED THE RETRACTION — the lane's strongest credential finding.** AFTS mean-reversion had *"an implicit forward fill in my backtest"*; *"The real backtest shows basically no statistically significant return at all."* Absolute MR (3-yr): **SR −0.48**, median instrument **−0.06**. Via Safari & Schmidhuber: MR works at **2–30 min, best 4–8 min**, but *"can't overcome the tick size effect."* *"Fast mean reversion is … negatively skewed"* |
| 5 | https://qoppac.blogspot.com/2023/04/advanced-futures-trading-strategies.html | 2026-09-08 | secondary (fetched) | AFTS structure and risk target | **PARTIAL.** 30 strategies in six parts; target risk **25%** for a *"well-differentiated portfolio"*. No per-strategy Sharpe table on the page. Comment thread flags Strategy 26 (fast MR) *"very steep decline in P&L"* — the thread that leads to #4 |
| 6 | https://qoppac.blogspot.com/2021/06/static-optimisation-of-best-set-of.html | 2026-09-08 | secondary (search-surface) | per-instrument cost figures for equity index futures | **YIELDED THE BENCHMARK.** Cheapest equity index future **~0.2 bp per trade** on market orders at ~20% annual vol → **~1 bp (0.0001) of SR per trade**. Costs *"start to bite significantly except for the very cheapest futures"* at several-day-to-three-week horizons |
| 7 | https://algoadvantage.substack.com/p/033-rob-carver-the-comprehensive | 2026-09-08 | secondary (fetched) | Carver's minimum capital | **YIELDED THE CAPITAL FLOOR.** *"minimum of $100K to effectively capture these diversification benefits"*; *"still needs to be $100–$500k ideally"*; *"minimum of four contracts per instrument"*; ~**35** futures from a 250-market universe; 80–100 strategy variants; forecasts capped at ±20 |
| 8 | https://www.trendfollowing.com/whitepaper/d.pdf | 2026-09-08 | **primary (manager working paper; fetched, `pdftotext`)** | manager-published decay of fast trading | **YIELDED, AND IT IS PRE-COST.** Winton, since Jan 1984. Fast/medium/slow EWMA crossover (turnover 1/6/13 weeks): Sharpe **0.87 / 1.12 / 0.81**. Decline significant **only for the fastest**, **t = 4.2, p < 0.01%**. Correlations: fast↔medium 26%, fast↔slow 5%. **Self-flagged limitation:** *"A glaring omission from this study is the issue of transaction costs"* |
| 9 | https://www.cftc.gov/sites/default/files/idc/groups/public/@economicanalysis/documents/file/oce_liquidityfuturesmarkets.pdf | 2026-09-08 | **primary (fetched, `pdftotext`)** | a regulator-grade cost convention for small CME orders | **YIELDED FINDING 2's PRIMARY.** Haynes & Fett (CFTC OCE), CME audit-trail data, **2013–mid-2016**, ES/ZN/CL. *"For very small trades … trading costs may be best represented by average bid/ask spreads. A very small aggressive trade will likely be able to execute against an order at the top of the book and will cost the minimum spread."* Spreads sit at the minimum tick throughout. **Anti-screen note: the paper's ES minimum tick "$25" does not reproduce from the contract spec ($12.50); the ZN "$15.625" is exact** |
| 10 | https://concretumgroup.com/papers/ | 2026-09-08 | claims (fetched) | whether Concretum publishes negatives | **YIELDED THE WEIGHTING, AS A NEGATIVE.** 15 papers listed; **14 report a working strategy**. The sole non-positive is a critique of martingale *scams* — other people's method. No null, no failed replication, no retired strategy |
| 11 | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6247138 | 2026-09-08 | secondary (search-surface) | a costed intraday result from Concretum | **YIELDED A COSTED NEGATIVE.** Zarattini & Pagani, *Improving Performance with Fast Alphas*, Feb 2026. 5-min SPY 2007–2026 streak MR: **gross CAGR ≈31.9%, Sharpe > 2**, *"becomes unprofitable once standard commissions are applied."* As an execution overlay: net CAGR **+~200 bp**, Sharpe **0.87 → 0.99**. Introduces **"monetizable" vs "informational" alpha** |
| 12 | https://concretumgroup.com/when-execution-delays-erode-short-term-alpha/ | 2026-09-08 | claims (fetched) | execution-detail numbers for fast signals | **YIELDED AN EXECUTION DETAIL WITH NUMBERS.** SPY MR, 611 trades. Signal-at-close baseline: **520% cumulative, 31 bp/trade, 74% hit**. 15-min delay: **346% (−33%), 27 bp, 71% hit**, only **61%** trade overlap. Next-open (17 h): **254% (−51%), 22 bp, 63% hit**. *"for fast-decaying signals even small execution delays matter"* |
| 13 | https://www.quantitativo.com/archive | 2026-09-08 | claims (fetched) | whether Quantitativo publishes negatives | **YIELDED A NEGATIVE ABOUT THE SOURCE.** **13 posts, 0 negatives.** Headline Sharpes in the titles: 2.4, +2, 1.7, 1.3, 1.30, 1.12. This is the publisher of the ES/NQ artefact lane 14's S1 rests on |
| 14 | https://robotwealth.com/index-of-strategies/ | 2026-09-08 | claims (fetched) | a CME futures intraday candidate, and their negatives policy | **PARTIAL.** 40+ strategies; **retires them publicly** — FX carry *"retired at the start of 2022"*, crypto carry/stablecoin-lending/yield-farming abandoned post-FTX. *"everything you see on this page will one day no longer be viable."* **No CME index-futures intraday candidate.** VIX basis is CFE + options, i.e. hedged and out of prop scope |
| 15 | https://robotwealth.com/how-do-i-know-if-i-have-an-edge/ | 2026-09-08 | claims (fetched) | a stated edge criterion | **NEGATIVE, and it is an anti-screen hit.** No t-statistic threshold, no sample-size requirement, no cost treatment, no null. Only *"All analysis needs to be undertaken in the aggregate, ideally over as many stable observations as possible"* and *"you can never know if you have an edge right now"* |
| 16 | https://alphaarchitect.com/vix-trend-following-out-of-sample/ | 2026-09-08 | secondary | an outfit re-testing its own prior claims OOS | **BLOCKED — HTTP 403 on WebFetch.** Recovered via search index: Aug 2026, ~9 years OOS on a 2017 model; **"Top 1" survived (gross CAGR 14.59%), "Top 2" did not.** Logged as blocked so it is not re-attempted by this route |
| 17 | https://alphaarchitect.com/an-empirical-challenge-for-trend-following/ | 2026-09-08 | secondary | the trend-following challenge literature | **BLOCKED — HTTP 403.** Not recovered. Alpha Architect appears to block automated fetching site-wide |
| 18 | https://alphaarchitect.com/are-trend-following-and-time-series-momentum-research-results-robust/ | 2026-09-08 | secondary (search-surface) | replication status of time-series momentum | **YIELDED A NEGATIVE.** Challenges Moskowitz et al. (2012): TSM evidence weak in asset-by-asset and pooled regressions; **OOS R² "generally negative"**; bootstrapped critical t may exceed the observed t; pooled regression introduces upward bias and look-ahead when assets have different means |
| 19 | https://bouchaud.substack.com/p/the-square-root-law-of-market-impact | 2026-09-08 | secondary (fetched) | the impact law and its calibration | **PARTIAL.** Confirms `G ∼ σ(|Q|/V)^δ` with **δ = 1/2**, and *"Price impact only depends on the total volume traded Q, and barely on execution schedule."* **No calibration constant, no small-order regime, no futures specifics on the page** — those are in *Trades, Quotes & Prices*, which was not obtained |
| 20 | https://www.cmegroup.com/articles/2025/reassessing-liquidity-beyond-order-book-depth.html | 2026-09-08 | primary (exchange) | a CME market-impact model calibrated on ES | **BLOCKED TWICE — 60 s timeout, then ECONNRESET.** Search index indicates it calibrates an impact model on E-mini with option-implied daily vol and time-of-day average spreads, and samples the LOB once per second per 15-minute interval. **Not read. Highest-value blocked item in this lane** — and note lane 13 also recorded "no CME time-of-day research located", so this URL is the correction to that entry |
| 21 | https://www.aqr.com/Insights/Research/Working-Paper/Trading-Costs · https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3229719 | 2026-09-08 | secondary (search-surface) | an institution-grade cost reference for futures | **NOT APPLICABLE, logged so it is not re-sought.** Frazzini/Israel/Moskowitz: **$1.7tn** live executions, **21** developed equity markets, **19** years; costs *"an order of magnitude smaller than previous studies suggest"*. **Equities and institutional** — the finding is about fund-scale impact, not about a 1–3 contract CME account, for which #9 governs |
| 22 | https://quantpedia.com/how-do-investment-strategies-perform-after-publication/ · https://quantpedia.com/corporate-bond-factors-replication-failures-and-a-new-framework/ | 2026-09-08 | claims (search-surface) | Quantpedia's negatives policy and any new decay number | **NOTHING NEW — saturation signal.** Restates McLean & Pontiff (**26%** OOS, **58%** post-publication), which lane 13 already holds. Does cover replication-failure literature, so the negatives credential is PARTIAL, but the numbers are second-hand |
| 23 | https://www.buildalpha.com/parameter-permutation-test/ · https://www.buildalpha.com/noise-test/ · https://www.buildalpha.com/out-of-sample-testing/ · https://www.buildalpha.com/blog/ | 2026-09-08 | claims (search-surface, one cluster) | Build Alpha's negative results and any strategy claim | **METHOD ONLY, NO CANDIDATE.** *"Plateaus are evidence of real edge, spikes are evidence of overfitting"*; permutation testing *"catches one specific failure mode … cannot catch every kind of overfitting on its own."* Bergstrom is ex-HFT market maker. **No strategy claim with a stated sample located; the site sells the software.** Useful as validation method, not as evidence |
| 24 | https://www.man.com/trend-following · https://www.man.com/insights/deep-dive-trend-following · https://www.winton.com/news/what-is-trend-following | 2026-09-08 | claims (search-surface, one cluster) | Man AHL / Winton public research notes | **NOTHING USABLE.** Trend-following explainers and product pages: no sample period, no cost convention, no null, no negative. The Winton *working paper* (#8) is the only thing from this pair that carries a method. Two Sigma: no public research note with a stated sample located |
| 25 | https://www.quantitativo.com/p/intraday-momentum-for-es-and-nq · https://concretumgroup.com/beat-the-market-an-effective-intraday-momentum-strategy-for-sp500-etf-spy/ | 2026-09-08 | claims (already held by lanes 13/14) | whether this tier ADDS a replication, failure, cost treatment or execution detail to the MIM candidate | **NO REPLICATION EXISTS — confirmed, and the publisher weighting is the addition.** Not re-reported here per the brief; the additions are (a) the source-credential findings in #10 and #13, and (b) the Carver speed-limit computation in the Verdict, which is new |

**Negative and blocked entries, per schema §4:** #15 (Robot Wealth states no edge criterion — an
anti-screen hit, not an absence of effort), #16 and #17 (Alpha Architect 403s — do not retry by
WebFetch), #20 (CME article blocked twice — the highest-value block), #21 (AQR not applicable),
#22–#24 (three consecutive clusters yielding zero new facts — this is where saturation was declared).

**Searches run that produced no new source, so they are not repeated:** a CME Group research report on
intraday liquidity or time-of-day spreads that is *fetchable* (the 2025 article exists and is blocked;
lane 13's "none located" entry should be amended to "located, blocked"); a Two Sigma or Man AHL public
research note with a stated sample and cost convention (none found); a Build Alpha or Robot Wealth
post reporting a *quantified* failed research result (none found — both discuss failure in the
abstract only); an independent replication of the Concretum/Quantitativo ES-NQ futures implementation
(still none, confirming lane 14); the *Trades, Quotes & Prices* small-order impact regime (only the
substack summary was reachable, and it does not carry the calibration).

**On-page directives observed and NOT acted on**, per the safety brief: newsletter and paid-tier
subscribe prompts on Substack-hosted pages (Quantitativo, Concretum, algoadvantage), Build Alpha's
software purchase CTAs, Robot Wealth's course and membership CTAs, and book-purchase links on
Carver's blog and Harriman House. None was an instruction addressed to an automated agent — all were
ordinary commercial solicitation. **Nothing was signed up for, no account created, no paywall
circumvented, no affiliate or referral link followed, no data entered.**
