# D369 RESULT — the trigger is established beyond doubt, the gate is not, and one verdict is genuinely undecidable

**Status:** RESULT. Pre-registration `8479558`, kernel `7ba776a`, runner `fb561a0` — all committed before this
record (R8). **OHLCV only. No holdout read. Holdout reads spent: 0. Programme total: 0.**
**Date:** 2026-09-07 · **Area:** Strategy research · **personal track**

**Seven of eight.** Q1, Q2, Q3, Q4, Q6, Q7, Q8 confirmed; **Q5, written against the construction, falsified — and
falsified in the direction that matters least, because the verdict it predicted came back UNRESOLVED rather than
either way.**

**These verdicts SUPERSEDE the 200-draw verdicts in D366, D367 and D368**, as committed before any number was
seen.

---

## Headline

**The evidence for the ranking and the evidence for the gate differ by two orders of magnitude.** On the same
construction, the same 10,000 draws:

| | margin over its null's p95, in standard errors of that p95 |
|---|---|
| the **trigger** (time rotation) | **143 – 164 SE**, with **0 of 10,000** draws beating it |
| the **gate** (time rotation of the gate) | **33 SE** for the nine-condition gate, **3.2 SE** for the one-condition gate |

And **the parsimony question cannot be answered on this fixture.** C9 alone against a best-of-ten multiplicity
control lands at **−1.0 SE — UNRESOLVED**, the category this record created before seeing any number precisely so
that a coin-flip could not be written up as a verdict.

## 1. Every arm, at 10,000 draws

Observed, single exit rank 90: **S6 +8.1063**, **C9 +6.9523**, reduced universe **+3.9194** bp/bar net PUB.

| arm | draws | p50 | p95 | **p95 SE** | observed | margin | in SE | rank | beat | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| GATE-ROT / S6 | 10,000 | +3.818 | +6.859 | 0.038 | +8.106 | +1.247 | **32.9** | 99.4% | 62 | **CLEARS** |
| GATE-ROT / C9 | 10,000 | +3.804 | +6.854 | 0.031 | +6.952 | +0.099 | **3.2** | 95.6% | 439 | **CLEARS** |
| A′ / S6 | 10,000 | −0.202 | +2.519 | 0.034 | +8.106 | +5.587 | **164.4** | 100.0% | **0** | **CLEARS** |
| A′ / C9 | 10,000 | −0.203 | +2.484 | 0.031 | +6.952 | +4.469 | **142.8** | 100.0% | **0** | **CLEARS** |
| GATE-ROT / reduced | 10,000 | +1.562 | +4.230 | 0.020 | +3.919 | −0.311 | −15.8 | 92.4% | 757 | **FAILS** |
| C (sign) | 9,600 | +0.008 | +4.449 | 0.056 | +8.106 | +3.657 | 64.9 | 99.9% | 9 | **CLEARS** |
| MULTI / S6 | 10,000 | +0.997 | +3.419 | 0.034 | +4.516 | +1.097 | **32.3** | 99.2% | 81 | **CLEARS** |
| **MULTI / C9** | 10,000 | +0.997 | +3.419 | 0.035 | +3.385 | **−0.034** | **−1.0** | 94.8% | 522 | **UNRESOLVED** |

**ROT is exact, not sampled.** 24 shifts is the whole population at D348's gate width, so it carries no sampling
error and needs none: D366 measured its p95 at −3.48 against an observed +8.09.

## 2. What is superseded

| earlier verdict | margin then | now | status |
|---|---|---|---|
| D366: S6 clears its rotation | +1.07 at 200 draws | +1.247 at **32.9 SE** | **stands, now safe** |
| D367: C9 clears its rotation by 0.50 · D368: by 0.12 | 0.4–1.7 SE | +0.099 at **3.2 SE** | **stands, but thin — 439 of 10,000 random gates beat it** |
| D367: C9 **fails** the best-of-46 by 0.05 | ~0.2 SE | **−0.034 at −1.0 SE** | **SUPERSEDED → UNRESOLVED.** That verdict was noise. |
| D367 Q7: the reduced universe **fails** its rotation by 0.56 | ~1.9 SE | −0.311 at **−15.8 SE** | **stands, now safe** |

