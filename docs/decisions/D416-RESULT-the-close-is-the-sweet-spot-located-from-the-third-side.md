# D416 RESULT — the touch-day close is the sweet spot, located from the third side; five of five predictions held

**FAILS THE BAR on T1 and T2; T3 passes, as predicted.** Pre-registration `41c4ef0` predates the
runner and this file (R8). **The ledger does not move. Nothing was admitted. No holdout was read.**
D413's 180,050 resolved touches and 26,024 cell-2 events reproduce exactly (P2) — the events are
D413's, read a fourth time.

Cost: four seconds.

---

## 1. Stage 0

```
S1 up-day        stalls 99.9%   lag p10/50/90 1/1/4 days   at t+1: 50.0%   k=1
S2 higher close  stalls 99.9%   lag           1/1/4        at t+1: 50.5%   k=1
S3 ROC turn      stalls 96.1%   lag           1/3/7        at t+1: 15.1%   k=3
```

X-a held: an up-day comes within ten days on 99.9% of events, and on **half of them it is the very
next day**. Stall rates inside cell 2 match outside (99.9% / 99.9%), so the selection trap does not
show in the rate; it shows in what the 0.1% that never stall are worth (§3c).

---

## 2. The bar — S1 pooled

```
                                                    n       mean       ±     SE
S1 stall entry (five-day hold from the stall day)   179,384   +3.92 bp  1.46   +2.7
touch-day close, SAME events (D413's entry)         179,384  +14.45     1.48   +9.8
PAIRED  stall − close                               179,384  -10.53     1.27   -8.3    T1 FAIL
clock at t+1, SAME events                           179,370  +13.53     1.46   +9.3
PAIRED  stall − clock                               179,370   -9.64     0.89  -10.9    T2 FAIL
baseline on the 253 events that NEVER stalled           253 -539.93    41.59  -13.0
dropped − kept                                               -554.38    41.61  -13.3    T3 PASS
```

| | condition | outcome |
|---|---|---|
| **G1** | S1 stalls ≥ 30% | PASS — 99.9% |
| **T1** | stall entry beats the touch-day close | **FAIL — 10.5 bp worse, −8.3 SE** |
| **T2** | stall entry beats the clock | **FAIL — 9.6 bp worse than waiting one day regardless, −10.9 SE** |
| **T3** | the dropped trades are not better than the kept | **PASS — they are 554 bp worse** |

**D416 FAILS.** Waiting for the momentum to stall costs 10.5 bp against D413's entry, pooled, and
**almost all of that is the stall itself, not the wait**: the unconditional one-day delay costs
0.9 bp (+14.45 → +13.53) and the stall condition costs the other 9.6.

---

## 3. The three findings, one per gate — and each replicates D415 at daily resolution

### 3a. T1 — later is worse

The pre-registration's §5 computed this from ADDENDUM 3's marginals before the run: a five-day
hold entered one day after the touch-day close should capture ~21 bp in cell 2 against 30 from
the close. **The clock at `t+1` in cell 2 came in at +22.24.** The arithmetic held to a basis
point, and it is the reason X-e was stated with confidence.

### 3b. T2 — THE CANDLE IS WORSE THAN THE CLOCK, AGAIN

D415 found the first 15-minute up-bar was 3 bp worse than an unconditional two-bar wait. **The
first daily up-day is 9.6 bp worse than an unconditional one-day wait, at −10.9 SE** — the same
finding, one time scale up, three times the size. The mechanism is the same and it is
definitional: **an up-day's close is higher than the day before's, so the confirmation is a worse
price — and the up-move you waited to see is part of the five-day edge you came for.** You pay
twice: once in price, once in the bar consumed.

S3 — the three-day ROC crossing zero, the "momentum indicator" in the ordinary sense — says it at
full volume: **44.9 bp worse than the close pooled (−27.3 SE), 79.2 bp worse in cell 2 (−17.9 SE),
and 37.7 bp worse than its own three-day clock (−33.0 SE).** A smoother indicator stalls later and
pays more for the pattern.

### 3c. T3 — THE FILTER IS GOOD, AND IT IS THE OPPOSITE OF D415, EXACTLY AS PREDICTED

X-d predicted T3 would pass because *an event that never stalls in ten days is a zone that broke*.
The 253 events with no up-day in ten sessions returned **−539.93 bp** under D413's entry, median
−412, positive on **3.6%**. S2's 183 never-stalled events: **−669 bp, positive on 0.0%.**

**So the stall is a very good filter and a bad timer — the mirror of D415, where the confirmation
was a bad timer that also dropped the winners.** The difference is the time scale: at 15 minutes
the events that never confirm are the late-session touches that pay; at daily resolution they are
the zones that failed outright. **Neither is usable as a filter at the time of entry**, because
whether an event will stall is not knowable at `t` — and at 0.1% of events, S1's filter is worth
0.4 bp per trade to the strategy that could not use it anyway.

---

## 4. Does the stall ever help — the early and late stalls, separated

**Read the caveat before the table. The stall lag is a property of the holding period itself:**
lag 1 means the day after the touch was an up-day, lag 6+ means the first five days were all
down. **A baseline stratified by it is conditioned on the future.** What follows explains *why* the
average is −10.5; it does not offer a way to improve it, because the lag is not knowable at `t`.
This is an accounting, in the sense ADDENDUM 3 used when it said *you cannot trade the gap.*

S1, `L = 10`, paired on the same events, in bp:

