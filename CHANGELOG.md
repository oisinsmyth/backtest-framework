# Changelog

All notable changes to the framework's code are logged here, in
[Keep a Changelog](https://keepachangelog.com/) style. This tracks *what shipped and when* —
the *why* behind each change belongs in [`docs/decisions/`](docs/decisions/README.md), not here.

No tagged releases yet. Entries accumulate under **Unreleased** until the first tagged
version (likely at the Phase C "first real number" milestone, see
[`DEVELOPMENT_TIMETABLE.md`](DEVELOPMENT_TIMETABLE.md)).

## [Unreleased]

### Added (2026-09-20)
- `data/fixtures/fut_btc_1m.csv.gz` + meta (D580): BTC and MBT one-minute bars, every session,
  UTC-keyed, front by trade-date volume, 2017-12-18 to 2026-09-10; builder
  `scripts/build_fut_btc_1m.py` (verify / build / gates / selftest). Stage 0 runner
  `scripts/stage0_d580_funding_clock.py` (the funding clock on CME bitcoin: NOT SUPPORTED).
- `data/fixtures/perp_funding.csv`, `perp_open_interest_daily.csv`, `perp_funding.meta.json` (D579):
  perpetual-swap funding rates from Binance, Bybit and OKX for BTC and ETH, USDT- and
  coin-margined, **46,892 settlements 2018-11-15 to 2026-09-20**, and Bybit daily open interest
  from 2020-08-04 (8,876 rows). New fetcher `scripts/fetch_perp_funding.py` (stdlib; probe /
  fetch / build / selftest; six gates proven to raise). Binance's +1 ms wire offsets are floored
  to the minute; the share at the +0.01 % default is recorded per series.
- `data/fixtures/cftc_cot_raw.csv.gz` extended (D572): **34 symbols, 274,473 rows, 1986-01-15
  to 2026-09-15** - ZL ZM HO RB PL PA added so every one of the breadth fixture's 17 commodity
  roots has its positioning series. Two more resolution traps pinned in `fetch_cftc_cot.py`:
  `%HEATING OIL%` matches only two spread contracts (the outright is `NY HARBOR ULSD`) and
  `%RBOB%` matches ten (the outright is `GASOLINE RBOB`). The 28 original series are not
  re-fetched and end at 2026-08-25; the six new ones end at 2026-09-15.

### Notes (this catch-up, 2026-09-17)
- **The last substantive entry below is dated 2026-09-02 and stops at D284.** Everything above it
  covers **D285 to D539** - 241 decision numbers over 1,077 commits in sixteen days - written from
  `docs/FINDINGS.md` (sections 10-75), `docs/internal/PICKUP.md`, `docs/STACK.md`,
  `docs/RULES.md` and `git log`. It is a catch-up, not a reconstruction: where a source carries a
  measured figure it is carried here, and where none does the claim is written without one.
- **The dated entries below this line are not edited.** Thirty-three of them name a bare
  `*_RESULTS.md` at the repository root and two name `AITODO.md`. Those files moved during the
  2026-09-15/17 repack - results documents to `docs/results/`, working state to `docs/internal/`.
  A path inside a dated block is what was true on that date, and correcting it would be editing a
  record to look tidier. `docs/results/README.md` and `docs/decisions/README.md` are the current
  indexes.
- **Numbering in this range is not clean and the entries say so.** Fourteen numbers have no record
  file on disk - D287, D294, D302, D304, D309, D316, D390, D407, D410, D496 and D516-D519 - and
  several are load-bearing anyway: **D410 is cited by 33 other decision records**, D302 by 22,
  D304 by 14 and D496 by 9, while D517 and D518 are cited nowhere in the tree at all.
  `tests/unit/test_cited_decisions_exist.py` carries ten of them as an allow-list with a reason
  apiece, split two ways: **six have their runner, their artifact and a commit and the record was
  simply never written** (D294, D302, D304, D309, D316, D496), and **three were reserved blocks
  never consumed** - D390 for the block master took twice and renumbered to D397, D400 and D402,
  D407 and D410 for an absorption study a later record states was never run.
- **Nine numbers name two unrelated studies each**, because three interactive sessions were taking
  numbers against `docs/decisions/` at commit time: D440, D472, D473, D495, D497, D498, D504, D506
  and D508. D497 and D498 are half-resolved - the hurdle-P pair was renumbered to D500 and D501 and
  both copies are in the tracked tree until the deletions are committed. **D508 is not resolved and
  is not going to be**: D507's amendment records that a decision number is an identity and
  reassigning one is the principal's call, not a link repair.

### Added (D539 - the public repository as a generated cut, round eight of the repack, 2026-09-17)
- `scripts/build_public_cut.py` - the public repository as a **generated artifact with fresh
  history**, built by reading `HEAD` rather than the worktree. The first implementation copied the
  worktree and refused on deleted-but-uncommitted files, which is this repository's ordinary state:
  **a publishing tool that refuses whenever the author has uncommitted work is a tool that never
  runs.** Reading `HEAD` removes the failure rather than guarding it, and fixes a second defect
  nobody had named - copying the worktree would publish whatever was half-edited at build time.
- The principal's decision, recorded in D539: **nothing is redacted.** The books, the prop
  research, `working/` and `docs/internal/` all go. The MIT grant is scoped instead.
- `NOTICE` - **the MIT grant covered 594,702 characters of other people's writing across 4,061
  passages in 148 files**, three to eight times the brief's estimate because the brief counted
  blockquotes and this repository quotes inline. The link gate was taught to see the file that
  says so. A FINRA FAQ sitting twenty lines below a CFR quote is **not** public domain, which the
  original framing would have got wrong.
- **The size case, in one number: blobs under `data/` are 98.46% of the 940 MiB pack**; everything
  else across 1,392 commits is 14.5 MB. Measured on the real cut: **42 MB against 965 MB, 23x**.
- **Zero credentials anywhere in history** - a full-content scan of 4,847 distinct blobs across
  every commit. No `.env`, no key, no vendor token. Confidentiality was never an argument for a
  fresh start; only size was.
- `docs/VERIFICATION.md` - what the suite guarantees, and the longer section on what it does not.
- Verified **inside the cut** rather than on this worktree: 3,025 of 3,025 blobs identical,
  **2,004 passed and 50 skipped**, 1,031 documents at 0 unresolved links, the manifest's 118 entries
  with 116 absent by design and 0 changed, and 42 MB of `.git`.

### Fixed
- **Fourteen files ran only on the author's machine**, and a hook printed the author's home
  directory into a stranger's session. Found by the publishing lane, not by any gate.
- **The cut caught a stale README counts block on its first run.** The inventory had been
  regenerated before two files were staged; nothing local caught it, because the suite had already
  run and the gate reads the index, which agreed with itself at the moment it was asked. Running
  the gates where the reader will is the whole argument for the mechanism and it paid on day one.
- **A tautological test, written the day before, in the file about a mechanism, in a session whose
  refrain was that a test which cannot fail is worse than none.**

### Added (D538 - round seven, the 136 skips, 2026-09-16)
- **1,909 passed / 136 skipped became 1,998 passed / 49 skipped, measured on a clone**, not
  inferred from this worktree.
- **The panel guard was on the tests instead of on the reader.** `test_us_shorts_fixture.py` put
  `skipif(not FIXTURE.exists())` on twenty tests and **fourteen of them never opened the panel** -
  they read tracked sidecars. The sidecar agreement, the dead-cohort floor, the delisting spread
  and the six hand-verified moves had never run anywhere but one machine. Measured by hiding the
  panel: 34 passed, 6 skipped, **0 failed**, and not one assertion changed.
- **D536's rule was by suffix while every number in its argument was a size.** The proxy misfired
  on its two smallest members - 0.2 MB and 6.7 MB, carrying 47 and 26 skips - and 67 tracked
  `.json` artifacts under `data/` are larger than the smaller of them. Because D536 deliberately
  did not rewrite history, both blobs were already in the object database, so re-tracking them
  cost **6.9 MB in the index and zero new bytes in `.git`**.
- `tests/unit/test_cited_decisions_exist.py` - **eleven decision numbers are cited and have no
  record, across 308 sites.** Six have their runner, their data file and a commit on disk and the
  record was simply never written; three are a reserved block taken twice; one is a "proposed D150"
  never adopted; and one was invented by this repack to cite a move that has no record at all.
  A second test asserts the allow-list cannot outlive its reasons.
- **The three large panels stay untracked** by D538's decision; about 24 of the 49 remaining skips
  are theirs.

### Added (round six - the first figures in 1,700 commits, 2026-09-16)
- `scripts/figures/svgkit.py` and six figures, built over a shared primitives module: the DSR
  hurdle, the look-ahead guard firing, one statistic under two nulls, cross-engine agreement drawn
  from its residuals, the cost waterfall and the ledger diff. `tests/unit/test_figures.py`,
  a `<picture>` wiring for light and dark, an index guard and a CI line. **The README has a figure
  above the fold for the first time in 1,700 commits.**
- The link checker learned to read `src=` and `srcset=`.

### Fixed
- **The flagship golden test asserted the SUM of commission and spread and nothing else.** Borrow,
  margin interest and the dividend were asserted nowhere: **678.82 of the 817.35 this scenario pays
  in frictions was checked in no test**, and a defect moving $6.00 between the two reported costs
  passed. Found only because a waterfall cannot be drawn from a number that does not exist. Fixed
  with a closed-book calculator that an AST gate forbids from importing the package.
- **`docs/verification/cross_engine_reconciliation.md` joined two different maxima with a
  parenthesis** - the absolute maximum is at bar 2,400 and the relative maximum at bar 2,494. Both
  figures were individually correct; the sentence presenting them as one measurement was not.
- **Five links only the author could follow** - gitignored panels and a `temp/` script, green here
  for years and dead for every other reader. The gate resolved against the disk; it resolves
  against the git index now.
- **The control in the D279 figure is eight cells, not the seven the brief said.** The lane
  computed it rather than trusting the brief, which is the only reason the figure is right.
- A `frozenset` iterated while emitting made the first build non-deterministic across processes, so
  `--check` declared its own fresh output stale. Caught in ten minutes by the `PYTHONHASHSEED`
  subprocess gate written for exactly that.

### Fixed (round five - the audit's own fixes, 2026-09-16)
- **The suite did not pass on a clone, and four rounds of claiming it did were never checked by
  cloning.** Three `Path.write_text` round-trips compared bytes against a page checked out as LF by
  `.gitattributes` while Python wrote `os.linesep`. Green in this worktree, which predates that file
  and still holds CRLF; **red on every clone.**
- **`docs/decisions/README.md` called itself an incomplete register for 251 numbers after it had
  stopped being one**, and the banner had propagated into four other documents - `CONTRIBUTING.md`,
  R5 in `docs/RULES.md`, `TUTORIAL.md` and the register's own preamble.
- **`docs/results/README.md` did not index 19% of its own directory** - 12 of 62 documents listed
  nowhere - because the completeness guard written for the decision index was never generalised.
  The link checker cannot catch this: it verifies that links resolve, not that documents are linked.
- **Eleven corrections in `docs/ARCHITECTURE.md`, a document one commit old**, two substantive:
  `RiskMonitor.evaluate` does not append violations to a list, it returns `RiskViolation | None` and
  yields at most one per bar; and the section-1 table presented two mutually exclusive fill modes
  as one sequence. A third is kept as a lesson rather than a fix - **"ordering within a slot
  provably cannot matter" is too strong**, since IEEE-754 addition is commutative but not
  associative and the test covers two bricks per slot, not three.
- **Fifteen errors that predate the repack**, including three more specification documents that
  tell a writer to put a results document where a test now forbids it, and `PHILOSOPHY.md` telling
  a reader to number the next decision `D50` when it is D538.
- **The counts in `README.md` were measured against a dirty worktree instead of `HEAD`.** 741
  decision records is 743 and 586 scripts is 588, each in three places, because six uncommitted
  deletions were sitting in the tree. **A document about the clone must be measured on the clone.**
  `scripts/build_readme_counts.py` generates the block from `git ls-files` now, and the
  hand-correction that replaced one of the typed numbers was itself wrong (274 to 275; the index
  says 276), which is the third time in one round that the answer to a wrong number was to stop
  typing it.

### Changed (rounds three and four - the root, the indexes and the register, 2026-09-16)
- **The repository root is empty of results documents.** 39 `*_RESULTS.md` moved to
  `docs/results/` in two passes - 25 unpinned, then the 14 test-pinned ones. **A `git mv` is the
  small half of a document move**: every one of these files is *written* by a script that hardcodes
  the root, so the two moves were 34 and 17 writer-path edits, and `run_etf_intraday_gate.py` would
  have silently scaffolded a fresh history-less copy at the root rather than erroring. The guard
  test had to be widened once when the gitignored `ETF_INTRADAY_RESULTS.smoke.md` slipped past the
  first glob - **the model of which writers were dangerous was backwards.**
- **No tracked path contains a space any more**: `New Docs/` became `docs/specs/` and
  `docs/prop firm leads/` became `docs/research/prop-firm-leads/`, which retired the link checker's
  `%20` special case along with its only real customer.
- `scripts/check_doc_links.py` became a CI gate, and **the 14 failures it had been carrying were
  four different problems**: nine mechanical repairs, **two a defect in the checker itself**
  (tracked-but-deleted files reported as failures, which blocks the gate for anyone mid-work), two
  pointing at a record that was never written, and one pointing outside the repository at a house
  rule with no file. **A count is not a diagnosis.** The order mattered - making the checker a gate
  before the move meant the move's 19 broken links were enumerated by a tool rather than discovered
  by a reader.
- `docs/decisions/README.md` became a complete register: **251 numbers backfilled, 500 of 500
  listed**, with `tests/unit/test_decision_index_is_complete.py` to keep it that way. The register
  and the curated D1-D284 table are two tables doing different jobs and the preamble says so, because
  **276 of the registered numbers carry no Status or Category at all** and synthesising those
  columns would have looked like data.
- `docs/results/README.md` - 48 studies indexed, five featured for what each proves about the
  instrument.
- `README.md` stopped reciting the studies: **97 lines of study prose that stopped at D218** replaced
  by a pointer at the index, plus a repo map. 71 lines out, 10 in.

### Added (D537 - round two, 2026-09-15/16)
- `.gitattributes`, pinning line endings before the CI that had never run got to disagree with the
  laptop about them. **It paid for itself inside the hour**: the link-rewriting scripts in the next
  step wrote CRLF into the worktree, and without this landing first, `PICKUP.md` and twelve other
  documents would be CRLF in the index - the exact divergence the first CI run would have tripped on.
- **D537: `derandomize=True` does not mean the same examples twice**, and six files said it did.
  The claim was withdrawn from all six and D78 amended in place.
- A ruff and mypy gate with **the ruleset named rather than inherited**: the measured baseline of 26
  findings came from `--select E4,E7,E9,F` spelled out, while the default ruleset on the pinned ruff
  is **553**. A ruleset unpinned by omission is a gate that widens on upgrade with no diff to show
  for it - the same failure D537 records for hypothesis, from a different direction, the same
  afternoon.
- `CONTRIBUTING.md` - the gate-first workflow written down as a procedure for the first time, plus
  three next-number pointers that were wrong by up to 257.
- 477 KB of working state left the front door for `docs/internal/` - **87 link edits, not a
  `git mv`**.

### Fixed
- **The commit that added the lint gate did not pass it.** `ruff --fix` had touched four `src/`
  files that were never staged, and `ruff check` passed afterwards only because it reads the
  worktree. **A gate verified against the working tree is not verified against what was committed.**
  Fixed forward rather than rebased, because a commit that adds a gate and fails it is a more useful
  thing to leave in history than a tidy commit and no trace.

### Added (D536 - round one, the data repack, 2026-09-15)
- **D536: the bulk panels leave the git index and the committed artifact is a manifest carrying
  sha256 AND the git blob id.** 962.6 MB of tracked data becomes 118.5, and the index goes from
  ~990 MB to **147.5 MB**. `filter-repo` was rejected in the same record, because it would convert
  a recoverable repack into a deletion - and the successor was named in the same breath, which is
  the public cut D539 built two days later. Verified before it was relied on: **113 of 113 blob
  pointers resolve, byte counts exact, 837.5 MiB recoverable.**
- `LICENSE` - MIT, stated rather than assumed. An unlicensed repository is all-rights-reserved by
  default, which reads as an oversight rather than a choice.
- CI, and the guards it could not have run without: a clone with no data panels now **skips** what
  it cannot load instead of erroring, measured by hiding the panels rather than asserted.
  `tests/unit/test_panel_guard.py` pins both directions, and `loading_a_panel` skips only for
  filenames the manifest lists, so a typo'd path still fails loudly.
- `README.md` stopped describing a project that ended at D218; every number in the new opening was
  measured that day.

### Fixed
- **The one failing property test was a real one-ULP gap, not a flake** - the invariant was stronger
  than the thing it tested. The weakened assertion was re-checked against a deliberate break.
- **The estimate of "~64 errors on a clone" was wrong, and the way it was wrong is the lesson.** It
  came from searching test files for fixture *names*, which is structurally blind to the eight tests
  that exec a `scripts/run_*.py` module and call its helpers - the panel is opened several frames
  down, through a constant the test never names. The real number was **78**, found in three minutes
  by hiding the panels and running the suite. **Measure, do not survey.**

### Notes (what the eight repack rounds got wrong, audited 2026-09-16)
- The audit re-measured every count and re-ran every quoted command against the tree. **The
  verification held** - 1,838 passed, ruff and mypy clean, 1,026 documents at zero unresolved links,
  manifest 118/0/0, every guard still firing when planted against. **What was wrong was the prose:
  roughly 38 factual errors in documents the first twenty steps wrote or touched**, plus about 15
  pre-existing ones surfaced on the way.
- The three systemic causes are worth more than the individual fixes: measuring against a dirty
  worktree instead of `HEAD`; building a completeness guard for one index and not its twin; and
  writing a banner, invalidating it one commit later, and leaving it standing so one stale sentence
  propagated into five documents. **Each is closed by a mechanism rather than an edit.**
- Left open deliberately: `docs/BOOK.md`'s bare `AITODO.md` reference stays stale, because the book
  is append-only and a quiet path edit is exactly the kind of change that rule refuses.

### Result (D523-D535 - the intraday mean-reversion and breakout families on futures, 2026-09-14/15)
- **D528 and its sixteen addenda - intraday reversion is real and four to eight times below cost.**
  The pre-registered primary is **UNRESOLVED at +0.0215 on a clustered SE of 0.0147** because the
  declared cell held 294 excursions; the x ladder pooled over the grid is **monotone rising,
  +0.0217 to +0.0603**, and the same quantity at x = 2.0 reads **+0.0339 at t +14.72 on 9,766
  excursions**. The return excess rises with excursion rarity, is **flat across six scales spanning
  13x in clock time**, and decays in **bars, not minutes**. In money it is **+0.04 sigma at t+3.9
  and about a third of a tick**, and both stop-fill conventions are biased by more than the effect.
  The 0.93 base rate is construction; only the excess counts. Fixture
  `data/fixtures/fut_day1m_mid.parquet`, quoted mid, 35 roots, 1,930,622 rows, the 2026-04-11
  onward slice reserved and unread.
- **D529 corrects a reframe made the same day, and the correction is the finding.** The framing was
  *hunt shape, not accuracy*, from the admitted arm's 50.5% hit rate and 1.13 payoff ratio. Run a
  detached signal through the arm's **own exit** and the payoff ratio is **1.041 at the median and
  1.138 at p95** - the arm's **1.128 is inside that**. Its hit rate is outside it entirely, **0 of
  400 draws reach it**. Accuracy alone flips the null's expectation from **-0.031 to +0.031**;
  asymmetry alone reaches only +0.011. **The arm is paid for being right; the payoff ratio is exit
  geometry.** An asymmetric exit manufactures a payoff above 1 on a random entry.
- **D530 - avenue 3 closed. The leveraged-ETF daily reset flow is real and carries no direction.**
  The equity roots trade **15.7-21.1% of session volume in the closing hour against an even 14.3%**,
  and both mechanism predictions fail: dose-response in the day's move reads 47.20% to 50.63% with
  Q5 at z 0.49, and concentration in the equity index reads **hit 50.03%, z +0.1 on 7,489
  observations**.
- **D531-D535, the opening-range breakout family: four pre-registrations, four DOES NOT PASS.**
  D531's gate broke its own prediction; D532's mechanism was declared with the sign backwards;
  D533's four conditions left only C1's sign standing; D534 found the gated state half as common as
  independence and displacement predicting **size, not direction**; D535's five declared guards
  earned their keep - **the contrast inverted in 2021** and the declared statistic is nearly
  orthogonal to the structure that is actually there.
- **D526 - the index roots trend intraday on a bounce-free mid.** ES, NQ, RTY and YM are persistent
  at **pooled t +3.10** with **10 of 10 signs replicating over twelve years**; ZT and SR3 were
  bid-ask bounce, and the rest of the rates complex reverts for real. A trade-close series must be
  paired against the quoted mid.
- **D523 - the path-efficiency label was void, and why.** The trending exception is **rarer than
  chance on all 35 roots** (gate 0b at **-61 SE**), and gate 0a passed on a between-root artefact.
  Path efficiency demands monotonicity and bid-ask bounce biases it down, so a real trend is
  invisible below H = 20. Simulate the effect and check the statistic moves before running it.
- `docs/FINDINGS.md` gains sections 73, 74 and 75: a slow conditioner's `n_eff` is in years, not
  sessions; **the directional base rate is not 50%** - it runs to **54.70% on ES at two hours and
  below 50% on natural gas** - and an exit rule scored on a hit rate answers a different question
  from the same rule scored in dollars.

### Fixed
- **D531's addendum had reported an ES upside-break hit rate of 55.08% as "+3.2 SE" against 50%.
  Against its true rotated base rate of 53.56% the lift is +1.53 points with 18.3% of rotated draws
  reaching it - inside the null.** The finding evaporated on the reference alone. **Across 48 cells
  the mean lift over base rate is -1.23 points and nothing clears**, where against 50% the same
  numbers had looked like a real asymmetry.
- **D533's C3 was the worst thing in the study on the declared statistic and the best thing in it in
  dollars.** On directional accuracy the exit lifts -3.95 and -3.03 points against the fixed
  60-minute exit, the largest single effect measured; at minimum tradable size the same rule raised
  gross Sharpe on all four roots (**book +0.80 to +1.03**) and produced the only positive net book
  in the record. It cuts the mean hold from 12.0 bars to 7.9 while raising gross dollars per trade
  and lowering the hit rate from 47.1% to 39.8% - it cuts losers faster than winners, and **a hit
  rate cannot see that.** The dollar reading was not pre-registered and is recorded as a lead.
- **D527 - the admitted arm fills at the worst minute of the day, and its cost line is amended.**
  The 1.009-tick crossing is a market-wide average and the arm does not trade at an average moment:
  it decides at h09's close and fills at h10's open, so **66.6% of entries land at 10:00, where MNQ
  averages 3.66 ticks and is one tick only 19.5% of the time**, against a day-session baseline of
  1.61; **75% of exits are the forced flat at 15:59, the day's best quote at 1.44**. Round-trip
  crossing **1.009 tk assumed becomes 2.411 measured**, the round trip **$3.50 becomes $4.21**, and
  in-sample net Sharpe **+0.724 becomes +0.661** against C-a's bar of 0.5. The entry stands,
  amended; the headline +0.698 is **not** restated, because a full re-score would read the spent
  2024+ slice. The bias runs in the arm's favour and the record says so - `tbbo` is 2025-26 while
  the window is 2016-23, and NQ went 4,000 to 27,000 against a fixed $0.50 tick. **Gross was 3.9x
  the assumed cost so the arm absorbed a 2.4x error; a construction whose gross was 1.5x its assumed
  cost would have been reported viable and been dead.**

### Fixed (D520-D524 - the flat id map, and one fixture that was wrong, 2026-09-13)
- **Every futures builder labelled bars from a flat instrument-id dictionary, and the dictionary is
  not deterministic.** `store.metadata.mappings` iterates in a different order in every process
  under string hash randomisation, so "the last write wins" picks a different winner each run. On
  the 2019 file **all 8 ambiguous ids get a different surviving label depending on the process**,
  8 observed of 8 over six hash seeds against 0.25 expected stable by chance. One id reads the
  Nikkei `NKDU0` five times and then **silver `SIF9`** on the sixth, so a five-read probe would have
  called it stable. **The count of mislabelled windows is stable; the identities are not - so two
  flat-dict builds of the same code over the same archive produce different fixtures, and a
  flat-built fixture cannot be reproduced or audited after the fact.** Distrust any pre-D520
  flat-built artifact beyond the rows a diff happened to catch.
- **D520 - `fut_sessions_hourly` was ingesting 229,206 foreign bars over a decade of archive
  (0.297%, 4.31% on the worst single file) and not one of them reached the panel.** The published
  nine-root fixture is **byte-identical** after the fix; the only change anywhere is **two rows
  removed from `fut_sessions_rolls.csv.gz`**, and those two turn out to be the "holiday artefact"
  D467's own G2 addendum had written up as a property of the euro market.
- **D521 - `fut_open_interest_daily.csv.gz` was carrying a phantom contract and is corrected.**
  Instrument 42007396 was `6AF4` (Australian dollar, January 2024) until 2024-01-21 and was reissued
  as `CLG36` in November, so the flat dictionary counted an FX contract as a **61st crude contract
  on 2024-01-03 to 2024-01-19**, overstating `oi_total` by 235-401 contracts (0.014-0.026%).
  **`oi_front` was never touched and all 63 gate scalars are identical.** Any cached CL total from
  before this commit must be re-pulled. `fut_micro_flow_5m` and all six `fut_index_1m` outputs are
  byte-identical.
- **The rule this leaves: front-month columns are insulated from the defect; totals and strip counts
  are not.** The open-interest fixture is the only one here with a column that has no volume filter
  in front of it, and it is the only one that moved - and **a term-structure study reads exactly
  those columns.**
- **D524 - `fut_day5m.parquet` verifies clean by two routes.** A rebuild into a temp path is
  byte-identical at 10,384,830 rows, and because `--build` reads a cached decode, the 5-minute bars
  were folded into hours and compared against `fut_breadth_hourly`, a separate decode pass:
  **906,905 root-session-hours, 0 differences in OHLCV and trade count, 0 orphan hours either way.**
- **D522 - RTY's G4 failure was one halted open, not a fixture defect.** Dropping 2020-03-16 takes
  RTY's open-to-close correlation with IWM from **0.989854 to 0.999339**. All four index roots
  printed once at 09:30 and nothing until 09:45 while the ETFs barely traded (QQQ at **0.4%** of its
  median opening volume), so the gate was comparing a limit-locked futures print against a cleared
  equity price. G4 now gates on sessions whose minute bars are contiguous over 09:30-09:44 - the
  span of the ETF bar the open leg is measured against, so not a free parameter - decided from the
  futures bars alone. **`fut_RTY_rth_1m.csv.gz` is committed; all gates pass on all four roots for
  the first time.** The threshold was not lowered and the statistic was not made robust: a rank
  correlation would have passed too, and would also have hidden a handful of badly-wrong days,
  which is the exact signature the id defect produces.
- **For any study: drop 2020-03-09, 2020-03-12 and 2020-03-16 if you read the 09:30 open of an
  index future.** The prints are real and are not tradeable opens.
- **And it reaches backward.** 16 of 36 roots do not trade in the 15:00-15:59 hour - the five grains
  have **zero bars** there, and CL, HG, NG and SI have full bars and dead volume - so every
  price-action statistic computed over a 09:00-15:59 template on a commodity root in this programme
  has included hours that root barely trades. **A close measured in an illiquid tail bounces on the
  spread, and bid-ask bounce is indistinguishable from mean reversion.** A first run of D530 showed
  a spectacular z = -12.6 "closing reversion" that was a control group measuring dead air.
- `scripts/build_fut_index_1m.py` is now parallel: **1.02 billion rows from ~20 minutes
  single-process to 6.2 minutes on 6 workers (5.67x, 94%)**, with `--verify N` proving the pool is
  a speed change only.

### Result (D506-D519 - the conditioner line on the admitted arm, and the spread census, 2026-09-13)
- **Four conditioners were proposed for the admitted MACD arm and all four close.** D508's absolute
  log distance from the 200-day average **ranks years, not sessions** - the primary Spearman is
  **+0.0089 at the 43rd percentile of its own exact rotation**, and within a year the relationship
  is negative in **seven years of eight**. D509 re-scored it on an economic primary and agreed to
  within a percentile. D512's range-expansion ratio is the closest a conditioner has come - **Delta
  +$25.37 a session against a rotation p95 of +$27.54, the 93.4th percentile, missing by $2.17** -
  and its 23-hour version clears its own null at the 98.6th percentile, which would be selection to
  take. D513 carried it to six roots with an unread slice and **it does not transfer: positive on
  three of six, a coin flip, with the declared primary at the 68.2nd percentile.**
- **The structural finding: conditioners on the admitted arm are unavailable, because the arm has no
  unread slice.** None could be confirmed even if one had cleared. Check that the target still has a
  holdout before designing a conditioner.
- **D509's methodological keeper: an exact rotation of a quintile-difference statistic subsumes a
  hand-built run-length-matched gate**, proved in the runner - duty 20.0% to 20.0%, 38 runs to 38,
  run-length multiset identical. **Prefer a statistic whose own null contains its control.**
- **D506 - in-play selection fails as alpha and works as drawdown management.** The fee lever is
  exactly what the premise promised and is swallowed: across 16 cells the fee term is **+0.85 points,
  positive in 16 of 16**, and directional accuracy is **-2.09 points, negative in 11 of 16**. The
  family p95 is +0.2192 against an observed maximum of +0.0620, so **97.8% of offsets beat the best
  real cell**. The decisive figure is the untradeable bound: conditioning on the day's **realised**
  range, which nobody can do in advance, is **-0.0018**. There was no prize to win even with perfect
  foreknowledge of the day's size. **But the same filter cuts P3a three to five fold** - ZB 14.00 to
  2.71 breaches a year, ZN 2.00 to 0.71, the NQ drift 0.57 to 0.00 - because both prop death
  mechanisms are counted in exposure-days.
- `scripts/activity_filter.py` - the filter kept as a standing module with `--selftest` and six
  checks, causal and root-agnostic. **One indication: reach for it when a construction fails P3a and
  nothing else. Never use it to choose direction.**
- **D510 and D511 - the tick binds on ZN and ZB and on nothing else**, and three independent
  measurements order the eight roots **identically at rho +1.000**: **ZN needs 261 trades to move
  one tick while one NQ trade moves two**, and a ZN crossing costs **16x** its per-trade volatility.
  The property that makes the large-tick roots predictable is what makes them expensive.
- **D514 and D515 - the Dow is not slow, it is trading the wrong hours.** Splitting the one-bar edge
  into day and night: NQ **+0.0275 day against -0.0008 night**, ZN +0.0225 against -0.0096, YM
  **-0.0004 day against +0.0078 night**. **ZN has the second-largest day edge of the eight, larger
  than the S&P, and still loses $12.83 a trade.** Why NQ, in one sentence: the largest day-session
  edge of the eight **and** the cheapest cost relative to its move, 3.2% against 6.3% for the next
  best. Removing the minimum hold makes YM worse, not better (-1.837 at M <= 1 against -0.412 at the
  frozen M = 5), so the exit is exonerated and **the window is the ceiling, not the hold.**
- **D507 - the spread census on all 41 roots.** Micros quote tighter than their parents, and the
  repository's 1.009-tick crossing assumption was wrong by up to **twelvefold**. A ten-day sample
  understated the full-year crossing by **62% on GC and 56% on NQ** and by under 6% on ES and 6E -
  **the error scales with book depth.**

### Fixed
- **D507's own section 8 corrects three things in its sections 1-7**: M6E's tick is double 6E's so
  the crossing in M6E ticks is half what was charged; the headline generalisation is wrong, because
  **three of eight micros are more expensive than their parents on the cost actually paid**, not one
  of five; and the GC, CL and 6E rows overstate the crossing by up to **75%**, having used the full
  contract's spread where the micro's is now measured.
- **`spearman` divided the covariance by n and the standard deviations by n-1**, so it was short by
  (n-1)/n - **0.05% at n = 1,876, so no D508 number moves, but 20% at five points** - and its
  n >= 30 guard silently returned NaN for a five-row monotonicity check. `rank_corr_small` fixes both
  and asserts the difference.
- **D502 - the 200-day SMA filter halves the candidate and its mirror beats it**, so the filter is
  not a filter. There is no trendiness on the daily clock to gate on: the median daily variance ratio
  is below 1 on seven of eight roots, and NQ is above 1 in **0.4% of sessions**.

### Result (D493-D505 - the prop components search, K8, and the barrier, 2026-09-12/13)
- **D498 - K8 is the components ledger's first and only entry, PROVISIONAL.** Long the NQ day
  session after a down day: **871 trades (44% of sessions), gross +$17.87 a trade (+11.6 bp, SE 4.0,
  median +$20.50), hit 57%, skew -0.02, positive in 6 of 8 years and both sub-periods**; after an up
  day the day session is -3.1 bp, so the difference is **z +2.89 against a family p95 of +2.41**;
  **net Sharpe +0.61 (SE 0.32)**; C-a, C-c and C-d pass. ES is the same sign at half the size and
  inside its null, at rho ~0.85 with NQ. The three declared second clocks are flat.
- **D503 - the one-pass forward read, and the holdout is spent.** 2024-01-02 to 2026-09-09 on the NQ
  day session is spent for both components and for the book. **The Sharpe transferred and nothing
  else did**: the MACD component's net Sharpe went +0.723 to **+0.736**, and its daily sigma went
  **$180 to $340, +89%, on price level alone**, with skew flipping -0.05 to +0.68. **One micro has
  grown into the prop barrier**; the binding constraint is now the vehicle, not the edge. K8's own
  forward read was **gross -$4.46 a trade against +$17.87 in sample, net Sharpe -0.160**, and the
  principal closed it on the negative gross mean. **The prop ledger holds no live entry.**
- **D493 - the account-size lever fixes the fee and runs into the barrier.** Every published plan x
  ES/NQ x micro/full x 1-5 contracts through D386's lifecycle: **0 of 448 cells carry.** Leaving the
  micro takes NQ's last-30 trade from a net Sharpe of **-0.13 at one micro to +0.48 at one full
  contract** and immediately exposes the barrier - a full contract's daily sigma is **3-6x the
  plan's $2,000-$4,500 trailing drawdown**, so funded life is **0.03-0.16 years on all fourteen
  plans**. The micro sits about 40 sigma from the barrier and loses on the fee. **Size cannot fix a
  prop edge.**
- **D494 - direction from outside the price path is worth at most one tick a day.** Eighteen declared
  cells - five cross-instrument overnight predictors, index-level Robintrack sentiment, three
  release-day gates on the MACD - **no pick**. The largest is the euro into ES at one tick, and the
  MACD earns **less** on CPI and payroll days, because the day leg starts ninety minutes after 08:30.
- **D495 and D497** - the day session after a big down day on NQ is **+$42.61 gross a trade on 110
  trades (+21.9 bp, SE 14.5), hit 56%, net Sharpe +0.47**, and it fails the family bar because the
  other side - long NQ's day session after **any** down day - is **+10.2 bp on 761 days**. Most of
  the pick is the drift. The four-quadrant open-interest read carries nothing on four roots, and on
  gold **the quadrant the textbook says to fade is the most positive** (+$10.7 over 334 sessions).
  **Useful negative: open interest is distinguishable from volume**, the two giving answers that
  differ by 3x and flip sign.
- **D499 - the hourly clock, closed by the principal.** The off-hours reversal is real on the US
  clock (pooled beta **-0.043 on ES, -0.037 on YM, -0.028 on NQ**, outside their exact rotation
  bands, with crude **continuing** at +0.030) and worth **1.7 to 4.9 ticks a trade, net negative
  after the $3 fee**. The volume partition shows nothing, because **London is thick on every root**,
  so the volume-thin set and the US-off-hours set are different objects. And the arithmetic closes
  the clock before any signal: **the fee is 14.5% of the expected hourly move on MNQ's thin hours
  against 2.4% on the day session**, and 19-80% on ZN with the tick.
- **D504 - the Asian chip channel is real, semis-specific, and clears entirely in the gap.** The
  Asian chip signal is worth **+25.65 bp (t +4.25) into the semis' relative opening gap and -1.65
  (t -0.64) into the day session**. The traded primary is +8.0 bp against 11.7 bp crossed. **The
  family maximum is a control** - transports against QQQ at **+27.97 bp, hit 61%, clearing its own
  rotation at the 0.8th percentile with no mechanism at all.** Keep a mechanism-free sector control
  in any study whose conditioner is a foreign market.
- **The one vehicle measurement worth keeping: the unconditional MNQ/MES day-session pair has a
  daily sigma of $128 against one MNQ's $282**, with zero days beyond -$1,000 in six years against
  the single micro's 0.2 a year. A hedged micro pair is the only construction that lowers the dollar
  sigma without leaving the micro; the dollar beta of NQ on ES is 1.72, so 1:1 under-hedges and 1:2
  over-hedges at $9 a round trip.
- **D505 - the expectation, priced.** The principal's stated expectation for the yearly breakdown is
  a **Sharpe-1.34 strategy**; the magnitude half of it is already met; and the thing worth being
  unhappy about is that **four accounts in five pay nothing**.
- **D500 and D501 (renumbered from D497/D498) - the worst day is a regime, not a habit.** D500 read
  P3 as a binary failure on a worst day of **-$1,315 against a $1,000 cap**; D501 computed the rate
  and the maximum turned out to be the wrong statistic - **two breaches in 1,873 sessions, 0.27 a
  year, one every 3.7 years**, with the worst day never reaching -$550 in six of eight years and
  2022 alone holding 13 of the 20 days beyond -$500 and both breaches.

### Added (D484-D492 - the log MACD, retail flow, and two rules of the principal's, 2026-09-12)
- **D484 - the log impulse MACD is the first construction in this programme to PASS a rotation
  null.** Pooled **+0.00961 at +39.6 SE** against the R1 p95, family maximum **+0.03256 at +13.8
  SE**; the off-diagonal lookback fails both at -62.2 and -23.5 SE. **0 of 84 costable cells are net
  positive.** It is a real signal that fails only on cost, and it reaches about **50.7% directional
  accuracy** against a break-even of 51.2% and a component bar of 53.6% - **the gap is three points
  of accuracy, not cost.** Rotate a smoothed signal; never shuffle it.
- **D485 - the micro contracts are not a retail identifier.** Within-session correlation of micro
  signed flow with the E-mini's imbalance is **0.71 on ES and 0.76 on NQ**; micro trades are **not**
  smaller (NQ's E-mini has more one-lots than the micro); there is no contrarian tilt, no sell bulge
  into the flatten window and no relation between the day's micro flow and the last hour. New fixture
  `data/fixtures/fut_micro_flow_5m.csv.gz` (exact aggressor side from `tbbo`). **Identify retail by
  construction - holder counts, tagged trades - never by contract size.**
- The retail-flow scoping in `docs/research/retail-flow/00-scoping.md`, and the literature that
  contradicts the folk rule: the **body** of retail flow is weakly informed **with** it (+10 bp a
  week) and only the **extreme of attention** is contrarian (-4.7% over 20 days). Robintrack is on
  disk at `data/raw/robintrack/` - 4.0 GB, 8,597 tickers hourly 2018-05 to 2020-08.
- **D487 - the ORB line closed at stage 0.** Continuation lives in **2018 and 2022** (variance ratio
  1.32 and 1.23 on ES, the same two on NQ) and **2020 is the most mean-reverting year at 0.88**; the
  quiet-volatility tercile trends most at 1.18; the first half-hour reverses into the last
  (**ES -0.10, -4.3 SE**); the next-day reversal after top-decile days is **-24.5 bp on NQ**. An ORB
  is a wrapper on intraday continuation from short-gamma hedging and delayed rebalancing, and it is
  flat in the 0DTE era.
- **D490 and D492 - the principal's range-reversion rule loses gross on both sides and both roots.**
  Development split: **ES pooled gross -$3.48 a trade, net Sharpe -1.14 (SE 0.38); NQ -$4.96,
  -1.03.** Long hit 57.6% with a median of +$10 and a mean of **-$2.70**; the target is reached on
  5% of trades and 78% ride to the close. **A wrong-range control - a range 3 to 22 sessions old,
  same mechanics - has a mean of about zero, and the rule is below it.** Three fifths of the longs
  are below yesterday's low on a volume spike: a breakdown with flow, not a stretched tape. The first
  declared filter set (an hourly RSI(14) confirmation) removes 74-77% of the trades and leaves the
  rest at zero, still below the stale-range control on both roots. **Neither reserve was touched and
  the runner refused the validation read.**
- **D486, D488, D489, D491** - cost-cutting closes 70% of the MACD's gap and stops, and only NQ gets
  anywhere; extending the hold fails, and the closure accidentally produced the first net-positive
  cell; **ZB is genuinely a large-tick instrument and the sigma that failed C-d is the window, not
  the contract**; and the conditional-hold exit is the first component candidate, thinner than it
  looks.
- **D469 - commission, not spread, binds at micro size.** Crossing is scale-free at about 1.01 ticks;
  **$3 a round trip is 2.40 of MES's bar.** C-d forces the micro.

### Result (D476-D483 - the daily channel line, closed by the principal, 2026-09-12)
- **The line ran D399 to D483 on a branch, spent no holdout, and is closed.** A causal daily channel
  from confirmed pivots, rebuilt three ways - the oracle's greedy window search made causal, with
  hysteresis and trend-side breaks, and re-dialled against the principal's own hand-drawn lines
  (**sign agreement 92 / 87%, recall 69 / 71%**) - and traded three ways.
- **Direction is worth nothing by any reading.** Five causal cells: long **+1 to +17 bp gross**,
  short **-39 to -54**, **every one below a within-name time rotation of its own trades** whose long
  p50 is **+37 to +59**. It gets worse as the gradient floor rises in every sweep. The cell that
  draws the principal's lines and confirms five bars before the principal does trades the same, at
  **+12.3 ± 3.4**. **A confirmed direction is a late one however early it is confirmed, and steeper
  is worse in real time - the gradient floor lifts hindsight lines and sinks causal ones.**
- **The oracle is a tautology, not a ceiling.** Hindsight windows with their boundaries hidden from
  the trader earn **+780 to +1,272 bp a trade at 84-93% win rates**, because a channel that exists at
  t was selected by what follows t. **A hindsight channel leaks the future through its EXISTENCE,
  not through its boundary**; the only honest oracle trades beyond the fit window.
- **Level is the first channel cell to meet the programme's signal criterion, and the control took
  it.** Long on a close at or below the bottom tenth of the channel, held 5 bars: **+43.6 ± 5.6
  gross, median +58, 41 SE above its null**, 52 names to half the P&L, net -34. Then D483: a close
  **4% below the previous 30 bars' low with no lines at all earns +47.4 ± 10.1** over the same five
  bars, and inside a live channel **+45.2**. **The channel adds nothing beyond the first day, and the
  channel was never the ingredient** - what D482 found is short-horizon reversal after a sharp break
  of a range, both directions, about 5-9 bp a bar for twenty bars.
- **Better lines trade identically.** Longer windows and hysteresis produce the same trade; the rule
  chops inside the window it was built to keep.
- Kept: `data/d478_hand_drawn_lines.json` - **140 lines drawn one bar at a time with the future
  hidden**, each with its draw bar and end bar - its scorer `scripts/d478_score_hand_lines.py`, the
  hand cell `scripts/d480_hand_cell.py`, and `scripts/run_d478_grow_trades.py`. **On that scorecard
  the principal's anchors sit 4% outside the wicks, are drawn one bar after the second swing, live 26
  bars, and end 45% on a break, 40% by replacement and 15% by drift.** Score constructions on it
  before trading them.
- **Overstay must be scored only on ends that were ends: 40% of the principal's ends were
  replacements.**
- **The line was renumbered at the merge**, because the branch's numbers collided with master's: it
  now sits at D398, D399, D476 and D477-D483, and the closing record carries the old-to-new map.
  Master's own D434 and D450-D463 are unrelated records.

### Added (D462-D475 - the futures data layer, the components ledger, and the overnight leg, 2026-09-12)
- **111.0 GB of CME futures on disk, verified.** Databento `GLBX.MDP3` under a one-month CME
  Standard subscription: every job quoted **$0.00 against $7,719** at published rates, total cost the
  $199 subscription. `data/raw/databento/` - `ohlcv-1m` on every instrument 2010-06-06 to 2026-09-10,
  `mbo` on eight roots for a month, `tbbo` on every instrument for a year, `statistics`, `definition`,
  `status` and `bbo-1m` on 41 roots. **129 of 129 hashes and byte counts verified, 16 of 16 DBN
  headers match the request, and the ten `ohlcv-1m` slices tile with zero gaps and zero overlaps.**
  Prices are **unadjusted raw symbols with no continuous series at all** - the roll must be built
  from `definition`. **It was written to `temp/databento/` on 2026-09-11 and moved to
  `data/raw/databento/` the next day**, because `temp/README.md` promises that if deleting a file
  would cost something it does not belong there, and this is free to re-fetch only to ~2026-10-11.
- **D462 - `scripts/build_fut_index_1m.py` and the ES, NQ, YM one-minute regular-hours fixtures**,
  front month by measured volume, no stitching, five gates, **usable from 2016-01-04**. The archive
  carries the index futures' evening bars but not their day session on most days before 2016 -
  **21-42% of the calendar in 2010-12** - so a fifth gate had to be added to see it, and **every
  earlier ES study's 2010-2015 numbers rest on 20-85% of days**. ZN, ZB, GC and 6E are complete from
  2010.
- **D467 - `data/fixtures/fut_sessions_hourly.csv.gz`**, hourly session tables 18:00 to 16:59 on
  ES, NQ, YM, ZN, ZB, GC, CL and 6E, front by volume, roll nights flagged, five gates, usable from
  2016-01-04 after two gate amendments (holiday sessions have no 16:00 print; the pre-2016 index and
  crude sessions are partial).
- **D466 - `docs/COMPONENTS_PROP.md`, the append-only components ledger and its pre-registered
  admission standard**: C-a net Sharpe > 0.5 **at minimum tradable size and the cost that size
  pays**, C-b rho < 0.3 with every prior entry, C-c skew >= -0.5, C-d sigma <= 1% of $50k, C-e
  provenance. **The ledger is empty after 30 constructions.** The figures that opened it - **C1 at
  0.62, NQ last-30 at 0.42, a 0.91 book at rho 0.09** - were shell-line numbers at full-size cost in
  basis points; under the standard, in dollars at one micro with $3 a round trip, they are
  **+0.37 and -0.01, and no book.**
- **D468 - 24 session windows on eight roots, none clears.** Best is ES-W1 at **+0.39 (SE 0.32), the
  78th percentile of the common-sign family-max null** (p50 +0.55, p95 +0.95). The overnight index
  drift is gross +0.54 to +0.64 on ES, NQ and YM and the $3 micro round trip takes **30-70% of it**;
  treasuries, gold, crude and the euro carry no session drift. The three index roots are one
  construction at rho 0.91.
- **D470 to D473 - the down-leg reversal, K7, entered and REMOVED on its own declared forward read.**
  The principal's continuation and above-average conditions came out **with the sign reversed** - the
  drift follows **down** sessions and **down** overnight legs on 8 of 8 cells - and the cleanest cell
  reached gated net Sharpe **+0.70 on ES and +0.62 on NQ at micro cost**, clearing both gate nulls
  and failing the family-max p95 on both because its size lives in 2020-2022. It replicated on SPY
  and IWM cash 2010-2015, outside the family, at **+5.5 / +7.7 bp against about 0**, right in 11 of
  12 symbol-years. The forward read, run on the principal's word: **NQ after a down leg +$30.76
  against +$21.29 after an up leg (+0.4 SE), SPY cash +0.71 against +9.22 bp (-1.6 SE), pooled
  z -1.30.** The gated nights paid because the whole overnight drift was strong; the down-then-up
  structure did not carry, and on cash it reversed. **Every forward prediction was wrong in the same
  direction. The process held: rule first, no sharpening, the rule fired.**
- **D474 and D475 - price-path momentum fails at every horizon tested on futures**, 10 seconds to
  5 hours, two clocks, eight roots. D474's ES volatility-conditioned continuation gradient was
  **in-sample selection and the sign flips on seven unseen roots.**
- **D471 - path efficiency is exactly the random-walk value on ES.** Use the variance ratio instead:
  **0.82 at 1 s, about 1.00 past 15 s, never above 1.02.** Efficiency fails as a conditioner, and a
  stop must be about half the target.
- **D463 and D464 - the first two prop candidates screened on the futures themselves, and both die
  on the instrument-account pair.** Market intraday momentum over the last 30 minutes on ES is
  **+1.18 ± 0.86 bp a trade at a 49% hit rate, slope +1.8 against the published 6.18**, inside its
  sign null. Hurdle P's P3/P4/P5 were computed for the first time: the sizing rule sizes below one
  contract at f <= 0.4%, and at every size that trades the worst day breaches 2% on 13-87 days.
  **A single ES contract's 30-minute sigma is about $650, so on a $50k account the floor is 3 sigma
  away per trade and no single-contract ES construction at that sigma clears P3/P4 whatever its
  edge.**
- **The overnight line is closed for the prop book and open for the personal book** (the principal,
  2026-09-12). The NY Fed mechanism - the index overnight drift as compensation for closing order
  imbalances at 2-3 a.m. ET - **compressed after 2021**, and a gate needs a mechanism that survived
  it. The unconditional drift is real and unaffordable at $3 a micro round trip.
- **The two-altitude rule, written into `CLAUDE.md` after the principal's correction.** Three prop
  records - C1, D463 and D464 - were written "closed / not a candidate" on standalone hurdle-P bars
  **with no component line.** The book is built by layering components at net Sharpe > 0.5 and
  pairwise rho < 0.3 to reach the account's 1.5-2, never by one strategy. **A standalone failure of
  hurdle P is not a verdict on the construction; it is the answer to one of two questions.**

### Result (D443-D461 - the filings programme, and three real effects that do not book, 2026-09-11/12)
- **Alpha Vantage's fundamentals serve 0 of 562 dead names** (D443, abandoned on its pre-registered
  coverage condition). **The SEC's XBRL companyfacts serve 433 of them** (D444) in about seven
  minutes, with the filing date of every value and a restatement rate of 0.1% on share counts, so
  first-filed is point-in-time for free. **11% of the fixture - multi-class and foreign filers - has
  no undimensioned share count in that API**, filers mis-scale counts on 0.2% of rows, and the
  vendor's counts agree with the first filing within 1% on **only 45%** of overlapping
  name-quarters.
- **D446 and D453 - net share issuance predicts the hedged return of the name per trade on both
  sides, against the right control, and the book is under one SE on thirteen years.** Short net
  issuers **+72 gross against a cell baseline of -97, increment +169, 2.6 control-SD**; long net
  repurchasers **+208 against +34, increment +174, 2.5 control-SD**. **The cell baselines are the
  finding as much as the increments** - shorting small volatile names loses 97 bp a half-year hedged
  and buying large low-volatility ones earns 34, so a study without the cell control would have read
  +208 as edge. The book is **+2.30 ± 1.51 bp/bar gross**, the common-offset rotation earns **+1.12
  with a p95 of +3.77**, the name-randomised selector **+0.39**, so the alignment term is about
  **+1.2 bp/bar on an SE of 1.5**. Beta-hedging and vol-scaling cut the SE to 1.17 at the same gross
  and **did not touch the rotated base rate** (+1.12 to +1.27) while the name-randomised one fell to
  +0.08.
- **D454 and D455 - an insider's open-market purchase is followed by +89 bp hedged over the next
  quarter, +65 over its cell, in the body of the distribution - and nets zero at the crossed line.**
  17,270 purchase filings 2010-2023 on **76% of the fixture and 71% of the dead cohort**, 90% filed
  within the statutory two business days. Median +96, 1%-trimmed mean +89; clusters of two or more
  distinct buyers **+120** against a single buyer's +54; directors only +101 against officers' +58;
  **the sales mirror is -23 ± 12, so sales carry no information.** The book is +1.11 ± 0.56 bp/bar
  gross, the rotated calendar earns +0.66, the crossed line costs 1.03, net **+0.08**. The top name
  is 6% of the P&L across 865 names - **this one is not tail-carried.**
- **Map issuers by CIK, never by ticker: 17,709 filings match a fixture symbol that belongs to
  another company.** Ten-percent owners are 18% of filings and nine of the ten largest dollar buys
  and are a different mechanism, set aside. Hyster-Yale's sixty-odd family trusts each file as a
  reporting owner and are every top "cluster" without a guard.
- **D456 and D457 - no 8-K item type carries a ten-day drift after the next open.** 154,970 8-Ks on
  82% of the fixture and 81% of the dead; 17 cells x all/pure x both sides against a state-matched
  control and an exact rotation, a family of 34 tests with 0.85 chance clears on the first control:
  **0 clear both, 4 clear the first, all on the long side.** After any 8-K the name does **+8 to +16
  bp better over ten bars than a quiet name in the same cell** - and the rotated calendar earns the
  same, so it is the filers' composition, not the filing's timing. **Every distress item is
  long-favoured after the next open** - impairments +59, delisting notices +103, auditor changes +92
  per trade, all with **negative medians**: the fall is in the gap the daily fixture cannot enter.
  **Every pre-registered short-side sign was wrong.**
- **The one-line lesson of the programme:** every information source outside the price path -
  volume conditioned on state, share supply, insider demand, the corporate-event calendar - produces
  a real per-trade effect against a control built to kill it, and none survives either the cost of
  the names it lives in or the gap it is priced in. **The true sentence is not "no signal"; it is
  "no book at this cost model on this fixture."**
- `docs/FINDINGS.md` section 67 - **the three-control template now used on every line**, and what
  each median means: the state-matched control's median is **not zero and is the first number to
  read**; the rotation's median is the composition's base rate; the gap between the rotation and the
  name-randomised selector is the price of the state tilt. **Predict the rotation's median from the
  cell baselines, not as zero.**
- **D458 to D461 and D465 - the prop lifecycle instruments.** The hold-length curve has no
  identifiable optimum and the observed argmax is **below its own nulls' median**; beyond 22 hours
  the shape-constraints lever does not exist at the frequency the rules operate on; conditional exits
  are the first thing in the chain to beat a matched control and still fail P4; a stage-0 on prop-firm
  forced flow at the flatten minutes was **abandoned**, because the hour is a decay from the cash
  close and a minute with no rule outranks both targets; and **the cost line was never what killed
  C1** - crossing costs a tenth of the edge.

### Result (D434-D442 - the volume line, and the cost models are range models, 2026-09-11)
- **The chain: a volume atlas flat as a universe average, then the conditional atlas that shows why.**
  A 3x volume day is **+38 bp in top-momentum names and -48 bp in top-price names** over the kernel's
  horizon, **and the average hid the sign flip.** The principal called for the conditional atlas and
  it is the method finding of the line: **cross a new feature with the atlas states before calling it
  flat.**
- **The one component that survived every stage** - a 3x volume bar in a top-price name, sold short -
  carries **+13 bp at 5 bars to +37 at 60** above a state-matched control's p95, and its increment
  lives in the **widest spread tercile** of its names. As a book at cap 20: gross **+38.8 a trade,
  +2.24 bp/bar**; crossed **-18.3 a trade, -0.63 bp/bar**; passive at the open **+7.1 a trade, +0.65
  bp/bar on an SE of 0.89**. 16 names to half the P&L and the top 1% of trades at 108% of it. **Not
  distinguishable from zero on sixteen years.** Both daily holdouts stay shut.
- **D439 - the repository's half-spread is a range estimator, and this reaches back to D285.** The
  PUB half-spread the kernel charges reads **median 28 bp a side, terciles 22.7 / 35.0, wide tercile
  55** on MSFT, JPM, CSCO, INTC, V and PG. **Their quoted half-spreads are one to two basis points.**
  The estimator reads intraday *range*, and range and quote converge only on small illiquid names.
  **Every net-of-cost verdict since D285 was made against a range, not a spread**: on small thin
  volatile names the two are close and the verdicts likely stand; on liquid names a construction has
  been charged up to ten times its cost.
- **What was measured model-free on those names: a limit at the open that needs a 5 bp trade-through
  fills 92% of the time**; on the 8% of days it does not, the price is +112 bp away at the half-hour,
  so the chase costs about **9 bp per order**; net of the chase a passive order recovers **0.66 of
  the modelled half-spread** (0.72 in the wide tercile, 0.57 on volume-shock days). Records since
  D439 print a second "passive at the open" line - modelled half-spread x 0.34 per side plus 9 bp
  chase - **labelled an assumption**, beside the crossed line.
- `scripts/d336_ibkr_quoted_spreads.py` and `scripts/run_d441_b_quotes.py` - the quoted-spread pulls,
  built, dry-tested and **blocked on a TWS session**. Raw bars land in `data/raw/ibkr/`, gitignored
  and exchange-licensed. **The highest-value unrun measurement in the programme**, because it would
  retire the range assumption on every record at once.
- **Two fixture facts the pull will hit:** the fixture carries **acquired names as `alive` with a
  constant close and zero volume** since the acquisition (SPLK pinned at 156.9, SGEN, KRTX, AVNS),
  because the metadata counts a delisting after the span end as alive. **Require volume > 0 and
  distinct closes over the last 21 bars when selecting live names.**
- **D442 - O1 clears the ledger's own criterion and dies inside the rotation null**, and the mask
  breaks the inactivity rule; its addendum records that **the two apparent wins were selection across
  four risk fractions.**
- **D440's second study, on the instrument** - the Gaussian was worth five sixths of the value, and
  **it is clustering, not kurtosis**; D452 repeats it and puts clustering at **94%, not 83%.**

### Fixed
- **D434's event pools were one bar ahead of the fill.** A causality check is not a mask alignment
  check: read the fill convention first and assert it. Re-run `[F]`-aligned.
- **D437's net prediction was off by 2x** because it did not quote the prior study's cost line. Read
  the cost convention the kernel gates on, and quote it beside any net prediction.
- **D439's adverse-selection term was the wrong one**: net capture is fill x half-spread minus the
  chase.

### Result (D412-D433 - the second-zone line, both daily holdouts spent, 2026-09-10)
- **Twenty-two studies, two holdout reads, and the line is closed by the principal.**
  `us_shorts_daily_holdout` (803 names) was read a second time under the principal's ruling that a
  holdout spent by an unrelated strategy is unseen by a new line; `us_shorts_daily_holdout2` (576
  names) was read once. **There is no unseen daily single-name data left for anything descended from
  a departure-zone touch.**
- **What is true across three disjoint name sets (1,573 / 803 / 576):** a distance-armed
  departure-zone touch entered at the touch-day close and exited at `t+5` earns **+9.8 / +10.1 /
  +13.0 bp gross**; the armed cell makes it **+30.3 / +18.1 / +18.0**; and the cell crossed with the
  top-ADV tercile makes it +37.9 / +21.3 / +13.4. **Cost is 24-34 bp. File the touch effect as a
  base rate a future study must beat; it is not a trade.**
- **Every layer selected on the spent names after one look vanished**, on both unseen sets: the
  second touch **+45 to +6 / +17**, the cheap tercile **+86 to +17 / +28**, long-only **+80 to
  -29 / -21**, the gap ordering inverts, the ADV tercile's gross side, a breadth gate and nine exit
  constructions. **Net Sharpe of the best transferable object: +0.05 / -0.03 / -0.19.**
- **And every in-sample null they passed - within-day permutation, matched random pools, +5 to +10
  SE - tests selection inside the spent names, not transfer.** The in-sample 2020 premium was the
  names: on unseen names 2020 was **-635 bp per cheap long.**
- **Two exits worth remembering as facts:** no ATR, structure or zone exit beats `t+5` with nothing,
  because inside the hold the expected remaining move is non-negative in every state including at the
  prior swing; and the one exit that carried information - a limit at the *next live* opposite-side
  zone - did so only on events the final construction dropped.
- `scripts/run_d430_holdout.py` - a fixture-parametrised pipeline with an in-sample `--proof` that
  reproduces bit-identically before any out-of-sample read; the ladder printed on the holdout so a
  failure is located; Sharpe with a monthly block-bootstrap SE.
- **Process disclosure, and it is recorded rather than smoothed.** `run_d411` installs an
  unconditional audit hook refusing any path containing "holdout", with no `allow` switch, and the
  designated logged unlock lives on a module this chain does not import. The two reads were opened in
  **separate hook-free processes** (`scripts/d430_oos_loader.py`, `scripts/d433_oos2_loader.py`,
  `--spend-the-holdout`), wrote the panel to a cache named without "holdout", and printed a receipt
  with the file's SHA-256. **The information the designated door would have logged is in the
  receipts; the designated function was not called.**
- **A prediction on a date-defined subset must have its sign computed from spent data before
  pre-registration** - the breadth gate was pre-registered with the wrong sign on a true stage-0 fact.

### Result (D398-D411 - the 15-minute structure line and the auxiliary-data screens, 2026-09-09/10)
- **D399 - stage 0 clears, the atlas fails cost, and the short leg cannot be tested at 15 minutes.**
  The ratcheted structural line's stage-0 state is **a direction, not a trigger** (D398).
- **D403 - the object was real and the barrier was not.** The wick-stack potential map read at 15
  minutes.
- **D405 - the capital-gains overhang is momentum, and its map is grid noise.** A map of shares still
  held reproduces the momentum ranking and adds nothing beyond it.
- **D406 and D409 - options open-interest density at spot fails its pre-screen**, and the pinning
  effect **is real at the expiry and absent over the quarter**. D408's W2 cell made primary on a
  disjoint slice: **the magnitude replicates, the shape does not.**
- **D411 - the sign is the half that matters and the volume is not.** Signed volume at price: the
  volume nodes were missing half their information, and the control that was supposed to break the
  claimed ingredient **preserved the sign it was meant to test.**
- **D407 and D410 have no record file: they are the ends of a block reserved for an absorption study
  that D412 records as NOT consumed**, and **D410 is nonetheless cited by 33 other decision
  records.**
- **D400 discharges R11's re-costing corollary for the Donchian ladder** - see the Fixed block below.
- **D401 - the principal closes the winners'-dip and the 15-minute structure avenues.**
- `docs/FINDINGS.md` section 60 - **`etf_wide_daily_raw` is not an ETF fixture.** **150 of 551 names
  carry a closed-end-fund distribution signature (27.2%)** on a rule declared before the counts were
  read, so every count is a lower bound, and an independent listing-flag count gave 172 (31.2%).
  **23 of its 24 dead names are closed-end funds by inspection**; the single exception paid no
  distributions at all. Distributions absent from `close` run at a whole-fixture median of
  **3.06%/yr** and a CEF-cohort median of **10.54%/yr**, understating terminal wealth by **5.37x**
  over sixteen years. **A dead-inclusive fixture whose deaths are fund term maturities and mergers is
  not measuring delisting risk at all.** Three studies had already run on it; all three pass the
  events file to `load_ragged` so their P&L is unaffected, and what is affected is anything reading
  `closes` as a price level - which is exactly the log-price axis the density line was built on.
  **A fixture's name is not its composition, and a status count is not a cause of death.**

### Fixed
- **D400 - D163's cost arithmetic is wrong by a factor of about 400, and the closure survives
  anyway, on signal.** The closure rested on "pays roughly 300% of capital a year in fees at the
  taker tier", which is **crypto spot at 40 bp/side**. At the futures figure of ~0.1 bp/side the same
  786x/yr turnover costs **0.79%/yr**: **BTC 15m goes 314.5%/yr to 0.786%/yr and ETH 298.3% to
  0.746%**, and the maximum cost drag anywhere on D163's ladder goes **4.11 Sharpe units to 0.0115**.
  Under the futures convention every cell reads "edge survives". **It changes nothing, because there
  is no gross edge at 15m to cost**: BTC is **-1.4 bp a trade over 2,628 trades** against a rotation
  null centred at +4.3 and ETH **+1.9 bp** against +4.5, at the 2.4th and 22.0nd percentiles, and
  both go negative on a symmetric 1% trim (**-7.8 and -5.2 bp**). D163 is not edited; under R8 a
  result is a separate record.
- **D402 - D280's overnight gap is not an opening-print artefact, and 17.6% of bars carry one
  anyway.** `[REP]` reproduced D280's committed gap IC to five decimals before any filter. Flagged
  share of 2,232,440 out-of-sample bars: **open == prior close 5.84%, open at a session extreme
  13.16%, all four signatures combined 17.58%**; `corr(gap, intraday)` is **-0.1564 on the
  contaminated bars and +0.0082 on the clean ones**, so the reversal a stale print must produce is
  confined almost exactly to the flagged bars. **Removing every contaminated bar makes the edge
  larger** - -0.01746 (t -4.49) against a committed -0.01531, on 60% of the sample. **The
  discriminating test ran the other way from the prediction written against it:** the gap IC is
  **1.8x stronger in the most liquid dollar-volume quintile than the thinnest** (-0.02194 against
  -0.01231), and a print artefact must concentrate where prints are unreliable. **This removes a
  doubt about the measurement, not about the money** - D280's own runner already records that the IC
  does not survive into money at N=25.

### Result (D384-D397 - the density line and the sign-sequence chain, both retired, 2026-09-08/09)
- **The density line, D384 to D388, is retired by the principal after five studies and about 4.5
  hours of compute, three of them spent measuring the wrong thing.** The object works: given a
  genuinely rare event it produces a smooth, causal, price-invariant, multi-modal density -
  **TV(f,g) 0.18-0.51, ratio CV 0.51-1.31, 2-3 modes** - proved bit-identical against an explicit
  loop. **What closed it is that the conditioner is inert.** It beats a shuffled-path null in **34 of
  36 cells at p to 7.2e-11** and a **rotated-density** null in **0 of 36**, and
  `corr(density shape, edge)` across all 36 cells has **mean -0.027 and is positive in 10 of 36 -
  below chance.** Net is negative in all 36 against a measured spread.
- **The distinction that decided it: N2 destroys the price path; A-prime destroys only the density's
  ALIGNMENT with the current price.** Beating the first and not the second means the edge was
  reversion from `x` alone. **Without A-prime this line reports a 7.2e-11 headline and admits a
  signal that is not there.**
- **What each of the three wrong measurements was.** D384 measured a statistic - total variation
  against a shuffle - that is a functional of the density **alone** and cannot see whether the
  density predicts returns; it also compared one density to the null's **mean density** with no null
  reference distribution, which **would have been reported as ~27 SE of structure at every
  half-life** and is a test that cannot fail. D385 measured a **flat object**: swing lows fire on 24%
  of ETF bars, so the density reproduced its own calibration. D387 measured a flat object on **half**
  its universe - absolute thresholds carried from ETFs to single names at 3-5x the volatility, so
  `move >2%` fires on a **median 28.3% of bars** - with **mismatched gates worth up to 126 bp**,
  larger than the entire claimed edge. **The principal had to ask "did the density have shape?" twice
  before it was looked at.**
- **D385's one emphatic signal was an artefact of the study's own tying rule**, caught by a
  prediction written in advance that lows and highs must behave the same. In a decade-long bull market
  **20-bar highs outnumber 20-bar lows 2.60x**, and because the centring half-life is tied to the
  event rate that becomes a **600-bar against a 218-bar centring EMA** - two types measured in
  different coordinates. The matched swing pair behaves identically. **Tying a centring half-life to
  an event rate makes rare and common event types mutually incomparable.**
- **A threshold in percent is not a threshold in rarity**: sigma units collapsed the cross-name rarity
  spread **4.37x to 1.37x**. And **`f-hat` is constant between events under plain decay**, because
  the scale factor cancels in the normalisation, so the dense accumulation is unnecessary and the
  recursion runs over the event rows - **39.0 ms to 1.6 ms, 24x, exact to 1.2e-14.**
- **The sign-sequence chain, D391 to D397, is retired and merged.** Eight candidates, **zero
  admitted, zero holdout reads.** `up_run_21` cleared all four nulls and **never cleared H1**, whose
  best-of-10 floor was never computed; the one cell that reached 1.00x cost coverage was **net
  -0.44**, found by searching 36 cells at a hold that was not the declared primary, whose own primary
  **failed the search floor by 22 SE.**
- The instruments outlive the chain: `scripts/lag_audit.py` (built because D391 shipped a look-ahead
  that cost 82% of its result), `data/d392_atlas.json` with `scripts/run_d392_base_rate_atlas.py`
  (**199 measured base-rate cells**, whose `lookup` **raises** outside the grid), **the exact
  permutation floor in `scripts/run_d395_chop.py`** (best-of-N for a cell picked from a grid, no
  independence assumption, 10,000 draws in 44 s, and it should replace normal-approximation floors
  programme-wide), and `scripts/ragged_sign_scores.py`, whose `sign_flips_21` is the most orthogonal
  score measured at max |rho| 0.025.
- **Six findings worth carrying:** base rates are large enough to look like signals (**price tercile
  +36.8 bp for a random long**); the edge lives where trading is dearest, measured three independent
  ways; a clairvoyant delisting filter would **lose** money; hit rate is immovable at **50.1-50.8%**;
  eleven observables all predict both tails equally; and no exit rule closes a cost gap - **126 cells,
  best recovered 2.53 bp of 50.88.**
- **D389 - the 0.44 correlation floor is ONE factor, and none of the four candidates explains it.**
  PC1's variance share reproduces the observed pairwise correlation to three decimals in both arms
  (**0.449 against 0.449; 0.478 against 0.476**), PC2 is an order of magnitude smaller and all 500
  books load with the same sign, **so a single correct identification would explain the whole thing.**
  Slot mechanics, equal-weighting, the eligibility floor and the shared hedge term all score
  **<= 0.052**, leaving **85% unattributed in the A-prime arm and 98.5% in the B arm** - and B is the
  arm that matters. **A-prime books share market exposure at 0.480; B books share the trading DAYS
  and their common factor is almost entirely not the market**, which points at the entry-condition
  distribution rather than at anything in the return-generating process.
- `scripts/probe_signfit_floor.py` - **a best-of-N permutation floor prices SELECTION and is blind to
  SIGN-FITTING.** Closed form and a 200,000-draw simulation, required to agree, no fixture involved.
  At k = 16: **best-of-16 |t| p95 is 2.95, a sign-fitted equal-weight composite is 4.23, and signs
  pre-declared in writing are 1.65.** **A composite of sixteen pure-noise signals clears the selection
  floor by +1.28.** The standard deviation is free of k, because the sqrt(k) multiplier and the 1/sqrt(k)
  of the mean cancel exactly. **Pre-declaring every sign in writing is worth a factor of about two in
  the hurdle for no computation at all.**

### Fixed
- **D392's atlas seed was never reproducible.** Each cell was seeded through `hash(side) % 97`, and
  `hash()` on a `str` is salted per interpreter process. Nothing is biased - every draw is uniform
  over the same eligible index either way - but **the 193 cells written before the fix cannot be
  reproduced bit-identically, and no record said so.** Fixed to an explicit code map; the 193 were
  not recomputed.
- **Printing the null's SPREAD reframes D391's table:** nine of its twelve cells sit above their p95
  floor, and **eleven of twelve sit inside the range 500 uniform draws actually produced.** It changes
  no verdict - D391 died on a same-pool control.
- **D280's own gloss on its independence result was backwards, and this record says so plainly.** The
  written position was that sixteen OHLC derivative terms carrying 13.50-15.76 effective inputs with
  no individual predictive power were "sixteen independent sources of noise, with no redundancy left
  to average away." **Orthogonality is the thing that helps**: at 13.5-15.8 effective inputs the
  multiplier is **3.7-4.0x**, while the nine price scores at 2.87 effective inputs buy only **1.69x**.
  **By this programme's own two measurements, the family it dismissed is the better combination
  candidate and the family it kept is the worse one.** The empirical part of D280 stands; the
  inference is withdrawn.

### Result (D365-D383 - the momentum buffer, the gate, and the programme's first holdout read, 2026-09-07/08)
- **D365 - the cost problem is a turnover problem.** The same twelve-month momentum signal behind a
  rank buffer nets **+2.59 bp/bar, Sharpe 0.417, +6.5%/yr**; refreshed daily it nets **-0.59, Sharpe
  -0.109, -1.5%/yr.** Turnover falls from 5.93% a day to 1.01%, so the toll falls sixfold while gross
  falls a tenth: **the jitter across the rank boundary was noise, not information.** A corollary - the
  next-open fill costs this book **1.8% of its gross** where it cost the event books 13.8 bp/bar, so
  **a slow book is nearly immune to the convention that destroyed the fast ones.** It clears every
  null, is not size and not beta (**103% of the top-decile drift survives a dollar-volume-matched
  hedge**), and **its two-factor intercept is +2.856 bp/bar at t = 1.74** - a Sharpe of 0.42 over
  twelve years cannot reach conventional significance. **Thirteen names are half the P&L of 709.**
- **D366 and D367 - a gate found by search clears its own rotation null, and half of what it buys is
  being out of the market rather than being out at the right times.** Gated and capped: **+8.09
  bp/bar, Sharpe 0.887, +20.4%/yr** against the ungated +2.59. The trigger's nulls are decisive - the
  rank rotation's *entire* distribution is negative. **But rotate the gate in time, preserving its
  on-share and its circular run structure exactly, and it still earns +4.10 bp/bar at the median.**
  The decomposition: ungated +1.85, a randomly timed gate +4.10, the real gate +8.09.
- **Six of the nine-condition gate were logically ENTAILED by the seventh.** An index at a 252-bar
  high is necessarily above its 200- and 50-day means, has positive 63- and 21-day returns, is not in
  a crash state and has broad participation - so six conditions change the result **to the last
  decimal**. **The nine-condition gate is one condition plus one more, and the whole difference
  between them is ten gate-open bars and about twenty trades.** One line of set algebra would have
  shown it before ninety constructions were searched.
- **An entry gate does not reduce exposure**, which is the correction D367 forced: the gate is shut on
  **90.8% of bars and the book is invested 91.6% of them**, holding 22.5 names on average, because the
  gate blocks entry only and positions run to the cap. **Every earlier description of this construction
  as flat most of the time was wrong.**
- **D368 and D369 - a 200-draw rotation null cannot resolve a 0.1 bp/bar margin, and three studies
  decided verdicts on exactly that.** The same gate under the same 200-draw design, two independent
  runs differing only in a dead parameter: **the null's p95 moved 0.40 bp/bar purely from redrawing**,
  while the verdicts these studies turned on were decided by margins of **0.05 to 0.56**. At 10,000
  draws the p95's own bootstrap SE falls from **0.301 to 0.020-0.056**, and the picture separates:
  the trigger clears its time rotation by **143-164 SE with 0 of 10,000 draws beating it**; the
  nine-condition gate by 32.9 SE; the one-condition gate by **3.2**; and the one-condition gate
  against a best-of-ten multiplicity control is **-1.0 SE - UNRESOLVED**, a margin and a standard
  error of the same size. **Precision cannot rescue a comparison whose effect equals its multiplicity
  penalty.** The UNRESOLVED category was created before the numbers were seen and caught exactly the
  case it was built for.
- **D371 - THE PROGRAMME'S FIRST HOLDOUT READ. Reads spent: 1. Both constructions failed four of six
  hurdles and are RETIRED.** Net went **+8.11 to +3.19 bp/bar**, Sharpe **0.887 to 0.344**,
  annualised **+20.4% to +8.0%**, names to half the P&L **12 of 515 to 2 of 255**. **The top-name
  shares above 100% are the finding: the top five contribute 142% of P&L, so everything outside them
  is net negative**, and outside the top ten the remainder loses 131% of what the book makes. One
  trade is **30% of all P&L**. The 1% trimmed mean per trade is **+63.9 against a 94.8 bp round
  trip**. **Both nulls fail, not just the gate**, against a prediction written twice that the trigger
  travelled and the overlay did not. **And pooling with the training set does not rescue it**: two
  universes sharing **zero names** over the same days still correlate **+0.545**, both being long US
  equity momentum.
- **D373, D376, D377 and D378 - the cohort was the strategy, and the dip timing is a small real
  effect rather than a rounding error.** Three independent methods put the cohort at **73-80%** of the
  winners'-dip long's +160.55 bp per trade: a same-day same-cohort swap centres at **+126.54**, a
  cohort-conditioned time rotation at **+116.91**, and subtracting the cohort's own equal-weight
  return collapses the mean to **+34.08 with the median at -30.74.** The increment over the
  cohort-conditioned rotation is **+15.98 bp per trade at +26.9 SE**, and **survives losing its largest
  trade at +9.8 SE.** The gain is **in the mean, not the median** - the same test on the median FAILS,
  +51.55 against a p95 of +64.00.
- **D372 - equal weight is the incumbent sizing and nothing has ever been run against it.** The kernel
  sizes `1/n_t` for its own leg, not `1/depth`, which is load-bearing on a dead-inclusive fixture, and
  **that is the only sizing decision this programme has ever made.** Pre-registration only; no cell
  scored. **An implicit default is not a decision, and the absence of a challenger is not evidence the
  incumbent won.**
- **D379 and D386 - the prop account, priced.** It is a down-and-out call and hurdle P had no objective
  function; **at zero edge a funded account is worth exactly its drawdown buffer**, and the whole
  question reduces to one leverage-invariant number, **Calmar >= 18.9 on open equity**. The best
  audited intraday CME programme in a 199-programme database is **1.07**.
- **D380 to D383 - no exit overlay beats not cutting, a stop is a late trigger, and two structure
  screens clear nothing.** The market-structure screen on the liquid universe finds nothing on the
  stable statistic and **the books are the market**; the 15-minute time-series screen clears nothing
  and **its ten passes are buy-and-hold.**

### Fixed
- **D370 - removing a book's best names tests nothing unless every null draw loses ITS OWN best
  names, and the verdict reverses when it does.** D367 removed the ten names the observed book earned
  most from and compared what remained against rotated gates that never produced those names. Made
  symmetric: **the asymmetric test read -0.311, -15.8 SE, FAILS at 10,000 draws; the symmetric one
  reads +0.602, +10.3 SE, CLEARS at 2,000.** Two separate defects, both measured: **the hedge was
  shorting names the book could not trade, worth +0.300 bp/bar** (the ranking was rebuilt on the
  reduced universe and the dollar-volume hedge was left spanning the full one), and **the null was
  spared the penalty the observed book paid** - once each draw loses its own ten, the null's p95 falls
  from **+4.230 to +3.617** and its median from **+1.562 to +0.679**. The sets genuinely differ,
  overlapping on a median of 5 of 10, so the earlier test was not absurd, merely unfair. **Section
  47's claim that "the trigger survives and the overlay does not" is RETRACTED**; the gate's premium
  survives at **83% retained, not the 57% reported.** And: **PRECISION CANNOT DETECT BIAS** - D369 ran
  this exact test at 10,000 draws and returned a confident, well-resolved, tightly-bounded, wrong
  answer at -15.8 standard errors.
- **D374 - D373's breadth hurdle was unreachable and it failed the most diversified book in its own
  null.** The bar was the bar's fault; H4 is retired.
- **The `docs/FINDINGS.md` section 52 heading over-claimed and the principal called it.** Correlation
  does not bound a difference in means: rho is computed after removing each series' mean and dividing
  by its own volatility, so **rho = +0.923 between two cohort books is a statement about shape, not
  level, and measures 80% of nothing.** The "~80%" rests on two measurements, not three. What the
  correlation does establish is narrower and still useful: **cohort books cannot diversify one
  another**, because a portfolio of two carries almost the risk of one.
- **The rule's original wording - "the selector is a rounding error on a factor exposure" - is
  withdrawn as too strong.** A real effect that is small relative to cost is **a small real effect**,
  and the two must not be written as the same thing.

### Result (D345-D364 - the event lens, the controls, and what an auction fill costs, 2026-09-06/07)
- **D345 - the event book failed as calibrated and taught three things the slot book could not.** The
  threshold was calibrated on **exposure** and never on return, landed at 11 / 89, fired nine times a
  year and could not be separated from a per-name time rotation of its own signal dates. **The target
  exit belongs to the always-invested construction**: +52.6 a trade under the target, **+237.6 under
  signal invalidation, +209.0 under a bare cap** - so D295's "stops, displacement, idle conditions,
  the ladder: dead" is a fact about a book that refills behind every exit, and is amended. **A
  threshold entry cannot be calibrated to a slot book's exposure.** And **a capital series for an
  unbalanced book must carry the hedge its ledger carries** - the raw signed sum hid a market drag of
  roughly 0.8 to 1.3 bp/bar.
- **The event kernel is proven bit-identical to the slot simulator's uncapped lens on 4,021 trades**:
  the slot book's invariant lens IS an event book whose signal is "ranked in the top two this bar".
- **D347 to D353 - the controls, and the one that was broken.** Four long signals, then five short
  ones, each against its own names at random times, a same-day same-bucket name, and random direction.
  **Every short signal beats its own names at random times and still loses, because the names it
  shorts rise.** No short event at any extreme beats random direction: the means are **-11.5 to +25.6
  bp a trade** before cost. The one long trigger that survives everything is **a one-week reversal
  entering the bottom decile: +43.4 bp a trade on 27,316 trades, above A-prime's p95 of +28.6 at 200
  draws, above a same-day same-bucket name at +35.8, above random direction at +15.2, mean equal to
  median, symmetric trim +35.3, 27 names to half the P&L, ten of fourteen years, positive in every
  down-year.** **-18.6 net under the published spread, +17.9 under the per-bar one.**
- **A slot cap small against the event count samples the signal's extreme, not the signal.** At K=2 a
  two-slot cap on 72,677 events admits **161 entries in sixteen years, most extreme first** - the
  deepest crashes each day a slot is free, which the interaction table says do worst - and the book
  loses. At K=4 it nets +3.5 with Sharpe 0.31. **Read every capped event book against its skipped
  share (99.8% here).**
- **D354 - the ranking chooses no hedge.** Hedging the trigger with a basket of the three
  highest-ranked names costs the pair **107-181 bp per pair**, and the random-partner null is centred
  within a basis point of the extreme basket at both K. **The pair is more volatile than a market
  hedge - 285 against 232 bp/bar - because three names are not a market.**
- **D355 - on a refilled slot book the target fires first.** The signal-invalidation exit lengthens
  the hold (median crossing at 27 bars against a target median of 15), halves the entries, and holds
  through the part of the path the target would have banked: **rsi k=40 goes +5.14 to +0.54 bp/bar,
  hist_L +12.42 to +10.34, and both together -7.75.**
- **D356 - the two candidate books blend to a higher Sharpe than either, and the arithmetic is
  exact.** A 50/50 capital blend on a gross-series correlation of **+0.21**: **net Sharpe 0.442
  against 0.268 and 0.401**, above 100 of 100 paired time rotations and 24 of 24 paired rank
  rotations. **The two books hold the same name on the same side on 46% of bars and still correlate
  at 0.21 - the diversification is in timing, not in names.** The pre-registered prediction that the
  blend would beat the arithmetic was **an identity, and is recorded as an error.**
- **D358 - a cross-sectional trigger on a wide universe is always on.** A fresh entry into the bottom
  2% of ~1,000 eligible names fires **5.2 times a bar**, so a 40-bar hold is 120 open positions on the
  average bar and never zero; to be flat half the time the product would have to be 0.7, which is five
  entries a year. **Rarity in the cross-section says which names; it cannot say when.** And **about
  70% of a long-only sleeve's gross is the floored market.**
- **D359 to D362 - the short side has no drifting pool, and one cell survives every control.** The
  bottom momentum decile **drifts UP on this universe (+0.64 bp/bar)**, because the floor admits only
  names above $5 with a passing dollar-volume window and the losers whose continued fall the
  literature measures leave the universe as they fall. A negative trailing market return **forecasts a
  rebound, not a fall** - the loser cohort earns **+96.2 bp** over the next twenty bars with the gate
  on against -15.9 with it off. **The one cell above every control is the gap-up fade with the market
  below its 200-day mean: +42.3 gross a trade on 3,977 trades (t 2.5) against a rotation p95 of +36.0,
  A-prime +25.8, B +37.7, C +25.2, net +3.3 at the per-bar line and -47.2 at the published one.** It
  is the third cell of four and the primary failed, and **the p95 margins are 5 to 6 bp.**
- **D362 - a filter found by screening a ledger needs two nulls, not one.** Removing two screened
  conditions lifts the fade to **+61.7 gross (t 3.2)**, above 200 random removals of the same count
  (p95 +55.7) **and** above 200 rotations of each name's hit flags (p95 +54.3). Removing all five
  reaches +83.6 and **fails the second null**, because high beta, a thin volume node and
  overnight-driven volatility describe *names*. **And a filter on a market-level variable is a gate**:
  with the calm-market condition on, the filtered cell falls **inside the gate rotation's p95.**
- **D363 and D364 - the remaining cost question is the auction, and the premise that it was free is
  withdrawn.** Charging each trade its own spread at its own bars costs the ledger **108 bp under the
  published convention against the median's 89**, so the net is **-49 / -66, not -30 / +20**. If both
  sides cross the fade loses 46 to 66 a trade; if one side does, about zero; if neither does, **+55
  before impact**. Then the participation measurement: **the opening minute is a median 1.44% of the
  day and the closing minute 7.85%**, so at $25k a position the median participation is **2.494% of
  the minute the entry fill happens in, against 0.024% of the whole day - a 69x understatement** - and
  **the widest spread quintile, the one carrying the whole edge, is the thinnest at 4.20%.** Section
  43's "liquidity is not the constraint" clause is withdrawn; the three bounds stand. **Measure
  participation against the bar the fill happens in, not the day.**

### Fixed
- **D351 - D347's control A was trading the excluded tail, and section 28's headline is withdrawn.**
  The rotation rolled each name's events within **every priced bar** while the observed events sat on
  the floored, eligible mask, and the kernel traded the rotated ones because it checked finiteness and
  not eligibility. Those bars earn **+226 to +318 bp per forty bars** on the names these signals
  touch, and **8-13% of every signal's rotated events landed there.** Confined to the floor: three of
  four long signals go from **below** their own names at random times to **above** them - hist_L
  **+60.4 against a p50 that falls from +70.8 to +23.9**, rev_21 +46.5 against +59.6 falling to +12.9
  - and **the cohort premium is +7 to +24 over a universe base rate of +1.7, not +45 to +71.**
  Reproduced to 0.0 from the studies' own seeds by their own code path. **Every null now asserts that
  its events lie in the same eligibility mask the observed events satisfy**, and reports the share
  that would not have. **A null centred far from the base rate is the first thing to explain: suspect
  the null before writing the mechanism.** The mechanism this document, `docs/STACK.md` and a memory
  rule carried for three records was wrong, and the check was one line.
- **`np.digitize` sends NaN to the last bin.** 961,819 eligible name-bars with no rsi percentile -
  nearly all off the warm base - were counted in the top bucket's base rate and drawn into its control
  pool. Confined to defined ranks the top bucket earns **+11 bp long, not -31.** D347's events sat in
  the bottom buckets so its verdict is untouched. **Mask NaNs before `digitize`.**
- **D341's floor-share assertion had a fallback that defaulted to the value under test**, found by a
  second runner writing the same assertion. **An assertion with a default is an assertion that cannot
  fail.** Raise on a missing key.
- **A pre-registered test that was VACUOUS BY CONSTRUCTION.** A continuation arm declared as a second
  look at a symmetric signed trade is the exact arithmetic negative of the reversion arm -
  `max |revert + continue| = 0.000e+00` across 10,025 cells - so its abandon condition could never
  fire. **Check that a declared alternative is not the arithmetic negative of the primary before
  pre-registering it.**

### Result (D329-D344 - the deal filter, the fill convention, the floor, and a declared candidate, 2026-09-05/06)
- **D342 - `rsi` symmetric at k=20 is the personal track's first DECLARED CANDIDATE, at three and a
  half basis points a bar.** Under the deal filter, the dividend bound, the published spread, the
  universe floor, a next-open fill and stressed borrow: **+3.52 bp/bar, +3.32 after borrow, Sharpe
  0.18**, above all 24 rotations of its liquid gate on gross (+14.72 against a null maximum of
  +14.64) and on net Sharpe (+0.181 against +0.149). Fourteen names to half the P&L, a 5.5% top trade
  that is a real eighteen-bar decline in a liquid biotech, no overnight-gap premium on either leg,
  eight of fourteen years positive. **Every trade loses money uncapped** - the invariant lens is -4.8
  bp a trade with both legs negative - **so the book earns entirely through the slot cap's selection
  of the two most extreme names per side.** The left tail does the work: **skew -1.69, bottom 1% of
  trades -54% of P&L against +40% for the top, a 0.51 payoff carried by a 72% win rate.**
- **D344 - the hold is a cost lever, and under a target exit k is a cap, not a hold.** At k=40 the
  candidate pays **7.6 bp/bar in cost against 11.3 at k=20**, gives up 1.7 of gross, and nets **+5.14
  bp/bar, Sharpe 0.27**, with drawdown down a quarter and **the ordering above all 24 rotations on
  every statistic - the only cell in the programme to manage that.** k=10 is -5.89 and inside its
  null. **Both mechanism predictions were wrong for one reason**: turnover was predicted to scale as
  1/k and came in at 1.55 and 1.44, and gross **peaks** at k=20, because k is a cap under a target
  exit, most positions close before it, and a ten-bar cap truncates the reversion before it completes.
  **The two lenses disagree in direction on k**: per trade k=40 is worse (-11.8 against -3.7), per bar
  it is better.
- **D346 - the corrections compressed the signal table rather than shifting it.** Twenty-nine of 46
  long legs **improved** against the pre-correction table (median +7.9 bp a trade) while the best legs
  fell hardest - **rsi +64 to -11, id_mean +35 to -67, retrace_leg +46 to -23** - and the long-leg
  95th percentile fell from **+42 to -6** while the median rose from -58 to -47. **A ranking of
  signals measured on the unfloored, same-close universe was mostly a ranking of exposure to one
  tail**, and D290's tier list was drawn on it. **And the incumbent's primary comes back at the longer
  hold**: hist_L at k=40 is **+12.42 bp/bar with a Sharpe of 0.40**, holding $23 names instead of $11,
  two and a half times the declared candidate. **Re-run the whole table when the conventions change,
  not the cells you were looking at** - four cells had been re-measured and they happened to be four
  that fell.
- **D338 - the best book in the programme is five names, and four of them could not have been
  bought.** `retrace_leg` orders its gate genuinely (**+32.4 bp/bar gross against a rank-rotation null
  whose maximum in 200 draws is +15.2**) and what it orders the gate toward is the illiquid tail.
  **Five names of 673 are half the P&L. The top trade is VSA, long, 2025-01-31, one bar, +330%, 15.9%
  of the ledger** - a real move with no dividend, in a stock trading at about **$0.18** (two later
  reverse splits inflate the adjusted close to $90.55), on **2,738 shares the day before**, at the 4th
  percentile of the universe by dollar volume. Four of the five largest trades are sub-$2 names in the
  bottom 7% by dollar volume, bought at the close on the day before a +68% to +330% gap. **A cell in
  another study's table is not a book.**
- **D339 - the illiquid tail was every book's top trade and none of their edge, and the universe now
  has a floor.** The census: **25 of 47 books take more than half their P&L below the floor, 35 of 47
  top trades fail it, and nine names supply the top trade of 30 books.** The floor fails 29.3% of live
  name-bars and the sub-$5 share of the universe went from 3% in 2010 to 13% in 2025. **The tail the
  floor removes was not edge**: three books improve and the fourth is unchanged on net. **Replace
  beats starve** - filling the vacated slot with the next liquid name is worth 3-6 bp/bar over a
  filter's hole - **so from D339 on the floor is the declared universe.** The floor is on the
  **as-traded** close, because a floor on the adjusted close would look through future reverse splits.
- **D343 - the floor leaked at re-listings, and the leak cost money.** One name's first day back after
  an eight-month halt was **4.4% of the book**: its trailing dollar volume had fewer than 21
  observations and the rule that a missing estimate never excludes passed it in. The clause now
  requires its 21 observations (**30.9% of live name-bars fail**), and **the 35 trades the hole had
  admitted across three books lost 134 bp a trade on net** - the one relisting pop was outweighed by
  names re-entering the tape against the book. **A prediction about a symbol is not a prediction about
  a trade**: the fixture stitches two companies under one ticker, and "this name is not in the ledger"
  was false for eight trades from 2022 the clause was never meant to touch.
- **D335 and D337 - the short side is a cost failure, and neither sizing nor borrow changes the
  verdict.** Of 46 dimensionless signals symmetric at depth 2, **one short leg in forty-six nets above
  zero** (+4.9 bp against a p95 of -13.3 and a p50 of -132.9). Under the old per-bar median six of the
  top ten shorts were positive. **Holding the name in constant shares is worth +45.85 bp a trade on
  hist_L's short leg** (the identity compound = summed - premium holds to 2e-14) **and the leg still
  nets -53 / -135.** At declared stress borrow rates the incumbent pays **0.25 bp/bar** against a
  convention gap of 20 on the same book. **And the rebalancing premium is a property of what the
  target exit SELECTS, not of how long the book holds** - the fixed 20-bar hold's premium is -33.8
  against the target exit's -45.8 at 11 bars. D328/D329 wrote it as a duration effect; **withdrawn.**
- **D329, D330 and D331 - the fixture contains pinned takeover targets, and a range-based spread
  estimator prices them as free.** `skew_63` on 63 observations is a single-jump detector: **29% of
  its short leg's trades are in a name that leaves the tape within 60 bars**, against 1% for the
  universe, and **96% of those end within +/-5% of the entry price with a median daily range of
  0.28%.** Those are cash takeovers. **Corwin-Schultz estimates the spread from the daily range, and a
  pinned stock has none** - 6.2 bp on the dying names against 9.0 on the survivors - **which is one
  cause for D326's unexplained 4.53x cost coverage, D327/D328's "cheapest names in the study" and
  D329's three zero-spread cells.** Mapped across all 46 signals: short legs are a median 1.5% pinned
  and `skew_63` is **21%**; **every volatility score's LONG leg is 24-35% pinned**, and their
  surviving names carry a held half-spread of exactly 0.0, because **the lowest-volatility name on the
  tape is a stock pinned at a deal price.** SEC EDGAR settled it: target-specific deal forms find
  **84% of the pinned trades with a median lead of 28 bars** and exclude only 2.4% of the universe,
  and with the deals removed **`skew_63`'s short leg nets -24 to -30 per trade at the old cost basis
  and -61 to -65 at the published one.** Its **+16.6 net, its 7.7 bp half-spread, its first-of-44 and
  its 4.53x coverage were the takeover targets, entirely. Retired as a short signal.** A name's death
  date is not a deal label - use the filings.
- **D329 - a signal can own ONE leg.** `hist_L` long with `skew_63` short beats both parents on both
  lenses at k=20 and k=40 (**+63.26 per trade against -0.89 and +44.83; Sharpe +0.434 against -0.082
  and +0.421**) and loses to `skew_63` at k=10, so every "every k" form failed on one cell and the
  record says so rather than re-cutting the claim. **The short leg is SPECIFIC and the long leg is
  not**: `skew_63` is first of 44 costable partners on both lenses, while `hist_L` is fifth per trade
  and **fourteenth as a book** among 45.

### Fixed
- **D332 - the spread estimator has a published convention and the programme was not using it.** The
  single two-day Corwin-Schultz estimate is **clamped to exactly zero on 43.2% of all live
  name-bars**, uniformly across price and uncorrelated bar to bar - the authors' own convention
  applied to an estimate that is negative nearly half the time. **The zeros are noise, not a property
  of any name**, and every runner since D318 charged the *median at entry* of that coin flip. **Corwin
  and Schultz never use the single estimate: they average the clamped daily estimates over a month**,
  which this codebase already computes. Universe median **31.7 bp a side against 14.2**, and across 92
  measured legs the published convention charges **2.03x the programme's at the median** (p10 1.40x,
  p90 3.31x). Repriced with one array swapped and every ledger bit-identical: **the incumbent at
  N=2/target k=5 goes +14.57 to -5.16 bp/bar**, N=19 **-15.02 to -37.09**, `retrace_leg` k=20 **+20.91
  to +16.06**, `skew_63` **+12.60 to +4.97**, the leg-wise book per trade **+63.26 to +35.99**. **The
  incumbent's headline was a cost-convention artefact.** Every relative finding survives and every
  level falls 8 to 20 bp/bar. **Which convention is TRUE is not decided and cannot be from OHLC
  alone**, so until a quoted-spread pull settles it every net number in this programme is a pair.
  **A clamp at zero on a noisy estimate turns a median into a coin flip.**
