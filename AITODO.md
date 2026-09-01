# AI TODO

Claude's current working task list for this project — not a roadmap (that's
[`DEVELOPMENT_TIMETABLE.md`](DEVELOPMENT_TIMETABLE.md)) and not a decision log (that's
[`docs/decisions/`](docs/decisions/README.md)). Kept short: only what's immediately in front of
us. Update this at the start/end of each working session — stale entries here are worse than
none.

## Now

> **SESSION HANDOFF 2026-09-01 — read [`PICKUP.md`](PICKUP.md) first.** The free half of the
> futures data layer is built and committed (D262). The one blocker is a Databento API key,
> which is the principal's to create; the next actionable step needs no key and no purchase.

- [x] **D262 — the futures data layer, and the free rung of the ladder.** CFTC Commitments of
      Traders built and committed (210,717 rows, 28 symbols, 1986-2026, public domain so it MAY
      be committed); the continuous-contract stitcher and its acceptance gates, built and tested
      against no vendor data; a Databento client that cannot spend by accident; provider
      references for both new sources.
- [x] Alpha Vantage 15-minute cache completed to 11,400 slices including the 2010-2017 backfill.
      **The 57-ETF extended-hours FIXTURE is refused on measurement** — only 2 of 57 symbols
      reach a median 58 of 64 slots, the raggedness is liquidity-correlated, and an unfiltered
      +428.52% bad print survives. The cache is still the durable win.
- [ ] **NEXT: pre-register and run the COT screen (rung 1).** Needs no key, no purchase, no new
      data. It is a STUDY, so it needs its own registration under R8 — D262 deliberately scored
      nothing. Scope the micro/mini form to ES/MES and NQ/MNQ (~6 years); MYM has ~4 and the
      metal micros under one. A negative result is worth as much as a positive one: it would say
      not to spend the ~$205 at all.
- [ ] **BLOCKED ON THE PRINCIPAL: `fetch_databento.py --verify`.** Free, ~7 calls. Needs a key at
      `~/.config/databento/key` (usage-based $0/mo, NOT Standard). Settles the one inferred
      number the whole costing rests on -- $28.00/GiB derived versus the 280.0 their docs show --
      and whether the roll-rule letters mean what the client source implies.
- [ ] Do NOT wire up `--submit` until the purchase is actually decided.


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
- [x] **Long-flat breakout study on BTC/ETH — the second research strategy, and the
      first directional one (D108–D117).** `strategies/breakout.py` (Donchian
      long-flat with toggleable filter and sizing bricks), `research/breakout_study.py`
      (walk-forward 252/63, four fee tiers, plateau surface, in-train grid selection,
      configuration-pool DSR), `research/trade_diagnostics.py` (position episodes:
      MFE/MAE, time-in-trade, whipsaw, capture, cost share).
      `BREAKOUT_RESULTS.md` + `data/breakout_study_summary.json`; 152 OOS trials,
      7,904 registry rows, offline and deterministic. Three things worth remembering:
      (1) the volume-confirmation filter is BLOCKED — `Bar` carries no volume and both
      workarounds are worse than the gap (D111); (2) the pairs study's chained-window
      pattern would have distorted a trend follower, so this study runs one continuous
      OOS backtest with a per-window parameter schedule (D113); (3) D38's label gate
      fired the moment `breakout.py` landed, exactly as D82 designed it to (D117).
      Headline: survives fees easily (10–11% of gross P&L at 0.40% taker, 0% whipsaw,
      ~26–29 day median hold) but loses badly to buy-and-hold on BTC and beats it
      modestly on ETH — the case is risk-adjusted only. 438 tests (77 new).
- [ ] Commit breakout study + D108–D117
- [x] **Breakout study review — three claims corrected, one question answered
      (D118–D121).** Prompted by "these results seem crazy — is that just the crypto
      hype?", which was the right question. (1) **Era decomposition** (D121): BTC rose
      426× over the OOS span, so the absolute returns are the instrument's; year by year
      the strategy lost to buy-and-hold in every up year and beat it in 5 of 6 down years,
      and its CAGR swings +11% to +49% on start date alone. It is insurance bought with
      bull-market underperformance, and the case rests on five observations. (2) **The
      Sharpe claim was retracted** (D120): +0.04/+0.11 gaps are a fraction of a standard
      error, P(>0) = 55%/59% under a paired block bootstrap. (3) **The benchmark was
      unfair in the other direction** (D119): at matched average exposure the strategy
      earns ~4× the terminal wealth of constant exposure at similar drawdown. (4) **The
      vol target was swept** (D118) and turns out to be a risk dial, not a Sharpe
      improvement. 453 tests (15 new).
- [ ] Commit breakout review + D118–D121
- [x] **BTC/ETH z-score pairs study — an honest negative, and the premise is what
      failed (D122–D127).** `research/crypto_pairs_study.py` +
      `scripts/run_crypto_pairs_study.py` → `docs/results/crypto_pairs_btc_eth.md` +
      `data/crypto_pairs_registry.sqlite`; 76 OOS trials, 3,344 registry rows, offline
      and deterministic on the same frozen snapshot as the breakout study.
      `ZScorePairsStrategy` reused UNMODIFIED (D69) — no new strategy was needed or
      written. Five things worth remembering:
      (1) **there is no edge to cost.** Zero fees AND zero carry still returns −88.7%
      over 2,709 OOS bars (Sharpe −0.67). Every cost number in the artifact describes
      how much faster a losing strategy loses, so the report leads with that rather
      than burying it under a cost table.
      (2) **the pair is not cointegrated** (D125): the traded 1:1 log spread is
      stationary in 6 of 43 *training* windows (14% — roughly what a 5% test fires at on
      noise), and the Engle–Granger β has median 0.74, so even the relationship the data
      supports is not the one being traded. Critical values are anchored against
      statsmodels rather than typed in.
      (3) **market neutrality is the one claim that survives**: realised β −0.011 /
      +0.022 / −0.006 against BTC / ETH / a 50/50 basket, against D37's ≈0 expectation.
      The engineering works; the thesis does not.
      (4) **borrow was not assumed to be zero** (D124): 10%/yr on the short leg, swept
      0–25%. A silent zero would have shown 1.47× the terminal wealth. The verdict does
      not move at 0%/yr either, which is what makes it robust.
      (5) **the D45 inner join truncates the study to ETH's inception** (2017-11-09,
      1,043 BTC bars discarded) — correct for a pairs trade, and it means no number here
      shares a span with `BREAKOUT_RESULTS.md`'s BTC rows (D127). 516 tests (63 new),
      mypy clean.
