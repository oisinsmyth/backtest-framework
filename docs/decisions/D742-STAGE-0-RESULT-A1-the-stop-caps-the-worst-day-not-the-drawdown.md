# D742 STAGE 0 RESULT (step 3, amendment A1) — the 1.0 σ_rem stop: NOT SUPPORTED as a drawdown filter. It reliably caps the worst day (−\$1,142 → −\$587; better in every bootstrap draw, p 0.0001 against random exits), but its Calmar and max-DD gains are not robust (random-exit p 0.24; P(ΔCalmar > 0) 0.47) and come from 2022–23 alone

*2026-10-01.*
- *Design: [D742-A1](D742-STAGE-0-PRE-REG-the-oracle-of-a-protective-stop-on-the-floored-nq-follow.md#amendment-d742-a1-2026-10-01-step-2-the-principals-stop-and-its-test-declared-before-it-is-scored)
  (c2cdfca1), the principal's choices.*
- *Scorer: `scripts/stage0_d742_step3_stop.py` (fa8d91ae), one run, 0.1 min.*
- *Output: `data/stage0_d742_stop_test.json`.*
- *In-sample ≤ 2023-12-29; floor A, 546 trades, one MNQ.*

## 0. The audits

- **Re-proved first:** D727's known answers; A's 546 trades; step 1's 1.0 σ_rem total (\$12,883.85, to \$0.01).
- **The self-test:** a planted loser-cutting stop is found (random-exit p 0.0001; P(ΔCalmar > 0) 1.0), and a random
  partial exit is not (p 0.60).

## 1. The books

| | total | net / trade | max DD | Calmar | worst day |
|---|---:|---:|---:|---:|---:|
| no stop (A) | \$15,751 | +\$28.85 | \$4,131 | 3.81 | −\$1,142 |
| **1.0 σ_rem stop** | \$12,884 | +\$23.60 | \$2,872 | 4.49 | **−\$587** |

The stop exits 147 trades, 18 of them winners.

## 2. The tests

**The random-exit null:** 147 random trades, each exited at a uniform random minute, 10,000 draws.

| statistic | the stop | null p50 | null p95 (p05 for DD) | p |
|---|---:|---:|---:|---:|
| **R1 Calmar** (primary) | 4.49 | 3.49 | 6.25 | **0.236** |
| R2 worst day | −\$587 | −\$1,142 | −\$888 | **0.0001** |
| R3 max DD | \$2,872 | \$3,776 | \$2,447 | 0.147 |

**The paired month-block bootstrap:** 71 months, 10,000 draws.

| difference (stop minus none) | P(better) | p05 | p50 |
|---|---:|---:|---:|
| Calmar | **0.474** | −4.46 | −0.11 |
| worst day | **1.000** | +\$276 | +\$554 |
| max DD | 0.706 | −\$2,557 | −\$567 |

**The halves** (by trade count):

| half | span | Calmar, stop / none | max DD, stop / none | net, stop / none |
|---|---|---|---|---|
| first | 2018-02 → 2021-11 | **2.30 / 3.52** | \$1,916 / \$1,883 | \$4,414 / \$6,621 |
| second | 2021-11 → 2023-12 | 2.95 / 2.21 | **\$2,872 / \$4,131** | \$8,470 / \$9,130 |

**Gate 2 fails on all three legs:** random-exit p 0.236 > 0.05; P(ΔCalmar > 0) 0.47 < 0.90; and the first half is
worse with the stop.

**Gate 3:** EARNS (6 of 6 years; \$1,159 a year without the two best).

**Reading: NOT SUPPORTED.**

## 3. Predictions (D742-A1)

| # | prediction | outcome |
|---|---|---|
| 1 | random-exit p ≤ 0.05 | **Failed** (0.236) |
| 2 | P(ΔCalmar > 0) between 0.60 and 0.90 | **Failed**, lower (0.474) |
| 3 | P(Δworst day > 0) ≥ 0.95 | **Held** (1.000) |
| 4 | NOT SUPPORTED | **Held**, but on the random-exit leg as well as the bootstrap |

## 4. What it says

1. **The stop is a worst-day control, and a robust one.**
   - It halves the worst day (−\$1,142 → −\$587). Every bootstrap draw improves it (median +\$554), and random exits
     almost never match it (p 0.0001).
   - Under the stop no day can lose more than about 1 σ_rem plus slippage. That matters for a prop account's daily loss
     rules and for hurdle P's P3 (a 2 % day on \$50k is \$1,000).
2. **It is not a drawdown control.**
   - A's drawdown is a run of ordinary losing days, not one tail day.
   - The stop's max-DD and Calmar gains are not distinguishable from random exits of the same count (p 0.15, 0.24), and
     they flip sign across the bootstrap (P 0.47).
   - Its gain sits in the 2022–23 drawdown episode. In 2018–21 it costs \$2,207 of net and lowers Calmar.
3. **What it costs:** \$2,867 of net over six years (−\$5.25 a trade), the price of the 18 winners it cuts and the losers
   it cuts that would have recovered.
4. **For the principal.**
   - As a **risk rule** (cap the worst day), the 1.0 σ_rem stop is justified by mechanism and by this test. That is
     exits truncating the losers' tails, with p 0.0001 on the worst day.
   - As a **drawdown filter**, nothing tested so far (D741's MACD agreement, this stop) reduces A's \$4,131 drawdown
     reliably. The stopped book's \$2,872 is still above the \$50k account's \$2,000 trailing barrier.

## Addendum (2026-10-01): the principal keeps the stop as a risk rule; how the book overlaps D737 (POST HOC, descriptive)

**The principal:** "Ok keep the 1.0 σ_rem stop as a risk rule. I would like you to see how often it agrees / wants to
trade at the same time as the similar strategy that is in the vault."

**The comparison.** The similar vault line is [D737](D737-PRE-REG-nq-leads-the-dow-for-the-joint-vault.md) (D735's
YM k1.0 1σ_rem cell, slot 1): MNQ, entries 10:00–14:30, the same stop, held to 15:59.
- **The script:** `scripts/diag_d742_overlap_d737.py`, with output `data/diag_d742_overlap_d737.json`.
- **The rebuild:** D737's trades come from its own frozen functions (`cell`, `check_known`: 1,699 trades, D735's mean to
  1e-9). The book is floor A plus the 1.0 σ_rem stop, with D742's total re-proved.
- **The window:** in-sample only, A's window 2018-02 → 2023-12-29.
- **It tests nothing.** A test needs its own pre-registration.

**The overlap:**

| | |
|---|---:|
| A's trade days on which D737 also trades | **513 of 546 (94 %)** |
| D737's days (in A's window) on which A also trades | 513 of 1,282 (40 %) |
| same direction on the shared days | 77 % (393 days); opposite on 120 |
| entry timing on shared days | same minute 42 %, D737 first 40 %, A first 18 %; within 30 minutes 74 % |
| daily net correlation | 0.36 (all sessions), 0.45 (shared days) |

