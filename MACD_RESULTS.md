# MACD RESULTS — the crossover ladder (D217)

The results ledger for D217. **Append-only.** Every work package adds a dated
section; nothing above is rewritten. This document carries the multiplicity count
that feeds the deflated Sharpe.

## Inherited disclosure

This study opens a **fresh ledger**, on the argument written into
[`D217`](docs/decisions/D217-the-macd-crossover-ladder.md): a different fixture (ETF
daily, not crypto 15m), a different claim family (directional single-name momentum,
not structure or terrain), and a sensor that did not exist in this repo. The
structure and terrain programmes' combined 395-look bar and the prior ETF-fixture
registries are disclosed adjacent and enter the third multiplicity count, which
carries the verdict.

## WP1-WP4 — the ladder, the sweep and the verdict

**Produced:** 2026-08-24 · **Reproduce:** `uv run python scripts/run_macd_ladder.py` (offline, deterministic, seed 0)

Fixture: `universe_daily_2015_2024_raw.csv.gz` — 57 ETFs, 2515 daily bars each. Warm-up burns 393 bars (15.63% of the sample), so every arm starts on 2016-07-26 and runs to 2024-12-30 — 2122 live bars, the same bars for all three rungs.

### WP2 — the census and the arithmetic. Zero looks.

A census is not a test. Nothing here compares anything to anything.

| arm | changes/ETF (median) | entries/ETF (median) | min | ETFs under 30 | bars held | in market |
|---|---:|---:|---:|---:|---:|---:|
| `momentum` | 161 | 160 | 123 | 0 | 13.2 | 99.82% |
| `momentum_gated` | 229 | 120 | 88 | 0 | 9.3 | 73.91% |
| `signal_line` | 170 | 170 | 143 | 0 | 12.5 | 99.95% |
| `signal_line_gated` | 241 | 123 | 98 | 0 | 8.8 | 52.13% |
| `zero_line` | 74 | 74 | 52 | 0 | 28.7 | 99.95% |
| `zero_line_gated` | 147 | 76 | 44 | 0 | 14.4 | 74.10% |

**The cost, derived rather than chosen — and it depends on who is trading.**

At an institutional book ($10,000,000 split 57 ways) the IBKR per-order minimum does not bind and the median per-side cost is **1.82 bp** (max 3.95 bp), including a 1 bp half-spread.

At a retail book ($100,000 split 57 ways) the $1.00 minimum binds on **57 of 57** ETFs and the median per-side cost is **6.7 bp** — roughly 4x the institutional figure, for the identical trades.

Zero-line turnover is 8.8 position changes per year, so the annual cost drag is 0.32% institutional against 1.18% retail. Against a median annualised vol of 21.73% that is **0.015 of Sharpe institutional and 0.054 retail**.

### WP3 — the ladder. 12 looks.

| rung | book | gate | Sharpe | total | maxDD | turnover | rot. null mean | delta | pct | block delta | pct |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| signal_line | long_short | none | +0.312 | 40.52% | -20.48% | 19427 | -0.200 | +0.512 | 89 | +0.794 | 99 |
| signal_line | long_short | 200ma | +0.205 | 19.03% | -16.89% | 14046 | +0.222 | -0.017 | 53 | +0.139 | 74 |
| signal_line | long_flat | none | +0.496 | 41.25% | -13.55% | 9721 | +0.214 | +0.282 | 99 | +0.335 | 100 |
| signal_line | long_flat | 200ma | +0.288 | 11.04% | -7.16% | 8427 | +0.266 | +0.022 | 58 | +0.105 | 89 |
| zero_line | long_short | none | +0.026 | 2.87% | -19.48% | 8267 | +0.298 | -0.272 | 16 | -0.125 | 35 |
| zero_line | long_short | 200ma | +0.019 | 1.83% | -20.44% | 8491 | +0.370 | -0.351 | 5 | -0.264 | 8 |
| zero_line | long_flat | none | +0.286 | 20.85% | -13.18% | 4156 | +0.285 | +0.001 | 52 | +0.030 | 69 |
| zero_line | long_flat | 200ma | +0.194 | 10.48% | -13.96% | 4521 | +0.313 | -0.119 | 8 | -0.087 | 9 |
| momentum | long_short | none | -0.136 | -13.63% | -31.11% | 17919 | +0.188 | -0.325 | 17 | -0.144 | 26 |
| momentum | long_short | 200ma | -0.070 | -6.64% | -26.01% | 13312 | +0.312 | -0.382 | 3 | -0.309 | 6 |
| momentum | long_flat | none | +0.157 | 10.99% | -17.06% | 8975 | +0.262 | -0.104 | 5 | -0.073 | 10 |
| momentum | long_flat | 200ma | +0.117 | 6.14% | -14.49% | 7629 | +0.299 | -0.183 | 0 | -0.144 | 2 |

