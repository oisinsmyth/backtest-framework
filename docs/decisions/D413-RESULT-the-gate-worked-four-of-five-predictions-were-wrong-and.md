# D413 RESULT — the distance gate worked, four of five predictions were wrong, and it is mostly short-term reversal

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D413-RESULT-the-gate-worked-four-of-five-predictions-were-wrong-and-it-is-mostly-reversal.md`. The H1 above is the full title.*

**FAILS THE BAR** (T4 and R1). **But T1, T2 and T3 all pass — the first time any construction in
this programme has beaten a matched-geometry level control.** Pre-screen `6374e5c` predates both
runners and this file (R8). **The ledger does not move. Nothing was admitted. No holdout was read.
D407 was not consumed.**

Cost: 54 s for the screen, 8 s for the extras.

---

## 1. The one change did what it was supposed to do

```
[DIST]  D413 min separation 1.000 of the required 1.0 ATR
        D412's rule gives 0.000  -- the gate BINDS, it is not decorative
        229,544 zones armed at delta=1.0 against 262,400 at delta=0  (87.5%)
```

```
                        D413              D412
median age at touch     6 bars            1 bar
touched within 5        48.3%             81.1%
expired unrevisited     20.8%             8.0%
distance/ATR p10/50/90  0.98 1.30 2.18    0.06 0.38 1.18
```

**The degenerate population is gone.** D412's median zone armed 0.38 ATR out and was touched the
next bar; D413's arms at 1.30 ATR and survives six.

**`[DIST]` fired on its first run**, at 0.358, and the cause was mine: the arming rule padded by the
ATR at the **creation** bar while the check divided by the ATR at the **arming** bar. Two different
numbers whenever volatility moved in between. The check now reads the quantity the gate read — and
it is still shown to fail against D412's rule, so it is a gate and not decoration.

**`delta = 0.0` reproduces D412's committed artifact byte-for-byte**, verified twice, so the two
studies are provably the same object with one rule changed.

---

## 2. FOUR OF MY FIVE PREDICTIONS WERE WRONG, ALL IN THE PESSIMISTIC DIRECTION

| | prediction | outcome |
|---|---|---|
| X-a | population cut by **more than half**, median age ≥ 3 | **half wrong** — age went 1 → 6 bars, but the cut was only 12.5% |
| **X-b** | **T1 fails again** | **WRONG** — **+13.21 bp, +9.0 SE** |
| **X-c** | **T2 fails: `LVL` still eats it** | **WRONG** — beaten by +77.7 SE |
| **X-d** | **R1 holds, the age gradient is monotone** | **WRONG** — it is hump-shaped |
| X-e | `ABS` ≈ departure | **correct** — 1.14 SE apart |

I called D412's failure as evidence the idea was weak. It was evidence the **arming rule** was
weak, which is what D412's own §9.4 said, and I still predicted against it.

---

## 3. The bar

```
first touch   n 180,050   mean +13.21 bp  +-1.48   +9.0 SE   win 50.8%
touch #2      n 169,841   mean +13.01 bp  +-1.48
touch #3      n 161,628   mean +10.62 bp  +-1.53

