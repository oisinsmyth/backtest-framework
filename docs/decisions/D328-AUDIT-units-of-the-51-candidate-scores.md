# D328 AUDIT — what units does each of the 51 candidate scores carry?

**Status:** CODE AUDIT. No data was run. Every entry is read from the estimator
source and cites it.
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. Why

D328 found that `macd_hist` is computed on **raw dollar closes** and that its
extreme ranks are therefore a price sort — $2,706 at one end, $3,020 at the
other, $22 in the middle — with a compounded extreme-rank spread of **+18 bp**
carrying **146 bp** of round trip (FINDINGS §14). The test is free and
dimensional: *before ranking a score across names, ask what units it carries.*
This applies it to every one of D290's 51.

## 1. Verdict

**Three scores carry dollar units by accident, all in axis A, all from
`research/macd.py` on raw closes.** Two more carry units **by design**, one of
which is the known-bad control. The remaining 46 are dimensionless.

| score | axis | construction | units | verdict |
|---|---|---|---|---|
| **`macd_line`** | A | `ema(12) − ema(26)` on raw closes (`macd.py:185–214`, `zero_line_score` returns `series.macd`) | **$** | **BUG** — ranks price |
| **`macd_hist`** | A | `macd − signal`, same series (`signal_line_score` returns `series.histogram`) | **$** | **BUG** — D328's case |
| **`impulse_nodz`** | A | `zlema(hlc3) − smma(close)` on raw H/L/C (`macd.py:484–489`, `impulse_no_deadzone_score`) | **$** | **BUG** — ranks price |
| `amihud_21` | G | mean of `|r| / (shares × close)` (`ragged_anomaly_scores.py:238–241`) | **1/$** | by design — it *is* dollar-volume illiquidity |
| `price_log` | G | `log(close)` (`ragged_anomaly_scores.py:223`) | log $ | by design — the control |

**`hist_L` and `md` are the same impulse-MACD family as `impulse_nodz` but
built on `log(high)`, `log(low)`, `log(close)`** (`run_activation_threshold.py:69–77`,
`log_parts`). The codebase has both the scale-free and the dollar-denominated
version of the same instrument, and D290 screened them side by side without the
difference being stated.

## 2. The 46 dimensionless scores, by axis

| axis | scores | why dimensionless |
|---|---|---|
| A | `hist_L`, `md`, `trailing_return`, `rsi` | log-price MACD; `close(t)/close(t−37) − 1`; Wilder RSI |
| B (7) | `upper_wick`, `lower_wick`, `wick_asym`, `body_frac`, `close_in_range`, `range_frac`, `gap_frac` | every one is a ratio of prices or of a range to a price (`ragged_features.py:210–216`) |
| C (5) | `rel_vol`, `vol_z`, `dollar_vol`, `vol_trend`, `signed_vol` | `rel_vol` is `log(vol) − median(log vol)`, a log ratio; **`dollar_vol` is `log(vol × px) − median`, a log ratio too, not a level** (`ragged_features.py:114–138`); the rest derive from `rel_vol` |
| D (4) | `dist_hvn`, `dist_lvn`, `mass_here`, `mass_imbalance` | distances in bucket widths of ATR; fractions (`ragged_profile.py:181–195`) |
| E (5) | `atr_norm`, `cs_spread`, `rvol21`, `vol_ratio`, `range_over_atr` | true range **divided by prev close** (`ragged_vol_scores.py:136`); Corwin-Schultz is a fraction; vols of log returns; ratios |
| F (5) | `on_mean`, `id_mean`, `on_share`, `on_minus_id`, `on_persist` | returns and ratios of returns |
| G (8) | `max_ret_21`, `ivol_21`, `beta_63`, `rev_5`, `rev_21`, `mom_252_21`, `skew_63`, `dist_52w_high` | returns, moments of returns, `log(c / hi)` |
| H (8) | `fvg_dist`, `fvg_signed`, `struct_trend`, `retrace_leg`, `choch_dist`, `park_vol_21`, `gk_minus_cc`, `gap_reversal` | log-price distances; a state; `(close − lo)/(hi − lo)`; `log(close / level)`; vols; a ratio of two returns (`ragged_structure_scores.py:150–243`) |

## 3. A second category, which is not a bug and must not be read as one

**Dimensionless is not tilt-free** (FINDINGS §14: `hist_L` is scale-free and
still holds $8–10 names at 4× the spread). Several of the 46 rank a nuisance
**deliberately**, because the nuisance is the axis:

- **Volatility, by construction:** `atr_norm`, `rvol21`, `park_vol_21`,
  `range_over_atr`, `ivol_21`, `max_ret_21`, `cs_spread`. Ranking these ranks
  volatility and therefore cheapness and spread. That is what axis E is *for*.
- **Liquidity, by construction:** `rel_vol`, `vol_z`, `dollar_vol`, `amihud_21`.

For these the D328 tilt screen — common-mode half-spread at the traded ends
against the universe median — is not a defect detector; it is a *cost
statement*. The question for them is whether the edge pays the tilt's cost, and
that is a book question, not a units question.

## 4. What follows

1. **`macd_line`, `macd_hist`, `impulse_nodz` were screened in D290, and
   `macd_hist` was a D325 PAIR, as price sorts.** Their D290 outcomes and
   D325's composite result must be re-read knowing that. The direct test is to
   normalise all three — by price or by ATR, declared in advance — and re-run
   the composites; FINDINGS §14 says why.
2. **A units check belongs in the score-cache builder**, not in a decision
   record. `d290_build_cache.py` could assert, per score, that multiplying every
   close by 10 leaves the score bit-identical (or shifts a log score by a
   constant). Three scores would have failed on the first run.
3. **`impulse_nodz` and `hist_L` are the same instrument in different units.**
   Whatever `impulse_nodz` showed in D290 relative to `hist_L` is the units
   difference, not a signal difference.

## 5. Files

Source read: `src/backtest_framework/research/macd.py`,
`scripts/run_activation_threshold.py`, `scripts/ragged_features.py`,
`scripts/ragged_profile.py`, `scripts/ragged_vol_scores.py`,
`scripts/ragged_session_scores.py`, `scripts/ragged_anomaly_scores.py`,
`scripts/ragged_structure_scores.py`, `scripts/d290_build_cache.py`.
