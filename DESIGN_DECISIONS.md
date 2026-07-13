# Framework Design Decisions Log

> **Superseded 2026-07-13.** This file is a frozen historical snapshot (D1–D49, written before
> implementation started). It is kept for reference but is no longer updated. New decisions are
> individual files under [`docs/decisions/`](docs/decisions/README.md) (D50 onward); the standing
> rules R1–R4 have moved to [`docs/RULES.md`](docs/RULES.md). See [`README.md`](README.md) for
> the full doc suite map.

Format: **Decision — because rationale.** Status: ✅ committed · 🔜 deferred (with written rationale) · 📌 rule.
Date: 2026-07-07. Source: design review session (cost models, execution, validation, instruments).

---

## Cost architecture

**D1. Replace monolithic CostModel with a CostStack (ordered list of composable cost bricks)** — because real trading frictions (spread, impact, commission, financing, borrow, FX) are independent layers, not one number. Composing small bricks per backtest makes every friction individually swappable, testable, and comparable. ✅

**D2. Split costs into two interfaces: per-trade costs (charged on fills) vs carry costs (charged per bar on open positions)** — because they are mechanically different things with different hook points in the simulator. Per-trade: spread, impact, commission, FX conversion. Carry: margin interest, borrow fees, dividend flows, funding rates. This distinction is itself an important trading mental model. ✅

**D3. Add square-root market impact brick (cost ∝ σ√(Q/ADV)); demote vol-proportional slippage to "another brick in the drawer"** — because the vol-proportional model ranks instruments by the wrong property (volatility instead of liquidity), overcharges liquid ETFs ~20×, and uses an invented constant (k=0.1). Sqrt impact is the industry-standard model reviewers/interviewers expect. Requires ADV field in data layer. ✅

**D4. Model IBKR's actual commission schedule (per-share, exchange fees, minimums) instead of flat bps + £1 min** — because the target broker is known and per-share pricing diverges from bps pricing by up to ~70× depending on share price. Free accuracy. ✅

**D5. Add margin interest carry brick: daily rate on (gross exposure − capital) when positive** — because market-neutral pairs run ~200% gross exposure, IBKR charges ~6%/yr on small balances, and for 10–50bps/trade edges financing drag is first-order. Currently modelled as zero. ✅

**D6. Store raw prices + separate dividends/splits table; compute returns from adjustments but fills/commissions from raw prices; add DividendFlow carry brick (credits longs, debits shorts)** — because adjusted prices silently corrupt historical cost math (commissions computed on rewritten notionals) and shorts pay dividends (XLE ~3% yield matters to pairs P&L). Blocking for any trustworthy pairs result. ✅

**D7. FX handled in two parts: FXConversionCost trade brick now; full multi-currency accounting deferred, with unhedged FX exposure reported as a tearsheet line item** — because base currency (EUR/GBP) vs USD positions creates real conversion costs and a hidden currency bet, but full multi-currency accounting is a large lift. Label the blind spot now, close it later. ✅ / 🔜

**D8. Cost-multiplier sweep harness: run every backtest at 0.5×/1×/2×/4× the CostStack, report all four in the tearsheet** — because for edges this thin, "does it survive 2× costs" is the single most informative output in the project — more valuable than any refinement to cost functional forms. Trivial once CostStack exists; first payoff of the refactor. ✅

## Execution / fill logic

**D9. Add LIMIT_TRADE_THROUGH fill assumption (fill only if price exceeds limit by ε) alongside optimistic touch-fill** — because touch ≠ fill (queue position) and bar-level limit fills are adversely selected. Keep both; compare sensitivity. ✅

**D10. Gap-through-stop fills at the bar open, not the stop price** — because filling at stop price through a gap is free money and fantasy risk numbers. This is a bug fix, not a configurable option. ✅

**D11. Rename "VWAP" fill assumption to TYPICAL_PRICE_OPTIMISTIC** — because (H+L+C)/3 is typical price, not VWAP, is unknowable intra-bar (mild look-ahead), and labelling it "realistic" is dishonest. Keep as sensitivity bound only. ✅

## Instruments

