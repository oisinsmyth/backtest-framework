# D678 RESULT (DEVELOPMENT) — no projection, overlay or lag rescues the month-end mechanism: none reaches NW t 2, the best (O2) sits at the 75th percentile of the best-of-13 null, and the fade is not liquidity, because the square-root law predicted MORE impact after 2018, not less

*2026-09-29. One run of `scripts/stage0_d678_month_end_variants.py` (`3c670661`) under
[D678's pre-registration](D678-PRE-REG-thirteen-projections-overlays-and-lags-for-d677.md) (`79051a41`), 8 s. L1's
input is `data/d678_es_1545.csv.gz` (sha256 1bff347d…, `scripts/build_d678_es_1545.py`). Output
`data/d678_month_end_variants.json`. **Development:** D677 had already read this window. Nothing on or after
2024-01-01 was read.*

## The answer in one line

**No variant earns a development pass. NW t runs from 0.34 to 1.42 against the bar of 2.0.**
- **Four beat their own null's p95:** P1, P6, O2 and O3.
- **Nothing beats the best-of-13 family null:** the best, O2 (the macro-day stand-aside), has a net Sharpe of +0.331
  at the 75.5th percentile.
- **Nothing is confirmable:** the expected t on 2024-01 → 2025-02 is at most 0.42, and 0.64 with the vault.
- **The fade is not a liquidity story.** P1's impact factor σ·√(S/DV) doubled from 2013–15 to 2020–23, while the
  realised edge per unit |z| turned negative (Spearman −0.25). The flow's price effect vanished even though the
  square-root law says it should have grown.

## 1. The mechanics held

- **D677 reproduced bit for bit:** base gross +7.1732 bp per active day, B1 −14.0594.
- **The prior-only audit passed** on the real data. In the self-test it fired on a pass-through that includes its own
  month.
- **The other audits** (book cost identity, sign in money, window guard, L1 causality) all fired on broken inputs in
  the self-test.
- **The nulls:** 159 enumerated month offsets, with every prior-only estimate refit inside each rotation. L1 used 93
  offsets over its 96 months.
- **Coverage:**
  - ES day-session volume existed on 31, 68 and 109 days in 2010–2012 and 205–253 a year after. DV60 could be formed
    on 800 of 810 active days.
  - GEX existed on 760.
  - L1's 15:45 signal existed on 480 of 480; 10 of them came from an early close's last bar.
  - 20 window days were macro-release days.

## 2. The thirteen variants (MES; daily net Sharpe on every trading day; own null of 159 offsets)

**The base** (D677, unfiltered): Sharpe +0.261, t +1.09. On L1's 2016–2023 window it is +0.130.

| v | Sharpe | null p50 | null p95 | pct | NW t | traded | net $ | own p95? | expected t 2024-25 / + vault | full-ES Sharpe |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---:|
| P0 \|z\| | +0.276 | −0.138 | +0.337 | 0.914 | +1.20 | 432 | 3,737 | no | 0.35 / 0.54 | +0.237 |
| **P1** √-law | +0.247 | −0.201 | +0.194 | **0.965** | +1.07 | 467 | 3,523 | yes | 0.31 / 0.48 | +0.182 |
| P2 quarter-end | +0.261 | −0.100 | +0.316 | 0.924 | +1.13 | 417 | 3,507 | no | 0.33 / 0.51 | +0.289 |
| P3 threshold | +0.195 | −0.103 | +0.337 | 0.852 | +0.78 | 138 | 1,888 | no | 0.23 / 0.35 | +0.205 |
| P4 gamma | +0.115 | −0.088 | +0.387 | 0.736 | +0.50 | 328 | 1,493 | no | 0.15 / 0.22 | +0.257 |
| P5 window day | +0.124 | −0.135 | +0.325 | 0.799 | +0.57 | 325 | 1,461 | no | 0.17 / 0.25 | +0.119 |
| **P6** structural | +0.327 | −0.188 | +0.155 | **0.988** | +1.41 | 252 | 3,600 | yes | 0.41 / 0.63 | +0.216 |
| P7 blend | +0.080 | −0.140 | +0.369 | 0.769 | +0.34 | 355 | 1,045 | no | 0.10 / 0.15 | +0.263 |
| O1 vol size | +0.164 | −0.143 | +0.246 | 0.918 | +0.63 | 810 | 2,513 | no | 0.19 / 0.28 | +0.200 |
| **O2** macro stand-aside | **+0.331** | −0.185 | +0.201 | **0.987** | **+1.42** | 790 | 5,033 | yes | 0.42 / 0.64 | +0.366 |
| **O3** hold 10 days | +0.251 | −0.216 | +0.127 | **0.969** | +1.00 | 2,420 | 7,023 | yes | 0.29 / 0.45 | +0.268 |
| L1 15:45 signal | +0.163 | −0.161 | +0.397 | 0.855 | +0.52 | 480 | 1,868 | no | 0.20 / 0.30 | +0.189 |
| L2 10-day window | +0.211 | −0.113 | +0.280 | 0.925 | +0.79 | 1,620 | 4,536 | no | 0.23 / 0.36 | +0.241 |

**The family null** (the best of 13 at each offset): p50 +0.198, p95 **+0.503**. The best observed variant, O2, has
+0.331, at the 75.5th percentile.

**Reading the table:**
- **No projection concentrates the edge.** The best projections (P6 +0.327 and P0 +0.276) are within noise of the
  base's +0.261, and every NW t is under 1.5.
- **The overlays:**
  - O2's lift (+0.261 → +0.331) comes from standing aside on 20 macro days. That is a small, post-hoc-looking
    improvement on a thin base.
  - O3's hold adds 1,610 days of exposure and lowers the Sharpe (+0.251). So D677's continuation (t −1.97) does not
    pay as a hold.
  - O1's volatility sizing is the worst of the three (+0.164). That is consistent with the edge sitting partly on
    high-volatility days, which O1 scales down; it was not measured directly.
- **The lags:** L1 (+0.163) beats the base on its own window (+0.130), and both are weak in 2016–2023. L2's longer
  window (+0.211) dilutes rather than front-runs.

## 3. The fade (the question P1 was built to answer)

| | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F = σ20·√(S/DV60), ×10⁻⁴ | 4.60 | 2.51 | 2.50 | 2.77 | 3.81 | 2.98 | 1.89 | 4.49 | 3.91 | 7.57 | 4.96 | 7.67 | 4.49 |
| realised edge, bp per unit \|z\| | +21.7 | +17.3 | +10.6 | +19.7 | +9.7 | +13.9 | +3.4 | +24.4 | −4.5 | −1.5 | −14.1 | −8.8 | +20.5 |

- **The square-root law's impact factor rose from 3.03 (2013–15) to 6.17 (2020–23).** Volatility rose, and ES day
  volume did not keep pace with the index level. For the same drift, the law predicts twice the impact.
- **The realised edge went negative in 2019–2022 anyway.** The Spearman ρ across years is **−0.25**, so "P1 explains
  the fade" is **false**.
- **So the fade is not liquidity absorbing the flow.** The price response to a predicted flow disappeared while the
  flow's predicted impact grew. That is the signature of the flow being **anticipated or offset**: front-run earlier
  than the last five days, netted by other calendar flows, or executed away from ES. It is not the signature of it
  being diluted. That explanation is not tested here. It is the only reading this record does not contradict.

## 4. The four groups, for the best variant (O2)

| | |
|---|---|
| daily net Sharpe | +0.331 |
| daily net Sortino | +0.495 |
| max drawdown | $3,395 |
| profitable years | 10 of 14 |
| correlation with the MACD arm | **−0.032** |

**Per traded day, in net $:**

| mean | median | win rate | mean ex-top 1% | mean ex-bottom 1% | trimmed mean, 1% both tails |
|---:|---:|---:|---:|---:|---:|
| +6.43 | +1.54 | 51.6% | **+0.24** | +12.39 | +6.20 |

The top 1% of days again carries almost all of the mean; the symmetric trim keeps it.

**Per-year net ($):**

| 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| −7 | +958 | +323 | +200 | +451 | +654 | +806 | +11 | +2,117 | −274 | +497 | −1,650 | −310 | +1,256 |

## 5. Predictions

| # | prediction | outcome |
|---|---|---|
| 1 | no variant clears the best-of-13 null | **HELD** (the best is at the 75.5th percentile) |
| 2 | F falls, and its Spearman with the edge is below 0.5 | **BROKEN**: F **rose** (3.0 → 6.2); ρ −0.25 |
| 3 | O1 is the best overlay | **BROKEN**: O2 +0.331 > O3 +0.251 > O1 +0.164 |
| 4 | O3 raises the Sharpe in-sample | **BROKEN**: +0.251 against the base's +0.261 |
| 5 | L1 beats the base on its window | **HELD** (+0.163 against +0.130) |
| 6 | P6 ≥ P7 | **HELD** (+0.327 against +0.080) |
| 7 | every development pass is unconfirmable alone | **HELD** (vacuously: none passes; all are under 0.42) |

## 6. What this decides

**The month-end rebalancing line has no tradeable form here.**
- D677 established the mechanism, in-sample, at about 80% of its published size.
- D678 tried 13 ways to concentrate it, time it or size it, declared in advance and scored as one family. None reaches
  t 2.
- The best is inside the family's null. None could be confirmed on the unread slice even if it were real (expected
  t ≤ 0.64 with the vault).

**Its fade has a mechanism-level reading.** The square-root law says the month-end flow should have hit harder after
2018, and instead the price stopped responding. That points to the flow being anticipated or offset, not diluted.
**This is the useful fact for any successor:** a front-running study would move the window earlier. It should not
filter the last five days.

**Proposals, each the principal's (R15):**
1. **Close the month-end rebalancing line as a strategy** (D677 and D678), with no unread slice spent. Keep the fact:
   the equity month-end flow was real through 2018 at about −14 bp per 1-SD, and faded while its predicted impact
   rose.
2. **Enter it in `COMPONENTS_PROP.md` as SCORED, NOT ENTERED.**
   - D677's unfiltered MES: net Sharpe 0.26, ρ −0.04 with the arm.
   - D678's best, O2: 0.33, ρ −0.03, inside its family null.
3. **If the anticipation reading is to be tested, it is a new line with a new window.** The drift signal would be
   scored over trading days 10–6 before month-end, and on the early days of the month (the flow from those who
   rebalance late). It would need its own pre-registration and power, and **by D678's evidence its prior is low**.
