# D695 STAGE 0 RESULT — none of the three inputs carries direction for the short-gamma long continuation: order flow and the gamma profile point the wrong way, breadth is flat, and every Spearman is under 0.025 of the 0.05 target

*2026-09-29. One run of `scripts/stage0_d695_directional_inputs.py` (`783db0ae`, committed with the
[design record](D695-STAGE-0-DESIGN-three-directional-inputs-ranked-at-mes.md) before the run), 199 s.*
- **Checks:** D688 reproduced, and G_ES re-evaluated at the prior settlement equals D688's on all 583 short-gamma
  sessions. The rotation's k = 0 reproduced every Spearman.
- **What it is:** in-sample 2016-01-05 → 2023-12-29, with nothing from 2024 read. No verdict, and no slice spent.
- **Output:** `data/d695_directional_inputs.json`.

## The fixture (order flow)

`fut_ES_signed_1m` holds 792,639 regular-session minutes, 2016-01-04 → 2023-12-29, from Sierra Chart's ES ticks
(front contract, aggressor side). Its metadata is in `data/fixtures/fut_ES_signed_1m.meta.json`. **Its declared
validation against the Databento 1-minute bars passed:**
- median volume ratio 1.000;
- per-minute volume correlation 0.9997;
- signed share 1.000;
- the last trade equal to the bar's close on 98.9% of minutes, and within one tick on 99.94%.

The build took 87 s. A first version formatted a time string per trade; it was stopped after 48 minutes and rewritten
to use integer minute buckets.

## The universe

G_SUM < 0, last hour up, 1 MES long for the next hour: **1,561 trades (198 a year), 51.7% winners, mean net
+$1.13.**

## The ranking (Spearman with the MES net; higher score declared better)

| input | n | Spearman | AUC vs the oracle | the curve's net Sharpe at that Spearman | rotation null p05 / p95 (percentile) | score terciles, low → high: mean net (win rate) |
|---|---:|---:|---:|---:|---|---|
| **A1** order-flow imbalance, last hour | 1,561 | **−0.031** | 0.478 | +0.16 | −0.107 / +0.107 (0.32) | +$3.75 (55%) / −$1.25 (51%) / +$0.89 (50%) |
| A2 net flow ÷ usual volume | 1,522 | −0.031 | 0.481 | +0.16 | −0.110 / +0.106 (0.33) | +$3.16 / +$1.57 / −$1.77 |
| A3 imbalance, last 15 minutes | 1,561 | −0.006 | 0.493 | +0.16 | −0.100 / +0.114 (0.44) | +$2.47 / +$2.79 / −$1.87 |
| **B1** NQ/RTY/YM also up (0–3) | 1,350 | +0.022 | 0.504 | +0.35 | −0.115 / +0.114 (0.65) | −$0.66 (low) / +$2.19 (high); a discrete score, so the middle tercile is empty |
| B2 their scaled mean move | 1,350 | +0.011 | 0.508 | +0.25 | −0.106 / +0.129 (0.53) | +$1.42 / +$2.81 / +$0.21 |
| C1 how short gamma now | 1,561 | −0.008 | 0.489 | +0.16 | −0.105 / +0.103 (0.46) | +$1.34 / −$0.33 / +$2.37 |
| **C2** how much shorter the move made them | 1,561 | **−0.048** | 0.477 | +0.16 | −0.105 / +0.103 (0.23) | +$2.44 / +$0.79 / +$0.15 |

**The partial-oracle curve on this universe (q = 50%):**

| Spearman | 0.00 | 0.02 | 0.05 | 0.07 | 0.09 | 0.14 | 0.19 |
|---|---|---|---|---|---|---|---|
| net Sharpe | +0.16 | +0.36 | +0.53 | +0.71 | +0.89 | +1.27 | +1.55 |

**The family null** (the maximum over the seven scores, per rotation): p50 +0.076, p95 +0.162.

**The declared reading: no input carries direction, survives the family, or is worth a filter.**

## What it says

1. **Order flow points the wrong way.**
   - Rises made on the LEAST aggressive buying continue best: +$3.75 and 55% winners in the lowest-imbalance tercile.
   - Rises on the most aggressive buying fade to +$0.89.
   - The declared mechanism (hedging flow still running, so it continues) is not what the data show. If anything, an
     aggressively bought hour has spent its buying.
   - At −0.031 it is about −1.2 standard errors, so it is not a finding either way.
2. **The gamma profile also points the wrong way.** C2 is −0.048, the largest |Spearman| of the seven: rises that
   left dealers shorter continue less, not more.
3. **Breadth is flat.**
   - B1 is +0.022, positive as declared, but half the 0.05 target and well inside noise.
   - When all of NQ, RTY and YM rose too, the trade averaged +$2.19, against −$0.66 when none did. That is suggestive,
     not significant.
4. **The detection limit.**
   - With 1,561 trades, a Spearman's iid standard error is about 0.025, so the 0.05 target is only 2 SE. This
     universe can barely confirm the accuracy a filter needs even when it is there.
   - The enumerated rotation null is wider still (p95 ≈ +0.10–0.13), because a rotated score overlaps the universe on
     fewer trades. That makes the declared bar conservative, and it does not change the reading: no input is positive
     beyond even the iid bound.

## What this leaves, for the principal

- **The three mechanism-grounded inputs do not supply the missing direction,** and two of them point the other way.
- **The trade stays where D693 left it:** the short-gamma long gate at MES, +$1.13 a trade, +0.28 net, below a
  component's bar.
- **The detection limit binds.** At about 200 trades a year, any input would need a Spearman of about 0.05 AND
  several years of data to show it.

**Possible next steps, the principal's call:**
1. Park the short-gamma continuation as mechanism evidence.
2. Pursue D (intraday implied volatility, which needs data) as the last mechanism that would explain the long-only
   asymmetry.
3. Widen the universe to raise power, for example NQ alongside ES. That would need NQ's own gamma, since NQ options
   are on disk.
