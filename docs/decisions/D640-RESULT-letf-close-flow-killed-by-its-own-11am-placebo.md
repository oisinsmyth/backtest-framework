# D640 — RESULT: the LETF close-flow model is KILLED at Gate 1. NQ passes H1 at 14:30 and 15:00, but its own 11:00 placebo is significant too, and the slice no prior line read shows nothing

*2026-09-27. The principal: "run it". One run of `scripts/run_letf_close_flow.py` (committed `9418a06`) under D639
(`e95c0a9`) with LETF-A1..A8, POWER `81dc902`. In-sample 2016-01-04 → 2025-02-28; nothing on or after 2025-03-01 read.
Output: `data/letf/letf_close_flow_signal.json` (all numbers below), `data/letf/trials.csv` (71 configurations).
`--check` rebuilds it byte for byte. The deposit's write-up is `docs/results/LETF_CLOSE_FLOW_REPORT.md`.*

*After the run, the suite showed that `trials.csv` had been written in the deposit's own §7 columns, not D592's union
schema (`validation.programme.TrialsCsv`), which the programme trial counter pools. The 71 rows were converted, every
value asserted equal: `doc` and `family` ("LETF close flow H1") were added, and `reads_2024_plus` moved into `notes`.
The runner now writes through `TrialsCsv`. The results JSON is untouched. These 71 rows are the programme's first
`trials.csv` rows.*

## Verdict (D639 §4; deposit §11)

**GATE 1 FAILED → STOP.**
- H1 passes in two primary cells, **NQ 14:30 and NQ 15:00**.
- But **H4, the identical rule at 11:00 → 12:00, is significant on NQ (t = 2.08 against the |t| < 2 bar)**. The deposit's
  kill condition: *"H1 passes but H4 placebo is also significant → Kill. It's generic late-day momentum, not LETF flow."*
- No ES cell passes H1. Gates 2 and 3, the book frame and the walk-forward do not run.

The placebo's t is close to the line, and the rule is applied as registered. The decisive fact does not depend on it
anyway: **on 2024-01-02 → 2025-02-28, the slice no prior line had read (D639 §2), every NQ cell is flat or negative**.

## H1 and the model's own claim (LETF-A7), the six primary cells, k = 3

| cell | active days | mean s | cost | t (HAC) | Holm p | H1 | 2016–23 mean (t) | **2024+ mean (t), n** | β vs own prediction [90% CI] | A7 label (Holm) |
|---|---:|---:|---:|---:|---:|---|---|---|---|---|
| NQ 14:30 | 944 | +5.57 bp | 1.63 | 2.54 | 0.028 | **pass** | +7.13 (2.65) | **−0.17 (−0.07), 201** | 0.55 [0.19, 0.90] | AT (unadjusted p 0.018; Holm 0.077) |
| NQ 15:00 | 961 | +5.84 | 1.64 | 2.84 | 0.014 | **pass** | +7.20 (2.88) | **+0.89 (0.33), 206** | 0.57 [0.24, 0.90] | AT (unadjusted 0.015; Holm 0.077) |
| NQ 15:30 | 961 | +2.04 | 1.64 | 1.35 | 0.215 | fail | +3.05 (1.66) | **−1.78 (−0.99), 200** | 0.19 [−0.04, 0.43] | **BELOW the claim: a powered null** |
| ES 14:30 | 60 | +29.2 | 2.95 | 1.61 | 0.215 | fail | +29.2 (1.61) | none active | 1.83 [−0.04, 3.70] | AT |
| ES 15:00 | 69 | +25.3 | 2.90 | 1.57 | 0.215 | fail | +25.3 (1.57) | none active | 1.67 [−0.08, 3.43] | AT |
| ES 15:30 | 68 | +12.7 | 2.88 | 0.97 | 0.215 | fail | +12.7 (0.97) | none active | 0.82 [−0.57, 2.22] | AT |

**H4 (11:00 → 12:00, same rule):**
- NQ: 842 days, **+3.29 bp, t 2.08: significant**, β 0.35 against its own prediction.
- ES: 47 days, +16.8 bp, t 1.57: passes.

**Reading:**
- **In 2016–2023 the NQ signal moves the close about half as much as the model predicts** (β ≈ 0.55), and it moves the
  late morning too (β 0.35). That is the signature of return-of-day continuation, not of a close-specific flow.
