# Deposit programme — infrastructure and research tracker

*The six pre-registrations that landed in `docs/internal/User-Doc-Deposit/` on 2026-09-21
(`SETTLEMENT_FLOW_LEDGER_PREREG` v1.9, `INDEX_REWEIGHT_FLOW_PREREG`, `LETF_CLOSE_FLOW_PREREG`,
`SHOCK_CLASSIFIER_PREREG`, `OPENING_AGENT_STATE_PREREG`, `ARCHITECTURE_OVERVIEW`), split into what
has to exist before a hypothesis can be scored and what produces a verdict. The split was written
2026-09-21; the status table is updated as rounds land. Append, do not rewrite the split.*

Infrastructure is anything that has to exist before a hypothesis can be scored: data, recorders,
guards, shared models. Research is anything that produces a verdict. Legend for the split as
written: ✓ existed in the repo or on disk on 2026-09-21, ◐ partial or vault-period only, ✗ missing.

## Status of the shared list

| # | item | built | record(s) | round |
|---|---|---|---|---|
| 1 | Forward data recorder | built, verified, untracked; **host (Q17) not built**; 7 of 16 jobs `ready`, 9 `needs_source`/`needs_key` | D608 | 3 |
| 2 | Vault guard | helpers built; **loader chokepoint not built; seal date not reconciled (principal's decision)** | D594 (`SealedWindow`, `filter_before`, `open_once`, `refuse_without_word`) | 2 |
| 3 | Programme registry and trial counter | built | D592 | 2 |
| 4 | Fill model | built | D587 | 1 |
| 5 | CostStack values per micro | built (2× variant is a coefficient on the same table) | D591 | 2 |
| 6 | Square-root impact + depth variant | built, verified, untracked: `FuturesSqrtImpact` (Y = 0.7), `depth_scaled`, params on 36 roots in three lines, and the first MBO reader — `fut_book_depth_1m` (65,688 minute rows, 8 roots, 21 days of 2026-08/09, **inside the vault window**) | D604 | 3 |
| 7 | Validation harness (leave-one-year-out) | built | D593 (`folds.py`) | 2 |
| 8 | Session calendar + event flags | built | D589 | 1 |
| 9 | Sourced economic calendar | built | D585 | 1 |
| 10 | Settlement window table | built | D586 | 1 |
| 11 | Power module | built | D588 | 1 |
| 12 | Look-ahead defences | built | D593 (`lookahead.py`) | 2 |
| 13 | Frozen-protocol guard | built | D594 | 2 |
| 14 | Prop-constraint simulator | built | D590 | 2 |
| 15 | Track 3 logging | built, verified, untracked (log schema, shortfall, latency, 50-trade review, trial counter); **automation for the 14:30 UK open NOT built — deposit O-Q3 open**; no trade exists | D605 | 3 |
| 16 | Episode / shared-period checks, haircut | built | D592 (`episodes.py`) | 2 |
| 16 | Error-budget tooling | built, verified, untracked: `fit.py` (OLS bit-identical to D365, log loss, 11-feature budget, retention check) and `error_budget.py` (leave-one-term-out, `StageOrder`); no `ERROR_BUDGET.md` committed, no study has run | D606 | 3 |
| 17 | Unit-test crosswalk (146 numbered tests: ledger 71, index 28, opening 25, shock 13, LETF 9 — the counts below were permuted when the split was written) | built, verified, untracked: `data/deposit_test_map.json` + `docs/results/DEPOSIT_TEST_MAP.md`; 43 of 146 claimed (29.5%) after round 3 (28 before), LETF 0 of 9 | D607 | 3 |

Commits: round 1 `89feba9` (D585–D589), round 2 `c192908` (D590–D594). Round 3 uncommitted at
the time of writing. Per-document infrastructure and every research item below: **nothing built,
nothing run.** The vault window (2025-03-01 → 2026-09-18) versus this repo's 2024-01-01 futures
holdout is unreconciled; the free Databento refetch window closes ~2026-10-11.

---

## The split as written, 2026-09-21

### Shared infrastructure (used by two or more docs)

1. **Forward data recorder** (ledger 13A.3). Raw responses saved unmodified, never overwritten,
   `fetched_at` on every record, gap log, always-on host (Q17). Every doc adds jobs to it. ✗
2. **Vault guard.** Loader refuses 2025-03-01 to 2026-09-18 unless a frozen model and one-shot open
   flag exist. Needs the seal date reconciled with the repo's 2024-01 futures holdout first. ✗
3. **Programme registry and trial counter.** `PROGRAMME_REGISTRY.md` with α slots, a counter
   summing every doc's `trials.csv`, programme-level DSR. Per-doc trial log and DSR ✓
   (`registry/trial_registry.py`, `validation/dsr.py`); the cross-doc layer ✗.
4. **Fill model.** Fill at t0+1 plus one tick, stress fill at the worst of t0+1 to t0+5, intra-bar
   pessimism, passive-limit diagnostic. ✗ as a shared component.
5. **CostStack values per micro** (MNQ, MES, MCL, MGC, NG and CL vehicles, the index roots without
   micros) and the 2× variant. Framework ✓ (`costs/stack.py`); values partly ✓ (D527's $4.21 MNQ
   round trip), rest ✗.
6. **Square-root impact model**, Y = 0.7 fixed, plus the depth-scaled variant from order-book data.
   Functional form ✓ (D66); depth variant ✗ and needs MBO, which is one month deep ◐.
7. **Validation harness.** Walk-forward 252/63 ✓ (`validation/walk_forward.py`), leave-one-year-out
   ✗, Monte Carlo and tearsheet ✓.
8. **Session calendar** with early closes, holidays, DST, front-by-volume roll days, and event flags
   (FOMC, CPI, payrolls, quad witching, index rebalance, month and quarter end, EIA reports). Rolls
   ✓ (`fut_index_rolls`), the rest ✗.
9. **Sourced economic calendar** `data/calendar/events.csv` from BLS, Fed and EIA archives. ✗ except
   EIA raw files.
10. **Settlement window table** per product with effective dates. ✗
11. **Power module.** Design-effect n_eff, SE, MDE, `POWER.md` and `TRACK_MAP.md` per doc,
    underpowered routing. ✗
12. **Look-ahead defences.** Static no-future-data check, leak canary, labels-never-features check,
    one-bar-delay rerun. ✗
13. **Frozen-protocol guard** that refuses to run when parameters differ from `FROZEN_<stage>.json`. ✗
14. **Prop-constraint simulator** (daily loss, trailing drawdown on open equity, flatten deadline).
    Hurdle P is defined in R11; the simulator ✗.
15. **Track 3 logging.** Implementation shortfall, signal-to-fill latency, the 50-trade cost review,
    automated execution for a 14:30 UK open. ✗
16. **Episode and shared-period checks**, 50% haircut, error-budget tooling (leave-one-term-out
    out-of-sample error). ✗
17. **Unit-test suites:** 9, 13, 25, 28 and 71 tests across the five pre-registrations.

### Per-document infrastructure

**Settlement ledger**
- Point-in-time fund panel for BOIL, KOLD, UCO, SCO, UNG, USO: NAV, shares, holdings by contract
  month, futures versus swap split, `published_at`. ✗
- Fund facts in `SOURCES.md`: creation cut-offs and lag, TAS usage, roll schedules, NAV strike
  basis. ✗
- P9 products (BetaPro, WisdomTree): NAV, units, effective leverage, FX, restrike terms. ✗
- NG and CL 1-minute bars for all held months ✓; trades with aggressor side ◐ (vault only); TAS
  instrument symbology to check in the definition file ◐.
- ETF NBBO 1-minute quotes and trades, official IIV for validation. ✗ (no equities feed)
- Attention data: GDELT, Wikipedia pageviews, optional social archive, frozen and hashed
  `QUERIES.md`. ✗
- CFTC disaggregated COT ✓ (raw on disk), swap dissemination records ✗, NG and CL options open
  interest ◐ (statistics schema held, not built), MBO ◐.
- Derived pipelines: iNAV computation, roll reconstruction with holdings validation, restrike
  detector, the Kalman update step, staged parameter estimation.

**Index reweight**
- BCOM target weights, tracking AUM and announcement dates per year 2016 to 2027; GSCI
  equivalents. ✗
- Methodology facts: execution days and fractions, designated contract schedule, determination
  date, holiday rules. ✗
- Daily settlements for all BCOM components: CME ✓ (settle strip fixture), ICE and LME ✗.
- 1-minute bars for the ~15 CME contracts ✓; signed window flow for calibration ◐ (vault only).
- CIT supplement and COT ✓ raw; MBO ◐.
- Derived: sub-index reconstruction and drift tracker, contract-count flow, `FROZEN_2027.json`
  before late October.

**LETF close flow**
- Point-in-time AUM for ten index LETFs (NAV × shares, prior close) with per-ticker sources. ✗
- NQ and ES 1-minute bars ✓, front-by-volume roll ✓, NQ-equivalent volume series (NQ + MNQ/10) ✗
  trivial.
- Derived: flow, contract conversion, normalised flow and impact, activation gate.

**Shock classifier**
- 1-minute bars for four traded roots and their peers (ES, NQ, RTY, ZN, 6J, BZ, HO, RB, SI, 6E) ✓.
- Trades with aggressor side for the traded roots ◐ (vault only, so the flow-flip exit is
  forward-only unless bought).
- Roll-day exclusion list ✓ derivable; economic calendar ✗ (shared item 9).
- Derived: time-of-day σ, shock detector with cooldown, rolling peer betas, confirmation ratio,
  class pipeline.

**Opening agent-state**
- ES and NQ 1-minute full Globex session ✓; trades with aggressor side ◐.
- SPY and QQQ 1-minute bars for the index-arb agent. ✗
- ES options open interest by strike and settlements ✓ (D581 fixture, to 2023 end); NQ options ✗.
- Economic calendar ✗ (shared item 9).
- Derived: label pipeline, seven agent pressures with 250-session standardisation, alignment
  summary, multinomial logit with the 11-feature budget guard, checkpoint progression, policy and
  three baselines.

**Architecture overview:** no infrastructure of its own. It records the shared list above and the
double-counting guards between ledger P8a/P8b and the index model.

### Research (verdict-producing items)

**Settlement ledger**
- Gate 0b: does self-computed iNAV match official NAV within 5 bp on 95% of days.
- H1 flow prediction at Stage A: does P1 predict signed window flow. This is the premise the whole
  doc stacks on.
- H2 price effect, H3 dose-response, H4 timing, H5 time placebo and day shuffle, H6 AUM scaling,
  H7 sizing.
- Stage retention decisions B through I (update step, creations baseline, premium and hedging
  split, attention, TAS, netting, rolls, non-US ETPs, depth impact, large-lot split).
- Diagnostics H8 to H15: where creation flow lands, stress and impact, crowding reversal, attention
  lead-lag, restrikes, roll flow versus calendar spreads, depth impact, swap timing.
- Parameter recovery and decision-relevance tests for p, h, n, n9; vault confirmation; Track 3
  efficacy or consistency.

**Index reweight**
- Gate R0: reconstructed sub-indices match published returns within 5 bp a month.
- Gate C0: κ > 0 on monthly-roll flow, price slope against predicted impact.
- H-R1 execution days, H-R2 reversal, H-R3 pre-positioning (descriptive and traded), H-R4 depth
  impact.
- Dose-response per stage, date placebo (business days 12 to 16), label shuffle, headline-only
  comparison.
- Yearly sign test (9 of 10, then 9 of 11), calibration ratio against the monthly mechanism, CIT κ
  consistency flag.
- The January 2027 forward event as vote, consistency test and calibration point.

**LETF close flow**
- Gate 0: AUM panel passes gap, reconciliation and spot checks (data QA, but it is the doc's
  declared stop).
- H1 primary effect on active days across six cells, H2 dose-response across quintiles, H3 AUM
  scaling by year, H4 11:00 time placebo, H5 overnight reversal diagnostic.
- Hold sweep, event-day and cost robustness, walk-forward selection of τ and k, Track 3 route.

**Shock classifier**
- Shock counts per class, instrument and year (the sizing step before anything else).
- Event-study curves; H1 class divergence with both signs predicted; H2 timing after t0+5; H3 label
  permutation; H4 dose-response in C; H5 net profitability of conditional exits versus time-only
  exits.
- Robustness across z, window, thresholds, event flag, year; walk-forward exit and threshold
  selection.

**Opening agent-state**
- Label frequency report and the merge rule for rare classes.
- H-O1 classification lift at 10:00 with permutation test and calibration; H-O2 decision value
  against the baselines (after fixing the per-day "best of" wording); H-O3 progression; H-O4
  timing; H-O5 label, agent and midday placebos; H-O6 agent signatures.
- Stage retention S-A to S-I on log loss and decision value; walk-forward and leave-one-year-out;
  vault confirmation; episode and one-bar-delay checks.

**Architecture overview:** nothing. It states that it adds no hypotheses.

### Two observations on the split

The infrastructure list is far longer than the research list, and most of it is sourcing rather
than code. And the research items that can run today on held data are few: ledger H1 and H2 at
Stage A-lite once fund AUM is sourced, the LETF H1 to H4 once LETF AUM is sourced, the shock
classifier through H4 with time-only exits, the opening model through S-A and S-C to S-E, and the
index drift tracker for CME components only. Everything touching signed flow, ETF quotes, SPY,
attention or non-CME prices is forward or purchase.
