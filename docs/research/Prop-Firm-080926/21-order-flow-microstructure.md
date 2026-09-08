# 21 — Order flow and microstructure, the practitioner tier

**Lane 21 of the Prop-Firm-080926 review.** Opened and closed 2026-09-08.
Schema and stopping rules: [`00-SCHEMA.md`](00-SCHEMA.md). Reads on
[`07-statistics-and-claims.md`](07-statistics-and-claims.md) and
[`14-practitioner-tier-screened.md`](14-practitioner-tier-screened.md), which
rejected "DOM/tick scalping as marketed" (R10) on the anti-screen alone and left
the underlying quantities unexamined. This lane goes past the marketing layer.
Filed toward **D386**.

**Stopping rule that bound: SATURATION, on the lane's central question.** The
horizon question was answered by four independent measurements that agree, and
the last five sources on the practitioner side (Bookmap's stop-run blog, Reddit,
Sierra Chart thread 85263, two paywalled journals) returned nothing, a block,
nothing, a 403 and nothing. **50 sources logged.** No cap was reached and none was
needed.

**NOTHING HERE IS EVIDENCE.** Every claim below is a hypothesis with a
falsification criterion. No strategy is recommended, no avenue is opened or
closed, and no look is added to any multiplicity ledger.

---

## VERDICT

### The horizon-versus-cost answer, which is what this lane was built to produce

**The horizon is about one second, or one to three mid-price changes, and it is
not a matter of dispute — four independent measurements converge on it. At that
horizon the entire predictable move on ES is a small fraction of one tick, and a
taker's round turn costs 1.32 to 1.80 ticks. There is no horizon where the edge
exceeds the cost, because the two quantities move in opposite directions: extend
the horizon to earn more than the round turn, and the predictability is already
gone.**

