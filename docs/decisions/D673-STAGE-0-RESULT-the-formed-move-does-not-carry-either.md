# D673 STAGE 0 RESULT — joining the day's move once it has formed carries nowhere: not on YM, RTY or ES, and not beyond its null on NQ. The MACD arm's later-entry gross does not reduce to a plain rule

*Design: [D673](D673-STAGE-0-DESIGN-join-the-formed-move-after-ten.md) (`d6aade7`), committed before the runner existed
(R8). Runner `scripts/stage0_d673_formed_move.py`, one run of `--run`. Numbers in
[`data/stage0_d673_formed_move.json`](../../data/stage0_d673_formed_move.json). In sample only; the vault (from
2025-03-01) was not read.*

## The answer in one line

**NOT SUPPORTED on YM, RTY and ES.** At the first hourly close after 10:00 where price is on the same side of
yesterday's close and today's open, entering that way and holding to the close earns:
- **YM −1.30 bp gross a trade (t −0.92), RTY −0.21 (t −0.11), ES +0.05 (t +0.04).** Every one sits inside both nulls.
- **NQ, where the idea came from: +1.85 bp (t 1.10), at the 55th percentile of its own within-week direction
  permutation.**

**The expected-profit filter never switches on** on the evidence roots: the rule's running mean never reaches
2 × cost.

**The MACD arm's later-entry gross, which D670 located, is not reproduced by the plainest statement of what those
entries do.**

## 1. The samples

| root | sessions used | trades (share) | σ (bp) | MDE (bp), printed first | micro cost |
|---|---|---|---|---|---|
| YM | 2,179 | 1,990 (91 %) | 62.7 | 4.55 | $3.80 |
| RTY | 1,820 | 1,680 (92 %) | 85.9 | 6.78 | $3.76 |
| ES | 2,184 | 1,970 (90 %) | 66.8 | 4.87 | $4.42 |
| NQ (dev) | 2,184 | 2,005 (92 %) | 82.6 | 5.97 | $4.07 |

- The drops are as D670's: rolls 36 (31 on RTY), circuit sessions 2–3, and the early-close holidays with the session
  after each.
- No entry needed the five-minute fill fallback.
- **The rule trades on about 91 % of sessions.** A move "forms" by 11:00 on most days, so the rule stays out of few.
- Mean hold 4.6–4.7 hours; 70–82 % of entries are at 11:00.

## 2. Gate 1 — the mechanism

| root | gross mean (t) | net mean | N1-week p50 / p95 (SE), percentile | N2 p50 / p95 (SE), percentile | ex Feb–Apr 2020 | net at +1 tick |
|---|---|---|---|---|---|---|
| **YM** | −1.30 (−0.92) | −4.08 | −0.16 / +1.87 (0.03), 17.9 | +0.05 / +2.49 (0.08), 17.0 | −1.92 | −4.81 |
| **RTY** | −0.21 (−0.11) | −4.47 | −0.54 / +2.43 (0.03), 57.4 | +0.08 / +3.59 (0.13), 45.3 | −0.49 | −5.60 |
| **ES** | +0.05 (+0.04) | −2.68 | +0.77 / +3.02 (0.03), 29.7 | +0.22 / +2.68 (0.07), 45.7 | −0.43 | −4.22 |
| NQ (dev) | +1.85 (+1.10) | −0.47 | +1.66 / +4.38 (0.04), 55.0 | +0.24 / +3.36 (0.07), 79.4 | +1.57 | −1.05 |

**Gate 1 fails on all three evidence roots.** The one-sided p-values are 0.82, 0.54 and 0.48, against Holm at a family
α of 0.025, and every mean is below both nulls' p95 by far more than 2 SE.

**On NQ the rule earns what random directions with the same weekly long share earn** (N1's median +1.66). Its +1.85 is
drift, not timing.

**The four groups (gross per trade, bp, and per-trade annualised ratios):**

| root | Sharpe gross / net | Sortino gross / net | median | win | payoff | skew | kurtosis | ex-top / ex-bottom / trimmed | maxDD at one micro | net total |
|---|---|---|---|---|---|---|---|---|---|---|
| YM | −0.31 / −0.96 | −0.41 / −1.27 | −1.11 | 49 % | 0.98 | −0.49 | 13.2 | −3.68 / +1.25 / −1.12 | $12,972 | −$12,649 |
| RTY | −0.04 / −0.77 | −0.05 / −0.99 | +2.37 | 51 % | 0.93 | −0.90 | 8.8 | −2.89 / +3.50 / +0.82 | $7,749 | −$7,027 |
| ES | +0.01 / −0.59 | +0.02 / −0.78 | +0.84 | 50 % | 0.97 | −0.67 | 11.9 | −2.36 / +2.91 / +0.49 | $10,389 | −$9,504 |
| NQ | +0.33 / −0.08 | +0.46 / −0.12 | +3.39 | 53 % | 0.95 | −0.56 | 9.2 | −1.13 / +5.38 / +2.41 | $8,733 | +$1,123 |

- **Every root's mean is below its median, with negative skew.** The left tail does the work: this rule's losers are
  the reversals of a move that looked formed.
- **The breakeven is below the cost everywhere.** The gross is 0.8 × cost on NQ and at or below zero elsewhere.

**What the winners depend on:**
- **By year, nothing is stable.** NQ's gross is 2022 (+17.4 bp) and early 2025 (+8.7); YM's best year is 2020 (+12.6);
  RTY and ES alternate in sign.
- Profitable years in net dollars: YM 3, RTY 1, ES 4, NQ 3.
- **Long beats short on YM, ES and NQ** (NQ +4.03 against −0.82). **RTY is the reverse** (−1.25 against +0.93).
- **By entry time:** the 11:00 entries, most of every book, are at −1.8 to +2.7 bp. The 13:00 entries are positive on
  all four (+5.0 to +8.4 bp on 77–118 trades); the 14:00 entries are negative on three (−9.9 to −13.3 bp on 40–59
  trades). **These are small cells, reported and not claimed.**
- There is no 0DTE-era break (NQ +1.82 before 2022-05-16, +1.91 after).

## 3. Gate 2 and the expected-profit filter

**Gate 2 is not reached.**

**The EP filter's forecast** (the expanding mean of earlier trades' gross, after 250 trades) never clears 2 × cost on
YM, RTY or ES, so the filter takes no trade there. On NQ it passes 52 trades (3 %), whose net is −21.7 bp. **The
filter keeps the rule out, which is what it is for.**

