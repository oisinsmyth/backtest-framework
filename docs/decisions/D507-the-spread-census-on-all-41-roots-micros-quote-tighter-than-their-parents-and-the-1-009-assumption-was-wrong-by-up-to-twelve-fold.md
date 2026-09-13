# D507 — the spread census on all 41 roots: **micros quote tighter than their parents**, the 1.009-tick assumption was wrong by up to **twelvefold**, and it kills HG

**2026-09-13.** Runner [`scripts/d507_spread_all_roots.py`](../../scripts/d507_spread_all_roots.py) ·
fixture [`data/fixtures/fut_spread_all_1m.csv.gz`](../../data/fixtures/fut_spread_all_1m.csv.gz) ·
artifact [`data/d507_spread_all_roots.json`](../../data/d507_spread_all_roots.json).

**41 roots, 13,526,478 front-contract quoted minutes, 2025-09-11 → 2026-09-10, 24.8 min.**
**NO RETURN IS READ** — quoted bid/ask, sizes and order counts only; every quantity is a
dispersion, a fraction or a depth, and none is signed. Nothing admitted ([R15](../RULES.md#r15)).

Extends [D510](D510-RESULT-the-tick-binds-on-ZN-and-ZB-and-on-nothing-else-lane-21s-ES-claim-is-refuted-and-the-property-that-makes-them-predictable-is-what-makes-them-expensive.md),
which measured nine roots, in the two directions that bite the book: **the micros the arm
actually trades**, and **the execution instants rather than the session average.**

---

## 1. The number the book needed: MNQ, not NQ

| | spread, ticks |
|---|---:|
| **assumed everywhere** (D471's ES figure, applied to every root) | **1.009** |
| NQ, the full contract (D510, confirmed here at 3.805) | 3.805 |
| **MNQ, session average** | **2.270** |
| **MNQ, at the execution instants (h10–h15 opens)** | **2.452** |

**The admitted arm's cost goes from 7.000 to 8.452 ticks, +20.7%.** Net per trade falls from
17.923 to **16.472 ticks** (−8.1%), so D504's published net Sharpe of **+0.698 becomes ≈ +0.64**.

**The arm survives its own cost measurement.** C-a wants 0.5 and it clears with room — but this is
the first time that cost line has been measured rather than assumed, and it was assumed low.

## 2. Micros quote TIGHTER than their parents, in ticks

| pair | parent | micro | **ratio** |
|---|---:|---:|---:|
| MBT / BTC | 9.013 | 4.016 | **0.45** |
| **MNQ / NQ** | 3.805 | 2.270 | **0.60** |
| M2K / RTY | 2.427 | 1.934 | 0.80 |
| MYM / YM | 2.643 | 2.268 | 0.86 |
| MES / ES | 1.121 | 1.112 | 0.99 |

**Four of five, and the mechanism is clean:** a micro has the *same* tick in index points as its
parent but a tenth of the notional, so a market maker quoting inside risks a tenth as much per
tick and can afford to. **Using the parent's spread for a micro overstates the cost by up to
40%** — which is the opposite direction from the error I expected, and it means D510's nine-root
table cannot be used for the arm even where it covers the root.

## 3. The 1.009 assumption was wrong in both directions, and by up to twelvefold

| | measured mean | vs 1.009 |
|---|---:|---|
| **ZN** | **1.000** | essentially exact |
| ZF, ZB | 1.002 | exact |
| ZT 1.007 · UB 1.011 · TN 1.015 · ZC 1.032 | | exact |
| ES 1.121 · ZS 1.135 · ZM 1.189 · 6J 1.237 | | ~10–20% low |
| CL 1.683 · ZL 1.650 · SR3 1.849 | | ~65–85% low |
| **HG 2.448** · MNQ 2.270 · RTY 2.427 · YM 2.643 | | **2.2–2.6× low** |
| PA 3.764 · NQ 3.805 · NKD 3.897 · BZ 4.244 · SI 4.657 · **GC 4.478** | | **4× low** |
| **BTC 9.013 · PL 11.505 · RB 12.111 · HO 21.248** | | **9× to 21× low** |

**The assumption was right for exactly the complex nobody has traded** — the Treasury curve and
the grains quote one tick essentially always — **and catastrophically wrong for energy and
metals.** HO's spread is 21 ticks; the programme costed it at 1.

And the depth column says the same thing from the other side: **SR3's touch carries 17,886 lots,
ZT 6,183, ZN 4,846, ZF 2,627** against **NQ 4, GC 4, PL 3, HO 3.**

## 4. The execution instants are mostly TIGHTER — except for the index micros

Conditioning on the open of h10–h15 rather than all session minutes:

    HO 21.248 -> 12.246    RB 12.111 -> 7.375    PL 11.505 -> 8.745    BZ 4.244 -> 2.914

**The session average is polluted by the thin overnight hours**, so for most roots the moment the
arm actually trades is cheaper than the average. **The exceptions are the index micros and YM**:

    MNQ 2.270 -> 2.452     MES 1.112 -> 1.148     YM 2.643 -> 2.707     M2K 1.934 -> 1.953

**The top of the hour is a moment of elevated uncertainty in index futures** and the book widens
into it. For the arm, that means the right figure is the *worse* one — 2.452, not 2.270 — and §1
uses it.

## 5. Re-costing D506, and it kills HG

| root | sized | gross tk | assumed cost | **measured cost** | net assumed | **net measured** | |
|---|---|---:|---:|---:|---:|---:|---|
| **NQ** | MNQ | +24.923 | 7.000 | **8.452** | +17.923 | **+16.472** | still + |
| **NG** | NG | +3.041 | 1.300 | **1.558** | +1.741 | **+1.483** | still + |
| **HG** | HG | +1.534 | 1.240 | **2.500** | **+0.294** | **−0.966** | **SIGN FLIPS** |
| GC | MGC | +1.839 | 4.000 | 7.207 | −2.161 | −5.368 | |
| PL | PL | +1.166 | 1.600 | 9.345 | −0.434 | −8.178 | |
| ES | MES | +3.335 | 3.400 | 3.548 | −0.065 | −0.213 | |
| …22 others | | | | | negative | negative | |

**Only NQ and NG are net-positive at a measured cost**, and NG fails C-d at $1,011 daily σ.

**HG is eliminated.** [D506 §9](D506-RESULT-the-MACD-arm-does-not-transplant-one-root-of-35-clears-its-own-null-and-it-is-the-one-we-already-had.md)
reported HG as the one genuinely new finding of the 36-root search — +2.9 SE over its own rotation
null and ρ = +0.109 with NQ, the decorrelated second root the book has been unable to find. **Its
breakeven crossing was 1.29 ticks and its measured spread is 2.26.** The edge was real and it is
smaller than the cost of taking it.

**So the corrected reading of the whole breadth exercise is: 36 roots, one arm, and it is the arm
we already had.**

## 6. The guard that found the defect, and what it was not looking for

The **integer-tick guard** — a spread must be a whole number of ticks, or the tick is wrong for
that root — **refused to write the census** on the first build:

    [TICK] MBT MBTK6 spread 1,844,659,239.37 ticks at tick_points 5.0

**Databento encodes an absent price as `INT64_MAX`, and `INT64_MAX > 0`**, so a one-sided book
passed a validity filter that tested `bid > 0 & ask > 0 & ask > bid`. `9223372036854775807 × 1e-9
/ 5.0 = 1,844,674,407` — the observed figure. **D510's nine roots never hit it because they are
liquid enough to always quote two-sided; Micro Bitcoin is not.** The filter now rejects the
sentinel explicitly and reports one-sided and crossed drops separately per file, which doubles as
a liquidity measurement.

**The guard was written to catch a wrong tick, and it caught a null-price sentinel.** That is the
third time in this session's data work that a check written for one purpose found something else.

## 7. Limitations, and one of them is directional

- **The window is 2025-09-11 → 2026-09-10, one year**, and every study this re-costs runs on
  2016–2023 or 2016–2026. **A tick is fixed in price terms**, so as a contract's price rose the
  same tick became a smaller share of its move — **a recent spread applied to an older window is
  OPTIMISTIC**, the same direction as [D504](D504-the-MACD-arm-across-every-year-the-fixture-holds.md) §4's
  price-level finding. **Every figure in §5 is therefore a best case.**
- **The quoted spread is a floor on the real cost**: queue position, partial fills and slippage on
  a flip sit on top of it. §1's 8.452 ticks is not what a live account pays; it is the least it
  could pay.
- **MGC, MCL and M6E were never acquired**, so GC, CL and 6E are re-costed on their **full
  contracts' spreads** — which §2 shows overstates a micro's cost by up to 40%. Those three rows
  are flagged and are the least trustworthy in §5. Given GC's full-contract spread is 4.478 ticks,
  an MGC measurement could matter.
- **Front-month determination is D467/D506's volume rule**, reused not re-derived; the micros
  inherit their parent's expiry, which is asserted in the self-test.
