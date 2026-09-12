# D488 — RESULT: extending the hold fails, and the closure accidentally produced the first net-positive cell

**2026-09-12.** Runner [`scripts/d488_extended_hold.py`](../../scripts/d488_extended_hold.py) ·
artifact [`data/d488_extended_hold.json`](../../data/d488_extended_hold.json) ·
pre-registration [D488 PRE-REG](D488-PRE-REG-does-the-MACD-edge-keep-growing-with-the-holding-period-and-does-it-cross-its-cost.md),
committed before the runner existed. Signal code **imported from D484 unchanged**.

---

## 1. The hypothesis fails

| variant | longest-H edge (pooled) | vs R1 p95 | **EDGE SURVIVES** |
|---|---:|---:|---|
| B1 impulse | +0.00157 | **−38.6 SE** | **no** |
| B2 plain | −0.00067 | **−39.5 SE** | **no** |

**At the longest holds the edge is gone.** Not marginal — forty standard errors below where the
rotation null's 95th percentile sits.

## 2. And the pattern is root-specific, not systematic — which is the tell

| root | variant | H=5 | H=8 | H=11 | H=16 | H=22 |
|---|---|---:|---:|---:|---:|---:|
| GC | B1 | **+0.0284** | +0.0267 | +0.0219 | +0.0161 | **+0.0043** |
| CL | B1 | +0.0159 | +0.0197 | +0.0144 | +0.0277 | **+0.0297** |
| CL | B2 | **+0.0321** | +0.0296 | +0.0210 | +0.0108 | **+0.0080** |
| ZN | B2 | −0.0025 | −0.0061 | −0.0109 | −0.0165 | **−0.0273** |
| ZB | B2 | +0.0093 | +0.0012 | −0.0151 | −0.0295 | **−0.0356** |
| 6E | B2 | −0.0210 | −0.0168 | −0.0162 | −0.0080 | **+0.0127** |

**GC decays monotonically. CL's B1 rises while CL's B2 falls — the two variants disagree on the
same root.** ZN and ZB go strongly negative. 6E climbs out of negative territory.

**There is no H effect. There is scatter.** Two smoothed MACD variants that disagree in sign
about the same instrument over the same window are measuring noise, not a horizon.

## 3. A flaw in my own pre-registered statistic, which I am recording rather than replacing

**S2's null is UNDEFINED and the statistic cannot be tested.** §3 defined S2 as the slope of
`log(edge_sigma × √H)` on `log H`. Under a rotation null the edge is centred on zero and goes
**negative about half the time**, and **the log of a negative number does not exist** — so the
statistic returns NaN on most null draws and the family mean is NaN.

**The observed values are +0.608 (B1) and +0.093 (B2) against a flat-edge value of 0.5, and they
are DESCRIPTIVE ONLY.** The bar is recorded as **unmet because ill-posed**, never as passed. I am
not substituting a different statistic and claiming a result on it; a slope of `edge_sigma` on
`log H` — no log of the edge — would be testable and needs its own pre-registration.

**This is the second time in two records that my choice of statistic was the weak link** (D474's
family-maximum against a monotone hypothesis was the first). The pattern is picking a statistic
for its expressiveness before checking it is defined on its own null.

## 4. W-c BROKEN — and this is the result worth keeping

**NQ, plain MACD, 5-hour hold, confined to the day session: gross/cost = 1.14, net +0.982
ticks.** The first net-positive cell in this entire sequence.

| | D484 (all hours) | **D488 (day session only)** |
|---|---:|---:|
| edge per σ | +0.01774 | **+0.02685** |
| σ in ticks | 217.0 | **297.6** |
| gross ticks | 3.849 | **7.991** |
| **gross/cost** | **0.55** | **1.14** |

**Both factors roughly doubled the product.** And the crucial point about provenance: **the
day-session restriction was FORCED by the principal's closure, not chosen for performance.** I
confined the index roots to the day session because the overnight leg is closed — the improvement
was a side effect, not a search.

