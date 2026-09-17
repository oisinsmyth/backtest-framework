# D426 — double down on the second zone: rung 1 traded, rung 2 added, the clock restarted and the zone stops brought in, both lenses

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D426-double-down-on-the-second-zone-rung-1-traded-rung-2-added-with-the-restart-and-the-zone-stops-both-lenses.md`. The H1 above is the full title.*

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file. D400–D425
used, D407–D410 and D390–D399 reserved. **No holdout of any kind is read.** Daily bars.

## 1. The construction, as the principal set it

Terms: **rung 1** = the first touch (D422's STACK1); **rung 2** = the second zone (STACK2-ANY,
D422's counter — distinct prior (day, side) pairs, kept exactly). Cell 2 throughout.

1. **Rung 1** in cell 2: enter at the touch-day close, five-session clock, **no stop**.
2. **A same-side rung-2 touch on the name while rung 1 is held** (gap ≤ 5): **double down** — a
   second equal unit at the rung-2 touch-day close.
3. From that close **both units** carry the zone exits read from the **rung-2 zone**: a limit at
   the next live opposite-side zone (D425's ZTP) and a stop on a close through the rung-2 zone's
   far edge (D423's FAR); and **rung 1's clock restarts** — both units exit five sessions after
   the rung-2 touch, or at the target/stop, whichever first.
4. A rung-2 event with no rung-1 held is a single-unit trade **with** the same exits.
5. Rung 3+ is never traded. An **opposite-side** rung-2 touch on a held name does not add
   (assumption stated to the principal; counted, not traded).

**Two versions.** **A**: the rung-2 touch must itself be in cell 2 to add. **B**: any same-side
rung-2 touch on a held cell-2 rung 1 adds (the standalone rung-2 pool stays cell 2 in both, so
the versions differ only in the add).

Flags in `scripts/d426_rung_flags.py`, committed with this record; levels from
`scripts/d425_zone_levels.py`.

## 2. Stage 0 — facts computed before this was written (no outcome bar)

```
rung 1 & cell 2   7,974 trades          rung 2 & cell 2   9,411
rung 2 & cell 2:  gap to the prior touch p10/50/90 = 2/9/18 sessions;  gap <= 5 on 32.2%;
                  the prior touch is a same-side event on 67.7%, opposite-side on 32.3%
adds A            1,022  = 12.8% of cell-2 rung-1 trades are doubled
adds B            1,249  = 15.7%
add gap A         p10/50/90 = 1/2/4  ->  rung 1's restarted hold: 5 + gap, median 7 sessions
rung 2 on a held rung 2 (same side, gap <= 5): 152 -- not doubled, reported
```

**Priors in numbers.** ADDENDUM 3's marginal per-bar edge on cell 2 is +6.3 +9.4 +6.9 +6.1 +1.5
through bar 5, then **−2.6, −6.3** on bars 6 and 7 — the restart holds rung 1 into the bars that
pay negative. D423's FAR on rung 2 was −6.61 per trade; D425's ZTP +0.36. D422: rung 1 pays
+29.87 in cell 2, rung 2 +44.84, the incumbent ANY-REQUIRED book +1.24 net over seeds.

## 3. The lenses

**Per episode (path-invariant).** The population is every cell-2 rung-1 trade (7,974). Each is an
*episode*: rung-1 entry, an add if one arrives, joint exit. P&L in **unit-returns** (unit 1's log
return plus unit 2's), so a doubled episode can earn or lose twice. Four rules on every episode:

```
BASE       rung 1 at t1+5; the rung-2 event traded as its own independent 5-day trade (D422 as is)
RESTART    both units exit at t2+5, no stops                    -- the restart alone
STOPS      rung 1 at t1+5; rung 2 alone with ZTP+FAR             -- the stops alone
DD         both units: ZTP+FAR from the rung-2 zone, clock from t2  -- the construction
```

Undoubled episodes are identical under all four; the deltas live on the 1,022 (A) / 1,249 (B).
Reported per episode, per unit, per capital-day, long/short, 2018+; the forfeit decomposition on
the doubled episodes; standalone rung-2 with ZTP+FAR against `t+5`.

**The book (path-variant).** D419's simulator with two-slot names: an add takes a second slot if
one is free (else it is skipped and counted); the exits and the restarted clock apply to both.
Books on cell 2, 10 slots, three seeds: `ANY-REQ` (D422's incumbent, reproduced bit-identically
first), `UNION-1PN` (rung 1 ∪ rung 2, one per name, no stops — rung 2 blocked when rung 1 is
held), `UNION-STOPS` (as UNION-1PN, standalone rung 2 with ZTP+FAR), `DD-A`, `DD-B`.

**Assertions:** `[X]` the episode walker with no add and no levels returns `r_base` exactly;
`[P2]` the two-slot simulator with adds disabled and no levels reproduces D422's ANY-REQ book
bit-identically on the rung-2 pool, and D425's `sim2` on ZTP+FAR levels on the same pool;
`[SIGN]` a synthetic doubled episode: unit 1 marks from its own entry, unit 2 from its own, both
exit on the same bar at the same price, the restart holds unit 1 past its original `t1+5`, a
short mirror exact in log return, the check fires when broken; `[RECON]` every book;
`[CHUNK]`/`[NUISANCE]` on the control.

## 4. The bar — version A

- **T1** on doubled episodes: mean of `DD − BASE` (unit-return sum) > 0 by 2 paired SE.
- **T2** `DD-A` net bp/bar − `ANY-REQ` net > 0 by 2 SE (three seeds, monthly block bootstrap).
- **T3** `DD-A` net above the p95 of matched-count random cell-2 pools (D422's control, one per
  name, no stops, 100 draws), D373's margin.

**Version A clears when all three hold.** B and the ladder are reported.

## 5. Predictions (LOW–MODERATE; the arithmetic is ADDENDUM 3 × D423 × D425)

- **X-a** `RESTART − BASE` on doubled episodes **−5 to −15** per episode: rung 1 is held into
  bars 6–7, which pay −2.6 and −6.3, and unit 2 is unchanged.
- **X-b** `STOPS − BASE` **−3 to −10**: FAR costs ~6.6 on the rung-2 unit, ZTP ~+0.4.
- **X-c** `DD − BASE` **−15 to −30** per doubled episode, negative by more than 2 SE. T1 fails.
  Per rung-1 trade (×12.8%) about −2 to −4.
- **X-d** `UNION-1PN` net **below** `ANY-REQ` by 0.3–1.0: it blocks the best trades (a third of
  rung 2 arrives inside rung 1's hold) and fills with +30 trades against a 29 bp round trip.
- **X-e** `DD-A` net **+0.2 to +0.9**, below `ANY-REQ`'s +1.24; utilisation 85–92%; T2 fails.
  **T3 passes** — random pools of ~17,000 cell-2 events sit near FIXED-all's −0.72 and DD-A is
  above them. `DD-B` within 0.2 of `DD-A`.
- **X-f** the ladder orders `BASE > STOPS > RESTART > DD` on the doubled episodes.

X-c is the study. If it is wrong — if doubling into the second zone with the restart and the
zone exits beats trading the two touches independently — the second zone is not merely a better
entry but a state in which the first trade should be re-underwritten, and that is a different
object from anything this line has measured.

## 6. Not in scope

No holdout, no 15m, no change to entry price, cell, cost model or hold length, no parameter
sweep, no opposite-side adds, no disposition. Twenty-sixth look by object; twenty-five of
twenty-five before it failed their bar.
