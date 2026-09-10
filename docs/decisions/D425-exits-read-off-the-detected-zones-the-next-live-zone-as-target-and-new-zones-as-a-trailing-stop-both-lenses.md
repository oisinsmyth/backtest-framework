# D425 — exits read off the detected zones: the next live zone as the target, new zones as the trailing stop, both lenses

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file. D400–D424
used, D407–D410 and D390–D399 reserved. **No holdout.** Daily bars only.

## 1. The question, as the principal put it

Exits based on **the zones the detector already finds** — not generic price structure (D423) and
not ATR multiples (D424). Three things the zone table gives that nothing before this used:

```
ZTP       take profit at the NEXT LIVE opposite-side zone: armed by the entry day, not yet touched,
          inside its 60-session life, band beyond the entry. Limit at its NEAR edge.
ZTRAIL    trail the stop under NEW same-side zones as they ARM during the hold: the far edge of the
          latest such zone, ratcheted in the trade's favour, evaluated on the close.
FAR       the entry zone's own far edge, the initial stop the trail ratchets from (D423's BREACH).
```

D423's OPP used only *touched* (dead) opposite zones — the event table is all it had. This reads
the whole zone table (`scripts/d425_zone_levels.py`, committed with this record): **229,544 armed
zones, 181,710 touched.**

**Rules:** `FIXED`; `ZTP`; `ZTRAIL` (no initial stop); `FAR→ZTRAIL` (stop at the far edge,
ratcheting up to each new zone); `ZTP+ZTRAIL`; `ZTP+FAR→ZTRAIL` (the fully zone-managed trade).
Every rule keeps the `t+5` clock. A resting limit fills before the close is evaluated.

## 2. Stage 0 — facts computed before this was written (pre-entry information only)

```
ZTP  ANY & cell 2   coverage 60.5%   distance ATR p10/50/90  1.11 / 1.99 / 4.30   within 2 ATR 50.4%
ZTP  ANY pooled     coverage 39.6%                            1.08 / 2.10 / 4.66
```

**The next live supply zone sits 1.99 ATR above the entry at the median.** That is D417's `TP 2.0`
distance, which D424 has just measured on this exact cell: **−2.72 ± 2.27 per trade, −1.2 SE,
fires 23.0%, forfeit −11.84** (the reachers keep running, as D423 found at 3.2 ATR). The trail's
engagement rate reads the hold and is reported by the runner, not predicted from data.

## 3. Assertions before any number

The 2-D-stop walker with a constant stop broadcast reproduces D423's `SWING+BREACH` and `FIXED`
bit-identically (`[X]`); the 2-D-stop book likewise reproduces D423's `SWING+BREACH` book and
D422's ANY-REQ `FIXED` book (`[P2]`); `[SIGN]` on a synthetic path: a trail that ratchets on bar 2
exits on a close below it on bar 3 and not on a wick, the short mirror is exact in log return, a
limit fills before the close; `[RECON]` every book; `[CHUNK]`/`[NUISANCE]` on the control.

## 4. The bar — ZTP on ANY ∧ cell 2 (9,411), D423's three tests

- **T1** paired delta `ZTP − FIXED` > 0 by 2 SE.
- **T2** beats the p95 of a within-day permutation of the ZTP *distance* (200 draws; NaN
  permutes with the rest), D373's margin.
- **T3** on the cell-2 ANY-REQUIRED 10-slot book, three seeds: `ZTP` net − `FIXED` net > 0 by 2 SE
  (monthly block bootstrap) **and** above the p95 of its sampled-runs control (200 draws).

ZTP clears when all three hold. The trail rules run through T1 and T3's book delta and are
reported. Long/short, 2018+, ANY pooled and cell 2 all reported; forfeit decomposition; premium;
utilisation; **the trail's engagement rate and the age at which it engages.**

## 5. Predictions (LOW; the arithmetic is D424's TP 2.0 on 60% of the cell)

- **X-a** ZTP delta **−4 to +1**, inside 2 SE; fires **12–20%**; forfeit **−5 to −20**. T1 fails.
- **X-b** ZTP at the median of its distance null, inside 2 SE of the p95 either way — the next
  zone is worth its distance (D423's finding). T2 fails.
- **X-c** ZTRAIL *engages* (a same-side zone arms inside the hold) on **10–25%** of trades and
  *fires* on **3–8%**; delta **−1 to −4** — a stop that only exists after an impulsive move in the
  trade's favour cuts a trade that is winning.
- **X-d** FAR→ZTRAIL within 2 bp of D423's BREACH (−6.61): the ratchet adds a few fires and
  changes little. ZTP+FAR→ZTRAIL **−8 to −14**.
- **X-e** ZTP book: gross delta −0.4 to +0.3, utilisation below 68.2%, net inside 2 SE; above
  its control's median, below its p95. Trail books negative. T3 fails.

X-c is the one number this study adds: nothing before it has measured how often the detector
finds a new zone *inside* a five-day hold, and whether that event marks a trade to leave.

## 6. Not in scope

No holdout, no 15m, no change to entry, hold, cost or cell, no sweep on zone parameters, no
disposition. Twenty-fifth look by object; twenty-four of twenty-four before it failed their bar.
