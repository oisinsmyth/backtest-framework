# D564 — PRE-REGISTRATION: **basis-momentum as published** (Boons–Prado 2019) on the 17 commodity roots of the settlement strip — the twelve-month momentum of the first-nearby minus that of the second-nearby, High4 long / Low4 short, scored on the nearby return

**Pre-registration. Committed before the runner exists (R8). Result in a separate file.** In
sample 2016-01-04 → 2023-12-29; the long window 2011 → 2023 is a declared diagnostic; **the 2024+
slice is RESERVED AND NOT READ** (this is a new line; it keeps its holdout). Nothing admitted (R15).

*2026-09-19. The first study after the closure of the trend and carry-timing lines (D563). Taken
from the deposit's `BASIS_MOMENTUM.md`, which the principal chose over hedging pressure, skewness
and value. The deposit's caveat — "verify the exact definition, lookback, and rolling convention
against the published paper before building" — is discharged in §1 from Kwon, Kang and Yun (2021,
Finance Research Letters), who replicate Boons–Prado on 21 US commodities and state the
construction in closed form; the JF paper itself is behind a paywall from this machine and its
Internet Appendix replication series is not on disk, so the harness check is internal (§6).*

---

## 1. The construction — Boons–Prado as Kwon–Kang–Yun state it, nothing tuned

**Nearby contracts and returns.** At the last session of month *m* (the formation month-end), for
each root: the **first-nearby** T1 is the listed contract with the smallest delivery month that
is **at least two calendar months ahead** (delivery ≥ *m*+2), and for the five energy roots (CL BZ
HO RB NG), whose contracts expire in the month *before* delivery, at least three (delivery ≥
*m*+3) — so that the contract held through month *m*+1 never expires inside it, which is
Kwon–Kang–Yun's "a position in the futures contract whose maturity is after the end of month
*t*+1". The **second-nearby** T2 is the next listed delivery month after T1 with a settlement on
the formation session. The monthly return of the *n*th-nearby for month *m*+1 is
`settle(Tn, month-end m+1) / settle(Tn, month-end m) − 1` on the **same contract**, a fully
collateralised excess return with collateral yield taken as zero. Both contracts are re-chosen
at every month-end; the roll is the change of contract between consecutive formations.

**The signal**, with a twelve-month ranking period as published:

```
BM(11,0)_t  =  Π_{s=t−11..t} (1 + R1_s)  −  Π_{s=t−11..t} (1 + R2_s)
basis_t     =  F^{T2}_t / F^{T1}_t − 1                  (contango positive, the paper's sign)
mom_t       =  Π_{s=t−11..t} (1 + R1_s) − 1
```

A root is **eligible** at a month-end when all twelve monthly returns of both series are finite
and neither T1 nor T2 is **stale**: a contract whose settlement is unchanged across the three
sessions ending at the formation session is stale and the root sits out that month (the deposit's
§6.6 filter, threshold declared here: 3 sessions). Eligibility counts are reported per month-end.

**Universe.** The 17 commodity roots of the strip — CL BZ HO RB NG · GC SI HG PL PA · ZC ZS ZW ZL
ZM · LE HE — of which 13 are in Kwon–Kang–Yun's 21 (they lack BZ, PL, PA; we lack feeder cattle,
oats, rice, lumber, cocoa, coffee, cotton, orange juice). The paper's High4/Low4 on 21 names is
High4/Low4 here on ≤ 17; a month-end with **fewer than 12 eligible roots is flat**, counted.
Ties in BM are broken alphabetically by root symbol, counted.

**Portfolio.** Rank eligible roots on BM; long the top four, short the bottom four, equal weight
within legs, positions set at the month-end and held to the next, **scored on the nearby
return**: the daily same-contract return of the held T1 contract from the strip's settlements (a
session on which the contract has no settlement contributes zero). The book is D557's `book_return`
convention — the equal average over positioned roots of sign × return, dollar-neutral in weight
space, which is half the paper's High-minus-Low; Sharpe is scale-free and both scales are printed.

