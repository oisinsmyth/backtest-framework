# D466 — the components ledger: the standard, and the scoring of every futures construction tested so far as a component

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D466-the-components-ledger-standard-and-the-scoring-of-every-futures-construction-tested-so-far-as-a-component.md`. The H1 above is the full title.*

**Pre-registration of a STANDARD and a scoring. Committed before the scorer exists (R8).** Result
in a separate file. In-sample 2016-01-04 to 2023-12-29 on the futures fixtures; **2024-01 onward
unread.** D466 taken after `ls docs/decisions` and `git log --all` on both worktrees showed D465
used on master and D462 used again in the other worktree (a number clash of theirs with D462 on
master; noted, not this record's to resolve).

## 0. Why

The principal's construction for the prop book is layering: components with net Sharpe above
0.5 and low mutual correlation, sized to equal risk, tested as a book against hurdle P. Three
prop records this week (C1, D463, D464) were written at the candidate altitude only, and two of
their objects — the overnight ES hold (net Sharpe 0.62) and the last-half-hour NQ trade (0.42) —
are components at correlation 0.09 whose equal-risk combination is 0.91. CLAUDE.md now requires
both altitudes on every record; **this record fixes the standard and scores what already exists**,
so that the ledger opens with numbers computed under a declared rule rather than the ones that
caught the eye.

## 1. The standard (copied verbatim into `docs/COMPONENTS_PROP.md`)

C-a net annualised Sharpe of the daily P&L > 0.5 at the instrument's minimum tradable size;
C-b correlation with every component already entered < 0.3; C-c skew ≥ −0.5; C-d daily σ at
minimum size ≤ 1% of a $50k account; C-e a pre-registered record. Sharpe with a monthly block-
bootstrap SE; entry order recorded; a gated subset of a component is not a component; two non-
overlapping windows on one instrument are two.

## 2. What is scored (every futures construction with a committed daily series)

| construction | series | size unit | cost per round trip |
|---|---|---|---|
| **K1** C1: ES hold 18:00 → 16:00, every same-contract night | `es_c1_holds` (D449), 2016–2023 | 1 MES ($5/pt) | $3 |
| **K2** last-30-min momentum, NQ | `d463_trades` | 1 MNQ ($2/pt) | $3 |
| **K3** last-30-min momentum, ES | `d463_trades` | 1 MES | $3 |
| **K4** last-30-min momentum, YM | `d463_trades` | 1 MYM ($0.50/pt) | $3 |
| **K5** C1 on S1 nights; **K6** C1 on S2-exposure nights | D464 | 1 MES | $3 |

K5 and K6 are scored and, by the standard, **cannot enter beside K1** (gated subsets). The
scoring is: daily net P&L in dollars at the size unit (zero on days the construction is flat),
net annualised Sharpe with SE, hit rate on active days, skew, the full pairwise correlation
matrix on matched days, and **the entry order the standard produces** (highest Sharpe first,
each next one admitted only if C-b holds against those already entered).

## 3. The assembled book, scored here as a REPORT (its hurdle-P test is D468's)

Equal-risk weights (1/σ over the in-sample window, static), the book's daily net P&L, its
Sharpe with SE, its worst day, its max drawdown on closes, and the Sharpe by year — for the set
the standard admits. Reported so D468 has a declared target; not gated here.

## 4. Predictions

- **X-a** K1 net Sharpe **0.55–0.70**, K2 **0.35–0.50**, K3 **−0.05–+0.10**, K4 **< 0**; K5, K6
  0.35–0.55.
- **X-b** ρ(K1, K2) **0.05–0.15**; ρ(K2, K3) **0.7–0.85**; ρ(K1, K5) and ρ(K1, K6) **> 0.3**
  (subsets).
- **X-c** the standard admits **K1 and K2 and nothing else** (K3 fails C-a; K4 fails C-a; K5/K6
  fail C-b against K1); the equal-risk book of K1 + K2 has Sharpe **0.8–1.0**, worst day
  **−2 to −4%** of a $50k account at 1 micro each (2020-03-16), max drawdown on closes 6–12%.
- **X-d** at one micro each the book's daily σ is **0.5–0.7%** of the account (C-d passes).

## 5. What follows this record (declared here, run under their own numbers)

- **D467 — the extended data layer:** the 26 archive files read once more for session-hold tables
  (18:00 → 16:00, same-contract, 1-minute path extremes, D449's construction) on **ES, NQ, YM, ZN,
  ZB, GC, CL, 6E**, gated as D462, committed as compact per-night tables; the RTH last-30 window
  already exists on ES/NQ/YM.
- **D468 — the wider scoring and the assembled book:** overnight holds on the seven other roots
  and any other declared window scored against this standard in the order the standard produces;
  then the assembled book, risk-parity at micro granularity, through D440's lifecycle for
  hurdle P and V, on 2016–2023; **the book is confirmed on the unread 2024 slice under a later
  record and the principal's word.**

## 6. Files

This record · `docs/COMPONENTS_PROP.md` (the ledger; opened by this record) ·
`scripts/run_d466_components.py` (`--run`, `--selftest`) · `data/d466_components.json` · RESULT.
