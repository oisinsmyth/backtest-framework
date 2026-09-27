# Index reweight flow: amendments to the deposit (v1.3 + IR-A1–IR-A14)

> The deposit, `User-Doc-Deposit/INDEX_REWEIGHT_FLOW_PREREG.md` (v1.3), is read-only here. Its §0.2
> says agreed changes are versioned edits made *before* code. This file is those edits, kept beside
> it. The deposit plus this file is the specification that Gates R0 and C0 and Stages R1–R3 run
> under. Written 2026-09-27, before any drift, flow or price statistic of this model was computed.
> Nothing in the deposit is deleted. Where an amendment settles a conflict, it quotes the deposit's
> line.
>
> Each amendment says where it comes from:
> - **the principal**: a decision taken on 2026-09-26/27;
> - **fact**: a correction the deposit asked for ("Verify."), settled from a source in
>   `data/index_reweight/SOURCES.md` or `SOURCES_GSCI_CFTC.md`;
> - **proposed**: Claude's, written on the principal's instruction "write the amendments". It stands
>   unless the principal overrules it before the Gate R0 pre-registration is committed.
>
> The amendments are numbered IR-A*n* so they cannot be confused with the settlement ledger's A1–A10.

## IR-A1. The sample split (from the programme rule A10)

*Source: the principal (A10, 2026-09-26).*

No model opens the vault (2025-03-01 → 2026-09-18) by itself, so this model's periods are:

| period | January events | monthly roll periods | read |
|---|---|---|---|
| **in-sample** | 2016–2025 (10) | 2016-01 → 2025-02 | Gates R0 and C0, Stages R1–R3 |
| **vault** | 2026 | 2025-03 → 2026-09 | only in the joint vault run |
| **forward** (Track 2) | 2027 | from 2026-10 | after the freeze (IR-A10) |