LVL  200 draws   observed +13.21   p50 +4.50   p95 +6.57 bp   +77.7 SE
ORD  200 draws   observed +13.21   p50 +6.51   p95 +8.30 bp   +65.9 SE
ABS  (contrast)  n 193,554   +10.97 +-1.30   departure - absorption +2.24 vs SE 1.97
```

| | condition | outcome |
|---|---|---|
| **T1** | first-touch mean > 0 | **PASS** — +13.21 bp, +9.0 SE |
| **T2** | beats `LVL` p95 | **PASS** — +77.7 SE. **Caveated by §5** |
| **T3** | beats `ORD` p95 | **PASS** — +65.9 SE |
| **T4** | first touch > second by 2 SE | **FAIL** — +0.21 bp against a 2 SE band of 4.18 |
| **R1** | age terciles monotone, oldest positive | **FAIL** — −10.63 / **+23.73** / +17.52 |

**D413 FAILS.** And the gate-ordering fix mattered in the good direction this time: T1 passed, so
T2 and T3 were evaluated at all — and both controls sit **positive**, so this is not the empty
"loses less than the control" pass that D411 and D412 produced.

**T4's failure is the substantive one.** The construction's whole claim is that a level is *spent*
by its first return. The second touch pays **+13.01 against the first's +13.21**. Nothing is being
consumed. **The state machine — the property that made this idea worth trying — is not doing
anything.**

**R1 fails but its shape is the finding.** Ages 1–2 bars pay **−10.63**; everything older pays
strongly positive. That is precisely D412's degeneracy showing up as a *sub-population*: D412 pooled
a losing immediate-return population with a winning delayed one and reported the average.

---

## 4. The sweep is a clean dose-response, and that cuts both ways

```
delta=0.5   +6.05 bp   +4.5 SE      life=120  +14.97      h= 1   +2.31 bp
delta=1.0  +13.21 bp   +9.0 SE      life=250  +14.41      h= 5  +13.21 bp
delta=2.0  +22.62 bp  +11.8 SE                            h=21   -4.59 bp
```

**Monotone in the distance gate**, stable in `life`, and **reversing by `h = 21`**. A dose-response
is what a real mechanism looks like. It is *also* exactly what short-term reversal looks like: a
bigger departure means a bigger round trip when price returns, and reversal decays and flips at a
month. §5 is the reason that matters.

---

## 5. THE EXTRAS FOUND TWO THINGS, AND BOTH CUT AGAINST THE RESULT

Run after the primary, and every arm could only weaken it — which is what makes running them after
the fact legitimate. **A passing result deserves harder questions than a failing one.**

### 5a. It is largely short-term reversal, and P3 tested the wrong horizon

The construction buys a demand zone when price **falls back into it**. That is fading a move, and
short-term reversal lives at three to five days — while P3 (inherited from D411's G4) measured the
trailing **twenty**-day return and duly found nothing (−0.018).

Response by quintile of the **signed trailing 5-day return at the touch**:

```
Q1  n 36,010   trailing5 -1101 bp   resp +48.79 +-4.16 bp   <- most reverted INTO the zone
Q2  n 36,009   trailing5  -478 bp   resp +18.12 +-2.94
Q3  n 36,010   trailing5  -248 bp   resp  +6.05 +-2.52
Q4  n 36,009   trailing5   -36 bp   resp  -3.27 +-2.63
Q5  n 36,010   trailing5  +433 bp   resp  -3.60 +-3.89
```

**Monotone, and Q1 alone carries about three-quarters of the pooled +13.21.** Q4 and Q5 are
negative. `corr` at 3 days is −0.062 against −0.018 at 20.

**The runner printed "NOT explained by reversal alone" on a crude rule I wrote before seeing the
data — three of five quintiles more than 2 SE above zero. The gradient overrides that line and I am
not going to hide behind it.** Q2 and Q3 being positive means reversal is not the *whole* story;
the steepness means it is most of it.

### 5b. `[MATCH]` matched the geometry and nothing checked the POPULATION

```
                real      LVL
touch rate      79.2%     68.9%
median age      6 bars    4.0 bars
resolved        180,050   156,856
```

**The control's zones are touched less often and sooner.** And §3 shows the youngest ages pay
**−10.63 bp**. So a control population skewed two bars younger scores worse **for reasons that have
nothing to do with the level** — which is a direct confound on T2's +77.7 SE.

`[MATCH]` asserted the (width, distance) distributions were identical, and they were, to
`0.0e+00`. **Matching the inputs is not matching the experiment.** This is the same error as D411's
VOL-SHUF in a new place: I checked what the control preserved and did not check what it produced.

**The fix is named and not run: match `LVL` on realised touch age**, by reweighting or by
stratifying both populations on age before comparing.

---

## 6. What this leaves

1. **The distance gate is the right construction change**, established on its own terms (§1) — the
   degeneracy that voided D412 is gone.
2. **T1–T3 pass, and that is unprecedented here** — nine constructions, and this is the first
   positive mean per trade that clears a matched-geometry level control. **Under R15 that is the
   definition of a signal**, and it would stand **if T2 were clean.** §5b says it is not.
3. **The mechanism claimed is refuted anyway.** T4 says levels are not consumed by contact; `ABS`
   says departure and absorption bars are indistinguishable at 1.14 SE, so what is measured is *"a
   notable bar happened here and price travelled away from it"*, not which kind of bar.
4. **Costs are NOT measured**, and +13.21 bp gross per trade is not obviously above them. CLAUDE.md
   requires Corwin–Schultz off the OHLC of the names actually held rather than a guessed fee — D285
   missed a guessed 15 bp/side bar by 0.65 and the held names measured 33.8. **That estimate has not
   been made and no cost claim is made here.**
5. **No time rotation**, again named and not run.

**Two clean next questions, neither run:** does the effect survive an age-matched `LVL`; and does it
survive conditioning on the trailing 5-day return rather than merely being stratified by it.

**Disposition is the principal's.** This record reports against the bar and stops.

---

## 7. R13

Thirteenth look by object, second on this construction, **informed by a failed run** — which under
R13 is strictly worse than an independent look, and is why §5 was run at all.

**Evidence:** `data/d413_distance_armed_zones.json` (the primary, against the committed bar) and
`data/d413_extras.json` (§5, exploratory). Runners `scripts/run_d413_distance_armed_zones.py` and
`scripts/run_d413_extras.py`, importing D412's construction rather than restating it.