### Four reasons this is a candidate and not a finding

1. **It is the best of 12 cells**, and the best of twelve looks good under any null.
2. **No null was attached to the tradeability claim.** §5's TRADEABLE bar required
   `gross/cost > 1.0` and nothing else — **a weakness in my pre-registration**, not something the
   data settled. The rotation null was computed for the longest-H edge and the growth exponent,
   neither of which covers this cell.
3. **The two variants disagree in sign on NQ.** B1 reads **−0.0029** at H=5 and **−0.0242** at
   H=7 where B2 reads **+0.0269** and **+0.0150**. In D484, on all hours, *both* were positive.
   **Restricting to the day session flipped one variant negative while doubling the other.** If
   the day-session edge were structural, two smoothed variants of the same indicator should agree.
4. **The cost line is still the declared $3.00**, not a quote, and the crossing is an ES
   measurement assumed for NQ.

## 5. Predictions

| | prediction | outcome | |
|---|---|---|---|
| **W-a** | B1 exponent > 0.5 and clears R1 | **BROKEN** | +0.608, but the null is undefined (§3) |
| **W-b** | the rise decelerates | HELD | |
| **W-c** | no index root tradeable | **BROKEN** | NQ B2 H=5 at 1.14 |
| **W-d** | GC or CL largest at the longest H | HELD | CL, +0.0297 |

**§0's arithmetic was right about the mechanism and wrong about the conclusion.** It predicted
NQ reaching only ≈0.65 in the day session on a flat edge — and NQ reached 1.14, because the
day-session edge per σ is half again larger than the all-hours edge the 0.65 was extrapolated
from. **The √H reasoning was sound; the input to it was the wrong number.**

## 6. What this changes, and what it does not

- **Extending the hold is closed as a lever.** Forty SE below the null at the longest holds, on
  eight roots, with the two variants disagreeing root by root. D486's "cheapest untested lever"
  is now tested and it does not work.
- **The day session is a new and unexamined axis.** Everything before this measured all 23 hours
  or the overnight leg. The one cell that confines itself to 09:00–16:00 more than doubled its
  gross edge. **That is where I would look next**, and it needs a pre-registration with a null on
  the specific cell.
- **Nothing is admitted.** `gross/cost = 1.14` on the best of 12 unnulled cells is a candidate.
  Nothing enters `COMPONENTS_PROP.md`, the vault or either book, and **2024+ stays sealed.**
- **GC, CL, ZN, ZB and 6E remain uncosted** — MGC/MCL/M6E are absent from the committed specs and
  **no tick value was guessed.** CL's B1 at H=22 (+0.0297) is the largest long-hold edge measured
  and cannot be priced without that fetch.

## 7. Checks

26 self-test checks. The growth exponent is calibrated exactly: a **flat** edge gives **0.500000**,
`H^0.25` gives **0.750000**, `H^-0.5` gives **0.000000**, and a decaying edge is proven to fall
below 0.5. The eligibility rules are proven to *bind*: every non-index hold exits exactly at index
21 (P2's 4pm cap), H=22 admits exactly one entry at the 18:00 open, and **an index root gets zero
entries at a 22-hour hold** — with a companion check that a *non-index* root does get one, so the
closure is shown to be what excludes it rather than P2. The imported D484 functions are
re-verified in place.

**Three fixes during construction, all mine:**

- **A tautology.** The scale-free check ended in `or True` and could not fail. **Third one this
  session** — it now compares ×1000-scaled returns to unscaled, with a companion check that
  doubling the *signal* does change the answer, so the test has teeth.
- **A planted-edge check that read 0.025 for a planted 0.040** and looked broken. It was not: that
  RNG draw carries a −0.015 spurious baseline (~2 SE at n = 20,000). Measuring the **increment**
  isolates the planted effect.
- **The S1 table used `H_NONINDEX` as its column headers**, so the index roots' H=7 cells existed
  in the data and were invisible in the report.

**Profiled before launch:** 16 ms per draw → 0.5 min.
