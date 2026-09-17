# D413 ADDENDUM 2 — my cost estimate was measured on the wrong bars, and path efficiency splits the effect in two

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D413-ADDENDUM-2-the-cost-estimate-was-wrong-and-path-efficiency-splits-the-effect.md`. The H1 above is the full title.*

**EXPLORATORY, on data D413 has already spent. Clears nothing, admits nothing, changes no verdict.**
Everything here is **selected on spent data** and would need its own pre-registration and an
out-of-sample test before it means anything.

Written in response to three questions from the principal: raise the universe floor; is price the
right floor; and are the "confounds" actually carrying information. **All three were productive and
the first one exposed an error in [ADDENDUM 1](D413-ADDENDUM-the-distribution-the-confounds-resolved-and-the-cost.md).**

---

## 1. THE COST ESTIMATE IN ADDENDUM 1 WAS WRONG, AND THE PRICE QUESTION IS WHAT EXPOSED IT

Addendum 1 charged Corwin–Schultz measured **at the entry and exit bars** and concluded the edge
covered `0.17×` its cost. **The tell was already in its own table:** cost was 101 bp in the cheapest
price quintile, then *flattened* near 70 and *rose* again at $149. **Proportional spread should fall
roughly with 1/price. A flat profile is the signature of an estimator reading volatility, not
spread** — and Corwin–Schultz infers the spread from high/low ranges, so it cannot tell them apart.

**And the entry bars are selected for being volatile**: an entry happens exactly when price has just
travelled back into a zone. Estimating the spread there and nowhere else estimates it on the worst
possible subsample.

Measured against a **neutral** estimate — the name's median Corwin–Schultz over the 60 bars ending
2 bars *before* entry, causal and unselected:

```
price      event-bar    neutral    ratio
$ 13.6       68.0 bp     29.9 bp   2.27x
$ 26.9       57.3        25.9      2.21x
$ 41.9       52.2        23.7      2.20x
$ 67.1       50.7        22.1      2.29x
$149.3       53.3        22.3      2.38x
```

**The neutral estimate falls with price. The event-bar one does not.** The bias is a uniform ~2.2×.

**Corrected coverage on the full population: `0.41×` on the neutral mean, `0.50×` on its median —
not `0.17×`.** Real spreads *do* widen on active days, so the truth sits between the two; but
"six times short" was wrong and I am correcting it rather than leaving it in the record.

---

## 2. PRICE IS THE WRONG FLOOR. LIQUIDITY IS THE RIGHT ONE — and neither is sufficient

Coverage = gross / cost, on the **neutral** estimate. Dollar volume is the **trailing** measure the
universe floor itself uses, not the entry bar's own — an entry happens on an active day by
construction, and a floor built on the event bar's volume partly selects on the event's own spike.
Using the event bar's volume inflated the top-decile gross from **+11.52 to +17.15**, which is the
size of the error avoided.

```
all (current floor)          n 179,990   gross +13.22   cost 32.6   cov 0.41x
price >= $20                 n 144,523   gross  +8.14   cost 29.9   cov 0.27x
price >= $100                n  32,191   gross  +4.16   cost 27.6   cov 0.15x
dollar-vol top 25%           n  44,998   gross +11.98   cost 24.1   cov 0.50x
dollar-vol top 10%           n  18,000   gross +11.52   cost 22.1   cov 0.52x
price >= $50 AND dv top 10%  n  12,657   gross +13.99   cost 21.6   cov 0.65x
```

**Raising the price floor makes it worse** — gross falls faster than cost does, from +13.22 to
+4.16. **Raising the liquidity floor helps** — gross holds while cost falls. That is the answer to
the question as asked: **the lever is dollar volume, not price.** On its own it still does not
clear.

---

## 3. THE THIRD POINT WAS RIGHT, AND IT IS THE BEST RESULT IN THIS LINE

> *"Even if two indicators agree at like p = 0.8 it does not mean that there is not extra
> information in the other indicator."*

**Correct, and this programme has been getting it backwards.** D411 and D413 both treated an
overlapping effect as a **confound to be stripped** — residualise it, standardise it out — and
never asked whether the pair beats either alone. The counterweight from this repo is real (D268:
nine price scores collapse to **2.87** effective independent inputs, RSI at +0.85 to a MACD level),
so it is a hypothesis to measure rather than a principle. **Measured:**

`corr(REV, EFF) = −0.18` — signed trailing 5-day return and 10-bar path efficiency
(`|net| / Σ|steps|`) are **nearly independent**. Path efficiency carries the *shape* of the path,
not its size, which is what makes it a different question rather than a rescaling.

Eight cells, each split at its median. `gap = real − LVL` is **the level's own contribution**:

```
 REV    EFF   LIQ        n    gross      LVL      gap      +-    cost     cov
