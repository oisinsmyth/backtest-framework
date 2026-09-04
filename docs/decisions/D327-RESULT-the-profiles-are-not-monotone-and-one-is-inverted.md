# D327 RESULT — no profile is monotone, one is inverted, and the buckets are too coarse

**Status:** RESULT. Pre-registered at `b8a2530`, runner at the commit before this
file existed (R8).
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is promoted. There is no path here, so nothing here can be priced.**

---

## 1. Q2 confirms — no signal has a monotone rank profile

Edge by rank bucket, k = 20, cross-sectionally demeaned. Bucket 0 is the **long**
end, 19 the **short** end.

| signal | 0 | 1 | 2 | 4 | 6 | 9 | 13 | 15 | 17 | 18 | **19** |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **hist_L** | **+50** | +22 | +19 | +5 | −1 | −5 | −5 | −13 | +1 | +10 | **+38** |
| retrace_leg | +28 | +16 | +12 | +10 | +13 | +3 | +1 | −2 | −11 | −16 | −27 |
| **skew_63** | −2 | −8 | −10 | +7 | +15 | +7 | −2 | +19 | −8 | −3 | **−6** |
| rsi | +52 | +16 | +12 | +12 | +8 | +5 | +4 | −7 | −10 | −9 | −19 |
| **macd_hist** | **−35** | +0 | +8 | +14 | **+29** | +23 | +11 | +0 | −6 | −28 | **−79** |
| price_log | **+190** | +80 | +46 | +25 | −7 | −8 | −19 | −23 | −16 | −21 | −80 |

Monotone fraction runs **0.58 to 0.79** — none is a clean cross-sectional factor.

## 2. `hist_L`'s short leg is ACTIVELY HARMFUL, and assertion [1] found it

**Both ends of `hist_L` are positive: +50 at bucket 0 and +38 at bucket 19.** The
book *shorts* bucket 19, so it is shorting names that rise 38 bp. Spread is
**+11**, and the long end is **433%** of it.

**That is why `hist_L` alone was one of the worst constructions in D326** — −13.10
per trade, `mean/2c` 0.86. It is not a weak signal. **It is a good long signal
paired with a short leg that gives most of it back.**

D283 recorded that "symmetry fails BY SIGN" on this programme's short work. **This
is that finding arriving inside the incumbent's own primary**, and no book-level
study could have seen it.

## 3. `macd_hist` is INVERTED at the long end and its edge is in the MIDDLE

```
bucket      0     2     6     9    13    18    19
edge      -35    +8   +29   +23   +11   -28   -79
```

**Its bucket-0 names FALL.** Longing them is wrong. Its short end is the
strongest in the study at −79. Its peak long-side edge is at **bucket 6**, a fifth
of the way down the ranking.

**This explains the pair effect D325 and D326 could not.** `macd_hist` alone is
the worst construction measured (−23.69 per trade) because a top-2 book longs
exactly the bucket where it is inverted. **Inside the composite it is never used
that way** — it supplies a *percentile* that re-ranks another signal's gate, so
the book harvests its middle-of-range information and never touches its broken
long end.

**"Which signals combine matters more than how strong they are individually" now
has a mechanism**: a signal can carry information at depths its own book never
trades, and a composite is a way of reaching it.

## 4. Q5 FALSIFIED — and the reason is a limitation of this study

**Spearman between extreme-bucket edge and D326's per-trade ranking is −0.200.**
Two signal lenses that should agree, disagree.

**`skew_63` is the case in point.** Its rank profile is nearly flat — spread
**+3 bp**, the smallest here — yet D326 gave it the **best** per-trade net in the
study (+56.22) at 4.53× cost coverage.

**The lenses are measuring different depths.** Bucket 0 is the top **5%** of ~988
live names — about **49 names**. The book holds **2**. **My buckets average away
exactly the region the book trades**, and a top-2 effect is invisible at
5-percentile resolution.

**So Q5's failure is not evidence against either lens. It is evidence that 20
equal buckets are the wrong instrument for a 2-name book**, and that is a defect
in this study's design, declared here rather than explained away.

**`skew_63`'s cost coverage remains unexplained**, and §5 shows its cost profile
is not the answer either.

## 5. Q3 confirms, but it does not explain `skew_63`

Median half-spread by bucket: `skew_63`'s extremes average **15.3 bp** against the
other signals' **16.8**. Cheaper, as predicted — **but marginally**, and its rank
edge is the flattest in the study. **A 9% cost advantage does not produce 4.53×
coverage against everyone else's 2.0.** The mechanism is still open, and §4 says
where to look: finer buckets at the extreme.

**`price_log`'s cost profile is the striking one** — **38.8 bp** at bucket 0
falling to **10.1** at bucket 18. Its long end is the most expensive region in the
study, which is D284's grave stated as a profile: **the largest rank edge here
(+270 spread, ratio +2.45 at bucket 0) sits in the names that cost the most to
trade.**

