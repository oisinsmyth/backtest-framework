# D474 — PRE-REG: does continuation, conditioned on volatility state, carry a signed edge that clears the micro cost?

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D474-PRE-REG-does-continuation-conditioned-on-volatility-state-carry-a-signed-edge-that-clears-the-micro-cost.md`. The H1 above is the full title.*

**2026-09-12, committed before the runner exists** (CLAUDE.md, [R8](../RULES.md#r8)).
Hypothesis proposed by the principal: **volatility for timing, continuation/momentum for
direction.**

---

## 0. Why this is not already answered, and why I nearly got it wrong

[D473](D473-RESULT-the-cost-structure-picks-the-horizon-hours-not-minutes.md)
§4 ruled out momentum entries on the grounds that the variance ratio is **0.82–1.02 across five
time grids and four volume grids, never above 1.02**.

**That variance ratio is POOLED OVER ALL STATES.** A pooled figure of 1.00 is exactly what you
get when momentum in one state and reversal in another cancel — and this repo has already been
caught by that precise error: D435, *"a volume shock is +38 in top-momentum names and −48 in
top-price ones; D434 averaged them to −7."* The standing memory reads *"a universe average hides
sign flips — condition the atlas."*

So D473 §4 does **not** dispose of the principal's hypothesis, which is the *conditional*
version. It is being tested properly here. (The same caution applies to my own habit recorded
as *construction vs axis*: one pooled statistic does not close a family.)

## 1. Data, fixed now

| | |
|---|---|
| fixture | `data/fixtures/fut_ES_rth_1m.csv.gz` — ES passes G1–G5, `usable_start` 2016-01-04 |
| window | **2016-01-04 → 2023-12-29** (D462 in-sample). **2024+ is not read.** A gate raises if any row past 2023 reaches the measurement. |
| session | RTH 09:30–15:59 as the fixture defines it; half-days (G3 lists 128) excluded |
| windows | **non-overlapping**, within one session, **single contract** — no roll straddle |
| cost | **3.409 MES ticks** per round trip (D465 crossing 1.009 + D466 commission 2.400) |

## 2. The construction, fixed now

For each non-overlapping h-minute window, `r_t` = (close of last minute − open of first
minute) / 0.25, in ticks.

- **Direction (continuation):** take the sign of `r_t`; the trade is that sign, held for the
  *next* window `t+1`, entered at its open and exited at its close. Nothing else enters the
  entry decision.
- **Horizons h ∈ {15, 30, 60, 120, 195} minutes.** 195 is half a session; D473 says the
  cost-optimal zone for 5% skill is ~325 min, so this grid brackets the plausible region from
  below and 195 is the longest that still gives non-overlapping pairs within a session.
- **Timing (volatility), two variants, because one of them is degenerate with the signal:**
  - **V1 — own magnitude:** quintiles of `|r_t|`. This is "a big move continues", and note the
    conditioner and the direction come from *the same observation*.
  - **V2 — prior regime:** quintiles of realised volatility over windows `t−3, t−2, t−1`,
    **strictly before the signal window**, so the conditioner is independent of the signal's
    own magnitude. This is "in a volatile regime, moves continue".

  Both are reported. V2 is the honest test of the hypothesis as stated; V1 is reported because
  it is the version most people mean.

## 3. The statistic, fixed now

**Primary — gross edge per trade, in ticks:** `mean( sign(r_t) · r_{t+1} )`, with its
t-statistic over non-overlapping windows. This is the quantity the standing signal criterion
names (*a signal = positive GROSS mean per trade above the nulls*), and it is in the same units
as the cost so the two can be compared without a conversion.

**Secondary:** hit rate `P(sign(r_{t+1}) = sign(r_t))`, implied skill `a = hit − ½` for
comparison with D473's table, and the net edge `gross − 3.409`.

**All four reporting groups** (CLAUDE.md) accompany any cell that passes: net and gross side by
side, the trade distribution with median and both-tail trims, the year-by-year split, and the
null distribution's p50 **and** p95.

## 4. The null, fixed now

**50 cells** (5 horizons × 5 buckets × 2 variants), so a per-cell threshold is not admissible.

- **Null construction:** within each volatility bucket, **independently randomise the sign of
  the signal** `sign(r_t)`, leaving `r_{t+1}` and the bucket membership untouched. This breaks
  **exactly** the claimed ingredient — that the previous window's direction predicts the next —
  while preserving the return distribution, the volatility clustering and the bucket structure.
  (Standing error to avoid: *a control must break the claimed ingredient*; D411's VOL-SHUF
  preserved the sign it meant to test.)
- **2,000 draws.** Statistic: the **family maximum** |t| across all 50 cells. Report the null's
  **p50 and p95**, not the percentile alone.
- **Carry the p95's bootstrap SE.** Per D373's rule, an observed maximum within **2 SE** of the
  null p95 is recorded **UNRESOLVED**, not a pass.

## 5. The bar, fixed now

| verdict | requires |
|---|---|
| **SIGNAL PRESENT** | a cell's gross edge > 0 **and** the family-max \|t\| exceeds the null p95 by more than 2 SE |
| **TRADEABLE** | additionally, gross edge > **3.409 ticks**, so the cell clears cost at micro size |
| **COMPONENT** | neither of the above is sufficient: `COMPONENTS_PROP.md` C-a–C-e must be met on a daily P&L series at minimum size, and that needs its own runner and record |

**Nothing enters `COMPONENTS_PROP.md` or either book off this runner.** A pass here licenses
writing a component study, nothing more.

## 6. Predictions, in the runner's own quantities

Recorded so they can be checked rather than admired (*predictions must be checkable*):

- **X-a.** The gross edge pooled over all cells lands **within 2 SE of zero**. Rationale: a
  variance ratio of 0.82–1.02 bounds the summed return autocorrelation at roughly |Σρ| ≤ 0.01.
- **X-b.** **No cell** shows gross edge > 3.409 ticks with a family-max |t| clearing the null
  p95 by 2 SE. I expect the hypothesis to fail at the *tradeable* bar.
- **X-c.** The sign at **h = 15 will be NEGATIVE** (reversal, not continuation) and will drift
  toward zero as h grows — because the measured variance ratio is furthest below 1 at the
  finest sampling and reaches ~1.00 by 15–60 seconds.
- **X-d.** Under **V1**, the top `|r_t|` quintile will show a **more negative** edge than the
  bottom — big moves revert more than small ones.
- **X-e.** Implied skill `a` in every cell will be **below 3%**, i.e. beneath the floor D473
  found for any horizon to reach C-a's Sharpe 0.5.

**If X-c and X-d hold with the sign I predict, the honest reading is that the principal's
hypothesis is right about the conditioner and wrong about the direction** — volatility does
carry timing information (ρ = +0.31, D471), but the directional term is reversal rather than
continuation. That variant is then the one worth a separate pre-registration, and this record
does **not** pre-authorise it.

## 7. What would make me wrong

Any cell with gross edge **> 3.409 ticks** and a family-max |t| more than 2 SE above the null
p95. A positive gross edge **below** cost is a signal and not a trade, and would be recorded as
such — it would then be a candidate for the longer horizons D473 §3 says cost prefers, which
this grid does not reach (325 min needs cross-session pairs and the RTH fixture cannot supply
them without collecting the overnight move).

## 8. Stated limitations, before any number exists

1. **RTH only.** The overnight session is where C1's edge lives and this grid never sees it.
2. **The ±|M| framing of D473 does not apply here** — this measures a realised signed edge
   directly, so no outcome model is imposed. But the exit is fixed at the window close; no stop,
   no target, no volume-clock exit (D472's +1.18 pp is *not* applied, so any pass understates by
   roughly that much).
3. **Half a session is the longest horizon**, which is short of the cost-optimal zone.
4. **One instrument.** ES only; 41 roots are on disk and untested for this.
5. **Skill constancy is not assumed here** — each cell is measured independently.
