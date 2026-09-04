# D323 RESULT — the ranking inverts with width, and `k` was never re-read either

**Status:** RESULT. Pre-registered at `fee3b50`, runner at `9a0f87c`, both
committed before this file existed (R8).
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is promoted.**

---

## 1. Q3 confirms emphatically — the premise was right

**Spearman ρ = −0.225** between D290's published tier-1 order and the net-Sharpe
order at `N_eff` = 2. Q3 predicted below +0.7. **The ranking does not merely move;
it inverts.**

| D290 rank | candidate | **best netSHRP at N=2** | k | dv | p |
|--:|---|--:|--:|--:|--:|
| 8 | **retrace_leg** | **+0.557** | 40 | n | 0.0099 |
| 12 | **rev_21** | **+0.498** | 10 | n | 0.0099 |
| 3 | **rsi** | **+0.481** | 10 | n | 0.0099 |
| 11 | **hist_L** | +0.262 | 40 | Y | 0.109 |
| 7 | choch_dist | +0.196 | 20 | n | 0.0198 |
| 9 | skew_63 | +0.177 | 40 | n | 0.129 |
| **1** | **price_log** | **+0.116** | 40 | n | 0.119 |
| 4 | dist_52w_high | +0.116 | 40 | n | 0.208 |
| 13 | dist_lvn | +0.062 | 20 | n | 0.158 |
| 6 | rev_5 | +0.050 | 40 | n | 0.168 |
| 5 | on_persist | +0.041 | 40 | n | 0.238 |
| 2 | macd_hist | −0.010 | 10 | Y | 0.040 |
| **10** | **macd_line** | **−0.478** | 40 | n | 0.654 |

**D290's first-ranked candidate is seventh here. Its eighth is first.** The
shortlist was ranked at widths of 3 to 50 and the book holds 2; **concentration
selects on a signal's rank profile and reorders it.**

**`price_log` behaves exactly as the records predicted** — 7th, and it holds the
most expensive book in the study at a **31.62 bp** half-spread against
`retrace_leg`'s 16.73. D293 called its apparent solvency a turnover artefact and
D291 called it a static tilt; at the operating point it is neither solvent nor
competitive.

## 2. Q2 is falsified by +0.008, which is a tie and not a win

| | net Sharpe |
|---|--:|
| **best incumbent cell** (confluence, k=10, dv28) | **+0.549** |
| retrace_leg, k=40, no dv | **+0.557** |
| **margin** | **+0.008** |

`retrace_leg` satisfies Q2's full clause — profitable at **+20.26 bp/bar**,
p = 0.0099, and it survives BH at the effective test count. **And it beats the
incumbent by eight thousandths of a Sharpe.**

**I am not calling that a win.** It is the fourth study running where a
load-bearing "no candidate beats X" prediction falls to a margin inside the noise,
and the discipline that applies is the one D316 established: **this fixture cannot
resolve differences of that size.**

**BH-FDR: NONE at the nominal 104 cells; six survive at the effective 58** —
`rsi` at k=5 and k=10, `retrace_leg` at k=5, k=20 and k=40, `rev_21` at k=10.
Median pairwise correlation is 0.131 and the effective count is Li-Ji **58.0** /
Cheverud-Nyholt **96.3**, so the nominal correction was over-strict but not by
much — unlike D321, where 19 correlated thresholds collapsed to 3.

## 3. The finding that is actually worth having was incidental

**The incumbent's own holding period was never re-read after concentration.**

```
incumbent net Sharpe        k=5      k=10     k=20     k=40
  dv28 off                +0.334   +0.454   +0.084   +0.160
  dv28 ON                 +0.507   +0.549   +0.272   +0.328
```

**k = 10 beats k = 5 at both settings** — **+0.454 against +0.334** without dv28,
and **+0.549 against +0.507** with it. `k = 5` was fixed by D293 at a 25-name
book and carried unchanged through D300's move to `N_eff` = 2 and everything
after.

**That is a free +0.12 net Sharpe on the stack as it stands**, found without
changing the signal, and it is a larger effect than anything the thirteen
candidates produced against the incumbent.

**Caveat, and it matters:** `k` is one axis of a 104-cell sweep, so this is a
selected maximum on the same 3,187 bars. It is not confirmed and it does not enter
the stack without its own pre-registered test.

## 4. `hist_L` alone is 11th of 13, and the confluence beats it by +0.287

