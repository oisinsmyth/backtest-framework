# D343 — the re-listing clause: a liquidity floor may not pass a name with no tape

**Status:** PRE-REGISTERED. Committed **before the module change and the runner exist**
(R8). Nothing here is a result. An amendment to the universe definition D339 declared.
**Date:** 2026-09-05
**Area:** Universe definition · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. Why

D342's top five included NBIS long on 2024-10-21 — the former Yandex's first day back
after an eight-month halt — at 4.4% of the candidate's P&L, with **no dollar-volume
percentile at entry**. The floor's dollar-volume clause is D320's `keep_mask`, whose rule
is *a name with no estimate is never excluded*, written so that a *spread* filter could
not become a liveness proxy. For a *liquidity* floor that rule is backwards: a name with
fewer than 21 trailing observations of dollar volume has no demonstrated liquidity, and
the floor exists to demand one. The hole is at re-listings and at every name's first
month of tape.

## 1. The amendment, declared

`keep_v2[t, i] = keep_v1[t, i] ∧ isfinite(DV[t, i])`

where `keep_v1` is D339's floor (as-traded close ≥ $5 at t−1 and the dv28 pass, replace
semantics) and `DV` is D320's lagged trailing-63 mean of close × volume, which is finite
only where at least 21 of the 63 prior bars carry a price and a volume. **Nothing else
changes.** `keep_v2 ⊆ keep_v1` by construction; the price clause and the percentile are
untouched; the missing-estimate rule stays in `keep_mask` for the spread filters it was
written for. `floor_mask_v2` is added to `scripts/d339_universe_floor.py` beside the
original, which stays for every identity that quotes it. **From this record on, the
declared universe is `keep_v2`.**

## 2. Cells

`rsi` F0 k=20, `retrace_leg` F0 k=20 and the incumbent C0 k=5, each under `keep_v1` and
`keep_v2`, open fill, both lenses, PB and PUB, GC+HTB. The `keep_v1` cells are identities
to D341 and D342. Reported on `rsi` v2: the four groups in D342's layout, the top five
with dollar-volume percentile, a 200-draw rotation null with the number of distinct
shifts stated. Also reported: the trades present in each v1 ledger whose entry cell fails
`keep_v2` — their count, their P&L, and their names.

## 3. Predictions

| | prediction |
|---|---|
| **Q1** | the clause removes **less than 1.5%** of live name-bars beyond D339's 29.30% — each name's first month and the re-listings. |
| **Q2** | *(load-bearing)* `rsi` under `keep_v2` stays **above its gross null's p95** and above **at least 22 of 24** distinct rotations; NBIS is not in its ledger. |
| **Q3** | `rsi`'s PUB net **falls, by less than 1.5 bp/bar** (NBIS was 4.4% of a +3.52 book). |
| **Q4** | `retrace_leg` v2 is within **1 bp/bar** of +2.68 and the incumbent within 1 of −13.41. |
| **Q5** | *(against)* the trades the clause removes from the three v1 ledgers have a **positive mean P&L** — the floor costs edge here, and pays for it in tradeability, not in return. |
| **Q6** | under `keep_v2` no top-five trade of any cell has a missing dollar-volume percentile. |
| *check* | every `keep_v1` cell reproduces D341/D342 to 1e-9; `keep_v2 ⊆ keep_v1` exactly. |

## 4. Stop conditions

- **Q2 holds** → `keep_v2` is the universe; D342's candidate status carries over to the
  v2 cell with the v2 numbers, and D342's out-of-sample design is amended to quote them.
- **Q2 fails** → the candidate did not survive a one-clause tightening of its own floor;
  its status is withdrawn and the record says so.
- **Q1 fails** (the clause removes more than 1.5%) → the clause is doing more than its
  name says and the record maps where before adopting it.
- **Q5 fails** (the removed trades lose on net) → the hole was costing money as well as
  honesty; recorded, no change to the amendment.

## 5. Assertions

| | |
|---|---|
| **[K]** | cache key; **[F0]** F0 counts; **[R]** raw factor and v1 share == census |
| **[V2]** | `keep_v2 == keep_v1 & isfinite(DV)` exactly; `(keep_v2 & ~keep_v1).sum() == 0`; the removed share equals `(keep_v1 & ~isfinite(DV) & finT).sum() / finT.sum()` |
| **[C]** | causality: `isfinite(DV[t])` is unchanged when every price and volume from bar t onward is perturbed, on 200 sampled bars |
| **[1]** | the three `keep_v1` open-fill cells reproduce D341 (RL, C0) and D342 (`rsi`) to 1e-9 |
| **[A]** | lag audit on `rsi` v2's long gate, 200 bars; the unlagged rebuild differs on most |
| **[S]** | every `rsi` v2 trade equals `pnl_recomputed_fill` to 1e-12; favourable paths pay positively |
| **[RQ]** | compound accumulation: same entries, different P&L |
| **[2]** · **[3]** · **[N]** · **[B]** · **[6]** | as D342 |

## 6. Files

`docs/decisions/D343-the-re-listing-clause-on-the-universe-floor.md` (this record) ·
`scripts/d339_universe_floor.py` (`floor_mask_v2`, additive), `scripts/run_d343_relisting_clause.py`,
`data/d343_relisting_clause.json` (to follow).
