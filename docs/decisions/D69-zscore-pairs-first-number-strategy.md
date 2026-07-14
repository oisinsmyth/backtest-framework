# D69 — Z-score pairs as the first-number strategy; "walk-forward" read as trailing-only simulation

**Status:** Committed
**Date:** 2026-07-14
**Category:** Signals & strategy interface
**Source:** Implementation session (Step 6)

## Decision

`strategies.zscore_pairs.ZScorePairsStrategy` is the strategy behind the first real
number: spread = ln(A) − ln(B) with a **fixed 1:1 log-hedge**, rolling z-score over
the `lookback` spreads ending at the **previous** bar (honoring D44's
estimate-up-to-the-previous-bar rule even though engine-level warm-up enforcement is
still future work), entry/exit thresholds with a hysteresis band (hold the current
side between exit_z and entry_z — small per-run mutable state, which is why the sweep
takes factories, D68), warm-up and zero-std self-guards. First-number parameters —
lookback 60, entry 2.0, exit 0.5, ±100%/leg — chosen a priori, not tuned.

**Gate reading (same discipline as D53/D66):** Step 6's "XLE/XOP walk-forward" is
satisfied by bar-by-bar forward simulation with trailing-only data, structurally
enforced by DataView (D32/D56). This strategy has **no fitting step** — the 1:1 hedge
is fixed precisely so that nothing is estimated — and Step 12's train/test window
machinery exists to guard *fitted* parameters. With nothing fitted, there is nothing
to walk forward from; the machinery arrives with pair selection (D22/D28/D29).

## Rationale

The first real number needed a strategy that actually trades on data (the
ScheduledWeightStrategy toy scripts its weights and would make the sweep
meaningless), but anything smarter — estimated hedge ratios, cointegration tests,
parameter tuning — creates fitted parameters that honestly require Step 12's
machinery, which R1 forbids building before the first number exists. Fixed-parameter
z-score mean reversion is the largest strategy that creates no fitting obligation.
Its hyperparameters being a-priori (and stated as such in the results doc) is what
keeps "no train/test split" honest rather than convenient.
