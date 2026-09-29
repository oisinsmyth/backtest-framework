# D673 STAGE 0 DESIGN — join the day's move once it has formed: after 10:00, enter when price is beyond both yesterday's close and today's open, and hold to the close; the evidence on YM, RTY and ES

*Drafted 2026-09-29.*
- *The principal: "Yes run the test on the other roots".*
- *It follows D670, whose post-hoc split located the MACD arm's in-sample gross in its entries after 10:00.*
- *Committed alone, before any runner exists (R8).*
- ***This rule has not been computed on any root.*** The only related numbers are D670's post-hoc split of the MACD
  arm's own trades on NQ, 2016–2023 (hourly fixture).
- *Numbered D673 because the other session's unmerged branch holds the two numbers before it.*

## 1. Why, and the two things this must not do

**What the MACD arm's in-sample record says** (D669, D670, NQ 2016–2023):
- **Its 10:00 entries**, two-thirds of its sessions, are close to noise: $9,830 gross, t 1.40.
- **Its later entries**, 23 % of sessions, carry more than half its gross: $12,281, t 3.69, hit 61 %.
- Those later entries come after its two MACDs come into agreement on a move that formed after 10:00. The arm also
  sits out days on which no move forms.
- Its timing rests on the impulse length and the 5-hour hold, the two settings D669 found to be a spike.

**The idea to test, without the MACD:** once the day's move has formed, it continues to the close.

**This must not be tuned on NQ.** The idea came from NQ's spent in-sample slice.
- NQ is **development only**, with no verdict.
- The confirmation rule below has **no free parameter**. It is the plainest statement of "a move has formed": price is
  on the same side of yesterday's close and today's open.

**This must not reuse what D670 already measured on its evidence roots:**
- D670's 15:00 last-hour cut was measured on YM, RTY and ES (YM t 2.78). It is therefore **reported as a variant, not
  gated here**.
- **The primary rule holds to the close.**

**Multiplicity.** This is the family's second construction on YM, RTY and ES, after D670. **Gate 1's family-wise α is
halved to 0.025,** Holm across the three evidence roots.

**The overlap:** the other session's unmerged plain-break line also enters once a move has formed, on the break of
yesterday's range plus 0.25 ATR. This rule's threshold is weaker and parameter-free. Their correlation is named as
missing until both are merged.

## 2. The rule

**Per root r ∈ {YM, RTY, ES} (evidence) and NQ (development).** The day session from D462's one-minute
`fut_{r}_rth_1m`; the session table is `fut_index_sessions`.

- **Decision times:** the closes of the 10:59, 11:59, 12:59 and 13:59 bars. The 14:59 decision is excluded: a one-hour
  trade into the close is the last-hour momentum of K4 and of D581/D640, a different construction.
- **Confirmation at decision T:** s_T = sign(C_T − C′₁₅:₅₉) if it equals sign(C_T − O₀₉:₃₀), else 0. C′₁₅:₅₉ is the
  prior session's last close.
- **Entry:** at the **first** T with s_T ≠ 0, enter in direction s_T at the open of the next minute (11:00, 12:00, 13:00
  or 14:00). **At most one trade a session.**
