# Alpha Programme: Mechanism-First Research for a Futures Book

**Status:** working document
**Scope:** how alpha is generated, validated, and turned into a strategy in this project
**Companions:**
- `FEATURE_RESEARCH.md` — how a feature is evaluated (IC, decay, CPCV, trial budget)
- `DATA_EXPANSION_PLAN.md` — what data exists and how it is ingested
- `HEDGING_FLOW_DERIVATION.md` — the worked derivation this document generalises from
- `READING_LIST.md` — sources, and the filter for judging them

This document covers the part the others assume: **where candidate alphas come from, and
what happens to one after it survives evaluation.**

---

## 1. The problem statement

Infrastructure is not the bottleneck. Framework quality is not the bottleneck. Alpha is.

Everything else in a systematic programme generalises — a backtester works on any strategy,
an evaluation harness works on any feature. Alpha does not generalise, cannot be bought,
and decays after discovery. It is also the only part where the search space is effectively
infinite and the base rate of success is close to zero.

Two structural facts follow, and they drive the rest of this document:

1. **The search space must be constrained by something other than the data**, because the
   data cannot support an unconstrained search (see §4 of `FEATURE_RESEARCH.md`: 1,000
   configurations returns a ~1.2 Sharpe from pure noise on a 10-year sample).
2. **The constraint that works is mechanism.** Not intuition, not aesthetics, not
   backtested performance — an argument about why someone is trading at a price they do
   not like.

---

## 2. The mechanism filter

> **If you cannot name the counterparty and the constraint that forces them to trade at a
> price they do not like, do not test it.**

This is a prior, and it is the only thing that makes the search tractable. It should kill
most candidates before they cost a trial. Write the mechanism into the pre-registration in
one or two sentences; if it cannot be written, that is the answer.

### 2.1 Categories that survive

| Category | Who trades badly, and why | Examples |
|---|---|---|
| **Forced flow** | Mandate or contract requires the trade regardless of price | Index rolls, ETF creation/redemption, margin-driven deleveraging, leveraged-ETF rebalancing, covenant-driven hedging |
| **Risk premia** | Compensation for holding something uncomfortable | Carry / roll yield, hedging pressure, volatility risk premium |
| **Slow diffusion** | Information propagates at finite speed | Time-series momentum, cross-sectional momentum, lead-lag, PEAD |
| **Liquidity provision** | Paid to absorb impatience | Short-horizon reversal, order-flow imbalance, post-liquidation reversal |
| **Positioning / sentiment** | Crowding creates fragility | COT extremes, speculator reversal |

Highest quality is **forced flow**, because the constraint is public and the counterparty is
price-insensitive by mandate. You are not claiming to know more than them — you are being
paid to take the other side of something they must do.

### 2.2 Categories to distrust by default

Chart patterns, indicator crossovers, anything justified by a picture. Price is the most
heavily mined dataset in existence. Time-series momentum and short-horizon reversal are the
real survivors from that family; both are published, low-Sharpe, and capacity-constrained.

### 2.3 The corollary about information

You are structurally the **least-informed** participant on fundamentals. Cargill, Glencore,
Vitol and Trafigura own the physical assets and buy satellite imagery of tank tops. Any
strategy premised on knowing more than them fails the mechanism filter in reverse: the
counterparty is better informed and has no constraint forcing them to trade badly.

**You cannot win on fundamental information. You can win on fundamental structure.**

---

## 3. Fundamental analysis in a futures context

There are no balance sheets. "Fundamental" means physical supply and demand: inventories,
production, capacity, refinery runs, weather, crop conditions — and for financials, real
rates and policy paths.

### 3.1 The term structure *is* the fundamental measurement

Theory of storage: low inventories → convenience yield → backwardation; abundant
inventories → storage cost → contango. The front-to-next spread is therefore a
market-aggregated summary of the inventory situation, priced by everyone who actually knows
what is in the tanks.

| | Raw fundamental data | Term structure |
|---|---|---|
| Frequency | Weekly / monthly | Daily |
| Revisions | Substantial | None |
| Release lag | Days to weeks | Real-time |
| Point-in-time integrity | Hard and costly | Trivial |
| Observations per 10y | 120–520 | ~2,500 |

This is why carry is the most robust documented futures effect, and why the highest-quality
fundamental signal available to a small operation is the curve rather than the data behind it.

### 3.2 Where raw fundamental data still adds something

