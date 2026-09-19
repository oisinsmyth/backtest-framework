# Feature Research Protocol

**Status:** design document, pre-implementation
**Scope:** equities (cross-sectional) and futures (cross-sectional + time-series)
**Audience:** future me, and anyone reading this repo as a portfolio piece

---

## 0. Why this document exists

The existing framework tests **strategies**. A strategy bundles together:

1. a predictive claim (this quantity carries information about future returns)
2. an entry rule
3. an exit rule
4. a sizing rule
5. a cost model

When a strategy fails, all five are suspects and you cannot tell which one is guilty.
When it succeeds, you cannot tell whether (1) was real or whether (2)–(4) happened
to fit the noise. Each full backtest also consumes a large slice of the multiplicity
budget, because the parameter surface is high-dimensional.

This protocol isolates (1) and tests it on its own, before any trading logic exists.
The output is a **feature library** with a numeric admission criterion, not a pile of
strategies. Strategy construction happens *afterwards*, downstream of a feature that
has already earned its place.

**Ordering rule:** no feature enters a strategy until it has passed this protocol.
No strategy is built to justify a feature that failed it.

---

## 1. Definitions

| Term | Definition |
|---|---|
| **Feature** `f(i, t)` | A number computed for instrument `i` at time `t` using only information available at or before `t`. |
| **Forward return** `r(i, t, h)` | Return of instrument `i` from `t` to `t+h`. The prediction target. |
| **IC** | Information Coefficient. Rank correlation between the feature and the forward return. |
| **IC decay curve** | Mean IC plotted against horizon `h`. Tells you the natural holding period. |
| **Incremental IC** | IC of a feature after regressing out every feature already in the library. |
| **Breadth** | Number of genuinely independent bets per year. Drives achievable Sharpe. |

The governing arithmetic is the Fundamental Law of Active Management:

```
IR ≈ IC × sqrt(Breadth)
```

This single relation explains most of the structural differences between equity and
futures research and should be kept in mind throughout. An IC of 0.03 with 500 names
rebalanced daily is a business. The same IC across 30 futures contracts rebalanced
monthly is not.

---

## 2. Defining the target

### 2.1 General rules

- Use **log returns** for aggregation and analysis, simple returns for P&L.
- Compute forward returns from the **tradeable price**, not the close you cannot get.
  If the intended fill is next-bar open, the target is open-to-open.
- Test a **grid of horizons**: `h ∈ {1, 2, 5, 10, 21, 63}` bars. Never a single horizon.
- Overlapping forward windows create autocorrelated observations. Handled in §5.

### 2.2 Equities: residualise before you predict

Raw forward returns are dominated by market and sector moves. A feature that
accidentally proxies for sector membership will show strong IC while carrying no
tradeable information. So the target is the **residual** return:

```
r_resid(i,t,h) = r(i,t,h) - Σ_k β(i,k) · F(k,t,h)
```

Minimum viable factor set `F`: market, sector dummies, size, and (if available)
value and momentum. Betas estimated on a trailing window (e.g. 252 days), strictly
out of sample relative to `t`.

This is where market-neutrality actually originates — in the target definition, not
in a later hedging step. Getting this right is more important than the model that
consumes it.

### 2.3 Futures: volatility-normalise before you compare

The equivalent problem in futures is scale, not sector. A 1% move in a rates contract
and a 1% move in natural gas are not comparable events. Cross-sectional ranking on raw
returns just ranks instruments by volatility.

```
r_norm(i,t,h) = r(i,t,h) / σ(i,t)
```

where `σ(i,t)` is a trailing volatility estimate (EWMA, 32-day half-life is a
reasonable default, computed strictly on data up to `t`). Everything downstream —
features, returns, positions — lives in volatility-normalised space.

Then neutralise by **asset class** (equity index, rates, FX, energy, metals, ags).
The energy complex co-moves almost as tightly as an equity sector; without
neutralisation your "cross-sectional" signal is a levered bet on crude.

