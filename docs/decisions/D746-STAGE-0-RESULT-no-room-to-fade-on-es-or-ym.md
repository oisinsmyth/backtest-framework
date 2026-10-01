# D746 STAGE 0 RESULT — NO ROOM on all four primary cells: on ES and YM, neither a 2.5σ stretch faded to the VWAP nor an opening gap faded to yesterday's close beats a coin-flip bracket; the move at stake is 4–10× the fee, but it does not come back

*2026-10-01. One run of `scripts/stage0_d746_intraday_fades.py --run` (1.7 minutes). The
[pre-registration](D746-STAGE-0-PRE-REG-intraday-fades-stretch-and-gap.md) (`7dfa707e`) was committed before the
runner, and the runner (`0bbf2690`) before its run.*
- **Output:** `data/stage0_d746_intraday_fades.json` (statistics only; no per-date GEX).

## 0. Checks

- **The seal:** every fixture and `DIX.csv` were restricted as text to rows before 2024-01-01 before parsing.
  - ES has 1,941 panel days and YM 1,938, 2016-01-04 → 2023-12-29.
- **The self-test passed:**
  - the sign audit in money (a target pays; a stop loses, with the open beyond it and a tick);
  - the lag audits on real ES bars (A's z and VWAP, B's prior close), with both canaries raising.
- **During the run:**
  - the lag audit passed on a sample of every cell;
  - the threaded timing null equals the serial one on 48 offsets;
  - right quantity: E1 differs from E2 in every cell.
- **The null** is enumerated over 1,901 (ES) and 1,898 (YM) offsets, so its SE is 0.
- **The mirror** (the same bracket entered with the move) is about −E1 less the two sides' stop ticks in every
  primary cell, as a sign audit should be.
- **GEX state (ES days):** short 233, long-low 620, long-high 1,088.

## 1. The result

E1 is the 1:1 bracket. Dollars are per trade at one MES (cost $4.42) or one MYM ($3.80).

| cell | trades | gross | net | NW t (gross) | C2 p50 / p95 | p | Holm | target / stop / close | median target (× 2c) |
|---|---|---|---|---|---|---|---|---|---|
| **A ES k2.5** | 450 | **−5.76** | −10.17 | −1.88 | −2.26 / +3.17 | 0.86 | 1.00 | 0.37 / 0.52 / 0.10 | $39 (4.4×) |
| **A YM k2.5** | 544 | **−1.56** | −5.36 | −0.71 | −0.56 / +3.08 | 0.68 | 1.00 | 0.41 / 0.49 / 0.10 | $32 (4.1×) |
| **B ES g0.5** | 934 | **−5.27** | −9.69 | −1.49 | +0.14 / +4.72 | 0.97 | 1.00 | 0.31 / 0.35 / 0.34 | $89 (10.0×) |
| **B YM g0.5** | 936 | **−0.55** | −4.34 | −0.19 | −0.31 / +3.33 | 0.54 | 1.00 | 0.32 / 0.34 / 0.34 | $74 (9.8×) |
| A ES k2.0 / k3.0 | 759 / 285 | −2.26 / +0.50 | −6.67 / −3.92 | −1.01 / +0.10 | | 0.53 / 0.26 | 1.00 | | $38 / $46 |
| A YM k2.0 / k3.0 | 803 / 343 | −1.30 / −1.34 | −5.09 / −5.14 | −0.68 / −0.44 | | 0.68 / 0.61 | 1.00 | | $31 / $34 |
| B ES g0.25 / g1.0 | 1,393 / 355 | −2.27 / −6.41 | −6.68 / −10.83 | −0.90 / −0.93 | | 0.92 / 0.83 | 1.00 | | $68 / $130 |
| B YM g0.25 / g1.0 | 1,380 / 401 | −0.72 / −0.98 | −4.52 / −4.78 | −0.37 / −0.21 | | 0.59 / 0.59 | 1.00 | | $57 / $100 |

- **Every primary cell reads NO ROOM.** The gross is below 2 × cost, and the kept half at ρ = 0.05 loses.
  - **REVERSION is false everywhere:** no cell's gross is positive at t ≥ 2, and none clears its timing null's p95.
  - **GO is false.**
