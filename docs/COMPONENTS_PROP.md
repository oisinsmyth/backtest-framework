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

**PROVISIONAL entries (added by D468, 2026-09-12).** When a record scores a *family* of declared
constructions, it reports the sign-randomisation null of the **best net Sharpe across the family**
(one sign vector per session, common to all members, so the family's correlation is preserved).
A construction that clears C-a but sits below that null's p95 is entered as **PROVISIONAL**: it
counts for C-b against later entries, it goes into the assembled book, and only the unread slice
(2024-01 onward, read under the principal's word) promotes it to a full entry or removes it. With
~2,000 days the SE of a Sharpe is ≈ 0.35 and the best of 24 draws under no edge sits near +0.6;
C-a on the point estimate is under that ceiling, and the ledger says so in the row.

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

| **D468 (2026-09-12): 24 session windows on eight roots**, W1 18:00→16:00, W2 18:00→09:00, W3 09:00→16:00, long only, minimum size, $3 ($6 on ZN/ZB) | D468 (D467) | family-max null p50 +0.55, p95 +0.95; observed best +0.39 (78th pct of the null) | **C-a on all 24**; nothing provisional |
| ES-W1 (1 MES) / NQ-W1 (1 MNQ) / YM-W1 (1 MYM) | D468 | +0.39 (0.32) / +0.38 (0.32) / +0.15 (0.33); gross +0.64 / +0.54 / +0.47 | C-a; ρ 0.91–0.92 among them (one construction); YM also C-c |
| ES-W2 / NQ-W2 / YM-W2 (the overnight leg) | D468 | +0.19 / +0.26 / +0.04; gross +0.63 / +0.56 / +0.60 | C-a; cost 54–93% of the gross mean — the edge is here and the micro cost is too |
| ES-W3 / NQ-W3 / YM-W3 (the day leg) | D468 | +0.04 / +0.10 / −0.25; gross +0.35 / +0.29 / +0.14 | C-a |
| ZN-W1/W2/W3 (1 ZN, $6) | D468 | −0.20 / −0.29 / −0.35; gross ≈ 0 | C-a; no micro; σ $290–400 a day |
| ZB-W1/W2/W3 (1 ZB, $6) | D468 | +0.01 / −0.08 / −0.08; gross ≈ 0 | C-a; **C-d** σ $682–939 (> 1% of the account); no micro |
| GC-W1/W2/W3 (1 MGC) | D468 | −0.23 / −0.19 / −0.63; gross +0.09 / +0.25 / −0.17 | C-a |
| CL-W1/W2/W3 (1 MCL) | D468 | −0.39 / −0.31 / −0.69; gross −0.09 / +0.14 / −0.30 | C-a; C-c |
| 6E-W1/W2/W3 (1 M6E) | D468 | −0.72 / −1.17 / −0.85; gross +0.01 / −0.21 / +0.24 | C-a |

| **D470 stage 0 (2026-09-12): four declared gates on ES/NQ W1 and W2** (continuation, prior overnight leg, 200-average, vol tercile), 32 cells | D470 (D467) | best gated component: ES-W2 after a DOWN overnight leg +0.70 (0.26), NQ-W2 +0.62 (0.25); clears N1/N2, **not the family-max p95** | stage 0 — a PICK, not a component: the reversal sign is on 8 of 8 cells but its size is 2020–2022; continuation is the wrong sign everywhere; 200-average clears every null on ES (+0.44) and reverses on NQ; only the unread 2024+ slice can promote it |

**Correction recorded 2026-09-12 (D466 RESULT):** the figures that motivated this ledger (C1 0.62,
NQ last-30 0.42, equal-risk book 0.91) were computed at full-size cost in basis points (1.1 bp a
round trip); at the standard's minimum size and $3 they are 0.37 and −0.01 and there is no book.
The gross edges (0.63, 0.66 at micro size) are real; the cost per round trip at micro notional
(~2 bp) eats them. Every component line from here on is computed by the runner under this
standard, never in a shell line.
