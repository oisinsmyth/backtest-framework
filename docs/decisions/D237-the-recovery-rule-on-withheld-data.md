# D237 — The recovery rule on withheld data

**Status:** Pre-registered — committed BEFORE any withheld data is touched
**Date:** 2026-08-27
**Area:** Strategy research

---

## The rule

```
md_L, hist_L  from Impulse MACD (34, 9) computed on LOG prices        (D232's I1L)

position = 1  if  hist_L > 0  AND  md_L <= 0
           0  otherwise
```

Long-flat, `lag = 1`, equal-weighted across the universe, 1,000-bar warm-up, costs from
`per_side_bps`, dividend-adjusted, `rf = 4%` charged on the exposed fraction.

**In English:** buy an instrument that sits at or below its own channel and has started to climb
back; sell when it reaches the channel top, or when the climb stalls. Both exits fall out of the
level rule — neither was designed.

### Its provenance, stated plainly

**This rule was found post-hoc.** D234 pre-registered a percentage *activation* threshold, every
declared cell failed catastrophically (−86% to −110% selection quality), and the complement was
computed **on my own initiative** because the arithmetic forced it. It was disclosed and counted
as one post-hoc look. **It has never been pre-registered as a hypothesis with hurdles stated in
advance. This record is that.**

### The mined-fixture numbers — reference, not hurdles

| | excess Sharpe | CAGR | vol | max DD | exposure |
|---|---:|---:|---:|---:|---:|
| **recovery rule** | **+0.746** | 5.43% | 6.1% | −10.30% | 18.9% |
| buy and hold | +0.235 | 8.42% | 17.7% | −34.60% | 100% |
| **delta** | **+0.511** | | | | |

Supporting controls on mined data: **0 of 1,000 rotations beat it** (100th percentile), and an
independent cut — bucketing held bars by trailing 63-day return — put the lowest quintile at
+49.9% annualised against the highest at −2.4%, monotone.

Against that: the paired bootstrap interval was **−0.204 to +1.098**, containing zero, and
hurdle E fails at 9 entries per symbol.

---

## Three tests, and what each isolates

| | universe | period | isolates | live bars |
|---|---|---|---|---:|
| **T1** | **60 new ETFs** | 2015–2024 | **instruments** | 1,515 |
| **T2** | 60 new ETFs | 2025–2026 | both — confounded | 414 |
| **T3** | **the same 57** | 2025–2026 | **period** | 414 |

**T1 and T3 decompose the question.** T1 holds the period fixed and changes the instruments; T3
holds the instruments fixed and changes the period. **T2 changes both and is reported as
corroboration only — it carries no verdict**, because a failure there could not be attributed.

### Power, stated before the run rather than as an excuse after it

**T1 is properly powered** — 1,515 live bars, the same as the mined fixture.

**T3 and T2 are not.** 414 bars is 27% of the mined span, so standard errors scale by
**√(1515/414) ≈ 1.91**. The mined bootstrap interval on `arm − B&H` was already −0.204 to
+1.098; at 414 bars the equivalent interval is roughly **±2.5**.

> **A 414-bar test cannot detect a +0.5 Sharpe difference.** T3 is a **sanity check** — did the
> rule catastrophically break in a new regime — **not a confirmation.** Treating a T3 pass as
> evidence of anything beyond "it did not fall apart" would be a misreading, and this sentence
> exists so that it cannot be done later.

**Hurdle E fails on T2 and T3 by construction** — roughly 300 pooled entries, ~5 per symbol
against the 30 required. Stated now, not waived.

---

## Hurdles

- **H1 (carries the verdict).** `arm excess Sharpe > buy-and-hold excess Sharpe`, on the same
  fixture, same cost path, dividend-adjusted, `rf = 4%` on the exposed fraction.
- **H2.** Beat the **matched-count rotation null** at p95 — same exposure, same turnover, same
  holding-period distribution, pointed at the wrong bars. On mined data the rule was at the 100th
  percentile of 1,000.
- **H3 (the anti-triviality leg).** The delta over buy-and-hold must be **at least 25% of the
  mined delta**, i.e. **≥ +0.128**. Out-of-sample shrinkage of 30–70% is normal; 25% is a lenient
  floor that still rules out "technically positive and worth nothing."
- **E.** Reported. Passes on T1, fails on T2 and T3, as stated above.

---

## How each outcome will be read — declared now so it cannot be storied later

