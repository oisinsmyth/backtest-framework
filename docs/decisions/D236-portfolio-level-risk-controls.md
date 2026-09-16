# D236 — Portfolio-level risk controls on the recovery rule

**Status:** Pre-registered — committed BEFORE any runner exists
**Date:** 2026-08-27
**Area:** Strategy research

---

## Why portfolio-level and not trade-level

D235 measured trade-level stops and targets on this rule and closed them: fixed ones fail
because they cut the entry dip and cap the tail; the clever ones fail because **their triggers
carry no information over random trimming** (the best landed at the 63rd percentile of
matched-count random exits).

**The concern that motivates this study is different, and Sharpe cannot see it.** Sharpe treats a
−24.5% trade and a −5% trade as the same kind of variance. It does not price ruin.

**The distinction that makes this worth running:** a per-trade stop cuts the entry dip, which *is*
the signal. **A portfolio-level control does not touch which trades are taken — only how much of
the book is held.** The measured failure of stops therefore does not carry over.

### What the tail actually looks like

Measured, and it reframes the risk:

| | recovery | buy & hold |
|---|---:|---:|
| max drawdown | **−10.30%** | −34.60% |
| worst 1 day | −2.86% | −9.72% |
| worst 21 days | **−6.82%** | −33.78% |
| daily 1% VaR | −0.97% | −2.80% |

**Single-trade loss is bounded by diversification** — a position is 1/57 of the book, so the worst
trade in six years (−24.5%) cost **0.43% of capital.**

**Through the COVID crash leg (2020-02-19 → 2020-03-23) the rule was 2.0% exposed and lost
0.73%, against buy-and-hold's −33.86%.** It is not a dip-buyer: `hist_L > 0` requires price to be
*rising* relative to its channel, so a sustained fall keeps it flat. **It buys the turn, not the
dip.**

**The two risks that remain** are what this study addresses:

1. **Correlated exposure.** Mean 18.9% but **maximum 89.5%**, above 50% on 10.4% of bars.
2. **The grind, not the crash.** The worst drawdown was **2021-11-08 → 2022-07-14, 171 bars** —
   the 2022 bear market, where turns kept failing.

---

## The three families

### C — exposure cap

**Scale every position proportionally when total exposure exceeds X**: `pos × min(1, X / total)`.

**Proportional scaling, not "keep the strongest N."** Ranking would introduce a selection
decision — a degree of freedom, and a different hypothesis. This isolates *limit total risk* from
*choose which to hold*, and uses no information the base rule did not already use.

`X ∈ {30%, 40%, 50%}`. Measured binding frequency, so the levels are informed rather than guessed:

| cap | binds on | mean book held back |
|---:|---:|---:|
| 30% | 19.27% of bars | 5.14% |
| 40% | 14.13% | 3.46% |
| 50% | 10.43% | 2.25% |

### R — market regime filter

**Hold the book only when `SMA(50) > SMA(200)` on the equal-weighted basket of the 57.**
The basket rather than a single index, so no instrument choice is smuggled in. Canonical 50/200,
so no sweep.

**A measurement that must be stated before the run, because it predicts trouble:**

| | share of bars | the rule's exposure |
|---|---:|---:|
| regime **ON** | 68.3% | **12.3%** |
| regime **OFF** | 31.7% | **33.1%** |

**The rule is nearly 3× more active when the regime is OFF**, because it buys turns and turns
follow declines. This filter therefore removes most of the rule's activity by construction.

And it does not cover the case it looks like it should: **during the COVID crash leg the regime
was ON 88% of the time** — SMA(50) had not crossed down before the crash was over. It covers only
the 2022 grind (**ON 35%**).

*Included because it was asked for, with the tension recorded in advance rather than reported as
a surprise.*

### D — book drawdown circuit breaker

**When the book's own drawdown from peak exceeds X, go flat for 21 bars.**

Targets the grind directly, and unlike R it reacts to the **book's** state rather than the
market's — so it does not systematically remove the regime the rule works best in.

`X ∈ {5%, 8%}`, 21-bar pause. Drawdown at close *t* is known at close *t*; the pause takes effect
from *t+1*.

**Six cells.**

---

## Hurdles — and the primary is not Sharpe

