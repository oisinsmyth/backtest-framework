# D95 — Capacity analysis: direct AUM sweep with size-aware bricks, recorder-wrapper attribution

**Status:** Committed
**Date:** 2026-07-14
**Category:** Validation & research integrity
**Source:** Implementation session (capacity analysis)

## Decision

`research/capacity.py` measures net(AUM) by running the byte-identical v2 study
(cointegration selection, 1:1 hedge — v3's verdict) at log-spaced
`starting_cash` levels with the REAL, unscaled cost stack. Five load-bearing
choices:

1. **Direct AUM sweep, not multiplier extrapolation.** The D8 sweep scales all
   frictions uniformly and structurally cannot see account size. The real bricks
   can: IBKR's $1/order minimum is a fixed cost that binds small accounts,
   √-impact's fraction grows as √(Q/ADV) and binds large ones, and
   spread/borrow/margin are scale-invariant rates. Varying `starting_cash` lets
   the bricks themselves produce the size dependence — a measurement, not a
   model of a model. Selection depends only on train views, so every level
   trades the same pairs on the same dates; levels differ only through costs and
   whole-share rounding.
2. **Recorder-wrapper attribution.** Per-brick drag comes from recording
   wrappers reusing the D68 scaling-wrapper delegation pattern (accumulate
   instead of multiply) into a `CostLedger` keyed by brick class name; the trade
   recorder also tracks per-symbol max |Q|. Recorders return the inner value
   UNCHANGED — the transparency identity (recorded run ≡ default run, exactly)
   is a tested property, and event flows pass through unwrapped (dividends are
   transfers, not frictions — the same boundary costs/scaling.py draws).
3. **`base_stack` hook.** `run_pairs_study` gains optional `base_stack=None` —
   the injection point the recorder needs, with the same None-default contract
   as `selector` (D92) and `strategy_factory` (D94): v1/v2/v3 stay
   byte-reproducible. The framework stays frozen; everything else lives in
   `research/`.
4. **Ledger-validity constraint.** Capacity runs use `multipliers=(1.0,)` only:
   a 0× run through a recording stack would still record the unscaled costs of a
   *different* trade path and poison the ledger. The gross reference comes from
   a separate plain-stack sanity run at $100M instead.
5. **Participation as the model boundary.** Max |Q|/ADV is reported per level
   using the SAME ADV the impact brick uses. The √-law is an empirical fit;
   rows pushing far into a symbol's ADV are extrapolation and the doc says so
   rather than presenting all rows with equal confidence.

DSR is explicitly not the object: these are cost diagnostics of one strategy at
varying account size, not new signal trials — but they are logged to the
registry and count toward the program-level multiplicity record (D90).

## Rationale

v2 made the capacity question concrete: profitable at 0.5× costs, −6.43% at 1×,
*at $100k*. "Would it clear at a different size?" is the natural next
measurement, and the honest way to answer it is to let the size-aware cost
model — already built and gate-tested in Step 5 — see different account sizes,
rather than extrapolating from the multiplier sweep's uniform scaling. The
result (see `docs/results/capacity_analysis.md`) stands either way: a clearing
window sharpens the Phase G capacity story; "no AUM clears" identifies exactly
which friction would have to move, via the drag decomposition.
