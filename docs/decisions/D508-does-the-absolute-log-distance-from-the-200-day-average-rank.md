# D508 — does |log(P / SMA200)| or |log(P / EMA200)| rank the admitted MACD arm's performance?

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D508-does-the-absolute-log-distance-from-the-200-day-average-rank-the-admitted-MACD-arms-performance.md`. The H1 above is the full title.*

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file.
**In-sample 2016-01-04 → 2023-12-29 only.**

## 0. The standing limitation, stated first

**The arm's 2024-01-02 → 2026-09-09 slice is SPENT** (D503, read once on the principal's word;
BOOK_PROP: *"That slice is spent and may never be re-read for this arm."*). This record therefore
runs on 2016–2023 alone and **has no forward slice available on NQ**. Whatever it finds is an
**in-sample measurement about an admitted arm, and it cannot on its own justify modifying that arm.**
Any change to the arm would need a slice nobody has read, and none exists for NQ. Stated up front so
that no later reading of this record mistakes a ranking for a licence to gate.

## 1. What is already known, so this does not repeat it

**D502 already tested the 200-day SMA on this exact arm, as a binary directional gate** (longs only
above the average, shorts only below). It took the NQ candidate from **+0.801 to +0.303 net Sharpe
while its mirror read +0.774** — a gate whose mirror beats it carries no information. Duty cycle ≈
82% above, 7–12 crossings a year. And the finding that governs this record's controls: **every one of
D502's eight regime cells raised NET Sharpe and lowered GROSS**, and **a random persistent gate of
the same duty cycle earns ≈ +0.2 net Sharpe for free** (the rotation null's p50). Cutting exposure
cuts cost; that channel is available to any gate and is not information.

**What is NOT tested, and is this record's question:** the **absolute** distance, `|log(P/MA)|`, as a
*continuous ranker of performance* rather than a directional gate. D502 asked which side of the
average to trade. This asks whether being far from the average, on either side, ranks the arm's
returns. Different axis, and unspent.

## 2. The object ranked, which is the arm itself and not a reconstruction

The runner **imports the frozen arm** — `d504_arm_full_history.build` for the signal and session
grid, `d491_conditional_hold.simulate` for the state machine — so what is ranked is the admitted
construction, byte for byte, not a re-implementation of the page's prose. The runner asserts its
reproduction of the arm against D504's published figures before ranking anything, and **stops** if
they disagree.

## 3. The conditioner

On the daily series of **day-session closes** (`build`'s `level`, the h15 close of each kept
session), with all windows ending at d−1:

- `SMA200_d` = the simple mean of the last 200 daily closes ending at d−1.
- `EMA200_d` = the exponential mean, α = 2/201, over the same history ending at d−1.
- **`stretch_sma_d = |log(close_{d−1} / SMA200_d)|`** and **`stretch_ema_d = |log(close_{d−1} /
  EMA200_d)|`**. Absolute value: the question is distance from the average, not side.
- The **signed** versions are computed and reported as the direct contrast with D502, and are
  secondary.
- The first 200 sessions are warm-up and are not ranked.

## 4. The primary statistic, one (R14)

**The Spearman rank correlation between `stretch_sma` and the arm's NET session P&L in dollars, on
NQ, 2016–2023.** Everything else is secondary or control.

Reported beside it, per quintile of the conditioner: **gross and net side by side** (D502's lesson),
trades per session, hit rate, net Sharpe, worst day, and P3a per year. Quintiles rather than deciles
for sample size: ≈ 2,000 sessions gives ≈ 400 a bucket.

## 5. Controls and nulls

- **N1, exact enumerated rotation.** The stretch series is a single market-level daily series, so the
  rotation group is finite: rotate it by `k = 1 … T−1` against the arm's P&L series, enumerated,
  ≈ 1,800 offsets after warm-up, p95 sampling error exactly zero. Reported: p50, p95, share of
  offsets at or above the observed statistic.
- **N2, family maximum.** Four cells — {SMA, EMA} × {absolute, signed} — share each offset; the bar
  is the p95 of the per-offset maximum.
- **N3, THE CONTROL THAT DECIDES IT — a run-length-matched random persistent gate.** D502 measured
  that a persistent gate of matched duty cycle earns ≈ +0.2 net Sharpe from the cost channel alone.
  The top-quintile cell is compared against random gates matched on **both duty cycle and run-length
  distribution**, not count. A cell that does not beat that band has found the cost channel, not a
  ranking.
- **N4, THE YEAR-PROXY DECOMPOSITION.** The arm is a regime construction: **2020 + 2022 + 2025 + 2026
  carry 96% of its total** (BOOK_PROP, qualification 2), and those are also the years price sits
  furthest from its 200-day average. So the pooled Spearman may be a proxy for *which year it is*.
  The runner therefore reports the Spearman **within each year** as well as pooled. If the pooled
  figure is positive while the within-year mean is ≈ 0, the conditioner ranks years, not sessions,
  and that is not a tradeable ranking.

## 6. Decision rule (pre-registered)

**PROCEED** to a declared stage 1 only if **all four** hold: the primary clears N1; it clears the N2
family p95; the top-quintile cell beats the N3 matched-random band; and **gross moves in the same
direction as net** across quintiles, so the effect is not purely the cost channel. **PICK** if the
primary clears N1 and N4 shows a within-year effect, but it fails N2 or N3. **CLOSE** otherwise.
The principal closes.

**Even a PROCEED cannot modify the admitted arm** (§0): it would licence a stage 1 on a root or slice
that is unspent, nothing more.

## 7. Predictions (checkable in the runner's quantities)

- **X-a** The pooled Spearman on the absolute SMA measure is **positive and small, +0.02 to +0.06**,
  and clears N1 pooled.
- **X-b** The **within-year mean Spearman is near zero, |ρ̄| < 0.03**, and most of the pooled figure
  is the year proxy N4 is built to expose.
- **X-c** Net Sharpe rises from the bottom quintile to the top by a wide margin while **gross per
  trade rises much less or falls**, reproducing D502's cost channel on a continuous conditioner.
- **X-d** The N3 matched-random band has a median near **+0.2 net Sharpe**, and the top-quintile cell
  **does not beat it by more than one standard error**.
- **X-e** The SMA and EMA versions agree to within **0.01 of Spearman**; at 200 periods the two
  averages are nearly the same series.
- **X-f** The **signed** versions are weaker than the absolute ones, consistent with D502 finding the
  signed binary gate uninformative.
- **X-g** The verdict is **CLOSE**.

## 8. Files

This record · `scripts/run_d508_stretch_ranker.py` (`--run`, `--selftest`) ·
`data/d508_stretch_ranker.json` · a quintile table · RESULT (separate). Projected runtime under two
minutes; the enumeration is ≈ 1,800 offsets × 4 cells over a 2,000-session series.
