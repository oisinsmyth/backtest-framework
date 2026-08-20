# D119 — A constant-fraction benchmark at the strategy's own average exposure

**Status:** Committed
**Date:** 2026-08-18
**Category:** Analytics
**Source:** Breakout study review session

## Decision

`run_constant_fraction_benchmark` holds a constant fraction *f* of capital in the
instrument and the rest in cash, through the same engine, cost tier and fill timing as
every strategy variant. The breakout report sets *f* to the strategy's own measured
average exposure and reports it as a third benchmark row, alongside 100% buy-and-hold.

It is run through the engine rather than computed, deliberately: unlike fixed-quantity
buy-and-hold (D115), a constant fraction genuinely rebalances, and that rebalancing costs
real money at these fee tiers. Charging it is the point.

## Rationale

The first version of the report compared a strategy that is in the market ~35% of the time
against a 100%-invested benchmark, and concluded from the gap that the strategy "loses
badly to buy-and-hold on BTC". That comparison answers a real question — *would you have
been better off just holding it?* — but it is not a like-for-like risk comparison, and
reading a verdict off it is a mistake in the strategy's disfavour.

Matching average exposure isolates the only thing the strategy actually claims to do:
choose **when** to take exposure. On this data that claim survives — at matched exposure
the strategy earns several times the terminal wealth of holding the same fraction
constantly, at comparable or lower drawdown, on both symbols. That is a materially better
case than the 100% row alone suggests, and it is the comparison a reviewer should be handed
first.

**Stated limitation, because matched average exposure is not a full risk match.** The
strategy concentrates its exposure into trending periods, so it runs higher realised
volatility while it is on (~41% vs ~29% annualised on BTC) even though its average exposure
and its max drawdown are similar. And by D120's bootstrap, the Sharpe difference against
this benchmark is *also* inside the noise band. The return and drawdown differences are the
defensible findings; the Sharpe difference is not, against either benchmark.

## Why not simply report both and let the reader choose

Both are reported. The addition here is that the report now says which question each row
answers, rather than presenting the 100% row as *the* benchmark and drawing a conclusion
from it. Per D115's benchmark-frame note (D37 inverted for a directional strategy), a
long-only benchmark is the right frame for this strategy — but *which* long-only benchmark
is a choice that changes the verdict, so it is made explicitly.
