# D679 RESULT: NO MECHANISM by the declared bar, and a consistent lift. On all nine roots the compressed third's breaks beat the rest before costs. On the five new roots that lift clears its exact rotation p95 (rank 0.957), but the compressed breaks' own gross is not significant (+0.86% of ATR, t 1.2). On CL/NG/GC/SI both parts miss narrowly (rank 0.949; t 1.6). Not tradeable after costs anywhere

*2026-09-29.*
- *One run of `scripts/stage0_d679_compression_mechanism.py --run` under D679 (`633a7ab8`) and D679-A1 (`7fb7e196`);
  runner `9ee452ea`; 1.4 min.*
- *Output: `data/stage0_d679_compression_mechanism.json`.*

**Inputs:**
- **Primary:** D678's fixture and gates (`2cd82b3d`).
- **Family 2:** D676's fixture (`0a6c033f`) with D676's R2.
- In-sample through 2025-02-28; no vault.
- The tier is finite from about 2017-10 (two 250-session walk-forward windows).

## 1. Gate 1, the mechanism (gross, % of ATR; C1 = the compressed third)

| | primary: HO, RB, BZ, HG, PL | family 2: CL, NG, GC, SI |
|---|---|---|
| **(a) Δ = C1 − rest** (mean over the roots) | **+1.25** | **+1.54** |
| enumerated common-offset rotation: offsets / p50 / p95 / rank | 1,788 / +0.01 / **+1.20** / **0.957** | 1,834 / +0.00 / **+1.56** / **0.949** |
| (a) above p95 | **yes** (by 0.05) | **no** (by 0.02) |
| **(b) C1 gross,** date series (HAC t, one-sided p) | +0.86 (1.2, 0.11) | +1.28 (1.6, 0.052) |
| (b) p < 0.05 | **no** | **no** |
| (c) Δ without February–April 2020 | +1.07 | +1.39 |
| **Gate 1** | **fails (b)** | **fails (a) and (b)** |
| **mechanism reading** | **NOT CONFIRMED** | **NOT CONFIRMED** |

**All nine, reported (D679-A1).** Each root's C1 − rest exceeds its own rotation's p50 on **9 of 9**; the binomial p at
½ is 0.002.
- **That p assumes independent roots, and they are not:** the energy roots co-move. So it overstates the evidence.
- The family rows above, which rotate every root by the same offset, keep that dependence. **They are the honest read,
  and each sits at the edge of its p95.**
- The C1 gross in % of A is also positive on 9 of 9, from +0.22 (HG) to +3.15 (NG). None has t above 2.2 (NG's).

## 2. Per root

| | HO | RB | BZ | HG | PL | CL | NG | GC | SI |
|---|---|---|---|---|---|---|---|---|---|
| C1 trades (a year) | 404 (57) | 402 (57) | 430 (62) | 418 (56) | 409 (55) | 290 (41) | 309 (44) | 375 (50) | 386 (52) |
| C1 / C2 / C3 gross, % of A | +2.67 / −0.07 / +1.00 | +2.18 / +0.86 / +0.79 | +0.89 / −2.85 / +1.88 | +0.22 / −1.35 / +0.33 | +0.79 / +1.12 / −0.67 | +1.32 / +1.70 / −1.00 | +3.15 / −1.76 / +1.29 | +2.50 / +0.59 / +0.57 | +1.62 / +0.62 / +2.57 |
| Δ = C1 − rest | +2.21 | +1.35 | +1.39 | +0.77 | +0.54 | +0.83 | +3.38 | +1.92 | +0.05 |
| own rotation rank | 0.93 | 0.80 | 0.83 | 0.69 | 0.63 | 0.67 | **0.96** | 0.87 | 0.52 |
| Δ with each input alone: rv5 / overnight | +3.05 / +0.49 | +1.73 / +0.58 | +1.19 / −1.32 | −0.96 / −0.88 | +0.16 / +1.77 | +2.94 / −1.27 | +0.04 / +4.55 | +1.56 / +0.70 | −0.50 / +0.53 |
| C1 gross, bp (t) | +10.95 (2.0) | +5.64 (1.4) | +4.10 (1.1) | −1.74 (−0.7) | +1.25 (0.4) | +8.96 (1.0) | +10.12 (1.5) | +2.07 (1.2) | +2.75 (1.1) |
| cost, bp | 6.46 | 4.59 | 5.14 | 4.04 | 10.56 | 3.33 | 6.44 | 2.83 | 11.07 |
| **C1 net, bp (t)** | +4.41 (0.8) | +0.98 (0.3) | −1.05 (−0.3) | −5.73 (−2.4) | −9.53 (−3.4) | +5.59 (0.6) | +3.61 (0.5) | −0.81 (−0.5) | −8.39 (−3.2) |
| verdict | NOT SUPPORTED (every root) | | | | | | | | |

## 3. What the lift is made of

**It is not a clean compression → expansion ladder.** The family ladder is C1 +0.86 / C2 −0.80 / C3 −0.14 on the
primary roots, and +1.28 / +0.67 / +0.79 on family 2.
- **The compressed third is the best of the three on only 4 of 9 roots** (HO, RB, NG, GC).
- It beats the other two combined on all nine because the middle or busiest third is weak, not because C1 is strong.

**The recent-range half (rv5) carries more of it than the overnight half.** Alone, rv5 lifts on 7 of 9 roots; the
overnight range alone lifts on 6 of 9, with the largest single read on NG (+4.55).

**It is not D678's gap.**
- The compressed third holds more gap-through opens (46–61% against 34–49% in all breaks), because a one-way overnight
  move has a small two-way range.
- ρ with the same root's gap book is 0.36–0.63.
- But D678 found no direction in the gap itself. So the lift comes from the breaks, not from the gaps they contain.

**Energy's compressed breaks earn on the short side:**

| C1 gross, bp | short (t) | long |
|---|---|---|
| HO | +16.82 (2.7) | +7.07 |
| RB | +21.01 (3.6) | −6.21 |
| BZ | +14.34 (2.3) | −3.06 |
| NG | +23.18 (2.9) | −3.90 |

- CL is balanced (+7.00 short against +10.21 long).
- The rotation null keeps each trade's side, so this does not create Δ, but it is where the energy gross sits.

**Years with C1 gross > 0,** of 2017–2025 (HG has no C1 trade in 2025): HO 7 of 9, RB 7, BZ 6, HG 4 of 8, PL 6, CL 7,
NG 8, GC 6, SI 7.

**Where the net is positive, it rests on one day.** HO and CL's top trade is 2020-04-02, the crude rebound (+1,127 and
+1,772 bp); their trimmed nets are +0.06 and −1.16.

