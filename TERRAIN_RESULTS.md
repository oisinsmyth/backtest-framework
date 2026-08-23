# TERRAIN_RESULTS.md — the terrain programme's ledger

**Append-only.** Every work package adds a dated section; nothing above is rewritten. This
is the single results ledger `TERRAIN_IMPLEMENTATION_PLAN.md` requires, and it carries the
multiplicity count that feeds the deflated Sharpe if the programme ever reaches WP7.

---

## WP1 + WP2 — the S1 volume-profile sensor and its null test

**Produced:** 2026-08-22 ·
**Reproduce:** `uv run python scripts/run_terrain_s1.py` (offline, deterministic)

### What was built

`VolumeProfileSensor` (S1) and the reusable null-test harness, plus the sensor interface
every later sensor must implement. Data: `crypto_daily_2015_2025_raw.csv.gz`, volume declared as
**quote_notional** (D187 — a crypto fixture's volume column is quote-currency notional,
so this is a dollars-traded-at-price map).

| Symbol | From | To | Bars |
|---|---|---|---|
| `BTC-USD` | 2015-01-01 | 2025-12-30 | 4,017 |
| `ETH-USD` | 2017-11-09 | 2025-12-30 | 2,974 |

**S1 is built on DAILY bars, deviating from the spec's stated preference for intraday.** The
1h fixture reports zero volume on half its bars — the known yfinance defect for crypto — so
a volume-at-price map built there would be missing half its mass, non-randomly. Daily volume
is complete over eleven years against the intraday fixture's two, and it is the frequency the
accepted baselines trade at, which is what WP5 has to annotate. The spec wants intraday for
sharpness, not necessity.

### The verdict

**S1 FAILS its null on both symbols** (`BTC-USD` FAIL, `ETH-USD` FAIL).

The stop condition in `TERRAIN_IMPLEMENTATION_PLAN.md` applies: the terrain programme stops here and is reported as a negative result. Volume-profile levels do not beat levels scattered at random over the same range.

### The primary configuration, both symbols

**`BTC-USD`** — 353 touches over 191 rebuilds, 3.9 levels each; 500 null draws.

| Metric | Real | Null mean | Null 90% | Percentile | p | Tail |
|---|---|---|---|---|---|---|
| P(reversal | touch) | +0.3768 | +0.3835 | [+0.3415, +0.4310] | 41.4th | 0.5868 | high |
| Bars to traverse | +4.3088 | +4.2891 | [+4.1623, +4.4120] | 58.8th | 0.4132 | high |
| Realized vol after / before | +1.1962 | +1.1932 | [+1.0861, +1.3062] | 52.6th | 0.5269 | low |

**`ETH-USD`** — 255 touches over 139 rebuilds, 3.9 levels each; 500 null draws.

| Metric | Real | Null mean | Null 90% | Percentile | p | Tail |
|---|---|---|---|---|---|---|
| P(reversal | touch) | +0.3529 | +0.3736 | [+0.3160, +0.4286] | 26.0th | 0.7425 | high |
| Bars to traverse | +4.3647 | +4.2841 | [+4.1276, +4.4293] | 80.8th | 0.1936 | high |
| Realized vol after / before | +1.1789 | +1.1387 | [+1.0458, +1.2409] | 76.0th | 0.7605 | low |

Primary: lookback 180d, bucket 0.5 ATR, touch band k=0.5. Each metric's tail was declared before the run — `MetricSpec.direction` exists so the direction is the hypothesis rather than something chosen once the numbers are in.

### Sensitivity — every other configuration in the stated sets

