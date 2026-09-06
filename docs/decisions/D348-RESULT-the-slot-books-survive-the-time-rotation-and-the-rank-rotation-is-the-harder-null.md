# D348 RESULT — the slot books survive the time rotation, their long legs do not carry cohort drift, and the rank rotation is the harder null

**Status:** RESULT. Pre-registered at `c1fe97b`, prep and runner at `27157f3` and `3acadf9` — all
before this file existed (R8). `keep_v2`, F0, next-open fill, D303's target exit, depth 2,
PUB primary, PB beside, GC/HTB borrow.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is promoted. The `rsi` candidate stands; the `hist_L` candidate record is now owed.**

---

## 1. The verdict

**Four of seven, and the load-bearing one held.** Every cell is above all 200 draws of
control A — each name's score rolled in time within its own finite bars, then re-ranked and
re-simulated — on every P&L statistic: gross bp/bar, PUB net, PB net, net after borrow, gross
Sharpe, PUB net Sharpe, and both legs' per-trade means on the invariant lens. The null that
D347 said the candidates had never faced does not take them.

| PUB net bp/bar | observed | **control A** p50 / p95 / max | draws below | rank rotation p50 / p95 / max | above k of 24 |
|---|--:|--:|--:|--:|--:|
| `rsi` k=40 | **+5.14** | −10.91 / −4.38 / +0.42 | 200 of 200 | −5.10 / +0.62 / +1.51 | 24 of 24 |
| `hist_L` k=40 | **+12.42** | −11.92 / −4.58 / +3.92 | 200 of 200 | −10.25 / −3.26 / +0.62 | 24 of 24 |
| `retrace_leg` k=20 | **+2.68** | −14.05 / −8.50 / −3.11 | 200 of 200 | −8.45 / −1.03 / +0.52 | 24 of 24 |

| gross bp/bar | observed | control A p50 / p95 / max | rank p50 / p95 / max |
|---|--:|--:|--:|
| `rsi` k=40 | +12.70 | −2.05 / +4.46 / +9.72 | +3.30 / +8.50 / +10.07 |
| `hist_L` k=40 | +26.73 | +0.21 / +8.10 / +17.13 | +0.78 / +10.14 / +11.56 |
| `retrace_leg` k=20 | +13.87 | −1.54 / +4.52 / +10.07 | +3.71 / +11.26 / +12.28 |

Control A's offsets are drawn independently per name, so its 200 draws are 200 distinct
books; the rank rotation has 24. The zero-offset draw reproduces D346's two k=40 cells and
D343's `retrace_leg` cell to 0.0 on every published statistic.

## 2. What the two predictions that failed say

**Q3 falsified, in the direction its stop condition named.** Control A's **long leg is centred
below zero**: −12.8 bp a trade for `rsi`'s names, −9.8 for `hist_L`'s, against observed +39.0
and +141.5. D347 found the opposite on the event ledger — the same names at random times
earned *more* than at the signal's times — and this record says why the slot book is
different. D347's control A kept each name's *events* and moved them: 23,491 `hist_L`
entries into the bottom decile across some 1,500 names, weighted by how often each name
fired. This record's control A moves each name's *score* and re-ranks: at a random date the
depth-2 gate selects whichever names' rotated scores are most extreme that day, which
over-selects names with long extreme stretches, held at moments unrelated to their true
state. Those trades lose. The observed book's long leg — the two most extreme names on the
day they are most extreme — earns +39 and +141 against that. **The slot book's long leg is
timing, not cohort membership.** D347's scope claim, that every per-trade positive in D335,
D344 and D346 was unmeasured against a time rotation, is now measured for the three cells
that matter, and they survive it. The claim is narrowed to what D347 actually tested: the
decile-entry event on every name.

**Q5 falsified: the time rotation is the easier null on a slot book.** On gross bp/bar its
p95 is below the rank rotation's on all three cells — +4.5 against +8.5, +8.1 against +10.1,
+4.5 against +11.3. The rank rotation keeps the day's gate and the day's cross-section and
permutes only the preference order inside it, so it preserves every same-day cohort effect
and every regime; the time rotation breaks those too. **For the slot books the rank rotation
stays the binding null.** Both are cleared, by every cell, on every statistic.

**Q4 falsified, half each way.** The short leg under control A is centred at −0.1 for `rsi`
(observed +46.5, above all 200) but at **+16.8 for `hist_L`** (observed +32.6, above 70% of
draws) and −1.0 for `retrace_leg` (observed +22.8, above 94.5%). Names with the highest
`hist_L` fall at random times: that short leg carries a cohort premium of its own, and its
observed +32.6 is not distinguishable from it. `hist_L`'s book is its long leg.

## 3. Turnover under the null

The observed cells enter less often than any rotated book: 847 entries for `rsi` against
901–985 under A, 771 for `hist_L` against 914–995. On the invariant lens the rotated books
carry 40% more trades per leg. A score aligned with its returns holds its positions to the
cap or the target; a rotated one is displaced sooner. The entry count is itself a signature
of alignment, and the record notes it without building on it.

## 4. Predictions

