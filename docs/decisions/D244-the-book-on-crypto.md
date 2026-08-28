# D244 — The book on crypto

**Status:** Pre-registered — committed BEFORE the crypto fixture is scored
**Date:** 2026-08-28
**Area:** Strategy research

---

## The question

**Do S1 and S2 capture something general about price behaviour, or something specific to US
equity ETFs?**

This is the strongest generalisation test available: a different asset class, different
microstructure, different participants, different cost regime. And it is pointed: **D239 and
D243 established S1 is a bet that reversals beat continuations, and crypto is reversal-heavy.**
If the reversal thesis is real, this is where S1 should work.

---

## The rules, frozen — and the one thing that cannot be frozen

```
S1   position = +1 if hist_L > 0 AND md_L <= 0     (Impulse MACD 34/9, log space)
S2   UPTREND := g_lo > 0 AND g_hi > 0              (k = 3, 252-bar OLS on log pivots)
     ENTRY at onset; EXIT at age 63 or state end
C    S1 + S2 on one shared pool at 100% capital
```

**Bar counts are frozen. Their calendar meaning is not, and cannot be.**

| | on ETFs (252 trading days/yr) | on crypto (365 days/yr) |
|---|---|---|
| 252-bar regression | **1 year** | **0.69 years** |
| 63-bar age cap | one quarter | ~2 months |
| 34-bar Impulse | ~7 weeks | ~5 weeks |

**The book specifies BARS, so bars is what runs.** D221 established the indicator is scale-free
in bar counts, and D219's amendment already requires cross-fixture comparison on
`arm − matched buy-and-hold` rather than on raw Sharpe.

**A calendar-matched variant (365/91) is NOT registered here.** If the bar-frozen version fails,
a calendar-matched one is a *separate* pre-registration, not a rescue. D243's "no new rule may be
proposed in this record" applies.

---

## Three asymmetries declared before the run

### 1. Costs are 6× higher, and this is the most likely thing to kill it

**`FEE_BPS = 10.0` per side** — `run_assembled_strategy`'s committed crypto constant, reused
rather than chosen. Against the ETF book's derived **~1.5–1.8 bp**, that is roughly **six times
the friction**, and both rules turn over.

**It is probably still optimistic for the small-cap alts**, where the spread alone can exceed
10 bp. **The breakeven cost is reported** so the sensitivity is visible rather than assumed.

### 2. `PPY = 365`, not 252

Crypto trades 24/7. Annualisation, the `rf` per-bar charge and every Sharpe here use 365.

### 3. The universe, chosen by date and not by performance

The fixture holds **63 coins with ragged inception**, and `load_panel` requires equal bar counts,
so a start date has to be chosen. The frontier:

| start | coins retained |
|---|---:|
| 2018-01-01 | **34/63** |
| 2019-01-01 | 41/63 |
| 2020-01-01 | 50/63 |
| 2021-01-01 | 63/63 |

**Rule: the earliest start that retains a majority of the universe → 2018-01-01, 34 coins.** That
is a stated criterion, not a sweep, and it maximises live span subject to keeping a real
cross-section. After the 1,000-bar warm-up (2.74 years on a 365-day calendar) that leaves
**~5.3 live years** — comparable to the ETF study's original 6.0.

**The universe is NOT survivorship-cleaned.** It contains **LUNC, USTC and FTT** — Terra and FTX
— which is the honest construction and will hurt any long book that held them.

---

## Hurdles

- **X1.** Each arm's excess Sharpe **> 0** and **> buy-and-hold's** on the same bars.
- **X2 — carries the verdict.** Each beats its **matched-count rotation null at p95**. Same
  exposure, turnover and holding periods, wrong bars. **This has been the most robust control in
  the programme**, at the 97th–100th percentile on every fixture where a rule was real and at the
  80.6th where S1 was not.
- **X3.** The **block bootstrap p05 on each arm's own excess Sharpe > 0.** D230 is why this is
  never optional, and D243 showed it is the leg that separates S1 from S2.
- **Reported, not hurdles:** ρ between S1 and S2 on crypto — *does the diversification structure
  travel to a different asset class?* — plus exposure, deployable return, Calmar, max drawdown,
  hurdle E, the **breakeven cost**, and the money leg of each null.

---

## Predictions

