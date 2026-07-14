# D102 — Declarative config for the real cost stack; train-window impact calibration (audit F2/F4)

**Status:** Committed
**Date:** 2026-07-14
**Category:** Backtest engine / Cost architecture / Validation & research integrity
**Source:** Audit remediation session (AUDIT_REPORT.md findings F2, F4)

## Decision

**1. The real stack is config-built (F2).** `config/cost_stack.py` extends the
D52 factory mechanism (same `{"type": ...}` dialect, same `FactoryRegistry`
class, same fail-loudly-naming-the-key contract) from the two Step-2 demo models
to the study's actual cost stack: one brick-config list per CostStack slot, with
data-dependent bricks (`sqrt_impact`, `dividend_flow`) built against a
`StackDataContext` derived from the snapshot — so config + snapshot fully
determine the stack. `StudyConfig.cost_stack_config()` produces the dict,
`build_cost_stack` consumes it, and `run_pairs_study` logs it verbatim in every
trial: **what the registry hashes is what ran**, closing the audit's finding that
the config hash covered a free-hand description nothing verified against the
objects. `build_base_cost_stack` survives as a thin wrapper for the capacity
study's injection path.

**2. The hash now covers everything that determines the result.** The audit
found `StudyConfig.to_dict()` omitted `starting_cash`, `multipliers`,
`periods_per_year`, `mc_seed`, and `benchmark_symbol` — two capacity levels
differed only by trial-id string, and two studies at different account sizes
could hash identically. Every field is now serialized, and
`StudyConfig.from_dict()` closes the study-level reproducibility loop: config →
registry → reload → rebuild → re-run reproduces the stitched curves exactly
(tested). A logged `cost_stack` that doesn't match what the rebuilt config would
construct is a loud error, never silently overridden.

**3. Train-window impact calibration (F4).** `StudyConfig.impact_calibration`:
`"full_sample"` (default — preserves v1/v2/v3/capacity/gross byte-for-byte and
remains D66's documented look-ahead) or `"train_window"`, which rebuilds the
stack per walk-forward window from that window's TRAIN slice only, through the
same declarative path — σ/ADV estimation then obeys D44's
no-test-window-data rule. The two regimes carry different config hashes by
construction. `train_window` refuses an injected `base_stack` (recorder/scaling
wrappers wrap one stack instance; a per-window rebuild would silently bypass
them) — capacity/gross runs stay full-sample until recording is made
window-aware, which no current question needs.

## Rationale

D35's own words — "the TrialRegistry's config hash is impossible while configs
hold live objects" — described exactly the state the audit found the *studies*
in, D52's promise that Step 3's bricks would "register with their own
FactoryRegistry instance using the same pattern" having quietly lapsed
(acknowledged in AITODO but unbuilt). The leak-free calibration option lands in
the same decision because it is the same mechanism: "which data calibrated the
bricks" is precisely the kind of result-determining fact that must live in the
hashed config, not in a script's local variables. The default stays
`full_sample` per the repo's own precedent (D92/D94/D95: hooks default to
byte-reproducing the published artifacts; changed behaviour is a new study
version) — the convention-sensitivity study quantifies the difference as its own
artifact rather than rewriting history.
