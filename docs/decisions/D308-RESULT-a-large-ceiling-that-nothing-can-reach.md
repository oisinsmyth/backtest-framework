# D308 RESULT — a large ceiling that nothing can reach

**Status:** RESULT. Pre-registered at `4500f38`, runner at `2ad1a99`'s successor,
both committed before this file existed (R8).
**Date:** 2026-09-03
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 1. Stage 1 — the ceiling is LARGE, and Q2 is falsified

I predicted the charged 63-bar oracle would beat the best static `N` by under
5 bp. It beats it by **+18.7 to +26.6**.

| family | best static | static net | **oracle f=63, charged** | **gain** |
|---|---|--:|--:|--:|
| none | N=2 | +11.20 | **+29.89** | +18.69 |
| target | N=2 | +15.25 | **+35.39** | +20.14 |
| none+overlay | N=2 | +7.77 | **+30.45** | +22.68 |
| target+overlay | N=2 | +8.57 | **+35.19** | +26.62 |

**And Q4 is falsified badly too.** I predicted transitions would consume more
than half the uncharged gain at `f` ≤ 21. At `f = 21` they took **4.9%** (2.10 of
a 42.69 gain); even at `f = 1` only 19%. The Viterbi routes around expensive
switches, and my 60–90 bp figure was about the cost of a *move*, not the cost of
a *policy* that makes them sparingly.

**The best static `N` is 2 for all four families**, so D306's conclusion is
unchanged and the baseline stands.

## 2. Stage 2 — Q3 confirmed, and the persistence is mixed

Mean run length of the oracle's width path, against **its own shuffle** (the
pre-registered null: same level distribution, ordering destroyed):

| family | f=1 | f=5 | f=21 | **f=63** |
|---|--:|--:|--:|--:|
| none | 1.33× | 1.09× | 1.03× | **0.93× ANTI** |
| target | 1.27× | 1.08× | 1.03× | **0.95× ANTI** |
| none+overlay | 1.64× | 1.37× | 1.27× | 1.17× |
| target+overlay | 1.51× | 1.28× | 1.16× | 1.20× |

**Q3 confirmed on the raw number** — mean runs of 1.24 to 1.98 blocks — and the
shuffle adds the sharper point: **at the decision frequency that matters, the two
best families' width paths are ANTI-persistent.** Last block's best width is, if
anything, *less* likely than chance to be this block's.

## 3. THE WALK-FORWARD TEST SETTLES IT

Stage 2's stop condition fires on Q3, but "no persistence" and "unusable" are
different claims and the record should not rest on the inference. So the simplest
investable use of whatever persistence exists — **hold the width that was best
last block** — was measured as a declared post-hoc diagnostic:

| family | f=1 | f=5 | f=21 | f=63 | best static |
|---|--:|--:|--:|--:|--:|
| none | −45.80 | −15.62 | −5.83 | −8.23 | +11.20 |
| target | −46.94 | −12.86 | −3.41 | −1.13 | +15.25 |
| none+overlay | −37.18 | −5.79 | **+1.48** | −3.98 | +7.77 |
| target+overlay | −32.47 | −10.99 | −2.60 | −1.36 | +8.57 |

**Sixteen of sixteen lose to the best static `N`**, by −6.29 to −62.19 bp, and
fifteen of sixteen turn a positive net negative. The single positive cell
(+1.48) still loses to its own static baseline by 6.29.

**So the ceiling is the value of knowing the future, not exploitable structure.**
A +26 bp ceiling whose most-informative available predictor — its own immediately
preceding block — delivers **−9.94** is the signature of fitting block-level
noise, not of a timing opportunity.

## 4. The answer to the question that was asked

**No market-wide indicator can track the best `N`**, and the reason is stronger
than "we did not find one":

**The optimal width's own immediate past is worse than useless as a predictor of
it.** Any indicator would have to beat that, on a target that is anti-persistent
at the frequency where transitions are affordable. **Stage 3 does not run**, per
the pre-registered stop condition, and the four declared conditioners —
cross-sectional dispersion, signal separation, breadth, and their product — are
not measured.

## 5. Predictions

| | prediction | outcome |
|---|---|---|
| **Q1** | the f=1 oracle beats static by > 50 bp uncharged | **CONFIRMED** — +166 to +180. A harness check, not a finding |
| **Q2** | the charged f=63 oracle gains < 5 bp *(against)* | **FALSIFIED** — +18.7 to +26.6 |
| **Q3** | `N*` mean run below 2 blocks at every frequency *(against)* | **CONFIRMED** — 1.24 to 1.98, and anti-persistent at f=63 for the two best families |
| **Q4** | transitions consume > half the uncharged gain at f ≤ 21 | **FALSIFIED** — 4.9% at f=21, 19% at f=1 |
| **Q5** | the Sharpe-optimal path is more persistent than the net-optimal | **NOT EVALUATED** — the study closed on Q3 before the Sharpe oracle was needed |
| **Q6** | X1 (dispersion) is the strongest conditioner | **NOT RUN** |
| **Q7** | no conditioner survives BH *(against)* | **NOT RUN** — and the walk-forward result makes it moot |
| **Q8** | the four families give materially different paths | **CONFIRMED** — the overlay families are persistent at f=63 where the others are anti-persistent |

**Two of my four "against" predictions were wrong in the direction of the
opportunity being larger**, and the study still closes — because the size of a
ceiling says nothing about whether it can be reached.

## 6. What stands

- **The static grid is the answer.** Best `N` = 2 on net for all four families;
  D306 and D307's readings are untouched.
- **`N` is a fixed design parameter, not a timed one.** Three studies have now
  tested varying it — D299's ladder, D305's blocking arms, and this — and all
  three closed.
- **Transitions are cheaper than I estimated**, which matters for any future
  rule that moves width for a *non-timing* reason (capital changes, capacity).

## Stop

**Time-varying book width is closed.** Not because the prize is small — it is
+26 bp — but because the target is anti-persistent at the only frequency where
the trade is affordable, and its own immediate past is a losing predictor.

**What is left is the entry signal**, frozen since D293 and now the only untested
surface of any size in this programme.

## Files

`data/d308_width_in_time.json` · `data/d308b_walk_forward.json` ·
`scripts/run_d308_width_in_time.py` · `scripts/d308b_walk_forward.py`