- **Gross is at or below zero in 11 of the 12 cells.** The one exception, A ES k3.0, is +$0.50 at t 0.10.
  - The fades sit at their own timing null's median: fading the selected stretch or gap is no better than fading
    the same bracket at the same clock on an arbitrary day.
- **The size is there; the direction is not.**
  - The median target is 4–10× the fee in every primary cell, so this is not D684's problem (a move too small to
    pay).
  - Against a 1:1 bracket, the stop is hit at least as often as the target. A's stretches carry on to the stop 49–52%
    of the time and come back to the VWAP 37–41%.

## 2. The four groups (primary cells)

**Performance, net and gross:**

| cell | Sharpe net | Sortino net | max DD | exposure | mean \|move\| vs 2c | breakeven cost |
|---|---|---|---|---|---|---|
| A ES k2.5 | −1.17 | −1.46 | $4,578 | 79 min | | −$5.76 |
| A YM k2.5 | −0.91 | −1.17 | $3,238 | 81 min | | −$1.56 |
| B ES g0.5 | −0.93 | −1.25 | $9,240 | 216 min | | −$5.27 |
| B YM g0.5 | −0.52 | −0.74 | $4,466 | 209 min | | −$0.55 |

- The breakeven cost is the mean gross; it is negative, so no cost clears it.

**Trade distribution:**

| cell | median net | win | payoff | skew | kurt | ex-top 1% | ex-bottom 1% | trimmed |
|---|---|---|---|---|---|---|---|---|
| A ES k2.5 | −18.17 | 0.44 | 0.86 | −0.08 | 0.4 | −11.72 | −8.57 | −10.12 |
| A YM k2.5 | −11.80 | 0.45 | 0.94 | −0.16 | 0.8 | −6.62 | −3.87 | −5.13 |
| B ES g0.5 | −15.67 | 0.46 | 0.94 | +0.15 | 2.8 | −13.69 | −5.87 | −9.88 |
| B YM g0.5 | −14.80 | 0.45 | 1.07 | +0.36 | 4.6 | −7.92 | −1.27 | −4.86 |

- No tail is doing the work: all three trimmed means are negative in every cell.

**What the result depends on:**
- **Positive years:**
  - A ES k2.5: 0 of 8. A YM k2.5: 0 of 8. B ES g0.5: 1 of 8 (2018). B YM g0.5: 3 of 8.
  - The loss is spread across years, not a single regime.
- **By |z| or |g| bin:** no bin reverts reliably.
  - A ES: −5.45 / −7.64 / −4.68 across the bins from 2.5 to above 4.
  - B ES: −4.57 / −9.57 / +0.09 across the bins from 0.5 to above 1.5.
- **By entry hour:** A triggers at 10:00 on 85–88% of days, and the 10:00 cohort loses. The later hours hold 4–46
  trades each and are noise.
