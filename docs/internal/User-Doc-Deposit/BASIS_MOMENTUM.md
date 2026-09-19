# Basis-Momentum: Base Specification

**Status:** base document, pre-registration draft — to be expanded
**Source:** Boons, M. & Prado, M. (2019). "Basis-Momentum." *Journal of Finance* 74(1), 239–279.
Earlier working title: "Basis-momentum in the futures curve and volatility risk" (SSRN 2587784).
**Role in the programme:** candidate second mechanism, selected for orthogonality to hedging
pressure rather than for standalone strength.

**Companions:**
- `ALPHA_PROGRAMME.md` — why mechanism-first, how features become strategies
- `FEATURE_RESEARCH.md` — the harness this is evaluated in
- `HEDGING_FLOW_DERIVATION.md` — the mechanism this must be orthogonal to
- `PUBLISHED_STRATEGIES.md` — the replication baseline this sits beside

---

## 1. What it is

Basis-momentum is momentum measured on the **difference between two points on the futures
curve**, rather than on price. Boons & Prado introduce it as a return predictor related to the
**slope and curvature** of the futures term structure.

Construction, in essence:

```
BM(i,t) = R_first(i, t−12 → t)  −  R_second(i, t−12 → t)
```

where:
- `R_first` is the cumulative total return of holding and rolling the **first-nearby** contract
- `R_second` is the cumulative total return of holding and rolling the **second-nearby** contract
- both are **total returns from a roll strategy**, not price changes

Taking the difference cancels the common price move and leaves the component driven by how
the curve's shape has been evolving.

**Relation to what you already have:**

| Signal | What it measures |
|---|---|
| Carry / basis | The curve's **current slope** |
| Momentum | The **price level's** recent direction |
| **Basis-momentum** | How the **slope has been changing** — slope *and* curvature |

Because it is a difference of two momentum terms, it captures curvature rather than level
alone. That is why it is not a repackaged carry signal.

**Portfolio formation, as published:** cross-sectional sort, long high BM and short low BM,
monthly rebalance. The paper's headline portfolios are **High4 minus Low4** out of roughly
21–32 commodities.

> **Construction caveat:** the formula above is the essential structure as I understand it
> from the abstracts and secondary sources. **Verify the exact definition, lookback, and
> rolling convention against the published paper before building.** The difference between
> "cumulative return of a rolled strategy" and "compounded monthly excess returns of the
> nth-nearby" is exactly the kind of detail that changes the result.

---

## 2. The mechanism, in detail

The one-line version — "imbalances in futures supply and demand when intermediary
market-clearing is impaired" — is accurate but hides why it works and why several of the
implementation decisions in §6 are forced rather than chosen. This section builds it up.

**Attribution note.** §§2.5–2.8 restate claims made by Boons & Prado. §§2.1–2.4, the
orthogonality framing in §2.9, and the implications in §3 are a reconstruction of *why* those
claims hang together. The reconstruction is consistent with what the paper reports but the
paper may argue it differently or more precisely. **Check against the published text.**

### 2.1 Why a curve needs clearing at all

The textbook relation pins the curve by storage economics:

```
F(t,T) = S(t) · e^((r + w − c)(T − t))
```

with convenience yield `c` reflecting inventory tightness. Low inventories → high convenience
yield → backwardation. This is the theory of storage, and it is the foundation of carry.

But it is a **no-arbitrage condition**, and no-arbitrage conditions hold only because somebody
performs the arbitrage. Enforcing this one means buying physical, borrowing, paying storage and
shorting the deferred contract — or, in the purely financial version, holding a calendar spread
to convergence. Either way someone commits balance sheet and carries mark-to-market risk in the
interim.

**The curve is not a mathematical object that snaps into shape. It is the output of a clearing
process performed by constrained agents.**

### 2.2 The curve clears maturity by maturity, not as a whole

This is the crux, and what makes basis-momentum distinct from every other commodity signal.

Each point on the curve has its own supply and demand, because participants concentrate at
different tenors:

| Participant | Tenor concentration | Why |
|---|---|---|
| Index funds | Front and second | Published roll methodology |
| Producers | 12–24 months | Covenant windows (see `HEDGING_FLOW_DERIVATION.md` §1.2) |
| Consumers | Purchasing cycle | Matches physical procurement |
| CTAs / speculators | Front | Liquidity |
| Options dealers | Wherever sold options sit | Gamma hedging |

**These flows do not net out at each maturity.** A producer-hedging shock hits the 1–2 year
region. An index roll hits the front two contracts. There is no reason for them to balance
point by point.

The entity that makes the curve internally consistent is whoever trades the **calendar spread** —
buying where there is excess selling pressure, selling where there is excess buying, warehousing
the resulting spread risk. That is the intermediary.

