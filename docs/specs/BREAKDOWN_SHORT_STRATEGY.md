# BREAKDOWN_SHORT_STRATEGY.md — Addon to BREAKOUT_STRATEGY_PROMPT.md

## Purpose and status
Specifies the short side of the breakout family: a regime-gated breakdown trend-following strategy ("crisis alpha" sleeve). This is a **Phase 2 addon** — do NOT implement until the long-side baseline from BREAKOUT_STRATEGY_PROMPT.md has been run, validated, and its accepted parameters recorded in `docs/results/BREAKOUT_RESULTS.md` (NOT the repository root — `tests/unit/test_results_docs_at_root.py` forbids a results document there). This doc exists so the design intent is preserved and so the long-side session can make forward-compatible choices (see "Forward-compatibility requirements" below, which DO apply immediately).

Read first: BREAKOUT_STRATEGY_PROMPT.md, BREAKOUT_REVERSAL_FEATURES.md, DESIGN_DECISIONS.md, VERIFICATION_SCHEME.md.

## Strategy concept
Extend the long-flat state machine to long-flat-short. The short book activates ONLY in the bear regime (price below 200-day SMA — the inverse of the long book's higher-timeframe gate), i.e. it wakes when the long book goes dormant. Rationale: crypto downtrends are driven by forced selling (liquidation cascades — mechanical positive feedback, no discretion in the participants), making breakdown momentum at least as mechanistic as breakout momentum. Ensemble purpose: near-zero or negative full-cycle correlation with the long book — this is the complementary-payoff component in the portfolio Sharpe math.

## Specification
- **Entry:** close(t) < min(low over bars t−N_entry … t−1), computed on completed bars only, same look-ahead discipline as the long side. Active only when close < SMA(200).
- **Exit:** close(t) > max(high over bars t−N_exit … t−1) — fast trailing, hysteresis preserved.
- **Tail discipline (NON-OPTIONAL, implement before any backtest run):** hard per-trade stop above the entry channel high; per-trade position cap. Short expectancy is only calculable with the squeeze tail truncated by construction. No configuration may disable these.
- **Sizing:** inverse-volatility, same brick as the long side. Note: vol expands in crashes, so vol-targeting automatically de-sizes as the move matures — this is intended behavior, do not "fix" it.
- **Parameters are NOT mirrored from the long side.** Documented asymmetries: bear legs are faster and shorter (expect shorter N_entry to dominate, e.g. sweep {10, 20, 30, 40}); bear rallies/short squeezes are violent (expect shorter N_exit, e.g. {3, 5, 10}, and tighter stops); time-stop matters more (a short not in profit within ~3–5 bars carries squeeze risk — implement as a toggleable exit brick, values {3, 5}). Run the short side's own plateau sweep, counted SEPARATELY for multiplicity. Different optimal parameters from the long side is the expected finding, not a red flag.

## Validation requirements
- Walk-forward per the existing harness. The sample MUST include the 2018 and 2022 bear markets — if the current data range excludes them, extending the data range is a prerequisite, not optional.
- **Null:** exposure-matched random-SHORT-entry strategies (same time-in-market fraction and holding-period distribution, randomized entries), ~1,000 draws. Percentile vs this null is the primary verdict.
- **Regime-sliced report is the headline table:** bull / bear / chop (ex-post labels, e.g. SMA(200) state). Success criteria: strongly profitable in bear regimes; flat-to-small-loss in bull regimes (the regime gate should keep it mostly inactive there); acceptable chop bleed. A short book that is ~flat through the bull sample and profitable through 2018/2022 is a strong positive result — evaluate it on the regime table, not the headline full-sample Sharpe.
- **Correlation with the long book:** compute long-vs-short strategy return correlation over the full cycle INCLUDING flat periods, per window. Target ρ ≤ ~0.2. Report combined long+short portfolio metrics (equal vol-weight) vs each component solo — the ensemble improvement is a primary result.
- Jobson–Korkie/Memmel test and deflated Sharpe per the existing analytics conventions. Register all trials in TrialRegistry.

## Diagnostics (in addition to the standard per-trade set)
- Squeeze events: count and P&L impact of adverse excursions > 2 ATR against open shorts
- Stop-hit rate and time-to-stop distribution (compare against long side)
- Regime-gate effectiveness: trades that would have triggered outside the gate, and their hypothetical outcomes (log-only counterfactual)
- Funding-context tag per trade if F5 data plumbing exists (shorting into negative-funding periods costs carry in live perp expression — tag it now for later cost modeling)

## Live tradability constraints (context, not implementation)
Crypto short expression is backtest + shadow-signals only (FCA retail crypto-derivatives ban; no retail spot margin). Short entry signals additionally feed the long book as exit/avoid vetoes (timestamped shadow record). The one legal live expression at current capital is equity-INDEX breakdown via UK spread betting (multi-day holds, gross edge must clear ~1% spread+financing hurdle) — out of scope for this doc; flagged for a future sibling spec.

## Forward-compatibility requirements for the LONG-side session (apply now)
1. The strategy brick must implement a position-state enum supporting {long, flat, short} even though Phase 1 only emits {long, flat}. No boolean in/out flags.
2. Entry/exit channel logic must be sign-parameterizable (direction as config), not duplicated code.
3. The higher-timeframe gate must be a standalone, direction-aware brick (above-SMA gates longs; its inverse will gate shorts).
4. The random-entry null generator must accept a direction parameter.
5. Data layer: confirm the sample can extend to cover 2018; if yfinance coverage is insufficient for that range, flag it in `docs/results/BREAKOUT_RESULTS.md` as a Phase 2 blocker.

## Out of scope
Live short execution in any venue; funding-carry (delta-neutral) strategies; attention-fade and token-unlock short families (separate SetupRegistry entries, separate future specs); any parameter tuning beyond the stated sweeps.
