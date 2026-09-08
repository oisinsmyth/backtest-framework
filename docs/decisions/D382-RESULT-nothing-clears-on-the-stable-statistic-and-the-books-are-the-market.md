# D382 RESULT — nothing clears on the segmentation-stable statistic, and the books are the market

**Date:** 2026-09-08
**Pre-registration:** [D382](D382-the-market-structure-screen-on-the-liquid-universe.md), committed `e4a36b0`, amended `886c9fe` — **both before the runner produced a verdict** (R8).
**Runner:** [`scripts/run_d382_structure_screen.py`](../../scripts/run_d382_structure_screen.py).
**Fixture:** `data/fixtures/etf_wide_daily_raw.csv.gz` — built and gated for this study (`e22350a`).
**Artifacts:** `data/d382_observed.json`, `data/d382_nulls.json`, `data/d382_scores.npz`.
**No holdout was read, and none could be:** §1's reserved window is guarded default-deny with no override.

---

## 0. The verdict

**§8's second abandon condition fired: nothing beats buy-and-hold at matched exposure, so this is
D290's result on a new universe and is written as one.**

**551 names, 2,516 mined bars (2010-01-04 → 2019-12-31), 1,671 reserved. 19 features × 4 holds × 2
tails = 152 cells.** Buy-and-hold at unit exposure earns **+6.63% CAGR, Sharpe +0.283**.

| hold | best observed **per trade** | rotation p95 | permutation p95 | clears? | best observed **bp per bar** | rot p95 | perm p95 | clears? |
|---:|---:|---:|---:|:--|---:|---:|---:|:--|
| 5 | +31.56 | +31.84 | +38.22 | **no** | 5.672 | 5.087 | 7.361 | **no** |
| 10 | +77.73 | +70.25 | +68.75 | *yes* | 5.584 | 4.538 | 6.426 | **no** |
| 20 | +181.67 | +190.01 | +192.82 | **no** | 4.186 | 4.435 | 4.964 | **no** |
| 40 | +846.75 | +850.36 | +1616.57 | **no** | 3.386 | 3.962 | 4.213 | **no** |

**On the segmentation-stable statistic — bp per bar held — nothing clears at any hold.** The single
apparent survivor, hold 10 on the per-trade mean, fails on the stable statistic, and §2 shows why the
per-trade number cannot carry a verdict here.

**And the permutation floor sits ABOVE the rotation floor on the rate at every hold.** Randomising
*which names* occupy the extreme decile produces a **better** per-bar book than the real feature
does. That is not a weak signal; it is the absence of cross-sectional information.

---

## 1. The excess over buy-and-hold, which is the hurdle for a directional book

**74 of 152 cells have positive excess — about half, which is what a coin flip produces.** The best:

| cell | excess vs B&H | CAGR | B&H matched | exposure | trades |
|---|---:|---:|---:|---:|---:|
| `close_in_range\|5\|lo` | **+1.079%** | +3.58% | +2.50% | 0.363 | 60,396 |
| `wick_asym\|5\|hi` | +0.924% | +3.47% | +2.54% | 0.369 | 62,392 |
| `lower_wick\|5\|lo` | +0.837% | +3.31% | +2.48% | 0.359 | 59,057 |
| `struct_trend\|20\|lo` | +0.766% | +2.46% | +1.69% | 0.244 | 10,529 |
| `mass_here\|40\|lo` | +0.608% | +4.65% | +4.04% | 0.594 | 7,404 |

**A best-of-152 cell earning +1.08% CAGR over its own matched buy-and-hold, on a spent fixture, with
no null cleared, is not a signal.** It is the top of a distribution whose median is zero.

**And the cost arithmetic that motivated the whole study does not rescue it.** The move to ETFs was
right about cost — a round trip here is ~6 bp against the single-name universe's ~151 — but **the
edge that cost was supposed to reveal is not there.** That is a cleaner negative than the single-name
work ever produced, because cost cannot be blamed for it.

---

## 2. The defect that changed how everything reads

**`lower_wick|40|hi` — the headline "+846.75 bp per trade" — has a mean run length of 306 bars
against a nominal hold of 40.**

Overlapping events **merge into one continuous position**: a name that fires again while already held
does not open a second trade, it extends the first. So the per-trade mean is inflated by **event
density** as well as by hold, and a "40-bar trade" can run for three hundred bars of drift.

| cell | per trade | **bp per bar** | mean run |
|---|---:|---:|---:|
| `lower_wick\|40\|hi` | +846.75 | **+2.765** | **306.2** |
| `lower_wick\|40\|lo` | +638.55 | +2.878 | 221.9 |
| `mass_here\|20\|lo` | +127.99 | **+3.086** | 41.5 |