## 6. Q7 falsified — longer holds are not uniformly flatter

Extreme spread at k=20 → k=40: `hist_L` +11 → +17 (steeper), `retrace_leg`
+55 → +44 (flatter), `price_log` +270 → +526 (much steeper). **Mixed, so the
prediction that a longer hold buys cost savings with signal is wrong as a general
claim** — it depends on the signal's own decay.

## 7. Predictions

| | prediction | outcome |
|---|---|---|
| **Q1** | the spread is signed correctly and reversing flips it | **CONFIRMED** — and it fired first in a stronger form, see §2 |
| **Q2** | **no monotone profile** *(against, load-bearing)* | **CONFIRMED** — 0.58 to 0.79 |
| **Q3** | `skew_63`'s extremes are cheaper | **CONFIRMED** — 15.3 against 16.8, but §5 says it is not the answer |
| **Q5** | the two signal lenses agree, ρ > 0.7 | **FALSIFIED** — ρ = **−0.200**, and §4 says why |
| **Q7** | flatter at k=40 | **FALSIFIED** — mixed |
| **Q8** | *(not pre-registered — added after [1] surfaced the asymmetry)* | long-end share of the spread: `hist_L` **433%**, `macd_hist` **−80%**, `retrace_leg` 51%, `rsi` 73% |

## 8. What this establishes

1. **No signal here is a cross-sectional factor.** Every profile is a tail effect
   with a noisy middle, which is the depth-free reason a concentrated book beats a
   wide one — and it settles on one measurement what six book-level studies argued
   about.
2. **`hist_L`'s short leg destroys most of its edge.** The incumbent's primary is
   a long signal wearing a spread book.
3. **`macd_hist` carries real information at depths its own book cannot reach**,
   which is a mechanism for the composite effect and the first explanation this
   programme has produced for it.
4. **`skew_63`'s cost coverage is not explained by its cost profile**, and this
   study's resolution cannot see where it comes from.

## 9. What is owed

1. **Finer buckets at the extreme** — the top and bottom 1% split out, so the lens
   can see the region a 2-name book actually trades. §4 is the reason and it is
   this study's own defect.
2. **A long-only reading of `hist_L`**, given §2. The incumbent has never been run
   without its short leg.
3. **`skew_63` remains open** and is now more interesting, not less.

## 10. Assertions

All seven pass. **[1] is the one that produced §2** — it fired on a sign
convention I had over-specified, and the failure was the finding.

| | |
|---|---|
| **[1]** | the spread is signed correctly and reversing flips it. *The first form asserted both ends' signs and fired: bucket 19 is POSITIVE. That asserted a property of the DATA, not the code — the same shape of error `[S]` had twice in D324* |
| **[2]** | causality — peeking moves the profile by up to 2.8 bp |
| **[3]** | the 20 buckets partition evenly, 129,482 to 132,556 name-bars each |
| **[4]** | **the demeaning is exact to 3.1e-17 at every bar**, so the profile sums to zero and cannot show a spurious level |
| **[C]** | the ratio is edge / (2 × half-spread) — one name crossing twice — and the paired 4× form is rejected |
| **[6]** | the check raises on a bucket handed free money |

## 11. Files

`data/d327_rank_profile.json` · `scripts/run_d327_rank_profile.py`

---

## 12. AMENDMENT, 2026-09-04 — §3 and §4 are both superseded by D328

Appended, not edited. The body above stands as written.

**§3 is wrong in its interpretation, and the measurement that replaces it is
plain.** `macd_hist` is computed on **raw closes** and is denominated in
**dollars**, so its extreme ranks are a **price sort**: median price **$2,706**
at rank 0 and **$3,020** at the opposite extreme, against a **$22** middle. Its
−35 at bucket 0 and −79 at bucket 19 are one expensive-name effect measured
twice, not "an inverted long end with information in the middle." Its middle `t`
of +9.62 is real; the story about a composite *reaching a hidden depth* is not.
**The composite works on it because a 25-name gate compresses the price
dispersion its full-cross-section extremes were sorting on.**

**§4's declared defect was described correctly and inferred from wrongly.** The
buckets *were* averaging the extremes away — at rank 0–1 the edges are **1.1× to
8.8×** what the top-5% bucket showed. But fixing it did not repair the lens
disagreement: **ρ went from −0.200 to −0.900.** Resolution was not the
explanation.

**§2 survives unchanged** — `hist_L`'s short end is still positive at single-rank
resolution, **+21 bp** at rank 0 from the short end.

See
[D328 RESULT](D328-RESULT-the-lenses-are-inverted-and-two-signals-rank-price.md)
and [FINDINGS §14](../FINDINGS.md#14-a-cross-sectional-ranking-on-a-quantity-that-carries-units-ranks-those-units).
