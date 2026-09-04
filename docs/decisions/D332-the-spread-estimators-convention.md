# D332 — the spread estimator's CONVENTION, not its floor: the stack has been charging less than half the estimator's published value

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-05
**Area:** Strategy research · **personal track** · cost model

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. What the stage-0 measurement found, and why this is not the study I set out to write

STACK §6 listed "the spread estimator's floor" as the next infrastructure
item: Corwin–Schultz reads a pinned stock's spread as zero, three D329 cells
divided by it, and a half-tick floor is exact and un-fitted. Before
pre-registering that, I measured the conditioner (`cs_zero_rate.py`, kept in
`scripts/` as `d332_cs_zero_rate.py`):

```
per-bar Corwin-Schultz half-spread, all 4,135,181 live name-bars
  EXACTLY ZERO on 43.2% of them
  by price bucket: 34% (<$1) ... 44% ($100+)   -- uniform
  P(next bar also zero | zero) = 0.44  vs  P(zero) = 0.43   -- uncorrelated
  median where nonzero: 51.3 bp     overall median: 14.2 bp
```

**The zeros are not pinned names. They are noise.** The authors' convention
sets a *negative* two-day estimate to zero, and the two-day estimate is
negative 43% of the time on every kind of stock. A single-pair estimate is a
coin flip between zero and a number, and **the cost model takes the median of
that coin flip across a leg's entries.** A leg whose entries land above 50%
zeros is charged **nothing** — the three degenerate cells — and a leg near 50%
is charged a number set by which side of the coin it fell, not by its spread.
A tick floor of 0.3–7 bp does not touch that.

**Corwin and Schultz do not use the single-pair estimate.** They set negatives
to zero and **average the daily estimates over a month**. This codebase already
computes exactly that: the axis-E score `cs_spread` is the trailing 21-bar
mean of the lagged, clamped daily estimates over each name's own bars
(`ragged_vol_scores.py:140–147`). Its universe median is **31.7 bp per side**.
The per-bar median the cost model uses is **14.2**. **The stack has been
charging 45% of the estimator's own published value.**

### The history, stated as carefully as the records allow

D285 reported the held names' spread as a **mean** — 33.8 bp — and that is
the number CLAUDE.md quotes. Later runners (D318: held 18.31; the universe
13.20 cited to D302 in FINDINGS §13) use the **per-bar median at entry**.
**No record in `docs/decisions/` explains that switch**, and the stack's
charged spread roughly halved at it. This study does not decide which is
*true* — that needs quoted spreads — but it establishes which is the
estimator's published form and what the stack looks like under it.

## 1. The three conventions, declared

At each trade's entry bar `e0` for name `i`:

| | half-spread charged | status |
|---|---|---|
| **PB** per-bar median | median over the leg's entries of `CS_pair(e0, i)` — the current cost model | the incumbent convention, unrecorded |
| **PUB** published | median over the leg's entries of `cs_spread(e0 − 1, i) / 2` — the trailing-21 mean of clamped daily estimates ending at the bar before entry, per the authors and per E2's causality convention | the estimator as specified |
| **+floor** | either, with `max(·, ½ tick / close)` applied per name-bar; tick = $0.01 at or above $1, $0.0001 below (Reg NMS Rule 612) | exact; a physical bound |

**IBKR's official per-share commission is unchanged and not in question.** It
is `$0.005 / price` per crossing, as D318 applied it. The per-order $1.00
minimum depends on position size and is the PM's to add; the 1% maximum binds
only below ~$0.50. Neither is applied here, and that is stated rather than
hidden.

**The harness change is one array.** Every runner from D318 on reads the
spread through `held_median(res, HALF)` at `(entry, row)`. PUB is a different
`HALF` array and nothing else moves — which is what makes `[1]` (identity under
PB) and `[S]` (the swap is the only difference) checkable.

## Part A — the levels, per leg. Measurement, no predictions

For every leg D329 and D330 measured — the six D329/D330 arms, the 46
symmetric singles, the three degenerate cells — the held half-spread under PB,
PUB, PB+floor, PUB+floor; the zero-clamp fraction among the leg's entries; and
the per-leg `2c` under each. Two tables, one per side.

## Part B — the stack repriced under PUB. Pre-registered

