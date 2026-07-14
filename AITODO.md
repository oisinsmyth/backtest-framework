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
- [ ] Commit this chunk's code + D59-D62 decision records

## Next (queued, not started)

- [ ] Phase C kickoff: Step 5 — real equity cost bricks (D3 sqrt impact, D4 IBKR
      commission schedule, D5 margin interest), replacing Step 3's toy bricks
      (`FlatCommission`, `PercentOfNotionalSpread`, `FlatRateCarry`) against the same
      `TradeCostBrick`/`CarryCostBrick` interfaces. `run_backtest` (`engine/backtest.py`)
      is now ready to drive real bricks through a real loop once they exist.
- [ ] Step 6 — cost-multiplier sweep (D8) → run the XLE/XOP walk-forward end-to-end.
      **This is Phase C's milestone and R1's existence-justification gate: the first
      real number.** Target week ~8 per `DEVELOPMENT_TIMETABLE.md`; kill criterion at
      week 10 if not produced by then. Still blocked on: `run_backtest` is
      single-instrument only (D59) — a real pairs walk-forward needs XLE+XOP aligned
      (D45), which this chunk deliberately didn't build.
- [ ] When Step 5 lands: re-run `test_step3_refactor_regression.py` and update its
      golden numbers deliberately (not silently) — D53 designated it the frozen
      baseline, so any change to its expected values needs to be a visible, explained
      diff, not a quiet drift.

## Watch list (not urgent, don't forget)

- R1: no framework scope creep beyond the current build order until the XLE/XOP walk-forward
  produces a first real number (Phase C milestone, week ~8, kill criterion at week 10).
  This is the next real gate — Phase C is where R1 actually bites.
- D62: `RiskMonitor` violations are recorded but not enforced in `run_backtest` — no
  corrective orders, no halt. Revisit once there's a validated strategy to inform what
  "corrective" should actually mean (same reasoning D31 used to defer real allocation).

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
