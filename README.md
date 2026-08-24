# Quant Backtesting Framework

A Lego-brick-modular backtesting framework built to run a market-neutral pairs-trading study
(starting with XLE/XOP) as a research portfolio piece. Governing principle: trust is enforced
by structure, not convention — every friction, instrument, and validation check is a swappable,
individually-tested component. Research output is the product; the framework is the instrument.

The framework is complete (all in-scope verification gates passed) and the Phase G
research program has published five studies from it, plus a second, deliberately
contrasting strategy (a long-flat crypto breakout) that exists to test the framework's
own claim that a strategy is a swappable brick.

**The final report is [`docs/results/final_report.html`](docs/results/final_report.html)**
— the whole project in one document: what was tested, how each idea died, the seven real
defects the guards caught, and the two properties that survived (neither of which is
signal). Published at
<https://claude.ai/code/artifact/322b8663-8de5-4c75-b798-988d50281d63>.

It is the single source for that summary — deliberately not mirrored as Markdown, because
two copies of the same prose drift apart, which is the most repeated defect in this
project's own history (D176, D183, D186).

**The research output is [`docs/writeup.md`](docs/writeup.md)** — the five-study
measurement of whether ETF pairs trading clears real frictions (draft skeleton; every
headline number final and cross-checked against its source artifact by the test suite).

**The second study is [`BREAKOUT_RESULTS.md`](BREAKOUT_RESULTS.md)** — a long-flat
Donchian breakout on BTC/ETH, run through the same engine, cost stack, walk-forward
harness and trial registry as the pairs work. It is **directional and beta-loaded**, and
explicitly labelled as outside the market-neutral thesis (D38/D117); its verdict is that
fees are not the binding constraint, which turns out to be the least interesting true
thing about it.

**The third study is [`docs/results/crypto_pairs_btc_eth.md`](docs/results/crypto_pairs_btc_eth.md)**
— the market-neutral thesis strategy (the existing z-score pairs signal, unmodified) on
the same BTC/ETH data, with borrow and margin priced. It is an honest negative: at zero
fees *and* zero carry the strategy still loses 88.7%, because the pair's log spread is
stationary in only 14% of training windows. Realised beta is ≈ 0 on all three benchmarks,
so the neutrality engineering works — the thesis is what fails (D122–D127).

**The seventh study is [`STRUCTURE_RESULTS.md`](STRUCTURE_RESULTS.md)** — a five-part
discretionary retail price-action strategy (change of character, the flipped level, the
61.8% Fibonacci retracement, the fair value gap, RSI), mechanised so each part could be
measured separately and together on BTC/ETH 15m bars. Closed after 86 looks (D204–D211).
The result is a single variable: **no component predicts anything once leg size relative to
ATR is held constant**, and three features that cleared the promotion bar turned out to be
one quantity under three names. Three findings stand independently of that — the course's
5R break-even is 22.3–28.4% after costs rather than the 20% it claims, 27–44% of its trades
cost at least their entire risk to trade, and the confluence stack is *worse* at zero cost
than no filters at all.

Seven worked trades from that study, in the same form as the terrain final report, are at
[`docs/results/structure_trade_examples.html`](docs/results/structure_trade_examples.html) —
published at <https://claude.ai/code/artifact/7b93befb-9689-4efa-bf95-378a0fafd9d9>. The
examples are chosen by a rule fixed before any outcome was read, and every number on the
page is pinned against its source artifact by the test suite.

**Start with [`PHILOSOPHY.md`](PHILOSOPHY.md) if you're new here.** It's the guiding layer
above everything else — the small set of values (trust by structure, honesty over comfort,
anti-self-deception, composability, scope discipline) that generated every decision below,
and the first thing any new decision should be checked against.

**To USE the framework, read [`docs/TUTORIAL.md`](docs/TUTORIAL.md)** — the full path from
setup to research output, with every example executed verbatim by the test suite so it
cannot rot.

## Doc suite

**Planning (frozen, pre-implementation snapshots — 2026-07-13):**
- [`MASTER_PROJECT_DOC.md`](MASTER_PROJECT_DOC.md) — single-file collation of the three docs below, as they stood before build started
- [`DESIGN_DECISIONS.md`](DESIGN_DECISIONS.md) — original running log, D1–D49 + rules R1–R4 (superseded by the split docs below; kept for history)
- [`VERIFICATION_SCHEME.md`](VERIFICATION_SCHEME.md) — the 12 build steps and their test gates. A step is done when its gate passes, not when code exists.
- [`DEVELOPMENT_TIMETABLE.md`](DEVELOPMENT_TIMETABLE.md) — phased schedule (weeks 1–24) and pre-committed kill criteria.

**Live (kept current as implementation proceeds):**
- [`PHILOSOPHY.md`](PHILOSOPHY.md) — the guiding design philosophy; changes rarely and deliberately
- [`docs/decisions/`](docs/decisions/README.md) — one file per design decision, D1–D49 migrated + D50 onward as they're made
- [`docs/RULES.md`](docs/RULES.md) — standing scope/sequencing rules (R1–R5), apply continuously rather than once
- [`CHANGELOG.md`](CHANGELOG.md) — what shipped and when, Keep a Changelog format. Rationale lives in the decision records, not here.
- [`AITODO.md`](AITODO.md) — Claude's current working task list for this project. Not a roadmap; reflects the next few steps only.

## Working conventions

- **A step is done when its [VERIFICATION_SCHEME.md](VERIFICATION_SCHEME.md) gate passes**, not when code exists.
- **Every design decision gets a record** in `docs/decisions/`, formatted as decision + rationale, per R4 in [`docs/RULES.md`](docs/RULES.md). This includes on-the-fly decisions made mid-implementation, not just pre-planned ones.
- **R1 is binding during execution sessions**: no framework scope-creep before the framework produces one real number (the XLE/XOP walk-forward). See [`docs/RULES.md`](docs/RULES.md).
- Version control: local git only, no remote configured yet.

## Status

**Framework complete; research program published.** All in-scope verification-scheme steps
(1–9, 11, 12) passed their gates; the simulator is anchored to hand-computed golden masters
and reconciled penny-exact against vectorbt. Phase G has produced five one-variable-per-step
studies (selection → hedging → capacity → gross exposure) on a frozen 57-ETF universe, all
collected in [`docs/writeup.md`](docs/writeup.md) — draft prose, final numbers. A sixth
study, the long-flat crypto breakout in [`BREAKOUT_RESULTS.md`](BREAKOUT_RESULTS.md)
(D108–D117), reuses the framework unchanged on a directional strategy — and recorded one
blocked feature (a volume filter the `Bar` schema cannot support, D111) rather than working
around it. Next: writeup polish and reviewer outreach. See [`AITODO.md`](AITODO.md) for the
live task list.
