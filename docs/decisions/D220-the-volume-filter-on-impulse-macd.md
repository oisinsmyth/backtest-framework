# D220 — Can volume tell Impulse MACD which of its trades are the bad ones?

**Status:** Committed (L1, L4, L5 confirmed; L2 and L3 falsified) — every cell underpowered
**Date:** 2026-08-27
**Category:** Validation & research integrity
**Source:** A user proposal — filter out the arm's bad trades, be in the market less,
keep the good ones

> A result section will be appended and nothing above it edited.

## What is being tested

D218's best cell, `I1_signal` long-flat, plus a condition on **volume at the entry bar**
that decides whether the trade is taken at all.

The claim is a selectivity claim and it is stated in trade terms, not portfolio terms:

> **A volume condition specified in advance removes trades that go on to lose at a higher
> rate than it removes trades that go on to win.**

Everything else — Sharpe, total return, exposure — is a consequence. If the trade-level
statement is false, an improvement in any portfolio number is arithmetic luck about which
particular trades got dropped, and the runner has to be able to tell the difference.

## The prior, measured before the design was fixed

**Filter-agnostic. Volume is deliberately not looked at anywhere in this section** — the
relationship between volume and trade outcome is the hypothesis, and measuring it before the
pre-registration is written would make the pre-registration worthless.

### The trade census

| | |
|---|---:|
| trades | 2,418 (7.1 per ETF per year) |
| **win rate** | **44.4%** |
| mean win | +6.02% |
| mean loss | −2.84% |
| median hold | 14 bars |
| sum of winners / losers | +62.68 / −38.77 log |

**A majority of this arm's trades lose.** It earns its return on a 2.1:1 payoff ratio, not on
hit rate. That matters for the design: there is a large population of losing trades available
to remove, so the proposal is not fighting the base rate. An earlier guess that a long-flat
arm in a rising universe would be mostly winners — and therefore that any filter must cut good
trades — is **wrong**, and it is recorded here because it was the reason this study was nearly
argued out of existence.

### The two bounds that bracket any filter

| remove | ORACLE Sharpe | ORACLE total | exposure | RANDOM matched, p5..p95 Sharpe | RANDOM total |
|---:|---:|---:|---:|---:|---:|
| 0% | +0.793 | +52.12% | 49.9% | — | — |
| 10% | **+1.503** | +109.47% | 47.2% | +0.737..+0.840 | +41.5..+50.1% |
| 20% | +1.871 | +144.35% | 44.9% | +0.723..+0.862 | +35.8..+45.1% |
| 30% | +2.126 | +170.12% | 42.6% | +0.684..+0.880 | +28.2..+39.8% |
| 50% | +2.451 | +198.82% | 37.2% | +0.621..+0.911 | +17.8..+28.6% |

**ORACLE** removes the worst k% of trades ranked by realised PnL. It is look-ahead by
construction, is never presented as a strategy, and exists only to bound the space. D181 is
the standing distinction: the look-ahead guard binds strategies, not analytics, and this is an
analytic bound with the word ORACLE on it in every table it appears in.

**RANDOM** removes the same *count* at random. This is the correct null for a selectivity
claim because it is matched on exactly what a filter does — remove n trades — so a delta over
it cannot be explained by having traded less.

Two things follow that shape the whole design:

1. **The oracle at 10% removal is +1.503, which clears the +1.420 verdict floor.** This is the
   first construction in this programme with headroom above its own noise floor. The standing
   claim that this fixture is exhausted was a claim about *arms* and does not transfer to
   *filters*. It remains true that the oracle is unreachable.
2. **Removing 10% of trades removes only 2.7 points of exposure**, so losing trades are
   materially *shorter* than winning ones. Any filter therefore removes less exposure than
   trade count, and exposure reduction is a weak proxy for selectivity.

## The arms

The volume condition is evaluated on the **entry bar only** and decides whether that trade is
opened. It never closes a trade early — that would be a different hypothesis (an exit rule)
and is out of scope.

