# D63 — Bar alignment: inner join on exact timestamp equality

**Status:** Committed
**Date:** 2026-07-13
**Category:** Data layer
**Source:** Implementation session (multi-instrument alignment for pairs)

## Decision

`data.alignment.align_bars(bars_by_instrument)` indexes every instrument's
`TimestampedBar` series by timestamp, intersects the timestamp sets (inner join), and
returns one `AlignedBar(timestamp, bars: dict[instrument_id, Bar])` per surviving
timestamp, sorted. A timestamp present for some instruments but not all is dropped
entirely — not just for the instrument missing it. No tolerance window; timestamps
must match exactly.

Carry accrual needs no special handling for a dropped bar: `run_backtest` computes
carry from `(prev_timestamp, curr_timestamp)` of two *consecutive aligned* bars, so a
dropped Tuesday just makes the Monday→Wednesday gap 2 calendar days instead of 1 — the
same mechanism D33 already uses for weekends and holidays. Verified, not assumed: see
`tests/integration/test_pairs_backtest.hand.txt`.

## Rationale

D45 states the policy ("pairs/multi-leg strategies use inner-join alignment... a
missing bar on one leg means no trading that bar") but not the matching mechanism.
Exact-equality matching was chosen over a tolerance window (e.g. "same trading day
regardless of minute") because every `TimestampedBar` in this codebase currently comes
from one `DataSource` fetch at one `timeframe` (`EquityDataSource`, D59) — two legs
fetched the same way land on identical timestamps by construction (verified against
real XLE/XOP data, `tests/integration/test_pairs_backtest.py::
test_real_xle_xop_pair_runs_end_to_end`). A tolerance window is exactly the kind of
speculative generality Pillar 5 of `PHILOSOPHY.md` warns against: it would solve a
problem (misaligned intraday timestamps across data sources) this codebase doesn't
have yet, at the cost of a fuzzy-matching policy that would itself need its own
decision record. If a future data source produces genuinely offset timestamps for the
same trading session, that's a new problem for a new decision — not something to guess
a tolerance value for now.