Buy-and-hold over the same bars, through the same cost path: **+0.266** Sharpe, 42.78% total, -35.13% max drawdown.

**The money, and the dividend adjustment.**

The fixture is split-adjusted and **dividend-unadjusted** (D75), so a price-only comparison silently favours a strategy that is out of the market part of the time over a benchmark that never is. The dividends are in the sidecar and in the same split-adjusted frame as the prices, so they are added back here: the ex-date dividend lands on its bar and is reinvested. **The position series is untouched** — MACD is computed on the price a trader sees, and rewriting the price to smuggle dividends into the SIGNAL would be a different indicator.

| rung | book | gate | price-only | +dividends | CAGR (price) | CAGR (+div) | exposure |
|---|---|---|---:|---:|---:|---:|---:|
| signal_line | long_short | none | 40.52% | 38.78% | 4.12% | 3.97% | 99.95% |
| signal_line | long_short | 200ma | 19.03% | 20.24% | 2.09% | 2.21% | 52.13% |
| signal_line | long_flat | none | 41.25% | 53.54% | 4.19% | 5.22% | 50.76% |
| signal_line | long_flat | 200ma | 11.04% | 17.22% | 1.25% | 1.91% | 33.01% |
| zero_line | long_short | none | 2.87% | 6.48% | 0.34% | 0.75% | 99.95% |
| zero_line | long_short | 200ma | 1.83% | 5.31% | 0.22% | 0.62% | 74.10% |
| zero_line | long_flat | none | 20.85% | 34.49% | 2.27% | 3.58% | 57.87% |
| zero_line | long_flat | 200ma | 10.48% | 19.81% | 1.19% | 2.17% | 47.55% |
| momentum | long_short | none | -13.63% | -11.64% | -1.73% | -1.46% | 99.82% |
| momentum | long_short | 200ma | -6.64% | -3.99% | -0.81% | -0.48% | 73.91% |
| momentum | long_flat | none | 10.99% | 22.76% | 1.25% | 2.46% | 57.12% |
| momentum | long_flat | 200ma | 6.14% | 14.63% | 0.71% | 1.64% | 47.10% |
| **buy-and-hold** | — | — | **42.78%** | **70.81%** | 4.32% | **6.56%** | 100.00% |

Dividends matched to bars: 2,285 (0 ex-dates fell past the last bar and are counted rather than dropped quietly).

**Hurdle A — the nested deltas. This is the study.**

| book | gate | R1 signal | R2 zero | R3 momentum | R1-R2 | R2-R3 | R1 turnover / R2 |
|---|---|---:|---:|---:|---:|---:|---:|
| long_short | none | +0.312 | +0.026 | -0.136 | **+0.285** | **+0.163** | 2.35x |
| long_short | 200ma | +0.205 | +0.019 | -0.070 | **+0.186** | **+0.089** | 1.65x |
| long_flat | none | +0.496 | +0.286 | +0.157 | **+0.209** | **+0.129** | 2.34x |
| long_flat | 200ma | +0.288 | +0.194 | +0.117 | **+0.093** | **+0.078** | 1.86x |

The hurdle is +0.10 Sharpe, above the null's p95.

**The fill-timing bracket — the first thing to check, because this returned a positive.** The record pre-registered a next-open fill. A close-to-close position series cannot express one, so the primary above charges the arm as if it filled at the close that produced its signal, which is one bar MORE favourable than what was pre-registered. The table below re-runs every cell with a full extra bar of lag, which is strictly LESS favourable. The true next-open number lies between them. This is a sensitivity on the same 12 cells, not 12 further looks.