```
                share      stall − close     stall − clock     baseline (D413's entry)
lag 1           50.0%        -156.09            0.00 *            +161.66
lag 2           24.8%          -9.59         -160.39                +8.00
lag 3–5         22.1%        +224.35          +65.37              -215.64
lag 6–10         3.1%        +669.54         +514.38              -683.27

cell 2
lag 1           50.2%        -163.14            0.00 *            +173.97
lag 2           25.3%         -40.11         -176.17               +34.61
lag 3–5         21.4%        +202.53          +45.11              -203.46
lag 6–10         3.1%        +703.74         +544.39              -700.70
```

*`k = 1`, so at lag 1 the clock **is** the stall day: identical entries, zero variance, no SE.*

**The paired delta is a mixture of two things that nearly cancel:**

- **Half the events stall the very next day, and on those the stall entry misses the bounce** —
  −156 bp against the close, because the up-day it waited to see *was* the bounce. The baseline
  made +162 on exactly these, which is the same number seen from the other side.
- **A quarter stall on day 3 or later, and on those the stall entry sidesteps a collapse** — +224
  and +670 against the close, because the close entry sat through three to ten down-days first.

**Net: −10.5 bp.** The stall rule is a bet that sidestepping the late collapses is worth more than
missing the early bounces. It is not, by 10.5 bp pooled and 27 in cell 2 — because the next-day
bounces (50%) are twice as common as the day-3-or-later collapses (25%), and the close entry
captures the bounces in full.

**And the lag-2 row is D415's finding in one number:** on events where day 1 was down and day 2 was
up, entering at `t+1` (after the down day, before the up day) beats entering at the stall by
**160 bp** — the entire size of the up-day paid for the privilege of having seen it.

---

## 5. The cell-2 secondary

```
                                          n      mean       ±     SE
S1 stall entry                        25,967   +3.92 bp  3.66   +1.1
touch-day close, same events          25,967  +31.18     3.74   +8.3
PAIRED  stall − close                 25,967  -27.26     3.30   -8.3     X-e: predicted < −10
clock at t+1, same events             25,965  +22.24     3.77   +5.9     pre-reg §5: predicted ~+21
PAIRED  stall − clock                 25,965  -18.29     2.38   -7.7
dropped − kept (38 events)                    -449.52   58.38   -7.7
```

**The stall entry in cell 2 makes +3.92 bp — the whole +30 bp edge is gone**, and the cell's
secondary bar fails T1 and T2 by 8 SE each. X-e said "worse than the close by more than 10 bp"; it
is worse by 27.

---

## 6. Shape: the `L` sweep on S1, and it says something

```
L= 5   stalls 96.8%   PAIRED stall − close   pooled -32.01 (-26.1 SE)   cell 2 -50.26 (-16.0 SE)
L=10   stalls 99.9%                          pooled -10.53 ( -8.3 SE)   cell 2 -27.26 ( -8.3 SE)
L=20   stalls 100.0%                         pooled  -9.89 ( -7.8 SE)   cell 2 -26.87 ( -8.1 SE)
```

The paired delta is **three times worse at `L = 5` than at `L = 10`**, on 97% of the same events.
That is not the window — it is composition: **events that stall on days 6–10 are ones where price
kept falling for a week after the touch, so D413's close entry was a disaster and the late stall
entry rescues it.** Including them pulls the paired mean toward zero. §4 separates the two.

---

## 7. Predictions — five of five

| | prediction | outcome |
|---|---|---|
| X-a | S1 stalls > 85%, median lag 1–2 | correct — 99.9%, lag 1 |
| X-b | pooled T1 fails | correct — −8.3 SE |
| X-c | T2 fails — the candle loses to the clock | correct — −10.9 SE |
| X-d | **T3 passes** — the dropped trades are the zones that broke, the opposite of D415 | correct — −554 bp at −13.3 SE |
| X-e | cell-2 stall entry worse than the close by > 10 bp | correct — −27.26, and the clock landed at +22.24 against a computed ~+21 |

**Every prediction held, and the one that mattered was computed from a record that already existed
rather than guessed.** That is the standard the pre-registration set for itself and it is the first
study in this line to meet it in full.

---

## 8. What three execution studies have located

| | entry | cell 2, against the touch-day close |
|---|---|---|
| D414 | first 15-minute touch | **−35 bp** (−4.9 SE) |
| D414 | first touch, limit at the edge | −37 |
| D415 | first 15m up-bar / higher low / re-cross | −32 / −30 / −46 |
| D415 | two 15m bars later, unconditional | −27 |
| **D413** | **the touch-day close** | **0, by definition — +30.26 gross** |
| D416 | one day later, unconditional | −9 (+22.24 vs +31.18) |
| D416 | first daily up-day | **−27** |
| D416 | first daily higher close | −30 |
| D416 | three-day ROC turn | −79 |

**Before the close, the intraday continuation is still running. After it, the multi-day bounce is
front-loaded and every day of delay forfeits it. Every confirmation pattern, at either time scale,
is a worse price than the clock it waits through.** The touch-day close is the one entry that sits
between the two — and it was D413's, declared before any of this was measured.

**What that means for a plan** is plain and it is not an optimisation: *enter at the close of the
day the zone is first touched.* The execution question on this construction is answered, and the
answer is that there was nothing to gain from execution. What remains is the question execution
cannot touch — **whether the signal survives out of sample** — and that is `holdout2`, unspent.

**Disposition is the principal's.**

---

## 9. R13

Sixteenth look by object; third on execution; no new data spent.

**Evidence:** `data/d416_momentum_stall.json`. Runner `scripts/run_d416_momentum_stall.py`,
reading D413's events from D413's runner and D412's window machinery rather than restating either.