**Q8 confirmed and this is the mechanical point of the whole record.** The largest p95 standard error at 10,000
draws is **0.056**; at 200 draws the self-test measured it at **0.301**. D368's two independent 200-draw runs of
the same gate differed by 0.40 — exactly what a 0.30 SE predicts. Every margin this programme has been deciding
on was inside one standard error of its own statistic. It no longer is.

## 3. The verdict that cannot be reached, and why that is the finding

**C9 alone — the one-condition gate — clears its own rotation (3.2 SE) but lands at −1.0 SE against the
best-of-ten multiplicity control.** It is neither a pass nor a fail. 522 of 10,000 shared-offset draws produce a
better timing premium than it does; 5% would be the threshold and it is at 5.2%.

More draws will not fix this. The SE is already 0.035 and the margin is 0.034 — the two are the same size, so
this is not sampling noise that precision can remove; **the effect and the multiplicity penalty are the same
magnitude.** The one-condition gate is exactly as good as the best of ten conditions chosen at random timing,
which is what you would expect if choosing the best of ten conditions is what produced it.

**A check on the multiplicity centres, because the margin is small enough to deserve it.** MULTI centres each
gate on a 400-draw pre-pass median, and those medians are ~0.23 lower than the 10,000-draw medians now available
(S6 +3.590 vs +3.818; C9 +3.567 vs +3.804). **The margin is invariant to this**: a uniform shift in the centres
lowers every draw's score and the observed premium by the same amount, so the p95 and the observed move together
and the difference is unchanged. The two shifts measured are +0.228 and +0.237 — common, as expected, since all
ten gates share the same 400 rotation seeds. Only two of ten centres could be checked at 10,000 draws; that is
the residual and it is stated rather than assumed away.

## 4. The trigger, settled

**Both candidate gates clear the per-name time rotation with zero of 10,000 draws beating them**, at 143 and 164
standard errors. The two A′ distributions are near-identical (p50 −0.202 vs −0.203, p95 +2.519 vs +2.484), which
is the right behaviour: the rotation destroys the *signal*, so what survives should barely depend on which gate
sits on top of it.

**Cross-sectional 12-month momentum, ranked on this floored universe, is not in question.** Everything unresolved
in this programme is about the market-timing overlay.

## 5. A caveat on the reduced-universe arm, raised by the principal

The reduced-universe verdict (FAILS at −15.8 SE) is now precise, but the principal asked whether the test is
**well posed** — whether removing the ten names leaves the gate "expecting something that isn't there". Measured:

- **The removal is asymmetric.** The observed book drops **4.187** bp/bar; the median rotated gate drops
  **2.256**. The real gate is penalised 1.85×.
- **Partly, but only partly, mechanical.** The ten names are defined by the *observed* book's P&L. But rotated
  gates hold many of the same names — a 252-bar hold catches the same long runs whenever it starts — so those ten
  are **45.1%** of the observed book's P&L and a median **~40%** of a rotated book's. In share terms the removal
  is nearly symmetric; the absolute asymmetry comes from the observed book earning more to begin with, which is
  the thing under test.
- **And the premium is retained, not destroyed.** The reduced book's gate premium is +2.357 against the full
  universe's +4.288 — **55% retained**, sitting at the 92nd percentile of its own rotation. D367's framing that
  "the trigger survives and the overlay does not" was too strong; the overlay is weakened, not eliminated.
- **A specification inconsistency, recorded.** The index the gate reads and the dollar-volume hedge are still
  computed over the **full** universe including the ten removed names. Ten of ~500–900 eligible names is small,
  but it was not intended.

**The symmetric test this implies has not been run**: for each rotation draw, remove *that draw's own* top ten
names, so both sides lose their own tail. That is the test that would settle whether the gate is fragile or
merely concentrated, and it is the natural successor to this record.

