# D411 — signed volume at price: the volume node's missing half

**Status:** design and bar committed BEFORE the runner exists (R8). Result separately.
**Date:** 2026-09-09
**Area:** Strategy research

**A PRE-SCREEN, not a pre-registration of a strategy.** D263's inversion — measure the conditional
against a bar stated before looking, and pay for a full pre-registration only if it clears. That
pattern has now paid four times. **The ledger does not move. Nothing is admitted to any book.**

**Number.** `D411`, by PICKUP's three-command procedure: `git log --all` shows D400–D410 used,
`D407–D410` reserved in `044f839`, `D390–D399` reserved for `worktree-signal-hunt-part2` (`945cbb5`,
live two hours ago). Master takes D411.

---

## 1. The one thing every dead construction had in common

Seven price-level programmes have closed here, and PICKUP §0d2 states the diagnosis:

> A wick — or a volume node, or a swing band, or an inventory field — is evidence that interest was
> **absorbed**, not that it **remains**.

There is a second property they also all shared, and it has never been attacked directly:

> **Every map summed MAGNITUDE.** TERRAIN's S1 stacked volume at price. D403 stacked wick spans —
> and stacked supply and demand **additively**, by the principal's own construction, so a supply
> zone and a demand zone at the same price *reinforced* each other instead of cancelling.

**Volume magnitude cannot distinguish absorption from initiative.** A million shares changing hands
at $50 looks identical whether buyers lifted every offer or sellers hit every bid. That is
information thrown away at the first step of every map this repo has built, and it is the half that
carries the *direction* — which is what "supply" and "demand" actually mean.

**And the consequence for the test is larger than the consequence for the object.** An unsigned map
can only predict `|move|`. A signed map predicts **direction**, which is a far sharper thing to be
wrong about — D403 and D406 could both only be tested on magnitude, and a magnitude conditional is
where D403's "8 of 8 large moves at dense map" turned out to be AUC 0.52.

---

## 2. THE STRUCTURAL THREAT, STATED UP FRONT

Recorded here rather than discovered in the result, in D406 §2's manner:

**This construction is at severe risk of being momentum in a costume.** If price has been falling,
the recent bars sit *above* current price, and falling bars close near their lows, so they carry
negative sign — supply overhead. If price has been rising, recent bars sit below and carry positive
sign — demand underneath. **So the imbalance `I` (§3) will tend to be positive after a rise and
negative after a fall, by construction and with no supply or demand involved.**

That is exactly the TERRAIN mechanism that closed 259 looks. **§5 makes it a declared gate rather
than a hope**, and declares the orthogonalised arm NOW so it cannot be invented afterwards.

---

## 3. THE CONSTRUCTION

For each daily bar `u` with `H > L`:

```
sign_u  =  2 * (C_u - L_u) / (H_u - L_u)  -  1              in [-1, +1]
v_u     =  V_u / mean(V over the window)                     scale-free per name
```

`sign_u` is the close's position within the bar's **own** range: +1 closed on the high (buyers took
it), −1 closed on the low. **Zero-range bars contribute nothing** — as D403's zero-width wicks did —
because they are halts and stub prints, not flow.

Each bar spreads `sign_u * v_u` **uniformly across its own range** `[L_u, H_u]`. The field is
therefore piecewise-constant and **there is no bandwidth and no grid**: the quantity resting in any
interval is exact arithmetic.

```
overlap(u, [a,b])  =  max(0, min(H_u, b) - max(L_u, a)) / (H_u - L_u)
```

