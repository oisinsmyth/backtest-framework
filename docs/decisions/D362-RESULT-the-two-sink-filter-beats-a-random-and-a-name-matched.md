# D362 RESULT — the two-sink filter beats a random removal and a name-matched rotation of its own flags; the five-sink version does not beat the rotation; and once the filter is on, the gate explains less

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D362-RESULT-the-two-sink-filter-beats-a-random-and-a-name-matched-removal-and-the-gate-explains-less-once-it-is-on.md`. The H1 above is the full title.*

**Status:** RESULT. Pre-registered at `38d7a74`, runner at `fcd6891` — both before this file
existed (R8). **No holdout data was read**: the runner audits every file it opens and refused
a probe path. `keep_v2`, F0, next-open fill, hedged, D345's kernel, cap 10, PUB primary, PB
beside, GC/HTB borrow in the net. Three arms, multiplicity three, on five conditions selected
from about forty on this same sample — the selection history is part of the result.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is a book. Nothing is promoted. Within-sample with nulls, not out-of-sample. The avenue is the principal's (R15).**

---

## 1. The verdict

**Eight of ten; the load-bearing prediction held; the "against" held.** Removing the events
that hit either of the first two sinks — a name trading below most of its own volume
history, or a calm market — from the gated gap-up fade's **signal** and re-simulating gives
**+61.7 gross a trade on 3,079 trades** (t 3.2) against +42.3 on 3,977 unfiltered. That is
above the p95 of removing the same number of events at random (**DROP +55.7**, p50 +41.8)
and above the p95 of rotating each name's own hit flags in time (**FROT +54.3**, p50 +43.4),
at 200 draws each. The two conditions remove the right events, not merely enough of them,
and the right *times* within a name, not merely the right names.

| arm, cap 10, short | events | trades | gross | median | t | trim 1% | era 1 | era 2 | net PB | net PUB | exposure |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| base (D361) | 4,574 | 3,977 | +42.3 | +16.9 | 2.5 | +35.0 | +18.9 | +55.1 | +3.3 | −47.2 | 28.0% |
| **A2, sinks 1–2 removed** | 3,529 | 3,079 | **+61.7** | +32.9 | 3.2 | +56.7 | +58.8 | +63.1 | **+20.3** | −29.8 | 24.9% |
| A5, all five removed | 2,026 | 1,868 | +83.6 | +42.4 | 3.9 | | +74.8 | +88.0 | +43.7 | −0.1 | 24.9% |
| W, size 0.5 per hit | 4,574 | 3,977 | +66.1 per unit capital | | 3.9 | | +50.3 | +74.3 | +26.8 | −23.7 | 28.0% |

**Q2 failed, and it is the finding that matters next.** A2 is above its own names at random
gate-on times (A′ p95 +32.9) and random direction (+32.3), but **not above the gate rotation
on the filtered signal (ROT p95 +79.3, p50 +30.6)**. Unfiltered, the gate was worth about +27
a trade over a random gate of the same shape (D361); filtered, the observed sits near the
85th percentile of random gates. The calm-market sink is itself a market state, so part of
what the gate did the filter now does, and the gate's incremental value shrinks. The record
says so rather than reading Q1 alone.

## 2. The three arms

**A2 is the filter.** Re-simulated and row-dropped agree to +0.7 bp (Q10): concurrency does
not carry the effect. Both eras improve, era 1 from +19 to +59 and era 2 — which did not set
the thresholds — from +55 to +63 (Q8). The symmetric 1% trim rises from +35 to +57 (Q7). It
removes 23% of the trades and 3 points of exposure (Q9). The held names are the same names
(43 bp a side against 42), so the net moves because the gross moves: +20 under PB, −30 under
PUB, breakeven 28 bp a side.

**A5 is more selective and less robust.** +83.6 on 1,868 trades, above DROP (+76.1) and
**inside FROT (p95 +89.8)**: the three extra sinks — high beta, a thin volume node,
overnight-driven volatility — are properties of *names* more than of times, and rotating a
name's flags across its own events removes much the same trades. Its names are cheaper (39 bp
a side) and it is at breakeven under PUB (−0.1) and +44 under PB. Q3 and Q4 held.

**W keeps every trade and has the best t.** Halving size per hit gives +66 per unit of
capital at t 3.9 on 67% of the base's capital (Q6), above the gate rotation and A′ on the
unfiltered signal; the weighted deployed base is +5.7 gross a bar against +4.7. Two thirds of
the improvement with none of the trade count lost.

## 3. The sinks on the base ledger

| | threshold (era 1) | trades hit | hit mean | non-hit mean |
|---|--:|--:|--:|--:|
| S1 below its volume history | ≥ 86.84 | 581 (15%) | −51.4 | +58.4 |
| S2 calm market | ≤ 99.03 bp | 437 (11%) | −4.8 | +48.1 |
| S3 high beta | ≥ 87.22 | 827 (21%) | −26.3 | +60.4 |
| S4 thin volume node | ≤ 18.77 | 663 (17%) | −12.6 | +53.3 |
| S5 overnight-driven vol | ≤ 6.38 | 811 (20%) | −4.5 | +54.3 |

Hits stack: 1,832 trades with none earn +86; one hit +30; two +6; three −92; four −304. Only
S1 is a loser in its own right at these thresholds; S2 and S5 are near zero. The filter works
by removing the trades that hit several, and by removing S1.

## 4. Four groups, A2

n 3,079 · mean +61.7 · median +32.9 · win 52.4% · payoff 1.09 · skew +0.3 · kurtosis 11 ·
trims: ex-top +15.1, ex-bottom +103.3, symmetric +56.7 · **names to half the P&L 11 of 995**
(base: 8) · top-1 / 5 / 10 name share 13% / 32% / 48% · profitable years 8 of 13 · **top
trade NBIS entered 2022-02-16 at $53.58, DV percentile 76, +8,772 bp = 4.6% of the P&L**
(base: PLAY March 2020, 7.2%). Dead and alive earn alike (+60 / +62); the cheaper half +80
against +44. 2021 is +387 on 69 trades and 2014 −84 on 53; 2023 is still negative (−37 on
217, from −69 on 346).

## 5. Predictions

| | | |
|---|---|---|
| **Q1** *(load-bearing)* | **CONFIRMED** | +61.7 > +42.3; DROP p95 +55.7; FROT p95 +54.3 |
| **Q2** | **FALSIFIED** | ROT p95 +79.3 (p50 +30.6); A′ p95 +32.9 cleared |
| Q3 | CONFIRMED | A5 +83.6 > A2 +61.7 |
| Q4 | CONFIRMED | A5 keeps 47%, A2 77% |
| Q5 *(against)* | FALSIFIED — the "against" held | −29.8 net PUB; +20.3 PB |
| Q6 | CONFIRMED | W t 3.88 > A2 t 3.19 |
| Q7 | CONFIRMED | trimmed +56.7 > +35.0 |
| Q8 | CONFIRMED | era 2 +63.1 > +55.1 |
| Q9 | CONFIRMED | 24.9% < 28.0% |
| Q10 | CONFIRMED | +0.7 bp |
| *check* | held | base == D361 to 1e-9; row-drop A5 era 2 = 1,221 / +91.48; the five features equal the export's columns on all 4,574 events |

## 6. Stop conditions, executed — and what the record does not decide

- **Q1 holds** → within this sample the two-sink filter is real beyond a random or
  name-matched removal of the same size. It is the version of the fade the principal can
  carry forward, knowing its selection history.
- **Q2 fails** → the filter improved the mean partly by removing what the regime explained:
  after it, the 200-day gate is inside its own rotation's p95. **The next question is not
  the filter's; it is whether the gate is still needed at all with S2 in place**, and the
  honest form of that is a cell the record has not run: the unfiltered T2 trigger with the
  calm-market condition alone and no 200-day gate, against the same rotation. Listed, not
  run.
- **A5 fails FROT** → the three name-level sinks are a description of which names lose, and
  the record does not carry them as timing.
- The cross-era evidence (thresholds from era 1, era 2 improves) is the only out-of-bin
  evidence and is reported, not counted. **The holdout was not read.**
- Nothing is promoted. Book: empty.

## 7. Deviations and what the run found

- **The pre-registration's §0 quoted +77 on 2,641 and +87 on 1,654** for the row-drop arms;
  those came from the export screen with full-sample thresholds. With the era-1 thresholds
  §1 fixes, the row-drop is +61.0 on 3,028 and +86.3 on 1,832. Only the §4 check (1,221,
  +91.5) was asserted and it reproduces; the §0 figures were illustrative and should have
  been recomputed at the thresholds the record fixed. STACK §7 item 32.
- **W's turnover** is on the weighted entries and the weighted held count; its cost line is
  G22's arithmetic on the weighted series, asserted equal to G22 key for key at unit weights.
- **FROT** rotates each name's whole hit matrix by one offset; 229 single-event names keep
  their flags (54 of A2's 1,045 removed events); periodic vectors are redrawn and counted.
- **The gate rotation** keeps the sink flags on their observed bars and rotates only the
  gate; the calm-market flag is therefore fixed in calendar time while the gate moves, which
  is the construction that makes Q2's failure interpretable.
- **[C]** at 3 SE, as D358–D361. No assertion weakened; [FEAT] checks every event, not 300.

## 8. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** · **[HOLDOUT-GUARD]** | via the shared prep; 271 file opens audited, none containing "holdout", the probe refused |
| **[ID]** · **[FEAT]** · **[HIT]** · **[RD]** | base == D361 to 1e-9; five features == the export on all 4,574 events; flags == a direct recomputation; row-drop A5 era 2 == 1,221 / +91.48 |
| **[W]** | unit weights == the unweighted rebuild and the kernel to 2e-18; Σ w·pnl / Σ w == a direct loop; capital == Σ w / n |
| **[DROP]** · **[FROT]** · **[ROT]** · **[A′]** · **[C]** | exact counts, never the observed set; per-name counts kept, never the observed vector; on-share and run multiset kept; every rotated event eligible and gate-on; C z −0.2 at 3 SE with the observed outside the band |
| **[S]** · **[HX]** | 300 A′ short trades == the recomputation to 0.0; +50 bp on ABFS 2011-08-04 moves one short by −50.000 and no other; the hedged deployed series == the ledger to 2e-15 on every arm |
| **[6]** | [ID], [FEAT], [DROP], [W], [S] each raise on their broken input |

**Speed:** self-test 12 s; DROP 0.12 s a draw, FROT 0.19, ROT 0.10, A′ 0.24; three arms in
parallel under 3 min; report 9 s; peak working set 1.16 GB.

## 9. What this establishes

1. **Two of the five sinks are timing, three are names.** S1 and S2 beat a name-matched
   rotation of their own flags; S3–S5 do not.
2. **The two-sink filter is the fade's better version within this sample**: +62 a trade,
   t 3.2, both eras, trim +57, 11 names to half, +20 net under PB.
3. **A calm-market filter is a regime condition**, and with it on the 200-day gate is no
   longer distinguishable from a random gate at the p95. Which of the two is the state
   variable is the next cell.
4. **Sizing per hit is the safer form**: every trade kept, t 3.9, two thirds of the gain.

## 10. Files

`data/d362_ctrl_{A2,A5,W}_p0.json` · `data/d362_sink_filter.json` · `scripts/run_d362_sink_filter.py`
· reuses `scripts/run_d361_regime_gated_short.py`, `scripts/d361_export_trades.py`,
`scripts/run_d360_news_gap_short.py`, `scripts/run_d359_loser_rally_short.py`,
`scripts/run_d358_flat_sleeve.py`, `scripts/d345_event_book.py`, `scripts/d348_prep.py`,
`scripts/d322_four_group_report.py`. The holdout fixture was not read.
