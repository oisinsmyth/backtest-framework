# D574 — PRE-REGISTRATION: **the forward read of basis-momentum** (D564, PASS under the formation amendment) on the reserved slice **2024-01-02 → 2026-09-09**, on the principal's word; the amended and the as-pre-registered constructions side by side, the seasonal and non-seasonal roots split, the dollar book and its six-root sub-book, with the forward nulls

**Pre-registration. Committed before the runner exists and before any session from 2024 onward
is read for these constructions (R8).** Result in a separate file. **This record spends the
2024+ slice of the breadth fixture and the settlement strip for basis-momentum on the 17
commodity roots — every cell of D564's family, the as-pre-registered variant, the seasonal /
non-seasonal split, and the C-d sub-book.** Nothing is admitted by this record (R15).

*2026-09-20. The principal's instruction: "pre-register the basis-momentum forward read and run
it". D564 is the one construction in the futures-curve programme that passed its in-sample nulls
— +0.692 gross / +0.990 Sortino on 2016–2023, rank 0.972 in the time rotation, 0.971 in the
family maximum, 0.975 in the name-randomised null — and it passed only under an amendment made
after the read: the formation settlement read as the last finite within five sessions of the
month-end, which repaired two calendar defects (2020-06-30, 2021-05-31) that had voided twelve
month-ends each; as pre-registered it was +0.421 at rank 0.796. Two roots reached half the
profit, natural gas was in the short leg 81 of 83 months, the nine non-seasonal roots read
−0.09 standalone, and the dollar book was +0.36 net at σ $3,803 with its six-root sub-book
+0.48 at σ $340 — both under the C-a bar. Holdout multiplicity is per line: the NG, trend and
carry lines have spent their slices; this line has not read a session past 2023-12-29.*

---

## 1. What is read, and what is frozen

- **The constructions, frozen.** D564's runner functions, imported and not re-implemented:
  `strip_tables`, `nearby_series` (ffill 5 amended; ffill 1 as pre-registered), `signals_at_
  month_ends` (BM = 12-month first-nearby product minus second-nearby product), `membership_
  fixed` (High4 / Low4 on ≥ 12 eligible, ties by symbol), D555's holds and book return, D556's
  minimum-size dollar book. The 17 roots, BZ untraded in dollars, the energy delivery rule
  ≥ *m*+3 and the grains' ≥ *m*+2, the stale rule — all as D564 §0 fixes them.
- **The data.** The breadth fixture through its last session with D562's forward loader (BTC's
  weekend sessions from 2026-05-30 dropped, irrelevant to the commodity roots; the in-sample rows
  asserted identical to D555's loader's); the settlement strip unfiltered; the curve table for
  the harness only.
- **The harness, before any forward number is read.** The in-sample primary rebuilt on the full
  calendar must equal D564's artifact — **+0.692157 (amended) and +0.420717 (as pre-registered)
  on 2016–2023 to 1e-9** — and D556's cell A likewise (for the overlay). A harness that does not
  reproduce stops the run.
- **The forward window.** Every session from **2024-01-02** to the fixture's last (2026-09-09,
  D562's window: 696 sessions). Positions from the 2023-12-29 month-end (in-sample data, forward
  P&L) onward: about 32 positioned months.

## 2. The cells

| cell | | in-sample (D564) |
|---|---|---|
| **EW High4/Low4, amended — PRIMARY** | the passing construction | +0.692 / +0.990; N1 0.972, N3 0.975 |
| EW High4/Low4, **as pre-registered** (ffill 1) | the construction before the amendment | +0.421, rank 0.796 |
| EW terciles | D557's leg rule on BM | +0.545, rank 0.983 |
| time-series (sign of de-meaned BM, 0.40/σ) | | +0.219, rank 0.948 |
| dollar High4/Low4, 16 contracts at minimum size, net | the component candidate | +0.36 net, σ $3,803, HO 37 % |
| **C-d sub-book: CL GC HG NG SI ZC at minimum size, net** | declared in D564 as a subset; its forward is spent by this read | +0.48 net, σ $340 |
| seasonal contribution (NG ZC ZS ZW ZL ZM LE HE) and non-seasonal contribution (BZ CL GC HG HO PA PL RB SI) of the primary | the two sum to the primary | the nine non-seasonal roots standalone −0.09 |

**Family for N2: D564's four cells** (amended primary, terciles, dollar net, time-series). The
as-pre-registered variant and the splits are diagnostic.

## 3. The statistics and the nulls

> **PRIMARY: the amended EW High4/Low4 book's gross annualised Sharpe on 2024-01-02 →
> 2026-09-09**, monthly block-bootstrap SE, Sortino beside it; net beside gross; the ~32
> positioned months' distribution; per root, per sector, per year; worst and best day with the
> root that made them; the root-month distribution with symmetric 1 % trims.