**D12. Introduce Instrument abstraction: positions/fills reference instrument objects, not ticker strings. Interface: notional(), margin_requirement(), carry_components(), tradeable_quantity(), quote_currency** — because the framework currently hard-codes "everything is a share of stock"; making that assumption explicit and swappable is what enables multi-asset support. Do in the same refactor as CostStack (same surgery, one anaesthetic). ✅

**D13. CostStacks are per-instrument-class** — because frictions genuinely differ: equity (tight spread, per-share commission, borrow/dividends), options (huge %-of-premium spread, per-contract commission, theta), crypto (%maker/taker fee, funding rate), FX (spread-only, rollover). Each cell of that matrix is a brick the instrument class declares. ✅

**D14. Crypto promoted above options in build priority; implement fully with a funding-rate carry brick** — because: clean free 24/7 data (no dividends/splits/adjusted-price trap), dead-simple fee schedules, funding rate is structurally identical to the existing borrow-fee brick (just signed), and crypto perps are the one venue where the "short overhyped things" thesis is executable without locates or buy-in risk. ✅

**D15. FX as plumbing, not strategy venue** — because the FXPair instrument (spread + rollover carry) is needed anyway for multi-currency NAV, but retail spot-FX edges are brutal. Low priority as a trading venue. ✅

**D16. Options implemented as a well-formed stub: real dataclass fields + contract multiplier logic, NotImplementedError on hard parts (margin, pricing, Greeks, assignment), pointing at docs/options_extension.md** — because the put-spread thesis is unrepresentable without an options wing (pricing, per-contract commissions, 5–10%+ spreads on illiquid strikes), which is months of work + paid data. A committed shape + written scoping rationale reads as maturity; a half-built module reads as sprawl. 🔜

**D17. Instruments own their trading calendar: instrument.periods_per_year(bar_duration); audit every annualisation constant in the codebase** — because equities ≈252 days, crypto = 365, FX ≈260, and hard-coded /365 or /252 constants become a subtle bug farm across asset classes. ✅

## Data & portfolio layers

**D18. Per-asset-class data fetchers behind one DataSource interface: get_bars(instrument, timeframe). Existing yfinance fetcher becomes EquityDataSource** — because each asset class has different sources but the engine should not care. Options data source stays unwritten. ✅

**D19. PortfolioState converts all positions to base currency for NAV** — because a multi-currency book has no meaningful single NAV otherwise. Depends on D7 FX plumbing. ✅

## Validation & research integrity

**D20. TrialRegistry: every backtest run appends config hash + params + headline metrics to local SQLite/CSV. Build before any real experimentation** — because Deflated Sharpe requires the number of trials attempted, and that count cannot be reconstructed retroactively. The one component that can't be retrofitted. ✅ (urgent)

**D21. Deflated Sharpe Ratio added as a sibling to the IS/OOS overfitting ratio, not a replacement** — because the ratio is a quick smoke alarm but statistically noisy at ~8–12 OOS windows; DSR is the proper instrument and punishes for number of trials (fed by D20). ✅

**D22. Pair selection moves inside the walk-forward training windows, over a broad universe** — because testing pre-known famous pairs (XLE/XOP, GLD/SLV) is meta-level in-sample selection: they're famous *because* they worked. Walk-forward interface generalises so each window's fit() can return different pairs, not just different parameters. ✅

**D23. Synthetic-pair null test: generate cointegrated-looking series with zero true edge; strategy must earn ~nothing on them** — because the returns-shuffle Monte Carlo destroys the autocorrelation a mean-reversion strategy trades, so it can't distinguish edge from luck. Block bootstrap retained; synthetic null added as the stronger test. ✅

## Scope & sequencing rules

**R1. 📌 No new framework code until the framework has produced one real number** (XLE/XOP walk-forward through the *current* imperfect version) — because research output, not infrastructure, is what a quant portfolio is judged on, and observed defects motivate better fixes than theorised ones. Suspended for design-only sessions; binding on execution sessions.

**R2. 📌 Timebox the CostStack + Instrument refactor to ~2 weeks of available time** — because satisfying architecture work expands to fill all available time; the framework earns its existence at the cost-multiplier sweep, not before.

