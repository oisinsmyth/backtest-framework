# Pairs Study v3 — β-hedged trading

**Date produced:** 2026-07-14 · **Snapshot:**
`54d4e476c0560d473fc1539e8540e0fa1ab371a69dad2f02b9bc6eae9cd671fd` · **Universe/windows/selection: identical to
[v2](pairs_study_v2.md)** — one variable changed (D94): each pair now TRADES its
train-window Engle-Granger β instead of the fixed 1:1 hedge. Spread = ln A − β·ln B;
legs sized in the β ratio with weights normalized to constant gross
2·leg_weight = 2 (w_A = 2w/(1+β), w_B = 2wβ/(1+β)), so
gross exposure — and therefore the risk being compared — matches v1/v2 exactly.
β = 1 provably reduces to v1/v2's strategy (tested identity). **Trials logged:**
175 (`data/pairs_study_v3_registry.sqlite`).

## The sweep (D8)

| Cost multiplier | Final NAV | Net P&L | Return | Max drawdown |
|---|---|---|---|---|
| 0× | 106,122.52 | +6,122.52 | +6.12% | 9.11% |
| 0.5× | 94,203.62 | -5,796.38 | -5.80% | 12.01% |
| 1× | 83,468.04 | -16,531.96 | -16.53% | 18.39% |
| 2× | 65,075.08 | -34,924.92 | -34.92% | 35.84% |
| 4× | 38,199.50 | -61,800.50 | -61.80% | 62.08% |

## v1 → v2 → v3 (one variable per step)

| | v1 (Gatev, 1:1 hedge) | v2 (coint. selection, 1:1 hedge) | v3 (coint. selection, β hedge) |
|---|---|---|---|
| 0× | +3.45% | +19.03% | +6.12% |
| 0.5× | -5.01% | +5.70% | -5.80% |
| 1× | -13.01% | -6.43% | -16.53% |
| 4× | -49.91% | -56.81% | -61.80% |

v1→v2 isolated selection; v2→v3 isolates the hedge. The measurement: whether
trading the fitted β beats trading 1:1 on the same pairs — β estimation noise is
part of that measurement, not a confound (the fit is honest train-window-only,
applied out-of-sample, D22).

**Finding: β-hedging hurt, at every cost level.** Gross falls from v2's +19.03%
to +6.12%; at real costs the loss deepens from −6.43% to
-16.53%. Since selection, windows, costs, and gross exposure are all held
fixed, the delta prices exactly one thing: a train-window β carried out-of-sample
is noisier than it is helpful on this universe. The pairs the selector admits
already have β ≈ 1 (the [0.7, 1.3] coherence window), so the hedge's room for
benefit was small by construction, while the estimation error it imports is not.
The 1:1 hedge is the better trade here — an estimation-error result, and a real
finding for the Phase G writeup, not a failure of the study.

## Tearsheet at 1× (real costs)

| Metric | Value |
|---|---|
| Sharpe (rf=4.00%/yr, 252 periods/yr) | -1.116 |
| Sortino (rf=4.00%/yr) | -1.521 |
| Max drawdown | 18.39% |
| Realised beta vs benchmark | +0.0954 (market-neutral expectation: ≈ 0, D37) |
| VaR 95% (daily) | 0.44% |
| CVaR 95% (daily) | 0.80% |

Block bootstrap (n=10,000, block=20, seed=0 — D34/D36):
| | p5 | p25 | p50 | p75 | p95 |
|---|---|---|---|---|---|
| Terminal return | -32.20% | -22.75% | -15.68% | -8.00% | +4.23% |
| Max drawdown | 10.63% | 16.45% | 21.75% | 27.27% | 35.42% |

## Deflated Sharpe Ratio (D21/D86/D90)

- Observed stitched Sharpe (daily, rf 4%): -0.0703
  over T = 2,205 OOS bars; skew 0.28,
  kurtosis 28.44.
- **DSR = 0.0000** — N and V pulled from this study's TrialRegistry.
- **Program-level multiplicity (D90, extended):** the research program has now run
  THREE studies of 175 logged trials each, every window scoring
  1,596 candidates. Registry-N per study understates
  both the cross-study count and the selection breadth, so any DSR here is
  optimistic: DSR < 0.95 read as "no demonstrated edge" remains the only safe
  reading; a DSR ≥ 0.95 could not be taken at face value.

## Standing caveats

Unchanged from v2 (σ/ADV full-sample calibration D66; single-source data D26;
XLF-spinoff-as-split encoding D88; fixed-lag no-constant ADF rank D93). New in v3:
β is a fitted parameter carried out-of-sample per window — its estimation error is
part of the strategy, and the v2→v3 delta prices exactly that trade-off (D94).

## Reproduction

`uv run python scripts/run_pairs_study_v3.py` — offline, deterministic. Strategy
mechanics tested in `tests/unit/test_beta_zscore.py` (incl. the β=1 → v2-strategy
identity); the factory wiring and the β=1 whole-study equivalence in
`tests/integration/test_pairs_study.py`.
