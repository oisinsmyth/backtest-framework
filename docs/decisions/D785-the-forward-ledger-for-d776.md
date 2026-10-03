# D785 — the forward ledger for D776 (the CPI and jobs-report fade, slot 2), built, proved in-sample and run: its first forward trade, 2026-10-02, lost $95

*2026-10-03. The principal: "Yes build D776's forward ledger".*

- **What it is:** the code that scores D776's frozen construction on the forward recorder's NQ bars, one row per CPI
  and Employment Situation release from 2026-09-21. It is a tool, not a test, and admits nothing.
- **Why this one can run now:** each D776 trade uses only its own morning (the 08:29, 08:34 and 11:00 bar closes). It
  needs no history, unlike L4 (D784), NQ F2 and C1, whose gates rank against hundreds of prior sessions and must
  wait for the joint run's vault-built history.

## The tool

`scripts/forward_d776_ledger.py`, three modes.

- **The trades are D775's functions, imported unchanged,** called as D776's frozen vault scorer calls them:
  `classify(sessions(bars, "NQ"), release_days)`.
- **The input:**
  - the recorder's NQ Globex sessions (`data/raw/forward/fut_NQ_fwd_globex_1m.csv.gz`);
  - read with D776's reader's filters (NQ, D775's bars, same-day stamps);
  - Sierra contract names normalised (`NQZ26-CME` → `NQZ6`).
- **The release days:** D585's calendar (`events.csv`), CPI and EMPSIT at 08:30, from 2026-09-21 to today.
- **The seals:**
  - no session before 2026-09-21 is read in `--ledger` (it raises);
  - `--prove` reads only 2016–2023;
  - D776's vault window (NQ 2024-01-01 → 2026-09-18) is never read.
- **The output:**
  - `data/forward/d776_forward.csv`, one row per release day: the contract, the impulse x, the side, entry and exit,
    gross, and net at \$4.07;
  - a status: trade, pending (no bars yet), missing bar, two contracts, or zero impulse;
  - a recorded row that later changes goes to `d776_forward_revisions.csv`.

## The proofs (in-sample, `data/forward/d776_ledger_proof.json`)

1. **The reader.**
   - Setup: the whole 2016–2023 NQ panel written in the recorder's Globex layout with Sierra contract names, then
     read back.
   - Result: D775's known answer exactly. 186 trades, mean gross +\$34.879032, on the same days with the same
     gross. The six non-trades are D775's own exclusions (4 sessions without bars, 2 zero impulses).
2. **The Sierra source.**
   - Setup: the recorder's own `build_globex` over Sierra's 2023 NQ files (2023-04-04 → 12-29).
   - Result: a ledger identical to Databento's. Status agrees on all 18 release days, 17 of 17 trades match, and
     side and gross agree to the cent.

- **The self-test:**
  - contract names normalise;
  - the reader keeps NQ's same-day D775 bars;
  - a reversal pays the fade in money (+\$12 on a synthetic up-impulse);
  - an unrecorded release is pending;
  - a missing bar is named.

## The first forward run (2026-10-03)

| day | event | x | side | entry → exit | gross / net |
|---|---|---|---|---|---|
| 2026-10-02 | EMPSIT | +128.25 pts | short | 31,118.25 → 31,163.75 | −\$91.00 / −\$95.07 |

- **The jobs-report impulse continued to 11:00 rather than reverting.** One trade is no evidence either way.
- **Forward power (D775 §7):** about 24 trades a year; 0.8 power at the in-sample effect needs about 110 trades,
  about 4.5 years. The ledger is a monitor; the confirmation is D776's vault read in the joint run.
- **Next:**
  - the 2026-10-14 CPI;
  - adding `--ledger` to the daily recorder task, on the principal's word.
