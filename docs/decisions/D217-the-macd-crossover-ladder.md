# D217 — the MACD crossover ladder: does the signal line add anything to trend following?

**Status:** Committed (H7 confirmed on turnover; H1, H3, H4, H6 falsified; H2 and H5 split)
**Date:** 2026-08-24
**Category:** Validation & research integrity
**Source:** A new study, opened on the most widely taught technical strategy there is

> A result section will be appended and nothing above it edited.

## What is being tested

The MACD signal-line crossover — long when the MACD line crosses above its 9-period signal
line, out or short when it crosses below. Gerald Appel, 1979; the histogram is Thomas
Aspray's, 1986. The 12/26/9 parameterisation is Appel's own and is the one every tutorial
teaches.

**The claim under test is not "does MACD make money".** It is:

> **H₀ — the signal line adds nothing over the zero-line cross, and the zero-line cross adds
> nothing over plain time-series momentum.**

If H₀ holds, "the MACD strategy" is trend following with two extra parameters and a worse
name, and the correct description of the indicator is a re-parameterisation rather than a
signal.

The reason to frame it that way is algebraic rather than empirical. The MACD line is
`EMA(close, 12) − EMA(close, 26)`, a difference of two exponential filters — a band-pass
filter, and by Zakamulin's result every moving-average trading rule can be rewritten as a
weighted moving average of past price changes, with performance depending *exclusively on the
shape of that weighting function*. MACD, a 12/26 EMA crossover, and an N-bar momentum rule are
therefore the same object under three weighting kernels. A study that tests MACD against
buy-and-hold and stops there cannot distinguish "MACD works" from "trend following works and
MACD is one spelling of it."

**This project has already been caught by exactly that failure once.** The STRUCTURE
programme closed after 86 looks with three features that cleared the promotion bar turning out
to be one quantity under three names — leg size relative to ATR. The design below exists to
detect that outcome by construction rather than discover it in the write-up.

### The ladder

Three strictly nested rungs, each containing the one below it:

| Rung | Rule | What it adds over the rung below |
|---|---|---|
| **R1** | MACD line crosses its 9-EMA signal line | the signal-line smoothing |
| **R2** | MACD line crosses zero — *identically* a 12/26 EMA crossover | the two-EMA difference |
| **R3** | sign of the trailing **37**-bar return | — (the floor) |

R2 is worth stating plainly because it is usually obscured: the MACD line crossing zero is the
event `EMA(12) = EMA(26)`. The signal line plays no part in it. R2 is a moving-average
crossover wearing the indicator's name.

### Deriving the rungs, and correcting my own arithmetic before the run

I first wrote R3's lookback as **26**, on the reasoning that the slow period of the rung above
is the natural match. **That is wrong, and the correct number is 37.** Working it out before
the run rather than after:

An EMA is linear and both EMAs' weights sum to 1, so the MACD's weighting of price *levels*
sums to zero — and a zero-sum weighting of levels is, by Abel summation, a weighting of
*returns*:

```
MACD_t = Σ_{i≥0} c_i · r_{t−i},     c_i = λ_s^(i+1) − λ_f^(i+1),     λ = (n−1)/(n+1)
```

For (12, 26): `λ_f = 11/13`, `λ_s = 25/27`, so **every `c_i > 0`** — a strictly positive,
hump-shaped kernel over roughly the last 40 returns, peaking around `c₈ ≈ 0.278`. Two exact
facts fall out:

- **Σ cᵢ = (n_s−1)/2 − (n_f−1)/2 = 12.5 − 5.5 = 7.0**
- **centre of mass = (a²−b²)/(a−b) = a + b = 12.5 + 5.5 = exactly 18.0 bars**

A flat N-bar momentum kernel has centre of mass `(N−1)/2`. Matching the two gives
**N = 2×18 + 1 = 37**. So R3's lookback is **derived from R2's kernel, not chosen**, and a
26-bar control would have been centred 12.5 bars back against R2's 18 — an unmatched
comparison that would have flattered whichever rung happened to suit the sample. `37` is a
pinned constant in the code, not a sweep default.

**And the signal line is not more of the same trend hypothesis — it is a different one.**
Because `(I − EMA₉)` annihilates constants, the *signal-line rule's* return kernel sums to
**exactly zero**: under constant drift `b`, the MACD sits at `7b` and the signal line converges
to `7b`, so their difference converges to `0`. R1 does not measure trend at all. **R1 is a
trend-*acceleration* rule; R2 is a trend-*level* rule.** That is the sharpest available
statement of what the signal line adds, it is exactly falsifiable, and it is what H1 and H7
below are really testing.

