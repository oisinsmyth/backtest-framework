# D54 — CostStack + Instrument interface shapes, and toy bricks now vs. real bricks in Step 5

**Status:** Committed
**Date:** 2026-07-13
**Category:** Backtest engine
**Source:** Implementation session (Step 3)

## Decision

- `Instrument` (`instruments/base.py`) is a `typing.Protocol`, not an ABC — structural
  typing, no forced inheritance, matching D12's stated interface exactly:
  `notional(quantity, price)`, `margin_requirement(quantity, price)`,
  `carry_components() -> tuple[str, ...]`, `tradeable_quantity(raw_quantity)`,
  `quote_currency`.
- `Equity.tradeable_quantity` rounds via a single `quantity_precision: int | None`
  field (`None` = whole units, an int = that many decimal places) rather than separate
  whole-share/fractional-share/crypto-precision classes. One mechanism, parametrized,
  covers all three rounding regimes the Step 3 gate tests for.
- `TradeCostBrick.cost(instrument, quantity, price)` and
  `CarryCostBrick.cost(base_amount, prev_timestamp, curr_timestamp)` are two separate
  `Protocol`s (matching D2's per-trade/carry split), each purely additive — a brick
  never reads another brick's output, so `CostStack` ordering is provably a no-op
  rather than an assumption.
- `FlatCommission`, `PercentOfNotionalSpread`, `FlatRateCarry` (`costs/bricks.py`) are
  toy implementations that exist to prove the interfaces and composition are correct.
  They are explicitly not D3 (sqrt impact), D4 (IBKR schedule), or D5 (margin
  interest on gross exposure minus capital) — those are Step 5's job and are expected
  to replace these, registered as their own concrete `TradeCostBrick`/`CarryCostBrick`
  implementations against the same interfaces.
- `FlatRateCarry` is the direct migration target Step 2's `CarryModel` demonstration
  class always said it would become (see its docstring) — `config/carry_model.py` now
  builds `FlatRateCarry` via its `FactoryRegistry` instead of a separate duplicate
  class. Step 2's own four gates were re-verified against this after the migration and
  still pass.

## Rationale

D12 specifies the Instrument interface's method names but not its implementation
mechanism (ABC vs Protocol vs duck typing) or how instrument-specific quantity rounding
should be modeled across asset classes; D1/D2 specify the CostStack split but not the
concrete brick call signature. Both needed a real answer to write any code, and both
choices were made to bias toward what Step 5 (real cost bricks) and Step 10 (crypto,
deferred past the portfolio deadline per `DEVELOPMENT_TIMETABLE.md`) will actually need,
without building either of those now:

- Protocol over ABC: `Equity` and `OptionStub` don't need a shared base class to satisfy
  the interface, and nothing about D12's text implies inheritance is required — this
  keeps instruments composable rather than forcing a class hierarchy that would need
  rethinking once a genuinely different instrument (e.g. an FX pair, D15) arrives.
- One parametrized rounding field over three classes: cheaper to write and test, and
  avoids inventing a `CryptoStub` class now that D14 (Step 10) will define properly with
  its own carry semantics (funding) — a bare precision override would be a false
  affordance if it silently implied "crypto is supported," which it doesn't (D48).
- Purely additive bricks: real-world cost bricks (spread, commission, impact) don't
  actually depend on each other's output in this framework's model — impact depends on
  quantity/ADV, commission on quantity/price, not on "the spread cost that was just
  computed." Keeping that constraint explicit now, and testing it, means a future brick
  that violates it (and needs real ordering semantics) is a deliberate, visible
  decision, not something that quietly breaks the existing composition guarantee.