- **Processing spreads** (crack, crush, spark) — physical margin relationships computable
  entirely from futures prices. Real mechanism, no external data, daily frequency.
- **Inventory surprise**, not level. Requires a consensus series to difference against.
- **Seasonality with a physical mechanism** — heating degree days, harvest pressure. Easiest
  thing in this document to overfit: 10 years is 10 observations of an annual cycle.
- **Macro nowcasting** for financials. Legitimate, long-horizon, heavily contested.

### 3.3 Point-in-time discipline

USDA and EIA both revise. Pulling current series and stamping them with reference dates is
lookahead and will produce a spectacular fake result. **Use ALFRED, not FRED** — the vintage
archive stores every release as originally published with its publication date. This is free
and non-optional.

---

## 4. The worked case: hedging pressure

Producers are structurally short their output and pay to be — not because they are wrong,
but because covenants and policy require the hedge regardless of price. The trade is not
"I know more about crude inventories than Vitol." It is "Vitol is required to hedge and I am
being paid to take the other side."

Documented back to Keynes on normal backwardation. Available to someone with no physical
information whatsoever.

### 4.1 Measurement

Company financials are the *wrong* instrument for measuring this, and understanding why
generalises:

| | Company financials | COT commercials |
|---|---|---|
| Frequency | Quarterly | Weekly |
| Lag | 60–90 days | 3 days |
| Coverage | Listed firms only | Whole market |
| Cost | Subscription | Free |
| History | Varies | 1986 (legacy), 2006–09 (disaggregated) |
| Effective obs / 10y | ~40 | ~520 |

**Use disaggregated COT, not legacy.** The legacy "Commercial" category lumps swap dealers in
with genuine end-user hedgers. Disaggregated separates Producer/Merchant/Processor/User from
Swap Dealers, Managed Money and Other Reportables.

**Critical measurement detail:** producers hedge OTC with their lending banks, who lay off in
futures. The flow therefore surfaces in **Swap Dealer** shorts, not Producer/Merchant. Reading
only the P/M line misses most of it. This is the first thing to verify.

### 4.2 Where financials *do* earn their place

As the **denominator**. COT gives a position in contracts; it does not tell you what fraction
of hedgeable exposure that represents. Filings give production volumes and policy ceilings:

```
hedge_saturation = commercial_net_position / estimated_sector_hedgeable_volume
```

Hedging demand is **bounded** — you cannot hedge more than 100% of output. Saturation
therefore measures **latent flow still to come**. Near the ceiling, pressure is spent and
rallies stop getting sold. Near the floor, a large pool of mandated selling waits for a
price trigger.

The filing lag that disqualifies financials as a signal is irrelevant here: production
capacity changes slowly, so an annual figure is fine for a structural constant.

---

## 5. Deriving instead of fitting

The full derivation is in `HEDGING_FLOW_DERIVATION.md`. What generalises is the *method*.

### 5.1 The principle

A derived constraint costs no sample. A fitted parameter does. So push as much of the model
as possible into the derived part, and spend the trial budget only on what remains.

This is system identification: a plant with known structure and unknown parameters, where you
estimate the parameters rather than fitting a black box to input-output data.

### 5.2 The semi-parametric structure

| Component | Source | Trial cost |
|---|---|---|
| Flow magnitude, timing, direction, bounds | Published mechanics | **Zero** |
| Functional shape of impact | Theory (square-root law) | **Zero** |
| Impact coefficient, behavioural slope | Estimated | 1–2 parameters |

A three-parameter model with derived structure is a completely different statistical object
from a three-parameter model chosen by sweep, because the structure came from outside the data.

### 5.3 What is derivable, ranked

| Mechanism | Derivability | Residual estimation |
|---|---|---|
| Leveraged ETF rebalance | Almost fully | Impact only |
| Index roll flow | Mostly (AUM estimated) | Impact, anticipation |
| ETF creation / redemption | Mostly | Impact |
| Carry / roll yield | Definitional | None |
| Expiry and delivery mechanics | Fully | Impact |
| Producer hedging | Shape only | Level, thresholds |
| Margin-driven deleveraging | Partially | Trigger distribution |
| Consumer hedging | Weakly | Most of it |

### 5.4 The hard line

