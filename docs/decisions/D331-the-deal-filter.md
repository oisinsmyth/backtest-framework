# D331 — the deal filter: an event-driven exclusion for pinned takeover targets, and the test the tape filter failed

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-05
**Area:** Strategy research · **personal track** · cost model

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. Why

D330 B's causal tape filter — a +20% day then quiet — caught **71%** of the
pinned trades in `skew_63`'s short leg and removed **39%** of the survivors.
Its stop condition fired: *the tape cannot separate a deal from a reversal
candidate; a deal-event source is required.* D331's data pull (`2abcb72`,
revised by a second pass) supplies it: SEC EDGAR filings for 1,465 of the
fixture's 1,573 names.

**This is the same test as D330 B with a better instrument**, and it keeps
D330 B's thresholds on purpose: catch > 80% of the pinned trades, remove < 10%
of the survivors. If an event source cannot do that either, the pinned-name
problem is not filterable on this fixture and every jump-detecting short is
uncostable here.

## 1. The filter, declared

**Filings that count** — three definitions, all run, predictions on F1:

| | forms | role |
|---|---|---|
| **F0** target-specific | DEFM14A, PREM14A, SC 14D9, SC TO-T, SC TO-C | filed by or about the **target** |
| **F1** *(primary)* | F0 ∪ 8-K with Item 1.01 and merger / tender / acquisition language | either party; the announcement-day form |
| F2 broad | F1 ∪ 425 | acquirer-dominated (59% of all hits, role not recorded) |

**Exclusion window.** From the fixture bar on or after the filing date, for
**189 trading bars** or until the name's last live bar, whichever comes first.
189 (≈ 9 calendar months) covers the great majority of US public-deal
close times and is a round number, not a fitted one; a broken deal un-pins a
name inside that window and is accepted as a cost of the rule. Overlapping
filings union.

**Causality.** A filing dated `d` is known at the close of bar `d`; the
exclusion applies to the *score* at `s ≥ bar(d)`, and `R.ranked` lags once,
so the first bar it can affect is `bar(d) + 1`. Applied to the score, not the
gate, so a removed name is **replaced** by the next rank (D330 B's convention;
`[R]` checks the refill).

**Coverage is a declared limit.** 108 names are unresolved, 88 of them dead;
a pinned trade in an unresolved name cannot be caught by any filing. The catch
rate is reported **overall and among resolved names**, and both are predicted.

## 2. Part A — validation against the look-ahead labels. No book

On `skew_63`'s symmetric short leg, path-invariant, depth 2, k=20 — D330 A's
ledger — with D330 A's labels recomputed (`[I]` holds them to D330 A):

- **catch rate**: of the pinned trades, the fraction whose name has a
  qualifying filing in `[entry − 63, entry]` bars;
- **survivor removal**: of the trades whose name survives 60 bars, the fraction
  with a qualifying filing in the same window;
- **lead time**: for caught pinned trades, bars from filing to entry — is the
  filing before the jump, or after it?

For each of F0, F1, F2.

## 3. Part B — the books, under both conventions

Arms at depth 2, k ∈ {10, 20, 40}, both lenses, per-leg costing, **PB and PUB
spread conventions side by side** (D332 made PUB the default and PB the
comparison):

| arm | long | short | filter |
|---|---|---|---|
| S | `skew_63` | `skew_63` | — |
| **S_F1** | `skew_63` | `skew_63` | F1, both legs |
| S_F0, S_F2 | | | F0 / F2, both legs (k=20 only) |
| H | `hist_L` | `hist_L` | — |
| LW | `hist_L` | `skew_63` | — |
| **LW_F1** | `hist_L` | `skew_63` | F1 on the short leg |

## 4. Predictions

Q1 and Q5 are load-bearing. Q6 and Q7 are against the broader definitions.

