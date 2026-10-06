# Cross-engine reconciliation

A backtester that is only ever checked against itself can be wrong in a consistent way that no
internal test notices. This one is checked against vectorbt, an engine written by other people.

## Method

Both engines consume one precomputed target-weight schedule: weight 0.6 in XLE when its 10-day
moving average is above its 30-day average, otherwise 0. The schedule is built once from the
bundled daily fixture (2015-01-02 to 2024-12-30, 2,515 bars), so signal code plays no part and
any difference is a disagreement about sizing, fills, fees or accounting.

Both re-size to the target percentage of current value every bar, fill at the close, use
fractional shares and charge a 5 bp proportional fee.

## Result

| | this engine | vectorbt 1.1.0 |
|---|---|---|
| Fills | 1,370 | 1,370 |
| Final value | $159,233.023491 | $159,233.023491 |
| Largest divergence over the curve | $2.2e-7 absolute, 1.3e-12 relative | |

The two engines made the same re-sizing decision on every bar.

## One convention difference

At a target weight of 1.0 the results would not match. When cash is the constraint, vectorbt
reserves the fee out of the purchase; this engine sizes first and pays the fee from cash. Below
full investment the two coincide, which is why the test uses 0.6. The difference is documented
rather than hidden.

## Scope

One instrument, long or flat, proportional fees only. Carry, dividends, splits, margin and
netting across strategies are outside what the two engines share, and are pinned by the
hand-computed golden ledgers instead.

Reproduce: `uv run pytest tests/integration/test_cross_engine.py`.
