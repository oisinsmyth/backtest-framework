# D264 — The intraday short on single names

**Status:** **SCREENED AND CLOSED on this sample** — zero of twelve short cells cleared.
**Date:** 2026-09-01
**Area:** Strategy research · **personal track** ([BOOK.md](../BOOK.md)), R12 personal standards

**Everything above the RESULT heading was committed in `56c6156`, BEFORE the fixture existed and
before anything was scored.** The result was appended afterwards and nothing above it was edited —
`git show 56c6156` is the check, not this sentence.

**The ledger moves by 16 fresh cells. Nothing is admitted to any book by this record.**

---

## What this is, and the authority for running it at all

A **cross-screen under [R12](../RULES.md#r12)** of [D247](D247-the-short-side-at-fifteen-minutes.md)'s
intraday short construction onto a **different universe**: eight US single names at fifteen minutes,
instead of fifty-seven ETFs.

**Three separate records license it, and none of them is being stretched:**

1. **D247's own stop, verbatim:** *"If everything fails, the intraday short question is not closed
   — **only these two estimators at these bar counts are.** A rule designed for the intraday
   horizon is a separate pre-registration, and the overnight/intraday decomposition above is the
   finding that would motivate it."*
2. **R12:** a `CLOSED` verdict is track-specific and **does not travel**; a candidate closed on one
   track is screened against the other's standards before it is discarded. This stays on the
   **personal** track throughout — the prop track's hurdle P is not applied and not relevant.
3. **[FINDINGS §9](../FINDINGS.md), which names this as the live question.** D256 closed shorts on
   single names *daily* and gave a reason that is a property of the **book**, not the instrument:

   > An equal-weighted book over 1,580 single names **IS a diversified basket.** Idiosyncratic
   > variance exists at the **name** level and averages away at the **book** level — the book holds
   > **76.5% of live names at once**. We rebuilt the very diversification the hypothesis identified
   > as the problem. **So the operative variable is not the instrument's listing status — it is how
   > many you hold at once.**
   >
   > **What is live now** is therefore a question of **construction**, not universe.

**This is not D256 re-run.** D256 held 1,580 names close-to-close. This holds **eight**, flat at
every session close. Both differences point the same way, and both were named as the live axis
before this record existed.

**What it is NOT:** it is not a new rule, not a parameter search, and not a candidate for S3 —
[D246](D246-the-search-protocol-for-s3.md)'s reserved cohort is **not touched** and its 8-cell
budget is **not spent**. Every constant below is frozen at the value D247 and D256 already ran.

---

## The one measurement that motivates it

D247's most informative number, and the only encouraging thing the short side of this programme
has produced:

| bars held by | annualised return of those bars |
|---|---:|
| ALL BARS | +9.02% |
| S1_short_**cont** (holds overnight) | **+4.72%** |
| S1_short_**intra** (flat at every close) | **−4.27%** |

**An 8.99-point swing, and D247 called it correctly:** *"It is the first construction in this
programme to isolate bars that actually fall."*

**It still lost, and it lost on arithmetic rather than on signal.** Turnover 334/yr, breakeven
**0.13 bp/side**, charged **~1.6 bp/side** — the cost was **twelve times** the gross edge.

**So the question this study asks is arithmetic before it is signal:**

> A single name has more idiosyncratic variance than an ETF ([FINDINGS §2](../FINDINGS.md)), which
> should raise the gross edge. It also has a wider spread, which raises the cost. **Does the edge
> rise faster than the cost, or does the cost wall move out to meet it?**

Idiosyncratic vol runs ~2–3× ETF vol; single-name costs perhaps 1.5–3×. **It is close to a wash,
which is exactly why it needs measuring rather than assuming.** And [FINDINGS §1b](../FINDINGS.md)
supplies the reason it may not be a wash in the direction anyone wants: a short pays a variance tax
scaling with `sigma^2`, so the same variance that carries the edge also taxes it — **and the tax is
quadratic while the edge is not.**

---

## THE FIXTURE, AND THE LIMIT THAT CANNOT BE ENGINEERED AWAY

`data/fixtures/single_name_intraday_15m_raw.csv.gz` — 8 symbols, 15-minute bars, regular hours
(26/session, 09:30–15:45 stamped at the interval **open**), **2018-01-02 → 2026-08-26**.

**The span is D247's span exactly**, so the ETF result is a **comparison** and not an analogy.

### The sample was chosen by a rule fixed before the data existed

`scripts/select_single_name_intraday.py`, run once against the committed **daily** fixture over
**2013-01-02 … 2017-12-29** — a window **disjoint from the test span**, so no statistic that picked
a name has seen a bar this study scores.

Survivor · ≥95% coverage · median dollar volume ≥ $50M · then stratified on realised volatility:
the **4 lowest-vol of the top 40 by dollar volume**, and the **4 highest-vol clearing the liquidity
floor**.

| stratum | names | ann. vol, 2013–17 |
|---|---|---|
| **LOW** | PG, LMT, PM, MO | 14.1% – 16.2% |
| **HIGH** | CLF, SM, YELP, RH | 53.7% – 78.0% |

**The 5.5× spread is the design, not an accident.** FINDINGS §1b and §2 make opposite predictions
about volatility — it is where the edge lives *and* where the tax bites — so the sample deliberately
spans the axis to find out which one binds. Volatility is a **declared design axis computed on data
the study never scores**, not a fitted parameter, and it is not swept.

**Disclosed rather than defended:** sorting the liquid pool on volatility produced defensive
mega-caps at one end (staples, defense, tobacco) and cyclicals/small-growth at the other. **The vol
axis is confounded with sector**, unavoidably, because that is what sorting on volatility does. Any
stratum-level reading carries it.

### SURVIVORSHIP — the limit, its size, and its direction

**MEASURED 2026-09-01, five probe calls.** `TIME_SERIES_INTRADAY` serves **nothing** for a delisted
ticker on this tier:

| | |
|---|---|
| AAPL 2022-06 | **546 bars, 21 sessions, 26.0/session** — the control, works |
| TWTR 2022-06 · FRC 2023-03 · SIVB 2023-02 · AABA 2019-06 | **155 bytes, `Invalid API call`**, four for four |

`TIME_SERIES_DAILY_ADJUSTED` **does** serve dead names — that is how D252 built a 35.7%-dead daily
fixture. **The intraday endpoint does not.** This is a provider limit, not a design choice.

**Its size: 496 of the 1,192 names trading in 2013–2017 are not survivors — 41.6% of the cohort is
unreachable at this frequency.**

[D252](D252-the-dead-inclusive-us-single-name-universe.md) holds that for a short book survivorship
*"does not weaken the measurement, it removes the thing being measured."* **That statement was made
about a close-to-close book, and it does not transfer at full strength here** — but it does not
vanish either, and the difference must be stated rather than assumed:

- **What weakens it:** an intraday-flat book **never holds a delisting gap**, and for a collapsing
  name the gap is most of the fall. The payoff this construction is built to capture is the
  09:30→16:00 grind, which is the component survivorship damages least.
- **What survives:** the deleted cohort still contains the names with **sustained intraday
  decline**, which is precisely this rule's target. Deleting them removes real short profit.

**DIRECTION, DECLARED NOW SO IT CANNOT BE CHOSEN LATER: survivorship makes this sample
CONSERVATIVE for a short.** Therefore, and this is binding on how the result may be read:

> **A PASS is informative. A FAIL IS AMBIGUOUS and does NOT close the question** — it cannot
> separate "no edge" from "the edge was in the 41.6% the provider will not serve." Any closure
> written from a negative result must say so in those words.

### The other things wrong with the fixture, stated in advance

1. **Eight names is thin.** R10 applies with full force; effective independent instruments are
   reported beside every pooled table and the pooled trade count is **never** quoted alone.
2. **The calendar mismatch is inherited from D247 and is severe.** S1's 34-bar Impulse is **1.3
   sessions** here against seven weeks daily; S2's 252-bar regression is **9.8 sessions** against a
   year. These are the same estimators at a radically shorter horizon, and D247 concluded that
   *"15-minute sampling breaks both estimators in both directions."*
3. **The empty-bar rate is measured, not assumed** (D192), and is quoted from the fixture meta
   before any cell is read.
4. **Splits: the provider reports zero across all eight names in the span.** Not taken on trust —
   the build reports every residual session-boundary step above D226's **15%** and classifies it by
   D252's test (reverts → bad print; persists at volume → corporate action; corroborated → real).
   **`SPLITS` + `DIVIDENDS` do not cover spin-offs**: XLF's XLRE spin-off is a −18.3% step Alpha
   Vantage reports as zero splits (PICKUP.md).

---

## Part A — the anatomy, reported BEFORE any cell is scored

D250, D255 and D256's precedent, and [D244](D244-the-book-on-crypto.md)'s lesson that **a null can
be beaten or lost by drift structure alone**. None of this is a cell; all of it is reported first so
no null result can be interpreted without it.

1. **The drift decomposition, per stratum.** Overnight vs intraday annualised drift. **On the 57
   ETFs this was +8.59% overnight against −0.36% intraday**, and that 8.95-point split is the entire
   reason an intraday-flat short is worth testing. It is not assumed to hold here.
2. **What the shorted bars actually return** — D247's table, per arm, per holding, per stratum.
3. **`exposure × edge` for every cell, never the edge alone** ([FINDINGS §1a](../FINDINGS.md)):
   selectivity cannot create gross return, it only redistributes it.
4. **R10 concurrency** — mean/max names held, share of the sample, against a per-symbol-rotated book
   of identical exposure, plus **effective independent instruments**.
5. **The `sigma^2` tax, measured against its formula.** D253 predicted `−mu − sigma^2` and landed
   within 2.85 points on crypto. A `SHORT_ALL` benchmark is computed per stratum and compared to the
   prediction. **A short book that does not clearly beat `SHORT_ALL` has found nothing.**
6. **Empty-bar rate and incomplete-session rate**, from the fixture meta.

---

## Part B — the cells. Frozen constructions, no parameter varied.

Exactly as D247 ran them, exactly as D256 froze them. **No constant below is fitted, swept or
re-cut.**

```
S1_short   position = -1 if hist_L > 0 AND md_L <= 0        Impulse 34/9
S2_short   DOWNTREND := g_lo < 0 AND g_hi < 0               k=3, window 252,
           enter at onset, exit at age 63 or state end       age cap 63

holding    cont   = holds across session boundaries, pays borrow
           intra  = flat at every session close, pays no borrow
```

| | shorts | long controls |
|---|---:|---:|
| arms × holdings | 2 × 2 | 2 × 2 |
| strata | **LOW, HIGH, ALL** | ALL only |
| **cells** | **12** | **4** |

**16 fresh cells. Counted in full.**

**The long controls are controls, not candidates**, and D247's design requires them: without them a
short failure cannot be attributed to **direction** rather than to 15-minute sampling breaking the
estimator. They are run on ALL only, which is why the count is 16 and not 24 — stated here so the
economy is a declared choice and not a quiet one.

### Costs — charged in advance, and the breakeven is the real output

**The commission is DERIVED, not chosen.** `per_side_bps` already applies the IBKR schedule
per symbol from its own median close — `max(min($0.005/share × shares, 1% of notional), $1.00)` —
and adds a half-spread. That machinery is reused unchanged (D212). **Only the half-spread and the
borrow rate are assumptions, and only those two are set here.**

| | half-spread | borrow/yr | *ETF reference (D217/D247)* |
|---|---:|---:|---|
| **LOW** (PG LMT PM MO) | **1.5 bp** | **0.30%** | *1.0 bp, 1.0%* |
| **HIGH** (CLF SM YELP RH) | **4.5 bp** | **3.00%** | *1.0 bp, 1.0%* |

**Per-symbol notional is fixed at D247's own figure — $175,438** (`PRIMARY_CAPITAL / 57`) — rather
than fixing total capital. The commission-in-bps depends on notional *per position*, so holding it
constant is what makes this study's cost directly comparable to D247's instead of merely similar.
Total capital is therefore 8 × $175,438 = **$1.40M**, which is also a plausible personal-book size
for eight names, where $10M across eight would not be.

**Borrow is charged only across session boundaries**, prorated by the real calendar gap (D247's
model), so `intra` cells pay **zero** borrow — the honest model of a flat-at-close book, and it is
asserted in code rather than assumed.

**These four numbers are the weakest part of this design and are labelled as such.** They are stated
before the run and not swept. **Locate fees and SEC Rule 201 are NOT modelled**, and are named here
as an unpriced cost that runs *against* the short — the high stratum especially, where a falling
small-cap is exactly what becomes hard to borrow.

> **Because the charged figures are assumptions, the primary cost statistic is the BREAKEVEN
> bp/side, which is a property of the strategy and not of my spread guess.** Every cell reports it.
> A reader who disagrees with 2.0 and 5.0 can substitute their own and re-read the verdict without
> re-running anything.

### Hurdles — every leg computed, or the run fails loudly (R6)

| | standard |
|---|---|
| **H** | matched-count rotation null at **≥95th percentile on Sharpe AND money**, both legs ([R10](../RULES.md#r10) 2nd corollary). Rotation respects session structure |
| **V** | **positive net CAGR** after fees, financing and borrow. H is a skill test, V is a viability test; a cell clearing H alone is reported as a measurement, **never as a result** (D253) |
| **E** | ≥100 pooled entries **and** ≥30 per symbol |
| **K** | **breakeven bp/side ≥ the charged cost**, headroom ≥ 1.0× |
| **B** | paired bootstrap on the excess Sharpe, **p05 > 0**. Never optional (R6/D230) |
| **F** | **best-of-16 floor** (D228), one shared offset vector across all cells |

**A cell must clear H, V, E, K, B and F. All six.**

---

## Predictions, declared before the run

D263 proved the value of doing this: the largest number in its table had the **wrong sign**, and
only the advance declaration made that legible rather than reinterpretable.

| | prediction | confidence |
|---|---|---|
| **P-a** | **No short cell clears all six hurdles.** Base rate in this programme is roughly one in eight, and D247 failed the cost leg by 12× | **moderate-high** |
| **P-b** | **The `intra` cells hold bars with a LOWER annualised return than the `cont` cells, on both strata** — D247's 8.99-point swing reproduces in sign. This is the **mechanism** prediction and the one most worth being wrong about | **moderate-high** |
| **P-c** | **The HIGH stratum shows a larger gross edge AND a larger cost wall, and the cost wall wins** — breakeven bp/side does **not** rise as fast as the spread does | **moderate** |
| **P-d** | **`exposure × edge` is roughly invariant across strata**, per FINDINGS §1a — selectivity and volatility redistribute return rather than create it | **moderate** |

**P-c is the one that matters, and its falsification is the only result that justifies expanding the
sample.** If breakeven rises *faster* than the spread — if the high-vol stratum clears hurdle K where
the ETFs missed by 12× — then the cost wall that closed D247, D248 and most of the intraday
microstructure literature on this programme's cost arithmetic **moves**, and that is a finding about
the whole family rather than about eight names.

**P-a is registered so that a null result is a recorded outcome rather than a disappointment.**

---

## Stop

**If no short cell clears all six hurdles, the construction is closed ON THIS SAMPLE** — no
parameter sweep, no additional stratum, no third arm, no re-cut of the window, **no move to
5-minute bars**, and D246's reserved cohort is not touched. Committed here so *"the last reading
wasn't the right one"* cannot be pulled later.

**And the closure is bounded, in these words:** a negative closes **this construction on these eight
survivor names**. It does **not** close the intraday short as a question, for the two reasons already
stated above and fixed before the run — **the sample is survivor-only and the bias runs against the
short**, and **eight names is thin**. Per R12, a stop condition must name its track: this one names
**the personal track and this sample**, and travels no further.

**If a cell does clear, nothing is promoted.** Under [R8](../RULES.md#r8) it becomes a candidate
needing its own pre-registered out-of-sample test on names this study never touched — which requires
a fetch that has not been made.

---

## Ledger

| count | N |
|---|---:|
| fresh — 12 short cells + 4 long controls | **16** |
| + Part A anatomy (drift decomposition, held-bar returns, `SHORT_ALL` per stratum) | 23 |
| + carried from D263 | 45,886 |
| **total** | **45,909** |

**The anatomy is counted.** It is a search over the same data, and counting only the 16 scored cells
would understate it — D248's precedent, which counted the 13 that produced its hypothesis.

---

## Reuse — D212 is binding

`macd`, `pivots`, `signals`/`walk` for S2, `base_masks`/`hold_book` for S1, the rotation nulls, the
bootstrap, D247's `flatten_overnight`, `excess_intraday` session-boundary borrow charge and
`breakeven_bps` — **all committed and tested, all reused, none reimplemented.** The fetcher reuses
`fetch_etf_intraday.py`'s helpers for the same reason.

**Written fresh:** the per-stratum cost schedule, the stratum partitioning of the scorer, and the
`SHORT_ALL` per-stratum benchmark.

**R9 is binding on every table here:** any conditional cut uses the value the rule could have seen,
`z[t-1]` and not `z[t]`. The runner's `lag = 1` already enforces it; the anatomy scripts do not get
that protection for free and must be written to it.

---

## RESULT — CLOSED on this sample. Zero of twelve, and the arithmetic is the whole story.

`uv run python scripts/run_single_name_intraday.py` · `data/single_name_intraday_summary.json` ·
[`SINGLE_NAME_INTRADAY_RESULTS.md`](../results/SINGLE_NAME_INTRADAY_RESULTS.md) · seed 0, 1,000
rotations, 8 × 55,004 bars, 2,117 sessions, live 8.25 years.

**Zero of the 12 short cells clear all six hurdles.** The stop fires.

### The predictions, scored against what was declared

| | prediction | outcome |
|---|---|---|
| **P-a** | no short cell clears all six | **CONFIRMED** — 0 of 12 |
| **P-b** | `intra` holds lower-returning bars than `cont`, both strata | **CONFIRMED, 6 of 6**, and far larger than on ETFs |
| **P-c** | HIGH shows a bigger edge *and* a bigger cost wall, and the wall wins | **SPLIT — the mechanism clause is FALSIFIED; the conclusion clause holds** |
| **P-d** | `exposure × edge` roughly invariant across strata | **FALSIFIED** — it ranges −1.94% to +8.31% for one rule |

### P-b, and the mechanism is real

| | cont | intra | swing |
|---|---:|---:|---:|
| **HIGH S1** | +22.48% | **−28.87%** | **51.35 pts** |
| ALL S1 | +20.22% | −11.94% | 32.16 pts |
| LOW S1 | +18.11% | +7.86% | 10.25 pts |
| *ETF S1 — D247* | *+4.72%* | *−4.27%* | *8.99 pts* |

**−28.87%/yr is the most negative held-bar return this programme has produced**, against D247's
−4.27%. Flattening at the close isolates falling bars, it does so far more strongly on volatile
single names than on ETFs, and **it is not the reason the construction fails.**

### Why it fails, stated as an identity that closes exactly

**HIGH S1_short_intra, continuously-compounded %/yr** — log units, because these legs must add and
annualised percentages do not:

| | |
|---|---:|
| `exposure × edge` (linear, FINDINGS §1a) | **+8.31%** |
| − the `sigma^2` variance tax (FINDINGS §1b) | **−4.87%** |
| **= realisable gross** | **+3.43%** |
| − trading cost, 324 turns/yr at 6.42 bp/side | **−20.68%** |
| **= net** | **−17.24%** (= **−15.84%** CAGR) |

**It is both taxes, and the cost is the one that decides.** The variance tax takes **59%** of the
linear gross — exactly the mechanism FINDINGS §1b describes — but the cell would still be
**profitable** after it. **Trading cost is 6.0× the realisable gross**, and that is what kills it.

### P-c — the half that was falsified, and the half that fires the stop

| | breakeven | charged | headroom |
|---|---:|---:|---:|
| *ETF S1_short_intra (D247)* | *0.13 bp* | *1.60 bp* | *0.08×* |
| **HIGH S1_short_intra** | **1.06 bp** | **6.42 bp** | **0.16×** |

**The breakeven rose 8.2× while the charged cost rose 4.0×** — the edge outran the cost, and P-c's
mechanism clause said it would not. The shortfall roughly halved, from **12.3×** to **6.1×**.

**But D264 tied the expand-the-sample trigger to the HIGH stratum CLEARING hurdle K, and it does
not.** The reason is assumption-free, which matters because the half-spread was named in advance as
this design's weakest number:

> **Mean commission ALONE on the HIGH stratum is 1.92 bp/side against a breakeven of 1.06 bp.
> The cell loses at a ZERO spread.**

So the verdict does not rest on 4.5 bp being right. **The stop fires as written.**

**And R12's usual escape hatch is unavailable here.** Its second corollary says a construction
excluded on ETF cost arithmetic must be re-costed on futures before being discarded. **This one
cannot be:** its edge is single-name idiosyncratic variance, and there is no retail futures contract
on a single name. The ~20× cost reduction that rescues other intraday constructions is not reachable
by this one.

### Two cells clear hurdle H on both legs and lose money

| cell | Sharpe pct | money pct | H | CAGR | V |
|---|---:|---:|:--:|---:|:--:|
| **HIGH S1_short_intra** | 96.9th | **99.7th** | **PASS** | −15.84% | ✗ |
| **LOW S2_short_intra** | 97.2th | 97.9th | **PASS** | −0.89% | ✗ |

**[FINDINGS §3](../FINDINGS.md) reproducing exactly: beating a null is not having a strategy.** There
is real timing skill here — a money leg at the 99.7th percentile is not noise — and it is worth less
than the cost of harvesting it.

### The finding that outlives the study: overnight drift is a property of VOLATILITY, not of equities

| stratum | overnight/yr | intraday/yr | swing |
|---|---:|---:|---:|
| **LOW** — PG LMT PM MO | +4.36% | **+5.56%** | **−1.21 pts** |
| **HIGH** — CLF SM YELP RH | +13.81% | **−8.97%** | **+22.78 pts** |
| ALL | +8.98% | −1.97% | +10.96 pts |
| *57 ETFs — D247* | *+8.59%* | *−0.36%* | *+8.95 pts* |

**In the defensive mega-caps the drift accrues INTRADAY and the sign reverses.** D247 measured
+8.59%/−0.36% on 57 ETFs, and the programme has since treated that as a fact about the asset class.
**It is not.** It is concentrated in high-volatility names and absent at the low-volatility end.

**This bears directly on the wide extended-hours question already queued** (commit `c25218d`), which
asks where the untraded-window drift accrues across 11 instruments. **A volatility split belongs in
that pre-registration**, and it is named here before that study runs.

### Other measurements worth carrying

- **`SHORT_ALL` against FINDINGS §1b's formula.** Predicted `−mu − sigma^2` vs measured: LOW
  **−2.85 pts** (the same error D253 got on crypto), ALL −14.25, HIGH **−16.13**. **The
  approximation degrades where `sigma^2` is large**, which is what a second-order expansion should
  do. Quoting it as universal is safe only at moderate volatility.
- **Effective instruments 3.02 of 8**, against the 57 ETFs' 2.23 — LOW 1.87, HIGH 2.08. **Eight
  single names carry more independent breadth than fifty-seven ETFs.** FINDINGS §4's saturation near
  2.2 is a property of that universe, not a universal ceiling.
- **7 of 8 cells in the ALL stratum lose money**, including three of four long controls. **This is
  D247's result reproduced exactly** — *"15-minute sampling breaks both estimators in both
  directions"* — so this is a **horizon** result as much as a direction result, and the short failure
  cannot be cleanly attributed to direction.

### POST-HOC, DISCLOSED, AND NOT ACTED ON HERE

**The IBKR commission is charged per SHARE, so cost in bps is inversely proportional to price**, and
within the HIGH stratum it varies twenty-fold:

| | RH | YELP | SM | CLF |
|---|---:|---:|---:|---:|
| commission, bp/side | **0.20** | 1.44 | 1.89 | **4.15** |

**A high-priced, high-volatility name gets the HIGH stratum's edge at a fraction of its commission.**
This was invisible on ETFs, which cluster in price.

**It is NOT tested here and must not be.** D264's stop forbids an additional stratum, and computing a
per-symbol verdict now would be exactly the complement-chasing
[D246](D246-the-search-protocol-for-s3.md) Constraint 3 forbids. **It is recorded as a candidate for
a separate pre-registration with this provenance stated**, which is the route Constraint 3 explicitly
leaves open.

---

## Stop — fired, and bounded exactly as written

**The construction is CLOSED on this sample.** No parameter sweep, no additional stratum, no third
arm, no re-cut window, no 5-minute bars. D246's reserved cohort was not touched.

**And the closure is bounded in the words fixed before the run.** It closes **this construction on
these eight survivor names, on the personal track**. It does **not** close the intraday short as a
question:

1. **The sample is survivor-only and the bias runs AGAINST the short.** 41.6% of the 2013–17 cohort
   is unreachable because `TIME_SERIES_INTRADAY` serves no delisted ticker. A fail is ambiguous, and
   that was declared before the data was seen precisely so it could not be argued afterwards.
2. **Eight names is thin**, at effective breadth 3.02.

**What a negative here DOES establish**, and it is not nothing: the cost arithmetic that closed D247
and D248 **moves with volatility, and does not move far enough** — and it fails at a zero spread,
which is a stronger and more durable statement than the one D247 could make.

---

## Ledger, as run

| count | N |
|---|---:|
| fresh — 12 short cells + 4 long controls | **16** |
| + Part A anatomy (drift decomposition ×3, held-bar returns, `SHORT_ALL` ×3) | 23 |
| + carried from D263 | 45,886 |
| **total** | **45,909** |

**Unchanged from the pre-registration.** No cell was added, and the post-hoc price observation above
is recorded rather than scored, so it costs nothing against this count.

---

## ADDENDUM — is the verdict an artefact of the capital size it was run at? No, and it cannot be.

**Asked by the principal after the result was committed.** `scripts/d264_cost_vs_size.py`.

**This scores no new cell.** It varies only the cost schedule against an already-measured breakeven,
which is the re-costing [R12](../RULES.md#r12) explicitly requires — *"a cross-screen must RE-COST,
not merely re-threshold"* — before a candidate is discarded. No book is rebuilt, no hurdle re-run,
no stratum added, no window re-cut. **It could only ever strengthen or weaken the closure, never
rescue a cell, because the breakeven it is compared against does not move.**

### The size the study was run at

**$175,439 per position** — `PRIMARY_CAPITAL / 57`, which is **D247's own per-position notional**,
fixed in the pre-registration so the commission comparison to the ETF study would be exact rather
than approximate. Eight names, so **$1.40M** total.

### Why the breakeven is the right thing to hold fixed

`breakeven_bps` reconstructs the arm's **cost-free** excess return — it adds the charged cost back
before dividing by turnover — so it is a property of the signal and its turnover, **not of the
account.** Changing size cannot move it. The question therefore reduces to a single one: **at what
size does the charged cost fall below the breakeven already measured?**

### The answer is that no size does, and the arithmetic says why before the table does

IBKR is `max(min(per_share × shares, 1% of notional), min_order)`. In the per-share regime the bps
figure is

```
1e4 × (c × N/p) / N   =   1e4 × c / p
```

**Notional does not appear.** Commission in bps is a function of **price alone**. Below
`shares = min_order / c` the order minimum binds and it gets **worse**; above, it is flat. **There is
no size at which it gets cheaper.**

| notional/position | HIGH commission, Fixed | HIGH commission, Pro tiered |
|---:|---:|---:|
| $1,000 | 10.00 bp | 3.50 bp |
| $10,000 | 2.12 bp | 1.40 bp |
| $50,000 | **1.92 bp** | **1.34 bp** |
| **$175,439** *(as run)* | **1.92 bp** | **1.34 bp** |
| $1,000,000 | 1.92 bp | 1.34 bp |
| $10,000,000 | 1.92 bp | 1.34 bp |

**Against HIGH S1_short_intra's breakeven of 1.06 bp.** So on **both** real IBKR schedules, at **every
size from $1,000 to $10M**, and at a **zero spread**, the cell still loses. This is strictly stronger
than the result section's claim, which priced only the Fixed schedule.

**The LOW stratum's S2_short_intra is the nearest thing to an exception and does not survive
either.** Breakeven 1.02 bp against a commission plateau of 0.50 bp (Fixed) or 0.35 bp (Pro), so
**commission alone clears** — but it would then need an all-in half-spread under roughly 0.5–0.7 bp
on names like MO, **tighter than SPY's**. Not reachable on a single name.

### And the large-size rows are optimistic, in an unmeasured amount

**Market impact is charged nowhere in this study**, and it is the only cost that **grows** with size.
The high-volatility names ran $60–85M median daily dollar volume in the selection window against
~324 turns/yr. **Every row above ~$1M per position understates the true cost by an amount nobody
here has measured.** Read those rows as *"not cheaper"*, never as *"this is what it would cost"*.

### A documentation defect this surfaced, recorded rather than silently fixed

**[R12](../RULES.md#r12) states the personal track's cost as *"IBKR Pro, and the $0.35 minimum binds
below ~$1,000 per position"*. The committed cost model in `run_macd_ladder.py` is IBKR FIXED:
`$0.005/share, min $1.00, cap 1%`.** D264 used the code, not the prose.

**Nothing is invalidated** — the verdict holds under both schedules, as the table shows — but the two
should agree, and the quoted threshold is right only for a ~$10 instrument: the minimum binds below
`100 × price` on Pro and `200 × price` on Fixed, so for a $250 name like RH it binds below $25,000,
not $1,000.

**Not fixed here, because which schedule the personal track assumes is a standing decision about the
book and not a detail of this study.** Flagged for whoever makes it.
