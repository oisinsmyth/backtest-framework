# D468 — the wider component scoring: three session windows on eight roots against the ledger's standard, with the family-maximum null, and the assembled book through the lifecycle

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file.
In-sample **2016-01-04 to 2023-12-29** on D467's session tables (or each root's `usable_start`
if later); **2024-01 onward unread; no holdout spent.** D468 taken after `ls docs/decisions` and
`git log --all` on both worktrees showed D467 as the highest number. Declared in D466 §5.

## 0. Why, and the rule that shapes it

The ledger is empty (D466): the gross edges exist at micro size and the $3 round trip eats them.
The plan (MFFU Rapid EOD 50K, BOOK_PROP) requires **flat by the 16:10 ET close**, so **every
session is at least one round trip** and no construction can amortise the cost over nights;
the two-night hold floated in the D466 RESULT §3 is foreclosed by the rule, not by data. What
remains is the search across instruments and within-session windows for a construction whose
**gross mean per round trip is large against $3 (or $6) and its own σ**. D467 built the tables;
this record declares the windows, scores them under the standard **in the runner**, reports the
null of the best-of-family, and assembles what enters into the book hurdle P is tested on.

## 1. The constructions (declared; nothing added after the numbers are seen)

On each root D467 passes (of ES, NQ, YM, ZN, ZB, GC, CL, 6E), **three windows, long only**, one
round trip each, entered at the segment's open and exited at the segment's close, on
**same-front sessions only** (D449's rule; roll nights dropped):

| | window | entry | exit | what it is |
|---|---|---|---|---|
| **W1** | 18:00 → 16:00 | `h18_o` | `h15_c` | the full session held (C1's construction) |
| **W2** | 18:00 → 09:00 | `h18_o` | `h08_c` | the overnight leg, exited before the cash-open hour |
| **W3** | 09:00 → 16:00 | `h09_o` | `h15_c` | the day leg |

W2 and W3 partition W1 (up to compounding). **24 constructions at most.** The short side of each
is the negative of the long and is **reported, never entered** — the family is 24 long tests,
and the null in §3 is sized to it. Nothing at a finer grid, no gates, no signals: these are the
components' clocks, and D464 showed gating buys nothing here.

**Size unit and cost per round trip** (D467 §5): MES $5/pt, MNQ $2/pt, MYM $0.50/pt, MGC
$10/oz, MCL $100/bbl, M6E $12,500 × Δprice, each **$3**; ZN and ZB one full contract at
$1,000/pt, **$6**. Daily P&L in dollars at that unit, zero on flat days, on the union calendar of
the roots' sessions — D466's construction, so every number here is comparable to K1–K6.

## 2. The scoring (the ledger's standard, computed in the runner)

Per construction: net and **gross** Sharpe with the monthly block-bootstrap SE, mean and σ per
day in dollars, the cost as a share of the gross mean and of σ, hit rate on active days, skew,
worst day, annual net, Sharpe by year; the full 24 × 24 correlation matrix; then the
**admission order the standard produces**: descending net Sharpe, each admitted only if C-a
(> 0.5), C-c (skew ≥ −0.5), C-d (σ ≤ 1% of $50k) hold and C-b (ρ < 0.3) holds against every
prior entry. **K1 (ES W1 from D449's table) is re-derived here as ES-W1** and must agree with
D466's K1 to within the hourly-vs-minute difference (§5 X-a).

## 3. The family-maximum null (the multiplicity D466 owes)

With ~2,000 days the SE of an annualised Sharpe is ≈ 0.35, so the best of 24 draws under no
edge sits near +0.6: **C-a on the point estimate is under the noise ceiling of this family.**
The null: **sign randomisation per session, common across all 24 constructions** (the same
sign vector applied to every construction's daily P&L, which preserves the cross-construction
correlation), 2,000 draws; the statistic is the **maximum net Sharpe across the family**; the
RESULT reports its p50 and p95 with the bootstrap SE of the p95 (D373's rule) beside the
observed maximum. **A construction that clears C-a but not the family p95 is entered as
PROVISIONAL** — the ledger gains a column for it — and only the unread 2024+ slice, under the
principal's word, promotes or removes it. This rule is added to `docs/COMPONENTS_PROP.md` by
this record's commit.

## 4. The assembled book (only if the standard admits ≥ 1 construction)

- **Weights:** equal risk at micro granularity — per component, contracts on day t =
  `floor(f · 50,000 / (n · σ̂_k,t))` with σ̂ the trailing 21 traded days' σ per contract (R9,
  D463's rule), capped at 4× static, on D463's grid **f ∈ {0.2, 0.4, 0.7, 1.1}%** plus the
  one-micro-each line.
- **Path:** the book's intraday path is hourly (D467's grid); the book's low in an hour is the
  **sum of the components' lows** and its high the **sum of the highs** — both adverse for a
  trailing floor that ratchets on the high — so the lifecycle result is a conservative bound.
- **Hurdle P** through D440's `simulate_provider` on the MFFU Rapid EOD 50K plan (P3 worst day,
  P4 funded life and pass probability, P5 day-share, V with SE, `p_breached`), 3,000 paths, 600
  days, as D463; and the book's net Sharpe, worst day, max drawdown, by-year, in-sample.
- **No confirmation here.** The 2024+ slice is read only under a later record and the
  principal's word.

## 5. Predictions (written before the runner)

- **X-a** ES-W1 net Sharpe within **±0.03** of K1's +0.37 on 2,043 ± 10 sessions.
- **X-b** Of the 24: **1–4** clear C-a on the point estimate; the family-max null p95 is
  **+0.65 to +0.90**; **0–1** clear it.
- **X-c** Where: **NQ-W1 +0.40 to +0.70** (the strongest published overnight drift is the
  Nasdaq's; MNQ's cost share is 1.85 bp); **GC-W2 +0.20 to +0.50 and GC-W3 negative** (the
  gold overnight-up / day-down pattern); **ZN-W1, ZB-W1 ≤ +0.2** (2022 inside the window);
  **CL-W1 ≤ 0** (contango drag on a long); **6E-W1 within ±0.3**; **W2 beats W3 on ES, NQ, YM**
  (the drift is overnight, D259).
- **X-d** ρ(W2, W3) on one root **|ρ| < 0.15**; ρ(ES-W1, NQ-W1, YM-W1) **> 0.85**, so at most one
  index root enters; ρ between index and ZN/ZB W1 **−0.4 to 0**; GC and 6E to the rest **|ρ| < 0.3**.
- **X-e** If two or more enter with ρ < 0.3, the equal-risk book's net Sharpe exceeds the best
  single entry by **≥ 15%**, and V(book) > V(best entry) at every f on the grid; if only one
  enters the book is that construction and D463/D464's standalone verdict repeats (P4 < 3 yr).
- **X-f** Runtime under **2 min** (tables are 30k rows; the null is 2,000 × 24 Sharpes on
  2,000 days); the lifecycle 1–3 min per f.

## 6. Files

This record · `scripts/run_d468_wide_components.py` (`--run`, `--selftest`) ·
`data/d468_wide_components.json` · `data/d468_book_days.csv.gz` (the book's daily table at
each f, if a book exists) · the ledger's new rows · RESULT.
