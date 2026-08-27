# D231 — The exposure dial

**Status:** Pre-registered — committed BEFORE the holdout fixture exists
**Date:** 2026-08-27
**Area:** Strategy research

---

## The request, and why it needs a different family

*"I can't accept a 50% exposure."*

The arm sits in the market **49.9%** of the time, and that is not incidental — it is
structural. `hist = md − sma(md, 9k)` has a kernel that sums to zero, so its sign is positive
about half the time **at any window and any sampling rate**. Measured, before this record:

| construction | exposure |
|---|---:|
| I1 `(34,9)` daily — the arm | 49.9% |
| I1 `(68,18)` daily | 50.9% |
| I0 jerk | 48.5% |
| 15m `k=4` parent (D226) | 49.7% |

**No change of timeframe or window can move this**, which is why the originally proposed
"hourly k=24" would not have answered the request. (It is also infeasible on ETF hourly bars:
a 24,379-bar warm-up against 14,014 available.)

Only two things move exposure: an **AND condition** (a gate — six studies, all failed, and
D228 explains why), or **raising the bar the signal must clear**. This study is the second.

---

## The two families

Both read the same normalised score, and neither is a gate — they raise the threshold on the
signal itself rather than adding an unrelated condition.

```
z[t] = hist[t] / trailing_sd(hist, 252)     # strictly trailing, inclusive of bar t
```

| family | rule | dial |
|---|---|---|
| **T — threshold** | hold when `z > c` | `c`, a time-series bar each symbol clears alone |
| **N — top-N** | hold the strongest `N` of the universe among those with `z > 0` | `N`, a cross-sectional bar |

They differ in a way worth separating: **T is independent per symbol; N is relative.** D228's
S5 hinted the cross-section might carry information and that hint was never tested cleanly.

### The calibration is free, and the constants are pinned here

Fixing a threshold to hit an exposure target reads **the position series and never a return**,
so it is free under D228's boundary. Calibrated on the mined 57-ETF fixture and **pinned before
any P&L is computed**:

| target exposure | `c` (family T) | achieved | universe fraction (family N) | achieved |
|---:|---:|---:|---:|---:|
| 40% | **0.230** | 39.9% | **0.544** (31 of 57) | 39.9% |
| 30% | **0.490** | 30.0% | **0.351** (20 of 57) | 29.5% |
| 20% | **0.815** | 20.0% | **0.228** (13 of 57) | 20.6% |
| 10% | **1.320** | 10.0% | **0.105** (6 of 57) | 10.1% |

Family N is declared as a **fraction of the universe**, not a count, so the rule transfers to a
60-symbol holdout without a second calibration: counts become 33, 21, 14, 6.

**`NORM_WINDOW = 252`.** Declared here rather than discovered later — D228 was caught by
leaving `MEDIAN_WINDOW` unpinned.

### PRE-RUN AMENDMENT — family T must self-calibrate too

*Written before the holdout fixture was built and before any cell was scored. Prompted by the
question "how are you going to hit that target?", which the section above does not actually
answer for family T.*

**The defect.** Family N is a **rank** rule, so holding the strongest 35% of the universe
produces ~35% exposure on *any* fixture, automatically. Family T's `c` values above were fitted
to the **mined** fixture's z-distribution; applied to 60 different ETFs they land wherever they
land. That makes exposure a **control** for N and an **outcome** for T — the two families would
not be comparable, and T's "four levels" would not be four levels of anything.

**The fix.** Family T becomes self-calibrating on the same principle as N:

```
c[i,t] = the (1 - target) quantile of z[i, t-252 .. t-1]     # per symbol, strictly trailing
hold when z[i,t] > c[i,t]
```

A rolling 252-bar quantile of each symbol's own z. Exposure is then ≈ target **by
construction**, with no look-ahead and no dependence on any other fixture.

**This is strictly better than what it replaces, for a reason beyond comparability: it removes
every trace of mined-fixture information from the holdout test.** The constants in the table
above are demoted to a **sanity reference** — the holdout's own fitted thresholds should land
near them if the two universes are similar, and a large divergence is itself worth reporting.
Nothing operative is inherited.

**The cost, stated:** `c` is now time-varying rather than fixed, so family T is a slightly
different estimator than the one first described. The dial it turns — target exposure — is
unchanged, and that is what the study is about.

### Additional prediction, committed with this amendment

| | prediction | confidence |
|---|---|---|
| **Y6** | **Excess Sharpe is monotone decreasing in the dial: 40% best of the four, 10% worst, and the drop from 40% to 10% exceeds 0.20 Sharpe.** Not tautological with Y2 — a selection effect strong enough to beat the concentration and cost penalties would make this **U-shaped** instead, with a middle level best | **moderate** |

The reasoning, so it can be checked against the outcome: **D228's S2 sized positions by
normalised `|hist|` and returned −0.019.** A threshold is the hard version of exactly that idea.
If the soft version was neutral-to-negative, the hard version should be worse, and worse
monotonically as the bar rises — because concentration and cost both worsen as exposure falls
while the selection effect apparently does not pay.

---

## Where it runs, and why not here

