# AI TODO

Claude's current working task list for this project — not a roadmap (that's
[`DEVELOPMENT_TIMETABLE.md`](DEVELOPMENT_TIMETABLE.md)) and not a decision log (that's
[`docs/decisions/`](docs/decisions/README.md)). Kept short: only what's immediately in front of
us. Update this at the start/end of each working session — stale entries here are worse than
none.

## Now

- [x] Set up the full doc suite (ADR records, RULES.md, CHANGELOG.md, this file, README.md)
- [x] Initialize local git repo + `.gitignore`
- [x] Write `PHILOSOPHY.md`, wired into README.md and RULES.md
- [x] Scaffold the Python project (`uv`, src-layout, pytest + hypothesis — logged as D50)
- [x] **Step 1 of `VERIFICATION_SCHEME.md` — gate passed.** TrialRegistry (D20), stop-gap
      fill fix (D10), calendar-day carry accrual (D33, + day-count convention D51). 20/20
      tests green: 7 golden (stop fills), 4 golden + 1 property (carry accrual), 8 unit
      (registry).
- [x] Commit Step 1 code + D50/D51 decision records
- [x] **Step 2 of `VERIFICATION_SCHEME.md` — gate passed.** Declarative config + factories
      (D35), config schema convention logged as D52. 35/35 tests green (15 new).
- [x] **Phase A milestone reached: the reproducibility loop closes** — a trial can be
      logged, reloaded, and re-run identically (`test_reproducibility_loop.py`).
