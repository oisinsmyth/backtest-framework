# D170 — Intrabar stop execution in the engine, and the stop that turned out not to bind

**Status:** Committed
**Date:** 2026-08-21
**Category:** Backtest engine
**Source:** Follow-on session disposing of [D169](D169-the-short-book-and-its-close-based-stop.md)'s recorded limitation

## Decision

`run_backtest` gains per-position stop orders. A `TargetWeight` may carry an optional
`stop` price; the engine keeps a live registry keyed `(strategy_id, instrument_id)`,
refreshed from every bar's targets, and checks it **before the strategy is consulted**,
routing through the existing `simulator/fills.stop_fill_price`.

`BacktestResult` gains `stop_fills`, recording which fills a stop actually caused.

This closes the limitation D169 recorded. It also **corrects a claim D169 made**.

## Rationale

**Why the stop rides on the target.** It is per-(strategy, instrument) state the strategy
already holds, and re-declaring it each bar is what lets a trailing stop move with no
extra machinery. An optional field with a default left all five `TargetWeight`
construction sites untouched, so the change is additive in the same way D168 was — and
every pre-existing golden master passing is the evidence, not a claim.

**Why it is checked before the strategy step.** A position opened at this bar's open can
still be stopped out on the same bar, which is real and must be allowed; and the
strategy's decision then sees a book that already reflects the stop. D42's
adverse-fill-first convention is satisfied by construction: the stop is intrabar and
every other exit in this engine is a decision taken at a close, so the stop is always
evaluated first and wins any bar in which both would have fired.

**Why the strategy must be told.** A stateful strategy does not otherwise learn it was
stopped out — it would keep emitting the same target and re-enter on the very next bar,
turning one bounded loss into a repeated one. The `Strategy` protocol gains an
**optional** `on_stop_filled(instrument_id)`, called via `getattr`, so every strategy
written before D170 still conforms. `BreakoutStrategy` implements it; `ScheduledBreakout`
forwards it, the same way it already carries `_state` across a schedule swap.

**Why splits are refused rather than handled.** The stop is declared in the VIEW frame
and enforced against EXECUTION prices. Those are the same series only when the instrument
has no splits (D75). Spot crypto has none (D108). Rather than silently compare two frames,
the engine raises when a stop is declared on a split-bearing instrument.

## What it found, which is not what was expected

**The mechanism works and barely matters.** Across both symbols the stop was armed for
**915 bars and caused one exit**, which filled at its stop price with no gap. The stop
sits at the far side of the entry channel — for a short entering on an N-bar low, the
N-bar high — which is an enormous distance from the entry, so the trailing exit channel
reaches every position first almost every time.

**The tail discipline is present but not binding.** A risk control that never binds has
not been shown to work on this sample; it has only been shown to be unneeded on it. That
is a weaker statement than either D169 or the brief assumed, and it is the honest one. A
tighter stop — ATR-based, say — is a different strategy and would need its own sweep and
its own multiplicity accounting.

**D169's headline stop number was a measurement artifact, and is withdrawn.** That report
claimed "4 of 4 stop exits filled beyond their own stop level, the worst by 38.5%".
`measure_stop_gaps` inferred stop exits by recomputing the stop level and asking whether
an exit price ended up beyond it — which also counts ordinary trailing-channel exits that
happened to close past the level. Most of those four were not stop exits at all. The
engine now records causation directly, because only the engine knows it, and the function
takes that record instead of guessing.

**The study's verdict is unchanged.** Null percentiles (BTC 51%, ETH 96%), the
correlation (~0.00 both), and the regime split all hold; BTC's baseline total return moves
−70.5% → −71.6%. So the Phase 2 conclusions stand — but they now stand on a measured stop
rather than an assumed one, which was the point.

## Consequences

- D169's limitation is disposed of; its reasoning is left intact per the D111 precedent,
  with a pointer here.
- `BREAKDOWN_RESULTS.md`'s stop section and standing caveat are rewritten, and the
  prose is now **computed from the numbers** rather than asserted beside them. This is the
  third time in this project that a hardcoded sentence drifted from the data next to it
  (the long study's multiplicity table, the short book's regime scorecard, and now this),
  which is a strong argument for deriving any sentence that quotes a figure.
- Any future strategy can use a real stop. The primitive was correct and tested in
  isolation since Step 1; what was missing was it being called.
