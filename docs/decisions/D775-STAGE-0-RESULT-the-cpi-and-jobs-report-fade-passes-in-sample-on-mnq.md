# D775 STAGE 0 RESULT — SUPPORTED on MNQ (GO true), with the principal's test passed on its win-rate branch at the boundary: fading the 08:30 CPI and jobs-report impulse nets +\$30.81 a trade in-sample, but its volatility-adjusted edge is a third as large in 2016–19 as in 2020–23

*2026-10-02. One completed run of `scripts/stage0_d775_cpi_nfp_fade.py --run` (31 seconds).*
- **The order:** the [pre-registration](D775-STAGE-0-PRE-REG-fade-the-cpi-and-jobs-report-impulse-on-mnq.md)
  (`b60574bd`) came before the runner (`fadf6d63`), and the runner before its run.
- **The first launch crashed in the reporting path before anything was printed or written.** The release-day subset
  had been taken before a column it reports by was added. The fix (`2158a8ea`) re-takes the subset and makes the
  self-test run the whole study on a synthetic panel. It was committed before the completed run; the construction,
  gates and nulls were unchanged.
- **Output:** `data/stage0_d775_cpi_nfp_fade.json` (statistics only).
- **What this can claim:** the in-sample was read before this record (D772), so a pass fixes a construction that
  survives its declared null and the principal's test. **It is not confirmation.** That needs unread data (§6).

## 0. Checks

- **Release days:**
  - **NQ:** 192 read, 186 used. 4 have no session in the fixture, 2 have a zero impulse; none has two contracts or a
    missing bar. Read = used + exclusions, asserted.
  - **ES:** 185 used. **YM:** 187. **RTY:** 146 (its fixture lacks 40 of the sessions).
- **The lag audit:** an explicit-loop second implementation over the raw bar rows re-derived the fade on 40 sampled
  release days per root; all equal.
- **Sign audit in money:** it raised on a mirrored book.
- **Right quantity:**
  - rotation offset 0 equals the observed;
  - the placebo differs from the treatment;
  - nothing on or after 2024-01-01.
- **The self-test:**
  - synthetic fades on both signs;
  - the two-contract exclusion;
  - the second implementation raises on a broken side;
  - chunk = whole for the rotation on a tie-heavy input;
  - the whole study runs end to end on a synthetic panel.

## 1. The gates (MNQ, one contract, \$4.07)

| gate | value | result |
|---|---|---|
| **G1** mean gross > 0, t ≥ 2 | **+\$34.88, t 2.73** (n 186) | pass |
| **N** above the exact rotation p95 (2,009 offsets, SE 0) | p50 +\$0.27, **p95 +\$17.26**, rank **0.9995** | pass |
| **Y** (i) win rate ≥ 50% in ≥ 6 of 8 years | **6 of 8**: 2016 50.0%, 2017 47.8%, 2018 54.2%, 2019 37.5%, 2020 60.9%, 2021 56.5%, 2022 66.7%, 2023 73.9% | **pass, at the boundary** (2016 is 11 of 22) |
| **Y** (ii) volatility-adjusted mean > 0 in ≥ 6 of 8 years, and 2016–19 ≥ half 2020–23 | 7 of 8 positive, but **2016–19 +0.090σ against 2020–23 +0.325σ** | fail (Y needs only one branch) |
| **G2** net t ≥ 2; net > 0 without the best two years; gross without 2022 ≥ \$8.14 | net +\$30.81, **t 2.41**; without 2020 and 2023 +\$2,040; without 2022 +\$34.73 | pass |

**Reading: SUPPORTED. GO true.**

- **The predictions:** G1 pass, as known. N pass, but its p95 (+\$17.26) came in above the predicted +\$12 to +\$15.
  Y was the gate at risk: it passed on the win-rate branch at its boundary, and the volatility-adjusted branch failed
  as feared.

## 2. The other nulls (reported)

| null | p50 | p95 (SE) | rank |
|---|---|---|---|
| year-and-weekday-matched non-release days (10,000) | −\$0.01 | +\$15.46 (0.21) | 0.9999 |
| year-and-\|impulse\|-decile-matched non-release days (10,000) | **−\$13.96** | −\$0.47 (0.16) | 1.0000 |
| non-release days, all (1,824) | mean −\$3.32 (t −0.97) | | |

- **The matched-impulse null is the mechanism's own contrast.** Equally large 08:30 moves on non-release days
  continue (p50 −\$13.96 for the fade). Release-day impulses reverse.

## 3. All four groups (MNQ)

**Performance:**

| | |
|---|---|
| mean gross / net | **+\$34.88 / +\$30.81** |
| net Sharpe / Sortino (daily, zero on the 90.7% of days without a release); gross Sharpe | **0.84 / 1.50**; 0.95 |
| maximum drawdown; total net (2016–2023) | \$1,036; +\$5,730 |
| mean \|gross\| against the cost; breakeven cost | \$115.83 against \$4.07; \$34.88 |

**Trade distribution:**

| | |
|---|---|
| count; median gross / net | 186; **+\$12.75 / +\$8.68** |
| win rate; payoff (net) | 55.9%; 1.42 |
| skew; kurtosis (net) | +0.48; 3.12 |
| net ex-top 1% / ex-bottom 1% / trimmed | +\$23.50 / +\$37.12 / +\$29.80 |
| five largest | 2021-12-03 +\$730.93, 2020-09-04 +\$675.43, 2022-07-13 +\$493.43, 2022-06-03 +\$482.93, 2023-04-12 +\$428.43 |
| five worst | **all 2022:** 09-13 −\$587.57, 11-10 −\$511.57, 06-10 −\$403.07, 10-07 −\$365.57, 01-07 −\$349.07 |

