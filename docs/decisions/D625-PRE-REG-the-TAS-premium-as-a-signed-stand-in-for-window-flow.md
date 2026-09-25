# D625 PRE-REGISTRATION — does the TAS price say which way the settlement flow went?

*2026-09-25. Committed alone, before the runner exists (R8). The design is the principal's, chosen in planning
on 2026-09-25; each choice is quoted. No TAS measure has yet been compared with any true signed flow.*

## 0. Why this exists

[D624](D624-RESULT-one-second-bars-cannot-carry-settlement-window-flow.md) showed that free one-second bars
cannot sign settlement-window flow. Amendment A8 therefore replaced Stage A's H1 with H1a, which tests the
flow's SIZE, and left direction to the price test H2. It also left Stage B's update step blocked, because
that step needs the signed pre-window flow S_pre.

TAS ("trade at settlement") contracts trade at a price differential to the day's settlement: −10 to +10 ticks
in the free one-second bars, median 0 (checked on 2023 CLT/NGT bars). A buyer paying above settlement is
demand for settlement-price exposure. The dealer who sells that TAS is short at the settlement, and hedges by
buying outright futures, largely in the window. **The hypothesis, stated before looking: a positive TAS
differential goes with net BUYING in the window.** The expected sign is fixed as +. A measure that agrees
reliably in the opposite direction is reported, but it is **not** re-signed after the fact and cannot pass.

The TAS one-second bars are free for the whole in-sample (2017 on). If a TAS measure tracks the flow's sign,
the ledger gets a signed flow test back for free.

## 1. Two roles, gated separately (the principal: "both, gated separately")

| role | TAS span used | the truth it must match | what a pass buys |
|---|---|---|---|
| **W: window** | session open (18:00 ET the evening before) → 14:30:00 ET | sign of the true window flow: aggressor-signed outright volume in the traded contract, 14:28:00–14:30:00 ET | a signed partner to H1a, **H1b**: the sign of Q_rem agrees with the sign of the TAS measure more often than chance. Written as its own amendment if W passes |
| **P: pre-window** | session open → τ, τ = **14:10** (13:50 and 14:00 reported) | sign of the true S_pre: aggressor-signed outright volume in the traded contract, 13:30 → τ (deposit line 371) | a signed stand-in for S_pre, which could unblock Stage B's update step. Written as its own amendment if P passes |

τ = 14:10 for role P is this record's choice, not the principal's. It is the last evaluation time, and it
carries the most pre-window information.

**The contracts.**
- The traded contract is D624's: for NG and CL, the index month with the largest weight; for HO and RB, the
  most active outright in the window, measured on the one-second bars.
- The TAS contract is **the TAS month matching the traded contract's delivery month** (for example, CLTX6
  for CLX6).
- A day whose matching TAS month has no bar in the span is excluded and listed.

## 2. The candidate measures, declared now

Each is computed on the matching TAS contract's one-second bars over the role's span. **cᵢ** is a bar's close
in differential ticks, and **vᵢ** its volume.

| id | measure | sign used |
|---|---|---|
| **T1** level | volume-weighted mean differential, Σ cᵢvᵢ / Σ vᵢ | sign(T1) |
| **T2** signed by level | Σ vᵢ·sign(cᵢ) (volume at a premium minus volume at a discount) | sign(T2) |
| **T3** tick rule on TAS | D624's E1 applied to the TAS bars: Σ vᵢ·sᵢ, with sᵢ the sign of the last non-zero change in cᵢ | sign(T3) |

The simplicity order is T1 < T2 < T3. **A measure of exactly 0 counts as a MISS**: the test is a sign call, and
it cannot abstain. The abstention share, and the agreement with abstentions dropped, are reported beside.

## 3. The statistic and the bar (the principal: "sign agreement ≥ 70%")

**Sign agreement** = the share of usable sessions on which sign(measure) = sign(truth). A session whose truth
is exactly 0 is dropped and counted. The bar is **≥ 0.70**. The day-level Pearson r is reported beside it and
never gates.

