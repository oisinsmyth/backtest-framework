# D306 RESULT — the target survives concentration, and the cap is a filter

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D306-RESULT-the-target-survives-concentration-and-the-cap-is-a-filter.md`. The H1 above is the full title.*

**Status:** RESULT. Pre-registered at `5926d93`, runner at `3a2375c`, both
committed before this file existed (R8).
**Date:** 2026-09-03
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 1. Q1, the study's central question, is FALSIFIED

I predicted the target's gross contribution would **shrink to under +2.00 bp at
N = 2**, because D304 and D305 established that the exit earns by replacing names
that have drifted out of selection, and almost nothing can drift out of a
two-name selection.

**It does not shrink.** The target's gross contribution by depth:

| N | 2 | 3 | 5 | 7 | 10 | 14 | 19 |
|---|--:|--:|--:|--:|--:|--:|--:|
| target − none, gross | **+4.32** | +7.39 | +1.38 | −0.20 | +2.27 | +2.10 | **+4.46** |

**+4.32 at N = 2 against +4.46 at N = 19** — essentially unchanged, and the
series across depths has no trend at all. The drifted-out mechanism does not
explain the target's value, or it operates through a channel that survives a
two-name selection. **Either way the prediction was wrong and its reasoning with
it.**

## 2. The two levers compose, and the best cell is both

| cell | net | gross | Sharpe | vol | exposure |
|---|--:|--:|--:|--:|--:|
| **N=2 / target** | **+15.25** | +32.89 | +0.754 | 692.2 | 100% |
| N=2 / none | +11.20 | +28.57 | +0.770 | 588.9 | 100% |
| N=2 / target+overlay | +8.69 | +21.96 | +0.562 | 620.4 | 69.4% |
| N=2 / none+overlay | +7.83 | +20.61 | +0.617 | 530.3 | 67.6% |
| N=3 / target | +5.55 | +26.22 | +0.797 | 522.4 | 100% |

**Concentration and the target add rather than substitute: +11.20 → +15.25.**
That is the pre-registered branch *"the target holds its +4.46 at small N → the
candidate is `concentrated + target`, and the two levers compose."*

**Q3, Q4 and Q6 all confirm:** net peaks at N = 2 in **every one of the four exit
configurations**, and no exit configuration changes which N is best. **Width and
exits are separable on net**, which means future work can optimise them
independently.

## 3. Net and Sharpe point at different books, sharply

| | best cell | net | Sharpe | vol |
|---|---|--:|--:|--:|
| **by net** | N=2 / target | **+15.25** | +0.754 | 692.2 |
| **by Sharpe** | N=7 / none+overlay | +1.85 | **+0.868** | 237.8 |

**A 3× difference in volatility separates them.** This is the principal's own
standing ruling arriving on a second axis: dedicated capital takes the best net,
shared capital takes the best Sharpe. They do not coincide here, and pretending
one number decides would hide the choice.

## 4. Q8 FALSIFIED, and the path-invariant lens is why we know

I predicted the contention drag would **turn positive as N falls** — that a stale
holding occupying half a two-name book would leave the cap nothing to filter.
**The opposite happens.**

| N | 2 | 3 | 5 | 7 | 10 | 14 | 19 |
|---|--:|--:|--:|--:|--:|--:|--:|
| drag, `none` | **−19.12** | −4.22 | −10.94 | −6.82 | +2.85 | −3.24 | +2.20 |
| drag, `target` | **−16.57** | −14.54 | −6.19 | −0.48 | −0.55 | −5.87 | −6.07 |

*(negative = the slot cap makes the book hold the BETTER names)*

**The cap's filter benefit is strongest at the tightest selection**, not weakest.
At N = 2 the variant holds exactly the top two names while the invariant holds
**7.4** — the top two plus everything still running from earlier entries. **The
cap enforces recency of selection, and recency matters most where the selection
is most informative.**

**This is the lens paying for itself.** The path-variant book alone cannot see
this; it took holding the same rule with the cap removed to show that contention
is a filter that *strengthens* under concentration.

## 5. Predictions

| | prediction | outcome |
|---|---|---|
| **Q1** | the target's contribution shrinks to < +2.00 at N=2 | **FALSIFIED** — +4.32 against +4.46 at N=19, and no trend across depths |
| **Q2** | the overlay's Sharpe contribution is constant in N | **PARTLY** — it is +0.207 at N=7, +0.213 at N=19, but **−0.153 at N=2**. It helps a wide book and hurts a concentrated one |
| **Q3** | net peaks at the smallest N in all four configurations | **CONFIRMED**, all four |
| **Q4** | the best net cell is at N=2 or N=3 | **CONFIRMED** — N=2 / target |
| **Q5** | `target+overlay` does not beat `target` at small N *(against D298)* | **CONFIRMED at N=2 and N=3** (+8.69 vs +15.25; +5.52 vs +5.55), **falsified from N=5 up**, where the overlay wins |
| **Q6** | no exit configuration changes which N is best | **CONFIRMED** |
| **Q7** | at N=2 the four configurations differ by < 3 bp of net | **FALSIFIED** — they span **7.42 bp**, from +7.83 to +15.25. The exit axis matters *more* on a concentrated book, not less |
| **Q8** | the contention drag turns positive as N falls *(against)* | **FALSIFIED** — it becomes *more* negative, −19.12 at N=2 against +2.20 at N=19 |

**Four of eight falsified**, three of them predictions I had reasoned from D304
and D305. The mechanism story those two studies produced — that the exit earns
through the drifted-out channel — does not survive the width axis.

## 6. What this does not establish

**N = 2 is four positions and volatility of 692 bp** — 2.9× the incumbent's 238.5.
D300 already noted 7 names of 663 produce half the P&L at this depth. **The best
net cell is also close to the least diversified thing this programme has ever
scored**, and no drawdown or era analysis has been run on it.

**All 28 cells clear BH-FDR at q = 0.10** and 22 of 28 clear p < 0.05 — but the
null tests *the ranking at that depth under that exit rule*, not the exit and not
the width. **No result here is evidence that the exits work**; D303 and D305 did
that separately.

**The overlay's cost is charged at `rt × turn × exposure`**, the favourable
convention declared in the pre-registration. The winning cell does **not** contain
the overlay, so that choice is not load-bearing — had it been, the record required
re-deriving it under D298's stricter convention.

**And this remains a screen on mined data.** R14 unchanged, holdout unread at 0.

## Ledger

| | |
|---|---:|
| **holdout reads spent** | **0** |
| holdout reads, whole programme | **0** |

Disclosed: 28 declared cells (14 position-level books, the overlay applied to the
return series), each against a rank-rotation null at 200 draws on both
statistics, plus 14 path-invariant ledgers for the contention decomposition.

## Stop

**The candidate is `N=2 or 3 / target`, and what it needs is risk work, not more
parameter search.** Name-level attribution, era splits, drawdown behaviour, and
the borrow that has never been charged anywhere in this programme.

**Width and exits are separable** (Q6), so nothing is gained by crossing them
again.

**The D304/D305 mechanism story needs revisiting**: the drifted-out channel
explained the exit's value at N=19 and does not explain it at N=2, where the
exit is worth the same and nothing can drift.

## Files

`data/d306_width_exits.json` · `scripts/run_d306_width_exits.py` ·
`temp/d306_run.log`
