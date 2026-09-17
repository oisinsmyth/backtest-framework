# D425 RESULT — the next live zone is where the move stops: the first exit that carries information, and too small to clear

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D425-RESULT-the-next-live-zone-is-where-the-move-stops-the-first-exit-that-carries-information-and-it-is-too-small-to-clear.md`. The H1 above is the full title.*

**FAILS THE BAR: T1 fails, T2 PASSES, T3 passes its control and fails its delta.** Pre-registration
`e98b3ee` predates the runner and this file (R8). **The ledger does not move. Nothing was admitted.
No holdout was read.** Daily bars.

Cost: 429 s (18 books in 4 s; 200 control books; 200 null walks).

```
[SIGN]  ratcheting trail, wick vs close, short LOG mirror, limit-before-close; fires when broken
[X]     walk2 with a constant stop == D423's SWING+BREACH walker, bit for bit, all 180,050
[P2]    sim2 == D422's ANY-REQ FIXED book and == D423's SWING+BREACH book, bit for bit
[RECON] 18 books;  [CHUNK];  [NUISANCE] control run 4.703 vs ZTP 4.705
```

---

## 1. The bar — ZTP (take profit at the next live opposite-side zone) on ANY ∧ cell 2

```
T1  paired delta vs FIXED            +0.36 ± 2.03 bp     +0.2 SE     FAIL
T2  vs distance-permutation null     observed +0.36   null p5 -3.74  p50 -2.12  p95 -0.40 (±0.07)   +10.2 SE   PASS
T3  book net delta vs FIXED          +0.158 ± 0.384 bp/bar   +0.4 SE                                 FAIL
    book net vs sampled-runs ctrl    +1.394  vs  p50 +0.784  p95 +1.238 (±0.024)   +6.6 SE          PASS
```

**Both information tests pass. Both money tests fail.** That is a different failure from the
eight exit constructions before it, and it should be read as one.

---

## 2. THE ZONE IS WHERE THE MOVE STOPS — the mechanism, in the forfeit

```
                        PAIRED     SE    early   would-have   filled-at   forfeit
ZTP    ANY & cell 2      +0.36   +0.2   15.6%     +526.59     +528.92     +2.33
ZTP    long              +2.24   +0.9   17.2%     +470.13     +483.16    +13.03
ZTP    short             -1.89   -0.6   13.7%     +611.66     +597.86    -13.79
ZTP    2018+             +1.58   +0.6   15.6%     +548.01     +558.15    +10.14
ZTP    cell 2 all        +2.12   +1.9   15.1%     +500.84     +514.83    +13.98
ZTP    ANY pooled        +0.83   +1.4    9.3%     +507.25     +516.23     +8.98
```

**Every target before this forfeited on the cell that pays** — an ATR multiple at the same
distance forfeits −11.84 (D424's `TP 2.0`, median 2 ATR; ZTP's median is 1.99), the prior swing
forfeits −28 (D423). **Trades that reach the detector's next live supply zone give back nothing
after it: +2.33, and +13 on the long side.** The move stops at the zone.

**T2 is the number that says why.** Permute which event gets which zone distance — same
distances, alignment with *this* event's zone destroyed — and the null sits at **−2.12**, which is
D424's ATR target: a level at that distance costs 2 bp. The zone at the same distance earns
+0.36. **The zone carries about +2.5 bp per trade of information beyond its distance** (about
+16 bp on the 15.6% that reach it), and it is the first level in this line — after the zone's own
edge (D418), the prior swing, the tested dead zone (D423) and every ATR multiple (D417, D424) —
that does. **The difference between a dead zone and a live one is the whole result: D423's OPP,
the same construction on zones that had already been touched, forfeited −24.**

**And it is too small to clear.** +0.36 on 9,411 trades has a paired SE of 2.03; the information
is real at 10 SE against its null and invisible against the fixed exit's own noise. It fires on
one trade in six.

**By side, again:** long +2.24 (forfeit +13), short −1.89 (forfeit −14). On the short side the
reachers keep going through the live demand zone below. D424 found the same asymmetry on the ATR
target. **A live zone is resistance on the long side and not support on the short side, on this
cell** — reported, not gated, and consistent with D422's trade shapes.

---

## 3. THE BOOK — the first exit with a higher gross than FIXED that keeps it net

```
cell-2 ANY-REQUIRED, 10 slots   gross     net     cost    util    run    early   per trade   net by seed
FIXED                          +4.889  +0.993   3.896   68.2%   5.00    0.0%    +35.85     +0.99 +1.51 +1.20
ZTP                            +5.332  +1.310   4.022   66.0%   4.70   14.3%    +38.03     +1.31 +1.84 +1.03
ZTRAIL                         +4.932  +1.037   3.895   68.1%   5.00    0.1%    +36.17     +1.04 +1.55 +1.30
FAR->ZTRAIL                    +4.494  +0.204   4.290   64.6%   4.33   23.0%    +30.12     +0.20 +0.17 +0.06
ZTP+ZTRAIL                     +5.340  +1.319   4.022   66.0%   4.70   14.3%    +38.09     +1.32 +1.84 +1.09
ZTP+FAR->ZTRAIL                +4.819  +0.396   4.423   61.9%   4.03   37.0%    +31.39     +0.40 +0.63 +0.28

