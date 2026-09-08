# D394 ADDENDUM 2 — a clairvoyant left-tail filter WOULD work; nothing observable at entry distinguishes the left tail from the right

**Status:** ADDENDUM 2. **DESCRIPTIVE** — no null, no hurdle, nothing selected, fitted or admitted
(R15). **Nothing is closed: only the principal closes an avenue.**
**Date:** 2026-09-08 · Runner: `scripts/run_d394_oracle_tail.py` · Artifact:
`data/d394_oracle_tail.json` · **Holdout reads: 0.**

---

## 0. Why this was run instead of another stop

A stop loss does not remove the left tail — **it relocates it.** Stopping at −500 bp turns a −1,386
trade into a −500 trade **and** turns a trade that would have recovered to +200 into a −500 trade.

**And this construction is a reversal strategy**: it buys names under sustained selling *because
they revert*. **A stop sells the names whose reversal has not happened yet — it is anti-correlated
with the strategy's own thesis.** That is why D394 found every stop level made things worse
(−5.65, −3.67, −3.67) rather than merely failing to help.

**So the operation of interest is an ENTRY FILTER, not an exit rule.** This measures the bound on
that idea before any filter is designed.

---

## 1. THE ORACLE BOUND — and it is NOT the obstacle

Remove the worst k% of trades **with perfect foresight**. No real filter can beat this.
**The bar is the measured round trip**, because removing trades does not change cost per trade.

| drop | cap 5 (bar **61.48**) | covers? | cap 20 (bar **61.19**) | covers? |
|--:|--:|---|--:|---|
| 1% | +25.38 | no | +60.29 | **just short** |
| 2% | +37.98 | no | **+85.13** | **YES** |
| **5%** | **+65.79** | **YES** | +142.41 | YES |
| 10% | +100.47 | YES | +216.97 | YES |
| 25% | +183.81 | YES | +399.26 | YES |

> **A clairvoyant filter needs to avoid only the worst 5% of cap-5 trades — or the worst 2% at
> cap 20 — to cover costs.** The left-tail direction is **not** closed by arithmetic. That is a
> genuinely different answer from the exit-rule grid, where nothing came within 5× of the bar.

**The symmetric trim, reported beside it, shows why:** trimming *both* tails leaves +3.92 falling to
+2.00 at cap 5. **The edge is in the difference between the tails, not in the body.**

---

## 2. THE ACTUAL OBSTACLE — every observable predicts BOTH tails equally

A filter is only useful if it separates the left tail from the right one. Filtering out
"dangerous" names removes both, and at a payoff of **1.024** that removes near-equal amounts.

**P(bottom decile) and P(top decile) by tercile of each entry-time observable, cap 5:**

| observable | P(left) spread | P(right) spread | **asymmetry** |
|---|--:|--:|--:|
| `up_run_21` (the score) | 0.3 pp | 1.0 pp | **−0.7** |
| `rsi` | 1.4 pp | 2.1 pp | **−0.7** |
| `rev_21` | 4.4 pp | 4.8 pp | **−0.4** |
| **`rvol21`** | **10.6 pp** | **10.1 pp** | **+0.6** |
| price | 4.7 pp | 4.1 pp | **+0.6** |

> **`rvol21` is a powerful predictor of the left tail — P(bottom decile) runs 5.4% → 16.1% across
> its terciles. It is an equally powerful predictor of the right tail, 5.9% → 15.9%.**
> **That is what volatility IS.** Asymmetry: +0.6 pp. Nothing.

**And at cap 20 it is worse than nothing.** `rvol21`'s asymmetry is **−2.6 pp** — the high-vol
tercile is *more* likely to produce a top-decile trade (17.7%) than a bottom-decile one (15.9%) —
**and it carries a mean of +66.79 against the low-vol tercile's +0.70.**

> **Filtering out the volatile names would remove the only cohort that earns anything.**

The same holds on price: the cheap tercile has the fattest left tail *and* the highest mean
(+56.68 at cap 20), which is [Addendum 6](D393-ADDENDUM-6-the-ten-cells-and-the-price-split.md)'s
finding arriving by a second route.

**Cutting the left tail with any of these costs more than it saves:** filtering to low-vol names at
cap 5 cuts P(left) from 10% to 5.4% and lifts the mean only **+4.72 → +6.15**.

---

## 3. What this hands the next attempt — a criterion, not a verdict

**Five observables is not a search of the space, and this closes nothing.** What it does establish
is the bar any candidate filter must clear:

> **A filter must be scored on ASYMMETRY — `spread_left − spread_right` — not on how well it
> predicts losses. Predicting losses is easy; volatility does it at 10.6 pp. It is useless, because
> it predicts gains just as well.**

**Where asymmetry could plausibly exist** — untested, and each would need its own pre-registration
(D289's fourth amendment):

1. **Genuinely one-sided events.** A failed deal or a bankruptcy filing is a crash with no mirror.
   F0 already removes announced deals; distress proximity is not tested.
2. **Structural bounds.** A trade's loss is bounded at −100% while its gain is not, so the
   *conditional* shape may be asymmetric even where tail *probability* is not.
3. **Anything the D392 atlas already prices** is likely a base-rate effect rather than an
   asymmetry, and should be checked against its conditional floor before being believed.

**What is now known not to work:** the score itself, `rsi`, `rev_21`, `rvol21` and price.

---

## 4. What this does NOT say

- **It does not close the left-tail avenue (R15).** It measures five observables on one ledger.
- **It admits nothing and proposes no construction.** Any filter found asymmetric would be a new
  construction needing its own pre-registration and its own nulls — and would change the sample,
  re-opening all four of D393's nulls at a +0.91 bp binding margin.
- **The oracle bound is not achievable.** It is a ceiling computed with future information, quoted
  to show the target is not absurd — **not a result.**

---

**Status footer.** Descriptive. No null, no holdout read, nothing admitted, nothing retired.
`docs/BOOK.md` holds S1 and S2, neither at capital; `docs/BOOK_PROP.md` is empty.
