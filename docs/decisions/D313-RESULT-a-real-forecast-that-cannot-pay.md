# D313 RESULT — the forecast is real, the estimator upgrade is real, and it still cannot pay

**Status:** RESULT. Pre-registered at `a533b8c`, runner committed at `2223184`
before this file existed (R8).
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 1. The headline

**The estimator upgrade is real and it shows up in the book — Q5 confirmed at
every target, with a monotone margin:**

```
B minus B_own, net Sharpe     N=2 +0.067   N=5 +0.185   N=10 +0.247   N=19 +0.344
```

**And it is a true A/B.** Assertion [1] shows `B_own`, run at D312's own targets,
reproduces D312's published arm B **bit-identically** — exactly 0.0 on both net
and Sharpe. The two arms differ in nothing but where the volatility estimate is
read from.

**It still does not beat doing nothing.** Sixteen testable cells, **none survives
BH-FDR at q = 0.10 on either statistic**, and the best p in the study is
**0.4478** — a coin flip.

**That is what §4 of the pre-registration predicted the mechanism for.** Widening
buys volatility reduction with net edge at a losing exchange rate, and a real
ρ ≈ 0.35 forecast does not change the rate.

## 2. The cells

`rt` = 57.0 bp, 3,187 bars, 20 cells. **Net Sharpe primary**, gross beside it.

| cell | gross | cost | trans | **NET** | vol | **netSHRP** | grsSHRP | voldisp | expo | **b/e rt** |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **F@N2** | +24.12 | 19.74 | 0.000 | **+4.37** | 780 | **+0.089** | +0.491 | 493 | 1.00 | **69.6** |
| B@N2 | +21.43 | 19.43 | 0.092 | +2.00 | 700 | +0.045 | +0.486 | 420 | 1.00 | 62.9 |
| E@N2 | +25.68 | 25.01 | 0.205 | +0.67 | 929 | +0.012 | +0.439 | 572 | 1.25 | 58.5 |
| B_own@N2 | +18.20 | 19.03 | 0.199 | −0.83 | 623 | −0.021 | +0.464 | 330 | 1.00 | 54.5 |
| B_out@N2 | +21.98 | 19.41 | 0.086 | +2.57 | 718 | +0.057 | +0.486 | 445 | 1.00 | 64.5 |
| **F@N5** | +19.23 | 17.17 | 0.000 | **+2.06** | 487 | **+0.067** | +0.627 | 278 | 1.00 | **63.8** |
| B@N5 | +17.60 | 18.03 | 0.273 | −0.43 | 574 | −0.012 | +0.486 | 341 | 1.00 | 55.6 |
| E@N5 | +20.70 | 20.80 | 0.196 | −0.11 | 554 | −0.003 | +0.593 | 312 | 1.20 | 56.7 |
| B_own@N5 | +11.54 | 17.98 | 0.470 | −6.44 | 519 | −0.197 | +0.353 | 258 | 1.00 | 36.6 |
| B_out@N5 | +17.63 | 18.05 | 0.288 | −0.42 | 579 | −0.011 | +0.483 | 346 | 1.00 | 55.7 |
| **F@N10** | +15.12 | 14.70 | 0.000 | **+0.43** | 346 | **+0.020** | +0.693 | 181 | 1.00 | **58.6** |
| B@N10 | +15.83 | 15.63 | 0.286 | +0.21 | 390 | +0.008 | +0.644 | 202 | 1.00 | 57.7 |
| E@N10 | +14.99 | 17.02 | 0.174 | −2.03 | 383 | −0.084 | +0.621 | 209 | 1.15 | 50.2 |
| B_own@N10 | +9.67 | 16.13 | 0.796 | −6.46 | 431 | −0.238 | +0.357 | 234 | 1.00 | 34.2 |
| B_out@N10 | +15.13 | 15.62 | 0.288 | −0.50 | 388 | −0.020 | +0.619 | 201 | 1.00 | 55.2 |
| **F@N19** | +10.61 | 11.48 | 0.000 | **−0.87** | 263 | **−0.053** | +0.640 | 130 | 1.00 | **52.7** |
| **B@N19** | +12.06 | 12.26 | 0.270 | **−0.19** | 294 | **−0.010** | +0.651 | 152 | 1.00 | 56.1 |
| E@N19 | +9.14 | 13.06 | 0.164 | −3.92 | 288 | −0.216 | +0.505 | 154 | 1.13 | 39.9 |
| B_own@N19 | +6.19 | 13.82 | 0.804 | −7.63 | 342 | −0.354 | +0.287 | 182 | 1.00 | 25.5 |
| B_out@N19 | +11.82 | 12.25 | 0.295 | −0.43 | 298 | −0.023 | +0.630 | 155 | 1.00 | 55.0 |

**`b/e rt` is the breakeven round trip in bp** — the cost the cell would tolerate
before net turns negative, against the actual 57.0. **Only the three F cells at
N ≤ 10 and the four N=2 breadth cells clear it.**

