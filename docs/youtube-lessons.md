# YouTube lessons

Things worth keeping from the transcripts in `docs/Youtube Transcrips/`.

**Nothing in this file is a result.** These are untested ideas lifted from other people's
videos, none of which carry a null, a cost convention, or a universe control. An entry here
means "worth half an hour as a variant", not "works". Anything that survives a real study
graduates to `docs/FINDINGS.md` and is deleted from here.

Transcript filenames carry their disposition as a prefix:

| prefix | meaning |
|---|---|
| `[CLOSED]` | read, nothing taken |
| `[EXTRACTED]` | read, something taken — recorded below |

The transcripts themselves are **git-ignored** (`.gitignore`): they are third-party source material
read for review, never evidence, and not ours to redistribute. Anything worth keeping is quoted
into this file or into a decision record, so losing the folder costs nothing.

---

## 1. A self-referential exit: close on the position's own N-bar high

**Source:** `[EXTRACTED] This Algo Strategy Has 70% Win-Rate & Trades AGAINST Retail Traders.txt`
(David, Critical Trading). **The video's own claim is worthless** — a 70% win rate reported
with no payoff ratio, on a rule whose no-stop geometry produces that win rate mechanically,
wrapped in a retail-flow story the strategy never measures. Its entry (buy the 5-bar low) is a
cruder copy of `rsi` / `retrace_leg`, which this programme has already pushed to the point
where [D341](decisions/D341-RESULT-honestly-scored-retrace-leg-is-2-7-bp-a-bar.md)
recommended against spending the holdout read. **Only the exit is
worth anything.**

**The rule:** close the position when the name's own high exceeds its highest high over the
previous N bars.

**What is already built, and the narrow thing this adds.**
[D355](decisions/D355-the-invalidation-exit-on-the-candidate-books.md) already tests a
self-referential exit — *invalidation*: the name's lagged floored **cross-sectional percentile**
of the same score crossing 50 — pre-registered, on `rsi:40` and `hist_L:40`, against the 24 rank
rotations and control A'. So "exit when the position's own signal reverts" is **not** a gap.

The remaining difference is narrow but real: D355's exit reads a **percentile among peers**, so
it can still fire because *other* names moved. An N-bar-high exit reads **only the name's own
price** and is fully independent of the cross-section. That makes it the strictest available
test of the complaint CLAUDE.md records against D285 — an exit *"fired on displacement by
unrelated names, not on its own signal reverting"* — and of `docs/FINDINGS.md` §10's note that
the gap between the two lenses is **opportunity cost, which nothing here has measured**.

**So the entry is worth keeping only as a third arm beside D355's**, not as a new idea. If D355's
invalidation arm already answers the question, this adds nothing.

**What to check if it is ever run.**

1. **It carries no stop**, so it inherits a fat left tail: a name that never makes an N-bar
   high is held indefinitely. Report the trade distribution with both tails trimmed (RULES
   group 2), not the mean alone.
2. **It changes holding period**, so CLAUDE.md's cost-cutting rule applies directly — a longer
   hold lifts breakeven by amortising one round trip while per-bar edge usually falls. Say
   which moved: edge per unit exposure, or cost per trade.
3. **Both lenses, never on the same statistic.** The point of the rule is that it decouples the
   exit from the slot cap, so the path-invariant and path-variant readings should diverge more
   than usual — that divergence *is* the opportunity-cost measurement, and it is the actual
   reason to bother.

**Status:** not tested. No cell scored, no book proposed.

---

## 2. Equal weight was never chosen — it is just what the kernel does

**Source:** `[EXTRACTED] Algo Trading Strategies 19% Profit in 10 Months & 30 Minutes Per Month.txt`
(David, Critical Trading). **The video's evidence is worthless** — it levers a low-volatility
portfolio and a high-volatility benchmark by the same 2:1 and reports the drawdown difference as
skill, which is a restatement of their volatilities. But its subject, inverse-volatility sizing,
exposed a question this programme had not asked.

Every cross-sectional book here is equal-weighted (`1/n_t` per leg,
[`run_d306_width_exits.py:240`](../scripts/run_d306_width_exits.py)) and **nothing has ever been
run against it**. Inverse-vol sizing exists in the breakout/crypto lineage (D110/D118/D119) and
has never met the single-name books.

