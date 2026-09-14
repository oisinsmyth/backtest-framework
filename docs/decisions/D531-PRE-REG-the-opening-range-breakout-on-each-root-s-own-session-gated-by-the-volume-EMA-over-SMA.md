# D531 — PRE-REGISTRATION: the opening-range breakout on **each root's own session**, at five minutes, gated by `log(EMA/SMA)` of opening-range volume

**Pre-registration. Committed before the runner exists (R8). The result goes in a separate file.**
**Window: 2016-01-04 → 2023-12-29 in sample. 2024-01 onward is RESERVED AND NOT READ by this record.**
Nothing here is admitted to any book or ledger (R15).

*On the principal's instruction, 2026-09-14, after he rejected my proposal to re-measure the
commodity roots instead. He is right that I was over-closing: my own standing note says I close whole
axes on one construction's failure and have been **corrected four times**. This is the fifth.*

---

## 0. Why this is not a re-run of D487

**D487's own title says it: *"The ORB line closes before a breakout is tested."*** It tested a
*precondition* — whether intraday continuation exists — on **ES and NQ only**, 1,993 sessions, on the
09:00–15:59 equity template. **No breakout was ever traded and no commodity root was ever looked at.**

Four things are new, and each is independently sourced:

1. **A breakout is actually tested.** D487 stopped at the precondition.
2. **Non-index roots.** D528's one-direction rule finding makes a second *index* arm a closure
   offence, so component #2 must live elsewhere — and no ORB has been run on a commodity root here.
3. **Each root's own session.** [D530](D530-avenue-3-closed-the-leveraged-ETF-reset-flow-is-real-and-carries-no-direction-and-16-of-36-roots-do-not-trade-in-the-day5m-close.md)
   measured that the 09:00–15:59 band is a *template*: CL trades **3.1 %** of its volume in the last
   hour, HG 2.6 %, the grains **zero**. Every commodity price-action statistic in this programme has
   included hours the root barely trades.
4. **Five-minute resolution.** `fut_day5m` (84 bars a session, verified in D524) is unused. Every
   prior price-action measurement here ran on **seven hourly bars a session**.

**And the volume gate has never been tested where volume is a strong instrument.** D224/D225 found it
on ETFs; D226's own disclosure records why that is weak evidence: *"ETF volume is a weak instrument…
a quiet tape can mean the authorised participants simply did not need to trade… it cuts one way: a
NEGATIVE here is weaker evidence against the gate as a concept."* Futures volume is the traded volume
of the traded contract.

**Lane note.** The concurrent D528 lane owns the volume filter on 5-minute bars and the
mean-reversion-on-excursions side. This record takes the **continuation** side and applies the gate
at the **session** level, where time-of-day is controlled by construction rather than corrected for.

## 1. The construction

**Session, per root, derived not assumed.** From `fut_day5m`, take each root's median volume by bar
index over the window; the session is the contiguous span of bar indices whose median volume is
**≥ 10 % of that root's maximum median bar volume**. The span is reported per root in the result.

**Opening range.** The first `N` bars of that span. `OR_high`, `OR_low`, and `OR_vol` = total volume
in those bars.

**Breakout.** The first bar after the OR whose high > `OR_high` (**long**) or low < `OR_low`
(**short**). **If one bar breaks both sides, the session is SKIPPED and counted** — OHLC cannot
order two touches inside a bar, and booking the favourable one is the exact artefact the external
research names (*"a backtest that books the target when a bar's range contains both stop and target
inflates win rate systematically"*).

**Entry** at the **next** bar's open after the breakout bar. **Exit** at the close of the session's
last bar. One round trip, forced flat inside the session — venue-agnostic under the
2026-09-13 amendment to hurdle P.

**The gate**, computed at the OR's close and therefore causal with respect to entry:

```
gate_d = log( EMA_10(OR_vol) / SMA_50(OR_vol) )        over SESSIONS, same root
```

Both averages include session `d`, whose `OR_vol` is known before entry. Comparing today's opening
range to previous opening ranges is **time-of-day-matched by construction** — which is why this form
does not need the time-of-day normalisation D528 had to add for 5-minute bars, where NQ's median
volume swings **14.5×** across the session.

## 2. The grid, and the PRIMARY declared before the run

`N ∈ {3, 6, 12}` bars — 15, 30 and 60 minutes. Roots: **CL, GC, SI, NG** (candidates) and **ES, NQ**
(calibration only, not candidates — index roots are ineligible for component #2).

> **PRIMARY CELL: `N = 6`, pooled over CL, GC, SI, NG, gated (`gate_d > 0`).**

Everything else is secondary and is reported as a family.

## 3. The statistic and the nulls

**Statistic: HIT RATE** — the share of trades whose gross P&L is positive. Not the payoff ratio:
[D529](D529-the-payoff-ratio-is-exit-geometry-the-hit-rate-is-the-edge-and-my-reframe-was-backwards.md)
established that an asymmetric exit manufactures a payoff ratio above 1 on a random entry, and that
this book is paid for accuracy. Mean gross per trade and net against the **$4.21** round trip
(D527-corrected) are reported beside it.

**N1 — sign randomisation, per session.** Flip the direction of each session's trade on a random
sign. This preserves entry timing, exit rule, hold length and the magnitude distribution, and
destroys **only** the directional claim. It is the right control because the ORB's entry timing is
derived from the price path and cannot be rotated away from it.

**N2 — family maximum.** One sign vector per draw, common to every cell, so the family's correlation
structure is preserved. The family is all `N × root` cells including the calibration roots.

**PASS requires both:** the primary's hit rate exceeds its own N1 p95, **and** the family maximum
exceeds the N2 p95. Anything less is reported as not clearing, and a cell that clears N1 but not N2
is reported as such rather than promoted.

## 4. Two predictions, written so they can be wrong

- **P-A — the ES cell FAILS.** D487 measured the first half-hour *reversing* into the last on ES,
  pooled slope **−0.102 (0.024), −4.3 SE**. A breakout-continuation on ES is trading against that. If
  ES comes out strongly positive, **suspect the implementation before believing the result.**
- **P-B — the gate COSTS accuracy rather than adding it.** D506 scored an activity filter against two
  signals this repo owns and found it buys **+0.85** points of fee dilution and costs **−2.09** points
  of accuracy. If this gate *adds* accuracy on futures, that is the genuinely new finding, and it
  would be the first evidence that D226's ETF caveat was the binding one.

Both gated and ungated are reported for every cell, so P-B is measured rather than assumed.

## 5. What would make this a component, and what would not

Clearing §3 makes it a **candidate**, not a component. A component needs the
`COMPONENTS_PROP.md` standard — C-a net Sharpe > 0.5 at minimum tradable size under the cost that
size pays, C-b ρ < 0.3 against the admitted MACD arm, C-c skew, C-d daily σ ≤ $500, C-e provenance —
scored by the runner in dollars, not inferred. **And C-b carries a second meaning now:** an arm that
takes the opposite side of the NQ arm in a *correlated* instrument is an account-closure offence at
three of five venues, which is why the candidate roots here are commodities.

**The reserved slice is not read by this record under any outcome.**