| cell | | |
|---|---|---|
| **EW High4/Low4, published (PRIMARY)** | sign ∈ {+1, 0, −1} into `book_return` | as published |
| EW terciles, published | `ceil(n/3)` a side, D557's rule | comparability with D557–D559 |
| dollar High4/Low4 at minimum size | one minimum-size contract per positioned root in T1; $3/$6 a round trip plus one tick; a change of T1 between formations is a roll, two sides; BZ untraded (roll count, as D555) | the component line |
| **time-series form**, published | per root, sign(BM − the root's own expanding mean of BM from its live start, after 12 observations), the deposit's §9 prop-compliant form, D556 cell B's demeaning rule; vol-scaled at 40 % as D555 | the paper predicts in the time series too; expected weaker |

**Family for N2: these four cells.** Ranking-period variants (Kwon–Kang–Yun's BM(5,1), BM(0,0),
BM(11,6)), other maturity pairs, curvature extensions, de-seasonalised or vol-multiplied
signals are **not run**: each is a different construction and would be selection on this window.
One declared robustness diagnostic, unpromotable: the primary recomputed on the **nine
non-seasonal roots** (energy ex-NG, metals) as High3/Low3 — the deposit's §6.4 "restrict to
non-seasonal markets as a robustness check", chosen here over de-seasonalisation.

**Causality.** The formation session's settlements are published that evening (D497, D556); the
position earns from the next session. BM at month-end *t* uses monthly returns through *t*.

## 2. The statistic

> **PRIMARY: gross annualised Sharpe of the EW High4/Low4 book on the nearby return,
> 2016-01-04 → 2023-12-29**, with a monthly block-bootstrap SE. Sortino beside it (R17).

## 3. Nulls

**N1** — enumerated rotation of the held membership grid within each root's span, offset common
to all roots, purged 252 sessions at both ends (D555 §2), leg sizes preserved at every offset
because the 17 share one span; profile stored. **N2** — the family maximum over the four cells at
each surviving offset. **N3 (diagnostic, the instrument D561/D562 recommended)** — the
**name-randomised null**: at each month-end keep the leg counts and draw which eligible roots
fill them, 2,000 seeded draws, each scored on the primary window; p50, p95 and the bootstrap SE
of the p95 reported, a margin within 2 SE recorded UNRESOLVED (D373). N3 separates the timing of
the membership from its tilt; it does not enter the PASS rule.

**PASS requires: the primary > 0, above its N1 p95, AND the family maximum above its N2 p95.**

## 4. Predictions — in the runner's quantities

| # | prediction | source |
|---|---|---|
| **P-1** (primary) | EW High4/Low4 gross Sharpe 2016–2023 **> 0 and above N1 p95**; point **0.25 – 0.55** | Kwon–Kang–Yun Table 1: High4−Low4 nearby return 8.06 %/yr, t 3.47, **Sharpe 0.81** on 21 commodities 1979–2017; the deposit's "expect half"; 17 roots and 8 years below that |
| **P-2** (T0 orthogonality, the deposit's stop rule) | mean cross-sectional Spearman ρ at month-ends of BM with **basis**: **\|ρ\| < 0.7**, point −0.2 … +0.2; with **mom**: \|ρ\| < 0.5 | BM cumulates past *changes* of slope; the current slope is a different quantity |
| **P-3** (composition) | annual turnover of the primary book in weight units **> D557's 5.6**; point 8 – 15 | the paper: more diverse composition than basis sorts |
| **P-4** (M6, the mechanism's direction, declared before looking) | gross Sharpe **2016–2023 ≥ 2011–2023's first half (2011-07 → 2015-12)**: no post-2010 decay | the deposit §3: post-crisis balance-sheet regulation should *strengthen* it; the decay story predicts the opposite; either outcome is recorded |
| **P-5** (T4, the tail with carry) | c5 of the primary book on **D556 carry A's worst 5 % of days**, in the primary's σ, **< 0**, point −0.1 … −0.4; the vol-matched blend's drawdown ratio **not below** its rotation null's p05 | both are intermediary-liquidity premia (deposit §5, §7.5); D561's instrument |
| **P-6** (volatility, §2.8) | the primary's monthly return in formation months whose cross-sectional mean EW vol is **above** its 2016–2023 median exceeds that in months below it | the paper: increasing in volatility |
| **P-7** (spreading return) | the High4−Low4 **spreading** return (long T1, short T2, per leg) **> 0** | Kwon–Kang–Yun: +0.78 %/yr, t 2.32 |
| **P-8** (breadth) | primary P&L positive on **≥ 9 of 17** roots over 2011–2023 | a documented cross-sectional effect |
| **P-9** (vehicle) | dollar book daily σ **> $500**; the C-d-eligible sub-book reported; the largest single root share of the dollar total reported (palladium is in this universe) | D555–D559 |
| **P-10** (falsifiers) | \|ρ(BM, basis)\| **> 0.7** → the mechanism has collapsed into carry at this scale and the deposit's own rule stops the programme. The T1 harness (§6) failing → the data layer is wrong and nothing is interpretable. Harness green and the primary **below N1 p50** → the sort did badly here | |

Reported beside them, all four groups: net beside gross with turnover cost and breakeven bp/side;
the root-month distribution with symmetric 1 % trims per leg and combined; concentration by root,
roots to half the P&L, top-1/3/5 share; per-year and per-era; eligibility, leg sizes and ties per
month-end; the number of formation months in which T1 changed (rolls); the per-root dollar
decomposition BEFORE the component line; the time-series cell's per-root sign persistence.

## 5. The component line

The dollar High4/Low4 cell: C-a net Sharpe at minimum size under the cost that size pays, C-c
skew, C-d daily σ, hit, gross beside net, the C-d-eligible sub-book, the per-root table, and ρ
with the ledger's live entry (absent unless its daily P&L is on disk — it is not). **Every cell
gets a component line whether or not it clears.**

## 6. Runner assertions and the harness

- **Signal by a second path:** BM, basis and mom recomputed for 300 random (root, month-end)
  cells by a pandas implementation reading the raw strip — its own contract selection by the
  delivery rule, its own monthly returns — never calling the runner's functions; exact agreement;
  proven to raise on a negated grid and on a grid with one month's return dropped.
- **Held-contract audit:** the T1 chosen at each formation has a settlement on the next
  month-end session in ≥ 99 % of positioned root-months (it did not expire inside the holding
  month); the shortfall listed by root.
- **Leg membership by a second path:** pandas `rank` per month-end; proven to raise on one
  swapped long/short pair.
- **Lag, sign in money (on the strip's T1 price change × usd_per_point), right quantity** — D555's
  three, each proven to raise.
- **Harness, internal:** (a) the strip's T1 monthly return and the breadth fixture's front
  monthly return correlate **> 0.9** per root on 2011–2023, median across roots; (b) the sign of
  `basis` at month-ends agrees with the sign of −`carry_ann` from D556's curve table on the same
  session in **> 80 %** of cells (different contract choice, same slope); (c) the exactness guard
  on 20 offsets against the plain loop. A harness failure fires P-10's second clause.
- `REQUIRED_OUTPUTS` guarded; `max_drawdown_convention` first; `encoding="utf-8"` everywhere.

## 7. What is read, and what is not

The settlement strip and the breadth fixture from 2010-06 (warm-up for the twelve monthly
returns; the first eligible formation is 2011-06 or later and the record says which), the curve
table for the harness and for D556's carry A rebuilt in-process for P-5, **all filtered below
2024-01-01 before anything is computed. Not read: any session from 2024-01-02 onward.** No COT
(the deposit's §7.6 negative control against hedging pressure is a separate declared read on the
COT fixture, not this record). No HKM factor, no dealer statistics (§4 is development work after
this resolves, as the deposit says).

## 8. What this record does not do

No ranking-period, pair or curvature variant; no de-seasonalisation; no vol multiplier; no
extension to FX or equity index (the deposit's own open question 2 blocks it); no calendar-spread
execution form (the dollar book is two outrights). A flat result is a result about
basis-momentum on these 17 roots and this window under the paper's construction, provided the
harness holds. Projected wall time under five minutes.
