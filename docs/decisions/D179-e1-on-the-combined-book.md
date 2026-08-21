# D179 — E1 on the combined book: the first ensemble improvement whose interval excludes zero

**Status:** Committed
**Date:** 2026-08-21
**Category:** Analytics
**Source:** E1 clears the every-symbol bar on both books separately (D178); whether it improves their COMBINATION is a different question

## The question, and why it is not already answered

D178 established that E1 improves the long book and the short book *separately*, at both
k, on both symbols — four independent passes. It is tempting to read that as settling the
combined book too. It does not, for a structural reason:

**The ensemble is equal-VOL weighted.** The two legs are combined at inverse-volatility
weights (D-series ensemble convention). So a rule that changes each leg's volatility
changes the WEIGHTS, and a rule that changes their correlation changes how much
diversification there is to have. Improving both components and improving the combination
are separate claims, and the second can fail while the first holds — the short book's own
history is the proof: it improved the point estimate of nothing and *hurt* the combination
by −0.79 Sharpe on BTC with the entire interval negative.

## What was run

Both legs carry `failed_breakout` at **k = 3**, against the same combination without it.

k=3 rather than k=2 because k=3 was the stronger of the two on **both** books in D178
(+0.101 / +0.177 long, +0.061 / +0.101 short). Using one k on both legs is the consistent
choice; picking k per leg would be a search this comparison has no need to run, and k=2
cleared the bar everywhere anyway.

**No new configurations were introduced.** The long leg with E1 is built from
`breakout_config(BASELINE_N_ENTRY, BASELINE_N_EXIT, exit_rules=[{"type": "failed_breakout",
"k": 3}])` — byte-identical to the long study's registered `exit_e1_k3`. Both long legs are
run outside the short book's registered variant loop, so they do not enter the short pool
either. This comparison is **a different reading of trials already paid for**, and costs no
additional multiplicity on either side.

## The result

### BTC-USD

| | Without E1 | With E1 on both legs | Δ |
|---|---|---|---|
| Long leg Sharpe | +1.202 | +1.303 | +0.101 |
| Short leg Sharpe | −0.619 | −0.558 | +0.061 |
| Long/short correlation | +0.001 | +0.002 | +0.001 |
| **Combined Sharpe** | **+0.412** | **+0.526** | **+0.114** |
| Combined max drawdown | 34.0% | 29.5% | **−4.5 pp** |

Paired block bootstrap (4,000 sims, 20-bar blocks, seed 0, D120): observed **+0.114**,
90% interval **[+0.002, +0.219]**, P(E1 helps the combination) = **95.4%**.

### ETH-USD

| | Without E1 | With E1 on both legs | Δ |
|---|---|---|---|
| Long leg Sharpe | +0.775 | +0.952 | +0.177 |
| Short leg Sharpe | +0.142 | +0.243 | +0.101 |
| Long/short correlation | −0.001 | −0.001 | −0.001 |
| **Combined Sharpe** | **+0.649** | **+0.845** | **+0.197** |
| Combined max drawdown | 29.5% | 24.4% | **−5.1 pp** |

Paired block bootstrap: observed **+0.197**, 90% interval **[+0.063, +0.362]**,
P(E1 helps the combination) = **99.5%**.

## What is actually new here

**Both intervals exclude zero, and that has not happened before in this project.** Every
prior ensemble claim either spanned zero or came out negative. This is the first
combined-book improvement that is measurable rather than a point estimate sitting inside
its own noise.

**The gain does not come from the correlation.** Correlation moves by 0.001 on BTC and
0.0005 on ETH — i.e. not at all. The improvement is entirely from improving both legs while
leaving their independence intact. That is worth stating explicitly because it is precisely
the channel through which this test could have failed and did not.

**Drawdown improves alongside Sharpe**, 4–5 points on both symbols. That matters more than
the Sharpe delta for this project specifically: the long book's only defensible claim has
always been drawdown SHAPE rather than alpha, and E1 strengthens exactly that claim. The
long leg's own max drawdown falls 43.0% → 29.2% on BTC.

## What this does not establish

**The underlying books are still what they are.** The short leg remains negative on BTC
(−0.558) and the short book's deflated Sharpe is 0.038–0.538. The combined book is
*better*, not *good*.

**It is the same two instruments, again.** E1 has now passed on both books, both k, and the
combination — but every one of those passes is on BTC-USD and ETH-USD. Correlated passes on
two instruments are not the same as independent evidence. The honest next test is unchanged
from what D178 named: **E1 versus no-E1 on the D140 universe**, one configuration each,
62 coins including the ones that died, exactly as D174 did for the swing stop.

**Nothing is adopted.** As with D177 and D178, clearing the stated bar is a reason to keep
testing, not a reason to believe.

## A bug worth recording, because of how it failed

The first run of this comparison produced **no combined-E1 section at all** rather than a
wrong one. The computation sat inside the variant loop, where `results_by_key` is only
partly populated — `exit_e1_k3` is appended LAST in the variant list, so the lookup
returned `None` at the point the baseline was processed, and the `if short_e1 is not None`
guard silently skipped the whole block.

Moved after both loops, where `results_by_key` is complete, and the silent skip replaced
with a **loud `AssertionError`**: if the short E1 or short baseline result cannot be found,
the run fails rather than omitting the section.

This is the quieter cousin of the failure mode D176 recorded (dead code wearing the
appearance of a delivered requirement) and of the one that recurs throughout this project
(hardcoded prose drifting from computed data). A missing section reads as "not run yet". A
missing section that was *supposed* to be there reads the same way, which is the problem —
absence is indistinguishable from not-yet-attempted unless something shouts. The guard is
the shout.
