# D786 STAGE 0 RESULT: NO NOMINATION. The five filters read 0.016 to 0.058, every one fails G2, and the debate's rejections stand as measurements. Two unread inputs came in about 1.75 SE above the debate's derivation, and the tug-of-war score's passive book is the closest thing to a pass

*2026-10-03. One run of `scripts/stage0_d786_china_open_five_filters.py --run` (231 seconds).*
- **The order:** the [pre-registration](D786-STAGE-0-PRE-REG-five-china-open-filters-read-once.md) (`f4007711`) came
  before the runner (`e86dbb6b`), and the runner before its one run.
- **Output:** `data/stage0_d786_china_open_five_filters.json` (statistics only).

## 0. Checks

- **Right quantity, all reproduced exactly:**
  - the taker book is D767's MGC pool (1,697; +\$3.14 gross, t 2.49; −\$2.79 net);
  - the passive book is D770's (1,466 filled; +\$2.12; −\$0.92; cost \$3.033);
  - spearman(F3, gross) is −0.051523;
  - D765's ρ(g_US, y) is +0.052436 on n 1,657.
- **The builds match the debate's outcome-free profiles:**

  | | debate | here |
  |---|---|---|
  | R*'s split-half reliability | +0.465 | +0.465 |
  | R*'s year medians | 1.165 … 0.907 | identical |
  | ρ(dev, x) | +0.056 | +0.056 |
  | ρ(R_US, x) | +0.002 | +0.002 |
  | ρ(g_US, x) | −0.083 | −0.083 |
  | selected counts | 463 / 464 / 460 / 463 / 481 | the same |

- **The lag audit passed on every score:** 40 sampled sessions each, plus the walk-forward flags and candidate 3's
  chain on 40 SGE days.
- **The seal:** nothing on or after 2024-01-01 was read, and every loader raised on a planted 2024 row in the
  self-test.
- **The rotation enumerated all 1,696 offsets per score,** and offset 0 reproduced the observed values.

## 1. The gates (taker, the primary book)

| | ρ(S, gross) | rotation p50 / p95; rank | third: mean net, t | B1 / B2 (\$) | **reading** |
|---|---|---|---|---|---|
| **2** B-US (post hoc) | **+0.058** | +0.001 / +0.043; 0.984 | +\$2.00, 0.85 | 2.2 / +2 | BELOW THE BAR |
| **21** A-INVAUD (post hoc) | **+0.052** | +0.000 / +0.043; 0.978 | +\$2.17, 0.91 | 1.8 / +98 | BELOW THE BAR |
| **3** A-PREM | +0.043 | −0.003 / +0.035; 0.972 | −\$1.03, −0.48 | 2.0 / −1,965 | NO EFFECT |
| **95** A-CLIENTELE | +0.048 | +0.000 / +0.044; 0.968 | +\$1.64, 0.68 | 2.6 / +112 | NO EFFECT |
| **117** A-TRANSIENT | +0.016 | +0.001 / +0.042; 0.721 | −\$2.78, −1.27 | 2.6 / −1,608 | NO EFFECT |
| 95's London secondary | +0.007 | +0.000 / +0.045; 0.607 | −\$1.09, −0.49 | 1.6 / −749 | NO EFFECT |

- **Holm across the three unread candidates,** on the rotation p: 3 is 0.087, 95 is 0.087 and 117 is 0.280. None is at
  0.05.
- **No candidate nominates.** The season-free reading changes nothing, because G2 fails everywhere: the best taker t
  is 0.91.
- **The pre-registered predictions held:**
  - all five read NO EFFECT or BELOW THE BAR;
  - 2 and 21 reproduce, at +0.058 on 2's own pool (+0.052 published) and +0.0515;
  - 3, 95 and 117 read within ±0.05 of zero, and agree in sign with the derivation within 2 SE.

## 2. The passive book (secondary)

| | ρ (p95) | third: mean net, t | Sharpe / Sortino | profitable years | B2 | reading |
|---|---|---|---|---|---|---|
| 2 | +0.044 (+0.047) | +\$2.97, 1.13 | 0.43 / 0.66 | 5 of 7 | +\$102 | NO EFFECT |
| 21 | +0.043 (+0.044) | +\$3.07, 1.17 | 0.45 / 0.66 | 5 of 7 | +\$187 | NO EFFECT |
| 3 | **+0.052** (+0.039) | +\$0.71, 0.31 | 0.12 / 0.18 | 4 of 7 | −\$1,091 | BELOW THE BAR |
| **95** | **+0.056** (+0.049) | **+\$4.80, 1.81** | **0.69 / 1.02** | **7 of 7** | **+\$840** | **BELOW THE BAR** |
| 117 | +0.023 (+0.047) | −\$0.58, −0.24 | −0.09 / −0.13 | 4 of 7 | −\$808 | NO EFFECT |

