# LIQUIDITY MAP

**Rendered from [`data/d651_liquidity_map.json`](../../data/d651_liquidity_map.json) by `scripts/build_fut_liquidity_map.py --report` ([D651](../decisions/D651-PRE-REG-the-time-of-day-liquidity-map-and-the-handoff-kill-1.md)).** The JSON is the truth; editing this page by hand is a change the next render throws away.

Front-contract `bbo-1m`, session days 2025-09-11 → 2026-09-10 (inside the programme vault; quotes only, no return). Spread is QUOTED spread in ticks, a floor on what an aggressor pays. Depth is bid + ask size at the touch, contracts. Windows in ET: W1 02:00–03:30, W2 07:30–08:30, W3 16:00–17:00 + 18:00–19:00; core 10:00–15:00.

## The decision

- kill 1 fires: **False**
- candidate set (TROUGH and H0 PASS): **none**
- branch **(c)**: No affordable trough: recommend no pull; the principal decides.

## Predictions

- P1 kill 1 does not fire; ES PASS, MES FAIL (read on W3): **HELD**
- P2 W3 TROUGH on ES NQ ZN CL: **FAILED** — {'ES': 'NOT A TROUGH', 'NQ': 'NOT A TROUGH', 'ZN': 'NOT A TROUGH', 'CL': 'NOT A TROUGH'}
- P3 W2 TROUGH on ZN ZB ES: **FAILED** — {'ZN': 'NOT A TROUGH', 'ZB': 'NOT A TROUGH', 'ES': 'NOT A TROUGH'}
- P4 W1 TROUGH on 6E 6B; not a TROUGH on the index roots: **FAILED** — {'6E': 'NOT A TROUGH', '6B': 'NOT A TROUGH', 'ES': 'NOT A TROUGH', 'NQ': 'NOT A TROUGH', 'RTY': 'NOT A TROUGH', 'YM': 'NOT A TROUGH'}
- P5 median D_W / median D_core < 0.5 on the index roots, every window: **FAILED**

## Per root and window

`x` = median ln(depth in window / thinner neighbour), 95% block-bootstrap interval; R = half quoted spread in $ / declared commission per side.

