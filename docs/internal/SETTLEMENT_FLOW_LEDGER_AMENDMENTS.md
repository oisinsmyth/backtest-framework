# Settlement flow ledger: amendments to the deposit (v1.9 + A1–A5)

> The deposit, `User-Doc-Deposit/SETTLEMENT_FLOW_LEDGER_PREREG.md` (v1.9), is read-only here. Its §0
> says agreed changes are versioned edits made *before* code. This file is those edits, kept beside
> it. The deposit plus this file is the specification that Stage A and every later stage runs
> under. Each amendment was decided by the principal on 2026-09-24, after the Gate 0b results and
> before any Stage A–I statistic was computed. None was chosen after seeing a flow or price result.
> Nothing in the deposit is deleted. Where an amendment settles a conflict, it quotes both lines.

## A1. Crude oil is co-primary (the deposit as written, "option A")

- CL and NG are both primary instruments, as §2 has them.
- CL's P1 uses an **estimated** futures share for UCO throughout, and for SCO before 2020-Q4.
  SCO is proven swap-free from 2020-Q4 on.
  - Source: `scripts/estimate_fut_share.py` → `data/ledger_fut_share_daily.csv.gz`.
  - The band is ±h, with h = 0.151, the pooled leave-one-out p90 over 53 quarter-ends.
  - The principal: CL "will just be less accurate and should come with smaller size and larger
    error bars". A4 and A5 are those bars and that size.
- **Excluded for CL: 2020-04-01 → 2020-09-16.** Over that window UCO and SCO departed from their
  benchmark during the move to the Balanced WTI index, and only 2020-06-30 is observed. The
  principal accepted this as a partial-information case.

## A2. The Stage A kill rule is per instrument

The deposit has two lines that disagree:
- line 539, H1: "slope > 0 with clustered t ≥ 2, **per instrument**, for Stage A";
- line 964, §14: "H1 fails at Stage A … Kill the ledger premise".

**Settled:** an H1 failure at Stage A kills **that instrument's** line only ("Just crude"). The
ledger premise is killed only when H1 fails at Stage A on **both** CL and NG. H2's Holm–Bonferroni
across the two instruments (line 543) is unchanged, and is still applied across both.

## A3. The CL-alone guard

"Add the guard but keep A, crude has to earn its own place."

- **When it applies:** only if NG fails H1 or H2 and CL passes, so that the study would continue on
  CL alone.
- **What it requires:** before any later stage, the book, or Track 3 runs on CL alone, CL's pass
  must hold under **all four** readings of f_fut:
  1. the interpolated f_est;
  2. the point-in-time f_pit (carried forward from the last published quarter-end);
  3. f_est − h, with the DISFAVOURED quarters at their lower edge;
  4. f_est + h, with the DISFAVOURED quarters at their upper edge.
- **If any reading fails,** CL does not carry the study alone. It is written up as "passes only
  under some readings of the missing holdings data".
- **When both instruments pass,** the guard does not apply. A1 stands as written.

## A4. CL's error bars: multiple imputation over the futures share

H1 and H2 on any day with an estimated f_fut use multiple imputation. This covers CL, and NG's
secondary BOIL-2023 sample. Proven days carry f = 1 exactly and are not drawn.

- **Paths:** M = 50, with seed 20260924. On path j, each estimated quarter segment q of each fund
  receives one error, e_qj ~ N(0, σ_q²). Then f = clip(f_est + e_qj, 0, 1).
  - For an ordinary quarter, σ_q = h / 1.645 = 0.0918, the normal whose p90 of |e| is h.
  - For a DISFAVOURED quarter, σ_q = h (UCO 2019-Q2, 2020-Q2, 2020-Q3, 2023-Q1, 2023-Q2; SCO
    2019-Q2, 2019-Q3).
  - One error is held for the whole segment, matching the estimator's constant band. This is
    conservative, since the true error is zero at a published quarter-end.