- [ ] Commit crypto pairs study + D122–D127

- [x] **Crypto breakout universe cross-section (D140–D144)** — `docs/results/breakout_universe.md`.
      Answers `BREAKOUT_RESULTS.md`'s own caveat 3 ("BTC and ETH are the two crypto assets
      that survived… the single largest un-deflatable bias in this document") by running the
      *identical, unmodified* machinery over 63 coins deliberately including ones that died.
      **Result: the timing claim generalises only to the assets that fell apart.** At
      `taker_40bp` the fixed baseline beats matched-exposure (D119) in 45% of survivors and
      67% of collapsed/delisted names; against 100% buy-and-hold, 45% vs 98%. Max drawdown
      is reduced in 63/63. BTC and ETH rank 1st/8th of 63 on return and 2nd/13th on Sharpe —
      the original study *was* substantially measuring its instrument choice, and now there
      is a number for it. Five things worth remembering:
      (1) **the universe policy is the deliverable as much as the numbers are** — pre-stated,
      mechanical, screening cleaned bars, applied once at fetch and again at study time so a
      rejected symbol cannot reach the engine, with every exclusion named (D140);
      (2) **the sanity gate had to be overridden** — D74's >60% move threshold is an *ETF*
      calibration and fires 143 times here, concentrated in the collapsed cohort, so obeying
      it would have restored the exact bias being measured (D143). Recalibration deferred;
      (3) **the policy was amended once, post-hoc, for a stablecoin** whose Sharpe was −∞,
      and D144 records the amendment rather than hiding it;
      (4) **no Sharpe difference is measurable** — a per-coin paired bootstrap clears zero in
      3/63 and 4/63, against ~6 expected by chance;
      (5) **the roster is still hindsight-assembled** and provider survivorship is unfixed
      (`MIOTA-USD` is missing, not omitted). Less biased than BTC/ETH; not unbiased.
      644 tests (44 new), mypy clean.
- [ ] Commit breakout universe study + D140–D144

## Now — the STRUCTURE programme (opened 2026-08-24, D204)

Mechanising a discretionary retail price-action strategy so its five components can be
measured separately and together. Spec `New Docs/STRUCTURE_MODEL.md`, ledger
`STRUCTURE_RESULTS.md`. Prior stated as bad up front: three of the five are pullback-fade
entries and fading lost in every form terrain measured.

- [x] **WP0 — pre-registration.** Spec + ledger + D204 committed before any code. Fixes the
      five definitions, the confirmation-lag requirement, the parameter sets and the named
      primary cell, three hurdles with the percentile beside every delta, a stop condition
      per WP, and seven predictions (four at high confidence that the component FAILS).
      Looks: 0.
- [x] **WP1 — the five detectors + their tests (D205).** `research/structure.py`, 55 new
      tests, 1098 green, mypy --strict clean. The suite passed first time, so the module
      was mutated six ways: **two mutations survived 43 green tests**, one of them the
      higher-low requirement that IS the pre-registered CHoCH definition. Both tests
      strengthened; the second finding generalises and is written up in D205.
- [x] **WP2 — the census (D206).** Stop condition CLEARS (120 and 106 stacked entries
      against a floor of 30) so H5 is falsified and the programme continues. The
      decisive number needed no backtest: **40 bps is 0.40% of price and the median
      C1-only stop is 0.41%**, so the cost of trading is roughly the entire distance to
      the stop and a 20% hit rate at 5R loses money in every cell. C5 dropped as a
      stacked filter on counts alone (RSI 30/70 leaves 2 entries), kept as a feature.
      Two guard-shaped defects flushed out by tests written before the run. 0 looks.
- [x] **WP3 — components against their placebos (D208).** **One variable — retracement
      depth — explains every apparent effect.** The ratio ladder is a monotone
      staircase: 0.618 ranks 4 of 8 and loses to 0.691/0.724 in 97%+ of draws. The
      depth-matched null then takes back the only clean pass: the fair value gap falls
      from +0.082 at the 100th percentile to +0.006/-0.006. Flipped level negative
      either way; CHoCH fails the both-symbols rule; **RSI, the control, is the only
      survivor**. Depth-matched null disclosed as post-hoc, 30 looks.
