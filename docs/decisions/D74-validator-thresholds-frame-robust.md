# D74 — Validator thresholds calibrated to observed data; frame-robust split awareness

**Status:** Committed
**Date:** 2026-07-14
**Category:** Data layer
**Source:** Implementation session (Step 7)

## Decision

`data.validator.validate()` (D26) splits findings into **hard violations**
(quarantine the snapshot) and **warnings** (recorded in meta, never blocking):

- Hard: OHLC inconsistency beyond 1e-9 relative tolerance (the observed XOP
  2018-10-24 artifact, 1.2e-16, passes); non-positive prices; unexplained
  close-to-close moves > 60%.
- Warning: unexplained moves in 25–60%; volume anomalies (zero, or >10× the
  trailing-20-bar median).

**Thresholds are calibrated against observed genuine data, not guessed**: XOP's
2020-03-09 oil-crash day is a real −37% move — a 25% hard threshold would have
quarantined the genuine COVID crash. The cleaner's spike-and-revert rule (D73) has
already dropped reverting prints by validation time, so a surviving large move is
probably real: warn, don't block. Only >60% — beyond anything observed for these
ETFs even in 2020 — quarantines.

**Frame-robust split awareness**: on a split ex-date the move is explained if it is
small in EITHER frame — the raw move (provider-adjusted series, already continuous)
or the ratio-adjusted move (as-traded series, which genuinely jumps ~1/ratio). The
first version judged only the as-traded frame and thereby *fabricated* a −75% hard
violation on our own clean provider-frame data, quarantining the v2 snapshot — the
gate caught its own author's bug, which is simultaneously embarrassing and exactly
the structural-refusal behavior D26 promises. Regression-tested in both frames.

## Rationale

A sanity gate whose thresholds quarantine real market history is worse than useless —
it trains its operator to bypass it. Anchoring the hard/warning split to the most
extreme *verified-genuine* observations in our own data keeps the gate strict enough
to catch true garbage (a 10× print) and honest enough to pass a crash. The
hard-vs-warning distinction implements D26's own wording: OHLC violations "quarantine",
volume anomalies "flag".
