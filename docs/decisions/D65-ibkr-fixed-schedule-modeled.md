# D65 — IBKR Fixed US-equity schedule modeled; cap overrides minimum; pass-throughs deferred

**Status:** Committed / Deferred
**Date:** 2026-07-13
**Category:** Cost architecture
**Source:** Implementation session (Step 5)

## Decision

`IBKRCommission` (`costs/equity_bricks.py`) models IBKR **Fixed** pricing for US
stocks/ETFs: $0.005/share, minimum $1.00/order, maximum 1% of trade value, as
`min(max(per_share × |q|, min_per_order), cap_pct × |q| × price)` — the cap
**overrides** the minimum (a 10-share order at $0.50 pays $0.05, not $1.00). The
three constants are dataclass fields defaulting to the published schedule, so a
schedule revision is a config change.

**Deferred, per R3:** regulatory pass-throughs (SEC/FINRA fees on sells — small but
nonzero, sell-side only) and the Tiered schedule (volume-discounted, exchange fees
broken out). Both are additive bricks against the same `TradeCostBrick` interface
when they're wanted.

## Rationale

D4's whole point is that the target broker is known and per-share pricing diverges
from flat bps by up to ~70× depending on share price — the X-table's row 7 (100
shares of a $2,000 stock: $1.00 vs a flat-5bps model's $100) makes that concrete.
Fixed over Tiered because Fixed is the all-in schedule a small account actually gets
by default, and Tiered's exchange-fee breakdown is precision the current research
question (does the pairs edge survive costs at all?) doesn't need yet.

The min/cap ordering matters and is easy to get backwards:
`max(min(...), min_per_order)` would charge $1.00 on the penny-stock order the
published schedule caps at $0.05. The X-table's rows 6 and 11 (cap-overrides-min,
and the triple boundary where all three regimes coincide) exist specifically to pin
this ordering.

**Anchoring caveat (anti-self-deception, stated rather than hidden):** the X-gate
wants the brick checked against a reference we didn't write. IBKR's pricing pages
403-block automated fetches — verified during planning, both URL forms. The
constants used are IBKR's long-published, widely-documented schedule, but a one-time
manual verification against the live page is still owed and is tracked in
`AITODO.md`. Claiming the X-gate is fully discharged without that check would be
exactly the kind of quiet overstatement `PHILOSOPHY.md` exists to prevent.
