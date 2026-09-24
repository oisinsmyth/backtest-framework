# D624 PRE-REGISTRATION — can one-second bars stand in for aggressor-signed flow in the settlement ledger's Stage A?

*2026-09-24. Committed alone, before the runner exists (R8). Every design choice below is the
principal's, made in planning on 2026-09-24. Where they chose between options, the choice is quoted.
No estimate has yet been compared with any true signed flow, on any root or any day.*

## 0. Why this exists

The settlement flow ledger's Stage A kill test (deposit H1, line 538) regresses **realised in-window
signed flow** on the predicted flow. "Signed" means aggressor-signed: buyer-initiated volume minus
seller-initiated volume, in outright contracts, over 14:28:00–14:30:00 ET. Databento sells that
history for CL and NG from 2017, but the principal cannot buy more data (AITODO, data gaps G1).

What is free under the CME Standard subscription is **one-second OHLCV bars**, the full history
(`data/ledger_free_pull_jobs.json`). They carry volume but not the aggressor side. Signed flow built
from them is therefore an **estimate**.

The principal's rule (2026-09-24): Stage A may run on the estimate **only if it matches true signed
flow at a day-level correlation of at least 0.8**. Below that, *"I will find a way to get the data."*
This record fixes how that 0.8 is measured, before any number exists.

Why 0.8 matters: error in the dependent variable does not bias H1's slope, but it adds noise. At a
correlation of ρ between estimate and truth, the test keeps roughly ρ² of its effective sample. At 0.8
that is 64%, and the planned flow MDE (deposit §9A.1, n_eff ≈ 5,000) moves from 0.028 to about 0.035.

## 1. Data: truth and inputs

Every truth series uses the Databento `trades` schema's `side`, which is the aggressor: `B` means the
buyer lifted the offer, `A` means the seller hit the bid, and `N` means no side (mostly legs of spread
trades). **Truth for a contract and interval is the sum of size over `B` trades minus the sum over `A`
trades, with `N` excluded.** The share of `N` volume is reported: it was 17–27% of window trades on the
three post-vault sessions inspected for structure.

| role | roots | span | source |
|---|---|---|---|
| estimator selection, first half | **HO, RB** (the principal: "post-vault + sibling roots"; BZ dropped because no settlement window is recorded) | 2025-09-25 → 2026-02-27 | free `trades` and `ohlcv-1s` under the subscription's last-12-months window |
| sibling agreement, second half | HO, RB | 2026-03-02 → 2026-09-18 | the same pull |
| **the gate** | **CL, NG** | 2026-09-21 → the top-up date (~2026-10-08; about 18 sessions) | free post-vault `trades`, already pulled 2026-09-19 → 09-23, plus `ohlcv-1s` for the same days, both topped up before the subscription lapses (~2026-10-11) |
| reported, not gated | CLT, NGT (TAS) | same as the gate | same |

