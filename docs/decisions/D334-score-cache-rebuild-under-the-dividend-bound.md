# D334 — the score cache rebuilt under the dividend bound

**Status:** INFRASTRUCTURE NOTE, written before the rebuild runs. No predictions; the
assertions below are the deliverable, and the numbers are filled in from the run.
**Date:** 2026-09-05
**Area:** Data integrity · follows D333

---

## 0. Why

D333 bounded the panel's dividend adjustment; `panel.total_log_returns` changed on
30 cells. Three of D290's 51 scores read it — `signed_vol` (`ragged_features.py:147-151`,
via `sub.total_log_returns`) and `beta_63` / `ivol_21` (through
`AN.market_return(panel.total_log_returns, live)`, `d290_build_worker.py:102`) — and
the score cache `temp/d290_scores.npz` is therefore stale for them. Its key
(`d290_build_cache.cache_key`) hashes nine estimator scripts and the fixture but **not
`ragged_panel.py`**, so nothing noticed. The same omission is in
`run_d299_ladder.cache_key` and `run_mine_neutral._cache_key`.

Ten runners verify the key and refuse on mismatch; about forty (every runner from D295
to D333) load the npz and never check it. Adding the file to the key protects the ten;
the rebuild is what fixes the forty.

## 1. What is done

1. `temp/d290_scores.npz` is copied to `temp/d290_scores_pre_d333.npz` **before**
   anything else (D335's Q6 reads it).
2. `"ragged_panel.py"` is added to the key tuples in `d290_build_cache.py`,
   `run_d299_ladder.py`, `run_mine_neutral.py`.
3. `d290_build_worker.py --verify` must pass (chunk == whole, bit-identical incl. the
   NaN pattern).
4. `d290_build_cache.py --procs 8`, full fan-out — `--reuse-chunks` is **not** safe
   because C and G are computed inside the chunks.

## 2. Assertions (a rebuild that changes the wrong thing is worse than no rebuild)

| | |
|---|---|
| **[K]** | the new npz's `key` equals `cache_key(FIXTURE)` with `ragged_panel.py` in the tuple |
| **[W]** | `warm` is bit-identical old → new |
| **[U]** | every score EXCEPT `beta_63`, `ivol_21`, `signed_vol` is `array_equal(equal_nan=True)` old → new — 48 of 51 |
| **[Δ]** | each of the three DOES differ; the fraction of finite cells changed and the max \|Δ\| are reported per score |
| **[M]** | the merge is a partition (the builder's own check, `d290_build_cache.py:126-130`) |
| **[V]** | one key-verifying runner loads the new npz without raising |

## 3. Side effects, budgeted

`temp/d303_cache` and `temp/d306_cache` are keyed on the npz mtime and rebuild on the
next run (~22 s + a gate build of 1–2 min). `temp/d299_cache` and the D288 cache are
now also keyed on `ragged_panel.py` and rebuild when next used.

## 4. Results

**Rebuilt 2026-09-05, 420 s wall-clock** (8 processes, 294–327 s per chunk; fast
families 52 s; 2.69 GB). `--verify` passed first: chunk == whole on all 27 slow-family
scores, bit-identical including the NaN pattern. `--reuse-chunks` was not used.

| | |
|---|---|
| **[K]** | new key == `cache_key(FIXTURE)`; `ragged_panel.py` in the new key, absent from the old |
| **[W]** | `warm` bit-identical, (1573, 4187) |
| **[U]** | **48 of 48** other scores bit-identical (`equal_nan=True`) |
| **[M]** | merge is a partition — all 1,573 rows written exactly once |
| **[V]** | `run_stage1_rerun.py`'s key check passes on the new npz |

**[Δ] — and the footprint of the three is very unequal:**

| score | finite cells | changed | share | max \|Δ\| | names touched |
|---|--:|--:|--:|--:|--:|
| `signed_vol` | 4,089,807 | 86 | **0.00%** | 3.82 | 19 |
| `ivol_21` | 4,105,779 | 521,962 | **12.7%** | 0.0024 | 1,573 |
| `beta_63` | 4,039,713 | 1,222,296 | **30.3%** | 0.16 | 1,573 |

`signed_vol` reads a name's own returns, so thirty bad cells moved 86 cells — the
thirty plus their rolling shadow. **`beta_63` and `ivol_21` go through the
cross-sectional market return**, so thirty fabricated days moved the market factor on
those bars and re-priced **every name**: a third of all beta cells, with a max shift of
0.16 in a beta. **The forty runners that never checked the key were reading a beta and
idiosyncratic-vol panel that was stale everywhere, not on thirty cells.** Any study that
ranked on `beta_63` or `ivol_21` before this rebuild (D290's screen, D330 A's long-leg
table for those two) is to be read with that in mind; neither was in D323's thirteen.

NaN patterns are unchanged for all three. Old npz kept at
`temp/d290_scores_pre_d333.npz` (2,693,752,677 B; the new one is 108 bytes longer — the
extra key line). Files: `scripts/d334_cache_diff.py`, `data/d334_cache_diff.txt`.

## 5. Files

`scripts/d290_build_cache.py`, `scripts/run_d299_ladder.py`, `scripts/run_mine_neutral.py`
(key lists) · `temp/d290_scores.npz` (untracked) · `temp/d290_scores_pre_d333.npz`
(untracked, deletable after D335)
