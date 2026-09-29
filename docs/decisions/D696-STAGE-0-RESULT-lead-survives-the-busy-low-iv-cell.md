# D696 STAGE 0 RESULT — LEAD SURVIVES: busy realised range that the options market does not price forward is the worst cell for the break beyond the search (0 of 2,182 rotations), and the same pre-specified cell is the worst for a different break it never saw (D663's, 0.7 % of rotations). In-sample only.

*2026-09-29. In-sample, 2018-01-09 → 2025-02-28; the vault was never read. The principal: "Yes write the pre-reg and
run it". Pre-registration [D696 STAGE 0 DESIGN](D696-STAGE-0-DESIGN-the-busy-low-iv-cell.md) (`5ac1497b`), committed
alone before its runner.*
- **The runner** `scripts/stage0_d696_busy_low_iv.py` was committed before any outcome (`f82d6467`). It ran once, in
  1.3 min. Output: `data/stage0_d696_busy_low_iv.json`, statistics only.
- **Labels and trades are D694's cached bundle.**
- **Known answers held before anything was scored:**
  - D694's grid was reproduced cell by cell;
  - D663's morning F was reproduced: ES 2,138 breaks, +0.30905 bp; NQ 2,118, −0.65576;
  - every E4 trade was re-derived bar by bar to D694's gross exactly.

## The answer in one line

**The cell survives every test the in-sample window can still give it.**
- X = compression tercile 3 with the IV/RV percentile < 1/2.
- **It is not the worst of six by chance:** S = −3.35 against a rotation p5 of −1.68, and no offset reaches it.
- **It carries IV information beyond the label's realised part,** narrowly: 2.3 % of the ingredient rotations.
- **The same pre-specified cell is the worst for D663's opening-range break,** a trade with a different clock, entry and
  exit that no grid had split: joint z −1.93 against p5 −1.31.
- **It is still in-sample.** It has earned a pre-registration on unseen data, not a place in any book.

## A. Beyond the search (trade 1: D694's E4 breaks; ES 1,118, NQ 1,110)

**Cell z-scores, each cell's mean gross over its SE.** Rows are ctier terciles and columns IV/RV halves (low | high).

| tercile | ES | NQ | **joint** |
|---|---|---|---|
| 1 | +1.64 \| +2.37 | +3.27 \| +1.59 | +3.47 \| +2.80 |
| 2 | +1.26 \| +1.08 | +0.57 \| +1.30 | +1.30 \| +1.68 |
| 3 | **−1.77** \| +0.21 | **−2.96** \| +2.12 | **−3.35** \| +1.64 |

- **X is the joint argmin, as asserted.** It is the only negative cell on either root.

| null (same k on both roots, enumerated, p5 SE = 0) | offsets | p50 | p5 | share at or below −3.35 | |
|---|---:|---:|---:|---:|---|
| **A1, the whole IV label rotated** | 2,182 | −0.69 | −1.68 | **0.000** | **pass** |
| A2, only ln IV's residual on the realised measures rotated | 2,179 | −2.17 | −3.18 | **0.023** | pass (thin) |

**Reading A2 honestly:**
- A2's median is −2.17. Keeping the realised part of the label and scrambling IV's own information already produces a
  jointly bad cell of about −2.2 most of the time.
- **Most of the cell's badness is realised information:** busy recent range, and IV that is low *given* realised.
- IV's own information supplies the increment from about −2.2 to −3.35. That increment is beyond the p5, by 0.16 z.
- The design's label for this outcome is "IV information", and it stands. A thin margin on an enumerated null is still
  a pass (its SE is 0), but it is the weakest link in this record.

**D694's grid dropped sessions with ctier = 1.0** from its top band (`ct < 1`). D696's declared "ctier ≥ 2/3" adds 5
(ES) and 3 (NQ) trades to tercile 3. All of them landed in Y, so X is unchanged: 85 and 99 trades.

## B. The mechanism (trade 1; readings declared in the design)

| | ES X (85) | ES Y (285) | ES rest (748) | NQ X (99) | NQ Y (273) | NQ rest (738) |
|---|---:|---:|---:|---:|---:|---:|
| gross bp | −7.37 | +0.47 | +4.31 | −14.71 | +6.34 | +6.40 |
| stop exits | 85 % | 95 % | 84 % | 89 % | 93 % | 84 % |
| MFE bp | 47.5 | 60.3 | 50.6 | **60.4** | 81.9 | 66.3 |
| MAE bp | −54.5 | −66.5 | −51.4 | **−98.8** | −79.4 | −64.5 |
| hold-to-close bp (no stop) | −0.3 | −6.6 | +2.0 | **−23.4** | +3.6 | +7.8 |
| range already made before entry | 51 % | 45 % | 38 % | 49 % | 45 % | 40 % |
| mean entry | 11:10 | 10:47 | 10:40 | 10:45 | 10:35 | 10:32 |

