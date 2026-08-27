# D224 — The assembled strategy: best window, volume gate, and a 2-ATR trailing ratchet

**Status:** Pre-registered — written and committed BEFORE the runner exists
**Date:** 2026-08-27
**Category:** Validation & research integrity
**Source:** A user specification — take the best timeframe ratio, scale the standard 15m
parameters to it, gate entries on `EMA(volume) > SMA(volume)` while exiting on signal
regardless of the gate, and layer a 2-ATR trailing ratchet on top.

> A result section will be appended and nothing above it edited.

## What is being tested

The first **assembled** strategy this programme has run — three components stacked rather
than one rung isolated. That makes attribution the central design problem, and it is why
this runs as a **2 × 2 factorial** rather than as the full stack alone.

| cell | volume gate | trailing stop |
|---|:--:|:--:|
| **A** parent | — | — |
| **B** | yes | — |
| **C** | — | yes |
| **D** the full specification | yes | yes |

**If the stack is only run as D and it works, nothing is learned about why.** Four cells cost
the same four looks as one cell would after the fact, and they separate the gate's
contribution from the stop's — and, more importantly, expose their *interaction*, which the
prior below predicts will be negative.

## The components, each fixed here

**1. The window — selected, and the selection is disclosed.** `k = 4`, giving `(136, 36)` on
15m bars: a 33-hour channel. Chosen as the best of the six 15m-matched cells D221 and D222
measured. **This is selection on prior results and it is counted as such in the ledger**
(D214's precedent). It is at least a robust selection — k = 4 wins on both symbols and on
both the 8.3-year and 5.6-year spans:

| | k=4 | k=32 | k=96 |
|---|---:|---:|---:|
| BTCUSDT | **+0.728** | +0.558 | +0.572 |
| ETHUSDT | **+0.756** | +0.237 | +0.667 |

**2. The volume gate.** `EMA(volume, 200) > SMA(volume, 200)`, evaluated at the entry bar,
deciding whether the trade opens. **Exits are unconditional on the gate**, as specified.

The same-period construction has a property worth recording: because both averages span the
same window, the diurnal cycle largely cancels in the ratio. Measured, against D223's
pre-committed 5% ceiling:

| construction | BTC % variance from hour-of-day | ETH | fires |
|---|---:|---:|---:|
| **EMA(200)/SMA(200)** | **1.5%** | **1.2%** | 54% / 55% |
| EMA(96)/SMA(960) — 1d/10d | 2.2% | 1.8% | 45% / 44% |

It is *cleaner* than the whole-day pair D223 proposed, and it fires on a balanced 54–55% of
bars rather than D220's lopsided 39%. The gate passes the diurnal stop.

**3. The trailing stop: 2 × ATR, ratcheting.** Parameters not given in the specification and
therefore declared here rather than chosen later:

- **ATR window = 56 bars** — the standard 14 scaled by the same `k = 4` as everything else.
- **ATR convention = arithmetic mean of true range**, matching `terrain.mean_true_range`. The
  repo has no Wilder ATR anywhere and this study does not introduce one.
- **Ratchet:** for a long, the stop is `max(previous stop, high_so_far − 2·ATR)` and never
  falls.
- **Fill convention, and it is the conservative one:** if a bar's low breaches the stop, the
  fill is `min(stop, that bar's open)`. A bar that gaps through the stop fills at the open,
  not at the stop price. Assuming the stop price on a gap-through would be inventing
  liquidity that was not there.
- The stop is **re-armed fresh on every entry**; it carries nothing across trades.

## The prior — and the interaction it predicts

D223's census established two facts about this fixture that bear directly on this stack:

| quintile | BTC VR(8) | ETH VR(8) | mean \|ret\| |
|---|---:|---:|---:|
| Q1 (quiet) | **1.351** | **1.331** | 9.2 / 12.1 bp |
| Q5 (loud) | **0.671** | **0.688** | 41.3 / 54.3 bp |

`VR > 1` is trending; `VR < 1` is mean-reverting. **Loud markets revert.**

That produces a specific, falsifiable prediction about the *stack* rather than its parts:

> **The volume gate selects into exactly the regime the trailing stop is worst in.** The gate
> puts the book in loud markets; loud markets are mean-reverting; a 2-ATR trailing stop in a
> mean-reverting market is a whipsaw generator. The two components should therefore interact
> **negatively** — D should underperform the better of B and C.

If that is wrong, it is wrong for an interesting reason, and the factorial is what makes it
visible.

The second relevant prior: the parent's average trade earns **14.4 bp (BTC) / 19.9 bp (ETH)
against a 20 bp round trip** at `maker_10bp` — it does not cover its own fees. **So removing
trades at random gains money mechanically**, and any component that reduces trade count will
improve net PnL for reasons unrelated to skill.

## Hurdles

**H (selectivity) — carries the verdict.** Every cell must beat its **matched-count random
null** at or above the 95th percentile on **both** net Sharpe and net total return at
`maker_10bp`. Because random removal is profitable here, **a cell that improves net PnL but
misses the null is reported as a failure, in those words.**

**P (parent).** Must beat cell A on net Sharpe *and* net total return at `maker_10bp`.

**I (interaction).** Reported, not passed or failed: `D − max(B, C)`. A stack that is worth
more than its parts has a positive interaction; one that is worth less has a negative one.

**E (census).** ≥ 30 trades retained per symbol. Will not bind — the parent has ~1,842 and
~1,891.

**Minimum detectable effect, stated before the run: ≈ 0.18 Sharpe** (D222: ~11 symbol-years,
SE ≈ 0.11 on a paired difference). **Anything smaller is not a finding here, however it
reads.**

## Predictions, committed before the run

| | Prediction | Confidence |
|---|---|---|
| **Q1** | Every cell improves **net** PnL over A — and so does the random null, so this is not evidence | **high** |
| **Q2** | The stop (C) raises Sharpe and **cuts total return**, the pattern every filter in this programme has produced | **moderate-high** |
| **Q3** | **The interaction is negative**: `D < max(B, C)` on net Sharpe, because the gate selects into the reverting regime the stop is worst in | **moderate** |
| **Q4** | No cell clears H on both metrics on both symbols | **moderate-high** |
| **Q5** | The stop cuts the median holding period by more than half, and the resulting trade count rise partly offsets the gate's cost saving | **moderate** |

**What would change my mind:** Q4 failing — cell D clearing the random null at p95 on both
metrics on both symbols, with an effect above 0.18 Sharpe. That would be the first tradeable
result this programme has produced, and under D215/D216 it would get a fresh pre-registration
and unmined data before anyone believed it, not a promotion.

## Ledger

| block | looks |
|---|---:|
| 2 × 2 factorial | **4** |
| the window selection, disclosed (best of 6 measured cells) | **6** |
| **fresh, D224 only** | **10** |
| inherited from D217 + D218 + D220 + D221 + D222 | 84 |
| crypto-fixture prior + structure/terrain bar on this fixture | 3,739 |
| **verdict count** | **3,833** |

Zero-look: the diurnal census, the variance-ratio census, the matched-count random null, the
unfiltered parent, and the ATR itself (a sensor is not a hypothesis).

## Pre-committed stops

- **The look-ahead gate.** The stop is evaluated against the bar's own high/low, so the runner
  must never let a stop that triggers on bar *t* earn bar *t*'s full favourable move. A test
  perturbs future bars and asserts the exit index does not move.
- **The random-null gate.** As above: net improvement without null clearance is a failure.
- **No parameter search.** ATR 56, multiple 2, windows 200/200, `k = 4`. None of these is
  swept. If the stack fails, the answer is not ATR 40 or 3 ATR.
- **Nothing is promoted without unmined data**, whatever the result (D215/D216).
