# POWER: settlement flow ledger, Stage A (H1a)

**Generated:** 2026-09-25 · `backtest_framework.validation.power` (D588)

Every value below is PLANNING arithmetic. Ledger §9A.1: the planning table holds estimates, and the real n_eff (with the design effect from the observed within-cluster correlation), SE and MDE are **recomputed on real data before each stage runs** and this file rewritten. A number here has never been compared with a market outcome.

| Stage | Test | Track | n | m | rho | n_eff | Units | SE | MDE (t = 2) | MDE (80%) | Plausible effect | Power class | Adoption by significance | Note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A: P1 rebalance (H1a) | CL: abs(Q_rem) vs abnormal window volume | Track 1 | 1,819 | 1.00 | 0.0000 | 1,819.0 | correlation | 0.0234 | 0.0469 | 0.0657 | 0.0884 | individually_testable | permitted | one row per day; pre-sample residual AC(1) 0.240; sim power at beta 0.25: HC1 0.92, NW5 0.90 |
| A: P1 rebalance (H1a) | NG: abs(Q_rem) vs abnormal window volume | Track 1 | 1,936 | 1.00 | 0.0000 | 1,936.0 | correlation | 0.0227 | 0.0455 | 0.0636 | 0.2660 | individually_testable | permitted | one row per day; pre-sample residual AC(1) 0.205; sim power at beta 0.25: HC1 1.00, NW5 1.00 |

**Adoption by significance** is BLOCKED for every row not classed `individually_testable` (ledger §9A.2 rule 3): an underpowered stage is evaluated under §9B instead, and a non-significant result there is recorded as *inconclusive*, never as *no effect* (rule 5).
