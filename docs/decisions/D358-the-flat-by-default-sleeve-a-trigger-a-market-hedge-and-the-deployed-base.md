# D358 — the flat-by-default sleeve: a real trigger, a market hedge, no slot cap, scored on the capital it actually asks for

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). Nothing here is a
result. Nothing here is a book: the output is a sleeve for a multi-strategy book — a
per-bar deployed series with its exposure flag — and the numbers that say what it earns per
unit of capital-time and when.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. Why

The principal's book is a multi-strategy book with era detection and dynamic weighting. A
sleeve in it should be flat by default, ask for capital only when it has an edge, and hand
the allocator a series that says when. The always-invested slot books are scored on
capital they sit on; that is the wrong lens for a sleeve. The record has tested
flat-by-default constructions three times (D345, D353, D354) and each was mis-built or
mis-hedged in a named way: a threshold calibrated to exposure, unhedged series, a target
exit that cuts the winner, a hedge made of a few names. This record builds the sleeve with
the fixes the record named — a trigger that beats every honest control (D351, D353), a
market hedge (D354), the hedged capital series (D353), no slot cap — and scores it on the
deployed base with its exposure stated.

## 1. The family, declared: two scores × three rarities = six cells

A trigger is a **fresh entry into the bottom p%** of the lagged floored cross-sectional
percentile of the score: `pct[t] ≤ p` and `pct[t−1] > p`, on eligible bars after the hedge is
defined. Scores `rev_5` and `hist_L` (the two real triggers with the cleanest and the
largest per-trade means); p ∈ {2, 5, 10}. The 10% cells are D350's `rev_5`/E1 and
`hist_L`/E1 and must reproduce them exactly. Multiplicity six, stated.

## 2. The sleeve

- **Entry:** every trigger event is taken at the next open, long the name. No slot cap:
  exposure floats with the signal and the allocator sees it.
- **Hedge:** the floored universe's equal-weight return, per bar, on every position — the
  strategy's alpha series. The **unhedged** series is reported beside it, because a
  long-only sleeve in a book may be hedged by the book.
- **Exits:** the 40-bar cap (primary) and invalidation (the percentile crosses back above
  50), each reported with its own cost line. No target: D355 says the target belongs to the
  refilled slot book.
- **Series:** the **deployed base** — the hedged return per bar averaged over open positions,
  NaN when flat — is the sleeve's series, costed as the slot books are (round trip at the
  held names' median half-spread, commission per crossing, turnover on names held; PUB
  primary, PB beside; no borrow, it is long). Beside it: exposure (share of bars with a
  position, mean positions when deployed), entries per year, the total-base series at
  U = 4 for comparison with D345/D353 only.
- **For the allocator:** the per-bar deployed hedged and unhedged returns, the open-position
  count and the entry count are written to `data/d358_series_{score}_{p}.npz` and must
  reload to the reported statistics.

## 3. The nulls

Per cell, on the primary exit: **A′** — each name's events rotated in time within its
eligible bars, re-simulated with the hedged series, 100 draws; **B** — each event's name
replaced by a random eligible name in the same `rsi` bucket that day, defined-percentile
pool, 100 draws; **C** — random direction on the per-trade ledger, 1,000. Statistics under
A′ and B: deployed net PUB bp/bar, deployed net Sharpe, mean per trade.

## 4. The splits the allocator needs

By year; era halves; down-years; and the deployed statistics **by `rsi` bucket of the
trigger name** (D347/D350: a long trigger is worst at the bottom of the ranking), so the
allocator can also condition on where the trigger fires.

## 5. Predictions

Q1 is load-bearing. Q5 is against.

| | prediction |
|---|---|
| **Q1** | *(load-bearing)* the `rev_5` 2% cell, cap exit, has **deployed PUB net bp/bar > 0** and is above the p95 of A′ and B on it. |
| **Q2** | mean per trade **rises with rarity** (2% > 5% > 10%) on the cap exit for both scores. |
| **Q3** | entries per year at 2% are **less than half** those at 10% for both scores. |
| **Q4** | the 2% cells are deployed on **fewer than half** the defined bars. |
| **Q5** | *(against)* some cell nets > 0 per trade under PUB on the invalidation exit. |
| **Q6** | the invalidation exit has higher deployed **gross** per bar than the cap on every cell, and lower deployed **net PUB** than the cap on every cell. |
| **Q7** | era 2 exceeds era 1 on deployed net PUB for every cell, and the 2% cells' era-1 deployed net PUB is ≤ 0. |
| **Q8** | the unhedged deployed series has higher gross and lower Sharpe than the hedged on every cell. |
| *check* | the 10% cells reproduce D350's event matrices and D353's `rev_5` ledger (27,316 trades, +43.38) exactly; the saved series reload to the reported statistics. |

## 6. Stop conditions

- **Q1 holds** → the `rev_5` 2% cell is the flat-by-default sleeve, its series in `data/`,
  its multiplicity six; its own out-of-sample design is written in the result (the holdout
  read is D357's and is not shared).
- **Q1 fails on the null** → the rare trigger is a sample of the 10% signal, not a sharper
  one; the sleeve is the 10% cell if that clears, else there is no flat-by-default sleeve
  on these triggers and the record says the always-invested book is the only construction
  that pays here.
- **Q1 fails on cost** (above both nulls, negative net) → the sleeve has edge and the
  published spread eats it; its breakeven half-spread is stated and it waits on D336.
- Nothing is promoted. Book: empty.

## 7. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | via the shared prep |
| **[G]** · **[ID]** | the 10% event matrices equal D350's members; the `rev_5` 10% cap ledger equals D353's (27,316 trades, +43.38 to 1e-9) |
| **[E]** | 300 sampled events per cell satisfy the definition on the raw lagged percentile at t−1 and t−2, and fail unlagged |
| **[HX]** | the hedged deployed series equals the per-trade ledger summed per bar to 1e-12; the unhedged likewise against raw returns |
| **[A′]** · **[B]** · **[C]** | every rotated event eligible and counts kept; date and bucket kept, defined-percentile pool; C's mean within 2 SE of zero |
| **[S]** | sign in money on an A′ ledger; favourable paths pay positively; a +50 bp move on a held name lifts the deployed series by 50/n_open on that bar |
| **[SER]** | each saved series reloads and reproduces the cell's deployed gross, net, Sharpe and exposure to 1e-12 |
| **[6]** | [HX] raises with the market term left in; [S] raises on a ledger handed +50 bp; [SER] raises on a perturbed file |

## 8. Files

`docs/decisions/D358-the-flat-by-default-sleeve-a-trigger-a-market-hedge-and-the-deployed-base.md`
(this record) · `scripts/run_d358_flat_sleeve.py` (stages `--selftest`, `--cell SCORE:P
--draws N --part p`, `--report`) · `data/d358_ctrl_*.json`, `data/d358_series_*.npz`,
`data/d358_flat_sleeve.json` (to follow). Reuses `scripts/d345_event_book.py` (with the
hedged series), `scripts/run_d353_rev5_record.py`, `scripts/run_d350_long_timing_screen.py`,
`scripts/run_d347_long_signal_controls.py`, `scripts/d348_prep.py`, `scripts/d322_four_group_report.py`.
