# The Binance archive, measured before anything is built on it

A provider probe, run in the same order D160 used: measure what the source actually serves, then design the study against that rather than against an assumption. Nothing here is a fixture, a snapshot or a result.

`binance_probe_summary.json` holds every figure below. Re-render this document from it with `--report-only`, offline.

## What the archive holds

Of the **63** coins the existing cross-section admitted (D140), **58** are reachable as `USDT` spot pairs at 1m and **5** are not.

Unreachable, with the reason the listing gave:

- `BSVUSDT` — no monthly 1m klines published
- `CROUSDT` — no monthly 1m klines published
- `HTUSDT` — no monthly 1m klines published
- `LUNA1USDT` — no monthly 1m klines published
- `OKBUSDT` — no monthly 1m klines published

**The missingness is not random, and that matters more than the count.** `OKB`, `HT` and `CRO` are the exchange tokens of OKX, Huobi and Crypto.com; `BSV` is a fork Binance delisted in 2019. A venue does not list its competitors' equity-like tokens, so switching provider silently applies a selection screen that the yfinance roster did not. The archive states no reason for any of them — that reading is an observation about which symbols these are, not a measurement — but a universe drawn from one venue is a universe that venue chose, and D180's lesson is that the sample is the thing most likely to be wrong.

**11 of 58 series terminate before the archive's latest month (2026-07)** — a delisting, with the history up to it preserved:

`BTGUSDT` (2022-10), `EOSUSDT` (2025-05), `MATICUSDT` (2024-09), `MKRUSDT` (2025-09), `OMGUSDT` (2024-06), `REPUSDT` (2022-12), `SNTUSDT` (2025-04), `SRMUSDT` (2022-11), `WAVESUSDT` (2024-06), `XEMUSDT` (2024-06), `XMRUSDT` (2024-02)

A gap *inside* a symbol's own span is a third case, distinct from both a delisting and a gap between bars — the provider published nothing for those months while the pair still existed:

- `FTTUSDT` — 9 months missing: 2022-12, 2023-01, 2023-02, 2023-03, 2023-04, 2023-05, 2023-06, 2023-07, 2023-08

