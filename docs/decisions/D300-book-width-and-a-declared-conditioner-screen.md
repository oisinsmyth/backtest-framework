# D300 — book width, and a declared conditioner screen

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-03
**Area:** Strategy research · **personal track**

**The holdout is not read, and this study does not read it. Holdout reads spent:
0. Programme total: 0.** The principal's instruction stands: no holdout testing.

---

## The question

**`N` has never been varied.** It fell out of `FRAC × N_BASE = 19` in D293 and
every study since — D295, D297, D298, D299 — has inherited it without testing it.
Meanwhile a diagnostic on mined data says the ranking's edge is concentrated:

| top-N per leg | positions | gross bp/bar per position | mean held half-spread |
|--:|--:|--:|--:|
| 2 | 4 | +27.64 | 61.1 |
| 5 | 10 | +18.47 | 56.8 |
| 7 | 14 | +14.83 | 60.6 |
| 10 | 20 | +12.74 | 63.1 |
| **19** | **38 — the incumbent** | **+11.27** | **78.7** |

**And cost per bar is invariant to `N`.** Turnover is
`per_bar_entries / N_slots / 2 = 1/k` — a *rate*, so halving the book does not
halve it; each position simply becomes larger. Cost moves with `N` only through
*which* names are held, and the names being dropped are the widest.

**That makes `N` the only lever found in this programme that raises gross without
paying for it in cost.** It is also the control for everything that would come
after it, which is why it goes first.

**THE DIAGNOSTIC ABOVE IS NOT EVIDENCE AND IS NOT BEING TREATED AS ANY.**
Per-rank means over ~3,187 bars with one name per rank per leg are noise at the
individual-rank level — rank 2 reads +1.49, rank 7 reads −2.75, rank 11 reads
−13.35. The *shape* motivated this record; no individual number in it is
load-bearing, and the study re-measures all of it against nulls.

## Arm 1 — fixed book width

**`N` per leg ∈ {2, 3, 5, 7, 10, 14, 19}.** Seven cells; 19 is the incumbent and
the control.

Everything else is inherited and nothing is re-searched: the D293 composite
(`hist_L` × mean-rank of the pair), the k = 5 cap, the slot-and-refill book with
D295's bar order. **No exits.** The interaction between concentration and the
exits is a real question and it is **explicitly out of scope** — adding it here
would confound the one axis this study exists to measure, and D295's price exits
carry an unfixed reference defect that should not be propagated into the control
for future work.

### Two statistics, because they will disagree

**Mean bp/bar and Sharpe are both primary.** Concentration raises the mean and
destroys diversification; a four-position book is not a portfolio. Reporting only
the mean would recommend `N = 2` and reporting only Sharpe would hide why. Both,
side by side, with vol and maxDD.

### The null: rank rotation, because a random subset is not a control

**A random subset re-draws every bar where the treatment persists**, so it churns
— D291's veto arm was voided by exactly that, and CLAUDE.md now carries the rule.
A size-matched random subset would be a turnover-mismatched control and would
flatter every cell.

**The null is a circular shift of the rank assignment within the selected 25.**
For a draw with offset `s`, the name that the composite ranks `j` is treated as
rank `(j + s) mod 25`. This preserves **each name's rank persistence exactly** —
a name that is persistently preferred becomes persistently something else — along
with the held-set size, the entry rate and the turnover. **Only the alignment
between rank order and actual preference is destroyed**, which is precisely the
question. It is D299's N2 applied to the rank axis instead of the time axis.

200 draws per cell.

**Plus a free directional diagnostic:** the **bottom-N** of the selected 25. Not
a null distribution — a sanity check. If the ranking carries ordinal information
the bottom must be worse than the top, and if it is not, nothing else in this
record means anything.

## Arm 2 — the conditioner screen, declared in advance

The motivation for a *variable* `N` is that the ranking is sharper on some bars
than others. That is a claim about an observable, and it is testable before any
rule is built.

**Four conditioners. All four are declared here so that the best of four is
priced rather than presented.** Every one is **signal-side** — computed from the
score distribution with **no returns in its construction** — which is the whole
point: a return-side conditioner fitted to which ranks happened to pay would be
fitting the noise in the table above.

| | conditioner | reading |
|---|---|---|
| **X1** | **rank gap** — percentile separation between rank `j−1` and `j`, normalised by the day's score sd | is rank 5 actually distinguishable from rank 6? |
| **X2** | **top-set dispersion** — sd of composite percentiles across the selected 25 | is the ranking sharp or bunched today? |
| **X3** | **pair agreement** — mean \|a₁ − a₂\| across the top `j` | do the two signals corroborate at depth? |
| **X4** | **breadth** — count of warm-and-live names | is there anything to pick from? |