## 3. Where the estimator's advantage actually comes from — and it is not timing

Q8 predicted B's edge over B_own would be **largest at N=2**, where the two
predictors' forecast correlations diverge most (−0.016 against +0.352), and
smallest at N=19 (+0.347 against +0.410). **It is exactly backwards** — +0.067 at
N=2 rising monotonically to +0.344 at N=19.

Decomposing the net difference:

| | B − B_own net | from **gross** | from cost incl. transitions |
|---|--:|--:|--:|
| N=2 | +2.83 | **+3.23** | −0.40 *(B pays MORE)* |
| N=19 | +7.44 | **+5.87** | +1.56 |

**~79–114% of the advantage is gross.** The blind conditioner does not merely
mistime; it parks the book at widths that earn less — `B_own` gross falls to
+6.19 at N=19 against arm F's +10.61 — and it churns three times as hard doing it
(transitions 0.804 against 0.270).

**So the margin measures harm avoided, not good obtained**, and it is largest
where a blind signal can do the most damage rather than where a good signal has
the most to add. Q8's mechanism was wrong even though its direction would have
looked like a confirmation of the study.

**The one genuinely encouraging number in the study:** at N=10 and N=19 arm B
raises gross **above** the fixed book (+15.83 against +15.12; +12.06 against
+10.61). The conditioner does find better widths at the wide end. **It cannot pay
for them** — cost rises alongside, and the breakeven round trip stays under 57.0.

## 4. The null — nothing survives, and the timing is still worse than random

Circular rotation of the realised path, 200 draws, **BH-FDR q = 0.10 over the 16
testable cells: NONE, on either statistic.**

| cell | netSHRP | null p50 | null p95 | **p** |
|---|--:|--:|--:|--:|
| **B@N19** | −0.010 | −0.025 | +0.186 | **0.4478** |
| B_out@N19 | −0.023 | −0.016 | +0.201 | 0.5274 |
| B@N10 | +0.008 | +0.022 | +0.226 | 0.5572 |
| B_out@N10 | −0.020 | +0.041 | +0.234 | 0.6766 |
| E@N5 | −0.003 | +0.058 | +0.169 | 0.7413 |
| … | | | | up to 0.9900 |

**At N=2, N=5 and N=10 the rotation medians are POSITIVE and beat their
treatments** — de-risking at unrelated times still beats de-risking when the
signal says to. Only at N=19 do the medians go negative and the treatment edge
them, at p = 0.4478. **The improvement over D312 is real** (best p there was
0.7811) **and it does not reach anywhere near a decision.**

## 5. Predictions

| | prediction | outcome |
|---|---|---|
| **Q1** | vol within 10% of target | **FALSIFIED — and partly on a statistic I mis-specified.** §6 |
| **Q2** | dispersion cut by >30% | **FALSIFIED, and worse: arm B RAISES dispersion at 3 of 4 targets** (341 vs 278, 202 vs 181, 152 vs 130). A volatility-control rule making volatility less stable |
| **Q3** | **B never beats fixed on net Sharpe** *(against, load-bearing)* | **FALSIFIED BY ONE CELL** — B@N19 −0.010 against F@N19 −0.053. §7 |
| **Q4** | **E never beats fixed on net Sharpe** *(against)* | **CONFIRMED** at all four targets |
| **Q5** | **B beats B_own at every target** | **CONFIRMED 4 for 4**, monotone: +0.067, +0.185, +0.247, +0.344. §3 shows the mechanism is not the one intended |
| **Q6** | arm E exposure within 1.05 of 1.00 | **FALSIFIED — 1.13 to 1.25.** The fix halved D312's 1.34–1.53 and §6 attributes the residual |
| **Q7** | `xs_out` indistinguishable from `xs_all` | **CONFIRMED** — max Sharpe gap 0.028 against a 0.05 bar. **The +0.355/+0.352 margin was noise, and declining to chase it was right** |
| **Q8** | B's edge over B_own largest at N=2 | **FALSIFIED, backwards.** §3 |

## 6. Two defects in my own pre-registration, both now measured

`data/d313_target_diagnostics.json`.

### Q1's statistic contradicts §3.1's target change

§3.1 changed the target from each level's **full-sample sd** to the **mean of its
rolling sds**, to remove D312's structural leverage — **and Q1's statistic was
left as the full-sample realised vol.** Those differ by construction, so arm F,
which does no targeting whatever, "misses its target" by 15–27%.

On the statistic the new target actually implies:

```
arm F, mean rolling vol vs target     -0.0%   +0.1%   +0.6%   +0.4%
arm B                                 -7.6%  +16.3%  +14.3%  +11.4%
arm E                                +21.4%  +15.3%  +10.1%   +7.4%
```

