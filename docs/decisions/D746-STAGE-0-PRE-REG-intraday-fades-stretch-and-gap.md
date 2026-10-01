# D746 STAGE 0 PRE-REG — intraday mean reversion for the prop book: is there room to fade an extreme stretch (A) or an opening gap (B) on ES and YM at one micro?

*2026-10-01. The principal:*
> "Any brand new strategy Ideas? We have a continuation one, I would Ideally like to have a strategy per market regime,
> we don't have one for mean reverting markets do we?"
>
> "Prop book only personal book when we have some real capital"
>
> "Pre-reg D746 and run the A and B oracle".

- **What it is:** a premise check, oracle first. It sizes the prize of two intraday fades and chooses no rule. Filters
  and triggers are designed afterwards, with the principal, only where there is room.
- **The order (R8):** this record is committed before the runner exists, the runner before its one run, and the result
  separately.
- **Why these two:**
  - The ordinary intraday fade on the index day session is real but grosses cents: D684's long-gamma fade made
    $0.2–0.3 a MES trade at 5–60 minutes against an $8.84 bar. NQ respects no intraday mean (D724).
  - So a prop reversion line must live where moves are large: rare stretches (A) and opening gaps (B).
  - **A's mechanism:** dealers long gamma sell rallies and buy dips. D683 found that on long-gamma days, realised
    variance runs at ×0.48 of short-gamma days and 5-minute reversion deepens. YM's move reverses in the morning (D727)
    and ES's first half hour reverses into the last (D487).
  - **B's mechanism:** D724 found yesterday's close is touched more often than equidistant mirror levels (t 4.7), and
    D725 found crossings of it do not continue. A level the price is drawn to and stalls at is a fade-to-target object.
- **Instruments:** ES and YM only. NQ continues from the open at every clock (D727); it is excluded.
- **The prior** (before any run): about 20% that either setup shows ROOM, and under 10% that one reaches GO. The
  likeliest outcome is that the stretch fade is real but small and the gap fade is drift.

## 0. Data, seal, conventions

- **Data:** ES and YM day session, one-minute OHLCV (`fut_{ES,YM}_rth_1m`), 2016-01-04 → 2023-12-29. The day panel is
  D727's `panel_from_raw` (≥ 380 bars, roll days excluded, σ_oc = the RMS of the prior 20 sessions' open-to-close
  move, in points). Highs, lows and volumes are pivoted on the same days.
- **The seal:** nothing dated 2024-01-01 or later is parsed. Every fixture, and SqueezeMetrics' `DIX.csv`, is
  restricted as TEXT to rows before 2024-01-01 before any value is read. ES 2024+ is D716's unseen span and YM 2024+
  D737's.
