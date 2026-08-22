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
