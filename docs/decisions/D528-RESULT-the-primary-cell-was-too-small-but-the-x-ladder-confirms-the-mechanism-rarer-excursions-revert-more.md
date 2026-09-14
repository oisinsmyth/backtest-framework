# D528 RESULT — the pre-registered primary is **UNRESOLVED** because I declared too small a cell, but the **x ladder confirms the mechanism**: rarer excursions revert more

**Result of D528** (spec `98bf297`, runner `69e38a7`). `scripts/d528_mean_reversion_oracle.py --run`
(`--self-test` passes, 16 checks; decode 16.1 min, run 1.5 min), artefact
[`data/d528_mean_reversion_oracle.json`](../../data/d528_mean_reversion_oracle.json), fixture
`data/fixtures/fut_day1m_mid.parquet`.
**35 roots, 1-minute QUOTED MID, 2025-09-11 → 2026-04-10, 1,930,622 rows.
2026-04-11 → 2026-09-09 RESERVED AND NOT READ.**
**No P&L, no cost, no position. Nothing admitted (R15).**

---

## 0. The two headline numbers, and they point different ways

| | value | verdict |
|---|---|---|
| **the pre-registered PRIMARY** — s=5, phase 0, x=2.0σ, τ=N | **+0.0215**, clustered SE 0.0147, **t = +1.47** on 294 excursions | **UNRESOLVED** — does not clear 2 SE |
| **the x ladder, pooled over scales and phases** | **monotone rising, +0.0217 → +0.0603, t +27.9 → +2.9** | **P3 confirmed** |

**The primary failed on power, not on sign.** One scale and one phase yielded **294 excursions**; I
declared that cell in §5 and it was too small. The same quantity pooled over the full grid has
**9,766 excursions at x = 2.0 and reads +0.0339 at t = +14.72.** Pooling was **not** the
pre-registered primary and is reported as what it is.

## 1. The x ladder — the prediction that separates the mechanism from an artefact

Pooled over all scales and phases, with the **pre-registered session-level block bootstrap**:

| x (σ) | excursions | excess | clustered SE | t |
|---:|---:|---:|---:|---:|
| 1.0 | 71,841 | +0.0217 | 0.0008 | **+27.87** |
| 1.5 | 34,019 | +0.0278 | 0.0011 | **+24.37** |
| **2.0** | **9,766** | **+0.0339** | 0.0023 | **+14.72** |
| 2.5 | 1,525 | +0.0465 | 0.0060 | **+7.79** |
| 3.0 | 105 | +0.0603 | 0.0207 | **+2.91** |

**The excess rises monotonically with the rarity of the excursion, and it is significant at every
step.** That is exactly the principal's mechanism — *"on rare oscillations it will move closer to
its extremes, we then trade in the direction towards its mean"* — and it is the one prediction (P3)
whose failure would have marked the signal as a routine-oscillation artefact. **It did not fail.**

**§11's declared split test is answered by the same column.** The excess does **not** peak at
k = 2.0σ; it **keeps rising to 3.0σ**. So the entry is **deeper than the envelope** — they are
distinct objects, and a construction should enter further out than the band that characterises the
window.

**The design effect of clustering is ≈ 1.0.** The clustered SE and the binomial SE agree to two
digits at every x, so excursions across phases and scales are close to independent in their return
outcomes despite sharing price paths. That was worth checking rather than assuming.

## 2. THE ABSOLUTE RETURN RATE IS NOT A WIN RATE, and this is the most important caveat

**P(return) is 0.9286 observed and 0.9070 under the null.** Both are near-saturated, and the reason
is structural: **the level is the least-squares line through the window, so the residual sums to
zero by construction and MUST cross it.** Returning to the level is very nearly certain whatever
the data does.

**Three consequences, all of which the record has to carry:**

1. **0.93 is not a tradeable win rate.** The level is fitted using the whole window, the future
   included. No causal rule has it.
