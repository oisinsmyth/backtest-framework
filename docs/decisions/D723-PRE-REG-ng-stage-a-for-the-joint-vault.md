# D723 PRE-REG — NG Stage A (D630's H2) for the joint vault run: the vault scorer and freeze that D630 §8 requires, programme slot 3

*2026-09-30. The principal: "Do the write up and freeze". This answers the joint-run checklist's §2.6: "NG Stage A has
no vault scorer".*
- **The order:**
  - this record is committed before its runner exists;
  - the runner, with its in-sample known answer and self-test, is committed next;
  - the freeze is written once, after the NG input path is final (it hashes that path);
  - the vault is scored only in the joint run, on the principal's word (A10).
- **The slot:** programme slot 3 (`ledger H2`, registered 2026-09-21: "Price effect: signed return from the t0+1
  fill to the W_end close on traded days"). No new slot is registered. D722 is the other session's.

## 1. What is scored: D630's H2 on NG, unchanged

- **The construction is D630's, frozen in `data/FROZEN_ledger_stage_a_ng.json` (2026-09-26):**
  - the side is sign(Q_rem) at t0 (P1 alone: BOIL +2, KOLD −2, BCOM NG holdings under S0);
  - t0 is the earliest pass among 13:50 / 14:00 / 14:10 of the gate |I| ≥ 3 × the $16 round trip with SNR ≥ 1.5;
  - entry is the close of the one-minute bar t0+1, and exit the close of the 14:29 bar;
  - one full-size NG, costed at $16 a round trip plus one tick of entry slippage ($26).
- **Its in-sample answer (2017-05-22 → 2025-02-28), the known answer the runner must reproduce:**
  - n 1,028, mean g $66.0214007782101, net $40.02;
  - reproduced 2026-09-30 by `scripts/build_ledger_vault_inputs.py --prove` from the rebuilt inputs.
- **The vault's trades:** the rows of the trade table that `build_ledger_vault_inputs.py --build-vault panels` writes
  (`data/joint_run/ng/d630_vault_trade_table.csv`), dated 2025-03-01 → 2026-09-18. D649 (slot 8) reads the same
  table.
  - **The vault anchors are the principal's, accepted 2026-09-30:** estimate_fut_share's vault LAST_ANCHOR is
    2026-06-30, and SWAP_Q_LAST is 2026-Q2, with the swap-free quarters extended to 2026-Q2.

## 2. The pass rule: D630 §8 (deposit line 902), unchanged

**PASS** requires all three:
1. the vault's mean g has the in-sample sign, which is positive;
2. its one-sided t ≥ 1.2816 (p < 0.10), with the same Newey–West convention as D630's registered t;
3. the vault's mean net at 1× cost ($26 a trade) is > 0.

**A failure** is written up as "not promoted", with no re-tuning.

**Floor:** the vault must hold at least 15 traded days. Below that the line is **UNRESOLVED**, and it is written up
as such, not as a pass or a failure.

**Power:** D630 §9 gives a vault pass rate of 0.09 / 0.40 / 0.82 at β = 0 / 0.1 / 0.25. The 0 line is the false-pass
rate, and it is kept as registered.

## 3. Reported beside the pass rule (never gating)

- **The micro line, the one the principal can trade:** at one MNG (a tenth of the size, the MNG round trip from the
  cost table): mean net, net Sharpe and Sortino.
  - Stage A's full-size net is the registered statistic, but the account trades micro.
  - D649 (slot 8) is Stage A's tradeable filter at MNG.
- **All four groups:**
  - net and gross, Sharpe and Sortino;
  - the trade distribution, with symmetric 1% trims;
  - the years, and 2025 against 2026;
  - the 11:30 placebo on the vault days (D630's own), the rotation p50/p95 on the vault days, and the ρ with D649's
    vault book.
- **The seal:** no NG, CL, HO or RB session dated 2026-09-19 or later (D626's sample) enters. The vault ends
  2026-09-18.

## 4. The runner (`scripts/vault_d723_ng_stage_a.py`)

- **`--known-answer`:** from the in-sample trade table (the `--prove` output, or D630's own path), it reproduces
  n 1,028 and mean g $66.0214007782101 exactly.
- **`--selftest`** (synthetic only):
  - the pass rule's three parts each fail when broken;
  - the floor gives UNRESOLVED;
  - a session on 2026-09-19 raises;
  - the vault mode refuses without the principal's word, without the freeze, and on a second opening;
  - a tampered runner, record or builder fails the hash check.
- **`--freeze`,** written once: `data/ledger_frozen_vault_h2_ng.json`, D630 §8's named file. It holds:
  - the sha256 of this runner, of this record, of D630's pre-registration and result;
  - the sha256 of `scripts/build_ledger_vault_inputs.py` and of each frozen builder it imports;
  - the parameters, the retained stage (A), the known answer, and the principal's instruction.
- **`--vault --trade-table PATH --principals-word "..."`:**
  - checks the freeze and D630's Stage A freeze (`verify_ledger_stage_a_ng.py`);
  - re-proves the known answer on the table's in-sample rows;
  - scores the vault rows once;
  - writes `data/vault_d723_ng_stage_a.json` and refuses a second opening.

## A1 (2026-10-01, before the freeze; the principal: "I take both your recomenations")

1. **The t that gates is Newey–West, 5 lags** (D630's own `nw_t`). §2 said "the same Newey–West convention as
   D630's registered t", which contradicted itself: D630's registered t was the ordinary one (5.01 in-sample), and
   NW(5) (4.55) was reported beside it. The principal chose NW(5). It is the stricter of the two and robust to
   trades clustered on consecutive days. The ordinary t is reported beside it.
2. **The vault's anchors may move in-sample rows dated 2025-01-02 → 2025-02-28.** The accepted LAST_ANCHOR
   (2026-06-30) can re-estimate the fund share on those days. The runner still requires the table's rows through
   2024-12-31 to match D630 row for row, and re-proves n 1,028 / $66.0214007782101 on D630's own path. The run
   passes `--accept-a6-tail-moves`, which the principal permitted, and the output records it.
3. **The table is the full** `data/joint_run/ng/d630_trade_table.csv`. The vault-only table holds no in-sample rows
   to re-prove against.
4. **The freeze also hashes** `scripts/build_strip_vault.py` (the vault settlement strip's builder) and every repo
   module it imports, beside `build_ledger_vault_inputs.py`.
