# D761 STAGE 0 PRE-REG — round-number stop cascades outside US hours, on M6E and MBT: does crossing a round level in a thin session start a run worth one micro?

*2026-10-02. The principal: "ok I would like to have a strategy or two that can trade on the outside the US hours";
"I like #1, can you have a fable 5.1 agent recommend the best construction and I would like you to do so also in
parallel"; "Put MBT in also".*
- **The design:**
  - It merges two independent designs, written before either author read the other's: a Fable 5.1 agent's, which
    read the papers in full, and Opus's.
  - Its key literature figures were checked against the saved paper texts.
  - Both drafts are in the session scratchpad (`fable_round_numbers.md`, `opus_round_numbers.md`).
- **What it is:** a premise check. It chooses no rule.
- **The order (R8):** this record is committed before the extraction and the runner exist; the runner before its one
  run; the result separately.
- **The prop book's rules:**
  - one micro (M6E or MBT), inside one Globex session, flat before 16:10 ET;
  - fully algorithmic;
  - no hedging (one position at a time).
  - MBT's eligibility is the principal's assumption (D758), not verified.

## 0. The mechanism and what is known

- **Osler** (FRBNY SR125 / JF 2003; SR150 / JIMF 2005; EPR 2000), on RBS's complete conditional-order book: 9,655
  orders in USD/JPY, GBP/USD and EUR/USD, 1999–2000.
  - **Take-profits cluster AT round numbers.** 9.3–9.9% of executed take-profits sit at endings 00, against 3.8–4.4%
    of stop-losses. So rising prices stall there.
  - **Stop-losses cluster JUST BEYOND them:**
    - stop-loss buys: 14.3% at endings 01–10 against 6.9% at 90–99;
    - around 50 the asymmetry is larger (18.1% at 51–60 against 6.3% at 40–49).
    - So a crossing triggers stops, which push the price further: a cascade.
  - **The price effect is small.** Comparing round with arbitrary levels:
    - continuation after a crossing is 0.3–0.9 points more over 15 minutes, on a base of 5–7;
    - crossing minus reversal is 0.8–1.3 points over 15–30 minutes;
    - it is gone by a day.
    - The illiquid NY afternoon roughly doubles it.
  - "Large, noticeable cascades happen at most once per week", against about 5 crossings a day.
  - The 50s carry the cascade; the 00s carry the wall.
- **Later work:**
  - Mitchell and Izan (2006): FX clustering yes, barriers weak.
  - Aggarwal and Lucey (2007) on gold: barriers are a variance effect, not a drift.
  - O'Connor and Lucey (2016): gold's \$10 drift exists in daily fixes only; silver has none.
  - Dowling et al. (2016): oil's barriers faded after 2007.
  - Kuo, Lin and Zhao (RFS 2015): round-number clustering in futures is retail.
  - CME stops are stop-limit orders with protection points (repo lane 21), so the exchange throttles cascades
    mechanically.
  - No study re-measures FX after algorithmic trading (about 2007).
- **The size arithmetic, which shapes the design:**
  - On M6E 1 bp = \$1.37. The literature's thin-session excess is about \$1.4–3.4 a crossing, against a \$8.76 bar.
    **Unconditionally, nothing clears.**
  - Only the cascade subset can clear: a ~10-pip stop band, about \$12.50, and real cascades of 20–40 pips.
  - So the construction stands or falls on picking out FAST crossings, and on entering FROM the trigger.
- **MBT:**
  - its cascades are forced liquidations of leveraged crypto positions, plausibly far larger than the bar;
  - it has the weakest fit to "outside US hours" (crypto has no thin session in the FX sense);
  - D758 found the bitcoin path reaches the level beyond a weekend gap more often than it fills (post hoc), which is
    the continuation sign.
- **The repo:**
  - no study of round numbers on futures;
  - D725 (NQ) found yesterday's levels are sticky zones that price falls back behind. That is a different source of
    levels, and it is this design's main failure mode.
- **The priors** (before any run):
  - M6E primary: about 12% (Fable) / 10–15% (Opus);
  - MBT: about 20% (Fable);
  - MGC: about 6%;
  - the premise gate (§5) passing on M6E: about 55%.

## 1. Data, seal, conventions

- **M6E's price series:** full-size 6E one-minute bars of the front contract, all hours, from the raw Databento
  ohlcv-1m archive (the same price as M6E; the deeper book prints every minute). The next contract is kept too, for
  the basis.
  - The front contract per day is `fut_breadth_hourly`'s.
  - **The roll week is excluded:** the 5 sessions before expiry, because 6E is deliverable (the standing rule on
    expiring physical contracts).
  - Window: 2010-06 → 2023-12.
