# D526 — the curve story fails Stage 0: the **level is a regime**, the **change carries nothing**, and the failure mode is now three-for-three

*2026-09-14, opening the search for the prop book's second component under the principal's "tell a
story" framing. Stage 0 only: no P&L, no position, no cost, nothing admitted to any book or ledger
(R15). Window 2016-01-04 → 2023-12-29; the 2024+ slice is RESERVED and was not read.*

---

## The story that was being tested

> **A price move is asymmetric when it forces somebody else to trade the same way. In a storable
> commodity the front-to-next spread is the market price of IMMEDIACY — and the outright price tells
> you nothing about it.**

Steep backwardation means inventory is tight and a participant with a physical obligation cannot
wait. The prediction was about the **shape** of the day-session move, not its mean: in backwardation
a dip forces buying, so the left tail is truncated and the payoff ratio rises.

**Why shape and not accuracy.** The admitted arm hits **50.5 %** with a payoff ratio of **1.13** —
`0.505 × 1.13 − 0.495 = +0.076`. At a payoff of 1.00 its edge would be **+0.005**. *The one thing
that works in this programme is not paid for being right; it is paid for being right bigger.* Every
prior search hunted accuracy. This one hunted shape.

> **THAT PREMISE IS WRONG, corrected the same day by [D529](D529-the-payoff-ratio-is-exit-geometry-the-hit-rate-is-the-edge-and-my-reframe-was-backwards.md).**
> A detached signal run through the arm's own exit produces a payoff ratio of **1.041 median / 1.138
> p95** — the arm's 1.128 is **inside** its own exit's null, while its **hit rate clears it with 0 of
> 400 draws reaching 50.5 %**. The arm is paid for being RIGHT. **This study was therefore designed
> around the wrong statistic**: §3's skew-and-payoff split was the wrong thing to measure. It does
> not change this record's verdict — the curve died on n_eff in §4 before the shape statistic
> mattered — but a future curve study should ask about ACCURACY, conditioned on the curve, and score
> it against its own exit's null.

The line was worth opening because the audit in D521 had established there **is** no curve study
here (*"every hit is incidental"*), and because the open-interest fixture was wrong in precisely
`oi_total` and `oi_n_contracts` — the columns a curve study reads and a front-month study does not —
until it was corrected the same week.

## The verdict, in one table

| check | CL | GC | verdict |
|---|---|---|---|
| **1 persistence** lag 1 / sign flips | **+0.943** / 3.8 % | +0.826 / 5.7 % | **passes** |
| **2 collinearity** 60-day, pearson / spearman | +0.498 / **+0.162** | −0.132 / −0.138 | **passes — not momentum** |
| **3 shape** skew, contango → backwardation | +0.39 → **−0.59** | +0.42 → +0.36 | prediction **inverted** on CL |
| **3 shape** payoff, contango → backwardation | 1.087 → **0.867** | 1.068 → 1.046 | prediction **inverted** on CL |
| **4 n_eff** years containing BOTH states | **0 of 8** | 5 of 8 | **the test is invalid** |
| **5 the change** year-gap mean / positive years | −0.038 / **3 of 8** | −0.005 / **3 of 8** | **nothing** |

## 1. Persistence passes — and that turns out to be the problem

CL's curve autocorrelates **+0.943** at one session and flips sign on **3.8 %** of sessions. That is
far more than enough to condition a hold measured in hours, which is what check 1 was for.

It is also *too much*. Check 4 asks the question check 3 assumed: **do both states occur inside a
year?** On CL, **zero of eight years** contain twenty observations of each extreme tercile. The
periods sort cleanly — 2016, 2017, 2019 and 2020 are contango; 2018, 2021, 2022 and 2023 are
backwardation.

**So the tercile is a PERIOD, not a state.** Comparing payoff across terciles compares *eras*, with
every other thing that changed alongside them, and the effective sample is **eight**, not 1,914.
CL's year-by-year payoff gap is computable in **no year at all**.

