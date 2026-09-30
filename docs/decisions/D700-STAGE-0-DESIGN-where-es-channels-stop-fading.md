# D700 STAGE 0 DESIGN — the premise check for the principal's trend detector: after D480's hand-cell channel spans 10 bars with a minimum slope, does ES continue or fade, and on which clock (1, 5 or 15 minutes)?

*2026-09-30. Committed before the runner exists (R8). The runner will be
`scripts/stage0_d700_channel_clock_profile.py`, committed separately before its one run.*
- **What it is:** in-sample, 2016-01-05 → 2023-12-29, on data D688–D699 have already read. Nothing dated 2024-01-01
  or later is read. No slice is spent.
- **What it is not:** it trades nothing, fits no filter, and admits nothing. It is a premise check: it decides whether
  a channel-based trend detector is worth a construction, and on which clock.

## Why

After D699, the principal proposed a trend detector: "If we have stable channels for 10 bars in the one minute time
frame and they have a some minimum slope? We did the trendline study before, reuse that machinary."

**The record argued against the 1-minute clock:**
- **The slope dial has inverted before.** The channel study's five causal cells (D476–D481) all sat below their
  rotation nulls. In D477 a minimum-slope floor made the real-time result worse every time.
- **Fast ES moves fade:**
  - 15-minute bursts fade on short-gamma days (D697);
  - aggressively bought hours fade (D695);
  - D699's continuation lives at the hours-long horizon.

The principal questioned a 2.5-hour confirmation (ten 15-minute bars) as too slow.

**The agreed design (the principal: "Ok lets go with your proposal"):**
- **The primary:** 10 bars of 5 minutes, which confirms in about 50 minutes.
- **The profile:** first, measure where fading turns into continuation across 1, 5 and 15 minutes, against the
  time-matched drift, on short- and long-gamma days.

The daily channel line (D483) was closed on the daily equity panel. This is a different panel (ES intraday, gated by
dealer gamma) and the principal's own proposal. The closure's lesson is carried as the slope sweep below.

## The construction (reused, not re-dialled)

**The line machinery:** D480's hand cell (`CELL_HAND` in `scripts/d480_hand_cell.py`), unchanged. It is the
construction that reproduces the principal's own hand-drawn lines best (sign 92/87%).
- **Pivots:** D399's tie-tolerant pivots (`pivots_tie_tolerant`) at k = 1.
- **The lines:** `recalc_pair` with the hand cell's every setting. The margin is 0, because it only shifts a drawn
  level and nothing here reads the level.
- **The dials:** the bar-count dials (k 1, carry 7, stale window 25, reach 130, min pivots 2) are unit-free and
  carried as they are.

**The percent dials are restated by rescaling the bars, not the dials.** The hand cell's percent dials (height 20%,
break 3%, stale 12%, fit tolerance 16%, the trend floor DELTA 0.001 a bar) were set on daily names whose median
per-bar σ was **σ_ref = 0.0205**. That was measured on the twelve hand-drawn windows of D478, whose per-window σ ran
0.0104–0.0386.
- **The scaling:** each ES bar is rescaled so its per-bar σ is σ_ref. Every percent dial then means what it meant on
  the hand-drawn names, in σ units:
  - the height deadband is 8.9σ;
  - the break is 1.4σ;
  - DELTA is 0.049σ a bar.
- **How it works:** within each session, the clock's bar log-returns are multiplied by s_d = σ_ref / σ̂_c,d.
  - σ̂_c,d is the sd of that clock's within-session bar returns over the 20 sessions before d, prior-only and fixed
    for day d.
  - Open, high, low and close are each rescaled relative to the previous bar's close. For the first bar of a session,
    they are rescaled relative to the session's open.

**The series is spliced like D699's MACD.** The overnight gap is dropped: a session's first open continues from the
previous session's last close. The channel state carries across sessions, so the morning is never blind.

