# D193 — The Binance fetcher, a manifest instead of bytes, and a fixture schema that grew a column without moving a snapshot id

**Status:** Committed
**Date:** 2026-08-22
**Category:** Data layer
**Source:** Wiring D190's parser into the data layer, on the assumption of time bars

## Decision

`BinanceDataSource` (`data/binance_source.py`) assembles monthly 1m archives into a
continuous series and conforms to `get_raw_history`, the seam every fetch script uses.
`scripts/fetch_binance_fixture.py` resamples that to **15m** and writes the standard
fixture trio plus a **manifest**. The 1m base is not committed.

Three things are settled here, each because a measurement said so.

## 1. The bar is 15m, and that is what keeps `clean-v1` untouched

D192 left the bar definition open, recording 57.97% empty **1m** bars on `BTGUSDT`
2022-01 and refusing to choose before a pre-registration did. Measured across
aggregations, the problem is a 1m phenomenon:

| instrument-month | 1m | 5m | **15m** | 1h |
|---|---:|---:|---:|---:|
| `BTGUSDT` 2022-01 | 57.97% | 13.83% | **0.97%** | 0.00% |
| `XEMUSDT` 2022-09 | 56.68% | 10.68% | **0.73%** | 0.00% |
| `BTCUSDT` 2017-09 | 22.02% | 3.34% | **0.32%** | 0.00% |

And the sanity gate is silent at 15m on those same worst months — 0 hard violations, 0
move warnings, 0 `spike_and_revert`, with a maximum 15m move of 10.49% against a 60% hard
threshold.

So: **no edit to `clean-v1` or `validate-v1`, no `allow_quarantined`, and D192's and
D143's deferrals both stay unspent.** The freeze path copies
`run_breakout_intraday.freeze` (D160) exactly — `clean()` on prices only, a second
`clean(bars, volumes)` purely to *measure* what the volume rule would have dropped, the
`SystemExit` asserting the price-only pass dropped nothing, and `validate` with volumes so
the empty bars surface as warnings rather than vanishing.

**A silent gate here is true and uninformative, and the record should say so.** D74's
thresholds are daily-equity thresholds; a 60% move in 15 minutes is a many-sigma event, so
the gate would pass almost any intraday series handed to it. The census is the evidence.
The script prints that sentence at the end of every run rather than leaving a clean gate
to be misread as a clean bill of health.

**What was NOT settled** is the bar definition for anything that needs 1m. Order flow does;
S1 may. This decision commits to time bars at 15m because the user asked for the path
built on that assumption, and it is reversible: the source, the manifest and the schema
are frequency-agnostic, and only the resample step changes if a pre-registration picks
volume or dollar bars. That is why aggregation lives in the fetch script and not in the
source.

## 2. The committed artifact is the provider's hash, not the bytes

D191 argued this from a size measurement; this is where it becomes code. The manifest
records `key`, `month`, `sha256` and `size` per archive, where the SHA256 is the one
**Binance published**, not one this repo computed.

Two implementation details carry the whole argument:

**The checksum is re-fetched on every run, including cache hits.** Skipping it to save a
request would be the obvious optimisation and would destroy the guarantee. A cached
archive whose published hash has since changed is precisely the event a manifest exists to
detect; if the check only ran on first download, the detector would be off during every
run that mattered.

**A mismatch raises.** `ChecksumMismatch`, never a warning, and the message distinguishes
a corrupt download from a stale cache. D191's claim is that a published hash is a stronger
guarantee than committed bytes. That is only true if a mismatch stops the run before a
number is computed, so the negative case is tested in both forms.

## 3. The fixture schema grew a column, and no snapshot id moved

Binance states base volume, quote volume and taker-buy volume as three separate named
fields. Carrying one and deriving the others through price is exactly D187. So
`save_fixture_csv` gained an optional `extra_columns` parameter and `SnapshotStore.create`
threads it to `Snapshot.extras`.

