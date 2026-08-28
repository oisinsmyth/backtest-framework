# D253 — The short sides of S1 and S2, on crypto

**Status:** Pre-registered — committed BEFORE the runner exists
**Date:** 2026-08-28
**Area:** Strategy research

---

## Provenance, stated first because it has to be

**This is the inverse of a cell that failed, and [D246](D246-the-search-protocol-for-s3.md)
Constraint 3 governs that.** [D244](D244-the-book-on-crypto.md) ran S1 **long** on crypto and it
landed at the **29.1st percentile** of its own rotation null — below random. Registering S1
**short** on the same fixture is a complement.

**The distinction that makes it registrable, and it is the only one that counts:** the prediction
comes from a *structural hypothesis stated before the measurement*, not from inspecting a bad
result and flipping its sign. D246 permits exactly this — *"It may be registered separately, on its
own merits, with that provenance stated."*

**This is therefore NOT S3**, it does not run under the S3 protocol, and **D245's reserved
never-seen cohort is not touched.**

---

## The hypothesis, and where it came from

The principal proposed it: **an ETF is a weighted average, so diversification removes idiosyncratic
variance by construction; what is left is the common factor, and the common factor is exactly what
carries the risk premium.** A fall in a diversified basket is therefore a premium being paid, and
it bounces. That is why every short this programme has built has died.

**Measured, R9-compliant, before this record was written** — forward 21-bar return of names that
have fallen, by idiosyncratic tercile:

| tercile | ETF equities | **crypto** |
|---|---:|---:|
| low idio | **+39.77%** | **−50.57%** |
| mid | +13.52% | −36.33% |
| high idio | +5.33% | **−61.43%** |
| **Q1 − Q5 premium** | **+18.47 / +7.57 / +9.86** | **−51.38 / −82.33 / −74.81** |

**The sign fully reverses.** And on S1's short mirror specifically: the held bars beat the name's
own drift on **42 of 46 equity ETFs** but on only **28 of 62 crypto names** — median excess
**−4.38%** against strongly positive on ETFs.

**One part of the hypothesis was NOT confirmed and is recorded as such:** within a universe,
idiosyncratic share does *not* predict shortability — `corr = −0.006` on crypto, `−0.195` (n.s.)
on ETFs. The operative variable is **between-universe**: whether a premium attaches to the thing
that fell. This study tests the between-universe claim, not the within-universe one.

---

## The rules — frozen, taken from the book, only the sign changed

```
S1_short   position = -1  if  hist_L > 0 AND md_L <= 0            (D238's mirror)
S2_short   DOWNTREND := g_lo < 0 AND g_hi < 0
           enter at onset, exit at age 63 or when the state ends  (D240's mirror)
C_short    S1_short + S2_short on one shared pool at 100% capital, FCFS
```

Bar counts frozen at the book's values — Impulse 34/9, k=3, window 252, age cap 63. **No cell
varies a parameter.** D221 established the indicator is scale-free in bars; a calendar-matched
variant is not run here and would be a separate registration, not a rescue.

---

## Fixture and overrides

**[D244](D244-the-book-on-crypto.md)'s frozen 34-coin fixture**, `crypto_book_2018_raw.csv.gz`,
chosen for consistency with the committed crypto book run and because it is rectangular. Three
overrides, each asserted OFF outside the crypto block:

| | | why |
|---|---|---|
| `PPY` | **365** | crypto trades 24/7 |
| `FEE_BPS` | **10 per side** | `run_assembled_strategy`'s committed crypto constant — 6x the ETF book's ~1.6bp |
| `BORROW_ANNUAL` | **10%** | `run_short_mirror`'s 1.0% is an *equity* borrow rate and is wrong here by an order of magnitude |

**The borrow rate is a stated assumption, not a measurement, and the verdict must not rest on it.**
Crypto borrow and perpetual funding vary enormously and we hold no funding data. **`breakeven
borrow` is therefore a HEADLINE number in every cell, not a footnote** — it says what rate would
have to hold for the cell to be worth anything, and the reader can price that themselves.

---

## The drift problem, named before the run

**Crypto's aggregate drift over the sample is the confound.** On the wider 63-name universe it is
**−10.13%/yr**; on this 34-coin fixture it will be measured and reported before any cell is scored.
**If the universe fell, a short makes money by existing** and every cell will look good for reasons
that have nothing to do with signal.

**This is exactly what hurdle H controls for.** The matched-count rotation null holds the same
exposure, the same turnover and the same holding periods on the wrong bars — so it earns the drift
too. **Only the excess over the null is evidence.** The raw return of a short book on a falling
universe is not a result and will not be reported as one.

## Hurdles

- **H — carries the verdict.** Beat the matched-count rotation null at **≥95th percentile on net
  Sharpe AND on money**. Both legs, per [R10](../RULES.md)'s second corollary: a per-symbol rotation
  null destroys cross-sectional synchrony and so *understates* the volatility of a market-wide
  signal — conservative on money, harsh on Sharpe. A single-leg verdict is not safe here.
