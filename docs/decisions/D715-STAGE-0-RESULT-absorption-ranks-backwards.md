# D715 STAGE 0 RESULT — NEITHER: the absorption score ranks the 10:30 → close outcome backwards (Spearman −0.061, the 0.7th percentile of its rotation); absorbed morning moves reverse and pushed ones continue, the opposite of proposal B's mechanism

*2026-09-30. One run of `scripts/stage0_d715_absorbed_morning.py` (25 s).*
- **The order:** the [design record](D715-STAGE-0-DESIGN-the-absorbed-morning-move.md) (`582022f6`) was committed
  before the runner; the runner and its contract-code fix were committed before the run.
- **The first launch stopped before any statistic.** Sierra writes contracts as ESH16 and the bars as ESH6, so no
  session's flow matched.
- **Checks:**
  - 40 candidates re-derived from the raw rows by a plain loop (m, I, z, R): equal;
  - F2's known answer re-proved (252 trades, +$13.208968) before its correlation was computed;
  - the absorbed share after the burn-in was 0.501.
- **What it is:** in-sample, 2016-01-04 → 2023-12-29, at one MES and $4.42. Nothing dated 2024-01-01 or later was
  read.
- **Output:** `data/stage0_d715_absorbed_morning.json`.

## The answer in one line

**The declared reading is NEITHER.** The mechanism gate G1 fails, and not by falling short: **it is significantly
inverted.**
- A morning move made with less aggressive flow than its size predicts **reverses** by the close.
- A move made with more aggressive flow **continues**.
- Proposal B predicted the opposite.

## 1. The candidates

- **1,961 of 1,993 ES sessions** qualify. 32 roll sessions are excluded, and none fails the flow-coverage rule.
- **The walk-forward burn-ins** leave 1,675 sessions with a residual R (G1's set). 1,425 have R's prior median as well
  (the books), and the first trade is on 2018-02-12.
- **Breadth** (at least two of NQ, RTY and YM agreeing) holds on 88% of candidates.

## 2. The gates

| gate | result | passes |
|---|---|---|
| **G1 mechanism** | Spearman ρ(absorption, gross) **−0.061**. The rotation's p50 is −0.000 and p95 +0.041 (1,636 offsets, SE 0), and **the observed value is at the 0.7th percentile** | **no, inverted** |
| G2 edge | book B nets −$11.64 (NW t −1.77); its efficiency is at the 3.8th percentile of the take-mask rotation | no |
| G3 ingredients | absorbed −$8.32 gross against pushed **+$9.15**; B −$7.22 | no |
| G4 not one episode | B is negative without 2020 (−$14.56) and without 2022 (−$8.03), positive in 2 of 6 years | no |
| G5 beyond the drift | T −$7.40 | no |

**The absorption quintiles** (gross per MES trade, 10:30 → 15:59, 335 each):

| quintile | 0 (most pushed) | 1 | 2 | 3 | 4 (most absorbed) |
|---|---:|---:|---:|---:|---:|
| mean gross | +$7.12 | **+$11.88** | +$4.66 | −$8.77 | **−$11.99** |

The gradient is monotone across the middle and clearly the wrong way.

## 3. The books (one MES; the four groups)

| book | trades | gross (NW t) | net (NW t) | median net | win | daily net Sharpe (Sortino); gross | ρ arm |
|---|---:|---|---|---:|---:|---|---:|
| **B, absorbed + breadth (primary)** | 626 | −$7.22 (−1.10) | **−$11.64 (−1.77)** | −$8.17 | 46.3% | −0.66 (−0.87); −0.41 | +0.19 |
| A, absorbed | 714 | −$8.32 (−1.39) | −$12.74 (−2.13) | −$8.17 | 46.4% | −0.78 (−1.01) | +0.19 |
| Pu, pushed | 711 | **+$9.15 (1.87)** | +$4.73 (0.97) | +$4.33 | 51.9% | +0.35 (+0.48); +0.67 | +0.09 |
| Br, breadth only | 1,256 | +$1.44 (0.37) | −$2.98 | −$2.54 | 49.0% | −0.26 | +0.20 |
| E0, every candidate | 1,425 | +$0.40 (0.11) | −$4.02 | −$1.92 | 49.1% | −0.38 | +0.20 |
| quiet + breadth (the unsigned secondary) | 620 | −$3.59 | −$8.01 | −$5.67 | 48.4% | −0.51 | +0.07 |

**Book B's detail:**
- **Distribution:** skew −0.22, kurtosis 6.1; trims 1%: ex-top −$17.21, ex-bottom −$6.23, both −$11.80. Max
  drawdown $8,848.
- **By year:** 2018 −$2,832, 2019 −$306, 2020 +$289, 2021 −$2,135, 2022 −$3,055, 2023 +$755.
- **Long −$7.38, short −$16.36** a trade. By price tercile −$17.37 / −$2.62 / −$14.87.
- **The F2 overlap:** 39% of B's gross falls in 15:30 → 16:00. ρ with F2's daily net is −0.09 (1,360 days).
- **Breadth against random deletion** (D714's check): B's Σnet / Σ|net| against 20,000 count-matched deletions of A's
  trades ranks at 0.70 (p50 −0.118, p95 −0.085). The cross-root agreement adds nothing.
- **The plain first-hour direction (E0) carries nothing:** +$0.40 gross, as D670 and D673 found.

## 4. What it says

1. **B's mechanism is wrong on ES's first hour.**
   - The house's fade findings (D697 bursts, D695's aggressively bought hours on V1, D499's large-move hour) do not
     extend to "absorbed morning moves continue".
   - Here, moves carried by more aggressive flow than their size predicts continue to the close, and moves carried by
     less aggressive flow reverse.
   - This sits opposite D704's gate (about +1 SE on V1's short-gamma trades), so the sign of the flow residual depends
     on the setting. No general "no-push" rule holds.
2. **The inverse is post hoc and not carried.** The pushed half nets +$4.73 a trade (t 0.97) at a daily Sharpe of
   +0.35. It was found by inverting a failed gate on the sample that failed it. Testing "pushed moves continue" would
   need a new mechanism statement, a new pre-registration and unseen data, and its in-sample t is under 1.
3. **Under R15 this closes proposal B's construction.** Closing the avenue (aggressor flow as a direction conditioner on
   the ES day session) is the principal's call. With D695 and D704, this is the third flow-conditioner result that does
   not establish direction.
