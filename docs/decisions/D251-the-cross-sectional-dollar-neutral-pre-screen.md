# D251 — Cross-sectional dollar-neutral ranking scores: a pre-screen

**Status:** Screened and CLOSED — no rule proposed, no hurdle run, no null computed.
**D245's never-seen cohort was NOT touched and remains reserved for S3.**
**Date:** 2026-08-28
**Area:** Strategy research

---

## What this is, and what it deliberately is not

**This is a pre-screen, in [D250](D250-the-overnight-gap-pre-screen.md)'s shape and under
[D246](D246-the-search-protocol-for-s3.md)'s protocol.** Measure the conditional cheaply first,
R9- and R10-compliant; only pay for a runner if it clears a stated economic bar.

**The bar was stated as a product before any number was printed**, per D250's own correction:
`gross = exposure x edge`, net of two-leg costs and borrow, **> ~2%/yr**.

Artifacts: `scripts/prescreen_cross_sectional.py`, `data/cross_sectional_prescreen_summary.json`,
`CROSS_SECTIONAL_PRESCREEN_RESULTS.md`. 57 ETFs x **3,222 live bars**, 2013-11-01 → 2026-08-26,
costs **1.93 bp/side** median, borrow 1.0%/yr on short notional. Seed 0, 5.7 seconds.

---

## Why this was the eligible family

D246 named cross-sectional dollar-neutral as one of two families that survive its constraints,
and the argument sharpened into something measurable:

**An ETF is a weighted average, so diversification removes idiosyncratic variance by
construction. What remains is the common factor — and the common factor is exactly what carries
the equity risk premium.** Everything the programme has measured points the same way:
[D238](D238-the-short-side-mirror.md)'s short mirror beat the name's own drift on 42 of 46 equity
ETFs, five directional short constructions have died on +9.02%/yr of drift, and effective
independent instruments saturate near 2.2 regardless of headcount.

**Dollar-neutral is the one construction that removes the factor rather than fighting it.**

### And the premise checks out — this is the part that is NOT a null

