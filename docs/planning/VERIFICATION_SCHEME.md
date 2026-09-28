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