**Normalised by exposure the ranking inverts** — the "best" cell is the worst of the three — **and
every one sits within a whisker of buy-and-hold's own ~2.6 bp/bar.**

**This is [D374](D374-RESULT-the-breadth-bar-was-unreachable-and-it-failed-the-most-diversified-book-in-the-null.md)'s
confound one level deeper than D374 found it.** D374 showed a per-trade statistic is confounded with
*hold length*; this shows it is also confounded with *event density*, which the hold does not bound.

**Two things follow, and the second is the one that mattered:**

1. **The within-hold null comparison stays fair**, because both sides merge identically — the floors
   in §0 are valid.
2. **The floor could not be taken ACROSS holds.** My first null pass did exactly that and produced a
   best-of-152 floor of +840 bp, set entirely by the 40-hold cells. Corrected before any full run to
   a **best-of-38 within each hold**, which is what §0 reports. The uncorrected version would have
   compared a 5-bar book against a 40-bar book's floor.

---

## 3. Predictions, scored

| | prediction | outcome |
|---|---|---|
| **Q1** | at least one of 19 clears all three nulls at some hold | **FALSIFIED on the stable statistic** — nothing clears bp/bar at any hold. On the per-trade statistic one cell clears at hold 10, and §2 shows that statistic cannot carry it |
| **Q2** | *against the study:* fewer than 3 survive gate 1e | **UNRESOLVED** — §8's buy-and-hold condition fired first and closed the study before capturability was needed. **My predicted killer was the wrong one**: the nulls and B&H closed it, not 1e |
| **Q3** | axis H survives better than axis B | **UNRESOLVED**, same reason. *Observationally* axis B tops the excess table (`close_in_range`, `wick_asym`, `lower_wick`, `upper_wick`) — the opposite of the prediction — but with nothing clearing a null that ordering adjudicates nothing |
| **Q4** | no cell beats B&H at matched exposure by more than 2 SE | **HELD in substance** — best +1.079% on a best-of-152 grid, 74 of 152 positive, median ≈ 0 |
| **Q5** | gate 1d′ passes | **UNRESOLVED** — not computed; there was no survivor to test for independence |
| **Q6** | the best cell's hold is 20 or 40, not 5 | **FALSIFIED** — four of the top five are hold **5** |
| **Q7** | `[SPLIT]` and `[LAG]` both hold on the first run | **HELD** — and `[X]` proved `[SPLIT]` raises on an untruncated panel *and* on one whose grids were cut but whose bar lists were not |

**Two falsified, one held, four unresolved because the study closed earlier than the gates they
concern.** Recorded as unresolved rather than quietly dropped.

---

## 4. What this closes, and what it does not

**Closes:** the market-structure feature family — axes B, D and H — as a **stage-1 long-flat
cross-sectional screen on the liquid daily ETF universe**. Nineteen features, four holds, both tails,
three nulls, and the strongest thing available is a best-of-152 cell at +1.08% CAGR over its own
matched benchmark with no null cleared.

**Does not close:**

- **The features at intraday frequency.** Everything here is daily bars; the family's move may live
  inside the session, which is where D290's capturability failures pointed and which this fixture
  cannot see.
- **A declared-direction version.** Gate 1h was **failed** by this study (amendment `886c9fe`): the
  direction was declared for the book and not for each feature's end, so both tails were scored and
  the floor doubled to best-of-152. A study that declares each end in advance faces a best-of-76
  floor — **materially easier, and legitimately so.**
- **Anything about the reserved window.** 2020-01-01 onward was never touched and remains available
  for a study that earns it.

**No holdout was read. Nothing is admitted to either book.**

---

## 5. What it cost, and what it bought

The study needed a prerequisite nobody had built: **the repo had no gated ETF fixture, daily or
intraday** — `universe_wide_w1_raw` had no meta at all, and four others carried a meta whose `gates`
block was empty. The cached ETF data could not be gated either, having been fetched as
`TIME_SERIES_DAILY` with no adjusted close, split coefficient or dividend.

So `etf_wide_daily_raw` was fetched and built for this study: **551 names, 2,215,437 rows, gate_a and
gate_b clean, max single-session move ×2.07.** It outlives the study and is the first gated ETF
fixture in the programme.

**Standing caveat on everything built from it:** `MIN_DEAD_SHARE` is **0.0** here against the
single-name fixture's 0.15, because the ETF pool measures **4.0% dead**. Survivorship bias in a
long-flat ETF book runs **in your favour**.

---

*Result committed separately from the pre-registration, per R8.*
