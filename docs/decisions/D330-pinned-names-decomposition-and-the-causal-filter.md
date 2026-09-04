# D330 — pinned takeover targets: how much of every leg is one (A), and a causal filter that predicts the signal gets WORSE (B)

**Status:** PRE-REGISTERED. Committed **before either runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-05
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. Why

D329 §10 found that **29% of `skew_63`'s short-leg trades are in a name that
leaves the tape within 60 bars, and 96% of those end within ±5% of the entry
price with a 0.28% daily range** — cash takeovers pinned at the offer. A short
earns nothing on them, cannot in practice borrow them, and Corwin–Schultz
prices them at 6.2 bp because a pinned stock has no range. That is one cause
behind D326's unexplained cost coverage, D327/D328's "cheapest names," and
D329's three zero-spread cells (FINDINGS §16).

**A dead-name exclusion is the wrong cut.** The fixture is dead-inclusive on
purpose: a short book's edge lives in names that collapse to delisting. A
blanket exclusion removes the collapses with the deals. And "exclude names
that die within 60 bars" uses the future — as a rule it is not a test, it is
flattery. What is needed is (A) a measurement of how much of *every* leg is
deal-pinned, look-ahead and never scored, and (B) a **causal** filter with the
honest prediction: **the per-trade net falls**, because the cost correction is
larger than the drift the short was collecting on zero-return names.

## Part A — the decomposition. Diagnostic; look-ahead; NO predictions

For each of the 46 dimensionless D290 signals (D328 units audit), both legs,
path-invariant, `DEPTH = 2`, `k = 20` — the ledger D329 used. For every trade
`(row, entry, age, pnl, side)`:

- **dies** — the name's last live bar is within 60 bars of entry **and is not
  the sample end** (a name alive at the end is censored, not dead).
- For dying trades, the return from entry to the last live bar, and the median
  daily range `(H − L) / C` while held.
- **pinned** — dies, |return to death| < 5%, median range < 0.5%.
- **collapse** — dies, return to death < −30%.
- **other** — dies, neither.

Per leg: trade count, dying fraction, pinned / collapse / other fractions,
gross P&L per trade and held median half-spread for each group. Two tables,
one per side, sorted by pinned fraction.

**Nothing in Part A is scored, ranked, or compared to a book.** Its labels use
the future and are diagnostic labels only. Part B reads them for one purpose:
to measure what fraction of the pinned trades its causal filter catches.

### Part A assertions

1. **[P]** every ledger P&L is reproduced from `(row, entry, age)` to 1e-12.
2. **[D] censoring** — a name whose last live bar is `T − 1` is never
   counted as dying, however close its entry.
3. **[G] the groups partition** — pinned, collapse and other are exclusive
   and exhaust the dying trades.
4. **[I] harness identity** — `skew_63`'s short leg reproduces D329 §10's
   numbers: 1,024 trades, 297 dying, 284 pinned, 0 collapses.
5. **[6]** the self-test raises on a broken label.

## Part B — the causal filter, pre-registered against the signal

### B.1 The filter, declared

At score time `s`, for name `i`, **using bars ≤ s only**:

- **jump** — the largest single-day log return in bars `[s − 62, s − 5]`
  exceeds **log(1.20)** — a +20% day between 5 and 63 bars ago. (Universe
  median biggest day is +5.4%; the pinned names' is +41%; 20% is a jump by any
  standard and is not tuned.)
- **quiet** — the median daily range `(H − L) / C` over bars `[s − 4, s]`
  is below **0.75%**. (Pinned names sit at 0.28%, survivors at 1.61%; 0.75% is
  a round number near their geometric midpoint, declared, not fitted.)
- **fire** = jump AND quiet. The 5-bar gap exists so that the range test
  never reads the jump day itself.

**The filter acts on the score, not the gate**: `z_f = where(fire, NaN, z)`,
then `rank_single` as usual. A removed name is therefore *replaced* by the next
rank, not left as a hole. `R.ranked` lags internally, so a score at `s` built
from bars ≤ s is used at `s + 1`; no extra lag is applied.

### B.2 Arms

