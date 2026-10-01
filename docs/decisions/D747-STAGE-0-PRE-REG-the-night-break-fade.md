# D747 STAGE 0 PRE-REG — the night-break fade: does a break of yesterday's range ± 0.25 ATR20 between 03:00 and 08:29 ET fall back to yesterday's extreme, on ES (never read) and on NQ's unread 2016–17?

*2026-10-01. The principal: "Close D746 and pre-reg C as D747" (C: NQ's night-break fade, the prop-book reversion
candidate left after D746).*
- **The order (R8):** this record is committed before the runner exists, the runner before its one run, and the result
  separately.
- **The prop book's rules:** one micro, entries 03:00–08:29 ET, flat at the 09:29 close, so nothing is held past the
  session.

## 0. What is already known, and why the test sits on unread data

- **The motivation is POST HOC.** D744's ungated book U was NQ's fresh crossing of yesterday's RTH high + 0.25 ATR20
  (or low − 0.25 ATR20) between 03:00 and 08:29.
  - It entered on a stop at the level, with the initial stop back at yesterday's extreme and a 0.25 ATR20 trail, flat
    at 09:29.
  - Over 298 trades (2018-01-09 → 2023-12-29) it lost −4.48 bp gross (HAC t −2.08; −$10.33 a MNQ): night breaks
    tend to fall back.
  - That slice is READ, so it cannot test the fade.
- **The decision is therefore taken only on data D744 never scored:**
  - **ES, 2016-01-04 → 2023-12-29:** D744 read NQ only. K7 / D470–D473 read ES's 18:00 → 09:00 overnight HOLD, a
    different object; no ES night break of yesterday's range has been scored.
  - **NQ, 2016-01-04 → 2018-01-08:** these sessions fell in D744's tier burn-in, and no U trade was scored on them.
- **NQ 2018-01-09 → 2023-12-29** is run and reported as the post hoc slice. It never enters the decision.
- **D746 (same day)** found no intraday reversion on ES or YM's day session: stretches and gaps do not come back. The
  night is a different clock, with a thinner book, where a fall-back to a level is plausible as liquidity provision.
  That is the only reason to expect a difference.
- **The prior** (before any run): about 15% SUPPORTED. The fade is the mirror of a −4.5 bp effect on NQ, against a night
  cost of about 2.3 bp on NQ and more on MES. Transfer to ES is the main uncertainty.

## 1. Data, chain, seal

