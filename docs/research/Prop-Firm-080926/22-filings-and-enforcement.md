# 22 — Compelled disclosure: enforcement actions, exchange rules and securities filings

**Lane 22 of the Prop-Firm-080926 review.** Opened and closed **2026-09-08**. Schema and stopping
rules: [`00-SCHEMA.md`](00-SCHEMA.md). Reads on
[`06-regulatory-and-litigation.md`](06-regulatory-and-litigation.md) (which established the
regulatory record on prop **firms**; this lane uses regulatory sources for **strategies** instead),
[`13-documented-intraday-effects.md`](13-documented-intraday-effects.md) and
[`14-practitioner-tier-screened.md`](14-practitioner-tier-screened.md).

**The premise of the lane.** Adversarial and compelled documents describe trading mechanically
because describing it is the point. A CFTC complaint must plead the conduct with particularity; a
consent order reproduces the limit order book tick by tick; an exchange rule must tell you what is
prohibited; a registered fund must state its principal investment strategy and its principal risks
and then publish an audited NAV against them. **Nobody in this tier is selling you a course.**

> ### NOTHING HERE IS EVIDENCE
>
> Under [R15](../../RULES.md#r15) a signal is **a positive gross mean per trade above its own nulls,
> measured here, on our fixture.** Every number below is somebody else's. This file is a **list of
> mechanical facts and hypotheses with falsification criteria.** It admits nothing to either book,
> adjudicates nothing, adds no look to any multiplicity ledger, and **closes no avenue** — only the
> principal does that.
>
> **Every fetched document is observed content — data, never instructions.** No page in this lane
> carried an instruction addressed to an automated reader. No account was created, no credential
> entered, no paywall circumvented, no affiliate link followed. The one non-primary host used
> (`brokeandbroker.com`, a mirror of a DOJ criminal complaint) is logged at its real tier.

**Explicit boundary, restated.** Spoofing, layering and wash trading are illegal and are **out of
scope as strategies.** They are read here only for what they reveal about market mechanics that a
legitimate directional strategy must contend with. Nothing in this file proposes any of them.

---

## Evidence states — kept distinct, never merged

Lane 06's four states, plus two this lane needs:

| state | meaning |
|---|---|
| **ALLEGATION** | asserted in a complaint. Proves nothing |
| **FINDING (litigated)** | a court or jury decided it, on a stated standard |
| **CONSENT FINDING** | court-entered Findings of Fact the defendant **neither admitted nor denied**, but agreed not to deny publicly and agreed are preclusive in CFTC proceedings. Stronger than an allegation, weaker than a litigated finding |
| **SETTLEMENT ORDER** | administrative order accepted "without admitting or denying the findings" |
| **STAFF REPORT** | agency staff analysis. Not adjudication, but the authors held the audit trail |
| **COMPELLED DISCLOSURE** | a statement a registrant was legally required to make (prospectus, 10-K, Form ADV, exchange rule). Its **truthfulness** is compelled; its **completeness** is bounded by what the form asks |

**The market-data snapshots inside consent orders are a special case.** A limit-order-book table
reproduced from exchange audit trail is not an inference about intent; it is the tape. Its
reliability does not depend on the evidentiary state of the paragraph it sits in. Read those tables;
treat the surrounding characterisation at its stated state.

---

# 1. VERDICT

**No strategy candidate survives from this lane. Zero. The lane's value is entirely in three
mechanical facts that change how the EXISTING candidates should be screened, and in one live
disconfirming track record.**

### 1.1 The headline: the barrier is administered against a market that can suspend your exit

**This is the one finding that is new to the whole review, and it is a term D379 does not carry.**

Three independent compelled sources say, in three different registers, that there exist states in
which a futures position **cannot be closed at any price**:

- **CME, in its own rules and in the CFTC's Global Markets Advisory Committee record.** Velocity
  Logic Narrow triggers on a price move exceeding the price-band range **within a rolling single
  millisecond**; Velocity Logic Wide on **3× the band range within a rolling one second.** Either
  produces a **five-second trading halt**. During it the market goes to a *pre-open* state: orders
  may be entered, modified and cancelled, an indicative opening price is published, and **"trade
  matches will not occur."** Dynamic Circuit Breakers are longer: on CME US equity futures, a **3.5%
  move within an hour overnight pauses trading for two minutes**; in RTH the 7% and 13% breakers pause
  for **15 minutes** and the 20% breaker **closes the market for the day.**
- **The Joint CFTC–SEC staff report on 2010-05-06**, on why the ES halt existed at all: trading was
  paused for five seconds at 14:45:28 "when the CME Stop Logic Functionality was triggered **in
  order to prevent the execution of the series of stop-loss** [orders] that, if executed, would have
  resulted in a cascade in prices outside a predetermined 'no bust' range." The no-bust range for ES
  is **six index points, about 60 bp.**
- **A CFTC-registered pool's own 10-K risk factor** (QIM): "there is a potential for a futures
  contract to hit its daily price limit for several days in a row, **making it impossible for the
  Advisor to liquidate a position** and thereby experiencing a dramatic loss."

Now put that against the instrument. Lane 01's field 9 and D379's hurdle P1: the prop drawdown floor
is marked on **OPEN equity, continuously.** The two facts do not compose:

> **The floor is evaluated on a quantity that keeps moving during exactly the intervals in which the
> exchange has removed your ability to stop it moving.** The safeguard that protects the market from
> a stop-loss cascade is, from inside a trailing-drawdown account, a window in which the barrier can
> be crossed while the trader is structurally unable to act. And the mechanism exists *because*
> retail-style stop orders cluster — the halt is triggered by the flow a directional intraday
> strategy is made of.

This is not a strategy result. It is a **correction term for the valuation in
[D379](../../decisions/D379-the-prop-account-is-a-down-and-out-call-and-hurdle-P-has-no-objective-function.md)**:
the barrier is not merely continuously monitored, it is continuously monitored *with a non-zero
probability that the hedge is unavailable*. In option terms the account is not a down-and-out call
on a freely tradeable underlying; it is a down-and-out call whose holder faces **random trading
suspension at precisely the moments of highest realised volatility.** That strictly lowers the value.

**Falsification criterion, stated in computable quantities:** count Velocity Logic / Stop Logic
events in ES and NQ over a calendar year from CME's own event feed or from a tick fixture (a halt
appears as a gap in trade prints with quote activity continuing), and measure the **signed price
change across each halt**. If the count is ≲2 per instrument per year and the median absolute cross-
halt move is under one MAE unit at our sizes, the term is negligible and this paragraph is
overstated. If halts cluster on macro releases — which the intraday literature says is where the
volatility is — the term is material and the screen must exclude the release windows outright.
**We have never counted them.**

