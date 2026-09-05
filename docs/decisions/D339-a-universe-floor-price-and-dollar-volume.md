# D339 — a universe floor on price and dollar volume, as a definition and under both semantics

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). Nothing here is a
result. Written after the D339 census (a stage-0 diagnostic with no predictions, quoted in
§1 and committed with this record); its numbers fix the predictions below and nothing else.
**Date:** 2026-09-05
**Area:** Universe definition · strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. Why

D338 found the best book in the programme earns its P&L in names it could not have
bought: four of `retrace_leg`'s five largest trades are sub-$2 stocks in the bottom 7%
of the live cross-section by dollar volume, all below the dv28 cut the programme has
carried since D321. The fixture is dead-inclusive with no price or volume floor, and an
extreme-rank selector on such a universe finds the junk tail first. **The question is
whether that is one book's problem or the fixture's**, and the census answers it before
this record predicts anything.

The programme has one liquidity filter, dv28, and it is a *variant* with starve
semantics: a name that fails it leaves a hole in the gate. A **universe definition**
replaces the name. The two are different objects and the principal asked for both.

## 1. The census (stage 0, `scripts/d339_census.py`, `data/d339_census.json`)

All 46 dimensionless signals as symmetric F0 books at depth 2, k=20, variant lens, plus
the incumbent; every trade cut on its entry: **(a)** as-traded prior close below **$5**
(the adjusted close times the product of split ratios dated after the bar), **(b)**
below the dv28 cut at entry, **(c)** either. Shares are of contribution P&L.

| | |
|---|--:|
| live name-bars failing (a) / (b) / **(c)** | 7.7% / 27.6% / **29.3%** |
| sub-$5 share of live name-bars, 2010 → 2025 | 3.2% → 12.7% |
| books with **more than half** their P&L in cut (c) | **25 of 47** |
| top trades failing at least one floor | **35 of 47** |
| names supplying the top trade of 30 of the 47 books | nine: VSA, TAOP, AHT, RLOC, PRMW, WATT, CYCN, KODK, DRYS |

`retrace_leg`: 12.2% of trades entered below $5 (against 7.7% of the universe) average
**+805 bp** a trade against **+76** outside, and carry **61.3%** of the P&L; cut (c) is
33.8% of trades for 58.5% of P&L. `close_in_range`, the second book, takes 96% of its
P&L from the 66% of its trades in the cut. **The incumbent C0 is the least
floor-dependent book in the census** — 33% of P&L from 25% of trades, in/out means +62
and +49 — and its top trade is still VSA, entered two days earlier at $0.29.

**The concentration is the fixture's, not one signal's.** That is the justification for
a floor as a definition rather than a variant, and it is measured before any prediction
below is written. Where a book's total P&L is near zero the share columns are
arithmetic, not concentration; the census prints the in/out means beside them.

## 2. The floor, declared

`keep[t, i] = (RAW_CLOSE[t−1, i] ≥ $5) ∧ keep_mask(DV, finT, 28, bad_low=True)[t, i]`

- **Raw price** is the as-traded price: the adjusted close times the product of split
  ratios dated after t (the fixture divides prices by that product on the way in). A $5
  floor on the *adjusted* close would look through future reverse splits — VSA's $90.55
  adjusted close on 2025-01-30 was $0.18 as traded. The raw price at t−1 is what traded
  at t−1 and is known then; the reconstruction undoes a future adjustment and nothing
  else. **Both thresholds are existing round numbers** — $5 is D337's hard-to-borrow
  cut and the SEC penny-stock line; 28 is D321's carried threshold — so nothing here is
  a free parameter.
- **Dollar volume** is D320's lagged trailing-63 mean of close × volume, the 28th
  percentile of the live cross-section per bar, missing estimates never excluded.
- **Two semantics, run as separate cells, never averaged:**
  - **replace** — the floor masks the *score* before ranking, exactly as the F0 deal
    filter does; the gate stays full and the next-ranked liquid name takes the slot.
    This is the universe-definition reading and the primary cell.
  - **starve** — dv28's semantics: the floor is applied inside the rank cut
    (`gate_from(rankT, finT, keep)`); the excluded name leaves a hole, the book narrows
    at full notional, fill falls, turnover divides by names held (D321 [F]).
  The same `keep` array feeds both; their difference is what the vacated slot is worth.

## 3. Cells

| cell | signal | k | filter | floor |
|---|---|--:|---|---|
| RL0 / RL-r / RL-s | `retrace_leg` symmetric, depth 2, D303 target | 20 | F0 | none / replace / starve |
| C0 / C0-r / C0-s | the incumbent (N=2/target) | 5 | none | none / replace / starve |
| RSI0 / RSI-r · HL0 / HL-r | `rsi`, `hist_L` symmetric | 20 | F0 | none / replace |

Both lenses, PB and PUB (PUB primary), GC+HTB borrow as new keys. **Four-group report
on RL-r** via D322's functions with the top-five table carrying raw price and entry-day
dollar-volume percentile (D338's format, extended per FINDINGS §20); group 1 and the
top-five table for RL-s. **Null:** rank rotation inside the 25-name gate, 200 draws,
seeded `[W.SEED, 339]`, one simulation per draw costed under both conventions, on RL-r;
**teeth on the gross null** — p95 > 0 on gross bp/bar — with the matched-cost net null
reported beside it as the cost test and R7's flag defined on the gross null (D338 §2's
correction, applied for the first time). RL-s gets a null only if time allows; the
record says which. Close fill throughout; D340's open-fill companion is owed where these
numbers are next quoted.