| book | gate | R1-R2 lag 1 | R1-R2 lag 2 | R2-R3 lag 1 | R2-R3 lag 2 |
|---|---|---:|---:|---:|---:|
| long_short | none | +0.285 | +0.247 | +0.163 | +0.042 |
| long_short | 200ma | +0.186 | +0.157 | +0.089 | +0.022 |
| long_flat | none | +0.209 | +0.183 | +0.129 | +0.033 |
| long_flat | 200ma | +0.093 | +0.028 | +0.078 | +0.022 |

| rung | book | gate | Sharpe lag 1 | Sharpe lag 2 | change |
|---|---|---|---:|---:|---:|
| signal_line | long_short | none | +0.312 | +0.225 | -0.086 |
| signal_line | long_short | 200ma | +0.205 | +0.133 | -0.072 |
| signal_line | long_flat | none | +0.496 | +0.425 | -0.071 |
| signal_line | long_flat | 200ma | +0.288 | +0.188 | -0.099 |
| zero_line | long_short | none | +0.026 | -0.022 | -0.048 |
| zero_line | long_short | 200ma | +0.019 | -0.024 | -0.042 |
| zero_line | long_flat | none | +0.286 | +0.242 | -0.044 |
| zero_line | long_flat | 200ma | +0.194 | +0.160 | -0.034 |
| momentum | long_short | none | -0.136 | -0.064 | +0.072 |
| momentum | long_short | 200ma | -0.070 | -0.046 | +0.024 |
| momentum | long_flat | none | +0.157 | +0.209 | +0.052 |
| momentum | long_flat | 200ma | +0.117 | +0.139 | +0.022 |

### WP4 — the declared sweep. 30 looks.

32 cells, grid fixed in D217 and not extended. Every cell reported.

| rank | rung | fast | slow | signal | Sharpe |
|---:|---|---:|---:|---:|---:|
| 1 | signal_line | 12 | 52 | 9 | +0.397 |
| 2 | signal_line | 6 | 26 | 5 | +0.377 |
| 3 | signal_line | 6 | 52 | 18 | +0.354 |
| 4 | signal_line | 24 | 26 | 9 | +0.354 |
| 5 | signal_line | 6 | 52 | 5 | +0.352 |
| 6 | signal_line | 6 | 26 | 18 | +0.346 |
| 7 | signal_line | 24 | 52 | 5 | +0.345 |
| 8 | signal_line | 24 | 26 | 5 | +0.342 |
| 9 | signal_line | 12 | 26 | 18 | +0.327 |
| 10 | signal_line | 12 | 26 | 9 | +0.324 |
| 11 | signal_line | 6 | 26 | 9 | +0.320 |
| 12 | signal_line | 12 | 13 | 18 | +0.315 |
| 13 | signal_line | 6 | 13 | 5 | +0.312 |
| 14 | signal_line | 12 | 26 | 5 | +0.307 |
| 15 | signal_line | 6 | 52 | 9 | +0.299 |
| 16 | signal_line | 12 | 52 | 18 | +0.295 |
| 17 | signal_line | 12 | 13 | 9 | +0.295 |
| 18 | signal_line | 12 | 52 | 5 | +0.295 |
| 19 | signal_line | 6 | 13 | 18 | +0.282 |
| 20 | signal_line | 12 | 13 | 5 | +0.270 |
| 21 | signal_line | 6 | 13 | 9 | +0.270 |
| 22 | signal_line | 24 | 52 | 9 | +0.266 |
| 23 | signal_line | 24 | 26 | 18 | +0.206 |
| 24 | signal_line | 24 | 52 | 18 | +0.159 |
| 25 | zero_line | 12 | 13 | - | +0.080 |
| 26 | zero_line | 6 | 13 | - | +0.079 |
| 27 | zero_line | 6 | 26 | - | +0.039 |
| 28 | zero_line | 6 | 52 | - | +0.024 |
| 29 | zero_line | 12 | 26 | - | +0.019 |
| 30 | zero_line | 12 | 52 | - | -0.043 |
| 31 | zero_line | 24 | 26 | - | -0.083 |
| 32 | zero_line | 24 | 52 | - | -0.166 |

