# D235 — stops and targets on the recovery rule

**STAGE 1 — SCREEN. Not a verdict.** The holdout and the 2025–2026 forward window are untouched.

*seed 0, 1,000 rotations, 30.8s. 57 symbols, 2018-12-21 to 2024-12-30, 1,515 live bars. All exits close-to-close, effective the following bar.*

## Baseline

| book | excess Sharpe | CAGR | vol | money | max DD | exposure |
|---|---:|---:|---:|---:|---:|---:|
| **recovery — the baseline** | +0.746 | 5.43% | 6.1% | +37.39% | -10.30% | 18.9% |
| buy and hold | +0.235 | 8.42% | 17.7% | +62.59% | -34.60% | 100.0% |

## The seven cells

| cell | exposure | excess Sharpe | √f predicts | selection | Δ baseline | money | rotation |
|---|---:|---:|---:|---:|---:|---:|:--:|
| **BE@3%** | 17.5% | +0.794 | +0.719 | +10% | +0.047 | +33.22% | **PASS** |
| **BE@6%** | 18.4% | +0.747 | +0.737 | +1% | +0.001 | +34.62% | **PASS** |
| **PT@3%** | 14.7% | +0.767 | +0.659 | +16% | +0.021 | +26.07% | **PASS** |
| **PT@6%** | 16.6% | +0.748 | +0.700 | +7% | +0.002 | +29.45% | **PASS** |
| **DT@0.5%** | 20.0% | +0.764 | +0.769 | -1% | +0.018 | +39.35% | **PASS** |
| **DT@1.0%** | 21.1% | +0.772 | +0.790 | -2% | +0.025 | +40.72% | **PASS** |
| **DT@2.0%** | 22.9% | +0.781 | +0.821 | -5% | +0.035 | +42.97% | **PASS** |

## V2 — the mechanism test

`BE` is the only variant that neither cuts the entry dip nor caps the tail. If it does *not* do least harm, then "stops fail because they cut the entry dip" is the wrong explanation.

| family | mean Δ | best Δ |
|---|---:|---:|
| **BE** | +0.024 | +0.047 |
| **PT** | +0.011 | +0.021 |
| **DT** | +0.026 | +0.035 |

## Hurdle B

Best real **+0.047** against a null p95 of **-0.284**. **CLEARS.**

