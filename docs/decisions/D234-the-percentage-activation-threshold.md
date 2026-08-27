# D234 — The percentage activation threshold

**Status:** Pre-registered — committed BEFORE any runner exists
**Date:** 2026-08-27
**Area:** Strategy research

---

## Why this is not a tenth filter study

D228's stop reads *"the filter line on this arm is closed."* **This overrides it, in writing,
under D214's pattern**, and the justification is specific rather than general.

Nine studies filtered on **`hist`** — the acceleration rung — and D233 established why they all
failed: **`hist` carries one bit, its sign.** Above zero there is no reliable gradient; below
zero there is none either, and the marginal bars are the worst.

**This study does not filter on `hist`.** It gates on **`md_L`**, the *level* rung, which is a
different quantity carrying its own (weak) information — D218 measured `I2` standalone at
**+0.129**. Conjoining a strong bit with a weak one is not the same operation as trying to
extract a second bit from the strong one.

**And it was untriable before.** The published `md` is measured in dollars, so a level threshold
on it has no cross-instrument meaning — 2% of an energy fund and 2% of a bond fund are the same
*percentage* and wildly different *dollars*. `md_L` is a **log-gap**, dimensionless: `0.01` means
*"the midline sits 1% outside the channel"*, identically on every instrument and in every era.

D231's z-threshold could only express *"statistically unusual for this symbol."* This expresses
*"physically large."* **A 2% breakout is routine for energy and extreme for bonds** — the z-rule
treats them alike, and this one does not.

**The override is scoped to this record.** D228's stop otherwise stands.

---

## The rung, and the decision to carry one

**`I1L` only.** The log construction is the sole basis from here: provably correct, *exactly*
scale-invariant, and dimensionless. `I1r` is dropped — fixing its denominator (divide by `hi`
rather than `mid`) gives `mi/hi − 1 ≈ log(mi/hi)`, which **is** `I1L` to first order, so it is
strictly a worse approximation to the same thing.

The published `I1` is reported alongside for continuity, not as a candidate.

*Recorded cost: `I1L` scored **−0.006** against the published rung on the mined fixture (D232) —
well inside a ±0.5 interval. The swap buys correctness at no measurable price, and is a
deliberate choice rather than a drift.*

---

## The rule

```
position = 1  if  hist_L > 0  AND  md_L > c
```

**Ladder, declared:** `c ∈ {0.00%, 0.25%, 0.50%, 0.75%, 1.00%}`. Round numbers with physical
meaning, chosen for interpretability rather than fitted.

`c = 0` is not a null cell — it is the **pure conjunction**, and it already excludes the
"below the band but recovering" case, which is precisely where the dollar-scale defect used to
manufacture signal.

---

## What is already measured, and is therefore not a prediction

Free under D228's boundary — position series only, no returns.

| rule | exposure | min entries/symbol |
|---|---:|---:|
| `hist_L > 0` (the I1L baseline) | **49.3%** | — |
| `+ md_L > 0.00%` | 30.4% | **16** |
| `+ md_L > 0.25%` | 29.0% | **11** |
| `+ md_L > 0.50%` | 27.5% | **6** |
| `+ md_L > 0.75%` | 25.9% | **3** |
| `+ md_L > 1.00%` | 24.5% | **1** |

`md_L` distribution over live bars: p50 **+0.44%**, p80 +3.52%, p95 +7.63%.

### Hurdle E fails across the entire ladder, and it is stated now

D217's hurdle E is a conjunction: **≥100 pooled AND ≥30 entries per ETF.** The pooled leg passes
comfortably (~1,700 at `c = 0`). **The per-symbol leg fails at every rung, starting at 16.**

This is **measured in advance, not predicted**, and it is not a reason to relax the hurdle —
changing a hurdle to fit a result is what pre-registration exists to prevent. It is a reason to
state the limitation plainly:

> **Every cell here is underpowered per symbol by construction.** A conjunction of two conditions
> cannot help but reduce per-symbol trade counts. The verdict rests on pooled statistics, and any
> per-symbol claim is unavailable. At `c = 0.75%` and `c = 1.00%` some symbols trade three times
> or once across six years — those cells are reported and should be read as very nearly
> degenerate.

---

## The bar this must clear, computed in advance

The √f law: with no selection benefit, Sharpe scales as √(exposure). Against the `I1L` baseline
of **+0.565** at 49.3%:

| c | exposure | √f predicts | **selection quality needed to tie** |
|---:|---:|---:|---:|
| 0.00% | 30.4% | +0.444 | **+27%** |
| 0.25% | 29.0% | +0.433 | **+30%** |
| 0.50% | 27.5% | +0.422 | **+34%** |
| 0.75% | 25.9% | +0.410 | **+38%** |
| 1.00% | 24.5% | +0.398 | **+42%** |

**The best selection quality anything in this programme has produced is +12%.** That is the
honest context for what follows, and it is stated before the run rather than after.

---

## Hurdles

- **P (carries the verdict).** Beat the `I1L` baseline on **excess Sharpe at rf = 4%, charged on
  the exposed fraction**.
- **B.** Clear a **best-of-search rotation null** over the five declared cells — one offset vector
  per replication shared across cells, 1,000 replications, seed 0. Rotation holds exposure,
  turnover and holding-period distribution fixed, so a delta over it cannot be "you just traded
  less."
- **E.** Reported, and **known to fail** on the per-symbol leg. Recorded per cell.
- **Money is reported and is not a hurdle** — D231's reasoning, unchanged: money is the wrong
  metric for a book that will be levered.

Every cell also reports the **√f decomposition** — predicted-from-exposure against actual, giving
selection quality — so each says directly whether it selected anything or merely traded less.

---

## Predictions

| | prediction | confidence |
|---|---|---|
| **W1** | **No cell beats the `I1L` baseline** on excess Sharpe | **moderate-high** |
| **W2** | **No cell reaches +15% selection quality**, let alone the +27% the easiest rung needs | **moderate-high** |
| **W3** | **Selection quality does not rise with `c`.** *This is the sharp test:* if `md_L`'s level carries information, a higher bar should mean better trades and the series should increase. If it is noise, it will be flat or fall | **moderate** |
| **W4** | **Nothing clears hurdle B** | **moderate-high** |
| **W5** | Money falls roughly linearly in exposure, near D228's **0.58 pp per pp** | **high** |

**W3 is what the study is actually for.** W1 and W2 will most likely be confirmed and would tell
us little beyond what the √f law already implies. W3 asks whether the *level* rung carries
information at all — and it is the one result that could reopen a line rather than close one.

---

## Stage 1 only

**Runs on the mined 57 and stops there.** The holdout is not touched. Under D231 amendment 2 the
mined fixture is a screen: it proves the construction and rejects catastrophic failure, and it
cannot detect a subtle success.

---

## Ledger

| count | N |
|---|---:|
| fresh — 5 thresholds | **5** |
| + D218's inherited | **67** |
| + disclosed ETF prior | **45,808** |

---

## Reuse — D212 is binding

| need | reuse | from |
|---|---|---|
| the log construction | `log_score`, `_band_md`, `_hist` | `run_scale_corrected.py` |
| rotation nulls, √f decomposition, rf-on-exposure, scoring | `rotation_nulls`, `score`, `_excess_sharpe` | `run_exposure_dial.py` |
| panel, costs, buy-and-hold | `load_panel`, `portfolio_log_returns`, `buy_and_hold` | `run_macd_ladder.py` |

**Written fresh:** the conjunction rule only — `md_L` and `hist_L` both already exist.
