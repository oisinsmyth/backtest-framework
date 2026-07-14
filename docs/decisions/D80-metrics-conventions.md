# D80 — Metrics conventions: required rf/periods args, geometric rf, ±inf on zero variance

**Status:** Committed
**Date:** 2026-07-14
**Category:** Analytics
**Source:** Implementation session (Step 9)

## Decision

`analytics/metrics.py` (D37, D49):

- **`rf_annual` and `periods_per_year` are required arguments with no defaults.**
  A default rf=0 is the exact silent shortcut D49 exists to kill; a default 252 is
  the constant-sprinkling D17 warns about. Honesty by signature: the caller states
  its hurdle and its calendar, or it gets a `TypeError`, not a flattering number.
- rf de-annualization is **geometric**: `(1+rf_annual)^(1/periods) − 1` — chosen
  both because it's the compounding-consistent form and because it's quantstats'
  convention, letting the X-gate tie exactly at nonzero rf instead of carrying an
  explained-but-unfalsifiable delta.
- Zero-variance conventions stated and tested: flat series with positive rf →
  Sharpe = −inf (the D49 gate's "negative", honestly extreme rather than a masked
  NaN); Sortino with no downside and positive mean → +inf.
- Sortino downside = full-length RMS of negative excess (quantstats' convention,
  same reasoning as the rf choice).
- `realised_beta` = cov(returns, benchmark, ddof=1)/var(benchmark, ddof=1); loud
  errors on length mismatch and zero-variance benchmarks (D37's first-class metric —
  the tearsheet prints the ≈0 market-neutral expectation next to it).
- `max_drawdown` relocated from `engine/sweep.py` to analytics (its natural home);
  sweep imports it back — pure relocation, baselines re-run unchanged.

## Rationale

Every convention above is a place where a plausible-looking default silently
flatters results (rf=0), breaks cross-asset correctness (hard-coded 252), or hides a
degenerate input (NaN instead of signed infinity). Making the honest choice the only
expressible one is Pillar 1 applied to an API: the signature, not reviewer
discipline, is what prevents the shortcut. Matching the reference implementation's
conventions where they're defensible (geometric rf, RMS downside) converts the
X-gate from "explain the difference" to "demand exact agreement" — the stronger
test, same argument as D79.
