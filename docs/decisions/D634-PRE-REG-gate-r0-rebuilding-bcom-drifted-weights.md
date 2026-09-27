# D634 PRE-REGISTRATION — Gate R0 of the index-reweight model: can BCOM's drifted weights be rebuilt?

*Drafted 2026-09-27 on the principal's word ("Commit it, then pre-register Gate R0"). It is committed alone, before
its runner exists (R8). The spec is the deposit `INDEX_REWEIGHT_FLOW_PREREG.md` v1.3 §4 and §8 (Gate R0), under the
amendments IR-A1–IR-A12 (`docs/internal/INDEX_REWEIGHT_FLOW_AMENDMENTS.md`, commit `4371f9a`). This record fixes
only what the deposit leaves open.*

## 0. What R0 is for, and what has already been seen

- **Purpose.** Every later part of the model (C0, R1–R3, the 2027 freeze) starts from the drift tracker: the
  weight each BCOM component has drifted to by the new determination date, and so the contracts trackers must
  trade, ΔN_i (deposit §4.3). R0 asks whether that tracker is built right. It is a validation gate, not a
  hypothesis test: it reads no settlement-window flow and no price move after an event.
- **Deposit §8, verbatim:** "Test: reconstructed sub-index returns match any published sub-index or component
  returns within 5 bp per month, where available." And: "**Fail → STOP.**"
- **No published sub-index series is free** (DATA_INVENTORY IR-G10). What is free is the NAV history of the
  ProShares funds whose stated benchmark is a Bloomberg single-commodity subindex, at a daily leverage L. The
  settlement ledger's Gate 0b rebuilt such a fund's NAV from settlements. R0 uses the same model, and that is this
  record's reading of "published sub-index returns" (§3).
