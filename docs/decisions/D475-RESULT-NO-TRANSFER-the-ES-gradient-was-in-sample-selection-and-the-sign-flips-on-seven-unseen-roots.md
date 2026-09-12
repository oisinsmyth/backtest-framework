# D475 — RESULT: NO TRANSFER. The ES gradient was in-sample selection, and the sign flips on seven unseen roots

**2026-09-12.** Runner [`scripts/d475_continuation_transfer.py`](../../scripts/d475_continuation_transfer.py) ·
artifact [`data/d475_continuation_transfer.json`](../../data/d475_continuation_transfer.json) ·
pre-registration [D475 PRE-REG](D475-PRE-REG-does-the-volatility-conditioned-continuation-gradient-TRANSFER-to-seven-instruments-it-was-never-seen-on.md),
committed before the runner existed.

Hypothesis: **volatility for timing, continuation for direction** (the principal's). Tested for
transfer to **seven roots it was never looked at on**, because D474's gradient was found post
hoc on ES and ES is therefore spent for it.

---

## 1. The verdict

| | |
|---|---|
| **primary statistic `S`** (mean trend slope, 35 cells, 482,942 observations) | **−0.1334 pp per quintile** |
| N1 sign-randomised null | p50 +0.0033, **p95 +0.1140** (SE 0.0036) → margin **−68.6 SE** |
| N2 quintile-shuffled null | p50 +0.0005, **p95 +0.1110** (SE 0.0034) → margin **−72.3 SE** |
| roots individually positive | **4 of 7** (the bar was ≥ 5) |
| tradeable cells | **1 of 10**; **0 roots** positive at ≥ 2 horizons |
| **verdict** | **NO TRANSFER — decisively short of both nulls and on the wrong side of zero** |

This is not a near miss. `S` is **negative**, and sits 68 SE below where a positive gradient
would have to reach. **The hypothesis fails at transfer.**

## 2. The number that tells the story

| | mean trend slope |
|---|---:|
| **ES** — the discovery root, where the gradient was found | **+0.2230** |
| **the seven unseen roots** | **−0.1334** |

**The sign flips.** That is the signature of in-sample selection, and it is precisely what
D430's standing lesson describes: *"+80/trade in-sample became −29 on 803 unseen names; only the
base effect reproduced; in-sample nulls test selection, not transfer."*

Per-root means, which is why the 5-of-7 consistency rule earned its place in §5:

    NQ  +0.1335    ZN  -0.6022    GC  -0.3636    6E  +0.0510
    YM  +0.1197    ZB  -0.5703    CL  +0.2980

The negative is driven by the **rates complex (ZN, ZB) and gold**. A mean can be dragged either
way by three roots out of seven, which is exactly the failure mode the consistency requirement
exists to catch — and it catches it in both directions here.

## 3. What the LEVEL says, which is a different question from the gradient

Pooled same-sign rate, 1–5 hour horizons, every root:

    NQ 49.47%   YM 49.27%   ZN 49.69%   ZB 49.84%
    GC 49.40%   CL 49.71%   6E 49.57%      (ES 49.33–50.32%)

**Below 50% on all seven**, and on ES. So at 1–5 hours the instrument shows **mild reversal, not
continuation** — consistent with [D471 AMENDMENT 1](D471-RESULT-the-spread-barely-widens-where-the-moves-are-and-path-efficiency-is-exactly-the-random-walk-value-in-every-bucket.md)'s
variance ratio of 0.82–1.02, which never exceeded 1.02 on any grid or clock. Two independent
instruments, same answer.

## 4. Predictions: four of five held, the reverse of D474

| | prediction | outcome | |
|---|---|---|---|
| **Y-a** | `S > 0` and clears N1 by 2 SE | **BROKEN** | `S` is negative |
| **Y-b** | `S` fails to clear N2 by 2 SE | HELD | trivially, `S` < 0 |
| **Y-c** | equity index > non-equity | HELD | eq **+0.127** vs non-eq **−0.237** |
| **Y-d** | nothing tradeable at ≥ 2 horizons | HELD | 0 roots |
| **Y-e** | best implied skill below 5% | HELD | **2.99%** |

**Y-c held but does not support the narrow reading I offered for it.** I suggested the effect
might be equity-index-specific. The *means* split that way, but **CL (crude) is non-equity and
the second most positive root at +0.298**, while gold is negative. There is no clean asset-class
story here — there is scatter around zero with rates pulling down.

## 5. What I got wrong, and it was the prior not the test

In D474 I predicted reversal and the data showed continuation, so I flipped and predicted
continuation would transfer (Y-a). **It did not.** The honest summary across both records:

- **D474**: on ES, in-sample, a monotone positive gradient (hit rate 49.93 → 55.53%). Four of
  five predictions broke toward it. **UNRESOLVED, nothing tradeable.**
- **D475**: on seven unseen roots, the gradient is **negative** and 68 SE short. **NO TRANSFER.**

**The D474 pattern was selection.** It was monotone, it was scale-free, it landed on D473's
specification — and it still did not survive contact with instruments it had not been fitted to.
That is worth recording as the strongest single illustration in this sequence of why transfer is
the test and in-sample monotonicity is not.

## 6. One thing this does NOT license, and I want it on the record

`S = −0.1334` against a null whose p95 is +0.1140 — by symmetry its p5 is near **−0.11**, so the
observed value sits *just past* it. **There is a hint of a NEGATIVE gradient: reversal
strengthening with volatility.** That is what I originally predicted in D474 (X-c, X-d).

**I pre-registered a one-sided test for a positive gradient and I am not harvesting the other
tail from it.** Claiming the negative would be exactly the switch D474 §4 refused. If reversal
conditioned on volatility is worth testing, it needs its own pre-registration, its own two-sided
or explicitly-negative bar, and — since ES and now these seven roots have been looked at — a
genuinely fresh test set. The 2024+ slice remains sealed.

## 7. What is now closed and what is not

**Closed on measurement**, for the prop track at micro size:

- **Continuation at 1–5 hours, conditioned on prior volatility, on eight index/rates/metal/
  energy/FX roots**: the gradient does not transfer, the level is below 50% everywhere, and 0 of
  7 roots is tradeable at 2+ horizons.
- Combined with [D473](D473-RESULT-the-cost-structure-picks-the-horizon-hours-not-minutes-and-the-entry-must-come-from-outside-the-price-path.md)
  §4 (variance ratio ≤ 1.02 on nine grids across two clocks) and
  [D474](D474-RESULT-the-pre-registered-bar-was-not-met-but-four-of-five-predictions-broke-toward-the-hypothesis-and-the-test-was-underpowered-where-it-mattered.md)
  (15–195 min on ES), **price-path momentum has now failed at every horizon from 10 seconds to
  5 hours, on two clocks, on eight instruments.**

**Not closed** — and per R15 none of this is mine to close anyway:

1. **The off-diagonal lookback.** This grid locks lookback = holding period (the canonical TSMOM
   form). A gradient at, say, a 4-hour lookback with a 1-hour hold is **untested**. It was named
   as a gap in the runner's docstring before the run, not discovered after.
2. **Cross-sectional momentum** — ranking the nine roots against each other rather than each
   against its own past. A different effect entirely, and the fixture supports it.
3. **Reversal** conditioned on volatility (§6), with its own pre-registration.
4. **The other four entry families** from D473 §5: clock/session structure (which is where C1's
   +0.37 lives and remains the best thing on the track), cross-instrument lead-lag, calendar and
   event structure, order-flow imbalance.

## 8. Checks

27 self-test checks. Tolerances come from an **analytic `slope_se()` with 3 SE bands**, not from
eye — a hand-picked 0.06 pp band on the first pass sat *below* one SE (0.079) and failed a
correct null for being correctly noisy, the same error D469 made with a guessed 2% band.

Both nulls are **module functions the run itself calls**, so the self-test exercises the real
code path rather than a re-implementation. The discriminating pair is verified non-vacuously:
N1 changes the indicator element-wise and drives the hit-rate level to 0.5; N2 changes the
quintile labels, **preserves their multiset** (a permutation, not a redraw), and leaves the
indicator — and therefore the hit-rate level — exactly intact. That asymmetry is what makes N2 a
test of the *conditioner* rather than a second copy of N1.

Runtime gates: every primary root's own G1–G5 results are read and required to pass; **RTY is
excluded on its stated G2 failure** (reverting roll 2020-06-14) rather than on convenience; only
`same_front` rows are used; and a gate raises if any row past 2023 survives the filter.

**Two things fixed during construction, both disclosed:** the null loop was profiled before
launch (55 ms per draw → **1.8 min**, against my guess that it might exceed ten minutes — the
guess was wrong, which is why CLAUDE.md says profile first), and the prior-volatility
computation was rewritten to **require all three prior segments present** rather than relying on
`nanmean` returning NaN and that NaN propagating into the validity mask.

**And the verdict label itself was imprecise on the first pass** — it printed
"UNRESOLVED / NO TRANSFER" as one composite. Those are different states: a statistic just under
a null p95 is unresolved; one 68 SE below it and negative is a decisive negative. The label now
distinguishes them.

## 9. What this does not do

- **It admits and closes nothing** ([R15](../RULES.md#r15)). Nothing is entered in
  `COMPONENTS_PROP.md` or either book. **2024+ remains sealed.**
- **It scores no construction**, so there is no component line to report.
- **Nothing is elevated** into `FINDINGS.md` or `RULES.md`.
