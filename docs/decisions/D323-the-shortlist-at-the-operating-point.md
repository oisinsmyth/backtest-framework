# D323 — D290's shortlist, read at the operating point

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. A framing I proposed and withdrew before writing this

I first pitched this study on the observation that **`hist_L` — the signal the
whole stack rests on — sits 11th of 13 on D290's cost-coverage column at 0.20×,
while `price_log` (1.96×) and `choch_dist` (2.43×) cleared cost outright in the
same table.**

**The repo had already priced both, and I should have checked before saying it.**

- **`price_log` is "a 1.9%-turnover static tilt, whose time-rotation null barely
  destroys anything"** (`d291_walkthrough.py`). Its cost coverage is a turnover
  artefact — D293's seventh cut names it explicitly: *"a cost ratio without
  turnover is unreadable (gate 1g, and what made `price_log` look solvent)"* — and
  its min z of +3.64 is measured against a null with **no teeth**, which is R7's
  named pathology.
- **`choch_dist` at N = 5 is underpowered by construction.** D291 found 18 cells
  producing no statistic and *"every one of the 18 is `choch_dist` (N=5) or
  `rev_21` (N=3)"*, because the four-way intersection a paired difference needs
  collapses at small N.

**So the cost-coverage column is not a ranking.** It mixes `k` — a 40-bar hold
turns over eight times less than a 5-bar hold at the same width — and its top
entry's nulls are toothless. `hist_L` being 11th on it is not evidence that a
better signal was passed over.

## 1. What IS untested, and it is narrower

**Every candidate in D290 was scored at ITS OWN best cell** — `N` from 3 to 50,
`k` from 1 to 40 — and D293 chose between two of them at **N = 25, k = 5**.

**The book now runs at `N_eff` = 2, `k` = 5.** No candidate has been read there.

That matters because **concentration selects on a signal's RANK PROFILE, not its
average.** D301 measured edge per position falling **27.64 → 11.27 bp** from top-2
to top-19, so a candidate that ranks well *averaged over 25 names* is not
necessarily the one that ranks well *at positions 1 and 2*. **Six studies varied
how much of the book to hold. None varied what goes into it, and the thing that
went into it was chosen at a width the book abandoned.**

**And D289's amendment deliberately deferred magnitude** — D290 says the
cost column is *"reported, never used to rank"*. **That deferral was never picked
back up.** This study picks it up, at the operating point, with D318's costing.

## 2. The grid

- **Candidates:** the **13 tier-1 spread candidates** published in D290 —
  `price_log`, `macd_hist`, `rsi`, `dist_52w_high`, `on_persist`, `rev_5`,
  `choch_dist`, `retrace_leg`, `skew_63`, `macd_line`, `hist_L`, `rev_21`,
  `dist_lvn` — **plus the incumbent confluence** as the baseline. Fourteen.
- **Width fixed at `N_eff` = 2.** The operating point, not re-chosen.
- **`k` ∈ {5, 10, 20, 40}**, because `k` is the cost lever and each candidate
  peaked at a different one. D296 established that at fixed `N` the round trip
  does not depend on `k`, so this axis moves turnover and nothing else.
- **`dv28` on and off**, a declared axis. This satisfies D321's guard that any
  study using dv28 report the cell with and without it.

**14 × 4 × 2 = 112 cells.**

**Build risk, declared:** the runner must rebuild each candidate's rank array from
`RF.VOL_SCORES` / `PR.PROFILE_SCORES` and must be able to vary `k`. **Any
candidate that cannot be rebuilt is dropped and NAMED in the result**, not
silently omitted.

## 3. Statistics

