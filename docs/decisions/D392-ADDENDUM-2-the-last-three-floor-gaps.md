# D392 ADDENDUM 2 — the last three floor gaps: cap 5 both sides, cap 1 short

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). **Nothing here is a
result.** No cell scored. This is a **MEASUREMENT** extension of D392's grid: it scores no
strategy, proposes no rule and **admits nothing (R15). Ledger contribution: 0.**

**Date:** 2026-09-09 · Parent: [D392 RESULT](D392-RESULT-the-base-rate-atlas.md) §7 ·
Spec: [D392](D392-the-base-rate-atlas.md) · Requested by the principal.

**No holdout testing. Holdout reads spent by this record: 0. Programme total: 1** (D371).

**Build (R16):** unchanged from D392 — `load_ragged(dividend_bound=True)`, `keep_v2` floor, F0,
next-open fill, `EB.simulate_event` via `run_d359`. Same fixture, same seed base, same statistic
(gross mean bp per trade, hedged by the floored market, no cost, no borrow).

---

## 1. The gaps, named with the exact numbers that need them

[D391 RESULT](D391-RESULT-the-reclaim-is-worth-less-than-no-reclaim-and-the-edge-was-the-event-bar.md)
§"The corrected ledger against every atlas floor" states:

> *"**Three cells have no floor** — cap 5 either side, and cap 1 short at 167,179 trades — because
> the grid's trade axis does not reach there at those caps. **Named rather than interpolated
> past.**"*

That sentence is the whole of this record's motivation, and it has been carried forward unresolved
into [D393 ADDENDUM](D393-ADDENDUM-the-primary-cell-in-money.md) §4, D396 §4 and `PICKUP.md`.

| gap | the observed number needing a floor | atlas trade axis at that cap | verdict today |
|---|--:|---|---|
| **cap 5, long** | **94,198** trades, +4.97 bp | [99 … **55,305**] | `lookup` **raises** |
| **cap 5, short** | **106,888** trades, +2.89 bp | [99 … **55,304**] | `lookup` **raises** |
| **cap 1, short** | **167,179** trades, +1.06 bp | [100 … **149,962**] | `lookup` **raises** |

Observed numbers from `data/d391_fill_and_decay.json` (`decay`), which is the corrected ledger —
**not** the withdrawn +43.02.

**Why the axis stops where it does.** `COUNTS` tops out at 60,000 for caps 5 and 60; the two
extensions since (`EXT_COUNTS` = 100,000/150,000 at caps 10/20/40, and `SHORT_CAPS` = 1/2/3 over
the full count grid) each covered the cell that was blocking work at the time and neither touched
cap 5. Cap 1 was extended to 150,000 on the assumption that *"a one-bar event book on this
universe reaches ~130,000 trades"* (`run_d392_base_rate_atlas.py:78`) — **D391's short side reaches
167,179 and that assumption was simply wrong.**

---

## 2. The six cells, frozen before any statistic is seen

| kind | n | cap | sides | draws |
|---|--:|--:|---|--:|
| uncond, pool ALL | **100,000** | **5** | long, short | 500 |
| uncond, pool ALL | **150,000** | **5** | long, short | 500 |
| uncond, pool ALL | **200,000** | **1** | long, short | 500 |

**Six cells, 3,000 kernel runs.** `DRAWS_UNCOND = 500` is unchanged — the principal's ruling of
2026-09-08 — so the new cells are directly comparable to the 193 already stored.

**Cap 1 long is included although nothing currently needs it.** D392 Q2 asks whether long and
short floors differ, and a one-sided extension cannot answer that at the new size. It costs ~3
minutes.

**Cap 60 is NOT included.** Its axis also stops at 60,000 (26,991 trades), but no observed ledger
in the programme has asked for a cap-60 floor above that, and this record does not extend a grid
speculatively. **Named here so the omission is deliberate rather than forgotten.**

**R14: all six cells will be reported.** There is no selection among them — the count of cells is
fixed by the three gaps, not by what the numbers turn out to be.

### 2a. What has ALREADY been read, disclosed rather than buried

