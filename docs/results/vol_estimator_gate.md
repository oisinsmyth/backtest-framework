# Does finer data give a better estimate? The volatility gate

D195 step 1, pre-registered in `D195-the-volatility-estimator-gate.md (commit c27e671)` before this run existed. A forecasting comparison: no strategy, no costs, no trading.

**The question.** `InverseVolatilityWeight` sizes every position off 20 close-to-close daily returns. The same 20 calendar days at 15m hold 1,920 observations. Does the finer estimator forecast the next 20 days better?

Both estimators come from the same 15m fixture with the daily series resampled from it, so provider, span and calendar are identical and the estimator is the only variable.

**Two targets are scored, and that is the point of the design.** The accurate target is realized vol from 15m — but the candidate is built the same way, so any systematic component in 15m realized variance is inherited by both and flatters it. The incumbent's own basis is scored as a second target. The candidate must win on both; a win only on the shared-basis target is an artifact, not a result.

## The bar: 30% loss reduction, every cell

| symbol | pairs | realized/MSE | realized/QLIKE | c2c/MSE | c2c/QLIKE | worst | verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| `BTCUSDT` | 3,026 | +18.6% | +29.9% | +15.8% | +27.2% | **+15.8%** | FAIL |
| `ETHUSDT` | 3,026 | +22.0% | +26.5% | +22.7% | +25.8% | **+22.0%** | FAIL |
| `XEMUSDT` | 1,250 | +32.8% | +55.7% | -0.2% | +34.6% | **-0.2%** | FAIL |
| `BTGUSDT` | 511 | +36.2% | +51.6% | -29.6% | +13.9% | **-29.6%** | FAIL |

**Gate (BTCUSDT, ETHUSDT): FAIL.** A positive reduction means the candidate's loss is lower.

## The losses in full

### `BTCUSDT` — 3,066 days, 2018-02-12 to 2026-07-31, 3,026 forecast pairs

| target | loss | incumbent | candidate | reduction |
|---|---|---:|---:|---:|
| realized | mse_log | 0.18441 | 0.15010 | +18.6% |
| realized | qlike | 0.64234 | 0.45007 | +29.9% |
| close_to_close | mse_log | 0.21883 | 0.18435 | +15.8% |
| close_to_close | qlike | 0.71589 | 0.52105 | +27.2% |
| realized | R² | 0.2128 | 0.2710 | — |
| close_to_close | R² | 0.1601 | 0.2188 | — |

### `ETHUSDT` — 3,066 days, 2018-02-12 to 2026-07-31, 3,026 forecast pairs

| target | loss | incumbent | candidate | reduction |
|---|---|---:|---:|---:|
| realized | mse_log | 0.17004 | 0.13256 | +22.0% |
| realized | qlike | 0.43758 | 0.32164 | +26.5% |
| close_to_close | mse_log | 0.19286 | 0.14916 | +22.7% |
| close_to_close | qlike | 0.47368 | 0.35169 | +25.8% |
| realized | R² | 0.2145 | 0.2938 | — |
| close_to_close | R² | 0.1915 | 0.2827 | — |

### `XEMUSDT` — 1,290 days, 2020-11-25 to 2024-06-16, 1,250 forecast pairs

| target | loss | incumbent | candidate | reduction |
|---|---|---:|---:|---:|
| realized | mse_log | 0.28050 | 0.18839 | +32.8% |
| realized | qlike | 1.01236 | 0.44839 | +55.7% |
| close_to_close | mse_log | 0.29201 | 0.29254 | -0.2% |
| close_to_close | qlike | 0.84892 | 0.55518 | +34.6% |
| realized | R² | 0.2100 | 0.2093 | — |
| close_to_close | R² | 0.1884 | 0.2020 | — |

### `BTGUSDT` — 551 days, 2021-04-17 to 2022-10-23, 511 forecast pairs

| target | loss | incumbent | candidate | reduction |
|---|---|---:|---:|---:|
| realized | mse_log | 0.20752 | 0.13233 | +36.2% |
| realized | qlike | 0.73854 | 0.35730 | +51.6% |
| close_to_close | mse_log | 0.19038 | 0.24668 | -29.6% |
| close_to_close | qlike | 0.46703 | 0.40195 | +13.9% |
| realized | R² | 0.0954 | 0.2074 | — |
| close_to_close | R² | 0.1055 | 0.1396 | — |

## What a pass does not mean

It means the incumbent sizing input is measurably worse than an available alternative. It does **not** mean the book improves — that is D195 step 2, and its bar of +0.10 Sharpe on both symbols was fixed before this ran. D195 predicts step 1 passes and step 2 fails, on the grounds that the sizing defect is structural in the weighting rule rather than an accuracy problem with its input.

---

Generated 2026-08-23T11:40:19.238127+00:00 in 11.1s · every figure rendered from `vol_estimator_gate_summary.json`
