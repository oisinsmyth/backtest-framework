# D319 RESULT — the overlay is width-specific, and the denominator was not the problem

**Status:** RESULT. Pre-registered at `1b58f2a`, runner at `46fb42c`, both
committed before this file existed (R8).
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 1. D297 reproduces exactly, and the hump does not exist at N = 2

Overlay minus control on **gross Sharpe** — D297's own statistic — arm `own`:

| X | 6 | 8 | **10** | **11** | **12** | **13** | **14** | 16 | 18 | 20 | 25 | 30 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **N=19 / none** | −0.357 | −0.034 | **+0.115** | **+0.142** | **+0.212** | **+0.151** | **+0.161** | +0.088 | −0.029 | −0.082 | −0.060 | −0.050 |
| **N=2 / none** | −0.198 | −0.131 | −0.232 | −0.186 | **−0.153** | −0.192 | −0.208 | −0.070 | −0.083 | −0.054 | −0.035 | **−0.006** |

**At N = 19 D297's hump reproduces exactly** — positive across X ∈ [10, 16],
peaking at X = 12, and `0.512 + 0.212 = 0.724` against D297's published **+0.728**.

**At N = 2 the overlay is negative at every one of the twelve thresholds.** The
best is X = 30 at −0.006, which is the overlay effectively switched off. **There
is no hump, and D306's single cell was not a threshold artefact.**

The same holds on the `target` base: negative at all twelve.

## 2. The mechanism hypothesis is dead

I argued the overlay fails at N = 2 because its trigger divides by the book's own
trailing volatility, which D312 measured at ρ = −0.016 there against +0.347 at
N = 19 — and that D313's universe dispersion (+0.352) should repair it.

**`O_univ` is worse than `O_own` at every width**, on net Sharpe at X = 12:

```
N=2   -0.132        N=3   -0.191        N=19  -0.268
```

**Q4 falsified.** The denominator was not the problem. **Q8 confirmed only in the
sense that the damage is smallest at N = 2** — the ordering I predicted, with the
sign of the effect reversed, which makes the confirmation hollow.

**So D313's universe predictor, which genuinely forecasts book volatility better,
makes a rule that uses volatility as a scale strictly worse.** Forecasting a
quantity well and using it well are different things, and this is the second time
that distinction has bitten (FINDINGS §11's trap, arriving from the other side).

## 3. The nulls

**BH-FDR at q = 0.10 over all 144 overlay cells: NONE survive.**

The only cells below p = 0.05 anywhere are `N=19/none/own` at **X = 12 and X = 13
(p = 0.0398)** — reproducing D297's window, on a book whose net is **−8.49
bp/bar**. At N = 2 the best p is **0.1194**.

## 4. Predictions

| | prediction | outcome |
|---|---|---|
| **Q1/Q2** | reproduction and denominator harness checks | **CONFIRMED** — all six base cells and D306's overlay cell reproduce to **0.0** |
| **Q3** | `O_own` clears at no X at N=2 *(against)* | **FALSIFIED IN LETTER** — X=8 (+0.003) and X=30 (+0.015) on net Sharpe, at p = 0.244 and 0.249. §5 |
| **Q4** | `O_univ` beats `O_own` at N=2, X=12 *(for)* | **FALSIFIED** — −0.132 |
| **Q5** | neither arm beats control at N=2, any X *(against, load-bearing)* | **FALSIFIED IN LETTER** by the same two cells. §5 |
| **Q7** | best-X exposure within 10 points of 70% | **FALSIFIED** — 53% at N=2, X=8 |
| **Q8** | `univ`'s edge largest at N=2, smallest at N=19 | **CONFIRMED, hollowly** — the edge is negative everywhere |

## 5. Q3 and Q5 carry the same wording defect for the THIRD time

Both are falsified by two cells whose margins are **+0.003 and +0.015 net
Sharpe**, at **p ≈ 0.24**, failing BH.

**D313's record identified this exact defect and stated the fix**: *"'does not
beat' means does not beat WHILE BEING PROFITABLE AND SURVIVING ITS OWN NULL. A
cell that beats the baseline by losing less does not falsify it."* **I wrote
D319's Q5 without that clause.** Third occurrence, after D313's Q3 and D315's QB2
(which never ran).

**Under the intended wording both Q3 and Q5 CONFIRM**, since nothing at N = 2
reaches p < 0.05 let alone survives BH.

**I am not resolving that by choosing the reading I prefer.** Both are on the
record. My recommendation is to read them as confirmed and close, because a
+0.003 Sharpe margin at p = 0.24 is not a finding under any standard this
programme has used — and because §1's gross-Sharpe sweep, which has no such
ambiguity, is negative at all twelve thresholds.

## 6. And a reframing of D297 that the cost basis exposes

**D297's celebrated +0.728 is a GROSS Sharpe on the N = 19 book, and that book
nets −15.51 bp/bar.** D297 charged only the overlay's own transition cost, which
is correct for a de-risking comparison on a fixed book — position cost is common
to both arms — but it means the number was never a net figure.

**The overlay has never operated on a profitable book.** It improves a losing
book's gross Sharpe by +0.212 and leaves it losing 8.49 bp/bar.

## 7. What this closes

**The overlay is width-specific and it is closed at the operating point.** It
helps a wide book, which loses money, and hurts a concentrated one, which makes
money. **The programme's largest Sharpe effect is unavailable where the book
actually runs**, and the reason is not its volatility denominator.

**The stack is unchanged:**

```
signal        the D293 confluence          min z +2.58 across three nulls
construction  factor-neutral spread        removes -mu - sigma^2
width         N_eff = 2, FIXED             +21 bp over N=19, basis-immune
exit          the target, or nothing       +0.69 bp/bar
overlay       CLOSED at this width         negative at all 12 thresholds
```

**Next: B, the tilt filters** — D304's unrun study, with the price-matched control
and the persistence-matched random exclusion, carrying `[S]`.

## 8. Assertions

All eight pass, and two are worth naming.

| | |
|---|---|
| **[1]** | all six base cells reproduce D306's gross **and** net to **0.0**, and `schedule_ext` is **identical** to D297's when handed the same denominator — the arms differ in one thing |
| **[1c]** | D306's published `N=19/none+overlay` reproduces to **0.0** — the overlay path is the same one |
| **[2]** | **causality** — both arms read only `t−1`, and both audits fail when the lag is removed |
| **[3]** | the universe series is the one D312 published |
| **[4]** | **rewritten before commit.** It contained `assert ... or True`, which cannot fail. It now asserts that tightening X from 30 to 8 raises firings **12 → 70**, transition cost **0.19 → 1.10**, and cuts exposure **94% → 55%** |
| **[S]** | **SPREAD BASIS, carried for the first time and owed since D317** — held round trips 86.7 / 91.3 / 106.7 against the universe's 57.0, and the check **rejects** the universe basis rather than reporting it |
| **[C]** | cost dimensions reproduce d295's 52.1893; the doubled form is rejected |
| **[7]** | [1] raises on a book handed free money inside the mask |

## 9. Files

`data/d319_overlay_concentration.json` ·
`scripts/run_d319_overlay_concentration.py`
