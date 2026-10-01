# D732 STAGE 0 RESULT — GO by the declared rule (no single year over half; Sharpe 0.95 without 2022), but POST HOC the book is 2020 + 2022, and outside those two years only the compression break pays

*2026-10-01. Pre-registered in [D732](D732-STAGE-0-PRE-REG-a-book-that-does-not-rest-on-one-year.md) (`74f907a4`).*
- *The runner is `scripts/stage0_d732_year_robust_book.py` (`f7203dc3`; `--selftest`: 7 canaries raise, every known
  answer reproduced), run once. Output: `data/stage0_d732_year_robust_book.json`.*
- *In-sample 2018-05-14 → 2023-12-29 (1,454 sessions), net dollars at one micro. No vault, no slot.*
- *The principal: "validate with a premise check first ... micros only ... ES and NQ".*

## 1. The components and the book (daily net at one MNQ; Sharpe and Sortino on √252)

| series | net | a year | net Sharpe (Sortino) | max DD | largest year: \$ / vol units | D729 label |
|---|---:|---:|---|---:|---|---|
| A, the MACD arm | \$14,435 | \$2,502 | 0.78 (1.16) | \$7,814 | 2020 61 % / 2020 99 % | BOTH |
| F, NQ F2 | \$5,628 | \$975 | 1.05 (1.79) | \$990 | 2022 67 % / 2022 69 % | BOTH |
| C, NQ compression C1 (328 of its 387 trades fall in the window) | \$4,954 | \$859 | 0.91 (1.86) | \$1,058 | 2022 39 % / 2021 33 % | **NEITHER** |
| **the book B = A + F + C** | **\$25,018** | **\$4,336** | **1.22 (1.97)** | **\$4,920** | **2022 45 % / 2020 49 %** | **NEITHER** |
| E, ES F2 at 1 MES (correlations only) | \$3,329 | \$577 | 0.91 (1.57) | \$707 | 2022 60 % / 54 % | BOTH |

**Correlations between components** (pooled daily ρ):

| pair | pooled ρ | by year |
|---|---:|---|
| A–F | 0.02 | −0.14 to +0.20 |
| A–C | 0.11 | 0.03 to 0.24 |
| F–C | 0.02 | −0.05 to +0.25 |
| F–E | 0.87 | — (the same trade) |

**The book by year:**

| year | net | share |
|---|---:|---:|
| 2018 (from May) | −\$455 | — |
| 2019 | −\$634 | — |
| **2020** | **+\$10,349** | **41 %** |
| 2021 | +\$3,861 | 15 % |
| **2022** | **+\$11,327** | **45 %** |
| 2023 | +\$570 | 2 % |

**The book's Sharpe without each year:**

| year removed | 2018 | 2019 | **2020** | 2021 | **2022** | 2023 |
|---|---:|---:|---:|---:|---:|---:|
| Sharpe | 1.34 | 1.39 | **0.90** | 1.23 | **0.95** | 1.42 |

**Beside:**
- **The fractional equal-risk weights** (A 0.38, F 1.32, C 1.30) give Sharpe 1.52 (Sortino 2.82). They are not
  tradable: only whole micros trade.
- **Context only** (D727's follow book, declined as a strategy by the principal): book + T1 1.19, book + T1.5 1.45, both
  NEITHER.

## 2. The declared reading: **GO**

- **The largest year is ≤ 50 % in both units:** 2022 is 45 % in dollars, 2020 is 49 % in volatility units.
- **The Sharpe without the largest year (2022) is 0.95,** which is ≥ 0.5.

**Two of my own disclosures:**
- **The volatility-unit share is 49 %, one point from the bar.**
- **The rule tested one year, but the book has two:** 2020 and 2022 together carry 86 % of its net (89 % in
  volatility units).

## 3. POST HOC (computed after the reading; changes none of it): without both 2020 and 2022

| without 2020 and 2022 (937 sessions) | net Sharpe | net |
|---|---:|---:|
| **the book** | **0.34** (Sortino 0.49) | \$3,342 (about \$900 a year) |
| A, the MACD arm | 0.01 | \$67 |
| F, NQ F2 | 0.33 | \$636 |
| **C, the compression break** | **0.98** | **\$2,640** |

- **Outside its two big years the book is the compression break, plus a little NQ F2.** The arm earns nothing.
- **In volatility units, the arm's net is 99 % 2020.** Its fixed \$3.50 a trip costs more per unit of risk in calm
  years, so per unit of volatility its whole net is the crash year.

## 4. Predictions (§4)

| # | prediction | outcome |
|---|---|---|
| 1 | the largest year is 2022, at 35–50 % | **held** (45 %) |
| 2 | the label is NEITHER | **held** (but 49 % in vol units) |
| 3 | Sharpe without 2022 ≥ 0.5, so GO | **held** (0.95) |
| 4 | in-sample Sharpe below 1.5 | **held** (1.22) |
| 5 | adding T1 raises the Sharpe and keeps NEITHER (context) | **failed** on the Sharpe (1.19 < 1.22); NEITHER held |
| 6 | pairwise ρ among A, F and C below 0.3 in every year | **held** (largest 0.25) |

## 5. What it means

- **By the declared rule, a declared-book pre-registration for the joint run is worth writing,** on the principal's
  word.
  - The book clears no single year's dependence, and the three components are uncorrelated in every year.
  - In-sample, the three at one MNQ each make 1.22 net Sharpe (Sortino 1.97) at a \$4,920 drawdown, against the
    1.5–2 geometry.
- **The honest picture is narrower:**
  - this book is mostly a bet that stretches like 2020 and 2022 recur;
  - **outside them, it is the compression break (0.98) and little else** (0.34 for the book);
  - the vault (2025-03 → 2026-09) will say which.
- **ES adds nothing at micro.** Its one component (ES F2) is NQ F2's trade (ρ 0.87). D689 and D708 are net-negative at
  MES, and D699 is closed.
- **A declared book would have to state** its components (A, F, C), their sizes (whole micros, presumably one each), and
  its vault criterion. Its sizing should be read from the post hoc line, not the 1.22.

## Correction (2026-10-01, found while freezing D734)

**What was wrong:** §1 says "328 of its 387 trades fall in the window" for C. In fact 328 is the count to 2023-12-29,
and 17 of those fall before the window opens on 2018-05-14.
**The right count:** 311 C1 trades lie in the window.
**What does not change:** every dollar figure, Sharpe and share above was computed on the windowed series, as the
runner's daily aggregation filters to the window. Only the count in the sentence was wrong.
