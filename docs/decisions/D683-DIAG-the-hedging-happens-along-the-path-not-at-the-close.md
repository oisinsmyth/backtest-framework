# D683 DIAG — why D681's dealer-gamma close failed: not too little impact. The flow is large and the test had power, but the hedging happens along the day's path (long gamma damps and mean-reverts it), not at the close; the close's pooled slope is the February–April 2020 crash

*2026-09-29. Post hoc, on D681's own in-sample (1,989 sessions, 2016-01-05 → 2023-12-29). No verdict, and no slice
spent. It answers the principal: "Do a full diagnostic, why did the mechanism fail? Did it not have enough impact?"*
- **The script** `scripts/diag_d683_gamma_close_mechanism.py` was committed before its run (`5fa84897`), with seven
  candidate explanations and their fingerprints in its docstring. It ran once, in 119 s. Output:
  `data/d683_gamma_close_diag.json` (statistics only, no per-date GEX).
- **D681's β_G reproduced exactly:** 0.12248493139982482.

## The answer in one line

**No, it did not lack impact. The hedge flow D681 computes is large, and the test could have seen the law's size several
times over. The price simply does not respond at the close.**
- **The mechanism is real, on the wrong clock.** Dealer gamma visibly shapes the intraday path:
  - on long-gamma days the day's 5-minute returns mean-revert more, monotonically in gamma (beyond every one of 1,970
    rotations);
  - realised variance is about half the short-gamma days'.
- **So the hedging is done continuously, as the price moves.** By 15:30 there is no stored imbalance left for the close
  to release.
- **What D681's pooled slope was:** the February–April 2020 crash. Without it the close slope is +0.04 (t 0.65).

## 1. A — too little impact? No

**The flow is not small.**

| hedge flow \|Q\| = \|G·r\| | median | p90 | p99 |
|---|---:|---:|---:|
| $bn | 2.05 | 9.24 | 24.8 |
| % of ES daily dollar volume | 1.2% | 4.8% | 11.1% |
| **% of ES's 15:30 → 16:00 dollar volume** | **8.6%** | **34.7%** | **79.2%** |

The closing half-hour carries 13.8% of the day's ES volume. If dealers traded D681's flow there, it would be a
substantial share of the half-hour's volume on a typical day and a third of it on one day in ten.

**The test had power.**
- The push's variance survives the controls: 95% of Z's variance is left after r, Z_L and σ_d are partialled out.
- **The expected t at each impact size Y,** against D681's own Newey–West standard error (0.0995, which is
  β / t = 0.1225 / 1.231):

| Y | 1.0 | 0.5 | 0.25 | **observed 0.12** |
|---|---:|---:|---:|---:|
| expected NW t | 10.1 | 5.0 | 2.5 | 1.23 |

- The homoskedastic OLS arithmetic, which the pre-registration's "t ≈ 4" sketch resembled, gives t 22.6 / 11.3 / 5.7.
  The NW standard error is 2.3× the OLS one because large-|Z| days are high-variance days. **Either way, a
  square-root impact of Y ≥ 0.25 would have shown.**

**The response by size of predicted push** (sign(Z)·R2, bp):

| \|Z\| decile | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| mean \|Z\| | 1.4 | 2.9 | 4.3 | 5.8 | 7.4 | 9.2 | 11.2 | 14.3 | 20.0 | 38.8 |
| mean sign(Z)·R2 | +1.2 | +0.9 | +0.5 | +0.1 | −0.6 | +0.3 | −2.7 | −1.4 | −0.7 | **+7.7** |
| SE | 1.5 | 1.1 | 1.2 | 1.4 | 1.8 | 1.5 | 2.1 | 1.8 | 2.5 | 5.0 |

- Nine deciles are flat at zero.
- The top decile returns +7.7 bp (SE 5.0) on a predicted 38.8 bp, a pass-through of 0.20, and it is the 2020 crash
  (G, below).
- **There is no dose-response: the close does not scale with the flow.**

## 2. B — continuous hedging along the path: yes, strongly

The first-order autocorrelation of the day's 5-minute returns (09:30 → 15:30), and the day's realised variance, by
gamma. σ_d is a control throughout, and each null is D681's enumerated day rotation of G (1,970 offsets, p95 SE 0).

| G_SUM quintile (0 = most short) | 0 | 1 | 2 | 3 | 4 |
|---|---:|---:|---:|---:|---:|
| 5-minute ρ1 | −0.009 | −0.022 | −0.028 | −0.034 | **−0.047** |
| median realised variance (bp²) | 10,046 | 5,170 | 2,885 | 1,954 | 1,600 |

