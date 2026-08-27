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

**Written fresh:** `hist_r` and `hist_L` only.

---

## STAGE 1 — SCREEN RESULT

*Appended after the run. **A screen, not a verdict.***

**Produced:** 2026-08-27 · `uv run python scripts/run_scale_corrected.py` · Page:
[`SCALE_CORRECTED_RESULTS.md`](../../SCALE_CORRECTED_RESULTS.md)

### The one-sentence version

**The defect is real, provable and exactly removable — and fixing it does not help. Both
corrections are fractionally *worse* than the published indicator, because on real data they
change the signal's sign on barely one bar in eighty-seven.**

### The numbers

| rung | Sharpe | excess @rf=4% | exposure | turnover | Δ vs published | boot p05 |
|---|---:|---:|---:|---:|---:|---:|
| **I1 published** | **+0.658** | **+0.570** | 49.9% | 4,835 | — | — |
| I1L log | +0.652 | +0.565 | 49.3% | 4,871 | **−0.006** | −0.051 |
| I1r ratio | +0.610 | +0.524 | 48.9% | 4,865 | **−0.047** | −0.105 |
| buy and hold | +0.333 | +0.235 | 100% | — | — | — |

`I1L − I1r = +0.041` (p05 −0.020). Hurdle A fails everywhere, as expected.

### Scoring

| | prediction | outcome |
|---|---|---|
| **Z1** | `I1L − I1 > 0` | **FALSIFIED.** −0.006 — a dead heat, fractionally the wrong way |
| **Z2** | the delta is below +0.10 | held, trivially, since it is negative |
| **Z3** | exposure within 2 pp | **CONFIRMED.** 49.3% and 48.9% against 49.9% |
| **Z4** | bootstrap p05 below zero | **CONFIRMED.** −0.051 and −0.105 |
| **Z5** | improvement correlates with abs log drift | **FALSIFIED, and backwards.** −0.111 and −0.156 |
| **Z6** | `I1L` beats `I1r` | **CONFIRMED** directionally, +0.041, though p05 −0.020 |

**Z5 is the one that matters.** It was declared as the mechanism test — *"a positive Z1 with a
null Z5 would mean the fix helped by accident"*. Z1 came out negative and Z5 came out negative,
so the small differences that do exist did not arrive through the channel the algebra names.

### Why a provable defect turned out to be immaterial

**Sign agreement between the published and log constructions: 98.85% mean, 95.45% worst.**
Histogram correlation 0.972. **The corrected signal makes the same call on 99 bars in 100.**

The reason is a horizon mismatch that the analysis missed:

> `hist = md − sma(md, 9)` reads md's change over **~9 bars**. The scale contamination is md's
> dollar magnitude drifting with the price level — **also over ~9 bars, not over the span**.
> Median absolute 9-bar move on this fixture is **2.24%**, so the contamination perturbs `md` by
> about 2%, against md's own 9-bar variation, which is far larger.

**In the synthetic demonstration the path was noiseless, so that 2% drift was the *only* thing
moving `md`, and it set the sign on 100% of bars. In real data there is always something else
happening.**

### The methodological error, recorded because it is the transferable part

The demonstration that motivated this study was a **noiseless path constructed to isolate the
mechanism**. That is the right way to *find* a defect and the **wrong way to size one** — an
adversarial path maximises the effect by construction, and I read a magnitude off it.

> **A defect that is provable is not thereby material.** Establishing that a bias exists and
> establishing that it matters are separate measurements, and the second cannot be inferred from
> a path chosen to make the first visible.

The cheap check that would have caught this before any of the machinery was written is the one
that explains it afterwards: **compare the corrected and uncorrected signals on the real data
and count how often they disagree.** 1.15% would have ended the study in a minute.

### A conjecture, labelled as such

Symbols that **fell** over the span improved under the fix (mean +0.0173, n=14); symbols that
**rose** got slightly worse (−0.0042, n=43). That is consistent with the dollar-scale bias having
acted as an accidental **long tilt** — it pushes `hist` positive when price levels rise, which
flatters a mostly-rising sample.

**It is not established.** The correlation with signed drift is +0.083, essentially zero; the
quartile gradient is non-monotone (+0.017, −0.016, +0.006, −0.002); and the "fell" group is 14
symbols. Recorded as a conjecture with a stated test — it predicts the corrected rungs should
*beat* the published one on a declining sample — and not as a finding.

### What survives

**Two things, and neither is a strategy.**

The corrected constructions are **provably right**: on a path with no acceleration both drive
`hist` to **~1e−16**, thirteen orders of magnitude below the published construction's 1.3e−03,
and `I1L` is *exactly* scale-invariant. Pinned by test. If a future study runs on an instrument
whose price level moves far more than these ETFs did — a crypto drawdown, a single stock, a long
bear market — **`I1L` is the construction to use**, on correctness grounds, at no measured cost.

And the horizon insight bounds every future attempt at this indicator: **the operator only ever
sees ~9 bars of `md`.** Anything hoped to matter must move `md` inside that window.

### The holdout

**Untouched.** Nothing here justifies spending it. `ImpulseSeries` already carries `md` and `mid`, so the
correction is a two-line function and nothing else needs restating — which is itself evidence
that the defect was always visible in the data structure and simply never looked at.
