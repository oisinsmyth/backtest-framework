# D70 — Committed CSV fixture as the pre-Step-7 frozen snapshot; calibration and adjusted-price caveats

**Status:** Committed / Deferred
**Date:** 2026-07-14
**Category:** Data layer
**Source:** Implementation session (Step 6)

## Decision

The Step 6 gate's "frozen snapshot" is satisfied, pre-Step-7, by
`data/fixtures/xle_xop_daily_2015_2024.csv` + sidecar `.meta.json` (fetch timestamp,
period, interval, source notes), fetched once by `scripts/fetch_fixture.py` and
**committed to git** — immutable in the sense that matters (changing it is a visible
diff, not a silent re-fetch, which is D24's actual concern), with the filename
serving as the `snapshot_id` on every logged trial. `data.csv_fixture` provides
save/load; volume is stored for Step 7's ADV work but not loaded (no false volume
affordance on TimestampedBar, D48). Step 7's SnapshotStore (checksummed IDs,
cleaning reports, sanity gate) replaces this.

**Caveats carried with the fixture, stated in `docs/results/first_real_number.md`:**
- Prices are yfinance **auto-adjusted** — commissions/impact computed on adjusted
  notionals is exactly the corruption D6 exists to fix; dividend cash flows on the
  short leg are not separately modeled.
- SqrtImpact σ/ADV are calibrated on the **full sample** (printed by the fetch
  script, hardcoded into the run config) — a mild look-ahead in cost calibration
  only, not in the signal.
- One OHLC epsilon artifact found in practice (XOP 2018-10-24, close < low by
  1.2e-16 relative — adjustment-arithmetic float noise): a concrete preview of why
  D26's sanity gate exists, handled with a stated tolerance (D47) in the fixture
  smoke test rather than an exact comparison.

## Rationale

Every alternative was worse: building SnapshotStore now pulls Step 7 forward against
R1/R2; running the first number on a live fetch makes it unreproducible the moment
yfinance restates history (D24's exact complaint); leaving the data uncommitted makes
the milestone unverifiable by anyone else. A committed CSV is the minimal artifact
that makes the number deterministic, reviewable, and honestly labeled. The e2e test
runs offline against it, so the Step 6 gate is a repeatable check rather than a
one-off event.
