# LETF close-flow: point-in-time AUM sources (deposit §3.2)

*Opened 2026-09-27 on the principal's word ("Yes, do the sweep, then open LETF close-flow"). Per ticker, the source
of `A[t-1]` = NAV × shares outstanding at the prior close. Nothing here is estimated yet.*

## ProShares: eight of ten tickers, issuer history, ON DISK

- **Source:** ProShares' all-funds historical NAV file, supplied by the principal on 2026-09-24
  (`historical_nav.zip`, 173 funds, 540,428 rows), cached at
  `data/raw/proshares_historical_nav/historical_nav_2026-09-23.zip`. It is identical to `fund_nav_daily` (the
  per-fund `accounts.profunds.com/etfdata/ByFund/{TICKER}-historical_nav.csv` route) on every common date.
- **Columns:** `Date, ProShares Name, Ticker, NAV, Prior NAV, NAV Change (%), NAV Change ($),
  Shares Outstanding (000), Assets Under Management`. Both A = NAV × shares and the published AUM are available,
  so the identity is a known-answer check on the parse.
- **Coverage before the vault (rows from 2025-03-01 not parsed, A10):**

| ticker | L | index | first row | rows to 2025-02-28 | longest gap (calendar days) | rows with 0 shares |
|---|---|---|---|---|---|---|
| TQQQ | +3 | NDX | 2010-02-09 | 3,788 | 5 | 0 |
| SQQQ | −3 | NDX | 2010-02-09 | 3,788 | 5 | 0 |
| QLD | +2 | NDX | 2006-06-19 | 4,705 | 5 | 0 |
| QID | −2 | NDX | 2006-07-11 | 4,690 | 5 | 0 |
| UPRO | +3 | SPX | 2009-06-23 | 3,947 | 5 | 0 |
| SPXU | −3 | SPX | 2009-06-23 | 3,947 | 5 | 0 |
| SSO | +2 | SPX | 2006-06-19 | 4,705 | 5 | 0 |
| SDS | −2 | SPX | 2006-07-11 | 4,690 | 5 | 0 |

- **Splits:** ProShares' 363 splits 2010–2026 are tracked at `data/fund_facts/proshares_splits.csv`; Gate 0's
  |ΔAUM| > 25% review must not flag a split (NAV and shares move inversely; AUM does not).
- **Forward (Track 2):** the same per-fund CSV route, daily.

## Direxion: SPXL (+3) and SPXS (−3), NOT SOURCED

- **Issuer page** (`direxion.com/product/daily-sp-500-bull-bear-3x-etfs`, read 2026-09-27 in a browser; plain
  fetches return 403): the current NAV and market close (as of 09/24/2026), a premium/discount tool and a
  **current-day** holdings CSV. **No NAV history and no shares-outstanding history** is offered.
- **EDGAR N-PORT, checked 2026-09-27** (Direxion Shares ETF Trust, CIK 1424958; SPXL S000022767, SPXS
  S000022765): NPORT-P from 2019-12, 1,728 filings to 2024-12. Each has the quarter-end `netAssets` and, per month,
  `mon1Flow`–`mon3Flow` and `monthlyTotReturn`: month-end net assets rebuild from 2019-Q3.
- **Ruling (LETF-A3):** estimate daily AUM from the N-PORT month-ends with a band measured on the ProShares funds;
  before 2019-Q3 check N-SAR/N-CSR; if it does not work, the principal sources it.
- Not used: sharesoutstandinghistory.com (~153 sparse points; third-party, terms unread).
