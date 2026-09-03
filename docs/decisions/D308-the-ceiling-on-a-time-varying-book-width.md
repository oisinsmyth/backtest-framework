# D308 — the ceiling on a time-varying book width

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-03
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## The object

**`A(N, t)`** — family `A` ∈ {`none`, `target`, `none+overlay`, `target+overlay`},
width `N` ∈ {2, 3, 5, 7, 10, 14, 19}, per bar `t`. **28 series, all of which
already exist from D306** and are reproduced here rather than re-derived.

The question is whether **`N(t)`** — a width that moves with time — beats the best
**static** `N`, and if so whether any observable tracks it.

**The static grid is the baseline and stays in every table.** It is what a
variable rule must beat, and it is the reference for everything after.

## THE PREMISE THAT MAKES THIS NON-TRIVIAL, AND ITS PRICE

D300's invariance results — turnover fixed at `1/k`, cost per bar unmoved by `N`
— are **static-N** statements. **A width that moves pays a transition cost that a
static one never does**, and at the round trips measured (73–107 bp) **one full
19 → 2 move costs 60–90 bp** against a book whose best net is +15 bp/bar.

**So an `N(t)` rule can afford roughly one full-width move per 4–6 bars before
the transitions consume the entire edge.** That is not a refinement to add later;
it decides the family, and it is what closed D299's ladder.

### The transition model, declared

Moving from `N₁` to `N₂` with equal weights rebalances every surviving position
as well as opening or closing the difference:

```
traded fraction  =  2 · |N₁ − N₂| / max(N₁, N₂)
transition cost  =  traded fraction · rt / 2
```

19 → 2 gives 1.789 × rt/2 ≈ **80 bp** at rt = 90. `rt` is the held-name round trip
of the width being moved to. **Transitions are charged in every stage below**,
including the oracle.

---

## Stage 1 — THE CEILING, and it runs first because it can close the study

**The decisive question is not which indicator tracks `N*(t)`. It is how much
there is to win with perfect foresight.**

```
oracle(f)  =  choose N with hindsight, once per f bars, to maximise the objective
              over that block
ceiling    =  oracle net  −  best static N net
```

**Decision frequencies `f` ∈ {1, 5, 21, 63} bars.** `f = 1` is the absolute
ceiling and will be absurd — it fits bar-level noise — and is reported as the
upper bound it is, not as an achievable number. **`f = 63` charged for
transitions is the realistic one.**

Three rows per family, on **both** objectives:

| | bounds |
|---|---|
| best static `N` | the baseline |
| oracle `N(t)`, transitions **not** charged | the absolute ceiling |
| oracle `N(t)`, transitions **charged** | the realisable ceiling |

**If the charged 63-bar oracle beats the best static `N` by little, no indicator
can matter and the study closes in one run.** That is the point of running it
first.

## Stage 2 — PERSISTENCE, which decides whether any indicator *could* work

From the block oracle: the distribution of `N*(block)`, its lag-1
autocorrelation, its **mean run length**, and the share of the ceiling that
survives when `N` may change only every `f` bars.

**A conditioner can only help if `N*(t)` persists longer than a transition takes
to amortise.** With a full-width move costing 60–90 bp and the book earning ~15
bp/bar, that threshold is **4–6 bars**; smaller moves amortise faster in
proportion. **If `N*` is white noise at every frequency, nothing predicts it and
the study closes here**, whatever Stage 1 said.

## Stage 3 — CONDITIONERS, only if Stages 1 and 2 both survive

**The target variable is the CONCENTRATION PREMIUM, not the level of returns:**

```
premium(t)  =  A(2, t)  −  A(19, t)        per family, per bar
```

**This corrects D300's Arm 2**, which declared the target as "the realised top-j
spread" — the *level*. A conditioner that forecasts the level tells you when to be
in the market, which is the overlay's job and already tested. **Only something
that forecasts the premium tells you what width to hold.**

**Four conditioners, declared, all lagged:**

| | | |
|---|---|---|
| **X1** | **cross-sectional return dispersion** — sd of returns across live names | the edge *is* the gap between the ends of a ranking, and that gap is bounded by how far apart names move at all |
| **X2** | **signal separation** — composite score gap between rank 2 and rank 19 | how confidently the ranking can be made |
| **X3** | **breadth** — count of warm-and-live names | how much there is to choose from |
| **X4** | **X1 × X2** | theory wants both: a confident ranking over a dispersed cross-section |

