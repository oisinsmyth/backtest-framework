# D245 — The wide universe

**Status:** Pre-registered — committed BEFORE the wide fixture is built or scored
**Date:** 2026-08-28
**Area:** Strategy research

---

## The question

**Does S2 work across the broad ETF universe, or only across the 57 it was found on?**

And the second, quieter one: **how much of the book's interval width is a breadth problem?** The
57 correlate so heavily that they are worth only **2.23 effective independent instruments**.
That number, not the span, is why every interval in this programme has been wide.

---

## What is already on disk

**The daily cache holds 1,276 symbols and the book has used 117.** No fetch of prices is
required. What was missing is corporate actions, and those are being fetched for all **792
symbols with history back to 2009-11-11** — the extended fixture's start — so the wide universe
can be scored on **the identical span and identical bars** as [D243](D243-the-book-on-extended-history.md).

**No leveraged or inverse products are present**, which removes the worst structural
contaminant. The cache does contain **closed-end funds**, which trade at premiums and discounts
to NAV and carry their own leverage. They are retained: they are tradeable instruments and the
rules are price-based. **The composition is reported, not screened on type.**

---

## Universe selection — by liquidity and history, never by performance

| median daily dollar volume | symbols retained |
|---|---:|
| ≥ $1,000,000 | 496 |
| **≥ $5,000,000** | **245** |
| ≥ $10,000,000 | 186 |

**Two cells, and the reason for both is the cost model rather than the returns.**

- **W5 — the primary.** `median dollar volume ≥ $5M/day`, **245 symbols.** Chosen so the
  committed **1 bp half-spread** in `per_side_bps` stays credible. It is still optimistic; a $5M
  ETF's spread is nearer 3–10 bp.
- **W1 — the breadth cell.** `≥ $1M/day`, **496 symbols.** Twice the breadth, weaker cost
  realism. **Registered because the trade-off is the actual question** — whether breadth or cost
  realism dominates — and guessing it would be worse than measuring it.

**The breakeven cost is reported for every cell**, so the half-spread assumption is visible
rather than buried.

---

## The split that carries the verdict

**The wide universe CONTAINS the 57 and the 60**, so it is not a clean holdout and will not be
reported as one. It decomposes:

| cohort | status |
|---|---|
| the mined **57** | S1 and S2 were built here |
| the holdout **60** | spent by D237 and D242 |
| **everything else** | **never seen by any rule in this programme** |

**Hurdles are evaluated on the never-seen cohort.** The full-universe numbers are reported for
**breadth and interval width only**, and are contaminated by construction.

---

## Hurdles

**On the never-seen cohort, for S2 — which is the entry with out-of-sample support:**

- **Z1.** Excess Sharpe **> 0** and **> buy-and-hold's** on the same bars.
- **Z2 — carries the verdict.** Beats its **matched-count rotation null at p95**.
- **Z3.** Delta over buy-and-hold reaches **25% of the 12.8-year mined delta** — S2 scored +0.511
  against +0.242, so the floor is **+0.067**. D237's construction, reused.

**Reported, not hurdles:** the same three legs for S1; **effective independent instruments**
(`1/(wᵀRw)`) for each cohort and cell; the bootstrap interval on every book, **against D243's
figures so the narrowing is measurable**; exposure, deployable return, Calmar, max drawdown,
hurdle E, breakeven cost, and ρ between S1 and S2 on the wide universe.

---

## Predictions

| | prediction | confidence |
|---|---|---|
| **Z-a** | **S2 clears Z1–Z3 on the never-seen cohort.** It has now replicated on 60 disjoint tickers and in a never-seen era, and its mechanism is structural | **moderate-high** |
| **Z-b** | **Effective independent instruments roughly doubles**, from 2.23 to somewhere near 4–6. The 57 are almost all US equity sectors; the wide set adds bonds, international, commodities and CEFs | **moderate** |
| **Z-c** | **The interval narrows but by less than the instrument count suggests.** Breadth is capped by correlation, not by headcount — 245 names at ρ ≈ 0.4 are not 245 independent bets | **moderate-high** |
| **Z-d** | **W1 (496 names) scores HIGHER than W5 (245) and is less trustworthy**, because the extra names are thinner and the 1 bp half-spread flatters them. If W1 beats W5 by more than its breadth advantage implies, that gap is the cost model, not alpha | **moderate** |
| **Z-e** | **S1 remains weak on the never-seen cohort**, consistent with D243 | **moderate** |

