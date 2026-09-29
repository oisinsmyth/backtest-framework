# D666 — STAGE 0 DESIGN: the re-break of yesterday's range: break out, pull back to the level, re-break 0.25 ATR beyond it within an hour, on ES and NQ separately, with a vol × gamma projection as the filter and gap and flow as the sizing

*2026-09-29.*
- *The principal's direction: "if we have break out from yesterdays range and then a pull back we place a limit order
  one or two ATR outside the range. Then if the market breaks out and it pulls back and breaks out again then we are
  in. That gives us our prediction, then we use the results of the other studies to confirm and project a price on
  which to filter. We use the overnight gap and order flow as confluence to help with sizing."*
- *Their choices: daily ATR(20); the pullback touches yesterday's level; all four exits (the projected target with a
  stop and the close, hold to the close, a fixed 60 minutes, **plus a trailing stop**); ES and NQ now, other roots
  later, "make sure the confluences are root specific"; the re-break within 60 minutes. After the frequency count:
  **0.25 × ATR, a 60-minute window**.*
- *To be committed alone, before its runner (R8).*

## 1. Why this, and what is new

**What is already known:**
- **The plain break carries nothing.** The opening-range break's 60-minute follow-through is +0.31 bp gross on ES and
  −0.66 on NQ, which is −3.2 bp net at micro size on both (D665 §C1).
- D531's opening-range breakout was null on every root.
- D482/D483: a plain channel breakout earns what a direction-free control earns.

**What is new here:** the **sequence**. The market breaks yesterday's level, returns to test it, and breaks again
within the hour. The hypothesis is that a level that holds on retest marks real demand (or supply) beyond it, where a
first break does not. **The control is therefore the plain break at the same distance, with no pullback required.**
The design isolates the value of the pullback-and-re-break.

**The gamma lesson (D665):** dealer gamma predicts how far the market moves, not which way. So gamma enters here only
through the **projected move** (the target and the filter), never the direction.

## 2. The frequency, read before this design (counts only)

`scripts/diag_rebreak_frequency.py` (`e79e861`) read the price path only up to each entry, never after it:

| distance, window | ES setups a year | NQ setups a year | vault events (ES / NQ) | push needed per trade, 60-min hold |
|---|---:|---:|---:|---:|
| 1 × ATR, 60 min | 2.1 | 2.3 | 3 / 4 | 62 / 81 bp |
| **0.25 × ATR, 60 min** | **76.8** | **80.6** | **119 / 125** | **12.5 / 15.1 bp** |

