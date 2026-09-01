# D261 — the index spread, as a prop-track candidate

**Produced by** `scripts/run_index_spread.py` · 3s · 3,115 holds, 2010-01-05 → 2026-08-26


`|z| > 2.0` entry, `|z| < 0.5` exit, 60-hold lookback, 20-hold cap, 0.2 bp per leg. **All six pairs, no selection step.**


| pair | trades | ann return | vol | Sharpe | breach | life | worst | **net beta** | null (S/M) | V | NEUT | P3 | P4 | NULL | **success** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:--:|:--:|:--:|:--:|:--:|:--:|
| **SPY-QQQ** | 96 | +0.23% | 4.8% | +0.048 | 0.067% | 6.0y | -4.08% | **+0.057** | 19/26 | y | y | n | y | n | no |
| **SPY-IWM** | 98 | +1.45% | 6.2% | +0.236 | 0.067% | 6.0y | -2.88% | **+0.010** | 78/6 | y | y | n | y | n | no |
| **SPY-DIA** | 116 | -1.02% | 5.1% | -0.199 | 0.133% | 3.0y | -2.03% | **+0.026** | 0/29 | n | y | n | n | n | no |
| **QQQ-IWM** | 91 | +1.46% | 9.9% | +0.147 | 0.200% | 2.0y | -4.72% | **+0.025** | 46/98 | y | y | n | n | n | no |
| **QQQ-DIA** | 97 | -1.82% | 10.6% | -0.173 | 0.466% | 0.9y | -5.06% | **+0.025** | 68/74 | n | y | n | n | n | no |
| **IWM-DIA** | 99 | +3.01% | 10.2% | +0.296 | 0.732% | 0.5y | -4.56% | **-0.010** | 24/60 | y | y | n | n | n | no |

## Verdict

**NO PAIR CLEARS V, NULL AND NEUTRALITY TOGETHER. Per D261's stop the spread category is CLOSED for the prop track — no threshold sweep, no second lookback, no cointegration screen added afterwards.**


*Equity proxies, not futures. A pass would be a feasibility bound.*