**Where each book's money is, in A's window** (net \$):

| days | A + stop | D737 |
|---|---:|---:|
| both trade, **same direction** (393) | **+\$13,142** (+\$33.4 a day) | **+\$43,450** (+\$110.6 a day) |
| both trade, **opposite** (120) | −\$1,042 | **−\$11,955** |
| only A trades (33) | +\$784 | — |
| only D737 trades (769) | — | **−\$5,877** |
| total | \$12,884 | \$25,619 |

**The books together** (A's window, one MNQ each):

| | Sharpe (Sortino) | max DD | worst day |
|---|---|---:|---:|
| A + stop | 0.92 (1.48) | \$2,872 | −\$587 |
| D737 | 1.31 (2.20) | \$2,690 | −\$609 |
| A + stop + D737 | 1.38 (2.38) | **\$3,925** | **−\$1,156** |

**What it says (descriptive):**
1. **The floored follow is nearly a subset of D737's days.** 94 % of its days are D737 days, mostly the same direction.
   By the principal's component rule (two constructions sharing a clock and largely a signal do not diversify), A is not
   a separate component next to D737. Holding both stacks risk: the drawdown rises to \$3,925 and the worst day to
   −\$1,156, for a Sharpe gain of 0.07.
2. **In-sample, D737's money is on the days the follow agrees with it.**
   - Where both point the same way, D737 makes +\$110 a day.
   - Where they disagree it loses \$100 a day, and on the 769 days the follow abstains (calm, or no |z| ≥ 1.5) it loses
     \$7.6 a day.
   - **POST HOC:** it suggests an agreement book (D737 traded only when the floored follow agrees), like D716's
     ES-agreement book. It was seen here, on the in-sample data. Only the vault, which is unseen for both, could test it,
     through its own pre-registration in a free slot on the principal's word. D737 itself stays frozen as it is.

## Addendum 2 (2026-10-01): the agreement lead recomputed point in time — declared before its script runs

**The principal:** "Run step 1".

**Why.** The split above labels a day "same" or "opposite" by the follow's **eventual** trade. On 40 % of the shared
days, D737 entered first. And a follow trigger opposite to D737 after D737's entry means the price had already moved
against D737. So the split is partly the outcome. The two forms below use only what is known at each entry.

**The script and the data.**
- **The script:** `scripts/diag_d742_agreement_pit.py`, with output `data/diag_d742_agreement_pit.json`.
- **D737's trades:** rebuilt with its own frozen functions (1,699 re-proved).
- **The follow's trigger:** at half-hours from 10:00, with the floor (σ\$ ≥ \$150, known before the open) and the
  1.0 σ_rem stop.
- **The window:** all of D737's in-sample, 2016-02 → 2023-12.

**PIT-1, the state at D737's entry** (D737 enters at its bar m₀'s open; the follow's trigger at t is known from minute
t). Each D737 trade falls into one of four classes:

| class | when |
|---|---|
| **floor off** | σ\$ < \$150, known at the open |
| **already agreed** | the floor is on, and the follow triggered at t ≤ m₀ in D737's direction |
| **already opposed** | the floor is on, and the follow triggered at t ≤ m₀ against D737's direction |
| **not yet** | the floor is on, and the follow has not triggered by m₀ |

For each class: the count, D737's mean and total net, and its win rate.

**PIT-2, wait for agreement.**
- Trade D737's direction only on days when both trigger the same way. Enter at the **later** of the two triggers:
  D737's own entry if the follow had already agreed; otherwise the open of the bar at the follow's trigger clock.
- One MNQ, D735's convention: the 1 σ_rem stop from that entry, else the 15:59 close, \$4.0671.
- Reported: the trades, the mean and total net, Sharpe and Sortino, the max DD, the worst day, and by year. D737 is
  given beside, on the same window.

**The decision rule, fixed now.** The lead **survives** only if both hold:
- **(a)** PIT-2's mean net per trade is ≥ D737's in-sample mean (+\$14.87) + \$10;
- **(b)** in PIT-1, D737's mean on **already agreed** exceeds its mean on **not yet** by ≥ \$10.

If both hold, step 2 follows: the power and a pre-registration on the principal's word. Otherwise the lead is closed.
Either way this is in-sample and post hoc, and nothing here is evidence for a vault claim.

### Addendum 2, the result: the rule as written reads SURVIVES, but the gain is the floor's, not the agreement's

**The checks.**
- D737's 1,699 trades and mean were re-proved.
- D737's own trades, re-priced by D742's `stop_exit`, equal its E1 gross on every trade, so the conventions agree.

**PIT-1, D737 by what was known at its entry** (2016-02 → 2023-12):

| state at D737's entry | trades | mean net | total | win rate |
|---|---:|---:|---:|---:|
| **floor off** (σ\$ < \$150, known at the open) | 725 | **+\$2.66** | \$1,926 | 0.47 |
| already agreed | 248 | +\$35.65 | \$8,841 | 0.57 |
| already opposed | 59 | **+\$48.14** | \$2,840 | 0.49 |
| not yet | 667 | +\$17.48 | \$11,656 | 0.52 |