### 2.4 Futures: continuous series construction (the main trap)

Features are computed on a **back-adjusted continuous series**; P&L is computed on
**individual contracts**. Mixing these up is the most common silent error in futures
research.

- **Roll schedule:** roll on volume or open-interest crossover, not a fixed calendar
  date. Record the roll dates in a table and version it — the roll schedule is a
  research parameter and changing it changes your results.
- **Adjustment method:** panama (difference) adjustment keeps return series clean but
  can drive prices negative far back in history; ratio adjustment keeps prices positive
  but distorts absolute levels. Pick one, document why, and never mix them within a
  study. Difference adjustment is the safer default for return-based work.
- **Never compute a percentage return across a roll boundary on the unadjusted series.**
  The jump is a contract change, not a market move.
- **Roll yield is a feature, not noise.** The spread between the front and next contract
  is the carry signal (§9.2). Do not adjust it away and then go looking for it elsewhere.

---

## 3. Feature construction and standardisation

Order of operations, per timestamp:

1. **Compute** the raw feature using only data up to `t`.
2. **Winsorise** at ±3 (or 1st/99th percentile) to stop one outlier owning the result.
3. **Standardise cross-sectionally**: z-score or rank-transform across the universe at
   that timestamp. Rank is more robust; z-score preserves magnitude information.
   Test both — the difference is informative about whether your signal lives in the
   tails or in the ordering.
4. **Neutralise** against sector (equities) or asset class (futures), and against any
   factor you do not want the feature to proxy for. Practically: regress the
   standardised feature on the dummies and keep the residual.
5. **Re-standardise** after neutralisation.

Steps 2–5 matter more than the choice of model that eventually consumes the feature.
Most "model choice" debates in low signal-to-noise settings are actually
standardisation debates in disguise.

---

## 4. Universe construction

The universe is a research parameter with as much influence as any feature. Fix it
before testing and record it.

**Equities**
- Point-in-time index membership. If you use today's S&P 500 constituents over ten
  years of history you have built a survivorship-biased backtest and every result is
  void.
- Liquidity filter: minimum 20-day median dollar volume, minimum price (to exclude
  sub-$5 names where the tick is a large fraction of the spread).
- Record the universe size per date. A feature whose IC comes entirely from the
  smallest, least liquid decile is not tradeable.

**Futures**
- 20–40 liquid contracts is the realistic ceiling. Balance across asset classes so no
  one sector dominates the cross-section.
- Liquidity filter on volume and open interest in the front contract.
- Include dead markets and delisted contracts if you can get them. Their absence is
  the futures form of survivorship bias, though it bites far less hard than in equities.

---

## 5. Evaluating a feature

### 5.1 Cross-sectional IC (the primary test)

For each timestamp `t` with `N_t` instruments:

```python
ic_t = spearmanr(f[:, t], r_fwd[:, t, h]).correlation
```

Giving an IC time series. Report:

- `mean(IC)` — the effect size. Equities: 0.02–0.05 is a real feature. Futures: noisier
  per-period because `N` is small, so judge on the t-stat and the decay curve.
- `std(IC)` — stability.
- **IC t-stat** = `mean(IC) / std(IC) × sqrt(T)`.
- **IC autocorrelation** — high autocorrelation means fewer independent observations
  than `T` suggests, and the naive t-stat is optimistic.
- **Hit rate** — fraction of periods with positive IC. A feature with mean IC 0.03 and a
  55% hit rate is very different from one with mean IC 0.03 driven by three quarters.

**Overlapping windows:** for `h > 1` the IC series is autocorrelated by construction and
the naive t-stat is inflated by roughly `sqrt(h)`. Fix by either sampling every `h`-th
timestamp, or applying Newey–West with lag `h`, or block-bootstrapping the IC series with
block length `≥ 2h`. The block bootstrap already exists in `analytics/` — reuse it and
report a confidence interval rather than a point estimate.

