# D381 — stops and targets at thresholds that actually select a tail

**Date:** 2026-09-08
**Kind:** **SIGNAL TEST (R15) on an OVERLAY**, governed by [R7](../RULES.md#r7). Admits nothing, reads no holdout.
**Pre-registered under R8 — committed before the runner exists. Result committed separately.**
**Corrects:** [D380 §6a](D380-RESULT-no-exit-overlay-beats-not-cutting-and-R7s-control.md),
where my ±200 bp thresholds fired on ~80% of trades and tested something other than a stop or a target.

---

## 0. Why this record exists

D380 tested three exit overlays and none beat holding to the cap. **Two of the three were
mis-specified**, and the principal identified it: *a stop that triggers on 79% of trades is not a
stop for this strategy, and the same goes for an 81% target.*

The cause, measured on the baseline's own paths:

| the baseline's paths | p50 | p90 / p10 |
|---|---:|---:|
| max **favourable** excursion | **+839.4** | +2,837.6 |
| max **adverse** excursion | **−772.5** | −2,510.8 |

**The median trade swings +839 up and −773 down at some point in its life.** A ±200 bp threshold sits
at a quarter of that — inside the ordinary wander of nearly every path. It never selected a tail.

**The error was one level down from D374's.** D374 retired a hurdle whose threshold was fixed in
advance of the *universe*; ±200 was fixed in advance of the *path distribution*. **The fix is to
declare a FIRE RATE and convert it to basis points from the data**, which is what this record does.

**What D380 established and this record does not revisit:** E1, the signal-invalidation overlay, has
no threshold, fires on 99.6% of trades because that is what the rule does, and **fails both its
controls**. That verdict stands. So does §2's finding that R7's control inherits the rule's trade
selection — this study is designed around it.

---

## 1. What is frozen

**D373's primary cell, inherited unchanged**, as every study since D374 has inherited it: `rev_5` dip
inside the `mom_252_21` top decile, long, next-open fill, hedged, **40-bar cap**, cell
**10:90 / cap 40**, mining prefix. `[MIR]` must reproduce **3,932 trades, +160.55 mean, +51.55
median** first. **Hedge convention H0**, for comparability, with the H1 figure reported beside it.

**Entries are identical under every arm**, so the trade count stays 3,932 and `[OVL]` proves it.

---

## 2. The six arms, with their thresholds stated as numbers

**The thresholds are already known** — they were computed and published in D380 §6a's correction from
the same stored paths. **Writing them here as numbers is more honest than implying they are unseen.**
What is *not* known is any result at these thresholds.

| arm | rule | declared fire rate | **threshold** |
|---|---|---:|---:|
| **T05** | profit target | 5% | **+3,798.8 bp** |
| **T10** | profit target | 10% | **+2,837.6 bp** |
| **T20** | profit target | 20% | **+1,881.2 bp** |
| **S05** | stop | 5% | **−3,229.4 bp** |
| **S10** | stop | 10% | **−2,510.8 bp** |
| **S20** | stop | 20% | **−1,743.0 bp** |

A trade fires an arm when its cumulative hedged path **first reaches** the threshold within its own
40-bar window; it then exits on that bar. Otherwise it holds to the cap, exactly as E0 does.

`[CAL]` asserts each arm's **realised** fire rate is within **2 percentage points** of its declared
one. A threshold that does not fire where it was calibrated to fire is not the arm this record names.

---

## 3. The comparison — BOTH benchmarks, which is D380's own correction

D380 §2 found that R7's matched-count control **inherits whichever trades the rule selects**: its p50
ran from **+11.95** (rule fires on winners) to **+181.11** (fires on losers, *harder than doing
nothing*). So a control-only verdict is not interpretable on its own, and **D380's pre-registration
omitted the baseline. This one does not.**

> **An arm works only if it beats BOTH: its own matched-count control (p95), AND the un-overlaid
> baseline's +160.55.** Neither alone.

**And §2's finding gives a directional expectation that doubles as a validity check:** the **stop**
arms fire on losers, so **their controls should centre ABOVE the baseline**; the **target** arms fire
on winners, so **theirs should centre below it**. If that ordering does not appear, the controls are
not doing what D380 says they do, and §8 applies.

**The control**, per R7 and D380: take exactly the trades the arm shortens, keep that set and count
fixed, cut each at a bar drawn uniformly from its own window `[1, hold_E0)`. A **loose** control that
re-draws which trades are cut, at the same count, is reported beside it.

**Draws: 2,000 per arm per control.** All of it is re-cutting one stored cumulative-sum matrix, so it
costs seconds, not parts.

---

## 4. The hurdles

| | hurdle | |
|---|---|---|
| **V1** | **an arm's gross mean per trade beats its strict control's p95 by > 2 SE, AND beats the baseline's +160.55** | **PRIMARY.** Both legs. §3 |
| **V2** | **V1 with the single largest trade removed** | **GATE.** D373's H1 died on one trade; the check has been a gate since D378 and stays one |
| **V3** | *reported* — the median per trade, and the arm against its **loose** control | where any gain lives, and whether it is trade selection rather than timing |
| **V4** | *reported* — **each control's own p50**, against the baseline | documents §3's inheritance effect at properly-scaled fire rates |
| **V5** | *reported* — mean holding run, turnover per bar, and the gross figure against the measured round trip under **both** PB and PUB | R15: cost gates nothing at the signal stage |

**Best-of-6 pricing.** Six arms are scored. **Any arm claimed as a winner must clear its control's p95
by ≥ 4 SE, not 2** — the doubling D377 used for a best-of-4 — and **all six are reported in full**, so
the reader sees the grid rather than the survivor.

---

## 5. Assertions

Inherited from D380 and re-run: **`[MIR]`**, **`[CUT]`** (the re-cut reproduces the kernel's own
per-trade P&L; it came back at 0.000e+00), **`[OVL]`** (every hold ≤ the baseline's, trade count
fixed), **`[R7]`** (the control cuts the same trades at the same count inside each trade's own
window), **`[FIRE]`**, **`[DIR]`**, **`[X]`**.

**New here:**

| tag | what it proves |
|---|---|
| **`[CAL]`** | each arm's realised fire rate is within **2 percentage points** of its declared rate — the assertion that the whole point of this record was achieved |
| **`[MONO]`** | fire rates are **monotone in threshold**: T05 fires on fewer trades than T10, which fires on fewer than T20, and likewise for the stops. A non-monotone grid means the excursion calculation is wrong |

**Persist before rendering.**

---

## 6. The search cost

**Six arms, one cell, one primary statistic.** The fire-rate grid {5, 10, 20}% and both directions
were chosen for coverage, not from results, and the thresholds follow mechanically from them. Priced
as a best-of-6 (§4). Under [R13](../RULES.md#r13) this adds **one look** to the winners'-dip ledger,
disclosed, on a fixture already spent. **No holdout is read.**

---

## 7. Predictions

**D380's mis-scaled arms told us nothing about properly-scaled ones, so these are genuinely open.**

| | prediction |
|---|---|
| **Q1** | **all three TARGET arms reduce the mean below +160.55.** The book's return is tail-driven — its mean excluding the top 1% is **+73.24** — and a target truncates exactly that tail. **T05 should hurt least** and still hurt |
| **Q2** | **at least one STOP arm beats the baseline's +160.55.** This is the overlay that can help a tail-driven book: it truncates the left tail and leaves the right intact. **This is the arm I expect to work**, and it is the opposite of D380's mis-scaled stop, which was the worst thing in that study |
| **Q3** | **the stop controls centre ABOVE +160.55 and the target controls below it** — §3's validity check, and D380 §2's mechanism at correct scale |
| **Q4** | **AGAINST myself: no arm clears V1 on BOTH legs.** A stop that beats the baseline will not also beat a control that is itself better than the baseline. **I expect the study to close stops and targets, and Q2 to be true while V1 still fails** |
| **Q5** | `[CAL]` holds on all six — realised fire rates within 2 points of declared |
| **Q6** | the **best stop arm is S10 or S20**, not S05: a 5% stop truncates too little to move a 3,932-trade mean |
| **Q7** | **V5 shows the stops barely change turnover** — they fire on 5–20% of trades and cut a fraction of a 40-bar hold, so the round-trip count is nearly unchanged. **Unlike D380's invalidation book at 6.4× turnover, cost should not be what decides this one** |

---

## 8. What would make me abandon this

- **`[CAL]` fails** → the thresholds do not fire where they were calibrated to; the arms are not what
  this record names and nothing may be reported under those names. Stop and re-derive.
- **`[MONO]` fails** → the excursion calculation is wrong. Stop.
- **§3's directional check fails** — stop controls not above the baseline, target controls not below
  → D380 §2's mechanism does not hold at this scale, which is itself a finding, and the arm verdicts
  are reported as **uninterpretable** rather than as verdicts.
- **Every arm fails V1's baseline leg** → **exits are closed on this construction**, properly scaled
  this time, and the record says so plainly rather than proposing a fourth parameterisation.

---

*Pre-registered 2026-09-08. Runner does not exist at the time of this commit (R8).*
