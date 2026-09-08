# D394 ADDENDUM — the cap-5 distribution: a near-symmetric coin flip with a 20-kurtosis tail, and a cost 13× the edge

**Status:** ADDENDUM to [D394 RESULT](D394-RESULT-no-exit-rule-closes-the-gap-and-the-take-profit-inverts.md).
**DESCRIPTIVE** — no null, no hurdle, nothing admitted (R15).
**Date:** 2026-09-08 · Runner: `scripts/run_d394_cap5_shape.py` · Artifact:
`data/d394_cap5_shape.json` · 30 s · **Holdout reads: 0.**

The lowest hold in the pre-registered grid, with **no exit rule of any kind** — buy on the signal,
hold five bars, sell.

---

## 1. The shape

| | |
|---|--:|
| trades / names | 24,777 / 1,104 |
| **mean** | **+4.72 bp** |
| **median** | **+0.88 bp** |
| std | **497.99 bp** |
| t | +1.49 |
| win rate | **50.15%** |
| avg win / avg loss | +323.21 / −315.70 |
| **payoff** | **1.024** |
| **skew** | **+0.33** |
| **excess kurtosis** | **+20.5** |

**Percentiles (bp):**

| 0.1 | 1 | 5 | 10 | 25 | 50 | 75 | 90 | 95 | 99 | 99.9 |
|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| −2,905 | −1,386 | −687 | −464 | −209 | **+1** | +218 | +475 | +702 | +1,460 | +3,093 |

min **−7,673** · max **+9,299**

> **The distribution is very nearly symmetric, with enormous fat tails and a negligible positive
> drift.** The 1st and 99th percentiles are −1,386 and +1,460. Skew is only **+0.33** — this is not
> a lottery-ticket book. It is a coin flip with a slightly loaded coin: **win 50.15% of the time,
> and win 1.024× as much as you lose.**

The expectancy decomposes exactly: `0.5015 × 323.21 + 0.4985 × (−315.70) = +4.71`, the mean.
**Both edges are barely above break-even, and neither alone would produce anything.**

---

## 2. The trims say the edge is NOT tail-driven — and that is the good news

| | mean |
|---|--:|
| full | +4.72 |
| ex-top 1% | −16.97 |
| ex-bottom 1% | +25.38 |
| **symmetric trim (both 1%)** | **+3.68** |

**The middle 98% of trades earn +3.68 of the +4.72; the extreme 2% add +1.04.** So roughly
**78% of the edge lives in the body**, not the tails.

**This is the case CLAUDE.md warns about, seen from the right side:** ex-top alone is −16.97 and
looks catastrophic, but ex-bottom is +25.38 and the symmetric trim lands near the mean. **Dropping
only winners frightens on any two-sided fat-tailed book** — D307 called four cells lottery books on
exactly that mistake. **This book is not concentration-driven.**

---

## 3. A STATISTIC THAT IS MEANINGLESS HERE, and it would have been easy to quote

The runner reports:

- top 1% of trades carry **454.4%** of P&L
- top 10% carry **1,864.1%**
- bottom 1% carry **−430.9%**
- **11 trades (0.04%) reach half the P&L; 7 names of 1,104**

**Every one of those is an artifact of dividing by a near-zero denominator.** Total ledger P&L is
**117,008 bp** against a per-trade standard deviation of 498 — the total is a *small residual of two
enormous offsetting tails*, so any "share of total" explodes and "trades to half the P&L" measures
nothing.

**On this ledger the honest concentration statistic is §2's symmetric trim, not a P&L share.**
Recorded because these numbers are in the artifact and a later reader could quote them as evidence
of concentration when they are evidence of a small mean.

**The top trade is named anyway (D322):** **GME**, entered **2021-01-08** (bar 2,773), held 5,
**+9,299 bp** — the squeeze again, and 7.95% of the ledger. Worst: **LADR**, entered **2020-03-13**
(bar 2,565), held 5, **−7,673 bp** — the COVID crash.

---

## 4. Why no exit rule could have worked, in one line

| | bp | as a share of one std |
|---|--:|--:|
| edge (mean) | +4.72 | **0.95%** |
| round trip | 61.48 | **12.3%** |

> **The cost is 13× the edge, and it is 12% of the noise the trade sits in.**

A stop, target or trail reshapes *where in this distribution* a trade lands. **It cannot move a
+4.72 mean to +61.48**, and D394 measured that directly: the best of 126 cells reached +13.05.
**With a payoff of 1.024 and a 50.15% win rate there is almost nothing asymmetric for an exit rule
to exploit** — the winners and losers are the same size.

**This is also why the take-profit inversion was small.** Truncating a right tail worth +1.04 bp
above the body cannot produce a large effect in either direction.

---

**Status footer.** Descriptive only. No null, no holdout read, nothing admitted, nothing retired.
`docs/BOOK.md` holds S1 and S2, neither at capital; `docs/BOOK_PROP.md` is empty.