| | | outcome |
|---|---|---|
| **Q1** | *(load-bearing)* `rsi` k=40 PUB net above A's p95 | **CONFIRMED** — +5.14 vs −4.38; 200 of 200 |
| **Q2** | `hist_L` k=40 PUB net above A's p95 | **CONFIRMED** — +12.42 vs −4.58; 200 of 200 |
| **Q3** | A's long leg centred > 0; `hist_L`'s observed below A's median | **FALSIFIED** — A's long leg −12.8 / −9.8; observed above every draw |
| **Q4** | A's short leg centred < 0 on both k=40 cells | **FALSIFIED** — `rsi` −0.1, `hist_L` +16.8 |
| **Q5** | A's gross p95 above the rank rotation's on every cell | **FALSIFIED** — below it on all three |
| **Q6** | *(against)* `retrace_leg` k=20 above A's p95 | **CONFIRMED** — +2.68 vs −8.50 |
| **Q7** | gross Sharpe above A's p95 on a k=40 cell | **CONFIRMED** — 0.661 vs 0.274; 0.864 vs 0.365 |
| *check* | zero-offset == D346 / D343 | held, 0.0 on all three |

Four of seven.

## 5. Stop conditions, executed

- **Q1 and Q2 hold → the `hist_L` k=40 candidate record follows** (STACK §6 item 2): four
  groups, the top trade with its liquidity, both nulls, multiplicity 92. D342's `rsi` record
  gains the control-A line: above all 200 time rotations as well as all 24 rank rotations.
- **Q3 failed with A at or below zero on the long leg → the slot book's long leg does not
  carry cohort drift the way the event ledger did**, and D347's scope claim is narrowed in
  writing (STACK §7, FINDINGS §28 amended by §29).
- Nothing is promoted. Book: empty.

## 6. Deviations and what the run found

- **The first launch exhausted the machine.** Every runner in this programme imports its
  predecessor with the same four-line `_load`, and nothing memoises it: a process executed
  `d285_spread_estimate.py` 151 times and paid 164 s of import alone — 460 s with six
  competing — and 5 to 7.5 GB of resident memory before building an array of its own. Five
  such processes paged a 32 GB machine to a standstill twice. `scripts/memo_load.py` now
  wraps `importlib` so each script executes once per process (0.2 s, ~1 GB); the prep cache
  built under it is bit-identical to the one built without it on all 38 arrays, and [ID]
  holds to 0.0 under it. D347's "process parallelism hurt here" (§8) was this.
- **The prep is cached** (`scripts/d348_prep.py`, `temp/d348_prep/<key>/`, 943 MB, keyed on
  the fixture, both upstream caches and every estimator module's mtime; `--verify` asserts
  every key of D347's `prep()` bit-identical). A control process starts in seconds.
- The pre-registration's [S] "synthetic dividend" is implemented as a +50 bp move on one
  held bar, asserted to lift a long trade by +50.0 and cut a short by −50.0.
- `--report` runs all 24 rank shifts once each rather than 200 draws memoised to 24.

## 7. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | via the shared prep: cache keys; 1,719 filings, 2.54%; factor == census; `keep_v2` 30.9056% == D343 |
| **[ID]** | zero-offset cell == D346 (`hist_L`, `rsi` k=40) and D343 (`retrace_leg` k=20) to 0.0: PUB/PB net, gross, Sharpe, trades, bars, both legs |
| **[A]** | every draw keeps every name's finite count, every bar's finite count and every name's multiset exactly |
| **[5]** | the vectorised rotation == `np.roll` loop bit-identically on the real score (3 draws per cell) and a tie-heavy synthetic (20) |
| **[N]** | offsets non-zero on 99.83–100.00% of names with L ≥ 100 |
| **[L]** | the long gate == the rebuild from `score[:, t−1]` on 200 sampled bars, observed and rotated; unlagged differs on 200 of 200 |
| **[S]** | 5,339 invariant and 881 variant trades equal the open-fill recomputation to 3.3e-16; favourable paths pay positively; ±50.0 bp on the two legs |
| **[6]** | [L] raises on the unlagged gate; [A] raises on a whole-panel `np.roll` |
| **[P]** | every part's stored observed statistic equals the re-simulated one to 0.0 |

**Speed:** self-test 17 s; 1.9 s a draw, six processes at once, 3.5 min per 100-draw part;
report 76 s including the three rank rotations.

## 8. What this establishes

1. **The three candidate cells survive the per-name time rotation**, 200 of 200 on every
   statistic. The null D347 said mattered has now been applied to the slot books and does
   not take them.
2. **The slot book's long leg is timing.** The same kind of names selected at random times
   lose 10 to 13 bp a trade; selected on their day they earn +39 to +141. Cohort drift is a
   property of D347's event definition, not of the depth-2 book.
3. **On a slot book the rank rotation is the harder null**, because it keeps the day. Both
   are carried from here; the rank rotation remains binding.
4. **`hist_L`'s short leg is a cohort premium** (A centred +16.8, observed at the 70th
   percentile); its book is its long leg.

## 9. Files

`data/d348_ctrl_{rsi_40,hist_L_40,retrace_leg_20}_p{0,1}.json` · `data/d348_score_rotation_null.json`
· `scripts/run_d348_score_rotation_null.py` · `scripts/d348_prep.py` · `scripts/memo_load.py`
