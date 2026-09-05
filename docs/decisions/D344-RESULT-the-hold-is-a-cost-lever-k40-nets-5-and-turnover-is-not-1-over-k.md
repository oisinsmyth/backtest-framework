# D344 RESULT — the hold is a cost lever: k=40 nets +5.14, above all 24 rotations, and turnover is not 1/k under a target exit

**Status:** RESULT. Pre-registered at `9f2f601`, runner at `00cd1e7` — both before this
file existed (R8). `rsi` F0, `keep_v2`, open fill, PUB primary. Three cells; multiplicity
three, stated wherever a number from this study is quoted.
**Date:** 2026-09-05
**Area:** Cost model · strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is promoted. Book: empty. A k chosen from three cells is a parameter.**

---

## 1. The three cells

| `rsi`, `keep_v2`, open fill | k=10 | k=20 (D343) | **k=40** |
|---|--:|--:|--:|
| gross bp/bar | +11.52 | **+14.36** | +12.70 |
| cost bp/bar PUB | 17.40 | 11.26 | **7.56** |
| **net bp/bar PUB** | −5.89 | +3.10 | **+5.14** |
| net bp/bar PB | +1.70 | +8.18 | +10.34 |
| **net after GC+HTB, PUB** | −6.09 | +2.90 | **+4.93** |
| vol bp/bar | 323.2 | 310.3 | 304.8 |
| **net Sharpe PUB** | −0.289 | +0.159 | **+0.268** |
| gross Sharpe | +0.566 | +0.735 | +0.661 |
| maxDD bp | 11,402 | 11,125 | **8,423** |
| turnover per bar (names held) | 0.1480 | 0.0955 | 0.0664 |
| held PUB round trip (spread) | 113.1 | 113.4 | 109.3 |
| held price | $45 | $44 | $45 |
| trades | 1,883 | 1,213 | 843 |
| mean move / 2c, PUB | 0.65× | 1.27× | **1.79×** |
| breakeven / measured, PUB | 0.65× | 1.29× | **1.71×** |
| invariant PUB per trade (long / short) | −16.6 (−9.5 / −23.9) | −3.7 (−11.1 / +3.8) | −11.8 (−18.1 / −5.4) |
| group 2: mean / median | +38 / +157 | +75 / +225 | +102 / +253 |
| group 2: trimmed vs 2c | +40 vs 59 | +86 vs 59 | **+122 vs 57** |
| group 2: top 1% / bottom 1% | +70% / −71% | +41% / −54% | **+29% / −46%** |
| group 3: names / to half | 723 / 6 | 621 / 13 | 504 / 12 |
| group 3: years net-positive | 5 of 14 | 7 of 14 | **9 of 14** |
| group 3: dead names' share | 32.0% | 14.5% | 23.0% |
| top trade | KODK **11.5%** | FPRX 5.6% | CYCN 5.3% |

**Q1 confirmed, against D323's unfloored ranking: the longer hold nets more.** k=40 pays
7.6 bp/bar of cost against k=20's 11.3 and k=10's 17.4, and the gross it gives up is
small. Every book-level statistic improves at k=40 — net, Sharpe, drawdown, cost coverage,
years positive, tail shares — while the per-trade lens gets *worse* (−11.8 against −3.7),
which is the two lenses disagreeing once more: a longer hold loses more per trade and
earns more per bar because it pays the round trip a third less often.

**Q2 confirmed:** k=10 is negative under PUB and, on gross, is the *worst* of the three.

## 2. The nulls

| k | gross score | null p50 | null p95 | null max | above k of 24 | PUB net Sharpe | above k of 24 |
|--:|--:|--:|--:|--:|--:|--:|--:|
| 10 | +11.52 | +3.14 | +15.25 | +15.25 | **22 of 24** — inside | −0.289 | 22 of 24 |
| 20 | +14.36 | +5.17 | +11.15 | +13.03 | **24 of 24** | +0.159 | 24 of 24 |
| **40** | **+12.70** | +3.60 | **+8.65** | +10.07 | **24 of 24** | **+0.268** | **24 of 24** |

**Q6 falsified at k=10 and only there**: two rotations beat it on gross. At k=40 the cell is
above all 24 on every one of the four statistics — the only cell in the programme to
manage that — with a gross margin over the best rotation of **2.6 bp/bar** (k=20: 1.3).
Longer holds shrink the null's upper tail as much as they shrink the cell's gross, and the
ordering keeps more of its margin than a random rotation keeps of its luck.

## 3. The mechanism, and where the pre-registration's arithmetic was wrong

**Q3 falsified: turnover is not 1/k.** The ratios are 1.55 and 1.44, not 2. **Q5
confirmed:** the held round trip moves 4% across the three k — the population is the
same, so k is a turnover axis and only a turnover axis, as D296 said. But D296's `1/k`
was measured on a *fixed* hold. Here k is a **cap**: the D303 target closes most
positions before it, so the realised hold rises sub-linearly in k (roughly 6.8, 10.5 and
15 bars) and turnover falls with the realised hold, not the cap. The record's stop
condition said to re-examine the arithmetic before reading: re-examined, the mechanism is
intact and the pre-registration mis-stated its denominator. Cost per bar is round trip
over *realised* hold, and a longer cap lengthens the realised hold by less than itself.