- **By dealer gamma (A's mechanism test), gross per trade:**

  | cell | short gamma | long, low | long, high |
  |---|---|---|---|
  | A ES k2.5 | +14.74 (n 57) | −15.92 (169) | −3.30 (224) |
  | A YM k2.5 | +12.55 (60) | −5.89 (199) | −1.51 (285) |

  - The declared contrast (long-high minus short) is −18.0 (Welch t −1.24) on ES and −14.1 (t −1.34) on YM.
  - **GAMMA SUPPORTS A is false.** The point estimates run the wrong way for the hedging mechanism: the fade does
    best on short-gamma days. With about 60 short-gamma trades this is noise, not a lead.

**Nulls:**
- In every cell, C2's p50 sits within $3.5 of the score, and the score is below p95 (table in §1).
- **The null is decisive in the negative:** the fades are indistinguishable from fading at random.

## 3. Oracles

| cell | O1: oracle share / mean net taken / per candidate | O2: ρ to break even | ρ to 2 × cost | kept half at ρ 0.05 | O3: median target vs 2c |
|---|---|---|---|---|---|
| A ES k2.5 | 0.44 / $47.26 / $20.69 | 0.20 | > 0.30 | −$7.61 | 4.4× |
| A YM k2.5 | 0.45 / $37.36 / $16.69 | 0.15 | > 0.30 | −$3.52 | 4.1× |
| B ES g0.5 | 0.46 / $81.30 / $37.17 | 0.15 | 0.30 | −$5.16 | 10.0× |
| B YM g0.5 | 0.45 / $69.97 / $31.62 | 0.075 | 0.20 | −$0.79 | 9.8× |

- **The oracle ceiling is large only because the brackets are wide.** Hindsight on a $40–90 coin flip makes about
  $20–37 a candidate.
- **A filter needs a Spearman of 0.075–0.20 just to break even.** D690's real filters reached 0.04–0.06, and at
  ρ = 0.05 every kept half loses.
- **B YM is the closest:** it breaks even at ρ 0.075, but its unfiltered gross is −$0.55 and inside its null.

## 4. The component line

- **Net Sharpe at one micro:** −1.17 (A ES), −0.91 (A YM), −0.93 (B ES), −0.52 (B YM).
- **Hit rate:** 0.44–0.46.
- **Skew:** −0.16 to +0.36.
- **Gross beside net:** −$5.76 / −$10.17 (A ES), −$1.56 / −$5.36 (A YM), −$5.27 / −$9.69 (B ES), −$0.55 / −$4.34
  (B YM).
- **Daily-P&L correlation:**
  - with D737's in-sample twin: −0.03, +0.11, +0.04, +0.02;
  - with NQ F2: +0.03, +0.05, −0.05, +0.07.
- Uncorrelated, but with nothing to add.

## 5. Predictions against the outcome

- **The prior:** about 20% that either setup shows ROOM, under 10% for GO, with the stretch fade "real but small". The
  result is NO ROOM for both.
- **The stretch fade was not even real:** its gross is at or below zero, and it continues to the stop more often than
  it returns to the VWAP.
- **The gap fade being drift was right in kind:** it is a coin flip around its null.

## 6. Reading

- **The obstacle is direction, not size.**
  - D684's intraday fade failed because the move was cents.
  - Here the bracket is 4–10× the fee and still loses, because extreme moves from the open on ES and YM do not
    return to the morning's VWAP, and opening gaps do not fill to yesterday's close more than they extend.
  - This agrees with D724 (no intraday mean is respected) and with D725 (yesterday's levels are sticky but do not
    pull).
  - D724's "touched more than the mirror" did not become a fill advantage from the open: B's target and stop are hit
    equally (0.31–0.32 against 0.34–0.35).
- **Reported exits, POST HOC and not significant:**
  - Holding A's YM fade to the close with no stop (E2) grosses +$4.50 to +$8.08 (NW t 1.06–1.47).
  - B YM to the close grosses +$3.88 to +$5.55 (t 0.71–1.61).
  - It is the same weak YM reversal D727 found (YM's β is negative in the morning). Its best net is +$4.29 at t 1.13.
    It is recorded as an observation and is not a lead.
- **The mechanism check ran the wrong way.** If dealer hedging dampened intraday extremes, the fade would pay on
  long-gamma days. It loses there, and its only positive cells are on the roughly 60 short-gamma days (not
  significant). Gamma predicts size, not reversion, consistent with D665 and D684.

## 7. CLOSED

*2026-10-01, the principal: "Close D746 and pre-reg C as D747".*
- **D746 is closed:** no intraday fade of a stretch to the VWAP, or of an opening gap to yesterday's close, on ES or
  YM at micro size.
- **Don't re-propose** either fade with a 1:1 bracket on ES or YM, or a dealer-gamma gate for intraday reversion
  (the split ran against the hedging mechanism).
- **Next:** C, NQ's night-break fade, is pre-registered as D747.

## 7a. What stood at the result, before the closure

- **The reading is NO ROOM for both setups.** Whether to close the line is the principal's call (R15).
- **The one remaining prop-compatible reversion candidate is C**, NQ's night-break fade (03:00–09:29; D744's ungated
  observation, −4.48 bp, t −2.08). It is a single reading found after the fact, so it needs its own pre-registration
  on the principal's word.
- **The multi-day ideas stay parked** for the personal book (AITODO).
