# D457 RESULT — no 8-K item clears both controls: the distress items rebound after the next open, and every 8-K filer drifts up about ten basis points in ten days against quiet names — which the rotated calendar earns too

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D457-RESULT-no-8-K-item-clears-both-controls-the-distress-items-rebound-after-the-next-open-and-every-8-K-filer-drifts-up-ten-basis-points-against-quiet-names.md`. The H1 above is the full title.*

**THE FAMILY: 0 of 17 cells clear both controls (chance 0.04); 4 clear the state-matched control
(chance 0.85), all on the LONG side and all among the largest cells.** Spec `0aad00a` predates the
runner (R8). **In-sample 2010–2023; the 2024–2026 slice was not read; no holdout; nothing
admitted.** 29.6 min (34 real cells × 2 sides × 2 caps; 2,550 state-matched draws; 2,720 exact
rotation offsets).

```
[K] kernel probe;  [F] every availability bar strictly after its filing (115,318 eligible filings);  [SYM] short gross == -long gross on every cell
C1 pool: eligible names with no 8-K of any item within +-5 bars, same day, same price x vol x mom cell;  C2: the cell's calendar rolled every 21 bars, exact
```

---

## 1. The atlas (cap 10, `all` version; the long side shown, the short is its mirror)

```
cell   filings   trades   long gross  median   C1 [p2.5, p50, p97.5]        z      2c PUB   net crossed (fav)   deployed/bar +- SE   C2 [p2.5, p50, p97.5]     verdict
1.01    13,740   11,997     +10.3     +8.9    [ -12.6,  -2.0,  +10.0]   +2.07     61.6      -51.3               +1.05 +- 0.93       [-0.94, +0.87, +2.70]    --
1.02     1,435    1,409      +5.4    +22.6    [ -48.3, -13.8,  +24.7]   +1.05     58.3      -53.0               -0.31 +- 2.25       [-4.26, +0.84, +5.86]    --
2.01     1,778    1,703     -14.1    -19.9    [ -26.9,  +1.6,  +27.6]   -1.09     60.1      -49.8 (short)       -2.12 +- 2.39       [-3.99, +0.75, +5.36]    --
2.02    35,313   33,900     +13.7    +11.5    [ -10.1,  -3.4,   +3.5]   +4.80     59.4      -45.7               +1.38 +- 0.84       [-0.50, +1.13, +3.29]    C1 only
2.03     7,111    6,610     +13.8     +9.0    [ -15.3,  -0.1,  +15.8]   +1.75     59.1      -45.4               +1.48 +- 0.93       [-1.08, +0.99, +2.96]    --
2.05       575      562     +26.3    +10.0    [ -47.9,  +4.1,  +60.7]   +0.78     60.8      -34.5               +2.19 +- 3.07       [-7.04, +0.59, +7.63]    --
2.06       265      261     +58.7     +9.6    [ -75.8, -14.6,  +58.9]   +1.96     59.9       -1.2               +4.67 +- 4.23       [-9.22, -0.21, +10.84]   --   (LONG favoured: impairments rebound)
3.01       295      285    +103.0    -17.5    [ -26.8, +22.5,  +86.0]   +2.44     50.6      +52.4               +7.65 +- 9.75       [-14.84, +2.47, +12.63]  C1 only (LONG: delisting notices rebound; median negative)
3.02     1,105    1,020      -0.8     -6.2    [ -33.5, +14.6,  +43.4]   -0.69     80.1      -82.2 (short)       +0.15 +- 3.55       [-6.52, +0.49, +8.67]    --
3.03       847      823     +40.7     +8.1    [ -25.4, +12.4,  +63.1]   +1.26     57.7      -17.1               +5.94 +- 5.37       [-5.32, +0.62, +6.75]    --
4.01       231      213     +92.1     -8.6    [ -62.8,  +0.5,  +87.6]   +2.03     65.4      +26.7              +14.05 +- 20.04      [-15.74, +0.98, +17.08]  --   (LONG favoured: auditor changes rebound; median negative)
5.02    21,060   19,061      -5.2     -2.9    [  -7.9,  +0.5,   +8.5]   -1.35     61.1      -58.5 (short)       -0.48 +- 0.54       [-0.20, +0.90, +2.36]    C2 only (short side below the rotation band)
5.03     3,296    3,229     +14.6     +5.1    [ -20.3,  +0.1,  +18.6]   +1.37     56.0      -41.4               +3.04 +- 2.63       [-2.52, +0.90, +4.12]    --
5.07     8,803    8,697     +15.6     +7.8    [ -16.2,  -2.5,  +12.7]   +2.54     59.8      -44.3               +1.20 +- 1.65       [-1.49, +1.00, +4.56]    C1 only
8.01    28,333   21,194      +7.5     +4.9    [ -13.2,  -3.4,   +4.6]   +2.24     57.9      -50.4               +0.68 +- 0.58       [-0.50, +0.67, +2.32]    C1 only
2.04*      120      117     +35.9    -33.8    [-113.9, +31.5, +117.9]   +0.07     65.9      -30.0               +3.53 +- 7.61       [-15.38, +1.10, +17.44]  (no bar)
4.02*       79       77     -35.1    +50.1    [-188.5, -27.2, +184.3]   -0.09     71.6      -40.1 (short)       +6.17 +- 9.53       [-21.17, +0.74, +24.28]  (no bar)
pure versions: 2.02 +13.4 (z +4.35, C1), 5.07 +8.4 (z +2.00), 8.01 +5.1 (z +2.24), 5.03 +20.6 (z +1.98), 3.01 +123 (z +1.75), 2.06 +1.0, 2.05 +55.0, 4.01 -41.6 (short), 3.02 +102 (n 137)
```

---

## 2. What the atlas found

**1. No corporate-event item carries a ten-day drift the book can see.** Zero cells clear both
controls against an expectation of 0.04. Four clear the state-matched control against an
expectation of 0.85 — twice what chance gives, so something is there — and every one of them
fails the rotation: **2.02 earnings** (+13.7 per trade against a quiet-name baseline of −3.4,
z = 4.8 on 33,900 overlapping trades; deployed +1.38 ± 0.84 inside a rotation band that reaches
+3.29), **8.01** (+7.5, z 2.2), **5.07** shareholder votes (+15.6, z 2.5), and **3.01** (§2.3).

**2. The common finding is a small positive drift after ANY 8-K, relative to a name that filed
nothing.** 1.01, 2.02, 2.03, 5.03, 5.07 and 8.01 are all +8 to +16 bp over ten bars with C1
medians of −3 to 0: a name that just filed *anything* does about ten basis points better over
the next two weeks than a quiet name in the same cell. That is the sign and size of the
"news-attention" drift, and it is worth a tenth of the round trip. **And the rotated calendar
earns it too** (C2 medians +0.7 to +1.1 bp/bar on the large cells): 8-K filers are a composition
that drifts up hedged on any dates, so the *timing* of the filing adds nothing the book can see.

**3. The distress items rebound after the next open — every sign prediction was wrong.** X-a
named 2.06, 3.01, 4.01, 3.02 and 2.05 as short-side clears. All five are **long-favoured** at cap
10: impairments +59, delisting notices +103, auditor changes +92, exit costs +26. Their **medians
are negative or near zero** (3.01 −17.5, 4.01 −8.6, 2.06 +9.6): the typical name keeps falling,
a minority rebounds by a lot, and the mean is the rebound. The fall itself is in the gap — the
event is public by the next open (D456: filed within two days; the market reacts on the day) and
the kernel's fill is after it. **A short after the next open is a short into a two-sided
distribution with a long right tail: not a trade.** 3.01 clears C1 on the long side (+103 vs the
band's +86) and not C2 (+7.65 deployed on 285 sparse trades, inside ±14).

**4. 5.02 officer changes are the one cell where the short side is below the rotation band**
(−0.48 deployed against a band floor of −0.20; C1 not cleared, z −1.35): a weak, consistent
negative drift after an officer departure, 5 bp over ten days — the direction the literature
gives for unplanned departures, and a twelfth of the round trip.

**5. Cost.** 2c is 51–80 bp on every cell; per-trade net crossed is positive on three cells only
(3.01 +52, 4.01 +27, 3.02-pure +31 — the rebound cells, with negative medians) and negative on
every large cell. Nothing here is within a factor of four of its cost.

---

## 3. Predictions — one of six

| | prediction | outcome |
|---|---|---|
| X-a | 2–4 cells clear both, all short, from the distress items; no long clears | **0 clear both; 4 clear C1, ALL long, none a distress item except 3.01 (long)** |
| X-b | distress short gross: 2.06 +60..+200, 3.01 +80..+250, 4.01 +40..+150, 3.02 +40..+120 | **−59, −103, −92, +1** (the shorts lose: rebounds); C1 p50 within ±15 ✓ except 3.01 (+22.5) and 2.04 |
| X-c | 2.02 |g| < 20 ✓; 5.02 −10..−40 (**−5**); 8.01/1.01/5.07/5.03 |g| < 15 (8, 10, **16**, **15**); 2.01 0..+30 (**−14**); 1.02 −20..−80 (**+5**) | mixed |
| X-d | C2 p50 within ±0.5 on every cell | **+0.6 to +2.5**: the filers' composition drifts up |
| X-e | cleared cells 2c 80–130, net crossed > 0 on ≤ 2 | no cell cleared; 2c 51–80 |
| X-f | cap 3 ≥ 60% of cap 10 on cleared; pure 2.06 / 2.05 stronger | n/a; 2.06 pure **weaker** (+1 vs +59), 2.05 pure stronger (+55 vs +26) ✓ |

---

## 4. What this leaves — the principal's call

1. **The corporate-event line closes on its own terms at stage 1:** no item type carries a
   ten-bar return the family bar admits; the 2024–2026 confirmation slice has nothing to confirm
   and **stays unread**. The atlas did what it was for — every cell was scored, no sign was picked,
   and the answer is that the reaction to an 8-K is in the gap before the next open, not after it.
2. **The two durable observations** are the ten-basis-point post-filing drift common to every
   large cell (and to the rotated calendar, so it is the filers' composition, not the filing) and
   the two-sided rebound distribution after the distress items. Neither is a trade at cap 10;
   the first is a tenth of the round trip, the second is a lottery on survival.
3. **What is not proposed:** a cap sweep, a cell subset, or a same-day construction (the daily
   fixture cannot fill inside the event day; the 15-minute fixtures could, and that would be a new
   line with its own record — the event is public at 6–8 am or after the close, so even there the
   fill is after the print).
4. **The 6-K filers (18% of the fixture) are untested** and would be a separate cell family.

**Disposition is the principal's.**

---

## 5. R13

Forty-ninth look by object; look #1 of the corporate-event line's forward-return ledger, priced
as a family of 34 tests; the 2024–2026 slice unread; no holdout. **Evidence:**
`data/d457_8k_atlas.json`. Runner `scripts/run_d457_8k_atlas.py`.
