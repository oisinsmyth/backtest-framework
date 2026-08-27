# D228 — Mining the mined fixture: a filter search with a *measured* selection bias

**Status:** Pre-registered — committed BEFORE any runner exists
**Date:** 2026-08-27
**Area:** Validation & research integrity

---

## The question

D218's acceleration arm is the only thing in this programme that survives contact with a
risk-free rate. Six studies have tried to improve it with a filter and all six failed the
same way. The question here is whether a seventh attempt can be made **on data that has
already been mined** without the search inventing its own answer.

The honest framing is not *"may we search?"* — D215 already committed the rule that a
positive *"would need its own pre-registration and holdout"*, which is permission to search
conditioned on what happens next. The framing is:

> **Searching is not the sin. Counting the search as the test is.**

So this study does two things: it declares a candidate set in advance, and it **measures the
selection bias of its own search** rather than bounding it with an analytic floor that
nothing can clear.

---

## Part 1 — The strategy, restated in full

Read from the code, not from memory. Every claim below cites where it lives.

### The arm

**`I1_signal` / `long_flat` / `gate = none`**, `lag = 1`, on the daily ETF fixture.

| element | value | source |
|---|---|---|
| indicator | Impulse MACD (LazyBear) | `research/macd.py::impulse_macd_series` |
| `length` | **34** | `macd.IMPULSE_LENGTH` |
| `signal` | **9** | `macd.IMPULSE_SIGNAL` |
| rung | **I1** — `sh = md - sma(md, 9)`, trend **acceleration** | `macd.impulse_signal_score` |
| book | **long-flat** — `1{score > 0}`, ties flat | `macd.positions` |
| confluence gate | **none** (the 200-MA gate was tested and is much worse: +0.291 vs +0.658) | `run_impulse_macd.py` |
| fill | `lag = 1` — exposure through bar *t* decided on *t-1* | `run_macd_ladder.arm_positions` |
| warm-up | **1,000 bars** (~4 years) — the Wilder legs dominate; alpha = 1/34 needs 926 bars | `macd.impulse_warm_up_bars` |

The construction, in full:

1. `hlc3 = (high + low + close) / 3`
2. `hi = smma(high, 34)`, `lo = smma(low, 34)`, `mi = zlema(hlc3, 34)` — Wilder smoothing
   (alpha = 1/n) for the bands, zero-lag EMA (`2*EMA1 - EMA2`) for the midline
3. `md = mi - hi` if `mi > hi`; `mi - lo` if `mi < lo`; else **exactly `0.0`** — the dead zone
   is a *stated value*, not a missing one
4. `sig = sma(md, 9)`, `hist = md - sig`
5. **Position = 1 when `hist > 0`, else 0.** Held through the next bar.

The rule is written as a level rule rather than an event rule deliberately: *"long on a cross
above, exit on a cross below"* produces exactly `1{hist > 0}`, and the level form is
self-healing (`macd.positions`).

### The fixture

`data/fixtures/universe_daily_2015_2024_raw.csv.gz` — **57 ETFs**, 143,355 rows. After the
1,000-bar warm-up: **2018-12-21 to 2024-12-30, 1,515 live bars, 6.01 years**, `PPY = 252`.

Costs are per-symbol from `run_macd_ladder.per_side_bps` on $10M notional split 57 ways.
Returns are **dividend-adjusted by default** (`total_log_returns`), price-only reported beside.

### What it actually did

| | Sharpe (price) | Sharpe (div-adj) | CAGR (price) | CAGR (div-adj) | total (div-adj) | max DD | exposure |
|---|---:|---:|---:|---:|---:|---:|---:|
| **the arm** | **+0.658** | **+0.793** | 5.99% | **7.23%** | **+52.12%** | **-12.70%** | **49.93%** |
| buy and hold | +0.333 | +0.457 | 6.08% | 8.42% | +62.59% | -34.81% | 100% |

D218 closed this as a failure on **hurdle D** — it beats the benchmark on Sharpe and loses on
money, +52.12% against +62.59%.

*Note on D218's prose: it quotes the best cell at "+0.658" while stating dividend-adjusted is
the default basis. +0.658 is the price-only Sharpe and +0.793 is the dividend-adjusted one;
the money figures quoted beside it are dividend-adjusted. The two bases are mixed in one
sentence. No verdict changes, but the comparison should be made within a basis, and this
record does that throughout.*

### Two facts about that money gap, established here, that D218 did not state

**(1) The money gap is *entirely* forgone dividend.** On price-only the arm and the benchmark
are a dead heat: **+41.83% against +42.59%**, a gap of 0.76 points at **a third of the
drawdown**. Dividends add 1.242 points of CAGR to the arm and 2.340 to the benchmark, and

```
1.242 / 2.340 = 0.531   ~=   exposure 0.499
```

