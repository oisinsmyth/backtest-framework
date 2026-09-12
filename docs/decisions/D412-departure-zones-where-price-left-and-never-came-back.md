# D412 — departure zones: where price left from and never came back

**Status:** design and bar committed BEFORE the runner exists (R8). Result separately.
**Date:** 2026-09-10
**Area:** Strategy research

**A PRE-SCREEN, not a pre-registration of a strategy.** D263's inversion. **The ledger does not
move. Nothing is admitted to any book.**

**Number.** `D412`, by PICKUP's three-command procedure: D400–D411 used, `D407–D410` reserved
(`044f839`), `D390–D399` reserved for `worktree-signal-hunt-part2` (`945cbb5`, live four hours ago).
Master takes D412.

**This does NOT consume D407.** D407 is reserved for a full absorption study and stays reserved and
unspent. Absorption appears here only as a **contrast arm that cannot clear** (§4).

---

## 1. The inversion

Eight constructions have closed, and the diagnosis in PICKUP §0d2 governs all of them:

> A wick — or a volume node, or a swing band, or an inventory field — is evidence that interest was
> **absorbed**, not that it **remains**.

**Every one of them scored where price STALLED.** A shelf, a node, a pivot, a wick: all places price
spent time. The diagnosis says that is precisely the wrong place to look, because time spent is
evidence of filling.

**So score the opposite: where price left from, fast, and has not come back.** If a large order was
resting at a level and price departed before it filled, the unfilled remainder is still there. The
observable is not the departure — it is the **combination of a fast departure and a subsequent
absence of trade at that level.** Absence of trade is the only direct evidence available that
interest was *not* absorbed.

**The property that makes this testable rather than another map:** it is not a static field. It is
an **event with a state**, and the state is destroyed by the very thing that would spend it — the
first return. That gives a first-touch/later-touch contrast no field-based construction has.

---

## 2. THE STRUCTURAL THREAT, STATED UP FRONT

**This is a pure function of the OHLC path**, and PICKUP §0d2's mechanical corollary says such
objects die to a rotation control. D411 ended in exactly that position: an object that beat its
permutation null by 22.4 SE, was untested against the rotation, and was made of price alone.

**And a second threat specific to this design: survivorship in the zone set.** A zone that stays
alive longest is, mechanically, the one furthest from price. Distance predicts both survival and
the size of any subsequent move. **§4's `LVL` control exists for exactly this and it is not
optional** — D403 pre-registered `LVL`, never built it, and three of its arms were unreportable as a
result. **D409's record says: if it is worth running it is worth running with its control.**

---

## 3. THE CONSTRUCTION

Daily bars. `ATR` is the trailing 20-bar mean true range, causal.

**Creation.** Bar `u` creates a candidate zone when it displaces:

```
d_u = |C_u - O_u| / ATR_u  >=  theta            theta = 1.0 primary
zone = [L_u, H_u]                                the departure bar's own range
```

**Arming — and this is the step that makes it a departure.** The candidate does nothing until price
has *left*. It becomes ARMED at the first bar `t > u` (within 20 bars, else discarded) whose close
is fully outside the zone:

```
C_t > H_u   ->  price left UPWARD    ->  DEMAND zone   (sign +1)
C_t < L_u   ->  price left DOWNWARD  ->  SUPPLY zone   (sign -1)
```

**The type comes from the direction of DEPARTURE, not from the bar's own colour.** It is the
departure that is being measured.

**Life and death.** Once armed the zone is ALIVE, for at most `L = 60` bars. It dies at the **first
touch** — the first bar `t'` that trades back into it:

```
HI[t'] >= L_u   and   LO[t'] <= H_u
```

**Consumed on contact.** A zone is spent by its first return, exactly as the absorption diagnosis
says a level is spent by trading. Later touches are recorded separately (§4, T4) and are not
treated as fresh.