- **N1-full (D562's forward null).** The held membership grid over the full span 2011 → 2026
  rotated by every common offset within each root's span, **scored on the forward window only**,
  purged 252 sessions at both ends of the full span, enumerated (SE 0), exactness guard on 20
  offsets. It asks whether the forward window's return is what any placement of this book's
  membership earns on these 32 months.
- **N3-forward (name randomisation).** At each forward month-end keep the leg sizes and draw the
  names from the eligible set; 2,000 draws, seed declared, bootstrap SE of the p95, D373's
  UNRESOLVED rule within 2 SE.
- **N2** — the family maximum over the four cells at each N1-full offset.

**Forward verdicts, declared:** **TRANSFERS** if the primary > 0, above N1-full's p95 and above
N3-forward's p95 by more than 2 SE; **INSIDE** if > 0 and not; **DID NOT TRANSFER** if ≤ 0;
**INVERTED** if below N1-full's p05.

## 4. Predictions — in the runner's quantities

| # | prediction | value declared | source |
|---|---|---|---|
| **P-1** (primary) | forward gross Sharpe **> 0**; point **0.2 – 0.7** | | the in-sample +0.69 shrunk for an amendment chosen after the read and two roots carrying half; a figure above the range is a miss |
| **P-2** (the amendment) | the as-pre-registered and amended forward books have **0 flat month-ends each** and forward Sharpes **within 0.05** | | the two defects were 2020 and 2021 calendar days; forward, the amendment should change nothing, and if it does the record says the construction depends on it |
| **P-3** (who carries it) | the **seasonal roots' contribution > the non-seasonal roots'**; the non-seasonal standalone book ≤ +0.2; **NG in the short leg at ≥ 75 % of forward month-ends** | | D564: NG short 81 of 83, non-seasonal −0.09 |
| **P-4** (concentration) | **two roots reach half** the forward P&L (top-2 share ≥ 0.5 of a positive total) | | D564: roots to half = 2 |
| **P-5** (the dollar books) | the 16-contract book **fails C-d** (σ > $500) with HO or NG the largest line; the **sub-book σ ≤ $500** and its forward net Sharpe within **±0.5** of its in-sample +0.48 | | in-sample σ $3,803 / $340 |
| **P-6** (overlay on carry) | c5 of the primary on D556 carry A's worst 5 % forward days **< 0** | | in-sample −0.29 σ; the book carries carry's tail forward too |
| **P-7** (falsifiers) | primary ≤ 0 → DID NOT TRANSFER; > 0 inside both nulls → INSIDE and no promotion; as-pre-registered and amended differing by > 0.1 → the amendment mattered forward; NG's contribution the largest single loss → the short-gas tilt was the in-sample result | | |

## 5. What the read settles and what it cannot

- **Settles:** whether the passing construction's return transfers to 32 unread months; whether
  the amendment mattered beyond the two days it repaired; whether the seasonal tilt and the
  natural-gas short were the return.
- **Cannot:** admit anything. The dollar book failed C-a and C-d in sample; the sub-book was a
  declared subset, not a construction, and its in-sample +0.48 is under the bar. A forward
  number cannot promote what did not clear in sample. What the read gives the sub-book is its
  forward figure, recorded, with its 2024+ spent; a future pre-registration of the sub-book as a
  construction would be written as seen with no clean test left on either window. The record
  says this so that the number cannot later be read as a promotion.
- **ρ with the ledger's arm:** absent (the MACD arm's daily P&L is not on disk); by instrument
  and clock expected near zero, an expectation.

## 6. Runner assertions

The forward loader's in-sample rows equal D555's loader's, row for row. The harness equalities
of §1 at 1e-9. D564's audits on the full-span objects — BM from the strip by a second path at 300
cells (proven to raise on a negated grid), leg membership by the pandas path (swapped pair), lag
(unlagged book), right quantity (daily grid), sign in money on the dollar book (negated and
mis-lagged), the held-contract share ≥ 99 % — each proven to raise. The 20-offset exactness
guard on N1-full; N3's draws checked for leg sizes. The runner **refuses to run without
`--principals-word`**, and the RESULT records the instruction it ran under. `REQUIRED_OUTPUTS`;
`max_drawdown_convention` first; `encoding="utf-8"` everywhere. Projected wall under five
minutes (nearby series ~100 s; ~3,900 offsets × 4 cells; 2,000 draws).

## 7. Spent

After this run the 2024+ slice is spent for basis-momentum in every form above on the 17
commodity roots, and for the C-d sub-book. Nothing else's slice is touched: the trend, carry,
NG-spread and NQ-day-session lines were spent by their own records; the grains' seasonal cells
and the livestock, heating-oil and crude avatars keep theirs.
