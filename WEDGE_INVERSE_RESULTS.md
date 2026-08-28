# D249 — the inverse wedge breakout

**PROVENANCE: complement of a failed construction -- registered separately, NOT S3.** D246 Constraint 3 makes an inverse-of-a-failed-cell ineligible under the S3 search protocol, so this is registered on its own merits. **D245's reserved never-seen cohort is not spent here.**

*seed 0, 1,000 rotations, 1,000 bootstrap draws at block 21, 109.0s. Screen: 57 ETFs x 3,222 live bars, 2013-11-01 .. 2026-08-26. Validation: 60 ETFs x 1,963 bars, 2018-11-01 .. 2026-08-26. k=3, window 252, ATR(21), armed at width ≤ 2·ATR, trigger ±2·ATR.*

## The one-sentence version

**The wedge down-break is not a per-instrument signal — it fires across the universe at once, holding up to 41 of 57 names simultaneously where a rotated book never exceeds 23 — so W2 builds a book 2.2× more volatile than its own null, earns more money than 99.8% of rotations and less per unit of risk than the median one, and on the holdout it is not paid at all.**

## The reading, as declared in advance

> **NO CELL SURVIVES THE HOLDOUT. The inverse wedge breakout is CLOSED under D249's stop -- no fourth holding rule, no re-cut arming threshold, no wider universe.**

## The setup structure — verified before the pre-registration, R9-compliant

**50.7%** of 183,654 live cells have converging lines. Channel width among those, in ATRs:

| p5 | p10 | p25 | p50 | p75 |
|---:|---:|---:|---:|---:|
| 1.26 | 1.61 | 2.13 | 2.64 | 3.15 |

| arming threshold | share of cells | episodes | per symbol |
|---|---:|---:|---:|
| width ≤ 1.0·ATR | 1.53% | 676 | 11.9 |
| width ≤ 2.0·ATR **← registered** | 10.32% | 3,021 | 53.0 |
| width ≤ 3.0·ATR | 34.76% | 5,586 | 98.0 |

**Episodes are not entries, and that is the correction D249 registered as T-a.** The 57 produce **1,474 down-breaks** and **1,099 up-breaks**; the up leg is never traded, and **799** further down-breaks are suppressed as overlapping at the 42-bar hold. What reaches the book is in the `entries` column below.

## The screen — the mined 57

| | | exposure | **net exSh** | *gross* | CAGR | deployable | max DD | Calmar | breakeven | entries | min/sym | E |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:--:|
| **W1** | down-break, hold 21 | 9.8% | **+0.115** | *+0.125* | 0.92% | 4.56% | -17.54% | 0.053 | 24.9 bp | 853 | **5** | ✗ |
| **W2** | down-break, hold 42 | 15.4% | **+0.265** | *+0.272* | 2.11% | 5.55% | -18.24% | 0.116 | 81.6 bp | 675 | **4** | ✗ |
| **W3** | W2 + stop at entry − 2·ATR | 9.3% | **+0.318** | *+0.335* | 1.05% | 4.71% | -4.66% | 0.226 | 38.7 bp | 675 | **4** | ✗ |
| *S1* | *for scale* | *18.2%* | *+0.478* | — | *3.11%* | *6.47%* | *-10.28%* | *0.303* | — | *2374* | *20* | — |
| *S2* | *for scale* | *13.3%* | *+0.511* | — | *1.85%* | *5.37%* | *-5.83%* | *0.318* | — | *393* | *5* | — |
| *B&H* | *always long* | *100.0%* | *+0.242* | — | *7.84%* | *7.84%* | *-34.55%* | *0.227* | — | — | — | — |

**Effective independent instruments: 2.29.** D245 measured 2.23 for this universe and found it *falls* as headcount grows. **The pooled trade count is not a sample size and is not quoted as one.**

## Hurdle H — the matched-count rotation null, which carries the verdict