| root | core S | core R | W1 x [95%] | W1 R | W2 x [95%] | W2 R | W3 x [95%] | W3 R |
|---|---:|---:|---|---:|---|---:|---|---:|
| ES | 1.04 | 2.16 | N +0.05 [+0.03, +0.07] | 2.39 P | N +0.07 [+0.04, +0.10] | 2.37 P | N +0.71 [+0.63, +0.80] | 2.43 P |
| NQ | 2.69 | 2.24 | N +0.04 [+0.04, +0.05] | 3.35 P | N +0.04 [+0.02, +0.05] | 3.17 P | N +0.30 [+0.27, +0.34] | 3.45 P |
| RTY | 1.70 | 1.42 | N +0.04 [+0.03, +0.05] | 2.06 P | N +0.07 [+0.06, +0.09] | 1.94 M | N +0.64 [+0.56, +0.71] | 2.01 P |
| YM | 2.14 | 1.78 | N +0.05 [+0.04, +0.05] | 1.99 M | N +0.04 [+0.04, +0.05] | 2.02 P | U -0.00 [-0.03, +0.03] | 2.68 P |
| MES | 1.05 | 0.44 | N +0.02 [+0.00, +0.03] | 0.47 F | N +0.08 [+0.07, +0.10] | 0.47 F | N +0.15 [+0.07, +0.25] | 0.48 F |
| MNQ | 1.73 | 0.29 | N +0.04 [+0.03, +0.05] | 0.40 F | N +0.04 [+0.02, +0.05] | 0.41 F | N +0.06 [+0.02, +0.10] | 0.42 F |
| M2K | 1.56 | 0.26 | N +0.04 [+0.03, +0.06] | 0.32 F | N +0.05 [+0.03, +0.06] | 0.33 F | N +0.22 [+0.19, +0.26] | 0.39 F |
| MYM | 1.64 | 0.27 | N +0.04 [+0.02, +0.05] | 0.38 F | N +0.05 [+0.03, +0.06] | 0.39 F | N +0.11 [+0.09, +0.13] | 0.47 F |
| CL | 1.46 | 2.43 | N +0.07 [+0.05, +0.08] | 2.70 P | N +0.07 [+0.05, +0.09] | 2.61 P | N +0.14 [+0.10, +0.17] | 3.51 P |
| NG | 1.22 | 2.04 | N +0.10 [+0.08, +0.12] | 2.44 P | N +0.05 [+0.03, +0.07] | 2.20 P | N +0.20 [+0.13, +0.23] | 2.86 P |
| GC | 3.85 | 6.42 | N +0.03 [+0.02, +0.04] | 6.99 P | N +0.04 [+0.03, +0.05] | 6.79 P | N +0.07 [+0.04, +0.08] | 8.31 P |
| SI | 3.86 | 16.08 | N +0.05 [+0.04, +0.07] | 19.06 P | N +0.03 [+0.02, +0.04] | 17.85 P | N +0.07 [+0.06, +0.08] | 20.14 P |
| HG | 2.14 | 4.46 | N +0.04 [+0.03, +0.05] | 5.05 P | N +0.04 [+0.03, +0.06] | 4.75 P | N +0.07 [+0.06, +0.09] | 5.22 P |
| ZN | 1.00 | 2.60 | N +0.15 [+0.12, +0.17] | 2.60 P | N +0.08 [+0.07, +0.09] | 2.60 P | N +0.79 [+0.72, +0.84] | 2.61 P |
| ZB | 1.00 | 5.21 | N +0.20 [+0.16, +0.23] | 5.22 P | N +0.10 [+0.08, +0.11] | 5.21 P | N +0.78 [+0.73, +0.82] | 5.22 P |
| ZF | 1.00 | 1.30 | N +0.21 [+0.18, +0.23] | 1.30 M | N +0.07 [+0.06, +0.09] | 1.30 M | N +0.82 [+0.78, +0.87] | 1.31 M |
| SR3 | 1.84 | 1.92 | N +0.20 [+0.16, +0.26] | 1.96 M | N +0.11 [+0.07, +0.17] | 1.92 M | N +0.27 [+0.15, +0.38] | 1.95 M |
| ZT | 1.00 | 1.31 | N +0.10 [+0.08, +0.12] | 1.31 M | N +0.07 [+0.05, +0.09] | 1.31 M | N +0.36 [+0.30, +0.46] | 1.32 M |
| UB | 1.00 | 5.22 | N +0.10 [+0.07, +0.14] | 5.28 P | N +0.06 [+0.05, +0.08] | 5.26 P | N +0.73 [+0.69, +0.77] | 5.30 P |
| TN | 1.01 | 2.62 | N +0.16 [+0.14, +0.19] | 2.64 P | N +0.07 [+0.06, +0.08] | 2.63 P | N +0.70 [+0.66, +0.73] | 2.64 P |
| RB | 7.17 | 5.02 | N +0.02 [+0.02, +0.03] | 7.47 P | N +0.03 [+0.01, +0.03] | 6.20 P | not in session (96) | — |
| HO | 12.30 | 8.61 | N +0.03 [+0.02, +0.04] | 15.35 P | N +0.03 [+0.01, +0.04] | 12.21 P | N +0.17 [+0.14, +0.21] | 22.32 P |
| BZ | 2.84 | 4.74 | N +0.11 [+0.10, +0.13] | 5.20 P | N +0.04 [+0.03, +0.05] | 4.81 P | not in session (93) | — |
| PL | 8.02 | 6.68 | N +0.04 [+0.03, +0.05] | 9.28 P | N +0.02 [+0.02, +0.04] | 7.47 P | N +0.15 [+0.13, +0.18] | 13.05 P |
| PA | 2.96 | 24.64 | N +0.05 [+0.04, +0.07] | 29.18 P | N +0.03 [+0.02, +0.04] | 27.75 P | N +0.09 [+0.07, +0.10] | 43.51 P |
| 6E | 1.21 | 1.26 | N +0.05 [+0.03, +0.08] | 1.31 M | N +0.14 [+0.11, +0.16] | 1.31 M | N +0.03 [+0.00, +0.07] | 1.41 M |
| 6J | 1.16 | 1.20 | N +0.07 [+0.05, +0.09] | 1.25 M | N +0.09 [+0.06, +0.10] | 1.25 M | **T** -0.06 [-0.10, -0.01] | 1.29 M |
| 6B | 1.20 | 1.25 | N +0.04 [+0.02, +0.06] | 1.31 M | N +0.09 [+0.07, +0.11] | 1.30 M | U -0.01 [-0.05, +0.02] | 1.38 M |
| 6A | 1.30 | 1.09 | N +0.05 [+0.03, +0.07] | 1.14 M | N +0.10 [+0.08, +0.13] | 1.13 M | N +0.06 [+0.03, +0.11] | 1.14 M |
| 6C | 1.15 | 0.96 | N +0.04 [+0.02, +0.06] | 1.03 M | N +0.10 [+0.07, +0.13] | 1.01 M | U +0.05 [-0.01, +0.11] | 1.06 M |
| 6S | 1.82 | 1.89 | N +0.09 [+0.07, +0.11] | 2.03 P | N +0.10 [+0.07, +0.14] | 1.99 M | N +0.32 [+0.28, +0.36] | 2.32 P |
| ZC | — | — | N +0.13 [+0.09, +0.17] | 2.16 P | not in session (0) | — | not in session (0) | — |
| ZS | — | — | N +0.12 [+0.09, +0.15] | 2.43 P | not in session (0) | — | not in session (0) | — |
| ZW | — | — | N +0.13 [+0.10, +0.15] | 2.47 P | not in session (0) | — | not in session (0) | — |
| ZL | — | — | N +0.07 [+0.04, +0.11] | 1.59 M | not in session (0) | — | not in session (0) | — |
| ZM | — | — | N +0.11 [+0.08, +0.14] | 1.96 M | not in session (0) | — | not in session (0) | — |
| LE | — | — | not in session (0) | — | not in session (0) | — | not in session (0) | — |
| HE | — | — | not in session (0) | — | not in session (0) | — | not in session (0) | — |
| NKD | 2.59 | 10.79 | N +0.13 [+0.09, +0.16] | 12.75 P | N +0.04 [+0.02, +0.05] | 10.92 P | N +0.08 [+0.06, +0.11] | 22.40 P |
| BTC | 7.42 | 30.91 | N +0.05 [+0.04, +0.07] | 35.01 P | N +0.06 [+0.05, +0.07] | 34.58 P | N +0.10 [+0.08, +0.13] | 37.31 P |
| MBT | 3.51 | 0.58 | N +0.06 [+0.05, +0.08] | 0.60 F | N +0.08 [+0.06, +0.11] | 0.59 F | N +0.39 [+0.34, +0.42] | 0.75 F |

T = TROUGH, N = NOT A TROUGH, U = UNRESOLVED; H0: P PASS (R ≥ 2), M MARGINAL, F FAIL (R < 1).

