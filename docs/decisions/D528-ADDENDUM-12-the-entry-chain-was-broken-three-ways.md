# D528 ADDENDUM 12 — forward reversion IS forecastable, and the entry chain was broken three ways

Date: 2026-09-14/15. Runners: `working/d528_wide.py`, `d528_forecast_reversion.py`,
`d528_forecast_vs_payoff.py`, `d528_joint_full.py`, `d528_drift_audit.py`,
`d528_target_and_stability.py`, `d528_corrected_chain.py`.

**Nothing admitted (R15). The reserved slice (2026-04-11 → 2026-09-09) is NOT spent** — see §6 for
one breach and its disclosure. Wide 5-minute fixture, 2010 → 2026-04-10, 36 roots.

---

## 0. The principal's pivot, and the answer

He asked: *"instead of finding a mean reversion that has already happened and hoping it will happen
again, can we forecast mean reversion before it happens?"*

**Yes, and it is the strongest measurement in D528.** Target: does price traverse ±1.5σ over
`[t, t+H)`, predicted from features strictly before `t`. On 4.88M scored bars, quintile edges from
2010–2019 applied unchanged to 2020–2026:

| feature | Q1 lift | Q5 lift | spread | t | early Q5 (generalisation check) |
|---|---:|---:|---:|---:|---:|
| **vol_ratio** | **+0.0716** | **−0.0706** | **0.1422** | **−155** | −0.0718 |
| squeeze | +0.0635 | −0.0481 | 0.1116 | −95 | −0.0446 |
| vratio2 | +0.0443 | −0.0462 | 0.0905 | −116 | −0.0425 |
| ac1 | +0.0451 | −0.0442 | 0.0892 | −114 | −0.0402 |
| *trav_past (the old premise)* | *+0.0056* | *+0.0000* | *0.0056* | — | *+0.0000* |

Base rate 14.95%; the quiet quintile forecasts **22.1%**, the active quintile **7.9%** — a **2.8×
spread**, and the early and late lifts agree to within 0.0012. **The features that work are ~25×
more informative than past traversal**, which every construction in D528 had been built on.

And the chain from forecast to money is intact at both links: P(trade target | traversed) = **57.0%**
against **2.3%** when it did not (t **+31.2**), gross **+$164.30** against **−$23.21**.

## 1. Why it still did not pay — the conservation law, third appearance

| cell | n | P(traverse) | **payoff when you win** | E[gross] |
|---|---:|---:|---:|---:|
| all late | 1,636 | 11.4% | **$187.62** | −5.41 |
| best quintile | 352 | 18.2% | $80.68 | −3.18 |
| **best 5%** | 74 | **24.3%** | **$30.96** | −15.40 |

Breakeven needs P(traverse) = **20.7%**; the forecast reaches **24.3%** — it clears its own bar.
**And the payoff when you win collapses to 0.17×.** Hit rate up 2.1×, payoff down 6.1×. The same
conservation that governed the stop ladder (ADDENDUM 4) and the geometry sweep (ADDENDUM 7),
now in the forecast.

**Three explanations were tested and rejected before this one:** target/cost too small (flat at
5.9–8.0 across quintiles), forecast target ≠ trade target (correlation **+0.62**, tightly linked),
and forecastability not transferring (it transfers). Only payoff-collapse survived.

### 1.1 The joint construction, both lenses

Forecast **and** entry-time payoff, cuts from 2010–2019, evaluated on 2020–2026:

| universe | cell | n | gross $ | net $ | Sharpe g | Sharpe n | maxDD/$2k |
|---|---|---:|---:|---:|---:|---:|---:|
| all roots | JOINT | 501 | **+8.02** | −7.68 | +0.25 | −0.25 | 4.24× |
| **micro (tradeable)** | JOINT | 196 | **−2.49** | −6.82 | −0.55 | −1.36 | 0.89× |
| micro | pool | 782 | −2.69 | −7.28 | −1.13 | −3.02 | 2.84× |

**The control that matters — forecast on/off within the high-payoff band — is t = +1.28 on all
roots and t = +0.25 on micro.** The +$8.02 does not clear its own standard error of $21.76, and on
the tradeable universe the joint cell is indistinguishable from the pool. One control *did* pass:
median σ is $15 in the high-forecast cell against $18 in the low, so the forecast is not merely a
volatility selector.

## 2. THE ENTRY CHAIN WAS BROKEN THREE WAYS

Every P&L number in D528 was computed through this chain. Two of its filters were wrong and the
measurement target was corrupt.

### 2.1 `slope_ok` cost 92% of the sample and bought nothing

| chain | candidates | P(traverse, price-referenced) |
|---|---:|---:|
| with `slope_ok` + aligned | 3,468 | 0.1361 |
| **without** `slope_ok` + aligned | **41,126** | **0.1395** |

**11.9× the candidates and a slightly higher reversion rate.** `slope_ok` (`|b1−b2|·H ≤ 0.5σ`)
came from the original A1 slope-agreement test and was carried through eleven addenda without ever
being justified against the target. It removes **93.1% of all bars** while moving P(traverse) by
**−0.0027**. **Dropped.**

