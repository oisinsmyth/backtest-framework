# D306 — book width crossed with the exits

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-03
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## The question D300 left open

D300 swept `N` with **no exit rule at all** and found the book crosses breakeven
between N = 5 and N = 3, reaching **net +11.20 bp/bar at N = 2**. D305's control
gave the one clean matched pair against it: at 38 positions the profit target is
worth **+4.46 gross, +3.67 cost, +0.79 net**.

**Whether the target still adds +4.46 on a four-position book is untested**, and
there is a real mechanism for it not to. D304 and D305 established that the exit
earns by replacing names that have **drifted out** of the selected set — the
replacement premium is +29.29 bp there and +9.22 (t = 0.96) where the name is
still selected. **At N = 2 almost nothing can drift out of a two-name selection**,
so the channel the target earns through may simply not exist.

## The grid

**`N` per leg ∈ {2, 3, 5, 7, 10, 14, 19} × exit ∈ {none, target, overlay,
target + overlay} = 28 cells.**

| | |
|---|---|
| **none** | D300's arm, re-run here so every cell comes from one runner |
| **target** | D303's adopted rule: market-referenced, `cum_x ≥ 0.9627 × u_x`, flat band |
| **overlay** | D297's book-level trailing spread, X = 12, s = 0.0 |
| **target + overlay** | both |

**The principal named three of these four.** `target` alone is added because
without it the target's and the overlay's contributions cannot be separated: with
only {none, overlay, target+overlay} every difference involving the target is
measured *through* the overlay. Four cells make a 2×2 and the interaction is
readable; three make it inferable at best. Nothing else is added.

Everything else inherited: gate 25, k = 5, the D293 triple, D303's multiplier,
D297's X. **Nothing re-searched.**

## Statistics, and the trap this study must not fall into

**Sharpe is primary for every cell containing the overlay**, because the overlay
changes exposure and a mean test rejects it for being out of the market — the
error D301's null column made and D297's docstring named.

**Gross bp/bar, Sharpe, exposure and net are all reported for every cell.**

**Net is computed with each depth's OWN held-name spread**, not a single round
trip applied everywhere. D300's runner made that mistake and it understated the
concentrated cells: at N = 2 the held half-spread is 21.68 bp against N = 19's
26.67, so applying N = 19's round trip charged N = 2 about 23% too much.

**Cost for overlay cells is charged as `rt × turn × exposure` for the positions,
plus D297's switching cost for the overlay itself.** A book that is flat is not
paying to trade. This is a modelling choice, it is more favourable to the overlay
than D298's convention, and it is stated here rather than buried.

## BOTH LENSES, in all four exit configurations

FINDINGS §10 requires it where a path exists, and a path exists at every cell
here. **Each of the 28 cells is run twice:**

| lens | construction | scored |
|---|---|---|
| **path-variant** | `N` slots, pool = top `N` — the book we would trade | **bp/bar, Sharpe, net** |
| **path-invariant** | **no slot cap**, pool = top `N` — every selected name held, contention removed | **per TRADE only** |

**The invariant lens is not a tradeable book** — unbounded capital, uncontrolled
exposure — and its trade-level mean is **never quoted in bp/bar beside a real
book**. It answers *is this exit rule good at this depth*, free of the slot cap.

**Their difference is the contention drag**, reported per cell:

```
drag(N, exit) = mean trade P&L invariant  −  mean trade P&L variant
```

D304 measured this once, at N = 19 with the target: **−6.07 bp**, i.e. the cap
made the book hold the *better* names — contention is a **filter, not a tax**.
**Whether that survives concentration is the question this axis adds**, and it is
not obvious either way: at N = 2 a single stale holding occupies half the book,
so the filter has far less to discard and far more to lose.

## The null

**The rank-rotation null of D300, unchanged** — the name ranked `j` is treated as
rank `(j + s) mod 25`, preserving each name's rank persistence, the gate
membership, the held-set size and the entry rate, and destroying only the
alignment between rank order and preference. 200 draws per cell, on **both**
statistics.

**What it does and does not test, stated:** it asks whether the *ranking* carries
information at that depth under that exit rule. **It does not test the exit** —
D303 and D305 already did that against holding-run-matched nulls. A cell clearing
here means its selection beats a scrambled selection, not that its exit beats no
exit; that second comparison is the paired difference across the exit axis, which
is within-book and needs no null.

## Predictions

Three are against.

| | prediction |
|---|---|
| **Q1** | **the target's gross contribution SHRINKS as N falls**, from +4.46 at N=19 to under +2.00 at N=2 — the drifted-out channel it earns through barely exists in a two-name selection. *This is the study's actual question* |
| **Q2** | the overlay's Sharpe contribution is roughly **constant in N**, being book-level and blind to how many names are held |
| **Q3** | **net peaks at the smallest N in every one of the four exit configurations** — cost per bar is invariant to N and gross is rank-monotone, so nothing about an exit rule changes that ordering |
| **Q4** | the best net cell in the whole grid is at **N = 2 or N = 3** |
| **Q5** | **`target + overlay` does NOT beat `target` alone on net at small N.** *Against D298*, which found the combination best at N=19 — but D301 showed the overlay sits out bars averaging **+6.03 bp** once the target is on, so it is cutting positive bars, and a concentrated book has more of them |
| **Q6** | **no exit configuration changes which N is best.** *Against the premise of running the factorial at all* — if true, the exits and the width are separable and future work can optimise them independently |
| **Q7** | at N = 2 the four exit configurations differ by less than 3 bp of net, i.e. **the exit axis stops mattering once the book is concentrated** |
| **Q8** | **the contention drag turns positive as `N` falls** — negative at N=19 (D304's −6.07, the cap as a filter) and **positive at N ≤ 3**, because a stale holding occupies half a two-name book and the cap has almost nothing left to filter. *Against D304's finding generalising* |

Q1 and Q6 are load-bearing.

## Decision rule, declared before the numbers

- **Q1 confirmed and Q7 confirmed** → the exits are a wide-book artefact, the
  candidate is the concentrated book with no exit rule, and six studies of exit
  tuning are superseded rather than wrong.
- **the target holds its +4.46 at small N** → the candidate is
  `concentrated + target`, and the two levers compose.
- **the best cell needs the overlay** → then the overlay's exposure modelling
  above becomes load-bearing and must be re-derived under D298's stricter
  convention before anything is adopted.

**Nothing is adopted from this study either way.** It is a screen on mined data,
and R14's ladder is unchanged: a pre-registered out-of-sample test on a fixture
never seen is what makes a candidate.

## Assertions

D300's set carries over — bit-identity of `N=19 / none` against D303's no-exit
control, held names tracking the depth, **turnover invariant across depths**,
every cell a distinct book, the rotation moving the book while holding the entry
rate, `[C]` cost dimensions against d295's published 52.19, and a self-test that
raises on a book handed free money.

**Two this study adds:**

- **[10] The `none` arm must reproduce D300's published numbers at every depth**,
  to floating point. If it does not, the two studies are not on the same book and
  no comparison between them is admissible.
- **[11] The overlay must not change the holdings** — it scales the book's return
  series and leaves the position simulation alone, so the trade ledger of
  `target + overlay` must be **identical** to `target` at every depth. If it
  differs the overlay has been wired into the book rather than over it.

## Files

`docs/decisions/D306-book-width-crossed-with-the-exits.md` (this record) · runner
and data to follow, in separate commits.
