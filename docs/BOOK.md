# The Book

Strategies that have cleared a pre-registered out-of-sample test. Numbered `S1, S2, …` and
append-only: an entry is amended or retired in writing, never quietly edited.

**A place in the book is not a decision to trade.** It records that a rule was specified in
advance, tested on data it had never seen, and survived — together with everything still wrong
with it. Every entry carries its own falsification conditions.

For the constraints that govern how entries get here, see [`RULES.md`](RULES.md). For the
decisions behind each one, see [`decisions/README.md`](decisions/README.md).

---

## S1 — The Recovery Rule

**Admitted:** 2026-08-27 · **Status:** live in the book, **not promoted to capital**
**Evidence:** [D234](decisions/D234-the-percentage-activation-threshold.md) (discovery) ·
[D237](decisions/D237-the-recovery-rule-on-withheld-data.md) (the out-of-sample test)

### What it does, in one sentence

**Buy an ETF that sits at or below its own volatility channel and has started to climb back out;
sell when it reaches the top of the channel, or when the climb stalls.**

### Specification

Everything below is exact. Nothing is fitted; every constant is either the indicator's published
default or falls out of the construction.

```
For each instrument, on DAILY bars, computed on LOG prices:

    h    = log(high)      l = log(low)       c = log(close)
    hlc3 = (h + l + c) / 3

    hi   = smma(h,    34)        Wilder smoothing, alpha = 1/34
    lo   = smma(l,    34)
    mi   = zlema(hlc3, 34)       zero-lag EMA:  2*EMA1 - EMA2

    md_L = mi - hi    if mi > hi          (above the channel)
           mi - lo    if mi < lo          (below the channel)
           0.0        otherwise           (inside -- a STATED value, not missing)

    hist_L = md_L - sma(md_L, 9)

    position = 1  if  hist_L > 0  AND  md_L <= 0
               0  otherwise
```

| | |
|---|---|
| **book** | long-flat, equal-weighted across the universe |
| **fill** | `lag = 1` — exposure held through bar *t* is decided on *t−1*'s close |
| **warm-up** | **1,000 bars** (~4 years). The Wilder legs at α = 1/34 need 926 alone |
| **costs** | per-symbol IBKR schedule + 1 bp half-spread, ~1.5–1.8 bp/side |
| **returns** | dividend-adjusted; `rf = 4%` charged on the **exposed fraction** |
| **universe** | liquid US ETFs. Tested on two disjoint 57/60-name sets |

**`md_L` is dimensionless** — a log-gap, so `0.01` means *"the midline sits 1% outside the
channel"*, identically on every instrument and at every price level. That property is what makes
the `md_L ≤ 0` condition expressible at all; the published dollar-denominated version cannot
state it.

**Both exits fall out of the level rule and neither was designed.** `md_L > 0` (price recovered
to the channel top) fires on **37.1%** of exits; `hist_L ≤ 0` (the climb stalled) on 62.9%. Mean
holding period **15 bars**, win rate **52.5%**.

### Evidence

| | mined 57 | **T1 — holdout 60** | T3 — forward 57 |
|---|---:|---:|---:|
| span | 2018-12-21 → 2024-12-30 | *same* | 2025-01-02 → 2026-08-26 |
| live bars | 1,515 | 1,515 | 413 |
| **excess Sharpe** | **+0.746** | **+0.779** | +0.898 |
| buy and hold | +0.235 | +0.230 | **+1.234** |
| **delta** | **+0.511** | **+0.549** | **−0.336** |
| CAGR | 5.43% | 5.49% | 3.64% |
| volatility | 6.1% | 5.9% | 3.3% |
| max drawdown | −10.30% | −9.04% | −2.94% |
| exposure | 18.9% | 19.7% | 15.6% |

**What T1 established.** On 60 ETFs sharing **zero tickers** with the training set, the rule
reproduced itself and the effect **grew** rather than shrank — the opposite of the usual
out-of-sample regression. It cleared all three pre-registered hurdles including a matched-count
rotation null.

