# D528 — the mean-reversion **ORACLE**: does a rare excursion return to its level more reliably than the same moves in random order?

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file.
**Quoted mid, 1-minute, 26 roots, 2025-09-11 → 2026-04-10. The last five months of the mid window
(2026-04-11 → 2026-09-09) are RESERVED AND NOT READ, for the eventual causal step.**

**This record builds a LABEL, not a trade.** No P&L, no cost model, no position, no hurdle P, no
component line. Nothing can be admitted from it (R15).

---

## 0. What an oracle is here, and why one is being built

The oracle is **the most accurate detector of a mean-reversion regime obtainable with foresight.**
Its only purpose is to **define the target** a causal statistic will later be asked to hit. It may
use the future freely; what it may not do is define a quantity whose answer is fixed by
construction.

**Three predecessors failed and each failure shaped this design.** D523's path-efficiency label was
**voided** — it demanded near-monotonicity and was biased down by bid-ask bounce. D525 was
**retired before running** — its primary was a thin root and its missing-data rule biased the test
toward its own hypothesis. D526 §8 found the scaling exponent **has no target** — it is a stable
structural constant, not a state, so nothing could predict it. This record is a different object:
the label is a **conditional return probability**, which is the quantity a construction would
actually face.

## 1. The model being detected — the principal's, stated as the object

The market settles on a price. Around that level price behaves as an **oscillator with random
variance**: it swings, but each swing's amplitude is drawn rather than periodic. News causes
**acute repricing** — the level jumps — and the market then settles on a **new** level and
oscillation resumes. Because shocks are rare, **most of the clock is spent oscillating.**

**Where the tradeable moment lives.** Most oscillations are moderate and sit well inside the
envelope. **Occasionally one reaches an extreme.** That is the entry: back toward the level. The
claim is **not** that price returns immediately or reaches the far side, only that **over time it is
highly likely to move that way** — and the moment worth having is the large oscillation **after a
jump or a scare**, when amplitude is elevated enough for the move to the level to be worth more
than a round trip.

**A window is, by definition, a stretch over which a stable level and a stable range exist.** That
is a property of the object being hunted, not a claim about markets in general. §4 operationalises
it.

## 2. The measurement frame

| | |
|---|---|
| **price** | the **QUOTED MID** `(bid+ask)/2` from `bbo-1m`. **Never trade closes** |
| **base granularity** | 1 minute, ~420 bars per day session (09:00–15:59 ET) |
| **scale ladder** | `s ∈ {1, 2, 3, 5, 8, 13, 21}` **minutes per bar** |
| **window** | **N = 20** s-bars. Spans `20s` minutes |
| **tiling** | windows **TILE** (non-overlapping) within each scale, at **4 grid phases** (offsets 0, N/4, N/2, 3N/4). Each phase is internally disjoint so counts stay honest |
| **episodes** | a **run of consecutive like-labelled tiles** is the episode — found, not searched for |

