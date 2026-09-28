# D656 STAGE 0 RESULT — the soybean crush carries no processors' premium, and its near-versus-next-year gap genuinely reverts but cannot be traded: the year-ahead legs trade half a percent of the near legs' volume and the move is a third of the cost bar

*Design: [D656](D656-STAGE-0-DESIGN-the-soybean-crush-premium-and-reversion.md) (`5a2b6ed`), committed alone before the
runner existed (R8). Runner `scripts/stage0_d656_crush.py` (one run of `--run`); numbers
[`data/stage0_d656_crush.json`](../../data/stage0_d656_crush.json) and the disclosed post-hoc null
[`data/stage0_d656_s2_randomwalk_null.json`](../../data/stage0_d656_s2_randomwalk_null.json). **The last settlement read
is 2023-12-29**; the crush's 2024+ slice is unread for this line. No construction was built: this record tests
premises.*

## The answer in one line

**S1 fails every bar: there is no processors' premium.** **S2 passes B1 and B2 and fails the rest.** The gap between
this year's margin and next year's reverts with a half-life of about eight weeks, which beats even a random-walk null
built to carry the Dickey–Fuller bias (§3). But the year-ahead contracts barely trade, the move is 2.0 cents a bushel
against a 6-cent bar, and the gap is an era label within years. **Route: S1 → close; S2 → reported, no construction.
Recommended: close the crush line** (principal, R15).

## 1. S1 — the processors' premium (674 weekly observations, 2011-01-07 → 2023-12-29)

| | outcome | bar |
|---|---|---|
| mean four-week change of the near crush Y1 | **+0.51 ¢/bu**, t **0.36** | B1 FAIL |
| its roll-down part R (Y1 less the constant-tenor change) | **+0.32 ¢/bu**, t **0.35** | B2 FAIL |
| years with positive mean Y1 | 8 of 13, against the zero-drift null's p95 of 10 (p50 7) | B3 FAIL |
| leave-one-year-out | negative without 2022 (−0.13 ¢) | B4 FAIL |
| mean change over a whole holding cycle (92 cycles) | +2.17 ¢/bu, t 0.81, against 3 × 1.00 ¢ | B5 FAIL |

The legs cancel: meal +4.99 ¢, oil −0.15 ¢, beans −4.33 ¢ a bushel per four weeks. 2016–2023 alone reads +1.13 ¢
(t 0.52). The year table runs from −9.2 ¢ (2023) to +8.2 ¢ (2022). **Whatever crushers pay to hedge forward, a fixed
crush contract held towards delivery does not collect it.**

## 2. S2 — the gap to next year

| | outcome | bar |
|---|---|---|
| β of the gap's four-week change on the gap | **−0.157** (Newey–West t **−2.09**; Spearman −0.11); 2016–2023 alone −0.201 | B1 pass |
| rotation null, 621 enumerated offsets | p05 −0.065, p50 +0.001, p95 +0.060: **rank 0.00** | B2 pass |
| years with a negative within-year β | 12 of 13, against a random-walk null whose **p50 and p95 are both 13** | B3 FAIL (§3) |
| years holding both extreme terciles | **2 of 13** (2014, 2021) | B4 FAIL |
| `|β| × median |G|` | **1.96 ¢/bu** (median gap 12.5 ¢) against 3 × 2.00 ¢ | B5 FAIL |
| year-ahead legs' cleared volume, share of the near legs', 2016–2023 | ZS **0.62 %**, ZM **0.51 %**, ZL **0.45 %**, against 5 % | B6 FAIL |

## 3. Two statements about the nulls

**B2's rotation was not the right null for B1's statistic, and a post-hoc check says the result survives the right
one.** Regressing a persistent series' change on its own level is biased towards reversion: Dickey–Fuller's bias,
the pooled form of the Kendall bias D653 met per year. A rotation shifts G against Y2 and destroys the mechanical
link between a level and its own change, so it cannot reproduce that bias. Post hoc and disclosed: with G simulated
as a pure random walk at its own weekly volatility and length (4,000 draws, seed 657), the null β has **p50 −0.026,
p05 −0.084, p01 −0.118**. The observed **−0.157 ranks 0.0018.** G's weekly AR(1) is 0.914, a half-life of 7.7
weeks. **The reversion is real.** For any future level-on-own-change test, the random-walk null is the declared
null and the rotation is a diagnostic.

**B3 could not pass.** With a half-life of weeks inside 52-week years, Kendall's bias pushes the random-walk null's
median to 13 negative years of 13. The bar asked for 13, and the design did not state the null's pass rate, which
the D653 memory rule says it should. A year count is uninformative for a series this persistent, and the per-year
robustness belongs in a pooled β against the random-walk null, block by block.

## 4. Why a real reversion is not a trade

- **The legs do not trade.** A year-ahead soybean, meal or oil contract clears about half a percent of its near
  month's volume. The crossing D651 measured is for the front, so the real cost on those legs is far above the
  $0.0200 a bushel this bar assumed.
- **The move is small.** A median gap of 12.5 ¢ a bushel reverting at 16 % a month is 2 ¢ of expected move per four
  weeks, a third of the cost bar even at front-month spreads.
- **It is an era within years.** In most years the gap sits entirely on one side of its terciles (2018 wholly high,
  2011–13 almost wholly low), so the "state" a trade would condition on changes a few times a decade.

A version of the same reversion with a liquid far leg, the next pair rather than next year's, would be a different
object with the seasonal calendar inside it. D576 closed the seasonal calendar spreads on this strip. It is not
proposed.

## 5. The predictions

| | prediction | outcome |
|---|---|---|
| 1 | S1-B1 holds, S1-B2 borderline | **FAILED**: t 0.36 and 0.35 |
| 2 | 2021 or 2022 the most influential year, S1-B4 holds | **FAILED**: 2023 is the most influential; B4 fails |
| 3 | S2's β negative, rotation rank ≤ 0.10 | held: −0.157, rank 0.00 (and 0.0018 against the random walk) |
| 4 | S2-B4 passes | **FAILED**: 2 of 13; the gap is also an era label |
| 5 | S2-B6 fails for soybean oil | held, and for beans and meal too |
| 6 | at most one premise routes | held: none routes |

## 6. What stays

The runner's crush builder (the 10 : 11 : 9 unit, the X/Z pairing, the first-notice guard) and the fact, parked
and not claimed: **the soybean crush's gap to next year's margin reverts with a half-life of about eight weeks, and
beats a random-walk null at rank 0.002.** A future deposit with a liquid expression of it would start there.

## 7. CLOSED by the principal, 2026-09-28

"Close it and merge into main." **The crush line is closed under R15**: S1 (the processors' premium) and S2 (the
reversion towards next year's margin), with no construction built on either. The 2024+ slice was never read for
this line. The parked fact in §6 stays a fact, not a lead.
