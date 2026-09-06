# D356 — the `rsi` and `hist_L` books as a portfolio: one blend, two arms, the covariance measured

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). The secondary arm's
construction is named in a committed addendum after D355's report, before it runs. Nothing
here is a result; the output is whether two books that each clear every hurdle are worth
more together.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. Why

`rsi` k=40 (+5.1 PUB, Sharpe 0.27) and `hist_L` k=40 (+12.4, Sharpe 0.40) are separate slot
books on different scores, each above both nulls (D348). A portfolio of two books is a
Sharpe lever with no new look, if their bar series are not the same series. D342 measured
the `rsi`–`retrace_leg` left-tail overlap (two names of twelve); nothing has measured
`rsi`–`hist_L`. D239's arithmetic is the caution: a 50/50 **capital** blend with a higher-vol
arm drags toward that arm, and `hist_L`'s vol is 1.6× `rsi`'s.

## 1. The construction

Both cells re-simulated as D346 built them. **50/50 capital:** `book_blend = 0.5·(book_rsi +
book_histL)` on the bars where both books are defined (asserted to be every bar both
report); gross the mean of the two; **cost the mean of the two books' own cost per bar**
(each `G22.costed` on its own ledger — a merged ledger is never re-priced); net, vol, net
Sharpe, max drawdown, PUB and PB. Beside it the arithmetic prediction
`Sharpe_pred = 0.5·(net_a + net_b) / sqrt(0.25·(v_a² + v_b² + 2ρ·v_a·v_b))`.

**Overlap:** the correlation of the gross series; the share of each book's worst 1% of bars
that are also in the other's; the names shared among the two books' worst 1% of trades; the
share of bars on which both hold the same name on the same side.

**Arms:** primary — the published target exit; secondary — D355's selected construction if
it is the invalidation exit (addendum). Multiplicity: one blend, two arms.

## 2. The nulls

100 paired draws: each parent time-rotated independently (D348's rotation, its own seeds
`[SEED, 356, parent, part]`) and blended the same way; the 24 rank rotations paired
shift-for-shift. Statistics: net Sharpe and net bp/bar, PUB.

## 3. Predictions

Q2 is load-bearing. Q6 is against.

| | prediction |
|---|---|
| **Q1** | the correlation of the two gross series is **< 0.4**. |
| **Q2** | *(load-bearing)* the blend's **PUB net Sharpe exceeds the better parent's** (0.401). |
| **Q3** | the blend's max drawdown is below the smaller parent's. |
| **Q4** | the worst 1% of bars overlap on **< 25%** of them, and the worst 1% of trades share **≤ 3** names. |
| **Q5** | the blend is above the p95 of its paired time-rotation null on net Sharpe. |
| **Q6** | *(against)* the blend's net Sharpe exceeds the arithmetic prediction by more than 0.05. |
| *check* | each parent reproduces D346 to 0.0; the blend's net equals the mean of the parents' to 1e-12; its variance equals the covariance arithmetic to 1e-9. |

## 4. Stop conditions

- **Q2 holds** → the blend is a candidate portfolio; whether D357's single read is spent on
  the portfolio or on the selected single book is the principal's choice, recorded in D357's
  addendum.
- **Q2 fails** → the books stay separate; the record says what the correlation was.
- Nothing is promoted. Book: empty.

## 5. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | via the shared prep |
| **[ID]** | each parent reproduces D346's cell to 0.0 |
| **[M]** | the two masks coincide |
| **[LIN]** | `net_blend == 0.5·(net_a + net_b)` and `gross_blend == 0.5·(gross_a + gross_b)` to 1e-12 |
| **[V]** | `vol_blend² == 0.25·(v_a² + v_b² + 2ρ·v_a·v_b)` to 1e-9 |
| **[T]** | the worst-1% bar and trade sets are recomputed independently |
| **[A]** | each parent's rotation keeps counts and multisets |
| **[6]** | [LIN] raises on a 60/40 blend; [V] raises with ρ replaced by 0 |

## 6. Files

`docs/decisions/D356-the-rsi-and-hist-L-books-as-a-portfolio.md` (this record; addendum to
follow) · `scripts/run_d356_blend.py` (stages `--selftest`, `--null --arm A --draws N --part
p`, `--report`) · `data/d356_*.json` (to follow). Reuses `scripts/run_d348_score_rotation_null.py`,
`scripts/d348_prep.py`, `scripts/d322_four_group_report.py`.

---

## Addendum — the secondary arm, 2026-09-06 (committed before any secondary-arm stage; none runs)

D355's Q1 failed on both cells: the target stays. By this record's §1 the secondary arm
exists only if D355 selects the invalidation exit, so **no secondary arm runs** and the
result reports the target arm alone.
