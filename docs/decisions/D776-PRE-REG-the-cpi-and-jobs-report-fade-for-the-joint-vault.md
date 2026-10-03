# D776 PRE-REG — D775's CPI and jobs-report fade on MNQ for the joint vault run: the vault scorer, the freeze and programme slot 2

*2026-10-02. The principal: "Put D775 in the next slot and freeze it".*

- **The order (as D737):**
  - this record is committed before its runner exists;
  - the runner, with its self-test, is committed next;
  - the in-sample rehearsal and the power run are each run once and committed;
  - the freeze is written once, after both, and registers the programme family;
  - the vault is scored only in the joint run, on the principal's word.
- **The slot:** the registry allocates the lowest free slot, which is **2** (slots 2 and 10 are free; α 0.005). After it,
  0.045 of the programme's 0.05 is allocated.
- **Nothing here reads a price dated on or after 2024-01-01.**

## 1. What is scored: D775's construction, unchanged

- **The functions are D775's,** imported from `scripts/stage0_d775_cpi_nfp_fade.py`: `sessions`, `classify`,
  `rotation`, and its bar list and cost lines. Nothing is re-implemented.
- **The trade:**
  - on every CPI and Employment Situation release at 08:30 ET (`data/calendar/events.csv`), one MNQ;
  - impulse x = close(08:34 bar) − close(08:29 bar), on the session's front contract;
  - side = −sign(x), entered at the 08:34 close and exited at the 11:00 close;
  - \$2 a point, \$4.07 a round trip.
- **The known answer** (D775, 2016-01-01 → 2023-12-31): 186 trades, mean gross +\$34.88.
  - The rehearsal records it to full precision. Every later mode must reproduce that count and mean (to 1e-9) before it
    scores anything.

## 2. The vault window and its input

- **Window:** NQ release days **2024-01-01 → 2026-09-18**.
  - That is the NQ window of slot 1 (D737) and slot 7 (D716): NQ prices from 2024-01-01 are unseen until the joint run.
  - The calendar holds 64 release days in it.
- **Input:** the vault opening fixture that the joint run's D680 step builds,
  `data/joint_run/d680/fut_opening_globex_1m.csv.gz` (main checkout).
  - It is D644's builder (`build_fut_opening_1m`) run unchanged through 2026-09-18, in the committed fixture's layout.
  - D680's wrapper proves its rebuild equals the committed fixture byte for byte on 2015-09-01 → 2023-12-29.
  - The committed fixture `fut_opening_globex_1m` stops at 2025-02-28 and cannot serve the vault.
