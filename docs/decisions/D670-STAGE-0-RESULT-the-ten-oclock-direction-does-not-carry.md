# D670 STAGE 0 RESULT — the move since yesterday's close, taken at 10:00 and held to the close, carries nowhere: not on YM or RTY, not on ES, and not on NQ, where it was found. The arm's money is in its later entries, which D669's reading missed

*Design: [D670](D670-STAGE-0-DESIGN-carry-the-overnight-direction-from-ten.md) (`772ade0`), committed before the runner
existed (R8). Runner `scripts/stage0_d670_overnight_direction.py`. Numbers in
[`data/stage0_d670_overnight_direction.json`](../../data/stage0_d670_overnight_direction.json). A post-hoc diagnostic is
in `scripts/diag_d670_arm_windows.py` → [`data/diag_d670_arm_windows.json`](../../data/diag_d670_arm_windows.json).
In sample only; the vault (from 2025-03-01) was not read. **Dealer gamma (GEX) data: SqueezeMetrics**, used under the
principal's written permission of 2026-09-28; no per-date value is published.*

*The runner was run twice. **The first run had a bug in P2's two trailing features.** A 20-session rolling window
counted early-close holidays, which have no 15:59 bar, so each holiday blanked the next 20 sessions and only about half
of each root's sessions had features. The second run restores the declared definition, the prior 20 complete sessions.
P1 and P3 do not read these features, and their log lines are identical across the two runs. No gate can change:
Gate 2 is evaluated only on roots that pass Gate 1, and none did. The first run's β_disc values, on about 840
forecasts a root, were YM −0.72 (t −1.86), RTY −0.52 (t −1.49), ES −0.19 (t −0.59) and NQ +0.22 (t +0.80). They are
superseded, recorded here, and change no conclusion.*

## The answer in one line

**NOT SUPPORTED on both evidence roots.**
- **YM loses before cost:** −4.45 bp a trade, t −2.76, at the 0.5th percentile of its own null. The direction
  reverses there.
- **RTY is flat:** −0.18 bp, t −0.07.
- **The development roots are no better:** ES −0.59 bp, and **NQ +1.26 bp (t 0.57), below its own null's median.**
- **Nothing known at 10:00 forecasts the trade's profit:** β_disc t is between −0.89 and +0.58 on all four roots.

**The mechanism as D669 stated it does not stand on its own.** A post-hoc split of the arm's own sessions (§6) shows
why:
- **most of the arm's gross comes from the 23 % of sessions where it enters after 10:00**: $12,281, t 3.69, hit 61 %;
- the sessions where it enters at 10:00 earn $9,830, t 1.40.

## 1. The rule and its samples

**The rule:** D = sign(C₀₉:₅₉ − the prior C₁₅:₅₉); enter at the 10:00 open; exit at the 15:59 close.

**The micro costs** (`d508_exec`): MES $4.42, MNQ $4.07, MYM $3.80, M2K $3.76 a round trip.

**Sessions dropped as declared** (the runner checked that the "missing" drops are almost all exchange early-close
holidays and the session after each, not thin minutes: one session per root lacked a 09:59 or 10:00 bar):

| root | in window | roll | circuit | missing | used | trades | σ (bp) | MDE (bp), printed before any mean |
|---|---|---|---|---|---|---|---|---|
| YM | 2,362 | 36 | 3 | 144 | 2,179 | 2,166 | 74.0 | 4.45 |
| RTY | 1,971 | 31 | 2 | 119 | 1,819 | 1,817 | 105.5 | 6.94 |
| ES | 2,362 | 36 | 2 | 140 | 2,184 | 2,162 | 79.3 | 4.78 |
| NQ | 2,362 | 36 | 2 | 140 | 2,184 | 2,180 | 98.9 | 5.93 |

## 2. P1 — the direction (Gate 1)

