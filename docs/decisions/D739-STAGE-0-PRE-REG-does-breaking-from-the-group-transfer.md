# D739 STAGE 0 PRE-REG — does D735's mechanism transfer? A root's move that its group does not share, on metals, energy, rates, FX and grains

*2026-10-01. The principal: "Lets do 3. D735's mechanism on other roots".*
- **The order (R8):** this record is committed before the runner exists, and the runner before its one run.
- **What it is:** a premise check, mechanism first. It chooses no rule. **The rule is D737's, unchanged.** Nothing is
  tuned per root.
- **The prior** (before any run):
  - about 10–15% that any micro-tradable root reaches GO;
  - higher, about 35%, that some group shows the mechanism.
  - On NQ the mechanism was tied to concentrated mega-cap flow, which none of these groups has in the same form.

## 1. The question

D735 found that on NQ, **the part of a move since the open that the rest of the equity market does not share continues,
and the shared part does not.**
- The mechanism read against YM (δ < 0, Holm 0.050).
- The trade, in the spread's direction, beat its timing null (ranks 0.94–1.00).

**Does the same hold inside other groups of related futures,** where each root carries a common factor (the dollar,
the rate level, the oil price, metals risk, the grain complex) plus its own part?

**The declared sign:** δ < 0 everywhere, as on NQ. The own part continues, and the common part continues less or
reverts.

## 2. Data, groups, windows

- **Source:** `fut_day1m.parquet` (one-minute day-session bars, 09:00–15:59 ET, 36 roots; the front from
  `fut_breadth_hourly`). It is read with a filter to **2016-01-04 → 2023-12-29**. **Nothing dated 2024-01-01 or later
  is read on any root.** 2024 onward is left unread for every root here, as the confirmation slice of anything that
  transfers.
- **Day filter, per root:** the session must be `present` and `same_front` (D728's rule), and hold ≥ 90% of its
  window's bars (missing closes are carried forward, and a missing open is the prior close). The leg's members need
  the same flags.
- **The groups and their common windows** (each group's window is its members' modal session from
  `cme_session_calendar`, cut to the earliest close):

| group | roots (26) | window (ET) | L (bars) | trigger window | micro-tradable members |
|---|---|---|---:|---|---|
| METALS | GC, SI, HG, PL, PA | 09:00 → 12:59 | 240 | 09:30 → 11:30 | GC (MGC), SI (SIL), HG (MHG) |
| ENERGY | CL, BZ, HO, RB | 09:00 → 14:29 | 330 | 09:30 → 13:00 | CL (MCL) |
| RATES | ZT, ZF, ZN, TN, ZB, UB | 09:00 → 14:59 | 360 | 09:30 → 13:30 | none |
| FX | 6A, 6B, 6C, 6E, 6J, 6S | 09:00 → 14:59 | 360 | 09:30 → 13:30 | 6E (M6E) |
| GRAINS | ZC, ZW, ZS, ZM, ZL | 09:30 → 14:19 | 290 | 10:00 → 12:50 | none |

- **Excluded, declared now:**
  - NG: it has no group partner (its co-movement with CL is weak);
  - LE and HE: two roots, weakly related;
  - SR3, BTC and NKD: no group;
  - the equity index roots: D735's, already spent.
- **The trigger window** is the window's open + 30 minutes to its close − 90 minutes, which is D735's geometry (10:00
  → 14:30 on a 09:30 → 16:00 session).

## 3. The construction (D737's rule; one cell per root)

**The objects** (for root R in group g, at minute m of the group window, m = 1 … L):
- x_R,m = (the close of bar m − 1 − O_R) / σ_R. O_R is the open of the window's first bar. σ_R is the RMS of the
  prior 20 valid sessions' window open-to-close moves (shifted one session).
- **The leg is the group:** x_G−R,m = the mean of x over the group's other members (all of them present that day).
- s_m = x_R,m − x_G−R,m; σ_s = the RMS of the prior 20 sessions' s_L (≥ 15 present); z_s,m = s_m / (σ_s √(m/L)).

**The trade:**
- **Trigger:** the first minute in the trigger window with **|z_s| ≥ 1.0**. D = sign(s). One trade a day.
- **Entry:** at the open of R's bar m0.
- **Stop:** σ_R √((L − m0)/L) away (**1σ_rem**), checked from bar m0. An open through it fills at the open, with one
  tick of slippage.
- **Exit:** the stop, or the close of the window's last bar.
- **Size and cost:** the smallest contract CME lists (the micro where `data/futures_costs.json` has one, else the full
  contract). The round trip is the file's `round_trip_usd` rule on its default line: commission + crossing ticks ×
  tick $ (d508_exec where measured, else one tick).
  - Full-size roots are scored and reported, but cannot reach GO (micro size only).

**Why no bin leg:** D735's per-|x| bin leg failed every cell, because its middle band held 55–73 trades and a $40–57
p95. That was power, not sign. Multiplicity over the 26 roots is carried by the family-wise null (§4) instead.

## 4. The tests (D735's, per root)

- **S1, MECHANISM (read first).**
  - y_R = a + β·x_R + δ·e, with e = x_G−R orthogonalised on x_R per clock. The clocks are every 30 minutes from 30 to
    L − 30, pooled.
  - The null rolls e across days (offsets 20 … n − 20, enumerated).
  - **MECHANISM** is δ < 0 with p_low ≤ 0.05, a day-clustered t ≤ −2, and Holm over the 26 roots ≤ 0.05.
- **O1, the room:** the fitted per-clock model's expected gross at the realised triggers, in the trade's direction,
  in $. NO ROOM if it is < 2 × the root's round trip.
- **C2a, the timing null:**
  - the trades' entry minutes and stop rules move to day d + j, enumerated, entered in that day's sign(x_R,m0);
  - the statistics are the mean net and the efficiency Σg/Σ|g|, with p50 and p95 reported;
  - **the family null** is the maximum over the 26 roots' C2a means at each offset. Offsets index each root's own day
    sequence;
  - Holm over the 26 C2a p_high.
- **C2b** (reported): that day's sign(s). Its offset 0 must reproduce the observed trades exactly.
- **Matched rows:**
  - every 5-minute row of the trigger window, in sign(x_R), under the same stop rule, matched by hour of the window
    and |x_R| bin;
  - the gain is the trades' net minus the rows' net, trade-weighted;
  - its SE is a day-block bootstrap: 2,000 draws, seed 739.
- **Counter trades** (sign(s) ≠ sign(x_R)), their mean gross, and C1 paired against the drift's direction.
- **The mirror.**

## 5. Readings (per root; then a count per group)

| reading | condition |
|---|---|
| **NO ROOM** | O1 < 2 × the round trip. Recorded first |
| **MECHANISM** | §4 S1 |
| **TRANSFERS** | MECHANISM; and O1 ≥ 2 × the round trip; and mean net > 0 at NW(5) t ≥ 2; and C2a's mean AND efficiency above their p95; and the matched-row gain ≥ one round trip at bootstrap t ≥ 2; and the counter subset's mean gross ≥ 0 when it holds ≥ 30 trades |
| **DRIFT ONLY** | mean net > 0, not TRANSFERS |
| **NOTHING** | otherwise |
| **GO** (to a vault pre-registration with the principal) | TRANSFERS; and C2a's mean above the **family** p95; and a micro contract (GC, SI, HG, CL, 6E); and net Sharpe ≥ 0.4; and ≥ 5 of 8 years positive; and the largest year < 50% in $ and in volatility units (D729, scale σ_R × $/pt); and **net > 0 without its two best years** (the principal's earn-when-trading standard, as D736 reads it) |

