# D730 STAGE 0 PRE-REG — the principal's three-part trade on NQ: direction from the drift since the open, trend detection from the volume profile (heavy early, then steady), size from the size forecast

*2026-10-01. The principal:*
> "high volume early then constant volume predicts trending?"
>
> "Lets look into (a), we get direction from, delta from open, we get trend detection from the volume and size
> from the dettector?"

- **This is step 3 of the trend line,** after D727 (NQ continues from the open) and D728 (cross-asset agreement does
  not sharpen it; NQ's continuation is its own).
- **The order (R8):** this record is committed before the runner exists, and the runner before its one run. The
  result is a separate record.
- **What it is:** a premise check, the detector first, oracle-style. It chooses no rule.

## 0. Data, seal, conventions

- **NQ is D727's object, unchanged:** the same days (roll days excluded), σ_oc, clocks t ∈ {10:00, 10:30, …, 15:00},
  x_t, y_t and z_t. The volume comes from the same `fut_NQ_rth_1m` bars.
- **YM and RTY** are reported for S1 only, as the transfer view. D728 found NQ leads them.
- **The seal:** 2016-01-04 → 2023-12-29. Nothing dated 2024-01-01 or later is read.
- **The money:** one MNQ at $4.07, as D727.

## 1. The volume profile (all from bars starting before t)

- **The normal curve:** for each one-minute bar of the day, the mean volume over the prior 20 sessions. Prior
  sessions only.
- **E, early relative volume:** volume 09:30 → 09:59 over its normal, which is fixed for the day from 10:00.
- **R_t, recent relative volume:** volume over the 30 minutes before t, over its normal.
- **Q_t, steadiness:** R_t / E. **"Constant volume" means Q_t ≥ 1:** the volume has not faded relative to the normal
  U-shape since the open.
- **The principal's detector, declared primary:**
  - D_t = 1 if E is in its top third, judged walk-forward against the previous 250 sessions' E (D671's `tiers`
    convention), **and** Q_t ≥ 1;
  - D_t = 0 otherwise.
- **The components alone, reported:** E's tercile, and Q_t ≥ 1.

**A known contaminant.** Front-contract volume drifts around rolls
([[an-abnormal-volume-dependent-on-a-rolling-contract-drifts]]). Roll days are already out. S1 is also reported with
the five sessions before each roll excluded.

## 2. What is measured

**S1, detection (primary):**
- **The statistic:** Δβ = the continuation slope (y on x, with an intercept, rows stacked over D727's eleven
  clocks) on D_t = 1 rows, minus the slope on D_t = 0 rows.
- **The null:** the enumerated rotation of the day's volume profile (E and every R_t together) across days, against
  NQ's prices fixed (offsets 20 … n − 20; the SE of the p95 is 0). It breaks the same-day link between participation
  and the move.
- **Reported beside:**
  - the slopes by clock, and for E-tercile and Q alone;
  - the oracle view: the precision of D_t for D727's trend days (the top third of |C − O|/σ_oc within each year) with
    the right sign, against the base rate.
- **The scale caveat:** x and y are both in σ_oc units, so the slope does not grow merely because loud days are big.
  That is the size-versus-trend separation D720–D725 needed.

**S2, the three-part book (reported; nothing chosen):**
- **Direction:** sign(z_t) at the first clock with |z_t| ≥ k. k = 1.0 is primary (D727's middle threshold), with 0.5
  and 1.5 reported.
- **Detection:** take the entry only if D_t = 1 at that clock.
- **Size, the size forecast known the evening before** (D724's F_close, built as D724 built it, finite from 2018-02):
  - q = 2 MNQ in its top walk-forward third;
  - q = 1 otherwise.
- **Size, alternative reading:** the detector's own strength. q = 2 when E is in its top tenth, q = 1 otherwise.
- **Held to the 15:59 close.**
- **The books reported:**
  - (i) D727's book, unfiltered;
  - (ii) detected only, at one MNQ;
  - (iii) detected and sized by F_close;
  - (iv) detected and sized by E.
- **Each with all four groups:**
  - net and gross, Sharpe and Sortino, max drawdown;
  - P3a at $50k and $150k;
  - trades, mean, median, win rate, skew, the symmetric 1% trims;
  - profitable years, the largest year's share.
- **The detection filter against its rotation:** the mean net per trade of (ii), minus that of (i).
- **The sizing against its rotation, under D720's A1 statistic:** Δ net Sharpe, for (iii) against (ii).

## 3. Readings (declared now)

| reading | condition |
|---|---|
| **VOLUME DETECTS** | S1's Δβ is above its rotation's p95, and D_t = 1's slope is positive at a NW t ≥ 2 |
| **VOLUME ANTI-DETECTS** | Δβ is below the rotation's p05 |
| **NOTHING** | otherwise |

**SIZE HELPS** if (iii)'s Δ net Sharpe over (ii) is above its rotation's p95. It is reported whatever S1 reads.

**The go/no-go for a rule design with the principal:**
- **GO** iff VOLUME DETECTS **and** book (ii) at k = 1.0 has a higher mean net per trade than (i) **and** grosses
  ≥ 2 × $4.07.
- **Otherwise** the result is written up, and closing the line is the principal's call.
- **Any later vault pre-registration** (programme slot 10) needs the principal's explicit, separate word.

## 4. Runner assertions

- **Lag:**
  - E, R_t and the normal curve are re-derived at sampled (day, clock) by a second implementation that reads only
    bars starting before t, and prior sessions for the normal;
  - a canary that includes the t bar must fire;
  - no negative index;
  - F_close uses D671's `forecast_audit` and `tier_audit` with their leak canaries.
- **Right quantity:**
  - NQ's objects equal D727's known answer;
  - Q_t = R_t / E is asserted;
  - the volume rotation moves E and R together.
- **Sign, in money:** q = 2 pays twice q = 1.
- **The self-test (synthetic):**
  - a profile that marks the drift days reads VOLUME DETECTS against its rotation;
  - an unrelated profile does not.
