# D733 STAGE 0 PRE-REG — the pullback entry in an NQ trend: does buying the retrace (or its turn) beat the drift it rides?

*2026-10-01. The principal:*
> "I don't want a dumb follow type strategy. I would like an entry signal?"
>
> "lets look at #1, have a fable 5.1 agent reason through it in parallel … and compare ideas"
>
> "Ok pre-reg, build and run the merged study".

- **How the design was made:** two independent designs were drafted, this session's and a Fable 5.1 agent's
  (2026-10-01; mine was written to the scratchpad before reading theirs), and merged as compared for the principal.
  - **The Fable agent's skeleton:** the arming, the trigger ladder, the timing null, the oracles, the clock budget
    and the family null.
  - **This session's 5-minute turn,** in place of a one-minute turn.
  - **The retest target and the matched-row decomposition,** reported.
- **The order (R8):** this record is committed before the runner exists, and the runner before its one run.
- **What it is:** a premise check, oracle first. It chooses no rule.
- **The prior** (both designers, before any run): 20–25% that EDGE reads. The likeliest outcome is a drawdown
  instrument, not an entry edge.

## 0. Data, seal, conventions

- **Data:** NQ's day session, one-minute OHLCV, 2016-01-04 → 2023-12-29, with D727's days, σ_oc and z. Roll days are
  excluded, and a day needs ≥ 380 bars.
- **The seal:** nothing dated 2024-01-01 or later is read. NQ's 2024+ last hour is D716's joint-vault look.
- **Bars:** bar m starts at 09:30 + m minutes. The price at minute m is the close of bar m − 1.
- **Size and cost:** one MNQ ($2 a point), $4.07 a round trip. One tick is 0.25.
- **Volume is not used.** The volume detector is CLOSED (D730/D731), so "quiet" enters only as pullback speed,
  measured on price.

## 1. The construction (everything as of bars that have already closed)

- **Armed:** the first minute m0 in 10:00 → 14:00 with |z_m0| ≥ 1.0, where z_m = (P_m − O)/(σ_oc √(m/390)) (D727's
  middle threshold, not its after-the-fact best). The direction is D = sign(z_m0), locked for the day. A day is armed
  at most once.
- **The move:**
  - X_t is the running extreme in direction D, the high (low for D = −1) of bars from 09:30 to t − 1;
  - A_t = D(X_t − O).
- **The pullback:**
  - L_t, the pullback extreme, is the most adverse low (high) since X_t was set;
  - the depth is r_t = D(X_t − P_t)/A_t;
  - the noise floor is D(X_t − P_t) ≥ 0.15 σ_oc.
  - **Qualifies** when r_t ≥ r_min;
  - **void for the day** if r_t > 0.8, or if price is back to the open (D(P − O) ≤ 0) before an entry.