- **D333 - the fixture carried thirty fabricated return days.** `load_ragged` applied every event-file
  dividend as `log1p(amount / close)` with no bound, and the events file records spin-off
  consideration, merger consideration, splits and returns of value as cash dividends with the price
  left at its post-transaction level. **Thirty of them, 0.08% of 35,713 dividends, became return days
  of +9% to +356%**: one name closed 10.94 to 11.04 and was paid **+356%**; another rose 39.5% on the
  tape and was paid 49% more. The pre-registered rule - a dividend of at least 10% of the close is
  applied only if the price fell at least half of what the distribution implies - **drops the thirty,
  keeps every real distribution, and names one borderline case.** Same trades, thirty bars corrected:
  **the incumbent goes +14.57 to +7.15 bp/bar - half its book** - the published-convention line
  **-5.16 to -12.68**, the concentration premium **+29.59 to +22.93**, hist_L's long leg per trade
  **+97.0 to +63.9**, and four signals lose 5 bp/bar each. **The incumbent's headline since D318 was
  half fabricated.**
- **And the rule this leaves is about reporting, not data.** D322's four-group report said "six names
  of 718 make half the P&L" and "top 1% of trades = 96.3% of P&L", and reporting rule 3 was followed.
  **Nobody asked which six, and one of them was the +356% day. Fifteen studies then ran on the
  unbounded panel.** A concentration report is not finished until the top trade is named, its bar
  printed - open, high, low, close, volume, return - and any event on that bar shown beside it.
