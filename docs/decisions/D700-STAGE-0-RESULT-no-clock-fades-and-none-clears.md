# D700 STAGE 0 RESULT — no clock fades, and none clears: a hand-cell channel on ES continues weakly at its onset on the 5- and 15-minute clocks (+$4.41 and +$6.76 a MES event over 60 minutes on short-gamma days, above their timing nulls' p95, but clustered t 1.96 and 1.86), about one round trip; on the 1-minute clock there is nothing; waiting until the channel has held for 10 closes removes what there is

*2026-09-30. One run of `scripts/stage0_d700_channel_clock_profile.py` (`7bbabf1d`), 221 s. Its
[design record](D700-STAGE-0-DESIGN-where-es-channels-stop-fading.md) (`8abf0124`, on main from `44f1e3ae`) was
committed before the runner, and the runner before the run.*
- **Checks:** D688 reproduced bit for bit.
  - **Lag audit:** on every clock, 30 truncated rebuilds agreed with the full run (12–13 of them on channel bars), and
    the audit RAISED on a detection read one bar ahead.
  - **The rescaling:** σ̂ was re-derived by a loop, and the rescaled sd is 1.05–1.06 × σ_ref.
  - **The splice:** the spliced series differs from the gapped one.
  - **Random walks:** `--selftest` passed. On eight more random-walk seeds the +60-minute excess was centred (mean t
    −0.27 over 144 cells). The t's spread there was 1.17, not 1.00, so a clustered t of 2 is slightly lenient here.
- **What it is:** in-sample, 2016-01-05 → 2023-12-29; 603 short-gamma and 1,386 long-gamma days. It trades nothing.
- **Output:** `data/d700_channel_clock_profile.json`.

## The answer in one line

**My prediction was wrong.** I argued, from D697 and D695, that fast ES moves fade, so a channel detector on the
1-minute clock would buy exhaustion. **No clock fades.**
- **On the 5- and 15-minute clocks,** a channel's onset is followed by a small continuation on short-gamma days. Both
  sit above their timing nulls' p95.
- **But neither reaches the declared t of 2,** and the size is about one MES round trip over 60 minutes.
- **On the 1-minute clock** there is nothing at 60 minutes.

**All three clocks read NEITHER.**

## 1. The profile at f = 0.1, the primary definition

Signed MES dollars a detection, gross. Each cell is the mean excess over the time-matched drift, with its clustered t.

| clock | class | events a day | +15 min | +30 min | **+60 min** | to 16:00 | +60 hit / median |
|---|---|---:|---|---|---|---|---|
| 1m | short γ | 9.4 | +$1.05 (1.68) | +$1.32 (1.38) | **+$0.61 (0.42)** | +$3.88 (1.19) | 52.0% / +$3.75 |
| 1m | long γ | 5.4 | +$0.39 (1.26) | +$0.64 (1.38) | +$1.17 (1.60) | +$3.46 (2.14) | 49.6% / $0.00 |
| **5m** | **short γ** | 2.1 | +$1.63 (1.45) | +$1.16 (0.76) | **+$4.41 (1.96)** | +$10.31 (1.76) | 53.0% / +$4.38 |
| 5m | long γ | 1.1 | +$0.74 (1.23) | +$0.47 (0.55) | +$1.88 (1.55) | +$2.81 (0.97) | 50.2% / +$1.25 |
| **15m** | **short γ** | 0.7 | +$2.03 (1.00) | +$2.76 (1.06) | **+$6.76 (1.86)** | +$2.19 (0.23) | 50.8% / +$1.88 |
| 15m | long γ | 0.4 | −$0.02 (−0.02) | −$0.54 (−0.40) | −$0.45 (−0.22) | −$5.20 (−1.28) | 49.4% / $0.00 |

The drift controls are all within ±$1.54, so the excess is almost all the gross.

## 2. The timing null and the declared reading (short-gamma days, +60 minutes)

This null gives each day another short-gamma day's event schedule, enumerated over 584 offsets (SE 0).

