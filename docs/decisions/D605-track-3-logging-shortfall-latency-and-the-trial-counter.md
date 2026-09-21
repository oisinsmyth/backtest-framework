# D605 — Track 3 logging: the per-trade fill log, implementation shortfall, latency and the trial counter, with the two things the deposit never defined named rather than guessed

**Status:** Committed
**Date:** 2026-09-21
**Category:** Testing
**Source:** `docs/internal/User-Doc-Deposit/SETTLEMENT_FLOW_LEDGER_PREREG.md` §13A.4 (lines
847–851) and §13A.5 (lines 853–860), with its unit tests 35 and 36; the four documents that
defer to that section — `LETF_CLOSE_FLOW_PREREG.md:228-230`,
`SHOCK_CLASSIFIER_PREREG.md:279-281`, `INDEX_REWEIGHT_FLOW_PREREG.md:322-324` and its unit test
28, `OPENING_AGENT_STATE_PREREG.md:251-252` and its open question O-Q3.
Builds on [D587](D587-shared-futures-fill-model.md) (the §7.3 fill model and the `Future`
instrument), [D591](D591-futures-cost-bricks-and-the-reconciled-cost-table.md) (`TickCrossing`
and the measured cost table), [D594](D594-the-frozen-protocol-layer.md) (`assert_frozen` and
`FrozenDriftError`) and [D588](D588-power-analysis-module.md) (`track3_route`), and inherits the
fill-log sign convention from `scripts/d364_slippage.py`
([D364](D364-the-auction-participation-bound.md), the record that built that log). Sibling of
D608, D604, D606 and D607, built the same day for the same deposit.

## Decision

`src/backtest_framework/validation/track3.py` — new module. `scripts/track3_report.py` is its
command line, `data/track3/SCHEMA.md` its column table. Nothing else in the repository is
touched: no runner, no README, no `VERIFICATION.md`, no `CHANGELOG.md`, no `data-available.md`,
no `docs/decisions/README.md`, no `COMPONENTS_PROP.md`.

**NOTHING HERE TRADES AND NO REAL FILL EXISTS.** There is no broker adapter, no scheduler and no
order router; `data/track3/` holds the schema and no trade file; every number in every test is
synthetic and hand-typed. This module reads a log somebody else will one day write.

**1. The API.**

| | |
|---|---|
| `TradeRow(trade_id, model, stage, frozen_sha256, root, size_label, side, qty, signal_ts, model_fill_px, order_sent_ts, fill_ts, fill_px, exit_signal_ts=None, exit_fill_ts=None, exit_fill_px=None, simulated=False, venue="", note="")` | frozen; prices in QUOTED points, `qty` in whole contracts, every `_ts` a `datetime` |
| `TradeRow.ordering_fault() -> str \| None` | the first of three ordering violations; never raises |
| `TradeRow.side_sign` · `.is_closed` · `.to_cells()` | +1/−1; whether the exit triple is present; the CSV cells |
| `TradeLog(path)` · `.append(row) -> TradeRow` · `.read() -> list[TradeRow]` | append-only CSV, header once, LF, floats through `repr` |
| `shortfall_ticks(row, fut) -> float` | ENTRY shortfall in TICKS, positive = worse for the strategy |
| `shortfall_usd(row, fut) -> float` | ticks × `tick_usd` × `qty`, same sign |
| `exit_shortfall_ticks(row, fut, model_exit_px) -> float` | the same rule with the sign INVERTED |
| `exit_shortfall_usd(row, fut, model_exit_px) -> float` | in dollars |
| `latency_bars(row, bar_seconds) -> float` | `(fill_ts − signal_ts) / bar_seconds`, in BARS |
| `latency_report(rows, bar_seconds, assumed_max=5) -> dict` | `min`, `p50`, `p95`, `max`, `n_beyond`, `share_beyond_t0_plus_5` |
| `quantile_nearest_rank(values, num, den) -> float` | integer-rank quantile |
| `cost_assumption_ticks(root, size=None, line=None) -> float` | crossing/2 + 1 adverse tick, per FILL, in ticks |
| `cost_review(rows, fut, assumption_ticks, n=50) -> CostReview` | `mean_shortfall_ticks`, `ratio`, `exceeds_by_50pct`, `action` |
| `TrialCounter(model, target=300, looks=(100, 200), frozen_path=None, counts_as_efficacy=True, efficacy_reason="")` | §13A.4's counter |
| `.add(x)` · `.extend(xs)` · `.n` · `.mean` · `.sd` · `.t` | ddof = 1; `mean` raises at N = 0, `sd` and `t` below N = 2, `t` on a constant series |
| `.at_look()` · `.futility()` · `.efficacy()` | the two decisions |
| `.check_frozen(params, code_paths, fixture_paths=()) -> Restart \| None` · `.restart(reason)` | §13A.4's restart |
| `.route(edge_sigma) -> Track3Route` · `.to_dict()` | delegated to `power.track3_route` |

