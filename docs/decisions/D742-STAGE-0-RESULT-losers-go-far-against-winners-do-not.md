# D742 STAGE 0 RESULT (step 1) — the floored follow's losers go well against it and its winners do not (median adverse excursion 1.05 σ_rem against 0.27); a volatility-scaled stop cuts the drawdown and the worst day at every width, but the curve is not smooth; no width is chosen

*2026-10-01.*
- *Pre-registration: [D742](D742-STAGE-0-PRE-REG-a-protective-stop-for-the-floored-follow.md) (cf3bb9d3).*
- *Runner: `scripts/stage0_d742_stop_oracle.py` (26388d3d, with a canary fix committed before any output), one run.*
- *Output: `data/stage0_d742_stop_oracle.json`, aggregates only.*
- *In-sample ≤ 2023-12-29; D740's A: 546 trades, one MNQ, \$4.0671.*

## 0. The audits, and one deviation

**The checks that passed:**
- D727's lag audit (its canary fired) and the known answers to 1e-6; A's 546 trades reproduced.
- The unstopped exit reproduces the follow's gross on every trade.
- **The stop simulation equals D735's `e1_tables` convention** on a synthetic panel (w 0.5, 1.0 and none; long and
  short; gapped opens).
- **The real data:** 25 sampled stopped trades re-filled from the raw rows agree, and each loses before costs (sign).

**The deviation, disclosed.**
- **What failed:** §3's canary, a scan starting one bar early (at the entry bar), changed **no exit at any width** on
  real data, because no entry bar's own range reaches w σ_rem. The first run raised on it and wrote nothing.
- **What replaced it:** the count is recorded (0 at every width), and the decisive canary now scans from the session
  open, letting the pre-entry bars leak in. It changed **198 exits** at w 1.0.
- **When:** the fix was committed before the one run that wrote output. On synthetic data the one-bar canary fires.

## 1. The excursions (in σ_rem = σ_oc √((390 − m)/390) from the entry)

**The maximum adverse excursion (MAE)** to 15:59:

| | 10 % | 25 % | 50 % | 75 % | 90 % |
|---|---:|---:|---:|---:|---:|
| winners (308) | 0.03 | 0.11 | **0.27** | 0.52 | 0.86 |
| losers (238) | 0.41 | 0.65 | **1.05** | 1.54 | 2.01 |

**The share whose MAE reaches a given level:**

| level (σ_rem) | 0.25 | 0.5 | 0.75 | 1.0 | 1.5 | 2.0 |
|---|---:|---:|---:|---:|---:|---:|
| winners | 0.53 | 0.27 | 0.14 | **0.06** | **0.02** | 0.01 |
| losers | 0.96 | 0.84 | 0.68 | **0.54** | **0.27** | 0.11 |

- **The maximum favourable excursion mirrors this:** winners have a median of 1.03, losers 0.28.
- **When the losers are worst:** 47 % reach their worst point in the last hour.
- **The worst 5 % of trades** (27): they average −\$662, with a median MAE of 2.02 σ_rem; 37 % were already ≤ −1 σ_rem
  by noon.

**The ceilings:**
- the losing trades lose \$48,909 in all, and the worst 20 lose \$14,534;
- the perfect exit (every loser flat at the cost) would net \$63,692, with a max DD of \$24. Hindsight, a ceiling only.

## 2. The stop curve (descriptive, not a test)

