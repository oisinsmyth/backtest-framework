# D529 — the payoff ratio is **exit geometry**; the hit rate is the edge. The reframe this session was running on was backwards.

*2026-09-14. A control on the admitted arm, prompted by a challenge found in the quarantined external
research. No new construction, nothing admitted, nothing closed (R15). In-sample only — the spent
2024+ slice was not read.*

---

## The one-line answer

**A detached signal with the arm's exact exit produces a payoff ratio of 1.04 at the median and
1.138 at p95. The arm's 1.128 is INSIDE that. Its hit rate of 50.5% is outside it entirely — zero of
400 draws reach it.** So the arm is paid for **being right**, not for being right bigger, and the
search direction this session adopted — *"hunt shape, not accuracy"* — was pointing the wrong way.

## Where the challenge came from

`docs/research/Prop-Firm-080926/15-reddit-mined.md` §C5, on an unrelated retail strategy:

> "**A trailing stop mechanically manufactures a low win rate and a high payoff ratio on ANY entry,
> including a random one.** That geometry is not evidence of a signal."
> "**Falsifier: run a random-entry control with the identical trailing-stop exit**, identical risk per
> trade, identical instrument and window."

The arm's exit is asymmetric in two ways that could do exactly this: a **5-hour minimum hold** that
forbids cutting a loser early, and a **forced flat at the h15 close** that terminates 75% of trades
on the clock rather than on the signal.

## The control

**It already half-existed.** `d504_arm_full_history.py` line 403 rotates the signal and re-runs
`simulate()` against the same price path with the same minimum hold, the same
signal-stops-favouring exit and the same forced flat — so exit geometry is reproduced in every draw.
That **is** the challenge's falsifier, and the arm cleared it at +0.698 against p95 +0.272. But that
null scores the **Sharpe**, and the challenge is about the **hit rate and the payoff ratio**. This
answers it on its own statistics.

400 rotations, in sample, 1,876 sessions, 1,908 trades:

| statistic | p05 | p50 | p95 | **observed** | draws ≥ obs | verdict |
|---|---:|---:|---:|---:|---:|---|
| hit rate | 0.457 | 0.475 | 0.493 | **0.505** | **0.0 %** | **CLEARS** |
| payoff ratio | 0.949 | 1.041 | **1.138** | **1.128** | 7.2 % | **INSIDE the null** |
| mean $/trade | −10.82 | −3.78 | +3.39 | **+8.08** | 0.5 % | **CLEARS** |

**Exit geometry alone manufactures a payoff ratio above 1** — median 1.041 — on a signal that has
been detached from the price path. The arm's 1.128 does not clear the p95 of 1.138. The hit rate
does, decisively.

## The decomposition

Expectation per unit risked is `hit × payoff − (1 − hit)`:

| | |
|---|---:|
| null median hit 0.475, null median payoff 1.041 | **−0.0307** |
| **observed hit 0.505**, null median payoff 1.041 | **+0.0313** ← accuracy alone flips the sign |
| null median hit 0.475, **observed payoff 1.128** | **+0.0105** ← asymmetry alone barely does |
| observed hit, observed payoff | **+0.0752** |

**Accuracy alone is worth three times what asymmetry alone is worth**, and accuracy alone is
sufficient to turn the null's losing expectation positive. Three percentage points of hit rate is
the whole edge.

## What this corrects

Earlier in this session I wrote, in `PICKUP.md` and in
[D526](D526-the-curve-story-fails-stage-0-the-level-is-a-regime-and-the-change-carries-nothing.md),
that *"the one thing that works is not paid for being right; it is paid for being right BIGGER"* and
that the search should **hunt shape, not accuracy**. That was inferred from the arm's 50.5 % / 1.13
without asking what a null exit produces. **It is wrong and the direction it implied is wrong.** Both
documents are corrected in place with a pointer here; this record is the correction.

The mistake has a name in this programme's own memory —
`test-the-statistic-not-just-the-story` — and this is the same shape: a mechanism was inferred from
a statistic before checking that the statistic ordered the outcome. What makes it worth a record is
that it had already begun steering the search: D526's curve story was chosen *because* it promised a
shape effect, and the Stage 0 that killed it was designed around skew and payoff ratio rather than
accuracy.

**What does NOT change:** the arm's admission stands. Its mean per trade clears at 0.5 %, its Sharpe
cleared its own rotation null by +35 SE, and D527's cost correction left it above C-a. Nothing here
touches the entry.

## What it implies for the second component

**A component must reproduce an accuracy edge, not a payoff shape.** Concretely: about three
percentage points of hit rate over what its own exit geometry produces on a detached signal, at a
horizon where cost is small against the move.

And the corollary is a test, not a theory: **any future candidate must be scored against its own
exit's null, not against zero.** A payoff ratio above 1 means nothing on its own; a hit rate above
its rotated null is the thing to look for. This is cheap — the machinery is
`scripts/d529_exit_geometry_control.py` and it runs in seconds.

**One honest limit.** The rotation preserves the signal's duty cycle and run-lengths and rolls it
whole sessions against the price path. It is therefore a *time rotation*, which is a stronger null
than a per-session random entry would be — a pure random entry would destroy the signal's persistence
and make the comparison easier. That direction of bias favours the arm's result, not the finding
against my reframe.

---

Recomputed by [`scripts/d529_exit_geometry_control.py`](../../scripts/d529_exit_geometry_control.py)
into [`data/d529_exit_geometry_control.json`](../../data/d529_exit_geometry_control.json), seconds.
The instrumented copy of `simulate()` is asserted bit-identical before its ledger is used — the first
draft diverged because it wrote `pnl + (g − c)` where the committed loop writes `pnl + g − c`, and
float addition is not associative.
