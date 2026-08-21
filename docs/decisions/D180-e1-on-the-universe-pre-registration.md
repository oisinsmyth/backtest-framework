# D180 — E1 on the D140 universe: the test D178 and D179 both named

**Status:** Committed (H1, H2 and H3 all falsified — H3 reversed)
**Date:** 2026-08-21
**Category:** Validation & research integrity
**Source:** E1 has passed five times and all five are the same two instruments

> Written and committed **before** the study runs, as D173 and D178 were. The predictions
> below are falsifiable and dated by git. A result section will be appended and nothing
> above it edited.

## The question

E1 (`FailedBreakoutExit(k)` — exit when the close falls back inside the channel the entry
broke, within k bars) has cleared the every-symbol bar five times:

| Test | Result | Record |
|---|---|---|
| Long book, k=2 and k=3 | KEEP both | D177 |
| Short book, k=2 and k=3 | KEEP both — H2 falsified | D178 |
| Combined ensemble, k=3 | +0.114 / +0.197, both 90% intervals exclude zero | D179 |

**Every one of them is BTC-USD and ETH-USD.** Those five passes are not five independent
tests; they are one pair of price series asked five related questions. This is the test
both prior records named as the honest next step, and it is the same test D174 ran for the
swing stop: the D140 cross-section, mechanically screened to **contain the coins that
failed**, one fixed configuration each, nothing tuned.

## What is built

`scripts/run_e1_universe.py`. Two configurations per book, four runs total:

- **Long:** the published baseline versus that baseline plus E1. The control is
  byte-identical to `breakout_universe.baseline_variant()` — the same configuration the
  D140/D141 universe study already publishes, not a re-derivation of it.
- **Short:** the short baseline versus that baseline plus E1. E1 is **not a stop** — it
  bounds duration inside a k-bar window, not loss — so it rides alongside the incumbent
  `channel_stop` the baseline also carries and that `BreakoutStrategy` refuses to build a
  short without. The delta prices E1 alone, as in D178.

**Both books, because the claim under test is direction-agnosticism.** D178's conclusion
was that E1's mechanism is direction-agnostic by construction. Running one side would
leave exactly that claim untested. This does mean two chances rather than one, and the
scoring below accounts for it: a pass on one book and not the other is a **split**, not a
win.

**k=3 only**, fixed on D179's stated grounds (the stronger k on both books in D178, so the
consistent choice rather than one picked per side). Running both k here would convert a
single out-of-sample test into a two-configuration search on the universe, which is the
thing D141 exists to prevent.

## A methodological point D174 did not face

D174 compared **two stops**, so the two configurations always differed on every symbol.
This compares **a baseline against that baseline plus a brick**, so on any symbol where E1
never fires the two runs are the *same run* and the delta is exactly zero.

A tie is not a loss. Counting it as one understates the rule; counting it as a win inflates
it. So win rates are computed over the symbols where E1 **actually fired**, and both
denominators are reported — because a rule that never fires on half the cross-section is
telling you something true about its reach that a raw win rate would hide.

## The predictions

Scored per book, per cohort (SURVIVED / COLLAPSED / DELISTED), at `taker_40bp`.

**H1 — E1 clears a >50% win rate in every cohort on the LONG book.** Predicted **TRUE**,
moderate confidence.

The mechanism is narrow and its target is common. E1 fires only on breakouts that
immediately fail, and small-cap alts produce more failed breakouts than BTC does, not
fewer. Nothing about the rule references a price level, a volatility scale, or a regime —
the things that usually fail to transfer.

Against this: on very noisy instruments, price crossing back inside the channel within 3
bars is close to a coin flip, and E1 then becomes a near-random early exit that cuts the
winners along with the failures. That is the same mechanism that killed all four entry
filters and three of six stops in this project.

**H2 — E1 clears a >50% win rate in every cohort on the SHORT book.** Predicted **TRUE**,
low confidence.