**R3. 📌 Deferred list is explicit and written: options wing (docs/options_extension.md), full multi-currency accounting, live IBKR integration** — because a reasoned scoping decision is a portfolio asset; silent sprawl is a liability.

**R4. 📌 Design decisions get recorded in this file as "decision — because rationale"** — because theorising must converge to commitments, not sprawl into open-ended exploration. This document is the map.

## Build order (as committed)

1. TrialRegistry (D20) + stop-gap bug fix (D10) — small, urgent, un-retrofittable
2. CostStack + Instrument abstraction, one refactor (D1, D2, D12) — timeboxed per R2
3. Equity bricks: IBKR commission (D4), margin interest (D5), sqrt impact (D3)
4. Cost-multiplier sweep (D8) → **run pairs through it; first real result**
5. Data layer rework: raw prices + dividend flows (D6, D18)
6. Crypto instrument + funding-rate brick (D14)
7. FX plumbing: conversion brick + base-currency NAV (D7, D19)
8. Options stub + design doc (D16)
9. Validation: pair selection in walk-forward (D22), DSR via registry (D21), synthetic nulls (D23)

---

# Session 2 additions — full-framework review (D24 onward)

## Data layer

**D24. Immutable data snapshots: fetch once, freeze with a fetch-date stamp; every trial logs its snapshot ID** — because yfinance restates history (dividends re-adjust all past prices, corporate action fixes rewrite old bars), so identical code produces different results months apart, silently making TrialRegistry entries incomparable. Data versioning is as fundamental to research integrity as trial counting. Brick: `SnapshotStore` sitting between fetcher and engine; engine only ever reads snapshots, never live fetches. ✅

**D25. Cleaner returns data + a change report; cleaning rules are explicit, versioned, and logged per dataset** — because silent cleaning makes "strategy result" indistinguishable from "cleaning artifact." The cleaner's contract changes from `clean(df) -> df` to `clean(df) -> (df, CleaningReport)`, and the report (what was filled, dropped, patched, and why) attaches to the snapshot metadata. ✅

**D26. Sanity gate between data source and engine: OHLC consistency (low ≤ open/close ≤ high), bar-to-bar move thresholds, volume anomaly flags — data failing the gate is quarantined, not passed through** — because yfinance is a scraper, not an API; it breaks and serves bad prints without warning, and garbage currently flows straight to fills. Brick: `DataValidator`, one class, applied at snapshot creation. Second-source cross-checking deferred as a future brick behind the same interface. ✅ / 🔜

## Signals & strategy interface

**D27. Pipeline boundary changes to signal → target weight → orders. Strategies output desired portfolio weights; a central sizer/allocator converts targets to orders** — because welding alpha ("XLE rich vs XOP") to implementation ("sell 43 shares") inside each strategy prevents reusing sizing logic, prevents comparing signals independent of sizing, and prevents netting orders across strategies (A buying what B sells should cancel internally, not pay costs twice). This is the standard architecture (Carver) and the single biggest interface change in the framework — cost of fixing grows with every strategy written, so it lands early. ✅

**D28. Regime models obey the same fitting rule as pair selection: fit inside the walk-forward training window only, structurally enforced (regime module receives training data via the same guarded accessor as strategies)** — because regime detection is the easiest overfit vector in the codebase ("works except in high-vol regimes" is usually discovered by looking at when it lost money). If the framework doesn't structurally prevent full-sample regime fitting, the module is a foot-gun. ✅

**D29. Pair selection handles multiplicity: rank candidate pairs and take top-N rather than thresholding p-values; the number of pairs tested is logged to the TrialRegistry** — because testing 200 pairs at p<0.05 yields ~10 false positives from pure noise. D22 fixed look-ahead; this fixes multiple testing. Both are needed for the selection step to be honest. ✅

## Portfolio layer

**D30. Risk checks run per-bar at portfolio level, not only as pre-trade gates** — because positions drift into violation via price moves with no order ever firing a check (a pair whose legs both moved can silently exceed gross exposure limits). Controls-engineering framing: safety interlocks run continuously, not only on operator commands. Brick: `RiskMonitor.evaluate(portfolio_state, bar)` called every bar by the engine; violations emit corrective orders or halt flags. ✅

