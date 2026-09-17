# D416 — enter when the momentum stalls: the "later" question, made conditional

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D416-enter-when-the-momentum-stalls-the-later-question-made-conditional.md`. The H1 above is the full title.*

**Status:** design and bar committed BEFORE the runner exists (R8). Result separately.
**Date:** 2026-09-10
**Area:** Strategy research · execution

**Number.** `D416`, by PICKUP's three-command procedure: D400–D415 used, `D407–D410` reserved
(`044f839`), `D390–D399` reserved for `worktree-signal-hunt-part2` (`945cbb5`, live 13 hours ago).
Master takes D416.

---

## 1. Why, and what the last three records make this

[D414](D414-RESULT-the-15m-touch-is-35bp-too-early-in-the-one-cell-that.md) found the
first intraday touch is 35 bp too early in cell 2 because the momentum into the zone runs through
the close. [D415](D415-RESULT-the-candle-is-worse-than-the-clock-and-the-filter-drops.md)
found no intraday confirmation recovers it. Both left the same open question: **the daily close or
later — and how much later?**

This asks it **conditionally**: wait for the daily momentum *into* the zone to stop, then enter at
that day's close. The entry decision is D413's daily zone and cell; the entry *day* is chosen by a
momentum stall on daily bars.

**It moves back to the full daily universe** — 1,573 names, 2010–2026, D413's 180,050 resolved
touches — where the signal is visible (+13.21 bp pooled, +30.26 in cell 2). Power is not the
constraint it was on 32 survivor names.

---

## 2. THE TRAP, inherited from D415 with its two controls

**A stall rule is a filter as well as a timing.** Events that never stall inside the scan window
are the ones where price kept going, so the stalled subset is positively selected by construction.
D415 measured exactly this and it ran *both ways* — the confirming bar was a worse price than an
unconditional clock, and the declined events were the book's best trades. **Both controls are
therefore built in, and a rule that cannot beat both has found nothing:**

1. **The time-matched unconditional entry.** `k` = the rule's median stall lag in days among the
   events it stalls. The control enters at `t + k` on the same events, no condition. `rule −
   control` is the information in *the stall* beyond the information in *waiting k days*.
2. **The dropped trades, accounted.** For every event that never stalls in the window, D413's own
   entry-at-touch return is reported beside the stalled events'. A rule that discards the winners
   is a worse strategy even if its timed entries are better.

---

## 3. THE CONSTRUCTION

D413's events, unchanged: distance-armed departure zones, first touch on day `t`, the cell-2
flags at ADDENDUM 2's median cuts. Path-invariant throughout — every event its own trade, no slot
cap, no book.

**Three stall rules, one primary.** For a demand zone (long); supply is the mirror via `sign`.
Scanning runs over days `d = t+1 … t+L`, **`L = 10`**. The stall day is `s`. Every rule is a single
comparison with no knob.

| | rule | `s` = the first `d` with … | what it is |
|---|---|---|---|
| **S1 — PRIMARY** | up-day | `sign × (C_d − O_d) > 0` | the daily analogue of D415's R1: the first day the selling paused |
| S2 — shape | higher close | `sign × (C_d − C_{d−1}) > 0` | the first day that closed better than the last |
| S3 — shape | ROC turn | `sign × (log C_d − log C_{d−3}) ≥ 0` | a three-day momentum indicator crossing zero — the "momentum indicator" in the ordinary sense |

**S1 is primary because it is the least parametric and is D415's rule at daily resolution**, so the
two records answer the same question at two time scales. S2 and S3 **cannot clear** (R14).
**`L ∈ {5, 20}` is shape** and cannot clear either: `L` is the one declared parameter, it interacts
with the dropped-trade accounting (a longer window drops fewer), and its primary value is stated
once.

**The trades — all five-day holds, all entered at a daily close, all one round trip:**

```
r_base  = sign × (log C[t+5]   − log C[t])        D413's entry at the touch-day close
r_S     = sign × (log C[s+5]   − log C[s])        entry at the stall day's close
r_ctrl  = sign × (log C[t+k+5] − log C[t+k])      the time-matched unconditional entry
r_drop  = r_base on events with no stall in the window
```

**Every arm crosses the spread once at a daily close**, so every paired difference is already net
of matched costs. The neutral round-trip spread from ADDENDUM 2 (~33 bp pooled, ~22 bp in cell 2)
is reported for reference; it does not enter the gates.

Eligibility: `floor_mask_v2` at the entry day and live at the exit day, for every arm.

---

## 4. THE BAR — D415's three gates, on S1 pooled

| | condition |
|---|---|
| **G1** | S1 stalls **≥ 30%** of events inside `L = 10`; D413's event set reproduces exactly (§6, P2) |
| **T1** | `mean(r_S − r_base)` on stalled events **> 0 by 2 paired SE** — the stall entry beats the touch-day close |
| **T2** | `mean(r_S − r_ctrl)` on stalled events with `t+k` inside the window **> 0 by 2 paired SE** — it beats the clock |
| **T3** | `mean(r_drop) − mean(r_base | stalled)` is **not > 0 by 2 SE** — the filter does not discard the winners |

**All three must hold.** T1 without T2 is "later is better," which is a clock. T1 and T2 without
T3 is a better entry on a worse book.

### 4a. Cell 2 — declared SECONDARY, cannot clear

Cell 2 is the candidate every record since D413 has carried, with the caveat that it was selected
on spent data. It has **~26,000 events here**, so the same three tests are reported on it at the
same 2 SE — **labelled secondary and unable to clear D416 on their own**, D408's R1 pattern and the
same treatment D414 and D415 gave it. Pooled is the gate because pooled is unselected.

---

## 5. WHAT THE SWEEP ALREADY SAYS, stated before the run

[ADDENDUM 3](D413-ADDENDUM-3-cell-2-decays-monotonically-and-the-level-gap-does.md) gives
cell 2's cumulative return by hold from the touch-day close: `h=1 +6.31, h=2 +15.73, h=3 +22.63,
h=4 +28.74, h=5 +30.26, h=6 +27.71, h=7 +21.40`. The **marginal** per-bar edge is therefore
`+6.3, +9.4, +6.9, +6.1, +1.5, −2.6, −6.3` — **front-loaded from bar 2, and negative from bar 6.**

A five-day hold entered one day after the touch-day close captures bars 2–6 ≈ **+21 bp**; two days
after, bars 3–7 ≈ **+6 bp**; against +30 from the close itself. **The unconditional delay forfeits
the edge in cell 2**, and the stall day adds D415's definitional cost on top — an up-day's close is
higher than the day before's.

**This is the pre-registration's own prediction and the reason X-e below is the one that matters.**
If the stall entry beats the touch-day close anyway, the stall carries information the clock does
not — enough to overcome a front-loaded term structure — and that would be the first timing signal
this line has produced. If it does not, the touch-day close is the sweet spot: after the intraday
continuation D414 found, before the multi-day bounce the sweep found, and three studies will have
located it from three sides.

---

## 6. Stage 0

| | check |
|---|---|
| **P1** | per rule: stall rate inside `L`, lag distribution in days, `k`; and the share stalling on `t+1` (the earliest possible, which is nearly the baseline) |
| **P2** | D413's 180,050 resolved events and 26,024 cell-2 events reproduce exactly from D413's own runner — the event set is D413's, not a rebuild |
| **P3** | stall rate and lag **inside cell 2** against outside — the selection trap, if it shows in the rate |
| **P4** | **look at the object** — one cell-2 event printed end to end: touch day, each rule's stall day, entry, control entry, the three returns |

---

## 7. Predictions

| | prediction | confidence |
|---|---|---|
| **X-a** | S1 stalls **> 85%** of events inside 10 days, median lag **1–2 days** — an up-day is common | high |
| **X-b** | **pooled T1 fails** — the stall entry does not beat the touch-day close by 2 SE | moderate |
| **X-c** | **T2 fails** — the stall does not beat the clock; the up-day's close is the worse price, as R1's was at 15 minutes | moderate-high |
| **X-d** | **T3 PASSES** — the dropped trades are *worse* than the kept, because an event that never stalls in ten days is a zone that broke. **The opposite of D415's T3**, and it would make the stall a good *filter* even if it is a bad *timer* — though not a usable one, since the filter cannot be known at `t` | moderate-high |
| **X-e** | **cell 2: the stall entry is worse than the touch-day close by more than 10 bp** — §5's arithmetic | moderate-high |

**X-e is the study.** Its mechanism is stated in §5 in the runner's own quantities, and it is
computable from a record that already exists — which is the standard a prediction has to meet
here.

---

## 8. What this does not do

- **No holdout read.** `holdout2` stays unspent; this runs on the fixture D413 ran on.
- No 15m data. Nothing reserved on the daily fixture; stated, not assumed.
- No book, no slot cap. **No sweep of rule parameters** — the rules have none; `L` is declared
  once with two shape values.
- **Does not recommend a disposition.** That is the principal's.

---

## 9. R13

Sixteenth look by object on price levels; third on execution; the first execution study on the
full universe. Same events as D413 — no new data spent; the events are read a fourth time.

**Cost: seconds on a fixture already on disk.**