| | prediction |
|---|---|
| **Q1** | **F1 catches > 75% of pinned trades overall and > 85% among resolved names, and removes < 10% of survivor trades.** *Load-bearing — the D330 B test.* |
| **Q2** | The filtered short leg's held half-spread rises: PB 7.7 → ≥ 8.5; PUB 16.3 → ≥ 20. |
| **Q3** | The trimmed-both mean of the short leg moves by **< 10 bp** under F1 — D330 B's Q3, now with a filter that leaves the survivors alone. |
| **Q4** | Under PUB, S_F1's short leg nets **more** per trade than S's (−0.6): pinned names were drift and cost, not edge. |
| **Q5** | **LW_F1 still beats both parents** on invariant net per trade at k=20 under PUB. *Load-bearing.* |
| **Q6** | *(against F0)* target-specific forms alone catch **< 50%** of pinned trades — the proxy is filed weeks after the announcement, and the name enters the short leg before it exists. |
| **Q7** | *(against F2)* adding form 425 removes **> 3×** as many survivor trades as F1 while catching < 5 points more of the pinned. |
| **Q8** | F1 applied to `skew_63`'s **long** leg removes < 2% of its trades. |
| **Q9** | For caught pinned trades, the median lead time from filing to entry is **> 5 bars** — the announcement precedes the jump-driven entry, so the filter fires in time. |

## 5. Stop conditions

- **Q1 and Q5 confirm** → the pinned-name problem is filterable by events,
  `skew_63`'s short leg has an honest number, and the leg-wise book's bound
  collapses to a point under each convention. D329 §1 and D330 are amended.
  Nothing enters the book.
- **Q1 fails on the catch rate with coverage explaining it** (resolved-name
  catch > 85%, overall < 75%) → the filter works and the data does not reach
  the dead names; the fix is resolution, not the rule.
- **Q1 fails on the catch rate among resolved names** → the pinned names are
  not takeover targets after all, or the forms are wrong. D330's reading is
  re-examined.
- **Q1 fails on survivor removal** → deals and reversals are not separable by
  events either; `skew_63` is retired as a short signal. *(D330 B's Q3 stop
  condition, now with its premise satisfied.)*
- **Q5 fails** → the leg-wise result was the deal artefact. D329 amended.

## 6. Assertions

1. **[K] causality** — truncation audit on the exclusion mask: delete every
   filing dated after `T0`, recompute, require bit-identity for `s ≤ T0`.
2. **[D] date mapping** — every filing maps to the first fixture bar on or
   after its date; filings after the name's last live bar or before its first
   are dropped and counted, never applied.
3. **[W] the window** — no exclusion extends past 189 bars from its filing or
   past the name's last live bar.
4. **[I] labels** — D330 A's labels reproduce: 1,024 / 297 / 212 pinned / 0
   collapse on `skew_63`'s short leg.
5. **[1] identity** — the unfiltered arms reproduce D332's PB and PUB cells to
   1e-9 on both lenses.
6. **[L] leg independence** — LW_F1's long ledger is H's, its short ledger is
   S_F1's, bit-identically, both lenses.
7. **[R] refill** — at every bar where the rank-0 short name is excluded, a
   different name holds rank 0.
8. **[F] the filter fires** — a non-zero number of name-bars, and S_F1 differs
   from S.
9. **[6]** raises on a book handed free money.

*Every assertion is a property of the code, the data mapping, or a prior
record. None asserts what a book will show.*

## 7. Scope

**Out:** borrow cost (the deal dates now anchor the cohort a stress charge
would target — a separate record); the tape filter (D330 B, closed); any
filing form outside the three definitions; deal *outcome* (closed / broken),
which EDGAR does not give directly; the holdout. **In:** the validation, the
three definitions, the books under both conventions.

## 8. Files

`docs/decisions/D331-the-deal-filter.md` (this record) ·
`data/fixtures/us_shorts_daily_raw_deals.json` and
`data/d331_edgar_coverage.txt` (the data, `2abcb72` and its revision) ·
`scripts/d331_edgar_deals.py` (the pull) · runner and result data to follow.