Errors: `Track3Error` and its subclass `Track3LogError`. Constants: `SIDE_SIGN`,
`ADVERSE_TICKS_PER_ENTRY = 1.0`, `LATENCY_ASSUMED_MAX_BARS = 5.0`, `COST_REVIEW_N = 50`,
`EXCEEDS_RATIO = 1.5`, `COST_REVIEW_ACTION`, `FIELDS`.

**2. THE SIGN CONVENTION IS D364's, INHERITED RATHER THAN REINVENTED.**
`scripts/d364_slippage.py` is the only fill-log schema this repository had, and its rule is
**POSITIVE = THE FILL WAS WORSE FOR THE STRATEGY**, encoded as
`SIDE_SIGN = {"short_entry": -1.0, "cover_exit": +1.0}`. Generalised to both directions:

    entry:  shortfall_ticks = +side_sign * (fill_px      - model_fill_px) / tick_points
    exit:   shortfall_ticks = -side_sign * (exit_fill_px - model_exit_px) / tick_points

On d364's two cases the general rule reproduces its two literals exactly. Ledger unit test 35 —
*"a long filled 2 ticks above the model price records +2 ticks of shortfall; a short filled 2
ticks below records +2"* — is asserted in ticks AND in money on both sides, because a sign
asserted in prose inverted D280. A property test states the convention as an inequality at
every price: the shortfall is positive exactly when the fill was worse for that side, zero
exactly at the model price, and reading the same fill as the opposite side negates it.

**3. THE DEPOSIT DEFINES NEITHER "the CostStack slippage assumption" NOR a model EXIT price.
Both gaps are named here and neither is silently filled.**

*The assumption.* §13A.5 compares the mean shortfall to "the CostStack slippage assumption" and
never says what that is. `cost_assumption_ticks` declares it, **per fill and in ticks**:

    assumption = crossing_ticks_per_round_trip / 2 + ADVERSE_TICKS_PER_ENTRY

The first term is what D591's `TickCrossing` charges for ONE fill — it charges half a round trip
per fill — and the second is §7.3's *"plus 1 tick of adverse slippage"* on the primary entry
fill, which is the model price the shortfall is measured against. Both halves are read from
`data/futures_costs.json` and from §7.3; neither is a literal chosen here. On MNQ's `d508_exec`
line that is 2.1342422122227602 / 2 + 1 = **2.0671211061113803 ticks a fill**, and on NQ full
size **2.5227066433527296**. On the `d556_one_tick` line it is exactly 1.5.

*The exit price.* §13A.5's log list names ONE model price — the entry's, *"per Section 7.3"* —
and calls the rest *"exit details"*. So there is no `model_exit_px` column, and
`exit_shortfall_ticks` takes it as an ARGUMENT. **The exit shortfall is therefore not computable
from the log alone**, and that is a gap in the pre-registration rather than a design choice
here. Inventing the column would have changed what the deposit says to log.

