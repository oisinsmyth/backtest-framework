# D133 — Trade concentration is reported in two units, and the drawdown claim gets a sampling distribution against BOTH benchmarks

**Status:** Committed
**Date:** 2026-08-18
**Category:** Analytics
**Source:** Breakout Monte Carlo session

## Decision

Two arithmetic-only nulls sit alongside the path nulls (D130/D131), both at D36's n = 10,000
because they are seconds of compute on series that already exist.

**1. Trade-level concentration and bootstrap.** A trade's return is its **NAV multiple**,
`NAV(exit bar) / NAV(bar before entry) - 1`, read off the strategy's own out-of-sample equity
curve. Concentration — the share of the result carried by the top 1, 3 and 5 trades — is
reported in **two units**: share of net **cash** P&L, and share of total **log** growth.
Terminal wealth is bootstrapped by resampling those returns **with replacement**.

**2. Paired block bootstrap of the drawdown difference.** `(benchmark max DD − strategy max
DD)`, resampling **one** index vector in contiguous 20-bar blocks (D106) and applying it to
both return series — D120's pairing, reused — reported against **both** benchmarks in the
study: 100% buy-and-hold (D115) and the risk-equalised constant-fraction benchmark at the
strategy's own average exposure (D119).

## Rationale

**Why NAV multiples rather than episode cash P&L over notional.** The strategy is flat between
episodes and the engine pays no interest on idle cash, so NAV is constant outside episodes and
the per-episode multiples **telescope exactly** into the reported total return. That identity is
asserted by test, and it is what makes the bootstrap a bootstrap over terminal wealth rather than
over an approximation of it. It also sidesteps the question of what to divide an episode's cash
P&L by, which has no non-arbitrary answer once vol-target rebalancing changes the position mid
trade (D112).

**Why two units for concentration.** Cash share is the number the question asks for and the one
a reviewer will quote, and it is mechanically biased toward *late* trades: on a book that has
compounded 50x, a +20% trade produces more cash than a +200% trade did at the start. Log share
removes that bias. Reporting only the cash figure would let a fact about the calendar be read as
a fact about the strategy; reporting only the log figure would answer a question nobody asked.
Where they disagree, the artifact says which is which.

**Why shares above 100% are printed rather than clamped.** When the losing trades subtract from
the net, the winners' share of that net exceeds one. That is the finding — a handful of trades
paid for the rest — and clamping it to 100% would hide exactly the concentration the statistic
exists to expose. The same rule as D112's negative-MFE note: information, not a bug.

**Why with replacement here, when D130 insists on permutation there.** Permuting a fixed multiset
of multiplicative trade returns gives the same product every time — the identical algebra that
makes the D130 null a controlled comparison makes a permutation useless for this question. The
only informative resampling of trades is one that varies *which* trades occurred.

**Why both benchmarks for the drawdown test, and what it found.** `BREAKOUT_RESULTS.md` names the
drawdown reduction as the one finding it can defend, and a max drawdown is a single-path statistic
from n = 1 — the claim had no interval on it. Running it against buy-and-hold alone would have
confirmed it and stopped. Running it against D119's matched-exposure benchmark as well is what
D119 exists for, and the two answers differ sharply: against 100% buy-and-hold the strategy's
drawdown is shallower on ~99% of resampled histories; against a constantly-held position of the
strategy's **own average size** it is shallower on well under half. **The drawdown advantage is
therefore a lower-exposure result before it is a market-timing result**, and the artifact says so
in those words. This qualifies — it does not contradict — the earlier report: that report's
"lower at every start date, typically by half" is measured against the 100% benchmark, and remains
true of it.

**Stated limitation.** This bootstrap does not test serial dependence. Block resampling destroys
the ordering a max drawdown depends on, so the resampled drawdowns are not expected to reproduce
the observed pair; the observed difference is quoted beside the distribution, never inside it. It
answers "how often would a re-drawn history hand the strategy the shallower drawdown?", which is
the sampling-variability question the n = 1 statistic could not answer on its own.
