# D740 STAGE 0 PRE-REGISTRATION — two filters on D727's NQ follow, designed by the principal: a fixed volatility floor, and agreement with the 20-day SMA's three-day direction

*2026-10-01.*
- *The principal: "Ok lets do a volatility floor and a higher time frame agreement filter?"*
- *Design choices, all the principal's:*
  - the higher time frame is a "3 day concurrent SMA change that agree with the signals direction", read as **the
    20-day SMA moved the trade's way on each of the last three sessions**;
  - test each alone and both together;
  - in-sample now, with a vault decision later.
- *Numbered D740 after telling the other session.*
- ***Committed alone, before its runner exists.** In-sample only (≤ 2023-12-29).*

## 0. Context and what is already known

- **The follow:** [D727](D727-STAGE-0-RESULT-nq-continues-from-the-open-alone.md)'s NQ book. At the first half hour
  from 10:00 at which |z| ≥ 1.5, one MNQ goes the drift's way, held to 15:59, at \$4.0671 a round trip; 1,024 trades,
  2016-02 → 2023-12.
- **Its learned expected-profit filters failed:** [D738-A1](D738-STAGE-0-RESULT-A1-no-filter-beats-its-rotation-null.md).
- **The post hoc diagnosis by two independent analyses** (Opus; a Fable 5.1 agent; their notes are in
  `temp/d738diag_opus/` and `temp/d738_fable/`):
  - the volatility information is regime-level;
  - a fixed floor keeps 2016–17 in play;
  - a filter should also be scored in σ-normalised units, against a within-year null.

**Disclosed: Filter A's in-sample result is already known.** It is Fable's post hoc idea 2, which I re-checked:
- σ\$ ≥ \$150 keeps 546 trades, at +\$28.85 against −\$0.34 for those dropped;
- exact rotation p 0.020 in dollars, 0.047 in y;
- 0 / 0 / 10 trades in 2016 / 2017 / 2019.

**Its in-sample reading is therefore descriptive, not evidence.** Filter B has not been scored on this book by anyone.

## 1. The object

**The trades:** D727's k 1.5 book, rebuilt through D738's functions:
- `read_cut` (a chunked read keeping day ≤ 2023-12-29), `panel_from_raw`, `objects`, `book`;
- D727's recorded k 0.5 / 1.0 / 1.5 answers checked to 1e-6 first;
- D727's lag audit and its canary.

**The window** is every k 1.5 trade whose Filter B state is defined: all but the first ~23 sessions of the panel. The
count is reported.

**No fitted parameter and no burn-in:** both filters are fixed rules.

## 2. The filters

**A — the volatility floor.** Take the trade iff σ\$ = σ_oc × \$2 ≥ **\$150**.
- σ_oc is D727's own: the RMS of the prior 20 sessions' open-to-close move.
- \$150 comes from D727's published curve: 2 × \$4.0671 ÷ (β₁₀:₀₀ 0.130 × k 1.5 × √(30/390)) = \$150.4, rounded.
- It is the daily scale at which the follow's average 10:00 continuation covers twice the fee.

**B — agreement with the higher time frame.**

*The series.* A continuous NQ daily close series:
- c_d − c_{d−1} = the 15:59 close minus the previous session's 15:59 close, within one contract;
- on a roll day it is that day's own open-to-close, which drops the roll gap.

*The state at session t* (closes through t − 1 only, so known before the open):
- **UP** iff SMA20 rose on each of t − 1, t − 2 and t − 3. Because SMA20 rises on day d iff c_d > c_{d−20}, UP means
  c_{t−1} > c_{t−21}, c_{t−2} > c_{t−22} and c_{t−3} > c_{t−23}.
- **DOWN** is the mirror.
- **MIXED** otherwise.

*The rule.* Take the trade iff (side = long and UP) or (side = short and DOWN). MIXED sessions and trades against the
trend are not taken.

**C = A and B.**

**Reported beside, not gated:**
- the trades **against** the trend (long in DOWN, short in UP);
- the **MIXED** trades.