**The response.** At first touch, entered at that bar's close — causal, because `HI[t']` and
`LO[t']` are known at the close:

```
resp = sign_zone * ( log C[t'+h] - log C[t'] )        h = 5 primary
```

**THE DIRECTION IS DECLARED HERE AND CANNOT BE RE-READ AFTERWARDS:** a demand zone should be bought
and a supply zone sold, so **`resp` is expected POSITIVE.** D263, D408 and D411 all refused a spread
that arrived with the wrong sign, and D411's primary did exactly that. The same rule binds here.

**Primary cell:** `theta = 1.0`, `L = 60`, `h = 5`. `theta ∈ {0.75, 1.5}`, `L ∈ {20, 120}` and
`h ∈ {1, 21}` are **shape and cannot clear** (R14).

**Universe:** `data/fixtures/us_shorts_daily_raw.csv.gz`, eligibility `floor_mask_v2`, as D406 and
D411 used it. Both the creating bar and the touch bar must be eligible.

---

## 4. THE CONTROLS — and the two that carry the study

Per the standing lesson that **a control must destroy the ingredient being claimed and leave the
rest intact**, each control below names what it breaks and what it keeps. D411's VOL-SHUF preserved
the very sign it was meant to test and its stated inference was wrong; that is not repeated here.

| control | destroys | keeps | answers |
|---|---|---|---|
| **`LVL`** | the level's identity | name, calendar, arming bar, **zone width, and distance from price at arming** | *does the price matter, or only the geometry?* |
| **`ORD`** | the displacement | everything else, same state machine | *does the fast departure earn its place?* |
| **`ABS`** | departure, replaced by its opposite | the machine | *contrast arm — D407's absorption bars, `(V/V̄) ÷ (range/ATR)`, top decile* |
| **`REV2/3`** | freshness | the level | *is "consumed on contact" a real property?* |

**`LVL` is built this time.** For each real zone, a random band in the **same name**, armed at the
**same bar**, with the **same width and the same distance from price**, run through the identical
state machine. This is the control D403 declared and skipped, and D273's trap — reachability is
arithmetic, and any random line reproduces a monotone distance ordering — is the reason it cannot be
skipped again.

**`ABS` cannot clear.** Reporting whichever of departure and absorption scored better would be the
D197–D203 ladder. Departure is primary because it is named primary here, before the run.

---

## 5. THE BAR

| | condition |
|---|---|
| **T1** | mean `resp` at first touch is **POSITIVE**, `h = 5` |
| **T2** | it beats **`LVL`'s p95** |
| **T3** | it beats **`ORD`'s p95** |
| **T4** | first-touch mean **exceeds** the second-touch mean, by more than 2 SE of the difference |

**T1 and T2 together are R15** — a positive gross mean per trade, above the nulls. Costs and
confluences come later and only if this clears.

**200 draws for `LVL` and `ORD`.** The p95's bootstrap SE is carried and **a margin within 2 SE is
recorded UNRESOLVED, not passed** (D373). If a gate lands UNRESOLVED, the answer is more draws, not
a softer bar — D411 §4 resolved one that way.

**T4 is the gate that says whether the state machine is the point.** If the second and third touches
pay the same as the first, then nothing is being consumed, the "unfilled" story is wrong, and what
is left is an ordinary level study.

---

## 6. Stage 0 — measured before any response is read

| | check | why |
|---|---|---|
| **P1** | zone counts: created, armed, touched, expired-unrevisited; age at first touch | If nearly everything is touched within a bar or two, "alive until touched" is not a state and the design is void. **This can end the screen.** |
| **P2** | the joint distribution of zone width and distance-at-arming | `LVL` cannot be matched on quantities that have not been measured. Built before the control, not after. |
| **P3** | `corr(resp, trailing 20-day return at the touch)` | D411's G4, carried forward as standing equipment. Above 0.5 and the result is reported as momentum whatever it scores. |
| **P4** | **look at the object** — one named zone printed in full: symbol, creation date, arming date, touch date, prices, age | Reporting a statistic without inspecting the construction has been my failure twice. |

---

## 7. Assertions, each shown to FAIL

- **`[T+1]`** — the touch is knowable at the close of the touch bar, and the response uses `t'+h`
  against `t'`. Re-derived in a second implementation that never calls the state machine.
- **`[STATE]`** — a zone cannot be touched before it is armed, cannot be armed before it is created,
  and cannot be touched twice as a *first* touch. Asserted on the event table, not in prose.
- **`[SIGN]`** — a synthetic demand zone followed by a rise must pay **positively**; the mirrored
  supply zone must pay positively too when price falls. In money, in the declared direction.
- **`[MATCH]`** — `LVL`'s widths and distances match the real zones' to within a stated tolerance,
  distributionally. **A control that is not matched is not a control**, and this is the assertion
  D403's missing `LVL` never had.
- **`[ELIG]`** — every event, real and control, satisfies `floor_mask_v2` at both bars (D351).
- **`[X]`** — every break must move **the scalar the gate reads**.

---

## 8. Predictions

| | prediction | confidence |
|---|---|---|
| **X-a** | **P1 shows most zones touched within ~5 bars**, so the interesting population is small | moderate-high |
| **X-b** | T1 passes — the raw first-touch mean is positive | moderate |
| **X-c** | **T2 fails: `LVL` reproduces it.** Distance-matching is what killed D273's ordering and I expect it to kill this | **moderate-high** |
| **X-d** | T4 fails — first, second and third touches pay alike | moderate |
| **X-e** | `ABS` and departure score within noise of each other, i.e. what is measured is "a bar happened here" | moderate |

**X-c is the one that matters.** T1 without T2 is the D403 situation exactly — an attractive number
with no matched level under it. **If the departure zones beat width-and-distance-matched random
bands, that is the first time any construction in this programme has done so.**

---

## 9. What this does not do

- No position, no book consequence, no admission. **A screen scores nothing.**
- **No holdout read.**
- **Does not consume D407.**
- **No time rotation** — named, not silently omitted. `LVL` and `ORD` are matched controls on the
  two ingredients claimed; the rotation is a different question and a build of its own, and D411
  left the same gap knowingly.
- **Does not proceed past a failed bar by widening it.**
- **Does not recommend a disposition.** That is the principal's.

---

## 10. R13

**Twelfth look by object on price levels, ninth construction.** The ledger carries 259 terrain looks
and 86 structure looks in, plus D403, D405, D406, D408, D409 and D411. **None has paid.**

**Cost if it fails: one afternoon on a fixture already on disk.**