## The prior, stated before the run

**I expect every rung to be null, and I expect the deltas between them to be the interesting
number rather than the levels.** Saying so now costs nothing; saying it after the result costs
credibility.

The external evidence points the same way and is disclosed rather than leaned on:

- A 14.3M-configuration parameter sweep (20 assets, 436 fast/slow pairs, 8 signal periods, 26
  holding periods, Bonferroni-corrected) reports **zero significant results from 1,788,800
  line-crossover tests**, and zero for 12/26/9 specifically on both sides. *Not peer-reviewed,
  methodology not auditable from the publication — cited for its design instinct (family-wise
  correction at scale), not as an authority.*
- *Improving MACD Technical Analysis…* (JRFM, 2021) finds textbook 12/26/9 **negative** on
  Nikkei 225 futures 2011–2019, and a positive optimised triple selected from **19,456
  models** without a data-snooping adjustment. I read that as evidence against the standard
  parameters and as an uncorrected in-sample search, not as evidence for optimisation.
- arXiv 2206.12282 (US indices, 2015–2021) reports a standalone MACD **win rate below 50%**,
  with no buy-and-hold benchmark and no transaction costs, over a sample that was mostly one
  bull market.
- Sullivan, Timmermann & White (1999): the bootstrap reality check dissolved most of the
  technical-rule literature's apparent profitability once the full universe of rules searched
  was accounted for. This is the result that governs the ledger below.

### Correcting the frame before the design: friction is probably not the binding constraint here

The last four studies in this project were 15m crypto, where friction ended the question
before the signal did — D215's effect was 0.24×–0.32× the cost of capturing it, and D216's
gap narrowed from ~4× to ~4 points and did not close. **It would be an error to carry that
intuition into daily ETFs, and I am recording the arithmetic now so the result cannot be
narrated as a cost story after the fact.**

Order-of-magnitude, to be replaced by WP2's measured figure: `IBKRCommission` at $0.005/share
on a $100 ETF is 0.5 bp, plus a 1 bp half-spread ≈ **1.5–2.5 bp per side**. A 12/26/9 daily
crossover turns over on the order of 25 round trips per year, so ≈ 50 sides ≈ **0.75–1.25%
per year** of drag, against an ETF vol near 15% — roughly **0.05–0.08 of Sharpe**.

That is real and it is not fatal. **On this fixture the signal has to fail on its own merits,
not on fees.** If it fails, "costs killed it" is not available as an explanation, and that is
the point of computing this before the run rather than after. The BREAKOUT study reached the
same conclusion by a different route, and its own verdict — that fees are not the binding
constraint — remains the least interesting true thing about it.

## Design

**Fixture.** `data/fixtures/universe_daily_2015_2024_raw.csv.gz` — the frozen 57-ETF universe,
**57 of 57 requested included, 0 excluded**, 2,515 daily bars each, 2015-01-01 → 2024-12-31.
Committed, offline, deterministic. Provider frame per its own metadata: `yfinance
auto_adjust=False, actions=True` — split-adjusted, **dividend-unadjusted** (D75), with an
`_events.json` sidecar carrying the flows.

Daily is chosen because 12/26/9 is a daily-designed parameterisation and testing it at 15m
would be answering a different question than the one the literature asks. The 15m crypto
fixture is not used and no result from it is inherited.

**Periods per year:** 252.0.

**Books.** Long-short flip and long-flat, as **separate arms**. Long-short isolates whether the
sign predicts direction; long-flat is the retail rule and is roughly half beta-loaded, which
is why the two are reported side by side rather than one standing for both. The gap between
them is itself a measurement.

**A constraint the short arm inherits, recorded now.** D169's reasoning — that a short book's
expectancy is only calculable with the squeeze tail truncated by construction, i.e. with a stop
— applies to any short arm at the engine layer. **But a stop is a third hypothesis**, and
putting one inside the ladder would make the rungs non-nested, which is the one thing this
design cannot afford. The resolution: Stage 1's long-short arm is a continuous position series
with no stop and no trade-level expectancy claim, which is where D169's concern does not bite;
if Stage 2 ever runs a short arm through the engine, the stop question is reopened there, in
writing, and not silently inherited.

