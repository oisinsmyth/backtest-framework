# D301 — the stack, layer by layer

**Status:** MEASUREMENT, not a study and not a result record. Every construction
here was decided by an earlier record; nothing was searched, nothing is
promoted, and no hypothesis was tested. Runner at `c645a4d`.
**Date:** 2026-09-03
**Area:** Strategy research · **personal track**

**Holdout reads spent: 0. Programme total: 0.**

---

## What it is

The primary signal, the confluence pair, the triple and the best mined exits on
**one identical book** with **one stat block**, so the layers are comparable.
Gate 25, 19 slots, k = 5. Cost columns are `rt × turn` with the robust round
trip (106.7 bp); the runner's original columns carried a spurious `* 2.0` and
have been recomputed — see the D299 correction.

Two guards make the comparison meaningful:

- **`[0]`** the rebuilt triple is identical to `d295.build_inputs` on both legs.
- **`[1]`** D301's simulator is **bit-identical** to `d295.simulate` on both
  rules (24,248 and 30,277 entries). It exists only because d295's trade ledger
  records `(cum, age, side)` and not the **name**, so it cannot answer how many
  names reach half the P&L.

## The table

| construction | gross | Sharpe | maxDD | turn | cost_rob | net_rob | null p95 | p |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| `hist_L` alone | +6.25 | +0.390 | 8,169 | 0.200 | 21.37 | −15.11 | +6.73 | 0.264 |
| `macd_hist` alone | +8.38 | +0.874 | 3,655 | 0.200 | 21.36 | −12.98 | +9.11 | 0.259 |
| `rsi` alone | +11.29 | +0.826 | 7,621 | 0.201 | 21.39 | −10.11 | +11.75 | 0.095 |
| pair mean-rank | +6.79 | +0.599 | 8,225 | 0.200 | 21.37 | −14.57 | +7.26 | 0.124 |
| **TRIPLE** | +7.54 | +0.512 | 9,374 | 0.200 | 21.36 | −13.82 | +7.18 | 0.055 |
| **TRIPLE + target** | **+12.49** | +0.828 | 9,548 | 0.250 | 26.67 | −14.18 | +11.26 | **0.005** |
| TRIPLE + overlay | +8.68 | +0.725 | **3,607** | 0.200 | 21.36 | −12.68 | +7.26 | **0.005** |
| TRIPLE + target + overlay | +11.19 | **+0.863** | 6,290 | 0.250 | 26.67 | −15.48 | +11.24 | 0.065 |

**Every cell is net-negative.**

## TWO COLUMNS THAT MUST NOT BE READ AS THEY STAND

**1. The single-signal rows are at the wrong operating point.** All five layers
run at gate 25 / 19 slots / k = 5, which is `hist_L`'s axis. `macd_hist` was
screened at **N = 50, k = 20** and `rsi` at **N = 10, k = 16**. Those rows
measure the signals *in `hist_L`'s clothes*, not the signals.

**They all beat their nulls in D290 at their own axes**, spread construction:

| signal | N | k | bp | t | min-null-Z |
|---|--:|--:|--:|--:|--:|
| `macd_hist` | 50 | 20 | 54.35 | 4.16 | **+3.21** |
| `rsi` | 10 | 16 | 113.46 | 4.00 | **+2.96** |
| `hist_L` | 25 | 5 | 52.52 | 2.86 | **+1.12** |

So nothing here bears on whether those signals work. Worth noting separately:
**`hist_L` has the weakest null margin of the three and is the one the programme
was built on** — D290's unified ranking chose it on capturability, cost and
name-split as well as null strength, so this is not a contradiction, but it is
worth knowing.

**2. The `beats p95` column is not interpretable for the two overlay rows.** The
null scores **gross mean**, and D297 named that error in its own docstring: *a
mean test would reject an overlay that is out of the market 20% of the time for
earning 20% less, which is arithmetic rather than evidence.* D298 tested those
cells on Sharpe with a matched null and its answer stands
(`target + overlay`, p = 0.0348).

There is a second reason the mean test is unfair here. Adding the overlay takes
the null's median from +5.29 to +4.17 but leaves its p95 at +11.26 → +11.24:
**overlay exposure is endogenous to each draw's own performance**, so a null draw
that runs well de-risks less and keeps its gross. The overlay compresses the
null's middle and not its tail, making the p95 bar no easier while the treatment
gives up mean.

## What the table does say

**The overlay and the target remove overlapping exposure.**

```
TRIPLE        -> + overlay:  sits out 28.8% of bars averaging  -3.95 bp   gross 7.54 -> 8.68  (RISES)
TRIPLE+target -> + overlay:  sits out 21.5% of bars averaging  +6.03 bp   gross 12.49 -> 11.19 (FALLS)
```

On the raw book the overlay removes losing periods. **On the target book it
removes positive ones**, because the target has already cut the bad positions.
That is the mechanism behind D298's small +0.036 interaction, and it means the
combination buys risk reduction (maxDD 9,548 → 6,290) rather than return.

**Trade distribution.** `rsi` alone has a **median trade of +0.0** against a mean
of +28.1, skew +4.59, kurtosis 188.6 — half its trades make nothing, though at
k = 5 against its own k = 16 that is partly an artefact too. The target's median
trade is **+106.1** at a 55.8% win rate and payoff 0.86.

**Concentration.** `hist_L` alone needs **6 names of 1,160** to reach half its
P&L; the target stack needs **18**. The exit diversifies the source.

## The ceiling, found by the self-test

```
[3b] at 19 of 25, at most 6 slots (31.6%) can differ under any rotation
```

**76% of the book is forced by gate membership alone**, whatever the ordering
says. The mean-rank confluence is only choosing 6 slots per leg. That caps how
hard the rank-rotation null can be — every p-value above is generous — and it is
the fact D300 was pre-registered to test.

## Files

`data/d301_stack.json` · `scripts/run_d301_stack.py` · `temp/d301_run.log`
