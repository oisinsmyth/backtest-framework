# D629 PRE-REGISTRATION — signed H1: does the leveraged funds' predicted rebalance show up as aggressor-signed flow in the settlement window?

*Drafted 2026-09-26. It is committed alone, before its runner exists (R8). The coverage rule is the principal's
(2026-09-26: "score only the covered contracts"). The rest mirrors D627 and A8/A9, with the changes listed in §10.*

## 0. Where this comes from, and what has already been seen

The deposit's Stage A kill test (§9, H1) asks whether predicted `Q_rem` explains **aggressor-signed** window flow.
That flow was not free, and it could not be estimated (D624, D625), so A8 moved Stage A to H1a, a size-only test.
H1a FAILED on both roots (D627), D628 found no line worth the vault, and the programme STOPPED. The write-up
(`SETTLEMENT_FLOW_LEDGER_WRITEUP.md` §7) named "aggressor-signed window trades for the in-sample" as a reopener.
**This record is that reopening.**

**The source.** Sierra Chart's historical 1-tick data (the principal's trial, 2026-09-26) carries a bid/ask
volume split per trade. On the sibling year (HO/RB, 2025-09-25 → 2026-09-18, `check_sierra_aggressor.py`):
- window total volume equals Databento's on every session;
- Sierra's window net flow against the exchange's aggressor flow: **r 0.877 (HO, 686 sessions) and 0.875 (RB,
  694)**, sign agreement 80%;
- the B/A trades match the exchange flag exactly. The error is the ~29% of window volume the exchange marks with NO
  aggressor (spread legs), which Sierra Chart signs by its own rule, with no field to identify it.

Both clear the principal's usability bar (r ≥ 0.8, 2026-09-24). The same check on CL/NG can run only after D626's
single read on 2026-10-10 (§6 makes it a validity condition).

**The coverage.** Sierra Chart serves about five months of ticks before each expiry. All 125 held contracts were
downloaded (`data/sierra_ledger_download_record.json`, commit `bcd5b25`). NG and CL era A are fully covered. From
late 2020, every CL day has at least one held June/December contract whose early months are missing (1,828 of 4,327
CL held contract-days). **The principal chose to score only the covered contracts.**

**Read before this record, all disclosed:**
- **The predictor side, in full**, as in D627.
- **This in-sample's unsigned window volume, and its association with |Q|:** D627 (CL β −0.74, t −4.12; NG β −0.10,
  t −3.07) and D628 (CL negative at 14:28 and at midday; NG flat once the life-cycle drift is removed; NG's TAS
  volume rising with |Q|). **This is the third test on this in-sample with this predictor.** The dependent is new
  (signed flow has never been read on CL/NG here), but the sample and the predictor are not.
- **The signed CL/NG in-sample flow: no association with anything has been computed.** Descriptive reads only:
  - the panel builder's known-answer: Sierra window volume against Databento's `vol_win`, and the sided share
    (§1);
  - three rows of NGF19's spans (2018-07-30 → 2018-08-01), printed while timing the builder.
- **POWER** (`ledger_power_signed_h1.py`, §9) used pre-sample signed flow (2015-07-01 → 2017-05-19) and
  Databento's unsigned in-sample window volume as a scale. It drops every in-sample signed row as the file is
  loaded, before any use (a guard raises if one survives).

## 1. Sample

- **Per root, CL and NG,** every NYMEX business day 2017-05-22 → 2025-02-28 on which τ\* is defined and at least one
  held contract is covered. CL excludes A1's transition (2020-04-01 → 2020-09-16).
- **A held contract h is COVERED on day t** if its Sierra Chart file's first record (ET date, from the panel
  summary) is dated before business day t−20. The trailing norm then lies inside the file. The runner re-derives the
  covered set a second way, from `sierra_ledger_download_record.json`'s `first_utc`, and asserts equality.