The inverted shape result in check 3 is therefore not a finding and is not reported as one. Its most
likely reading is mundane: the contango bucket contains **2020**, whose day-session SD is 226 bp
against 159 and 179 for the other two.

## 2. Collinearity passes, and the way it passes is worth keeping

CL's Pearson correlation against trailing returns rises with horizon — +0.127, +0.317, **+0.498** —
which taken alone would have killed the story as momentum in disguise. But **Spearman over the same
horizons is +0.020, +0.088, +0.162.** The Pearson is a handful of extreme joint observations; there
is no rank relationship. GC is independent outright.

**A conditioner can look collinear on Pearson and be independent on ranks**, and on this data the
difference is the whole verdict. Report both.

## 3. The repair, and the real answer

The level is a regime; the **change** is a session-level event. That is a real repair and it works as
one: **8 of 8 years** carry both extremes of `d(curve)`, so the within-period variation that check 4
found missing is there.

And it carries nothing. CL steepening 0.938 vs flattening 0.956; GC 1.047 vs 0.916 pooled — which
looks interesting until the year-by-year gap reads **−0.005, positive in 3 of 8 years**. A pooled
effect that is positive in three years of eight is a pooled effect, not an edge.

## 4. What generalises — and this is the part worth more than the story

**This is the third conditioner to fail the same way, and the failure is structural rather than
empirical.**

| record | conditioner | how it failed |
|---|---|---|
| D508 | log(price / 200-day MA) | *"ranks YEARS, not sessions"* |
| D512 | log(EMA50 / SMA200 of the range) | the effect was a property of NQ's own history; did not transfer |
| **D526** | the front-to-next settlement spread | **0 of 8 years contain both states** |

> **On a daily clock with an eight-year in-sample window, a conditioner slower than about a month has
> n_eff measured in YEARS, not sessions, and cannot be tested cross-sectionally at all.** Its
> terciles are calendar periods wearing state labels.

**The operational rule this leaves:** before designing any study around a conditioner, compute
**how many years contain both of its extreme states**. If the answer is not most of them, the
conditioner cannot be tested on this fixture at that resolution, and the only version with real
within-period variation is its *change* — which must then be tested on its own, year by year, never
pooled.

That check costs one line and would have saved this study, D508 and D512.

## 5. Two by-products that outlive the story

**The settlement strip now exists.** [`data/d526_curve_strip_CL_GC.csv.gz`](../../data/d526_curve_strip_CL_GC.csv.gz)
— 263,983 settlements, CL **188 contracts** (p50 **124 a session**) and GC 110 (p50 21), 2,013
sessions each, 2016-2023, CL priced −37.63 … 123.70 and GC 1,073.60 … 2,456.20. It is the first
curve data in the repository and it is reusable by anything that wants the strip rather than the
front month.

**A SECOND missing-value sentinel in the `statistics` schema, which nothing in the repo filters.**
The band assertion fired on **646 settlements of exactly `0.0`** — CL 344, GC 302, spread across all
eight years, concentrated in deferred months (`CLF30`…`CLF35`). `UNDEF` is `INT64_MAX` and the
existing builders filter it; **zero is a different marker and it is positive-adjacent, so no
existing guard catches it.** And the fix cannot be "drop non-positive", because **CL legitimately
settled −37.63 on 2020-04-20**. Any future study reading settlements must drop exact zeros and keep
genuine negatives.

---

Everything here is recomputed by [`scripts/d526_curve_premise.py`](../../scripts/d526_curve_premise.py)
(`--extract`, 1.8 min on the system interpreter; `--run`, seconds) into
[`data/d526_curve_premise.json`](../../data/d526_curve_premise.json).

**Not closed:** the curve as an object, and CL/GC as roots. This closes *this conditioner at this
resolution on these two roots*. Under [signal criterion and avenue closure] only the principal
closes an avenue, and I have been corrected four times for retiring an axis on one construction's
failure.