**Q4 falsified: gross does not fall monotonically in k.** It peaks at k=20; k=10 is
lowest. A cap of ten bars cuts `rsi`'s mean reversion off before it completes — the
per-trade median is +157 at k=10 against +253 at k=40 — and the shorter hold pays for
the privilege twice, in cost and in truncated gross. The "ordering dilutes over a longer
hold" premise was wrong for a target-exit book: the target does the exiting, and the cap
only bites when it is short.

**Q7 confirmed, against:** Sharpe 0.268 at k=40. **Q8 falsified at k=10 only**: KODK's
2020 squeeze week is 11.5% of that ledger; the two viable cells have top trades of 5.6%
and 5.3%.

## 4. Predictions

| | | outcome |
|---|---|---|
| **Q1** | *(load-bearing)* PUB net k=40 > k=20 | **CONFIRMED** — +5.14 vs +3.10 |
| **Q2** | PUB net k=10 < k=20 | **CONFIRMED** — −5.89 |
| **Q3** | turnover ∝ 1/k within 15% | **FALSIFIED** — 1.55, 1.44; k is a cap, the target exits first |
| **Q4** | gross falls monotonically in k | **FALSIFIED** — peaks at k=20; k=10 lowest |
| **Q5** | held round trip moves < 35% | **CONFIRMED** — 4% |
| **Q6** | all three above their gross null p95 | **FALSIFIED** at k=10 (22 of 24); k=20 and k=40 above all 24 |
| **Q7** | *(against)* Sharpe k=40 > k=20 | **CONFIRMED** — 0.268 vs 0.159 |
| **Q8** | no top trade > 7% | **FALSIFIED** at k=10 (KODK 11.5%); 5.6% and 5.3% otherwise |
| *check* | k=20 reproduces D343 | to 0.0 |

Four of eight; the load-bearing one held, and both mechanism predictions were wrong in
an instructive way.

## 5. Stop conditions, executed

- **Q1 and Q6 hold at k=40 → the candidate cell moves to k=40 as a declared choice made
  after seeing three cells.** The multiplicity is three; it is written into D342's
  out-of-sample design, which is what protects the choice; **every number from the k=40
  cell is quoted beside k=20's and never alone.** The candidate is now: `rsi` symmetric,
  depth 2, k=40, D303 target, F0, `keep_v2`, open fill — +5.14 PUB, +4.93 after borrow,
  Sharpe 0.27, above all 24 rotations on every statistic.
- **Q3 fails → re-examined before reading** (§3): the arithmetic was on the wrong
  denominator; the mechanism stands.
- **Q6 fails at k=10** → k=10 is out regardless of net, and it is negative anyway.
- **Nothing is promoted.** Sharpe 0.27 still cannot be told from zero on any holdout this
  fixture has; D342's recommendation against spending the read stands. What would change
  it is written there.

## 6. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | cache key; F0 counts; raw factor == census; `keep_v2` share == D343 |
| **[1]** | k=20 reproduces D343's `rsi` v2 cell to **0.0** on net and Sharpe under both conventions and invariant per trade |
| **[T]** | `BASE_HOLD` bites: entries 1,887 / 1,217 / 847; every ledger's max age equals its k |
| **[A]** | the one gate all three k read, rebuilt from the floored score at t−1 by a direct stable argsort, equals the gate on 200 of 200 sampled bars; the unlagged rebuild differs on 200 |
| **[S]** | every k=40 trade equals the open-fill recomputation to 2.2e-16; favourable paths pay positively on every long and short |
| **[RQ]** | same 843 entries under compound accumulation, 763 P&Ls differ; group 1 scores the summed ledger |
| **[2]** | every k's ledger reconstructs gross to < 1 bp with no hole before T−k; rejects a ledger missing a trade |
| **[3]** | symmetric trim in every cell; rejects one deeper |
| **[N]** | rotation moves k=40 gross +12.70 → −0.26; 200 of 200 draws per k, 24 distinct shifts each |
| **[B]** | borrow reconciles to 7.3e-12 on all three cells; `net_bp` untouched |
| **[6]** | raises on +5 bp handed |

**Speed:** 66 s including three nulls (7 s).

## 7. What this establishes

1. **The hold is a cost lever, and it moved the candidate more than anything since the
   floor.** +3.10 → +5.14 PUB, Sharpe 0.16 → 0.27, drawdown down a quarter, nine of
   fourteen years, above all 24 rotations on every statistic. The gross given up (1.7
   bp/bar) is less than half the cost saved (3.7).
2. **Under a target exit, k is a cap and turnover follows the realised hold.** D296's 1/k
   is a fixed-hold result; the pre-registration applied it to the wrong construction and
   both mechanism predictions failed for that reason. A cap of ten bars truncates the
   reversion and pays double for it.
3. **The two lenses disagree in direction on k.** Per trade, k=40 is worse than k=20
   (−11.8 against −3.7); per bar it is better. Opportunity cost, FINDINGS §10, once more:
   the book that trades is the slot-capped one, and it pays the round trip a third less
   often.
4. **A k chosen from three cells is a parameter.** Multiplicity three, stated; the
   out-of-sample design is the protection; the read is still not worth spending at 0.27.

## 8. Files

`data/d344_hold_length.json` · `scripts/run_d344_hold_length.py`
