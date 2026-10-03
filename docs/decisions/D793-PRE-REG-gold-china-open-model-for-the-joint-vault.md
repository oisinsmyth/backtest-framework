# D793 PRE-REG: D791's gold China-open model for the joint vault run. The vault scorer, the freeze, and programme slot 11 by amendment

*2026-10-04. The principal: "Add it to the vault", then "Put it in slot 11".*

- **The order (as D737, D776 and D781):**
  - this record is committed before its runner exists;
  - the runner, with its self-test, is committed next;
  - the in-sample rehearsal and the power run are each run once and committed;
  - the freeze is written once, after both, and registers the programme family;
  - the vault is scored only in the joint run, on the principal's word.
- **Nothing here reads a price dated on or after 2024-01-01** before `--vault`.
- **The prop book's rules:** one MGC, entered by 10:00 Beijing (21:00–22:00 ET) and flat by 15:00 Beijing (02:00–03:00 ET),
  long before 16:10 ET; fully algorithmic. It is a signed fade, outside the 2026-09-12 closure (D772).

## 0. The amendment: an eleventh family in slot 11

- **The registry is full:** 10 of 10 slots, α 0.050 of 0.05.
- **The door:** the registry's rule is that "an eleventh requires a doc amendment that re-allocates α — never
  retroactively for families already evaluated". `Registry.register(..., amendment=...)` is its only door. It places
  the family in slot 11 at the standard slot α of 0.005.
- **The amendment, recorded here:**
  - the programme's allocated α becomes **0.055** (10 slots × 0.005 for the existing families, unchanged, plus this
    family's 0.005);
  - the existing ten families keep their slots, α and gates;
  - no family already evaluated is touched (none of the ten has been read).
- **Why this door and not an equal re-split** (0.05 / 11 ≈ 0.00455 a slot): a re-split would edit ten other
  registrations, and their records, for one new line. The principal's instruction was a slot, not a re-split.
- **The cost of the choice, stated plainly:** the programme-wide false-positive budget rises from 5% to 5.5%.
- **D792** (the assembled prop book, frozen 2026-10-04 by the other session) names exactly five members. This line is
  outside it by construction; including it would need a new record.

## 1. What this record says against itself

- **Its evidence is pseudo out-of-sample** (D791 §4.1). The walk-forward protected the model's fit, not its 36
  features. Those were assembled after D786, D787 and D790 had read 2016–2023.