Weaker because the short book on this universe is already catastrophic (D174: median coin
loses roughly half the account, three accounts past −100%), and improving the Sharpe of a
book that loses on that scale is not a stable thing to measure.

**H3 — the effect is LARGER in COLLAPSED/DELISTED than in SURVIVED.** Predicted **TRUE**.

This is the informative prediction and the reason the cohort split is worth reporting at
all. E1 prices failed breakouts specifically, and failed breakouts dominate exactly the
coins that died. **Noise would not sort by cohort.** If E1's gain is real and mechanistic,
it should be concentrated where its trigger is most common; if it is an artifact of two
instruments, the cohort ordering should be arbitrary.

**Confidence, stated honestly:** my last two mechanism-first predictions were wrong.
D173's H1 was falsified and D178's H2 was falsified, both times because I identified a real
mechanism and mis-ranked it against another real one. H3 is the prediction I would defend
hardest, because it is the one that fails loudly if E1 is noise.

**What would falsify each:** a win rate at or below 50% among firing symbols, in any
cohort of that book.

## Multiplicity

**None is added to either published book.** These runs go to their own registry
(`data/e1_universe_registry.sqlite`) under `e1-universe-*` prefixes, exactly as D174's did.
The long study stays at 30 configurations and the short at 27; no DSR in either report
moves because of this.

That is not a loophole — it is what D141's one-configuration-across-the-cross-section rule
buys. The configuration was fixed before it met the universe, so the universe is not part
of the search that produced it.

## What this cannot establish

A win here does not make either book worth running, and the report says so in its own
verdict. The long book's DSR sits near 1.0 only because its plateau is flat, and the short
book's is 0.04–0.538. This asks one question — whether E1's effect belongs to the rule or
to two instruments — and answers nothing about whether a breakout book has an edge.

---

# RESULT — appended 2026-08-21, after the run. Nothing above this line was edited.

**Status: H1 FALSIFIED. H2 FALSIFIED. H3 FALSIFIED, and reversed on the long book.**

E1 does not survive contact with coins it was not fitted on.

## The run reproduces every published number first

| | This run | Published | |
|---|---|---|---|
| BTC long, k=3 | +0.101 | +0.101 (D177) | ✓ |
| ETH long, k=3 | +0.177 | +0.177 (D177) | ✓ |
| BTC short, k=3 | +0.061 | +0.061 (D178) | ✓ |
| ETH short, k=3 | +0.101 | +0.101 (D178) | ✓ |

All four land exactly on the published figures. Nothing below is a measurement difference:
same rule, same code, same tier, sixty more instruments.

## H1 — the long book: FALSIFIED

| Cohort | Symbols | Wins | Losses | Win rate | Mean Δ Sharpe | Median Δ |
|---|---|---|---|---|---|---|
| **ALL** | 62 | 24 | 38 | **39%** | **−0.065** | −0.050 |
| survived | 19 | 10 | 9 | 53% | −0.022 | +0.018 |
| collapsed | 41 | 14 | 27 | 34% | −0.081 | −0.063 |
| delisted | 2 | 0 | 2 | 0% | −0.144 | −0.144 |

E1 fired on all 62 symbols, so the tie-handling built for this test turned out not to
matter. It was still the right thing to build: it was not knowable in advance, and a rule
that fires everywhere is itself a finding.

**Absolute P&L**

| Arm | Median return | Mean (ex blow-ups) | Mean Sharpe | Mean max DD | Profitable | Trades |
|---|---|---|---|---|---|---|
| baseline | **+152.4%** | +338.1% | +0.411 | 49.1% | 52/62 | 1,329 |
| + E1 | **+97.6%** | +317.2% | +0.346 | 47.0% | 50/62 | 1,732 |

E1 costs the median coin **55 percentage points of total return**, two profitable symbols
and 0.065 Sharpe, and buys 2.1pp less drawdown.

## H2 — the short book: FALSIFIED

