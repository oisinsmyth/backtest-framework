# D497 — PRE-REG: open interest against price — does the four-quadrant read carry a signed day-session edge on ES, NQ, CL and GC?

**2026-09-12. Committed before the fixture builder and the runner exist (R8).** Directed by the
principal, who chose this first from the price-action and volume slate. **In-sample
2016-01-04 → 2023-12-29; 2024 onward sealed; no holdout of any line touched; nothing admitted.**

## 0. Why this object

Every construction this programme has closed on the futures was a function of the price path, and
[D473](D473-RESULT-the-cost-structure-picks-the-horizon-hours-not-minutes-and-the-entry-must-come-from-outside-the-price-path.md)
showed the path carries nothing at intraday scale. **Open interest is not a function of the price
path.** It is the count of contracts outstanding: how many positions exist, not what price did.
The `statistics` schema carries it daily for 41 roots back to 2010-06-06, and **nothing in this
repo has ever read it** — D406 was *options* open interest on equities.

The classic reading pairs the day's price change with the day's change in open interest:

| | open interest rises | open interest falls |
|---|---|---|
| **price up** | new longs — money entering — continuation | short covering — positions closing — exhaustion |
| **price down** | new shorts — continuation | long liquidation — exhaustion |

So the declared signal is **`s = sign(Δprice) × sign(ΔOI)`**: trade *with* yesterday's move when
open interest rose, *against* it when open interest fell.

## 1. The premise check, already done, and what it fixes about the design

A scoping probe of the schema (data layer only, no returns read) established:

- **Open interest is `stat_type` 9, carried in the `quantity` field**; `price` is undefined on
  those records. Cleared volume is `stat_type` 6. Settlement is 3.
- **`ts_ref` is the session START (19:00 ET, weekdays Sun–Thu, no Friday)**, so a record's
  reference session is the evening *before* the trade date it describes.
- **First publication is ≈ 21:00 ET on the trade date itself** (trade date 2020-01-07 first
  published 2020-01-07 20:56 ET), with a tail that slips to ≈ 13:30 ET the next business day.

**Therefore, at a 10:00 ET entry on session D, the freshest open interest legitimately known is
the figure for the close of session D−1** — the standard one-day-lagged read, not a two-day-old
one. **The runner takes only values with `ts_event` strictly before 10:00 ET on the traded
session**, so causality holds by construction regardless of the publication convention, and the
realised staleness is measured and reported rather than assumed.

## 2. Fixture (data layer, gated first, no study in it)

