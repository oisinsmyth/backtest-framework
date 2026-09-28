# Quant Backtesting Framework — Master Project Document

> **Frozen snapshot.** Collated once, 2026-07-13, as a single-file archive of the pre-implementation
> planning docs. Not updated going forward — see [`README.md`](README.md) for the live doc suite
> (decision records, changelog, current AI todo) added the same day, just before implementation began.

Collated: 2026-07-13. Contains all project documents to date, in order:

1. **Design Decisions Log** (D1–D49, rules R1–R4, build order)
2. **Verification Scheme** (per-step test gates)
3. **Development Timetable** (Week 0 → month 6, kill criteria)

Governing principles: Lego-brick modularity — every component swappable behind a stable interface. Trust enforced by structure, not convention. A step is done when its gate passes, not when code exists. Research output is the product; the framework is the instrument.

---

# Framework Design Decisions Log

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


---

# Verification Scheme

One gate per build step. A step is **done when its gate passes**, not when the code exists.
Test types: **U** unit · **G** golden-master (hand-computed, exact within D47 tolerance) · **P** property/invariant (randomised inputs) · **I** integration · **X** cross-validation against external reference.

Conventions: every stochastic test takes a seed (D34). Every G test lives next to a text file showing the hand arithmetic. CI runs everything offline (no live fetches — snapshots only, D24).

---

## Step 1 — TrialRegistry + bug fixes (D10, D20, D33)

**TrialRegistry**
- U: write→read roundtrip preserves config hash, params, metrics, snapshot ID, seed.
- U: registry is append-only — attempting overwrite of an existing trial ID fails.
- U: survives process restart (reopen file/DB, prior trials intact).
- U: identical config + snapshot + seed → identical hash; any semantic change → different hash.

**Stop-gap fix (D10)**
- G: long position, stop 45, next bar opens 38 → fill at 38, not 45.
- G: stop 45, bar opens 46 then low 44 → fill at 45 (intra-bar touch, no gap).
- G: mirror both cases for a short position (gap *up* through stop).

**Calendar accrual (D33)**
- G: short held Friday close → Monday close accrues exactly 3 days of borrow + margin interest.
- G: hold across a market holiday accrues the holiday.
- U: hourly bars over a weekend gap accrue the full gap, not one bar-duration.
- P: total accrued carry over any window == rate × Σ(calendar-day gaps), regardless of bar frequency.

## Step 2 — Declarative config (D35, D47)

- U: same config dict → same hash across runs and across dict key orderings.
- U: factory(config) produces objects whose behaviour is identical to hand-constructed equivalents (run a mini-backtest both ways, equity curves match within tolerance).
- U: invalid config (unknown model name, wrong type, missing required key) fails loudly at factory time with a message naming the bad key — never at bar 3,000 of a backtest.
- U: config → hash → registry → reload config → re-run reproduces the original result (the full reproducibility loop).

## Step 3 — CostStack + Instrument + signal→target→order refactor (D1, D2, D12, D27)

**CostStack**
- U: empty stack == ZeroCostModel to the tolerance.
- G: each brick alone vs hand arithmetic (one scenario per brick).
- U: stack total == sum of individual brick outputs; brick ordering effects are either zero or documented and tested.

**Instrument**
- U: equity notional = qty × price; tradeable_quantity rounding (whole, fractional, 8-dp crypto stub).
- U: option stub multiplier math correct; hard methods raise NotImplementedError pointing at the design doc (D16, D48).

**Pipeline (D27)**
- G: target weights on a known portfolio → exact expected orders.
- U: already-at-target → zero orders (no churn).
- G: strategy A targets +10 sh, strategy B targets −10 sh of same ticker → zero external orders; both virtual books updated (D46).
- U: same sizing module drives two different strategies without modification.

**Refactor regression (the big one)**
- G: a pre-refactor golden backtest (frozen snapshot, old cost assumptions expressed as bricks) reproduces its equity curve through the new architecture within tolerance. **The refactor is not done until this passes.**

## Step 4 — Structural guards (D30, D31, D32)

**DataView (D32)**
- U: requesting bar index > current raises.
- U: no public attribute or method of anything handed to a strategy returns the full frame (reflection/attribute audit test).
- I: a deliberately cheating strategy (tries `.iloc`, `.data`, parent refs) cannot obtain future bars — test asserts the exception, not the honour system.

**RiskMonitor (D30)**
- I: scripted scenario — both pair legs drift so gross exposure exceeds the limit *with no order submitted* → violation flagged on exactly the bar it occurs.
- U: pre-trade gate still rejects an order that would breach limits.

**Allocator stand-in (D31)**
- U: constant split sums to 1.0 across N strategies; capital changes propagate next bar.

## Step 5 — Equity bricks (D3, D4, D5)