- **Exit, primary:** at the close of the 15:59 bar.
- **Sessions dropped**, as D670 declared and D670's check confirmed (almost all early-close holidays and the session
  after each):
  - a roll (the contract differs from the prior session's);
  - the three circuit-breaker sessions of March 2020;
  - any session missing its 09:30 open, its prior session's 15:59 close, or its own 15:59 close.
- A decision bar that is missing is skipped for that session: the rule waits for the next decision time.
- **The windows:** ES, NQ and YM 2016-01-04 → 2025-02-28; RTY 2017-07-10 → 2025-02-28. The vault is sealed.
- **Cost:** as D670, the micro round trip from `data/futures_costs.json`'s `d508_exec` line, in dollars and in bp of
  the entry notional.

**Variants, each reported and never gated:**
- **V1, with D670's 15:00 cut:** exit at the 15:00 open if the entry is before 15:00 and the 14:00 hour moved against
  the position.
- **V2, the arm-like subset:** only sessions whose 09:59 confirmation (the same test at 09:59) was 0.
- **V3, from 10:00:** the 09:59 decision included, entry at 10:00.

## 3. The expected-profit filter (the programme's rule, k = 2)

The forecast is **the expanding mean gross of the root's earlier trades**, an intercept-only model. It is 0 until 250
trades exist. **Trade when forecast ≥ 2 × the trade's cost in bp.** It is a switch on the rule's own record.
- D670 showed that no feature known at 10:00 discriminates, so none is added.
- The filtered book is reported with every statistic, and its trades a year.

## 4. The controls

**N1, the direction permutation within ISO week** (as D669 and D670). The rule's directions are permuted among its
trades of the same week. The windows, entry times and weekly long count stay the same.
- 10,000 draws, seed 673.
- Statistic: the mean gross per trade.
- Reported: p50, p95 and the p95's bootstrap SE. The exact drift carry is asserted within 3 SE of the draw mean.

**N2, clock-matched random entries, on every session.**
- Each draw takes a session sample of the rule's trade count from all usable sessions.
- On each, it enters at a decision time drawn from the rule's own entry-time distribution, with a side drawn at the
  rule's long share, and holds to the 15:59 close.
- 2,000 draws, seed 673.
- It asks whether choosing *which days*, and which side, beats chance at the same clock.

## 5. The gates

**Gate 1, the MECHANISM (primary, unfiltered, gross), per evidence root:**
- the mean gross per trade, one-sided Newey-West t (5 lags), **Holm across YM, RTY and ES at a family α of 0.025**;
- **above N1-week's p95 by more than 2 bootstrap SE, and above N2's p95 by more than 2 SE** (within 2 SE is
  UNRESOLVED);
- positive without February–April 2020.

**Gate 2, TRADEABILITY, on a root that passed Gate 1:**
- the unfiltered net per trade > 0, one-sided, Holm across the roots that passed Gate 1;
- net > 0 at **+1 extra tick on each fill**.

**Verdicts per evidence root:**
- Gates 1 and 2: **SUPPORTED**.
- Gate 1 only: **MECHANISM ONLY**.
- Neither: **NOT SUPPORTED**.

**The construction:**
- **SUPPORTED on any evidence root:** a pre-registration for the joint vault run (the frozen rule, its EP filter and
  the component line), to the principal with its vault power.
- **MECHANISM ONLY:** recorded, untradeable at micro size.
- **NOT SUPPORTED on all three:** "join the formed move" is recorded as not transferring, and the MACD arm's later-entry
  gross as NQ's alone in sample.

## 6. Reported (CLAUDE.md's four groups), per root, for the primary, the filtered book and V1–V3

- **Performance:** net and gross side by side; Sharpe and Sortino, per trade annualised by the book's own trades a
  year, and daily at one micro; exposure (the share of sessions traded, and the mean hours held); σ; maxDD; breakeven
  cost; the mean move per trade against 2c.
- **The trade distribution:** count, mean, median, win rate, payoff, skew, kurtosis, and the three 1 %-trimmed means.
- **What the winners depend on:**
  - by year;
  - long against short;
  - by entry time (11:00 / 12:00 / 13:00 / 14:00);
  - before and after 2022-05-16;
  - sessions to half the P&L;
  - the top trade named.
- **The nulls as distributions:** N1's and N2's p50 and p95, with SE.
- **The component line**, computed by the runner:
  - the daily $ net Sharpe at one micro, hit rate, skew, gross beside net;
  - ρ with K8 (rebuilt as in D670), with the MACD arm (2016–2023 overlap), with D670's 10:00 rule on the same root,
    and with each other root's rule;
  - the other session's plain-break book named as missing.

**Power, before the run.** The hold is 2–5 hours, so σ per trade is below D670's 74–106 bp. Assume 60–85 bp and about
1,500–1,800 trades a root. With Holm's smallest threshold at 0.025 / 3, the minimum detectable effect at 80 % power is
**about 4.5–7 bp**. The runner prints each root's MDE from its realised σ before any mean.

## 7. Seals and order of work

- **The vault (2025-03-01 →) is not read;** a guard raises on any surviving row.
- No gamma, no Sierra data, and no download.
- CL/NG stay sealed.
- NQ 2024-01 → 2025-02 was read by D503 for the arm; NQ is development.

**The order of work:**
1. This record, committed alone.
2. `scripts/stage0_d673_formed_move.py`, with `--selftest`, then `--run` once.

**The self-test must show, each on a deliberately broken input:**
- a confirmation that reads a bar after its decision time raises (the causality canary);
- a trade entered at its own decision bar's close, not the next minute's open, raises;
- a second trade in one session raises;
- a roll session's trade raises;
- a vault row raises;
- the sign audit in money;
- the permutation keeps each week's long count, with its draw mean within 3 SE of the exact carry;
- an oracle direction beats N1's p95, and a random direction sits near p50;
- the EP forecast uses earlier trades only (a canary that includes the trade's own outcome raises).

## 8. Predictions, written before the run

1. NQ (development) earns a positive mean gross and clears N1-week.
2. **At most one of YM, RTY and ES passes Gate 1.**
3. **YM fails Gate 1** (its 10:00 direction reversed in D670).
4. More than 60 % of trades enter at 11:00.
5. V1 (the 15:00 cut) beats the primary on at least three of the four roots.
6. On NQ, V2 (the arm-like subset) earns more per trade than the rest.
7. ES's mean gross is below 2 bp.

## 9. Outputs

- `scripts/stage0_d673_formed_move.py`;
- `data/stage0_d673_formed_move.json`;
- a RESULT record with the component line.
