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

> **The book has one entry at 18.9% exposure. That is a start, not a book.**

---

## Standing conditions on every entry

1. **Admission requires a pre-registered out-of-sample test** with hurdles committed before the
   withheld data is touched (D215).
2. **Every entry states its falsification conditions on admission**, not afterwards.
3. **An entry is never silently edited.** Amend or retire in writing, with the reason.
4. **A place in the book is not a decision to trade.** Sizing, leverage and capital allocation are
   separate decisions and are recorded separately.