| statistic | slope | NW t | rotation null p05 / p50 / p95 | percentile |
|---|---:|---:|---|---:|
| ρ1 on G_SUM ($bn) | −0.00145 | −3.50 | −0.00081 / +0.00002 / +0.00075 | **0.000** (below every rotation) |
| ρ1 on the short-gamma dummy | +0.0190 | +3.02 | −0.0125 / −0.0006 / +0.0135 | 0.995 |
| log RV on G_SUM ($bn) | −0.0485 | −11.2 | −0.0084 / +0.0002 / +0.0092 | **0.000** |
| log RV on the short-gamma dummy | +0.729 | +12.8 | −0.141 / −0.005 / +0.127 | **1.000** |

**This is the hedging mechanism's own fingerprint:**
- **Long gamma** means dealers sell rallies and buy dips as they happen. The path mean-reverts (ρ1 more negative, in a
  monotone gradient) and the day is calmer (realised variance ×0.48, controlling trailing σ).
- **Short gamma** removes the damping.

**The flow D681 aggregated into one 15:30 imbalance is executed bar by bar during the day.** What remains at the close
is noise.

**Caveats.**
- **Bid–ask bounce cannot make the gradient.** At a quarter-point tick its contribution to a 5-minute ρ1 is
  −0.001 to −0.004, against a quintile spread of 0.038.
- **Gamma is correlated with the volatility level** (median σ_d 117 → 59 bp across the quintiles), and the control is
  linear in trailing σ. A same-day-volatility control is the one check this record did not run.
- **At 5 minutes the dampening is not tradeable directly:** about 0.2 bp of expected reversion per bar in the top
  quintile, against a ~2 bp MES round trip.

## 3. C — the wrong move to hedge? No

If dealers rehedge through the day, the imbalance at 15:30 should be the recent move. Z rebuilt on shorter lookbacks
(same regression and rotation):

| move since | prior settle (D681) | 09:30 | 12:00 | 14:30 | 15:00 | 15:15 |
|---|---:|---:|---:|---:|---:|---:|
| β_G | +0.122 | +0.025 | +0.038 | +0.125 | +0.220 | +0.204 |
| NW t | 1.23 | 0.28 | 0.31 | 0.87 | 1.20 | 0.85 |
| rotation percentile | 0.91 | 0.56 | 0.54 | 0.77 | 0.86 | 0.74 |

**No lookback predicts the close.** That is consistent with B: the imbalance is cleared continuously, so no residual
from any window carries over.

## 4. D — anticipated or temporary? No clear sign

| window, on Z | β | NW t |
|---|---:|---:|
| 14:30 → 15:30, Z built at 14:30 | +0.118 | +1.60 |
| overnight, 16:00 → next 09:30 | −0.133 | −0.78 |
| next 09:30 → 10:00 | −0.045 | −0.82 |
| close + overnight | −0.079 | −0.46 |

The hour before is as weak as the close. The overnight coefficient leans towards reversal but is noise. **There is no
front-running to find, because there is no close effect to front-run.**

## 5. E — a noisy measure? No: both books carry real information

| short-gamma dummy on | log RV (t, percentile) | 5-minute ρ1 (t, percentile) | short share |
|---|---|---|---:|
| SPX GEX | +0.960 (12.1, 1.000) | +0.011 (1.26, 0.85) | 12.5% |
| ES book (prior close) | +0.642 (12.1, 1.000) | +0.021 (3.56, 0.999) | 43.1% |
| SUM | +0.729 (12.8, 1.000) | +0.019 (3.02, 0.995) | 30.3% |

- **Both books order variance independently.** Jointly, SPX +0.71 (t 9.2) and ES +0.48 (t 9.7).
- **The ES book's sign carries the path's autocorrelation better than SPX's.** Its 43% short share is not convention
  noise, and it answers D681's open premise question in the book's favour.
- **The close slope** is +0.17 (t 1.6, n 1,380) where the books agree, and −0.15 (t −0.6, n 609) where they disagree.
- **On SPX's long-gamma days (87%) the close slope has the wrong sign:** −0.45 (t −1.9). The predicted reversal is
  absent, and it leans the other way.

## 6. F — the controls absorb it? No

