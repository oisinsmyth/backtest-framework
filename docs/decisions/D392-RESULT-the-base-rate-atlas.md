# D392 RESULT — the base-rate atlas: price is the widest axis, volatility the narrowest, and four of six predictions failed

**Status:** RESULT. A **MEASUREMENT** (D280's class): it scores no strategy, proposes no rule and
**admits nothing (R15). Ledger contribution: 0.**
**Date:** 2026-09-08 · Spec: [D392](D392-the-base-rate-atlas.md), committed before the runner.
Runner: `scripts/run_d392_base_rate_atlas.py` · Artifacts: `data/d392_atlas.json`,
`data/d392_calibration.json`, `data/d392_tercile_cost.json`

**127 cells, 46,400 kernel runs, 188 minutes** against a calibrated projection of 186.
**Build (R16):** `load_ragged(dividend_bound=True)`, `keep_v2` floor, F0, next-open fill,
`EB.simulate_event` via `run_d359`. **Holdout reads: 0.**

---

## 0. The headline

**Two pools decide more than most signals do, and neither had ever been measured.**

| conditional pool, n=30,000, cap 20, hedged, **no signal whatsoever** | long p50 | short p50 |
|---|--:|--:|
| **price — cheap third** | **+19.22** | −19.42 |
| price — middle third | +1.65 | −1.87 |
| **price — dear third** | **−17.54** | +17.27 |
| **momentum — bottom third** | −9.03 | +10.33 |
| momentum — middle third | −0.75 | −0.13 |
| **momentum — top third** | **+23.12** | −22.57 |
| volatility — bottom third | −5.84 | +5.72 |
| volatility — middle third | +0.25 | −0.17 |
| volatility — top third | +6.35 | −8.39 |

**Spread of the median random long, top minus bottom:**

| axis | spread | |
|---|--:|---|
| **price** | **36.8 bp** | widest, and never previously measured on the gross side |
| **momentum** | **32.2 bp** | FINDINGS §52 with a number on it |
| volatility | **12.2 bp** | narrowest — and I predicted it widest |

**A random long on high-momentum names earns +23.12 bp a trade at the median.** §52 concluded *"the
cohort was the strategy"* from three bespoke measurements on one construction; this says it holds
for **any** construction selecting in that pool, before the construction exists.

---

## 1. The unconditional curve, and it behaves

Cap 20, long, pool ALL — **p50 is ~zero everywhere**, which is the reassuring part: the hedged
kernel with a next-open fill is unbiased on a no-information draw.

| events | 100 | 300 | 1,000 | 3,000 | 10,000 | 30,000 | 60,000 |
|---|--:|--:|--:|--:|--:|--:|--:|
| trades | 99 | 298 | 989 | 2,927 | 9,337 | 24,946 | 42,874 |
| **p50** | −0.37 | +4.29 | +0.04 | +0.56 | +0.80 | +1.56 | **+1.36** |
| **p95** | +159.4 | +109.2 | +51.0 | +30.5 | +18.0 | +11.5 | **+8.27 ± 0.63** |

**Long and short are near-perfectly antisymmetric** (+8.27 vs +5.12 at n=60,000; +19.22 vs −19.42
on cheap names), which is the internal consistency check the whole atlas rests on.

---

## 2. Predictions, scored — four of six failed

| | prediction | outcome |
|---|---|---|
| **Q1** | *(load-bearing)* n=60,000 cap-20 long p95 within ±15 bp of +43 | **FALSIFIED** — **+8.27**, off by ~35 |
| **Q2** | long and short floors differ by < 15 bp | **HELD** — +8.27 vs +5.12 |
| **Q3** | p95 scales ~1/√n; ratio p95(1k)/p95(10k) in [2, 4] | **HELD** — 51.0/18.0 = **2.84** |
| **Q4** | floors substantially positive at every cap and rising with cap | **SPLIT** — the **p95** rises with cap (+8.27 → +11.89 → +13.61 at n=60,000) but the **p50 is ~0**. True of the tail, false of the centre |
| **Q5** | volatility the widest conditional axis | **FALSIFIED** — the **narrowest**, by 3× |
| **Q6** | *(against my own scoping)* concentration matters > 25 bp | **FALSIFIED** — 10,000 events on 5% of names gives p95 **+14.43** against **+17.73** on all names, a **3.3 bp** difference. **v1's decision to make concentration a sensitivity rather than an axis was correct** |

**Four of six failed, including the load-bearing one.** An instrument whose author's predictions
mostly survived it would be a weaker instrument.

---

## 3. The correction this forces on D391

**D391's RESULT §2 asserted: *"two opposite constructions earning +43 bp is a base rate, not two
signals."* That is WRONG as written and is withdrawn.**

D391's ledger was **+43.02 bp on 61,835 trades**. The nearest in-grid floor is **+8.27** at 42,874
trades, and the 1/√n curve implies roughly **+6.9** at 61,835 — **so +43.02 sits about five times
above the unconditional random floor, not at it.** I attributed the number to the hold and the
universe on no evidence, and the instrument built to catch exactly that error caught mine.

**What the atlas cannot say**, and the record must not pretend otherwise: D391's events fire on
names taking out a pivot low intrabar, which plausibly skews cheap (+19.22) and high-volatility
(+6.35). **A uniform draw does not share that nuisance** — D291's rule — so the unconditional
floor is the wrong comparator and the *right* one is a pool the atlas does not have: "names at a
fresh pivot undercut." **That pool exists only as D391's own `B_r`, which is why `B_r` remains the
better control and why D391's verdict is untouched:** the reclaim arm returned **+6.0** against its
own same-bar, same-structure pool at **+13.5**.

**The candidate stays dead. Only my explanation of the +43 was wrong.**

---

## 4. The cost line, which the spec owed and which settles the price finding

`data/d392_tercile_cost.json` — measured Corwin–Schultz (D285's estimator), median over each
tercile's eligible cells, PUB convention, 2-crossing line (the name's own round trip, D358):

| tercile | p10 $ | median $ | p90 $ | half-spread bp/side | round trip | gross p50 | **net p50** |
|---|--:|--:|--:|--:|--:|--:|--:|
| cheap | 7.77 | 17.25 | 27.40 | 34.46 | 68.92 | +19.22 | **−49.70** |
| middle | 29.30 | 41.05 | 63.33 | 27.62 | 55.23 | +1.65 | **−53.59** |
| dear | 56.62 | 102.36 | 276.61 | 25.35 | 50.70 | −17.54 | **−68.24** |

> **The price effect is not tradeable. +19.22 gross on the cheap tercile is eaten three times over
> by a 68.92 bp round trip.**

Two things worth noting. **The cheap tercile is not the penny tail** — its median name is $17.25,
because the D339 floor already excludes sub-$5 — so this is not the artifact D284 died on, and it
is still uneconomic. And **the half-spread differs far less across terciles than the gross return
does** (34.5 vs 25.4 bp/side, a 1.36× ratio, against a 36.8 bp gross swing), so the price effect is
**not merely a spread artifact** — it is a real gross tilt that cost happens to bury.

---

## 5. Two defects found by testing the lookup, not by reading it

Both would have silently corrupted every future call:

1. **The concentration cells polluted the main curve.** They carry `pool="ALL"`, so they entered
   the unconditional interpolation and put two points at n=10,000. Fixed: `lookup` filters on
   `conc` and merges points within 1%, keeping the better-sampled cell.
2. **The grid endpoint failed on a rounding boundary** — a caller quoting 42,874 trades against an
   endpoint of 42,873.7 was refused as out-of-grid. Fixed with a 0.1% tolerance and a clamp.

**And a design correction the concentration cells forced: the lookup now keys on TRADES, not
events.** The kernel holds one position per name at a time, so 60,000 events become 42,874 trades
at cap 20 and 26,958 at cap 60 — and under concentration, 10,000 events become 4,116. **A candidate
reporting 61,835 trades must be read against the trade axis**; the event axis remains available as
`by="events"`.

---

## 6. How to use it without overfitting

1. **It is a null, not a signal.** Used as a comparator it adds zero degrees of freedom — it can
   only make verdicts stricter.
2. **Look up the pool your MECHANISM implies, declared in the pre-registration before the run.**
   Choosing the comparator after seeing the number flatters the candidate.
3. **Never re-cut the buckets.** Fixed terciles, cross-sectional, per bar.
4. **Do not browse the atlas for opportunities.** 127 cells; "which pool pays best" is mining.
5. **It is in-sample.** It makes in-sample verdicts honest; it does not substitute for R8.
6. **It refuses to extrapolate.** Outside the grid it raises, and the caller reports the nearest
   in-grid floor *as* the nearest.

---

## 6a. ADDENDUM, 2026-09-08 — the grid is extended, D391 now has an exact floor, and it deepens rather than closes the question

**§7's first owed item is done.** Twelve cells at n ∈ {100,000, 150,000} × cap ∈ {10, 20, 40},
500 draws, 1.6 h, calibrated first. **The atlas now holds 139 cells and the cap-20 trade axis runs
to 75,340.**

| cap 20, long, ALL | trades | p50 | p95 |
|---|--:|--:|--:|
| n = 60,000 | 42,874 | +1.36 | +8.27 |
| **n = 100,000** | **60,149** | +0.92 | **+6.49 ± 0.39** |
| **n = 150,000** | **75,340** | +1.23 | **+5.60 ± 0.23** |

**D391 no longer falls outside the grid.** At **61,835 trades** the interpolated floor is:

| | observed | atlas floor p95 | ratio |
|---|--:|--:|--:|
| ~~**D391 long**~~ | ~~+43.02~~ | +6.38 ± 0.39 | ~~6.7×~~ |
| ~~**D391 mirror**~~ | ~~+43.73~~ | +3.54 | ~~12.4×~~ |

> ### THE ATLAS FOUND A LOOK-AHEAD — corrected 2026-09-08, and this is the record's first real use
>
> **A 6.7× margin is not something this programme produces, and it was not one.**
> [D391 §9](D391-RESULT-the-reclaim-is-worth-less-than-no-reclaim-and-the-edge-was-the-event-bar.md)
> traced it: the ledger booked **the signal bar's own open-to-close**, the bar whose close defines
> the event. The kernel treats its mask as the bar the position *opens on*, and D391's mask was
> passed unlagged.
>
> | | look-ahead | **corrected** | floor | |
> |---|--:|--:|--:|---|
> | D391 long | +43.02 | **+8.00** | +6.38 ± 0.39 | barely above |
> | D391 mirror | +43.73 | **+5.63** | +3.54 | barely above |
>
> **The absurdity of the margin is what forced the reconciliation**, and the reconciliation found
> the bug. That is the atlas doing the job it was built for — not admitting a candidate, but
> making a number impossible to accept quietly.

**The §6a hypothesis below was also wrong**, and doubly so: it supposed the entry convention was
crediting the gap, when the convention excludes it *and* the real defect was a missing lag. Both
are recorded rather than deleted.

**This confirms the withdrawal in §3 with a measured number rather than an extrapolation: +43 was
never the base rate.** But it makes the real question sharper, because **both** sides clear their
floors by wide margins — a long and a short, on opposite signals, each 6.7× and 12.4× above a
uniform draw.

### A hypothesis, named as one, with the test that settles it

**Neither the price nor the volatility tercile explains it.** Scaled to 61,835 trades those floors
land near +19 (cheap) and +11.5 (high-vol) — still far under +43.

**The candidate explanation is the ENTRY CONVENTION, not the pool.** Both event families are
defined by a bar with a **large intrabar range**: the long closes above a level it pierced, the
short closes below one it exceeded. **The next open after such a bar may gap systematically in the
direction of that close**, which would credit *both* books mechanically.

The programme has already measured that this convention is enormous —
[D340](D340-RESULT-the-same-close-fill-was-three-quarters-of-the-best-book.md): *the same-close
fill was three quarters of the best book* — and FINDINGS §21: *the fill convention credited the
overnight gap to every entry, and it was worth more than the spread.*

**This is a hypothesis and this record does not assert it.** The test is cheap and specific:
**re-score D391's two ledgers under a same-close fill and compare.** If the +43 collapses on both
sides, the number was the entry gap on high-range bars, and *the atlas cannot see it because
uniform draws land on ordinary bars.* If it survives, something real sits in that event family and
D391's `B_r` failure means only that the reclaim is the wrong half of it.

**Recorded as the next owed measurement, not as a finding.** Two mechanisms were asserted and
withdrawn in this programme today; this one is written as a question with a named experiment.

---

## 7. What is owed

- **Extend the grid past 42,874 trades.** D391 sat outside it, which is precisely the size a wide
  event study reaches. n = 100,000 and 150,000 events at cap 20 would cover it.
- **Pools the atlas lacks.** "Names at a fresh pivot undercut" is D391's `B_r`, and every future
  event family will want its own. **The atlas cannot pre-compute every pool** — it covers the three
  standing axes, and a candidate whose pool is not among them still owes a bespoke control.
- **Deferred from the spec and still deferred:** sector, dead-vs-alive, era, the intraday fixtures.

---

**Status footer.** A measurement. No strategy was scored, nothing was admitted, and no avenue is
closed (R15). `docs/BOOK.md` holds S1 and S2, neither at capital; `docs/BOOK_PROP.md` is empty.
