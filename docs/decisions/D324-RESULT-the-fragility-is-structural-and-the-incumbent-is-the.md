# D324 RESULT — the fragility is structural, and the incumbent is the least fragile of the four

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D324-RESULT-the-fragility-is-structural-and-the-incumbent-is-the-least-fragile.md`. The H1 above is the full title.*

**Status:** RESULT. Pre-registered at `5544e7c`, runner at `e75d97d`, both
committed before this file existed (R8).
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is promoted. All five predictions confirm.**

---

## 1. Q2 confirms — no candidate is healthier on both declared statistics

At the **matched** cell (k = 10, dv28 off), with the two statistics declared
before the numbers:

| cell | trades | names | **NAMES/HALF** | **LOW-PRICE SHARE** | top-10 | netSHRP |
|---|--:|--:|--:|--:|--:|--:|
| **incumbent** | 1,828 | 607 | **3** | **51.5%** | 77.5% | +0.454 |
| retrace_leg | 2,047 | 889 | 6 | 76.5% | 65.8% | +0.211 |
| rev_21 | 1,947 | 649 | 6 | 76.4% | 69.3% | +0.498 |
| rsi | 2,049 | 880 | 6 | **89.4%** | 67.3% | +0.481 |

**Every candidate beats the incumbent on the PRIMARY statistic — 6 names to half
the P&L against 3 — and every one is far worse on the SECONDARY.**

**This is the opposite of what the study was hoping for**, and declaring both
statistics in advance is what makes it readable. A composite score would have
blended a 2× improvement in name spread against a 25-to-38-point deterioration in
price dependence and produced a number nobody could interpret.

## 2. The finding nobody was looking for: the incumbent is the LEAST price-dependent

```
share of P&L in the cheapest price tercile, matched cell

  incumbent (confluence)   51.5%
  rev_21                   76.4%
  retrace_leg              76.5%
  rsi                      89.4%      <- one of the confluence's own pair members
```

**`rsi` puts 89.4% of its P&L in the cheapest third of names.** It is one of the
two signals the confluence re-ranks on, and on its own it is the most
price-dependent book in the study.

**So the confluence dilutes the price concentration of its own components.**
D293 chose it because it beat `hist_L` head-to-head on `t`; D323 showed it beats
`hist_L` by +0.287 at the operating point; **and this is a third reason to keep it
that nobody selected for.**

Given D322's finding that the low tercile costs **7.01 bp round trip against 0.87**
in the top, a book at 51.5% is materially more robust to a cost shock than one at
89.4%, at the same Sharpe.

## 3. And a cost to D323's "free" k = 10

D323 found k = 10 beats k = 5 by +0.12 net Sharpe and called it unclaimed.
**It is not free:**

| incumbent | names to half P&L | era first half |
|---|--:|--:|
| k = 5 (D322) | **6** | 50.5% |
| k = 10 | **3** | **34.9%** |

**Halving the number of names that carry half the P&L, and unbalancing the era
split**, buys that +0.12. The pre-registered `k = 10` test now has a second thing
to weigh, and it should not be adopted on Sharpe alone.

## 4. Q3, Q4, Q6, Q7 — the fragility is structural

- **Q3 CONFIRMED.** Every candidate puts **> 45%** of P&L in the low-price
  tercile — range 51.5% to 89.4%. **The price dependence is a property of the
  book, not of the signal.** No candidate on this shortlist fixes it.
- **Q4 CONFIRMED.** Every matched cell needs **≤ 6 names** for half the P&L.
  Extreme name concentration is structural too.
- **Q6 CONFIRMED everywhere.** Dead names are more profitable per trade than alive
  ones in all six cells — +290.7 against +148.9 for `retrace_leg`, +183.5 against
  +54.5 for the incumbent. **No candidate has a survivorship problem.**
- **Q7 CONFIRMED everywhere.** The mean sits below the median in all six cells,
  so the two-sided fat tail is book-level, and the symmetric trims are all
  strongly positive (+48.03 to +123.19).

## 5. What the own-best cells add

| cell | netSHRP | names/half | low-price | win rate | payoff | era 1st |
|---|--:|--:|--:|--:|--:|--:|
| retrace_leg k=40 | **+0.557** | 4 | 65.7% | **80.6%** | **0.394** | 47.8% |
| incumbent k=10 dv28 | +0.549 | 4 | 64.8% | 61.5% | 0.832 | 49.1% |
| rev_21 k=10 | +0.498 | 6 | 76.4% | 62.8% | 0.754 | 59.1% |
| rsi k=10 | +0.481 | 6 | 89.4% | 63.4% | 0.775 | 73.0% |

**`retrace_leg` at k=40 is a different animal** — an 80.6% win rate with a payoff
of 0.394, so many small wins against few large losses. That is the opposite
profile to the incumbent's 61.5% / 0.832 and it carries a different tail risk,
which a Sharpe of +0.557 against +0.549 does not express.

**`rsi`'s era split is 73.0% first half** — its edge is concentrated in the early
sample, which the incumbent's 49.1% is not.

## 6. Predictions

| | prediction | outcome |
|---|---|---|
| **Q1** | reproduction | **CONFIRMED** — group 2 to 0.0e+00, group 3's names-to-half and low-price share exactly, and every candidate's D323 gross to 0.0e+00 |
| **Q2** | **no candidate healthier on BOTH** *(against, load-bearing)* | **CONFIRMED** — better on the primary, worse on the secondary, all four |
| **Q3** | price dependence is book-level *(against the hope)* | **CONFIRMED** — 51.5% to 89.4% |
| **Q4** | name concentration is book-level *(against)* | **CONFIRMED** — ≤ 6 everywhere |
| **Q6** | dead ≥ alive everywhere | **CONFIRMED** |
| **Q7** | mean below median everywhere | **CONFIRMED** |

## 7. `[S]` was wrong twice, and the second failure is a finding

I first asserted the held round trip **exceeds** the universe median — which every
earlier study could assert, because every book they scored was dearer than the
universe. **It fails here, correctly:** dv28 filters to high-dollar-volume names,
so the incumbent's dv28 cell holds names **tighter** than the universe and lands
within **3%** of it.

I then asserted it must **differ** from the universe by 5%, which failed for the
same real reason. **Both forms assert a property of the DATA, not of the code.**
What a basis test must catch is a hard-coded constant, so it now checks each
cell's rt equals 4× its own held-name median **and** that the rt spans **37%**
across cells.

**The failure is worth keeping: dv28 takes the incumbent's held round trip
essentially to the universe average.**

## 8. Where this leaves the direction

**The entry axis closes for a reason that is not Sharpe.** Four candidates within
0.08 of each other on net Sharpe, and **none of them fixes either fragility** —
every one needs ≤ 6 names for half its P&L and puts more than half its P&L in the
cheapest third of the market.

**The incumbent survives the comparison and is strengthened by it**, being the
least price-dependent of the four by 25 points.

**What this does NOT establish** is that the fragility is a property of the
*strategy* rather than of the *fixture*. Every book here is 2 names a leg drawn
from the same 25-name gate over the same 3,187 bars. **Six names carrying half the
P&L may be what a two-name book on a 1,573-name panel looks like**, and nothing
tested so far could tell the difference.

**That question is the one worth asking next, and it is not a signal question.**

## 9. Files

`data/d324_composition.json` · `scripts/run_d324_composition.py`