A **one-draw trade-count probe** was run at each (n, cap) before this record was written, to size
the grid. **It read trade counts only; no return statistic, no p95, no p50 was computed or seen.**
This is exactly what `--calibrate` exists to do and it is the same information `trades_mean`
publishes afterwards.

| probed | trades on one draw |
|---|--:|
| n=100,000, cap 5 | **87,645** |
| n=150,000, cap 5 | **124,038** |
| n=200,000, cap 1 | **199,954** |

**All three gaps are bracketed on both sides**, which is the point — `lookup` interpolates
log-linearly between two measured cells and **raises** outside them, so a gap is only closed by a
cell *above* the target:

- cap 5 long, 94,198 ∈ (87,645, 124,038) ✓
- cap 5 short, 106,888 ∈ (87,645, 124,038) ✓
- cap 1 short, 167,179 ∈ (149,962, 199,954) ✓

---

## 3. Two changes to the shared runner, declared because they change what a re-run produces

### 3a. THE SEED WAS NEVER REPRODUCIBLE, and this fixes it going forward

`run_d392_base_rate_atlas.py:346` seeds each cell with

```python
rng = np.random.default_rng([SEED, c["n"], c["cap"], hash(c["side"]) % 97, hash(c["pool"]) % 97])
```

**`hash()` on a `str` is salted per interpreter process.** Two runs of the same command therefore
draw different events for the same cell. This does not bias anything — every draw is uniform over
the same eligible index either way, which is all the atlas claims — but it means **the 193 stored
cells cannot be reproduced bit-identically, and the record has never said so.**

**It is being fixed to an explicit code map** (`SIDE_CODE`, `POOL_CODE`) in the shared runner, with
the defect named in a comment. **No stored cell changes** — the run loop skips any key already in
the atlas, and the merge step asserts byte-identity of every pre-existing cell. **The six new cells
are reproducible; the 193 old ones remain what they are, and this record is where that is
recorded.**

### 3b. `need_grids=False`, and it must be PROVEN not assumed

The parent runner calls `prep(need_grids=True)`. `need_grids` gates only `P["F"]`, the percentile
grid, whose sole consumer is `tercile_pools` — and every cell here is `pool="ALL"`. Dropping it
loads in ~1 s.

**This is my optimisation, so it carries its own assertion:** `[G]` a probe ledger under
`need_grids=False` must equal the same probe under `need_grids=True` **bit-identically**, or the
runner stops. An unproven speed-up that changes a published floor is exactly the class of error
this programme keeps paying for.

---

## 4. Cost, stated before launching (CLAUDE.md)

Measured, one draw per cell, on this machine:

| n | cap | s/draw | × 500 |
|--:|--:|--:|--:|
| 100,000 | 5 | 0.585 | 4.9 min |
| 150,000 | 5 | 0.541 | 4.5 min |
| 200,000 | 1 | 0.348 | 2.9 min |

**Serial projection: 24.6 minutes.** The kernel is `simulate_event`'s pure-Python double loop over
bars and open positions — **GIL-bound**, so threads are the wrong tool (CLAUDE.md).

**The optimisation pass: six processes, one per cell**, each writing its own shard, merged
afterwards. Sharding is by *cell*, and each cell already owns an independent RNG stream, so the
shard boundary is exactly the stream boundary.

> **Projected wall time: ~5 minutes at ~82% efficiency** (24.6 min of work over 6 × ~5.0 min).
> Below the 70% floor the run reverts to serial.

**Memory:** `prep` is mmap'd and loads in 1 s; the per-process cost is the draw mask (~6.6 MB), the
eligible index (~32 MB) and the trades list. The run is capped at six workers to leave the
principal's stated 10 GB headroom, and working-set is checked mid-run and reported.

---

## 5. Assertions the runner must carry

- **[SELFTEST]** the parent's own `selftest()` is called, not reimplemented — it carries `[N]` the
  draw is exactly n cells, `[E]` none off the eligible mask, `[SE]` no p95 without its bootstrap
  SE, and `[X]` both of those proved to **raise** on a deliberately broken input.
