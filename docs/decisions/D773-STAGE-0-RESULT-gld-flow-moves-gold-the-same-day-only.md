# D773 STAGE 0 RESULT — NO DIRECTION: GLD creations do coincide with rising gold (same-day ρ +0.126) and the flow persists (lag-1 +0.26), but yesterday's published flow says nothing about today's London morning (ρ +0.007, p 0.70); the expected-sign trade nets −$7.85 per MGC

*2026-10-02. Prop book.*
- *Pre-registration: [D773](D773-STAGE-0-PRE-REG-gld-flow-and-the-london-gold-morning.md) (`64658ab2`).*
- *Runner: `scripts/stage0_d773_gld_flow.py` (`0d143b78`).*
- *Output: `data/stage0_d773_gld_flow.json`. Extraction 4.6 minutes; run 3.3 seconds; one run.*

**The extraction's first launch failed for lack of memory.**
- A worker could not allocate 38 MB while the machine was under memory pressure from another process.
- Nothing had been computed. The same committed extraction was re-launched once memory was free (18 GB) and finished
  cleanly.
- No code changed.

**The checks:**
- **the lag audit:** a csv-module second implementation agreed on 40 days; it raises when the same day's holdings are
  used;
- **the clock:** 134 days on which London and New York daylight saving disagree;
- **units:** median GC close $1,480;
- **delivery:** the nearest front was 2 days from first notice;
- **the rotation's offset 0** reproduced ρ;
- **the seal:** nothing on or after 2024-01-01 read;
- **the extraction:** chunk == whole.

**The sessions:** 2,203 eligible trade dates, 2015-06-03 → 2023-12-29.
- Inflow 537, outflow 763, no change 903.
- The trade's walk-forward top third holds 638 days.

## 1. The reading

| | value |
|---|---|
| **G1: Spearman ρ(yesterday's flow, the 08:00 → 15:00 London move)** | **+0.007**; exact rotation p2.5 / p50 / p97.5 = −0.040 / +0.000 / +0.042; **p 0.698** |
| G2: the top-third trade, expected sign (long after inflows) | gross **−$1.92** (NW t −0.41, median +$1.00) against $5.93 |
| G3 | 3 of 8 full years positive; −$5,567 without the best year (2018) |
| **reading** | **NO DIRECTION** |

## 2. The mechanism is real, and it is contemporaneous

| | ρ |
|---|---|
| lag-1 autocorrelation of the daily flow (eligible days) | **+0.262** |
| yesterday's flow against today's flow | +0.271 |
| **today's flow against today's London morning** (diagnostic; it looks ahead and cannot be traded) | **+0.126** |
| yesterday's flow against today's London morning (G1) | +0.007 |
| yesterday's premium to NAV (the proxy D772 withdrew) | +0.025 |

- **Creation days are rising-gold days, at the same time.** The +0.126 is about 6 SE on 2,200 days. Investors buy GLD
  when gold rises, and the APs' bullion flow lands with it.
- **What persists is the investors' demand, not its price effect.** Yesterday's flow predicts about 7% of the variance
  of today's flow (ρ +0.27), so it carries about 0.27 × 0.126 ≈ 0.03 of today's ρ. That is under the rotation's band.
  - The forced bullion buying is real.
  - It is small against gold's daily turnover.
  - What can be seen of it in advance is a fraction of a fraction.

**The other windows carry nothing either:**

| window | ρ | top-third gross |
|---|---|---|
| the auction (FIX ± 5 min) | −0.003 | +$0.36 |
| after the auction (FIX + 5 → + 30 min) | +0.039 | −$0.12 |
| the US morning (09:30 ET → the auction) | +0.010 | −$1.70 |

**The clock control:** on the 134 mismatch days, ρ is +0.001 on the London clock and −0.001 on a fixed 10:00 ET clock.

**By year:** ρ ranges −0.16 to +0.11.
- 2023 is the most negative (−0.156): GLD saw outflows while gold rose on central-bank buying.
- Quintiles of \|flow\| show no gradient.

## 3. The trade (one MGC, the top third of |flow|, expected sign; four groups)

| | value |
|---|---|
| trades | 638 of 2,203 days, 7 h each |
| gross mean (median) | −$1.92 (+$1.00) |
| **net mean (median)** | **−$7.85** (−$4.93); −$8.85 with one extra tick |
| win; payoff | 47%; 0.89 |
| skew / kurtosis | −1.20 / 12.4 |
| net trims: ex-top 1% / ex-bottom 1% / both | −11.59 / −3.00 / −6.72 |
| daily net Sharpe (Sortino); gross | −0.61 (−0.77); −0.15 (−0.19) |
| max drawdown; break-even cost | $6,143; none |
| inflow trades / outflow trades (gross) | −$4.11 (310) / +$0.14 (328) |
| best and worst trades | 2020-03-12 +$518, 2021-01-08 +$418; 2020-11-09 −$978 (the vaccine Monday), 2022-03-09 −$626 |
| ρ with D737 / F2 / C1 | −0.03 / +0.05 / +0.03 |

**The component line:** net Sharpe −0.61. Not a component.

## 4. Predictions against outcomes

| | predicted | outcome |
|---|---|---|
| P1 | NO DIRECTION (P 0.65) | **held:** p 0.70 |
| P2 | same-day ρ(flow, y) positive, p < 0.05 (P 0.6) | **held:** +0.126, about 6 SE (not rotation-tested; reported) |
| P3 | flow AR(1) between 0.15 and 0.30 (P 0.8) | **held:** +0.262 |
| | P(PREMISE HOLDS) ≈ 0.04 | NO DIRECTION |

## 5. What it shows

**The ETF flow is a forced flow, and it does show in the price, on the day it happens.**
- It cannot be traded from what is published beforehand. Yesterday's flow predicts too little of today's, and today's
  price effect is too small per unit of predictable flow.
- With D751 (the fix, price-only) and D772's withdrawn premium proxy, the London PM auction has now been tried with:
  - the price,
  - the ETF premium,
  - and the actual metal.

  None signs the move.

**What follows:**
- No trading pre-registration in-sample.
- **The principal's call:** close the GLD-flow construction.

## 6. CLOSED (2026-10-02)

**The principal: "Close that".**
- The GLD creation/redemption-flow construction is closed for the prop book.
- The fixture `gld_holdings_daily.csv` remains available.
- The gold line continues with a two-agent mechanism debate.