**Net Sharpe primary**, costed per [D318](D318-the-stack-recosted.md): per-cell
held-name round trip, IBKR per-share commission, and **turnover on the names HELD**
(D321's `[F]`).

**Null: D321's circular rotation**, not a paired difference. **D291's power
failure was specific to the four-way intersection a paired difference needs**, and
this study operates at exactly the small `N` where that collapsed.

**Multiplicity priced at the EFFECTIVE test count**, per D321's amendment: the
candidate books are correlated, so BH over 112 nominal tests would correct for
tests that do not exist. The runner computes `M_eff` by Li-Ji and Cheverud-Nyholt
from the correlation matrix of the cells' own returns and **reports BH at both the
effective and the nominal count.**

**R7 IS ENFORCED PER CANDIDATE.** Every cell reports its null's **p50 and p95**,
and **any candidate whose null is centred negative is flagged as untrustworthy
regardless of its p** — that is `price_log`'s known defect and it must not pass
unremarked a second time.

## 4. Controls

- **The incumbent confluence** at the same operating point — the comparison that
  decides the study.
- **A raw-price factor control**, ranking on `close` alone. **`price_log` must be
  shown to differ from it**; if it does not, it is the price level, which
  [D284](D284-the-overnight-long.md) died of and [D320](D320-RESULT-the-tilt-axis-closes-and-the-filters-were-width.md)
  guarded against.

## 5. Predictions

Two are against, and Q2 is load-bearing.

| | prediction |
|---|---|
| **Q1** | each candidate reproduces D290's published cell at its own `(N, k)`, and the incumbent reproduces D293's at N=25/k=5. **A harness check — if it misses, nothing else is read** |
| **Q2** | **no candidate beats the incumbent at the operating point on net Sharpe, after the effective-`M` BH correction.** *Against — load-bearing.* "Beats" means beats **while profitable and surviving its own null** |
| **Q3** | **the candidate ranking changes materially between D290's own-best cells and `N_eff` = 2** — Spearman ρ below 0.7. **This is the study's premise: if the ranking does not move, re-screening was pointless and D290's choice stands untouched** |
| **Q4** | **`price_log` is not distinguishable from the raw-price control**, and its null is centred negative — R7's pathology, already recorded |
| **Q5** | `choch_dist` produces a usable statistic at `N_eff` = 2 under the rotation null, where D291's paired difference could not. *If it fails too, the small-N problem is the design's and not the statistic's* |
| **Q6** | the cost-coverage ranking at fixed `k` differs from D290's `× bar` column, because that column mixed `k` |
| **Q7** | **`dv28` helps every candidate or none** — its effect is signal-independent. *If it helps only the incumbent, it was fitted to it* |

## 6. Stop conditions

- **Q2 confirms and Q3 confirms** → the ranking *does* move with width and the
  incumbent still wins at the operating point. **D290's choice is vindicated at a
  width it was never tested at, and the entry axis closes on a measurement.**
- **Q2 fails** → a different signal wins where the book actually runs. **That is
  the largest finding this programme could produce at this stage**, and it needs
  its own pre-registered confirmation before anything else. It is not a promotion.
- **Q3 fails** → the ranking is width-invariant, the study's premise was wrong,
  and re-screening adds nothing. Say so and close.
- **Q1 fails** → misimplemented; nothing else is read.

## 7. Assertions

1. **[1] Reproduction**, two ways: each candidate at its own D290 cell, and the
   incumbent at D293's N=25/k=5.
2. **[F] FILL** — turnover on the names **held**; the check FAILS against the
   nominal-slot form.
3. **[S] SPREAD BASIS** — round trips from the names held; rejects the universe
   median.
4. **[2] CAUSALITY** — every candidate's score is lagged, and a peeking variant
   must produce a different book. **R9 has fired three times in this programme,
   twice on `hist_L`**, and this study rebuilds thirteen scores.
5. **[3] `k` BITES** — turnover falls monotonically in `k` at fixed `N`, and the
   round trip does **not** move with `k` (D296's structural finding).
6. **[R7] NULL QUALITY** — every candidate's null p50 and p95 are reported, and a
   negative-centred null is flagged.
7. **[C] Cost dimensions** against d295's 52.1893; doubled form rejected.
8. **[4] Every cell is a distinct book.**
9. **[5] The self-test raises** on a book handed free money inside the mask.

## 8. Scope

**Out:** any candidate not in D290's published tier-1 spread list — **no new
mining**; the exits beyond inheriting `target`; the gate; width; the overlay;
and the holdout.

**This study re-reads an existing, already-null-tested shortlist at the width the
book actually uses.** It cannot promote anything. **If Q2 confirms, the entry axis
closes and the programme has exhausted every surface it can test on this fixture
without spending a holdout read.**

## 9. Files

`docs/decisions/D323-the-shortlist-at-the-operating-point.md` (this record) ·
runner and data to follow, in separate commits. Prior evidence:
`data/d290_stage1.json`, `data/d293_candidate.json`, `data/d318_stack_recost.json`,
`data/d321_dv_sweep.json`, `data/d321b_effective_tests.json`.