- **A derived-array cache must be keyed on the panel builder, or a data fix reproduces the old numbers
  silently.** `d290_build_cache` was not, and D334 rebuilt it: **48 of 51 scores bit-identical,
  `signed_vol` moved on 86 cells, `ivol_21` on 12.7% of all cells and `beta_63` on 30.3%** - thirty
  fabricated days reached every name through the cross-sectional market return.
- **D340 - the fill convention credited the overnight gap to every entry, and it was worth more than
  the spread.** Every D300-family book computed its signal at the close of t-1 and opened the position
  earning `close[t-1] -> close[t]` - a fill at the signal's own close, which no book can do. With a
  next-open fill: **`retrace_leg` goes +18.93 to +5.14 bp/bar net, -73%**, gross +32.37 to +18.06, the
  invariant per trade **+10.02 to -18.27**, and its long leg per trade **+46.23 to -12.03**. **The gap
  credited per entry was +44.8 bp on the long leg and +27.2 on the short - larger than the published
  half-spread on either leg**, because names that break below their swing low gap UP at the next open
  and names above their swing high gap DOWN. **A structure-breakdown signal at the close is partly a
  forecast of the next open**, and the convention booked the forecast as if it were tradeable. **It is
  not only the entry-bar mark**: only 378 of 1,256 trades recur across fills, because the target reads
  the accumulated excess and the books walk apart. **Forty studies inherited the convention from D295
  without naming it as a choice**, so every net number before D340 is a same-close-fill number.
- **And the family's rotation null has 24 distinct values.** The shift runs 1 to 24, so 200 draws are
  24 books and p95 is the maximum whenever the top value recurs. **"p = 0.005" means "above all 24"
  and its floor is 1/25.**
- **D341 - corrections that share a cause do not add, and the load-bearing prediction was wrong in the
  programme's favour.** `docs/STACK.md` predicted the floor and the fill together would take
  `retrace_leg` to zero or below. **Together they take it to +2.68 bp/bar, +2.46 after borrow - the
  two corrections overlap by 13.33 bp/bar**, because the overnight gap the fill credited was
  three-quarters in the sub-$5, bottom-decile-volume names the floor removes: the long-leg premium per
  entry falls from **+44.8 to +11.2** once the floor is on, while the short leg's does not (+27.2 to
  +29.2). **Predict the interaction or predict nothing; a sum of marginal effects is a prediction that
  the mechanisms are disjoint.**
- **`rsi` is the first book here to GAIN from honest scoring**, at +3.52 under both conventions with no
  gap premium on either leg once floored; its unfloored book was negative.

### Result (D300-D328 - book width, the corner, and what the rankings were made of, 2026-09-03/05)
- **D300 - the book crosses breakeven by getting smaller.** Concentration is worth **+32 bp/bar
  between N=2 and N=19** and the premium is basis-immune. Every book since runs `sel = rank < N_SLOTS`,
  which is the construction FINDINGS section 10 is about.
- **D303 to D306 - the market-referenced target is adopted and the band is not**, only one
  self-replacing arm keeps the book full, and the target survives concentration while the cap is a
  filter. **Two rules agreeing on 73% of the decisions they both face end up sharing only 56% of their
  positions**, because one divergent exit frees a slot that refills differently and the paths separate
  from there.
- **D304 - widening the pool ALONE is inert, and the earlier claim that it was "a one-line change" was
  wrong.** A 19-slot book drawing from a 25-name gate is **bit-identical** to one drawing from the top
  19 - same 30,242 trades, same +24.2 bp/trade, same +12.00 bp/bar - because refill only runs when a
  slot is free and a drifted-out name **holds its slot**. **The bench is unreachable unless something
  evicts the drifted-out holders**: pool width and eviction are one change, not two.
- **D311 to D313 - forecast the book's risk from the UNIVERSE, never from the book.** Targeting the
  book's volatility from its own trailing 63-bar standard deviation correlates **-0.016** with the next
  63 bars' realised vol at the width that earns; **the cross-sectional dispersion of the whole live
  universe correlates +0.352 at the same width**, and **dispersion over the ~969 names OUTSIDE the
  gate (+0.355) beats the whole universe and beats the 50 gate names outright (+0.242).** The gate is
  chosen on the signal, so its dispersion is contaminated by the selection. **A conditioner whose own
  level does not persist cannot forecast anything** - own lag-63 rho **-0.016** against universe
  dispersion **+0.616** - **and that costs one line to check before a study is designed.** Two further
  traps priced in the same record: **vol targeting against a full-sample-sd target is structurally a
  leverage rule** (measured ratios 1.15-1.27, realised mean exposure **1.34-1.53**, so a third of such
  an arm is leverage), and **breadth is a priced risk lever** - widening cuts volatility and gross
  roughly one for one.
- **D314 and D315 - the width optimum is a corner, and that is why every variable-N study closed.**
  Fitted to sixteen widths: `vol(N)^2 = 2,396 + 1,201,745/N` at R^2 0.9994, and the implied average
  pairwise correlation is **rho = 0.0020, statistically zero**, so `vol(N) = sigma/sqrt(N)` almost
  exactly and Sharpe collapses to one term. **`net(N) = 5.96 - 2.38 ln N`: the edge dilutes 1.58x
  faster than the cost falls**, which is why net is monotone down in width everywhere. **A rule that
  varies N can only move AWAY from a corner**, which retro-explains five closed studies. **Fit the
  surface before searching it** - three regressions on numbers already in `data/`.
- **D320 and D321 - reach a tilt through a well-measured variable, not through the noisy one.** A
  direct spread filter calibrated to reach the SAME held half-spread as a dollar-volume filter loses
  at **all nineteen thresholds, by +0.060 to +0.582 of net Sharpe** - identical tilt, opposite outcome
  - because the per-name Corwin-Schultz half-spread is noisy and filtering on it discards good names
  that merely MEASURED wide. **How well an input is measured decides more than what the input is.**
  The counter-example travels with it: substituting a better-forecasting universe predictor into the
  volatility overlay made that rule **worse at every width**, because it needed a scale and not a
  forecast.
- **A sweep is one hypothesis, not N.** The nineteen threshold books correlate at a median of
  **0.892**, the first eigenvalue explains **90%** of the variance, and the effective independent count
  is **3.0 to 4.7**. The multiple-testing bar for the smallest p moves from 0.00526 to 0.020-0.033 and
  the cell clears. **Correct a sweep for its effective width, not its nominal one - and say which you
  used.**
- **D328 - a cross-sectional ranking on a quantity that carries units ranks those units.** `macd_hist`
  is computed on **raw closes** and is denominated in **dollars**, so a $3,000 stock's histogram is
  ~100x a $30 stock's for the same percentage move. Median price by rank bucket runs
  **$2,706 / $798 / $438 / $22 / $477 / $1,002 / $3,020** - **both tails are the expensive names and
  the middle is the cheap ones** - and the forward edge follows at **-557 bp at one extreme and -650 at
  the other, t -12.58 and -4.61.** **Long minus short leaves +18 bp.** The audit of all 51 candidate
  scores: **three carry dollars by accident** and two by design.
- **Passing the dimensional test is not enough.** `hist_L` is scale-free and its extremes are still
  **$8-10 names at 4x its own middle's spread** and 3.3x the universe median. **And the natural
  statistic points backwards**: `rho(corr(rank, price), net per trade) = +0.800` while
  `rho(max log deviation, net per trade) = -1.000` - **the correlation test passes both losing books
  and fails both winning ones**, because the fatal shape is **symmetric** and a correlation cannot see
  a U. **A symmetric price relation pays nothing and costs double**: `macd_hist`'s legs carry the same
  -600 bp price penalty which cancels in the spread, while **the spread it must pay sums to 146 bp of
  round trip against +18 bp of return.** The statistic derived from the mechanism is the
  **common-mode half-spread against the live universe median**, where a threshold near 2x separates
  the two losing books from the three winners.
- **Two P&L conventions, and the difference between them is a finding.** Every book runner from D295
  to D326 earns the **sum** of one-bar simple returns, which is equal-weight rebalanced daily;
  buy-and-hold with constant shares earns the **compound**. **The difference is the rebalancing
  premium, and on `hist_L`'s $8-10 names it is the size of the whole effect: +78 on the long leg and
  -85 on the short, 163 bp over 20 bars from position sizing alone.** So **`hist_L`'s short leg loses
  under the book's convention because it is short the rebalancing premium on bouncy names** - a sizing
  artefact, not a signal failure, and D283's "symmetry fails BY SIGN" has its mechanism. **And the
  rebalancing is uncosted in every one of those runners.**
- **D323 to D327 - the ranking inverts with width, the fragility is structural, and no rank profile is
  monotone.** The incumbent is the least fragile of the four candidates; synergy in composites is real
  and nothing wins on the declared condition; **the composite premium was the cap and the pair effect
  was not**; and one profile is outright inverted while the buckets are too coarse to see it.

### Fixed
- **D299's cost column was overstated, not understated** - the correction is recorded in its own
  record rather than folded into the result.
- **D307's lottery verdict came from a one-sided test.** Four cells were called lottery books on a
  trim that dropped only winners; **the symmetric trim is +24 to +52 bp, and at N=19 the losing tail
  was larger, -181% against +161%.** Dropping only winners is a flag, not a verdict.
- **D308's ceiling was less than noise, and N=2 is not always interior.**
- **D315 Stage A withdrew D314's closed form.** `N* = 1.66` **IS WITHDRAWN**: the seven widths below
  the grid floor were run, gross turns down at `N_eff` 1.15 and net at 1.45, so **the log-linear net
  curve does not extend below N = 2 and 1.66 was an invalid extrapolation.** Refitting on the full
  range makes the gross fit worse (**R^2 0.9774 to 0.9143**) for an equally meaningless 4.75. **The
  corner itself survives and is now MEASURED rather than extrapolated**: net Sharpe peaks at `N_eff` =
  2.00 on a surface sampled from 1.00 to 25.00, and no width below 2 is distinguishable from 2
  (**largest paired t = 0.12, win rate 47.8%**). The diversification law was verified at the boundary -
  at `N_eff` = 1 measured vol is **1,089 bp against an implied 1,095.** **A fitted form is evidence
  only inside its fitted range**, and the optimum sat outside it.
- **D317 - the D310 family was charged the wrong spread**, and D318 re-costed the stack, which
  dissolved D306's net/Sharpe conflict.
- **D320 - the tilt filters that "worked" were width in disguise.**

### Result (D285-D299 - the factor-neutral book, the mine, and the confluence, 2026-09-02/03)
- **D285 - the factor-neutral book, and it is the last structurally different idea on the personal
  track.** Eight studies had returned no survivors, and the arithmetic is why: **every construction
  tested was net directional in a market with positive drift, paying `-mu - sigma^2` before a dollar
  of cost** - D279's top-25 short at **-0.432 Sharpe gross**, D282's short-everything-overnight at
  **-21.92% CAGR**. These are not cost failures; they lose at zero fees. **A factor-neutral book
  removes the `-mu` term by construction.** The record says first that **it is not a novel idea** - it
  is cross-sectional short-term reversal, documented since 1990 and documented as concentrated in
  small, illiquid, low-priced names and largely consumed by the bid-ask spread. **D251's ETF closure
  does not transfer**, because that failed at 2.2 effective instruments across 57 ETFs and this
  fixture carries 1,573 names at **10.06 effective independent instruments over a held book.**
- **D285's cost measurement is the one every later record inherits: the held names' Corwin-Schultz
  spread is 33.8 bp a side, against a guessed 15 bp/side bar it missed by 0.65.** Estimate the spread
  of the names HELD rather than trusting a fee assumption.
- **D286 - the exit that keys on the signal, and it came from an objection rather than from the
  data.** D285's exit holds while the name stays in the top or bottom N, so **with N = 10 drawn from
  ~1,570 qualifying names a position exits when ten OTHER names become more extreme. The held name's
  own score is not consulted: it is evicted by strangers.** That is why the persistence table looks
  the way it does, and **the question is not how long to hold but whether exiting for the right reason
  is worth anything.** The objection also refuted the fix that was about to be pre-registered: a longer
  hold collects a *falling* per-bar edge (**10.70 to 6.96 bp**) while adding exposure, and raises
  breakeven only by amortising one round trip. **Cost-cutting is not edge-sharpening**, and it became a
  standing note in `CLAUDE.md`.
- **D288 - the mine is closed, and the holdout was never read.** **Zero of 31 pre-registered candidates
  cleared the best-of-31 floor.** The stop condition written before the run applies as written: no
  thirty-second candidate, no second cut of the axes, no re-run at a different N. **The screen
  validated exactly first** - `hist_L` came back at +25.6 / +56.3 / +28.3 bp at N = 10 / 25 / 50, peak
  horizons 3 / 25 / 16, best t **+2.86**, reproducing D286's published band and its published best-t
  to the decimal from an independent runner, with the calibration delta recorded as **0.0 bp against a
  15 bp tolerance**. A calibration miss would have made the run void rather than negative. **The
  load-bearing prediction - that every candidate would show both legs positive - is dead: 16 cells
  carry a negative short leg at k >= 5.**
- **D289 - the promotion pipeline, and R14 with it.** The whole promotion tree is pre-registered
  before stage 1 and looks multiply across stages. See the standing-rule block below for its seven
  amendments.
- **D290 - the stage-1 re-run, 51 candidate scores, and four things the pre-registration could not have
  asked.** `hist_L` reproduces D286 to a delta of **0.002**; the name split shrinks the top candidate
  by 31% against a predicted 40% - **it generalises better than predicted**; **24 of 51 survive all
  three nulls**; and **the tail tax is falsified as the mechanism** - five risk-selecting scores show
  tail z >= rotation z, the *opposite* of D283/D284, which was the programme's standing explanation for
  why risk-selecting signals appear to work.
- **D291 - the gate closes, and the veto was never actually tested.** **0 of 254 evaluated cells clear
  both paired t >= 2 and the best-of-272 floor of +3.67**, with the best cell at t +2.92. And the
  second result matters more: **87 of those cells - the entire veto arm - should never have been
  scored, because the control pre-registered for them is not turnover-matched.** That is D279's error,
  written in `CLAUDE.md` in as many words, and designed into the pre-registration anyway. **A random
  subset is never a control for a persistent selector** - it re-draws each bar, so it churns: **2.4x
  the entries, up to 7x, which voided 87 cells. Randomise the partner, not the membership.**
- **D292 - four cells clear the bar, and the bar was too low.** The arm's central tendency is negative
  again - `t_min` mean **-0.26**, median -0.31, **only 32% of live cells positive**, so a second filter
  on average makes the book worse. **Four cells cleared the pre-registered promotion floor, so the
  load-bearing prediction is falsified as written - and the bar does not require the effect to be
  distinguishable from zero**, BH-FDR keeps none at q = 0.10 or 0.20, and **12 cells were VOID by the
  pre-committed turnover audit.** The defects are disclosed rather than used quietly to erase a
  pre-registered pass.
- **D293 - the confluence wins the symmetric comparison, and the load-bearing prediction is
  falsified.** On the spread construction at N=25, k=5: **+61.91 bp at t +3.80 against `hist_L` alone
  at +52.52 and t +2.86**, and the confluence is further from its nulls on every one - min z **+2.58
  against +1.60**, cross-validation +1.35 against +0.98, open-entry +2.96 against +2.30.
- **D295 to D299 - stage 2 closes: nothing clears, the anti-pattern won, and the book was pinned.**
  The exit family - stops, displacement, idle conditions, the ladder - is dead **on a book that
  refills behind every exit** (amended by D345 for the event lens). Criterion-matched nulls show the
  k=5 cell licenses only its own t; combining the structurally different exits adds a little and
  **half the factorial was one book**; and the ladder's null suite decomposes it into a family that
  acted with nothing there. **D295's asymmetric arm was three copies of reversion**, recorded as a
  correction.

### Changed (docs/RULES.md - the standing-rule sequence, 2026-08-29 to 2026-09-13)
*No existing document narrates this, so it is derived from `git log` on `docs/RULES.md` and
`docs/decisions/D289-the-promotion-pipeline.md`.*
- **R7 gains an ADDITION, 2026-09-08 - the control is a NULL, not a POLICY, and the verdict depends on
  an objective the STRATEGY declares.** Three clauses: report the overlay against the **un-overlaid
  baseline** as well as the control; the control's difficulty is inherited from the rule's trade
  selection, so a control-only verdict is not enough; and **when the rule's trade selection is knowable
  only ex post - which paths *will* breach a threshold - the control's level is unattainable and must
  not be read as a policy.** An overlay that cuts drawdown by more than it cuts mean wins on one
  criterion and loses on another, and the strategy says which.
- **R11 - hurdle P for the prop-firm route, created 2026-08-29 and amended six times since, the first
  on the day it was written.** The entries below it in this file predate the rule and never recorded
  it, so the whole sequence is here:
  - **P2 amendment, 2026-08-29** - the flatten time is venue-specific, not universal, and one venue
    permits the overnight.
  - **P1 restatement, 2026-09-08** - **P1 is a SIZING RULE and cannot fail. It was listed as a filter
    and it is not one**, found by an audit of every absolute threshold in the programme for whether
    anything had ever cleared or failed it.
  - **P4 ruling, 2026-09-11** - **"expected time-to-breach" is the life of the FUNDED ACCOUNT, a
    running balance against a floor that ratchets up on gains and never down. It is NOT
    `1 / (per-hold breach rate)`.** The question existed because one study computed both on the same
    arm, the same fixture and the same sizing rule and got **6.40 years against 0.14 years**. **Both
    were computed correctly; they are different objects, and P4 did not say which. It does now.**
  - **P4 and P5 restatement, 2026-09-12** - the principal relaxed both. **P4 was a survival test and
    survival was never the objective**: a prop account is a purchased, replaceable instrument with a
    price, and if the expected profit extracted before breach exceeds that price, breaching often is a
    cost of doing business.
  - **P3 amendment, 2026-09-13** - **P3 reads a RATE, not a maximum**, forced by a candidate whose
    worst day was -$1,315 against a $1,000 cap being read as a binary failure when the rate was **two
    breaches in 1,873 sessions**. P3 is now three numbers: **P3a breaches per year <= 1.0**, **P3b the
    life cost of enforcing it <= 33%**, and the worst day reported and no longer a gate.
  - **Hurdle-P amendment, 2026-09-13** - **the first strategies must fit any venue, so score hurdle P
    at the INTERSECTION, not per venue.** This partly reverses the practical effect of the P2
    amendment: a candidate is scored against the **strictest** rule among the venues, so the overnight
    is not available, the daily loss limit is assumed at 2% and the consistency cap at 30%.