The objective here is **drawdown**, and Sharpe is the wrong instrument for it. Every control below
cuts exposure, so excess Sharpe will fall roughly as √f whether or not the control is any good.

- **K1.** Max drawdown improves.
- **K2 (carries the verdict).** **`CAGR / |max drawdown|` improves** — the drawdown reduction is
  worth more than the return it costs.
- **N (R7, and this is its first application).** Each control must beat an **overlay null**: keep
  the base book, and bind the control at **random bars matched on how often it really binds**. If
  a cap that binds on 19.27% of bars does no better than holding back the same amount at random
  times, the *rule* for when to bind carries nothing.
- **Excess Sharpe and the √f decomposition are reported**, not hurdles.

---

## Predictions

| | prediction | confidence |
|---|---|---|
| **U1** | **All three caps reduce max drawdown** | **high** — near-mechanical |
| **U2** | **Excess Sharpe falls at every cell**, roughly as √f | **moderate-high** |
| **U3** | **At least one cell improves `CAGR/\|maxDD\|`** | **moderate** |
| **U4** | **R is the worst cell of the six** — it removes the rule's most active regime and misses the crash it appears designed for | **moderate-high** |
| **U5** | **No cell beats its overlay null** — the controls will bound risk mechanically without their *timing* carrying information | **moderate** |

**U5 is the real test.** U1 is arithmetic and U3 is likely for a mechanical reason. **U5 asks
whether these controls are smart or merely small**, and it is the question D235's corrected null
was built to answer.

---

## Stage 1 only

**The mined 57.** The holdout and the 2025–2026 forward window are not touched.

---

## Ledger

| count | N |
|---|---:|
| fresh — 6 cells | **6** |
| + D234's 6 and D235's 7 | 19 |
| + disclosed ETF prior | **45,822** |

---

## Reuse — D212 is binding

| need | reuse | from |
|---|---|---|
| the recovery book, `md_L`/`hist_L`, overlay machinery | `base_masks`, `hold_book`, `overlay` | `run_stops_targets.py` |
| scoring, rf-on-exposure, √f decomposition | `score`, `_excess_sharpe` | `run_exposure_dial.py` |
| trade spans | `trade_spans` | `run_filter_search.py` |

**Written fresh:** the three controls and **the matched-frequency overlay null R7 requires** —
which does not exist yet as reusable code, and should, since R7 now binds on every future overlay
study.

---

## STAGE 1 — SCREEN RESULT

*Appended after the run. **A screen, not a verdict.** The holdout and the 2025–2026 forward
window are untouched.*

**Produced:** 2026-08-27 · `uv run python scripts/run_risk_controls.py` · Page:
[`RISK_CONTROLS_RESULTS.md`](../results/RISK_CONTROLS_RESULTS.md)

### The one-sentence version

**All six controls reduce drawdown, none improves risk-adjusted return, and every one is beaten
by holding back the same amount at random times — which means the bars they cut are better than
average, not worse.**

### The six

Baseline: **+0.746** excess Sharpe, 5.43% CAGR, **−10.30%** max DD, **CAGR/|DD| = 0.527**,
18.9% exposure. Buy-and-hold: 0.243.

| cell | binds | exposure | max DD | CAGR/\|DD\| | Δ | excess Sharpe | √f predicts | null p95 | K1 | K2 | N |
|---|---:|---:|---:|---:|---:|---:|---:|---:|:--:|:--:|:--:|
| C@30% | 19.3% | 13.7% | **−6.03%** | 0.420 | −0.107 | +0.609 | +0.637 | +0.840 | ✓ | — | — |
| C@40% | 14.1% | 15.4% | −7.19% | 0.469 | −0.058 | +0.694 | +0.675 | +0.845 | ✓ | — | — |
| C@50% | 10.4% | 16.6% | −8.07% | 0.511 | −0.016 | +0.746 | +0.700 | +0.815 | ✓ | — | — |
| **R SMA50>200** | 31.7% | 8.4% | **−2.87%** | 0.288 | −0.239 | +0.267 | +0.497 | +0.868 | ✓ | — | — |
| D@5% | 72.9% | 5.5% | −7.24% | 0.286 | −0.241 | +0.446 | +0.402 | +0.915 | ✓ | — | — |
| D@8% | 40.3% | 10.6% | −9.93% | 0.310 | −0.216 | +0.516 | +0.558 | +0.879 | ✓ | — | — |

