# D122 — The BTC/ETH pairs study gets its own harness; `ZScorePairsStrategy` is reused unmodified

**Status:** Committed
**Date:** 2026-08-18
**Category:** Validation & research integrity
**Source:** Crypto pairs study session ([`docs/results/crypto_pairs_btc_eth.md`](../results/crypto_pairs_btc_eth.md))

## Decision

`research/crypto_pairs_study.py` is a new study module. It does **not** call
`research.pairs_study.run_pairs_study`, and it does **not** modify, subclass, or wrap
`strategies.zscore_pairs.ZScorePairsStrategy` — that strategy is constructed exactly as
D69 built it, with its `lookback` / `entry_z` / `exit_z` / `leg_weight` fields and nothing
else.

What the study *does* reuse, by import and without edits:

| Piece | From | Why reuse rather than rebuild |
|---|---|---|
| `CostTier`, `DEFAULT_TIERS` | `research.breakout_study` (D114) | the two crypto studies must price fees identically or their fee columns are not comparable |
| `run_benchmark` | `research.breakout_study` (D115) | fixed-quantity buy-and-hold is already correct there; a second implementation is a second chance to get it wrong |
| `recording_cost_stack`, `CostLedger` | `research.capacity` (D95) | per-brick attribution (fees vs borrow vs margin) is the study's most load-bearing table |
| `engle_granger_beta`, `adf_stat` | `research.cointegration` (D92/D93) | the ADF machinery already exists and is anchored against statsmodels |
| `walk_forward_windows`, `run_backtest`, `build_cost_stack`, `TrialRegistry`, `deflated_sharpe_from_trials`, `analytics.metrics` | framework | gate-tested; a study does not get to reimplement them |

## Rationale

**Why not `run_pairs_study`.** It is the right harness for the study it was written for
and the wrong one here, for a reason that is not stylistic. `StudyConfig.cost_stack_config()`
hard-codes the ETF cost stack — IBKR commission, sqrt impact, 1 bp spread, 0.25% borrow,
6% margin, dividend flow — and `run_pairs_study` logs that dict verbatim in every trial.
Running it with an injected `base_stack` (the D95 hook) would have produced trials whose
logged `cost_stack` described bricks that were not the bricks that ran: precisely the
drift D102 exists to close, reintroduced deliberately. The alternatives were to add a
cost-stack hook to `StudyConfig` — a change to an existing interface this study is not
entitled to make — or to write study glue. Study glue is what `research/` is for (D89).

The same argument applies more weakly to the rest of `run_pairs_study`'s shape: it takes
a selector over a universe (there is no selection here, D125), it sweeps cost multipliers
rather than fee tiers (D8's dimension, not this study's), and it chains windows (D123).
Bending it to fit would have left a harness that served neither study well.

**Why the strategy is untouched.** The brief's constraint and this repo's own discipline
point the same way, but there is also a research reason: the study's question is whether
*the existing signal* has an edge on this pair. A strategy modified to suit the data being
tested is not the strategy whose result is being reported. Two things were genuinely
tempting and were not done —

- **A band-rebalance policy.** `ZScorePairsStrategy` emits a target *weight* every bar and
  `Sizer` re-sizes to current NAV (D61), so both legs are rebalanced daily while in a
  trade — the source of the study's ~31× annualised turnover and most of its fee bill. A
  no-trade band around the target would cut that dramatically. It is a strategy change,
  it would need its own decision and its own golden master, and it would make the result
  incomparable to the published v1–v3 artifacts, which share the convention. It is named
  in the artifact's caveats instead.
- **A β-hedged variant.** D94 already built one (`research/beta_zscore.py`) for the ETF
  study. Wiring it in here would have answered a *different* question in the same run, and
  the one-variable-per-study-version rule (D92) says that is a v2, not a footnote. The
  cointegration section names it as the obvious next experiment.