- **It is about two-thirds overfit in training** (D791's addendum): ρ 0.16–0.23 on the training years against 0.059
  out of sample.
- **It is fragile:**
  - a rolling 3-year window has no edge (ρ about 0);
  - the registered α = 100 is the best of 10 / 100 / 1000;
  - 2018, 2019 and 2022 were flat or negative; 2020, 2021 and 2023 carried it.
- **Every vault session follows the SHFE day-session call auction** (2023-05-26). Nearly all its training sessions
  preceded it.
- **The honest prior on its forward edge** is \$0 to about +\$3 a trade passive, below the out-of-sample +\$4.80.
- **Promotion is unlikely:** it needs a programme-adjusted p ≤ 0.005 (about t ≥ 2.8). At the out-of-sample edge on
  about 190 trades, the expected t is about 1.3.
- **Why freeze it anyway (the principal's call):**
  - the vault is the only data no study of this fade has read;
  - it is the only confirmation inside years (forward recording needs about two to three years for 190 trades);
  - its daily ρ with D775 and D777's MNQ book was 0.01–0.05 in-sample (D786/D787 component lines).

## 2. What is scored: D791's 36-feature no-calendar ridge, frozen

- **The features:** D791's 40 pre-entry features less the calendar four (month sine and cosine, weekday, the US clock).
  The 36 are built by the same functions as D791's `--build`:
  - D786's `build()`, `premium_table()`, `dev_for_sessions()`, `western_returns()` and `rstar_all()`;
  - D790's `session_features()` and `trend_features()`;
  - D791's construction of the remainder.
  - Every input is stamped at or before 09:30 Beijing, except the passive book's own fill.
- **The model, fitted ONCE at the freeze on every 2016–2023 candidate session (1,697), and frozen:**
  - **the scaling:** each feature maps to its empirical CDF among the 1,697 training values, minus 0.5, with a missing
    value mapped to 0. The 36 sorted training vectors are stored in the freeze;
  - **the target:** the percentile rank of the taker gross, minus 0.5;
  - **scikit-learn `Ridge(alpha=100.0)` with an intercept.** The coefficients and intercept are stored in the freeze.
  - The descriptive fit of 2026-10-04 gave an intercept of −0.0041 and a threshold of 0.0117. The freeze's values must
    reproduce them to 1e-9;
  - **the rule:** take the session if its score exceeds the 2/3 quantile of the 1,697 in-sample scores (the threshold,
    frozen).
- **Never refitted:** the vault applies the frozen model. There is no rolling refit and no new threshold.
- **The books:**
  - **passive, PRIMARY** (the principal's standing ruling): D770's rule. Rest at the 09:30 touch on the fade's side,
    filled on a trade-through within 30 minutes, exit at the 15:00 touch, one MGC.
    - Cost: \$3.033, which is \$3.00 plus D770's MGC exit adjustment, frozen at its in-sample value.
  - **taker, reported beside it as the fill-failure bound:** entry at the 09:31 bar's open, exit at P(15:00), \$5.93.
- **The candidate sessions:** D765's MGC rules (eligible, x ≠ 0; China holidays, the GC roll week, missing and void
  prints excluded).
- **The known answers** (in-sample, recorded to full precision by the rehearsal):
  - D786's build reproduces D767 (1,697; +\$3.14) and D770 (1,466 filled; +\$2.12);
  - the full-sample fit's predictions, the take flag and its passive and taker books;
  - D791's walk-forward ridge without the calendar: out-of-sample ρ +0.0590 and a passive top third of 479 trades at
    +\$4.80. The runner must re-derive these before anything else.

## 3. The vault window and its inputs (built at the joint run)

- **The window:** trade dates **2024-01-02 → 2026-09-18.** History before the window (the trailing medians, the moving
  averages, the 250-session high) reads 2023, which is in-sample and allowed.
- **The window is unseen by this line.** Every study in its lineage stopped at 2023-12-29: D765, D767, D770, the
  debate, its oracle, and D786–D791. No forward recorder reads gold at the China open.
- **The inputs.** Each is built into `data/joint_run/d793/` (main checkout) by a joint-run step, never before:

  | input | source | how the step is checked |
  |---|---|---|
  | GC, SI, HG, 6A one-minute bars, 2015-12 → 2026-09-18 | the raw `ohlcv-1m` archive (to 2026-09-09) and the pre-lapse top-up (2026-09-10 → 09-18, `JOINT_RUN_CHECKLIST` V5), through D765's own extractor with its window moved | its rows to 2023-12-29 must equal D765's cache, row for row |
  | the China exchange holiday calendar, 2024–2026 | the same `exchange_calendars` XSHG source as D765's calendar (a published schedule) | its 2016–2023 rows must equal the committed calendar |
  | the CNY central parity, 2024 → 2026-09-18 | SAFE's yearly pages, through `scripts/fetch_cny_fix.py` / `build_cny_fix.py` with the end moved | its 2023 rows must equal the committed fixture |
  | the SGE SHAU benchmark, 2024-01-01 → 2026-09-18 | the SGE endpoint, cut at decode | its 2016–2023 rows must equal `data/fixtures/sge_shau_benchmark_2016_2023.csv` |
  | GC `tbbo` + `bbo-1m`, China window, 2024-01-02 → 2026-09-18 | 2025-09-11 → 2026-09-11 from the subscription download already on disk; **2024-01-02 → 2025-09-10 and 2026-09-12 → 09-18 bought** (priced 2026-10-04 at about **USD 23** by `metadata.get_cost` on 60 sampled windows; GC only) | per-file record windows, as the paid fetcher checks |

- **The purchase needs the principal's explicit word at the joint run.** Without it, the passive book and R* are
  scored on the subscription year only, as a reported book that cannot PASS. The taker book and the model's other 35
  inputs need no purchase; a missing R* is scaled to 0, as in training.
- **The vault step refuses** an input that fails its identity check, and any row after 2026-09-18.

## 4. The pass rule (fixed here; passive book)

| gate | condition |
|---|---|
| **G0** | at least 60 passive trades taken in the window (about 190 expected), else UNRESOLVED |
| **G1** | mean net > 0, with one-sided t of the mean net ≥ 1.2816. One trade a session and none overlapping, so the t is iid |
| **G2** | the taken book's mean gross above the p95 of the exact rotation of the take flag over the window's passive-valid sessions (every offset, SE 0) |

- **PASS** = G0, G1 and G2. **FAIL** = mean net ≤ 0. **Otherwise UNRESOLVED.** Nothing is re-tuned after the look.
- **Promotion beyond a PASS** needs the family's programme-adjusted p ≤ 0.005 (about t ≥ 2.8) and a programme-level
  DSR ≥ 0.95 (the registry's rule). A vault PASS admits nothing by itself.
- **Reported beside the gate, not gated:**
  - the taker book, with the same gates;
  - ρ(score, gross) over every valid session, with its exact rotation;
  - the years 2024, 2025 and 2026;
  - the long and short fades;
  - the score's terciles;
  - the four groups;
  - the component line: daily ρ with D775, D777's MNQ book and the unfiltered fade;
  - the window from 2025-03-01 alone (the programme's sealed-vault convention), as a split.

## 5. Power (computed in-sample before the freeze)

- `data/vault_d793_power.json` resamples about 190 trades, the in-sample take rate times the window's sessions, from
  D791's out-of-sample passive book (2018–2023, 479 trades). It does so at 100 / 75 / 50 / 25 / 0% of its edge, and
  gives P(G0 and G1).
  - It repeats this with 2020–2023 and with 2018–2019 as the base, because the edge differs between them.
- **The analytic reference** (normal; sd about \$52; n about 190): P(G1) is about 49% at the full edge (+\$4.80), about
  25% at half, and 10% at zero.

## 6. The freeze

- `data/FROZEN_vault_d793_gold_china_open_model.json` stores:
  - the 36 feature names;
  - the 36 sorted training vectors;
  - the coefficients, the intercept and the threshold;
  - the passive cost;
  - the known answers.
- It hashes, LF-normalised:
  - the runner;
  - this record, D791's scope note and result, and their JSONs;
  - the rehearsal and power files;
  - every repo module the runner imports (D765, D767, D769, D770, D786, D790 and D791's scripts), which then cannot be
    edited.
- `--vault` verifies the freeze first and refuses on any drift.
- **The registry and its page:**
  - the family `gold China-open model (MGC, D791 ridge)`, slot 11, α 0.005, amendment
    `D793 §0: an eleventh family by amendment (the principal: "Put it in slot 11")`;
  - the page rendered at its pinned date;
  - `tests/unit/test_programme.py` and `deposit_test_map.json` pinned to the eleven-family state.
- **Also:**
  - `docs/internal/JOINT_RUN_CHECKLIST.md` gains the D793 steps (the inputs of §3, then the vault);
  - `docs/COMPONENTS_PROP.md` gains a PROVISIONAL entry with the in-sample component line.

## 7. Runner assertions and the self-test

- **The modes:**
  - `--selftest`;
  - `--rehearse` (in-sample, once) and `--power` (in-sample, once);
  - `--freeze` (once);
  - `--vault --principals-word "..."`: the joint run only. It is refused without a word, without a freeze, when its
    output exists, or when an identity check fails.
- **The self-test (synthetic, plus small in-sample samples):**
  - the scaler maps the training values to their CDF and a missing value to 0;
  - a planted relation passes G1 and G2, and a shuffled one does not;
  - the gate's three readings;
  - `--vault` is refused without a word;
  - the window filter refuses a row past the end;
  - the freeze check fires on a moved coefficient and on a moved import;
  - the feature builder, given in-sample dates, reproduces D791's cache row for row.
- **No price dated on or after 2024-01-01 is read** in any mode but `--vault`.

## 8. Output

- `scripts/vault_d793_gold_china_open_model.py`;
- `data/vault_d793_rehearsal.json`, `data/vault_d793_power.json`, `data/FROZEN_vault_d793_gold_china_open_model.json`;
- at the joint run, `data/vault_d793_result.json` and a separate result record.
