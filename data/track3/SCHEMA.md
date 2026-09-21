# Track 3 per-trade fill log — schema

The columns of `data/track3/<model>_trades.csv`, written and read by
[`src/backtest_framework/validation/track3.py`](../../src/backtest_framework/validation/track3.py)
(D605). The spec is `SETTLEMENT_FLOW_LEDGER_PREREG.md` §13A.5, quoted verbatim in that module's
docstring; `LETF_CLOSE_FLOW_PREREG.md`, `SHOCK_CLASSIFIER_PREREG.md`,
`INDEX_REWEIGHT_FLOW_PREREG.md` and `OPENING_AGENT_STATE_PREREG.md` all defer to it.

**THIS DIRECTORY HOLDS THIS FILE AND NOTHING ELSE. No trade file exists, because no order has
ever been sent from this repository** — there is no broker adapter, no scheduler and no order
router. Every number in the tests is synthetic and hand-typed.

| column | type | unit | notes |
|---|---|---|---|
| `trade_id` | text | — | unique within the file; `append` refuses a repeat |
| `model` | text | — | which pre-registration this trade belongs to |
| `stage` | text | — | the signal stage traded (§13A.5 starts at Stage A / A-lite) |
| `frozen_sha256` | text | — | the `FROZEN_<stage>.json` content digest this trade ran under (D594) |
| `root` | text | — | exchange root, e.g. `MNQ`. The shortfall refuses a `Future` whose root differs |
| `size_label` | text | — | `micro` or `full`, the cost table's size key |
| `side` | enum | — | `long` or `short`. Direction lives here, never in the sign of `qty` |
| `qty` | int | contracts | positive whole contracts |
| `signal_ts` | ISO-8601 | — | when the signal existed |
| `model_fill_px` | float | quoted points | §7.3's model-intended price, **as at the signal, never recomputed** |
| `order_sent_ts` | ISO-8601 | — | when the order left |
| `fill_ts` | ISO-8601 | — | when it filled |
| `fill_px` | float | quoted points | the actual fill |
| `exit_signal_ts` | ISO-8601 | — | blank on an open trade; all three exit fields or none |
| `exit_fill_ts` | ISO-8601 | — | ″ |
| `exit_fill_px` | float | quoted points | ″ |
| `simulated` | bool | — | `True` for a paper or prop-simulator fill (deposit decision D24) |
| `venue` | text | — | the broker or simulator the fill came from |
| `note` | text | — | free text; read back stripped |

**Prices are in the instrument's QUOTED points** (5000.25 index points on MNQ), never in ticks
and never in dollars. The tick and the dollar value come from `Future`, which reads the
exchange's own specification file.

## The sign convention

**POSITIVE = THE FILL WAS WORSE FOR THE STRATEGY** — `scripts/d364_slippage.py`'s rule, the only
fill-log convention this repository had, generalised to both directions.

    entry:  shortfall_ticks = +side_sign * (fill_px      - model_fill_px) / tick_points
    exit:   shortfall_ticks = -side_sign * (exit_fill_px - model_exit_px) / tick_points

with `side_sign` = +1 long, −1 short. A long filled 2 ticks above the model price and a short
filled 2 ticks below it both record **+2** (ledger unit test 35). The exit sign inverts because
an exit is the opposite trade.

`model_exit_px` is **not a column**: §13A.5 names one model price, the entry's, and calls the
rest "exit details", so the exit shortfall is not computable from the log alone and takes the
model exit price as an argument.

## File rules

Append-only; header written once; **LF newlines on every platform** (D550); floats written
through `repr`, so a round trip is exact. `read()` is strict — a malformed cell raises naming
the line and the field — and `append` refuses a duplicate `trade_id`, a row whose
`order_sent_ts` precedes `signal_ts`, a row whose `fill_ts` precedes `order_sent_ts`, a
half-recorded exit, and a row mixing timezone-aware and naive timestamps.
