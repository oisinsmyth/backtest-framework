# D411 RESULT — the sign is the half that matters, the volume is decorative, and my T3 said the wrong thing

**FAILS THE BAR on both arms.** Pre-screen `f0a8a14` predates both runners and this file (R8).
**The ledger does not move. Nothing was admitted. No holdout was read.**

Cost: 23 min for the screen, 19 for the `I⊥` gates, 73 to resolve T3. Fixture already on disk.

---

## 1. Both arms, against the committed bar

`W = 100`, `k = 2`, `h = 5`, 4,187 dates × 1,573 names, 43.4% of cells eligible.

```
                Q1      Q2      Q3      Q4      Q5    spread
signed  I     +4.1    +8.4    +4.4    +9.7    +1.7     -2.4 bp    <- PRIMARY
unsigned U    +7.2    +8.4    +4.4    +5.8    +2.0     -5.2 bp
I_perp        +2.9    +6.6    +5.9    +6.8    +5.8     +2.9 bp
U_perp        +5.2    +6.2    +6.5    +4.5    +5.2     +0.0 bp
```

| | raw `I` | `I⊥` (declared in §5 in advance) |
|---|---|---|
| **T1** monotone increasing, spread > 0 | **FAIL** — −2.4 bp, and the sign is **opposite to the one I declared** | **FAIL** — +2.9 bp but a step at Q1, not a gradient |
| **T2** outside the permutation p95 | **FAIL** | **PASS** — +2.9 vs p95 +1.5, **+22.4 SE** |
| **T3** outside VOL-SHUF p95 | passes on a technicality — see §3 | **FAIL** — +2.93 vs p95 +3.15, **−3.75 SE** |
| **T4** signed ≥ 1.5× unsigned | **FAIL** — 0.45× | **PASS** — **62.55×** |

**D411 FAILS.** No arm cleared, and no pre-registration is earned.

---

## 2. THE RAW ARM CAME IN WITH THE WRONG SIGN, AND IT IS REFUSED

I committed, before the run: *"demand underneath and no supply overhead is the bullish
configuration, so high `I` predicts HIGHER forward return."* The observed spread is **−2.4 bp**, and
it sits **beyond the permutation null's p5** (−2.0 ± 0.07) — a real effect pointing the other way.

**It cannot be cashed and it is not offered as anything.** D263 refused its own largest spread on
this rule and D408 refused a −5.6%/yr signed spread on it. The direction was named in advance
precisely so this could not be re-read afterwards.

**It also has a boring explanation.** G4 fired at **+0.5084**: `I` is half a restatement of trailing
return. So the raw arm is short-horizon *reversal* on a momentum proxy — which is why the sign
flips with horizon and window:

```
h= 5   -2.4 bp        W=100  -2.4 bp
h=21  +12.9 bp        W=250  +5.1 bp     (and +7.6, +6.6 at k=1, k=4)
```

Reversal at a week, momentum at a month, and **the spread turns positive once the window is long
enough that recent price stops dominating the field.** That is one coherent contamination story, not
three findings.

---

## 3. MY T3 EXPLANATION WAS WRONG, AND THE CORRECTION CHANGES WHAT THIS STUDY FOUND

The pre-screen said of VOL-SHUF: *"survive it and the information is in volume; **fail it and this
is the price path again**."*

**The second half of that sentence is false, and I should have seen it when I wrote the control.**
VOL-SHUF permutes volume across bars **while holding the price path fixed** — and `sign_u` is
computed from `C`, `H`, `L`. **So a VOL-SHUF draw still carries every sign at every price, correct
and in place; only the volume weights are scrambled.** Failing VOL-SHUF therefore means *"the volume
weighting adds nothing beyond sign and geometry."* It does **not** mean the object is the price
path.

The question I thought T3 answered is actually answered by **T4**, and T4 says the opposite:

```
raw:          signed -2.4  vs  unsigned -5.2  ->  0.45x    the sign ATTENUATES
residualised: signed +2.9  vs  unsigned +0.0  ->  62.55x   the sign is ALL THAT IS LEFT
```

**Residualise both fields on trailing 20-day return and log price and the unsigned volume node —
TERRAIN's object, rebuilt inside this runner — goes to exactly +0.0 bp.** The signed field keeps
+2.9. So the sign is not decorative; **the volume is.**

**What actually survives is sign-weighted geometry with no volume in it:** where up-closing bars sit
relative to price versus where down-closing bars sit. VOL-SHUF's median is **+1.96 bp** against an
observed **+2.93** — two-thirds of the residual spread is reproduced with volume destroyed.

**This is D405's finding again in a different construction** — there the scalars were momentum with
decorative volume at a 0.97 shuffle correlation. Two independent constructions, same verdict on the
same ingredient.

---

## 4. Resolving T3 rather than reporting it ambiguous

The declared 50 draws put T3 at **−1.2 SE**, inside D373's 2 SE band, so it was recorded
**UNRESOLVED** — a margin that small is not a fail.

**The way out of UNRESOLVED is more draws, not a softer bar**, so 200 were run at a fresh seed:

```
 50 draws   observed +2.9   p5 +0.7   p50 +1.8   p95 +3.1   margin -1.2 SE   UNRESOLVED
200 draws   observed +2.93  p5 +0.41  p50 +1.96  p95 +3.15  margin -3.75 SE  RESOLVED, FAILS
```

