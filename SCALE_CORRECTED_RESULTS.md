# D232 — the scale-corrected Impulse MACD

**STAGE 1 — SCREEN. Not a verdict.** The mined fixture cannot detect a subtle success; this establishes whether the corrected signal is a better baseline.

*seed 0, 1,000 bootstrap replications, 6.0s. 57 symbols, 2018-12-21 to 2024-12-30, 1,515 live bars.*

## The three rungs, long-flat, no gate

| rung | Sharpe | excess @rf=4% | CAGR | money | max DD | exposure | turnover |
|---|---:|---:|---:|---:|---:|---:|---:|
| I1 published | +0.658 | +0.570 | 7.23% | +52.12% | -11.78% | 49.9% | 4,835 |
| **I1r ratio** | +0.610 | +0.524 | 6.60% | +46.85% | -12.49% | 48.9% | 4,865 |
| **I1L log** | +0.652 | +0.565 | 7.09% | +50.95% | -11.67% | 49.3% | 4,871 |
| buy and hold | +0.333 | +0.235 | 8.42% | +62.59% | -34.81% | 100.0% | — |

## Hurdle A — the paired deltas

| comparison | book | gate | Δ Sharpe | Δ excess | boot p05 | boot p95 | A |
|---|---|---|---:|---:|---:|---:|:--:|
| `I1r_ratio` | long_flat | none | **-0.047** | -0.047 | -0.105 | +0.008 | — |
| `I1r_ratio` | long_flat | 200ma | **-0.001** | -0.000 | -0.055 | +0.044 | — |
| `I1r_ratio` | long_short | none | **-0.079** | -0.076 | -0.164 | -0.002 | — |
| `I1r_ratio` | long_short | 200ma | **-0.050** | -0.047 | -0.105 | -0.002 | — |
| `I1L_log` | long_flat | none | **-0.006** | -0.005 | -0.051 | +0.033 | — |
| `I1L_log` | long_flat | 200ma | **+0.032** | +0.033 | -0.012 | +0.072 | — |
| `I1L_log` | long_short | none | **-0.003** | -0.002 | -0.055 | +0.047 | — |
| `I1L_log` | long_short | 200ma | **+0.011** | +0.012 | -0.019 | +0.052 | — |
| `I1L_minus_I1r` | long_flat | none | **+0.041** | +0.042 | -0.020 | +0.103 | — |
| `I1L_minus_I1r` | long_flat | 200ma | **+0.033** | +0.033 | -0.008 | +0.080 | — |
| `I1L_minus_I1r` | long_short | none | **+0.076** | +0.074 | -0.002 | +0.172 | — |
| `I1L_minus_I1r` | long_short | 200ma | **+0.060** | +0.059 | +0.013 | +0.129 | — |

## Z5 — the mechanism test

The defect scales with **level drift**, so the fix should help most where the price level moved most. A positive result with a null correlation here would mean the fix helped by accident.

| rung | corr(improvement, abs log drift) | mean per-symbol Δ | symbols improved |
|---|---:|---:|---:|
| `I1r_ratio` | **-0.156** | -0.0220 | 23 / 57 |
| `I1L_log` | **-0.111** | +0.0011 | 32 / 57 |