**Scored as Spearman correlation with `premium(t)`, each against a circular
rotation of the conditioner** — these are strongly autocorrelated and a textbook
p-value assumes an independence that does not exist. 200 rotations. **BH-FDR at
q = 0.10 across all conditioner × family × objective combinations**, and the
max-|ρ| priced by the rotation null.

**Stage 3's output is a hypothesis, not a rule.** Any rule gets its own
pre-registration and is scored **against the best static `N`** — never against the
incumbent 19, or it banks the concentration gain D300 already established.

---

## Statistics

**Net bp/bar and Sharpe, both primary and reported separately at every stage.**
D306 had net pointing at N=2 and Sharpe at N=7; **they will give different `N*(t)`
paths and neither is "the" answer.** Net uses each width's own held-name round
trip; the mean-based figure is carried as the truncation artefact D302 showed it
to be.

## Nulls

- **Stage 1** has no null: an oracle is an upper bound by construction.
- **Stage 2's** run-length is compared against `N*` **shuffled**, preserving its
  level distribution and destroying its ordering.
- **Stage 3** uses the rotation null above.
- **Any rule that follows** needs a control that switches `N` at the **same rate
  and with the same persistence** at unrelated times — matched-count is not
  matched-turnover (D279) and a per-bar redraw churns (D291).

## Predictions

Four are against.

| | prediction |
|---|---|
| **Q1** | the `f = 1` oracle beats the best static `N` by **> 50 bp/bar** uncharged — mechanical, it fits bar-level noise, and it is a sanity check on the harness rather than a finding |
| **Q2** | **the `f = 63` oracle, transitions charged, beats the best static `N` by under 5 bp/bar.** *Against the premise of the study* — **load-bearing** |
| **Q3** | **`N*(block)` has a mean run length below 2 blocks at every frequency**, i.e. close to white noise. *Against* — **load-bearing** |
| **Q4** | transitions consume **more than half** of whatever the uncharged oracle gains at `f` ≤ 21 |
| **Q5** | the Sharpe-optimal `N*(t)` path is **more persistent** than the net-optimal one, Sharpe being the smoother statistic |
| **Q6** | **X1 (dispersion) is the strongest of the four**, and the only one clearing its rotation null |
| **Q7** | **no conditioner survives BH at q = 0.10.** *Against the study's own motivation*, and consistent with D299, which tested a variable `N` conditioned on P&L state and got 1 of 24 cells against 1.2 expected while losing to the deliberately-invalid control |
| **Q8** | the four families give **materially different** `N*(t)` paths — if they agree, the exit axis is irrelevant to width timing and one family suffices |

## Stop conditions

- **Q2 confirms** (charged 63-bar oracle gains < 5 bp) → **close.** No indicator
  can beat a ceiling that low, and Stages 2 and 3 are not run.
- **Q3 confirms** (`N*` is white noise) → **close**, whatever Stage 1 showed.
- **both survive** → Stage 3 runs, and its output is a hypothesis needing its own
  pre-registration.
- **a conditioner survives BH** → the rule it implies is pre-registered
  separately, benchmarked against the best static `N`, with a rate- and
  persistence-matched switching control.

## Assertions

1. **[1] Reproduction.** At constant `N`, `A(N, t)` must reproduce **D306's
   published net and Sharpe** for all 28 cells to floating point. If it does not,
   this study is not on D306's book and no comparison to the static baseline is
   admissible.
2. **[2] The degenerate oracle.** An oracle allowed only one `N` for the whole
   sample must equal the **best static `N`** exactly. An oracle that cannot
   reproduce its own baseline is not an oracle.
3. **[3] Transitions are zero when `N` never changes**, and **monotone in
   |ΔN|** — a cost model whose charge does not move with the size of the move is
   not charging the move.
4. **[4] Nesting.** The `f = 1` oracle must be **≥** the `f = 5` oracle, which
   must be **≥** `f = 21`, uncharged. A less constrained optimum cannot be worse.
5. **[C] Cost dimensions** against d295's published 52.1893, with the doubled
   form rejected.
6. **[7] The self-test must raise on a deliberately broken book**, corrupting
   bars inside the mask.

## Scope

**Out:** any change to the entry signal, the gate, `k`, the exit thresholds, the
overlay's X, or the composite. Every family is D306's, unchanged. **No rule is
built in this study** — Stage 3 measures correlations and stops.

## Files

`docs/decisions/D308-the-ceiling-on-a-time-varying-book-width.md` (this record) ·
runner and data to follow, in separate commits.
