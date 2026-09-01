# D267 — The magnitude-calibration screen

**Status:** PRE-REGISTERED. Committed **before the screen is run**. Nothing here is a result.
**Date:** 2026-09-01
**Area:** Strategy research · **personal track** ([BOOK.md](../BOOK.md))

**No book is built and no rule is proposed.** This screens a **property of signals**, not strategies.

---

## The question, and it is the principal's

> *"Selectivity and how good it becomes is a real function of strategy. If we went with RSI mean
> reversion it may not be all that great. Even if for the current strategy it does not work, that
> does not mean it won't for other strategies."*

**That is correct, and this record exists because it is correct.** The programme has repeatedly
treated selectivity as a technique that works or fails. **It is neither — it is a property a
signal either has or does not have, and it must be measured per signal.**

### The property, stated precisely

For selectivity to pay, a signal's strength must predict the **magnitude of the forward move**. That
is a different property from predicting its **direction**, and almost every technical indicator is
built for the second.

**RSI is the principal's own example and it is the clean case.** RSI is bounded and mean-reverting by
construction, so an extreme reading says *"price is far from its recent mean"* — a statement about
where price **is**, not how far it is about to **travel**. A signal can be 55% right on direction at
every strength level and completely flat on magnitude; selectivity then cuts the sample and buys
nothing.

**And the cost bar this programme has derived is a MAGNITUDE bar.** [D265](D265-the-entry-time-reconciliation.md)
established that an enter-once/hold/exit construction must satisfy

```
mean move per trade  >=  2c        (the round-trip cost)
```

with the trade count cancelling out entirely. **Hit rate does not appear.** D265 measured 52.0% hit
with a 1.03 payoff and the hit rate was nearly irrelevant to whether the cell paid. **So selectivity
helps exactly those signals whose strength is magnitude-calibrated, and nothing else.**

### A correction to the record this replaces

[D248](D248-the-strength-filtered-intraday-short.md) is routinely cited in this programme as
*"selectivity failed."* **It is not that.** Its hurdle A7 measured `|hist_L|` quintiles against
forward returns and found them non-monotone with **the sign flipping between halves** — Q5 at
+10.51% on the screen against −3.52% on validation. **That is one measurement of one signal's
calibration.** It says nothing about any other score, and citing it as a general result was an
overgeneralisation made in this session and corrected here.

---

## The design

**The inversion this programme already uses** (D250, D251, D263): measure the conditional first,
against a bar stated in advance, and pay for a full pre-registration only if something clears. **A
signal screened out here costs one cell instead of one study.**

### The library — nine scores, fixed here, all from committed and tested primitives

| # | score | source | family |
|---|---|---|---|
| 1 | `impulse_hist` | `impulse_signal_score` — I1 | acceleration *(this is S1's own score)* |
| 2 | `impulse_md` | `impulse_band_score` — I2 | level |
| 3 | `impulse_nodz` | `impulse_no_deadzone_score` — I3 | level, no dead zone |
| 4 | `macd_hist` | `signal_line_score`, 12/26/9 | acceleration |
| 5 | `macd_line` | `zero_line_score` | level |
| 6 | `trailing_return` | `trailing_return_score` | momentum |
| 7 | `rsi` | `structure.rsi`, window 14 | **oscillator — the principal's example** |
| 8 | `g_lo` | S2's support slope, `rolling_fit` | trend slope |
| 9 | `g_min` | `min(g_lo, g_hi)` — joint downtrend strength | trend slope |

**Nothing is added to this list after the run and no parameter inside any score is varied.** Every
constant is the committed default.

### The measurement

**Fixture:** `single_name_intraday_15m_panel.csv.gz`, the 8-name panel D264 built. No fetch.

```
for each score s, each symbol:
    quintile the LAGGED score s[t-1] within that symbol
    forward move = sum of log returns over bars t .. t+H-1, truncated at the session close
    report the mean forward move per quintile, in bp
```

**`H = 8` bars (2 hours), fixed and not swept.** D265 derived it: the marginal edge over bars 1–8 is
**+0.641 bp/bar** against a **constant +0.316 bp/bar** variance tax, and beyond bar 8 the two are
level. It is the horizon at which the edge outruns the tax, chosen by measurement rather than
preference.

**R9 is binding and is the defect that killed D248's motivating analysis.** The score is lagged one
bar: `s[t-1]` decides, and the forward window starts at `t`. No bar is read that the rule could not
have seen.

### Hurdles — all three, every leg computed (R6)

| | standard |
|---|---|
| **M1** | **Monotone** — the five quintile means are strictly ordered, in either direction. The direction is the signal's, not mine; a monotone *upward* score is a long signal and counts |
| **M2** | **The extreme quintile clears the cost bar** — `\|mean forward move\| >= 2c`, at the stratum's own cost: **4.00 bp** (LOW), **12.84 bp** (HIGH), **8.42 bp** (ALL) |
| **M3** | **Best-of-27 floor (D228)** — the quintile spread must exceed the **p95 of the maximum spread across all 27 cells** under a shuffle null, drawn with **one shared shuffle per simulation** so the cells are not made artificially independent |

**The null shuffles the score within each symbol**, preserving both marginal distributions and
destroying only the alignment between score and forward return. That is the correct null for a
calibration question: it asks whether *this* ordering carries information, not whether the returns
have structure.

**A score must clear M1, M2 and M3. All three.**

### Cells and count

**9 scores × 3 strata (ALL, LOW, HIGH) = 27 cells**, counted in full. ALL is the primary; LOW and
HIGH are a declared robustness split, **not** a licence to report the best of three.

---

## Predictions, declared before the run

| | prediction | confidence |
|---|---|---|
| **Q-a** | **No score clears all three.** Base rate in this programme is roughly one in eight and 27 cells against a best-of-27 floor is a hard bar | **moderate-high** |
| **Q-b** | **`impulse_hist` fails M1**, reproducing D248's A7 on a different universe and frequency. If it *passes* here, D248's result was universe-specific rather than a property of the score | **moderate-high** |
| **Q-c** | **`rsi` fails M2 even if it passes M1** — the principal's own example, declared so it is a test rather than an anecdote | **moderate** |
| **Q-d** | **If anything clears, it is a trend-slope score (`g_lo`, `g_min`) rather than an oscillator**, because oscillators are calibrated to position-in-range and slopes to travel | **low-moderate** |

**Q-b and Q-c are the ones worth being wrong about.** Q-b tests whether this programme's most-cited
negative result generalises; Q-c tests the principal's stated intuition against data rather than
agreeing with it.

---

## Stop

**If no score clears all three, the magnitude-calibration route is closed for this library** — no
tenth score, no second horizon, no re-cut quintiles, no per-stratum threshold. Committed here so
*"the last reading wasn't the right one"* cannot be pulled later.

**If a score does clear, nothing is promoted.** Under [R8](../RULES.md#r8) it becomes a candidate
needing its own pre-registered out-of-sample test, and it inherits **all 27 cells** into its
multiplicity count — not the one that won.

---

## Ledger

| count | N |
|---|---:|
| fresh — 9 scores × 3 strata | **27** |
| carried from D265 | 46,167 |
| **total** | **46,194** |

**The floor this is judged against.** [D218](D218-impulse-macd.md) measured this programme's
deflated-Sharpe noise floor at **+1.42 Sharpe at ~45,800 looks**, and concluded that *no arm anyone
runs on this fixture can clear it.* **That conclusion stands and is not suspended by this record.**
A score clearing M1–M3 here is evidence about a *property*, cheaply obtained — it is not a Sharpe
claim, and it must not be reported as one.
