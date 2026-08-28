# D242 — the uptrend arm and the combined book on withheld data

**STAGE 2 — THE VERDICT.** 60 ETFs sharing zero tickers with the mined 57.

*seed 0, 1,000 sims, 22.7s. 60 ETFs x 1,515 live bars, 2018-12-21 .. 2024-12-30. Every constant frozen and asserted against the mined runner.*

**What this cannot show, stated before the run:** the two universes correlate **+0.978** and both sit inside the 2018–2024 market. This is an **instrument** holdout, not a time holdout.

## The books on withheld data

| | exposure | excess Sharpe | *mined* | shrinkage | CAGR | deployable | max DD | Calmar | E |
|---|---:|---:|---:|---:|---:|---:|---:|---:|:--:|
| **S1** | 19.7% | **+0.779** | — | — | 5.49% | 8.87% | -9.04% | 0.607 | ✗ |
| **A0** | 13.9% | **+0.672** | *+0.610* | +10.1% | 2.38% | 5.89% | -4.40% | 0.541 | ✗ |
| **A2** | 12.5% | **+0.699** | *+0.822* | -15.0% | 2.09% | 5.66% | -2.71% | 0.771 | ✗ |
| **C0** | 31.1% | **+0.873** | — | — | 7.13% | 10.07% | -9.52% | 0.749 | ✗ |
| *B&H* | *100.0%* | *+0.230* | — | — | *8.34%* | *8.34%* | *-37.92%* | *0.220* | — |

## H1–H3 — the entry rules

*H3's floor is **+0.147** — 25% of the mined delta, set the way D237 set its own.*

| | excess Sharpe | Δ vs B&H | rot null p95 | percentile | money pct | H1 | H2 | H3 | **all** |
|---|---:|---:|---:|---:|---:|:--:|:--:|:--:|:--:|
| **A0** | +0.672 | **+0.442** | +0.487 | **99.7th** | 99.9th | ✓ | ✓ | ✓ | **✓** |
| **A2** | +0.699 | **+0.469** | +0.499 | **99.6th** | 99.9th | ✓ | ✓ | ✓ | **✓** |

## H4 — did the −8% stop's edge replicate?

*R7's matched-exit-count overlay null: keep A0's book, cut the same number of trades short at random trades and random points inside their own spans. Kept separate from H1–H3 so that "the entry replicated" and "the stop replicated" cannot be conflated.*

| trades cut | actual | null p50 | null p95 | **percentile** | H4 |
|---:|---:|---:|---:|---:|:--:|
| 57 of 241 | **+0.699** | +0.667 | +0.765 | **71.7th** | ✗ |

## H5 / H6 — the combined book

| | excess Sharpe |
|---|---:|
| S1 alone | +0.779 |
| **C0 combined** | **+0.873** |
| **delta** | **+0.094** |
| bootstrap p05 | -0.104 |
| bootstrap p95 | +0.276 |
| **H5** (point estimate) | **✓** |
| **H6** (interval) | **✗** |

**ρ between S1 and A2 on this fixture: `+0.1749`** (mined: +0.1586).

## The reading, as declared in advance

> **THE STRONGEST RESULT THE PROGRAMME HAS PRODUCED. Still one era and a +0.978-correlated universe -- the next step is more forward time, not capital.**

