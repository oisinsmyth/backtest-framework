# Index reweight: POWER for Gate C0 (D635 §8)

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
