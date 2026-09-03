# D298 — combining the structurally different exits

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-03
**Area:** Strategy research · **personal track**

**The holdout is not read. Holdout reads spent: 0.**

---

## The question

Three things have now beaten their own nulls, each alone:

| | rule | where | p |
|---|---|---|--:|
| **signal exit** | leave the selected set (`reversion`) | D295 B1 | 0.030 |
| **price exit** | profit target at 1.0 × vol | D295 B6 | 0.005 |
| **book overlay** | de-risk at 12 vols of drawdown | D297 X=12 | 0.015 |

**Do they combine?** That is a question about INTERACTION — whether the stack
beats the best of its parts — not about whether the stack beats the control,
which it will trivially if any part works.

**A FACTORIAL, not a list of cells**, so an interaction can be read off rather
than inferred.

| axis | levels |
|---|---|
| **S** — signal exit | none · **reversion** |
| **P** — price exit | none · **stop 1.0×vol** · **target 1.0×vol** · **stop + target** |
| **O** — book overlay | off · **X = 12, s = 0.0** |

**2 × 4 × 2 = 16 cells**, one of which is the un-exited, un-overlaid control.
Every parameter is INHERITED from the study that screened it. **Nothing is
re-searched** — not the thresholds, not X, not the base book.

**The mandated cell is `S=reversion, P=target, O=on`** — the principal's
"take profit with trailing spread and classification-change exit".

## THE LIMITATION, STATED FIRST

**The book is pinned: 19 slots and the composite selects exactly 19.** A rule
that exits a still-selected name re-enters the same name on the same bar. So:

- **reversion already forces the MAXIMUM return-to-selection** — it exits the
  instant a name stops being selected, and D295 §1 showed the book's return is
  monotone in exactly that.
- **a price exit on top of it can only churn**, because the names it exits are
  by construction still selected.

**Q2 predicts the two are near-redundant** and the runner measures it directly
rather than arguing it: the share of held bars on which `S+P` and `S` alone hold
different names. **If that share is near zero, the price axis is untestable on
this book and the answer is a bench problem, not an exit problem.**

**The overlay is not affected.** It scales whatever book it is given, so it
composes with anything.

## The statistic is SHARPE

The overlay changes exposure, so a mean comparison would penalise it for being
out of the market. Sharpe is the only currency all sixteen cells share. Reported
beside it: mean, vol, maxDD, exposure, return-per-unit-exposure, turnover, cost.

## The interaction test

For every cell, three increments — against the control, and against **each
constituent it is built from**:

```
Sharpe(S,P,O)  -  Sharpe(control)         does the stack work at all
Sharpe(S,P,O)  -  max over its own parts  does COMBINING add anything
```

**The second is the study.** A stack that beats the control and ties its best
part has discovered nothing about combining.

## The null

Composite and matched per cell, both mechanisms randomised **simultaneously**:

- **position exits** — replaced by exits drawn from that cell's OWN holding-run
  distribution, so rate and persistence match (D279; and the mismatch that
  voided D291's veto arm)
- **the overlay** — that cell's own on/off series, circularly rotated, so
  off-bar count and episode lengths match exactly (D297)

**200 draws.** The question: does exiting and de-risking *on these triggers*
beat exiting and de-risking the same amount at unrelated times?

## Pass condition

**Sharpe above the cell's own null at p < 0.05**, and — for the interaction
claim — **above the best of its own parts.** One screen-level bar, because this
is unspent data and nothing is promoted. Per D295's amendment a family-wise
floor is a promotion instrument; the **false-positive arithmetic is reported
instead** (count against expectation, the count tested against the null's own
correlated structure, and Benjamini-Hochberg).

**Cost reported, not gating.** Stage-3 question.

---

## Predictions

| | prediction | direction | confidence |
|---|---|---|---|
| **Q1** | **no combination beats the best of its own parts.** Exits that each work by accelerating return-to-selection cannot stack, because the first one already gets there | **AGAINST** | moderate-high |
| **Q2** | **`reversion + price` holds nearly identical names to `reversion` alone** — under 5% of held bars differ — so the price axis is degenerate on a pinned book | **AGAINST the design** | moderate-high |
| **Q3** | **the overlay composes additively.** It scales whatever book it is handed, so its Sharpe increment is roughly constant across S and P | for | moderate |
| **Q4** | **the mandated cell beats the control and NOT the overlay alone** — it inherits the overlay's gain and adds nothing from the two position exits | **AGAINST** | moderate |
| **Q5** | **cost rises monotonically with each axis switched on**, and the full stack is the most expensive cell | for | high |
| **Q6** | **the best cell overall contains the overlay.** Of the three screened effects it is the only one the pinning does not blunt | for | moderate |

**Q1 and Q2 are load-bearing and both are against.** Q2 in particular would mean
the study cannot answer the question it was built for — and that is worth
knowing in one run rather than after three.

## Ledger

| | |
|---|---:|
| **holdout reads spent** | **0** |
| holdout reads, whole programme | **0** |

Disclosed: **16 cells**, each against a composite matched null of 200 draws.
Every threshold is inherited from the study that screened it; the upstream
selection of `hist_L`, the partner pair and `f` is inherited and unpriced until
a holdout is read.

## Stop

**If no combination beats the best of its parts, combining exits is closed for
this book** — no third axis, no re-cut of thresholds.

**If Q2 fires** — the price axis holding the same names as reversion alone —
then the negative is about the PINNED BOOK and not about combining, and the
honest next step is the deeper bench (19 slots drawn from `hist_L`'s 25), which
is a different book and needs its own pre-registration.

**Neither outcome closes** the cost question, which now blocks two separate
results.

## Not attempted here

Any change to the base book or the bench. Re-searching any threshold. The
`trailing_capped` diagnostic from D295's correction, which was post-hoc and
carries no null.
