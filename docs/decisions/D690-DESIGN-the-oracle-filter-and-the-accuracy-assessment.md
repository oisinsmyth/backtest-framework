# D690 DESIGN — the oracle filter and the accuracy assessment: a yardstick for every expected-profit filter, first applied to D689's candidate trades

*2026-09-29. Committed before its runner's output is read.*
- **Library, tests and runner:** committed as `cc7a69bc`, with every statistic and rule declared in the runner's
  docstring.
- **The run:** one run was started after that commit. Its result follows as a separate record.
- **What it is:** post hoc on spent in-sample data (2016-01-05 → 2023-12-29), a method and a diagnostic, not a
  verdict.

The principal: "We need a better way to filter for profits, make an oracle filter and the accuracy assessment."

## 1. Why

Every strategy here carries an expected-profit filter (k = 2 × cost), and the filters have been designed by
judgement, not assessed.
- D689's filter scaled its projection with the size of the last move. It kept the trades that lost (−$91 a full-ES
  trade), because that edge lives in the sign, not the magnitude.
- Nothing measured how much a perfect filter could earn, or how accurate a real one would have to be before it pays.

## 2. The library: `backtest_framework.validation.filter_oracle`

Stdlib and numpy only; every guard raises. Twelve unit tests in `tests/unit/test_filter_oracle.py`.

1. **The oracle filter:** take a candidate iff its realised net is above zero (`oracle_take`), or iff its gross is at
   least k × cost (`oracle_take_threshold`). It is hindsight: the ceiling, never a strategy.
2. **The partial oracle** (after D668's size oracle): a forecast with a chosen normal-score correlation ρ to the
   realised outcome. ρ = 0 is a random filter (the null) and ρ = 1 is the oracle. The curve of what the top q of
   candidates earn against ρ answers **how accurate a filter must be before it pays.**
3. **The accuracy assessment** (`assess`, `calibration`), scoring a real filter against the oracle:
   - the confusion matrix (precision, recall, F1, balanced accuracy);
   - the AUC;
   - the Spearman of its score with the outcome, which places it on the curve;
   - its capture of the oracle's net;
   - its calibration: an honest projection has a realised-on-projected slope of 1.

## 3. The first application (`scripts/diag_d690_oracle_filter.py`)

- **The candidates:** every hourly continuation on every day (10:30–14:30, following the last 60 minutes), at full
  ES and MES, after a 250-session burn-in.
- **Declared parts:**
  - **A:** the oracles and a size-only oracle.
  - **B:** the partial-oracle curves for the gross and for size, at q = 20% and 40%, with 200 draws each.
  - **C:** five prior-only walk-forward filters, each assessed as above, with its books and a day-rotation null. They
    are the regime gate, D689's π·|m|, linear expected profit, logistic, and regime-cell expected profit.
- **"Better than the regime gate"** means a higher full-ES daily net Sharpe AND above the p95 of the filter's own
  rotation null. No threshold is tuned after the run.
