# D732 STAGE 0 PRE-REGISTRATION — is there an ES/NQ book at one micro that does not rest on one year? A premise check before any book is declared for the joint vault run

*2026-10-01.*
- *The principal: "Ok well validate with a premise check first, when evaluating net profits look at micros only and
  look at ES and NQ", on the recap of a book that does not need 2022 (after
  [D722](D722-DIAG-RESULT-no-variable-explains-2022.md) and
  [D729](D729-METHOD-the-volatility-unit-year-concentration-report.md)).*
- *Numbered D732 after telling the other session.*
- ***Committed alone, before its runner exists.** In-sample only: 2018-05-14 → 2023-12-29. Nothing dated 2024-01-01 or
  later enters any statistic. No slot, no vault, and no frozen line changes.*

## 0. Why, and what is known

- **D722:** the surviving index lines win on different days but in the same year.
- **D729:** NQ F2 leans on 2022 in volatility units too; the MACD arm is 2020-heavy; the NQ compression break leans on
  no year.
- **CLAUDE.md's geometry:** a book Sharpe of about 1.5–2 from components at net Sharpe 0.4–0.6 with ρ < 0.3.
- **The joint run scores "the assembled book"** (AITODO's programme rule). Nothing has yet declared which book that is.

**Known before this record:**
- **D727's post hoc:** its NQ book is ρ 0.24 with the arm and −0.10 with NQ F2, and arm plus book makes net Sharpe 0.96.
- **The ledger's component lines.** At MES:
  - D689 −0.18 and D708 −0.45 (net-negative at micro);
  - D699 is closed;
  - ES F2 is parked as the same trade as NQ F2 (ρ 0.94 in 2022, D722).

## 1. The objects (net dollars at ONE micro each; ES at MES, NQ at MNQ)

**The primary book** is the index components the programme already carries: one admitted, one provisional, one frozen.

| id | component | source (imported, never edited) | known answer asserted |
|---|---|---|---|
| A | the MACD arm (#2), 1 MNQ | `diag_d722_lines.load_lines()` K1 (D722-A1's sealed path) | 1,876 sessions, $15,423 total (2016–2023) |
| F | NQ F2 (#5, D716 book B), 1 MNQ, $4.067121 | `load_lines()` L2 | 271 trades, mean net 20.768672… |
| C | NQ compression break C1 (D680), 1 MNQ | `vault_d680_nq_compression.in_sample()` and `known_answer` | 387 C1 trades; then cut to ≤ 2023-12-29 |

- **C's dollars:** (net bp / 10⁴) × entry price × $2. These are D672-A1's single-count net basis points.

**Beside the book (reported, not read):**
- **T1 and T1.5:** D727's practical NQ book at k 1.0 and k 1.5 (`diag_d727_overlap.first_crossing_daily`), at 1 MNQ
  and $4.07.
  - Each is asserted to reproduce D727's trades and mean net over its own window (k 1.0: 1,505 trades, +$7.14; k 1.5:
    1,024, +$15.22).
  - This is development: it failed its transfer test, and k 1.5 is the best of three after the fact.
  - **CONTEXT ONLY:** the principal declined D727's plain follow as a strategy on 2026-10-01 ("I don't want a dumb
    follow type strategy"; recorded in D731 and AITODO). It is shown only to say what the book would look like with an
    unconditional NQ continuation in it. **It is not a candidate component.**
- **E:** ES F2 at 1 MES (`load_lines()` L1). It enters only the correlation table, as the ES component the ledger
  holds.

**ES at micro.** No other ES construction is eligible: D689 and D708 are net-negative at MES, and D699 is closed.
Their ledger rows are quoted, not rebuilt.

**The calendar:**
- The ES/NQ sessions of `diag_d722_conditioners` from 2018-05-14 to 2023-12-29.
- A component's daily net is the sum of its trades that session, and 0 on a session without one.
- The book B = A + F + C, one micro each, with no weights chosen. A fractional equal-risk variant is reported beside it,
  not read, since only whole micros trade.

## 2. The premise checks

**S1 — each component and the book:**
- total net and net a year;
- daily net Sharpe and Sortino (√252);
- maximum drawdown;
- net by year;
- D729's report on the daily net, with scale = $2 × NQ's prior front settlement × σ20 (D729's NQ scale), giving
  shares in dollars and in volatility units, and the label.

**S2 — the book without each year:** the book's daily net Sharpe with each calendar year's sessions removed in turn.

**S3 — the correlations:** pairwise daily ρ among A, F, C, T1, T1.5 and E, pooled and in each year.

**The reading (the book B):**

| reading | when |
|---|---|
| **GO** (worth designing a declared book) | the book's largest year carries ≤ 50 % of its net in dollars **and** in volatility units (D729 label NEITHER), **and** its net Sharpe without its largest year is ≥ 0.5 |
| **PARTIAL** | not GO, but its net without its largest year is > 0 |
| **NO-GO** | otherwise |

**What each means:**
- **GO:** a declared-book pre-registration for the joint run (its components and whole-micro sizes fixed before the
  vault opens) is worth writing, on the principal's word.
- **PARTIAL:** the book depends on one year; any declared book should be sized on its ex-year figure.
- **NO-GO:** these components do not make a book outside one year.

## 3. The runner's assertions (each shown to raise in `--selftest`)

1. **The seal.** No session ≥ 2024-01-01 in any series; a planted row raises. D680's in-sample function reads its own
   window to 2025-02-28 and is cut to the calendar before anything is computed.
2. **Known answers:** each of A, F, C, T1 and T1.5 (§1) before the cut.
3. **The daily aggregation:**
   - each component's daily sum equals its trade total on the window;
   - a dropped day or a duplicated trade raises (D680 and D727 hold one trade a session; the arm's rows are already
     daily).
4. **The book identity:** B equals A + F + C day by day, and its variance equals the sum of variances plus twice the
   covariances.
5. **The reading logic** is checked on synthetic books built to give each reading.

## 4. Predictions (mine, before the runner exists)

| # | prediction |
|---|---|
| 1 | the book's largest year is 2022, at 35–50 % of its net in dollars |
| 2 | its D729 label is NEITHER |
| 3 | its net Sharpe without 2022 is ≥ 0.5, so the reading is **GO** |
| 4 | its in-sample net Sharpe is below 1.5, short of the geometry |
| 5 | adding T1 raises the book's Sharpe and keeps NEITHER (context only, not read) |
| 6 | pairwise ρ among A, F and C stays below 0.3 in every year |