## 4. The variants (reported, never gated)

| root | V1: the 15:00 cut, paired difference (t) | V2: 09:59 unconfirmed (the arm-like subset), trades, gross (t) | the rest's gross | V3: from 10:00, gross (t) |
|---|---|---|---|---|
| YM | +0.97 (+1.83) | 603, +2.68 (+1.15) | −3.03 | −2.48 (−1.56) |
| RTY | +0.37 (+0.49) | 438, −0.23 (−0.06) | −0.20 | +1.26 (+0.55) |
| ES | +0.85 (+1.39) | 646, +0.82 (+0.39) | −0.32 | +0.04 (+0.02) |
| NQ | +0.36 (+0.51) | 580, +3.34 (+0.91) | +1.25 | +3.46 (+1.77) |

**V1:** the 15:00 last-hour cut helps on all four roots again, as in D670 (+0.36 to +0.97 bp). Here no root reaches
t 2. D670 had already measured it on these roots, so this is a repetition, not new evidence.

**V2, the arm-like subset** (days when no move had formed by 09:59):
- **It beats the rest on YM, ES and NQ, but no cell reaches t 1.2, and none is net positive except NQ's (+1.07 bp).**
- On NQ, D670's split of the arm's own later entries found t 3.69. **The plain version of those sessions gives t 0.91.**
  The gap is what the arm's two indicators add on NQ in sample.

## 5. Component line

| root | daily net Sharpe (gross) at one micro | Sortino | hit | skew | ρ K8 | ρ MACD arm | ρ D670's rule | ρ other roots |
|---|---|---|---|---|---|---|---|---|
| YM | −1.07 (−0.43) | −1.39 | 46 % | −0.67 | 0.06 | 0.21 | 0.42 | RTY 0.46, ES 0.68, NQ 0.40 |
| RTY | −0.82 (−0.08) | −1.04 | 49 % | −1.12 | 0.01 | 0.17 | 0.40 | YM 0.46, ES 0.55, NQ 0.42 |
| ES | −0.60 (−0.05) | −0.78 | 48 % | −0.99 | 0.01 | 0.26 | 0.40 | YM 0.68, RTY 0.55, NQ 0.72 |
| NQ | +0.04 (+0.36) | +0.06 | 51 % | −0.86 | 0.03 | 0.35 | 0.40 | YM 0.40, RTY 0.42, ES 0.72 |

The other session's plain-break book is missing (unmerged). No construction here is a component.

## 6. The predictions

| | prediction | outcome |
|---|---|---|
| 1 | NQ positive and clears N1-week | **FAILED**: +1.85, 55th percentile |
| 2 | at most one evidence root passes Gate 1 | held: none |
| 3 | YM fails Gate 1 | held |
| 4 | more than 60 % of trades enter at 11:00 | held: 70–82 % |
| 5 | V1 beats the primary on at least 3 of 4 roots | held: 4 of 4 |
| 6 | on NQ, V2 earns more than the rest | held: +3.34 against +1.25 |
| 7 | ES's gross is below 2 bp | held: +0.05 |

Six of seven held. I expected the rule to fail.

## 7. What this decides

**"Join the formed move and hold to the close" is recorded as not transferring,** and the MACD arm's later-entry gross
as NQ's alone in sample. The rule does not clear its null even on NQ.

**Across D669, D670 and D673:**
- **The arm's in-sample returns come from timing:** it is not riding NQ's drift, the price level or volatility.
- **Two plain rules built from its behaviour fail on every root, NQ included:** the 10:00 direction (D670) and
  confirmation after 10:00 (this record).
- **So what earns in sample is the arm's specific timing on NQ,** set by the impulse length and the 5-hour hold, which
  D669 found to be a spike.
- **No portable mechanism has been found.** That is the principal's overfitting reading, now tested three ways.

**One small ingredient repeats:** cutting a position at 15:00 when the last hour went against it helps on every root in
both D670 and D673, by 0.2–1.5 bp. It is too small to carry a book. It is an exit, not an edge.

**Proposals, each the principal's (R15):**
1. **Close the reshaping line** (D670 and D673). No plain form of the arm's behaviour carries.
2. **Amend the MACD arm's qualification in `BOOK_PROP.md`** with D669, D670 and D673:
   - the Sharpe is the top of its family, with a neighbourhood median of 0.24 and a failed deflated Sharpe;
   - no transferable mechanism exists;
   - the returns rest on NQ-specific timing.

   **Whether to keep, resize or retire the arm is the principal's decision.** The book is append-only, so any change is
   written there, not made here.
3. **Keep the 15:00 last-hour cut as a candidate exit** for any intraday book's pre-registration, where its small,
   repeated effect can be measured on unread data.
