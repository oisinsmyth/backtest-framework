# D368 — the relaxation sweep: is the gate a knife-edge at the high, or the end of a smooth curve?

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). **OHLCV only.**
**Date:** 2026-09-07 · **Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.** D367 §5's declared out-of-sample protocol is
not executed here.

---

## 0. Why

D367 reduced D366's nine-condition gate to one: **C9, the index at a 252-bar high.** Six of the other eight are
logically *entailed* by it and contribute identically nothing; the ninth (C4) adds +1.23 of timing premium on ten
gate-open bars while having negative standalone timing content. That left one question that no further work on
the same point can answer:

> **Is "at a 252-bar high" a knife-edge, or the end of a smooth relationship?**

The cap sweep already behaved badly this way — no plateau, ±10 bars swinging Sharpe from 0.735 to 0.922. If the
gate collapses the moment the index is allowed to sit half a percent below its high, that is the **second jagged
surface** in this construction and it is a pattern rather than an accident. If the premium decays smoothly, the
mechanism is credible and a capacity dial comes free.

**This record does not tune anything.** It sweeps one parameter and reports the curve.

## 1. The relaxation

C9 becomes **C9(d): the index closes within d% of its trailing 252-bar high**, lagged as before:

```
    C9(d)   idx[t-1]  >=  (1 - d/100) * max(idx[t-253 : t-1])
```

`d = 0, 0.5, 1, 2, 5, 10`. **`d = 0` recovers C9 exactly** and is the identity check, not a data point earned.

**Three families, because the redundancy breaks as d grows.** At `d = 0` an index at its high is *necessarily*
above its moving averages, positive over 63 and 21 bars, not in a crash and broad — which is why six conditions
were free. At `d = 5` none of that is implied any more, so the other conditions may start to earn their keep. That
is itself a measurement:

| family | gate |
|---|---|
| **A** | C9(d) alone |
| **B** | C9(d) + C4 — the pair D367 showed is equivalent to the full nine |
| **C** | C9(d) + all eight others — D366's S6 with only its binding condition relaxed |

18 gates. Everything else is D366's frozen construction: `mom_252_21`, enter above rank 95 with the gate open,
252-bar cap (a **declared holding-period constraint**, not tuned), equal-weight long, dollar-volume-weighted short
of the eligible universe, next open on both legs, hedge borrow and rebalancing charged.

## 2. One change to the frozen construction, and why it is not a free parameter

D366's exit rank depends on gate state: hold above rank 80 while the gate is open, above 90 while shut. **That
would confound this sweep** — raising `d` opens the gate on more bars, which would also loosen the exit on more
bars, so two things would move at once and the curve would not be attributable to the gate.

D367 measured that split to be **dead**: S6 with exit rank 90 everywhere gives +8.11 at Sharpe 0.887 against
+8.09 at 0.887 for the 80/90 split. So the **primary construction here uses a single exit rank of 90**, making the
gate purely an entry condition and the sweep a genuine one-parameter change. The frozen 80/90 version is reported
beside at every `d`, and the number of bars on which the open-state rank actually binds is reported, because that
number is ~0 at `d = 0` and will not be at `d = 10`.

## 3. Nulls

- **GATE-ROT, per gate** — each of the 18 gates circularly shifted within its defined range, on-share and circular
  run-length multiset preserved exactly, trigger untouched. **200 draws each.**
- **SHARED-OFFSET MAX** — one shift per draw applied to **all 18** gates, scored on the best timing premium among
  them, pricing this sweep's own search. 200 draws.

**The statistic is the timing premium** — net less the median of that gate's own rotation — because on-share is
the nuisance parameter and it is exactly what `d` moves. Raw net, gross and on-share are reported beside it and
never used to rank.

## 4. Predictions

Q1 is load-bearing. Q3 is against.

