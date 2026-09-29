# D697 STAGE 0 RESULT — the move-triggered short-gamma long loses: fast rises on short-gamma days fade into the close (−$13.73 a trade), below even buying at the same minutes on every short-gamma day (+$8.32 gross); the burst trigger selects exhaustion, and the drift does the work

*2026-09-29. One run of `scripts/stage0_d697_short_gamma_burst_long.py` (`1042f2df`, committed with the
[design record](D697-STAGE-0-DESIGN-the-short-gamma-burst-long-to-the-close.md) before the run), 180 s.*
- **Checks:** D688 reproduced. The trigger was re-derived by a loop on 40 days, and the crossing audit fired on gap
  days.
- **What it is:** in-sample, 2016-01-05 → 2023-12-29, with nothing from 2024 read. No slice spent.
- **Output:** `data/d697_short_gamma_burst_long.json`.

## The answer in one line

**The declared reading fails on all three counts:**
- **(a)** the mean net is −$13.73;
- **(b)** it trails the drift control by −$17.63 (NW t −1.66);
- **(c)** it sits at the 19.5th percentile of its rotation null.

**On short-gamma days, a 15-minute burst of at least 1.5σ, above 0.25σ over the prior settlement, is followed by a
fade, not a continuation.**

## 1. The oracle (the ceiling for any later filter)

- **46.5% of the 256 trades win** after cost.
- **The oracle** takes only those: +$145.77 a trade, net Sharpe +2.9, about 15 a year.

## 2. The book (1 MES, $4.42 a round trip; four groups)

| trades | net Sharpe (Sortino) | gross Sharpe (Sortino) | mean net (NW t) | median | hit | payoff | trimmed 1%: both / ex-top | max DD | ρ with the arm |
|---:|---|---|---|---:|---:|---:|---|---:|---:|
| 256 (32 a year, 42% of short-gamma days) | **−0.38 (−0.50)** | −0.26 (−0.35) | **−$13.73 (−1.29)** | −$10.67 | 46.5% | 0.96 | −$13.39 / −$20.61 | $4,285 | +0.13 |

- **By year (net):** 2016 −434, 2017 −237, 2018 −2,255, 2019 −170, 2020 +949, 2021 −56, 2022 −790, 2023 −521. Seven
  of eight years lose.
- **Breakeven:** the mean gross is −$9.31, so no cost level clears it.

## 3. The drift control (declared)

- **Buying at the same minutes on every short-gamma day,** and holding to 16:00, grosses **+$8.32**.
- **The triggered trades gross −$9.31.** The trigger's excess is −$17.63 (NW t −1.66).

**The trigger picks worse entries than the clock.** Whatever positive drift short-gamma days carry into the close, a
fast rise has already spent it.

## 4. Controls (not traded)

- **The same long trigger on long-gamma days:** 380 trades, gross +$1.91, net −$2.51.
- **The downward mirror on short-gamma days** (a fast fall, shorted to the close): 261 trades, gross −$5.49, net
  −$9.91. **Fast falls also fade.**
- **The rotation null** (the short-gamma label rotated across days, applied to every day's long trigger): p50
  −$6.60, p95 +$5.74. The observed −$13.73 is at the 19.5th percentile.

## 5. The path (for conditional exits, as the principal asked)

**Mean gross after entry:**

| +15 min | +30 min | +60 min | +120 min | close |
|---:|---:|---:|---:|---:|
| −$3.46 | −$2.80 | −$0.63 | −$2.46 | −$9.31 |

**Excursions to the close:**
- **Favourable (MFE):** mean $111, median $65.
- **Adverse (MAE):** mean −$133, median −$81.

**By trigger hour (count, mean gross):**

| 09 | 10 | 11 | 12 | 13 | 14 |
|---|---|---|---|---|---|
| 67, −$15.8 | 89, −$10.1 | 44, +$5.3 | 18, −$85.8 | 18, +$73.5 | 20, −$21.9 |

The later cells hold 18–20 trades each and are noise.

**The fade starts at once** (−$3.46 in the first 15 minutes), so the entry buys the top of the burst. Neither a stop
nor a target could reverse a mean that is negative from the first bar.

## 6. What it says, with D695

1. **At the speed of a 15-minute burst, dealer short gamma does not produce continuation.** D695 found the same at
   the hour: aggressively bought hours fade. The amplification the mechanism describes, if present, is swamped by
   short-term overshoot and reversal of the burst itself.
2. **What earns on short-gamma days is the drift, not the move.** Buying at the same minutes on every short-gamma day
   grosses +$8.32 to the close, about 1.9 times the MES round trip. This is D689's drift caveat measured directly.
   It was a control here, so it is a lead, not a finding. The in-sample years were mostly a bull market, and
   short-gamma days are mostly post-selloff days.
3. **The move-triggered construction is closed as designed.** Conditional exits cannot rescue a trade whose mean is
   negative from the first 15 minutes.

## 7. The principal's options

1. **The drift itself:** on short-gamma days, buy at a fixed time and hold to the close. This needs its own
   pre-registration, with a matched control on long-gamma days and on all days (is it gamma, or just post-selloff
   drift?), and a check across market regimes.
2. **Invert the burst:** fade fast rises. That is outside the short-gamma mechanism, and at −$3.46 in the first 15
   minutes the reversal is below the round trip.
3. **Park the short-gamma direction line.** Keep gamma for size, as D665 and D683 found.
