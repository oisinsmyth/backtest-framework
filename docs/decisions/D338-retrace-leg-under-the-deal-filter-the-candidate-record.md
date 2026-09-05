# D338 — `retrace_leg` symmetric under the deal filter: the candidate record

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). Nothing here is a
result. **Nothing in this study can admit a strategy to the book** — R8 needs a separate
out-of-sample test on a fixture the candidate has never seen, and the holdout stays at
zero reads. What this study can do is make `retrace_leg` the programme's first *declared
candidate*, with the four groups a result needs and the top trade named, or show why
it is not one.
**Date:** 2026-09-05
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. Why

`retrace_leg` symmetric at k=20 has been the best book in the programme for three
studies running — D333 (+18.78 PB / +13.76 PUB bp/bar), D335 under the F0 deal filter
(+23.43 / **+18.93**, Sharpe +0.676 / **+0.546**), D337 by omission — and it has never
had a record of its own. Every number quoted for it is a cell in another study's table.
It has no four-group report, no named top trade, no null of its own under F0, no borrow
charge. D322 was the first four-group report and D333 found PNK inside it; STACK §6
puts this record before anything else is built on the book.

## 1. What `retrace_leg` is

From `ragged_structure_scores.py`: with confirmed swing pivots at half-width K=3 and a
leg wider than half an ATR, `retrace_leg = (close − last_low) / (last_high − last_low)`,
defined only while both pivots are fresher than 252 bars, bounded to ±30. **It is
dimensionless** (a price ratio — D328 §14's test), and it is a structure-relative
position: 0 at the last swing low, 1 at the last swing high, below 0 through the low,
above 1 through the high. The symmetric book **longs the 25 most negative** (names that
have broken below their last swing low) and **shorts the 25 most positive** (above their
last swing high), depth 2 on each side, D303's market-referenced target exit at k=20.

**What is already known about its legs** (D335, F0, per trade, PUB): long +46.2 net on
+110.0 gross, t = 3.36, held half-spread 31.9 bp at $28; short **−29.0** net on +31.7
gross, t = 1.21, 30.4 bp at $38. The long leg is the book; the short leg costs 29 bp a
trade and is kept for what it hedges. That is a statement about the invariant lens; the
book is scored on the variant one, and never on the same statistic.

## 2. The cell, fixed

One cell, no grid: `retrace_leg` symmetric · depth 2 · k=20 · D303 target (`X_TARGET =
0.9627`) · **F0 deal windows removed from the score before ranking** (D331's target
forms, 189-bar window; the name is replaced, not left a hole) · D333-bounded panel ·
D334-rebuilt cache. Both spread conventions, **PUB primary**. Borrow under D337's
declared schemes (GC 50 / HTB 500 bp/yr on F0-window or sub-$5 names; house 300) as new
keys. Both lenses: variant book in bp/bar, invariant ledger per trade.

The four-group report is `d322_four_group_report`'s own functions — `costed`, `group1`,
`group2`, `group3`, `contributions`, `unattributed` — applied to this cell, so a
reader of D322 can read this without a new convention. The null is the family's own:
**rank rotation inside the 25-name gate** (D300/D306/D322/D323), 200 draws, seeded
`[W.SEED, 338]`, scored under both conventions on gross bp/bar, gross Sharpe and net
Sharpe. `fast_null.py` is not the scorer here because this family's book is a
simulator with an exit, not a position matrix; the null draws are the simulator's own
`shift` argument, as in every D300-family record.

## 3. The top trade, declared in advance

Reporting rule 3 and FINDINGS §18: the largest trade by P&L on the variant ledger and
the largest name by contribution are **named**, and the top trade's bars are printed —
date, open, high, low, close, volume, one-day return — with any dividend on file for
those dates and any F0 filing within 400 days. The top five trades are tabled with the
largest one-day |return| in each hold and the dividend on that day if any.

## 4. Predictions

Q6 is load-bearing. Q1 is the data gate. Q5 is against.

| | prediction |
|---|---|
| **Q1** | *(data gate)* the top trade is a price move, not an event: no dividend ≥ 1% of the close on any bar of its hold, and its largest one-day return equals the close-to-close move on that bar within 1 pp. Its P&L is **< 5%** of the ledger's total (the incumbent's top trade was 15%, and it was PNK). |
| **Q2** | the mean trade P&L is **below the median** (the invariant lens has 72 against 194), and **the bottom 1% of trades outweighs the top 1%** in share of P&L: the left tail does the work. The symmetric 1% trim moves the mean by **< 15 bp**. |
| **Q3** | names to half the P&L **≥ 40**; top-10 name share **< 25%**. |
| **Q4** | PUB net-positive in **≥ 11 of the 17** calendar years; gross-positive in ≥ 13. |
| **Q5** | *(against)* the cheapest price tercile is **< 50%** of P&L (the incumbent's was 57%) and is net-positive on its own `2c` under PUB; dead names are **< 30%** of P&L; **both era halves** are net-positive under PUB. |
| **Q6** | *(load-bearing)* net Sharpe is above the rank-rotation null's **p95 under both PB and PUB**, and the null has teeth — **p95 > 0** on net Sharpe. |
| **Q7** | HTB covers **< 10%** of short position-bars; GC+HTB costs **< 0.5 bp/bar**; PUB net after GC+HTB and after the house rate both stay **> +15 bp/bar**. |
| **Q8** | breakeven half-spread per side is **≥ 2.0×** the held PUB half-spread (≥ 65 bp against 32.4). |
| **Q9** | the book is live on **> 95%** of panel bars and fills its four slots on **> 99%** of live bars. |
| *check* | the cell reproduces D335's F0 `retrace_leg` cells to 1e-9 — variant net and Sharpe under PB and PUB, invariant net per trade, both legs. A reproduction, not a prediction. |

## 5. Stop conditions

- **Q1 fails** → nothing is read. The event is named, D333's bound is revisited, the
  panel is fixed, and this study re-runs on the fixed panel under the same record.
- **Null p95 ≤ 0 on net Sharpe** → R7's pathology (a losing random control): the result
  is untrustworthy whatever the percentile; the null is redesigned before anything is
  read.
- **Q6 fails on either convention** → `retrace_leg` is **not a candidate**. Recorded as
  such; no further work on it as a book.
- **Q2, Q3 or Q5 fail** → the book carries a concentration or lottery flag in its
  record and stays a candidate with the flag; the four-group report is the deliverable
  either way.
- **Q7 fails** → the borrow charge is reported and the PUB-after-borrow number replaces
  the PUB number wherever this book is quoted.
- **Everything holds** → `retrace_leg` symmetric under F0 is the personal track's
  **declared candidate**, frozen at these parameters, for an R8 out-of-sample test that
  this study does not run: the same cell, no parameter free, predictions on net bp/bar
  and own-null p95 declared before the read, on a fixture disjoint from this one in
  names or in time. **Nothing is promoted here.** Book: still empty.

## 6. Assertions — properties of code, not of outcomes

| | |
|---|---|
| **[1]** | reproduces D335's F0 `retrace_leg` cells to 1e-9 (variant PB/PUB net bp/bar and Sharpe; invariant per-trade net under both; both legs' net) |
| **[A]** | **lag audit, second implementation**: on 200 sampled bars, the long-leg gate at t is rebuilt from the raw score at **t−1** with the F0 mask at t−1 and the warm-and-live base at t, by an independent stable argsort that never calls `rank_single` or `rank_columns`, and equals the gate's set; the same rebuild from the score at **t** differs on most sampled bars |
| **[S]** | **sign audit in money**: on a synthetic two-bar path, a long over a rise pays positively and a short negatively; on the real ledger every trade's P&L equals `sgn·Σ(v − mt)` recomputed from `(row, e0, age, side)` to 1e-12 |
| **[RQ]** | right quantity: the summed ledger differs from `simulate(accumulate="compound")`'s on the same entries and exits, and the summed one is what group 1 scores |
| **[2]** | ledger reconciliation (D322 [2]): closed trades reconstruct gross bp/bar up to the positions open at T, no hole before `T − k`; the check rejects a ledger with a mid-run trade removed |
| **[3]** | the 1% trim is symmetric and the check rejects a trim one deeper on one side |
| **[F]** | the F0 mask reproduces D331's second pass: 1,719 filings applied, 2.54% of live name-bars |
| **[N]** | rotating the rank array moves the book; ≥ 195 of 200 null draws are valid (≥ 200 masked bars) |
| **[B]** | borrow per bar × `cnt1` equals borrow per trade, summed, within 1e-9; house = 300/252 on every ledger-covered short bar |
| **[U]** | the score is dimensionless and bounded: every finite value in [−30, 30], and multiplying every close by 10 leaves `(close − lo)/(hi − lo)` unchanged on a synthetic path |
| **[6]** | [1] raises on a book handed +5 bp on 200 masked bars |

## 7. Scope

**In:** the one cell, both lenses, both conventions, three borrow schemes, the four
groups, the named top trade, the rank-rotation null. **Out:** any parameter sweep (k,
depth, target, filter window — each is fixed above); dv28 (the book fills; D321's
variant is not applied); the compounding book; the holdout; the out-of-sample test
itself, which needs a fixture that does not exist here.

## 8. Speed

Two simulations for the cell, 200 for the null at ~1.2 s each under the slot cap; the
panel and cache load once. About five minutes; run in the background.

## 9. Files

`docs/decisions/D338-retrace-leg-under-the-deal-filter-the-candidate-record.md` (this
record) · `scripts/run_d338_retrace_leg_candidate.py`, `data/d338_retrace_leg_candidate.json`
(to follow). Prior evidence: `data/d335_legs_under_filter.json` (the cells reproduced),
`data/d331_deal_filter.json`, `data/d337_constant_shares_borrow.json`.
