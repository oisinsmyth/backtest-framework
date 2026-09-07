# D369 — the null precision rerun: 10,000 draws on the settings we would actually trade

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). The shared kernel `7ba776a` is
infrastructure with its own bit-identity proof, committed before this record.
**OHLCV only. No holdout read. Holdout reads spent: 0. Programme total: 0.**
**Date:** 2026-09-07 · **Area:** Strategy research · **personal track**

---

## 0. Why, and the commitment that has to be made before any number is seen

D368 measured the same gate under two independent 200-draw rotations that differed only in a parameter D367 had
already proved dead. **Net moved 0.02 bp/bar; the null's p95 moved 0.40 and its median 0.18.** D366→D367 showed
the same gate's p95 move from +7.02 to +6.42 with the draws beating it going 2 → 0.

The verdicts D366, D367 and D368 turned on were decided by margins of **0.05 to 0.56 bp/bar** — every one of them
inside that spread:

| verdict | margin | at risk |
|---|---|---|
| C9 alone clears its own rotation | 0.12 (D368) / 0.50 (D367) | could go either way |
| C9 alone **fails** the best-of-46 multiplicity control | 0.05 | could go either way |
| the reduced universe **fails** GATE-ROT | 0.56 | could go either way |
| S6 clears its own rotation | 1.07 (D366) / 1.67 (D367) | probably safe |

**THE COMMITMENT.** The verdicts produced here at 10,000 draws **supersede** the 200-draw verdicts in D366, D367
and D368, **whichever way they fall**, and this record will say so explicitly for each. Choosing a draw count
after seeing which way an answer went is choosing the answer; the count is fixed here, before running, at
**10,000 for every rotation arm** and is not revisited.

**This is a precision study, not a new hypothesis.** It restates hypotheses already pre-registered elsewhere and
measures them properly. No construction is modified, tuned, or searched.

## 1. The settings measured — the two live candidates, not the sweeps

The principal's instruction is to test *the settings we plan on using*. Two candidate gates remain live after
D367 and D368, and both are run:

| | gate | why it is live |
|---|---|---|
| **S6** | all nine conditions (≡ C9 + C4; the other seven are entailed or inert) | D366's construction; clears every control so far |
| **C9** | the index at a 252-bar high, alone | one parameter instead of nine; D367 showed six conditions are logically entailed by it |

Everything else is frozen and identical for both: `mom_252_21`, enter above rank 95 with the gate open, hold
above rank 90, **252-bar cap — a declared holding-period constraint, not a tuned parameter**, equal-weight long,
dollar-volume-weighted short of the eligible universe, next open on both legs, hedge borrow and rebalancing
charged, PUB primary.

**The exit rank is the single value 90** (D367: the 80/90 split is worth 0.02 bp/bar at these on-shares and is
not a degree of freedom). The frozen 80/90 figure is reported beside.

**The relaxation sweep is not rerun.** D368's `d > 0` settings are not settings anyone plans to use, and
sweeping further on this fixture is explicitly not the point of this record.

## 2. Arms

| arm | draws | question |
|---|---|---|
| **GATE-ROT / S6** | 10,000 | is the nine-condition gate's timing real? |
| **GATE-ROT / C9** | 10,000 | is the one-condition gate's timing real? |
| **A′ / S6** | 10,000 | is the trigger real behind that gate? |
| **A′ / C9** | 10,000 | is the trigger real behind that gate? |
| **GATE-ROT / reduced universe** | 10,000 | D367's Q7, which failed by 0.56 |
| **MULTI** — shared-offset max over the 9 singles + S6 | 10,000 | does either candidate survive being chosen from ten? |
| **C** — random direction | 100,000 | cheap; the sign control |
| **ROT** — rank rotation | **24, exhaustive** | *not* a sample: 24 shifts is the whole population at D348's gate width, so it has no sampling error and is reported as exact |

**Every reported p95 carries its own bootstrap standard error** (1,000 resamples of the draw set), and a verdict
whose margin is smaller than **two** of those standard errors is reported as **UNRESOLVED**, not as a pass or a
fail. That category is created here, before any number is seen, precisely so that a narrow result cannot be
written up as a clean one.