| controls | none | r | Z_L | σ_d | r + σ_d | all three (D681) |
|---|---:|---:|---:|---:|---:|---:|
| β_G | +0.127 | +0.109 | +0.113 | +0.125 | +0.108 | +0.122 |
| NW t | 1.12 | 1.08 | 1.11 | 1.13 | 1.08 | 1.23 |

- Pooled, corr(Z, r) is +0.18 and corr(Z, Z_L) is +0.10.
- **Within each regime, however, Z and the LETF push are ±0.91 correlated,** since both scale with √|r|. **D681's
  within-regime slopes (+0.55 short, −0.01 long) are therefore poorly identified against the LETF control,** and should
  not be read as a clean regime contrast.

## 7. G — concentration: yes, the pooled slope is one episode

| sample | β_G | NW t | n |
|---|---:|---:|---:|
| all (D681) | +0.122 | 1.23 | 1,989 |
| **without 2020** | **+0.033** | **0.52** | 1,743 |
| **without 2020-02-20 → 04-30** | **+0.038** | **0.65** | 1,943 |
| without the top 1% of \|R2\| | +0.022 | 0.44 | 1,969 |
| **short gamma, without 2020-02-20 → 04-30** | **+0.059** | **0.24** | 577 |
| \|Z\| tercile low / mid / high | +0.278 / +0.013 / +0.136 | 1.24 / 0.09 / 1.25 | 663 each |

**D681's one surviving hint, the short-gamma continuation (+0.55), falls to +0.06 without the crash window** (46
sessions, 26 of them short-gamma). Outside that window the close slope is about a thirteenth of Y = 0.5.

## 8. What the diagnostic says

**Scored against the declared fingerprints:**

| | explanation | fingerprint | reading |
|---|---|---|---|
| A | too little impact | expected t < 2 at Y = 0.5 | **Rejected.** Expected NW t 5.0; the flow is 8.6% of the closing half-hour's volume at the median |
| B | continuous hedging | ρ1 and RV fall with gamma, beyond the rotation null | **Supported,** beyond every rotation (see §2's volatility caveat) |
| C | the wrong move to hedge | a shorter lookback predicts better | Rejected |
| D | anticipated or temporary | earlier push, or an overnight reversal | Not found |
| E | a noisy measure | the ES sign orders nothing | **Rejected.** Both books order variance at t ≈ 12 |
| F | the controls absorb it | β rises without controls | Rejected; within-regime collinearity noted |
| G | concentration | β moves by more than one SE without the crash | **Supported:** +0.12 → +0.04 |

**The principal's question.** The mechanism did not fail for lack of force. Dealers' gamma demonstrably moves the path:
it halves the day's variance and deepens its mean reversion when they are long gamma. **What failed is D681's timing
assumption:** that the day's hedging accumulates and lands in the last half-hour. The data say it lands as the price
moves.

This is the same shape as B665 (gamma predicts size; a record on the unmerged branch `wt/after-d643`) and D581 (the ES book does not sort the close), now with
a mechanism: **the hedge flow is a damper applied continuously, so it shows up as lower variance and more reversal
along the path, not as a directional push at any fixed clock.**

**What this suggests, for the principal (nothing is tested here, and every in-sample fact above is spent for selection).**
- **Close D681's construction:** the close, and any fixed clock.
- **Gamma is a path-state variable.** Its natural uses are the ones the memory already lists (size, stops, the
  expected-profit filter's magnitude term), plus one new one: **the strength of intraday mean reversion.**
  - A reversion or fade construction on a slower bar, gated to long-gamma days, is the mechanism's own direction.
    The 5-minute effect is far below cost, so it would need a slower bar.
  - A breakout or continuation construction should stand aside on long-gamma days.
  - Both would need their own pre-registration, and a check on the volatility confound in §2 first.

## Addendum, 2026-09-29: §2 narrowed by D684

[D684](D684-SIZING-no-go-the-long-gamma-fade-is-far-below-cost.md) ran the check this record left open: the same-day
volatility control.
- **With the day's realised variance up to each decision as a control, the 5-minute gamma gradient is not
  distinguishable from zero** (c −0.0065, t −0.62, the 31st percentile of the rotation null). §2's "long gamma
  deepens the path's mean reversion" is therefore mostly the volatility level.
- **Unchanged:** §1 (not too little impact), the realised-variance result, and §7 (the crash concentration).
- **What gamma adds beyond volatility, at 30–60 minutes,** is short-gamma continuation (D684 §2 and §4).