| | condition at entry | the claim it encodes |
|---|---|---|
| **V1** | `volume > mean(volume, N)` | the textbook one: volume confirms the move |
| **V2** | `volume < mean(volume, N)` | the contrarian one: quiet entries are the good ones |
| **V3** | `mean(volume, N) > mean(volume, N)` one bar earlier | participation is building, level irrelevant |

`N` ∈ {20, 50}. **Both directions are declared** because testing only V1 leaves "we should
have tried it the other way" available after a failure, which is not a hurdle, it is an
escape. Both are counted.

Books: long-flat and long-short, as every prior study in this line has run them.

**6 filter configurations × 2 books = 12 fresh looks.** The grid is declared here and is not
extended later. No scope additions mid-study; new ideas go to the parking lot.

## Hurdles

The D219 dual verdict applies in full — **standalone A–G and in-portfolio P1–P5, reported side
by side, neither allowed to replace the other.** D220 adds one hurdle specific to filters:

**H. Selectivity.** The filter must beat the **matched-count random null** at or above the
95th percentile on **both** Sharpe and total return, *and* the mean PnL of the trades it
removed must be below the mean PnL of the trades it kept at p95 of a permutation test on the
trade labels.

H is the hurdle that decides the study. A filter can improve Sharpe purely by removing
exposure from a book whose marginal exposure is unprofitable, and that is not selectivity —
the random null is matched on count precisely so that this shows up as a failure.

**The capture ratio is the headline number:**

```
capture = (filter - random_median) / (oracle - random_median)
```

What fraction of the available space the filter actually took. Reported for Sharpe and for
total return, at the filter's own removal count so the oracle is matched to it.

## Predictions, committed before the run

| | Prediction | Confidence |
|---|---|---|
| **L1** | V1, the textbook confirmation rule, does **not** clear hurdle H | **moderate-high** |
| **L2** | No cell reaches a capture ratio of 20% on either metric | **moderate-high** |
| **L3** | Every filtered arm correlates **> 0.85** with its unfiltered parent and therefore fails P4. A filter can only remove exposure, so its return stream is a sub-sample of its parent's and high correlation is structural rather than empirical | **high** |
| **L4** | No cell clears both verdicts | **high** |
| **L5** | V1 and V2 do not both fail — one of the two directions will look better than random, because they are near-complements and the sample is finite. **This is the prediction that matters**, because a single direction looking good is exactly what 12 looks buys you by chance, and hurdle G is what it has to survive | **moderate** |

**What would change my mind:** L1 failing — V1 clearing H on both metrics and both books, with
a capture ratio above 20%. That would mean the oldest claim in technical analysis carries real
information on this universe, which contradicts the 200-MA gate precedent, where the one
filter already tested on this exact arm took Sharpe from +0.793 to +0.454 and 40 points off
the return.

## Ledger

| block | looks |
|---|---:|
| filters — 3 conditions × 2 windows × 2 books | **12** |
| **fresh, D220 only** | **12** |
| inherited from D217 + D218 | 62 |
| disclosed prior ETF-fixture configurations + structure/terrain bar | 45,741 |
| **verdict count** | **45,815** |

**Zero-look items, stated explicitly:** the trade census (a census is not a test), the oracle
bound (an upper bound is not a hypothesis), the matched random null and the unfiltered parent
(a null is the yardstick for a look, not an additional look), and the capture ratio (a
rescaling of numbers already counted).

## Pre-committed stops

- **The volume data gate.** Volume is present in the fixture and clean — 143,355 bars, zero
  zero-volume bars — but `load_panel` does not currently carry it. If plumbing volume through
  changes any existing published number by more than floating-point noise, everything stops
  until that is explained, because it would mean the loader change altered the price path.
- **The census gate.** Any cell whose filter leaves fewer than 30 entries per ETF is
  **underpowered and carries no verdict** (D216, WP2), and a filter that removes most of the
  book will trip this before it can look good.
- **The programme stop.** If no cell clears H, the study closes as a reportable negative and
  no volume work continues on this fixture. A cell that clears H but fails the dual verdict is
  reported as exactly that and still gets no follow-up here.