- **Planned n** (from POWER's design, before any signed in-sample read), 2017-06-20 → 2025-02-28: **CL 1,819 and
  NG 1,936.** The median covered share of predicted Q is **CL 0.648** and **NG 1.0**. Days with every held contract
  covered: **CL 700** and **NG 1,936**. The runner reports the realised n and every excluded day by reason.
- **Inputs:**
  - `data/ledger_signed_window_daily.csv.gz` (`build_signed_window_panel.py`; Sierra Chart; vault never decoded);
  - `data/ledger_predicted_flow_daily.csv.gz` and `data/ledger_predicted_flow_contracts.csv.gz`;
  - `data/ledger_calendar_flags.csv`; `data/ledger_fut_share_daily_a6.csv.gz`.

  The runner re-asserts that no row is dated on or after 2025-03-01.

## 2. The regression, per root

    S_t = α + β Q_t + γ r_t + Σ δ_k F_k,t + ε_t

- **S_t, abnormal signed window flow:**
  - Σ over the covered held contracts C_t of Sierra's `AskVolume − BidVolume`, 14:28:00–14:30:00 ET (+ = buyers);
  - minus the mean over business days t−20 … t−1 of the same sum over the same C_t;
  - a covered contract with no row on a day traded 0.
- **Q_t:** `q_est` at τ\* (§7.1's earliest pass; 14:10 on a no-signal day) × Σ_{h ∈ C_t} `units_share`(h, τ\*).
  This is the P1 rebalance (K = 0, p = 0, BOIL+KOLD or UCO+SCO, at f_est[t−1] and AUM[t−1]) in the covered contracts
  only. It is **signed**: both funds buy when r > 0.
- **r_t:** the held return from the prior settlement to 14:28 (`r_held` at τ = 14:28), **signed**.
- **F:** D627's flags. For both roots: index_roll_close, fund_roll, expiry, eia_report. CL adds index_annual_roll and
  index_reset; NG adds ng_spot_last3.
- **Estimation:** OLS, HC1 (one row per day, so this is the day-clustered t).

**Why r_t is in.** Q_t is AUM × L(L−1) × r(τ) scaled, so without r_t any flow that simply follows the day's price
(momentum traders, stop orders, the market's own imbalance) would pass. With r_t in, β is identified from how the
flow's response to the return grows with the funds' AUM: the fund mechanism, and nothing that every market shares.

**β's unit:** contracts of net aggressor buying in the window per contract of predicted P1 in the covered contracts.
The plausible effect is β = 0.25 (A9.5), stated before POWER ran.

## 3. The futures share (A3, A4), unchanged from D627

- **NG:** f = 1 is proven except BOIL in 2023 and the carried days of 2025, which use A4's imputation.
- **CL, A4's multiple imputation:** M = 50 paths, seed 20260924; one error e ~ N(0, σ_q²) per (fund, segment),
  f = clip(f_est + e, 0, 1); σ_q = h/1.645 in an ordinary quarter and h in a DISFAVOURED one, h = 0.162; proven days
  are not drawn; Rubin's rules; the gate reads Rubin's t. Q_t on each path keeps the covered share.
- **A3's four readings** (f_est, f_pit, f_lo, f_hi) are each run and reported.

## 4. Controls that must fire

- **C1, time placebo.** The same regression one window earlier, on days whose 11:30 row has no stale leg:
  - S^plc_t: the covered contracts' 11:50–12:20 net flow minus its trailing mean (the same C_t);
  - Q at τ = 11:30 × the covered share at 11:30;
  - r to 11:30;
  - the same flags.

  **It must give |t| < 2.**
- **C2, the rotation null (A9.4).** Q is regressed on the controls, its residual rotated circularly within each year
  by an offset drawn uniformly from [20, n_year − 20], and added back to the fitted part. 1,000 rotations, seed 629,
  each refit with HC1. **The observed t must exceed the rotations' p95**, with p50, p95 and the p95's bootstrap SE
  reported. On CL it runs on the f_est reading.

## 5. What passes

Per root, **signed H1 PASSES** if all three hold:
1. β̂ > 0 with t ≥ 2 (Rubin's t on CL);
2. C1: the placebo has |t| < 2;
3. C2: the observed t exceeds the rotation p95 by more than 2 bootstrap SEs (D373's rule; within 2 SE is
   UNRESOLVED).

## 6. The verdict ladder, and what each outcome does

**The power class decides what a miss means (deposit §9A.2, rules 3 and 5; §9).** NG is `individually_testable`
and takes the ladder as written. CL is `underpowered` (power 0.29 at the plausible β, an upper bound). A CL miss is
therefore INCONCLUSIVE, never "no effect", and is reported with its bound. A CL pass cannot be adopted on
significance alone (rule 3): it is reported and put to the principal.

| outcome | condition | consequence |
|---|---|---|
| **PASS** | all of §5 | NG: Stage A passes on signed flow; the next step is H2 (the price test), and the vault's one look goes back to the principal. CL: reported, not adopted (rule 3), put to the principal |
| **FAIL** (NG) | β̂ ≤ 0, or t < 2, whatever the controls show | the signed route is closed for NG. With CL inconclusive or failing, the reopening ends and the programme stays STOPPED |
| **INCONCLUSIVE** (CL) | β̂ ≤ 0, or Rubin's t < 2 | not detected at 0.29 power. The record states what is excluded: β above β̂ + 2 SE (Rubin) |
| **UNRESOLVED (control)** | t ≥ 2 but C1 fires or C2 is not beaten | the link is not separated from the market's general flow. Written up and put to the principal |
| **UNRESOLVED (margin)** | C2's margin within 2 SE | as above |
| **VOID** | the CL/NG known-answer check (after 2026-10-10) gives r < 0.8 for that root | the result stands as recorded but may not be used: Sierra's sign is not good enough on that root |

**The validity check, fixed now.** After D626's read, `check_sierra_aggressor.py` is extended to CL and NG and run
once on the post-vault sessions D626 reads, with the sibling check's definitions (window 14:28–14:30, ≥ 20
contracts, Databento truth on ts_recv). r ≥ 0.8 keeps the root's verdict; r < 0.8 turns it into VOID. Until then
every verdict is **provisional**, and the result record says so.

**What a pass does NOT say.** Sierra's sign is an estimate (r ≈ 0.88 on the siblings), so β is measured with
noise in S_t. That noise widens the band and does not bias β unless Sierra's rule for the spread legs correlates
with Q beyond r. The pass also covers only the covered contracts: on CL from late 2020, that is the monthly
component and whichever June/December contracts are inside five months of expiry.

## 7. Reported beside, never gating

- The Newey-West t (5 lags) for the main regression and C1.
- A3's four readings on CL.
- **Confound checks on the return control:** year fixed effects; r × year interactions (lets the market's own
  flow–return slope change by year, so AUM's year-to-year growth cannot stand in for the funds); the signed pre-window
  flow (13:30–14:28, abnormal, same C_t) added as a control.
- The largest-share covered contract alone; τ fixed at 14:10.
- Splits: by year; CL era A and era B; signal days vs no-signal days; with and without roll days; fully covered
  days only.
- β̂ against the plausible 0.25, and the implied share of predicted P1 arriving as net aggressor flow.
- Descriptive: the share of window volume Sierra signs; the share of days with sign(S_t) = sign(Q_t).
- **Not applicable:** Sharpe, Sortino, trade distribution and the component line. This is a premise test on flow
  and books no position; H2 carries the price test.

## 8. The runner and its assertions

- **File:** `scripts/run_signed_h1_stage_a.py`, with `--selftest`, `--run` (refuses a second run) and `--check`.
  **Output:** `data/ledger_signed_h1_stage_a.json`, with a `REQUIRED_OUTPUTS` guard: the per-root verdict, β̂, the
  HC1 and NW t, C1, C2's p50/p95/SE, n, and the coverage counts.
- **Lag audit.** D627's `audit_flow` on the predictor panel (every NAV and f date before t; q_est re-derived from
  q1 × f; τ\* re-derived from `gate_pass`).
- **Coverage audit.** The covered set re-derived from the download record's `first_utc` in a second implementation;
  a contract not covered on a day may not enter S_t or Q_t.
- **Sign audit.** Q has the sign of r; S's sign convention (+ = buyers) is re-checked on one contract-day computed
  straight from the raw Sierra file.
- **Right-quantity.** S_t differs from the placebo's S^plc_t, from its own raw level, and from D627's unsigned A_t.
- **Selftest** (no in-sample signed row): the real design with POWER's pre-sample noise; β = 0.5 injected → PASS;
  β = 0 → not PASS; each audit RAISES on a deliberate break (a NAV dated t; an uncovered contract let in; a flipped
  sign); `analyse` runs end to end on synthetic data before the one real run.
- `-W error::RuntimeWarning`.

## 9. POWER (`data/ledger_power_signed_h1.json`, `SETTLEMENT_FLOW_LEDGER_POWER_SIGNED.md`)

Pre-sample noise: Sierra Chart files of the BCOM lead and next contracts held 2015-07-02 → 2017-05-19 (463 fully
covered days per root). The noise is signed abnormal window flow as a fraction of the window's normal volume.

| | CL | NG |
|---|---|---|
| pre-sample mean of the dependent (its t) | 0.008 (0.39) | −0.006 (−0.26) |
| pre-sample slope on the signed return (its t) | −4.05 (−5.55) | −3.10 (−4.06) |
| residual SD; AC(1) | 0.430; −0.010 | 0.467; 0.008 |
| in-sample median \|Q\| (covered) / window volume V | 82 / 809 | 293 / 1,261 |
| size, HC1 (β = 0, 1,000 datasets) | 2.5% | 2.5% |
| rotation control's false-pass rate (β = 0, 100 datasets); combined gate | 9%; 5% | 2%; 1% |
| power, HC1 t ≥ 2: β = 0.05 / 0.1 / 0.25 / 0.5 / 1 | 0.05 / 0.07 / **0.29** / 0.51 / 0.91 | 0.70 / 0.99 / **1.00** / 1.00 / 1.00 |
| β̂'s SD across datasets | 0.35 | 0.021 |
| the combined gate at β = 0.25 | 0.28 | 1.00 |
| power class (§9A.2) | underpowered | individually testable |

- **No drift:** the dependent has mean zero on the pre-sample, so D627's life-cycle failure is absent. A signed
  sum nets out the contract's growing volume.
- **The pre-sample window flow runs against the day's return** (both roots, t −4 to −6). The generic flow–return
  relation is negative and strong, which is why r_t is a gating control and why the r × year check is reported.
- **CL is weak because its window is deep:** the funds' median predicted rebalance is about 10% of CL's normal
  window volume, against about 23% on NG. Measurement error from Sierra's spread-leg rule is not simulated, and A4's
  imputation is not either: both would lower the power further.

## 10. Changes from D627, and why

- **The dependent is signed** (deposit H1 as written), not unsigned volume (A8's retreat).
- **The predictor is signed Q, and the return control is signed r** (it was |Q| and |r|).
- **D627's pre-window volume control is dropped from the gate** and reported beside as signed pre-window flow. Signed
  flow from 13:30 overlaps the time after τ, so as a control it could absorb the funds' own flow.
- **Coverage:** only the covered contracts, in S_t and Q_t alike (the principal).
- **The VOID row** for Sierra's measurement quality on CL/NG.

## 11. What this does not touch, and two things disclosed

- No vault data (2025-03-01 → 2026-09-18): the Sierra files of contracts expiring after February 2025 hold vault
  ticks, and the builder never decodes their prices, volumes or sides (binary search on the timestamps; asserted).
  **Disclosed:** while diagnosing a failed sortedness guard (NGH17: one 2 ms inversion, 2017-01-30), a scan read
  **every record's timestamp** in every file, the vault period's included. That exposes trade timing and counts,
  but no volume, side or price. Nothing from it was tabulated beyond the inversion count.
- **Disclosed:** the builder's known-answer bar was changed after its first run. The first version compared days
  before each Sierra file starts and required exact equality on 95% of contract-days; it fired at 0.33. On covered
  days the exact share is 95.6% (CL) and 94.3% (NG); within 1% it is 99.2% and 98.5%; the total ratio is 1.0009 and
  1.0016. The bar is now within-1% on ≥ 95% per root, with a total ratio within 1%. That compares window volume
  only, which D627 had already read.
- No D626 sample, and nothing from the sibling year beyond the known-answer already committed.
- No price move after τ.
- **Deviations** are listed in the output and never replace a verdict.
