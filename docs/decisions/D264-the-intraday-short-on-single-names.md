# D264 — The intraday short on single names

**Status:** PRE-REGISTERED. Committed **before the fixture was scored**. Nothing here is a result.
**Date:** 2026-09-01
**Area:** Strategy research · **personal track** ([BOOK.md](../BOOK.md)), R12 personal standards

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
