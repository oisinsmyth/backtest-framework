# D779 STAGE 0 RESULT — NO EFFECT on every root: skipping the closing-auction fall-side buys on days the 10-year Treasury future fell removes winners, and in 2022 itself the losing buys came on days Treasuries did NOT fall

*2026-10-03. One run of `scripts/stage0_d779_auction_fade_rates_filter.py --run` (22 seconds).*
- **The order:** the [pre-registration](D779-STAGE-0-PRE-REG-the-closing-auction-fade-with-a-rates-filter.md)
  (`3d1b9469`) came before the runner (`655fa174`), and the runner before its one run.
- **Output:** `data/stage0_d779_auction_fade_rates_filter.json` (statistics only).

## 0. Checks

- **Right quantity:**
  - the base book reproduced D778's on all four roots (M2K 280 trades, +\$15.84);
  - base = kept + removed;
  - offset 0 equals the observed for N and for F(b);
  - nothing on or after 2024-01-01, equity or ZN (2,063 ZN days).
- **The lag audit:** an explicit-loop second implementation over the raw equity and ZN rows re-derived c, ZFELL, the
  keep decision and the fade on 40 sampled base trades per root; all equal.
- **ZN readings:** present on 99.7% of M2K's valid sessions.
- **The self-test:**
  - a planted ZFELL continuation passes F;
  - a flag tracking nothing fails F;
  - a 2022-only continuation passes F(a) and F(b) and fails F(c);
  - a missing or two-contract reading keeps the trade;
  - ZFELL reads no other day;
  - the second implementation raises on a broken keep and on a broken ZFELL;
  - chunk = whole; the base-book guard fires; the whole study runs end to end.

## 1. The gates (M2K primary)

