# D232 — The scale-corrected Impulse MACD

**Status:** Pre-registered — committed BEFORE any runner exists
**Date:** 2026-08-27
**Area:** Strategy research

---

## The defect, derived analytically

`md` is the displacement of the zero-lag midline from the Wilder band, **measured in dollars**.
It is therefore proportional to the price *level*, and `hist = md − sma(md, 9)` is a slope
estimator on it. So `hist` picks up level drift as if it were signal.

**Demonstrated on a fully controlled path — no market data, no P&L, free under D228's boundary.**
A steady −20%/yr decline with zero noise:

| | |
|---|---|
| price | 41.25 → 2.90 |
| `md` | −1.0814 → −0.0760 — **negative on 100% of bars** |
| `md` slope | **+3.0e−04** — rising, because a shrinking negative number rises |
| **`hist > 0`** | **100.0% of bars → LONG throughout a persistent decline** |

**The same path with `md` expressed as a fraction of price:**

| | |
|---|---|
| `md/price` slope | **−2.5e−19** — zero |
| `hist > 0` | **48.8%** — a coin flip, which is correct: there is no acceleration here |

It is not a units bug. Multiplying the whole series by 7 leaves `sign(hist)` **100% identical**.
The defect is that the price level **drifts within** a single series, and `md`'s magnitude drifts
with it.

### Two further properties, recorded because they bound what any fix can achieve

**The operator is a chop detector.** Gain of `x − sma(x,9)` by cycle length: 1.000 at 3 bars,
**1.190 at 13** (peak), 0.410 at 60, **0.100 at 252**. A year-long trend is attenuated by 90%.
Scale correction does not touch this.

**~50% exposure is structural.** The kernel sums to zero, so `sign(hist)` is a coin flip whatever
the market does. **Normalisation cannot change this**, and any hope that a better signal would
also be a more selective one is misplaced.

---

## The correction

```
md_n[t] = md[t] / mid[t]          where mid = smma(close, 34)
hist_n  = md_n - sma(md_n, 9)
```

**Normalised by `mid`, not by `close`.** `mid` is already computed inside `ImpulseSeries`, is
contemporaneous, and is smooth — dividing by the raw close would inject the close's own noise
into the numerator's denominator for no benefit. `mid` is strictly positive, so no guard is
needed.

**Everything else is unchanged**: same `length = 34`, same `signal = 9`, same dead zone, same
long-flat book, same `lag = 1`, same 1,000-bar warm-up, same costs.

### PRE-RUN AMENDMENT — both fixes, not one

*Committed before any runner exists. The section above names one correction; two were offered
and they are not equivalent, so both are registered and compared.*

| rung | construction | scale invariance |
|---|---|---|
| **`I1r`** | `md_r = md / mid` — normalise the displacement | **approximate** |
| **`I1L`** | compute the **entire indicator on log prices**: `log H`, `log L`, `log C` | **exact** |

**They differ in kind, not degree.**

`I1r` divides the final displacement by a contemporaneous scale. It is a correction applied
*after* the fact.

`I1L` removes the defect at its root. `smma` and `zlema` are linear operators with unit DC gain,
so on `log(kP) = log k + log P` every leg shifts by the same constant and the difference
`mi − hi` is **exactly** unchanged. More importantly for the defect actually found: a steady
exponential trend is a **straight line in log space**, so `md_L` becomes *constant*, so
`hist_L → 0`, so the rule stands aside — which is the correct answer for a path with no
acceleration.

`md_r ≈ log(mi/hi)` only for small displacements, so **`I1r` is the first-order approximation to
`I1L`.** That makes the comparison informative rather than redundant: if they agree, the
displacements are small and either will do; if they diverge, the approximation is being asked to
work where it does not hold.

**Ledger updated: fresh looks 4 → 8** (two rungs × 2 books × 2 gates). Both are reported
whatever they show; neither is dropped after the fact.

**This is the first time in this programme that the SIGNAL is being changed rather than gated.**
Seven filter studies tried to remove the arm's bad trades from outside. This asks whether some
of them were manufactured by the indicator's own arithmetic.

---

## The test