| symbol | fixture symbol | months | first | last | listing gaps | size | checksums |
|---|---|---:|---|---|---:|---:|---:|
| `BTCUSDT` | `BTC-USD` | 108 | 2017-08 | 2026-07 | 0 | 230.8 MB | 100% |
| `ETHUSDT` | `ETH-USD` | 108 | 2017-08 | 2026-07 | 0 | 214.9 MB | 100% |
| `BNBUSDT` | `BNB-USD` | 105 | 2017-11 | 2026-07 | 0 | 182.0 MB | 100% |
| `NEOUSDT` | `NEO-USD` | 105 | 2017-11 | 2026-07 | 0 | 139.7 MB | 100% |
| `LTCUSDT` | `LTC-USD` | 104 | 2017-12 | 2026-07 | 0 | 178.5 MB | 100% |
| `QTUMUSDT` | `QTUM-USD` | 101 | 2018-03 | 2026-07 | 0 | 116.1 MB | 100% |
| `ADAUSDT` | `ADA-USD` | 100 | 2018-04 | 2026-07 | 0 | 164.9 MB | 100% |
| `XLMUSDT` | `XLM-USD` | 99 | 2018-05 | 2026-07 | 0 | 143.1 MB | 100% |
| `XRPUSDT` | `XRP-USD` | 99 | 2018-05 | 2026-07 | 0 | 170.9 MB | 100% |
| `ETCUSDT` | `ETC-USD` | 98 | 2018-06 | 2026-07 | 0 | 140.0 MB | 100% |
| `ICXUSDT` | `ICX-USD` | 98 | 2018-06 | 2026-07 | 0 | 110.8 MB | 100% |
| `ONTUSDT` | `ONT-USD` | 98 | 2018-06 | 2026-07 | 0 | 122.0 MB | 100% |
| `TRXUSDT` | `TRX-USD` | 98 | 2018-06 | 2026-07 | 0 | 162.5 MB | 100% |
| `VETUSDT` | `VET-USD` | 97 | 2018-07 | 2026-07 | 0 | 149.3 MB | 100% |
| `LINKUSDT` | `LINK-USD` | 91 | 2019-01 | 2026-07 | 0 | 144.8 MB | 100% |
| `ZRXUSDT` | `ZRX-USD` | 90 | 2019-02 | 2026-07 | 0 | 96.0 MB | 100% |
| `BATUSDT` | `BAT-USD` | 89 | 2019-03 | 2026-07 | 0 | 104.2 MB | 100% |
| `DASHUSDT` | `DASH-USD` | 89 | 2019-03 | 2026-07 | 0 | 120.7 MB | 100% |
| `ZECUSDT` | `ZEC-USD` | 89 | 2019-03 | 2026-07 | 0 | 122.0 MB | 100% |
| `ATOMUSDT` | `ATOM-USD` | 88 | 2019-04 | 2026-07 | 0 | 132.4 MB | 100% |
| `THETAUSDT` | `THETA-USD` | 88 | 2019-04 | 2026-07 | 0 | 106.4 MB | 100% |
| `ALGOUSDT` | `ALGO-USD` | 86 | 2019-06 | 2026-07 | 0 | 117.6 MB | 100% |
| `DOGEUSDT` | `DOGE-USD` | 85 | 2019-07 | 2026-07 | 0 | 134.2 MB | 100% |
| `EOSUSDT` | `EOS-USD` | 85 | 2018-05 | 2025-05 | 0 | 130.8 MB | 100% |
| `HBARUSDT` | `HBAR-USD` | 83 | 2019-09 | 2026-07 | 0 | 112.1 MB | 100% |
| `XTZUSDT` | `XTZ-USD` | 83 | 2019-09 | 2026-07 | 0 | 104.6 MB | 100% |
| `BCHUSDT` | `BCH-USD` | 81 | 2019-11 | 2026-07 | 0 | 123.6 MB | 100% |
| `LSKUSDT` | `LSK-USD` | 78 | 2020-02 | 2026-07 | 0 | 66.2 MB | 100% |
| `SCUSDT` | `SC-USD` | 73 | 2020-07 | 2026-07 | 0 | 86.7 MB | 100% |
| `SNXUSDT` | `SNX-USD` | 73 | 2020-07 | 2026-07 | 0 | 94.9 MB | 100% |
| `CRVUSDT` | `CRV-USD` | 72 | 2020-08 | 2026-07 | 0 | 107.2 MB | 100% |
| `DOTUSDT` | `DOT-USD` | 72 | 2020-08 | 2026-07 | 0 | 116.1 MB | 100% |
| `MANAUSDT` | `MANA-USD` | 72 | 2020-08 | 2026-07 | 0 | 96.8 MB | 100% |
| `SANDUSDT` | `SAND-USD` | 72 | 2020-08 | 2026-07 | 0 | 101.7 MB | 100% |
| `SOLUSDT` | `SOL-USD` | 72 | 2020-08 | 2026-07 | 0 | 124.9 MB | 100% |
| `YFIUSDT` | `YFI-USD` | 72 | 2020-08 | 2026-07 | 0 | 103.2 MB | 100% |
| `AVAXUSDT` | `AVAX-USD` | 71 | 2020-09 | 2026-07 | 0 | 108.7 MB | 100% |
| `EGLDUSDT` | `EGLD-USD` | 71 | 2020-09 | 2026-07 | 0 | 95.0 MB | 100% |
| `FTTUSDT` | `FTT-USD` | 71 | 2019-12 | 2026-07 | 9 | 88.2 MB | 100% |
| `KSMUSDT` | `KSM-USD` | 71 | 2020-09 | 2026-07 | 0 | 90.6 MB | 100% |
| `SUSHIUSDT` | `SUSHI-USD` | 71 | 2020-09 | 2026-07 | 0 | 93.4 MB | 100% |
| `AAVEUSDT` | `AAVE-USD` | 70 | 2020-10 | 2026-07 | 0 | 109.5 MB | 100% |
| `FILUSDT` | `FIL-USD` | 70 | 2020-10 | 2026-07 | 0 | 109.8 MB | 100% |
| `NEARUSDT` | `NEAR-USD` | 70 | 2020-10 | 2026-07 | 0 | 106.8 MB | 100% |
| `AXSUSDT` | `AXS-USD` | 69 | 2020-11 | 2026-07 | 0 | 97.0 MB | 100% |
| `MATICUSDT` | `MATIC-USD` | 66 | 2019-04 | 2024-09 | 0 | 101.0 MB | 100% |
| `WAVESUSDT` | `WAVES-USD` | 66 | 2019-01 | 2024-06 | 0 | 86.5 MB | 100% |
| `MKRUSDT` | `MKR-USD` | 63 | 2020-07 | 2025-09 | 0 | 79.6 MB | 100% |
| `OMGUSDT` | `OMG-USD` | 63 | 2019-04 | 2024-06 | 0 | 73.5 MB | 100% |
| `XMRUSDT` | `XMR-USD` | 60 | 2019-03 | 2024-02 | 0 | 81.4 MB | 100% |
| `STEEMUSDT` | `STEEM-USD` | 52 | 2022-04 | 2026-07 | 0 | 47.8 MB | 100% |
| `LUNCUSDT` | `LUNC-USD` | 47 | 2022-09 | 2026-07 | 0 | 88.0 MB | 100% |
| `XEMUSDT` | `XEM-USD` | 44 | 2020-11 | 2024-06 | 0 | 47.0 MB | 100% |
| `USTCUSDT` | `USTC-USD` | 41 | 2023-03 | 2026-07 | 0 | 52.5 MB | 100% |
| `REPUSDT` | `REP-USD` | 31 | 2020-06 | 2022-12 | 0 | 27.6 MB | 100% |
| `SRMUSDT` | `SRM-USD` | 28 | 2020-08 | 2022-11 | 0 | 39.9 MB | 100% |
| `SNTUSDT` | `SNT-USD` | 24 | 2023-05 | 2025-04 | 0 | 23.8 MB | 100% |
| `BTGUSDT` | `BTG-USD` | 19 | 2021-04 | 2022-10 | 0 | 15.9 MB | 100% |

