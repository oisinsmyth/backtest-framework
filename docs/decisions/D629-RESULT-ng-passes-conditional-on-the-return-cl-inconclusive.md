# D629 RESULT — signed H1: NG PASSES (provisional), CL is INCONCLUSIVE. NG's pass is conditional on the return control: without it, the window flow runs against the funds

*Filename shortened 2026-09-27 to keep every tracked path within 85 characters (`tests/unit/test_public_cut.py`, D540); was `D629-RESULT-ng-passes-conditional-on-the-return-and-cl-is-inconclusive.md`. The H1 above is the full title.*

*Run once on 2026-09-26 (`scripts/run_signed_h1_stage_a.py --run`, committed `0b08571` after the
pre-registration `2b5406b`). Output: `data/ledger_signed_h1_stage_a.json`, which `--check` reproduces byte for byte.
Sections 1–3 are the registered result. Section 4 is POST HOC (`scripts/explore_signed_h1_decomposition.py` →
`data/ledger_signed_h1_posthoc.json`) and never replaces it. **Every verdict is PROVISIONAL** until the CL/NG check
of Sierra's sign, after D626's read on 2026-10-10 (D629 §6), keeps it or turns it VOID.*

## 1. The verdict

| root | n | β̂ (gate) | t (gate) | placebo t | rotation p50 / p95 (± SE) | verdict |
|---|---|---|---|---|---|---|
| CL | 1,819 | 0.357 (Rubin) | **1.79** (Rubin) | 0.75 | 0.04 / 1.77 (± 0.07) | **INCONCLUSIVE (underpowered)** |
| NG | 1,936 | **0.061** | **4.21** (f_est HC1) | −1.41 | 0.30 / 1.84 (± 0.07) | **PASS** |

- **NG passes all three parts of D629 §5.** β̂ > 0 at t 4.21 (Newey-West 3.45); the placebo is flat (t −1.41); the
  observed t beats the rotation p95 by 2.36, 34 SEs. Under D629 §6, Stage A passes on NG's signed flow. H2 (the price
  test) is next, and the vault's one look goes back to the principal.