**`N` too small:** below roughly `N = 10` per timestamp, cross-sectional IC is too noisy
to interpret. This is why BTC/ETH alone cannot be studied this way, and why the futures
cross-section (N ≈ 30) needs long history and should be supported by the time-series
tests in §5.2.

### 5.2 Time-series IC (futures, single instruments)

For instruments studied individually, or when `N` is too small:

```python
ic_i = spearmanr(f[i, :], r_fwd[i, :, h]).correlation
```

One IC per instrument. Then examine the **distribution of IC across instruments**. The
question is not "is the mean positive" but "is it positive for most instruments". A
feature that works on 26 of 30 contracts is a real effect. One that works on 4 with a
large mean is a story about those 4.

This pooled-instrument view is the futures analogue of a large equity cross-section, and
it is how the published futures literature (TSMOM, carry) actually establishes its results.

### 5.3 Quantile bucket analysis (always run this)

Sort into 5 or 10 buckets by feature value at each timestamp, compute mean and median
forward return per bucket.

Check:
- **Monotonicity** across buckets. This is a much stronger claim than a non-zero
  correlation and much harder to fake. A U-shape usually means the feature is proxying
  for volatility.
- **Top-minus-bottom spread**, with a standard error.
- **Symmetry.** If all the information is in the bottom bucket, you have a short-side
  signal, which has different capacity and borrow implications in equities and none in
  futures.
- **Per-year stability.** Print the spread by calendar year. One dominant year is the
  single most common way a feature dies in production.

**Critical:** run this on **every bar**, not only on bars where a trade would have
triggered. Conditioning on entry bakes the entry rule into the sample and you end up
measuring feature-plus-rule again. Unconditional analysis over the full panel is what
makes features comparable to one another.

### 5.4 IC decay curve

Plot mean IC against `h`. This is the most operationally useful single chart in the
protocol:

- **Monotonic decay from h=1** → short-horizon signal, high turnover, cost-sensitive.
- **Peak at h=5–20 then decay** → the natural holding period is the peak.
- **Flat or rising out to h=63** → slow signal, low turnover, likely a risk premium.
- **No structure at any h** → kill it.

The holding period is read off this curve. It is not a parameter to be optimised later.

### 5.5 Turnover and cost sensitivity

Before any strategy exists you can already estimate whether the feature can survive costs:

- **Feature autocorrelation** at lag `h` is a direct turnover proxy. Autocorrelation 0.95
  means a slow, cheap signal; 0.2 means you will trade constantly.
- **Break-even cost**: top-minus-bottom spread per period ÷ turnover per period, expressed
  in bps. Compare against the existing `CostStack` assumptions.
- A feature whose break-even cost is within 2× of your realistic all-in cost is not a
  feature. It is a cost model with extra steps.

### 5.6 Orthogonality (the admission test)

A new feature earns its place only by adding information the library does not already have.

- **Correlation matrix** of all standardised features, cross-sectionally, averaged over time.
  Pairwise |ρ| > 0.7 means you likely have one feature, not two.
- **Incremental IC**: regress the new feature on all existing features cross-sectionally,
  take the residual, re-standardise, and compute its IC. If incremental IC is near zero,
  the feature is a repackaging of something you already have.
- **Combined IC uplift**: does the combined forecast's IC actually improve when the feature
  is added? Report before and after.

---

## 6. Multiplicity accounting and the trial budget

Everything above is fast, which means it is easy to run hundreds of tests. Without
accounting, the best of 200 tests is guaranteed to look good.

### 6.1 The arithmetic that motivates everything else

The standard error of a Sharpe estimate over `T` years is approximately `1/sqrt(T)`. On a
10-year sample that is **~0.32**.

Given `n` candidate configurations with *zero* true edge, the expected best in-sample Sharpe
among them is approximately `σ_SR × sqrt(2 · ln n)`:

| Configurations tried | Expected best Sharpe from pure noise (10y) | (45y sample) |
|---|---|---|
| 10 | 0.69 | 0.36 |
| 100 | 0.97 | 0.51 |
| 1,000 | 1.19 | 0.63 |
| 10,000 | 1.37 | 0.73 |

A three-parameter sweep at ten values each is 1,000 configurations. **That sweep will return
a ~1.2 Sharpe from a strategy with no edge at all**, and it will look convincing. This is not
a caution about sloppiness; it is the expected output of the procedure.

Two consequences:

- On a 10-year sample, a swept result must clear roughly 1.2 before it is even *interesting*,
  and clearing it is still not evidence.
- Extending the sample to 45 years roughly halves every figure in that table. That is the
  statistical argument for the data expansion, in one line.

This is the logic the Deflated Sharpe Ratio formalises, which is why the trial count `n` is
an **input** to it. Untracked `n` means no DSR, which means eyeballing.

### 6.2 Mandatory practice

1. **Pre-register.** Before running anything: write the feature definition, the mechanism
   (§9.1), the predicted sign, and the horizon you expect it to work at. A feature that
   works with the opposite sign to the mechanism is a red flag, not a discovery.
2. **Set a trial budget in advance.** Decide and record it: *"this study gets 25 trials."*
   If the budget is blown, record the real number and accept the harsher discount. Never
   quietly reset the counter.
3. **Register every test.** A CSV appended to on every run: timestamp, feature name,
   universe, horizon, sign predicted, IC, t-stat, trial index, verdict. Including —
   especially — the abandoned ones. This file is a portfolio asset in its own right.
4. **Apply a correction.** Benjamini–Hochberg FDR across the family of tests in a study.
   Deflated Sharpe Ratio at the *recorded* `n` when reporting any strategy-level result.
5. **Sign discipline.** If you flip the sign after seeing the result, that is two tests,
   and the feature no longer has a mechanism.
6. **Count the parameters you do not think of as parameters.** Universe selection, start
   date, rebalance frequency, volatility target, cost assumptions, roll rule, outlier
   handling. These are researcher degrees of freedom and they multiply into `n` exactly
   like sweep points do. A meticulously counted 3×10 grid means nothing if four universes
   and two roll conventions went unrecorded.
7. **Holdout.** Hold out a block of history and touch it once, at the end of a research
   programme, never during. If you touch it twice, it is training data.

**Rule of thumb:** with `n` tests, a t-stat of 2.0 means nothing. Harvey, Liu & Zhu argue
the threshold for a newly claimed factor should be closer to 3.0. Adopt 3.0 as the
admission threshold and treat anything between 2 and 3 as "interesting, retest on new data".

---

## 7. Parameter parsimony — spending fewer trials

§6 measures the damage. This section reduces it. The cheapest way to stop burning sample is
to fit less, and most of the techniques below cost nothing and improve live results.

**1. Global parameters, never per-instrument.** Forty contracts × three parameters is 120
fitted numbers versus three. The true optimal lookback almost certainly does not differ
meaningfully between ES and CL, and the differences you would estimate are noise. Worth
running *once* as a diagnostic — fit globally, fit per-instrument, compare out-of-sample.
Per-instrument reliably loses; having that result in the repo is good evidence.

**2. Ensemble lookbacks rather than selecting one.** Averaging signals from 20/60/120-day
windows costs **zero selection trials**, because nothing was chosen. It is also better on the
merits: the right lookback is genuinely unknown, and averaging over an uncertain parameter is
the correct response to that uncertainty rather than a compromise. Different speeds fire at
different times, so there is a diversification benefit too. Costs: slightly higher turnover,
and dilution if one speed is truly dead.

**3. Literature values as priors.** A published lookback costs nothing and is defensible in
a writeup. "Parameters from Moskowitz, Ooi & Pedersen" is a stronger sentence than "47 days
worked best."