**Supporting controls.** On mined data, **0 of 1,000 rotations** beat it (100th percentile) —
same exposure, same turnover, same holding periods, wrong bars. And an independent cut, taken for
a different purpose, agrees: bucketing held bars by trailing 63-day return puts the lowest
quintile at **+49.9%** annualised against the highest at **−2.4%**, monotone across five buckets.
Two unrelated measurements both say it earns by buying weakness that has turned.

**Behaviour under stress.** Through the COVID crash leg (2020-02-19 → 2020-03-23) it was **2.0%
exposed and lost 0.73%**, against buy-and-hold's **−33.86%**. `hist_L > 0` requires price to be
*rising* relative to its channel, so a fall that is still accelerating keeps it flat. **It buys
the turn, not the dip** — which is why it does not behave like a mean-reversion strategy in a
crash.

### What is wrong with it — at full strength

1. **Every bootstrap interval contains zero.** T1's delta of +0.549 has a 90% interval of
   **−0.152 to +1.158**. The effect is short of significance by **0.106**, and closing that gap
   needs **~2.6 more years** at the current effect size.
2. **It lost to buy-and-hold over the only forward period ever tested.** T3's delta is −0.336.
   The rule itself did *better* forward (+0.898) — buy-and-hold made **23.72%/yr**, and a book
   15.6% exposed cannot keep pace with a melt-up.
3. **Hurdle E fails everywhere**, including T1: **9 entries per symbol** against 30 required. The
   result rests entirely on pooling across a universe whose members correlate at ~0.4. **This is
   the weakest part of the case.**
4. **The holdout is not independent of the training set.** The two universes correlate at
   **+0.978**. T1 proves the rule is not fitted to particular tickers; it proves nothing about
   independence from the 2018–24 market.
5. **It was found post-hoc.** D234 pre-registered a different hypothesis, every declared cell
   failed, and this rule is the complement — computed on the analyst's initiative, disclosed and
   counted as one look. D237 is its first pre-registration.
6. **18.9% exposure is not a portfolio.** Four fifths of the capital sits in cash.
7. **It is a bet on a regime, and that is now measured.**
   [D239](decisions/D239-time-series-momentum-as-arm-two.md) ran twelve-month time-series
   momentum on the same fixture and found it is not merely skill-free but an **anti-signal** —
   the 0.7th percentile of its own rotation null on Sharpe, the 0.2nd on money. The mechanism
   is that 2018–2024 is dense in sharp **V-shaped** reversals, which whipsaw trend and are
   exactly what S1 buys. **The single feature of this fixture that makes S1 work is the feature
   that makes its opposite fail.** So: *S1's edge is in part a bet that reversals dominate
   continuations, and in a continuation-dominated regime it should weaken.* T3 already agrees —
   it lost to buy-and-hold across the 2025–2026 melt-up, which is a continuation regime.

### Deployment notes

**Levered to buy-and-hold's volatility** (T1 figures, financing charged at `rf`):

| | return | vol | max drawdown |
|---|---:|---:|---:|
| unlevered | 5.49% | 5.9% | −9.04% |
| **at 3.02× (vol-matched)** | **~17.9%** | 17.8% | **~−27.3%** |
| buy and hold | 8.34% | 17.8% | −37.92% |

**Leverage multiplies the drawdown too** — −9.04% becomes roughly −27.3%, and it multiplies an
edge whose interval contains zero. The levered figure is a monotone restatement of the Sharpe
difference, not independent evidence.

### Falsification — what removes S1 from the book

Committed now, so the exit is as pre-specified as the entry:

- **A negative delta over buy-and-hold across a further ≥2 years of forward data**, pooled with
  T3's window.
- **Failure of a matched-count rotation null** on any future fixture.
- **A structural change to the rule.** S1 is this specification exactly. A variant is a new
  entry, tested from scratch — not an amendment to this one.

### What it needs next

**A second, uncorrelated strategy — and the arithmetic is specific.** Required data scales as
`1/delta²`, so two arms at ρ ≈ 0 give **×√2** on the delta and cut the requirement from 8.6 years
to **4.3** — significant on data already in hand, with no waiting.

