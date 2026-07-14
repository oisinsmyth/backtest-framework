# The First Real Number, v2 — XLE/XOP through the hardened data layer

**Date produced:** 2026-07-14 · **Snapshot:**
`19c479baa02c35d63a6a199ee2a0710b07c68f1c21c047cd579d815fa26b0e1d` (content-addressed, D72 — reproducible from the committed
`xle_xop_daily_2015_2024_raw.csv`) · **Bars:** 2515 aligned daily bars, 2015–2024 · **Starting
capital:** $100,000 · **Seed:** 0 · Trials logged as
`first-real-number-v2-20260714T021011Z-<multiplier>x`.

Same strategy, pair, parameters, and sweep as
[v1](first_real_number.md) — v1 stays as the historical Phase C milestone (D76). What
changed is the data path (Step 7, D72–D75): cleaner → sanity gate → frozen snapshot;
**split-adjusted prices for signals, reconstructed as-traded prices for execution**
(commissions on the ~$8 XOP shares actually traded pre-split, not the $32 phantom
ones); **explicit dividend cash flows** (long leg credited, short leg debited — 81
ex-dates across the pair); XOP's 2020-03-30 1-for-4 reverse split scales positions
mid-run.

## Pipeline provenance (attached to the snapshot, D24/D25/D26)

- Cleaning (`clean-v1`): 0 change(s) on 5,030 raw bars.
- Validation (`validate-v1`): passed = True,
  1 warning(s) recorded (genuine 2020 crash-day moves and volume
  anomalies — see D74's calibration note; warnings never quarantine).

## The sweep (D8)

| Cost multiplier | Final NAV | Net P&L | Return | Max drawdown |
|---|---|---|---|---|
| 0× | 121,740.73 | +21,740.73 | +21.74% | 29.98% |
| 0.5× | 99,527.46 | -472.54 | -0.47% | 33.47% |
| 1× | 81,439.75 | -18,560.25 | -18.56% | 39.65% |
| 2× | 54,352.89 | -45,647.11 | -45.65% | 50.64% |
| 4× | 23,445.97 | -76,554.03 | -76.55% | 77.03% |

## v1 → v2

| | v1 (adjusted prices, no flows) | v2 (hardened path) |
|---|---|---|
| 0× | +13.21% | +21.74% |
| 1× | −22.70% | -18.56% |
| 4× | −76.43% | -76.55% |

Differences come from: dividend economics now explicit (the short leg *pays* ~1–3%/yr
in dividends it previously escaped; the long leg receives them), commissions/impact on
true as-traded notionals, the split handled as an event rather than baked into prices,
and slightly different signal values (split-adjusted-only views vs v1's
dividend-and-split-adjusted closes).

## Caveats closed by v2 (were v1 caveats 3–4)

- ~~Adjusted prices corrupting cost notionals~~ → as-traded execution (D75).
- ~~Dividend flows unmodeled~~ → explicit DividendFlow, both legs (D6).
- ~~No snapshot/cleaning/sanity gate~~ → full D24/D25/D26 pipeline, provenance in
  the snapshot meta.

## Caveats that remain (R3: labeled, not hidden)

1. **Famous-pair selection bias (D22)** — unchanged; honest pair selection is Step 12.
2. **Full-sample σ/ADV calibration (D66/D70)** — unchanged; and ADV's share frame is
   the provider's, so pre-split XOP impact is approximate (≤2× in √-terms).
3. **Single-source data (D26's deferred second-source cross-check)** — the events
   table and prices both come from yfinance; the dividend/split values were
   sanity-checked for internal consistency (frame continuity) but not against an
   independent source.
4. **No fitted parameters / no train-test split** — unchanged from v1 (D69).

## Reproduction

`uv run python scripts/run_first_result_v2.py` — offline, deterministic; recreates the
same content-addressed snapshot and identical numbers. Asserted in
`tests/integration/test_first_result_v2_e2e.py`.
