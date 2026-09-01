# D269 — Volume structure as the orthogonal third input

**Status:** **RUN, AND VOID BY ITS OWN CONTROL.** No stage-2 reading was taken.

**Everything above the RESULT heading was committed in `76eb3da`, BEFORE the test was written.**
**Date:** 2026-09-01
**Area:** Strategy research · **personal track**

---

## Why

[D268](D268-score-independence.md) found the nine price scores collapse to **2.87 effective
independent inputs**, with the first component holding 49.4% of the variance and RSI — the supposed
contrarian — correlating **+0.85** with a MACD level. The consensus proposal needs a genuinely
different input, and volume is the obvious candidate: it is not a transformation of the price path.

**Two stages, and both must pass. Independence without information is useless, and information
without independence is already counted.**

---

## THE DESIGN POINT THAT DECIDES WHETHER THE ANSWER MEANS ANYTHING

**Intraday volume is violently U-shaped by time of day.** A raw volume score would come out
orthogonal to every price score **because it measures the clock**, not because it carries
independent information. That would be a fake pass and it is the single most likely way this test
produces a wrong answer.

**So every volume score is normalised WITHIN BAR-OF-DAY**, against the trailing 20 sessions at the
same clock position. Declared here, mandatory, not a variant.

**And a control is built in to prove the normalisation works — see V-c below.**

---

## The scores — five, fixed here

| score | construction | intent |
|---|---|---|
| `rel_vol` | `log(volume / median volume at this bar-of-day, trailing 20 sessions)` | relative participation |
| `vol_z` | the same quantity, z-scored on the trailing window | participation, scale-free |
| `dollar_vol` | the same, on `close × volume` | participation in money terms |
| `vol_trend` | slope of `rel_vol` over the trailing 8 bars | is participation building or fading |
| `signed_vol` | `rel_vol × sign(trailing 8-bar return)` | **THE CONTROL — deliberately contaminated with price** |

Every window is the committed default or a round number fixed here. **Nothing is swept.**

---

## Hurdles

### Stage 1 — independence (V1)

Re-run D268's instrument on all **fourteen** scores (nine price + five volume).

| | standard |
|---|---|
| **V1a** | **Effective independent scores rises from 2.87 to ≥ 3.5** |
| **V1b** | **At least one volume score has `max abs(rho) < 0.5` against ALL nine price scores** |

**Both.** V1a alone can be satisfied by adding noise; V1b requires a specific score to be distinct.

### Stage 2 — calibration (V2)

**Only scores passing V1b proceed**, and they face D267's hurdles unchanged: **M1** monotone
quintiles, **M2** extreme quintile ≥ `2c`, **M3** a best-of-N shuffle floor with one shared draw.
Horizon **H = 8 bars**, as D267 fixed it.

**A volume score must clear V1b, M1, M2 and M3.**

---

## Predictions, declared before the run

| | prediction | confidence |
|---|---|---|
| **V-a** | **At least one volume score clears V1b.** Volume genuinely is not a function of the price path | **moderate-high** |
| **V-b** | **No volume score clears M1–M3.** [FINDINGS §8](../FINDINGS.md) already closes the volume regime gate (D226 — *"the spike moved between asset classes; a fitted parameter"*), and D267 found the achievable dispersion bounded below cost for every price score | **moderate-high** |
| **V-c** | **`signed_vol` FAILS V1b** — it must correlate with the price blob, because it contains a return sign by construction. **This is a control on the method, not a hypothesis about markets: if `signed_vol` comes out orthogonal, the bar-of-day normalisation is broken and the whole run is void** | **high** |

**V-c is the leg that can invalidate the study rather than merely fail it**, which is why it is
stated as a prediction rather than left implicit.

---

## Stop

**If V1 fails, volume is closed as the third input** and the consensus proposal is closed with it —
no sixth volume score, no second normalisation window, no per-stratum retry.

**If V1 passes and V2 fails, volume is INDEPENDENT BUT UNINFORMATIVE at this horizon.** That is a
real and reportable finding: it would mean a consensus rule could include volume for diversification
without expecting it to carry edge — and D267's cost arithmetic says diversification alone does not
pay a round trip.

**Nothing is promoted under any outcome.** R8 governs.

---

## Ledger

| count | N |
|---|---:|
| fresh — 5 volume scores × 3 strata | **15** |
| carried from D267 | 46,194 |
| **total** | **46,209** |

*D268 scored nothing and did not move the count.*

---

## RESULT — VOID. The control fired, and the diagnosis says the control was wrong, not the method.

`uv run python scripts/run_volume_structure.py` · `data/d269_volume_summary.json`

### What happened

| score | max abs(rho) vs the nine price scores | V1b |
|---|---:|---|
| `rel_vol` | 0.09 | pass |
| `vol_z` | 0.09 | pass |
| `dollar_vol` | 0.01 | pass |
| `vol_trend` | 0.01 | pass |
| **`signed_vol` — the control** | **0.14** | **pass — and it was required to FAIL** |

Effective independent scores rose **2.87 → 4.85 of 14**, so V1a and V1b both passed on their face.

**And V-c fired.** D269 states: *"if `signed_vol` comes out orthogonal, the bar-of-day normalisation
is broken and the whole run is void."* It came out orthogonal. **Stage 2 was not run and no
calibration number from this run is reported.**

### The diagnosis — and it exonerates the normalisation

| | rho |
|---|---:|
| `sign_only` vs `trailing_return` | **+0.279** |
| `signed_vol` vs `trailing_return` | +0.131 |
| **`signed_vol` vs `rel_vol`** | **+0.013** |

**The last row is the tell.** `signed_vol` is `rel_vol × sign(return)`, and it is uncorrelated with
`rel_vol` itself. Multiplying by a symmetric ±1 sends high `rel_vol` to *both* extremes of the
ordering, so the product decorrelates from **both** its parents. It is not a contaminated version of
`rel_vol`; it is a different object.

**And a sign was never going to reach the 0.5 threshold anyway:** `sign_only` on its own reaches only
**+0.279** against `trailing_return`, because a sign discards magnitude and rank correlation is
mostly magnitude. **A control that cannot reach the bar even in its pure form cannot test anything.**

### The verdict, and why it is not reinterpreted

**The control was mis-specified. The normalisation is sound.** That is the honest reading of the
diagnosis — and it is *not* a licence to read stage 2, because "the control was silly, let us use the
result anyway" is exactly the move this programme's stop conditions exist to prevent. **The
pre-registered void condition fired and is honoured.**

**A corrected control requires a new pre-registration**, which is [D270](D270-volume-structure-retest.md).
The V1 numbers will reproduce exactly — the run is deterministic — but they will have been produced
under a control capable of failing.

### What is worth keeping regardless

**A sign-multiplied score decorrelates from both of its parents under rank correlation.** Anyone
testing independence by correlation can be fooled by a symmetric transform into believing a
contaminated input is clean. That is a methodological hazard, it was found by a control doing its
job badly rather than not at all, and it is the reason D270 uses a **two-sided** control.
