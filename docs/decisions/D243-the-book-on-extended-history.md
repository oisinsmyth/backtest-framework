# D243 — The book on extended history

**Status:** Pre-registered — committed BEFORE the extended fixture is scored
**Date:** 2026-08-28
**Area:** Strategy research

---

## What this is

**The two book entries, frozen, run on twice the history.** Nothing else. No variants, no cells,
no parameter changes, no search. `S1` and `S2` exactly as `BOOK.md` specifies them, plus the
combination of the two, which is what the book *is*.

The fixture was rebuilt from a price cache that already held full history; what was fetched was
**corporate actions over the full span** — 5,716 dividends and 30 splits for the 57, against
sidecars that previously stopped at 2015-01-16. Building without them would have left every
pre-2015 split unadjusted, which D226 showed produces confident nonsense.

| | old | **new** |
|---|---:|---:|
| mined 57 | 2,515 bars, **6.0y live** | 4,222 bars, 2009-11-11 → 2026-08-26, **12.8y live** |
| holdout 60 | 2,515 bars, 6.0y live | 2,963 bars, 2014-11-12 → 2026-08-26, 7.8y live |

**The old fixtures are untouched** (D24). Every published number stays reproducible.

---

## The one thing that makes this different from every prior test

**The extended live window CONTAINS the training window.** It is not a clean holdout, and
reporting it as one would be wrong. It decomposes into:

| period | bars | status |
|---|---|---|
| **~2013-11 → 2018-12** | ~1,280 | **NEVER SEEN. The first time-independent test in this programme** |
| 2018-12 → 2024-12 | 1,515 | the training window for S1 and S2 |
| 2024-12 → 2026-08 | ~413 | forward; spent by D237 for S1, unspent for S2 |

**Every holdout so far has been an INSTRUMENT holdout.** The 60-ETF universe correlates **+0.978**
with the 57, so D237 and D242 showed the rules are not fitted to particular tickers and showed
nothing about the era. **The pre-2018 stretch is the first data that is new in TIME**, and it is
where the verdict of this record lives.

**Both spans are reported separately and the new one carries the weight.** The full-span numbers
are contaminated by containing the training data and are reported for interval width only.

---

## The rules, frozen

```
S1   position = +1  if  hist_L > 0  AND  md_L <= 0
S2   UPTREND := g_lo > 0 AND g_hi > 0   (k = 3, 252-bar OLS on log pivot prices)
     ENTRY the first bar of an episode; EXIT at age 63 or when the state ends
C    S1 + S2 on one shared pool at 100% capital
```

**No stop.** D242 retired the −8% stop after it failed its overlay null out of sample; it is not
part of S2 and is not tested here.

Every constant asserted against the committed runners. If one differs, the test is void.

---

## Hurdles

**On the NEW period (~2013-11 → 2018-12), which carries the verdict:**

- **V1.** Each entry's excess Sharpe **> 0** and **> buy-and-hold's** over the same bars.
- **V2.** Each beats its **matched-count rotation null** at p95 on that sub-period.
- **V3.** The delta over buy-and-hold reaches **25% of the mined delta** — S1's floor
  `0.25 × 0.511 = +0.128`, S2's `0.25 × 0.375 = +0.094`. D237's construction, reused.

**On the full extended span, reported for precision rather than as a verdict:**

- **V4.** The **block bootstrap interval on each arm's own excess Sharpe**, and on the
  combination's delta over S1. **The whole point of doubling the data was to narrow these**, and
  whether they now exclude zero is the single most consequential number in the record.

**Reported, not hurdles:** exposure, deployable return, Calmar, max drawdown, hurdle E (which
should finally improve, since entries per symbol scale with span), and the behaviour through
**2015–16 and 2018 Q4** — corrections the original fixture never contained in its live window.

---

## Predictions

| | prediction | confidence |
|---|---|---|
| **W1** | **S1 does WORSE on the new period than on training.** D239 established its edge is partly a bet that reversals beat continuations, and 2013–2018 was a steady low-volatility grind — continuation-dominated | **moderate** |
| **W2** | **S2 does BETTER on the new period than on training**, for the same reason and in the opposite direction: it is the continuation arm | **moderate** |
| **W3** | **Both still clear V1 and V2.** The rotation nulls have been the most robust evidence in the programme, at the 99.7th–100th percentile on every fixture so far | **moderate-high** |
| **W4** | **S1's own interval now excludes zero on the full span**; at 12.8 years the standard error falls to ~0.32 from ~0.46 | **moderate** |
| **W5** | **The combination's delta over S1 still fails.** It was +0.178 (p05 −0.010) mined and +0.094 (p05 −0.104) on the holdout; doubling the data narrows the interval but the point estimate is small | **moderate** |

