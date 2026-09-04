# D314 — the algebra of width, and one explanation for five closed studies

**Status:** **DERIVATION.** Descriptive fits to already-published cells. **Not a
study, not pre-registered, and it scores no book.** Any rule derived from it
needs its own pre-registration — see D315.
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. Why this exists

Five studies have tried to vary book width — D299's ladder, D308's discrete
width, D311's continuous λ, D312's vol target, D313's universe-conditioned vol
target — and all five closed. **Each close was written as though it had its own
reason.** The principal asked whether the answer could be derived from the
mathematics of how the book makes money rather than searched for.

**It can, and the five studies have one reason between them.**

## 1. Three curves, fitted to all sixteen widths

`data/d314_width_algebra.json` · `scripts/d314_width_algebra.py`

| | fit | R² |
|---|---|--:|
| **diversification** | `vol(N)² = 2,396 + 1,201,745 / N` | **0.9994** |
| **dilution** | `gross(N) = 29.47 − 6.50 · ln N` | 0.9774 |
| **turnover** | `cost(N) = 23.51 − 4.12 · ln N` | 0.9522 |

### The first line is the one that matters

`vol² = a + b/N` is the textbook decomposition: `a` is the systematic variance no
amount of widening removes, `b/N` the idiosyncratic part that diversifies away.
It implies an average pairwise correlation

```
rho = a/(a+b) = 0.0020
```

**and it is statistically zero** — fitting on N ≤ 10 alone returns −0.0053.
Implied single-name spread vol σ ≈ **1,097 bp**; the systematic floor `σ√ρ` is
**49 bp** against **237 bp** at the widest width ever tested.

**The names in this book are essentially uncorrelated, so `vol(N) = σ/√N` almost
exactly, and the book is nowhere near its diversification floor.** That is a
consequence of it being a *spread* book — D297 measured the market at 6.1% of a
held position's variance, and the long/short construction nets out most of even
that.

### The second and third give the whole economics in one line

```
net(N) = gross(N) − cost(N) = 5.96 − 2.38 · ln N
```

**The edge dilutes 1.58× faster than the cost falls** (6.50 against 4.12). That
single ratio is why net is monotone *down* in width at every width in every
study, and it is a property of the signal's rank decay against the weight-drift
turnover — not of any exit, gate or parameter that has been varied.

## 2. Sharpe collapses to one term, and the optimum is closed-form

With ρ ≈ 0:

```
Sharpe(N) = net(N) / vol(N) = √N · net(N) / σ
```

Maximising `√N · net(N)` where `net = n0 + n1 ln N`:

```
d/dN [ √N (n0 + n1 ln N) ] = 0   ⟹   net(N) = −2N · net′(N)
                                 ⟹   ln N* = −n0/n1 − 2
```

```
n0 = 5.964    n1 = −2.377    ⟹    ln N* = 0.509    ⟹    N* = 1.66
```

**The grid floor is N_eff = 2. The optimum lies below it.** Numerically,
`√N · net(N)` peaks at the floor:

```
N=2.0  +6.183      N=3.0  +5.896      N=5.0  +4.617      N=10  +1.350
N=2.5  +6.117      N=4.0  +5.296      N=7.0  +3.238      N=19  −3.813
```

### It is not an artefact of one point

| subset | n0 | n1 | −n0/n1 | **N\*** | R² |
|---|--:|--:|--:|--:|--:|
| all 16 | 5.964 | −2.377 | 2.509 | **1.66** | 0.9951 |
| drop N=25 | 5.889 | −2.329 | 2.528 | **1.70** | 0.9975 |
| drop N≥20 | 5.926 | −2.355 | 2.517 | **1.68** | 0.9971 |
| N ≤ 10 | 6.123 | −2.502 | 2.447 | **1.56** | 0.9993 |
| N ≤ 5 | 6.165 | −2.537 | 2.430 | **1.54** | 0.9991 |
| N ≥ 5 | 5.733 | −2.291 | 2.503 | **1.65** | 0.9863 |

**N\* spans 1.54 to 1.70 and sits below the grid floor in every subset.** N=25 is
the whole gate, where the exponential weights flatten completely and gross drops
9.11 → 6.00; dropping it moves N\* by 0.04.

## 3. What this explains

**The Sharpe-optimal width is a CORNER SOLUTION at the tightest width the grid
can express.** A rule that varies N can only move *away* from a corner, and
moving away from a corner can only hurt.

**That is one explanation for five closed studies.** D299, D308, D311, D312 and
D313 were not five independent failures of five different mechanisms. They were
five ways of leaving a corner.

It also retro-explains details each study reported without connecting:

- **D312's B@N2 sat pinned at the most concentrated level for 80.6% of bars.** It
  was pinned against the corner.
- **D311's oracle gain was reproduced 100–124% by noise.** There was no interior
  optimum for the oracle to find.
- **D313's arm B raised gross at N=10 and N=19 and still lost.** Moving toward
  the corner from a wide start helps; it cannot help past the corner.

## 4. What N *should* vary with, if anything

Write `gross = σ · ĝ(N)` — edge scales with volatility — while cost does not:

```
Sharpe(N) = √N · ( ĝ(N) − cost(N)/σ )
```

**σ cancels except through `cost/σ`.** The optimal width moves with the
**cost-to-opportunity ratio**, never with the volatility level itself.

**A vol target varies N with σ(t) directly. The algebra says that is the wrong
argument** — and it predicts D312 and D313 fail, before either was run.

The sensitivity is real rather than theoretical:

```
opportunity × 0.5   →   best N_eff = 2
opportunity × 1.0   →   best N_eff = 2
opportunity × 2.0   →   best N_eff = 8
```

And the derived rule has **no free parameters**:

```
ln N*(t) = −n0(t)/n1(t) − 2
```

so the entire question of whether width should vary reduces to **how often
−n0(t)/n1(t) rises above ln 2 + 2 = 2.693.** It currently sits at **2.509**.

## 5. Caveats, stated up front

1. **These are descriptive fits, not a model with standard errors on N\*.** The
   log-linear forms hold at R² 0.95–0.98 for gross and cost; the variance
   decomposition at 0.9994. No confidence interval on N\* is claimed.
2. **N\* = 1.66 is an extrapolation below every width ever run.** The fits are
   estimated on N ∈ [2, 25] and the optimum is outside that range. **The correct
   statement is "the optimum is at or below 2", and D315 tests it directly.**
3. **ρ ≈ 0 is what makes `Sharpe ∝ √N · net` exact.** At a much wider book, or on
   a long-only book, the `a` term would bind and this algebra would not hold.
4. **Cost is the median-based round trip** (D302), 57.0 bp, held constant across
   widths. D300 measured cost/bar as invariant to N in *rate* terms; the held
   names' spread does vary with width and that variation is not in these fits.
5. **This uses the `none` family with no exits.** D306 showed width and exits
   separable, so the curves should carry, but that is an inherited claim.

## 6. Files

`scripts/d314_width_algebra.py` · `data/d314_width_algebra.json`.
Pre-registration of the two tests it implies: **D315**.