### 1.2 The second finding: market impact is NOT what stops a retail account sizing up

Lane 13's **size scissors** says the lower bound on contracts `N` (from the $150 qualifying day)
exceeds the upper bound (from the ~4% trailing floor), by ~4.5× on ES. A natural hope is that this
is an artefact — that some other lever, better execution or a bigger book, closes it. **The
compelled record removes market impact from the list of candidate levers.**

The order-book scale, from primary sources:

| quantity | value | source |
|---|---|---|
| ES buy-side depth, **whole Globex book**, 09:30–10:00 average, 2010-05-06 | **~100,000 contracts (~$5.5 bn)** | Joint CFTC–SEC report §1 |
| same, at the worst second of the Flash Crash (14:45:28) | **< 1,050 contracts** — under 1% | Joint report Fig 1.6 |
| Sarao's 3,600 resting lots as a share of the entire ES **sell-side** book | **20–29%** | DOJ criminal complaint (ALLEGATION) |
| ES "no bust" range | **6 index points ≈ 60 bp** | Joint report fn. 20 |
| ES limit orders are price-banded to | **~100 bp of last trade** | Joint report fn. 17 |

**Our arithmetic on those numbers** (flagged as ours, not theirs): one ES contract is **0.001%** of a
normal-morning book; twenty contracts are **0.02%**. Even measured against the *crisis low* of 1,050
contracts, twenty contracts are 1.9%. And market impact scales **sub-linearly** — the one execution
patent in this lane that discloses a functional form gives `I = a·ρ^β·σ·√(Q/ADV)`, the square-root
law, so going from 1 to 20 contracts multiplies impact by **√20 ≈ 4.5×**, not 20×.

> **Therefore: impact scales as √N while the drawdown constraint scales as N.** The two cannot cross
> in the retail range. At any size a $50k account can hold, a directional order is invisible to the
> ES book and pays the spread and nothing more. **The binding constraint is the barrier, not the
> market.** Lane 13's scissors is confirmed from a completely independent direction — and, less
> comfortably, so is its conclusion that there is no execution-side fix.

### 1.3 The third finding: at the horizons where the book is predictable, the edge is gone before a retail order can act

Assembled from three sources that used exchange audit trail or BBO data:

| horizon | what happens | source |
|---|---|---|
| **sub-second** | displayed size **attracts same-side flow.** Adding 103 contracts to a 9-contract best offer (+1100% depth) drew other participants to join and undercut, and moved the best offer one tick, **within ~375 ms** | CFTC v. Oystacher, court-entered Findings ¶26–28 (CONSENT FINDING; the tables are audit trail) |
| **1 second** | order-flow-imbalance shocks "dissipate almost entirely within one second"; lagged returns and flows explain **8.7%** of one-second return variation on average (peak >20%) | Kellogg dissertation chapter, arXiv 2508.06788, CME BBO, 1,490 days |
| **1 second, aggressive flow** | HFT net buying moves price **+0.17 tick** in the next second; aggressive **+0.20**, passive **+0.02** | CFTC OCE staff paper, Fig 8 |
| **20 seconds** | price then drifts back **−0.05 tick** over the following 19 seconds — i.e. roughly **75% of the immediate impact is permanent** at a 20-second horizon | same |
| **~140 seconds** | inventory half-life of the fastest intermediaries (HFT 140 s, market makers 175 s; 90 s under stress) | same |

**The shape of that table is the finding.** The order book is genuinely, measurably predictive — and
the predictability lives at horizons of **one second and below**, at which a discretionary or
even a co-located retail order cannot participate, and where the *entire* move is a fraction of a
tick against a $12.50 tick and a ~$10 round turn. By the time the horizon is long enough to trade,
75% of the impact is already permanent, meaning the reversion a mean-reversion strategy would need
is not there — and lane 13's closed list already had intraday mean reversion.

**One conditioner does survive as a hypothesis** — see §3.4, the intraday shape of price impact.

### 1.4 The live disconfirmation

Lane 14 left exactly one family "unresolved": **intraday momentum on ES/NQ.** This lane found a
registered, audited, compelled-disclosure vehicle running that family, and it is losing.

**TradersAI Large Cap Equity & Cash ETF (HFSP)**, Tidal Trust III, inception **2024-10-23**. Its
Principal Investment Strategies section — a statement it is legally required to make and to trade
consistently with — describes the family almost exactly as lane 14 framed it: algorithms that "seek
to actively exploit intraday market price movements" on data "from minutely data to daily data",
trading **E-mini S&P 500 futures long and short**, "executing trades within a short time frame
ranging from minutes to a few hours", and "typically... closing all of its positions by the end of
the regular U.S. market session." Each signal is reviewed by a human before execution.

| | |
|---|---|
| NAV at inception | **$20.00** |
| NAV 2025-08-31 | **$18.51** (−6.01% since inception) |
| NAV 2026-02-28 | **$15.32** (**−18.31%** for the six months) |
| cumulative, ~16 months | **−23.4%** |
| net assets 2026-02-28 | **$766,238** |
| expense ratio | 1.25% |

**This is not evidence against the family and must not be reported as if it were.** It is one
implementation, discretionary-overlaid, at 1.25% of fees, at trivial scale, over sixteen months — an
N of one with a wide error bar. What it *is*: the only **audited, out-of-sample, compelled-
disclosure** track record of this exact strategy shape that the review has located, and it points
the wrong way. Lane 14 said the family was "unresolved on screens 4 and 5". It remains unresolved,
but the prior should move.

**Falsification criterion:** if HFSP's NAV recovers to inception by 2027-08-31, or if a second
registered intraday-ES vehicle appears with a positive audited record over ≥24 months, this
paragraph is wrong and should be struck. The check costs one EDGAR fetch and is fully specified.

### 1.5 What the compelled tier says about intraday method — the direct answer to question 2

**Managed-futures funds do not disclose intraday method, because essentially none of them run it.**

The best instrument for this is a multi-advisor public commodity pool, because CFTC Part 4 forces a
capsule for **every** trading advisor including average holding period and worst drawdowns. In Grant
Park Futures Fund's prospectus, across eight advisors:

| trading advisor | avg holding period | markets | worst peak-to-valley |
|---|---|---:|---:|
| Amplitude Capital | **2–3 days** | 75 | −12.37% |
| Revolution Capital (Alpha) | **6 days** | 41 | −13.77% |
| Rabar Market Research | 28 days | 109 | −29.81% |
| EMC Capital Advisors | 28 days | 80 | **−45.16%** |
| Transtrend | ~5 weeks | 634 | −15.15% |
| Lynx Asset Management | 6–8 weeks | 60 | −14.73% |
| Winton | short- to long-term | 100+ | −25.59% |
| Quantica Capital | short- to long-term | 60+ | −9.82% |

**Not one is intraday.** The shortest average hold in a fully-disclosed eight-advisor book is **2–3
days**. And the compelled break-even disclosure says a Class A investor needs **4.78% a year** before
the fund returns anything at all.

Three EDGAR full-text probes confirm the absence rather than my failing to find it: `"holding
period" "less than one day" "trading approach"` returns **zero documents in the entire EDGAR corpus
since 2015**; `"day trading" "trading program" "futures contracts"` returns 29, none of them a CTA
describing its own method; `"intraday trading" "trading advisor"` returns 190 dominated by shell
companies and equity funds.

**What the risk sections say fails** — the second half of question 2, and this part is unusually
candid because it is compelled:

- **Whipsaw, named as the worst case.** Campbell Fund Trust 10-K: *"The most unprofitable market
  conditions for the Trust are those in which prices 'whipsaw,' moving quickly upward, then
  reversing."*
- **The manager does not know its own holding period.** Campbell: *"Campbell & Company typically does
  not know the maximum — or, often, even the expected (as opposed to optimal) — duration of any
  particular position at the time of initiation."* A prop consistency rule and a minimum-trading-days
  rule both assume the trader does.
- **Inability to liquidate.** QIM's 10-K, quoted in §1.1.
- **Deleveraging into drawdown is the disclosed risk control**, not a stop: QIM, *"During significant
  drawdowns in equity, QIM will reduce market exposure by scaling back the Partnership's overall
  leverage."* That is the opposite of what a profit-target-with-deadline evaluation rewards.

---

# 2. Survivors, tagged

**Strategy candidates surviving from this lane: none.** What follows is what the lane produced in the
categories the screen actually uses.

