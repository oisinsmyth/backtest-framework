# D587 — Futures fills are one library module with pessimism as the default, not five per-script literals that disagree

**Status:** Committed
**Date:** 2026-09-21
**Category:** Backtest engine
**Source:** The execution sections of the three deposit pre-registrations
(`docs/internal/User-Doc-Deposit/SETTLEMENT_FLOW_LEDGER_PREREG.md` §7.3–7.4 and its required
unit tests 10–11, `SHOCK_CLASSIFIER_PREREG.md` §5.1–5.3 and its required unit tests 9–10,
`OPENING_AGENT_STATE_PREREG.md` §6.3), which each specify the SAME fill model in prose and
none of which had an implementation. Extends D10 (gap-through stops), D42 (the stop is the
only intrabar order), D12 (the `Instrument` protocol), D48 (no false affordances, raise
rather than answer wrongly) and D9's two fill assumptions. Governed by R16 for the two
equality guards below.

## Decision

Two new library modules, and nothing else in `src/` changed except a `Future` export.

### 1. `src/backtest_framework/instruments/future.py`

```
Future(root: str, tick_points: float, usd_per_point: float, tick_usd: float,
       quote_currency: str = "USD")                                  # frozen dataclass
Future.from_specs(root, *, specs_path=None, fallback_path=None) -> Future
  .round_to_tick(price: float, direction: "nearest"|"up"|"down" = "nearest") -> float
  .assert_on_grid(price: float, what: str = "price") -> None
  .ticks(price_diff: float) -> float                 # price points -> ticks, signed
  .usd(price_diff: float, quantity: float) -> float  # price points x contracts -> dollars
  .notional(quantity: float, price: float) -> float  # = quantity x price x usd_per_point
  .carry_components() -> tuple[str, ...]             # () -- the basis is in the price
  .tradeable_quantity(raw_quantity: float) -> float  # whole contracts
```

Units: `tick_points` and every price are in the units the contract is QUOTED in (index
points for ES, dollars per barrel for CL); `usd_per_point` and `tick_usd` are US dollars
per contract; `ticks()` returns ticks; `usd()` and `notional()` return dollars.

