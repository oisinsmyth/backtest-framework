# D228 — Mining the mined fixture: a filter search with a *measured* selection bias

**Status:** Committed (Q1, Q3, Q4, Q5 confirmed; Q2 confirmed on a corrected basis) — **the filter line is closed**
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

---

## RESULT

*Appended after the run. Nothing above this line was edited except the Status field.*

**Produced:** 2026-08-27 · **Reproduce:** `uv run python scripts/run_filter_search.py`
(offline, deterministic, seed 0, **73.5 s**) · Page:
[`FILTER_SEARCH_RESULTS.md`](../results/FILTER_SEARCH_RESULTS.md) · Artifact:
`data/filter_search_summary.json`

### The one-sentence version

**Nothing clears anything. The best of eight declared candidates improves the arm by +0.023
excess Sharpe against a measured selection-bias floor of +0.104 — so the search found less
than the same search finds on noise — and the pre-registered stop closes the filter line.**

### The eight

Parent: **+0.570** excess Sharpe, **+52.12%** dividend-adjusted, 49.9% exposure.
Buy and hold: **+0.235**, +62.59%, 100%.

| | excess Sharpe | Δ Sharpe | money | Δ money | exposure | entries | min/sym | P | E |
|---|---:|---:|---:|---:|---:|---:|---:|:--:|:--:|
| G1 vol gate | +0.399 | −0.171 | +16.39% | −35.73 pp | 24.0% | 1,334 | **16** | | **fail** |
| G2 slope gate | +0.089 | **−0.481** | +8.24% | −43.88 pp | 25.4% | 1,458 | **11** | | **fail** |
| **S1 inverse-vol** | **+0.594** | **+0.023** | +43.42% | −8.70 pp | 43.1% | 12,585 | 37 | | pass |
| S2 magnitude | +0.551 | −0.019 | +40.14% | −11.97 pp | 37.6% | 11,748 | 171 | | pass |
| S3 = G1 continuous | +0.459 | −0.111 | +31.72% | −20.40 pp | 42.8% | 2,418 | 34 | | pass |
| S4 = G2 continuous | +0.570 | +0.000 | +23.34% | −28.78 pp | 25.0% | 2,418 | 34 | | pass |
| S5 rank | +0.466 | −0.104 | +61.00% | **+8.88 pp** | 66.9% | 20,447 | 293 | | pass |
| R1 bonds when flat | +0.333 | −0.238 | +55.32% | +3.20 pp | 100.0% | 3,002 | 34 | | pass |

**Not one of the eight clears hurdle P.** Three improve money, none of those improves Sharpe;
one improves Sharpe, and it loses money. Six studies became seven.

### Hurdle B — the floor, measured

| | best real | null p50 | **null p95** | |
|---|---:|---:|---:|:--:|
| excess Sharpe | +0.023 | +0.014 | **+0.104** | **FAIL** |
| money | −8.70 pp | −1.95 pp | **+6.55 pp** | **FAIL** |

**The best candidate is inside the noise on both metrics.** S1's +0.023 is barely above the
null's *median* of +0.014 — the search's single best result is roughly what this search
returns on a coin flip.

### Scoring the predictions

| | prediction | outcome |
|---|---|---|
| **Q1** | No gating candidate clears B | **CONFIRMED, emphatically.** −0.171 and −0.481, and *both gates also fail hurdle E* — 16 and 11 entries per symbol against the required 30. The gates cut so hard they destroy their own sample |
| **Q2** | The floor is materially below +1.420 | **CONFIRMED, but the comparison as written was wrong** — see below. +1.420 is an *absolute* Sharpe floor; everything here is on the *delta* scale. The prediction compared incommensurable quantities and happened to be right |
| **Q3** | A sizing candidate beats its gating twin on money within 0.10 Sharpe | **CONFIRMED.** S3 beats G1 by **15.33 pp** of money at a Sharpe difference of 0.060. And S4 beats G2 on **both** metrics, by 15.10 pp and 0.481 Sharpe. **Sizing dominates gating on both matched pairs** |
| **Q4** | Selection bias over correlated candidates is real and measurable | **CONFIRMED.** Best-of-seven p95 **+0.104** against the largest single-candidate p95 of **+0.069** (G2) and S1's own **+0.022**. Searching seven costs ~5× a single look |
| **Q5** | Nothing clears B at all | **CONFIRMED** |