HO and RB settle on the same 14:28:00–14:30:00 ET window as CL and NG (`data/settlement_windows.csv`,
SER-4867). **No CL or NG data dated 2025-03-01 → 2026-09-18 is read** (A6's vault). The sibling year sits
in the same calendar span but is not NG, CL or a fund, and it is recorded in the Q25 table of
`docs/internal/SETTLEMENT_FLOW_LEDGER_AMENDMENTS.md`. The post-vault NG/CL sessions are also the start
of Track 2's forward period. They are read here for estimator accuracy only: no flow model, no Q_rem
and no price statistic.

## 2. The quantity

For each session and contract: **the daily window flow W = signed volume over bars (estimate) or trades
(truth) stamped in [14:28:00, 14:30:00) ET.** A bar's stamp is its open.

- **The contract**, per the principal ("traded contract; all reported"):
  - **NG:** the Bloomberg Natural Gas Subindex month with the larger weight at the start of the
    window. Lead = Table 9's designated month for month m; next = month m+1's. The weight on next is
    BCOM §2.8's s0(k) = clip((k − 5)/5, 0, 1) on business day k (`scripts/gate_0b_ng_nav.py`). Ties go
    to the nearer month.
  - **CL:** the Balanced WTI index's contract month with the largest weight.
    - The components are monthly (m+2, rolling to m+3 at the BD2–3 closes), June and December, each
      at one third.
    - A month held by two components has two thirds.
    - A three-way tie goes to the monthly component's month (`scripts/gate_0b_cl_nav.py`).
  - **HO, RB:** the outright with the most one-second-bar volume in the window that day. That is
    measured on the estimator's input, never on the truth.
- **Sessions:** a session is used when its contract has at least 20 true trades in the window. That
  floor removes early closes and holidays. Excluded sessions are listed.
- **The statistic:** Pearson r across sessions between estimated and true W, with a 90% Fisher-z
  interval. Spearman is reported beside it.

## 3. The candidate estimators, declared now

They run on the one-second bars of the contract (o, h, l, c, v), in time order. The sign state is
carried from 09:00 ET onward.

| id | rule | signed contribution of bar i |
|---|---|---|
| **E1** tick rule | sᵢ = sign(cᵢ − cᵢ₋₁); zero carries the last non-zero sign; before any change, sᵢ = 0 | sᵢ·vᵢ |
| **E2** in-second direction | sᵢ = sign(cᵢ − oᵢ); if zero, E1's sign | sᵢ·vᵢ |
| **E3** bulk volume classification | zᵢ = (cᵢ − cᵢ₋₁)/σ, with σ the standard deviation of consecutive-bar close changes over [13:58:00, 14:28:00) that day. If σ = 0 or there are fewer than 30 bars, E1 is used for that session and counted | vᵢ·(2Φ(zᵢ) − 1) |

The simplicity order is E1 < E2 < E3.

## 4. Selection and agreement (the principal: "pick on siblings, test on NG/CL"; "pick on 1st half, agree on 2nd")

1. **Selection.** On the first half, the chosen estimator is the one with the highest mean of r(HO) and
   r(RB). A candidate within 0.005 of the best loses to a simpler one.
2. **Agreement.** On the second half, which the choice never saw, the chosen estimator must reach
   **r ≥ 0.8 on HO and on RB separately**.
3. **Only the chosen estimator** is ever computed against NG or CL truth.

## 5. The gate (the principal: "point ≥ 0.8 + siblings agree"; "per root"; "once, after the top-up")

It is read **once**, after the top-up, on every usable post-vault session. There is no provisional read.

| outcome for root X ∈ {CL, NG} | consequence |
|---|---|
| siblings agree **and** r_X ≥ 0.8 | X's Stage A runs on the estimate. The regression of truth on estimate (slope, residual SD) is carried as X's measurement-error band |
| siblings agree **and** 0.70 ≤ r_X < 0.8 | **UNRESOLVED (near miss)**, added by the principal after seeing the power table below. X's Stage A still waits, as for a fail. The record states that sampling on this many sessions cannot be ruled out as the cause |
| siblings agree **and** r_X < 0.70 | **FAIL**. X's Stage A waits until the principal sources real signed flow |
| siblings do not agree | neither root runs Stage A on the estimate |
| fewer than 15 usable sessions for X | **UNRESOLVED** for X: no Stage A on the estimate yet, and the result is reported with its interval |

Per root, as A2 has it. The 90% interval is reported beside r and is not used in the decision.

**Power, computed before the run.** On 18 sessions (Fisher SE = 1/√15), the chance that the sample
correlation reaches 0.8:

| true correlation | 0.75 | 0.80 | 0.85 | 0.90 | 0.95 |
|---|---|---|---|---|---|
| chance | 0.31 | 0.50 | 0.73 | 0.93 | 1.00 |

A good-but-not-great estimator can fail on sampling alone. The principal chose the point reading before
this table was computed. The table was shown to them with this record, before the pre-registration
was committed.

## 6. Checks that must pass first, and controls that must fire (each raises)

- **K1, the known answer: bars and trades align.**
  - For every contract and window second, the one-second bar volume equals the sum of trade sizes, all
    sides including `N`, stamped in that second.
  - It must hold on at least 99.9% of window seconds, on the siblings and on NG/CL.
  - It proves the clock, the timezone and the contract mapping before any correlation is computed.
- **C1, a day shift.** On the siblings' second half, the estimate for day t against the truth for day
  t+1 must have |r| < 0.5.
- **C2, random signs.** A seeded random sign per bar (seed 624) must have |r| < 0.3 against the truth.

## 7. Reported beside, never gating

- **The pre-window flow**, 13:30 → τ for τ ∈ {13:50, 14:00, 14:10}. This is Stage B's S_pre input
  (deposit line 371).
- **All outright months summed.**
- **Volume-weighted classification accuracy:** the share of true signed volume whose second's sign
  matches the estimate.
- **The `N` share.**
- **TAS (CLT, NGT):** daily signed TAS volume from the session open to 14:30 ET. Estimate against truth,
  r and interval, no bar. Stage D's own bar is not set here.

## 8. What this does not touch, and the files

- **Not read or computed:** no CL or NG data dated 2025-03-01 → 2026-09-18, no fund data, no flow
  prediction, no price move, and none of H1–H15.
- **Runner:** `scripts/validate_flow_estimate.py`.
  - `--siblings` runs K1 on the siblings, the selection, the agreement check, C1 and C2.
  - `--gate` runs K1 on NG/CL and the gate, after the top-up.
- **Output:** `data/ledger_flow_estimate_validation.json`, reproduced byte for byte by `--check`.
- **The free pulls:** `scripts/fetch_ledger_free.py`.
- **Deviations:** anything changed after the first run is listed in the output's `deviations` and
  never replaces a verdict.