| clock | observed | p05 | p50 | p95 | percentile | clustered t | reading |
|---|---:|---:|---:|---:|---:|---:|---|
| 1m | +$0.65 | −$2.21 | −$0.01 | +$2.56 | 0.659 | +0.42 | NEITHER |
| 5m | +$4.39 | −$3.65 | −$0.05 | +$3.76 | **0.971** | +1.96 | NEITHER (t below 2) |
| 15m | +$6.21 | −$6.45 | −$0.60 | +$5.69 | **0.967** | +1.86 | NEITHER (t below 2) |

Two of the three clocks pass the null leg and miss the t leg by 0.04 and 0.14.

**Taken as a family of three, with the t's slightly wide spread on random walks, these are not significant.**

## 3. Where it lives

- **Gamma contrast:**
  - **15m:** clear. Short γ +$6.76 against long γ −$0.45.
  - **5m:** weaker. Short γ +$4.41 against long γ +$1.88.
  - **1m:** none.
- **At the onset, not after.** Under the strict reading of "stable" (held at each of the last 10 closes), the
  continuation is gone on every clock (short γ at +60 min):
  - 1m: +$1.73 (t 1.06);
  - 5m: +$0.06 (t 0.02);
  - 15m: −$2.98 (t −0.50).

  Confirmation delay is expensive (the principal's objection to 2.5 hours was right, and D477's lesson again): what
  little continuation there is belongs to the channel's first bar.
- **The slope floor (+60 min, short γ):**
  - **1m** inverts, as D477 did: +$1.70, +$0.61, −$1.38, −$4.87 across f = 0.05, 0.1, 0.2, 0.4.
  - **5m** does not invert: +$3.36, +$4.41, +$4.38, +$13.35. The last is on few events.
  - **15m** peaks at 0.1: +$3.74, +$6.76, +$5.29, −$8.28.
- **Direction (5m, short γ):** up +$6.35 (t 1.93), down +$2.54 (t 0.80). Both continue, and the up side is stronger.
- **Hour (5m, short γ):**
  - 09: 84 events, −$19.9;
  - 10: +$8.5; 11: −$4.4; 12: +$10.6; 13: +$4.0; 14: +$13.8.

  The cells are small, and no hour was declared. The first hour, where the channel is anchored in yesterday's
  afternoon, is the worst.
- **Coverage:**
  - both lines are drawn at 39–45% of bar closes;
  - an up channel on the primary definition holds at 10–15% of closes, and a down channel at 9%.

## 4. What it says

1. **The 1-minute detector is dead, as the principal first proposed it.** It neither fades nor continues at 60
   minutes, and its slope floor inverts.
2. **At 5 and 15 minutes a channel's onset carries a little continuation on short-gamma days.** It is about one round
   trip at 60 minutes, beats its timing null, and stops short of the declared t.
   - It is the same kind of evidence as D699's V1: right direction, right gamma contrast, just short of the bar.
   - The two likely overlap. Both are 15-minute-scale trend signals on the same days, and nothing here measured their
     correlation.
3. **I was wrong on one point, and right on another.**
   - **Wrong:** "fast ES moves fade" does not carry from D697's bursts to channels. A channel's onset is an orderly
     move, and orderly moves did not fade here.
   - **Right:** a long confirmation window spends the move.

## 5. The principal's options

1. **Stop.** No clock clears, and the 1-minute construction is closed as proposed.
2. **Test the channel as V1's companion, not as a new entry.**
   - **First,** measure how much the 5- and 15-minute channel onsets overlap V1's entries on the same short-gamma days.
   - **If they are the same information,** there is nothing to add.
   - **If they are not,** the agreement of two independent trend reads is the natural conditioner, and it would be
     designed with the principal against V1's oracle.
3. **Use the channel as V1's exit** (a break of the support line), as proposed before D700. It targets V1's weakness:
   a median trade of +$0.58.

None of these would be confirmable on 2024-01 → 2025-02 (66 short-gamma days). The vault question from D699 stands
unchanged.
