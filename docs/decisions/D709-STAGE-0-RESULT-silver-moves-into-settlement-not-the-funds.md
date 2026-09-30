# D709 STAGE 0 RESULT — FAIL (not the funds): silver does move into its settlement window with the day's sign after 2019 (+$5.63 a SIL gross, t 3.14, above every rotation), but it did so before 2019 too, when the funds did not hedge there; the net at $8 is negative, and the effect has faded since 2021

*2026-09-30. One run of `scripts/stage0_d709_silver_settlement_flow.py`. The runner was committed at `e7b20c6a` with
POWER and amendment A1, and its path fix at the next commit, before the run.*
- **The order:** the [design record](D709-STAGE-0-DESIGN-silver-letf-settlement-flow.md) was committed before the
  runner existed; A1 (the gold gate) was ruled after POWER and before the run.
- **Two earlier launches stopped before computing anything,** after the data load: the system Python lacked scipy, and
  D618's fixture path pointed inside the worktree. Nothing was computed or written.
- **What it is:** in-sample, 2011-01-03 → 2023-12-29. Nothing dated 2024-01-01 or later was read from SI, GC or the
  funds' files. The arm loader's read of its own NQ fixture is disclosed in the output.
- **Output:** `data/d709_silver_settlement_flow.json`.
- **The premise check P0 holds.** AGQ, ZSL, UGL and GLL match the rebuilt settlement subindex within 5 bp on 99.7% of
  post-era days, and on 1.4–4.6% of pre-era days. The benchmark switch is real in the data.

## The answer in one line

**The declared reading is FAIL (not the funds), on G3.**
- The settlement-window move exists after the funds moved to the settlement (G1 passes), and it is specific to the
  clock (the midday placebo is flat) and to silver (gold is flat).
- **But it existed before 2019 as well** (t 4.03), when the funds struck at the London fix.
- **By the design's rule, a pre-era effect means the move is not the funds'.**

## 1. The cells (gross per contract, one trade a day)

| cell | trades | mean gross | t | rank in its enumerated rotation null |
|---|---:|---:|---:|---:|
| **SI settlement, post-era** (2019-01-07 → 2023) | 979 | **+$5.63** | **3.14** | 1.000 (p50 +$0.10, p95 +$2.79) |
| SI settlement, pre-era (2011 → 2019-01-04) | 1,512 | +$10.55 | 4.03 | 1.000 (p95 +$4.20) |
| SI midday placebo, post | 984 | −$1.05 | −0.53 | 0.32 |
| SI midday placebo, pre | 1,521 | −$5.39 | −2.28 | 0.01 |
| GC settlement, post (one MGC) | 1,017 | −$0.74 | −1.06 | 0.14 |
| GC settlement, pre | 1,570 | +$1.18 | 2.09 | 0.98 |
| GC midday, post | 1,019 | −$0.28 | −0.36 | 0.34 |

The SE ladder for the post-era SI cell runs from 2.79 (monthly block) to 3.14 (ordinary). Every rung clears 2.

## 2. The gates

| gate | result | passes |
|---|---|---|
| G1 edge | +$5.63, t 3.14, above the p95 (+$2.79) | yes |
| G2 clock | midday placebo t −0.53; settlement minus midday on the same days +$6.57 (t 2.48) | yes |
| **G3 era** | **pre-era t 4.03** (bar < 2); post − pre −$4.92 | **no** |
| G4 gold (A1) | gold's post mean in σ units −0.0054 against silver's +0.0145; does not fire. The superseded "t < 2" rule would also pass (gold t −1.06) | yes |
| G5 dose | Q̂/V terciles +$2.21 / +$7.26 / +$7.42; top > bottom | yes |
| N net at $8 | −$2.37 (t −1.32) | no |

- **G5b, the attribution qualifier:** top minus bottom +$5.21 against the AUM-rotation null (p50 +$2.37, p95 +$7.07),
  rank 0.85. Scale unresolved.
- **The dose does not follow the funds' size.** By AUM tercile the means are +$8.57 / +$1.25 / +$7.09.

## 3. What the reported lines add (none gates; they are read with care)

**The pre-era effect is all before the 2015 pit closure.**

| pre-era part | trades | mean gross | t |
|---|---:|---:|---:|
| 2011-01 → 2015-06 (pit era) | 833 | +$18.40 | 4.00 |
| **2015-07 → 2019-01-04** (electronic, funds at the London fix) | 679 | **+$0.91** | 0.65 |

- **The three periods line up with the mechanism.** 2015-07 → 2019-01 is the only period when the settlement was
  electronic and the funds were not hedging at it, and it shows nothing. The post-era shows +$5.63.
