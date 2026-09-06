# D363 RESULT — the entry-day spread is a fifth narrower at the median and no narrower at the mean; charging each trade its own spread raises the cost a fifth over the ledger median; and the cost question is execution, not estimation

**Status:** RESULT. Pre-registered at `44292b4`, runner at `a7b3251` — both before this file
existed (R8). The ledger is D362's two-sink arm, unchanged and reproduced to 1e-9; every
cost line is the record's own Corwin–Schultz estimator on OHLC. **No holdout data was read**
(the file-open audit refused the probe). D336's quoted spreads are on hold and nothing here
pre-empts them.
**Date:** 2026-09-06
**Area:** Cost model · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is a book. Nothing is promoted. Cost decides nothing about the signal (R15); this record says what the cost is and where it can move.**

---

## 1. The verdict

**Two of eight, and the estimator does not move the cost.** The Corwin–Schultz half-spread
measured on the three bars around the entry — the day before the gap, the gap day and the
entry day — is **34.6 bp a side at the median against 42.9 for the trailing month** (19.5%
lower; Q1 asked for 25%), and **52.4 against 51.7 at the mean**: spreads compress at the
median on top-decile volume days and do not compress in the wide tail, which is where this
ledger's cost and its gross both live. The round trip is 105 bp under the entry-window line
against 108 under PUB. Nothing in the estimator's timing changes the answer.

| per-trade cost line, bp | entry ½-spread median | exit median | mean 2c | mean net | net t | share of trades net > 0 |
|---|--:|--:|--:|--:|--:|--:|
| PUB, trailing 21-bar mean | 42.9 | 42.9 | 107.7 | −48.7 | −2.5 | 46% |
| PB, the per-bar convention | 17.9 | 17.9 | 125.1 | −66.1 | −3.4 | 45% |
| **EW, three bars around entry / exit** | 34.6 | 36.0 | 105.1 | −46.1 | −2.4 | 47% |
| EW1, the estimator's own pair | 29.5 | 8.0 | 124.3 | −65.3 | −3.4 | 46% |

**And the convention matters more than the estimator.** Every per-trade net in the record
since D285 charges the ledger's *median* half-spread to every trade. Charging each trade its
own name's spread at its own entry and exit bars — the per-trade convention this record
uses in every table — gives a mean round trip of **107.7 under PUB against D362's 88.8**, and
under PB **125.1 against 38.7**: PB's single-pair estimate is zero on 43% of bars and has a fat
right tail, so its median is small and its mean is the largest of the four. The net moves from
D362's −30 / +20 (PUB / PB, median convention) to **−49 / −66**. On a ledger whose gross sits
in its widest names, the median convention understates the charge by a fifth under PUB and
by three times under PB. STACK §7 item 33 and FINDINGS §43 rule 1.

## 2. The execution bounds

| mean net per trade, bp | full crossing | half crossing | auction (no spread) |
|---|--:|--:|--:|
| PUB | −48.7 | +3.0 | +54.7 |
| PB | −66.1 | −5.7 | +54.7 |
| EW | −46.1 | +4.3 | +54.7 |

The fade nets **−46 to −66 if both sides cross the spread, about zero if one side does, and
+55 if neither does.** The kernel's fills are the opening print and the closing print, which
are auction prints; an order in the auction pays impact, not the spread. **Impact is not
modelled here**; what the record can say is that liquidity is not the constraint: at $25k a
position the trade is **0.04% of the entry day's dollar volume at the median and 0.21% at
the 90th percentile**, under 1% on 99.8% of trades, and under 1% on 99.3% at the exit bar
(Q4 confirmed). At $50k it is under 1% on 98%. A 100 bp swing rests on how the order is
placed, and daily bars cannot see that. This is the cost question, and it is not an
estimator's.

## 3. By spread quintile, per-trade convention

| PUB quintile at entry | n | ½-spread PUB / EW in | price | gross | net PUB | net EW | net PB |
|---|--:|--:|--:|--:|--:|--:|--:|
| tightest, 2 to 26 | 616 | 20 / 17 | $53 | +43 | **+0.4** | −11 | −30 |
| 26 to 37 | 616 | 32 / 26 | $41 | +17 | −53 | −60 | −85 |
| 37 to 50 | 616 | 43 / 36 | $36 | −3 | −96 | −98 | −126 |
| 50 to 72 | 616 | 59 / 48 | $30 | +27 | −101 | −97 | −108 |
| **widest, 72 to 316** | 615 | 94 / 78 | $20 | **+225** | **+6** | **+36** | +18 |

The middle three quintiles, 1,848 trades, are +13 gross and −83 to −106 net under every line
(Q5's "against" held in the record's favour). The widest quintile is the only one that pays
at full crossing, by 6 bp under PUB and 36 under the entry-window line, on names at $20 with
a 94 bp half-spread. Under the per-trade convention the tightest quintile is at breakeven
rather than D362's median-based +17 under PB.

## 4. Sizing

| per unit of capital | gross | t | net PUB | net PB | net EW | deployed net PUB, 4 crossings |
|---|--:|--:|--:|--:|--:|--:|
| equal | +61.7 | 3.2 | −48.7 | −66.1 | −46.1 | −10.5 |
| INV, ∝ 1 / cost | +29.7 | 1.8 | −47.3 | −71.6 | −51.8 | −12.1 |
| U, middle quintiles halved | +82.4 | 3.7 | −33.9 | −48.9 | −29.4 | −9.1 |

**Inverse-cost sizing gives the gross away** (Q6 held under PB and not under PUB, where the
lower cost offsets the lower gross by 1 bp): capital follows cheapness and the edge is not
cheap. **The U shape is above its within-name permutation null** — net PUB −33.9 against a
p95 of −35.6 at 200 draws, p50 −44.6 (Q7) — by 1.7 bp, and it is still negative under every
line at full crossing. It is the in-sample shape re-found in the sample it came from, and it
does not rescue the net.