**Why the mid.** Bounce is an MA(−1) in the trade price; it has contaminated this line three times
(D523 void, D526 §4, D529's segmenter), and **no null can hold it while releasing reversion**,
because at this resolution they are the same kind of object. The mid removes the contaminant
rather than correcting for it.

**Why one window per scale.** Reversion at scale `s` and trend at scale `5s` are then measured in
**different windows** and never compete. Under self-similarity, mean reversion at one scale *is*
trend at a lower one — both readings are valid and this frame holds both without arbitration.

**Windows per session by scale:** 21, 10, 7, 4, 2, 1, 1. **The ladder has a precise middle and a
1-window top**, and §9 says how the top is handled.

## 3. The level, the envelope, and the excursion

**LEVEL: a linear detrend within the window.** There is no separate mean-timescale parameter — the
window sets it. A *drifting* level is therefore allowed, which is what "taking account of minor
drift" requires. **An SMA is rejected**: it lags by `(M−1)/2` bars, so price sits persistently above
its mean in an uptrend and a detector reads lag as extension — manufacturing reversion signals
exactly in trends.

**ENVELOPE: `±k·σ` of the detrended residual, NOT a quantile.** A quantile cannot express a *rare*
level — q02 of 20 points lies below the observed minimum. **`k ∈ {1.5, 2.0, 2.5, 3.0}` is the
declared split test** (§11): if the primary peaks at 2.0 the envelope *is* the entry; if it keeps
rising to 3.0 the entry is deeper than the envelope and they are distinct objects.

**EXCURSION: `x` in residual-σ units, `x ∈ {1.0, 1.5, 2.0, 2.5, 3.0}`** — scale-free and comparable
across windows, roots and scales.

**RETURN: price reaches the detrended level**, within one tick. The level is evaluated **at the time
of the return**, not at entry, because a drifting level moves while the position would be open.

**THE HORIZON IS NOT A CUT-OFF.** The runner reports the **survival curve** — P(returned by τ) for
`τ ∈ {0.25N, 0.5N, N, 2N}` s-bars from the excursion — so no arbitrary horizon is needed and any
later trading rule picks its own off the curve.

**AND THE RETURN IS MEASURED PAST THE WINDOW'S END.** An excursion at bar 18 of 20 is not a failure
because the window stopped. **This is legitimate precisely because it is an oracle**, and it removes
an edge artefact that would otherwise bias every short-horizon number downward.

**NO STOP IS DEFINED.** Each excursion gets a **three-way outcome** at each τ: *returned to level* /
*extended by ≥ 0.5x further out* / *neither yet*. A stop is a trading choice and does not belong in
the label.

## 4. Window admission — two filters, both declared

**A1 — STABILITY, which operationalises "a stable level and range exist".** Estimate the level
(detrend slope and intercept) and the envelope (residual σ) on the **first half** of the window and
again on the **second half**. The window is *stable* when both agree within tolerance:

    |slope_1 - slope_2| * (N/2) <= 0.5 * sigma_pooled     and     0.5 <= sigma_1/sigma_2 <= 2.0

Reported as a **continuous score** and applied as a filter at that declared threshold. A window
failing it is not one of the windows the model describes.

**A2 — LATTICE, per WINDOW and never per root.** Drop a window whose **median |return| is under 4
ticks**, because on a coarse lattice "oscillation around a mean" is mostly rounding. **Per window
is essential**: a root-level version of this filter would have discarded **49.9% of ES's windows**
that are perfectly usable, and it would have judged each root by a median that throws its time
series away. Roots then fall out on their own arithmetic rather than by fiat — measured at s=5,
ZN retains 0.9%, ZT 0.8%, ES 49.9%, RB ~100%.

**The retained fraction is reported per root per scale**, because filtering on a window's own
volatility means each root is sampled on a different part of its own distribution and cross-root
comparisons must be read with that in hand.

## 5. The primary statistic — ONE (R14)

> **`P(return to level within N s-bars | excursion ≥ 2.0σ)` minus the same quantity under the
> window's own sign shuffle** — at **s = 5 minutes**, envelope **±2.0σ**, pooled over all admitted
> windows across the 26 roots, phase 0.

**Why s = 5:** mid-ladder, 4.2 windows a session, and the scale the admitted arm already operates
on. **Why x = 2.0σ:** the middle of the declared excursion ladder. **Why τ = N:** a declared fixed
horizon rather than the estimated period `T`, which would make the primary depend on another
estimate.

**SE by a session-level block bootstrap** — resample root-sessions, 2,000 draws. Never the naive
count: excursions inside one session are not independent, and root-level correlation was measured
at ρ = 0.51 on the index roots in D525 §6.

## 6. Everything else the oracle reports, per admitted window

1. **Is the window mean-reverting** — **level crossings vs its sign-shuffle null**. Crossings are
   sign-sensitive; **variance is not, and cannot express reversion at all** — a Λ path reads as
   trending at every scale under a variance ratio, which D528's predecessor measured directly.
   Efficiency deviation reported as a companion.
2. **Three traverses and their dependence** — edge→level, level→edge, edge→edge. They are **not**
   symmetric: from the level either edge counts and one is reached eventually; from an edge there is
   one way to succeed and one way to break out. The departure from
   `edge→edge ≈ (edge→level)·(level→edge)` is the target-placement information.
3. **Range width `W`** in ticks **and in dollars**, so the cost filter is expressible later.
4. **Oscillation period `T`** — from level crossings of the detrended residual.
5. **Drift as a reported dimension**, `drift × T / W`, **flagged at ≥ 0.5** but never used to
   exclude. Exclusion would discard information; a flag keeps it.
6. **Realised volatility, reported not fixed.** A volatility clock was considered and rejected: with
   the ladder in time units, a fixed movement budget makes bars-per-window vary **5.5–8.8×** with
   4–5 bars at the 5th percentile — fewest observations exactly in the violent windows where the
   behaviour is. Measuring volatility and stratifying later keeps the variation that fixing it
   throws away, and this model is *about* volatility changing.
7. **Range predictability** — `W` in window `t+1` against `W` in window `t`, within root. Not a
   causal claim; the oracle simply records whether the quantity a later filter would need is
   autocorrelated at all.

## 7. The null

**A SIGN SHUFFLE OF THE WINDOW'S OWN RETURNS.** Magnitudes stay exactly in place; only the signs
are randomised. It therefore holds the return distribution, the **fat tails** and the **volatility
clustering** identically and randomises only the **arrangement** — which is precisely the claim
under test, since "does price oscillate around a level" is a statement about arrangement.

**Validated unbiased over 300 paths a cell** in the design work: a Gaussian walk reads DEV +0.0010,
a t(3) fat-tailed walk −0.0204, a vol-clustered walk +0.0051. **200 shuffle draws per window**,
with the draw count's contribution to the SE reported.

**One property worth stating:** the shuffle preserves `Σ|r|` over every prefix, so the lattice
filter (A2) and the window grid are **identical** under the null. Observation and null share their
admission exactly.

## 8. Benchmarks are SIMULATED, never closed-form

Every reference value — the random-walk crossing count, the survival curve of a driftless walk at
each `(k, x, τ)` — is obtained by simulation at the same N and the same scale, at a frozen seed,
and asserted reproducible. **The closed form is wrong here by more than the effect**: D471's `C` is
1 only for Gaussian steps and measured 1.17–1.21; D525 measured a finite-window bias of +0.0477
against a whole effect of 0.05; D529's Λ-detection failed on exactly this.

## 9. Sampling, pooling, and the reserved slice

- **26 roots**, whichever have a mid and pass A1/A2 in a given window.
- **In sample: 2025-09-11 → 2026-04-10** (~145 sessions).
- **RESERVED AND NOT READ: 2026-04-11 → 2026-09-09** (~105 sessions). **This is for the causal
  step, not for this record.** An oracle is a measurement instrument and cannot be "confirmed"; the
  thing that will need unseen data is the detector built against it. D526 spent the whole mid window
  on a different statistic, so this split is the last clean test bed this line has.
- **Top of the ladder (s = 13, 21) has one window per session**, so those scales are pooled across
  sessions and reported with that stated. The precise middle and the noisy top are labelled as such.

## 10. Predictions, in the runner's own quantities

| | prediction | why |
|---|---|---|
| **P1** | **the primary excess is in `[−0.02, +0.04]`** — small, and possibly negative | D526 found the index roots *persistent* on the same mid (Hu 0.53), which argues against reversion at 5 minutes on exactly the roots that dominate the sample |
| **P2** | **the per-root primary excess correlates POSITIVELY with D526's anti-persistence ordering**, Spearman > +0.4 — positive on GC/ZB/TN/6E, negative on ES/NQ/RTY/YM/HO | two instruments on the same data should agree about which roots revert; if they disagree, one of them is measuring something else |
| **P3** | **the excess RISES monotonically with `x`** across 1.0→3.0σ | the model says *rare* excursions revert; if instead it falls with x, the signal is a routine-oscillation artefact rather than the described mechanism |
| **P4** | **A1 admits 20–50% of windows** | a stable level and range is a real restriction, not the common case |
| **P5** | **range predictability (item 7) exceeds +0.3 within root at s=5** | volatility clustering is the most robust fact in this repo, and `W` is a volatility proxy |
| **P6** | **the principal's 80%** — the share of *admitted* windows labelled reverting — **lands above 70%, but its EXCESS over the sign-shuffle null is under 15 points** | a pure random walk already reads mean-reverting 50–68% depending on the definition, so most of any 80% is the baseline |

**P1 and P2 predict against the principal's expectation on the index roots and with it on the
metals and rates.** P3 is the one that separates his mechanism from an artefact.

## 11. The declared split test

The **envelope σ ladder `k ∈ {1.5, 2.0, 2.5, 3.0}`** answers "is the envelope the entry, or is the
entry deeper?" in one pass. Declared here so it is not a search: **if the primary peaks at k = 2.0
the two are the same object; if it rises monotonically to 3.0 they are distinct** and the envelope
is the wider boundary.

## 12. Decision rule, pre-registered

- **A TARGET EXISTS** — the primary excess is positive by more than 2 session-bootstrap SE **and**
  P3's monotonicity in `x` holds. The oracle has then found a real state and a causal detector is
  worth designing against it, on the reserved slice.
- **A TARGET EXISTS BUT IS UNTRADEABLE** — the above holds, but at no scale does `W` in ticks cover
  a round trip on any root with an admitted-window share above 5%. Recorded as such; the label is
  kept as an instrument and no construction follows.
- **NO TARGET** — the primary does not clear, or clears while P3 *falls* with `x`. The mechanism as
  described is then not detectable even with foresight, which closes it on its premise rather than
  on a construction.
- **UNRESOLVED** wherever a margin sits within 2 SE. Never rounded into a pass.

## 13. Checks the runner must carry, each able to fire

1. **Known-answer paths.** A sine wave with random amplitude scores a high crossing excess and a
   high return probability; a straight line scores ~0 crossings; a Gaussian walk scores DEV ≈ 0 at
   every `(k, x, τ)`. **[X]** each must fail on the wrong path.
2. **The envelope is σ-based and can sit outside the sample** — assert that at N=20 a ±3σ band
   sometimes lies beyond the observed min/max, which a quantile band never can.
3. **[X] a quantile envelope makes the label degenerate** — assert that with the band at the
   realised extremes the traverse is identically 1, proving why quantiles were rejected.
4. **The return is measured past the window end** — assert an excursion at bar N−2 can still return,
   and **[X]** that truncating at the window boundary lowers the short-τ probability.
5. **The three-way outcome is exhaustive and exclusive** at every τ.
6. **A1 fires** — assert a synthetic window with a vol regime change in the middle is rejected, and
   one with a constant level and range is admitted.
7. **A2 is per window, not per root** — assert ES retains roughly half its windows and that a
   root-level threshold would have retained none.
8. **The sign shuffle preserves prefix `Σ|r|`** exactly, hence the grid and the lattice filter are
   identical under the null.
9. **The null is unbiased** — reproduce the design figures for Gaussian, t(3) and vol-clustered
   walks within their SEs.
10. **Benchmarks reproduce at the frozen seed** and the runner **raises** if they do not.
11. **The runner computes the pre-registered primary** — s=5, k=2.0, x=2.0σ, τ=N, phase 0, pooled —
    asserted explicitly, because D506 compared a different quantity than its spec declared and D523
    never computed a secondary it had declared.
12. **The reserved slice is never loaded** — assert `max(day) <= 2026-04-10` and raise.
13. **Duty cycle** — every reported cell carries its window count, its session count and its
    admitted fraction.

## 14. Speed

The ladder is 7 scales × 4 phases × 200 shuffles over ~145 sessions × 26 roots. **A naive
implementation is far past the ten-minute rule**, so an optimisation pass is required before launch
and its projected wall time must be stated in the result (CLAUDE.md). The band state machine and
the survival curve are the hot paths; both are integer/boolean work over short arrays and should
vectorise over the shuffle axis.

## 15. What this record does not do

No P&L, no cost, no position, no hurdle P, no component line, no construction. Nothing enters
`FINDINGS.md`, `RULES.md`, `COMPONENTS_PROP.md` or either book on this record's authority (R8, R15).
**The reserved slice stays unread whatever the outcome** — it belongs to the causal step.

---

# 16. AMENDMENT, 2026-09-14 — **§3's level saturates the statistic and is replaced. The primary becomes a HELD level.**

**The first run exposed a defect in §3, not in the data.** With the level defined as a
least-squares line over the **whole** window, the residual sums to zero **by construction** and
must therefore cross the level. `P(return)` came out at **0.9077 on a Gaussian random walk** —
**9.2% of headroom for any effect to live in**, and the measured excess of +0.034 was most of what
was available to find.

## 16.1 The centred SMA was tried and makes it WORSE

The principal proposed a centred SMA as the level. Measured on 8,000 random-walk windows:

| level | P(return) on a random walk | headroom |
|---|---:|---:|
| §3's linear, whole window | 0.9077 | 9.2% |
| **centred SMA w=3** | **0.9988** | **0.1%** |
| centred SMA w=5 | 0.9964 | 0.4% |
| centred SMA w=9 | 0.9922 | 0.8% |
| centred SMA w=15 | 0.9863 | 1.4% |
| centred SMA w=21 | 0.9798 | 2.0% |

**A centred SMA is a high-pass filter**, so `price − CSMA` *is* the high-frequency component and it
crosses zero roughly every `w/2` bars. The narrower the window the more certain the return. At
w = 3 there is **0.1%** of headroom left. Confirmed on NQ and ES at s=5 (0.9976 and 0.9952).

**The saturation was never about smoothing. It is about fitting the level to the same data the
return is measured on.**

## 16.2 The replacement: a level fitted on the FIRST HALF and HELD

| level | random walk | NQ | ES | headroom |
|---|---:|---:|---:|---:|
| **HALF-LINE** — line on bars [0, H), slope carried forward | 0.3712 | 0.3315 | 0.3410 | **63–67%** |
| **HALF-FLAT** — mean of bars [0, H), held flat | 0.4635 | 0.3563 | 0.3917 | 54–64% |
| HALF-FLAT (median) | 0.4598 | 0.3688 | 0.4108 | 53–63% |
| HALF-SMOOTH (last-5 mean, held) | 0.4712 | 0.3630 | 0.3797 | 53–64% |

**A 7× increase in headroom**, because the second half carries no constraint to return — price may
drift away and never come back.

**THE AMENDED DESIGN, on the principal's ruling:**

- **PRIMARY LEVEL: `HALF-LINE`** — least-squares line on the window's first half `[0, H)` with the
  slope **carried forward** over `[H, N]`. Chosen because it **adjusts for drift**, which §1's model
  requires, and it has the most headroom and the most excursions.
- **`HALF-FLAT` is reported beside it** — the mean of the first half held flat, which is §1's
  "settled price" stated literally. The drift question is then answered by measurement rather than
  by choosing now.
- **`σ` is the residual standard deviation over the ESTIMATION HALF only**, and **excursions are
  counted only from bar `H` onward.** The first half is the estimation window and nothing is
  measured in it.
- The original **whole-window linear level is retained as a third row**, so the amended and the
  original numbers are directly comparable.
- Everything else is unchanged: the sign-shuffle null, the x ladder, the τ survival curve, the
  three-way outcome, A1/A2, the scale ladder, the reserved slice.

## 16.3 What this costs in multiplicity, stated rather than glossed

**The in-sample window has already been read once** — with the §3 level, giving a primary of
+0.0215 at t = +1.47 (UNRESOLVED), which **stands as reported**. Re-reading it with a held level is
a **second look**, and the amended primary is therefore **exploratory relative to the original
pre-registration.**

**What limits the damage is how the new level was chosen: on a NULL, not on the outcome.** The four
candidates were ranked by `P(return)` **headroom on a Gaussian random walk** — a property of the
construction, not of the data. Real `P(return)` was inspected for NQ and ES to confirm the headroom
survived on real prices, but **the excess over the sign shuffle — the actual statistic — was not
computed for any candidate before this amendment.** So the statistic itself is unseen; the level was
selected on arithmetic.

**And one warning is on the record before the run.** Under a held level the real roots return
**less** often than a Gaussian walk (NQ 0.356, ES 0.392 against 0.464), which is the *opposite*
direction from mean reversion and consistent with D526 finding the index roots persistent. A
Gaussian walk is not the null, so this is not a result — **but the +0.034 excess measured under the
saturated level may not survive, and possibly not even in sign.** That is recorded now so it cannot
be presented as a surprise afterwards.
