# D642 — PRE-REG: the shock classifier's signal frame, Phases 3–4 (event-study curves, H1–H4, robustness)

*2026-09-28. The principal: "confirm SC-A7 and SC-A8, then write the pre-registration". Committed ALONE, before any
runner exists (R8). **No forward return has been read on this line**: Phase 2 (D641) and POWER (`2f6a2b3`) read the
signal and the unsigned dispersion of the 30-minute move only. Spec: `SHOCK_CLASSIFIER_PREREG.md` v1.2 (read-only),
with SC-A1..A8 (`docs/internal/SHOCK_CLASSIFIER_AMENDMENTS.md`). Where this record and the deposit differ, the
deposit wins unless an amendment says otherwise.*

## 1. The object

- **Shocks:** D641's, from `data/shock/phase2_shocks.csv.gz`, on SC-A6's 2,282 usable sessions, 2016-01-04 →
  2025-02-28, rebuilt by the runner from the same code (a byte-identical check against the committed counts).
  - Primary: z = 4, w ∈ {1, 3} pooled, (c_hi, c_lo) = (0.6, 0.2).
  - Classes: INFO 11,671, LIQ 480, NONE 2,041.
- **Prices:** the D641 minute grids (front contract, peers forward-filled for at most 5 minutes; the traded markets
  are 100% covered).
- **Prior reads (SC-A2):** D528, D499 and D526 already measured large one-minute moves on these roots. Every result
  carries the **unconditional baseline**: all shocks at z = 4, classified or not.

## 2. Definitions, fixed here