**This is deliberate and it is the lesson from D405**, whose `FP` scalar turned out to be grid noise
(`[GRID]` drift −0.1065 against g's +0.0001). A construction with no grid cannot fail that way.

At each bar `t` with price `P` and band half-width `b = k * ATR_t`:

```
D_below  =  SUM_u  max(sign_u, 0) * v_u * overlap(u, [P - b, P))      demand underneath
S_above  =  SUM_u  max(-sign_u, 0) * v_u * overlap(u, (P, P + b])     supply overhead

           D_below - S_above
   I_t  =  -----------------                                          in [-1, +1]
           D_below + S_above
```

**`I` is read from bars `u <= t-1` only.** The current bar never enters its own field. `[LAG]`.

**Primary cell, declared in advance:** window `W = 100` daily bars, `k = 2`, horizon `h = 5`.
`W ∈ {60, 250}` and `k ∈ {1, 4}` are **shape and cannot clear** — R14: sweep the function choice and
read the SHAPE, do not pick the best cell.

**Universe:** `data/fixtures/us_shorts_daily_raw.csv.gz`, eligibility `floor_mask_v2` exactly as
D406 used it. **Daily only.** D403's `[ALIGN]` trap — the 15m fixtures are corporate-action adjusted
and the daily fixture is not, which put ServiceNow's map at five times its own prices — is avoided
entirely by never crossing fixtures. There is no 15m arm and there will not be one in this record.

---

## 4. THE BAR — stated before the runner exists

`I` is ranked **cross-sectionally within each day** and quintiled; the outcome is the mean forward
return over `h = 5` bars.

**THE DIRECTION IS DECLARED HERE AND CANNOT BE RE-READ AFTERWARDS:** demand underneath and no supply
overhead is the bullish configuration, so **high `I` predicts HIGHER forward return.** Q1→Q5
increasing. D263 refused its own largest spread for arriving with the wrong sign; D408 refused a
−5.6%/yr signed spread on the same rule. The same rule binds here.

| | condition |
|---|---|
| **T1** | mean forward return **monotone INCREASING** across Q1→Q5, and `Q5 − Q1 > 0` |
| **T2** | the spread is outside the **p95 of the within-day permutation null** |
| **T3** | the spread is outside the **p95 of VOL-SHUF** |
| **T4** | **the sign is doing the work:** the signed spread is at least **1.5×** the unsigned spread |

**T4 is the gate that decides whether this is a new object at all.** The unsigned arm sets
`sign_u ≡ +1`, which is TERRAIN's volume node rebuilt inside this runner. If it produces the same
spread, D411 is a re-run of a closed programme and the signed field adds nothing.

**Nulls, and why these two.** The design is cross-sectional, so its matched null is the
**within-day permutation** of `I` across names — it holds the cross-section, the calendar and every
forward return fixed and destroys only the ordering. It was decisive in both directions in D409 and
it is the control D406 and D408 both reported spreads without. **VOL-SHUF** permutes each name's
volume across bars while holding the price path exactly fixed: survive it and the information is in
volume; fail it and this is the price path again.

**200 draws for the permutation null, 50 for VOL-SHUF** (each VOL-SHUF draw rebuilds the field).
**A sample p95 is biased toward the centre**, so the p95's bootstrap SE is carried and **a margin
within 2 SE is recorded UNRESOLVED**, not passed — D373's rule.

**A time rotation is NOT run.** For a cross-sectional quintile design the within-day permutation is
the matched null; a per-name time rotation is a different question, and D351's trap (rotate inside
`elig`, never `finT`) makes it a build of its own. Named, not silently omitted.

---

## 5. G4 — THE TERRAIN GATE, AND THE ORTHOGONALISED ARM DECLARED IN ADVANCE

> **G4 — `corr(I_t, trailing 20-day return)`, pooled over eligible name-bars.**

**Declared reading:** D403's map measured −0.009 to −0.109 on this test and that independence was
the single durable positive it produced. **If `|corr| > 0.5`, the primary result in §4 is reported
as a momentum restatement regardless of whether it passes**, because §2 says that is the most likely
way this construction produces an attractive and meaningless number.

**And the arm that can still carry information is declared NOW, so it is not invented afterwards:**

> **`I⊥` — `I` cross-sectionally residualised, each day, on trailing 20-day return and on
> `log(price)`.** Causal, same-day, no fitted parameter carried across days.

`I⊥` runs against the same four gates. **It is the arm that actually answers PICKUP §0d2's
challenge** — whether a construction built on volume carries anything the price path does not.

---

