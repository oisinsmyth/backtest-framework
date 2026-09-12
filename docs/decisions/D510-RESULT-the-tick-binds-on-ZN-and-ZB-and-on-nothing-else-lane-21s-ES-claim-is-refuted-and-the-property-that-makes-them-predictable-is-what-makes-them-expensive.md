# D510 RESULT — the tick binds on ZN and ZB and on almost nothing else; lane 21's ES claim is REFUTED on its own terms; and the property that makes them predictable is the property that makes them expensive

> **RENUMBERED D491 -> D510 on 2026-09-12.** This record was committed as **D491** in
> `299cb5d / 84c740b`; a concurrent session had already taken D491 for an unrelated study, and under this
> repository's convention the later writer moves. **No stub is left at D491** — that number
> belongs to the other session's record. Numbers were taken from a reserved block well clear
> of the active frontier (D496) because three sessions are racing the same counter and the
> next-free approach is what produced the collision.

**Pre-registration:** [`D510`](D510-PRE-REG-the-quoted-spread-census-on-bbo-1m-does-the-tick-BIND-and-does-the-spread-rank-the-roots-the-way-tau-did.md),
committed before the runner existed. **Runner:** `scripts/d510_spread_census.py`
(`--selftest` passes, five checks each shown to fire on a broken input). **Build:** 13 `bbo-1m`
files, 7.45 GB, **6.7 min** → `data/fixtures/fut_spread_1m.csv.gz`. **Evidence:**
`data/d510_spread_census.json`. **Window 2025-09-11 → 2026-09-09, 3,169,134 front-contract quoted
minutes. NO RETURN WAS READ.**

