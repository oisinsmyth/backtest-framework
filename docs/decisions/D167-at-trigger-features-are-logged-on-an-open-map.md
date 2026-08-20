# D167 — At-trigger features are logged on an open map, computed at the trigger bar, and never imputed

**Status:** Committed
**Date:** 2026-08-21
**Category:** Diagnostics & reporting
**Source:** Phase 1.1 session (feature-analysis pass)

## Decision

`TradeEpisode` gains `features: Mapping[str, float | None]` — an open, F-numbered map
rather than named columns. `extract_episodes` takes an optional `features_at` callback
invoked with the **trigger index**, defined as `entry_index - 1`. A new
`research/feature_analysis.py` ranks trade outcomes by feature and issues a verdict per
feature. None of it can change a fill, a weight or a cost, and none of it enters the DSR
trial pool.

Three conventions are pinned:

1. **`None` means unavailable, and is never imputed.** An absent key means the feature
   was not computed for that run at all — a different statement from a computed `None`.
2. **Blocked features are logged as blocked**, with the reason recorded in
   `FEATURE_UNAVAILABLE`, rather than omitted.
3. **Features are computed at the trigger bar, not the entry bar.**

## Rationale

**Why an open map.** The terrain addon (`TERRAIN_MODEL.md`) states as a forward-
compatibility requirement that "per-trade diagnostics schema must accept additional named
features without migration (F-numbering is open-ended)", and it continues the numbering
at F7/F8/F9. Phase 1 shipped `TradeEpisode` as a frozen dataclass with fixed fields, so
every new feature would have been a schema change rippling through the summary payload,
the registry metrics and the golden masters. A map makes a new feature a new key.
`DiagnosticsSummary` is deliberately *not* given the same treatment — its `to_metrics()`
coerces every field to `float` for the registry, and features are per-trade, not
per-variant.

**Why the trigger bar, emphatically.** Fills are next-open (D103): a decision taken on
bar t's close fills at bar t+1's open, so an episode whose `entry_index` is t+1 was
triggered by bar t. Computing a feature on the entry bar would read a bar the strategy
had not seen when it decided — a one-bar look-ahead living inside the diagnostics, where
no property test would catch it because the diagnostics do not feed the engine. It would
not corrupt any P&L number; it would corrupt every conclusion drawn about which triggers
were good, which is the entire purpose of the exercise. This is the single most
error-prone line in the feature work and it is why it is stated twice in code and once
here.

**Why logging is free.** `BREAKOUT_REVERSAL_FEATURES.md` is explicit that logging carries
no multiplicity cost and that promotion to a live filter is a separate, later exercise
with its own TrialRegistry accounting. So the feature verdicts are `CANDIDATE` or `NO`,
never `ADOPTED`, and the module's docstring says so. The promotion criteria have three
legs — monotonic, stable, and a plateau over the feature's own threshold — and this pass
tests only the first two. The third needs threshold sweeps, which *would* cost
multiplicity, so it is deliberately not run here.

**Why the verdict thresholds are blunt and fixed.** `|rho| >= 0.2`, sign agreement across
the two halves of the sample, and at least 4 of 5 monotone quintile steps. These are
stated up front rather than searched, because a threshold search over a few dozen trades
is how a null result is converted into a finding. A feature that needs a finer threshold
than this to look good has not been found.

## Consequences

- The terrain addon's F7/F8/F9 can be annotated onto existing trade logs with no schema
  migration, which is what its WP5 assumes.
- Two of six features are reported blocked rather than dropped: **F2** (trigger volume
  ratio) hits the same D111 `Bar`-schema gap that blocks the volume-confirmation filter,
  which is now the second independent place that gap has bitten and is the strongest
  argument yet for closing it; **F5** (leverage decomposition) has no derivatives
  plumbing.
- **F6 is half-computable, and the report says which half.** On daily bars with a 00:00
  UTC boundary every close sits exactly on a perp funding stamp (00/08/16 UTC), so the
  funding-proximity component is identically zero and carries no information at this
  frequency. Only the options-expiry component varies. This is a limitation of the bar
  clock, not of the idea, and it would resolve at intraday frequency.
- The sample is thin — a few dozen closed trades per symbol — so trades are pooled across
  symbols on the baseline variant, and every table prints its bucket counts. Pooling is
  defensible because the configuration is identical across symbols and F4's hypothesis is
  cross-sectional to begin with; it does not make the sample large.