**4. The quantiles are NEAREST RANK, in integer arithmetic, and the reason is a float.**
`rank = (num * n + den - 1) // den`. An interpolated p95 computes `0.95 * (n - 1)`, and 0.95 is
not a binary fraction: at n = 6 that is 4.750000000000001 rather than 4.75, so the reported p95
would depend on the last bit of a constant. The integer form has no such dependence and every
reported quantile is a value that actually occurred. At small n the p95 IS the maximum, which is
a property of the sample size and is said in the docstring rather than hidden.

**5. `cost_review` reads the FIRST n rows and never returns a verdict on fewer.** The deposit's
review happens *"after 50 trades"*; a review that silently widens its window every time it is
called is a different test each time it runs. Below n rows it returns `sufficient=False` with
the count and `mean`, `ratio` and `exceeds_by_50pct` all **None** — "within budget" computed on
six trades is a verdict manufactured out of an empty sample. The trigger is **strictly** greater
than 1.5 ("by more than 50%"), pinned by a unit test at exactly 1.5. **The action is a FLAG:**
nothing in this module edits `futures_costs.json`, a `CostStack` or a doc, because the deposit
says *"via doc edit"* and a doc edit is a human act.

**6. The counter's two decisions are separated, and only one of them can be switched off.**
`futility()` is True only at a look (`n in looks`) and only when mean < 0 **and** t < −1. The
rule is signed: `t < −1`, never `|t| > 1` — a book at t = **+2** satisfies the absolute form and
must not stop, which is hand case C in the golden. `efficacy()` exists at exactly N = target and
is False at N = target ± 1. `counts_as_efficacy=False` makes `efficacy()` False at every N and
**requires a reason string** — that is `INDEX_REWEIGHT_FLOW_PREREG.md` unit test 28, *"Track 3
January trades are never counted as independent efficacy evidence"*. **Futility is unaffected by
the flag**, deliberately: about five execution days a year cannot prove the index model works,
but they can still show it losing.

**7a. A FINDING THE PROPERTY TEST PRODUCED, AND THE BAR IS NOT SOFTENED FOR IT: a `t` landing
exactly on 2 is decided by the last bit, and a change of UNIT can flip it.** The series
`[0, d, d]` has `t = 2` algebraically for every `d > 0` — mean 2d/3, sd d/√3, t = 2 with `d`
cancelling. The computed `t` does not cancel: at `d = 0.0546875` it is exactly **2.0** and
`efficacy()` is **True**, while multiplying all three values by that same 0.0546875 gives
**1.9999999999999998**, one ULP lower, and `efficacy()` is **False**. The rescale-invariance
property found the pair; `test_a_t_exactly_on_the_bar_is_decided_by_the_last_bit` pins both.

**No tolerance is added and the threshold is not moved** — `t ≥ 2` is the deposit's
pre-registration and softening it here would be an undeclared amendment. What follows for the
forward test is the operative half: **a Track 3 run finishing at t = 2.000000 must be reported
as ON the bar, not as a pass.** The same holds for `t < −1` at a futility look.

**7. `t` raises three times rather than returning a number.** At N = 0 there is no mean; below
N = 2 there is no ddof = 1 sd; on a constant series sd = 0 and `t` is not infinite significance,
it is a data fault. Each raise says which.

**8. `check_frozen` does not re-raise, and that is the one place this module departs from D48's
"raise loudly".** §13A.4 makes drift a protocol event with a defined consequence — *"Any change
restarts the count at N = 0 under a new frozen file"* — not an error. `assert_frozen` (D594) is
called unchanged; on `FrozenDriftError` the returns list is cleared, a `Restart` carrying the
drift message is appended to `.restarts` and returned. Re-raising after the reset would leave
the caller with a reset it never learned about. The drift is not silent: the return value is
truthy, `to_dict()` carries every restart, and `check_frozen` with no `frozen_path` raises.

**9. AUTOMATION IS NOT BUILT.** `OPENING_AGENT_STATE_PREREG.md` O-Q3 asks for *"Execution
automation for Track 3 (broker API, hosting), given the 14:30 UK open"* — 09:30 ET is 14:30 UK,
inside the owner's working day. This record does not answer it and does not pretend to. What it
does is pin down what an automated executor must hand back, listed in Consequences below.