**4. Plateaus, not peaks.** "Positive across lookbacks from 20 to 120 days" is a far weaker
claim than "the optimum is 47", and weak claims are cheap. If the surface shows a spike
surrounded by a cliff, that is noise. If a broad region works, take its centre — not the
peak within it.

**5. Replace thresholds with continuous forecasts.** The highest-value item here. Entry
z-score, exit z-score and stop distance are three fitted parameters. A continuous forecast
scaled to a volatility target has none: position size is proportional to signal strength and
you are always in the market at some size. It deletes an entire family of parameters and
tends to improve out-of-sample results. Directly applicable to z-score-based spread work.

**6. Shrink toward equal weights.** Optimised combination weights fitted on 10 years reliably
underperform equal weights out of sample. At this sample size, 1/N across features is close
to unbeatable. Optimise only after demonstrating the optimiser beats 1/N out-of-sample — and
count that demonstration as a trial.

**7. Prefer fewer, better-motivated candidates.** A mechanism-filtered shortlist of 15
features tested once each is a vastly better use of a 10-year sample than 2,000 sweep points.
The mechanism filter in §9.1 is, ultimately, a trial-budget device.

---

## 8. Validation: purging, embargo, CPCV and PBO

Standard cross-validation is invalid on this data for three distinct reasons, which are
often conflated:

1. **Shuffling destroys time order** — the model sees the future. Walk-forward already
   fixes this.
2. **Overlapping labels leak.** If the label is "return over the next 20 days", the labels
   at `t` and `t+1` share 19 days of outcome. Put one in train and the other in test and the
   training set contains the test set's answer. No shuffling required — the leak is in the
   label construction.
3. **Serial correlation in features.** Even with non-overlapping labels, features at `t` and
   `t+1` are near-identical, so observations either side of a split boundary are not
   independent.

### 8.1 Purging and embargo

**Purging** addresses (2). For a test block spanning `[t_start, t_end]`, remove from
*training* every observation whose label interval `[t_i, t_i + h]` intersects that span. In
practice this drops roughly `h` bars either side of each boundary.

**Embargo** addresses (3). Purging handles label overlap but not residual correlation in
features and errors immediately after the test block, so additionally drop a buffer of
observations *following* each test set from training. López de Prado suggests ~1% of the
sample; a practical rule is embargo ≈ 1–2× the label horizon, verified by checking that
model residual autocorrelation has decayed across the gap.

Both are cheap. Omitting them produces a reassuring number that means nothing, which is
worse than no number at all.

### 8.2 Purged k-fold and CPCV

**Purged k-fold:** split into `N` contiguous, non-shuffled groups; test on one, train on the
rest — *including groups that come after the test group*.

That last part looks like cheating and is not, but it does mean something specific:

> **CV measures generalisation** — does this configuration work on data it was not fitted to?
> **Walk-forward measures deployability** — would this have worked live, using only past data?

Both are legitimate and they are different questions. CPCV **sits beside** the existing
walk-forward harness; it does not replace it.

**CPCV** generalises this. With `N` groups, testing `k` at a time (`k ≥ 2`):

```
splits = C(N, k)
complete backtest paths = (k / N) × C(N, k)
```

| N | k | Splits | Paths |
|---|---|---|---|
| 6 | 2 | 15 | 5 |
| 8 | 2 | 28 | 7 |
| 10 | 2 | 45 | 9 |
| 12 | 2 | 66 | 11 |

Each **path** is a full-length backtest over the entire history, assembled from blocks that
were out-of-sample in their respective splits. The output is therefore a *distribution* of
performance rather than one number: report "Sharpe 0.9, IQR 0.5–1.3" instead of "Sharpe 0.9".
That is a large upgrade in honesty and precisely what a single holdout cannot provide.

**Settings.** On the current 10-year sample: `N = 6–8` (blocks of 15–20 months), `k = 2`,
embargo 1–3 months for a 20–60 day label. On the expanded sample: `N = 12–16`. Cost is
15–66 backtest runs per configuration, which is negligible.

