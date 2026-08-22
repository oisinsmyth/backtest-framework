# D187 — Two fixtures, two volume conventions, one field: the impact model was scaled by √price

**Status:** Committed
**Date:** 2026-08-22
**Category:** Data layer
**Source:** Found while setting up the ETF cross-section, one day after D186 published a capacity number computed with it

## What was wrong

`SqrtImpact` divides an order **quantity** by ADV:

```
impact_fraction = coefficient × σ_daily × √(|Q| / ADV)
```

`calibrate_impact_params` filled `ImpactParams.adv_shares` with `mean(volume)` and never
asked what the volume column counted. **The two fixtures in this repo count different
things:**

| Fixture | Column | Sanity check |
|---|---|---|
| `universe_daily_2015_2024` (ETFs) | **shares** | SPY prints 68.1M; × $474 ≈ $32bn/day, correct |
| `crypto_universe_2015_2025` | **quote-currency notional** | BTC prints 47.5bn — it cannot be coins, only 21M will ever exist |

The crypto policy's own docstring says so plainly — *"the provider reports volume in the
quote currency, i.e. USD notional"* — and the calibration below it did not read it.

So for every crypto run the ratio was `Q_units / ADV_usd`: dimensionally wrong, and off by
a factor of the price.

| | ADV used | ADV correct | Ratio | Effect on the impact charge |
|---|---|---|---|---|
| `BTC-USD` | 22.2bn | 1.01M coins | 21,970× too large | **understated ~148×** |
| `ETH-USD` | 14.9bn | 17.4M | 855× too large | understated ~29× |
| `LUNC-USD` | 353M | 559bn | 1,585× too **small** | **overstated ~40×** |

An instrument priced above $1 had its impact understated by √P; one priced below $1 had it
overstated by √(1/P). **The same run was wrong in both directions at once**, which is why it
produced two results that looked like findings and were artifacts:

- **BTC appeared almost immune to impact.** It was not; its impact was divided by 148.
- **`LUNC-USD`'s account was destroyed by impact at $30M.** It was not; its impact was
  multiplied by 40. With the units right, **no book is destroyed at any size tested.**

## The fix

`calibrate_impact_params` takes an explicit `volume_units`, one of `("shares",
"quote_notional")`, and **raises on anything else**. There is no safe default to guess with:
guessing wrong scales every charge by √price. `"shares"` remains the default because it is
the equity convention every caller before this assumed, which keeps the pairs study's
published trials untouched.

For `quote_notional`, conversion is **bar by bar** — `Σ(volume_t / close_t) / n` — not
mean-notional over mean-price. On a series whose price moves by orders of magnitude, and
every coin here does, those are different statistics and only the first is ADV.

`CostTier` carries `volume_units`, emitted from `config()` only alongside the impact brick,
so no tier without impact changes its hash. Both study summaries remain byte-identical.

## A second bug, found only because the fix required an assertion

Converting notional to units needs volumes aligned bar-for-bar with prices, so the fix added
a length check. It failed immediately on `ADA-USD`: **2,974 volumes against 2,709 bars.**

All three benchmark runners — `run_benchmark`, `run_benchmark_via_engine`,
`run_constant_fraction_benchmark` — had been handed a **sliced** bar series
(`bars[oos_start:oos_end]`) alongside a **full-length** volume series. Introduced the day
before, in D186, when volumes were first threaded to them.

Without the assertion this would never have raised. ADV would simply have been calibrated
over a longer window than the bars it priced — quietly, on every benchmark, in the direction
of understating impact. **The alignment guard was written for a units conversion and caught
a slicing bug**, which is the argument for putting assertions where the invariant is, not
where the suspicion is.

## The corrected result

D186's sweep, rerun. Its RESULT section is left as written and a CORRECTION is appended
there.

| Total AUM | Edge as published | Edge corrected | |
|---|---|---|---|
| $0.1M | +0.067 | **+0.075** | |
| $1M | +0.051 | **+0.068** | |
| $10M | +0.014 | **+0.047** | |
| $30M | −0.000 | **+0.026** | |
| $100M | −0.026 | **−0.014** | |

**Capacity moves from ~$30M to ~$66M**, and no book is destroyed at any level.

**I predicted the correction would move capacity DOWN and it moved up.** The reasoning was
that BTC and ETH would see impact rise 148× and 29×, and they carry weight in the book. What
that missed is arithmetic about the cross-section: BTC and ETH are **2 of 62** in an
equal-weight portfolio, while the majority of the universe trades **below $1** — and every
one of those had its impact *overstated*. The many small corrections downward outweighed the
two large corrections upward.

The general form is the same error as D185's: **a correct mechanism applied to the wrong
population.** There I reasoned about turnover and forgot the volatility denominator; here I
reasoned about the two coins I had checked and forgot the sixty I had not.

## Consequences

- **D186's capacity number is corrected from ~$30M to ~$66M**, and its "two books destroyed
  by impact" finding is **withdrawn** — that was the units bug, not a capacity limit.
- **The pairs study is unaffected.** It passes equity share volume and the default is
  `"shares"`.
- Two tests pin this: one asserts the conversion arithmetic exactly (1,000 notional at
  alternating 100/200 gives ADV 1,000 as shares and 7.5 as units), one asserts an unknown
  unit raises rather than defaulting.

## The lesson worth keeping

**A units error is invisible to every check this project runs.** The DSR, the trial
registry, the walk-forward, the look-ahead guard, the golden masters, the property tests —
none of them can see that a number is the right magnitude in the wrong unit. It survived
because `adv_shares` was populated by a function that never asked what it was being handed,
and the field name was the only place the assumption was written down.

**The name of a field is not a contract.** The parameter that enforces it is.