**Z-d is registered so that a better W1 number cannot be reported as a better result.**

**Hurdle E will NOT be fixed by this, and I said otherwise in conversation before checking.**
Entries per symbol scale with **span**, not with universe size — S2 went from 2 to 5 per symbol
when the span doubled and will not move here. That correction is recorded rather than quietly
dropped.

---

## Stop

**No rule is proposed or changed.** If S2 fails on the never-seen cohort it is amended in
`BOOK.md` in writing, with the result recorded as a demonstrated weakness. **No re-cut, no
universe-specific variant.**

---

## Ledger

| count | N |
|---|---:|
| fresh — 2 cells, both liquidity screens on a frozen rule | **2** |
| + D244's 0, D243's 0, D242's 3, D241's 5, D240's 5, D239's 3, D238's 4, D234's 6, D235's 7, D236's 6 | 41 |
| + the gradient anatomy | 62 |
| + disclosed ETF prior | **45,865** |

---

## Reuse — D212 is binding

Everything except the fixture builder. `fetch_extended_history.fetch_actions` supplies the
actions; `run_book_extended.books_on` already repoints the loader at an arbitrary fixture; the
scorers, nulls, allocator and bootstrap are committed and tested.

**Written fresh: the wide-universe builder and the cohort split — nothing else.** The builder
must iterate to a fixed point, as `run_book_crypto`'s does, because `clean` drops bars per symbol
and a raw date intersection will not load with equal bar counts.

## Verification

- **The 57-symbol subset of the wide fixture must reproduce D243's numbers** — +0.478 for S1 and
  +0.511 for S2. If it does not, the builder has changed the data and the comparison is void.
- **The cohort split is asserted disjoint** and to cover the universe exactly.
- **No leveraged or inverse tickers** enter, asserted against a named list.
- **The liquidity screen is computed on the fixture's own span**, never on a later window.
- `--report-only` re-renders byte-for-byte; full suite green.

---

## AMENDMENT 1 — a completeness screen was required, and it is survivorship bias

*Forced by the first build, recorded rather than patched away.*

A rectangular panel needs every symbol present on every date, so **one delisted fund truncates
the whole intersection.** The first build produced **W1 at 880 bars ending 2017-10-13**, and even
W5 lost 1,115 bars.

**56 of the 792 stop trading before 2026-08** — FEO in 2022-12, then IRL, DDF, DEX, MGU and NKG
through 2023, mostly liquidated closed-end funds — and 67 carry sparse coverage.

**The screen: at least 4,200 bars in the window and data through 2026-08-01. It drops 67 and
leaves 725.**

**This is survivorship bias and it flatters any long book**, because funds that get liquidated
are disproportionately funds that did badly. The alternative is a ragged panel, which
`load_panel` refuses by design. **The excluded names are written to the artifact** so the bias is
auditable rather than asserted to be small.

The runner now also refuses a fixture with fewer than 500 live bars, rather than crashing a
hundred lines later inside `max_drawdown_of`.

---

## RESULT

**Produced:** 2026-08-28 · `build_wide_universe.py` then `run_book_wide.py` · Page:
[`BOOK_WIDE_RESULTS.md`](../results/BOOK_WIDE_RESULTS.md)

### The one-sentence version

**Both entries clear on instruments they have never seen — S1 included — and the premise this
study was recommended on is falsified: adding 429 ETFs LOWERED effective breadth from 2.23 to
2.02.**

### The never-seen cohort — where the verdict lives

