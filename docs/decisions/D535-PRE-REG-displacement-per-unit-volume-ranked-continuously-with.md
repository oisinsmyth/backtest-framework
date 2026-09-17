# D535 — PRE-REGISTRATION: displacement per unit volume, **ranked continuously**, with five declared guards against averaging the effect away

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D535-PRE-REG-displacement-per-unit-volume-ranked-continuously-with-five-guards-against-averaging-the-effect-away.md`. The H1 above is the full title.*

**Pre-registration. Committed before the runner exists (R8). Result in a separate file.**
**In sample 2016-01-04 → 2023-12-29. The 2024+ slice is RESERVED AND NOT READ.** Nothing admitted (R15).

*On the principal's instruction, 2026-09-15: run the ranking, and "make sure you don't average out an
important result… I haven't identified a problem but my intuition is telling me there is potential
for one."*

---

## 0. The construction

D534 gated on a **conjunction** — `|z| > 1` AND thin — and the conjunction turned out to occur at 44–57 %
of the rate independence predicts, leaving ~7 trades a year per root. This record measures the same
quantity **continuously**, on every session:

| | |
|---|---|
| `lr` | `log(C[h08] / O[h18])` — the overnight return, **signed** |
| `v` | night volume, h18 → h08 |
| **`x`** | **`log(|lr|) − log(v)`** — displacement per unit volume, Amihud illiquidity in logs |
| `xd` | `x` less its **trailing** 50-session mean (shifted) |
| **`pct`** | `xd`'s **trailing 250-session percentile** (shifted) — high = price moved far per contract traded |
| **direction** | `sign(lr)` |

High `pct` is the story's state: **price travelled and nobody traded against it**, so whoever took the
other side holds it unwillingly. **WITH** = the break's side equals `sign(lr)`; **AGAINST** = it does not.

**A causality fix that also corrects earlier practice.** D533's terciles and D534's thresholds were
taken over the **whole sample**, so today's bucket membership was decided partly by future sessions.
It affects membership, not outcomes, so it is mild — but it is a leak, and it is avoidable. **Every
rank here is a TRAILING quantile**, shifted, and the record says so because the earlier ones were not.

## 1. The five guards — declared, because an average is where a real effect goes to die

The principal has not named a fault; these are the four places I can find where this design would
report ~0 while something real sits underneath, plus the one that stops the record.

**G1 — up-breaks and down-breaks are NOT pooled inside WITH.** A WITH trade is either *(night up,
break up)* — short covering — or *(night down, break down)* — long liquidation. **These are different
mechanics and there is no reason their magnitudes match.** The runner reports all **four** cells
(night side × break side) with n and mean. D531 hid a 7.7–9.3 point spread this exact way.

**G2 — roots are reported, never only averaged.** Per-root contrast, its n, and the **count of roots
agreeing in sign**. An effect on three of ten markets and absent on seven is a different object from a
weak effect on all ten, and the mean cannot tell them apart.

**G3 — the whole rank profile, not one bucket.** The contrast is reported **by decile** of `pct`. A
tercile dilutes an effect that lives in the extreme tail by mixing it with two-thirds of nothing.

**G4 — mean AND trimmed mean, both declared in advance.** D533's tails were ±$10k on 25 trades a side;
a mean over ~600 trades with tails that size is mostly tail noise, and a real body effect can hide
under it. The **symmetric 1 % trim** and the **median** are computed for every declared cell.
**The mean is the pass statistic** (it is the programme's signal criterion). The trim is a declared
diagnostic with its own null and **cannot upgrade a fail to a pass** — but if the two disagree, that
disagreement is the result and is reported as the headline.

**G5 — era split.** Every declared cell is reported on **2016–2019** and **2020–2023** separately. An
effect that died in 2020 averages to half of itself across the window.

## 2. Universe — ten roots, and a declared reason

**Primary set (continuity with D533/D534): CL, GC, SI, NG.**
**Confirmation set, declared here and not chosen afterwards: HG, HO, RB, ZN, 6E, ZC** — copper, two
refined energies, rates, FX and a grain, all non-index, all with clean day5m coverage from 2016.

The confirmation set is **not** a widening of the selection family: the primary is scored on the four
candidate roots alone, and the other six exist so that **G2's sign count has ten markets to speak
with** rather than four. Index roots are excluded throughout — a second index arm beside the admitted
NQ arm is a closure offence under the one-direction rule, not merely a C-b failure.

## 3. The statistic

**Gross dollars per trade at minimum tradable size**, normalised per root by that root's **trailing
250-session sd of its own unfiltered break P&L** (shifted) — trailing rather than whole-sample so a
volatility regime change cannot make one era dominate the mean (that is G5's companion). Roots are
**equal-weighted**; the n-weighted version is reported beside it, because n-weighting recreates
D533's SI-dominance problem in another guise.

Exit: **the fixed 60 minutes**, as in D534. No exit rule is tested here (FINDINGS §75).

> **PRIMARY: the contrast mean(WITH) − mean(AGAINST) in the TOP DECILE of `pct`, equal-weighted over
> CL/GC/SI/NG, 60-minute exit.**

**Family (the declared unit of selection): 6 pooled cells** — {top decile, top tercile} × {30, 60,
120 min}. Per-root, per-decile, per-era and the four G1 sub-cells are **diagnostic and unpromotable**.

## 4. Nulls

**N1** — cyclically rotate the night state `(pct, sign(lr))` **as a coupled pair** against the day that
follows it, per root, 1,000 draws. Destroys the night→day link and nothing else: the day's breaks and
moves, the night state's distribution and its serial correlation, and the coupling between
displacement and direction all survive.

**N2** — the family maximum over the 6 declared cells, one offset per root per draw common to every
cell.

**N3** — a null for the monotone trend: the Spearman correlation between decile index and contrast,
against the same rotation.

**PASS requires: the primary contrast > 0, clearing its N1 p95, AND the family maximum clearing N2.**

## 5. Predictions, in the runner's own quantities

- **P-1 (primary).** contrast > 0 and above its N1 p95.
- **P-2 (the sharper one).** **Monotone**: Spearman(decile, contrast) > 0 and above its N3 p95. A
  single bucket clearing could be selection; an ordering across ten could not as easily.
- **P-3 (G2's bar).** The per-root contrast is positive on **≥ 8 of 10** roots. P(≥8 | coin) = 5.5 %.
  The count is reported whatever it is.
- **P-4 (falsifier).** A negative top-decile contrast means a displaced, unpaid-for night predicts the
  day **fading** it — a reversion story, not this one.
- **P-5 (the stopping condition, and this one is new).** **If the four G1 sub-cells do not agree in
  sign, the pooled contrast is declared UNINTERPRETABLE regardless of what its null says**, and the
  record reports the decomposition instead of the average. This is committed here precisely so it
  cannot become a post-hoc excuse for a number I do not like.

## 6. Premise checks, run BEFORE anything is scored

1. **[F]** the night precedes the session — `corr(C[h08], first open) > 0.99` per root, as D534.
2. **Coverage** — `finite n of m` for `x` and `pct` per root; **raise** if the top decile is empty.
3. **Duty cycle** — n per declared cell; a pooled cell under **200** trades is not scored.
4. **[X]** the trailing rank must be causal: assert a session's own value is excluded from its
   reference window, and that a deliberately shifted state fails the alignment check.

## 7. What a pass would mean

A **candidate**, not a component. The component line (C-a…C-e in dollars at minimum size under the
cost that size pays, with its correlation against the ledger and **its duty cycle**) is computed by
the runner whatever the outcome — D534's failed on duty cycle at 7 trades a year, and that check
comes before any Sharpe is read.

**The reserved slice is not read by this record under any outcome.**