*Same exposure, same turnover, same holding periods, wrong bars. **Money is a hurdle leg here, not a diagnostic** — a book that concentrates exposure right after 2-ATR declines is exposed in noisy weather by construction, and Sharpe alone cannot tell that from skill.*

| | actual | null p95 | **pctile** | money | money p95 | **pctile** | vol ratio | H |
|---|---:|---:|---:|---:|---:|---:|---:|:--:|
| **W1** | **+0.115** | +0.457 | **29.0th** | +12.48% | +15.28% | **81.2th** | 2.770x | ✗ |
| **W2** | **+0.265** | +0.429 | **63.0th** | +30.55% | +23.59% | **99.8th** | 2.204x | ✗ |
| **W3** | **+0.318** | +0.455 | **74.7th** | +14.31% | +15.18% | **91.8th** | 1.292x | ✗ |

**The two legs disagree, and the vol ratio is why — this is the finding.**

*Money earned per unit of volatility, actual against the null's median. If the timing found genuinely better bars this ratio rises; if it merely found louder ones and was paid the going rate, it does not.*

| | vol | null vol p50 | **ratio** | money/vol | null money/vol | better bars? |
|---|---:|---:|---:|---:|---:|:--:|
| **W1** | 4.66% | 1.68% | **2.77x** | 2.68 | 5.72 | ✗ |
| **W2** | 5.59% | 2.54% | **2.20x** | 5.47 | 6.40 | ✗ |
| **W3** | 2.15% | 1.66% | **1.29x** | 6.67 | 5.98 | ✓ |

**The measured +15% to +18% annualised after a down-break is compensation for risk, not timing skill.** The rotation null matches exposure, turnover and holding periods — **it does not match the volatility of the book that results**, and that gap is the entire distance between the money column and the Sharpe column.

### Where that volatility comes from — and it is NOT the obvious answer

*Two candidates, and they separate cleanly. **Loudness**: the bars it holds are individually more volatile than average. **Clustering**: it holds many names at the same time. `rotation_nulls` draws an independent offset per symbol, so it destroys cross-sectional synchrony by construction.*

| | loudness | names held, mean | max | *rotated max* | bars over 20 names | *rotated* | clustering |
|---|---:|---:|---:|---:|---:|---:|---:|
| **W1** | 1.22× | 5.6 | **36** | *19* | **4.3%** | *0.0%* | **1.44×** |
| **W2** | 1.14× | 8.8 | **41** | *23* | **13.7%** | *0.0%* | **1.36×** |
| **W3** | 0.89× | 5.3 | **30** | *19* | **2.0%** | *0.0%* | **1.33×** |

**The bars are barely louder than average (1.14×). The book is vastly more crowded.** W2 holds more than 20 of 57 names on **13.7%** of bars where a rotated book of identical exposure does so on **0.0%**, and it peaks at **41** names against the rotation's **23**. **Converging channels break downward together, because they break when the market falls.**

**So the rule is a market timer wearing a per-instrument signal.** It is not selecting which ETF to buy; it is selecting *when* to buy all of them. That is a legitimate thing to be — it is roughly what S1 is — but it means the diversification across 57 names that the equal-weighted book appears to have is largely illusory on exactly the bars that matter, and it is why the book carries an −18% drawdown at 15% exposure where S2 carries −5.8% at 13%.

**A limitation of the null, recorded rather than buried:** a per-symbol rotation null **understates the volatility of any book whose signal is market-wide**, so it is a *conservative* control for such a rule on money and a *harsh* one on Sharpe. Both legs were registered, and between them they bracket the truth — which is the practical argument for the two-legged form.

**D249 registered the money leg for the opposite reason and it caught this anyway.** The record's argument was D238's: a high-volatility book could inflate its *Sharpe*, so money was added as the leg that cannot be inflated. What happened is the mirror image — **money was the inflated leg and Sharpe was the honest one** — because D238's arm had a negative mean and this one does not. The reasoning was pointed the wrong way; requiring *both* legs is what made that harmless.