**Four of five, with Q2's reasoning corrected.**

### The finding that partly refutes this record's own premise

D228 argued that `expected_max_sharpe` should be replaced because it *"takes `var_trials` as an
input and cannot see how correlated the candidates are."* Measured, at **matched trial count**:

| | floor |
|---|---:|
| analytic `expected_max_sharpe(8, var_from_null)` | **+0.099** |
| **measured best-of-seven p95** | **+0.104** |

**They agree to within 5%.** The formula is well calibrated. What was wrong was never the
approximation — it was **the `var_trials` fed to it and the inherited N**, and D224 had already
caught the first of those.

So the honest version of this record's methodological claim is narrower than the claim it
made:

> **The simulation's value is that it supplies the right `var_trials` for free and cannot be
> fed the wrong one.** It is not that the analytic bound is inaccurate. On this candidate set
> the two are interchangeable, and the correlation structure the simulation captures for free
> turned out not to matter much here — which is itself only knowable by having run it.

The analytic floor at the disclosed prior (**+0.287** on the delta scale, N = 45,811) also
fails S1's +0.023, so the verdict is unanimous across every bar this study could have used.

### The mechanism, confirmed across eight independent constructions

D228 Part 1 claimed the arm's money gap against buy-and-hold **is** its exposure gap. Eight
candidates spanning **24.0% to 100.0%** exposure:

> **r = +0.823**, slope **0.58 pp of money per pp of exposure.**

The two candidates that gain money are the two that raise exposure (S5 at 66.9%, R1 at 100%);
the two that lose most are the two gates that cut it hardest. **A filter's effect on this
arm's money is predicted by how much time it removes from the market, and almost nothing
else.** That is the mechanism behind seven studies of "better Sharpe, less money", measured
rather than argued.

**S4 is the cleanest illustration and reads as a control**: it is close to a pure scale change,
and it moves money by −28.78 pp while moving Sharpe by **+0.000**. Sharpe is scale-invariant;
money is not.

### Defects and disclosures

1. **`MEDIAN_WINDOW = 252` was not pinned by the pre-registration.** The record named "trailing
   63-day realised vol … below its own trailing median" without saying over what window. One
   year was chosen at implementation time. It is a free parameter the pre-registration failed
   to close, and it is disclosed rather than described as declared.
2. **S4's construction was not pinned either**, and the reading chosen (`0.5 + 0.5·z`) turned
   out **near-degenerate** — mostly a constant halving. It was left as built rather than
   corrected after the smoke run, because changing a candidate after seeing its number is the
   exact freedom this study exists to control. The best-of-search null handles it correctly
   anyway: a candidate that cannot discriminate contributes nothing to the max in *either* the
   real or the rotated arm, and its own null p95 of **+0.001** shows that directly.
3. **S5 does not do what the pre-registration implied.** It normalises rank to mean 1 across
   **all 57** symbols rather than the held subset, so it *raises* exposure to 66.9% instead of
   preserving it. Also left as built, for the same reason, and it is why S5 gains money.
4. **R1 is excluded from hurdle B** — its signal is the parent's own flat mask, so there is
   nothing to rotate. The null covers **seven** candidates, not eight. This is a gap in the
   pre-registration's design, not in the runner.
5. **The exposure-vs-money correlation was added after a 5-sim smoke run**, when the pattern
   was visible in the table. It is descriptive, costs no looks (it re-reads cells already
   scored), and is not a hurdle. Flagged because it was not pre-registered.
6. **The runner was written after this record was committed**, which is the correct order and
   the opposite of D226's disclosure.

### What this changes

**The pre-registered stop applies: the filter line on this arm is closed.** No ninth candidate,
no widened sweep, no second fixture for the same question. Seven studies have now tried to
improve this arm by filtering it and all seven failed, and D228 supplies the reason rather than
another instance: **filtering removes exposure, and on this arm money is exposure.**

**What survives is the arm, unfiltered** — **+0.570** excess Sharpe against buy-and-hold's
**+0.235**, at 8.8% volatility against 17.7%, with a −12.70% maximum drawdown against −34.81%.
It has never been tested on unmined data, and that is now the only live thread on this line.

**And the boundary survives.** *"A look is any operation conditioned on the arm's realised
P&L"* let this study derive eight candidates from the arm's construction without spending a
single look on exploration, and let D229 measure turnover, exposure and dead-zone frequency
before committing to predictions. It is the reusable part.
