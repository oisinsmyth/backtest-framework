# D233 — The strategy, and every way I can think of to improve it

**Status:** Reference — a characterisation and a candidate register. **No looks spent, no verdict.**
**Date:** 2026-08-27
**Area:** Strategy research

---

## Part 1 — What the strategy is

**Impulse MACD (LazyBear), `length = 34`, `signal = 9`, rung I1, long-flat, no gate, `lag = 1`,
daily bars, 57 ETFs, equal-weighted.**

```
hlc3 = (H + L + C) / 3
hi   = smma(H, 34)      lo = smma(L, 34)      mi = zlema(hlc3, 34)
md   = mi - hi   if mi > hi
       mi - lo   if mi < lo
       0.0       otherwise                     <- the dead zone, a STATED value
hist = md - sma(md, 9)

position = 1 if hist > 0 else 0                <- held through the next bar
```

Warm-up **1,000 bars** (~4 years; the Wilder legs at α = 1/34 need 926 alone). Live span
**2018-12-21 → 2024-12-30**, 1,515 bars, 6.01 years. Costs ~1.5–1.8 bp/side.

### What it did

| | excess Sharpe @rf=4% | Sharpe (div, rf=0) | CAGR | vol | max DD | exposure |
|---|---:|---:|---:|---:|---:|---:|
| **the arm** | **+0.570** | +0.793 | 7.23% | **8.8%** | **−12.70%** | 49.9% |
| buy and hold | +0.235 | +0.457 | 8.42% | 17.7% | −34.81% | 100% |

**86% of the market's return at half its volatility and a third of its drawdown.**

**And the honest qualifier:** the advantage of **+0.335** has a 90% interval of **−0.242 to
+0.804** (D230 addendum). It contains zero. The point estimate is the best estimate; it is not
established that it generalises.

---

## Part 2 — What the signal actually is

Four properties, all derived rather than fitted, and each one closes off a class of ideas.

**1. It carries exactly one bit: its sign.**

| region | what we measured | where |
|---|---|---|
| `hist > 0` (held) | **+15.6%/yr** | — |
| `hist < 0` (flat) | **+1.7%/yr** | — |
| raising the bar within the positive half | no reliable gradient; best selection +12%, declining as you tighten | D228, D231 |
| lowering the bar into the negative half | no gradient, and the **marginal bars are the worst** (+1.1% nearest zero vs +2.1% most negative) | measured here |

**The threshold does real work. The distance from it does not.** That single fact explains nine
consecutive filter failures as one finding rather than nine disappointments.

**2. Exposure is ~50% and cannot be changed by any parameter.** `hist = md − sma(md, 9)` has a
kernel summing to zero, so its sign is positive about half the time whatever the market does.
Measured at 49.9% (k=1), 50.9% (k=2), 48.5% (jerk rung), 49.7% (15m k=4).

**3. It sees only ~9 bars of `md`.** `hist` is a slope estimator over the signal window.
Anything hoped to matter must move `md` inside that window — which is why the dollar-scale
defect proved immaterial despite being provable (D232).

**4. It is a chop detector, not a trend detector.** Gain of `x − sma(x,9)`: 1.190 at 13 bars
(peak), 0.410 at 60, **0.100 at 252**. A year-long trend is attenuated by 90%.

### Nine studies, one mechanism

| | tried | outcome |
|---|---|---|
| D220 | volume filter | failed |
| D223/224 | volume regime gate | cleared on crypto, failed the floor |
| D225 | the gate at 1h | replicated, window one point wide |
| D226 | the gate on 57 ETFs at 15m | **the spike moved** — fitted, not discovered |
| D228 | 8 candidates (gates, sizers, bond overlay) | **0 of 8**; measured `r = +0.823` between exposure Δ and money Δ |
| D229 | the jerk rung | −0.218 |
| D230 | bootstrap sweep of every reported delta | **0 of 24** clear as claimed |
| D231 | the exposure dial, 2 families × 4 levels | **0 of 8** beat the parent |
| D232 | fixing the signal's scale defect | 98.85% identical calls; immaterial |

> **Every one was trying to extract a second bit from a one-bit signal.**

---

## Part 3 — Every way I can think of to improve it

Ranked by expected value. Each carries what we already know, my prediction, and the cost.

### Tier 1 — highest expected value

**1. Leverage to matched volatility.**
Not a new signal — a deployment choice, and the one the low volatility exists to enable. At
~2× with financing charged at `rf`: roughly **14.0%/yr at 17.6% vol** against buy-and-hold's
8.4% at 17.7%. Sharpe is unchanged by leverage; what changes is that the ratio becomes money.
*Prediction: works, by arithmetic — it is the same result restated.* *Risk: it multiplies the
drawdown too (−12.7% → ~−25%), and it multiplies an edge whose interval contains zero.*
**Cost: no new looks. It is a decision, not a study.**

