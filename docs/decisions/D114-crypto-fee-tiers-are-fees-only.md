# D114 — Crypto cost tiers model an exchange fee and nothing else, stated loudly

**Status:** Committed
**Date:** 2026-08-18
**Category:** Cost architecture
**Source:** Breakout study session

## Decision

The breakout study's cost tiers are a single `percent_spread` brick each, built through the
declarative `build_cost_stack` path (D102):

| tier | fee | role |
|---|---|---|
| `maker_0bp` | 0.00% | maker |
| `maker_10bp` | 0.10% | maker |
| `maker_25bp` | 0.25% | maker |
| `taker_40bp` | 0.40% | taker |

No commission, no bid/ask spread, no market impact, no funding, no borrow. `taker_40bp` is
the **reference tier** the headline verdict is read at. `role` is a label, not a mechanism.

## Rationale

The brief asked specifically whether the maker/taker difference decides viability, and a
one-brick-per-tier stack answers exactly that question with nothing else moving. Adding
sqrt-impact (D3) would have been defensible but would confound the measurement: the study's
own finding is that the fee range moves the result by a fraction of a Sharpe point, and
that finding is only legible if fees are the only thing varying.

The cost of that clarity is that every number in the study is optimistic, and the report
says so in its first caveat rather than in a footnote. Two things are worth separating:

- **The 0.40% taker tier is a fee, not a cost.** Sending a market order into an instrument
  that has just printed a 40-day high is the most adversely-selected moment to be a buyer.
  On daily bars that slippage is invisible, and it is plausibly larger than the entire
  0–40 bp range this study sweeps.
- **The maker tiers are a lower bound, not an execution plan.** Earning a maker fee means
  resting a limit order and accepting no fill in the fastest breakouts — which are the
  trades that pay. Treating `maker_10bp` as "how this would be run" inverts the result.
  The maker rows answer "how much of the outcome is fees?", and that is all they answer.

Because the tiers are declarative, the dict the TrialRegistry hashes is the dict the stack
is built from, so no trial can drift from its stated cost model.
