# D166 — The breakout brick is sign-parameterized, and `direction` is omitted from `config()` at its LONG default

**Status:** Committed
**Date:** 2026-08-21
**Category:** Signals & strategy interface
**Source:** Phase 1.1 session (forward-compatibility retrofit)

## Decision

`BreakoutStrategy` gains a `direction: Direction` field and a `PositionState` enum
replacing the boolean `_in_position` flag; `TrendGateFilter` gains the same `direction`.
Channel logic is written once against the sign rather than duplicated per side.

**`config()` emits `direction` only when it is not `Direction.LONG`.** A long-flat
configuration therefore produces byte-identical config dicts — and byte-identical trial
hashes — to those the v1 study logged, before the sign parameterization existed.

## Rationale

The breakdown addon (`BREAKDOWN_SHORT_STRATEGY.md`) states four forward-compatibility
requirements that bind on the *long-side* session, not on Phase 2: a position-state enum
admitting {long, flat, short} with **no boolean in/out flags**, sign-parameterizable
channel logic, a direction-aware higher-timeframe gate, and a direction parameter on the
null generator. Phase 1 shipped none of them. They are cheap now and expensive later,
which is exactly why the addon asked for them up front — a bool cannot express three
states, so retrofitting the third means touching every read of it, and duplicated
long/short channel code means every future change is made twice or, worse, once.

The retrofit is behaviour-preserving by construction. `PositionState` values ARE the sign
of the exposure, so `state * weight` is the signed target with no branch; for a long book
the state is `1` and the arithmetic is the identity. `_channel_extreme` and `_beyond`
take the sign and select the field and the comparison together, so `direction=LONG`
reproduces the original `max(high)` / `>` and `min(low)` / `<` exactly.

**On omitting the default from `config()`.** D102's rule is "hash what you run", and the
tempting reading is that every field must appear. But the trial config is what the
registry content-addresses, and emitting a new key unconditionally would change the hash
of all 184 v1 trials while changing nothing about what was run — destroying the ability
to compare the v1 registry against any later one, in a project whose entire discipline is
that history is not quietly rewritten (the same principle D76 applies to results
documents). Absence is unambiguous here because the default is pinned in two places that
must agree: the dataclass field and `_direction()`, the parser. An omitted key does still
determine the run.

The cost is real and worth stating: a reader of a raw config dict cannot see the
direction without knowing the default. That is the trade accepted, and it is why the
parser rejects anything that is not a known direction name rather than silently
defaulting on a typo.

## Consequences

- Phase 2's short book is a configuration change plus a stop brick, not a rewrite of the
  strategy.
- The v1 and v1.1 trial registries remain hash-comparable for every long-flat trial.
- `type` remains `"breakout_long_flat"` even for a short configuration, which is now a
  misnomer. Left alone deliberately: changing it is the same hash-churn problem, and
  Phase 2 should decide the naming when it actually has a short book to name. Recorded
  here so the inconsistency is a known debt rather than a discovery.
- The null generator's direction parameter (requirement 4) is **not** delivered: the null
  that exists is a block-bootstrap synthetic-bar null (D130), not the exposure-matched
  random-entry null the addon presumes. Its `direction` field is a metric tail, not a
  trade side. Building a random-entry null is Phase 2 work; see
  [`BREAKOUT_RESULTS.md`](../../BREAKOUT_RESULTS.md).