### H-BEST — the multiplicity leg

*Three cells screened, one shared offset vector per simulation (D228). **D240's stop cleared at the 99.6th percentile with no correction and failed out of sample at the 71.7th.***

| best cell | actual | best-of-3 floor | pctile | actual money | money floor | pctile | H-BEST |
|---|---:|---:|---:|---:|---:|---:|:--:|
| **W3** | +0.318 | +0.505 | **60.0th** | +14.31% | +23.59% | **34.9th** | ✗ |

### H-OVL — R7, scoped to the stop cell

*A rotation null is the wrong control for something that modifies a book W2 already chose. Keep W2's book; cut the same number of trades short at random trades and random points inside their own spans.*

| | trades cut | actual | null p50 | null p95 | **pctile** | H-OVL |
|---|---:|---:|---:|---:|---:|:--:|
| **W3** | 381 of 675 | **+0.318** | +0.208 | +0.293 | **97.9th** | ✓ |

## THE OVERLAP ANALYSIS — is this a new arm, or S1 with a different trigger?

*S1's own exposure is the chance baseline: if the two rules were independent, `P(S1 | wedge)` would equal S1's exposure exactly. D242 measured **8.9%** for S2 — less than half chance — which is what a structurally disjoint arm looks like.*

| | `P(S1 \| wedge)` | *chance* | `P(wedge \| S1)` | *chance* | `P(S2 \| wedge)` | `P(wedge \| S2)` |
|---|---:|---:|---:|---:|---:|---:|
| **W1** | **28.2%** | *18.2%* | **15.1%** | *9.8%* | 7.2% | 5.3% |
| **W2** | **32.5%** | *18.2%* | **27.6%** | *15.4%* | 6.9% | 8.0% |
| **W3** | **29.5%** | *18.2%* | **15.1%** | *9.3%* | 8.0% | 5.6% |

**Correlation of the daily excess-return streams, with the paired block bootstrap interval — both arms recomputed on identical resampled dates:**

| | ρ with S1 | p05 | p95 | ρ with S2 | p05 | p95 |
|---|---:|---:|---:|---:|---:|---:|
| **W1** | **+0.1988** | +0.138 | +0.370 | +0.3992 | +0.208 | +0.560 |
| **W2** | **+0.3886** | +0.257 | +0.588 | +0.3824 | +0.206 | +0.539 |
| **W3** | **+0.3815** | +0.308 | +0.478 | +0.3017 | +0.226 | +0.388 |

**The diversification condition, `SR_B > ρ · SR_A`** — evaluated against both arms. *A weak incumbent makes this a weak test, which D249 registered as T-e.*

| | actual | bar vs S1 | vs S1 | bar vs S2 | vs S2 |
|---|---:|---:|:--:|---:|:--:|
| **W1** | **+0.115** | +0.095 | ✓ | +0.204 | ✗ |
| **W2** | **+0.265** | +0.186 | ✓ | +0.196 | ✓ |
| **W3** | **+0.318** | +0.183 | ✓ | +0.154 | ✓ |

**The S1-excluded residual** — W2's book with every bar S1 also holds removed, keeping **67.5%** of its bars: excess Sharpe **+0.190** at 10.4% exposure, +18.69% total return. *Declared as a diagnostic in D249 and counted; not a cell.*

### O4 — the direct answer, as D249 required it

> **NEITHER. It is not S1 in disguise -- overlap peaks at 32.5% of the wedge's held bars against a 18.2% chance baseline (1.79x chance) with rho at most +0.389, so the two rules lean on a shared population without being the same rule. But it is not a new arm either, and that is the operative half: there is no edge here to diversify. No cell beats its rotation null on the screen, and on the holdout the best of the three sits at the 7.3th-15.7th percentile of randomly-timed books holding the same amount. What the two rules share is the thing the concurrency measurement names: both are buying broad market weakness. The wedge holds up to 41 of 57 names at once, so it is a market timer wearing a per-instrument signal, and S1 is the same bet made better.**

