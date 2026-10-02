# D766 STAGE 0 PRE-REGISTRATION — crowded leverage and the MBT day: when perpetual-swap funding was extreme overnight, does the CME bitcoin day session (09:30 → 16:00 ET) move against the crowd? (BTC prices, one MBT; prop book)

*2026-10-02. Prop book.*
- *The principal: "Close the MBT expiry idea, any other MBT ideas?". They then chose "Crowded leverage
  (Recommended)".*
- *Numbered D766, claimed with the documentation-review session.*
- ***Committed alone, before its runner exists.** In-sample only (≤ 2023-12-29).*

## 0. The mechanism and what is on file

**The mechanism.** A perpetual swap's funding rate is what longs pay shorts each eight hours to keep the swap near
spot.
- **Extreme positive funding** means leveraged longs are crowded and paying to stay in. **Extreme negative funding**
  means crowded shorts.
- **A crowded side is fragile:** a move against it forces liquidations that feed the move.
- **What it predicts:** after an extreme-funding night, the day leans against the crowd, and is larger.

**On file:**
- **D579:** the funding and open-interest fixture.
- **D580:** the funding *settlement clock* (a five-minute burst at the 8-hour settlements). NOT SUPPORTED.
- **Nothing on file uses the funding *level* as a positioning signal.**

**The regime caveat.**
- The in-sample (2019-09 → 2023) is before the US spot ETFs (2024-01).
- It contains the 2020–21 leverage boom, when funding stayed extreme for weeks.
- **A slow conditioner's effective sample is counted in episodes, not days.** Episodes are counted and gated (G3).

## 1. Data and quantities (fixed now)

**The signal:** `perp_funding.csv`, venue Binance, symbol BTCUSDT, from 2019-09-10.
- **F_d** is the mean of the three funding rates settled at **16:00 UTC on d−1, 00:00 UTC on d and 08:00 UTC on d**.
  Each is published at its settlement, so all three are known at least 5.5 hours before 09:30 ET.
- Settlements are floored to the minute (D579's +1 ms offset).
- Rows on or after 2024-01-01 are dropped as text.

**The crowding state:**
- **The walk-forward percentile:** F_d against the previous 250 sessions' F, strictly prior.
- **Crowded long (L):** F_d > the prior 90th percentile.
- **Crowded short (S):** F_d < the prior 10th percentile.
- The comparisons are strict, because a third or more of the rates sit exactly at the +0.0001 clamp.

**The outcome:** `fut_btc_1m`, root BTC (the price MBT tracks); trade date = the ET date.
- P(09:30) and P(16:00) are each the close of the last bar starting before that time, ineligible if staler than 10
  minutes.
- **r_d** = P(16:00) − P(09:30), in $ per MBT ($0.10 a point).
- **Eligible sessions:** weekdays with both prices, 2019-09-10 → 2023-12-29, after the 250-session burn-in.

**The trade:** against the crowd.
- short MBT at 09:30 on L days, long on S days;
- exit at 16:00;
- net = gross − $4.31 (the default line).

## 2. The gates

| gate | what | passes when |
|---|---|---|
| **G1 direction** | the contrarian mean A = mean of (−r on L days, +r on S days) | A > 0 and above the p95 of the **exact enumerated rotation of the F-percentile series** across eligible sessions (offsets 1 … n−1). The rotation keeps the signal's persistence and the L/S counts |
| **G2 prize** | the contrarian trade | mean gross ≥ $4.31 with a Newey-West(5) t ≥ 2 over the trade sequence |
| **G3 not one episode** | episodes are maximal runs of L (or S) days with gaps of at most 5 sessions | at least 8 episodes in total; the net is positive without 2021 and without 2022; no single episode carries more than 50% of the net |

**The readings:**

| reading | when |
|---|---|
| **NO DIRECTION** | G1 fails |
| **DIRECTION, NO PRIZE** | G1 passes; G2 fails |
| **EPISODIC** | G1 and G2 pass; G3 fails |
| **PREMISE HOLDS** | all three |

**What follows a PREMISE HOLDS:** a trading pre-registration read on the held slice (ETF era) and forward, on the
principal's word. The regime change would be stated.

## 3. Reported, never gating

- **Size:** the mean \|r\| on L or S days against other days, with the same rotation (the liquidation story predicts
  larger days).
- **L and S separately**, and the quintile tails (80th and 20th percentiles).
- **Open interest** (Bybit, daily, from 2020-08): L days on which open interest also rose over the prior day,
  against L days on which it did not.
- **The longer sample:** the same gates on Bybit's inverse BTCUSD funding, from 2018-11.
- **The episodes:** count, lengths and their dates.
- **By year;** the four groups of the contrarian trade, with the top trades named.
- ρ of its daily net with F2, C1 and D737.

## 4. Size and power (stated now)

- **The sessions:** about 1,080 eligible from 2019-09; about 830 after the burn-in, of which about 165 are L or S.
- **The SE:** a CME bitcoin day session moves about $100–160 per MBT (sd), so the SE of the contrarian mean is about
  $10. G2 needs a mean of about $20 or more.
- **The effective sample is smaller:** L days cluster in the 2020–21 boom, so the true SE is larger than $10. The
  rotation null carries that clustering, and G3 guards the episode count.

## 5. The runner's assertions (each proved to raise in `--selftest`)

1. **Lag:**
   - the F_d settlements are all at or before 08:00 UTC on d (asserted per row);
   - a plain loop re-derives F_d, its percentile and the L/S flags for 40 sampled sessions;
   - **Break:** adding the 16:00 UTC settlement of d itself must raise.
2. **The clock:** 09:30 ET maps to 14:30 UTC in January and 13:30 UTC in July.
3. **Sign in money:** short on L pays when the price falls.
4. **The rotation's offset 0** equals the observed A.
5. **The seal:** a 2024-dated row in either input raises.
6. **Synthetic:**
   - a planted contrarian effect passes G1;
   - noise fails it about 95% of the time;
   - **a persistent signal against a trending price is not passed by its own trend:** an AR(1) signal (ρ 0.98)
     against independent returns fails G1 about 95% of the time.

**Speed:** seconds. **Output:** `data/stage0_d766_crowded_leverage.json`.

## 6. Predictions (Opus)

- **P1: NO DIRECTION** (P 0.6). In 2020–21 crowded longs stayed crowded through the trend, and the contrarian trade
  pays only at the turns.
- **P2: L and S days are larger** (size ratio > 1.1) (P 0.6). That is the liquidation channel showing as volatility.
- **P3: fewer than 15 episodes** in total (P 0.6).
- **P(PREMISE HOLDS) ≈ 0.07.**