## Rationale

**One log, five documents.** Four of the six deposit pre-registrations say "logs implementation
shortfall and signal-to-fill latency per trade, with the 50-trade cost review from the ledger
doc (13A.5)" and then stop. Five copies of a shortfall formula is five chances to get the sign
wrong in one of them, and the sign is the whole quantity: a shortfall that comes out negative
when it should be positive turns a cost overrun into a cost saving.

**The golden pair caught the exit sign, before the code did.** The hand file's section 2 was
written first and got T4's exit backwards twice — it dropped `side_sign` from the formula and
then described 5016.25 against a 5016.00 model as "a tick BELOW". The golden failed on exactly
that assertion, and the hand file was corrected. That is the pairing working as designed: the
hand arithmetic is not a transcription of the code, so the two can disagree, and when they did
the disagreement was real.

**A log that half-parses is worse than one that refuses**, which is d364's own sentence. `read`
raises `Track3LogError` naming the file, the line and the field for a wrong header, a short row,
a non-numeric or non-finite price, an unparseable timestamp, a blank required cell, an unknown
side, a `simulated` that is not `True`/`False`, a half-recorded exit and a hand-reordered row.
It raises `Track3LogError` rather than d364's `SystemExit` because library code that kills the
interpreter cannot be tested for the message it raised.

**Ordering is checked by the LOG, not by the ROW, so that the guard can be fed a broken case.**
`TradeRow.__post_init__` validates everything that is a property of the row and deliberately
leaves ordering alone; `ordering_fault()` returns a string and `append` raises on it. A guard
that cannot be handed a violation cannot be shown to fire — CLAUDE.md's *"a self-test that
cannot fail is worse than none"*, and the memory rule that a break must hit the scalar compared.
Three orderings are read: the deposit's two (signal → order sent → fill) and, on a closed trade,
the exit pair after the entry fill. **The third is an ADDITION of this module** — the deposit
says only "exit details" — and is named as one here.

**Mixing aware and naive timestamps is refused at the row.** Subtracting them raises a bare
`TypeError` three functions later, inside a latency report, where nothing says which row did it.

**The property tests check the three shapes no finite example set covers** (D78 as amended by
D537): the sign is algebra and must hold at every price, on both sides, for entry and exit; a
row must survive the CSV exactly, over prices, quantities, microsecond timestamps, the optional
exit and arbitrary text; and **the verdicts must be invariant to a positive rescale of every
return**, because the deposit never fixes a unit for "mean net return per trade" and a futility
stop that depended on points-versus-dollars would be a verdict about the unit.

**The counter's hand cases are exact in binary, by construction.** A series of one outlier at
`m − (n−1)d` and `(n−1)` values at `m + d` has mean `m`, `sd = d·√n` and `t = m/d`; at n = 100,
√n = 10, so sd and t are both exact doubles and the golden asserts `==` on −0.125, 0.625 and
−2.0 rather than approximating. The same construction truncated to 99 values gives mean < 0 and
t ≈ −1.99 — both futility conditions satisfied — and `futility()` is still False, because 99 is
not a look. That is ledger unit test 36's second half and it needed a series where both
conditions genuinely hold off-look; a series that merely fails the conditions would have passed
a broken implementation.

## Consequences

- **103 tests** — 73 unit (`tests/unit/test_track3.py`, parametrised), 16 golden
  (`tests/golden/test_track3_ledger.py`, hand arithmetic in the paired `.hand.txt`), 14 property
  (`tests/property/test_track3_property.py` at `SETTINGS = settings(derandomize=True,
  max_examples=40, deadline=None)`). Two unit tests carry the deposit's own numbers in their
  names — `test_ledger_35_shortfall_sign_long_and_short_hand_ticks` and
  `test_ledger_36_futility_stops_at_n100_only_when_mean_negative_and_t_below_minus_one` — plus
  `test_ledger_36_n99_is_not_a_look_even_though_both_conditions_hold` and
  `test_index_unit_28_january_trades_never_count_as_efficacy_evidence`, so a reader goes from a
  numbered requirement to its test without a search. `uv run ruff check` and `uv run mypy` are
  clean on all five files; the set runs in about 1.9 s.
