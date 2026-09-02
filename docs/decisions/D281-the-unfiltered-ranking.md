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
---

# RESULT — appended 2026-09-02, after the run

**`scripts/run_unfiltered_ranking.py`, seed 0, 300 null draws, 1,223s. Artifact:
`data/d281_unfiltered_summary.json`. Console: `data/d281_run.log`.**

**SURVIVORS: NONE. No cell clears V. No cell clears C. No cell clears F. The stop fires.**

**And the failure is not a near miss — it is the wrong sign.** The unfiltered `hist_L` ranking does
not merely fail to add the +0.635 gross Sharpe it needed. **It SUBTRACTS**, losing to a random
control at all three N, gross and net.

## The lag audit — the check D279 failed, run first and reported whether or not it passed

| | |
|---|---:|
| `corr(hist_L at t, return at t)` | **+0.0737** — ranking on this is peeking |
| `corr(hist_L at t-1, return at t)` | **−0.0103** — the tradeable version |
| bars re-derived from `score[:, t-1]` and **matched**, each N | **3,186 / 3,186** |
| mean cross-sectional percentile of held names, **lagged** score | 0.0055 · 0.0146 · 0.0299 |
| mean cross-sectional percentile of held names, **contemporaneous** score | 0.0073 · 0.0176 · 0.0346 |

**The book is lagged.** Held names sit deeper in the *lagged* distribution than in the bar's own —
the opposite of the D279 defect, which held names already at the bottom of the bar being paid for.
`audit_lag` is a second implementation that does not call `top_n`, so it could have disagreed; it
did not, on any of 9,558 bar-cells.

**The universe is what was pre-registered:** 2,621,967 unfiltered name-bars against 703,602
qualifying. **The qualifying set is 26.8% of the universe D281 ranks.**

## The grid — every cell NET and GROSS

GROSS is zero fees, zero borrow, zero rf. `top` is the ranking; `rnd` redraws every bar;
`per` draws once and holds.

| cell | expo | turnover | **net CAGR** | **net SR** | **GROSS CAGR** | **GROSS SR** | maxDD | trades |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `hist_L\|all` | 61.54% | 2,403 | **−9.50%** | −0.760 | −9.50% | −0.632 | **−82.52%** | 1,675 |
| **`hist_L\|top10`** | 0.75% | 10,162 | −0.41% | **−0.969** | −0.38% | **−0.853** | −6.81% | 5,086 |
| `hist_L\|rnd10` | 0.75% | 62,922 | −0.31% | −1.551 | −0.12% | **−0.573** | −5.00% | 31,466 |
| `hist_L\|per10` | 0.75% | 18 | −0.14% | −0.798 | −0.13% | **−0.686** | −2.34% | 14 |
| **`hist_L\|top25`** | 1.87% | 22,497 | −0.70% | **−0.911** | −0.63% | **−0.764** | −11.10% | 11,261 |
| `hist_L\|rnd25` | 1.87% | 154,465 | −0.79% | −1.768 | −0.33% | **−0.698** | −12.41% | 77,245 |
| `hist_L\|per25` | 1.87% | 51 | −0.30% | −0.768 | −0.30% | **−0.648** | −4.96% | 38 |
| **`hist_L\|top50`** | 3.74% | 40,984 | −1.05% | **−0.796** | −0.93% | **−0.636** | −16.89% | 20,517 |
| `hist_L\|rnd50` | 3.74% | 299,270 | −1.43% | −1.723 | −0.56% | **−0.616** | −21.34% | 149,660 |
| `hist_L\|per50` | 3.74% | 116 | −0.45% | −0.653 | −0.45% | **−0.523** | −7.88% | 83 |

Best-of-10 floor: **−0.230**. **Nothing in the study exceeds it.**

**Breakeven borrow is NEGATIVE in all ten cells** (−8.7% to −40.6%). **No borrow rate makes any of
them profitable, zero included.** D279's primary cost statistic is not even reachable here.