A `last` month short of the present is a **delisting**, and the archive keeps the history up to it rather than withdrawing it. That is the failure-universe signature D140/D180 needs, and it is honest — there is no back-fill.

## Schema, and a units switch inside the archive

Kline `open_time` changed from **milliseconds to microseconds** partway through the archive. A reader that assumes milliseconds dates a mid-2025 bar to the year 57,400. This is D187's failure mode exactly — a units error, invisible to every other check — so the reader detects the unit per file and refuses a third.

| symbol | month | bars | epoch unit | cols | header | zero-vol | rate | zero-vol == zero-trade | sha256 |
|---|---|---:|---|---:|---|---:|---:|---|---|
| `BTCUSDT` | 2017-08 | 21,360 | **ms** | 12 | no | 6,974 | 32.650% | yes | verified |
| `BTCUSDT` | 2022-02 | 40,320 | **ms** | 12 | no | 0 | 0.000% | yes | verified |
| `BTCUSDT` | 2024-11 | 43,200 | **ms** | 12 | no | 0 | 0.000% | yes | verified |
| `BTCUSDT` | 2024-12 | 44,640 | **ms** | 12 | no | 0 | 0.000% | yes | verified |
| `BTCUSDT` | 2025-01 | 44,640 | **us** | 12 | no | 0 | 0.000% | yes | verified |
| `BTCUSDT` | 2025-02 | 40,320 | **us** | 12 | no | 0 | 0.000% | yes | verified |
| `BTCUSDT` | 2026-07 | 44,640 | **us** | 12 | no | 0 | 0.000% | yes | verified |
| `ETHUSDT` | 2017-08 | 21,360 | **ms** | 12 | no | 5,806 | 27.182% | yes | verified |
| `ETHUSDT` | 2022-02 | 40,320 | **ms** | 12 | no | 0 | 0.000% | yes | verified |
| `ETHUSDT` | 2024-11 | 43,200 | **ms** | 12 | no | 0 | 0.000% | yes | verified |
| `ETHUSDT` | 2024-12 | 44,640 | **ms** | 12 | no | 0 | 0.000% | yes | verified |
| `ETHUSDT` | 2025-01 | 44,640 | **us** | 12 | no | 0 | 0.000% | yes | verified |
| `ETHUSDT` | 2025-02 | 40,320 | **us** | 12 | no | 0 | 0.000% | yes | verified |
| `ETHUSDT` | 2026-07 | 44,640 | **us** | 12 | no | 0 | 0.000% | yes | verified |
| `XEMUSDT` | 2020-11 | 9,240 | **ms** | 12 | no | 1,915 | 20.725% | yes | verified |
| `XEMUSDT` | 2022-09 | 43,200 | **ms** | 12 | no | 24,486 | 56.681% | yes | verified |
| `XEMUSDT` | 2024-06 | 23,220 | **ms** | 12 | no | 3,145 | 13.544% | yes | verified |
| `BTGUSDT` | 2021-04 | 20,746 | **ms** | 12 | no | 1,580 | 7.616% | yes | verified |
| `BTGUSDT` | 2022-01 | 44,640 | **ms** | 12 | no | 25,878 | 57.970% | yes | verified |
| `BTGUSDT` | 2022-10 | 33,660 | **ms** | 12 | no | 15,886 | 47.195% | yes | verified |