**K1: 6 of 6. K2: 0 of 6. N: 0 of 6.**

### The finding, and it inverts the premise of the study

**Every control's real excess Sharpe sits below its own overlay null's p95.** Holding back the
*same amount of book at random bars* beats holding it back when the control says to — C@50% real
**+0.746** against a null p95 of **+0.815**; R real **+0.267** against **+0.868**.

That is not "the controls are neutral." It is stronger:

> **The bars these controls cut are better than average.** A cap binds exactly when exposure is
> high — and high-exposure bars are when the rule has the most breadth and conviction. Cutting
> there removes its best moments.

**Concentration was assumed to be the risk. It is measured here as the opposite** — the 89.5%-exposure
days are not the dangerous ones, they are the profitable ones.

That agrees with the one other exposure result in the programme: D235's `DT@2.0%` was the single
construction that gained by *adding* exposure. **At 18.9% this rule is under-exposed, and
everything that cuts participation costs more than it saves.**

### The regime filter behaved exactly as the pre-registration said it would

`R` gives the **largest drawdown reduction of any cell** — −10.30% to **−2.87%**, a 72%
improvement — and the **worst excess Sharpe**, +0.267 against the baseline's +0.746. Its implied
CAGR is **0.83%/yr**. It reduces drawdown by very nearly not trading.

The measurement recorded before the run explains it: the rule is 3× more active when the regime
is OFF (33.1% exposure) than ON (12.3%), so gating on "bull market" removes most of its activity
by construction. **This was stated in advance rather than discovered afterwards**, which is the
only reason it counts for anything.

### Scoring

| | prediction | outcome |
|---|---|---|
| **U1** | all caps reduce max drawdown | **CONFIRMED**, 6 of 6 |
| **U2** | excess Sharpe falls at every cell, roughly as √f | **SPLIT.** It falls at five of six, but **four cells beat their own √f prediction** (C@40, C@50, D@5) — the drop is smaller than exposure alone implies |
| **U3** | at least one cell improves `CAGR/\|maxDD\|` | **FALSIFIED. Zero of six.** Every control costs more return than the drawdown it saves |
| **U4** | `R` is the worst cell | **SPLIT.** Worst on excess Sharpe (+0.267) by a distance; second-worst on Calmar, where D@5% edges it by 0.002 |
| **U5** | no cell beats its overlay null | **CONFIRMED**, 0 of 6 — and by a wide margin |

**Two clean of five.**

### What this means for the concern that prompted it

The worry was **unbounded loss in unusual conditions.** Three measurements bear on it, and none
supports adding a control:

1. **Single-trade loss is bounded by diversification** — a position is 1/57, so the worst trade in
   six years cost **0.43% of capital**.
2. **The rule was 2.0% exposed through the COVID crash leg** and lost 0.73% against −33.86%.
   `hist_L > 0` keeps it flat while a fall is still accelerating. It buys the turn, not the dip.
3. **The concentration case is profitable, not dangerous** — established above by the overlay
   null.

**The residual risk is the grind**, and `D` was built for it: the 5% breaker binds on **72.9% of
bars** and takes exposure to 5.5%. It does not manage the grind so much as abolish the strategy.

### What survives

**Nothing is promoted, and one thing is closed.** Portfolio-level risk controls join trade-level
stops and targets: measured, mechanism understood, shut.

**R7's overlay null works and earned its place immediately** — it is the only hurdle here that
distinguished "reduces risk" from "reduces risk intelligently", and all six cells look reasonable
on K1 alone. Its first application found six false positives that K1 would have waved through.

**And the direction is now unambiguous across three studies**: `DT@2.0%` gained by adding
exposure, every cut here lost, and the overlay null says the cut bars are above average. **The
next thing worth testing on this rule adds exposure, not risk control.**

### Ledger

| count | N |
|---|---:|
| fresh — 6 cells | 6 |
| + D234's 6 and D235's 7 | 19 |
| + disclosed ETF prior | **45,822** |
