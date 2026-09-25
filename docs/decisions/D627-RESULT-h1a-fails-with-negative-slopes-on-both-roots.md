# D627 RESULT — H1a FAILS on both roots, with NEGATIVE slopes. The premise is killed as pre-registered, and the dependent carried a life-cycle drift the pre-registration missed

*Run once on 2026-09-25 (`scripts/run_h1a_stage_a.py --run`, committed `46e317d` after the pre-registration
`505d83b`). Output: `data/ledger_h1a_stage_a.json`, which `--check` reproduces byte for byte. Sections 1–3 are
the registered result. Section 4 is POST HOC and never replaces it.*

## 1. The verdict

| root | n | β̄ (Rubin) | t (Rubin) | placebo t | rotation p50 / p95 (± SE) | verdict |
|---|---|---|---|---|---|---|
| CL | 1,819 | **−0.737** | **−4.12** | −2.33 | −1.02 / 0.91 (± 0.07) | **FAIL** |
| NG | 1,936 | **−0.102** | **−3.07** | −0.26 | −1.79 / −0.64 (± 0.04) | **FAIL** |

- Under D627 §6 (the principal: FAIL "whatever the controls show"), each root FAILS because β̄ ≤ 0 and t < 2.
- Under A2, each instrument's line is killed. Under A8's kill row, **the premise is killed, because both roots
  fail.**
- Nothing is marginal. Both slopes are negative at |t| > 3 on every reading:
  - Newey-West t: CL −4.49, NG −2.25;
  - A3's four f readings: CL −3.78 to −4.92, NG −2.99 to −3.37;
  - τ fixed at 14:10: CL −4.37, NG −3.31;
  - the micro cost line's τ\*: CL −4.51, NG −3.10.
- Exclusions: 20 warm-up days per root, and CL's 117 A1-transition days. No day was lost to a missing input.

**What the registered numbers say:** a larger predicted P1 rebalance does not come with more abnormal
settlement-window volume on the held contracts. The association, given the controls, goes the other way.

## 2. The controls

- **C1, the placebo.**
  - CL's fires, at t −2.33, with a slope (−0.78) about the same as the window's (−0.74).
  - The association on CL is therefore **not specific to the settlement window**: midday volume shows it too.
  - NG's placebo is flat (t −0.26).
- **C2, the rotation null.** Its centre is **negative** on both roots (p50 −1.02 and −1.79). Part of the negative t is
  structure the rotation keeps (within-year serial structure, and the fitted part of |Q|) rather than day-level
  alignment.
- Neither control changes a FAIL (§6).

## 3. Reported beside (never gating)

| fit | CL β (t) | NG β (t) |
|---|---|---|
| TAS volume, held months | −0.63 (−1.93) | **+0.67 (+4.89; NW 3.15)** |
| largest-share contract alone | +0.21 (+0.23) | −0.11 (−3.16) |
| signal days / no-signal days | −0.40 (−2.71) / −1.25 (−2.60) | −0.01 (−0.17) / −0.26 (−0.86) |
| without roll days | −0.79 (−3.57) | −0.04 (−1.16) |
| CL era A / era B | +0.75 (+0.68) / −0.09 (−1.32) | — |

- **By year,** no single year is significantly positive. CL 2019 (t −2.68) and NG 2018 (t −2.48) are the only years
  past |2|, both negative.
- **β̄ against the plausible effect:** the plausible effect (A9.5) was +0.25. The estimates are −0.74 (CL) and −0.10
  (NG).

## 4. POST HOC, after the run (diagnostics only)

1. **Year fixed effects do not remove it.**
   - CL: −0.71 (t −3.59, NW −3.53).
   - NG: −0.12 (t −2.72, NW −2.08).
   - A guess made on first sight of the result, that the sign came from between-year AUM regimes, is therefore
     wrong, and it is withdrawn.
2. **D627's dependent is not mean-zero.** It carries a life-cycle drift that the pre-registration missed.
   - A_t is positive on 77% (CL) and 74% (NG) of days.
   - The median ratio of today's window volume to its 20-day trailing mean is 1.36 and 1.41. That ratio is uniform
     across the business days of the month, so it is not a roll-day effect.
   - The cause: the index always holds a contract that is moving toward the front, and that contract's volume grows
     all the while it is held. A trailing mean over the same contracts therefore lags.
   - The pre-window control P is built the same way and absorbs some of this. **Whether the drift explains the
     negative slope has not been established.** It is a construction flaw, and it is recorded here so it is not
     repeated.
3. **NG's TAS link survives year fixed effects:** β +0.69, t 3.86, NW 3.16. This is consistent with A8's own caveat
   that the funds may execute at the settlement through TAS rather than in the window. It is a POST-HOC reading of a
   "reported beside" line, and a hypothesis at most. It would need data no one has read.

## 5. What this does and does not settle

- **It settles** Stage A's kill test as pre-registered: FAIL on both roots, so the premise is killed (A8's kill row).
  Under the deposit, Gate 1 then fails and the programme goes to STOP → write-up.
- **It does not show** that fund rebalancing has no footprint:
  - H1a measured window volume on the held contracts;
  - its dependent drifted, as §4.2 shows;
  - on NG, the one line where the funds might plausibly execute (TAS) moves with predicted size, in the expected
    direction.
- **Any corrected or TAS-based test is a new, post-hoc hypothesis.** The in-sample is now spent for H1a-type
  questions. A new test needs data no one has read: the vault (§13A.8's one confirmation look, 2025-03-01 →
  2026-09-18) or forward data. That choice is the principal's.

## 6. Deviations

None from D627. The runner's one recorded interpretation, Rubin's t on NG as well as CL, is in its docstring, which
was committed before the run. It changes no verdict: NG's f_est t is −3.10.
