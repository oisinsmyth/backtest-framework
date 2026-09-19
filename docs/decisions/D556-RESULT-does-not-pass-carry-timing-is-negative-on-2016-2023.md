# D556 RESULT — **DOES NOT PASS**: carry timing as published is **−0.20 gross** on 2016–2023, below its own null's median, after **+1.61** on 2011–2015; it is uncorrelated with trend (ρ 0.18) as the deposit said, and adding it at equal weight lowers the trend book's Sharpe while shallowing its drawdown

*2026-09-19. Spec committed in `60ec9f6` BEFORE the fixture builder and the runner (R8). Primary
window 2016-01-04 → 2023-12-29 (2,065 sessions); long window 2011-01-03 → 2023-12-29 as the declared
diagnostic; **the 2024+ slice was not read.** Nothing admitted (R15). Nothing closed. Fixture
`scripts/build_fut_settle_strip.py` (both metas carry `all_gates_pass`), runner
`scripts/run_d556_carry_timing.py`, output `data/d556_carry_timing.json`, 89 s.*

**The data layer passed every gate and the effect is absent on the window.** The settlement strip
reproduces D526's independent CL/GC extraction exactly (263,983 rows, settlements identical), the
front settlement sits within a median 0.31% of the session close on the worst root, and every audit
fired on its deliberate break. On that foundation the KMPV timing rule — long backwardation, short
contango, vol-scaled, held a month — returns **−0.20 gross** on 2016–2023 (SE 0.35), at the **38th
percentile** of a purged rotation null whose median is −0.08. The same rule earned **+1.61** on
2011–2015 and **+0.38** over the long window. Four of eight predictions held: the ones about carry's
*character* (uncorrelated with trend, negatively skewed, loses in March 2020, positive on 23 of 36
roots over 13 years). The ones that inherited a *magnitude* did not.

---

## 1. The declared verdict

| | | |
|---|---|---|
| **PRIMARY** — cell A (carry sign), published book, gross Sharpe 2016–2023 | **−0.204** (SE 0.35) | N1 purged: p05 −0.69, p50 −0.08, **p95 +0.51**, rank **0.375** → **INSIDE, below the median** |
| **N2 family**, 6 declared cells | best **+0.246** (B / dollar) | p50 **+0.25**, p95 +0.83, rank 0.49 → **INSIDE** — the family's best is the null's median, as in D555 |

