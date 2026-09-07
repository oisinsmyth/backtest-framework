# D368 RESULT — neither a knife-edge nor a curve: the gate works only at its tightest setting, and the null cannot resolve the margin

**Status:** RESULT. Pre-registration `aee38bb`, runner `d04f92d` — both committed before this record (R8).
**OHLCV only. No holdout read. Holdout reads spent: 0. Programme total: 0.**
**Date:** 2026-09-07 · **Area:** Strategy research · **personal track**

**One of eight confirmed** — Q5. Q1 (load-bearing) falsified; Q2, Q4, Q6, Q7 falsified; **Q3, written *against*
the construction, also falsified**, which is the one piece of good news.

---

## Headline

**The gate is not a knife-edge — and it is not a smooth curve either.** Relaxing "at a 252-bar high" by half a
percent nearly doubles the on-share and costs only a sixth of the timing premium, so the effect does not live at
a single point. But **only the tightest setting clears its own rotation, and it clears by 0.12 bp/bar** — a margin
smaller than the null's own sampling error between runs. The premium then wanders rather than decaying.

**The most consequential finding is methodological: 200 rotation draws cannot resolve the margins this programme
has been deciding on.**

## 1. Family A — C9(d) alone

Timing premium = net − the median of that gate's own rotation. "Clears" compares **net** to that rotation's p95.

| d% | open% | gross | net | rot p50 | **premium** | rot p95 | rank | beat | clears | trades | Sharpe |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **0** | 9.5% | +8.53 | **+6.95** | +3.84 | **+3.11** | +6.83 | 97.0% | 6 | **YES** | 1,013 | 0.796 |
| 0.5 | 18.1% | +7.65 | +6.01 | +3.42 | +2.58 | +6.49 | 89.5% | 21 | no | 1,160 | 0.706 |
| 1 | 25.5% | +6.96 | +5.30 | +3.39 | +1.91 | +6.27 | 85.5% | 29 | no | 1,256 | 0.626 |
| 2 | 38.1% | +7.16 | +5.46 | +3.13 | +2.33 | +5.81 | 91.0% | 18 | no | 1,368 | 0.649 |
| 5 | 60.3% | +6.81 | +5.04 | +2.65 | +2.39 | +5.19 | 92.5% | 15 | no | 1,702 | 0.637 |
| 10 | 76.1% | +4.12 | +2.29 | +2.21 | +0.08 | +3.89 | 53.0% | 94 | no | 2,021 | 0.315 |

**Premium curve: +3.11 → +2.58 → +1.91 → +2.33 → +2.39 → +0.08.** One of six clears; two inversions.

**Q3 failed, and that matters.** The against-prediction said the premium at d = 0.5 would fall below half of
d = 0's. It came in at **+2.58 against a +1.56 threshold — 83% retained** while the on-share nearly doubled from
9.5% to 18.1%. **"At the high" is therefore not a point effect**, which is the opposite of what the cap sweep
showed and is genuinely reassuring about the mechanism.

**Q1 failed, and that matters more.** Only d = 0 clears its own rotation, and it does so by **+6.95 against a p95
of +6.83 — 0.12 bp/bar, with 6 of 200 draws beating it.** Net falls faster with d than the rotation's p95 does, so
every relaxed gate becomes indistinguishable from its own random placement even though its premium is still
positive.

**Q2 failed: the curve is not monotone.** It falls to +1.91 at d = 1, then rises to +2.33 and +2.39 before
collapsing at d = 10. That is a third wandering surface in this construction, after the cap sweep and the
ten-bar C4 effect.

## 2. Families B and C — the redundancy does not break as predicted

| d% | A premium | B premium (C9+C4) | C premium (all nine) | C − A |
|---|---|---|---|---|
| 0 | +3.11 | +4.22 | **+4.24** | +1.13 |
| 0.5 | +2.58 | +3.99 | +4.06 | +1.48 |
| 1 | +1.91 | +2.74 | +2.67 | +0.76 |
| 2 | +2.33 | +3.07 | +2.89 | +0.56 |
| 5 | +2.39 | +1.85 | +2.36 | **−0.04** |
| 10 | +0.08 | +0.18 | +2.37 | +2.29 |

**Q4 failed.** At d = 5 the eight other conditions add **−0.04** — nothing — against +1.13 at d = 0. They *do*
bind there (family C's on-share is 39.3% against A's 60.3%, so they are excluding a fifth of the sample) but
excluding those bars buys no premium. The conditions were not merely redundant at d = 0; **they are not useful at
any d where they are not redundant.** The single exception is d = 10, where they rescue a collapsed gate by
clamping the on-share back to 39.8% — that is the conditions acting as a *substitute* for the high, not as a
complement to it.

**Q7 failed, and the reason is the point.** C4's contribution across the sweep runs
**+1.10, +1.40, +0.83, +0.74, −0.55, +0.10.** It does not grow, it does not decay, it wanders and turns negative.
D367 showed C4 has negative standalone timing content and adds +1.23 on ten bars; this sweep shows that
contribution is **not a stable property of the condition at all.** The prediction was written to catch exactly
this and technically failed only because the d = 0.5 value (+1.40) exceeded d = 0's +1.23 — the formulation was
too tight, the conclusion it was aiming at is supported.

**Q6 failed: capacity cannot be bought.** No relaxation with an on-share of 20% or more clears its own rotation —
not at 26%, 38%, 60% or 76%. The effect is only demonstrable while the gate is nearly shut.

## 3. Q5 — the one confirmation, and the multiplicity control

