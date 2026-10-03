# D782 FIXTURE — the other BLS releases at 08:30 ET (PPI, import and export prices, the Employment Cost Index, productivity), sourced from the BLS year pages D585 cached

*2026-10-03. The principal, on extending D775's mechanism to other 08:30 releases: "Lets go with option 1"; on
scope, "BLS first, then decide".*

- **What it is:** a data fixture for D783's Stage 0. No price is read and no outcome is computed.
- **Why:** D585's calendar (`events.csv`) holds CPI and the Employment Situation at 08:30, but no other 08:30
  release. The BLS year pages it cached list the rest of BLS's schedule with dates and clocks.

## The file

`data/calendar/events_bls_0830.csv` (+ `.meta.json`), built by `scripts/build_bls_0830_calendar.py` from
`data/raw/calendar/` (main checkout). Nothing was fetched.

| event | page title (exact match) | rows | per full year |
|---|---|---|---|
| `PPI` | Producer Price Index | 131 | 12 |
| `IMPEXP` | U.S. Import and Export Price Indexes | 131 | 12 |
| `ECI` | Employment Cost Index | 44 | 4 |
| `PROD_P` | Productivity and Costs (P) | 44 | 4 |
| `PROD_R` | Productivity and Costs (R) | 44 | 4 |

- **All 394 rows are at 08:30 ET,** read off the page.
- **None falls on a CPI or Employment Situation day.**
- **The span is 2016 → 2026.** 2025 is disrupted (D585: the funding lapse) and 2026 is partly forward.

## The gates

- **G0:** the raw cache's manifest holds the BLS year pages. (The first build failed here silently: D585's module
  fixes its manifest path at import, so repointing the raw directory alone read an empty manifest. G1 caught it,
  since 0 rows did not equal 262, and the builder now repoints both and checks the cache.)
- **G1:** D585's parser, with the event map as a parameter, **reproduces `events.csv`'s 262 CPI and EMPSIT rows
  exactly**, every column, before any new row is written.
- **G2:** every full year 2016–2024 has 12 PPI, 12 IMPEXP, 4 ECI, 4 PROD_P and 4 PROD_R rows.
- **G3 (in the parser):** the page's weekday word agrees with the parsed date, and the row's year with the page's.
  The self-test shows both checks raise, and that a near-name ("Producer Price Index Detailed Report") is not matched.

## What it does not touch

- `events.csv` is unchanged. It is read by D775 and by D776's frozen vault line.
- `fetch_release_calendar.py` is unchanged; the new builder imports it.
- Census (retail sales), BEA (GDP, personal income) and DOL (jobless claims) are not in this file. They need their
  own sourced schedules and are the principal's call after D783.
