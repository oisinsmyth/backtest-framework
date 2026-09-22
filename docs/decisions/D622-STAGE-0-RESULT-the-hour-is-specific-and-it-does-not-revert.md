# D622 STAGE 0 RESULT — the hour pair is specific to the index roots and is the family maximum of the clock, and it does NOT revert: four of six predictions hold and the two that fail are the mechanism's own

**Pre-registration:** [`D622`](D622-PRE-REG-the-last-hour-decline-and-who-must-be-flat.md), committed alone
before this runner existed. **Runner:** `scripts/stage0_d622_close_inventory.py` ·
**artifact:** `data/stage0_d622_close_inventory.json` · 2.3 s · in-sample 2016-01-04 → 2023-12-29, 1,993 ES
sessions and eight roots of hourly bars. **No holdout was read; the 2024+ slice is untouched.**

## VERDICT

> **PARTLY SUPPORTED — NO AGGREGATE VERDICT.** Passed **P4, P5, P7, P9**; failed **P6, P8**. Under the
> pre-registration's own disposition a mechanism test that is partly supported is a description and not a
> finding, and the two failures are not peripheral: **P8 is the test that separates inventory from
> information, and it fails in the direction that says information.**

The effect is real, and it is far more specific than anything else this programme has found. It just is not
the thing §1 said it was.

## 1. The arm, and the two specificity tests it passes

`H1 = r(14:00→15:00)/σ`, short 15:00 → 16:00 when `H1 ≤ −1.0` — the threshold declared in the record, not
tuned. **182 sessions, 9.1 % of the window; mean +6.83 bp; t +1.23; hit 58.8 %; gross $11.14 at one MES
against a $4.25 round trip.** Against the **enumerated** rotation null of the signal side, rotated as a block
over 1,974 offsets: observed **+6.83** against p50 +0.06 and **p95 +4.40, rank 0.9965** — clears.

**P5 — the effect is specific to the 16:00 cash close. PASSES, and this is the test that killed D530.**

| root | | n | mean | z | hit |
|---|---|---:|---:|---:|---:|
| ES | index | 180 | **+8.88 bp** | +1.57 | 0.606 |
| NQ | index | 177 | **+12.69 bp** | +2.04 | 0.582 |
| YM | index | 171 | **+7.04 bp** | +1.53 | 0.556 |
| ZN | other | 183 | −0.57 | −0.88 | 0.393 |
| ZB | other | 216 | −0.00 | −0.00 | 0.389 |
| GC | other | 139 | +0.92 | +0.44 | 0.489 |
| CL | other | 247 | −4.01 | −1.21 | 0.490 |
| 6E | other | 131 | +0.11 | +0.14 | 0.473 |

All three index roots **agree in sign** and are 7–13 bp; the five others average **|z| 0.538**. D530's version
of this test is where its per-root signs disagreed (NQ +0.52, RTY +0.65, ES −0.45, YM −0.54). This one does
not disagree.

**P9 — the deadline placebo. PASSES: the tested pair is the family maximum of all 21 usable ES hour pairs**,
at rank 21 of 21. The runner-up is h21→h22 at +5.32 bp against the tested pair's +8.88, then h12→h13 at
+4.24 and h15→h16 at +3.79. The hour pair was a **1-of-22 selection** from FINDINGS §81's census and it
survives being priced as one.

**P7 — the forced trade arrives. PASSES.** The closing hour takes **23.69 %** of session volume on arm days
against **20.70 %** otherwise, on an even share of 15.38 % — a hump of **1.54×** against 1.35×. D530 measured
1.10×–1.48× as the unconditional baseline; arm days sit above its top.

**P4 — the deadline binds. PASSES on the declared comparison, weakly.** The three 20-minute legs read
**+3.07, −0.26, +4.02 bp**. The third exceeds the first, which is what the record required, but the pattern
is not a ramp — the middle leg is negative and the largest leg's own t is 1.00. Reported as passing the
stated test and not as evidence of a smooth deadline effect.

## 2. The two failures, and why they matter more than the four passes

**P8 — the reversal test. FAILS, decisively and in the informative direction.** Conditional on the arm, the
subsequent returns are:

| horizon | mean | t |
|---|---:|---:|
| overnight to 09:30 | **−9.19 bp** | −0.96 |
| the next full session | **−5.24 bp** | −0.44 |
| five sessions (D483's own hold) | **−2.71 bp** | −0.09 |
| the next session after the *deepest* declines (`H1 ≤ −2`, n 62) | **−36.13 bp** | — |

The decline **continues** rather than reverting, and it continues *more* after the largest declines, which is
the exact opposite of the predicted pattern. An inventory discharge pushes price away from fair value and
must give some back; this gives back nothing and takes more. **That is a repricing signature.** The
pre-registration said what to do with this outcome and it is done here: the continuation is not unreal, but
§1's mechanism is the wrong story for it, and the effect therefore **has no named counterparty again**.

**P6 — the level. FAILS, and in the opposite direction to the prediction.** Arm sessions where the
14:00–15:00 hour took price below the prior session's low earned **+5.00 bp (n 115)**; those that held above
it earned **+9.99 bp (n 67)**. Running through resting liquidity made the continuation *smaller*. Combined
with [D483](D483-RESULT-the-channel-is-not-the-ingredient-a-close-4pc-below-the.md)'s finding that the
hand-drawn lines add −2.2 bp over a plain level, the "break a level where stops cluster" channel is now
refuted from two directions on this repository's own data.

## 3. The asymmetry that motivated the record does not survive its declared threshold

This is the correction the record owes most plainly. §6 of the pre-registration disclosed a median-|H1|
split in which the down side earned $5.27 a trade at t 3.04 against the up side's $1.92 at t 1.23 — the
asymmetry that made an *asymmetric* forced seller the hypothesis at all. At the **declared 1.0σ threshold**:

| | n | mean | t |
|---|---:|---:|---:|
| down arm (`H1 ≤ −1`) | 182 | **+6.83 bp** | +1.23 |
| up arm (`H1 ≥ +1`) | 187 | **+5.27 bp** | +1.34 |

**The asymmetry is 1.56 bp and the up side's t is the larger of the two.** The effect is very nearly
symmetric once the threshold is declared rather than fitted to the median. That removes the observation
which pointed at an asymmetric participant, and it is why §1's mechanism has no support left after P8: the
motivating asymmetry was a property of where the split was drawn.

## 4. What is actually established

Stripped of the mechanism that failed, four facts survive and they are not small:

1. **Something is specific to 14:00 → 15:00 → 16:00 on the equity index roots.** All three agree in sign at
   7–13 bp while five non-index roots read nothing, and the pair is the maximum of 21 on its own clock. Two
   independent specificity tests, one across instruments and one across hours, both pass.
2. **The closing-hour volume hump is larger on those sessions** (1.54× against 1.35×), so something does
   arrive.
3. **It does not revert at any horizon out to five sessions**, and continues most after the largest declines.
4. **It is not asymmetric** at a declared threshold, and it is **not** stronger through a broken level.

Facts 1–2 with 3–4 describe a **repricing that concentrates in the last hour of the index session** — not an
inventory discharge and not a stop cascade. A mechanism for it would have to explain why the repricing is
instrument-specific and hour-specific while being direction-symmetric and persistent. Late-day information
arrival and the cash close as a price-discovery event are the obvious candidates and neither is tested here.

## 5. What is spent, and what is not

The in-sample window was read for the six predictions and the reproductions. **The holdout was gated on P5
and P7 and both passed — but P8's failure removes the mechanism the gate was protecting, so the 2024+ slice
is NOT read**, and nothing here asks to read it. The deferred signed-flow premise check on the reserved
`tbbo` year (§4 of the pre-registration) is **moot**: it was designed to test whether liquidity providers are
long into the close and sell, and P8 has already shown that whatever sells does not behave like an inventory
holder.

**The economic line, for the record and not as a verdict** — Stage 0 declared no economic bar. The arm's
gross is **$11.14 a trade against $4.25** at one MES, the best ratio in this programme, on **182 sessions
over eight years, 23 a year, at t 1.23**. At that firing rate the power arithmetic of
[D618 §3e](D618-STAGE-0-RESULT-the-band-around-the-price-was-the-signal.md) applies with full force, and a
holdout could not resolve it even if the mechanism had survived.

Every audit raised on its break: leg additivity to **3.5e-12 bp** with a one-bp slip refused and the window
being its own third leg refused; the rotation null refused a constant outcome and refused too few offsets;
the declared-output guard fired on a missing block.

**Nothing is admitted. No line is closed** — under R15 that is the principal's call, and §4's disposition for
this outcome was "reported cell by cell with no aggregate verdict", which is what this record does.