| | symbols | new | | excess Sharpe | B&H | delta | floor | null pctile | verdict |
|---|---:|---:|---|---:|---:|---:|---:|---:|:--:|
| **W5** | 244 | **152** | S1 | +0.468 | +0.365 | +0.103 | +0.059 | **99.8th** | **✓** |
| | | | S2 | +0.496 | +0.365 | +0.131 | +0.067 | **99.0th** | **✓** |
| **W1** | 486 | **385** | S1 | +0.493 | +0.319 | +0.174 | +0.059 | **100.0th** | **✓** |
| | | | S2 | +0.497 | +0.319 | +0.178 | +0.067 | **99.9th** | **✓** |

**S1 clears on 385 instruments it has never seen.** Together with D243 that locates its problem
exactly: **S1 generalises across INSTRUMENTS and fails across ERAS.** It is not a broken rule, it
is a rule with a regime dependency — which is what D239 predicted from a mechanism, before D243
measured it.

### The finding: breadth did not increase, it fell

| universe | symbols | **effective independent instruments** |
|---|---:|---:|
| the 57 | 57 | **2.23** |
| W5 | 244 | **2.02** |
| W1 | 486 | **2.08** |

**Adding 429 ETFs added correlation, not diversification.** The 57 were unusually diverse —
bonds, metals, commodities and fourteen country funds. The wide universe above $5M/day is
dominated by US equity sector and style products that move together.

**This puts a hard ceiling on "more instruments" as a route to narrower intervals**, and it is
the most consequential thing in this record.

### The intervals, against D243's 57-name figures

| | D243 (57) | W5 (244) | W1 (486) |
|---|---:|---:|---:|
| S1 | +0.478 `[−0.036]` | +0.491 `[−0.053]` | +0.499 `[−0.050]` |
| **S2** | +0.511 `[+0.066]` | **+0.530** `[+0.126]` | +0.514 `[+0.110]` |
| **C** | +0.620 `[+0.126]` | **+0.649** `[+0.126]` | +0.641 `[+0.140]` |

**S2's lower bound roughly doubled, from +0.066 to +0.126.** Real, and far less than an eightfold
increase in instruments would suggest — because breadth, not headcount, is what sets it.

**S1's interval contains zero at every universe size.**

### Scoring — two confirmed, three falsified

| | prediction | outcome |
|---|---|---|
| **Z-a** | S2 clears Z1–Z3 on the never-seen cohort | **CONFIRMED** at both floors |
| **Z-b** | effective breadth roughly doubles to 4–6 | **FALSIFIED.** It *fell* to 2.02 |
| **Z-c** | the interval narrows by less than the count suggests | **CONFIRMED**, emphatically |
| **Z-d** | W1 scores higher than W5 and is less trustworthy | **FALSIFIED.** W1 scored *lower* on S2, +0.514 against +0.530. The cost-model inflation this guarded against did not appear |
| **Z-e** | S1 stays weak on the never-seen cohort | **FALSIFIED.** 99.8th and 100th percentile |

**Three of five wrong, and Z-b was the premise the study was recommended on.** The
recommendation was right for a reason that turned out to be false: expansion was worth doing as
an *instrument holdout*, not as a breadth fix.

### What this changes

**S1's evidence table gains a row and its diagnosis sharpens.** It has now cleared two
instrument holdouts — 60 tickers (D237) and 385 (here) — and failed one era holdout (D243) and
one asset class (D244, inconclusive). **Instrument-general, era-specific**, stated precisely.

**S2 is confirmed across the broad ETF universe** at both liquidity floors.

**And "add more instruments" is closed as a route to significance.** At ρ ≈ 0.4 across US equity
ETFs, breadth saturates near 2 and headcount cannot fix it. The remaining routes are more
*time*, or genuinely uncorrelated *return drivers* — which is what D246's protocol already
targets.

### Ledger

| count | N |
|---|---:|
| fresh — 2 cells | 2 |
| + D247's 8, D242's 3, D241's 5, D240's 5, D239's 3, D238's 4, D234's 6, D235's 7, D236's 6 | 49 |
| + the gradient anatomy | 70 |
| + disclosed ETF prior | **45,873** |
