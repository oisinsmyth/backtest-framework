# TERRAIN_IMPLEMENTATION_PLAN.md — Work-package plan for TERRAIN_MODEL.md

## Status and prerequisites
Companion to TERRAIN_MODEL.md (the spec); this doc is the build plan. Phase 3 gating still applies: WP2 onward must not start until the Phase 1 long baseline is accepted. **Exception: WP0 (intraday data brick) is independently justified by execution modelling and may be built any time after the Phase 1 session.** Each work package (WP) is sized for one focused Claude Code session, ends with an acceptance gate, and must leave the repo green (all tests passing) — no WP starts while a previous WP's gate is unmet. Ground rules from DESIGN_DECISIONS.md, VERIFICATION_SCHEME.md, and the multiplicity restrictions in TERRAIN_MODEL.md apply throughout and override anything here if in conflict.

**REVISION NOTE (post data-source research, Aug 2026):** Revised in step with TERRAIN_MODEL.md. Changes: WP3 rebuilt around Coin Metrics Community anchor + self-computed URPD from Dune UTXO data (point-in-time-correct, free); WP8 redefined as a diagnostics/risk-context channel — S4 is OUT of fusion permanently; MVRV Z-score supervisory gate added to WP7's candidate list; data-immutability rule added to cross-cutting rules; priors updated (S1 lead; S3 open hypothesis); terrain is BTC-first (ETH on S1+S2 only until S3 earns extension).

## Dependency graph
```
WP0 (intraday data) ──> WP1 (S1 volume profile) ──┐
WP0 ──> WP4 (S2 anchored VWAP)                     ├──> WP2 (null-test harness, run per sensor)
WP3 (S3: CM anchor + self-computed URPD) ──────────┘
WP2-passed sensors ──> WP5 (fusion + F7/F8/F9 feature logging)
WP5 ──> WP6 (confluence analysis)          [analysis only, no code changes to strategies]
WP6 ──> WP7 (promotion: gate / exit-mod / size-mod / MVRV-Z gate bricks)
WP8 (S4 liquidation diagnostics channel) — unscheduled; feeds WP6-style analysis only, never fusion
```

---

## WP0 — Intraday OHLCV data brick
**Goal:** extend the data layer to multiple bar frequencies per instrument from exchange-native sources.
- Source: Kraken public OHLC API primary (aligns with likely live venue); Binance public API as secondary/cross-check. BTC and ETH; 1h bars as the base frequency (finer can wait).
- Deliverables: `IntradayBars` data brick behind the existing DataView interface; Parquet caching consistent with current scheme; resampling utility (1h → 4h/1d) with explicit UTC bar-boundary convention (00:00 UTC, matching Phase 1); gap/outage handling policy documented (forward-fill prohibited; gaps logged, bars flagged).
- Tests: resampled daily bars reconcile against existing yfinance dailies within tolerance (log discrepancies — exchange vs composite pricing differences are expected and worth a note in the report); property test that resampling is idempotent and boundary-stable; cache round-trip.
- **Acceptance gate:** two years of clean 1h BTC/ETH data cached; reconciliation report written; all tests green.
- Est: 1 session.

## WP1 — S1 volume profile sensor
**Goal:** first terrain sensor, on WP0 data.
- Implement the common sensor interface FIRST (this WP defines it for all sensors): `sensor(timestamp, instrument) -> density over price buckets`, computed strictly from data ≤ timestamp; normalized output; declared availability range; stub-mode flag.
- Volume-at-price histogram: rolling lookback (config: 90/180d only), bucket width in ATR units (config: 0.25/0.5 ATR only). HVN/LVN extraction as local maxima/minima above/below density quantiles.
- Tests: no-look-ahead property test (future bars must not alter current density — same pattern as Phase 1); synthetic-data test (known volume distribution in, known histogram out); normalization stability.
- **Acceptance gate:** sensor interface frozen and documented; S1 produces sane profiles on real data (spot-check plots archived); tests green.
- Est: 1 session.

## WP2 — Sensor null-test harness (the make-or-break WP)
**Goal:** reusable harness answering "does this sensor's map beat random levels?" — the step-1 validation from TERRAIN_MODEL.md.
- Implement: pseudo-level generator matched to the real map's level density; reaction statistics at levels — P(reversal within k×ATR of touch), realized-vol change near level, traversal speed through level; comparison report real-vs-random with bootstrap confidence intervals (reuse existing block-bootstrap machinery; block length per the intraday vol-clustering scale).
- Touch/reversal definitions must be mechanical and fixed before running (write them in the harness docstring; k ∈ {0.5, 1.0} ATR only).
- Run against S1. Record verdict in TERRAIN_RESULTS.md (new results doc, created by this WP).
- Tests: harness on synthetic data with planted levels (must detect them) and on pure random walk (must NOT find levels — false-positive check). The false-positive check is mandatory.
- **Acceptance gate:** harness passes both synthetic checks; S1 verdict recorded with CIs. If S1 fails its null, STOP the terrain programme and report — do not proceed to WP3+ on the theory that other sensors will save it.
- Est: 1–2 sessions.

