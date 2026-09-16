# D248 — the strength-filtered intraday short

*seed 0, 1,000 rotations, 582.5s. PPY 6513, normalisation window 1,638 bars (63 sessions). Split at **2022-06-30** — SCREEN 25,734 bars, VALIDATE 26,716.*

*D247's unfiltered reference reproduced at **-1.550**.*

## The three cells

| | exposure | turnover/yr | SCREEN Sharpe | null pctile | breakeven | VALIDATE Sharpe | null pctile | breakeven |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **T05** | 5.3% | 102 | **-1.564** | 90.6th | -0.87 bp | **-1.426** | 100.0th | -0.21 bp |
| **T10** | 10.1% | 169 | **-1.589** | 94.6th | -0.49 bp | **-1.477** | 100.0th | 0.01 bp |
| **T15** | 14.9% | 226 | **-1.439** | 99.3th | -0.07 bp | **-1.602** | 100.0th | 0.01 bp |

*D247 unfiltered, for reference: 25.9% exposure, 334 turnover, −1.550 Sharpe, 0.13 bp breakeven. Charged cost ~1.6 bp/side.*

## Hurdles

| | A1 >0 | A2 null | A3 best-of-3 | A4 cost | **SCREEN** | A5 | A6 | **VALIDATE** |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **T05** | ✗ | ✗ | ✗ | ✗ | **✗** | ✗ | ✗ | **✗** |
| **T10** | ✗ | ✗ | ✗ | ✗ | **✗** | ✗ | ✗ | **✗** |
| **T15** | ✗ | ✓ | ✓ | ✗ | **✗** | ✗ | ✗ | **✗** |

*Best-of-three floor: SCREEN -1.445, VALIDATE -2.284.*

## A7 — does the strength ordering survive out of sample?

*The most informative hurdle. All signal-on intraday bars, bucketed by `z`, unfiltered by any cell — this tests the RELATIONSHIP, not a book.*

| quintile | SCREEN | VALIDATE |
|---|---:|---:|
| Q1 — weakest | -10.10% | +13.86% |
| Q2 | -16.48% | +2.55% |
| Q3 | -8.29% | +2.25% |
| Q4 | -5.28% | -5.08% |
| Q5 — strongest | +10.51% | -3.52% |

**Strictly monotone: SCREEN ✗, VALIDATE ✗.**

## The reading

> **NO CELL SURVIVES. The strength-filtered intraday short is CLOSED per D248's stop: no fourth target, no md_L variant, no re-cut window, no 30-minute bars.**