**On the holdout, not the mined fixture.** This is not procedure, it is arithmetic: D228's
best-of-search null puts the detection floor on the mined fixture at **+0.104**, and D230 showed
the arm's own advantage there has a **±0.5** interval. Eight more cells on that fixture would
produce eight more numbers inside the noise. It cannot answer.

The holdout is 60 ETFs chosen by a rule committed before it ran (`scripts/fetch_etf_holdout.py`),
on the parent's exact date grid — same period, different instruments.

**This record is committed before the fixture is built.** Pre-registering against data that does
not yet exist is the strongest form available and it should be said plainly, because the
programme has not managed it before.

---

## D228's stop, overridden in writing

D228's stop reads: *"the filter line on this arm is closed. No ninth candidate, no widened
sweep, no second fixture for the same question."* **This study violates it, deliberately, and
D214's pattern requires that be recorded rather than done quietly.**

**The reasoning, both sides:**

- **Against.** D228's mechanism — money delta tracks exposure delta at **r = +0.823**, slope
  0.58 pp per pp — predicts every cell below will lose money to the parent, and the two gates
  that cut exposure hardest lost 35.7 and 43.9 points. The prior that this fails is strong.
- **For, and it is a real argument.** Every prior filter was judged on **money**, and money is
  the wrong metric if the book is to be levered. What leverage converts is **Sharpe**. A book at
  20% exposure with a higher Sharpe can be levered harder than one at 50%, and ends up ahead at
  matched risk *even though it loses on unlevered money*. **No prior study tested that**, because
  all of them measured the thing leverage makes irrelevant.
- **And the family is genuinely new.** D229 explicitly set the threshold idea aside as *"not a
  rescue — a second study"*. This is that study, on fresh data, with the dial declared.

The override is scoped: **this record only.** D228's stop otherwise stands.

---

## Hurdles

- **X (carries the verdict).** Beat the unfiltered parent on **excess Sharpe at `rf = 4%`,
  charged on the exposed fraction**, on the holdout.
- **B.** Clear a **best-of-search null** over the 8 declared cells — D228's construction reused
  unchanged, one offset vector per replication shared across cells.
- **E.** ≥100 pooled signals and ≥30 entries per symbol. **Expected to fail at the 10% level**
  and possibly at 20%; declared now so a failure there is not read as a surprise.
- **Money is reported and is NOT a hurdle.** This is the deliberate break with D217's hurdle D
  and it is the point of the study. A cell that loses unlevered money while raising Sharpe is a
  **pass**, because leverage converts the second into the first.

### The presentation that answers the actual question

Every cell is reported **levered to buy-and-hold's volatility with financing charged at `rf`**:

```
levered return  =  rf  +  (vol_bh / vol_cell) x excess_return_cell
```

**Stated honestly: this is a monotone transform of excess Sharpe, not independent evidence.**
It ranks cells identically to hurdle X. It is reported because it converts a ratio into money at
constant risk, which is the form the question was asked in.

---

## Predictions

| | prediction | confidence |
|---|---|---|
| **Y1** | **Every cell loses unlevered money to the parent**, and the loss is roughly linear in exposure at D228's 0.58 pp per pp | **high** |
| **Y2** | **No cell clears hurdle X.** Raising the bar removes trades that were, on average, as good as the ones kept | **moderate-high** |
| **Y3** | **The 10% cells fail hurdle E** on entries per symbol | **moderate-high** |
| **Y4** | **Family N beats family T** at matched exposure on excess Sharpe — the cross-sectional bar carries information the per-symbol bar does not | **low-moderate** |
| **Y5** | **Nothing clears hurdle B** | **moderate-high** |

Y2 is the one that matters. **If it is falsified — if a lower-exposure book has a genuinely
higher Sharpe on fresh data — that is the first positive this programme has produced**, and it
would be on pre-registered hurdles against data selected by a rule fixed in advance. It would
deserve more scrutiny than a failure, not less.

Y4 is deliberately low-confidence: it is the one prediction here I have no mechanism for.

---

## The stop

**If no cell clears X, the exposure dial is closed** and the answer to *"can this arm be made
more selective"* is a measured no, on fresh data, across two families and four levels.

**If a cell clears X and B**, it is still not finished: it becomes a single named configuration
with a stated exposure, and the next step is **forward time** — the only remaining source of
independent data once the holdout is spent.

---

## Reuse — D212 is binding

| need | reuse | from |
|---|---|---|
| best-of-search null, rf-on-exposure, scoring | `best_of_search_null`, `excess_sharpe`, `score` | `scripts/run_filter_search.py` |
| the arm, panel, costs, buy-and-hold | `arm_positions`, `load_panel`, `portfolio_log_returns`, `buy_and_hold` | `run_jerk_rung.py`, `run_macd_ladder.py` |
| trailing sd (already look-ahead tested) | `trailing_std` | `scripts/run_filter_search.py` |
| paired bootstrap for the interval | `paired_block_bootstrap` | `scripts/run_jerk_rung.py` |

**Written fresh:** the holdout panel loader (the parent's is hardcoded to its own fixture and
dividend sidecar) and the two dial constructions.