### 2.3 The arbitrage that is not free

Warehousing spread risk costs margin, balance sheet, risk limits and funding. It carries
mark-to-market risk, and a spread can move against the holder for a long time before converging.
In physical commodities the true version additionally requires **storage capacity**, which is
finite and sometimes full.

So when intermediary capacity is impaired — constrained balance sheets, binding VaR limits,
expensive funding — maturity-specific flow can push the curve out of shape **and it stays that
way**. The deviation persists rather than being smoothed.

### 2.4 The control analogy

The curve is a **distributed system with a local disturbance**, and the arbitrage loop is the
controller that propagates and dissipates that disturbance along the maturity axis.

When intermediary capacity shrinks, **loop gain drops**. Local deviations that would normally be
rejected instead persist and evolve.

**Basis-momentum is a measurement of that persistence.**

This is not decoration. It is why the signal is a *cumulated difference* rather than a level:
you are measuring how long a disturbance has been failing to dissipate, which is the observable
consequence of reduced loop gain.

### 2.5 From persistent imbalance to a signal

The construction now follows. Take the rolled return of the first-nearby and of the
second-nearby over the same window. Both contain the same underlying spot move. **Differencing
cancels it.**

What remains is the difference in **roll returns** between two points on the curve, cumulated
over twelve months — a measurement of how the curve's shape at the front has been evolving
relative to slightly further out.

| | |
|---|---|
| Carry | The slope **now** |
| Basis-momentum | The **accumulated change in slope across maturities** — i.e. curvature |

Hence the paper's framing as related to slope *and* curvature.

A high reading means the front has been **persistently** outperforming the deferred in roll
terms: sustained, one-directional pressure at a specific point on the curve that has not been
arbitraged away.

### 2.6 The critical fork — risk premium or mispricing?

Two very different stories predict the same signal, and which one is true determines what to
expect:

| | Underreaction (mispricing) | Compensation for risk |
|---|---|---|
| Story | Flow arrives gradually, impact accumulates, past shape-change predicts more | The imbalance persists because the intermediary holds an unwanted position and must be paid to keep holding it |
| Signal is | The mispricing itself | The **signature** of the imbalance; future return is **payment for absorbing it** |
| Predicts | **Decay** once published and arbitraged | **Persistence** — a risk premium cannot be arbitraged away, only accepted |

**Boons & Prado land on the second.** Their discriminating evidence: exposure to basis-momentum
is **priced** among commodity-sorted portfolios and individual commodities. A pure mispricing
would not appear as a priced risk factor.

**This changes what to expect.** A risk premium does not decay from arbitrage — but it loses
money when the risk materialises. You are not finding free money. You are being paid to hold
something uncomfortable, and periodically the discomfort arrives.

### 2.7 What the risk actually is

The paper ties it to intermediary constraints directly: basis-momentum is **negatively exposed
to financial intermediary risk**, consistent with leverage-constrained-intermediary theories
(Brunnermeier–Pedersen 2009, Adrian–Shin 2014), with an estimated price of risk consistent in
sign and magnitude with Adrian, Etula & Muir (2014).

Operationally, "negatively exposed" means:

- **You earn** in normal times by supplying the market-clearing that constrained intermediaries
  cannot.
- **You lose** when intermediary capacity contracts *further* — deleveraging, funding stress,
  risk-limit cuts — because the imbalances you are positioned in get **worse** rather than
  converging.

That is the risk you are paid for. It is also exactly why it pays: returns are bad in the states
where investors most need money.

### 2.8 Why volatility amplifies it

The paper finds the effect **increasing in volatility**. The mechanism explains this with no
additional assumption:

```
higher vol → higher VaR on the same position → risk limits bind sooner
           → intermediary warehousing capacity shrinks
           → lower loop gain → larger persistent deviations → stronger signal
```

This is why folding volatility in as a continuous multiplier (§6.5) **costs no trial**. It is
not a regime discovered by splitting your sample; it is a prediction of the mechanism.

### 2.9 The orthogonality argument

**The elegant part, and the reason this candidate was selected.**

The paper reports that basis-momentum is **present in currencies and stock indexes**, and that
the findings are **inconsistent with explanations based on storage, inventory, and hedging
pressure**.

Those two facts are the same fact. There is no storage in FX. There is no convenience yield on
the S&P. There are no producers hedging output in an equity index future. **Every
physical-commodity explanation is structurally unavailable in those markets** — so if the effect
appears there, the mechanism cannot be physical.

What *is* common across commodities, FX and equity index futures: multiple maturities,
participants concentrated at different tenors, and intermediaries who must warehouse spread risk
to keep the curve coherent. That is the only surviving explanation.

This is why the universe extension (§8) is **principled rather than opportunistic**. You are not
hoping the effect generalises; you are extending to markets where the mechanism says it should
exist and where the competing explanations cannot operate.