| stop | stopped (winners / losers) | total | net / trade (median) | gross / trade | Sharpe (Sortino) | **max DD** | **Calmar** | **worst day** | longest drawdown | win rate | standard |
|---|---|---:|---|---:|---|---:|---:|---:|---:|---:|---|
| none (A) | 0 | \$15,751 | +\$28.85 (+\$40.93) | +\$32.91 | 0.87 (1.27) | \$4,131 | 3.81 | −\$1,142 | 162 | 0.56 | EARNS 6/6 |
| 0.5 σ_rem | 284 (83 / 201) | \$12,185 | +\$22.32 (**−\$79.64**) | +\$26.38 | 0.88 (**1.80**) | **\$1,737** | **7.02** | **−\$296** | 171 | **0.41** | EARNS 5/6 |
| 0.75 | 206 (43 / 163) | \$10,776 | +\$19.74 (−\$11.07) | +\$23.80 | 0.71 (1.22) | \$2,978 | 3.62 | −\$442 | 308 | 0.49 | EARNS 5/6 |
| **1.0** | 147 (18 / 129) | \$12,884 | +\$23.60 (+\$20.43) | +\$27.66 | 0.79 (1.28) | \$2,872 | 4.49 | −\$587 | 155 | 0.53 | EARNS 6/6 |
| 1.25 | 97 (10 / 87) | \$14,838 | +\$27.18 (+\$33.68) | +\$31.24 | 0.88 (1.38) | \$3,356 | 4.42 | −\$730 | 140 | 0.55 | EARNS 6/6 |
| **1.5** | 69 (5 / 64) | **\$16,206** | **+\$29.68** (+\$39.18) | +\$33.75 | **0.95 (1.46)** | \$3,231 | 5.02 | −\$875 | 162 | 0.55 | EARNS 6/6 |
| 2.0 | 28 (3 / 25) | \$15,334 | +\$28.08 (+\$40.68) | +\$32.15 | 0.87 (1.28) | \$3,971 | 3.86 | −\$995 | 161 | 0.56 | EARNS 6/6 |

**By year** (net \$):

| | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---:|---:|---:|---:|---:|---:|
| none | 1,257 | 450 | 1,858 | 3,487 | 6,325 | 2,374 |
| 0.5 | 1,074 | 480 | **−1** | 1,985 | 5,640 | 3,007 |
| 1.0 | 1,689 | 422 | 511 | 2,532 | 5,717 | 2,013 |
| 1.5 | 1,549 | 450 | 1,329 | 3,079 | 7,321 | 2,478 |

## 3. Predictions (D742 §4)

| # | prediction | outcome |
|---|---|---|
| 1 | the winners' median MAE < 0.5 σ_rem; the losers' > 0.8 | **Held** (0.27; 1.05) |
| 2 | a 1 σ_rem stop stops 20–35 % | **Held** (27 %) |
| 3 | some width cuts the max DD below \$3,000 with Calmar ≥ 3.81 | **Held** (0.5: \$1,737 / 7.02; 1.0: \$2,872 / 4.49) |
| 4 | the 0.5 stop lowers the mean by more than \$10 | **Failed** (−\$6.53) |
| 5 | every width ≤ 1.5 cuts the worst day by at least a third | **Failed at 1.5** (−\$875, a 23 % cut). It held at 0.5–1.25 |

## 4. What it says

1. **There is something real for a stop to use.** The losers go against the trade by about a σ_rem, and the winners
   rarely do: at 1 σ_rem the stop catches 54 % of the losers and 6 % of the winners.
2. **The widths trade off differently.**
   - **The worst day falls steadily** as the stop tightens: −\$1,142 → −\$296.
   - **The max DD and Calmar are not monotone** in w. 0.75 is worse than 1.0 and 1.5. These are single-path statistics,
     so choosing the best of six from this table is selection.
   - **0.5 σ_rem** has the best Calmar (7.02) and Sortino (1.80), but its median trade is −\$79.64 at a 41 % win rate: a
     different book, which lives on fewer, larger winners. It also turns 2020 flat.
   - **1.0–1.5 σ_rem** keep the follow's shape (median +\$20 to +\$39, win rate 0.53–0.55), cut the worst day by 23–49 %
     and the max DD by 22–30 %.
   - **1.5 σ_rem raises the net** (\$16,206 against \$15,751) and the Sharpe (0.95).
3. **What step 3 must handle** (the principal's choice of width first, in step 2):
   - one width, declared;
   - **a null for an exit:** the same number of exits placed at random times on the same trades, or a paired block
     bootstrap of the Calmar and worst-day differences against no stop;
   - the halves of the sample read separately.
