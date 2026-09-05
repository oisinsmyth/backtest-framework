# D335 — the leg-wise book's legs, re-chosen under the deal filter and the published spread convention

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-05
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. Why

D329 built the first leg-wise book — `hist_L` long, `skew_63` short — and D331 retired
`skew_63` as a short: its edge was pinned takeover targets. D332 changed the default
spread convention to the published trailing mean (PUB). D333 corrected thirty
fabricated return days. **Every leg has to be re-read under all three**, and the
leg-wise construction, which stands, has no short leg.

## 1. Why legs, not pairs

D329's assertion `[L]` proved that a leg-wise book's ledger is the union of its
parents' legs, bit-identically, on both lenses. On the path-invariant lens, then, the
best pairing per trade is the best long leg plus the best short leg — **there is no
pair effect to enumerate**. Forty-six symmetric books give every signal's long-leg and
short-leg per-trade statistics; multiplicity is 46 per leg, reported as rank with the
p50/p95 of the 46, not 2,116 pairs.

## 2. The universe and the arms

- **Universe:** the F0 deal windows (`run_d331_deal_filter.filing_bars` on target forms,
  `exclusion_mask`, 189 bars from filing) removed from **every** score before ranking.
  The D333-bounded panel. The D334-rebuilt score cache (asserted, `[K]`).
- **Per-leg table:** the 46 dimensionless D290 signals, each as a symmetric book at
  depth 2, k=20, path-invariant lens: long-leg and short-leg `net`, `gross`, `t`, held
  half-spread, rebalancing premium, under PB and PUB. PUB is primary.
- **Book check:** the top-3 long legs × top-3 short legs by PUB per-leg net, as
  leg-wise books on both lenses, PB and PUB; `retrace_leg` symmetric under F0 as the
  incumbent best.
- **Cache impact:** `beta_63`, `ivol_21`, `signed_vol` per-leg nets on the rebuilt npz
  and on `temp/d290_scores_pre_d333.npz`.

## 3. Predictions

Q4 and Q5 are against. Q1 is the retirement, re-stated as a test.

| | prediction |
|---|---|
| **Q1** | `skew_63`'s short leg is **not** in the top 3 of 46 under F0 + PUB. |
| **Q2** | `hist_L`'s long leg **is** in the top 3 of 46 long legs under F0 + PUB. |
| **Q3** | `retrace_leg`'s long leg is in the top 3 too. |
| **Q4** | *(against)* **at least one** short leg nets > 0 per trade under F0 + PUB. |
| **Q5** | *(against)* the best top-3 × top-3 book beats `retrace_leg` symmetric (F0) on PUB net bp/bar. |
| **Q6** | the three rebuilt signals move by **< 1 bp/bar** on their symmetric books between the old and new cache. |

## 4. Stop conditions

- **Q4 fails** → no short leg on this fixture pays its own cost under the published
  convention once deal targets are removed. **The leg-wise book has no short leg**, and
  the short side of this programme is a cost problem before it is a signal problem.
  That is recorded as the finding, not worked around.
- **Q4 confirms and Q5 fails** → a positive short leg exists but pairing it with the
  best long leg does not beat the best symmetric book; the leg-wise construction is a
  per-trade result without a book-level one.
- **Q2 fails** → `hist_L`'s long leg was also carrying deal names; the incumbent's
  primary has no leg left.
- **Nothing is promoted.** The best pairing, if any, is a candidate for a separate
  pre-registered test (R8).

## 5. Assertions

1. **[1]** with no filter, under PB, D329's four arms reproduce D333's new-panel cells
   to 1e-9 on both lenses.
2. **[F]** the F0 mask reproduces D331's second-pass counts: 1,719 filings applied,
   2.54% of live name-bars excluded.
3. **[K]** the score cache is post-rebuild: `z['key'] == cache_key()` with
   `ragged_panel.py` in the tuple, and the npz mtime is newer than `ragged_panel.py`'s.
4. **[L]** each top pairing's ledgers equal its parents' per side, both lenses.
5. **[C]** per-leg `2c` is 2 × that leg's held median half-spread.
6. **[6]** the self-test raises on a leg handed free money.

## 6. Scope

**Out:** signals outside the 46 (the five dimensional ones stay out); pair-level
enumeration; borrow (D337); the holdout. **In:** the per-leg table, the nine books, the
cache-impact measurement.

## 7. Files

`docs/decisions/D335-the-legs-re-chosen-under-the-deal-filter.md` (this record) ·
runner and data to follow. Prior evidence: `data/d333_dividend_bound.json`,
`data/d331_deal_filter.json`, `data/d329_legwise.json`.