- [x] **D207 amendments**, written before the runs they govern: market entry at the
      close (so D196's adverse selection is NOT paid here — stated, not buried), 5R
      primary target, and an 8-arm ablation rather than 16.
- [x] **WP4 — marginal contribution (D210).** **Nothing survives holding leg size
      constant.** Three features clear the promotion criteria and turn out to be ONE
      quantity under three names (pairwise rho +0.79 to +0.88); MFE is in R, so
      MFE_R = excursion/risk tracks leg size arithmetically. Inside stop-width
      quintiles the largest correlation any feature reaches is 0.13 against a bar of
      0.2, depth included. Stacking all four filters is WORSE before costs. 48 looks.
- [x] **D209 defect**: the stop was on the wrong side of the trade. A guard rejected
      93% of setups and kept an adversely selected sliver — found by a count that did
      not match another count, not by a test. WP2's friction table corrected and one
      finding reversed.
- [~] **WP5 — costed verdict: DOES NOT RUN.** D210 triggered the pre-registered stop.
- [x] **WP6 — the discretion audit and the close (D211).** The verdict is not a
      property of one cell: across all 8 grid cells the largest rank correlation any
      feature reaches inside any stop-width quintile is 0.10-0.15 against a bar of 0.2,
      and stacking the filters helps at zero cost in **0 of 8**. **Programme CLOSED at
      86 looks.** Final report is the last section of `STRUCTURE_RESULTS.md`.
- [x] **D212**: a cost-convention defect (the census and the lattice priced the same
      tier a factor of two apart; a test named for their agreement compared one to
      itself), plus a post-close addendum restating every arm in **Sharpe and PnL**
      against buy-and-hold and cash. **0 of 16 arms make money at 40 bps/side and 0
      of 16 at 10 bps/side.** Ledger 86 -> 102 looks.

## Now — D217, the MACD crossover ladder (opened and closed 2026-08-24)

Not a continuation of STRUCTURE. A fresh ledger on a different fixture (57-ETF daily, not
crypto 15m), a different claim family, and a sensor that did not exist in this repo. Record
`docs/decisions/D217-the-macd-crossover-ladder.md`, ledger `MACD_RESULTS.md`.

The claim under test was never "does MACD make money" — it was whether the signal line adds
anything over the zero-line cross (which is identically a 12/26 EMA crossover) and whether
that adds anything over flat momentum at the same centre of mass.

- [x] **WP0** pre-registration, committed BEFORE the runner existed. Seven predictions with
      confidences, hurdles A–G, the programme stop, and the ledger arithmetic.
- [x] **WP1** `research/macd.py` — the first EMA here, seed convention and 393-bar burn-in
      derived and stated. 57 tests: unit, property (analytics has no D32 guard, so this file
      is the guard), and a golden at MACD(3,7,3) where every value is a dyadic rational.
- [x] **WP2** census + break-even. Zero looks. No arm underpowered; friction is 0.015 Sharpe
      institutional, and the IBKR $1.00 minimum binds on all 57 ETFs at a $100k book.
- [x] **WP3** the ladder, 12 looks. **H1 falsified**: R1−R2 = +0.285, and the algebra I was
      most confident about was right and read the wrong way round.
- [x] **WP4** the declared sweep, 30 looks. 12/26/9 ranks 10 of 32; all eight zero-line cells
      sit between −0.166 and +0.080.
- [x] **The verdict**: 0 of 12 cells clear all seven hurdles. The best clears six and fails
      only the DSR floor — +0.334 at the fresh count of 42, +0.638 at the verdict count of
      45,783. **Stage 2 does not run**; the pre-registered stop fired.

Open, and deliberately not pursued inside this study (D215's rule): the R1-vs-R2 separation
is the one transferable claim — *trend acceleration predicts where trend level does not* —
and it needs its own pre-registration and its own holdout on a fixture this project has not
already mined. The crypto daily universe is the obvious candidate.

> **Housekeeping debt, noticed while writing the D217 section:** the STRUCTURE checklist
> above stops at D212, while D213, D214, D215 and D216 all shipped and are in the CHANGELOG.
> That is drift against R5 and against this file's own instruction that stale entries are
> worse than none. Not fixed here because backfilling four studies from memory is exactly
> the kind of reconstruction this project does not trust; it needs a session with the
> records open.

## Now — D229, the jerk rung (opened and closed 2026-08-27)

Record `docs/decisions/D229-one-more-rung-up-the-derivative-ladder.md`, page
`JERK_RUNG_RESULTS.md`.

- [x] **Jerk does not beat acceleration.** `I0 - I1 = -0.218`, hurdle A fails in all four
      cells. P1-P5 all confirmed.
- [x] I0 **beats the level rung** (+0.310) while losing to acceleration — the ladder is not
      monotone, and both derivative rungs beat level.
- [x] Built the **paired block bootstrap** the repo lacked.

**THE DERIVATIVE LADDER CLOSES AT I1.**

## Now — D230, the bootstrap sweep (opened and closed 2026-08-27)

Record `docs/decisions/D230-the-bootstrap-sweep.md`, page `BOOTSTRAP_SWEEP_RESULTS.md`.

- [x] Swept all **24** reported deltas through the test the records said had been run.
- [x] **8 cleared as scored. 0 clear as claimed. All 24 intervals contain zero.**
- [x] Reproduction gate clean to 1e-9 — this audits the published numbers.
- [x] Found the error running the **other** way: near-zero deltas reported as evidence of
      absence on intervals 3-6x their own size.
- [x] Corrected D229's over-generous statement about D218's replication argument, and
      appended an addendum to D229 so it does not read as sound standalone.

**STANDING RULE, now binding: a hurdle that names a test is not cleared until the test is
run.** A record must point at the artifact field holding the output; a multi-leg hurdle must
compute every leg or fail loudly.

**What is NOT in question:** the arm itself. +0.570 excess Sharpe against buy-and-hold's
+0.235 is an absolute measurement, not a rung delta, and was not audited here.

**What IS now open:** whether acceleration beats level. `I1 - I2` was the programme's one
carried-forward positive and it is a plausible estimate on an interval containing zero,
corroborated by a correlated study on overlapping data.

## THE BOOK HAS ITS FIRST ENTRY — S1, the recovery rule (2026-08-27)

[`docs/BOOK.md`](docs/BOOK.md). Admitted after [D237](docs/decisions/D237-the-recovery-rule-on-withheld-data.md),
the first pre-registered out-of-sample test anything in this programme has passed.

- **T1 (60 new tickers, zero overlap):** +0.779 excess Sharpe against buy-and-hold's +0.230,
  delta **+0.549** — and the effect **grew** rather than shrank. All three hurdles cleared,
  including a matched-count rotation null.
- **Still wrong with it, all four recorded in the entry:** every interval contains zero
  (short by 0.106); hurdle E fails at 9 entries/symbol; the holdout correlates **+0.978** with
  the training set; and it **lost to buy-and-hold** over the only forward period tested.
- **Not promoted to capital.** D237 pre-committed that, and R8 now makes it general.

## D251 — cross-sectional dollar-neutral, pre-screened and closed (2026-08-28)

**D250's inversion applied a second time, and it paid a second time.** Eight ranking scores —
D246's stop exactly — each with its a priori long leg declared before the run. No
pre-registration, no runner, no null. **D245's never-seen cohort was not touched.**

- **The premise checks out and is not the null.** Eigenvalue participation ratio **3.61** on raw
  returns against **11.55** on market-neutral residuals: removing the common factor really does
  triple the breadth. *The argument being right and the family paying are separate claims.*
- **The spread table cleared and every book still lost.** RESMOM was the cleanest cross-sectional
  relationship this programme has found — monotone across all five quintiles, **+4.80%/yr** edge,
  net beta only −0.14 — and its book made **−2.41%/yr**. All sixteen lost.
- **The gap is the finding.** `gross = exposure × edge` **needs a third term for a two-sided
  book**: minus the short leg's convexity. A daily-rebalanced short earns `log(2 − e^r)`,
  expectation `−μ − σ²`, worth **6.2 to 14.9 points a year** here — D238's +9.22 from the other
  side. **A spread table is stated in a coordinate system where shorting is free of variance
  drag.**
- **R10's literal form cannot fire on a fixed-count sort** — it is *less* crowded than its own
  rotated null. The binding form is **net beta**, and it fired twice: BAB at **−1.27** and
  low-vol at **−0.74** are levered short-the-market books wearing factor names. **Matched
  notional is not matched exposure.**
- **Also measured:** short-horizon relative strength is *reversal*, not momentum (both fail their
  declared direction), and S1's level rules do not survive being turned into ranks.

## D249 — the inverse wedge breakout, closed (2026-08-28)

Registered **separately and explicitly not as S3**, because it is the inverse of a failed
construction and [D246](docs/decisions/D246-the-search-protocol-for-s3.md) Constraint 3 forbids
complement-chasing under that protocol. **D245's reserved never-seen cohort was not spent** — the
runner refuses to open it and the refusal is pinned by test.

- **Every return hurdle failed.** 0 of 3 cells beat the matched-count rotation null on the 57
  (29.0th / 63.0th / 74.7th percentile) and 0 of 3 on the 60 (10.1st / 15.7th / 7.3rd). Costs are
  not the cause: breakeven 24.9–81.6 bp against ~1.6 charged.
- **The mechanism is concurrency, not per-bar loudness.** The two null legs disagreed — W2 at the
  **99.8th percentile on money** and the **63.0th on Sharpe** — because its book is **2.20× more
  volatile** than a randomly-timed book of identical exposure and turnover. Decomposed: the held
  bars are only **1.14×** as volatile as average, but the book holds **more than 20 of 57 names on
  13.7% of bars** where a per-symbol-rotated book does so on **0.0%**, peaking at **41** against the
  rotation's 23. **Converging channels break downward together, because they break when the market
  falls.** The rule is not choosing which ETF to buy; it is choosing when to buy all of them, and
  W2 earns 5.47 units of money per unit of volatility where the rotated book earns 6.40.
- **An error in the motivating measurement, found before registering and corrected in it.** "50.4
  entries/symbol at k=2" counts armed **setups**. Only the down-breaks are traded, not every episode
  triggers, and overlapping trades are suppressed — the real figure is 16.4 mean and a **minimum of
  5** per symbol. **Hurdle E fails, worse than S1's 20.**
- **The overlap answer: neither a new arm nor S1 in disguise.** `P(S1 | wedge)` peaks at **32.5%**
  against an 18.2% chance baseline (1.79× chance, against S2's 0.49×), ρ at most **+0.389**. The
  two rules lean on a shared population without being the same rule, and the operative half is that
  there is no edge here to diversify.

**Two things to carry forward, and the first is R9's neighbour rather than a case of it.**

1. **A pooled conditional-return table cannot see the book it implies.** 1,474 down-breaks look
   like 1,474 observations and are a few dozen market-wide events. **Report concurrency — names
   held per bar, actual against rotated — beside any pooled table whose triggers can synchronise
   across the universe.** `concurrency` in `scripts/run_wedge_inverse.py` is short and reusable.
2. **A per-symbol rotation null is a biased control for a market-wide signal, in a known
   direction.** Independent offsets destroy cross-sectional synchrony, so the null under-states the
   arm's volatility: flattering on money, penalising on Sharpe. Still the right control for
   exposure and turnover — but the concurrency gap should be reported next to the percentile.

*Neither is promoted to a standing rule; recorded here so the next study that needs them can find
them.*

## The only live thread

- [ ] **A SECOND, UNCORRELATED STRATEGY.** Now the highest-value item in the programme, and the
      arithmetic is specific: required data scales as `1/delta²`, so two arms at rho ~ 0 give
      **x sqrt(2)** on the delta and cut the requirement from **8.6 years to 4.3** — significant
      on data already in hand, with no waiting. It also covers S1's one demonstrated weakness,
      since T3 showed it cannot keep pace in a strong bull market.

      **D238 sharpened the target and closed the obvious candidate.** The short-side mirror
      was tried and it **supplies the correlation but not the return**: `corr(S1, M1) =
      -0.0687`, which is exactly the rho ~ 0 the argument above needs, at an excess Sharpe of
      **-0.407**. Adding an arm helps only when `SR_B > rho * SR_A = -0.051`, so the combined
      book scores **-0.484 against S1 alone**, with the whole 90% interval below zero.

      **The bar for arm two is therefore roughly -0.05 excess Sharpe at rho ~ 0, and
      uncorrelatedness was never the binding constraint.** That is a much easier target than
      "beat S1" and a much more specific one than "find something uncorrelated".

      **And one constraint is about the fixture, not the rule:** on 57 long-only US equity
      ETFs the worst-conditioned bars *any* of these constructions can isolate still return
      **+0.85%/yr**. A short arm needs instruments that actually fall.

      **D239 closed the second candidate and added the sharpest constraint yet.** Twelve-month
      time-series momentum is not skill-free on this fixture, it is an **anti-signal** — the
      **0.7th percentile** of its own rotation null on Sharpe, the **0.2nd on money**, with
      selection quality of **−35.8%** against a random slice of the same exposure. The
      mechanism matters more than the verdict: 2018–2024 is dense in sharp **V-shaped**
      reversals, which whipsaw trend and are exactly what S1 buys.

      > **Arm two must not be another bet on reversals-beating-continuations. S1 already is
      > one, and that is now recorded as its seventh weakness.**

      Candidates that remain live and do *not* violate it: **cross-sectional dollar-neutral**
      (drift cancels, and D238's signed scorer finally makes it computable), and **pairs** —
      `ZScorePairsStrategy` already exists with tests, and the universe has natural candidates
      in `GDX/GLD`, `XOP/XLE`, `IWM/SPY`, `EWA/EWC`.

- [x] **D240 FOUND ONE — and it is the first candidate that has cleared every registered
      hurdle.** Enter at the onset of a structural uptrend (`g_lo > 0 AND g_hi > 0`, OLS slopes
      of log swing-low/high prices over 252 bars, `k = 3`), exit at the earliest of 63 bars, the
      state ending, or a fixed **−8%** stop.

      **The number that matters is ρ = +0.150 against S1, not the Sharpe.** A0 beats its
      rotation null at the **97.3rd** percentile (money **99.2nd**); A2 beats R7's
      matched-exit-count overlay null at the **99.6th**; A2 posts **+0.822** at a **−1.93%**
      drawdown, Calmar **1.306** against S1's 0.527. Pairing arithmetic: **S1 + A2 → 1.032**,
      cutting time-to-significance from **8.8 years to 5.5**.

      **And what is wrong with it, which is a lot.** Hurdle E fails at **2 entries per symbol**
      against 30 — worse than S1's 9 and the single biggest reason to withhold belief. A2's pass
      is **not multiplicity-corrected** across the four overlay cells. The design is **fitted** —
      age cap, long-only and state definition all came from anatomy on this same fixture.
      Deployable return is **6.08%** against buy-and-hold's 8.42%, so it is a diversifier, not
      the return engine the income arithmetic needs.

- [x] **DONE — the combined book was built (D241) and tested on withheld data (D242).**

      **The book now has two entries.** S2 — the uptrend onset — scored **+0.672** on 60 ETFs
      sharing zero tickers with the training set, against **+0.610** mined. **It grew**, at the
      **99.7th percentile** of its rotation null and the **99.9th on money**, with a delta over
      buy-and-hold of **+0.442** against a floor of +0.147.

      **ρ with S1 held at +0.175** (mined +0.159), so the diversification is structural and
      travelled. Only 8.9% of S2's positions are also S1's — less than half what chance gives.

      **The combined book beat buy-and-hold on money AND drawdown out of sample** — 10.07%
      deployable against 8.34%, at −9.52% against −37.92%.

      **And the −8% stop was fitted.** It failed its overlay null out of sample (99.6th → 71.7th),
      exactly as D242's R3 predicted. It is a risk control, not alpha, and it is **not** part of
      S2. D240's headline is corrected in writing.

- [ ] **THE ONE THING THAT MOVES THE NEEDLE NOW: extend the fixture back to ~2005.**
      Every remaining weakness is the same weakness. The combined book's advantage over S1 has
      `p05 = −0.104`; hurdle E fails at **2 entries per symbol**; and the holdout correlates
      **+0.978** with training, so what has been shown is instrument-independence, never
      time-independence.

      **Six years of data against the ~8.8 needed.** Most of these ETFs go back to 2003–2005 and
      Alpha Vantage has it. Tripling the span would satisfy the data requirement outright,
      include **2008**, and fix hurdle E directly — since entries per symbol scale with span.

      **It is a fetch, not a research problem.** No further analysis of this fixture can
      substitute for it.

- [ ] **OPEN METHODOLOGICAL ITEM — three studies running, the result has lived in the
      complement of what was registered.** S1 came out of D234's failed cells; D238's exclusion
      reading out of the mirror's failure; and D239's inverse-of-an-anti-signal sits at the
      99.3rd percentile *by construction*. **None of these has been chased and the third must
      not be.** Either the registrations are systematically aimed wrong or the protocol leaks,
      and only one of those is testable. Needs a rule.


- [ ] **OPEN METHODOLOGICAL ITEM, opened by D251 — is the house scorer's PER-SYMBOL
      aggregation right for a TWO-SIDED book?** `signed_log_returns` averages per-symbol log
      growths, so every name is its own compounding sleeve. That is correct for every book this
      programme has scored — all of them long-flat — and it charges a dollar-neutral book the
      **name-level** variance drag on its short leg (`E[log(2 − e^r)] ≈ −μ − σ²`, 4–6%/yr at
      typical ETF volatility). In a real dollar-neutral account both legs sit in **one equity**,
      so the drag is set by the **spread's** variance, not by each name's.

      **It is a 6.6-point swing and it flips the sign** of D251's best cell. It is not a licence
      to re-score anything: the two agree to well inside a tenth of a point on long-flat books,
      so nothing already in `BOOK.md` moves. **What it blocks is registering a long-short arm
      before the question is settled**, because the answer decides the verdict rather than
      decorating it.

- [ ] **Test the arm on unmined data** — ETFs outside these 57. No further work on this
      fixture can narrow the intervals above, because they are a property of the sample.

## RESOLVED — the open item that mattered most (closed by D230)

**Every ladder delta in D217 and D218 was reported as clearing a hurdle whose bootstrap leg
was never computed.** The leg now exists, and D218's headline `I1 - I2 = +0.628` fails it in
all four cells with a 90% interval of `-0.133` to `+1.325`.

This does **not** say the effect is zero — it says the reported certainty was not earned.

~~D218's cross-construction replication argument (D217's +0.285 from unrelated arithmetic) is
separate evidence the bootstrap cannot see.~~ **D230 corrected this.** The `I1 − C ≈ 0` leg is
exactly what the sweep dissolves (intervals ≈ ±0.3), and "independent" overstated it: D218's
span is a *subset* of D217's on the same 57 ETFs, so the two are correlated. What survives is
**corroboration, not independent replication**.

- [x] **Ran `paired_block_bootstrap` against every delta this programme has reported.**
      Closed by D230: 8 of 24 cleared as scored, **0 as claimed**, all 24 intervals contain
      zero.

## Now — D228, the filter search (opened and closed 2026-08-27)

Record `docs/decisions/D228-mining-the-mined-fixture.md`, page `FILTER_SEARCH_RESULTS.md`.

- [x] Defined the **free/costly boundary** the programme never had: a look is any operation
      conditioned on the arm's realised P&L. Describing the market is free.
- [x] Mined the arm's **construction**, not its returns — eight candidates from what the arm
      throws away (sign only, unit size, equal weight, cash half the time). Zero looks spent
      on exploration.
- [x] Built the **best-of-search null** and measured the floor at **+0.104**.
- [x] **Nothing clears.** Best candidate +0.023, below the floor and barely above the null's
      median. Both gates also fail hurdle E.
- [x] **The mechanism measured**: r = +0.823 between exposure delta and money delta.
- [x] Honoured D220's volume stop rather than overriding it.

**THE FILTER LINE ON THIS ARM IS CLOSED.** Seven studies have tried to improve it by filtering
and all seven failed. D228 supplies the reason rather than another instance: filtering removes
exposure, and on this arm money *is* exposure.

**Corrected programme-wide:** rf on a long-flat book belongs on the **exposed fraction**. The
arm is **+0.570** excess Sharpe against buy-and-hold's **+0.235** — not the +0.354 / +0.240
quoted before the correction.

**Open, and now the only live thread on this line:** the arm has never been tested on unmined
data. D229 (the jerk rung) is pre-registered and not yet run.

## Now — D226, the gate on 57 ETFs (opened and closed 2026-08-27)

Record `docs/decisions/D226-the-volume-gate-on-57-etfs-at-15-minutes.md`, page
`ETF_INTRADAY_RESULTS.md`.

- [x] Fetched, split-adjusted and committed a 57-ETF 15m fixture (3.19M rows, 7.94 live
      years, ZERO zero-volume bars). Twelve unadjusted splits found and fixed - worst was a
      **+1,772% single bar** - in prices AND volumes.
- [x] **THE SPIKE MOVED.** H clears at one window of ten (96 bars); D224's committed
      200-bar window lands at the 45th percentile. Two spiky profiles, different spikes.
- [x] Three cells cleared the multiplicity floor - a first - because 57 instruments tighten
      the null, not because the effect is stronger.
- [x] Nothing survives; the gate loses money to its own parent.
- [x] **The dividend fetch changed the verdict** - price-only it ties, dividend-adjusted it
      loses by 4.6 points.

**THE VOLUME REGIME GATE IS CLOSED.** It survived two coins and two sampling rates; given 57
instruments and its own pre-registered sweep it produced a spike at a different window while
losing money to the arm it filters. That is a more useful negative than another failed floor,
because it explains *why* D224 and D225 looked positive without needing them to be wrong
about their own numbers.

**What survives is the method:** the matched-count null, the floor-from-the-null correction,
naming both metrics up front, and pre-registering the sweep. Those made a fitted parameter
visible in one 9-minute run instead of surviving three more studies.

**Open, and now the only live thread:** the acceleration-versus-level result from D217/D218
has never been tested on unmined data. Everything since has been about a filter on top of it.

## Now — D227, abandoned on power (2026-08-27)

Record `docs/decisions/D227-the-time-split-that-cannot-answer-its-own-question.md`.

- [x] Designed the time split, verified the split bar is clean (149,192, parent flat on
      both symbols, zero straddling trades).
- [x] **Computed the power BEFORE running it, and it kills the design.** Per-half MDE
      +0.554 to +0.642 against effects of +0.558 to +0.635 - the effect sits ON the
      threshold. P(all four symbol-halves clear) = **7%** on an effect that is real by
      assumption.
- [x] Checked the better-powered reformulation (difference between halves): detects a full
      collapse only 37% of the time. Also unusable.
- [x] **Zero looks spent.** Blind to the outcome throughout.

**The transferable lesson:** compute the MDE before designing the stop, not after seeing
which half failed. A stop that fires 93% of the time on a true effect is not a hurdle.

**The stability question is redirected, not abandoned** - it goes to the 57-ETF intraday
fixture, where 57 instruments carry more information about generalisation than two halves
of two correlated coins.

## Now — D225, the gate at 1h (opened and closed 2026-08-27)

Record `docs/decisions/D225-does-the-volume-gate-survive-a-change-of-sampling-rate.md`.

- [x] **The gate replicates at 1h** — not a sampling artifact. H clears on both symbols.
- [x] **Its working window is one point wide**, and inverts at 200h into a significant
      anti-signal. This is the strongest mark against the result on the record.
- [x] Separated two claims: the SIGNAL is scale-free in bars; the GATE is window-critical.
- [x] Verified by bit-exact reproduction of D224's artifact (delta = 0.00e+00).
- [x] Recorded AFTER the run and disclosed; the 40-cell sweep was unregistered.

**Standing constraint now in force:** the 50-hour window is **contaminated for selection**.
It was clean in D224 because it fell out of "200 bars at 15m" rather than a search. Any study
that picks 50h from here inherits D225's 40 looks.

**The open thread, and the shape it now has.** The gate is above its selectivity null on two
symbols and two sampling rates, and below its multiplicity floor on both. The next question is
no longer "does it work" but **"is 50h a property of the market or of these two coins over this
span"** — and the cheapest discriminating test is a TIME split, since 8.29 years is available
and needs no new data.

## Now — D223 and D224 (opened and closed 2026-08-27)

Records `docs/decisions/D223-the-volume-regime-gate.md` and
`docs/decisions/D224-the-assembled-strategy.md`, page `ASSEMBLED_RESULTS.md`.

- [x] Measured both premises before designing. Volume/volatility: **confirmed, 4.5x**.
      Signal-to-noise: **refuted** — VR falls 1.35 -> 0.67, so loud markets REVERT.
- [x] Ran the user's specified stack as a **2x2 factorial** rather than whole.
- [x] **The volume gate clears hurdle H on both symbols** — the first time anything here has
      beaten its matched-count random null.
- [x] It fails the multiplicity floor. ETH clears the FRESH floor and fails the verdict one.
- [x] The 2-ATR stop stops out 98% of trades and costs 2-3 Sharpe. Closed at these
      parameters, and D224 pre-committed to not sweeping them.
- [x] Interaction strongly negative, as the census predicted.

**Two methodology keepers.** `var_trials` must come from the **simulated null**, not from a
study's own cells — D219's amendment identified the inflation and D224 shows it at its
extreme (+4.944, unusable). And a stack gets run as a **factorial**, because a bad number
from a whole stack teaches nothing about which part caused it.

**The open thread, and it is the most promising one this programme has:** the volume-regime
gate cleared selectivity by a margin above the stated MDE and failed only a floor set by
3,833 accumulated looks on a heavily mined fixture. **That is a statement about the fixture,
not the idea.** The next step is the same pre-registered claim on **unmined data**, where the
floor is set by ten looks and ETH's +0.584 would clear comfortably. Not another
parameterisation here.

## Now — D222, the scaling ladder (opened and closed 2026-08-27)

Record `docs/decisions/D222-does-the-fine-bar-advantage-grow-with-the-window.md`, page
`SCALING_RESULTS.md`.

- [x] Tested a user prediction with a SHAPE - that the fine-bar margin grows with the
      timeframe - across k = 4, 32, 96.
- [x] **It does not.** Delta goes up, down, then sideways, is negative in 3 of 6 cells, and
      every bootstrap interval straddles zero.
- [x] The internal check is the strongest evidence: the same Delta(4) is +0.054 on 8.3
      years and +0.155 on 5.6. That is why the pre-registration refused to reuse D221's
      number.
- [x] Turnover, like signal, is set by the window and not the bar rate.
- [x] Scored 1 of 5; the one that landed was N4, the prediction that the study could not
      tell.

**Standing note on power, and it belongs in the DESIGN of the next study rather than its
bootstrap:** this fixture supports roughly 11 symbol-years of independent crypto history at
the frequencies that matter, so **effects below ~0.15 Sharpe are not resolvable on it,
whatever the hypothesis**. Check a proposed effect size against that number before building
a runner.

**Closed:** the D221 residual. Any future work citing "the 15m arm slightly beat the 1h arm"
is citing noise.

## Now — D221, sampling invariance (opened and closed 2026-08-27)

Record `docs/decisions/D221-does-the-indicator-care-about-sampling-rate.md`, page
`SAMPLING_RESULTS.md`.

- [x] A user proposal that turned out to be a paired test with a real null: scale the
      parameters by x4 on 15m so the window matches 1h, and see whether they converge.
- [x] **They converge.** |delta| <= 0.15 on every symbol, rho 0.94-0.96.
- [x] The control is what proves it: unmatched window, same bars, rho **0.50**.
- [x] **Corrected my own earlier screen** — "the signal is dead at 15m" was a
      parameterisation artifact. Matching the window moves BTC -0.298 -> +0.735 on the
      same bars. Scored 1 of 6 on my predictions; the proposal was right wherever we
      differed.
- [x] Recorded that `crypto_intraday_1h_raw` is 50.4% zero-volume and unusable.

**Standing conclusion.** Frequency is now a **cost** decision, not a signal decision. Porting
this indicator across timeframes REQUIRES scaling the parameters or the hypothesis has
changed. The practical rule is simply to multiply by the frequency ratio — the derived
lag-match gave no advantage over the naive x4.

**Open, and it is the natural next study:** whether a matched-window arm clears anything on a
fixture where fees are payable. On this evidence it needs maker rates or a coarser bar. That
is a pre-registration, not an extension of D221.

## Now — D219 and D220 (opened and closed 2026-08-27)

**D219 — the dual verdict.** A proposal to swap hurdles A–G for three portfolio criteria,
resolved as *both run, neither replaces the other*. Records
`docs/decisions/D219-the-dual-verdict-standalone-and-in-portfolio.md`.

- [x] Tested the proposal against the 24 existing arms before deciding: 2 of 24 pass, and
      the two survivors correlate at **0.90** — the first layering attempt produced two
      copies of one strategy.
- [x] Established that **leverage, not layering**, converts Sharpe into PnL, and that at
      rho = 0.90 the combined Sharpe ceiling is +0.823 for any N.
- [x] Added P4 (marginal contribution to a **pre-declared** incumbent) and P5 (deflate the
      **book**, not the arm).
- [x] **Pre-run amendment:** cross-fixture comparisons use `arm − matched B&H`. Corrected
      the claim that the crypto fixture buys meaningful multiplicity relief — it buys
      0.09–0.20 Sharpe, because the floor is logarithmic in N and set by `var_trials`.

**D220 — the volume filter.** Record `docs/decisions/D220-the-volume-filter-on-impulse-macd.md`.

- [x] Census first, blind to volume: **44.4% win rate**, 2.1:1 payoff — a majority of trades
      lose, so the proposal was not fighting the base rate. My contrary guess is recorded in
      the pre-registration as wrong.
- [x] ORACLE and matched-count RANDOM bounds computed **before** any filter was tested.
- [x] **0 survivors; every cell underpowered.** The transferable result is that this arm
      cannot be filtered and remain powered.
- [x] Hurdle H alone would have promoted a losing book — the conjunction caught it.

**Standing conclusions.** The ETF fixture is closed to arms *and* now to filters. The ORACLE
bound is worth keeping as a standing tool: it costs nothing and converts "would a filter
help?" into a bounded question.

**Not built, and it is a gap in the D220 runner rather than in D219:** P4 was measured only
against the buy-and-hold incumbent, which is a weak bar — all six long-flat cells clear it,
including cells losing 31 points to their own parent. The declared-order greedy incumbent
D219 also specified was not implemented. Any future study using P4 should build it.

**Next:** the crypto pre-registration (63 symbols), which owes a ragged-span and
inception-bias treatment, and where K6 — the delta transfers, the level does not — is the
falsifiable claim.

## Now — D218, Impulse MACD (opened and closed 2026-08-24)

A user-supplied indicator that turned out to be a test of D217 rather than a new question.
Record `docs/decisions/D218-the-impulse-macd-replication.md`, ledger `MACD_RESULTS.md`.

- [x] Spec read from the published Pine and restated in the record before any code.
- [x] The algebra first: `smma` is Wilder (alpha = 1/n, 33b lag), `zlema` has centre of mass
      exactly zero, so `md = 33b` and `sh -> 0` — the same level/acceleration split D217
      found, on a construction sharing no arithmetic with MACD.
- [x] Four rungs isolating the signal line, the dead zone, and D217's own R1 as control.
- [x] **J2 confirmed**: the replication holds in sign. **And the clean read is better**:
      I1 − C ≈ 0, so the two acceleration rungs are interchangeable and the result is about
      acceleration versus level rather than about either indicator.
- [x] J3 and J5 falsified: the delta is twice D217's (because the level rung is worse, not
      because the top rung is better), and the dead zone hurts both metrics.
- [x] 0 of 16 clear. Verdict floor +1.420 at 45,803 looks.

**The standing conclusion about this fixture:** no arm anyone runs on the 57-ETF universe can
clear +1.42, and the inherited prior rather than any new study is what put it there. Any
further work on the acceleration-versus-level result moves to unmined data — the crypto daily
universe — and tests `acceleration − level` rather than a named indicator, using whichever
construction is cheapest to compute.

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
- [ ] **β-hedged crypto pairs (v2 of D122's study).** The obvious next experiment the
      cointegration section points at: BTC/ETH's Engle–Granger β has median 0.74, not
      ≈1, so D94's finding (a fitted β costs more in estimation noise than it buys) does
      not transfer from a universe whose selector already demanded β ≈ 1.
      `research/beta_zscore.py` already exists. One variable per version (D92).
- [ ] **A crypto pair chosen inside the training window, from a universe.** D22's rule,
      which the BTC/ETH study structurally cannot satisfy — and the only thing that would
      give its DSR something honest to deflate (D126).
- [ ] **Volume on `TimestampedBar` (D111)** — the one interface change the breakout
      study wanted and could not make. Needs: a decision record accepting the schema
      change, a golden master covering a volume-gated entry, and a re-run of the D79
      cross-engine reconciliation. Unblocks the volume-confirmation filter (~40 lines
      against the existing `EntryFilter` protocol) and D3's ADV work shares the plumbing.
- [ ] **Execution realism for the breakout study** — the honest next experiment per
      BREAKOUT_RESULTS.md: intraday bars, a spread/impact model for crossing into a
      breakout, and fill-probability modelling for resting maker orders. The report's own
      finding is that this moves the numbers by more than the entire 0–40 bp fee range.
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
- **`Strategy` protocol variance (breakout session):** `engine/strategy.py` declares
  `strategy_id` as a settable attribute, so the frozen `ScheduledWeightStrategy` does not
  type-conform — the same trap audit F20 fixed on `Instrument.quote_currency` by making it
  a read-only property. Left alone (existing interface, not this study's to change) with a
  narrow `type: ignore` in `research/breakout_study.py`. Fix it the next time
  `engine/strategy.py` is opened for another reason.
- **Two studies now use different walk-forward stitching (D113).** The pairs studies chain
  per-window backtests; the breakout study runs continuously with a parameter schedule.
  Both are correct for their strategy's holding period, and neither is being rewritten —
  but any future cross-study comparison has to account for it.

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
- **2026-08-18** — Crypto breakout **universe cross-section** shipped (D140–D144,
  `docs/results/breakout_universe.md`). Built to attack `BREAKOUT_RESULTS.md`'s own
  stated worst bias rather than restate it: 77 tickers attempted across cohorts chosen
  for *past* prominence plus a cohort chosen *because it failed*, 63 admitted (20
  survived / 41 collapsed / 2 delisted), every exclusion and the one fetch failure named
  with its statistic. One fixed configuration everywhere (D141) so the cross-section is
  the only variable; every computation imported unmodified from `breakout_study`. The
  answer: **the strategy's value is concentrated in the assets that died** — 67% of the
  wrecks beat matched exposure against 45% of the survivors, and 98% vs 45% against
  buy-and-hold — while drawdown reduction holds in 63/63. BTC and ETH sit in the top
  quartile of their own cross-section. Two integrity notes worth more than the numbers:
  the ETF-calibrated sanity gate had to be explicitly overridden because obeying it would
  have deleted the failed cohort (D143), and the selection policy was amended once,
  post-hoc, when a stablecoin produced an undefined Sharpe — recorded in D144 with its
  reason rather than folded in silently. 644 tests green (44 new), mypy clean.
- **2026-08-19** — Breakout **cost–frequency frontier** shipped (D160–D165,
  `docs/results/breakout_intraday.md`). Tests `BREAKOUT_RESULTS.md`'s "fees are not the
  binding constraint" rather than restating it: the identical rule from 1h to 1d on
  BTC/ETH, 1h fetched once and resampled upward so every frequency spans the identical
  730 days (D161), walk-forward scaled to equal *calendar* duration so all six rungs get
  7 windows over the same 441 out-of-sample days. Two designs, deliberately not conflated
  (D162): **A** holds the 40-day/10-day horizon fixed and **never crosses** — turnover
  rises only 10.5× → 11.5× from 1d to 1h, so the original conclusion survives intact for
  the 40-day signal at any sampling rate. **B** holds the bar count fixed and **crosses at
  2h on both symbols independently** (4h the finest bar that clears), with turnover
  10.5× → 188.7× and fee drag 4.2% → 75.5% of capital a year. At 15m, reported as a
  turnover measurement with no return claim because 60 days cannot hold a 252-day training
  window (D163), the rule turns over ~790×/yr and pays ~315% of capital annually in fees.
  The methodological work is where the value is: the window this provider serves
  (2024-08 → 2026-08) contains **no trend edge at any frequency**, so the obvious
  net-Sharpe crossover reading returns "1d" everywhere and says nothing — the study
  therefore splices a precisely-measured cost curve onto the ten-year gross edge and
  states the assumption's direction (D165), and the answer is a bound: the true crossover
  is coarser than 2h, never finer. Two data-layer findings reported rather than absorbed:
  the shared cleaner's volume rule would have deleted half the hourly bars (D160), and the
  1h→1d resample does *not* reconcile with the committed daily fixture (D161) — pinned by
  a test on the negative. 643 tests green (36 new), mypy clean.
