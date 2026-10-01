# D742 STAGE 0 PRE-REGISTRATION — step 1 of a protective stop for the floored NQ follow's drawdown: how far the trades go against them, and what a volatility-scaled stop would have done (descriptive; no stop chosen)

*2026-10-01.*
- *The principal: "Ok lets look at 1": a protective stop scaled to volatility, aimed at the floored follow's drawdown,
  oracle first.*
- *Numbered D742 after telling the other session.*
- ***Committed alone, before its runner exists.** In-sample only (≤ 2023-12-29).*

## 0. The book and the three steps

**The book:** [D740](D740-STAGE-0-RESULT-the-floor-picks-the-years-and-the-monthly-trend-adds-nothing.md)'s A, kept by
the principal.
- D727's k 1.5 NQ follow, only when σ\$ ≥ \$150.
- 546 trades, +\$28.85 a trade, Sharpe 0.87 (Sortino 1.27).
- **Max DD \$4,131, worst day −\$1,142, longest drawdown 162 sessions** ([D741](D741-STAGE-0-RESULT-the-macd-agreement-drops-the-best-trades.md)).

**The steps** (the principal's rule for filters and exits, 2026-09-29):

| step | what | where |
|---|---|---|
| **1** | the excursion profile and the stop curve | this record |
| 2 | the stop's form and width, chosen **with the principal** | an amendment, before any stop is tested |
| 3 | the chosen stop scored against a null | after step 2 |

## 1. The convention (D735's, unchanged)

- **The entry** is at P_t, the close of the bar starting t − 1, at D727's first-crossing clock t. The trade is then
  watched on the one-minute bars from t to 15:59.
- **A stop w σ_rem away from the entry,** where σ_rem = σ_oc × √((390 − m) / 390) and m is the entry's minute after
  09:30:
  - it is touched when a bar's low (for a long) or high (for a short) reaches it;
  - it fills at the stop less one tick (0.25 points), or at that bar's open less a tick if the bar opens beyond it;
  - otherwise the trade exits at the 15:59 close.
- One MNQ, \$4.0671 a round trip.

## 2. What is reported (descriptive; nothing is chosen)

**A. The excursions, on A's 546 trades.**
- **MAE and MFE**, the maximum adverse and favourable excursions from the entry to 15:59, in σ_rem units and in
  dollars. Distributions are given for winners and losers separately (on the unstopped net).
- **The share of winners and of losers whose MAE reaches** 0.25, 0.5, 0.75, 1.0, 1.5 and 2.0 σ_rem. The winners are
  what a stop would cut wrongly; the losers are what it would cut rightly.
- **When the MAE happens:** the share of losers whose worst point comes in the last hour, against before it.
- **The worst 5 % of trades by net:** their MAE, and whether they were already worse than −1σ_rem by 12:00.

**B. The ceilings.**
- **The perfect exit:** every losing trade flat at −cost. Its net, max DD and Calmar.
- **The size of the prize:** the unstopped book's total loss on losing trades, and on its worst 20 days.

**C. The stop curve.**
- **Grid:** w ∈ {0.5, 0.75, 1.0, 1.25, 1.5, 2.0} σ_rem, plus none.
- **Per width:**
  - trades stopped, and winners stopped;
  - net and gross, the mean (median) per trade, Sharpe and Sortino;
  - **max DD, Calmar, the worst day, the longest drawdown**;
  - by year;
  - D736's standard with abstention.
- **This is a description of the curve, not a test.** Choosing a width from it would be selection. Step 2 records
  the choice and step 3 scores it.

## 3. The audits

- **The trades:**
  - D727's three known answers, to 1e-6;
  - D740's A count of 546;
  - D727's lag audit and its canary.
- **The stop simulation:**
  - it is checked against D735's `e1_tables` convention, on a synthetic panel where both implementations run;
  - a canary that starts the scan one bar early (the entry bar itself) must change the results;
  - a gap-through fill must be at the open less a tick.
- **Sign:** sampled trades re-priced from the raw rows. A long whose stop is hit loses (stop − entry − tick) × \$2 less
  the cost.

## 4. Predictions

| # | prediction |
|---|---|
| 1 | the winners' median MAE is below 0.5 σ_rem, and the losers' median above 0.8 σ_rem |
| 2 | a 1 σ_rem stop stops 20–35 % of A's trades |
| 3 | at least one width cuts the max DD below \$3,000 while keeping Calmar ≥ A's 3.81 |
| 4 | the 0.5 σ_rem stop lowers the mean net by more than \$10 a trade (it cuts too many winners) |
| 5 | every width ≤ 1.5 σ_rem cuts the worst day (−\$1,142) by at least a third |

## 5. Mechanics

- **The runner** is `scripts/stage0_d742_stop_oracle.py`, built on D738's `read_cut`, `book` and the panel functions,
  and on D740's floor.
- **Its output** is `data/stage0_d742_stop_oracle.json`, run once, aggregates only.
- **Its self-test** must show that the stop simulation agrees with D735's convention on a synthetic panel, and that its
  canaries fire.

## Amendment D742-A1 (2026-10-01): step 2, the principal's stop and its test, declared before it is scored

**The principal's choices**, after step 1's
[result](D742-STAGE-0-RESULT-losers-go-far-against-winners-do-not.md):
- **The stop:** **1.0 σ_rem**, D735's convention as in §1.
- **The test:** "Random-exit null + bootstrap".

**Disclosed:** step 1 already shows this stop's in-sample book:

| book | Calmar | max DD | worst day | net / trade |
|---|---:|---:|---:|---:|
| the 1.0 σ_rem stop | 4.49 | \$2,872 | −\$587 | +\$23.60 |
| no stop | 3.81 | \$4,131 | −\$1,142 | +\$28.85 |

What is unknown is how these compare with the nulls below.

**A1.1 The random-exit null (does the stop choose the right trades and moments?).**
- **Each draw** picks **147 of A's 546 trades at random** (the stop's own count). Each picked trade exits at a minute
  drawn uniformly from its entry minute to 15:59, at that minute's close less one tick against the trade. Every other
  trade runs to 15:59.
