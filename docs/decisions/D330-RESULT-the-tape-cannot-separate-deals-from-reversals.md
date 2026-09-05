# D330 RESULT — the artefact lives in two places, and the tape cannot separate deals from reversals

**Status:** RESULT. Pre-registered at `112bebd`, runners at `2eb7a47` — both
before this file existed (R8).
**Date:** 2026-09-05
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is promoted.**

---

## Part A — where the pinned names are. Look-ahead; never scored

46 signals × 2 legs, path-invariant ledger, depth 2, k=20. Labels use the
future and are diagnostic only.

### A.1 The short side: it is a `skew_63` problem, not a programme problem

| short leg | trades | dies | **pinned** | pinned P&L | pinned half | collapse | alive P&L | alive half |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| **skew_63** | 1,024 | 29% | **21%** | +8.3 | 4.4 | 0% | +47.3 | 9.0 |
| dist_lvn | 1,879 | 15% | 12% | +10.0 | 2.6 | 0% | +49.1 | 6.1 |
| on_share | 1,358 | 10% | 7% | +51.3 | 3.2 | 0% | −43.3 | 0.0 |
| *median of 46* | | | **1.5%** | | | 0.3% | | |
| hist_L | 1,419 | 5% | 1.2% | +46.5 | 9.7 | 1.0% | −18.8 | 48.0 |

**Median pinned fraction across the 46 short legs is 1.5%.** `skew_63` at 21%
is the outlier by a factor of two over the next signal and fourteen over the
median. **The incumbent's short leg is clean** — 1.2% pinned, 1.0% collapse.

**Collapses are rare everywhere** — median 0.3%, maximum 4.4%
(`park_vol_21`, `atr_norm`, `cs_spread`, `rvol21`, `ivol_21`, all ~4%) — and
where they occur they pay **+1,300 to +3,500 bp per trade**. That is the short
edge the dead-inclusive fixture exists to include, and it sits in the
high-volatility legs, not in `skew_63`, which has none.

### A.2 The long side: every volatility score's long leg is a third takeover targets

| long leg | trades | dies | **pinned** | pinned P&L | **alive P&L** | **alive half** |
|---|--:|--:|--:|--:|--:|--:|
| **atr_norm** | 963 | 36% | **35%** | −34.0 | −50.5 | **0.0** |
| **park_vol_21** | 973 | 34% | **34%** | −25.0 | −48.1 | **0.0** |
| **rvol21** | 975 | 34% | **31%** | −37.9 | −48.8 | **0.0** |
| **ivol_21** | 983 | 33% | **31%** | −31.5 | −61.5 | **0.0** |
| **max_ret_21** | 1,023 | 31% | **29%** | −32.6 | −53.8 | **0.0** |
| **range_frac** | 1,665 | 31% | **29%** | −40.2 | −54.2 | **0.0** |
| vol_ratio | 1,814 | 29% | 24% | −28.8 | −46.3 | 6.3 |
| cs_spread | 1,253 | 14% | 12% | −35.4 | −42.3 | 0.0 |
| *median of 46* | | | **1.0%** | | | |
| hist_L | 1,413 | 3% | 0.2% | | +190.7 | 52.3 |
| skew_63 | 923 | 4% | 1.4% | | +78.6 | 9.1 |

**The lowest-volatility name on the tape is a stock pinned at a deal price.**
So the long end of every axis-E and vol-family score — the "quietest" names —
is 24–35% pinned takeover targets, and its *alive* names carry a held
half-spread of **exactly 0.0**: the survivors are pinned too, just not yet
delisted. A long on a pinned name loses the market's drift (−25 to −40 per
trade, demeaned), and the whole leg nets −45 to −60.

**This is why axis E's long legs looked like the cheapest books in D290 and
why three D329 enumeration cells divided by zero.** A range-based spread
estimator reads the least tradeable names on the tape as the cheapest, and a
low-vol ranking selects for exactly them.

## Part B — the causal filter. Two of six falsified, and the two that matter for separability

The filter fires on **0.18%** of live name-bars — and removes the rank-0 short
name on **1,442 of 4,187 bars**. It hits `skew_63`'s top pick a third of the
time.

| | prediction | outcome |
|---|---|---|
| **Q1** | catches > 80% of pinned; removes < 10% of survivors | **FALSIFIED** — catches **71%**, removes **39.3%** of survivors |
| **Q2** | filtered short-leg half-spread ≥ 8.5 bp | **CONFIRMED** — 7.7 → **11.1** |
| **Q3** | trimmed-both mean moves < 10 bp | **FALSIFIED** — +46.8 → +36.3, a move of **10.5** |
| **Q4** | LW_f net per trade FALLS below LW's *(load-bearing, against)* | **CONFIRMED** — **+63.26 → +51.05** |
| **Q5** | removes < 2% of the LONG leg | **CONFIRMED** — **0.0%** |
| **Q6** | LW_f still beats S_f and H, both lenses *(load-bearing)* | **CONFIRMED** — +51.05 vs +30.36 / −0.89; Sharpe +0.224 vs +0.152 / −0.082 |

### B.1 What the filter did to `skew_63`'s short leg

| | trades | gross | **net** | t | half | premium |
|---|--:|--:|--:|--:|--:|--:|
| unfiltered | 1,024 | +32.0 | **+16.6** | +0.92 | 7.7 | −23.5 |
| filtered | 1,101 | +14.3 | **−8.0** | +0.38 | 11.1 | −22.1 |