## 5. Predictions

| | | |
|---|---|---|
| **Q1** *(load-bearing)* | **FALSIFIED** | 34.6 against 42.9, ratio 0.805 |
| Q2 | FALSIFIED | −46.1 under EW |
| Q3 | FALSIFIED | exit EW 36.0, 16% below PUB — the exit window compresses too |
| Q4 | CONFIRMED | 99.8% under 1% at $25k |
| Q5 *(against)* | FALSIFIED — the "against" held | middle three −85 under EW |
| Q6 | FALSIFIED on one clause | INV lower under PB (−71.6 vs −66.1), 1 bp higher under PUB |
| Q7 | CONFIRMED | U −33.9 against PERM p95 −35.6 |
| Q8 | FALSIFIED by 0.4 points | EW1 zero on 42.6% (yes); EW on 15.4% (not under 15%) |
| *check* | held | ledger == D362 to 1e-9, median 2c 88.77 / 38.70 == D362; the per-bar estimator's 21-bar mean == `HALF_PUB` to 6e-14 on 300 name-bars; `HALF_PB[t]` == the pair at t+1 to 0.0 |

## 6. Stop conditions, executed — and what the record does not decide

- **Q1 fails** → the trailing month is not far from the right estimate for these days at the
  mean; the entry-window line is the third line the record carries, and it changes the round
  trip by 3 bp.
- **The execution bounds are the remaining question.** The fade is a 100 bp question of
  order placement — crossing against the auction — and that is not answerable on daily
  bars. Two things could answer it: D336's quoted spreads for the level (on hold at the
  principal's instruction), and fills or intraday quotes on names like these for the
  auction's impact. Listed.
- **Q7 holds and does not matter**: U is above its permutation and negative under every
  line at full crossing; INV fails. Equal weight and D362's per-hit sizing stand.
- **The per-trade cost convention** is adopted from here for any per-trade net on a ledger
  whose gross is concentrated by spread; the ledger-median line is printed beside it for
  comparability with the record. Which convention the programme carries is the principal's
  call; the record carries both until then.
- Nothing is promoted. Book: empty.

## 7. Deviations and what the run found

- **The per-bar estimator's day.** The record's Corwin–Schultz stores each two-day pair at
  its first day; `HALF_PUB[t]` is the trailing mean of pairs ending at t−1 and `HALF_PB[t]` is
  the single pair (t, t+1) — **PB reads the entry day and the day after it**, which is why
  its per-trade mean is the largest line and why two trades with no day after the entry fall
  back to PUB (counted). The windows here are defined on the pair's second day and asserted
  against the raw bars.
- **PB's per-trade mean (125) against its ledger median (38.7)** is the single-pair
  estimator's zero clamp on 43% of bars and its right tail; PB was never meant to be a
  per-trade charge and the record has used it as one through the median. Stated, not fixed.
- **Q6 read as a conjunction**; INV's 1 bp under PUB is within the noise of a 19-trade cap.
- **The INV cap at 5** binds on 19 trades (uncapped maximum 11.5).
- **[C]** not run: no signal is tested here. No assertion weakened; an `isfinite(PB)` check
  that fired legitimately on the two no-day-after trades was replaced by the counted fallback
  and the change is in a code comment.

## 8. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** · **[HOLDOUT-GUARD]** | via the shared prep; 274 file opens audited, none containing "holdout", the probe refused |
| **[ID]** | the ledger == D362's A2 (3,079, +61.708338) and its median 2c to 1e-9; D362's base [ID] passed on the way |
| **[CS]** | the per-bar pair at its second day, 21-own-bar trailing mean ending at t−1 == `HALF_PUB` to 6e-14 on 300 name-bars, NaN pattern equal; `HALF_PB[t]` == the pair at t+1 to 0.0; the clamp reproduces D332's 43.2% zeros |
| **[EW]** · **[PART]** | 300 trades' four window values == an independent recomputation from 2,394 raw bars to 1e-14; participation == position / (raw close × raw volume) to 0.0 |
| **[W]** · **[PERM]** | unit weights == the kernel to 3e-18; every permutation keeps each name's weight multiset and is never the observed on the 456 permutable names |
| **[6]** | [ID] on +1 bp; [CS] on a window ending at t; [EW] on a gap-day high × 1.01; [PERM] on a doubled weight — all raise |

**Speed:** self-test 16 s; PERM 0.06 s a draw; report 15 s; peak working set 1.57 GB.

## 9. What this establishes

1. **The entry-day spread is not the lever.** A fifth narrower at the median, unchanged at
   the mean, 3 bp on the round trip.
2. **Charging each trade its own spread is the honest per-trade convention on a ledger
   whose gross is in its widest names**, and it costs this ledger a fifth more than the
   median it has been charged. The record carries both lines from here.
3. **The cost question is execution.** Full crossing −46 to −66; half +3; auction +55; the
   position is 0.04% of the day's volume. What the auction costs is the number the programme
   does not have.
4. **Cost-aware sizing does not rescue the net**; the U shape is real within its sample and
   still negative; inverse cost gives the edge away.

## 10. Files

`data/d363_perm_p0.json` · `data/d363_cost_lines.json` · `scripts/run_d363_cost_lines.py` ·
reuses `scripts/run_d362_sink_filter.py`, `scripts/run_d361_regime_gated_short.py`, the
record's Corwin–Schultz (`scripts/d285_spread_estimate.py` as `d348_prep` builds the half-spreads),
`scripts/d361_export_trades.py`, `scripts/d348_prep.py`, `scripts/d337_borrow.py`. The holdout
fixture was not read; D336 is not pre-empted.