- **SqueezeMetrics:** the GEX row dated strictly before each session (D663's `gex_prior`). Output is statistics only;
  no per-date GEX or derived series is written or tracked.
- **Bars:** bar m starts at 09:30 + m. The price at minute m is the close of bar m − 1 (D727). An entry "at minute m"
  fills at bar m's open.
- **Size and cost:** one MES ($5 a point, tick 0.25 = $1.25) or one MYM ($0.50 a point, tick 1 = $0.50).
  - The round trip is $3 plus the d508_exec crossing: **MES $4.42, MYM $3.80**.
  - A stop fill carries one tick of slippage in price.
  - **The prize bar is 2 × cost: MES $8.84, MYM $7.60.**
- **Fills:**
  - A target fills only when a bar trades THROUGH it by at least one tick, at the target (or at the bar's open if the
    bar opens beyond it).
  - A stop fills when a bar reaches it, at the stop (or at the bar's open if beyond it), then one tick against.
  - A bar that reaches both counts as stopped.
  - Bars are checked from the entry bar onward, and the exit at 15:59 is that bar's close.

## 1. The setups

**A, the stretch fade:**
- z_m = (P_m − O) / (σ_oc · √(m/390)), D727's normalised move from the open.
- **Trigger:** the first minute m0 in 10:00–14:30 (m 30–300) with |z_m0| ≥ k, k ∈ {2.0, 2.5, 3.0}. One trade a day
  per k.
- **Side:** F = −sign(z_m0), against the move.
- **Entry:** bar m0's open.
- **Target:** the session VWAP at entry, from bars 09:30 → m0 − 1, with typical price (H + L + C)/3 weighted by
  volume. It is fixed at entry. A trigger whose VWAP is not at least 2 ticks on the favourable side is skipped and
  counted.
- **Stop:** 1:1, the target's distance beyond the entry.
- **E1 (primary):** the target, the stop, or the 15:59 close. A 1:1 bracket makes P(target first) = ½ the no-reversion
  value, so E1's gross is the reversion itself.

**B, the gap fade:**
- g = O − C_prev, where C_prev is the prior panel session's 15:59 close on the same contract. A day after a roll, or
  with no prior session in the panel, is skipped.
- **Trigger:** |g| ≥ g_min · σ_oc, with g_min ∈ {0.25, 0.5, 1.0}.
- **Side:** F = −sign(g), towards yesterday's close.
- **Entry:** the 09:30 open (O).
- **Target:** C_prev.
- **Stop:** 1:1, O + sign(g)·|g|.
- **E1 (primary):** the target, the stop, or the 15:59 close.

**Reported exits for both:** E2, held to the 15:59 close with no target and no stop; E3, the target with no stop,
else the close.

**The cells:** 2 roots × 3 thresholds per setup, 12 in all. **The primary cells are A at k = 2.5 and B at
g_min = 0.5, each on ES and on YM.**

## 2. Controls and nulls

- **C2, the timing null (primary, enumerated over every rotation offset, SE 0):**
  - For each offset j = 20 … n − 20, every trade's entry minute and its target and stop distances (in σ_oc units)
    move to day d + j (mod n).
  - There the same bracket is entered at the same minute, against that day's OWN move: −sign(z) at that minute for A,
    −sign(g) for B.
  - **The statistic** is the mean E1 gross per trade.
  - The question it answers: does fading at the selected stretch or gap beat fading the same-sized bracket at the same
    clock on an arbitrary day?
  - Each cell's p is its share of offsets at or above the cell.
  - **Holm over the 12 cells.**
- **The mirror:** the primary cells entered WITH the move (−F), the same bracket mirrored. It is the sign audit in
  money and should be about −E1 before cost.
- **By dealer gamma (A's mechanism test):** E1's gross on short-gamma days (GEX < 0), long-gamma days below and above
  the walk-forward median of the prior 250 sessions' GEX, and days with no GEX row.
  - The declared contrast is long-gamma-high minus short-gamma, with Welch t.
  - **GAMMA SUPPORTS A** when that contrast is > 0 at t ≥ 2 in the primary cell.

## 3. Oracles (computed first; they can kill the idea)

On each cell's E1 trades, at one micro:
- **O1, the ceiling:** the oracle filter (`filter_oracle.oracle_take`, net > 0), with its mean net per trade, total and
  share of trades.
- **O2, the accuracy a filter needs:** `partial_oracle_curve` with the target = net, q = 0.5 (keep the better half),
  ρ ∈ {0, 0.025, 0.05, 0.075, 0.10, 0.15, 0.20, 0.30}, 500 draws, seed 746.
  - It reports the kept half's mean net at each ρ, and the smallest ρ at which it is ≥ 0 and at which it is ≥ 2 × cost.
  - D690's real filters reached ρ ≈ 0.04–0.06, so **ρ = 0.05 is the realistic filter**.
- **O3, the size of the move at stake:** the median target distance in dollars (A: |VWAP − entry|; B: |g|) against
  2 × cost. A bracket whose median target is under 2 × cost cannot pay however often it wins.

## 4. Readings (declared now; per cell, read on the primary cells)

| reading | condition |
|---|---|
| **NO ROOM** | the unfiltered E1 mean gross < 2 × cost **and** O2's kept half at ρ = 0.05 has mean net ≤ 0. Recorded first, whatever follows |
| **REVERSION** | E1 mean gross > 0 at a NW t ≥ 2 (trades in day order, 5 lags) **and** above C2's p95 |
| **DRIFT / NOTHING** | otherwise |

- **ROOM** is the complement of NO ROOM.
- **GO to a filter and rule design with the principal** requires all of:
  - REVERSION and ROOM in the primary cell;
  - its Holm-adjusted p ≤ 0.05;
  - a net Sharpe ≥ 0.4 at one micro, unfiltered or at O2's ρ = 0.05 kept half;
  - ≥ 5 of 8 years positive;
  - the largest year's share < 50%.
- GO starts the design conversation; it admits nothing.

**Reported for every cell (all four groups):**
- net and gross, Sharpe and Sortino, max drawdown, exposure (minutes held), the mean move per trade against 2c, and
  the breakeven cost;
- trades, mean, median, win rate, payoff, skew, kurtosis, and the symmetric 1% trims (ex-top, ex-bottom, trimmed);
- the years, the largest year's share, the split by entry hour, and A's |z| bins / B's |g| bins;
- C2's p50 and p95 beside the score.
- **The component line:** net Sharpe at one micro, hit rate, skew, gross beside net, and the daily-P&L correlation
  with D737's in-sample twin (D735's YM k1.0 1σ_rem cell) and NQ F2 (D711's in-sample book).

## 5. Runner assertions

- **Lag audit:** a second implementation from the raw rows re-derives z at the trigger minute, the VWAP at entry, and
  B's C_prev, on a sample of trades. It reads only bars that start before the entry, and its canary reads the entry
  bar.
- **Sign audit in money:** a synthetic day where price falls to the target pays +; one that rises to the stop pays −
  (cost and slippage included).
- **Right quantity:** E1 differs from E2 on the same trades.
- **The self-test must fail on a broken book:** a deliberately shifted trigger (reading bar m0) raises the lag audit.

## 6. Output

- `scripts/stage0_d746_intraday_fades.py` (the runner) and `data/stage0_d746_intraday_fades.json` (statistics only).
- The result is a separate record.
