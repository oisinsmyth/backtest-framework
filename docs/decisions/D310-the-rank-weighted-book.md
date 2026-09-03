# D310 — the rank-weighted book

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-03
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## Why

D308c measured the thing that decides this:

```
N=2 beats N=3 by      +9.70 bp/bar          <- the signal
sd of that difference  387.0 bp/bar
over the whole 3,187-bar sample             t = 1.41
bars needed for t = 2                       6,367   (~25 years; we have 12.6)
```

**Even the static claim "N=2 is the best width" is not established.** The *shape*
of the rank profile is solid — +15.25 at N=2 against −13.03 at N=19, large and
monotone — but the *location of the peak* rests on 1.4 sigma.

**Choosing a corner on that evidence is estimation risk with no expected return.**
A rank-weighted book replaces the seven-way corner choice with one continuous
parameter, so the distinction the data cannot support no longer has to be made.

**This does not solve the noise problem and is not claimed to.** N=2 versus N=3
remains indistinguishable. What it tests is whether, at matched concentration, a
smooth weighting beats a hard cut — and whether performance is *less sensitive*
to the parameter, which is the estimation-risk benefit.

## THE WEIGHTS

**Exponential decay in rank, over the gate:**

```
w_j  ∝  exp( −λ · j )        j = 0 … (gate size − 1), rank 0 = most preferred
                             renormalised to sum to 1 on each leg, each bar
```

**Parameterised by EFFECTIVE N, not by λ.** λ is uninterpretable and not
comparable to anything; the inverse Herfindahl is both:

```
N_eff  =  1 / Σ_j w_j²
```

**For equal weight over N names, `N_eff = N` exactly.** That is the property that
makes the comparison clean: the rank-weighted book at `N_eff = 2` is directly
comparable to the hard-cut book at `N = 2`, matched on concentration rather than
on a parameter with no shared meaning. **λ is solved for numerically at each
declared `N_eff`** and reported.

### Why rank and not score

The obvious alternative is a softmax on the composite score, `w_i ∝ exp(β·s_i)`,
which uses the size of the gap and not only the ordering.

**It is deliberately out of scope**, for two reasons: it would change two things
at once — the weighting shape *and* the use of score magnitude — and the score's
dispersion is non-stationary, so β would not mean the same thing in different
periods. **Every prior study in this programme selects on rank**, and this one
changes the weighting only. Score-weighting is the natural successor if this
works.

### Why exponential and not power or linear

A power law `(j+1)^−α` behaves similarly and would do; exponential is chosen for
one property: **constant ratio between adjacent ranks**, so the scheme has no
preferred scale and does not implicitly favour the top of the gate more at one
concentration than another. **Linear/triangular is rejected** — it reaches zero at
a finite rank, which reintroduces the hard cutoff this study exists to remove.

## THE PROBLEM THIS DESIGN HAS, STATED FIRST

**A hard-cut book trades only when a name crosses the boundary. A rank-weighted
book trades EVERY BAR, because every weight moves as ranks shuffle.** Turnover is
the binding constraint in this programme, and this design attacks it from the
wrong side.

So a **no-trade band** is a declared axis rather than a later rescue:

```
band = 0     trade to the target weights every bar
band = 0.20  trade a position only when |w_target − w_held| > 0.20 · w_target
```

**If turnover explodes without the band and the band fixes it, that is the
finding. If the band cannot fix it, the family closes on a mechanical ground and
we will know that in one run.**

## The grid

