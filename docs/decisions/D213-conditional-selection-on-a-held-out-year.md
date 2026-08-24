# D213 — can selection rescue it? A mined rule, and a held-out seven years

**Status:** Committed (H1–H4 confirmed; H5 void, then amended and falsified)
**Date:** 2026-08-24
**Category:** Validation & research integrity
**Source:** the observation that the strategy "works some of the time", and the question of
whether the good trades share anything

## The claim under test

**That some observable property of a setup, visible at entry, separates the trades that
work from the ones that do not — well enough to survive being carried to years it was not
found in.**

This reopens nothing. D211 closed the five components as a source of directional signal and
that stands. This is a different claim: not "does a fair value gap predict", but "does
*anything logged at entry* select". D212 stated the rule that governs it in advance —
a positive is a new hypothesis requiring its own pre-registration — so this is that
pre-registration, with its own ledger, disclosing the 102 looks behind it.

## Why the question is dangerous, and what that changes about the design

"What do the winners have in common" is the most reliable way to manufacture a result that
exists in one sample and nowhere else. With thousands of trades and eight features,
something always separates them.

**So the primary output of this study is not a filter. It is a measurement of how much
in-sample selection flatters.** The design produces three numbers, and the third is the one
worth having:

1. how good the mined rule looks **in the year it was mined from**;
2. how good it is on the **seven years it never saw**;
3. how good a rule the same procedure mines from **the same year with the outcomes
   shuffled** — pure selection, no signal, as a distribution.

Number 3 is what makes numbers 1 and 2 interpretable. If the real in-sample edge sits
inside the shuffled distribution, the mining found nothing and the design says so directly
rather than by argument.

## The development year, chosen before any outcome is read

**The earliest full calendar year in which both symbols have at least 200 base-arm trades.**

Mechanical, outcome-blind, and fixed here. Counting trades per year is a census, not a
look — this project has drawn that line since D197 and draws it again here. Choosing the
year by where the strategy did well would make everything downstream meaningless, which is
precisely the failure this rule exists to prevent.

Once the dev year is named it is **excluded from every later measurement**, permanently. It
does not appear in the out-of-sample table, in the pooled totals, or in any sensitivity.

**A disclosure that weakens this and has to be stated:** the aggregate results across all
years have already been seen — D206, D208, D210, D212. No year here is virgin. What has
*not* been done is this per-feature mining within a year, so the holdout is meaningful for
the specific rule being mined and weaker than a genuinely untouched holdout would be. It is
a holdout against *this* search, not against all knowledge of the data.

## The population and the target

**Population:** the C1-only arm — every pullback after a change of character, overlapping,
both symbols. Roughly 3,900 setups per symbol against the stacked arm's 222. Mining a rule
on 28 trades a year would be an exercise in noise, and the base arm is where the sample is.

**Target: mean gross R.** Naturally bounded by the frozen wrapper, which stops at −1R and
targets +5R, so no winsorisation is needed and no free parameter is introduced. **Net R is
explicitly not the mining target** — cost divided by a four-basis-point stop runs to 20R and
would make the exercise a search for wide stops. Costs are applied afterwards, to the
verdict, never to the search. This is D202's zero-cost diagnostic used the same way and for
the same reason.

## The eight features, fixed here

Four carried from WP4, four new. `gap_distance_atr` and `atr_to_golden` are deliberately
**dropped**: D210 measured them at +0.79 to +0.88 rank correlation with `stop_atr`, so
carrying all three would be one feature counted three times.

| feature | what it is | why it is a candidate |
|---|---|---|
| `fib_depth` | retracement at entry | the variable D208 found explains the WP3 reaction ladder |
| `stop_atr` | risk over ATR | the variable D210 found explains everything else |
| `rsi` | RSI(14) at the signal bar | the control that outlived the structural components |
| `bars_waited` | bars from change of character to entry | a fast pullback is a different animal from a slow one |
| `hour_utc` | hour of the signal bar | crypto has real session structure; the course never mentions it |
| `trend_align` | +1 if the trade is with the 200-bar close trend, −1 against | the most-cited missing filter in every critique of this style |
| `leg_bars` | bars in the impulse leg | separates an impulsive leg from a drifting one |
| `vol_regime` | ATR over its own 1,920-bar median | whether the setup fired in a calm or violent tape |

Eight, named in advance, no additions. A feature thought of after the run is a ninth look
and would be recorded as one.

## The mining procedure, fixed here

Deliberately crude, because a fine one is a search:

1. In the dev year, split each feature at its **median**. No threshold search.
2. Keep a feature if the better half beats the worse half by at least **0.10R** in mean
   gross R *and* the split holds the same sign on **both symbols**. Both conditions, stated
   now.
3. Combine every surviving feature by intersection into **one** rule. Not a best subset —
   the union of what survived, taken as it comes.

One rule out. If nothing survives step 2, that is the result and there is nothing to carry
forward.

## The hurdles for the held-out years

All required:

1. The rule's mean gross R exceeds the unfiltered arm's by ≥ **0.10R** out of sample.
2. It does so on **both symbols**.
3. Its in-sample advantage sits **above the 95th percentile** of the shuffled-outcome
   distribution — i.e. the mining found something a selection effect would not have.
4. After costs at 40 bps per side, the filtered arm's mean **net** R is positive.

Hurdle 4 is separate on purpose. A rule can carry real information and still not clear a
toll that D212 measured at 0.96R on the median base-arm trade.