| T1 (instruments) | T3 (period) | reading |
|:--:|:--:|---|
| **pass** | **pass** | The strongest result this programme has produced. Still one span and one short forward window — **not proof**, and the next step would be more forward time, not promotion |
| **pass** | fail | **Instrument-general, period-specific.** The 2018–24 regime made it. Weak, and consistent with the +0.978 correlation between the two universes |
| fail | **pass** | **Period-general, instrument-specific** — fitted to those 57 names. Given T3's power, this combination is more likely noise than signal |
| **fail** | **fail** | **The rule does not generalise. Closed.** |

**T1 is the verdict-carrier.** T3 can only downgrade a T1 pass or fail to rescue a T1 failure.

---

## Predictions

| | prediction | confidence |
|---|---|---|
| **T1a** | **T1 passes H1** — the arm beats buy-and-hold on the new instruments | **moderate** |
| **T1b** | **The effect shrinks** — T1's delta is smaller than the mined +0.511 | **high** |
| **T1c** | **T1 passes H2**, the rotation null, as it did at the 100th percentile on mined data | **moderate** |
| **T3a** | **T3 is inconclusive** — its interval spans zero by a wide margin whatever the point estimate | **high** |
| **T3b** | **T3's point estimate is positive** but fails H3's +0.128 floor | **low-moderate** |

**T1a is the one that matters, and moderate is honest.** The two universes correlate at +0.978,
so if the rule works at all it should transfer; the risk is that it was fitted to the *names* in
the mined 57 rather than to anything general.

---

## The stop

**If T1 fails H1, the rule is closed** — no variant, no re-cut, no third fixture. Ten studies of
modification have already been spent on this arm's family.

**If T1 passes, nothing is promoted either.** It becomes a rule with one clean out-of-sample
result on a correlated universe, and the next step is **more forward time** — which accumulates
for free — not a decision to trade it.

**The 2025–2026 window is spent by this record.** It cannot be reused, and any future forward
test needs months that have not yet happened.

---

## Ledger

| count | N |
|---|---:|
| fresh — 1 rule × 3 fixtures | **3** |
| + D234–D236's 19 | 22 |
| + disclosed ETF prior | **45,825** |

---

## Reuse — D212 is binding

| need | reuse | from |
|---|---|---|
| the rule, `md_L`/`hist_L` | `base_masks`, `hold_book` | `run_stops_targets.py` |
| scoring, rf-on-exposure, rotation null | `score`, `rotation_nulls`, `_excess_sharpe` | `run_exposure_dial.py` |
| paired bootstrap | `paired_block_bootstrap` | `run_jerk_rung.py` |
| panel loading, costs, buy-and-hold | `load_panel`, `portfolio_log_returns` | `run_macd_ladder.py` |
| the fixture builder and split adjustment | `split_factor_at`, `do_build`'s pattern | `fetch_etf_holdout.py` |

**Written fresh:** the two forward fixtures only. The rule itself is untouched from D234 — **if
so much as a parameter moves between the mined run and this one, the test is void**, and that is
the single thing this record exists to guarantee.

---

## RESULT

*Appended after the run. Nothing above this line was edited.*

**Produced:** 2026-08-27 · `uv run python scripts/run_withheld_test.py` · Page:
[`WITHHELD_TEST_RESULTS.md`](../results/WITHHELD_TEST_RESULTS.md)

### The one-sentence version

**T1 passes all three hurdles and the effect did not shrink — the first genuine out-of-sample
pass this programme has produced. T3 fails, because 2025–26 was a melt-up the rule could not
participate in at 15.6% exposure.**

### The three tests

| | isolates | bars | arm | B&H | **Δ** | boot p05 | boot p95 | H1 | H2 | H3 |
|---|---|---:|---:|---:|---:|---:|---:|:--:|:--:|:--:|
| **T1** | **instruments** | 1,515 | **+0.779** | +0.230 | **+0.549** | −0.152 | +1.158 | **✓** | **✓** | **✓** |
| T2 | both (confounded) | 413 | +1.016 | +1.146 | −0.130 | −1.346 | +0.465 | ✗ | ✗ | ✗ |
| **T3** | **period** | 413 | +0.898 | **+1.234** | **−0.336** | −1.475 | +0.418 | ✗ | ✗ | ✗ |

*H3 floor +0.128, being 25% of the mined delta of +0.511.*