**The clocks.** ES front-month 1-minute day-session bars (D688's, with highs and lows), aggregated within the session
into 1-, 5- and 15-minute bars: 390, 78 and 26 a session.
- A bucket with no trade is a flat bar at the previous close.
- The series starts 2015-10-01, and normalisation starts at the 21st session.

## The detection event (the principal's "stable channel for 10 bars with a minimum slope")

At each bar close t, in direction D (+1 up, −1 down), a CHANNEL holds when all three conditions do:
- **Both lines are drawn** at t: support and resistance.
- **Both slopes clear the floor:** D·g_support ≥ f·σ_ref and D·g_resistance ≥ f·σ_ref. The slope g is in log units a
  bar on the rescaled series, so f is in σ a bar.
- **Both lines span at least 10 bars:** each side's segment anchor is at or before t − 9. The channel on the chart at
  t describes the last 10 bars or more.

**The event** is the first bar close at which the channel holds, after a bar at which it did not.
- **Fill:** one minute after the deciding bar's close, at the close of the next 1-minute bar.
- **Allowed:** events whose deciding close is from the first bar close to 15:45.
- **Repeats:** a day can hold several events.

**The declared floor is f = 0.1σ a bar,** twice the hand cell's own trend floor (DELTA = 0.049σ). Over the 10-bar
span, that is a rise of at least 1σ. Also declared:
- **The slope sweep** f ∈ {0.05, 0.1, 0.2, 0.4}, reported so that an inversion like D477's shows;
- **a stricter reading of "stable"** (a secondary): the channel must have held at every one of the last 10 bar
  closes, not only span them.

## The measurement

**For each event:** the signed forward move in MES dollars, D × (P(fill + h) − P(fill)) × $5, at h = 15, 30 and 60
minutes and at 16:00.
- **Horizons:** a horizon is scored only for events whose fill + h is at or before 16:00, so no horizon is clipped.
- **Cost:** none; this is gross. The $4.42 round trip is shown beside it.
- **The time-matched drift control:** for each event, D × the mean over every tradable day of the same gamma class of
  (P(fill + h) − P(fill)) × $5.
- **The excess:** the event's move minus its control, with a t clustered by day (events on one day are not
  independent).
- **Gamma class:** G_SUM < 0 (short) or ≥ 0 (long), from D688's panel, reproduced bit for bit first.

**Declared outputs:**
- **The profile:** clock × horizon × gamma class, at f = 0.1 on the primary definition. For each cell: the event
  count and events a day, the mean and median signed gross, the drift control, the mean excess and its clustered t,
  and the hit rate.
- **The timing null (the primary cell's gate),** per clock, on short-gamma days at +60 minutes.
  - Each day receives the event schedule (fill minutes and directions) of another short-gamma day, k = 10 … n − 10,
    enumerated so the p95's SE is zero.
  - The statistic is the mean signed gross, with p05, p50, p95 and the percentile.
  - The reading is two-sided, because a fade matters as much as a continuation.
- **The slope sweep and the strict "stable" reading,** at +60 minutes on both gamma classes.
- **Up against down, and events by hour,** for the primary clock.
- **Channel coverage:** the share of bar closes with a channel held, per clock. On a random walk the hand cell draws
  both lines about half the time, so coverage alone is not evidence.

## Runner assertions

- **Lag audit (a truncation rebuild):** at 30 sampled bar closes per clock (events and non-events), the bars are cut
  at t. The rescaling, pivots and lines are then rebuilt on the cut, and the channel state at t must equal the full
  run's. It must RAISE on a broken book: a detection read one bar ahead.
- **Prior-only rescaling:** σ̂ is recomputed for sampled days directly from the raw bars of the 20 previous sessions.
- **Sign audit, in money:** an up event on a rising path pays positively; a down event pays the opposite.
- **Right quantity:**
  - the rescaled bar returns' sd is within 15% of σ_ref in-sample, so the rescaling was applied;
  - the rescaled series differs from the raw one;
  - the spliced series differs from the gapped one.
- **D688 reproduced; window guard** (no row dated 2024-01-01 or later).
- **Self-test:** on a synthetic random walk, every clock's +60-minute excess sits inside ±2 clustered SE.

## The declared reading

**On each clock, short-gamma days, +60 minutes, f = 0.1:**
- **CONTINUES:** mean excess over the drift control with clustered t ≥ +2, and the signed gross above the timing
  null's p95.
- **FADES:** clustered t ≤ −2, and the signed gross below the timing null's p05.
- **NEITHER:** anything else.

**What follows from it (a proposal, for the principal):**
- **A construction is worth building** only on a clock that CONTINUES on short-gamma days, and by more than on
  long-gamma days. That construction would be a D699-style book: V1's nulls, the drift control and the oracle first.
- **If no clock continues,** the channel is not a trend detector on ES at these clocks, and the proposal is to use it
  only as V1's exit, if at all.

No clock, floor or definition is chosen after the run for a construction without saying so. Any construction that
follows is its own design.
