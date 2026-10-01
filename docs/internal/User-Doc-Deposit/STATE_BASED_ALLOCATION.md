# State-Based Allocation: RL vs Regime Models

**Short verdict:** RL for the allocator, no. A regime model feeding probabilities, maybe, but at the component level first, not the allocator.

## Why RL is the wrong tool here

- **Effective sample size.** The allocator only makes a real decision when two components want the slot at once. Count those collision events in the 2016–2026 data. It's probably hundreds, possibly fewer. An RL policy can't learn anything real from a few hundred decisions.
- **The simulator is the history.** RL earns its keep when you have a simulator you trust and a huge state/action space. Here the "environment" is a bootstrap of your own trades, so the agent will learn to exploit quirks of that sample. That's overfitting with extra steps.
- **Sparse, noisy reward.** Pass/bust is one bit per episode. Shaping it into something per-trade puts you back to expectancy ranking anyway.
- **Tiny action space.** Take / skip / preempt across a handful of components can be enumerated outright. RL adds nothing that brute-force simulation doesn't already give you, and you lose interpretability.
- **Live debugging.** When it does something odd on a funded account, you need to know why. System knowledge is load-bearing.

## The defensible version: meta-labelling

"AI producing the probability from state" already has a name: **meta-labelling** (López de Prado, *AFML* ch. 3). Each component's primary signal fires. A secondary model takes state features (regime, volatility, time of day, trend context) and outputs P(this trade is a winner) or conditional expectancy. Then:

- **Single slot:** take the trade if P × payoff − cost clears a threshold.
- **Collision:** rank by conditional expectancy ÷ 1-contract risk.

With integer contracts, the probability can't scale size. It becomes a **take/skip gate plus a priority score**.

### HMMs as the state source

- **Use filtered probabilities only**, P(state_t | data up to t). Viterbi or smoothed states use the future and will make the backtest look brilliant and the live account bleed.
- **Keep it to 2–3 states.** Latent state labels are unstable across refits, so check that "state 2" means the same thing in each walk-forward window.
- **Test the HMM against a dumb baseline.** A realised-volatility percentile plus a trend-strength measure often captures most of what the HMM does. If the HMM doesn't beat that, drop it.
- **Use a small model for the probability.** Logistic regression or shallow gradient boosting with a handful of features, calibrated (check the reliability curve). A deep net on this sample size is the RL problem again.

## Sequencing (cascade rule: inner loop before outer loop)

1. **Component level:** does state-conditioning improve each component on its own (gating or exit modulation) in walk-forward? Prior expectation: exit modulation is the likeliest win.
2. **Only if (1) holds:** feed the conditional expectancies into the allocator's ranking.
3. **Allocator test:** does state-conditional arbitration beat the pre-registered fixed rule on P(pass) in walk-forward Monte Carlo? If the gain is within noise, keep the dumb rule.

If (1) fails, the allocator has no information to arbitrate on, and no amount of AI on top fixes that.

## Sanity check before any of this

Count the collision events. If the constraint binds rarely, the allocator barely matters, and the state model's value lives entirely in step 1.