**2. A second uncorrelated signal — the layering plan.**
The original intent of this programme, never executed. Two arms at 50% exposure with ρ ≈ 0 give
**full deployment and a higher Sharpe than either alone** — √2 × better at ρ = 0. This is the
only route that raises the book's Sharpe without fighting the √f law, because it adds
information rather than rearranging it.
*Prediction: the mechanism is certain; whether a genuinely uncorrelated second signal exists is
the open question, and this programme has not found one yet.*
**Cost: a full study per candidate signal.**

**3. Book-level volatility targeting.**
Scale *total* book exposure to hit a constant volatility, rather than sizing per symbol.
Different from D228's S1 (which changed exposure and was scored as a filter). Volatility
clustering is among the most robust facts in finance, and constant-vol targeting typically adds
**0.05–0.15 Sharpe** in published work.
*Prediction: modest positive, ~+0.05–0.10. It does not change which bars you hold, only the
size, so the √f law does not apply.* **Cost: one small study.**

### Tier 2 — structurally different, genuinely untested

**4. Cross-sectional long-short.**
Long the strongest-ranked, short the weakest, market-neutral. **Always fully deployed, so it
escapes the √f penalty entirely** — a different risk rather than less of the same one. D218's
`long_short` book is *not* this: it goes long/short per symbol on the same signal, which is a
directional bet.
*Prediction: uncertain, and the most interesting unknown on this list. It removes the market
factor, which is where most of the arm's return comes from — so it could be much better or much
worse.* **Cost: one study.**

**5. Risk-parity weighting across the 57.**
The book is equal-weighted, so a 40%-vol energy fund and a 5%-vol bond fund contribute wildly
different risk. Weight by inverse volatility **at constant total exposure** — changing what risk
is taken, not how much.
*Prediction: small positive. This is the one Tier-2 item with a clear mechanism.*
**Cost: one small study.**

**6. Test the unfiltered arm on the holdout.**
Not an improvement — a validation, and the only thing that can move the ±0.5 interval. 60 ETFs
selected by a rule fixed in advance, built and reserved.
*Prediction: the honest one is that it comes back inside the noise, because the effect being
tested is small and the fixture is one span.* **Cost: spends the holdout, once.**

### Tier 3 — worth listing, low expectation

**7. A faster smoother.** The Wilder legs need **926 bars** of burn-in for the seed to stop
mattering — an absurd warm-up that costs four years of every fixture. An EMA or a shorter Wilder
would shorten it and shift the frequency response.
*Prediction: changes the warm-up more than the result.* **Cost: small.**

**8. Conjoining the rungs.** `hist` gives one bit; `md` (the level rung, I2) gives another.
Requiring both — or voting — is a 2-bit rule, and the conjunction has never been tested. D218
measured them separately and as deltas, never together.
*Prediction: weak. I2 alone scored +0.129, so the second bit is a poor one.* **Cost: small.**

**9. The signal window.** The operator sees only ~9 bars of `md`. A longer `signal` sees more
and attenuates less at low frequency. D218 swept `lengthMA ∈ {21, 34, 55}` and found a monotone
decline with 34 in the middle — but that was `length`, not `signal`.
*Prediction: low. Three points on the neighbouring axis showed nothing.* **Cost: small, but it
is a sweep and sweeps cost multiplicity.**

**10. Cost reduction.** Turnover is 4,835 units over 6 years across 57 names — roughly **23
bp/yr** of drag. Halving it via patient execution gains ~12 bp/yr ≈ **0.013 Sharpe**.
*Prediction: real but negligible.* **Cost: small.**

### Closed — do not reopen without a written override

| | why |
|---|---|
| **Filtering on signal strength** | Nine studies. `hist` has one bit; there is nothing left to filter on. D228's stop stands |
| **Stop-losses / cut-losers** | Measured today: loses money at **every** level (−2.95 at 1%, −1.87 at 2%, −1.47 at 3%). Trades that dip disproportionately recover. D224 found the same independently |
| **Volume in any form** | Failed on four fixtures (D220, D224, D225, D226). D220's stop stands |
| **Widening the entry band** | The marginal flat bars are the **worst** flat bars |
| **Scale-correcting the indicator** | 98.85% identical calls (D232). Keep `I1L` for correctness on high-drift instruments; expect nothing from it here |

---

## What I would do, in order

**1, then 3, then 6.** Leverage is a decision that needs no study. Vol targeting is the
highest-confidence small win. The holdout is what tells us whether any of it is real — and it
should be spent on the **simplest** version of the arm, not a decorated one, because a holdout
answers one question well and several questions badly.

**2 is the biggest prize and the largest project.** It is also what this programme set out to do
in the first place.

---

## What this record is not

**No looks are spent here.** Nothing above evaluates a new configuration; Part 1 and Part 2
restate measurements already in the ledger, and Part 3 is a list of hypotheses with predictions
attached so that each can be scored honestly when it is run.

**The predictions are committed now**, before any of them is tested, so that a candidate which
works cannot later be described as expected, and one which fails cannot be described as
obviously doomed.
