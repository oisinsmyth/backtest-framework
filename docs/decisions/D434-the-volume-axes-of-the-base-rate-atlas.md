# D434 — the volume axes of the base-rate atlas

**A MEASUREMENT** (D280's class; D392's form): what a random event set earns on this universe when
it is conditioned on **volume**, and the p95 of that. **It scores no strategy, proposes no rule,
admits nothing (R15). Committed before the runner exists (R8).** D400–D433 used, D407–D410 and
D390–D399 reserved.

## 1. Why

D392 gave the atlas three axes — price, volatility, momentum — because three lines had died on
them. The departure-zone line (D412–D433) died on a fourth thing it never measured: it used volume
only as a liquidity floor, and the one lever that moved cost (dollar volume, D432) was never a base
rate. The principal has restricted the next supply/demand search to **price and volume at any
timeframe**, and PICKUP 0d2's diagnosis stands — every closed map was a function of the price
path; volume is the one thing in OHLCV that is not. **Before any volume construction is built, the
atlas must say what a random trade earns conditioned on volume alone**, so a construction is read
against that and not against zero.

## 2. The panel and what it can and cannot express

D392's panel (`d348_prep.prep`, the studies' own kernel via `run_d359`, next-open fill, cap exit,
hedged by the floored market) carries `CLOSE`, `VOL`, `DV` and the score `rvol21`. **It carries no
high/low/open.** "Result" is therefore the close-to-close move in vol units, not the true range;
the record says so wherever range would have been the natural quantity.

## 3. The features — all causal at the close of bar `t`, all from `VOL`, `DV`, `CLOSE`, `rvol21`

```
ADV20    mean(VOL[t-20..t-1])          ADV5/ADV60 likewise      r_t = log CLOSE_t - log CLOSE_{t-1}
rv       VOL_t / ADV20                                       relative volume
ef       rv / (|r_t| / rvol21_t + 0.1)                        effort per unit result; high = much volume, little move
vt       ADV5 / ADV60                                        participation trend
uv       sum(VOL over up-close days, t-19..t) / sum(VOL, t-19..t)   up-volume share (accumulation vs distribution)
dv       DV_t (D347's trailing dollar volume)                liquidity
ret20    log CLOSE_t - log CLOSE_{t-20}                      for the divergence quadrants
```

**Pools** (cross-sectional terciles per bar among eligible names, D392's rule, unless marked absolute):
```
rv_lo / rv_mid / rv_hi          ef_lo / ef_mid / ef_hi          vt_lo / vt_mid / vt_hi
uv_lo / uv_mid / uv_hi          dv_lo / dv_mid / dv_hi
rv_x3        ABSOLUTE: VOL_t >= 3 x ADV20                                     (the volume-shock day)
cx_dn        ABSOLUTE: rv >= 3 and r_t <= -2 x rvol21                         (the down climax)
cx_up        ABSOLUTE: rv >= 3 and r_t >= +2 x rvol21                         (the up climax)
pv_up_rise / pv_up_fall / pv_dn_rise / pv_dn_fall
             ret20 above/below the bar's cross-sectional median x vt above/below its median (divergence quadrants)
```
22 pools. Each: long and short, n ∈ {3,000, 10,000, 30,000} (D392's conditional counts), cap 20,
200 draws, D392's seed scheme, [E] every draw on the eligible mask, [SE] every p95 with its
bootstrap SE, [P] persisted per cell. A pool smaller than n records EMPTY, as D392 does.

**Cost, projected from `data/d392_calibration.json`:** 0.120 / 0.198 / 0.394 s per draw at cap 20
→ 132 cells ≈ 105 min serial. Run as **two processes on disjoint halves of the pool list**, each to
its own artefact (`data/d434_atlas_volume_a.json`, `_b.json`), ≈ 55 min wall, ~1 GB each.

**Assertions:** `[K]` D392's own kernel check (score_once == run_d359's path) re-run; `[T]` every
tercile triple partitions the eligible cells of every bar it is defined on; `[C]` **causality** —
recomputing every feature with `VOL` and `CLOSE` perturbed at bars > t leaves the pool masks at bar
t unchanged, and perturbing bar t itself changes them (a check that fires when broken); `[E]`,
`[SE]`, `[P]` as D392.

## 4. Predictions — the spread of the median random long, top minus bottom tercile, at n=30,000

D392's spreads were price 36.8, momentum 32.2, volatility 12.2 bp. Held at LOW–MODERATE:

- **X-a** `rv` (relative volume): **+8 to +20** — a random long after a high-volume day earns more
  over 20 bars than after a quiet one (the high-volume return premium). `rv_x3` above `rv_hi`.
- **X-b** `cx_dn` long **+20 to +50** at p50 (a 3-vol-unit down day on 3× volume mean-reverts);
  `cx_up` long **−10 to −30**. Both pools are small (EMPTY at 30,000; present at 3,000).
- **X-c** `ef` (absorption): spread **inside ±10** — effort-vs-result carries no base rate on its
  own; if it does, it is the one surprise this record could hold.
- **X-d** `vt` (participation trend): **+5 to +15**, rising volume helps a random long.
- **X-e** `uv` (up-volume share): **+10 to +25** — it is momentum measured by volume, and
  momentum's spread is 32.
- **X-f** `dv`: `dv_lo` ≈ `price_lo` (+15 to +25 at p50), `dv_hi` near zero: the liquidity axis is
  the price axis wearing a different coat.
- **X-g** divergence quadrants: `pv_dn_rise` (price down, volume rising) is the worst long
  quadrant, `pv_up_rise` the best; the four span **20 to 40 bp**.

## 5. Not in scope

Any strategy; any rule; any holdout. The atlas is a prior. Thirty-fourth look by object on this
universe, and a measurement.