**PIT-2, wait for agreement** (145 of its 393 entries move to the follow's later trigger), beside D737 and two post hoc
lines:

| book | trades | net / trade (median) | total | Sharpe (Sortino) | max DD | Calmar | worst day |
|---|---:|---|---:|---|---:|---:|---:|
| **PIT-2, the agreement book** | 393 | **+\$30.21** (+\$24.43) | \$11,871 | 0.90 (1.49) | \$1,687 | 7.04 | −\$587 |
| D737 as frozen | 1,699 | +\$14.87 (+\$0.93) | \$25,264 | **1.11 (1.85)** | \$2,690 | **9.39** | −\$609 |
| *POST HOC:* D737, floor on only | 974 | +\$23.96 (+\$14.43) | \$23,338 | 1.05 (1.76) | \$2,690 | 8.67 | −\$609 |
| *POST HOC:* D737, floor off only | 725 | +\$2.66 (−\$3.57) | \$1,926 | 0.37 (0.62) | \$1,537 | 1.25 | −\$148 |

**The declared rule:**
- (a) PIT-2's mean +\$30.21 ≥ +\$24.87: holds.
- (b) agreed minus not yet = +\$18.17 ≥ \$10: holds.
- **As written, the lead SURVIVES.**

**What the full table says** (my rule was incomplete: it judged only the mean per trade):
1. **The agreement book is not better as a book.** It has a higher mean per trade but less than half D737's total, a lower
   Sharpe (0.90 against 1.11) and a lower Calmar (7.04 against 9.39). The per-trade gain is bought by dropping trades
   that also earn.
2. **The agreement mechanism does not hold point in time.** D737 does better when the follow had already gone the
   **other** way (+\$48.14, 59 trades) than when it had already agreed (+\$35.65). The eventual-trade split in the
   first addendum (+\$43k against −\$12k) was mostly the outcome showing in the label.
3. **The floor carries it.**
   - **Floor off:** D737's 725 trades on days with σ\$ < \$150 (known before the open) net +\$2.66 a trade: break-even
     trading, which the principal's standard rejects.
   - **Floor on:** its 974 trades carry \$23,338 of its \$25,264 (92 %).
   - **The overlap with the follow's floor:** the "A abstains" losses in the first addendum were mostly these calm days.
   - The floor-on line is post hoc: the floor was found on the follow and is applied to D737 here after being seen.

**Reading.** The agreement lead is **closed**. Its declared rule passed, but it is not a better book and its mechanism
reverses point in time. What remains is a post hoc observation: D737, like the follow, earns only when the daily range
is large enough. D737 stays frozen. Scoring D737 with the floor in the vault would need its own pre-registration in a
free slot, on the principal's word.
   - The drawdown is the cost of a regime-shaped edge traded at one micro. The options are the account size (\$150k), or
     accepting it.

## CLOSED (2026-10-01): the floored NQ follow with its stop; D737 left as frozen

**The principal:** "My leaning is to close the follow plus stop and leave D737 as is", then "Write it".

**What is closed.** D727's NQ follow is closed as a line, with D740's floor A and this record's 1.0 σ_rem stop. That
covers [D738](D738-STAGE-0-RESULT-A1-no-filter-beats-its-rotation-null.md),
[D740](D740-STAGE-0-RESULT-the-floor-picks-the-years-and-the-monthly-trend-adds-nothing.md),
[D741](D741-STAGE-0-RESULT-the-macd-agreement-drops-the-best-trades.md) and this record. No vault slot is taken.

**Why:**
1. **It is not a separate component.** 94 % of its days are D737's, on the same clock and mostly the same side.
   Holding both raised the max DD to \$3,925 for a Sharpe gain of 0.07 (addendum 1).
2. **It is still the follow the principal declined as a strategy.** The floor and the stop make it selective and cap
   its worst day, but they give it no entry signal.
3. **Every number that recommends it is in-sample, after about 50 looks.** The floor was seen before it was tested.

**D737 is untouched.** It stays frozen in slot 1 and is scored in the joint run on its own rule. The agreement lead is
closed (addendum 2).

**Kept as lessons, not as a book:**
- **Abstain when the day's volatility cannot cover the fee.** The floor σ\$ ≥ \$150 separated the follow's earning and
  break-even regimes (D740). Post hoc, D737 shows the same split: +\$2.66 a trade below the floor, 92 % of its net above
  it.
- **A volatility-scaled stop caps the worst day** (random-exit p 0.0001), **but it does not fix a regime-shaped
  drawdown** (Calmar p 0.24).
- **A rule judged on the mean per trade alone can pass while the book gets worse.** Declare book-level statistics
  (total, Sharpe, Calmar) in every decision rule (addendum 2).

**A monitor item, not a test.** On the forward data the other session already records for D737
(`data/forward/d737_forward.csv`), split D737's forward trades by floor on and floor off (σ\$ ≥ \$150 at the open). This
watches the floor observation on unseen sessions. It changes nothing in D737's rule or its vault scoring, and it is read
only after enough forward sessions to say anything.