| | value | gate |
|---|---|---|
| the base L4 book (D778's) | 280 trades, +\$15.84 gross / +\$12.08 net (t 2.47) | — |
| **G1:** the F1 book | **211 trades, +\$12.13 gross / +\$8.37 net, t 1.62** | **fail** |
| N: exact rotation of the F1 signal | p50 −\$1.50, p95 +\$9.24, rank 0.982 | pass |
| **F(a):** the removed trades' mean gross | **+\$27.21 (69 trades): winners** | **fail** |
| **F(b):** Δ against the rotated ZFELL flag | **Δ −\$3.72**, against p50 −\$3.58 and p95 +\$1.22; rank 0.48 | **fail** |
| F(c): outside 2022, removed against kept fall-side buys | +\$34.70 (56) against +\$36.83 (64) | pass (by \$2) |
| Y | win ≥ 50% in 4 of 5 full years; volatility-adjusted > 0 in 4 of 5, 2016–19 0.14 against 0.17 | pass |
| G2 | net t 1.12; net +\$42 without 2020 and 2021; ex-2022 +\$16.12; trimmed +\$11.78 (bar \$7.52) | fail |

**Reading: NO EFFECT** (G1 fails first). The filter also fails F(a) and F(b). **GO false.**

- **F(c)'s pass is empty.** A \$2 gap on 56 and 64 trades is noise: under no effect, a strict "below" comparison
  passes about half the time. The pre-registration did not give it a null. F(b), which does have one, ranks 0.48.
- **The predictions:**
  - "F(a) passes": WRONG.
  - "F(c) is the gate at risk": it passed trivially, and F(a) and F(b) failed first.
  - "G2 at risk": it failed.

## 2. What happened in 2022: the mechanism fails in its own year

**M2K's fall-side buys (the base book), split by the ZN state:**

| year | ZN fell: n, mean gross | ZN did not fall: n, mean gross | share removed |
|---|---|---|---|
| 2018 | 6, +\$5.67 | 10, +\$22.90 | 38% |
| 2019 | 10, +\$7.80 | 10, +\$48.05 | 50% |
| 2020 | 15, **+\$57.00** | 24, +\$40.69 | 39% |
| 2021 | 19, **+\$49.84** | 12, +\$28.17 | 61% |
| **2022** | **13, −\$5.04** | **4, −\$123.00** | 76% |
| 2023 | 6, +\$4.83 | 8, +\$41.63 | 43% |

- **The rates story predicted 2022's losses would sit on the rising-yield days. They did not.**
  - The 13 rising-yield-day buys lost \$5 a trade, about flat.
  - The four other buys lost \$123 a trade.
  - So the loss came from falls on days the 10-year was flat or up. Four trades is too few to say what they were.
- **In other years the state does not sort the trades consistently.** Rising-yield-day dips earned less in 2018, 2019
  and 2023, and more in 2020 and 2021.
- **The shorter ZN windows (reported) fail the same way:**
  - 15:00 → 16:00: removed 51 trades at +\$33.19, F(b) rank 0.38;
  - 15:50 → 16:00: removed 36 trades at +\$39.38, F(b) rank 0.34.
  - Both remove 2022's buys at −\$26 to −\$27 and the other years' at +\$4 to +\$117.

## 3. All four groups (M2K, the F1 book)

| | |
|---|---|
| mean gross / net; median net | +\$12.13 / +\$8.37; +\$4.74 |
| net Sharpe / Sortino; gross Sharpe | 0.48 / 0.72; 0.69 (base: 0.81 / 1.25) |
| exposure; maximum drawdown; total net | 15.5% of sessions; \$983; +\$1,766 (base \$1,167; +\$3,384) |
| mean \|move\| against the round trip; breakeven cost | \$78.05 against \$3.76; \$12.13 |
| win; payoff; skew; kurtosis | 54.0%; 1.12; +0.09; 2.48 |
| net ex-top 1% / ex-bottom 1% / trimmed | +\$4.68 / +\$11.71 / +\$8.02 |
| sides kept, net | fall (long) +\$23.67 (68, t 2.03); rise (short) +\$1.09 (143) |
| \|c\| terciles, net | +\$0.29 / +\$15.59 / +\$9.34 |
| by year, net (kept) | 2018 +\$5.04, 2019 +\$1.63, 2020 +\$20.78, 2021 +\$12.57, **2022 −\$14.84**, 2023 +\$14.04 |
| settlement-clock regimes, net | before 2020-10-26 +\$13.76 (118); to 2021-06-25 +\$14.85 (22); after −\$2.60 (71) |
| drift-adjusted (drift +\$3.82 a night) | fall side kept +\$23.61; rise side +\$8.67 |
| five largest / worst | 2020-03-13 +\$495, 2022-01-24 +\$293, 2020-03-20 +\$283, 2023-03-14 +\$248, 2022-05-05 +\$218 / 2022-06-15 −\$348, 2020-04-06 −\$335, 2023-12-13 −\$274, 2022-09-28 −\$266, 2020-04-03 −\$247 |

- **The component line:** daily ρ with D775 +0.019, D777's MNQ book −0.023, D737's twin −0.059, NQ F2 −0.057, C1
  +0.034.
- **The other roots:**

| root | F1 trades | mean gross (t) | N rank | removed (mean) | 2022's removed | F(b) rank | reading |
|---|---|---|---|---|---|---|---|
| MES | 314 | +\$8.69 (0.96) | 0.945 | 90 (+\$19.39) | 18 (−\$14.17) | 0.46 | NO EFFECT |
| MYM | 293 | +\$7.22 (0.89) | 0.942 | 86 (−\$0.44) | 20 (−\$24.88) | 0.80 | NO EFFECT |
| MNQ | 337 | +\$15.65 (1.39) | 0.968 | 94 (+\$21.83) | 16 (−\$45.62) | 0.62 | NO EFFECT |

  MYM is the only root where the removed trades lost (F(a) passes), and its F(b) rank of 0.80 still fails.

## 4. The reading

- **Declared:** NO EFFECT on every root; the filter fails F(a) and F(b). GO false.
- **The rates mechanism for 2022 is refuted in-sample.**
  - Rising-yield days do not mark the closing-auction drops that continue overnight, in 2022 or in other years.
  - A rotation of the same flag removes as much.
- **Together with D778,** neither a trend state nor a rates state, both known by 16:00, separates 2022's losing
  dip-buys from the other years' winning ones. That is what [D722](D722-DIAG-RESULT-no-variable-explains-2022.md)
  found for other books: 2022 is not a measurable regime with the pre-trade variables tried so far.
- **What it says about L4 itself:** the base book is unchanged (+\$12.08 net, t 2.47 gross, net t 1.88). It fails G2
  on its own, and two filters have now failed to rescue it.
- **Recommendation, as the pre-registration set it:**
  - close the rates-filtered construction;
  - keep base L4 as an open lead, not frozen.
  - **Forward recording needs RTY added to the forward recorder, which does not carry it today.**
  - All three are the principal's call.
