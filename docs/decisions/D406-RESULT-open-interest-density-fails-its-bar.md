# D406 RESULT — open-interest density at spot fails its bar, and the direction is right

**Status:** SCREENED AND CLOSED. The bar was committed in `478fb72` **before** this ran.
**Date:** 2026-09-09

**The ledger does not move. Nothing was admitted to any book. No holdout was read.**

Cost: 7,560 requests (124 min of paced pulling) plus 36 s of screening.

---

## 1. The verdict

Primary cell — `w = 1.0` daily sigma, `h = 63` bars, outcome `|forward move| / sigma`:

```
density quintile      Q1      Q2      Q3      Q4      Q5
|move| / sigma     0.7728  0.7567  0.7736  0.7260  0.7325
n                    1198    1183    1190    1178    1209
```

| | condition | outcome |
|---|---|---|
| **T1** | monotone DECREASING across Q1→Q5 | **FAIL** — Q3 rises above Q2, Q5 above Q4 |
| **T2** | Q1 − Q5 ≥ 10% of pooled mean | **FAIL** — +0.0403 against a bar of 0.0752, **54% of it** |
| **T3** | T1 survives within volatility terciles | **FAIL** — 0 of 3 monotone |

```
vol lo    0.8973  0.9410  0.9118  0.8798  0.8603    spread -0.0370
vol mid   0.7194  0.7088  0.6633  0.6337  0.7036    spread -0.0158
vol hi    0.6598  0.6155  0.6060  0.6368  0.6280    spread -0.0318
```

**D406 CLOSES.** No pre-registration is written and no further rung is pulled.

---

## 2. The honest part: the direction is right everywhere

Unlike D263 — where *"the largest spread has the wrong sign"* — **every spread here points the way
the record declared in advance.** All three windows and all three volatility terciles:

```
w = 0.5   spread -0.0507        vol lo   -0.0370
w = 1.0   spread -0.0403        vol mid  -0.0158
w = 2.0   spread -0.0759        vol hi   -0.0318
```

Six of six negative, in the declared direction, and **the tercile spreads stay negative — so this is
not purely the volatility confound T3 was written to catch.** Something weak is there.

**It is one weak observation, not six.** The windows overlap heavily and the terciles partition the
same 5,973 rows; these are not independent confirmations. **And no cell is monotone**, which is the
shape D263 named: *"these are not weak signals, they are noise."*

### The rescue that is available and is refused

**At `w = 2.0` the screen nearly passes.** Its spread of −0.0759 clears the T2 bar of 0.0752, and its
quintiles run `0.8036 0.7621 0.7447 0.7232 0.7277` — **monotone on three of four steps**, failing
only the last, by 0.0045.

**`w = 1.0` is the primary cell and `w = 2.0` was declared as shape.** Promoting it now is precisely
the post-hoc selection this design existed to prevent, and precisely what D197–D203 did five times —
each refinement beating its predecessor, none moving the null gap, and the one that fixed the
*statistic* producing the worst result of the five. **It is recorded here so a future reader sees it
was available and declined**, not so it can be picked up later without a fresh pre-registration.

---

## 3. The tradeability screen, reported and refused

Signed forward return over a quarter, by density quintile:

```
+0.0099  +0.0061  +0.0016  +0.0053  +0.0004      spread -0.0095
```

A −0.95%/quarter spread, roughly **−3.8%/yr**, is not a trivial number.

**It cannot clear and is not evidence.** §5b committed in advance that the thesis makes no
directional prediction, so any sign found here is post-hoc — and it is not monotone anyway (Q4 rises
above Q3). D263 refused its own −7.32%/yr on exactly this rule.

---

## 4. What was verified along the way

**`[ALIGN]` — the D403 trap was avoided.** Strikes are as-traded; the daily fixture is
split-adjusted. Levels therefore used `RAW_CLOSE = CLOSE * raw_price_factor`, and the basis was
checked against an **independent estimate taken from the options data itself** — the strike whose
call delta sits nearest 0.5. Over 5,979 name-snapshots the median ratio is **1.0190**, which is what
a slightly-forward ATM strike should give. The two bases agree.

**`[ALIGN]` also caught the run's only real bug.** `Path.stem` on `2023-11-15.json.gz` strips one
suffix and leaves `"2023-11-15.json"`, so every date key was unjoinable to the panel and the screen
silently built **zero rows**. The assertion refused to certify a basis on zero evidence and stopped
the run. Without it the screen would have failed on an empty universe and been indistinguishable
from a real negative.

**Coverage.** 6,402 of 7,559 chains carried parseable strike/OI rows; 5,973 name-snapshots cleared
the ≥10-strikes-at-OI-100 floor, over **204 names and all 36 snapshots**. The data was not the
limitation.

**Calls and puts were summed and never netted**, as committed. No signed dealer-gamma estimate was
computed anywhere.

---

## 5. What this settles

**Open interest density at spot does not order subsequent movement on this universe**, at the
declared window, on the declared outcome, with volatility held.

This was the strongest remaining candidate for the thesis: an observable that is **not** a function
of the price path, at price levels, on obligations rather than inferences. It came closer than the
seven price-history maps — the sign is consistent where D263's was backwards — and it still does not
clear a bar stated in advance.

**The recommendation from [D405](D405-RESULT-the-overhang-is-momentum-and-its-map-is-grid-noise.md)
§6 now stands twice: close the supply-and-demand line.** It remains the principal's call. What is
left parked in PICKUP §0d2 — resting liquidity via the book, execution anchors — is a different kind
of object again, and the book is blocked on the TWS session rather than on evidence.

**What is NOT settled**, stated precisely so it is not closed by implication:

- **Expiry-window effects.** These snapshots are mid-quarter *by design*, away from the third Friday
  where pinning is classically claimed. This screen says nothing about the expiry week.
- **The `w = 2.0` cell**, §2 — available, declined, and not to be picked up without a fresh
  pre-registration that declares it primary in advance.
- **Any signed or gamma-weighted aggregation**, which was excluded by design as inference.

---

## 6. R13

Eight looks by object, seven programmes closed, none paid. This is the first on an observable that
is not a function of the price path, and it is also the cheapest: **one afternoon and 7,560
requests**, against a full study's day. Fourth time the inversion has paid.

**Evidence:** `data/d406_oi_density_screen.json`. Runner `scripts/run_d406_oi_density_screen.py`,
acquisition `scripts/pull_av_options_snapshots.py`, chains under `data/raw/alphavantage/options/`
(gitignored, D191).
