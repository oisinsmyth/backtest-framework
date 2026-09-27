# Index reweight: POWER for Gate C0 (D635 §8) and Stages R1–R3 (D636 §8)

## Stages R1–R3 (D636 §8)

*Run 2026-09-27 by `scripts/power_r_stages.py` → `data/index_reweight/power_r.json`, after D636 (`1315ecf`, with its
§11 notes) and before any R-stage runner. It reads moves on PLACEBO dates only: January BD12–BD16 for R1; the same
holds entered at BD16 for R2; 1 Nov → 1 Dec for R3. κ is assumed (C0 has not run) on a grid; the SNR gate is taken
as passed; B's legs use their own t0; R3's forecast is BCOM-only. The noise is a year-block bootstrap, 4,000 draws,
seed 636.*

**R1 is individually testable, by a wide margin.**
- The noise SE is $7–10 a trade.
- The MDE (2.8 SE) is $20–27, about the $26 cost.
- The plausible effect, a realised move of 0.5·|I| on the traded set, averages $109–188.
- Power is **100%** for A and B at every κ, and the yearly sign test's power is 100%.
- The within-year correlation is about 0 (ρ between −0.0001 and 0.004), so n_eff ≈ n.
- The size is below 0.1%. Passing needs the mean ≥ cost as well as t.
- A traded 316, 393 and 459 contract-days at κ = 0.02, 0.05 and 0.10. The energy roots trade on nearly every day.
  Corn almost never trades: its window volume is deep, so its predicted impact is small.

**R2 is underpowered.**

| hold | noise SE | MDE | plausible (0.25·I_total) | power |
|---|---|---|---|---|
| 1 day | $125–148 | $350–414 | $89–170 | 3–9% |
| 3 days | $256–285 | $717–798 | the same | 0.3% |
| 5 days | $262–290 | $733–811 | the same | 0.5–0.8% |

- **An R2 miss is INCONCLUSIVE, not evidence against a reversal** (D636 §8). The excluded effect size is stated from
  the SE: only reversals of several hundred dollars a contract can be seen.

**R3 can only see large effects.**
- The noise SE of a month-long hold is about $670; the MDE is about $1,870 a contract.
- Its size is 4.7–5.5%, sound. No plausible effect was stated (D636 §8), so an R3 miss excludes only effects above
  the MDE.

*Run 2026-09-27 by `scripts/power_gate_c0.py` → `data/index_reweight/power_c0.json`, after D635's pre-registration
(`e001171`) and before its runner exists. It reads each contract's settlement-window flow on NON-hedge days only
(BD12–BD16 of the roll months, as their deviation from the trailing 20-day norm). No hedge-day flow is set against
any predicted roll flow.*

## The design (`scripts/c0_design.py`)

- **15,000 observations:** 100 roll months (2016-02 → 2025-02, no January) × the 5 hedge days × the BCOM lead and
  next × 15 roots.
- **The predictors:**
  - Q_B uses the D634 re-run tracker. Its weights are asserted equal to the committed tracker: 11,330 cells, worst
    difference 5e-13.
  - Q_G is per $1bn of GSCI, from the published RPDW (`gsci_rpdw.csv`, `gsci_schedule.csv`, built by
    `build_gsci_inputs.py`).
  - **corr(Q_B, Q_G) = 0.47**, far below D635's 0.9 bar for separating them. Energy separates them: GSCI rolls it
    monthly, BCOM six times a year. In GC both roll the same legs in the same months. There is no GSCI term for HG,
    ZL or ZM.
- **The scale:** the median |Q_B + AUM_B·Q_G| where nonzero is **21,675 contracts**. The non-hedge-day noise SD per
  contract runs from 124 contracts (HG) to 1,152 (ZC).

## The result (400 draws per κ, seed 635)

| κ | C0-flow pass rate | median t | separable |
|---|---|---|---|
| 0 (size) | **3.25%** | 0.17 | 0% |
| 0.02 | 100% | 80 | 100% |
| **0.05 (plausible)** | **100%** | 143 | 100% |
| 0.10 | 100% | 174 | 100% |
| 0.25 | 100% | 186 | 100% |

- **The size is sound** (3.25% against a nominal 2.5–5%).
- **C0 is individually testable far below the plausible effect.** κ = 0.02 is detected every time. So a C0-flow
  fail would be evidence against the mechanism, not an underpowered miss. D635 §5's INCONCLUSIVE row does not apply.
- **Why t flattens as κ grows.** The simulated world treats GSCI's tracking assets as equal to BCOM's each year
  (AUM_B varies from $85bn to $110bn), while the fitted two-predictor model holds κ_G constant per $1bn. The mismatch
  grows with κ and enters the residual. It is a property of the declared world, not a fault in the fit.
- **The caveat POWER cannot cover:** the noise model is the flow's own spread on non-roll days. If Sierra's signing
  of calendar-spread legs (about 29% of window volume on HO/RB) differs on roll days, that is what the per-root sign
  check (D635 §7) is for.
