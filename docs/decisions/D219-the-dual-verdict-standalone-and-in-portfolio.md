# D219 — Two verdicts per arm: standalone and in-portfolio, reported side by side

**Status:** Pre-registered — written and committed BEFORE the runner exists
**Date:** 2026-08-27
**Category:** Validation & research integrity
**Source:** A user-proposed change to the acceptance criteria, and the compromise that
resolved it

> A result section will be appended and nothing above it edited.

## What is changing

Until now an arm carried **one** verdict: does it clear hurdles A–G on its own. The proposal
was to replace that with three portfolio-flavoured criteria — beat the nulls on PnL, beat the
nulls on Sharpe, beat buy-and-hold on Sharpe — on the argument that enough such strategies,
layered, would beat buy-and-hold on money.

**The resolution is that neither replaces the other. Every arm now carries two verdicts,
reported in the same table, and neither may be dropped.**

| | asks | fails when |
|---|---|---|
| **Standalone** (A–G, unchanged) | is this tradeable by itself? | it does not clear the noise floor for the number of looks taken |
| **In-portfolio** (P1–P5, new) | is this *additive to a book*? | it duplicates something already held |

The point of running both is that **they disagree, and the disagreement is the finding.**
This is D218's hurdle D one level up: naming Sharpe *and* money before the run is what turned
"beats the benchmark" into a `no` in the table rather than an addendum two days later. Naming
standalone *and* in-portfolio before the run does the same for "we can layer our way out."

## The prior, stated before the run

An exploratory pass over the 24 arms D217 and D218 already produced — **re-reporting existing
arms in new units, not new looks** (the D217 dividend addendum is the precedent) — established
the following, and D219 exists because of it:

- **The three proposed criteria are not a rubber stamp.** 2 of 24 arms pass. R2-LF and R1-LS
  each fail on exactly one leg, so the criteria are not merely firing together.
- **The two survivors correlate at 0.90**, and 0.65–0.67 with buy-and-hold. They are the two
  acceleration rungs — precisely the pair D218 showed are the same measurement
  (`I1 − C ≈ 0`). The first layering attempt produced two copies of one strategy.
- **Stacking them raised Sharpe from +0.793 to +0.800 — under one percent.** What produced
  money was *leverage*, not layering: vol-matched to buy-and-hold, a single arm returns
  +126.71% against +62.59%. Layering is what makes leverage survivable; it is not what
  converts Sharpe into PnL.
- **At rho = 0.90 the combined Sharpe ceiling is +0.823 as N goes to infinity.** The DSR floor
  on this fixture is +1.420. No number of strategies at that correlation reaches it. Five
  strategies at rho = 0.30 beat a thousand at rho = 0.90.

**So the binding variable is correlation, not count**, and P4 below exists to make that a
hurdle rather than a hope.

## The in-portfolio verdict, specified

**P1.** Beats the rotation null on **total return**, at or above the 95th percentile.

**P2.** Beats the rotation null on **Sharpe**, at or above the 95th percentile.

**P3.** Beats buy-and-hold on **Sharpe**.

**P4. Marginal contribution.** Adding the arm to the incumbent book at equal weight raises the
book's Sharpe by at least **+0.05**, and the arm's correlation with the incumbent book is
reported beside it. *This is the hurdle the proposal was missing.* An arm at rho = 0.90 has a
marginal contribution near zero and fails here on arithmetic.

**P5.** The **book's** Sharpe — not the arm's — clears `expected_max_sharpe` at the combined
count. The unit of deflation moves to the portfolio, which is the strongest form of the
argument for the change: a sleeve in a multi-strategy book is not required to be independently
tradeable, but *the book is required to be real*.

P1–P3 are the proposal as stated. P4 and P5 are what make it survive contact with the
arithmetic above.

## The incumbent book — declared now so it cannot be selected later

A greedy build that picks the best arm at each step **is a search**, and a marginal
contribution measured against a book chosen after seeing the Sharpes is not a hurdle. So two
incumbents are declared, both reported, and their properties differ deliberately:

1. **Buy-and-hold as incumbent.** No ordering decision, no peeking, zero fresh looks. Answers
   the question an allocator actually has: *does adding this to a passive book help?*
2. **Greedy build in structurally-declared order** — R3, R2, R1, I3, I2, I1, which is the
   ladder's own nesting order (simplest rung first), fixed by construction and not by
   performance. Zero fresh looks, because nothing is selected.

A **performance-greedy** build is also run, and is **counted as a search** — `K + (K-1) + ...`
candidate evaluations, added to the fresh ledger — because that is what it is. Reporting it
next to the two non-peeking builds is the whole point: if the peeking build looks much better
than the declared-order build, the difference is the size of the selection effect.