## Validation — the 60-ETF instrument holdout

*The wedge rule has never touched these 60 names. **The cohort is not pristine at the universe level** — it was spent on S1 (D237) and on A0/A2/C0 (D242) — and its span is shorter than and nested inside the screen's era, so this tests instruments and not time.*

| | | exposure | **net exSh** | *gross* | CAGR | deployable | max DD | Calmar | breakeven | entries | min/sym | E |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:--:|
| **W1** | down-break, hold 21 | 9.2% | **+0.001** | *+0.010* | 0.37% | 4.01% | -18.16% | 0.020 | 2.6 bp | 515 | **1** | ✗ |
| **W2** | down-break, hold 42 | 14.4% | **+0.115** | *+0.121* | 1.34% | 4.80% | -19.60% | 0.068 | 46.4 bp | 405 | **1** | ✗ |
| **W3** | W2 + stop at entry − 2·ATR | 8.2% | **-0.021** | *+0.001* | 0.28% | 3.96% | -4.78% | 0.060 | 0.1 bp | 405 | **1** | ✗ |
| *S1* | *for scale* | *19.6%* | *+0.660* | — | *4.45%* | *7.79%* | *-9.04%* | *0.492* | — | *1585* | *14* | — |
| *S2* | *for scale* | *13.2%* | *+0.468* | — | *1.75%* | *5.27%* | *-5.67%* | *0.308* | — | *271* | *2* | — |
| *B&H* | *always long* | *100.0%* | *+0.326* | — | *9.86%* | *9.86%* | *-37.92%* | *0.260* | — | — | — | — |

| | Δ vs B&H | floor | null p95 | **pctile** | money pctile | H | P | floor | **all** |
|---|---:|---:|---:|---:|---:|:--:|:--:|:--:|:--:|
| **W1** | **-0.325** | -0.032 | +0.564 | **10.1th** | 10.6th | ✗ | ✗ | ✗ | **✗** |
| **W2** | **-0.211** | +0.006 | +0.545 | **15.7th** | 55.6th | ✗ | ✗ | ✗ | **✗** |
| **W3** | **-0.348** | +0.019 | +0.580 | **7.3th** | 7.2th | ✗ | ✗ | ✗ | **✗** |

**Effective independent instruments on the 60: 2.14.**

### The screen restricted to the validation span, so the two are comparable

*The 57 scored only over 2018-11-01 onward — same era, different instruments.*

| | 57, matched span | 60, full |
|---|---:|---:|
| **W1** | +0.059 | +0.001 |
| **W2** | +0.243 | +0.115 |
| **W3** | +0.240 | -0.021 |
| *S1* | *+0.626* | *+0.660* |
| *S2* | *+0.673* | *+0.468* |
| *BH* | *+0.363* | *+0.326* |

## Intervals — reported for width, not as a verdict

*Block 21, paired on identical resampled dates. At 2-odd effective instruments no interval here is going to be narrow.*

| | excess Sharpe | p05 | p95 | excludes 0 | Δ vs B&H | p05 | excludes 0 |
|---|---:|---:|---:|:--:|---:|---:|:--:|
| **W1** | +0.115 | -0.276 | +0.764 | ✗ | -0.127 | -0.399 | ✗ |
| **W2** | +0.265 | -0.192 | +0.835 | ✗ | +0.023 | -0.257 | ✗ |
| **W3** | +0.318 | -0.165 | +0.802 | ✗ | +0.075 | -0.283 | ✗ |
| **S1** | +0.478 | -0.036 | +0.917 | ✗ | +0.236 | -0.198 | ✗ |
| **S2** | +0.511 | +0.066 | +0.989 | ✓ | +0.269 | -0.134 | ✗ |

