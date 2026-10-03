# D787 DIAG RESULT — not a candidate by the declared rule (four of six books, not five, keep the sign without 2020/2022), but signal strength is the first trade-level sort that survives those years where it can: NQ F2 (a tier, so not the price level) and NG. It does nothing for the two books whose trigger is a crossing or a rank. D776's and L4's magnitudes are in index points, which carry the price level

*2026-10-03. One run of `scripts/diag_d787_signal_strength.py --run` (271 seconds).*
- **The order:** the [pre-registration](D787-DIAG-PRE-REG-signal-strength-against-its-own-gate.md) (`68f5742a`) came
  before the runner (`299d1260`).
- **Output:** `data/diag_d787_signal_strength.json`. Descriptive only.

## 0. Checks

- **Every known answer was reproduced first** (D737 1,699, NQ F2 274, C1 328, D776 186 / +\$34.88, L4 280 /
  +\$15.84, NG's D630 table).
- **Every trade sits past its gate as recorded:** D737's \|Z\| ≥ 1 at the trigger minute, C1's tier < 1/3, and L4's
  \|c\| ≥ its threshold.
- **The strength audit** recomputed 20 sampled trades per book by explicit loop over earlier trades only; all equal.
- **The self-test:**
  - a planted effect is a candidate; noise is not;
  - the audit raises on a strength that includes the current trade;
  - a calendar-concentrated weak half fails the calendar check.

## 1. Strong half against weak half (strength ≥ 0.5 against < 0.5), mean net per trade

| book | strong: n, mean | weak: n, mean | spread (z) | without 2020/2022: strong / weak (z) | weak half's largest year | ρ with NQ volatility |
|---|---|---|---|---|---|---|
| D737 | 851, +\$18.12 | 818, +\$11.76 | +\$6.36 (0.65) | +\$9.33 / +\$10.25 (−0.11) | 14% | −0.07 |
| **NQ F2** | 136, +\$31.83 | 108, +\$12.47 | +\$19.36 (1.13) | **+\$24.08 / −\$12.64 (2.04)** | 33% | +0.07 |
| C1 | 149, +\$17.02 | 149, +\$16.13 | +\$0.90 (0.06) | +\$11.74 / +\$16.23 (−0.31) | 22% | +0.10 |
| **D776** | 125, +\$46.56 | 31, +\$1.17 | **+\$45.39 (2.08)** | **+\$50.24 / −\$3.09 (2.29)** | 32% | +0.07 |
| L4 | 194, +\$16.84 | 56, +\$1.95 | +\$14.89 (1.09) | +\$20.20 / +\$3.68 (1.08) | 38% | +0.34 |
| **NG** | 521, +\$6.63 | 219, −\$6.71 | **+\$13.34 (4.85)** | **+\$2.20 / −\$8.03 (3.65)** | 48% | +0.26 |

- **The declared rule:**
  - over 2 SE in at least two books: met (D776, NG);
  - the same sign in all six with every year: met;
  - **without 2020/2022, positive in only four of six** (D737 −\$0.92, C1 −\$4.49): **not met;**
  - the calendar check: met (no year above 48% of the weak half).
  - **So it is not a candidate by the rule fixed beforehand.**
- **Strength is not volatility in disguise:** its correlation with the NQ volatility percentile is −0.07 to +0.34.
- **D737's earliness** (the second measure) gives nothing either: z 0.01, and −0.17 without 2020/2022.

## 2. What the pattern is

- **It sorts the books whose trigger is a size that feeds the payoff:**
  - **NQ F2's tier.** It is a rank of the late-day move, so it is free of the price level, and it survives without
    2020/2022: the weak half loses −\$12.64 a trade.
  - **NG's predicted flow \|I\|.** The bigger the forced flow, the bigger the reversion. The weak half loses
    −\$6.71 a trade.
  - **D776's impulse and L4's closing move.**
- **It does nothing for the two books whose trigger is not a size:**
  - **D737** fires at the first minute its spread crosses 1σ, so the overshoot at the crossing carries no
    information.
  - **C1's** strength is how compressed the day was, a rank of a quiet state, not the size of what it trades.
- **The caution: D776's \|x\| and L4's \|c\| are in index points, and points grow with the index's price.** The
  expanding percentile then calls later trades "strong", the same confound that undid family A (D786 A1/A2):
  - D776's weak half sits mostly in 2017–2020;
  - L4's sits in 2019 (38%) and 2023 (36%).
  - A price-neutral magnitude separates the two: \|x\| and \|c\| in units of each book's own trailing volatility.
  - **On the vault the point form would also degenerate:** at 2024–26 prices almost every trade would rank "strong"
    against 2016–2023 history.

## 3. Reading

- **Not a candidate by the declared rule.**
- **It is the first trade-level sort that survives without 2020/2022, in the books where it can apply:**
  - it holds in NQ F2 (price-free) and NG;
  - it is suggestive in D776 and L4, pending the price-neutral check;
  - it is absent where the trigger is a crossing or a rank (D737, C1).
- **As a principle it reads: trade only when the size that drives the payoff is large for this book, and do not
  apply it to triggers that are not sizes.** That is narrower than the general rule the principal asked for, and it
  is stated after the look.
- **The next design is the principal's:**
  - the price-neutral re-check for D776 and L4 (in-sample);
  - and whether a strength rule for the size-triggered books (NQ F2, D776, L4, NG) goes to the vault before the run.