**The hazard is not obvious and is worth stating.** `save_fixture_csv` is also how
`SnapshotStore.create` lays down `bars.csv`, and `_hash_payload` hashes those bytes. A
change to the *default* write path would silently renumber every snapshot id in the
project — and a snapshot id is logged with every trial and printed in the header of every
results doc. The provenance of eight studies would have quietly become wrong.

So the extension is opt-in, column order is `sorted()` so bytes cannot depend on dict
ordering, and the inertness is **pinned by test rather than argued in a comment**:
`test_snapshot_store.py` freezes three committed fixtures and asserts their ids against
values recorded before the change.

```
crypto_intraday_1h_raw          88b3e08d666006f7b47f08ba42eaa3bcae5ec484d9a8d3811d1c7240e177a281
crypto_universe_2015_2025_raw   51756f0d66b037982a8fb7d08db68d843fb84e81bf62f51e97688798da90776d
universe_daily_2015_2024_raw    b1e9424d04ca988264a3421ad337c6dd8e69d96c2e4aa985402821a9110eb1ad
```

**The `volume` column stays quote notional.** Every crypto fixture here is quote notional,
`CostTier.volume_units` defaults to it, the liquidity screen bakes USD into its error
string, and D189's S1 sensor ran on it — so the terrain re-test stays comparable.
`base_volume` and `taker_buy_base` are the extras. The extension is additive in meaning as
well as in bytes.

`trades` is carried through the source but not into the fixture. It is there because it is
the only independent check on a zero-volume bar: D192's criterion is that zero volume is
droppable only where it **disagrees** with the trade count, and inferring trades from
volume would make that test answer itself. The fetch script **refuses to build a fixture**
on a symbol where the two disagree.

## 4. A second provider defect: fourteen days of skewed clock, found by the grid guard

D190 admitted this archive after measuring it as high-fidelity. Building on it turned up a
defect the probe's stratified sample could not have seen, and D161's bucket-alignment
guard caught it on the first real run:

> `15m bucket at 2017-12-05 slot 0 starts at 2017-12-05 00:00:20.799000, expected
> 2017-12-05 00:00:00 — buckets are not aligned to 00:00 UTC (D161)`

**From 2017-12-04 06:00:20.799 to 2017-12-18 10:00:20.799, every `BTCUSDT` 1m bar is
stamped exactly 20.799 seconds past the minute.** A constant offset, not jitter — 20,401
bars. `ETHUSDT` carries 20.810s across the same window, and a second episode at 14.789s /
14.800s runs into February 2018. Seventeen affected days per symbol in total, 21,602 bars.
Binance's kline generator was running on a skewed clock for a fortnight, through the
December 2017 top.

**The bars are not snapped to the grid.** The OHLC of a bar labelled `00:00:20.799` could
describe `[00:00, 00:01)` or `[00:00:20.8, 00:01:20.8)`, and nothing in the archive says
which. Rewriting the timestamp would be inventing the answer — the sin `clean-v1` avoids
by dropping and reporting rather than correcting (D25). `offgrid_census` reports the days
and the distinct offsets; the fetch script decides what to do with them.

### And the fix for it was wrong the first time, which the gate caught

The obvious response — drop the off-grid days like any other bad day — **quarantined the
snapshot**, and the reason is worth recording because it is a property of D161's drop
policy rather than of this provider:

```
BTCUSDT  2017-12-19 00:00:00  close 11165.41 -> 18865.0 (+69.0%)
ETHUSDT  2017-12-19 00:00:00  close   460.3  ->   775.0 (+68.4%)
```

Neither is a bad print and neither is a real 15-minute move. Removing
2017-12-04..2017-12-18 made 2017-12-03 and 2017-12-19 **adjacent**, so fifteen days of the
December 2017 rally arrived as one bar. **The drop policy manufactured the violation.**

That artifact is latent in the existing 1h fixture too — it drops 5–6 days for BTC/ETH
(D161) — and has simply never fired, because an isolated one-day hole does not move price
60%. It fires here because the hole is a fortnight long and lands on the most violent
rally in the instrument's history.