**Under [R15](../RULES.md#r15) this record closes nothing and opens nothing.**

---

## 0. THE ANSWER

> **BRANCH B. The roots do not saturate — `P1` runs from 0.012 to 1.000 — so the spread IS the
> discriminator and `τ` was a proxy. But the proxy was a GOOD one: `S1` agrees at ρ = +0.929 on the
> same window, so [D489](D489-RESULT-ZB-IS-large-tick-and-the-sigma-that-failed-C-d-is-the-window-not-the-contract-but-C6s-median-split-cuts-where-the-data-is-densest.md)'s
> ordering is confirmed on an independent quantity.**
>
> **`S3` PASSES and `S2` FAILS. ZN quotes one tick 99.97% of session minutes and ZB 99.80%; ES
> quotes one tick 88.2% of the time. `C6`'s instrument choice is vindicated at the quote level and
> lane 21's *"ES is the canonical large-tick book: the spread is one tick essentially always"* is
> false as written.**
>
> **And the finding neither record anticipated: the property that makes ZN and ZB large-tick is the
> property that makes them expensive to trade. ZN moves FOUR ticks an hour and you pay one to
> cross. ES moves fifty and pays 1.12. On spreads-crossed-per-hour, ZN and ZB are LAST of the
> eight and NQ is FIRST.**

## 1. The census

| root | minutes | **P1** | P2 | P3+ | mean tk | **q orders** | **q lots** | τ_1h (same window) | ticks/h | **cross/h** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **ZN** | 351,199 | **1.000** | 0.000 | 0.000 | 1.000 | **527** | **4,863** | 0.2516 | 4.0 | **4.0** |
| **ZB** | 345,048 | **0.998** | 0.002 | 0.000 | 1.002 | **207** | **1,386** | 0.2578 | 3.9 | **3.9** |
| **ES** | 352,235 | **0.882** | 0.117 | 0.001 | 1.120 | 25 | 36 | 0.0201 | 49.9 | 44.5 |
| 6E | 354,928 | 0.733 | 0.261 | 0.005 | 1.297 | 24 | 74 | 0.0593 | 16.9 | 13.0 |
| CL | 353,116 | 0.502 | 0.392 | 0.106 | 1.678 | 9 | 12 | 0.0158 | 63.3 | 37.8 |
| YM | 353,057 | 0.046 | 0.600 | 0.354 | 2.583 | 6 | 6 | 0.0120 | 83.4 | 32.3 |
| NQ | 352,481 | 0.013 | 0.193 | 0.794 | 3.768 | 4 | 4 | 0.0036 | 281.3 | **74.6** |
| GC | 353,143 | 0.012 | 0.138 | 0.850 | 4.435 | 4 | 4 | 0.0060 | 167.0 | 37.7 |
| *RTY* | *353,927* | *0.131* | *0.575* | *0.293* | *2.377* | *7* | *8* | *0.0139* | *72.2* | *30.4* |

*`cross/h` = `ticks_per_hour ÷ mean_spread_ticks`: how many spread-widths an hour's move spans.
RTY is reported and outside every bar.*

**The queue column is the mechanism and it is not a near thing.** ZN's touch carries **4,863
contracts across 527 orders**; ES's carries **36 across 25**. **ZN's touch is 135× ES's in
contracts.** NQ and GC carry **four** contracts in **four** orders. **That is what a binding tick
looks like and what a non-binding one looks like, and nothing in the corpus had measured it.**

## 2. The three declared conditions

| | condition | observed | |
|---|---|---|---|
| **`S1`** | ρ(P1 order, same-window τ_1h order) ≥ 0.7; UNRESOLVED if ≥5 roots at P1 ≥ 0.95 | **ρ = +0.929**, **2** of 8 saturated — **the tie clause did not fire** | **AGREE.** D489's ordering confirmed on an independent quantity |
| **`S2`** | lane 21 literally: P1(ES) ≥ 0.95 | **P1(ES) = 0.8824**; ES is at two ticks **11.7%** of session minutes | **FAILS** |
| **`S3`** | BOTH ZN and ZB strictly above ES on P1 | **ZN 0.9997, ZB 0.9980 vs ES 0.8824** | **PASSES** |

The two orderings differ by exactly three adjacent transpositions — (ZB,ZN), (6E,ES), (NQ,GC) —
which is what ρ = +0.929 on eight objects means.

## 3. The era control earned its keep, and it was not a formality

τ_1h, same construction, two windows:

| root | τ 2016–23 | τ 2025–26 | ratio | P1 |
|---|---:|---:|---:|---:|
| ZB | 0.1459 | **0.2578** | **1.77×** | 0.998 |
| ZN | 0.1729 | **0.2516** | **1.45×** | 1.000 |
| 6E | 0.0440 | 0.0593 | 1.35× | 0.733 |
| ES | 0.0317 | 0.0201 | 0.63× | 0.882 |
| CL | 0.0301 | 0.0158 | 0.53× | 0.502 |
| NQ | 0.0082 | 0.0036 | 0.44× | 0.013 |
| **GC** | 0.0322 | **0.0060** | **0.19×** | **0.012** |

**The bonds got MORE large-tick; the index and commodities got LESS.** **GC fell by 5.3× and is now
the least large-tick root of the eight** — gold's 2025–26 volatility has left its $10 tick far
behind, and its `P1` of 0.012 confirms it independently. **In 2016–23 GC sat at rank 4 beside ES; it
is now rank 7.**

> **Without the control, every one of those moves would have been read as a horizon effect.** The
> pre-registration required this comparison for exactly that reason and it changed the reading.

## 4. Predictions — SIX OF SEVEN MISSED, and the only clean hit was the wall clock

| | predicted | observed | |
|---|---|---|---|
| **`P-a`** | `S2` passes, P1(ES) ≥ 0.97 | **0.882** | **WRONG.** ES is at two ticks one minute in nine |
| **`P-b`** | `S3` **fails**; ZB 0.85–0.95 and **below** ES | **ZB 0.998, far above ES** | **WRONG**, and it was the prediction written to cost me. It cost me the other way |
| **`P-c`** | `S1` UNRESOLVED on the tie clause; ES, ZN, GC, CL, 6E all > 0.95 | **2 of 8 saturated**; GC 0.012, CL 0.502 | **WRONG.** I expected a ceiling and found a 98-point range |
| **`P-d`** | NQ **lowest** P1, 0.55–0.80 | NQ **0.013**, second-lowest behind GC 0.012 | **WRONG on both clauses** — off by 54–79 pp, and GC is lower. Right only that NQ is near the bottom |
| **`P-e`** | `cross/h` is nearly circular and must not be read as independent | **Branch B, so the reasoning does not apply** — and `cross/h` **inverts** the ordering rather than reproducing it | **the caution was right, the reason was wrong.** See §6 |
| **`P-f`** | ZB's quote materially wider overnight than 08:00–10:00 | **0.9945 → 0.9998 across every session hour: a range of 0.53 pp** | **WRONG.** ZB's spread does not widen at any hour. See §5 |
| **`P-g`** | under 8 minutes | **6.7 min** | **RIGHT** |

> **Six substantive misses out of seven.** The pattern in the last two records was *optimistic*
> misses about ZB; **this one is a miss in the same direction again** — ZB's quote is tighter, more
> stable and deeper than I predicted. **Three records running where the errors all favour the same
> instrument is a reason to distrust my priors about ZB, not a reason to like ZB.** Every number
> above is a cost/liquidity fact; **none of them is an edge**, and §7 says so.

## 5. `P-f`: ZB's spread and ZB's volatility are DECOUPLED across the clock

D489's `R1b` found ZB's σ varies **1.8×** across the session — a 7-hour evening hold is $379 and a
7-hour day hold is $682. **The spread does not vary at all:** `P1` sits between **0.9945 (18:00)**
and **0.9998 (15:00)**, a range of **0.53 percentage points**, while the touch queue triples from
**85 orders at 18:00 to 346 at 15:00**.

> **That is precisely what a binding tick means: the spread CANNOT narrow below one tick, so the
> liquidity variation has nowhere to go but into DEPTH.** The quote is pinned at all hours and the
> book gets thicker or thinner behind it. **Volatility and spread are independent on ZB across the
> clock — a claim the hourly census can make and `τ` structurally could not.**

*(Hour 17:00, the CME maintenance halt, sits at P1 0.9529 on 1,273 minutes. It is outside the
declared 18:00→16:00 session and is reported rather than scored — "the quote is wide during the
halt" is not a fact about ZB's liquidity. An earlier draft of the runner let that hour set the
"widest quote" headline; it was corrected before this record was written.)*

## 6. THE FINDING NEITHER RECORD ANTICIPATED, and it cuts against `C6`

`cross/h` was declared under `P-e` as a quantity I expected to be **circular**. Under Branch B it is
not circular, and it **inverts** the ranking:

| | ZN | ZB | 6E | YM | GC | CL | ES | **NQ** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **cross/h** | **4.0** | **3.9** | 13.0 | 32.3 | 37.7 | 37.8 | 44.5 | **74.6** |

**ZN moves 4.0 ticks an hour and the spread is 1.0 tick. ES moves 49.9 and the spread is 1.12.**

> **The same coarse tick that pins ZN's quote and stacks 4,863 lots behind it is a tick the price
> only crosses four times an hour.** `C6`'s premise — that large-tick books carry predictable
> short-horizon direction — is **confirmed as a premise** by §1. But **the predictable move and the
> cost of taking it are the SAME quantity on a large-tick book**, and that is a structural tension
> `C6`'s row never priced.

**This is stated as a post-hoc observation on a pre-declared quantity, not as a test.** It was not
one of `S1`–`S3`, nothing was scored on it, and it decides nothing. **It is the number the next
person designing a `C6` stage 1 has to answer**, and it is now on the record rather than waiting to
be discovered after a runner exists.

## 7. What this changes

**Confirmed, on an independent quantity:** D489's `T1`, `T2` and `T3` all stand. **ZN and ZB are the
large-tick outrights, and `C6` named the right pair.**

**Corrected:**

1. **Lane 21's ES claim is false as written** and should be amended where it appears. **ES's spread
   is one tick 88.2% of session minutes, not "essentially always", and its touch carries 36 lots
   against ZN's 4,863.** D489 §4 tried to rescue the claim by assigning it to the per-event horizon;
   **the direct census says it does not hold at the quote either.** *That rescue is withdrawn.*
2. **My D489 recommendation — "replace `C6`'s median split with the gap split, `{ZN, ZB}` versus the
   other six" — is only half-safe.** The ORDER is robust (ρ +0.929) but the TIER BOUNDARY is not:
   **on τ the largest gap is ZB→6E (3.3×); on `P1` it is CL→YM (0.502→0.046).** A gap split on `P1`
   gives a **five/three** tiering, not two/six. **`C6` must say WHICH quantity defines its tiers**,
   and that is a specification question for the principal, not something this record settles.
3. **`C-d` and cost are separate axes and `P1` speaks only to cost.** Nothing here touches
   [D468](D468-RESULT-none-of-24-session-windows-on-eight-roots-clears-the-component-standard-the-best-sits-at-the-78th-percentile-of-its-family-null.md)'s
   `C-a` rejection of ZB (gross Sharpe +0.10/+0.05/+0.05). **A pinned one-tick spread on a deep book
   is a precondition for monetising an edge, not evidence of one.**

## 8. What was spent

**A quote census on 2025-09-11 → 2026-09-09. NO RETURN WAS READ, no construction was scored, no
component line was computed, and the 2024+ slice remains unspent for every return-bearing line** —
including the overnight leg on NQ/ES/SPY/IWM, which a separate record already spent and which this
one does not touch. **A later study may not claim this slice was already gone.**

**Cost: one pre-registration, one runner, one 6.7-minute build, one new committed fixture
(`fut_spread_1m.csv.gz`, 150,349 rows).**