## 4. Data

| use | roots | span | source (all free) |
|---|---|---|---|
| selection, first half | HO, RB (TAS: HOT, RBT; about 650 and 600 TAS trades a session in March 2026) | 2025-09-25 → 2026-02-27 | outright truth and bars already on disk from D624. HOT/RBT `trades` and `ohlcv-1s` from a new free pull, 0.013 GB each |
| agreement, second half | HO, RB | 2026-03-02 → 2026-09-18 | same |
| **the gate** | CL, NG (TAS: CLT, NGT) | post-vault, 2026-09-21 → the top-up | D624's post-vault pull and top-up; both include CLT/NGT |

No CL or NG data dated 2025-03-01 → 2026-09-18 (A6's vault) is read.

## 5. Selection, agreement and the gate (the principal: "same as D624")

1. **Selection, per role.** On the first half, the chosen measure has the highest mean sign agreement over
   HO and RB. A measure within 0.01 of the best loses to a simpler one.
2. **Agreement, per role.** On the second half, the chosen measure must reach **≥ 0.70 on HO and on RB
   separately**. From 0.65 to 0.70 is a **near miss (UNRESOLVED)**. Below 0.65 fails.
3. **The gate, per role and per root.** It is read ONCE on CL and NG after the top-up, with the chosen
   measure only:

| outcome for root X and role R | consequence |
|---|---|
| siblings agree (R) **and** agreement ≥ 0.70 | R's use is admitted for X. It is written as an amendment (H1b for W, the S_pre stand-in for P) before any stage uses it |
| siblings agree **and** 0.65 ≤ agreement < 0.70 | UNRESOLVED (near miss). Not used |
| siblings agree **and** agreement < 0.65 | FAIL. Not used |
| siblings do not agree (R) | not used for either root |
| fewer than 15 usable sessions | UNRESOLVED. Not used |

**Power, before the run.** On 15 NG/CL sessions, ≥ 0.70 needs 11 of 15. The chance of passing when the
measure's true agreement is 0.60 / 0.70 / 0.75 / 0.80 / 0.85 / 0.90 is **0.22 / 0.52 / 0.69 / 0.84 / 0.94 /
0.99**. On about 120 sibling sessions per half, the 90% half-width at 0.70 is about ±0.07. **The post-vault
count is 15 only if the top-up takes Friday 2026-10-09's session.** The top-up task is therefore moved to Sat
2026-10-10, one day before the subscription is expected to lapse. On 14 sessions the NG/CL read is
UNRESOLVED by rule.

## 6. Checks and controls (each raises)

- **K1, TAS:** for every TAS contract and second from the session open to 14:30, the one-second bar volume
  equals the summed trade size on `ts_recv` (D624's deviation 1) on ≥ 99.9% of seconds. It is checked on the
  siblings and on NG/CL.
- **C1, day shift:** on the siblings' second half, the chosen measure against the NEXT session's truth must
  agree ≤ 0.60.
- **C2, random signs** (seed 625): a random sign per session must agree ≤ 0.60 with the truth.
- **The size field is cast to int64 before any subtraction** (D624's deviation 2). The runner is run with
  `-W error::RuntimeWarning`.

## 7. Reported beside, never gating

- Pearson r against the truth's size.
- The abstention share.
- Agreement against the **true TAS aggressor flow** (does the premium even track TAS buying?).
- Role P at τ = 13:50 and 14:00.
- All three measures on the second half, for the record.

## 8. Files, and what this does not touch

- **Runner:** `scripts/validate_tas_premium.py` (`--siblings`, `--gate`, `--check`, `--selftest`).
- **Output:** `data/ledger_tas_premium_validation.json`.
- **The pull:** `scripts/fetch_ledger_free.py --siblings-tas`.
- **Not read:** no fund data and no price move. No CL or NG data from the vault.
- **Deviations** are listed in the output and never replace a verdict.