## Volume fidelity, and why the zero bars are not the same finding as D160's

D160 found yfinance reporting `Volume = 0` on roughly half of all hourly BTC/ETH bars whose prices were present, consistent and on instruments that have never had a zero-volume hour. That is a provider defect.

The zero-volume bars here are a different thing, and the column that separates them is `number_of_trades`. Where zero volume and zero trades are **the same bars**, the bar is telling the truth: nothing traded in that minute. On a young or thin listing that is a property of the market, not of the feed.

Every sampled month with zero-volume bars, and whether the two columns agree:

- `BTCUSDT` 2017-08: 6,974 zero-volume, 6,974 zero-trade, 6,974 both — **agree**
- `ETHUSDT` 2017-08: 5,806 zero-volume, 5,806 zero-trade, 5,806 both — **agree**
- `XEMUSDT` 2020-11: 1,915 zero-volume, 1,915 zero-trade, 1,915 both — **agree**
- `XEMUSDT` 2022-09: 24,486 zero-volume, 24,486 zero-trade, 24,486 both — **agree**
- `XEMUSDT` 2024-06: 3,145 zero-volume, 3,145 zero-trade, 3,145 both — **agree**
- `BTGUSDT` 2021-04: 1,580 zero-volume, 1,580 zero-trade, 1,580 both — **agree**
- `BTGUSDT` 2022-01: 25,878 zero-volume, 25,878 zero-trade, 25,878 both — **agree**
- `BTGUSDT` 2022-10: 15,886 zero-volume, 15,886 zero-trade, 15,886 both — **agree**

### The rate is a property of the instrument, and it is severe on the ones that matter

The majors are clean from 2022 onward — 0.000% on every sampled month. The worst month sampled is `BTGUSDT` 2022-01 at **58.0%**: more than half of that month's minutes contain no trade at all.

| symbol | month | bars | zero-volume | rate |
|---|---|---:|---:|---:|
| `BTGUSDT` | 2022-01 | 44,640 | 25,878 | 57.970% |
| `XEMUSDT` | 2022-09 | 43,200 | 24,486 | 56.681% |
| `BTGUSDT` | 2022-10 | 33,660 | 15,886 | 47.195% |
| `BTCUSDT` | 2017-08 | 21,360 | 6,974 | 32.650% |
| `ETHUSDT` | 2017-08 | 21,360 | 5,806 | 27.182% |
| `XEMUSDT` | 2020-11 | 9,240 | 1,915 | 20.725% |
| `XEMUSDT` | 2024-06 | 23,220 | 3,145 | 13.544% |
| `BTGUSDT` | 2021-04 | 20,746 | 1,580 | 7.616% |

**This is the finding that constrains the study design, not the cleaner collision.** The failure universe — a cross-section screened to include the assets that died — is the only screen in this project that ever caught anything (D140/D180). On exactly those instruments, a 1m time grid is majority-empty. A rule sampled on it would spend most of its bars looking at a price that did not move because nothing traded, which is not the same as a price that did not move.

