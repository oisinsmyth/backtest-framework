# D453 RESULT — the beta hedge and vol scaling halve the lottery and do not touch the rotated base rate: the issuance book stays under one SE

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D453-RESULT-the-beta-hedge-and-vol-scaling-halve-the-lottery-and-do-not-touch-the-rotated-base-rate-the-issuance-book-stays-under-one-SE.md`. The H1 above is the full title.*

**NOT A CANDIDATE: T3 passes on both sides; T1, T2, T4 and T5 fail — the same four as D446.** Spec
`8b7747d` predates the runner (R8). **In-sample; no holdout read; nothing admitted.** 11.7 min.
The selection is D446's trade for trade; only the accounting changed.

```
[L]  the ledgers are D446's: 1,055 short / 1,063 long trades, same entry bars, same holds
[K2] beta == 1, w == 1 reproduces the kernel's book_dep_x on every held bar and every trade's pnl to 1e-9
beta (252-bar OLS, clipped [0,3]): short side mean 1.20, long 0.97;   w (median sigma / sigma, clipped [0.25,4]): short 0.88, long 1.05
```

---

## 1. The bar, beside D446

```
                                            D453 (beta-hedged, vol-scaled)         D446 (unit hedge, equal weight)
T1  gross > C2 p95 (exact) & > C3 p95 2SE   +2.225 vs C2 +3.435 (p50 +1.265) FAIL   +2.296 vs +3.768 (p50 +1.122)  FAIL
                                            vs C3 +1.159 +- 0.064 (p50 +0.076) pass  vs +1.761 (p50 +0.391)         pass
T2  net crossed > 0 by 2 SE                 +0.861 +- 1.171  (+0.7 SE)         FAIL   +0.967 +- 1.515  (+0.6 SE)     FAIL
T3  per trade > C1 p95, short / long        PASS / PASS  (2.2 / 2.2 control SD above the median)   PASS / PASS (2.6 / 2.5)
T4  era-2 net > 0 by 2 SE                   +0.265 +- 2.042                     FAIL   +0.524 +- 2.586                FAIL
T5  to-half >= 20, top 1% <= 50%            9 names, 51%                        FAIL   5 names, 85%                   FAIL
```

---

## 2. What the accounting change did and did not do

```
                          gross/bar   SE      net crossed   to-half   top 1%   GME share of the long leg   short beta   long C1 baseline
D446  unit hedge, equal   +2.296     1.515    +0.967          5        85%           29%                       --           +34.2
D453  beta, vol-scaled    +2.225     1.171    +0.861          9        51%           10%                      1.20          +85.2
```

**Did:** the SE fell by a quarter (1.52 → 1.17) at the same gross; the lottery halved — nine names to
half the P&L instead of five, the top 1% of trades 51% instead of 85%, GameStop 10% of the long leg
instead of 29%. X-c, X-d and X-f held (SE, concentration, the short side's β of 1.20 and w of 0.88).

**Did not:** move the evidence. Net crossed +0.86 at 0.7 SE (was +0.97 at 0.6); era 2 +0.27 at
0.1 SE. And the one prediction this record was built around **failed: X-b.** The rotated
selector's base rate did not collapse — **C2's median went from +1.12 to +1.27 while C3's fell
from +0.39 to +0.08.** The gap between the two controls, which is the price of the composition,
*widened* from +0.7 to +1.2 bp/bar under the beta hedge.

---

## 3. What that means — the composition premium is not a hedge error

D446 §4 read the rotated base rate as a unit-beta artefact: big low-volatility longs under-hedged
in an up market, small high-volatility shorts over-hedged. If that were all, β-hedging would have
taken it out. It did the opposite on the long side: **the state-matched long baseline rose from
+34 to +85 per trade** — hedging a β = 0.97 name with 0.97 of the market instead of 1.0 returns
the drift it was carrying — and C2's median rose with it. **The names that sit in the issuance
deciles earn in excess of their beta over 2010–2023 whether or not it is their issuance year.**
That is a factor premium of the composition (the repurchasers are large, low-volatility,
profitable; the issuers are the reverse — the low-volatility / quality tilt the six axes cannot
name), and the rotation control prices it exactly because it keeps every name's own state.

**So the honest accounting of the +2.2 bp/bar is:** about +1.3 is what a persistent selector of
this composition earns on any dates (C2's median), and about +1.0 is what aligning it to the
actual issuance year adds — on an SE of 1.2. Per trade the alignment is 2.2 control-SDs on each
side (p ≈ 0.01–0.02 per side); at the book it is 0.8 SE, and the two are the same fact measured
with and without the overlap of 40 concurrent six-month positions.

---

## 4. Predictions — three of five

| | prediction | outcome |
|---|---|---|
| X-a [K2] | identity | ✓ to 1e-9 |
| X-b | C2 p50 falls to +0.2..+0.7, within 0.4 of C3; p95 +1.5..+2.6 | **C2 p50 +1.27 (rose); C3 p50 +0.08; p95 +3.44** — FAILED, and it is the finding |
| X-c | gross +1.2..+2.0, SE 0.9..1.2, net +0.3..+1.2, T2 fails | gross **+2.23** (above), SE 1.17 ✓, net +0.86 ✓, T2 fails ✓ |
| X-d | to-half 12..25, top 1% 30..55, GME < 15% | 9 (below), 51% ✓, 10% ✓ |
| X-e | C1 short −30..0 / long −10..+20; real +30..+70 / +80..+150 | **−63 / +85**; +65 ✓ / **+198** |
| X-f | β short > 1.2, long < 0.9; w short < 0.8, long > 1.1 | 1.20 ✓ / 0.97; 0.88 / 1.05 |

---

## 5. What this leaves — the principal's call

1. **The issuance line has two forward-return looks on the same trades and one answer:** a real
   per-trade effect on both sides against the right control (2.2–2.6 control-SDs, twice), and a
   book whose alignment term is +1.0 bp/bar on an SE of 1.2. The accounting change that removed
   the two artefacts it could remove (noise from unequal volatility; the lottery) did not change
   that answer, and it revealed that the rotated base rate is a factor premium of the composition,
   not a hedge error.
2. **What would change the answer is not on this fixture:** thirteen years of one universe cannot
   resolve a 1 bp/bar alignment term at this hold length. More calendar time (the fixture's 2024–
   2026 tail is reserved), or a second universe — both need an EDGAR panel, and the second needs a
   CIK map first.
3. **What would be a refinement and is not proposed:** a factor hedge (regressing on a
   low-volatility or quality factor) to strip the composition premium from the book; a shorter
   hold; a different decile. Each is a new selection on spent data.
4. **The holdouts stay shut.**

**Disposition is the principal's.**

---

## 6. R13

Forty-fifth look by object; look #2 of the issuance line's forward-return ledger, on D446's
trades. **Evidence:** `data/d453_beta_vol_book.json`. Runner `scripts/run_d453_beta_vol_book.py`.
