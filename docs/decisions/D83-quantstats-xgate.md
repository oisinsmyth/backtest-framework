# D83 — Step 9's X-gate reference is quantstats; exact ties, one API quirk documented

**Status:** Committed
**Date:** 2026-07-14
**Category:** Analytics
**Source:** Implementation session (Step 9)

## Decision

The Step 9 X-gate (`tests/unit/test_quantstats_xgate.py`) anchors Sharpe, Sortino,
and max drawdown against **quantstats 0.0.81**, which installed and runs correctly
against pandas 3.0.3 — the vectorbt-returns-accessor fallback planned for a
compatibility failure was not needed. Agreement is **exact** (1e-9 relative at rf=0;
1e-6 at rf=4%), not tolerance-waved: D80 deliberately adopted quantstats'
conventions (geometric rf de-annualization, full-length RMS downside) where they're
independently defensible, so the comparison demands equality rather than explaining
deltas — the same matched-conventions-then-exact-agreement argument as D79.

**Quirk found during the smoke test, documented in the test:** quantstats' nonzero-rf
path requires a DatetimeIndex — a plain RangeIndex crashes inside its tz-localization
(`TypeError: index is not a valid DatetimeIndex or PeriodIndex`). The X-gate series
carries business dates for that reason. Also a self-correction worth recording: the
first smoke test's "suspicious" negative Sharpe on a positive-mean-parameter draw was
*correct* — the seeded sample's realized mean is negative, and the manual
recomputation matched quantstats to the last digit. The reference survived being
doubted, which is what a reference is for.

## Rationale

quantstats over the vectorbt fallback because it's the reference the original
verification scheme named, it's a different codebase from the Step 8 anchor (two
independent references beat one used twice), and it worked. The DatetimeIndex quirk
is exactly the kind of integration fact worth writing down: the next person to feed
quantstats a bare array gets a cryptic tz error, and the test's docstring now says
why.
