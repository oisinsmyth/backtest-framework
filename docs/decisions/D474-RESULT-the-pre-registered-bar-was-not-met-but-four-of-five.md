# D474 — RESULT: the pre-registered bar was not met, but four of five predictions broke *toward* the hypothesis, and the test was underpowered exactly where it mattered

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D474-RESULT-the-pre-registered-bar-was-not-met-but-four-of-five-predictions-broke-toward-the-hypothesis-and-the-test-was-underpowered-where-it-mattered.md`. The H1 above is the full title.*

**2026-09-12.** Runner [`scripts/d474_continuation_conditioned_on_vol.py`](../../scripts/d474_continuation_conditioned_on_vol.py) ·
artifact [`data/d474_continuation_conditioned_on_vol.json`](../../data/d474_continuation_conditioned_on_vol.json) ·
pre-registration [D474 PRE-REG](D474-PRE-REG-does-continuation-conditioned-on-volatility-state.md),
committed before the runner existed.

Hypothesis: **volatility for timing, continuation for direction.** ES RTH, 2016-01-04 →
2023-12-29, non-overlapping in-session single-contract windows. 2024+ not read.

---

## 1. The verdict, against the bar as written

| | |
|---|---|
| family maximum \|t\| over 40 cells | **3.16** |
| null family-max \|t\| | p50 **2.40**, p95 **3.22** (bootstrap SE of p95 0.035) |
| margin | **−0.05 = −1.6 SE** |
| **verdict** | **UNRESOLVED** — inside 2 SE of the null p95, which D373's rule and §4 of the pre-reg both require be recorded as unresolved rather than as a pass |
| cells clearing the **TRADEABLE** bar | **0 of 40** |

**Nothing here licenses a component study, and nothing is entered in `COMPONENTS_PROP.md` or
either book.** The hypothesis is *not* confirmed.

## 2. But four of five pre-registered predictions broke, and every one broke toward the hypothesis

| | prediction | outcome | |
|---|---|---|---|
| **X-a** | pooled edge within 2 SE of zero | **BROKEN** | +0.216 tk, t = **+2.04** |
| **X-b** | no cell tradeable | HELD | 0 cells |
| **X-c** | h = 15 sign NEGATIVE (reversal) | **BROKEN** | +0.051 tk — not reversal, just zero |
| **X-d** | V1 top quintile more negative than bottom | **BROKEN** | top **+2.423** vs bottom +0.441 tk |
| **X-e** | implied skill below 3% everywhere | **BROKEN** | max \|a\| = **6.55%** |

I predicted reversal strengthening with volatility. **The data says mild continuation
strengthening with volatility** — the opposite, in both dimensions the hypothesis names.

## 3. The pattern, and why the scale-free version is the one that matters

**V1 (bucket on the signal's own magnitude), top volatility quintile:**

| horizon | n | gross ticks | **hit rate** | implied skill | net ticks |
|---|---:|---:|---:|---:|---:|
| 15 min | 10,031 | +0.606 | 49.93% | −0.07% | −2.803 |
| 30 min | 4,683 | +0.725 | 51.23% | +1.23% | −2.684 |
| 60 min | 2,006 | +2.190 | 52.34% | +2.34% | −1.219 |
| 120 min | 798 | +3.224 | 54.76% | +4.76% | −0.185 |
| **195 min** | **398** | **+5.369** | **55.53%** | **+5.53%** | **+1.960** |

**The tick column rises partly because moves are bigger at longer horizons** — E|M| goes from
13.7 to 53.1 ticks over this range (D473 §2) — so on its own it proves little. **The hit rate
is scale-free and rises monotonically too**: 49.93 → 55.53% across five horizons. That is the
harder thing to dismiss, and it is the same direction in the volatility dimension (V1 q5 beats
q1 at every horizon past 30 min).

**And the 195-minute top-volatility cell lands exactly on D473's specification** — 55.53%
accuracy, implied skill +5.53%, against D473 §3's "C-a wants ≈5 pp of skill held ≈5 hours."
**On n = 398 with t = 0.90.** That is not evidence; it is a coincidence of the right shape, and
I record it as such.

## 4. The test was underpowered precisely where the effect appears, and that is my design error

Non-overlapping in-session windows give **one pair per session at 195 minutes** — 1,974
observations total, 398 in the top quintile. D473 says the cost-optimal zone is **60–325
minutes**. **I built a test with almost no data in the region the arithmetic had already
identified as the only one worth looking at.**

Worse, **the pre-registered statistic was the wrong instrument for the hypothesis.** A
family-maximum |t| over 40 cells is built to find *one exceptional cell*. This hypothesis
predicts a **monotone gradient** in two dimensions, and a trend statistic pools evidence that a
family-max throws away. I pre-registered the less powerful test. That is recorded, and it does
**not** license switching statistics now and claiming a pass — the §5 bar stands as written.

## 5. What a properly powered follow-up needs (and it needs its own pre-registration)

1. **A statistic that matches the hypothesis:** a monotone-trend test across horizon and
   volatility bucket, with the family-wise null built on the same trend statistic.
2. **Data in the 60–325 minute band.** Cross-session windows would supply it, which needs a
   fixture carrying the overnight move — `data/fixtures/fut_sessions_hourly.csv.gz` exists and
   has not been read here. Overlapping windows with a block bootstrap are the alternative.
3. **More than one instrument.** 41 roots are on disk; this tested ES alone, and a gradient that
   appears on NQ, YM and RTY as well is a different class of evidence.
4. **The volume-clock exit is NOT applied here** (D472's +1.18 pp), so every net figure above
   understates by roughly that much.

## 6. A bug fixed mid-run, and what it did to the answer

The first run produced **zero windows at h = 120 and h = 195**: `build` gated *both* variants on
`t−3…t+1` all being valid, but V1 needs only `t, t+1`, and a 390-minute session holds just 3 and
2 windows at those horizons. It also discarded V1 rows at every shorter horizon for a lookback
V1 does not use. Eligibility is now per variant.

**Disclosing what that changed, because it moved the verdict's sign:** the observed family max
stayed **3.16**, but restoring the 10 legitimate extra cells raised the null's family-max p95
from **3.10 to 3.22** — so the margin went from **+1.9 SE to −1.6 SE**. Both readings are
UNRESOLVED under the pre-registered rule, but the direction flipped. **That is family-wise
control working exactly as intended: more cells searched, higher bar to clear.**

## 7. Reading this honestly

The hypothesis is **not refuted and not established**. What can be said:

- **At the bar I committed to in advance, it failed** — unresolved family statistic, zero
  tradeable cells. That is the finding of record.
- **Every prediction I made about its direction was wrong**, which is a point *for* the
  hypothesis and against my prior. D473 §4's dismissal of momentum rested on a pooled variance
  ratio, and the pre-reg was right to say that a pooled 1.00 cannot rule out a conditional
  effect.
- **The one region where the arithmetic says an edge could pay is the one region I barely
  sampled.** That is a fixable flaw, not a verdict.

**What is NOT open on this evidence:** the short end. At 15 minutes the edge is +0.051 ticks
against a 3.409-tick cost, and the hit rate in the top volatility bucket is 49.93%. Whatever is
happening, it is not happening in fifteen minutes.

## 8. Checks

`--self-test` carries 18 checks. The statistic is proven to recover a **planted +2-tick edge**
(reads +1.990, t = 28.3), to read **zero** on unrelated series, and to read **negative** on a
planted reversal, with continuation and reversal exact mirror images. **The decisive capability
check reproduces the D435 failure mode on purpose:** a conditional edge planted in one bucket
only reads **−0.010 pooled** while the bucketed statistic finds **+6.191, t = 39.6** — so if a
conditional effect existed at a detectable size, this runner would see it.

The null is verified to destroy the planted edge, to leave the forward returns untouched
element-wise, to change only signs and never magnitudes, and to preserve bucket membership.
**Two of those null checks were tautologies on the first pass** (`planted.std()` compared with
itself, and `buck != buck`); they now compare the null's arrays against the originals, and a
deliberate break confirms the guard is not vacuous.

Runtime gates: the fixture's ES gate results are read and required to pass, `usable_start` must
precede the window, and a hard stop raises if any row past 2023 is reached.
