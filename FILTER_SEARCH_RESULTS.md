# D228 — the filter search, with the selection bias measured

*Produced by `scripts/run_filter_search.py` (seed 0, 1,000 null replications, 73.5s). 2018-12-21 to 2024-12-30, 1,515 live bars. rf = 4%, charged on the exposed fraction.*

## The baseline

| book | excess Sharpe | Sharpe (rf=0) | CAGR | total | max DD | exposure |
|---|---:|---:|---:|---:|---:|---:|
| **parent (I1 accel)** | **+0.570** | +0.793 | 7.23% | +52.12% | -11.78% | 49.9% |
| buy and hold | +0.235 | +0.457 | 8.42% | +62.59% | -34.81% | 100.0% |

## The eight candidates

| | excess Sharpe | delta | money | delta | exposure | entries | P | E |
|---|---:|---:|---:|---:|---:|---:|:--:|:--:|
| **G1** | +0.399 | -0.171 | +16.39% | -35.73 pp | 24.0% | 1,334 |  |  |
| **G2** | +0.089 | -0.481 | +8.24% | -43.88 pp | 25.4% | 1,458 |  |  |
| **S1** | +0.594 | +0.023 | +43.42% | -8.70 pp | 43.1% | 12,585 |  | PASS |
| **S2** | +0.551 | -0.019 | +40.14% | -11.97 pp | 37.6% | 11,748 |  | PASS |
| **S3** | +0.459 | -0.111 | +31.72% | -20.40 pp | 42.8% | 2,418 |  | PASS |
| **S4** | +0.570 | +0.000 | +23.34% | -28.78 pp | 25.0% | 2,418 |  | PASS |
| **S5** | +0.466 | -0.104 | +61.00% | +8.88 pp | 66.9% | 20,447 |  | PASS |
| **R1** | +0.333 | -0.238 | +55.32% | +3.20 pp | 100.0% | 3,002 |  | PASS |

## Hurdle B — the best-of-search null

Seven candidates rotated together, 1,000 replications. R1 is excluded: its signal is the parent's own flat mask, so there is nothing to rotate.

| | best real | null p50 | **null p95** | clears |
|---|---:|---:|---:|:--:|
| excess Sharpe | **+0.023** | +0.014 | **+0.104** | FAIL |
| money | **-8.70 pp** | -1.95 pp | **+6.55 pp** | FAIL |

**Best candidate: S1. Hurdle B: FAILS.**

### Selection bias, measured

| | p95 of delta |
|---|---:|
| G1 alone | +0.065 |
| G2 alone | +0.069 |
| S1 alone | +0.022 |
| S2 alone | -0.005 |
| S3 alone | -0.003 |
| S4 alone | +0.001 |
| S5 alone | +0.068 |
| **best of seven** | **+0.104** |

## The mechanism, tested across the eight

D228 Part 1 claims the arm's money gap against buy-and-hold *is* its exposure gap. Across candidates spanning 24% to 100% exposure, money delta against exposure delta gives **r = +0.823**, slope **0.58 pp of money per pp of exposure**.

## The analytic floor, for comparison

| count | N | floor |
|---|---:|---:|
| fresh | 8 | +0.099 |
| with_inherited | 70 | +0.164 |
| verdict_count | 45,811 | +0.287 |

