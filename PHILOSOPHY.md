# Design Philosophy

This is the generative layer above [`docs/RULES.md`](docs/RULES.md) and
[`docs/decisions/`](docs/decisions/README.md). Rules are specific, binding constraints;
decisions are specific, dated choices. This document is neither — it's the small set of
values that, applied consistently, produced the first 49 decisions — and, unchanged, the
573 numbered decisions the directory now holds (D1 through D621; a pre-registration and
its result share a number). When a new situation isn't covered by an existing rule or decision,
this is what to reason from.

Extracted from the actual pattern across `DESIGN_DECISIONS.md`, not written from a
blank page — every principle below is backed by decisions that instantiate it. If a
future decision contradicts a principle here, either the decision is wrong or the
principle needs amending in writing — it doesn't just get silently overridden.

## The one-sentence version

**Build something you can't lie to yourself with.**

Every pillar below is a different angle on that. A backtester is uniquely easy to fool
yourself with — it will happily report a beautiful Sharpe ratio built on look-ahead bias,
survivorship bias, an undercounted trial history, or a bug you never noticed. The entire
point of the framework is to make self-deception structurally harder than honesty.

---

## Pillar 1 — Trust is structural, not agreed-upon

If something must never happen, make it *impossible*, not merely against the rules.
An honor system fails exactly once, silently, usually at 6:50am.

- Physically enforce invariants in code rather than in comments or conventions —
  the look-ahead guard doesn't ask strategies nicely not to peek at future bars, it makes
  the future bars unreachable ([D32](docs/decisions/D32-structural-look-ahead-guard-strategies-receive.md)).
  The trial registry doesn't ask you not to overwrite a trial, it refuses
  ([D20](docs/decisions/D20-trialregistry-every-backtest-run-appends-config.md)).
- **No false affordances.** An enum value, config knob, or interface method that doesn't
  actually work is either implemented or deleted — never left in place implying a
  capability that isn't real
  ([D48](docs/decisions/D48-no-false-affordances-enum-values-and.md)). A stub is fine;
  a stub that looks finished is a liability.
- **Explicit over implicit, always.** RNG seeds, risk-free rate, cash/margin accounting,
  bar-alignment policy, warm-up periods, money-comparison tolerance — every one of these
  is a stated, logged, tested policy rather than an assumed default
  ([D34](docs/decisions/D34-explicit-rng-seed-policy-every-stochastic.md),
  [D49](docs/decisions/D49-sharpe-sortino-take-an-explicit-risk.md),
  [D43](docs/decisions/D43-short-sale-cash-accounting-made-explicit.md),
  [D45](docs/decisions/D45-multi-ticker-bar-alignment-policy-is.md),
  [D44](docs/decisions/D44-engine-enforces-a-warm-up-period.md),
  [D47](docs/decisions/D47-money-is-float64-with-a-stated.md)).

## Pillar 2 — Honesty over comfort

A convenient number you can't trust is worse than an ugly number, or no number at all.

- **Model the real mechanism, even when a proxy is easier to code.** Raw prices instead
  of adjusted prices for cost math, the actual IBKR commission schedule instead of flat
  bps, calendar-day carry accrual instead of per-bar, sqrt market impact instead of an
  invented constant
  ([D6](docs/decisions/D06-store-raw-prices-separate-dividends-splits.md),
  [D4](docs/decisions/D04-model-ibkr-s-actual-commission-schedule.md),
  [D33](docs/decisions/D33-bars-for-sequencing-timestamps-for-accrual.md),
  [D3](docs/decisions/D03-add-square-root-market-impact-brick.md)).
- **Distinguish genuine bugs from legitimate sensitivity knobs.** Gap-through-stop fills,
  calendar accrual, and adverse intra-bar fill ordering are simply *wrong* if done any
  other way — they get fixed outright, not exposed as configurable options. Fill
  assumptions and cost multipliers, by contrast, are legitimately uncertain — those get
  exposed and swept for comparison. A bug never gets to hide behind the word "configurable"
  ([D10](docs/decisions/D10-gap-through-stop-fills-at-the.md),
  [D42](docs/decisions/D42-intra-bar-ambiguity-convention-when-two.md) vs.
  [D8](docs/decisions/D08-cost-multiplier-sweep-harness-run-every.md),
  [D9](docs/decisions/D09-add-limit-trade-through-fill-assumption.md)).
- **Report only what the sample supports.** Tail-risk metrics on too few observations
  print "insufficient data," not a confident-looking wrong number
  ([D36](docs/decisions/D36-tail-risk-metrics-are-gated-by.md)).
- **Label blind spots and limitations in writing, not just in your head.** A deferred
  feature, a known gap, a directional strategy inside a market-neutral thesis — all get
  one honest paragraph rather than silent omission. This converts a liability into
  evidence of self-awareness
  ([D7](docs/decisions/D07-fx-handled-in-two-parts-fxconversioncost.md),
  [D38](docs/decisions/D38-sector-momentum-is-explicitly-labelled-a.md),
  [D16](docs/decisions/D16-options-implemented-as-a-well-formed.md), R3 in
  [`docs/RULES.md`](docs/RULES.md)).

## Pillar 3 — Anti-self-deception

Internal consistency isn't evidence. A framework that only checks itself against itself
can be wrong in a stable, self-confirming way forever.

- **Anchor every load-bearing result to a reference you didn't write.** Cross-engine
  reconciliation against `vectorbt`, an engine written by someone else (D41 named
  *"backtesting.py or vectorbt"*; only the second was used), commission math against published
  IBKR schedules, risk metrics against `quantstats`, DSR against the original paper's
  worked example
  ([D41](docs/decisions/D41-cross-engine-validation-run-one-identical.md), the X-tests
  throughout [`VERIFICATION_SCHEME.md`](VERIFICATION_SCHEME.md)).