| Symbol | Lookback | Bucket (ATR) | k | Touches | Verdict | Metrics beaten |
|---|---|---|---|---|---|---|
| `BTC-USD` | 180 | 0.25 | 0.5 | 630 | fail | none |
| `BTC-USD` | 180 | 0.25 | 1.0 | 722 | fail | none |
| `BTC-USD` **(primary)** | 180 | 0.5 | 0.5 | 353 | fail | none |
| `BTC-USD` | 180 | 0.5 | 1.0 | 429 | fail | none |
| `BTC-USD` | 90 | 0.25 | 0.5 | 590 | fail | none |
| `BTC-USD` | 90 | 0.25 | 1.0 | 680 | fail | none |
| `BTC-USD` | 90 | 0.5 | 0.5 | 389 | fail | none |
| `BTC-USD` | 90 | 0.5 | 1.0 | 462 | fail | none |
| `ETH-USD` | 180 | 0.25 | 0.5 | 416 | fail | none |
| `ETH-USD` | 180 | 0.25 | 1.0 | 489 | fail | none |
| `ETH-USD` **(primary)** | 180 | 0.5 | 0.5 | 255 | fail | none |
| `ETH-USD` | 180 | 0.5 | 1.0 | 280 | fail | none |
| `ETH-USD` | 90 | 0.25 | 0.5 | 418 | fail | none |
| `ETH-USD` | 90 | 0.25 | 1.0 | 480 | fail | none |
| `ETH-USD` | 90 | 0.5 | 0.5 | 284 | fail | none |
| `ETH-USD` | 90 | 0.5 | 1.0 | 311 | fail | none |

### Multiplicity ledger

| | |
|---|---|
| Configurations run | 16 |
| Metrics per configuration | 3 |
| **Total looks** | **48** |

Two symbols x two lookbacks x two bucket widths x two touch bands, on three metrics. **A 5%
test taken 48 times is not a 5% test**, which is why one
configuration was named before the run and the rest are sensitivity. Every row counts here
regardless — retired and failed configurations included — because the deflated Sharpe at WP7
has to pay for all of them.

### Standing caveats

1. **The null matches count and range, not where price lingered.** A high-volume node is by
   construction a price the market spent time at, so price is more likely to be near one
   than near a uniformly-placed level. The pseudo-levels match the real map's count and span
   but cannot match that property without destroying the thing being tested. **If S1 passes,
   this confound is the first thing to check, not the last.**
2. **Daily bars are a coarse map.** A 0.5-ATR bucket on BTC is hundreds to thousands of
   dollars wide; intraday data would sharpen it and is unavailable at usable quality.
3. **A pass here is not evidence the terrain model works.** It is evidence that one sensor's
   levels beat randomly placed ones on reaction statistics. The ladder's actual go/no-go is
   WP5 — features on the existing trade population — which this phase does not touch.

---

## WP2 re-run — S1 on exchange-native 15m volume (D194)

**Produced:** 2026-08-23 · **Reproduce:** `uv run python scripts/run_terrain_s1_intraday.py` (offline, deterministic)

Pre-registered in `D194-the-s1-sensor-re-tested-at-15m.md (commit d2cc20e)`, before this run existed. Data: `crypto_binance_15m_raw.csv.gz`, volume declared as `quote_notional`. Every window calendar-matched to D189 at 96 bars/day — lookback 8640/17280 bars, ATR 1920, horizon 480, rebuild every 1920. `n_sims` 500, seed 0.

### The bucket-span census, reported before the verdict

A bar narrower than a bucket puts its whole volume at one price, which is a close-price histogram wearing a volume label. D194 pre-committed to reporting this first, because a map that has degenerated this way looks exactly like a real one.

| symbol | median span | mean span | single-bucket share | bars censused |
|---|---:|---:|---:|---:|
| `BTCUSDT` | 4.0 | 5.33 | 1.4% | 354,240 |
| `ETHUSDT` | 4.0 | 5.39 | 1.3% | 354,240 |
| `XEMUSDT` | 4.0 | 5.72 | 2.7% | 353,506 |
| `BTGUSDT` | 4.0 | 5.73 | 3.1% | 351,362 |

### The primary configuration, against D189

