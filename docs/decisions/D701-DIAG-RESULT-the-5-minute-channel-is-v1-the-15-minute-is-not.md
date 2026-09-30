# D701 DIAG RESULT — the 5-minute channel is V1 again (93% of its up onsets fall inside V1's positions, and its continuation lives only there); the 15-minute channel is uncorrelated with V1 (φ 0.00) and continues on both sides of it, but the pieces are small

*2026-09-30. One run of `scripts/diag_d701_channel_v1_overlap.py` (`33652879`), 174 s. Its
[design record](D701-DIAG-DESIGN-do-the-channel-and-v1-carry-the-same-information.md) was committed before the runner,
and the runner before the run.*
- **Checks:** both objects were reproduced through their own runners' functions, exactly:
  - V1: 572 trades, mean net +$10.4748;
  - the channel's +60-minute excess: 5-minute +$4.4090, 15-minute +$6.7642.

  D700's truncation lag audit passed again and fired on its broken book. V1's minute holding mask was checked by a
  loop, which fired on a shifted fill. D699's and D700's short-gamma days are the same 603.
- **What it is:** in-sample, 2016-01-05 → 2023-12-29, a diagnostic. It fits and admits nothing.
- **Output:** `data/d701_channel_v1_overlap.json`.

## The answer in one line

**5-minute: SAME INFORMATION.** The 5-minute channel is V1 read on a finer clock:
- its up onsets come while V1 is already long 93% of the time, against a time-matched 53%;
- the continuation D700 measured lives only there: +$7.09 (t 2.07) with V1 long, −$3.88 on the 37 onsets with V1
  flat;
- V1's trades without a 5-minute channel keep their edge.

**15-minute: the declared rule flags INDEPENDENT and CONDITIONER CANDIDATE.**
- The 15-minute channel is uncorrelated with V1's state (φ 0.00).
- Its continuation shows whether V1 is flat or long.

**Both flags rest on small cells** (41 onsets, 29 trades), and neither is evidence by itself.

## A. Coincidence (short-gamma days)

| | 5-minute channel | 15-minute channel |
|---|---|---|
| V1 long at up onsets | **93.4%** (time-matched base 52.9%), 553 onsets | 66.7% (base 54.2%), 138 onsets |
| V1 long at down onsets | 8.3% (base 51.4%) | 40.9% (base 53.4%) |
| an up channel held at V1's entries | 8.6% (base 12.6%) | 5.1% (base 9.5%) |
| φ, V1's state against the up channel's, every 15-minute close | **+0.344** | **+0.000** |

- **The 5-minute channel tracks V1:** it turns up when V1 is long and down when it is flat.
- **Neither channel is usually already present when V1 enters.** An up channel holds at 5–9% of V1's entries, below
  its base rate. V1 enters before the channel is drawn, and the channel confirms the move afterwards.

## B. The channel's information without V1 (+60 minutes, the signed MES excess over the drift)

| onsets | 5-minute | 15-minute |
|---|---|---|
| up, V1 long | 516: **+$7.09 (t 2.07)**, hit 58.5% | 97: +$7.42 (t 1.04), hit 52.6% |
| up, V1 flat | 37: **−$3.88 (t −0.31)**, hit 40.5% | 41: **+$13.45 (t 1.17)**, hit 61.0% |
| up, pooled | 553: +$6.35 (t 1.93) | 138: +$9.21 (t 1.56) |
| down, V1 long | 46: +$5.19 (t 0.43) | 102: +$3.78 (t 0.58) |
| down, V1 flat | 531: +$2.31 (t 0.70) | 154: +$6.54 (t 1.00) |

## C. V1's information without the channel (V1's 572 trades, split at the deciding close)

| split | trades | mean net | mean gross | median net | hit | drift excess (t) |
|---|---:|---:|---:|---:|---:|---|
| 5-minute channel up | 49 | +$19.56 | +$23.98 | −$8.17 | 44.9% | +$16.12 (0.79) |
| no 5-minute channel up | 523 | +$9.62 | +$14.04 | +$1.83 | 51.1% | +$8.24 (1.35) |
| 15-minute channel up | 29 | **+$18.73** | +$23.15 | +$10.58 | 55.2% | +$18.15 (0.90) |
| no 15-minute channel up | 543 | +$10.03 | +$14.45 | +$0.58 | 50.3% | +$8.43 (1.39) |

## The declared reading

| clock | SAME: up-flat excess < ⅓ of pooled and \|t\| < 1, and V1 without keeps ≥ ⅔ of its gross | INDEPENDENT: up-flat ≥ ⅔ of pooled | CONDITIONER: with − without ≥ $4.42 | reading |
|---|---|---|---|---|
| 5m | −$3.88 < $2.12, t −0.31; $14.04 ≥ $9.93 | no | ($9.94, but superseded by SAME) | **SAME INFORMATION** |
| 15m | no (+$13.45) | +$13.45 ≥ $6.14 | +$8.70 ≥ $4.42 | **INDEPENDENT, CONDITIONER CANDIDATE** |

**What the 15-minute flags are worth.**
- **The conditioner flag rests on 29 trades.** V1's per-trade sd is about $131, so a 29-trade mean has an SE of about
  $24. The $8.70 difference is about 0.35 SE. The design said no split would be evidence by itself, and this one is
  not.
- **INDEPENDENT is a better-supported statement.** It rests on:
  - the φ of 0.00;
  - the continuation's sign agreeing in all four 15-minute cells.

  It is still a description of small cells, not a test.

## What it says

1. **D700's 5-minute result was not a second piece of evidence.** It re-measured V1's trend on a finer clock, so V1's
   t 1.64 and the 5-minute channel's t 1.96 must not be read as two confirmations.
2. **The 15-minute channel appears to be a different read.** It is uncorrelated with V1's state, and it continues
   whether V1 is flat or long.
   - Its pooled evidence is thin: +$6.76, t 1.86 over 466 onsets, which is 0.77 a day.
   - Because it is independent of V1, it could be a separate component rather than a filter on V1.
3. **Neither channel is present at V1's entries** (5–9%). The channel is a confirmation that arrives after V1 is in.
   As an entry conditioner for V1 it would cut V1 to a few dozen trades. It could still serve as a hold or exit rule
   inside V1's trades, which is option 3 of D700.

**The binding constraint on this whole line is unchanged:** nothing here is confirmable on 2024-01 → 2025-02 (66
short-gamma days).