It also covers S1's one demonstrated weakness: **T3 showed it cannot keep up in a strong bull
market**, which is precisely where a higher-exposure arm would earn.

**Amendment, 2026-08-27 ([D238](decisions/D238-the-short-side-mirror.md)).** The obvious
candidate — the short-side mirror of this rule — was tested and **closed**. It is recorded here
because it sharpens the target rather than merely removing an option: the mirror **supplies the
correlation and not the return.** `corr(S1, M1) = −0.0687` is exactly the ρ ≈ 0 the arithmetic
above needs, at an excess Sharpe of **−0.407**; the combined book scores **−0.484 against S1
alone**, with the entire 90% interval below zero. Since adding an arm helps only when
`SR_B > ρ·SR_A = −0.051`, **the bar for arm two is about −0.05 excess Sharpe at ρ ≈ 0 —
uncorrelatedness was never the binding constraint.**

*S1's specification and evidence are unchanged by this. Nothing above this line moved.*

**Amendment, 2026-08-28 ([D239](decisions/D239-time-series-momentum-as-arm-two.md)).** Trend
following was tested as arm two and **closed** — it fails every hurdle and is an anti-signal.
The finding that matters is not about trend: **arm two must not be another bet on
reversals-beating-continuations**, because S1 already is one. That is a constraint on the search
no earlier study could have stated, and it is recorded as weakness 7 above.

> **The book has one entry at 18.9% exposure. That is a start, not a book.**

---

### AMENDMENT, 2026-08-28 — S1 failed the first time-independent test

*Committed in advance by [D243](decisions/D243-the-book-on-extended-history.md)'s stop. S1 is
amended, not dropped and not re-cut.*

**The fixture was extended from 6.0 to 12.8 live years, back to 2013-11.** The stretch
**2013-11 → 2018-12 had never been seen** — and every previous holdout was an *instrument*
holdout at ρ = +0.978 between universes, so **this is the first data that was new in time.**

| S1 on the never-seen window | |
|---|---:|
| excess Sharpe | **−0.123** |
| buy-and-hold over the same bars | −0.149 |
| delta | +0.025 |
| **floor it had to clear** | **+0.128** |
| rotation null percentile | **80.6th** |

**S1's excess Sharpe was negative, it beat buy-and-hold by a fifth of its floor, and it failed
its rotation null for the first time ever** — having sat at the 100th percentile on both prior
fixtures.

**The headline number is restated.** `+0.746` was measured over 6.0 years; over 12.8 it is
**+0.478**, with a 90% interval of **−0.036 to +0.917** that still contains zero. The old number
was never wrong — it was measured on a window that suited the rule.

**This is weakness 7 realised, not a new one.** D239 predicted it: *"S1's edge is in part a bet
that reversals dominate continuations, and in a continuation-dominated regime it should weaken."*
2013–2018 was that regime. **The prediction was registered before the data existed.**

**Why S1 stays in the book.** It cleared a pre-registered instrument holdout (D237), its
rotation null on two fixtures, and it remains **structurally uncorrelated with S2 at ρ = +0.123
measured across all 12.8 years.** What it is *not* is a rule that works in every era, and the
book now says so.

**Falsification unchanged**, and one condition is now partially met: a negative delta over
buy-and-hold across a further ≥2 years. NEW is 5.1 years and the delta was positive by +0.025,
so the condition has not fired — but it came close, and a repeat retires S1.

---

### AMENDMENT, 2026-08-28 — S1 also failed on crypto, at the 29.1st percentile

[D244](decisions/D244-the-book-on-crypto.md) ran the frozen book on **35 coins over 5.2 years**
at 10 bp/side. The test was pointed: D239 and D243 established S1 is a bet that reversals beat
continuations, **so the most reversal-heavy asset class available is where it should have
worked.**

| S1 on crypto | |
|---|---:|
| excess Sharpe | **−0.291** |
| equal-weighted buy-and-hold | −0.105 |
| delta | −0.187 |
| max drawdown | −48.90% |
| **rotation null percentile** | **29.1st** |
| breakeven cost | **−50.6 bp** |

