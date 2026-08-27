# D230 — the bootstrap sweep

*`scripts/run_bootstrap_sweep.py`, seed 0, 1,000 replications at block 21, 12.6s. D217 arms start at bar 393, D218 and D229 at 1,000.*

**8 of 24 deltas cleared the hurdle as the runners scored it. 0 clear it as the records claimed it. 8 change verdict.**

*Reproduction gate: every point estimate matches its committed artifact to 1e-9.*

## Every delta

| study | delta | book | gate | point | p05 | p95 | width | as scored | as claimed |
|---|---|---|---|---:|---:|---:|---:|:--:|:--:|
| D217 | `R1 - R2` | long_short | none | **+0.285** | -0.167 | +0.809 | 0.977 | PASS | **FAIL** |
| D217 | `R1 - R2` | long_short | 200ma | **+0.186** | -0.081 | +0.495 | 0.576 | PASS | **FAIL** |
| D217 | `R1 - R2` | long_flat | none | **+0.209** | -0.152 | +0.572 | 0.724 | PASS | **FAIL** |
| D217 | `R1 - R2` | long_flat | 200ma | **+0.093** | -0.250 | +0.433 | 0.682 | — | **FAIL** |
| D217 | `R2 - R3` | long_short | none | **+0.163** | -0.078 | +0.443 | 0.521 | PASS | **FAIL** |
| D217 | `R2 - R3` | long_short | 200ma | **+0.089** | -0.043 | +0.241 | 0.283 | — | **FAIL** |
| D217 | `R2 - R3` | long_flat | none | **+0.129** | -0.070 | +0.322 | 0.391 | PASS | **FAIL** |
| D217 | `R2 - R3` | long_flat | 200ma | **+0.078** | -0.078 | +0.212 | 0.290 | — | **FAIL** |
| D218 | `I1 - I2` | long_short | none | **+0.628** | -0.133 | +1.325 | 1.458 | PASS | **FAIL** |
| D218 | `I1 - I2` | long_short | 200ma | **+0.366** | -0.076 | +0.721 | 0.797 | PASS | **FAIL** |
| D218 | `I1 - I2` | long_flat | none | **+0.529** | -0.055 | +1.015 | 1.070 | PASS | **FAIL** |
| D218 | `I1 - I2` | long_flat | 200ma | **+0.096** | -0.322 | +0.435 | 0.757 | — | **FAIL** |
| D218 | `I2 - I3` | long_short | none | **-0.016** | -0.068 | +0.031 | 0.099 | — | **FAIL** |
| D218 | `I2 - I3` | long_short | 200ma | **-0.032** | -0.102 | +0.020 | 0.121 | — | **FAIL** |
| D218 | `I2 - I3` | long_flat | none | **-0.024** | -0.115 | +0.049 | 0.165 | — | **FAIL** |
| D218 | `I2 - I3` | long_flat | 200ma | **-0.029** | -0.105 | +0.034 | 0.139 | — | **FAIL** |
| D218 | `I1 - C` | long_short | none | **-0.038** | -0.378 | +0.279 | 0.657 | — | **FAIL** |
| D218 | `I1 - C` | long_short | 200ma | **-0.042** | -0.299 | +0.169 | 0.468 | — | **FAIL** |
| D218 | `I1 - C` | long_flat | none | **+0.008** | -0.258 | +0.263 | 0.521 | — | **FAIL** |
| D218 | `I1 - C` | long_flat | 200ma | **-0.096** | -0.339 | +0.152 | 0.490 | — | **FAIL** |
| D229 | `I0 - I1` | long_short | none | **-0.224** | -1.031 | +0.621 | 1.652 | — | **FAIL** |
| D229 | `I0 - I1` | long_short | 200ma | **-0.152** | -0.712 | +0.391 | 1.104 | — | **FAIL** |
| D229 | `I0 - I1` | long_flat | none | **-0.218** | -0.759 | +0.402 | 1.161 | — | **FAIL** |
| D229 | `I0 - I1` | long_flat | 200ma | **+0.006** | -0.554 | +0.563 | 1.118 | — | **FAIL** |

**24 of 24 intervals contain zero.**