## WP3 — S3 cost-basis sensor (anchor layer + self-computed distribution)
**Goal:** point-in-time-correct cost-basis sensor from immutable/free sources; no mutable vendor feeds.
- **WP3a — Anchor layer (fast):** Coin Metrics Community API — `CapRealUSD` (realized cap → realized price) and `CapMVRVCur`, daily, BTC (+ETH for the MVRV gate candidate only). No API key; rate limit 10 req/6s. FIRST TASK: verify these metrics are still on the free Community tier (they are being trimmed post-Talos acquisition); if retired, fall back to computing realized cap within WP3b and record the change. Cache to Parquet per existing scheme; confirm 2018+ coverage.
- **WP3b — Distribution layer (the real work):** self-compute a URPD-style histogram from raw Bitcoin UTXO data via Dune SQL (free tier, 40 req/min, small credit allowance — design queries to run monthly-snapshot batches, not per-day). Output: fraction of supply by last-moved price band, monthly or weekly snapshots, 2018+. Validate shape against free CheckOnChain URPD charts (manual spot-check, archived screenshots). Self-computation is the point: immutable by construction, no entity tagging, no restatement risk.
- STH/LTH cohort variants and vendor granular URPD (Glassnode Advanced ~$49/mo): committed PAID-UPGRADE stubs only — the trigger for paying is S3 surviving WP5, nothing else.
- BTC only. ETH extension is out of scope until S3 earns it.
- Run WP2 harness on the self-computed distribution; record verdict.
- **Acceptance gate:** anchor layer cached with source-availability note; self-computed URPD snapshots validated against CheckOnChain in shape; null verdict recorded; upgrade stubs in place.
- Est: 2 sessions (WP3a is minutes; WP3b's Dune SQL and credit budgeting is the bulk; cap at 2 and descope to anchor-layer-only if the UTXO computation overruns — anchor-only S3 is a legitimate thin sensor, flagged as such).

## WP4 — S2 anchored VWAP sensor
**Goal:** cohort cost-basis proxies from pre-registered anchors.
- **Anchor pre-registration happens IN THIS DOC, now, before any testing:** (a) cycle low of each major bear (mechanical: lowest daily close of each drawdown >50%), (b) capitulation flushes (mechanical: daily close-to-close return below −15% on volume >3× 20d average), (c) nothing else. This list may not grow. Each anchor spawns a VWAP-from-anchor series; sensor density = mass at each anchored-VWAP level.
- Run WP2 harness; record verdict. Prior (recorded in TERRAIN_MODEL.md): marginal — a failure here is expected and fine.
- **Acceptance gate:** verdict recorded; sensor dropped from fusion if failed (weight 0, code retained).
- Est: 1 session.

## WP5 — Fusion + feature logging (F7/F8/F9)
**Goal:** equal-weight fusion of WP2-passing sensors; compute per-trigger features on EXISTING accepted trade populations.
- Implement `terrain(p)` fusion (equal weights over live sensors; three-sensor maximum — S4 is permanently out of fusion); derived quantities path_resistance (F7), wall_distance (F8), cleared_mass (F9) exactly as specified in TERRAIN_MODEL.md.
- Extend per-trade diagnostics with F7/F8/F9 + sensor-availability mask (schema must already support this per Phase 1 forward-compat; if it doesn't, fix that first and flag the gap).
- **Recompute features retroactively over the accepted Phase 1 (and Phase 2 if done) trade logs** — no strategy re-runs, pure feature annotation of existing trades. Where sensor history doesn't cover a trade, mark unavailable, never impute.
- Quintile analysis: trade outcomes (MFE, MAE, capture ratio, whipsaw flag) by F7/F8/F9 quintile, per walk-forward window, with the promotion criteria from BREAKOUT_REVERSAL_FEATURES.md (monotonic, stable, plateau).
- **Acceptance gate:** feature-annotated trade log archived; quintile tables in TERRAIN_RESULTS.md; explicit go/no-go verdict per feature. A no-go across all three features ends the programme at analysis (a reportable negative result) — WP7 does not run.
- Est: 1–2 sessions.

## WP6 — Confluence analysis (kinematic × structural)
**Goal:** test the pre-registered predictions linking the reversal features (F1–F5, E1) to terrain structure. Analysis only — no strategy code changes.
Pre-registered hypotheses (recorded here, before data):
1. **H1:** E1 (failed-breakout) frequency is monotonically increasing in F7 (path_resistance) at trigger. This is the central mechanism test — the terrain gate and the E1 exit should be ex-ante/ex-post views of the same phenomenon.
2. **H2:** F1 (extension) and F8 (wall_distance) are substantially correlated, and F8 dominates F1 in outcome prediction where terrain data exists (F1 is the terrain-free proxy).
3. **H3:** Kinematic reversal features (F3 rejection close, F5 OI/funding if available) predict outcomes materially better conditioned on low F8 (near a wall) than unconditionally. Test as interaction: outcomes vs feature × wall-proximity bucket.
4. **H4 (capitulation zone, S3-only form — weakened post-research):** the capitulation-reversal zone is defined as "inside the deep cost-basis mass band" (self-computed URPD dense region below current price; LTH band if cohort data is later purchased). The original "below the consumed liquidation cluster" clause is DROPPED with S4's demotion — liquidation data may appear in the descriptive check via the WP8 diagnostics channel but carries no definitional weight. Log against historical bear lows as a descriptive check only — no trading conclusions drawn. This is honestly the weakest hypothesis; say so in the report.
- Method: contingency/quintile tables and interaction splits on the WP5-annotated trade log; bootstrap CIs; per-window stability. No new parameters, no threshold search — buckets are terciles, fixed.
- **Acceptance gate:** verdict per hypothesis in TERRAIN_RESULTS.md, including falsifications stated plainly. H1's verdict determines WP7 priority order (gate first if H1 holds; exit-modulation first if only H3 holds).
- Est: 1 session.

## WP7 — Promotion to live bricks
**Goal:** implement only what WP5/WP6 justified, one increment at a time on top of the accepted baseline.
- Candidate bricks, each toggleable, each a separate trial series in TrialRegistry: (1) terrain entry gate (F7 quantile threshold, {median, lower tertile} only) as a new link in the composable gate chain; (2) exit modulation (hysteresis narrowing on wall entry; fast-exit lookback from the pre-stated set); (3) size modulation (bounded [0.5×, 1.5×] conviction multiplier); (4) **MVRV Z-score supervisory gate** — NOT a terrain brick; a gate-chain link beside the 200-day SMA gate, one threshold, data from WP3a. Skeptical prior recorded: its one supportive study (Grobys et al. 2026) is 3 round-trips, cost-free, single-path — the increment test here is the first honest evaluation with costs and walk-forward. Requires only WP3a, not WP5 — may be tested as soon as the anchor layer exists and the Phase 1 baseline is accepted.
- Order determined by WP6 (H1 → gate first). **Expectation set post-research:** exit modulation is the most likely increment to survive — "where a move stalls" is a more robust claim than entry-gate alpha; do not force the gate through if counterfactuals show it filtering winners. Each increment: walk-forward on the standard harness, mandatory gate counterfactuals (rejected triggers + hypothetical outcomes), marginal-contribution report vs the previous increment, deflated Sharpe with cumulative trial count across the whole terrain programme.
- **Acceptance gate per increment:** out-of-sample improvement on the primary metrics AND counterfactual cost of missed winners reported. Keep or revert explicitly; no increment stays in "provisional" state.
- Est: 1 session per increment (max 3).

## WP8 — S4 liquidation diagnostics channel (unscheduled; NEVER fusion)
**Goal:** deterministic liquidation-structure data as risk context and confluence-analysis input. S4 does not gate, size, or shape `terrain(p)` under any outcome — this is a permanent decision (basis: CEX heatmaps are models of positions, not observations; ~86% of directional perp leverage is CEX so the deterministic DeFi map covers a minority slice; the one rigorous cascade study found early-warning signals event-heterogeneous).
- **DeFi deterministic layer (the only build):** DefiLlama liquidations API + Aave/Compound/Sky contract state via Dune. Exact liquidation levels, revision-free, free. Log per-trade "DeFi liquidation density in trade direction" as a diagnostic feature for WP6-style analysis; usable for short-side stop-placement sanity checks.
- **CEX heatmaps (Coinglass):** monitoring-only at most; no backtest role; may be omitted entirely.
- Est: 1 session, unscheduled; never blocks anything.

---

## Cross-cutting rules
- **TERRAIN_RESULTS.md** is the single results ledger for the programme: sensor verdicts, quintile tables, hypothesis verdicts, increment reports. Every WP appends; nothing is overwritten (append-only, dated sections).
- **Multiplicity ledger:** a running count of every parameter combination, sensor variant, and hypothesis tested across all WPs, maintained in TERRAIN_RESULTS.md, feeding the deflated Sharpe at WP7. Retired/failed items still count.
- **Data immutability (added post-research):** sensor inputs must be self-computed from immutable raw data or point-in-time vendor series. Mutable entity-tagged metrics (exchange netflows, whale/miner tags) are prohibited as sensor inputs; if ever used diagnostically, lag them and haircut conclusions, flagged in TERRAIN_RESULTS.md. Verify free-tier availability of any vendor endpoint at session start — free tiers are shrinking (Coin Metrics Community trimming, Glassnode free gutted).
- **Stop conditions:** S1 failing WP2 stops the programme; all features failing WP5 stops it at analysis. Both are reportable negative results, written up with the same care as positives. S3's null verdict is a genuine open question (zero independent validation exists for the thin-zone claim) — a clean S3 failure with S1 passing yields an S1-only terrain, which is an acceptable end state.
- **No scope additions mid-WP.** New ideas go into a parking-lot section of TERRAIN_RESULTS.md for triage between WPs.
- **Session hygiene:** each WP session starts by reading this doc, TERRAIN_MODEL.md, and the current TERRAIN_RESULTS.md; ends by updating TERRAIN_RESULTS.md and the WP checklist below.

## WP checklist (update on completion)
- [x] WP0 intraday data brick — delivered earlier by D160/D161/D165, not as a terrain WP
- [x] WP1 S1 volume profile + sensor interface — D189
- [x] WP2 null-test harness + S1 verdict — **S1 FAILED**, D189
- [x] WP2 re-run on exchange-native 15m volume — **S1 FAILED AGAIN**, D194; S1 closed at any resolution by D194's permanent stop
- [ ] ~~WP3a Coin Metrics anchor layer~~ — not run, stop condition
- [ ] ~~WP3b self-computed URPD (Dune) + verdict~~ — not run, stop condition
- [ ] ~~WP4 S2 anchored VWAP + verdict~~ — not run, stop condition
- [ ] ~~WP5 fusion + F7/F8/F9 + quintile go/no-go~~ — not run, stop condition
- [ ] ~~WP6 confluence analysis~~ — not run, stop condition
- [ ] ~~WP7 increments~~ — not run, stop condition
- [ ] ~~WP8 S4 diagnostics channel~~ — not run, stop condition

**PROGRAMME STOPPED at WP2 on 2026-08-22**, by this document's own condition: *"If S1 fails
its null, STOP the terrain programme and report."* S1's volume-profile levels are
indistinguishable from levels scattered at random — 16 of 16 configurations fail, and on
P(reversal | touch) the real levels sit BELOW the null median on both symbols. Verdict and
tables in `TERRAIN_RESULTS.md`; reasoning in
`docs/decisions/D189-the-s1-terrain-sensor-and-its-null.md`. The harness is retained: it
passed both synthetic controls and can test any future sensor.

**RE-OPENED ONCE AND CLOSED FOR GOOD on 2026-08-23 (D194).** D189 tested a 90-to-180-DAY
volume profile built from daily bars — a construction nobody trades — and named the gap in
its own losing result: a map from real intraday exchange volume is a different
measurement. D190–D193 built that data. D194 re-ran S1 on exchange-native 15m volume with
every window calendar-matched to D189, so bar resolution was the only variable.

**S1 failed again, on all three pre-registered conditions.** The primary configuration
reached the 89.6th percentile on BTC (p = 0.106) and the 66.4th on ETH (p = 0.337). The
sign did flip — D189's real levels sat below their null, D194's sit above it on both
symbols — so intraday attribution produces a real, correctly-signed effect. It is 6.6x and
19x below the pre-registered effect-size floor.

Three BTC configurations DID clear p <= 0.05, one at **p = 0.0080, the 99.4th percentile,
on 30,187 touches** — which is what a discovery looks like. All were 4.5x to 7.1x below
the floor, and none was on ETH, so two independent pre-registered guards killed the same
cell. That is the run's most useful output.

A span-matched daily control on the overlapping years rules out the era: still
indistinguishable from random (BTC 22.4th percentile, ETH 51.2nd). The bucket-span census
rules out degeneracy: median span 4.0 buckets, so the map is a genuine volume profile and
not a close-price histogram.

**S1 is closed at any resolution**, by D194's own pre-registered permanent stop: the
resolution ladder is infinite, every rung is a fresh look at one hypothesis, and two rungs
two orders of magnitude apart both returning an effect ~20x too small to act on means the
hypothesis is not resolution-limited. No 5m, 1m or tick variant will be tried.

**Cumulative multiplicity: 147 looks on one hypothesis** (48 from D189, 96 from D194, 3
for the control). WP3–WP8 remain unrun.