2. **The measurable excess is compressed into the top ~9% of headroom.** A +0.034 excess on a 0.91
   base is a large fraction of what was available to find.
3. **But the null shares the identical construction**, so the **excess** is exactly the part
   attributable to the real *arrangement* of moves rather than to the level's definition. The
   excess is the finding; the base rate is arithmetic.

## 3. The horizon curve — the advantage is FAST

At the primary cell, x = 2.0σ:

| τ (s-bars) | P(returned) obs | null | excess | P(extended) obs | null |
|---:|---:|---:|---:|---:|---:|
| 5 | 0.9116 | 0.8467 | **+0.0648** | 0.0612 | 0.0712 |
| 10 | 0.9184 | 0.8990 | +0.0194 | 0.0646 | 0.0797 |
| 20 | 0.9286 | 0.9070 | +0.0215 | 0.0544 | 0.0797 |
| 40 | 0.9320 | 0.9130 | +0.0190 | 0.0510 | 0.0758 |

**The excess is largest at a quarter of a window and decays as the horizon lengthens** — given
enough time the null catches up, because both must eventually cross. So whatever edge exists is a
*speed* edge, not an *eventuality* edge, which matters for how a construction would be timed.

**And the three-way outcome points the tradeable way:** real excursions **extend less often**
(0.0544 against 0.0797) as well as returning more often. Both halves of the asymmetry favour the
reversion side.

## 4. The range is nowhere near the cost — the "untradeable" branch does NOT apply

Median range `W` at k = 2σ, s = 5, in ticks and in dollars at micro size:

    NQ 309.9 tk = $155   GC 156.1 = $156   PL 140.3 = $702   BTC 138.3 = $69
    HO 124.7 = $524      RB 116.9 = $491   YM 111.2 = $56    SI 99.0 = $2,474
    ES  52.3 = $65       CL  50.5 = $51    RTY 77.1 = $39    6E 28.4 = $36

**22 of 22 roots have a 2σ range above $6**, i.e. more than twice a $3 round trip, and most are
one to two orders of magnitude above it. **The decision rule's "a target exists but is
untradeable" branch is not the one we are in.** (This is the branch the first run could not
evaluate at all — see §6.)

## 5. Predictions, scored

| | prediction | measured | |
|---|---|---|---|
| **P1** | primary excess in [−0.02, +0.04] | **+0.0215** primary, +0.0339 pooled | **LANDS** |
| **P2** | Spearman(excess, D526 Hu) < −0.4 | **−0.168** on 15 roots | **FAILS** — right sign, far too weak, and per-root excursion counts are 5–33 so it is barely measurable |
| **P3** | excess **rises** with x | **+0.0217 → +0.0603, monotone** | **CONFIRMED** |
| **P4** | A1 admits 20–50% | **2.7–3.8%**, flat across all seven scales | **FAILS decisively** |
| **P5** | range predictability > +0.3 | W lag-1 **+0.26 / +0.29 / +0.32** at s=1/2/3, +0.01 at s=5 (5 roots) | **MARGINAL** — clears at s=3 only |
| **P6** | reverting share > 70%, excess over null < 15 pts | **71.2–73.2%**, flat across all seven scales | **first half LANDS** — and remarkably scale-invariant |

**P6 is the principal's 80% claim, measured: 72% of admitted windows have more level crossings than
their own sign shuffle produces, and the figure is the same at every scale from 1 to 20 minutes.**
That scale-invariance was his prediction from self-similarity and it holds to within 2 points.

**P4's failure is the one to think about.** A1 admits 3% of windows, not 20–50%. The self-test
measured ~6% admission on a constant-volatility random walk, so **real data is admitting at roughly
the random-walk rate** — the "stable level and range" structure is no commoner in the market than in
noise. Either the split-half thresholds are too tight, or a stable level is genuinely rare. The
threshold was declared in advance and has not been touched; loosening it is a separate,
pre-registered question.

## 6. Defects in this record's own instruments

