# D260 — the vol-targeted overnight hold, on a time holdout

**Produced by** `scripts/run_vol_targeted_hold.py` · 33s · 12,901 holds, 2010-02-11 → 2026-08-26

Screen 6,899 holds (→ 2018-12-31), **holdout 6,002 holds, and it contains March 2020 by design.**


`TARGET = 4% / N`, cap 4x, volatility over the prior 21 holds.


## All four cells — screen and holdout

| N | target | | breach | expected life | ann return | profit before breach | worst hold |
|---|---:|---|---:|---:|---:|---:|---:|
| 6 | 0.67% | screen | 0.304% | 1.30y | +8.33% | 10.9% | -8.50% |
|  | 0.67% | holdout | 0.167% | 2.38y | +6.20% | 14.8% | -6.64% |
| 8 | 0.50% | screen | 0.130% | 3.04y | +6.26% | 19.0% | -6.37% |
|  | 0.50% | holdout | 0.050% | 7.94y | +4.65% | 36.9% | -4.98% |
| 10 | 0.40% | screen | 0.087% | 4.56y | +5.01% | 22.8% | -5.10% |
|  | 0.40% | holdout | 0.033% | 11.91y | +3.72% | 44.3% | -3.98% |
| 12 | 0.33% | screen | 0.014% | 27.38y | +4.17% | 114.2% | -4.25% |
|  | 0.33% | holdout | 0.000% | ∞ | +3.10% | ∞ | -3.32% |

## The verdict cell — N chosen on the screen, judged on the holdout

**N = 12**, target **0.33%**


| hurdle | measured | required | |
|---|---:|---:|:--:|
| **P4** expected life | ∞ | > 3 y | **YES** |
| **P3** worst hold | -3.32% | ≥ −2.00% | no |
| **LADDER** profit before breach | ∞ | > 26% | **YES** |
| **STABILITY** holdout/screen breach | 0.00x | 0.5–2.0x | **YES** |

## 2020, reported separately — V-c's test

| N | 2020 breach | holdout ex-2020 | ratio |
|---|---:|---:|---:|
| 6 | 0.379% | 0.134% | 2.8x |
| 8 | 0.126% | 0.038% | 3.3x |
| 10 | 0.000% | 0.038% | 0.0x |
| 12 | 0.000% | 0.000% | infx |

**V-c predicted 2020 would be the worst year in the holdout, because a 21-hold volatility estimate cannot adapt to a regime that changed in a week.**


## Verdict

**THE VERDICT CELL DOES NOT CLEAR ALL FOUR. Per D260's stop, C1 is CLOSED for good — no third sizing scheme, no re-split, no alternative estimator window.**


*A pass here is a FEASIBILITY BOUND, not a deployable backtest: the path is equity extended-hours bars, 16 of the 23 futures hours.*