**D31. Allocator is a bare-bones stand-in: constant capital split across strategies, behind a stable `Allocator` interface** — because multi-strategy allocation (correlation, capacity, sleeve rebalancing) is a hard problem with zero validated strategies to inform it; any interface designed now from speculation will be wrong. Constant-split keeps the Lego socket real and testable while committing nothing. Same pattern as the options stub: shape committed, cleverness deferred. ✅

## Backtest engine

**D32. Structural look-ahead guard: strategies receive a `DataView` accessor that physically cannot return bars beyond the current index and raises if asked — the full DataFrame is never reachable from strategy code** — because slicing-by-convention (`iloc[:i+1]`) is an honor system; one careless reference to the underlying frame (or one 6:50am mistake) silently invalidates every result. The framework's entire value proposition is trustworthy answers; trust must be enforced by structure, not agreement. ✅

**D33. Bars for sequencing, timestamps for accrual and annualisation. All carry costs (borrow, margin interest, funding) accrue on the calendar-day gap between consecutive bar timestamps, not per bar** — because a Friday→Monday hold is one bar but three calendar days of borrow and interest; per-bar accrual with `bar_duration_days=1.0` undercharges every weekend and holiday (~40% of calendar time on daily equity data). Bug fix, not an option (same class as D10). Also resolves annualisation once instruments carry their own calendars (D17). ✅

**D34. Explicit RNG seed policy: every stochastic component (Monte Carlo shuffle, block bootstrap, synthetic nulls) takes a seed parameter; seeds are logged in the TrialRegistry** — because "deterministic simulator" means nothing for reproducibility if the analytics layer is silently nondeterministic. Re-running a logged trial must reproduce it to the penny, randomness included. ✅

**D35. Configuration becomes declarative: SimConfig and strategy configs are plain data (dicts/strings — e.g. `{"cost_model": "ibkr_v1"}`), with factories constructing live objects from them** — because the TrialRegistry's "config hash" is impossible while configs hold live objects (cost model instances, timedeltas, CostStacks) that don't serialise or hash stably. Declarative config makes trials hashable, diffable, comparable, and re-runnable — load-bearing for D20, D21, and D34. ✅

## Analytics

**D36. Tail-risk metrics are gated by sample size: VaR/CVaR and extreme percentiles only report when observations support them, otherwise the tearsheet prints "insufficient data" — and Monte Carlo default n rises from 500 to ≥10,000 (seeded per D34)** — because 95% VaR from ~500 daily points estimates the 25th-worst day, and n=500 was an arbitrary number; simulations are cheap. Reporting numbers you shouldn't trust is worse than not reporting them — reviewers probe exactly these. ✅

**D37. Benchmark frame matches strategy type: market-neutral strategies benchmark against the risk-free rate, and realised beta to SPY becomes a first-class tearsheet metric with an explicit ≈0 expectation** — because beating SPY is the wrong question for a neutral book, and a nonzero realised beta falsifies the "market-neutral" claim itself. The most important diagnostic for the stated philosophy currently isn't printed. ✅

**D38. Sector momentum is explicitly labelled a learning/reference strategy in the repo (README + strategy docstring), not part of the portfolio thesis** — because it is directional and beta-loaded inside a framework whose stated philosophy is market-neutrality; unacknowledged, the contradiction reads as incoherence to a reviewer. One honest paragraph converts a liability into evidence of self-awareness. ✅

## Testing

**D39. Golden-master tests: at least one hand-computed tiny scenario (≈5 bars, 2 trades, known costs, weekend gap included) asserted to the penny** — because unit tests verify the code does what the code says, not that the simulator is right; a scenario verified by hand arithmetic is ground truth. The weekend gap doubles as the regression test for D33. ✅

**D40. Property-based invariant tests on the simulator: cash never negative absent margin, every fill price within its bar's high–low range, buys+sells reconcile exactly to positions, NAV continuity across bars** — because invariants catch whole classes of bugs no example-based test anticipates, and the simulator is the component everything downstream trusts blindly. ✅

