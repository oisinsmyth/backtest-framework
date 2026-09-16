# D234 — the percentage activation threshold

**STAGE 1 — SCREEN. Not a verdict.** The mined fixture cannot detect a subtle success. The holdout is untouched.

*seed 0, 1,000 rotations, 21.7s. 57 symbols, 2018-12-21 to 2024-12-30, 1,515 live bars. rf = 4% on the exposed fraction.*

## Baseline

| book | excess Sharpe | CAGR | vol | money | max DD | exposure |
|---|---:|---:|---:|---:|---:|---:|
| **I1L — the baseline** | +0.564 | 7.08% | 8.7% | +50.85% | -11.67% | 49.3% |
| I1 published (continuity) | +0.570 | 7.23% | 8.8% | +52.12% | -11.78% | 49.9% |
| buy and hold | +0.235 | 8.42% | 17.7% | +62.59% | -34.60% | 100.0% |

## The ladder

`√f predicts` is what the cell scores from trading less **alone**. `selection` is what it earned above that.

| c | exposure | excess Sharpe | √f predicts | **selection** | Δ baseline | money | min ent/sym | rotation |
|---|---:|---:|---:|---:|---:|---:|---:|:--:|
| **md_L>0.00%** | 30.4% | +0.062 | +0.443 | **-86%** | -0.502 | +9.47% | 16 ✗ | — |
| **md_L>0.25%** | 29.0% | +0.036 | +0.433 | **-92%** | -0.527 | +8.24% | 11 ✗ | — |
| **md_L>0.50%** | 27.5% | +0.048 | +0.421 | **-89%** | -0.515 | +8.18% | 6 ✗ | — |
| **md_L>0.75%** | 26.0% | +0.014 | +0.409 | **-97%** | -0.550 | +6.72% | 3 ✗ | — |
| **md_L>1.00%** | 24.5% | -0.042 | +0.397 | **-110%** | -0.605 | +4.77% | 1 ✗ | — |

*`✗` marks hurdle E failing on its per-symbol leg — known and stated before the run. Every cell is underpowered per symbol by construction.*

## W3 — does the level rung carry information?

The sharp test. If `md_L`'s level carries information, a higher bar should mean better trades and selection quality should **rise** with `c`. If it is noise, flat or falling.

- slope: **-21.6% of selection quality per 1% of threshold**
- correlation across the ladder: **-0.880**
- monotone increasing: **no**

## Hurdle B — best-of-search rotation null

Best real **-0.502** against a null p95 of **-0.019** (p50 -0.260). **FAILS.**