- **Prove the strategy isn't fooling you with a test where it's *supposed* to fail.**
  Synthetic cointegrated pairs with zero true edge should earn ~nothing — if they
  "profit," that falsifies the whole pipeline, not just one test
  ([D23](docs/decisions/D23-synthetic-pair-null-test-generate-cointegrated.md)).
- **Overfitting and multiplicity are first-class engineering concerns, not statistical
  footnotes.** Every trial is logged before any real experimentation starts — trial count
  can't be reconstructed retroactively, so it has to be captured live. Pair selection
  and regime fitting are structurally confined to the training window, using the same
  guarded accessor as everything else, and multi-candidate selection is corrected for
  the number of candidates tried
  ([D20](docs/decisions/D20-trialregistry-every-backtest-run-appends-config.md),
  [D22](docs/decisions/D22-pair-selection-moves-inside-the-walk.md),
  [D28](docs/decisions/D28-regime-models-obey-the-same-fitting.md),
  [D29](docs/decisions/D29-pair-selection-handles-multiplicity-rank-candidate.md)).

## Pillar 4 — Composability

Real frictions and instruments are independent, swappable layers — model them that way,
not as one entangled blob.

- **Lego-brick modularity.** Cost frictions are an ordered stack of small, individually
  testable bricks, not one monolithic cost function; instruments are swappable objects
  behind a stable interface, not hard-coded ticker-string assumptions; data sources,
  allocators, and risk checks all sit behind their own stable sockets
  ([D1](docs/decisions/D01-replace-monolithic-costmodel-with-a-coststack.md),
  [D12](docs/decisions/D12-introduce-instrument-abstraction-positions-fills-reference.md),
  [D18](docs/decisions/D18-per-asset-class-data-fetchers-behind.md),
  [D31](docs/decisions/D31-allocator-is-a-bare-bones-stand.md)).
- **Components own their own semantics instead of the engine hard-coding assumptions
  about them.** Instruments carry their own trading calendar rather than the codebase
  scattering bare `/252` or `/365` constants
  ([D17](docs/decisions/D17-instruments-own-their-trading-calendar-instrument.md)).
- **Commit the shape before the cleverness, when the cleverness isn't ready.** The
  options module is a real, well-formed stub — correct contract-multiplier arithmetic, and
  the genuinely hard parts scoped out in writing rather than half-built with hidden gaps. The
  allocator socket was committed on the same principle and has since been filled:
  `ConstantSplitAllocator` (`engine/allocator.py:21`) is a working implementation behind
  the protocol, which is what the socket was for
  ([D16](docs/decisions/D16-options-implemented-as-a-well-formed.md),
  [D31](docs/decisions/D31-allocator-is-a-bare-bones-stand.md)).

## Pillar 5 — Scope discipline

Architecture work is satisfying and infinite. Research output is what gets judged, and
it's finite time. Protect the second thing from the first.

- **Research output is the product; the framework is the instrument.** No new framework
  code until the current, imperfect framework has produced one real number — observed
  defects motivate better fixes than theorised ones (R1 in
  [`docs/RULES.md`](docs/RULES.md)).
- **A step is done when its verification gate passes, not when the code exists.** This
  is the single load-bearing definition of "done" for the whole project — see
  [`VERIFICATION_SCHEME.md`](VERIFICATION_SCHEME.md).
- **Timebox the satisfying work on purpose, because it will expand to fill all available
  time otherwise.** The CostStack/Instrument refactor gets a hard ~2-week budget with a
  pre-written slip rule for what to cut if it overruns (R2 in
  [`docs/RULES.md`](docs/RULES.md), Phase B slip rule in
  [`DEVELOPMENT_TIMETABLE.md`](DEVELOPMENT_TIMETABLE.md)).
- **Pre-commit rules and kill criteria in writing, while calm, specifically so
  future-you can't renegotiate them under pressure or fatigue.** The kill criteria in
  the timetable exist because a deadline under stress is exactly when scope discipline
  erodes — the decision gets made once, in advance, by the version of you with the most
  perspective ([`DEVELOPMENT_TIMETABLE.md`](DEVELOPMENT_TIMETABLE.md) kill criteria, R2).
- **The human system is engineered with the same honesty as the code.** The timetable
  budgets an explicit illness/life buffer, names the morning habit — not the code — as
  the actual critical path, and states plainly that a slipped week is absorbed, not
  chased, because catching up is how streaks die. Optimistic planning is itself a form
  of the self-deception this whole project is trying to eliminate.
- **Every decision gets recorded as "decision — because rationale," always.** Theorising
  converges to a written commitment or it doesn't count — it doesn't get to live only in
  chat history or in your head (R4 in [`docs/RULES.md`](docs/RULES.md), the entire
  [`docs/decisions/`](docs/decisions/README.md) suite).

---

## Using this document

- When making a new design decision, check it against these pillars before writing it up
  as the next free number — ask the directory, not this page (this line named `D50` and `D51`
  until D544: it was written at D49 and the directory has run to D544 since, which is exactly
  why it now names no number at all) If it fights a pillar, that's worth noticing before it's committed,
  not after.
- When a decision *does* fight a pillar deliberately (a real tradeoff, not an oversight),
  say so explicitly in that decision's rationale — a philosophy that never bends is
  usually just being applied thoughtlessly.
- This document changes rarely and deliberately. If it needs to change, that's itself
  worth a short note here explaining what shifted and why — same discipline as everywhere
  else in this suite.