| Cohort | Symbols | Wins | Losses | Win rate | Mean Δ | Median Δ |
|---|---|---|---|---|---|---|
| **ALL** | 62 | 30 | 32 | **48%** | **−0.010** | −0.001 |
| survived | 19 | 7 | 12 | 37% | −0.021 | −0.006 |
| collapsed | 41 | 22 | 19 | 54% | −0.003 | +0.011 |
| delisted | 2 | 1 | 1 | 50% | −0.046 | −0.046 |

A coin flip. Median return improves 6pp (−55.9% → −49.5%) while mean Sharpe slightly
worsens, which is what trimming losses and volatility together looks like. Neither is an
effect at this sample size. Two accounts still passed −100% (`LUNA1-USD`, `LUNC-USD`) —
the D175 gap, unchanged.

## H3 — FALSIFIED, and the reversal is the most informative result here

H3 predicted the gain would be **larger** in COLLAPSED/DELISTED, on the reasoning that E1
prices failed breakouts and failed breakouts dominate the coins that died. The long book
runs monotonically the other way:

> survived **−0.022** → collapsed **−0.081** → delisted **−0.144**

The prediction was not merely wrong, it was backwards. And it was the prediction I said I
would defend hardest, on the grounds that *noise would not sort by cohort*. It sorted — in
the opposite direction. Dead coins do not produce cleaner failed breakouts; they produce
more of what E1 mistakes for one.

The short book orders the way H3 predicted (collapsed 54% vs survived 37%), but on a book
whose overall effect is zero, so it carries no weight.

---

# What the data says the mechanism actually is

Four candidate explanations were tested against the cross-section rather than asserted.
Only one survives.

## Rejected: volatility

The obvious story — *E1's trigger is near-random on noisy instruments* — is the one I wrote
into the pre-registration as the argument against H1. **The data does not support it.**

| Correlation with Δ Sharpe | Long | Short |
|---|---|---|
| annualised volatility | **+0.06** | −0.17 |
| return autocorrelation | +0.21 | −0.06 |
| history length | −0.03 | +0.07 |
| baseline Sharpe | −0.02 | −0.09 |

Volatility explains essentially nothing, and it does not predict how often E1 fires either
(corr with trade growth −0.12). The instrument's noisiness is not the variable.

## The one thing that predicts the damage: how many extra trades E1 creates

| Correlation with Δ Sharpe | Long | Short |
|---|---|---|
| **E1's trade-count growth** | **−0.72** | **−0.57** |
| extra trades, absolute | −0.61 | −0.46 |

Nothing else comes close. Split the long book on it:

| E1's effect on trade count | Symbols | Mean Δ Sharpe |
|---|---|---|
| added ≤10% trades | 5 | **+0.055** |
| added ≥40% trades | 18 | **−0.220** |

`ICX-USD` went +479% → +91% while its trade count went 17 → 31. `VET-USD` gained +143pp
with its count unchanged at 22.

## But the firing rate is not a property of the instrument

E1's trade-count growth is roughly **+30% on everything**, and it is not predicted by
volatility (−0.12), baseline Sharpe (+0.04) or baseline trade count (−0.10). So the harm
is not "E1 misfires on bad coins". It is closer to: **E1 fires at a constant rate
everywhere, and what varies is how much each firing costs.**

## What makes a firing expensive: how concentrated the book's return is per trade

| Baseline trade count | Symbols | Mean Δ Sharpe | Mean trade growth |
|---|---|---|---|
| Q1: 9–17 | 15 | **−0.091** | +33% |
| Q2: 17–21 | 16 | −0.077 | +34% |
| Q3: 21–25 | 15 | −0.065 | +27% |
| Q4: 25–42 | 16 | **−0.028** | +29% |

Monotone in the damage, flat in the firing rate. A book with 12 trades carries its whole
return in a handful of them, so interrupting one is expensive; a book with 38 spreads the
same return more thinly, so an interruption costs less.

**This is what made BTC and ETH misleading, and it is measurable:**