## 4. The four groups and the component line (C1, one full contract)

| | HO | RB | BZ | HG | PL | CL | NG | GC | SI |
|---|---|---|---|---|---|---|---|---|---|
| net mean / median | +4.4 / −15.6 | +1.0 / −22.3 | −1.1 / −19.4 | −5.7 / −17.5 | −9.5 / −24.2 | +5.6 / −22.3 | +3.6 / −29.2 | −0.8 / −8.2 | −8.4 / −18.3 |
| win / payoff | 38% / 1.90 | 41% / 1.47 | 36% / 1.69 | 32% / 1.51 | 33% / 1.31 | 40% / 1.75 | 39% / 1.67 | 39% / 1.46 | 33% / 1.32 |
| trimmed / ex-top / ex-bottom | +0.1 / −1.3 / +5.8 | +0.1 / −3.1 / +4.3 | −2.8 / −4.8 / +1.0 | −7.0 / −7.7 / −5.0 | −10.7 / −11.7 / −8.6 | −1.2 / −4.0 / +8.5 | +1.5 / −1.2 / +6.3 | −1.6 / −2.2 / −0.2 | −9.4 / −10.7 / −7.1 |
| Sharpe net / gross (per trade, annualised) | +0.35 / +0.88 | +0.08 / +0.47 | −0.10 / +0.40 | −0.97 / −0.29 | −1.23 / +0.16 | +0.26 / +0.42 | +0.18 / +0.50 | −0.18 / +0.46 | −1.12 / +0.37 |
| Sortino net | +0.85 | +0.14 | −0.19 | −1.58 | −1.86 | +0.68 | +0.31 | −0.31 | −1.66 |
| **daily $ Sharpe net / gross** | **+0.21 / +0.73** | +0.05 / +0.44 | +0.03 / +0.51 | −0.92 / −0.28 | −1.18 / +0.18 | −0.01 / +0.22 | +0.15 / +0.40 | −0.16 / +0.42 | −0.87 / +0.42 |
| $ a year; max drawdown | +1,332; 16,146 | +288; 11,681 | +148; 11,643 | −2,769; 26,344 | −2,386; 19,490 | −38; 12,429 | +476; 7,314 | −666; 21,269 | −3,975; 34,669 |
| ρ K8 | −0.03 | +0.02 | −0.02 | −0.02 | +0.01 | +0.04 | −0.01 | +0.00 | +0.01 |

**Gross daily Sharpe is positive on 8 of 9, and net is at most +0.21.** Nothing here is a component.

## 5. Predictions (§5, on the primary five)

| # | prediction | outcome |
|---|---|---|
| 1 | the family's Δ > 0 | held (+1.25) |
| 2 | excess over own p50 on ≥ 4 of 5 | held (5 of 5) |
| 3 | no root passes Gate 2 | held |
| 4 | the family ladder is monotone | **failed** (C2 is the worst third) |

## 6. What this says, and what it does not

**The principal's criterion, a gross edge on other roots but not a net one, describes what was found:**
- the compressed breaks do better than the other breaks, before costs, on every root;
- the family lift on the new roots is beyond its exact rotation p95;
- after costs, nothing is tradeable at full size.

**But the declared bar is not met.**
- Gate 1 also required the compressed breaks to be positive **on their own**, at one-sided p < 0.05. They are
  +0.86% of ATR at p 0.11 (new roots) and +1.28% at p 0.052 (CL/NG/GC/SI).
- **Much of the lift is that the other two-thirds of breaks lose,** rather than that the compressed ones win big.
- And the lift is not a gradient.

**The honest summary is a consistent but small selection effect at the edge of detection.** It is not a confirmed
mechanism, and it is nowhere near NQ's size.
- On NQ the compressed third was about 4.8% of ATR above the rest (D672). Here it is 1.25–1.54%.
- The NQ vault case stays NQ-specific, as D682 left it. This record adds that the tier's sign holds on nine other roots.

**Not done, and not to be done on this data:** combining the two families into one nine-root rotation test. It was
not declared, and choosing it now, after seeing two p95s just either side of the line, would be selection.
- A confirmation would need a pre-registered test of the lift alone (Gate 1a) on roots no break has read: FX (6E, 6J,
  6B, 6A, 6C, 6S), grains (ZC, ZS, ZW, ZL, ZM), PA and the deferred treasuries.
- At the effect size seen here (≈ 1.3% of ATR), about ten such roots give power of about 0.6. Left to the principal.