- Every read of a price, a flow or a settlement uses `reserved_from="2025-03-01"` (D594's helpers).
- **Deposit §11, Track 1 ("2016–2026 events").** January 2026 moves from Track 1 to the vault.
- **The yearly sign test (§8B.2) keeps its rule,** one-sided binomial p < 0.05, and the count follows from it:
  - in-sample, 10 votes: **≥ 9 of 10** (p ≈ 0.011);
  - at the joint run, 2026 is the 11th vote: ≥ 9 of 11 (p ≈ 0.033);
  - with 2027, 12 votes: **≥ 10 of 12** (p ≈ 0.019; 9 of 12 gives p ≈ 0.073 and fails).
- **The consistency test (§11 v1.3)** applies to 2026 at the joint run exactly as it applies to 2027. Its Track 1
  intervals come from 2016–2025 only.
- α sits in the programme's fixed slots of 0.005 per family, so the joint run changes no bar.

## IR-A2. Estimates are allowed, with measured bands

*Source: the principal's standard for the programme (2026-09-24).*

An input that cannot be observed may be estimated if the estimate is directionally correct. It then carries a band
measured on data where the truth is known, and every result that depends on it is reported at both ends of the
band. IR-A4, IR-A5 and IR-A7 are such estimates.

## IR-A3. The execution days are business days 5–9; the multipliers are set on business day 4

*Source: fact (deposit §3.2 line 68: "understood to run over the 6th–10th business day … **Verify.**").*

The BCOM methodology (every version, 2016–2026) defines two windows:
- the index **Roll Period**, business days 6–10, over which the index level moves from the old weights to the new;
- the **Hedge Roll Period**, business days 5–9, where a book that replicates the index trades, 20% at each close.

**Settled:**
- The execution days of Stage R1 and of every monthly roll in Gate C0 are **BD5–BD9**, and φ_d = 0.2 on each.
  "6th–10th" in §3.2 and §6 reads as BD5–BD9.
- **A business day is BCOM's:** a day on which the index commodities open for trading carry more than 50% of the
  commodity index percentages. It is not the CME calendar. The code implements this definition from the exchanges'
  holiday calendars. Where it disagrees with a date BCOM printed, the disagreement is reported in Gate R0.
- **The determination date** (deposit §3.2, "CIM determination date") is **BD4 of January**, at that day's
  settlements of the January lead contracts. So ΔN on det uses BD4 settlements, and a forecast before det uses the
  latest settlements available at the forecast time (§0.6, unchanged).
  - Three printed dates are checked in Gate R0 against the business-day rule: 2016-01-06, 2018-01-05/06 and
    2022-01-07.
- **GSCI** rolls on its own BD5–BD9 at 20% a day, and its January reweight happens inside that roll (S&P GSCI
  Methodology, August 2026, p.12). The two indices trade on the same days. Whether their κ values separate is still
  decided by C0's own test (R-D4), which C0's pre-registration fixes.
  - GSCI holds no ZL, ZM or COMEX copper, so its term is zero for those three.
- **The January roll.** Of the 15 CME components, only live cattle, lean hogs and gold roll contracts in January
  (Table 9a). For the other 12, the January flow is the reweight alone.

## IR-A4. The non-CME prices: Sierra Chart for ICE, Westmetall for LME

*Source: the principal ("Can you not get this data from Sierra Chart?"; "Yes to both", 2026-09-27).*

Deposit §3.3 asks for daily settlements of every component, with the ICE and LME sources to be confirmed (R-Q3).

| components | weight (target years 2016–2026) | source | the daily price |
|---|---|---|---|
| ICE Europe: Brent, low-sulphur gasoil (from target year 2019) | 7.5–11.3% | Sierra Chart intraday files (Package 3; `sierra_index_reweight_download.py --set ice`) | the last trade at or before the contract's settlement time |
| ICE US: sugar, coffee, cotton (cocoa only from 2026, in the vault) | 7.0–9.2% | the same | the same |
| LME: aluminium, zinc, nickel, lead (from 2023) | 9.4–10.7% | Westmetall's free LME official cash-settlement and 3-month prices (`fetch_westmetall_lme.py`) | interpolated to BCOM's designated prompt: cash + (3M − cash) × (days to prompt ÷ days to the 3-month date) |

- **These are estimates (IR-A2).** Their bands are measured before Gate R0 reads a drift:
  - **ICE:** the Sierra Brent price against NYMEX BZ's settlement (on disk, in `fut_settle_strip`) on the same
    days. The component's monthly return error is the band.
  - **LME:** the interpolated return against the pure 3-month return. The absolute difference, per month and
    component, is the band.
- **Every ICE settlement time is sourced** (with its effective dates) before it is used, as for CME windows
  (§3.4, IR-A9).
- **§8, Gate R0's missing-weight rule** ("If the missing components exceed 10% of index weight in a year, that
  year is excluded") counts a component as missing only when it has **no** price. An estimated price is present,
  with its band. No in-sample year is therefore excluded on this rule unless a source fails.
- **Cross-check, reported, never used:** the BCOM aggregate excess-return index level against the reconstructed
  index, if a free history is found.
- **The drift formula is BCOM's own.** A component's drifted weight is CIM_i·P_i(t) / Σ_j CIM_j·P_j(t), with the
  CIMs set on det from the targets. The deposit's §4.2, w·R / Σ w·R, equals this only when there are no roll
  gaps. Gate R0 reports the two side by side.

## IR-A5. BCOM tracking AUM in the years it is not published

*Source: proposed.*

AUM is published for 2019 (~$85bn), 2022 (> $100bn), 2023 (> $110bn), 2024 ($105.5bn), 2025 ($102bn) and 2026
($108.8bn). It is not stated for 2016–2018, 2020 or 2021.

| year | point value | band |
|---|---|---|
| 2016–2018 | 85 (2019's figure, carried back) | 60–110 |
| 2020, 2021 | linear between 2019 (85) and 2022 (100): 90, 95 | ±15% |
| 2019 "~85" | 85 | ±10% |
| 2022 "> 100", 2023 "> 110" | 100, 110 (the stated floors) | the floor to +10% |
| 2024–2026 | as published | none |

- **AUM scales every component's ΔN in a year by the same factor.** So the cross-sectional statistics do not
  depend on it: the yearly Spearman sign test, construction B's ranking and the label shuffle. They are reported
  first.
- **What does depend on it:** the |I| ≥ 3 × RT gate and κ's scale. Those results are reported at both ends of the
  band.

## IR-A6. Roll periods per contract, and the C0 power table

*Source: fact (deposit §5: "about 12 calibration events a year per contract").*

BCOM rolls each component 4–7 times a year, not 12 (Table 9a):
- energy 6;
- grains, copper, gold and silver 5;
- live cattle 6;
- lean hogs 7.

GSCI rolls its energy contracts monthly, and its grains, softs and precious metals 4–5 times. §8B.1's C0 row
(~9,000 observations over 120 roll periods × ~15 contracts) is recomputed from the real counts in `POWER.md` before
Gate C0 runs. This is the deposit's own rule (§8B.1: "estimate … before Stage R1 runs").

## IR-A7. Signed window flow comes from Sierra Chart, validated per contract

*Source: the principal ("Sierra Chart, free", 2026-09-27).*

- **Source:** Sierra Chart 1-tick files. The aggressor side is taken from the ask and bid volume. The download list
  is BCOM's lead contract for every month 2015-12 → 2025-03, 775 contracts
  (`sierra_index_reweight_download.py`).
- **It is not the exchange's flag.** On HO/RB the net window flow correlates at 0.877 and 0.875 with Databento's
  exchange-flagged trades.
- **The check, per contract, before Gate C0 reads any flow:** Sierra-signed against exchange-signed window net
  flow, on sessions outside the in-sample and the vault.
  - For the 11 non-energy roots: Databento `trades` from 2026-09-19 onward (free, the last 12 months).
  - For CL, NG, HO and RB: the same sessions, but only after D626's single read on 2026-10-10.
  - The check reads the two flows only. It never relates flow to a predicted flow or to a price.
- **The bar:** r ≥ 0.8, the programme's (G1). A root below it is excluded from C0 and from R1's flow statistics,
  and is never defaulted.
- **CL and NG** use the files already on disk from the ledger. Their check is the one D629 §6 already schedules.

## IR-A8. KE, the one CME component not bought

*Source: the principal ("Yes, download", 2026-09-27).*

KE's settlements and definitions, 2010-06-06 → 2026-09-26, were ordered free from Databento on 2026-09-27 (UTC
2026-09-26 23:21). The script is `fetch_index_reweight_ke.py` and the job record `data/index_reweight_ke_jobs.json`;
both jobs were re-quoted at exactly $0.00 before submission. KE is in the traded universe like the other 14.

## IR-A9. Settlement windows are sourced before they are used

*Source: fact (deposit §3.4: "No window time may be assumed").*

`data/settlement_windows.csv` holds sourced windows before 2026-09-21 for the four energy roots only. For the other
11, windows with effective dates are sourced from CME's settlement-procedure notices before Gate C0 runs. For a
(root, date) with no sourced window, `window_for` raises, and that root and date are excluded from C0 and R1. The
same holds for the ICE settlement times of IR-A4.

## IR-A10. The freeze, and what may not be read before it

*Source: the principal ("Freeze code + rules", 2026-09-27), and deposit §11 / R-D8.*

- **When:** before the earlier of BCOM's and GSCI's 2027 announcements.
  - BCOM announced between 10-20 and 11-09 in 2015–2025; GSCI in early November.
  - **Target: Friday 2026-10-16.**
- **What is frozen** (`scripts/freeze.py`, into `results/index_reweight/FROZEN_2027.json`):
  - the code hashes of the drift tracker, the flow formula, the C0 fitting code, the gates and the trading rules;
  - the hashes of every input on disk at the freeze.
- **If C0 is not finished by then,** κ is whatever the frozen code returns on the in-sample data, computed after
  the freeze. Nothing about 2027 can move it.
- **After the freeze,** a code change is allowed only as a logged bug fix, versioned here with the reason.
- **Until the freeze,** no one reads any 2027 BCOM target-weight or GSCI CPW publication, including a pro-forma or
  an advisory-panel document. GSCI's advisory pro-forma is published about a month before its announcement.

## IR-A11. The CFTC variants (R-Q10)

*Source: proposed; the deposit asks for it to be pre-registered "before any fit".*

- The CIT supplement exists only as **futures-and-options combined**.
- So the swap-dealer proxy (§5A.3) uses the **futures-and-options combined Disaggregated** report, like for like.
  - The repo's `cftc_cot_raw` is futures-only, so the combined series is fetched when 5A runs.
- The CIT covers 13 agricultural markets and **no energy or metals**.
- **Soybean meal** is in the CIT only from 2013-04-05. Its fit starts there.
- Neither report is on disk yet; `DEPOSIT_INFRASTRUCTURE_TRACKER.md` line 158 is wrong about the CIT.

## IR-A12. GSCI's scale

*Source: fact (the S&P GSCI methodology; SOURCES_GSCI_CFTC.md).*

- **GSCI publishes no tracking-AUM estimate.** Its "Investment Support Level" is explicitly "not an accurate
  estimate" of invested assets.
- **So §4.4's κ_G multiplies GSCI's January flow per unit of index quantity:** the change in CPW, times the
  normalizing constant, times the contract size. It absorbs the unknown AUM. No GSCI AUM figure is ever entered.
- **The GSCI weights** for 2017 come from a third-party mirror of S&P's February 2018 methodology. That mirror's
  other column matched S&P's own 2019 figures on all 24 rows. The 2016 document swaps the lead and nickel labels.
  Both are flagged in the sources and carried as they are.

## IR-A13. The ICE prices are Sierra Chart's daily settlements (revises IR-A4's ICE row)

*Source: fact, and within the principal's "Yes to both" (Sierra Chart for ICE). Written 2026-09-27, after
IR-A4 and before any drift, CIM or ΔN is computed.*

- **Why IR-A4's ICE row changes.**
  - Sierra Chart's intraday ICE files hold about five months per contract. Many contracts therefore miss their
    roll-in period (for example SBH20 starts 2019-09-30, after the September roll into it).
  - Sierra's DAILY files (`.dly`) hold each contract's whole life. **Their Close is the exchange settlement:**
    - it equals the CME settlement strip exactly on NGH20 and ZCH20, 1,095 of 1,095 days (2018–2020);
    - on ICE Brent it equals NYMEX BZ's settlement (BZ is cash-settled to ICE Brent, with the same month label)
      exactly on 99.99% of 60,867 contract-days (55 contracts, 2016 → 2025-02). The largest difference is $0.03.
  - All 237 ICE daily files span their roll-in to their roll-out
    (`data/index_reweight/sierra_download_record_ice.json`, `daily_covers`).
- **Settled:**
  - the ICE daily price is the Sierra daily file's Close, taken as the exchange settlement;
  - it is not an estimate, so IR-A4's ICE band, the last-trade rule and the ICE settlement times are no longer
    needed for pricing;
  - IR-A9's ICE clause lapses; its CME clause stands.
  - The Brent comparison above is written into Gate R0's output as a known answer.
- **Unchanged:** the LME row of IR-A4 (Westmetall, interpolated, with its band). CME prices remain the settlement
  strip; KE's come from its own pull, with Sierra's daily file as a cross-check.

## IR-A14. Gate R0's rulings after its UNRESOLVED (proxy) run

*Source: the principal, 2026-09-27 ("Go with your recommendations, fill the holes and rerun R0"), on
D634-RESULT §5. Written after that result and before the re-run.*

1. **The 2020 holes are filled and R0 is re-run once.**
   - `fut_settle_strip` lacks most CME roots on 2020-02-27 and 2020-06-30. Those settlements are filled from Sierra
     Chart's daily files, and only where the strip has none (`scripts/fill_strip_holes_2020_sierra.py` →
     `data/index_reweight/strip_holes_2020_sierra.csv`, 44 settlements across 13 roots).
   - **Known answers:** Sierra equals the strip exactly on 156 neighbouring cells, and equals the ledger's EIA fills
     for CL and NG on all 4 shared cells.
   - The re-run writes `gate_r0_rerun.json` and `drift_tracker_daily_rerun.csv.gz`, and happens once. The first
     run's output stays as it is and reproduces byte for byte.
