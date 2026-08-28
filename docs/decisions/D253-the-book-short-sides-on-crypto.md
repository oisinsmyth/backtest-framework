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