**Appel's 12/26/9 ranks 10 of 32** in its own declared grid, at +0.324 against a grid median of +0.295 and a grid max of +0.397.

### Multiplicity

| block | cells | looks |
|---|---|---:|
| core ladder | 3 rungs x 2 books x {gate off, on} | 12 |
| declared sweep | 8 (fast,slow) pairs x 3 signals + 8 zero-line, minus 2 already counted | 30 |
| **total, fresh** | | **42** |

**A correction to the pre-registration's own arithmetic, disclosed rather than absorbed.** The record wrote the sweep block as 6 (fast,slow) pairs and 22 looks. The grid it declares — fast in {6,12,24}, slow in {13,26,52}, fast < slow — admits EIGHT pairs, because (12,13) and (24,26) satisfy fast < slow and were missed when the pairs were counted by eye. The grid itself is unchanged and was not widened: the COUNT was wrong, and the ledger carries the corrected 42, which is the number the deflated Sharpe is computed against.

Census, break-even arithmetic, nulls and buy-and-hold carry zero looks — a null is the yardstick for a look, not an additional one.

| count | N | SR0 (per-period) | SR0 (annualised) |
|---|---:|---:|---:|
| combined_with_disclosed **(verdict)** | 45783 | 0.04017 | 0.638 |
| fresh | 42 | 0.02104 | 0.334 |
| fresh_plus_prior_configs | 45388 | 0.04015 | 0.637 |

The prior ETF-fixture registries hold **129,286 rows**, which is NOT an N — re-running the same window at scaled costs is not an independent trial (D98/D116/D126/D142). The `include` predicate is distinct logged config payload, giving 45,346 distinct configurations; the raw count stands as the ceiling.

### The verdict

| cell | Sharpe | A ladder | B rotation | C block | D benchmark | F halves | G DSR | survivor |
|---|---:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `signal_line/long_short/none` | +0.312 | yes | no | yes | yes | yes | no | no |
| `signal_line/long_short/200ma` | +0.205 | no | no | no | yes | no | no | no |
| `signal_line/long_flat/none` | +0.496 | yes | yes | yes | yes | yes | no | no |
| `signal_line/long_flat/200ma` | +0.288 | no | no | no | yes | yes | no | no |
| `zero_line/long_short/none` | +0.026 | yes | no | no | yes | no | no | no |
| `zero_line/long_short/200ma` | +0.019 | no | no | no | yes | no | no | no |
| `zero_line/long_flat/none` | +0.286 | yes | no | no | yes | yes | no | no |
| `zero_line/long_flat/200ma` | +0.194 | no | no | no | no | yes | no | no |
| `momentum/long_short/none` | -0.136 | no | no | no | no | yes | no | no |
| `momentum/long_short/200ma` | -0.070 | no | no | no | no | no | no | no |
| `momentum/long_flat/none` | +0.157 | no | no | no | no | yes | no | no |
| `momentum/long_flat/200ma` | +0.117 | no | no | no | no | yes | no | no |

**Hurdle D under a total-return reading, disclosed.** The record wrote *beat buy-and-hold* without naming a metric, and the study ran it on Sharpe, which is therefore the reading that counts. On dividend-adjusted TOTAL RETURN the long-flat cells are judged against buy-and-hold's 70.81%, and **0** cells would survive under that reading. The verdict is unchanged either way — every cell already fails G — so this is recorded as a second reading, not used to move a goalpost.

**0 of 12 cells clear every hurdle.**

Stage 2 — the costed engine verdict — **does not run.** D217's pre-registered programme stop applies and the study closes here as a reportable negative.

**Reading.** The signal line is worth +0.285 Sharpe long-short and +0.209 long-flat against a +0.10 hurdle, while turning over 2.35x as much as the rung it sits on. The two-EMA difference is worth +0.163 and +0.129 over flat momentum at the same centre of mass. Those four numbers are the study; everything above them is the apparatus that makes them mean something.

## D218 — Impulse MACD, and whether D217's mechanism replicates

**Produced:** 2026-08-24 · **Reproduce:** `uv run python scripts/run_impulse_macd.py` (offline, deterministic, seed 0)