**Rungs `I1r` and `I1L`, each against `I1`, as paired deltas** — D217's statistic, and the right one:
nested constructions on the same bars share almost all their variance, so the difference is
estimated far more precisely than either level. Cells: 2 books × 2 gates. Primary:
**`long_flat / gate = none`**, the cell D218 named.

### Hurdles

- **A.** `I1x − I1 ≥ +0.10` (for each corrected rung) **and** the paired block bootstrap's **p05 > +0.10** — D229's
  construction, block 21, 1,000 replications, both rungs on identical resampled dates.
  **The standing hurdle is used unchanged.** A positive delta below +0.10 will be reported as
  exactly that: an improvement that does not clear the programme's bar. Lowering the bar to fit
  the expected effect is the thing pre-registration exists to prevent.
- **D.** Beat buy-and-hold on excess Sharpe at `rf = 4%` charged on the exposed fraction, and on
  dividend-adjusted money. Reported for both rungs.
- **E.** ≥100 pooled and ≥30 entries per symbol.

### Validation, as tests rather than hurdles

- **The synthetic downtrend**: **both** corrected rungs must hold **< 60%** of bars on the
  −20%/yr noiseless path where `I1` holds 100%. `I1L` should land near 50%. This is the direct check that the fix does what the algebra says.
- **Scale invariance**: signs identical on `P` and `kP` for both, and `md_L` **exactly**
  unchanged (not merely close) — that is the property `I1L` is built on.
- **No look-ahead**: perturbing from bar *t* moves no decision at or before *t*.

---

## Predictions

| | prediction | confidence |
|---|---|---|
| **Z1** | **`I1L − I1 > 0`** at the primary cell — removing a known contaminant helps | **moderate** |
| **Z2** | **The delta is below +0.10**, so hurdle A fails on the point estimate alone. The defect is a contaminant, not the whole signal, and the arm already earned +0.570 with it | **moderate-high** |
| **Z3** | **Both corrected rungs' exposure stays within 2 pp of `I1`'s 49.9%** — the zero-sum kernel is untouched by normalisation | **high** |
| **Z4** | **The bootstrap p05 is below zero**, as it was for all 24 deltas in D230. Precision is a property of the sample and the fix does not change the sample | **high** |
| **Z5** | **The per-symbol improvement correlates positively with that symbol's absolute log price drift** over the span — the defect scales with level drift, so the fix should help most where the level moved most | **moderate** |
| **Z6** | **`I1L` beats `I1r`**, because the ratio is only the first-order approximation to the log construction and ETF displacements are not always small | **low-moderate** |

**Z5 is the mechanism test.** Z1 could come out positive for any reason; Z5 only comes out
positive if the improvement arrives through the channel the algebra identifies. A positive Z1
with a null Z5 would mean the fix helped by accident, and should be treated as such.

---

## Stage 1 only

**This runs on the mined 57 and stops there.** Under D231 amendment 2 the mined fixture is a
screen: it proves the construction and rejects catastrophic failure, and it cannot detect a
subtle success. **The holdout is not touched.**

The stated purpose is to establish whether the corrected signal is a better *baseline* — the
thing future work would mine against — not to produce a verdict.

---

## Ledger

| count | N |
|---|---:|
| fresh — `I1r` and `I1L` × 2 books × 2 gates | **8** |
| + D218's inherited | **70** |
| + disclosed ETF prior | **45,811** |

**Not the verdict**, as in D229: the paired delta is, and it stands or falls on its own interval.

---

## Reuse — D212 is binding

| need | reuse | from |
|---|---|---|
| paired block bootstrap | `paired_block_bootstrap` | `run_jerk_rung.py` |
| ladder arms, panel, costs, buy-and-hold, scoring | `arm_positions`, `load_panel`, `score_cell`, `excess_sharpe` | `run_jerk_rung.py`, `run_macd_ladder.py` |
| the Impulse series and its `mid` leg | `impulse_macd_series` | `research/macd.py` |

**Written fresh:** `hist_r` and `hist_L` only. `ImpulseSeries` already carries `md` and `mid`, so the
correction is a two-line function and nothing else needs restating — which is itself evidence
that the defect was always visible in the data structure and simply never looked at.
