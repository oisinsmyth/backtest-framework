# D509 — the stretch ranker re-scored on an economic primary: top-minus-bottom quintile in dollars per session

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file.
**In-sample 2016-01-04 → 2023-12-29 only**; the arm's 2024+ slice is SPENT (D503) and is not scored.

## 0. Provenance, stated first because it is the weakness of this record

**This primary was chosen AFTER seeing D508's result.** D508 declared a Spearman rank correlation,
read +0.0089, and I then argued in the session that the statistic was the wrong lens for this arm:
its information sits in the tails, a rank statistic compresses magnitude, the quintile pattern is not
monotone (net Sharpe +0.61, +0.35, +0.36, +0.68, +1.36), and 9% of sessions tie at exactly $0
because the arm does not trade them. **The principal then directed this re-score.**

**That makes the primary post-hoc on a window already looked at.** The consequence is fixed in
advance: **no outcome of this record can be a discovery.** A clearing result would mean "worth
declaring on a slice nobody has read", and **the arm has no such slice on NQ** — so in practice the
ceiling here is a measurement and a better-specified null, not a promotion. This record exists to
answer the question with the right statistic, not to give the conditioner a second chance at a
verdict.

## 1. The primary, one (R14)

**Δ = mean net P&L per session in the TOP quintile of `|log(P/SMA200)|` minus the mean in the BOTTOM
quintile, in dollars at one MNQ.** From D508's table the observed value is +20.45 − 6.63 = **+13.82 a
session**, and this record tests that number rather than re-deriving it.

Why this statistic instead of a rank correlation: it is denominated in the unit the account actually
pays in, it does not assume monotonicity, and it is unaffected by the block of tied zero sessions
sitting in the middle of the distribution.

**Reported beside it:** the full five-quintile shape in net and gross side by side, gross per trade,
trades per session, hit, worst day and P3a per quintile; and a **monotonicity check** — Spearman of
the quintile means against the quintile index — so a U-shape is visible rather than hidden.

## 2. The null, which is now cleaner than D508's

**N1, exact enumerated rotation of the conditioner.** For each offset `k = 1 … T−1`, roll the
conditioner against the arm's P&L, re-form the quintiles, and recompute Δ. Enumerated, ≈ 1,875
offsets, p95 sampling error exactly zero.

**This null subsumes D508's separate matched-random-gate control (N3), and that is the methodological
point of this record.** A rotated conditioner is, by construction, a persistent gate with **identical
duty cycle and an identical run-length distribution** to the observed one — rotation permutes *when*
the states occur without changing *how long they last*. D508 needed a hand-built run-length-matched
gate because its primary was a correlation over all sessions; a quintile-difference statistic gets
that control for free from its own rotation. The hand-built band is therefore **not** re-run.

**N2, family maximum** over the four cells — {SMA, EMA} × {absolute, signed} — under common offsets,
p95 of the per-offset maximum of Δ.

**N3, the within-year decomposition.** Δ computed inside each calendar year and averaged. D508 found
the Spearman reversed sign between pooled and within-year (pooled +0.009, within-year mean −0.042),
because the arm's P&L concentrates in 2020 and 2022 and those are also high-stretch years. If Δ is
large pooled and ≈ 0 or negative within year, the conditioner ranks years.

**N4, the tie control.** Δ recomputed on **traded sessions only** (the 1,708 of 1,876 where the arm
took a position), since the 168 untraded sessions are exactly $0 and belong to no quintile in an
economic sense. Both are reported; the pooled all-sessions figure is the primary.

## 3. Decision rule (pre-registered)

- **PROCEED** — meaning "worth declaring on an unread slice", which does not exist for this arm, so
  in practice this outcome is recorded and not acted on — if Δ clears the N1 p95, clears the N2
  family p95, keeps its sign within year (N3), and survives the tie control (N4).
- **PICK** if Δ clears N1 but fails N2 or N3.
- **CLOSE** otherwise. The principal closes.

## 4. Predictions (checkable in the runner's quantities)

- **X-a** Observed Δ is **+13.82 ± 0.05** a session, reproducing D508's quintile table exactly.
- **X-b** The N1 rotation null is **wide and centred near zero**: p50 within ±$3, p95 between **+$12
  and +$28** a session. Δ lands between the **70th and 92nd percentile** and **does not clear p95**.
  Reason: rotation preserves the conditioner's persistence, so a rotated gate still catches or misses
  whole regimes, and the arm's P&L is concentrated in two of eight years.
- **X-c** The N2 family p95 is **at least 1.3×** the single-cell p95, and the observed family maximum
  does not clear it.
- **X-d** The within-year mean Δ is **below +$6 a session** and **negative in at least four of the
  eight years**, consistent with D508's within-year Spearman of −0.042.
- **X-e** The traded-only Δ is **within 25%** of the all-sessions Δ, so the tie block was a real but
  second-order defect in D508's statistic.
- **X-f** The quintile means are **not monotone**: the index-versus-mean Spearman is below +0.8, and
  quintile 1 beats quintiles 2 and 3 in net dollars.
- **X-g** The verdict is **CLOSE**.

## 5. Files

This record · `scripts/run_d509_quintile_primary.py` (`--run`, `--selftest`, importing D508's
conditioner and the frozen arm) · `data/d509_quintile_primary.json` · RESULT (separate).
Runtime seconds.