- **10,000 draws, seed 7421.**
- **The statistics:**
  - **R1** = Calmar (primary);
  - **R2** = the worst day;
  - **R3** = the max DD.
- **p** = the share of draws at least as good as the stop.

**A1.2 The paired block bootstrap (is the gain over no stop robust to the sample?).**
- **Blocks:** calendar months of the session calendar, from A's first trade to 2023-12-29, drawn with replacement.
  Each draw has as many months as the window, and the stopped and unstopped daily series are drawn together.
- **10,000 draws, seed 7422.**
- **Reported:** P(ΔCalmar > 0), P(Δworst day > 0) and P(Δmax DD < 0), where Δ means the stop minus no stop, and the
  5th and 50th percentiles of each.

**A1.3 The halves.** A's trades are split by count into two halves, and the Calmar is read with and without the stop
in each.

**The gates** (Gate 1, the mechanism, holds already: NW t 2.79 on A's gross, D741):

| gate | standard |
|---|---|
| **Gate 2** | R1's random-exit p ≤ 0.05, **and** the bootstrap's P(ΔCalmar > 0) ≥ 0.90, **and** the stop's Calmar exceeds no stop's in **both** halves |
| **Gate 3** | the principal's standard with abstention (D740) on the stopped book |

**Readings:** SUPPORTED (Gates 2 and 3 hold) or NOT SUPPORTED (Gate 2 fails). If only Gate 3 fails, the reading is
DRAWDOWN ONLY.

**Predictions:**

| # | prediction |
|---|---|
| 1 | R1's random-exit p ≤ 0.05: the stop chooses the losers, which random exits cannot |
| 2 | the bootstrap's P(ΔCalmar > 0) is between 0.60 and 0.90. A drawdown is a single-path statistic, so its gain is noisy |
| 3 | P(Δworst day > 0) ≥ 0.95 |
| 4 | the reading is **NOT SUPPORTED**, on prediction 2 |

**Mechanics.**
- **The runner** is `scripts/stage0_d742_step3_stop.py`, using the step-1 runner's `stop_exit` and the trades.
- **It re-proves step 1's 1.0 σ_rem total** (\$12,884; to \$0.01) before any null.
- **Its output** is `data/stage0_d742_stop_test.json`, run once.