## Leverage is disclosed, never assumed

Every in-portfolio number is reported **twice**: unlevered, and vol-matched to buy-and-hold
**with financing charged** at the study's stated rate. The scratch figure that prompted this
decision (+134.30% at 2.01x) ignored financing and was an upper bound; publishing that shape
of number without the financing leg is the failure this clause exists to prevent. Max drawdown
is reported at both leverages, because a -22.7% in-sample drawdown at 2x is a risk-of-ruin
statement, not a performance statistic — and it is flattered by these arms happening to be out
of the market in March 2020, which is one event, not a property.

## The risk-free rate stops being ignorable, and this is a real correction

`run_macd_ladder.sharpe_of` uses **rf = 0**, deliberately, to stay comparable with every
STRUCTURE/TERRAIN headline. The BREAKOUT programme meanwhile uses
`breakout_study.rf_annual = 0.04` through `analytics.metrics.sharpe`, and D96's headline is
literally that a strategy *underperforms T-bills*. **The project has two Sharpe conventions and
the MACD studies picked the one that ignores cash.**

Under a PnL-first regime that was a rounding error. Under a Sharpe-first regime it is not, and
it is not neutral: these long-flat books sit in cash **~50% of the time**. The arithmetic:

> excess return of a long-flat book = exposure x (asset return - rf)

So the correction subtracts `1 x rf` from buy-and-hold and only `~0.5 x rf` from a 50%-exposure
arm. **It lowers both, and it lowers buy-and-hold roughly twice as much.**

Both conventions are therefore reported, rf = 0 and rf = 0.04, and switching silently is
forbidden — the rf = 0 column is what keeps these numbers comparable with the studies they sit
beside, and the rf = 0.04 column is the one that is economically correct for a book that holds
cash half the time.

## Predictions, committed before the run

| | Prediction | Confidence |
|---|---|---|
| **K1** | No arm clears **both** verdicts. The set that passes P1–P5 and the set that passes A–G do not intersect | **high** |
| **K2** | P4 kills the second acceleration rung outright — marginal contribution < +0.05 at rho = 0.90 | **high** |
| **K3** | On the rf = 0.04 basis, the gap between the best long-flat arm and buy-and-hold **narrows by more than half** on both Sharpe and money, because B&H gives up twice as much | **moderate-high** |
| **K4** | The performance-greedy book beats the declared-order book by a visible margin, and that margin is selection, not skill | **moderate** |
| **K5** | No book of arms available on this fixture clears P5 at the combined count. The rho = 0.90 ceiling of +0.823 against a floor of +1.420 leaves no room | **high** |

**K3 is the one to watch.** It is the only prediction whose positive branch changes an existing
published conclusion — D217's and D218's hurdle-D failures were both scored against a
buy-and-hold that was never charged for the cash it did not hold.

## Ledger

**The dual verdict applied to arms already run costs ZERO fresh looks.** It re-reports 24
existing arms in new units against pre-declared incumbents. Only the performance-greedy build
is a search, and it is counted as one.

| block | looks |
|---|---:|
| re-reporting 24 existing arms, two verdicts, two rf bases, two leverages | **0** |
| buy-and-hold incumbent + declared-order greedy build (no selection) | **0** |
| performance-greedy build over 24 candidates | counted by the runner, not typed here |
| inherited from D217 + D218 | 62 |
| disclosed prior ETF-fixture configurations + structure/terrain bar | 45,741 |

The verdict count carries the same floor as D218's: **+1.420**, and P5 is measured against it.

## Scope, and the stop

**This runs on the 57-ETF fixture first, as validation of the machinery, not as a search for a
winner.** The fixture is exhausted — D218 established that no arm anyone runs on it can clear
+1.42 — and running the dual verdict where the answer is already known is how the machinery
gets tested against a known negative before it is trusted on unmined data.