## 3. What is reported (per filter, and for take-all on the same window)

- **All four groups** (CLAUDE.md):
  - net and gross, Sharpe and Sortino, max DD;
  - share of sessions in the market;
  - the trade distribution with both-tail trims;
  - by year;
  - nulls as distributions (p50 and p95).
- The mean **y = gross / σ\$** (the pass-through) of the kept and the dropped trades.

## 4. The nulls and the gates

**The nulls, for each filter's take mask over the window's trades:**
- **The exact time rotation:** every circular offset, enumerated, which keeps the mask's count and clustering. Its
  statistics:
  - **S1** = mean net per kept trade;
  - **S2** = mean y per kept trade.
- **The within-year permutation:** the mask shuffled inside each calendar year, count-matched per year, 10,000 draws,
  seed 740. It measures day-level information inside a regime, and is reported on S1 and S2.

**Multiplicity.**
- **Holm across B and C only,** on S1's rotation p. These are the two tests whose answers are unknown.
- **A is reported with its raw p and labelled POST HOC (known).** Its in-sample reading carries no evidential weight.

| gate | standard |
|---|---|
| **Gate 1 (mechanism, gross)** | take-all on the window has mean gross > 0 with Newey–West t ≥ 2 (5 lags) |
| **Gate 2 (the filter, net)** | the filter's mean net per trade > take-all's, and S1's rotation p ≤ 0.05 (Holm-adjusted for B and C; raw for A) |
| **Gate 3 (the principal's standard, with abstention)** | D736's G1–G3 over traded years only. A traded year has ≥ 10 kept trades; other years are abstention years, excluded from G1–G3, with their net kept in every total. Fewer than four traded years reads UNDEFINED |

**Flag:** SIZE-CARRIED if S1 passes and S2's rotation p > 0.05.

**Readings:**

| reading | when |
|---|---|
| **SUPPORTED** | Gates 1, 2 and 3 hold |
| **FILTER ONLY** | Gates 1 and 2 hold, and Gate 3 fails |
| **NOT SUPPORTED** | Gate 2 fails |
| **NO MECHANISM** | Gate 1 fails |

For A, SUPPORTED means "in-sample consistent", nothing more.

**Power, stated before the run.**
- The per-trade net sd is about \$211.
- Keeping half of about 1,000 trades, the iid SE of the kept-minus-all mean is about \$6.6.
- 80 % power at a one-sided p 0.05 needs a lift of about \$16 a trade (about \$19 after Holm for two).

## 5. Predictions

| # | prediction |
|---|---|
| 1 | B keeps between 35 % and 55 % of the trades (MIXED takes a share) |
| 2 | B reads NOT SUPPORTED. The 20-day trend carries little day-level information about the afternoon's continuation (D724: NQ respects no intraday mean; D728: NQ continues more against the complex) |
| 3 | the against-trend trades have a positive mean net (the follow works against the monthly trend too) |
| 4 | C keeps fewer than 350 trades and has the highest mean net per trade of A, B and C |
| 5 | C's Gate 3 reads EARNS with 2016 and 2017 as abstention years |

## 6. Mechanics, and what follows

**The runner** is `scripts/stage0_d740_floor_and_htf.py`.
- **Its point-in-time audit:** a second implementation of the continuous close and the UP/DOWN state from the raw
  minute rows, on sampled sessions. A canary that includes session t's own close must raise.
- **Its sign audit:** sampled trades re-priced from the raw rows.
- **Its self-test** (synthetic) must show four things:
  - a planted agreement effect is found by both nulls;
  - a random mask sits near p 0.5;
  - the roll-day adjustment removes a planted roll gap;
  - the SMA rule is the c_{t−1} > c_{t−21} identity.
- **Its output** is `data/stage0_d740_floor_and_htf.json`, run once, aggregates only.

**What follows.** If B or C reads SUPPORTED, the next step is the principal's: a frozen vault pre-registration in a
free programme slot (2 or 10). NQ's 2024+ is unread for this question, and the joint run would be its first look. A is
not in-sample evidence; it would go only with that vault step.