| | prediction | confidence |
|---|---|---|
| **Y1** | **S1 clears X1 and X2.** Crypto is reversal-heavy and D239/D243 identified that as exactly what S1 harvests. This is the prediction the whole record is pointed at | **moderate** |
| **Y2** | **S2 also clears X1 and X2.** Crypto trends violently, and a trend-onset rule should find that | **moderate** |
| **Y3** | **Both fail X3.** 5.3 live years is less than the ~12 needed at the effect sizes seen so far; the ETF book only cleared its interval at 12.8 years | **moderate-high** |
| **Y4** | **ρ between S1 and S2 stays below 0.35.** It has been +0.159, +0.175 and +0.123 on three ETF spans, and the reason is structural — an instrument below its channel is rarely in a confirmed uptrend — so it should travel | **moderate** |
| **Y5** | **Buy-and-hold on the equal-weighted 34 is much worse than BTC alone**, because the alt basket contains total losses. The benchmark this book must beat is therefore weak, and a win against it means less than it looks | **moderate-high** |

**Y1 is the point of the record.** If S1 fails on the most reversal-heavy asset class available,
after D243 showed it failing in a continuation era on ETFs, then **its viable window is narrow
enough to question whether it has one.**

**Y5 is registered so a win cannot be oversold.** An equal-weighted basket including LUNC and FTT
is a low bar, and clearing it is not the same as making money.

---

## What this can and cannot show

**Can:** whether the rules are about price behaviour or about US equity ETFs.

**Cannot:** anything about era. Crypto 2020–2025 overlaps the ETF training window, so this is an
**asset-class holdout, not a time holdout.** D243 remains the only time-independent evidence.

---

## Stop

**This record proposes no rule and changes no rule.** Whatever happens, the outcome is recorded
in `BOOK.md` as evidence for or against the existing entries — nothing is re-cut, and no crypto
variant is created.

---

## Ledger

| count | N |
|---|---:|
| fresh — **0 cells.** Two frozen rules and their union, on a new asset class | **0** |
| + D243's 0, D242's 3, D241's 5, D240's 5, D239's 3, D238's 4, D234's 6, D235's 7, D236's 6 | 39 |
| + the gradient anatomy | 60 |
| + disclosed ETF prior | **45,863** |

**Nothing is searched**, so the count does not move.

## Reuse — D212 is binding

`books_on` from `run_book_extended` already repoints the loader at an arbitrary fixture; the
scorers, nulls, allocator and bootstrap are all committed and tested. `FEE_BPS` is
`run_assembled_strategy`'s. **Written fresh: the panel builder for the 34-coin intersection, the
cost override and the `PPY = 365` override — and nothing else.**

## Verification

- The frozen constants are asserted against `run_uptrend_onset`'s.
- **The ETF fixtures must still reproduce their published numbers**, so the overrides cannot have
  leaked into the equity results.
- **`PPY` and `cost_fraction` are asserted to be the crypto values** inside the run, and the ETF
  values outside it — an override that silently persisted would corrupt every later study.
- **The 34-coin panel is asserted**: 34 symbols, equal bar counts, first bar 2018-01-01 or later.
- **Hurdle E is computed, not assumed.**

---

## VERDICT

**Produced:** 2026-08-28 · `uv run python scripts/run_book_crypto.py` · Page:
[`BOOK_CRYPTO_RESULTS.md`](../../BOOK_CRYPTO_RESULTS.md)

**35 coins × 1,899 live bars (5.2 years at PPY 365), 2020-10-15 → 2025-12-30, 10 bp/side.**

### The one-sentence version

**S1 does not merely fail on the most reversal-heavy asset class available — it lands at the
29.1st percentile of its own rotation null, meaning randomly-timed books at the same exposure
beat it seven times in ten.**

### The book on crypto

| | exposure | excess Sharpe | Δ vs B&H | CAGR | deployable | max DD | rot null |
|---|---:|---:|---:|---:|---:|---:|---:|
| **S1** | 25.4% | **−0.291** | −0.187 | −6.17% | −3.38% | −48.90% | **29.1st** |
| **S2** | 14.3% | +0.052 | +0.156 | 1.53% | 5.00% | −34.30% | 73.2nd |
| **C** | 38.1% | −0.162 | −0.058 | −3.67% | −1.30% | −59.44% | 49.0th |
| *B&H, equal-weighted 35* | *100%* | *−0.105* | — | *−4.18%* | *−4.18%* | ***−90.90%*** | — |
| *BTC alone* | *100%* | *+0.602* | — | ***+48.15%*** | *+48.15%* | *−76.63%* | — |

**X1: 1 of 2. X2: 0 of 2. X3: 0 of 2.**

### S1 failed, and not because of costs

