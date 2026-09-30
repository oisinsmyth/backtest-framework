# Joint vault run: checklist (programme slots 3, 7, 8, 9)

*Prepared 2026-09-30, before the Databento CME subscription lapses (~2026-10-11). Nothing here opened the vault.
The vault is 2025-03-01 → 2026-09-18. The principal calls the run (A10).*

**Recorded decision.** The principal said "go with your full recommendation" on 2026-09-30. D680's frozen
`--vault` therefore runs through a joint-run wrapper, `scripts/joint_d680_vault.py`, and no amendment record is
written. The wrapper holds `stage0_d663_per_root_gamma_break.RESERVED_FROM` at 2026-09-19 for the frozen runner's
own call, and restores it however the call ends. This is D698's `raised_cut` mechanism. No frozen file is edited.
The D630 §8 path is `scripts/build_ledger_vault_inputs.py`. It needs no new decision number.

## 0. Before anything: verify (all must pass)

| check | command | 2026-09-30, before / after this prep |
|---|---|---|
| NG Stage A freeze (20 code files, 12 fixtures) | `uv run python scripts/verify_ledger_stage_a_ng.py` | VERIFIED / VERIFIED |
| D716, D680, D707 (withdrawn), D649: each runner's own hash check (runner, record, `imported_unchanged`) | run in each `--vault`. Pre-flight: `uv run python scripts/joint_d680_vault.py --selftest` (D680). The other three are checked the same way | 4 of 4 OK / 4 of 4 OK |
| `freeze.py` guards | `uv run python scripts/freeze.py --selftest` | 9 checks raise / same |
| D680, D649 self-tests (synthetic) | `uv run python scripts/vault_d680_nq_compression.py --selftest`; same for `ledger_vault_pp_ng.py` | OK / OK |
| D680 input path (synthetic) | `uv run python scripts/joint_d680_vault.py --selftest` | OK, 6 checks fire |
| NG input path (synthetic) | `uv run python scripts/build_ledger_vault_inputs.py --selftest` | OK, 6 checks fire |

**Do not run D716's `--selftest` or `--known-answer` before the run.** D711's `load_root` reads the whole rth
fixture, 2024+ rows included, before it filters.

## 1. Inputs for 2025-03-01 → 2026-09-18 (metadata only)

Sources: file names, sizes, `.meta.json`, job records, and DBN header start/end. The SPY row also used date keys.

