# D430 — the long book out of sample: `us_shorts_daily_holdout`, one read, both lenses

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file. D400–D429
used, D407–D410 and D390–D399 reserved. Daily bars.

## 1. The decision this executes

The principal's standing rule was: no holdout until there is a tradeable indicator. D429 met the
candidate condition on the principal's terms. **The principal has chosen to spend
`data/fixtures/us_shorts_daily_holdout.csv.gz` on this line — and only that file.**
`us_shorts_daily_holdout2.csv.gz` is not read, not opened, not touched. The file was read once
before by an unrelated strategy; this line (D412–D429) has never read it, so for this line it is
unseen, and after this study it is spent.

**What "out of sample" means here, stated so it cannot be over-read:** the holdout is the same
2010–2026 span on a **disjoint set of 803 names** (34% dead), built by the same pre-live screen
as the 1,573 in-sample names. A pass is evidence that the construction generalises **across
names**. It is *not* evidence about time: the 2020–2026 regime that carries the in-sample
premium is in this file too. The 2018+ and 2021+ windows are reported, not gated.

## 2. The construction — frozen, to the digit, from in-sample

Nothing is re-derived on the holdout:

```
zones     D413: THETA 1.0, LIFE 60, H 5, DELTA 1.0, ARM_MAX 20; entry at the touch-day close, exit at t+5 close, no stop
cell 2    REV <= -0.02473244344202641   EFF > 0.23669449533835638   DV > 44370158.19015902   (in-sample medians)
rung      STACK2-ANY: exactly one prior (day, side) pair on the name in the trailing 20 sessions (D422's counter)
price     entry close < 38.50639133333333   (D427's in-sample cheap tercile)
gap       prior touch 3-20 sessions back
side      long only (demand zones)
priority  opposite-side prior 3-10 back, long
cost      neutral Corwin-Schultz (60-bar trailing median ending 2 bars before) + IBKR $0.0035/share; no borrow (long)
mask      D406/D411's eligibility (floor_mask_v2 on raw price and dollar volume), same code, same parameters
slots     N = 2 PRIMARY -- the in-sample rule (occupancy/N ≈ 0.5-0.6) applied to a universe half the size:
          expected 0.17 events/day, occupancy 0.85 positions.  N = 1 and 3 reported as shape.
seeds     419, 4190, 41900
```

**Expected counts, scaled by 803/1,573 from in-sample:** ~92,000 zone touches, ~13,300 in cell
2, ~4,800 second touches in cell 2, **~720 long-pool events**, ~85 priority events. These are
predictions, not facts; the runner prints the actual counts first and the record carries both.

## 3. The runner, and the proof that precedes the read

`scripts/run_d430_holdout.py` will take the fixture path as a parameter. It has two modes:

- **`--proof`** reads only the in-sample fixture through the *same* parametrised path and must
  reproduce **D429 bit-identically**: the 1,416-event long pool, its trade table, and the N=3
  priority book on every seed (net, gross, trade count to 1e-12), plus D422's 9,411 and D413's
  180,050 / 26,024. **If the proof fails, the holdout is not opened.**
- **`--holdout`** reads `us_shorts_daily_holdout.csv.gz` + `_events.json` **once**, computes
  everything in §4 in one process, writes `data/d430_holdout.json`, and stops. No second run
  against that file is permitted by this record; a bug found afterwards is recorded as a bug, not
  re-run.

The panel loader is D411's body with `FIX`, `EVJ` and the cache path as parameters (its own
cache name, so the in-sample cache is never confused with the holdout's). One control worker's
RSS is printed before any fan-out.

## 4. What the single read computes — everything, because there is no second read

**The ladder, per trade (path-invariant), so a failure is located and not just declared:** all
zone touches → cell 2 → second touch ∧ cell 2 → + cheap → + gap → long (the pool); each with
D422's trade table (gross, median, SE, net, win, payoff, trim, ex-top/ex-bottom) on pooled, 2018+,
2021–2026; the priority sub-cell; the short half of the pool, reported; concentration with the top
trade named and its bars printed; the |r| > 50% variant; per-year means.

**The book (path-variant):** N ∈ {1, 2, 3}, three seeds, with and without the priority;
monthly block-bootstrap SE on pooled, 2018+, 2021–2026; utilisation, cost/bar, per-trade net.

**Controls, drawn from the holdout's own cell 2 (the only legitimate pool for them):** matched-
count random **long** cell-2 pools, one per name, 100 draws, at N = 2 (the book control); and
D422's within-day label permutation on the long pool's premium over the rest of the holdout's
cell-2 long events (the per-trade null), 200 draws.

## 5. The bar — declared with its power, because the power is the point

- **T1 (signal):** the long pool's per-trade **gross** mean > 0 by 2 SE. In-sample +79.9 on 1,416
  with SE 17.4 → on ~720 the SE is ~24, so a mean above ~+50 clears. **Net** is reported beside it
  with its SE; net > 0 in sign is required (T1b), not net > 2 SE, because 2 SE on net at this
  count needs +48 and the in-sample net is +45 — a gate the in-sample itself would barely pass.
- **T2 (book):** the N = 2 priority book's net > 0 by 2 SE (block bootstrap, three seeds).
  **Declared under-powered:** at half the event density the book runs ~20–25% utilised, the
  expected net is ~+2.3/bar with SE ~1.6 if the holdout is exactly as strong as in-sample — about
  1.4 SE. T2 passes only if the holdout is *stronger* per trade than in-sample, or luckier.
- **T3 (control):** the N = 2 book above the p95 of the random long-pool control (D373's margin).
  This has power: in-sample the margin was +22 SE.

**Candidate condition: T1 ∧ T1b ∧ T2 ∧ T3.** Two named partial outcomes, so they are read the
same way whoever reads them: **"T1, T1b, T3 pass, T2 fails"** = the signal generalises across
names and the book's capacity is too thin to prove at 803 names — not a clear, and not a
failure of the signal. **"T1 fails"** = the construction does not generalise across names, and
no book result rescues it.

## 6. Predictions (LOW–MODERATE; a holdout is where the in-sample numbers are supposed to shrink)

- **X-a** counts within ±20% of §2's scaled expectations; the long pool 580–870 events.
- **X-b** the ladder shrinks but keeps its shape: cell 2 > all touches; second touch > cell 2;
  cheap is the largest single step; gross at each rung 50–80% of in-sample.
- **X-c** the long pool: gross **+35 to +65**, net **+0 to +30**, median above the mean, win
  54–60%. T1 passes more likely than not; T1b passes; neither by a distance.
- **X-d** the per-trade permutation null passes.
- **X-e** the N = 2 book: net **+1 to +3.5** ± ~1.6 — T2 fails at 2 SE more likely than not,
  positive on at least two of three seeds; T3 passes.
- **X-f** 2018+ and 2021+ above pooled, as in-sample — the same years carry it; 6–10 names to
  half the P&L.
- **X-g** the priority delta inside its noise; N = 1 at or above N = 2 per bar.

**The prediction that matters is X-c.** If gross on new names is inside 2 SE of zero, the
construction's per-trade edge was the names it was built on, and nothing in the twenty-nine
studies before this survives that.

## 7. Not in scope

`holdout2` in any form; a second read of this file; any change to any threshold; any exit;
15m; disposition. Thirtieth look by object; the **first** on data this line has not seen.