1. **`session_bars` demanded a fixed 420-minute grid, which would have silently excluded every
   grain at every scale.** ZW's session is roughly 09:31–14:21 — **291 minutes is its trading day,
   not a gap** — while NQ and ES carry 420.0 bars in 100% of in-sample sessions with one unbroken
   run. Found by looking at the fixture rather than at the code; the path is now sampled inside each
   session's own longest contiguous run. **This is the same per-root-session-band error the day5m
   fixture already recorded, and I walked into it again.**
2. **THREE pre-registered outputs were not computed by the first run** — range predictability
   (item 7 / P5), the reverting share (P6), and **the range in ticks and dollars (item 3), which
   gates a branch of the decision rule.** All three were added and the run repeated rather than the
   omission being documented. **This is the third occurrence of this failure mode** (D506 compared a
   different quantity than its spec declared; D523 never computed a declared secondary), and the
   pattern is that outputs which are not part of the primary do not get wired up.
3. **Two arithmetic corrections to the spec's ladder**, recorded rather than quietly applied:
   **s = 21 is infeasible** — N bar-returns need N+1 price points and 420/21 = 20 points yields 19,
   so the top step is 20 minutes; and **§11's split test belongs to the x ladder, not the k
   ladder**, because the conditional return probability does not depend on the envelope radius at
   all.
4. **`traverses` looped over windows** — ~8M interpreter iterations across the grid. Vectorised and
   asserted equal to the reference loop.

## 7. Verdict by the pre-registered decision rule

**UNRESOLVED on the letter.** "A target exists" required the primary to clear 2 SE **and** P3 to
hold. **P3 holds decisively; the primary does not clear.** The honest statement is that the
pre-registered cell was underpowered by my own declaration — 294 excursions out of the 9,766 the
grid contains — and that the pooled ladder, which was not the primary, shows the mechanism's
signature at t = +14.7 with monotone rarity dependence.

**What is established:** a rare excursion from a least-squares level returns to that level more
reliably than the same magnitudes in random order, the advantage grows with rarity, it is fastest
at short horizons, and the range it traverses is one to two orders of magnitude larger than the
crossing cost.

**What is not:** whether any of it survives a level that does not use the future. **That is the
reserved slice's question and it remains unread.**

Nothing enters `FINDINGS.md`, `RULES.md`, `COMPONENTS_PROP.md` or either book on this record
(R8, R15).

---

# 8. ADDENDUM, same day — **THE EDGE IS SELF-SIMILAR, and it is indexed by BARS rather than by the CLOCK**

The scale ladder was computed by the first run and reported only pooled — the same
"computed but not surfaced" failure as §6.2, in a third guise. It is the table that answers
whether the market is self-similar in the principal's sense, so it is now printed by default
(structural fix 3).

## 8.1 The excess is FLAT across six scales spanning 13× in clock time

Excess at x = 2.0σ, τ = 20 bars, pooled over phases, with the session bootstrap:

| s (min) | window (min) | excursions | excess | SE | t |
|---:|---:|---:|---:|---:|---:|
| 1 | 20 | 3,882 | **+0.0319** | 0.0036 | +8.99 |
| 2 | 40 | 2,293 | **+0.0335** | 0.0049 | +6.76 |
| 3 | 60 | 1,717 | **+0.0394** | 0.0050 | +7.93 |
| 5 | 100 | 1,002 | **+0.0355** | 0.0074 | +4.83 |
| 8 | 160 | 558 | **+0.0306** | 0.0103 | +2.98 |
| 13 | 260 | 261 | **+0.0359** | 0.0130 | +2.76 |
| 20 | 400 | 53 | +0.0157 | 0.0313 | +0.50 |

**+0.031 to +0.039 with no trend, over windows from 20 minutes to 260 minutes.** The only
departure is s = 20, which has 53 excursions and t = +0.50 — noise. **Higher timeframes work
exactly as well as lower ones**, which is self-similarity measured rather than assumed.

