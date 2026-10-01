# D733 STAGE 0 RESULT — DRIFT ONLY. The pullback entry adds nothing beyond the drift at the same moment (C2 rank 0.74, matched-row gain +$0.02); it enters later and higher than the plain follow and gives up $31.84 a trade to it; waiting for the turn costs $16.53 against the resting limit; the book is a 28%-win, tail-carried lottery (trimmed mean −$0.12). GO false. Both designers' priors were borne out

*2026-10-01. One run of `scripts/stage0_d733_pullback_entry.py` (0.6 min, with `--data-root` set to the main
checkout).*
- **The order:** the [pre-registration](D733-STAGE-0-PRE-REG-the-nq-pullback-entry.md), a merged design of this
  session's and a Fable 5.1 agent's, was committed first. The runner (`185e02de`) was committed before the run.
- **The audits:**
  - NQ's objects reproduce D727's known answer;
  - the lag audit (a second implementation from bars truncated at the entry minute) passed on 60 sampled trades a
    cell;
  - the canary (the entry bar's own close) fired;
  - C2's offset 0 reproduced the observed trades for cells (b) and (c) exactly;
  - the self-test also shows a gapped stop filling at the open and a voided day producing no trade.
- **The data:** 1,941 days, 1,707 of them armed. Nothing dated 2024-01-01 or later was read.
- **The output:** `data/stage0_d733_pullback_entry.json`.
- **The MACD arm, used in the ledger line below, was RETIRED by the principal on 2026-10-01** (aa894c80, after this
  record's pre-registration). Its ρ is reported as declared, as context only.

## 1. The six cells (one MNQ, $4.07; E1 = the stop or the 15:59 close)

| cell | trades | mean net (NW t) | C2 timing null p50 / p95; rank | Holm | gross (median) | net Sharpe (Sortino); gross | max DD | stopped | years + |
|---|---:|---|---|---:|---|---|---:|---:|---|
| r 0.25, (a) limit | 1,256 | **+$6.15** (+1.46) | +5.18 / +11.69; 0.59 | 1.0 | +$10.22 (−$22.11) | +0.53 (+1.04); +0.87 | $2,947 | 54% | 4/8 |
| **r 0.25, (b) 5-minute turn: PRIMARY** | 1,086 | **+$3.90** (+1.17) | +1.56 / +7.09; **0.74** | 1.0 | +$7.96 (−$20.00) | +0.38 (+0.87); +0.78 | $2,658 | **70%** | 4/8 |
| r 0.25, (c) bounce | 1,564 | −$0.38 | +1.29 / +5.53; 0.25 | 1.0 | +$3.69 | −0.05 | $5,594 | 85% | 3/8 |
| r 0.5, (a) | 1,481 | −$0.74 | +2.71 / +7.64; 0.12 | 1.0 | +$3.33 | −0.09 | $4,261 | 75% | 3/8 |
| r 0.5, (b) | 727 | +$0.18 | +0.98 / +8.31; 0.42 | 1.0 | +$4.24 | +0.02 | $3,325 | 70% | 4/8 |
| r 0.5, (c) | 1,094 | −$2.49 | +0.98 / +6.21; 0.15 | 1.0 | +$1.57 | −0.29 | $4,728 | 81% | 3/8 |

- **The family p95 (the maximum over the six cells) is +$11.92.** No cell clears even its own p95.
- **By |x| at entry, the primary cell clears its p95 in 0 of 4 bins.**
- **The primary cell's distribution:** win rate 28%, payoff 2.91, skew +2.82, kurtosis 16.1; median −$24.07.
- **The symmetric 1% trims:** ex-top −$2.29, ex-bottom +$6.10, both trimmed **−$0.12**. The mean is carried by the
  right tail.
- **The primary cell by year:** net 2016 −$546, 2017 −$279, 2018 +$1,619, 2019 −$1,028, 2020 −$1,283, 2021 +$1,553,
  2022 +$3,559, 2023 +$635. The largest year (2022) is 84% of the total.

## 2. The controls: what the entry does and does not add

| control | result |
|---|---|
| **C2, the timing null** (the same entry minutes and stop distances on other days, in their own direction) | the primary cell is at rank 0.74. **The pullback's timing is worth no more than entering at that minute on any armed day** |
| **The matched-row decomposition** (E1 from every armed 5-minute row, against the trigger rows, by clock hour and \|x\| bin) | **+$0.02** a trade. The trigger rows are indistinguishable from the rest |
| **C1, the same-day follow** from the arming minute to the close | the follow grosses **+$39.80** against the trade's +$7.96: **−$31.84 a day (t −6.78)**. Of that, −$31.63 is the entry price: the pullback entry is LATER and HIGHER than the arming price, because the move usually extends before retracing a quarter. The stop costs only −$0.21 |
| **C3, the turn against the limit** (r 0.25) | (b) − (a) = **−$16.53 (t −4.72)**. Waiting for the 5-minute turn costs money. TURN PAYS is false |
| **The mirror** (the same entry, against the trend) | −$5.84 net. The small edge that exists is directional |

## 3. The oracles

- **O1, the perfect-turn ceiling, is +$86.62 net a trade** (1,665 days). There is room: NO ROOM is false. A perfect
  fill at the pullback's eventual extreme would pay well.
- **O2:**
  - 70% of the primary cell's trades are stopped out (mean −$49.73);
  - the unstopped 30% average +$128.37;
  - a filter that knew which pullbacks hold would be worth a great deal, and nothing here finds it.
- **O3, the clock budget, is +$5.79 a trade.**
  - That is the drift D727 implies at the realised entry clocks; 57% of entries are at 10:00–10:59.
  - It is under $8: **the construction is paying for a late entry,** as the Fable agent warned.

## 4. Reported

- **Exits from the same entries** (net, win rate):
  - 1R −$3.11 (49%); 2R −$2.26 (35%);
  - a retest of the extreme −$4.77 (50%);
  - 60 minutes −$0.71;
  - **no stop, to the close: +$4.10**;
  - a stop wider by 0.1σ: +$4.38.
  - Targets make it worse; the stop is roughly neutral.
- **The MFE/MAE ladder is symmetric** (+$31 / −$33 at 15 minutes; +$116 / −$112 at the close). The entry does not
  put the price on a favourable side of the range.
- **The splits:**
  - pullback speed slow / mid / fast: +$7.49 / +$2.99 / +$1.21. Slow, quiet pullbacks do better, which agrees with
    the quiet-tape picture (D730/D731). This is post hoc, and inside chance;
  - up-trend days +$6.04 (554), down-trend days +$1.66 (532).
- **The multi-entry book** (≤ 3 a day; re-entry after a stop): 1,621 trades, +$2.94 a trade, daily net Sharpe +0.38.
- **The ledger line (the primary cell):** ρ +0.13 with the MACD arm (now retired), +0.04 with NQ F2.

## 5. Readings

- **NO ROOM: false.** O1 is +$86.62.
- **The primary cell: DRIFT ONLY.** The mean net is > 0, but it sits inside C2 and below C1.
- **TURN PAYS: false.**
- **GO: false.**

## 6. What it says

1. **On NQ, buying the pullback adds nothing to the drift it rides.** Its trades earn what any entry at the same
   minute in the trend's direction earns (C2, matched rows), and less than entering when the trend first appears
   (C1), because the move usually extends before it retraces.
2. **Waiting for confirmation costs money,** again (D477, D700). The turn underperforms the resting limit by $16.53 a
   trade.
3. **The book is a lottery:** 28% winners, payoff 2.9, the trimmed mean zero, one year most of the net. It is not the
   defined-risk, positive-expectancy entry a prop account needs.
4. **There is room,** O1 and O2 say: a pullback that holds pays $128 a trade. But nothing in price timing tells a
   holding pullback from a failing one.
5. **The independent designs agreed on the outcome in advance,** at a prior of about 20–25% for EDGE: drift only, the
   limit beats the turn, a late entry. They were right on every count.
6. **Proposed, not decided:** close the pullback entry (all six cells, any stop or exit variant) under R15, on the
   principal's word. The quiet-pullback split (slow > fast) is recorded as structure, unconfirmed.

## 7. CLOSED (2026-10-01, the principal: "Close D733")

**The pullback entry in an NQ trend is CLOSED under R15:** all six cells, any depth, trigger, stop or exit variant. It
was closed after D735 (NQ breaking from the market) beat its own timing null where this did not.

**A correction to §2–§3, from the two re-analyses written for D735** (this session's and a Fable 5.1 agent's). None
of them changes a reading.
- **C1's −$31.84 is mostly selection, not a cost of waiting.**
  - The follow's +$39.80 is measured on the trigger days, which are days that extended after arming.
  - An unconditional follow from a comparable arming grosses about $11 (D728's k 1.0 book).
  - So "later and higher" describes those days, not money an ex-ante alternative would have kept. The clean
    comparisons are C2 and the matched rows, both zero.
- **O1 (+$86.62) and O2's +$128 are hindsight quantities.**
  - The fill at a segment's eventual extreme and the survivors of a near barrier would read "room" on a random walk.
  - §3's "there is room" and §6's point 4 overstate what they show. A room oracle must be predictive; D735's O1 is.
- **The stop's 70% hit rate is about the random-walk rate.** At 0.22 σ_oc, a driftless walk hits it about 81% of
  the time. It was a noise barrier, not a level.
