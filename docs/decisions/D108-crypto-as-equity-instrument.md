# D108 — BTC/ETH modelled as `Equity(quantity_precision=8)`, not a new crypto instrument

**Status:** Committed
**Date:** 2026-08-18
**Category:** Instruments
**Source:** Breakout study session ([`BREAKOUT_RESULTS.md`](../../BREAKOUT_RESULTS.md))

## Decision

The breakout study trades BTC-USD and ETH-USD through the existing `Equity` instrument
with `quantity_precision=8`, rather than introducing a `CryptoSpot` / `CryptoPerpetual`
class. Annualisation uses 365 days, supplied by the caller
(`BreakoutStudyConfig.periods_per_year`), because the `Instrument` protocol as built
carries no calendar method.

The fixture (`data/fixtures/crypto_daily_2015_2025_raw.csv.gz`) records a **00:00 UTC bar
boundary, fixed** — no alternative boundary is offered or tested. The events sidecar is
empty by construction, and `scripts/fetch_crypto_fixture.py` fails loudly if the provider
ever returns a dividend or split for spot crypto rather than silently dropping it.

## Rationale

For a long-only, unlevered spot book the `Equity` semantics are not an approximation —
they are exactly right. Notional is signed quantity × price; margin is full notional; the
position never goes short, so borrow never applies; the weight is capped at 1.0, so gross
exposure never exceeds NAV and the margin-interest brick's base is always zero. The one
genuinely crypto-specific field is the lot size, and `Equity.quantity_precision` already
exists for it — its own docstring names 8 dp as "a crypto-precision stub".

What a real crypto instrument would add is what this study does not use: a funding-rate
carry brick for perpetuals (D14, Step 10's deferred work) and a `periods_per_year` method
the protocol never grew (D17 as designed vs `instruments/base.py` as built). Building
either in order to run a spot backtest would be speculative generality of exactly the kind
this codebase avoids, and R1's spirit — research output before framework code — points the
same way.

The gap is named in the report's caveats rather than papered over: a perpetual-futures
version of this study would need the funding brick, and funding is a cost of precisely the
kind the study exists to measure.