The arm collects almost exactly its exposure-share of the yield. **The entire ten-point money
deficit is the price of being flat half the time**, not a shortfall in price performance.

This is the mechanism behind *"better Sharpe, less money"* six studies running: **every filter
tried so far removes exposure, and removing exposure removes yield.** Gating fights the arm's
money by construction.

**(2) The risk-free correction was applied wrongly in conversation, and the fix matters.**
A long-flat arm holds **cash** when flat, and cash earns `rf`. So `rf` is charged on the
**exposed fraction**, not on the whole book. At `rf = 4%` (`breakout_study.rf_annual`):

| | mean log | sd | exposure | excess | **Sharpe @ rf = 4%** |
|---|---:|---:|---:|---:|---:|
| **the arm** | 0.0698 | 0.0881 | 0.499 | 0.0498 | **+0.566** |
| buy and hold | 0.0808 | 0.1771 | 1.000 | 0.0408 | **+0.231** |

Charging `rf` on 100% of the arm gave **+0.354**; the correct figure is **+0.566**. The
direction is unchanged — the arm beats the benchmark on excess Sharpe — and the margin is
roughly double what was reported. **This accounting goes into the baseline of this study, not
into the candidate set:** it is a correction to how a long-flat book is scored, not a strategy
change, and it applies identically to the parent, every candidate and the benchmark.

---

## Part 2 — How the mining is done

### The free/costly boundary

The programme has never defined what counts as a "look" precisely enough to permit
exploration. This study proposes the line:

> **A look is any operation whose output is conditioned on the arm's realised P&L.**
> Describing the *market* is free. Describing the *arm's outcomes* is a look.

Characterising the volatility structure of these 57 ETFs costs nothing, because that analysis
is identical in a world where the arm was never built. Asking *"how did trades entered in
high-vol regimes do?"* is a look, and is counted.

### What is actually mined — and it is not the returns

**No candidate below was found by searching P&L.** The mining here is of the **arm's
construction**, asking one question that needs no returns at all:

> **What information does this arm have available, and throw away?**

- It takes **sign only** — `1{hist > 0}` discards the magnitude of `hist` entirely.
- It takes **unit size** — a full unit in a 40%-vol energy ETF and a full unit in SHY.
- It **equal-weights** every symbol it is long, discarding the cross-section.
- It sits in **cash 50% of the time**, discarding the yield that D218's hurdle D turned on.

Four discarded channels, none of which required looking at a single return to notice. That is
the search space, and it is why the declared candidate list *is* the whole search — which is
the condition that makes the null in Part 3 exact rather than approximate.

### The candidate set — 8, declared in full, mechanism before number

**Volume is excluded, and the stop is honoured, not overridden.** D220's stop reads *"no
volume work continues on this fixture"* and this is that fixture. Volume has now failed on
four separate fixtures (D220 daily, D224 15m crypto, D225 1h crypto, D226 57-ETF 15m). There
is no case for a fifth look and no override is sought.

**Family G — gating (removes exposure). Included as controls, expected to fail.**

| | rule | mechanism |
|---|---|---|
| **G1** | enter only when trailing 63-day realised vol is below its own trailing median | trend-following is whipsawed in high-vol chop |
| **G2** | enter only when the 200-day MA **slope** is positive | acceleration against a falling trend is a bounce, not a trend |

*G2 is deliberately distinct from D218's tested `200ma` gate, which compared price to the MA
level. Slope is a different rule; it is counted as a fresh look regardless.*

**Family S — sizing (preserves exposure). The actual hypothesis.**

| | rule | mechanism |
|---|---|---|
| **S1** | `position = clip(target_vol / realised_vol, 0, 1)` | equalises risk contribution across time and across instruments |
| **S2** | `position` proportional to normalised `abs(hist)` | recovers the magnitude the sign rule discards |
| **S3** | **G1 expressed continuously** rather than 0/1 | the paired test of gating vs sizing, same information |
| **S4** | **G2 expressed continuously** rather than 0/1 | the second paired test |
| **S5** | weight by cross-sectional rank of `hist` rather than equally | recovers the cross-section the equal weighting discards |

**Family R — exposure-raising.**

| | rule | mechanism |
|---|---|---|
| **R1** | hold **IEF** (already in the universe) when the arm is flat | the money deficit is forgone yield; flat time currently earns only cash |

**G1/S3 and G2/S4 are matched pairs on identical information.** They are the point of the
design: if the gating-vs-sizing hypothesis is right, the sizing twin beats its gate on money
while holding the Sharpe. If both twins move together, the hypothesis is wrong and the
distinction does not matter.

**The list is closed.** No candidate is added after this record is committed. An idea that
arrives later waits for its own pre-registration.

---

## Part 3 — The best-of-search null

### Why the analytic floor cannot be the verdict here