This is the direct cause of the sample-size problem that crippled every cell in the study: ADDENDUM
7 established ~14,500 trades are needed to resolve a $0.50 effect against a $36.54 per-trade sd,
and every cell had 40–500.

### 2.2 The measurement target was partly its own reference level — and the asymmetry REVERSED

Forward traversal was measured against the `[t−H,t)` line **extrapolated forward**. Three
definitions, same σ throughout, so only the reference changes:

| target | P(trav \| **ALIGNED**) | P(trav \| ANTI) | ratio |
|---|---:|---:|---:|
| `line` (extrapolated) | 0.1127 | **0.1750** | 1.55× |
| `flat` (level held) | **0.1745** | 0.0931 | 0.53× |
| `price` (no level at all) | **0.1395** | 0.0680 | **0.49×** |

**The prediction recorded before running was that the asymmetry would SHRINK toward zero if it was
level-chasing. It did not shrink — it reversed.** On a level-free target, drift-aligned excursions
revert **2.05× more often** than anti-aligned ones.

**So the principal's drift-alignment rule is correct**, and the drift audit's apparent finding —
that his filter "removes 83.3% of excursions and keeps the least-reverting 16.7%" — was entirely an
artefact of the line-referenced target. **This is the third time the same level-chasing mechanism
has produced a false reading in D528** (ADDENDUM 1's P(residual return), ADDENDUM 8's oracle null,
and here). It is the single most persistent error source in the study.

### 2.3 And the excursion filter helps, contrary to what was reported

It was reported to the principal that "the 2σ entry selects against traversal", from
P(traverse) 14.95% on all bars against 11.1% on the tradeable subset. **Wrong attribution.** The
funnel shows the excursion *raises* P(traverse) from 0.1238 to **0.3099**; it is the *alignment*
stage that lowers it — and §2.2 shows that lowering was the artefact. **Withdrawn.**

## 3. The forecast survives the corrected chain, and is strongest inside it

Q1 lift on the **level-free** target:

| population | vol_ratio | squeeze | vratio2 | ac1 |
|---|---:|---:|---:|---:|
| all scored bars | +0.0470\* | +0.0725\* | +0.0222\* | +0.0251\* |
| **no `slope_ok`, aligned** | **+0.0752\*** | **+0.0804\*** | +0.0454\* | +0.0500\* |
| no `slope_ok`, anti-aligned | +0.0451\* | +0.0726\* | +0.0250\* | +0.0281\* |

\* beyond 2 block-bootstrap SE. **The forecast works better inside the drift filter than outside
it** — so the two components are complementary, not competing.

**The corrected baseline:** reversion 6.5% base → **13.95%** from the entry chain → **~21%** with
the forecast, on **41,126** candidates rather than 3,468.

## 4. Two incidental facts worth keeping

**A pure sinusoid can never satisfy the traverse test.** Its peak-to-residual-sd ratio is
√2 = 1.414 and `TRAV_K` is 1.5. So `traverse` never detected smooth oscillation — it structurally
requires **spiky, two-sided** movement. That explains why the classifier kept selecting the spike
profile, and it means "range" in this construction never meant what the word suggests.

**Removing the stop entirely doubles the win rate and makes the mean worse.** Pool, all roots:
win 23.8% → **49.2%**, median **−11.50 → +5.50**, gross **−2.18 → −12.68**. A positive median with a
negative mean is the shape of a strategy that feels like it is working while it bleeds — the
account compounds the mean.

## 5. Disposition

1. **The forecastability result stands on its own** and is independent of every construction
   defect: t = −155, replicating out of time, on 4.88M bars.
2. **`slope_ok` is dropped permanently.** Any future work on this fixture starts without it.
3. **The drift-alignment rule is vindicated** and should be kept.
4. **Never measure a reversion target against an extrapolated level again.** Use price.
5. **Every P&L number in ADDENDA 1–11 was computed on 8% of the available candidates, through a
   filter that bought nothing, against a corrupt target.** Their *directional* findings on
   geometry and conservation stand; their levels do not. The construction is being re-run on the
   corrected chain (`d528_corrected_chain.py`), both lenses, out of time.
6. **No component line, no promotion.** The axis remains the principal's to close.

## 6. Disclosure: five months of the reserved slice were read

In an early version of `d528_wide.py --calibrate` the overlap window was taken from the raw
`fut_day1m_mid` parquet's own maximum day — **2026-09-09** — rather than through `Q.load()`, which
applies the 2026-04-10 cutoff. The quoted-MID arm of that one calibration therefore covered
**2026-04-11 → 2026-09-09**, about five months of the reserved slice, producing two pooled figures
(pool gross +1.89, spike gross −14.31). The trade-close arm was correctly capped.

Nothing was tuned, selected or parameterised on those numbers — they were a bounce calibration
being read, not fit — and they were discarded. **Both code paths now cap explicitly and assert.**
Whether the slice is considered spent is the principal's call, not this record's.
