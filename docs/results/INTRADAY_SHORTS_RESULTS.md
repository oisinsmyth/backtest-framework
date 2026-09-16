# D247 — the short side of S1 and S2 at fifteen minutes

**A BASELINE, EXPECTED NEGATIVE.** The long cells are controls, not candidates.

*seed 0, 1,000 rotations, 797.3s. 57 ETFs x 55,726 bars over 2,156 sessions (25.85/session, PPY 6513); warm-up 1,000 bars = 39 sessions, live 8.40 years. 2018-01-02 .. 2026-08-26.*

**Calendar mismatch, declared before the run:** S1's 34-bar Impulse is **1.3 sessions** here against seven weeks daily; S2's 252-bar regression is **9.8 sessions** against a year. These are the same estimators at a radically shorter horizon.

## The eight cells

| | | long | short | excess Sharpe | CAGR | max DD | turnover/yr | borrow/yr | E |
|---|---|---:|---:|---:|---:|---:|---:|---:|:--:|
| **S1_short_cont** | S1 mirror, short, holds overnight | 0.0% | 27.2% | **-1.248** | -6.48% | -45.07% | 208 | 0.32% | ✓ |
| **S1_short_intra** | S1 mirror, short, flat at every close | 0.0% | 25.9% | **-1.550** | -5.55% | -40.66% | 334 | 0.00% | ✓ |
| **S2_short_cont** | S2 downtrend, short, holds overnight | 0.0% | 12.4% | **-0.784** | -2.44% | -21.05% | 27 | 0.12% | ✓ |
| **S2_short_intra** | S2 downtrend, short, flat at every close | 0.0% | 11.9% | **-1.113** | -2.51% | -19.86% | 87 | 0.00% | ✓ |
| **S1_long_cont** | *S1 long — control* | 22.6% | 0.0% | **-0.279** | -1.37% | -24.04% | 181 | 0.00% | ✓ |
| **S1_long_intra** | *S1 long, intraday — control* | 21.6% | 0.0% | **-0.586** | -1.98% | -20.97% | 285 | 0.00% | ✓ |
| **S2_long_cont** | *S2 long — control* | 12.9% | 0.0% | **+0.191** | +1.13% | -8.26% | 28 | 0.00% | ✓ |
| **S2_long_intra** | *S2 long, intraday — control* | 12.4% | 0.0% | **-1.209** | -1.96% | -15.69% | 91 | 0.00% | ✓ |
| *B&H* | *always long* | *100.0%* | *0.0%* | *+0.289* | *+9.02%* | *-35.78%* | *0* | *0.00%* | — |

## Hurdles — the four short cells

| | Q1 >0 | Q2 rotation null | pctile | Q3 boot p05 | best-of-4 | **all** |
|---|:--:|:--:|---:|---:|:--:|:--:|
| **S1_short_cont** | ✗ | ✓ | **100.0th** | -1.806 ✗ | ✗ | **✗** |
| **S1_short_intra** | ✗ | ✓ | **100.0th** | -2.100 ✗ | ✗ | **✗** |
| **S2_short_cont** | ✗ | ✓ | **96.3th** | -1.337 ✗ | ✗ | **✗** |
| **S2_short_intra** | ✗ | ✓ | **99.6th** | -1.710 ✗ | ✗ | **✗** |

*Best-of-four floor (D228, one shared offset vector): **+0.315**.*

## The long controls — do the estimators survive this horizon at all?

| | excess Sharpe | rotation null pctile | clears Q2 |
|---|---:|---:|:--:|
| **S1_long_cont** | -0.279 | 99.4th | ✓ |
| **S1_long_intra** | -0.586 | 100.0th | ✓ |
| **S2_long_cont** | +0.191 | 81.5th | ✗ |
| **S2_long_intra** | -1.209 | 0.0th | ✗ |

## Costs — the predicted verdict

| | turnover/yr | **breakeven bp/side** | charged | headroom |
|---|---:|---:|---:|---:|
| **S1_short_cont** | 208 | **-1.55** | ~1.6 | -0.97x |
| **S1_short_intra** | 334 | **0.13** | ~1.6 | 0.08x |
| **S2_short_cont** | 27 | **-7.71** | ~1.6 | -4.82x |
| **S2_short_intra** | 87 | **-1.05** | ~1.6 | -0.66x |
| **S1_long_cont** | 181 | **0.60** | ~1.6 | 0.38x |
| **S1_long_intra** | 285 | **0.86** | ~1.6 | 0.54x |
| **S2_long_cont** | 28 | **4.08** | ~1.6 | 2.55x |
| **S2_long_intra** | 91 | **-0.87** | ~1.6 | -0.54x |

*Breakeven below ~1.6 bp means costs alone sink the cell, before any signal question arises.*

## What the shorted bars actually returned

*D244's lesson: a null can be beaten or lost by drift structure alone, so this is measured before any null result is interpreted.*

| bars held by | count | annualised return of those bars |
|---|---:|---:|
| ALL BARS | 3,119,382 | **+9.02%** |
| S1_short_cont | 847,362 | **+4.72%** |
| S1_short_intra | 808,634 | **-4.27%** |
| S2_short_cont | 385,404 | **+9.52%** |
| S2_short_intra | 370,504 | **+4.53%** |

**This is the finding.** The intraday-only S1 short holds bars returning **−4.27%/yr** against the continuous version's **+4.72%** — an **8.99-point swing**, close to the +8.55 predicted from the overnight/intraday decomposition. **It is the first construction in this programme to isolate bars that actually fall.** It still loses, because turnover costs five times the gross edge.

## The reading

> **THE LONG CONTROLS HOLD AND THE SHORTS DO NOT -- a direction result, and informative.**


*The auto-generated line above is too crude and is corrected in [D247](../decisions/D247-the-short-side-at-fifteen-minutes.md): it counts a long control as "holding" if it merely beats its rotation null, and S1's longs do that at **−0.279** and **−0.586** excess Sharpe. **Seven of eight cells lose money.** The honest reading is that 15-minute sampling breaks both estimators in both directions.*