## The decomposition — this is the study

| N | vs `rnd` net | **vs `rnd` GROSS** | vs `per` net | **vs `per` GROSS** | turnover ratio |
|---:|---:|---:|---:|---:|---|
| 10 | +0.581 | **−0.280** | −0.171 | **−0.167** | rnd 6.2× · per 0.002× |
| 25 | +0.858 | **−0.065** | −0.143 | **−0.116** | rnd 6.9× · per 0.002× |
| 50 | +0.927 | **−0.019** | −0.143 | **−0.113** | rnd 7.3× · per 0.003× |

**Read the GROSS columns. Every one is negative.** The unfiltered ranking is worse than random
selection at zero fees, zero borrow and zero rf, against **both** controls, at **all three** N.

**The two controls bracket the ranked book on turnover from opposite sides, and it loses to both.**
`rnd-N` churns **6–7× harder**; `per-N` churns **~440× less**. The ranked book sits between them,
so its gross loss cannot be a turnover artefact in either direction. **The net columns against
`rnd-N` are positive purely because `rnd-N` pays 6–7× the fees** — precisely the confound D279
found, reproduced here, and precisely why gross was pre-registered as the informative number.

### Against the bar written down before the run

| | gross Sharpe over `per25` |
|---|---:|
| what D279's **filtered** ranking added | **+0.203** |
| what was needed to reach **zero gross** | **+0.635** |
| Grinold prior at IC −0.00524, written down in advance | **≈ +0.19**, up to +0.3 |
| **what D281's unfiltered ranking actually added** | **−0.116** |

**The magnitude of the Grinold estimate was about right and its SIGN was wrong.** Predicted |0.19|,
observed |0.113–0.167|. The arithmetic was fine; the assumption that a negative all-names IC is
tradeable by an **ascending** short was not.

## The finding — the two ICs explain both studies once the sign is read correctly

The pre-registration above carried the motivating framing that *"short ranks ascending, so a
negative IC is tradeable."* **The book says otherwise, and it says it consistently.**

`corr(hist_L[t-1], return[t]) = −0.0103`: **low `hist_L` predicts HIGH next-bar return.** The arm
ranks **ascending** and shorts the **lowest** `hist_L`. **So it shorts the names with the highest
expected return.** That is not a marginal miss — it is the wrong end of the cross-section.

**And the same convention explains D279 exactly:**

| study | population | measured IC (D280, Spearman, OOS from 2018) | sign for an **ascending short** | gross ranking contribution |
|---|---|---:|---|---:|
| **D279** | qualifying only | **+0.00462** | **favourable** — low score ⇒ low return | **+0.203** |
| **D281** | all live names | **−0.00524** | **adverse** — low score ⇒ high return | **−0.116** |

**Two studies, opposite IC signs, opposite measured ranking contributions, comparable magnitudes.
One convention accounts for both.** The D280 measurement was correct and the reading of it was
backwards: **the qualifying-set IC is the one correctly signed for this arm, and the all-names IC
is the one that is not.**