- **CL misses the t bar** (Rubin's t 1.79; the f_est HC1 t is 1.91). CL is underpowered (POWER: 0.29 at β = 0.25), so
  under D629 §6 and deposit §9A.2 this is INCONCLUSIVE, not "no effect". **What is excluded: β above 0.76**
  (β̂ + 2 SE, Rubin's SE 0.20).
- **Size of NG's effect:** 0.061 ± 0.015 contracts of net aggressor buying in the window per contract of predicted
  P1. At most about 9% of the predicted rebalance (β̂ + 2 SE = 0.090) arrives as aggressive window flow, against
  the plausible 0.25 stated before POWER ran. The funds' rebalance, as the ledger predicts it, is mostly NOT visible
  as aggressive window flow.
- **Coverage.** NG: every held contract on all 1,936 days. CL: 700 days fully covered (all of era A), and 1,119 era-B
  days on the covered share (median 0.65 of predicted Q).
- **Exclusions.** 20 warm-up days per root and CL's 117 A1-transition days. No day was lost to coverage or a missing
  input.
- **Sign audit.** The panel equals the raw Sierra file on CLU17 and NGU17, 2017-06-20.

## 2. The controls

- **C1, the placebo** (11:50–12:20 against Q at 11:30): CL t 0.75, NG t −1.41. Neither fires.
- **C2, the rotation null** (1,000 rotations, seed 629): p95 1.77 (CL) and 1.84 (NG), each ± 0.07; centres near zero
  (0.04 and 0.30). On NG the margin is decisive. On CL the f_est t (1.91) clears the p95 by 0.14, exactly 2 SE,
  which would be UNRESOLVED (margin) if the t bar had been met.

## 3. Reported beside (never gating)

| fit | CL β (HC1 t; NW t) | NG β (HC1 t; NW t) |
|---|---|---|
| main, f_est | 0.382 (1.91; 2.78) | 0.061 (4.21; 3.45) |
| A3 readings pit / lo / hi, t | 2.77 / 3.85 / 1.19 | 4.06 / 4.51 / 4.17 |
| year fixed effects | 0.384 (1.95) | 0.061 (4.18) |
| **r × year** (the market's flow–return slope free by year) | 0.278 (1.26) | **0.054 (2.34)** |
| signed pre-window flow as a control | 0.383 (1.94) | 0.062 (4.27) |
| largest-share covered contract alone | 0.377 (1.45) | 0.057 (3.84) |
| τ fixed at 14:10 | 0.311 (1.43) | 0.058 (3.98) |
| signal days / no-signal days | 0.18 (0.80) / 1.15 (3.00) | 0.034 (2.04) / 0.099 (0.77) |
| without roll days | 0.386 (1.45) | 0.044 (2.58) |
| CL era A (fully covered) / era B | 0.602 (1.64) / 0.014 (0.22) | — |

- **By year, NG** reaches t > 2 only in 2021 (2.55) and 2024 (2.60). Six of its nine years are below t 1, and 2019,
  2022 and 2025 are negative. **CL** has no year above t 2.
- **Descriptive:** Sierra signs 100% of the covered window volume. sign(S_t) = sign(Q_t) on only **36% (NG)** and
  **44% (CL)** of days (§4 explains why).
- **Not applicable** (D629 §7): Sharpe, Sortino, the trade distribution and the component line. This is a premise
  test on flow and books no position.

## 4. POST HOC: what NG's pass is made of

These were computed after the run to explain the 36% sign agreement. They change no verdict.

- **Without the return control, the relation reverses.** The deposit's H1 as written (S on Q and the flags) gives
  **NG β −0.061, t −7.98**, and CL −0.21 (t −1.61). The window's net flow leans AGAINST the day's return: about
  −60 (NG) and −42 (CL) contracts of net selling per +1% on the return alone (t −11.7 and −3.6), and POWER saw the
  same on the pre-sample. Q moves with the return, so unconditionally the window flow runs against the funds'
  predicted trade.
- **With the return held fixed,** NG's flow leans against the return LESS when the funds are larger: that is the
  +0.061. It is not carried by one year. Leaving out each year in turn gives β 0.046–0.112 and t 3.0–5.1.
- **But it does not look like a proportional footprint.** Split by fund size (contracts per unit return), NG's β is
  1.65 (t 1.28), 0.090 (t 1.03) and **0.008 (t 0.40, SE ≈ 0.02)** from the smallest tercile to the largest. A constant
  6% pass-through would show at about t 3 in the top tercile, where the funds are biggest, and it does not. The pooled
  β comes mostly from BETWEEN the size regimes: in large-fund periods the market's contrarian window flow is weaker.
  That fits the funds absorbing part of the contrarian flow, and it also fits any other change that moved with
  their AUM. The r × year check (t 2.34) removes year-level changes, not changes within a year.
- **CL shows the same shape:** −0.21 without the control, +0.38 with it, and 0.027 (t 0.12) in the top size tercile.

## 5. What this means, and what it does not

- **As pre-registered, the reopening succeeds on NG.** Stage A passes on NG's signed flow (provisionally), and the
  ledger's premise is not dead on NG: a predicted-rebalance term explains window flow beyond the return, the calendar,
  the placebo window and a rotation null.
- **What it does not show:**
  - that the funds' rebalance arrives as buying (the window flow runs against it unconditionally);
  - that the footprint grows with the funds' size (the top tercile is flat);
  - anything about price, which is H2's question.
- **The effect is small:** at most about 9% of predicted P1 as aggressive window flow. That is consistent with
  D628's lead (NG's TAS volume rising with the rebalance): the funds are mostly matched at the settlement price, not
  in the window's order book.
- **Next, for the principal:**
  1. After 2026-10-10: the CL/NG check of Sierra's sign (D629 §6), which keeps or voids each verdict.
  2. Whether to pre-register H2 on NG (the price move into the settlement, in the ledger's direction). Given §4, H2's
     sign is not implied by this pass: the window flow's unconditional direction is against the funds.
  3. The vault's one look stays unread until an H2 pre-registration spends it.
- **The Sierra trial ends 2026-10-17.** Every file this study needs is on disk.