- `scripts/track3_report.py --selftest` accepts the good case first, then proves **22 raises**,
  and returns 0. Two unit tests import it by explicit path (`scripts/` is not a package and
  pytest imports any path you hand it) and run both its `selftest` and its live `report` path,
  so the script is not dead code. `REQUIRED_SECTIONS` is checked in the runner: the report
  raises if one of the four declared blocks was not emitted.
- **The script pins its own stdout and stderr to UTF-8.** The module's docstrings quote the
  deposit verbatim, so they carry `§`, the true minus and the ellipsis; a Windows console
  defaults to cp1252 and a print of any of them dies with `UnicodeEncodeError`, which turns a
  failing guard into a failing encoder and hides which one fired. Every message the library
  RAISES is ASCII for the same reason.
- **What an automated executor must supply, so O-Q3 can be answered later.** Four timestamps —
  `signal_ts`, `order_sent_ts`, `fill_ts`, and the `exit_signal_ts`/`exit_fill_ts` pair; the
  **model-intended fill price as at the signal**, from `futures_fills.entry_fill`, written into
  `model_fill_px` and **never recomputed afterwards** (a model price recomputed after the fact
  makes the shortfall a measurement of the recomputation); the `frozen_sha256` of the
  `FROZEN_<stage>.json` the trade ran under; the `simulated` flag (deposit D24); and the venue.
  Nothing in that list needs a particular broker, which is why it can be written down before the
  adapter exists.
- **Two gaps in the deposit are on the record and unresolved:** it defines neither "the CostStack
  slippage assumption" (§13A.5) nor a model EXIT price for the exit shortfall. Decision 3 above
  states what this module does about each. A future amendment to the pre-registration should
  settle both rather than leave the library declaring them.
- **One inherited lossiness, named rather than hidden:** text cells are read back STRIPPED,
  following `d364_slippage.read_log`, so a `note` with leading or trailing spaces does not round
  trip exactly. The property test quantifies over already-stripped text and says why.
- `data/track3/` holds `SCHEMA.md` and nothing else. **No trade file is created**, because none
  exists.
- `validation/__init__.py` stays empty; `track3` is imported by its full path, as `power`,
  `frozen` and `dsr` are.

## Draft integration text, for the integrator

**`docs/data-available.md` paragraph:**

> **`data/track3/` — the Track 3 per-trade fill log schema (D605).** `SCHEMA.md` alone: the 19
> columns of `data/track3/<model>_trades.csv` with their units, the sign convention
> (POSITIVE = the fill was worse for the strategy, inherited from `scripts/d364_slippage.py`)
> and the file rules (append-only, header once, LF, floats through `repr`, a strict typed
> reader). **No trade file exists and none is created**: no order has ever been sent from this
> repository, there is no broker adapter and no real fill has been recorded. The reader and the
> four statistics the deposit's §13A.5 asks for live in
> `src/backtest_framework/validation/track3.py`.

**`CHANGELOG.md` bullet:**

> - **D605 Track 3 logging** — `validation/track3.py`: the append-only per-trade fill log
>   (`TradeRow`/`TradeLog`, strict typed reader, duplicate and ordering refusals), implementation
>   shortfall in ticks and dollars on d364's sign convention with the exit sign inverted,
>   signal-to-fill latency with nearest-rank quantiles and the share beyond t0+5, the 50-trade
>   cost review as a FLAG that never edits a cost table and never returns a verdict below 50
>   trades, and §13A.4's `TrialCounter` with futility looks at N = 100/200, the efficacy decision
>   at exactly N = 300, the `counts_as_efficacy` switch for the index model, and a frozen-drift
>   restart through D594's `assert_frozen`. `scripts/track3_report.py` (+`--selftest`, 22 raises)
>   and `data/track3/SCHEMA.md`. 103 tests. No order is sent, no automation is built and no real
>   fill exists.
