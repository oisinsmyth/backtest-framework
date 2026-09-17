# D360 RESULT — the news gap carries no drift: the gapped name bounces against its own random days, both gap directions reverse, and the short side closes on tape signals

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D360-RESULT-the-news-gap-carries-no-drift-the-gapped-name-bounces-and-the-short-side-closes-on-tape-signals.md`. The H1 above is the full title.*

**Status:** RESULT. Pre-registered at `2562e2c`, runner at `d3b528b` — both before this file
existed (R8). `keep_v2`, F0, next-open fill, hedged against the floored market, D345's kernel
with the hedged series, no slot cap, PUB primary, PB beside, GC/HTB borrow in the net. Four
cells, multiplicity four.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is a book. Nothing is promoted. The short side has no tape signal on the floored universe.**

---

## 1. The verdict

**Zero of nine; the check held.** A gap in the bottom 2% of the day on top-decile volume, in
a name still above the floor after the gap, shorted at the next open and held ten bars, is
**−0.42 bp a trade on 20,059 trades**. Its own names at random eligible times earn the short
+6.3 (A′ p50; p95 +14.4): **the day after bad news is a better day to be long the name than a
random day.** The same-day same-bucket control is −1.6 / +4.1; random direction +11.0 at
p95. No cell, no exit, no arm is above any control.

| short, bp per TRADE, cap 10 | events | excluded | n | mean | median | t | 2c PUB | 2c PB | half-spread PUB | borrow | HTB | net PUB | net PB |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **cell 2 / 10** | 23,332 | 422 | 20,059 | **−0.4** | +0.6 | −0.1 | 64.9 | 39.3 | 31.0 | 2.4 | 2.6% | **−67.8** | −42.1 |
| cell 2 / 20 | 30,308 | 763 | 25,177 | −1.3 | −0.6 | −0.2 | 65.3 | 35.8 | 31.3 | 2.4 | 2.5% | −69.1 | −39.6 |
| cell 5 / 10 | 37,089 | 642 | 29,454 | −7.8 | −0.6 | −1.5 | 64.0 | 35.2 | 30.6 | 2.4 | 2.7% | −74.2 | −45.5 |
| cell 5 / 20 | 54,737 | 1,268 | 40,883 | −6.4 | +0.4 | −1.5 | 64.3 | 31.7 | 30.8 | 2.4 | 2.6% | −73.1 | −40.5 |
| no-volume gap, 2% | 12,681 | 626 | 10,063 | −7.3 | +5.8 | −0.7 | 85.5 | 16.6 | 40.9 | 2.5 | 2.8% | −95.3 | −26.4 |
| **mirror: volume gap up, LONG** | 24,736 | 14 | 20,621 | **−14.8** | −16.0 | −2.1 | 69.9 | 36.5 | 33.5 | — | — | −84.7 | −51.2 |

The names are what the record wanted them to be — ordinary, $35, 31 bp a side under PUB
(18 PB), general collateral on 97% — and it makes no difference, because there is nothing to
earn.

## 2. Stage 0: the gap reverses, in both directions

The premise was the event's own drift. It is the opposite sign.

| the NAME's hedged forward return, bp per event | 10 bars | 10, era 1 | 10, era 2 | 10, down-years | 20 bars | 20, era 2 | 20, down-years |
|---|--:|--:|--:|--:|--:|--:|--:|
| after a volume gap down (primary, 23,332) | −1.6 | +1.3 | −4.4 | **+16.8** | **+7.0** | +12.6 | **+37.7** |
| after a no-volume gap down (12,681) | +13.4 | −11.0 | +32.9 | +3.8 | +33.4 | +73.4 | +15.8 |
| the same names, random eligible days | −7.3 | −11.7 | −3.4 | −7.0 | −26.0 | −26.2 | −26.3 |

These names drift *down* on their random days (−7 per 10 bars, −26 per 20: they are the
kind of names that gap). After a volume gap down they drift down *less* at ten bars and *up*
at twenty, by 6 to 33 bp against their own baseline, and in the down-years they bounce +17
and +38. The no-volume gap bounces harder still (+13 / +33). **And the gap up on volume
reverses too**: the mirror, long, loses 15 bp a trade at cap 10 on every cell (t −2.1 to −3.7).
On this universe a large gap on volume is followed by a partial reversal in either direction,
not by drift. The post-announcement drift the literature measures on earnings dates does not
show on tape-identified news days here — or it is smaller than the reversal that follows an
extreme day, which D347, D350 and D358 already established for falls without a gap.

## 3. The predictions, and what each said

| | | |
|---|---|---|
| **Q1** *(load-bearing)* | **FALSIFIED** | −0.42; A′ p95 +14.4, B p95 +4.1, C p95 +11.0 |
| Q2 | FALSIFIED | no-volume −7.3, the volume arm is 6.9 better, not 20 — the attention is worth something, the information is not |
| Q3 | FALSIFIED | mirror −14.8 — the gap up reverses |
| Q4 *(against)* | FALSIFIED — the "against" held | −67.8 net PUB after borrow |
| Q5 | FALSIFIED by 1 bp | 31.0 a side against 30; PB 18.2 — ordinary names, as argued |
| Q6 | FALSIFIED | cap 20 −9.6 against cap 10 −0.4 — the longer the hold, the more the bounce |
| Q7 | FALSIFIED on size | `rev_5`'s gap-day entries +37.2 against +44.0 for the rest, 6.75 less, not 15 — the direction held |
| Q8 | FALSIFIED on one clause | HTB 2.6% (not < 2%), borrow 2.4 (< 3) |
| Q9 | FALSIFIED | era 1 −1.5, era 2 +0.6 |
| *check* | held | gap == raw open / prior close to 0.0 on 300 events; 422 ex-distribution and 0 zero-volume gaps excluded and counted on the primary; D353 reproduced to 1e-9 |

**Q2, Q5, Q7 and Q8 held in direction and failed on the size the record asked for.** They
describe the construction correctly — the names are ordinary, the volume adds a little, the
gap day is a slightly worse entry for the long — and none of that is a short.

## 4. Four groups, the primary cell

n 20,059 · mean −0.4 · median +0.6 · win 50.0% · payoff 1.00 · skew −1.9 · kurtosis 66 ·
trims: ex-top −35.9, ex-bottom +38.3, symmetric +2.8 · profitable years 10 of 17 · **top
trade ARNA entered 2010-09-14 at $4.13 (DV percentile 69), held 10 bars, +9,516 bp** — a
biotech's FDA-panel week, entered at an as-traded price under the floor's later level (the
floor is applied at t−1; the name qualified). Concentration fields are undefined on a
ledger whose total is at zero. Dead names +15.5 on 4,653 against alive −5.2; the cheaper
half +15.7 against −16.5. The short earns only on names that later died and on cheap
names, and loses on the rest.

**The `rsi` interaction**: the (95, 98] bucket is −206 on 161 trades and the (50, 75] bucket
−59 on 1,156 — a gap down in a name that was strong keeps bouncing; no bucket is a short's
ground.

## 5. Deployed base

Every cell is deployed on 100% of bars (49 to 172 positions open; D358's arithmetic again),
gross −0.1 to −1.1 bp/bar hedged, net −13 to −14 under the 4-crossing line and −7 under the
2-crossing line. Nothing to add.

## 6. Stop conditions, executed

- **Q1 fails and Q2 fails** → by the pre-registration, **news gaps carry no drift on this
  universe; with levels (D352), loser rallies (D359) and news events (this record) tried,
  the short side of the three-layer design closes on tape signals.** What remains is a
  regime gate (the loser cohort falls in era 1 and the down-years, D359) or data from
  outside the tape.
- Nothing is promoted. Book: empty.

## 7. Deviations and what the run found

- **Control B keeps 21% of the primary's events** (4,944 of 23,332) for want of a same-day
  same-bucket eligible name: news gaps cluster in earnings seasons and crashes and the
  bucket's pool runs out. The shortfall is counted per the pre-registration; B is
  therefore partly the observed ledger and its p95 is a weak bar. Q1 fails on A′ and C
  regardless.
- **The gap is a price gap on the split-adjusted bars, ex-dividend**: `open(g) / close(g−1)
  − 1` on the fixture's own bars (a second streamed read, cached in `temp/`, whose close
  equals the prep's bit-identically), not derived from the kernel's returns, because `r1T`
  is a total return. Ex-distribution days are re-read from the events file (amounts ≥ 1% of
  the prior close; 9,678 such entries across the fixture).
- **The recovery exit** runs through the kernel's invalidation mechanism on a per-name grid
  keyed to the name's most recent event, replayed independently ([REC], 20,167 trades,
  trade for trade); 62% of its trades exited on the retrace, 38% on the cap.
- **Stage 0** is a direct forward grid (h = 10, 20), not the ledger; events in the last h
  bars dropped and counted.
- **[C]** at 3 SE, as D358 and D359. No assertion weakened.

## 8. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | via the shared prep; the open grid streamed from the fixture, its close == the prep's bit-identically |
| **[GAP]** | 300 sampled events across every arm: derived gap == raw open / prior close to 0.0; `rv` == direct recomputation to 0.0; the kernel identity `(1+r1T)/(1+ocT)−1` == gap to 8.9e-16 off dividend days |
| **[E]** | 300 per cell by direct count in the day's cross-section, `elig` at g+1, grids to 1e-9 |
| **[XD]** · **[V0]** | no survivor on an ex-distribution or zero-volume day; excluded counts printed per arm |
| **[G]** | cells partition the volume gap-downs with their complements; the no-volume arms and mirrors disjoint from every cell; cells nest |
| **[R5]** | 27,316 trades, +43.3806 to 1e-9, and D358's identity against D353's own path; the Q7 split covers every trade |
| **[SB]** | 200 trades to 0.0; HTB 523 of 20,059 by the rule |
| **[S]** | 300 A′ short trades == the open-fill recomputation bit-identically; 156 fell / 144 rose, all paid the right way; +50 bp on SDOCQ 2010-04-07 moves one short by −50.000 and the deployed series by −6.25 = −50 / 8, no other bar; the mirror's +50 bp on TDG moves one long by +50.000 |
| **[A′]** · **[B]** · **[C]** | every rotated event eligible, counts kept; date and bucket kept, 4,944 kept == the counted shortfall; C z +0.1 at 3 SE, the observed inside the band, stated |
| **[HX]** | hedged and unhedged deployed series equal the ledger per bar to 2e-14 on all cells × exits |
| **[REC]** | the recovery ledger equals an independent replay of the kernel's rules trade for trade; 300 trades against the raw closes: 184 on the first retrace bar, 116 on the cap |
| **[6]** | [GAP] raises on a perturbed open; [S] on a sign-flipped ledger; [XD] on an injected ex-distribution event; [R5] on a perturbed ledger; [REC] on a trade held one bar long |

**Speed:** self-test 26 s (18 s of it the one-time open-grid build); A′ 0.7 s a draw, B 1.1;
four cells in parallel under 4 min; report 73 s; peak working set 1.33 GB.

## 9. What this establishes

1. **A tape-identified news day is followed by reversal, not drift, on this universe** — in
   both directions, at ten and twenty bars, and hardest in the down-years. The long side's
   rule (a sharp fall bounces) covers gaps too; the argued exception did not hold.
2. **The short side has no tape signal on the floored universe.** Levels select the wide
   names whose drift is smaller than their cost (D352); loser rallies are inside a pool that
   rises (D359); news gaps reverse (D360). Three constructions, one universe, one answer.
3. **What remains for a short sleeve** is a regime gate — the only place any short paid
   before cost is where the loser cohort falls — or information that is not on the tape.
4. **The winners' dip long (D359 §6) is the next pre-registration**, unchanged by this
   record.

## 10. Files

`data/d360_stage0.json` · `data/d360_ctrl_{2,5}_{10,20}_p0.json` · `data/d360_news_gap_short.json`
· `scripts/run_d360_news_gap_short.py` · reuses `scripts/run_d359_loser_rally_short.py`,
`scripts/run_d358_flat_sleeve.py`, `scripts/run_d349_short_signal_controls.py`,
`scripts/run_d353_rev5_record.py`, `scripts/d345_event_book.py`, `scripts/d337_borrow.py`,
`scripts/d348_prep.py`, `scripts/d322_four_group_report.py`.

---

## Addendum — the closure withdrawn, 2026-09-06 (the principal's ruling)

§6 and §9 above say "the short side closes on tape signals" and §9(3) says what
"remains". That was the pre-registered stop condition executed as written, and it was
wrong to write as a closure: **a research avenue is closed by the principal, not by a
record.** The principal's ruling, the same day:

- **The criterion for a signal is a positive gross mean per trade, above the nulls.**
  Cost — the spread convention, borrow, the crossing line — is reported beside it and is
  tuned afterwards; confluences and gates are the next step for a signal that passes,
  not a reason to discard one.
- **The short side stays open.** What this record established is that a volume gap in
  either direction reverses on this universe at ten and twenty bars. What it did not
  test is listed in D361: a regime gate on the triggers the record already has, and the
  gap-up fade (the mirror, +15 a trade at cap 10, t −2.1 to −3.7 for the long) under its
  own controls.

The sentences in §6 and §9 stand as written and are read with this addendum. FINDINGS
§40 rule 1 and STACK §0 are amended the same way.
