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

**0 of 12 cells clear every hurdle.**

Stage 2 — the costed engine verdict — **does not run.** D217's pre-registered programme stop applies and the study closes here as a reportable negative.

**Reading.** The signal line is worth +0.285 Sharpe long-short and +0.209 long-flat against a +0.10 hurdle, while turning over 2.35x as much as the rung it sits on. The two-EMA difference is worth +0.163 and +0.129 over flat momentum at the same centre of mass. Those four numbers are the study; everything above them is the apparatus that makes them mean something.

---

### Parking lot

- **PPO on the signal line.** `EMA(macd/d) != EMA(macd)/d`, so PPO-signal-cross and
  MACD-signal-cross are genuinely different hypotheses (rungs 2 and 3 are provably
  unmoved by any positive divisor). Deliberately outside this ledger; it is a
  question for a crypto-daily replication, where the price multiple is large enough
  for the two to diverge.
