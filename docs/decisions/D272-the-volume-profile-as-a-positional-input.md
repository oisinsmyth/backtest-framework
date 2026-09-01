# D272 — The volume profile as a positional input

**Status:** PRE-REGISTERED. Committed **before the run**. Nothing here is a result.
**Date:** 2026-09-01
**Area:** Strategy research · **personal track**

**Two stages. (a) independence, then (b) calibration, and (b) runs only if (a) passes.**

---

## The question

[D268](D268-score-independence.md) found nine price scores collapsing to **2.87 effective
inputs**. [D270](D270-volume-structure-retest.md) added volume and reached **5.25 of 16** — but
found relative volume is mostly a **volatility** selector: it widens the forward distribution
from 58.8 to 77.2 bp sd and shifts its mean only **+2.15 bp** against a 4.00 bp cost bar.

**A volume profile measures something neither family does: WHERE volume sits in price space,
relative to where price is now.** That is positional, not magnitude. `rel_vol` says *how much*
is trading; `dist_to_HVN` says *what the current price is standing on*.

**Whether that is a genuinely separate input is a measurement, and it is stage (a).**

---

## DISCLOSURE — this sensor has a programme behind it, and it closed

`VolumeProfileSensor` was built and tested by the terrain programme:
[D189](D189-the-s1-terrain-sensor-and-its-null.md) on daily crypto bars,
[D194](D194-the-s1-sensor-re-tested-at-15m.md) on exchange-native 15-minute Binance volume.
[`TERRAIN_RESULTS.md`](../../TERRAIN_RESULTS.md) closes it:

> **Closed:** price-derived terrain as a source of directional or reversal signal on this data.
> **S1 at any resolution (D194).**

**And the mechanism it found is not crypto-specific:**

> Inventory accumulates below price exactly when price has been *falling into* it, so trading
> it fades a decline. **Fading lost in every form measured** — short leg worse than long in
> 16 of 16 cells, 16 of 16, 8 of 8, **11 years of 11**. The map's local structure is not
> uninformative about direction; **it is reliably wrong.** Reading it better made the answer
> worse.

### On the ledger, and why this record starts a new one

TERRAIN_RESULTS says *"anything that reuses these sensors inherits the count"* — **259 looks.**
It also labels that row **"Total on one hypothesis"**, and closes with:

> A different data source, a different claim, or a genuinely new construction **starts a new
> document and a new ledger, with this one disclosed.**

**This record has all three** — US single-name equities rather than crypto, *independence of an
input* rather than *directional signal from a map*, and a positional score rather than a
reversal rule. **Multiplicity correction applies to looks at the same hypothesis; inheriting
looks spent on a different one over-corrects and would make any finding here unfalsifiable by
construction.**

**So: new ledger, terrain disclosed.** The 259 is not summed in — but the terrain *evidence* is
load-bearing where it belongs, in the predictions below, because stage (b) is adjacent enough
that its likely sign should be declared in advance rather than explained afterwards.

---

## Construction — every constant from the sanctioned set, none swept

The sensor validates its own parameters and raises on anything outside them, calling a third
value *"an unregistered search"*. Both values below are already in those sets.

| | value | why this one |
|---|---|---|
| `lookback_bars` | **180** | `LOOKBACK_BARS` allows 90 / 180 / 8,640 / 17,280. At 26 bars per session 180 bars is **≈ 7 sessions** — proportionate to an 8-bar forward horizon. 8,640 would be 332 sessions, a 16-month map against a two-hour question |
| `bucket_atr` | **0.5** | `BUCKET_ATR` allows 0.25 / 0.5. D189 and D194's primary |
| `atr_window` | **182 bars** | calendar-matched to the lookback, exactly as D194 matched its windows to D189 so that resolution was the only variable |
| `volume_units` | **`shares`** | the fixture's volume column is share count, split-adjusted. Reading a share column as notional is the D187 defect the sensor's own validator exists to prevent |
| rebuild cadence | **every 26 bars** (once per session) | a 7-session map does not need rebuilding intra-session. D194's precedent is a periodic rebuild, not a per-bar one |

