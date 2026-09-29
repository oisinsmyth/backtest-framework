# D692 DIAG — the MES oracle profile: the hourly continuation's winners concentrate on ES-book short-gamma days, on the long side, late in the day and against the day's move; no bucket clears the $8.84 bar, and the best barely clears the round trip

*2026-09-29. One run of `scripts/diag_d692_oracle_profile_mes.py` (`ca5cb8d7`, committed with the
[design record](D692-DESIGN-the-oracle-profile-at-mes.md) before the run).*
- **The run:** a first attempt stopped in the input stage on a transient out-of-memory, while another session parsed
  the same options file; no statistic had been computed. The rerun took 110 s.
- **Checks:** D688's β_G and D690's MES oracle reproduced exactly.
- **What it is:** hindsight and descriptive, with no verdict. It is the evidence for designing the filters with the
  principal.
- **Output:** `data/d692_oracle_profile_mes.json` (statistics only, no per-date GEX).

## The whole candidate set (1 MES, $4.42 a round trip)

9,760 hourly continuations (1,237 a year), 2016-01-05 → 2023-12-29.
- **WIN** (net > 0): 43.6%.
- **BAR** (gross ≥ $8.84): 36.5%.
- **Mean per trade:** gross +$1.26, net −$3.16.
- **Payoffs:** the winners average +$32.92 net and the losers −$31.01.
- **The breakeven win rate is about 48.5%.** A filter must lift the win rate by about 5 points before it covers the
  round trip, and by far more before it reaches the template's 2c bar.

## The profile

It has 67 buckets, which overlap heavily. With that many, the largest |t| expected under no effect is about 2.5–2.8.
Rates are shown with their lift over the whole set.

| bucket | trades/yr | WIN (lift) | BAR (lift) | mean gross (t) | mean net | share of the oracle's net |
|---|---:|---|---|---|---:|---:|
| **G_SUM < 0** (short gamma) | 379 | 0.493 (×1.13) | 0.453 (×1.24) | +$3.77 (2.93) | −$0.65 | 0.51 |
| G_SUM ≥ 0 | 858 | 0.410 (×0.94) | 0.327 (×0.89) | +$0.15 (0.32) | −$4.27 | 0.49 |
| SPX < 0 (always with the ES book < 0 here) | 156 | 0.483 | 0.455 | +$1.91 (0.76) | −$2.51 | 0.27 |
| **SPX ≥ 0, ES book < 0** | 381 | 0.480 (×1.10) | 0.427 (×1.17) | **+$3.68 (4.00)** | −$0.74 | 0.38 |
| both ≥ 0 | 699 | 0.401 | 0.311 | −$0.21 (−0.44) | −$4.63 | 0.36 |
| G_SUM quintile 0 (most short) | 247 | 0.498 (×1.14) | 0.465 (×1.27) | +$4.74 (2.71) | **+$0.32** | 0.38 |
| G_SUM quintiles 3 / 4 | 247 each | 0.386 / 0.403 | 0.300 / 0.307 | −$0.67 / −$0.24 | −$5.09 / −$4.65 | 0.12 each |
| **short gamma, long side** | 198 | 0.517 (×1.19) | 0.470 (×1.29) | **+$5.55 (3.26)** | **+$1.13** | 0.25 |
| short gamma, short side | 181 | 0.467 | 0.434 | +$1.83 (0.97) | −$2.59 | 0.26 |
| long gamma, long / short | 460 / 398 | 0.436 / 0.381 | 0.342 / 0.309 | +$0.32 / −$0.05 | −$4.10 / −$4.47 | 0.24 / 0.25 |
| 10:30 / 11:30 / 12:30 / 13:30 / 14:30 | ~248 each | .458 / .447 / .395 / .432 / .446 | .397 / .384 / .325 / .357 / .365 | −0.22 / +1.75 / +0.02 / +1.99 / **+2.74 (2.21)** | −4.64 … −1.68 | .23 / .20 / .16 / .19 / .22 |
| short gamma × 13:30 | 76 | 0.487 | 0.450 | +$7.26 (2.74) | **+$2.84** | 0.11 |
| long gamma × 10:30 | 173 | 0.433 | 0.356 | −$2.08 (−1.71) | −$6.49 | 0.11 |
| \|m\| / normal hour, terciles low / mid / high | 412 each | .428 / .424 / .455 | .346 / .352 / .397 | +0.54 / +1.32 / +1.91 (1.99) | −3.88 / −3.10 / −2.50 | .28 / .32 / .40 |
| short gamma × top \|m\| tercile | 160 | 0.514 | 0.477 | +$4.48 (2.31) | +$0.06 | 0.23 |
| today's volatility so far, low / mid / high | 412 each | .377 / .440 / .490 | **.262 / .375 / .459** | +0.32 / +1.16 / +2.29 | −4.10 / −3.26 / −2.13 | .13 / .28 / **.60** |
| short gamma × mid-volatility tercile | 100 | 0.479 | 0.417 | +$4.74 (2.77) | +$0.32 | 0.09 |
| long gamma × high volatility | 164 | 0.469 (×1.08) | 0.424 (×1.16) | +$0.02 (0.01) | −$4.40 | 0.19 |
| last hour WITH / AGAINST the day's move | 778 / 458 | .438 / .432 | .368 / .361 | +0.62 (1.01) / **+2.33 (2.68)** | −3.79 / −2.09 | .61 / .39 |
| year, worst / best | 2017: 152 / 2023: 156 | .344 / .500 | .221 / .463 | −0.35 / +3.73 (2.46) | −4.77 / −0.69 | .03 / .17 |

