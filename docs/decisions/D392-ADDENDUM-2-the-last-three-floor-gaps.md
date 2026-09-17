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

[D391 RESULT](D391-RESULT-the-reclaim-is-worth-less-than-no-reclaim-and-the-edge.md)
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

---
---

# RESULT — the gaps are closed, and eleven of D391's twelve cells turn out to sit inside the null's own spread

**Status:** RESULT, appended 2026-09-09. Runner: `scripts/run_d392_atlas_gapfill.py` ·
Artifact: `data/d392_atlas.json` (**193 → 199 cells**).
**6 cells, 3,000 kernel runs, 6.1 minutes** against a serial projection of 24.6.
**Holdout reads: 0.** A MEASUREMENT: **admits nothing (R15). Ledger contribution: 0.**

## R1. The six cells, all of them (R14)

| n | cap | side | trades | p05 | p50 | **p95** | ± SE | max |
|--:|--:|---|--:|--:|--:|--:|--:|--:|
| 100,000 | 5 | long | 87,672 | −2.34 | +0.02 | **+2.52** | 0.19 | +4.49 |
| 100,000 | 5 | short | 87,676 | −2.58 | −0.19 | **+2.20** | 0.11 | +4.03 |
| 150,000 | 5 | long | 123,936 | −2.28 | −0.00 | **+2.09** | 0.08 | +3.70 |
| 150,000 | 5 | short | 123,937 | −2.18 | −0.04 | **+2.22** | 0.09 | +3.75 |
| 200,000 | 1 | long | 199,950 | −0.64 | +0.00 | **+0.64** | 0.05 | +1.19 |
| 200,000 | 1 | short | 199,950 | −0.68 | −0.03 | **+0.78** | 0.04 | +1.22 |

**Every p50 is within 0.19 bp of zero**, which is the atlas's standing finding restated at sizes it
had never reached: *the p95 rises with cap but the centre is ~0* (D392 Q4).

## R2. The three gaps, closed

`lookup` raised on all three of these yesterday. It now interpolates between two measured cells:

| | observed (D391, corrected) | **floor p95** | ± SE | ratio | bracketed by |
|---|--:|--:|--:|--:|---|
| **cap 5, long** | +4.97 | **+2.43** | 0.19 | **2.05×** | 87,672 – 123,936 |
| **cap 5, short** | +2.89 | **+2.21** | 0.11 | **1.31×** | 87,676 – 123,937 |
| **cap 1, short** | +1.06 | **+0.83** | 0.05 | **1.28×** | 149,962 – 199,950 |

**[X] the lookup still raises outside the grid** — `lookup(400,000, cap 5, long)` was asserted to
throw. The atlas states what it measured and does not extrapolate.

## R3. Predictions: four held, one split, one FAILED

| | verdict | |
|---|---|---|
| **Q1** p95 falls monotonically on all four new curves | **SPLIT** | three of four fall. **cap 5 short RISES** 55,304→87,676→123,937 as +3.00 → +2.20 → **+2.22**. The +0.02 is inside 1 SE (0.09–0.11) so the two cells are indistinguishable, but **the prediction as written says "monotonically" and it is not** |
| | | the sub-clause also missed: cap 5 long at 123,936 was predicted below +2.0 and came in at **+2.09** |
| **Q2** cap 5 long ∈ [+2.0, +3.0]; D391 at 1.7×–2.5× | **HELD** | **+2.43**, ratio **2.05×** |
| **Q3** cap 5 short ∈ [+1.2, +1.9]; D391 at 1.5×–2.4× | **FAILED, both halves** | **+2.21**, above the band; ratio **1.31×**, below it |
| **Q4** cap 1 short ∈ [+0.78, +0.86]; D391 at 1.2×–1.4× | **HELD** | **+0.83**, ratio **1.28×** |
| **Q5** sides differ < 0.3 bp at cap 1, < 1.5 at cap 5 | **HELD** | 0.14 at cap 1; 0.32 and 0.13 at cap 5 |
| **Q6** every `se_p95` below 0.30 | **HELD** | 0.04 – 0.19 |

**Q3 is the informative failure and it went against D391, not for it.** My extrapolation took the
slope from the 28,761 → 55,304 leg, which is the steep part; **the p95 curve flattens above
~90,000 trades** and I read a straight line through a bend. The floor came in *higher* than
predicted and D391's cap-5 short margin *thinner* — **1.31× where I said 1.5×–2.4×.**

## R4. The completeness check, and it reframes D391's whole table

`--d391table` reads the merged atlas against `data/d391_fill_and_decay.json`. **Every cell D391
reported now has an in-grid floor; nothing is interpolated past.** But printing the null's *spread*
beside its p95 — CLAUDE.md: *"the distribution, not the percentile alone"* — changes how the table
reads:

