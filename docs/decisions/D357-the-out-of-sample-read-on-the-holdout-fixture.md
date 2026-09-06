# D357 — the out-of-sample read on the holdout fixture: one read, on the construction D355 and D356 select

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8), and before the
withheld fixture is touched by anything that reads a return. The construction is frozen in
a **committed addendum** after D355 and D356 report; the read runs once, on the principal's
explicit go, and never before the addendum.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing yet. Holdout reads spent: 0. Programme total: 0. This record spends the first.**

---

## 0. Why

R8: a strategy enters the book only after a test whose hurdles were committed before the
withheld data was touched. D342 wrote the design for `rsi` at k=20 and recommended against
spending the read until a null with more than 24 values was cleared and the re-listing hole
was closed; D343 closed the hole and D348 supplied 200 draws the cell clears on every
statistic. The candidate is now k=40 (D344), the exit may change (D355), and the read may go
to a portfolio (D356). The design is restated here for whichever construction those two
select, so the programme's scarcest asset is spent once.

## 1. The fixture

`data/fixtures/us_shorts_daily_holdout.csv.gz`: 803 names **disjoint from the mining set**
(asserted at build and re-asserted here from both fixtures' metadata), the same 2010–2026
span, its own events file. It has never been read. It has **no deal filings**: `--prep` pulls
them from EDGAR with D331's reproducible script pointed at the holdout's symbols, and F0 is
built exactly as D331 built it. **The whole pipeline is re-pointed at the fixture** — score
cache, D303 arrays, census and floor, open fill, floored market, the shared prep under its
own key — by setting the fixture constants before any cache builds; on the mining fixture
the re-pointed pipeline must reproduce D346 to 0.0 first.

**`--dry` reads no return.** It prints counts only — names, bars, filings applied, floor
share, gate coverage — and runs every assertion that does not touch a P&L. A static check
asserts the dry and prep stages contain no path that turns `r1T` or `ocT` into a statistic.

## 2. The read

One process, one time, `--read --spend-the-holdout`, after the addendum names the frozen
construction: the cell (or the portfolio) exactly as selected — depth 2, its exit, k=40,
`keep_v2`, F0, the open fill, PUB with GC/HTB and PB beside — both lenses, both nulls (24 rank
rotations; 200 time rotations of the score), the four groups with the top trade named, the
splits, the trims.

## 3. Hurdles, all six required

| | hurdle |
|---|---|
| **H1** | PUB net bp/bar **> 0** after GC/HTB borrow |
| **H2** | gross bp/bar above the **p95 of both nulls**, each p95 stated |
| **H3** | the symmetric 1% trim of the per-trade ledger is above the round trip (net of cost) |
| **H4** | no trade above **10%** of the ledger's P&L |
| **H5** | at least **10 names** to half the P&L |
| **H6** | PUB net Sharpe **> 0** |

**Any failure retires the construction.** All six → the candidate enters `BOOK.md` carrying its
falsification conditions (S1's block as the template: a negative delta over two further
years pooled forward; failure of either null on any future fixture; any structural change is
a new entry) and every record's header reads *Holdout reads spent: 1*. Whichever way it goes,
the read is not repeated on this fixture for this or any derived construction.

## 4. Stop conditions

- **All six hold** → admission to `BOOK.md`; sizing and capital are separate decisions.
- **Any fails** → the construction is retired in writing; the mining-fixture candidate
  record is amended; no second read.
- **The addendum is never committed** (D355 and D356 both fail their load-bearing
  predictions and the principal declines to read the declared cell) → the read is not spent
  and this record stands as written.

## 5. Assertions

| | |
|---|---|
| **[DIS]** | the holdout's symbols and the mining set's are disjoint, from both metadata files, before anything else runs |
| **[PIPE]** | the re-pointed pipeline on the **mining** fixture reproduces D346's two cells to 0.0 |
| **[NR]** | `--dry` and `--prep` contain no code path from `r1T`/`ocT` to a statistic (static check on the stage's call graph) and their logs contain no return statistic |
| **[K]** · **[F0]** · **[R]** | the holdout's own cache keys; filings applied and the share excluded; the raw factor and the floor share, reported as counts |
| **[L]** · **[A]** | lag audit on the holdout gate; the rotation keeps counts |
| **[S]** · **[ID]** | on the read: sign in money; the two nulls' constructions as in D348 |
| **[6]** | [PIPE] raises on a perturbed score cache; [NR] raises when a return statistic is added to `--dry` |

## 6. Files

`docs/decisions/D357-the-out-of-sample-read-on-the-holdout-fixture.md` (this record; the
addendum to follow) · `scripts/run_d357_holdout_read.py` (stages `--prep`, `--dry`, `--read
--spend-the-holdout`) · `data/fixtures/us_shorts_daily_holdout_deals.json` (from `--prep`) ·
`data/d357_*.json` (to follow). Reuses the whole prep chain re-pointed:
`scripts/run_book_single_names.py` (fixture constants), `scripts/d290_build_cache.py`,
`scripts/run_d303_reference.py`, `scripts/d331_edgar_deals.py`, `scripts/run_d331_deal_filter.py`,
`scripts/d339_census.py`, `scripts/d339_universe_floor.py`, `scripts/d340_fill.py`,
`scripts/d348_prep.py`, `scripts/run_d348_score_rotation_null.py`, `scripts/run_d355_exit_swap.py`.

---

## Addendum — the frozen construction, 2026-09-06 (committed before the read; the read has not run)

**D355** kept the target exit (zero of seven). **D356** held its load-bearing prediction: the
50/50 blend nets +8.78 PUB at a Sharpe of 0.442 above both parents and both paired nulls.
The principal chose the blend. The construction, frozen in `data/d357_construction.json`:

- **Cells:** `rsi` k=40 and `hist_L` k=40, depth 2, D303's target exit, `keep_v2`, F0 (the
  holdout's filings from the EDGAR pull), next-open fill, PUB with GC/HTB, PB beside.
- **The blend:** 50/50 capital, each book at its own cost per bar, on the shared mask.
- **The hurdles gate the blend.** Each parent's six hurdles are computed and reported from
  the same read and gate nothing.
- **Hurdle definitions as the runner computes them:** H3 is the symmetric 1% trimmed mean of
  the pooled ledger with each trade charged its own book's `2c` under PUB (the stricter
  trimmed-minus-full-round-trip printed beside); H4 requires positive total P&L and no
  trade above 10% of it; H5 counts names to half the P&L on the contribution basis
  (raw-P&L basis beside); H6 is the PUB net Sharpe before borrow (after-borrow beside).
- **Nulls:** 24 rank rotations and 200 time rotations of the score per parent; the blend's
  paired versions of each.

**In-sample status of the same six hurdles on the mining fixture**, from the rehearsal of
the read path (which reproduces D356's blend to 1.8e-15), stated so the read is spent
knowing it: `rsi` passes all six; **`hist_L` alone fails H5 (nine names to half)**; the
blend passes all six (fourteen names to half, top trade 5.7% of P&L). The blend is the
construction the read gates; `hist_L` alone would not have been a sound target.

**The read runs once**, `--read --spend-the-holdout`, after this addendum is committed and
the principal gives the word; the runner writes its receipt before any holdout return is
read and refuses a second run.