So the rule is split by the shape of the hole, which is a fact about the cause rather than
a tuned threshold: **a clock skew persists for weeks, a missing minute is isolated.**
Isolated short days are dropped and the series continues, exactly as the 1h fixture
already does. An off-grid run is not stitched across — the series is **truncated to start
after the last off-grid day**, costing BTC and ETH 170 otherwise-good days each and about
six months of 2017–18 history. Losing real months is the honest price of not fabricating
an adjacency that every downstream return, sigma and channel would silently consume.

After truncation: **0 hard violations, snapshot not quarantined, no override.**

The general lesson is the one this project keeps relearning in new costume: a data
*policy* can create the defect it is meant to remove, and the only reason this one was
visible is that a guard compared consecutive bars and said something impossible had
happened.

## 5. Gzipped fixtures are now byte-reproducible

Found while checking determinism: `gzip.open` stamps the current time into the gzip
header, so re-running a fetch produced a whole-file diff even when not one row had
changed — 25 MB of noise. Decompressed content was identical; only the header's `mtime`
field moved.

Writes now pin `mtime=0` and omit the embedded filename, so the compressed bytes are a
function of the content and nothing else. **A diff that always appears is a diff that
stops being read**, and immutable-by-diff (D70/D24) is the entire reason a fixture is
committed rather than re-fetched. Reads are untouched, every committed fixture still
loads, and snapshot ids are unaffected because `SnapshotStore` writes `bars.csv`
uncompressed.

## The universe screen is deliberately not run

`apply_policy` / `DEFAULT_POLICY` is not applied to this fixture, and the meta says so in
prose rather than the call simply being absent. Both of its data-dependent screens are
per-**bar** medians calibrated on **daily** bars:

- `min_median_daily_volume_usd = 5_000_000` against a median per-15m-bar notional
- `min_median_abs_daily_return = 0.005` — the stablecoin peg screen — against a median
  per-15m-bar absolute log return, which for a real coin sits far below 0.5%

Applied verbatim, **the peg screen alone would exclude every symbol in the universe**. A
daily screen pointed at intraday bars is not a conservative choice; it is a broken one.
Recalibrating it is a framework change five studies depend on, so it is named here and
left for whoever needs it, in D143's and D160's manner.

## Three hazards found while planning, none triggered here

None of these is a defect in this change. All three are live for the next intraday study,
and all three are silent — which is why they belong in the record rather than in a comment
someone would have to already be reading.

- **`calibrate_impact_params` (`costs/calibration.py:64-87`) keeps exact `0.0` volumes and
  feeds them to `statistics.fmean`**, so ADV is understated in proportion to the empty-bar
  rate. Worse, `adv_shares` is a **per-bar** mean while an order quantity is a full
  position: hand it 15m bars and participation is overstated by 96×. This is D187's cousin
  — a units error in a cost model that no other check can see.
- **`VolumeConfirmationFilter.accepts` (`strategies/breakout.py:907-918`) divides by
  `self.window` rather than the count of non-zero bars**, so its threshold collapses
  toward zero as the empty rate rises. It degrades silently on exactly the thin
  instruments it exists to protect against; it never fails.
- **`validate`'s `volume_spike` check self-disables** wherever the trailing 20-bar median
  is `0.0`, which on a majority-empty grid is most of the series. It appears to run.

## Consequences

- `dedupe_seam` finally has a caller. Monthly archives are concatenated at the seam, which
  is precisely the duplicate `align_bars` raises on (D99) and `validate-v1` counts as a
  hard violation; the drop count reaches the report rather than vanishing.
- D161's day-level drop policy is reused rather than reinvented: `resample` refuses to
  emit a bucket short of its full complement, and 1m archives do have missing minutes, so
  a UTC day the provider served short is dropped entirely and counted.
- A re-run with a warm cache touches the network only for listings and checksums, which is
  what makes the fixture reproducible without re-downloading gigabytes.