**The statistic, and why 57 ETFs is not 57 looks.** The claim is about the rule, not about any
ETF. Each arm produces **one** statistic: the equal-weighted cross-sectional portfolio of the
per-ETF position series, scored by `curve_sharpe`. The 57 assets are the sample that gives
that statistic power; they are not 57 hypotheses. Per-ETF results are reported as dispersion
beside the headline and are **never selected from**. This is stated because the opposite
convention — STRUCTURE's `cells × symbols` — was the house habit at 2 symbols and would be
wrong at 57.

**Cost convention.** D212 is binding: **per side is the authority.** `PositionResult`
charges on every unit of exposure changed, so a long-short flip is charged twice, which is
correct. The bps figure is **derived, not chosen**: computed per ETF from the IBKR schedule at
that ETF's median close plus a 1 bp half-spread, and reported. A ±10 bp sensitivity column
sits beside the headline.

**Dividends are a real bias here and are handled, not noted.** A long-flat arm is out of the
market part of the time; buy-and-hold never is. Running raw closes against a total-return
benchmark **biases the comparison in the strategy's favour**. Both the arms and the benchmark
are computed on the same dividend treatment, and if that proves awkward at this layer the
raw-price result is reported *with the bias direction and its size stated*.

**Warm-up, and the arithmetic for it.** MACD is **the first IIR estimator in a codebase built
entirely on FIR windows** — every other indicator here (Donchian, ATR, the SMA gate, realized
vol, the z-score) is a function of an explicit `range(i−w, i)`, whereas the MACD's value at `t`
depends on where the run *started*. Two studies over different date ranges would see different
MACD at the same calendar bar. The burn-in is what makes it safe to use in a walk-forward at
all, and it is a research-integrity parameter — *do not trade on a number the seed convention
could have moved* — not a numerical nicety.

Two seeds differing by `Δ` differ by `Δ·λᵏ` after `k` bars. Requiring residual ≤ `1e-12 ×
price` from a worst-case O(price) seed error:

```
BURN_IN(n) = ceil( ln(1e-12) / ln((n−1)/(n+1)) )
  n = 12 → 166      n = 9 → 124      n = 26 → 360   ← binding
warm_up = (slow−1) + (signal−1) + BURN_IN(slow) = 25 + 8 + 360 = 393 bars
```

**393 bars is ~15.6% of each 2,515-bar ETF series**, and that is a real cost stated up front.
It is *not* zero-risk: any crossing whose margin is within `1e-12 × price` of zero can still
have its sign flipped by the seed. That is a knife-edge property of the **rule**, not of the
seed, and H7 is where it gets measured.

**The comparability constraint.** R1 warms up at 393, R2 at 385, R3 at 37. If each arm starts
on its own first eligible bar the three equity curves cover different spans and **the ladder
is not a comparison**. Every arm therefore starts on the same bar — the maximum warm-up across
the whole ladder — and the runner asserts this rather than assuming it.

**Fill convention.** The cross is evaluated on a completed bar and filled at the next open, so
the decision bar is never the fill bar. One asymmetry against the breakout strategy sitting
next to it is named rather than glossed: `∂(macd − signal)/∂close(t) = (α_f − α_s)(1 − α_g) > 0`,
so **today's close can flip the rule on its own** — a property `breakout.py` deliberately
engineers away. It is not look-ahead (the bar is complete, the fill is next-open) but it is a
different robustness profile, and it is stated here so it cannot be discovered later and read
as a defect.

**Normalisation is not swept, and the reason is a proof rather than a preference.** Every EMA
is linear, so for `P' = cP` with `c > 0` the whole ladder rescales and the *sign* is exactly
invariant. Stronger: for any strictly positive divisor series `d_t`,
`sign(macd_t / d_t) ≡ sign(macd_t)` bit-for-bit. **PPO's zero-line cross and MACD's zero-line
cross are therefore the same strategy — not similar, identical, bar for bar** — and the same
holds for ATR-normalisation. R2 and R3 cannot be moved by any positive normalisation, so
normalising them would be trial-count inflation buying a provable no-op.

R1 is the exception: `EMA₉(macd/d) ≠ EMA₉(macd)/d` when `d` varies, so **PPO-signal-cross and
MACD-signal-cross are two genuinely different hypotheses**. That distinction is real and it is
**deliberately not in this ledger** — adding it mid-design is exactly the scope addition the
house rules forbid. It goes to the parking lot with this note: on a 2015–2024 ETF universe no
member ran the kind of multiple where the two diverge much, so it is a question for a
crypto-daily replication, not for this study.

