# D414 RESULT — the pooled delta is nothing, and in the one cell that mattered the 15-minute touch is 35 bp too early

**FAILS THE BAR on T1 and T2.** Pre-registration `330ab58` predates the runner and this file (R8).
**The ledger does not move. Nothing was admitted. No holdout was read. 2024+ was not read.**

Cost: 30 seconds on fixtures already on disk, plus one mis-written assertion.

---

## 1. What was measured

3,077 D413 touches on the 32 fifteen-minute names, 2018-01-02 → 2023-12-31. Paired: the same
event entered at the daily close (D413's entry) and at the first 15m bar into the zone, exits held
fixed at `t + 5` so the exit cancels and **`delta = sign × (log C[t] − log P_entry)`** is the
entry alone, positive when the 15-minute entry was better.

```
[RESERVED]  every 15m bar past 2023-12-31 cut before scoring
[ALIGN]     32 names, worst median 0.00000, worst off-share 0.00%
[BASIS]     |phi[u]/phi[t] - 1|  p50 0.03%  p90 0.11%  p99 0.29%  max 3.28%  ->  2 dropped (0.06%)
[SAME-DAY]  daily touch with no 15m bar into the zone: 40 of 3,063 (1.31%)
paired events 3,023   cell 2 among them 900
```

**`[SAME-DAY]` at 1.31% is the number that says the basis is right.** Every daily touch but 40 was
found on the same day's 15m bars, and the 40 are the size of the 15:45–16:00 gap the fixture does
not cover (§6).

---

## 2. The bar

```
                                        n      mean       +-     SE    median    >0
MARKET  first-bar close vs daily close  3,023   -1.60 bp  4.00   -0.4   +0.00   47.6%
LIMIT   edge/open fill vs daily close   3,023   +5.05 bp  4.45   +1.1   +5.72   51.5%
LIMIT   + half-spread saved             3,023  +15.45 bp  4.48   +3.5  +13.37   55.2%
```

| | condition | outcome |
|---|---|---|
| **G1** | assertions hold, n ≥ 500 | **PASS** — 3,023 |
| **T1** | market delta > 0 by 2 paired SE | **FAIL** — −1.60 bp, −0.4 SE |
| **T2** | limit delta > 0 by 2 paired SE | **FAIL** — +5.05 bp, +1.1 SE |

**On the pooled events the 15-minute entry has no timing value at all.** The market arm is flat to
the basis point and the limit arm's +5 is inside its own noise. The only thing that clears is the
**neutral half-spread saved by resting at the edge — median 6.0 bp** — which is an execution gain
with no information in it, and it is the *optimistic* bound (a fill at the edge with no queue).

This is the outcome §7 called *"an execution gain, not a timing gain."* It is not, however, the
outcome that matters.

---

## 3. THE CELL-2 STRATUM REVERSES THE SIGN, AND IT IS THE ONLY NUMBER HERE THAT CHANGES A PLAN

```
MARKET  cell 2        n   900   mean  -35.08 bp  +-7.20   -4.9 SE   median -21.46   >0 41.0%
LIMIT   cell 2        n   900   mean  -36.60 bp  +-9.21   -4.0 SE   median -24.74   >0 41.9%
MARKET  not cell 2    n 2,123   mean  +12.59 bp  +-4.78   +2.6 SE   median  +2.60   >0 50.4%
```

**In cell 2 — the cell every addendum since D413 has been built on — entering at the first
15-minute touch is 35 bp WORSE than entering at the daily close, at 4.9 SE.** Outside cell 2 it is
12.6 bp *better*. The conditioning does not shift the execution delta; **it flips it.**

**Two artefacts were checked and both made it stronger**, computed from the committed event list:

```
cell 2, touch AT THE OPEN (bar 0)      -56.98 +-12.21   -4.7 SE   n 416
cell 2, touch INTRADAY (bar > 0)       -16.25 +- 8.22   -2.0 SE   n 484
not cell 2, at the open                +10.29 +- 7.57   +1.4 SE   n 850
not cell 2, intraday                   +14.12 +- 6.16   +2.3 SE   n 1,273

cell 2 by year   2018 -46.08 (-3.5)   2019 -31.83 (-1.9)   2020 -13.95 (-0.8)
                 2021  -9.87 (-0.4)   2022 -62.11 (-3.6)   2023 -41.33 (-3.1)
cell 2 by side   demand -40.98 (-4.7 SE)    supply -28.17 (-2.4 SE)
cell 2 trimmed 1% both tails   -34.75 bp   against raw -35.08
```

- **Not a gap-day artefact.** Gap-through touches carry more of it, but the intraday touches are
  also negative at −2.0 SE — and outside cell 2 *both* splits are positive. The reversal belongs to
  the cell, not to the open.
- **Not a 2020–2021 artefact.** Negative in all six years, and the pandemic-and-meme years are the
  *weakest* two. 2018, 2022 and 2023 are each beyond −3 SE.
- Both sides, and the symmetric trim moves it by a third of a basis point.

**The mechanism is the cell's own definition.** Cell 2 is *deep reversal into a **clean** path* —
price has fallen at least 2.47% in a straight line into the zone. Straight-line momentum does not
stop at the first 15-minute contact; **it keeps going through the close.** The daily-close entry
buys *after* the day's continuation; the touch entry buys *before* it, and pays the difference. The
zone holds, if it holds at all, over the following sessions — which is precisely why
[ADDENDUM 3](D413-ADDENDUM-3-cell-2-decays-monotonically-and-the-level-gap-does-not.md) found
the *first* bar after entry the weakest of the sweep.

**The consequence for a plan is concrete and it is the opposite of D403's founding assumption:**
*for cell 2, enter at the close, not the touch.* The touch is early by more than the whole daily
gross edge (+30.26 bp on the full universe).

---

## 4. Predictions

| | prediction | outcome |
|---|---|---|
| X-a | `[ALIGN]` passes, `[BASIS]` drops < 2% | correct — 0.06% — **after** a mis-written assertion was fixed (§6) |
| X-b | T1 fails, market delta within 2 SE of zero | correct — −0.4 SE |
| X-c | T2 passes | **wrong** — +1.1 SE gross; only the spread saved clears |
| **X-d** | **cell-2 stratum not distinguishable from pooled** | **WRONG — −35.08 against −1.60, a 4.9 SE effect the other way. The miss that matters.** |
| X-e | first touch inside the first hour for > 1/3 | correct — 59.6%, and **41.9% at the open itself** |

Three of five, and the one I called *indistinguishable* is the finding.

---

## 5. Stage 0 — the object was looked at

**P3.** 41.9% of first touches are the 09:30 bar; 59.6% are inside the first hour. **An "intraday
entry" on this construction is, two times in five, the open.** That is the daily gap landing in the
zone, not a level being tested intraday, and it is why the limit arm's fill convention (§6) matters.

**P4.** The largest delta is GameStop, 2021-03-10, demand zone `[36.26, 52.33]`, first touch 12:30,
market 49.50, close 65.76 — **+2,841 bp**, a squeeze day. A median event is Howmet, 2021-01-22, zone
`[25.13, 26.43]`, first touch 10:15, market 26.40, close 26.75, **+132 bp**. Both are what the
construction says they are.

---

## 6. Three things the runner decided that the pre-registration did not, and one it got wrong first

1. **`[BASIS]` was mis-written and dropped 88% on its first run.** `phi` is measured per session
   from the 15m 16:00 close against the daily close *with* the auction print, so it carries a few
   tenths of a percent of closing-auction noise on every session. The first version asked
   `phi[u] == phi[t]` to 1e-9 — equality between two noisy measurements, not the absence of a
   *step*. A real action is ≥ 2% (ILMN's spinoff was 2.7%, a split is 100%+); the observed noise
   is p99 0.29%, max 3.28%. The gate now sits at 2% and the noise scale is printed beside it. **The
   assertion fired on noise and I read the fixture's own docstring to find out why.**
2. **`[SAME-DAY]` carries a 10% tolerance.** §4 of the pre-registration said the runner stops if
   the 15m bars disagree with the daily touch. The 15m session ends at 15:45 and the daily bar does
   not, so a touch that happened only in the last quarter-hour or the closing auction is invisible
   on 15m bars — an expected miss, not a basis failure. 1.31% is that gap.
3. **A limit fills at the better of the edge and the open** when price gaps through the zone at
   09:30. That is the correct convention and is still optimistic on queue.

---

## 7. What this leaves

1. **Pooled, the 15-minute entry buys nothing but the spread.** ~6 bp median, on the optimistic
   fill. That is the honest value of "daily map, 15-minute execution" on this construction.
2. **In cell 2 it costs 35 bp.** Robust across years, sides, tails, and open-vs-intraday. For the
   one cell with a positive daily edge, **the daily close is the better entry, and a later one may
   be better still** — untested, and a different question.
3. **The signal was not tested here and is not confirmed** (§1 of the pre-registration). The
   cell-2 daily gross on these 32 names in this window was −2.20 ± 17.07 bp before any of this.
4. **2024-01-01 → 2026-08 on the 15m fixtures remains reserved.** It is the out-of-sample window
   for the cell-2 execution delta if that number is ever to be relied on.

**Disposition is the principal's.**

---

## 8. R13

Fourteenth look by object on price levels, first on execution. The 32 names and window have been
read by D403 (four of them) and now D414.

**Evidence:** `data/d414_15m_entry.json` — assertions, counts, the bar, every stratum, the
bar-of-day distribution, and **the full event list**, from which §3's splits are computed. Runner
`scripts/run_d414_15m_entry.py`, importing D413's construction and D403's basis repair rather than
restating either.