**Q1 still fails on the corrected statistic** — 2 of 8 cells inside 10% rather
than 0 of 8 — so the rule does genuinely overshoot. But the reported miss of
+14% to +51% was roughly half my own bookkeeping.

### The calibration MEDIAN biases `v̂` low, and that is Q6's residual leverage

I chose a median for `c_j` on D302's robustness grounds. A median of a
right-skewed ratio sits below its mean, so `v̂` is biased low, so `target / v̂`
exceeds 1 before any forecasting:

| `N_eff` | mean `v` | mean `v̂` | ratio | arm E exposure |
|--:|--:|--:|--:|--:|
| 2 | 637.1 | 540.2 | **1.179** | **1.25** |
| 5 | 417.3 | 365.2 | 1.143 | 1.20 |
| 10 | 305.4 | 279.7 | 1.092 | 1.15 |
| 19 | 234.9 | 222.4 | 1.056 | 1.13 |

**The ordering matches exactly and the magnitudes nearly.** §3.1 removed the
between-window component — D312's 1.34–1.53 became 1.13–1.25 — and left a
median-vs-mean bias that a successor should correct directly rather than
rediscover.

## 7. Q3 is falsified in letter and the finding it was written to detect is absent

**B@N19 beats F@N19 on net Sharpe, −0.010 against −0.053.** By the letter, Q3
fails and the pre-registered branch applies:

> **Q3 fails → universe-conditioned breadth earns something. It needs its own
> confirmation before anything else.**

**It does not earn anything.** That cell's net is **−0.19 bp/bar**, its Sharpe is
**negative**, its p against its own rotation null is **0.4478**, and it does not
survive BH. It beats the fixed book by losing less.

**My prediction was mis-specified.** "Does not beat on Sharpe" can be falsified by
a less-bad loss; it should have required the cell to be **profitable** and to
**survive its null**. Under either added clause Q3 confirms at all four targets.

**I am not going to resolve that by choosing the reading I prefer.** D312's record
exists because I reinterpreted a stop condition after seeing results, and doing it
again in the conservative direction is still doing it. **Both readings are stated
and the call is the principal's.** My recommendation is to close: a −0.19 bp/bar
cell at p = 0.45 is not a finding under any standard this programme has used.

## 8. What holds

**The universe predictor is better than the book's own, decisively and
reproducibly.** That result stands independent of everything above — it is a
bit-identical A/B, confirmed 4 for 4, and it is the answer to the question that
prompted this study. **FINDINGS §11 is unchanged and unweakened.**

**A real risk forecast still cannot pay the width trade-off.** §4 of the
pre-registration set the price — from N=2 to N=10, gross falls 37.3% while cost
falls only 25.5% — and ρ ≈ 0.35 does not beat it. **This is now a measurement
rather than an estimator defect, which is exactly what D312 could not claim.**

**`xs_out` was noise, as predicted.** Declining to chase the +0.355/+0.352 margin
cost nothing, and Q7 is the evidence that post-hoc margins of that size on this
book should be ignored.

## 9. Scope, caveats, reporting groups

**Construction caveat, unchanged from D312 and restated:** arm B splices between
sixteen separately-simulated books at bar granularity, charging weight-distance
turnover but not re-running the holding path. **It is an instrument, not a
tradeable book, and it flatters B.** B still loses.

**Groups 2 and 3 of the reporting standard are inherited from D310**, as declared
in §5 of the pre-registration — arms B, E, B_own and B_out reweight the same
trades and produce no new ledger. **Groups 1 and 4 are reported in full**, group
1 including the breakeven round trip per cell.

**Out and unchanged:** the entry signal, the exits, the gate, `k`,
return-conditioned breadth (closed three times), and the combined B+E arm.

## 10. Assertions

All nine pass.

| | |
|---|---|
| **[1]** | arm F reproduces D310's gross and net at 7 shared levels (max 4.9e-15 bp) **and `B_own` reproduces D312's arm B BIT-IDENTICALLY at all 4 targets** |
| **[2]** | **causality** — `c_j` and `P` read only `t−1`, and removing the lag moves 2.5% of bars to a different level, so the audit can fail |
| **[3]** | stage 0 reproduces `d312_universe_forecast.json` **to zero** on persistence and forward correlation — a harness check, not a test |
| **[4]** | transitions vanish on a constant path in both mechanisms and are monotone |
| **[5]** | all 20 cells are distinct books |
| **[6]** | rotation preserves move count and the \|Δ\| distribution, up to the wrap |
| **[7]** | every breadth arm is exactly fully invested, so arm E's exposure is the only place Q6's leverage can hide |
| **[C]** | `rt × turn` = 52.1893 reproduces d295's 52.1893; the doubled form is rejected |
| **[8]** | assertion [1] raises on a book handed free money inside the mask |

## 11. Files

`data/d313_universe_risk.json` · `scripts/run_d313_universe_risk.py` ·
`data/d313_target_diagnostics.json` · `scripts/d313_target_diagnostics.py`