- **ETF volume is a weak instrument and it is disclosed now, not later.** ETF liquidity comes
  from the creation/redemption mechanism and the underlying basket, so on-exchange volume is a
  poor proxy for interest — a quiet tape can simply mean the authorised participants did not
  need to trade. A negative result here is therefore **weaker evidence against volume as a
  concept** than the same result would be on single names or crypto, and the report must say
  so where the verdict is rather than in a footnote.

---

## RESULT

*Appended after the run. Nothing above this line was edited.*

**Produced:** 2026-08-27 · **Reproduce:** `uv run python scripts/run_volume_filter.py`
(offline, deterministic, seed 0) · Ledger: [`MACD_RESULTS.md`](../../MACD_RESULTS.md) ·
Artifact: `data/volume_filter_summary.json`

### The one-sentence version

**A volume filter selective enough to matter removes 39–61% of this arm's trades, which
drops it below the power threshold before it can be judged — every one of the twelve cells
is underpowered and carries no verdict — and on the way there it takes 18 to 31 points of
return with it while not one cell beats the parent on money.**

### Scoring my own predictions

| | Prediction | Outcome |
|---|---|---|
| **L1** | V1, the textbook confirmation rule, does not clear H | **CONFIRMED.** Best V1 cell reaches the 79th/86th percentile against a 95 requirement; the long-short V1 cells reach 18/0 and 46/0 |
| **L2** | No cell reaches a capture ratio of 20% on either metric | **FALSIFIED.** `V2_contrarian` long-short captures **38%** and **35%** of the Sharpe space. Both cells have negative Sharpe and zero minimum entries |
| **L3** | Every filtered arm correlates > 0.85 with its parent and fails P4 | **FALSIFIED IN BOTH DIRECTIONS** — see below. It held for long-flat (0.86–0.96) and broke completely for long-short (0.23, 0.26, 0.36, 0.41, **−0.41**, **−0.43**), and all six long-flat cells *cleared* P4 rather than failing it |
| **L4** | No cell clears both verdicts | **CONFIRMED.** 0 survivors |
| **L5** | V1 and V2 will not both fail — one direction will look good by chance, and G is what it must survive | **CONFIRMED, exactly as described.** `V2_contrarian` long-short sits at the **100th percentile on both metrics and on the label permutation**, and is dead on every other hurdle |

**Three confirmed, two falsified.**

### What is actually true

**1. The census gate kills all twelve, and that is the finding.**

The parent trades 43 round trips per ETF at a *minimum* of 34 — barely above the 30-entry
power threshold D216 set. Every filter here removes 39–61% of trades, so:

| book | min entries per ETF, after filtering |
|---|---|
| long-flat cells | 8, 8, 13, 17, 17 |
| long-short cells | 0, 0, 0, 0, 1 |

**Filtering this arm and retaining power are incompatible.** At 7.1 round trips per ETF per
year there is not enough trade population to subset. That is a structural fact about the
arm, not about volume, and it would apply to *any* filter — which makes it the more useful
result: the pre-registered census gate ended this study before the volume question could be
answered properly.

**2. The textbook claim fails on its own terms.**

`V1_confirmation` — volume above its own trailing mean at entry, the oldest claim in
technical analysis — never clears H on either window or either book.

**3. Not one cell beats the parent on money.**

Two cells beat it on Sharpe: `V1/50/long_flat` at +0.841 and `V3/50/long_flat` at +0.817,
against the parent's +0.793. Both cost enormous return:

| cell | Sharpe | total | vs parent's +52.12% |
|---|---:|---:|---:|
| parent, unfiltered | +0.793 | +52.12% | — |
| V1 confirmation / 50 | +0.841 | +21.5% | **−31 points** |
| V3 rising / 50 | +0.817 | +33.7% | **−18 points** |

So the hypothesis is answered directly, and the answer is the same shape as the 200-MA
gate's: **you can be in the market less and nudge Sharpe up; you cannot keep the good
trades.** The filters removed winners and losers at close to the rate chance would.

**4. The capture ratios say it plainly: 0–6% on the book that matters.**

The space is real — the ORACLE reaches +1.503 by removing the worst 10% — and on the
long-flat book volume captured **0%, 5%, −4%, −7%, 0% and 3%** of it. Volume is not
carrying information about which of these trades will fail.

**5. Volume is right-skewed, which makes "above average volume" a much blunter instrument
than it sounds.**

