# D412 RESULT — the state was not a state, later touches pay more, and the matched level ate the result

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D412-RESULT-the-state-was-not-a-state-and-the-matched-level-ate-the-result.md`. The H1 above is the full title.*

**FAILS THE BAR.** Pre-screen `f48e21b` predates the runner and this file (R8). **The ledger does
not move. Nothing was admitted. No holdout was read. D407 was not consumed.**

Cost: 47 seconds on a fixture already on disk.

---

## 1. P1 VOIDED THE PREMISE BEFORE ANY RESPONSE WAS READ

The pre-screen said, in advance: *"If nearly everything is touched within a bar or two, 'alive until
touched' is not a state and the design is void. **This can end the screen.**"*

```
candidates 266,548   armed 262,400   touched 241,415   expired unrevisited 20,985 (8.0%)
age at first touch   p10 1   p50 1   p90 12 bars      within 5 bars 81.1%
```

**The median zone is touched one bar after arming. 92% are touched at all.**

**And P2 shows the mechanism, which is my construction's fault and not the market's:**

```
distance/ATR at arming   p10 0.06   p50 0.38   p90 1.18
width/ATR                p10 1.23   p50 1.59   p90 2.33
```

A zone arms as soon as **one close** sits outside it, and the median separation at that moment is
**0.38 ATR** — against a zone **1.59 ATR wide**. Price is barely outside the zone when the clock
starts, so it steps straight back in. **The "and never came back" half of the idea was never
measured.** What was measured is "price returns to the previous bar's range", which is close to
universal.

**X-a was right and I under-called it:** I predicted "most touched within ~5 bars"; the median is 1.

---

## 2. The bar

`theta = 1.0`, `life = 60`, `h = 5`, 240,088 resolved first touches.

```
first touch   n 240,088   mean  -3.06 bp  +-1.27   median +0.00   win 49.7%
touch #2      n 229,596   mean  +5.47 bp  +-1.28
touch #3      n 220,626   mean +10.40 bp  +-1.31
```

| | condition | outcome |
|---|---|---|
| **T1** | first-touch mean > 0 | **FAIL** — **−3.06 bp, −2.4 SE.** The direction was declared positive in advance |
| **T2** | beats `LVL` p95 | **FAIL** — −12.4 SE |
| **T3** | beats `ORD` p95 | passes, and §4 explains why that means nothing |
| **T4** | first touch > second by 2 SE | **FAIL — and inverted.** −8.53 bp against a 2 SE band of 3.61 |

**D412 FAILS.** The direction arrived wrong for the second study running, and it is refused on the
same rule D263, D408 and D411 applied to their own.

---

## 3. LVL WAS BUILT THIS TIME, AND IT ATE THE RESULT

D403 pre-registered `LVL` and never built it, which made three of its arms unreportable. It exists
now, and it is the strongest thing in this record:

```
LVL  200 draws   observed -3.06   p5 -4.82   p50 -3.52   p95 -2.37 bp   -12.4 SE
```

The control permutes the **(width, distance) pair across zones within direction**, so the joint
geometry distribution is preserved **exactly** — `[MATCH]` returns `0.0e+00`, not a tolerance. Same
name, same calendar, same arming bar, same geometry; **only the level's identity is destroyed.**

**A random band with a real zone's geometry pays −3.52 bp. The real zone pays −3.06.** The level's
identity is worth about half a basis point and the observed value sits inside the null.

**This is D273's trap measured rather than argued.** Reachability is arithmetic; so, it turns out,
is the response. **X-c was the prediction that mattered and it was correct.**

---

## 4. T3 "PASSES" AND IT IS THE SAME EMPTY PASS AS D411's T3

```
ORD  200 draws   observed -3.06   p5 -6.97   p50 -5.49   p95 -3.79 bp   +10.4 SE
```

Departure zones beat ordinary bars' zones by 10.4 SE — **and both are negative.** "Loses less than
the control" is not a result, and a gate written as *beats the control's p95* cannot tell the
difference when the estimate is on the wrong side of zero.

**That is now twice in two studies.** D411's T3 passed the same way, with VOL-SHUF centred at −3.4
bp. The conjunction `T1 and T3` catches it, and both studies failed anyway — but the per-gate line
in a summary table reads as support when it is nothing of the kind. **A control comparison is only
interpretable once the estimate is on the right side of zero**, and that ordering belongs in the
gate, not in the commentary.

---

## 5. THE FRESHNESS PREMISE IS NOT ABSENT — IT IS BACKWARDS

X-d predicted the touches would pay alike. They do not:

```
touch #1   -3.06 bp        n 240,088
touch #2   +5.47 bp        n 229,596
touch #3  +10.40 bp        n 220,626
```

**Monotone, and the third touch is the best one.** The construction says a level is spent by its
first return; the data says the opposite, with the first return the *worst* moment to act.

**And the event counts are their own verdict on the state machine.** Of 240,088 zones with a first
touch, **229,596 get a second and 220,626 a third** — 92% survive to be touched three times inside
60 bars. **A state that almost never ends is not a state**, which is P1's finding arriving a second
time from a different direction.

---

## 6. What was clean

- **P3 does NOT fire.** `corr(resp, signed trailing 20-day return at the touch)` = **−0.0189** on
  240,080 events. **This is not momentum contamination** — unlike D411, whose G4 fired at +0.508.
  The object is genuinely independent of recent price. It is also worthless, which is the useful
  pairing: independence from the price path is necessary and nowhere near sufficient.
- **`ABS`, the contrast arm, scores −2.27 ± 1.15 against departure's −3.06 ± 1.27** — a difference
  of 0.79 against a 1.71 combined SE. **X-e correct:** absorption and departure are the same
  number. What is being measured is *"a bar happened here"*, not which kind. **D407 is not consumed
  by this** and is not answered by it either; this is one decile of one absorption statistic on a
  degenerate state machine.
- **The sweep contains no positive cell beyond noise.** The best is `theta = 1.5` at **+1.04 ±
  2.55** — under half a standard error, on the thinnest cell (64,131 events). `h = 21` is −7.13,
  `theta = 0.75` is −4.69 on 478,045 events.

---

## 7. Predictions

| | prediction | outcome |
|---|---|---|
| X-a | most zones touched within ~5 bars | **correct**, and understated — median 1 bar |
| **X-b** | **T1 passes, the raw first-touch mean is positive** | **WRONG** — −3.06 bp, −2.4 SE |
| **X-c** | **T2 fails: `LVL` reproduces it** | **correct**, −12.4 SE |
| X-d | T4 fails, touches pay alike | **half right** — T4 fails, but they do not pay alike; later touches pay strictly more |
| X-e | `ABS` ≈ departure | **correct** |

---

## 8. Assertions

- **`[MATCH]`** quantile gap **0.0e+00** — exact, because the control permutes real geometry rather
  than approximating it. This is the assertion D403's missing `LVL` never had.
- **`[STATE]`** no zone armed at or before creation, no touch at or before arming, no double-counted
  first touch, no zone armed with price inside it. Asserted on the event table.
- **`[SIGN]`** demand +536.2 bp and supply +682.9 bp on synthetic paths — **both positive**, in the
  declared direction, because the response is sign-adjusted.
- **`[T+1]`** entry at the touch bar's close, which is causal: `HI[t']` and `LO[t']` are known then.
- The first-touch path takes `argmax` rather than `cumsum` — the LVL null calls it 200 times on a
  15.7M-cell window, and the cumsum it does not do was the run's largest single cost.

---

## 9. What this leaves

1. **The construction as specified does not isolate its own idea.** Arming at 0.38 ATR of separation
   measures "price came back to the last bar", not "price left and stayed away".
2. **`LVL` now exists**, is exact, and is reusable. It is the most durable thing here — every future
   level construction in this repo can be judged against matched geometry instead of against
   nothing.
3. **Later touches pay more than first touches, monotonically.** Unexplained, uncontrolled, and
   stated as an observation rather than a finding — it has had no `LVL`, no rotation, and it is the
   kind of number that has looked good before and died.
4. **A redesign would have to gate on departure DISTANCE, not on the close being outside** — require
   price to reach some multiple of ATR away before arming, which is what would make the surviving
   population the one the idea is about. **That was not run**, deliberately: changing the
   construction after seeing it fail is the D197–D203 ladder, and this would have been the fourth
   consecutive study to do it.
5. **Size:** −3.06 bp per event. Nothing here is near a cost bar.

**Disposition is the principal's.** This record reports against the bar and stops.

---

## 10. R13

Twelfth look by object on price levels, ninth construction. **None has paid.**

**Evidence:** `data/d412_departure_zones.json`. Runner `scripts/run_d412_departure_zones.py`, which
imports D411's panel and holdout guard rather than restating them.
