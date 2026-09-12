# D502 — PRE-REG: an orthogonal daily-clock confluence on the hourly MACD — the 200-day SMA regime, daily trendiness, and the volatility regime

**2026-09-13.** Committed **before the runner exists** ([R8](../RULES.md#r8)), and committed on
its own to claim the number — five collisions in two evenings came from writing runners first.

Requested by the principal: *"I still want you to Test the 200 day SMA regime filter or some
other confluence if you can think of another one that compliments momentum?"*

---

## 1. Why the last confluence was not one, and what "complements momentum" means

[D495](D495-RESULT-the-confluence-fails-decisively-and-produces-the-best-cell-anyway.md) tested
whether the two MACD variants must **agree**. The principal's correction stands: that is
**redundancy, not confluence** — the two variants agree 66–71% of the time where independent
signs would agree ~50%, so requiring agreement removed 30% of bars and only 6.5% of trades. Both
are MACDs on the same price series on the same clock. It had no independent information to add.

**A momentum rule needs two things: a direction, and a market that follows through.** The MACD
supplies the direction. So the complement is *not* another direction measure — it is a measure of
**whether follow-through is likely**. That is the reasoning behind the three conditioners below,
and it is why one of them is not the principal's SMA at all.

**All three live on the DAILY clock and are known before the session's first decision**, so they
are orthogonal in the way that matters: a different clock, different information, and no shared
construction with an hourly MACD. §5's premise checks measure that orthogonality rather than
assuming it.

## 2. The signal under test — unchanged, not re-tuned

The [D491](D491-RESULT-the-first-component-candidate-and-why-it-is-thinner-than-it-looks.md)
state machine and the [D484](D484-RESULT-log-MACD-is-a-real-signal-that-fails-only-on-cost.md)
signal code, imported unchanged. Day session, decide at each hour's close from h09, execute at
the next hour's open, exit when the signal turns after a minimum hold, forced flat at the close
of h15 (16:00 ET). **Minimum hold M = 5, the committed candidate's setting.** Cost $3 + 1.009
ticks a round trip at the instrument's minimum size.

**Primary arm: AGREE.** Secondary arms B1 (impulse) and B2 (plain), reported and covered by the
same family null.

## 3. The three conditioners

Each is computed from a **continuous back-adjusted daily log-price index** — the within-contract
close-to-close log return accumulated, with a zero return across a roll, so no roll jump enters a
200-session average. The daily close is the close of **h15**, the day session's own close, taken
from the **previous** session. Nothing reads the session being traded.

| | conditioner | state | why it might complement momentum |
|---|---|---|---|
| **R1** | **200-session SMA regime** — the principal's | daily index above / below its 200-session SMA | the canonical trend filter; the claim is that intraday momentum follows through in the direction of the slow trend |
| **R2** | **daily trendiness — the variance ratio** | `Var(r_5)/(5·Var(r_1))` over a trailing 252 sessions, above / below 1.0 | **this is the one that actually answers the question.** A momentum rule needs follow-through, and the variance ratio is follow-through measured directly. [D471](D471-RESULT-the-spread-barely-widens-and-path-efficiency-is-the-random-walk-value.md) told us to use the variance ratio rather than path efficiency, and it killed path efficiency **on the tick clock at 10 s – 5 h.** The daily clock is a different axis and is untested |
| **R3** | **volatility regime** | 20-session realised vol of the daily index, above / below its own trailing 252-session median | **[D501](D501-the-worst-day-is-a-regime-not-a-habit.md) motivates this in-sample**: 13 of the 20 days beyond −$500 and both P3 breaches sit in 2022, and four accounts died there. Declared as in-sample-motivated, so the rotation null carries the whole weight of it |

### The eight declared cells, and nothing else

| cell | what it does |
|---|---|
| `R1_GATE_UP` / `R1_GATE_DOWN` | trade only while above / only while below the SMA |
| `R1_DIR_ALIGN` | longs only while above, shorts only while below |
| `R1_DIR_COUNTER` | the mirror — shorts only while above, longs only while below |
| `R2_GATE_TREND` / `R2_GATE_CHOP` | trade only while the variance ratio is above / below 1.0 |
| `R3_GATE_LOWVOL` / `R3_GATE_HIGHVOL` | trade only while realised vol is below / above its median |

`DIR_COUNTER` is in the family because a gate that helps only in its mirror image is a sign
error, not a finding, and the family null prices both directions the same way.

## 4. The statistic, the null, and the window

**Primary statistic: the pooled net-Sharpe lift.** For each cell, `S_net(gated) − S_net(plain)`
averaged over the eight roots, both arms scored **on the identical session set** — the gated arm
carries a zero on every session it stands down, which is what the account actually experiences.

**The null: a circular rotation of the REGIME series.** 2,000 draws, offsets drawn over the
session axis. This is the correct null and not a shuffle: a regime is strongly autocorrelated,
and a rotation **preserves its duty cycle and its run-length structure exactly** while destroying
its alignment to price. A shuffle would destroy the persistence and make any persistent gate look
significant. What the rotation leaves intact is "a persistent block gate of this duty cycle";
what it destroys is "*this* regime". That is the ingredient under test.

**Reported for every cell:** observed, null **p50 and p95**, the p95's bootstrap SE, and the
margin in SE — with a margin inside 2 SE recorded **UNRESOLVED** (D373's rule). **Family-max
null over all 24 pooled statistics** (8 cells × 3 arms), and a separate family-max over the 24
candidate-cell statistics on NQ.

**Gross beside net, and trips per session, for every cell**, because a gate is a cost-cutting
lever as much as an edge lever and the two have opposite fixes.

**The window shortens and the baseline is restated.** R2 and R3 need 252 sessions of warm-up and
R1 needs 200, so the first ~252 sessions of 2016 carry no conditioner. Every figure is computed
on the reduced window, **including the unfiltered baseline** — the candidate's +0.723 is on the
full window and is not the comparison. The runner asserts the two arms see identical session
sets. **2024+ stays sealed.**

## 5. Premise checks, computed before the study statistic is read

A conditioner that is almost always on, or that flickers, cannot carry a regime claim
([stage-0 rule](../../CLAUDE.md)). Each conditioner must satisfy:

| | requirement |
|---|---|
| **duty cycle** | in [0.15, 0.85] |
| **persistence** | median run length ≥ 5 sessions |
| **orthogonality** | \|ρ\| < 0.10 between the regime state and the arm's own daily P&L, and between the state and the MACD sign |

A conditioner failing any of these is reported as **PREMISE FAILED** and its cells are reported
but not counted as tests of a confluence.

## 6. Predictions

| | prediction |
|---|---|
| **U-a** | R1's above-SMA duty cycle is **70–85% on NQ** and within [0.55, 0.90] on every root |
| **U-b** | `R1_DIR_ALIGN`'s pooled lift **does NOT clear** its rotation p95 — the SMA regime is mostly "up" on the index roots, so it barely bites |
| **U-c** | `R3_GATE_LOWVOL`'s pooled lift is **positive, ≥ +0.05**, and **does NOT clear** its null — cutting 2022 must help in-sample almost by construction, and the rotation is exactly what prices that |
| **U-d** | `R2`'s two cells read **\|pooled lift\| < 0.10** and neither clears |
| **U-e** | on the NQ candidate cell **at least one** of the eight cells reads above the restated baseline, and **none** clears the family-max null |
| **U-f** | every conditioner passes the orthogonality premise, **\|ρ\| < 0.10** — the SMA regime is not the MACD sign in disguise |

**I expect this to fail.** Five of six predictions are failures, and they are written that way
because the honest prior is [D494](D494-RESULT-outside-the-price-path-on-the-day-session-eighteen-cells-no-pick-the-largest-is-the-euro-at-one-tick-and-the-release-day-MACD-is-worse-not-better.md):
eighteen cells of gates from outside the price path produced no pick, the largest worth one tick.
The reason to run it anyway is that **R2 is a genuinely new axis** — trendiness on the daily
clock, which is the thing a momentum rule actually needs and which nothing here has measured.

## 7. Checks the runner must carry

1. **No look-ahead, proven**: the conditioner for session *t* is re-derived from sessions ≤ *t−1*
   in a second implementation that never calls the conditioner function, and a deliberately
   forward-shifted conditioner must make the assertion **raise**.
2. **The roll-neutral index**: assert no single-session move in the daily index exceeds 8 σ, and
   assert the naive (non-adjusted) index **fails** that check on at least one root — so the
   adjustment is proven to do something.
3. **The gate is a strict subset**: assert every gated entry is an entry of the ungated arm, and
   that trips fall or stay equal, never rise.
4. **`net = gross − cost × trips`** asserted exactly, with an identical trip count either way.
5. **Identical session sets** between the gated and plain arms, asserted per root.
6. **The rotation preserves duty cycle and run-length distribution** to within floating error,
   and a **shuffle is shown to destroy** the median run length — the difference the null depends
   on.
7. **The family-max null covers every statistic reported**, asserted by count.
8. Every `[X]` break must fire on the **scalar the assertion compares**, not on its name.

## 8. What this cannot do

- It admits nothing ([R15](../RULES.md#r15)). No ledger entry, no book entry.
- **In-sample only.** 2024+ is sealed and a cell that clears here is a candidate for that read,
  not a result.
- **R3 is motivated by a pattern already seen in-sample**, and no null can fully undo that. If R3
  is the only cell that clears, the honest reading is *selection*, and it is recorded as such.
- Fills remain open-of-next-segment at the measured half-spread. Every figure is an upper bound.
