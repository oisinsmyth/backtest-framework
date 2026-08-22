# D190 — The Binance flat-file archive is a second provider, in a different price frame, with a per-file epoch unit

**Status:** Committed
**Date:** 2026-08-22
**Category:** Data layer
**Source:** Provider probe ([`docs/results/binance_provider_probe.md`](../results/binance_provider_probe.md))

## Decision

`data.binance.vision` is admitted as a second market-data provider for crypto, parsed by
`data/binance_archive.py` (pure, offline) with network access confined to
`scripts/probe_binance_archive.py`. It does not replace `EquityDataSource`; the daily
crypto fixture stays as it is.

Three provider facts are enforced in code rather than assumed:

1. **The epoch unit is read per file.** `detect_timestamp_unit` maps digit width to
   `ms`/`us` and raises on anything else.
2. **The price frame is as-traded, with no events, ever.** `as_traded_from_adjusted` must
   **not** be applied to Binance data.
3. **Base and quote volume are carried separately**, in the provider's own units, and
   neither is derived from the other.

## Rationale

**Why a second provider at all.** Every intraday conclusion in this project is a statement
about yfinance. D160 recorded `Volume = 0` on 17,520 of 34,923 hourly BTC/ETH bars, so the
cleaner had to be called on prices only. D163 refused any return claim below 1h because 60
days cannot hold a 252-day training window. D165 had to splice a cost curve onto a
separately-measured gross edge because the 730 days served contain no trend edge at all.
D189 then closed the terrain programme on an S1 volume-profile sensor computed from
**daily** bars, for the same reason.

Those are four compromises forced by one source. The probe measures whether a different
source removes them: **108 monthly archives of 1m bars for BTC and ETH, 2017-08 to
2026-07**, against 730 days of 1h. On every sampled month from 2022 onward the zero-volume
rate is **0.000%**.

**Why the epoch unit is detected and not configured.** Binance changed kline `open_time`
from milliseconds to microseconds at the 2025-01 monthly file. The probe pins the boundary
on both majors independently: 2024-12 is 13 digits, 2025-01 is 16. A reader that assumes
milliseconds dates a mid-2025 bar to the year 57,400 — and nothing else in this project
would catch it, because every downstream check operates on the series it is handed.

That is D187 exactly. Crypto volume quoted in dollars was read as coins, every
market-impact charge came out wrong by √price, and two results looked like findings until
the units error surfaced. D187's own conclusion was that *the name of a field is not a
contract, the parameter that enforces it is*. A configured unit would be a name. A detector
that raises on an unrecognised width is a contract.

**Why the price frame difference is load-bearing.** yfinance's `auto_adjust=False` frame is
already split-adjusted and dividend-unadjusted (D75), which is why
`as_traded_from_adjusted` exists. Binance publishes what actually traded on the venue: no
adjustment of any kind, and spot crypto has no dividends or splits to adjust for. Applying
the inverse-split machinery to a frame that was never adjusted would silently rescale
prices by any split ratio it found. The events sidecar stays empty-but-present, and the
guard that refuses to write a fixture whose empty sidecar would be a lie (D48/D108) is kept
even though this provider can never trip it.

**Why both volume columns are carried.** The probe runs the check D187 did not have: quote
volume ÷ base volume must be a price inside the bar's own high–low range. It holds on
**100.0000% of bars in every sampled month**. Deriving one column from the other would
throw away the only cross-check available at the provider boundary.

**What this costs, and it is not nothing.** Of the 63 coins the existing cross-section
admitted (D140), **58** are reachable and **5** are not — and the missingness is not
random. `OKB`, `HT` and `CRO` are the exchange tokens of OKX, Huobi and Crypto.com; `BSV`
is a fork Binance delisted in 2019. A venue does not list its competitors' tokens, so
adopting a single-venue archive silently applies a selection screen the yfinance roster did
not. The archive states no reason for any exclusion, so that reading is an observation
about which symbols these are rather than a measurement. It is recorded because D180's
lesson is that the sample is the thing most likely to be wrong, and a universe drawn from
one venue is a universe that venue chose.

Set against it: the archive **retains delisted pairs and stops at the death date**, with no
back-fill. Eleven of the 58 terminate before 2026-07 — `BTGUSDT` at 2022-10, `SRMUSDT` at
2022-11, `XMRUSDT` at 2024-02. That is the failure-universe signature D140/D180 needs, and
it is more honest than a provider that withdraws history when a listing ends.

**Why the parser is pure and the network is not.** Mirrors the `_bars_from_dataframe` /
`EquityDataSource` split (D59), for the same reason: conversion is the part that can be
wrong in a way that matters, so it must be testable without the provider. Thirty-eight
offline tests cover the parser; one `live_fetch` test asserts shape invariants only.

**Why this is not a `DataSource`.** The `DataSource` protocol in `source.py` is structural,
unused anywhere in `src`, and takes an `Instrument`. The seam every fetch script actually
uses is `get_raw_history(symbol, start, end, timeframe)`. This module parses and stops
there; a fetcher conforming to that seam is a later decision, made when a study needs one.

## Consequences

- Sub-hourly walk-forward becomes possible for the first time: 108 months of 1m against
  D163's 60 days. D163's refusal was correct on its data and does not bind on this.
- `taker_buy_base` arrives in the same row as the bar, so signed order flow costs nothing
  extra. The `aggTrades` archives are ~409 MB per symbol-month; the klines are ~2.1 MB.
- The daily crypto fixture now has an independent check (§ D191's reconciliation): BTC
  agrees to a median 9.6 bp and ETH to 14.8 bp over May 2021.
- Two further decisions follow directly: [D191](D191-manifest-only-storage-for-large-archives.md)
  on storage and [D192](D192-zero-volume-at-one-minute-is-real.md) on the cleaner.

## What this does not settle

It measures a provider. It says nothing about whether any intraday rule works, and D163's
conclusion needs no return data to survive better bars: a rule paying a triple-digit
percentage of capital a year in fees cannot be run. Going intraday has to mean changing the
hypothesis class, not the sampling rate.