`DEPTH = 2`, `k ∈ {10, 20, 40}`, both lenses, D329's per-leg costing.

| arm | long leg | short leg | filter on |
|---|---|---|---|
| S | `skew_63` | `skew_63` | — |
| **S_f** | `skew_63` | `skew_63` | **both legs** |
| LW | `hist_L` | `skew_63` | — |
| **LW_f** | `hist_L` | `skew_63` | **short leg only** — the treatment |
| LW_ff | `hist_L` | `skew_63` | both legs |
| H | `hist_L` | `hist_L` | — |

### B.3 Predictions

Q4 and Q6 are load-bearing. Q4 is *against* the signal and is the point.

| | prediction |
|---|---|
| **Q1** | The filter catches **> 80%** of the trades Part A labels *pinned* in `skew_63`'s short leg, and removes **< 10%** of the trades whose name survives. |
| **Q2** | `skew_63`'s filtered short leg has a held median half-spread of **≥ 8.5 bp**, up from 7.7 — the cost becomes honest. |
| **Q3** | The trimmed-both mean of the short leg moves by **< 10 bp** — the edge was never in the pinned names. |
| **Q4** | **LW_f's invariant net per trade at k=20 is BELOW LW's +63.26.** *Load-bearing and against.* The cost correction outweighs the market drift the short collected on zero-return names. |
| **Q5** | Applied to `skew_63`'s **long** leg the filter removes **< 2%** of its trades — the signature sits at the top of skew, not the bottom. |
| **Q6** | **LW_f still beats both parents** — S_f and H — on invariant net per trade at k=20 **and** on variant net Sharpe at k=20. *Load-bearing.* If it does not, the leg-wise result was the deal artefact. |

### B.4 Stop conditions

- **Q4 and Q6 confirm** → the leg-wise book has an honest per-trade number
  and a real short leg. That number replaces D329's +63.26 as the one to
  quote, and the construction remains a candidate for a separate pre-registered
  test (R8). Nothing enters the book.
- **Q6 fails** → the leg-wise finding was the deal artefact. D329 §1 is
  amended accordingly.
- **Q1 fails** → the causal signature does not find the pinned names; the
  filter is not the instrument and a deal-event source is required.
- **Q3 fails** → the survivors' edge and the pinned names are not separable;
  `skew_63` is a deal detector, not a short signal, and is retired as one.
- **Q4 fails (net rises)** → the drift term was larger than the cost term. Not
  a problem for the construction, but the record must say the filter *helped*,
  and why, before anything is quoted.

### Part B assertions

1. **[K] causality of the filter** — truncation audit: delete every bar after
   `T0`, recompute `fire`, require bit-identity before `T0`.
2. **[F] the filter fires** — it removes a non-zero number of name-bars and
   S_f differs from S on both lenses.
3. **[1] harness identity** — the unfiltered arms reproduce D329's cells to
   1e-9 on both lenses.
4. **[L] leg independence** — LW_f's long ledger is H's, bit-identically, in
   both lenses; its short ledger is S_f's.
5. **[R] refill** — at every bar where the unfiltered rank-0 name is removed,
   the filtered ranking has a different rank-0 name. Filtering the score, not
   the gate, is what makes that true, and it is checked.
6. **[C]** per-leg `2c` is 2 × that leg's held median half-spread.
7. **[6]** the self-test raises on a book handed free money.

## Scope

**Out:** a borrow-cost term — the fixture has no borrow rates and no deal
events, and a name that passes the filter can still be unborrowable. That
stays a declared gap beside FINDINGS §10. Also out: any threshold other than
the two declared; filters on any signal other than `skew_63`'s legs and, as
a diagnostic, `hist_L`'s; the holdout.

**Both parts run in parallel; neither reads the other's output.** Part B
recomputes Part A's labels on `skew_63`'s short leg for Q1 alone.

## Files

`docs/decisions/D330-pinned-names-decomposition-and-the-causal-filter.md`
(this record) · two runners and two data files to follow. Prior evidence:
`data/d329_legwise.json`, `data/d329_skew63_diagnostics.txt`,
`scripts/d329_skew63_short_leg.py`.
