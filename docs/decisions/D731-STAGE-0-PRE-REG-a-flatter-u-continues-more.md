# D731 STAGE 0 PRE-REG — the flatness of NQ's volume U: the higher the midday trough against the morning peak, the more the day's move continues into the close?

*2026-10-01. The principal: "I think we should look at a more flat/flatened U shape volume profile?", then "I would
like a proper flatness check, where the high the lower part of the U relative to the morning peaks the better".*
- **Where it comes from:** D730 tested "heavy early then steady" and read NOTHING. Its early-volume terciles ran the
  wrong way: a quiet open continued most. That was seen before this record, and is declared here.
- **What is new:** the principal's measure is the TROUGH relative to the PEAK, a dose-response, which D730 never
  measured. D730's steadiness Q compared the last 30 minutes with the open, not the lunch trough.
- **The order (R8):** this record is committed before the runner exists, and the runner before its one run.
- **What it is:** a premise check. It chooses no rule.

## 0. Data, seal, conventions

- **NQ is D727's object, unchanged.** The volume is from the same one-minute bars, and the normal curve is D730's (the
  mean per minute over the prior 20 sessions).
- **YM and RTY** are reported for S1.
- **The seal:** 2016-01-04 → 2023-12-29. Nothing dated 2024-01-01 or later is read.
- **The money:** one MNQ at $4.07.

## 1. Flatness

- **The windows:** the morning peak is 09:30 → 09:59. The trough is 11:30 → 13:29, the lunch lull of the normal U.
- **Flatness at clock t ≥ 12:00:** the trough so far is 11:30 → min(t, 13:30), at least 30 minutes.
  - F_t = [V_trough(t) / V_peak] / [N_trough(t) / N_peak], where V is today's volume and N the normal curve's.
  - F_t > 1 means today's trough sits higher against today's peak than usual: a flatter U.
- **The clocks:** {12:00, 12:30, 13:00, 13:30, 14:00, 14:30, 15:00}. From 13:30 on, the trough is complete and F is
  fixed for the day.
- **f_t,** the day's F_t as a walk-forward percentile among the previous 250 sessions at the same clock (D671's
  `tiers`), centred at 0.5.
- **The raw ratio V_trough/V_peak** is reported beside F, unnormalised.

## 2. What is measured

**S1, the dose-response (primary):**
- **The model:** y_t = a + β·x_t + γ·x_t·(f_t − 0.5), rows stacked over the seven clocks, where x and y are D727's
  (the move since the open, and the rest of the day, both in σ_oc units).
- **γ > 0:** the flatter the U, the more the move since the open continues.
- **The statistic:** γ, with a NW t (5 lags, day-major order).
- **The null:** the enumerated rotation of the day's flatness series (all clocks together) across days, against the
  prices fixed (offsets 20 … n − 20; the SE of the p95 is 0).
- **Reported beside:**
  - β by f tercile (low / mid / high), pooled and per clock;
  - the same for the raw ratio;
  - the five sessions before each roll excluded (D730's contaminant check).

**S2, the money (an afternoon entry; flatness is not known before lunch):**
- **The trade:** at 13:30, when the trough is complete, if |z_13:30| ≥ k, one MNQ in sign(z), held to 15:59.
  - k = 1.0 is primary; 0.5 and 1.5 are reported.
  - D727 read 13:30 as CONTINUATION, and its 13:30 book at k 1.0 grossed +$11.14.
- **The books:**
  - (a) every entry;
  - (b) entries with f in its top third (the flat days);
  - (c) entries sized 2 MNQ on the top third, 1 on the middle, 0 on the bottom: the principal's "the higher the
    better".
- **Each with all four groups:**
  - net and gross, Sharpe and Sortino, max drawdown;
  - P3a at $50k and $150k;
  - trades, mean, median, win rate, skew, the symmetric 1% trims;
  - years, the largest year's share.
- **The ledger line:** the daily-net ρ of (b) with the MACD arm and with NQ F2 (they share the afternoon clock).
- **The flat-filter gain** (the mean net per trade of (b) minus that of (a)) against the same rotation.

## 3. Readings (declared now)

| reading | condition |
|---|---|
| **FLATNESS DETECTS** | γ above its rotation's p95, γ's NW t ≥ 2, **and** β rising from the low to the high f tercile |
| **FLATNESS ANTI-DETECTS** | γ below its rotation's p05 |
| **NOTHING** | otherwise |

**The go/no-go:**
- **GO** iff FLATNESS DETECTS **and** book (b) at k = 1.0 has a higher mean net per trade than (a) **and** grosses
  ≥ 2 × $4.07.
- **Otherwise** the result is written up, and closing the line is the principal's call.
- **Any vault pre-registration** (slot 10) needs the principal's explicit, separate word.

## 4. Runner assertions

- **Lag:**
  - V_peak, V_trough(t) and the normal sums are re-derived at sampled (day, clock) by a second implementation from
    the raw rows, reading only bars starting before t, and prior sessions for the normal;
  - a canary that includes the t bar must fire;
  - the f tiers use `tier_audit` with its leak canary.
- **Right quantity:**
  - NQ's objects equal D727's known answer;
  - at clocks ≥ 13:30 the trough window is the full 11:30 → 13:29 and F is constant across them, which is asserted.
- **Sign, in money:** q = 2 pays twice q = 1, and q = 0 pays nothing.
- **The self-test (synthetic):**
  - a flatness that raises continuation reads FLATNESS DETECTS against its rotation;
  - an unrelated one does not.