## 6. Predictions

| | | verdict |
|---|---|---|
| **Q1** | *(load-bearing)* S6 clears its GATE-ROT p95 by >2 SE | **CONFIRMED** — 32.9 SE |
| **Q2** | *(load-bearing)* C9 alone clears its GATE-ROT p95 by >2 SE | **CONFIRMED** — 3.2 SE |
| **Q3** | both clear A′ by >2 SE | **CONFIRMED** — 164 and 143 SE, 0 of 10,000 |
| **Q4** | S6 clears MULTI | **CONFIRMED** — 32.3 SE |
| **Q5** | *(against)* C9 alone **fails** MULTI | **FALSIFIED** — it is UNRESOLVED at −1.0 SE, neither pass nor fail |
| **Q6** | the reduced universe fails its rotation | **CONFIRMED** — −15.8 SE |
| **Q7** | ≥1 flagged verdict comes back UNRESOLVED or reversed | **CONFIRMED** — MULTI/C9 |
| **Q8** | the p95 SE is below 0.10 | **CONFIRMED** — largest 0.056, against 0.301 at 200 draws |
| *check* | the kernel is bit-identical to D366's functions | **exact — zero delta** |

## 7. Assertions

`[FAST]` the kernel is **bit-identical** to D366's own functions on every gate used, rotations included — zero
delta, proved in `7ba776a` across 17 probes and re-asserted per run. `[ID]` S6 equals the stored
`d366_gated_buffer.json` exactly. `[PART]` draws stride across the 8 workers by `i % nparts` with a per-draw seed
`[SEED, 369, arm, i]`, so a draw's value does not depend on which worker ran it; a 4-way strided run reproduces
the serial run bit-identically, and the report re-checks the pooled indices form a partition. `[SE]` every p95
carries a 1,000-resample bootstrap SE. `[SHARE]` `[SHARED]` `[MEM]` hold; `[6]` shows four raising on broken
input. Peak working set 1,181 MB per worker; 8 workers left 13.5 GB free against a 6 GB floor.

**The kernel's optimisation is the permitted kind and no more.** Hoist the invariant (entry and hold masks depend
only on the percentile grid, which a gate rotation never touches), skip what nothing reads (a null needs a mean,
not a drawdown), and index sparsely into a pre-zeroed buffer *of the same shape* so the dense sum reduces the same
values in the same order. Summing only the held entries would have reordered a float sum. 193 ms → 72 ms.

## 8. Status

**Nothing promoted. Book: empty. The avenue is the principal's (R15).**

- **The trigger is established.** 0 of 10,000 on both candidates, at 143–164 SE. No further null work is owed on
  it, and any future study can stop re-proving it.
- **The nine-condition gate clears everything**, including multiplicity, at 32–33 SE — even though D367 showed six
  of its nine conditions are logically inert.
- **The one-condition gate is undecidable here.** It clears its own rotation at 3.2 SE and ties the multiplicity
  control at −1.0 SE. The parsimony that made it attractive is not available on this fixture's evidence, and more
  draws cannot supply it — the effect and the multiplicity penalty are the same size.
- **The reduced-universe test needs its symmetric version** (§5) before its verdict carries the weight D367 gave
  it.

Two things would move this forward and neither is another sweep: the symmetric top-ten test, and the
out-of-sample protocol declared in D367 §5 — which remains unspent.

## 9. Files

`docs/decisions/D369-the-null-precision-rerun.md` (pre-registration) · `scripts/d369_fast_kernel.py` ·
`scripts/run_d369_null_precision.py` · `data/d369_*_p*of8.json`, `data/d369_multi_p50.json`,
`data/d369_report.json`. Reuses `scripts/d348_prep.py`, `scripts/run_d366_gated_buffer.py`,
`scripts/run_d367_gate_deconstruction.py`, `scripts/run_d365_momentum_buffer.py`. The holdout fixture is not read.