**The breakeven cost is −50.6 bp per side.** S1 loses money with *free trading*. Costs — the
thing D244 named as most likely to kill it — are not the cause. Neither is the benchmark: S1
underperformed an equal-weighted alt basket that itself lost 4.18% a year and drew down 90.9%.

**The rotation null is the damning number.** At the 29.1st percentile, S1's timing is *worse than
random* at the same exposure, turnover and holding periods. On the mined and holdout ETF fixtures
it sat at the 100th.

### S2 was not skilful either, only unharmful

**S2 cleared X1 — it beat buy-and-hold by +0.156 — and failed X2 at the 73.2nd percentile.** Its
positive result is not distinguishable from trading the same amount at random times. It has real
cost headroom (breakeven **63 bp**, 6.3× what was charged), so if a signal were there the fees
would not have hidden it.

### CORRECTION — the universe does not contain LUNC, USTC or FTT

**The pre-registration above states the universe holds Terra and FTX. It does not.** All three
launched after 2018, so the date cut excludes them. Caught by a test asserting their presence,
which failed.

**What the 35 do retain is the 2017-era cohort that collapsed** — XEM, LSK, STEEM, SC, SNT, ICX,
BTG, OMG, QTUM, REP, WAVES, most of them down 90-99% from their peaks. **The equal-weighted
benchmark still drew down 90.90%**, so nothing was screened out and the conclusion is unchanged.
But the exposure to catastrophic failure is of the *2018 cohort*, not the 2021-22 blowups, and
the record should not have said otherwise.

### Y5 mattered, and it is why no win here would have counted

**Buy-and-hold on the equal-weighted 35 lost 4.18% a year at a −90.90% drawdown, while BTC alone
made 48.15%.** The benchmark this book had to beat was a catastrophe, and beating it would have
meant very little. As registered in advance.

### Scoring — three confirmed, one split, one falsified

| | prediction | outcome |
|---|---|---|
| **Y1** | **S1 clears X1 and X2** | **FALSIFIED**, and it was the point of the record |
| **Y2** | S2 clears X1 and X2 | **SPLIT.** X1 yes, X2 no |
| **Y3** | both fail X3 | **CONFIRMED**, p05 −1.205 and −0.647 |
| **Y4** | ρ stays below 0.35 | **CONFIRMED**, +0.2343 — higher than the ETF spans but still low |
| **Y5** | equal-weighted B&H much worse than BTC | **CONFIRMED** by 52 points of CAGR |

### The reading, as declared in advance

> **NEITHER RULE TRAVELS. Both are about US equity ETFs.**

### What is fair to say, and what is not

**Two confounds are real and were declared before the run.**

1. **The calendar mismatch.** 252 bars is one year on ETFs and **0.69 years** here, so S2's
   "confirmed year-long uptrend" is really eight months and S1's 34-bar Impulse is five weeks
   rather than seven. The bar-frozen rule is what the book specifies and what was run, **but this
   is not the same economic rule.**
2. **The warm-up ate 2.74 years**, so the live window starts 2020-10 and misses the 2018–2020
   crypto bear entirely. What was tested is the 2021 blowoff, the 2022 collapse and the recovery.

**What those confounds do NOT excuse is the rotation null.** A calendar mismatch would make the
rule weaker; it would not make its timing *worse than random*. **S1 at the 29.1st percentile is a
statement about the signal, not about the units.**

**And per this record's stop, no calendar-matched variant is created here.** If someone wants to
test 365/91 on crypto, that is a separate pre-registration.

### What this changes

**Nothing in the rules. Everything in the evidence.**

**S1's record is now:** cleared an instrument holdout on US equity ETFs (D237) · **went negative
in a continuation era on the same asset class** (D243, 80.6th percentile) · **negative and
worse-than-random on crypto** (here, 29.1st percentile).

**Two failures in a row, the second on the asset class the reversal thesis said should suit it
best.** Recorded in `BOOK.md` as evidence against S1.

**S2's record is:** cleared an instrument holdout (D242) · cleared a time holdout (D243) ·
**showed no demonstrated skill on crypto, while not being harmful** (here). It remains the
stronger entry, and its generality is now bounded to equities.

### Ledger

| count | N |
|---|---:|
| **fresh — 0 cells** | **0** |
| + D243's 0, D242's 3, D241's 5, D240's 5, D239's 3, D238's 4, D234's 6, D235's 7, D236's 6 | 39 |
| + the gradient anatomy | 60 |
| + disclosed ETF prior | **45,863** |
