# D180 — E1 on the D140 universe: the test D178 and D179 both named

**Status:** PRE-REGISTERED — implementation committed, **study not yet run**
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