**W1 and W2 together are the real test, and they are a paired bet.** If S1 weakens and S2
strengthens in a trending era, D239's mechanism is confirmed and the two arms are diversifying
for a *reason* rather than by coincidence. **If both move the same way, the ρ ≈ 0.16 measured
twice was luck**, and the case for the pairing is much weaker than it looks.

---

## Stop

**If either entry fails V1 on the new period, it is amended in `BOOK.md` in writing** — with the
sub-period result recorded as a demonstrated weakness — not quietly dropped and not re-cut. R8's
append-only rule binds.

**No new rule may be proposed in this record.** If something fails, it fails; the response is a
separate pre-registration, not a fix appended here.

---

## Ledger

| count | N |
|---|---:|
| fresh — **0 cells.** Two frozen rules and their union, on new data | **0** |
| + D242's 3, D241's 5, D240's 5, D239's 3, D238's 4, D234's 6, D235's 7, D236's 6 | 39 |
| + the gradient anatomy | 60 |
| + disclosed ETF prior | **45,863** |

**Nothing is searched here**, so the count does not move. That is the point of running only the
book.

## Reuse — D212 is binding

Everything. `books_on` from `run_uptrend_withheld` already repoints the loader at an arbitrary
fixture; the scorers, nulls, allocator and bootstrap are all committed and tested. **Written
fresh: the sub-period split, and nothing else.**

## Verification

- The frozen constants are asserted against `run_uptrend_onset`'s.
- **The old fixtures must still reproduce their published numbers** — +0.746 and +0.610 mined,
  +0.779 and +0.672 on the holdout. A runner that cannot is measuring something else.
- **The new fixture's span and symbol set are asserted**: 57 symbols, 4,222 bars, first bar
  2009-11-11.
- **No look-ahead across the join:** the sub-period split is applied to *scored returns*, never
  to the signal, so the pre-2018 window is scored with exactly the warm-up it would have had.

---

## VERDICT

**Produced:** 2026-08-28 · `uv run python scripts/run_book_extended.py` · Page:
[`BOOK_EXTENDED_RESULTS.md`](../results/BOOK_EXTENDED_RESULTS.md)

**3,222 live bars from 2013-11-01.** NEW 1,293 · TRAIN 1,516 · FORWARD 413.

### The one-sentence version

**S1 goes NEGATIVE in the never-seen era and fails all three hurdles; S2 clears all three — and
D239 predicted exactly this, from a mechanism derived before either result existed.**

### The verdict window — never seen

| | **NEW** | *TRAIN* | B&H on NEW | Δ vs B&H | floor | rot null pctile | V1 | V2 | V3 |
|---|---:|---:|---:|---:|---:|---:|:--:|:--:|:--:|
| **S1** | **−0.123** | *+0.752* | −0.149 | +0.025 | +0.128 | **80.6th** | ✗ | ✗ | ✗ |
| **S2** | **+0.248** | *+0.521* | −0.149 | **+0.396** | +0.094 | **97.1th** | ✓ | ✓ | ✓ |

**S1's excess Sharpe over 2013–2018 is negative.** It beat buy-and-hold by +0.025 — a fifth of
its floor — and sat at the **80.6th percentile** of its own rotation null, the first time it has
ever failed one. On the mined and holdout fixtures it was at the 100th.

**S2 cleared everything**, with a delta over buy-and-hold of **+0.396 against a floor of +0.094**
— four times over — and a rotation null at the 97.1st percentile.

### Every period

| | NEW | TRAIN | FORWARD | FULL |
|---|---:|---:|---:|---:|
| S1 | **−0.123** | +0.752 | +0.896 | +0.478 |
| S2 | +0.248 | +0.521 | **+1.504** | +0.511 |
| **C** | +0.023 | +0.839 | +1.528 | **+0.620** |
| *B&H* | *−0.149* | *+0.249* | *+1.235* | *+0.242* |

**2013–2018 was hard for this universe** — buy-and-hold itself scored **−0.149**, dragged by the
commodity and emerging-market collapse. That makes it a demanding test, and S1 failed it while
the market was also failing.

