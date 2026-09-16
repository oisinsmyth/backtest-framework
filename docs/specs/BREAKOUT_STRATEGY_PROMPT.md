# Task: Implement and test a long-flat breakout trend-following strategy

## Context
Read `DESIGN_DECISIONS.md`, `VERIFICATION_SCHEME.md`, and `DEVELOPMENT_TIMETABLE.md` first. This strategy must conform to the design decisions (D1–D49) and standing rules (R1–R4), and slot into the existing architecture as a swappable strategy brick alongside the pairs and momentum strategies — same signal-to-orders pipeline, same walk-forward harness, same CostStack. Do not modify existing interfaces; if an interface seems insufficient, stop and flag it rather than working around it.

## Strategy specification

**Concept:** Long-flat trend following on daily bars. Flat is the default state. Enter on confirmed upward breakout, exit on a much faster trailing condition (deliberate hysteresis). No shorting.

**Baseline (implement first, no filters):**
- Entry: close(t) > max(high over bars t−40 … t−1). Signal computed strictly on completed bars — today's bar cannot trigger on itself. Execution at next bar open via the existing fill semantics.
- Exit: close(t) < min(low over bars t−10 … t−1).
- Bar boundary: 00:00 UTC, fixed. Do not test alternative boundaries.
- Position sizing: inverse-volatility (target vol / trailing realized vol, capped at 1.0× capital), using the existing portfolio layer if it supports it; otherwise fixed fractional as a stopgap and flag it.
- Instruments: BTC and ETH daily data to start (existing data layer / yfinance).
- Costs: run through CostStack with a maker-fee brick (0.00%–0.25% range) AND a taker brick (0.40%) as separate trials — the strategy's viability difference between these is itself a result we care about.

**Filter bricks (each implemented and tested SEPARATELY, added one at a time on top of baseline):**
1. Close-confirmation debounce: condition must hold for m consecutive closes, m ∈ {1, 2}.
2. Volume confirmation: trigger bar volume > 1.5× 20-day average volume.
3. Volatility-contraction precondition: only accept triggers when ATR(20)/ATR(100) < threshold (try 0.8, 1.0).
4. Higher-timeframe gate: only take entries when price > 200-day SMA.

Keep only filters that improve out-of-sample performance. Each filter is a separable, toggleable component — no hardcoding into the entry logic.

## Testing requirements (non-negotiable)
- Walk-forward: train_bars=252, test_bars=63, consistent with the existing harness. All parameter selection inside training windows only.
- Parameter plateau analysis: sweep N_entry ∈ {20, 30, 40, 55}, N_exit ∈ {5, 10, 20}. Report the full performance surface. A spike at one combination with poor neighbors = curve-fit; flag it explicitly.
- **Sweep-edge rule (literature-informed):** the published time-series momentum evidence (Moskowitz-Ooi-Pedersen 2012; Carver ex-AHL) locates trend persistence at 1–12 MONTH lookbacks — the stated sweep sits at the fast end of that range. If out-of-sample performance is still IMPROVING at N_entry=55 (the sweep boundary), do NOT extend the sweep in this session; record the boundary gradient in the report and flag "extend N_entry toward {100, 150, 250} in a follow-up session" as a recommendation. Any extension is a new trial series with its own multiplicity accounting.
- Multiplicity: count every parameter combination and filter variant evaluated; report deflated Sharpe alongside raw Sharpe.
- **Signal-vs-sizing ablation (mandatory, run once on the accepted baseline):** re-run the baseline with IDENTICAL triggers but constant fixed-fractional sizing instead of inverse-volatility sizing, and report the two equity curves and metric sets side by side. Rationale: published critique (Kim-Tse-Wald) found much of time-series momentum's measured performance comes from the volatility-scaling overlay rather than the entry signal. Attributing our performance between "signal" and "sizing" is a required decomposition, not optional — if the overlay dominates, that is a finding about what our edge actually is, and it must be stated plainly in the report. Two trials, negligible multiplicity cost.
- Benchmark: buy-and-hold BTC and ETH over the same period with the same cost model.
- Register every trial in TrialRegistry with hashed config per the existing scheme.
- Unit tests for: no look-ahead in the extremum calculation (property test — perturbing future bars must not change today's signal), hysteresis correctness (entry and exit thresholds never chatter on a synthetic oscillating series), and cost application. Golden-master test on a fixed fixture once baseline behavior is accepted.

## Per-trade diagnostics to log
- MFE / MAE (max favorable/adverse excursion) per trade
- Time-in-trade distribution; time-to-stop-out for losers
- Capture ratio: fraction of instrument upside captured vs fraction of drawdown avoided
- Whipsaw rate: trades stopped out within 3 bars of entry, as % of all trades
- Round-trip cost as % of gross P&L, per trial

## Report
Write results to `docs/results/BREAKOUT_RESULTS.md` (NOT the repository root — `tests/unit/test_results_docs_at_root.py` forbids a results document there): baseline vs each filter increment, maker vs taker cost scenarios, plateau surface (including the sweep-edge gradient note if performance rises at the boundary), the signal-vs-sizing ablation with an explicit attribution verdict, deflated Sharpe, benchmark comparison, and a candid verdict on whether this survives costs at the maker tier. Result-corrupting issues (look-ahead, fill semantics) take priority over performance tuning — if you find any, stop and report before continuing.

## Explicitly out of scope
Shorting, intraday bars, crypto perps/derivatives, parameter optimization beyond the stated sweep, and any modification to ground-truth documents.