**It was not the costs.** A breakeven of −50.6 bp means S1 loses with *free trading*. **It was
not the benchmark** — it underperformed an alt basket that itself lost 4.18%/yr and drew down
90.9%. **The rotation null is the finding: at the 29.1st percentile S1's timing was worse than
random** at the same exposure, turnover and holding periods. It sat at the 100th on both ETF
fixtures.

**Two declared confounds are real.** 252 bars is one year on ETFs and **0.69 years** on a
365-day calendar, so this is the same estimator and not the same economic rule; and the 2.74-year
warm-up pushed the live window to 2020-10, missing the 2018–20 crypto bear. **Neither excuses the
null** — a units mismatch would make a rule weaker, not worse than random.

**S1's evidence base, stated plainly:**

| | result |
|---|---|
| Instrument holdout, US equity ETFs (D237) | **passed**, and the effect grew |
| Time holdout, 2013–2018 ETFs (D243) | **failed** — negative, 80.6th percentile |
| Asset-class holdout, crypto (D244) | **failed** — negative, 29.1st percentile |

**It works on US equity ETFs over 2018–2024 and has not been shown to work anywhere else.** It
stays in the book because it cleared a pre-registered holdout and because it contributes +0.109
to the pair over 12.8 years — but **it should not be traded standalone, and the case that it
generalises is now weak.**

---

### CORRECTION to the amendment above, 2026-08-28 — the crypto result is INCONCLUSIVE, not a failure

*Appended rather than edited. The table above is left as written and this replaces its third row.*

**The line "neither excuses the null — a units mismatch would make a rule weaker, not worse than
random" is WRONG.** It addressed the calendar confound and missed a second one that does explain
a below-null result without saying anything about the signal.

**Crypto has the opposite conditional-return structure to equities.** Forward return by trailing
63-bar return quintile, Q1 being the most beaten down:

| quintile | **ETFs, 12.8y** | **crypto, 5.2y** |
|---|---:|---:|
| **Q1 — most beaten down** | **+16.83%** | **−41.65%** |
| Q2 | +7.48% | −8.75% |
| Q3 | +5.16% | −1.05% |
| Q4 | +5.02% | +71.18% |
| Q5 | +5.31% | −11.43% |

**In equities, buying weakness is the best thing available. In crypto it is the worst, by 58
points.** 19 of the 35 coins had negative CAGR, median −9.1%.

S1's whole mechanism is buying weakness that has turned, so **it concentrates exposure in exactly
the bars crypto punishes.** A rotation null spreads the same exposure across all five quintiles.
**S1 therefore lands below its null by construction given the drift structure — no timing failure
is required to produce the 29.1st percentile.**

This is the mirror of [D238](decisions/D238-the-short-side-mirror.md), which established that a
*short* fails on positively-drifting ETFs. The symmetric statement — a *dip-buyer* fails on
negatively-drifting assets — is the same structural fact from the other side, and it should have
been seen before the crypto result was weighed.

**Corrected reading of row three: INCONCLUSIVE.** The test measured whether crypto mean-reverts,
not whether S1's signal works. What it legitimately bounds is narrower: **S1 requires an asset
class that mean-reverts.**

**None of this rescues S1, and the verdict is unchanged.** The case against it never rested on
crypto:

```
out-of-training ETFs -- 6.8 years, same asset class, same rule, same units
  S1                   +0.106
  buy and hold         +0.243        delta  -0.137
  what S1 adds to S2   -0.155
```

**One fact does cut in S1's favour and is recorded for completeness.** The Q1 premium of
**+16.83%** spans the full 12.8 ETF years *including 2013–2018*, the era S1 lost money in. **The
effect S1 targets was present when S1 failed to capture it** — which points at this particular
implementation rather than at the thesis. That is not a licence to re-cut the rule; doing so
would be the fourth time a result in this programme lived in the complement of what was
registered, which is an open methodological item in `AITODO.md`.

---

### AMENDMENT, 2026-08-28 — S1 cleared a second instrument holdout, on 385 unseen names

