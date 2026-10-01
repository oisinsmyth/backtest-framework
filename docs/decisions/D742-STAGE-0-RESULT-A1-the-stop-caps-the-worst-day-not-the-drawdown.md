# D742 STAGE 0 RESULT (step 3, amendment A1) — the 1.0 σ_rem stop: NOT SUPPORTED as a drawdown filter. It reliably caps the worst day (−\$1,142 → −\$587; better in every bootstrap draw, p 0.0001 against random exits), but its Calmar and max-DD gains are not robust (random-exit p 0.24; P(ΔCalmar > 0) 0.47) and come from 2022–23 alone

*2026-10-01.*
- *Design: [D742-A1](D742-STAGE-0-PRE-REG-the-oracle-of-a-protective-stop-on-the-floored-nq-follow.md#amendment-d742-a1-2026-10-01-step-2-the-principals-stop-and-its-test-declared-before-it-is-scored)
  (c2cdfca1), the principal's choices.*
- *Scorer: `scripts/stage0_d742_step3_stop.py` (fa8d91ae), one run, 0.1 min.*
- *Output: `data/stage0_d742_stop_test.json`.*
- *In-sample ≤ 2023-12-29; floor A, 546 trades, one MNQ.*

## 0. The audits

- **Re-proved first:** D727's known answers; A's 546 trades; step 1's 1.0 σ_rem total (\$12,883.85, to \$0.01).
- **The self-test:** a planted loser-cutting stop is found (random-exit p 0.0001; P(ΔCalmar > 0) 1.0), and a random
  partial exit is not (p 0.60).

## 1. The books

| | total | net / trade | max DD | Calmar | worst day |
|---|---:|---:|---:|---:|---:|
| no stop (A) | \$15,751 | +\$28.85 | \$4,131 | 3.81 | −\$1,142 |
| **1.0 σ_rem stop** | \$12,884 | +\$23.60 | \$2,872 | 4.49 | **−\$587** |

The stop exits 147 trades, 18 of them winners.

## 2. The tests

**The random-exit null:** 147 random trades, each exited at a uniform random minute, 10,000 draws.

| statistic | the stop | null p50 | null p95 (p05 for DD) | p |
|---|---:|---:|---:|---:|
| **R1 Calmar** (primary) | 4.49 | 3.49 | 6.25 | **0.236** |
| R2 worst day | −\$587 | −\$1,142 | −\$888 | **0.0001** |
| R3 max DD | \$2,872 | \$3,776 | \$2,447 | 0.147 |

**The paired month-block bootstrap:** 71 months, 10,000 draws.

| difference (stop minus none) | P(better) | p05 | p50 |
|---|---:|---:|---:|
| Calmar | **0.474** | −4.46 | −0.11 |
| worst day | **1.000** | +\$276 | +\$554 |
| max DD | 0.706 | −\$2,557 | −\$567 |

**The halves** (by trade count):

| half | span | Calmar, stop / none | max DD, stop / none | net, stop / none |
|---|---|---|---|---|
| first | 2018-02 → 2021-11 | **2.30 / 3.52** | \$1,916 / \$1,883 | \$4,414 / \$6,621 |
| second | 2021-11 → 2023-12 | 2.95 / 2.21 | **\$2,872 / \$4,131** | \$8,470 / \$9,130 |

**Gate 2 fails on all three legs:** random-exit p 0.236 > 0.05; P(ΔCalmar > 0) 0.47 < 0.90; and the first half is
worse with the stop.

**Gate 3:** EARNS (6 of 6 years; \$1,159 a year without the two best).

**Reading: NOT SUPPORTED.**

## 3. Predictions (D742-A1)

| # | prediction | outcome |
|---|---|---|
| 1 | random-exit p ≤ 0.05 | **Failed** (0.236) |
| 2 | P(ΔCalmar > 0) between 0.60 and 0.90 | **Failed**, lower (0.474) |
| 3 | P(Δworst day > 0) ≥ 0.95 | **Held** (1.000) |
| 4 | NOT SUPPORTED | **Held**, but on the random-exit leg as well as the bootstrap |

## 4. What it says

1. **The stop is a worst-day control, and a robust one.**
   - It halves the worst day (−\$1,142 → −\$587). Every bootstrap draw improves it (median +\$554), and random exits
     almost never match it (p 0.0001).
   - Under the stop no day can lose more than about 1 σ_rem plus slippage. That matters for a prop account's daily loss
     rules and for hurdle P's P3 (a 2 % day on \$50k is \$1,000).
2. **It is not a drawdown control.**
   - A's drawdown is a run of ordinary losing days, not one tail day.
   - The stop's max-DD and Calmar gains are not distinguishable from random exits of the same count (p 0.15, 0.24), and
     they flip sign across the bootstrap (P 0.47).
   - Its gain sits in the 2022–23 drawdown episode. In 2018–21 it costs \$2,207 of net and lowers Calmar.
3. **What it costs:** \$2,867 of net over six years (−\$5.25 a trade), the price of the 18 winners it cuts and the losers
   it cuts that would have recovered.
4. **For the principal.**
   - As a **risk rule** (cap the worst day), the 1.0 σ_rem stop is justified by mechanism and by this test. That is
     exits truncating the losers' tails, with p 0.0001 on the worst day.
   - As a **drawdown filter**, nothing tested so far (D741's MACD agreement, this stop) reduces A's \$4,131 drawdown
     reliably. The stopped book's \$2,872 is still above the \$50k account's \$2,000 trailing barrier.

## Addendum (2026-10-01): the principal keeps the stop as a risk rule; how the book overlaps D737 (POST HOC, descriptive)

**The principal:** "Ok keep the 1.0 σ_rem stop as a risk rule. I would like you to see how often it agrees / wants to
trade at the same time as the similar strategy that is in the vault."

**The comparison.** The similar vault line is [D737](D737-PRE-REG-nq-leads-the-dow-for-the-joint-vault.md) (D735's
YM k1.0 1σ_rem cell, slot 1): MNQ, entries 10:00–14:30, the same stop, held to 15:59.
- **The script:** `scripts/diag_d742_overlap_d737.py`, with output `data/diag_d742_overlap_d737.json`.
- **The rebuild:** D737's trades come from its own frozen functions (`cell`, `check_known`: 1,699 trades, D735's mean to
  1e-9). The book is floor A plus the 1.0 σ_rem stop, with D742's total re-proved.
- **The window:** in-sample only, A's window 2018-02 → 2023-12-29.
- **It tests nothing.** A test needs its own pre-registration.

**The overlap:**

| | |
|---|---:|
| A's trade days on which D737 also trades | **513 of 546 (94 %)** |
| D737's days (in A's window) on which A also trades | 513 of 1,282 (40 %) |
| same direction on the shared days | 77 % (393 days); opposite on 120 |
| entry timing on shared days | same minute 42 %, D737 first 40 %, A first 18 %; within 30 minutes 74 % |
| daily net correlation | 0.36 (all sessions), 0.45 (shared days) |