deep   chop    lo   19,249   +34.81   +38.01    -3.19    5.13    35.9    0.97x
deep   chop    hi   18,630   +33.52   +37.41    -3.89    4.75    22.8    1.47x
deep  clean    lo   26,120   +20.70    +6.99   +13.71    4.18    34.9    0.59x
deep  clean    hi   26,024   +30.26   +15.11   +15.15    3.80    22.9    1.32x
shal   chop    lo   25,699    -1.07   -13.10   +12.03    4.21    31.4   -0.03x
shal   chop    hi   26,445    +0.46    -0.61    +1.07    3.36    21.7    0.02x
shal  clean    lo   18,955    +0.75    -2.25    +3.00    4.62    31.8    0.02x
shal  clean    hi   18,923   -12.85    -5.01    -7.83    4.27    21.0   -0.61x
```

**Path efficiency splits the effect into two different phenomena:**

- **Deep reversal into a CHOPPY path** — the biggest gross (+34.81, +33.52) and **the level
  contributes nothing.** `LVL` matches or beats it (−3.19, −3.89). This is pure short-term
  reversal; the zone is decoration.
- **Deep reversal into a CLEAN path** — the level contributes **+13.71 and +15.15 bp, at 3.3 and
  4.0 SE.** Here the zone is doing real work.

**So the "confound" was never a confound. It is the variable that says which regime you are in** —
and stripping it out, as both prior studies did, averaged the two together and destroyed the
distinction.

**Two cells clear 1.0× coverage on the neutral spread, and both require high liquidity.** That ties
§2 and §3 together: the liquidity floor is **necessary and not sufficient** — it only pays once the
reversal condition selects the population.

---

## 4. What this does NOT establish

- **Eight cells were examined and the best two are being quoted.** That is multiplicity, on data
  already spent, with splits chosen at medians I computed from the same data.
- **Coverage above 1.0× is on the NEUTRAL spread only.** On the event-bar estimate the best cell is
  `1.12×` and the clean-path cell is below 1. The truth is between, and neither figure has an
  execution model behind it — no participation limit, no impact, no borrow for the short side.
- **No out-of-sample test. No time rotation.** And ADDENDUM 1 §4 found the effect concentrated in
  2010–2013, which a pooled table hides.
- The level's contribution in the clean-path cells has **not** been re-tested against an age-matched
  `LVL`, which ADDENDUM 1 §3 showed was worth ~70% of the raw margin.

---

## 5. What would settle it

**This is the first cell in the programme that survives its own matched control, clears a cost
estimate, and has a mechanism that predicts where it should and should not work.** Under R8 the next
act is a **pre-registration with the cells declared in advance and a confirmation on a fixture this
line has never read.**

`data/fixtures/us_shorts_daily_holdout2.csv.gz` is **built and unspent** and is the only clean
confirmation set. **It is not read here and will not be read without the principal's explicit,
specific authorisation.**

**Disposition is the principal's.**

---

**Evidence:** `data/d413_costs2.json`, `data/d413_combine.json`. Runners
`scripts/run_d413_costs2.py`, `scripts/run_d413_combine.py`.
