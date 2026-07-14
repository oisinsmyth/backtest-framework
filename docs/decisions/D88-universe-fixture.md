# D88 — The 57-ETF universe fixture: composition, coverage policy, gzip

**Status:** Committed
**Date:** 2026-07-14
**Category:** Data layer
**Source:** Implementation session (Phase G kickoff)

## Decision

`data/fixtures/universe_daily_2015_2024_raw.csv.gz` (+ events JSON + meta): 57
liquid US ETFs with pre-2015 inception — broad index (SPY doubles as the D37 beta
benchmark), sector SPDRs, industry, commodity, bond, international, and REIT funds —
fetched raw with corporate actions via `EquityDataSource.get_raw_history`
(`scripts/fetch_universe.py`, polite 0.5s inter-symbol delay, one retry).

- **Coverage policy**: symbols with fewer bars than 98% of the modal count are
  excluded and *named in the meta* — inner-join alignment across 57 symbols would
  otherwise silently truncate the whole universe to the youngest symbol's start (the
  finite-lived-instrument failure mode D84 identified). Late launches (XLRE, XLC)
  are excluded by construction, not list curation. Actual outcome: 57/57 requested
  symbols passed; zero exclusions, zero fetch failures.
- **Deliberate stress tests in-universe**: OIH's 1-for-20 and USO's 1-for-8 reverse
  splits, UNG's two 1-for-4s, forward splits (XBI 3:1, IYT 4:1, SMH 2:1), and XLF's
  ratio-1.231 event (yfinance's encoding of the 2016 XLRE spin-off — handled
  mechanically as a split, economically approximate, stated in the study caveats).
  14 splits and 2,285 dividends total, all flowing through the D75 machinery.
- **Gzipped commit**: `csv_fixture` gained transparent `.gz` support (suffix-based,
  roundtrip-tested); the fixture is 2.5MB compressed vs ~17MB raw.

## Rationale

The Phase G study's universe must be reproducible from the repo (the same argument
as D70 — an unfetchable universe makes the study a one-off), which means committing
it; gzip keeps that honest at 2.5MB. The coverage policy converts a silent
data-shape hazard into a named, reported exclusion list. Keeping the pathological
split cases IN the universe rather than curating them away is deliberate: the
corporate-actions machinery is gate-tested, and a study that only runs on clean
names would be quietly overfit to data convenience.