- **R13 was added at D276-D279** (already recorded below) and **R14 arrived with D289 on 2026-09-02,
  then took seven amendments**, five of them on the day it was written: both original "tightenings"
  were wrong and the principal was right; **stage 1 gains a CAPTURABILITY gate**; **a cost ratio is
  unreadable without turnover**, so turnover and holding run become reported; **a score is a RANKING
  and its direction is a choice**; **a peak at the edge of a sweep is unresolved, not concluded**; then
  on 2026-09-03 **the holding period is a DEPLOYMENT variable, not a research one**; and on 2026-09-08
  two more - **no gate is an admission on its own, each is half of a pair**, and **gates 1c and 2c gain
  their partner, hold-driven.** A later addition records that **a FUNCTION choice is a free parameter
  too, and a worse one, because it cannot be swept.**
- **R15, 2026-09-06 - a signal is a positive gross mean per trade above its nulls; cost is tuned
  afterwards, and only the principal closes an avenue.** Written when a closure in D360 was withdrawn
  at the principal's ruling: what was written as a closure was a statement of what had been tested.
- **R16, 2026-09-08 - a published number is not reproducible without naming the build it was computed
  on. Reproduce it EXACTLY on that build, or do not inherit it.**

### Notes (decision numbering across three concurrent sessions, 2026-09-02 to 2026-09-14)
- **`ls docs/decisions/` is not sufficient and will collide.** It happened twice within one hour on
  2026-09-09, the second time while fixing the first: two sessions both took D389, the loser was
  renumbered to **D390 - which was already RESERVED** by a branch that had reserved D390-D399 the day
  before **as a commit message on another branch**, invisible to `ls` and invisible to `git log` run
  on master alone. Both records moved clear of the block, to D400 and D401. **Checking that a number
  is unused is not the same as checking that it is unclaimed**: search `git log --all` for the number
  **and** for `RESERVE`, and list the branches to see who is live.
- **Renaming a number is done by explicit, count-asserted replacement, never a blanket `sed`** -
  a blanket rename once corrupted a link to a *different* record in `docs/RULES.md`. The branch's
  volatility-tilt D390 became D397 across its record, its RESULT, its runner and its artifact; the
  three mentions of the *reserved block* in neighbouring records were deliberately left alone, because
  they name the block and not the study.
- **The lesson that produced the memory rule: commit the pre-registration on its own, before building
  anything. The commit claims the number.** Five collisions in one evening across three sessions.
- **Two sessions both hold a D473 on master** - one a cost-structure study, one the K7 component -
  and it is recorded as a clash rather than resolved.

### Added (D281-D284 - closing the directional short, 2026-09-02)
- `scripts/run_unfiltered_ranking.py` (D281), `scripts/run_overnight_short.py` (D282),
  `scripts/run_descending_ranking.py` (D283), `scripts/run_overnight_long.py` (D284).
  All four returned SURVIVORS NONE.
- `scripts/d280_combined_forecast.py`, `d280_dividend_check.py`, `d280_sign_audit.py` -
  measurement only, ledger unmoved.
- D284 adds `tail_rnd`, a VOLATILITY-MATCHED control: N drawn at random from the 2N most
  extreme |lagged score| names. It is what separates a 4 bp directional signal from a 14 bp
  tail premium, and without it hurdle C would have passed on the nuisance.
- D282 and D284 add an overnight scorer that compounds `log(open[t+1]/close[t])` and refuses
  a grid equal to `total_log_returns`; turnover is charged as `2*|pos|` every night.

### Fixed
- **D279's `top_n` ranked with `score[:, t]` and earned bar `t`'s return** - look-ahead, R9.
  Both survivors withdrawn; ~93% of the apparent ranking edge was the bug.