**You can derive the constraint. You cannot derive the price impact.** Flow → return requires
an impact function, and impact is empirical. Four other things resist derivation: anticipation
(others know the calendar too), absorption capacity (dealer balance sheets), the free
parameters in the agent's problem (risk aversion, policy specifics), and reflexivity (the
effect changes once exploited).

### 5.5 The homogeneity paradox

The more standardised the behaviour, the more derivable — and the more crowded. Uniform,
calendar-driven flow is exactly what gets front-run until anticipation is priced into the days
before rather than during. Derivability shifts where the edge sits and caps its size; it does
not guarantee one exists.

### 5.6 Sign-stability beats precision

You do not need a tight parameter estimate if the **sign of the prediction is stable across
the plausible range.**

Derive the parameter distribution from documents and aggregation, Monte Carlo over it, and
propagate to predicted flow:

- **Sign-stable** → parameter uncertainty does not matter. Stop estimating; you have bought
  robustness instead of precision.
- **Sign flips within the range** → tightening will not rescue it either, because estimation
  error will swamp the signal. Abandon the formulation.

This is robust control rather than optimal control, and it is the right posture when the plant
parameters drift — which they do, since covenant standards move with the credit cycle.

---

## 6. From feature to strategy

### 6.1 Combination, never filtering

Three things hide under the word "confluence":

**Filtering** — take short-term signals only when a slow signal agrees. The common retail
formulation and the weakest. Halves trade count, so breadth halves and IR falls ~29%; the
filter must raise IC by 41% just to break even. Reintroduces threshold parameters. And it is
silently a 100%-sized bet on the slow signal, validated as though it were a refinement.

**Conditioning** — the short-term signal behaves differently in different states. Defensible,
testable by computing IC within state buckets. But splitting the sample multiplies standard
errors by √(number of states). **Two states maximum** until the deep history lands, and the
conditioning variable must be pre-registered.

**Combination** — both as standardised features in one forecast. What firms actually do, and
strictly better than both. Agreement produces large positions and disagreement produces small
ones *automatically*, with no thresholds, no discarded trades, and no hidden bet. Each feature
stays separately measurable.

### 6.2 The combination arithmetic

```
IC_combined ≈ (IC_A + IC_B) / √(2(1 + ρ))
```

Fast signal at IC 0.04, slow at 0.03:

| ρ | Combined IC | vs fast alone |
|---|---|---|
| 0.0 | 0.049 | +24% |
| 0.3 | 0.043 | +9% |
| 0.7 | 0.038 | −5% |
| 1.0 | 0.035 | −13% |

**The entire benefit comes from decorrelation.** A slow signal that is really a slower version
of your fast one makes things worse despite a respectable standalone IC. This is why
orthogonality is an admission criterion, not a nicety.

### 6.3 The real reason to add a fundamental leg

Not higher IC — **shallower drawdown**. Short-term signals (reversal, breakout, momentum) fail
in the same conditions: regime transitions, vol spikes, gaps. Carry and hedging pressure have
a different failure mode. Under a trailing drawdown limit, the tail is the binding constraint
and decorrelation is the only reliable way to shrink it.

The right question of a fundamental component is *"does this reduce the depth of the worst
stretch"*, not *"does this improve returns."*

### 6.4 Implementation

```python
forecast = sum(w * z for w, z in zip(weights, feature_zscores))
forecast = clip(forecast, -2, +2)
position = forecast * vol_target / instrument_vol
```

Equal weights until optimised weights are demonstrated to beat 1/N out of sample. The cap is
conventional rather than fitted. No entry thresholds, no exit rules, no stops — position size
is proportional to forecast, rebalanced on a schedule.

Replacing thresholds with continuous forecasts is the single highest-value parameter-parsimony
move available (see §7 of `FEATURE_RESEARCH.md`).

---

## 7. Worked strategy sketch

**The trade:** hedgers sell the 12–24 month tenors regardless of price. Whoever absorbs that
flow is paid a premium. Be the other side, systematically, sized by how much flow there is.

Three consequences:
- The position is a **calendar spread** (long back, short front), not flat price. Neutral to
  the oil price; isolates the mechanism.
- You are **providing liquidity, not front-running**. Enter as and after flow arrives, when the
  back is cheap. Getting ahead of it means competing with every energy desk.
- It **generalises across commodities** — anywhere hedgers are structurally net short. That is
  where breadth comes from.

**Three layers:**

