# Capacity: does the portfolio edge exist at size?

**Produced:** 2026-08-22 ·
**Snapshot:** `318edab51866d81986f1426abf9ab275908b27f2c6b0b8330a6529263c89b957` ·
**Reproduce:** `uv run python scripts/run_capacity_portfolio.py` (offline, deterministic)

## What this charges

Every number in this project before D186 assumed a fill at the quoted price **regardless of
size** — on 62 small-cap alts, rebalanced daily. This charges square-root market impact
(D66):

    impact_fraction = 1.0 x sigma_daily x sqrt(|Q| / ADV)

so total impact dollars scale as Q^1.5. The coefficient is D66's Y ~ 1 convention and is
**not swept**. Sigma and ADV are calibrated per coin from the snapshot's own bars and
volumes, and a coin with missing or zero volume **raises** rather than defaulting (D48).

The between-coin rebalancing charge from D185 stays fixed at 40 bp
throughout, so this study varies exactly one thing: **size**.

**The benchmark is charged impact too.** A passive equal-weight basket also trades to hold
its weights, and it holds every coin every day. Charging only the strategy would rig the
comparison — the principle D185 established, applied to impact.

Reference tier `taker_40bp` only: capacity is a reference-tier question and four
tiers would quadruple the runtime for a sensitivity nobody reads here.

## The sweep

| Total AUM | Per coin | Strategy Sharpe | Return | Max DD | Books destroyed | Benchmark Sharpe | Edge |
|---|---|---|---|---|---|---|---|
| $0.1M | $2k | +1.248 | +2,683% | 29.4% | 0 | +1.173 | **+0.075** |
| $0.3M | $5k | +1.246 | +2,665% | 29.4% | 0 | +1.173 | **+0.073** |
| $1.0M | $16k | +1.241 | +2,629% | 29.4% | 0 | +1.172 | **+0.068** |
| $3.0M | $48k | +1.233 | +2,573% | 29.5% | 0 | +1.172 | **+0.061** |
| $10.0M | $161k | +1.218 | +2,468% | 29.6% | 0 | +1.170 | **+0.047** |
| $30.0M | $484k | +1.194 | +2,311% | 29.7% | 0 | +1.168 | **+0.026** |
| $100.0M | $1,613k | +1.149 | +2,043% | 30.1% | 0 | +1.163 | **-0.014** |

**The edge dies at $100.0M.** Below it the strategy beats the equal-weight universe; at and above it, it does not.

The strategy's own Sharpe falls +1.248 → +1.149 across the sweep, a loss of **0.099**. Impact is the only thing that changes between rows — same signal, same rebalancing charge, same span.

**No book was destroyed at any size tested.** Impact made the fills worse all the way to $100M; it did not wipe an account out.

## The deflated Sharpe — D183's second debt

At $0.1M the portfolio scores **+1.248**
annualised. Deflated against **30 trials** (V[SRn] = 4.99e-05 daily,
both read from the long study's own published DSR inputs rather than asserted here), DSR =
**0.9996**.

The portfolio runs **one** configuration — but that configuration is the survivor of a
30-configuration search on the long book, so the pool is 30. Not
1, and not 62: **holding a selected rule on more instruments does not undo the selection
that produced it.**

Units are per-period throughout (D98): observed SR 0.06533 daily over
3,510 bars, skew +4.763, kurtosis 106.68. Feeding an annualised
Sharpe against a daily pool variance would inflate the noise floor ~19x and force the DSR
to zero regardless of the strategy — the exact bug D98 was written to close.

## Standing caveats

1. **Impact is calibrated FULL-SAMPLE** (D66's stated caveat, carried forward verbatim):
   sigma and ADV come from the whole series. A mild look-ahead in cost parameters, never in
   the signal. Per-window calibration remains deferred.
2. **A square-root impact model is not a liquidity model.** It says what a fill costs, not
   whether a counterparty exists. On a delisted coin the honest answer is that the trade
   does not happen at any price, and no coefficient expresses that.
3. **The per-coin slice is AUM / 62**, the steady-state share. Early in the sample far
   fewer coins are live and the real slice is larger, so early-period impact is understated.
4. **ADV is the whole-period mean.** A coin's volume in 2016 and in 2025 differ by orders of
   magnitude, and one average across both flatters the thin years.
5. Everything D183 and D185 carry still applies: one crypto cross-section, one
   bull-dominated decade, no out-of-sample test on a cross-section this one does not contain.