| | effective independent directions |
|---|---:|
| equal-weight estimator, raw returns (BOOK.md's number, reproduced) | **2.29** |
| eigenvalue participation ratio, raw returns | **3.61** |
| **eigenvalue participation ratio, market-neutral residuals** | **11.55** |

**Removing the common factor triples the breadth.** The motivating argument was right. *The
argument being right and the family paying are separate claims, and only the first one survived.*

*A note on estimators, because it matters. `run_book_wide.effective_instruments` is `n²/sum(R)`,
which is `1/Var` of the equal-weighted average — exactly right for a long-only equal-weighted
book and **degenerate here**, since market-neutral residuals sum to zero across names and their
equal-weighted average is identically zero. The participation ratio is the measure a signed-weight
book gets to use.*

---

## The eight cells, declared with their direction before the run

D246 stops screening at 8 cells. **This is exactly 8**, each scored at two horizons.

| cell | score, all from bars ≤ t | a priori long leg |
|---|---|---|
| **RS21 / RS63 / RS252** | trailing 21/63/252-bar return minus the equal-weighted universe | Q5 (high) |
| **RESMOM** | residual momentum — beta and alpha from the 252 bars ending at `t−252`, residual accumulated over the 252 bars ending at `t`, standardised | Q5 |
| **IVOL** | trailing residual sd, annualised — low-vol anomaly | **Q1 (low)** |
| **BETA** | trailing slope on the universe — betting-against-beta | **Q1 (low)** |
| **MDL** | S1's `md_L`, divided by its own trailing 252-bar sd | **Q1 (low)** |
| **HISTL** | S1's `hist_L`, same normalisation | Q5 |

**The direction is declared so a spread of the wrong sign cannot be re-read as a spread of the
right sign.** Two cells duly came back with the wrong sign and are reported as failures, not
flipped.

**Two construction choices are part of the cell definition, not extra looks.** (1) RESMOM's
estimation and accumulation windows do not overlap, because OLS residuals sum to zero over their
own estimation window and the nested version is degenerate by algebra. (2) MDL and HISTL are
scale-free, per [D232](D232-the-scale-corrected-impulse-macd.md): `md_L` is a dimensionless log-gap
but still scales with the name's volatility, so a raw cross-sectional rank on it is mostly a
volatility sort wearing a signal's name.

---

## Result 1 — the spread table, which is where the candidate looked alive

Pooled forward return by quintile of the lagged score, annualised. `h = 63`:

| cell | Q1 | Q2 | Q3 | Q4 | Q5 | **edge** | turnover | cost | borrow | **net** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| RS21 | +7.15% | +8.32% | +9.01% | +8.59% | +5.46% | −1.69% | 78% | 0.23% | 1.00% | −2.92% |
| RS63 | +8.02% | +8.62% | +8.50% | +7.60% | +5.73% | −2.29% | 77% | 0.23% | 1.00% | −3.52% |
| RS252 | +6.57% | +7.69% | +8.02% | +8.15% | +8.20% | +1.62% | 38% | 0.11% | 1.00% | +0.51% |
| **RESMOM** | +5.91% | +7.51% | +7.38% | +7.29% | **+10.71%** | **+4.80%** | 50% | 0.15% | 1.00% | **+3.66%** |
| IVOL | +7.26% | +9.57% | +8.56% | +9.55% | +3.67% | +3.59% | 7% | 0.02% | 1.00% | +2.57% |
| BETA | +2.91% | +7.54% | +8.95% | +11.11% | +8.54% | **−5.63%** | 12% | 0.03% | 1.00% | −6.67% |
| MDL | +7.93% | +7.52% | +7.06% | +9.47% | +6.63% | +1.30% | 73% | 0.21% | 1.00% | +0.08% |
| HISTL | +6.65% | +7.77% | +8.53% | +8.98% | +6.65% | −0.00% | 86% | 0.25% | 1.00% | −1.25% |

**Turnover is measured, not assumed** — assuming 100% would have overstated the cost by 2–30x,
and the costs are trivial regardless. **Borrow, at a flat 1.0%/yr on the short leg, is larger than
every trading cost in the table.** Five cells clear the 2% bar on this reading.

**And this table is wrong, in a way that is the whole finding.**

---

## Result 2 — the books, and the term the invariant was missing

Every cell was then built as an actual matched-count dollar-neutral book — long one extreme
quintile, short the other, `lag = 1`, rebalanced every `h` bars — and scored with D238's signed
scorer. **All sixteen lose money.**

| `h = 63` | long leg | **short leg** | short leg *priced naively* | **convexity cost** | **book at 100/100** |
|---|---:|---:|---:|---:|---:|
| RS252 | +8.23% | −15.13% | *−6.33%* | **8.79 pts** | **−6.94%** |
| **RESMOM** | +9.61% | −11.83% | *−5.59%* | **6.24 pts** | **−2.41%** |
| IVOL | +6.66% | −18.73% | *−4.02%* | **14.70 pts** | **−11.71%** |
| BETA | +2.62% | −19.53% | *−8.49%* | **11.05 pts** | **−15.88%** |

**The gap between the spread table and the book is the short leg's convexity, and it is 6.2 to
14.9 points a year.** A daily-rebalanced short earns `log(2 − e^r)`, whose expectation is
`−mu − sigma²`; at 20–25% name volatility that is 4–6%/yr, and it is larger still on the
high-volatility baskets IVOL and BETA short. **This is D238's `+9.22 percentage points` — the same
number, arrived at from the other side.**

> **The invariant needs a third term for a two-sided book:**
> **`gross = exposure x edge − short-leg convexity`.**
>
> A cross-sectional spread table is stated in a coordinate system where shorting is free of
> variance drag. It is not. **A quintile spread of `s` does not deliver `s` to a short-leg book,
> and on this universe it delivers `s` minus six to fifteen points.** That is why five cells
> cleared the bar on the table and none cleared it as a book.

**This generalises past this family**, in the same way D250's selectivity finding did: any future
long-short screen that prices its short leg off a return table is reading a number that does not
exist. It is the exact mistake `pos * log_return` makes, wearing different clothes.

---

## Result 3 — a disclosed second aggregation, which does not rescue it

`signed_log_returns` averages **per-symbol** log growths, so each name is its own compounding
sleeve. That is right for a long-flat book and it charges a dollar-neutral book the **name-level**
variance drag. In a real dollar-neutral account both legs sit in one equity — the long leg's gain
funds the short leg's loss on the same bar — so the drag is set by the **spread's** variance
(3.4% vol here), not by each name's.

**A portfolio-level aggregation was therefore computed and is disclosed as a post-hoc look**, not
substituted for the mandated scorer. It is `log1p(mean_i(pos_i · expm1(r_i)) − costs)` — *not*
`pos * log_return*`, and pinned identical to the house scorer on a one-symbol universe so the
difference is provably aggregation and not a second defect.

**It flips the sign and it does not clear the bar:**

| best cell, portfolio-level | | |
|---|---:|---|
| **RESMOM @ 63** CAGR at 38.6% gross exposure | **+0.82%/yr** | |
| net of borrow | **+0.63%/yr** | needs **~3.2x leverage** to reach the 2% bar |
| **Sharpe** | **+0.237** | *and leverage does not move this* |
| first half / second half | **+0.45% / +1.19%** | |
| ex-2020 | +0.40% | |
| top-10 days' share of P&L | **101%** | |
| independent 63-bar periods | **51** | |

**The bar is stated as a return, and a return can always be bought with leverage. The Sharpe
cannot.** At +0.237 over 51 independent periods, against S2's +0.511 with an interval that
excludes zero, this does not earn a pre-registration under either aggregation.

---

## Result 4 — what each score actually said, since three of them said something

**RESMOM is the only monotone relationship in the study** — +5.54 / +7.23 / +7.75 / +7.88 /
+10.76 at `h = 21` — and it is the cleanest cross-sectional signal this programme has found. Its
net beta is **−0.14**, so it is a genuine cross-sectional bet and not a disguised market
position. **It is also entirely an artefact of the second half**: −0.08%/yr in the first, +1.30%
in the second. D250 Result 3's shape exactly.

**Short-horizon relative strength is REVERSAL, not momentum.** RS21 and RS63 both put Q1 above
Q5, so both fail in their declared direction. *Disclosed complement, and counted:* reversed,
RS63 @ 63 would show +2.29% gross, **+1.06% net** — still under the bar, and a complement-chase
that [D246 Constraint 3](D246-the-search-protocol-for-s3.md) forbids anyway. It is recorded so
nobody re-derives it as a discovery.

**Betting-against-beta is inverted here and is the worst cell in the study**, at −5.63% in its
declared direction. The profile is non-monotone (+2.91 / +7.54 / +8.95 / **+11.11** / +8.54): the
lowest-beta quintile is bad, the fourth is best. **Its net beta is −1.27** — a BAB book on this
universe is a levered short of the market wearing a factor's name, and it lost accordingly over an
era the market rose in.

**Low idiosyncratic volatility "works" for the same disqualifying reason.** +3.59% in its declared
direction, but non-monotone (only Q5 is bad) and **net beta −0.74**. It is a short-the-market
position, not a cross-sectional one.

**S1's own signals do not rank the cross-section.** MDL +1.30% and HISTL −0.00% at `h = 63`, both
inside noise, both at 73–86% turnover. **`md_L` and `hist_L` are level rules and do not survive
being turned into ranks** — which is a real, if unexciting, answer to a question worth asking.

---

## R10, and why its literal form cannot fire on this construction

**A fixed-count cross-sectional sort holds the same headcount every day**, so it is *less* crowded
than its own rotated null — rotation breaks the exact-count property and lets the extremes bunch
(actual max 23 of 57 against a rotated 34.9). **The concurrency test cannot fail here, and a test
that cannot fail is not evidence** — R7's corollary, applied to a diagnostic rather than a hurdle.

**The binding form of R10 for this family is net beta**, reported beside every table, and it fired
twice: BETA at **−1.27** and IVOL at **−0.74** are market-timing books that a dollar-neutral
headcount constraint failed to catch. **Matched notional is not matched exposure.** That
distinction should be carried into any future long-short registration.

---

## What is closed, and what is not

**Closed: these eight ranking scores, on this universe, as dollar-neutral quintile books.**
Not closed: the family. D246 named it and D245's cohort is still unspent — but **the entry price
just went up by six to fifteen points a year**, and a future candidate has to clear the
convexity term explicitly rather than be screened on a spread table.

**Also not closed, and it is now the sharper question:** whether the house scorer's per-symbol
aggregation is the right one for a two-sided book. It is right for every book the programme has
scored so far and **it is a 6.6-point swing on this one**. That is a methodological item, not a
strategy, and it belongs in `AITODO.md` rather than in a hurdle.

**What was not spent.** D245's never-seen wide-universe cohort. D246 permits one candidate; none
earned it, so it remains reserved, and this record exists partly to say so in writing.

**Cost:** one script, one afternoon, no pre-registration, no runner, no test module, no null.
**That is the second time D250's inversion has paid**, and the thing it caught this time was not
a weak signal — RESMOM is the best cross-sectional relationship in the programme's history — but
a **missing term in the economics** that a full study would have discovered after the
pre-registration was already committed.

---

## Predictions, retrospectively scored

D246's **S-b** predicted cross-sectional dollar-neutral would screen better on D245's wide
universe than on the 57, *"because a decile stops being six lumpy sector funds"*. **That
prediction is not resolved and should not be scored** — the binding constraint turned out to be
the short leg's convexity, which is a property of the instruments and not of the headcount, and
**a wider universe does not fix it.** Recorded so S-b is not later marked correct or incorrect on
evidence that never addressed it.

---

## Ledger

| count | N |
|---|---:|
| 8 ranking scores x 2 horizons | 16 |
| the portfolio-level re-aggregation of the same 16 books (disclosed, Result 3) | 32 |
| 2 half-splits + the 2020 exclusion, applied uniformly | 35 |
| the disclosed reversed-sign reading on RS63 | 36 |
| carried from D250 | 45,936 |
| **total** | **45,972** |