Impulse MACD is **not a MACD variant**. There is no difference of two EMAs of one series anywhere in it: it is a zero-lag mid price against a slow smoothed high/low channel, with a dead zone. But the algebra puts it in the same shape D217 worked in — `smma` is Wilder smoothing (alpha = 1/n, lagging a ramp by exactly 33b) and `zlema = 2*EMA1 - EMA2` has centre of mass **exactly zero** — so on constant drift **`md = 33b`** where D217's **`macd = 7b`**, and `sh -> 0` exactly as D217's histogram does. `md` is a trend-LEVEL rule; `sh` is a trend-ACCELERATION rule. **That makes this a replication of D217's finding on a construction that shares no arithmetic with it.**

Warm-up is **1000 bars** — about four years of daily data — because Wilder smoothing at alpha = 1/34 needs 926 bars for its seed to stop mattering, against 360 for a 26-period EMA. The SMA seed is exact for the 2/(n+1) convention and **not** for Wilder, and that asymmetry is the whole gap. Every arm, including the D217 control, starts on 2018-12-21 and runs to 2024-12-30 — 1515 live bars.

### The ladder. 16 looks.

| rung | book | gate | Sharpe | +div total | CAGR | maxDD | expo | rot. delta | pct |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| I1 signal line | long_short | none | +0.363 | 39.88% | 5.74% | -19.22% | 96.85% | +0.445 | 84 |
| I1 signal line | long_short | 200ma | +0.170 | 15.02% | 2.36% | -14.14% | 52.98% | -0.186 | 32 |
| I1 signal line | long_flat | none | +0.658 | 52.12% | 7.23% | -12.70% | 49.93% | +0.355 | 100 |
| I1 signal line | long_flat | 200ma | +0.291 | 13.60% | 2.14% | -6.22% | 32.87% | -0.069 | 32 |
| I2 band state | long_short | none | -0.265 | -17.19% | -3.09% | -30.30% | 88.10% | -0.766 | 0 |
| I2 band state | long_short | 200ma | -0.196 | -12.41% | -2.18% | -26.81% | 78.39% | -0.718 | 0 |
| I2 band state | long_flat | none | +0.129 | 14.34% | 2.25% | -15.28% | 54.64% | -0.262 | 0 |
| I2 band state | long_flat | 200ma | +0.195 | 15.40% | 2.41% | -13.46% | 49.81% | -0.210 | 1 |
| I3 no dead zone | long_short | none | -0.249 | -16.18% | -2.89% | -29.80% | 99.93% | -0.744 | 1 |
| I3 no dead zone | long_short | 200ma | -0.164 | -10.08% | -1.75% | -25.09% | 84.86% | -0.657 | 0 |
| I3 no dead zone | long_flat | none | +0.153 | 17.61% | 2.74% | -16.95% | 60.60% | -0.230 | 0 |
| I3 no dead zone | long_flat | 200ma | +0.224 | 18.27% | 2.83% | -14.55% | 53.61% | -0.177 | 1 |
| C MACD control | long_short | none | +0.401 | 42.24% | 6.04% | -20.48% | 99.93% | +0.547 | 88 |
| C MACD control | long_short | 200ma | +0.212 | 17.13% | 2.67% | -16.89% | 52.01% | -0.112 | 39 |
| C MACD control | long_flat | none | +0.649 | 53.21% | 7.35% | -13.55% | 50.87% | +0.361 | 100 |
| C MACD control | long_flat | 200ma | +0.387 | 16.07% | 2.51% | -6.24% | 32.32% | +0.039 | 64 |
| **buy-and-hold** | — | — | **+0.333** | **62.59%** | 8.42% | -34.81% | 100.00% | — | — |

**Hurdle A — the deltas. J2 is the whole study.**

| book | gate | I1 | I2 | I3 | C | I1−I2 (signal) | I2−I3 (dead zone) | I1−C |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| long_short | none | +0.363 | -0.265 | -0.249 | +0.401 | **+0.628** | **-0.016** | -0.038 |
| long_short | 200ma | +0.170 | -0.196 | -0.164 | +0.212 | **+0.366** | **-0.032** | -0.042 |
| long_flat | none | +0.658 | +0.129 | +0.153 | +0.649 | **+0.529** | **-0.024** | +0.008 |
| long_flat | 200ma | +0.291 | +0.195 | +0.224 | +0.387 | **+0.096** | **-0.029** | -0.096 |