- **Candidate 95's passive third is the closest thing to a pass the filter line has produced.**
  - 391 trades, +\$7.83 gross against a \$3.03 cost; net t 1.81 against G2's 2.
  - Its mean net is above every rotation of R_US but 0.6% (rank 0.994; p50 −\$0.34, p95 +\$3.23).
  - It earns in all seven selectable years (2017–2023) and outside Dec–Mar (+\$840).
  - Its trimmed means are +\$3.15 (ex-top 1%), +\$6.71 (ex-bottom 1%) and +\$5.06 (both); the median is +\$4.97.
  - Without its best year (2020), it nets +\$3.73.
- **It is not a nomination,** for three reasons:
  - the pre-registration gated the taker book and Holm on the taker p;
  - this is a secondary read (passive), with D770's caveat that adverse selection takes the best 8% of fills;
  - the taker book on the same selection reads NO EFFECT at +0.0475.

## 3. Measured against the debate's derivation

| | derived or published | measured | difference |
|---|---|---|---|
| 3 A-PREM | −0.003 (through x and g) | +0.043 | **+1.73 SE** |
| 95 A-CLIENTELE | +0.000 (through x and g) | +0.048 | **+1.76 SE** |
| 117 A-TRANSIENT | 0.01–0.04, argued as a modulator | +0.016 | inside |
| 2 B-US | +0.052 published | +0.058 on its own pool | +0.2 SE |
| 21 A-INVAUD | +0.0515 published | +0.0515 | 0 |

- **Neither unread signed input crossed the pre-declared 2-SE line.** But both came in on the same side, at about 1.75
  SE.
  - The debate's no-direct-path derivation put them at zero; each measured near the 0.05 screen.
  - Pooling the two is a reading made after seeing, and is not gated.
- **So the screen's assumption is not refuted, but it is not reliable to the precision it was used at.** "Argued 0.00"
  for an input orthogonal to x and g meant ±0.05 in practice. Inputs the debate argued out at 0.00–0.02 could sit
  anywhere up to the screen.
  - That does not reopen any verdict: the binding bar was G2, and nothing here reaches it.

## 4. Splits (taker ρ; reported, not gated)

| | EST / EDT | Dec–Mar / Apr–Nov | years 2017 → 2023 | after the SHFE auction (≈130) |
|---|---|---|---|---|
| 2 | 0.077 / 0.051 | 0.046 / 0.069 | **all 7 positive**: 0.118, 0.043, 0.082, 0.028, 0.055, 0.097, 0.037 | 0.087 |
| 21 | 0.032 / 0.062 | 0.039 / 0.058 | −0.064, −0.112, 0.147, 0.051, 0.126, 0.041, 0.105 | 0.089 |
| 3 | **0.108 / 0.017** | **0.090 / 0.027** | 0.064, −0.033, 0.049, −0.061, **0.216**, 0.091, −0.007 | 0.026 |
| 95 | 0.054 / 0.044 | 0.034 / 0.051 | 0.097, 0.047, 0.075, 0.034, 0.091, −0.019, 0.075 (6 of 7) | −0.008 |
| 117 | −0.007 / 0.032 | 0.030 / 0.016 | 0.126, 0.092, 0.040, −0.143, −0.099, 0.077, 0.071 | 0.073 |

- **The US afternoon's continuation (2) is positive in every year and leans out of season.** That was the split the
  debate said would move both agents. Its accuracy is published (post hoc), so it cannot nominate. Its third still
  fails G2 (t 0.85 taker, 1.13 passive).
- **The tug-of-war score (95) is positive in 6 of 7 years and season-neutral.**
- **The onshore premium (3) is a winter and 2021 effect:** EST 0.108 against EDT 0.017, and 2021 at 0.216. This is
  B2's failure seen directly. Its book loses \$1,965 outside Dec–Mar.
- **R\* (117), the debate's best-built profile, carries nothing:** 0.016, with signs flipping by year.
- **An observation, not a finding:** 2 and 95 point in opposite directions from adjacent Western windows.
  - The US afternoon after COMEX's 13:30 settlement (g_US) continues into y.
  - The US day session before it (R_US, 08:20–13:30 ET) reverses into y.
  - They are nearly orthogonal (ρ(R_US, g) −0.009). A combination of the two was not pre-registered here, and choosing
    it now would be selection after seeing.

