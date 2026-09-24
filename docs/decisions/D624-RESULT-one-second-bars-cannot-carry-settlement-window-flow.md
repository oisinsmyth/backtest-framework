# D624 RESULT — one-second bars cannot stand in for settlement-window signed flow: the sibling check fails, so neither CL nor NG runs Stage A on the estimate

*2026-09-25. Pre-registration: [D624](D624-PRE-REG-validating-estimated-signed-flow-for-stage-A.md),
committed alone in `6e1bfa4`. Runner: `scripts/validate_flow_estimate.py`; output
`data/ledger_flow_estimate_validation.json` (the `siblings` phase). The gate phase on NG and CL has not been
read, and under §5 it cannot change this outcome.*

## The verdict

**The siblings do not agree** (§4 step 2). The chosen estimator reaches r = −0.03 on HO and −0.22 on RB over
the second half, against a bar of 0.8 on each. Under §5's table, **neither CL nor NG runs Stage A on the
estimate**. The kill test needs real aggressor-signed flow in the settlement window, which is data gap G1 in
AITODO, and the principal has said they will source it.

## The numbers

**K1 (alignment) passes exactly:** 252,053 window seconds; bar volume 1,271,123 = trade volume 1,271,123,
equal on 100% of seconds (after the deviation below).

**Selection, first half** (2025-09-25 → 2026-02-27, window flow in the most active outright):

| | E1 tick rule | E2 in-second direction | E3 bulk volume classification |
|---|---|---|---|
| r, HO | 0.220 | 0.209 | 0.225 |
| r, RB | 0.370 | 0.448 | 0.393 |
| mean | 0.295 | **0.329 (chosen)** | 0.309 |

**Agreement, second half** (2026-03-02 → 2026-09-18). E2 was the chosen estimator; the other two are
reported for the record and never gated:

| | E1 | **E2** | E3 |
|---|---|---|---|
| HO, r (90% CI), n = 141 | −0.09 | **−0.03 (−0.17, +0.11)** | −0.09 |
| RB, r (90% CI), n = 140 | −0.19 | **−0.22 (−0.35, −0.08)** | −0.23 |

**Reported beside, not gating:**

| quantity | HO | RB |
|---|---|---|
| Classification accuracy (share of true signed volume whose second's sign matched), mean | 0.609 | 0.605 |
| All outright months summed, window | r −0.07 | r −0.19 |
| Pre-window flow, 13:30 → 13:50 / 14:00 / 14:10 | 0.44 / 0.60 / 0.60 | 0.48 / 0.41 / 0.49 |
| Controls (must be small): C1 day shift, C2 random signs | 0.07, 0.01 | 0.16, −0.01 |

The sessions: 249 per root in total, of which 2 per root fall below the 20-true-trade floor (2026-05-25 on
both; 2026-02-16 on HO; 2026-09-07 on RB).

## What the object shows (8 RB sessions inspected, June 2026)

Every second of the two-minute window holds trades: 116–120 one-second bars, 900–1,900 contracts. The true net
is a few hundred contracts either way, and in 7 of the 8 sessions it is net selling. Almost no volume trades in
bars where the price did not move (0–4%), so the estimators do have a price change to work with. But at a
volume-weighted accuracy of about 60%, the misclassified volume on 1,000–2,000 contracts is as large as the net
itself. The estimate had the net's sign right in 5 of the 8 sessions.

The mechanism fits a VWAP settlement: in the window, buyers and sellers alternate at bid and ask within the
same second while the price barely moves, so the direction of the price carries little information about who
initiated. Over the longer pre-window spans (20–40 minutes) the same estimators reach r ≈ 0.4–0.6: moderate,
still under 0.8, and not what Stage A's H1 measures.

## Deviations (all in the runner's `DEVIATIONS`, none touching a threshold)

1. **The clock.** K1 raised on the first run: bars and trades matched on 98.32% of seconds. Databento builds
   `ohlcv-1s` bars on the receive timestamp (`ts_recv`), and trades had been bucketed on the exchange's
   `ts_event`. Trades, and so the truth, now use `ts_recv`. K1 then passes on 100% of seconds. D624 did not
   name the timestamp.
2. **A void run.** The second run's truth subtracted sell size from buy size on Databento's **unsigned**
   `size`, so net selling wrapped to about 4.3 × 10⁹. Its correlations were computed against a corrupted truth
   and are void. They are recorded in the runner so the run is not hidden. The void numbers still carried
   sign information (E2 looked best), and they were seen before the corrected run. The selection rule was
   mechanical and fixed in advance, so that exposure could not move the choice.
   The sums are now cast to int64, and the selftest has a net-selling case on uint32 sizes.
3. A crash in `load` before any statistic (`.dt` missing on a date conversion).

## What follows

- **Stage A needs real signed flow for both roots.** The cheapest real route, quoted 2026-09-25 with
  metadata calls only:
  - Databento `trades` for CL/NG in just the settlement window, 14:28–14:30 ET, plus H5's time-placebo span,
    11:50–12:20 ET. That is about **$108 for the in-sample** (2017-05 → 2025-02) and about **$7.50 for the
    vault**. It is scaled from 12 sample days at 10.5% of the whole-day cost.
  - Stage B's pre-window flow (13:30 → τ) would add to that, and one-second bars reach only r ≈ 0.4–0.6 there.
- **The NG/CL gate phase is not needed for the decision.** Whether to spend the free top-up (before
  ~2026-10-11) on it as a record is the principal's call.
- **This does not touch** the other free-data uses: the ETF premium from Alpha Vantage, TAS as reported, and
  the one-second bars as price data.
