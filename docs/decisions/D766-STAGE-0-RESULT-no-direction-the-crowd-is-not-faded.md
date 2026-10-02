# D766 STAGE 0 RESULT — NO DIRECTION: after an extreme-funding night the CME bitcoin day does not lean against the crowd (contrarian mean +$6.96 per MBT, below the rotation p95 of +$10.27, p 0.13); crowded longs ran on in 2021, and on Bybit's longer sample the contrarian side loses in every year

*2026-10-02. Prop book.*
- *Pre-registration: [D766](D766-STAGE-0-PRE-REG-crowded-leverage-and-the-mbt-day.md) (`a7c99592`).*
- *Runner: `scripts/stage0_d766_crowded_leverage.py` (`3f7c331f`).*
- *Output: `data/stage0_d766_crowded_leverage.json`. Wall 3.6 s; one run.*

**The checks:**
- the lag audit (a plain loop re-deriving F_d, its percentile and the flags for 40 sampled sessions) passed inside the
  run;
- the rotation's offset 0 reproduced A;
- nothing dated 2024-01-01 or later was read (the seal is asserted on both inputs).

**A disclosed supplement.** §3 of the pre-registration reports "the same gates on Bybit's inverse BTCUSD funding,
from 2018-11". The runner did not compute that:
- it read BTC prices only from 2019-09-01;
- its 250-session burn-in counts eligible price days;
- so its Bybit line began on 2020-09-02, no longer than the main sample.

`scripts/stage0_d766_bybit_long_sample.py`, written after the run, calls the runner's own functions unchanged and
widens only the price window, to 2018-11-15. Its output is `data/stage0_d766_bybit_long_sample.json`. Both versions are
in §4. The line is reported and never gated.

## 1. The reading

The sample is Binance BTCUSDT funding against the CME bitcoin day session, 09:30 → 16:00 ET.

| | value |
|---|---|
| eligible sessions after the burn-in | **840** (2020-09-11 → 2023-12-29) |
| crowded long (L) / crowded short (S) | **65 / 83** |
| **G1: contrarian mean A** | **+$6.96** per MBT; the exact rotation (839 offsets) gives p05 / p50 / p95 of −$12.23 / −$0.88 / **+$10.27**; **p 0.133** |
| G2: gross against $4.31 | +$6.96, NW(5) t **0.93** (median +$0.75) |
| G3: episodes | **28**, but net ex-2022 is **−$451** and the largest episode is a loss |
| **reading** | **NO DIRECTION** |

**G1 fails.** The contrarian mean is positive, but at the 87th percentile of a null that keeps the signal's
persistence and its L/S counts. G2 and G3 would have failed as well.

## 2. Where it went: crowded longs were right, crowded shorts were squeezed in 2022

| | n | contrarian gross mean | t | median |
|---|---:|---:|---:|---:|
| **L: short after crowded-long nights** | 65 | **−$8.32** | −0.70 | −$19.00 |
| **S: long after crowded-short nights** | 83 | **+$18.93** | 1.66 | +$2.50 |
| quintile tails (80th / 20th percentiles) | 209 | +$7.82 | 1.31 | −$0.50 |

**Shorting the crowded long loses.** After the most extreme long-funding nights the day kept rising. That was P1's
reason:
- **the costliest episode** is 2021-02-03 → 02-22 (12 L days, **−$602**), the run from about $37k to $57k;
- with 2020-12-18 → 2021-01-20 (−$160), the 2020–21 boom's L episodes lost **$762**.

**The S side's gain is one bear market.** In 2022 every flagged day was S: 36 days, **+$844**. Three episodes carry
it:
- 2022-01-13 → 02-04: +$278;
- 2022-02-21 → 03-14: +$181;
- 2022-04-13 → 04-27: +$380.

Without 2022 the trade loses $451.

**Open interest splits the L side** (Bybit linear, daily change; post hoc in spirit, though the split was reported by
design):

| | n | contrarian mean | t |
|---|---:|---:|---:|
| L days with OI rising | 37 | +$16.00 | 1.03 |
| L days with OI flat or falling | 28 | **−$40.46** | **−2.36** |

- **With OI rising** (new leverage arriving), the short leans the way the crowding story predicts, but not
  significantly.
- **When funding is extreme and OI is not growing,** the day continues up hard.

It is one split of 65 days, chosen among several. It is not a finding.

## 3. Size

| | value |
|---|---|
| mean \|r\| on L or S days | $69.67 |
| mean \|r\| on other days | $55.36 |
| ratio | **1.26**; the rotation null's p50 / p95 are 0.98 / **1.38**; rank 0.87 |