## 5. The four groups, on the taker third

| | 2 | 21 | 3 | 95 | 117 |
|---|---|---|---|---|---|
| trades (a year) | 463 (68) | 481 (71) | 464 (68) | 460 (68) | 463 (68) |
| gross / net mean; t net | +7.93 / +2.00; 0.85 | +8.10 / +2.17; 0.91 | +4.90 / −1.03; −0.48 | +7.57 / +1.64; 0.68 | +3.15 / −2.78; −1.27 |
| median; win rate; payoff | +3.07; 53.1%; 0.99 | +3.07; 52.8%; 1.01 | −1.43; 49.1%; 0.97 | +3.07; 54.1%; 0.93 | −0.93; 49.5%; 0.87 |
| skew; excess kurtosis | +0.45; 5.0 | −0.18; 4.0 | +0.70; 5.0 | −0.33; 3.5 | −0.22; 1.8 |
| trimmed means: ex-top / ex-bottom / both | −0.04 / +3.73 / +1.69 | +0.32 / +4.19 / +2.35 | −3.08 / +0.41 / −1.64 | −0.03 / +3.60 / +1.94 | −4.41 / −0.96 / −2.59 |
| net Sharpe / Sortino (gross Sharpe) | 0.33 / 0.49 (1.29) | 0.35 / 0.50 (1.30) | −0.18 / −0.27 (0.87) | 0.26 / 0.37 (1.21) | −0.49 / −0.65 (0.55) |
| max drawdown; total net | \$683; +\$926 | \$1,108; +\$1,043 | \$1,595; −\$479 | \$716; +\$752 | \$2,429; −\$1,287 |
| breakeven cost a round trip | \$7.93 | \$8.10 | \$4.90 | \$7.57 | \$3.15 |
| profitable years; net without the best | 4 of 7; +\$1.04 | 4 of 7; +\$0.20 | 2 of 7; −\$3.45 | 4 of 7; +\$0.71 | 3 of 7; −\$4.28 |
| largest trade | 2022-03-08 +\$337 | 2020-03-09 −\$302 | 2022-02-24 +\$289 | 2020-03-09 −\$302 | 2020-03-18 −\$207 |
| third's mean net against its rotation (p50 / p95; rank) | −2.28 / +0.90; 0.982 | −2.34 / +0.76; 0.992 | −2.22 / +0.84; 0.741 | −2.32 / +1.03; 0.979 | −2.27 / +0.89; 0.397 |

- **2, 21 and 95 beat their own rotations on the third's mean net** (ranks 0.98–0.99). The inputs carry a selection
  effect, but at micro taker cost it is worth \$2 a trade at t below 1.
- **A mean below its median** on 2 and 95 (+2.00 against +3.07; +1.64 against +3.07) says the left tail does part of
  the work: 2020-03 is in the worst five of every book.

## 6. The component line (taker third, daily ρ)

| | the unfiltered D765 MGC fade | D775 | D777's MNQ book |
|---|---|---|---|
| 2 | 0.511 | 0.030 | 0.012 |
| 21 | 0.538 | 0.023 | 0.025 |
| 3 | 0.469 | 0.008 | 0.021 |
| 95 | 0.515 | 0.012 | 0.028 |
| 117 | 0.472 | 0.005 | −0.012 |

- **Each is a gated subset of the base fade (ρ about 0.5),** and is unrelated to the two index lines that could be
  rebuilt.
- **Not computed:** the D755 other-lines file (`temp/d755_other_lines.csv`) no longer exists.
- **No row is entered in `docs/COMPONENTS_PROP.md`:** net Sharpe is at most 0.35 taker, below C-a's 0.5. D765, D767
  and D770 were not entered either.

## 7. What this decides

- **No 2024+ confirmation is recommended.** Nothing nominated, so the sealed slice stays unspent.
- **The debate's 210 rejections stand,** now as measurements on the five where the argument carried the verdict.
  - The screen's derivation understated two orthogonal inputs by about 1.75 SE each.
  - The binding constraint was always G2, and no input reaches it at micro cost.
- **What is left on this fade's filter line:**
  - candidate 16 (SGE volume), which needs data;
  - a possible tug-of-war construction, 95 passive.
- **On the second, a new pre-registration would carry its selection plainly:** chosen after this read, on its passive
  book, with the 2024+ slice as its only clean test. It would face the SHFE auction change (95 reads −0.008 on the 132
  post-auction sessions here, too few to mean anything).
- **Whether to spend data on it is the principal's call.**