- **2016–2023 is exactly where D530, D463 and D487 already located that continuation**: 2018 and 2022, a regime
  property.
- **Out of that window, in 2024–2025, the effect is zero** at all three NQ entry times.
- At 15:30, the clock of ledger components K2/K3, the move is **significantly below the model's own claim**: a powered
  null against the mechanism.

## Nulls (D639 §5: exact circular rotation, all T − 1 = 2,264 offsets, no sampling SE)

| cell | observed | null p50 | null p95 | rank |
|---|---:|---:|---:|---:|
| NQ 14:30 | +5.57 | +0.12 | +3.08 | 0.999 |
| NQ 15:00 | +5.84 | −0.08 | +2.43 | 1.000 |
| NQ 15:30 | +2.04 | −0.03 | +1.99 | 0.955 |
| ES 14:30 / 15:00 / 15:30 | +29.2 / +25.3 / +12.7 | ≈ 0 | +9.3 / +7.2 / +5.8 | 0.999 / 0.998 / 0.993 |

The rotation breaks the day pairing between the signal and the move, so it clears easily. What it cannot separate is
a flow effect from day-level momentum. That is H4's job, and H4 failed.

## Dose-response, AUM scaling, overnight (H2, H3 under LETF-A8, H5), reported for completeness

- **H2 (|q| quintiles, all days):**
  - NQ 14:30: 0.5, 0.0, 3.4, 3.8, 4.9 bp (ρ 0.90, one inversion; passes).
  - NQ 15:00: 1.8, −0.8, 0.5, 3.4, 9.1 (passes).
  - NQ 15:30 passes.
  - ES 14:30 and 15:00 fail; ES 15:30 passes.
  - Larger flow days move more, but larger |q| is larger |return-of-day|, the same confound H4 exposes.