**The declared readings:**

| root | reading | hold-to-close t | MFE X vs Y, Welch t |
|---|---|---:|---:|
| **NQ** | **REVERSAL** | −2.11 | −2.81 |
| **ES** | **NEITHER** | −0.06 | −1.83 |

- **On NQ the break in X is a false break.** It gets less far in its favour, goes much further against, and is 23 bp
  the wrong way by the close.
- **On ES it is a smaller day that goes nowhere.** Less favourable excursion, a flat close.
- **What X shares on both roots:**
  - the break fires later in the morning;
  - it fires after about half the day's range is already made, against about 40 % elsewhere.
  That is the "spent range" story. On NQ, where the break then reverses, the reversal is what the rule reads.

## C. The prediction on a trade the grid never saw (D663's opening-range break, 60-minute F)

- **Window breaks:** ES 1,667 and NQ 1,620. X holds 143 and 161.
- **Mean F in X:** ES −4.18 bp, NQ −4.95 bp. D663's all-break means are +0.31 and −0.66.

**Joint z grid** (low | high IV/RV):

| tercile | joint |
|---|---|
| 1 | +0.82 \| −0.51 |
| 2 | −1.50 \| +0.98 |
| 3 | **−1.93** \| +1.22 |

- **C-i holds:** X is the jointly worst cell. Per root it is the worst on ES; on NQ it is second, just behind tercile 2
  low (−1.40 against X's −1.33).
- **C-ii passes:** X's joint z of −1.93 against the fixed-cell rotation's p5 of −1.31 and p50 of +0.02. Only **0.7 %**
  of 2,182 offsets are at or below it.
- **This is the result that makes the lead worth carrying.** The cell was named before this trade was split. The trade
  has a different entry (10:00–11:29, off the opening range), a different exit (60 minutes, no stop) and a different
  clock. Its days overlap trade 1's, so it is corroboration, not an independent sample.

## Predictions (§6 of the design)

| # | prediction | outcome |
|---|---|---|
| 1 | A1 passes | **held** (0 of 2,182) |
| 2 | A2 fails (the cell is the realised part) | **failed**: A2 passes, thinly (2.3 %). Most of the cell is realised, and IV adds a real increment. |
| 3 | B reads SPENT RANGE on both roots | **failed**: NQ REVERSAL, ES NEITHER |
| 4 | C-ii fails (a property of E4's stop) | **failed**: C-ii passes (0.7 %). The cell is a property of the day, not of E4. |

## What it would be worth, and the routes to confirming it

**The size of the prize, from the grid (arithmetic, NOT a result).** The cell was chosen for being worst, so this
number is biased upward. Vetoing X from the plain break (D694's net, friction once) would move:
- ES: from +0.04 to about +0.84 bp a trade;
- NQ: from +2.64 to about +4.52 bp.

NQ's REVERSAL reading also suggests the opposite trade (fading NQ breaks in X). That is a different construction and
has not been examined at all.

**The expected count on unseen data:**

| | X share | vault 2025-03 → 2026-09-18 | forward (Track 2) |
|---|---:|---:|---:|
| E4 breaks | ~7.6 % | ~18 a root | ~11 a root a year |
| D663's breaks | ~9 % | ~33 a root | ~21 a root a year |

**No single unseen slice confirms a per-trade mean with power.** A confirmation design has to pool the two roots and
the two breaks, or use the cell's rank, or wait for forward data. **That is the question for the next
pre-registration, on the principal's word.**

## Deviations (none replaces a verdict)

1. **D694's grid omitted ctier = 1.0 from its top band.** D696 reproduced D694's grid under D694's rule and then
   scored its own declared cell. The 5 and 3 added trades all landed in Y.
2. **The mechanism's second implementation ran on every 50th trade** (about 22 a root), not on all of them.

## Routing (§7 of the design)

**LEAD SURVIVES, so the next step is a separate pre-registration for unseen data, on the principal's word.** It states:
- the vault's and forward recording's expected counts (above) first;
- how it pools the roots and breaks;
- whether the object is a veto of the plain break, the NQ fade, or the cell's rank;
- the vault slot it would need (7 or 10 are free);
- the prerequisites: the vault-input bar path, an NQ options fixture past 2025-02-28, and ES's options ending
  2026-09-09.
