# Pairs Study v1 — walk-forward Gatev/z-score over a 57-ETF universe

**Date produced:** 2026-07-14 · **Snapshot:**
`54d4e476c0560d473fc1539e8540e0fa1ab371a69dad2f02b9bc6eae9cd671fd` (content-addressed, reproducible from the committed
`universe_daily_2015_2024_raw.csv.gz`) · **Universe:** 57 ETFs, 2015–2024 daily · **Windows:**
35 (train 252, test 63) ·
**Selection:** Gatev top-5 of **1,596
pairs per window** · **Trials logged:** 175
(`data/pairs_study_v1_registry.sqlite`).

The first Phase G research artifact. Pipeline provenance: cleaning made
0 change(s); validation passed with
43 warning(s); 14 splits (incl. OIH 1-for-20, USO 1-for-8) and 2,285
dividends handled as events (D75).

## Strategy (study v1)

Z-score mean reversion on each selected pair (fixed 1:1 log-hedge, lookback
30, entry 2.0, exit 0.5, ±100%
per leg), top-5 pairs traded simultaneously in ONE portfolio per window —
shared legs net internally (D27). Windows chain: each starts with the previous
window's ending NAV. Cointegration tests and Kalman hedge ratios are future study
versions, deliberately not v1.

## The sweep (D8)

| Cost multiplier | Final NAV | Net P&L | Return | Max drawdown |
|---|---|---|---|---|
| 0× | 103,445.43 | +3,445.43 | +3.45% | 4.08% |
| 0.5× | 94,987.93 | -5,012.07 | -5.01% | 7.24% |
| 1× | 86,987.86 | -13,012.14 | -13.01% | 13.91% |
| 2× | 72,947.01 | -27,052.99 | -27.05% | 27.24% |
| 4× | 50,094.20 | -49,905.80 | -49.91% | 49.91% |

## Tearsheet at 1× (real costs)

| Metric | Value |
|---|---|
| Sharpe (rf=4.00%/yr, 252 periods/yr) | -3.029 |
| Sortino (rf=4.00%/yr) | -3.807 |
| Max drawdown | 13.91% |
| Realised beta vs benchmark | +0.0199 (market-neutral expectation: ≈ 0, D37) |
| VaR 95% (daily) | 0.15% |
| CVaR 95% (daily) | 0.28% |

Block bootstrap (n=10,000, block=20, seed=0 — D34/D36):
| | p5 | p25 | p50 | p75 | p95 |
|---|---|---|---|---|---|
| Terminal return | -19.92% | -15.66% | -12.68% | -9.63% | -5.21% |
| Max drawdown | 7.78% | 11.42% | 14.15% | 16.93% | 20.93% |

## Deflated Sharpe Ratio (D21/D86/D90)

- Observed stitched Sharpe (daily, rf 4%): -0.1908
  over T = 2,205 OOS bars; skew -0.07,
  kurtosis 30.13.
- **DSR = 0.0000** — N and V[{SRn}] pulled from this study's TrialRegistry
  (175 logged backtests), never typed in.
- **Multiplicity caveat (D90):** registry-N counts logged backtests, but each window
  *scored 1,596 candidate pairs* to pick its top
  5 — selection breadth the registry-N does not capture, so even this
  DSR is optimistic. Interpreting DSR < 0.95 as "no demonstrated edge" is therefore
  conservative in the safe direction; interpreting DSR ≥ 0.95 would NOT be.

## Standing caveats (R3)

1. σ/ADV impact params are full-sample calibrated (D66) — documented look-ahead in
   cost parameters, not signal.
2. Single-source data (yfinance); event tables trusted after internal frame checks
   (D75); second-source cross-check remains deferred (D26).
3. Study v1 signal is the simplest honest one; richer signals are future versions.
4. XLF's 2016 "split" (ratio 1.231) is yfinance's encoding of the XLRE spin-off —
   handled mechanically as a split; economically approximate.

## Reproduction

`uv run python scripts/run_pairs_study.py` — offline, deterministic; recreates the
same content-addressed snapshot and identical numbers. Study mechanics are tested in
`tests/integration/test_pairs_study.py`.
