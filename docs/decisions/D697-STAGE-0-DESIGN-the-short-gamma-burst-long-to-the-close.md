# D697 STAGE 0 DESIGN — the principal's move-triggered short-gamma long: a fast rise since the prior settlement, bought on 1 MES and held to the close

*2026-09-29. Committed with its runner (`scripts/stage0_d697_short_gamma_burst_long.py`), before the run.*
- **What it is:** in-sample, 2016-01-05 → 2023-12-29; nothing dated 2024-01-01 or later is read.
- **The filter:** none is fitted. The expected-profit filter is to be designed with the principal from this run.

## Why a new construction

The principal objected to the clock-grid construction of D689–D695 ("I don't like that construction, why is it limited
to those decision times?"). Its decision times (10:30 … 14:30) were inherited from D684's sizing grid, never chosen
for a mechanism. It missed 15:00–16:00, and it anchored "the last hour" to the clock rather than to the dealers' last
hedge.

## The principal's decisions (2026-09-29)

| question | the principal's choice |
|---|---|
| trigger | "Move-triggered" |
| the move | "measured since the prior settlement" (the dealers' last full hedge; D688's r) |
| exit | "hold to close (with room for conditional exits)" |
| threshold | "some sigma per bar, if it rises really quickly with a minimum of 0.25 sigma" |
| speed window | "Last 15 minutes" |
| speed bar | "≥ 1.5σ" |
| last entry | "15:00" |
| gap days | "Must cross after the open" |
| kept | "Short-gamma days only (G_SUM < 0)", "Long only", "1 MES on a filtered expectant profit, to be made later" |

## The construction

- **The day:** G_SUM < 0.
- **Checked each minute from 09:45 to 15:00:**
  - **level:** log P(t) − log S_prev ≥ 0.25 σ_d;
  - **speed:** the rise over the last 15 minutes is at least 1.5 × the normal 15-minute σ, from the prior 20 sessions'
    1-minute variance;
  - **crossing:** the level condition was false earlier in the session.
- **The trade:** at the first minute all three hold, buy 1 MES at P(t) and sell at 16:00. One trade a day, at
  $4.42 a round trip.
- **Declared outputs:**
  - the book, with the four groups and ρ with the MACD arm;
  - the oracle (net > 0) on its trades, the ceiling for the later filter;
  - **a time-matched drift control:** buying at the same minute on every short-gamma day, to address D689's drift
    caveat;
  - two controls not traded: the long trigger on long-gamma days, and the downward mirror on short-gamma days;
  - the enumerated day-rotation null of the short-gamma label;
  - **the path, for conditional exits:** the favourable and adverse excursions (MFE, MAE), the P&L at +15, +30, +60
    and +120 minutes, and when the trigger fires.
- **A trigger audit:** a loop re-derives 40 days, and the audit must fire on gap days when the crossing rule is
  dropped.

**The declared reading.** The construction has an edge worth filtering if:
- its mean net is above 0;
- it beats the drift control at NW t ≥ 2;
- it is above the p95 of its rotation null.

No parameter is tuned after the run.