### V4 — the intervals, and doubling the data did its job

| | excess Sharpe | p05 | **excludes 0** | Δ vs B&H | p05 | excludes 0 |
|---|---:|---:|:--:|---:|---:|:--:|
| S1 | +0.478 | −0.036 | ✗ | +0.236 | −0.198 | ✗ |
| **S2** | +0.511 | **+0.066** | **✓** | +0.269 | −0.134 | ✗ |
| **C** | **+0.620** | **+0.126** | **✓** | **+0.378** | **+0.036** | **✓** |

**For the first time in this programme, an interval excludes zero — and the combination beats
buy-and-hold with an interval that excludes zero too.** That is what six more years bought.

**And S1's headline number was inflated by its sample.** +0.746 over 6.0 years becomes **+0.478**
over 12.8. The number in `BOOK.md` was never wrong; it was measured on a window that happened to
suit it.

### Money, over the longer span — and a correction

| | exposure | CAGR | **deployable** | max DD | Calmar | E |
|---|---:|---:|---:|---:|---:|:--:|
| S1 | 18.2% | 3.11% | 6.47% | −10.28% | 0.303 | ✗ (20) |
| S2 | 13.3% | 1.85% | 5.37% | −5.83% | 0.318 | ✗ (5) |
| **C** | 30.5% | 4.83% | **7.73%** | **−10.40%** | **0.465** | ✗ (24) |
| *B&H* | *100%* | *7.84%* | *7.84%* | *−34.55%* | *0.227* | — |

**Correction to what D241 and D242 supported.** On the six-year windows the combined book beat
buy-and-hold on money *and* drawdown. **Over 12.8 years it does not beat it on money** — 7.73%
against 7.84%. It wins decisively on risk (Calmar 0.465 against 0.227, drawdown −10.40% against
−34.55%) and on risk-adjusted return with an interval that excludes zero. **But "beats
buy-and-hold on money" was a six-year fact and does not survive the longer sample.**

**Hurdle E improved as predicted** — S1 from 9 to **20** entries per symbol, the combination to
**24**. Still short of 30, and S2 remains at 5.

### Scoring — two confirmed, one split, two falsified

| | prediction | outcome |
|---|---|---|
| **W1** | S1 does worse on the new period | **CONFIRMED**, and far worse than intended — it went negative |
| **W2** | S2 does better on the new period | **SPLIT.** Absolutely it fell (+0.248 vs +0.521); **relative to buy-and-hold it rose** (+0.396 vs +0.272), which is the comparison that carries the mechanism |
| **W3** | both still clear V1 and V2 | **FALSIFIED.** S1 fails both |
| **W4** | S1's interval excludes zero on the full span | **FALSIFIED** at p05 −0.036 — but **S2's and the combination's do** |
| **W5** | the combination's delta over S1 still fails | **CONFIRMED**, p05 −0.052 |

**ρ between S1 and S2 held at +0.1233** across 12.8 years, against +0.159 mined and +0.175 on
the holdout. **Measured three times on three spans, and stable.** The diversification is
structural.

### What this means, plainly

**D239's mechanism is confirmed by a prediction registered before the data existed.** That record
found trend-following was an *anti-signal* on 2018–2024 and concluded S1's edge is partly a bet
that reversals beat continuations. 2013–2018 was a continuation-dominated grind. **S1 went
negative there and S2, the continuation arm, beat the market by four times its floor.** The two
arms are not merely uncorrelated — they are opposite sides of one regime variable, and each
covers the other's bad era.

**That is a better reason to hold both than the ρ number ever was.**

### The stop applies as written

**S1 is amended in `BOOK.md` in writing** — not dropped, not re-cut — with the sub-period result
recorded as a demonstrated weakness and its headline Sharpe restated at +0.478 over the full
span. D243 committed this before the run.

**S2's entry gains this evidence.** It has now cleared a pre-registered instrument holdout
(D242) *and* a pre-registered time holdout (here), which no other rule in this programme has
done.

**No new rule is proposed here.** If S1 needs a regime filter, that is a separate
pre-registration, and this record does not open it.

### Ledger

| count | N |
|---|---:|
| **fresh — 0 cells** | **0** |
| + D242's 3, D241's 5, D240's 5, D239's 3, D238's 4, D234's 6, D235's 7, D236's 6 | 39 |
| + the gradient anatomy | 60 |
| + disclosed ETF prior | **45,863** |