**The real test bed is `crypto_universe_2015_2025_raw` — 63 symbols**, comparable breadth to
the 57 ETFs, never asked this question by this project. It gets **its own pre-registration**,
not an extension of this one. Two complications are named now so they cannot be discovered
conveniently later: the fixture is **ragged** (1,172 to 4,017 bars per symbol, against the ETF
fixture's uniform 2,515), so Impulse MACD's 1,000-bar warm-up leaves some coins almost no live
span; and the roster is **inception-biased** by construction. Both need handling in that
record, not this one.

**The stop is unchanged in form:** if no arm clears both verdicts, the dual-verdict regime
closes as a reportable negative on this fixture and moves to crypto. A positive on one verdict
and not the other is **not** a survivor — it is the finding this decision exists to make
visible.

## What would change my mind

**K5 failing** — a book on this fixture whose *portfolio* Sharpe clears +1.420. That would mean
the correlation structure among these arms is materially better than the 0.90 the two
survivors showed, and it would make the layering argument correct on this fixture rather than
merely correct in principle. I do not expect it, and the ceiling of +0.823 as N grows is why.

---

## AMENDMENT (pre-run) — 2026-08-27

*Written BEFORE the runner exists and BEFORE any result. Nothing above this line
is edited; this section adds a reporting invariant, commits a prediction, and
corrects a claim made above.*

**Source:** the observation that ETFs and crypto are different instruments, and
that a real strategy might work on one and not the other.

### The point is correct, and the data says what form the allowance takes

Splitting the 57 ETFs by instrument volatility and re-scoring R1 long-flat —
dispersion reporting over arms already run, **zero fresh looks**:

| tercile | vol | arm Sharpe | B&H Sharpe | **arm - B&H** |
|---|---:|---:|---:|---:|
| low vol | 14.9% | +0.988 | +0.651 | **+0.337** |
| mid vol | 23.9% | +0.789 | +0.512 | **+0.277** |
| high vol | 37.4% | +0.549 | +0.284 | **+0.265** |

The raw Sharpe collapses as volatility rises. **Buy-and-hold on the same
instruments collapses just as fast, so the delta is nearly flat.** Splitting
instead by each asset's own drift gives the same answer: +0.263, +0.366, +0.213.

The rule is not worse on volatile instruments. Those instruments were worse, and
the rule inherits whatever the instrument does.

### The invariant this adds

> **Every cross-fixture comparison is made on `arm - matched buy-and-hold`,
> never on raw Sharpe.**

Comparing an ETF Sharpe against a crypto Sharpe compares the *instruments*, not
the strategies. This closes a specific trap: crypto's raw Sharpes may come back
far higher purely because BTC rose ~300x inside the window, and that would say
nothing about the rule. The delta is the only quantity with a claim to transfer.

### The prediction, committed now

**K6.** On the crypto fixture the **delta** transfers to within +/-0.15 of the ETF
value (~+0.28), while the **level** does whatever crypto's own buy-and-hold does.
Confidence: **moderate**. Falsifiable, unlike "crypto is different".

**What limits it, stated now rather than when it becomes convenient:**
correlation(instrument vol, instrument B&H Sharpe) = **-0.42** in this universe,
so high-vol and weak-drift are partly the same split and cannot be fully
separated here. Crypto sits **outside the observed range on both axes** — high
vol *and* high drift, where this universe only offered high vol *with* weak
drift. The extrapolation is therefore unsupported by the ETF data, which is a
reason to run crypto rather than a reason to predict it.

### The guard against the obvious abuse

"Instruments differ" explains away any negative, and if ETFs fail while crypto
passes, that sentence is available for free. It is the mirror of what D218 was
built to catch: that study asked whether two different-looking things were the
same; this asks whether two same-looking tests are different. Both fail
identically if decided after the fact. **So the expected direction and its
mechanism are committed before the crypto run (K6 above), and a difference that
was not predicted is recorded as unexplained rather than as an instrument
effect.**

### CORRECTION to the Scope section above

That section argues the crypto fixture is worth moving to because the inherited
ETF prior does not apply there. **The size of that relief was overstated.**
Measured:

| | N | floor (D217 var_trials) | floor (D218 var_trials) |
|---|---:|---:|---:|
| ETF fixture | 45,765 | +0.638 | +1.420 |
| crypto (ETF prior drops away) | 3,763 | +0.547 | +1.217 |
| crypto, fresh only | 24 | +0.299 | +0.667 |

Dropping ~42,000 inherited looks buys **0.09-0.20 Sharpe**, not a
transformation, because `expected_max_sharpe` grows like `sqrt(2 ln N)` and is
logarithmic in the count. ETF registries hold 45,346 distinct configs against
crypto's 3,344, and that 12x reduction is nearly invisible in the floor.

**What actually sets the floor is `var_trials`, estimated from each study's own
sweep.** A 5x change there moves the floor further than a 1,900x change in N.
D218's +1.420 was high in large part because its sensitivity block swept a rung
already established as anti-predictive, scattering the Sharpes and inflating the
variance. That is conservative and therefore safe, but it means the published
number is *"the floor if all of my own dispersion were noise"* rather than the
noise floor, and no study in this project has said so out loud until now.

**The case for crypto therefore does not rest on multiplicity relief.** It rests
on the fixture being unmined for this question and on K6 being falsifiable there.
That is a weaker argument than the one written above, and it is the true one.
