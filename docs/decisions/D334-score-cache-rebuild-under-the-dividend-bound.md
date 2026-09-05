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

*(filled from the agent's report)*

## 5. Files

`scripts/d290_build_cache.py`, `scripts/run_d299_ladder.py`, `scripts/run_mine_neutral.py`
(key lists) · `temp/d290_scores.npz` (untracked) · `temp/d290_scores_pre_d333.npz`
(untracked, deletable after D335)