Against your existing programme:

| | Hedging pressure | Basis-momentum |
|---|---|---|
| Who is constrained | The **hedger** — must trade regardless of price | The **arbitrageur** — cannot absorb the imbalance |
| Nature of constraint | Mandate, covenant, policy | Balance sheet, risk limits, funding |
| What you are paid for | Taking the other side of forced flow | Supplying market-clearing capacity |
| Where it shows up | **Level** of the curve, net position | **Shape** of the curve, maturity-specific |
| Fails when | Hedgers reverse (distress unwinds) | Intermediaries deleverage |

Hedging pressure is a story about **demand to trade**. Basis-momentum is a story about **supply
of liquidity**. Different constraints on different agents, which is why they coexist as separate
premia.

**But look at the bottom row.** Both failure modes are flavours of financial stress and will
often arrive together — a crisis produces both distressed hedgers and deleveraging
intermediaries. The average correlation can be near zero while the tails overlap heavily, and
the tails are what a drawdown limit cares about. **This concern is derived from the mechanism,
not merely an empirical caution.** It is why T4 (§7.5) exists and why it should run early.

### 2.10 Additional published properties

From the paper and its earlier working version, basis-momentum is:

- **Maturity-specific** — measured at the short end it indicates near-to-expiring contracts
  will outperform next month, but it also contains a maturity-specific component that varies
  across the curve
- **Driven by roll returns** — not by spot price moves
- **Present in currencies and stock indexes**, not only commodities
- **Increasing in volatility**
- Predictive of **both spot and term premiums**, in **both** the time series and the
  cross-section
- More **diverse in portfolio composition** than basis sorts (higher turnover of constituents)

### 2.11 Decay exposure

Published 2019, working paper 2015. Roughly seven years of post-publication exposure versus
forty for momentum and longer for carry. Per `PUBLISHED_STRATEGIES.md` §1.1, expect decay but
less of it than for the older effects. **Do not assume it is undecayed** — test subperiod
stability explicitly (§10 item 8, and §3 below for the prediction that cuts the other way).

---

## 3. Testable implications of the mechanism

If §2 is right, the following should hold. **Each is a sharper test than "does it have IC"**,
because each tests the *mechanism* rather than the *returns* — and a mechanism that survives
independent tests is far more credible than a backtest that looks good.

| # | Implication | Follows from | Data needed |
|---|---|---|---|
| M1 | **Stronger in less liquid markets**, where intermediary capacity is thinner relative to flow | §2.3 | Volume, open interest — already held |
| M2 | **Stronger after volatility spikes**, with a lag reflecting how quickly risk limits respond | §2.8 | Realised or implied vol |
| M3 | **Concentrated at maturities where identifiable participant groups cluster** — front for index/CTA flow, 1–2yr for producer hedging | §2.2 | Full curve settlements |
| M4 | **Correlated with dealer balance-sheet stress** — capital ratio, funding spreads, dealer positions | §2.7 | He–Kelly–Manela intermediary capital factor; NY Fed primary dealer stats (§4.1) |
| M5 | **Uncorrelated with inventory data** — a direct test of the storage explanation | §2.9 | EIA stocks, COMEX/LME warehouse stocks — free (§4.4) |
| M7 | **Stronger around quarter-end and year-end**, when regulatory reporting mechanically shrinks dealer balance sheets | §2.3, §2.4 | Reporting calendar only — derivable, free (§4.2) |

**M6 — the prediction that cuts against the standard story.**

Post-crisis bank regulation (Basel III, Volcker, SLR) **reduced dealer balance-sheet capacity**.
By this mechanism, that should have **strengthened** basis-momentum post-2010, not weakened it.

This runs directly opposite to the usual publication-decay expectation. If the subperiod
analysis shows the effect holding up or growing post-2010, that is **evidence for the
mechanism** rather than merely a fortunate sample. If it shows decay, the risk-premium framing
(§2.6) is weakened and the mispricing story gains ground — which would change the expected
persistence and therefore whether this belongs in the book at all.

**Pre-register the direction before looking.** M6 is the single most informative test in this
document.

**Note on trial accounting:** M1–M7 are tests of the *mechanism*, not selections among
candidate configurations. They do not consume the selection budget in §7, but they must still
be pre-registered with predicted directions, and a failure should be reported rather than
quietly dropped.

---

## 4. Development work: instrumenting the mechanism

§2 names a specific state variable — **intermediary capacity**. That variable is observable.
Measuring it turns basis-momentum from "a signal that happens to work" into "a signal
conditioned on the thing the mechanism says drives it", and it supplies the data for M1–M7.

This section is **development work for after the base tests (§7) resolve**, not a prerequisite
for them. Build the signal first; instrument the mechanism second.

