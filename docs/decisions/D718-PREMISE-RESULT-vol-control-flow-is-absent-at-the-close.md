# D718 PREMISE RESULT — ABSENT: ES's last 15 minutes lean the way volatility-target funds would trade (+1.35 bp per sd of projected flow, the 96.8th percentile of its rotation), but not at t 2; yesterday's flow predicts as well as today's, 2020–2023 show nothing, and the sign trade grosses $0.50 a MES trade against $4.42

*2026-09-30. One run of `scripts/premise_d718_vol_control_close.py` (10 s).*
- **The order:** the [design record](D718-PREMISE-DESIGN-vol-control-flow-at-the-close.md) was committed before the
  runner, and the runner before the run.
- **Checks:**
  - the target weight w was re-derived by a plain loop on 40 days: equal;
  - the rotation's offset 0 equals the regression's β.
- **What it is:** ES only, 2016–2023 (with a warm-up from 2015-06). Nothing dated 2024-01-01 or later was read.
- **Output:** `data/premise_d718_vol_control_close.json`.

## The answer in one line

**The declared reading is ABSENT: G1 fails.**
- The 15:45 → 16:00 move rises by +1.35 bp per sd of the projected flow f, with the day's move to 15:45 controlled.
  But NW t is 1.35, under 2.
- The rotation (G2) puts it at the 96.8th percentile. It leans the way the mechanism predicts but is not established.
- The timing check (G4) says the lean is not today's flow either: **yesterday's already-executed flow predicts as
  much** (β +1.55, t 1.70).

## 1. The gates (1,405 days with f ≠ 0)

| gate | result | passes |
|---|---|---|
| **G1 exists** | β_close **+1.35 bp / sd (NW t 1.35)**. Momentum control γ −0.80 | **no** |
| G2 not chance | the enumerated rotation of f: p50 +0.01, p95 +1.18, percentile 0.968 | yes |
| G3 the close, not the day | the 11:45 placebo β −1.03 (t −1.92); the close exceeds it | yes |
| G4 today, not yesterday | f(d − 1) in f's place: β **+1.55 (t 1.70)** | yes (t < 2), but the point estimate is larger than today's |

## 2. Reported (none gates)

| line | β (t) or result |
|---|---|
| with the 14:30 → 15:30 hour also controlled (F2's own signal) | +1.59 (1.56) |
| **uncapped weight** | **+1.76 (2.85)** |
| λ = 0.90 | +1.88 (2.08) |
| λ = 0.97 | +0.09 (0.07) |
| **the up-day contrast** (days up to 15:45): the window on vol-rise days (the funds sell) against vol-fall days (they buy) | **−3.43 bp (225 days) against +1.04 bp (549)**, the direction the mechanism predicts |

- **The shape is sensitive to the convention.** The uncapped weight and the faster EWMA reach t 2 or more, and the slower
  one is zero.
  - These were declared as a shape to read, not as gates. Choosing one now would be selection.
  - The capped λ = 0.94 convention (the S&P rule) was the pre-registered one.
- **β by year** (t):

| year | β (t) |
|---|---|
| 2016 | +0.95 (1.12) |
| 2017 | no flow: the cap binds every day |
| 2018 | +3.65 (2.12) |
| 2019 | +1.49 (1.46) |
| 2020 | −1.97 (−0.48) |
| 2021 | +6.05 (3.10) |
| 2022 | −0.65 |
| 2023 | −0.18 |

  **The recent, higher-volatility years (2022–23), when the flow is non-zero on 95–98% of days, show nothing.**

**The sign trade** (sign(f) held 15:45 → 16:00, one MES, $4.42; reported only):

| book | trades a year | gross (t) | net (t) | win | bp |
|---|---:|---|---|---:|---:|
| every flow day | 176 | **+$0.50 (0.45)** | **−$3.92 (−3.50)** | 45.6% | +0.30 |
| the largest third of \|f\| | 59 | +$2.23 (1.13) | −$2.19 | 47.5% | +1.51 |
| LETF agrees (sign(f) = the day's sign) | 93 | +$1.32 (0.93) | −$3.10 | 45.7% | +0.61 |

Daily net Sharpe (every flow day) is −1.36 (Sortino −1.74), gross +0.17; ρ with the MACD arm is −0.13. The largest
flow days gross $2.23, half the round trip.

**F2 alignment** (the other session's request):
- On ES F2's 220 take days, the flow's sign equals F2's side 53.2% of the time, against 52.2% on all days.
- On NQ F2's 239 take days it is 53.6%, against 52.0%.
- **Vol-control flow does not explain F2's direction.**
- ρ of the sign trade's daily net with NQ F2 is −0.005.

## 3. What it says

1. **The flow's footprint is at most faint.** The direction is right: the rotation is at the 97th percentile, and the
   up-day contrast has the right sign. But the declared test does not reach t 2.
2. **It is not clearly today's flow.** Yesterday's projected flow predicts the close at least as well, which reads as
   volatility persistence rather than a mandated rebalance.
3. **It is gone where it would matter.** 2022–23 show nothing.
4. **As a trade it is dead at MES under any variant.** The strongest version grosses $2.23 against $4.42.
5. **Proposal A's construction is ABSENT at the premise stage.** The design said a trade record would follow only on
   PRESENT, so none is proposed. Closing A under R15 is the principal's call.

## CLOSED, 2026-09-30, on the principal's word

The principal: "Close A".
- **Closed under R15:** proposal A (volatility-target funds rebalancing at the close) as a trade on the ES close, any
  variant of its flow convention included.
- **The ordinary-day flow was tested here for the first time** and is recorded as absent at the premise stage.
- **The five-agent round of 2026-09-30 is now fully closed:** E (D708–D713), D (D709), C (D710), B and its reversal
  (D715, D717), and A (D718).