Same cells as Part A plus the incumbent (`C0_incumbent` via D325's
`rank_composite`, at depth 2 and depth 19) and the D323 shortlist's thirteen
at the operating point. Both lenses, k=20, D329's per-leg costing, PUB
throughout unless the row says PB.

| | prediction |
|---|---|
| **Q1** | **The incumbent nets ≤ 0 bp/bar at N=2 under PUB.** Under PB it nets +11.36 at a charged round trip of 73; PUB roughly doubles the spread term. *Load-bearing, against the stack.* |
| **Q2** | **Concentration survives**: N=2 minus N=19 on the incumbent stays within ±5 bp/bar of its PB value, because turnover is `1/k` at every depth and the basis cancels (STACK Axis B). |
| **Q3** | **The leg-wise book still beats both parents** on invariant net per trade at k=20 under PUB — its cost advantage is relative. |
| **Q4** | **dv28's advantage over its base widens** under PUB — a cost effect grows with the cost basis. *Directional only: the dv28 cell here is rebuilt from `DV` and `gate_from(keep=)` and is not asserted to be D321's cell.* |
| **Q5** | **The D323 shortlist's top-2 at the operating point changes** under PUB — at least one of its two leaders on net bp/bar is replaced. *Against the current shortlist.* |
| **Q6** | The three degenerate cells become costable under PUB and **none ranks in the top 10** of its enumeration direction. |
| **Q7** | The half-tick floor changes **no** PUB cell's net per trade by more than 1 bp — under the published convention it is a formality. |

### Stop conditions

- **Q1 confirms** → the stack's headline number is a cost-convention artefact,
  and STACK §0 is rewritten under PUB with PB shown beside it. Nothing about
  the *ranking* of constructions is decided by this alone.
- **Q2 fails** → Axis B's "basis-immune" claim was wrong for this basis;
  D300/D306's width result needs re-running under PUB.
- **Q3 fails** → the leg-wise result was a cost-convention artefact. D329 and
  D330 are amended.
- **Q5 confirms** → D323's shortlist is re-read under PUB before any signal
  study uses it.
- **Either way:** **which convention is *true* is not decided here.** That
  needs quoted spreads, and the fixture has none. Part C.

## Part C — the validation this cannot do, proposed

IBKR's historical data API serves BID_ASK bars for live names. A sample of
fixture names still trading — stratified by price and by dollar volume — over
a recent window would give the quoted half-spread directly. Compare PB, PUB and
at least one alternative estimator (Abdi–Ranaldo 2017's close–high–low, built
for daily data) against it, with the selection rule declared in advance:
lowest median absolute error in log spread across the sample. **The winner
becomes the cost convention; until then PUB is the default because it is the
one the estimator's authors specify.** This is a data task on the principal's
IBKR session, not a study I can run.

## Assertions

1. **[1] identity under PB** — every arm reproduces D329's cells to 1e-9 on
   both lenses when `HALF` is the per-bar array.
2. **[S] the swap is the only difference** — under PUB the trade ledgers are
   bit-identical to PB's; only the cost changed. (Cost never touches
   selection here, and this proves it.)
3. **[Z] PUB's zero rate** — the fraction of finite PUB values that are exactly
   zero is below 1%, against PB's 43%. The published convention is the
   dilution it claims to be.
4. **[C] causality of PUB** — `cs_spread(e0 − 1)` uses pairs ending at bar
   `e0 − 1`; the truncation audit from `ragged_vol_scores` holds on the array
   used.
5. **[F] the floor is a floor** — applied values are ≥ the tick bound
   everywhere and equal to the input wherever the input was above it.
6. **[U] units** — PUB is `cs_spread / 2 × 1e4` (round-trip fraction to
   half-spread bp); the universe medians reproduce 31.7 (PUB) and 14.2 (PB).
7. **[6]** the self-test raises on a cell handed a free spread.

*Every assertion is a property of the code or of the estimator's definition.
None asserts what a book will show.*

## Scope

**Out:** any estimator other than Corwin–Schultz (Part C proposes one); borrow;
the rebalancing cost; the holdout. **In:** the levels (A), the repricing (B),
and the record of what convention the stack has actually been using.

## Files

`docs/decisions/D332-the-spread-estimators-convention.md` (this record) ·
`scripts/d332_cs_zero_rate.py` (the stage-0 measurement, committed with this
record as its evidence) · runner and data to follow.
