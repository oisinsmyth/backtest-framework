# D736 STAGE 0 RESULT — only the NQ compression break both earns and abstains; NQ F2 is break-even by the principal's standard; D735's equity legs earn but are in the market most days

*2026-10-01.*
- *Pre-registration: [D736](D736-STAGE-0-PRE-REG-which-es-nq-constructions-earn-when-they-trade.md) (6d29f06f).*
- *Runner: `scripts/stage0_d736_earn_when_trading_screen.py`, committed before its one run.*
- *Output: `data/stage0_d736_earn_when_trading_screen.json`.*
- *In-sample only. It read committed result JSONs and nothing else.*

## 0. The answer

**Under the principal's standard** (earn when it trades: positive without the two best years, positive in at least
two-thirds of years, and at least \$209 a year outside the two best years at one micro), the on-file constructions
that earn and **also abstain by design** come to one:

| construction | status | years positive | ex-2 a year | in the market | ex-2 per market session |
|---|---|---:|---:|---:|---:|
| **NQ compression C1** (D680) | queued, slot 9 | 6 / 6 | \$372 | **21 %** of sessions | \$6.90 |

**Two other constructions earn, but neither abstains:**
- **D735, NQ breaking from the market.** Its EQ, YM, ES and RTY legs earn. It is in the market on **71–91 %** of
  sessions. Its YM k1.0 cell is already frozen for the joint run as D737 (slot 1).
- **D727's NQ follow at k 1.0 and 1.5.** It earns on D732's 2018–23 window only, is in the market on **50–74 %** of
  sessions, and was declined by the principal.

**NQ F2 (D716, slot 7) reads BREAK-EVEN.** It is positive in 4 of 6 years, but outside 2020 and 2022 it makes **\$159 a
year** at one MNQ. By the principal's standard, that is a line that trades without earning. ES F2 and every other F2
variant read the same.

**The retired MACD arm makes \$17 a year outside its two best years,** with 3 of 6 years positive. The screen agrees
with its retirement.

**Nothing new is on the shortlist that the programme has not already queued or declined.**

## 1. Counts