- **H3 (yearly slope of the raw move on signed q, against mean L(L−1)A):** ρ between −0.33 and +0.15 in every cell, and no
  cell fails (permutation p 0.17–0.67). **The effect does not grow with LETF assets**, though the NDX set's L(L−1)A grew
  **elevenfold, $17bn (2016) → $192bn (2025)**, and the SPX set's doubled ($38bn → $81bn). A flow mechanism predicts
  that it should (deposit H3's built-in placebo).
- **H5 (close → next 09:45):**
  - NQ: −1.0 to −2.9 bp, a partial reversal.
  - ES: **−35 to −51 bp**. The large-move days that activate ES give back more than the close gained.

## Robustness (D639 §6), NQ primary cells

| | NQ 14:30 | NQ 15:00 | NQ 15:30 |
|---|---|---|---|
| k = 2 / k = 5 (mean bp, t) | 4.8, 2.56 / 7.1, 1.94 | 4.8, 2.79 / 8.5, 2.67 | 2.0, 1.56 / 3.8, 1.62 |
| without flagged days | 5.4, 2.40 | 5.3, 2.49 | 2.0, 1.23 |
| hold 5 / 15 / 30 / 60 min | 0.2 / 0.3 / 0.1 / 4.7 | 1.9 / 3.1 / 4.6 / 5.8 | 0.5 / −0.1 / 2.0 / 2.0 |
| cost ×2, mean net bp | +2.3 | +2.6 | −1.2 |

**ES:**
- **Direxion's quarterly-anchor stretch changes nothing**: no ES activation falls in 2017-11 → 2019-07.
- **At Direxion's AUM band edges** the active days move by at most 5 and every ES t stays below 2 (0.85–1.92).

## The four groups (CLAUDE.md), 1 micro, D639's cost (MNQ $4.07, MES $4.42 a round trip)

| | NQ 14:30 | NQ 15:00 | NQ 15:30 | ES 14:30 | ES 15:00 | ES 15:30 |
|---|---|---|---|---|---|---|
| trades | 944 | 961 | 961 | 60 | 69 | 68 |
| **Sharpe net / gross** (annualised by trades a year) | 0.49 / 0.74 | 0.73 / 1.04 | −0.08 / 0.32 | 1.07 / 1.20 | 1.11 / 1.27 | 0.48 / 0.66 |
| **Sortino net** | 0.73 | 1.10 | −0.11 | 1.79 | 1.92 | 0.79 |
| mean gross / net per trade | $11.95 / $7.88 | $13.77 / $9.70 | $3.27 / −$0.80 | $41.85 / $37.44 | $35.14 / $30.73 | $16.67 / $12.25 |
| breakeven round trip | $11.95 | $13.77 | $3.27 | $41.85 | $35.14 | $16.67 |
| max drawdown | −$4,474 | −$3,225 | −$5,262 | −$763 | −$511 | −$704 |
| median / win rate / skew | $8.25 / 0.53 / 0.31 | $9.50 / 0.55 / 0.21 | $2.50 / 0.51 / 0.17 | $38.12 / 0.60 / 0.26 | $23.75 / 0.59 / 0.55 | $3.12 / 0.53 / 0.59 |
| mean ex-top 1% / ex-bottom 1% / trimmed | 4.70 / 19.12 / 11.86 | 7.86 / 19.52 / 13.61 | −1.15 / 7.77 / 3.36 | 29.3 / 52.7 / 40.0 | 26.1 / 41.2 / 32.2 | 7.8 / 23.2 / 14.2 |

- **Mean vs median:** the NQ means sit above their medians, so the left tail is not doing the work. The ES cells rest
  on 60–69 trades over nine years, each an extreme-move day.
- **Dependence:** per-year means, flagged-day splits and price-level terciles are in the JSON. **The whole NQ result is
  2016–2023; 2024+ is flat.**
- **Nulls:** as above.

## Component line (CLAUDE.md; entered in `docs/COMPONENTS_PROP.md` as scored, not entered)

Daily net Sharpe over all calendar days, 1 micro, 2016-01 → 2025-02. Correlation with D466's committed series over
2016–2023 (K1 overnight C1; **K2/K3 the 15:30 → 16:00 momentum on NQ/ES**; K4 YM; K5/K6 gated C1):

| cell | net Sharpe (all days) | ρ K2 | ρ K3 | ρ K1 |
|---|---:|---:|---:|---:|
| NQ 14:30 | 0.49 | +0.52 | +0.44 | +0.06 |
| NQ 15:00 | 0.73 | +0.59 | +0.53 | +0.00 |
| **NQ 15:30** | −0.08 | **+0.83** | +0.68 | +0.02 |
| ES 14:30 / 15:00 / 15:30 | 0.50 / 0.52 / 0.23 | +0.32 / +0.35 / +0.39 | +0.34 / +0.39 / +0.43 | ≈ 0.1 |

**NQ 15:30 is K2** (ρ 0.83 > D639 §10's 0.7): the same construction, not a new component. NQ 14:30 and 15:00 share
half their variance with it.

## Audits (D639 §8; each proved to fire in `--selftest`)

- **Lag:** a second implementation of A[t−1], V, σ_d, r, Q, q, I, the activation and the direction, never calling
  `letf.model`, agrees on every signal day of every cell.
- **Money:** a favourable move pays, long and short, and the inverse fund's flow has the move's sign.
- **Right quantity:** all 36 roll days price t−1 in today's contract, and t−1's AUM differs from t's on all 2,265
  signal days.
- A `--dry-run` on synthetic prices ran every path before the one real run.

## What was learned

1. **The LETF reset flow is real; its predicted price effect is not visible beyond generic continuation.** This
   extends D530 with the model the deposit specifies: real AUM, volume normalisation, the impact gate and three entry
   times. It reaches the same place: direction is return-of-day momentum, which appears at 11:00 as well and vanished
   after 2023.
2. **The model's own claim is testable on NQ, and at 15:30 it fails**: a powered null (LETF-A7). At 14:30 and 15:00
   the move is about half the claim in 2016–2023 and nothing after.
3. **ES is untestable at this bar.** ES volume swamps the S&P funds' flow: 3% of days activate, and none after 2023.
4. **Deposit §14's v2 overlays** (vol-control, month-end, late-day conditioning) would rest on this v1 verdict. There is
   no v1 effect for them to overlay.

## Programme slot 1 RELEASED by the principal, 2026-09-30

*The principal: "Release 1 and 2".*

- **Slot 1** ("LETF close flow H1") is moved to `released` in `data/programme_registry.json` with its reason
  (`Registry.release`).
- **Why it is free:** the line was killed in-sample by its own 11am placebo (above) and never reached the vault, so
  no vault look is being given up.
- **This is the principal's override** of the deposit's never-retroactively default, as for H-O2 (D658). It
  applies to this family only, and the family can never be registered again.
