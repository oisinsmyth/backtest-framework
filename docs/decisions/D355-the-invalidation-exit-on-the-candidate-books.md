# D355 — the invalidation exit on the candidate books: a signal exit beside the target, on the two cells that pay

**Status:** PRE-REGISTERED. Committed **before the runner or the simulator edit exists** (R8).
Nothing here is a result. Nothing here is a book: the output is which exit the candidate
construction carries into the out-of-sample read.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. Why

The slot books exit on D303's target — the summed hedged excess reaching 0.96 of the name's
own vol — or on the hold cap. D295 closed the exit family on the slot book because a slot
refills behind any exit; D345 amended that: on an event book the target cuts the winner and
a **signal-invalidation exit** was worth +185 a trade over it. D353 measured the same exit on
`rev_5`: three times the per-bar yield of the cap. The two candidate books have never been
run with the exit that the record says is worth the most, and the slot simulator has no
signal exit. This record adds one, additively, and runs it on the two cells that pay net of
the published spread.

## 1. The exit

A position opened long on name i exits at the first bar t with age > 0 on which the name's
**lagged floored cross-sectional percentile of the same score** is **≥ 50**; a short exits
when it is **≤ 50**. The percentile is D347's `percentile_grid` of exactly the lagged score the
ranker ranks (`PCT` in the shared prep for `rsi` and `hist_L`), so the exit reads the signal's
own reversion through the median, known at the close of t−1. The hold cap stays. The
slot refills behind the exit as it always has.

Implemented as a keyword-only `invalidation=None` on `run_d306_width_exits.py::simulate`,
ORed into the existing exit decision and nothing else: with the keyword absent the simulator
must reproduce every published cell to 0.0.

## 2. The cells and the arms

`rsi` k=40 and `hist_L` k=40 under `keep_v2`, F0, the open fill, PUB and PB, GC/HTB:

| arm | exit |
|---|---|
| **target** | D303's target or the cap — the published cell; the identity arm |
| **invalidation** | the percentile crossing 50, or the cap; no target |
| **both** | target or invalidation, whichever first, or the cap |

Multiplicity six, stated. Both lenses, D348's 23 statistics.

## 3. The nulls, per arm

The 24 rank rotations of the observed gate, and control A′ — D348's per-name time rotation
of the score within its finite bars — **with the percentile grid recomputed from the rotated
score**, so the exit under the null reads the rotated signal and not the real one. 200 draws
per arm per cell in two parts, seeds `[SEED, 355, cell, arm, part]`.

## 4. Predictions

Q1 is load-bearing. Q6 is against.

| | prediction |
|---|---|
| **Q1** | *(load-bearing)* the invalidation arm's **PUB net bp/bar exceeds the target arm's** on **both** cells. |
| **Q2** | the invalidation arm is above the p95 of **both** nulls on PUB net bp/bar on both cells. |
| **Q3** | entries at least **double** under invalidation on both cells (the event lens holds 6.6 bars against 40). |
| **Q4** | the swap is edge-sharpening, not cost-cutting: gross bp/bar rises by **more than** cost bp/bar rises, on both cells. |
| **Q5** | the long leg's mean per trade **falls** under invalidation and its mean per bar held **rises**, on both cells. |
| **Q6** | *(against)* PUB net Sharpe rises on both cells. |
| **Q7** | the `both` arm's PUB net sits **between** the other two on both cells. |
| *check* | the target arm reproduces D346 to 0.0; the invalidation exit agrees bit-identically between the slot simulator and D345's kernel on the invariant lens. |

## 5. Stop conditions

- **Q1 and Q2 hold** → the invalidation construction is the candidate the out-of-sample read
  (D357) is spent on, as a **new** candidate entry — BOOK.md: a structural change to the rule
  is a new entry, tested from scratch — and D356's secondary arm.
- **Q1 fails** → the target stays; D357 reads the declared cell.
- **Q2 fails with Q1 held** → the invalidation arm earns more and is inside a null it must
  clear; the target stays and the record says why.
- Nothing is promoted. Book: empty.

## 6. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | via the shared prep |
| **[ID0]** | with `invalidation` absent the simulator reproduces D346's `rsi` and `hist_L` k=40 cells to 0.0 on every statistic (D348's identity), and D346's own self-test cells |
| **[IDX]** | with `invalidation=PCT`, `use_target=False`, `slots=False`, the slot simulator's ledger, counts and book equal D345's kernel with `exit="invalidation"` fed `rank < 2` and `PCT` as its score, bit-identically; the gate is empty wherever `PCT` is undefined, asserted |
| **[X0]** | on the same entries the target arm's exit bars are a subset of the `both` arm's |
| **[PC]** | the percentile grid of the rotated score equals an independent rebuild on 3 draws; the observed grid equals the prep's cached `PCT` |
| **[A]** · **[N]** | the rotation keeps every per-name and per-bar finite count and multiset; offsets non-zero on > 99% of names |
| **[L]** | lag audit on the observed and one rotated book, target and invalidation arms |
| **[S]** | sign in money on an invalidation-arm ledger, both lenses |
| **[6]** | [ID0] raises on a perturbed grid; [IDX] raises with `use_target=True` left on; [L] raises on the unlagged score |
| **[P]** | every part's stored observed statistics equal the re-simulated ones to 1e-9 |

## 7. Files

`docs/decisions/D355-the-invalidation-exit-on-the-candidate-books.md` (this record) ·
`scripts/run_d306_width_exits.py` (the additive keyword) · `scripts/run_d355_exit_swap.py`
(stages `--selftest`, `--cell SIG:K --arm A --draws N --part p`, `--report`) ·
`data/d355_ctrl_*.json`, `data/d355_exit_swap.json` (to follow). Reuses
`scripts/run_d348_score_rotation_null.py`, `scripts/d348_prep.py`, `scripts/d345_event_book.py`.