| line | input | on disk through | raw source | 10-09 top-up covers the gap? |
|---|---|---|---|---|
| 7 D716 | `fixtures/fut_{ES,NQ}_rth_1m` (D462) | **2026-09-09**. Built 09-13 from ohlcv-1m, whose last file header ends 2026-09-10T00:00Z. D716 §3 agrees | `raw/databento/*/…ohlcv-1m…` | **Partly.** The top-up's ohlcv-1m starts 2026-09-11, so after a D462 rebuild it covers 09-11 → 09-18 (6 sessions). **2026-09-10 is not covered.** AITODO's "no vault-input build is needed" misses 7 sessions |
| 9 D680 | D644 fixture, then G0's bars and use (this prep) | built at the run | ohlcv-1m, as above | as above: 09-10 missing |
| 9 D680 | `fixtures/fut_index_sessions` (D462; D644's front contract) | 2026-09-09 | ohlcv-1m | rebuild with D462: 09-11 → 09-18 yes, 09-10 no |
| 9 D680 | SPY daily (`raw/alphavantage/daily/SPY.json.gz`, G0's usable days) | **2026-08-26** (last date key; mtime 2026-08-27) | Alpha Vantage, not Databento | **No.** Refresh it, or the use list drops 16 vault sessions. The builder takes `--spy PATH`, so the raw cache is not overwritten |
| 9 D680 | `fixtures/cme_session_calendar` | 2026-09-09 (meta span) | CME definition/status | Rebuild optional. It sets only G0's half days (none on 09-10 → 09-18) and D671's event flags, which D680 reads only in-sample |
| 3, 8 NG | Databento ohlcv-1s: CL `GLBX-20260924-UMCCWJ39BQ`, NG `…S5DLBTQTSP`, TAS `…NLQP44SHSR` | headers end **2026-09-19T00:00Z** | free pull (D624) | not needed |
| 3, 8 NG | `fixtures/fund_nav_daily` | 2026-09-18 (meta, all four funds) | D619 | not needed |
| 3, 8 NG | `fixtures/fut_settle_strip` | **2026-09-10** (meta, CL/NG/HO/RB) | statistics, `GLBX-20260911-SDNLQ6M99S`, header end 2026-09-11 | **Yes for the data** (statistics from 09-11). **But the builder cannot see it as written:** `build_fut_settle_strip.py:40` reads ONE job dir. It also has no cut, and CL/NG/HO/RB from 2026-09-19 are D626's sealed sample until 10-10 |
| 3, 8 NG | `fixtures/fund_holdings_quarterly` | last period 2026-06-30 (meta) | SEC filings | n/a |
| 3, 8 NG | `ledger_swap_free_quarters.json` | **2025-Q4** (all six funds) | `prove_swap_free_quarters.py` | **No.** 2026-Q1 and Q2 are needed if the vault's A6 swap quarters run to 2026-Q2 |
| 3, 8 NG | `calendar/events.csv`, `raw/uscf/…-2026.csv`, `fixtures/oecd_ir3tib_monthly.csv` | 2026-12-31 / 2026 / 2026-08 | on disk | n/a |

**The one Databento gap the top-up does not close:** GLBX.MDP3 `ohlcv-1m`, `ALL_SYMBOLS` (stype_in `raw_symbol`,
the archive's form), 2026-09-10T00:00Z → 2026-09-11T00:00Z. That is session 2026-09-10 and the 09-11 session's
evening from 18:00 ET. `mbo` has the same hole (not needed here).
- Why: the archive ends 2026-09-10T00:00Z, and `fetch_prelapse_topup.py` and `quote_prelapse_sweep.py` both assume
  09-11.
- Price: no repo script quotes an arbitrary window, so it is not quoted. The sweep quoted the same schema from 09-11
  at USD 0.00.
- The simplest fix is **ohlcv-1m's START = 2026-09-10 in the top-up before it runs on 10-09.** That is the
  principal's call. Nothing was submitted or downloaded here.

## 2. After the 10-09 top-up, before the run (in order)

1. Decide the 2026-09-10 hole: pull it, or accept it (`--accept-hole 2026-09-10` on D680's fixture build).
2. D462 rebuild (`python scripts/build_fut_index_1m.py --build`).
   - It globs every job dir.
   - It writes `fut_{ES,NQ,YM,RTY}_rth_1m`, `fut_index_sessions` and `fut_index_rolls` in place, so the manifest shas
     move. D716 reads `data/fixtures/` of the checkout it runs in.
3. Refresh SPY daily to ≥ 2026-09-18 into a separate path, for `--spy`.
4. Extend the settlement strip to 2026-09-18.
   - It needs the new statistics job dir. `RAW` is one dir, so this means a wrapper or a change.
   - Read nothing for CL/NG/HO/RB dated ≥ 2026-09-19 before D626's read on 10-10.
   - Then update `data_manifest.json` deliberately (`load_panel` checks the digest).
5. NG choices, the principal's:
   - estimate_fut_share's vault `LAST_ANCHOR` and `SWAP_Q_LAST` (proposed 2026-06-30 and 2026-Q2; there is no
     default);
   - swap-free quarters to 2026-Q2.
6. **NG Stage A has no vault scorer.**
   - D630 §8 requires a freeze first, `data/ledger_frozen_vault_h2_ng.json` (runner, both builders, the record).
   - Neither that file nor a `--vault` mode in `run_h2_ng_stage_a.py` exists. The pass criteria are in the Stage A
     freeze's `vault_pass`.
   - Slot 3 cannot be scored until the principal has one written and frozen. D649 (slot 8) has its own scorer.

## 3. The run, per slot (each refuses without `--principals-word`)

Run §0 first. Every `--vault` checks its own freeze, refuses a second opening, and re-proves its in-sample known
answer before scoring.

**Slot 7, D716 NQ F2** (after §2.2, in the checkout holding the rebuilt fixtures):
`uv run python scripts/vault_d716_nq_f2.py --vault --principals-word "..."`. It re-proves 274 / +$20.670105, B 271,
A 216 / +$25.578712 and the take-session hashes.

**Slot 9, D680 NQ compression** (after §2.1–2.3):
1. `python scripts/joint_d680_vault.py --build-vault fixture --principals-word "..." [--spy P] [--accept-hole 2026-09-10]`
   (SYSTEM python). It refuses a hole in the ohlcv-1m headers that is not accepted, and a session table short of
   09-18.
2. `uv run python scripts/joint_d680_vault.py --build-vault inputs --principals-word "..." [--spy P]`. It refuses if
   SPY ends before 09-18. It writes `data/joint_run/d680/` with bars, use and a manifest of sha256s.
3. `uv run python scripts/joint_d680_vault.py --run-vault --principals-word "..."`.
   - Before the call it checks the freeze and the manifest.
   - Before the call it runs a rehearsal on the vault files' own calendar with synthetic prices. That must show vault
     sessions reaching the frame and C1 trades after the cut.
   - It holds the cut and calls the frozen `main`. The frozen `main` re-proves 387 C1 trades, +6.93 / +7.56 bp,
     then scores.

**Slots 3 and 8, NG** (after §2.4–2.6):
1. `python scripts/build_ledger_vault_inputs.py --prove dbn`, then `uv run … --prove panels`. This is the in-sample
   reference the vault build is compared against.
2. `python scripts/build_ledger_vault_inputs.py --build-vault dbn --principals-word "..."`. It checks that every
   file ends by 2026-09-19T00:00Z and that files do not overlap, and that the rows before 2025-03-01 equal the
   frozen files'.
3. `uv run python scripts/build_ledger_vault_inputs.py --build-vault panels --principals-word "..." --fut-share-anchor … --swap-q-last …`
   - It refuses if the NAV or the strip ends before 09-18.
   - It refuses if an in-sample day on or before 2024-12-31 moved.
   - It writes `data/joint_run/ng/d630_vault_trade_table.csv`.
4. D649: `uv run python scripts/ledger_vault_pp_ng.py --vault data/joint_run/ng/d630_vault_trade_table.csv --principals-word "..."`.
5. Stage A (slot 3): only once §2.6's scorer exists and is frozen.

## 4. Proofs on record (in-sample, 2026-09-30; scratch in `temp/`)

**D680.** ES/NQ sessions before 2024-01-01 only, under D716's seal. D680's own window runs to 2025-02-28, so its
387-trade known answer is left to the frozen `--vault`.
- D644's rebuild matches the committed fixture byte for byte.
  - 18 in-sample files; 49 records past the cut were dropped on `ts_event` alone.
  - 5,823,780 rows, sessions 2015-09-01 → 2023-12-29, text sha256 `7f3c6eb9…3c5e98`.
- G0 plus the writer reproduce that text byte for byte and equal D668's frozen in-sample loader frame exactly.
- The use list matches gate0.json exactly: 2,285 sessions, 2,303 NYSE days, 18 half days.
- The frozen `book()` on the written files reproduces D672's per-year C1 for 2018–2023 exactly: 47 / 64 / 52 / 52 /
  58 / 55 trades, gross and net |diff| 0.0.
- With the cut raised, the in-sample trade table is unchanged.
- Every check fired on its break.

**NG, cut at 2025-03-01.** Every Databento file read ends by 2025-03-01T00:00Z (headers). The catalogue panels were
restricted as text on their date column.
- Six frozen inputs reproduce the Stage A freeze's sha256 exactly:
  - window panel `4def0334…` (10.3 min, SYSTEM python);
  - minute bars `238a80fb…` (4.3 min);
  - fut-share A6 `f8b0028c…`;
  - calendar `7c2ade96…`;
  - flow daily `b91d527f…`;
  - flow contracts `5e34bcab…`.
- The committed summaries also reproduce. The flow panel's does so except for the staged panels' own digests.
- D630's trade table from those inputs gives n 1,028 and mean g $66.0214007782101, both exact.
- D649's known answer: 270 trades, MNG net $15.43.
- The main pull's Jan–Feb 2025 records equal the tail pull's, 7,788,234 records each. Every field was compared except `publisher_id`, which was not compared.
  So the vault build (main year files, no tail) cannot move the prefix.
- The signed window panel (H1, Sierra) is frozen but is not a D630 input, and was not rebuilt.
- Every check fired on its break.
