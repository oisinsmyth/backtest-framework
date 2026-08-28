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
