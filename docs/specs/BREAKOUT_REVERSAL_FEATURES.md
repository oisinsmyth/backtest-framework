# BREAKOUT_REVERSAL_FEATURES.md — Companion to BREAKOUT_STRATEGY_PROMPT.md

## Purpose
Defines candidate features that discriminate genuine breakouts from exhaustion prints (tops), and the protocol for testing them WITHOUT adding multiplicity debt. Read BREAKOUT_STRATEGY_PROMPT.md first; this doc extends its diagnostics section. Nothing here changes the baseline strategy. Do not implement any of these as live filters in the first pass.

## Core protocol — features, not filters
1. Log every feature below **per trade** in the existing per-trade diagnostics. Logging is free of multiplicity cost.
2. After the baseline walk-forward run, regress/rank trade outcomes (MFE, MAE, capture ratio, whipsaw flag) against these features across the trade population. Simple approaches only: outcome by feature quintile, monotonicity check, in-train vs out-of-sample stability.
3. **Promotion criteria** — a feature becomes a candidate live filter ONLY if it shows (a) a monotonic relationship with outcomes, (b) stability across walk-forward windows, (c) a plateau over its own threshold (no knife-edge cutoffs). Promotions are a separate, later session with their own multiplicity accounting in TrialRegistry.
4. Exception: the two exit-side signatures (E1, E2 below) may be implemented immediately as toggleable exit bricks, tested one at a time on top of the accepted baseline, because they modify exits rather than adding entry-filter dimensions.

## At-trigger features (log at entry)

**F1 — Extension at trigger.** (close − SMA(50)) / ATR(20) at the trigger bar. Hypothesis: high values (≥ ~3) = late-stage breakout, worse forward outcomes; low values near the base = early-stage. Predicted strongest survivor. Related to the existing volatility-contraction precondition but continuous, not binary.

**F2 — Trigger volume ratio.** Trigger-bar volume / 20-day average volume. Hypothesis: relationship is a BAND, not a floor — <1.0 fails quietly (no participation), >~5 is climax/distribution, healthy zone roughly 1.5–3×. Test as quintiles, expect an interior optimum. If confirmed, the volume filter in the main prompt should become a band, not a threshold.

**F3 — Close location value (intrabar rejection).** (close − low) / (high − low) on the trigger bar. Hypothesis: CLV < 0.3 (new high but close in bottom third, long upper wick) = level probed and sold, worse outcomes.

**F4 — Cross-sectional breadth.** Fraction of the instrument universe (BTC, ETH, extend when more instruments are added) above their own 20-day high or 50-day SMA at trigger time. Hypothesis: solo breakouts against flat/negative breadth underperform confirmed market-wide impulses. Low power with only 2 instruments — log it now, expect it to become informative only when the universe grows. Flag this limitation in the report.

**F5 — Leverage decomposition (crypto-native; requires derivatives data — see Data note).**
- ΔOI/Δprice over the trigger bar and prior 3 bars (open interest change per unit price change)
- Funding rate percentile vs trailing 90 days at trigger
Hypothesis: OI spiking WITH the breakout + funding in a high percentile = leverage-driven, crowded-long fuel for a squeeze, worse outcomes. Flat/declining OI + positive spot premium = spot-driven, better outcomes. This is the most differentiated feature in the set; prioritize getting the data plumbing right over sophistication of the metric.

**F6 — Known-flow window proximity (crypto-native calendar feature; shares F5's data plumbing).** Distance in hours from the trigger bar to (a) the next Deribit BTC/ETH options expiry (monthly/quarterly, 08:00 UTC) and (b) the nearest perp funding timestamp (every 8h). Rationale (from disclosed-strategy research): derivatives positioning dwarfs the underlying and concentrates mechanical flow at known times — the retail-scale use is not trading the flow but measuring whether triggers that fire into known-flow windows have worse follow-through (flow-driven false impulse) than triggers in quiet windows. Log-only; same promotion criteria as all features. If the expiry calendar plumbing is not built, log funding-timestamp proximity alone (computable from the bar clock with zero data dependencies) and stub the expiry component.

## Post-trigger exit signatures (may be implemented as exit bricks per protocol §4)

**E1 — Failed-breakout re-entry (highest priority).** Price closes back INSIDE the entry channel (below the N_entry-day high that triggered entry) within k bars of entry, k ∈ {2, 3}. Action when enabled: immediate exit, overriding the N_exit trailing stop. Rationale: trapped-longs-overhead is the classic reversal setup; we cannot short it, but we must not sit in it. This deepens the hysteresis asymmetry deliberately.

**E2 — Time-stop.** Position has not achieved MFE ≥ 1 ATR within n bars of entry, n ∈ {5, 7}. Action when enabled: exit flat; strategy may re-enter on a fresh trigger. Rationale: genuine breakouts work quickly; stagnation is information. Validate n against the baseline's own MFE-vs-time distribution before choosing values — do not tune n beyond the two stated candidates.

**E3 — Impulse decay (log only, do NOT implement).** Declining bar range and volume over consecutive post-entry bars while price grinds marginally higher. Definition is fuzzy; log range/volume trajectories per trade so it can be studied, but no exit rule in this phase.

## Data note
F5 requires perpetual futures open interest and funding rates (read-only market data — we do not trade derivatives; FCA retail ban applies to trading, not reading). Verified free sources (Aug 2026 research): exchange-native APIs — Binance `/fapi/v1/fundingRate` (USDT-margined; history to ~2019–2020) and `/dapi/v1/fundingRate` (coin-margined), Bybit `/v5/market/funding/history` and `/v5/market/open-interest`; OKX and Deribit have equivalents. Prefer native per-venue APIs (authoritative, free); Coinglass free tier only for cross-venue aggregation. If the data layer lacks the plumbing, implement an honest stub with a committed interface per the existing stub convention, log F5 as unavailable, and flag it in the report rather than silently omitting it. Do not block the baseline run on this.

## Reporting
Extend `docs/results/BREAKOUT_RESULTS.md` (NOT the repository root — `tests/unit/test_results_docs_at_root.py` forbids a results document there) with a "Feature analysis" section: outcome-by-quintile tables per feature, monotonicity/stability verdicts, and an explicit ranked shortlist of features meeting promotion criteria. State clearly which hypotheses were falsified — a clean negative result is a valid and reportable outcome.

## Priors to test against (from design discussion, not evidence)
Predicted survivors: F1 (extension), E1 (failed-breakout re-entry). Most valuable if confirmed: F5 (leverage decomposition). Predicted weak at current universe size: F4. F6 (known-flow proximity): weak prior either way — genuinely open. These priors are recorded so the analysis can confirm or embarrass them — do not let them bias threshold choices.

## External calibration note (from disclosed-strategy research, Aug 2026)
The published systematic-CTA literature (Moskowitz-Ooi-Pedersen TSMOM; Carver ex-AHL) independently validates this family's core structure — trend/breakout signals, vol-targeted sizing, modular forecast→position→vol-target separation, realistic net Sharpe ≤1.0. Two consequences carried into the main prompt: the N_entry sweep-edge rule (published persistence runs 1–12 months; our sweep is at the fast end) and the mandatory signal-vs-sizing ablation (Kim-Tse-Wald: vol-scaling may drive much of measured TSMOM performance). Expectations for this strategy should be anchored to Sharpe ≤1.0 net — a materially higher backtest result is a red flag for overfitting or a cost-model gap, not a celebration.