- **The chain is D744's loader, unchanged:** `M.load_bars` under D720's `lowered_cut`, with D680's CUT held at
  2024-01-01, for ES and NQ.
  - Disclosed: the loader parses the fixture and drops rows at or after the cut (D735-A1's accepted practice). No
    statistic reads a dropped row, and `Z.no_session_after` asserts it.
  - Sessions are D663's `root_frame` per root: usable sessions, with prior_high, prior_low, prior_close and atr20
    known before the session.
- **Bars:** each session's Globex 1-minute bars from 03:00 to 09:29 (D744's `night_arrays`).
- **The seal:** nothing dated 2024-01-01 or later is read (ES 2024+ is D716's unseen span, NQ 2024+ D716's and
  D737's). The vault is untouched.
- **Cost** (D744's night line): \$3 + 1.5 × the d508_exec crossing ticks × the tick's dollars.
  - **MNQ \$4.60, MES \$5.13.** The prize bar is 2 × cost: \$9.20 and \$10.25.
  - The day line (1.0 ×) is reported beside it.
- **Size:** one MNQ (\$2 a point) or one MES (\$5 a point).

## 2. The construction

- **Levels:** up = Lh + 0.25 A and dn = Ll − 0.25 A (D744's), where Lh and Ll are yesterday's RTH high and low and A is
  ATR20.
- **A candidate session:** it has a 03:00 bar, and that bar's open is strictly inside (dn, up) (D744's condition).
- **The entry:** resting limits from 03:00 to 08:29.
  - A SELL limit at up fills on the first bar whose high ≥ up + 1 tick, at up (or at the bar's open if it opens above
    up).
  - A BUY limit at dn fills symmetrically.
  - The first fill is the trade, one a session.
  - A bar that would fill both sides is skipped and counted.
- **The exit, a 1:1 bracket anchored at the level,** for b ∈ {0.10, 0.25, 0.50} × A:
  - for the sell, the target is up − bA and the stop is up + bA; for the buy, mirrored;
  - each is rounded to the nearest tick.
  - **The primary is b = 0.25:** the target is then yesterday's extreme itself, the level D744's longs fell back to.
- **Fills and checks:**
  - On the fill bar only the stop is checked. From the next bar, the target and the stop are both checked.
  - The target fills only when a bar trades through it by one tick, at the target (or at the bar's open if it opens
    beyond).
  - The stop fills at the stop (or the open if beyond), plus one tick against.
  - A bar reaching both is stopped. If neither is hit, the exit is the 09:29 bar's close.
- **Reported exits:**
  - E2: no target and no stop, flat at 09:29;
  - the mirror: the same bracket entered WITH the break, as a sign audit.

## 3. Cells, decision slices, nulls

- **The cells:**
  - **ES-full:** ES, 2016–2023;
  - **NQ-early:** NQ, 2016-01-04 → 2018-01-08;
  - **NQ-late (post hoc):** NQ, 2018-01-09 → 2023-12-29.
  - Each at b ∈ {0.10, 0.25, 0.50}. **The primary cells are ES-full b 0.25, then NQ-early b 0.25.**
- **C2, the timing null (enumerated, SE 0):**
  - For each offset j = 20 … n − 20 within the cell's own sessions, every trade's fill minute and bracket (in A
    units) move to session d + j.
  - There it is entered at that minute's bar open, against that session's own move since the 03:00 open, with the same
    bracket checks.
  - The statistic is the mean gross per trade.
  - The question it answers: does fading a break of yesterday's range beat fading the night's move at the same clock
    on an arbitrary night?
- **The oracles (as D746):**
  - O1, the oracle ceiling;
  - O2, the partial-oracle curve (q 0.5, ρ ∈ {0, 0.025, 0.05, 0.075, 0.10, 0.15, 0.20, 0.30}, 500 draws, seed 747);
  - O3, the median target in dollars against 2 × cost.

## 4. The decision rule (declared now)

**SUPPORTED** iff all of these hold:
1. **ES-full b 0.25:**
   - it has ≥ 100 trades;
   - its mean gross > 0 at a NW t ≥ 2 (trades in date order, 5 lags);
   - its mean gross is above C2's p95;
   - its mean net > 0 at the night cost.
2. **NQ-early b 0.25:** mean gross > 0 (the same sign; it is too short for significance, at about 2 years).
3. **ES-full's standard:**
   - net positive in ≥ 5 of its 8 years;
   - its largest year < 50% of the total;
   - net still positive without its two best years (D736's EARNS test).

**LEAD** if ES-full b 0.25 has mean gross > 0 at t ≥ 1.28 and net > 0 but another condition fails, or if NQ-early b 0.25
alone meets condition 1's t and C2 bars.

**NO ROOM** (recorded first, as in D746): ES-full b 0.25's gross < 2 × cost **and** its kept half at ρ 0.05 has mean
net ≤ 0.

**NOT SUPPORTED** otherwise.

SUPPORTED or LEAD opens the confirmation question (the forward recorder's Globex bars for NQ and ES from 2026-09-22,
or a vault slot on the principal's explicit word). It admits nothing.

## 5. Assertions (each canary must raise)

1. **Known answer:** D744's own `night_break` and `night_exit` on NQ's sessions with a finite D744 ctier
   (2018-01-09 → 2023-12-29) reproduce U exactly: 298 trades and gross −4.475559322876281 bp (1e-9).
2. **Lag:**
   - the candidate test reads only the 03:00 bar's open;
   - the levels use only prior sessions (prior_high, prior_low and atr20 re-derived from the previous rows on a
     sample);
   - a canary using the same day's high must raise.
3. **Second implementation:** every fade trade is re-derived by an independent bar loop. Fill bar, side, fill price and
   exit price must agree exactly. A canary flat at 09:28 must disagree on some trades.
4. **Sign, in money:** a hand-built night where a sold break falls to its target pays +, and one that rises to the stop
   pays −.
5. **Right quantity:** E1 ≠ E2; the 03:00-inside condition binds; the night cost exceeds the day cost.

## 6. The report (all four groups, per cell)

- **Performance, net and gross:** Sharpe and Sortino, max drawdown, exposure (sessions traded, minutes held), the mean
  move against 2c, and the breakeven cost.
- **Trade distribution:** count, mean, median, win rate, payoff, skew, kurtosis, the three 1% trims, the exit mix, and
  the fill hour.
- **What it depends on:** years, without the two best years, sell against buy, and the top trade named.
- **Nulls:** C2's p50 and p95 beside the score.
- **The component line:** net Sharpe at one micro, hit rate, skew, gross beside net, and the daily-P&L correlation with
  D737's in-sample twin, NQ F2 and C1. C1 trades from 09:30, so the clocks do not overlap.

## 7. Predictions (checkable)

- **Opus:** P(SUPPORTED) ≈ 0.15, P(LEAD) ≈ 0.15.
  - NQ-early will be positive (the effect is NQ's).
  - ES-full's gross will be positive but under 2 × cost, given D746's ES day-session result and MES's higher night
    cost.

## 8. Output

`scripts/stage0_d747_night_break_fade.py` and `data/stage0_d747_night_break_fade.json` (statistics only).
