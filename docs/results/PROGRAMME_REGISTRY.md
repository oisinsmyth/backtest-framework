# PROGRAMME REGISTRY

**Generated:** 2026-09-21 · `backtest_framework.validation.programme` (D592) · rendered from [`data/programme_registry.json`](../../data/programme_registry.json)

The deposit's programme-level false-positive controls name this page `results/PROGRAMME_REGISTRY.md` ([`SETTLEMENT_FLOW_LEDGER_PREREG.md`](../internal/User-Doc-Deposit/SETTLEMENT_FLOW_LEDGER_PREREG.md) §13A.8(2), [`OPENING_AGENT_STATE_PREREG.md`](../internal/User-Doc-Deposit/OPENING_AGENT_STATE_PREREG.md) §12A(2)). **This repository has no root `results/`**: the rendered page lives here in `docs/results/` with the other prose-results pages, and the state it is rendered from lives in `data/` with the other artefacts (D592).

**Programme-wide α = 0.05, split into 10 equal slots of 0.005.** Sealed 2026-09-21. **9 of 10 slots allocated; 1 reserved for future models.**

A family may only be registered into a free slot. When all ten are used, an eleventh requires a doc amendment that re-allocates α — never retroactively for families already evaluated. **Promotion requires the family's within-doc adjusted p-value ≤ 0.005 (roughly t ≥ 2.8), in addition to every within-doc criterion, and a programme-level DSR ≥ 0.95.** A row below is a registration, not a result.

| Slot | Family | α | Doc | Registered | Statistic |
|---|---|---|---|---|---|
| 1 | `LETF close flow H1` | 0.005 | `LETF_CLOSE_FLOW_PREREG.md` | 2026-09-21 | Primary effect: on active days the mean signed return tau -> close is positive (§4 H1; Holm across the 6 primary cells) |
| 2 | `shock classifier H1` | 0.005 | `SHOCK_CLASSIFIER_PREREG.md` | 2026-09-21 | Class divergence: INFO and LIQ returns differ in the shock direction (§6 H1; Holm across the 4 instruments) |
| 3 | `ledger H2` | 0.005 | `SETTLEMENT_FLOW_LEDGER_PREREG.md` | 2026-09-21 | Price effect: signed return from the t0+1 fill to the W_end close on traded days (§9 H2; Holm across the 2 instruments) |
| 4 | `index H-R1` | 0.005 | `INDEX_REWEIGHT_FLOW_PREREG.md` | 2026-09-21 | Execution-day effect: signed entry -> W_end close return pooled across commodities, days and years (§6 H-R1; Holm across constructions A and B) |
| 5 | `index H-R2` | 0.005 | `INDEX_REWEIGHT_FLOW_PREREG.md` | 2026-09-21 | Reversal: signed return in the reversal direction over 1/3/5 days (§6 H-R2; Holm across 3 holds x 2 constructions) |
| 6 | `index H-R3(b)` | 0.005 | `INDEX_REWEIGHT_FLOW_PREREG.md` | 2026-09-21 | Pre-positioning, TRADING arm only: the December entry -> pre-execution exit return in the forecast direction (§6 H-R3(b); H-R3(a) is descriptive and is not a decision family) |
| 7 | `last-hour F2 (ES)` | 0.005 | `D707-PRE-REG-f2-last-hour-filter-for-the-joint-vault.md` | 2026-09-30 | Vault line on D705 F2: the ES last-hour continuation (sign of 14:30->15:30, held to 16:00, one MES, $4.42) when tiers((tiers(abs(F5)/sigma) + tiers(rv to 15:30)) / 2) >= 0.8; PASS with >= 30 trades on 2024-01-01 -> 2026-09-18, net > 0 and one-sided NW t >= 1.2816 |
| 8 | `ledger H2 projected-profit (NG)` | 0.005 | `D649-PRE-REG-ng-projected-profit-line-for-the-joint-vault.md` | 2026-09-28 | Vault line on D630's trade: one MNG when b_t x |I_t| projects >= 2 x $5 (b_t from earlier traded days); PASS with >= 15 trades, one-sided t >= 1.2816 on the MNG gross and a positive MNG net |
| 9 | `opening compression break (NQ)` | 0.005 | `D680-PRE-REG-the-nq-compression-break-for-the-joint-vault.md` | 2026-09-29 | Vault line: D672's C1 on NQ (the plain break of yesterday's RTH range, E4, on the compressed third), one MNQ, friction once; PASS with >= 30 C1 trades, one-sided HAC t >= 1.2816 on the gross and a positive net |
| 10 | *(reserved)* | 0.005 | — | — | — |

**α allocated: 0.045 of 0.05.**

**Released slots.** The deposit's default is that α is never re-allocated retroactively for a family already evaluated; each row below is the principal's recorded override for one closed family. Its slot is free again; the family itself can never be registered again.

| Slot | Family | Doc | Registered | Released | Reason |
|---|---|---|---|---|---|
| 7 | `opening H-O2` | `OPENING_AGENT_STATE_PREREG.md` | 2026-09-21 | 2026-09-29 | D658 CLOSED by the principal ('close opening model v1'; on slot 7: 'Release it'): Gate O1 failed, no agent retained, H-O2's policy net-negative at both t0; the vault was never read for it. The principal's override of the deposit's never-retroactively default, for this family only |

---

## The other programme controls

This page is control 2 of seven. The rest, as the two docs write them:

| # | Control | Where it is implemented |
|---|---|---|
| 1 | Sealed vault, 2025-03-01 → 2026-09-18, one look per model | not implemented — it is a property of a loader that does not exist yet |
| 2 | Cross-document α allocation (this page) | `validation/programme.py:Registry` |
| 3 | Programme-level Deflated Sharpe, two counts per Sharpe | `validation/programme.py:programme_dsr`, `programme_trial_count` |
| 4 | 50% winner's-curse haircut, or the vault estimate if lower | `validation/programme.py:haircut` |
| 5 | Episode concentration and shared-period dependence | `validation/episodes.py` |
| 6 | One-bar-delay robustness and the leak canary | not implemented — both are properties of a runner that does not exist yet |
| 7 | The forward consistency route also requires a vault pass | a rule, not code |
