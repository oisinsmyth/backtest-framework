# D423 — structure exits on the second zone: the first bounce as the target, the tested level, and the breach, through both lenses

**Pre-registration. Committed before the runner exists (R8).** Result goes in a separate file.
Numbered by PICKUP's procedure: D400–D422 used, D407–D410 and D390–D399 reserved. **No holdout.
The principal's standing rule holds — no holdout until there is a tradeable indicator — and an
exit study on an entry rung that has not itself been pre-registered (D422 §7 item 2) cannot
produce one.** 2024+ on the 15m fixtures is not read; this study is daily bars only (§3).

## 1. The question

D422 left the best object this line has: **STACK2-ANY ∧ cell 2** — the second touch on a name in
twenty sessions, either side, with REV ≤ −2.47%, EFF > 0.2367, DV > $44.4M — 9,411 trades, gross
+44.84 (median +25.57), net +16.04 per trade, and the first cell-2 required book that is net
positive on every seed. It exits at `t+5` close, no stop. D417 found no ATR-multiple exit beats
that clock, D418 found a zone stop knows nothing beyond its distance, D419 found a target recycles
the slot for +10 bp gross per swap and pays the round trip.

The principal asks whether an exit **read from the structure** does better. Three structures are
available at the entry, none of which reads a bar after it (`scripts/d423_exit_levels.py`,
committed with this record):

```
SWING   the extreme of the path between the prior touch day t_j and today, in the trade's
        direction -- WHERE THE FIRST BOUNCE ENDED. A second-zone trade is a bet on the bounce
        repeating; the structural target is the last one's high. NaN if not beyond the entry.
OPP     the nearest TESTED opposite-side level in the trade's direction: a prior opposite-side
        zone on the name, touched within 60 sessions, whose band lies beyond the entry.
FAR     the zone's far edge (D418's ST-edge) as a STOP ON THE CLOSE -- a close beyond it, not an
        intrabar touch, because D418 showed the intrabar version pays gap fills for nothing.
```

**The exit rules:** `FIXED` (t+5, the incumbent); `SWING` (limit at the swing, else t+5); `OPP`
(limit at the tested level, else t+5); `BREACH` (exit at the first close beyond FAR, else t+5);
`SWING+BREACH` (both; a resting limit fills before the close is evaluated). Every rule keeps the
`t+5` clock — these are *early* exits inside the hold, which is what was asked. Limit fills at
the level or better (`max(level, open)` in signed space); breach fills at the close.

## 2. Stage 0 — computed before this was written, as facts (no outcome bar read)

```
                      coverage    distance to level, ATR (p10/50/90)      within 2 ATR
SWING  ANY & cell 2     99.9%          1.73 / 3.24 / 5.26                   15.1%
OPP    ANY & cell 2     52.2%          0.21 / 1.31 / 3.65                   65.6%
FAR    ANY & cell 2    100.0%          0.36 / 1.42 / 2.46                   78.3%
SWING  ANY pooled       99.2%          1.10 / 2.18 / 4.07                   43.2%
```

Both SWING and OPP exist on 52.1% of the cell; on 92.9% of those OPP is the nearer. **The swing
is far — 3.24 ATR at the median, because cell 2's REV cut selects deep pullbacks, so the first
bounce's high is a long way back up.** D417's map on a fixed-distance target is `TP 1.0 +0.89
(50.8% fire), TP 2.0 +1.04 (20.9%), TP 3.0 +0.81 (8.0%)` pooled; a target at 3.2 ATR fires
seldom and, if structure is nothing but distance, adds about a basis point. The prior touch is
the same side on 50.4% — D422's split, unchanged.

## 3. The lenses, the object, and what is fixed

Entry at the touch-day close, five-session clock, D413's neutral cost — unchanged. Daily bars,
path-invariant walker in long space (D417's construction) for the per-trade lens; D419's
simulator with per-event level triggers for the book. **The primary population is ANY ∧ cell 2
(9,411).** Reported beside it: ANY pooled, cell 2 all, and long/short separately, because D422's
trade table showed the two sides have different shapes (long median +62, short median −14).

**Assertions before any number:** the level walker given `E ± 2·ATR` as its target reproduces
D417's `TP 2.0` exit bar and fill bit-identically on all 180,050 events (`[X]`, D418's pattern);
the level book given the same reproduces D419's `TP` book bit-identically and given no levels
reproduces D422's ANY-REQUIRED FIXED book bit-identically (`[P2]`); `[SIGN]` on a synthetic path
— a long whose swing is hit on bar 2 exits at the swing on bar 2, a short mirror exactly, a close
through FAR exits at that close and an intrabar wick through it does not; every book `[RECON]`.

## 4. The bar — SWING on ANY ∧ cell 2

- **T1 (per trade):** paired delta `SWING − FIXED` over the 9,411 trades exceeds zero by 2 SE
  (paired SE).
- **T2 (structure, not distance):** the delta beats the p95 of a **within-day permutation of the
  swing DISTANCE** (each event receives another same-day event's swing distance in ATR, applied
  from its own entry; 200 draws) — the null that keeps the distance distribution and destroys
  only the alignment with this event's structure. D373's margin. This is the test D418 taught.
- **T3 (book):** on the cell-2 ANY-REQUIRED 10-slot book, three seeds (419, 4190, 41900), the
  SWING exit's net bp/bar minus the same book's FIXED net exceeds zero by 2 SE (monthly block
  bootstrap), **and** the SWING book's net exceeds the p95 of D419's sampled-runs control (random
  holds drawn from SWING's own realised run distribution, 200 draws, seed 419), D373's margin.

**SWING clears when T1, T2 and T3 all hold.** OPP, BREACH and SWING+BREACH run through the same
three tests and are reported; only SWING is gated. Also reported, gated on nothing: D417's
would-have / filled-at decomposition on the early-exited trades (the forfeit), D419's replacement
premium on the book's swap ledger, the run distributions, and every table on ANY pooled and cell
2 all.

## 5. Predictions — held at LOW confidence, because four studies say the path has no state

- **X-a** SWING per-trade delta on ANY ∧ cell 2 between **0 and +4 bp**, inside 2 SE. T1 fails.
- **X-b** SWING fires on **8–16%** of the cell's trades (D417's map at 3.2 ATR).
- **X-c** trades that reach the swing give back **between −5 and +5 bp** afterwards — the target
  forfeits nothing, as D417's did.
- **X-d** BREACH delta **−5 to −12 bp**, fires on 25–35% (FAR is 1.42 ATR; D417's SL 1.5 fired
  31.2% in cell 2 at −10.84). Fails.
- **X-e** OPP delta inside 2 SE; fires on 25–35% of all cell trades (half have a level, half of
  those are within 1 ATR).
- **X-f** SWING inside 2 SE of its distance-permutation p95 — structure knows nothing beyond
  distance, D418's finding on the other end of the trade. T2 fails.
- **X-g** SWING book gross delta **0 to +0.5 bp/bar**, net delta inside 2 SE of zero; above the
  sampled-runs control's median, below its p95 (D419's TP pattern). T3 fails.

X-a and X-g are arithmetic on D417 and D419; X-f is the study. If X-f is wrong — the swing
beats its permuted distance — the first bounce's high carries information the ATR does not, and
that is the only result here that would change what the next pre-registration is about.

## 6. Not in scope

No holdout, no 15m fills, no change to entry, hold, cost model or cell, no parameter sweep on
the levels, no disposition. Twenty-third look by object on price levels; twenty-two of
twenty-two before it failed their bar.
