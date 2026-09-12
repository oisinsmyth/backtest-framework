# DRAFT (no number taken) — Robintrack stage 0: does the day's most-herded Robinhood stock lose over the next month on our own fixture, and does a matched-attention control take it away?

*Drafted 2026-09-12 while D485 runs; to be numbered and committed as a PRE-REG before its runner
exists. The download the principal authorised is on disk: `data/raw/robintrack/popularity_export/`,
8,597 tickers, hourly `users_holding` 2018-05-02 → 2020-08-13 (median gap 1.00 h), two site-wide
outages of ~10 days ending 2019-01-30 and 2020-01-16 (must be masked, not interpolated).*

**Overlap with the programme's daily fixtures:** 959 of the 1,573 mining names, 512 of holdout #1's
803, 341 of holdout #2's 576. Stage 0 reads the 959 only.

## The published object (Barber, Huang, Odean & Schwarz, JF 2022)
"Herding episodes": days on which the number of Robinhood users holding a stock rises the most
(top 0.5% of stock-days by the increase); the top stocks bought each day earn **−4.7% abnormal
over the next 20 trading days**. The mechanism is attention (the app's top-mover lists), so the
confound is the same-day move itself: names with a large |return| and volume attract holders
*and* mean-revert. **The control must break the claimed ingredient:** match on the day's
|return| decile and volume decile without the holder change.

## Fixture (data layer, gated)
`data/fixtures/robintrack_daily.csv.gz`: per (ticker ∈ overlap, trading day) the last observation
at or before 15:55 ET (`users_close`), the observation nearest 09:25 ET (`users_open`), counts of
observations that day, a flag for outage days. Gates: [R1] cadence — ≥ 20 observations on a
normal day; [R2] the two outages masked; [R3] join to the daily fixture on ticker and date with
≥ 95% of fixture days matched inside the span; [R4] no future — `users_close` is stamped ≤ 15:55.

## Stage 0 measurement (in-sample = the 959 names, 2018-05-03 → 2020-07-31)
- `h_t = (users_close_t − users_close_{t−1}) / users_close_{t−1}` and the absolute change.
- Each day rank the cross-section on `h_t`; **the top decile and the top ten** are the herded set.
- Outcome: hedged forward return over 1, 5, 20 days from the next open (fill at the open, D392's
  kernel convention), hedged against the equal-weight fixture.
- Controls: (C1) the same-day |return| and volume matched set without the holder change
  (partner randomisation, never a re-drawn subset — D291); (C2) within-name time rotation of `h`.
- Splits: price tercile, size (users level) tercile, and the 2020-03 → 2020-08 era alone.
- Cost: Corwin–Schultz on the names held; net beside gross.

## Predictions
1. Top-decile herding: 20-day hedged **−100 to −300 bp**, below C2's p5; the top-ten set larger in
   magnitude and noisier.
2. C1 removes **at least half** of it: most of the "herding" return is the same-day move reverting.
3. The residual after C1 lives in the bottom price tercile and in 2020 — i.e. in the names where
   the crossed cost is largest; net at 20 days near zero.
4. Nothing on the long side: the least-herded (largest outflow) decile is within ±50 bp.

## What it does not do
Reads no holdout; enters nothing in any book; the RTAT ten-year table is a separate record.
