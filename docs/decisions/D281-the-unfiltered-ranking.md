# D281 — The unfiltered ranking

**Status:** PRE-REGISTERED. Committed **before the runner exists**. Nothing here is a result.
**Date:** 2026-09-02
**Area:** Strategy research · **personal track**

---

## Why this exists — the filter and the ranking are the same variable

[D279](D279-the-concentrated-short-on-dead-inclusive-names.md) held the top N of the **qualifying**
set, where qualifying means `hist_L < 0 & md_L >= 0`, and ranked the survivors by **`hist_L`
ascending**. [D256](D256-the-book-on-single-names.md) built the same qualifying set and held all of
it. **In both, the variable that selects the population and the variable that orders it are the
same number.**

`data/d280_score_extrapolation.json` measured what that costs. Cross-sectional Information
Coefficient — Spearman, **within bar**, lagged score against the **NEXT** bar's return, out of
sample from **2018-01-01**, minimum 20 names per bar:

| population | score | mean IC | t | bars | reading |
|---|---|---:|---:|---:|---|
| **ALL live names** | `hist_L` | **−0.00524** | **−1.79** | 2,173 | **correctly signed for a short** — ranks ascending, so a negative IC is tradeable |
| **QUALIFYING ONLY** (`hist_L < 0 & md_L >= 0`) | `hist_L` | **+0.00462** | +1.43 | 2,147 | **WRONG SIGN** |

**The sign flips when the filter is applied.** The filter spends the signal; ranking the survivors
by the same variable re-uses a number that has already done its work, and what remains inside the
qualifying set points the other way.

**D281 removes the collision and does nothing else: rank the WHOLE universe, no qualifying
filter.** This is the one construction in the D256/D279 family where the ranking is asked a
question the filter has not already answered.

