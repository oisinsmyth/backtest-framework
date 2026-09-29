# D699 STAGE 0 DESIGN — the principal's log MACD on short-gamma days: a normalised 15-minute log MACD (12/26/9, gaps spliced out), long on 1 MES, in three variants (the histogram, its rate of change, and the two OR'd), each with hysteresis

*2026-09-30. Committed before the runner exists (R8). The runner will be
`scripts/stage0_d699_gamma_macd_long.py`, committed separately before its one run.*
- **What it is:** in-sample, 2016-01-05 → 2023-12-29. Nothing dated 2024-01-01 or later is read. No slice is spent.
- **The filter:** none is fitted. As in D697, the expected-profit filter is designed with the principal from this run,
  against the oracle it reports first.

## Why, and the reopen

The principal asked about momentum under short dealer gamma (2026-09-30). The mechanism: a dealer who is short gamma
buys as price rises and sells as it falls, at the re-hedging horizon (hours), so on those days a move should carry.
D697 found that a 15-minute burst fades, so the continuation, if it exists, is slower than a burst. A smoothed trend
signal at the re-hedging horizon is the natural next object. The principal proposed:

> "Ok lets use a log MACD -> its scale and unit invariant, and we go off the hourly standard parameters. I would like
> it to ignore gaps/ smooth them, and the basicly the trade signal becomes if the rate of change of the histogram >
> than some threshhold or the histogram is > 0."

D675 §10 closed "any MACD variant or re-parameterisation" under R15. **The principal reopened it for this use on
2026-09-30** ("Reopen it"). That is recorded as an addendum to D675. The reopen is narrow: a MACD gated by dealer
gamma, on ES, on the day session. D675's lines stay closed as it left them: D484's signal as a line, and any Stage 2
built on a §3 clock cell.

**What is new against D675:**
- **The gamma gate.** D675 never conditioned on dealer gamma.
- **The spliced series.** Removing the overnight gap removes the overnight reversal component D675 found on six of
  eight roots.

## The principal's decisions (2026-09-30)

| question | the principal's choice |
|---|---|
| reopen | "Reopen it" |
| bars | "15-minute bars" (the standard 12/26/9; hourly 12/26/9 on day-session bars spans 2–4 sessions, too slow for a daily gamma regime) |
| signal | "three variants, each signal variant plus the combine OR'd" |
| hysteresis | "Add hysteresis" |
| threshold and normalisation | "you pick the threshold and normalise the log MACD" |
| kept from D697 | short-gamma days only (G_SUM < 0); long only; 1 MES at $4.42 a round trip; the bar is net > 0; flat at 16:00 |

## The construction