[D245](decisions/D245-the-wide-universe.md) rebuilt the universe from the cache — 1,276 symbols
were available and the book had used 117 — and ran the frozen book on two liquidity cells over
the identical span as D243.

| | never-seen instruments | S1 | B&H | delta | floor | rotation null |
|---|---:|---:|---:|---:|---:|---:|
| W5, 244 symbols | **152** | +0.468 | +0.365 | +0.103 | +0.059 | **99.8th** ✓ |
| W1, 486 symbols | **385** | +0.493 | +0.319 | +0.174 | +0.059 | **100.0th** ✓ |

**S1's diagnosis is now precise. It is INSTRUMENT-GENERAL and ERA-SPECIFIC.**

| test | result |
|---|---|
| Instrument holdout, 60 tickers (D237) | **passed**, effect grew |
| **Instrument holdout, 385 tickers (D245)** | **passed**, 100th percentile |
| Time holdout, 2013–2018 (D243) | **failed** — negative, 80.6th percentile |
| Asset class, crypto (D244) | **inconclusive** — opposite drift structure |

**Two instrument holdouts passed, one era holdout failed.** That is not a broken rule; it is a
rule with a regime dependency, and D239 predicted it from a mechanism before D243 measured it.
**Its own interval still contains zero at every universe size** (p05 −0.036, −0.053, −0.050),
and it should still not be traded standalone.

---

## S2 — The Uptrend Onset

**Admitted:** 2026-08-28 · **Status:** live in the book, **not promoted to capital**
**Evidence:** [D240](decisions/D240-the-uptrend-onset-arm.md) (discovery) ·
[D242](decisions/D242-the-uptrend-arm-on-withheld-data.md) (the out-of-sample test)

### What it does, in one sentence

**Buy an ETF on the first day it enters a confirmed structural uptrend — rising swing lows *and*
rising swing highs over the past year — and hold it for one quarter or until the trend breaks.**

### Specification

```
For each instrument, on DAILY bars, in LOG space:

    lows  = confirmed swing lows  in the trailing 252 bars   (k = 3)
    highs = confirmed swing highs in the trailing 252 bars

    g_lo  = OLS slope of log(price) on bar index, over lows
    g_hi  = OLS slope of log(price) on bar index, over highs

    UPTREND := g_lo > 0 AND g_hi > 0

    ENTRY   the FIRST bar of an UPTREND episode  (onset only; no re-entry within one)
    EXIT    the earlier of  age >= 63 bars  |  the state ends
```

| | |
|---|---|
| **book** | long-flat, equal-weighted across the universe |
| **fill** | `lag = 1` |
| **warm-up** | 1,000 bars, shared with S1 so both are scored on identical bars |
| **costs / returns** | unchanged from S1 — per-symbol IBKR schedule, dividend-adjusted, `rf` on the exposed fraction |
| **exposure** | 13.9% |

**Every constant is either fixed by prior decision or canonical.** `k ∈ {2,3}` was fixed by
D173; 252 bars is one year; 63 bars is one quarter. **The regression answers D173's standing
objection to trend lines rather than evading it** — OLS over *all* confirmed pivots in the window
chooses no points, refits every bar, and includes the disagreeing third, which are precisely the
free parameters D173 named.

### Evidence

| | mined 57 | **holdout 60** |
|---|---:|---:|
| **excess Sharpe** | +0.610 | **+0.672** |
| buy and hold | +0.235 | +0.230 |
| **delta** | +0.375 | **+0.442** |
| rotation null percentile | 97.3rd | **99.7th** |
| *money* leg of that null | 99.2nd | **99.9th** |
| max drawdown | −5.78% | **−4.40%** |
| exposure | 14.2% | 13.9% |

**The effect grew out of sample**, +0.610 → +0.672, on 60 ETFs sharing zero tickers with the
training set. That is the second rule here to do so, after S1.

**ρ with S1 is +0.175 on the holdout, against +0.159 mined.** The two rules avoid each other by
construction — an ETF at or below its volatility channel is rarely in a confirmed year-long
uptrend — and only **8.9%** of S2's positions are also S1's, *less than half* what chance would
give. **The diversification is structural and it travelled.**

