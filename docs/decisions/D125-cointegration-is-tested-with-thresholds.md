# D125 — Cointegration is a tested premise here, not an assumption; and this is where the ADF gets critical values

**Status:** Committed
**Date:** 2026-08-18
**Category:** Validation & research integrity
**Source:** Crypto pairs study session

## Decision

`crypto_pairs_study.cointegration_report` runs, inside each walk-forward **training**
window only, two tests on the 252 training bars and reports how often each rejects:

1. **The traded 1:1 log spread.** `ln A − ln B`, demeaned, through
   `research.cointegration.adf_stat` (D93), compared against the **Dickey–Fuller τ_μ**
   table — the hedge ratio is *known*, not estimated, so only the mean is removed.
2. **The textbook Engle–Granger residual.** `ln A = α + β·ln B` fitted on the window
   (`engle_granger_beta`), its residual ADF'd against the stricter **Engle–Granger**
   table, because β was estimated from the same sample. β is reported and **not traded**,
   per D92's coherence argument.

Both critical-value tables are module constants with a stated source. The Dickey–Fuller
table is **anchored against `statsmodels.tsa.stattools.adfuller` in the unit suite** at
the study's own `train_size`, not typed in from memory (Pillar 3). The Engle–Granger table
carries an ordering invariant test instead (it must be strictly stricter at every level),
since the statsmodels API does not expose it in a form the same anchor can consume.

The diagnostic is structurally confined by construction: `walk_forward_windows` hands out
train views that physically contain no test bar (D22/D56). A unit test wrecks every bar
after window 0's training slice by a factor of 50 and asserts window 0's statistics are
bit-identical.

The report has positive and negative controls: a synthetic AR(1)-spread pair must be
detected in 100% of windows, and two independent random walks must be rejected at roughly
the nominal rate.

## Rationale

**Why the premise is tested at all.** BTC/ETH was chosen a priori, and it is famous. D22's
rule — selection belongs inside the training window, over a broad universe — cannot be
satisfied by a study with no selection step, so D70's meta-in-sample caveat applies in
full and D29's multiplicity machinery has nothing to bite on. Testing the premise is the
one honest thing left: rather than assume the pair mean-reverts because everyone says so,
measure it on training data and let the answer shape the verdict.

It did. The traded spread is stationary at the 5% level in **6 of 43** windows (14%) —
about what a 5% test fires at on noise — and the fitted β has a median of 0.74 and sits
inside D92's [0.7, 1.3] coherence band in only half the windows. So the pair fails on both
counts: the spread does not mean-revert, and the relationship the data *does* support is
not the 1:1 one being traded. That is the artifact's lead finding, not a footnote.

**Why thresholds exist here when D29 and D93 refused them.** Those decisions govern
*selection*. When the operation is "rank 1,596 candidates and take the top 5", a p-value
adds nothing that the ranking does not already provide, and the MacKinnon critical-value
machinery would be pure cost — which is exactly why `adf_stat` computes the statistic
only. This study selects nothing. The only question an ADF can answer about a *given* pair
is the binary one, and a binary answer requires a threshold. The constants live in this
study's module rather than in `research/cointegration.py` for that reason: they are this
study's need, not a change to the shared selector's contract.

**The approximation, stated rather than buried.** Running `adf_stat` (a no-constant
regression) on a demeaned series is not algebraically identical to an ADF with a constant
included, so comparing it to the τ_μ table is an approximation. Its size is measured, not
waved at: a unit test over 20 random walks bounds the divergence from statsmodels'
constant-included statistic at 0.25, and on the real fixture the worst window differs by
0.067. That is well inside the gap between the 5% and 10% critical values, so no window's
verdict turns on it — but it is written down, because the alternative was to change
`adf_stat`'s signature, and this study does not get to change an existing interface.

**What was deliberately not done.** The cointegration test is a *diagnostic*; it does not
gate a trade. Standing aside in windows that fail the test would be a different strategy
(and, on this pair, would mean standing aside 86% of the time — "do not trade this pair"
by a longer route). Making it a gate would also make it a fitted selection step, which
would need its own multiplicity accounting. It is named as the next experiment in the
artifact instead.