**Written up properly as
[D372](decisions/D372-equal-weight-is-the-incumbent-sizing-and-the-hurdle.md)** — equal weight
declared as the baseline, the four ways it is dumb, why it is still hard to beat, the challengers,
the confounding with the D339 floor, and the hurdle. Stage 0 there is a volatility-decile split of
contribution P&L, which may end the question before any sizing scheme is built.

---

## 3. A prop account is a down-and-out call, so hurdle P is six screens with no objective behind them

**Source:** `[EXTRACTED] How Quant Finance Made Me $1.6M Trading Prop Firms.txt`. **The video's own
record is worthless as evidence** — it derives `t = SR·√T` correctly on screen, then offers a
**16-month** live record as proof, which by its own arithmetic is **t = 1.15** against the t = 2 it
calls the loosest defensible bar. Its author states he ran "thousands" of uncounted backtests
selecting patterns that had already worked and never corrects for it; every strategy claim in it
carries no number; it ends in a mentorship pitch. **Its loss-streak and t-stat arithmetic is exactly
right** — P(≥4 losses in 100 at a 50% win rate) = 0.973 against the claimed 97%, 0.810 against 81%,
0.546 against 55% — **and that is the only part that checks out.**

**One idea in it is not recycled.** A funded account is a **down-and-out call**, component for
component: the drawdown limit is a knock-out barrier monitored continuously on open equity, the
payout ladder caps the payoff, and consistency rules constrain its path. So value is
`E[payouts | survival] × P(survival)` — **non-linear in size, with an interior optimum** — where own
capital has no second factor and is linear.

**Written up properly as
[D379](decisions/D379-the-prop-account-is-a-down-and-out-call-and-hurdle-P-has-no.md).**
It survives the bar for this file for one reason: **it checks out against our own committed
artifacts, not the video's.** [BOOK_PROP.md](BOOK_PROP.md)'s C1 table already carries `E[payout]`
under the name **"profit before breach"**, falling monotonically (28.20% → 1.75%) while annual return
rises (+4.41% → +13.04%) — so **C1's value peak sits at or below 0.48x, the boundary of the sweep,
and was never searched.** D379 also gives P3 and P5 a mechanism they were adopted without: near the
barrier the account's convexity inverts and variance becomes free, so the consistency rules are the
firm's defence against a risk-shifting incentive the instrument creates.