**What happens next, by outcome:**
- **A group whose roots read MECHANISM but no GO** is recorded as structure: "the common part reverts in group g".
- **If no root in any group reads MECHANISM,** D735's effect is recorded as NQ-specific (the mega-cap story), and the
  cross-group line is proposed for closure under R15. That is the principal's word.

## 6. Reported (CLAUDE.md's four groups, every root)

- **Performance:** net and gross; Sharpe and Sortino; max drawdown; the round trip and gross ÷ cost; the in-market
  share; net per year without the two best years.
- **The trade distribution:** with the symmetric 1% trims.
- **Years:** by year; D729's label.
- **The rest:** the entry-hour table; aligned against counter; up against down; the stopped share; O1, O2 (the drift
  budget from the root's own β per clock) and the excess.
- **Correlations:** daily ρ with NQ F2 (D720's `build_f2`) and with D735's YM k1.0 cell (rebuilt through D737's
  `in_sample`).
- **Group by group:** the δ table by clock.

## 7. The runner's assertions

- **Lag:**
  - a second implementation rebuilds s, z_s and the trigger from the raw parquet rows of R and its group, bars ≤
    m0 − 1, on 40 sampled trades per root;
  - a one-bar-lead canary must raise;
  - a shifted date join must raise.
- **Sign, in money:**
  - a rising day pays long and loses short;
  - a gapped stop fills at the open less a tick.
- **Right quantity:**
  - the generic functions here, at L = 390 and the trigger window 30 … 300, equal D735's on a synthetic panel to 1e-12
    (E1 table, trigger, timing null);
  - C2b's offset 0 reproduces each root's trades;
  - the FW null's offset 0 equals δ̂.
- **The seal:** the parquet filter's upper bound is 2023-12-29, and the runner raises if any later row reaches it.
- **Run-once.**
- **Roots in parallel** (threads; numpy). The projected wall time is a few minutes.

**The output:** `data/stage0_d739_group_breaks.json` (aggregates only).