- [x] Commit Step 2 code + D52 decision record
- [x] **Step 3 of `VERIFICATION_SCHEME.md` — gate passed.** CostStack + Instrument +
      signal→target→order pipeline (D1, D2, D12, D27). Greenfield reinterpretation of
      the "refactor regression" gate logged as D53 (no legacy engine exists to reconcile
      against — this step's own golden scenario is now the baseline). Interface design
      choices logged as D54 (CostStack/Instrument) and D55 (pipeline sizing). 60/60 tests
      green (25 new). Migrated Step 2's `CarryModel` demo into
      `costs.bricks.FlatRateCarry`, exactly as its docstring always said would happen.
- [x] Commit Step 3 code + D53/D54/D55 decision records
- [x] **Step 4 of `VERIFICATION_SCHEME.md` — gate passed.** DataView look-ahead guard
      (D32), per-bar RiskMonitor (D30), Allocator stand-in (D31). DataView built so
      future bars are never stored at all, not merely access-gated (D56) — genuinely
      immune to reflection tricks, not just underscore-prefixed. RiskMonitor's exposure
      formula and simulate-then-check pretrade design logged as D57. Allocator wired
      into `Sizer.capital_by_strategy` with a test proving the connection (D58), closing
      the loop D55 (Step 3) left open on purpose. 78/78 tests green (18 new).
- [x] Commit Step 4 code + D56/D57/D58 decision records
- [x] **Phase B complete.** Both Step 3 and Step 4 gates pass — the whale is done,
      without needing the pre-committed slip rule (refactor regression gate has been
      green since Step 3, no need to split D27 out to Phase D).
- [x] **Minimal data source + production engine loop, planned and built.** Not a
      numbered `VERIFICATION_SCHEME.md` step — inserted infrastructure to unblock
      Step 5/6, scoped via `EnterPlanMode` before writing code (first time this
      session; new architectural ground warranted it). Built `data.yfinance_source
      .EquityDataSource` (unhardened D18-lite, D59) and `engine.backtest.run_backtest`
      generalizing Step 3's test-only harness into a real, multi-strategy-capable loop.
      95/95 tests green (17 new), offline by default — one `@pytest.mark.live_fetch`
      test hits real yfinance and is excluded from normal runs per
      `VERIFICATION_SCHEME.md`'s own cross-cutting gate.
- [x] Commit this chunk's code + D59-D62 decision records
- [x] **Multi-instrument bar alignment for pairs, planned and built (D45).** Second
      `EnterPlanMode` pass this session — the Strategy/run_backtest interface change
      was breaking, not additive, and worth aligning on before touching well-tested
      code. Built `data.alignment.align_bars` (D63, inner join) and generalized
      `Strategy`/`ScheduledWeightStrategy`/`run_backtest` to multi-instrument, with
      single-instrument as the N=1 case (D64). Migrated the Step 3/D53 golden-master
      test to the new signature and re-ran it — identical numbers, not assumed.
      104/104 tests green (9 new + migrations), offline by default. Real XLE/XOP pair
      confirmed running end-to-end via a `live_fetch`-marked smoke test.
- [x] Commit this chunk's code + D63/D64 decision records
- [x] **Step 5 of `VERIFICATION_SCHEME.md` — gate passed.** Real equity cost bricks in
      `costs/equity_bricks.py`: `IBKRCommission` (D4/D65, 13-row X-table incl. the
      cap-overrides-min penny-stock case), `SqrtImpact` (D3/D66, fraction ∝ √Q and
      dollars ∝ Q^1.5 both asserted; loud errors on missing/zero ADV), `MarginInterest`
      (D5/D67, portfolio-level base max(gross − NAV, 0) via a new
      `CostStack.portfolio_carry_bricks` slot + start-of-bar snapshot in the engine).
      Frozen D53/pairs baselines re-run and confirmed byte-identical (new slot defaults
      empty). 134/134 tests green (30 new).
- [x] Commit Step 5 code + D65/D66/D67 decision records
- [x] **Step 6 of `VERIFICATION_SCHEME.md` — gate passed. THE FIRST REAL NUMBER
      EXISTS (Phase C milestone, R1's existence-justification gate).**
      `docs/results/first_real_number.md`: XLE/XOP z-score pairs, 2015–2024 frozen
      fixture, full real cost stack, 0×/0.5×/1×/2×/4× sweep. **+13.2% gross at 0×
      costs; −22.7% at 1× real costs** — perfectly monotonic, the (weak) gross edge
      is entirely destroyed by real frictions. Ugly, produced, logged, framed. Built:
      sweep harness (D8/D68), `ZScorePairsStrategy` (D69), committed CSV fixture as
      pre-Step-7 snapshot (D70), `BorrowFee` brick (D71). 163/163 tests green (29
      new), both D8 gates asserted on synthetic AND real data, offline.
- [x] Commit Step 6 code + D68–D71 records + the results doc
- [x] **Step 7 of `VERIFICATION_SCHEME.md` — gate passed; v2 first number produced.**
      Full hardened data path: content-addressed SnapshotStore (D72), drop-and-report
      cleaner (D73 — zero changes needed on the real fixture, reported as zero),
      sanity gate with observed-data-calibrated thresholds (D74), corporate actions
      with two price frames + dividend flows + split scaling (D75), and
      `docs/results/first_real_number_v2.md` alongside the preserved v1 (D76):
      **+21.74% at 0× / −18.56% at 1× / −76.55% at 4×** — conclusion unchanged, the
      edge doesn't survive real costs, but the number now rests on a validated,
      frozen, reproducible-by-hash data path. 205/205 tests green (42 new).
- [x] Commit Step 7 code + D72–D76 records + the v2 results doc
- [x] **Step 8 of `VERIFICATION_SCHEME.md` — gate passed. The simulator is anchored
      to references we didn't write (Phase D milestone).** THE golden master (D77:
      5-bar short-side scenario, every fill/carry/flow/cash/NAV line asserted against
      an independent calculator — the $1 IBKR minimum, the dividend debit on the
      short, drifting margin bases all fire), 8 property invariants (D78,
      derandomized hypothesis incl. the shadow-accountant leak test), and
      cross-engine reconciliation vs vectorbt 1.1.0 (D79): **penny-exact — 1,370
      trades in both engines, identical final value $159,233.023491, max curve
      divergence 1.3e-12 relative, divergence table empty**
      (`docs/verification/cross_engine_reconciliation.md`). 218/218 tests green.
- [x] Commit Step 8 code + D77–D79 records + the reconciliation doc
- [x] **Step 9 of `VERIFICATION_SCHEME.md` — gate passed.** The analytics layer
      exists and is honest by construction: `analytics/` (metrics with REQUIRED
      rf/periods args and geometric rf — D80; VaR/CVaR gated at ≥30 tail
      observations, so n≥600 at 95% — D81; seeded block-bootstrap MC, n=10k default,
      seed required — D81; tearsheet that literally prints "insufficient data
      (n=X, need ≥Y)"). X-gate vs quantstats 0.0.81: EXACT ties on Sharpe (rf=0 and
      rf=4%), Sortino, max drawdown (D83). D38 reinterpreted (D82): no sector
      momentum exists to label; the grep-test enforces honest labels on existing
      strategies and fails on any unregistered new strategy module. 248/248 tests
      green (30 new).
- [x] Commit Step 9 code + D80–D83 records
- [x] **Step 11 of `VERIFICATION_SCHEME.md` — gate passed (U-gate green since
      Step 3; the deliverable was the write-up).** `docs/options_extension.md` is now
      the real scoping decision (D84): six hard problems (data is the blocker;
      expiry/assignment lifecycle is the deepest engine gap — finite-lived
      instruments break D45's alignment assumption), the Lego audit (what bolts on
      vs what's engine surgery), verification gates if ever built, and explicit
      trigger conditions (pairs writeup first, per R1). Doc-rot grep-test added.
- [x] Commit Step 11 doc + D84 record
- [x] **Step 12 of `VERIFICATION_SCHEME.md` — gate passed. THE FRAMEWORK IS
      COMPLETE.** All in-scope verification-scheme steps (1–9, 11, 12; Step 10 is
      the timetable's pre-committed cut) are done. Milestone: *the framework can now
      say "no edge" and be believed.* Walk-forward with structurally-guarded fitting
      (D85 — fitters receive DataViews built from training slices only; the same
      socket enforces D28 for future regime models), Gatev top-N selection returning
      its multiplicity count for registry logging (D29), DSR reproducing the
      Bailey/López de Prado worked example with N and V pulled from the
      TrialRegistry (D86 — paper checkpoints N=46→0.9505, N=88-normal→boundary,
      N=100→0.9004), synthetic random-walk-spread nulls earning ≈0 at zero cost
      (D87 — "if this profits, stop everything": it didn't), and the quantified
      shuffle-vs-block demonstration. 260/260 tests green (13 new).
- [x] Commit Step 12 code + D85–D87 records
- [x] **PHASE G HAS BEGUN: pairs study v1 produced — the first research artifact.**
      Universe fetcher (57 ETFs, zero exclusions/failures, 14 splits + 2,285
      dividends as events, 2.5MB gzipped fixture — D88), automated σ/ADV calibration
      (`costs/calibration.py`), and the study runner (`research/pairs_study.py` —
      D89: one multi-strategy run per window with netted shared legs, warm-up
      prefix, window chaining). **Result (`docs/results/pairs_study_v1.md`): gross
      +3.45% over 35 OOS windows (~0.4%/yr — essentially nothing pre-cost), −13.01%
      at real costs, monotone to −49.91% at 4×, DSR = 0.0000 with the multiplicity
      caveat stated (D90). The framework said "no edge" on real data and can be
      believed — the milestone claim, exercised.** 273/273 tests green (13 new).
- [x] Commit Phase G kickoff: fixture, calibration, study runner, artifact, D88–D90
- [x] **`docs/TUTORIAL.md` — the full usage guide, executable (D91).** Nine
      `# runnable` blocks covering setup → hello-world → real cost stack → custom
      strategy → clean/validate/snapshot (incl. a live quarantine refusal) → sweep →
      registry → analytics → walk-forward/DSR → a mini end-to-end study; all
      extracted and exec'd verbatim by `tests/integration/test_tutorial.py`, so the
      tutorial fails CI instead of rotting. Linked from README.
- [x] Commit the tutorial + D91
- [x] **Study v2: cointegration-filtered selection — the filter works, the
      conclusion holds (D92/D93).** One variable changed from v1 (selection: Gatev
      prefilter → EG β with [0.7,1.3] coherence window → ADF rank; β logged, not
      traded). Own 40-line ADF statistic tied to statsmodels at 1e-9 (dev-dep
      X-anchor). **Result (`docs/results/pairs_study_v2.md`): gross +3.45% → +19.03%
      — a real selection edge; PROFITABLE at 0.5× costs (+5.70%); still −6.43% at
      full retail costs; DSR = 0.0000.** The cleanest possible evidence for the
      "edge exists but doesn't clear retail frictions" thesis — v2 turned the
      writeup's central claim from assertion into measurement. 281/281 tests (8 new).
- [x] Commit study v2 + D92/D93
- [x] **Study v3: β-hedged trading — the hedge HURT, and that's the finding (D94).**
      One variable changed from v2 (trading: each pair trades its train-window EG β,
      spread = ln A − β·ln B, legs in the β ratio, weights normalized to constant
      gross 2w so risk matches v1/v2 exactly). New `research/beta_zscore.py` +
      `strategy_factory` hook in the study runner (`None` = v1/v2 byte-identical);
      β=1 provably reduces to the old strategy — tested at target level AND as a
      whole-study equity-curve identity. **Result (`docs/results/pairs_study_v3.md`):
      gross +19.03% → +6.12%; 1× costs −6.43% → −16.53%. A train-window β carried
      OOS imports more estimation noise than hedge benefit — the selector's [0.7,1.3]
      coherence window already leaves the hedge little room to help. The 1:1 hedge
      wins; the writeup gains a genuine estimation-error exhibit.** 288 tests (7 new).
- [x] Commit study v3 + D94
- [x] **Capacity analysis: NO account size clears real costs — the hump measured
      (D95).** The v2 study run at 9 log-spaced AUM levels ($10k–$100M) with the
      real UNSCALED stack — the bricks themselves produce the size dependence
      (multiplier sweep can't see size). New `research/capacity.py`: recording
      wrappers (D68 delegation pattern, accumulate not multiply) → CostLedger
      per-brick attribution + per-symbol max |Q|; `base_stack=None` hook in the
      study runner (v1/v2/v3 byte-identical); recorder transparency is a tested
      identity. **Result (`docs/results/capacity_analysis.md`): the hump lands
      where theory predicts — $10k −20.06% (commission minimums), optimum $300k
      −5.77%, $100M −59.05% (impact, at 143% of ADV = deep extrapolation) — but
      the whole curve is below zero. At the optimum: gross ≈+2.01%/yr vs 2.68%/yr
      total drag, half of it the scale-invariant floor of a ~200% gross book
      (margin 0.87% + spread 0.38% + borrow 0.11%). Even free margin funding only
      lifts the optimum to ≈+0.19%/yr. Cross-checks: $100k row reproduces v2's
      −6.43% exactly; $100M gross +19.04% vs v2's +19.03%.** 295 tests (7 new).
- [x] Commit capacity analysis + D95
- [x] **Gross exposure study: five low-gross cells clear absolute costs — but
      none clear the risk-free hurdle (D96).** One variable: leg_weight
      (book gross = 2·lw·NAV), grid {0.25, 0.5, 0.75, 1.0} × {$100k…$10M}. The
      margin threshold (max(gross − NAV, 0)) collapsed exactly as predicted:
      0.866%/yr drag at lw 1 → 0.220% at lw 0.75 → 0.000% at lw ≤ 0.5. **Result
      (`docs/results/gross_exposure_study.md`): best cell lw 0.5 @ $300k at
      +0.12%/yr net vs +1.03%/yr gross — positive absolute net, but Sharpe −1.61
      vs the 4% rf: underperforms T-bills by ≈3.9%/yr. The two-sided headline:
      at low gross the edge can just pay for its own implementation; it cannot
      pay for the capital it occupies.** Honest notes: sim credits no interest
      on idle cash (a ≤100%-gross book is mostly idle cash — recorded in D96);
      five-study multiplicity makes any thin positive indistinguishable from
      zero anyway. 299 tests (4 new).
- [x] Commit gross exposure study + D96
- [x] **The Phase G writeup skeleton — the portfolio document exists (D97).**
      `docs/writeup.md`: ten sections + appendices, methodology-first (the
      trust story leads), every headline number final and quoted from a
      committed artifact; `[TODO prose]` marks narrative polish only — a
      tested rule (numbers are never TODO). Anchor test
      (`tests/unit/test_writeup.py`): 24 (number, source-artifact) pairs must
      appear in BOTH documents, so a re-run study that moves a headline fails
      CI instead of letting the writeup lie. Records the pre-registration
      correction ("clears at £X AUM" → what was actually measured) and the
      evidence-based Kalman cut (v3's estimation-error result). README updated:
      writeup is now the lead link; stale "pre-implementation" status fixed.
      326 tests (27 new).
- [ ] Commit writeup skeleton + D97

## Next (queued, not started) — Phase G closing

- [ ] **Writeup polish**: expand the `[TODO prose]` sections (pairs-trading
      motivation ¶, gate-discipline ¶, DSR intuition ¶, institutional-scenario
      arithmetic, universe appendix table). Then freeze v1 of the writeup.
- [ ] **Reviewer outreach** (timetable: parallel task, human-led) — QuantNet/
      Wilmott, LinkedIn, meetups; the writeup attaches as-is since its numbers
      are final.
- [ ] Study candidates if research resumes: parameter sensitivity (every
      variant logged → honest DSR); an idle-cash interest brick (the material
      cost-model gap the gross sweep exposed).
- [ ] Wire `analytics.tearsheet` into the v1/v2 first-number scripts (own diff).
- [x] Config factories for real bricks + strategy (D52) for full re-run-from-config
      — done as D102 (audit remediation): the study stack is config-built, the
      trial config covers every determining field, and `StudyConfig.from_dict`
      closes the study-level reproducibility loop.
- [x] Per-window σ/ADV calibration (closes D66's deferral) — done as D102
      (`impact_calibration="train_window"`); priced against full-sample in the
      convention-sensitivity artifact (D105).
- [x] **Audit remediation (AUDIT_REPORT.md, all 31 findings dispositioned).**
      Fixed: DSR units + trial pool (D98 — the one result-corrupting finding),
      duplicate/empty/grid/event-ordering guards (D99), carry_components
      enforcement (D100), pretrade gate + sleeve fills (D101), declarative stack
      config + train-window calibration (D102), next-open fill mode (D103),
      property-suite scope (D104), convention-sensitivity study (D105), plus the
      hygiene sweep (mypy clean, doc rot, dead code). Pinned-not-changed: share
      rounding, carry mark timing, MC block length (D106). Deferred with written
      rationale per R3: margin lock, stop/limit fill menu, FX brick, IS/OOS
      ratio, registry artifact policy (D107).

## Watch list additions

- D79: at target weight ≈ 1.0, vectorbt reserves fees from the purchase while we
  charge fees to cash — a real convention difference, documented, deliberately below
  the comparison's 0.6 weight. Revisit if any strategy ever runs at full investment.

## Watch list (not urgent, don't forget)

- R1: no framework scope creep beyond the current build order until the XLE/XOP walk-forward
  produces a first real number (Phase C milestone, week ~8, kill criterion at week 10).
  This is the next real gate — Phase C is where R1 actually bites.
- **IBKR schedule manual check owed (D65):** pricing pages 403-block automated fetches,
  so the brick's constants ($0.005/sh, $1 min, 1% cap) are anchored to the well-known
  published schedule but not re-verified against the live page. One-time human eyeball
  of interactivebrokers.com discharges this.
- D66: `SqrtImpact` σ/ADV are static config params — estimation from data belongs with
  Step 7 snapshots (and must obey D44's no-same-bar-lookahead rule when built).
- D62: `RiskMonitor` violations are recorded but not enforced in `run_backtest` — no
  corrective orders, no halt. Revisit once there's a validated strategy to inform what
  "corrective" should actually mean (same reasoning D31 used to defer real allocation).
- D63: alignment uses exact-timestamp matching, no tolerance window — fine for one
  `DataSource` fetching both legs the same way; revisit if a future data source
  produces genuinely offset timestamps for the same session.

## Log

- **2026-07-13** — Doc suite created (D1–D49 migrated to `docs/decisions/`, R1–R4 moved to
  `docs/RULES.md` + R5 added, `CHANGELOG.md`/`README.md`/`AITODO.md` created, git initialized).
  Old `DESIGN_DECISIONS.md` and `MASTER_PROJECT_DOC.md` marked as frozen historical snapshots.
  Implementation not yet started.
- **2026-07-13** — `PHILOSOPHY.md` added: five pillars (structural trust, honesty over
  comfort, anti-self-deception, composability, scope discipline) extracted from the pattern
  across the existing 49 decisions, not written fresh. Sits above `docs/RULES.md` and
  `docs/decisions/` as the thing new decisions get checked against. Requested explicitly
  before starting Step 1, so it's settled before any code exists.
- **2026-07-13** — Step 1 implemented and gate passed. Scaffolded with `uv` (src-layout,
  pytest + hypothesis — D50). Built `backtest_framework.simulator.fills.stop_fill_price`
  (D10: gap-through-stop fills at the bar open) and
  `backtest_framework.simulator.carry.accrue_carry*` (D33: calendar-day accrual; day-count
  convention ACT/365 logged separately as D51 since D33 never specified one). Built
  `backtest_framework.registry.trial_registry.TrialRegistry` (D20: SQLite-backed,
  append-only via primary key, deterministic canonical-JSON hash over
  config+snapshot_id+seed). 20 tests, all green — golden-master hand-arithmetic files sit
  next to their test files per D39. No portfolio/broker/engine built yet; Step 1 stayed
  deliberately narrow (pure functions + registry), full integration is Step 3's job.
- **2026-07-13** — Step 2 implemented and gate passed. Built a generic
  `FactoryRegistry`/`ConfigError` pair (`backtest_framework.config.factory`) plus a
  `SimConfig` validator (`config.sim_config`) and two demonstration model configs,
  `CarryModel`/`FillModel`, that wrap Step 1's `accrue_carry_between_bars` and
  `stop_fill_price` behind the `{"type": ..., ...params}` schema — logged as D52.
  Deliberately did *not* pull Step 3's CostStack/Instrument refactor forward just because
  the verification scheme's Step 2 test language ("mini-backtest", "equity curves")
  implied richer objects than currently exist; built the mechanism generically instead and
  proved it against what's real. All four Step 2 gates pass, including the full
  reproducibility loop (config → hash → registry → reload → re-run), which is also the
  Phase A milestone. 35 tests total, all green.
- **2026-07-13** — Step 3 ("the whale") implemented and gate passed. Built
  `instruments.base.Instrument` (Protocol, D12), `instruments.equity.Equity`, and
  `instruments.option_stub.OptionStub` (D16, with `docs/options_extension.md` created as
  a stub so its `NotImplementedError` points somewhere real). Built
  `costs.bricks`/`costs.stack.CostStack` (D1, D2) with toy trade/carry bricks. Built
  `pipeline.sizing` (D27): stateless `Sizer`, cross-strategy netting, per-strategy
  virtual books (D46). Hit a real gap immediately: the verification scheme's "refactor
  regression" gate assumes a pre-refactor engine exists to reconcile against, and this
  project has none — reinterpreted explicitly as D53 rather than silently skipped, and
  proved out with a hand-computed 3-bar golden scenario
  (`test_step3_refactor_regression.py`) that's now the frozen baseline for future
  refactors of these three components. Migrated Step 2's `CarryModel` demo class into
  `costs.bricks.FlatRateCarry` per its own stated intent; re-ran Steps 1/2's full suite
  afterward to confirm no regression before adding Step 3's own tests. Design choices for
  the Instrument/CostStack shapes and the pipeline's stateless design logged as D54/D55.
  60 tests total, all green (25 new). Did not build a Portfolio/broker class — the mini-
  backtest harness proving Step 3's components compose stays test-only, explicitly not
  promoted to src/, since general portfolio/engine state is Step 4+'s job.
- **2026-07-13** — Step 4 implemented and gate passed; Phase B complete. Built
  `engine.dataview.DataView` (D32) using a "never store what you can't see" design
  rather than access-gating a full series — future bars aren't reachable by any means,
  including direct access to the "private" field, because the object never holds them
  (D56). Built `engine.risk.RiskMonitor` (D30): gross exposure sums absolute notional
  (longs and shorts both count, matching the pairs-trading framing in D5), with
  `pretrade_check()` reusing `evaluate()`'s exact logic via a simulate-then-check
  pattern (D57). Built `engine.allocator.ConstantSplitAllocator` (D31) and a test
  proving its output feeds `Sizer.capital_by_strategy` unmodified (D58) — actually
  closing the gap D55 flagged rather than leaving it as an unverified intention. 78
  tests total, all green (18 new), including a hand-computed integration scenario
  proving a pairs position drifts into a risk violation via price movement alone with
  no order ever submitted, flagged on exactly the correct bar.
- **2026-07-13** — Data source + production engine loop chunk implemented. Planned via
  `EnterPlanMode` first (user asked to scope this explicitly) since it crossed real
  architectural thresholds Steps 1-4 hadn't: first production dependency (`yfinance`
  + `pandas`, `pyproject.toml` was `dependencies = []` until now), first stateful
  portfolio class, first strategy interface. Built `data.bars.TimestampedBar` (wraps
  `Bar` rather than extending its schema — D60), `data.source.DataSource` +
  `data.yfinance_source.EquityDataSource` (D18-lite, explicitly unhardened — no D24
  snapshotting, D25 cleaning, D26 sanity gate; no volume/ADV field), and
  `engine.portfolio.PortfolioState`, `engine.strategy.Strategy` +
  `ScheduledWeightStrategy`, `engine.backtest.run_backtest` — the production
  generalization of Step 3's test-only `run_mini_backtest`. Registered a `live_fetch`
  pytest marker excluded by default, matching `VERIFICATION_SCHEME.md`'s own
  cross-cutting gate language exactly. Caught a plan-vs-reality mismatch before it
  became a bug: the plan called the reference strategy "FixedWeightStrategy," but the
  regression-anchor test needs a *changing* weight schedule (0.5→0.5→0.0) — corrected
  to `ScheduledWeightStrategy` during implementation. Verified independently (not
  assumed) that `run_backtest`'s per-bar NAV-based capital allocation (D61) still
  reproduces Step 3's frozen golden numbers exactly, via a standalone bar-by-bar trace
  in `test_backtest_loop.hand.txt`. RiskMonitor violations are recorded but not
  enforced in the loop (D62), tested explicitly rather than left implicit. 95 tests
  total, all green (17 new, one `live_fetch`-marked test excluded from the default
  count and confirmed to pass separately against real yfinance data).
- **2026-07-13** — Multi-instrument bar alignment (D45) implemented, unblocking a real
  XLE/XOP pair. Planned via `EnterPlanMode` again since the change was breaking:
  `Strategy.generate_targets` moved from one `DataView` to `Mapping[str, DataView]`,
  `ScheduledWeightStrategy` from `(instrument_id, weight)` to `weights_by_instrument`,
  `run_backtest` from `(bars, instrument_id)` to `bars_by_instrument` — single
  instrument is now the N=1 case throughout, mirroring the precedent D55/D58 already
  set (D64). Built `data.alignment.align_bars` (D63): inner join on exact timestamp
  equality: a bar missing on one leg drops that timestamp for every leg, and carry
  accrues correctly across the resulting gap with no special-case code, since it's
  already driven by consecutive timestamps rather than bar count (same mechanism D33
  uses for weekends). Migrated `test_strategy.py` and `test_backtest_loop.py`
  (including the Step 3/D53 golden-master reproduction test) to the new signatures and
  re-ran them — identical numbers confirmed, not assumed, same discipline as the
  Step 2→3 `CarryModel` migration. New: a hand-computed synthetic scenario proving a
  dropped bar on one leg drops it for both and carry spans the real 2-day gap
  (`test_pairs_backtest.hand.txt`), plus a `live_fetch`-marked test running a real
  long-XLE/short-XOP pair through `run_backtest` end-to-end. 104 tests total, all
  green (9 new plus in-place migrations).
- **2026-07-13** — Step 5 implemented and gate passed. New `costs/equity_bricks.py`
  alongside (not replacing) the toys: `IBKRCommission` (Fixed schedule, min/cap
  ordering pinned by a 13-row hand table — the cap-overrides-min penny-stock row is
  the one that catches the tempting-but-wrong formula), `SqrtImpact` (the U-gate's
  "√2 on doubling" clarified in D66 to apply to the impact *fraction*, with total
  dollars asserted at 2√2 — implementing dollars ∝ √Q literally would be the wrong
  model and D3's "industry-standard" rationale controls), `MarginInterest` (needed a
  genuinely new engine concept: a `portfolio_carry_bricks` slot on CostStack, charged
  once per bar on max(gross − NAV, 0) from a start-of-bar snapshot so per-leg carry
  deductions can't perturb the margin base mid-step — D67; reuses
  `engine.risk.gross_exposure`, one exposure formula everywhere per D57's argument).
  Tried to anchor the IBKR constants against the live pricing page during planning;
  403-blocked, so the caveat is written into the hand file and a manual check is on
  the watch list rather than quietly claiming the X-gate fully discharged. Frozen
  baselines re-run and confirmed unchanged. 134 tests, all green (30 new).
- **2026-07-14** — **Step 6: THE FIRST REAL NUMBER (Phase C milestone, R1 satisfied).**
  Planned via `EnterPlanMode` (three gate terms needed pre-Step-7/9/12 readings, all
  logged: "frozen snapshot" → committed CSV fixture D70; "tearsheet" → minimal
  markdown sweep table D68; "walk-forward" → trailing-only forward simulation, no
  fitted parameters exist to walk forward from, D69). Built `costs/scaling.py` (per-
  brick multiplier wrappers), `engine/sweep.py` (strategy-*factory* API so stateful
  strategies can't leak across multiplier runs), `strategies/zscore_pairs.py` (fixed
  1:1 log-hedge, hysteresis, D44-honoring previous-bar windows), `BorrowFee` (D71),
  `data/csv_fixture.py` + fetched/committed the 2015–2024 XLE/XOP fixture (2,515
  bars/leg, σ/ADV printed for impact params). Result: **+13.21% at 0× / −6.35% at
  0.5× / −22.70% at 1× / −47.31% at 2× / −76.43% at 4×** — monotonic, gross edge
  fully consumed by real costs; caveats (famous-pair bias per D22, adjusted prices
  per D6, full-sample σ/ADV calibration) stated in the results doc, not hidden.
  Bonus finding: the fixture surfaced a real OHLC epsilon artifact (XOP 2018-10-24,
  close < low by 1.2e-16) — a concrete preview of D26's sanity-gate work, handled
  with a stated tolerance per D47. 163 tests, all green (29 new); the e2e run is an
  offline repeatable test, not a one-off.
- **2026-07-14** — **Step 7: data layer hardening + v2 first number (Phase D core).**
  Planned via `EnterPlanMode`; user approved including the v2 re-run. Built the full
  D24/D25/D26 pipeline (`snapshot_store`, `cleaner`, `validator`) plus D6's corporate
  actions (`corporate_actions`, `DividendFlow` event brick + 4th CostStack slot,
  split position scaling + view/execution series split in `run_backtest`). **The data
  taught us three things the plan had wrong**: (1) yfinance `auto_adjust=False` is
  ALREADY split-adjusted — prices AND dividends — so the true as-traded frame is
  *reconstructed*, not fetched (verified via frame-continuity on XOP's split, D75);
  (2) my remembered XOP split date (June 2020) was wrong — it's 2020-03-30, read from
  the data; (3) the validator's first split-aware check judged only the as-traded
  frame and QUARANTINED our own clean provider-frame snapshot with a fabricated −75%
  violation — the gate structurally refused bad validation logic, the bug was fixed
  (frame-robust: explained if small in either frame, D74), and the store needed
  meta-refresh-on-refreeze so a fixed validator can un-quarantine (D72). Thresholds
  calibrated to observed genuine data: XOP's real −37% crash day warns, doesn't
  block. Also normalized timestamps to naive exchange-local at the data boundary —
  aware timestamps would have made D33's carry DST-sensitive. Cleaner made zero
  changes on the real fixture (reported as zero). v2 result: +21.74%/−18.56%/−76.55%
  at 0×/1×/4× — same conclusion as v1, now on a reproducible-by-content-hash path.
  205 tests, all green (42 new). v1 doc untouched (D76).
- **2026-07-14** — **Step 8: testing hardening; the simulator is anchored to
  references we didn't write.** Two gate clauses reinterpreted openly (D77/D78, D53
  discipline): no stop orders exist in the engine so THE golden master covers the
  engine as built (gap-through-stop keeps its Step 1 unit-level golden), and there's
  no broker class to reset so the fresh-state guarantee is asserted as
  identical-runs-identical. Added fills/cash_curve instrumentation to BacktestResult
  (additive; baselines unchanged). THE golden master: independent calculator (never
  imports the framework) → hand file → line-by-line assertions; the short-side
  scenario fires every brick at once, including the $1 IBKR minimum on a 53-share
  re-size and the −$626.50 dividend debit. Property suite: 8 derandomized hypothesis
  invariants; the shadow accountant (zero costs → NAV change ≡ position × Δprice) is
  the strongest leak detector short of duplicating the engine. Cross-engine (D79):
  fed vectorbt the identical precomputed MA-cross weight schedule — its
  target-percent sizing matches our D27/D61 convention — and got penny-exact
  agreement across 2,515 bars and 1,370 trades (1.3e-12 max relative divergence,
  empty divergence table). Real finding: vectorbt reserves fees from the purchase at
  ~full investment while we charge cash — documented boundary, comparison runs at
  0.6 weight. 218 tests, all green (13 new).
- **2026-07-14** — **Step 9: analytics honesty.** Greenfield `analytics/` package —
  no analytics existed at all, so the honesty rules are constructed-in, not
  retrofitted: `metrics.py` makes rf_annual and periods_per_year REQUIRED args (a
  default rf=0 is D49's exact target; a default 252 is D17's), adopts quantstats'
  geometric rf and RMS-downside conventions deliberately so the X-gate demands
  EXACT agreement rather than explaining deltas (same argument as D79), and states
  ±inf conventions for zero-variance series; `tail_risk.py` gates VaR/CVaR on ≥30
  tail observations (n≥600 at 95% — stricter than the gate's 100-bar case, and D36's
  own 500-point complaint case fails too, tested); `monte_carlo.py` is a seeded
  block bootstrap (D23's retained tool, Step 12 reuses it), n=10k default, seed
  required positionally; `tearsheet.py` prints the literal insufficient-data string
  with the minimum-n arithmetic. quantstats 0.0.81 works on pandas 3.0.3 (fallback
  unneeded); one quirk documented — its nonzero-rf path needs a DatetimeIndex. D38
  reinterpreted (D82): no sector momentum strategy exists to label; the grep-test
  enforces labels on existing strategies and trips on unregistered new modules.
  max_drawdown relocated engine/sweep → analytics/metrics (pure move, baselines
  re-run). numpy promoted to an explicit production dependency. 248 tests, all
  green (30 new).
- **2026-07-14** — **Step 11: options scoping write-up.** The stub and its U-gate
  have been green since Step 3; the deliverable was `docs/options_extension.md` as a
  real scoping decision (D84) replacing the placeholder: six hard problems (paid
  historical chain data as the blocker; pricing/marking; per-contract cost bricks;
  Reg-T margin; expiry/assignment lifecycle; delta-aware risk), the Lego audit
  separating bolt-on work from engine surgery, framework-style verification gates if
  ever built, and trigger conditions gated on the pairs writeup per R1. Honest
  scoping finding: the expiry-lifecycle problem is bigger than D16's original list
  implied — a time-varying instrument universe breaks D45's inner-join alignment
  assumption (the whole portfolio would silently truncate at the shortest contract's
  expiry), which is exactly the kind of thing only surfaced by scoping properly.
  Doc-rot grep-test added (same discipline as D82's labels). 249 tests green.
- **2026-07-14** — **Step 12: validation science. The framework is complete.**
  DSR X-gate solved a real evidence problem during planning: the paper PDF's
  equation glyphs don't survive text extraction, so the worked example's parameters
  were recovered from its surviving PROSE — two plain-text checkpoints (N=46 →
  0.9505; N=88 under normality → the 95% boundary) overdetermine the one unknown,
  back-solving V[{SRn}]=0.002 exactly and confirming the remembered skew/kurt
  (−3/10) simultaneously; headline N=100 → 0.9004 reproduces. N and V are pulled
  from the TrialRegistry, never typed in — Step 1's registry investment paying off
  as designed. Walk-forward fitting reuses DataView as THE guarded accessor (one
  look-ahead guard in the codebase, not two). Synthetic nulls: random-walk spread,
  NOT OU — an OU spread has real edge and would be the wrong null. One honest test
  recalibration recorded in D87: the multiplicity gate first "failed" with a −4.3%
  mean that was ~1σ of noise at 200% gross — bounds recalibrated at 50% gross where
  ≈0 has teeth (leverage-invariance makes it calibration, not result shopping).
  Shuffle-vs-block quantified: AR(1) ρ=0.6 → shuffled acf₁ < 0.05, block > 0.35.
  260 tests, all green (13 new). No framework steps remain; Phase G begins.
- **2026-07-14** — **Phase G kickoff: universe + study runner + THE FIRST RESEARCH
  RESULT.** Fetched 57 liquid ETFs (2015–2024 raw + events; coverage policy excluded
  nothing; OIH 1-for-20 and USO 1-for-8 reverse splits deliberately in-universe as
  D75 stress tests; XLF's odd 1.231 "split" is the XLRE spin-off encoding — noted).
  gz fixture support added (2.5MB committed vs 17MB raw). `costs/calibration.py`
  automates σ/ADV (D66 caveat carried). `research/pairs_study.py` (new research/
  package = Phase G boundary; framework stays frozen): per window, top-5 of 1,596
  Gatev-scored pairs trade as 5 strategies in ONE portfolio (D27 netting on shared
  legs), warm-up prefix from train tails, NAV-chained windows — the headline test is
  the identity "stitched returns compound starting cash to final NAV exactly."
  Study v1 verdict: the naive Gatev/z-score approach on this universe has ~no gross
  edge (+3.45%/9yr) and is decisively unprofitable at real costs (−13.01%);
  DSR = 0.0000, with D90's multiplicity caveat making the reading conservative in
  the safe direction only. This is a *good* result: it's the honest negative that
  the Phase G writeup builds from, produced by the exact machinery the framework
  spent twelve steps making trustworthy. 273 tests green.
- **2026-07-14** — **Study v2: the selection filter works.** CointegrationSelector
  (Gatev prefilter 50 → EG β coherence window [0.7,1.3] → ADF rank) via the new
  `selector` hook (`None` = v1 byte-identical, D92). Own 40-line ADF statistic tied
  to statsmodels at 1e-9 (D93). Gross +3.45% → +19.03%; profitable at 0.5× costs;
  −6.43% at 1×. The "edge exists but doesn't clear retail frictions" thesis is now
  a measurement. 281 tests green.
- **2026-07-14** — **Study v3: β-hedged trading — the hedge hurt, cleanly measured
  (D94).** `research/beta_zscore.py::BetaHedgedZScoreStrategy` trades the
  train-window β that v2 only logged (spread = ln A − β·ln B), with weights
  normalized to constant gross (w_A = 2w/(1+β), w_B = 2wβ/(1+β)) so gross is 2w for
  every pair — risk comparability with v1/v2 held fixed by construction. New
  `strategy_factory` hook in `run_pairs_study` (per window/multiplier/pair, fresh
  instances per D68, receives the pair's selector-details entry carrying its β;
  `None` = v1/v2 byte-identical). The β=1 equivalence is tested twice: target-level
  identity vs `ZScorePairsStrategy`, and a whole-study equity-curve identity via a
  β=1-forcing factory — the v3 machinery provably contains v2 as a special case.
  First rerun of the script tripped the registry's append-only UNIQUE constraint
  (regenerating the artifact re-adds identical trials) — resolved by deleting the
  local gitignored registry and rerunning, keeping one copy of each trial, which is
  the honest count. Result: gross +6.12% (v2: +19.03%), −16.53% at 1× (v2: −6.43%),
  DSR 0.0000 — estimation noise in a train-window β out-costs its hedge benefit on
  a universe whose selector already demands β ≈ 1. The 1:1 hedge stands. 288 tests
  green (7 new).
- **2026-07-14** — **Capacity analysis: no account size clears real costs (D95).**
  Method: the D8 multiplier sweep can't see account size, but the real bricks can
  (IBKR $1/order minimum binds small, √-impact binds large, spread/borrow/margin
  are scale-invariant rates) — so run the byte-identical v2 study at 9 log-spaced
  `starting_cash` levels with the real UNSCALED stack and let the bricks produce
  the size dependence. Selection depends only on train views → every level trades
  the same pairs; levels differ only through costs (and whole-share rounding).
  Built `research/capacity.py` (recording wrappers → CostLedger attribution;
  transparency = tested identity: recorded run ≡ default run to the penny, unit
  AND whole-study) + `base_stack=None` hook in `run_pairs_study` (third
  None-default hook after D92's selector and D94's factory). Ledger-validity
  rule: capacity runs are 1×-only — a 0× pass through a recorder would record a
  different trade path's costs; the gross reference is a separate plain-stack
  sanity run. Result: hump confirmed ($10k −20.06% → $300k −5.77% → $100M
  −59.05%), all below zero; at the optimum, 2.68%/yr drag vs ≈+2.01%/yr gross
  edge, and even free margin funding lifts it only to ≈+0.19%/yr — the binding
  constraint is the ~200%-gross cost floor, not any size-dependent friction.
  Participation reported per level as the √-law validity boundary ($100M trades
  143% of EWL's ADV — extrapolation, flagged). Cross-checks: $100k row ≡ v2's
  −6.43%; $100M gross +19.04% vs v2's +19.03%. 295 tests green (7 new).
- **2026-07-14** — **Gross exposure study: the margin threshold pays, the rf
  hurdle doesn't (D96).** Thin composition — `research/gross_sweep.py` runs one
  D95 capacity study per leg_weight (`trial_prefix` param added to
  `run_capacity_study`, default preserves D95 ids). Grid lw {0.25,0.5,0.75,1.0}
  × AUM {$100k…$10M} + per-lw 0× gross references at $100M (edge scales ≈∝ lw:
  +0.52/+1.03/+1.53/+2.01%/yr). Margin drag collapsed at the threshold exactly
  as the piecewise arithmetic predicts (0.866→0.220→0.000→0.000%/yr across
  falling lw); five cells turned absolutely net-positive (best lw 0.5 @ $300k,
  +0.12%/yr). Two honesty corrections made during the run: (1) the tests
  discovered that AT the threshold (lw 0.5) rounding/NAV drift produce trace
  margin on scattered bars — "exactly zero" needs gross strictly below NAV;
  test and doc state the collapse (orders of magnitude), not false zero.
  (2) First artifact draft called the best cell's Sharpe −1.61 "statistically
  indistinguishable from zero" — wrong: it is decisively NEGATIVE vs the 4% rf;
  corrected to the two-sided finding (clears implementation costs, not the
  capital hurdle) with the idle-cash-interest caveat cutting the other way.
  Regenerated deterministically (registry deleted + rerun, same as v3/capacity
  precedent). 299 tests green (4 new).
- **2026-07-14** — **Phase G writeup skeleton (D97).** `docs/writeup.md` — the
  document the timetable's kill criterion and reviewer-outreach plan both point
  at, started well inside the week-20 deadline. Methodology-first ordering (for
  this audience the trust story IS the product); skeleton = final numbers +
  draft prose (`[TODO prose]` markers only — a tested rule rejects any
  non-prose TODO); the pre-registered capacity claim and its data-driven
  correction stated in the document; the planned Kalman stage recorded as an
  evidence-based cut (v3: static β estimation error already out-costs its
  benefit; a dynamic hedge re-estimates that same parameter continuously).
  Anti-rot: 24 anchor pairs assert each headline number appears in both the
  writeup and its source artifact (unicode-minus normalized); one anchor
  failure during development was the writeup rounding 143.33% → "143%" —
  exactly the class of drift the test exists to catch. README brought current
  (was still claiming "pre-implementation"); writeup is now its lead link.
  326 tests green (27 new).