The two ways out point in opposite directions and neither is free. Restricting intraday work to liquid names reintroduces precisely the survivorship problem D180 identified, where five passes on BTC and ETH turned out to be five readings of two unusually favourable series. Moving off time bars onto volume or dollar bars keeps the failure universe but changes the object being measured, and no result in this project would then be comparable to the daily ones. That choice belongs in a pre-registration, before anything is run.

This collides with the data layer. `clean-v1`'s `non_positive_volume` rule drops any bar with volume at or below zero, and there is no per-rule disable — `clean()` and `validate()` take data and nothing else, and their thresholds are module constants. The only existing lever is `allow_quarantined=True` on `SnapshotStore.load`, which is D143's override. D143 explicitly deferred per-asset-class thresholds, on the grounds that recalibrating a cross-cutting gate from inside a study is how gates stop meaning anything. That deferral is now due.

### The units cross-check D187 did not have

Binance states base volume and quote volume as two separate named columns, so their ratio must be a price inside the bar's own high–low range. That check is run on every bar of every sampled month:

- `BTCUSDT` 2017-08: 14,386/14,386 bars (100.0000%) have quote÷base inside [low, high]
- `BTCUSDT` 2022-02: 40,320/40,320 bars (100.0000%) have quote÷base inside [low, high]
- `BTCUSDT` 2024-11: 43,200/43,200 bars (100.0000%) have quote÷base inside [low, high]
- `BTCUSDT` 2024-12: 44,640/44,640 bars (100.0000%) have quote÷base inside [low, high]
- `BTCUSDT` 2025-01: 44,640/44,640 bars (100.0000%) have quote÷base inside [low, high]
- `BTCUSDT` 2025-02: 40,320/40,320 bars (100.0000%) have quote÷base inside [low, high]
- `BTCUSDT` 2026-07: 44,640/44,640 bars (100.0000%) have quote÷base inside [low, high]
- `ETHUSDT` 2017-08: 15,554/15,554 bars (100.0000%) have quote÷base inside [low, high]
- `ETHUSDT` 2022-02: 40,320/40,320 bars (100.0000%) have quote÷base inside [low, high]
- `ETHUSDT` 2024-11: 43,200/43,200 bars (100.0000%) have quote÷base inside [low, high]
- `ETHUSDT` 2024-12: 44,640/44,640 bars (100.0000%) have quote÷base inside [low, high]
- `ETHUSDT` 2025-01: 44,640/44,640 bars (100.0000%) have quote÷base inside [low, high]
- `ETHUSDT` 2025-02: 40,320/40,320 bars (100.0000%) have quote÷base inside [low, high]
- `ETHUSDT` 2026-07: 44,640/44,640 bars (100.0000%) have quote÷base inside [low, high]
- `XEMUSDT` 2020-11: 7,325/7,325 bars (100.0000%) have quote÷base inside [low, high]
- `XEMUSDT` 2022-09: 18,714/18,714 bars (100.0000%) have quote÷base inside [low, high]
- `XEMUSDT` 2024-06: 20,075/20,075 bars (100.0000%) have quote÷base inside [low, high]
- `BTGUSDT` 2021-04: 19,166/19,166 bars (100.0000%) have quote÷base inside [low, high]
- `BTGUSDT` 2022-01: 18,762/18,762 bars (100.0000%) have quote÷base inside [low, high]
- `BTGUSDT` 2022-10: 17,774/17,774 bars (100.0000%) have quote÷base inside [low, high]

D187 was a units error that scaled every market-impact charge by the square root of price and produced two results that looked like findings. Here the ambiguity is removed by the provider rather than by a parameter.

### Signed order flow arrives in the same row

`taker_buy_base` is column 9 of the kline file, so taker sell volume is `volume - taker_buy_base` and the imbalance needs no separate download. The `aggTrades` archives are roughly two orders of magnitude larger for the same span.