| | CAGR | vol | max DD | exposure |
|---|---:|---:|---:|---:|
| T1 arm | 5.49% | 5.9% | −9.04% | 19.7% |
| T1 B&H | 8.34% | 17.8% | −37.92% | 100% |
| T3 arm | 3.64% | 3.3% | −2.94% | 15.6% |
| **T3 B&H** | **23.72%** | 14.1% | −14.06% | 100% |

### T1 — the pass, and it is a real one

**On 60 ETFs sharing zero tickers with the training set, the rule reproduced itself almost
exactly:**

| | mined | **T1 (withheld instruments)** |
|---|---:|---:|
| excess Sharpe | +0.746 | **+0.779** |
| exposure | 18.9% | 19.7% |
| max drawdown | −10.30% | −9.04% |
| **delta over B&H** | **+0.511** | **+0.549** |

**The effect did not shrink — it grew slightly**, which falsifies T1b and is the single most
surprising number here. Out-of-sample results normally regress. And it cleared **H2**, the
matched-count rotation null, as it had at the 100th percentile on mined data.

**The honest discount, stated in the pre-registration and unchanged by the result:** the two
universes correlate at **+0.978**. T1 shows the rule is not fitted to the particular 57 tickers.
It does *not* show independence from the 2018–24 market, because both fixtures live in it.

### T3 — the failure, and what it actually says

**The rule did not break. The benchmark had an exceptional run.**

The arm's own forward performance was **better than its mined performance** — +0.898 excess
Sharpe against +0.746, at a −2.94% maximum drawdown. What changed is that buy-and-hold made
**23.72% a year** at +1.234 excess Sharpe. **A book 15.6% exposed cannot keep pace with a 24%
melt-up**, and Sharpe is already the volatility-matched comparison, so leverage does not close it.

**The declared reading stands** — `(T1 pass, T3 fail)` was pre-registered as *"instrument-general,
period-specific."* That verdict is not rewritten here. The additional fact worth recording is
that the mechanism is not deterioration but **benchmark outperformance**, and those are different
failure modes with different implications.

**And T3 cannot distinguish anything.** Its interval is **−1.475 to +0.418**, spanning 1.9 Sharpe
points. T3a predicted exactly this. **A 413-bar test was always a sanity check**, and what it
reports is that the rule kept working on its own terms in a regime it had never seen.

### Scoring

| | prediction | outcome |
|---|---|---|
| **T1a** | T1 passes H1 | **CONFIRMED** |
| **T1b** | the effect shrinks out-of-sample | **FALSIFIED.** +0.549 against +0.511 — it grew |
| **T1c** | T1 passes H2, the rotation null | **CONFIRMED** |
| **T3a** | T3 is inconclusive, interval spanning zero widely | **CONFIRMED.** −1.475 to +0.418 |
| **T3b** | T3's point estimate is positive but below the floor | **FALSIFIED.** It is negative, −0.336 |

**Three of five.**

### Hurdle E fails everywhere, including T1

Minimum entries per symbol: **9 (T1), 1 (T2), 2 (T3)** against 30 required. Declared in advance
for T2 and T3; T1's failure matches the mined fixture's 9 and was not flagged.

**This is a real limitation, not a technicality.** Nine entries per symbol over six years means
the per-symbol evidence is thin, and the result rests entirely on pooling across a universe whose
members are correlated at ~0.4. It is the weakest part of the case.

### What this changes — and the stop, applied as written

**The rule is not closed.** T1 passed, so D237's closure condition did not trigger.

**And nothing is promoted**, exactly as pre-committed: *"it becomes a rule with one clean
out-of-sample result on a correlated universe, and the next step is more forward time — not a
decision to trade it."*

What the programme now has, stated at its real strength:

- **A rule that survived a genuine instrument holdout without shrinking**, cleared a matched-count
  rotation null on both fixtures, and carries an independent corroborating measurement (the
  trailing-63-day cut).
- **Whose every bootstrap interval still contains zero**, whose per-symbol sample fails hurdle E,
  and which **lost to buy-and-hold over the only forward period ever tested.**

**The 2025–2026 window is spent.** Any further forward test needs months that have not happened
yet — roughly a year before another 250 bars exist.

### Ledger

| count | N |
|---|---:|
| fresh — 1 rule × 3 fixtures | 3 |
| + D234–D236's 19 | 22 |
| + disclosed ETF prior | **45,825** |
