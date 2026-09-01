# D268 — Score independence: the gate on a consensus rule

**Status:** Measured. **The declared bar fails, narrowly — 2.87 against ≥3.0.**
**Date:** 2026-09-01
**Area:** Strategy research · **personal track**

**Descriptive. No cell scored, no forward return read, no book built.** This measures the
correlation structure of the *scores only*, and exists to kill a proposal cheaply if its premise is
false. **The ledger does not move.**

---

## The proposal it gates

The principal's: **bucket strategies by type — breakout, momentum, mean reversion, trend — and use
agreement between families as the selectivity mechanism**, rather than the strength of any single
signal.

**That is a genuinely different quantity from [D267](D267-the-magnitude-calibration-screen.md)'s.**
It counts independent confirmations instead of grading magnitude, so D267's failure does not carry
over to it.

**But it rests entirely on the families being independent**, and this repo already has the warning:
[D218](D218-impulse-macd.md) measured Impulse MACD's acceleration rung against classic MACD's on
identical bars and found them agreeing **within 0.04 Sharpe** — *"the whole apparatus buys nothing
over EMA(12) − EMA(26)."* Two constructions sharing no arithmetic, one signal.

**If nine scores are three things wearing nine hats, a three-family consensus is one signal agreeing
with itself.**

## RESULT

`scripts/d268_score_independence.py` · 432,032 bars, 8 symbols, Spearman on within-symbol ranks.

### The declared bar

| | |
|---|---:|
| **Effective independent scores** (participation ratio of the eigenvalues) | **2.87 of 9** |
| bar, declared before the run | **≥ 3.0** |
| variance in the first component | **49.4%** |

**It fails, by 0.13.** Stated as measured rather than rounded toward the answer that keeps the
proposal alive.

### The taxonomy does not survive contact with the data

**Five between-family pairs exceed |ρ| = 0.70, and the worst offenders are the ones the taxonomy
calls opposites:**

| pair | declared families | ρ |
|---|---|---:|
| `macd_line` vs `trailing_return` | LEVEL vs MOMENTUM | **+0.884** |
| **`macd_line` vs `rsi`** | **LEVEL vs OSCILLATOR** | **+0.853** |
| **`trailing_return` vs `rsi`** | **MOMENTUM vs OSCILLATOR** | **+0.782** |
| `impulse_md` vs `trailing_return` | LEVEL vs MOMENTUM | +0.777 |
| `impulse_nodz` vs `trailing_return` | LEVEL vs MOMENTUM | +0.771 |

**RSI — the mean-reversion oscillator, and the principal's own example of a different kind of
signal — correlates +0.85 with a MACD level and +0.78 with trailing return.** At fifteen minutes on
these names it is not a contrarian input. It is a monotone restatement of recent return.

**Classifying by what an indicator is *for* gives a different answer from classifying by what it
*measures*.** The by-construction taxonomy was declared before the correlations were read precisely
so the data could contradict it, and it did.

### The empirical taxonomy, which replaces it

Eigenvalues **4.45, 2.50, 1.45**, then a cliff to 0.25. **Three components, not five, not nine:**

| | what actually loads together |
|---|---|
| **1. Level / momentum / oscillator** — 49.4% | `impulse_md`, `impulse_nodz`, `macd_line`, `trailing_return`, `rsi` |
| **2. Acceleration** | `impulse_hist`, `macd_hist` (ρ = +0.74) |
| **3. Slope / structure** | `g_lo`, `g_min` (ρ = +0.99) |

**Within-family mean |ρ| is 0.857 and between-family 0.342**, so the *declared* families are
internally coherent — the problem is that three of them are one family.

## Verdict

**The bar was declared at ≥3.0 and came in at 2.87, so the proposal does not proceed as specified.**

**But the honest reading is narrower than "dead":** three genuinely distinct inputs *do* exist, and
the eigenvalue cliff after the third is sharp. **A three-way vote is available; a five-way or
nine-way one is not.** What is ruled out is the breadth the proposal assumed, not the mechanism.

**And the finding stands on its own, independent of the proposal:** most technical indicators on
this fixture are monotone transformations of trailing return, which is why *"several indicators
agree"* feels like corroboration and usually is not. **Any future consensus construction must
measure its inputs' independence before counting their votes** — and this file is the instrument
for it.