- **MBT's price series:** `data/fixtures/fut_btc_1m.csv.gz` (BTC front contract, all hours), read as text with
  `day` < 2024-01-01.
  - Window: trade dates 2018-01-01 → 2023-12-31.
  - The MBT era (from 2021-05-03) is reported.
- **MGC (variant):** full-size GC one-minute front bars, all hours, from the raw archive, 2010-06 → 2023.
- **The seal:** nothing dated 2024-01-01 or later is read, for any input.
- **Spot-equivalent levels:**
  - **6E:** the forward basis comes from the front/next calendar spread over 12:00–15:00 ET of the PRIOR session,
    scaled by (days to front expiry) / (days between the two expiries). It is frozen for the next Globex session.
    S ≈ F1 − b.
  - **BTC:** the basis is the prior session's median of (CME BTC close − Binance BTCUSDT spot close) at the 15-minute
    stamps 12:00–15:00 ET (`crypto_binance_15m_raw`, read before 2024), frozen for the next session.
- **The clock:** UTC → ET by zoneinfo, checked against the statutory US rule on every bar.
- **Prices:** an entry or exit at minute t uses only bars that start before t, except the stop-entry's fill rule (§3).
- **Costs:**
  - M6E: \$4.38 a round trip (bar 2c = \$8.76). M6E tick 0.0001 = \$1.25.
  - MBT: \$4.31 (bar \$8.62). MBT tick \$5 on the price = \$0.50.
  - MGC: \$5.93 (bar \$11.87).
  - The full round-trip cost is charged ON TOP of the stop-entry's modelled slippage, which is conservative: it
    counts the entry's half-crossing twice.

## 2. The levels

| | round grid (treatment) | half-round grid (primary control) | stop band (excluded from the offset null) |
|---|---|---|---|
| M6E | spot-equivalent xx00 and xx50 (50-pip spacing); 00 and 50 reported separately | xx25 / xx75 | offsets within ±10 pips |
| MBT | spot-equivalent \$1,000 multiples | \$500 offsets | ±\$200 |
| MGC (variant) | futures \$10 multiples | \$3, \$4, \$6, \$7 offsets | ±\$1 |

- **The futures-round 6E grid** (no basis adjustment) is its own reported cell. The bank stop book predicts the spot
  grid; CME chart traders predict the futures grid.

## 3. The construction (per cell)

- **The window:**
  - **Asia, 18:30 → 02:00 ET**, the primary;
  - London (02:00 → 08:00) is the contrast: the euro's deepest session;
  - NY (09:00 → 16:00, am against pm) is the replication reference.
  - Exits are on the clock; a trade entered before a window's end may run past it, never past 16:10.
- **The trigger (up; down mirrors):** level L is crossed in bar b when high(b) ≥ L + 1 tick and close(b−1) ≤ L.
  - It must be the first crossing of L in that direction in the session, with no close above L in the previous
    60 minutes.
  - One position at a time; a 60-minute cooldown per level.
- **The side:** WITH the crossing (long an up-cross). The fade is not traded.
- **Entry, two lenses on the same events, never pooled:**
  - **Lens A (primary): a resting stop at L + 1 tick.**
    - Fill = min(high(b), L + 1 tick + s), or open(b) if b opened beyond L.
    - The slippage ladder is s = 1, 2, 4 ticks, with s = 2 the headline.
  - **Lens B: a market order at open(b+1)** after close(b) ≥ L + 2 ticks.
  - **A − B per event** measures how much of the run is inside the crossing minute. It is a registered output.
- **The fast filter (the selection), with the timing fixed so nothing is read after the fill:**
  - **Lens A:** the stop is live during bar b only if the approach is fast, measured on COMPLETED bars:
    - the mean one-minute range over b−5 … b−1, divided by the median one-minute range over b−65 … b−6, is
      between 2 and 15;
    - the mean volume over b−5 … b−1, divided by the median volume over b−65 … b−6, is at least 2.
  - **Lens B:** the crossing bar's own range and volume (bar b, complete before entry at b+1) are at least 3× the
    prior 60 minutes' median, and the range is at most 15×.
  - The unconditional cell and the speed-tercile ladder are reported.
  - **The filter is applied identically to every control grid.**