- **BTC-USD: 38 baseline trades — the 97th percentile of the cross-section.**
- **ETH-USD: 28 baseline trades — the 85th percentile.**
- Median coin: 21.

The two instruments the rule was developed on sit in the **top quartile of trade density —
the quartile E1 damages least** — and within that quartile they happen to fall on the
positive side. They rank **9th and 3rd of 62** by Δ Sharpe.

Five "independent" passes were five readings of two unusually favourable series.

## And E1 is not noise — it is a real risk reducer that is overpriced

This is the part that is easy to miss and matters most for what to do next.

| | Long | Short |
|---|---|---|
| Max drawdown improved | **42 / 62** | 39 / 62 |
| Mean Δ max drawdown | **−2.1 pp** | −2.2 pp |
| Median Δ total return | **−7.9 pp** | +1.6 pp |

E1 reduces drawdown consistently, on both books, on roughly two-thirds of instruments. A
random exit would not do that. **The rule does what it claims** — it gets out of failed
breakouts — and on 60 of 62 coins the return it gives up exceeds the risk it removes.

The correct reading is therefore not "E1 does nothing". It is **E1 is a hedge with a real
payoff and a price, and on this cross-section the price is higher than the payoff.**

## The re-entry attribution, settled

D177 observed E1 raising the long book's trade count (38 → 44) and read that as **re-entry
being a benefit**. D178 falsified that attribution and concluded the benefit was simply not
sitting in a failed trade. The cross-section settles it, and against D177:

E1 raised the trade count on **61 of 62 long symbols and 60 of 62 short symbols**, and the
correlation between that rise and the outcome is **−0.72**. Re-entry is not the mechanism
of E1's benefit. **Re-entry is the mechanism of E1's harm**, and it only looked like a
benefit on two instruments where each re-entry was cheap.

---

# Consequences

**E1 is not adopted, and its record is now correctly stated.** Five every-symbol passes on
two instruments; one clear failure on sixty-two, on the book where it was developed.

**D179's arithmetic stands and its interpretation does not.** The combined-book numbers
reproduce exactly and the bootstrap intervals were computed correctly. But both intervals
excluded zero on a sample now demonstrated to be the rule's *best case* — BTC and ETH at
the 97th and 85th percentiles of the variable that predicts the outcome. A confidence
interval quantifies sampling error within a sample; it cannot tell you the sample was
unrepresentative. That is what this test was for, and it is why D179 named it.

**No multiplicity was added to either published book**, as pre-registered. The long study
stays at 30 configurations and the short at 27; no DSR in either report moves. These runs
live in `data/e1_universe_registry.sqlite` under `e1-universe-*`.

**The project-level pattern is now unambiguous.** Four entry filters failed. Three of six
stops failed. The swing stop transferred only as a family, with its k flipping between
books (D178). E1 passed five times on two instruments and fails on sixty-two. **Nothing in
this project has yet survived contact with instruments it was not found on.** That is not a
run of bad luck across independent tests; it is the same result each time, and the thing
being measured is the two-instrument sample, not the rules.

**What this does not say.** It does not say the long book is worthless — the baseline
returns a median +152% across this cross-section, which is a fact about a crypto bull
sample and not an edge claim. It says nothing about whether a breakout book has an edge.
The long book's DSR sits near 1.0 on a flat plateau and the short book's is 0.04–0.538, and
nothing here moves either.

## What this changes about method

**Two instruments is not a sample, and no amount of statistical machinery inside it fixes
that.** This project has built a walk-forward harness, a trial registry, deflated Sharpe,
paired block bootstraps and pre-registration — all correct, all applied, and all of them
were satisfied by a rule that does not work. Every one of those tools controls for error
*within* a sample. None of them can detect that the sample is the problem.

The cross-section is the only test in this project that has ever caught anything, and it
has now caught two of two rules put to it (D174's swing stop as a family-only transfer,
E1 outright). **Candidate rules should meet the universe before they are written up as
findings, not after.**