### 8.3 Probability of Backtest Overfitting

A different tool in the same family. PBO derives from **Combinatorially Symmetric
Cross-Validation** and evaluates the *selection procedure*, not a single strategy — so it
requires a set of candidate configurations, which any parameter sweep already provides.

Mechanically: build a performance matrix (time × configuration), split time into `S` blocks,
and form all `C(S, S/2)` ways of partitioning into half train / half test. In each partition,
select the configuration ranked best in-sample and record its out-of-sample rank.

```
PBO = fraction of partitions where the in-sample winner ranked below the OOS median
```

- **PBO near 0** — selecting on in-sample performance has skill.
- **PBO > 0.5** — the selection procedure is worse than random; whatever was chosen is noise.

Two by-products are arguably more useful than the headline number:

- **Performance degradation.** Regress OOS Sharpe on IS Sharpe across configurations. A
  positive slope means in-sample performance carries information. A **negative slope** —
  common in practice — means the better a configuration looked, the worse it did, and the
  sweep should be discarded entirely.
- **Probability of loss** at the selected configuration.

### 8.4 Four limitations, stated honestly

1. **CPCV assumes enough stationarity that training on later data to predict earlier data is
   meaningful.** Under regime shifts that is a real assumption, not a formality. It is the
   price of the efficiency gain.
2. **Paths are not independent** — they share most of their training data. The spread across
   paths *understates* true uncertainty. Treat it as a lower bound on the error bar.
3. **CPCV does not fix multiple testing.** Running it across 500 configurations and picking
   the best is still overfitting, now better instrumented. §6 and §7 are the treatment;
   this section is the diagnosis.
4. **Path-dependent strategies do not decompose cleanly into blocks.** Stops, trailing exits
   and carried portfolio state do not survive being cut, producing edge effects at every
   boundary.

Point 4 maps directly onto the existing two-frame testing practice, which resolves it cleanly:

| Frame | Validation method |
|---|---|
| Path-invariant (signal) | **CPCV** — observations are genuinely separable |
| Path-variant (book) | **Walk-forward** — sequence and carried state matter |

Run both. Disagreement between them is informative: a signal that survives CPCV but fails
walk-forward usually means the trading logic is destroying the edge, not that the edge is absent.

---

## 9. Where candidate features come from

### 9.1 The mechanism filter

**If you cannot name the counterparty and the constraint that forces them to trade at a
price they do not like, do not test it.**

This filter exists because the search space of computable functions of price is infinite
and its base rate of real edge is approximately zero. The filter is a prior, and it is the
only thing that makes the search tractable. It should kill most candidates before they
cost you a test.

Write the mechanism down in the pre-registration. One or two sentences. If it cannot be
written, that is the answer.

### 9.2 Categories that survive, with futures examples

**Risk premia** — compensation for holding something uncomfortable. Persistent,
low-Sharpe, high-capacity. Not alpha, but an honest base layer.
- *Carry / roll yield*: front-to-next contract spread, volatility-normalised. The single
  most documented futures effect. Long backwardated, short contangoed.
- *Hedging pressure*: producers are structurally short commodity futures and pay to be.

**Slow information diffusion**
- *Time-series momentum*: own-return sign over 1/3/12 months. Documented across a century
  and every asset class.
- *Cross-sectional momentum*: 12-1 month return, ranked across the cross-section.
- *Lead-lag*: related contracts, or equity sector ETFs leading their constituents.
- *PEAD* (equities): drift after earnings surprise.

**Forced flow / structural constraint** — the highest-quality category, because the
constraint is public and the counterparty is price-insensitive by mandate.
- *Index roll windows*: the Goldman/Bloomberg commodity index roll periods are published
  in advance and involve large, price-insensitive flow.