- **So D776's vault step runs after slot 9's `--build-vault fixture` step.**
  - It refuses if that file is missing, or ends before 2026-09-18 (`--accept-end` is the principal's call).
  - It refuses a row after 2026-09-18.
- **Before scoring, the vault step re-derives the known answer on the vault file's own 2016–2023 rows.** This ties the
  vault input to the in-sample one; it is a whole-sample re-proof, stronger than D737's two-month overlap.
- **2024-01-01 → 2025-02-28 sits in the committed fixture.** It is never read: D775's loader filters below
  2024-01-01, and that is asserted.

## 3. The pass rule (fixed here; D775 §7 proposed it)

| gate | condition |
|---|---|
| **G0** | at least 40 trades in the window (else UNRESOLVED) |
| **G1** | mean net > 0 (net = gross − \$4.07) and one-sided t of the mean net ≥ 1.2816 (trades are a month apart: iid t) |
| **G2** | mean gross above the p95 of the exact rotation of the release labels over the window's valid sessions (all offsets, SE 0) |

- **PASS** = G0, G1 and G2. **FAIL** = mean net ≤ 0. **Else UNRESOLVED.** No re-tuning after the look.
- **Promotion beyond a PASS** needs the family's programme-adjusted p ≤ 0.005 (about t ≥ 2.8), and a programme-level
  DSR ≥ 0.95 (the registry's rule). A vault PASS alone admits nothing.
- **Reported beside the gate, not gated:**
  - the 09:30 → 11:01 leg alone (clear of the spent 18:00 → 09:00 NQ slice);
  - the down/up split and the |impulse| terciles;
  - CPI against jobs reports; the years;
  - the volatility-adjusted mean;
  - the four groups.

## 4. Power (computed in-sample before the freeze)

- **The power file** (`data/vault_d776_power.json`) resamples 64 in-sample trades at 100 / 75 / 50 / 25 / 0% of the
  in-sample edge, and gives P(G1).
  - It does the same with the 2016–19 trades and with the 2020–23 trades as the base, because the edge differed
    threefold between the halves (D775).
  - It runs the full gate (G1 and G2) on every in-sample window of 64 consecutive release days, stepping 8 releases
    (about 2.7 independent windows).
- **D775's analytic figures:** about 0.63 at the full effect, 0.81 at the 2020–23 effect, 0.29 at the 2016–19 effect.

## 5. The freeze

- `data/FROZEN_vault_d776_cpi_nfp_fade.json` hashes, LF-normalised (as D737):
  - the runner;
  - this record, D775's pre-registration and result, and D775's JSON;
  - the rehearsal and power files;
  - every repo module the runner imports.
- It records the known answer, the parameters and the slot.
- `--vault` verifies the freeze first and refuses on any drift.
- **The registry and its page:** the family `CPI/jobs-report fade (NQ, D775)`, slot 2, registered 2026-10-02. The page
  is rendered at its pinned date; `tests/unit/test_programme.py` is pinned to the new state.
- **Also:** `docs/internal/JOINT_RUN_CHECKLIST.md` gains the D776 step (after slot 9's fixture build). `docs/COMPONENTS_PROP.md`
  gains a PROVISIONAL entry.

## 6. Runner assertions and the self-test

- **Modes:** `--selftest`, `--rehearse` (in-sample, once), `--power` (in-sample, once), `--freeze` (once), and
  `--vault --principals-word "..."` (the joint run only; refused without a word, without a freeze, or when its output
  exists).
- **The self-test (synthetic only):**
  - the gate's three readings;
  - the window filter refuses a row past the end;
  - `--vault` is refused without a word;
  - a planted reversal passes G1 and G2, and a planted continuation fails;
  - the freeze check fires on a moved parameter and a moved import.
- **No price dated on or after 2024-01-01 is read** in any mode but `--vault`.

## 7. Output

- `scripts/vault_d776_cpi_nfp_fade.py`;
- `data/rehearsal_vault_d776.json`, `data/vault_d776_power.json`, `data/FROZEN_vault_d776_cpi_nfp_fade.json`;
- at the joint run, `data/vault_d776_cpi_nfp_fade.json`. The vault result is a separate record.

## A1 (2026-10-03) — the re-freeze: D775's result record renamed to meet the 85-character path limit

*The principal, on the long path: "re-freeze".*

- **Why:**
  - D775's result record was `docs/decisions/D775-STAGE-0-RESULT-the-cpi-and-jobs-report-fade-passes-in-sample-on-mnq.md`,
    90 characters.
  - The tracked-path limit is 85 (D540; `tests/unit/test_public_cut.py`). The documentation session found it failing.
  - The record is one of the three this freeze hashes, so a rename needs a re-freeze.
- **What moved:**
  - **The record's path, not its content.** It is now
    `docs/decisions/D775-STAGE-0-RESULT-the-cpi-and-jobs-report-fade-passes-in-sample.md`, and its sha256 is unchanged
    (`a59e57d3…`).
  - **This runner:** the new path constant, and a `--refreeze` mode (below).
  - **This record:** this addendum.
  - The link in `docs/COMPONENTS_PROP.md` entry #7 now points to the new path. `docs/internal/JOINT_RUN_CHECKLIST.md`
    notes the re-freeze.
- **What did not move, and the re-freeze refuses otherwise:**
  - D775's pre-registration;
  - D775's runner and every imported file (including `programme.py`);
  - D775's JSON, the rehearsal and the power files;
  - the parameters, the gate and the known answer (186 trades, mean gross +\$34.879…);
  - the programme slot (2), family and α (0.005). The registry is not touched, and `--refreeze` checks it still holds
    slot 2 for this record.
- **The mechanism:**
  - The first freeze (runner sha256 `b4df3be5…`; the manifest file's own sha256 `2035f669…`) is kept unchanged as
    `data/FROZEN_vault_d776_cpi_nfp_fade_v1.json`.
  - `--refreeze` writes `data/FROZEN_vault_d776_cpi_nfp_fade.json` once. It copies the first freeze's slot, family, α,
    instruction and known answer onto the current manifest, and adds a `refrozen` block (date, instruction, reason,
    the rename, the previous file and its hash, what moved).
  - It raises if the renamed record's content moved, if any other record, data file, parameter or imported file
    moved, or if the registry disagrees.
  - **The self-test** shows it accepts the declared moves, and fires on a renamed record whose content moved, an
    undeclared record move and a moved data file.
- **No price was read.** The vault is unopened, and `--vault` verifies the new freeze exactly as before.
