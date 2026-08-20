# D110 — Inverse-volatility sizing lives in the signal→target-weight stage, not the portfolio layer

**Status:** Committed
**Date:** 2026-08-18
**Category:** Signals & strategy interface
**Source:** Breakout study session

## Decision

Inverse-volatility position sizing (weight = target annual vol ÷ trailing realized vol,
capped at 1.0× capital) is implemented as an `InverseVolatilityWeight` brick consumed by
the strategy, producing the `TargetWeight` the strategy emits. `pipeline.sizing.Sizer` is
untouched.

Realized vol is the sample stdev of `vol_window` log returns **ending at bar t−1** (D44),
annualised by √365. The brick carries a `rebalance` policy: `"at_entry"` (default — the
weight is computed once when the trade opens and held for its life) or `"every_bar"`.

## Rationale

The framework's portfolio layer has no vol-targeting sizer, and adding one would be the
wrong fix. Under D27 the pipeline boundary is *signal → target weight → orders*, and the
`Sizer`'s job is deliberately confined to converting a weight into a quantity for any
strategy without modification (D55). "How large should this signal's position be" is a
statement about the signal; it belongs on the strategy side of that boundary. So this is
genuine inverse-vol sizing, not the fixed-fractional stopgap the brief allowed for — the
`FixedWeight` brick is the control, not the fallback.

The `rebalance` policy is not a knob for its own sake; it is a measured cost. Recomputing
the target weight every bar makes the position chase a daily-updating vol estimate, and
the study prices that: `sizing_invvol_daily` spends **32–37% of all its trade costs** on
interior rebalancing (against 0.2% for a constant full weight) and gives up a large chunk
of return for it. Freezing the weight at entry is both standard trend-following practice
and the cheaper policy, so it is the default — with the daily variant kept and reported,
so the choice is evidenced rather than assumed.

One consequence worth stating, since it surprised the golden master: under next-open fills
(D103) *any* weight below 1.0 rebalances, because the target is sized on the decision
bar's close and filled at the next bar's open. Only a constant weight of exactly 1.0
generates no turnover beyond lot rounding. That is why the buy-and-hold benchmark holds a
fixed quantity rather than a fixed weight
([D115](D115-buy-and-hold-benchmark-is-a-fixed-quantity.md)).