- **The trigger ladder, r_min ∈ {0.25, 0.5}:**
  - **(a) the resting limit, no turn.** A limit at Lim_t = X_t − D·r_min·A_t, which moves with X. It fills on the
    first bar after arming whose range reaches Lim, at Lim (or at the bar's open if that opens beyond it). Its stop is
    the void depth: X − D·0.8·A − D·1 tick, at the fill.
  - **(b) the 5-minute turn, PRIMARY.** After qualifying, the first completed 5-minute bar (bars aligned at 09:30 +
    5k) whose close is beyond the previous 5-minute bar's high (low for D = −1). Entry is at the next one-minute
    bar's open. The stop is L − D·1 tick, at entry.
  - **(c) the bounce.** After qualifying, the first one-minute close beyond L + D·0.25·(X − L). Entry is at the next
    bar's open, with the stop as in (b).
- **The entry deadline is 15:00.** One trade a day per cell.
- **The grid** is 2 × 3 = 6 cells. **The primary cell is (r_min 0.25, trigger b).**
- **The stop fill:**
  - checked on bars after the entry bar (for (a), the fill bar too, if its range reaches the stop);
  - if a bar opens beyond the stop, the fill is the open; otherwise the stop;
  - then 1 tick of slippage against the trade;
  - a bar reaching both the stop and a target counts as stopped.
- **The exits:**
  - **E1, primary:** the stop, or the 15:59 close;
  - **reported:** 1R and 2R targets (R = |entry − stop|); a retest of X; a 60-minute time exit; and the same entry with
    no stop, held to the close (the cost of defined risk).

## 2. Controls and nulls

- **C2, the timing null (primary, enumerated, SE 0):**
  - For offset j = 20 … n − 20, every trade's entry minute and stop distance (in σ_oc units) are moved to day
    d + j.
  - There it is entered at the open of the same minute's bar, in that day's OWN locked direction. It is skipped if
    day d + j is not armed by then.
  - The exit is E1.
  - **The statistic:** the mean net per trade.
  - **Reported:** pooled, and by |x| at entry (x = (P_entry − O)/σ_oc; bins < 0.5, 0.5–1, 1–1.5, ≥ 1.5).
  - **The family null:** the maximum over the six cells at each offset.
- **C1, the same-day follow:** from arming (m0) to the close, on the same days. The per-day difference between the
  pullback trade and the follow is split into (P_m0 → P_entry) plus the effect of the stop.
- **C3, does the turn pay:** (b) − (a) on days where both trade, as a paired mean and t.
- **The mirror:** the primary cell entered against D. This is a sign audit in money, and a check that any edge is
  directional.
- **The matched-row decomposition (reported):** the E1 outcome from every armed 5-minute clock row, against the
  trigger rows, within the same clock hour and |x| bin.

## 3. Oracles (computed first, and they can kill the idea)

- **O1, the perfect-turn ceiling:** on armed days with a qualifying pullback (r ≥ 0.25), a fill at the pullback's
  eventual extreme (the most adverse price before a new X, or before the close), held to the close with no stop.
  **If its mean net is under 2 × $4.07, the reading is NO ROOM.**
- **O2, the stop-out oracle:** the share of the primary cell's trades that are stopped out, and the book of only the
  unstopped trades (the ceiling of any pullback-quality filter).
- **O3, the clock budget:** the drift-implied gross at the realised entry clocks, β_D727(clock) · x_entry · σ_oc · $2,
  using D727's NQ β at the nearest half hour. **Under $8 a trade, the construction is paying for a late entry.**

## 4. Readings (declared now)

| reading | condition |
|---|---|
| **NO ROOM** | O1 is under 2 × $4.07. Recorded first, whatever follows |
| **EDGE** | the primary cell's mean net > 0 at a NW t ≥ 2 (trades in day order, 5 lags); **and** above C2's p95, pooled and in ≥ 3 of the 4 \|x\| bins (bins with ≥ 30 trades); **and** its excess over C1 per day ≥ 0 at t ≥ 1 |
| **DRIFT ONLY** | mean net > 0, but inside C2 or below C1 |
| **NOTHING** | otherwise |

- **TURN PAYS:** C3's paired t ≥ 2.
- **Holm over the six cells:** each cell's p is its share of C2 at or above it.
- **GO to a rule design with the principal** requires all of:
  - EDGE in the primary cell;
  - the primary cell above the FAMILY p95;
  - net Sharpe ≥ 0.4 at one MNQ;
  - ≥ 5 of 8 years positive;
  - the largest year's share < 50%.

**Reported for every cell:**
- net and gross, Sharpe and Sortino, max drawdown, P3a at $50k and $150k;
- trades, mean, median, win rate, payoff, skew, kurtosis, the symmetric 1% trims;
- the years, and the largest year's share;
- the MFE and MAE at +15, +30 and +60 minutes and at the close;
- pullback-speed terciles, up days against down days, the entry hour;
- a wider-stop sensitivity (L − D·0.1σ_oc);
- the multi-entry book (≤ 3 a day, re-entry only once flat; path-variant).

**The ledger line for the primary cell:** ρ with the MACD arm and with NQ F2.

## 5. Runner assertions

- **Lag:**
  - every sampled trade is re-derived by a second implementation from rows truncated at the entry minute;
  - a canary that reads the entry bar's own extreme must fire;
  - the self-test shows the audit raising on a one-bar lead.
- **Right quantity:**
  - the trades carry D727's days and σ_oc (asserted against D727's known answer);
  - C2's offset 0 reproduces the observed E1 trades for cells (b) and (c), whose entry is a bar open.
- **Sign, in money:** a long stopped below its entry loses; the mirror's sign is opposite; a stop hit on a gapped
  open fills at the open.
- **The self-test** shows each audit firing on a deliberately broken input.
