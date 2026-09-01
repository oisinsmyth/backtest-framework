# D269 — Volume structure as the orthogonal third input

**Status:** PRE-REGISTERED. Committed **before the test is run**. Nothing here is a result.
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