| Layer | Signal | Horizon | Role |
|---|---|---|---|
| 1 | Cross-sectional hedging pressure across ~15–20 commodities, from disaggregated COT, z-scored then ranked | 4–12 weeks | Documented risk premium; breadth |
| 2 | Derived CL flow model (maintenance + reaction + compliance), on the 12m–3m spread | Weeks | The derivation; curve-specific |
| 3 | Managed Money position-change reversal | 1–4 weeks | Liquidity provision; bets per unit time |

Combined per §6.4, rebalanced weekly on COT release.

**Why it fits the prop constraint:** calendar spreads have low volatility and CME margin
offsets; the cross-section supplies breadth; weekly rebalancing satisfies minimum-activity
rules without manufacturing trades; and it decorrelates against a trend-based book.

**What it does not fix:** spreads still gap on EIA Wednesday and the Sunday open, and the
derived flow lands where back-tenor liquidity thins, so execution cost needs careful modelling.

---

## 8. Portfolio construction

### 8.1 Diversification is additive in return at fixed risk

Return = Sharpe × volatility. Hold the vol target fixed and double the Sharpe, and the return
doubles. No leverage required.

Four uncorrelated strategies, each 5% at 10% vol, active in non-overlapping windows:
- Returns add linearly: **20%**
- Risk adds in quadrature: √(4 × 0.10²) = **20%**
- Sharpe: 1.0, i.e. 0.5 × √4

Return quadrupled while volatility doubled. The gain comes from **filling idle risk budget** —
a strategy active a quarter of the time leaves three-quarters of its risk capacity unused.

The capital-splitting intuition is wrong for futures: margin is a small fraction of notional, so
cash rarely binds. The binding constraint is the **risk budget**, and risk aggregates
sub-linearly across uncorrelated sources.

### 8.2 Constraints on that

- The gain is **√n, not n**. Four strategies buy double, not quadruple.
- **Genuine orthogonality is the hard part.** Trend in crude, gas and copper is one strategy.
  Carry and hedging pressure correlate 0.4–0.6 — substantially the same mechanism viewed twice.
  Realistic ceiling for a solo researcher: 3–5 orthogonal signals.
- **Correlations rise in stress**, because everything becomes a position on the same dealer
  balance sheets. Benefits computed on the full sample overstate what you get in the drawdown
  that threatens the account.
- **Overlap risk.** Sizing intermittent strategies as though windows are disjoint leaves you
  double-levered when two fire together — which tends to happen in high-vol conditions, because
  that is often why both triggered.

### 8.3 The implication for strategy selection

**Calendar-known windows are the ideal case.** Index rolls, redetermination-season compliance
flow, expiry and delivery mechanics, scheduled-release reactions. Windows known in advance
mean you can size against a known aggregate risk profile rather than hoping they stay apart.

Note that the always-on layered strategy in §7 does *not* get this benefit — all three layers
are continuously sized. The timing argument is a reason to add a **different kind** of strategy
alongside it, not a property of that one.

### 8.4 How to raise returns

**Add orthogonal mechanisms and more instruments. Do not refine one mechanism with conditions.**

The test for any proposed addition: **does it add breadth or subtract it?**

- *Excluding a regime* removes 20% of the sample → breadth −20% → IR −11%. Must raise IC by
  >12% to break even. Most do not.
- *Adding sign-flipped instruments* takes a 15-market cross-section to 20 → IR +15%, with
  **zero new parameters**, because the sign is derived from which side the hedging population
  sits on.

A 26-point swing between two things that both sound like "handling the exceptions."

---

## 9. Scope and exceptions

### 9.1 Sign inversions — these are opportunities, not hazards

**Consumer-hedged markets.** The mechanism assumes hedgers are structurally net short. Airlines
are long jet-fuel exposure and hedge by buying. Live cattle: feedlots hedge cattle short but
corn long. Electricity and gasoline have mixed populations. Where the dominant hedging
population is a consumer, the premium reverses sign — so these belong in the cross-section with
the sign flipped, adding breadth for free.

Check the historical sign of the commercial position per market before assuming direction.

### 9.2 Markets where the mechanism does not exist

- **Precious metals.** Gold and silver are financial assets; commercials are bullion banks
  intermediating investment flow, not producers. Miners hedge episodically in waves driven by
  shareholder politics. Exclude or test separately.
- **Financial futures.** No producers. TFF categories (Dealer, Asset Manager, Leveraged Funds)
  have no physical interpretation. Different mechanism entirely.