**What the winners depend on:**

| split | n | mean gross | win | volatility-adjusted | t |
|---|---|---|---|---|---|
| 2016–19 | 93 | +\$8.20 | 47.3% | +0.090σ | 0.89 |
| 2020–23 | 93 | +\$61.56 | 64.5% | +0.325σ | 2.61 |
| CPI | 93 | +\$33.55 | 61.3% | +0.239σ | 1.94 |
| jobs report | 93 | +\$36.21 | 50.5% | +0.182σ | 1.91 |
| **impulse down (fade long)** | 82 | **+\$50.52** | 64.6% | +0.422σ | 2.51 |
| impulse up (fade short) | 104 | +\$22.55 | 49.0% | +0.045σ | 1.37 |
| \|impulse\| low / mid / **high** tercile | 62 each | +\$14.15 / +\$14.94 / **+\$75.55** | 57% / 47% / 65% | 0.11 / 0.14 / 0.38σ | 1.09 / 0.83 / 2.44 |
| NQ price low / mid / high tercile | 62 each | +\$14.33 / +\$11.71 / +\$78.60 | | 0.15 / 0.07 / 0.41σ | |

- **By year (mean gross):** 2016 −\$1.57, 2017 +\$0.35, 2018 +\$21.79, 2019 +\$11.08, 2020 +\$45.41, 2021 +\$42.91,
  2022 +\$35.85, **2023 +\$123.17 (t 3.03)**.
- **Volatility-adjusted by year:** −0.165, +0.046, +0.280, +0.134, +0.276, +0.266, +0.091, +0.678σ.
- **Where it lives:** in the fade of DOWN impulses, of LARGE impulses, and in 2020–23. In volatility units the
  2016–19 half is a third of the 2020–23 half; in dollars it is a seventh, because price and volatility also grew.

**The split around the cash open (signed by the impulse):**
- 08:35 → 09:30: +\$5.33 (t 0.83); placebo −\$1.01.
- **09:30 → 11:01: +\$29.55 (t 2.47)**; placebo −\$2.31.
- **The declared secondary (entry at the 09:30 print):** +\$29.55 gross / +\$25.48 net, t 2.47, median +\$6.00.
- **The give-back is a cash-open event, as the mechanism says.**

**The plateau grid (mean gross, t):**
- **K ≥ 3** with exits 10:30–12:00: +\$20.39 to +\$36.89 (t 1.40–2.75). K = 5 / 11:00 sits inside it, not at a
  peak (K = 5 / 12:00 is +\$36.89).
- **K = 1:** +\$11.90 to +\$17.88 (t 0.81–1.37). It is weaker, as D772 found, but not negative to these exits.

## 4. The transfers (reported, not gated)

| root | n | mean gross (cost) | t | rotation p95, rank | volatility-adjusted 2016–19 / 2020–23 | reading |
|---|---|---|---|---|---|---|
| MES | 185 | +\$16.69 (\$4.42) | 2.18 | +\$11.14, 0.992 | 0.107 / 0.266 | NO PRIZE (net t 1.60) |
| MYM | 187 | +\$10.07 (\$3.80) | 1.73 | +\$9.97, 0.953 | 0.145 / 0.153 | NO EFFECT (t < 2) |
| M2K | 146 | +\$8.36 (\$3.76) | 1.15 | +\$11.17, 0.878 | 0.016 / 0.099 | NO EFFECT |

- **The sign carries to ES and YM,** both above their rotation p95. YM's is the most even across the halves in
  volatility units. **The dollars are NQ's:** it has the largest dollar volatility, and the give-back scales with it.

## 5. The component line

- **MNQ:** net Sharpe 0.84, Sortino 1.50, hit 55.9%, skew +0.48, gross +\$34.88 beside net +\$30.81.
- **Daily ρ:** with D737's twin −0.010, with NQ F2 −0.042, with C1 −0.016 (1,724 days).
- **It is a different clock** (08:35 → 11:01, on 24 days a year) from every NQ line in the vault.

## 6. The reading, and what the confirmation must do

- **SUPPORTED, by the declared rules.** The construction survives its exact null (rank 0.9995), the matched-impulse
  contrast and G2.
- **The principal's test passed only on its win-rate branch, exactly at the boundary.** The volatility-adjusted
  branch failed: the edge per unit of volatility was about three times larger in 2020–23 than in 2016–19. In those
  terms the effect strengthened with the inflation era; it was not born of 2022 (2022 is +0.09σ, and holds the five
  worst trades).
- **Admits nothing.** Only a pass on unread data can promote it. §7 of the pre-registration designed that test, and it
  needs the principal's word:
  - **V, a vault family in slot 2 or 10:** NQ 2024-01-01 → 2026-09-18, 64 release days. The proposed pass: mean gross
    > \$4.07, one-sided t ≥ 1.2816, and above the vault-window rotation p95. Power about 0.63 at the full in-sample
    effect.
    - At the 2020–23 effect (t 2.61 on 93) the expected t on 64 is about 2.17, so power about 0.81.
    - At the 2016–19 effect (t 0.89 on 93) it is about 0.74, so power about 0.29.
  - **F, the forward recorder:** about 4.5 years.
- **For any confirmation, report beside the primary:** the 09:30 → 11:01 leg alone (it is clear of the spent overnight
  slice), the down/up split, and the high-|impulse| tercile.