deltas vs FIXED               gross      NET
ZTP                          +0.276    +0.158 ± 0.384   +0.4 SE
ZTRAIL                       +0.060    +0.061 ± 0.044   +1.4 SE
FAR->ZTRAIL                  -0.712    -1.092 ± 0.420   -2.6 SE
ZTP+ZTRAIL                   +0.298    +0.180 ± 0.388   +0.5 SE
ZTP+FAR->ZTRAIL              -0.292    -0.801 ± 0.617   -1.3 SE
```

**ZTP's book has the highest gross per bar of any book in the record (+5.332), and it is the
first early exit whose net is above FIXED's on every seed.** Its swap premium is +26 ± 33 on 595
swaps — the arriving trade earns +35.7 and the departing one forfeits +9.7 (i.e. it *would have
made* 9.7 more; the book's forfeit is positive where the per-trade one on the cell is +2.3,
because the book's swaps are the subset that found a refill). It beats random exits at its own
turnover by +6.6 SE at the p95 — **D419's target sat below its p95 by 3.2 SE; D424's by 12.9;
this is the first that clears it.** And the net delta over FIXED is +0.158 ± 0.384: the
improvement is a third of its bootstrap SE. The thin pool is still the ceiling — utilisation
66.0% — but this exit is the first that pays more than it idles.

**The trail is nothing.** A same-side zone arms inside the hold on 7.9% of the cell's trades,
first at bar 4 at the median, and its far edge is then so far behind the price that the stop
fires on 0.1%. `FAR→ZTRAIL` is `BREACH` (−6.52 vs D423's −6.61); the ratchet added four fires.
X-c predicted 10–25% engagement and 3–8% firing; the detector finds a new zone in the hold less
often than that and the zone it finds is never reached.

---

## 4. Predictions — two of five, and the misses are the result

| | prediction | outcome |
|---|---|---|
| **X-a** | ZTP −4..+1 inside 2 SE; fires 12–20%; **forfeit −5..−20** | delta and firing as predicted; **forfeit +2.33 — wrong sign, the reachers stop** |
| **X-b** | ZTP at its null's median | **wrong — +10.2 SE above the p95; the zone is not its distance** |
| X-c | ZTRAIL engages 10–25%, fires 3–8%, −1..−4 | engages 7.9%, fires 0.1%, +0.14 — less of everything |
| X-d | FAR→ZTRAIL within 2 of −6.61; ZTP+FAR→ZTRAIL −8..−14 | −6.52; −5.86 (just outside) |
| **X-e** | ZTP book above ctrl median, **below p95**; trail books negative | **beats p95 by +6.6 SE**; ZTRAIL book +1.4 SE, not negative |

I predicted the zone would behave like its distance because every level before it had. It did
not. **The prediction that was wrong is the finding.**

---

## 5. What this leaves

1. **Not a clear.** T1 and T3's delta are inside their noise; the pre-registered condition was
   all three, and the money tests are the ones that would matter to a book.
2. **The detector's live zones carry exit information that price levels, ATR multiples and dead
   zones do not** — +2.5 bp/trade over the same-distance null at 10 SE, a book that beats
   random exits at its turnover at 6.6 SE, forfeit of the right sign for the first time. It is
   the first exit result in nine constructions with a mechanism that reads correctly, and it is
   worth about a third of an SE net on the book.
3. **Where it would grow, if anywhere:** the long side (+2.24 per trade, forfeit +13, where the
   short side is negative); a wider pool where a freed slot refills (the 50-slot pooled ANY book
   was not run here); and 15m fills at the zone's edge instead of daily limit fills. Each is a
   different study and none is recommended here.
4. **Trailing the stop under new zones is empty**: the zones the detector finds inside a hold
   are too far from price to ever be hit, and putting the entry zone's edge under them is D423's
   breach.
5. The entry rung is untouched; D422 §7 item 2 stands.

**Disposition is the principal's.**

---

## 6. R13

Twenty-fifth look by object on price levels. No new data spent.

**Evidence:** `data/d425_zone_exits.json`. Runner `scripts/run_d425_zone_exits.py`; levels
`scripts/d425_zone_levels.py`, committed with the pre-registration.
