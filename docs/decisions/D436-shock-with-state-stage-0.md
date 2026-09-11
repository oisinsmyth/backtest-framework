# D436 — shock-with-state: stage 0 of a volume-shock construction weighted by the conditional atlas

**Pre-registration of STAGE 0 only. Committed before the runner exists (R8).** Stage 0 reads no
forward return: counts, rates, overlaps, occupancy, cadence. It ends in a continue/abandon
condition for stage 1, which would be its own pre-registration. D400–D435 used, D407–D410 and
D390–D399 reserved. **No holdout is read; the mining fixture only.**

## 1. The construction, from D434/D435

A 3× volume bar (`rv_x3`: VOL_t ≥ 3 × ADV20, D434's definition) in a **state** known at the same
close; the event is placed at `t+1` and filled at `t+1`'s open (D340's convention, D434
ADDENDUM). Held to a 20-bar cap, no stop, no target, one position per name, market-hedged as the
atlas measures.

| | event → side | D435 cell p50 (state's own) | weight |
|---|---|---|---|
| **A** | shock in the top 12-1 momentum tercile → long | +38 (+23) | **0.40** |
| **B** | shock in the top price tercile → short | +50 (+17.5) | **0.25** |
| **C** | shock in the bottom price tercile → long | +32 (+19) | 0.15 |
| **D** | shock in the bottom momentum tercile → short | +19.5 (+9) | 0.10 |
| **E** | inside A and C: `rv_hi` ∧ `ret20_lo` → size tilt +25%; `rv` is a shock already, so E is the `ret20_lo` flag | +14 spread | 0.10 (as a tilt) |

**The weights are set here, from the atlas, and are never re-fit to the book's P&L.** They may
be re-derived only from a refreshed atlas on names this line has not traded.

**Declared nulls for stage 1 (written now so stage 1 cannot choose them):** each component's
floor is its own D435 cell (a random trade in the same state after the same event); the
combined book's control is a book of random events drawn from the same four state cells at the
same daily rate; a time rotation of the shock series. Both lenses.

## 2. What stage 0 computes (dates, states and volumes only)

1. **Counts** per component, total, by year; **daily rate**; names touched.
2. **Overlaps:** a name-day in more than one component (A∩C: `mom_hi` ∧ `price_lo`; B∩D:
   `price_hi` ∧ `mom_lo`; A∩D and B∩C are impossible by construction — asserted).
3. **Same-name blocking:** a shock on a name already inside a 20-bar hold — the share of events
   the one-position-per-name rule would refuse, per component.
4. **Occupancy:** mean open positions at a 20-bar hold after blocking — the number the slot count
   must be sized to (D428: capacity is a queue, not a mean; p50/p90/max of daily occupancy too).
5. **Cadence:** the spacing between consecutive shocks on the same name; the share of spacings in
   **58–68 sessions** (a quarter) as the earnings-cadence proxy, against the share expected if
   spacings were uniform over 1–120.
6. **E's coverage:** the share of A and C events with `ret20_lo`.
7. **Side balance:** long events (A+C) vs short (B+D) by year.

**Assertions:** `[F]` every event mask is the `t−1` pool placed at `t` (D434's check, reused);
`[X]` A∩D and B∩C are empty; `[N]` the counts equal the D435 pool cells shifted and re-masked
(the runner reads the pools from the same code that built the atlas cells).

## 3. Continue / abandon, declared

**Continue to stage 1** if: A's daily rate ≥ 1.0; the overlap share (events in two components /
all events) ≤ 20%; occupancy after blocking is at least 50 (a book that can hold the components
at their weights); and the quarterly-cadence share is **reported**, not gated — an earnings-drift
mechanism is not a reason to stop, it is a thing stage 1 must then control for (a calendar null).
**Abandon** if A's rate is below 0.5 a day or the overlap share exceeds 40%: the components are
then not separable at the weights declared.

## 4. Predictions (computed from D435's pool sizes; MODERATE)

- **X-a** events: A ≈ 13,500, B ≈ 12,400, C ≈ 15,900, D ≈ 13,300 (the D435 cells' pool sizes,
  shifted); total 50,000–58,000; **12–14 a day**; 1,400+ names.
- **X-b** overlaps: A∩C **8–15%** of A (cheap high-momentum names), B∩D **8–15%** of B; total
  overlap share 10–18%. Continue condition met.
- **X-c** blocking: with one position per name and a 20-bar hold, **35–50%** of events arrive
  on a name already held (shocks cluster: earnings weeks, news runs).
- **X-d** occupancy after blocking **120–200** positions at the median — a 50-slot book would be
  three to four times over-subscribed; the slot count for stage 1 is set from this number.
- **X-e** cadence: **25–40%** of same-name spacings fall in 58–68 sessions against ~9% uniform —
  a large earnings component, to be controlled for in stage 1.
- **X-f** E covers **25–35%** of A and C.
- **X-g** longs (A+C) outnumber shorts (B+D) in most years; the ratio is between 0.8 and 1.4.

## 5. Not in scope

Any forward return; any holdout; stage 1 itself. Thirty-sixth look by object; stage 0 spends
nothing.
