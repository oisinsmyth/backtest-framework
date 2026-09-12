# The Components Ledger — prop book

**Append-only.** A component is entered here on the standard below; it is amended or retired in
writing, never quietly edited. **Nothing in this ledger is admitted to the prop book**: only the
assembled book is tested against hurdle P (R11) and only the assembled book can enter
[`BOOK_PROP.md`](BOOK_PROP.md). The ledger exists because the book-level Sharpe the account
needs (~1.5–2) is reached by layering low-correlation components, never by one construction
(CLAUDE.md, *Two altitudes*).

## The standard (pre-registered in D466, 2026-09-12)

A construction is a **component** when, on the in-sample window (the D462 usable window,
2016-01-04 to 2023-12-29, for the futures fixtures) at the instrument's **minimum tradable size**
(the micro where one exists, one contract otherwise), net of the declared futures cost:

| | bar |
|---|---|
| **C-a** net annualised Sharpe of its daily P&L | **> 0.5** |
| **C-b** correlation of its daily P&L with **every** component already in the ledger | **< 0.3** |
| **C-c** skew of its daily P&L | **≥ −0.5** (P1 punishes negative skew; positive is fine) |
| **C-d** expressible | daily σ at minimum size ≤ 1% of a $50k account, so the assembled book can be sized |
| **C-e** provenance | a pre-registered record; the window; the cost line; the nulls it was scored against |

**C-a is a bar on the point estimate, and a component's Sharpe carries its SE** (block
bootstrap, monthly); the ledger records both. **Order of entry is recorded** because components
are chosen after their Sharpes are seen: the assembled book is confirmed only on the unread slice
(2024-01 onward on the futures fixtures), and the order fixes what "already in the ledger" meant
when C-b was applied.

**A gated subset of a component is not a new component** (it shares the clock and the signal).
**Two windows on one instrument that do not overlap in time are two components** (ρ ≈ 0.1).

## The ledger

| # | component | instrument, window, rule | record | window | net Sharpe (SE) | hit | skew | ρ with prior | entered |
|---|---|---|---|---|---|---|---|---|---|
| — | *no entry* | | D466 | 2016–2023 | | | | | *the standard admitted nothing on 2026-09-12* |

## Scored and NOT entered

| construction | record | net Sharpe | why not |
|---|---|---|---|
| K1 C1: ES hold 18:00→16:00 every same-contract night, 1 MES, $3 | D466 (D449, D465) | **+0.37 (SE 0.32)**; gross +0.63 | C-a. $3 is 41% of the $7.29 gross mean per night; clears C-a only below $1.48 a round trip |
| K2 last-30-min momentum NQ, 1 MNQ, $3 | D466 (D463) | −0.01 (0.40); gross +0.66 | C-a. cost 102% of the gross mean |
| K3 last-30-min momentum ES, 1 MES, $3 | D466 (D463) | −0.29 (0.41); gross +0.62 | C-a; ρ(K2,K3) = 0.73 — one construction across roots |
| K4 last-30-min momentum YM, 1 MYM, $3 | D466 (D463) | −1.12 (0.48); gross +0.08 | C-a; no gross edge |
| K5 C1 on S1 nights (SPY gate), 1 MES | D466 (D464) | +0.36 (0.40) | C-a; a gated subset of K1 (ρ 0.35) |
| K6 C1 on S2-exposure nights (SPY gate), 1 MES | D466 (D464) | +0.39 (0.29) | C-a; C-c skew −1.21; a gated subset of K1 (ρ 0.26) |

**Correction recorded 2026-09-12 (D466 RESULT):** the figures that motivated this ledger (C1 0.62,
NQ last-30 0.42, equal-risk book 0.91) were computed at full-size cost in basis points (1.1 bp a
round trip); at the standard's minimum size and $3 they are 0.37 and −0.01 and there is no book.
The gross edges (0.63, 0.66 at micro size) are real; the cost per round trip at micro notional
(~2 bp) eats them. Every component line from here on is computed by the runner under this
standard, never in a shell line.