2. **UNRESOLVED (proxy) is resolved by the long/short pair split** (D634-RESULT §4). For each single-commodity pair,
   the rebuild's part of the monthly error (the half-sum of the two funds' errors) must be within 5 bp in ≥ 90% of
   months, with both daily rules passing and coverage holding. **The re-run's tracker is then the one that is
   frozen.**
3. **The LME stays a measured band.** It moves any weight by at most 0.015% and flips no ΔN sign. The BCOM
   aggregate check (UCD/CMD) is reported and does not gate.
4. **det stays the rule's BD4** (IR-A3). BCOM's printed dates are reported beside.

## IR-A15. One vault day is opened for the 2026 multipliers; the freeze is run now

*Source: the principal, 2026-09-27: "Allow the single-day read, freeze now, and schedule daily recording". Written
before the freeze and before any 2026-01-07 settlement is read.*

- **The exception to A10.** Forecasting the 2027 rebalance, and scoring it, needs CIM(2026): each component's 2026
  target over its lead-contract settlement on det 2026 = **2026-01-07** (BD4, IR-A3; BCOM's printed date agrees).
  That day is inside the vault (2025-03-01 → 2026-09-18).
  - **Read:** the settlement of each of the 25 components' January lead contract on 2026-01-07, and nothing else.
    That includes CL, NG, HO and RB (all March 2026). No other vault day, no intraday data, no return.
  - **Use:** an index fact (the 2026 multipliers), written to `data/index_reweight/track2/cim_2026.json` with the
    ruling inside it. It enters no tested outcome of 2016–2025, and no C0 or R-stage run reads it.
  - **How:** `record_index_reweight_2027.py --cim2026`, which refuses without `track2/cim2026_ruling.json`. The
    Sierra daily file of an expired contract holds its whole life, so the reader splits only the line dated
    2026-01-07 into prices; the Westmetall 2026 page is parsed for that date alone (its bytes are kept as fetched).
  - **Cost to the vault:** the programme's joint vault run later sees one day it did not see first. The 2026 event's
    own scoring (R-stages on the vault) needs BD5–9 and later days, which stay closed.
- **The freeze runs now,** ahead of the 16 October target, on the code as committed with this amendment. Gate C0 has
  not run: κ is what the frozen `run_gate_c0.py` returns on the in-sample data (IR-A10).
- **Before the freeze, the recorder's readers were narrowed** (a bug fix of the same kind as the D626 guard): the
  Sierra daily reader and the Westmetall parser now parse only the wanted dates. Re-run on the 125 recorded
  settlements, it returns all 105 Sierra values bit-identically and records no revision.
- **Daily recording:** a scheduled task runs `--settlements --refresh` each morning, and `--forecast` once the 2027
  targets are transcribed. It commits nothing.

## IR-A16. A logged bug fix after the freeze: the frozen file moves to `data/`, and the model is re-frozen

*Source: the principal, 2026-09-27 ("Move and re-freeze"), on the suite finding below. Written before the change.*

- **The bug.** The IR-A10/IR-A15 freeze wrote `results/index_reweight/FROZEN_2027.json`. This repository has no root
  `results/`: rendered pages live in `docs/results/` and machine-readable state in `data/` (D592). Two tests enforce
  that (`tests/unit/test_crosswalk.py`, `tests/unit/test_programme.py`), and both went red at the freeze commit
  (`dc4bf97`). The settlement ledger's frozen file already lives in `data/`.
- **The fix, one line of one frozen file:** `scripts/freeze_index_reweight_2027.py`'s `OUT_DIR` changes from
  `results/index_reweight` to `data/index_reweight`, and its docstring follows. No other code, input or parameter
  changes.
  - The first freeze (content_sha256 `11c54c31…`, spec `4945c1f`) is kept, renamed, at
    `data/index_reweight/FROZEN_2027_superseded_4945c1f.json`.
  - The new freeze is `data/index_reweight/FROZEN_2027.json`. Its hashes must equal the first freeze's on every file
    except the wrapper, and that is checked before the new file is committed.
- **Nothing was run between the two freezes:** no C0, no R-stage run, and no 2027 publication was read. The daily
  recorder is not a model run.
- **Found at the same time, not changed here:** D636 promises that every R-stage configuration is logged in
  `results/index_reweight/trials.csv` (read `data/index_reweight/trials.csv`, D592's translation), but the frozen
  runners write no trials file. The log is to be derived from each runner's own JSON output after its run, by a
  script outside the freeze, since outputs are not hashed. That is proposed, not yet ruled.
