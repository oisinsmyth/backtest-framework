# The stack, signal to present

**What each layer actually contributed, which contributions are measurable, and
where the next one should go.** Written 2026-09-04, after D315a.

> ## CORRECTION, 2026-09-04, same day — §3 applied the wrong bar
>
> **The principal challenged §3's "decoration" verdict: the standard here is
> beating your own pre-registered matched null, with an out-of-sample test as a
> separate later gate. That is correct and §3 did not apply it.** §3 invented a
> *paired difference between books*, applied it retrospectively to components
> that were never scored that way, and read every non-significant result as a
> null result. Two things are wrong with that.
>
> **1. The paired test is structurally blind at the operating point.** Minimum
> detectable effect, against a book whose entire net is **+4.37 bp/bar**:
>
> | comparison | diff | t | **MDE** | 95% CI |
> |---|--:|--:|--:|---|
> | the target, at N_eff = 2 | +1.56 | +0.17 | **18.3** | [−16.3, +19.4] |
> | `hard` vs `exp`, at N_eff = 2 | +3.84 | +0.70 | **11.0** | [−6.9, +14.6] |
>
> **The MDE is 2.5× to 4.2× the whole book's net.** No component that could
> exist would register. Those `t` values are a statement about the test's
> resolution, not about the components. **Absence of evidence, read as evidence
> of absence.**
>
> **2. The components DID clear the programme's standard, and §3 omitted it.**
>
> | component | its own matched null | study |
> |---|---|---|
> | the confluence signal | min z **+2.58** across three nulls | D293 |
> | **the exit target** | **+4.95 bp/bar, t +2.58, p = 0.0050** vs a rate- and persistence-matched null (p50 +1.49, p95 +3.11) | **D295** |
> | concentration | p = **0.0050** at every depth vs rank rotation | D300 |
>
> **The target is not decoration. It cleared the bar this programme actually
> uses, and nothing since has overturned it** — D307 discounted its *net*
> advantage as a round-trip measurement artefact, which is a statement about cost
> accounting, not about the rule.
>
> **What genuinely closed still stands**, because those six studies failed their
> *own pre-registered* tests rather than a bar invented afterwards: D299, D308,
> D311, D312, D313 and D315a. **All six varied width or risk OVER TIME. None
> removed a component already in the book.**
>
> **The one thing §3's test does establish** is where it has power. MDE falls to
> **3.4–4.3 bp at N_eff = 19**, and there the target is bounded to
> **[−3.9, +2.7]** — small. **And the resolution limit is itself the finding:
> this fixture cannot separate components at the operating point, which is a
> reason to spend the next study on a big effect rather than a refinement.** That
> conclusion in §5 survives; the route §3 took to it does not.
>
> §3 is left standing below, uncorrected in place, so the error is legible.

Every number here names its study. Companion to
[FINDINGS.md](FINDINGS.md) (substantive results) and
[decisions/](decisions/README.md) (one call each).
**[PICKUP.md](../PICKUP.md) is stale** — last updated 2026-09-02, before the
whole D285→D315 spread programme.

---

## 0. The one-line state

**The book makes money and is nowhere near tradeable.**

```
best cell   none/exp2      +4.37 bp/bar net      net Sharpe +0.089
            gross +24.12   cost 19.74            gross Sharpe +0.491
            round trip 57.0 bp   breakeven 69.6 bp
```

**Cost takes 82% of gross.** Gross Sharpe peaks at **+0.693** (N_eff = 10) and
net Sharpe there is **+0.020**. That gap is the whole problem and it has been the
whole problem since D264.

---

## 1. The stack, layer by layer

| # | layer | study | what it bought | measurable? |
|---|---|---|---|:--|
| 1 | **the universe** | D256 | 1,573 single names, 35.7% dead, ragged, per-symbol pre-live screen | n/a |
| 2 | **spread, not direction** | **D285** | removes the `−μ − σ²` tax that killed 8 prior constructions | **decisive** |
| 3 | **the confluence signal** | D290, **D293** | +61.91 bp/trade at N=25/k=5, t +3.80, min z **+2.58** across three nulls | **decisive** |
| 4 | the market-referenced exit | D303 | adopted on **correctness**, not performance | **no** — −0.49 bp, t −0.42 |
| 5 | **concentration** | **D300** | gross ×3.79 from N=19→N=2 at *constant* turnover | **directionally** |
| 6 | the exit target | D295, D306 | carried as base ever since | **no** — +1.56 bp, t +0.17 |
| 7 | weight shape | D310 | `hard` vs `exp` at fixed `N_eff` | **no** — +3.84 bp, t +0.70 |
| 8 | variable width | D299, D308, D311 | three constructions | **no** — all closed |
| 9 | vol-targeted width | D312, D313 | two constructions | **no** — all closed |
| 10 | width below the corner | D315a | seven widths never run | **no** — +0.36 bp, t +0.12 |

**Layers 2, 3 and 5 are the strategy. Layers 4 and 6–10 are decoration** — every
one of them measured, and every one inside the noise.

---

## 2. What is load-bearing

### Edge 1 — the spread construction is the single largest step ever taken

Not a marginal gain. It is the difference between **losing at zero cost** and
making money:

```
D279  S1_short|top25   −0.432 gross Sharpe   at zero fees, zero borrow, zero rf
D282  short every name overnight   −21.92% CAGR
D285  factor-neutral: the long leg gains what the short leg loses; −μ cancels
```