`from_specs` reads `data/futures_contract_specs.json` (CME's own service, 23 roots) and
falls back to `data/fut_specs_from_definition.json` (Databento GLBX definitions, 41 roots,
the only source for MBT). **An unknown root raises `KeyError`** naming both files'
contents. `__post_init__` re-asserts the specification file's own invariant,
`usd_per_point × tick_points == tick_usd`, on every construction. The class is the
protocol's third implementation and `isinstance(f, Instrument)` holds.

`Future` is exported from `instruments/__init__.py`; `Equity` and `OptionStub` are not,
because adding them was outside this record's touch list. The asymmetry is stated in that
file rather than hidden.

### 2. `src/backtest_framework/simulator/futures_fills.py`

Array-first — numpy arrays of one session's 1-minute bars, indexed by bar — with
`session_ohlc(frame)` as the only place a DataFrame appears and `bar_at(ohlc, i)` handing
back the `simulator.fills.Bar` that D10's gap rule already speaks.

```
Side.LONG | Side.SHORT                      # an Enum; a str or an int raises TypeError
FillAssumption.TOUCH | TRADE_THROUGH        # epsilon is ONE TICK, not an absolute 1e-9
ExitKind.STOP | TARGET | NONE
Fill(bar: int, price: float)
ExitResolution(kind: ExitKind, price: float | None, gapped: bool)
PassiveResult(filled: bool, bar: int | None, price: float | None)
SessionOHLC(open, high, low, close)   PassiveSession(ohlc, t0, side)

adverse_price(price, side, ticks, fut, *, closing=False) -> float
entry_fill(close, t0, side, fut, ticks_adverse=1, *, at="close", open=None) -> Fill
stress_fill(close, t0, side, fut, k=5, ticks_adverse=1) -> Fill
resolve_exit(bar, stop, target, side, fut, *, stop_rule=TOUCH, target_rule=TOUCH,
             stop_slippage_ticks=0, gap_through=True, levels_on_grid=True) -> ExitResolution
passive_limit(open, high, low, close, t0, side, fut, cancel_after=5,
              rule=TRADE_THROUGH) -> PassiveResult
passive_diagnostic(sessions, fut, *, horizon, cancel_after=5, rule=TRADE_THROUGH)
    -> {"unfilled_rate", "mean_outcome_filled", "mean_outcome_unfilled",
        "n", "n_filled", "n_unfilled"}          # outcomes in TICKS, no costs
running_peak_drawdown(high, low, side, fut) -> float            # price points
assert_entry_before(bar_ts, window_start, min_minutes=3) -> None # raises; ledger test 10
selftest(log=print) -> int
```

**The defaults are the deposit documents' conventions**: entry at the close of bar t0+1
plus one tick against the side; the stress fill the worst close of t0+1…t0+k; the stop
resolved before the target whenever a bar spans both; the D10 gap rule on the stop; the
target filled at `max/min(target, open)` on a gap in favour; every returned price on the
tick grid.

**Every window guard raises rather than truncating.** `entry_fill` with t0+1 past the
session end, `stress_fill` with t0+k past it, `passive_limit` with t0+cancel_after past it
— all raise. A stress window quietly shortened near the close stops being a stress window
on exactly the bars it matters on.

**Four knobs exist because the runners genuinely disagree, and each names its caller:**
`stop_rule`/`target_rule` (D490 mixes trade-through on the stop with touch on the target),
`stop_slippage_ticks` and `gap_through=False` (D490's trailing stop fills at `stop − TICK`
and never consults the open), `levels_on_grid=False` (a level computed as a fraction of a
range is not a tradeable price).

**The module ships a `selftest()`** — `uv run python -m
backtest_framework.simulator.futures_fills` — in which every audit passes a clean case and
then RAISES on a deliberate break, the `expect_raise` idiom of
`scripts/stage0_d581_gamma_close.py`. `tests/unit/test_futures_fills.py` gates the helper
itself: handed a function that cannot fail, `_expect_raise` must complain.

### 3. What this is NOT

Not a cost model. Commission, spread and impact stay in the `CostStack` bricks (D1, D2).
The only concession here is the tick the pre-registrations name.

## Rationale

### The equality guards (R16), and what they returned

`temp/d587_equality_guards.py`, on **the first 50 ES sessions of 2019** from
`data/fixtures/fut_ES_rth_1m.csv.gz` (2019-01-02 … 2019-03-14). Both scripts imported with
`importlib.util.spec_from_file_location`; neither edited. No session on or after
2024-01-01 is read. Wall time 1.4 s.

| guard | reference | result |
|---|---|---|
| **A** | `scripts/run_d490_range_reversion.py:simulate` — entry price and trailing-stop exit price | **BIT-IDENTICAL on all 44 trades** (7 trail, 36 close, 1 target), on entry price, exit price, exit bar index AND exit type |
| **B** | `scripts/d465_es_spread_and_mae_bias.py:mae_three_ways`, pessimistic branch | **BIT-IDENTICAL on all 50 sessions** |

Compared as IEEE-754 bit patterns (`struct.pack("<d", x).hex()`), not with a tolerance.

Guard A is not a re-run of D490's loop: it drives a second loop written against the REAL
price series with an explicit `Side`, where D490 works on a sign-flipped series with the
side folded into the prices (`series()` negates and swaps high/low so its long logic serves
both). Every level is reflected through that transform and the fills come from
`entry_fill` / `resolve_exit` / `adverse_price`. That the two agree to the last bit on 44
trades is evidence about the transform as well as about the fills.

Guard B: `mae_three_ways` returns its pessimistic branch as `max((cummax(high) − low)/entry)`;
`running_peak_drawdown` returns `max(cummax(high) − low)` in points and the guard divides.
Division by a positive constant is monotone in IEEE-754, so `max(x)/e` and `max(x/e)` are
the same float. The guard also reports `max |pessimistic − optimistic| = 0.00122422` over
the 50 sessions, because d465's own docstring records a bug where the two branches
collapsed onto each other and the test could no longer tell them apart.

### One convention was NOT adopted, and one default was added

* `scripts/run_d531_orb_session_native.py:breakouts` **skips** a bar that breaks both
  sides. It is recorded in the module docstring and deliberately not implemented: a
  skipped bar is a silent change to the sample, which is a different and worse failure
  than resolving the ambiguity pessimistically.
* The deposit documents define the stress fill only as "the worst close among t0+1…t0+5",
  with no concession. `stress_fill` carries `ticks_adverse` and defaults it to the same
  one tick as the primary fill, because a stress fill without it comes out BETTER than the
  primary fill whenever bar t0+1 is itself the worst close — a "stress" that is a discount
  on exactly the paths it exists to describe. The property test pins `stress ≥ entry`.

### Where the module disagrees with what is on disk

| existing literal | this module | which is right |
|---|---|---|
| `research/terrain_strategies.py:TRADE_THROUGH_EPS = 1e-9`, an ABSOLUTE price epsilon | `FillAssumption.TRADE_THROUGH` trades through by **one tick** | The tick. 1e-9 is 4e-09 of an ES tick and a different rule again on ZN's 1/64. On a tick grid `low ≤ stop − tick` is exactly D490's `low < stop`, so the tick epsilon reproduces the script and the absolute one does not. |
| `run_d490_range_reversion.py` enters at the **next OPEN** + 1 tick | default `at="close"`, the deposit documents' convention; `at="open"` is a required explicit argument and will not fall back to the close | Both. They are different assumptions about when the decision is made, not a bug; `at="open"` is what makes guard A exact. |
| `run_d490_range_reversion.py: MULT = {"ES": 5.0, "NQ": 2.0}` | `Future.from_specs("ES").usd_per_point == 50.0`; `MES` is 5.0 and `MNQ` is 2.0 | **The literal is right about the contract it means and wrong about the name.** Those are the MICRO multipliers. Nothing in D490's numbers is wrong — it sized micros throughout — but a reader taking `MULT["ES"]` for ES's multiplier is off by 10x. `Future.from_specs("MES")` is the object it wanted. Not fixed here: D490 is a frozen runner that produced a published number. |
| `d465_es_spread_and_mae_bias.py:mae_three_ways` returns three conventions | only the **pessimistic** one is implemented | d465's question is the BRACKET; this module's is the rule. A convention no caller reads would be a D48 affordance. |
| `run_d531_orb_session_native.py` skips both-sided bars | resolves to the stop | See above. |
| `d527_arm_crossing_cost.py: TICK_PTS, TICK_USD = 0.50`, `run_d531: COST_USD = 4.21`, `COMMISSION_RT = 3.00` | not represented | Costs are out of scope by design. |

### One deviation from the brief's letter, stated because it is a deviation

The grid tolerance is `1e-9 × tick_points` **floored at 4 ULP of the price**. Unfloored, a
nanotick is tighter than a double can carry once `price / tick_points` gets large: on 6E
(tick 5e-05) a price of 5,000 has 2.2e-09 ticks of representation error, and
`5000 + k × 5e-05` was declared off its own grid for 648 of 1,001 consecutive k. 6E trades
at 1.10 and every fixture on disk is unaffected — ES, NQ, CL, NG, GC, SI, ZN, ZB, ZF and
the micros all pass either way — so the floor changes no current number. It is there so
the guard degrades to "as tight as the float can express" instead of to a false alarm.

## Consequences

### Tests: 129 across four files, and 20 of 20 deliberate breaks caught

| file | tests | tier |
|---|---|---|
| `tests/golden/test_futures_fills_ledger.py` + `.hand.txt` | 25 | G — a five-bar MES session and a second one for the adverse-selection pair, every figure worked by hand in the `.hand.txt` before the assertions existed and without importing this codebase |
| `tests/unit/test_future_instrument.py` | 36 | U |
| `tests/unit/test_futures_fills.py` | 57 | U |
| `tests/property/test_futures_fills_property.py` | 11 | P |

The deposit documents' named tests are present and cite their source: **ledger 10**
(`assert_entry_before`, the 3-minute constraint, boundary inclusive), **ledger 11 and shock
9** (a bar spanning stop and target records the stop — in the golden ledger on both sides,
in the unit file across all four rule combinations, and in the property file quantified
over bars and instruments), **shock 10** (the stress fill picks the worst close for the
direction).

Property invariants, at `SETTINGS = settings(derandomize=True, max_examples=40,
deadline=None)` and citing D78/D537: every returned price is on the grid; `entry_fill` is
never better than the t0+1 close and equals it at zero ticks; `stress_fill` is never better
than `entry_fill` and coincides with it at k=1; a target is never returned from a bar whose
stop was also reached; a stop fill is never better than the stop level; trade-through is
strictly more demanding than touch; a fill does not change when bars after it are perturbed;
`round_to_tick` brackets and is idempotent. The generator draws prices as integer multiples
of the tick and its spread is drawn from {2, 8, 200} ticks, so at 2 the bars are tie-heavy
by construction — ties are where two conventions that agree everywhere else disagree.

**`temp/d587_mutation_check.py` applies 20 deliberate breaks one at a time and requires a
red suite for each: 20 of 20 caught.** The first run caught 9 of 10, and the survivor was
the one that matters most — swapping the tick epsilon for an absolute 1e-9 changed nothing,
because on a grid the two rules are the same statement. Two unit tests were added that use
OFF-GRID levels (`levels_on_grid=False`, the D490 case) where the rules finally differ; the
mutation is now caught on all four branches, stop and target, long and short. A suite that
could not tell this module's central claim from the literal it replaces was not testing it.

### What this does not do

* **Nothing is wired into `engine/backtest.py`.** `_sweep_intrabar_stops` is untouched and
  still treats the stop as the only intrabar order (D42). This module is available to
  study code; adopting it in the engine is a separate decision with its own diff.
* **No script was edited.** The literals in D490, D491, D527 and D531 stand; those files
  are evidence for published numbers (D543's reasoning). What changes is that the next
  runner does not have to re-derive them.
* **No strategy return was computed.** The equality guards read ES bars in 2016–2023 only
  and score nothing.
