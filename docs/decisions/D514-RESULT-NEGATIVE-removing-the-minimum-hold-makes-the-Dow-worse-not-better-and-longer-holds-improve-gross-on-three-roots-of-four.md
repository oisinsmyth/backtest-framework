# D514 RESULT — NEGATIVE: removing the minimum hold makes the Dow **worse**, not better. Gross improves with a **longer** hold on three roots of four, and the exit never had room to act

**Result of D514** (spec `85c4cc5`). Runner `scripts/run_d514_hold_ladder.py --run`
(`--selftest` passes, seven checks; 0.3 min), artefact `data/d514_hold_ladder.json`.
**2016-01-04 → 2023-12-29. No 2024+ slice was read.**

## 0. The answer

**No.** YM's gross is negative at every minimum hold, and shortening the hold makes it worse.

| M | YM gross $/session | YM gross $/trade | YM gross Sharpe | trips/session | mean hold, segments |
|---:|---:|---:|---:|---:|---:|
| **0 (no minimum)** | **−1.837** | −1.63 | −0.330 | 1.13 | 3.83 |
| 1 | −1.837 | −1.63 | −0.330 | 1.13 | 3.83 |
| 2 | −1.868 | −1.67 | −0.330 | 1.12 | 3.97 |
| 3 | −1.518 | −1.38 | −0.266 | 1.10 | 4.18 |
| 4 | −0.814 | −0.76 | −0.141 | 1.08 | 4.44 |
| **5 (the frozen value)** | **−0.412** | −0.40 | −0.070 | 1.03 | 4.78 |

**The primary** — YM's gross per session at no minimum hold — is **−$1.837**, against its own
rotation p95 of **+3.509** and an 18-cell family p95 of **+5.016**. **Verdict: NEGATIVE.** The exit is
exonerated: YM is signal-dead at this clock, exactly as D513's addendum read it.

**M = 0 and M = 1 are the same machine**, as the pre-registration predicted and the runner asserts:
a position entered at decision `t` carries `entry_t = t`, and the exit test is first evaluated at
`t + 1`, so the elapsed count is never zero at an exit opportunity. "No minimum hold" means M ≤ 1.

## 1. The direction is the opposite of the hypothesis, and it is general

**A longer hold gives better gross on three roots of four**, including the one where the signal is
alive:

| root | gross $/session at M ≤ 1 | at M = 5 | direction |
|---|---:|---:|---|
| **NQ** (reference) | +10.125 | **+13.021** | longer is better |
| YM | −1.837 | **−0.412** | longer is better |
| 6E | −1.753 | **−1.127** | longer is better |
| CL | −0.528 | −1.625 | shorter is better, the exception |

NQ's ladder is monotone across all six values: +10.13, +10.13, +10.65, +10.90, +11.93, +13.02. **The
frozen M = 5 is the best of the six on NQ's gross**, and the ladder is still rising where the window
stops it.

## 2. Why nothing much happened: the exit still has no room

**D491 said this would be the case and this confirms it on the AGREE arm and on gross.** Its words:
*"on 83% of sessions the construction IS a fixed day-session hold… the minimum hold did almost
nothing on the index roots, because the closure's six-hour window leaves nearly no scope for an
early exit. The idea is untested rather than refuted: it needs a window where it can act."*

Removing the hold entirely moves the machine very little:

| | at M = 5 | at M ≤ 1 |
|---|---:|---:|
| trips per session, YM | 1.03 | **1.13** |
| mean hold, YM | 4.78 segments | **3.83** |

**Prediction X-a expected trips of 1.3 to 1.8 at no minimum hold and got 1.10 to 1.16.** Six decision
points and a forced flat leave the conditional exit almost nothing to do at any setting of M. The
hold is not the binding constraint on this construction; **the window is.**

## 3. Predictions

| | predicted | observed | |
|---|---|---|---|
| X-a | trips 1.3–1.8 at M ≤ 1; hold falls to 2–4 segments | trips **1.10–1.16**; hold 3.8–4.0 | **wrong on trips**, right on the hold; M barely binds at all |
| X-b | YM gross at M ≤ 1 still negative, −$3 to 0 | **−$1.84** | right |
| X-c | gross falls as M falls on ≥ 2 of 3 declared roots | **2 of 3** (YM, 6E; CL the exception) | right |
| X-d | NQ gross positive at every M, +$8 to +$16 | **+$10.13 to +$13.02** | right |
| X-e | family p95 in [+$1, +$4]; no YM cell clears | p95 **+$5.02**; none clears | conclusion right, **band too narrow** |
| X-f | the verdict is NEGATIVE | NEGATIVE | right |

**Four of six.**

## 4. What stands

- **The Dow's negative gross is not an artefact of the exit.** Removing the minimum hold makes it
  worse at every step. D513's addendum reading holds: YM, CL and 6E are **signal-dead** at this clock,
  while ZN, ZB and GC are **cost-dead**. Two different failures, and this one rules the exit out of
  the first.
- **Gross rises with hold length on three roots of four, and the window caps the hold.** NQ's ladder
  is still climbing at M = 5, where six decision points and the 16:00 flatten stop it. **The
  construction sits at its window's ceiling**, and the only way past it is to hold overnight, which
  the prop flatten forbids (P2). That is a constraint of the venue, not of the signal.
- **Nothing about the admitted arm is re-specified.** NQ was a reference row, not a declared cell,
  its 2024+ is spent, and no figure here changes the book.
- **Nothing was spent.** No 2024+ slice was read on any root.

## 5. Files

Runner · this record · the artefact · D513's addendum (the cost-dead versus signal-dead split) ·
D491 (which predicted §2) · PICKUP.