## What the oracle says (descriptive; no bucket was chosen on this table and then tested)

1. **The winners sit on short-gamma days, and the ES book carries that more than SPX.**
   - The strongest cell of all is **SPX long, ES book short**: +$3.68 gross, t 4.00, 381 a year.
   - That is the population the 2024 slice is made of (D689 §5, caveat 2), so the caveat resolves in the confirmation's
     favour.
   - G_SUM quintiles fall from +$4.74 (the most short) through +$1.73 and +$0.73 to −$0.67 and −$0.24 (the most long).
2. **The long side carries it.**
   - Short-gamma longs make +$5.55 (t 3.26); short-gamma shorts make +$1.83 (t 0.97).
   - D689's drift caveat is confirmed: the short side adds little.
3. **Volatility raises the WIN and BAR rates, but not through direction.**
   - In low-volatility hours only 26% of trades can even clear $8.84, against 46% in high-volatility hours.
   - The mean gross of long-gamma high-volatility hours is zero, though: volatility helps a trade clear its cost, and
     does not make the continuation right.
   - Size alone is not an edge. That matches D690's size-only oracle (−$0.26 at MES).
4. **The later decision times are better than 10:30,** which on long-gamma days loses (−$2.08). Continuations that go
   **against** the day's move so far beat those that go with it (+$2.33 against +$0.62).
5. **At MES nothing clears the bar in expectation.**
   - The best cells net between +$0.06 and +$2.84 a trade: short-gamma longs +$1.13, short-gamma 13:30 +$2.84, the
     most-short quintile +$0.32.
   - A calibrated expected-profit filter at the $8.84 template would take almost nothing.
   - The oracle's 36.5% of bar-clearing trades are spread thin across every bucket: none concentrates them above 48%.

## The design questions this sets for the principal

1. **Universe:** every day, or short-gamma days only? And long side only, given the drift?
2. **The gamma input:** G_SUM, the ES book alone, or SPX × ES cells? The ES book alone looks the stronger.
3. **Conditioning inputs:** time of day (skip 10:30?), alignment with the day's move, today's volatility (as a
   cost-clearing floor, not a direction signal).
4. **The bar at MES:** the 2c template ($8.84) looks out of reach for every cell. Keep it, or use net > 0 (the round
   trip) for this trade?
5. **The form:** a few pre-declared cells (gates), a per-cell expected-profit table, or a fitted projection. Each must
   be scored at MES, walk-forward, and against the oracle with the D690 library.
