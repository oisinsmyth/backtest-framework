# D348 — control A on the slot books: each name's score rotated in time, re-ranked, re-simulated

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). Nothing here is a
result. Nothing here is a book: the output is whether the candidate cells survive the one
null they have never faced.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. Why

D347 found that every long signal's excess is cohort membership, not timing: the same names
held at random dates earn more than the signal earns. The control that showed it — a
per-name rotation in *time* — has never been applied to a slot-book cell. The slot books'
null since D300 is a circular shift of the rank assignment inside the gate on the same day
(24 distinct shifts), which is D347's control B, the one the long signals beat. So the
`rsi` candidate's +5.14 PUB bp/bar at k=40, the `hist_L` book's +12.42, and `retrace_leg`'s
+2.68 at k=20 are each "above all 24 rotations" against a null that does not carry cohort
drift. This record puts the time rotation on all three. STACK §6 item 1 names the first
two; the third is added so that the whole candidate list faces the same null (a widening of
one cell, stated here).

## 1. The cells

Under `keep_v2`, F0, the next-open fill, D303's target exit, depth 2 (lowest two scores long,
highest two short), PUB primary and PB beside, GC/HTB borrow on the short leg:

| cell | published (D346 / D343) | status |
|---|--:|---|
| `rsi` k=40 | +5.14 PUB, Sharpe 0.27 | declared candidate (D342, D344) |
| `hist_L` k=40 | +12.42 PUB, Sharpe 0.40 | best of 92, unnulled, candidate record owed (D346) |
| `retrace_leg` k=20 | +2.68 PUB, Sharpe 0.14 | formal candidate with its own recommendation against an OOS read (D339, D341) |

The runner rebuilds each cell exactly as D346 did (`run_d346_legs_floor_open.py::run_cell`)
and asserts it reproduces the published numbers to 0.0 before any draw.

## 2. The null, exactly

The cell's score is `sc = apply_floor_replace(where(excl, NaN, z[sig]), keep)` — the raw
per-name value with the deal filter and the floor as NaN, shape (n, T). **Control A:** for
each name, its finite values are circularly shifted in time by an offset drawn uniformly on
`[0, L_i)` where `L_i` is the number of bars on which that name's score is finite; the shift
is *within* those bars, so the NaN pattern — the floor, the deal filter, the warm-up, the
delisting — is untouched. The rotated score then goes through the unchanged pipeline:
`rank_single` (the one-bar lag lives there), `gate_from`, `simulate` on both lenses, and
the costing. Per name the multiset of values is preserved; per bar the count of finite
names is preserved; every offset is independent across names, so the distinct draws are
effectively unbounded (the rank rotation has 24).

What this null carries that the rank rotation does not: each name's own unconditional
excess, its beta, its volatility, its era membership and its cohort membership — the same
names are held, at times unrelated to their score. What it destroys: the alignment of a
name's score with its subsequent return. A cell above this null has *timing*; a cell inside
it is holding a cohort.

**200 draws per cell**, RNG keyed `[SEED, 348, cell, part]`, in two parts of 100 for
parallelism. The 24-shift rank rotation is run beside it on the same cell so the record
shows both nulls on one table (FINDINGS §28, rule 1: every candidate carries both).

## 3. Statistics

Per draw, variant lens: gross bp/bar, PUB net bp/bar, gross Sharpe, PUB net Sharpe, bars,
entries. Invariant lens: the long leg's and the short leg's mean bp per trade and their
counts. The observed cell's statistics are reported beside each null's p50, p95 and max,
and the fraction of draws the observed exceeds.

## 4. Predictions

Q1 is load-bearing. Q6 is against.

| | prediction |
|---|---|
| **Q1** | *(load-bearing)* `rsi` k=40's **PUB net bp/bar** is above control A's p95. |
| **Q2** | `hist_L` k=40's PUB net bp/bar is above control A's p95. |
| **Q3** | control A's **long-leg per-trade mean** is centred **above zero** for both k=40 cells (cohort drift enters the slot book through the long leg), and the observed long-leg mean of `hist_L` k=40 is **below** control A's median — D347's pattern reproduced inside the slot book. |
| **Q4** | control A's **short-leg per-trade mean** is centred **below zero** for both k=40 cells: the short side pays the cohort premium at random times. |
| **Q5** | control A's p95 on **gross bp/bar** is above the rank rotation's p95 for every cell — the time rotation is the harder null. |
| **Q6** | *(against)* `retrace_leg` k=20's PUB net bp/bar is above control A's p95. |
| **Q7** | the observed **gross Sharpe** is above control A's p95 for at least one of the two k=40 cells. |
| *check* | the zero-offset draw reproduces D346's `hist_L` k=40 and `rsi` k=40 and D343's `retrace_leg` k=20 to 0.0 on net bp/bar, Sharpe, trades and both legs' per-trade means. |

## 5. Stop conditions

- **Q1 fails** → the `rsi` candidate is amended in D342's record: the null it never faced
  takes it; the OOS design is not run. Nothing else on `rsi` until a timing claim survives A.
- **Q2 fails** → no `hist_L` candidate record; STACK §6 item 2 closes.
- **Q1 and Q2 hold** → the `hist_L` candidate record follows (four groups, top trade with
  liquidity, both nulls, multiplicity 92), and D342's record gains the control-A line.
- **Q3 fails in the direction of A centred at or below zero on the long leg** → the slot
  book's long leg does not carry cohort drift the way the event ledger did; the record says
  so and D347's scope claim ("every per-trade positive in D335, D344 and D346 is unmeasured
  against it") is narrowed in writing.
- Nothing is promoted. Book: empty.

## 6. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | cache keys; F0 counts; raw factor == census; `keep_v2` share == D343 |
| **[ID]** | the zero-offset cell equals the published cell to 0.0 (D346 for k=40, D343 for `retrace_leg` k=20): PUB and PB net bp/bar, Sharpe, trades, bars, both legs' per-trade means |
| **[A]** | for every draw: per-name finite count, per-bar finite count and per-name sorted values of the rotated score equal the original's exactly |
| **[5]** | the vectorised rotation equals a `np.roll` loop, on the real score for 3 draws and on a tie-heavy synthetic score (integers 0–3, 30% NaN) for 20 |
| **[N]** | offsets are non-zero for > 99% of names with L ≥ 100 |
| **[L]** | lag audit: the held long set is re-derived from `score[:, t−1]` by a second implementation that never calls `rank_single`, on the observed book and on one rotated book |
| **[S]** | sign in money on a rotated ledger: a favourable move pays positively; long and short legs move oppositely on a synthetic dividend |
| **[6]** | [L] raises on a book fed the unlagged score; [A] raises on a whole-panel `np.roll` |
| **[P]** | `--report` asserts each part's stored observed statistic equals the re-simulated one to 1e-9 |

## 7. Files

`docs/decisions/D348-control-A-on-the-slot-books-the-score-rotated-in-time.md` (this record) ·
`scripts/run_d348_score_rotation_null.py` (stages: `--selftest`, `--cell SIG:K --draws N --part p`,
`--report`) · `data/d348_ctrl_{sig}_{k}_p{part}.json`, `data/d348_score_rotation_null.json`
(to follow). Reuses `scripts/d348_prep.py` (the cached prep shared with D349 and D350),
`run_d346_legs_floor_open.py`'s cell construction, `run_d291_confluence.py`'s vectorised
rotation, `d322_four_group_report.py`, `run_d329_legwise.py`, `run_d338_…`'s borrow block.