- **Seen before this record, all disclosed:**
  - **The ledger's Gate 0b** (`gate_0b_ng_nav.py`), with the same sub-index formula (BCOM §2.8) and the same NAV
    model:
    - BOIL 99.1% and KOLD 98.7% of days within 5 bp over 2017-05-22 → 2023-12-29. Both PASS, and the index's own
      schedule (hedge BD5–9) fits roll days best.
    - `ledger_gate_0b_2024.json`: PASS on 2024-01 → 2025-02 for all four funds.
    - UCO 88.8% and SCO 88.4% over 2017-05 → 2023-12: FAIL. The window includes their 2020 move to a different
      Bloomberg benchmark (the ledger's A1). Their pre-2020 share alone has not been computed.
    - So R0's natural-gas part is largely known in advance. Its new content is the other components, the
      multipliers and the index-level weights.
  - **The index facts** (commit `4371f9a`): the target weights, Table 9a and the determination dates.
  - **No drift, CIM, ΔN or weight** of this model has been computed.
  - **One disclosure (IR-A1):** while checking Westmetall's page layout, the aluminium cash and 3-month prices for
    September 2026 were printed. They are a drift input in the vault, not a flow or price outcome.

## 1. What is rebuilt (deposit §4, IR-A3, IR-A4)

For every target year y from 2016 to 2025 (the in-sample, IR-A1):

1. **The business-day calendar:** BCOM's own definition (IR-A3). A day is a business day when the components open
   for trading carry more than 50% of the commodity index percentages, using the prior year's CIPs up to and
   including the determination date. Each exchange's open days come from its settlement records: a component is
   open on a day when its designated contract has a settlement (CME, the strip; KE, the new pull), a Sierra ICE
   price (IR-A4), or a Westmetall LME price.
2. **det(y):** BCOM business day 4 of January of year y.
3. **Each component's excess-return sub-index I_i(t)**, by BCOM §2.8:
   - on business day d of month m, with p the previous business day,
     R_i,d = ((1−b)·P_L(d) + b·P_N(d)) / ((1−b)·P_L(p) + b·P_N(p));
   - L is month m's lead contract and N is month m+1's (Table 9a);
   - b = 0 on BD1–5, then 0.2, 0.4, 0.6, 0.8 on BD6–9, and 1 from BD10 on (the index Roll Period, BD6–10).
4. **The multipliers.**
   - The formula is BCOM §2.7: ICIM_i = CIP_i·1000 / FPD_S,i at det(y)'s settlements of the January lead,
     CIM_i(y) = ICIM_i·AF, with AF = WAV1(CIM(y−1), FPD_S)/1000.
   - The 2015 CIMs are set the same way from the 2015 targets at det(2015), so the chain starts on 2015 prices.
   - The level of AF does not affect any weight.
5. **The drifted weight (IR-A4):**
   - w_drift,i(t) = CIM_i(y−1)·F_i(t) / Σ_j CIM_j(y−1)·F_j(t), where F_i(t) is the held price;
   - the held price is the lead's settlement outside the roll, and the roll-weighted mix of lead and next inside
     it, with each leg's own settlement (the WAV weights of §2.8);
   - the deposit's §4.2 form, w·I / Σ w·I, is computed beside it.
6. **ΔN_i(y)** (deposit §4.3):
   - ΔN_i(y) = AUM_B(y)·(w_target,i(y) − w_drift,i(det(y))) / (P_i(det(y))·mult_i), with AUM_B from IR-A5;
   - ΔN_i,d = 0.2·ΔN_i on each hedge day BD5–BD9 (IR-A3);
   - written for the 15 CME components and, for §4.5's net-flow check, for all components.

## 2. The inputs, and what must exist before the runner is written

| input | source | status |
|---|---|---|
| CME settlements, all listed months | `fut_settle_strip.csv.gz` (14 roots) | on disk |
| KE settlements | Databento statistics, `fetch_index_reweight_ke.py` | downloading; a KE strip is built the way the other roots' was |
| ICE prices: Brent, gasoil (target year 2019 on), sugar, coffee, cotton | Sierra Chart; the last trade at or before each contract's sourced settlement time (IR-A4, IR-A9) | the list must start **2014-12**, because the 2016 drift runs from det(2015). The ICE settlement times are to be sourced |
| LME prices | `lme_westmetall_daily.csv.gz`, interpolated to the designated prompt (IR-A4) | on disk |
| target weights 2015–2025 | `data/index_reweight/weights/` (2015 is the 2016 file's prior column) | on disk |
| AUM | IR-A5 | fixed |
| the published-return series | ProShares historical NAV CSVs (§3) | BOIL, KOLD, UCO and SCO on disk. **UGL, GLL, AGQ, ZSL, UCD and CMD are pending the principal's approval** (six small CSVs); each one's benchmark and dates are to be sourced from its prospectus |

**The runner is not written until every row above exists.** The published-return set in §3 is fixed from the
prospectus facts before any NAV of it is compared.

## 3. The tests

### R0-a. Known answers (each raises)

- BCOM Appendix C's worked example (Table 13) is reproduced to 0.001 index points on all rows, as in Gate 0b.
- **Weights equal targets at det.** At det(y), with the new CIMs, the weights equal w_target(y) to 1e-12 on every
  component. This is the deposit's "by construction", asserted.
- **The deposit's unit tests (§13), each a failing case first:**
  - 1: weights sum to 1;
  - 2: equal moves leave the weights unchanged;
  - 3: a doubling component gains weight, and its ΔN is negative at an unchanged target;
  - 4: drift beats headline;
  - 5: AUM $100bn, a +0.5% gap, P 50, mult 1,000 gives +10,000 contracts;
  - 6: the daily split sums to ΔN;
  - 7: a 25-component index nets to zero;
  - 8: no price after det;
  - 12: an unmapped product raises;
  - 13: the excluded-year rule.

### R0-b. The published-return check (the deposit's test)

**The series.** Each fund whose sourced benchmark is a Bloomberg single-commodity subindex, over the dates its
filings state that benchmark:

| fund | L | series | expected in-sample span |
|---|---|---|---|
| BOIL, KOLD | +2, −2 | Natural Gas Subindex | 2016-01 → 2025-02 |
| UCO, SCO | +2, −2 | WTI Crude Oil Subindex | 2016-01 → the day before the 2020 benchmark change (dated from the filings) |
| UGL, GLL | +2, −2 | Gold Subindex | 2016-01 → 2025-02, if sourced |
| AGQ, ZSL | +2, −2 | Silver Subindex | the same |
| UCD, CMD | +2, −2 | BCOM itself | its sourced span inside 2016-01 → 2025-02, if any (the fund appears to be closed) |

**The NAV model** is Gate 0b's:
- iNAV_t = NAV_{t−1}·(1 + L·(I_t/I_{t−1} − 1)) + NAV_{t−1}·D·(y/360 − ER/365);
- D is the calendar days between the NAV dates, y the OECD 3-month rate of the prior month, and ER each fund's
  sourced expense ratio;
- splits come from the funds' split records, and a split day is excluded as in Gate 0b.

**Two statistics per fund**, with err_t = (iNAV_t − NAV_t)/NAV_t in bp and missing days counted as failures:
1. **Daily:** the share of days with |err| ≤ 5 bp. It is reported separately on **roll days** (hedge BD5–BD9 and
   index BD6–BD10) and on **other days**. This is Gate 0b's rule, borrowed because it is what catches a wrong roll
   schedule, contract or calendar.
2. **Monthly, the deposit's bar:**
   - the fund-implied subindex return is Π_t (1 + ((NAV_t − NAV_{t−1}·D·(y/360 − ER/365))/NAV_{t−1} − 1)/L) − 1
     over the month's NAV days;
   - the monthly error is the reconstructed monthly return minus the fund-implied one;
   - a month matches when |error| ≤ 5 bp. This record reads "within 5 bp per month" as a share of months, because
     the fund proxy adds its own noise (interest, fees, swap financing, NAV rounding) that a published subindex
     would not.

### R0-c. Coverage, for the 11 CME components without a published series

For HO, RB, ZC, ZS, ZW, KE, ZL, ZM, HG, LE and HE there is no published return, so R0 checks what can go wrong in
the shared code's inputs:
- the lead and next contract each have a settlement on every BCOM business day of their roll and lead months. An
  exact-zero settlement counts as missing.
- the daily sub-index return is finite. |R_i,d − 1| > 20% is listed with its contracts and prices, and never
  dropped silently.

## 4. The verdict

| outcome | condition | consequence |
|---|---|---|
| **PASS** | R0-a holds; every single-commodity series passes the daily rule (≥ 95%) on BOTH roll days and other days and the monthly rule (≥ 90% of months within 5 bp); R0-c has missing lead/next settlements on ≤ 0.5% of business days per component | the tracker is frozen into the model (IR-A10) and C0 may run |
| **UNRESOLVED (proxy)** | the daily rule passes on both subsets, but the monthly rule fails for a fund; or only the BCOM aggregate (UCD/CMD) fails | the error is decomposed (interest and fees, swap-held periods, rounding, roll days) and written up for the principal. C0 waits for their ruling |
| **FAIL → STOP** | any single-commodity series fails the daily rule on roll days, or R0-c's coverage bar fails | deposit §8, "Fail → STOP" |

- **One bug-fix pass is allowed.** R0 exists to find build errors. If a FAIL is traced to a demonstrable code error
  (a wrong contract, month, calendar or unit, shown by a failing unit test written first), the fix is committed
  with that test and R0 is re-run once. Changing a threshold, a schedule, the NAV model or the fund set is not a
  fix. A second FAIL is final.
- **The missing-weight rule (§8)** excludes a year only for a component with **no** price at all (IR-A4). The
  estimated components are present, with their bands.

## 5. Reported beside, never gating

- **The two drift formulas side by side:** IR-A4's CIM × held price against the deposit's w·I/Σ w·I. The largest
  weight difference and the largest ΔN difference, per year.
- **The determination dates:** BCOM's printed dates against the rule-based BD4. 2016-01-06 is BD3 by a weekday
  count; 2018 is printed as Jan 5 and Jan 6; 2022-01-07 is BD5. **The rule-based BD4 is used** (IR-A3), and ΔN is
  also reported at the printed date where they differ.
- **§4.5's net-flow check:** Σ_i ΔN_i·P_i·mult_i over all components, as a share of AUM, per year. Also the
  CME-subset net.
- **The bands (IR-A2, IR-A4, IR-A5):**
  - ICE: Sierra's Brent price against NYMEX BZ's settlement, as the monthly return error;
  - LME: the interpolated return against the pure 3-month return;
  - AUM: the band ends of IR-A5;
  - for each, ΔN of every CME component at the band ends, flagging any year where a band flips ΔN's sign.
- **The sensitivities** of Gate 0b: y = 0; one-day accrual; ER = 0; the NAV rounding floor per fund.
- **The weights over time,** per component: the drifted weight at each det against the prior target (the drift)
  and the new target (the gap).

## 6. The runner

- **File:** `scripts/run_gate_r0.py`, with `--selftest`, `--run` (refuses a second run unless the bug-fix path of
  §4 is logged) and `--check` (reproduces byte for byte).
- **Output:** `data/index_reweight/gate_r0.json`, with a `REQUIRED_OUTPUTS` guard, plus the tracker panel
  `data/index_reweight/drift_tracker_daily.csv.gz` (gitignored, hashed in the JSON).
- **Reads** go through `load_panel(..., reserved_from="2025-03-01")` (IR-A1). No row dated on or after
  2025-03-01 is in memory.
- **The selftest proves the checks can fire:**
  - a roll schedule shifted by one day (trading BD6–10) fails R0-b's roll-day rule on a synthetic fund built with
    the true schedule;
  - a lead contract swapped for the front month fails it too;
  - pairing each NAV with the previous day's index return fails;
  - flipping L fails;
  - the unit tests of R0-a each raise on a deliberately broken input.
- **The sign audit, in contracts:** a component whose drifted weight is below its new target has ΔN > 0
  (trackers buy), and the reverse.
- `-W error::RuntimeWarning`.

## 7. What this does not touch

- **No settlement-window flow, no signed volume and no price move** after any event. None of C0 or H-R1 to H-R4 is
  read.
- **No vault data:** no drift across 2025-03 → 2026-09, and no 2026 event.
- **No 2027 publication of either index** (IR-A10).
- **Deviations** are listed in the output and never replace the verdict.

## 8. Amendment before the runner (2026-09-27): ICE prices are Sierra's daily settlements (IR-A13)

*Written after this record's commit (`8fb1619`) and before any runner code, drift, CIM or ΔN existed.*

- **§2's ICE row now reads:** the ICE daily price is the Close of Sierra Chart's daily file for the contract,
  which is the exchange settlement.
  - It matches the CME strip exactly on 1,095 of 1,095 days (NGH20, ZCH20).
  - It matches NYMEX BZ, which cash-settles to ICE Brent, exactly on 99.99% of 60,867 contract-days (largest
    difference $0.03).
  - All 237 daily files cover their roll periods.
  - The ICE settlement times are no longer an input to R0.
- **§5's bands:** there is no ICE band now. The Brent comparison becomes an R0-a known answer: share of exact days
  ≥ 99.9% and a maximum difference ≤ $0.05, else it raises.
- **Also settled from the facts:**
  - UCD and CMD, which track the BCOM aggregate, end on 2016-08-31, so their check covers January–August 2016 only.
  - UGL, GLL, AGQ and ZSL have NAV files for the whole in-sample (2008-12 → 2026-09).
- **The fund set's benchmark spans, sourced from ProShares Trust II's 10-Ks (CIK 0001415311, cached in
  `data/raw/index_reweight/sec/`).** They replace the "expected" column of §3's table:

| fund | benchmark is the Bloomberg subindex | source |
|---|---|---|
| BOIL, KOLD | throughout (Natural Gas Subindex) | the ledger's Gate 0b sources |
| UCO, SCO | to 2020-09-16 (WTI Crude Oil Subindex). From 2020-09-17 the Balanced WTI index; the ledger's A1 departure window 2020-04-01 → 09-16 is excluded, **so the CL check runs 2016-01 → 2020-03-31** | 10-K filed 2021-02-19: "struck its NAV using its new benchmark for the first time on September 17, 2020" |
| UGL, GLL, AGQ, ZSL | **from 2019-01-07 only.** Before that they tracked the LBMA gold and silver fixing prices (the 10-K filed 2017-03-01 lists them as "Commodity Funds", not index funds) | 10-K filed 2019-03-01: "struck their NAVs using their respective new benchmarks for the first time on January 7, 2019" |
| UCD, CMD | the Bloomberg Commodity Index, **to 2016-08-25**, when they closed to creations and redemptions ahead of liquidation | 10-K filed 2017-03-01 |

  So R0-b checks NG over 2016-01 → 2025-02, CL over 2016-01 → 2020-03, gold and silver over 2019-01-07 →
  2025-02, and the BCOM aggregate over 2016-01 → 2016-08-25.