## 3. Predictions

Q1 and Q2 are load-bearing. Q5 is against.

| | prediction |
|---|---|
| **Q1** | *(load-bearing)* **S6 clears its own GATE-ROT p95 at 10,000 draws**, and the margin exceeds two bootstrap SEs of that p95. |
| **Q2** | *(load-bearing)* **C9 alone clears its own GATE-ROT p95** and the margin exceeds two SEs. D367 said yes by 0.50, D368 by 0.12; at 10,000 draws this resolves. |
| **Q3** | both S6 and C9 clear their A′ p95 by more than 2 SEs. The trigger has never been in doubt — margins of several bp — and this should be the easy one. |
| **Q4** | **S6 clears the MULTI p95**; D367's best-of-46 gave +4.15 against +2.96. |
| **Q5** | *(against)* **C9 alone fails the MULTI p95**, as it did in D367 by 0.05. If C9 cannot survive being chosen from ten candidates, the one-condition simplification is not available on evidence. |
| **Q6** | the **reduced universe fails** its GATE-ROT p95 — D367's Q7 verdict survives at precision. |
| **Q7** | at least one of the four verdicts D368 flagged as inside the null's spread comes back **UNRESOLVED** or **reversed** at 10,000 draws. |
| **Q8** | the p95 bootstrap SE at 10,000 draws is **below 0.10 bp/bar** — i.e. this draw count is actually enough to settle margins of the size in dispute. If this fails, no verdict here is safe either and the record says so. |
| *check* | the fast kernel reproduces D366's stored figures **bit-identically**; every arm's observed value equals the stored one exactly |

## 4. Stop conditions

Status only. **The avenue is the principal's (R15).**

- **Q1 and Q2 hold** → both gates are real; the choice between them is parsimony versus the multiplicity result,
  and Q4/Q5 decide that.
- **Q2 fails or is UNRESOLVED** → the one-condition gate is not available on evidence and S6 stands as the
  construction, nine conditions and all, with six of them known to be inert.
- **Q1 fails** → the gate does not survive precision, and D366's headline was a 200-draw artefact. That is a
  major negative result and gets written up as one.
- **Q8 fails** → the draw count is still too low; the record reports every margin as unresolved and states what
  count would be needed, without running it.
- Nothing is promoted. Book: empty.

## 5. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | via the shared prep |
| **[FAST]** | the kernel is **bit-identical** to D366's functions on every gate used here, rotations included — zero delta, not a tolerance (proved in `7ba776a`, re-asserted per run) |
| **[ID]** | each arm's observed value equals the corresponding **stored** D366/D367 figure exactly |
| **[SHARE]** | every rotation preserves on-share exactly and the circular run-length multiset |
| **[SHARED]** | MULTI applies one shift to all ten gates per draw, verified by recomputation |
| **[PART]** | the 8 worker processes stride the draw index; their union is asserted to be the whole draw set with no duplicates, and a single-process run of the first 200 draws reproduces the parallel result exactly |
| **[SE]** | the bootstrap SE is computed from 1,000 resamples of the draw set and reported for every p95 |
| **[MEM]** | peak working set is reported per worker; the run is sized to leave **at least 6 GB free** |
| **[6]** | [FAST], [SHARE], [SHARED] and [PART] each raise on a deliberately broken input |

## 6. Files

`docs/decisions/D369-the-null-precision-rerun.md` (this record) · `scripts/d369_fast_kernel.py` (committed,
`7ba776a`) · `scripts/run_d369_null_precision.py` (stages `--selftest`, `--arm NAME --draws N --part i --nparts
N`, `--report`) · `data/d369_*.json` (to follow). Reuses `scripts/d348_prep.py`,
`scripts/run_d366_gated_buffer.py`, `scripts/run_d367_gate_deconstruction.py`,
`scripts/run_d365_momentum_buffer.py`. The holdout fixture is not read.
