# D76 — v2 first-number published alongside v1; v1 preserved as the milestone

**Status:** Committed
**Date:** 2026-07-14
**Category:** Data layer
**Source:** Implementation session (Step 7, scope approved by user)

## Decision

`docs/results/first_real_number_v2.md` re-runs the identical study (same pair,
strategy, parameters, sweep) through the hardened Step 7 pipeline — cleaned,
validated, content-addressed snapshot; adjusted views / as-traded execution; explicit
dividend flows; split-scaled positions. `first_real_number.md` (v1) is untouched: it
is the historical Phase C milestone, and its documented caveats are the reason v2
exists.

Headline: v1 → v2 at 0× costs +13.21% → +21.74% (dividend economics now explicit —
the long leg's yield was previously invisible to the cost side; signal series also
differs slightly), at 1× −22.70% → −18.56%, at 4× −76.43% → −76.55%. **The
conclusion is unchanged: the naive famous-pair z-score edge does not survive real
costs.** The point of v2 is not a better number — it's that the number now rests on
a data path whose every transformation is reported, validated, frozen, and
reproducible from a committed fixture by content hash.

## Rationale

Superseding v1 in place would erase the record of what the unhardened path produced
— exactly the kind of quiet history-rewriting the TrialRegistry exists to prevent at
the trial level. Keeping both documents makes the data layer's effect on the result
itself a visible, explained diff (the v1→v2 comparison table), which is more
instructive for a portfolio reader than either number alone. Remaining caveats
(famous-pair selection per D22, full-sample σ/ADV per D66, single-source events) are
restated in v2 rather than inherited silently.