This is **scope definition**, not regime conditioning — derived from the absence of a hedging
population, not from performance.

### 9.3 Temporary mechanism failures

- **Distress and unwind.** Producers monetising in-the-money hedges for liquidity generate
  *buying* — opposite sign, arriving at the worst moment. March–April 2020. The biggest gap in
  the derivation, and correlated with everything else in the book going wrong.
- **Negative prices.** April 2020 WTI below zero: percentage returns undefined, log returns
  impossible, storage logic inverted. The data layer needs an explicit decision.
- **Squeezes and delivery failures.** LME nickel 2021 — the exchange cancelled trades, so the
  backtest contains prices that never settled.
- **Covenant regime breaks.** RBL terms tightened after 2014 and again after 2020. The shale
  transition around 2010 changed the population. A model fitted across these averages two
  different worlds.

### 9.4 Market-specific quirks

- **Natural gas** — seasonality dominates; storage constraints bind; population includes both
  producers and utilities; weather overwhelms flow.
- **Agriculturals** — harvest cycles impose calendar-driven hedging unrelated to price; index
  traders (Supplemental COT) are a large non-hedger presence in the 13 covered markets.
- **Deferred contracts** — thin liquidity means stale settlements; apparent signals are often
  settlement artefacts. Relevant because the derived CL flow lands at 12–24 months.

### 9.5 Event windows to handle explicitly

Expiry and delivery periods; scheduled releases (EIA Wednesday, WASDE, OPEC); index roll
windows (large enough to swamp hedging flow, and a separate signal in their own right);
redetermination seasons (model predicts selling, but distress unwinds cluster here too — both
directions active).

---

## 10. Exclusion discipline

Exclusions chosen after seeing results are the most reliable way to inflate a backtest, because
removing the worst periods always helps.

### 10.1 The test

> **Can you verify the premise was violated using evidence other than the returns?**

If yes, it is a mechanism failure. If the only evidence is that you lost money, it is circular —
the regime has been defined by its outcome.

### 10.2 Decompose into observable premises

The hedging-pressure mechanism has four, each independently checkable:

1. A hedging population exists and is structurally net short → *check the COT category sign*
2. They are constrained, trading regardless of price → *check covenant terms; check flow occurred on rallies*
3. Someone must be compensated to absorb it → *check speculators are net long*
4. The flow actually happened → *check the position change*

Then:
- **Gold** — premise 1 fails, establishable without computing a return. Legitimate.
- **March 2020** — premise 2 inverts, visible directly in position data. Legitimate.
- **"2015 was a bad year"** — all four held. It just lost. **Not an exclusion.**

### 10.3 The base rate problem

At IC ≈ 0.03 you lose ~45% of periods by construction. The worst 20% window in any random
sequence looks awful. Go looking for a period to exclude and you will always find one, whether
or not the mechanism is real. "This period underperformed" carries almost no information.

### 10.4 Two tests that break circularity

- **Does the premise indicator flag periods the losses did not?** Build it from non-return data.
  If it fires only on loss-making periods, it was reverse-engineered from P&L. If it fires
  elsewhere *and those also underperformed*, that is out-of-sample confirmation of the exclusion.
- **Does the exclusion make further predictions?** A mechanism-based one does: "gold fails
  because the hedging population is weak" predicts a *continuous* relationship — intermediate
  populations, intermediate returns. Testable. A performance-based exclusion predicts nothing.

### 10.5 The move that dissolves the problem

**If the premise is observable, weight by it continuously instead of excluding.**

Scale the forecast by hedging-population strength rather than excluding gold. Scale by whether
commercial positioning behaves as the model expects rather than excluding distress periods. No
threshold to fit, no sample split, no breadth loss — and if the indicator is uninformative, the
weighting does nothing rather than silently removing your worst periods.

### 10.6 Three kinds of failure

| Pattern | Diagnosis | Response |
|---|---|---|
| One bad stretch | Noise | Nothing |
| Structural break with identifiable cause, confirmed independently | Mechanism failure | Exclude, pre-registered |
| Continuous failure after publication | Decay | **Retire the strategy** |

Exclusion is only right for the middle case, and it is the rarest of the three. The published
hedging-pressure premium decayed post-publication, as documented effects generally do — which
means checking stability across subperiods rather than pooling and reporting one number.

### 10.7 Procedural requirement