- X: IBKR commission brick vs a table of ≥10 published-schedule examples (per-share rate, minimum, percentage cap — high-price, low-price, tiny-order cases).
- G: margin interest charged only on (gross exposure − capital) when positive; weekend case ties to D33.
- U: sqrt impact — doubling quantity multiplies impact cost by √2; ADV=0 or missing → loud error, not silent zero (D48 spirit).

## Step 6 — Cost sweep (D8) — **first-result gate**

- I: 0.5×/1×/2×/4× sweep → net P&L monotonically non-increasing in the multiplier.
- U: 0× sweep == ZeroCost run.
- I: **XLE/XOP walk-forward runs end-to-end on a frozen snapshot and produces a tearsheet with the sweep table.** This is the framework's existence-justification gate (R1/R2). The number can be ugly; it must be *produced*.

## Step 7 — Data layer (D6, D18, D24, D25, D26, D45)

- U: same snapshot ID → byte-identical data (checksum); re-fetch → new ID; every trial row carries a snapshot ID.
- U: cleaner given injected defects (NaN close, zero-volume day, 40% single-bar spike, low>high) → CleaningReport lists every change; clean input → empty report (D25).
- U: sanity gate quarantines OHLC violations and threshold breaches; quarantined data never reaches the engine (D26).
- G: known historical dividend (e.g. an XLE ex-date): short debited, long credited, on the ex-date, using raw prices (D6).
- G: commission on a pre-split historical bar computed on raw price, not adjusted — assert the difference vs the adjusted-price calculation is nonzero and equals hand arithmetic.
- U: pair with a missing bar on one leg → no fills that bar, carry still accrues (D45).

## Step 8 — Testing hardening (D39, D40, D41)

- G: THE golden master — ~5 bars, 2 trades, one weekend, one dividend, one gap-through-stop, hand-computed in an adjacent text file, asserted line-by-line: every fill price, commission, carry accrual, and the final NAV.
- P (hypothesis-style, seeded): across randomised price paths and order streams —
  - cash never negative absent margin;
  - every fill price within its bar's [low, high];
  - Σ(buys) − Σ(sells) == final position per ticker, exactly;
  - NAV change per bar == price P&L − costs − carry (no leaks);
  - broker.reset() → state identical to fresh construction (walk-forward leakage guard);
  - same seed + config + snapshot → identical equity-curve hash (determinism, D34).
- X: identical simple strategy (MA cross, market orders, fixed costs) on an identical snapshot through backtesting.py or vectorbt; every penny of divergence reconciled in a committed markdown doc (D41). Re-run on every simulator-touching change.

## Step 9 — Analytics honesty (D34, D36, D37, D38, D49)

- U: 100-bar series → VaR/CVaR report "insufficient data", not a number (D36).
- U: Monte Carlo n ≥ 10,000 default; same seed → identical percentile table (D34, D36).
- U: realised beta of SPY vs itself == 1.0 ± tol; beta of constant cash series == 0 (D37).
- U: Sharpe with rf=4% on a flat-return series is negative (D49 — catches silent rf=0).
- X: Sharpe, max drawdown, Sortino vs quantstats on the same return series, within tolerance.
- U: sector momentum strategy docstring/README carries the learning-strategy label (D38 — yes, a test that greps; labels rot otherwise).

## Step 10 — Crypto + FX (D7, D13, D14, D15, D17, D19)

- G: funding-rate brick — positive and negative funding both flow correctly (shorts *receive* positive funding); 8-hour funding accrued correctly across daily bars.
- U: crypto instrument annualises on 365; equity on its trading calendar — via instrument.periods_per_year (D17).
- U: lint test — no bare 252/365 constants outside instrument/calendar classes (grep-based; crude, effective).
- G: two-currency portfolio NAV in base currency vs hand calc at a fixed FX rate; conversion cost > 0 on a round trip (D7, D19).

## Step 11 — Options stub (D16)

- U: dataclass fields + multiplier notional correct; margin/pricing raise NotImplementedError referencing docs/options_extension.md; nothing else claims to work (D48).

## Step 12 — Validation science (D21, D22, D23, D28, D29)

- I: pair selection inside walk-forward — synthetic universe where a pair's relationship inverts after the training window: selection may pick it, but must demonstrably use only training data (structural test via DataView, D28/D32 shared machinery).
- P: multiplicity — top-N selection on a pure-noise universe of 200 series → OOS edge ≈ 0 within CI (D29); number of pairs tested appears in the registry.
- X: DSR implementation reproduces the worked example from the Bailey & López de Prado paper; trials count is pulled from the TrialRegistry, not typed in (D20, D21).
- P: strategy on zero-edge synthetic cointegrated pairs → mean P&L ≈ 0 within CI (D23). If this "profits," stop everything.
- U: demonstrate returns-shuffle vs block-bootstrap divergence on an autocorrelated series (documents *why* the shuffle was demoted).

---

## Cross-cutting gates