| | p50 | p95 | max | best gate | draws beating it |
|---|---|---|---|---|---|
| shared-offset max over all 18 | +1.14 | **+3.62** | +5.86 | C@0, premium **+4.24** | 4 of 200 |

The best gate in the sweep clears the best-of-18 control. The full gate at d = 0 survives being searched over
eighteen candidates, as it survived D367's forty-six.

## 4. The finding that undercuts the rest: the null cannot resolve these margins

The same gate, the same 200-draw rotation design, two independent runs:

| | net | rot p50 | rot p95 | verdict |
|---|---|---|---|---|
| D367's C9 (frozen exit) | +6.93 | +4.02 | **+6.43** | clears by 0.50 |
| D368's A@0 (single exit) | +6.95 | +3.84 | **+6.83** | clears by 0.12 |

The construction differs only in the dead exit rank — net moves by 0.02 — but **the null's p95 moves by 0.40 and
its median by 0.18, purely from redrawing 200 rotations.** D367's D366 comparison showed the same thing: S6's
GATE-ROT p95 was +7.02 there against +6.42 in D367, and the draws beating it went 2 → 0.

**Every "clears / does not clear" verdict in D366, D367 and D368 was decided on margins of 0.05 to 0.5 bp/bar
against a statistic whose own run-to-run spread is about 0.4.** That includes:

- C9 alone clearing its rotation (0.12 here, 0.50 in D367);
- C9 alone *failing* the best-of-46 control in D367 by 0.05;
- the reduced universe *failing* GATE-ROT in D367 by 0.56.

None of those verdicts is safe at 200 draws. **This is not a reason to disbelieve the results; it is a reason to
stop deciding at 200 draws.** The fix is cheap and is stated here rather than performed, because performing it
would be choosing a number after seeing the outcome: **the decisive comparisons should be rerun at 2,000+ draws**,
and the record should quote the p95's own standard error beside it.

## 5. Predictions

| | | verdict |
|---|---|---|
| **Q1** | *(load-bearing)* ≥4 of 6 d clear their own p95 | **FALSIFIED** — 1 of 6 |
| **Q2** | premium non-increasing, ≤1 inversion | **FALSIFIED** — 2 inversions |
| **Q3** | *(against)* premium(0.5) < half of premium(0) | **FALSIFIED** — +2.58 vs +1.56; not a knife-edge |
| **Q4** | family C beats A by >1.23 at d = 5 | **FALSIFIED** — −0.04 |
| **Q5** | best of 18 above the shared-offset p95 | **CONFIRMED** — +4.24 vs +3.62 |
| **Q6** | *(capacity)* some d ≥20% open clears | **FALSIFIED** — none of 26/38/60/76% |
| **Q7** | C4's contribution does not grow with d | **FALSIFIED** on formulation; the wandering it targeted is confirmed |
| *check* | C9(0) reproduces D367's stored C9 | **exact**, <1e-9 |

## 6. Assertions

All pass; `--selftest` in 8 s. `[ID]` reproduces D367's **stored** C9 to <1e-9. `[MONO]` proves C9(d) is a strict
superset of C9(d′) across all six values. `[SHARE]` `[SHARED]` `[S]` hold; `[6]` shows five raising on broken input.

**Two things the assertions measured that the pre-registration only argued:**

- **`[EXIT]` — the confound was real.** Bars on which the open-state exit rank actually binds go
  **177 → 769 → 1,709 → 4,386 → 10,779 → 17,439** across the sweep, and the two exit conventions diverge from
  +0.02 bp/bar at d = 0 to **+0.50** at d = 10. Collapsing to a single exit rank was necessary for this to be a
  one-parameter sweep, not a convenience.
- **`[IMPLY]` — where each entailment breaks.** At d = 0 six of seven other conditions give a **byte-identical**
  book. Each first bites at a different point: C3 and C7 at 0.5%, C6 at 2%, C1, C2 and C8 at 5%. **C5 was never
  fully entailed even at d = 0** (2 bars), which is exactly why D367 measured it adding +0.05 where the other six
  added precisely zero.

## 7. Status

**Nothing promoted. Book: empty. The avenue is the principal's (R15).**

Against the pre-registration's stop conditions, the outcome is the one combination §5 did not enumerate: **Q3
fails *and* Q1 fails.** Not a knife-edge, not a smooth curve — a shallow, wandering surface whose only
null-clearing point is its endpoint, decided by a margin the null cannot measure.

What this does and does not say:

- **It does not weaken the trigger.** D367's rank and time rotations were 0-of-24 and 0-of-200; nothing here
  touches them. The cross-sectional momentum signal is not in question.
- **It does weaken the case for a one-condition gate on mechanism.** C9 alone was attractive because nine
  parameters became one. This sweep says the one parameter has no supporting curve — the neighbouring settings
  do not clear.
- **It closes the capacity question negatively.** The effect exists only while the gate is nearly shut.

**The honest next step is not another sweep on this fixture.** Three sweeps have now produced three wandering
surfaces, and a fourth would produce a fourth. The two things that would actually move this forward are the
null-precision fix in §4, and the out-of-sample protocol declared in D367 §5 — which remains unspent and stays
that way until the principal says otherwise.

## 8. Files

`docs/decisions/D368-the-relaxation-sweep-is-the-gate-a-knife-edge.md` (pre-registration) ·
`scripts/run_d368_relaxation_sweep.py` · `data/d368_sweep.json`, `data/d368_report.json`. Reuses
`scripts/d348_prep.py`, `scripts/run_d367_gate_deconstruction.py`, `scripts/run_d366_gated_buffer.py`,
`scripts/run_d365_momentum_buffer.py`. The holdout fixture is not read.
