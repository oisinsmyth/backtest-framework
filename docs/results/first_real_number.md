# The First Real Number — XLE/XOP z-score pairs, full cost sweep

**Date produced:** 2026-07-14 · **Snapshot:** `xle_xop_daily_2015_2024.csv`
(fetched 2026-07-13, see sidecar `.meta.json`) · **Bars:** 2515 aligned daily bars,
2015–2024 · **Starting capital:** $100,000 · **Seed:** 0 (no stochastic
components in this run) · Trials logged to the local TrialRegistry as
`first-real-number-20260714T012834Z-<multiplier>x`.

This is Phase C's milestone and R1's existence-justification gate
(`DEVELOPMENT_TIMETABLE.md`): the framework's first end-to-end number on real data
through the real cost stack. Per the gate's own words: the number can be ugly; it must
be produced. **It is a milestone of the instrument, not a research claim** — see
caveats.

## Strategy

`ZScorePairsStrategy` (D69): spread = ln(XLE) − ln(XOP), fixed 1:1 log-hedge, rolling
z-score over the previous 60 bars (never the current one),
enter at |z| > 2.0, exit at |z| < 0.5,
hold in between, ±100% of capital per leg when in a
trade (~200% gross). Hyperparameters chosen a priori, not tuned.

## Cost stack (at 1×)

- Trade: IBKR Fixed commission ($0.005/sh, $1 min, 1% cap — D65) + square-root impact
  (σ/ADV per leg from the fixture — D66) + 1bp half-spread stand-in.
- Carry, per leg: borrow fee 0.25%/yr on short notional (D71).
- Carry, portfolio: margin interest 6%/yr on max(gross − NAV, 0) (D67).

## The sweep (D8)

| Cost multiplier | Final NAV | Net P&L | Return | Max drawdown |
|---|---|---|---|---|
| 0× | 113,208.20 | +13,208.20 | +13.21% | 33.22% |
| 0.5× | 93,652.65 | -6,347.35 | -6.35% | 38.63% |
| 1× | 77,303.64 | -22,696.36 | -22.70% | 43.68% |
| 2× | 52,685.44 | -47,314.56 | -47.31% | 52.50% |
| 4× | 23,569.71 | -76,430.29 | -76.43% | 76.89% |

## Caveats — what this number is NOT (R3: labeled, not hidden)

1. **Famous-pair selection bias (D22):** XLE/XOP was chosen *because* it's the
   canonical pairs example. That is meta-level in-sample selection. Honest pair
   selection inside walk-forward training windows is Step 12.
2. **No fitted parameters, so no train/test split** — the "walk-forward" here is
   bar-by-bar forward simulation with trailing-only data (structurally enforced by
   DataView). Nothing was optimized; nothing needed holding out (D69).
3. **Adjusted prices (D6 gap):** the fixture stores yfinance auto-adjusted closes.
   Return dynamics embed dividends, but commissions/impact are computed on adjusted
   (not raw) notionals — exactly the corruption D6 exists to fix in Step 7. Dividend
   cash flows on the short leg are not separately modeled.
4. **Unhardened data (D24–D26 gaps):** no snapshot checksum, no cleaning report, no
   sanity gate. The fixture is frozen only by being committed to git (D70).
5. **Cost-parameter look-ahead (D70):** σ/ADV for the impact model are calibrated on
   the full sample. This touches cost calibration only, not the trading signal.
6. **IBKR constants unverified against the live page (D65):** the schedule modeled is
   the long-published one; the pricing page 403-blocks automated fetches.

## Reproduction

`uv run python scripts/run_first_result.py` — offline, deterministic from the
committed fixture. The same run is asserted in
`tests/integration/test_first_result_e2e.py` (monotonicity + 0× ≡ zero-cost gates).
