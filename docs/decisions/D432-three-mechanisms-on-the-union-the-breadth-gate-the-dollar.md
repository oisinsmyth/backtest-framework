# D432 — three mechanisms on the union: the breadth gate on the long arm, the dollar-volume lever on cell 2, and the gap structure by half

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D432-three-mechanisms-on-the-union-the-breadth-gate-the-dollar-volume-lever-and-the-gap-by-half.md`. The H1 above is the full title.*

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file. D400–D431
used, D407–D410 and D390–D399 reserved. Daily bars. **All data here is spent for this line
(universe + holdout 1); `holdout2` is not touched. A pass is in-sample evidence.** The one
transfer check left is agreement between the in-sample half and the holdout half, so every table
carries both.

## 1. What each mechanism is, and why it is a mechanism rather than a split

**M1 — the breadth gate on the long arm.** D430's long arm inverted on new names through a left
tail in 2020 and 2022. Stage 0 (dates only, no outcome bar): cell-2 long touches per day on the
union have median 2, p95 19, max 193; a trailing-5-day breadth above its p90 marks a market
falling broadly; **27% of the long pool's trades fall on such days, and in the years the long
arm lost — 2022 54%, 2018 45%, 2024 38%, 2020 35% — against 17–24% where it paid.** Only 3.4% of
the short pool's trades do. *A second demand zone in one name is a bounce; in forty names in a
week it is a market falling.* The gate: **drop a long touch when the trailing-5 cell-2 long
breadth on its touch day (known at that close, computed on the union's own event stream) exceeds
58, the union's p90, frozen.** The short arm is reported through the same gate and predicted
unchanged.

**M2 — dollar volume as the cost lever on the rung that transfers.** Cell 2 is +26 gross on the
union and +18 on the holdout half at ~29 bp cost. D413 found dollar volume, not price, is what
moves cost. Terciles of trailing ADV inside cell 2, cuts fixed on the union and printed: gross,
cost, net by tercile, both halves, three windows; the top tercile's 10-slot book. The question:
**is there a tercile of the smallest transferable object that nets positive on new names with
nothing layered on it?**

**M3 — the gap structure by half.** D426 found the second zone that pays is the one arriving after
the first trade resolved (gap 6–10 +61, 3–5 +57, 11–20 +39 in-sample). Holdout-half counts: 708 /
1,111 / 2,091. Reported by half; no gate. It asks whether that timing structure was the names.

## 2. The bar — M1 only, on the holdout half, which was never selected on for the gate

- **T1** the gated long pool's **gross** > 0 by 2 SE on the holdout half (n ≈ 490, SE ≈ 28 →
  needs ~+56; declared under-powered, as D430's was). **T1b** its net > 0 in sign.
- **T2** on the holdout half, `kept − excluded` (the gate's paired selection) > 0 by 2 SE.
- **T3** that difference beats the p95 of the **enumerated time-rotation null of the breadth
  series** (all 4,189 circular offsets; SE exactly 0 — D373 does not apply): does *this* set of
  days matter, or would any 27% of days do?
- **T4** the gated long book, N = 3, on the union: net > 0 by 2 SE (three seeds, block bootstrap).

**All four → the gate is an in-sample improvement with a mechanism that agrees across halves —
still not a candidate; `holdout2` is what a candidate would need.** T2 ∧ T3 without T1 = the gate
removes the right trades and what is left is still not a trade on new names.

## 3. Measured

Per trade on the union and each half, three windows: the long pool gated / excluded / ungated;
the short pool the same; D422's table throughout, concentration, the top trade named. M2's
tercile table and book. M3's gap table by half. Books: gated long N=3, ungated long N=3 (D428's
arm on the union, the reference), top-DV-tercile cell 2 N=10, three seeds; costs as before (no
borrow on longs; 1% on shorts where shown). Assertions: `[STAGE0]` the union's 2,083 / 1,783 and
the 27% / 3.4% breadth shares reproduce; `[P2]` the union pipeline reproduces D431's short-pool
N=3 book on every seed; `[GATE]` the breadth series is causal (a shifted-by-one recomputation
changes it — a check that fires when broken); `[ROT]` the rotation null's offset 0 equals the
observed statistic exactly; `[RECON]` every book.

## 4. Predictions (MODERATE for M1's direction, LOW for its size; M2, M3 moderate)

- **X-a** union long pool: excluded (27%) mean **−20 to +10**; kept **+55 to +75**; the
  difference +50 to +90, > 2 SE. On the **holdout half**: excluded **−150 to −300**, kept
  **0 to +40**; T2 passes; T3 passes (the rotation null's p95 is far below).
- **X-b** T1 fails (kept gross on ~490 trades inside 2 SE) and T1b is a coin — the gate removes
  the crash and does not by itself make new-name longs a trade.
- **X-c** the short pool through the gate: kept − excluded inside ±30 with a wide SE (3% exposure).
- **X-d** the gated long book on the union N=3: **+2 to +4.5** net/bar, above the ungated
  (D428's long arm on the union) by 0.5 to 2.
- **X-e** M2: cost falls monotonically with the DV tercile (bottom ~40 bp, top ~20); gross falls
  less than cost; the **top tercile of cell 2 nets −5 to +10 on the union and inside ±15 on the
  holdout half**; its 10-slot book inside ±1 of zero.
- **X-f** M3: on the holdout half the 6–10 premium is **+15 to +40** against +61 in-sample, and
  6–10 > 3–5 still; 11–20 lowest.

## 5. Not in scope

`holdout2`; any threshold other than the frozen ones and the one breadth cut fixed here; exits;
disposition. Thirty-second look by object; spent data throughout.