**Where each book's money is, in A's window** (net \$):

| days | A + stop | D737 |
|---|---:|---:|
| both trade, **same direction** (393) | **+\$13,142** (+\$33.4 a day) | **+\$43,450** (+\$110.6 a day) |
| both trade, **opposite** (120) | −\$1,042 | **−\$11,955** |
| only A trades (33) | +\$784 | — |
| only D737 trades (769) | — | **−\$5,877** |
| total | \$12,884 | \$25,619 |

**The books together** (A's window, one MNQ each):

| | Sharpe (Sortino) | max DD | worst day |
|---|---|---:|---:|
| A + stop | 0.92 (1.48) | \$2,872 | −\$587 |
| D737 | 1.31 (2.20) | \$2,690 | −\$609 |
| A + stop + D737 | 1.38 (2.38) | **\$3,925** | **−\$1,156** |

**What it says (descriptive):**
1. **The floored follow is nearly a subset of D737's days.** 94 % of its days are D737 days, mostly the same direction.
   By the principal's component rule (two constructions sharing a clock and largely a signal do not diversify), A is not
   a separate component next to D737. Holding both stacks risk: the drawdown rises to \$3,925 and the worst day to
   −\$1,156, for a Sharpe gain of 0.07.
2. **In-sample, D737's money is on the days the follow agrees with it.**
   - Where both point the same way, D737 makes +\$110 a day.
   - Where they disagree it loses \$100 a day, and on the 769 days the follow abstains (calm, or no |z| ≥ 1.5) it loses
     \$7.6 a day.
   - **POST HOC:** it suggests an agreement book (D737 traded only when the floored follow agrees), like D716's
     ES-agreement book. It was seen here, on the in-sample data. Only the vault, which is unseen for both, could test it,
     through its own pre-registration in a free slot on the principal's word. D737 itself stays frozen as it is.
   - The drawdown is the cost of a regime-shaped edge traded at one micro. The options are the account size (\$150k), or
     accepting it.