Write exclusions into the pre-registration, justified by **mechanism**, before testing. Build
one diagnostic that runs the strategy with and without each exclusion and reports both. A
mechanism-driven exclusion should help modestly and consistently. If an exclusion is the
difference between a failing and a passing result, that is where you are fooling yourself.

---

## 11. Honest expected magnitudes

**Gross Sharpe, three-layer strategy:** 0.5–0.8, weighting the lower half more heavily.
Published hedging-pressure literature sits at 0.4–0.7; add modest uplift for combining
imperfectly-correlated layers; haircut for retail-grade data and execution.

**Net of cost:** 0.4–0.7. Turnover is low so drag is small, but back-tenor spread legs are
where liquidity thins.

| Vol target | Expected annual return at SR 0.6 | Expected worst drawdown |
|---|---|---|
| 5% | ~3% | ~8–12% |
| 10% | ~6% | ~15–25% |
| 15% | ~9% | ~25–35% |

Drawdowns of 1.5–2× annual volatility are normal at this Sharpe, not exceptional.

**Character:** slow, low-vol, low-turnover, capacity-limited by back-tenor liquidity. Its role
is the decorrelating always-on leg of a book. It is not the thing to rely on to pass an
evaluation, and any version that looks like it could should be treated with suspicion.

**The capital point.** At 6% net, earning £100k from trading requires ~£1.7m. The strategy is
not the constraint; capital is. The primary value of this programme is the research artefact
and the demonstrated process — which route through a salary, not through P&L.

---

## 12. The prop evaluation as a first-passage problem

The evaluation is not a test of the strategy. It is a first-passage problem with barriers set
close together.

```
P = (1 − e^(−θb)) / (1 − e^(−θ(a+b)))     θ = 2·Sharpe/σ
```

With a = 8% target, b = 5% trailing limit, no time limit:

| Sharpe | σ=10% | σ=20% | σ=30% | σ=50% |
|---|---|---|---|---|
| 0.0 | 38% | 38% | 38% | 38% |
| 0.5 | 49% | 44% | 42% | 40% |
| 1.0 | 68% | 54% | 49% | 45% |
| 1.5 | 79% | 63% | 55% | 48% |
| 2.0 | 87% | 71% | 61% | 52% |

Two readings that should change behaviour:

**A zero-edge strategy passes 38% of the time.** Your own pass is therefore not evidence the
strategy works. Several attempts are needed before the outcome carries information — and a
single failure tells you nothing. **Decide in advance not to change anything on fewer than
three failures**, or you will be fitting to evaluation noise.

**Lower leverage raises the pass probability.** Barriers are fixed in percentage terms, so
reducing volatility gives drift more time to accumulate relative to noise. You are not paid for
volatility here; you are punished for it.

**But expected time to target ≈ 0.08/(Sharpe × σ)** — roughly 200 days at 10% vol, 40 at 50%.
A 30-day limit forces you into the high-vol columns where pass probability collapses. **Choosing
a firm without a tight time limit moves the odds more than any plausible strategy improvement,
and costs nothing.**

### 12.1 Breadth per unit time

A signal updating weekly with multi-week decay gives 1–4 independent bets per evaluation window.
At breadth ≈ 2 the outcome is a coin flip regardless of edge quality. The fix is **cross-sectional
breadth**, not faster signals — and market-neutral cross-sectional construction also suppresses
portfolio volatility, which raises pass probability. Both requirements point the same way.

### 12.2 Hazards

- **The trailing limit ratchets.** Gains raise the floor, so profits cannot be given back. Once
  a few percent up, cut leverage further — remaining buffer is what matters.
- **Check whether drawdown is measured on closed equity or including open positions.** Intraday
  measurement is materially tighter than a daily-close backtest suggests.
- **Gaps are the main breach mechanism.** Sunday opens, EIA, WASDE, payrolls, FOMC. A daily
  backtest cannot see an intraday spike that breaches and closes back green. Consider flattening
  into known events: small EV cost, large tail benefit.
- **Correlation clustering.** Thirty contracts are not thirty bets. Size with a shrunk
  covariance matrix, not per-instrument vol targeting.
- **Budget 3–5 attempts** as a known cost. At a 55% pass rate there is a 9% chance of three
  consecutive failures with a perfectly good strategy.

### 12.3 Two tiers