- **D280 parts 3-5 asserted the wrong SIGN convention** ("a negative IC is the tradeable
  direction for an ascending short"), inverting their headline. Settled in money by
  `d280_sign_audit.py`.
- **`d280_sign_audit.py` itself mixed two lag alignments**, pairing `hist_L[t-1]` with
  `return[t+1]` for the close-to-close target. Both alignments now computed and printed.
- **D279's E-prime was measured over the panel, not the held book** - 5.44 for every cell.

### Documentation
- D271, D274 written up as RECONSTRUCTED POST-HOC; D280 as a measurement record; D284's
  pre-registration AMENDED before the run to add the volatility-matched control, with the
  original preserved byte-for-byte.

### Fixed (D279 LOOK-AHEAD CORRECTION, 2026-09-02)
- **`scripts/run_concentrated_short.py` gains `lag1` and applies it INSIDE `top_n`.** The first
  version ranked qualifying names with `score[:, t]` - `hist_L` computed from the close of the
  very bar the position was about to earn - while `hold_book` lagged the qualifying mask
  correctly. So WHICH NAMES QUALIFIED was honest (D256 is untouched) and WHICH N OF THEM WERE
  HELD was look-ahead, landing exactly on the quantity hurdle C tests. Measured:
  `corr(hist_L[t], return[t]) = +0.0737` against `corr(hist_L[t-1], return[t]) = -0.0103`, on a
  score whose one-bar autocorrelation is +0.9805. **The lag lives inside `top_n` rather than at
  the call site because three other modules call it.**
- **D279's whole RESULT section is rewritten. Its two survivors are withdrawn**: `top25` went
  +2.250 -> **-0.638** Sharpe and `top50` +1.865 -> **-0.659**. **0 of 14 cells survive**, every
  cell has a negative net CAGR and every breakeven borrow rate is negative.
- `data/d279_concentrated_summary.json` and `data/d279_turnover_decomposition.json` regenerated;
  the contaminated versions are kept as `*.WITHDRAWN_lookahead.json` rather than deleted.
- `scripts/d279_fix_eprime.py` re-run on the corrected positions
  (`data/d279_eprime_corrected.log`). **The runner's E-prime defect is NOT fixed** - it still
  calls `RP.effective_instruments(panel, 0)` and returns 5.44 for all fourteen cells - so the
  summary now carries an `Eprime_panel_defect` flag on every cell.
- **Withdrawn as computed on contaminated positions:** every breakeven-borrow figure,
  `data/d279_survivor_attribution.json` in full, and the corrected-E-prime survivor list in
  `data/d279_eprime.log`. `scripts/d279_survivor_only_cut.py` was never completed and is now moot.

### Added (D280 - the forecast pre-check, 2026-09-02)
- `scripts/d280_forecast_precheck.py` - **a measurement instrument, not a study**: DEMA plus
  velocity/acceleration/jerk Taylor extrapolation of each OHLC component, weights FIXED at
  1, 1, 1/2, 1/6 so it cannot overfit, on a declared `n` grid of {9, 21, 34}, reported out of
  sample from 2018-01-01. **Loses to naive persistence in all 48 level comparisons.** Also
  measures effective independent inputs among the 16 terms: **13.50-15.76 of 16**, against a
  predicted collapse below 3.
- `scripts/d280_delta_range_precheck.py` - the anchored `open(t+1) := close(t)` reparameterisation.
  **The anchor is not free: median |gap| 0.5263%, |gap|/|body| = 0.515.** Range forecasts reach
  correlation **+0.87** and still lose to persistence-of-range on MAE in all nine cells.
- `scripts/d280_score_extrapolation.py` - **corrects two errors in the two scripts above**: they
  forecast the RAW close and range when the strategy ranks on the already-smoothed `hist_L`, and
  they used POOLED correlation when the strategy is purely CROSS-SECTIONAL. Measures the
  within-bar Spearman IC instead. **`hist_L` scores -0.00524 (t -1.79) over all live names and
  +0.00462 (t +1.43) - the wrong sign - inside the qualifying set**, because D256 and D279 filter
  and rank on the same variable.
- `scripts/d280_combined_forecast.py` (part 4) - combines the surviving parts as a RANKING question
  rather than a point forecast, and produces the record's headline. **The score's cross-sectional
  edge is entirely OVERNIGHT**: IC vs the gap **-0.01531 (t -4.71)**, vs the intraday session
  **+0.00168 (t +0.65)**; inside the qualifying set the intraday leg runs actively against the short
  at **+0.00868 (t +2.85)**. **Close-to-close - all D256 and D279 ever measured - is the sum of the
  two, which is why it read as noise.** Forecloses intraday exit overlays on this construction, and
  equally forecloses taking the position at the open to shed overnight risk.
- `scripts/d280_dividend_check.py` (part 5) - the ex-dividend confound, since `gap` is built from
  raw OHLC, the fixture is split- but not dividend-adjusted, and a short OWES the dividend.
  **Dividend-adjusted the IC is -0.01498 (t -4.59) against -0.01531 raw**, and excluding ex-dates
  gives -0.01494: a 2-3% move, because only 0.834% of bars go ex next session. On those 216 bars the
  IC is **-0.05197**, 3.4x the average - the mechanism is real and localised. **The overnight edge is
  real.** Records one defect in its own output: the script prints a fixed gloss asserting the score
  tilt is positive when the measured tilt is **-0.0057**, so the printed conclusion does not follow
  from the sign measured. It changes nothing (t -0.97) and is recorded rather than left standing.
- **AN IC IS NOT MONEY, stated in the record:** an overnight book trades ~252 round trips a year
  against ~17 for D279's ~15-day holds, so D265's `mean move per trade >= 2c` bar must be cleared
  15x more often. **D282 is pre-registered separately to measure that arithmetic.**
- **Ledger unmoved at 0** - no cell scored, no rule proposed - but under R13 test 2 any study
  built on these measurements inherits their **161 distinct comparisons** (165 reported across five parts).

### Added (D279 - the concentrated short on the dead-inclusive daily universe, 2026-09-01)
- `scripts/run_concentrated_short.py` (D279) - top-N concentration on D256's two arms,
  N in {10, 25, 50}, with the `random-N` control and the five hurdles. Committed while the
  run was still in flight so the code could not follow the number.
- `scripts/d279_turnover_decomposition.py` - separates ranking from turnover in hurdle C.
  Re-scores every cell at zero fees/borrow/rf and adds a PERSISTENT random control that
  holds its draw while it qualifies. Found that `random-N` churned 5.6x harder than the
  ranked book, so the pre-registered control differed from the treatment in two ways.
- `scripts/d279_fix_eprime.py` - recomputes E-prime over the HELD BOOK rather than the
  panel. The runner's version returned 5.44 for all fourteen cells; corrected it
  disqualifies `S1_short|top10`, the study's highest Sharpe.
- `scripts/d279_survivor_attribution.py` - attributes already-scored P&L across dead vs
  live names, calendar year, and per-symbol concentration.

### Added (cohort 3 - the third instrument holdout, 2026-09-01)
- `data/fixtures/cohort3_intraday_15m_raw.csv.gz` - V JPM FDX MDLZ / BBD TRIP CIEN MUR,
  448,861 rows, 2018-01-02 .. 2026-08-31, 104/104 monthly slices per name, build gates PASS.
  All 28 session-boundary steps above 15% classify REAL (9 market-wide, 19 idiosyncratic
  on volume). Spendable ONCE, on D278's terms.
- `scripts/select_holdout_names.py` gains `--next8` - ranks 13-16 of each stratum under
  D264's rule unchanged, excluding both prior cohorts, with a documented exclusion path
  for names the provider cannot serve.
- `scripts/fetch_single_name_intraday.py` and `scripts/classify_single_name_steps.py` gain
  `--cohort3`, swapping the symbol list and fixture triple in one place.

### Fixed
- D279's hurdle E-prime was computed over the panel instead of the held book, making it
  constant across the grid. Third appearance of the D230/D270 pattern - a hurdle computed,
  printed, and not applied to what it names.
- D279's hurdle C compared books with 5.6x different turnover. S2_short's three C passes
  were the fee gap alone and are withdrawn.

### Documentation
- `docs/decisions/README.md` backfilled with D265-D270, D272-D273 and D275-D279, which had
  not been indexed. **D271 and D274 have scripts but no decision record** - noted, not
  invented.

### Added (D265-D278 - the single-name intraday programme, 2026-09-01)
- `scripts/run_entry_time_reconciliation.py` (D265) - two arms x three bar-of-day buckets,
  behind a **validation gate that rebuilt D264's committed gross to 0.003 points** before
  any bucket was read. Established the cost bar the rest of the session runs on:
  **mean move per trade >= 2c**, in which the trade count cancels and hit rate never
  appears.
- `scripts/run_magnitude_calibration.py` (D267) - nine price scores x three strata x
  quintiles, with a best-of-27 shuffle floor on one shared draw. 0 of 27.
- `scripts/d268_score_independence.py` (D268) - the correlation instrument. **Nine scores
  collapse to 2.87 effective inputs**, and RSI correlates **+0.85** with a MACD level.
  Reusable for any future consensus construction.
- `scripts/run_volume_structure.py` (D269/D270) - five volume scores normalised WITHIN
  bar-of-day, with **two-sided synthetic controls**: `ctrl_blend` must fail, `ctrl_noise`
  must pass.
- `scripts/run_volume_profile.py` (D272), `scripts/run_travel_estimator.py` (D273),
  `scripts/d273_halt_test.py` - the volume profile as input, as travel estimator and as a
  halt level, reusing `research/terrain.VolumeProfileSensor` unchanged.
- `scripts/d271_trade_anatomy.py` + `d271_build_report.py` - per-trade distributions and a
  self-contained HTML report, published as an Artifact.
- `scripts/d274_exit_timing.py` (D274), `scripts/run_choch_short.py` (D275),
  `scripts/run_leg_exit.py` (D276) - the exit question and the BOS/CHoCH state machine.
- `scripts/d277_mine.py` + `d277_sizing.py` (D277) - the 300-cell mine and its sizing
  analysis, with a best-of-300 floor over the whole search.
- `scripts/select_holdout_names.py`, `scripts/run_holdout_test.py` (D278) - the sixteen-name
  instrument holdout and its runner. **`--validate` reproduces all twelve of D277's
  in-sample cells to four decimal places** before the runner may touch the holdout.
- `data/fixtures/holdout_intraday_15m_raw.csv.gz` - 16 names sharing no ticker with the
  in-sample eight. **Three carry splits in span** (RTX x1.589, CMCSA x1.067, HLF x2.0)
  where the original eight had none, so the back-adjustment is load-bearing.

### Changed
- **`docs/RULES.md` - R13 added.** A ledger is scoped to a hypothesis and transfers only
  where it shaped the search. Written after the principal pushed back twice, correctly, on
  inherited counts: terrain's 259 and the ETF programme's 45,783 are disclosed and not
  carried, since **D218 scopes its own floor to "this fixture"** meaning 57 ETFs daily.
  D247-D276 keep the older convention and are not restated.
- `docs/FINDINGS.md` - two extensions. **Section 1b: the `-mu - sigma^2` approximation is a
  FLOOR on the drag, not an estimate** (error -2.85 pts at low volatility, -16.13 at high).
  **Section 6: the overnight/intraday decomposition is cross-sectional as well as
  era-dependent** - low-vol names accrue the drift intraday with the sign reversed.
- `scripts/build_intraday_panel.py` - `--single-names` and `--holdout`, two path constants
  each. ETF defaults untouched.
- `scripts/fetch_single_name_intraday.py` - `--holdout` swaps symbols and the fixture triple
  together in one place, for the reason `build_targets` exists in the ETF fetcher.

### Fixed
- **`exposure_x_edge` was `exposure * (cagr / exposure)`** - algebraically just `cagr`, and
  the column duly reproduced the CAGR column in all sixteen rows (D264). The R6 failure
  mode. Replaced with D250's construction, which is what surfaced the session's central
  decomposition.
- **D270's runner computed M3 only for cells that had already cleared M1 and M2**, so when
  none did it printed "M3 not computed" and stopped - the same short-circuit D230 found in
  D217/D218. Computed afterwards, and it changed the reading: three of fifteen volume cells
  beat the shuffle floor.
- **D271's volume arm counted overlapping windows as trades** - 43,204 "trades" from four
  names over 8.25 years, or 1,309 per symbol per year against 252 sessions. De-overlapped,
  the t-statistic falls from +5.30 to +2.31.
- **The decomposition table was first rendered by subtracting annualised percentages**,
  which do not add: -19.48% where the net was -15.84%. Restated in log units.
- **`classify_single_name_steps.py` used the wrong tests twice** before settling on D259's
  actual bad-print signature - one bar out of line with BOTH neighbours.
- **D273's halt test shuffled without stratifying**, and H2 passed six of six - which under
  R7's corollary is a broken hurdle, not six findings. Stratified, it drops to four.


### Added (D264 - the intraday short on single names, 2026-09-01)
- `scripts/select_single_name_intraday.py` - the sample rule, run ONCE against the committed
  daily fixture over **2013-01-02 .. 2017-12-29, a window disjoint from the 2018-2026 test
  span**, so no statistic that picked a name has seen a bar the study scores. Survivor,
  >=95% coverage, median dollar volume >=$50M, then stratified on realised volatility.
  Output frozen into the fetcher as a literal tuple: LOW = PG LMT PM MO (14.1-16.2%),
  HIGH = CLF SM YELP RH (53.7-78.0%).
- `scripts/fetch_single_name_intraday.py` - `--plan / --actions / --fetch / --build`, reusing
  `fetch_etf_intraday.py`'s helpers rather than copying them (D212). Adds a gate the ETF
  builder does not have: **every session-boundary step above D226's 15% is reported and
  classified**, because `SPLITS` + `DIVIDENDS` do not cover spin-offs and XLF's XLRE
  spin-off is a -18.3% step Alpha Vantage reports as zero splits.
- `scripts/classify_single_name_steps.py` - D226's allow-list, built by measurement.
  **All 30 flagged steps classify as REAL** - 13 market-wide, 17 idiosyncratic on a clean
  volume spike, zero corporate actions, zero split-like ratios, which corroborates the
  provider's "no splits in span" from a direction that does not depend on the provider.
  Every flagged step is in the HIGH stratum; the LOW stratum flagged nothing.
- `data/fixtures/single_name_intraday_15m_raw.csv.gz` + meta + events - 448,279 rows,
  8 symbols, 2018-01-02 .. 2026-08-31. **Zero-volume rate 0.0000%, incomplete-session rate
  0.099%**, 16 half-days derived and dropped.
- `data/fixtures/single_name_intraday_15m_panel.csv.gz` - the aligned panel `load_panel`
  requires: **8 x 55,004 bars, 2,117 sessions, exactly 26.0 per session**, converged on the
  first pass. Comparable by construction to D247's 57 x 55,726 at 25.85/session.
- `scripts/run_single_name_intraday.py` - 16 cells, six hurdles, every leg computed (R6).
  Three things written fresh and each PINNED against the committed primitive it generalises:
  `cost_vector` (per-symbol cost; commission still derived from the IBKR schedule, only the
  half-spread is per-stratum; pinned against `L.per_side_bps`), `excess_vec` (D247's
  financing with a per-symbol borrow rate; pinned against `D.excess_intraday`), and
  `rotation_all` (ONE shared offset draw across all 16 cells in all three strata, because
  the strata are subsets of the same eight symbols and drawing per stratum would inflate the
  best-of floor).
- `SINGLE_NAME_INTRADAY_RESULTS.md`, `data/single_name_intraday_summary.json`,
  `data/single_name_intraday_selection.json`, `data/single_name_intraday_steps.json`.

### Changed (D264)
- `scripts/build_intraday_panel.py` - generalised by two path constants and a
  `--single-names` flag. **The ETF defaults are untouched.** Duplicating 130 lines of
  fixed-point intersection to change two paths is what D212 exists to prevent.
- `docs/FINDINGS.md` - two extensions, both measured by D264. **Section 1b: the
  `-mu - sigma^2` approximation degrades where `sigma^2` is large** - error -2.85 pts on the
  low-vol stratum, reproducing D253's crypto error exactly, against -16.13 pts on the
  high-vol one; it is a FLOOR on the drag, not an estimate. **Section 6: the
  overnight/intraday decomposition is cross-sectional as well as era-dependent** - low-vol
  names accrue the drift INTRADAY with the sign reversed (+4.36% overnight against +5.56%
  intraday) while high-vol names run +13.81% against -8.97%. Section 9 records that the
  concentrated branch was taken and answered.

### Fixed (D264, found during the run and both recorded rather than quietly replaced)
- **`exposure_x_edge` was computed as `exposure * (cagr / exposure)`**, which is
  algebraically just `cagr`, and the column duly reproduced the CAGR column in all sixteen
  rows. R6 is the rule it broke: a reporting requirement that names a quantity is not
  satisfied until that quantity is computed. Replaced with D250's construction - the signed
  position against the bar return - and reported beside the held-bar edge it is the product
  of. The decomposition it enabled is where the study's answer turned out to live.
- **The decomposition table was first rendered by subtracting annualised percentages**,
  which do not add: it gave -19.48% where the net was -15.84%. Restated in
  continuously-compounded units, where the identity closes exactly.
- **`classify_single_name_steps.py` used the wrong tests twice.** v1 asked "did price revert
  within 5 sessions" and "was volume above the trailing median", and tagged CLF and YELP as
  CORPORATE ACTION on 2020-03-17 while tagging RH REAL on the same date - a corporate action
  does not hit three unrelated companies on one day, and the volume denominator already
  contained the crash weeks. v2 still called RH 2018-06-12 a BAD PRINT on 25.69x volume.
  The working test is D259's actual signature: ONE bar out of line with BOTH its neighbours.
  Both wrong versions are documented in the module docstring.


### Added (D262 - the futures data layer and the free rung, 2026-09-01)
- `scripts/fetch_cftc_cot.py` - sibling of `fetch_index_extended.py`, same
  `--plan / --probe / --map / --fetch / --build` phases, same limiter discipline, stdlib
  only. **The symbol map is DERIVED by `--map` and refuses ambiguity**, because a typed
  contract code returns a plausible, well-formed series for the WRONG MARKET and nothing
  downstream errors: `%CRUDE OIL%` matches seven contracts, and `%NATURAL GAS%` matches
  the main Henry Hub contract not at all (the CFTC abbreviates it to `NAT GAS NYME`).
- `data/fixtures/cftc_cot_raw.csv.gz` + meta + map - **210,717 rows, 28 symbols, three
  report families, 1986-01-15 to 2026-08-25, 3.1 MB. COMMITTED**, which nothing else in
  the futures data layer may be: COT is a work of the US government and is public domain.
  Tidy shape, one row per (report, category), `family` on every row so incomparable
  trader taxonomies cannot be pooled. **The micros have their own contracts** (MES
  `13874U`, MNQ `209747`, M2K `239747`, MYM `124608`, plus micro metals), which gives the
  proposal's rung 2 a free weekly form.
- `scripts/futures_continuous.py` - the continuous-contract stitcher and its acceptance
  gates, **built and tested against no vendor data at all**. Rolls on volume or
  open-interest crossover with persistence required, never the calendar; ratio and
  difference back-adjustment with the unadjusted series always retained; no
  forward-filling.
- `scripts/fetch_databento.py` - **verify-first client that cannot spend by accident**.
  `--plan` touches neither network nor key, `--verify` calls only free metadata
  endpoints, `--submit` refuses without both a passed verify and an explicitly accepted
  figure and is then deliberately not wired up.
- `tests/unit/test_cftc_cot_fixture.py` (23), `test_futures_continuous.py` (14),
  `test_databento_client.py` (16). The load-bearing ones are **the open-interest identity
  holds on 55,661/55,661 rows**, **ratio adjustment recovers synthetic ground truth to
  1e-12**, **the gates REJECT the reconstructed Yahoo `ES=F` signature** and a correct
  series still passes, **the provider's own typos are pinned verbatim**, **`--plan` fails
  if it reaches the network**, and **the fixture is byte-reproducible**.
- `docs/cftc_cot.md`, `docs/databento_api.md` - provider references in the shape of
  `docs/alpha_vantage_api.md`. The Databento one tags **every fact VERIFIED or INFERRED**,
  because the docs site is JS-rendered and the surface was established from the two
  official client sources instead.

### Fixed (D262)
- **`fetch_cftc_cot.py --build` is byte-reproducible.** Content was stable across rebuilds
  but the FILE was not: gzip stamps an mtime into header bytes 4-7, so identical builds
  hashed differently. Written with `mtime=0` and asserted directly - D252's
  non-idempotent-build defect in a new disguise.
- **The COT open-interest gate was wrong on its first version**, passing on 5.82% of rows.
  `OI == sum(long)` is not the identity; a spread position is one long AND one short held
  by the same trader, inside open interest and outside the directional columns.
- **The release-date convention was wrong on its first version.** A flat +3 days from a
  Wednesday report lands on a Saturday, and a Friday-dated report would release on itself.

### Changed (D262)
- `scripts/fetch_etf_intraday.py` gains `--start` / `--end`, so extending the ETF span is
  a flag rather than an edit to a module constant.
- `docs/research/futures-data/data-purchase-proposal.md` - three corrections. Rung 2 has a
  free weekly form via the micro COT series; **the proposal's `ES.c.0` is almost certainly
  the CALENDAR roll** and is corrected to `ES.v.0`, since rolling at expiry is precisely
  the defect the acceptance tests exist to catch; and the totals carried a rounding error
  ($0.51 per symbol-year is really $0.5079, so $182.58 is really $181.81).

### Added (D252 - the dead-inclusive US single-name universe, 2026-08-28)
- `scripts/fetch_short_universe.py` - sibling of `fetch_etf_holdout.py`, same
  `--plan / --fetch / --select / --actions / --build` phases, same key handling, same
  rate limiter, same structural success test. **Written fresh: delisted-cohort discovery
  from `LISTING_STATUS state=delisted` plus 16 yearly snapshots, a recycled-ticker rule,
  a PER-SYMBOL pre-live screen, a ragged writer, evidence-based split confirmation, a
  three-way classifier for extreme bars, and a shared-limiter concurrent fetch.**
- `data/fixtures/us_shorts_daily_raw.csv.gz` + events + meta - **1,573 US common stocks,
  4,137,239 rows, 2010-01-04 to 2026-08-26, 562 of them (35.7%) delisted inside the span.**
  Ragged by design: 870 distinct bar counts. `run_macd_ladder.load_panel` refuses it and
  the loader it needs does not exist yet; the meta says what that loader must do.
- `tests/unit/test_us_shorts_fixture.py` - 40 gates. The load-bearing ones are **the
  delisted cohort is above its floor**, **the screen reads the pre-live window and
  nothing after it** (called against `apply_screen` with two series identical for 252
  bars and maximally different afterwards), **no persistent up-step survived without
  volume behind it**, **no rejected split coefficient was applied**, **`--build` never
  reads the sidecar it writes**, and **the key appears in no artifact and no source**.
- `docs/alpha_vantage_api.md` - `LISTING_STATUS` and `TIME_SERIES_DAILY_ADJUSTED`
  sections, provenance-tagged like the rest.

### Notes (D252)
- **Four data findings, each of which changed the build.** (1) `delistingDate` is often a
  roster-refresh stamp - **601 of 9,449 delisted rows carry 2026-08-27**. (2) The
  provider's split coefficients are unreliable for single names: **16 of 959 rejected**
  because the price series contradicts them, 7 of which would have manufactured in-span
  single-bar returns up to **x66.7**. (3) Extreme bars fall into three classes with three
  different right answers - reverting bad prints are LEFT IN for `clean()`, volume-
  corroborated events are retained, unexplained persistent steps exclude the symbol
  (ORIG's x300 is Ocean Rig's unrecorded post-restructuring reverse split). (4) `--build`
  was **not idempotent** and produced 1,580 / 1,573 / 1,574 symbols across three runs of
  unchanged code; fixed, pinned by a test.
- **No strategy was run, no cell scored, no rule proposed.** Ledger contribution: 0.

### Added (D251 - the cross-sectional dollar-neutral pre-screen, 2026-08-28)
- `scripts/prescreen_cross_sectional.py` - eight ranking scores, each with its a priori long leg
  declared before the run, sorted into daily quintiles on the LAGGED score and measured at 21 and
  63 bars, with `exposure x edge` net of measured turnover and borrow. **Written fresh: a
  prefix-sum `rolling_ols` generalising `run_uptrend_onset.rolling_fit` from a bar-index
  regressor to an arbitrary one (pinned against it on the bar-index case), nan-safe prefix sums,
  an eigenvalue `participation_ratio` because `effective_instruments` is degenerate on
  market-neutral residuals, and a disclosed portfolio-level aggregation.** Reused: `load_panel`,
  `base_masks`, `signed_log_returns` / `excess_of` / `score` from D238, `effective_instruments`
  from D245.
- `tests/unit/test_cross_sectional_prescreen.py` - 18 gates. The load-bearing ones are **R9 from
  the strong side** (corrupt every bar after a cut point; no earlier score may move), **a nan may
  not poison the future** (the defect that silently emptied both `md_L` cells on the first run),
  **the reuse pin against `rolling_fit`**, and **the two aggregations identical on one symbol** -
  D251's verdict turns on their difference, so a second defect in either had to be excluded.
- `CROSS_SECTIONAL_PRESCREEN_RESULTS.md`, `data/cross_sectional_prescreen_summary.json`.

### Notes (D251)
- **D245's reserved never-seen cohort is not spent.** The pre-screen names only the extended 57
  fixture, and a test pins that no reserved fixture appears in the script at all.
- **No hurdle, no null, no runner.** A pre-screen in D250's shape - the point is to close a family
  before paying for the machinery, and it did.

### Added (D249 - the inverse wedge breakout, 2026-08-28)
- `scripts/run_wedge_inverse.py` - the wedge geometry (two pivot regression lines, convergence,
  ATR-scaled channel width), a +/-2 ATR trigger off the channel midline, and a long-only book on
  the DOWN break. Screened on the extended 57, validated on the 60-ETF instrument holdout.
  **Written fresh: the wedge state machine and its walk, a paired block bootstrap on the
  CORRELATION (`J.paired_block_bootstrap` returns a Sharpe difference, a different statistic), and
  a daily `breakeven_bps` (the existing one is bound to `excess_intraday`).** Everything else is
  reused - `rolling_fit`, `atr_log` and `null_book` from D240, the signed scorer, `excess_of` and
  `rotation_nulls` from D238, `sub_score` from D243, `effective_instruments` from D245.
- `tests/unit/test_wedge_inverse.py` - 19 gates. The load-bearing ones are **R9 asserted from both
  sides** (the armed mask, the centre and the ATR must each be the `t-1` value or a synthetic trade
  lands on a different bar), **no look-ahead on the real panel**, and **hurdle E asserted PER SYMBOL
  and asserted to FAIL** - if it ever silently passes, the record is stale.
- `WEDGE_INVERSE_RESULTS.md`, `data/wedge_inverse_summary.json`.

### Notes (D249)
- **D245's reserved never-seen cohort is not spent.** `books_on` refuses to open either
  wide-universe fixture and the refusal is pinned by test.
- **The two-legged null is what caught the result.** Money alone would have passed W2 at the 99.8th
  percentile; Sharpe alone would have missed that the book earns real money. The gap is a 2.20x
  volatility ratio against the null.
- **`concurrency` is a new diagnostic and it belongs beyond this study.** It decomposes that
  volatility gap into *loudness* (are the held bars individually more volatile - here only 1.14x)
  and *clustering* (how many names are held at once - here up to 41 of 57 against a rotated book's
  23). **A per-symbol rotation null destroys cross-sectional synchrony by construction**, so it
  under-states the volatility of any market-wide signal. Computed post-hoc, disclosed, counted.

### Added (D244 - the book on crypto, 2026-08-28)
- `scripts/run_book_crypto.py` - the frozen book on 35 coins over 5.2 years at 10 bp/side.
  **Written fresh: the 34-coin panel builder, the cost override and the PPY = 365 override.**
  The builder iterates to a fixed point because `clean` drops bars per symbol, so a raw date
  intersection does not survive loading with equal bar counts.
- `data/fixtures/crypto_book_2018_raw.csv.gz` - 35 coins from 2018-01-01, chosen by DATE (the
  earliest start retaining a majority of the 63 ragged-inception coins), never by performance.
- `tests/unit/test_book_crypto.py` - 16 gates. The load-bearing ones cover the two silent ways
  this study could go wrong: **an override leaking** into the shared modules and corrupting every
  later equity study, and **a single-symbol book scored on the full panel**.
- `BOOK_CRYPTO_RESULTS.md`, `data/book_crypto_summary.json`.

### Fixed (D244)
- **"BTC alone" was being scored at 1/35 weight.** Zeroing 34 of 35 rows leaves
  `portfolio_log_returns` dividing by 35, so BTC reported +1.13% CAGR instead of **+48.15%** -
  the same defect `subset_panel` was written for in D239. Now scored on its own one-symbol panel.
- **The crypto overrides are restored in a `finally` and asserted off afterwards.** `PPY` and
  `cost_fraction` live on shared modules; one left switched on would have silently corrupted
  every later study on the equity fixtures.

### Changed (D244)
- **`docs/BOOK.md` carries two more amendments.** S1 failed on crypto at the **29.1st percentile**
  of its own rotation null - worse than random timing - which is its second consecutive failure
  and the first on the asset class the reversal thesis said should suit it. S2's generality is
  recorded as **bounded to equities**: it beat the benchmark and failed its null at the 73.2nd.
- **D244 carries a written CORRECTION**: its pre-registration claimed the universe held LUNC,
  USTC and FTT. It does not - all three launched after 2018 and the date cut excludes them.
  Caught by a test asserting their presence, which failed. Appended, not edited.

### Added (D243 - the book on extended history, 2026-08-28)
- `scripts/fetch_extended_history.py` - rebuilds the daily fixtures back to each universe's own
  inception. The price cache already held full history; what was missing was **corporate actions**,
  whose sidecars stopped at 2015-01-16. Fetches SPLITS and DIVIDENDS over the full span for all
  117 symbols (234 calls) - 5,716 dividends and 30 splits for the 57. Building without them would
  have left every pre-2015 split unadjusted, which D226 showed produces confident nonsense.
- `data/fixtures/universe_daily_extended_raw.csv.gz` - 57 symbols, 4,222 bars, 2009-11-11 to
  2026-08-26. **12.8 live years against 6.0.** Capped by GDXJ's inception.
- `data/fixtures/universe_holdout_extended_raw.csv.gz` - 60 symbols, 2,963 bars, 7.8 live years.
  Capped by HACK.
- `scripts/run_book_extended.py` - the frozen book on the extended fixture, with the live window
  split into NEW / TRAIN / FORWARD. **Written fresh: the sub-period split, and nothing else.**
- `tests/unit/test_book_extended.py` - 16 gates, including that the split is applied to scored
  RETURNS rather than to the signal, so the pre-2018 window carries the warm-up it would have had.
- `BOOK_EXTENDED_RESULTS.md`, `data/book_extended_summary.json`, `data/extended_history_summary.json`.

### Changed (D243)
- **`docs/BOOK.md` carries two amendments, both committed in advance by D243's stop.** S1 failed
  every hurdle on the never-seen 2013-2018 window and its headline Sharpe is restated from +0.746
  (6.0y) to **+0.478** (12.8y). S2 cleared every hurdle there and is now the only rule in this
  programme to have passed both an instrument holdout and a time holdout.
- **The old fixtures are untouched** (D24), so every previously published number stays reproducible.

### Added (D242 - the withheld-data verdict, 2026-08-28)
- `scripts/run_uptrend_withheld.py` - A0, A2 and the combined book on the 60-ETF holdout.
  **Written fresh: nothing.** Every component already existed and was tested; a holdout test
  that needed new code would be a holdout test whose code had never been checked.
- `tests/unit/test_uptrend_withheld.py` - 14 gates, including the two ways a holdout test can be
  worthless: **the rule drifting** (every frozen constant asserted, and the mined numbers must
  reproduce before the withheld fixture is touched) and **the fixtures being crossed** (the two
  symbol sets asserted disjoint).
- `UPTREND_WITHHELD_RESULTS.md`, `data/uptrend_withheld_summary.json`.

### Changed (D242)
- **`docs/BOOK.md` gains S2 - the uptrend onset.** Second entry, admitted on a pre-registered
  out-of-sample test per R8, carrying its falsification conditions and five recorded weaknesses.
- **D240's result section carries a written CORRECTION.** Its headline quoted A2 at +0.822 on the
  strength of a stop that then failed its overlay null out of sample - 99.6th percentile mined,
  71.7th on the holdout. A0 is the finding. Appended, not edited.

### Added (D241 - the combined book and capital allocator, 2026-08-28)
- `scripts/run_combined_book.py` - the S1 + A2 book, and a **capital allocator** with a shared
  pool, per-arm reserves and first-come-first-served rationing. Written fresh: nothing in the
  repo can express *this entry was denied because the pool was full* - D236's control scales a
  position matrix that already exists.
- `tests/unit/test_combined_book.py` - 14 gates.
- `COMBINED_BOOK_RESULTS.md`, `data/combined_book_summary.json`.

### Fixed (D241 - two invariants, both caught by assertions during the build)
- **A name is held once and charged once.** Both arms can want the same instrument (1,000 cells,
  3.63% of demand); the first draft summed the two granted books and **double-funded** them. The
  allocator now works on names, with an owning arm tracked for accounting only, and ownership
  transfers without a capital event when one arm exits and the other still wants the name.
- **`TOTAL` is a hard cap and is enforced globally.** Because ownership can transfer without a
  capital event, an arm can come to hold more than its reserve - after which the per-arm room
  checks no longer bound the sum, and the 50%-cap cell over-committed. `RESERVE` constrains
  *funding* per arm; `TOTAL` constrains the *book*.

### Added (D240 — the uptrend-onset arm, 2026-08-28)
- `scripts/run_uptrend_onset.py` — pivot-regression trend states, an onset/age-cap state
  machine, log-space ATR, and **R7's matched-exit-count trade-level overlay null**, which did
  not exist: `run_risk_controls.overlay_null` is bar-level position scaling, and D235's
  committed runner only ever called a rotation null whose p95 of −0.284 anything would clear.
- `tests/unit/test_uptrend_onset.py` — 14 gates. The load-bearing two are the prefix-sum
  regression pinned against brute-force `np.polyfit`, and D173's confirmation lag asserted
  directly (a pivot is invisible for exactly `k` bars).
- `UPTREND_ONSET_RESULTS.md`, `data/uptrend_onset_summary.json`.
- **`rolling_fit`** — rolling OLS slope *and* intercept in **O(T) per symbol** via prefix sums
  over `(1, x, y, x², xy)` deposited at pivot indices, replacing 86k per-`(symbol, bar)`
  refits. Measured at 0.2s for all 57 symbols. The causal window `i ∈ [t−252, t−k]` is
  expressed exactly as `P[t−k+1] − P[t−WINDOW]`.

### Added (D239 — time-series momentum as arm two, 2026-08-28)
- `scripts/run_tsmom_arm.py` — 12-month TSMOM on the 57, plus `subset_panel`.
- `tests/unit/test_tsmom_arm.py` — 13 gates.
- `TSMOM_ARM_RESULTS.md`, `data/tsmom_arm_summary.json`.

### Fixed (D239)
- **`subset_panel`, and the defect that motivated it.** An N-name book must be equal-weighted
  over **N**. Zeroing the unwanted rows of a 57-row position matrix leaves
  `portfolio_log_returns` dividing by 57, so an 11-name book at 49.8% exposure scored as a
  57-name book at **9.6%**. Caught only because D239 published the exposure *before* the run.
- **`run_short_mirror.rotation_nulls` filtered cell names against its own module-level
  `CELL_ORDER`**, so it silently returned nothing for any caller whose cells are named
  differently — which D239 is. Now uses dict insertion order. **D238's artifact is numerically
  unchanged** (the two orders coincided for its own call); verified field-by-field against the
  committed JSON.

### Added (D238 — the short-side mirror, 2026-08-27)
- `scripts/run_short_mirror.py` — the first **signed** book in the programme, and with it a
  scorer that handles `position = −1` correctly.
- `tests/unit/test_short_mirror.py` — 16 gates, offline and deterministic.
- `SHORT_MIRROR_RESULTS.md`, `data/short_mirror_summary.json`.

### Fixed (D238 — short compounding, and it would have been silent)
- **`position * log_return` is wrong for a short.** It is exact at `pos ∈ {0, 1}` and wrong at
  `pos = −1`, because a daily-rebalanced short earns `log(1 − r_simple)` per bar, not
  `−log(1 + r_simple)`. The two differ by one variance per bar and the error runs one way:
  it **flatters the short**. Measured on D238's own book, **−11.97% correct against −2.75%
  naive — a 9.22-point overstatement.** On a two-bar case it flips the sign outright.
- The replacement, `signed_log_returns`, is `log1p(pos * expm1(r)) + log1p(−cost)` and is
  **exactly backward-compatible**: it reduces to the existing code at `pos ∈ {0, 1}`, so no
  previously published number moves. That is pinned by test against `portfolio_log_returns`
  rather than asserted, and against a hand-computed short.
- **Financing generalised too.** `excess = total − mean(max(pos,0))·rf − mean(max(−pos,0))·borrow`
  — rf on the long fraction only, since a short book's collateral earns rf, plus borrow on the
  short fraction. Also reduces exactly to the long-flat formula.
- `run_exposure_dial.score`, `_excess_sharpe` and `rotation_nulls` all inherit the original
  defect. They are **correct for every book scored so far**, all of which are long-flat, and
  are superseded for signed work by the versions in `run_short_mirror.py`.
- Stale `next number` counters corrected in `docs/RULES.md` (D236 → D239) and
  `docs/decisions/README.md` (D238 → D239).

### Added (Alpha Vantage intraday provider, 2026-08-27)
- `scripts/fetch_etf_intraday.py` — 15-minute bars for the 57-ETF universe, 2018-01 to
  2026-08, one call per `(symbol, month)`. Resumable, cached, paced at 66/min against a
  75/min tier ceiling. Raw cache is not committed (D191); only the derived fixture is.
- `docs/alpha_vantage_api.md` — the provider reference, with **every claim tagged
  `[DOC]` / `[MEASURED]` / `[INFER]`**, because the documentation is thin on exactly the
  points a study depends on.

### Why (Alpha Vantage)
- yfinance serves **60 days of 15m** (D160). Impulse MACD at `(136, 36)` needs **4,049
  bars of warm-up alone** — short by a factor of three *before* the strategy starts. Alpha
  Vantage's `month=YYYY-MM` slices reach back to 2000-01, which is what makes an intraday
  ETF study possible at all.

### Measured before spending ~5,900 requests
- **Volume is CONSOLIDATED** — SPY median session 66,595,182 shares against a ~70–90M
  consolidated ADV. Undocumented, and the one finding that could have killed the study.
- Timestamps mark the interval's **OPEN**, so a bar stamped `t` is not complete until
  `t+15m` — a look-ahead hazard, now recorded in the fixture meta.
- Errors arrive as **HTTP 200** with an `Error Message` body; success must be decided
  structurally or error bodies land in the fixture.
- `outputsize=full` is **mandatory** with `month`; the default returns 100 bars silently.
- **Fetch extended hours, build regular hours only.** Extended bars exist only where
  something traded (AGG 27–35/session, ragged; RTH exactly 26 every session), so an
  extended-hours fixture would put a **liquidity-correlated** difference in bar counts into
  a **volume** study.

### Fixed
- Corrects an inference that `adjusted=true` dividend-adjusts **volume**. Measured: volume
  is byte-identical either way (ratio 1.000000); only prices adjust. `adjusted=false` is
  still right — adjusted prices are *back-adjusted* and drift with every dividend, which
  breaks D24's immutable-snapshot rule.

### Added (holdout fetcher, 2026-08-27)
- `scripts/fetch_etf_holdout.py` — the selection rule pinned in code and committed
  **before** it runs. LISTING_STATUS active ETFs minus the parent 57, ipoDate <= 2014-12-31,
  no leveraged/inverse, ranked by median dollar volume over **2015-01-02..2018-12-20** —
  strictly *before* the parent's first live bar, so the screen cannot see the test period.
  Top 60 with complete coverage of the parent's exact date grid. Pool: **1,219 eligible**.

### Result (D230 addendum) — the arm against buy-and-hold also contains zero
- `arm - buy-and-hold` was D218's hurdle D, quoted in every record since, and **never given
  an interval**. Computed: **+0.335, 90% interval −0.242 to +0.804, contains zero.**
- +0.335 remains the best estimate, and 8.8% vol against 17.7% with a −12.70% drawdown
  against −34.81% are descriptive facts the interval does not touch. What is not established
  is that the advantage generalises.
- Now stored under `arm_vs_benchmark` in the artifact, reproducible rather than conversational.

### Added (D230 — the bootstrap sweep, 2026-08-27)
- `scripts/run_bootstrap_sweep.py` + `data/bootstrap_sweep_summary.json` +
  `BOOTSTRAP_SWEEP_RESULTS.md` + `tests/unit/test_bootstrap_sweep.py` (18).
- A **reproduction gate**: every point estimate must match its committed artifact to 1e-9
  or the sweep stops and reports that instead.

### Result (D230) — zero of twenty-four clear the hurdle as claimed
- **8 of 24 cleared as the runners scored it. 0 clear as the records claimed it.
  All 24 intervals contain zero.** Reproduction clean.
- **The subtler error runs the other way**: D218's `I2-I3` (-0.016 to -0.032) and `I1-C`
  (~0) were read as evidence of *absence*, on intervals 3-6x and ~±0.3 wide. An interval
  that wide around zero is evidence of nothing.
- 12 of 24 have intervals wider than 5x their point estimate; the extremes are 180.8x
  and 63.6x.

### Fixed (D230)
- **Corrects D229 and the conversation.** D229 called D218's cross-construction argument
  "untouched"; it is not. The `I1-C` leg is what the sweep dissolves, and "independent"
  overstates it — D218's span is a *subset* of D217's on the same 57 ETFs. What survives is
  corroboration, not independent replication. Recorded as an addendum on D229 too, so that
  record does not read as sound standalone.

### Added (D229 — the jerk rung, 2026-08-27)
- `scripts/run_jerk_rung.py` + `data/jerk_rung_summary.json` + `JERK_RUNG_RESULTS.md` +
  `tests/unit/test_jerk_rung.py` (17).
- **A paired block bootstrap**, which the repo did not have. Both rungs recomputed on
  identical resampled dates, block 21, 1,000 replications.

### Result (D229) — the derivative ladder closes at I1
- **Jerk does not beat acceleration.** `I0 - I1 = -0.218`, hurdle A fails in all four cells.
- **P1-P5 all confirmed**, and a clean sweep in a study that predicted its own failure is
  the easy case; only P4 carried information.
- **I0 beats the LEVEL rung** (`+0.310`) while losing to acceleration — both derivative
  rungs beat level, so the ladder is not monotone.
- The pre-registration's free measurements landed exactly: exposure 48.5% (48.53% predicted),
  turnover 16,421 (16,422 predicted).

### Fixed (D229)
- **D217 and D218 both state hurdle A as "above the paired bootstrap's p95" and NEITHER
  RUNNER EVER RAN ONE.** The leg now exists, and **D218's headline fails it in all four
  cells**: `I1 - I2 = +0.628` has a 90% interval of `-0.133` to `+1.325`, containing zero.
  Fairly stated, this attacks the reported *certainty*, not the point estimate, and leaves
  D218's cross-construction replication argument untouched.
- **Third appearance of the `sort_keys` idempotency defect** (D220, D222): `--report-only`
  emitted the same content in a different row order. Pinned by an explicit `CELL_ORDER`.

### Added (D228 — the filter search, 2026-08-27)
- `scripts/run_filter_search.py` + `data/filter_search_summary.json` +
  `FILTER_SEARCH_RESULTS.md` + `tests/unit/test_filter_search.py` (23).
- The **best-of-search null**: the identical eight-candidate search run over rotated filter
  signals, one offset vector per replication reused across all candidates so cross-candidate
  correlation survives. 1,000 replications, 73.5 s.

### Result (D228) — the filter line on the acceleration arm is closed
- **Nothing clears anything.** Best candidate +0.023 excess Sharpe against a measured floor
  of **+0.104**, barely above the null's *median* of +0.014. Not one of eight clears hurdle P.
- **Both gates also fail hurdle E** — 16 and 11 entries per symbol against 30 required.
- **Sizing dominates gating on both matched pairs**: S3 beats G1 by 15.33 pp of money at a
  0.060 Sharpe difference; S4 beats G2 on both metrics.
- **The analytic floor was never the problem.** At matched N the formula (+0.099) and the
  measured floor (+0.104) agree to within 5%. What was wrong was `var_trials` and inherited N.
- **The mechanism, measured**: across candidates spanning 24%–100% exposure, money delta
  against exposure delta gives **r = +0.823**, slope 0.58 pp per pp. Seven studies of "better
  Sharpe, less money" explained rather than repeated.

### Fixed (D228)
- **rf on a long-flat book is charged on the EXPOSED FRACTION**, not the whole book. The arm's
  excess Sharpe is **+0.566**, not the +0.354 quoted in conversation; buy-and-hold is +0.231.
- Recorded that D218's headline **+0.658 is price-only** while the money figures beside it are
  dividend-adjusted — two bases mixed in one sentence. The dividend-adjusted Sharpe is +0.793.

### Added (D226 — the gate on 57 ETFs at 15m, 2026-08-27)
- `scripts/fetch_etf_intraday.py` gains `--actions` (SPLITS + DIVIDENDS) and split
  adjustment; `data/fixtures/etf_intraday_15m_raw*` — a purpose-built 57-ETF 15-minute
  fixture, 3.19M rows, 7.94 live years, zero zero-volume bars.
- `scripts/run_etf_intraday_gate.py` + `data/etf_intraday_gate_summary.json` +
  `ETF_INTRADAY_RESULTS.md` + `tests/unit/test_etf_intraday_fixture.py` (20).

### Result (D226) — the volume regime gate is closed
- **The spike moved.** The gate clears H at **one window of ten (96 bars)**, and D224's
  committed **200-bar window lands at the 45th percentile** here. Two spiky profiles with
  spikes in different places is a fitted parameter, not a discovered one.
- **Three cells cleared the multiplicity floor** — a first — but because 57 instruments
  tighten the null (sd 0.082 vs crypto's 0.24), dropping the floor from +0.88 to +0.35 at a
  *larger* look count. D219's amendment, demonstrated.
- **Nothing survives**: window 96 beats the parent on Sharpe and loses on money.
- **The dividend fetch changed the verdict**: price-only the gate ties its parent (+15.5%
  each); dividend-adjusted it loses by 4.6 points.

### Fixed (D226)
- **Twelve unadjusted splits** in the new fixture, worst appearing as a **+1,772% single
  15-minute bar**. Now back-adjusted in prices *and* volumes (opposite directions —
  `corporate_actions.split_adjusted` does not touch volume, and this is a volume study).
  Five of the twelve existed nowhere in this repo.
- An early runner draft declared `VERDICT_COUNT = 3879`, D225's *crypto* arithmetic applied
  to an ETF study. Corrected to 10 / 78 / 45,819.

### Added (D225 — the gate at 1h, 2026-08-27)
- `scripts/run_gate_1h_replication.py` + `data/gate_1h_summary.json`. Reuses D224's scoring
  path verbatim; only the position builder is local, because `build_positions` hard-reads
  its window constants.

### Result (D225)
- **The volume gate replicates at 1h.** Δ vs parent **+0.635** (BTC) and **+0.558** (ETH)
  against 15m's +0.489 / +0.590, with hurdle H at 99.5/100 and 98.5/98.8. It is **not** an
  artifact of the 15m sampling rate, and it beats the mechanical benefit of trading less by
  about **6×**.
- **Its working window is one point wide.** 50h is the only positive-net window on BTC out
  of ten; both neighbours are negative; and **at 200h the identical construction inverts
  into a significant anti-signal** (0.5th percentile of its own null).
- **Two claims separated:** the *signal* is scale-free in bars (D221); the *gate* is **not**
  scale-free in wall-clock — it is window-critical.
- Nothing clears the verdict floor. ETH clears the fresh-look floor by 0.084 — D214's
  pattern for the second study running.

### Fixed (D225)
- **Recorded after the run**, which departs from this programme's practice and is disclosed
  in the record rather than glossed. The replication was confirmatory of a pre-registered
  claim; the **40-cell window sweep was an unregistered search** and is counted as such.
  The 50-hour window was clean when D224 used it and **is not clean now**.
- Corrects a subagent claim: the window-response curve agreeing across the 15m and 1h grids
  is a *mathematical consequence* of D221's invariance (the 1h series is resampled from the
  same bars), so it validates the implementation and is silent on whether 50h is special.

### Added (D223/D224 — the volume-regime gate and the assembled strategy, 2026-08-27)
- **D223** pre-registers the volume-regime hypothesis and measures its two premises.
  Volume/volatility holds emphatically (top quintile has **4.5x** the mean absolute move);
  the signal-to-noise refinement does **not** — the variance ratio falls from **1.35 to
  0.67** across volume quintiles, so quiet markets trend and loud markets revert.
- **D224** + `scripts/run_assembled_strategy.py` + `data/assembled_strategy_summary.json`
  + `ASSEMBLED_RESULTS.md` + `tests/unit/test_assembled_strategy.py` (14). Run as a
  **2x2 factorial**, not a stack, so each component's contribution and their interaction
  are separable.

### Result (D224)
- **The volume gate is the first thing this programme has produced that beats its own
  matched-count random null** — 96th/96th percentile on BTC, 100th/100th on ETH. It takes
  BTC from -0.284 to **+0.205** net Sharpe and ETH from -0.006 to **+0.584**, deltas above
  the pre-stated MDE of 0.18.
- **It still fails the multiplicity floor** (+0.880 / +0.923 at 3,833 looks). ETH clears the
  *fresh-look* floor and fails the verdict one — D214's pattern exactly.
- The **2-ATR trailing stop is catastrophic**: it stopped out **98%** of trades, cut median
  hold 63 -> 7 bars and cost 2.0-2.9 Sharpe.
- The **interaction is strongly negative** (-2.561, -1.568), exactly as D223's variance-ratio
  census predicted. Running the stack whole would have shown a bad number and taught nothing.

### Fixed (D224)
- **A look-ahead defect, caught by an implausible number.** Zeroing the position on the bar
  the stop triggered let the book escape the entire adverse move, inflating `C_stop` to
  gross **+4.197**. The stop bar is now a held bar earning `log(fill / previous close)`.
- **The fill now uses `simulator.fills.stop_fill_price` (D10)** rather than a restatement —
  the repo already encoded "a gapped stop fills at the open", and reimplementing it was
  D212 again.
- **`var_trials` now comes from the simulated null, not from the study's own cells.** D219's
  amendment predicted the inflation; here it is extreme, with `C_stop`'s -3.17 putting the
  floor at an unusable **+4.944**. Every future study should estimate it from its null.
- Hurdle G was **missing from D224's pre-registered hurdle list** and was added post hoc —
  defensible only because it made the result worse, and disclosed rather than absorbed.

### Added (D222 — the scaling ladder, 2026-08-27)
- `scripts/run_scaling_ladder.py` + `data/scaling_ladder_summary.json` +
  `SCALING_RESULTS.md` + `tests/unit/test_scaling_ladder.py` (12). Reuses D221's arm,
  annualisation and Sharpe by import rather than restating them (D212).
- A **paired block bootstrap** on the shared daily grid — both arms recomputed on the same
  resampled index set, so the pairing survives the resample.

### Result (D222)
- **The fine-bar residual D221 left is noise.** Delta(k) goes up, down, then sideways:
  BTC +0.155 / -0.124 / +0.012 and ETH +0.148 / -0.087 / -0.120 across k = 4 / 32 / 96.
  Negative in 3 of 6 cells, no ordering by k, and **all six bootstrap intervals straddle
  zero** (widths 0.36-0.50 against deltas of 0.01-0.16).
- **The cleanest proof needs no statistics:** the same Delta(4) measures +0.054 on D221's
  8.3 years and +0.155 here on 5.6. A statistic that moves 0.10 when you change the start
  date is not measuring a property of the estimator.
- **Strengthens D221.** At k = 96 the 15m arm decides 96x more often than the daily arm and
  still trades the same 8-9 round trips a year: **turnover is set by the window, not the
  bar rate** — as signal already was.
- The verdict is **"not detectable here"**, not "does not exist": resolving a 0.05 effect
  needs ~19x the independent sample, about 100 symbol-years against the ~11 available.

### Fixed (D222)
- The shared-span gate demanded identical start timestamps across configs, which is
  impossible — a daily bar can only begin at 00:00 UTC and an 8h bar at 00/08/16:00. It
  fired on the first run, **wrong in the safe direction**: it refused to publish rather
  than publishing a misaligned comparison. Rewritten as a bounded spread (all starts agree
  to within one coarse bar) and pinned by a test that checks it still rejects a genuinely
  misaligned ladder.

### Added (D221 — sampling invariance, 2026-08-27)
- `scripts/run_sampling_invariance.py` + `data/sampling_invariance_summary.json` +
  `SAMPLING_RESULTS.md` + `tests/unit/test_sampling_invariance.py` (13). The 1h series is
  exact OHLCV aggregation of the 15m source (D161) on a **shared calendar**, so a gap
  between the two is the sampling rate and nothing else.

### Result (D221)
- **Invariance holds. The window is the variable; the sampling rate is not.** 15m with x4
  parameters matches 1h with defaults on every symbol — deltas +0.054, +0.080, -0.103,
  -0.149 — with hourly return streams correlating at **0.94-0.96**.
- **The control carries it:** the same indicator on the same 15m bars with an *unmatched*
  window correlates at only **0.50** and loses up to 4.183 Sharpe.
- Round trips are set by the window too: ~225/yr matched on either bar rate, ~950
  unmatched. The cost problem and the signal problem had one cause.
- **Nothing is tradeable**, as pre-committed. Every matched config is negative at
  `taker_40bp`; the sole positive net cell is BTG, the least reliable series in the study.

### Fixed (D221)
- **Corrects the earlier 15m screen.** It reported gross -0.400 on BTC and concluded the
  signal was dead at 15m. That ran the default `(34, 9)` on 15m bars — an 8-hour channel
  against the 1h version's 33-hour one — so it compared two indicators and reported it as a
  comparison between two timeframes. Matching the window moves BTC from -0.298 to **+0.735
  on the same bars**. The screen's cost arithmetic stands; its signal conclusion does not.
- Records that `crypto_intraday_1h_raw`, the repo's only **native** 1h crypto fixture, is
  **50.4% zero-volume bars** — the cleaner drops 17,520, leaving an irregular ~2h series
  wearing a 1h label. Unusable for frequency comparison and for volume work.

### Added (D219/D220 — the dual verdict and the volume filter, 2026-08-27)
- **D219** changes the acceptance rule: every arm now carries **two verdicts**, standalone
  (A–G) and in-portfolio (P1–P5), reported side by side with neither allowed to replace the
  other. P4 makes correlation a hurdle rather than a hope; P5 moves the unit of deflation
  from the arm to the book. Amended pre-run with the cross-fixture invariant — comparisons
  are made on `arm − matched buy-and-hold`, never on raw Sharpe.
- **D220** + `scripts/run_volume_filter.py` + `data/volume_filter_summary.json` +
  `tests/unit/test_volume_filter.py` (22). Volume is loaded **separately** rather than by
  changing `load_panel`, so no previously published number can move; a test pins it.
- The **ORACLE bound** and the **matched-count random null** as a reusable pair for any
  selection rule over a fixed trade population, plus the **capture ratio** they define.

### Result (D219/D220)
- **A volume filter selective enough to matter cuts the arm below its own power threshold
  before it can be judged.** All 12 cells remove 39–61% of trades; every one fails the
  pre-registered census gate. At 7.1 round trips per ETF per year the trade population is
  too thin to subset — a fact about the **arm**, not about volume.
- The textbook confirmation rule never clears selectivity. **No cell beats the parent on
  money**; the two that beat it on Sharpe cost 31 and 18 points of return.
- Capture ratios of **0–6%** against an ORACLE reaching **+1.503**: the space was real and
  volume took none of it.
- **Hurdle H in isolation would have promoted a book with Sharpe −0.003.** Only the
  conjunction caught it — D219's dual verdict working on its first outing.

### Fixed (D220)
- `append_section` reintroduced D217's non-reproducible-render defect in a new place: the
  insert and replace paths emitted a different number of blank lines, so `--report-only`
  did not reproduce the page byte-for-byte. Now strips any existing section first so both
  paths run one insertion, pinned by
  `test_report_only_reproduces_the_page_byte_for_byte`.

### Added (D218 — Impulse MACD, 2026-08-24)
- Impulse MACD (LazyBear) in `research/macd.py`: `smma` (Wilder, alpha = 1/n), `zlema`
  (`2*EMA1 - EMA2`, centre of mass exactly zero), `impulse_macd_series` and the three rung
  scores. Deliberately in the same module as the D217 ladder so the two indicator families
  stay pinned together.
- `scripts/run_impulse_macd.py` + `data/impulse_macd_summary.json` + a D218 section in
  `MACD_RESULTS.md`. The runner **imports the D217 runner** rather than restating its cost
  path, portfolio arithmetic, nulls or DSR machinery — D212 is why — and a test asserts by
  identity that it has not defined its own copies.
- `tests/unit/test_impulse_macd.py` (33) and `tests/unit/test_impulse_ladder.py` (16).

### Result (D218)
- **D217's mechanism replicates, and the clean read is stronger than the headline delta.**
  I1−I2 = +0.628 long-short against D217's +0.285, but **I1−C ≈ 0** (−0.038 to +0.008): a
  Wilder channel, a zero-lag mid and a dead zone buy nothing over `EMA(12)−EMA(26)`. Two
  acceleration rules from unrelated arithmetic agree to within 0.04 Sharpe while both level
  counterparts are dead.
- The level rung is **anti-predictive**, not merely dead: −0.265 Sharpe at the 0.0th
  percentile of its own rotation null.
- The dead zone hurts **both** metrics — the indicator's most distinctive feature is its
  most useless one.
- Best cell +0.658 (the highest this project has produced on this fixture) fails A, D and G.
  **0 of 16 clear; the pre-registered stop applies.**
- Verdict floor +1.420 at 45,803 looks, driven by the inherited prior rather than this
  study: **no arm anyone runs on this universe can clear it.** The fixture is exhausted.

### Fixed (D218)
- Hurdle D now names **both** metrics before the run (Sharpe AND dividend-adjusted total
  return, both required), which is the design-time fix for the gap D217 had to disclose in
  an addendum. It bites immediately: the best cell beats buy-and-hold on Sharpe at a third
  of the drawdown and loses 10 points of money.
- Recorded a real defect in the published indicator: an SMA seed matches an EMA's steady
  state only at `alpha = 2/(n+1)`, and Wilder smoothing uses `1/n`, so Impulse MACD starts
  16.5 slopes from its own steady state and needs **926 bars** to forget it — about four
  years of daily data. Pinned by
  `test_the_sma_seed_is_exact_for_the_macd_ema_and_NOT_for_wilder`.

### Added (D217 — the MACD crossover ladder, 2026-08-24)
- `src/backtest_framework/research/macd.py` — the first EMA in this codebase, with the seed
  convention stated rather than assumed (SMA-seeded at `slow-1`, each leg over its own
  window; exact on a linear ramp, which is why that seed and not another) and the burn-in
  derived (166/124/360, slow leg binding, **393** total for 12/26/9). MACD is the first IIR
  estimator in an all-FIR codebase and the module says so out loud.
- `scripts/run_macd_ladder.py` + `data/macd_ladder_summary.json` + `MACD_RESULTS.md` (a new
  append-only ledger). Census, break-even arithmetic, the three-rung nested ladder, the
  declared sweep, rotation and block nulls, a fill-timing bracket, and the deflated Sharpe at
  three multiplicity counts. Offline, deterministic, seed 0.
- `tests/unit/test_macd.py` (36), `tests/property/test_macd_invariants.py` (9),
  `tests/golden/test_macd_golden.py` + its hand-computed twin (12), and
  `tests/unit/test_macd_ladder.py` (15). The golden runs at MACD(3,7,3) so every alpha is a
  power of two and every value in the walk is a dyadic rational — asserted with `==`, not
  `approx` — and its scenario makes the two rungs hold opposite positions, so a ladder that
  collapses into one rule turns the file red.

### Result (D217)
- **The signal line is the only part of MACD that does anything, and the whole thing still
  dies on multiplicity alone.** R1−R2 = +0.285 long-short against a +0.10 hurdle, holding at
  +0.247 under a stricter fill. All eight zero-line sweep cells land between −0.166 and
  +0.080 against a signal-line median of +0.315, so the separation is structural rather than
  a lucky cell.
- The best cell clears **six of seven** hurdles — ladder deltas, rotation null at the 99.25th
  percentile, block null at the 100th, buy-and-hold (+0.496 vs +0.266 at half the drawdown),
  both halves — and fails only the deflated-Sharpe floor: +0.334 at the fresh count of 42,
  +0.638 at the verdict count of 45,783.
- R2−R3 collapses from +0.163 to +0.042 under one more bar of lag: the middle rung's edge is
  a fill-timing artifact, surfaced only because the implemented fill was disclosed as more
  favourable than the pre-registered one and bracketed instead of argued.
- The 200-MA confluence gate is destructive in every cell and both books (−0.09 to −0.21).
- 0 of 12 cells clear every hurdle, so the pre-registered programme stop applies and Stage 2
  (the costed engine verdict) does not run.

### Added (D217 ADDENDUM — dividend-adjusted returns, 2026-08-24)
- `scripts/run_macd_ladder.py` gains a total-return panel: sidecar dividends laid onto the
  bar grid and reinvested on the ex-date (`r_tr[t] = log((close[t] + div[t]) / close[t-1])`),
  2,285 matched and 0 unmatched. Dividends and fixture prices are both in the split-adjusted
  frame (D75), so `as_declared_dividends` is deliberately not called. **The position series
  is untouched** — the signal still reads the price a trader sees.
- Every cell now reports price-only and dividend-adjusted total return and CAGR, and the
  verdict records hurdle D under both a Sharpe and a total-return reading.
- Six tests in `tests/unit/test_macd_ladder.py`, including the sign check that a long
  receives the dividend and a short pays it.

### Changed (D217 ADDENDUM)
- **The best cell loses to buy-and-hold on money, and the adjustment roughly tenfolds the
  margin**: +53.54% against +70.81% dividend-adjusted, a 17.3-point gap (−1.34pp CAGR),
  where price-only it was 1.5 points (−0.13pp). Its Sharpe advantage is a risk-reduction
  result — half the exposure, −13.6% drawdown against −35.1% — not a return result.
- Hurdle D fails under the total-return reading, 0 of 12. The verdict is unchanged because
  every cell already failed G. The ladder deltas are unmoved: both rungs hold the same kind
  of exposure, so the dividend stream largely cancels inside them.

### Fixed (D217)
- D217's own ledger arithmetic: the declared sweep grid admits **8** (fast,slow) pairs, not
  the 6 counted by eye — (12,13) and (24,26) satisfy `fast < slow`. The grid was not widened;
  the count was wrong. Fresh look count corrected from 34 to 42, which is what the deflated
  Sharpe is computed against, and pinned by
  `test_the_sweep_grid_admits_eight_pairs_not_six`.

### Added (D216 — the tail, the frequency and the fill, 2026-08-24)
- `scripts/run_reversion_tail.py` + `data/reversion_tail_summary.json` + a D216 section.
  Adds a spacing-based tail sampler (≥ M bars apart, ~8× the events blind stepping gives at
  the 99th percentile), a maker-fill arm on `FillAssumption.TRADE_THROUGH`, and an
  asymmetric break-even solver — break-even is a fixed point, not a constant, because the
  take-profit can rest and the stop cannot.
- `tests/unit/test_reversion_tail.py` (40), including the mandatory pair, a subset/strictness
  pin on the fill convention, and a regression pin on `_rate` (see Fixed).

### Findings
- **`p` keeps rising all the way into the tail.** 52.33% → **56.66%** (BTC) and 52.89% →
  **61.43%** (ETH) across the 87.5th → 99.5th percentiles of move size, monotone on both.
  D215's one open thread, closed with a yes.
- **It still does not pay.** The maker arm — the only arm whose costs make a 15m entry
  possible at all — reaches 59.27% and 58.60% against break-evens of 63.77% and 60.76%.
  **The gap narrows from roughly 4× to about 4 points and does not reach zero.**
- **Two cells cleared every hurdle, both on the optimistic bound.** `maker in/out` prices the
  stop as a maker fill; you cannot rest a stop, so those passes are real arithmetic on an
  untradeable fee model.
- **At daily the sign flips.** BTC's top bucket reverts 40.00% — big daily moves continue.
  H3 predicted weaker reversion and got reversal of sign, matching the standard stylised
  fact. Weak claim on n = 120 / 100 and recorded as one.
- **Adverse selection is real in direction but half the predicted size**: +1.46% mean against
  a predicted ≥ 3 points, 7 of 10 cells in the predicted direction.

### Fixed
- **`rate()` returned 1.0 for every cell.** `sum(1 for _, ok in rows)` with no `if ok` counts
  every row, so every bucket read 100.00%, every hurdle "cleared", and the reading function
  announced a positive. No test caught it — the halves function sums bools correctly and
  disagreed with the headline, the same tell as D209. Root cause: it was a **closure inside
  `measure`**, so it could not be imported and was never pinned. Now module-level `_rate`,
  pinned against a hand-counted list, with a companion test requiring the headline to equal
  the sample-weighted blend of the halves.
- **The verdict table paired a taker fill with maker costs**, taking `p` from the population
  that crossed the spread and the cost from the population that rested. It produced a
  spurious pass (ETH 99.5th, +0.67%) that reads −2.16% once corrected. Each tier in `FEES`
  now declares the arm it is coherent with, pinned by test.
- **The test fixture could not test what it was written for.** `_bars` padded every synthetic
  bar with a 0.1% wick, so a limit at the previous close always traded through and the maker
  arm filled 434 of 434 events. Default padding is now zero.

### Added (D215 — is it just mean reversion?, 2026-08-24)
- `scripts/run_generic_reversal.py` + `data/generic_reversal_summary.json` + a D215 section.
  Both arms call the *same* `structure_nulls.continue_from` — one function, not two
  implementations — so the comparison is like-for-like by construction.
- `tests/unit/test_generic_reversal.py` (12), including the mandatory pair: the statistic
  must be flat on a random walk and steep on a series built to revert.

### Findings
- **The staircase survives with the structure deleted.** Bucketing every 8th bar by move
  size reproduces the Fibonacci ladder's shape with no change of character, no leg, no level
  and no gap: 37.8% → 50.9% (BTC), 37.6% → 52.6% (ETH). Slopes +0.10288 and +0.10293 — two
  independent assets to four decimal places.
- **Matched on move size, the structure is worse.** −0.033 and −0.030, outside the ±0.02
  band on the negative side. **H2 falsified in the hypothesis's favour**: the components do
  not merely fail to add, they subtract about three percentage points. Conjecture: D173's
  confirmation lag makes the move stale by the time a touch registers.
- **The slope decays two thirds by 20 bars** — reversion's signature, not a level's.
- **It is a slope, not a level**: even the largest-move bucket reverts only ~51%.
- **Matching the target to the horizon converts the tilt into hit rate and gives it back in
  size**: P(target) 4.5% → 42.4% at 1R, gross R unchanged-to-worse, net R worse.
- **And it ends at 15m regardless**: the predicted move is a 0.5 ATR band worth 0.19%/0.26%
  of price against an 80 bp round trip — **0.24× and 0.32× the cost of capturing it**.


### Added (D214 — the terrain map as a confluence gate, 2026-08-24)
- `scripts/run_structure_terrain_gate.py` + `data/structure_terrain_gate_summary.json` + a
  D214 section. Overrides D203's stop by explicit amendment, recorded before the runner
  existed. Field windows calendar-matched to 15m per D194 and asserted by test.
- `tests/unit/test_structure_terrain_gate.py` (19), including the composition look-ahead
  pair — both inputs are individually guarded and neither says anything about reading the
  field at the signal bar rather than the entry bar.

### Findings
- **0 of 12 cells clear the gross-R hurdle, 0 of 12 beat the shuffle control, and 0 of 12
  clear a Sharpe bar — including the lowest.** Best observed Sharpe −2.28. The three-bar
  distinction never arises: not a result history killed, one that was never there.
- **H2 falsified.** `inverted` did not clear +0.10R despite D202's measured anti-signal —
  though the *direction* held: it averages −0.007R against `aligned`'s −0.038R and wins 5 of
  6 paired cells. The prior pointed the right way at a twentieth of the needed size.
- **In 8 of 12 cells the rejected trades beat the kept ones** (D198 repeating).
- **The grid census was first written as a tautology** that returned exactly zero and could
  not have failed — `Grid.bucket` depends only on `ln_min`, the fixture's lowest low falls
  in the first half, so every bucket index was identical by construction. Rebuilt to perturb
  the axis origin by half a bucket, it shows **5.7% / 4.0% of gate decisions flip**, which
  bounds the precision of any gate on this field and is inside every advantage measured.
- D203's stop is restored; the exception was bounded and is spent.

### Added (D213 — mined selection rule on a held-out seven years, 2026-08-24)
- `scripts/run_structure_selection.py` + `data/structure_selection_summary.json` + a D213
  section. Development year picked on counts before any outcome was read; thresholds frozen
  at that year's medians and never recomputed on a holdout year; mining on gross R so the
  search cannot become a search for wide stops.
- A shuffled-outcome control that runs the identical mining procedure on permuted outcomes,
  which is what makes the in-sample and out-of-sample numbers interpretable.

### Findings
- **Two features survived 2018 — wait longer, higher volatility — and inverted out of
  sample**: +0.489R/+0.265R in sample against **−0.128R/−0.016R** on the seven held-out
  years, negative in 7 of 8 years on BTC.
- **54% of shuffled-outcome draws manufacture a surviving feature** from pure noise, yet
  the real in-sample edge cleared that control's 95th percentile — so 2018 was a real
  pattern that did not persist. Regime, not randomness.
- **`trend_align` was pre-registered and never tested**: a median split cannot divide a ±1
  variable, so it vanished from the table without appearing as a failure — D196's H4 again,
  caught by checking which keys the output contained. Amended, tested standalone, and
  falsified out of sample (+0.012R / +0.087R against a +0.10R bar).
- **After costs the filtered arm returns −1.850R and −1.476R a trade.** An entry filter
  changes which trades are taken, not what the wrapper risks.
- Records the control's own weakness: shuffling independently per symbol destroys
  cross-symbol correlation, so the null is narrower than the true selection distribution.

### Added (worked trade examples, 2026-08-24)
- `scripts/run_structure_examples.py` + `data/structure_examples_summary.json` — extracts
  example trades from the full confluence arm under a selection rule fixed in the script
  before any outcome was inspected: per symbol the best, median and worst by net R, plus
  the pooled highest and lowest cost in R.
- `docs/results/structure_trade_examples.html` + `scripts/build_structure_examples_report.py`
  — the report, reusing `final_report.html`'s stylesheet verbatim so the two are the same
  document rather than two that resemble each other.
- `tests/unit/test_structure_examples.py` (13) pins every number the page quotes against
  its source JSON, including that the stylesheet is still byte-identical to the original's.

### Added (candlestick charts on the examples, 2026-08-24)
- `scripts/build_structure_examples_report.py` now draws an inline SVG candle chart per
  trade — the change of character, the impulse leg, the 61.8% touch band drawn to scale,
  the fair value gap, entry, stop, 5R target and exit. Hollow/filled candles rather than
  red/green: the inherited palette has one accent and it is reserved for what the trade
  turned on. Every colour is a custom property, so the charts follow the viewer's theme.
- `run_structure_examples.py` now stores the full bar window per trade (23–88 bars, from
  before the change of character to past the exit) rather than ±4 bars around entry.
- Seven further tests: one candle per bar against the stored window, nothing drawn outside
  its own frame, no hard-coded colours, every chart marking the structure it illustrates,
  and each chart in its own horizontal scroll container.

### Findings — illustrative, not a verdict
- **The eight-slot rule yields seven trades: the highest-cost trade in either book IS
  BTC's worst.** The worst outcome and the most expensive one are the same event.
- **The worst trade is not a bad prediction, it is a fee bill.** Gross −1.00R, an ordinary
  stop-out; the entry sat 0.038% of price from its stop, so the round trip cost **20.891R**.
  ETH's worst is the same shape at 0.039% and 20.443R, five years and one asset apart.
- **The 61.8% level is a band covering 9.6%–28.1% of the leg on each side.** BTC's best
  trade qualifies as a golden-ratio touch at an actual retracement of **37.8%**.
- **Both best trades are genuine, clean 5R winners.** The strategy is not one that never
  works — it needs 40.2%/33.5% of trades to do that and gets 11.0%/15.4%.

### Fixed (the cost convention, 2026-08-24 — D212)
- `structure_setups.friction_in_r` charged `cost_bps` once for a round trip while
  `structure_strategies.r_multiples` charged it per side — **two halves of one study
  pricing the same tier a factor of two apart.** Per-side is correct
  (`CostTier.fee_bps` is a per-fill exchange fee; `StrategyResult.net_returns` doubles it).
- The suite missed it because `test_the_cost_charged_in_r_matches_the_census_arithmetic`
  compared `r_multiples` to a formula retyped from `r_multiples` — a test named for an
  agreement between two components that never called both. The real pin now exists.
- WP2's friction doubles and the conclusion strengthens: the stacked arm's round trip now
  costs **more than the entire risk of the trade** (1.41R / 1.01R), and the required hit
  rate at 5R rises to 32.7%/28.0% (base) and 40.2%/33.5% (stacked). Nothing in D208/D210/D211
  moves — those rest on zero-cost and rank statistics.

### Added (post-close Sharpe/PnL addendum, 2026-08-24 — D212)
- `scripts/run_structure_pnl.py` + `data/structure_pnl_summary.json` + an addendum section.
  Supplies the sizing rule the R-based study never had (constant unit exposure through each
  trade, `PositionResult` path) so the arms can be reported in Sharpe and money against
  buy-and-hold and cash, at three fee tiers.
- **0 of 16 arms make money at 40 bps/side, and 0 of 16 at 10 bps/side.** Buy-and-hold
  returns +460% (BTC, Sharpe +0.32) and +115% (ETH, +0.11) over the same span. The best
  zero-cost arm returns +1,788% and goes to −9,532 of 10,000 at ten basis points a side.
- Admitted to a closed programme as a descriptive restatement under three pre-stated
  conditions, including that a positive would have required its own pre-registration.
  Ledger 86 → **102 looks**.

### Added (the discretion audit and the close, 2026-08-24 — D211)
- `scripts/run_structure_audit.py` + `data/structure_audit_summary.json` + the WP6 section
  and the FINAL REPORT section of `STRUCTURE_RESULTS.md`.
- **The structure programme is closed after 86 looks.** Across all 8 cells of the
  pre-registered grid the largest rank correlation any feature reaches inside any
  stop-width quintile is 0.10–0.15 against a bar of 0.2; stacking the filters helps at zero
  cost in **0 of 8** cells; the base arm's zero-cost mean R never leaves +0.013 to +0.093.
- WP5 never ran — D210 triggered the pre-registered stop.

### Fixed (the stop was on the wrong side of the trade, 2026-08-24 — D209)
- `structure_setups.stop_price` now returns `leg.start_price`, the extreme the impulse came
  FROM. It previously used `leg.end_price`, which for a long sits ABOVE the entry. The
  wrong-side guard in `run_arm` rejected 1,865 of 2,000 setups and kept an adversely
  selected 135 — a wrong answer converted into a missing one, D205's finding for the third
  time. Surfaced by a count that did not match another count, not by a test.
- WP2's friction table recomputed and its section carries a generated correction banner
  naming the superseded figures. One finding reverses: a deeper entry is a TIGHTER stop, so
  the confluence stack raises friction from 0.48R to 0.71R rather than halving it.
- Two tests pin the stop side in both directions and the `(1 - retracement) x |span|` identity.

### Added (the marginal analysis, 2026-08-24 — D210)
- `scripts/run_structure_marginal.py` + `data/structure_marginal_summary.json` + the WP4
  section. Three readings: feature quintiles on an overlapping annotation population,
  the same features conditioned on depth and on stop width, and the 8-arm ablation lattice.
- `structure_strategies`: MFE/MAE moved into **R units** (scale-invariant, asserted by
  test) after the price-fraction form made `stop_atr` a false candidate at rho +0.56 —
  D187's lesson in a new costume. `run_arm` gained `allow_overlap` for annotation
  populations; the one-at-a-time rule was throwing away 93% of the sample for a rank
  statistic. `expectancy` gained `median_r`, `share_untradeable` and `mean_r_tradeable`
  after mean R came back −104 (correct arithmetic for a position size nobody can take).

### Findings — WP4, 48 looks
- **Nothing survives holding leg size constant.** Three features clear the promotion
  criteria unconditionally and are one quantity under three names (pairwise rank
  correlation +0.79 to +0.88). Inside stop-width quintiles the largest correlation any
  feature reaches is **0.13** against a bar of 0.2, with no sign agreement — depth included.
- **Stacking all four filters makes the strategy worse before costs**: −0.038R and −0.102R
  a trade at zero cost, against the base arm's +0.013R and +0.093R.
- **44% and 32% of base-arm trades are untradeable** at 40 bps — the round trip costs at
  least their entire risk.
- **The pre-registered stop condition is triggered. WP5 does not run.**

### Added (component placebos and the frozen wrapper, 2026-08-24 — D207/D208)
- `research/structure_nulls.py` — the continuation statistic (`terrain_nulls`' reversal
  definition, re-oriented by the setup's direction rather than the approach side), four
  matched placebos, a paired bootstrap, and `DepthTable` for the depth-matched re-reading.
- `research/structure_strategies.py` — the frozen wrapper, identical in every arm. Market
  entry at the close (D207), stop at the swing extreme with D10 gap-through fills and D42
  stop-first ordering, 5R target, channel trail after 1R. Direction-signed excursions, so
  `feature_analysis.analyse_feature` can rank a two-sided book.
- `scripts/run_structure_components.py` + `data/structure_components_summary.json` + the
  WP3 section of `STRUCTURE_RESULTS.md`.
- `tests/unit/test_structure_nulls.py` (22), `tests/unit/test_structure_strategies.py` (16).

### Findings — WP3, no costs, 30 looks
- **One variable explains the whole strategy: retracement depth.** The eight-ratio ladder
  is a strictly monotone staircase in depth. 0.618 ranks **4 of 8** on both symbols and
  loses to 0.691 and 0.724 in 97%+ of paired bootstrap draws. The spread between arbitrary
  ratios is ten times the golden ratio's advantage over them.
- **The depth-matched null takes back the study's only clean pass.** The fair value gap
  falls from +0.082 at the 100th percentile to **+0.006 / −0.006**, because real gaps sit
  at retracement 0.626 against the uniform placebo's 0.444.
- **The flipped level is negative either way**, consistent with D196's S5 result.
- **The change of character fails the both-symbols requirement**: BTC +0.133 delta at the
  66th percentile (below the null's p95), ETH −0.057 at the 43.6th.
- **RSI — the control — is the only arm that survives depth matching.** H6 confirmed.
- The depth-matched null was **post-hoc**, is counted as six further looks, and makes every
  verdict harsher rather than kinder. Disclosed rather than folded in.

### Added (the setup census, 2026-08-24 — D206)
- `research/structure_setups.py` — composes the five detectors into `Setup` objects that
  record, per bar of the pullback window, **which conditions held there**. Any subset reads
  its own entry off the same object, so WP4's 16 arms differ in the filters and in nothing
  else. `SetupPopulation` returns the drops explicitly. Plus `friction_in_r` and
  `required_hit_rate`, pinned against D196/D197's published 0.49R/0.12R pair.
- `scripts/run_structure_census.py` + `data/structure_census_summary.json` + the WP2
  section of `STRUCTURE_RESULTS.md`. Counts only — no return, no Sharpe, 0 looks. The
  section's prose is generated from the payload so the two cannot drift (D176/D183/D186).
- `tests/unit/test_structure_setups.py` (26).

### Findings — counts only, no backtest
- **The round-trip cost is roughly the whole distance to the stop.** 40 bps is 0.40% of
  price; the median C1-only stop is 0.41% (BTC) and 0.56% (ETH), so friction is 0.97R and
  0.72R.
- **The course's arithmetic fails once costs exist.** Its 5R target breaks even at 16.7%
  frictionless and at 23.3–32.9% at 40 bps. **A 20% hit rate at 5R loses money in every
  cell measured.** Independent of whether any component carries information.
- **H5 falsified** — the stacked arm is not underpowered (120 and 106 entries against a
  floor of 30). WP3/WP4 proceed.
- **C5 dropped as a stacked filter on counts alone**: RSI 30/70 collapses the stack to 2
  entries on both symbols. Retained as a continuous feature for WP4a.
- **C3 admits 69–70% of setups on its own** — very little work for a filter, before WP3
  asks whether 0.618 differs from the placebo ratios.
- **The stack's one measurable effect is entering deeper** (retracement 0.32 → 0.54, stop
  1.05 → 1.75 ATR), which halves friction and is not evidence of a signal.
- **The discretion gap, measured**: 340 BTC setups had all three conditions somewhere in
  the window and only 120 had them at the same bar.

### Fixed
- Two guard-shaped defects, both caught by tests written before the run. ATR warm-up was
  punching holes in pullback windows, producing non-contiguous windows whose first bar was
  not the bar an entry became possible; those setups are now refused and counted. And ~9%
  of setups were dropped dead-on-arrival by an `if window:` without being counted — found
  because `SetupPopulation`'s drop arithmetic is asserted to add up.

### Added (the structure detectors, 2026-08-24 — D204/D205)
- `docs/specs/STRUCTURE_MODEL.md` + `STRUCTURE_RESULTS.md` — a new programme and a new
  ledger, opened at 0 looks, on a genuinely new construction: the five components of a
  discretionary retail price-action strategy. Terrain's 259 looks disclosed adjacent.
  Pre-registered before any code existed (D204).
- `research/structure.py` — five INDEPENDENT detectors, no strategy and no thresholds.
  `market_structure` (the BOS/CHoCH state machine, D173's confirmation lag applied),
  `retracement` + `ratio_price` (continuous depth, never a boolean), `fair_value_gaps`
  (three-bar imbalance, filled on the bar RANGE), `rsi` (Wilder's original smoothing, as
  the study's control). `PLACEBO_RATIOS` fixed here: 0.447/0.553/0.691/0.724, the
  non-canonical ratios 0.618 is measured against.
- `tests/unit/test_structure.py` (45) + `tests/property/test_structure_invariants.py` (10).

### Findings — from a mutation pass run because the suite passed first time
- **Two of six deliberate mutations survived 43 green tests.** Mutation 5 dropped the
  higher-low requirement — the pre-registered definition of a change of character — and
  nothing noticed. Mutation 6 introduced a mirror sign error on the bullish leg's start,
  and the degeneracy guard converted it into *missing* legs rather than wrong ones, which
  the sign-of-every-leg assertion satisfied vacuously.
- Both fixed: a planted pattern that separates the higher-low definition from the naive
  one (and its mirror, reflected through a price axis), and leg-endpoint assertions that
  require **each direction to be populated**.
- The general form, recorded in D205: **an invariant asserted only over the outputs a
  component produces cannot see a component that has stopped producing them.** Same shape
  as D196's H4, reached from the opposite direction.
- 1,098 tests green (55 new), mypy `--strict` clean on the new module.

### Added (the volatility estimator gate, 2026-08-23 — D195)
- `research/vol_estimators.py` — the incumbent (20 close-to-close daily returns, pinned by
  test against `InverseVolatilityWeight.weight()` rather than merely resembling it) and the
  candidate (realized vol from 15m returns), plus MSE-on-log-vol, QLIKE and Mincer-Zarnowitz
  R². Both estimators come from the SAME 15m fixture with the daily series resampled from
  it, so provider, span and calendar are identical and the estimator is the only variable.
- `scripts/run_vol_estimator_gate.py` + `data/vol_estimator_gate_summary.json` +
  `docs/results/vol_estimator_gate.md`. Runs in 11 s.

### Findings — predictions committed first (c27e671), then scored
- **The gate FAILS. Step 2 does not run.** Loss reduction on the majors is +15.8% to
  +29.9%, against a pre-registered floor of 30%. BTC's worst cell is short by 14.2 points,
  ETH's by 8.0.
- **H1 FALSIFIED.** Predicted at high confidence that the candidate would win
  *comfortably*. The direction was right on all eight gate cells and the magnitude was not
  — D195 wrote that case down in advance: the effect being smaller than the literature that
  motivated it IS the finding. A floor calibrated on equity data was applied to 24/7 crypto.
  **The floor was not moved after the fact.**
- **H2 FALSIFIED, and the two-target design is why we know.** Predicted the effect would be
  smaller on thin dying coins. Against the accurate target it is LARGER — XEM +32.8%/+55.7%,
  BTG +36.2%/+51.6%, the only cells anywhere clearing the bar. Against the incumbent's own
  basis it goes NEGATIVE: XEM −0.2%, **BTG −29.6%**, a 65.8-point divergence. On a thin
  instrument the candidate predicts *itself* well and predicts reality worse than a
  20-observation estimator. Scored on one target, BTGUSDT would have been the run's
  strongest result; it is the weakest.
- **H3 untested**, since step 2 did not run. Its argument — that the 70%-of-risk-budget
  defect is structural in the weighting rule rather than an accuracy problem with its input
  — is untouched and remains the more likely explanation.
- Real and unused: forecast R² of 20-day-ahead volatility rises 0.2128 → 0.2710 on BTC and
  0.2145 → 0.2938 on ETH. Better estimate, nothing built on it.

### Verified
- 898 tests green (20 new), mypy clean. Every figure in the result section checked against
  the summary JSON programmatically; one R² was quoted at an ambiguous 3 dp and is now 4.

### Added (S1 re-tested at 15m and closed for good, 2026-08-23 — D194)
- `scripts/run_terrain_s1_intraday.py` — the WP2 re-run on exchange-native 15m volume,
  every window calendar-matched to D189 so bar resolution is the only variable. Appends its
  own dated section to `TERRAIN_RESULTS.md` rather than overwriting it, which the daily
  runner does despite the ledger's append-only header.
- `data/terrain_s1_15m_summary.json` — every figure in the result, machine-readable.
- `rolling_mean_true_range` / `rolling_realized_volatility` in `research/terrain.py`. The
  reaction scan recomputed a 1,920-bar ATR per bar: measured at 173 hours for the grid.
  These are linear, build in 0.08 s, and are pinned by test against the per-call forms.
- A bucket-span census on `PriceDensity` (`spans`, `median_span`, `single_bucket_share`),
  pre-registered in D194 as a diagnostic that can invalidate a pass.
- `ATR_WINDOW`, `HORIZON` and `REBUILD_EVERY` are now parameters rather than constants read
  at import; `run_null` never forwarded `horizon` at all, which is fixed.

### Changed
- `VolumeProfileSensor.lookback_days` → **`lookback_bars`**. The field was applied as a bar
  count and named days — harmless on daily bars, a lie at 15m. `LOOKBACK_BARS` extended to
  `(90, 180, 8_640, 17_280)`, with `DAILY_LOOKBACKS` kept as its own tuple so extending the
  set cannot silently change what D189's runner iterates.

### Findings — predictions committed first (d2cc20e), then scored
- **H1 CONFIRMED. S1 fails all three pre-registered conditions.** Primary configuration:
  BTC 89.6th percentile (p = 0.106), ETH 66.4th (p = 0.337). Deltas +0.0068 and +0.0024
  against a floor of 0.045 — **6.6× and 19× short**. Breadth 3/8 and 0/8.
- **The sign flipped, and that is the honest nuance.** D189's real levels sat BELOW their
  null on both symbols; D194's sit above it on both. Intraday attribution produces a real,
  correctly-signed effect — roughly a fiftieth the size needed to be useful.
- **H3 CONFIRMED, and it is why the run was worth doing.** Three BTC configurations cleared
  p ≤ 0.05, one at **p = 0.0080, the 99.4th percentile, on 30,187 touches**. All were
  4.5–7.1× below the effect-size floor, and none was on ETH. Reported alone that cell would
  have read as "S1 works at 15m". Two independent pre-registered guards killed it.
- **The span-matched daily control rules out the era**: D189's configuration on the
  overlapping years is still indistinguishable from random (BTC 22.4th, ETH 51.2nd). It
  also shows how unstable ~250 touches is — the same configuration moved 41.4th → 22.4th on
  BTC merely by dropping the pre-2018 years.
- **The bucket-span census rules out degeneracy**: median span 4.0 buckets, single-bucket
  share 1.3–3.1%. The map is a genuine volume profile, not a close-price histogram.
- **S1 is closed at any resolution** by D194's permanent stop. WP3–WP8 remain unrun.
  Cumulative multiplicity: **147 looks on one hypothesis**.

### Corrected
- **D194's runtime estimate was wrong by 6×** — 0.5 hours predicted, 10,909 s (3.03 hours)
  measured. The benchmark timed the per-bar scan and omitted the per-touch work, and the
  two numbers it lacked were 23.85 levels per rebuild (D189: 3.88) and 13,782 touches per
  scan (D189: 353). Recorded rather than quietly fixed: a 6× miss on a figure stated in a
  pre-registration is the class of unverified number this project keeps catching.

### Verified
- D189's committed summary reproduces **byte-identically** from the refactored code.
- Both synthetic controls re-run at intraday windows: nothing found in a random walk across
  three seeds, planted level still found.
- Precomputed and per-call reaction paths pinned to agree end to end.
- 878 tests green (16 new), mypy clean.

### Added (BinanceDataSource and the first non-yfinance fixture, 2026-08-23 — D193)
- `data/binance_source.py` — assembles monthly 1m archives into a continuous series behind
  `get_raw_history`, the seam every fetch script uses. Verifies each archive against its
  published SHA256 **on every run including cache hits** and raises on mismatch; calls
  `dedupe_seam` at the monthly joins, which is the caller that function was committed
  without. Caches under `data/raw/` (already gitignored).
- `scripts/fetch_binance_fixture.py` + `data/fixtures/crypto_binance_15m_raw.csv.gz` —
  BTCUSDT/ETHUSDT (matching D189) and XEMUSDT/BTGUSDT (delisted, carrying the empty-bar
  problem), 1m resampled to 15m through D161's existing contract. Refuses to write a
  partial fixture unless `--allow-partial`.
- `data/manifests/binance_1m_majors.json` — D191's committed artifact: 279 archives with
  the provider's own SHA256. The 1m base (486 MB cached) is not committed.
- `save_fixture_csv` gained an optional `extra_columns`, threaded through
  `SnapshotStore.create` to `Snapshot.extras`, so the fixture carries base volume, quote
  volume and taker-buy volume side by side rather than deriving one from another (D187).

### Findings
- **A second provider defect, caught by D161's alignment guard on the first real run.**
  From 2017-12-04 06:00:20.799 to 2017-12-18 10:00:20.799 every `BTCUSDT` 1m bar is
  stamped exactly 20.799 seconds past the minute — a constant clock skew, not jitter.
  `ETHUSDT` carries 20.810s; a second episode at ~14.79s runs into February 2018. 17 days
  and 21,602 bars per symbol. The bars are **dropped, not snapped**: a bar labelled
  00:00:20.799 could describe [00:00, 00:01) or [00:00:20.8, 00:01:20.8) and the archive
  does not say which, so rewriting the timestamp would be inventing the answer (D25).
- **The first fix for it was wrong, and the gate caught that too.** Dropping the off-grid
  days made 2017-12-03 and 2017-12-19 adjacent, so fifteen days of the December 2017 rally
  arrived as one bar and the validator correctly called it +69.0% on BTC / +68.4% on ETH.
  The drop policy manufactured the violation. The series is now TRUNCATED to start after
  the last off-grid day rather than stitched across it, costing BTC and ETH 170 good days
  each. The same artifact is latent in the 1h fixture and has only never fired because its
  holes are one day long.
- **The 15m base needed no gate override.** 0 hard violations, snapshot not quarantined,
  7,334 warnings (6,671 `volume_spike`, 658 `zero_volume`, 5 `unexplained_move`). The
  volume rule would have dropped 658 bars — measured by calling `clean()` twice, not
  assumed. D192's and D143's deferrals both stay unspent.
- **Empty-bar rates at 15m**: BTC/ETH 0.000%, XEM 0.195%, BTG 0.788%, against 25.3% and
  44.7% for the same two dying coins at 1m.
- **Reconciliation against the daily fixture over 2,853 days**: BTC median 8.3 bp
  (p90 63.6, max 371), ETH median 9.4 bp (p90 66.2, max 585). Reported, not asserted —
  a single-venue USDT pair and a multi-venue USD index are different instruments (D161).

### Fixed
- **Gzipped fixtures are now byte-reproducible.** `gzip.open` stamps the current time into
  the header, so re-running any fetch produced a whole-file diff — 25 MB of it here — even
  when not one row had changed. Writes now pin `mtime=0` and omit the embedded filename.
  A diff that always appears is a diff that stops being read, and immutable-by-diff
  (D70/D24) is the reason fixtures are committed rather than re-fetched. Reads untouched;
  snapshot ids unaffected, since `bars.csv` inside a snapshot is uncompressed.
- A units bug in `binance_source`'s first draft: the D192 census was being computed against
  a trade count inferred from volume, which would have made "does zero volume agree with
  zero trades" answer itself. It now uses the provider's own `number_of_trades`, and the
  fetch refuses to build a fixture on a symbol where the two disagree.

### Verified
- Three committed fixtures still freeze to their pre-change snapshot ids, pinned as a test
  — the schema extension is provably inert on the default write path.
- Two consecutive full fetches produce a byte-identical fixture.
- A tampered cached archive is refused by name, identified as stale rather than corrupt.
- 862 tests green (49 new), mypy clean.

### Added (the Binance archive, probed before anything is built on it, 2026-08-22 — D190/D191/D192)
- `data/binance_archive.py` — pure, offline parsing for Binance's public flat-file
  archives. The epoch unit is DETECTED per file, not configured: the archive switched kline
  `open_time` from milliseconds to microseconds at 2025-01, and a reader that assumes
  milliseconds dates a mid-2025 bar to the year 57,400. Base and quote volume are carried
  separately in the provider's own units and neither is derived from the other.
- `scripts/probe_binance_archive.py` — the network probe. Writes no fixture and no
  snapshot; produces `data/binance_probe_summary.json` and a report rendered from it, with
  `--report-only` re-rendering offline. Retention and size come from S3 listings, so only a
  stratified sample of archives is actually downloaded.
- `docs/results/binance_provider_probe.md` — the findings.
- `tests/unit/test_binance_archive.py` — 38 offline tests plus one `live_fetch` smoke test
  that deliberately picks a month AFTER the microsecond switch.

### Findings
- **Retention: 108 monthly archives of 1m bars for BTC and ETH, 2017-08 to 2026-07**,
  against the 730 days of 1h yfinance serves. D163 refused any return claim below 1h
  because 60 days cannot hold a 252-day training window; that constraint does not bind here.
- **Zero-volume rate is 0.000% on every sampled month from 2022 onward**, against D160's
  17,520-of-34,923 on yfinance hourly bars.
- **The zero bars that do exist are TRUE, and the column that proves it is
  `number_of_trades`.** In every sampled month on every symbol, the zero-volume bars and the
  zero-trade bars are the same bars exactly — 25,878 of each on `BTGUSDT` 2022-01. That is
  the market saying nothing traded, not a feed defect, and it is the opposite of D160's case.
- **On dying coins a 1m time grid is majority-empty**: 57.97% on `BTGUSDT` 2022-01, 56.68%
  on `XEMUSDT` 2022-09. Since the failure universe is the only screen in this project that
  ever caught anything (D140/D180), this constrains the bar definition of any intraday
  study, and D192 declines to choose it before a pre-registration does.
- **The units cross-check D187 did not have passes on 100.0000% of bars** in every sampled
  month: quote volume ÷ base volume lands inside the bar's own high–low range.
- **The daily crypto fixture gets its first independent check.** Binance 1m resampled to
  UTC days agrees with it to a median 9.6 bp on BTC and 14.8 bp on ETH over May 2021.
  Volume does not reconcile and should not — global USD notional against single-venue base
  units, which is the same distinction D187 got wrong in the other direction.
- **58 of 63 universe coins are reachable, and the 5 that are not are not random**: `OKB`,
  `HT` and `CRO` are rival exchanges' tokens. A single-venue archive applies a selection
  screen the yfinance roster did not, and that is recorded rather than absorbed.
- **6.34 GB of 1m archives, 952x the largest committed fixture and 367x the whole `.git`.**
  Checksum coverage is 100% across all 58 symbols, which is what makes D191's manifest-only
  policy available rather than merely appealing.

### Fixed
- A local-time bug in the archive parser, caught before it reached a result:
  `datetime.fromtimestamp(x, tz=None)` reads the epoch in the machine's zone, so the same
  archive would have parsed differently in London and New York and the fixture would have
  depended on who ran the fetch.

### Added (Phase 3: the S1 terrain sensor and its null, pre-registered, 2026-08-22 — D189)
- `research/terrain.py` — the terrain sensor interface, frozen for every later sensor, plus
  `VolumeProfileSensor` (S1). `PriceDensity` returns None outside the mapped range rather
  than 0.0; a bar's volume spreads across the buckets its RANGE covers rather than landing
  at its close. Lookback/bucket/volume-units all raise outside the spec's stated sets.
- `research/terrain_nulls.py` — the reusable null-test harness. Touch and reversal
  definitions fixed in the docstring before any run; reuses `MetricSpec`/`summarise_null`
  from D130 so every metric declares its own tail.
- `TERRAIN_RESULTS.md` — the programme's append-only ledger, carrying the multiplicity count.
- Look-ahead guarded HERE rather than inherited: D181 established `DataView` protects
  strategies and not analytics built on their output, and a sensor is analytics.

### Findings — predictions committed first (e2a8b09), then scored
- **S1 FAILS its null on all 16 configurations, all 3 metrics, both symbols.** At the
  primary config (180d, 0.5 ATR, k=0.5): BTC P(reversal|touch) real +0.3768 against a null
  mean of +0.3835 — the **41st percentile**; ETH +0.3529 against +0.3736, the **26th**.
  **On the metric the model rests on, real levels reverse price LESS often than random
  ones.** Traversal and volatility sit mid-null and in the wrong tail.
- **H1 confirmed**, against the spec's own prior that S1 is the lead sensor expected to pass.
- **The terrain programme STOPS at WP2** by its own stated condition. WP3-WP8 do not run:
  S1 was the strongest sensor on the spec's assessment, S2 is marginal and expected to fail,
  and S3 has zero independent validation in the literature.
- **The mandatory false-positive check passed first time** — on a pure random walk across
  three seeds the harness finds nothing.
- **The positive control failed twice and the FIXTURE was wrong both times.** A drift of
  `-0.9*gap` pushes price TOWARD the level, building a magnet rather than a wall; the
  harness correctly reported the planted level as worse than chance. Flipping to `+1.2*gap`
  built a wall price never returned to — one touch in 1,500 bars. The harness caught both.
- `docs/specs/` is now complete: every phase either delivered or closed by its own criterion.


### Added (the ETF cross-section, pre-registered, 2026-08-22 — D188)
- `scripts/run_etf_universe.py` — the SAME long baseline, unchanged, on 57 ETFs.
  `periods_per_year=252`, `volume_units="shares"` (D187), dividends PAID on both arms
  (2,285 across 53 symbols + 14 splits), two crypto-specific screens disabled with the
  measurement behind each. Two cost tiers fixed in advance: equity (IBKR + 1bp) and the
  crypto 40bp as a stated handicap. Impact off — this asks whether the effect exists, not
  what it costs at size.
- `actions` threaded through `run_variant`, all three benchmark runners and
  `run_universe_study`, mirroring the volumes pattern; `_context_for` now serves both
  data-dependent bricks. Dividends are not optional: on SPY alone they move the strategy
  from +0.060 to +0.171 Sharpe, and omitting them would flatter the STRATEGY, which is
  flat about half the time and collects fewer than the benchmark.

### Findings — predictions committed first (cac1c45), then scored
- **The portfolio does NOT transfer. H1 confirmed emphatically.**

  | | Sharpe | Return | Max DD |
  |---|---|---|---|
  | Strategy (equity costs) | **-0.273** | +21.6% | **6.1%** |
  | Equal-weight basket | +0.395 | +100.5% | 33.4% |
  | SPY buy & hold | +0.617 | +187.0% | 33.7% |

  **Edge -0.667**, against +0.075 on crypto. At the crypto 40bp tier, -1.190 and the book
  returns -0.5%. Turnover 0.4x/yr: the breakout condition barely fires on an index fund.
- **H2 confirmed** — max DD 6.1% vs 33.4%. The drawdown property has now survived every
  test in this project and is the only claim that has. Read for what it is: a book invested
  a fraction of the time has a small drawdown for the same reason it has a small return.
- **H3 FALSIFIED, and its failure is the finding.** I predicted the diversification lift
  would reproduce, calling it "arithmetic, not a market claim". The portfolio Sharpe
  (-0.273) is BELOW the median single ETF (-0.177) — the lift **reversed**.
  **Sharpe is mean/sigma: averaging shrinks sigma, so it raises the Sharpe when the mean is
  positive and makes it MORE NEGATIVE when the mean is negative.** Diversification is a
  magnifier with the sign of the expectancy, not free arithmetic. D183 called the lift
  guaranteed; it is conditional on a positive mean, which is the entire question.
- **This was the easier test.** All 57 ETFs survived — identical spans, no delistings — the
  opposite property to the crypto universe, which was built to contain the assets that died.
  The strategy lost on the friendlier sample by 0.667 Sharpe.
- **Still untested, and now the deepest assumption in the project:** both samples are
  2015-2024. A different asset class is not a different era, and that cannot be fixed with
  data already on disk.


### Fixed (volume units in the impact model, 2026-08-22 — D187)
- **`SqrtImpact` divides an order QUANTITY by ADV, and `calibrate_impact_params` never
  asked what the volume column counted.** The ETF fixture reports SHARES (SPY 68.1M, x $474
  = $32bn/day); every crypto fixture reports QUOTE-CURRENCY NOTIONAL (BTC 47.5bn, which
  cannot be coins). So every crypto charge was off by sqrt(price): BTC's ADV was 21,970x
  too large (impact understated ~148x), LUNC's 1,585x too small (overstated ~40x). **The
  same run was wrong in both directions at once.**
- `calibrate_impact_params` now takes `volume_units` in `("shares", "quote_notional")` and
  **raises** on anything else — there is no safe default to guess with. `"shares"` stays
  the default, so the pairs study's published trials are untouched. Conversion is bar by
  bar, `mean(volume_t / close_t)`, not mean-notional over mean-price.
- **A second bug, found only because the fix required an alignment assertion.** All three
  benchmark runners were handed a SLICED bar series with a FULL-LENGTH volume series
  (`ADA-USD`: 2,974 volumes against 2,709 bars), introduced the day before when volumes
  were first threaded to them. Without the assertion it would never have raised — ADV would
  have been calibrated over a longer window than the bars it priced, quietly, in the
  direction of understating impact.
- Both study summaries remain byte-identical; `volume_units` is emitted only alongside the
  impact brick.

### Findings — D186 corrected
- **Capacity moves from ~$30M to ~$66M.** Edge: +0.075 at $100k (was +0.067), +0.047 at
  $10M (was +0.014), -0.014 at $100M (was -0.026).
- **"Two long books destroyed by impact" is WITHDRAWN.** `LUNA1-USD` and `LUNC-USD` are
  sub-cent coins whose impact was overstated ~40x. With the units right, **no book is
  destroyed at any size tested**.
- **H1 is now FALSIFIED by 0.001**: Sharpe falls 0.099 against a predicted >0.10. Called as
  written rather than left as yesterday's confirmation.
- **H2 still confirmed, and the concentration mechanism is stronger**: the strategy loses
  10x more Sharpe to impact than the benchmark (0.099 vs 0.010), up from 5.3x.
- **I predicted the correction would move capacity DOWN and it moved up.** BTC and ETH see
  impact rise 148x and 29x — but they are 2 of 62 in an equal-weight book, and most of the
  universe trades below $1 where impact was OVERstated. Same error class as D185: a correct
  mechanism applied to the wrong population.


### Added (capacity, pre-registered, 2026-08-22 — D186)
- `CostTier.impact_coefficient` wires square-root market impact (D66) into the breakout
  cost tiers, reusing `SqrtImpact` and `calibrate_impact_params` from the equities pairs
  study. **The D166 rule, fifth application**: the `sqrt_impact` brick is ABSENT when off,
  not present with coefficient zero, so every config hash in both studies is unchanged.
- `CostTier.build()` takes an optional `StackDataContext` and raises if impact is on
  without one; a new `_context_for` helper is the single place all four build sites ask
  "did anyone pass the volumes".
- `scripts/run_capacity_portfolio.py` sweeps $100k-$100M, per-coin slice AUM/62, at the
  reference tier, with the benchmark charged impact on the same terms.
- `run_universe_study` gains `compute_dsr` (only the capacity sweep passes False).

### Findings — predictions committed first (6a9529e), then scored
- **BOTH CONFIRMED. Capacity is ~$30M of total AUM (~$484k per coin).** Edge over the
  equal-weight universe: **+0.067** at $100k, +0.051 at $1M, +0.014 at $10M, **-0.000 at
  $30M**, **-0.026 at $100M**.
- **H1 confirmed narrowly**: strategy Sharpe falls +1.240 -> +1.124, a loss of 0.116
  against a predicted >0.10.
- **H2 confirmed, and for the predicted reason.** The strategy loses **5.3x more Sharpe to
  impact than the benchmark** (0.116 vs 0.022) despite the benchmark turning over 2.7x
  more. Volatility normalisation did not rescue it — the mechanism the pre-registration
  named — because the strategy's impact CONCENTRATES in the thin coins it trades while the
  benchmark spreads turnover across all 62. **First time a mechanism-first prediction here
  was right about both the mechanism and its consequence.**
- **Two long books destroyed by impact alone** at $30M+: `LUNA1-USD`, `LUNC-USD`. No long
  book dies at zero impact (D183). Also the model's own edge: a sqrt-impact charge large
  enough to bankrupt an account is outside the range D66's form was fitted for.
- **Deflated Sharpe = 0.9996** at $100k (30 trials, V[SRn] read from the long study's
  published inputs, not asserted). **It should not be quoted alone**: DSR deflates against
  a trial pool, not a benchmark. At $30M the strategy and the benchmark both score +1.161
  and the DSR would still be high — it measures crypto beta surviving a multiplicity
  correction, not skill surviving one. Skew +4.76, kurtosis 106.7.
- **All three of D183's debts are now paid**; the honest summary is an equal-weight crypto
  basket with a breakout overlay, at a third of the basket's drawdown, with an edge that is
  small at $1M, marginal at $10M and gone at $30M.

### Fixed
- `run_universe_study` accepted `volumes_by_symbol`, used it for the policy screen and
  **never handed it to the run**. Harmless until a cost tier needed ADV, at which point it
  became a loud failure — which is the only reason it was found. Volumes now passed
  unconditionally to `run_variant` and to both benchmarks; verified byte-identical on the
  existing portfolio study before anything downstream was trusted.
- `dated_returns` tested `a <= 0.0` for account death, which is False for NaN. Impact large
  enough to exceed a position's notional produces exactly that; in the one observed case
  NAV went negative several hundred bars before it went NaN, so the loose guard happened to
  catch it. Now `not (a > 0.0) or not isfinite(b)`.


### Added (rebalancing cost charged, pre-registered, 2026-08-22 — D185)
- `_equal_weight_arm` now returns one-way TURNOVER alongside the gross series, and the
  portfolio study charges it at the project's existing 0/10/25/40bp ladder. **The benchmark
  is charged too** — the equal-weight universe rebalances daily as well, and charging only
  the strategy would rig the comparison. Buy-and-hold pays nothing after its first purchase.
- Break-even solver: the cost at which the strategy's Sharpe edge over the benchmark
  reaches zero, by bisection, reporting "none" rather than interpolating a number that does
  not exist.
- The two D184 artifacts are neutralised in the benchmark only; the strategy is untouched
  by both.

### Findings — predictions committed first (32fd7a2), then scored
- **The cost barely touches the result. Both predictions FALSIFIED.**
- Annual turnover: strategy **1.8x**, equal-weight universe **4.8x**, BTC buy & hold 0x.
- Net Sharpe at 40bp: strategy **+1.252** (from +1.277), benchmark **+1.174** (from
  +1.196), BTC +1.096. **Edge +0.081 -> +0.078.** Break-even **972bp**, about 24x the
  reference tier.
- **H1 falsified**: predicted the strategy would drop below +1.00 at 40bp; it drops 0.025.
  1.8x turnover at 40bp one-way is 0.72%/yr against ~25% vol.
- **H2 falsified as stated**: the edge narrows very slightly rather than widening, and a
  break-even exists. The turnover half of the reasoning was right — the 2.7x asymmetry was
  predicted and observed, for the predicted reason (flat books do not drift).
- **The error is the normalisation, and it is worth keeping.** A cost's damage to a SHARPE
  is `cost / volatility`. The benchmark turns over 2.7x more and pays the same Sharpe
  penalty because it is 3.4x more volatile. Turnover and volatility scale together, so the
  comparison is near cost-invariant. **In RETURN terms the intuition does hold**: the
  strategy gives up 7% of total return at 40bp, the benchmark 17%.
- Drawdown is untouched: 28.8% -> 29.3%.
- **D183's largest stated threat is now paid.** Two debts remain: a deflated Sharpe against
  the 30-configuration pool, and an out-of-sample cross-section. And a turnover charge is
  not a liquidity model — capacity in small-cap alts is the next and harder question.


### Fixed (unrecorded corporate actions, 2026-08-21 — D184)
- **A benchmark returned +102,682,123%, and it came from ONE bar.** `HT-USD` printed
  **+3,398,300%** on 2025-03-12 (close 0.0000150 -> 0.5098, then flat at ~0.50): a
  price-scale defect, not a market move. Neutralising that single bar takes the benchmark
  to +70,139% — a factor of **1,464x** from one day, because daily rebalancing compounds
  it forward.
- **`AAVE-USD` +10,189% on 2020-10-03 is the LEND->AAVE 100:1 token migration** — a genuine
  redenomination that no split adjustment handles. The preceding bar also carries a zero
  open and zero low.
- **The events file is empty.** `crypto_universe_2015_2025_raw_events.json` has `dividends`
  and `splits` for all 63 symbols and every list is `[]`. The machinery is wired and has
  nothing to apply.
- **Four scripts passed an empty corporate-actions object rather than loading it** —
  `run_swing_universe`, `run_e1_universe`, `run_combined_universe`, `run_portfolio_universe`.
  Now fixed. Verified a genuine no-op: every field of the portfolio payload is identical
  after the change, and only the content-addressed snapshot id moves.
- **The strategy results are NOT contaminated.** Long portfolio return on 2025-03-12:
  **+0.0127%**; on 2020-10-03: **+0.0860%**. D103's next-open fill means a one-bar gap
  cannot be entered — the strategy arrives after the jump while buy-and-hold holds through
  it. The defect inflates the BENCHMARK far more than the strategy.
- **D143's validator override is now costed.** Its reasoning stands (the >60% gate deletes
  the failed assets and hands back survivorship bias), but an override with no follow-up
  inspection accepts unknown defects, and the follow-up had never been done.

### Added (benchmarks for D183, appended to that record)
- **Like for like, daily-rebalanced strategy vs daily-rebalanced equal-weight universe, the
  breakout rule is worth +0.084 Sharpe (full span) and +0.194 (>=5 coins live)** — not the
  +0.49 the naive single-coin comparison suggested. Daily rebalancing alone is worth +0.21
  Sharpe on the benchmark (+1.191 daily vs +0.978 monthly), charged nothing.
- Conservative span: strategy +0.927 Sharpe / +316% / **22.9% max DD**, against BTC buy &
  hold +0.786 / +1,087% / 76.6%, equal-weight true buy & hold +0.651 / +438% / 87.7%.
- **The drawdown result is the real one** — a quarter to a third of every benchmark, and
  not explained by diversification, since the equal-weight universe is equally diversified
  and draws down 81%. Being flat about half the time is what does it.
- **The return result is unfavourable**: 15% of buy-and-hold BTC over the full span.
- Correct summary: roughly the return of an equal-weight crypto basket, at a quarter of its
  drawdown, with a small Sharpe edge over that basket rebalanced identically — and the
  +0.084 sits inside the range an un-charged turnover cost could erase.


### Added (cross-sectional portfolio, pre-registered, 2026-08-21 — D183)
- `scripts/run_portfolio_universe.py` — a long/short portfolio ACROSS the 62-coin
  universe. Each date, the long portfolio earns the equal-weighted mean of every live long
  book, likewise the short; the two are combined at D181's expanding inverse-vol weights.
  Return aggregation, not a portfolio backtest. Own registry, no multiplicity added.
- Books that wipe out are truncated at NAV zero. Once NAV is negative `b/a - 1` is not a
  return and averaging it would propagate nonsense across every other coin. Stricter than
  the per-symbol studies, still not a liquidation model (D175).

### Findings — predictions committed first (9dbd2d6), then scored
- **H1 CONFIRMED, narrowly.** Long portfolio Sharpe **+1.278** (total return +2,913%, max
  DD 28.8%) against **+0.437** on the median single coin. But the pre-registered robustness
  check bites: restricted to dates with >=5 coins live, it is **+0.928** — clearing the
  predicted +0.90 bar by 0.028. **A third of the headline was the thin 2015-2017 sample.**
  Still more than double the median single coin, so the diversification claim survives even
  though the headline does not.
- **This is the first thing in this project that has worked.** It is also the least
  surprising, because it is arithmetic: it operates on the return DISTRIBUTION rather than
  on one book's timing, which is what every failed rule tried to do.
- **H2 CONFIRMED, three times more strongly than per symbol.** Adding the short portfolio
  costs **-1.170** Sharpe (D182's per-symbol cost was -0.382) and takes total return from
  +2,913% to +54%. On the breadth-conditioned sample the combined book is NEGATIVE.
  The pre-registered counter-mechanism — that aggregation would fix the short book by
  making it continuously held — is refuted: it is continuously held here and subtracts more.
- **D181's weighting flaw gets WORSE at portfolio level.** Mean long-portfolio weight
  **0.302** — the losing leg carries 70% of the risk budget, against 61% on BTC alone.
  Pooling 62 coins diversifies the short arm's returns, lowering its measured volatility,
  which inverse-vol rewards with MORE weight. **The construction pays a book for being
  diversified and for being absent.**

### Fixed (in this study's own reporting, before publication)
- The weighting paragraph asserted that aggregation would make D181's flaw bite LESS. It
  was written before the run and is the opposite of what happened; it is now derived from
  the payload rather than hardcoded.
- The breadth table was labelled "books with a position open" and actually counts books
  LIVE IN THE SAMPLE — a flat book contributes a 0.0 return and was counted. Label fixed,
  and the exposed gap stated: **position-level breadth is not measured**, which bears
  directly on whether daily equal-weighting is realistic.

### Owed before +0.928 is a result rather than a number
- The rebalancing cost between coins, which this study does not charge and which
  daily-rebalanced equal weight maximises. The largest single threat to the finding.
- A deflated Sharpe: the underlying baseline survived a 30-configuration search.
- Its own out-of-sample test. One crypto cross-section over one bull-dominated decade is
  exactly the sample-shaped problem D180 exists to warn about.


### Added (combined book on the D140 universe, pre-registered, 2026-08-21 — D182)
- `scripts/run_combined_universe.py` — the long+short combined book across 62 coins,
  per-symbol, no rule attached. The baseline that had never been measured. Own registry,
  no multiplicity added; the long arm is `breakout_universe.baseline_variant()` itself.

### Findings — predictions committed first (b75e2e3), then scored
- **H1 CONFIRMED on both clauses.** The combination scores a LOWER Sharpe than the long
  book alone on **57 of 62 coins** (8% win rate, mean Δ -0.382) and a SMALLER max drawdown
  on 68% (mean -4.7pp). On the 19 survivors it is worse on every single one.
- **Absolute P&L is the headline.** Median total return: long **+123.2%**, combined
  **+5.7%**. Profitable symbols 51/62 -> 34/62. Mean Sharpe +0.392 -> **+0.010**.
  Combining destroys ~118pp of median return and 17 profitable symbols to buy 4.7pp of
  drawdown. BTC alone: +4,672% long vs +197% combined.
- **H2 CONFIRMED more strongly than predicted.** Correlation is within +/-0.2 on **62 of
  62** coins, and the largest absolute correlation anywhere is **0.0023** — three orders of
  magnitude inside the brief's ~0.2 target. And combining still costs 0.38 Sharpe on 92% of
  coins. The correlation is MECHANICAL (the short book is flat ~85% of bars, so the legs
  rarely have simultaneous exposure) and **the ~0.2 target is retired as evidence**.
- **The drawdown benefit is real, scales correctly, and inverts in the tail.** By long-book
  drawdown quartile the mean Δ runs +1.0pp (Q1) -> -8.3pp (Q4), monotone. But drawdown got
  WORSE on 20/62, led by `LUNA1-USD` at 21.2% -> **74.5%** (+53.3pp): the long book
  returned +1,298% there and the combination -5%. The hedge smooths ordinary drawdowns and
  amplifies the one that would end the account.
- **D181's weighting flaw, now measured.** Median long-leg weight 0.456; the long leg holds
  a MINORITY of the risk budget on 47/62 coins. corr(long weight, Δ Sharpe) = **+0.604**
  while corr(long weight, short-leg Sharpe) = **-0.043** — the allocator sizes on how often
  a book trades, not on how good it is. On LUNA1 it gave 81% of the budget to the leg about
  to lose more than the account.
- Weighting fell back to 50/50 on **0.8%** of bars, against 75% for the 63-bar trailing
  window D181 rejected.
- Not a portfolio result: per-symbol combination asks whether pairing one coin's two books
  helps, not whether a cross-sectional long/short book works.


### Fixed (ensemble weighting look-ahead, 2026-08-21 — D181)
- **`combine_books`/`combined_series` set their inverse-vol weights from WHOLE-SAMPLE
  volatility and applied them from bar 0.** The calmer leg got exactly the right weight in
  advance. Mild - two scalars, no per-bar leakage, no effect on either leg's trades - but
  every published combined Sharpe was inflated by it, and it was undocumented.
- D44 already required vol to be measured on a window ending at the PREVIOUS bar. The
  structural guard (D32/D56) never applied because the ensemble operates on return series
  rather than a `DataView`: **the guard makes look-ahead impossible for strategies and
  does nothing for analytics built on their output.**
- Now an EXPANDING window with a 252-bar warm-up (`ENSEMBLE_MIN_BARS` = `train_size`),
  using Welford's online variance so it stays O(n) - the naive version is O(n^2) and would
  make the 62-symbol universe run intractable.
- A 63-bar TRAILING window was tried first and rejected by its own diagnostics: the short
  book is flat on 88% of BTC bars, so the window was entirely flat and fell back to 50/50
  on **75%** of bars - an "equal-vol" book that was equal-CAPITAL three times in four.
  That also explains why removing the look-ahead first appeared to RAISE BTC's combined
  Sharpe 0.412 -> 0.685; the fallback was flattering it.
- `combine_books` no longer takes `min(len(a), len(b))` and slices from the end - it
  raises on unequal spans. A no-op today (both books produce identical spans) and a silent
  misalignment the first time that stopped being true.
- All three arms are now scored over the same post-warm-up span; `EnsembleResult` gains
  `short_max_drawdown`, `n_warmup_bars`, `n_fallback_bars` and `mean_long_weight`.
- New test: the weight applied at bar t is unaffected by returns at bar t or later. That
  single property is the definition of the bug and nothing asserted it.

### Findings
- Corrected combined Sharpe: BTC 0.412 -> **0.462**, ETH 0.649 -> **0.570**.
- **D179's conclusion is downgraded** (CORRECTION appended there): BTC's bootstrap
  interval now SPANS ZERO, [-0.008, +0.231]. "Both intervals exclude zero" was that
  record's load-bearing claim; one does.
- **ETH's short leg reads +0.142 over the full span and -0.228 once the first 252 bars are
  dropped.** Its positive Sharpe lived entirely in the 2018 bear market.
- **NOT fixed, now reported instead:** mean weight on the long leg is 0.389 (BTC) / 0.453
  (ETH) - the majority of the risk budget sits on the leg that is flat ~85% of the time
  and loses money, BECAUSE it is flat. Inverse-vol reads a flat book as low-risk when what
  it is, is absent. Surfaced via `mean_long_weight` on every combined result.
- `data/breakout_study_summary.json` byte-identical - the long book has no ensemble, so
  that was the decisive regression check.


### Added (E1 on the D140 universe, pre-registered, 2026-08-21 — D180)
- `scripts/run_e1_universe.py` — E1 vs no-E1 on BOTH books across the 62-coin D140
  cross-section, k=3 fixed, four runs, own registry so no published DSR moves. The long
  control is byte-identical to `breakout_universe.baseline_variant()`.
- Ties counted as ties: E1 is an added brick rather than a swapped one, so win rates are
  over firing symbols only and both denominators are reported. (It fired on all 62, so
  this turned out not to bind.)
- `--report-only` re-renders the report from the saved payload without re-running four
  walk-forwards.

### Findings — predictions committed first (494450e), then scored
- **All three predictions FALSIFIED, one of them reversed.** Long book 39% win rate
  (mean Δ Sharpe -0.065), short book 48% (-0.010). H3 predicted the gain would be LARGER
  among the coins that died; the long book runs monotonically the other way — survived
  -0.022, collapsed -0.081, delisted -0.144.
- **The four published BTC/ETH numbers reproduce exactly** (+0.101/+0.177 long,
  +0.061/+0.101 short), so this is not a measurement difference.
- **Absolute P&L, long book:** median total return +152.4% -> +97.6%, profitable symbols
  52 -> 50, mean Sharpe +0.411 -> +0.346, for 2.1pp less drawdown.
- **The damage is predicted by E1's trade-count growth (-0.72), NOT by volatility
  (+0.06)**, baseline Sharpe (-0.02) or history length (-0.03). Symbols where E1 added
  <=10% trades: mean Δ +0.055. Where it added >=40%: mean Δ -0.220.
- **The firing rate is ~+30% on everything** and is not predicted by any instrument
  property. What varies is the COST per firing: bucketed by baseline trade count, mean Δ
  runs -0.091 (9-17 trades) -> -0.028 (25-42), monotone, while the firing rate stays flat.
- **BTC sits at the 97th percentile of baseline trade count and ETH at the 85th**, median
  21 — the top quartile is the one E1 damages least. They rank 9th and 3rd of 62.
- **E1 is not noise.** Max drawdown improves on 42/62 long and 39/62 short, mean -2.1pp.
  It is a real risk reducer whose price exceeds its payoff outside two instruments.
- **The re-entry attribution is settled against D177.** E1 raised the trade count on 61/62
  long symbols, and that rise correlates -0.72 with the outcome. Re-entry is the mechanism
  of E1's HARM, not its benefit; it looked like a benefit only where re-entry was cheap.
- **D179's arithmetic stands, its interpretation does not.** Both bootstrap intervals
  excluded zero on a sample now shown to be the rule's best case. A confidence interval
  quantifies sampling error within a sample; it cannot detect an unrepresentative one.


### Added (E1 on the combined book, 2026-08-21 — D179)
- A second long leg carrying `failed_breakout` at k=3, so the LONG+SHORT ensemble can be
  measured with E1 on both legs against the same ensemble without it. `COMBINED_E1_K = 3`
  — the stronger k on both books in D178, used on both legs rather than tuned per side.
- `_combined_e1_block` in the breakdown report, and a `combined_e1` entry in
  `data/breakdown_study_summary.json`.

### Findings
- **The first ensemble improvement in this project whose interval excludes zero.** BTC
  combined Sharpe 0.412 -> 0.526 (+0.114, 90% CI [+0.002, +0.219], P=95.4%); ETH 0.649 ->
  0.845 (+0.197, 90% CI [+0.063, +0.362], P=99.5%). Every prior ensemble claim either
  spanned zero or was negative.
- **The gain is not from correlation.** Correlation moves ~0.001 or less on both symbols.
  It comes entirely from improving both legs while leaving their independence intact —
  which is exactly the channel through which the vol-weighted combination could have got
  worse while both components got better.
- **Drawdown improves alongside Sharpe**: combined max DD 34.0% -> 29.5% (BTC) and 29.5%
  -> 24.4% (ETH). The long leg's own max DD falls 43.0% -> 29.2% on BTC.
- **No new multiplicity.** The E1 long leg's config is byte-identical to the long study's
  registered `exit_e1_k3`, and both long legs run outside the short book's registered
  loop. A different reading of trials already paid for.
- Still the same two instruments throughout. The honest next test is unchanged from D178:
  E1 vs no-E1 on the D140 universe, 62 coins.

### Fixed
- The combined-E1 comparison was computed inside the variant loop, where `results_by_key`
  is only partly populated (`exit_e1_k3` is appended last) — the `is not None` guard
  silently skipped the whole section, so the first run produced NO tables rather than
  wrong ones. Moved after both loops and the silent skip replaced with a loud
  `AssertionError`.


### Added (cross-book test, pre-registered, 2026-08-21 — D178)
- `exit_swing_k2` / `exit_swing_k3` on the LONG book, and `exit_e1_k2` / `exit_e1_k3` on
  the SHORT book — each rule on the side it was NOT developed on. Both k tested on both
  sides, because testing only the winning k would repeat D173's actual error. E1 is not a
  stop, so on a short it rides alongside the incumbent channel stop the baseline carries
  and the delta prices E1 alone.

### Findings — predictions committed first (80dab52), then scored
- **H1 holds literally and is misleading if left there.** `swing_k2` fails the long book
  (+0.100 BTC, **-0.075** ETH) as predicted — but `swing_k3` CLEARS it (+0.015 / +0.148).
  The family transfers; the parameter does not.
- **The k FLIPS between books.** Short book: k2 wins, k3 does not (D173). Long book: k3
  wins, k2 does not. The pivot lookback is a property of the BOOK; the rule family is a
  property of the RULE. Carrying the number across is what fails.
- **H2 FALSIFIED.** E1 clears the every-symbol bar on the short book at BOTH k (+0.020 /
  +0.059 at k=2, +0.061 / +0.101 at k=3). H2 rested on attributing E1's long-book benefit
  to RE-ENTRY; trade counts say otherwise (35->39 BTC, 27->28 ETH). **E1's benefit is not
  re-entry, it is not sitting in a failed trade** — a real secondary mechanism mistaken
  for the primary one, the same class of error as D173.
- **E1 is now the strongest rule in this project**: four independent every-symbol passes,
  both books, both k, direction-agnostic by construction. Not adopted — pools grew to 30
  (long) and 27 (short) and both DSRs moved to pay for it. The honest next test is the
  D140 universe, as D174 did for the swing stop.


### Added (Phase 1.5 exit signatures, 2026-08-21 — D177)
- **`FailedBreakoutExit(k)` (E1)** — exits when the close falls back INSIDE the channel
  the entry broke, within k bars. Never built before, despite the doc calling it
  "highest priority" and a predicted survivor. `OpenPosition` gains
  `entry_channel_level`: the boundary that was BROKEN, distinct from `stop_level` (the
  opposite boundary) and `entry_reference` (the trigger close).
- **`TimeStopExit.mfe_atr` (E2)** — at 0.0 the rule is unchanged (the short book's "not
  in profit"); above 0.0 it is E2 as specified, MFE >= mfe_atr x ATR since entry. New
  keys emitted only when non-default, so short-book config hashes are untouched (D166).
- **`mfe_by_bar()`** — E2's stated prerequisite, the baseline's MFE-vs-time distribution,
  which did not exist: `TradeEpisode` carried only a terminal MFE.
- **`TradeEpisode.trajectories` + `impulse_trajectories()` (E3)** — post-entry range and
  volume per trade, logged and gating nothing, per the doc's explicit instruction. A
  sibling field rather than an extension of `features`, which D167 pinned as scalars.

### Findings
- **E1 KEEPS on both symbols** (+0.058/+0.177 at k=2, +0.101/+0.177 at k=3) — the first
  prediction in `BREAKOUT_REVERSAL_FEATURES.md` to hold. Unlike every other trade-touching
  device tested here, it RAISES the trade count (38->44 BTC, 28->30 ETH): it cuts a failed
  trade early and the strategy re-enters on a fresh trigger.
- **E2 DROPS at both n**, and its own prerequisite explains why: only 26% (BTC) / 43%
  (ETH) of trades reach 1 ATR by bar 5, so E2 cuts most of the book including the trends
  that pay. The validation the doc demanded would have predicted this before the run.
- Long-study DSR pool grew 24 -> 28 and every DSR moved; all 5,568 pre-existing variant
  metrics are byte-identical.

### Fixed
- **The MFE-vs-time table printed an impossibility** — ETH at 43% by bar 5 and 39% by bar
  7, when the rate cannot fall as the window grows. Trades closing before bar n were
  excluded from bar n's numerator while sharing bar 5's denominator. Fixed, and the report
  now raises if the rate ever falls again.


### Added (Phase 2's two missing diagnostics, 2026-08-21 — D176)
- **Squeeze events** — adverse excursions beyond 2 ATR against an open short, with share
  of trades, P&L carried, and how many the stop caught. The function existed as DEAD CODE
  from the Phase 2 session and was never called, so the requirement looked satisfied.
- **Per-window long/short correlation** — the brief asks for it per window; the study
  reported the full-sample figure only.

### Fixed
- **The dead squeeze function had the direction backwards.** It used `abs(mae)` as the
  adverse excursion. Excursions are measured in PRICE terms (D112), so a SHORT's adverse
  side is MFE — a short is hurt when price rises. It would have reported the short book's
  profitable moves as squeezes. The code carried a comment reasoning confidently to the
  wrong answer; it was caught only because wiring it up meant reading it again. Dead code
  is unreviewed code wearing the appearance of a delivered requirement.

### Findings
- **6 of 35 BTC trades (17%) ran more than 2 ATR against the position**, worst 3.70 ATR,
  carrying -39,015 of P&L — and **0% ended at the stop**. A direct measurement of what
  D169-D171 kept circling: the stop is present and is not what closes the dangerous trades.
- **Per-window correlation holds**: 15 of 59 windows measurable (the book sat out 44,
  which is the regime gate working), none exceeding ±0.2, median -0.004. The near-zero
  full-sample figure is NOT opposite-signed regimes cancelling out.
- Windows the short book sat out are reported as unmeasurable, not zero — "uncorrelated"
  and "not present" are different claims, and 44 of 59 fall in the second.


### Added (swing_k2 out-of-sample on the D140 universe, 2026-08-21 — D174)
- **`scripts/run_swing_universe.py` + `docs/results/swing_universe.md`** — `swing_k2` and
  `trail_10` run UNCHANGED across 62 screened coins, one configuration each, no
  per-symbol tuning (D141). The single pre-stated question D173 left standing.
- `run_universe_study` gains an optional `variant` parameter so the short book reuses that
  machinery instead of forking it; default unchanged, so the published long-book universe
  study is untouched.

### Findings
- **The stop survives, the strategy does not.** `swing_k2` beats `trail_10` on 43/62
  symbols (69%), above half in EVERY survivorship cohort — collapsed 71%, delisted 2/2,
  survived 63% — and robust to dropping blow-ups (41/59). But median total return is
  -50.5%, profitable on 5/62, and it posts one FEWER profitable symbol than `trail_10`
  while beating it on average.
- **Three accounts lost more than everything** (D175): USTC -1105.7%, LUNC -167.1%,
  LUNA1 -149.5%, with stops active. The engine models no margin call, no liquidation and
  no borrow recall, so NAV goes negative and the book keeps trading. This was the most
  important thing the run found and it is not what the run was looking for.
- Reports lead on the MEDIAN: a mean over a cross-section containing a -1105% row is not
  an average of anything. CAGR emits None rather than nan past -100%, because a nan in a
  results document is a number nobody has thought about — the first cut printed one.


### Added (swing-structure rules, pre-registered, 2026-08-21 — D173)
- **`SwingStructureStop(k)`** — the stop sits at the most recent CONFIRMED swing pivot
  against the trade; **`SwingStructureGate(k)`** — an entry gate requiring the last two
  confirmed swings to agree (higher high AND higher low, or lower high AND lower low),
  with ambiguous structure vetoing rather than guessing. `k in {2,3}`.
- **`last_swings()`** — pivot detection that never considers a bar newer than `index - k`.
  A k-bar pivot is not knowable until k bars after it forms, and an implementation that
  forgets that offset leaks the future INVISIBLY: DataView stops a crude version indexing
  past the present, but not one that computes pivots from visible bars and drops the lag.
  Asserted directly — a pivot must be invisible at t and t+k-1 and visible at t+k.
- Pivot LEVELS, not drawn trend lines. A sloped line through chosen swing points is a fit
  with free parameters, and `TERRAIN_MODEL.md` already rules out discretionary drawing.

### Findings — the pre-registration was committed first (d1f0d6c), then scored
- **H1 FALSIFIED.** `swing_k2` beats `trail_10` on BOTH symbols (+0.100 BTC, +0.093 ETH)
  and is the first stop here to improve both substantially. The prediction that no
  structure stop would clear the every-symbol bar was wrong.
- **Why it was wrong:** the redundancy argument compared swing SPACING to channel
  LOOKBACK and concluded the levels coincide. Spacing ~ lookback does not imply level ~
  level — a swing pivot is a LOCAL extreme and sits far closer to price after a
  favourable move than a rolling N-bar extreme still carrying the pre-move high. The
  prediction did hold for k=3 (+0.008), which is the case its spacing was reasoned from;
  the mechanism was right and generalised to the wrong parameter.
- **H2 holds.** Neither gate improves on the plain baseline across both symbols (k2
  -0.066/-0.006, k3 +0.168/-0.165). Trade counts fall by two thirds — another
  trade-removing device removing good trades with bad.
- **H3 holds.** DSR with the pool at 25: BTC 0.037-0.088, ETH 0.392-0.538, and DSR still
  selects `stop_trail_5` / `short_40_5` as best rather than `swing_k2`. **The
  falsification does not rescue the book:** `swing_k2` is a real improvement over
  `trail_10` and simultaneously the 25th configuration tried on a strategy with no
  demonstrated edge, and the second fact dominates.


### Added (short book: trial registry + deflated Sharpe, 2026-08-21 — D172)
- **Every breakdown trial is now registered** — one variant row per (symbol, variant,
  tier) plus one per walk-forward window, into `data/breakdown_study_registry.sqlite`
  under the `breakdown-v1` prefix. 168 out-of-sample trials, 2,142 per-window rows.
- **Deflated Sharpe per (symbol, tier)**, pool = configurations tried at that cell
  (D116), selected on identity fields and never on the presence of a metric (D98).
- **A paired block bootstrap of (combined - long-only) Sharpe** (D120), so the ensemble
  claim has an interval rather than a point estimate. The brief asked for
  Jobson-Korkie/Memmel; this project's convention for a Sharpe difference is the paired
  bootstrap, which answers the same question without assuming normality — the deviation
  is recorded in D172 rather than left silent.
- `breakout_study.log_trials` / `dsr_for` are now **public**: the breakdown book reuses
  this module's `VariantResult` and `run_variant` wholesale, so it shares these rather
  than becoming a fifth private copy. Every other study keeps its own.
- A **multiplicity sum-guard**, matching the one Phase 1.1 added to the long study after
  its breakdown table failed to add up.

### Findings — the gap was not cosmetic
- **DSR: BTC 0.039-0.096, ETH 0.393-0.515.** The long study sat near 1.0 at every tier;
  not one cell here reaches 0.95.
- **This overturns the report's two strongest positives.** ETH's 96th-percentile null
  result and its clean sweep of the three success criteria were the best of 21
  configurations; priced for that search, the evidence for skill is gone.
- **It lands on the stop sweep too.** DSR selects `stop_trail_5` as BTC's best — the very
  stop D171 found taking BTC from -71.6% to -40.6% — and deflates it to 0.039. D171's
  refusal to adopt it was right, and this is the number that proves it.
- **Ensemble, with an interval:** BTC -0.79 Sharpe, 90% CI [-1.13, -0.44], P(helps) = 0%
  — the whole interval is negative, so the short book measurably hurts. ETH -0.13,
  CI [-0.57, +0.31], P(helps) = 31% — spans zero, which is absence of evidence, not
  neutrality.


### Added (stop family + sweep, 2026-08-21 — D171)
- **`TrailingChannelStop`, `AtrStop`, `ChandelierStop`** alongside the incumbent
  `ChannelStopExit`, all direction-agnostic. `ExitRule` gains an optional
  `stop_level(view, position)`; the strategy keeps the TIGHTEST proposal each bar and
  RATCHETS it, because a level that can loosen is not a stop. The close-based backstop
  moved onto the strategy, applied once against the ratcheted level instead of being
  duplicated into every rule.
- **A seven-family stop sweep on the short book** at fixed entry/exit parameters, with a
  bind-rate column — D170's incumbent stop bound once in 915 armed bars, the trailing
  stops bind 20-60 times, and that is the difference between a stop being tested and a
  stop being decorative.
- **`SHARPE_EPS = 0.01`**, a stated floor below which a Sharpe difference is not called a
  difference. An earlier cut of the scorecard marked `trail_20` KEEP on a delta that
  rounds to +0.00 — it is in fact the incumbent under another name (for a short entering
  on a 20-bar low, a 20-bar trailing high IS the entry channel) and is now correctly
  reported INERT.

### Findings
- Two stops survive the every-symbol rule (`trail_10`, `atr_2`); neither is adopted,
  because the sweep added a fresh trial series to a book with no demonstrated entry edge.
- **Binding more is not uniformly better**: rank correlation between bind frequency and
  improvement is +0.94 on BTC and -0.43 on ETH, where the most-active stops cut winners
  rather than losers — the same failure mode the long study found in its entry filters.
- `trail_5` takes BTC from -71.6% to -40.6% and its drawdown from 72% to 52%, at a Sharpe
  that is still -0.34. Less bad is not good; no stop repairs an entry.
- **Known gap now pressing:** the short book still logs no TrialRegistry rows and computes
  no deflated Sharpe. Every Sharpe in the breakdown report is raw and is an upper bound.


### Added (intrabar stop execution, 2026-08-21 — D170, disposes of D169's limitation)
- **`TargetWeight.stop`** — an optional stop price riding with the target it protects.
  Re-declared every bar, so a trailing stop moves with no extra machinery; optional with
  a default, so all five construction sites and every pre-existing golden master are
  untouched.
- **Stop orders in `run_backtest`** — a live registry keyed (strategy, instrument),
  checked BEFORE the strategy is consulted so a position opened at this bar's open can
  still be stopped on the same bar, and routed through the existing
  `simulator/fills.stop_fill_price` so a gapped stop fills at the open rather than at a
  price the market never traded (D10). D42's adverse-fill-first convention holds by
  construction: the stop is intrabar, every other exit is a close decision.
- **Optional `Strategy.on_stop_filled`** — without it a stateful strategy never learns it
  was stopped and re-enters on the next bar, turning one bounded loss into a repeated
  one. Called via getattr, so every pre-D170 strategy still conforms.
  `ScheduledBreakout` forwards it to its inner strategy.
- **`BacktestResult.stop_fills`** — which fills a stop actually caused, recorded by the
  engine because only the engine knows.

### Fixed
- **D169's stop-gap measurement was wrong, and its headline number is withdrawn.**
  `measure_stop_gaps` inferred stop exits by asking whether an exit price ended beyond
  the stop level, which also counts trailing-channel exits that closed past it. That
  produced the "4 of 4 stop exits gapped, worst 38.5%" claim. Measured properly, the stop
  caused ONE exit across both symbols and did not gap. The real finding: armed for 915
  bars, binding once — the stop sits at the far side of the entry channel, so the
  trailing exit gets there first. Present, not binding.
- The breakdown report's stop section and standing caveat are now **computed from the
  numbers** rather than asserted alongside them — the third instance in this project of
  hardcoded prose drifting from the data beside it.


### Added (Phase 2 — the breakdown short book, 2026-08-21 — see `BREAKDOWN_RESULTS.md`, D169)
- **`ExitRule` brick family on the breakout strategy** — the mirror of `EntryFilter`: a
  filter can only keep you OUT of a trade, an exit rule can only get you OUT of one. The
  trailing channel stays the safety net underneath every added rule. `exit_rules` is
  emitted from `config()` only when non-empty, so long-flat configs written before it
  existed still hash identically.
- **`ChannelStopExit` and `TimeStopExit`** — the per-trade stop at the entry channel's
  opposite boundary fixed at entry, and the "not in profit within n bars" exit. Both are
  signal-level rules measured against the trigger bar's close, because the strategy
  decides on a close and the engine fills at the next open — it genuinely does not know
  what it paid.
- **Tail discipline enforced at construction (D169)** — a SHORT strategy without a
  `ChannelStopExit`, or with a weight source capping above 1.0, refuses to build. There
  is no flag that disables either. The long book is deliberately NOT held to this: a
  long's worst case is the instrument going to zero, a short's has no ceiling.
- **`CostTier.borrow_annual_rate` + `SHORT_TIERS`** — 10%/yr on short notional (D124's
  rate). The brick is emitted only when non-zero, so every long-side tier config and
  trial hash is unchanged.
- **`research/breakdown_study.py`** — the short book's own sweep ({10,20,30,40} x
  {3,5,10}, deliberately faster than the long book's), ex-post bull/bear/chop regime
  slicing, long-vs-short correlation computed INCLUDING flat bars, equal-vol ensemble
  metrics, an exposure-matched random-entry null that takes a `direction` parameter (the
  last outstanding D166 forward-compat requirement), and stop-gap measurement.
- **`scripts/run_breakdown_study.py` + `BREAKDOWN_RESULTS.md`** — 120 out-of-sample
  trials across 15 variants and 4 tiers on two symbols.

### Known limitation (D169)
- **The short stop is CLOSE-based, so the squeeze tail is not truncated by construction.**
  `stop_fill_price` has correct D10 gap semantics but is a Step-2 demonstration vehicle
  wired only to `config/fill_model.py`, never to `run_backtest`. The study measures the
  shortfall instead of assuming it away, and the measurement is damning: every stop exit
  on both symbols filled beyond its own stop, by roughly 18%.


### Added (volume reaches strategy code, 2026-08-21 — closes D111, see D168)
- **`DataView` carries volume (D168)** — an aligned, optionally-present series
  constructed sliced exactly as bars are, so the look-ahead guarantee is inherited
  rather than re-argued. `Bar` and `TimestampedBar` are unchanged. `build_data_view`,
  `run_backtest` and `walk_forward_windows` each gain one optional parameter with a
  default, so no existing call site changed — and all pre-existing golden masters pass
  untouched, which is the evidence the change is additive rather than a claim about it.
- **Three volume states, only one of them loud.** `has_volume` False means the
  instrument has none (silent, correct); a `None` entry means a gap on that bar
  (silent, consumer states its policy); `require_volume` on a view with no series
  raises `MissingVolumeError`. Collapsing the first and third is the trap — a volume
  filter with no volume rejects every entry and returns a clean-looking, entirely wrong
  result. `NaN` is normalised to `None` once at construction and never enters a view.
- **`VolumeConfirmationFilter(multiple=1.5, window=20)`** — the filter the original
  brief specified and D111 recorded as blocked. Added as a fifth filter variant facing
  the same keep/drop rule as the others. Averaging baseline ends at t−1 (D44) so a big
  trigger bar cannot inflate the threshold it has to beat; any missing volume in the
  window or on the trigger bar rejects the entry, stated and tested.
- **Feature F2 (trigger volume ratio) is computable** for the first time; D167 recorded
  it blocked by the same gap.
- **Verification** — the D32 reflection audit extended to the new surface (its Attack 5
  inspected only tuples of `Bar`, so the volume tuple would have been untested by
  construction); a property test that perturbing any future volume cannot change a
  target already produced; and a hand-computed golden master
  (`test_volume_confirmation_golden.hand.txt`) whose bar 3 and bar 9 differ in volume
  and nothing else.


### Added (breakout Phase 1.1, 2026-08-21 — see `BREAKOUT_RESULTS.md`, D166–D167)
- **`Direction` / `PositionState` on the breakout brick (D166)** — the strategy is now
  sign-parameterized: one `_channel_extreme` / `_beyond` pair serves both sides, the
  boolean `_in_position` flag is replaced by a three-state enum whose value IS the sign of
  the exposure, and `TrendGateFilter` gates longs above its SMA and shorts below it. These
  are the forward-compatibility requirements `BREAKDOWN_SHORT_STRATEGY.md` places on the
  long-side session; Phase 1 shipped without them. Behaviour-preserving for a long book,
  and `direction` is omitted from `config()` at its LONG default so every v1 trial hash
  survives unchanged.
- **`TradeEpisode.features` open map + `research/feature_analysis.py` (D167)** — the
  at-trigger feature pass from `BREAKOUT_REVERSAL_FEATURES.md`, which Phase 1 never ran.
  F1/F3/F4/F6 computed, F2 and F5 logged as blocked with reasons, quintile tables and a
  monotonicity/stability verdict per feature. Features are read off the TRIGGER bar
  (`entry_index - 1`), not the entry bar — reading the entry bar would be a one-bar
  look-ahead living inside the diagnostics. Logged only: nothing here gates a run or
  enters the DSR pool.
- **Sweep-edge section in the report** — the brief's sweep-edge rule mandated recording
  the boundary gradient and flagging an N_entry extension when performance is still
  improving at the sweep boundary. v1 did not report it at all, despite one symbol's best
  cell sitting exactly on the boundary. Now reported symmetrically, since the two symbols
  point at opposite edges.

### Fixed (breakout report, 2026-08-21)
- **The multiplicity breakdown did not sum.** Sub-rows totalled 19 against a stated 23
  variants — the four vol-target sensitivities had no row — and the verdict prose then
  quoted the wrong 19 in two places while the DSR tables correctly said 23. The row is
  added, the prose is computed rather than hardcoded, and the builder now raises if the
  breakdown ever disagrees with the variant count again.
- **The era section was hardcoded to BTC's shape.** "that decade" and "a four-figure
  percentage return" were emitted verbatim for ETH, whose out-of-sample span is 7.4 years
  and whose returns are three-figure. Both are now derived from the symbol's own span and
  its own headline number.


### Added (breakout cost–frequency frontier, 2026-08-19 — see `docs/results/breakout_intraday.md` and D160–D165)
- **`scripts/fetch_crypto_intraday.py` + `data/fixtures/crypto_intraday_{1h,30m,15m}_raw*`
  (D160)** — BTC-USD/ETH-USD intraday fixtures. yfinance serves 730 days of 1h, 60 days of
  15m/30m, no 4h over a usable span and **no 6h interval at all**, so 1h is the study base
  and 2h/4h/6h/12h/1d are resampled from it. One-time manual fetch; the only step that
  touches the network. A `live_fetch`-marked test pins the assumption the offline pipeline
  cannot check for itself — that the provider stamps intraday crypto bars in UTC, on the
  hour.
- **`research/breakout_intraday.py` (D161/D162)** — the resampling contract (exact OHLCV
  aggregation on 00:00-UTC-anchored buckets, incomplete buckets raise), the two frequency
  designs, calendar-scaled walk-forward, calendar-unit trade diagnostics, and the frontier
  renderers. Every number comes from `research.breakout_study` imported unmodified
  (`run_variant`, `run_benchmark`, `run_constant_fraction_benchmark`, `breakout_config`,
  `CostTier`, `DEFAULT_TIERS`). No existing interface changed.
- **Equal walk-forward windows across frequencies as a theorem, not a check (D161).** A UTC
  day the provider does not serve in full is dropped at *every* frequency, so each rung
  holds exactly `complete_days × bars_per_day` bars and the window count
  `floor((days − 315)/63) + 1` is frequency-independent by construction. `window_count`
  takes no frequency argument; `run_frontier` asserts the equality against every run anyway.
  7 windows over 441 out-of-sample days at every rung, both symbols.
- **`periods_per_year` consistency enforced at runtime (D162).** It lives in two places —
  the argument `analytics.metrics` requires (D17) and the field inside the
  `inverse_vol_weight` config (D110) — and `assert_periods_per_year_agree` refuses any cell
  where they disagree. Both copies are logged with every trial so the check is auditable
  after the fact.
- **The headline (D165).** Design B (40-bar/10-bar at every frequency) crosses at **2h on
  both symbols independently**, with **4h the finest bar that still clears its own gross
  edge**; annualised turnover runs 10.5× → 188.7× and fee drag 4.2% → 75.5% of capital a
  year from 1d to 1h on BTC. Design A (constant 40-day/10-day calendar horizon) **never
  crosses** at any rung down to 1h — turnover rises only 10.5× → 11.5×. So
  `BREAKOUT_RESULTS.md`'s "fees are not the binding constraint" **survives for the 40-day
  signal at any sampling rate and fails decisively for the shortened-horizon rule below
  roughly 4-hourly bars.**
- **`data/breakout_intraday_registry.sqlite`** — 112 rows (96 out-of-sample trials +
  16 sub-hourly measurement rows), all distinct hashes, config and snapshot id logged per
  D20. DSR pooled in per-calendar-day units after collapsing every equity curve to
  end-of-day NAV (D164), because pooling per-bar Sharpes across frequencies is exactly the
  units bug D98 exists to prevent.
- **Two data-layer findings, reported rather than absorbed.** (1) `clean-v1`'s
  `non_positive_volume` rule would have deleted **17,520 of 34,923** hourly bars — yfinance
  reports Volume = 0 on roughly half of them — so the intraday fixture is cleaned on prices
  only, with the volume column still written to the snapshot and the artifact surfacing as
  non-blocking warnings (D160). (2) The 1h → 1d resample **does not** reconcile with the
  committed daily fixture: opens and closes differ ~2 bp with no sign bias, but the
  resampled high is at or below the provider's daily high on 99.8% of days and the low at
  or above on ~90% — yfinance's daily crypto bar is not the aggregate of its own hourly
  bars, and the bias tilts toward *more* trading (D161). A test pins the negative so a
  future reconciliation cannot pass silently.
- **Tests** — `tests/unit/test_breakout_intraday.py` (21) and
  `tests/integration/test_breakout_intraday_study.py` (15, + 1 `live_fetch`): exact OHLCV
  aggregation, loud incomplete buckets, 00:00-UTC anchoring, frequency-independent window
  counts, `periods_per_year` agreement in both places, fixture and snapshot round-trips,
  cost monotonicity across tiers *at every frequency*, registry hash uniqueness, and the
  derived-vs-measured cost-wedge cross-check.

### Added (crypto breakout universe cross-section, 2026-08-18 — see `docs/results/breakout_universe.md` and D140–D144)
- **`scripts/fetch_crypto_universe.py` + `data/fixtures/crypto_universe_2015_2025_raw*` (D140)** —
  a 63-symbol crypto fixture built to contain the assets that **died**. 77 tickers attempted
  across three cohorts chosen for *point-in-time* prominence (the 2018 top-30, the 2021 peak,
  and a cohort sought out because it failed: Terra/LUNA under both provider tickers, TerraUSD,
  FTT, Celsius, Serum, with OKB/LEO as the surviving exchange-token control). Outcome:
  **20 survived, 41 collapsed, 2 delisted**; 13 excluded by the pre-stated policy and 1
  (`MIOTA-USD`) the provider would not serve, every one named in the meta with the statistic
  that rejected it. The one-time fetch is the only step that touches the network.
- **`research/breakout_universe.py` (D140/D141)** — selection policy, cross-sectional
  aggregation and rendering, and *nothing else*. Every number comes from
  `research.breakout_study` imported unmodified (`run_variant`, `run_benchmark`,
  `run_constant_fraction_benchmark`, `breakout_config`, `CostTier`, `DEFAULT_TIERS`,
  `annual_breakdown`, `start_date_sensitivity`, `sharpe_difference_bootstrap`); an
  integration test pins that every logged config is byte-identical to
  `breakout_config(40, 10)`. `apply_policy` is the single implementation of the screen,
  run at fetch time and re-run by the study on the committed fixture so a rejected symbol
  cannot reach the engine — tested by feeding the study a symbol that fails the coverage
  rule and asserting it appears in neither the results nor the registry.
- **The headline (D140).** Across 63 coins at `taker_40bp` the fixed baseline beat 100%
  buy-and-hold in **51/63 (81%)**, beat the matched-exposure benchmark (D119, the fair
  test) in **38/63 (60%)**, and reduced max drawdown in **63/63 (100%)**. Split by
  outcome: against buy-and-hold it wins **45%** of survivors and **98%** of the wrecks;
  at matched exposure **45%** vs **67%**. **The timing claim generalises only to the
  assets that fell apart, and fails on the ones that survived** — the standing prior for
  a trend follower, measured for the first time here. BTC and ETH rank 1st and 8th of 63
  on total return and 2nd and 13th on Sharpe: the original study's caveat 3 answered with
  a number.
- **DSR pool = the cross-section (D142)** — one row per symbol per tier, N = 63, selected
  on identity fields (`row_kind == "symbol"`), never on presence of a metric (D98). New
  registry `data/breakout_universe_registry.sqlite`: 252 out-of-sample trials, 756
  benchmark rows, 9,552 per-window rows, all hashed with the snapshot id. DSR ≈ 0.96 at
  every tier, and the best symbol is `LUNA1-USD` — a delisted token over 881 bars, printed
  next to that fact rather than in a headline.
- **D120's bootstrap, counted instead of described** — a per-coin paired block bootstrap
  (20-bar blocks, 4,000 sims, seed 0) puts the Sharpe difference's 90% interval clear of
  zero in **3 of 63** coins against buy-and-hold and **4 of 63** against matched exposure,
  where ~6 would be expected by chance at that confidence level. No Sharpe comparison in
  the document is a measurement.
- **`SnapshotStore` quarantine overridden, loudly (D143)** — the validator's ETF-calibrated
  >60% move threshold (D74) fires 143 times across 41 of 63 crypto symbols, concentrated in
  the collapsed cohort. Respecting it mechanically would delete the failed assets and
  restore the very survivorship bias the study measures, so the run loads with
  `allow_quarantined=True` in one visible place and the report carries the full violation
  census. The validator is not modified; recalibration is deferred per R3.
- **Peg screen added post-hoc and recorded as such (D144)** — the policy's first run raised
  on `UST-USD` (a stablecoin never prints a 40-bar high, so its Sharpe is −∞ rather than
  bad). Fixed in the universe policy rather than by imputing or by selecting the DSR pool
  around it. The threshold sits in an order-of-magnitude-wide empty gap (peg 0.14%/day vs
  BTC 1.42%/day), and the amendment is dated and explained in D144 rather than folded in.
- `tests/unit/test_breakout_universe.py` (25) and
  `tests/integration/test_breakout_universe_study.py` (19, one `live_fetch`-marked) — policy exclusions and their
  reasons, "the screen never looks at a return", fixture round-trip and 00:00 stamping,
  empty events sidecar, cost monotonicity across tiers, registry id/hash uniqueness, DSR
  pool composition, cross-study reconciliation of the BTC/ETH rows against
  `BREAKOUT_RESULTS.md`, and determinism. 644 tests green (44 new), mypy clean.

### Added (BTC/ETH z-score pairs study, 2026-08-18 — see `docs/results/crypto_pairs_btc_eth.md` and D122–D127)
- **`research/crypto_pairs_study.py` (D122)** — the study harness for the repo's
  market-neutral thesis strategy on crypto. `strategies/zscore_pairs.py` is reused
  **unmodified** (D69): no new strategy was needed, so none was written. The harness
  imports `breakout_study.CostTier` / `run_benchmark` (D114/D115), `capacity`'s
  `recording_cost_stack` (D95) and `cointegration`'s Engle–Granger/ADF machinery
  (D92/D93) rather than reimplementing any of them. It does **not** reuse
  `run_pairs_study`, whose `StudyConfig` hard-codes the ETF cost stack and logs it
  verbatim — running it here would have produced trials whose logged `cost_stack`
  described bricks that did not run, the exact drift D102 closed.
- **Continuous stitching, with the chained seam priced (D123)** — one continuous OOS
  backtest per (variant, tier), the breakout study's pattern. The chained alternative
  ships as a sensitivity row: −96.7% vs −98.0% at the reference tier, 52 round trips vs
  40. Two seams motivate the choice for a pairs book, not one — the free liquidation
  D113 already named, plus the silent reset of `ZScorePairsStrategy._side`, which
  discards the hysteresis band at every boundary and is a *signal* artifact.
- **A pairs cost stack that charges what a pairs book pays (D124)** — the tier fee brick
  byte-identical to the breakout study's, plus `BorrowFee` at a stated, swept, non-zero
  10%/yr on the short leg and `MarginInterest` at 10%/yr on `max(gross − NAV, 0)`. All
  built through `build_cost_stack` (D102). `leg_weight` swept {1.0, 0.5, 0.25}; the D96
  margin-threshold collapse reproduces exactly (6,129 → 318 → 0).
- **Cointegration tested rather than assumed (D125)** — `cointegration_report` runs the
  ADF on each *training* window only, on both the traded 1:1 log spread (Dickey–Fuller
  τ_μ) and the Engle–Granger residual, with critical values anchored against
  `statsmodels.tsa.stattools.adfuller` in the unit suite. Positive and negative controls
  (a synthetic AR(1) spread; two independent random walks) ship with it.
- **Per-brick cost attribution and pair-level diagnostics (D127)** — fees / borrow /
  margin from a recording stack, plus round trips, exposure and annual turnover computed
  locally rather than by extending `trade_diagnostics.py`, whose "trade = long-flat
  position episode" definition (D112) does not describe a pairs book.
- **`tests/golden/test_crypto_pairs_golden.py` + `.hand.txt`** — a six-bar scenario
  hand-computed to the cent, pinning the axes the breakout golden master cannot reach:
  two legs filling per decision, borrow charged on the short leg *and only* the short
  leg, margin charged on gross above NAV, and the constant-gross re-normalization that
  produces interior fills as NAV moves. Reconciles exactly on first run.
- `tests/unit/test_crypto_pairs.py` (24), `tests/property/test_zscore_pairs_invariants.py`
  (9 — headline: perturbing bars after the decision bar cannot change a target, at signal
  level and through the full engine with carry), `tests/integration/test_crypto_pairs_study.py`
  (22), `tests/golden/test_crypto_pairs_golden.py` (8). 453 → 516 tests green.

### Added (breakout study review, 2026-08-18 — see D118–D121)
- **Era decomposition (D121)** — `annual_breakdown`, `exposure_by_year` and
  `start_date_sensitivity` in `research/breakout_study.py`, with a mandatory
  "Is this the strategy, or is it the era?" report section. Answers the question a
  four-figure crypto return always raises: BTC rose 426× over the OOS span, the strategy
  lost to buy-and-hold in every up year and beat it in 5 of 6 down years, and its CAGR
  ranges +11% to +49% purely on start date.
- **Risk-equalised benchmark (D119)** — `run_constant_fraction_benchmark` holds a constant
  fraction of capital (set to the strategy's own average exposure) through the same engine
  and tier, so the benchmark's average exposure matches the strategy's and the only
  remaining difference is *when* exposure was taken.
- **Paired block bootstrap on Sharpe differences (D120)** —
  `sharpe_difference_bootstrap`, seeded, resampling one index vector applied to BOTH return
  series so their correlation is preserved.
- **Vol-target sweep (D118)** — `voltarget_*` variants at 20/30/60/80% alongside the 40%
  baseline, registered as trials. DSR pool per (symbol, tier) grows 19 → 23 configurations.
- `tests/unit/test_breakout_era_analysis.py` (15 tests): bootstrap-against-itself is
  degenerate at zero (which fails if the pairing breaks), determinism under seed,
  constant-fraction at f=1 matching engine buy-and-hold, exposure-by-year computed from
  timestamps rather than run-relative indices, and the vol sweep varying exactly one key.
  438 → 453 tests green.

### Fixed (breakout study review)
- **`BREAKOUT_RESULTS.md`'s risk-adjusted claim retracted (D120).** The first version
  concluded "the entire case for this strategy is a risk-adjusted one" from Sharpe gaps of
  +0.04 (BTC) and +0.11 (ETH). Those are a tenth and a quarter of one standard error;
  P(strategy > benchmark) is 55% and 59%. Replaced with the narrower claim that survives:
  a drawdown-shape result, not an alpha result.
- **The 100%-invested benchmark was doing unfair work in both directions (D119).** A
  ~35%-exposed strategy was being judged against a 100%-exposed alternative; the
  matched-exposure row shows the strategy earning several times the terminal wealth of
  constant exposure at comparable drawdown.
- An up-year/down-year claim in the verdict was hardcoded and wrong for ETH (it has a down
  year, 2019, in which the strategy lost to holding). Now counted from the data.
- `exposure_by_year` originally indexed the OOS calendar with run-relative episode indices,
  misattributing time-in-market across years; now computed from episode timestamps, pinned
  by a test.

### Added (breakout study, 2026-08-18 — see BREAKOUT_RESULTS.md and D108–D117)
- **`strategies/breakout.py` (D109)** — long-flat Donchian breakout, the repo's second
  research strategy and its first directional one. Entry on an N_entry-bar high, exit on a
  faster N_exit-bar low, both extrema computed over completed bars strictly before the
  current one. Filters (`ConsecutiveCloseFilter`, `VolatilityContractionFilter`,
  `TrendGateFilter`) and sizing (`FixedWeight`, `InverseVolatilityWeight`) are separate
  toggleable bricks behind `Protocol`s with declarative configs and factory registries, so
  a strategy rebuilds from the exact dict the registry hashes (D102). `n_exit > n_entry` is
  refused: the nesting is what makes entry/exit mutually exclusive on any bar.
- **`research/breakout_study.py` (D113, D114, D116)** — walk-forward harness
  (train 252 / test 63 / step 63) running each (symbol, variant, tier) as ONE continuous
  OOS backtest with a per-window parameter schedule (`ScheduledBreakout`) rather than
  chained windows; four crypto fee tiers built through the declarative cost-stack path;
  plateau surface, in-training-window grid selection, per-(symbol, tier) DSR whose pool is
  configurations rather than windows; report renderers.
- **`research/trade_diagnostics.py` (D112)** — position-episode reconstruction from engine
  fills: MFE/MAE, time-in-trade distribution, time-to-stop-out for losers, whipsaw rate,
  capture ratios, round-trip cost as a share of gross P&L, and rebalance-vs-signal cost
  split.
- **`data/fixtures/crypto_daily_2015_2025_raw.csv.gz` (D108)** + fetch script — BTC-USD and
  ETH-USD daily bars at a fixed 00:00 UTC boundary; 0 cleaning changes and 0 hard
  validation violations through the Step-7 pipeline.
- **`scripts/run_breakout_study.py`** → `BREAKOUT_RESULTS.md` + `data/breakout_study_summary.json`
  (offline, deterministic; 152 out-of-sample trials, 7,904 registry rows).
- **Tests:** `tests/golden/test_breakout_golden.py` (+ `.hand.txt`) — 9-bar scenario
  asserted line by line against hand arithmetic; `tests/property/test_breakout_invariants.py`
  — no-look-ahead under arbitrary future-bar perturbation (signal level and through the
  engine), hysteresis, cost application, fee monotonicity; `tests/unit/test_breakout.py`,
  `tests/unit/test_trade_diagnostics.py`, `tests/integration/test_breakout_study.py`.
  361 → 438 tests green (77 new).

### Changed
- `tests/unit/test_strategy_labels.py` (D117) — D38's label gate fired for the first time
  when `breakout.py` landed, exactly as D82 designed it to. The breakout module now carries
  an explicit directional / not-market-neutral / benchmarked-against-buy-and-hold label, and
  the gate greps for all three.
- `strategies/breakout.py`'s `EntryFilter` / `WeightSource` protocols declare `name` and
  `rebalance` as read-only properties, so frozen brick dataclasses type-conform — the same
  variance fix audit F20 applied to `Instrument.quote_currency`.

### Deferred
- **Volume-confirmation filter (D111)** — not built. `Bar` carries no volume and
  `DataView` hands strategies `Bar` objects; adding volume to the bar schema is a framework
  change with its own gate, and smuggling a volume series past `DataView` would open the
  look-ahead hole D32 exists to close. Recorded rather than worked around; no class exists
  claiming the capability.

### Fixed (audit remediation, 2026-07-14 — see AUDIT_REPORT.md and D98–D107)
- **DSR wiring (D98, the audit's one result-corrupting finding):** per-window Sharpes are
  now logged in daily (per-period) units matching the observed SR — the old code logged
  annualized values under the same name, inflating SR0 by √252 and forcing DSR toward 0
  regardless of the strategy; the trial pool is the study's 1×-cost rows only, undefined
  window Sharpes are omitted (loud at 1×), and capacity/gross levels skip the per-level
  DSR entirely (`compute_dsr=False`).
- **Silent failure modes made loud (D99):** duplicate bar timestamps raise in `align_bars`
  and hard-quarantine in the validator (was last-wins collapse); zero-overlap alignment
  raises in `run_backtest` (was a silently-empty result at starting cash); the pairs study
  asserts per-symbol bar grids match the aligned universe; dividends in a gap containing a
  split now pay on the share count held on their ex-date; cleaner volume indexing is
  bounds-guarded.
- Doc rot: validator docstring matched to its actual thresholds and the real XOP split
  date; strategy-module Kalman promise removed (cut per D97); loader duplication collapsed;
  `hello()` scaffolding removed; mypy 7 → 0 across `src/`.

### Added (audit remediation)
- `config/cost_stack.py` (D102) — the study's real cost stack is built from the same
  declarative dict logged to the TrialRegistry; `StudyConfig.to_dict()` covers every
  determining field (starting_cash and multipliers were missing) and `from_dict()` closes
  the study-level reproducibility loop, tested end to end.
- `StudyConfig.impact_calibration="train_window"` (D102) — per-window σ/ADV estimation from
  the train slice only (D44-compliant), alongside the documented full-sample default.
- `run_backtest(fill_timing="next_open")` (D103) — decisions fill at the next bar's open;
  hand-computed golden + property invariants; default "close" preserves every baseline.
- `run_backtest(enforce_pretrade=True)` (D101) — the previously-unwired pre-trade gate
  rejects breaching netted orders and rolls back the instrument's virtual orders.
- `BacktestResult.virtual_fills` / `final_virtual_positions` (D101) — D46's strategy-tagged
  fill stream at the result surface.
- Carry/event bricks declare their carry component and the engine consults
  `Instrument.carry_components()` (D100) — no behaviour change for equities.
- `deflated_sharpe_from_trials(include=...)` predicate with a stated units contract (D98).
- Property suite: signed positions, real OHLC bars, unconditional commission/carry shadow
  accountants, next-open invariants (D104).
- `scripts/run_convention_sensitivity.py` → `docs/results/convention_sensitivity.md`
  (D105) — the v2 configuration across {close, next-open} × {full-sample, train-window}.
- Conventions pinned by test/record: round-half-even share rounding, current-close carry
  marks, MC block length rationale (D106); written R3 deferrals for the margin lock,
  stop/limit fill menu, FX brick, IS/OOS ratio, and registry artifact policy (D107).

### Added
- Full documentation suite: per-decision ADR records under `docs/decisions/`, standing rules
  in `docs/RULES.md`, this changelog, `AITODO.md`, top-level `README.md`, `.gitignore`.
- `PHILOSOPHY.md` — five guiding pillars extracted from the pattern across the existing 49
  decisions, sitting above `docs/RULES.md` and `docs/decisions/` as the reference point for
  any future decision.
- Local git repository initialized.
- Project scaffolding: `uv`-managed src-layout Python package, pytest + hypothesis test
  stack (D50).
- `backtest_framework.simulator.fills.stop_fill_price` — gap-through-stop fills at the
  bar's open instead of the stop price (D10).
- `backtest_framework.simulator.carry` — `accrue_carry`/`accrue_carry_between_bars`, carry
  cost accrual on the calendar-day gap between bar timestamps rather than bar count (D33),
  using an ACT/365 day-count convention (D51).
- `backtest_framework.registry.trial_registry.TrialRegistry` — SQLite-backed, append-only
  trial log with a deterministic config+snapshot+seed hash (D20).
- Step 1 of `VERIFICATION_SCHEME.md` — gate passed (20/20 tests: golden-master, property,
  unit).
- `backtest_framework.config.factory.FactoryRegistry`/`ConfigError` — generic type-keyed
  declarative-config factory pattern, fails loudly naming the bad key (D35, D52).
- `backtest_framework.config.sim_config.SimConfig` validator/builder, plus two
  demonstration model configs (`carry_model.CarryModel`, `fill_model.FillModel`) wrapping
  Step 1's carry accrual and stop-fill behaviour behind the factory pattern.
- Step 2 of `VERIFICATION_SCHEME.md` — gate passed (35/35 tests total, 15 new), including
  the full reproducibility loop (config → hash → registry → reload → re-run). This closes
  the Phase A milestone in `DEVELOPMENT_TIMETABLE.md`.
- `backtest_framework.instruments` — `Instrument` protocol, `Equity`, `OptionStub` (D12,
  D16). `docs/options_extension.md` added as a stub so `OptionStub`'s
  `NotImplementedError` points at a real path.
- `backtest_framework.costs` — `CostStack` (D1) plus `TradeCostBrick`/`CarryCostBrick`
  protocols (D2) and three toy bricks: `FlatCommission`, `PercentOfNotionalSpread`,
  `FlatRateCarry`.
- `backtest_framework.pipeline.sizing` — `Sizer`, `TargetWeight`, `Order`, `net_orders`,
  `apply_virtual_orders`: the signal → target weight → orders pipeline (D27), with
  cross-strategy netting and per-strategy virtual books (D46).
- Step 3 of `VERIFICATION_SCHEME.md` — gate passed (60/60 tests total, 25 new). The
  "refactor regression" gate was reinterpreted for this project's greenfield conditions
  (D53) and satisfied with a new hand-computed 3-bar golden-master scenario
  (`test_step3_refactor_regression.py`), now the frozen baseline for future refactors of
  CostStack/Instrument/pipeline.
- `backtest_framework.engine.dataview` — `DataView`, `LookAheadError`,
  `build_data_view()`: a structural look-ahead guard (D32) built so future bars are
  never stored in the object at all, not merely access-gated (D56).
- `backtest_framework.engine.risk` — `RiskLimits`, `RiskViolation`, `RiskMonitor`,
  `gross_exposure()`: per-bar portfolio-level risk checks plus a pre-trade gate sharing
  the same limit logic (D30, D57).
- `backtest_framework.engine.allocator` — `Allocator` protocol, `ConstantSplitAllocator`:
  a bare-bones capital-allocation stand-in (D31), wired into `pipeline.sizing.Sizer`'s
  `capital_by_strategy` input (D58).
- Step 4 of `VERIFICATION_SCHEME.md` — gate passed (78/78 tests total, 18 new). **Phase B
  complete** (`DEVELOPMENT_TIMETABLE.md`) — both Step 3 and Step 4 gates pass without
  needing the pre-committed slip rule.
- First production dependencies: `yfinance`, `pandas` (`pyproject.toml` was
  `dependencies = []` until now).
- `backtest_framework.data` — `TimestampedBar` (D60), `DataSource` protocol (D18),
  `EquityDataSource` (a deliberately unhardened yfinance passthrough — no snapshotting
  D24, cleaning D25, or sanity gate D26 yet; see D59).
- `backtest_framework.engine.portfolio.PortfolioState` — broker-facing cash/positions
  and NAV (D43's short-sale accounting falls out naturally from signed notional, no
  special-casing needed).
- `backtest_framework.engine.strategy` — `Strategy` protocol, `ScheduledWeightStrategy`
  (a toy reference strategy, analogous to Step 3's toy cost bricks).
- `backtest_framework.engine.backtest.run_backtest` — the production loop generalizing
  Step 3's test-only `run_mini_backtest`: wires DataView, Strategy, Allocator, Sizer,
  CostStack, PortfolioState, and (optionally) RiskMonitor and TrialRegistry together
  per bar. Capital is reallocated from current NAV every bar (D61). Risk violations are
  recorded, not enforced (D62).
- `pytest` marker `live_fetch`, excluded by default via `addopts` — matches
  `VERIFICATION_SCHEME.md`'s own cross-cutting gate ("CI runs everything offline...
  live-fetch tests are excluded by marker").
- Minimal data-source + engine-loop chunk (not a numbered `VERIFICATION_SCHEME.md`
  step; inserted ahead of Step 5 to unblock it — D59) — gate: a `ScheduledWeightStrategy`
  run through `run_backtest` reproduces Step 3's frozen golden-master NAV curve exactly
  (95/95 tests total, 17 new, offline by default).
- `backtest_framework.data.alignment` — `AlignedBar`, `align_bars()`: inner-join
  multi-instrument bar alignment (D45, D63). A bar missing on one leg drops that
  timestamp for every leg; carry accrues correctly across the resulting gap with no
  special-case code.
- Multi-instrument alignment chunk (D45) — gate: a real long-XLE/short-XOP pair runs
  end-to-end through `run_backtest` (104/104 tests total, 9 new, offline by default;
  the XLE/XOP run is `live_fetch`-marked).
- `backtest_framework.costs.equity_bricks` — the real equity cost bricks (Step 5):
  `IBKRCommission` (Fixed schedule: $0.005/sh, $1 min, 1% cap, cap overrides min —
  D4/D65), `SqrtImpact` (square-root impact law, fraction ∝ √Q / dollars ∝ Q^1.5,
  static per-symbol σ/ADV params, loud errors on missing/zero ADV — D3/D66),
  `MarginInterest` (accrues on max(gross exposure − NAV, 0) — D5/D67). Toy bricks
  remain alongside as simple/sensitivity bricks.
- `CostStack.portfolio_carry_bricks` — a third slot for portfolio-level carry, charged
  once per bar on an engine-computed base, with start-of-bar snapshot semantics in
  `run_backtest` (D67). Additive; existing stacks and the frozen D53 baseline are
  unchanged (re-run and confirmed).
- Step 5 of `VERIFICATION_SCHEME.md` — gate passed (134/134 tests total, 30 new):
  X (13-row IBKR schedule table; live-page anchoring 403-blocked, manual check
  tracked in `AITODO.md`), G (margin interest weekend case tied to D33's arithmetic +
  only-when-positive + engine integration run), U (sqrt impact √2/2√2 scalings +
  loud-error paths).
- `backtest_framework.costs.scaling.scaled_cost_stack` — per-brick cost-multiplier
  scaling across all three CostStack slots (D8, D68).
- `backtest_framework.engine.sweep` — `run_cost_sweep` (strategy-factory API, optional
  per-multiplier TrialRegistry logging), `render_sweep_table`, `max_drawdown` (D68).
- `backtest_framework.strategies.zscore_pairs.ZScorePairsStrategy` — the first
  non-toy strategy: fixed 1:1 log-spread z-score mean reversion with hysteresis,
  previous-bar estimation windows, warm-up/zero-std self-guards (D69).
- `backtest_framework.costs.equity_bricks.BorrowFee` — per-leg carry, shorts pay /
  longs free (D71).
- `backtest_framework.data.csv_fixture` — save/load committed CSV fixtures;
  `data/fixtures/xle_xop_daily_2015_2024.csv` + `.meta.json` committed as the
  pre-Step-7 frozen snapshot (D70). `scripts/fetch_fixture.py` (one-time network),
  `scripts/run_first_result.py` (offline, deterministic).
- **`docs/results/first_real_number.md` — THE FIRST REAL NUMBER (Phase C milestone,
  R1's gate):** XLE/XOP z-score pairs 2015–2024, full real cost stack, sweep
  +13.21% at 0× → −22.70% at 1× → −76.43% at 4×, monotonic; caveats stated.
- Step 6 of `VERIFICATION_SCHEME.md` — gate passed (163/163 tests total, 29 new):
  0× ≡ zero-cost and monotonicity asserted on both a penny-exact synthetic scenario
  and the real fixture, offline and repeatable.
- `backtest_framework.data.snapshot_store.SnapshotStore` — content-addressed frozen
  snapshots (sha256 payload ids), checksum-verified loads, quarantine refusal (D24,
  D72).
- `backtest_framework.data.cleaner` — drop-and-report ruleset `clean-v1` with
  `CleaningReport` attached to snapshot meta (D25, D73).
- `backtest_framework.data.validator` — sanity gate with hard-vs-warning findings,
  observed-data-calibrated move thresholds, frame-robust split awareness (D26, D74).
- `backtest_framework.data.corporate_actions` — dividends/splits tables, two-frame
  conversions (`as_traded_from_adjusted`, `as_declared_dividends`, `split_adjusted`),
  events JSON persistence (D6, D75).
- `EventFlowBrick` protocol + `DividendFlow` brick + `CostStack.event_flow_bricks`
  (4th slot, unscaled by the D8 sweep — flows are transfers, not frictions);
  `run_backtest` gains `splits_by_instrument` (position scaling on ex-dates) and
  `view_bars_by_instrument` (signal/execution series separation) (D75).
- `EquityDataSource.get_raw_history` (additive); committed raw fixture
  `data/fixtures/xle_xop_daily_2015_2024_raw.csv` + events JSON;
  `scripts/fetch_fixture_v2.py`, `scripts/run_first_result_v2.py`.
- **`docs/results/first_real_number_v2.md`** — the first number re-run through the
  hardened path (+21.74% at 0× / −18.56% at 1× / −76.55% at 4×; conclusion
  unchanged); v1 preserved as the historical milestone (D76).
- Step 7 of `VERIFICATION_SCHEME.md` — gate passed (205/205 tests total, 42 new):
  snapshot checksum/restatement/quarantine U-gates, cleaner defect-injection gate,
  validator gate, XLE ex-date dividend G-gate (long credited/short debited, exact),
  pre-split XOP commission G-gate (as-traded vs adjusted differs by hand-computed
  $15.00 on a $32k order), split NAV-continuity, D45 no-fills assertion.

- `BacktestResult.fills` and `.cash_curve` — per-fill and per-bar-cash
  instrumentation (D77, additive).
- **THE golden master** (`tests/golden/test_the_golden_master.py` + `.hand.txt`, D39/
  D77): five-bar short-side scenario asserting every fill, commission, carry accrual,
  the dividend debit, and cash/NAV per bar against an independent calculator.
- Property invariant suite (`tests/property/test_simulator_invariants.py`, D40/D78):
  8 derandomized hypothesis invariants — cash ≥ 0 absent margin, fills within bar
  range, exact fill/position reconciliation, shadow-accountant leak tests,
  fresh-state guarantee, determinism hash.
- Cross-engine reconciliation (`tests/integration/test_cross_engine.py` +
  `docs/verification/cross_engine_reconciliation.md`, D41/D79): our engine vs
  vectorbt 1.1.0 on identical inputs — **penny-exact** (1,370 trades both sides,
  identical final value, 1.3e-12 max relative curve divergence). New dev dependency:
  `vectorbt`.
- Step 8 of `VERIFICATION_SCHEME.md` — gate passed (218/218 tests total, 13 new).
  **The simulator is anchored to references we didn't write** (Phase D milestone,
  `DEVELOPMENT_TIMETABLE.md`).
- `backtest_framework.analytics` — the analytics layer, honest by construction:
  `metrics` (Sharpe/Sortino with REQUIRED rf and periods args, geometric rf, stated
  ±inf conventions; `realised_beta`; `max_drawdown` relocated from `engine.sweep` —
  D80), `tail_risk` (VaR/CVaR gated on ≥30 tail observations, explicit
  insufficient-data results — D36/D81), `monte_carlo` (seeded block bootstrap,
  n=10,000 default, required seed — D34/D81), `tearsheet` (renders the literal
  "insufficient data (n=X, need ≥Y)" string, rf stated in the Sharpe row, D37's ≈0
  beta note).
- Step 9 X-gate: exact agreement with quantstats 0.0.81 on Sharpe (rf=0 and rf=4%),
  Sortino, and max drawdown (D83). New dev dependency: `quantstats`; `numpy`
  promoted to an explicit production dependency.
- D38's label gate reinterpreted (D82): grep-test enforces honest thesis labels on
  the strategies that exist and fails on unregistered strategy modules.
- Step 9 of `VERIFICATION_SCHEME.md` — gate passed (248/248 tests total, 30 new).
- `docs/options_extension.md` rewritten from placeholder to the real scoping decision
  (D16, D84): six hard problems, Lego audit, verification gates if built, trigger
  conditions. Doc-rot grep-test added alongside the existing OptionStub gates.
- Step 11 of `VERIFICATION_SCHEME.md` — gate passed (the stub's U-gate has been green
  since Step 3; the write-up was the remaining deliverable). 249/249 tests.
- `backtest_framework.validation` — the research-integrity layer:
  `walk_forward` (fitters receive DataViews built from training slices only — the
  D22/D28 guarded accessor, D85), `pair_selection` (Gatev-distance top-N with the
  multiplicity count returned for registry logging, D29), `dsr` (PSR/SR0/DSR with N
  and V[{SRn}] pulled from the TrialRegistry, stdlib normal functions, D86),
  `synthetic` (random-walk-spread null pairs, D87).
- `analytics.monte_carlo.block_bootstrap_paths` exposed (additive; seeded output
  byte-identical).
- Step 12 gates: DSR reproduces the Bailey & López de Prado worked example
  (N=100 → 0.9004, N=46 → 0.9505, N=88-normal → the 95% boundary; parameter recovery
  method in D86); inverting-pair walk-forward I-gate; 200-series noise-universe
  multiplicity P-gate (n_pairs_tested = 19,900 logged and read back); zero-edge
  synthetic nulls earn ≈ 0 ("stop everything" not triggered); shuffle-vs-block
  autocorrelation demonstration.
- Step 12 of `VERIFICATION_SCHEME.md` — gate passed (260/260 tests total, 13 new).
  **All in-scope verification-scheme steps are complete. The framework can say
  "no edge" and be believed** (`DEVELOPMENT_TIMETABLE.md` Phase F milestone).
- Transparent `.gz` support in `data.csv_fixture` (D88);
  `data/fixtures/universe_daily_2015_2024_raw.csv.gz` committed — 57 ETFs, 2015–2024
  raw + 2,285 dividends + 14 splits (`scripts/fetch_universe.py`).
- `costs.calibration.calibrate_impact_params` — automated σ/ADV for SqrtImpact
  (full-sample, D66 caveat carried).
- `backtest_framework.research` — the Phase G study package (framework frozen;
  research versions per study): `pairs_study.run_pairs_study` — walk-forward Gatev
  top-N selection, one multi-strategy netted run per (window, multiplier), warm-up
  prefixes, NAV-chained windows, per-trial registry logging, registry-fed DSR
  (D89/D90). `scripts/run_pairs_study.py` produces the artifact offline.
- **`docs/results/pairs_study_v1.md` — THE FIRST PHASE G RESEARCH RESULT**: 57-ETF
  universe, 35 OOS windows, 1,596 pairs scored per window; gross +3.45%, −13.01% at
  real costs, monotone sweep, **DSR = 0.0000** with the multiplicity caveat stated.
  The framework's milestone claim — saying "no edge" believably — exercised on real
  data. (273/273 tests total, 13 new.)
- `docs/TUTORIAL.md` — the start-to-output usage guide; every `# runnable` example
  block is executed verbatim by `tests/integration/test_tutorial.py` (D91), so the
  tutorial breaks CI rather than rotting. Linked from README. (275/275 tests.)
- `research/cointegration.py` — Engle-Granger β + residuals, ADF t-statistic
  (statistic only, rank-don't-threshold per D29; tied to statsmodels at 1e-9 as a
  dev-dep X-anchor, D93), and `CointegrationSelector` (Gatev prefilter → β coherence
  window → ADF rank, D92). `run_pairs_study` gains an optional `selector` (v1
  default preserved). New dev dependency: `statsmodels`.
- **`docs/results/pairs_study_v2.md` — study v2**: selection is the only change from
  v1; gross +3.45% → **+19.03%**, profitable at 0.5× costs (+5.70%), still −6.43%
  at full retail costs, DSR = 0.0000 with the program-level multiplicity note. The
  "edge exists but doesn't clear retail frictions" thesis, measured. (281/281
  tests, 8 new.)
- `research/beta_zscore.py` — `BetaHedgedZScoreStrategy` (D94): trades the
  train-window Engle-Granger β (spread = ln A − β·ln B, legs in the β ratio),
  weights normalized to constant gross (w_A = 2w/(1+β), w_B = 2wβ/(1+β)); β = 1
  reduces exactly to `ZScorePairsStrategy` — tested as a target-level identity AND
  a whole-study equity-curve identity. `run_pairs_study` gains an optional
  `strategy_factory(pair, strategy_id, config, details)` hook (v1/v2 default
  preserved; called per window/multiplier/pair; receives the pair's
  selector-details entry carrying its fitted β).
- **`docs/results/pairs_study_v3.md` — study v3**: trading is the only change from
  v2; the β hedge **hurt** — gross +19.03% → **+6.12%**, 1× costs −6.43% →
  **−16.53%**, DSR = 0.0000. Train-window β carried out-of-sample imports more
  estimation noise than hedge benefit on a selector-coherent (β ≈ 1) universe; the
  1:1 hedge stands. (288/288 tests, 7 new.)
- `research/capacity.py` (D95): recording cost-stack wrappers (D68 delegation
  pattern, accumulate instead of multiply) feeding a `CostLedger` — per-brick
  friction attribution plus per-symbol max |Q| for participation reporting; the
  recorder returns inner values unchanged (transparency is a tested whole-study
  identity). `run_capacity_study` runs the v2 study per AUM level at real
  unscaled costs; `run_pairs_study` gains an optional `base_stack` hook
  (None-default, v1/v2/v3 byte-identical).
- **`docs/results/capacity_analysis.md` — the capacity analysis**: v2's study at
  nine AUM levels, $10k–$100M. **No level clears real costs**: the hump lands as
  predicted (commission minimums small, √-impact large; optimum $300k at
  −5.77%/9yr) but ≈+2.01%/yr of gross edge faces 2.68%/yr of drag at the optimum,
  half of it the scale-invariant floor of a ~200% gross book. Cross-checks: the
  $100k row reproduces v2's −6.43% exactly; $100M gross +19.04% vs v2's +19.03%.
  (295/295 tests, 7 new.)
- `research/gross_sweep.py` (D96): `run_gross_sweep` — one capacity study per
  leg_weight (thin composition), with net-return / margin-drag / total-drag
  matrix renderers; `run_capacity_study` gains `trial_prefix` (default
  "capacity" preserves the D95 artifact's trial ids).
- **`docs/results/gross_exposure_study.md` — the gross exposure study**:
  leg_weight {0.25, 0.5, 0.75, 1.0} × AUM {$100k…$10M}, real unscaled costs.
  The margin threshold collapses as predicted (0.866%/yr at lw 1 → 0 below
  gross ≤ NAV) and **five low-gross cells clear absolute costs** (best lw 0.5 @
  $300k, +0.12%/yr vs +1.03%/yr gross) — **but none clear the 4% risk-free
  hurdle** (best cell Sharpe −1.61; idle-cash-interest caveat stated both
  ways). The two-sided headline: at low gross the edge pays for its own
  implementation, not for the capital it occupies. (299/299 tests, 4 new.)
- **`docs/writeup.md` — the Phase G writeup skeleton (D97)**: the portfolio
  document; methodology-first, ten sections + appendices, all five studies'
  headline numbers final and quoted from committed artifacts, `[TODO prose]`
  markers for narrative polish only. `tests/unit/test_writeup.py` anchors 24
  (number, source-artifact) pairs so a re-run study that moves a headline
  fails CI, asserts required sections, enforces the prose-only-TODO rule, and
  checks the README link. README brought current (stale "pre-implementation"
  status replaced; writeup is the lead link). (326/326 tests, 27 new.)

### Changed
- Bar/event timestamps are normalized to naive exchange-local wall time at the data
  boundary (D75) — daily-bar identity is the exchange-local date, and D33's
  calendar-day carry must not be DST-sensitive.
- `config.carry_model`'s factory now builds `costs.bricks.FlatRateCarry` instead of the
  retired `CarryModel` demonstration class, per that class's own docstring (D54). No
  change to `SimConfig`'s shape or to Step 2's four passing gates.
- **Breaking**: `Strategy.generate_targets` now takes `Mapping[str, DataView]` instead
  of a single `DataView`; `ScheduledWeightStrategy` now takes `weights_by_instrument`
  instead of `instrument_id`/`weight`; `run_backtest` now takes `bars_by_instrument`
  instead of `bars`/`instrument_id`. Single-instrument is the N=1 case throughout
  (D64). The Step 3/D53 golden-master reproduction test was migrated and re-verified
  to produce identical numbers under the new signatures.

<!--
Template for future entries:

## [x.y.z] - YYYY-MM-DD

### Added
- New feature X (see D50)

### Changed
- Behaviour of Y (see D51)

### Fixed
- Bug in Z

### Deprecated / Removed
-->
