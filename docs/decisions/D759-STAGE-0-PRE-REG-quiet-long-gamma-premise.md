# D759 STAGE 0 PRE-REGISTRATION — the premise check for quiet long-gamma days: is the reverting rate seen in D757 above the 10:30 fade's break-even on non-impulse days?

*2026-10-02. Prop book.*
- *The principal: "Strong long-gamma days without an early impulse premise check first".*
- *Numbered D759, claimed with the documentation-review session.*
- ***Committed alone, before its runner exists.** In-sample only (≤ 2023-12-29).*

## 0. What is already seen, and the one new quantity

**Seen POST HOC in D757 (`data/stage0_d757_gamma_impulse.json`).** On strong long-gamma days (G: GEX at the prior
close in its walk-forward top tercile) **without** a 10:30 impulse (¬I: \|z₁₀:₃₀\| < 1.5), the reverting-day (RD)
rate:

| root | RD rate | days |
|---|---|---|
| ES | 0.3745 | 542 |
| NQ | 0.378 | 508 |
| YM | 0.4039 | 510 |
| RTY | 0.4058 | 308 |

**Pooled over ES, YM and RTY (D757's decision roots): about 0.393 on 1,360 days, binomial SE about 0.013.**

**Re-measuring that rate in-sample is no evidence:** it is where it was found.

**The new quantity is the trade's break-even on its own population.** p\*, measured on non-impulse days for the
fade D757 declared, says whether a selector with that precision could pay at all.

**This record does NOT compute the fade's net on G ∧ ¬I days, or any gamma-conditional P&L.** That is the trading
test. It stays unread, for a pre-registered read on the held 2024-01 → 2025-02 slice, on the principal's word.

## 1. Definitions (D757's, unchanged; D756's label and costs)

- **G, I and RD:** exactly as `scripts/stage0_d757_gamma_impulse.py` and `scripts/stage0_d756_reverting_days.py`
  build them, read-only.
- **The trade:** the fade at **10:30**, side −sign(P₁₀:₃₀ − O), exit at 15:59's close, one micro, net of the
  default-line cost (D757's). A day with P₁₀:₃₀ = O does not trade.
- **The population: every non-impulse day (¬I),** across all gamma states, pooled over ES, YM and RTY. NQ is
  reported only (D727).

## 2. The computation

**The prize on non-impulse days:**
- μ_RD and μ_non: the mean net of the fade on ¬I days that are and are not RD, with t, median and win rate;
- **Z:** μ_RD > 0 at t ≥ 2, and the mean \|net\| on ¬I ∧ RD days ≥ 3× cost;
- **p\*:** −μ_non / (μ_RD − μ_non).

**The seen precision:** P(RD \| G ∧ ¬I) pooled = q, recomputed exactly (the known answer below), with its binomial
SE.

## 3. The reading

| reading | condition | what follows |
|---|---|---|
| **NO PRIZE** | Z fails | |
| **NO ROOM** | q < p\* | the line stops |
| **THIN** | p\* ≤ q < p\* + 2 SE | the principal decides whether the held slice is worth spending on it |
| **ROOM** | q ≥ p\* + 2 SE | a trading pre-registration may follow, read only on the held slice, on the principal's word |

**Reported:** the same per root, NQ included; and p\* split by gamma state (G and ¬G among ¬I days) **for the
prize only**, never as net on the selected days.

## 4. Assertions

1. **The known answer:** D757's G ∧ ¬I cells are reproduced exactly per root (ES 542 / 0.3745, NQ 508 / 0.378,
   YM 510 / 0.4039, RTY 308 / 0.4058), and D757's impulse-day p\* of 0.29636.
2. **Sign in money:** D756's `fade` (as D757).
3. **The seal:** nothing on or after 2024-01-01 is read.

## 5. Predictions (Opus)

- **P1:** Z holds (P 0.7). A reverting day still pays a fade that is already leaning the right way, even on a small
  morning move.
- **P2: NO ROOM** (P 0.6). On quiet mornings there is little to give back, so μ_RD is small, while the trend days
  that follow a quiet morning still cost a full day's move. I expect p\* between 0.45 and 0.55.
- **P(ROOM) ≈ 0.15.**