- *Index rebalance* (equities): additions and deletions, announced ahead of effective date.
- *Month-end / quarter-end*: pension and risk-parity rebalancing flow.
- *Expiry and settlement*: cash-settled contract expiry auctions, options open interest
  clustering at strikes.
- *CTA trigger levels*: published trend-following methodologies imply estimable trigger
  prices; the flow is mechanical.

**Liquidity provision** — getting paid to absorb impatience.
- *Short-horizon reversal*: 1–5 day reversal after volume-confirmed moves.
- *Order flow imbalance*, where you have the data.

**Positioning / sentiment**
- *CFTC Commitments of Traders*: free, weekly, the futures analogue of sentiment data.
  **Lookahead trap:** the report reflects Tuesday's positions and is released Friday
  afternoon. Lag it by at least four calendar days, and verify against the release
  calendar rather than assuming.

**Term structure and volatility**
- *Curve slope and curvature* beyond the front spread.
- *Realised-vs-implied vol spread*, where options data is available.
- *Skew of realised returns*, cross-sectionally ranked.

### 9.3 Categories to be sceptical of by default

Chart patterns, indicator crossovers, Fibonacci levels, harmonic patterns, anything whose
justification is a picture. Price is the single most heavily mined dataset in existence.
Time-series momentum and short-horizon reversal are the real survivors from that family,
and both are published, low-Sharpe and capacity-constrained — not 0.5%-per-trade edges.

---

## 10. Common failure modes checklist

Run through this before believing any positive result.

- [ ] **Survivorship bias** — point-in-time universe membership, or the result is void.
- [ ] **Lookahead in fundamentals** — use as-reported data with the actual release date,
      not the restated figure stamped with the period end date.
- [ ] **Lookahead in weekly/monthly data** — COT, inventories, macro releases. Lag to the
      publication timestamp, not the reference date.
- [ ] **Roll contamination** — no returns computed across a roll on an unadjusted series.
- [ ] **Timezone / settlement alignment** — futures across exchanges do not settle at the
      same time. A feature built from misaligned closes can manufacture false lead-lag.
      This is a very easy way to discover a spectacular fake alpha.
- [ ] **Stale prices** — illiquid instruments with unchanged closes create artificial
      autocorrelation that looks exactly like predictability.
- [ ] **The result lives in one decile** — check the IC excluding the smallest/least liquid
      instruments.
- [ ] **The result lives in one year** — check per-year stability.
- [ ] **The result lives in one instrument** — check per-instrument IC distribution.
- [ ] **The result lives in 2008/2020** — check with crisis periods excluded.
- [ ] **Sign flipped after seeing the data** — count it as two tests, and be honest that
      the mechanism is now post-hoc.

---

## 11. Proposed implementation

New top-level layer, sibling to the existing six:

```
research/
    features/
        base.py            # Feature protocol: compute(data, t) -> panel
        registry.py        # Named feature registry + metadata (mechanism, sign, author date)
        price.py           # momentum, reversal, vol, skew
        carry.py           # term structure, roll yield
        flow.py            # COT, open interest, volume
        cross.py           # lead-lag, sector-relative
    targets.py             # forward returns, residualisation, vol-normalisation
    standardise.py         # winsorise, z-score, rank, neutralise
    evaluate.py            # IC series, t-stats, NW correction, bucket analysis
    decay.py               # IC decay curves across horizon grid
    orthogonality.py       # correlation matrix, incremental IC
    validation/
        splitters.py       # PurgedKFold, CombinatorialPurgedCV (sklearn-compatible)
        purge.py           # label-overlap purging + embargo, given a horizon
        paths.py           # assemble CPCV splits into complete backtest paths
        pbo.py             # CSCV: PBO, performance degradation slope, prob. of loss
        deflated.py        # Deflated Sharpe Ratio, takes recorded n as input
    registry_log.py        # append-only test log + trial budget counter
    report.py              # per-feature markdown/HTML tear-off
```