| | D189 (daily) | D194 (15m) |
|---|---|---|
| **BTCUSDT** touches | 353 | 13,782 |
| P(reversal \| touch) real | +0.3768 | +0.6022 |
| null mean | +0.3835 | +0.5955 |
| **real − null** | -0.0067 | **+0.0068** |
| percentile | 41.4th | 89.6th |
| **ETHUSDT** touches | 255 | 13,664 |
| P(reversal \| touch) real | +0.3529 | +0.5879 |
| null mean | +0.3736 | +0.5855 |
| **real − null** | -0.0206 | **+0.0024** |
| percentile | 26.0th | 66.4th |

### The span-matched daily control

D189's exact primary configuration on daily bars, restricted to 2018-02-12 – 2025-12-31 — the overlap with the 15m fixture. Without it, any difference between D189 and D194 is confounded with a different decade.

| symbol | bars | span | touches | real | null mean | real − null | pct |
|---|---:|---|---:|---:|---:|---:|---:|
| `BTC-USD` | 2,879 | 2018-02-12 .. 2025-12-30 | 262 | +0.3511 | +0.3773 | -0.0261 | 22.4 |
| `ETH-USD` | 2,879 | 2018-02-12 .. 2025-12-30 | 248 | +0.3710 | +0.3706 | +0.0004 | 51.2 |

### The bar, as pre-registered

| condition | requirement | result |
|---|---|---|
| 1. Statistical | beats its null on BOTH symbols | **FAIL** |
| 2. Effect size | real − null ≥ 0.045 on both | **FAIL** |
| 3. Breadth | effect in > half the grid | **FAIL** |
| **Overall** | all three | **FAIL** |

The effect-size floor is the half-width of D189's own BTC null interval. The effect had to be large enough that D189 would have seen it.

### Every configuration