**What this does NOT license, and the restraint is the point.** The obvious next move — flip the
ranking to descending and re-run — **is not made here.** It is a new hypothesis with a new sign,
arrived at *after* seeing a result, on a fixture whose looks are already counted at 51. Under
[R8](../RULES.md#r8) and the stop clause written above, **D281 records what it pre-registered and
stops.** Anything else needs its own pre-registration and its own ledger.

## Verdict against the pre-registered predictions

| | prediction | confidence | outcome |
|---|---|---|---|
| **U1** | the unfiltered ranking beats `per-N` GROSS at all three N, by more than +0.203 | moderate | **WRONG, by the maximum margin** — it beats `per-N` at **no** N, gross or net, and is **negative** at all three |
| **U2** | no cell reaches positive GROSS Sharpe | high | **CORRECT** — the best gross Sharpe in the study is **−0.523**, and it belongs to a *random* control |
| **U3** | hurdle V fails everywhere; the stop fires | moderate-high | **CORRECT** — all ten CAGRs negative, from −0.14% to −9.50% |
| **U4** | the gross ranking contribution declines monotonically in N | moderate | **WRONG** — it *rises* (−0.167 → −0.116 → −0.113). The book improves as it dilutes toward the unconditional base, which is the same statement as U1's failure |

**Two of four wrong, and the two that were right were the two declared AGAINST the construction.**

**The falsification mechanism was named in advance and is the one that fired.** The
pre-registration's *"What would falsify U1"* reads: *"a top-N cut samples the extreme tail of
`hist_L`, not the whole cross-section the IC was measured over."* The lag audit measures that tail
directly — held names sit at percentile **0.0055 / 0.0146 / 0.0299** of the lagged cross-section.
**A rank IC over the whole cross-section does not survive into the bottom 0.5–3% of it**, and this
study is the measurement of how far it fails to.

## Defects and degeneracies — all four, headed rather than buried

### 1. `per-N` IS NOT TURNOVER-MATCHED ON AN UNFILTERED UNIVERSE, and the pre-registration said it would be

**This is the one real design error and it is mine.** `persistent_rnd` refills only **vacancies**,
and on the qualifying set a vacancy occurs whenever a name stops qualifying — which gave D279 a
turnover ratio of **0.5–0.7×**. **On the unfiltered universe there is no qualifying condition to
stop qualifying**, so the only vacancy is a delisting. `per-N` turnover collapses to **18 / 51 /
116 units against the ranked book's 10,162 / 22,497 / 40,984 — a ratio of 0.002×.**

**It is not a turnover-matched control here. It is a random buy-and-hold basket of N names.**
Copying a control across a change of population without re-checking what it holds constant is the
same class of error as D279's `random-N`: **a control's name is not a guarantee of what it
matches.**

**What survives the defect, stated precisely.** The **gross** comparison is scored at zero fees, so
the mismatch cannot enter it through cost — what it does change is the **holding period**, and
`per-N` holds for years where `top-N` holds for days. **So the gross gap against `per-N` mixes
selection with holding period and is not a clean single-variable read.** The verdict does not rest
on it alone: `rnd-N` churns 6–7× *harder* than the ranked book and the ranked book loses **gross to
that control too**, at all three N. **Two controls failing on opposite sides of the turnover axis
is what makes the negative verdict safe**, and it is why both were pre-registered rather than one.

### 2. Hurdle H is broken again, in a new way, and again carries no verdict

Pre-registered as reported-not-decisive under [R7](../RULES.md#r7)'s corollary. It earned that
treatment twice over:

| cell | net CAGR | net Sharpe | rotation null | reading |
|---|---:|---:|---|---|
| `hist_L\|all` | **−9.50%** | −0.760 | **100.0th / 100.0th** | a book losing 9.5%/yr at the ceiling of its own null, whose p50 is −0.925 |
| `hist_L\|per50` | −0.45% | −0.653 | **100.0th / 100.0th** | **a RANDOM control clears H on both legs** |
| `hist_L\|per25` | −0.30% | −0.768 | 99.0th / 88.0th | random again, near the ceiling |
| `hist_L\|top10` | −0.41% | −0.969 | **0.7th / 0.7th** | the ranked book is at the **bottom** of its own null |

**A random draw clearing a skill test at the 100th percentile is the cleanest demonstration of R7's
corollary this programme has produced.** H was excluded from `clears_all` in code before the run;
that exclusion is what stops this table reading as three passes.

**The 0.7th-percentile line is the informative one, and it points the same way as the verdict.**
Randomising the *timing* of the ranked book's own positions beats the real book **99.3% of the
time**. `top25` sits at the 5.0th / **0.3rd**; `top50` at the 65.0th / **1.7th**. **Three
independent controls — random selection at matched count, random selection held, and random timing
of the book's own positions — all agree the ranking is worse than chance.**

### 3. E′ degenerates further than it did in D279, and in both directions

| cell | names held ≥250 bars | E′ over the book | verdict |
|---|---:|---:|---|
| `hist_L\|top10` | **2** | **2.00** | fails |
| `hist_L\|top25` | 63 | **63.00** | passes — the correlation matrix is the **identity** |
| `hist_L\|top50` | 187 | **177.97** | passes |
| `hist_L\|rnd10/25/50` | **0** | **0.00** | fails — a bar-by-bar redraw accumulates 250 held bars on *no* name |
| `hist_L\|per25` | 35 | 4.48 | passes |

**`top25` scoring 63.00 on 63 names is E′ announcing that it has stopped measuring correlation.**
D279 recorded this at 28.00 on 28 names; the wider universe makes it worse. **E′ is a headcount on
this construction**, it was retained only because it was pre-registered, and **it decided nothing**
— every cell that "passes" E′ fails V, C and F.

### 4. `top_name_share` is not readable on a losing book and is not interpreted

The statistic is `max_i(sum_t pos·r) / sum_i(...)` — an unnormalised, cost-free per-name log-return
sum, where `score` divides by live-name count and charges fees. **On a book whose scored return is
negative the two can carry opposite signs**, and here they do: `top10` reports **61.3%**, `top25`
**57.6%**, `top50` **30.8%** of a positive raw total, while the scored cells lose. **Reported for
continuity with D279 and explicitly NOT used as evidence.** The concentration question it exists to
answer is moot — nothing survived to be concentrated.

## What the unconditional base says, since it is a cell here for the first time

**`hist_L|all` — short every live warm name — loses 9.50%/yr at 61.5% gross exposure with an
82.52% drawdown.** That is [FINDINGS §1b](../FINDINGS.md)'s variance tax measured on this fixture
with no selection at all, and it is the floor every cell in D256, D279 and D281 is trying to climb
off. **Its gross Sharpe of −0.632 sits within 0.004 of `top50`'s −0.636**: at N = 50 the ranking
has diluted all the way back to the unconditional short.

## Stop — it fires, exactly as written

> *"If no cell clears V, C and F, the unfiltered ranking is closed. No fourth N, no alternative
> score, no re-cut of the universe, no second population."*

**No cell cleared V, C or F. The unfiltered ranking is CLOSED**, and nothing was tuned after the
result was seen.

**Together with D256 and D279 this closes `hist_L`-ASCENDING-ranked directional shorts on the
dead-inclusive daily fixture.** The three studies between them tested holding everything that
qualifies (D256), the top N of what qualifies (D279), and the top N of everything (D281).

**What is NOT closed by this, stated so the closure is not read wider than it is:**

1. **The descending ranking is untested and is now the obvious candidate** — but it is a *new*
   hypothesis, found post-hoc, and under R8 it needs its own pre-registration, its own predictions
   and its own ledger. **It is not run here and no number for it exists.**
2. **D279's filtered result is untouched by this.** D281 tested a different population; it neither
   confirms nor withdraws anything about the qualifying set.
3. **The factor-neutral branch of [FINDINGS §9](../FINDINGS.md) remains untouched**, as it has been
   since D256.

## Ledger, as pre-registered

| count | N |
|---|---:|
| fresh — 3 N × 3 modes + 1 unfiltered base | **10** |
| carried: D279 | 20 |
| carried: D256 | 21 |
| **total** | **51** |

**Unchanged from the pre-registration.** No cell was added after the run: the lag audit, the
decomposition, E′ and `top_name_share` all re-read positions already scored. **D280 remains
disclosed and scores no cell** — and its measurement is now the most load-bearing thing in this
record, because reading its sign correctly is what explains D279 and D281 together.
