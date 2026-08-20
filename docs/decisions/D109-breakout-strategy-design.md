# D109 — Long-flat breakout: filters and sizing as bricks, hysteresis enforced structurally

**Status:** Committed
**Date:** 2026-08-18
**Category:** Signals & strategy interface
**Source:** Breakout study session

## Decision

`strategies/breakout.py` implements a long-flat Donchian breakout: enter when
`close(t) > max(high)` over t−N_entry … t−1, exit when `close(t) < min(low)` over
t−N_exit … t−1. Both windows exclude the current bar. No shorting; flat is the default
state.

Two brick families sit *beside* the entry logic rather than inside it, each behind a
`Protocol` with a declarative `config()` and a `FactoryRegistry` (D52), so a strategy is
rebuilt from the exact dict the TrialRegistry hashes (D102):

- **`EntryFilter`** — consulted only on the bar an entry would otherwise fire, and only as
  a veto: `ConsecutiveCloseFilter`, `VolatilityContractionFilter`, `TrendGateFilter`.
  Filters are never consulted on exits — a filter can keep you out of a trade, never trap
  you in one.
- **`WeightSource`** — decides the size of an open position as a target weight:
  `FixedWeight`, `InverseVolatilityWeight` (see [D110](D110-vol-target-sizing-lives-in-the-weight.md)).

`n_exit > n_entry` is refused in `__post_init__`. Trailing estimates (ATR, the SMA gate,
realized vol) use windows ending at t−1, per D44; only the breakout comparison itself
reads `close(t)`, which is a completed bar at decision time and fills at the next bar's
open (D103).

## Rationale

**Why excluding the current bar is enforced by construction rather than by comment.** If
`max(high)` included bar *t*, a bar with a large high and a modest close could trigger on
itself, and the resulting equity curve would be untradeable in a way no summary statistic
would reveal. It is unit-tested directly and property-tested through the engine:
perturbing any bar after the decision bar — arbitrarily, scaled by up to 100× — cannot
change a target the strategy already produced.

**Why `n_exit <= n_entry` is a hard error, not a warning.** It is what makes "never
chatters" a theorem rather than a hope. With the exit window nested inside the entry
window, `max(high)` over the entry window is at least `min(low)` over the exit window, so
no close can be strictly above one and strictly below the other — entry and exit cannot
fire on the same bar. The measured whipsaw rate of 0% at the baseline parameters is that
inequality showing up in the data, not a lucky sample.

**Why filters are bricks and not booleans on the strategy.** The study's method is adding
one filter at a time and pricing the delta. A flag-per-filter entry function makes
"baseline plus exactly one filter" a code path rather than a configuration, and code paths
cannot be enumerated by a trial registry or hashed into a config. This is D1's CostStack
argument applied to signals.