The chosen setup trades about **77–81 times a year per root**, balanced long and short. **Its bar is 12.5–15.1 bp per
trade** (D661's formula at the vault count), against the plain break's +0.31 bp gross (D665).

## 3. The rules, per root r ∈ {ES, NQ}, day session 09:30–16:00

**Levels, known before the open:**
- L⁺ = the prior session's RTH high; L⁻ = its RTH low;
- A = D644's `atr20`, the daily ATR over the prior 20 sessions.

**The setup, long side** (the short side mirrors it):
1. **Arm:** a one-minute bar trades above L⁺.
2. **Pullback:** a later bar's low touches L⁺ (≤ L⁺). Record the touch minute τ.
3. **Entry:** a **buy stop at L⁺ + 0.25 A**, armed at the pullback's touch (the principal: "arm the ... trade after
   the breakout and immediately after the pull back reaches the range as by definition if the trade hits the ...
   order then it has broke out again").
   - The order sits beyond the level, so only a re-break fills it. In broker terms it is a stop order; a limit order
     placed there would fill at once.
   - With one-minute bars, a bar that both touches and reaches the stop cannot be ordered within the minute. The
     order is live from the **bar after τ** (conservative), and the runner reports how many same-bar cases this
     leaves out.
   - It stays live until **τ + 60 minutes**. If it does not fill in time, the setup **expires**, and that side returns
     to idle and may set up again.
   - Only the **first entry of the day**, on either side, is traded.
   - No entry after 15:29.
4. **Fill:** at the stop, or at the triggering bar's open if that bar opens through the stop, **plus one tick of
   stop slippage**.

**Exits** (the four the principal chose). Exits are checked from the bar after the entry bar. Within a bar the stop is
taken before the target (pessimistic). Stops fill at the stop, or the open through it, minus one tick. Targets fill at
the touch.

| exit | rule |
|---|---|
| **E1, projected target** | target = entry ± P (§4); stop at L (back through yesterday's level); else flat at 15:59's close |
| **E2, hold to close** | stop at L; else flat at 15:59's close |
| **E3, fixed 60 minutes** | the close of the bar starting 60 minutes after the entry bar, no stop (comparable with D662–D665's F) |
| **E4, trailing stop** | initial stop at L; then it trails **0.25 A behind the best price since entry**, and never loosens; else flat at 15:59's close |

**Cost:** the micro round trip in dollars (D645's `COST_USD`), plus the ticks of stop slippage above, in bp of the
entry.

## 4. The projection and the filter: "use the results of the other studies to confirm and project a price"

**The projected move P, in bp:** P = σ_left × m.
- σ_left = σ₂₀ × √(minutes from the entry to 16:00 / 390), with σ₂₀ the prior 20 sessions' RTH close-to-close sd.
- **m = 1.5 when dealers are short gamma, else 1.0.**
  - Short gamma for ES: SqueezeMetrics SPX GEX, the prior row, < 0 (credited; licensed).
  - Short gamma for NQ: its own options book's G < 0.
  - **The 1.5 is informed by D665's in-sample |F| ratio between short- and long-gamma sessions. That is disclosed:
    it was read on this sample.**

**The expected-profit filter** follows the principal's standing rule and D649's template. The principal asked "How
are you projecting profits?"; P alone is a size estimate and says nothing about capture. So:

**projected gross_i = π̂_i × P_i**; trade only when **projected gross ≥ 2 × the round-trip cost** at the entry.
- **π̂_i, the pass-through:** the mean of (the realised gross / P) over **all EARLIER trades of the same root and
  exit** (an expanding window, in time order). The trade's own outcome and any later one are never used. π̂ carries
  the setup's directional edge: near 0 if re-breaks do not carry, so the filter then blocks.
- **Burn-in:** the first 40 trades per root and exit are traded unfiltered, and π̂ is built from them.
- **A minimum count:** if fewer than 30 filtered trades remain after the burn-in, that cell's filtered verdict is
  UNRESOLVED.
- **Two gates (§7), after the principal: "It should pass the gross bar not net".**
  - The unfiltered re-break must show the **mechanism**, a directional edge **before costs**.
  - The filter then has to make it **tradeable after costs**.
  - A filter on no mechanism selects noise. But a mechanism whose average trade does not clear the fee can still be
    tradeable on the trades its projection selects: D649's pattern, and the reason the rule exists.
- Reported: the filter's pass rate, π̂'s path, and the net of the trades it removes.
- A lag canary must raise: a π̂ that includes the trade's own outcome.

## 5. Sizing: "the overnight gap and order flow as confluence", each root's own

**Confluences, each signed by the trade direction D and known at the entry:**
- **gap:** D × (the session's open / the prior close − 1) > 0.10 × A (as %), i.e. the gap ran the trade's way;
- **futures flow:** D × A7 > 0, the root's own large-lot signed share (`data/opening/a7.csv`, sealed), at the latest
  checkpoint (09:45 / 10:00 / 10:30 / 11:00) at or before the entry;
- **cash breadth:** D × the root's own constituent TICK (TICK-SP for ES, TICK-NQ for NQ) over 09:30 → the entry's
  signal bar, as D663 defined it, > 0.5.

**Size = 1 + the number of aligned confluences, in micros (1 to 4).**

**The fade veto.** The principal chose the opening model's one informative signal as a veto: D645's observables model
(S-A) identifies FADE days out of sample (AUC 0.64–0.66; D658, D660).
- Its **walk-forward, out-of-sample p_FADE** is taken at the latest checkpoint (09:45 / 10:00 / 10:30 / 11:00) at or
  before the entry. It is rebuilt with D645's own `walk_forward`, as registered: pooled fit, market dummy.
- **The veto:** p_FADE ≥ the 80th percentile of p_FADE over the prior 252 sessions (earlier sessions only), **and**
  the fade's direction (towards the prior close, −sign(gap)) opposes the trade. Then the trade's size is 0 (skipped).
- An entry before 09:45 has no checkpoint and cannot be vetoed.

**Sizing and the veto are the secondary layer.** The gates use 1 micro on every setup. The sized-and-vetoed book is
reported beside them on the same setups:
- its Sharpe against the flat book's;
- the slope of net per trade on the confluence count (t);
- the net of the vetoed trades, against the kept ones.

A lag canary must raise: p_FADE taken at a checkpoint after the entry.

## 6. Statistics

**Gate 1, the mechanism: 8 cells (4 exits × 2 roots).**
- The **gross** P&L per trade, bp, **unfiltered**: every re-break setup is traded.
- One-sided (mean > 0), **Holm across the 8**, HAC t over the trades in time order.
- The controls below are read on gross too.

**Gate 2, tradeability, on each cell that passes Gate 1:**
- the **expected-profit-filtered** book's (§4) **net** P&L per trade, bp at 1 micro;
- one-sided, Holm across the cells that reached Gate 2;
- at least 30 filtered trades after the burn-in, else UNRESOLVED.
- The unfiltered net is reported beside it for every cell.
- One-sided (mean > 0), **Holm across the 8**, HAC t over the trades in time order.

**The controls:**
- **C1, the plain break (the claim's control):** the same distance and exits, with the buy stop at L⁺ + 0.25 A live
  from 09:30. No arm or pullback is needed, and the first fill is taken. The **difference re-break − plain** per exit
  and root is reported with its t (Welch).
- **C2, random entry within the setup's own hour (the timing null):** the same session, side and exits, but
  entering at a uniformly random minute in the 60 minutes after τ. 1,000 draws (seed 666). Reported: p50, p95 (with
  its bootstrap SE) and the rank of the re-break's mean.

**Tails, eras and dependence:**
- without February–April 2020; without the top and bottom 1% (and each alone);
- by year;
- long against short;
- before and after 2022-05-16;
- the top trade named with its bar.

**The four groups** (CLAUDE.md), per cell and at 1 micro:
- net and gross; Sharpe and Sortino, annualised by the cell's trades a year; exposure; maxDD; breakeven cost;
- the trade distribution with the three trimmed means;
- **a component line**: daily $ net Sharpe, hit rate, skew, and ρ with D466's K1–K6.

**Power:** the MDE of each cell, and the vault power at its in-sample mean (about 120 vault events per root).

**Secondary:**
- **sizing:** the sized book's Sharpe against the flat book's on the same trades, and the slope of net per trade on
  the confluence count (t);
- **the filter's value:** the net of the trades it removes.

## 7. Verdict (per root)

**Gate 1, the MECHANISM, passes** for exit e when all of these hold:
- the cell's mean **gross** > 0 with Holm p < 0.05 (across all 8 cells);
- the re-break's gross beats the plain break's with the same exit (difference > 0, t ≥ 2);
- its gross mean is above C2's p95 by more than 2 SE;
- it is positive without February–April 2020.

**Gate 2, TRADEABILITY, passes** when the cell passed Gate 1 and all of these hold:
- the **filtered net** mean > 0 with Holm p < 0.05 across the Gate-2 cells;
- there are at least 30 filtered trades;
- it is positive without February–April 2020.

**Verdicts:**
- Gates 1 and 2: **SUPPORTED**.
- Gate 1 only: **MECHANISM ONLY**, real before costs but not tradeable at micro cost as filtered.
- Neither: **NOT SUPPORTED**.

Each is stated with its power: the MDE against the 12.5–15.1 bp bar, and the vault power.

## 8. Routing

- **SUPPORTED:**
  - vault power first, to the principal;
  - then a pre-registration of the trade (the supported exit, the filter, the sizing if the secondary supports it)
    for the joint vault run;
  - then roll-out to other roots, each with its own confluences, as the principal asked.
  - Under the SqueezeMetrics permission, anything built on GEX informs only the principal's own trading.
- **NOT SUPPORTED:** the re-break line closes on ES and NQ. Other roots are not tried on this construction without a
  new reason.

## 9. The runner's assertions, each proved to fire in `--selftest`

1. **Lag:** the setup is re-derived by a second implementation that never calls the setup function. Every
   confluence and the projection use data dated before the entry bar. Canaries must raise:
   - a gap measured to the entry price;
   - A7 at the checkpoint after the entry.
2. **Sign, in money:** a long that rises pays and a short that falls pays. A stop exit loses exactly the stop
   distance plus slippage and cost.
3. **Fills:** a bar that opens through the stop fills at its open. Stop-before-target inside a bar. The trailing stop
   never loosens (a canary loosens it and must raise).
4. **The window:** a setup whose fill comes after τ + 60 is not traded (canary: a 61-minute fill).
5. **Right quantity:**
   - the re-break's trade set differs from the plain break's;
   - E3 differs from E2.
6. **The licence guard** (D663's): no per-date gamma in any output.

**Speed, by design:** the cells and the 1,000 random-entry draws fan out to processes over the roots and exits. The
setup scan is one pass per session.

## 10. Predictions, written before the run

1. **Both roots: NOT SUPPORTED, failing Gate 1.** The plain break carries about 0 gross (D665), and a retest adds
   little.
2. **The re-break minus the plain break is within ±2 bp** for every exit.
3. **No exit beats E3 by more than its SE** (memory: exits cannot rescue a thin micro edge).
4. **Sizing:** the slope of net per trade on the confluence count is inside noise (|t| < 2). **The veto:** the
   vetoed trades' net is below the kept ones' by less than 2 SE, i.e. not distinguishable.
5. **Every cell's vault power is below 50%.**
6. **The pass-through π̂ settles near 0** (within ±0.1) on both roots, so the filter blocks most trades after the
   burn-in.

## 11. Outputs

- `scripts/stage0_d666_rebreak.py` (`--selftest`, `--dry-run`, `--run` once);
- `data/stage0_d666_rebreak.json` (statistics only, licence-guarded);
- a RESULT record, crediting SqueezeMetrics.

No trials rows are written.

## Amendment D666-A1, before the run (2026-09-29): the random-entry null must not condition on the re-break

§6 C2 drew its random entries "within the setup's own hour" on the sessions where a re-break filled. The runner's
dry run on synthetic bars (no real data read) showed why that is wrong: its p95 came out at +17 to +25 bp against
trade means of about 0. The re-break sessions are known to rise through the stop level later in that hour, so a
random earlier entry at a better price is handed the future.

**C2 is therefore drawn on EVERY session's first retest** (the first pullback touch of the day, either side), whether
or not it re-broke:
- a uniform minute in (τ, τ + 60] and at or before 15:29;
- entered at that bar's close + 1 tick, on the setup's own side;
- the stop 0.25 A + 1 tick away;
- the same projection and exits.

That compares "enter on the re-break" with "enter anywhere in the hour after the retest", with no knowledge of
whether the retest succeeds. Nothing else changes.