| | n |
|---|---:|
| blocks screened | 174 |
| yearly sums reproduce the recorded total | 168 (6 have no recorded total: D721's) |
| UNREADABLE | 0 |
| **EARNS** | **15** |
| BREAK-EVEN | 12 |
| INTERMITTENT | 18 |
| RESTS ON ITS BEST YEARS | 129 (93 of them D727 per-clock cells) |

**Duplicates in the universe, disclosed** (they change no reading):
- D728's `S2_book/*/full_book` blocks are D727's NQ first-crossing books, number for number. D728 kept the full book
  beside its splits.
- D721's `M0` F2 books for ES, NQ and YM are D711's F2 lines.
- D711 A1 15:30 is ES F2, which is also D732 E.

**Families.** The pre-registration declared a family as **source and root**. The runner keyed it by source and
leg/series instead, which is a deviation, disclosed here. The three counts:

| definition | EARNS families |
|---|---:|
| as keyed by the runner | 7 |
| **as declared (source, root)** | **2** (D732-NQ: C, T1, T1.5; D735-NQ) |
| by construction | 3 (C1; D735's breaks; D727's follow) |

## 2. The EARNS table (all 15 blocks)

Notes on the columns:
- **Share** is days in the market over sessions.
- **\$/mkt** is ex-2 a year over (252 × share).
- **Sharpe and Sortino** are as recorded in each block's own record (net, daily, whole window). This screen computes no
  new performance number.

| block | window | total | ex-2 | ex-2 / yr | yrs + | best-2 share | share | \$/mkt | Sharpe (Sortino) | trades | status |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---|
| D732 C (NQ compression C1) **P** | 2018–23 | 4,954 | 1,488 | 372 | 6/6 | 0.70 | 0.214 | 6.90 | 0.91 (1.86) | 311 | QUEUED slot 9 |
| D732 T1.5 (NQ follow k1.5) | 2018–23 | 16,056 | 6,463 | 1,616 | 5/6 | 0.60 | 0.499 | 12.86 | 1.02 (1.47) | 725 | DECLINED |
| D732 T1 (NQ follow k1.0) | 2018–23 | 11,764 | 3,178 | 794 | 5/6 | 0.73 | 0.743 | 4.24 | 0.61 (0.86) | 1,081 | DECLINED |
| D735 EQ k1.5 1σ | 2016–23 | 20,485 | 8,565 | 1,428 | 6/8 | 0.58 | 0.734 | 7.71 | 0.97 (1.66) | 1,131 | DRIFT ONLY |
| D735 EQ k1.0 1σ | 2016–23 | 22,220 | 8,535 | 1,422 | 6/8 | 0.62 | 0.909 | 6.21 | 0.97 (1.63) | 1,400 | DRIFT ONLY |
| D735 EQ k1.0 none | 2016–23 | 22,022 | 8,333 | 1,389 | 6/8 | 0.62 | 0.909 | 6.06 | 0.89 (1.37) | 1,400 | DRIFT ONLY |
| D735 EQ k1.5 none | 2016–23 | 18,230 | 4,777 | 796 | 6/8 | 0.74 | 0.734 | 4.30 | 0.80 (1.24) | 1,131 | DRIFT ONLY |
| D735 YM k1.0 1σ | 2016–23 | 25,264 | 6,933 | 1,156 | **7/8** | 0.73 | 0.881 | 5.20 | 1.11 (1.85) | 1,699 | QUEUED slot 1 (D737) |
| D735 YM k1.5 1σ | 2016–23 | 20,428 | 6,153 | 1,026 | 6/8 | 0.70 | 0.716 | 5.68 | 0.98 (1.67) | 1,381 | DRIFT ONLY |
| D735 YM k1.0 none | 2016–23 | 22,649 | 5,468 | 911 | 7/8 | 0.76 | 0.881 | 4.10 | 0.92 (1.40) | 1,699 | DRIFT ONLY |
| D735 YM k1.5 none | 2016–23 | 15,740 | 2,077 | 346 | 6/8 | 0.87 | 0.716 | 1.92 | 0.69 (1.05) | 1,381 | DRIFT ONLY |
| D735 ES k1.0 1σ | 2016–23 | 21,106 | 4,741 | 790 | 6/8 | 0.78 | 0.885 | 3.54 | 0.92 (1.56) | 1,710 | DRIFT ONLY |
| D735 ES k1.0 none | 2016–23 | 19,291 | 3,486 | 581 | 6/8 | 0.82 | 0.885 | 2.61 | 0.78 (1.21) | 1,710 | DRIFT ONLY |
| D735 ES k1.5 none | 2016–23 | 15,194 | 3,450 | 575 | 6/8 | 0.77 | 0.712 | 3.21 | 0.69 (1.05) | 1,376 | DRIFT ONLY |
| D735 RTY k1.5 1σ | 2016–23 | 19,864 | 2,896 | 483 | 6/8 | 0.85 | 0.761 | 2.52 | 0.91 (1.59) | 1,180 | DRIFT ONLY |

**P** = the record's own pre-registered line. Every D735 cell above is **post hoc**: D735's primary, ES k1.5 1σ, reads
**INTERMITTENT** (5 of 8 years positive, ex-2 \$706 a year).

## 3. The other readings that bear on the programme

| block | label | ex-2 / yr | yrs + | share | what it means |
|---|---|---:|---:|---:|---|
| D732 F, **NQ F2 book B** (slot 7) | BREAK-EVEN | \$159 | 4/6 | 0.186 | outside 2020 and 2022 it does not pay one account fee a year |
| D732 E, ES F2 (= D711 A1 15:30, D721 ES M0) | BREAK-EVEN | \$136 | 5/6 | 0.173 | the same shape on ES |
| D711 A2 NQ (= D721 NQ M0), NQ F2 on its own 2018-04 window | BREAK-EVEN | \$168 | 5/6 | 0.19 | the same on F2's own window |
| D699 V1, ES gamma-gated MACD long (closed) | BREAK-EVEN | \$179 | **8/8** | ~0.29 | positive every year, but small |
| D732 A, the **MACD arm** (retired) | INTERMITTENT | **\$17** | 3/6 | 0.828 | agrees with the retirement |
| D727 NQ first crossing k1.5 (= T1.5 on 2016–23) | INTERMITTENT | \$999 | 5/8 | 0.528 | the follow fails G2 on its own longer window: **window-dependent** |

## 4. Predictions (D736 §4)

| # | prediction | outcome |
|---|---|---|
| 1 | NQ compression C1 reads EARNS | **Held** (6/6, \$372 a year ex-2) |
| 2 | NQ F2 and ES F2 read BREAK-EVEN | **Held** (\$159 and \$136 a year) |
| 3 | the MACD arm fails G2 | **Held** (3 of 6) |
| 4 | at least one D735 equity-leg cell EARNS; the TICK cells do not | **Held** (11 equity-leg cells; TICK reads INTERMITTENT or RESTS) |
| 5 | fewer than five families EARN | **Held as declared** (2 by source and root; 3 by construction). **It fails as the runner keyed families** (7); see §1 |

## 5. What this does and does not say

1. **The only on-file construction that meets the principal's standard and abstains by design is the compression break**
   (in the market 21 % of sessions, positive every year). It is already queued (slot 9).
2. **D735's breaks earn by the standard's money tests, but they do not abstain.**
   - They enter on most days, at 10:00–14:30.
   - Their earning cells are post hoc from 20, and the declared primary fails G2.
   - The principal has already sent the YM cell to the joint run (D737). This screen neither strengthens nor weakens that
     test; it read the same in-sample numbers.
3. **NQ F2 is queued (slot 7, and half of D734's book) and reads break-even outside its two best years.**
   - This is a statement about the in-sample record under the principal's standard. It is not a new test, and the frozen
     joint run will score F2 on its own pre-registered criteria regardless.
   - **For the principal to weigh:** under "trading without making money … is shit", F2's in-sample record is the
     MACD arm's problem at a smaller scale. F2 trades on 19 % of sessions, not 83 %, and is positive in 4 of 6 years,
     not 3.
   - Nothing is changed here. The joint run is frozen.
4. **D727's follow is window-dependent** (EARNS on 2018–23, INTERMITTENT on 2016–23), and the principal declined it.
5. **Not a test.**
   - Every figure was recorded in-sample before this screen. The gates were declared knowing several of them (D736 §0).
   - The shortlist is a robustness filter, not evidence. Every block's full report (net and gross, distribution, nulls)
     is in its own record; this screen recomputed none of it.

## 6. Next, only on the principal's word

**What it implies for new research:** design for selectivity. A construction should abstain on most sessions, the way
the compression break does, rather than mine D735's near-always-on family further. The NQ compression break's
mechanism diagnostic (what its tier selects) is the natural next step if the principal wants new selective designs.

Nothing here touches the joint run's frozen lines.
