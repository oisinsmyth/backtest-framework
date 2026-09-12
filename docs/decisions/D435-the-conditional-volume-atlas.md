# D435 — the conditional volume atlas: what volume means inside each state of price, momentum, volatility and the 20-day return

**A MEASUREMENT** (D280's class; D392/D434's form). **Scores no strategy, proposes no rule, admits
nothing (R15). Committed before the runner exists (R8).** D400–D434 used, D407–D410 and
D390–D399 reserved.

## 1. Why

D434 measured volume's base rates as universe averages and found the axis nearly flat (widest
spread 8.5 bp) with one exception (a 7–12 bp short-side drift after a volume shock). The
principal's objection: **volume may mean different things in different states, and an average
over the universe can hide opposite signs.** The atlas's own axes say which states have base
rates of their own — price (36.8), momentum (32.2), volatility (12.2), and the 20-day return
sign (±7–10 from D434's quadrants) — so those are the conditioners.

## 2. The grid

**Conditioners** (cross-sectional terciles per bar among eligible names, D392's rule, shifted to
`t−1` like every pool here): `price`, `mom` (12-1), `vol` (rvol21) from D392's `tercile_pools`;
`ret20` from D434's features. 4 × {lo, mid, hi} = **12 states**.

**Volume features** (D434's definitions, unchanged): `rv_lo`, `rv_hi`, `uv_lo`, `uv_hi`,
`ef_lo`, `ef_hi` (6 tercile pools), `rv_x3`, `cx_dn` (2 absolute shock pools).

**Cells:** every (state ∩ volume pool), long and short, cap 20, 200 draws, D392's kernel, seed
and draw. Tercile pools at **n = 10,000** (a state ∩ tercile has ~320k cells); shock pools at
**n = 3,000** (a state ∩ `rv_x3` has ~14k cells, ∩ `cx_dn` ~4k — 3,000 is what fits, and a pool
smaller than n records EMPTY). **192 cells:** 144 at 10,000 (~40 s each) + 48 at 3,000 (~25 s).
**Projected ~116 min serial; two halves on disjoint conditioners (`price`,`mom` | `vol`,`ret20`),
~60 min wall, ~1 GB each** — measured on D434's runs.

**Alignment:** every pool is the `t−1` feature placed at `t` (D434 ADDENDUM; `[F]` with its
break); the conditioner is shifted identically, so state and volume are both complete at the
close before the fill.

**Statistics per (state, feature axis):** the two cells' p50s and p95 ± SE; the **conditional
spread** = hi p50 − lo p50 inside the state, with an SE from the two cells' draw distributions;
and beside it D434's **marginal spread** for the same axis. **Heterogeneity** = the range of the
conditional spread across the three states of a conditioner. For the shock pools: the state's
long and short p50 against D434's marginal (−7 / +7 for `rv_x3`, −13 / +12 for `cx_dn`).

**Assertions:** `[K]` D392's kernel probe; `[T]` within each conditioner state the volume
terciles partition its eligible cells; `[F]` every combined pool equals (state at `t−1`) ∧
(feature at `t−1`) placed at `t`, with the break that removes the shift and must fire; `[E]`,
`[SE]`, `[P]` as D392; `[M]` the union over the three states of a (conditioner, feature) equals
D434's marginal pool for that feature (shifted), so the conditional cells decompose the marginal
and nothing else.

## 3. Predictions (LOW–MODERATE; D434's directional record is one of seven)

- **X-a** `uv` inside `ret20` terciles: the −8.5 marginal spread **shrinks below 5 bp in every
  state** — up-volume share is the 20-day return in a volume coat.
- **X-b** `rv` and `ef` inside every state: **|spread| < 8** everywhere — relative volume and
  effort-vs-result carry nothing in any state either.
- **X-c** the shock drift is **state-dependent in size, not in sign**: `rv_x3` and `cx_dn` shorts
  earn +5 to +20 in every state, **largest in `mom_lo`** (losers that shock keep losing) and
  **smallest in `price_hi`**.
- **X-d** heterogeneity: **at least one (state, feature) conditional spread exceeds 20 bp**,
  most likely `uv` inside `price_lo` or `vol_hi`, where the universe's base rates are widest.
- **X-e** the sum-of-parts check `[M]` passes, and the marginal spreads recomputed from the
  three conditional cells' trade-weighted p50s land within 3 bp of D434's.

X-d is the principal's hypothesis stated as a number; X-a is mine.

## 4. Not in scope

Any strategy, any rule, any holdout; 4-way crosses; the 15m fixtures. Thirty-fifth look by
object on this universe, and a measurement.
