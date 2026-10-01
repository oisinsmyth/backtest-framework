# D744 STAGE 0 PRE-REGISTRATION — the consolidation break at the European open: NQ's first fresh crossing of yesterday's range between 03:00 and 08:29 ET, on compressed sessions, flat at 09:29

*2026-10-01.*
- *The principal: "Ok close that and look at idea 2" — idea 2 of the C1 mechanism comparison (an Opus analysis and
  an independent Fable 5.1 agent's; notes in `temp/c1_opus/`, `temp/c1_fable/`).*
- *Design choices, all the principal's:*
  - **the gate is C1's two halves rebuilt for a 03:00 clock**: rv5, plus the Asia session's two-way range;
  - **flat at 09:29**;
  - **MNQ only**;
  - execution is algorithmic: resting entry stops, a trailing stop and a timed flatten.
- *Numbered D744, the next free number in `docs/internal/AITODO.md`.*
- ***Committed alone, before its runner exists.** In-sample only (≤ 2023-12-29).*

## 0. Context and what is already known

**The idea** (Fable's, POST HOC).
- C1's mechanism is post-shock consolidation: recent ranges are well below a still-elevated ATR20, and a crossing of
  yesterday's extreme is then not reversed.
- The same balance may be crossed on the second information clock, the European session, before the US open prices
  it.
- D677 found that on the roots whose clock is foreign, the crossing the night already made is the one that works.

**Nothing on file tests this.** A read-only search (a Sonnet agent; the load-bearing points checked) found:
- every break study on ES/NQ enters from 09:30 (D666/D668/D672/D680/D682/D725);
- Globex bars have only been used as a pre-09:30 feature.

**The nearest relatives:**
- K7 / D470–D473, the 18:00 → 09:00 hold: REMOVED, and the 2024+ NQ/ES overnight-leg slice is read on both sides;
- D499, the hourly fade through Globex hours: CLOSED;
- D651, the session handoffs: no liquidity trough, CLOSED;
- an unverified forum "London Session" MNQ signal, rejected in `research/`;
- the cited Boyarchenko et al.: the 02:00–03:00 ET drift has been about zero since 2021.

**The premise check (counts only, no P&L; `temp/c1_idea2/premise.py`), sessions 2016–23:**
- **About 50 fresh crossings a year:** the price is inside yesterday's range ± 0.25 ATR20 at 03:00, then crosses it
  by 08:29.
- **About 9–14 % of sessions are already beyond the level at 03:00.** They are not fresh crossings, and this design
  skips them.
- **On the compressed third by rv5 alone: 96 fresh crossings, 12–15 a year.** The full gate below needs another
  250-session burn-in, so expect about 80 scored trades.
- **One third of those crossings come in the 03:00 hour.**

**This is a low-power design, stated as such.**

**Confirmation route (not decided here):**
- The forward recorder keeps only 09:30–16:00 bars. A forward test would need Globex bars recorded inside Sierra's
  roughly five-month download window.
- A vault slot needs the principal's explicit word.
- K7 has already read NQ's 2024+ overnight leg on both sides (about +\$25 a night), so any 2024+ read of this
  construction is partly informed.

## 1. The object

**Data:**
- NQ's Globex 1-minute bars (`fut_opening_globex_1m`, 18:00 → 16:59 ET per session), through D680's chain:
  `M.load_bars` under D720's `lowered_cut`, with D680's CUT held at 2024-01-01;
- **known answer first:** D672's C1 is reproduced through `V.book` and `V.known_answer` (DIX read for the t671
  window only; no GEX-derived series is written outside `temp/`);
- sessions are those of D663's `root_frame` (prior_high, prior_low, atr20, prior_close, all known before the session).

**A disclosed data filter:** `root_frame` keeps only sessions whose own RTH data are usable. That is an availability
filter that C1 shares, not a signal.

**The levels** are yesterday's RTH high and low ± 0.25 · ATR20: Lh + 0.25A for a long and Ll − 0.25A for a short.

**A candidate session:** the 03:00 bar's open is strictly inside (Ll − 0.25A, Lh + 0.25A). Otherwise the session is not
traded.

**The entry:** a stop at each level, live on the 03:00 → 08:29 bars. The first fill of the session, either side, is
the trade:
- the long is checked first within a bar, as in D666's `plain_break`;
- the fill is at the level, or at the bar's open if the bar opens through it;
- gross is measured at the level with no fill tick (C1's convention, D680's `gross`).

**The exit (E4):**
- an initial stop at L (the broken level itself);
- a trail 0.25A behind the best price, checked from the next bar on, never loosened;
- the fill at the stop, or at the bar's open if the bar opens through it;
- **flat at the close of the 09:29 bar.**

**The gate, every input known at 03:00:**
- rv5 = D671's `session_features` rv5: the mean RTH range ÷ ATR20 of the prior five sessions;
- **asia** = (the high − the low of the session's Globex bars from 18:00 to 02:59 − |the 02:59 bar's close − the prior
  RTH close|) ÷ ATR20. That is C1's two-way overnight range with the night cut at 02:59;
- p_rv, p_asia = D671's `tiers` (the walk-forward percentile among the previous 250 finite values);
- comp = (p_rv + p_asia) / 2, and ctier = `tiers(comp)`, exactly C1's construction;
- **trade iff ctier < 1/3.**

**Cost** (one MNQ):
- the night cost = \$3 + 1.5 × D680's crossing ticks × the tick's dollars. D651 measured NQ's night spread at
  1.41–1.54 × the core's;
- **reported beside it:** C1's day cost (1.0 ×) and 2.0 ×.

**The window:** every session with a finite ctier, ≤ 2023-12-29. The first scored session is reported.

## 2. The books

- **P, the primary:** the gated trades (ctier < 1/3).
- **U, ungated:** every fresh crossing, the always-on night break (the control).
- **R, the rest:** U minus P (ctier ≥ 1/3).

## 3. The statistics

**Per trade:**
- gross and net in bp and in dollars at one MNQ;
- the gross HAC t, by D680's `R.nw_t`.

**The gate's null:** exact rotation of P's take mask over U's trades, every circular offset (D738's `rotation`).
- **S2, the primary statistic:** gross efficiency Σg / Σ|g|.
- **S1, reported:** mean net.