| symbol | definition |
|---|---|
| b, t0 | the shock's bar (labelled by its start); t0 = its close |
| d | the shock direction, sign(r_w[b]) |
| trade direction D | INFO → +d, LIQ → −d (§4.7) |
| **curve at k** | c_k = D × (P[b + k] / P[b] − 1) × 10⁴, k = 0 … 60 minutes after t0, in bp (§7's event study) |
| **primary fill** | the close of bar b + 1 (§5.1). The one tick of adverse slippage belongs to the cost, not to the price |
| **H1 return** | x = d × (P[b + 1 + 30] / P[b + 1] − 1) × 10⁴: the 30-minute time-only exit from the primary fill, **in the SHOCK direction** (not the trade direction), so the two classes are comparable. INFO predicts x > 0, LIQ predicts x < 0 |
| cost | §5.1 at micro size: D508's default crossing + $3 commission + one adverse tick, in bp of the fill (NQ 2.4, ES 3.3, CL 10.7, GC 4.5 on average; POWER) |
| clustered SE | CR1 cluster-robust by session day, so shocks of both classes on one day share a cluster |
| day-block bootstrap | 9,999 resamples of session days with replacement, seed 642, for every CI |

A shock whose 30-minute exit bar falls outside the session grid, or on a missing price, is dropped and counted.

## 3. The tests (deposit §7)

**Event-study curves (produced first).** For each instrument × class (INFO, LIQ, NONE, and the unconditional
baseline), the mean c_k for k = 0 … 60, with 95% day-block-bootstrap CIs, and the count. They are rendered as a
figure in the report.

**H1: class divergence, per instrument.**
- The statistic is Δ = mean_INFO(x) − mean_LIQ(x), estimated as the OLS coefficient on an INFO indicator over the
  INFO and LIQ shocks, with the CR1 day-clustered SE. The test is one-sided (Δ > 0), with Holm–Bonferroni across the
  four instruments.
- **An instrument passes if** its Holm-adjusted p < 0.05 (clustered t ≥ 2 at least) **and both classes have the
  predicted sign**: mean_INFO(x) > 0 and mean_LIQ(x) < 0.
- **POWER's labels travel with the verdict.** NQ, ES and CL are UNDERPOWERED (§7A), so a null there is INCONCLUSIVE,
  not a failure. GC is the informative cell.
- Beside Δ, SC-A2's reading: INFO − baseline and LIQ − baseline, each with its clustered t. **A class that does not
  differ from the unconditional baseline adds nothing to what D528/D499 already measured**, and the report says so.

**H2: timing, for each class of each H1-passing instrument.**
- The **peak** k* is the argmax over k = 0 … 60 of the class's mean curve c_k.
- **Pass:** k* > 5, **and** c_5 ≤ 50% of c_{k*}, with c_{k*} > 0.
- The **delay cost** is reported: c_{k*} (captured from t0) against c_{k*} − c_5 (captured from t0 + 5).
- A fail means that class is untradeable at this latency.

**H3: label placebo (Gate 2).**
- Within each instrument × calendar year, the INFO/LIQ labels are permuted among that year's INFO and LIQ shocks
  (the per-year LIQ count is kept). 1,000 permutations, seed 642; Δ is recomputed each time.
- **Pass (per instrument that passed H1):** the observed Δ exceeds the permutation p95.
- CLAUDE.md's rule applies: the p95's bootstrap SE is reported, and a margin within 2 SE is **UNRESOLVED**, not a
  pass. p50 and p95 are reported beside Δ for all four instruments.

**H4: dose-response (Phase 4).**
- Within INFO, Spearman ρ(C, x) > 0: larger confirmation, stronger continuation.
- Within LIQ, Spearman ρ(C, x) > 0: smaller C, more negative x, stronger reversion.
- Both are reported per instrument and pooled, with day-block-bootstrap 95% CIs.
- **Pass:** the predicted sign in both classes.

## 4. Gates (deposit §10)

- **Gate 1** = H1 passes for ≥ 1 instrument **and** H2 passes for ≥ 1 class of a passing instrument. Otherwise STOP
  → write-up. That write-up states which instruments were inconclusive for power, not failed.
- **Gate 2** = H3 passes (for the instrument(s) that passed Gate 1). Otherwise STOP → write-up.
- Phase 5 (the book frame, conditional exits, fills, costs, prop constraints, Monte Carlo) and Phase 6 (walk-forward,
  DSR) run only past Gate 2, under their own pre-registration.
- The deposit's kill conditions (§12) apply as written.

## 5. Robustness (reported, never re-selected; deposit §7)

- **Stress fill:** the worst close of bars t0+1 … t0+5 for the trade direction (§5.1), as the fill for x.
- **Cost:** x net of 1× and 2× the §5.1 cost, per class, in the TRADE direction (the signal frame's gross-to-net view).
- **Grid:** z = 3 and 5; w = 1 and w = 3 separately; (c_hi, c_lo) = (0.5, 0.3) and (0.7, 0.1).
- **Events:** with and without event-flagged shocks, plus CL's NGSR diagnostic flag (SC-A7).
- **Time:** by calendar year, and the **2016–2023 vs 2024-01 → 2025-02 split** (SC-A2's disclosure).
- **Diagnostics (descriptive only, D3):**
  - the flow-profile feature is not computable in v1 (bars only, SC-A3), which is stated;
  - the **liquidity-regime** feature is the shock bar's volume relative to the median volume at that minute over
    the prior 60 sessions, in terciles, against x.

## 6. Reporting (CLAUDE.md, the parts the signal frame has)

- Per class and instrument: n, mean, **median**, win rate (x in the trade direction > 0), skew, kurtosis, the
  symmetric 1% trims (ex-top, ex-bottom, both), gross and net of the §5.1 cost in bp and in dollars at one micro.
- Dependence on years, on event shocks and on the shock window.
- Nulls as distributions: H3's p50, p95 and its SE.
- The book-frame groups (Sharpe/Sortino, drawdown, breakeven, component line) belong to Phase 5.

## 7. Multiplicity and trials

Every configuration evaluated is a row of `data/shock/trials.csv` through `validation.programme.TrialsCsv` (D592's
union schema: `doc` SHOCK_CLASSIFIER_PREREG.md, `family` "shock classifier H1"). It uses the deposit's §8 columns and
puts `reads_2024_plus` in `notes`. The **four H1 instruments are the only inference**; everything else is labelled
sensitivity. `tests/unit/test_programme.py`'s TRIALS_CSV_FILES is amended in the same commit as the rows.

## 8. The runner's assertions (CLAUDE.md), each proved to fire in `--selftest`

1. **Lag:**
   - the shocks are re-detected by the runner and must equal D641's committed counts;
   - a second implementation of the classification, from the stored C, event flag and thresholds, never calling
     `shock.model.classify`, must agree on every shock;
   - every price used for x or c_k is at a bar strictly after b.
2. **Money:** a favourable move in the trade direction pays positively, long and short, and x's sign convention is
   checked on a synthetic continuation and a synthetic reversion.
3. **Right quantity:** x from the t0+1 fill differs from the same move measured from the t0 close, and the SHOCK
   direction differs from the TRADE direction on every LIQ shock.

A `--dry-run` on synthetic prices (reading only the grids' calendar) runs every path before the one real `--run`.
The runner refuses a second run and has a `--check` that rebuilds it byte for byte.

## 9. What is fixed from this commit

Every definition, test, threshold, seed and output above. **A change is a versioned amendment (SC-A9 onward), written
before the code that uses it.** Nothing is chosen after a return is seen.