| configuration | touches | real | null mean | delta | pct | p | median span |
|---|---:|---:|---:|---:|---:|---:|---:|
| `BTCUSDT|17280|0.25|0.5` | 26,783 | +0.6017 | +0.5954 | +0.0064 | 97.0 | 0.032 | 4.0 |
| `BTCUSDT|17280|0.25|1.0` | 30,187 | +0.6488 | +0.6387 | +0.0101 | 99.4 | 0.008 | 4.0 |
| `BTCUSDT|17280|0.5|0.5` | 13,782 | +0.6022 | +0.5955 | +0.0068 | 89.6 | 0.106 | 3.0 |
| `BTCUSDT|17280|0.5|1.0` | 15,462 | +0.6442 | +0.6389 | +0.0052 | 82.6 | 0.176 | 3.0 |
| `BTCUSDT|8640|0.25|0.5` | 27,687 | +0.6027 | +0.5973 | +0.0054 | 94.6 | 0.056 | 4.0 |
| `BTCUSDT|8640|0.25|1.0` | 30,697 | +0.6481 | +0.6396 | +0.0085 | 98.4 | 0.018 | 4.0 |
| `BTCUSDT|8640|0.5|0.5` | 14,142 | +0.6032 | +0.5975 | +0.0057 | 87.4 | 0.128 | 3.0 |
| `BTCUSDT|8640|0.5|1.0` | 15,646 | +0.6468 | +0.6391 | +0.0077 | 90.4 | 0.098 | 3.0 |
| `BTGUSDT|17280|0.25|0.5` | 3,546 | +0.5790 | +0.5811 | -0.0021 | 43.2 | 0.569 | 5.0 |
| `BTGUSDT|17280|0.25|1.0` | 4,116 | +0.6256 | +0.6170 | +0.0086 | 76.6 | 0.236 | 5.0 |
| `BTGUSDT|17280|0.5|0.5` | 1,417 | +0.5695 | +0.5808 | -0.0113 | 25.0 | 0.750 | 3.0 |
| `BTGUSDT|17280|0.5|1.0` | 1,673 | +0.6169 | +0.6179 | -0.0010 | 46.4 | 0.537 | 3.0 |
| `BTGUSDT|8640|0.25|0.5` | 4,411 | +0.6071 | +0.5958 | +0.0113 | 92.0 | 0.082 | 4.0 |
| `BTGUSDT|8640|0.25|1.0` | 5,154 | +0.6348 | +0.6220 | +0.0128 | 93.6 | 0.066 | 4.0 |
| `BTGUSDT|8640|0.5|0.5` | 1,916 | +0.6054 | +0.5975 | +0.0080 | 70.8 | 0.293 | 3.0 |
| `BTGUSDT|8640|0.5|1.0` | 2,241 | +0.6265 | +0.6235 | +0.0030 | 58.2 | 0.419 | 3.0 |
| `ETHUSDT|17280|0.25|0.5` | 27,408 | +0.5879 | +0.5853 | +0.0026 | 77.4 | 0.228 | 4.0 |
| `ETHUSDT|17280|0.25|1.0` | 30,700 | +0.6287 | +0.6277 | +0.0010 | 59.4 | 0.407 | 4.0 |
| `ETHUSDT|17280|0.5|0.5` | 13,664 | +0.5879 | +0.5855 | +0.0024 | 66.4 | 0.337 | 3.0 |
| `ETHUSDT|17280|0.5|1.0` | 15,316 | +0.6276 | +0.6283 | -0.0006 | 46.2 | 0.539 | 3.0 |
| `ETHUSDT|8640|0.25|0.5` | 26,566 | +0.5862 | +0.5855 | +0.0007 | 59.0 | 0.411 | 4.0 |
| `ETHUSDT|8640|0.25|1.0` | 29,607 | +0.6265 | +0.6260 | +0.0005 | 53.8 | 0.463 | 4.0 |
| `ETHUSDT|8640|0.5|0.5` | 13,431 | +0.5861 | +0.5861 | -0.0000 | 50.2 | 0.499 | 3.0 |
| `ETHUSDT|8640|0.5|1.0` | 15,100 | +0.6237 | +0.6270 | -0.0033 | 28.8 | 0.713 | 3.0 |
| `XEMUSDT|17280|0.25|0.5` | 20,089 | +0.5996 | +0.5983 | +0.0013 | 57.8 | 0.423 | 5.0 |
| `XEMUSDT|17280|0.25|1.0` | 22,601 | +0.6422 | +0.6386 | +0.0036 | 77.4 | 0.228 | 5.0 |
| `XEMUSDT|17280|0.5|0.5` | 8,216 | +0.5944 | +0.5948 | -0.0003 | 46.6 | 0.535 | 3.0 |
| `XEMUSDT|17280|0.5|1.0` | 9,049 | +0.6307 | +0.6361 | -0.0054 | 22.8 | 0.772 | 3.0 |
| `XEMUSDT|8640|0.25|0.5` | 17,334 | +0.5962 | +0.5978 | -0.0016 | 37.0 | 0.631 | 4.0 |
| `XEMUSDT|8640|0.25|1.0` | 19,366 | +0.6397 | +0.6423 | -0.0026 | 30.4 | 0.697 | 4.0 |
| `XEMUSDT|8640|0.5|0.5` | 7,830 | +0.5983 | +0.5980 | +0.0004 | 53.8 | 0.463 | 3.0 |
| `XEMUSDT|8640|0.5|1.0` | 8,805 | +0.6353 | +0.6400 | -0.0046 | 28.2 | 0.719 | 3.0 |

Traversal in the payload is in 15-minute bars; divided by 96 it is directly comparable to D189's 4.31 (BTC) and 4.36 (ETH) days.

### Multiplicity ledger — cumulative

| | |
|---|---|
| D189 looks | 48 |
| This run, configurations | 32 |
| This run, looks | 96 |
| Daily control looks | 3 |
| **Cumulative looks on one hypothesis** | **147** |

Never reset. D189's failures count — the question has not changed, and the plan's own rule is that retired and failed items still count.

