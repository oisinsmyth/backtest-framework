# D757 STAGE 0 RESULT — NOT A DETECTOR: impulse days are trend starts (24 % reverting against a 33 % base), and strong long gamma does not change that (+1.6 points, p 0.26)

*2026-10-02. Prop book.*
- *Pre-registration: [D757](D757-STAGE-0-PRE-REG-gamma-and-impulse-reverting-days.md) (fb58ae7f).*
- *Runner: `scripts/stage0_d757_gamma_impulse.py`, committed before its run (2e649cb5). One known-answer fix
  (ea1a1bf6) came after an attempt that stopped at that check, with the mean already matching exactly and no prize
  or test computed.*
- *Output: `data/stage0_d757_gamma_impulse.json`. Wall 15 s.*
- *The known answer held: D756's traded reverting days (2,440) and its 10:00 prize (+\$34.19). The GEX lag canary
  fired; vector == loop on 50 offsets.*

## 0. The reading

| | | |
|---|---|---|
| **Z₁₀:₃₀**, the prize on impulse days (ES, YM, RTY) | reverting: **+\$65.29** (t 20.1, win 97.5 %, n 353); other: −\$27.50 (n 1,100) | holds |
| **p\*** on impulse days | **0.296** | |
| **T1**, gamma adds to the impulse | P(RD \| G ∧ I) **0.245** (n 465) against P(RD \| ¬G ∧ I) **0.229** (n 802): **+0.016, p_high 0.259** (null p50 −0.003, p95 +0.046) | **fails** |
| **T2**, precision ≥ p\* | 0.245 < 0.296 | fails |
| **T3**, at least 150 days | 465 | holds |

**NOT A DETECTOR.**

## 1. What it shows

**Impulse days are mostly trend days.** A move of at least 1.5σ (time-scaled) by 10:30 is followed by a reverting
day only **22.7–25.3 %** of the time on every root, against the 33.3 % base. A big early move usually keeps going.
This holds on ES, YM and RTY as well as NQ, in line with D727's detection curve.

**The prize is large when an impulse day does revert.** The 10:30 fade nets +\$65 on those days with a 97.5 % win
rate, which brings p\* down to 0.296. But gamma doesn't find those days: strong long gamma adds 1.6 points, inside
the null.

**Per root,** RD rate for G ∧ I / I alone / G alone:

| root | G ∧ I | I alone | G alone |
|---|---|---|---|
| ES | 0.234 | 0.249 | 0.348 |
| NQ | 0.259 | 0.229 | 0.349 |
| YM | 0.233 | 0.227 | 0.363 |
| RTY | 0.264 | 0.253 | 0.354 |

## 2. A POST HOC pattern, recorded and not evidence

**Strong long gamma *without* an impulse** (G ∧ ¬I) is followed by a reverting day **37.5–40.6 %** of the time on
all four roots:

| root | RD rate | days |
|---|---|---|
| ES | 0.375 | 542 |
| NQ | 0.378 | 508 |
| YM | 0.404 | 510 |
| RTY | 0.406 | 308 |

**Two cautions:**
- On those days the morning move is small by construction, so a 10:30 fade has less to give back. **Its p\* is
  unknown and probably higher** than the impulse days' 0.296.
- It was seen after the run.

**What it means.** The principal's idea may work the other way round: the long-gamma reverting day is the quiet
one, not the stretched one. Testing it needs its own pre-registration, with its own prize and p\*, read only on the
held 2024-01 → 2025-02 slice, on the principal's word.

## 3. Predictions against outcomes

| | predicted | outcome |
|---|---|---|
| P1 | Z₁₀:₃₀ holds | **held** (+\$65.29, t 20.1) |
| P2 | impulse days revert less than base (P 0.5) | **held** (0.23–0.25 on every root) |
| P3 | T1 fails (P 0.7) | **held** (p 0.26) |
| | P(DETECTOR WORTH IT) ≈ 0.05 | NOT A DETECTOR |

## 4. What follows

- **No trading rule.** The combined detector is no better than the impulse alone, and the impulse alone selects
  *against* reverting days.
- **The intraday mean-reversion closure on the index micros stands for trading.**
- **D756's gap × alternation lead and this record's gamma-without-impulse pattern** are both post hoc. If either is
  pursued, it should be declared with its own prize and read on the held slice.