| axis | levels |
|---|---|
| **N_eff** | 2 · 3 · 5 · 7 · 10 · 14 · 19 |
| **band** | 0 · 0.20 |
| **exit** | none · target (D303's adopted rule) |

**28 cells**, plus the seven hard-cut books at matched `N` as the baseline — which
already exist from D306 and are re-run here so every number comes from one
runner.

**The overlay families are out.** D306 showed the exits separable from width and
the overlay actively harmful under concentration (−0.153 Sharpe at N=2), and
adding it would double the grid for an axis already answered.

Everything else inherited: gate 25, k = 5, the D293 triple, D303's multiplier.

## Cost, which is now measured differently and must reconcile

Turnover can no longer be counted from entries — a weight that moves from 0.30 to
0.25 is a trade with no entry. **Turnover per leg per bar is `Σ_i |Δw_i| / 2`**,
and cost is that times the held-name round trip.

**Assertion [3] holds this to D306:** on a hard-cut book the weight-change
turnover must reproduce the entry-count turnover D306 used, to floating point. If
it does not, the two studies are not measuring the same quantity and no
comparison between them is admissible.

## Statistics

**Net bp/bar and Sharpe, both primary.** Net uses each cell's own held-name round
trip, with the mean-based figure carried as the truncation artefact D302 showed
it to be. **Trimmed net — top and bottom 1% of trade contributions removed, cost
kept — is reported for every cell**, per the amended reporting rule.

**And the flatness statistic, which is the estimation-risk claim:**

```
flatness  =  ( best net over the seven levels )  −  ( worst net over the seven )
```

reported for both schemes. **A flatter curve means the choice of concentration
matters less**, which is the benefit a smooth scheme is supposed to deliver even
if its peak is no higher.

## Nulls

Each cell against the **rank-rotation null** of D300 and D306, unchanged — the
name ranked `j` is treated as rank `(j + s) mod 25`, preserving each name's rank
persistence, the gate membership and the entry rate, destroying only the
alignment between rank order and preference. 200 draws, both statistics,
BH-FDR at q = 0.10 across the grid.

## Predictions

Three are against.

| | prediction |
|---|---|
| **Q1** | **without a band, turnover at least doubles** against the hard cut at matched `N_eff` — mechanical, and if it does not the weights are not moving |
| **Q2** | the 0.20 band brings turnover to within 25% of the hard cut's |
| **Q3** | gross at matched `N_eff` is within 15% of the hard cut's — the weighting reshapes the book, it does not change the edge |
| **Q4** | **volatility at matched `N_eff` is LOWER** than the hard cut's, because a smooth weight vector is less lumpy than a 0/1 one |
| **Q5** | **the rank-weighted curve is FLATTER** — its best-minus-worst across the seven levels is under 70% of the hard cut's. *This is the estimation-risk claim and the study's actual point* |
| **Q6** | **no rank-weighted cell beats the best hard-cut cell on net.** *Against the study's motivation* — smoothing removes the need to choose, it does not add edge |
| **Q7** | **the banded cells beat the unbanded ones on net at every `N_eff`.** *Against* the idea that trading to target is worth its cost |
| **Q8** | at `N_eff = 2` the rank-weighted book holds a materially non-trivial tail — the top two names carry under 80% of the weight — so it is not the hard cut wearing a different name |

Q1 and Q5 are load-bearing. **Q1 failing means the arm is not implemented as
described; Q5 is what the study is for.**

## Decision rule, declared before the numbers

- **Q5 confirms and Q6 confirms** → the rank-weighted book is adopted as the
  *parameterisation*, not as an improvement: same expected edge, less exposed to
  a choice the data cannot make. The reported figure becomes a curve, not a peak.
- **Q5 fails** → smoothing buys nothing, the hard cut stands, and the corner
  choice is simply reported with its 1.4 sigma.
- **Q6 fails** (a rank-weighted cell beats the best hard cut) → treat with
  suspicion, not celebration: it would most likely be the same noise that put the
  hard-cut peak at N=2, and it needs its own confirmation before anything else.
- **turnover cannot be controlled by the band** → the family closes mechanically.

## Assertions

1. **[1] Nesting at the tight end.** As λ → ∞ the rank-weighted book must
   converge to the `N = 1` hard-cut book. Checked at λ = 20.
2. **[2] The scale is anchored.** `N_eff` computed from equal weights over `N`
   names must equal `N` exactly, for every `N` in the grid — this is what makes
   matched comparison meaningful.
3. **[3] Turnover reconciles.** On a hard-cut book, `Σ|Δw|/2` must reproduce
   D306's entry-count turnover to floating point.
4. **[4] Weights are a proper allocation** — non-negative, summing to 1 per leg
   per bar, and **monotone decreasing in rank**.
5. **[5] Every cell is a distinct book** — the guard D295 lacked.
6. **[6] The hard-cut baseline reproduces D306** at all seven widths, exactly.
7. **[C] Cost dimensions** against d295's published 52.1893, doubled form
   rejected.
8. **[7] The self-test raises on a deliberately broken book**, corrupting bars
   inside the mask.

## Scope

**Out:** score-weighted allocation, any change to the entry signal, the gate, `k`,
the exit thresholds, the overlay, and time-varying anything — D308 closed that on
a null and it is not reopened here.

## Files

`docs/decisions/D310-the-rank-weighted-book.md` (this record) · runner and data
to follow, in separate commits.