**Splitter design.** `CombinatorialPurgedCV(n_groups, k, horizon, embargo)` yields
`(train_idx, test_idx)` pairs with purging and embargo applied automatically from the label
horizon — so it is impossible to run an unpurged split by forgetting a flag. Keep the
interface sklearn-compatible so it drops into existing tooling. `paths.py` then stitches the
`(k/N)·C(N,k)` complete paths and returns a performance distribution rather than a scalar.

**Trial budget.** `registry_log.py` holds a budget per study, increments on every evaluation,
and surfaces the running count. `deflated.py` reads `n` from that log rather than taking it
as an argument, so the DSR cannot be computed against a flattering number.

**Feature protocol.** A feature is a pure function from a data panel and a timestamp to a
cross-section of numbers, with metadata attached: name, mechanism (free text, required),
predicted sign, expected horizon, data dependencies. The mechanism field being *required*
is a deliberate design choice — it makes the §9.1 filter structural rather than optional.

**Standard artefact per feature** (`research/reports/<feature>.md`):
1. Definition and mechanism, as pre-registered.
2. IC table across the horizon grid, with confidence intervals.
3. IC decay curve.
4. Bucket analysis: spread, monotonicity, per-year table.
5. Turnover proxy and break-even cost.
6. Correlation to existing library + incremental IC.
7. CPCV path distribution: median and IQR, not a point estimate.
8. Trial count consumed, and DSR at that count if a strategy-level number is quoted.
9. Verdict: **admit / reject / retest**, with a one-line reason.

**Admission criteria (pre-registered, to be met in full):**

| Criterion | Threshold |
|---|---|
| IC t-stat (after overlap correction) | ≥ 3.0 |
| Bucket monotonicity | no sign reversal in the interior buckets |
| Per-year stability | positive spread in ≥ 60% of years |
| Break-even cost | ≥ 3× modelled all-in cost |
| Incremental IC vs library | ≥ 50% of standalone IC |
| CPCV path distribution | ≥ 75% of paths positive |
| PBO (where a sweep was involved) | < 0.3 |
| Performance degradation slope | positive |
| Mechanism | stated in advance, sign matches prediction |
| Fitted parameters | as few as possible; ensembled or literature-sourced where available |

A feature failing any one of these is rejected or parked, not tuned until it passes.

---

## 12. Migration path for existing work

1. Build `research/` with targets, standardisation and IC evaluation. No new features yet.
2. **Port the signals already embedded in existing strategies into the feature library and
   re-evaluate them unconditionally.** Expect some to show IC near zero — which would mean
   the strategy results came from the exit logic, not the signal. That is a genuinely
   valuable finding and belongs in the writeup either way.
3. Establish the baseline library from the published effects in §9.2 — carry, TSMOM,
   cross-sectional momentum, short-term reversal. These should replicate. If they do not,
   the harness is broken, and finding that out on known-good signals is far cheaper than
   finding it out on a novel one.
4. Build `research/validation/` and the trial log. Wire CPCV into the path-invariant frame
   alongside the existing walk-forward harness for the path-variant frame (§8.4).
5. **Re-run any historical sweep result through PBO.** This is retrospective and slightly
   uncomfortable, but a negative performance-degradation slope on past work is exactly the
   thing worth knowing before more effort goes into it.
6. Only then start testing novel candidates, one pre-registered mechanism at a time, against
   a declared trial budget.

Step 3 is the part that is easy to skip and should not be. Replicating a known result is
the only way to validate the measuring instrument before you use it to measure something
unknown.

Step 5 is the uncomfortable one, and worth doing early rather than late.

---

## 13. What this is worth as a portfolio artefact

A strategy with a good Sharpe proves very little; anyone can produce one, and a reviewer's
first assumption is that it was mined. A feature library with IC decay curves, an
orthogonality matrix, an append-only test log with the failures still in it, and a holdout
that was touched once proves something much rarer: that the author understands why most
apparent edges are not real, and built the process that tells the difference.

Lead the README with the test log and the kills.