### What is wrong with it — at full strength

1. **Hurdle E fails worse than anything else in this book: 2 entries per symbol** against 30,
   from 217 entries across 60 ETFs.
2. **Instrument holdout, not time holdout.** The two universes correlate **+0.978**.
3. **The design was fitted on the mined fixture** — the 63-bar cap came from a measured decay
   table, the long-only decision from measured downtrend returns.
4. **Modest money: 5.89% deployable against buy-and-hold's 8.34%.** It earns its place as a
   diversifier, not a return engine.
5. **The −8% stop is NOT part of this entry.** It was tested and **failed** its matched-exit-count
   overlay null out of sample (99.6th percentile mined → **71.7th** on the holdout). It lowers
   drawdown to −2.71% *mechanically*, by holding less, and adds no demonstrated timing
   information. **A variant with the stop is a separate entry and is not in this book.**

### AMENDMENT, 2026-08-28 — S2 cleared a time holdout, which nothing else here has

[D243](decisions/D243-the-book-on-extended-history.md) ran the frozen book on 12.8 live years,
of which **2013-11 → 2018-12 had never been seen.**

| S2 on the never-seen window | |
|---|---:|
| excess Sharpe | **+0.248** |
| buy-and-hold over the same bars | −0.149 |
| **delta** | **+0.396** |
| floor it had to clear | +0.094 |
| rotation null percentile | **97.1st** |

**Four times its floor, and it cleared its rotation null** — in an era where buy-and-hold itself
scored −0.149, dragged by the commodity and emerging-market collapse. It also posted **+1.504**
over 2025–2026 against buy-and-hold's +1.235, the window where S1 loses.

**S2 has now cleared a pre-registered instrument holdout (D242) and a pre-registered time
holdout (D243). No other rule in this programme has done both.**

**Over the full 12.8 years its own interval excludes zero** — `+0.511`, p05 **+0.066** — the
first time any entry here has managed that. Its advantage over buy-and-hold does not (p05
−0.134).

**And the pairing has a mechanism now, not just a correlation.** D239 established that S1 bets
on reversals beating continuations; S2 is the continuation arm. **Each covers the other's bad
era** — S1 went negative over 2013–2018 while S2 beat the market by four times its floor. ρ has
been +0.159, +0.175 and +0.123 on three separate spans. **That is a better reason to hold both
than the correlation ever was.**

*Weakness 1 above is partly relieved: entries per symbol are unchanged for S2 at 5, but the
combined book now reaches 24 against the 30 required, from 9 on the original fixture.*

### AMENDMENT, 2026-08-28 — S2's generality is bounded to equities

[D244](decisions/D244-the-book-on-crypto.md) ran S2 on 35 coins over 5.2 years.

| S2 on crypto | |
|---|---:|
| excess Sharpe | +0.052 |
| equal-weighted buy-and-hold | −0.105 |
| delta | **+0.156** |
| rotation null percentile | **73.2nd** |
| breakeven cost | 63 bp — **6.3× what was charged** |

**S2 beat the benchmark and showed no demonstrated skill.** It cleared X1 and failed X2: its
result is not distinguishable from trading the same amount at random times. **It was not harmful,
and costs did not hide anything** — the breakeven is 6.3× the fee charged.

**So S2's generality is bounded.** It has passed an instrument holdout and a time holdout **on US
equity ETFs**, and has not been shown to work outside them. The same declared confounds apply:
252 bars is 0.69 years on a 365-day calendar, so this was the same estimator rather than the same
economic rule.

**Note added 2026-08-28, and it cuts against S2 rather than for it.** The correction to S1's
crypto amendment above shows crypto's conditional-return structure is *hostile* to a dip-buyer —
Q1 at −41.65% — which excuses S1's result there. **It is not hostile to a continuation rule in
the same way**: the second-highest trailing-return quintile returned **+71.18%**. So the
structure was not stacked against S2, and S2 still failed its rotation null at the 73.2nd
percentile.

