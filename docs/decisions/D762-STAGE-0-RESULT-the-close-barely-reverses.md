# D762 STAGE 0 RESULT — the cash close barely reverses: NO REVERSAL on ES, NQ and RTY; YM reverses (ρ −0.084) but no more than at noon, and its fade grosses $1.50 against a $3.80 cost

*2026-10-02. Prop book.*
- *Pre-registration: [D762](D762-STAGE-0-PRE-REG-does-the-cash-close-reverse.md) (`02a6afce`).*
- *Fixture builder: `d9a58134`. The fixture and the runner (`scripts/stage0_d762_cash_close.py`) were committed before
  the one run (`72003c0c`).*
- *Output: `data/stage0_d762_cash_close.json`. Wall 25 s.*
- *Checks: the lag audit (a raw-row loop on 40 sessions per root) passed; the rotation's offset 0 reproduced ρ. Nothing
  dated 2024-01-01 or later was decoded or read.*

## 0. The fixture

`fut_index_close_1m`: 342,270 one-minute bars, 15:30–16:14 ET, built in 115 s from 11 archive files covering
2016–2023 only.

| root | sessions | V1 overlap identity | V2 post-close coverage |
|---|---:|---:|---:|
| ES | 1,997 | 1.000 (59,910 bars) | 1.000 |
| NQ | 1,997 | 1.000 | 1.000 |
| YM | 1,995 | 1.000 | 1.000 |
| RTY | 1,618 (from 2017-07-10) | 1.000 | 1.000 |

**All pass.**

## 1. The readings

x is the pressure (P₁₆:₀₀ − P₁₅:₅₀) and y the response (P₁₆:₁₀ − P₁₆:₀₀). Eligible sessions: ES 1,941, NQ 1,941,
YM 1,938, RTY 1,557.

| root | C1 sd(y) per micro | C2 ρ(x, y) (rotation p05 / p50 / p95; Holm p) | C3 margin against 15:00 / 12:00 (SE) | C4 top-third fade gross (t) against cost | reading |
|---|---:|---|---|---|---|
| ES | $18.95 | −0.021 (−0.037 / +0.000 / +0.037; 0.42) | −0.078 (0.036) pass / +0.051 (0.036) unres. | +$0.54 (0.58) against $4.42 | **NO REVERSAL** |
| NQ | $37.10 | −0.003 (−0.038 / +0.000 / +0.038; 0.45) | −0.070 (0.036) unres. / +0.059 (0.035) unres. | +$0.31 (0.20) against $4.07 | **NO REVERSAL** |
| **YM** | $13.31 | **−0.084** (−0.038 / −0.000 / +0.037; **0.002**) | **−0.133 (0.037) pass** / −0.048 (0.036) unres. | +$1.50 (2.10) against $3.80 | **UNRESOLVED** |
| RTY | $11.96 | −0.027 (−0.043 / −0.000 / +0.041; 0.42) | −0.100 (0.040) pass / +0.018 (0.039) unres. | +$0.97 (1.50) against $3.76 | **NO REVERSAL** |

**C3's verdicts** follow D373's rule: a margin beyond −2 SE passes, beyond +2 SE fails, and anything between is
UNRESOLVED.

**The placebos tell the story:**
- **At 15:00, the ten-minute move continues on every root:** ρ +0.049 to +0.072.
- **At noon, it reverses on every root:** ρ −0.036 to −0.072.
- **The close sits between them.** On ES, NQ and RTY its ρ is smaller in size than noon's.
- **YM is the one root where the close reverses beyond its rotation.** It reverses more than at 15:00, but by less
  than 2 SE more than at noon. So it cannot be told apart from the generic midday ten-minute reversal (D499).

## 2. The C4 fades (one micro; walk-forward top third of \|x\|; four groups)

| root | trades | net mean (median) | gross mean (median) | win | skew | daily net Sharpe (Sortino) | gross Sharpe (Sortino) | max DD | +1 tick |
|---|---:|---|---|---:|---:|---|---|---:|---:|
| ES | 648 | −$3.88 (−$4.42) | +$0.54 ($0.00) | 37.2% | −0.75 | −1.61 (−1.99) | 0.22 (0.31) | $2,554 | −$5.13 |
| NQ | 652 | −$3.76 (−$3.82) | +$0.31 (+$0.25) | 39.7% | −0.28 | −0.93 (−1.24) | 0.08 (0.11) | $2,550 | −$4.26 |
| YM | 610 | −$2.30 (−$2.30) | +$1.50 (+$1.50) | 41.3% | −1.20 | −1.23 (−1.54) | 0.81 (1.15) | $1,500 | −$2.80 |
| RTY | 445 | −$2.79 (−$2.76) | +$0.97 (+$1.00) | 37.8% | −0.32 | −1.87 (−2.28) | 0.66 (0.96) | $1,245 | −$3.29 |