**The replication test.** D217 measured its own signal-line delta at **+0.285** long-short and **+0.209** long-flat. The same delta here, on an indicator sharing no arithmetic with it, is **+0.628** and **+0.529**. Same sign: **yes**. Clears the +0.10 hurdle: **yes**.

**A caveat on the magnitude, before anyone quotes it.** A large I1−I2 delta can be manufactured two ways: by I1 being good, or by I2 being BAD. I2 here sits at the **0th percentile of its own rotation null** on three of four cells — the band state is not noise, it is actively anti-predictive — so part of the +0.628 is I2 being wrong rather than I1 being right. The clean read is `I1 − C`, which compares this indicator's acceleration rung against D217's on the same bars: **that delta is approximately zero**. The replication is real in SIGN; its MAGNITUDE is inflated by how badly the level rung does here.

**The dead zone, and the exposure trap it walks straight into.**

| book | gate | I2 expo | I3 expo | I2 +div total | I3 +div total | Sharpe I2−I3 |
|---|---|---:|---:|---:|---:|---:|
| long_short | none | 88.10% | 99.93% | -17.19% | -16.18% | -0.016 |
| long_short | 200ma | 78.39% | 84.86% | -12.41% | -10.08% | -0.032 |
| long_flat | none | 54.64% | 60.60% | 14.34% | 17.61% | -0.024 |
| long_flat | 200ma | 49.81% | 53.61% | 15.40% | 18.27% | -0.029 |

The dead zone's only mechanism is standing aside, so it buys Sharpe by holding less and pays for it in money. D217's addendum documented that trade exactly; here it is designed into the indicator rather than emerging from a filter, which is why hurdle D names **both** metrics up front.

### The fill bracket

| rung | book | gate | Sharpe lag 1 | Sharpe lag 2 | change |
|---|---|---|---:|---:|---:|
| I1 signal line | long_short | none | +0.363 | +0.294 | -0.068 |
| I1 signal line | long_short | 200ma | +0.170 | +0.102 | -0.068 |
| I1 signal line | long_flat | none | +0.658 | +0.607 | -0.050 |
| I1 signal line | long_flat | 200ma | +0.291 | +0.228 | -0.063 |
| I2 band state | long_short | none | -0.265 | -0.275 | -0.010 |
| I2 band state | long_short | 200ma | -0.196 | -0.225 | -0.030 |
| I2 band state | long_flat | none | +0.129 | +0.131 | +0.002 |
| I2 band state | long_flat | 200ma | +0.195 | +0.184 | -0.011 |
| I3 no dead zone | long_short | none | -0.249 | -0.335 | -0.087 |
| I3 no dead zone | long_short | 200ma | -0.164 | -0.243 | -0.079 |
| I3 no dead zone | long_flat | none | +0.153 | +0.102 | -0.051 |
| I3 no dead zone | long_flat | 200ma | +0.224 | +0.217 | -0.006 |
| C MACD control | long_short | none | +0.401 | +0.316 | -0.086 |
| C MACD control | long_short | 200ma | +0.212 | +0.121 | -0.091 |
| C MACD control | long_flat | none | +0.649 | +0.593 | -0.056 |
| C MACD control | long_flat | 200ma | +0.387 | +0.263 | -0.124 |

### Sensitivity — `lengthMA`. 4 looks.

**These levels are not comparable to the ladder above.** `lengthMA = 55` needs a 1,506-bar burn-in of its own, so this block starts at bar 1622 rather than 1000 and runs on 893 live bars — a shorter and later span. Only the comparison WITHIN the block is meaningful, and the question it answers is narrow: is 34 special?

| rung | lengthMA | Sharpe |
|---|---:|---:|
| I1 signal line | 21 | +0.124 |
| I2 band state | 21 | -0.542 |
| I1 signal line **(published)** | 34 | +0.010 |
| I2 band state **(published)** | 34 | -0.755 |
| I1 signal line | 55 | -0.132 |
| I2 band state | 55 | -0.343 |