**Crowded days are larger, but not beyond what the rotation gives.** Extreme funding clusters in high-volatility
regimes, and the rotation keeps that clustering. The liquidation channel is not separable from the regime here.

## 4. The longer sample (Bybit inverse BTCUSD funding)

| | runner (prices from 2019-09) | supplement (prices from 2018-11) |
|---|---|---|
| sessions (L / S) | 846 (92 / 86), from 2020-09-02 | **1,026 (99 / 100)**, from 2019-12-13 |
| contrarian A | −$8.09 (p95 +$10.02, p 0.89) | **−$7.50** (p95 +$8.40, **p 0.905**) |
| NW t | −1.30 | −1.34 |
| L short / S long | | −$7.67 / −$7.33 |
| net by year | | 2020 −$323 · 2021 −$937 · 2022 −$889 · 2023 −$200 |
| episodes | 32 | 36 |

**On Bybit's funding the contrarian side loses on both sides and in every year.** Even the 2022 S gain does not
transfer from Binance's flags to Bybit's. The two venues disagree on the S side's sign, which is what noise looks
like.

The burn-in again consumed the first 250 sessions (2018-11 → 2019-12). No L or S day fell in 2019.

## 5. The contrarian trade (one MBT; four groups)

**Performance:**

| | net | gross |
|---|---:|---:|
| mean per trade | +$2.65 | +$6.96 |
| median | −$3.56 | +$0.75 |
| daily Sharpe (Sortino), 252 × all 840 sessions | 0.18 (0.27) | 0.46 (0.74) |
| total | +$393 | +$1,031 |

- **The other performance lines:**
  - exposure: 148 of 840 sessions (17.6%), 6.5 hours each;
  - max drawdown: **$1,030**;
  - break-even cost: $6.96 a round trip;
  - with one extra tick: +$2.15 net.
- **The distribution (net):**
  - 148 trades, win 46.6%, payoff 1.24;
  - skew +0.55, kurtosis 2.0;
  - the 1% trims: **ex-top +$0.24, ex-bottom +$4.45, both +$2.03**;
  - **the mean is above the median:** the right tail carries the mean.
- **The best and worst days:**
  - the five best are all S longs: 2022-01-24 (+$358), 2022-02-24 (+$306, the day Russia invaded Ukraine),
    2022-02-28, 2022-02-04 and 2021-06-22;
  - the worst are L shorts: 2021-01-05 (−$262), 2021-02-19 and 2021-02-22.
- **By year (net):**

| 2020 | 2021 | 2022 | 2023 |
|---:|---:|---:|---:|
| −$155 (12) | −$311 (55) | **+$844** (36) | +$15 (45) |

- **ρ with the books:** F2 +0.09, C1 −0.04, D737 +0.00.
- **The component line:** net Sharpe 0.18 on a G1 failure, carried by one year. It is not a component.

**The episodes:**
- 28 in all (10 L, 18 S); their lengths run from 1 to 18 days, with a median of 3;
- the largest by \|net\| are the L 2021-02 episode (−$602) and the three 2022 S episodes above.

## 6. Predictions against outcomes

| | predicted | outcome |
|---|---|---|
| P1 | NO DIRECTION (P 0.6) | **held:** p 0.133; the boom's L episodes lost |
| P2 | size ratio > 1.1 (P 0.6) | **held as stated:** 1.26, though inside the rotation null (p95 1.38) |
| P3 | fewer than 15 episodes (P 0.6) | **missed:** 28 (extreme funding came in short bursts more often than in long regimes) |
| | P(PREMISE HOLDS) ≈ 0.07 | NO DIRECTION |

## 7. What it shows

**The overnight funding level does not set the MBT day's direction.**
- On Binance's flags the contrarian trade is positive but inside its null. Its sides disagree, and its gain is the
  2022 bear market's short squeezes.
- On Bybit's flags, over a longer sample, it loses every year.

**The crowd was not faded in-sample.** In the 2020–21 boom, extreme long funding marked a trend that continued
through the day. A crowd that pays to stay long was often right for longer than a day.

**What is left is size, and size is the regime.** Crowded days are 26% larger, which a volatility forecast already
carries (D720: a day-size forecast is a volatility forecast). No trading pre-registration follows in-sample.

**Open for the principal:**
- **close the funding-level line;**
- or **a post-hoc lead,** written as a new pre-registration: the L-and-flat-OI continuation (−$40, t −2.4 on 28 days)
  as a long-with-the-crowd trade. It is one split of a small sample, found after the run, and its prior should be
  low.

## 8. CLOSED (2026-10-02)

**The principal: "Close this".** The perpetual-swap funding-level line is closed for the prop book. The post-hoc
flat-OI lead is not pre-registered.
