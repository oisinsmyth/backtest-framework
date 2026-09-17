# D436 RESULT — stage 0 continues: the book is a 135-position book, not a 50-slot one; a third of the momentum longs are also cheap longs; a sixth of shocks are quarterly

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D436-RESULT-stage-0-continues-the-book-is-a-135-position-book-not-a-50-slot-one-and-a-third-of-the-momentum-longs-are-also-cheap-longs.md`. The H1 above is the full title.*

**STAGE 0 CONTINUES TO STAGE 1** on the condition declared in `7380bcf` (A ≥ 1.0/day: **3.28**;
overlap share ≤ 20%: **12.9%**; occupancy ≥ 50: **137**). Runner written after the spec (R8).
**No forward return was read. Nothing is scored. No holdout.** 7 s.

```
[F] every event mask is the t-1 pool placed at t;  [N] counts equal D435's cells exactly;  [X] A&D and B&C empty
```

---

## 1. The events

```
component                        events   per day   names   refused by one-per-name (20-bar hold)
A  shock in mom_hi   -> long     13,731    3.28     1,235   24.2%
B  shock in price_hi -> short    12,597    3.01       661   22.0%
C  shock in price_lo -> long     16,182    3.86     1,005   27.0%
D  shock in mom_lo   -> short    13,560    3.24     1,225   25.0%
union                            37,457    8.95     1,420   accepted 28,288
overlaps: A&C 4,281 = 31.2% of A;  B&D 2,924 = 23.2% of B;  share of all component-events 12.9%
occupancy after blocking: mean 137  p50 135  p90 198  max 304
long:short 1.10 overall, 0.99-1.14 by year; 2010 has no A or D (12-1 momentum needs a year)
```

Three things stage 1 has to be written around:

1. **The book is ~135 positions at a 20-bar hold, 200 at the 90th percentile, 304 at the peak.**
   A 50-slot book would refuse two-thirds of accepted events; stage 1's slot count is set here at
   **150 primary, 100 and 250 as shape**, and the path-variant lens will be a full book most days.
2. **A third of the momentum longs are also cheap longs (A&C = 31% of A), and a quarter of the
   high-price shorts are also low-momentum shorts.** The components are not as separate as the
   weights implied. Stage 1 declares the rule now: **a name-day in two components is one position
   at the sum of the two weights** (0.55 for A&C, 0.35 for B&D), and each component's per-trade
   table is reported on its own events and on its exclusive events, both.
3. **Shocks cluster.** The most common spacing between a name's 3×-volume bars is **one day**
   (4,966 of 35,023) — news runs — which is what the one-per-name rule absorbs (22–27% refused);
   the next peak is **62–64 sessions** (2,553), the earnings quarter. **15.4% of spacings fall in
   58–68 against 9.2% uniform** — a real earnings component, about a sixth of events, smaller
   than the 25–40% predicted. Stage 1 carries a **calendar null**: the same book on shocks whose
   spacing from the prior shock is 58–68 versus the rest.

E (the 20-day-loser tilt) covers **42%** of A∪C — more than a tilt; stage 1 reports A and C split
by it rather than sizing on it blind.

---

## 2. Predictions — two of seven

| | prediction | outcome |
|---|---|---|
| X-a | counts ≈ D435 cells; 12–14/day; 1,400+ names | counts exact by `[N]`; **8.9/day** (overlap); 1,420 ✓ |
| X-b | A&C 8–15% of A; B&D 8–15%; share 10–18% | **31% / 23%**; share 12.9% ✓ |
| X-c | 35–50% refused | **22–27%** |
| X-d | occupancy 120–200 at the median | 135 ✓ |
| X-e | quarterly share 25–40% | **15.4%** |
| X-f | E covers 25–35% of A∪C | **42%** |
| X-g | long:short 0.8–1.4 | 1.10 ✓ |

The misses are all about structure I could have computed from the same pools before writing them
(overlap and blocking are set operations on masks that existed). Same lesson, smaller stakes.

---

## 3. What stage 1 is, as a consequence

A pre-registration of the in-sample event study and book on the mining fixture — **not a holdout
read**: components A–D with the weights of `7380bcf` and the overlap rule above; 20-bar cap, next-
open fill, one position per name, market-hedged, equal-risk sizing; **150 slots** primary; both
lenses; **the D435 cells as each component's declared floor**, the state-matched random-event book
as the combined control, the time rotation, and the calendar null. Predictions computed from the
atlas: per-trade gross ≈ +40 weighted, cost ≈ 24–34, net ≈ +6 to +16; the book's net per bar from
that and 137 positions. Then holdout 1 and holdout 2, once each, both unseen by this line.

**Whether to write stage 1 is the principal's.**

---

## 4. R13

Stage 0; no return read; nothing spent. Thirty-sixth look by object.

**Evidence:** `data/d436_stage0.json`. Runner `scripts/run_d436_stage0.py`.
