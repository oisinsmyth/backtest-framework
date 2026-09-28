# D652 STAGE 0 RESULT — NOT SUPPORTED: the crack's deviation from its seasonal norm predicts nothing at 2–13 weeks, because the deviation is an era label, not a state; and the design's year count (B3) was a check that could not fail

*Design: [D652](D652-STAGE-0-DESIGN-does-the-crack-spread-revert-to-its-norm.md) (`a4ddf4f`), committed
alone before the runner existed (R8). Runner `scripts/stage0_d652_crack.py` (one run of `--run`, seconds); numbers
[`data/stage0_d652_crack.json`](../../data/stage0_d652_crack.json). **The last settlement read is 2023-12-29**; the
2024+ slice is unread for this line and stays so. No construction was built, so there is no book and no component
line: this record tests a premise.*

## The answer in one line

**There is no reversion to find.** On 407 weekly observations (2016-02-19 → 2023-12-29), a crack $1 above its
norm is followed by **−0.7 cents** of change over four weeks (β −0.0068, Newey–West t −0.10). That sits at the
**66th percentile** of 354 enumerated rotations (p05 −0.050, p50 −0.019, p95 +0.061; SE 0 because enumerated). The
same holds at 2, 8 and 13 weeks (β −0.005 to +0.017, every t within ±0.15). Five of the six bars fail, and the one
that passes (B3) is shown below to pass for a random walk. **Route: B1 and B2 fail, so the premise is not supported
and the recommendation is to close the crack line.** The principal decides (R15).

## 1. The bars

| bar | declared | outcome |
|---|---|---|
| B1 | β < 0, NW t ≤ −2 | **FAIL**: β −0.0068, t −0.10 |
| B2 | below the rotation p05 | **FAIL**: −0.0068 against −0.050, rank 0.661 |
| B3 | negative in ≥ 6 of 8 years | passes, 8 of 8, **and a random walk passes it 99.4 % of the time** (§3) |
| B4 | both extreme terciles in ≥ 6 of 8 years | **FAIL**: 1 of 8 (2017 alone) |
| B5 | \|β\| × median \|D\| ≥ 3 × $0.060 | **FAIL**: $0.029 a barrel of predicted move at the median \|D\| of $4.34 |
| B6 | negative in every leave-one-year-out fit | **FAIL**: without 2023, β is +0.023 |

## 2. The object, year by year

| year | crack C ($/bbl) | norm S | deviation D | sd of D | mean 4-week change Y | weeks |
|---|---:|---:|---:|---:|---:|---:|
| 2016 | 14.63 | 19.85 | −5.22 | 3.69 | +0.43 | 46 |
| 2017 | 17.75 | 17.71 | +0.05 | 4.16 | +0.38 | 52 |
| 2018 | 18.35 | 17.29 | +1.07 | 1.75 | −0.57 | 52 |
| 2019 | 17.85 | 16.96 | +0.89 | 2.18 | +0.46 | 52 |
| 2020 | 10.94 | 17.94 | −6.99 | 3.43 | +0.09 | 53 |
| 2021 | 19.06 | 15.69 | +3.37 | 2.89 | +0.82 | 52 |
| 2022 | **34.55** | 15.86 | **+18.69** | 7.78 | **+3.17** | 52 |
| 2023 | 30.05 | 21.55 | +8.50 | 6.06 | +0.49 | 48 |

The deviation is a **regime label**. The three-year same-month norm lags every level shift: the 2016 glut and the
2020 collapse read as whole years below the norm, and 2022–2023 as whole years above it. **In 2022, the year with
the largest deviations, the crack kept rising** (+$3.17 a barrel every four weeks on average). The five largest
|D| weeks are all May–June 2022 (July–September deliveries, D +31.9 to +37.0). Four of the five fell $4.7–$16.9
over the next four weeks, so the peak itself reverted, but the year around it did not, and one pooled β carries
both. The terciles make the same point: 2016 and 2020 have no week in the top tercile, 2022 and 2023 none in the
bottom. That is [D526](D526-the-curve-story-fails-stage-0-the-level-is-a-regime-and-the.md)'s failure again:
persistence passes so hard that the test compares eras, not states. D's weekly AR(1) is 0.974, a half-life of
25.8 weeks.

## 3. The check that could not fail, stated plainly

B3 counted years with a negative within-year slope. **A within-year regression of a level's forward change on the
level itself is biased towards reversion on a short sample (Kendall's bias).** Post hoc and disclosed, on a random
walk with the crack's own weekly volatility and the same per-year sample sizes (2,000 draws): **mean 7.62 of 8 years
negative, P(≥ 6) = 0.994, P(8 of 8) = 0.686, median per-year β −0.31.** The observed per-year slopes (median −0.38;
−0.03 in 2016 to −0.74 in 2018) are what a random walk gives. Within a year, the crack behaves like a random walk
at these horizons. The flaw was the design's, and B1/B2 did not depend on it. The lesson is general: a year-count
of slopes needs its own null, the same as the pooled β has the rotation.

## 4. The predictions

| | prediction | outcome |
|---|---|---|
| 1 | half-life 4–26 weeks | held, barely (25.8), but it is the regime's persistence, not a reversion speed |
| 2 | β −0.05 to −0.30, t −1.5 to −3.5 | **FAILED**: β −0.007, t −0.10 |
| 3 | B4 passes | **FAILED**: 1 of 8 |
| 4 | 2022 the most influential year | held (leave it out and β is −0.114) |
| 5 | products carry over half of β | a ratio of two near-zeros (6.0); **not interpretable** |
| 6 | always-on drift small beside the signal | **FAILED**: the signal is nothing; the drift is +$0.66 per four weeks (t 2.0) |
| 7 | B5 by an order of magnitude | **FAILED** |
| 8 | forward power on 2024-01 → 2025-02 below 0.5 | held: 0.02, and 0.03 with the vault; had the premise passed, no forward read could have decided it |

## 5. The diagnostic objects

- **The gasoline crack** (`42 × RB − CL`, 546 weeks from 2013-06): β −0.056, t −0.80, rank **0.067** at four
  weeks (p05 −0.060). It is the nearest thing to a reversion in this record, and it does not reach its own p05. Its
  11-of-11 year count is §3's bias.
- **The distillate crack** (ULSD deliveries): β −0.008, t −0.17, rank 0.47.

Neither could pass anything, and neither is taken forward.

## 6. What is parked, and what is not proposed

**Parked, not claimed:** the always-on 3:2:1 crack, one fixed delivery month held four weeks, rose **+$0.66 a
barrel per four weeks at t 2.0** over 2016–2023. That is the crack curve's roll-down (the nearby crack sits above the
deferred, and a fixed contract climbs as it nears delivery), which is carry in a new object and seen in sample. It
is a fact a future deposit may build on, and it would need a window that has not read it.

**Not proposed:** a faster norm (deviation from the last few months rather than three years). It would be a second
trial on a seen sample, and §3 says the within-year crack is random-walk-like at these horizons, which leaves it
little to find.

**What stays:** the runner's contract resolver (recycled one-digit codes against the definition expiries), its
same-delivery-month crack builder with the ULSD cut, and the real-time norm with its assertion.