**Fixture:** `single_name_intraday_15m_panel.csv.gz` — the same 8 names, 55,004 bars. No fetch.

### The four scores, fixed here

| score | construction |
|---|---|
| `dist_hvn` | signed `(price − nearest HVN) / bucket_width` |
| `dist_lvn` | signed `(price − nearest LVN) / bucket_width` |
| `mass_here` | mass at the current price, as a percentile of the profile's occupied mass |
| `mass_imbalance` | `(mass above price − mass below price) / total` |

**R9.** The profile at a session's first bar is built with `index` = the previous session's last
bar, and the score at bar `t` reads the price at `t−1`. No bar is used that a rule could not
have seen. **`density()` slices everything after `index` away before any arithmetic touches
it**, so this is a property of the sensor's code path rather than of my calling convention.

---

## Stage (a) — independence

Run D268's instrument over **17 scores**: 9 price + 4 volume + 4 profile.

| | standard |
|---|---|
| **A1** | **At least one profile score has `max abs(rho) < 0.5` against ALL thirteen existing scores** |
| **A2** | **Effective independent scores rises by ≥ 0.5** over the same 13 measured without the profile family |

**Both.** A2 alone is satisfiable by adding noise; A1 requires a specific score to be distinct.

**The two-sided controls from D270 are reused unchanged** — `ctrl_blend` (half a price score,
**must fail**) and `ctrl_noise` (seeded random, **must pass**). Either misbehaving voids the run.
They are instrumentation and are not eligible to pass.

## Stage (b) — calibration

**Runs only on scores clearing A1.** D267's hurdles unchanged: **M1** monotone quintiles,
**M2** extreme quintile ≥ `2c`, **M3** best-of-N shuffle floor with one shared draw, at
**H = 8 bars**.

**M3 is computed for every eligible score regardless of M1 and M2.** D270's runner
short-circuited and skipped it, which is the R6 defect D230 named; it is not repeated.

---

## Predictions

| | prediction | confidence |
|---|---|---|
| **X-a** | **At least one profile score clears A1.** Position in price space is not a function of the price-path scores, and D270 showed volume magnitude already is not | **moderate-high** |
| **X-b** | **No profile score clears M1–M3.** The terrain programme closed the directional claim four separate ways and its mechanism transfers unchanged to equities | **high** |
| **X-c** | **If `dist_hvn` shows any relationship, it will favour CONTINUATION, not reversal** — price near a high-volume node will precede further movement in the direction it arrived from. This is TERRAIN's mechanism restated: *"inventory accumulates below price exactly when price has been falling into it."* **Declared so the sign cannot be re-read afterwards**, which is exactly what D263 demonstrated the value of | **moderate** |
| **X-d** | **Both controls behave** | **high** |

**X-c is the one that carries the terrain evidence.** It is not a ledger entry; it is a prior,
and stating it in advance is what makes the terrain programme's 259 looks useful here rather
than merely disclosed.

---

## Stop

**If (a) fails, the volume profile is closed as an input** and the consensus proposal closes with
it — no fifth score, no second lookback, no alternative bucket width.

**If (a) passes and (b) fails, the profile is INDEPENDENT BUT UNINFORMATIVE.** That would be the
**third** such finding — after volume in D270 and the price library in D267 — and three of them
in a row is itself the result: *inputs are available; edge at this horizon is not.*

**Nothing is promoted under any outcome.** R8 governs, and a passing score would still need its
own out-of-sample test on names this fixture has never touched.

---

## Ledger

| count | N |
|---|---:|
| fresh — 4 profile scores × 3 strata | **12** |
| carried from D270 | 46,209 |
| **total** | **46,221** |

**Disclosed and NOT summed: the terrain programme's 259 looks**, spent on a different hypothesis
(directional signal from the map, on crypto). Recorded here so the decision to keep them separate
is visible and arguable rather than silent.