## 6. Stage 0 — the premise checks, before any conditional is read

Per the standing rule that a conditioner's own properties are measured before a study is built on
it. **These are reported whatever they say and two of them can end the screen on their own.**

| | check | why, and the declared reading |
|---|---|---|
| **P1** | `corr(sign_u, sign of (C−O))` and `corr(sign_u, r_u)` | **D269 built a `signed_vol` that was `rel_vol × sign(trailing return)` — deliberately contaminated, as its CONTROL.** If close-in-range signing correlates above **0.95** with the day's own return, this construction *is* that control and the screen says so and stops. |
| **P2** | `corr(I_t, unsigned equivalent)` | If ~1, there is no new object and T4 cannot pass. Measured before T4 rather than inferred from it. |
| **P3** | autocorrelation and half-life of `I_t` | If `I` flips daily it cannot be read at `h = 5`; if it is near-unit-root it is a slow name characteristic and the conditional is a value/size restatement. **This is what sets whether `h = 5` was a sane primary — and `h = 5` stands regardless, because it was declared.** |
| **P4** | look at the field | modes, whether supply concentrates above and demand below, and a named example bar printed. **A test statistic reported without ever inspecting the construction has been my failure twice.** |

---

## 7. Assertions the runner must carry, each shown to FAIL

- **`[LAG]`** — `I_t` re-derived in a second implementation that never calls the field function, and
  the current bar proved absent from its own field.
- **`[QTY]`** — the closed form: a single bar's total contribution over the whole line equals
  `sign_u * v_u` exactly. The overlap arithmetic has no grid, so this is checkable to float error.
- **`[SIGN]`** — a synthetic bar closing on its high must produce `sign = +1` and must move `I`
  **upward** for a price above it; the mirrored bar must move it oppositely. Asserted in the
  direction §4 declared, not in prose.
- **`[ELIG]`** — every name-bar entering a quintile satisfies `elig`, and the nulls draw from the
  same mask (D351).
- **`[X]`** — each break must move **the scalar the assertion reads**, not the name of the check.

---

## 8. Predictions, so they cannot be re-read afterwards

| | prediction | confidence |
|---|---|---|
| **X-a** | **P1 lands between 0.70 and 0.95** — close-in-range and close-minus-open are related but not the same thing, so it will look uncomfortably high without ending the screen | moderate |
| **X-b** | **G4 fires: `corr(I, trailing 20d) > 0.5`** and the raw arm is a momentum restatement | **moderate-high** — this is §2, and it is the single most likely outcome |
| **X-c** | **T4 fails** — the signed spread will not reach 1.5× the unsigned one, because volume magnitude and signed volume concentrate in the same places | moderate |
| **X-d** | **`I⊥` produces a spread indistinguishable from its permutation null** | moderate |
| **X-e** | T1 fails on monotonicity — every quintile design in this programme has failed it, three for three | high |

**X-b and X-c are the two that matter**, and they are the two that decide whether this is a new
object or the seventh map wearing volume. If **both** fail to fire — the field is not a momentum
restatement *and* the sign carries more than the magnitude — that is the first genuinely new
price-level object this programme has produced.

---

## 9. What this does not do

- No position, no book consequence, no admission. **A screen scores nothing.**
- **No holdout read.** Nothing here touches a holdout fixture.
- **No 15m arm**, for the `[ALIGN]` reason in §3.
- **Does not proceed past a failed bar by widening it.** D197–D203 ran five refinements, each
  beating its predecessor, none moving the null gap.
- **Does not recommend a disposition.** The result is reported against this bar and what follows
  from it is the principal's call.

---

## 10. R13

**Eleventh look by object on price levels**, and the eighth construction. The ledger carries 259
terrain looks and 86 structure looks in, plus D403, D405, D406, D408 and D409. **None has paid.**
That base rate is why this is a screen with four gates and a declared abandon-shaped bar rather than
a study with a sweep — and why §6's P1 is allowed to end it in twenty minutes.

**Cost if it fails: one afternoon on a fixture already on disk. No acquisition, no new vendor.**
