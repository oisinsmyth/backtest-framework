# D231 — the exposure dial

**STAGE 1 — SCREEN. This is not a test and carries no verdict.** Its job is to prove the dials land where declared and to drop catastrophic cells before the holdout is spent. Sharpes below are reported for completeness only.

*`scripts/run_exposure_dial.py --stage screen`, seed 0, 51.2s. `universe_daily_2015_2024_raw.csv.gz` — 57 symbols, 2018-12-21 to 2024-12-30, 1,515 live bars. rf = 4% on the exposed fraction.*

## Baseline

| book | excess Sharpe | CAGR | vol | money | max DD | exposure |
|---|---:|---:|---:|---:|---:|---:|
| **parent (50%)** | +0.570 | 7.23% | 8.8% | +52.12% | -11.78% | 49.9% |
| buy and hold | +0.235 | 8.42% | 17.7% | +62.59% | -34.60% | 100.0% |

## The dial

`√f predicts` is what the cell scores from trading less **alone**. `selection` is what it earned above that — the only part attributable to picking better trades.

| cell | exposure | excess Sharpe | √f predicts | **selection** | money | entries/sym | levered @ B&H vol |
|---|---:|---:|---:|---:|---:|---:|---:|
| **T@40%** | 39.3% | +0.560 | +0.506 | **+11%** | +42.53% | 32 | 13.92% |
| **T@30%** | 29.5% | +0.418 | +0.439 | **-5%** | +26.70% | 30 | 11.40% |
| **T@20%** | 19.9% | +0.261 | +0.360 | **-28%** | +14.02% | 23 | 8.61% |
| **T@10%** | 10.9% | +0.159 | +0.267 | **-40%** | +6.57% | 16 | 6.81% |
| **N@40%** | 39.9% | +0.430 | +0.510 | **-16%** | +29.77% | 36 | 11.61% |
| **N@30%** | 29.5% | +0.344 | +0.438 | **-21%** | +18.04% | 35 | 10.10% |
| **N@20%** | 20.6% | +0.310 | +0.367 | **-16%** | +11.75% | 26 | 9.48% |
| **N@10%** | 10.1% | +0.353 | +0.257 | **+37%** | +6.52% | 11 | 10.25% |

*Levered column is a monotone transform of excess Sharpe — it ranks cells identically and is not independent evidence. Buy-and-hold makes 8.42% at 17.7% vol for comparison.*

## Nulls — matched-count rotation

Each cell rotated against itself 1,000 times: same exposure, same turnover, same holding-period distribution, pointed at the wrong bars. A delta over this cannot be "you just traded less" — it is the √f confound measured rather than assumed. One offset vector shared across cells, so cross-cell correlation survives.

| cell | Δ vs parent | own-rotation p95 | beats own rotation |
|---|---:|---:|:--:|
| **T@40%** | -0.010 | -0.162 | **PASS** |
| **T@30%** | -0.153 | -0.122 | — |
| **T@20%** | -0.310 | -0.074 | — |
| **T@10%** | -0.411 | -0.003 | — |
| **N@40%** | -0.141 | -0.189 | **PASS** |
| **N@30%** | -0.226 | -0.162 | — |
| **N@20%** | -0.261 | -0.126 | — |
| **N@10%** | -0.217 | -0.042 | — |

**Best-of-search across all 8 cells: best real -0.010 against a null p95 of **+0.053** (p50 -0.265). Hurdle B: FAILS.**

*Hurdle B is reported here for information. **Stage 1 carries no verdict** — the mined fixture's detection floor makes a pass here uninformative, and only stage 2 decides.*

## Screen

Floor: selection quality ≥ -25%. **6 of 8 survive.**

- **survivors:** T@40%, T@30%, N@40%, N@30%, N@20%, N@10%
- **dropped:** T@20%, T@10%