| root | gross mean (t) | net mean | N1-week p50 / p95 (SE) | percentile | ex Feb–Apr 2020 | gap alone | first half hour alone | C0, long always | long / short gross |
|---|---|---|---|---|---|---|---|---|---|
| **YM** | **−4.45 (−2.76)** | −7.23 | −0.74 / +1.65 (0.03) | 0.5 | −5.25 | −2.14 | −1.77 | +1.26 | −2.95 / −6.22 |
| **RTY** | **−0.18 (−0.07)** | −4.44 | −0.57 / +3.23 (0.05) | 57.1 | −1.38 | −0.04 | +2.66 | −1.38 | −1.45 / +1.31 |
| ES (dev) | −0.59 (−0.35) | −3.32 | −0.09 / +2.44 (0.03) | 37.1 | −1.33 | −0.06 | +0.31 | +1.84 | +1.13 / −2.71 |
| NQ (dev) | +1.26 (+0.57) | −1.06 | +1.65 / +4.95 (0.04) | 42.1 | −0.14 | +1.87 | +3.62 | +2.11 | +3.06 / −0.95 |

**Gate 1 fails on YM and RTY.** The Holm one-sided p-values are 0.997 and 0.528, and both roots sit below their N1
p95 by far more than 2 SE. N1-month tells the same story on every root.

**No root carries the direction:**
- **Each half alone does at least as well as the full direction on every root**, and the first half hour alone does
  better on all four. Both halves are inside noise.
- **Always long in the same windows (C0) beats the rule on YM, ES and NQ.**
- **On NQ the rule sits below N1-week's median:** random directions with the same weekly long share earn more (+1.65).

**By year:**

| year | NQ | YM | RTY | ES |
|---|---|---|---|---|
| 2016 | −5.93 | −4.88 | | −0.39 |
| 2017 | −0.21 | −1.05 | +4.46 | −1.70 |
| 2018 | +1.05 | −4.32 | +1.68 | −1.09 |
| 2019 | −0.84 | −2.59 | +0.50 | −0.56 |
| 2020 | **+18.40** | +1.28 | +5.50 | +8.10 |
| 2021 | +1.39 | −1.47 | +2.34 | +4.47 |
| 2022 | +2.33 | **−13.43** | **−13.65** | −5.64 |
| 2023 | −3.58 | −6.95 | +1.51 | −3.19 |
| 2024 | −1.18 | −4.64 | +1.81 | −3.79 |
| 2025 (to Feb) | +0.87 | −16.59 | −20.16 | −10.80 |

- **NQ's rule is 2020.** The best trades on every root are March 2020 longs: NQ 2020-03-17, +674 bp.
- YM has no profitable year in net dollars. Neither does RTY.

**The four groups, per book (unfiltered rule, gross against net, per trade):**

| root | Sharpe gross / net (per-trade, annualised) | Sortino gross / net | median gross | win | payoff | skew | kurtosis | ex-top / ex-bottom / trimmed mean | maxDD at one micro |
|---|---|---|---|---|---|---|---|---|---|
| YM | −0.93 / −1.50 | −1.22 / −1.94 | −2.05 | 48 % | 0.91 | −0.34 | 11.6 | −7.32 / −1.48 / −4.36 | $24,018 |
| RTY | −0.03 / −0.65 | −0.04 / −0.87 | +3.93 | 52 % | 0.93 | −0.07 | 7.4 | −3.79 / +3.72 / +0.11 | $8,927 |
| ES | −0.11 / −0.64 | −0.16 / −0.86 | 0.00 | 50 % | 0.97 | −0.30 | 10.5 | −3.59 / +2.51 / −0.49 | $15,403 |
| NQ | +0.20 / −0.17 | +0.28 / −0.23 | +1.01 | 51 % | 1.01 | 0.03 | 7.0 | −2.33 / +4.73 / +1.13 | $11,335 |

**Breakeven per side** is below zero on YM, RTY and ES, and +0.63 bp on NQ. The gross is 0.54 × cost on NQ.

**RTY's mean sits below its median** (−0.18 against +3.93): the left tail does the work there.

## 3. P2 — can the profit be forecast at 10:00? (Gate 2 not reached)

**P2a, the prize.** The oracles keep the top two-fifths of sessions by realised |move| or by efficiency. **On three of
the four roots the rule loses even on those days:**

| root | top 40 % by \|move\| | top 40 % by efficiency |
|---|---|---|
| YM | −10.67 | −9.17 |
| RTY | −2.33 | −1.03 |
| ES | −0.53 | −0.28 |
| NQ | +3.46 | +4.93 |