`scripts/build_fut_open_interest.py --build` → `data/fixtures/fut_open_interest_daily.csv.gz`
(+ `.meta.json`). Source: `data/raw/databento/GLBX-20260911-SDNLQ6M99S/*.statistics.dbn.zst`,
17 files, 11 GB, 2010-06-06 → 2026-09-10, processes over files (projected **under 5 minutes**;
one worker's RSS printed before the pool).

Rows: one per (root ∈ {ES, NQ, CL, GC}, usable session). Columns: `oi_total` (summed over **all
outright contracts of the root**, which is immune to the roll because open interest migrating
from the front to the next month leaves the total unchanged), `oi_front` (the front contract
alone, secondary), `cleared_volume_total`, `ref_session` (the trade date the figure describes),
`staleness_sessions`, `n_contracts`, and `published_at_et`.

**Gates, asserted in `--gates`, written to the meta:**

- **[O1] causality:** every row's newest `ts_event` is strictly before 10:00 ET on its usable
  session. Asserted, not assumed.
- **[O2] staleness:** the distribution of `usable session − ref session` in trading days is
  reported; the fixture raises if the median exceeds 1.
- **[O3] coverage:** ≥ 98% of the D467 hourly table's sessions carry an open-interest row on each
  root; absent sessions listed, never silently dropped.
- **[O4] roll immunity:** at every quarterly roll, `oi_total` changes by less than 10% while
  `oi_front` falls by more than 40% — the check that the total is the roll-free object.
- **[O5] level sanity:** `oi_total` is positive, and its daily percentage change has a standard
  deviation below 0.10 on every root.

## 3. The trade, common to every cell

Entry at the 10:00 ET print (`h09_c` of the D467 hourly table), exit at the 16:00 print
(`h15_c`). **One round trip, intraday-closable, flat before every venue's flatten time.** Scored
in dollars at **one micro** (MES, MNQ, MCL, MGC) net of **$3.00 commission + 1.009 ticks
crossing**, the lines D465/D466 declared.

`Δprice` and `ΔOI` are both measured over the open interest's own reference session, settlement
to settlement: `Δprice = h15_c(ref) − h15_c(ref−1)` and `ΔOI = oi_total(ref) − oi_total(ref−1)`.

## 4. The declared family: four cells

`s = sign(Δprice) × sign(ΔOI)` on **ES, NQ, CL, GC**. One signal, four roots, nothing else.
Sessions where either difference is exactly zero are no-trade and counted.

**Reported per root, descriptively, not as cells:** the mean day-session move in each of the four
quadrants, so the record says which quadrant carries anything; and the same split by position in
the roll cycle.

## 5. Controls and nulls

- **N1, exact rotation:** the signal series rotated against the fixed move series at every
  k ∈ [1, T−1] (T ≈ 2,000; enumerated, SE 0).
- **N2, family maximum:** common-offset maximum of |mean signed P&L| across the four roots.
- **C1, the ingredient-breaking control (the one that matters):** the identical rule with `ΔOI`
  replaced by `Δ(cleared volume)`. Open interest and volume both rise on busy days; if the volume
  version reproduces the result, **the signal is activity, not positioning**, and the record says
  so. [[control-must-break-the-claimed-ingredient]].
- **C2, the baseline the interaction must beat:** `sign(Δprice)` alone, with no open interest.
  D487 and D495 already found daily reversal on the NQ day session, so a positive result must be
  shown to come from the open-interest term and not from the price term carrying it.
- **Audits:** [F] every input stamped before 10:00 ET on the traded session, asserted on the
  timestamps, not on the column names; [S] sign in money; [M] vectorised P&L equals the loop;
  [X] flipping the sign of ΔOI must negate the statistic exactly; [D] no session after
  2023-12-29 reaches the measurement.

## 6. The bar

A cell is a **pick** when its mean signed P&L is positive, above N1's exact p95, above N2's
family p95, **and** above both C1 and C2 by more than one block-bootstrap SE. A pick is not a
component; it goes to the sealed slice only on the principal's word.

**Context for reading any number:** on the NQ day session the average absolute move is 286 MNQ
ticks against a 7.01-tick round trip, so break-even is **51.2% directional accuracy** and a
component Sharpe of 0.5 needs **53.6%** (arithmetic on committed fixtures, this session).

## 7. Predictions

1. **Data layer:** staleness is exactly 1 trading day on ≥ 80% of sessions, ≤ 2 on ≥ 97%;
   coverage ≥ 98% on all four roots; [O4] holds (total moves < 10% while the front drops > 40%).
2. **The primary signal is inside its rotation null on all four cells**, with ES and NQ nearest
   zero (|mean| < $3 a session at one micro) and CL the largest in magnitude.
3. **The largest single quadrant is price-down-with-open-interest-down (long liquidation) on CL**,
   and it is still inside its own null.
4. **C1 reproduces the OI result within ±40% on at least three of four roots** — the change in
   open interest is mostly an activity measure.
5. **C2 is negative on NQ** (the daily reversal D487/D495 measured), so the interaction starts
   from a negative baseline rather than a flat one.

## 8. What this record does not do

It opens no avenue and closes none (R15). Nothing enters `COMPONENTS_PROP.md` or either book. The
sealed slice stays sealed. The volume-character constructions from the same slate (volume per unit
of overnight range; where in the session the volume sits) are a separate record and are not run
here.