**D41. Cross-engine validation: run one identical strategy on identical data through an established engine (backtesting.py or vectorbt) and reconcile every penny of divergence, documented in the repo** — because one successful reconciliation buys more trust than 200 unit tests, and every divergence surfaces a design assumption — which directly serves the framework's stated purpose of understanding everything. Runs once per major simulator change, not per backtest. ✅

## Build order — revised with session 2 items

1. TrialRegistry (D20) + bug fixes: stop-gap (D10), calendar-day accrual (D33)
2. Declarative config + factories (D35) — prerequisite for the registry hash being real
3. CostStack + Instrument abstraction + signal→target→order pipeline (D1, D2, D12, D27) — one large refactor, timeboxed per R2; D27 added here because it touches the same interfaces
4. Structural guards: DataView look-ahead guard (D32), per-bar RiskMonitor (D30), allocator stand-in (D31)
5. Equity bricks: IBKR commission (D4), margin interest (D5), sqrt impact (D3)
6. Cost-multiplier sweep (D8) → **first real result**
7. Data layer: snapshots (D24), cleaner contract (D25), sanity gate (D26), raw prices + dividends (D6, D18)
8. Testing hardening: golden master (D39), invariants (D40), cross-engine reconciliation (D41)
9. Analytics honesty: sample-size gating + n≥10k (D36), beta + risk-free benchmark (D37), momentum labelling (D38), RNG seeds (D34)
10. Crypto + funding brick (D14), FX plumbing (D7, D19)
11. Options stub + doc (D16)
12. Validation science: pair selection in walk-forward (D22) + multiplicity (D29), regime fitting rule (D28), DSR (D21), synthetic nulls (D23)

---

# Session 3 additions — final sweep of the original design (D42 onward)

**D42. Intra-bar ambiguity convention: when two exits are touchable in the same bar (e.g. stop and limit/target both within the bar's range), assume the adverse one fills first** — because OHLC bars cannot tell you whether the high or low came first; without a stated convention the simulator silently picks the optimistic path. Conservative-path assumption is documented and tested, not implied. ✅

**D43. Short-sale cash accounting made explicit: short proceeds credit cash but the margin requirement locks equivalent buying power; NAV = cash + longs − |shorts|, defined in one place and tested** — because "free" short proceeds funding new longs is the single most common silent simulator bug, and the current PortfolioState design never states its policy. ✅

**D44. Engine enforces a warm-up period: no trading until the longest indicator lookback (incl. the cost model's vol_window) is satisfied; vol estimates use data up to the *previous* bar only** — because right now the first 21 bars silently use the fallback cost regime (a mid-backtest cost shift), indicators computed on partial windows are noise, and same-bar vol estimation is a small look-ahead. ✅

**D45. Multi-ticker bar alignment policy is explicit: pairs/multi-leg strategies use inner-join alignment; a missing bar on one leg means no trading that bar (carry still accrues)** — because forward-filling fabricates prices that fills then execute against, and unstated alignment is where pairs backtests quietly diverge from reality. ✅

**D46. Per-strategy P&L attribution: fills are already strategy-tagged; add per-strategy virtual books so sleeve-level returns exist** — because order netting (D27) makes portfolio positions non-attributable, and the future allocator brick (D31) is blind without per-sleeve return streams. Cheap now, painful to reconstruct later. ✅

**D47. Money is float64 with a stated reconciliation tolerance (default 1e-6), used by every "to the penny" test** — because penny-exact assertions on floats fail spuriously or pass falsely; the epsilon is a policy, not an accident. ✅

**D48. No false affordances: enum values and flags for unimplemented behaviour are removed or implemented. Immediate case: FillStatus.PARTIAL either gains a volume-cap fill brick or is deleted** — because dead options imply capabilities that don't exist, and a reviewer (or future you) will trust them. Same rule applies to any config knob that no code path reads. ✅

**D49. Sharpe/Sortino take an explicit risk-free rate input, consistent with the D37 benchmark frame** — because rf≈0 shortcuts are wrong in a 4–5% rate era and materially flatter a market-neutral book whose honest hurdle *is* the risk-free rate. ✅