**The trend days that carried the arm do not carry this direction.** A filter would need a rank correlation of about
0.1–0.2 with the trade's own profit to clear cost: 0.1 gives +1.8 to +9.7 bp gross kept, depending on the root.

**P2b, the walk-forward forecast** (after the correction):

| root | forecasts | β_disc (t) | N2 p95 of t | filter passes | π̂ final | ρ(ŷ, \|move\|) | ρ(ŷ, efficiency) |
|---|---|---|---|---|---|---|---|
| YM | 1,916 | −0.25 (−0.89) | +1.39 | 3 | −0.03 | 0.04 | 0.05 |
| RTY | 1,549 | −0.16 (−0.40) | +1.53 | 9 | −0.16 | 0.21 | −0.05 |
| ES | 1,912 | +0.06 (+0.26) | +1.18 | 14 | +0.05 | 0.10 | 0.04 |
| NQ | 1,930 | +0.15 (+0.58) | +1.43 | 170 | +0.17 | 0.09 | 0.05 |

- **No root discriminates.** The pass-through is near zero or negative, so the filter trades almost nothing: 3 to 170
  sessions.
- **The forecast sees a little size on RTY (0.21) and no trend on any root.** That repeats D647's finding (trend days
  are invisible before the open) with the first half hour added.

## 4. P3 — the 15:00 exit (Gate 3)

| root | exits at 15:00 | paired difference, bp (t) | secondary: under water at 15:00 (t) |
|---|---|---|---|
| **YM** | 1,069 | **+1.50 (+2.78)** | +1.59 (+3.08) |
| RTY | 868 | +0.92 (+1.19) | +1.33 (+1.69) |
| ES | 1,033 | +0.92 (+1.68) | +1.08 (+1.73) |
| NQ | 1,048 | +0.23 (+0.36) | +1.08 (+1.49) |

- **Gate 3 passes on YM and fails on RTY.**
- **Cutting a position whose last hour went against it helps on every root,** consistent with D581 and D640's finding
  that the close continues its prior hour.
- It helps a rule that loses, so under the declared routing it decides nothing now. It is the one measured ingredient
  here that holds out of NQ.

## 5. Component line

| root | daily net Sharpe (gross) at one micro | net Sortino | hit | skew | ρ K8 | ρ MACD arm | ρ with the other roots |
|---|---|---|---|---|---|---|---|
| YM | −1.64 (−1.07) | −2.08 | 45.1 % | −0.41 | 0.09 | 0.19 | ES 0.65, NQ 0.35, RTY 0.46 |
| RTY | −0.76 (−0.13) | −1.00 | 49.6 % | −0.44 | 0.05 | 0.24 | ES 0.54, NQ 0.38, YM 0.46 |
| ES | −0.73 (−0.24) | −0.95 | 48.0 % | −0.53 | 0.03 | 0.35 | NQ 0.61, YM 0.65, RTY 0.54 |
| NQ | −0.11 (+0.16) | −0.16 | 48.9 % | −0.22 | −0.03 | 0.37 | ES 0.61, YM 0.35, RTY 0.38 |

The other session's plain-break book is missing (unmerged). No construction here is a component.

## 6. Post hoc, disclosed: where the arm's money is

D669 found that the sign since the prior close, **measured at each trade's own entry**, earns 92 % of the arm's gross on
its windows. This record fixed the measurement at 10:00, and the rule went flat. So the diagnostic splits the plain
10:00 rule, and the arm's own gross, by what the arm did each day. It runs on D669's hourly fixture, NQ 2016–2023
(spent data, nothing new read), in gross dollars at one MNQ.

| sessions | count | mean | total | t | hit |
|---|---|---|---|---|---|
| plain 10:00 rule, all sessions | 1,820 | $3.15 | $5,725 | 0.61 | 50.7 % |
| plain rule where the arm enters at 10:00 | 1,269 | $5.46 | $6,926 | 0.93 | 50.2 % |
| plain rule where the arm enters later or not at all | 551 | −$2.18 | −$1,201 | −0.21 | 51.7 % |
| plain rule where the arm makes no trade | 115 | **−$68.80** | −$7,912 | **−3.19** | 34.8 % |
| **the arm's own gross, 10:00-entry sessions** | 1,270 | $7.74 | $9,830 | 1.40 | 49.4 % |
| **the arm's own gross, later-entry sessions** | 438 | **$28.04** | **$12,281** | **3.69** | **60.7 %** |