| | net Sharpe at N=2 |
|---|--:|
| the confluence (incumbent) | **+0.549** |
| `hist_L` alone | +0.262 |
| `rsi` alone (a pair member) | +0.481 |
| `macd_hist` alone (the other pair member) | −0.010 |
| `macd_line` alone | −0.478 |

**The composite is worth far more than its primary**, and one of its two pair
members (`rsi`) beats the primary on its own. D293's head-to-head established the
confluence beat `hist_L` at N=25; **it holds at N=2 and by a much larger margin.**

That is a genuine endorsement of the confluence construction, and it was not what
this study set out to test.

## 5. Two corrections to my own analysis, both caught before reporting

1. **The runner defined `m_eff` and `bh` and never called them.** The cell loop
   wrote the JSON and stopped, so the multiplicity correction the pre-registration
   promised was missing. Supplied in `d323b_shortlist_analysis.py`.
2. **The first effective-count computation was rank-deficient.** It intersected
   all 104 masks and got **73 common bars**, then estimated a 104×104 correlation
   matrix on them — eigenvalues meaningless, and the BH result built on them
   untrustworthy. Corrected to **pairwise-complete** correlation, median pair
   overlap **2,926 bars**.
3. **My R7 flag was mis-specified and flagged 13 of 13.** It tested for a null
   with a negative *median*; D295's actual pathology is a null whose **p95** is
   negative. **A costed two-name book built from a scrambled ranking SHOULD lose
   money**, so a negative median is the null working. On the corrected test,
   **0 of 13 are flagged** — every candidate's null has a positive upper tail and
   is sound.

## 6. Predictions

| | prediction | outcome |
|---|---|---|
| **Q1** | reproduction | **CONFIRMED** — the incumbent reproduces D306's N=2/target to 0.0 bp, and a single candidate's gate is a real 25-name gate distinct from the composite's |
| **Q2** | **no candidate beats the incumbent** *(against, load-bearing)* | **FALSIFIED by +0.008.** §2 |
| **Q3** | **the ranking moves, ρ < 0.7** | **CONFIRMED** — ρ = **−0.225**, an inversion |
| **Q4** | `price_log` is not distinguishable from price | **PARTLY** — it is 7th and holds a 31.62 bp book, but the raw-price control was not built; the runner omitted it and the omission is recorded here |
| **Q5** | `choch_dist` yields a usable statistic at N=2 | **CONFIRMED** — +0.196 at p = 0.0198, where D291's paired difference produced none |
| **Q6** | cost coverage ranks differently at fixed k | **CONFIRMED** — `price_log` leads D290's column and is 7th here |
| **Q7** | dv28 helps every candidate or none | **FALSIFIED** — it helps `hist_L` and `macd_hist` and hurts the strong candidates; `retrace_leg`, `rev_21` and `rsi` all peak with **dv off** |

**Q7's failure is the one to carry forward.** dv28 was tuned on the incumbent, and
**the three candidates that beat the incumbent's dv-off cells all prefer dv28
off.** That is evidence dv28 is fitted to the confluence rather than a general
cost lever, and it sharpens D321's guard rather than relaxing it.

## 7. Stop conditions

The pre-registered branch for **Q2 fails** reads: *"a different signal wins where
the book actually runs. That is the largest finding this programme could produce
at this stage, and it needs its own pre-registered confirmation."*

**I do not think that branch has fired in substance.** The margin is +0.008 — a
tie — and calling it a win would repeat exactly the error D313's Q3, D315's QB2
and D319's Q5 each recorded. **What has fired is Q3**, and its consequence is
different: the shortlist reorders with width, so **the entry axis is NOT closed —
it has been read once, at one width, with a coarse `k` grid.**

## 8. What is owed

1. **A pre-registered test of `k = 10` on the incumbent.** It is the largest
   unclaimed effect on the table and it costs one cell.
2. **The raw-price control for `price_log`**, which this runner omitted.
3. **`retrace_leg` and `rev_21` deserve a proper read** — not as promotions, but
   because two candidates D290 ranked 8th and 12th now sit at the top, and neither
   has ever been examined.

## 9. Files

`data/d323_shortlist.json` · `scripts/run_d323_shortlist_at_operating_point.py` ·
`data/d323b_analysis.json` · `scripts/d323b_shortlist_analysis.py`