### The arms

| Block | Cells | Looks |
|---|---|---|
| Core ladder | 3 rungs × 2 books × {200-MA filter off, on} | **12** |
| Parameter sweep | fast ∈ {6,12,24} × slow ∈ {13,26,52} with `fast < slow` ⇒ 6 pairs; R1 × signal ∈ {5,9,18} = 18, R2 = 6; long-short only, filter off; minus the 2 already counted above | **22** |
| **Total** | | **34** |

The grid is **declared here and is not extended later.** Its purpose is to answer a specific
published claim — that 12/26/9 is unremarkable within its own parameter distribution — not to
find a winner. Every cell is reported whether or not it is flattering.

The 200-MA filter is the commercially taught confluence version: take a cross only in the
direction of a 200-period moving average. It is in the design to test whether the filter,
rather than the MACD, is doing whatever work gets done.

## The hurdles

All required. A cell that misses any one of them is not a survivor.

**A. The nested-ladder deltas — this is the study.**
R1 − R2 ≥ **+0.10** Sharpe *and* R2 − R3 ≥ +0.10, each above the paired bootstrap's **p95**.

**B.** Beat the matched placebo null (random entries, same count and holding-period
distribution) by ≥ +0.10 Sharpe, above p95.

**C.** Beat the rotation/shuffle null by ≥ +0.10 Sharpe, above p95.

**D.** Long-flat arms must beat **buy-and-hold**. Long-short arms must clear **cash** — net
Sharpe > 0 after costs. Buy-and-hold is the wrong yardstick for a near-zero-beta book and
saying so now, rather than when a long-short arm conveniently fails it, costs nothing.