- **H-BEST.** A best-of-three floor (D228), because D240's stop cleared at the 99.6th uncorrected
  and died at the 71.7th out of sample.
- **E.** ≥100 pooled entries and ≥30 per symbol.
- **Financing.** `excess = total − long_f·rf − short_f·borrow`, D238's `excess_of`. Report gross,
  net, and **breakeven borrow**.
- **[R10](../RULES.md) concurrency, mandatory.** Names held at once — mean, max, fraction above 20 —
  actual against a per-symbol-rotated book of identical exposure. **Crypto synchronises harder than
  equities.** Report the effective sample, never the pooled trade count.

## Predictions, committed before the runner exists

| | prediction | confidence |
|---|---|---|
| **T-a** | **Both short arms hold bars that fall relative to their own drift.** The anatomy already shows the median crypto name doing this at −4.38% | **high** — measured, disclosed above |
| **T-b** | **At least one cell clears H on Sharpe AND money.** This is the study's real question | **moderate** |
| **T-c** | **Concurrency is extreme — over half the universe held at once at peak, against a rotated max far below it.** Crypto co-moves harder than the 57 ETFs, where the wedge book already hit 41 of 57 | **high** |
| **T-d** | **S2_short FAILS hurdle E.** S2 gives 5 entries/symbol on 57 ETFs over 12.8 years; 34 coins over ~8 years will give fewer | **high** |
| **T-e** | **The raw returns look good and most of it is drift, not signal** — the gap between raw return and null percentile is the number that matters, and it will be large | **moderate-high** |

**T-b and T-e are registered in tension on purpose.** A cell can post a large positive return and
be worthless. **T-e exists so that a good-looking raw number cannot later be quoted as a result**,
which is the trap D240 walked into when it read an uncorrected 99.6th percentile as a finding.

## Stop

**If no cell clears H on both legs, this is CLOSED.** No fourth cell, no calendar-matched variant,
no re-cut fixture, no move to the ragged 63-name universe as a rescue. A wider universe is a
separate registration with its own ledger, not a second look at this one.

## Ledger

| count | N |
|---|---:|
| fresh — 3 cells | 3 |
| + the motivating anatomy: 3 idio terciles x 2 universes x (2 return buckets + 1 held-bar measure) | 21 |
| + carried from D250 | 45,936 |
| **total** | **45,957** |

---

## RESULT — CLOSED, and the registered primary hurdle was the wrong hurdle

**Produced:** 2026-08-28 · `uv run python scripts/run_book_shorts_crypto.py` · artifact
`data/book_shorts_crypto_summary.json` · page `BOOK_SHORTS_CRYPTO_RESULTS.md`

35 coins x 2,899 bars, **5.20 live years**, 2020-10-15 → 2025-12-30. Universe equal-weighted
CAGR **−4.17%**, median coin **−9.12%**, **19 of 35 coins fell**. Effective independent
instruments **1.80 of 35**.

### The one-sentence version

**Two cells clear hurdle H at the 98.7th and 99.3rd percentiles on both legs, and both lose
double-digit percentages a year — because hurdle H measures skill against random timing and
cannot see the structural variance drag that makes a crypto short unviable regardless of skill.**

### The cells (model B — one pooled account, 1/n per coin)

| cell | exposure | CAGR | terminal | excess Sharpe | vol | max DD | min entries/sym | breakeven borrow |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **S1_short** | 25.4% | **−10.12%** | x0.574 | −0.395 | 25.2% | −57.92% | 17 | **−25.6%** |
| **S2_short** | 14.7% | **−6.46%** | x0.707 | −0.472 | 14.8% | −37.20% | 2 | **−31.7%** |
| **C_short** | 34.0% | **−13.55%** | x0.469 | −0.463 | 29.2% | −66.32% | 15 | **−26.1%** |
| *SHORT_ALL* | *100%* | ***−58.90%*** | *x0.010* | *−0.882* | *77.6%* | *−99.23%* | — | *−44.6%* |
| *B&H* | *100%* | *+32.55%* | *x4.332* | *+0.709* | *77.6%* | *−84.86%* | — | — |

**Every breakeven borrow is NEGATIVE.** These lose with free stock loan, and would still lose if a
counterparty *paid* 25% a year to lend. **Making borrow a headline number was worth it: the
assumption turned out to be irrelevant, which is exactly what needed establishing.**

### Hurdle H — passed, and worthless

| cell | Sharpe pct | money pct | clears H |
|---|---:|---:|:--:|
| **S1_short** | **98.7th** | **95.8th** | **YES** |
| S2_short | 86.3rd | 79.6th | no |
| **C_short** | **99.3rd** | **98.5th** | **YES** |

**The signal has real skill.** S1_short loses 10.12%/yr where randomly-timed shorts of identical
exposure, turnover and holding period lose materially more. It also clearly beats the registered
`SHORT_ALL` benchmark. **By the letter of this pre-registration, two cells pass.**

