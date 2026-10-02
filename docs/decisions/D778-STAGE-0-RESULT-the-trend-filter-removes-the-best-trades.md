# D778 STAGE 0 RESULT — NO EFFECT, and the filter adds nothing: skipping the closing-auction fall-side buys in a downtrend removes the BEST trades, not the losing ones. Downtrends were where buying the close's forced selling paid most, and 2022 was the exception, not the rule

*2026-10-03. One completed run of `scripts/stage0_d778_auction_fade_trend_filter.py --run` (20 seconds).*
- **The order:** the [pre-registration](D778-STAGE-0-PRE-REG-the-closing-auction-fade-with-a-trend-filter.md)
  (`f10f5121`) came before the runner (`94d9feb0`), and the runner before its run.
- **The first launch stopped on its own lag audit (RTY, 2019-08-09) before anything was printed or written.**
  - The pre-registration had not said what the trend index does across a session with no 16:00 price. The vectorised
    index dropped the return across the gap; the explicit-loop index carried the last priced close forward.
  - The fix (`ff0a50be`) makes the vectorised index follow the loop. The audit now compares the index itself. The
    self-test drops 16:00 bars on 17 sessions and checks both agree, and that case was shown to fire on the old
    convention.
  - Construction, gates and nulls are otherwise unchanged, and the fix was committed before the completed run.
- **Output:** `data/stage0_d778_auction_fade_trend_filter.json` (statistics only).

## 0. Checks

- **The lag audit:** an explicit-loop second implementation re-derived c, the trend index, the keep decision and the
  fade on 40 sampled base trades per root; all equal.
- **Right quantity:**
  - base = kept + removed on every root;
  - offset 0 equals the observed for N and for F;
  - nothing on or after 2024-01-01.
- **The self-test:**
  - a planted downtrend continuation is removed and passes F;
  - a filter tracking nothing fails F;
  - the trend state uses no later price;
  - the second implementation raises on a broken decision;
  - chunk = whole;
  - the whole study runs end to end;
  - the sign audit raises on a mirrored book.
- **The DOWN state covers 45% of M2K's valid sessions.**

## 1. The gates (M2K primary)

| | value | gate |
|---|---|---|
| the base L4 book on the same sessions (for comparison) | 280 trades, +\$15.84 gross / +\$12.08 net (t 2.47); net Sharpe 0.81, Sortino 1.25 | — |
| **G1:** the F1 book | **208 trades, +\$9.84 gross / +\$6.08 net, t 1.38** | **fail** |
| N: exact rotation of the F1 signal | p50 −\$1.64, p95 +\$8.78, rank 0.965 | pass |
| **F(a):** the removed trades' mean gross | **+\$33.19 (72 trades): they were winners** | **fail** |
| **F(b):** the improvement against the rotated DOWN flag | **Δ −\$6.00**, against p50 −\$3.44 and p95 +\$2.09; rank 0.20 | **fail** |
| Y | win ≥ 50% in 3 of 5 full years (need 4); volatility-adjusted 2016–19 −0.08σ | fail |
| G2 | net t 0.86; net −\$263 without 2020 and 2021 | fail |

**Reading: NO EFFECT** (G1 fails first). The filter also fails F on both counts. **GO false.**

**The predictions:**
- "F(a) passes": WRONG.
- "F(b) is the gate at risk": it failed, and worse than a random rotation of the same flag.
- "G1, N and G2 pass": G1 and G2 failed, because the filter took the edge out.

## 2. What the filter removed (M2K, the fall-side buys on DOWN sessions)

| year | 2018 | 2019 | 2020 | 2021 | **2022** | 2023 |
|---|---|---|---|---|---|---|
| removed trades | 11 | 11 | 17 | 9 | **17** | 7 |
| their mean gross | +\$26.68 | +\$42.09 | **+\$94.24** | +\$40.72 | **−\$32.79** | +\$31.71 |

- **Buying a closing-auction fall while the index is below its 200-session average was the most profitable trade in
  the book in five of six years.** Late 2018, 2020, 2021 and 2023's dips were bought into downtrends and reverted
  overnight. Only 2022 lost.
- **The same on the other roots:**

| root | removed | their mean gross | 2022's removed trades |
|---|---|---|---|
| MNQ | 46 | +\$38.52 | −\$35.59 |
| MES | 50 | +\$17.25 | −\$81.02 |
| MYM | 63 | +\$1.30 | −\$69.40 |

- **F2, rising volatility (reported):** removes 61 M2K trades with a mean of +\$36.65, and leaves +\$10.05 (t 1.38).
  The same failure.

## 3. All four groups (M2K, the F1 book)

| | |
|---|---|
| mean gross / net; median net | +\$9.84 / +\$6.08; −\$0.76 |
| net Sharpe / Sortino; gross Sharpe | 0.37 / 0.57; 0.59 (base: 0.81 / 1.25) |
| maximum drawdown; total net | \$1,086; +\$1,265 (base \$1,167; +\$3,384) |
| win; payoff; skew; kurtosis | 51.0%; 1.20; +0.36; 2.80 |
| net ex-top 1% / ex-bottom 1% / trimmed | +\$2.31 / +\$9.10 / +\$5.32 |
| sides kept: fall (long, UP states) / rise (short) | +\$17.06 net (65) / +\$1.09 net (143) |
| \|c\| terciles, net | −\$15.86 / +\$15.49 / +\$18.93 |
| by year, net (kept) | 2018 −\$4.76, 2019 −\$9.54, 2020 +\$9.34, 2021 +\$22.27, 2022 +\$1.74, 2023 +\$5.69 |
| drift-adjusted (drift +\$3.82 a night) | fall side kept +\$17.00; rise side +\$8.67 |
| five largest / worst | 2020-03-13 +\$495, 2022-01-24 +\$293, 2023-03-14 +\$248 / 2020-04-06 −\$335, 2023-12-13 −\$274, 2020-04-03 −\$247 |

- **The component line:** daily ρ with D775 +0.011, D777's MNQ book −0.080, D737's twin −0.045, NQ F2 −0.071, C1
  +0.032.
- **The other roots' F1 books:**

| root | trades | mean gross (t) | rank | reading |
|---|---|---|---|---|
| MNQ | 385 | +\$14.43 (1.45) | 0.950 | NO EFFECT |
| MES | 354 | +\$10.20 (1.38) | 0.959 | NO EFFECT |
| MYM | 316 | +\$6.32 (0.92) | 0.912 | NO EFFECT |

## 4. The reading

- **Declared:** NO EFFECT on every root, and the filter fails its own null. GO false.
- **The mechanical story behind the filter is refuted in-sample.**
  - D778's premise was that "closing selling in a trend persists, so buying it loses". In every downtrend of the sample
    except 2022, buying the closing-auction drop paid the most.
  - **2022's losses are not a property of being in a downtrend.** That year was different in some other way, and this
    test does not identify it. Candidates for a later look:
    - a rate-driven repricing rather than a liquidity event;
    - the negative overnight drift (M2K −\$4.1 a night);
    - the closing move's information content.
- **What it says about L4 itself:** the base book, unfiltered, keeps its in-sample numbers (+\$12.08 net, t 2.47 on
  these 280 sessions). Its edge sits in exactly the trades a trend rule would remove.
  - A filter that keeps 2022 out without removing 2018–2021's dips would have to know 2022's difference in advance.
    None was found.
- **Recommendation:**
  - close the trend-filtered construction;
  - leave L4's base construction as an open lead, with 2022 as its known failure mode. It would only become a
    pre-registration with a reason for 2022 that can be stated in advance.
  - Both are the principal's call.