**E.** n ≥ 100 signals pooled per arm, and ≥ 30 entries per ETF on the fully-filtered arm.
Below either, the cell is **underpowered and carries no verdict** (D216's rule, unchanged).

**F.** Same sign in both chronological halves — 2015–2019 and 2020–2024.

**G.** Annualised Sharpe clears the deflated-Sharpe bar at all three multiplicity counts below.

**Every delta is reported with the null percentile beside it.** D202's lesson 5 is the reason
and it is a limitation this project found in its own method: a +0.10 delta over a null *mean*
is not a hurdle when the null is wide — D201's statistic cleared it at the 67th percentile. A
delta that clears +0.10 while sitting below p95 has not cleared anything.

## Controls and nulls

Reused rather than rebuilt: `research/breakout_nulls.py` supplies `bar_shapes` /
`resample_bars` (block bootstrap of bar shapes), `simulation_seeds` for the explicit-seed
policy (D34), `path_null` and `summarise_null` → `NullDistribution`, which is where the
percentiles the hurdles require come from. `terrain_field_nulls.rotation_null` supplies the
rotation control. `trade_bootstrap` supplies the paired bootstrap for hurdle A.

**Rejected-signal counterfactual, mandatory per D198/D214.** Where an arm filters (the 200-MA
version), the outcomes of the **rejected** crosses are reported beside the kept ones, always.
In 8 of 12 cells of D214 the rejected trades beat the kept ones, and that is only visible if
it is reported by default rather than on suspicion.

**The census runs first and carries zero looks** — crossover counts, trade frequency and
holding-period distributions per ETF, before any performance number. WP2 exists because counts
have repeatedly caught defects in this project before they became results (D197, D198, D201,
D202), and because *"there is no sample"* is a legitimate finding about a strategy sold as a
repeatable process.

## Predictions, committed now

| | Prediction | Confidence |
|---|---|---|
| **H1** | R1 − R2 < +0.10 Sharpe on both books — the signal line adds nothing. Sharper form: R1's kernel sums to zero, so it is a trend-*acceleration* bet, and acceleration is not what carries the trend premium | **high** |
| **H2** | R2 − R3 < +0.10 — the two-EMA difference adds nothing over flat 37-bar momentum at the same centre of mass | **moderate-high** |
| **H3** | Long-flat arms beat cash but **lose to buy-and-hold** over 2015–2024 | **moderate-high** |
| **H4** | Long-short arms are ≤ 0 net of costs | **moderate** |
| **H5** | 12/26/9 sits mid-distribution in the sweep, and the best swept cell fails to clear `expected_max_sharpe` for the sweep's own N | **moderate-high** |
| **H6** | The 200-MA filter improves long-flat and does ~nothing for long-short — i.e. it is beta timing, not signal improvement | **moderate** |
| **H7** | **R1 turns over materially more than R2** — because its kernel sums to zero, the signal-line difference decays geometrically toward zero on any smooth trend, so near the crossing its sign is decided by noise and the arm chatters. Prediction: R1's turnover exceeds R2's by ≥ 50%, and R1 gives back more to costs than R2 | **moderate-high** |

**On H5, the honest framing of the default parameters.** 12/26/9 is famous *because people
found it worked* — it is the XLE/XOP of technical indicators (D70/D22). The default arm is
therefore meta-in-sample by parameter choice, through a search this project did not run and
cannot count. The report leads with the **plateau** around 12/26/9, not with the default cell,
and any result at exactly 12/26/9 is read in that light.

**H6 is the one to watch**, and the reason both books are in the design rather than one. It is
the only prediction whose positive branch would mean something real, and the only one the
arithmetic does not settle in advance. H1's confidence is *high* because it is a claim about
algebra as much as about data — which is exactly the kind of confidence this project has been
wrong with before (D214's H2 pointed the right way at a twentieth of the size needed).

## The rule if it works, committed now

D215's rule applies unchanged: a surviving cell is a **positive claim**, it does **not** get
pursued inside this study, and it gets **its own pre-registration and its own holdout** before
anyone believes it. Committed here so it survives contact with a good number.

**And the programme stop:** if no cell clears hurdles A–G, **Stage 2 — the costed engine
verdict — does not run**, and the study closes as a reportable negative. This is WP4→WP5's
precedent from the STRUCTURE programme, where WP5 genuinely did not run.

## Ledger

**This study opens a fresh ledger at 34, with the prior counts disclosed adjacent.** The
argument, made explicitly because a positive-claim study does not get the asymmetry D215's
Test A relied on: different fixture (ETF daily, not crypto 15m), different claim family
(directional single-name momentum, not structure or terrain), and a sensor that does not exist
in this repo — there is no EMA anywhere in the codebase, so nothing is being re-read.

The verdict is nonetheless reported against **three** counts, per D214, so that a result which
would have been publishable as a first study and is not publishable as the *n*-th look is
visible as exactly that:

1. **Fresh — 34.**
2. **Fresh + prior ETF-fixture configurations.** The registries that ran on this universe hold
   **129,286 rows** between them: `e1_universe` 41,760, `combined_universe` 20,880,
   `portfolio_universe` 20,880, `swing_universe` 20,880, `capacity_portfolio` 18,270,
   `etf_universe` 4,446, `gross_sweep` 980, `capacity_study` 385, `convention_sensitivity` 280,
   `pairs_study_v1/v2/v3` 175 each.

   **129,286 is a row count, not an N, and it is not fed to `expected_max_sharpe` as one.**
   D98/D116/D126/D142 are explicit that re-running the same window at scaled costs is not an
   independent trial, and that the `include` predicate must select on config identity and never
   on presence of the metric. Count 2 is the number of **distinct configurations** under a
   predicate de-duplicating window, cost multiplier and symbol; the raw 129,286 is reported
   beside it as the ceiling. Both are produced by the runner from `TrialRegistry.all_trials()`,
   never typed in.
3. **Combined** — count 2 plus the disclosed 395-look structure+terrain bar, as a deliberate
   upper bound, labelled as such rather than claimed as the right count.

**Count 3 carries the verdict.** `validation/dsr.expected_max_sharpe` supplies the noise floor
at each, computed in the runner. The D98 units contract applies: the logged metric, `sr` and
`t` are all per-period.

**Never reset. Retired and failed cells count.** The 34 is an estimate of the declared design,
not a licence — the actual count is what feeds the deflated Sharpe, and any post-hoc re-reading
is counted separately and in full rather than folded into the arm it re-reads (D209's rule).

## What would change my mind

**H1 failing.** A signal-line delta clearing +0.10 above p95 on both books would mean the 9-EMA
smoothing does real work that the zero-line cross does not — which contradicts the algebra this
whole design rests on, and would be the most interesting outcome available here. It would also
mean the ladder framing is wrong, and the correct response would be to say so rather than to
explain it away.

Secondarily: if the census shows the fully-filtered arm leaves fewer than 30 entries per ETF,
the honest finding is that a strategy sold as a repeatable process does not fire often enough
to be one, and that finding is reported instead of the performance numbers, not alongside them.

---

## RESULT

*Appended after the run. Nothing above this line was edited.*

**Produced:** 2026-08-24 · **Reproduce:** `uv run python scripts/run_macd_ladder.py`
(offline, deterministic, seed 0) · Ledger: [`MACD_RESULTS.md`](../../MACD_RESULTS.md) ·
Artifact: `data/macd_ladder_summary.json`

### The one-sentence version

**The signal line is the only part of MACD that does anything, it does considerably more
than the +0.10 hurdle, it survives a stricter fill than the one pre-registered — and the
whole thing still dies, on multiplicity alone, at the last hurdle of seven.**

### Scoring my own predictions

| | Prediction | Outcome |
|---|---|---|
| **H1** | signal line adds nothing (R1−R2 < +0.10) | **FALSIFIED.** +0.285 / +0.209 / +0.186 / +0.093 across the four book×gate cells — clears on three of four, and survives the lag bracket |
| **H2** | two-EMA difference adds nothing over flat 37-bar momentum | **SPLIT, and the split is the finding.** +0.163 / +0.129 at the primary fill, **+0.042 / +0.033** with one more bar of lag. The advantage is a fill-timing artifact |
| **H3** | long-flat arms lose to buy-and-hold | **FALSIFIED** for both MACD rungs (+0.496 and +0.286 against B&H's +0.266), confirmed for momentum (+0.157) |
| **H4** | long-short arms ≤ 0 net of costs | **FALSIFIED** for R1 (+0.312) and marginally for R2 (+0.026); confirmed for R3 (−0.136) |
| **H5** | 12/26/9 mid-distribution, and the best swept cell fails its own noise floor | **SPLIT.** Mid-distribution **confirmed** — rank 10 of 32, +0.324 against a grid median of +0.295. Noise floor **falsified**: the best cell (+0.397, 12/52/9) clears SR0 = +0.318 at the sweep's own N |
| **H6** | the 200-MA filter improves long-flat, does ~nothing for long-short | **FALSIFIED, and in the opposite direction.** The filter makes *every* cell worse in *both* books — signal-line long-flat falls +0.496 → +0.288 |
| **H7** | R1 turns over ≥1.5× R2 and gives back the difference to costs | **CONFIRMED on turnover** (2.35× / 1.65× / 2.34× / 1.86×), **falsified on the consequence** — the drag is 0.015–0.054 Sharpe and cannot overturn a +0.285 delta |

**One clean confirmation, four falsifications and two splits.** That is a bad prediction
record and it is the honest summary. The one I was most confident about — H1, at *high*,
on the grounds that the algebra settled it — is the one that failed hardest.

### What is actually true

**1. The signal line is not the redundant part. It is the only part that works.**

The prediction rested on a correct piece of algebra read the wrong way round. R1's return
kernel does sum to zero, and R1 *is* a trend-acceleration rule rather than a trend-level
rule — the derivation stands and the tests pin it. What I inferred from that was that
acceleration would be noise. On this universe it is the reverse: the *level* rung is the
dead one.

The sweep makes this structural rather than anecdotal. **All eight zero-line cells in the
declared grid land between −0.166 and +0.080** — every parameterisation of "EMA(fast)
crosses EMA(slow)", across a 4× range of both windows, is indistinguishable from nothing.
The twenty-four signal-line cells have a median of **+0.315**. That is not a knife-edge or
a lucky cell; the two rungs separate across the whole grid.

**2. The two-EMA difference's edge over flat momentum is a fill-timing artifact.**

R2 − R3 is +0.163 at the primary fill and **+0.042** with one more bar of lag. R1 − R2 is
+0.285 and **+0.247** — it barely moves. So the middle rung is doing nothing that survives
contact with a realistic fill, while the top rung is. Momentum is the only arm that gets
*better* with lag (−0.136 → −0.064 long-short), which is what a slower signal should do.

**3. The confluence filter is destructive, and it is destructive everywhere.**

The 200-MA gate — the commercially taught version of this strategy — costs between −0.09
and −0.21 Sharpe on every one of the six cells it touches, in both books. It is not beta
timing that helps a long-flat book and does nothing for a long-short one, as predicted; it
just removes good exposure. This is the second time this project has found a taught
confluence stack to be worse than no filter at all.

**4. The result dies on multiplicity, and only on multiplicity.**

`signal_line / long_flat / gate off` clears **six of seven hurdles**: the ladder deltas,
the rotation null (+0.282 at the **99.25th** percentile, above its p95 of +0.371), the
block null (100th percentile), buy-and-hold (+0.496 against +0.266, at *half* the drawdown
— −13.6% against −35.1%), and sign stability across both halves (+0.647 and +0.469).

It fails **G**. At the fresh count of 42 looks the noise floor is SR0 = **+0.334** and
+0.496 clears it comfortably. At the verdict count — 45,783, which is the fresh count plus
the 45,346 distinct configurations already logged against this fixture plus the disclosed
395 — the floor is **+0.638**, and it does not.

**This is the exact situation D214 built the three-count report for: a result that would
have been publishable as a first study and is not publishable as the 45,783rd look, made
visible as precisely that.** The honest statement is not "MACD does not work"; it is that
*this project has already spent enough of its search budget on this fixture that it can no
longer distinguish a +0.496 Sharpe from the best of its own noise.* Sullivan, Timmermann &
White (1999) is not a citation here — it is the mechanism that produced the verdict, run
against this project's own trial registry.

**0 of 12 cells clear every hurdle. Stage 2 does not run.** The pre-registered programme
stop applies and the study closes as a reportable negative.

**5. Friction was never the binding constraint, as predicted — but the retail arithmetic
is its own finding.** Institutional per-side cost is 1.82 bp median and the drag is 0.015
Sharpe. At a $100,000 book split 57 ways the **IBKR $1.00 per-order minimum binds on all
57 ETFs**, taking the per-side cost to 6.7 bp — roughly 4× — for identical trades. Still
not fatal here (0.054 Sharpe), but it means the cost of this strategy is a function of who
is trading it, and quoting one number for it would have been wrong.

### Defects found, and how

**The ledger arithmetic was wrong in the pre-registration, and the runner caught it.** The
record wrote the sweep block as "6 (fast,slow) pairs ⇒ 22 looks". The grid it declares —
fast ∈ {6,12,24}, slow ∈ {13,26,52}, `fast < slow` — admits **eight** pairs: (12,13) and
(24,26) satisfy the constraint and were missed counting by eye. The grid was not widened;
the count was wrong. Corrected fresh total: **42**, and that is the number the deflated
Sharpe is computed against. `test_the_sweep_grid_admits_eight_pairs_not_six` pins it.

**The implemented fill is one bar more favourable than the pre-registered one.** D217 says
next-open. A close-to-close position series cannot express an open fill, and the repo's
`PositionResult` convention charges as if filled at the decision close. Rather than argue
about which is closer, every cell is reported at both `lag=1` and `lag=2`, which brackets
next-open from either side. **That disclosure is what produced finding 2** — without it,
R2 − R3 = +0.163 would have been reported as a real effect. This is a sensitivity on the
same 12 cells, not 12 further looks.

### Ledger

| block | looks |
|---|---:|
| core ladder — 3 rungs × 2 books × {gate off, on} | 12 |
| declared sweep — 8 pairs × 3 signals + 8 zero-line, minus 2 already counted | 30 |
| **fresh total** | **42** |

Census, break-even arithmetic, the lag bracket, the nulls and buy-and-hold carry zero
looks. Verdict count: **45,783** (42 + 45,346 distinct prior ETF-fixture configurations +
395 disclosed). The raw registry row count, **129,286**, is reported as a ceiling and is
**not** used as an N.

### What happens to the positive

D215's rule, pre-committed and unchanged: the surviving cell is a positive claim, it does
**not** get pursued inside this study, and it gets its own pre-registration and its own
holdout before anyone believes it. Two things would have to be true for that to be worth
doing, and both are stated now rather than after a good number:

1. **It has to replicate out of sample on a fixture this project has not already mined** —
   the crypto daily universe is the obvious candidate, and it is the only way to escape a
   45,346-configuration prior that has nothing to do with MACD but everything to do with
   what this fixture has already been asked.
2. **The R1-versus-R2 separation has to survive it.** That separation, not the level, is
   the transferable claim: *trend acceleration predicts where trend level does not.* If
   that reproduces on independent data it is worth a study. If it does not, the honest
   reading of this one is that 45,783 looks bought a coincidence with a good story.