Organised by which part of §2 each source measures.

### 4.1 Measuring the constraint (§2.7)

**He–Kelly–Manela intermediary capital ratio — the canonical measure, and free.**

He, Kelly & Manela (2017, *JFE* 126(1), 1–35) construct a risk factor from shocks to the equity
capital ratio of the **NY Fed's primary dealer counterparties**. They find it has significant
explanatory power for cross-sectional variation in expected returns across equities, government
bonds, corporate and sovereign bonds, derivatives, **commodities and currencies** — i.e. exactly
this universe. The factor is strongly procyclical, implying countercyclical intermediary
leverage, and the price of risk is consistently positive and of similar magnitude estimated
separately by asset class.

Availability:
- **asaf.manela.org/data/** — intermediary capital risk factor, quarterly and monthly from
  1970Q1, daily from 2000-01-01, plus the portfolio returns used in the cross-sectional tests,
  a readme and replication code
- **zhiguohe.net** — maintained updated versions, quarterly from 1970 to present and daily
  from 2023

This is the direct instrument for **M4**, and it closes the loop between Boons & Prado's
price-of-risk comparison and your own test. Get this first.

**NY Fed Primary Dealer Statistics.** Weekly, free. Positions and financing by security type.
Where the capital ratio measures the *constraint*, this measures the *inventory actually being
carried* — a more direct read on warehousing capacity in use.

**Cross-currency basis — computable in-house.** Deviations from covered interest parity are a
direct, daily measure of dealer balance-sheet scarcity: when balance sheet is expensive, the
basis widens, because closing it requires precisely the capacity that is missing
(Du, Tepper & Verdelhan 2018). Constructible from FX futures plus rates — both already required
for the §8 universe. No vendor, daily frequency, and it measures the same constraint in a
different market.

**Equity index futures basis — computable in-house, and possibly the best instrument available.**

Arbitraging index futures against the cash basket requires balance sheet. When capacity is
constrained, futures richen or cheapen against fair value. The **implied financing rate** backed
out of the ES/NQ/RTY basis is therefore a direct measure of dealer balance-sheet cost — the same
constraint as §2.7, measured in a different market, at daily or better frequency, **from data
already held**.

Two reasons to rank this highly:

- It measures the constraint **in an instrument you actually trade**, rather than in a quarterly
  academic series constructed from bank balance sheets.
- The **quarter-end widening** in index futures basis is well known to the people who trade it,
  which makes it a direct and independent test of **M7** (§4.2) rather than a proxy for it.

Note the dependency: the same dividend-drift confound that affects the signal (§8, open question
2) affects this measurement. Back out the financing rate properly rather than reading raw basis.

**Funding spreads.** SOFR–IORB, SOFR–EFFR, FRA–OIS, commercial paper spreads, repo spikes.
Note the TED spread is discontinued following the LIBOR transition; do not build on it. Via
FRED — and **via ALFRED for anything historical**, per `DATA_EXPANSION_PLAN.md` §2.5.

**Dealer bank CDS spreads and equity volatility.** Higher-frequency distress proxies than the
quarterly capital ratio. Secondary.

### 4.2 The calendar-known version — highest-value derivative of the mechanism

**Quarter-end and year-end regulatory reporting dates.**

G-SIB scoring and leverage-ratio reporting are **snapshot-based**, so dealers shrink balance
sheets into reporting dates and re-expand afterwards. That is a **known-in-advance,
mechanically-driven contraction in exactly the capacity the mechanism depends on.**

The prediction follows directly from §2.4: loop gain drops into quarter-end → curve
disturbances persist longer → basis-momentum is stronger around those dates. **Year-end more
than quarter-end**, since reporting pressure is larger.

Why this is the most valuable item in the section:

- **Costs nothing** — the calendar is public and derivable
- **Sharp and pre-registerable** — direction and relative magnitude both predicted in advance
- **Converts a risk premium into something with a schedule**, which is the bridge to the
  calendar-window strategy class in `ALPHA_PROGRAMME.md` §8.3 — strategies with published
  active windows that can be sized against a known aggregate risk profile

This is **M7**. Pre-register the direction and the year-end-versus-quarter-end ordering before
looking.

### 4.3 Measuring the clearing process itself (§2.4)

**Calendar spread liquidity, from existing Databento data.** The most direct available
measurement of loop gain, and almost nobody extracts it: bid-ask, depth at touch, and volume
**on the spread instrument itself** rather than on the outright legs.

If the spread market is thin, the arbitrage that flattens curve disturbances is expensive, and
§2.3 says deviations should persist. The data is already owned; extracting it cleanly is real
work — which is exactly why it is a moat rather than a commodity input (cf. §6.1, the
second-nearby construction moat).

**COT Swap Dealer gross positions and trader counts.** Already held. Swap dealers *are* the
intermediaries in commodities. Use **gross, not net** — gross positioning is capacity in use.
The trader-count and concentration-ratio fields give capacity *fragility*. Both underused.

**Aggregate open interest and the OI-to-volume ratio.** When warehousing capacity contracts,
open interest falls relative to turnover.

### 4.4 Measuring the disturbance (§2.2), and the negative control

| Source | Measures | For |
|---|---|---|
| Full-curve settlements | *Where* on the curve the imbalance sits | M3 |
| Options OI by strike and expiry | Dealer gamma positioning — one of the §2.2 maturity-specific flows | M3 |
| Index roll calendars | A **known** disturbance with a published schedule | M1, M7 |
| EIA stocks, COMEX/LME warehouse inventories | Storage state — the **negative control** | M5 |

The index-roll item is worth singling out: if basis-momentum measures disturbance *persistence*,
it should spike around rolls and **decay at a rate that depends on intermediary capacity**. That
is a joint test of both halves of the mechanism in one experiment.

On M5 — worth doing precisely because it is a test you might fail. One extension: **storage
capacity utilisation** is the physical analogue of balance-sheet constraint. When tanks are
full, the physical arbitrage is unavailable for the same structural reason the financial one is
when balance sheets are full. If both matter, that refines the authors' claim rather than
contradicting it, and would be a genuine contribution.

### 4.5 Two cautions

**Lead-lag discipline on conditioning variables.** Intermediary stress is **contemporaneous**
with losses in this strategy (§2.7). Conditioning on stress measured at the same time partly
regresses losses on losses and produces a relationship that is not tradeable. Use **lagged**
stress to predict forward returns, and state the lag in the pre-registration.

**Each dataset multiplies the hypothesis space.** Ten sources tested against one signal is not
one test. M1–M7 are cheap *because the direction is predicted in advance*; open-ended searching
across these datasets is not, and the noise-Sharpe arithmetic in `FEATURE_RESEARCH.md` §6.1
applies to the whole family. Add a source where §2 says it should matter, not because it is
available.

### 4.6 Priority

| Rank | Item | Why |
|---|---|---|
| 1 | HKM intermediary capital ratio | Free, canonical, directly answers M4, closes the loop with the paper |
| 2 | Quarter/year-end reporting calendar | Free, derivable, sharp prediction, bridges to calendar-window strategies |
| 3 | Calendar spread liquidity from own data | Highest effort, biggest moat, most direct measure of loop gain |
| 4 | Equity index futures basis | Built in-house, daily, measures the constraint in a traded instrument; direct M7 test |
| 5 | Cross-currency basis | Built in-house, daily, independent confirmation in another market |
| 6 | Everything else | Only where §2 says it matters |

---

## 5. Pros and cons

### Pros

| | |
|---|---|
| **Distinct mechanism** | Orthogonality to hedging pressure established by the authors, not assumed |
| **No external data** | Computable entirely from futures prices — no vendor, no revisions, no point-in-time problems |
| **Inputs already required** | Carry work needs the two nearest contracts; this needs the same series |
| **Replication benchmark exists** | Internet Appendix to the JF article contains replication data — turns "did I build this right" into a correlation check rather than a judgement call |
| **Recent publication** | Less decay exposure than trend or carry |
| **Extends beyond commodities** | Solves the universe-size problem at micro-contract scale |
| **Derived conditioning variable** | "Increasing in volatility" is handed to you by the paper — no trial cost |

### Cons

| | |
|---|---|
| **Small cross-section** | High4/Low4 at 21–32 commodities; at your universe the legs are 2–3 names. Idiosyncratic risk dominates; one squeeze owns the month |
| **Cross-sectional long/short** | Likely conflicts with prop hedging rules. Time-series version required for funded accounts (§9) |
| **Data-intensive** | Clean second-nearby series is where most retail futures data quietly fails |
| **Risk-premium framing cuts both ways** | If it is compensation for intermediary-constraint risk, it loses when intermediaries are impaired — crises, deleveraging, liquidity events. **Same tail as carry.** Check drawdown correlation, not just return correlation |
| **Shorter evidence base** | One paper plus follow-ups, not a century of data across 67 markets |
| **Higher constituent turnover** | More diverse composition than basis sorts — good for diversity, worse for cost |

**The con to weight most heavily** is the tail correlation. Both carry and basis-momentum are
intermediary/liquidity-risk premia. Their *average* correlation may be low while their *crisis*
correlation is high, which is precisely the failure mode `ALPHA_PROGRAMME.md` §8.2 warns about.
This must be tested on drawdown overlap, not on full-sample correlation.

---

## 6. Implementation challenges — where the edge actually is

For a published signal, implementation quality *is* the edge. Ranked by how much difference
doing it well makes.

### 6.1 Second-nearby series construction — the primary moat

Basis-momentum is a **difference of two similar quantities**. Errors do not average out; they
enter the signal at full size. A 0.3% error in each leg is a 0.6% error in a signal whose total
content might be 1–2%.

Everyone can compute first-nearby returns. Correctly building a continuously-rolled
second-nearby **total return** series — right roll dates, right adjustment, no contamination
from the roll itself — is where most implementations break.

Requirements:
- Roll schedule for the second contract is **not** simply the first-contract schedule shifted;
  derive it explicitly and version it
- Never compute a return across a roll boundary on an unadjusted series (`FEATURE_RESEARCH.md` §2.4)
- Reconstruct the adjusted series from unadjusted prices plus roll gaps and verify it reproduces
  the vendor's — if it does not, your understanding of the adjustment is wrong
- Reconcile both legs against a second vendor over the overlap period

This is unglamorous engineering that rewards care and does not decay. It is a real barrier.

### 6.2 Roll-return decomposition

The effect is **driven by roll returns**. If your return series conflates spot return and roll
return incorrectly, you are measuring something else entirely.

Build the decomposition explicitly:
```
total return = spot return + roll return (+ collateral, if modelled)
```
and be able to demonstrate it reconciles. This is both an accuracy requirement and a good
portfolio artefact.

### 6.3 Maturity pair selection — a choice, not a parameter

The paper finds basis-momentum measured at the short end predicts near-to-expiring contracts
outperforming next month, **and** that it contains a maturity-specific component varying across
the curve.

Which pair you use changes **what you are measuring**. This is not a free parameter to sweep.

- Choose deliberately (default: first vs second nearby, matching the paper)
- State the reason in the pre-registration
- Test any alternative pair as a **separate pre-registered hypothesis** with its own trial cost
- Never report the best of several pairs as though one had been chosen in advance

### 6.4 Seasonality

Natural gas and agricultural curves have seasonal shape built in. A naive slope-change measure
picks up the calendar rather than an imbalance.

De-seasonalise properly and demonstrate the signal survives it. Fiddly enough that many
implementations skip it, which is exactly why it is a differentiator. Candidate approaches to
pre-register (pick one, do not sweep): month-of-year fixed effects on the basis series; compare
same-delivery-month contracts year over year; restrict to non-seasonal markets as a robustness
check rather than as the main test.

### 6.5 Volatility conditioning — free, derived

The effect is **increasing in volatility**. This is a conditioning variable *handed to you by
the paper*, not one found by splitting your own sample.

Fold it in as a **continuous multiplicative term** on the forecast, not as a regime gate. Costs
no trial, adds no threshold parameter, and is exactly the enhancement `FEATURE_RESEARCH.md` §7
item 5 calls for.

### 6.6 Liquidity and staleness at the second contract

The second contract is thinner than the front, in some markets substantially. **Stale
settlements in the deferred leg manufacture fake signal** — and because the signal is a
difference, a stale second leg directly injects the first leg's move into the signal.

Build an explicit staleness filter: exclude instrument-months where the second contract's
volume or open interest fell below a threshold, or where settlements repeated. Pre-register the
threshold.

### 6.7 Sector handling

Precious metals are financial assets with no meaningful convenience yield and behave
differently in commodity factor work generally. Treat separately rather than pooling —
justified by mechanism (`ALPHA_PROGRAMME.md` §9.2), not by performance.

### 6.8 Execution form

| Form | Cost | Margin | Prop-compliant |
|---|---|---|---|
| Two outrights | Higher | No offset | Depends on rules |
| Calendar spread | Lower, tighter fills | CME offsets | **Likely prohibited** |

On personal capital the spread form is clearly better. On a funded account, check the rulebook
before assuming either is available.

### 6.9 Turnover management

Constituent composition turns over more than basis sorts. Cost control matters more here than
for carry. Use **position buffering** — rebalance only when the target has moved beyond a band —
rather than rebalancing to target every period. Carver covers this well; use his approach rather
than deriving one.

---

## 7. Pre-registered tests

### 7.1 T0 — Orthogonality check (run first, before anything else)

**Not a performance test and therefore not a trial.**

Compute basis-momentum on the target universe and measure its correlation to:
- the carry signal
- the trend signal
- (later) the hedging-pressure signal

**Decision rule, set now:** if |ρ| > 0.7 against carry on your universe, the mechanism has
collapsed into an existing one at your scale and the programme stops. Costs one afternoon and
decides whether the rest is worth doing.

### 7.2 T1 — Replication, commodities

Build to the published specification on the commodity universe. Compare against the JF Internet
Appendix replication data over the overlapping period.

**Success criterion:** meaningful positive correlation with the published factor series, and a
sign and rough magnitude consistent with the paper. If this fails, the data layer is wrong —
fix that before interpreting anything.

Trial cost: **1**.

### 7.3 T2 — Extension to financials

Extend to FX and equity index micros, per the paper's finding that basis-momentum is present in
currencies and stock indexes.

Trial cost: **1**.

### 7.4 T3 — Standard feature evaluation

Push through the harness per `FEATURE_RESEARCH.md`: IC across the horizon grid, IC decay curve,
bucket monotonicity, per-year stability, turnover and break-even cost, incremental IC versus the
existing library, CPCV path distribution.

Admission criteria as in `FEATURE_RESEARCH.md` §11 — no separate standard for this.

### 7.5 T4 — Drawdown correlation with carry

Distinct from T0 and more important. Compare the **drawdown periods** of basis-momentum and
carry, not their full-sample return correlation.

**Pre-registered expectation:** because both are intermediary/liquidity-risk premia, crisis
drawdowns will overlap more than average correlation suggests. If they overlap substantially,
the diversification benefit is smaller than the correlation figure implies, and the combined
vol target must be set accordingly.

### 7.6 Negative control

Correlation of basis-momentum to changes in COT commercial positioning should be **low**, if the
authors' claim that the effect is not hedging pressure holds. Cheap confirmation that the
mechanism is what it is said to be — and a useful line in the writeup either way.

**Total pre-registered trial budget for this programme: 2** (T1, T2). T0, T4, T5.6 are
diagnostic rather than selective. T3 is evaluation of an already-committed feature.

---

## 8. Universe

The commodity-only version at micro scale gives legs of two to three names — marginal at best.
**The extension to financials is core, not optional.**

| Sector | Instruments | Second-contract liquidity |
|---|---|---|
| Energy | MCL (+ micro gas if listed) | Good for CL; verify gas |
| Metals | MGC, SIL, MHG | Moderate; verify |
| Equity index | MES, MNQ, M2K, MYM | Quarterly cycle — second contract usable but check |
| FX | M6E, M6B, M6A, M6J | Quarterly cycle; verify deferred liquidity |
| Rates | Micro yield futures | Verify — curve structure differs |
| Agriculturals | Mini XC/XW/XK only | Poor; seasonal; likely exclude initially |

**Open question 1 — roll cycle.** Equity index and FX futures roll quarterly, so "second
nearby" is three months out rather than one. The maturity-specific component (§6.3) means this
is not automatically comparable to the commodity construction. Needs an explicit decision and a
stated rationale before T2 runs.

**Open question 2 — the financial-futures curve is a different object.** This is the more
serious one, and it must be settled before T2.

A commodity curve is a **storage** curve. An equity index curve is **financing cost minus
expected dividends**; an FX curve is an **interest rate differential**. Porting the commodity
construction across without adjustment measures something else entirely.

The specific confound, for equity index futures:

> S&P 500 concentration has risen sharply — the top 10 constituents now hold roughly 37–40% of
> index weight, against about 19% a decade ago, the highest since the mid-1960s. Mega-cap
> technology names pay **low dividends** relative to the composition they displaced. Rising
> concentration has therefore produced a **slow, one-directional structural drift in the index
> dividend yield**, and so in the curve shape.

Basis-momentum is a **cumulated change in curve shape**. A decade-long structural drift in the
dividend component would register as persistent basis-momentum that is **pure composition
artefact**, with no intermediary imbalance behind it at all. Run naively, T2 would likely return
a positive result that means nothing.

**Required before T2:** residualise the curve against expected dividends, or work in
**implied-financing-rate space** rather than raw basis, so the signal measures deviation from
fair value rather than the level of the dividend yield. Pick one, pre-register it, and state
the reasoning. The FX analogue is to work in basis-versus-covered-parity space rather than raw
forward points.

This is a genuine contribution to the construction rather than a technicality: the paper reports
the effect is present in currencies and stock indexes, but the correct way to measure a curve
whose shape is set by financing rather than storage is not obvious and is where a careless
replication will go wrong.

---

## 9. Deployment forms

| | Research / personal capital | Prop account |
|---|---|---|
| Construction | Cross-sectional long/short | Time-series |
| Signal | Rank BM across universe | BM relative to instrument's own history |
| Position | Long top, short bottom | Long if BM above own mean, short if below |
| Execution | Calendar spreads where permitted | Outright, one position per instrument |
| Compliant | N/A | Yes — no opposing positions |

The paper predicts in the time series as well as the cross-section, so the compliant form has
published support rather than being an improvised workaround. Expect it to be weaker.

Combination with existing signals follows `ALPHA_PROGRAMME.md` §6.4 — continuous forecast,
equal weights, no filtering, no thresholds.

---

## 10. Open items for the expansion

1. **Verify the exact construction** against the published paper — lookback, rolling convention,
   total-return definition, weighting within legs.
2. **Obtain the Internet Appendix replication data.**
3. **Decide the maturity pair for quarterly-cycle instruments** (§8, open question 1).
3a. **Decide how to handle the financing/dividend curve for equity index and FX** (§8, open
    question 2) — residualise against expected dividends, or work in implied-financing-rate
    space. **Blocking for T2.** Without it the equity index result is likely a concentration
    artefact rather than a signal.
4. **Choose the de-seasonalisation method** and pre-register it (§6.4).
5. **Set the staleness threshold** for the second contract (§6.6).
6. **Curvature extension** — three or four points on the curve rather than two. Natural follow-on
   given the paper's slope-and-curvature framing, but a separate hypothesis with its own trial.
7. **Capacity estimate** — how much size the second-nearby leg supports before impact eats the
   edge. Relevant to the personal-capital growth path, not to prop.
8. **Subperiod stability** — 2015 working paper, 2019 publication. Split pre-2015, 2015–2019,
   post-2019 and check for decay. This is a diagnostic, not a regime exclusion
   (`ALPHA_PROGRAMME.md` §10). **Note this test also carries M6 (§3)** — the mechanism predicts
   post-2010 *strengthening*, opposite to the decay expectation, so the result discriminates
   between the two stories rather than merely measuring decay.
9. **Design the M1–M7 mechanism tests properly** (§3, sourced in §4) — predicted directions,
   data sources, and what each outcome would imply. M4 uses the HKM capital factor (§4.1);
   M5 needs inventory series aligned point-in-time via ALFRED; M7 needs the reporting calendar
   and a pre-registered year-end-versus-quarter-end ordering (§4.2).
10. **Decide whether M6's outcome is a gate.** If the effect decayed post-2010, the
    risk-premium framing weakens and the mispricing story gains — which changes expected
    persistence and therefore whether this belongs in the book at all. Set that decision rule
    before running it.

---

## 11. Honest position

Basis-momentum is the **least-trodden** of the credible candidates and the one with the
clearest documented orthogonality to the existing programme. It is not the strongest standalone
signal available and it will not transform the book's return.

Its case rests on three things: the mechanism is distinct and stated by the authors; the inputs
are already required for other work; and the implementation difficulty is a real, non-decaying
barrier that rewards careful engineering over insight.

Its main risk is that the diversification is smaller than it looks, because both this and carry
are liquidity-risk premia that may fail together. **T4 is the test that decides whether this
earns its place**, and it should be run early rather than at the end.

**On the mechanism work in §§2–4.** The reconstruction there is not decoration and not portfolio
padding. It does three things the returns alone cannot: it makes the orthogonality claim
checkable rather than borrowed (§2.9), it converts "increasing in volatility" from a discovered
regime into a free derived term (§2.8), and it generates M1–M7 — seven tests of the *mechanism*
that cost no selection budget and would each be informative whatever the answer.

M6 in particular is the kind of test that distinguishes understanding from replication: a
prediction that runs *against* the default expectation, made in advance, where either outcome
teaches something. Testing a published effect's mechanism rather than its returns is a rare
thing to find in a portfolio, and it is worth writing up on that basis even if the feature is
ultimately rejected.

---

## 12. Sources

- Boons, M., Prado, M.P. (2019). "Basis-Momentum." *Journal of Finance* 74(1), 239–279. DOI 10.1111/jofi.12738. Internet Appendix contains replication data.
- Boons, M., Prado, M.P. (2015). "Basis-momentum in the futures curve and volatility risk." SSRN 2587784 — earlier working version.
- Adrian, T., Etula, E., Muir, T. (2014) — intermediary leverage pricing; the price-of-risk comparison the paper draws on.
- Brunnermeier, M., Pedersen, L.H. (2009); Adrian, T., Shin, H.S. (2014) — constrained-intermediary theory underpinning the mechanism.
- Qian (2025), "Factor Momentum in Commodity Futures Markets," *Journal of Futures Markets* — recent work citing basis-momentum; useful for post-publication behaviour.
- He, Z., Kelly, B., Manela, A. (2017). "Intermediary asset pricing: New evidence from many asset classes." *Journal of Financial Economics* 126(1), 1–35. Data: asaf.manela.org/data/ and zhiguohe.net.
- Du, W., Tepper, A., Verdelhan, A. (2018). "Deviations from Covered Interest Rate Parity." *Journal of Finance* — basis as a balance-sheet-constraint measure.
- NY Fed Primary Dealer Statistics — weekly dealer positions and financing, free.
- Sakkas, A., Tessaromatis, N. — "Factor Based Commodity Investing"; places basis-momentum among nine commodity sorting characteristics and notes it is not explained by storage, backwardation or hedging pressure.