- **[K]** `score_once` equals `run_d359`'s own path to 0.0 on a 2,000-event probe, and a changed
  score does not change a cap-exit ledger.
- **[G]** §3b's `need_grids` equivalence, bit-identical.
- **[SHARD]** a cheap plan (n=2,000, cap 5, both sides, 20 draws) computed **as one serial loop**
  equals the same plan computed **as separate subprocesses**, cell for cell, to 0.0. Stride is the
  cell; prove chunk == whole before spending the real run (CLAUDE.md).
- **[P]** every shard persisted before anything is rendered (D371; D391 repeated it).
- **[M]** the merge adds only new keys: every pre-existing key compares byte-identical after.
- **[B]** after the merge, `lookup` resolves all three target trade counts **where it raised
  before**, and the raise is demonstrated on a count still outside the grid.

**No cell is reimplemented.** `draw_mask`, `score_once`, `summarise`, `eligible_index`, `cell_key`
and `lookup` are imported from `run_d392_base_rate_atlas.py`.

---

## 6. Predictions, written before the runner exists

The p95 falls with trade count throughout the stored grid (a mean over more trades has less
dispersion). Extrapolating log-linearly from the two nearest stored cells on each curve:

| | prediction |
|---|---|
| **Q1** | **p95 falls monotonically with trade count on all four new curves.** cap 5 long: +3.34 → below +2.6 at 87,645 → below +2.0 at 124,038. cap 1: +0.86 → below it at 199,954 |
| **Q2** | **cap 5 long at 94,198 lands in [+2.0, +3.0]**, so D391's corrected **+4.97 stays above its floor, at 1.7×–2.5×** |
| **Q3** | **cap 5 short at 106,888 lands in [+1.2, +1.9]**, so D391's **+2.89 stays above, at ~1.5×–2.4×** |
| **Q4** | **cap 1 short at 167,179 lands in [+0.78, +0.86]** — so D391's **+1.06 sits barely above a uniform draw, at 1.2×–1.4×**, which is the tightest margin any D391 cell will have |
| **Q5** | at cap 1 the long and short floors differ by **< 0.3 bp**; at cap 5 by **< 1.5 bp** (D392 Q2 re-tested at sizes it never reached) |
| **Q6** | every new cell's `se_p95` is **below 0.30**, because SE shrinks with trade count and the largest stored SE at n ≥ 100,000 is 0.39 |

**Q4 is the one that matters and it is declared against interest for D391.** If cap-1 short lands
where predicted, the cell D391 could only mark *"no floor"* turns out to be the one closest to
being pure base rate — which **strengthens** D391's corrected verdict rather than softening it.

**A result in the opposite direction on any of these is reported as such and counts against the
extrapolation.**

---

## 7. The bias caveat that applies to every number this will produce

**A SAMPLE p95 IS BIASED TOWARD THE CENTRE** (CLAUDE.md; D373's rule). A 500-draw p95 is therefore
**more lenient than it looks**, and these floors are if anything too low. Every cell carries
`se_p95`; **a margin within 2 SE of a floor is UNRESOLVED, not a pass.**

**These cells are NOT enumerable.** The exact-enumeration escape (D361/C2b) applies to a time
rotation of one market-level series, ~4,000 offsets. A uniform draw of 100,000 cells from ~4 M
eligible cells is not a finite group; only more draws touch the bias here, and 500 is the
programme's standing choice.

---

## 8. What this record will NOT do

- **It will not admit anything, and it does not revive D391.** D391 died on `B_r`, its **same-pool**
  control, which said the reclaim underperforms at every horizon. A uniform floor does not share
  that event's nuisance (D291) and never decided it. Closing these gaps changes the *reporting* of
  D391's table, not its verdict.
- **It will not extend the grid anywhere else**, including cap 60, and will not add pools. D392 §7
  stands: *"the atlas cannot pre-compute every pool"*.
- **It will not close a research avenue.** Only the principal does that (R15).

---

**Status footer.** No runner exists. `docs/BOOK.md` holds S1 and S2, neither at capital;
`docs/BOOK_PROP.md` is empty. Nothing here is a result.