## 4. Predictions

P3 is load-bearing. P6 and P9 are against.

| | prediction |
|---|---|
| **P1** | RL-r's PUB net falls from +18.93 by **more than 40%** — below +11.4 bp/bar. The census puts 58.5% of the unfloored P&L in the cut; replacement names earn something, not nothing. |
| **P2** | RL-r's top-5 name share falls **below 30%** (from 51.5%) and names-to-half rises **above 15** (from 5). |
| **P3** | *(load-bearing)* RL-r is **above the gross null's p95** — the ordering survives on names a book can hold. |
| **P4** | RL-r's symmetric 1% trim still clears the PUB round trip. |
| **P5** | RL-r's top trade is **< 5%** of the ledger and its entry-day dollar-volume percentile is **> 28**. |
| **P6** | *(against)* the incumbent C0-r moves by **less than 3 bp/bar** on PUB net — the census found it the least floor-dependent book, with in/out means of +62 and +49. |
| **P7** | C0-r's top trade is no longer VSA and its top-trade share falls **below 10%** (from 17.9%). |
| **P8** | fill stays 100% under replace; falls **below 90%** under starve for RL. |
| **P9** | *(against)* RL-s's PUB net is **below** RL-r's, and the gap between them is smaller than the drop from RL0 to RL-r. |
| *check* | the floor's share of live name-bars is **29.3%**, the census's number, to 1e-9. A reproduction, not a prediction. |

## 5. Stop conditions

- **P3 fails** → `retrace_leg` is a squeeze detector as `skew_63` was a takeover
  detector: an edge in a cohort the book cannot trade. **Retired as a book.**
- **P3 and P4 hold** → RL-r is the programme's **first liquid candidate**; the R8
  out-of-sample design is written (a fixture disjoint in names or time, predictions on
  net bp/bar and own-null p95 declared before the read) and **not run**. Book: still
  empty.
- **P6 fails** → the incumbent's history was a liquidity story too; D322's four-group
  report is re-read under the floor.
- **P9 fails** (starve beats replace) → the vacated slot's replacement is worth less
  than nothing, which would say the marginal liquid name in the gate is a loser; recorded
  and the replace cell's null is re-read.
- **Regardless of outcome, the floor becomes the declared universe for every study
  after this one.** It is a definition, and §1 is its justification; a study that wants
  the unfloored universe says so and reports both.

## 6. Assertions — properties of code

| | |
|---|---|
| **[1]** | RL0 reproduces D338's cells and C0 reproduces D333's new-panel cells to 1e-9 |
| **[K]** | cache key with `ragged_panel.py` in the tuple; npz newer than the builder |
| **[R]** | raw factor: 1.0 on every bar of a name with no splits on file; VSA 2025-01-30 raw close within 1e-3 of 90.55 × 0.002 |
| **[C]** | causality: the floor mask through bar t−1 is unchanged when every price and volume from bar t onward is perturbed, on 200 sampled bars (second implementation of the mask, never through `keep_mask`) |
| **[G]** | `keep = all-True` reproduces the unfloored cell bit-identically under BOTH semantics; fill is 100% under replace and < 100% under starve; the floor's share of live name-bars equals the census's 29.3% to 1e-9 |
| **[W]** | on 200 sampled bars, replace and starve enter the same names wherever the unfloored gate's top-2 per side all pass the floor |
| **[A]** | lag audit: the floored long-leg gate rebuilt from the raw score at t−1, the floor at t−1 and the base at t by a direct stable argsort equals the gate on 200 sampled bars; the unlagged rebuild differs on most |
| **[S]** | sign in money: every trade's P&L equals `sgn·Σ(v − mt)` from the ledger to 1e-12; a favourable excess path pays positively on every long and short |
| **[RQ]** | the summed ledger differs from `accumulate="compound"` on identical entries and exits; group 1 scores the summed one |
| **[2]** | ledger reconciliation (D322 [2]); rejects a ledger missing a trade |
| **[3]** | symmetric trim; rejects an asymmetric one |
| **[N]** | rotating the rank array moves the book; ≥ 195 of 200 draws valid |
| **[B]** | borrow per bar × `cnt1` equals per trade to 1e-9 |
| **[6]** | [1] raises on a book handed +5 bp on 200 masked bars |

## 7. Scope

**In:** the floor, both semantics, the eight cells, both lenses and conventions, borrow,
the four groups on RL-r, the null on RL-r. **Out:** any other threshold (no sweep — the
two numbers are inherited); the open fill (D340, run in parallel; both records quote the
close fill and the companion is owed where the number is next quoted); a long-only
hedged `retrace_leg` (conditional on P3); the holdout.

## 8. Files

`docs/decisions/D339-a-universe-floor-price-and-dollar-volume.md` (this record) ·
`scripts/d339_census.py`, `data/d339_census.json`, `data/d339_census.txt` (the census,
committed with this record) · `scripts/d339_universe_floor.py`,
`scripts/run_d339_universe_floor.py`, `data/d339_universe_floor.json` (to follow).