- **Exit:**
  - 30 minutes after the fill, at P(t + 30);
  - or EARLIER on a re-cross: a one-minute close back through L by 1 tick, exiting at the next bar's open.
  - No profit target.
  - Reported: 15, 60 and 120 minutes, and the next day's close (Osler's reversal), for the decay profile only.

## 4. Controls and nulls

1. **The half-round grid (primary control):** identical in everything but roundness. Its statistic is the treatment
   minus the control, per trade.
2. **The exact offset enumeration (SE 0):** the whole construction on the grid shifted by every offset.
   - M6E: o = 0 … 49 pips. MBT: o = \$0 … \$990 in \$10 steps. MGC: \$0.1 steps.
   - The round grid's rank is taken among the offsets OUTSIDE the stop band. p50 and p95 are reported.
   - **The predicted profile, reported:** a peak at 0, decay by the band's edge, flat in between, and bumps at x0
     above x5 (M6E).
3. **Fingerprints (signed predictions, reported):**
   - continuation excess at 50s ≥ at 00s, and bounce excess at 00s ≥ at 50s;
   - Asia ≥ London;
   - NY pm ≥ NY am.
4. **Within speed terciles,** treatment against control, so a volatility gate cannot pose as a level effect.

## 5. The premise gate (first, per cell, no P&L)

- **A touch** = the first bar in the window whose high comes within 1 tick of L from below (low within 1 tick from
  above), with close(b−1) at least 3 ticks away.
- **A bounce** = P(t + 15) back on the approach side.
- **The gate** is the bounce rate at round levels minus the half-round grid's (Osler: +1.5 to +4.5 points):
  - **PASS** at ≥ 2 percentage points;
  - **FAIL** below 1 point with SE < 0.5;
  - otherwise UNRESOLVED.

## 6. Readings (declared now, per cell, in this order)

| reading | condition |
|---|---|
| **MECHANISM ABSENT** | the gate FAILS. The line closes for that instrument; the P&L is reported, not read |
| **NO PROFILE** (the D725 analogue) | the gate is not FAIL, but the round grid's Lens A s = 2 mean signed gross ranks below 0.95 among the eligible offsets, or does not exceed the half-round grid's |
| **SIZE FAILURE** | profile present, but the fast cell's mean \|move\| over the hold is below 2 × the bar (\$17.52 M6E, \$17.24 MBT). The component line is written anyway |
| **CASCADE** | the profile is present (rank ≥ 0.95, above the half-round grid) **and** the Lens A s = 2 mean NET > 0 at t ≥ 2, Holm-adjusted over the two primary cells (M6E-Asia, MBT-Asia) **and** net positive without its best two years |
| **NOTHING** | otherwise |

- **GO** = CASCADE, which starts a Stage 1 design conversation with the principal (a forward or vault slice). It
  admits nothing.
- **MGC, London, NY, Lens B, the futures-round grid and the 00/50 split are reported, in no reading.**

**Reported, all four groups (per primary cell):**
- gross and net at each slippage step; Sharpe and Sortino; max drawdown; the mean move against 2c; the breakeven cost;
- count, mean, median, win rate, payoff, skew, kurtosis, the symmetric trims, and the largest trades named;
- years, eras (MBT's listing; 6E 2010–14 against 2015–23, when the basis changed sign), sessions, 00 against 50,
  and the speed terciles;
- the offset profile with its p50 and p95, and the half-round control;
- **the component line:** net Sharpe, hit rate, skew, gross beside net, and the daily ρ with D737's twin, NQ F2 and
  C1 over their span.

## 7. Runner assertions

- **Lag:**
  - the events are re-derived from close(b−1) by a second implementation that never calls the detector;
  - Lens A's filter reads only bars before b (a canary that includes bar b must change the selected set);
  - the basis uses only the prior session.
- **Sign, in money:** an up-cross that keeps rising pays the long and a down-cross the short; the audit raises on a
  mirrored book.
- **Right quantity:**
  - Lens A ≠ Lens B on a known synthetic event;
  - the half-round grid ≠ the round grid;
  - no event is counted on two grids at the same offset;
  - the events read equal the events used plus those excluded (roll week, missing bars).
- **The seal:** no kept row is dated on or after 2024-01-01.
- **The clock:** zoneinfo against the statutory US rule on every bar.
- **Speed:** the offset enumeration fans out over processes, and the self-test proves that chunked equals whole.

## 8. Output

- the 6E and GC extraction (cache in `temp/`; any derived fixture a record quotes goes in `data/`);
- `scripts/stage0_d761_round_number_cascades.py`;
- `data/stage0_d761_round_number_cascades.json` (statistics only).
- The result is a separate record.