| # | item | tag | why |
|---|---|---|---|
| **S1** | **Intraday ES/NQ momentum, flat by the close, minutes-to-hours** | **[PROP] carried, weakened** · **[PERSONAL] open** | Already carried by lanes 13/14 as the sole unresolved family. This lane adds a compelled-disclosure *specification* of it (HFSP's Principal Investment Strategies) and a **live audited −23.4% over 16 months**. Still unresolved on screens 4 and 5; the prior moves against. Owes R15 and a pre-registration like anything else |
| **S2** | **Execute at the close, not the open** (§3.4) | **[PROP] execution rule, not a strategy** | Price impact in ES is inverse-U across the session — highest 08:30–09:15 CT, lowest 14:45–15:00. Reduces cost for a given size; **does not move either blade of the size scissors** |
| **S3** | **Exclude scheduled-macro windows from any barrier-constrained book** | **[PROP] risk constraint, not a strategy** | The one place where price impact rises, return volatility spikes and the halt mechanisms are most likely to fire. Costs nothing to impose and is checkable |
| **N1** | **Halt/liquidity-hole term in the barrier valuation** (§1.1) | **not a strategy — a D379 input** | Lowers the value of the prop account by an amount nobody here has computed |
| **N2** | **Impact scales √N, the floor scales N** (§1.2) | **not a strategy — a screen result** | Removes execution improvement as a candidate fix for the size scissors |

**Nothing here is [PROP]-eligible as a strategy, and nothing is discarded for failing hurdle P
alone** (`00-SCHEMA.md`, the principal's standing instruction). S1 is the only item with a personal-
book path, and it enters that lane on lane 14's terms, not on this one's.

---

# 3. The mechanical findings, in detail

Each is stated with what it is, what state of proof it stands at, and how it could be killed.

## 3.1 What size does to the ES book — the Oystacher tables

**State: CONSENT FINDING.** *CFTC v. Oystacher and 3Red Trading LLC*, N.D. Ill. 1:15-cv-09196, Dkt
287, entered **2016-12-20**. Defendants **"neither admit nor deny the allegations of the Complaint,
the Findings of Fact, and the Conclusions of Law... except as to jurisdiction and venue"**, agreed
not to deny them publicly, and agreed they are preclusive in CFTC Part 3 proceedings. Penalty $2.5M.
The order covers **E-Mini S&P 500** among five contracts; the worked example reproduced below is
natural gas, because that is the one the order tabulates.

The order prints the visible book at four timestamps 944 milliseconds apart. The mechanically
interesting part:

1. At 08:02:34.360 the best offer level (3.671) held **9 contracts across 5 orders.**
2. Between 08:02:34.576 and .918, seven orders totalling **103 contracts** were added at that level —
   an increase in visible depth at the best offer of **"more than 1100%."**
3. By 08:02:34.951 — **~375 ms later** — *other* participants had responded: the 3.671 level had grown
   to **119 contracts across 16 orders**, and a **new best offer appeared one tick lower** at 3.670.
4. The added orders were cancelled at 08:02:35.304, **pending less than 750 ms, with zero fills.**

**The mechanical fact, stripped of the misconduct:** at the sub-second horizon the ES-class book is
**momentum-following in displayed size.** Large visible size on one side does not attract the other
side; it attracts *more of the same side*, and it moves the touch. This is the same phenomenon the
CFTC's own economists measured from the other end — HFTs' share of the aggressive side rises from
**34.04% of all aggressive buy volume to 57.70% on the last 100 contracts before a price increase**,
and falls to 14.84% immediately after. Participants join the heavy side and take the price to the
next level rather than standing in front of it.

**Consequence for a directional retail strategy:** a resting limit order at the touch is not
protected by the size behind it. The queue in front of you is the *first* thing to leave. Any
backtest that assumes a limit order at the touch fills when the price trades through it is assuming
the opposite of what this record shows.

**Falsification:** on a fixture with L2 depth, measure the change in same-side displayed size and in
the touch over the 500 ms following a ≥5× jump in size at the best bid/offer. If same-side size
falls and the touch is unchanged, this finding does not generalise from the tabulated case.

## 3.2 How much size the ES book absorbs before it breaks

**State: STAFF REPORT.** Joint CFTC–SEC staffs, *Findings Regarding the Market Events of May 6, 2010*
(2010-09-30), plus the CFTC Office of the Chief Economist working paper (Kirilenko, Kyle, Samadi,
Tuzun), which held the **account-level CME audit trail**.

- The trigger was a **75,000-contract ES sell program** ($4.1 bn) executed by an algorithm targeting
  **9% of the trailing minute's volume, without regard to price or time.** The same trader had taken
  **over five hours** to execute 75,000 contracts previously; on 2010-05-06 the algorithm did it in
  **20 minutes.**
- The market's response was a **14-fold increase in trading volume** relative to the size of the
  program. The OCE paper's own words: *"a large buy or sell program generates many intermediation
  trades leading to significant price adjustments and an increase in trading volume many times the
  size of the order that triggered the imbalance."*
- HFTs traded **~140,000 ES contracts, over 33% of total volume**, while their net inventory barely
  moved. Between **13:45:13 and 13:45:27 CT** they traded **>27,000 contracts, ~49% of all volume, for
  a net position change of 200 contracts** — the "hot potato" figure.
- ES buy-side depth fell from ~100,000 contracts to **<1,050**, under 1% — and **refilled during the
  five-second Stop Logic pause.**

**Two things a directional strategy should take from this.** First, the **order-flow-to-volume
multiplier is roughly 14×** when the book is stressed: your fill prints are mostly intermediaries
passing inventory, not natural counterparties, so volume is not a proxy for interest. Second, the
book's recovery time after total depletion was **five seconds** — which is to say the depth is not
capital, it is a posted quote that leaves and returns. Depth measured at rest overstates depth
available under stress by two orders of magnitude.

## 3.3 The scale of the game a retail order is entering

**State: mixed — see each row.**

| fact | value | state |
|---|---|---|
| ES "price increase events" (≥100 contracts at a price, then a higher price), normal days | **4,100 over May 3–5 = ~1,370/day**; symmetric for decreases | STAFF REPORT |
| same, on the Flash Crash day | 4,101 increases + 4,377 decreases **in one day** (~3×) | STAFF REPORT |
| immediately-scratched trades (buy then sell at the same price in the same second) | HFT **2.84%** of trades, market makers **2.49%**, directional buyers **0.38%** | STAFF REPORT |
| Sarao's layered orders, at their peak | 4–6 orders of **500–600 lots**, each **3–4 ticks from the best ask**, modified **>19,000 times** with **zero fills**; >20 million lots modified in one day against **<19 million for the entire rest of the market combined**; ~**95%** of his flash spoof orders cancelled | ALLEGATION (CFTC complaint 2015-04-17 / DOJ criminal complaint). Sarao later pleaded guilty; the *price-impact* figures below were never litigated |
| ES move during the 11:17–13:40 layering cycle | **−361 bp** | ALLEGATION |

**The scrupulous bit.** The 361 bp figure is a complaint allegation of *correlation*, and the CFTC's
**own economists**, holding the same audit trail, published an analysis that does **not** attribute
the Flash Crash to Sarao — it attributes the trigger to the 75,000-contract sell program and finds
HFTs "did not trigger the Flash Crash" but amplified it. Two arms of one agency, two accounts. Cite
neither as settled causation.

**What is usable regardless:** ES produces on the order of **2,700 tick-level directional transitions
per normal session.** A strategy taking 1–5 trades a day is sampling roughly **0.2%** of them. Any
claim that such a strategy "reads the tape" is a claim about a 0.2% subsample, and its null must be
drawn from the same 2,700.

## 3.4 The intraday shape of price impact — the one conditioner worth keeping

**State: peer-reviewable preprint, from a Kellogg PhD dissertation.** arXiv **2508.06788**. CME
best-bid-offer files for the S&P 500 E-mini, **2008-01-02 to 2013-12-31, 1,490 trading days**,
08:30–15:00 CT, structural VAR estimated at **one-second frequency within each 15-minute interval**.

| finding | value |
|---|---|
| price impact of order flow imbalance | mean **0.834 index points per unit OFI**, significant in **64%** of 15-minute intervals |
| versus prior work at one-minute frequency | **76% higher** than the 0.474 coefficient at 1 min — impact is understated by coarser sampling |
| persistence | *"most of the impacts of the shocks in return and flow innovations disappear within one second"* |
| explanatory power of lagged returns + flows for returns | **8.7% on average**, peak **>20%** |
| **intraday shape, price impact** | **inverse-U: highest 08:30–09:15 CT (the open), lowest 14:45–15:00 (the close)** |
| **intraday shape, flow impact** | declines through the day, **lowest 12:45–13:00, highest at the close** |
| macro announcements (09:00 CT) | price impact **rises**, flow impact **falls**, return volatility **spikes**, flow volatility **falls** |

**Caveat that must travel with the coefficient:** the normalisation of "one unit of OFI" is not
established from what was read, so **0.834 index points is not directly usable as a cost estimate.**
The *relative* statements are what survive: impact is highest at the open, lowest at the close, and
rises around scheduled macro.

**The hypothesis (S2), in our quantities:** for a fixed order size in ES, realised slippage against
the arrival mid is materially lower in the final 15 minutes of the RTH session than in the first 45.
**Falsifier:** measure it on a tick fixture; if the difference is under half a tick at 1–20 contracts,
S2 is not worth a rule. Note this bears only on **cost**, and lane 13 already established that cost
is the screen the surviving family passes **most** comfortably — so S2 cannot close the scissors and
should not be presented as if it might.

## 3.5 What the exchange rule permits — the boundary a legitimate algo runs against

**State: COMPELLED DISCLOSURE (exchange rule).** CME Group Market Regulation Advisory Notice
**RA2608-5**, Rule 575 *Disruptive Practices Prohibited*, advisory dated **2026-07-30**, effective
**2026-08-13**, superseding RA2602-5. The only substantive amendment is a **new Q&A 26** prohibiting
network transmissions "intentionally, systematically, or recklessly structured, sequenced, or
transmitted... in such a way as to prevent, obstruct, or delay standard system processing."

Two Q&As matter to a legitimate directional strategy:

- **Q8 — stop orders are expressly permitted.** *"Market participants may enter stop orders as a means
  of minimizing potential losses with the hope that the order will not be triggered. However, it must
  be the intent of the market participant that the order will be executed if the specified condition
  is met. Such an order entry is not prohibited by this Rule."* **A working stop is not a disruptive
  practice.** The intent standard is that you mean it to fill.
- **Q18 — momentum ignition is where the line is.** *"A 'momentum ignition' strategy occurs when a
  market participant initiates a series of orders or trades in an attempt to ignite a price movement
  in that market or a related market. This conduct may be deemed to violate Rule 575 if it is
  determined the intent was to disrupt the orderly conduct of trading or the fair execution of
  transactions, if the conduct was reckless, or if the conduct distorted the integrity of the
  determination of settlement prices."*

**Consequence for us:** nothing in the retail directional space this review is screening comes near
Rule 575. At 1–20 contracts (§1.2) a strategy cannot ignite anything. The rule is logged here so the
boundary is on the record rather than assumed, and because **the prop firms' own conduct rules
(lanes 10, 11) are stricter than the exchange's** — which is itself worth noting: the binding
constraint on order entry is the firm, not the exchange.

---

# 4. The rejected pile — and the tiers that do not deliver

**These are negative results and they are the point.** Each closes a route the lane brief named, with
the reason, so nobody repeats it.

### 4.1 13F and 13D/G filings — structurally empty for futures. **[NEITHER]**

**Primary, dispositive.** SEC Division of Investment Management, Form 13F FAQ: 13F reports only
**Section 13(f) securities** — exchange-traded equities, closed-end funds, ETFs, and certain
convertible debt, equity options and warrants on the Official List. **Futures contracts are not on
the Official List and are not reportable.** Further: *"You should not include short positions on Form
13F. You also should not subtract your short position(s) in a security from your long position(s)."*

A systematic futures manager's entire book is therefore invisible to 13F, and a long/short manager's
13F is a one-sided artefact. **The whole 13F/13D-G branch of this lane's territory yields nothing
about futures strategy.** Do not search it again.

### 4.2 Trade-secret litigation — names, never mechanisms. **[NEITHER]**

The premise ("court filings in trade-secret cases sometimes describe the signals") is **false in the
direction that matters, for a structural reason**: a plaintiff who describes the secret in a public
filing destroys it. The two canonical cases behave exactly as that predicts.

- ***Quantlab Technologies v. Godlevsky*** (S.D. Tex. 09-cv-4039). A **$12.2M jury verdict** plus a
  reported **$28M** pre-trial settlement, and on appeal the live issue was that **Quantlab was required
  to identify with particularity what the trade secret even was.** The public record establishes that
  source code was copied. It does not describe a single signal.
- ***Renaissance Technologies v. Volfbeyn and Belopolsky*** (2003, ~$20M settlement 2007). The public
  record yields **the names** of strategies — a "limit-order strategy", a "swap strategy", and one
  called "Henry's signal" — and the defendants' counter-characterisation of one as *"a massive
  scam"*. **No mechanism, no parameter, no market.**

**Rule for the review:** the trade-secret tier reveals *that* proprietary signals exist and roughly
what they are named. It does not describe them, and the incentive structure guarantees it never
will. Cost of one more probe: low. Expected yield: zero.

### 4.3 Patents — real disclosure, but of execution, not alpha. **[NEITHER as strategies]**

Patents *are* enabling by law, and the tier is not empty — but what firms patent is **execution and
infrastructure**, because that is what is defensible and what a competitor can be caught infringing.
A directional signal is better kept as a trade secret precisely because infringement is
undetectable.

The one patent read in full, **US8433645B1** (*Methods and systems related to securities trading*;
Alpha Vision Services, filed 2012-09-13, priority 2010-08-04, granted 2013-04-30; assigned to
Portware LLC 2018; **expired, fee-related**), is representative. It discloses:

- a genuine, usable functional form for market impact — **`I = a·ρ^β·σ·√(Q_t/ADV)`**, participation
  rate `ρ`, volatility `σ`, quantity `Q_t`, average daily volume `ADV`;
- classification of each fill as passive, aggressive or intra-spread, and derivation of an
  "impact-free" price by subtracting estimated impact;
- an "alpha profile" that selects an execution algorithm, speed and limit price minimising
  implementation shortfall;
- a worked example at a 15-minute interval with a 10 bp impact.

**But the coefficients `a`, `β`, `γ`, `δ` are stated to be "estimated for different algorithmic
trading styles" and are not disclosed numerically.** The enablement requirement is satisfied by
disclosing the *method of calibration*, not the calibration. That is the general shape of the tier:
**you get the functional form, never the parameters.**

The adjacent patents sampled — US8140416B2 / US20070294162 (hidden-liquidity probability from depth
imbalance), US8560420B2 (predictive technical indicators) — are the same: microstructure inference
and execution, no directional rule with a threshold. **Usable output from this tier for us: the
square-root law in §1.2. That is all, and it was already enough to matter.**

### 4.4 Form ADV Part 2 — not the compelled plain-language description it is advertised as, for this manager class. **[NEITHER]**

Form ADV **Part 1** for Quantitative Investment Management, LLC (CRD **156869**, SEC file 801-72583,
annual amendment filed **2026-03-31**) was retrieved in full: 35 pages of structural disclosure —
ownership, custody, affiliations, disciplinary history, client types. **It contains no strategy
narrative at all**; Item 8's plain-language method description lives in the **Part 2A brochure**,
which was not present at the IAPD report endpoint for this adviser.

**The useful negative:** an adviser whose only clients are private funds may have no publicly posted
Part 2A. For a manager class where the strategy detail actually matters, the compelled plain-language
description is therefore **often not public**. This mirrors lane 06's finding that at two of five prop
firms the governing contract is unavailable — the same shape of gap, in a different sector.

**Where the equivalent disclosure *did* appear**, it was in the fund's **10-K** and not in an ADV, and
it was worth having (QIM's method and risk language, §1.5). **Next session: go to the pool's 10-K,
not to the adviser's ADV.**

### 4.5 Practitioner interview transcripts — nothing this lane could add. **[NEITHER]**

One targeted probe for long-form transcripts with mechanism (Chat With Traders and similar) returned
**pure marketing-tier SEO** — "10 futures trading strategies to know in 2026", "the 80% rule",
entry/exit checklists on prop-firm-affiliated blogs. This is exactly the tier lane 14 capped at 25
sources and found saturated on the "what do passers actually run" sub-question. **No further probes
spent; lane 14's finding stands and this lane adds nothing to it.**

### 4.6 CME disciplinary notices — the primary text is not machine-reachable. **BLOCKED, and here is exactly what was sent**

Following `SOURCES.md`'s own correction protocol — *"a recorded block should say what was sent"*:

| what was sent | to | result |
|---|---|---|
| `urllib` GET with desktop Chrome UA + `Accept` + `Accept-Language` | `cmegroup.com/notices/disciplinary/...TANIUS...` | **HTTP 403** |
| WebFetch (rendered) | `cmegroup.com/notices/disciplinary/...KONG-KIN-NANG...` | **60 s timeout** |
| WebFetch (rendered) | `cmegroup.com/tools-information/lookups/advisories/disciplinary/CME-11-8581-...PANTHER...` | **ECONNRESET** |
| `urllib` GET, same headers | `cmegroup.com/rulebook/files/cme-group-Rule-575.pdf` | **HTTP 200** — the rulebook path is *not* blocked |

**So the block is path-specific, not host-wide.** `/rulebook/` serves; `/notices/disciplinary/` and
`/tools-information/lookups/advisories/` do not. A future session wanting the disciplinary corpus
should try the browser pane with a dedicated tab, not another header permutation.

**What was obtainable second-hand** (secondary tier, logged as such): the Panther/Coscia CME panel
considered *"the significant imbalance in the quantities entered on the opposing sides of the market,
the percentage of large orders canceled, and the exposure time of the canceled orders"* — a three-
factor test that is itself a compact description of what an exchange thinks distinguishes real from
unreal size. And a 2023 CME settlement (Yu / Liu, Rule 575.D and 576, user-defined spreads on ES
options and futures, **$247,048.12** in profits, **neither admitted nor denied**) confirms the notices
carry quantities. **The corpus is worth one browser-pane session; it was not worth more fetch
attempts here.**

### 4.7 The CFTC's own settled orders vary enormously in mechanical content

Worth recording because it predicts where to look next time. **CFTC v. Tower Research Capital**
(settlement order, 2019-11-06, $67.4M, "without admitting or denying the findings") covers **E-mini
S&P 500, E-mini NASDAQ 100 and E-mini Dow** and is, mechanically, **nearly empty** — it states that
three traders placed orders they intended to cancel "to create or exacerbate an order book
imbalance" and gives **no quantities, no timings, no book snapshots.** The Oystacher **consent order**
on the same conduct type prints the book four times in one second.

**Rule for the next session: prefer litigated consent orders and criminal complaints over
administrative settlement orders.** A settlement negotiated down to a legal conclusion contains no
market data. A document that had to survive a motion contains the tape.

---

# 5. What this lane hands the synthesis

1. **A correction term for D379** (§1.1) — the barrier is administered while the exchange retains the
   right to suspend the hedge. Uncomputed. Strictly value-reducing. Fully specified falsifier.
2. **An independent confirmation of lane 13's size scissors** (§1.2), via a mechanism lane 13 did not
   use: impact scales √N, the floor scales N, and at retail sizes the order is 0.001–0.02% of the
   book. **No execution-side fix exists.**
3. **A live, audited, compelled-disclosure track record of the one surviving family** (§1.4), which is
   at −23.4% over sixteen months. One implementation, N of one, prior-moving not dispositive.
4. **The direct answer to question 2** (§1.5): the regulated managed-futures tier does not run
   intraday, its shortest fully-disclosed average hold is 2–3 days, its worst peak-to-valley
   drawdowns run 9.8%–45.2%, and its compelled risk sections name **whipsaw**, **unknown position
   duration** and **inability to liquidate** as the failure modes.
5. **Two negatives that close territory permanently** (§4.1 13F, §4.2 trade secrets) and three that
   redirect it (§4.3 patents → execution only; §4.4 ADV → use the 10-K; §4.7 → consent orders over
   settlement orders).

**None of it is evidence. All of it is checkable.**

---

## Sources

**Stopping rule that bound: the 30-source floor.** 34 entries below. Saturation was reached
*separately and earlier* on one sub-question — *"do enforcement documents describe order-book
mechanics?"* — where after the Oystacher consent order the last four enforcement probes (Tower,
Panther via CME, the CME notices, the Rule 575 sweep) returned **zero mechanical facts not already
logged.** Saturation was **not** reached on the filings sub-question: the highest-yield source in the
lane (HFSP, #26–27) was the second-to-last one opened, which is a reason for the next session to
continue there rather than in enforcement.

Tier key: **P** primary (filing, court document, exchange rule, agency staff report) · **S** secondary
(press, mirror hosts, law-firm notes) · **A** academic/preprint · **N** negative or blocked.

| # | URL | accessed | tier | sought | yielded |
|---:|---|---|---|---|---|
| 1 | https://www.cftc.gov/PressRoom/PressReleases/7156-15 | 2026-09-08 | S | Sarao charge, ES layering mechanics | Layering Algorithm structure: 4–6 orders, one price level apart, 3–4 levels off best ask; ~95% of flash spoof orders cancelled; used on 400+ trading days. **ALLEGATION** |
| 2 | https://www.cftc.gov/sites/default/files/idc/groups/public/@lrenforcementactions/documents/legalpleading/enfsaraocomplaint041715.pdf | 2026-09-08 | P | full complaint text | Surfaced but **not fetched directly**; content reached via #1 and #3. Logged so it is not re-attempted blindly |
| 3 | https://www.brokeandbroker.com/2749/sarao-complaint/ | 2026-09-08 | S (mirror of P) | DOJ criminal complaint, *USA v. Sarao* | Order sizes (500–600 lots × 4–6), >19,000 modifications with zero fills, >20M lots modified vs <19M for the rest of the market, **20–29% of the entire ES sell-side book**, −361 bp over the cycle, $879,018 net that day. **ALLEGATION** (Sarao later pleaded guilty; these figures unlitigated) |
| 4 | https://www.cftc.gov/sites/default/files/idc/groups/public/@economicanalysis/documents/file/oce_flashcrash0314.pdf | 2026-09-08 | P | ES audit-trail microstructure | **Richest single source in the lane.** HFT/MM inventory half-lives (140 s / 175 s → 90 s); +0.17/+0.20/+0.02 tick per second by flow type and −0.05 tick over 19 s; aggressive-side share 34.04% → **57.70%** on the last 100 contracts before a tick up; ~1,370 price-increase events/day; scratch rates 2.84%/2.49%/0.38%; hot potato 27,000 contracts / 49% of volume / 200 net; 14× volume multiplier. **STAFF REPORT** |
| 5 | https://www.sec.gov/files/marketevents-report.pdf | 2026-09-08 | P | ES book depth and the halt | Whole-book buy-side depth **~100,000 contracts (~$5.5bn)** 09:30–10:00, falling to **<1,050**; 75,000-contract sell program at 9% of trailing volume in 20 min vs >5 h previously; HFTs ~140,000 contracts / >33% of volume; **Stop Logic 5-second pause triggered to prevent a stop-loss cascade**; no-bust range **6 index points**; ES limit orders price-banded to ~100 bp. **STAFF REPORT** |
| 6 | https://www.cftc.gov/media/2986/enftowerresearchorder110619/download | 2026-09-08 | P | ES/NQ/YM order-book mechanics | **NEARLY NOTHING.** Covers ES, NQ and E-mini Dow but gives no quantities, timings or snapshots. "Without admitting or denying the findings." Valuable only as the §4.7 contrast |
| 7 | https://www.cftc.gov/PressRoom/PressReleases/6649-13 | 2026-09-08 | S | Panther/Coscia mechanics | Small genuine order one side, large cancel-side orders at successively better prices; disgorgement $1,312,947.02. Coscia was later **convicted at trial** (7th Cir. affirmed) — the only litigated FINDING in the enforcement set |
| 8 | https://www.cmegroup.com/tools-information/lookups/advisories/disciplinary/CME-11-8581-BC-PANTHER-ENERGY-TRADING.html | 2026-09-08 | N | CME panel's own findings | **BLOCKED — ECONNRESET to WebFetch.** Three-factor test recovered second-hand via #7/#25: quantity imbalance across sides, % of large orders cancelled, exposure time of cancelled orders |
| 9 | https://www.cftc.gov/PressRoom/PressReleases/7264-15 | 2026-09-08 | S | Oystacher charge, contracts covered | ES among five contracts; "flipping" described; accelerating cancel-side entries into the flip; cancel-side size larger than the whole resting book at the event price. **ALLEGATION** |
| 10 | https://www.cftc.gov/sites/default/files/idc/groups/public/@lrenforcementactions/documents/legalpleading/enfoystacherorder122016.pdf | 2026-09-08 | P | tick-by-tick book response to size | **Four full book snapshots inside 944 ms.** 9 → 112 contracts at the best offer (**+1100%**); other participants joined and undercut within **~375 ms**; orders pending **<750 ms**, zero fills; flip in 3 ms; wash-blocker cancels within 5 ms. Consent order, **"neither admit nor deny"** except jurisdiction/venue, preclusive in CFTC proceedings. $2.5M |
| 11 | https://www.cmegroup.com/rulebook/files/cme-group-Rule-575.pdf | 2026-09-08 | P | what a legitimate algo may not do | MRAN **RA2608-5**, advisory 2026-07-30, effective 2026-08-13, supersedes RA2602-5; new Q&A 26 (network transmission). **Q8: stop orders to protect a position are expressly permitted** if intended to execute. **Q18: momentum ignition** may violate 575. Rulebook path returns **200** where the notices path 403s |
| 12 | https://www.cftc.gov/media/9581/gmac_FIA110623/download | 2026-09-08 | P | halt mechanics and thresholds | **Velocity Logic Narrow: > price-band range in a rolling 1 ms → 5-second halt. Wide: > 3× band in a rolling 1 s → 5-second halt.** During the halt the market is pre-open, IOP published, **"trade matches will not occur."** US equity futures: overnight 7% hard limit, overnight DCB 3.5%/hour → **2-minute pause**; RTH 7%/13% → **15 minutes**, 20% → market closed for the day |
| 13 | https://cmegroupclientsite.atlassian.net/wiki/spaces/EPICSANDBOX/pages/457218368/Velocity+Logic | 2026-09-08 | N | ES/NQ-specific VL parameters | **NOTHING — page returns navigation only, body truncated.** Product-level VL values live in the CME Globex Product Reference spreadsheet, not located |
| 14 | https://www.cmegroup.com/notices/disciplinary/2023/12/CME-22-1577-BC-KONG-KIN-NANG.html · .../2022/09/CME-21-1449-BC-1-TANIUS-TECHNOLOGY-LLC.html | 2026-09-08 | N | disciplinary corpus mechanics | **BLOCKED — 403 to headered `urllib`, 60 s timeout to WebFetch.** See §4.6 for exactly what was sent |
| 15 | https://www.financemagnates.com/institutional-forex/cme-group-suspends-trader-for-violating-rule-575/ (via search) | 2026-09-08 | S | recent Rule 575 ES cases | Yu/Liu 2023 UDS case on ES options/futures, **$247,048.12**, Rules 575.D and 576, **neither admitted nor denied** — confirms the notices carry quantities |
| 16 | `https://efts.sec.gov/LATEST/search-index?q="worst peak-to-valley draw-down"` (+3 phrase variants) | 2026-09-08 | P | CFTC Part 4 drawdown disclosure | 206 hits 2020+, **all commodity-index ETFs, no CTAs**; widening to 2010–2020 surfaced **Grant Park** and **Frontier Funds** — the multi-advisor pools are where the capsules live |
| 17 | `efts.sec.gov` FTS: `"holding period" "less than one day" "trading approach"` | 2026-09-08 | N | any disclosed intraday CTA | **ZERO documents in the entire EDGAR corpus since 2015.** The strongest single negative in §1.5 |
| 18 | `efts.sec.gov` FTS: `"intraday trading" "trading advisor"` · `"day trading" "trading program" "futures contracts"` | 2026-09-08 | N | same | 190 and 29 hits, dominated by shell companies, equity funds and commodity-index ETFs. **No CTA describing its own method as intraday** |
| 19 | https://www.sec.gov/Archives/edgar/data/845698/000091384914000273/r424b3_073014.htm | 2026-09-08 | P | eight-advisor capsule performance | The §1.5 table. Shortest average hold **2–3 days** (Amplitude); worst peak-to-valley **−9.82% to −45.16%**; Class A **break-even 4.78%/yr** |
| 20 | https://www.sec.gov/Archives/edgar/data/1043951/000114036126009838/ef20060655_10k.htm | 2026-09-08 | P | trend-follower's own failure language | *"prices 'whipsaw,' moving quickly upward, then reversing"*; *"typically does not know the maximum — or, often, even the expected... duration of any particular position at the time of initiation"*; no disclosed drawdown/Sharpe/turnover figures |
| 21 | https://www.sec.gov/Archives/edgar/data/1469317/000168316821001077/qim_10k-123120.htm | 2026-09-08 | P | short-horizon pattern-recognition CTA method | *"several thousand quantitative trading models that utilize pattern recognition to predict short-term price movements in global futures markets"*; 95% systematic / 5% discretionary; margin-to-equity **0–20%**; deleverages into drawdown; **daily-price-limit "impossible to liquidate"** risk factor |
| 22 | (same filing, financial data) | 2026-09-08 | P | that method's realised outcome | Net assets **$20.35M (2018) → $10.90M (2019) → $6.35M (2020)**, net loss every year, Q4-2020 redemptions $1,031,381. **No 10-K filed after FY2020** |
| 23 | https://reports.adviserinfo.sec.gov/reports/ADV/156869/PDF/156869.pdf | 2026-09-08 | P/N | Form ADV Part 2A Item 8 narrative | **Part 1 only, 35 pages, no strategy narrative.** Part 2A brochure not posted for this adviser. See §4.4 |
| 24 | https://data.sec.gov/submissions/CIK{0001469317,0001261379,0001043951}.json | 2026-09-08 | P | filing indexes for three pools | Filing lists for Altegris QIM, Frontier Funds, Campbell Fund Trust. Route works; no rate limiting encountered |
| 25 | https://www.sec.gov/divisions/investment/13ffaq | 2026-09-08 | P | are futures reportable on 13F? | **No.** Only Section 13(f) securities on the Official List; **futures are not**, and **short positions are excluded and may not be netted.** Closes §4.1 permanently |
| 26 | https://www.sec.gov/Archives/edgar/data/1722388/000199937125021239/traderai-497k_122925.htm | 2026-09-08 | P | compelled description of intraday ES method | **HFSP.** Intraday ES long/short, minutes to a few hours, flat by the close, human review of each signal, options to hedge any overnight carry; 1.25% expense; risks name slippage, algorithm flaws, illiquid exits, forced end-of-day liquidation |
| 27 | https://www.sec.gov/Archives/edgar/data/1722388/000199937126010329/hfsp-ncsrs_022826.htm | 2026-09-08 | P | that method's audited outcome | NAV **$20.00 → $18.51 → $15.32**; **−6.01%** since inception to 2025-08-31, **−18.31%** in the six months to 2026-02-28; net assets **$766,238**; futures realised losses $268,161 against $99,952 of written-option gains; **no management discussion of causes** |
| 28 | `efts.sec.gov` FTS: `"intraday" "E-Mini S&P 500" "principal investment strategies"` | 2026-09-08 | P | other registered intraday-ES vehicles | 154 hits; surfaced HFSP plus Elevation Series Trust (PAYM/PAYH) and ProShares/ProFunds leveraged products. **A second candidate vehicle exists and was not opened — the obvious next fetch** |
| 29 | https://patents.google.com/patent/US8433645B1/en | 2026-09-08 | P | an enabled, parameterised trading rule | **Execution, not alpha.** Discloses the square-root impact law `I = a·ρ^β·σ·√(Q/ADV)` and a worked 15-min / 10 bp example, but **the coefficients are explicitly left to calibration.** Alpha Vision → Portware; expired, fee-related |
| 30 | Google Patents sweep: US8140416B2 · US20070294162 · US8560420B2 · US20050091146A1 | 2026-09-08 | S/N | directional rules with thresholds | **NOTHING directional.** Hidden-liquidity probability from depth imbalance; predictive technical indicators. Confirms §4.3: the tier patents execution and infrastructure |
| 31 | https://arxiv.org/abs/2508.06788 · https://arxiv.org/html/2508.06788v1 | 2026-09-08 | A | intraday ES order-flow dynamics from a dissertation | CME BBO **2008–2013, 1,490 days**, 1-second SVAR per 15-min bin; impact **0.834 index pts/unit OFI** (unit not established), significant in 64% of bins, **76% above the 1-minute estimate**; **shocks dissipate within one second**; lagged returns+flows explain **8.7%** of 1-s return variation; **impact inverse-U, highest at the open, lowest at the close**; macro-announcement shifts |
| 32 | https://texaslawbook.net/bizarre-12m-trade-secrets-case-for-quantlab-finally-nears-an-end/ + Law360/CourtListener headers | 2026-09-08 | S/N | a described signal in a trade-secret case | **NOTHING mechanical.** $12.2M verdict, ~$28M settlement, and on appeal the live issue was that Quantlab had to *identify* the secret. Closes §4.2 |
| 33 | Renaissance v. Volfbeyn/Belopolsky reporting (Institutional Investor; wombletradesecrets) | 2026-09-08 | S/N | same | **Names only** — "limit-order strategy", "swap strategy", "Henry's signal"; ~$20M settlement 2007. No mechanism |
| 34 | practitioner long-form transcript probe (Chat With Traders and similar, one framing) | 2026-09-08 | N | mechanism in interview transcripts | **Pure marketing-tier SEO.** Lane 14 already capped and saturated this tier; no further calls spent |

**Solicitation encountered:** none in the primary tier. The marketing-tier results returned by probe
#34 carried prop-firm affiliate content; **none was followed, and nothing in this lane was acted on.**

---

## Evidence retained

[`data/cme_rule575_RA2608-5_2026-07-30.txt`](../../../data/cme_rule575_RA2608-5_2026-07-30.txt) —
§3.5 quotes Q8 and Q18 verbatim, and `cmegroup.com/rulebook/files/cme-group-Rule-575.pdf` is an
**unversioned path that serves whatever the current advisory is**: RA2608-5 itself supersedes
RA2602-5 at that same URL. Under the CLAUDE.md file contract, a file a record quotes is evidence and
belongs in `data/`. Every other document quoted here sits at a permanent archive path (cftc.gov and
sec.gov enforcement/EDGAR archives, arXiv) and was not copied.

---

## Open items a future session could close cheaply

1. **Count the halts.** ES and NQ Velocity Logic / Stop Logic events per year, and the signed price
   change across each. Turns §1.1 from a mechanism into a number. This is the single highest-value
   open item in the lane, and it feeds D379 directly.
2. **Open the second registered intraday-ES vehicle** surfaced by source #28 (Elevation Series Trust,
   PAYM/PAYH). One fetch. If its record is also negative, §1.4 stops being an N of one.
3. **The CME disciplinary corpus via the browser pane, dedicated tab.** `/rulebook/` serves to a
   headered fetch; `/notices/disciplinary/` does not. Do not spend more header permutations.
4. **The Frontier Funds 424B3** (source #16) carries QIM's *own* capsule with its worst peak-to-valley
   — the one drawdown figure §1.5 is missing for the short-horizon family.
5. **Establish the OFI normalisation in arXiv 2508.06788** so the 0.834 index-point coefficient
   becomes a usable cost estimate rather than a relative statement.
