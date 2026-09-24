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

## What Gate 0b established, for the record (not an amendment)

Each result below is reproduced byte for byte by `--check`. The pre-registered verdicts stand,
and post-hoc findings are labelled in each output.

| instrument | pre-registered Gate 0b | resolution | output |
|---|---|---|---|
| NG (BOIL, KOLD) | **PASS** 99.1% / 98.7% | the funds trade at the BCOM closes of BD5–9 | `data/ledger_gate_0b_ng.json` |
| CL (UCO, SCO) | **FAIL** 88.8% / 88.4% | the Balanced WTI index rolls 50/50 at the BD2–3 closes (Bloomberg BCBCLI methodology, 6/23/2020). Under it, excluding A1's window: 99.74% / 99.48%. Stage C2 is not disabled for CL | `data/ledger_gate_0b_cl.json` |

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
- **Gate 0b from 2024 on** (AITODO 1f) waits on the seal decision (AITODO 2).