- CI runs Steps 1–12 suites offline on every commit; live-fetch tests are excluded by marker.
- Every G test's hand arithmetic lives in the repo next to the test.
- Every red test that reveals a simulator bug gets a one-line entry in DESIGN_DECISIONS.md if the fix changes behaviour.
- The X tests (IBKR schedule, quantstats, external engine, DSR paper) are the anti-self-deception layer: they anchor the framework to references you didn't write.


---

# Development Timetable

## Assumptions (the honest kind)

- **Budget: ~7 h/week.** Weekday mornings ~45 min × 5 = 3.75 h, plus one 3 h weekend block. If the morning habit doesn't hold, every date below slips 1:1 — the habit is the critical path, not the code.
- **Estimates include a 25% illness/life buffer.** Weeks like this one (sick, 2 h sleep) are the rule, not the exception. A slipped week is absorbed, not "caught up" — catching up is how streaks die.
- **A step is done when its VERIFICATION_SCHEME gate passes** (see that doc), not when code exists.
- **Scope cut already applied:** Step 10 (crypto + FX instruments) is deferred past the portfolio deadline. It's a strong framework feature but zero portfolio-narrative value vs. the pairs research. FX *plumbing* needed for base-currency NAV rides along in Step 7/9 minimally.

## Week 0 — now

No code. Recover from being ill; install the wind-down + morning routine and hold it for 7 consecutive days. Optional light task if a morning feels good: read Chan ch. 1–3. **Gate: 5 of 7 mornings happened.** If this gate fails twice, the problem is the routine design, not discipline — redesign it before touching the timetable.

## Phase A — Foundations (weeks 1–2, ~12 h)

- Step 1: TrialRegistry + stop-gap fix (D10) + calendar accrual fix (D33)
- Step 2: declarative config + factories (D35)
- Reading: Chan *Quantitative Trading* alongside.
- **Milestone: reproducibility loop closes** — a trial can be logged, reloaded, and re-run identically.

## Phase B — The whale (weeks 3–6, ~26 h, hard timebox per R2)

- Step 3: CostStack + Instrument + signal→target→order refactor
- Step 4: DataView guard, RiskMonitor, allocator stand-in
- **Slip rule:** if the refactor regression gate (Step 3's golden reproduction) isn't passing by end of week 5, split D27 (pipeline) out and land it in Phase D. Do not extend the whale.
- Reading: Carver *Systematic Trading* (directly informs D27).

## Phase C — First contact with reality (weeks 7–8, ~12 h)

- Step 5: IBKR commission, margin interest, sqrt impact bricks
- Step 6: cost-multiplier sweep → **run XLE/XOP walk-forward end-to-end**
- **Milestone (~week 8): THE FIRST REAL NUMBER.** Ugly is fine. This is the project's existence gate (R1). Log it, frame it, move on.

## Phase D — Trust hardening (weeks 9–11, ~19 h)

- Step 7: data snapshots, cleaner contract, sanity gate, raw prices + dividend flows
- Step 8: golden master, property invariants, cross-engine reconciliation
- **Milestone: the simulator is anchored to references you didn't write.**

## Phase E — Honest reporting (weeks 12–13, ~10 h)

- Step 9: sample-size gating, beta + rf benchmark, seeds, momentum labelling
- Step 11: options stub + docs/options_extension.md (cheap, high signalling value)

## Phase F — Validation science (weeks 14–17, ~22 h)

- Step 12: pair selection inside walk-forward + multiplicity, regime fitting rule, DSR (reproduce the paper's worked example), synthetic nulls
- Reading: López de Prado relevant chapters + Bailey/de Prado DSR paper; Gatev paper re-read.
- **Milestone: the framework can now say "no edge" and be believed.**

## Phase G — Research & portfolio (weeks 18–24, ~40 h)

This is the actual portfolio. The framework is frozen except for bug fixes.
- The study: Gatev distance → cointegration → Kalman (Anderson & Moore interleaved), pair selection in-window over a broad ETF universe, full cost sweep, DSR-adjusted results.
- Writeup: methodology, results (including negative ones), the "doesn't clear costs at retail scale, clears at £X AUM" analysis, scoping docs as appendices.
- **Parallel from week 18: reviewer access.** Finding senior quants to review it has lead time — QuantNet/Wilmott forums, LinkedIn, Manchester/Dublin meetups, cold emails with the writeup attached. This is a networking task and it starts before the writeup is polished.

## Summary line

Framework: weeks 1–17 (~100 h). Research + writeup: weeks 18–24. Portfolio lands ~month 6 — exactly on the original deadline, with zero slack beyond the built-in 25%. Anything added to framework scope now comes directly out of the research phase, i.e. out of the part reviewers actually judge.

## Kill criteria (pre-committed, so future-you can't negotiate)

- First real number (Phase C gate) not produced by **week 10** → cut Phase D to snapshots-only, drop cross-engine test to post-portfolio.
- Entering **week 20** without a started writeup → freeze all code permanently, write up whatever exists. An honest writeup of a modest study beats an unfinished ambitious one.
