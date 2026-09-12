# D457 — the 8-K item atlas with returns: 17 cells, both sides, cap 10, the state-matched and rotation controls on every cell; the 2024 slice stays shut

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file. **The
first forward-return look at corporate-event items in this repo.** In-sample on the mining fixture
2010–2023; **no holdout is read, and the 2024-01 to 2026-08 slice parsed by D456 stays unread**
— it is the family's confirmation set and is opened, if at all, under a later record on the
principal's word. D457 taken after `ls docs/decisions` and `git log --all` showed D456 last.

## 0. What is being tested

That the hedged return over the ten bars after an 8-K of a given item type differs from what a
random name in the same price × volatility × momentum cell on the same day earns, and from what
the same names earn on rotated dates — **on every item type at once, without picking a sign or a
cell in advance.** D456 established the events: 154,970 8-Ks, dead-inclusive, filed the same or
next day, 15 item cells with ≥ 300 filings.

## 1. The cells and the events (from `data/d456_8k_events.csv.gz`, frozen)

- **Cells:** the 15 items with ≥ 300 filings (1.01, 1.02, 2.01, 2.02, 2.03, 2.05, 2.06, 3.01, 3.02,
  3.03, 4.01, 5.02, 5.03, 5.07, 8.01) **plus 2.04 and 4.02 reported without a bar** (192 and 170).
- **Two versions of each cell:** **all** (every filing carrying the item) and **pure** (a single
  item other than 9.01). Both scored; the family count is over **all**.
- **Event:** one filing on one name, 2010-01-01 to 2023-12-29, name eligible at the availability
  bar; `mask[t_av, name] = True` with `t_av` the first bar strictly after `filingDate` (the fill is
  the open of `t_av`). **[F] asserted.** A name already held in a cell's book is not re-entered
  until its hold ends (the kernel's rule) — so the trade count is below the filing count where
  filings cluster.

## 2. The construction

D345's kernel through `run_d359`: **`exit = "cap"`, `cap = 10` bars (primary; corporate events
resolve in days), `n_max = None`, hedged, equal weight; both sides scored on every cell** (side 0
long, side 1 short with D337's borrow). **`cap = 3` reported.** Score panel constant.

**Two lenses per cell.** Per trade: the hedged pnl per trade (bp). The book: the **deployed** mean
of `book_dep_x` over the bars on which the cell holds anything (bp per bar deployed — a cell with
326 events is flat most days and a full-window mean would only measure sparsity), with a monthly
block-bootstrap SE over those bars. The two lenses are never compared to each other.

## 3. The two controls, on every cell

- **C1 — state-matched random names, per trade.** Each event replaced by a random eligible name
  in the same price × volatility × momentum tercile cell (D392's `tercile_pools` at the bar
  before availability) on the same day that has **no 8-K of any item within ±5 bars**; the same
  daily count; **100 draws on `all`, 50 on `pure`**; the long-side per-trade mean's p2.5 / p50 /
  p97.5 (the short side is its mirror, less borrow). Destroys the item; keeps day, count, cell.
- **C2 — the enumerated rotation of the cell's calendar, on the book.** The cell's event mask
  rolled by a common offset for every name, every 21 bars from 21 to T−21 (~160 offsets), the
  deployed mean re-computed; p2.5 / p50 / p97.5 exact on the grid. Keeps each name's event count
  and the composition; destroys alignment. **On `all` only** (the family count).

## 4. The bar — a cell **clears** when

- **its favoured side** (the sign of `real − C1 p50`) has a per-trade gross **beyond C1's p97.5
  (long) or p2.5 (short) by 2 MC-SE**, and
- its deployed book on that side is **beyond C2's p97.5 / p2.5**, exact on the grid.

Reported beside, not gated: per-trade **net crossed** (gross − 2c PUB − borrow on the short side)
and **net passive** on the favoured side; the `pure` version's C1 verdict; cap 3.
**The family is 17 cells × two sides at 2.5% a tail: about 0.85 cells clear C1 by chance and
about 0.04 clear both. The family verdict is the count that clears both against those numbers,
and every cell's numbers are printed whether or not it clears — no cell is dropped.** A cleared
cell is **not a candidate for anything until it reproduces on the unread 2024–2026 slice**, which
this record does not open.

## 5. Predictions (MODERATE on direction, LOW on size — the first look at every one of these)

- **X-a** cells clearing both controls on `all`: **2 to 4 of 17**, all on the **short** side, from
  {2.06 impairments, 3.01 delisting notices, 4.01 auditor changes, 3.02 unregistered equity sales,
  2.05 exit costs}; **no long-side cell clears both**.
- **X-b** the distress cells' short-side gross per trade at cap 10: 2.06 **+60 to +200 bp**, 3.01
  **+80 to +250**, 4.01 **+40 to +150**, 3.02 **+40 to +120**; C1 p50 within **±15** on every cell
  (a ten-bar cell drift is small); C1's 95% band about **±40 to ±120** wide depending on n.
- **X-c** the large cells are flat: 2.02 (earnings, no surprise sign) **|gross| < 20**, 5.02
  **−10 to −40** (short favoured, does not clear C2), 8.01 / 1.01 / 5.07 / 5.03 **|gross| < 15**;
  2.01 completed acquisitions **0 to +30**; 2.03 **−20 to +10**; 1.02 **−20 to −80** (short).
- **X-d** C2's median deployed mean is within **±0.5 bp/bar** of zero on every cell (a ten-bar
  composition drift is small) and its 95% band is **±2 to ±8 bp/bar** on the small cells.
- **X-e** cost: on the cells that clear, 2c PUB is **80 to 130 bp** (they are thin) and per-trade
  **net crossed is positive on at most two cells**; passive net positive on all that clear.
- **X-f** cap 3 gross per trade is **≥ 60% of cap 10's** on the cleared cells (front-loaded) and
  cap 3's per-bar deployed mean exceeds cap 10's; `pure` versions of 2.06 and 2.05 are **stronger**
  than `all` (the earnings co-filings dilute them).

## 6. Not in scope

The 2024–2026 slice; any holdout; 8-K text; 6-K filers; any selection among cells beyond the
declared bar. Forty-ninth look by object; look #1 of the corporate-event line's forward-return
ledger, priced as a family of 34 tests.

## 7. Files

This record · `scripts/run_d457_8k_atlas.py` (`--run [--quick]`, `--selftest`) ·
`data/d457_8k_atlas.json` · RESULT.
