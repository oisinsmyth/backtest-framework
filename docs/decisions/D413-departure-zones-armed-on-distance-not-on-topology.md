# D413 — departure zones, armed on DISTANCE rather than on topology

**Status:** design and bar committed BEFORE the runner exists (R8). Result separately.
**Date:** 2026-09-10
**Area:** Strategy research

**A PRE-SCREEN.** D263's inversion. **The ledger does not move. Nothing is admitted to any book.**

**Number.** `D413`, by PICKUP's three-command procedure: D400–D412 used, `D407–D410` reserved
(`044f839`), `D390–D399` reserved for `worktree-signal-hunt-part2` (`945cbb5`, live five hours ago).
Master takes D413. **D407 is not consumed.**

---

## 1. WHY THIS IS NOT THE D197–D203 LADDER, WHICH IS THE FIRST THING TO ESTABLISH

[D412](D412-RESULT-the-state-was-not-a-state-and-the-matched-level-ate-the.md) failed and this
changes its construction. That is the shape of the refinement ladder D197–D203 ran five times, each
version beating its predecessor and none moving the null gap. **Three things separate this from
that, and if a reader disagrees with all three then this study should not be run:**

1. **The defect was diagnosed as a property of the CONSTRUCTION, not chosen from the OUTCOME.**
   D412's arming rule fired when one close sat outside the zone; the median separation at that
   moment was **0.38 ATR against a zone 1.59 ATR wide**. That is a statement about the mechanism,
   visible in `P2`, and it would have been just as true if the study had produced a large positive
   number.
2. **The fix and its reason were committed in D412's own record (`f617b10`) BEFORE this design
   existed** — §9.4, *"a redesign would have to gate on departure DISTANCE, not on the close being
   outside."* The redesign is therefore not selected on results it has already seen.
3. **The change is one parameter, declared once, not a search.** D197–D203 tried five constructions.
   This tries one, at one primary value, with the sweep marked shape.

**The multiplicity cost is real and is not waved away.** This is the **thirteenth look by object** on
price levels and the **second on this construction**, and it is a look *informed by a failed run*.
Under R13 that is strictly worse than an independent look, and §5's bar is not loosened to
compensate — it is the same bar, with one gate ordering fixed (§4).

---

## 2. THE ONE CHANGE

**D412, unchanged in every other respect**, imported rather than restated so the two are provably
the same object. The runner changes exactly one rule:

```
D412  ARM when   C[t] > H_u              or  C[t] < L_u
D413  ARM when   C[t] > H_u + delta*ATR  or  C[t] < L_u - delta*ATR       delta = 1.0
```

**"Left and never came back" is a claim about distance and time. D412 encoded neither** — it encoded
a topology condition, and a topology condition is satisfied by a price that has gone nowhere.

Everything else is held: zone `= [L_u, H_u]` from a bar with `|C−O|/ATR ≥ 1.0`; type from the
direction of departure; at most 60 bars alive; death at the first bar trading back in; response
`sign × (log C[t'+h] − log C[t'])` entered at the touch bar's close; `floor_mask_v2` at both bars.

**Primary cell:** `delta = 1.0`, `theta = 1.0`, `life = 60`, `h = 5`.
`delta ∈ {0.5, 2.0}`, `life ∈ {120, 250}`, `h ∈ {1, 21}` are **shape and cannot clear** (R14).

**`life ∈ {120, 250}` is in the sweep for a mechanical reason, not a hopeful one:** a zone armed a
full ATR further away takes longer to be revisited, so a 60-bar life will expire more of them. The
expiry share is reported, and if most zones expire the primary is thin and says so.

---

## 3. THE AGE ARM — declared as a REPLICATION, because it is not independent evidence

D412 reported first/second/third touches paying **−3.06 / +5.47 / +10.40 bp**, monotone. **That
observation is why the principal asked for this study, so an arm built on it cannot be scored as a
discovery.** It is declared here the way D408 declared R1 — a separate statistic with its own
threshold, which clears nothing on its own:

> **R1 — first-touch response stratified by AGE (bars from arming to touch), in terciles, is
> monotone INCREASING, and the oldest tercile's mean is positive.**

**Two honest qualifications, stated now:**

- **D412's pattern was in TOUCH NUMBER, not age.** They are related and not the same object, so R1
  is a test of a *neighbouring* claim rather than a re-reading of the same numbers. D412's touch-
  number table is *also* recomputed here, and that one **is** a direct re-reading and is reported
  as such.
- **The primary in §2 is ALL first touches, not the aged subset.** Declaring the aged subset primary
  would be selecting the population on D412's outcome. The age structure is reported in full; it
  does not filter the primary.

**R1 clearing does not clear D413** and admits nothing. It would justify a full pre-registration —
D263's ladder logic, and nothing more.