- **The pit-era effect has a different source.** The settlement then was set in the pit, by a different procedure.
- **This is post hoc.** The design declared the whole pre-era as the placebo and reported the pit split beside it. The
  verdict does not change, but a redesign would have its placebo era.

**The post-era is fading.**

| year | trades | mean gross | t |
|---|---:|---:|---:|
| 2019 | 190 | +$9.82 | 2.89 |
| 2020 | 193 | +$17.80 | 3.25 |
| 2021 | 195 | +$4.18 | 1.04 |
| 2022 | 201 | +$0.87 | 0.24 |
| 2023 | 200 | −$3.87 | −1.26 |

- Without 2020 the mean is +$2.65 (t 1.49).
- The last two in-sample years carry nothing, even though fund AUM in 2021–2023 was larger than in 2019–2020 (§5 of the
  design).
- The fade matches the precedent the design named: flows that are published and anticipated get absorbed (D685–D687).

**Other mechanism diagnostics:**
- **The event curve** builds steadily from the fill to the window: +$0.54 at one minute, +$4.27 at 16 minutes, +$5.63
  at the exit.
- **The 30 minutes after the settlement** revert +$3.16 against s (t 1.94), which is temporary pressure (P6).
- **An exit at the official settlement** gives +$6.77 (t 3.81).
- **The form question (D648):** the payoff loads on the inventory-risk projection x̂_GM (t 3.61), not on the
  square-root one (t −0.79). At midday, neither.
- **The triple difference** in σ units, (SI post − pre) − (GC post − pre), is +0.0124 (t 1.39).

## 4. The four groups and the component line (SI post-era, one SIL, $8)

**Performance.**

| | per trade | daily book (1,287 sessions, 76% exposed): Sharpe (Sortino) | max DD |
|---|---|---|---:|
| gross | +$5.63 (t 3.14) | **+1.39 (+2.47)** | $1,245 |
| net at $8 | −$2.37 (t −1.32) | **−0.58 (−0.92)**, SE 0.52 | $5,548 |
| net at $13 / $24.50 (stresses) | −$7.37 / −$18.87 | −1.81 / −4.59 | |

- The mean move is 0.35 × 2c ($16). **The breakeven round trip is $5.63.**
- Daily σ is $49 at one SIL.

**The trade distribution (gross).**
- n 979, mean +$5.63, median +$5.00, win rate 51.6%, payoff 1.14.
- Skew +2.02, excess kurtosis 15.6.
- Trims 1%: ex-top +$2.84, ex-bottom +$7.09, **both +$4.29**. The mean is above the median.
- **The top trade:** 2019-09-06, SIZ9, short from 18.61 to 18.07, +$540.

**Dependence.**
- 4 of 5 years profitable. Half the P&L comes from 9 days; the top 10 days are 53%.
- **By price tercile:** +$9.36 / +$0.54 / +$7.02.
- **When the front is the index contract:** +$6.11 (t 3.11, 856 trades). When it is not: +$2.32 (123).
- **The carved index-roll days** (reported beside): +$8.32 (t 1.24, 179).
- The contract more than 10 sessions from first notice (a stricter buffer): +$5.87 (t 3.01).

**Nulls.** Every cell's enumerated rotation is shown in §1. The p95s have SE 0.

**The component line:** at one SIL and $8, the net daily Sharpe is −0.58 (Sortino −0.92), SE 0.52. Hit rate 45.9%,
daily skew +2.28, gross +1.39 beside it. ρ +0.05 with #2 (the MACD arm) and +0.03 with #4 (F2). ρ with #3 is not
computable.

**The declared secondary (the oracle, D690).**
- The oracle's net > 0 takes 449 trades for +$16,948.
- The size-only oracle captures 1.6% of that. Size alone carries nothing here.
- No filter is proposed. The principal designs filters, and the effect's fade argues against one.

## 5. What it says

1. **Silver's settlement window carries the day's sign in 2019–2020, and nothing since.** In-sample the effect is
   real: above every rotation, specific to the clock and to silver, and partly reversed afterwards. But it pays below
   the $8 round trip, and 2021–2023 show nothing.
2. **The funds are not established as its cause.** The declared test failed: the pre-era carried the effect too.
   Reported, not declared: the pre-era effect sits entirely in the pit era, and 2015-07 → 2019-01 is flat, which is
   what the funds' mechanism predicts. The data do not decide between the two readings.
3. **Why it is not worth a redesign now:** a redesign could declare 2015-07 → 2019-01 as the placebo era. But the
   post-era has faded to nothing in the last two in-sample years. Unseen data would be testing a flow that the market
   seems to have learned to absorb, as with month-end (D685–D687).
4. **Under R15, this closes the construction, not the avenue.** Closing the silver settlement line is the principal's
   call.