- **Each path** reruns the stage and its day-clustered estimate: slope or mean b_j, variance U_j.
- **Combined (Rubin's rules):**
  - b̄ = mean of b_j;
  - T = Ū + (1 + 1/M)·B, where Ū is the mean of U_j and B is the between-path variance of b_j;
  - t = b̄ / √T, with Rubin's degrees of freedom.
  - The pass rule on this t is unchanged: t ≥ 2, and Holm–Bonferroni for H2.
- **Why:** the clustered SE alone ignores error in the predictor. That error biases the slope
  toward zero and does not widen the bars. Imputation widens them honestly.

## A5. CL's size: the futures-share variance enters var_Q1

§4 P1 (line 160) is
`var_Q1 = (AUM × L(L−1) × f_fut)² × σ²_remaining(τ)`, in contract units once divided by
`(multiplier × P_held)`. On days with an estimated f_fut, the amended form is

```
var_Q1 = (AUM × L(L−1) × f_est)² × σ²_remaining(τ)  +  (P1 at f = 1)² × σ_q²
```

- P1 at f = 1 is §4's Q1 with f_fut set to 1.
- σ_q is A4's per-quarter σ; it is zero on proven days.
- **Effect:** the Kalman prior widens, and H7 sizing shrinks by itself. This is §8A's error budget
  applied to f_fut. No separate size haircut is added on top.

## A6. The seal is the deposit's vault (decided 2026-09-24)

The principal chose option B, after the Q25 record below was put to them.
- **In-sample** ends **2025-02-28**. Its start is item 3's decision, no earlier than 2017-05-21.
- **The vault**, 2025-03-01 → 2026-09-18, is the one confirmation look, as §13A.8 has it.
  - It also serves as this repository's R8 out-of-sample test for anything this study would put
    in a book.
- **Every read** in this study goes through `load_panel(..., reserved_from="2025-03-01")`, and the
  study's pre-registration declares that cut.
  - The repository's 2024-01-01 holdout is lifted **for this study's reads only**. Every other
    runner keeps its own cut.
  - The vault guard (deposit unit test 64) is built before any stage reads data.
- **Why:**
  - it is the deposit as written, and §9A's power assumes it;
  - crude's widened error bars need the extra 14 months;
  - Q25 shows that 2024-01 → 2025-02 is no cleaner than the vault for NG and CL, since the same
    four runs read both.
- **Consequences:**
  - Gate 0b is extended to 2024-01 → 2025-02 (AITODO 1f);
  - the trades quote grows by $147.29 (AITODO 6).

## A7. The sample starts 2017-05-22, and C2 runs on a declared sub-sample (decided 2026-09-24)

The principal chose "choice 1" (deposit Q6). §9A and §13A.2 are otherwise unchanged.
- **The in-sample is 2017-05-22 → 2025-02-28** for every stage, except as below.
  - 2017-05-22 is the first session of CME's order-book history, which starts on the evening of
    2017-05-21. That is Stage H's floor.
  - Business days: NG 1,955; CL 1,839 after A1's 2020 exclusion.
- **Stage C2 (the premium) and C3's attention-versus-ETF-volume test (H11a)** run on a declared
  sub-sample, **2018-05-01 → 2025-02-28**. That is when ETF quotes and trades begin on NYSE Arca,
  the listing venue of all six funds. No affordable NBBO exists before 2023.
- **The quote is Arca's best bid and offer mid, in place of the NBBO mid.** That changes deposit
  lines 102 and 199, and is an amendment. The valid-minute rule (line 200) applies to Arca's quote.
- **Known-answer check before C2 runs:** on 2023-01 → 2025-02, where Databento's consolidated
  NBBO also exists, the premium is computed both ways. Their day-level correlation and mean gap are
  recorded in `POWER.md`.
- **The vault uses Arca too,** so the model is fitted and confirmed on one quote source. The NBBO
  version is reported beside it.
- **The retention test for C2** (§6: stage k against k−1, out of sample) compares C2 with C1 **on
  the sub-sample only**, with C1 re-scored there. It does not compare C2's sub-sample against C1's
  full sample.
- Every other stage (A, B, C1, the C3 parts that don't use ETF volume, D, E, F, H and I) runs on the
  full in-sample.

## A8. Stage A without signed flow: H1 becomes H1a (flow SIZE), and direction rests on H2 (decided 2026-09-25)

**Why.** The principal cannot buy aggressor-signed CL/NG trades, and D624 showed that the free one-second bars
cannot estimate settlement-window signed flow (sibling r −0.22 to −0.03 against a bar of 0.8). This A8
replaces the draft the principal held on 2026-09-24, whose first clause (estimated signed flow) died with
D624. The principal's choices are quoted.

**H1a replaces H1 at Stage A** (deposit line 538):
- **Dependent:** abnormal window volume A_t. That is the outright volume in the traded contract over
  W_start → W_end (14:28:00–14:30:00 ET), minus its trailing 20-day mean over the same window. It comes from
  Databento `ohlcv-1s`, which is exact: D624's K1 matched it to the trades contract for contract.
- **Predictor:** |Q_rem| at τ. At Stage A, Q_rem is P1 alone (K = 0, p = 0), in contracts, in the traded
  contract.
  - **τ is the earliest-pass rule's time** (§7.1: 13:50, else 14:00, else 14:10), per the principal.
  - On a day where no candidate signals, τ = 14:10, the last evaluation, because H1a is scored on ALL days,
    not only traded days.
- **Controls** (the principal: "abnormal volume + controls"). Big-move days are busy days, and |Q_rem| scales
  with |return|. Without controls, H1a would pass on the link between volatility and volume alone. The
  controls are:
  1. |the traded contract's return from the prior settlement to 14:28|;
  2. abnormal volume 13:30 → 14:28, as the day's activity, minus its own 20-day mean;
  3. indicator flags for index-roll days, the fund's own roll days, contract expiry and EIA report days.

  With these in place, the coefficient on |Q_rem| is identified by **the same move producing more window
  volume when the funds are larger**, which is the ledger's own claim that flow scales with AUM × L(L−1).
- **Pass:** the coefficient on |Q_rem| is > 0, with day-clustered t ≥ 2, per instrument.
- **Controls that must fire:**
  1. **Time placebo:** the same regression on 11:50–12:20 volume, with the ledger computed at 11:30, must
     give |t| < 2.
  2. **Day shuffle:** |Q_rem| reassigned across days within instrument-year, 1,000 permutations. The observed
     t must exceed the 95th percentile.
- **Reported beside, never gating** (the principal: TAS "yes, reported"): the same regression on abnormal daily
  TAS volume (CLT/NGT, from the session open to 14:30 ET). The funds may execute at settlement through TAS
  rather than in the window.

**Direction rests on H2.** H2, H3, H4 and H5's price placebos are unchanged, and they run on the free 1-minute
bars.
- **Gate 1** (deposit line 946) becomes: H1a and H2 pass at Stage A, **or** H1a passes and a later stage
  lifts H2.
- **The kill row** (line 964) becomes: H1a fails at Stage A → that instrument's line is killed (A2). The
  premise is killed only if H1a fails on both.

**What H1a cannot do, stated so no result is over-read.**
- It cannot tell buying from selling. A flow that arrives but nets, or points the wrong way, still passes
  H1a.
- Only H2 carries direction.
- A pass says the predicted **size** arrives in the window, scaled by fund AUM. It does not say that the
  ledger's signed prediction is right.

**The rest of this amendment:**
- **C2 runs on Alpha Vantage 1-minute bars over the full in-sample,** time-averaged and anchored on the exact
  daily closing premium. IEX's free quotes check the trade-price bias on a sample of days (decided
  2026-09-24). This replaces A7's Arca sub-sample.
- **Stage H is forward-only** until the principal sources order-book history (G5).
- **Blocked until real signed flow exists (G1), and not run on estimates:**
  - Stage B's update step (signed S_pre, line 371);
  - Stage I (individual trade sizes);
  - diagnostics H8a and H9.
- **The retention rule** (line 417) keeps its H2 clause. Its flow clause is read on H1a's quantity: the
  correlation of |Q_rem| with abnormal window volume, net of the controls.
- **The vault look stays free.** The one-second bars run to 2026-09-18.

## Q25: earlier reads of the vault window in NG, CL and the six funds (recorded 2026-09-24)

The deposit's §13A.8 requires "any earlier analysis that touched 2025-03-01 → 2026-09-18 data in NG,
CL or related ETFs" to be recorded. Its standard is that the vault is "clean for these hypotheses,
not a virgin dataset".

This list was made by searching every decision record from D540 on for reads after 2024-01-01 and
for the vault's dates, then reading each hit's own window. **No record below scored a
settlement-window flow, the 14:28–14:30 window, or an ETF premium.**

| record | what was read in the window | on what |
|---|---|---|
| D562 | daily returns, 2024-01-02 → 2026-09-09: the 12-month trend book and carry A (**scored**) | 36 roots, including CL and NG |
| D566 | the NG winter calendar spread's forward read, 2024-01-02 → 2026-09-09 (**scored**, did not transfer) | NG curve |
| D574 | basis momentum's forward read, 2024-01-02 → 2026-09-09 (**scored**); NG was never short | 17 commodity roots, including CL and NG |
| D578 | the disaggregated COT reports 2024-01 → 2026-08 against the 12–24-month strip path (**scored** as a regression) | CL |
| D507 | a quoted-spread census from `tbbo`, 2025-09-11 → 2026-09-10 (no return) | all 41 roots, including CL, MCL and NG |
| D511 | trade counts from `tbbo`, 2025-09-11 → 2026-09-09 (no return) | 8 roots, including CL |
| D604 | a depth census, 2026-08-11 → 09-09, and impact parameters (no return) | CL among the roots |
| D619 | BOIL/KOLD/UCO/SCO NAV, shares and AUM to 2026-09-18, fetched and gated; one day of holdings (no statistic) | the four ProShares funds |
| D620 | 10-Q/10-K holdings filed to 2026 (parsed; no statistic) | all six funds |
| coverage census of the Alpha Vantage pull, 2026-09-24 (after A6) | bar counts per regular-hours session for BOIL/KOLD/UCO/SCO/UNG/USO, 2017-05 → 2026-09. Timestamps only; no price, return or flow read. Later coverage checks stop at 2025-02-28 | the six ETFs |
| item 1, `9147920` | held months checked at quarter-ends to 2026-Q2 and on the 2026-09-18 table; swap P&L from statements of operations to 2025-Q4 (composition only: no flow, price or window statistic) | all six funds |

The ES-only records (D622's in-sample Stage 0, D623's close census and D617's options census) touch
no NG or CL series.

**What this means:**
- The **price path** of NG and CL through the vault has been seen, by the trend, carry, spread,
  basis-momentum and COT lines.
- **Fund composition** in the vault has been seen.
- **Settlement-window flow has not been seen.** No record has scored the signed window flow or a
  window return on NG or CL in any period, in-sample or out.
- The same list covers 2024-01 → 2025-02, which D562, D566, D574 and D578 read in the same runs.
- **The nearest in-sample exposure (2016–2023, not the vault):** D530 tested the equity-index
  leveraged-ETF reset flow.
  - Its control group scored NG and CL's 15:00–15:59 ET continuation. That hour is after NYMEX's
    14:30 settlement, when those roots' volume is only 3–4% of the session.
  - It was withdrawn as dead air, and it touched no bar inside 14:28–14:30.

## What Gate 0b established, for the record (not an amendment)

Each result below is reproduced byte for byte by `--check`. The pre-registered verdicts stand,
and post-hoc findings are labelled in each output.

| instrument | pre-registered Gate 0b | resolution | output |
|---|---|---|---|
| NG (BOIL, KOLD) | **PASS** 99.1% / 98.7% | the funds trade at the BCOM closes of BD5–9 | `data/ledger_gate_0b_ng.json` |
| CL (UCO, SCO) | **FAIL** 88.8% / 88.4% | the Balanced WTI index rolls 50/50 at the BD2–3 closes (Bloomberg BCBCLI methodology, 6/23/2020). Under it, excluding A1's window: 99.74% / 99.48%. Stage C2 is not disabled for CL | `data/ledger_gate_0b_cl.json` |
| all four, **2024-01-02 → 2025-02-28** (A6's added months) | **PASS**: BOIL 100%, KOLD 99.66%, UCO 100%, SCO 100% (291 days each) | the established rules, scored unchanged on days they had never seen. Both predictions held: S0 is NG's best schedule, and the documented BD2–3 roll is CL's best of 20 candidates (the 2017-era S0 gets 88.7% / 87.6%). The one failure is KOLD 2024-01-02, at 5.19 bp | `data/ledger_gate_0b_2024.json` |

- **Business days** for both roots drop holiday republications, meaning days on which every
  settlement equals the prior day's.
- **The strip's holes** on 2020-02-27 and 2020-06-30 are filled from EIA
  (`data/ledger_settle_holes_2020.csv`).
- **UNG and USO roll days are proven 2017–2023.**
  - 2020–2023: USCF's official roll calendar (`data/ledger_uscf_months_rolls_check.json`).
  - 2017–2019: UNG's month-end NAV (`data/ledger_ung_monthly_rolls_check.json`). The documented
    schedule is identified with mean |err| 3.9 bp against 9.3 bp for the best alternative
    (sign test p = 0.02). The known-answer window, 2020–2022, identifies it first.
  - USO 2017 → April 2020 rests on the same documented rule. Its held months match 13 of 13
    quarter-ends, and its roll days have not been checked against NAV.
- **Gate 0b now covers the whole in-sample under A6,** 2017-05-22 → 2025-02-28. The only exception
  is CL's 2020-04-01 → 09-16 window, excluded under A1.