---

## 4. THE BAR — D412's, with one ordering defect fixed

| | condition |
|---|---|
| **T1** | first-touch mean **> 0**, `h = 5`, direction declared in advance |
| **T2** | beats **`LVL`'s p95** |
| **T3** | beats **`ORD`'s p95** |
| **T4** | first touch **exceeds** the second by more than 2 SE of the difference |

**The one fix: T2 and T3 are NOT EVALUATED unless T1 holds.** In D411 and again in D412 a control
gate reported `True` while the estimate and its control were **both negative** — "loses less than
the control" scored as a pass. The conjunction caught it both times and both studies failed anyway,
but the per-gate line reads as support when it is nothing of the kind. **Here T2/T3 return
`not_applicable` when T1 fails, and every control prints its MEDIAN beside the observed value**, so
a null sitting on the wrong side of zero is visible immediately.

**This is a tightening, not a loosening.** No threshold moved.

**Controls, each naming what it destroys and what it keeps** — the rule D411's VOL-SHUF broke:

| control | destroys | keeps |
|---|---|---|
| **`LVL`** | the level's identity | name, calendar, arming bar, and the **(width, distance) pair, permuted across zones** — geometry preserved exactly, `[MATCH]` = 0 by construction |
| **`ORD`** | the displacement | the machine, the mask, the arming rule |
| **`ABS`** | departure, replaced by absorption | the machine — **CONTRAST ARM, CANNOT CLEAR** |

**200 draws. The p95's bootstrap SE is carried and a margin within 2 SE is UNRESOLVED, not passed**
(D373). The way out of UNRESOLVED is more draws — D411 §4 resolved one that way.

---

## 5. Stage 0 — and P1 can end this screen exactly as it ended D412's premise

| | check | declared reading |
|---|---|---|
| **P1** | armed count, expiry share, **median age at first touch** | **The distance gate exists to move this number.** If the median age is still ≤ 2 bars, the gate did not work and the redesign has failed on its own terms. **This can end the screen.** |
| **P2** | distance-at-arming distribution | must now sit near or above `delta`; D412's was 0.38 ATR |
| **P3** | `corr(resp, signed trailing 20d at touch)` | D412's was −0.019 and did not fire. Carried as standing equipment |
| **P4** | **look at the object** — one named zone printed in full | reporting a statistic without inspecting the construction has been my failure twice |

---

## 6. Assertions

`[STATE]`, `[MATCH]`, `[SIGN]`, `[T+1]` and `[ELIG]` are D412's, inherited with the runner. **One is
added, because it guards the only thing that changed:**

- **`[DIST]`** — every armed zone's separation at arming is **≥ `delta × ATR`**, asserted on the
  event table; and the same assertion **must fail** when run against D412's arming rule. A gate that
  cannot be shown to bind on the old behaviour is not a gate.

`[X]`: every break must move **the scalar the gate reads**.

---

## 7. Predictions

| | prediction | confidence |
|---|---|---|
| **X-a** | the distance gate **cuts the population by more than half**, and the median age at first touch rises from 1 bar to **≥ 3** | high |
| **X-b** | **T1 fails again** — the all-ages mean stays ≤ 0 | moderate |
| **X-c** | **T2 fails: `LVL` still eats it.** The level's identity was worth ~0.5 bp in D412 and distance-gating creates no reason for that to change | **moderate-high** |
| **X-d** | **R1 holds** — the age gradient is monotone increasing | moderate |
| **X-e** | `ABS` and departure remain within noise of each other | moderate |

**X-c is the one that matters, again.** D412's `LVL` verdict was contaminated by the degenerate
population — the control bands also armed 0.38 ATR out and were also touched within a bar, so
"matched geometry pays the same" was a statement about bands where price never left. **D413 is the
first clean test of whether a departure level carries anything its own geometry does not.**

**And X-b against X-d is the interesting tension:** if the all-ages mean is flat while the age
gradient is steep, the construction's problem was never the level — it was the clock.

---

## 8. What this does not do

- No position, no book consequence, no admission. **The ledger does not move.**
- **No holdout read. D407 not consumed.**
- **No time rotation** — named, not silently omitted, as in D411 and D412.
- **Does not declare the aged subset primary** (§3).
- **Does not run a third version of this construction.** If D413 fails, the next act is not D414 with
  another parameter.
- **Does not recommend a disposition.** That is the principal's.

---

## 9. R13

**Thirteenth look by object, second on this construction, and informed by a failed run.** The ledger
carries 259 terrain looks and 86 structure looks in, plus D403, D405, D406, D408, D409, D411 and
D412. **None has paid.**

**Cost: minutes, on a fixture already on disk and a runner already written.**