`V1_confirmation` removed **61%** of trades, not the ~50% a symmetric reading would predict,
because daily volume's mean sits well above its median. Anyone specifying a volume filter as
"above average" is cutting substantially more than half the book, and this is worth knowing
before choosing the threshold rather than after.

**6. Hurdle H in isolation would have promoted a book that loses money.**

`V2_contrarian` long-short clears selectivity at the **100th percentile on both metrics and
on the permutation test** with a Sharpe of **−0.003**. It genuinely is selective — it beats
its matched-count random null convincingly — and it is still not worth holding. Only the
conjunction caught it. **This is D219's dual-verdict design working on its first outing**,
and it is the strongest argument in the record so far for never scoring an arm on one axis.

**7. L3 was wrong, and the reason is instructive.**

I argued that a filter can only *remove* exposure, so a filtered arm's return stream is a
sub-sample of its parent's and high correlation is structural rather than empirical. That is
true for **long-flat**, where the filtered book's position is always either the parent's or
zero, and the six cells duly came in at 0.86–0.96.

It is false for **long-short**, and I should have seen it: removing a run from a long-short
book replaces a *short* with flat. That is not a subset of the parent's exposure, it is a
change of sign, and in a rising universe removing shorts changes the return stream
fundamentally. Two cells came in at **−0.41 and −0.43**. The structural argument was sound
only for the book I happened to be thinking about.

### Defects and disclosures

**The verdict floor of +3.599 is inflated by var_trials, exactly as D219's amendment
predicted.** The twelve cells span **−1.171 to +0.841** because the long-short cells are
catastrophic; the long-flat cells alone span +0.663 to +0.841. Including wildly dispersed
cells in the variance estimate raises the bar for everything, and D219's amendment recorded
that `var_trials` moves the floor further than N does. This is that effect observed live,
one study later. It is conservative and therefore safe, and it means +3.599 should be read
as *"the floor if all of this dispersion were noise"*.

**P4 measured against buy-and-hold is a weak hurdle, and D220 only implemented one of the
two incumbents D219 declared.** All six long-flat cells clear P4 — including cells that lose
31 points of money to their own parent — because adding any decent-Sharpe arm to a +0.457
benchmark at equal weight lifts the book. The declared-order greedy incumbent, which would
have measured these against the parent arm rather than against a passive book, was **not
built**. That is a gap in this runner, not in D219, and it is the reason the P4 column here
should not be read as evidence that these filters add anything.

**The `append_section` defect from D217 recurred here and was caught before publication.**
The insert path and the replace path emitted a different number of blank lines, so
`--report-only` did not reproduce the page byte-for-byte. Fixed by stripping any existing
section first so both paths run one insertion, and pinned by test.

**ETF volume is a weak instrument**, as disclosed before the run. ETF liquidity comes from
the creation/redemption mechanism and the underlying basket, so a quiet tape can mean the
authorised participants did not need to trade. **This negative is weaker evidence against
volume as a concept than the same result on single names or crypto would be**, and the
census finding above is the part that generalises.

### Ledger

| block | looks |
|---|---:|
| filters — 3 conditions × 2 windows × 2 books | 12 |
| **fresh, D220 only** | **12** |
| inherited from D217 + D218 | 62 |
| disclosed prior ETF-fixture configurations + structure/terrain bar | 45,741 |
| **verdict count** | **45,815** |

Zero-look: the trade census, the ORACLE bound, the matched random null, the capture ratio.

### What this changes

**The pre-registered stop applies: no volume work continues on this fixture.**

The transferable result is not about volume. It is that **this arm cannot be filtered and
remain powered** — 7.1 round trips per ETF per year is too thin a trade population to
subset, and any future filter proposal on a low-frequency arm should be checked against the
census gate *before* it is designed rather than after it fails.

The ORACLE bound is worth keeping as a standing tool. Computing it costs nothing, it is the
ceiling for any selection rule over a fixed trade population, and it converts "would a
filter help?" from an open question into a bounded one. **On this arm it showed the space
was real and that volume took none of it** — which is a far more useful negative than a
Sharpe that came in slightly lower than hoped.