**That makes S2's crypto non-result somewhat more informative than S1's**, though not decisive —
the crypto quintile profile is **non-monotone** (Q5 at −11.43%), so "crypto rewards trend" is not
a clean claim either. The honest reading stays: **no demonstrated skill outside US equity ETFs**,
with a slightly firmer basis than for S1.

### Falsification — what removes S2

- **A negative delta over buy-and-hold across ≥2 years of forward data.**
- **Failure of a matched-count rotation null** on any future fixture.
- **A structural change to the rule.** S2 is this specification exactly. Adding the stop, moving
  the age cap, or changing `k` makes a new entry tested from scratch.

---

## How the book behaves when the market falls

*Added 2026-08-28. Measured across the 12.8-year extended fixture, pooling every bar on which
the equal-weighted 57 was in a drawdown worse than 10% — **1,375 bars, 42.7% of the sample.***

| | **in market drawdowns** | in everything else |
|---|---:|---:|
| Buy and hold | **−43.57%** | **+365.31%** |
| **S1** | **+10.03%** | +34.48% |
| S2 | −5.52% | +33.81% |
| **Combined** | **+4.09%** | +75.69% |

**The book earns in falling markets.** The combined book made **+4.09%** across bars where the
market lost **43.57%**. Through COVID (2020-01-17 → 2020-07-13) S1 alone made **+16.98%** against
buy-and-hold's −11.11%, having bought the March bottom.

**The weakness is the other side.** The book captures **+75.69%** of a **+365.31%** up-move —
roughly a fifth. **Up-capture, not downside, is what is broken here**, and any addition to the
book should be judged against that.

### This is what S1 is for, and it reframes its standalone numbers

**S1 is the crash-alpha arm: +10.03% in drawdowns against S2's −5.52%.** And it holds outside its
training window — through the 2014-09 → 2016-06 decline, entirely inside the never-seen period,
S1 made **+1.10%** while the market lost 10.90%.

**S1's poor out-of-training Sharpe and its crash performance are the same fact seen twice.** It
earns in falling markets and does little in rising ones; 2013–2018 was mostly rising. **An
all-weather Sharpe is the wrong instrument for measuring an arm with that job**, in the same way
D236 found Sharpe could not see drawdown.

**This supersedes the reading in the amendments above that S1 might be retired.** It stays, and
it is judged on crash contribution — which is measurable, out-of-training, and which it passes.

---

## Standing conditions on every entry

1. **Admission requires a pre-registered out-of-sample test** with hurdles committed before the
   withheld data is touched (D215).
2. **Every entry states its falsification conditions on admission**, not afterwards.
3. **An entry is never silently edited.** Amend or retire in writing, with the reason.
4. **A place in the book is not a decision to trade.** Sizing, leverage and capital allocation are
   separate decisions and are recorded separately.

---

## A book-level finding: adding instruments is closed as a route to significance

*[D245](decisions/D245-the-wide-universe.md), 2026-08-28. Recorded here because it constrains
every future entry, not just these two.*

The book's intervals have always been wide, and the reason was assumed to be too few
instruments. **Measured, it is not.**

| universe | symbols | **effective independent instruments** |
|---|---:|---:|
| the 57 | 57 | **2.23** |
| W5 | 244 | **2.02** |
| W1 | 486 | **2.08** |

**Going from 57 to 486 ETFs LOWERED effective breadth.** The 57 were unusually diverse — bonds,
metals, commodities and fourteen country funds. The broad universe above $5M/day is dominated by
US equity sector and style products that move together, so **429 extra names added correlation
rather than independence.**

S2's lower bound did roughly double, +0.066 to +0.126, which is real and far smaller than
eightfold more instruments would suggest — because **breadth, not headcount, sets it.**

> **At ρ ≈ 0.4 across US equity ETFs, breadth saturates near 2 and no amount of headcount fixes
> it. The remaining routes to significance are more TIME, or genuinely uncorrelated RETURN
> DRIVERS.**

*I recommended the expansion partly as a breadth fix. That premise was wrong and is recorded as
such. It was worth doing as an instrument holdout, which is what it delivered.*
