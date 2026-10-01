# D729 METHOD — the volatility-unit year-concentration report: informational, binds nothing; applied in-sample to the four lines queued for the joint vault run

*2026-10-01.*
- *The principal: "construct a non-binding informational gate on the volatility unit", following
  [D722](D722-DIAG-RESULT-no-variable-explains-2022.md)'s method note.*
- *Numbered D729 after telling the other session (it takes nothing below 730).*
- ***Committed before its code exists.***

## 1. Why

D705's gate (d) asks whether one calendar year carries more than half a line's net, **in dollars**. D722 showed that
this conflates two different things:
- **a line that was more often right in one year** (NQ F2's 2022: REGIME);
- **a line that was equally right, but whose year had bigger moves** (HO's and the MACD arm's 2022: SCALE).

HO's 2022 share was 62 % in dollars and 30 % per unit of volatility.

## 2. The report

**The library function** `backtest_framework.validation.concentration.year_concentration(sessions, gross, scale=None)`:

| input | meaning |
|---|---|
| sessions | ISO dates |
| gross | per-trade P&L, in any unit |
| scale | an optional per-trade volatility in the **same unit** as gross, known before the trade |

**It returns, per calendar year:**
- the count, the sum and the share of the total, for gross;
- the same for u = gross / scale;
- the largest year and its share, and the number of positive years, both ways.

**Its label (informational, a fixed rule):**

| label | when |
|---|---|
| **UNDEFINED** | either total is ≤ 0 |
| **BOTH** | the largest share is > ½ in both units |
| **SCALE-CARRIED** | > ½ in dollars, ≤ ½ in volatility units |
| **VOL-ONLY** | ≤ ½ in dollars, > ½ in volatility units |
| **NEITHER** | otherwise |

**It binds nothing.**
- No existing gate, frozen line or vault criterion changes.
- D705's gate (d) stays as written wherever it is declared.
- A future pre-registration may choose to declare this report as a gate, in its own words.

**The scale used here** (one convention for every root):
- σ20 = the standard deviation of the front contract's same-contract daily settlement log returns over the 20 settling
  sessions ending the prior session (at least 15), from `fut_settle_strip` and `fut_curve_front_next`. A roll is never
  a return.
- **Per trade:** r = gross in dollars / (dollars per point × the prior session's front settlement). For a line scored
  in bp, r = bp / 10⁴.
- u = r / σ20.
- **No hold-length factor:** each line's holds are similar within the line, so a constant factor cancels in its year
  shares. This is stated, not assumed away.

## 3. Applied to the vault-queued lines (in-sample only, through each line's own in-sample function)

**The four queued lines:**

| line | slot | source | known answer asserted first |
|---|---:|---|---|
| NQ F2 book B ([D716](D716-PRE-REG-nq-f2-for-the-joint-vault.md)) | 7 | `diag_d722_lines.load_lines()` L2 | 271 trades, mean net 20.768672… |
| NQ compression C1 ([D680](D680-PRE-REG-the-nq-compression-break-for-the-joint-vault.md)) | 9 | `vault_d680_nq_compression.in_sample()` | its `known_answer` (387 C1) |
| NG Stage A ([D723](D723-PRE-REG-ng-stage-a-for-the-joint-vault.md)) | 3 | `vault_d723_ng_stage_a.in_sample()` | n 1,028, gate mean 66.0214007782101 |
| NG projected-profit MNG ([D649](D649-PRE-REG-ng-projected-profit-line-for-the-joint-vault.md)) | 8 | `ledger_vault_pp_ng.in_sample()` + `select` | 270 trades, $15.43 |

**Reference rows** (not queued, from D722's tables): ES F2, D699 V1, HO F2 and the MACD arm. These show the label on
lines D722 already read as SCALE or REGIME.

**Windows and seals:**
- **Each line is read only over its own in-sample window:** NQ F2 to 2023-12-29; D680, D723 and D649 to 2025-02-28.
  The 2024-01 → 2025-02 slice was spent by those three lines' own development.
- **NQ's and NG's settlements are read below 2025-03-01 only.** Nothing in the vault is opened, and no `--vault` mode
  runs.
- **NQ F2's unseen window starts 2024-01-01.** No statistic here is computed on NQ F2 trades after 2023. NQ's daily
  settlement volatility for 2024–25-02 enters only as the scale of D680's own in-sample trades.
- **Output:** `data/report_d729_vol_unit_concentration.json`, aggregates only (per-year sums and shares).

## 4. The code's assertions (unit tests, each canary shown to fail)

1. **A hand example** reproduces exact shares.
2. **A synthetic SCALE year** (one year's gross and scale both multiplied by 3) reads SCALE-CARRIED. The same year with
   its gross alone multiplied reads BOTH.
3. **Invariance:** multiplying a year's gross and scale by the same factor leaves the vol-unit shares unchanged.
4. **UNDEFINED** when a total is ≤ 0.
5. **Bad input raises:** a scale ≤ 0 or non-finite, mismatched lengths, a non-ISO session.
6. **In the report script:**
   - the seal (a planted 2025-03-01 settlement raises);
   - the σ20 lag (a same-day σ must be caught by a second implementation);
   - each line's known answer.

**No predictions:** this is a report, not a test.

## 5. The report, applied (2026-10-01): informational, binding nothing

**The commits:**
- the code is `c1ef11a5`, with its unit tests (four broken versions each caught);
- the fix is `ab355138`;
- the output is `data/report_d729_vol_unit_concentration_v2.json`.

**A disclosed error, caught before anything was recorded.** The first run (`data/report_d729_vol_unit_concentration.json`,
kept as evidence) passed each trade's return, not its dollars, as the gross. Its "dollar" column was therefore a
return-unit share (the price level removed). v2 passes dollars against the dollar scale (dollars per point × price ×
σ20), as §2 declares, and reports the return-unit shares beside. **The shares are of gross P&L.** D705's gate (d)
reads net, which this report does not restate.

| line | n | largest year, \$ | largest year, return units (beside) | largest year, vol units | label |
|---|---:|---|---|---|---|
| **NQ F2 book B** (D716, slot 7) | 271 | 2022 60 % | 2022 52 % | **2022 55 %** | **BOTH** |
| **NQ compression C1** (D680, slot 9) | 387 | 2024 34 % | 2022 22 % | 2024 26 % | **NEITHER** |
| **NG Stage A** (D723, slot 3) | 1,028 | 2022 62 % | 2022 41 % | 2022 44 % | **SCALE-CARRIED** |
| **NG projected-profit MNG** (D649, slot 8) | 270 | 2022 75 % | 2022 62 % | **2022 61 %** | **BOTH** |
| ES F2 (D707, withdrawn; reference) | 252 | 2022 51 % | 2022 45 % | 2022 45 % | SCALE-CARRIED |
| D699 V1 (closed; reference) | 572 | 2022 60 % | 2022 49 % | 2022 58 % | BOTH |
| HO F2 (D719, closed; reference) | 239 | 2022 62 % | 2022 47 % | 2019 31 % | SCALE-CARRIED |
| the MACD arm (admitted; reference) | 1,708 | 2020 43 % | 2020 44 % | 2020 40 % | NEITHER |

**What the labels say about the queued lines:**
- **NQ F2 and the NG MNG line lean on 2022 even per unit of volatility.** That is a concentration of direction, not of
  size. It matches D722's REGIME reading for NQ F2.
- **NG Stage A's 2022 is mostly size.** In volatility units 2024 nearly matches it (36 % against 44 %).
- **The NQ compression break is the one queued line with no year dependence** (7 of 8 years positive).
- **Nothing changes:** no slot, no vault criterion and no frozen file is touched by this report.