All four are already computable from the cached `rank`, percentile and
`disagree` arrays. All are **lagged**, so `X(t)` is knowable at the close of
`t − 1`.

**Measured:** Spearman correlation between `X(t)` and the realised top-`j` spread
at bar `t`, at **all seven depths** — 4 × 7 = **28 correlations**.

### The null here is not optional and not a textbook p-value

These conditioners are **strongly autocorrelated series**, and so is realised
spread. A Spearman p-value on 3,187 overlapping bars would be wildly
overstated — it assumes independence that does not exist.

**Each correlation is scored against a circular rotation of `X`**, which
preserves `X`'s autocorrelation *exactly* and destroys only its alignment with
the returns. 200 rotations per correlation. Same construction as Arm 1's null and
as D299's N2, for the same reason.

**Multiplicity:** BH-FDR at q = 0.10 across the 28, and the **max |ρ| over the
whole screen** priced by the rotation null and reported beside the winner. Per
correlation, beating its own rotation null is the bar; this is a screen on mined
data.

**The output of Arm 2 is a hypothesis, not a finding.** Nothing here builds a
variable-`N` rule. If a conditioner survives, the rule gets its own
pre-registration and is scored **against the best fixed `N` from Arm 1** — never
against the incumbent 19, which would let it claim the concentration gain as its
own. That is D298's "vs best part" column, and it exists because a stack that
inherits its part's number and reports it as its own has discovered nothing.

## Predictions

Committed before the runner exists. Three are against.

| | prediction |
|---|---|
| **Q1** | gross bp/bar per position falls monotonically with `N` |
| **Q2** | **Sharpe does NOT peak at the smallest `N`** — diversification loss dominates below some depth, and the Sharpe peak lands at `N` ∈ [5, 10] while the mean peak lands at 2 or 3. *Against the naive reading of the table above* |
| **Q3** | **cost/bar is near-invariant to `N`** — at `N = 5` it is 0.85–0.95× the `N = 19` figure, not 0.26×. A mechanical check that the cost accounting is right; if cost scales with `N` the turnover denominator is wrong |
| **Q4** | the top-`N` beats a rank-rotated set of the same size at every depth. If this fails at `N = 19` the composite carries no ordinal information beyond membership and the study is void |
| **Q5** | the bottom-`N` is worse than the control at every depth |
| **Q6** | **no conditioner clears BH at q = 0.10.** *Against this study's own motivation* — D299 tested a variable-`N` rule conditioned on P&L state and found 1 of 24 against 1.2 expected, losing even to the deliberately-invalid control. The honest prior is that `N` is a constant, not a signal |
| **Q7** | of the four, **X1 (rank gap) is the strongest**, being the only one that is about *depth* rather than about the day |

Q4 and Q6 are load-bearing. **Q4 failing voids the study**; Q6 holding closes the
variable-`N` avenue before a runner is written for it.

## Stop conditions

- **Q4 fails** → the ranking has no ordinal content; concentration is not a lever
  and the diagnostic table was noise. Nothing else is reported as a finding.
- **Sharpe is flat in `N`** → book width is a capital-sizing decision rather than
  a research variable, and the principal's standing ruling on the holding period
  applies to it unchanged: dedicated capital takes the best gross `N`, shared
  capital the best Sharpe `N`. No further study.
- **Q6 holds** → variable `N` is not built. Arm 1's winner stands as a fixed
  setting and the next question is the entry signal, which has been frozen since
  D293 and is the largest untested surface in the programme.

## Scope and speed

**Out:** exits of every kind, the D297 overlay, the D299 ladder, and any change
to the entry signal. **The entry is frozen for this study and is named here as the
next surface, not this one.**

**Cost is reported, not gating**, and is measured with Corwin–Schultz half-spreads
**on the names actually held at each depth** — the rule D285 exists to enforce and
the one D299's runner got wrong by using a universe-wide mean. Both the mean and
robust round trips are carried, since they still disagree by 2.5×.

**Speed:** reuse D299's cache and simulator unchanged — a fixed `N` is
`simulate(A, np.full(T, N))`, and the rank-rotation null is a shift of a cached
integer array. 7 cells × 200 draws = **1,400 book simulations**; Arm 2's 5,600
rotations involve no book at all, only a Spearman on cached series. 6 shards,
processes not threads, BLAS pinned to 1.

## Files

`docs/decisions/D300-book-width-and-a-declared-conditioner-screen.md`
(this record) · runner and data to follow, in separate commits.
