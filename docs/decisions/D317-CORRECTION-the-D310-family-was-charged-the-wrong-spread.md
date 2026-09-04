# D317 — the cost basis, and how much of the width result rests on it

**Status:** CORRECTION and OPEN METHODOLOGICAL QUESTION. Bears on **D310, D311,
D312, D313, D314, D315a, D316** and on [STACK.md](../STACK.md). The affected
records are not edited; this stands beside them.
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. How this was found, and one framing corrected at the door

The principal asked me to re-check [STACK.md](../STACK.md)'s claim that nothing
after D300 was an improvement. Two things came out of it, and the second is
larger.

**A framing I used first and withdrew:** I initially wrote this up as *"D310's
pre-registration specifies a held-name round trip and its runner uses a global
median, therefore defect."* **The principal's correction is right and I accept
it: a pre-registration records the thinking before the run, not a contract the
runner is in breach of.** Reasoning moved between the two, and in this case it
moved for a *documented reason* — [D307 §1](D307-the-candidates-are-lottery-books.md)
concluded, one study earlier:

> *"any comparison of two exit rules must charge them a **common** spread or it is
> partly measuring which rule happens to trade tighter names."*

**So D310 charging one common round trip is D307's own recommendation applied.
That part is not an error.** What follows is about *which* common level, and
about an axis distinction neither record drew.

## 1. The level is below anything the book holds

D310 sets the common round trip at **4 × the universe's median half-spread =
56.98 bp**. The names the book actually weights:

| `N_eff` | weighted median half-spread | implied rt |
|--:|--:|--:|
| **2** | **18.51** | **74.06** |
| 5 | 20.31 | 81.22 |
| 10 | 22.16 | 88.65 |
| **19** | **25.05** | **100.22** |

*(corroborates D302: this audit's global median is 14.25 against D302's universe
13.20, and its widest-book weighted median 25.05 against D302's held-name 26.31)*

**No reading of D307 justifies charging the book a spread cheaper than any name
in it.** A common basis can be set at a held-name level — D302's 26.31 median, or
any of the above — and remain common. The universe's level is 30% to 76% below
what the book trades.

## 2. Under any held-based level, every cell is net-negative

| `N_eff` | **common 56.98** (D310) | **common 105.24** (D302 held) | **per-cell held** |
|--:|--:|--:|--:|
| **2** | **+4.37** | **−12.35** | **−1.54** |
| 3 | +3.41 | −12.40 | −3.25 |
| 5 | +2.07 | −12.47 | −5.24 |
| 7 | +1.23 | −12.36 | −6.52 |
| 10 | +0.43 | −12.02 | −7.74 |
| 14 | −0.24 | −11.41 | −8.87 |
| 19 | −0.87 | −10.60 | −9.59 |

**The published `none/exp2` at +4.37 is −1.54 on its own names' spread and
−12.35 on D302's held-name median.** STACK.md §0 quoted +4.37 as "the best cell";
that is wrong.

## 3. THE PART THAT MATTERS — the width conclusion's SIGN depends on the basis

Advantage of `N_eff` = 2 over `N_eff` = 19 on net:

| cost basis | N2 − N19 |
|---|--:|
| **per-cell held rt** (D300/D306's method) | **+8.04** |
| common, universe rt 56.98 (D310) | +5.25 |
| common, the N=2 book's own rt 74.06 | +2.77 |
| **common, D302 held-name rt 105.24** | **−1.75** |

**Under a common held-name round trip, the wide book wins.** The mechanism is
arithmetic: with a common `R`, the advantage is
`(gross₂ − gross₁₉) − R·(turn₂ − turn₁₉)` = `13.505 − 0.1450·R`, which crosses
zero at **R = 93.1**. The concentrated book turns over more, so raising the common
level penalises it, and the crossing sits inside the plausible range.

### The axis distinction neither record drew

**D307's common-spread rule is right for comparing EXIT RULES at fixed width**,
where one rule happening to trade tighter names is incidental to what is being
tested.

**It is the wrong rule for comparing WIDTHS**, because there the spread
difference is *caused by the choice under test* — a concentrated book genuinely
holds tighter names, genuinely pays less, and D300 counted that as a real second
benefit rather than a measurement artefact.

**So per-cell is correct on the width axis and common is correct on the exit
axis, and D310 applied the exit-axis rule to a width study.** That is an argument,
not a measurement, and **the whole width result rests on it** — which nothing in
D300, D306, D307, D310 or D314 said out loud.

## 4. D300/D306's construction is robust to the basis; D310's is not

| book | own held rt | common 105.24 | turnover |
|---|--:|--:|--:|
| **D306 `N=2 / target`** | **+15.25** | **+7.53** | 0.2410 |
| **D300 `N=2 / none`** | **+11.20** | **+7.49** | 0.2003 |
| D310 `none/exp2` | −1.54 | **−12.35** | **0.3465** |

**D300/D306's book stays net-positive under every basis tested. D310's is
net-negative under every held-based one.** The difference is turnover — 0.2003
against 0.3465, **1.73×** — because D310's rank-weighted book re-weights as ranks
move where D300's holds an entry for `k` bars.

**D310 documented that mechanism honestly.** What was never done is compare the
two constructions on net with both correctly costed. On that comparison
**D300/D306 is the better book**, and it is the one the programme should be
carrying.

## 5. What survives in D311–D316

**Their relative results survive** — every arm within each study shares one
`rt`, so the estimator A/B (D313 Q5), the rotation nulls, the arm rankings and
the corner's *location* are unaffected. **Their absolute net figures do not.**

**D314's closed form is doubly invalid**, reinforcing rather than contradicting
D315a's withdrawal of it: its cost curve `23.51 − 4.12 ln N` was fitted on the
universe basis, and the per-cell slope is about **−2.43**.

## 6. What is owed

1. **A width study on the D300/D306 construction with the basis stated and both
   readings reported.** Not "which N is best" but "which N is best, and does that
   survive the cost basis" — §3 says at present it does not.
2. **A runner assertion, in the same class as `[C]`:**

   > **`[S]` SPREAD BASIS.** The round trip charged must be computed from the
   > names the book holds or weights, must be reported per-cell *and* common, and
   > must FAIL against the universe median. `[C]` checked cost's *dimensions* and
   > never its *basis*.
3. **D300/D306 is the live construction** until D310's is re-costed and shown to
   beat it.

## 7. And the claim that prompted this is withdrawn

**"Nothing after D300 was an improvement" is wrong.** Corrected:

| study | contribution |
|---|---|
| **D303** | correctness fix — indistinguishable on mean (t −0.42), 13% smaller maxDD, 13 of 14 profitable years. Its own stated conclusion |
| **D305 arm S** | **net +1.35 bp/bar**, gross unchanged (t −0.88), and the only arm that kept the book **full** at 38 |
| **D306** | the target composes with concentration, **+11.20 → +15.25**, and **width and exits are separable** — net peaks at N=2 in all four exit configurations |
| **D307** | the target's advantage is +4.05 on own spreads and **+0.80 on a common one**, matching D305's +0.79 at N=19 — so **~+0.8 is its consistent value** |
| **D307-CORR** | the symmetric trim **preserves D306's ranking**; N=2/target best at +52.1 |

**Three improvements after D300, then six closures** — and every one of the six
tried to make width or risk vary over time.

## 8. Files

`scripts/d317_cost_basis_audit.py` · `data/d317_cost_basis_audit.json`