Eight constructions across five universes and two frequencies failed before this
change. None has failed the same way since.

### Edge 2 — the ranking has real cross-sectional content

**This is the only thing in the programme that is decisive against a null.**

- D293: min z **+2.58** across rotation, permutation and tail-randomised nulls,
  beating `hist_L` alone head-to-head on the same grid (+2.58 vs +1.60).
- D300: every depth clears BH-FDR at q = 0.10 against a rank rotation, sorted
  p from **0.0050**.
- D315a: all eight widths at the enumeration floor **p = 0.0400**, all surviving
  BH.

### Edge 3 — concentration, directionally

**Cost per bar is invariant to `N`** — turnover 0.2003 at every depth, spread
0.0000 — **while gross rises 3.79×** as the book concentrates (D300). It is what
carries the book across breakeven, and it fixes the price tilt for free: median
held price **$23.72 → $75.95**, half-spread **26.67 → 21.68 bp**.

**Bounded by D314/D315a:** with ρ ≈ 0, `Sharpe = √N·net/σ`, and the optimum is a
**corner at N_eff = 2** on a surface now measured from 1.00 to 25.00.

---

## 3. What is decoration — every lever, measured pairwise

These books share every bar and correlate at 0.92–0.999, so the paired per-bar
difference is the right statistic (D303's argument) and ranking the table is not.

| lever | best effect | **t** | source |
|---|--:|--:|---|
| the exit target | +1.56 bp | **+0.17** | D316 |
| weight shape, `hard` vs `exp` | +3.84 bp | **+0.70** | D316 |
| width, N=2 vs N=5 | +2.31 bp | **+0.36** | D315a |
| width below 2 (best, 1.45) | +0.36 bp | **+0.12** | D315a |
| the market reference | −0.49 bp | **−0.42** | D303 |
| variable width | — | 5 studies, none survives | D299/308/311/312/313 |

> **The differences BETWEEN books are all inside the noise. Only the difference
> between a book and a scrambled ranking is decisive.**

That is the single most useful sentence in this document, and it took until D316
to state it, because each lever was scored against a null rather than against
the book it was supposed to improve.

---

## 4. Why the stack stopped improving

**Every lever since D300 attacked the book's SHAPE** — width, weights, exits,
timing, risk targeting. **D314's algebra says why that was doomed.**

```
rho = 0.0020        so  vol(N) = sigma/sqrt(N)      (verified at N=1: 1,089 vs 1,095)
net(N) = 5.96 - 2.38 ln N    the edge dilutes 1.58x faster than the cost falls
Sharpe = sqrt(N) * net(N) / sigma       =>   the optimum is a CORNER
```

**A rule that varies N can only move away from a corner.** Five variable-width
studies were five ways of leaving it, and D315a confirmed the corner by direct
measurement. **There is no shape improvement left to find.**

---

## 5. Where the next improvement goes

**Two untouched surfaces. Both attack the binding constraint — cost against
gross — rather than the shape.**

### A. The entry signal — frozen since D293, and it is the gross input

**Six width studies varied how much of the book to hold. None has varied what
goes into it.** Gross is the numerator of every ratio above; a 20% better signal
moves net Sharpe further than everything in §3 combined, because everything in §3
moved it by nothing.

### B. The cost side — and one specific lever was planned and never run

**D304's tilt filters.** [D300's amendment](decisions/D300-AMENDMENT-cost-basis-and-what-D304-and-D305-changed.md)
says *"D304's tilt study is the next one on the list, and D300 generates its
baseline"* — then the D304 slot was spent on `d304_two_lenses.py`, a different
question, and the tilt arm was never run.

**The evidence is already collected and it is unusually specific:**

| | |
|---|---|
| D302 | held names' median half-spread **26.31 bp** against the universe's **13.20 bp** |
| D300 | concentration alone moved held price **$23.72 → $75.95** and half-spread **26.67 → 21.68 bp** |
| D264 | commission per bp ran **0.20 bp (RH) to 4.15 bp (CLF)** *inside one volatility stratum* — a **price** effect, not a liquidity one |

**The book pays roughly twice the universe's spread because short-term reversal
selects cheap names** — which is exactly the mechanism D285's own
pre-registration named as the documented reason this effect usually dies, and it
has never been tested here.

### Recommendation: B first

Cost is the binding constraint, the baseline exists from D300, the mechanism is
documented rather than hoped for, and it is a small study. **A is larger and more
open-ended**, and it is where the ceiling actually is.

**Mandatory control on B, and it is not optional:** [D284](decisions/D284-the-overnight-long.md)
died of discovering the **price level** rather than a filter. A filter that
improves cost by holding pricier names has found the price level, not a filter.
**Price-matched control, and a persistent random exclusion matched on count *and*
persistence** — a per-bar random exclusion churns where the treatment persists,
the defect that voided D291's veto arm.

---

## 6. What this document does not claim

- **Nothing here is promoted.** [BOOK.md](BOOK.md) and [BOOK_PROP.md](BOOK_PROP.md)
  are unchanged; the prop book remains empty.
- **Holdout reads spent: 0. Programme total: 0.**
- Every paired t in §3 is **post-hoc** — computed after the studies that produced
  the cells. They are the right statistic and they were not pre-registered.
