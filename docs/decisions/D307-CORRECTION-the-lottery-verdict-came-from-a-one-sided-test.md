# D307 CORRECTION — the lottery verdict came from a one-sided test

**Status:** CORRECTION to `D307-the-candidates-are-lottery-books.md`. The record
is not edited; this stands beside it, and **its title is now wrong.**
**Date:** 2026-09-03
**Area:** Strategy research · **personal track**

**Holdout reads spent: 0.**

---

## What is wrong

D307 called all four candidates **lottery books** on the strength of one number —
the mean after dropping the best 1% of trades — and concluded that *"three of the
four lose money without their best 1%."*

**That test is one-sided, and these distributions are fat on both sides.** Applied
alone it produces the verdict rather than measuring it.

**The tell was in D307's own table and I did not read it:** at N=2/target the
mean is **+68.1** and the median is **+94.4**. A mean below its median is not the
signature of a book carried by a few big winners.

## Both tails, measured

| cell | mean | median | ex-top-1% | **ex-bottom-1%** | **trimmed 1%** |
|---|--:|--:|--:|--:|--:|
| N=2 / target | +68.1 | +94.4 | +2.5 | **+117.8** | **+52.1** |
| N=3 / target | +54.2 | +92.1 | −2.0 | +104.1 | **+47.9** |
| N=5 / none | +41.1 | +18.7 | −13.4 | +85.0 | **+30.5** |
| N=7 / none | +34.1 | +18.4 | −20.2 | +78.8 | **+24.4** |
| N=19 / target | +24.2 | +107.6 | −14.9 | +68.5 | **+29.5** |
| N=19 / none | +18.7 | +11.6 | −31.7 | +64.8 | **+14.2** |

| cell | top 1% share | **bottom 1% share** | top 1% mean | bottom 1% mean |
|---|--:|--:|--:|--:|
| N=2 / target | +96% | **−71%** | +6,708 | −4,966 |
| N=3 / target | +104% | −90% | +5,631 | −4,907 |
| N=5 / none | +132% | −105% | +5,493 | −4,357 |
| N=7 / none | +159% | −129% | +5,423 | −4,398 |
| **N=19 / target** | +161% | **−181%** | +3,892 | −4,369 |
| N=19 / none | +268% | −242% | +5,019 | −4,539 |

**At the incumbent depth the losing tail is LARGER than the winning one** —
−181% against +161%. The one-sided test says that book is carried by its winners;
the two-sided test says it is dragged down by its losers.

## The corrected reading

**The symmetric trim is strongly positive at every depth**, and it preserves
D306's ranking:

```
N=2/target  +52.1  >  N=3/target  +47.9  >  N=5/none  +30.5
            >  N=19/target  +29.5  >  N=7/none  +24.4  >  N=19/none  +14.2
```

**Concentration still wins on the trimmed statistic.** The central mass of trades
is profitable at every depth, and more profitable the more concentrated the book.

**Net effect of the two tails on the mean:**

| cell | dropping winners | dropping losers | **net** |
|---|--:|--:|--:|
| N=2 / target | −65.6 | +49.7 | **−15.9** |
| N=3 / target | −56.2 | +50.0 | −6.2 |
| N=7 / none | −54.3 | +44.7 | −9.6 |
| **N=19 / target** | −39.0 | +44.3 | **+5.3** |

The right tail is modestly larger than the left at the concentrated depths —
**by 16 bp on a mean of 68, not by the 65.6 the one-sided test implied** — and at
N=19 the left tail is larger.

## What stands and what does not

**Withdrawn:** the "lottery book" verdict, the claim that three of four cells lose
money without their best 1%, and the framing of §2 of D307 generally. The
underlying numbers were right; the conclusion drawn from them was not.

**Unaffected:**

- **§1, the round-trip artefact.** The target's advantage is +4.05 on own spreads
  and +0.80 on a common one. That is arithmetic and it stands.
- **§3, name concentration and drawdown.** Six names of 718 for half the P&L, 17%
  from one name, 92–93% of bars underwater, runs of 466–967 bars. **This is the
  real risk finding and it is untouched** — it is about *names* and *time*, not
  about trade tails.
- **§5, the theory section.** The two mechanical predictions hold, the three
  behavioural ones fail. Untouched.
- **§6, N=3/target as the reasoned pick.** Its case was era stability and
  null-clearing, not the tail test, and it survives — indeed it improves, since
  its trimmed mean is +47.9 against N=2's +52.1 on a book with 50% more
  positions.

**The stop condition changes.** D307 said no cell is an R8 candidate because
every one is a lottery book. **That reason is withdrawn.** The remaining reasons —
six names for half the P&L, 92% of bars underwater, unmodelled borrow, and a
behavioural-effect layer that is noise — are sufficient on their own, but they are
different reasons and the record should say so.

## The durable fix

`CLAUDE.md` reporting group 2 says *"drop the best 1% and re-report the mean."*
That is a good **flag** and a bad **verdict**: on a two-sided fat-tailed
distribution it always produces a frightening number. **The rule is amended to
require both trims**, so the asymmetry is visible rather than assumed.

## Files

`data/d307b_both_tails.json` · `scripts/d307b_both_tails.py`
