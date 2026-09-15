# AUDIT_REPORT — Backtest Framework

**Date:** 2026-07-14 · **Auditor:** independent code audit (AI-assisted-code scepticism applied) ·
**Scope:** full repo vs the three ground-truth docs (`DESIGN_DECISIONS.md` D1–D49 + R1–R4,
`VERIFICATION_SCHEME.md` 12 steps, `DEVELOPMENT_TIMETABLE.md`), plus the live doc suite
(`docs/decisions/` D50–D97, `docs/RULES.md`). Audit-only; no code was modified.
**Test suite:** 326 passed, 0 failed, 0 skipped, 2 deselected (`live_fetch` marker), 16.83 s.
**Type check:** mypy (not configured in repo; run ad hoc): 6 errors, all in `research/`.

---

## 1. Executive summary

Overall health is **high** — far above the norm for AI-assisted codebases. The simulator core is anchored to a hand-verified golden master (I independently re-derived its fills and they check out), reconciled penny-exact against vectorbt, and guarded by real property tests; look-ahead prevention (D32/D56) is genuinely structural, not conventional. The three most dangerous findings: **(1)** the study-level DSR is computed with inconsistent units — annualised window Sharpes feed V[{SRn}] while the observed SR is daily, inflating the rejection threshold SR0 by √252 ≈ 15.9×, so the published "DSR = 0.0000" is meaningless as computed (reproduced: a strategy with true DSR 0.9996 would be reported as 0.0000); **(2)** the reproducibility contract (D20/D35) is convention, not structure — config factories exist only for two Step-2 demo models, so the registry's config hash covers a hand-written description dict nothing verifies against the objects actually run; **(3)** the same-bar-close fill convention plus full-sample σ/ADV cost calibration make the low-cost "gross edge" numbers (e.g. v2's +19.03% at 0×) optimistic, with no next-bar-open sensitivity run anywhere. **Can the numbers be trusted?** The accounting arithmetic: yes, to the penny. The published *negative* conclusions ("doesn't clear real costs"): robust — every identified bias points the optimistic way, so reality is the same or worse. The DSR statistic as printed: no. Any future *positive* claim from this framework: not until findings F1–F4 are fixed.

---

## 2. Findings table

Severity: 🔴 corrupts results · 🟠 architectural / reproducibility defect · 🟡 quality or maintainability · 🔵 note.