**Overlap and the component line:**
- sessions that P shares with C1 (ctier < 1/3 at 09:30, from `V.book`), and the share of those in the same direction;
- daily ρ with C1's in-sample trades, with D737's in-sample twin (`V737.cell` over D738's `read_cut` panels) and with
  NQ F2 (`Z.build_f2`);
- net Sharpe and Sortino at one MNQ, hit rate, skew, and gross beside net.

## 4. The decision rule (declared now)

**SUPPORTED** iff all four hold:
1. P has ≥ 30 trades.
2. **D680's in-sample bar:** P's gross HAC t ≥ 1.28 AND P's mean net > 0, at the night cost.
3. **The gate selects:** S2's exact rotation p ≤ 0.05 (one primary test, so no family correction).
4. **The principal's standard:** P's book EARNS under D736's G1–G3, abstention years counted as abstention.

**LEAD** if (2) holds and (3) or (4) fails. **Also a LEAD, reported separately,** if U alone meets (2) at the night
cost: an always-on night break, which is not selective and so is not this design.

**NOT SUPPORTED** otherwise.

**A cost reading:** the 1.0 × and 2.0 × lines are reported. A SUPPORTED reading that fails (2) at 2.0 × carries the
label "COST-FRAGILE".

## 5. Assertions (each canary must raise)

1. **Known answer:** D672's C1 through `V.book` and `V.known_answer`.
2. **Lag:**
   - the asia range reads no bar at or after 03:00, and a canary that includes the 03:00 bar must raise;
   - D671's `tier_audit` passes on p_rv, p_asia and ctier, and raises on `tiers(leak=True)`;
   - the candidate test reads only the 03:00 bar's open.
3. **Second implementation:** every P and U trade is re-derived with D666's own `plain_break` and `exit_trade` on the
   same bars, with their constants set for this clock (last entry 08:29, close 09:29, no fill tick) and restored
   after. Entry bar, direction, entry and exit price must agree exactly. A canary with the close at 09:28 must
   disagree.
4. **Sign, in money:** on a hand-built rising night, the long's dollars are > 0 and the short's < 0.
5. **Right quantity:** the 03:00-inside condition binds (it drops > 0 sessions); P ⊂ U; the rotated mask differs from
   the observed; the night cost exceeds the day cost.

## 6. The report (all four groups)

For P, U and R:
- **Performance, net and gross:** total, mean, net and gross Sharpe and Sortino, the share of sessions traded, max
  drawdown, Calmar, worst day, mean gross against 2c, and the breakeven cost.
- **Trade distribution:** median, win rate, payoff, skew, kurtosis, the three 1 % trims, the exit reasons, and the
  entry hour.
- **What it depends on:** net by year; the book without its two best years; long against short; the top trade named.
- **Nulls:** S1 and S2 with p50 and p95.
- **The minimum detectable mean (gross, t 1.28)** for P's count and standard deviation.

## 7. Predictions (checkable)

**Opus: P(SUPPORTED) ≈ 0.15.** U's gross is near zero:
- a fresh crossing on a foreign clock was −5.3 to +1.6 bp in D677;
- the 02:00–03:00 drift has been about zero since 2021.

If P is positive, it will rest on two or three years, like C1's 2021–22.

**The Fable agent's prediction was not quantified** ("0 variants run").

## 8. Runtime

The Globex load (about 1 min, cached), the RTH panels for D737's twin, and loops over about 2,000 sessions: a few
minutes, run-once. Nothing is fanned out.

## 9. What follows

- **SUPPORTED or LEAD:** the principal chooses the confirmation route (forward Globex recording, or a vault slot on
  the explicit word). Nothing is admitted.
- **NOT SUPPORTED:** recorded. The C1 comparison's ideas are then spent; idea 3 (FOMC 14:00) was described by its
  own author as underpowered.