## 8.2 The speed edge decays in BARS, not in MINUTES — and that is the sharper finding

| s (min) | τ=5 | τ=10 | τ=20 | τ=40 |
|---:|---|---|---|---|
| 1 | +0.0731 (5m) | +0.0392 (10m) | +0.0319 (20m) | +0.0290 (40m) |
| 2 | +0.0750 (10m) | +0.0426 (20m) | +0.0335 (40m) | +0.0311 (80m) |
| 3 | +0.0790 (15m) | +0.0423 (30m) | +0.0394 (60m) | +0.0343 (120m) |
| 5 | +0.0738 (25m) | +0.0372 (50m) | +0.0355 (100m) | +0.0320 (200m) |
| 8 | +0.0641 (40m) | +0.0303 (80m) | +0.0306 (160m) | +0.0294 (320m) |
| 13 | +0.0752 (65m) | +0.0363 (130m) | +0.0359 (260m) | +0.0359 (520m) |
| 20 | +0.0754 (100m) | +0.0169 (200m) | +0.0157 (400m) | +0.0157 (800m) |

**Read the τ=5 column: +0.064 to +0.079 from 5 minutes of clock time to 100 minutes.** The edge is
the same size whether "five bars" means five minutes or an hour and a half. **And the halving from
τ=5 to τ=10 happens at every scale** — 5→10 minutes at s=1 and 65→130 minutes at s=13, a 13×
difference in clock time and the same decay.

**The clock-time overlay makes it decisive.** At 10 minutes elapsed, `s=1, τ=10` gives **+0.0392**
while `s=2, τ=5` gives **+0.0750** — same clock time, nearly double the excess, because what
matters is **bars elapsed, not minutes elapsed**. At 40 minutes: +0.0290 (s=1, τ=40), +0.0335
(s=2, τ=20), +0.0641 (s=8, τ=5).

**So "how fast" has no answer in minutes.** The answer is **within about 5 bars of whatever scale
you are looking at**, and a construction's time stop must be set in bars, not in clock time.

## 8.3 The rarity gradient holds at 5 of 7 scales

| s | x=1.0 | x=1.5 | x=2.0 | x=2.5 | x=3.0 | monotone |
|---:|---|---|---|---|---|---|
| 1 | +0.0188 | +0.0249 | +0.0319 | +0.0471 | +0.0645 | **YES** |
| 2 | +0.0235 | +0.0296 | +0.0335 | +0.0393 | — | **YES** |
| 3 | +0.0222 | +0.0293 | +0.0394 | +0.0516 | — | **YES** |
| 5 | +0.0240 | +0.0313 | +0.0355 | +0.0592 | — | **YES** |
| 8 | +0.0253 | +0.0273 | +0.0306 | +0.0157 | — | no |
| 13 | +0.0324 | +0.0321 | +0.0359 | +0.0792 | — | **YES** |
| 20 | +0.0244 | +0.0519 | +0.0157 | — | — | no |

The two failures are the two thinnest cells. **P3 is therefore not an artefact of pooling** — it
holds independently at five scales.

## 8.4 Three structural fixes, in code rather than in prose

1. **`REQUIRED_OUTPUTS` is a manifest in the runner and `check_outputs` RAISES** before anything
   is reported. Verified to fire — it names 10 missing outputs on a stub artefact — and to pass on
   the real one. This is the answer to §6.2 recurring three times: prose in a record does not
   catch an unwired output, a guard does.
2. **The SESSION BAND PER ROOT is now in the fixture metadata**, measured at build time, with the
   reason attached. The build prints it: **28 roots span all 420 minutes and 7 are shorter** —
   HE and LE 276 minutes (09:31–14:07), ZC/ZL/ZM/ZS/ZW 292–294 (09:31–14:22). A fixed grid drops
   all seven silently, which is what §6.1 did.
3. **The scale breakdown prints by default**, because it was computed, not surfaced, and it carries
   §8.1 and §8.2 — the whole self-similarity result.
