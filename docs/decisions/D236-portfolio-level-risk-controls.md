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