**They are still uninvestable.** A book returning −10.12%/yr is not a strategy whatever percentile
it occupies. **The registration's defect is now recorded: hurdle H is a skill test, not a
viability test, and D253 never registered a hurdle requiring a positive return.** Necessary, not
sufficient — and the same error is available to any future study that reads a percentile as a
result.

### Why everything loses — the mechanism, and it is quantitative

**A daily-rebalanced short earns `log(2 − e^r)`, whose expectation is approximately `−mu − sigma^2`.**
[D251](D251-the-cross-sectional-dollar-neutral-pre-screen.md) found this independently on ETFs and
measured the drag at 6.2 to 14.9 points a year. Crypto's volatility makes it enormous:

| | |
|---|---:|
| universe vol | **77.6%** → `sigma^2` = **0.602** |
| universe geometric drift `mu` | −4.17% |
| **predicted** short return `−mu − sigma^2` | **−56.05%** |
| **measured** `SHORT_ALL` | **−58.90%** |
| gap | **2.85 points** |

**The formula predicts the measured number to under three points.** This is also why `B&H` returns
**+32.55%** while the median coin returns **−9.12%**: the same convexity, with the sign reversed,
paid as a rebalancing premium. **The long and short sides of this universe are not mirror images —
variance is a tax on one and a subsidy on the other.**

### Model A — ruin, caught by an assertion D238 wrote

`run_short_mirror.signed_log_returns` refuses to score a position wiped out on one bar. **It
refused.**

| cell | worst adverse bar | | equity at 1x | verdict |
|---|---:|---|---:|---|
| **S1_short** | **+215.1%** | BTG-USD 2025-06-13 | **−1.15** | **RUINED** |
| **C_short** | **+215.1%** | BTG-USD 2025-06-13 | **−1.15** | **RUINED** |
| S2_short | +70.9% | STEEM-USD 2022-04-21 | +0.29 | survives |

**Maximum survivable per-name notional is 0.46x.** Eight bars in this fixture would wipe out a
full-notional short; the arms held one of them. **A guard written for a different study on a
different asset class caught the thing that matters most here** — that a crypto short is not
merely unprofitable but not survivable at full size.

Model B (pooled, 1/n) is what the table above scores, and **it flatters the arms**: it assumes
costless continuous rebalancing to 1/n and no intra-bar margin call. Both models are reported;
the ruin is not superseded by the pooled numbers.

### R10 — concurrency, and T-c was right

| cell | mean held | max | *rotated max* | **sd ratio** |
|---|---:|---:|---:|---:|
| S1_short | 8.9 | **35 of 35** | *16* | **4.37x** |
| S2_short | 5.1 | 23 of 35 | *13* | **2.80x** |
| C_short | 11.9 | **35 of 35** | *23* | **3.92x** |

**Both S1-derived cells hold the entire universe at once.** Effective instruments **1.80 of 35**.
The 1,121 pooled entries are not a sample size.

### Scoring

| | prediction | outcome |
|---|---|---|
| **T-a** | both arms hold bars that fall relative to their own drift | **CONFIRMED** — S1_short at the 98.7th percentile of its matched null |
| **T-b** | at least one cell clears H on both legs | **CONFIRMED** — two do, and it did not matter |
| **T-c** | concurrency extreme, over half the universe at peak | **CONFIRMED** — 35 of 35, sd ratio 4.37x |
| **T-d** | S2_short fails hurdle E | **CONFIRMED**, and understated: **all three fail**, at 17 / 2 / 15 minimum entries |
| **T-e** | raw returns look good and most is drift | **FALSIFIED, and it is the informative one.** The raw returns look terrible and the null looks worse. I expected drift to flatter the arms; instead **variance drag crushed everything and the arms beat their nulls by losing less** |

**T-e is the miss worth more than the four hits.** The pre-registration anticipated the wrong
confound. It guarded against a good-looking number being drift, and the actual hazard was a
bad-looking number being read as a failure of the signal when it was a failure of the instrument.

### What is closed, and what is not

**CLOSED per the registered stop.** No fourth cell, no calendar-matched variant, no move to the
63-name universe.

**What this does NOT close is the principal's hypothesis.** The between-universe claim held: the
buy-the-dip premium reverses sign between ETFs and crypto, and the short signal has measurable
skill here where it had none on ETFs. **What defeats it is a second obstacle the hypothesis never
addressed** — the variance drag on a short position, which scales with `sigma^2` and is therefore
worst in exactly the high-idiosyncratic instruments the hypothesis points toward.

**That is the finding: the two effects run in opposite directions.** Idiosyncratic risk is where
the short edge lives, and it is also what makes a short position bleed. Crypto has enough of the
second to swamp the first by an order of magnitude. A single-name equity universe sits between the
two extremes, which is where D252's fixture becomes the deciding test rather than an extension.
