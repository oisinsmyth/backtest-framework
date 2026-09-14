# D528 ADDENDUM 8 — the premise was backwards, and even the oracle fails its null

Date: 2026-09-14. Runner: `working/d528_oracle_vs_causal.py`. Evidence:
`data/d528_oracle_vs_causal.txt`. Charts: `working/d528_sample_trades.png`.

**Nothing admitted (R15).** Micro universe, in sample only; reserved slice UNREAD. The oracle arms
read the future by construction and can never be traded.

The principal asked where the edge lives and where his logic went wrong. Both ends of the
reasoning fail, independently, and the second failure is the one that closes the line.

---

## 1. The premise check that should have come first — and it is BACKWARDS

The construction's premise was "a range that has been traversed will be traversed again."
This programme's own rule is to measure a conditioner's persistence **before** designing a study
that conditions on it. It was never done. On 441,848 bars:

| | |
|---|---:|
| P(traverse ahead) | 0.1732 |
| P(traverse ahead \| traverse **behind**) | **0.1387** on 76,167 bars |
| P(traverse ahead \| **no** traverse behind) | 0.1804 |
| **lift** | **−0.0345** (SE 0.0014, **t = −25.08**) |

**A window that has just traversed its range is LESS likely to traverse it again.** The premise is
not merely unsupported — it is inverted, at 25 standard errors.

This explains a pattern that ran through ADDENDA 2–7 without being understood: `traverse` and
`cross2` repeatedly lost to **no classifier at all**, and `cross2` was the single worst cell in the
study. Both classifiers were anti-selecting. Six addenda of exit-geometry work sat on top of an
entry premise that had never been checked and was pointing the wrong way.

## 2. The oracle test, and the control that overturns it

Identical strategy in every arm — entry at 2σ, alignment, feasibility, `reflect` target, drift
frame, G = 3.0, τ = 40. **Only the traverse test moves**, from the past window to a future one.
Self-test 4 asserts every arm's trades are byte-identical to the unfiltered ones at the same bars,
so the arms differ in admission and in nothing else.

| arm | n | P(target) | win% | NET $/tr | Sharpe net | maxDD/$2k |
|---|---:|---:|---:|---:|---:|---:|
| no classifier | 717 | 11.2% | 19.2% | −5.93 | −6.02 | 2.25 |
| causal `traverse` | 109 | 11.0% | 21.1% | −1.66 | −0.65 | 0.17 |
| **oracle, next 10 bars** | 98 | **57.1%** | 64.3% | **+19.23** | **+4.99** | 0.06 |
| oracle, next 40 bars | 220 | 31.8% | 39.5% | +6.14 | +2.79 | 0.17 |

Read alone, that table says the regime is tradeable and the detector is blind. **It was reported
that way to the principal before the null column existed, and that reading is withdrawn.**

### 2.1 Against the sign-shuffle null, no arm beats its own benchmark

| arm | real gross | null p50 | null p95 | real Sharpe n | null p50 | null p95 | verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| no classifier | −1.21 | −1.07 | +0.83 | −6.02 | −5.96 | −3.51 | inside |
| causal | +3.00 | −1.20 | +3.79 | −0.65 | −2.08 | −0.35 | inside |
| **oracle, 10 bars** | +23.92 | **+28.16** | +31.79 | +4.99 | **+6.11** | +7.28 | **inside, below median** |
| **oracle, 40 bars** | +10.85 | **+14.16** | +17.48 | +2.79 | **+4.03** | +5.43 | **inside, below median** |

**Give a sign-shuffled universe the same foresight and it earns MORE than the real one.** The
oracle's Sharpe of 5.0 is a property of conditioning on the future, not of the market: selecting
windows in which price traverses a band selects windows in which price moves far in both
directions, and a reversion trade inside such a window wins by construction — identically on random
data.

The null here is the correct control precisely because **it carries the same foresight**: it
isolates "does real-market foresight beat random-market foresight", and the answer is no.

### 2.2 And real underperforms its null consistently — 4 of 4

| arm | lens | real − null p50 |
|---|---|---:|
| oracle 10 | gross $/trade | **−4.24** |
| oracle 10 | Sharpe net | **−1.12** |
| oracle 40 | gross $/trade | **−3.31** |
| oracle 40 | Sharpe net | **−1.24** |

Both oracle arms, both lenses, same sign. **A hypothesis, not a conclusion:** conditioning on a
future traversal selects, in the real market, windows whose volatility *persists*, so reversion
inside them is less clean than in a random rearrangement of the same absolute moves. This is
consistent with D526's finding that index roots are intraday-*persistent* on a bounce-free mid.

## 3. What this settles

**Both ends of the construction's logic fail, independently:**

1. **The premise is inverted** — past traversal anti-predicts future traversal at t = −25.
2. **The conclusion fails even granting the premise** — hand the strategy perfect knowledge of the
   future traversal and it still does not beat its own shuffle.

Point 2 is the stronger of the two, because it forecloses the obvious next move. **A better causal
detector cannot help**: the ceiling on detection was measured directly, and the ceiling is inside
the null. There is no point searching for a causal predictor of forward traversal — volatility
regime, time of day, volume, spread, event proximity — because the thing it would predict is not
worth money even when known perfectly.

**Where the edge lives, stated plainly: nowhere in this construction.** Not in the entry, not in
the exit geometry, not in the classification, and not in a hypothetically perfect classification.

**What survives all eight addenda** is the small unconditional effect in cell B: real,
consistently signed across all 30 geometries at `real − null` = +0.24 to +0.84, mean about **+$0.50
per trade against $4.68 of cost** (ADDENDUM 7 §1.1). That is a genuine measurement of intraday
mean reversion on quoted mids, and it is about a ninth of what it needs to be.

## 4. Disposition

1. **The mean-reversion-detector construction is finished on this evidence**, and finished for a
   reason stronger than "it loses money": its ceiling has been measured and the ceiling is inside
   the null. **The axis remains the principal's to close** — this record does not close it.
2. **Do not build a better classifier for this trade.** §2.1 is the argument against it.
3. **No component line**, no promotion, and the reserved slice
   (2026-04-11 → 2026-09-09) is **still unread** — correctly, since there is nothing to confirm.
4. **A reporting failure of mine is recorded here as part of the result.** §2's arm table was
   reported to the principal as "the regime is tradeable, the detector is blind" before the null
   column had been computed, having flagged in the same message that the oracle's window overlaps
   the trade's own horizon. The flagged risk was not partial, it was the entire effect. The lesson
   is the programme's existing one, sharpened: **an oracle arm is uninterpretable without a null
   that carries the same foresight**, and the interpretation must wait for it.
