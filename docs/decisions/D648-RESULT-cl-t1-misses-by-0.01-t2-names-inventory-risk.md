# D648 RESULT — CL: the move into the settlement misses T1's bar by 0.01 of a t, T2 names inventory risk (σ²·Q) over square-root impact, and 78% of the move reverts

*One run of `scripts/run_theory_cl.py --run` (runner `2609490`, input `6885fe0`) under D648's pre-registration
(`c56e411`, POWER `66725c8`). Output `data/ledger_theory_cl.json`; `--check` reproduces it byte for byte.
Disclosed before the run: the NG-beside path was exercised while testing the runner, so NG's T2 (SR) was seen before
CL was read (NG is spent; D648 labels it exploratory).*

## 1. The verdicts

| test | statistic | bar | verdict |
|---|---|---|---|
| **T1** CL moves in the funds' direction (739 traded days) | mean **$28.46**, **t 2.230** (NW 1.92); placebo t −0.30; rotation p50 −0.10 / p95 **1.53 ± 0.06** | t ≥ 2.2414, placebo \|t\| < 2, p95 beaten by > 2 SE | **FAIL** — by 0.011 of a t. Both controls clear; the second Holm step (t ≥ 1.96) would pass and is reported beside, not gating |
| **T2** the form (1,819 τ\* days, continuation control) | **t_GM 3.55**, t_SR −0.75, t_mom −0.87; placebo NEITHER | GM iff t_GM ≥ 2 and t_SR < 2 | **GM** (inventory risk) |
| **T3** the reversal, 14:29 → 14:59 against the direction | **$22.34, t 3.18** (78% of T1's mean) | mean > 0, t ≥ 2 | **PASS** |

- **T1 by the letter is a FAIL.** The estimate ($28.46; a pass-through of **0.26** of |I|, against NG's 0.31) is within
  sampling error of POWER's plausible effect, and the controls are clean, but the pre-registered bar is 2.2414 and
  2.230 is below it. The record does not round it up.
- **T2 names GM, and the reading holds under every registered variant:** with year fixed effects t_GM 3.53 / t_SR
  −0.92; without the continuation control 3.45 / −0.93; alone, x_GM t 3.01 (R² 1.9%) against x_SR t 1.63 (R² 0.7%).
  POWER's error rates: at the null T2 names GM 6% of the time, and 8% when SR is true.
- **T3 is the theory's temporary-pressure signature:** most of the move is gone thirty minutes after the settlement.

## 2. What it means

- **On CL, the inventory-risk form fits and the square-root form does not.** Per unit of flow, the move scales with
  the variance of the remaining window, as liquidity providers paid to hold a predictable flow would require. The
  ledger's |I| (square root) is the weaker predictor here.
- **It does not agree with NG.** NG's T2 (exploratory, spent) names SR: t_SR 2.71, t_GM 0.20. One reading: the two
  markets differ in who absorbs the flow (NG's funds are all futures in one contract; CL's are mostly swaps over three).
  Another: one of the two verdicts is the 6–8% false positive. **The form is not settled across markets**; CL supports
  inventory risk, NG (on a sample already read) square-root impact.
- **The mechanism is present on CL but small and not tradable as registered:** net −$3.00 a trade at full size
  ($31.46 cost; the move is 0.90 of it), −$2.15 at one MCL.
- **This admits nothing.** CL's Gate 1 is unchanged (D629's H1 INCONCLUSIVE); no vault is opened.

## 3. Performance, net and gross (T1's trade; CLAUDE.md's four groups)

| | full CL ($31.46) | one MCL ($5) |
|---|---|---|
| mean per trade, gross / net | $28.46 / **−$3.00** | $2.85 / **−$2.15** |
| Sharpe gross / net (SE) | 0.83 / **−0.09 (0.54)** | 0.83 / **−0.63 (0.58)** |
| Sortino gross / net | 1.39 / −0.14 | 1.39 / −0.93 |
| hit rate net; daily skew net | 44.9%; +1.51 | 42.9%; +1.36 |
| exposure; daily vol net; max DD | 40.6% of days; $221; −$11,953 | 40.6%; $22; −$2,194 |
| mean move / cost; breakeven cost | 0.90; $28.46 | 0.57; $2.85 |

**Trade distribution (full, net):** 739 trades, mean −$3.00, **median −$31.46**, win rate 45%, payoff 1.20, skew
0.98, excess kurtosis 6.1. Trimmed means: ex-top 1% −$19.85, ex-bottom 1% +$8.14, both −$8.76. The median sits at
minus the cost: the typical trade loses its cost and the right tail pays.

**What it depends on (gross, per trade):**
- **Years:** 2018 +$146 (t 2.38, 24 trades), 2022 +$59 (t 1.76, 208), 2023 +$21, 2024 **−$19** (85); without 2022
  +$16 (t 1.38).
- **Era:** A (to 2020-09-16, one held contract) **+$109, t 2.17** on 82 trades; B (three held contracts) +$18, t 1.43
  on 657 — the three-way split dilutes it, as §1 of the pre-registration stated and did not test.
- **UCO+SCO AUM terciles:** +$37 / −$9 / +$57. **CL price terciles:** +$32 / +$4 / +$49. **t0:** 13:50 +$29 (687
  trades), 14:00 +$90 (26), 14:10 −$37 (26).
- **Traded − untraded:** untraded days' same rule +$10.65 (t 1.76, 1,080 days); the difference **+$17.81, Welch t
  1.26** — weaker than NG's +$72 (t 5.03): a part of CL's move is generic continuation, not the funds.
- **H4:** the share of the move made by t0+5 is −2%; the move comes later in the window.
- **DSR 0.22** over this record's two configurations. Components ledger: correlations not computable (no daily
  series on disk).

**Nulls (group 4):** the rotation's p50 −0.10 and p95 1.53 ± 0.06 (1,000 draws, seed 648): decisive against the
observed 2.23 (margin 0.70, 12 SE). The placebo t −0.30.

## 4. Reported beside, never gating: the projected-profit rule on CL (point-in-time)

The scale from prior traded days only (≥ 100), trade when the projection ≥ 1.5 × the round trip:

| projection from | size | trades | net per trade | net Sharpe / Sortino |
|---|---|---|---|---|
| **x_GM** (inventory risk) | full | 124 | **+$54.19** | 0.45 / 0.80 |
| **x_GM** | one MCL | 70 | **+$14.91** | 0.77 / 1.53 |
| x_SR (the ledger's \|I\|) | full | 213 | −$1.13 | −0.01 / −0.02 |
| x_SR | one MCL | 116 | +$2.86 | 0.24 / 0.36 |

The form that T2 named also makes the better filter; the ledger's own |I| does not. This is a report on a sample T1
and T2 have now read, not a result; a rule built on x_GM would need its own registration and unread data.

## 5. Next, for the principal

1. **Record the form question as open across markets**: CL (clean) says inventory risk, NG (spent) says square root.
   The joint vault run (A10) is where both can be read once more, on unseen data: NG 2025-03 → 2026-09 already holds
   D630's look; CL's vault holds none.
2. **If the D630 line is carried to the vault with a projected-profit rule** (the post-hoc NG idea), register which
   form it projects from before the run. On CL's evidence x_GM; on NG's own in-sample x_SR. That choice is the
   principal's.
3. CL is not tradable as registered at either size.
