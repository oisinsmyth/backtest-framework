# D747 STAGE 0 RESULT — NOT SUPPORTED (and NO ROOM on ES): the night-break fade does not replicate on the data D744 never read; on the slice it did read, it rests on 2022

*2026-10-01. One run of `scripts/stage0_d747_night_break_fade.py --run` (4.8 minutes). The
[pre-registration](D747-STAGE-0-PRE-REG-the-night-break-fade.md) (`a5bcf880`) was committed before the runner, and the
runner (`ec312ce2`) before its run.*
- **Output:** `data/stage0_d747_night_break_fade.json`.

## 0. Checks

- **The known answer:** D744's U was rebuilt with D744's own `night_break` and `night_exit`. It matches exactly:
  298 trades and −4.475559322876281 bp, from 2018-01-09.
- **The seal:** nothing on or after 2024-01-01 reached any frame (D744's chain, `Z.no_session_after`).
- **The levels:** they are the previous session's RTH high and low on 25 sampled sessions per root. The same-day
  canary fired.
- **The second implementation:** an independent bar loop agrees with the vectorised engine on every trade in every
  cell (fill bar, side, fill price, exit price). The 09:28 canary disagreed on 3–289 trades per cell.
- **Sign:** a sold break that falls to its target pays; one that rises to its stop loses.
- **Right quantity:**
  - E1 ≠ E2;
  - the 03:00-inside condition binds (210 ES and 216 NQ sessions were already beyond a level);
  - no bar filled both sides;
  - the night cost exceeds the day cost (MES \$5.13 against \$4.42; MNQ \$4.60 against \$4.07).
- **A disclosed blank:** NQ-early's correlations with NQ F2 and C1 are undefined. Neither line trades before 2018 in
  its in-sample window, so their daily series are constant.

## 1. The result

The decision cells are ES-full and NQ-early, both never scored by D744. Dollars are per trade, gross, at one micro.

| cell | trades | gross (NW t) | net, night cost | C2 p50 / p95 | p | median target (× 2c) | years + |
|---|---|---|---|---|---|---|---|
| **ES-full b0.25 (primary)** | 405 | **+1.45 (+0.56)** | −3.67 | +0.18 / +4.22 | 0.30 | \$46 (4.5×) | 2 of 8 |
| ES-full b0.10 | 405 | −2.13 (−1.73) | −7.26 | −0.81 / +1.19 | 0.85 | \$18 (1.8×) | 0 of 8 |
| ES-full b0.50 | 405 | +5.84 (+2.02) | +0.71 | +0.53 / +5.90 | 0.05 | \$92 (9.0×) | 3 of 8 |
| **NQ-early b0.25 (second)** | 94 | **−0.50 (−0.19)** | −5.10 | +0.58 / +4.41 | 0.67 | \$26 (2.8×) | 0 of 3 |
| NQ-early b0.10 / b0.50 | 94 | −1.89 / +1.24 | −6.49 / −3.36 | | 0.91 / 0.46 | | 0 / 1 of 3 |

**The decision:**
- condition 1 (ES-full b0.25) fails;
- condition 2 (NQ-early the same sign) fails;
- condition 3 fails;
- there is no LEAD;
- **NO ROOM on ES-full:** the gross is \$1.45 against 2c of \$10.25, and the kept half at ρ 0.05 makes −\$1.95.

**NOT SUPPORTED.**

**The post hoc slice** (NQ 2018-01-09 → 2023, which D744 read; never in the decision):

| cell | trades | gross (NW t) | net | C2 p95 | p | years + | net without the best two years |
|---|---|---|---|---|---|---|---|
| NQ-late b0.25 | 293 | +9.09 (+1.79) | +4.49 | +9.29 | 0.05 | 4 of 6 | −\$844 |
| NQ-late b0.50 | 293 | +13.99 (+2.12) | +9.39 | +11.66 | 0.02 | 3 of 6 | −\$1,064 |

- The fade does show where D744 found the reversal. But **2022 alone is +\$1,707 of the b0.25 book's +\$1,315
  total.** Without its two best years it loses.
- On the unread NQ years before it, and on ES, it is not there.

## 2. The four groups (ES-full b0.25, the primary)

- **Performance:**
  - net −\$3.67 a trade (gross +\$1.45);
  - net Sharpe −0.52, Sortino −0.72;
  - max drawdown \$1,887;
  - 405 trades in 8 years (about 51 a year; it abstains on about 77% of candidate nights);
  - at the day cost, net −\$2.96;
  - the breakeven cost is \$1.45, against \$5.13.
- **Trade distribution:**
  - median −\$2.33, win rate 0.47, payoff 0.95, skew +0.24, kurtosis 0.7;
  - trims: ex-top −\$5.18, ex-bottom −\$2.35, trimmed −\$3.86;
  - exits: 0.31 target, 0.32 stop, 0.37 at the 09:29 close;
  - sell fades −\$4.9 (228), buy fades −\$2.1 (177).
- **What it depends on:**
  - years −532 / −230 / −304 / −393 / +23 / −190 / +337 / −199 (2016 → 2023);
  - the top trade is 2020-03-25, sell, +\$219.
- **Nulls:** C2 p50 +0.18, p95 +4.22, and the score of +1.45 sits at the 70th percentile. Fading a break of yesterday's
  range is no better than fading the night's move at a random clock.

## 3. The component line

| cell | net Sharpe | hit rate | skew | gross / net | ρ with D737's twin | ρ with NQ F2 | ρ with C1 |
|---|---|---|---|---|---|---|---|
| ES-full b0.25 | −0.52 | 0.47 | +0.24 | +1.45 / −3.67 | +0.01 | +0.10 | −0.01 |
| NQ-early b0.25 | −1.52 | 0.47 | −0.31 | −0.50 / −5.10 | −0.06 | — | — |

## 4. Predictions against the outcome

- **Opus:** P(SUPPORTED) ≈ 0.15 → NOT SUPPORTED ✓.
- "NQ-early will be positive" ✗: it is −\$0.50, 0 of 3 years.
- "ES-full's gross will be positive but under 2c" ✓: +\$1.45 against \$10.25.

## 5. Reading

- **The night-break reversal was a property of the slice it was found on, not of the market.**
  - D744's U found it on NQ 2018–2023. The fade reproduces it there, but 2022 carries the whole book.
  - On NQ's two earlier years, and on ES's eight, the same construction is a coin flip at its own null.
  - This is [[layers-selected-on-spent-names-vanish-out-of-sample]] once more, here on spent years rather than spent
    names.
- **A note on b0.50, not a lead.** ES's widest bracket grossed +\$5.84 at t 2.02, just under its null's p95 (+\$5.90).
  - It almost never reaches its target or stop (81% of trades go to 09:29), so it is the E2 fade (+\$6.74), a small
    drift back toward yesterday's range by the open.
  - It nets +\$0.71 with 3 of 8 years positive, and without its two best years it loses.
  - Under the record's rules it is noise. It is recorded so it is not re-proposed as a finding.
- **With D746, the prop book has no intraday mean-reversion line on the index micros:**
  - D746: neither the day session's stretches nor its gaps come back.
  - D747: the night's breaks do not come back either, outside 2022 on NQ.

## 6. Next

- **The reading is NOT SUPPORTED.** Closing it is the principal's call (R15).
- **Not proposed:** another reversion construction on the index micros. Two in-sample tests and D724/D725 all say the
  same thing.
- The multi-day ideas stay parked for the personal book.