| prediction | | |
|---|---|---|
| **P-1** primary > 0, above N1 p95; point 0.2–0.5 | −0.204 | **fails** |
| **P-2** \|ρ(carry, trend)\| daily < 0.3; point ≈ 0.1 | **+0.179** (monthly +0.123) | **holds** |
| **P-3** combination C > max(A, D555's +0.304) | +0.204 | **fails** — but see §4 |
| **P-4** skew < 0 and March 2020 < 0 | skew −0.20; **March 2020 −4.1%** (trend that month +21.0%) | **holds** |
| **P-5** turnover < 14.7 weight-units/yr and sign persistence > 0.8 | turnover **24.3**; persistence **0.93** | **fails** on turnover: the *sign* is slow but the vol scale is re-read monthly, and on the 100×-levered rates legs that is the turnover |
| **P-6** P&L positive on ≥ 21 of 36 roots, 2011–2023 | **23 of 36** (16 of 36 on 2016–2023) | **holds** |
| **P-7** commodity-only < diversified | CM −0.26 vs all −0.20 | **holds**, trivially: both negative |
| **P-8** falsifier | gates green, primary **below N1 p50** | **fires: carry did badly here**; the fixture is not the reason |

## 2. Performance — net and gross, the four groups

**Cell A, published book (MOP-style equal average of 40%-vol positions), 2016–2023:**

| | gross | net (turnover) | net incl. rolls |
|---|---:|---:|---:|
| Sharpe | **−0.204** | −0.219 | −0.332 |
| ann. vol · max drawdown | 11.6% · **−43.5%** | | |
| hit (days) · skew · kurtosis | 50.5% · −0.20 · 2.8 | | |
| turnover · cost | 24.3 weight-units/yr → 18.5 bp/yr | | |

Long window 2011–2023 gross **+0.38**. Eras: **2011–2015 +1.61**, 2016–2019 −0.36, 2020–2023 −0.07.
Years: 2011 +1.91, 2012 +1.11, 2013 +1.09, 2014 +1.43, 2015 +2.31, then **2016 −0.77, 2017 +0.13,
2018 +0.22, 2019 −1.12, 2020 −1.48, 2021 +1.63, 2022 +0.48, 2023 −0.46**. Five consecutive positive
years before the primary window, three of eight inside it. Sectors 2016–2023: FX +0.26, equities
+0.08, **fixed income −0.31, commodities −0.26**; over 2011–2023 all four are positive (+0.21, +0.37,
+0.10, +0.15).

**Group 2 — root-months (3,187, 2016–2023, units of book return):** mean −6.1e-5, **median +2.0e-5**,
ex-top-1% −16.6e-5, ex-bottom-1% +6.8e-5, symmetric trim −3.7e-5; win 50.3%, payoff 0.95, skew −0.38.
**Only 34% of root-months are long** (39% of root-month carries are positive): the book is mostly
short contango, and the short months lose (−1.6e-4 each) while the long months earn (+1.3e-4).

**Group 3 — what the losers depend on.** Worst roots on 2016–2023: **6C −0.71** Sharpe, TN −0.99,
BTC −0.70, SR3 −0.66, NG −0.60, UB −0.50, GC −0.45 — gold is short every month it is live (carry
never positive) and rallied; the rates legs carry the same 100×-plus positions D555 recorded (ZT 107×,
SR3 125×) and are where the turnover lives. Best: 6A +0.63, PA +0.55, ZB +0.46, 6J +0.43 (short every
month, yen fell), YM, 6E, 6B. Carry sign persistence is 0.93 month to month; the state is a regime,
which is D526's finding on CL from the other direction.

**Group 4 — nulls** in §1: SE 0 by enumeration; the primary sits below the median.

## 3. The component line — and what the dollar book is actually made of

| | A / dollar (34 roots, min size) | C-d sub-book (17 roots) |
|---|---:|---:|
| **C-a** net Sharpe | **+0.199** (SE 0.31); gross +0.226 | +0.030 |
| **C-c** skew · **C-d** daily σ | **−0.78** · **$7,341** | · $1,514 |
| total · max DD · cost | +$215,975 · −$299,974 · $26,426 (3,860 sides + 4,614 roll sides) | |

**The dollar book's sign is not carry's sign.** The published book is −0.20 and the dollar book +0.20
on the same signs because one contract of **palladium** (σ **$4,344** a day at full size, thirty times
a micro) contributes **+$276,410** of a **+$215,975** total; without it the book is negative, and the
next two contributors (ZB +$43k, 6J +$33k) do not cover the two largest losers (UB −$72k, TN −$36k).
A minimum-size book across 34 roots is a weighted bet on whichever full-size contracts have the
largest dollar σ, and it can disagree in sign with the equal-risk book it is meant to express. **Not
entered: fails C-c and C-d, and C-a is one instrument.** Cells B and C fail the same way.

## 4. Trend and carry together — the deposit's actual claim, and what held

The deposit put carry in the book for the *shape* of the combined curve, not its return. Measured:

| | D555 trend 12m | carry A | **C = (trend + carry)/2** |
|---|---:|---:|---:|
| gross Sharpe 2016–2023 | +0.304 | −0.204 | **+0.204** |
| max drawdown | **−36.4%** | −43.5% | **−28.8%** |
| ρ with trend (daily) | 1 | **+0.18** | |
| worst-5%-days overlap with trend | | 29% | |

Equal-weighting a −0.20 leg into a +0.30 leg cost a third of the Sharpe and **cut the drawdown by a
fifth** — the decorrelation is real (P-2) and the drawdown claim held; the return claim did not, and
P-3 was written on the return. The deposit's own rule — "the right question of a fundamental
component is whether it reduces the depth of the worst stretch" — is the one this window answers yes
to, at the price it names.

## 5. What was not done, and what is still wrong with this

- **No de-seasonalisation** — NG (mean carry −0.22, Sharpe −0.60) and HE (−0.18) are the roots where
  the paper's basic measure reads the calendar; a seasonal-adjusted carry is a different, declared
  construction. **No vol cap**, as in D555. **No cross-sectional sort** (deposit strategies 3–5).
- **The published number KMPV report (0.6 per class, 0.9 global) is on 1972–2012**; the long-window
  +0.38 here and the 2011–2015 +1.61 are consistent with the effect having been present and then
  absent, and this record cannot separate decay from a bad decade. The AQR-style free benchmark D555
  had does not exist for carry; the harness rests on G1 and G3.
- **The financial-futures carry is the futures-implied basis** (financing minus dividends, rate
  differentials), as the deposit specifies; on the rates legs its sign is close to a constant (long
  share 72–85%), so "carry timing" on ZN/ZB/UB/TN is mostly a long bond position through 2022.
- The 2011–2023 null was not enumerated, as in D555; it is a two-minute read.


---

*Addendum, 2026-09-19, under [R17](../RULES.md#r17) (every reported Sharpe carries a Sortino).* Re-run with the Sortino beside every Sharpe; no previously written number changed. **Cell A published, 2016–2023: Sharpe −0.204, Sortino −0.280**; purged null Sortino p50 −0.12, p95 +0.75 (Sharpe p50 −0.08, p95 +0.51). The Sortino is below the Sharpe: the carry book loses in its large days, which is the negative skew §1 P-4 predicted, now in the ratio. Verdict unchanged; every cell carries both ratios in `data/d556_carry_timing.json`.