**The 10:00 entries, two-thirds of the arm's sessions, are close to noise.**

**The later entries carry more than half the arm's gross.** Those are sessions where the two MACDs disagree at 10:00
and come into agreement later in the day, after the day's own move has formed. **On them the arm's hit rate is
61 %.** So "the sign since the prior close at the moment of entry" was, for these trades, **the direction of the day
so far**, taken once both indicators confirmed it.

**The arm also avoids the days the plain rule loses worst.** The 115 sessions with no trade cost the plain rule $69 a
session, with a 35 % hit rate. The arm knows those days only by watching them unfold.

**Correction to D669 §10 and FINDINGS §89:** the arm does not earn by carrying the 10:00 direction. On this split, it
earns by joining a move once it has formed after 10:00, and by staying out of days that never form one. This is post
hoc on the spent in-sample slice. It names where to look and supports nothing.

## 7. The predictions

| | prediction | outcome |
|---|---|---|
| 1 | NQ ≥ 4 bp gross and clears N1-week | **FAILED**: +1.26, below N1's median |
| 2 | YM fails Gate 1 | held: −4.45 bp, t −2.76 |
| 3 | at most one evidence root passes Gate 1 | held: none |
| 4 | the full direction beats both halves on ≥ 3 of 4 roots | **FAILED**: 0 of 4 |
| 5 | β_disc t < 2 on both evidence roots | held |
| 6 | P3 positive on NQ, t < 2 on both evidence roots | **FAILED**: YM t 2.78 |
| 7 | long gross > short gross on every root | **FAILED**: RTY's short side is better |

Three of seven held.

## 8. What this decides

**The reshaped rule is NOT SUPPORTED on YM and RTY.** By the declared routing, **D669's mechanism as stated ("carry the
move since yesterday's close") is recorded as not transferring.** It does not stand as a plain rule even on NQ.

**On the principal's overfitting concern:** the reading is stronger than D669's.
- The arm's 10:00 trades are noise.
- Its gross sits in a quarter of sessions whose entries depend on when two tuned indicators come to agree: the
  impulse length and the minimum hold that D669 found to be a spike.
- **What remains is a plausible idea** (join the day's move once it has formed, and stay out when it never forms) **that
  has not been tested anywhere it was not found.**

**Withdrawn:** D669 §10's second proposal, a component built on the 10:00 direction.

**Proposals, each the principal's (R15):**
1. **Record D669's mechanism as corrected here, and the arm's 10:00 entries as noise,** in the qualification note
   D669 proposed for `BOOK_PROP.md`.
2. **Test "join the formed move after 10:00, flat on days that never form one" on YM, RTY and ES,** with its own
   pre-registration and a parameter-free confirmation rule, or close the line.
   - The idea came from spent NQ data. Its design must not be tuned on NQ.
   - It overlaps the other session's plain-break design, which also enters once a move has formed.
3. **The 15:00 last-hour cut** helped on all four roots (YM t 2.78). It is a candidate ingredient for any intraday
   book's exit, to be pre-registered where it is used.

**Disclosed, not claimed:** fading the 10:00 direction on YM would have earned +4.45 bp gross against a 2.8 bp cost.
It is found here, on YM's in-sample, and has no mechanism of its own beyond D487's reversal of the opening into the
close.

## 9. CLOSED by the principal, 2026-09-29

"Close and merge then remove the worktree." **The reshaping line is closed under R15, together with D673.** The 10:00
direction held to the close carries on no root. D673's pre-registered follow-up (join the formed move after 10:00) did
not carry either. The correction to D669's mechanism stands as recorded here and in D674's amendment of the arm. The
15:00 last-hour cut remains a candidate exit for a future pre-registration; the YM fade stays disclosed and unclaimed.