| | prediction |
|---|---|
| **Q1** | *(load-bearing)* **at least 4 of the 6 `d` values in family A clear their own GATE-ROT p95.** A knife-edge shows up as only `d = 0` clearing. |
| **Q2** | family A's timing premium is **non-increasing in `d`, allowing at most one inversion** — the curve decays rather than wandering. |
| **Q3** | *(against)* **premium(d = 0.5) < half of premium(d = 0)**, i.e. below +1.46. This is the knife-edge outcome and it is written so it can win. |
| **Q4** | **the redundancy breaks**: at `d = 5`, family C's premium exceeds family A's by **more than the +1.23** that separated them at `d = 0`. Once the high no longer implies the trend conditions, they should start contributing. |
| **Q5** | the **best of the 18** gates is above the p95 of the shared-offset max over all 18. |
| **Q6** | *(capacity)* **at least one `d` with an on-share of 20% or more clears its own GATE-ROT p95.** This is the tradeable-capacity question stated as a test. |
| **Q7** | at every `d`, family A's premium exceeds family B's **minus** 1.23 — i.e. C4's contribution does not grow with `d`; if C4 were a real condition rather than ten bars, it should help more when the gate is looser, not less. |
| *check* | `C9(0)` under the frozen 80/90 exit reproduces D367's **stored** C9 figures (net +6.93, premium +2.91, 1,008 trades) to 1e-9 |

## 5. Stop conditions

Status only. **The avenue is the principal's (R15).**

- **Q1 holds and Q3 fails** → the gate is a smooth relationship, not a point. C9 alone becomes defensible on
  mechanism as well as parsimony, and the largest `d` that still clears gives a capacity dial.
- **Q3 holds** → "at the high" is a knife-edge. With the cap sweep, that is two jagged surfaces in one
  construction, and the record says so plainly.
- **Q1 fails while Q3 fails** → neither smooth nor a clean point; the curve is noise and the gate is not
  characterised by this parameter at all.
- **Q4 holds** → the eight "redundant" conditions are not redundant in general, only at `d = 0`; the honest
  construction at any usable `d` is larger than one condition.
- **Q6 fails** → the effect exists only at on-shares under 20%, which bounds how much of the year this can trade.
- Nothing is promoted. Book: empty.

## 6. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | via the shared prep |
| **[ID]** | `C9(0)` under the frozen exit reproduces D367's **stored** `data/d367_gates.json` figures to 1e-9 |
| **[MONO]** | `C9(d)` is a strict **superset** of `C9(d′)` for every `d > d′`, and on-share is strictly increasing in `d` — asserted across all six, not assumed |
| **[IMPLY]** | at `d = 0` the six entailed conditions change the book **byte-identically**; the record reports the smallest `d` at which each stops being implied, measured rather than argued |
| **[EXIT]** | the two exit conventions are compared at every `d`, and the count of bars on which the open-state rank actually binds is reported at every `d` |
| **[SHARE]** | every rotation preserves on-share exactly and the **circular** run-length multiset (D367's ring version, not the doubled-array one that failed a correct rotation) |
| **[SHARED]** | all 18 gates in one draw use the same shift, verified by recomputation from the recorded shift |
| **[S]** | +50 bp on one held name moves the book's bar by 50 / n_held and no other bar |
| **[6]** | [MONO], [IMPLY], [SHARE], [SHARED] and [S] each raise on a deliberately broken input |

## 7. Files

`docs/decisions/D368-the-relaxation-sweep-is-the-gate-a-knife-edge.md` (this record) ·
`scripts/run_d368_relaxation_sweep.py` (stages `--selftest`, `--sweep --draws N`, `--report`) ·
`data/d368_sweep.json`, `data/d368_report.json` (to follow). Reuses `scripts/d348_prep.py`,
`scripts/run_d367_gate_deconstruction.py`, `scripts/run_d366_gated_buffer.py`,
`scripts/run_d365_momentum_buffer.py`. The holdout fixture is not read.
