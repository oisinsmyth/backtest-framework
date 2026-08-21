# D172 — The short book gets a trial registry and a deflated Sharpe, and its positive results do not survive them

**Status:** Committed
**Date:** 2026-08-21
**Category:** Validation & research integrity
**Source:** Closing the gap D169/D171 recorded as standing caveats

## Decision

`run_breakdown_study.py` now registers every trial and computes a deflated Sharpe per
(symbol, tier), closing the gap the short book had carried since Phase 2. Three pieces:

1. **TrialRegistry rows.** One variant row per (symbol, variant, tier) plus one per
   walk-forward window, into `data/breakdown_study_registry.sqlite`, under the trial-id
   prefix `breakdown-v1`.
2. **Deflated Sharpe**, pool = every variant's out-of-sample daily Sharpe at that
   (symbol, tier) cell — D116's rule that for a parameter-swept study N is the number of
   CONFIGURATIONS tried, selected on identity fields in the logged config and never on
   the presence of a metric (D98).
3. **A paired block bootstrap of (combined − long-only) Sharpe** (D120), giving the
   ensemble claim an interval instead of a point estimate.

`breakout_study.log_trials` and `breakout_study.dsr_for` become **public**. Every other
study in this repo keeps its own private pair shaped to its own result type; the breakdown
book reuses this module's `VariantResult` and `run_variant` wholesale, so sharing these
two is correct and a fifth copy would not be.

## Rationale

**Why this before anything else.** D171 left the gap as a standing caveat and named it the
prerequisite for adopting any stop family. That was right, and understated: the gap was
not cosmetic. Every Sharpe the short book reported was raw, and the book had by then
searched 21 configurations. Adding a 22nd — the swing-structure trend rules under
discussion — would have deepened a hole rather than tested an idea.

**Why the bootstrap rather than Jobson–Korkie/Memmel.** The brief asks for JK/Memmel. This
project's established convention for inference on a Sharpe difference is D120's paired
block bootstrap, which answers the same question without assuming normality and preserves
the correlation between the two series by applying the same resampled bar indices to both.
Introducing a second, weaker convention for one table would be worse than reusing the
one the long study already defends. Recorded here so the deviation from the brief's
literal wording is visible rather than silent.

**Why `combined_series` was split out of `combine_books`.** The bootstrap must run on the
same equal-vol-weighted series that produced the reported point estimate. Recomputing the
weights separately would give an interval for a differently-weighted book than the number
it brackets — a quiet mismatch that makes an interval meaningless.

## What it found, which overturns the report's best results

**DSR across all four tiers: BTC 0.039–0.096, ETH 0.393–0.515.** The long study sat near
1.0 at every tier. Not one cell here reaches 0.95, and BTC does not reach 0.10 anywhere.

**This reframes the two strongest positives in the document.** ETH's 96th-percentile null
result and its clean sweep of the brief's three success criteria were computed on the best
of 21 configurations. Priced for that search, the evidence for skill is gone.

**And it lands squarely on the stop sweep.** The variant DSR selects as BTC's best is
`stop_trail_5` — the very stop D171 found taking BTC from −71.6% to −40.6%. It deflates to
0.039. That is not DSR being harsh; it is DSR doing exactly the job it exists for, on a
search this study performed and then reported. D171's refusal to *adopt* either surviving
stop was the right call for the right reason, and this is the number that proves it.

**The ensemble claim now has an interval, and one symbol is decisive.** Combined minus
long-only Sharpe: **BTC −0.79, 90% interval [−1.13, −0.44], P(helps) = 0%** — the entire
interval is negative, so adding the short book measurably hurts rather than merely failing
to help. **ETH −0.13, interval [−0.57, +0.31], P(helps) = 31%** — spans zero, so not
measurable, which is the absence of evidence and must not be reported as neutrality.

## Consequences

- The short book's honest summary is now: **a rule with no demonstrated edge, whose
  apparent successes are consistent with having looked 21 times.** Every earlier positive
  in `BREAKDOWN_RESULTS.md` is now read against its DSR.
- `trail_20` remains inert (mechanically the incumbent under another name), so 20 of the
  21 variants are distinct. The pool is **not** reduced for it: a configuration you tried
  and learned nothing from still cost you a look.
- Runtime went from ~20s to ~120s, from registry writes and two 4,000-sim bootstraps.
  Worth it.
- The DSR pool counts configurations only. It does not count the two-symbol choice, nor
  the decision to test a short book on crypto after a decade of visible crypto trend. The
  long study's framing holds: a DSR below 0.95 means "no demonstrated edge"; above 0.95
  would not mean the reverse.
- **What this unblocks:** any further stop or trend-qualifier work — including the
  swing-structure rules discussed but not built — can now be evaluated against a deflated
  benchmark instead of a raw one. That was the point of doing this first.