Evaluation vehicle and funded strategy need not be the same. Evaluation: maximum breadth per
unit time, low vol, tight risk control. Funded: the structural signals whose horizon suits the
capital. Check the agreement first — some firms restrict post-funding strategy changes or run
consistency rules.

### 12.4 The funded account is almost certainly simulated — added 18 Sep 2026

Everything in §12 above treats a funded prop account as routing to the exchange. **It usually
does not.** Funded accounts at the major firms are predominantly simulated: trading is against
the firm's fill engine on real market data, and payouts come from the firm's reserves (largely
evaluation fees). Topstep's 2025 disclosure puts live call-ups at **0.71%** of Express Funded
participants; Apex keeps funded accounts on sim indefinitely.

Five consequences, none of which the earlier analysis accounted for:

1. **The firm is the counterparty.** A consistently profitable trader is a cost to the house.
   Expect payout caps, consistency rules, and rule changes aimed at algorithmic edges. The
   account-life arithmetic in §12 assumed a rule set stable for years; it will not be.
2. **Execution is against a sim engine, not the book.** Strategy edge must survive the *firm's*
   fill model. Sim engines typically fill market orders at the displayed price with no impact and
   limit orders at the touch or on trade-through — sometimes more favourable than live, which is
   what firms' anti-exploitation rules target. **Maintain two cost models**: sim for prop,
   real book for personal capital.
3. **A sim track record is not a live track record.** The "credential" value attributed to prop
   trading earlier in this programme is materially lower than stated. Real payouts are evidence
   of something; they are not evidence a fund allocator will weigh.
4. **Forced-flat and product rules are tighter than assumed.** Topstep: flat by 3:10 PM CT, no
   overnight. Apex 4.0: flat by 4:59 PM ET. Apex has removed metals. Check each study's window
   and universe against the *current* rulebook of the specific firm.
5. **Automation is not automatically permitted.** Some firms restrict unattended trading.
   Constraint 6 (algorithmic) must be verified per firm rather than assumed.

The income arithmetic in §12 and in the discussion that followed it still holds *if* the
strategy's edge survives the sim engine and the rule set holds. Both are now explicit
assumptions rather than background facts.

**The route this strengthens is personal capital.** Everything about the sim environment that
makes prop income fragile is absent when trading your own account against the real book —
which is the direction the plan was already heading, and this is one more reason to get there.

---

## 13. Probability and modelling

Four distinct roles, often conflated:

1. **The forecast is a conditional expectation.** `E[r | features]`. IC evaluation deliberately
   discards magnitude, so it measures ordering, not the distribution being bet on.
2. **Second moments are far more predictable than first.** Vol forecasts achieve R² ≈ 0.3–0.5;
   return forecasts ≈ 0.003. **Most realised Sharpe improvement comes from modelling risk well,
   not return.**
3. **Higher moments determine survival.** Carry strategies have negative skew — small steady
   gains, occasional large losses. Sharpe is blind to this; a trailing drawdown limit is not.
4. **Sizing is an explicit probabilistic decision.** Kelly ≈ μ/σ², but μ is estimated with huge
   error, so fractional Kelly is the correct response to parameter uncertainty rather than mere
   conservatism. And under prop rules Kelly is the wrong objective entirely — maximise
   P(target before limit), not growth rate.

**Priorities:** a proper volatility model feeding sizing; shrinkage everywhere (covariance
toward a structured target, Sharpe toward zero, weights toward 1/N); first-passage simulation
with parameter uncertainty propagated; fat-tailed assumptions (Student-t, 4–6 df) in any
simulation.

**Skip:** regime-switching, stochastic vol with latent states, hierarchical Bayes, MCMC. Not
wrong in theory — they add parameters a 10-year sample cannot support, and complexity in the
model is indistinguishable from complexity in the fit.

**Simulation caveat:** bootstrap estimates sampling variability around what you observed. It
cannot tell you whether the observed edge was real. IID bootstrap destroys volatility
clustering and makes drawdowns look far milder than reality; block bootstrap preserves some,
and still understates crisis clustering.

---

## 14. What industrialisation means here

Firms industrialise to raise throughput: standardised research units, separation of alpha from
portfolio construction, data onboarding pipelines, versioned alphas with live-vs-backtest IC
tracking and retirement triggers, marginal evaluation against the existing combined forecast,
and a managed hypothesis funnel (~100 ideas → ~20 tested → ~3 admitted → ~1 alive in two years).

