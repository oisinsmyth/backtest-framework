# D85 — Walk-forward with structurally-guarded fitting; Gatev top-N selection with logged multiplicity

**Status:** Committed
**Date:** 2026-07-14
**Category:** Validation & research integrity
**Source:** Implementation session (Step 12)

## Decision

`validation/walk_forward.py`: `walk_forward_windows(...)` aligns the universe
(D45/D63) and yields windows whose training data is delivered **only** as
`Mapping[str, DataView]` built from the training slice — the test window is
physically absent from anything a fitter receives (D56's construction guarantee,
reused). This single `fit(views) -> ...` accessor is simultaneously D22's rule for
pair selection and D28's rule for regime models: **any** fitting code gets training
data through the identical guarded socket. D28 has no regime model to bind yet —
same situation as D82's missing sector momentum; the socket enforces the rule the
day one arrives.

`validation/pair_selection.py`: Gatev distance (SSD of rebased log prices over the
training window, all C(n,2) pairs via the gram-matrix identity), **rank and take
top-N — no p-value thresholding** (D29: testing 200 pairs at p<0.05 manufactures
~10 discoveries from noise). `n_pairs_tested` is part of the return value so callers
log it to the TrialRegistry — the multiplicity count DSR later deflates by.

The I-gate scenario makes the guarantee concrete: a pair engineered to be locked
together in-sample and to invert out-of-sample IS selected (its training score is
genuinely best), the train views provably end at the training boundary
(LookAheadError beyond), and the selected pair trades the test window end to end.
No claim is made about the OOS outcome's sign — the point is that selection could
not have known.

## Rationale

D22's rationale ("famous pairs are famous *because* they worked") is a statement
about information leakage at the research-process level; the framework's answer is
the same one it gave for strategy code in D32 — make the leak structurally
impossible rather than procedurally discouraged. Reusing DataView means there is
exactly one look-ahead guard in the codebase, already adversarially tested (the
Step 4 cheating-strategy suite), rather than a second bespoke one for fitters.
Returning `n_pairs_tested` from selection (rather than trusting the caller to count)
makes the honest multiplicity number the path of least resistance.