D218's floor at the verdict count is **+1.420**, and its own record says *"no arm anyone runs
on this universe can clear +1.42."* Of the 45,803 looks, **45,741 are inherited** — the floor
is set almost entirely by work that has nothing to do with this question. A hurdle that no
possible result can clear does not discipline research; it just ends it.

`expected_max_sharpe` is also an *approximation*: it takes `var_trials` as an input and cannot
see how correlated the candidates are with each other. Eight near-identical filters carry far
less multiplicity than eight genuinely different ones, and the analytic form cannot tell them
apart. **The quantity it approximates can be measured directly.**

### The construction

> Run the **identical search** — same 8 candidates, same code, same selection rule — over
> replications in which no candidate can have any true alignment with the arm's outcomes.
> Record **the best candidate found** in each replication. That distribution is the floor.

**Rotate the filter signal, not the positions.** Each replication draws one offset vector
(one offset per symbol) and circularly rotates **every candidate's signal series** by it,
following `run_macd_ladder.rotation_null`'s precedent. This:

- preserves each candidate's **own autocorrelation** exactly — it is the same series, pointed
  at the wrong bars;
- destroys its **alignment** with the arm's trades;
- leaves the **parent identical in every replication**, so the only thing varying is the
  filter's alignment, which isolates precisely the quantity in question.

**One offset vector per replication, reused across all 8 candidates.** This preserves the
*cross-candidate* correlation, and that is not a detail: rotating each candidate independently
would make the eight artificially independent, inflating the max and producing a floor that is
wrong in the conservative direction. Correlated candidates must stay correlated.

`n_sims = 1000`, `seed = 0`.

### The verdict rule — hurdle **B**

**The best real candidate's improvement over the parent must exceed the 95th percentile of
the best null candidate's improvement over the parent — on Sharpe AND on dividend-adjusted
money**, both reported at `rf = 4%` with `rf` charged on the exposed fraction.

This is a **gate, not a verdict.** It answers *"did the search find anything, or would any
search over these eight have found this much on noise?"* — and nothing more. A candidate that
clears B has earned the right to be tested on unmined data. It has not been shown to work.

### What else is reported, and what it is for

- **The analytic floor at all three counts** (8 fresh; 8 + D218's 62; 8 + 45,803), stated up
  front as *expected to fail at the verdict count* so that nobody reads its failure as news.
- **Hurdle P**: beat the unfiltered parent on both metrics. Six studies have cleared this on
  Sharpe and failed it on money.
- **Hurdle E**, unchanged: at least 100 pooled signals and at least 30 entries per ETF,
  asserted per cell.
- **Exposure and dividend capture per cell**, because Part 1 establishes those are the
  mechanism, and a candidate that improves Sharpe by cutting exposure should be visibly doing
  so.

---

## Predictions

Committed before any runner exists.

| | prediction | confidence |
|---|---|---|
| **Q1** | **No gating candidate (G1, G2) clears B.** Six studies, six failures, and Part 1 explains why | **high** |
| **Q2** | The best-of-search 95th percentile is **materially below +1.420** — a bar that can actually be cleared | **high** |
| **Q3** | **At least one sizing candidate beats its gating twin on money** while matching it within 0.10 Sharpe — the gating-vs-sizing hypothesis | **moderate** |
| **Q4** | The best-of-search floor is **above** the naive single-candidate null — i.e. selection bias over 8 correlated candidates is real and measurable, not negligible | **moderate-high** |
| **Q5** | **Nothing clears B at all.** The most likely single outcome, and the one the design must be able to report cleanly | **moderate** |

Q1 and Q5 are the predictions that would hurt to be wrong about, because they are the ones
that would let a mined result through.

---

## The stop

**If no candidate clears hurdle B, the filter line on this arm is closed.** No ninth
candidate, no widened sweep, no second fixture for the same question. The arm goes to unmined
data unfiltered, as it stands.

**If a candidate clears B, it is still not a result.** It becomes a hypothesis with a written
mechanism, and the next study tests it on **ETFs outside these 57** — the universe was a
choice, not a census, and the provider has hundreds more liquid names. No number from this
fixture is ever quoted as evidence for it.

---

## Ledger

| count | N | floor |
|---|---:|---|
| fresh (this candidate set) | **8** | computed at run |
| + D218's inherited | **70** | computed at run |
| + disclosed ETF prior | **45,811** | expected to fail — disclosed in advance |
| **best-of-search null (the verdict)** | — | **measured, not bounded** |

---

## What this record is really proposing

The methodological claim, separable from whether any candidate works:

> **Selection bias should be measured by running the search against nulls, not bounded by an
> analytic floor whose inputs are guessed.** The floor is a proxy; the simulation is the
> quantity itself, with the candidate set's real correlation structure included for free.

If that holds, it is reusable across the whole programme, and it is worth more than any filter
this study might find.