**D280 is a measurement, not a study.** It scores no cell, admits no candidate, and clears no
hurdle. It is disclosed in the ledger below because it **shaped this search space** — under
[R13](../RULES.md#r13) that is the test that matters, not whether it produced a return.

---

## The fixture

`us_shorts_daily_raw.csv.gz` — **1,573 names, 4,137,239 rows, 2010-01-04 → 2026-08-26, RAGGED.**
**562 carry a delisting date (35.7%)**, 122 more collapsed while listed. Loaded through
`RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=B.FEE_BPS)` where `B = scripts/run_book_single_names.py`
— per-symbol live windows, **equal weight over LIVE names**, delisting as an exit with no
foreknowledge, no forward-filled prices.

D252's own caveat is carried rather than paraphrased: it *"deliberately contains dead companies and
is still not free of survivorship bias"* — provider coverage records 40–76 delistings a year for
2009–2012 against 700–1,000 after 2016, so **the dead cohort is materially under-sampled early in
the span.**

---

## The construction — one change from D279

```
D279     base = -hold_book(hist_L < 0 & md_L >= 0)     then rank the survivors by hist_L
D281     base = -hold_book(scored & warm)              then rank ALL of them by hist_L
```

```
universe  every LIVE, WARM name with a finite (md_L, hist_L) pair.
          NO `hist_L < 0` filter. NO `md_L >= 0` filter. The mask keeps
          D279's finiteness-and-warm-up condition and DROPS BOTH VALUE
          CONDITIONS, so the universe here is exactly D279's superset.

score     hist_L, LAGGED ONE BAR, ascending. Most negative acceleration
          ranks first, which is the strongest short.

arm       short the N lowest-lagged-hist_L names among all live warm
          names at each bar. N in {10, 25, 50}.

frozen    5 bp/side, borrow 3%/yr, rf 4%, PPY 252, Impulse 34/9,
          window 252, seed 0, 300 null draws. Nothing is varied.
```

### The lag is the correctness requirement, and it has already failed once here

**D279's first result was entirely look-ahead.** `top_n` ranked with `score[:, t]` — the close of
the very bar the position was about to be paid for — instead of `score[:, t-1]`. Measured, not
argued: `corr(hist_L at t, return at t) = +0.0737` against `corr(hist_L at t-1, return at t) =
−0.0103`. `top25` scored **+2.250 Sharpe unlagged and −0.638 lagged.**
`scripts/d279_lookahead_check.py` is the diagnostic that caught it.

**D281 reuses `C.top_n` and `C.lag1` from `scripts/run_concentrated_short.py`, which now lag
internally and unconditionally**, and the runner **must** carry its own positional check: for every
bar, the held set is re-derived from `score[:, t-1]` in a second, independent implementation and
asserted equal to the book actually scored. **A failed assertion aborts the run.** That check is
reported with the result whether or not it passes.

---

## The controls — matched count is NOT matched turnover

D279 learned this the expensive way, and **both** controls are pre-registered here.

| | control | what it matches | why it is not enough alone |
|---|---|---|---|
| **`rnd-N`** | N names drawn at random **each bar** | count, bars, N | **churns ~5–6× harder than a ranked book** and pays ~5–6× the fees. A weak control: it differs from the treatment in *two* ways, selection and turnover |
| **`per-N`** | **persistent** random — draw at random, then HOLD the draw while the name is still live, refilling only vacancies | count, bars, N, **and turnover** | this is the control hurdle C should always have carried |

`per-N` is `persistent_rnd` copied from `scripts/d279_turnover_decomposition.py`, unchanged.

### Every cell is reported NET and GROSS

**GROSS = zero fees, zero borrow, zero rf** — the same zero-cost panel construction as
`d279_turnover_decomposition.py`, which rebuilds the panel with `cost_fraction` zeroed.

**On this daily fixture the book loses GROSS**, so costs are not the binding constraint and **the
gross number is the informative one.** A cell that fails gross cannot be rescued by a cost
assumption, and a cell that clears only on net is a statement about the control's turnover rather
than about the ranking.

---

## Hurdles

| | standard |
|---|---|
| **V** | **Positive net CAGR** after fees, financing and borrow |
| **C** | **Beats BOTH controls — `rnd-N` and `per-N` — on Sharpe AND on money, GROSS and NET.** Four comparisons per control, eight per cell, all required |
| **F** | **Best-of-K floor** ([D228](D228-mining-the-mined-fixture.md)), one shared offset vector, **K = 10**, the total cell count of this study |
| **E′** | **Effective independent instruments ≥ 3.0 over the HELD BOOK** — `eff_over_book` from `scripts/d279_fix_eprime.py`, **NOT** `RP.effective_instruments(panel, ...)` — and **≥ 500 pooled trades** |
| **H** | Rotation null, **REPORTED BUT NOT DECISIVE.** See below |

### E′ uses the corrected estimator, and the defect it corrects is named

D279's runner called `RP.effective_instruments(panel, 0)`, which measures the whole **1,573-name
panel** and returned **5.44 for every cell** — a hurdle whose entire job is to tell a ten-name book
from a twelve-hundred-name book, scoring them identically. `eff_over_book` takes correlations on
bars where **both names were HELD**, not merely live. **That is the estimator D281 uses.**

**And its known weakness is declared in advance:** in a rotating top-N book almost no *pair* shares
250 held bars, so the correlation matrix tends to the identity and E′ degenerates into *"how many
names accumulated 250 held bars"*. **It is a headcount dressed as a breadth measure.** It is
retained because it was pre-registered in D279 and because dropping a hurdle after seeing what it
does to a grid is exactly the move this programme does not make — but **no verdict here rests on
E′ alone**, and per-symbol P&L concentration is reported beside every cell as the thing E′ was
supposed to guard.

### Hurdle H is broken on this fixture and carries no verdict

D279 established it under [R7](../RULES.md#r7)'s corollary — *a hurdle that everything clears is not
evidence, it is a broken hurdle*:

> `S1_short|all` scores the **100th percentile on both legs** with **−0.757 Sharpe** and **−2.45%
> CAGR**. Its null distribution sits at **p50 −1.058 / p95 −0.986.**

**A rotation null on a near-always-on book is worse than uninformative here — it is nearly the
identity.** D281's unfiltered base holds essentially every live warm name every bar, and rolling a
constant within a symbol's own window returns that constant. **H is computed, printed, and
explicitly excluded from every verdict.** The verdicts rest on **V, C and F**, with E′ as a
disclosed side condition.

---

## The bar this must clear, in numbers, before the run

From D279's **corrected** decomposition (post-lag-fix, `data/d279_turnover_decomposition.json`), in
**GROSS Sharpe**:

| | gross Sharpe |
|---|---:|
| turnover-matched random, `per25` | **−0.635** |
| the **filtered** `hist_L` ranking, `top25` | **−0.432** |
| **what the filtered ranking adds** | **+0.203** |
| the cost step, `top25` net −0.638 vs gross −0.432 | **−0.206** |

**To reach zero gross from −0.635, D281's ranking must add more than +0.635 — more than THREE times
what the filtered ranking manages — and the ~0.206 cost step comes after that.**

**The Grinold prior says it will not.** `IR ≈ IC × sqrt(breadth)`. At `IC = −0.00524` and a breadth
of 252 bars/yr × 5.44 effective independent instruments ≈ 1,371 independent bets per year,
`sqrt(BR) ≈ 37` and **`IR ≈ 0.19`**; on the most generous defensible breadth the figure reaches
roughly **+0.3**. That is **1.0–1.5× the filtered ranking's +0.203**, and **less than half of the
+0.635 needed to reach zero gross.**

**So the honest prior, written down before the run: this construction IMPROVES the book and does
not reach positive.** If it reaches positive gross, the Grinold arithmetic above is wrong by more
than a factor of two and that is the finding, not the return.

---

## Predictions

| | prediction | direction | confidence |
|---|---|---|---|
| **U1** | **The unfiltered ranking beats `per-N` on GROSS Sharpe at all three N**, and by **more than the filtered ranking's +0.203** at N = 25 | **for** the construction | **moderate** |
| **U2** | **No cell reaches positive GROSS Sharpe.** Every top-N cell stays below zero at zero fees, zero borrow, zero rf | **AGAINST** | **high** |
| **U3** | **Hurdle V fails everywhere — no cell posts a positive net CAGR**, so no cell clears V, C and F together and the stop below fires | **AGAINST** | **moderate-high** |
| **U4** | **The gross ranking contribution over `per-N` DECLINES monotonically in N** (10 > 25 > 50), because a wider slice dilutes toward the unconditional short. D279's filtered figures were +0.223 / +0.204 / +0.202 | neutral | **moderate** |

**U2 and U3 are declared against the construction and U2 is the load-bearing one.** If U2 is wrong
— if removing the filter/ranking collision lifts a daily single-name short to positive gross Sharpe
against a turnover-matched control — then D280's IC measurement understates the tradeable signal by
more than a factor of two, and **that** is the result, ahead of any cell's CAGR.

**What would falsify U1:** `top-N` failing to beat `per-N` gross at any N, or beating it by less
than the filtered ranking already does. That outcome says the ALL-names IC of −0.00524 does not
survive translation into a top-N book — most likely because a top-N cut samples the extreme tail of
`hist_L`, not the whole cross-section the IC was measured over.

---

## Stop

**If no cell clears V, C and F, the unfiltered ranking is closed.** No fourth N, no alternative
score, no re-cut of the universe, no second population. **Nothing is tuned after a result is seen.**

Together with D256 (the universe) and D279 (the construction), a failure here **closes the
dead-inclusive daily fixture for `hist_L`-ranked directional shorts** — the three studies between
them have tested holding everything that qualifies, holding the top N of what qualifies, and
holding the top N of everything.

**If a cell clears, it is not a book entry.** Under [R8](../RULES.md#r8) admission requires a
pre-registered out-of-sample test, and **this fixture has no untouched cohort left.** D246's
reserved wide-universe cohort is a different fixture and is not spent here.

---

## Ledger

Under [R13](../RULES.md#r13) — scoped to a hypothesis, carried where it shaped the search.

| count | N | why |
|---|---:|---|
| **fresh — 3 N × 3 modes (`top`/`rnd`/`per`), + 1 unfiltered base** | **10** | controls are counted like anything else; D228's floor does not care what a cell was built to prove |
| carried: **D279**, 14 pre-registered + 6 persistent controls | 20 | same fixture, same arm family, same score |
| carried: **D256** | 21 | same fixture, same arms, and D279 carried it for the same reason |
| **total** | **51** | |

**D280 is disclosed and scores NO cell.** It is a cross-sectional IC measurement that admits no
candidate and clears no hurdle — but it **shaped this search space**, which is R13's second test,
so it is named here rather than left implicit. An undisclosed exclusion is indistinguishable from
an oversight.

**NOT carried:** the single-name **intraday** programme (D264–D278, ~430) — different fixture,
different frequency, and the construction tested here was named by
[FINDINGS §9](../FINDINGS.md) before that programme began. The ETF programme's 45,783 is not
carried for the reasons R13 already records.

---
