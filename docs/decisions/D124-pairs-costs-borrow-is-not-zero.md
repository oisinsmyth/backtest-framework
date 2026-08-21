# D124 — A pairs book pays borrow and margin; the rates are stated, swept, and never silently zero

**Status:** Committed
**Date:** 2026-08-18
**Category:** Cost architecture
**Source:** Crypto pairs study session

## Decision

Every cost stack in the BTC/ETH pairs study is three bricks, built through the declarative
`build_cost_stack` path (D102) so the dict the `TrialRegistry` hashes is the dict the stack
is built from:

```
trade_bricks            [{"type": "percent_spread", "bps": <tier fee>}]   <- byte-identical to CostTier's
carry_bricks            [{"type": "borrow_fee",      "annual_rate": 0.10}]
portfolio_carry_bricks  [{"type": "margin_interest", "annual_rate": 0.10}]
event_flow_bricks       []                                                <- spot crypto pays no dividends (D108)
```

- **The fee slot is the breakout study's, unchanged.** `breakout_study.CostTier` and its
  four tiers (maker 0/10/25 bp, taker 40 bp) are imported and used as-is, and
  `pair_cost_stack_config(tier, ...)["trade_bricks"] == tier.cost_stack_config()["trade_bricks"]`
  is asserted in the unit suite. A fee-column difference between the two reports can
  therefore never be a modelling difference. `taker_40bp` is the reference tier, for
  D114's reason: a z-score entry is a market order.
- **Borrow is 10%/yr on the short leg, and it is swept.** `BorrowFee` (D71) charges on
  each leg's own signed notional, so longs pay nothing and whichever leg is currently
  short pays on ~100% of NAV for the entire life of the trade. Sensitivities at 0%/yr and
  25%/yr ship as `cost`-group rows, plus a `carry_free` row that zeroes both carry bricks
  and is the study's direct comparability point against the breakout study's fees-only
  model (D114).
- **Margin interest is 10%/yr on `max(gross − NAV, 0)`** (D5), and `leg_weight` is swept
  over {1.0, 0.5, 0.25} as `gross`-group rows.

## Rationale

**Two legs is the easy part and it is still worth saying.** A pairs round trip is four
fills, not two, so the same tier costs twice as much per trade as it does in the breakout
study — before accounting for the fact that `ZScorePairsStrategy` re-normalizes both legs
to constant gross every bar (D61/D94), which takes annualised turnover to ~31×. Going
from `maker_0bp` to `taker_40bp` gives up 62% of the zero-fee terminal wealth here,
against "a fraction of a Sharpe point" in the breakout study. Same tiers, different
regime, and the reader is told which effect is which.

**Why borrow is not zero, and why the number is 10%.** Shorting spot BTC or ETH means
borrowing the coin from a venue. It is neither free nor stable: major-venue spot margin
borrow on BTC/ETH has run in roughly the 5–20%/yr band across this sample, spiking on
utilisation. 10%/yr is a defensible mid-range figure and it is an *assumption*, labelled
as one in the artifact's caveats — no rate history was sourced, and a real study would use
one, not least because borrow spikes correlate with exactly the dislocations this strategy
sizes into.

A silently-assumed zero would have been the single most result-corrupting choice available
to this study, and the arithmetic says so plainly: at 0%/yr the baseline ends with 1.47×
the terminal wealth it ends with at 10%/yr. That is the number the sweep exists to expose.
What makes the study's verdict robust is not the rate chosen but that **the verdict does
not move at 0%/yr either** — a 10-point range in an assumption that cannot flip a sign is
a range worth publishing rather than agonising over.

**Perpetuals cut the other way, and that is stated too.** A perp implementation would
replace borrow with funding, and BTC/ETH perp funding has historically been positive on
average — i.e. it *pays* shorts. That is the one modelling change that could move the cost
side materially in the strategy's favour, and it appears in the caveats rather than being
quietly omitted because it is inconvenient to the conclusion. It does not close an −88.7%
zero-cost gap.

**Why margin is swept rather than argued.** D96 found the gross-exposure threshold to be
the dominant cost lever on the ETF pairs book, and at `leg_weight = 1.0` this book runs
~200% gross, so D5's base is roughly NAV itself. The sweep reproduces the collapse exactly
— margin falls from 6,129 to 318 to 0 across leg weights 1.0 / 0.5 / 0.25 — which is a
clean cross-instrument confirmation of an earlier finding, and it rescues nothing:
de-levering a negative-drift strategy walks it toward cash, and against a positive
risk-free rate cash strictly beats it. Stated as a *collapse* rather than "exactly zero at
0.5", for the reason D96's own remediation recorded: at the threshold, lot rounding and
NAV drift leave trace margin on scattered bars.

**What is still missing, in one line.** No bid/ask spread, no market impact, no slippage —
D114's caveat inherited unchanged. A market order into a dislocated spread is the
adversely-selected moment to trade, and daily bars cannot see it.