The point estimate barely moved; the SE halved and that is what settled it. **The bias ran the way
the rule predicts** — a sample p95 is biased toward the centre, so the additional draws pushed p95
*up*, away from the observed value, not toward it.

---

## 5. Stage 0 — three of four premises measured before the conditional

| | measured | reading |
|---|---|---|
| **P1** | `corr(sign, (C−O)/O)` **+0.663**, vs log return +0.540 | **Clears the 0.95 bar.** Close-in-range signing is *not* D269's deliberately-contaminated `rel_vol × sign(trailing return)`. This was the check that could have ended the screen in twenty minutes. |
| **P2** | `corr(I, unsigned)` **+0.932** | Called T4's raw failure before the conditional ran. Doing this *first* is why T4's failure was expected rather than surprising. |
| **P3** | ac1 **+0.897**, half-life **6.4 bars** | `h = 5` was a sane primary, not a lucky one. |
| **G4** | `corr(I, trailing 20d)` **+0.5084** | **Fires**, barely. §2. |

**P4 — the object was looked at, and it has a defect worth recording.** `|I| = 1` on **10.3% of
eligible bars**, because the ratio normalisation makes a band with *zero* supply overhead score +1
no matter how thin the demand below it:

```
AAL 2010-06-01   I +1.0000   D_below 0.064   S_above 0.000   close 8.64
```

**A saturated field is a one-sided field, and the magnitude is thrown away at the last step.**

---

## 6. `[SIGN]` found a property of the construction, not a bug

The assertion failed first at `supply below did not lower I`, and investigating rather than
loosening it found the reason: **§3 reads only `max(sign,0)` below and `max(−sign,0)` above, so
supply below price and demand above price are discarded entirely.** The trapped-short and
trapped-long halves of the field — which are D405's overhang reading — never enter.

Confirmed on synthetic bars rather than asserted in prose: demand below +0.9615, supply above
−0.9734, **supply below −0.1834 against a baseline of −0.2000**, i.e. it moves `I` only through the
volume normalisation. That is the pre-registered construction behaving as written, and it is half
the field.

A second property fell out of the same test: **a perfectly neutral name has an empty field.** Every
bar signing to exactly zero gives `D_below = S_above = 0` and `I` undefined.

---

## 7. Predictions

| | prediction | outcome |
|---|---|---|
| X-a | P1 lands 0.70–0.95 | **wrong** — 0.663, below the range, in the harmless direction |
| X-b | G4 fires | correct — +0.5084 |
| X-c | T4 fails | **correct on the primary** (0.45×), **wrong on `I⊥`** (62.55×) |
| **X-d** | **`I⊥` is indistinguishable from its permutation null** | **WRONG — it beat it by 22.4 SE** |
| X-e | T1 fails | correct, on both arms |

**X-d was the miss that mattered.** I expected the residual to be nothing. It orders the
cross-section decisively — and then fails on the control that shows the ordering does not need the
volume.

---

## 8. Assertions, and the `[X]` breaks

- **`[QTY]`** partition of unity, error **0.0e+00** — exact, because the construction has no grid.
- **`[LAG]`** a second implementation looping `u ∈ [t−W, t−1]` and never calling the field function
  agrees to **1.7e-16**.
- **`[SIGN]`** §6 — and it *fired*, on the scalar the verdict reads.
- **The fast field is guarded by equality, not inspection.** The four shifted array copies per lag
  became slice views and `inv` hoisted out of the loop: **2.29× / 2.48× / 2.53×** on three cells,
  **bit-identical** to the loop it replaced (`--verify`). The multiplication order was left alone
  deliberately so bit-identity was achievable.
- **The residualiser rewrite** (3×3 normal equations for `lstsq`) matches to **2.8e-14** on a
  200-day slice.

---

## 9. What this leaves

1. **The raw construction is momentum, and its own G4 says so.** §2.
2. **The sign is the informative half and the volume is not** — and that is the reverse of what the
   pre-screen expected to find, established by T4 on residualised fields where the unsigned
   comparator is exactly zero. §3.
3. **What survives is a pure OHLC object**, which PICKUP §0d2 predicts dies to a rotation control —
   **and the time rotation was declared NOT RUN in §4 and was not run.** So the surviving object is
   untested against the control most likely to kill it. That is a stated boundary of this screen,
   not a finding.
4. **Size, so it is not mistaken for a near-miss:** +2.9 bp on a Q5−Q1 book over five sessions,
   gross, ≈ 0.6 bp/bar. D285 measured **33.8 bp/side** on the names actually held. Even taken at
   face value it is not tradeable, and it does not meet R15 because it does not clear its nulls.
5. **Unspent:** the four other constructions from the 2026-09-09 slate, and D407/D410 in their
   reserved block.

**Disposition is the principal's.** This record reports the result against the bar and stops there.

---

## 10. R13

Eleventh look by object on price levels, eighth construction. **None has paid.**

**Evidence:** `data/d411_signed_volume_at_price.json` (both raw arms, the sweep, stage 0, the
nulls), `data/d411_perp_gates.json` (the declared 50 draws) and
`data/d411_perp_gates_resolve.json` (200 draws, T3 resolved). Runners
`scripts/run_d411_signed_volume_at_price.py` and `scripts/run_d411_perp_gates.py`.