| cap | side | trades | observed | floor p95 | ratio | the null's p05 … max | |
|--:|---|--:|--:|--:|--:|---|---|
| 1 | long | 144,582 | +0.60 | +0.83 | 0.73× | −0.98 … +1.75 | inside |
| 2 | long | 118,498 | +1.05 | +1.48 | 0.71× | −1.52 … +3.40 | inside |
| 3 | long | 106,657 | +2.90 | +1.76 | 1.65× | −2.08 … +5.33 | inside |
| **5** | **long** | **94,198** | **+4.97** | **+2.43** | **2.05×** | −2.34 … **+4.49** | **above all 500 draws** |
| 10 | long | 78,808 | +6.50 | +3.72 | 1.74× | −3.09 … +7.00 | inside |
| 20 | long | 61,818 | +8.00 | +6.38 | 1.25× | −4.23 … +13.02 | inside |
| 1 | short | 167,179 | +1.06 | +0.83 | 1.28× | −0.74 … +1.66 | inside |
| 2 | short | 135,945 | +2.06 | +1.20 | 1.72× | −1.56 … +2.53 | inside |
| 3 | short | 121,730 | +2.36 | +1.60 | 1.48× | −1.80 … +4.56 | inside |
| 5 | short | 106,888 | +2.89 | +2.21 | 1.31× | −2.58 … +4.03 | inside |
| 10 | short | 87,881 | +1.99 | +3.05 | 0.65× | −3.80 … +5.65 | inside |
| 20 | short | 67,350 | +5.63 | +3.54 | 1.59× | −6.71 … +10.40 | inside |

> **Nine of twelve cells sit above their p95 floor — and ELEVEN of twelve sit inside the range 500
> uniform draws actually produced.** Only cap-5 long exceeds every draw.

**What that does and does not license.** Being below the max of 500 draws is a weak statement on
its own — the max is roughly a 99.8th percentile and almost anything short of a real edge fits under
it. **The p95 is the decision threshold and by that threshold nine of twelve are above it.** The
column is here because *"1.25× the floor"* reads like a margin and **+8.00 against a null that
produced +13.02 in 500 tries** does not. Both are true; only together are they honest.

**None of this moves D391's verdict, and the addendum said in advance it would not.** D391 died on
`B_r`, its **same-pool** control — undercut-and-reclaim against undercut-and-closed-below, a
**−7.6 bp** difference at every horizon. A uniform draw does not share that event family's nuisance
(D291), and D392 §6a already named the reason the uniform ratios look wide: these events sit on
**large-intrabar-range bars**, which is a pool the atlas does not carry. **The gap-fill buys
reporting completeness, not a re-litigation.**

## R5. Cost, against the projection

| | projected | actual |
|---|--:|--:|
| serial work | 24.6 min | **30.9 min** |
| wall, 6 processes | ~5 min | **6.1 min** |
| speed-up | 5.0× | **5.08×** |
| efficiency | 82% | **85%** |
| peak WS per worker | — | **0.28–0.32 GB** |
| total Python WS, machine-wide, mid-run | ≤ 10 GB budget | **1.78 GB** |

The per-cell work came in 26% above the one-draw calibration — a single draw underestimates,
because the trades list grows through the cell. **The efficiency floor was cleared with margin and
the principal's 10 GB headroom was never approached.**

## R6. Assertions, all of them discharged

| | |
|---|---|
| **[SELFTEST]** | the parent's own `selftest()` called, not copied: `[N]` exactly n cells drawn, `[E]` none off the eligible mask, `[SE]` no p95 without its SE, `[X]` both proved to raise |
| **[K]** | `score_once` == `run_d359`'s own path to 0.0 (1,966 trades, **−22.892659 bp**); a changed score does not change a cap-exit ledger |
| **[G]** | `prep(need_grids=False)` **bit-identical** to `need_grids=True` at cap 20 long, cap 5 short and cap 1 short on the same 2,000-event probe |
| **[SHARD]** | the tiny plan as subprocesses == the same plan as one serial loop, every field but wall time, to 0.0 — **and a p95 perturbed by 1e-12 IS CAUGHT** |
| **[P]** | every shard written before anything was rendered |
| **[M]** | **all 193 pre-existing cells byte-identical** after the merge; count 193 → 199 |
| **[B]** | all three targets resolve; `lookup(400,000, cap 5, long)` still raises |
| **guard** | `--merge` **refuses** any plan but `gaps`, so the 20-draw proof cells can never reach `data/` |

## R7. What is still owed on the atlas

- **Cap 60 above 26,991 trades.** Deliberately not run: no record has asked for it. Named in §2 so
  the omission stays deliberate.
- **Pools the atlas lacks**, unchanged from D392 §7 — including the one D391 actually needed,
  *names on a large-intrabar-range bar*. **The atlas cannot pre-compute every pool.**
- **The 193 cells written before 2026-09-09 remain non-reproducible** (§3a). They were not
  recomputed and this record does not propose recomputing them; the defect is now on the record in
  both this addendum and D392 RESULT §7.
- **Sector, dead-vs-alive, era, the intraday fixtures** — deferred since the spec, still deferred.

---

**Status footer, 2026-09-09.** A measurement. No strategy was scored, nothing was admitted, no
avenue was opened or closed (**R15 — only the principal does that**), and **no holdout read was
spent.** `docs/BOOK.md` holds S1 and S2, neither at capital; `docs/BOOK_PROP.md` is empty.