## Predictions

- **H1 — at least one feature survives the dev-year split.** Confidence: **high.** With
  eight features and a 0.10R bar on a few hundred trades, something will. That is the
  point of measuring the shuffled distribution.
- **H2 — the mined rule's out-of-sample advantage is under half its in-sample advantage.**
  Confidence: **high.**
- **H3 — the rule fails hurdle 1 out of sample on at least one symbol.** Confidence:
  **moderate.**
- **H4 — the rule fails hurdle 4 regardless of hurdles 1–3.** Confidence: **high.** Costs
  are 0.96R on the median trade and no entry filter changes what the wrapper risks.
- **H5 — `trend_align` is the feature most likely to survive both in and out of sample.**
  Confidence: **low**, and named so that "we found the trend filter works" has to survive
  having been guessed in advance.

## Ledger

Opens at zero. 8 features × 2 symbols in the dev year = **16 looks**; the frozen rule on the
holdout, 2 symbols = **2**. The shuffled-outcome distribution is a control and is not a look.
The 102 looks of the structure programme are disclosed adjacent and separately counted.

---

# RESULT — appended 2026-08-24, nothing above it edited

**Development year: 2018**, the earliest in which both symbols carry 200+ base-arm trades.
Chosen on counts, before any outcome was read, and excluded from every number below.

## Two features survived, and the rule inverted out of sample

| | `BTCUSDT` | `ETHUSDT` |
|---|---:|---:|
| in-sample advantage (2018) | **+0.489R** | **+0.265R** |
| out-of-sample advantage (7 other years) | **−0.128R** | **−0.016R** |
| as a share of in-sample | −26% | −6% |

Survivors: **`bars_waited`** (wait longer for the pullback) and **`vol_regime`** (higher ATR
than its own trailing median). Both plausible. Both above the 0.10R bar on both symbols in
2018. Both worthless afterwards.

The advantage does not merely decay — it **changes sign**. Year by year on the holdout the
filter is negative in 7 of 8 years on BTC and 6 of 8 on ETH.

H1 confirmed, H2 confirmed with room to spare, H3 confirmed on both symbols rather than the
one predicted.

## The control, and what it does and does not settle

Running the identical procedure 200 times on the same 2018 trades with outcomes shuffled
within symbol:

- **54% of noise draws produce at least one "surviving" feature.** Eight features and a
  0.10R bar is enough to manufacture a rule from nothing, more often than not.
- median advantage mined from noise **+0.071R**, 95th percentile **+0.274R**, largest of 200
  **+0.410R**.
- the real rule's in-sample advantage was **+0.377R** — above the 95th percentile.

So the 2018 pattern was *more* than a selection artefact and still did not generalise. That
is the more interesting failure: not "we fooled ourselves with noise" but "a real property
of 2018 was not a property of 2019–2026". Regime, not randomness.

**A weakness of the control, recorded rather than left to be found.** The shuffle is
independent per symbol, so it destroys cross-symbol outcome correlation that real data has.
The survivor test requires both symbols to agree, and correlated real outcomes agree more
readily than independently shuffled ones — so the null distribution is **narrower than the
true selection distribution** and its 95th percentile is an easier bar than it appears. A
block shuffle preserving the cross-symbol pairing is the right fix and is a different study.

## H5 was void, then amended, then falsified

**`trend_align` was pre-registered and never tested.** A median split cannot divide a ±1
variable — the median sits on one of the two values, one side comes back empty, and the
thinness guard removes the feature. It vanished from the results table *without appearing as
a failure*.

This is D196's H4 in a new costume: there, every S5b strategy read level prices and never
the score, so ten cells came back bit-identical and the sensor was never tested at all.
Caught here the same way — by checking which keys the output actually contained rather than
trusting that eight features in means eight features out.

Amended to a split at zero and run **standalone**, deliberately not folded back into the
mined rule, because re-mining after seeing the holdout is the move the design exists to
prevent. Four further looks:

| symbol | 2018 edge | held-out edge |
|---|---:|---:|
| `BTCUSDT` | +0.041R | **+0.012R** |
| `ETHUSDT` | +0.183R | **+0.087R** |

Trading with the 200-bar trend does something on ETH and nearly nothing on BTC, and neither
clears the +0.10R bar out of sample. **The most-cited missing filter in this style is not the
missing piece.** H5 named it as most likely to survive; it survives better than the mined
rule and still not well enough.

## And none of it reaches the cost line

After costs the filtered arm returns **−1.850R and −1.476R** a trade out of sample. Hurdle 4
fails exactly as H4 predicted at high confidence, and it would have failed even if hurdles
1–3 had passed: **an entry filter changes which trades are taken and not what the wrapper
risks**, and the toll is 0.96R on the median base-arm trade. Selecting better trades cannot
fix a cost structure that is a function of the stop.

## Ledger

**22 looks**: 16 dev-year feature splits, 2 for the frozen rule on the holdout, 4 for the
`trend_align` amendment. The shuffled control is a control and is not a look. The structure
programme's 102 are disclosed adjacent and separately counted.

## The finding worth keeping

**A rule can beat a noise control in-sample and still invert out of sample.** Clearing a
selection-effect null is necessary and not sufficient — the same shape as D196's lesson that
a paired null is necessary and not sufficient, one level up. What the shuffle rules out is
*randomness*; what it cannot rule out is *a real pattern that does not persist*, and only a
holdout can see that.
