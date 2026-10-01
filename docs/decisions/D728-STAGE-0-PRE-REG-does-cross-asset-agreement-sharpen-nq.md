# D728 STAGE 0 PRE-REG — does cross-asset agreement sharpen NQ's continuation from the open, and does NQ's move explain why the Dow does not continue?

*2026-10-01. The principal: "Lets look at (B)". This is step 2 of the trend-detection plan, after D727.*
- **D727 found:**
  - NQ's move since the open continues into the rest of the day at every clock;
  - YM reverses in the morning, and RTY echoes only the morning;
  - NQ's first-|z| ≥ k book pays one MNQ, but the curve does not transfer.
- **The question:** is NQ's continuation stronger when other markets move with it at that clock (a market-wide, or
  rates- or dollar-driven, day)? And is the Dow's morning reversal NQ's move showing up late?
- **The order (R8):** this record is committed before the runner exists, and the runner before its one run.
- **What it is:** a premise check. It chooses no rule, and spends no vault look.

## 0. Data, seal, conventions

- **NQ is D727's object, unchanged:** `fut_NQ_rth_1m`, the same days, σ_oc, clocks, x_t, y_t and z_t, built by D727's
  functions.
- **The agreement assets come from `fut_day1m`** (one-minute day-session bars, 36 roots; bar b is the minute 09:00 +
  b ET):
  - ES, YM, RTY (the equity group);
  - ZN (the 10-year note);
  - 6E (the euro, the dollar's mirror).
- **An asset's open is the 09:30 bar's open; its price at t is the close of the bar starting t−1.** Its σ_oc is the
  RMS of its prior 20 sessions' 09:30 → 15:59 moves. Its z_t uses D727's formula.
- **An asset-day is excluded** if the fixture marks it `same_front = False` (a roll) or `present = False`.
- **The seal:** 2016-01-04 → 2023-12-29. The fixture is filtered at read time, and nothing dated 2024-01-01 or later
  is used.

## 1. Agreement at a clock

**For asset i at clock t, against NQ:**
- a_i,t = +1 if |z_i,t| ≥ 0.5 and sign z_i,t = sign z_NQ,t;
- a_i,t = −1 if |z_i,t| ≥ 0.5 and the signs differ;
- a_i,t = 0 (silent) otherwise.

**Three groups, each tested separately:**

| group | definition | agree | disagree |
|---|---|---|---|
| G_eq | the mean of a over ES, YM and RTY | A ≥ +1/3 | A ≤ −1/3 |
| G_rates | a_ZN: NQ up with ZN up (yields down), the duration story | a = +1 | a = −1 |
| G_usd | a_6E: NQ up with the euro up (the dollar down) | a = +1 | a = −1 |

- **The sign conventions for ZN and 6E are declared now.** The test is two-sided, so an effect with the opposite
  convention shows as WEAKENS, and is reported as such.

## 2. What is measured

**S1, primary: Δβ_g.**
- **Pooled:** NQ's continuation slope (y on x with an intercept, one observation per day and clock, stacked over
  D727's eleven clocks) on agree rows, minus the same on disagree rows.
- **By clock:** reported beside.
- **The null:** the enumerated rotation of the asset's z series across days, against NQ fixed. Agreement is
  recomputed with NQ's own sign, which breaks the same-day link between the asset and NQ. Offsets run 20 … n − 20,
  and the SE of the p95 is 0.
- **p50, p95 and rank** are reported.

**S2, the book:**
- **The book is D727's NQ practical book, unchanged.** Primary k is 1.0, the middle of D727's three, so as not to
  build on D727's after-the-fact best (1.5). k = 0.5 and 1.5 are reported.
- **Split by agreement at the entry clock:** trades, mean and median gross and net per MNQ in agree / silent /
  disagree, for each group.
- **The statistic:** Δ = mean gross (agree) − mean gross (disagree), against the same rotation.
- **The agree-only book:** net and gross Sharpe and Sortino, the trim triple and the years, against the full book.
  Reported.

**S3, the Dow question** (reported; it answers the principal's "why NQ and not YM"):
- **The regressions:** YM's rest of the day y_YM,t on its own move x_YM,t and on NQ's move x_NQ,t together,
  pooled over clocks, with each coefficient against a rotation of NQ's series across days. The same is done for RTY.
- **"NQ leads, the Dow follows"** would show as a positive coefficient on x_NQ with a negative one on x_YM: the Dow
  drifts after NQ and gives back its own move.

## 3. Readings (per group; Holm across the three groups on the rotation rank of Δβ)

| reading | condition |
|---|---|
| **SHARPENS** | Δβ_g is above its rotation's p95 (Holm-adjusted across the three groups) **and** the agree-only book at k = 1.0 has a higher mean net per trade than the full book |
| **WEAKENS** | Δβ_g is below its rotation's p05 (Holm-adjusted) |
| **NOTHING** | otherwise |

- **This record makes no rule.** It decides only what a later rule design may contain.
- **A SHARPENS group may be offered to the principal** as a filter for a future slot-10 vault pre-registration of
  NQ's open-drift follow. That pre-registration needs the principal's explicit, separate word.
- **With NOTHING,** the follow stands, if at all, on its own.

## 4. Runner assertions

- **Lag:**
  - each asset's price at t is re-derived at sampled (day, clock) from the raw rows by a second implementation that
    reads only bars starting before t;
  - the canary reads the t bar and must fire;
  - no negative index (D724's wrap);
  - each asset's σ_oc uses prior sessions only.
- **The alignment:** an asset row and NQ's row are joined by date, never by position. A shifted join must fire the
  audit.
- **Right quantity:** NQ's objects are D727's (asserted equal to a fresh D727 build). Agreement uses NQ's sign at the
  same clock.
- **The self-test (synthetic):**
  - an asset whose agreement days carry stronger NQ continuation reads SHARPENS against its rotation;
  - an independent asset does not;
  - a shifted date join fires the audit.
