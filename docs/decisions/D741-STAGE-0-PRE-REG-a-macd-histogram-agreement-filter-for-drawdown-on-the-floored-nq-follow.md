# D741 STAGE 0 PRE-REGISTRATION — does a 30-minute log-MACD histogram that agrees with the trade cut the floored NQ follow's drawdown more than dropping the same number of trades at random?

*2026-10-01.*
- *The principal: "Ok we keep (A), we need something for drawdown, how about MACD histo agrees with dirrection?"*
- *Design choices, all the principal's:*
  - 30-minute bars;
  - log-MACD 12/26/9;
  - agreement means the histogram's sign agrees with the trade.
- *Numbered D741 after telling the other session.*
- ***Committed alone, before its runner exists.** In-sample only (≤ 2023-12-29).*

## 0. The base and the question

**The base** is [D740](D740-STAGE-0-RESULT-the-floor-picks-the-years-and-the-monthly-trend-adds-nothing.md)'s
filter **A**:
- D727's k 1.5 NQ follow, taken only when σ\$ = σ_oc × \$2 ≥ \$150;
- 546 trades, +\$28.85 a trade, Sharpe 0.87 (Sortino 1.27), **max drawdown \$4,131** (in 2020–22);
- in-sample and post hoc, kept by the principal.

**The question is the drawdown, not the mean.**
- Any filter that drops trades shrinks a drawdown just by trading less.
- So the MACD filter is judged against **masks that drop the same number of A's trades**, on a statistic that rewards
  a smaller drawdown only when the net survives it: **Calmar = total net / max drawdown** (daily net, one MNQ).

## 1. The filter (M = A and MACD agreement)

**The bars.** NQ's day-session minutes (09:30–15:59) are read through D738's `read_cut` (keeping day ≤ 2023-12-29).
- **13 thirty-minute bars a session:** 09:30–09:59, …, 15:30–15:59. Each bar's close is the last minute's close,
  forward-filled.
- **A continuous log-close series across sessions:**
  - within a contract, each bar's change is log(close) − log(previous bar's close), including the overnight step
    between sessions;
  - on a roll day, the first bar's change is log(close) − log(that day's 09:30 open), which drops the roll gap.
- **The MACD:** EMA12 − EMA26 of that series (pandas `ewm(span, adjust=False)`); the signal is EMA9 of the MACD; the
  **histogram** is the MACD minus the signal.

**At the entry** (the first half hour t from 10:00 at which |z| ≥ 1.5):
- the last **completed** bar is the one ending at t;
- its close is P_t, the follow's own entry price, so the histogram is known at the fill.

**The rule:** **keep A's trade iff sign(histogram) = the trade's side.** A zero histogram is not kept.

**Reported beside:** the A trades the filter drops (the histogram against the trade).

## 2. What is reported

- **For A, M and the dropped set, on the same session calendar:** the four groups (net and gross, Sharpe and Sortino,
  max DD, share in the market, the trade distribution with trims, by year), plus **Calmar**, the **worst day**, and the
  **longest drawdown** in sessions.

## 3. The nulls and the gates

**The nulls**, for M's take mask over A's 546 trades in session order:
- **The exact time rotation:** all 546 circular offsets. It keeps the count and the clustering.
- **The within-year permutation:** count-matched per calendar year, 10,000 draws, seed 741.

**Their statistics:**
- **C1** = Calmar (primary);
- **C2** = max drawdown, where lower is better (reported);
- **S1** = mean net per kept trade (reported).
- A p-value is the share of null masks at least as good as M: C1 ≥, C2 ≤, S1 ≥.

| gate | standard |
|---|---|
| **Gate 1 (mechanism, gross)** | A's trades have mean gross > 0 with NW t ≥ 2 (5 lags) |
| **Gate 2 (drawdown)** | M's max DD < A's (\$4,131), **and** M's Calmar > A's, **and** C1's rotation p ≤ 0.05. This is the only test, so there is no multiplicity correction |
| **Gate 3 (the principal's standard, with abstention)** | as in D740: D736's G1–G3 over traded years (≥ 10 kept trades) |

**Readings:**

| reading | when |
|---|---|
| **SUPPORTED** | Gates 1, 2 and 3 hold |
| **DRAWDOWN ONLY** | Gates 1 and 2 hold, and Gate 3 fails |
| **NOT SUPPORTED** | Gate 2 fails |
| **NO MECHANISM** | Gate 1 fails |

**Within-year C1 is reported, not gated.** It shows whether the cut is day-level or regime-level.

**Power, stated before the run.** A max drawdown is a single extreme path statistic, and its null spread is wide. An
in-sample Calmar gain must be large to clear p 0.05: a drawdown cut of roughly a third with the net largely intact.

## 4. Predictions

| # | prediction |
|---|---|
| 1 | M keeps **60–85 %** of A's trades. The follow enters after a sized move, which the 30-minute histogram will usually share |
| 2 | M's max DD is below A's \$4,131 |
| 3 | C1's rotation p > 0.05: **NOT SUPPORTED**. An indicator built from the move that triggered the trade adds little beyond the trigger |
| 4 | the dropped trades' mean net is below the kept trades' |

## 5. Mechanics

**The runner** is `scripts/stage0_d741_macd_drawdown.py`.
- It rebuilds the follow, D727's known answers and D740's A count of 546 trades.
- **Its point-in-time audit:** a second implementation recomputes the histogram from a series truncated at the entry
  bar, on sampled trades. A canary that reads the next bar must change the values and raise.
- **Its self-test** (synthetic) must show four things:
  - the EMA and MACD against an explicit loop;
  - the roll-gap removal;
  - a planted drawdown-cutting mask found by the rotation null;
  - a random mask centred.
- **Its output** is `data/stage0_d741_macd_drawdown.json`, run once, aggregates only.

**What follows.** If M reads SUPPORTED, the floored follow with the MACD agreement is the candidate for a vault
pre-registration, in a free slot (2 or 10) on the principal's word. A itself is post hoc, so the vault would be the
first clean look at both.
