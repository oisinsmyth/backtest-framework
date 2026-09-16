# Cross-engine reconciliation (D41, D79)

**Date:** 2026-07-14 · **Reference engine:** vectorbt 1.1.0 (pandas 3.0.3, Python
3.12) · **Repeatable test:** `tests/integration/test_cross_engine.py` — lives in the
normal offline suite, so this reconciliation re-runs on every simulator-touching
change automatically.

D41's premise: a framework that only checks itself against itself can be wrong in a
stable, self-confirming way forever. This document anchors `run_backtest` to an
engine we didn't write.

## Design: same inputs, isolate the engines

Both engines consume the **identical precomputed target-weight schedule** —
MA(10)/MA(30) cross on the committed XLE fixture closes
(`data/fixtures/xle_xop_daily_2015_2024.csv`, 2,515 daily bars), weight 0.6 when
fast > slow else 0. Signal code is therefore out of the comparison entirely; any
divergence is a disagreement about *simulator mechanics* — sizing, fills, fees,
accounting.

## Conventions matched (each one deliberate)

| Convention | Ours | vectorbt | Why it matters |
|---|---|---|---|
| Re-sizing basis | weight × current NAV, every bar (D27/D61) | `size_type='targetpercent'` of current value, every bar | Architecturally the same convention — the reason vectorbt was chosen over hold-until-exit engines |
| Fill price | close of the signal bar | `price=close` | Timing mismatch would shift every trade |
| Shares | fractional (`Equity(quantity_precision=8)`) | fractional (no granularity) | Eliminates rounding-convention divergence (our `round()` vs their `floor`) |
| Fees | `PercentOfNotionalSpread(bps=5)` on \|order notional\| | `fees=0.0005` on order value | Identical proportional model |
| Carry / dividends / margin | none in this stack | unsupported | Compared on common ground only |
| Target weight | 0.6, not 1.0 | 0.6 | At ~full investment, vectorbt reserves fees from the purchase while we pay fees from cash — a real convention difference that the comparison deliberately stays below (found during design, verified by smoke test) |

## Result

| | Ours (`run_backtest`) | vectorbt `from_orders` |
|---|---|---|
| Bars | 2,515 | 2,515 |
| Trades | **1,370** | **1,370** |
| Final value | **$159,233.023491** | **$159,233.023491** |

- **Max absolute divergence across the full 10-year equity curve: $0.0000002186**, at bar
  2,400 — floating-point noise, orders of magnitude inside D47's 1e-6 tolerance.
- **Max *relative* divergence: 1.30e-12, at bar 2,494**, where the absolute divergence is
  $0.0000002138.

  > **Corrected 2026-09-16.** This read *"$0.0000002186 (1.30e-12 relative)"*, which presents
  > one measurement expressed two ways. They are the maxima of two different series and they
  > fall on two different bars: at bar 2,400 the relative divergence is 1.262e-12, and at bar
  > 2,494 the absolute is $0.0000002138. Both published figures were individually correct; only
  > the parenthesis joining them was not. Found by building
  > [`docs/figures/cross-engine-agreement.svg`](../figures/README.md) from the residual series,
  > which is the first time either series was looked at rather than summarised.
- **Divergence table: empty.** Identical trade counts on every one of 1,370 re-size
  decisions; no penny required itemized reconciliation.

## What was learned anyway (D41's real payoff)

1. **The fee-reserving boundary at full investment**: vectorbt's target-percent
   sizing reserves fees out of the purchase when cash-constrained; ours charges fees
   to cash after sizing. Below ~100% target weight the conventions coincide; at 1.0
   they don't. If this framework ever runs at full investment, that convention
   difference is now a documented, known fact rather than a surprise.
2. Both engines mark equity at the close after same-bar fills, and both treat
   target-percent orders against pre-order value — assumptions that were implicit in
   our engine are now cross-confirmed.

## Caveats

- One instrument, long-flat only, proportional fees only — the comparison covers the
  shared subset of both engines' capabilities. Carry, dividends, splits, margin, and
  multi-leg netting are ours alone and are anchored instead by THE golden master
  (`tests/golden/test_the_golden_master.py`) and the D40 invariant suite.
- vectorbt is itself software with bugs; agreement is strong evidence, not proof.
  The IBKR schedule (D65) and quantstats (Step 9's X-gate) provide further
  independent anchors.
