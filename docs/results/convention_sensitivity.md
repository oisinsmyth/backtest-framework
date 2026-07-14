# Convention sensitivity — how much of the v2 result is convention? (D105)

**Date produced:** 2026-07-14 · **Snapshot:**
`54d4e476c0560d473fc1539e8540e0fa1ab371a69dad2f02b9bc6eae9cd671fd` · **Configuration: identical to [v2](pairs_study_v2.md)**
(cointegration selection, 1:1 hedge, same windows/parameters) — only the two
execution/calibration conventions vary. **Trials logged:**
280
(`data/convention_sensitivity_registry.sqlite`). Baseline anchor: the published
v2 artifact reports +19.03% at 0× and -6.43% at 1×.

## Why this study exists (audit F3/F4)

Every study through v3 fills orders at the close of the bar that generated the
signal — optimistic for mean reversion, since the entry always catches exactly
the close that triggered it — and calibrates sqrt-impact σ/ADV on the full
sample (a documented look-ahead in cost parameters, D66, never in the signal).
D103/D102 added the honest alternatives: next-bar-open fills and per-window
train-slice calibration. This study prices both conventions on the program's
strongest configuration, per the house one-variable-per-study rule.

## The 2×2

| Variant | Fill timing | Impact calibration | 0× return | 1× return | DSR |
|---|---|---|---|---|---|
| baseline | close | full sample | +19.03% | -6.43% | 0.0000 |
| next-open | next open | full sample | +16.79% | -7.90% | 0.0000 |
| train-cal | close | train window | +19.03% | -6.28% | 0.0000 |
| both | next open | train window | +16.79% | -7.76% | 0.0000 |

Reading: the **0× column at next-open prices the fill-timing convention alone**
(no costs, so calibration is irrelevant at 0× — the train-cal 0× row must equal
the baseline 0× row, a built-in cross-check). The **1× rows price the full
stack** under each convention pair; "both" is the fully-conservative cell.

## Interpretation rule (D90/D98)

Per-variant DSRs are computed over each variant's own 1× window trials (N =
35 per variant, daily units). The
program-level multiplicity caveat applies unchanged: DSR < 0.95 read as "no
demonstrated edge" is the only safe reading.

## Reproduction

`uv run python scripts/run_convention_sensitivity.py` — offline, deterministic.
Engine fill-timing semantics are gate-tested (`test_backtest_loop.py`,
`test_simulator_invariants.py`, D103); per-window calibration leak-freedom is
gate-tested (`test_pairs_study.py`, D102).
