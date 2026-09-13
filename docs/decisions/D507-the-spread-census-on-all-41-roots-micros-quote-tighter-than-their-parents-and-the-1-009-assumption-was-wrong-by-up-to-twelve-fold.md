# D507 — the spread census on all 41 roots: **micros quote tighter than their parents**, the 1.009-tick assumption was wrong by up to **twelvefold**, and it kills HG

> ## ⚠ AMENDED — §8 CORRECTS THREE THINGS IN §1–§7
>
> [D508](D508-the-crossing-cost-actually-paid-from-tbbo.md) measured the crossing cost from
> `tbbo` — the book immediately before each trade — for the micros `bbo-1m` never covered.
> It corrects this record in three places:
>
> 1. **§5's 6E row has a UNIT ERROR.** M6E's tick is *double* 6E's, so the crossing in M6E
>    ticks is half what §5 charged.
> 2. **§2's headline generalisation is WRONG.** On the cost actually paid, **three of eight
>    micros are *more* expensive than their parents**, not one of five.
> 3. **§5's GC, CL and 6E rows overstate the crossing by up to 75%**, because they used the
>    full contract's spread where the micro's is now measured.
>
> **What does NOT change: no verdict in §5 flips.** The admitted arm survives, HG still dies,
> and GC/CL/6E stay negative. §1–§7 stand as written; §8 is the correction.

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

---

# 8. AMENDMENT — three corrections from D508's `tbbo` measurement

[D508](D508-the-crossing-cost-actually-paid-from-tbbo.md) measures the crossing cost from `tbbo`,
which carries the book **immediately before each trade** and therefore gives what the aggressor
**actually paid** — `2·|price − mid| / tick` — rather than a quoted spread sampled every minute.
`tbbo` was bought for **every instrument**, so the three micros `bbo-1m` never covered are on disk.

**Provisional window: 2026-09-01 → 09-10, 18,364,637 trades across 16 roots.** The full year is
decoding; these figures are a 10-day sample whose per-root trade counts run from 25,707 (M6E) to
6,862,203 (MNQ), so the *means* are precise and only the **time variation** is unmeasured.

## 8a. §5's 6E row has a unit error — M6E's tick is DOUBLE 6E's

    MGC/GC   0.1    vs 0.1      SAME        MES/ES   0.25 vs 0.25   SAME
    MCL/CL   0.01   vs 0.01     SAME        MNQ/NQ   0.25 vs 0.25   SAME
    M6E/6E   0.0001 vs 0.00005  **DOUBLE**  MYM/YM   1.0  vs 1.0    SAME

§2 generalised *"a micro has the same tick in index points as its parent"* from five index pairs.
**M6E breaks it**, so a spread expressed in 6E ticks is **half as many M6E ticks**, and §5 charged
6E the full 6E-tick figure against an M6E-tick commission:

| | §5 as published | **corrected** |
|---|---:|---:|
| 6E measured cost | 3.662 tk | **3.031 tk** |
| 6E net measured | −4.543 tk | **−3.912 tk** |

**Still negative — the verdict holds.** The self-test computes this discrepancy from D507's own
artifact so the correction is evidenced rather than asserted.

## 8b. §2's headline is wrong: on the cost actually PAID, three of eight micros are DEARER

| tighter than parent | ratio | | **dearer than parent** | **ratio** |
|---|---:|---|---|---:|
| MBT / BTC | 0.63 | | **M2K / RTY** | **1.37** |
| MNQ / NQ | 0.83 | | **MCL / CL** | **1.29** |
| MGC / GC | 0.87 | | **MES / ES** | **1.07** |
| MYM / YM | 0.95 | | M6E / 6E | 1.01 |

**§2's "four of five, and the mechanism is clean" does not survive the better statistic.** The
mechanism I gave — same tick, a tenth of the notional, so a maker can quote inside — explains the
index micros on a *time-weighted* spread and fails on the *trade-weighted* cost for rates,
crude and the S&P. **The honest statement is that it splits by asset class and I generalised from
five pairs measured the wrong way.**

## 8c. The calibration, which is the most useful thing here

`bbo-1m` is **time-weighted** (a snapshot every minute, traded or not). `tbbo` is
**trade-weighted** (the book when someone transacted). Trades cluster when the book is tight, so:

| | `bbo-1m`, D507 | `tbbo` effective, D508 | overstatement |
|---|---:|---:|---:|
| NQ | 3.505 | **2.324** | +51% |
| GC | 4.207 | **2.767** | +52% |
| **MNQ** | **2.452** | **1.936** | **+27%** |
| ES | 1.109 | **1.029** | +8% |

**A time-weighted spread overstates what a transacting trader pays by 8–52%.** Both are
legitimate and they answer different questions: for a market order that *must* fire at a fixed
instant the time-weighted figure is the honest upper bound, and the trade-weighted one is what
you get if liquidity is there when you arrive.

**So the admitted arm's crossing is BRACKETED, not a point estimate: 1.936 to 2.452 ticks.**

| MNQ crossing | cost, ticks | D504's net Sharpe becomes |
|---|---:|---:|
| 1.009 assumed (as published) | 7.009 | +0.698 |
| **1.936 (trade-weighted)** | 7.936 | **≈ +0.67** |
| **2.452 (time-weighted)** | 8.452 | **≈ +0.65** |

**The arm clears C-a on both bounds.** That is the substantive outcome: its cost line is no longer
an assumption, and it is now known to within half a tick.

## 8d. And §5's GC, CL and 6E rows overstate the crossing by up to 75%

§5 flagged those three as re-costed on their full contracts' spreads. Measured:

| | §5 used (parent) | **micro measured** | overstatement | corrected net |
|---|---:|---:|---:|---:|
| **GC → MGC** | 4.207 | **2.404** | **+75%** | −3.565 tk (was −5.368) |
| CL → MCL | 1.501 | 1.560 | −4% | −6.092 tk (was −6.033) |
| 6E → M6E | 1.262 | 1.057 | +19% | −3.912 tk (was −4.543) |

**No verdict flips.** And MGC at **$2.40 a round trip** is the **most expensive micro to cross** in
the acquired universe, against a $3 commission — worth knowing before anyone proposes gold.

## 8e. One thing only `tbbo` could show

The **effective** cost exceeds the **quoted** spread on every root — MGC 2.404 against 1.920, MNQ
1.936 against 1.427 — because a trade that sweeps beyond the touch pays more than the quote.
**A quoted spread is structurally a floor**, and this is the first measurement in this programme
that prices the part above it.
