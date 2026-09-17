# D470 — stage 0: can a state known at the entry concentrate the overnight index drift enough to pay the micro cost? Four declared gates on ES and NQ, two gate nulls

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D470-stage-0-can-a-state-at-the-entry-concentrate-the-overnight-index-drift-enough-to-pay-the-micro-cost-four-declared-gates-on-ES-and-NQ-with-two-gate-nulls.md`. The H1 above is the full title.*

**Pre-registration of a STAGE-0 premise check. Committed before the runner exists (R8).** Result
in a separate file. In-sample **2016-01-04 to 2023-12-29** on D467's session tables (same-front
nights only); **2024-01 onward unread; no holdout spent.** D470 taken after `ls docs/decisions`
and `git log --all` on both worktrees showed D469 as the highest number.

## 0. The question, and the arithmetic it has to beat

D468: the session hold on the index futures is gross-positive (ES-W1 $7.69 a night on σ $183 at
one MES; NQ-W1 $10.13 on $287 at one MNQ) and the $3 round trip leaves net Sharpe +0.39 / +0.38,
under the ledger's 0.5. The principal asked whether a **condition** — continuation, or the prior
close below a 200-day average — could lift it. **The cost per traded night is fixed, so a gate
can only help by raising the gross mean per traded night relative to its σ.** A component is
scored over all calendar days with zeros on untraded ones, so a gate that trades a fraction p of
nights has Sharpe √p × (net mean / σ on the traded nights) × √252. For ES-W1 to reach 0.5:

| p | gross mean needed on the traded nights (σ 183) |
|---|---:|
| 1.00 | $8.80 |
| 0.50 | $11.10 |
| 0.33 | $13.20 |
| 0.25 | $14.50 |

and if the selected nights are also more volatile the bar rises with σ. D464 already showed the
failure mode: S1/S2 gates on a tenth of nights picked +13.8 / +9.1 bp against a base of +5.3 and
sat inside the run-length-matched null, because a tenth of eight years cannot be told from luck.

## 1. What is measured (nothing added after the numbers are seen)

**Constructions:** ES-W1 and NQ-W1 (18:00 → 16:00, one micro, $3) as the primary family; ES-W2
and NQ-W2 (the overnight leg, 18:00 → 09:00) as a secondary family reported the same way. YM is
not scored (ρ 0.92 with ES; it would add cells and no information).

**States, evaluated at the 16:00 print of the entry day `a` (before the 18:00 entry), each a
two-sided split:**

- **G-A continuation:** the session return `c16(a) / c16(a−1) − 1` (same contract on both days)
  > 0 vs ≤ 0.
- **G-B prior overnight leg:** the overnight return into day `a` (`h08_c(a) / h18_o` of the
  night before) > 0 vs ≤ 0.
- **G-C trend:** `c16(a)` above vs below the simple average of the last 200 session closes
  (raw front-month closes; the roll gap is small against a 200-day mean and is declared, not
  adjusted). Nights before the average exists are excluded (the first ~200 sessions of 2016).
- **G-D realised volatility:** the σ of the last 21 session log returns, in the top vs bottom
  tercile of its **trailing 252-session** distribution (causal boundaries; the middle tercile is
  neither side and is reported).

**Per cell (root × window × state × side):** nights, share p, gross mean $/night, σ, hit rate,
mean/σ per night, cost as a share of the gross mean, and **the net Sharpe of the gated
component on all calendar days** (the ledger's quantity), with its monthly block-bootstrap SE.

## 2. The nulls (D464's two, exactly)

- **N1 — exact rotation of the gate against the P&L**: every offset of the gate series over the
  aligned nights (~1,970 offsets per root), the statistic the gated gross mean per night; p50, p95
  exact (SE 0). Destroys the alignment, preserves the gate's count and run structure.
- **N2 — run-length-matched random gates** (2,000 draws): random gates that reproduce the
  real gate's on-run and off-run length distributions; p50, p95 with its bootstrap SE (D373's
  rule: a margin within 2 SE is UNRESOLVED).
- **Family maximum:** the primary family is 16 cells (2 roots × 4 states × 2 sides) at ρ 0.91
  between roots; the **common-offset rotation** (one offset applied to every cell's gate) gives
  the null of the best gated mean across the family; its p95 is the bar a single cell must clear
  to be called a concentration rather than a pick.

## 3. What would justify a stage-1 pre-registration (declared now)

A cell is **worth a component record** only if all three hold: the gated component's net Sharpe
> 0.5 on the point estimate; its gross mean per night is above N1's p95 and above N2's p95 + 2 SE;
and it is above the family-maximum rotation p95. A cell that clears the first and not the others
is a **pick**, reported and not pursued. Nothing here enters the ledger.

## 4. Predictions

- **X-a** base rates reproduce D468: ES-W1 $7.69 / σ 183 on 1,974 nights; NQ-W1 $10.13 / 287.
- **X-b** G-A and G-B do not concentrate: the two sides' gross means differ by **less than one
  SE of the difference** (the overnight premium is not autocorrelated at the daily lag).
- **X-c** G-C below-average nights carry a higher gross mean (**1.3–2.0×** the base) **and** a
  higher σ (**1.4–1.7×**), so mean/σ per night improves by less than the √p penalty; the gated
  net Sharpe is **below 0.5** on both roots. G-D top tercile has the same shape.
- **X-d** No cell clears all three of §3. The family-maximum rotation p95 on ES-W1 is **$11–14**
  a night; the best observed cell is at or below it.
- **X-e** The W2 family shows the same picture with ratios closer to W1's on the below-average /
  high-σ side (the overnight leg is where the drift lives).
- **X-f** Runtime under 2 min.

## 5. Files

This record · `scripts/run_d470_gate_stage0.py` (`--run`, `--selftest`) · `data/d470_gate_stage0.json` · RESULT.
