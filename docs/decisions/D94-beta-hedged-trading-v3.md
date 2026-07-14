# D94 — Study v3 β-hedged trading: constant-gross weight normalization, factory hook, β=1 equivalence

**Status:** Committed
**Date:** 2026-07-14
**Category:** Validation & research integrity
**Source:** Implementation session (study v3)

## Decision

`research/beta_zscore.py::BetaHedgedZScoreStrategy` trades the train-window
Engle-Granger β that D92 logged: spread = ln A − β·ln B, same rolling-z /
hysteresis / warm-up machinery as `ZScorePairsStrategy`. Four load-bearing
choices:

1. **Constant-gross weight normalization.** The factor-neutral hedge holds dollar
   notionals in the ratio N_B = β·N_A; raw (±w, ∓βw) would let gross exposure
   drift with β (1.7w–2.3w across the [0.7, 1.3] coherence window) and break risk
   comparability with v1/v2. So: **w_A = 2w/(1+β), w_B = 2wβ/(1+β)** — gross is
   exactly 2·leg_weight for every pair, every β.
2. **β = 1 reduces exactly to `ZScorePairsStrategy`** — same spread, same weights.
   Tested twice: target-level identity (unit) and whole-study equity-curve
   identity via a β=1-forcing factory (integration). The v3 machinery provably
   contains v2 as its β=1 special case.
3. **Strategy-factory hook.** `run_pairs_study` gains optional
   `strategy_factory(pair, strategy_id, config, details) -> Strategy`; `None`
   preserves the v1/v2 construction byte-for-byte. The factory is called per
   (window, multiplier, pair) so every run gets fresh instances (D68), and
   receives the pair's entry from the selector's `last_details` — which is how
   the fitted β travels from selection to trading without the framework growing
   any coupling between the two.
4. **Research-package placement.** The framework stays frozen; like the selector
   (D92), the strategy lives in `research/` with the honest thesis label in its
   docstring even though the D82 auto-trip only watches `strategies/`.

β is fitted on the training window only (through guarded DataViews, D22/D85) and
applied out-of-sample, never re-fitted mid-window.

## Rationale

One variable per study version: v3 = v2's selection byte-identical + β-hedged
trading, so the v2→v3 delta prices the hedge alone (estimation noise included —
that is part of the strategy, not a confound).

**The measurement came back negative, and that is the finding**: gross fell from
v2's +19.03% to +6.12%, and at 1× costs the loss deepened from −6.43% to −16.53%.
With selection, windows, costs, and gross exposure all held fixed, the conclusion
is clean: on this universe a train-window β carried out-of-sample imports more
estimation error than hedge benefit — unsurprising in hindsight, since the
selector's coherence window already restricts to β ≈ 1, leaving the hedge little
room to help while its noise costs in full. The 1:1 hedge wins; the Phase G
writeup gets a genuine estimation-error result rather than a decoration.
