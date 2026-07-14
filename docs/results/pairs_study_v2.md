# Pairs Study v2 — cointegration-filtered selection

**Date produced:** 2026-07-14 · **Snapshot:**
`54d4e476c0560d473fc1539e8540e0fa1ab371a69dad2f02b9bc6eae9cd671fd` · **Universe/windows/trading: identical to
[v1](pairs_study_v1.md)** — one variable changed (D92): selection is now Gatev
prefilter (top 50 of 1,596)
→ Engle-Granger β with a coherence window of [0.7, 1.3] (the
strategy trades the 1:1 spread, so β must be near 1) → ADF-statistic rank → top
5. β is logged per selected pair (informing a future β-hedged v3), not
traded. ADF statistic anchored against statsmodels (D93). **Trials logged:**
175 (`data/pairs_study_v2_registry.sqlite`).

## The sweep (D8)

| Cost multiplier | Final NAV | Net P&L | Return | Max drawdown |
|---|---|---|---|---|
| 0× | 119,028.94 | +19,028.94 | +19.03% | 10.86% |
| 0.5× | 105,703.43 | +5,703.43 | +5.70% | 13.52% |
| 1× | 93,570.09 | -6,429.91 | -6.43% | 16.18% |
| 2× | 72,921.94 | -27,078.06 | -27.08% | 28.41% |
| 4× | 43,185.18 | -56,814.82 | -56.81% | 57.00% |

## v1 → v2 (selection is the only change)

| | v1 (Gatev only) | v2 (cointegration-filtered) |
|---|---|---|
| 0× | +3.45% | +19.03% |
| 1× | -13.01% | -6.43% |
| 4× | -49.91% | -56.81% |

## Tearsheet at 1× (real costs)

| Metric | Value |
|---|---|
| Sharpe (rf=4.00%/yr, 252 periods/yr) | -0.978 |
| Sortino (rf=4.00%/yr) | -1.348 |
| Max drawdown | 16.18% |
| Realised beta vs benchmark | +0.0503 (market-neutral expectation: ≈ 0, D37) |
| VaR 95% (daily) | 0.43% |
| CVaR 95% (daily) | 0.73% |

Block bootstrap (n=10,000, block=20, seed=0 — D34/D36):
| | p5 | p25 | p50 | p75 | p95 |
|---|---|---|---|---|---|
| Terminal return | -23.48% | -13.03% | -5.09% | +3.76% | +18.26% |
| Max drawdown | 8.06% | 11.77% | 15.73% | 20.55% | 28.32% |

## Deflated Sharpe Ratio (D21/D86/D90)

- Observed stitched Sharpe (daily, rf 4%): -0.0616
  over T = 2,205 OOS bars; skew 0.41,
  kurtosis 13.51.
- **DSR = 0.0000** — N and V pulled from this study's TrialRegistry.
- **Program-level multiplicity (D90, extended):** the research program has now run
  two studies of 175 logged trials each, every window scoring
  1,596 candidates. Registry-N per study understates
  both the cross-study count and the selection breadth, so any DSR here is
  optimistic: DSR < 0.95 read as "no demonstrated edge" remains the only safe
  reading; a DSR ≥ 0.95 could not be taken at face value.

## Standing caveats

Unchanged from v1 (σ/ADV full-sample calibration D66; single-source data D26;
XLF-spinoff-as-split encoding D88). New in v2: ADF ranking uses a fixed lag order
(1) and the no-constant EG-residual convention — statistic-only,
no p-values, per D29's rank-don't-threshold rule (D93).

## Reproduction

`uv run python scripts/run_pairs_study_v2.py` — offline, deterministic. Selection
mechanics tested in `tests/unit/test_cointegration.py` (incl. exact statsmodels
ADF ties) and `tests/integration/test_pairs_study.py`.