The **alpha factory** extreme — formal operator grammars searched mechanically, millions of
alphas — does not transfer. It works only with tiny weights across thousands of signals,
sophisticated combination infrastructure, and an enormous cross-section. With 40 contracts and
10 years, mechanical search returns a beautiful 1.4 Sharpe from pure noise.

| | Many weak alphas | Few structural alphas |
|---|---|---|
| Needs | Scale, breadth, data spend, infra | Domain insight, patience |
| IC per alpha | 0.01–0.03 | 0.05+ |
| Count | 50–500 | 3–8 |
| Breadth source | Cross-section | Time + instruments |
| Works at small scale | No | **Yes** |

**Invert the objective.** Firms industrialise to raise throughput; you industrialise to drive
the cost of a *well-motivated* test to near zero while keeping the number of tests deliberately
small. Same infrastructure, opposite volume.

Priorities: the harness (feature in, standard report out, one command); industrialising the
**input** side (new datasets expand the hypothesis space; new transformations of price mostly
do not); a triaged mechanism backlog ordered by prior × cheapness; decay monitoring from day
one; and pre-registration as the substitute for peer review you do not have.

---

## 15. Roadmap

**Phase 1 — harness and baseline**
1. Build `research/` per `FEATURE_RESEARCH.md`. Port existing strategy signals into the feature
   library and re-evaluate them unconditionally.
2. Replicate carry and TSMOM on deep history. If they do not replicate, the harness is broken —
   find that out on known-good signals.
3. Build `research/validation/`, wire CPCV to the path-invariant frame alongside walk-forward on
   the path-variant frame. Run PBO retrospectively on existing sweep results.

**Phase 2 — hedging pressure**
4. Verify the flow appears in Swap Dealers (P9 in the derivation). If not, stop and fix the mapping.
5. Check `h̄` against (strip − survey expectation) on quarterly data (P7).
6. Pre-registered regression for P1–P3 on disaggregated COT from 2009, with the time-to-delivery
   confound removed.
7. Sign-stability Monte Carlo — establish whether λ needs pinning down at all.
8. Build layer 1 (cross-sectional hedging pressure) as a feature; admit or reject per the
   standard criteria.

**Phase 3 — breadth**
9. Add sign-flipped consumer-hedged markets. Largest gain, zero new parameters, and a genuine
   test of the mechanism: if the premium reverses where the population reverses, the effect is
   real rather than fitted.
10. Fold saturation and the σ² term into the continuous forecast. Already derived, no trial cost.
11. Index roll as a separate strategy with its own derivation and calendar.
12. Delivery-period mechanics as a third.

**Phase 4 — deployment**
13. Combine surviving features at equal weight, vol-target through a shrunk covariance matrix.
14. First-passage simulation to choose evaluation sizing.
15. Forward log from day one — the only uncontaminated holdout accrues at one month per month.

---

## 16. Open questions

- What fraction of the hedgeable population actually carries an RBL covenant? Needs a count from
  filings; it bounds the compliance term.
- How much has the hedging-pressure premium decayed within the available sample? Subperiod
  stability, not a pooled number.
- Does the derived CL layer add anything over cross-sectional hedging pressure, or is it the
  same signal measured twice? Incremental IC decides.
- What is the realistic capacity of the back-tenor spread leg before impact eats the edge?
- Do consumer-hedged markets genuinely show the reversed premium? This is the strongest available
  falsification test of the whole mechanism.

---

## 17. Portfolio framing

A strategy with a good Sharpe proves little; anyone can produce one and the reviewer's first
assumption is that it was mined.

What is rare: a mechanism derived from primary sources with an explicit free-parameter count, a
pre-registered prediction set, a test log with the kills still in it, honest treatment of where
the model inverts, and a stated reason for choosing the few-structural-alphas model over the
factory model.

The honest narrative is exactly that argument: *"the industrial many-weak-alphas model requires
scale I do not have, so I built the high-prior, low-throughput version, and here is the
discipline that makes it valid."* A senior quant reads that as someone who understands both
models and chose correctly — a much stronger signal than an imitation of the factory at
1/10,000th scale.

**This holds even if every feature in Phase 2 comes back at zero IC.** A writeup concluding
"the mechanism is real, the signal is not measurable at this sample size, here is the evidence"
is more persuasive than a working strategy with an unexplained edge.