| # | Sev | Location | Finding | Related | Evidence (observed vs expected) |
|---|-----|----------|---------|---------|--------------------------------|
| F1 | 🔴 | `src/backtest_framework/research/pairs_study.py:255-291` + `validation/dsr.py:63-83` | **DSR unit mismatch.** `run_pairs_study` logs each window's Sharpe via `sharpe(...)`, which is **annualised** (×√252), under the misleading name `window_sharpe_daily`; `deflated_sharpe_from_trials` takes the variance of those annualised values as V[{SRn}], while the observed SR passed in is **daily** (annualised/√252). Bailey–LdP requires SR, SR0, and V in the same per-period units. SR0 is inflated ×15.87. | D21, D86, D90 | Reproduced (scratch script): SR0 shipped = 5.443 vs correct 0.343 (daily units), ratio 15.87 = √252. A genuinely good strategy (ann. SR 2.5, V_ann 0.25, N=175, T=2205): shipped DSR = 0.000000 (REJECT) vs correct 0.9996 (ACCEPT). Published v1/v2 "DSR = 0.0000" is numerically unchanged only because the observed SR was negative — the instrument is broken exactly where it matters (a positive edge). The suite can't see it: `test_pairs_study.py:110` asserts only `0 ≤ dsr ≤ 1`. |
| F2 | 🟠 | `config/sim_config.py:18` (`REQUIRED_KEYS = ("carry_model","fill_model")`), `engine/backtest.py:58-73`, `tests/unit/test_reproducibility_loop.py:24-31` | **D35 declarative config never reached production.** Factories exist for exactly two Step-2 demo models. The engine and all five studies construct cost stacks, strategies, and allocators as live objects; the `config` dict logged to the registry is a hand-written description that nothing checks against the objects run. Two experiments can therefore differ (or collide) while hashing identically — the config hash's fidelity is caller discipline. The Step-2 "full reproducibility loop" gate passes on a self-described "stand-in" (`test_reproducibility_loop.py` docstring), not a real backtest. Acknowledged as open work in `AITODO.md:233`, but the gate is marked passed. | D20, D35, D52 | `grep FactoryRegistry` → only `carry_model.py` / `fill_model.py` register factories; `FillModel` is itself unused by the engine. Re-running a logged study trial requires the script, not the config. |
| F3 | 🟠 | `engine/backtest.py:122-199`, `strategies/zscore_pairs.py:79` | **Same-bar signal→fill at the signal bar's own close.** Strategies see bar *t*'s close (DataView includes it), and orders fill at that identical close. The z-score's mean/std window ends at bar *t−1* (good), but the spread being tested and the fill price are the same number — a mean-reversion entry always catches exactly the close that triggered it. Standard-but-optimistic convention; matched deliberately in the vectorbt reconciliation (D79) so it is *consistent*, but no next-bar-open fill mode or sensitivity study exists anywhere. All five studies inherit it; v2's headline "+19.03% gross edge at 0×" partially rests on it. | D27, D61, D79 (convention); brief §2 "signals computed at bar t executed at bar t's own price" | Engine: `views` built with `build_data_view(..., i)` (includes bar i) at :170, fills at `prices[...] = ab.bars[...].close` at :195-196. No alternative fill timing exists in the codebase. |
| F4 | 🟠 | `costs/calibration.py:25-49`, `strategies/zscore_pairs.py:70`, absence in `engine/backtest.py` | **D44 not implemented at the engine; cost calibration is full-sample.** The engine has no warm-up enforcement — any strategy may trade from bar 1; warm-up is per-strategy self-discipline (D69 admits "engine-level warm-up enforcement is still future work" — yet D44 is a committed ✅ decision). Worse for D44's second clause ("vol estimates use data up to the previous bar only"): SqrtImpact σ/ADV are calibrated on the **full sample including every test window**. Documented as a caveat (D66/D70, restated in study artifacts), but it is a live look-ahead in the cost model of every published number. | D44, D66, D70 | `calibrate_impact_params` consumes the whole fixture; study configs hardcode its output. Direction of bias: unclear per-window, small; but it contradicts a committed decision. |
| F5 | 🟠 | `engine/backtest.py:116,190,212-213` | **D46 attribution half-built: virtual books maintained, then discarded.** `virtual_positions` (per-strategy books) are updated every bar and used for sizing, but `BacktestResult` never exposes them; per-sleeve return streams — D46's entire point ("the future allocator brick is blind without per-sleeve return streams") — exist nowhere. Fills are logged only post-netting with no strategy tag. | D46, D31 | `BacktestResult` fields: equity/cash curves, netted fills, violations, final positions — no per-strategy anything. |
| F6 | 🟠 | `engine/backtest.py:64-68`, `.gitignore` (`*.sqlite`) | **"Every backtest run is logged" is optional, and the evidence is untracked.** `trial_registry=None` is the default; nothing structurally forces a research run to log (studies do so by discipline). Study registries (`data/pairs_study_v1_registry.sqlite` etc.) are gitignored, so the N and V behind published DSRs cannot be audited from the repo without re-running the (deterministic) scripts. | D20 | D20 calls the registry "the one component that can't be retrofitted"; its population is the one thing the framework leaves to convention. |
| F7 | 🟠 | `engine/portfolio.py:23-26`, `instruments/equity.py:22-24` | **D43 half-implemented: NAV formula yes, margin lock no.** NAV = cash + signed position value, defined in one place and golden-tested ✓. But `margin_requirement()` is **never called by any production code** — short proceeds credit cash with no buying-power lock; nothing prevents unbounded gross except the RiskMonitor, which records violations without enforcing (D62). "Cash never negative absent margin" is property-tested only for long-only weights ≤ 0.9. | D43, D62, D40 | `grep margin_requirement` → defined in instruments, called only from `tests/unit/test_instruments.py`. |
| F8 | 🟠 | `research/pairs_study.py:255-259,269` | **DSR trial pool semantics.** (a) N=175 counts (window × multiplier) runs — the same strategy at five cost levels is five "trials", which are near-perfectly correlated, not independent trials in the paper's sense; (b) windows where the strategy never traded, or with zero return variance, log `window_sharpe_daily = 0.0` instead of their true (negative, rf-excess) value or exclusion — silently distorting V and the Sharpe distribution. D90 documents the *selection-breadth* under-count but not these two. | D90, D21 | `window_sharpe = ... if len(set(window_returns)) > 1 else 0.0`; `... if np.isfinite(window_sharpe) else 0.0`. |
| F9 | 🟡 | `research/capacity.py:163-173` | Every capacity/gross-sweep level calls `run_pairs_study`, which **always computes a DSR against the shared cumulative registry** — level *i*'s `StudyResult.dsr` is computed over all trials logged so far across mixed prefixes. The number is meaningless; it is (correctly) unused in the artifacts but sits live on the result objects for anyone to quote. | D95, D96 | `run_pairs_study` unconditionally computes DSR; capacity levels share `registry`. |
| F10 | 🟡 | `data/alignment.py:34-37`, no guard in `cleaner.py`/`validator.py` | **Duplicate timestamps silently collapse, last-wins.** `align_bars` builds `{tb.timestamp: tb.bar}` dicts — a duplicated bar (a real yfinance failure mode after joins/re-fetches) is silently dropped, keeping the *last*. No layer (cleaner, validator, snapshot) checks for duplicate timestamps. | D26, D45 | Reproduced: 2 bars with identical timestamps in → 1 aligned bar out, close = the later one's, no error/warning. |
| F11 | 🟡 | `engine/backtest.py:85,122` | **Zero-overlap alignment → silently empty backtest.** If instruments share no common timestamps, `run_backtest` returns an empty equity curve with `final_nav == starting_cash` — no exception, no warning. The study runner has upstream guards; direct callers don't. This is the brief's "data-layer failure produces a quietly-empty backtest" case. | D45, brief §6 | Reproduced: two instruments with disjoint timestamps → `bars: 0, final_nav: 100000.0`, no exception. |
| F12 | 🟡 | `engine/risk.py:75-94` | `RiskMonitor.pretrade_check` is **never called by the engine** — unit-tested only. The Step-4 gate "pre-trade gate still rejects an order that would breach limits" passes on a function production never invokes. Combined with D62 (violations recorded, not enforced), risk in this framework is entirely observational. | D30, D62 | `grep pretrade_check` → `risk.py` + `tests/unit/test_risk_monitor.py` only. |
| F13 | 🟡 | `simulator/fills.py`, `config/fill_model.py` | **Stop-order machinery is unreachable from production.** `stop_fill_price` (D10) and the D42 adverse-fill convention exist and are golden-tested, but the engine places no stop orders (documented, D77); `FillModel` exists only as the Step-2 config demo. D9 (LIMIT_TRADE_THROUGH) was never built; D11's "VWAP → TYPICAL_PRICE_OPTIMISTIC rename" is moot — **no fill-assumption enum of any kind exists**; the engine fills at close, full stop. Correctly labelled everywhere, but three committed execution decisions (D9, D11, D42's multi-exit case) have no engine surface. | D9, D10, D11, D42, D77 | `grep stop_fill_price` → simulator, config demo, tests. Zero engine references. |
| F14 | 🟡 | `tests/property/test_simulator_invariants.py:32-48,68-72,77-87,136-146` | **Property-test scope gaps.** Scenarios are single-instrument, long-only (weights 0–0.9), flat OHLC bars (`open=high=low=close`) — so "fill within [low, high]" is tautological at engine level; "cash never negative" never sees shorts, margin, carry, or dividends; the flat-commission leak test's assertion is inside an `if` that silently passes when sizing diverges (vacuous for those examples). The invariants D40 promises hold, but over a narrower domain than the gate text implies. | D40, D78 | See cited lines; short/margin paths are covered only by example-based golden tests. |
| F15 | 🟡 | `instruments/equity.py:29-32`, `engine/portfolio.py:24` | **Rounding + no fill-time cash check.** `tradeable_quantity` uses Python `round()` (banker's, round-half-to-*nearest*) — desired quantities round **up** half the time, so a 100%-weight target can buy slightly more notional than capital; `apply_fill` debits cash with no sufficiency check. Residual cash is correctly accounted (absorbed in cash), but negative cash is silently possible at high weights with whole shares. | D40, D43 | `round(1250.5) = 1250` but `round(1251.5) = 1252`; no test pins the rounding convention's direction. |
| F16 | 🟡 | `data/validator.py:9-13` vs `:32-39,141-149` | **Validator docstring contradicts its own code.** Docstring: "an unexplained >25% close-to-close move is a hard violation" and cites the XOP reverse split as "2020-06-22". Code: >25% is a *warning*, hard only >60% (D74); the actual split ex-date is 2020-03-30 (D75 explicitly records that the June date was a false memory). Classic doc-rot describing behaviour the code doesn't have. | D74, D75 | Compare module docstring vs `MOVE_WARNING_THRESHOLD/MOVE_HARD_THRESHOLD` and D75. |
| F17 | 🟡 | `data/cleaner.py:89` vs `data/validator.py:152` | **Inconsistent defensive style on volume indexing.** Validator guards `i < len(volumes)`; cleaner indexes `volumes[i]` unguarded — a shorter volume series raises IndexError mid-clean. Also `_is_bad_print` reads neighbours from the *raw* series, so a spike adjacent to an already-dropped bar is judged against a bar that no longer exists downstream. | D25 | Read both call sites. |
| F18 | 🟡 | `research/pairs_study.py:176-214` | **Study slicing assumes per-symbol index == aligned index.** The warm-up prefix slices `bars_by_symbol[symbol][lo:hi]` using the symbol's *own* series index for an *aligned* window; if any symbol carried extra bars inside a test span, windows would silently shorten (run_backtest re-inner-joins). **Holds today** — verified: all 57 universe symbols and both XLE/XOP fixture symbols have byte-identical timestamp sets — but nothing asserts it, so it's a data-shape landmine for the next universe. | D63, D88 | Scratch check: 57/57 symbols identical timestamps (2,515 bars); assumption currently safe. |
| F19 | 🟡 | `engine/backtest.py:128-157` | **Dividend/split same-gap ordering edge.** Splits scale positions (step 0) before event flows compute (step 1) using post-split quantities and as-declared amounts. If a dividend ex-date *precedes* a split ex-date within the same inter-bar gap (possible only across a dropped/missing bar), the dividend pays on the post-split share count — wrong by the split ratio. Not observed in the committed data; latent. | D75 | Code ordering at cited lines; no test covers both events in one gap. |
| F20 | 🟡 | mypy (ad hoc) | **6 type errors, all in `research/`**: `object`-typed recorder wrappers (`capacity.py:59,73`), `object`-typed matrix lambdas (`gross_sweep.py:87,93,100`), and a `Mapping` variance nit (`pairs_study.py:237`). Framework core is clean (60 files checked). Hints elsewhere are present and honest. | brief §6 | `uvx mypy src --ignore-missing-imports` → 6 errors / 3 files. |
| F21 | 🟡 | `data/csv_fixture.py:58-115` | **Near-duplicate loaders.** `load_fixture_csv` and `load_fixture_csv_with_volumes` duplicate the parse loop wholesale (one could delegate to the other). Similarly `BetaHedgedZScoreStrategy` clones the entire z-score/hysteresis machinery of `ZScorePairsStrategy` rather than sharing it (a deliberate research-copy per D94, but it is the codebase's one real logic duplication). | brief §4 | Diff the two loaders; diff the two strategies. |
| F22 | 🟡 | multiple | **Docstring/comment rot (beyond F16):** `engine/strategy.py:13` still promises "Gatev → cointegration → Kalman is Phase G work" (Kalman was cut, D97); `test_multiplicity_null.py:98` comment says "20 pair-returns", actual 30; `csv_fixture.py:32` says "~4MB gzipped" vs D88's 2.5MB; the `strategies/__init__` D82 auto-trip watches only `strategies/`, while the actually-traded v3 strategy lives in `research/` (labelled voluntarily). | D97, D82 | Cited lines. |
| F23 | 🔵 | `src/backtest_framework/__init__.py:1` | Dead scaffolding: `hello()` — never imported or called. | brief §4 | grep. |
| F24 | 🔵 | `instruments/base.py:28`, `instruments/equity.py:26` | `carry_components()` is a **decorative interface method** — no production code ever consults it. The engine applies every carry brick in the stack to every position regardless of what the instrument declares; an instrument declaring `()` (OptionStub) would still be charged borrow by a BorrowFee stack. Interface drift / mild D48 false affordance; also the shape of D13's non-implementation (one stack per backtest, not per instrument class — moot while only equities trade). | D12, D13, D48 | grep: defined + tested, never called. |
| F25 | 🔵 | `engine/backtest.py:150,160` | **Carry/margin bases are marked at the *current* bar's close** for accrual over (prev, curr] — the position's value at the *end* of the accrual period, a mildly anticipatory convention (real borrow accrues on prior marks). Consistent, hand-verified in the golden master (I re-derived the FRI fill: base 1200×98), but not recorded as an explicit decision. | D33, D67 | Golden master hand.txt uses the same convention. |
| F26 | 🔵 | `engine/backtest.py`, `engine/portfolio.py` | **D12's letter vs spirit:** positions and fills are keyed by ticker *strings* with an `instruments` side-table, not by instrument objects ("positions/fills reference instrument objects, not ticker strings"). The abstraction is real (all math goes through the Instrument protocol) but the letter is violated. | D12 | `positions: dict[str, float]`; fills carry `instrument_id: str`. |
| F27 | 🔵 | absent | **No FXConversionCost brick** (D7's "now" half), `quote_currency` never read, no base-currency NAV (D19), no crypto (D14), no FX instrument (D15), no instrument calendars (D17 — replaced by required `periods_per_year` args per D80), and D21's sibling **IS/OOS overfitting ratio was never built** (`grep -i overfit` → zero hits in src/tests). All are timetable scope cuts or greenfield gaps except D7's committed half and the D21 sibling, which are silent gaps. | D7, D14, D15, D17, D19, D21 | greps cited. |
| F28 | 🔵 | `engine/dataview.py:69-77` | `build_data_view` copies the visible prefix per instrument per bar — O(n²) tuple construction per backtest. Immaterial at current scale (2,515 bars; window studies are 93 bars) and the price of the structural guarantee; flagged only so nobody "optimises" it into a leaky cursor. | D32, D56 | By inspection; runtime fine (full suite 16.8 s). |
| F29 | 🔵 | `analytics/monte_carlo.py:23` | Block-bootstrap block length 20 is a stated default with no recorded justification (D81 names the value, not the reasoning); no block-length sensitivity exists. Standard practice would motivate ~n^(1/3) or an autocorrelation-based choice. | D81 | D81 text. |
| F30 | 🔵 | `research/pairs_study.py:322-323` | `render_study_tearsheet` silently drops return observations whose dates are missing from the benchmark map (fine for the committed SPY-in-universe data where coverage is total; silent subsetting if a sparser benchmark is ever passed). | D37 | By inspection. |
| F31 | 🔵 | dependency hygiene | Prod deps minimal (numpy, pandas, yfinance) and lockfile (`uv.lock`) committed; dev deps (pytest, hypothesis, quantstats, statsmodels, vectorbt) used by gates. No secrets in tracked files or history-visible names (`git grep` for key/token/password: clean; `.env` gitignored; no registries/snapshots tracked). `pandas` is production-listed but used only in `yfinance_source` (fine — yfinance requires it). | brief §6 | greps + `git ls-files`. |

---

## 3. Design-decision conformance (D1–D49)

Statuses: **OK** implemented correctly · **PART** partially implemented · **WRONG** implemented incorrectly · **STUB** stubbed as designed · **NOT** not started · **CONTRA** contradicted by code. Where a D50+ record reinterprets a decision, it's cited.

| D | Decision (short) | Status | Notes |
|---|---|---|---|
| D1 | CostStack of composable bricks | **OK** | Genuinely a stack, not a monolith: 4 slots (trade/carry/portfolio-carry/event-flow), bricks purely additive, order-invariance *tested* not assumed (`test_cost_stack`). Empty stack = zero-cost by construction. |
| D2 | Per-trade vs carry split | **OK** | Two protocols with different hook points (`bricks.py:25-30`); the split is real — engine calls them at different loop stages. Third+fourth slots (D67/D75) extend, not blur, the split. |
| D3 | Sqrt impact brick | **OK** | `equity_bricks.py:60-114`. Mathematically correct: fraction = coeff·σ·√(Q/ADV) (dimensionless ✓), dollars = fraction × notional (∝ Q^1.5). Gate's "√2" clause applied to the fraction, deliberately and documented (D66). Static full-sample σ/ADV is the D66 deferral → F4. |
| D4 | IBKR actual schedule | **PART** | Fixed schedule correct incl. the subtle min/cap ordering (cap overrides min, `equity_bricks.py:46-48`), 13-row X-table. Exchange/regulatory pass-throughs deferred in writing (D65); manual verification vs live page still owed (AITODO). |
| D5 | Margin interest carry brick | **OK** | Accrues as carry (never per-trade) on max(gross − NAV, 0), engine-computed base, portfolio slot (D67), weekend-tested at unit + engine level. |
| D6 | Raw prices + dividend flows | **OK** (post-Step-7) | Two-frame machinery (D75): signals on provider/adjusted frame, execution/costs on reconstructed as-traded, dividends as signed cash flows (longs credited, shorts debited), splits scale positions. No adjusted-price logic hides in any return computation (grep: no shift/ffill/bfill anywhere). v1 artifact predates this and says so. |
| D7 | FX: conversion brick now, accounting later | **NOT** | The committed "now" half (FXConversionCost brick) does not exist; no tearsheet FX line. Single-currency USD throughout. Silent gap vs the decision text (timetable cut covers the *instrument*, not the brick) → F27. |
| D8 | Cost-multiplier sweep | **OK** | Per-brick scaling wrappers, 0× ≡ frictionless-with-flows (refinement documented, D75), monotonicity gate-tested, sweep table in every artifact. |
| D9 | LIMIT_TRADE_THROUGH fill | **NOT** | No limit-order logic anywhere → F13. |
| D10 | Gap-through-stop at open | **OK** (component) | `stop_fill_price` correct both sides, golden-tested incl. boundary. Unreachable from the engine (no stop orders) — documented (D77) → F13. |
| D11 | Rename VWAP → TYPICAL_PRICE_OPTIMISTIC | **NOT** (moot) | No fill-assumption enum exists at all; engine fills at close only. Nothing dishonestly labelled — the decision's target never existed in this greenfield build → F13. |
| D12 | Instrument abstraction | **PART** | Protocol with the exact specified methods; all math flows through it. Letter violated: positions/fills keyed by ticker strings (F26); `carry_components` decorative (F24). |
| D13 | Per-instrument-class cost stacks | **NOT** (moot) | One stack per backtest; no per-class dispatch. Harmless while only equities exist; will bite the day a second class trades (interacts with F24). |
| D14 | Crypto + funding brick | **NOT** | Explicit timetable scope cut (Step 10 deferred past portfolio deadline). Correctly absent, no false affordances. |
| D15 | FX as plumbing | **NOT** | Same scope cut. |
| D16 | Options well-formed stub | **STUB** ✓ | Real dataclass fields, correct ×100 multiplier notional, `margin_requirement` raises NotImplementedError naming `docs/options_extension.md`; scoping doc is real (D84) and rot-tested. Exactly as designed. |
| D17 | Instruments own calendars | **PART** | No `periods_per_year()` on any instrument. Substitute mechanism: `rf_annual`/`periods_per_year` are *required* args on all metrics (D80) and no bare 252/365 constants exist outside `DEFAULT_DAY_COUNT=365` (D51) and study config values. The audit-the-constants half is effectively met; the instrument-owned half is not started. |
| D18 | DataSource interface per asset class | **PART** | Protocol + `EquityDataSource` (honestly labelled unhardened, D59). Only one asset class exists; interface uncontested. |
| D19 | Base-currency NAV | **NOT** | `quote_currency` never read; single-currency NAV only → F27. |
| D20 | TrialRegistry before experimentation | **PART** | Registry itself: correct — SQLite, append-only via PK (structural), survives restart, hash = sha256(canonical config+snapshot+seed), all gate-tested. Gaps: logging optional at engine level; config-hash fidelity is convention (F2); registries gitignored (F6). |
| D21 | DSR sibling to IS/OOS ratio | **PART / WRONG in study wiring** | DSR implementation reproduces the paper to 4 decimals (3 checkpoints, registry-fed N). But the study wiring feeds mixed units → F1 🔴, and the "sibling" IS/OOS overfitting ratio was never built (F27). |
| D22 | Pair selection inside walk-forward | **OK** | Structural: selection sees only train `DataView`s (D85); adversarial I-gate with an OOS-inverting pair passes. |
| D23 | Synthetic-pair null test | **OK** | Random-walk-spread null (correct null — OU would be wrong, documented D87), 40 seeds, non-vacuous, zero-cost. |
| D24 | Immutable snapshots | **OK** | Content-addressed sha256, load() re-hashes and refuses mismatch, every `add_trial` requires a snapshot_id. Meta-not-hashed is a documented, defensible choice (D72). |
| D25 | Cleaner returns change report | **OK** | `clean() -> (data, CleaningReport)`, versioned ruleset, drop-and-report-never-rewrite (D73). Minor: F17. |
| D26 | Sanity gate + quarantine | **OK** | Hard violations quarantine structurally (`QuarantinedSnapshotError`); warnings recorded. Thresholds calibrated and regression-tested both frames (D74). Gaps: no duplicate-timestamp check (F10); docstring rot (F16); second source deferred as written. |
| D27 | signal → weight → orders pipeline | **OK** | Verified: **no strategy touches Order objects or execution APIs** (both strategy classes + both research strategies emit `TargetWeight` only; grep confirms). Central Sizer, cross-strategy netting real and tested (offsetting strategies → zero external orders). |
| D28 | Regime models fit via guarded accessor | **STUB** ✓ | No regime model exists; the guarded `fit(views)` socket is the same one selection uses (D85), so the rule binds automatically when one arrives (D82-style reinterpretation). |
| D29 | Top-N + logged multiplicity | **OK** | Rank-and-take-top-N everywhere (no p-value thresholds; ADF is statistic-only by design, D93); `n_pairs_tested` = full C(n,2) flows to registry; pure-noise P-gate passes. |
| D30 | Per-bar risk checks | **PART** | `evaluate()` runs every bar ✓ (drift I-gate passes). But violations are recorded, never enforced (documented deferral D62), and `pretrade_check` is never wired into the engine (F12). Detection-only. |
| D31 | Allocator stand-in | **OK** | One-method Protocol + `ConstantSplitAllocator`; no accidental complexity (30 lines); wired into Sizer with a loop-closing test (D58). |
| D32 | Structural DataView guard | **OK** | Genuinely structural: the object is *constructed* holding only visible bars (D56) — no reflection path to future data exists, adversarial test tries `.iloc`/parent-refs/`__dict__` walks. I attempted to construct a bypass and found none: the engine passes only per-instrument `DataView`s; `view_bar_series` never leaks. Residual (not a breach): strategies see bar *t*'s close before filling at it → F3. |
| D33 | Calendar-day accrual | **OK** | `(end−start).total_seconds()/86400` — weekends/holidays/dropped bars all accrue via timestamp gaps; Fri→Mon = 3.0 days golden-tested + property-tested (Σ gaps identity). ACT/365 denominator is D51's recorded default. |
| D34 | RNG seed policy | **OK** | MC seed is a *required* arg; same-seed byte-identity tested; seeds logged in trial rows; hypothesis derandomized (D78). Simulator itself is deterministic (hash-tested). |
| D35 | Declarative config | **PART** | Mechanism built and gate-tested — but only for two demo models; production runs are live-object-constructed → F2 🟠. |
| D36 | Tail gating + MC n≥10k | **OK** | ≥30-tail-observations gate (stricter than the spec'd 100-bar case, reasoned in D81); n_sims default 10,000; insufficient-data message printed verbatim in tearsheet. |
| D37 | rf benchmark + realised beta | **OK** | Beta first-class in tearsheet with "≈ 0 expected" note; rf required everywhere; SPY in the universe as benchmark. |
| D38 | Sector momentum labelled | **STUB** ✓ (reinterpreted) | No sector momentum exists (greenfield); label convention enforced by grep-test on existing strategies + auto-trip for unregistered strategy modules (D82). Gap: the trip only watches `strategies/`, not `research/` (F22). |
| D39 | Golden-master tests | **OK** | THE golden master: 5 bars, short side, weekend, dividend debit, drifting margin base, $1-minimum fire, hand file adjacent. **Independently re-verified in this audit** (THU/FRI fills recomputed by hand — match). Deviation: no gap-through-stop in the engine scenario, documented (D77). |
| D40 | Property invariants | **PART** | 8 real invariants incl. the shadow accountant and determinism hash — but the tested domain is narrower than the decision text (long-only, flat bars, no shorts/carry in scenarios) → F14. Cash-negative-absent-margin is *tested where tested*, not enforced (F7/F15). |
| D41 | Cross-engine validation | **OK** | vectorbt 1.1.0, conventions matched then exact agreement demanded: 2,515 bars, 1,370 trades each, max divergence 1.3e-12 rel; documented in `docs/verification/`; test lives in the normal suite so it re-runs automatically. One of the strongest artifacts in the repo. |
| D42 | Intra-bar adverse-first convention | **PART/STUB** | Convention documented in `fills.py` docstring; single-stop case handled; the two-exit case has no engine surface to exercise (no stops/limits in engine) → F13. |
| D43 | Short-sale cash accounting | **PART** | NAV = cash + longs − |shorts| defined once and tested ✓; short proceeds credit cash ✓; margin **lock** absent (F7). |
| D44 | Engine warm-up period | **NOT** (engine) / **PART** (convention) | No engine enforcement; strategy self-guards honour previous-bar estimation; cost-model σ violates the previous-bar rule via full-sample calibration → F4. |
| D45 | Inner-join alignment | **OK** | Exact-timestamp inner join (D63); missing bar → no trading, carry spans gap (tested); fabricated prices impossible (cleaner never rewrites, views error loudly on missing timestamps). Duplicate-timestamp hole → F10. |
| D46 | Per-strategy attribution | **PART** | Virtual books exist and are netting-correct in-loop; sleeve returns never exposed → F5. |
| D47 | Float money + stated tolerance | **OK** | 1e-6 rel tolerance declared in every golden/X test; exact equality reserved for share counts (integers) — correct discipline. |
| D48 | No false affordances | **PART** | No FillStatus.PARTIAL, no dead config knobs, stubs raise loudly — mostly exemplary. Residue: `carry_components()`/`margin_requirement()` decorative on Equity (F24/F7), `hello()` (F23). |
| D49 | Explicit rf for Sharpe/Sortino | **OK** | Required argument, no default; geometric de-annualization matching quantstats; flat-series-at-rf negative gate passes (−inf convention, D80). |

**R1–R4 spirit check:** R1 (first number before new framework code) — honoured; D59's inserted infrastructure was the tightest call and was planned/recorded rather than silent. R2 (timebox) — honoured (D53/D77 chose reinterpretation over scope growth). R3 (deferred list written) — honoured with one silent exception: D7's conversion brick and D21's sibling ratio are gaps with no deferral record (F27). R4 (decisions recorded) — exceptionally honoured; D50–D97 is the best part of this repo. **No speculative-feature sprawl found** — the codebase is if anything under-built relative to the decisions, never over-built.

---

## 4. Verification-gate status (12 steps)

| Step | Gates specified | Present in suite | Passing | Actually tests the claim? |
|---|---|---|---|---|
| 1. TrialRegistry + D10 + D33 | U×4, G×5, P | `test_trial_registry` (roundtrip, append-only via PK, restart, hash semantics), `test_stop_fill_gap_through` (7 cases, both sides), `test_calendar_carry_accrual` (+property: Σ gaps identity) | ✅ | Yes — append-only is structural (PK), not convention. |
| 2. Declarative config | U×4 | `test_sim_config`, `test_reproducibility_loop` | ✅ | **Partially** — the reproducibility loop closes over demo models only; no real backtest is reconstructible from config (F2). |
| 3. CostStack + Instrument + pipeline | U/G ×many + refactor regression | `test_cost_stack`, `test_cost_bricks_golden`, `test_instruments`, `test_pipeline_sizing`, `test_step3_refactor_regression` | ✅ | Yes; regression gate legitimately reinterpreted for greenfield (D53) and recorded. |
| 4. Structural guards | U/I DataView, I risk drift, U allocator | `test_dataview`, `test_dataview_lookahead_guard` (adversarial), `test_risk_monitor`, `test_risk_monitor_drift`, `test_allocator` | ✅ | DataView: yes, genuinely adversarial. Risk: detection only; the tested pre-trade gate is never wired (F12). |
| 5. Equity bricks | X (IBKR ≥10 rows), G margin, U sqrt | `test_ibkr_commission` (13 rows incl. cap-overrides-min + triple boundary), `test_margin_interest`, `test_sqrt_impact` | ✅ | Yes; √2 clause applied to the fraction per D66 (recorded); IBKR manual page check still owed (D65/AITODO). |
| 6. Cost sweep / first result | I monotonic, U 0×, I XLE/XOP e2e | `test_cost_sweep`, `test_first_result_e2e`, `test_first_result_v2_e2e` | ✅ | Yes — offline, on committed fixtures; 0× ≡ frictionless-with-flows refinement documented. |
| 7. Data layer | U snapshot/cleaner/gate, G dividend/split-commission, U missing-bar | `test_snapshot_store`, `test_cleaner`, `test_validator`, `test_dividend_flow` (both signs + engine level), `test_split_commission`, `test_pairs_backtest` | ✅ | Yes. Gap: no duplicate-timestamp defence anywhere (F10). |
| 8. Testing hardening | G golden master, P invariants ×6, X cross-engine | `test_the_golden_master` (+hand.txt — independently re-verified in this audit), `test_simulator_invariants`, `test_cross_engine` + committed reconciliation doc | ✅ | Golden master: yes. Properties: yes but narrow domain (F14). Cross-engine: penny-exact, auto-re-run, documented — exemplary. Reset gate reinterpreted (D78, recorded). |
| 9. Analytics honesty | U tail gate, U MC seed/n, U beta, U rf, X quantstats, U label grep | `test_tail_risk`, `test_monte_carlo`, `test_metrics`, `test_quantstats_xgate` (exact ties), `test_strategy_labels` | ✅ | Yes; D38 gate reinterpreted for a strategy that doesn't exist (D82, recorded, with auto-trip). |
| 10. Crypto + FX | G funding, U calendars, U lint, G 2-currency NAV | — | **N/A — deferred** | Explicit timetable scope cut; correctly absent rather than half-built. The 252/365 lint test rode along into deferral; current code is clean by inspection. |
| 11. Options stub | U fields/multiplier/NIE | `test_instruments` (+D84 doc-rot test) | ✅ | Yes. |
| 12. Validation science | I guarded selection, P multiplicity, X DSR paper, P nulls, U shuffle-vs-block | `test_walk_forward_selection`, `test_multiplicity_null` (19,900 logged; OOS ≈ 0), `test_dsr` (3 paper checkpoints, registry-fed), `test_shuffle_vs_block` | ✅ | **At unit level, yes. At study level, no** — the gates validate `dsr.py` in isolation; the unit mismatch sits in `pairs_study.py`'s wiring, exactly one layer above the highest gate (F1). The suite asserts the study DSR is merely finite. |

**Test-quality audit:** 287 test functions (326 with parametrization), zero without assertions (verified by AST scan); no mocked-away subjects; golden masters all have adjacent `.hand.txt` arithmetic; hypothesis derandomized. Weakest coverage of critical paths: short/margin accounting under randomized inputs (example-based only), the study runner's DSR wiring (finiteness only), duplicate-bar handling (none).

---

## 5. Understanding checklist (interview-readiness)

One line each — be ready to explain unaided:

1. `costs/equity_bricks.py:105-114` — why the square-root law makes the impact *fraction* ∝ σ√(Q/ADV) and total dollars ∝ Q^1.5; units check; the Y≈1 coefficient convention.
2. `costs/equity_bricks.py:42-48` — the IBKR min/cap ordering (`min(max(per_share·q, min), cap)`) and the penny-stock case where cap overrides minimum.
3. `simulator/carry.py:14-36` — ACT/365 vs ACT/360; why the *numerator* is calendar-day gaps (Fri→Mon = 3 days) and what per-bar accrual undercharges (~40% of calendar time).
4. `engine/backtest.py:145-164` — D67 start-of-bar snapshot: why carry bases freeze before deductions (order-independence), and margin base = max(gross − NAV, 0).
5. `engine/backtest.py:122-199` — the same-bar-close fill convention and NAV-driven per-bar re-sizing (D61); be ready to defend it vs next-bar-open fills and to say which way it biases a mean-reversion strategy.
6. `engine/dataview.py:69-77` + `docs/decisions/D56` — why construction-time truncation is structurally stronger than access control (Python has no private attributes).
7. `strategies/zscore_pairs.py:69-89` — z window ending at the previous bar (D44), the hysteresis band and why `_side` state exists (and why sweeps take strategy *factories*, D68).
8. `research/beta_zscore.py:60-66` — derive w_A = 2w/(1+β), w_B = 2wβ/(1+β) from "gross constant = 2w" + "notional ratio N_B = β·N_A".
9. `research/cointegration.py:34-71` — Engle-Granger step 1 OLS, why the residual ADF has no constant, and how the t-statistic falls out of `lstsq` (σ²(XᵀX)⁻¹).
10. `validation/pair_selection.py:42-52` — Gatev SSD on *rebased* log prices, and the gram-matrix identity ‖xᵢ−xⱼ‖² = ‖xᵢ‖²+‖xⱼ‖²−2xᵢ·xⱼ.
11. `validation/dsr.py:33-60` — PSR's skew/kurtosis denominator, SR0's Euler–Mascheroni expected-maximum formula, why every quantity must be per-period (non-annualised) — and F1 as the cautionary tale.
12. `analytics/monte_carlo.py:36-57` — block bootstrap mechanics; why blocks preserve the autocorrelation a shuffle destroys (D23); block-length trade-off (and that 20 is currently unjustified).
13. `validation/synthetic.py:30-53` — why the zero-edge null must be a random-walk spread and an OU spread would be the *wrong* null.
14. `validation/walk_forward.py:50-65` — window arithmetic: `start + train + test ≤ n`, step = test ⇒ contiguous non-overlapping OOS; train views end at `train_size − 1`.
15. `data/corporate_actions.py:75-118` — the two-frame finding (yfinance auto_adjust=False is *already split-adjusted*), as_traded = adjusted × Π(future ratios), and dividend cash-flow invariance.
16. `analytics/metrics.py:32-57` — geometric rf de-annualization ((1+rf)^(1/p)−1), ddof=1, the ±inf zero-variance conventions, Sortino's full-length RMS downside.
17. `analytics/tail_risk.py:40-47` — min-observations arithmetic: n ≥ 30/(1−confidence); why 95% VaR from 500 points is "the 25th-worst day".
18. `pipeline/sizing.py:44-98` — weight→quantity conversion, netting (A buys what B sells → zero external orders), and why virtual books update by their own orders regardless of netting.
19. `docs/verification/cross_engine_reconciliation.md` — the vectorbt fee-reserving boundary at ~full investment, and why conventions were matched *before* demanding exact agreement.
20. `research/pairs_study.py:206-253` — warm-up prefix arithmetic (lookback train bars ⇒ first trade = first test bar) and NAV chaining across windows.
21. `data/validator.py:127-150` — frame-robust split awareness: why a move must be small in *either* frame, and how the one-frame version quarantined clean data (D74).
22. `tests/golden/test_the_golden_master.hand.txt` — be able to reproduce the FRI re-size by hand: post-carry NAV → −1253 target → −53 delta → $1 IBKR minimum fires.
23. `validation/dsr.py` + `docs/decisions/D86` — how the paper's V = 0.002 was back-solved from two prose checkpoints (overdetermination as verification).
24. `docs/decisions/D95/D96` — why capacity is a direct AUM sweep (multiplier sweep can't see size), the margin threshold max(2·lw−1, 0), and the "pays for implementation, not capital" two-sided headline.

---

## 6. Recommended fix order

Sequenced per the build order and R2's timeboxing (registry/reproducibility first, result-corrupting next, everything else queued). Sizes: **S** ≤ 2 h, **M** ≈ one week's budget (~7 h), **L** multi-week.

**Phase 1 — reproducibility & the validation instrument (do before quoting any more numbers):**
1. **F1 (S)** — Fix DSR units in `pairs_study.py`: log window Sharpes per-period (divide by √252) or convert before `variance()`; rename the metric; add a unit-consistency test (e.g. assert SR0 < 1 in daily units for realistic V). Re-run studies v1–v3 + capacity + gross sweep (deterministic scripts) and re-anchor `test_writeup.py` if any headline moves (DSR lines will).
2. **F8 (S)** — Decide and record (decision record) what a "trial" is for N: exclude non-1× multiplier runs or justify inclusion; stop mapping non-traded windows to Sharpe 0.0 (exclude and log the exclusion, or use the true rf-excess value).
3. **F2 (M)** — Config factories for the real bricks/strategies/allocator (already `AITODO.md:233`); make `run_backtest` accept config-built stacks so the registry hash describes what actually ran. Close the *real* reproducibility loop with a test that rebuilds a study window from a logged config.
4. **F6 (S)** — Either commit study registries (small SQLite files) or record the decision that scripts-as-reproduction suffices; add a one-line note to each results doc.
5. **F9 (S)** — Suppress/omit `StudyResult.dsr` for capacity/gross runs (dedicated flag), or compute per-level with a scoped registry view.

**Phase 2 — result-corrupting risks in the simulator's blind spots:**
6. **F10 (S)** — Duplicate-timestamp check in cleaner or validator (hard violation); one test.
7. **F11 (S)** — `run_backtest` raises on zero aligned bars.
8. **F19 (S)** — Order event flows before split scaling within a gap, or assert the events aren't co-gapped; one test.
9. **F3 (M)** — Add a next-bar-open (or next-bar-close) fill mode and re-run study v2 as a sensitivity line in the writeup. This is the single highest-value honesty upgrade for the portfolio narrative.
10. **F4 (M)** — Per-train-window σ/ADV calibration (already an AITODO candidate); removes the last documented look-ahead. Warm-up enforcement in the engine can ride along or be formally re-deferred with a decision record.
11. **F15 (S)** — Pin the rounding convention (floor-toward-zero is the conservative choice) and add a fill-time cash check or an explicit margin-allowed flag (partially discharges F7/D43).

**Phase 3 — architectural debt, queued:**
12. **F5 (M)** — Expose per-strategy virtual books + sleeve equity curves on `BacktestResult` (D46's payoff; needed before any real Allocator work).
13. **F7 (M)** — Buying-power lock via `margin_requirement`, or a decision record formally deferring it (the honest minimum given D43 is marked committed).
14. **F12 (S)** — Wire `pretrade_check` into the engine behind a flag, or record its deferral alongside D62.
15. **F14 (M)** — Extend property scenarios: shorts, mixed-sign weights, non-flat OHLC bars, a carry brick in the stack; remove the conditional assert in the flat-commission test (force same-trade-sequence by construction).
16. **F13 (S)** — Decision record resolving D9/D11/D42's status for a close-fill-only engine (implemented-as-components vs formally deferred); kills the ambiguity cheaply.
17. **F27 (S)** — Deferral records for D7's conversion brick and D21's IS/OOS ratio (R3 compliance), or build the ratio (S — the walk-forward machinery makes it ~20 lines).

**Phase 4 — hygiene sweep (batchable into one short session):**
18. **F16/F22 (S)** — Fix validator docstring (threshold + split date), strategy.py Kalman line, test comment counts, gzip size note.
19. **F17 (S)** — Bounds-guard cleaner volume indexing.
20. **F20 (S)** — Type the recorder wrappers/lambdas properly; add mypy to CI (it's 6 errors from clean).
21. **F21 (S)** — Collapse the duplicate CSV loaders.
22. **F23/F24 (S)** — Delete `hello()`; either consult `carry_components()` in the engine or remove it from the protocol with a decision note (D48 discipline applied to your own interface).
23. **F18 (S)** — Assert per-symbol/aligned index equality at study start (one `if`, converts a landmine into a loud error).
24. **F29/F30 (S)** — Record a block-length rationale; make the tearsheet benchmark filter loud on dropped observations.

---

*Method note: layers read in data → instruments/costs → simulator/engine → config/registry/pipeline → analytics/validation/research order; all 97 decision records read; suspected bugs reproduced with throwaway scripts in the session scratchpad (not added to the repo): DSR unit mismatch (observed SR0 inflation exactly √252; verdict flip 0.000→0.9996), fixture timestamp-set identity (57/57 identical), duplicate-timestamp silent dedup, zero-overlap silent-empty backtest, and a by-hand re-derivation of the golden master's THU/FRI fills (match). No code, test, or doc in the repo was modified.*


---

## 7. Remediation status (appended post-audit, 2026-07-14)

All 31 findings were dispositioned in the same session, in the fix order above
(commits `4fdc818`..`cf3f283`; decision records D98–D107). Suite after
remediation: **360 passed** (was 326), mypy **0 errors** (was 6). All five study
artifacts regenerated with **byte-identical headline numbers**; only DSR-section
descriptions changed.

| Finding | Disposition |
|---|---|
| F1 🔴 DSR units | **Fixed** (D98): daily-unit logging, units contract + regression test pinning the metric to the observed-SR units at 1e-12. Published DSRs re-confirmed 0.0000 under correct units. |
| F2 🟠 config-hash fidelity | **Fixed** (D102): real stack config-built from the logged dict; `to_dict` covers every determining field (starting_cash/multipliers were missing); `from_dict` closes the study-level reproducibility loop, tested. |
| F3 🟠 same-bar-close fills | **Fixed + measured** (D103/D105): `fill_timing="next_open"` mode, golden + property tested; sensitivity artifact — gross edge survives (+16.79% vs +19.03% at 0×), conclusion not a fill-timing artifact. |
| F4 🟠 full-sample calibration / D44 | **Fixed + measured** (D102/D105): `impact_calibration="train_window"` (leak-free, tested); worth ~0.15pp at 1× — immaterial. Engine-level warm-up remains strategy-side (unchanged; D44 gap now measured and bounded). |
| F5 🟠 sleeve attribution | **Fixed** (D101): `virtual_fills` + `final_virtual_positions` on BacktestResult; cost attribution to sleeves deferred with rationale. |
| F6 🟠 optional logging / untracked registries | **Recorded** (D107.5): binds structurally at the study runner; registries stay regenerable local artifacts, reproduction commands in every artifact. |
| F7 🟠 margin lock absent | **Deferred with record** (D107.1): observable (D30) + rejectable (D101) + priced (D5); lock awaits a policy a validated strategy motivates. |
| F8 🟠 trial-pool semantics | **Fixed** (D98): 1×-only pool via include-predicate; undefined Sharpes omitted, loud at 1×. |
| F9 🟡 per-level capacity DSR | **Fixed** (D98): `compute_dsr=False` for capacity/gross; `StudyResult.dsr` honestly None. |
| F10 🟡 duplicate timestamps | **Fixed** (D99): align_bars raises; validator hard-quarantines. |
| F11 🟡 silently-empty backtest | **Fixed** (D99): run_backtest raises on zero aligned bars. |
| F12 🟡 pretrade never wired | **Fixed** (D101): opt-in enforcement with virtual-order rollback. |
| F13 🟡 unreachable stop machinery / D9/D11/D42 | **Recorded** (D107.2): D11 moot; D9/D42-multi-exit deferred until stops become an engine feature. |
| F14 🟡 property-test scope | **Fixed** (D104): signed weights, real OHLC bars, unconditional commission/carry accountants, next-open invariants. |
| F15 🟡 rounding + no cash check | **Pinned** (D106.1): round-half-even tested; negative cash = implicit margin posture recorded; changing it is a study-version bump. |
| F16 🟡 validator docstring rot | **Fixed**: thresholds and split date match code/D74/D75. |
| F17 🟡 cleaner volume indexing | **Fixed** (D99): bounds-guarded. |
| F18 🟡 study grid assumption | **Fixed** (D99): per-window loud assertion (grids verified identical on committed fixtures). |
| F19 🟡 dividend/split gap ordering | **Fixed** (D99): gap segmented at split ex-dates; three-case test incl. same-date convention. |
| F20 🟡 mypy errors | **Fixed**: 0 errors across src (typed recorders, protocol property, annotations). |
| F21 🟡 duplicate CSV loaders | **Fixed**: bare loader delegates. |
| F22 🟡 comment rot | **Fixed**: Kalman line, test counts, gzip size. |
| F23 🔵 `hello()` | **Fixed**: removed. |
| F24 🔵 decorative `carry_components` | **Fixed** (D100): engine consults it; bricks declare components; wrappers forward. |
| F25 🔵 carry mark timing | **Pinned** (D106.2 + D104 property test). |
| F26 🔵 D12 letter (string ids) | **Accepted**: the abstraction is real (all math through the Instrument protocol, now enforced further by D100); re-keying positions by object identity would be churn without behavioural gain. |
| F27 🔵 D7 brick / D21 ratio absent | **Deferred with records** (D107.3/D107.4). |
| F28 🔵 registries gitignored | **Recorded** (D107.5). |
| F29 🔵 block length unjustified | **Recorded** (D106.3). |
| F30 🔵 tearsheet silent subsetting | **Fixed**: refuses incomplete benchmark coverage. |
| F31 🔵 dependency hygiene | **No action needed** (already clean; noted for the record). |
