# D784 — the forward ledger for base L4 (D781's frozen line), built now and proved in-sample, to run after the joint run

*2026-10-03. The principal: "Yes start with L4's forward ledger".*

- **What it is:** the code that turns the forward recorder's RTY bars into base L4's forward trades, so that after the
  joint run D781's line can be followed forward without new code. It is a tool, not a test. It admits nothing and
  reads no vault price.
- **Why now:** the recorder has kept RTY's bars from 2026-09-21 since 2026-10-03 (`record_forward_nq_lines.py`), but
  nothing scored them. A bug found after the joint run would land on live forward data.

## The tool

`scripts/forward_l4_ledger.py`, three modes.

- **The construction is D778's `frame`, imported unchanged** (the same function D781's frozen runner scores).
- **This file adds only the input path:**
  - **History:** the joint run's rebuilt YM/RTY fixture (`data/joint_run/d781/fut_opening_globex_1m_ym_rty.csv.gz`,
    through 2026-09-18). L4's q80 gate needs 250 prior sessions (at least 120), and its warm-up needs 200. Forward
    history alone could score sessions only from about mid-2027.
  - **Forward:** the recorder's RTY Globex sessions (`data/raw/forward/fut_RTY_fwd_globex_1m.csv.gz`).
  - Both are read with D778's loader's filters (root, D778's bars, a 0–4 day stamp lag). **Sierra contract names are
    normalised** (`RTYZ26-CME` → `RTYZ6`), because D778's trend state zeroes a return across a change of contract name.
  - **The splice** refuses an overlap, and a hole of more than four days between the last history session and the
    first forward one.
- **The seals:**
  - `--ledger` refuses, reading nothing, until D781's vault output (`data/vault_d781_l4_auction_fade.json`) exists,
    that is, until the joint run has scored the vault window. Checked today: it prints OWED and exits.
  - A forward session before 2026-09-21 raises.
  - `--prove` reads only 2016–2023.
- **The output:**
  - `data/forward/l4_forward.csv`: one row per forward session S. The columns are the contract, c, the threshold,
    gated, the side, entry, exit, gross and net at \$3.76, and a status (trade / no trade / pending / invalid).
  - **A recorded row that later changes is never overwritten silently;** the old values go to
    `l4_forward_revisions.csv`, as the recorder does for D737.
- **Scored sessions:** every forward session S from the first one the recorder has whole. The recorder skips
  2026-09-21 whole: its Globex session opens on 09-20, before the seal. The trade on the vault's last session,
  2026-09-18, whose exit falls after it, belongs to neither the vault nor the ledger.

## The proofs (in-sample, `data/forward/l4_ledger_proof.json`)

1. **The splice and the read path.**
   - Setup: Databento's RTY bars split after 2022-12-30. The 2023 part was written in the recorder's Globex layout
     with Sierra contract names, then read back through the ledger's reader.
   - Result: the ledger's 2023 trades equal D778's base book exactly (28 trades, net +\$315.22). The whole ledger
     equals the unspliced one.
2. **The Sierra source.**
   - Setup: the recorder's own `build_globex` over Sierra's 2023 RTY files (2023-04-04 → 12-29, its validation
     window), spliced onto Databento history.
   - Result: the same ledger as Databento's over 192 sessions. Status agrees on all 192, 18 of 18 trades are
     identical, and the sides and gross agree to the cent.
   - That rests on today's tick rounding: RTY's 0.1 tick is rounded from Sierra's float32 prices.

- **The self-test:**
  - contract names normalise;
  - the splice joins, and raises on an overlap and on a hole;
  - the reader keeps only RTY rows of D778's bars within the stamp lag.

## After the joint run

- Run `python scripts/forward_l4_ledger.py --ledger` once D781's vault step has written its output.
- Then add it to the daily recorder task, after `--record`.
- **Forward power:** about 47 trades a year, so the ledger is a monitor, not a confirmation, for years (D781 §0).
