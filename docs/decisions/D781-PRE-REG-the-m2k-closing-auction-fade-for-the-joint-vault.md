# D781 PRE-REG — base L4, the M2K closing-auction fade, for the joint vault run: the vault scorer, the freeze and programme slot 10

*2026-10-03. The principal: "Pre-reg L4's freeze for slot 10".*

- **The order (as D737 and D776):**
  - this record is committed before its runner exists;
  - the runner, with its self-test, is committed next;
  - the in-sample rehearsal and the power run are each run once and committed;
  - the freeze is written once, after both, and registers the programme family;
  - the vault is scored only in the joint run, on the principal's word.
- **The slot:** slot **10**, the last free one (α 0.005). After it, the programme's whole 0.05 is allocated: a later
  line enters only by an amendment that re-allocates α.
- **Nothing here reads a price dated on or after 2024-01-01** before `--vault`.
- **The prop book's rules:** one M2K, entered at the 18:05 reopen and exited at 10:00 the next day; flat long before
  16:10; fully algorithmic. The overnight closure does not apply (the principal, 2026-10-02: signed fades are outside it).

## 0. What this record says against itself

- **Base L4 fails the bar D775 cleared before its freeze.** In-sample (D778's base book, 2018–2023):
  - net t 1.88, below 2;
  - net −\$15 in total without 2020 and 2021.
- **Its one losing year, 2022, is unexplained.** In-sample, neither a trend state (D778) nor a rates state (D779) known
  at 16:00 separates 2022's losing trades from the other years' winners.
- **It was chosen over L3 for this slot on in-sample numbers** ([D780](D780-STAGE-0-RESULT-gold-s-weekend-reopen-is-a-2020-book.md)):
  - net per trade +\$12.08 against +\$9.54;
  - without the best year, +\$6.32 against +\$2.73;
  - net Sharpe 0.81 against 0.48.
- **The vault test is close to a coin flip even if the edge is real.** By normal approximation on about 133 trades:
  - P(G0 and G1) ≈ 51% at the in-sample net;
  - ≈ 27% at the net without the best year;
  - 10% at zero (§4 replaces these with resampled figures).
- **Why freeze it anyway (the principal's call):**
  - the vault is the only confirmation inside years; forward recording alone needs about 320 trades, about six years;
  - its daily ρ with every component in the ledger lies between −0.06 and +0.03;
  - it passes the principal's year test (win ≥ 50% in 5 of 6 years).

## 1. What is scored: D778's base book, unchanged

- **The functions are D778's and D777's,** imported, not re-implemented:
  - `stage0_d778_auction_fade_trend_filter.frame`, which calls `stage0_d777_post_close_fade.panel`;
  - D777's `rotation`, and D775's `trade_stats`.
- **The trade:**
  - c = close(15:59 bar) − close(15:49 bar) on session S, on S's front (the 15:50 → 16:00 closing-auction move);
  - the gate: |c| ≥ the 80th percentile of |c| over the 250 prior sessions (at least 120);
  - side = −sign(c), entered at the close of S+1's 18:04 bar (the 18:05 price), exited at the close of S+1's 09:59
    bar (the 10:00 price);
  - S+1 at most four calendar days after S (D777's panel);
  - \$5 a point, \$3.76 a round trip.
  - D778's validity rule is kept as it stands, including its 200-session trend warm-up. In the vault, history fills
    the warm-up.
- **The known answer** (D778, base book, 2018–2023): **280 trades, mean gross +\$15.84.**
  - The rehearsal records it to full precision.
  - Every later mode must reproduce that count and mean (to 1e-9) before it scores anything.

## 2. The vault window and its input

- **Window:** M2K sessions S from **2024-01-01**, with S+1 on or before **2026-09-18**. That is about 133 trades at the
  in-sample rate.
- **The window is unseen by this line:**
  - Every read in L4's lineage stopped before 2024-01-01: D772's lead hunt, D777, D778, D779 and the main session's
    scratch looks.
  - The forward recorder reads RTY from 2026-09-21 only.
  - **D682 read RTY through 2025-02-28 for a different construction** (the opening compression break, exited by
    15:59, with the overnight range as a feature). It shares no design decision with L4.
  - Under the principal's 2026-09-10 ruling (holdout multiplicity is per line), 2024-01 → 2025-02 is unseen by L4.
  - The alternative, 2025-03-01 → 2026-09-18 only, is about 76 trades: P(G0 and G1) ≈ 38% against 51% at the
    in-sample net. It is recorded here and not chosen.
- **Input:** `fut_opening_globex_1m_ym_rty` rebuilt through 2026-09-18 at the joint run.
  - It uses D644's builder (`scripts/build_fut_opening_1m.py --roots YM,RTY`, D682's extension), unchanged, into
    `data/joint_run/d781/fut_opening_globex_1m_ym_rty.csv.gz` (main checkout).
  - **Identity check:** its rows through 2025-02-28 must equal the committed fixture's, row for row. The vault step
    refuses otherwise.
  - The committed fixture stops at 2025-02-28 and cannot serve the vault. Its 2024-01 → 2025-02 rows are never
    read before `--vault`: every in-sample mode filters below 2024-01-01, and that is asserted.
- **The raw archive:**
  - The `ohlcv-1m` files on disk reach 2026-09-09.
  - 2026-09-10 → 09-18 arrives with the pre-lapse top-up scheduled for 2026-10-09. It is all-symbol, so RTY is
    included; it starts at 09-10 (`JOINT_RUN_CHECKLIST` V5).
  - Its Saturday header gap (V2: 2026-09-12, no bar lost) applies to this build too, accepted on the same word.
  - The vault step refuses a fixture ending before 2026-09-18 (`--accept-end` is the principal's call). It refuses a
    row after 2026-09-18.
- **Before scoring,** the vault step re-derives the known answer on the rebuilt file's own 2016–2023 rows.
- **History:** the gate's 250-session threshold and the 200-session warm-up read the sessions before S, so early-2024
  trades use 2023 history. That is in-sample data and is allowed.

## 3. The pass rule (fixed here)

| gate | condition |
|---|---|
| **G0** | at least 40 trades in the window (else UNRESOLVED) |
| **G1** | mean net > 0 (net = gross − \$3.76) and one-sided t of the mean net ≥ 1.2816. Each trade is one night and no two overlap, so the t is iid |
| **G2** | mean gross above the p95 of the exact rotation of the signal (side × gate) against the outcomes over the window's valid sessions (all offsets, SE 0) |

- **PASS** = G0, G1 and G2. **FAIL** = mean net ≤ 0. **Else UNRESOLVED.** No re-tuning after the look.
- **Promotion beyond a PASS** needs the family's programme-adjusted p ≤ 0.005 (about t ≥ 2.8), and a programme-level
  DSR ≥ 0.95 (the registry's rule). A vault PASS alone admits nothing.
- **Reported beside the gate, not gated:**
  - the fall and rise sides (in-sample, the edge was in buying falls), and the drift-adjusted give-back;
  - the years 2024, 2025 and 2026, and the |c| terciles;
  - the volatility-adjusted mean;
  - the share of |c| given back by 10:00 (2022's failure measure: 2.5% against 52–72% elsewhere);
  - the four groups;
  - the window from 2025-03-01 alone, as a reported split.

## 4. Power (computed in-sample before the freeze)

- **The power file** (`data/vault_d781_power.json`) resamples 133 in-sample trades at 100 / 75 / 50 / 25 / 0% of the
  in-sample edge, and gives P(G0 and G1).
  - It does the same with the 2018–19 trades and with the 2020–23 trades as the base, because the edge differs between
    them (+\$3.14 against +\$15.54 net a trade).
  - It runs the full gate (G1 and G2) on every in-sample window of 133 consecutive base trades, stepping 16 trades.
    That is about two independent windows.
- **The analytic figures above** (51%, 27%, 10%) are the reference.

## 5. The freeze

- `data/FROZEN_vault_d781_l4_auction_fade.json` hashes, LF-normalised (as D776):
  - the runner;
  - this record, D778's pre-registration and result, and D778's JSON;
  - the rehearsal and power files;
  - every repo module the runner imports (D778's, D777's and D775's runners among them, which then cannot be edited).
- It records the known answer, the parameters and the slot.
- `--vault` verifies the freeze first and refuses on any drift.
- **The registry and its page:**
  - the family `closing-auction fade (M2K, base L4)`, slot 10;
  - the page rendered at its pinned date;
  - `tests/unit/test_programme.py` pinned to the new state, with no free slot left.
- **Also:**
  - `docs/internal/JOINT_RUN_CHECKLIST.md` gains the D781 steps: the YM/RTY fixture build, then the vault;
  - `docs/COMPONENTS_PROP.md` gains a PROVISIONAL entry.

## 6. Runner assertions and the self-test

- **Modes:**
  - `--selftest`;
  - `--rehearse` (in-sample, once) and `--power` (in-sample, once);
  - `--freeze` (once);
  - `--vault --principals-word "..."`: the joint run only. It is refused without a word, without a freeze, when its
    output exists, or when the identity check fails.
- **The self-test (synthetic only):**
  - the gate's three readings;
  - the window filter refuses a row past the end;
  - `--vault` is refused without a word;
  - a planted reversal passes G1 and G2, and a planted continuation fails;
  - the identity check refuses a rebuilt fixture whose early rows differ;
  - the freeze check fires on a moved parameter and a moved import.
- **No price dated on or after 2024-01-01 is read** in any mode but `--vault`.

## 7. Output

- `scripts/vault_d781_l4_auction_fade.py`;
- `data/rehearsal_vault_d781.json`, `data/vault_d781_power.json`, `data/FROZEN_vault_d781_l4_auction_fade.json`;
- at the joint run, `data/vault_d781_l4_auction_fade.json`. The vault result is a separate record.

## 8. Prediction

- **P(PASS)** is about 0.5 if the in-sample edge holds. For a lead found by a search, about 0.3 is more honest.
- **UNRESOLVED** (net > 0 but t < 1.28) is the likeliest other reading.