### Multiplicity — and this study does not get a fresh ledger

D217 argued a fresh ledger on three grounds: different fixture, different claim family, a sensor that did not exist here. **None of them hold now.** Same fixture, same claim family, close-cousin sensors — so D217's 42 are inherited in full.

| block | looks |
|---|---:|
| the ladder — 4 rungs x 2 books x {gate off, on} | 16 |
| sensitivity — 3 lengths x 2 rungs, minus 2 already counted | 4 |
| **fresh, D218 only** | **20** |
| inherited from D217 | 42 |

| count | N | SR0 (per-period) | SR0 (annualised) |
|---|---:|---:|---:|
| combined_with_disclosed **(verdict)** | 45,803 | 0.08946 | 1.420 |
| fresh_d218_only | 20 | 0.04032 | 0.640 |
| with_inherited_d217 | 62 | 0.05001 | 0.794 |

62 new looks against 45,741 moves the floor by almost nothing, and that is the point rather than a footnote: **this fixture is exhausted.** The raw registry row ceiling is 129,286 and is not used as an N (D98/D116/D126/D142).

### The verdict

| cell | Sharpe | +div total | A | B | C | D both | F | G | survivor |
|---|---:|---:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `I1_signal/long_short/none` | +0.363 | 39.88% | no | no | no | yes | yes | no | no |
| `I1_signal/long_short/200ma` | +0.170 | 15.02% | no | no | no | yes | no | no | no |
| `I1_signal/long_flat/none` | +0.658 | 52.12% | no | yes | yes | no | yes | no | no |
| `I1_signal/long_flat/200ma` | +0.291 | 13.60% | no | no | no | no | yes | no | no |
| `I2_band/long_short/none` | -0.265 | -17.19% | no | no | no | no | yes | no | no |
| `I2_band/long_short/200ma` | -0.196 | -12.41% | no | no | no | no | yes | no | no |
| `I2_band/long_flat/none` | +0.129 | 14.34% | no | no | no | no | yes | no | no |
| `I2_band/long_flat/200ma` | +0.195 | 15.40% | no | no | no | no | yes | no | no |
| `I3_no_deadzone/long_short/none` | -0.249 | -16.18% | no | no | no | no | yes | no | no |
| `I3_no_deadzone/long_short/200ma` | -0.164 | -10.08% | no | no | no | no | yes | no | no |
| `I3_no_deadzone/long_flat/none` | +0.153 | 17.61% | no | no | no | no | yes | no | no |
| `I3_no_deadzone/long_flat/200ma` | +0.224 | 18.27% | no | no | no | no | yes | no | no |
| `C_macd_signal/long_short/none` | +0.401 | 42.24% | no | no | yes | yes | yes | no | no |
| `C_macd_signal/long_short/200ma` | +0.212 | 17.13% | no | no | no | yes | no | no | no |
| `C_macd_signal/long_flat/none` | +0.649 | 53.21% | no | yes | yes | no | yes | no | no |
| `C_macd_signal/long_flat/200ma` | +0.387 | 16.07% | no | no | no | no | yes | no | no |

**0 of 16 cells clear every hurdle.**

D218's pre-registered stop applies and the study closes here as a reportable negative.

**Reading.** D217's acceleration-beats-level result **REPLICATES** here: I1-I2 is +0.628 long-short and +0.529 long-flat, against D217's +0.285 and +0.209 on an indicator sharing no arithmetic with it. The dead zone is worth -0.016 Sharpe while cutting exposure from 99.93% to 88.10% — hurting BOTH metrics, not trading one for the other. And Impulse MACD beats D217's own best rung by -0.038: the whole apparatus of a Wilder channel, a zero-lag mid and a dead zone buys nothing over a plain 12/26/9 signal line. Those numbers are the study; everything above them is what makes them mean something.

---

### Parking lot

- **PPO on the signal line.** `EMA(macd/d) != EMA(macd)/d`, so PPO-signal-cross and
  MACD-signal-cross are genuinely different hypotheses (rungs 2 and 3 are provably
  unmoved by any positive divisor). Deliberately outside this ledger; it is a
  question for a crypto-daily replication, where the price multiple is large enough
  for the two to diverge.