This is not a close call and it is not an implementation problem. It is
arithmetic on measured inputs, and it reproduces from
[`scripts/`-style working](#the-arithmetic-and-where-it-comes-from) below.

#### 1. The horizon, four ways

| source | instrument | sample | the horizon statement |
|---|---|---|---|
| **arXiv 2508.06788** (Kellogg PhD, Andersen committee) | **ES itself** | CME BBO files, **1,490 trading days, 2 Jan 2008 – 31 Dec 2013**, 34,512,298 one-second samples | *"Impulse responses indicate that shocks dissipate almost entirely within a second."* And in text: *"most impacts dissipate quickly, with responses beyond one lag nearly negligible"* |
| **Cont, Kukanov & Stoikov**, JFE 2014 | 50 US stocks | NYSE TAQ, April 2010 | order book events *"have complicated auto- and cross-correlation structures on the timescale of individual events, which typically vanish after 10 seconds"* |
| **Gould & Bonart** 2016 | 10 Nasdaq stocks | LOBSTER, all of 2014 | the target is **the direction of the NEXT mid-price movement**. One step. Nothing beyond it is tested |
| **Kolm, Turiel & Westray**, *Mathematical Finance* 2023 | 115 Nasdaq stocks | LOBSTER/WRDS, 1 Jan 2019 – 31 Jan 2020, ~10TB | horizons studied span *"between 0 and 2 average price changes"*; on how far ahead returns can be predicted: **"about 2-3 price changes"** |

The convergence is the finding. Two of the four are on large-tick books, which is
the ES-like regime, and one is on ES itself.

#### 2. The cost, and why ES's tick size is the whole story

**ES is the canonical large-tick book: the spread is one tick essentially always.**
Two independent primary confirmations:

- **arXiv 2508.06788 Table 1**: average spread **mean 0.25, sd 0.01**, and the
  **1st, 5th, 25th, 50th and 75th percentiles are all exactly 0.25** — one tick.
  0.26 at the 95th, 0.30 at the 99th.
- **CME's own liquidity research**: measured "Average bid offer spread" of
  **0.004%** in the calm weeks of 17-Mar, 24-Mar and 31-Mar-2025, rising to
  **0.010%** on 7-Apr-2025. At a reference price of 5,700 one tick is
  0.25/5700 = **0.00439%** — so CME's 0.004% *is* one tick, and even the
  crisis-day 0.010% is two.

That single fact fixes the cost. A taker buys at the ask and sells at the bid; a
round turn against the mid is **one full tick = $12.50**, before commission.

| | round turn vs mid | in ES ticks |
|---|---|---|
| spread only | $12.50 | 1.00 |
| + retail commission ($4.00/RT, lane 14 src 17) | **$16.50** | **1.32** |
| + this screen's convention ($10.00/RT) | **$22.50** | **1.80** |

#### 3. The collision

**The required directional hit rate for a taker, by horizon.** `p_req = 0.5 +
cost/(2 × gross)`. On a one-tick-spread book the mid moves in **half-tick**
increments as one side's queue depletes; a full tick per mid-price change is
carried as the generous alternative so the conclusion does not rest on the choice.

| granularity | horizon | gross | p_req @ $16.50 | p_req @ $22.50 |
|---|---|---|---|---|
| half-tick moves | 1 change | $6.25 | **1.82 — impossible** | **2.30 — impossible** |
| half-tick moves | 2 changes | $12.50 | **1.16 — impossible** | **1.40 — impossible** |
| half-tick moves | 3 changes | $18.75 | 0.94 | **1.10 — impossible** |
| full-tick (generous) | 1 change | $12.50 | **1.16 — impossible** | **1.40 — impossible** |
| full-tick (generous) | 2 changes | $25.00 | 0.83 | 0.95 |
| full-tick (generous) | 3 changes | $37.50 | 0.72 | 0.80 |

**The hit rate the literature documents.** Kolm et al.'s out-of-sample R² is
**~1% typically and ~5% at best** for the most favourable large-tick names. Under
the Gaussian orthant map `accuracy = 0.5 + arcsin(√R²)/π` that is a directional
accuracy of **0.532 to 0.572**.

> **Required: 0.72 at the single most generous cell, and rising to 2.30.
> Documented: 0.53 to 0.57. In SEVEN of the twelve cells the requirement exceeds
> 1.0 — in those, a perfect forecaster still loses money.**

**And the same collision computed the other way, on ES's own measured volatility.**
arXiv 2508.06788 Table 1 gives the standard deviation of the one-second ES
mid-quote return as **0.91 bp** (and its 25th, 50th and 75th percentiles as
**exactly 0.00** — a majority of seconds contain no mid-price move to predict at
all). With `E[r | s] = √R² × σ × s`:

| index level | σ (1 sec) | E[gross], R²=1%, 1sd signal | E[gross], R²=5%, 3sd signal | cost ÷ E[gross] |
|---|---|---|---|---|
| ~1,250 (the paper's era) | $5.69 | $0.57 | $3.82 | **4.3× to 29× — every cell fails** |
| ~6,700 (today) | $30.49 | $3.05 | $20.45 | **0.8× to 5.4× — all fail but one** |

*(A ratio above 1.0 means the round turn costs more than the expected gross move.
The single value below 1.0 is the R²=5% × 3-sd × today cell, taken apart next.)*

**One cell clears, and it does not survive inspection.** R²=5% × 3-sd signal ×
today's index gives $20.45 against $16.50. It stacks five favourable choices, and
two are checkable:

- **Volatility.** 0.91 bp/sec implies **22% annualised** — it is a GFC-inclusive
  2008–2013 read, carried forward to today's index level. At 18% it barely clears
  ($16.85 vs $16.50); **at 15% it fails ($13.93)**. Below ~21% annualised the last
  cell dies.
- **Linear extrapolation to 3 sd is wrong at the extreme.** Gould & Bonart's fitted
  relation **saturates**: their local logistic puts P(up) at *"about 0.8 to 0.9"*
  when imbalance is extreme, not at the linear extrapolation. Substituting that
  measured conditional probability instead of extrapolating, **every one-price-change
  cell loses** ($-3.38 to $-18.12 per round turn), and only full-tick moves at
  h ≥ 2 with retail commission survive.

#### 4. The distinction the whole practitioner tier gets wrong

**The famous "order flow explains 65% of price moves" is a CONTEMPORANEOUS
regression and is untradeable by construction.**

Cont, Kukanov & Stoikov regress `ΔP_k` on `OFI_k` where — their words —
*"ΔP_k are the 10-second mid-price changes and OFI_k are the **contemporaneous**
order flow imbalances."* Same interval. It is a description of how price forms,
not a forecast. The authors flag the circularity themselves:

> *"OFI_k includes the contributions of price-changing order book events, leading
> to a possible tautology in the regression."*

Excluding those events, *"the R² declined, but remained in the 35%-60% region."*
Kolm's own slide says it plainly: OFI *"is well known to be an excellent predictor
of **contemporaneous** returns (all timescales)."*

**The predictive R² for the same quantity is 1%–5%.** The gap between 65% and 1%
is the gap between explaining a move that already happened and forecasting one
that has not. Every marketing page that cites the 65% is citing the wrong number.

#### 5. What the latency finding corrects

The received wisdom is "retail is too slow for order flow." **At the one-second
horizon that is false, and it matters that it is false**, because it means the
family is not rescued by better infrastructure.

Retail round-trip latency is quoted at **1–3 ms from a Chicago VPS, 12–25 ms from
New York** (claims tier — VPS vendors; no primary CME or broker figure exists).
Against a **one-second** horizon, 25 ms is 2.5% of the signal's life. **Speed is
not the binding constraint on the taker route. Cost is.** Anyone who "fixes" this
family by buying a Chicago VPS has diagnosed it wrong.

Speed *is* the binding constraint on the maker route — see below — where the
relevant floor is **287 microseconds one-way on fibre** from the Chicago Equinix
hub to the matching engine at Aurora, and retail is 10³–10⁵× that.

#### 6. Both doors, and why each is shut

| route | how it would pay | why it is shut |
|---|---|---|
| **Taker** — cross the spread on an imbalance reading | capture more than 1.32–1.80 ticks per round turn | **Arithmetic.** Section 3. Required 0.72–1.10 accuracy against a documented 0.53–0.57, over a horizon of ~1 second |
| **Maker** — post and earn the spread instead of paying it | flips the $12.50 spread from cost to revenue; cost becomes commission only | **Queue position, and it is a technology rent, not a signal.** Moallemi: *"for some large tick-size stocks… queue value can be of the same order of magnitude as the bid-ask spread"*, and price-time priority *"creates a technological arms race"*. ES top-of-book depth is **mean 630 / median 550 contracts** (arXiv 2508.06788 Table 1). Worse, the signal is **anti-correlated with your fill**: the long queue that predicts an up-move is the queue your buy order is at the back of. And Topstep prohibits *"using software, AI, ultra-high speed systems, or mass data entry to gain an unfair advantage"* |

**Who is on the other side.** CFTC Office of the Chief Economist, on the **ES audit
trail** for August 2010 and August 2011: HFTs participate in **~40% of transactions**
(HL 18% + LH 18% + HH 3%; LFT-to-LFT is 61%), and

> *"high frequency traders have a particularly high success rate on each
> transaction… **when trading against low frequency traders**."*

Measured on the regulator's own audit trail, on this exact contract. And ES is
where the price discovery happens: Hasbrouck (2003), *"E-mini exhibits the largest
information share, accounting for 90% of the price discovery of the S&P 500 index."*
The ES book at the one-second horizon is the most competitively mined order book in
equities, and the counterparty distribution is measured, not assumed.

### The arithmetic, and where it comes from

Every number above reproduces from a single script,
[`data/lane21_horizon_cost.py`](../../../data/lane21_horizon_cost.py), with its
full output committed alongside at
[`data/lane21_horizon_cost.txt`](../../../data/lane21_horizon_cost.txt). Its
measured inputs are ES tick $12.50, ES spread percentiles, ES one-second return
SD 0.91 bp, ES depth 630/550 contracts (all arXiv 2508.06788 Table 1), and R²_OS
1%/5% (Kolm et al. 2023). **Lane 14's NEW
TELL 13 is "arithmetic that does not reproduce from the page's own stated inputs";
this lane's own arithmetic is scripted precisely so it cannot commit that tell.**

**Two known weaknesses in it, stated because they are the falsifiers:**

1. **The R² is imported from Nasdaq equities.** No published ES-futures
   equivalent exists. Kolm et al.'s own closing slide lists *"Can we extend what
   we have to other venues/asset classes (**futures**)?"* as an untried
   **extension**. Direction of the bias: ES is large-tick, deep-queue and
   high-update — precisely the profile where Kolm finds the **best** R²
   (`Log(Updates/PriceChg)` explains R²_OS with an adjusted R² of 75%). **The
   transfer therefore favours the strategy, and the conclusion survives it.**
2. **The volatility is a 2008–2013 read carried to a 2026 index level.** Stressed
   in section 3; the conclusion is unchanged below ~21% annualised.

---

## SURVIVORS

**Zero candidates survive as signals. One thing is worth carrying forward, and it
is not a signal.**

### E1 — OFI as an execution filter on a trade another signal already generated

*(Named `E1`, not `S1`, to avoid collision with lane 14's S1, which it attaches to.)*

**[NEITHER, as a candidate — and that is the correct classification, not a
demotion.]**

Under [R15](../../RULES.md#r15) a signal is *a positive gross mean per trade above
its nulls*. An execution filter **has no mean per trade of its own**. It does not
generate a trade; it chooses the moment to place one that a different rule already
demanded. So it cannot be a personal-book candidate, cannot be pre-registered as
one, and must not be counted as one.

**Why it is nonetheless the only thing here worth keeping.** It is the one use of
order-book imbalance that **does not have to clear a round turn**, because the
round turn is already being paid. Cont & Kukanov's own follow-on is literally
*Optimal Order Placement in Limit Order Markets* (Quantitative Finance 2016), and
the **published** JFE 2014 abstract of Cont/Kukanov/Stoikov closes by discussing
*"a potential application of order flow imbalance as a measure of adverse
selection in limit order executions"* — the literature's own application of this
quantity is **to reduce execution cost, not to generate alpha**.

> **Attribution note, because the distinction matters.** That sentence is in the
> **published** JFE 2014 abstract, recovered at search-surface. It is **not** in
> the March 2011 arXiv preprint (source #5), which this lane read in full and
> which contains zero occurrences of "adverse selection". The two versions differ;
> only the published one carries the claim.

**Where it would attach.** Lane 14's **S1 (intraday momentum on ES/NQ)** is
budgeted at *"0.25 tick in slippage in every transaction"*. One ES tick is $12.50;
0.25 tick is $3.125 per transaction, and a round turn is two transactions. **The
entire prize available to a perfect execution filter on lane 14's S1 is $6.25 per
round turn** — exactly half a tick — real, bounded, and an
order of magnitude smaller than the $150/day target. It is a cost line, not a
strategy.

**Falsification criterion, in our own quantities.** On ES minute-and-book data,
compute realised slippage vs mid for lane 14's S1 entries, unconditionally and
conditioned on top-of-book imbalance at the moment of entry. **E1
survives iff the conditional slippage is lower by more than its own standard
error, on a fixture the rule has not seen.** It owes no R15 test because it makes
no R15 claim.

---

## THE REJECTED LIST

Structural rejections are the durable output.

| # | family | tag | why, precisely |
|---|---|---|---|
| **R1** | **Order-book imbalance / DOM imbalance as a directional taker signal** | **[NEITHER]** | The lane's central rejection. Required accuracy 0.72–1.10 against a documented 0.53–0.57, at a horizon of ~1 second. Six of twelve cells require a hit rate **above 1.0**. See VERDICT §3 |
| **R2** | **Queue-position market making on the imbalance signal** | **[NEITHER]** | The edge is real but it is a **technology rent**: queue value is *"of the same order of magnitude as the bid-ask spread"* in a 550–630 contract queue, won by a *"technological arms race"*. Retail latency is 10³–10⁵× the 287 μs colocated floor. Independently barred by Topstep's *"ultra-high speed systems"* prohibition. **The signal is not the scarce input; the microsecond is** |
| **R3** | **"Follow the big flow" / trade-sign momentum** | **[NEITHER]** | **Refuted by the mechanism that makes it look true.** Trade signs *are* long-memory autocorrelated (C₀(ℓ) ~ ℓ^−γ, γ ≈ 1/5 to 2/3, positive to lags beyond 1,000). Prices are nonetheless near-martingale because impact is **transient with a decay exponent tuned to exactly cancel it** (βc = (1−γ)/2 ≈ 0.4 for France Telecom). Bouchaud et al.'s own conclusion: after shifting by the 0.01 EUR cost of a market order — *"half the typical bid-ask spread"* — the distribution is nearly symmetric and one can *"hardly detect the statistical presence of informed trades that correctly anticipate the sign of the price change… **such as to at least cover their trading**"* costs. **The predictability of order flow is real and is precisely the amount that price formation removes** |
| **R4** | **VPIN / order-flow toxicity** | **[NEITHER]** | Two independent kills. (a) **It is not directional.** VPIN forecasts *volatility*; a $150/day book needs a sign. (b) **It has no incremental power even for that.** Andersen & Bondarenko, on S&P 500 futures: *"we find **no evidence of incremental predictive power of VPIN for future volatility**"* once volume and volatility are controlled. TR-VPIN *"falls short of this uninformed benchmark, rendering it a truly inferior predictor"* — **R7's pattern (a celebrated metric losing to an uninformed benchmark), found here in someone else's literature rather than our own.** And *"the information content of BV-VPIN is fully subsumed by realized volatility"* |
| **R5** | **Absorption as a reversal predictor** | **[NEITHER]** | **The first half is real and quantified; the second half is untested and the nearest directional evidence has the opposite sign.** Frey & Sandås (Xetra, 30 DAX-30 stocks, Jan–Mar 2004): an iceberg on the side being hit cuts expected impact *"by approximately 80% from 2.2 to 0.3 basis points"* at a 30-trade horizon — that **is** absorption, measured. But no paper found tests whether it predicts a reversal, and where direction *is* measured, detected icebergs fill **faster** (median time-to-fill ratio **0.7**, 23 of 30 stocks below 1) because they *"attract market orders"*. The authors' own reading: impact falls with execution fraction *"consistent with **liquidity rather than informed trading**"* — **the absorber is a liquidity provider, not an informed accumulator** |
| **R6** | **Stop runs / liquidity sweeps as a chart-readable setup** | **[NEITHER]** | **Three kills.** (a) **Sign.** Osler's round-number result is *continuation*, not reversal: excess post-crossing move of **0.71 / 0.91 / 0.33 bp** (DEM/JPY/GBP) over 15 minutes, peaking at 2.35 bp, and **turning negative by one day in two of three pairs**. Reversal frequency 59.3% vs 54.8% — and insignificant in GBP. (b) **Fuel.** The CFTC's own CME audit-trail study, 2014–2016: stop orders are **0.9% of ES volume** (2% CL, 0.3% ZN), and **98% of executed ES stops are stop-LIMIT** with exchange protection points. *There is not enough stop-order fuel in ES for a cascade, and the order type used is the one that cannot cascade.* (c) **Input.** Where deliberate stop-hunting is *proven* — CFTC v. Deutsche Bank, $30,000,000 penalty, chats including *"where are [yo]ur stops … i can hunt with u"* — the trader knew the levels because **the stop was placed through his own bank, or a colluding trader told him**. The chart carried none of it |
| **R7** | **Iceberg detection as a signal** | **[NEITHER]** | Killed by the vendor's own documentation. Bookmap states flatly that *"the size of the hidden part of the Iceberg order **cannot be detected**"*, that its presence and displayed size *"cannot be detected **before it gets executed**"*, and that the moment of placement *"cannot be detected in advance"*. **Detection is strictly backward-looking and never reveals how much is left** — so "there is a big hidden bid there, fade into it" uses a quantity the vendor says is unobservable |
| **R8** | **Footprint / delta divergence as a signal** | **[NEITHER]** | No vendor publishes a recomputable definition. ATAS gives delta exactly (*"subtraction of the volume of contracts traded at the Bid price from the volume of contracts traded at the Ask price"*) but its **divergence** rule has *no formula, no lookback and no detection rule* — only bands (*"Below 5% indicates balance"*, *"Above 10%… indicates initiative"*). Sierra Chart's "stacked imbalance" threshold is a **user parameter with no vendor default**, so every published win rate for it is conditioned on an unstated choice. ATAS itself warns *"A session-wide divergence is not necessarily a reversal signal"* |
| **R9** | **Volume-at-price / volume profile levels** | **[CLOSED ALREADY]** | D189/D194/D196. A permanent stop fired. **Not re-reported here as a signal, and this lane found nothing that would reopen it** |

### One nuance that cuts the other way, and should be recorded

**Footprint bid/ask classification is EXACT on CME, and approximate everywhere
else.** The tick rule and Lee-Ready classify at roughly **80–84%** accuracy against
a true aggressor flag. Sierra Chart's documented 7-step hierarchy uses *"exchange
indication"* — *"the most accurate"* — for CME Group, EUREX and NASDAQ, and falls
back to the price/tick ladder otherwise; it states *"This method is not used with
CQG."* So a footprint built on a CME feed carrying the aggressor flag is measuring
what it claims to measure, while the same chart on a feed without it carries a
**16–20% misclassification rate into every delta and imbalance number**. Nobody in
the practitioner tier propagates that error into a claimed win rate.

This is a genuine data-quality finding and it **does not rescue any candidate** —
R1's arithmetic assumes perfect classification and still fails. It is recorded
because it is the one place where the practitioner tooling is more rigorous than
its reputation.

---

## ANTI-SCREEN SPECIMENS

Lane 07's twelve tells and lane 14's NEW TELL 13 are the reference. **One new tell
is added.**

**Specimen 1 — futureshive, "Footprint Charts Complete Guide". The canonical case.**
Seven win-rate claims, every one bare: *"75-80% win rates"* (stacked imbalance),
*"70-75% when absorption holds with clear rejection candle"*, *"80%+ when all
confluence factors align"*, *"65-70% for breakouts, 70-75% for fades"*,
*"70-80%+ win rates on 10-20 point scalps"*, *"85%+ setup"*. **No N, no date range,
no cost convention, no null, on any of them.** It does state payoff ratios
(*"2:1+"*, *"1.5-2x risk minimum"*) — which makes it **self-refuting**: 77.5% at
2:1 implies **+1.33R per trade**, and the *"85%+"* cell implies **+1.55R**. An edge
of that size on ES would be the most valuable discovery in the history of futures
trading and it is being given away on a blog.

**Specimen 2 — the disappearing primary.** Jigsaw Trading's two published papers,
`IntroductionToOrderFlow.pdf` and `ConfirmingLevelsWithOrderFlow.pdf`, are still
indexed by search engines and both return **HTTP 404** on the vendor's own site.
The flagship published material of the most research-oriented vendor in this tier
is **no longer retrievable from the party that wrote it.** Third-party mirrors
exist and were not fetched — unverifiable provenance.

**Specimen 3 — the empty definition.** ATAS's `help.atas.net` article for its own
core quantity, Delta, renders as *"Loading…"* and *"Sorry! nothing found for
Delta."*

> **NEW TELL 14 — the vendors do not make the claims; the affiliate layer around
> them does.**
> This is the opposite of what lane 14's specimen 1 (TradeAlgo) would predict, and
> it changes where to look. **Sierra Chart and Bookmap publish engineering
> documentation and make essentially no performance claims at all** — Bookmap's
> iceberg page is three consecutive admissions of what *cannot* be detected, which
> is better disclosure than anything in lane 07 or lane 14. Every quantified
> win-rate claim found in this territory came from the SEO/affiliate layer
> (futureshive, quantstrategy.io, prop-firm review sites), not from the party that
> built the tool. **Consequence: rejecting a vendor because its resellers lie is a
> category error, and the vendor documentation is the highest-value tier here** —
> it is where the recomputable definitions and the admitted limitations live.

**Specimen 4 — a methodological hazard this lane hit twice, and it is not a
source problem.** WebFetch's PDF summariser **fabricated an entire sample
description** for Frey & Sandås — reporting "NASDAQ, 113 most actively traded
stocks, January to December 2001, ~1.6 million limit orders" with a quoted
"continuation rather than reversal" finding. **None of it is in the paper**, which
is Xetra, DAX-30, Jan–Mar 2004. It was caught only because the exchange
contradicted a search snippet.

> **Every academic number in this lane was extracted locally with `pypdf`, not
> taken from a fetch summary.** Lane 14 recorded PDFs as **BLOCKED** ("no
> poppler") and lost the Gao et al. t-statistics to it; `pypdf` is installed in
> this environment and reads them fine. **That block should be lifted from the
> research notes.**

**On-page directives observed and NOT acted on**, per the safety brief: Jigsaw's
*"GET STARTED NOW"* → `/try-buy-options/`; Bookmap's marketplace CTAs; Databento's
*"$125 in free credits"* sign-up; several affiliate/broker resellers
(discounttrading.com, propfirmapp.com) which were not fetched. **No page contained
an instruction addressed to an automated agent** — all were ordinary commercial
solicitation. **Nothing was signed up for, no account or trial created, no
software downloaded, no affiliate or referral link followed, no data entered.**

---

## WHAT DATA WOULD BE REQUIRED TO TEST ANYTHING HERE

**The headline is counterintuitive and it should be recorded: the data is not the
constraint.**

**The quantity that matters needs only Level 1.** Cont/Kukanov/Stoikov's OFI is
built from *"the imbalance between supply and demand at the **best bid and ask**
prices"*, computed from NBBO quote updates — **best bid/ask price and size, and
nothing deeper.** Every retail futures feed carries that. Gould & Bonart's queue
imbalance is the same two numbers. **The single best-documented short-horizon
predictor in finance is computable from a feed a retail futures trader already
has.** It still does not clear the round turn.

**MBO is needed only for the routes already rejected** — queue position (R2) and
iceberg detection (R7).

### If it were tested anyway, the shopping list and the trap

| need | product | price | note |
|---|---|---|---|
| ES top-of-book history | Databento GLBX.MDP3, MBP-1/BBO | **unpriced publicly** — metered $/GB; five separate attempts failed to read a rate, the SPA never renders one | Standard plan **$199/mo** gives only *"1 year of L1 history and 1 month of L2 and L3 history"* |
| ES **MBO** history | Databento GLBX.MDP3 | MBO available only from **2017-05-21**; 2010-06-06 to then is FIX/FAST where *"the highest granularity available… is MBP-10"* | full history needs **Plus $1,750/mo** or **Unlimited $4,500/mo** → **≥$21,000/yr** |
| Real-time MBO, **display** | Rithmic CME bundle $101 + CME Non-Pro Depth of Market bundle $36.50 | **$137.50/mo** | MBO is *not* a separate CME product: *"delivered in the same data feed"*; the 2026 CME fee list has **no MBO line item** |
| Real-time MBO, **non-display (automated)** | Rithmic $101 + CME User Non-Display Cat A $457 | **$558/mo** | |

> **THE TRAP, and it is the finding of this section.** The cheap ~$36.50 retail
> figure is a **display-device** licence. **The moment the data drives an automated
> system, CME's own fee list moves you to non-display at $208–$609/month per DCM —
> a 6× to 17× step.** That distinction, not vendor pricing, is the binding cost of
> running any order-flow signal live, and no page in the practitioner tier mentions
> it.

### The falsifier for this lane's whole verdict

**Stated so it can kill the verdict, in our own quantities.**

> On ES top-of-book data (L1 is sufficient), compute queue imbalance `I` at each
> mid-price change and fit the Gould & Bonart classifier. Then compute, **per
> single ES contract and in dollars**, the realised mid-to-mid move over horizons
> of 1, 2, 3 and 5 subsequent mid-price changes, conditioned on `I`. **The lane's
> verdict is wrong iff there exists a horizon at which
> `E[signed move | I] > $16.50`**, with a null that shares the treatment's
> turnover — randomise the *timing* of entry within the same eligibility mask, not
> the membership, per D291 — and with the p50 and p95 of that null reported beside
> the score.
>
> **Prediction, computable from the numbers already in this file before the runner
> exists:** no such horizon exists, because at h=1 the move is half a tick ($6.25)
> and by h=3 the documented predictability is already *"almost 0"*. If a horizon
> **is** found, the most likely explanation is that the conditional move was
> measured without charging the spread — check that first.

---

## WHAT LANE 21 HANDS FORWARD

1. **The horizon-versus-cost collision is the durable output, and it generalises
   past this family.** Any candidate whose gross edge per trade is a *fraction of
   one ES tick* is dead before a backtest is written, because the round turn is
   **1.32 ticks at retail commission and 1.80 at this screen's convention**. That
   is a cheap pre-filter, computable in one line, and it disposes of the entire
   tick-scalping tier that lane 14 could only reject on the anti-screen.
2. **A published R² is not a hit rate, and a contemporaneous R² is not a forecast.**
   The 65% (Cont/Kukanov/Stoikov, same-interval) versus ~1% (Kolm et al.,
   forward-looking) gap **on the same quantity** is the single most useful
   correction this lane produces. **Any future record citing an order-flow R² must
   state which regression it came from**, and any R² must be converted to a hit
   rate before it is compared to a cost.
3. **The "retail is too slow" story is wrong at this horizon and should stop being
   repeated.** 25 ms against a 1-second signal is not the problem. Saying it is
   invites the wrong fix.
4. **VPIN is an EXTERNAL instance of the pattern this repo has recorded four times
   internally** — a celebrated metric that loses to an uninformed benchmark
   (R7). It is not a fifth entry in our own ledger; it is the same failure mode
   found in someone else's. Andersen & Bondarenko's argument is exactly
   this repo's rule that *a control must share the treatment's nuisance* — they
   killed VPIN by controlling for volume and volatility, which ELO characterised
   as *"irrelevant or illegitimate"*. **That dispute is worth reading as a
   methodology case study, independent of VPIN.**
5. **Absorption is real at −80% of price impact and says nothing about direction.**
   The practitioner claim and the academic result are **different claims about the
   same event**, and the gap has never been tested. That is a `NOT PUBLISHED`, not
   a refutation — but the nearest directional evidence points the other way.
6. **Lift the PDF block.** Lane 14 recorded PDFs as unreadable; `pypdf` is
   installed and read seven of them here, including the two Osler NY Fed reports
   and two CFTC documents that WebFetch could not. Lane 14's source #5 (Gao et al.
   t-statistics) should be re-attempted.
7. **NEW TELL 14** (vendor documentation is more honest than its affiliate layer)
   should be added alongside lane 14's TELL 13 before this screen is reused.
8. **The unmoderated forum tier remains unsampled**, as in lane 14 — Reddit is
   unfetchable and futures.io/EliteTrader were not reachable via the search index.
   This is a real limitation of coverage in both lanes.

---

## Sources

**50 sources.** Tier per schema §4: **primary** (exchange docs, firm T&Cs,
regulator filings and studies, vendor documentation) / **secondary** (peer-reviewed
literature, press) / **claims** (marketing, vendor blogs, forums). **fetched** =
full page or PDF retrieved and read locally; **search-surface** = recovered via
search index only. Negative and blocked results are mandatory entries.

### A — the horizon question (this lane's core)

| # | URL | accessed | tier | sought | yielded |
|---|---|---|---|---|---|
| 1 | https://arxiv.org/pdf/2508.06788 | 2026-09-08 | **secondary, ES-specific** (fetched, pypdf) | a futures-specific horizon measurement | **THE LANE'S CENTRAL ARTEFACT.** CME BBO files, **1,490 days, 2 Jan 2008 – 31 Dec 2013**, 34,512,298 one-second samples. *"Impulse responses indicate that shocks dissipate almost entirely within a second"*; *"responses beyond one lag nearly negligible"*. Table 1: spread **mean 0.25, sd 0.01, p1–p75 all 0.25**; 1-sec mid return **SD 0.91 bp, p25=p50=p75=0.00**; depth **mean 630 / median 550**; 45 events/sec at 15 contracts. Tick 0.25 = $12.50, contract $50 × index. **No transaction-cost analysis** — spread used only as a descriptive proxy |
| 2 | https://www.northinfo.com/Documents/1087.pdf (Kolm/Turiel/Westray, *Math. Finance* 2023) | 2026-09-08 | **secondary, peer-reviewed** (fetched, pypdf) | how far ahead OFI predicts | **THE HORIZON NUMBER.** *"How far ahead can we predict returns? (**about 2-3 price changes**)"*. 115 stocks, LOBSTER/WRDS **1 Jan 2019 – 31 Jan 2020**, ~10TB, 10ms latency buffer. Horizons *"between 0 and 2 average price changes"*. **R²_OS axis −0.25% to 1.25%**, cross-section to ~5%. *"Small R² but high profitability due to the short horizons"* — **asserted with no cost analysis anywhere**. Slide 43 lists **futures as an untried extension** |
| 3 | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3900141 | 2026-09-08 | secondary | the SSRN version of #2 | **BLOCKED — HTTP 403.** SSRN 403s consistently; content taken from #2 instead. Logged so it is not re-attempted |
| 4 | https://arxiv.org/pdf/1512.03492 (Gould & Bonart 2016) | 2026-09-08 | **secondary, peer-reviewed** (fetched, pypdf) | the queue-imbalance predictor's actual accuracy | **YIELDED THE BEST-CASE HIT RATE.** 10 Nasdaq stocks, **all of 2014**, LOBSTER, 10:00–15:30. Target is **the direction of the NEXT mid-price movement only** — *"we restrict our attention to the direction of mid-price movements, not their size"*. Out-of-sample AUC **0.752–0.805** large-tick, **0.581–0.642** small-tick. Local logistic P(up) *"about 0.8 to 0.9"* at extreme imbalance. Large-tick works **because** *"the mean bid–ask spread… is very close to its minimum possible value"*. **Zero transaction-cost analysis; "transaction cost" appears once, in a citation** |
| 5 | https://arxiv.org/pdf/1011.6402 (Cont/Kukanov/Stoikov, JFE 2014) | 2026-09-08 | **secondary, peer-reviewed** (fetched, pypdf) | the origin of the "65%" figure | **THE CONTEMPORANEOUS/PREDICTIVE DISTINCTION.** *"ΔP_k are the 10-second mid-price changes and OFI_k are the **contemporaneous** order flow imbalances."* Average **R² 65%**; authors' own tautology caveat, and excluding price-changing events R² *"remained in the 35%-60% region"*. **50 S&P 500 stocks, one month, April 2010, 21 days.** Also the clock-time horizon: event correlations *"typically vanish after 10 seconds"*. **OFI needs only NBBO best bid/ask — Level 1.** **Version caveat:** this is the **March 2011 preprint**; it contains **zero** occurrences of "adverse selection". The published JFE 2014 abstract adds that application. Do not attribute the published abstract's sentence to this file |
| 6 | https://arxiv.org/abs/1011.6402 | 2026-09-08 | secondary | abstract confirmation | Confirms contemporaneous framing and the 50-stock TAQ sample. No R² in abstract |
| 7 | https://arxiv.org/pdf/1707.01167 | 2026-09-08 | secondary (fetch failed) | the "next 2 mid-price changes" claim | **BLOCKED via WebFetch** (PDF unparsed by the summariser); claim corroborated at search-surface and superseded by #2's stronger statement |
| 8 | https://arxiv.org/abs/1803.06917 (Sirignano & Cont, *Quant. Finance* 2019) | 2026-09-08 | **secondary, peer-reviewed** (fetched) | universality and accuracy of LOB prediction | Abstract verbatim. Target is **"the direction of price moves"** — one-step, same as #4. *"billions of electronic market quotes"*, US equities. **NEGATIVE: no numerical accuracy figure and no transaction-cost treatment anywhere in the abstract** |
| 9 | http://rama.cont.perso.math.cnrs.fr/pdf/SirignanoCont2019.pdf | 2026-09-08 | secondary | #8 full text | **BLOCKED — TLS certificate hostname mismatch.** Logged so it is not re-attempted by this route |
| 10 | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7053198 ("Predictive Order Flow Imbalance", Kethan S E, Jul 2026) | 2026-09-08 | secondary, **NOT peer-reviewed** (search-surface) | a cost-inclusive OFI backtest incl. futures | **YIELDED A DIRECT CORROBORATION, UNVERIFIED.** Twelve US equity/ETF/**futures** instruments. Gross Sharpe **+0.981** → net Sharpe **−1.726**; *bid-ask crossing costs exceed the gross signal edge by a factor of **164*** at ten-second frequency. Mean IC **+0.0044**, OOS **+0.0022**; 5m/10m ICs do not survive multiple-testing correction. **SSRN 403'd — numbers could not be verified. Unrefereed, no stated affiliation.** Agrees in direction with this lane's independently computed arithmetic; carried as corroboration, not as evidence |
| 11 | https://repec.econ.au.dk/repec/creates/rp/13/rp13_42.pdf (Andersen & Bondarenko) | 2026-09-08 | **secondary, peer-reviewed dispute** (fetched, pypdf) | whether VPIN works on ES | **KILLS R4.** On S&P 500 futures: *"we find **no evidence of incremental predictive power of VPIN for future volatility**"*; TR-VPIN *"falls short of this uninformed benchmark, rendering it a truly inferior predictor"*; *"the information content of BV-VPIN is fully subsumed by realized volatility"*; *"using perfect classification leads to diametrically opposite results"*. Flash-crash day: TR-VPIN CDF 95.3% at 12:30, **surpassed on 71 preceding days (11.7% of the pre-crash sample)**. Classification: BV misclassifies **8.3%** vs TTR **2.3%** at volume-bucket level; CPS best BV **20.3%** vs TTR **9.2%** |
| 12 | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1881731 · .../2062450 · https://www.sciencedirect.com/science/article/abs/pii/S1386418113000293 | 2026-09-08 | secondary (search-surface) | both sides of the VPIN dispute | ELO's rejoinder position recovered: *"AB attack a methodology we do not advocate, an analysis we never performed, and conclusions we did not draw."* The disagreement is squarely about **whether controls are legitimate** — ELO characterise benchmarks as *"irrelevant or illegitimate"* |
| 13 | https://www.cftc.gov/sites/default/files/2020-02/ABHFT20191129_ada.pdf (Aït-Sahalia & Brunetti, CFTC OCE) | 2026-09-08 | **primary, regulator, ES audit trail** (fetched, pypdf) | who wins the seconds-horizon game on ES | **YIELDED THE COUNTERPARTY DISTRIBUTION.** Audit-trail data, **August 2010 (September 2010 contract) and August 2011**, ticker ES. *"high frequency traders have a particularly high success rate on each transaction… **when trading against low frequency traders**"*. **8.1 million transactions in Aug 2010**; LL **61%**, HL **18%**, LH **18%**, HH **3%** — HFTs in *"about 40% of transactions"*. Also quotes Hasbrouck (2003): E-mini has *"the largest information share, accounting for **90% of the price discovery** of the S&P 500 index"* |
| 14 | https://moallemi.com/ciamac/papers/queue-value-2016.pdf | 2026-09-08 | secondary (fetched, pypdf) | price the maker route | **KILLS R2.** *"for some large tick-size stocks… **queue value can be of the same order of magnitude as the bid-ask spread**"*; price-time priority *"creates a **technological arms race** among high-frequency traders"*; *"adverse selection costs are **increasing with queue position**"*. Calibrated on **NASDAQ ITCH (MBO)**, large-tick US equities, 2013 |
| 15 | https://arxiv.org/pdf/cond-mat/0307332 (Bouchaud/Gefen/Potters/Wyart 2004) | 2026-09-08 | **secondary, peer-reviewed** (fetched, pypdf) | is "follow the flow" tradeable? | **KILLS R3.** France Telecom, Paris Bourse, **~2×10⁶ trades in 2002**. Sign autocorrelation γ ≈ 1/5 (FT), 2/3 (Total); naive amplification would be **Ne ≈ 50**, observed R(ℓ) rises only **~2×** to ℓ*≈1000. Resolution: propagator must decay at **βc = (1−γ)/2 ≈ 0.4**. The killers: individual impact *"rapidly becomes lost in the fluctuations"*, and after subtracting the **0.01 EUR** cost of a market order — *"half the typical bid-ask spread"* — one can *"**hardly detect** the statistical presence of informed trades… such as to at least cover their trading"* costs |
| 16 | https://arxiv.org/abs/1610.00261 · https://moallemi.com/…/queue-value-2014 · https://www.sciencedirect.com/…/S1386418125000229 | 2026-09-08 | secondary (search-surface) | fill probability vs signal | Queue position drives adverse selection and inhibits inventory management; fill probability depends on queue position and market-order arrival; *"latency being especially important after a price change"*. **Confirms the maker route is a speed problem, not a signal problem** |

### B — absorption and stop runs

| # | URL | accessed | tier | sought | yielded |
|---|---|---|---|---|---|
| 17 | https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf (Osler, JIMF 2005) | 2026-09-08 | **secondary, peer-reviewed** (fetched, pypdf) | the stop-cascade effect size and horizon | **KILLS R6 ON SIGN AND SIZE.** Prices min-by-min **2 Jan 1996 – 30 Apr 1998**; orders 9,655 orders / >$55bn from **one** dealing bank, **Aug 1999 – Apr 2000**. Excess move after crossing a round number, 15 min: **0.71 / 0.91 / 0.33 bp** (DEM/JPY/GBP). Excess movement peaks **2.35 bp** (JPY, 2h) and **turns negative by one day in two of three pairs** (−5.23 DEM, −2.60 GBP). Reversal frequency **59.3/60.1/58.1%** vs **54.8/57.3/56.6%**; GBP insignificant. Author's own caveat: *"we **cannot yet look directly at price cascades**"* |
| 18 | https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr125.pdf (Osler, JF 2003) | 2026-09-08 | **secondary, peer-reviewed** (fetched, pypdf) | round-number clustering | Clustering confirmed: stop-loss buys **14.4%** at 01–10 vs **7.4%** at 90–99; very large stops **62%** near round numbers vs 28% for take-profits. **CRITICAL NEGATIVE: the paper's price-dynamics claim is a SIMULATION**, and the simulations are *"intentionally structured so that the effects of conditional order flow **exceeds those one might expect in reality**"*. The famous citation does not contain the measurement it is cited for |
| 19 | https://www.cftc.gov/sites/default/files/Stoploss_final_ada.pdf | 2026-09-08 | **primary, regulator study** (fetched, pypdf) | futures stop-order data | **KILLS R6 ON FUEL.** CME audit trail **2014–2016**. Stops are **0.9% of ES volume** (22,789,175 of 2,483,400,538), 2% CL, 0.3% ZN. **98% of executed ES stops are stop-LIMIT**, not stop-market (95% ZN, 99% CL). Protection points: ES 3 index points. Stops *"provide significant liquidity in the direction of the move"*. **MANDATORY NEGATIVE: no round-number clustering analysis, no post-trigger price path, no cascade or reversal test — the one dataset that could settle it does not ask** |
| 20 | https://www.cftc.gov/…/enfdeutschebankagorder012918.pdf | 2026-09-08 | **primary, enforcement order** (fetched, pypdf) | is stop hunting real and prosecuted? | **YES — AND THE MECHANISM IS THE FINDING.** Dec 2009 – Feb 2012, COMEX/NYMEX metals, **$30,000,000** penalty. Chats: *"where are [yo]ur stops … i can hunt with u"*, *"[I] have chunky stop at 27.35 … keep to urself"*. **The trader knew the levels because the stop was placed through his bank or a colluding trader told him.** No price magnitude given. A chart has no analogue of that input |
| 21 | https://conference.nber.org/confer/2008/mms08/sandas.pdf (Frey & Sandås) | 2026-09-08 | secondary, working paper → QJF (fetched, pypdf) | does absorption predict anything? | **THE ABSORPTION NUMBER, AND THE OPPOSITE SIGN.** Xetra, **30 DAX-30 stocks, 2 Jan – 31 Mar 2004**. Iceberg on the hit side: impact *"drops by approximately 80% from **2.2 to 0.3 basis points**"* at 30 trades. Opposite side: **+1.5 to 4.3 bp**. Detected icebergs fill **faster** (time-to-fill ratio **0.7**, 23/30 stocks), they *"attract market orders"*; impact falls with execution fraction *"consistent with **liquidity rather than informed trading**"*. **MANDATORY NEGATIVE: reversal is never tested** |
| 22 | https://academic.oup.com/rof/article-abstract/9/2/201/1611889 (Degryse et al. 2005) | 2026-09-08 | secondary, peer-reviewed (abstract only) | book resiliency | *"do return to their initial level within **20 best limit updates** after the shock"*; initial impact *"partly reversed"* but a long-term effect remains. **NEGATIVE: no effect size, no sample in the abstract; full text 403'd** |
| 23 | https://www.sciencedirect.com/science/article/abs/pii/S1386418106000528 (Large 2007) + RePEc + Semantic Scholar | 2026-09-08 | secondary (blocked ×4; abstract snippet only) | replenishment rate and half-life | **BLOCKED at all four routes** (403, 403, empty body, *"No abstract is available"*). Snippet only: *"In over 60 per cent of cases, the order book does **not** replenish reliably after a large trade. However, if it does replenish, it does so with a fairly fast half life of around 20 seconds."* **Wording high-confidence, sample unverified** |
| 24 | https://research.tilburguniversity.edu/files/543112/file · semanticscholar (Degryse full text) | 2026-09-08 | secondary | Degryse magnitudes | **BLOCKED — HTTP 403 / empty body.** Logged so they are not re-attempted |
| 25 | https://www.sciencedirect.com/science/article/abs/pii/S106294081630002X ("Invisible walls") | 2026-09-08 | secondary | a contrary result on round-number barriers | **BLOCKED — HTTP 403.** Title suggests a negative on psychological barriers; **unresolved, and it cuts against R6's clustering premise, so it is worth a future attempt** |
| 26 | WebSearch: Bessembinder/Panayides/Venkataraman, hidden liquidity (JFE 2009) | 2026-09-08 | secondary, peer-reviewed (search-surface) | hidden-order economics | Euronext-Paris: hidden orders are **44% of order volume**; hiding decreases full-execution probability and increases time to completion; *"exposing rather than hiding order size increases average execution costs"* |
| 27 | WebSearch: "liquidity sweep" / "stop hunt", peer-reviewed | 2026-09-08 | — | any academic treatment | **NOTHING. Zero peer-reviewed hits.** Every result is broker content, trading education or TradingView. **This is the cleanest negative in the lane: the practitioner tier's most-marketed pattern has no literature at all** |
| 28 | WebSearch: futures round-number clustering (Chung 2006; Schwartz 2004; Donaldson & Kim 1993) | 2026-09-08 | secondary (search-surface) | equity-index analogue | Clustering confirmed at x.00/x.50. Donaldson & Kim, DJIA 1974–1990, report a *"bandwagon effect"* after crossing — **the same continuation sign as Osler**, no magnitude retrieved. **NEGATIVE: nothing found on reversion after a breach** |

### C — the tooling tier

| # | URL | accessed | tier | sought | yielded |
|---|---|---|---|---|---|
| 29 | https://www.sierrachart.com/index.php?page=doc/NumbersBars.php | 2026-09-08 | **primary, vendor doc** (fetched) | a recomputable definition | **THE BEST DEFINITION IN THE TERRITORY.** Bid/Ask Volume defined as *"the sum of all traded volume… that were Bid Trades"*, with a documented **7-step classification hierarchy**: (1) *"exchange indication"* — *"the most accurate"* — used for CME Group, EUREX, NASDAQ; then price/tick fallbacks. *"This method is not used with CQG."* **"Diagonal Dominant Side" is defined with NO numerical threshold** |
| 30 | https://www.sierrachart.com/index.php?page=doc/StudiesReference.php&ID=386 | 2026-09-08 | primary, vendor doc (fetched) | imbalance formulas | Four methods with explicit ratios: *"Ask Volume (Next) / Bid Volume * 100"* etc. **Thresholds are user parameters with no vendor default** — so every published "stacked imbalance" win rate is conditioned on an unstated choice. `Ask Volume (Next)` left undefined at bar extremes |
| 31 | https://bookmap.com/knowledgebase/docs/KB-Bookmap-Wiki-Iceberg-Orders-Tracker | 2026-09-08 | **primary, vendor doc** (fetched) | iceberg algorithm and limits | **KILLS R7 FROM THE VENDOR'S OWN PAGE.** Three admissions: *"The size of the hidden part of the Iceberg order cannot be detected"*; *"cannot be detected before it gets executed"*; *"The moment of placement… cannot be detected in advance."* Also *"Exchanges do not report Iceberg orders via market data."* **No accuracy percentage anywhere — only *"hardly distinguishable"*** |
| 32 | https://learn.atas.net/volume-basics/volume-analysis/divergence-scale-and-workflow · https://help.atas.net/…/72000602362-delta | 2026-09-08 | primary, vendor doc (fetched) | delta and divergence definitions | Delta recomputable: *"subtraction of the volume of contracts traded at the Bid price from the volume of contracts traded at the Ask price"*. **Divergence NOT recomputable — no formula, no lookback, no detection rule.** Vendor-admitted limit, to its credit: *"A session-wide divergence is not necessarily a reversal signal"*. **The `help.atas.net` Delta article is an empty stub — renders *"Sorry! nothing found for Delta"*** |
| 33 | https://bookmap.com/blog/stops-and-icebergs-… · https://bookmap.com/blog/detecting-stop-runs-using-cvd-and-iceberg-absorption… | 2026-09-08 | claims, vendor blog (fetched) | any statistics on stop runs | **NOTHING quantified — logged as one cluster.** No rules, no hit rate, no sample, no date range, no backtest. Narrative only (*"a sudden price movement triggers a series of stop-loss orders"*) with an illustrative hypothetical. One useful line: *"Without MBO data, a stop run just looks like a surge in volume"* |
| 34 | https://jigsawtrading.com/wp-content/uploads/2014/02/IntroductionToOrderFlow.pdf · .../2013/11/ConfirmingLevelsWithOrderFlow.pdf · https://jigsawtrading.com/learn-to-trade-free-order-flow-analysis-lessons-lesson10/ | 2026-09-08 | primary, vendor papers | Jigsaw's published research | **BLOCKED — HTTP 404 on both PDFs. SPECIMEN 2.** Still indexed by search, removed from the vendor's own site. The lesson page carries no written definition, no method, no N — the content is a video. Mirrors exist (silo.tips, pdfcoffee) and were **not** fetched: unverifiable provenance |
| 35 | https://futureshive.com/blog/footprint-charts-complete-guide-2025 | 2026-09-08 | claims (fetched) | quantified practitioner claims | **ANTI-SCREEN SPECIMEN 1.** Seven bare win rates — *"75-80%"*, *"70-75%"*, *"80%+"*, *"65-70%"*, *"70-80%+"*, *"85%+"* — **no N, no dates, no cost convention, no null on any**. Payoff ratios *are* stated (*"2:1+"*), which makes it self-refuting at **+1.33R to +1.55R per trade**. Imbalance thresholds *"3:1"*, *"4:1 or 5:1 minimum"* — confirming the threshold is arbitrary |
| 36 | WebSearch: tick rule / Lee-Ready accuracy vs CME aggressor flag | 2026-09-08 | **secondary, academic** (search-surface) | is the footprint's base quantity sound? | **THE ONLY QUANTIFIED BENCHMARK IN THE TOOLING TIER, AND IT COMES FROM ACADEMIA.** Lee-Ready *"success rate of 84.4%"*, tick test *"83.0%"*; the tick method *"does not perform well when trades occur at the spread midpoint"*. **So a footprint on a feed WITHOUT the exchange aggressor flag carries a 16–20% misclassification into every delta** |
| 37 | https://www.reddit.com/r/FuturesTrading (search) · https://www.sierrachart.com/SupportBoard.php?ThreadID=89109 · ...85263 · https://quantstrategy.io/blog/backtesting-order-flow-strategies-… · WebSearch: vendor-published absorption backtest | 2026-09-08 | claims / primary forum | a vendor claim checked and failed; community backtests with N | **NOTHING — logged as one cluster, and this is where saturation was declared.** Reddit **BLOCKED** (*"Claude Code is unable to fetch from www.reddit.com"*). Both Sierra Chart engineering threads declined to state a limitation. quantstrategy.io's two "case studies" are **illustrative hypotheticals, not analyses** — *"The backtest shows an incredible win rate (90%)"* is a worked example, with no sample and no dates, so it **cannot be cited as a claim checked and failed**. **No documented case of an order-flow vendor claim being independently checked was found anywhere** |

### D — the data bridge

| # | URL | accessed | tier | sought | yielded |
|---|---|---|---|---|---|
| 38 | https://www.cmegroup.com/articles/faqs/market-by-order-mbo.html | 2026-09-08 | **primary, exchange** (fetched) | is MBO obtainable by retail? | **DECISIVE.** *"MBO is supported for **all** CME Globex options and futures products."* OrderID *"can be used to determine their place in the priority queue"*; MBO covers *"all price levels (not restricted to top 10)"*. MBP is insufficient: *"**Individual queue position and order sizes cannot be determined with a high degree of accuracy**."* **Not a separate product** — *"delivered in the same data feed"*. History from launch; rollout Dec 2016 – Jun 2017 |
| 39 | https://api.databento.com/static/licensing/cme/cme-market-data-fee-list.pdf (eff. **2026-01-01**) | 2026-09-08 | **primary, exchange fee schedule** (fetched) | the real cost of running this live | **THE TRAP.** Non-Pro Depth of Market **$12.10/DCM, bundle $36.50**; Non-Pro Top of Book $1.55/$4.65. But **Non-Display Cat A1 "Trading As a Principal" $609/mo per DCM** (Premium $1,820, Enterprise $3,640); User Non-Display Cat A **$457**; Managed User Non-Display **$208**. **No MBO line item exists** — the licence is by *use*, not granularity. **Automating the signal is a 6×–17× step over the display licence** |
| 40 | https://www.cmegroup.com/articles/2025/reassessing-liquidity-beyond-order-book-depth.html | 2026-09-08 | **primary, exchange research** (fetched) | CME's own ES liquidity numbers | **INDEPENDENTLY CONFIRMS THE ONE-TICK SPREAD.** Measured "Average bid offer spread" **0.004%** (weeks of 17/24/31-Mar-2025), 0.005%, **0.010%** on 7-Apr-2025 — and 0.25/5700 = **0.00439%**, so 0.004% *is* one tick. Realised impact **5.4 bps** for $58.75m at the open on 7-Apr-2025 vs **2.1 bps** on 17-Mar. Depth fell *"approximately 27%"* then a further **68%**. ADV notional **$412,992,948,821**. **NEGATIVE: every depth figure is a chart — CME never publishes ES top-of-book size in contracts** |
| 41 | https://www.cmegroup.com/education/articles-and-reports/understanding-the-cme-liquidity-tool-methodology.html · .../assessing-liquidity · .../cme-liquidity-tool.html | 2026-09-08 | primary, exchange (fetched) | the Liquidity Tool's algebra | **PARTIAL — logged as one cluster.** Method text obtained: 10 book levels, per-update since 2024-04-01, cost-to-trade walks the book, inactive seconds forward-filled. **The formula images are not in the HTML, so the exact algebra was NOT obtained**, and the tool itself is a JS app with no numbers in source |
| 42 | https://www.cmegroup.com/…/e-mini-sandp500.contractSpecs.html · micro-e-mini-sandp-500 · e-mini-nasdaq-100 · micro-e-mini-nasdaq-100 · .volume.html | 2026-09-08 | primary, exchange | contract specs | **PARTIAL.** MES *"$5 x the S&P 500 Index"*, NQ *"$20 x the Nasdaq-100 index"*, MNQ *"$2 x the Nasdaq-100 Index"*, all *"a minimum tick of 0.25 index points"*. **ES's own spec table and the volume table are JS-rendered and returned NOTHING**; the $50 multiplier was recovered arithmetically from #40's notional table (206 contracts = $58,750,000 at 5,700 → $285,194 vs 5,700 × 50 = $285,000) |
| 43 | https://www.cmegroup.com/articles/2021/e-mini-sp-500-esg-futures-… | 2026-09-08 | primary, exchange (fetched) | a published top-of-book size | **A TRAP AVOIDED, RECORDED SO IT IS NOT FALLEN INTO.** *"The top of book size on the touch is on average 10 contracts"* — **this is the E-mini S&P 500 ESG contract (~1K ADV), NOT ES.** The only numeric top-of-book CME publishes is for the wrong product |
| 44 | https://databento.com/pricing · /blog/introducing-new-cme-pricing-plans · /docs/quickstart/pricing · /docs/api-reference-historical/basics/metered-pricing · /catalog/cme/GLBX.MDP3 | 2026-09-08 | primary, vendor (5 attempts) | the $/GB rate for ES MBO history | **NOTHING, FIVE TIMES — a mandatory negative.** SPA shell; no price string in raw HTML. Plans read: Standard **"$199 per month"** (blog says **"$179/month"** — conflicting), Plus **"$1,750 license fees per month"**, Unlimited **"$4,500"**. Standard gives only *"1 year of L1 history and 1 month of L2 and L3 history"*. **Any "one year of ES MBO costs $X" claim must be marked UNPRICED** |
| 45 | https://databento.com/blog/CME-history-extended-to-2010 · /blog/cme-colocation · roadmap.databento.com (2023-06-04) | 2026-09-08 | primary, vendor (fetched) | MBO history depth and latency floor | History from **2010-06-06**, but **MBO only from 2017-05-21** — before that *"the highest granularity available for this period is MBP-10"*. Latency floor: *"at least **287 microseconds one-way on fiber**"* from the Chicago Equinix hub to the matching engine at 2905 E. Diehl Road, Aurora IL. Live CME *"starting at $36.50/month for non-professionals and $1,219/month for professional non-display use"* |
| 46 | https://bookmap.com/en/partner/rithmic · https://rithmic.com/products · support.edgeclear.com/…/rithmic-market-by-order-mbo-data | 2026-09-08 | claims/vendor (fetched) | a retail real-time MBO path | *"Rithmic provides true Market-by-Order (MBO) data for CME futures"*; *"CME Bundle…: **$101/month**"*, single exchange $39. **NEGATIVE: rithmic.com/products returned 49 bytes of text — Rithmic's MBO claim rests entirely on resellers (Bookmap, EdgeClear), not on a Rithmic document** |
| 47 | https://iqhelp.dtn.com/core-service-fees · /globex_data_packages · WebSearch: CQG/Tradovate/Rithmic depth models | 2026-09-08 | primary vendor + secondary | what depth brokers actually deliver | IQFeed Level II **$20/mo**, Core $108.15, RT US Futures $24.87, market-depth surcharge $24.15. **No MBO product, and no statement of how many depth levels.** DTN's *"as low as $1 per month per exchange"* page is dated **March 1, 2014** — stale against #39. Claim (unverified against any primary vendor doc): Tradovate and CQG are MBP-aggregated, CQG ~10 levels |
| 48 | WebSearch: retail latency to CME Globex Aurora | 2026-09-08 | **claims (VPS vendors)** | realistic retail latency | **1–3 ms Chicago VPS, 12–25 ms New York, 100–150 ms Europe**; engine *"less than 150 microseconds"*. **All from self-interested VPS marketing (tradingfxvps.com, tradoxvps.com, traderfuel.net). No CME-published or broker-published retail round-trip figure exists.** Treat 5–25 ms as a working assumption, unsourced to any primary party |
| 49 | https://help.topstep.com/en/articles/10296582-prohibited-conduct | 2026-09-08 | **primary, firm rules** (fetched) | does any rule bar this family? | **YIELDED, AND EXTENDS LANE 14 SRC 13.** Prohibited: *"Unfair technology — using **software, AI, ultra-high speed systems**, or mass data entry to gain an unfair advantage"*. **NEGATIVE AND USEFUL: no minimum hold time and no scalping restriction of any kind appears** — so a seconds-horizon strategy is not barred by holding period, only the *latency* route is barred |
| 50 | WebSearch: CME Rule 575 (disruptive practices) | 2026-09-08 | secondary (law-firm summaries) | spoofing/layering enforcement thresholds | Rule 575 *"Disruptive Practices Prohibited"* effective **15 September 2014**; prohibits spoofing and quote stuffing; advisory RA1405-5. **NEGATIVE: no message-to-trade ratio thresholds, no Messaging Efficiency Program numbers, and no CME order-book-imbalance research of any kind was found** |

**Searches run that produced no new source, so they are not repeated:** an ES-futures
order-book-imbalance predictability study with a stated cost convention (**none
exists** — Kolm et al. list futures as an untried extension); a CME-published
order-book-imbalance or message-ratio study (none found); a vendor-published
absorption or stacked-imbalance backtest with a stated N (none found from Sierra
Chart, ATAS, Bookmap, Jigsaw or Quantower); any peer-reviewed treatment of
"liquidity sweep" or "stop hunting" as a tradeable pattern (**zero hits**); any
documented case of an order-flow vendor's claim being independently checked and
failing (none found); and a primary retail-latency figure from CME or any broker
(none exists).
