# D579 — FIXTURE: perpetual-swap **funding rates from three venues (Binance, Bybit, OKX) and Bybit daily open interest**, BTC and ETH, USDT- and coin-margined — 46,892 settlements 2018-11-15 → 2026-09-20 and 8,876 open-interest days from 2020-08-04, fetched free from the venues' public endpoints and committed as a tidy fixture

*2026-09-20. A data record, not a study. Built for the funding-cycle line
(`FUNDING_CYCLE_BASIS.md`), whose F1 is the published funding rate for the coming settlement and
whose F5 is perp open interest times |F1|. Fetcher `scripts/fetch_perp_funding.py` (stdlib only;
`--probe`, `--fetch` resumable into `data/raw/perp_funding/`, `--build` cache → fixture, `--selftest`
proving the gates raise). Nothing here reads a CME bar or computes a return.*

## What the venues give, as probed and fetched on 2026-09-20

| venue | series | from | rows | on the 00/08/16 UTC grid | share exactly at the +0.01 % default | share negative |
|---|---|---|---:|---:|---:|---:|
| Binance USDT-M | BTCUSDT | 2019-09-10 | 7,703 | 100 % | 35 % | 14 % |
| Binance USDT-M | ETHUSDT | 2019-11-27 | 7,469 | 100 % | 34 % | 14 % |
| Bybit linear | BTCUSDT | 2020-03-25 | 7,111 | 100 % | 41 % | 16 % |
| Bybit linear | ETHUSDT | 2020-10-21 | 6,482 | 100 % | 39 % | 17 % |
| **Bybit inverse** | **BTCUSD** | **2018-11-15** (the deepest) | 8,598 | 100 % | 47 % | 19 % |
| Bybit inverse | ETHUSD | 2019-01-25 | 8,384 | 100 % | 48 % | 18 % |
| OKX | four swaps | **2026-06-17 only** | 286 each | 100 % | 9–19 % | 9–21 % |
| Bybit open interest, daily | BTCUSDT / BTCUSD / ETHUSDT / ETHUSD | 2020-08-04 (ETHUSDT 2020-10-22) | 2,160–2,239 each | | | |

Every series runs to the 2026-09-20 16:00 UTC settlement; every series covers 100 % of its 8-hour
slots. **The cross-venue average the deposit asks for is Binance + Bybit.** OKX's public history
is three months deep and is carried for the overlap only. **Open-interest history is Bybit's
alone:** Binance's `openInterestHist` serves the last 30 days and OKX's contract statistics refuse
any range beyond the recent window; both are recorded in the meta as not fetched.

## Three things that bite, found on the way

1. **Binance's settlement timestamps carry a +1 ms offset on the wire** on 6,640 of its 15,172
   rows (`1568476800001` for 2019-09-14 16:00:00 UTC). The grid gate, which floors to seconds,
   passed at 100 % while the cross-venue join keyed on the raw millisecond found 3,861 common
   settlements of 7,111. The build floors every key to the minute (a settlement is on the minute
   by every venue's schedule) and records the count; the join then finds all 7,111.
2. **A third to a half of every series is exactly +0.0001.** That is the venues' clamp when the
   premium index is near zero, not a measurement: an event at the default carries no sign
   information and its sign is always positive. A signed mean over all events would be biased
   by construction. The share is in the meta by series, and any signed test runs with defaults
   excluded (the Stage 0 design says so).
3. **The rate settled at S is the time-average of the premium over the period ending at S.** It
   is known to within the last minutes before the settlement, not published in advance as the
   deposit's §1.1 says; the strictly-known-in-advance rate is the one settled at S−8h. Both are
   in the fixture by construction (every settlement is a row).

## Gates (in the meta, proven to raise by `--selftest`)

G1 no duplicate (venue, symbol, settlement); G2 Binance BTCUSDT settlements on the 00/08/16 UTC
grid ≥ 95 % (100 %); G3 Binance vs Bybit-linear BTC funding on the 7,111 common settlements:
**Pearson 0.67, sign agreement 82 %** (bar > 0.3); G4 no |rate| above 5 % a period (max 0.75 %,
the Binance cap); G5 no duplicate open-interest rows; G6 no negative open interest.

## Files

`data/fixtures/perp_funding.csv` (46,892 rows, 2.8 MB, tracked — small enough to live in git
under the manifest's own rule that plain csv stays tracked), `data/fixtures/perp_open_interest_daily.csv`
(8,876 rows), `data/fixtures/perp_funding.meta.json` (the per-series table above, the gates, the
sources, what was not fetched); the raw responses in `data/raw/perp_funding/` (gitignored, 14
files). Licence: public market-data endpoints, no key, no redistribution terms presented at fetch;
committed as a small derived fixture (D191). `docs/data-available.md` and the CHANGELOG carry the
entry; the manifest is rebuilt in this commit.