**The day.** G_SUM < 0: SqueezeMetrics SPX GEX plus the ES options book at the prior settlement, known before the
open (D688's panel, D688 reproduced bit for bit first).

**The spliced series.** ES front-month 1-minute day-session bars (D688's), sampled every 15 minutes at 09:45, 10:00,
…, 16:00: 26 bar closes a session.
- x is the running sum of within-session 15-minute log returns, from 2015-10-01 (the warm-up) onward.
- The first return of a session is log(P 09:45 / P open). The overnight gap, log(P open / P prior 16:00), is dropped.
- Sessions with fewer than 380 bars are not in the series. They are skipped like the gap.
- **Scale and unit invariance:** x is a log price, so the MACD is in log units and does not depend on the price level.

**The log MACD** on x: M = EMA12(x) − EMA26(x), the signal line EMA9(M), the histogram H = M − EMA9(M), with
α = 2 / (n + 1). The EMAs run continuously across sessions on the spliced series.

**The normalisation (my choice, declared here).** H is a fixed linear filter of the past returns: H_t = Σ_k w_k r_{t−k}.
Under a random walk with bar volatility σ, its standard deviation is σ ‖w‖.
- **The standardised histogram:** z_H = H / (σ̂_15 ‖w‖), where ‖w‖ = 0.3379 for 12/26/9.
- **The standardised rate of change:** z_R = ΔH / (σ̂_15 ‖Δw‖), where ΔH is the change in H over one 15-minute bar and
  ‖Δw‖ = 0.0867.
- **σ̂_15** is the standard deviation of the spliced 15-minute returns over the 20 sessions before d (520 returns),
  prior-only. It is fixed for the whole of day d.
- **Result:** both z are unit-free and volatility-free, with standard deviation 1 under a random walk. A simulation of
  4,000 random-walk sessions gave 0.99 and 1.00.

**The three variants.** Each is a long state with hysteresis, run separately on each short-gamma day and started
flat.

| variant | enter long when | exit when |
|---|---|---|
| **V1 HIST** | z_H > +0.5 | z_H < −0.5 |
| **V2 ROC** | z_R > +1.0 | z_R < −1.0 |
| **V3 OR** | V1's state or V2's state is long (each run as its own machine) | both are flat |

**The thresholds (my choice, declared here, from the random-walk simulation, with no market data read):**
- **V1, h = 0.5:** under a random walk it gives 0.91 trades a day, held 12.7 bars (about 3.2 hours) on average. Without
  hysteresis (h = 0) it gives 1.45 trades a day held 8.6 bars.
- **V2, k = 1.0:** it gives 1.32 trades a day, held 8.4 bars (about 2.1 hours).
- **The criterion:** about one round trip a day, held for two to three hours, the re-hedging horizon.
  - D692 measured the hourly gross on short-gamma days at about one MES round trip an hour. A book that turns over
    every bar cannot pay its fee.
  - The band is wide enough to cut the no-hysteresis churn by roughly a third, and no wider.

**Timing.**
- **Decisions** are taken at each 15-minute bar close, from 09:45 to 16:00.
- **Entries** are allowed at the closes from 09:45 to 15:45.
- **Fills** are at the price one minute after the deciding close: the close of the next 1-minute bar. This is one
  minute more conservative than D697.
- **Forced flat** at 16:00, at the close of the 15:59 bar.
- **Cost:** $4.42 a round trip on 1 MES, charged on every trade. A day can hold several trades.

**The short mirror** (enter below −0.5 or −1.0, exit above +0.5 or +1.0) is reported beside the primary, not traded.

## Declared outputs

1. **The oracle first,** for each variant: the share of trades net > 0, their mean net, the oracle book's net Sharpe
   and trades a year. That is the ceiling for any later filter.
2. **The book for each variant,** with CLAUDE.md's four groups:
   - **Performance:** trades a year, exposure (the share of session time held), daily net and gross Sharpe and
     Sortino, mean net and gross per trade, the NW t of the mean net, the breakeven round trip, the maximum drawdown.
   - **The trade distribution:** mean, median, hit rate, payoff, skew and kurtosis, the mean hold, and the trimmed
     means (ex-top, ex-bottom, both).
   - **Dependencies:** by year, without Feb–Apr 2020, the top five trades, and the entries by hour.
   - **ρ with the admitted MACD arm** (daily net). It is a MACD, so the overlap is reported, not assumed.
3. **The time-matched drift control:** for each trade, the mean gross of holding over the same clock interval
   (entry fill minute to exit fill minute) on every short-gamma day. The trade's excess over it is the MACD's timing
   information beyond the short-gamma day's drift (D697 §3). The mean excess is reported with its NW t.
4. **The timing null (the gate):** the day-rotation of the position SCHEDULE among short-gamma days.
   - Day i receives the entry and exit minutes that day i + k's MACD produced, applied to day i's prices.
   - This keeps each variant's turnover, holding lengths and time-of-day profile, and breaks only the link between the
     MACD and the day's own path. It randomises the partner, not the membership.
   - k is enumerated from 10 to n_short − 10, so the p95's SE is zero.
   - The statistic is the mean net per trade. It is reported per variant and as the FAMILY MAXIMUM over the three
     (the multiplicity control).
5. **The gamma-label null (reported, not a gate):** the rotation of the short-gamma label across all days (k = 10 …
   n − 10), applied to each variant's trades on every day. It asks whether short gamma matters to the MACD.
6. **Controls, not traded:** each variant on long-gamma days; the short mirror on short-gamma days; and the
   always-long control (buy at 09:46, hold to 16:00) on short-gamma and on long-gamma days.

## Runner assertions

- **Lag audit:** a second implementation recomputes the EMAs, the normalisation and the hysteresis on 40 sampled days
  with a plain Python loop over the spliced prices. It never calls the vectorised functions, and it must reproduce the
  trade list exactly. It must RAISE on a broken book: one whose decision at a close reads the next close.
- **Sign audit, in money:**
  - a long held across a rise pays positively, and the short mirror pays the opposite;
  - the fill is later than the deciding close, which is asserted on every trade.
- **Right quantity:**
  - the spliced MACD must differ from the one computed with the gaps left in;
  - ‖w‖ and ‖Δw‖ must match the impulse response recomputed from the EMA recursion.
- **Window:** no row dated 2024-01-01 or later survives the cut.

## The declared reading (in-sample, not a verdict)

A variant **has an edge worth filtering** if all three hold:
- **(a)** its mean net per trade is above 0;
- **(b)** its mean gross beats the time-matched drift control with NW t ≥ 2;
- **(c)** its mean net per trade is above the p95 of the family-maximum timing null.

No threshold, band or parameter is tuned after the run. Any follow-up that changes one is a new design.

**The limits:**
- **Unconfirmable:** as D689 found, 2024-01 → 2025-02 holds 66 short-gamma days (expected t about 1.1), so a pass
  here stays in-sample until a confirmation design is found.
- **Not the admitted arm:** the arm trades NQ on the hourly clock. This construction trades ES on 15-minute bars, on
  short-gamma days only, so it shares neither the instrument nor the clock. It shares the signal family. CLAUDE.md's
  rule ("a gated subset of C1 is C1") is answered by the ρ in output 2, not by argument.