**The filtered short leg loses money per trade.** Its cost became honest (Q2)
and its gross more than halved — because the filter removed 39% of the
survivors along with 71% of the pinned names. "A +20% day, then quiet" is the
signature of a pinned deal **and** of a post-jump reversal candidate that has
calmed down. **On the tape, those are the same object.**

### B.2 The construction survives; the book halves

| arm, k=20 | net/trade | Sharpe | maxDD |
|---|--:|--:|--:|
| LW | +63.26 | +0.434 | 28,278 |
| **LW_f** | **+51.05** | **+0.224** | 28,658 |
| S_f | +30.36 | +0.152 | 25,607 |
| H | −0.89 | −0.082 | 43,956 |

Q6 held: the leg-wise book beats both parents *even over-filtered*. That is
the robust part, and it says leg ownership was not the deal artefact. **But
the Sharpe halves**, and `skew_63` alone drops from +0.421 to +0.152 — most of
its book-level quality was in the trades the filter removes, honest or not.

## What this establishes

1. **The honest number for the leg-wise book is a bound, not a point.** Net
   per trade **between +51.05 (over-filtered) and +63.26 (deal-contaminated)**;
   Sharpe **between +0.224 and +0.434**. D329 §1 is amended to say so.
2. **`skew_63`'s short leg is unresolved, not retired.** Q3's pre-registered
   stop condition — "not separable → `skew_63` is a deal detector, retire it"
   — *presumed a working filter*. Q1 failed too, so the Q3 miss (10.5 against
   10) is confounded by the filter's bluntness, not evidence of inseparability
   in principle. **I am not invoking that stop condition, and this line is the
   record of the judgment.** What Q1's failure does establish is its own stop
   condition: **the tape signature is not the instrument; a deal-event source
   is required.**
3. **The artefact is concentrated, and now mapped.** Two places: `skew_63`'s
   short leg (21%) and the long leg of every volatility score (24–35%).
   Elsewhere it is 1–2%. `hist_L` is clean on both legs.
4. **The vol-family long legs were never books.** A third pinned, the rest at
   zero measured spread, netting −45 to −60. Any D290 reading of axis E's long
   side is a reading of takeover targets.
5. **Collapses — the genuine short edge on a dead-inclusive fixture — are
   0–4% of trades and pay +1,300 to +3,500 each, in the high-vol legs.** That
   is where a short book's fat right tail comes from and it was never in
   `skew_63`.

## What is owed

1. **A deal-event source.** The fixture's event file carries dividends and
   splits only. Without announced-deal dates, no causal filter on this tape
   can separate a deal from a reversal, and no short leg built on a jump
   detector can be costed honestly.
2. **The spread estimator's floor** (D329 §5, FINDINGS §16) — now with a
   mechanism: the zero-range names *are* the pinned deals.
3. **A borrow-cost term**, still.
4. **The long leg for the leg-wise book**, from the profile side, now with the
   knowledge that every low-vol candidate is disqualified.

## Assertions

All twelve pass, all properties of the code.

| Part A | |
|---|---|
| **[P]** | every ledger P&L reproduced to 4.4e-16 |
| **[D]** | CENSORING: a name alive at the sample end is never dying; one dead in 3 bars is |
| **[G]** | pinned / collapse / other partition the 336 dying trades |
| **[I]** | `skew_63`'s short leg reproduces D329 §10: 1,024 / 297 / 284 / 0; with the range condition, pinned = 212 |
| **[6]** | raises on a living trade given a dying label |

| Part B | |
|---|---|
| **[K]** | CAUSALITY: deleting every bar after T0 = 2093 leaves the filter bit-identical before T0 |
| **[F]** | the filter fires: S_f differs from S on both lenses |
| **[1]** | unfiltered arms reproduce D329's k=20 cells to 0.0e+00 |
| **[L]** | LW_f's long ledger is H's, its short ledger is S_f's, bit-identically, both lenses |
| **[R]** | REFILL: at all 1,442 bars where the rank-0 short name is filtered, a different name holds rank 0 |
| **[C]** | per-leg 2c is 2 × that leg's held median half-spread |
| **[6]** | raises on a book handed free money |

**Speed:** A 89 s, B 68 s, in parallel. Both built on the transposed layout
with contiguous windows, and neither re-reads the score archive inside a loop.

## Files

`data/d330a_pinned_decomposition.json` · `data/d330b_causal_filter.json` ·
`scripts/run_d330a_pinned_decomposition.py` · `scripts/run_d330b_causal_filter.py`

---

## AMENDMENT, 2026-09-05 — Part A's "survivor" label does not mean "not a deal"

Appended after D331 ran the event source against these labels. Part A called
a trade a *survivor* if its name was still trading 60 bars after entry. A US
public deal takes four to six months to close. **D331 finds a target-specific
deal form (DEFM14A, tender offer) within 63 bars of entry for 27.1% of the
727 "survivors" in `skew_63`'s short leg** — pinned targets whose deal had not
yet closed. Part A's "+47.3 bp gross on the survivors, a genuine post-jump
reversal" is therefore partly deals, and the D330 B survivor-removal test
(39%) was measured against a contaminated denominator. **The instrument that
labels a non-deal is the event source, not the tape's death date.** §What this
establishes item 5 and FINDINGS §16's "the edge that survives is real" are
amended by D331 §1–2: with the deals removed by target-specific filings, the
short leg nets −24 to −30 (PB) / −61 to −65 (PUB) per trade across the two
EDGAR passes, and `skew_63` is retired as a short signal.