- **Break-even cost:** the gross mean ($0.31–1.50 a round trip), against $3.76–4.42.
- **The symmetric trims** do not change the sign anywhere (YM: ex-top −$2.90, ex-bottom −$1.51, both −$2.11).
- **Every year is negative** except ES 2021, NQ 2021 and YM 2022. RTY has no positive year.
- **ρ of the daily net with the ledger:** F2 +0.02 to +0.11, C1 and D737 within ±0.04.

**What the largest trades depend on: the window is also the earnings window (POST HOC).** NQ's best and worst fades
fall on megacap earnings evenings, with releases at 16:00:
- 2021-01-27 (+$296): Apple, Facebook, Tesla;
- 2021-07-27 (+$170): Apple, Microsoft, Alphabet;
- 2018-10-25 (−$208): Amazon, Alphabet;
- 2022-04-26 (−$357): Microsoft, Alphabet.

The largest post-close moves are news, not auction pressure.

## 3. Reported, not gating

**The longer pressure measures reverse more, and on every root:**

| root | ρ(x₃₀, y) (F2's window) | ρ(open → 16:00, y) |
|---|---:|---:|
| ES | −0.077 | −0.107 |
| NQ | −0.041 | −0.065 |
| YM | −0.139 | −0.111 |
| RTY | −0.080 | −0.072 |

These were declared as reported, not gating. Picking one now would be selection. The size bounds them anyway: at
ρ ≈ −0.1 and sd(y) of $12–19, a fade grosses about $1–2 against about $4.

**Heavy-auction days** (ρ, n):

| | ES | NQ | YM | RTY |
|---|---|---|---|---|
| quarterly-expiry Fridays | −0.03 (32) | −0.02 (32) | +0.01 (32) | **−0.32 (26)** |
| month-ends | −0.00 (95) | −0.01 (95) | −0.09 (95) | +0.04 (77) |
| Russell reconstitution | −0.25 (8) | −0.48 (8) | −0.45 (8) | −0.37 (6) |

- **The reconstitution day reverses on all four roots.** Its all-day fade grosses +$5 to +$13. But it is **one day a
  year (n 6–8)**: not a strategy, and too few to test.
- **Month-ends show nothing.** Quarterly expiry shows something on RTY only.

**YM's ρ by year:** −0.35 (2016), −0.26 (2017), +0.07, −0.05, −0.02, −0.20, −0.11, −0.09 (2023). It is strongest in
the first two years, the fading shape of D685's month-end flow.

**The window's shape:** ρ(x, y at 16:05) and ρ(x, y at 16:15) look the same as at 16:10 (ES −0.011 / −0.025, YM
−0.075 / −0.078).

## 4. Predictions against outcomes

| | predicted | outcome |
|---|---|---|
| P1 | C2 passes on at least two roots (P 0.6) | **missed:** YM only |
| P2 | C3 UNRESOLVED or fails on most roots that pass C2 (P 0.5) | **held:** YM UNRESOLVED (noon) |
| P3 | C4 fails everywhere (P 0.7); RTY the likeliest exception | **held:** YM came closest (+$1.50 against $3.80), not RTY |
| | P(PREMISE HOLDS) ≈ 0.12 | none |

## 5. What it shows

- **The closing auction's final ten minutes do not reliably give back after 16:00.** On ES, NQ and RTY there is no
  reversal beyond chance. On YM it is real but no larger than noon's generic reversal.
- **The reversion that is there is about a tenth of the day's late move.** A fade inside the 16:00–16:10 window
  collects about $1–2 against about $4. **The window is too short for the prize, and the prop book's flat-by-16:10
  rule fixes its length.**
- **The post-close window is information-heavy:** megacap earnings land in it. That is a reason, not a fix.
- **F2 is not undone by the close** (ρ of the fade with F2 is +0.02 to +0.11). F2's late-day follow is not a
  temporary auction effect that gives back within ten minutes.

## 6. What follows

- **The cash-close premise does not hold for the prop book.** No root reads PREMISE HOLDS, and no trading
  pre-registration follows from this record.
- **Post hoc, recorded, not leads for the prop book:**
  - the Russell reconstitution day (one a year);
  - the longer-pressure reversal (ρ about −0.1, about $1–2 gross);
  - YM's early-sample strength.
- **The fixture `fut_index_close_1m` stays** (15:30–16:14, 2016–2023, validated) for any later post-close question.
- **The other scheduled-flow candidates from the reasoning** remain untested: the FOMC overshoot and expiry-day hedging.
  They are for the principal to choose.
