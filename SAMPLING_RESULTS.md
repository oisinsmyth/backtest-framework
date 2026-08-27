# Sampling invariance — D221

**Produced:** 2026-08-27 · **Reproduce:** `uv run python scripts/run_sampling_invariance.py` (offline, deterministic) ·
Record: [`D221`](docs/decisions/D221-does-the-indicator-care-about-sampling-rate.md) ·
Artifact: `data/sampling_invariance_summary.json`

Two estimators covering the **same wall-clock window** on the same asset over the
same days. The 1h series is exact OHLCV aggregation of the 15m source (D161), so a
gap between them is the sampling rate and nothing else.

## Gross — the primary comparison

| symbol | config | bars | gross Sharpe | Δ vs 1h | ρ with 1h | RT/yr |
|---|---|---:|---:|---:|---:|---:|
| BTCUSDT | A_1h_default | 60m | +0.681 | +0.000 | 1.00 | 226 |
| BTCUSDT | B_15m_x4 | 15m | +0.735 | +0.054 | 0.95 | 222 |
| BTCUSDT | C_15m_lag_matched | 15m | +0.789 | +0.108 | 0.94 | 233 |
| BTCUSDT | D_15m_default | 15m | -0.298 | -0.979 | 0.50 | 946 |
| ETHUSDT | A_1h_default | 60m | +0.733 | +0.000 | 1.00 | 226 |
| ETHUSDT | B_15m_x4 | 15m | +0.813 | +0.080 | 0.96 | 228 |
| ETHUSDT | C_15m_lag_matched | 15m | +0.813 | +0.080 | 0.95 | 240 |
| ETHUSDT | D_15m_default | 15m | +0.224 | -0.510 | 0.50 | 939 |
| XEMUSDT | A_1h_default | 60m | -0.547 | +0.000 | 1.00 | 239 |
| XEMUSDT | B_15m_x4 | 15m | -0.650 | -0.103 | 0.96 | 234 |
| XEMUSDT | C_15m_lag_matched | 15m | -0.626 | -0.079 | 0.96 | 244 |
| XEMUSDT | D_15m_default | 15m | -1.939 | -1.392 | 0.58 | 990 |
| BTGUSDT | A_1h_default | 60m | +0.767 | +0.000 | 1.00 | 217 |
| BTGUSDT | B_15m_x4 | 15m | +0.617 | -0.149 | 0.96 | 215 |
| BTGUSDT | C_15m_lag_matched | 15m | +0.431 | -0.336 | 0.97 | 229 |
| BTGUSDT | D_15m_default | 15m | -3.416 | -4.183 | 0.50 | 961 |

## Verdict — hurdle I

Invariance holds if `|Δ| <= 0.15` **and** `ρ >= 0.8` on every symbol.

| symbol | Δ (B−A) | within ±0.15 | ρ | ρ ≥ 0.80 |
|---|---:|:--:|---:|:--:|
| BTCUSDT | +0.054 | yes | 0.95 | yes |
| BTGUSDT | -0.149 | yes | 0.96 | yes |
| ETHUSDT | +0.080 | yes | 0.96 | yes |
| XEMUSDT | -0.103 | yes | 0.96 | yes |

**Invariance holds: YES.**

## Net — hurdle J, the arithmetic gate

| symbol / config | RT/yr | drag @ 40bp | net Sharpe @ 40bp | tradeable at any tier |
|---|---:|---:|---:|:--:|
| BTCUSDT/A_1h_default | 226 | 181% | -3.544 | yes |
| BTCUSDT/B_15m_x4 | 222 | 178% | -3.286 | yes |
| BTCUSDT/C_15m_lag_matched | 233 | 187% | -3.437 | yes |
| BTCUSDT/D_15m_default | 946 | 757% | -16.852 | no |
| BTGUSDT/A_1h_default | 217 | 174% | -0.810 | yes |
| BTGUSDT/B_15m_x4 | 215 | 172% | -0.831 | yes |
| BTGUSDT/C_15m_lag_matched | 229 | 183% | -1.104 | yes |
| BTGUSDT/D_15m_default | 961 | 768% | -9.907 | no |
| ETHUSDT/A_1h_default | 226 | 181% | -2.561 | yes |
| ETHUSDT/B_15m_x4 | 228 | 183% | -2.442 | yes |
| ETHUSDT/C_15m_lag_matched | 240 | 192% | -2.612 | yes |
| ETHUSDT/D_15m_default | 939 | 751% | -13.039 | yes |
| XEMUSDT/A_1h_default | 239 | 191% | -2.661 | no |
| XEMUSDT/B_15m_x4 | 234 | 187% | -2.649 | no |
| XEMUSDT/C_15m_lag_matched | 244 | 195% | -2.719 | no |
| XEMUSDT/D_15m_default | 990 | 792% | -10.767 | no |

## The fixture finding that outlives this study

`crypto_intraday_1h_raw`, the repo's only **native** 1h crypto fixture, is **50.4%
zero-volume bars**. The cleaner drops 17,520 of them, leaving an irregular ~2h series
wearing a 1h label. It is unusable for any frequency comparison and for any volume
work. That is why the 1h arm here is resampled rather than fetched.

**No config is promoted by this study under any outcome** — it asks how an estimator
behaves, not whether an arm is tradeable. A positive gross Sharpe here gets its own
pre-registration or it gets nothing.