**Status:** framing only. No cell scored, no candidate reopened, no hurdle amended. The three things
it recommends each owe a pre-registration ([R8](RULES.md#r8)), and the binding limit is that a
valuation framework allocates an edge rather than supplying one — **the prop candidate list is
exhausted, so there is nothing to value.**

---

## 4. The account is purchasable, so price the portfolio — and backtest the barrier, not the curve

**Source:** `[EXTRACTED] The EXACT Trading Strategy That Made Me $1,200,000 in the Last 12 Months.txt`
— **same author as §3, second video.** Recorded as a separate entry because it adds a separate term.

**Its evidence is worse than §3's, and it gives more away.** He states **twice** that the strategy has
no live edge — *"it would probably break even"*, *"I haven't even done it"* — while presenting $1.2M
of payouts, and **does** supply the denominator the first video omitted: **$200–250k of evaluation
fees.** The two cannot both stand: at zero edge, extraction per funded account is bounded near the
drawdown allowance, so the plan is a thin spread set by the counterparty, not a 4.8× return. The
evidence offered is **one selected week, ~16 trades, 11–12 wins** (t = 2.35–2.86, nominally past a
t = 2 bar), and it deflates §3's sample claim: *"20 trades a day, over 7,000 trades"* is **~3.2 setups
a day replicated across five copy-traded accounts** — roughly **1,400 independent decisions**, since
copies of one decision have correlation 1.

**The one term worth taking** is his backtesting instruction, which is right: *don't backtest the
equity curve, simulate the barrier — find your **pass rate**, then cost per funded account is
`fee ÷ pass rate`.* That is the acquisition cost of the option in §3, amortised over the evaluations
that fail, and it makes the object a **portfolio** — `V = N × [P(pass) × E[payout|funded] − fee]`
with `N` purchasable.

**Written up as the 2026-09-08 amendment to
[D379](decisions/D379-the-prop-account-is-a-down-and-out-call-and-hurdle-P-has-no.md).**
It survives the bar here for the same reason §3 did: **`P(pass)` is computable from machinery
[D259](decisions/D259-the-extended-session-and-the-overnight-interior.md) already built** — the same
ratcheting-floor simulation, stopped at a target. The amendment also measures what the **trailing**
floor costs: at zero edge on a +3,000/−2,000 eval, static gives the optional-stopping **40.0%** and
trailing gives **26.5%**.

**What it must not be read as licensing.** He claims pass rate is the only thing worth optimising and
that "strategies that do not work on live will work on prop firms". **Both are false** — `P(pass)` is
a function of edge, cost and the firm's geometry, and at zero edge it is pinned by optional stopping
whatever the strategy. [R15](RULES.md#r15) stands.

**Status:** framing only, folded into D379. Nothing scored, nothing reopened, and the amendment's one
new recommendation owes a pre-registration like the rest.

---

## 5. Volatility clustering is the autocorrelation D379's caveat named, and it argues for a state-dependent prop size

**Source:** `[EXTRACTED] I Re-Created A Quant Trading Strategy With Claude Code (Nobel Prize Method).txt`.
**The method in it is entirely recycled here, and its own headline numbers do not survive being
recomputed** — see the four checks below. **One inference is not recycled, and it is not in the video:**
volatility clustering is exactly the property [D379](decisions/D379-the-prop-account-is-a-down-and-out-call-and-hurdle-P-has-no.md)
names in its closing caveat as the reason its valuation is optimistic, and it is a reason to make
prop-account size **state-dependent** rather than constant.

### What was checked, on our own fixture

Run on `data/fixtures/crypto_universe_2015_2025_raw.csv.gz`, BTC-USD daily, 4,016 returns,
2015-01-01 → 2025-12-30 (the video claims 15 years; ours is 11).

| his claim | recomputed here | verdict |
|---|---|---|
| "typical day ~10% chance of a violent move; **after a violent day it triples to 30%**" | top-decile \|r\|: base **10.0%** → **20.1%** after a violent day (8.9% after a calm one). **Lift 2.01×, not 3×.** The 3× lift appears only at the **top-5%** threshold (5.0% → 14.9%) — a different definition from the one he states | **half the claimed size** at the stated decile; the effect itself is real |
| GARCH(1,1) on BTC: "**shock 15%, memory 85%**… almost as persistent as it is mathematically possible to be" | MLE here: ω=0.510, **α=0.126, β=0.844, α+β=0.970**; long-run ann vol 79%, shock halflife **23 days** | his rounding sums to **exactly 1.00 = IGARCH**, under which the "base level the market always carries" he calls the asset's personality **does not exist** and the variance is a random walk. His own numbers delete the third of his three components |
| GARCH is the Nobel machinery quant desks run | **corr(GARCH forecast vol, EWMA(λ=β)) = 0.9961.** corr with a plain **20-day trailing realised vol** — the estimator [D110](decisions/D110-vol-target-sizing-lives-in-the-weight.md) already uses — **= 0.8935** | on this series the model is a 99.6%-correlated relabelling of an exponentially weighted average of squared returns, and adds ~11% of variance in the vol *level* over the incumbent estimator, before any sizing decision |
| Nasdaq, 50y: vol targeting "cost a full point of CAGR, so **\$99 less dollars**" | 1 pp of CAGR over 50 years is **~36% of terminal wealth** at any plausible base (9%→13% all give 35.9–36.9%) | arithmetically consistent with a \$1 base; the *presentation* is the move — a third of the money, quoted in dollars so it sounds like a rounding error |

Also unreported anywhere in the video: **cost**. Vol targeting resizes every bar. This programme
measured that: [D195](decisions/D195-the-volatility-estimator-gate.md) quotes D185's portfolio
resizing cost at **1.8×/yr turnover, worth 0.025 Sharpe**. His Bitcoin arms are gross-only, and the
gap between them is **2.3–2.6 pp of CAGR on a ~103% CAGR series** (\$1 → 21,000 vs 17,900) with a
**63% max drawdown on the arm sold as risk management**.

### Why the method itself is closed

Every component already exists here, and the one question the video is actually asking was
pre-registered and answered:

- **Vol-target sizing** is built and swept — [D110](decisions/D110-vol-target-sizing-lives-in-the-weight.md)
  (`InverseVolatilityWeight`), [D118](decisions/D118-vol-target-swept-not-assumed.md) (target swept,
  not assumed), [D119](decisions/D119-risk-equalised-constant-fraction-benchmark.md) (risk-equalised
  benchmark).
- **Vol sizing as a challenger to equal weight** is pre-registered as
  [D372](decisions/D372-equal-weight-is-the-incumbent-sizing-and-the-hurdle.md) — `IV`/`IVT`/`RE`/`RW`,
  with the §5 trap that `IV` is confounded with the D339 price floor.
- **"Does a better volatility *estimate* improve sizing"** is
  [D195](decisions/D195-the-volatility-estimator-gate.md) exactly. It set a gate before running it,
  **the gate FAILED**, and step 2 — the sizing study — **was declined by its own rule**. D195's
  untested H3 is the stronger claim: the sizing defect is *structural in the weighting rule*, not an
  accuracy problem with its input, and **a better input does not fix a rule with the wrong shape.**
  The GARCH correlations above say the input on offer is barely better anyway.

### The one thing that is not recycled

[D379](decisions/D379-the-prop-account-is-a-down-and-out-call-and-hurdle-P-has-no.md)
§2 prices a prop account at **constant** size: rows indexed by annualised vol at fixed Sharpe 1.0,
`E[payout]` peaking at 0.05 and collapsing **82%** by 0.10, where `P(survive)` has fallen 0.532 → 0.030.
D379's closing caveat states that its toy assumes iid normal returns and that real P&L is
**"fat-tailed and autocorrelated, so both understate ruin."**

**Volatility clustering is that autocorrelation, measured: 2.01× at the decile on our own fixture.**
It has a direct consequence D379 does not draw and the video never approaches, because the video has
no barrier in it:

> A **constant-notional** account does not occupy one row of D379's table. It **drifts across the
> rows**, and clustering means the high-vol rows arrive in concentrated blocks. Because the barrier
> is **absorbing**, time spent where `P(survive)` has collapsed is **not offset** by the calm time
> that follows. Constant *notional* is therefore not constant *size* in the only sense the valuation
> cares about — and clustering says the drift is forecastable a day ahead.

So a vol-conditional size is worth strictly more against a knock-out barrier than on the personal
book, where the objective is linear and the same trade is merely insurance. The video's own Nasdaq
numbers are the shape of it — worst year −28.8% → −13%, worst month 10.9% → 7.7%, for ~36% of
terminal wealth — a bad trade on a linear account and possibly a good one against a barrier.

**Explicitly not extracted: the GARCH.** If this is ever run, the estimator is D110's existing
20-day trailing vol (corr 0.894 with the GARCH forecast), because D195 already declined to buy a
better one on a pre-registered gate.

**Status:** framing only. Nothing scored, no cell run, no candidate reopened, D379 not amended, and
it inherits D379's binding limit unchanged — **a valuation framework allocates an edge rather than
supplying one, and the prop candidate list is exhausted, so there is nothing to size.** Any run owes
a pre-registration ([R8](RULES.md#r8)), and D379's §2 is a fixed-vol toy, so the argument above is a
statement about *shape*, not a measurement.

### Housekeeping

Two things worth noting about the source that are not about trading. It ships a **Claude Code skill
and a Pine Script**, free, behind an email link — the product is audience, not a mentorship, which
makes it a lower-grade shill than §3/§4's. And it cites a **language model's output as an authority
on screen** ("as Fable points out") for an unmeasured behavioural claim about capitulation. The
Pine Script it describes sizes on a **trailing realised-vol percentile**, not on the GARCH forecast
it spends the video deriving — so the shipped artifact does not appear to contain the Nobel equation
at all. Read from the transcript only; the repo was not opened.

---

## 6. "In-play" stocks: two of its three categories are already answered here, and in equities the filter selects the price band where cost is largest

**Source:** `[EXTRACTED] I Only Trade Stocks That Meet This Criteria.txt` (Lance, SMB Capital).
Read 2026-09-13. A concept video with no rule, no parameter and no backtest. Its thesis: stock
selection is the first skill, and the only tickers worth trading are **in play**, meaning active for
one of three reasons — **a news catalyst, a technical catalyst** (breakout or breakdown on surging
volume), **or volatility and range expansion** (a name whose range is several multiples of its
normal range). Its supporting claims: about 25 positive-expected-value tickers exist on a given day,
fewer than five move P&L, and **5 to 10 stocks make 90% of a trading firm's profits**.

### The thesis is not new here. It is what the books already do, unasked

**D339's census: `retrace_leg` takes 61.3% of its P&L from the 12.2% of trades entered below $5** —
+805 bp against +76 — and those are the high-volatility names (FINDINGS §51). The equity books are
already concentrated in exactly the population this video says to select. **The repo's reading of
that fact is the opposite of the video's**: not "we found the broken slot machine" but *"the books
may be harvesting a volatility premium rather than exercising selection skill — a different object,
priced differently, with different capacity."*

### And in equities the filter selects the price band where cost is largest

This is the parse worth keeping, because it reverses the intuition. **Whether "in play" helps
depends entirely on the shape of the cost model:**

- **Fixed-dollar cost (futures micros).** Cost is $3 a round trip whatever happens, so selecting a
  bigger move raises cost coverage. But FINDINGS §69 measured the ratio at **2.4% of the average
  MNQ day move**, and its own corollary is that *selecting high-volatility days to raise the move
  against a fixed fee only pays where cost/E|M| is large* — scalping, or the 15-minute bar (D472).
  At 2.4% there is almost nothing to win.
- **Proportional, price-inverse cost (equities).** Cost in bp scales inversely with price, which is
  what **killed D284**; D285 assumed 15 bp a side and the **names actually held measured 33.8**. The
  in-play population is disproportionately low-priced and wide, so the filter **raises** cost in bp
  at the same time as it raises the move. Whether cost over E|M| improves is an empirical question
  with the sign undetermined, and the two studies that met it head-on both died on the cost side.

**So the video's central mechanism is a cost-coverage argument it never makes and never measures,
and the one regime where this programme found that lever binding is the short-horizon, wide-tick
one — not the day session it is talking about.**

### Its headline statistic is this programme's disqualifying red flag

"5 to 10 stocks make 90% of the firm's profits" is offered as proof of edge. **Measured in our own
data, that shape is the failure mode**, and the rules that say so were written before this video was
read:

| where it was measured | the number |
|---|---|
| D285 | the top 1% of trades = **196.9% of P&L** |
| D446 | GameStop's January-2021 trade = **29% of the long leg** |
| D503, the MACD component, forward | **3 of 632 sessions carry half the P&L**, and the **mean per trade ex-top-1% is −$0.59** |

CLAUDE.md's reporting rule requires a symmetric 1% trim precisely because of this, and D431 gave the
rule its predictive form: **predict the book from the TRIMMED mean when the top 1% carries more than
30% of P&L.** A book whose P&L is 90% from five names has no demonstrable edge, because nothing in
it says *which* five in advance.

**The reconciliation, which is real and worth stating.** Both readings can be true at once, and the
difference is not skill against luck — it is **conditional sizing with information the backtest does
not contain.** A discretionary trader who recognises the setup can press size into the five names and
hold a small clip in the rest; the concentration is then an *output of sizing*, not evidence about
the signal. A systematic book sized ex ante cannot do that, so the same concentration is evidence of
a lottery. **A claim of this shape is a statement about the sizing process, never about the
selector.**

### Two of the three categories are already tested here

1. **News catalyst — TESTED, and it made an existing signal worse.** FINDINGS §40 (D360) defines the
   tape-identified news day as exactly this video's first category: **a gap in the bottom 2% of the
   day on top-decile relative volume**, on the floored universe, 23,332 events. The gapped name
   bounces against its own baseline (+7.0 bp at 20 bars against −26.0 on random eligible days), the
   gap *up* on volume reverses (−15 a trade, t −2 to −4), and decisively: **`rev_5`'s own
   bottom-decile long earns 6.75 bp LESS on entries that arrived by a volume gap.** As a gate on an
   existing signal, the in-play state **subtracted**. That is the video's claim, run at scale, with
   the answer already on the record.
2. **Technical catalyst — TESTED as a level read, and the lines were never the ingredient.** The
   daily channel line (FINDINGS §68, D399–D483, closed by the principal) found that the level read's
   one positive cell is a dip, and that **a 4% break of the 30-bar low with NO lines earns the
   same**. The video's "clean levels" and "breaks a huge multi-month level with real velocity" are
   that construction, and the repo's version of it is closed with the lines shown to be surplus.
3. **Volatility and range expansion — the one member with no direct record.** Not as an *entry*
   (D413's ≥ 1-ATR departure zone, FINDINGS §49, is an entry) but as a **universe filter**: restrict
   the tradeable set to names whose current range is several multiples of their own trailing range,
   then run an existing cross-sectional book unchanged inside it. That specific object is unscored.

### What is worthless in it

- **"Over $100 million in verified profits."** Unverifiable, and "verified" is doing no work.
- **The three examples — Circle, IonQ, Qualcomm.** All 2025 winners, chosen after the fact, with no
  base rate and no losers shown. The video's own criterion fires on hundreds of names a year;
  showing three that worked is the selection this programme's nulls exist to price.
- **"You want stocks everyone is watching."** Our retail-flow reading says the opposite at horizons
  beyond a day: the *body* of retail flow is **+10 bp with it over a week**, but the **attention
  extreme is contrarian, −4.7% over 20 days**. An intraday trader and a 20-day horizon are different
  objects, so this is not a refutation — but "everyone is watching" is precisely the attention
  extreme, and the sign flips somewhere between the two.
- **The casino framing.** It argues that edge exists in in-play names; it never measures an edge.

### If the one surviving category is ever run

**The object:** an in-play *universe filter* — top-decile relative volume **and** range at ≥ 2× the
trailing 20-day average range, both causal — applied to an existing cross-sectional book and scored
against the same book on the complement. Half an hour on the 1,573-name daily fixture (2010–2026,
OHLCV, unadjusted, 562 delisted), which supports both terms directly.

**Four controls this repo already knows are compulsory, and which the video has none of:**

1. **Volatility-matched, not count-matched.** Matched-count ≠ matched-turnover (D279) ≠
   matched-volatility (D284). The filter selects volatility, so the control must hold it fixed or the
   comparison is circular.
2. **Price-matched as well.** D339's below-$5 band carries 61.3% of `retrace_leg`'s P&L, so an
   unmatched in-play basket is a bet on the price band rather than on the state.
3. **Randomise the partner, not the membership** (D291): a random subset re-drawn each bar churns and
   is not a control for a persistent selector.
4. **Estimate the spread of the names actually held** (CLAUDE.md group 1; D285's 33.8 bp), and report
   the passive line beside the crossed one, because the filter moves the held population into the
   wide band.

**Status:** framing plus one narrow variant. Nothing scored, no candidate reopened, and the two
categories that have records are not reopened by a video offering no measurement. The prediction, for
the file: the filter **subtracts** on an existing signal, as it did in §40, because it selects the
price band whose cost in bp is largest; if it adds anywhere it will be on a fixed-dollar cost line
rather than a proportional one.

### The companion transcript is deferred, deliberately

`Stop Trading in No Man's Land If You Want to Be Profitable.txt` (same channel) was read but is left
without a disposition prefix pending its own pass. Its concept — price inside a contracting range has
negative expected value, so trade only breaks to fresh intraday extremes — is a range-position
conditioner, which lands on **closed ground** (FINDINGS §68's channel line; D490's range reversion
losing gross on both sides), and its remaining content is psychological (paper cuts damaging
subsequent decisions) and not testable on price data. It is the weaker of the two and was not chosen.

---

## 7. [CLOSED] "No man's land": the measurable half of it is backwards in our data, and the rest is unfalsifiable

**Source:** `[CLOSED] Stop Trading in No Man's Land If You Want to Be Profitable.txt` (Lance, SMB
Capital). Read 2026-09-13. **Nothing is taken.** This entry exists only so the next session does not
re-read it; it is not a lead, and the file's convention that an entry means "worth half an hour"
does not apply here.

**The claim.** "No man's land" is price action that looks tradable and is not: stuck in a range with
volatility contracting, choppy, negative expected value. Traders bleed there by a thousand paper
cuts, and — the part the video cares about most — the paper cuts then damage the next decision, so
the real move gets skipped. Its operational rules: size down mid-range, cap attempts, and take
continuation trades only on a break to fresh intraday highs or lows.

### Its measurable half is backwards here, on three independent measurements

The claim decomposes into two conditions: **price mid-range** and **volatility contracting**. The
second is measurable on our own data with the instrument kept from D506, and it says the opposite.

**Directional accuracy of the day session by decile of the prior night's activity** (`activity_filter`,
eight roots × two signals, 2016–2023, ~190 sessions a cell):

| | quietest decile | busiest decile |
|---|---:|---:|
| the long day drift, pooled | **53.6%** | 51.8% |
| the log MACD, pooled | **53.0%** | 47.2% |
| both, mean across 16 cells | **53.29%** | **49.50%** |

**The quietest decile beats the busiest on accuracy in 14 of 16 cells**, and the accuracy-versus-
activity slope is negative in 13 of 16. This is the third time the record has pointed the same way:
**D487** found the *quiet* volatility tercile trends most, *"which is the opposite of the
volatility-gated hypothesis both sessions carried"*; **D506** found accuracy falling 2.09 points on
the busiest decile; and this resolves the whole curve rather than the two ends D506 compared.

**What that does and does not settle.** The video is about minute-scale discretionary entries inside
a consolidating stock, and this is a whole session on futures — so it is not a refutation on the
video's own turf. It refutes the **generalisation** the video insists on (*"no matter how good you
think you are, this concept applies to you"*) at the one clock we can measure, and it does so with
the sign reversed rather than merely absent.

**And the quiet decile is NOT a finding.** It is a cell chosen after looking at a curve. Declaring it
now would be exactly the selection that produced K8 — D495's "other side", promoted on an in-sample
bar, dead forward at −$4.46 a trade. If anyone ever wants it, it needs its own pre-registration, and
NQ and ES have no forward slice left (spent by D503) though YM, ZN, ZB, GC, CL and 6E do.

### The rest of it is unfalsifiable, or structurally absent from a systematic book

- **The rule cannot be wrong as stated.** Two exceptions are given — fresh breaking news, and "a very
  clear support or resistance level you can buy or short into within no man's land" — and the second
  is immediately undercut ("still lower probability than breaking out of the range"). A losing
  mid-range trade confirms the rule; a winning one was an exception. Nothing in it can fail.
- **Its central harm does not exist for us.** The mechanism the video actually argues is that a paper
  cut *damages the next decision*: the trader who lost $2,500 on two early attempts then skipped the
  trade that worked. That is a real phenomenon and it is **zero by construction in a systematic
  book** — our rules do not hesitate. So the video is an argument for automation, not for the rule
  it is selling.
- **Its level half is closed ground here.** "Clear levels" and "breaks a huge multi-month level" are
  the daily channel line (FINDINGS §68, D399–D483, closed by the principal), where the level read's
  one positive cell is a dip and **a 4% break of the 30-bar low with no lines drawn earns the same**.
- **The evidence offered is one anecdote with invented numbers** ("I don't recall the exact P&L, but
  let's say"), plus "90% or more" of paper cuts attributed to traders he works with, with nothing
  shown. Three links to other videos and a course.

### The one idea with any transfer, and why it is not taken

**The attempt cap** — "at max I want to give it two attempts" — is the only rule in the video that is
not a signal claim. It is an **exposure-count constraint**, the same family of instrument as the
activity filter kept on 2026-09-13, and by the same arithmetic it would act on P3a rather than on
edge. It is not taken because **no construction here re-enters**: the book's admitted arm takes at
most one position a session with a five-hour minimum hold and a forced flat. There is nothing for a
cap to bind on. Revisit only if a re-entering construction is ever built.

**Status:** closed. Nothing scored, nothing reopened, no candidate proposed. The one thing worth
carrying forward is the measurement above, which is already the third confirmation of a direction the
record had twice: **on the clock we can measure, quiet is where direction lives.**