- `BTCUSDT` 2017-08: taker buys are 0.4603 of base volume
- `BTCUSDT` 2022-02: taker buys are 0.4963 of base volume
- `BTCUSDT` 2024-11: taker buys are 0.5009 of base volume
- `BTCUSDT` 2024-12: taker buys are 0.4886 of base volume
- `BTCUSDT` 2025-01: taker buys are 0.4892 of base volume
- `BTCUSDT` 2025-02: taker buys are 0.4712 of base volume
- `BTCUSDT` 2026-07: taker buys are 0.4948 of base volume
- `ETHUSDT` 2017-08: taker buys are 0.4777 of base volume
- `ETHUSDT` 2022-02: taker buys are 0.5048 of base volume
- `ETHUSDT` 2024-11: taker buys are 0.5059 of base volume
- `ETHUSDT` 2024-12: taker buys are 0.4969 of base volume
- `ETHUSDT` 2025-01: taker buys are 0.4892 of base volume
- `ETHUSDT` 2025-02: taker buys are 0.4845 of base volume
- `ETHUSDT` 2026-07: taker buys are 0.4999 of base volume
- `XEMUSDT` 2020-11: taker buys are 0.4733 of base volume
- `XEMUSDT` 2022-09: taker buys are 0.5157 of base volume
- `XEMUSDT` 2024-06: taker buys are 0.5435 of base volume
- `BTGUSDT` 2021-04: taker buys are 0.5189 of base volume
- `BTGUSDT` 2022-01: taker buys are 0.5013 of base volume
- `BTGUSDT` 2022-10: taker buys are 0.4930 of base volume

## The first independent check the daily fixture has ever had

Every crypto result in this project rests on one provider. Resampling Binance 1m to UTC days gives a second, genuinely independent measurement of the same days.

| symbol | vs | month | days | min \|diff\| | median | max |
|---|---|---|---:|---:|---:|---:|
| `BTCUSDT` | `BTC-USD` | 2021-05 | 31 | 0.1 bp | 9.6 bp | 97.8 bp |
| `ETHUSDT` | `ETH-USD` | 2021-05 | 31 | 0.1 bp | 14.8 bp | 98.7 bp |

**Reported, not asserted.** These are different instruments — a single-venue `USDT` pair against a multi-venue `USD` index — so agreement at this scale is informative and exact equality would be suspicious. D161's precedent is that a cross-source discrepancy is a finding; a tolerance would hide it.

Volume does **not** reconcile, and should not: the fixture reports global USD notional across all venues where Binance reports base units on one. Both are internally correct and they are not the same quantity — which is the same distinction D187 got wrong in the other direction.

## Perpetuals and funding

| symbol | perp klines | span | funding rate | span |
|---|---:|---|---:|---|
| `BTCUSDT` | 79 | 2020-01 .. 2026-07 | 79 | 2020-01 .. 2026-07 |
| `ETHUSDT` | 79 | 2020-01 .. 2026-07 | 79 | 2020-01 .. 2026-07 |

Funding is a real carry on a perpetual, and the engine already has the slot for it: `CostStack.portfolio_carry_bricks` (D5/D67). Perps are measured here and deferred — spot is the study base, for continuity with the daily fixture.

## Storage, and why the manifest is the thing to commit

The reachable universe holds **6,336.4 MB** of compressed 1m archives. The largest fixture currently committed is **6.7 MB** and the entire `.git` directory is **17.3 MB**.

Committing the bytes would end the immutable-by-diff property rather than extend it. Binance publishes a SHA256 sidecar beside every archive, and the sampled minimum coverage across symbols is **100%** — so the manifest is committable where the data is not.

That is arguably a **stronger** guarantee than committing bytes, not a retreat from one. A hash we compute over data we downloaded attests that we did not change it. A hash the provider published attests to the same thing, is independently verifiable by anyone, and cannot be quietly regenerated by us.

## What this probe does not settle

It measures a provider. It says nothing about whether any intraday rule works, and D163's conclusion needs no return data to survive contact with better data: a rule paying a triple-digit percentage of capital a year in fees cannot be run, however clean the bars are. Going intraday has to mean changing the hypothesis class, not the sampling rate.

The two phases this gates — the S1 terrain sensor re-tested on real intraday volume, and order-flow imbalance measured against a null before anything is built on it — are pre-registered separately, in the usual way, before they run.

---

Probed 2026-08-22T18:28:21.753762+00:00 in 181s · every figure rendered from `binance_probe_summary.json`
